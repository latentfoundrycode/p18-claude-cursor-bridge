#!/usr/bin/env python3
"""mutation-run: apply mutants in a scratch copy, run tests, cache kills.

Run from the Workspace root: python ~/.claude/cursor-bridge/mutation-run.py <mutants file>
[--all] [--checkpoint <commit>] [--scratch <folder>] [--mutant-timeout <seconds>]. The mutants
file is run/supervisor/<id>-mutants.json. Scratch defaults to ~/.cursor-bridge/scratch/<project>/.
Exit 0 when every mutant is killed (or cached kill); 1 when any survived, was not applied, or an
expect-survive mutant was killed; 2 for a malformed file, refused path or resolution check, when
the same run id is already running in the scratch base, or --all with --checkpoint; 3 when any
mutant errored or on an internal crash; 4 in --checkpoint mode
when any listed new test passed on the old code; 5 when a tests list fails or errors on the
unmutated code before any mutant runs. A mutant whose tests list times out on the unmutated code
is an error and is not run. ASCII-only on purpose (cp1252 consoles).
"""
import argparse
import ast
import hashlib
import stat
import importlib.machinery
import json
import os
import re
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone

_IMPORT_ERRORS = []
try:
    import tomllib
except Exception as e:
    _IMPORT_ERRORS.append(("tomllib", e))
    tomllib = None

_BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BRIDGE_DIR not in sys.path:
    sys.path.insert(0, _BRIDGE_DIR)
try:
    import bridge_env
except Exception as e:
    _IMPORT_ERRORS.append(("bridge_env", e))
    bridge_env = None

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def interpreter_argv():
    if sys.version_info >= (3, 11):
        return [sys.executable, "-P"]
    return [sys.executable]
MUTANT_ID_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
PLUGIN_NAME = "_mutation_resolution_check.py"
PLUGIN_MOD = "_mutation_resolution_check"
OUTCOMES_PLUGIN_NAME = "_mutation_outcomes.py"
OUTCOMES_PLUGIN_MOD = "_mutation_outcomes"
DEFAULT_DOTTED_PREFIXES = ("", "src/")
OUTCOMES_PLUGIN_CODE = """import json
import os

OUT_PATH = os.environ.get("MUTATION_PYTEST_RESULTS", "")

_state = {"tests": [], "collect_errors": [], "session_finished": False, "exitstatus": None}


def _slash_file(nodeid):
    head, sep, tail = nodeid.partition("::")
    return head.replace(chr(92), "/") + sep + tail


def _write():
    if OUT_PATH:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(_state, f)


def pytest_runtest_logreport(report):
    if report.when == "call":
        if report.passed:
            outcome = "passed"
        elif report.failed:
            outcome = "failed"
        elif report.skipped:
            outcome = "skipped"
        else:
            outcome = "error"
    elif report.failed:
        outcome = "error"
    elif report.skipped:
        outcome = "skipped"
    else:
        return
    nodeid = _slash_file(report.nodeid)
    _state["tests"].append({"nodeid": nodeid, "outcome": outcome})


def pytest_collectreport(report):
    if report.failed:
        _state["collect_errors"].append(_slash_file(report.nodeid))


def pytest_sessionfinish(session, exitstatus):
    _state["session_finished"] = True
    _state["exitstatus"] = exitstatus
    _write()
"""


def _try_lock_byte(fd):
    if sys.platform == "win32":
        import errno
        import msvcrt
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return True
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EDEADLOCK):
                return False
            raise
    import fcntl
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def _unlock_byte(fd):
    if sys.platform == "win32":
        import msvcrt
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        import fcntl
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass


class Refuse(Exception):
    """Malformed input or refused path; exit 2."""


class InternalError(Exception):
    pass


class ResolutionTimeout(Exception):
    def __init__(self, seconds):
        self.seconds = seconds


def git(*args, cwd=None, env=None, binary=False, ok=(0,)):
    try:
        p = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-c", "core.quotepath=false"] + list(args),
            capture_output=True, cwd=cwd, env=env, creationflags=NO_WINDOW,
        )
    except OSError as e:
        raise InternalError("git could not be started (%s)" % e)
    if p.returncode not in ok:
        err = p.stderr.decode("utf-8", "replace").strip()[:400]
        raise Refuse("mutation-run: git %s failed: %s" % (" ".join(args[:4]), err))
    return p.stdout if binary else p.stdout.decode("utf-8", "replace")


def git_try(*args, cwd=None, binary=False):
    try:
        p = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-c", "core.quotepath=false"] + list(args),
            capture_output=True, cwd=cwd, creationflags=NO_WINDOW,
        )
    except OSError:
        return None
    if p.returncode != 0:
        return None
    return p.stdout if binary else p.stdout.decode("utf-8", "replace")


def ls_files_index(workspace):
    out = git("ls-files", "-z", cwd=workspace)
    return [p for p in out.split("\0") if p]


def path_bad(rel):
    if not rel or rel.startswith("/") or (len(rel) > 1 and rel[1] == ":"):
        return True
    if rel == ".":
        return True
    parts = rel.replace("\\", "/").split("/")
    if ".." in parts or not parts[0]:
        return True
    if "" in parts or "." in parts:
        return True
    if parts[0].lower() == ".git":
        return True
    for part in parts:
        if part.endswith(".") or part.endswith(" "):
            return True
        if ":" in part:
            return True
    return False


def normalize_rel(p):
    return p.replace("\\", "/")


def import_root_is_absolute(rel):
    if not isinstance(rel, str):
        return False
    s = rel.replace("\\", "/")
    if s.startswith("/"):
        return True
    if len(s) >= 2 and s[1] == ":":
        return True
    return os.path.isabs(rel)


def validate_import_roots(data, workspace, checkpoint, commit):
    if "import_roots" not in data:
        return []
    ir = data["import_roots"]
    if not isinstance(ir, list):
        raise Refuse("mutation-run: import_roots must be a list of strings")
    out = []
    for entry in ir:
        if not isinstance(entry, str):
            raise Refuse("mutation-run: import_roots must be a list of strings")
        rel = normalize_rel(entry)
        if import_root_is_absolute(rel):
            raise Refuse("mutation-run: import_roots entry must be relative, not absolute (%r)" % entry)
        if path_bad(rel):
            if ".." in rel.replace("\\", "/").split("/"):
                raise Refuse(
                    "mutation-run: import_roots entry %r leaves the Workspace" % entry)
            raise Refuse("mutation-run: import_roots entry %r is not a valid path" % entry)
        parts = [p for p in rel.split("/") if p]
        cur = os.path.abspath(workspace)
        for part in parts:
            cur = os.path.join(cur, part)
            try:
                st = os.lstat(cur)
            except FileNotFoundError:
                break
            except NotADirectoryError:
                break
            except (OSError, ValueError):
                raise Refuse("mutation-run: import_roots entry %r passes through a link" % entry)
            if stat.S_ISLNK(st.st_mode) or getattr(st, "st_reparse_tag", 0):
                raise Refuse("mutation-run: import_roots entry %r passes through a link" % entry)
        full = os.path.join(workspace, rel.replace("/", os.sep))
        if not checkpoint:
            if not os.path.isdir(full):
                if os.path.lexists(full):
                    raise Refuse(
                        "mutation-run: import_roots entry %r is not a folder" % entry)
                raise Refuse("mutation-run: import_roots entry %r is not in the working tree" % entry)
        out.append(rel)
    return out


def module_dotted_prefixes(import_roots_norm, mapped_roots_norm):
    prefixes = list(DEFAULT_DOTTED_PREFIXES)
    seen = set(prefixes)
    for r in import_roots_norm + mapped_roots_norm:
        rp = normalize_rel(r)
        if rp == ".":
            continue
        if not rp.endswith("/"):
            rp = rp + "/"
        if rp not in seen:
            prefixes.append(rp)
            seen.add(rp)
    return prefixes


def active_import_roots(tree_root, import_roots_norm):
    active = []
    for rel in import_roots_norm:
        p = os.path.join(tree_root, rel.replace("/", os.sep))
        if not os.path.isdir(p):
            continue
        active.append(rel)
    return active


def active_mapped_roots(tree_root, mapped_roots_norm):
    active = []
    for rel in mapped_roots_norm:
        if rel == ".":
            continue
        p = os.path.join(tree_root, rel.replace("/", os.sep))
        if os.path.isdir(p):
            active.append(rel)
    return active


def map_probe_entries(probe_paths, workspace, copy_root):
    mapped = []
    try:
        wr = os.path.realpath(os.path.abspath(workspace))
    except OSError:
        return mapped
    nwr = os.path.normcase(wr)
    for raw in probe_paths:
        if not isinstance(raw, str) or not raw:
            continue
        try:
            ar = os.path.realpath(os.path.abspath(raw))
        except (OSError, TypeError, ValueError):
            continue
        nar = os.path.normcase(ar)
        if nar != nwr and not nar.startswith(nwr + os.sep):
            continue
        if nar == nwr:
            wrel = "."
        else:
            try:
                wrel = os.path.relpath(ar, wr).replace("\\", "/")
            except ValueError:
                continue
        if wrel == ".":
            cp = copy_root
        else:
            cp = os.path.join(copy_root, wrel.replace("/", os.sep))
        if not path_under_or_equal(cp, copy_root):
            continue
        if wrel not in mapped:
            mapped.append(wrel)
    return mapped


def run_interpreter_path_probe(plugin_dir, tree_root, env, timeout_sec):
    probe_env = pytest_env(plugin_dir, tree_root, env)
    cmd = interpreter_argv() + ["-c", "import sys; print(repr(sys.path))"]
    try:
        rc, out, err, timed = run_process(cmd, probe_env, tree_root, timeout_sec)
    except OSError:
        return []
    if timed or rc != 0:
        return []
    try:
        if isinstance(out, bytes):
            text = out.decode("utf-8", "replace")
        else:
            text = out or ""
        paths = ast.literal_eval(text.strip())
    except (ValueError, SyntaxError, MemoryError, RecursionError, TypeError):
        return []
    if not isinstance(paths, list):
        return []
    for p in paths:
        if not isinstance(p, str):
            return []
    return paths


def run_paths(plugin_dir, copy_root, workspace, import_roots, env, timeout_sec):
    probe_paths = run_interpreter_path_probe(plugin_dir, copy_root, env, timeout_sec)
    mapped_all = map_probe_entries(probe_paths, workspace, copy_root)
    mapped_active = active_mapped_roots(copy_root, mapped_all)
    ir_active = active_import_roots(copy_root, import_roots)
    dotted_ps = module_dotted_prefixes(ir_active, mapped_active)
    path_kw = dict(
        import_roots_rel=ir_active, mapped_roots_rel=mapped_active, dotted_prefixes=dotted_ps)
    return ir_active, mapped_active, path_kw


def mutants_file_ok(workspace, path):
    try:
        rel = os.path.relpath(os.path.abspath(path), workspace).replace("\\", "/")
    except ValueError:
        raise Refuse("mutation-run: mutants file must be run/supervisor/<id>-mutants.json")
    if not rel.startswith("run/supervisor/") or not rel.endswith("-mutants.json"):
        raise Refuse("mutation-run: mutants file must be run/supervisor/<id>-mutants.json")
    base = os.path.basename(rel)
    run_id = base[: -len("-mutants.json")]
    if ".." in run_id or not MUTANT_ID_RX.match(run_id):
        raise Refuse("mutation-run: mutants file name is not a valid run id")
    return run_id


def link_on_path(path, stop=None):
    cur = os.path.abspath(path)
    stop_abs = os.path.abspath(stop) if stop else None
    while True:
        if bridge_env.is_link(cur):
            return True
        if stop_abs is not None and os.path.normcase(cur) == os.path.normcase(stop_abs):
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return False


def refuse_links_under(workspace, rel):
    full = os.path.join(workspace, rel.replace("/", os.sep))
    if os.path.isfile(full):
        if bridge_env.is_link(full):
            raise Refuse("mutation-run: %s is a link" % rel)
        return
    if not os.path.isdir(full):
        return
    for dirpath, dirnames, filenames in os.walk(full, followlinks=False):
        for name in dirnames + filenames:
            p = os.path.join(dirpath, name)
            if bridge_env.is_link(p):
                r = os.path.relpath(p, workspace).replace("\\", "/")
                raise Refuse("mutation-run: %s is a link" % r)


def validate_tracked_copy(workspace, tracked_list):
    for rel in tracked_list:
        full = os.path.join(workspace, rel)
        if not os.path.lexists(full):
            continue
        parts = rel.replace("\\", "/").split("/")
        cur = workspace
        for part in parts:
            cur = os.path.join(cur, part)
            if os.path.lexists(cur) and bridge_env.is_link(cur):
                raise Refuse("mutation-run: %s is a link" % rel)
    env_src = os.path.join(workspace, ".env")
    if os.path.lexists(env_src) and bridge_env.is_link(env_src):
        raise Refuse("mutation-run: .env is a link")


def assert_worktree_top(workspace):
    top = git_try("rev-parse", "--show-toplevel", cwd=workspace)
    if top is None:
        raise Refuse("mutation-run: not inside a git work tree")
    top_n = os.path.normcase(os.path.realpath(top.strip()))
    ws_n = os.path.normcase(os.path.realpath(os.path.abspath(workspace)))
    if top_n != ws_n:
        raise Refuse("mutation-run: cwd is not the top of the git work tree")


def refuse_cache_links(workspace):
    for part in ("run", "run/supervisor", "run/supervisor/mutation-cache"):
        p = os.path.join(workspace, part)
        if os.path.lexists(p) and bridge_env.is_link(p):
            raise Refuse("mutation-run: %s is a link" % part.replace("\\", "/"))


def parse_mutant_timeout(raw):
    try:
        v = int(raw)
    except (TypeError, ValueError):
        raise Refuse("mutation-run: --mutant-timeout must be a positive integer")
    if v <= 0:
        raise Refuse("mutation-run: --mutant-timeout must be a positive integer")
    return v


def load_mutants(path, checkpoint, workspace, commit=None):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise Refuse("mutation-run: invalid JSON in mutants file (%s)" % e)
    if not isinstance(data, dict):
        raise Refuse("mutation-run: mutants file must be a JSON object")
    allowed = {"mutants", "new_tests", "untracked", "import_roots"}
    for k in data:
        if k not in allowed:
            raise Refuse("mutation-run: unknown field %r in mutants file" % k)
    import_roots = validate_import_roots(data, workspace, checkpoint, commit)
    mutants = data.get("mutants")
    if mutants is None:
        raise Refuse("mutation-run: missing field mutants")
    if not isinstance(mutants, list):
        raise Refuse("mutation-run: mutants must be a list")
    if not mutants and not checkpoint:
        raise Refuse("mutation-run: mutants list is empty without --checkpoint")
    seen = set()
    parsed = []
    for i, m in enumerate(mutants):
        if not isinstance(m, dict):
            raise Refuse("mutation-run: mutant %d is not an object" % i)
        for req in ("id", "file", "pairs", "tests", "expect_fail"):
            if req not in m:
                raise Refuse("mutation-run: mutant %r missing field %s" % (m.get("id"), req))
        mid = m["id"]
        if not isinstance(mid, str) or not mid:
            raise Refuse("mutation-run: mutant id must be a non-empty string")
        if not MUTANT_ID_RX.fullmatch(mid):
            raise Refuse("mutation-run: mutant id %r is not a valid plain name" % mid)
        if mid in seen:
            raise Refuse("mutation-run: duplicate mutant id %r" % mid)
        seen.add(mid)
        fpath = m["file"]
        if not isinstance(fpath, str):
            raise Refuse("mutation-run: mutant %r file must be a string" % mid)
        fpath = normalize_rel(fpath)
        if path_bad(fpath):
            raise Refuse("mutation-run: mutant %r file path is not relative" % mid)
        pairs = m["pairs"]
        if not isinstance(pairs, list) or not pairs:
            raise Refuse("mutation-run: mutant %r pairs must be a non-empty list" % mid)
        for j, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "old" not in pair or "new" not in pair:
                raise Refuse("mutation-run: mutant %r pair %d is malformed" % (mid, j))
            if not isinstance(pair["old"], str) or not pair["old"]:
                raise Refuse("mutation-run: mutant %r pair %d old must be non-empty" % (mid, j))
            if not isinstance(pair["new"], str):
                raise Refuse("mutation-run: mutant %r pair %d new must be a string" % (mid, j))
        tests = m["tests"]
        if not isinstance(tests, list) or not tests:
            raise Refuse("mutation-run: mutant %r tests must be a non-empty list" % mid)
        norm_tests = []
        for t in tests:
            if not isinstance(t, str):
                raise Refuse("mutation-run: mutant %r tests entries must be strings" % mid)
            t = normalize_rel(t)
            if path_bad(t):
                raise Refuse("mutation-run: mutant %r test path is not relative" % mid)
            norm_tests.append(t)
        tests = norm_tests
        ef = m["expect_fail"]
        if not isinstance(ef, list) or not ef:
            raise Refuse("mutation-run: mutant %r expect_fail must be a non-empty list" % mid)
        for tid in ef:
            if not isinstance(tid, str):
                raise Refuse("mutation-run: mutant %r expect_fail entries must be strings" % mid)
        survive = None
        if "expect" in m:
            exp = m["expect"]
            if not isinstance(exp, str) or not exp.startswith("survive "):
                raise Refuse("mutation-run: mutant %r expect must start with survive " % mid)
            reason = exp[8:]
            if not reason:
                raise Refuse("mutation-run: mutant %r survive reason is empty" % mid)
            survive = reason
        parsed.append({
            "id": mid, "file": fpath, "pairs": pairs, "tests": tests,
            "expect_fail": list(ef), "survive": survive,
        })
    new_tests = data.get("new_tests")
    if new_tests is not None:
        if not isinstance(new_tests, list):
            raise Refuse("mutation-run: new_tests must be a list")
        nt = []
        for item in new_tests:
            if not isinstance(item, str):
                raise Refuse("mutation-run: new_tests entries must be strings")
            nt.append(item)
        new_tests = nt
    untracked = data.get("untracked")
    if untracked is not None:
        if not isinstance(untracked, list):
            raise Refuse("mutation-run: untracked must be a list")
        ut = []
        for u in untracked:
            if not isinstance(u, str):
                raise Refuse("mutation-run: untracked entries must be strings")
            u = normalize_rel(u)
            if path_bad(u):
                raise Refuse("mutation-run: untracked path is not relative")
            ut.append(u)
        untracked = ut
    for m in parsed:
        test_files = set(m["tests"])
        for tid in m["expect_fail"]:
            if "::" not in tid:
                raise Refuse("mutation-run: mutant %r expect_fail id %r is malformed" % (m["id"], tid))
            fpart = normalize_rel(tid.split("::", 1)[0])
            if fpart not in test_files:
                raise Refuse(
                    "mutation-run: mutant %r expect_fail id %r is not in one of its tests files"
                    % (m["id"], tid))
    return parsed, new_tests, untracked or [], import_roots


def validate_tracked(paths, workspace, tracked_set, label):
    for p in paths:
        if p not in tracked_set:
            raise Refuse(
                "mutation-run: %s %r is not in the git index (stage new test files first)" % (label, p))


def path_under_or_equal(child, parent):
    child_n = os.path.normcase(os.path.realpath(os.path.abspath(child)))
    parent_n = os.path.normcase(os.path.realpath(os.path.abspath(parent)))
    if child_n == parent_n:
        return True
    try:
        return os.path.commonpath([child_n, parent_n]) == parent_n
    except ValueError:
        return False


def paths_overlap_workspace(a, b):
    a_n = os.path.normcase(os.path.realpath(os.path.abspath(a)))
    b_n = os.path.normcase(os.path.realpath(os.path.abspath(b)))
    if a_n == b_n:
        return True
    try:
        if os.path.commonpath([a_n, b_n]) == a_n:
            return True
        if os.path.commonpath([a_n, b_n]) == b_n:
            return True
    except ValueError:
        pass
    return False


def _samefile_or_identity(a, b):
    try:
        return os.path.samefile(a, b)
    except OSError:
        try:
            sa, sb = os.stat(a), os.stat(b)
            return sa.st_dev == sb.st_dev and sa.st_ino == sb.st_ino
        except OSError:
            return False


def _scratch_arg_forbidden(raw):
    if not raw:
        return False
    norm = raw.replace("/", os.sep)
    if norm.startswith("\\\\?\\") or norm.startswith("\\\\.\\"):
        return True
    if norm.startswith("\\\\"):
        return True
    return False


def _scratch_overlaps_workspace_identity(scratch, workspace):
    ws = os.path.abspath(workspace)
    sc = os.path.abspath(scratch)
    if os.path.lexists(sc) and os.path.lexists(ws) and _samefile_or_identity(sc, ws):
        return True
    cur = sc
    while True:
        if os.path.lexists(cur) and os.path.lexists(ws) and _samefile_or_identity(cur, ws):
            return True
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    cur = ws
    while True:
        if os.path.lexists(cur) and os.path.lexists(sc) and _samefile_or_identity(cur, sc):
            return True
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return paths_overlap_workspace(scratch, workspace)


def _untracked_reaches_git(full, workspace):
    git_p = os.path.join(workspace, ".git")
    if not os.path.lexists(git_p):
        return False
    try:
        if os.path.lexists(full) and _samefile_or_identity(full, git_p):
            return True
        cur = os.path.normpath(full)
        ws = os.path.abspath(workspace)
        while True:
            if os.path.lexists(cur) and _samefile_or_identity(cur, git_p):
                return True
            if os.path.normcase(cur) == os.path.normcase(ws):
                break
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    except OSError:
        raise Refuse("mutation-run: untracked path is not allowed")
    return False


def validate_untracked(untracked, workspace):
    ws = os.path.abspath(workspace)
    for u in untracked:
        full = os.path.normpath(os.path.join(workspace, u))
        if not path_under_or_equal(full, ws):
            raise Refuse("mutation-run: untracked %r lies outside the Workspace" % u)
        if _untracked_reaches_git(full, workspace):
            raise Refuse("mutation-run: untracked %r reaches .git" % u)
        if link_on_path(full, stop=ws):
            raise Refuse("mutation-run: untracked %r is reached through a link" % u)
        if os.path.isdir(full):
            refuse_links_under(workspace, u)
        elif bridge_env.is_link(full):
            raise Refuse("mutation-run: untracked %r is a link" % u)


def default_scratch(workspace, env):
    home = bridge_env.real_home(env)
    parent = os.path.basename(os.path.dirname(os.path.abspath(workspace)))
    return os.path.join(home, ".cursor-bridge", "scratch", parent)


def validate_scratch(scratch, workspace, run_id):
    if _scratch_arg_forbidden(scratch):
        raise Refuse("mutation-run: scratch folder must not lie inside the Workspace or contain it")
    scratch = os.path.abspath(scratch)
    ws = os.path.abspath(workspace)
    if _scratch_overlaps_workspace_identity(scratch, ws):
        raise Refuse("mutation-run: scratch folder must not lie inside the Workspace or contain it")
    if link_on_path(scratch):
        raise Refuse("mutation-run: scratch path is reached through a link")
    sub = os.path.join(scratch, "mutation-run-" + run_id)
    if os.path.lexists(sub) and bridge_env.is_link(sub):
        raise Refuse("mutation-run: existing mutation-run-%s is a link" % run_id)
    return scratch, sub


def kill_tree(proc):
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            capture_output=True, creationflags=NO_WINDOW, stdin=subprocess.DEVNULL,
            timeout=30,
        )
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            proc.kill()


_last_run_process_still_alive = False


def run_process_still_alive_after_timeout():
    return _last_run_process_still_alive


def run_process(argv, env, cwd, timeout_sec):
    global _last_run_process_still_alive
    _last_run_process_still_alive = False
    if sys.platform == "win32":
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                creationflags=NO_WINDOW)
    else:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                creationflags=NO_WINDOW, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        try:
            out, err = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            out, err = b"", b""
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                pass
        _last_run_process_still_alive = proc.poll() is None
        return None, out, err, True
    return proc.returncode, out, err, False


def copy_tracked(workspace, dest, tracked, untracked):
    for rel in tracked:
        src = os.path.join(workspace, rel)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    env_src = os.path.join(workspace, ".env")
    if os.path.isfile(env_src):
        shutil.copy2(env_src, os.path.join(dest, ".env"))
    for u in untracked:
        src = os.path.join(workspace, u)
        dst = os.path.join(dest, u)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst, symlinks=False)
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    remove_bytecode_from_copy(dest)


def remove_bytecode_from_copy(copy_root):
    for dirpath, dirnames, filenames in os.walk(copy_root, topdown=True, followlinks=False):
        for i in range(len(dirnames) - 1, -1, -1):
            if dirnames[i] == "__pycache__":
                p = os.path.join(dirpath, dirnames[i])
                if not bridge_env.is_link(p):
                    shutil.rmtree(p)
                del dirnames[i]


def extract_archive_tar(tar_bytes, dest):
    import io
    dest = os.path.abspath(dest)
    dest_prefix = dest + os.sep
    tf = tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:")
    try:
        members = tf.getmembers()
        for member in members:
            name = member.name
            if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
                raise Refuse("mutation-run: archive member %r is not relative" % name)
            if "\\" in name or ":" in name:
                raise Refuse("mutation-run: archive member %r is not relative" % name)
            parts = name.replace("\\", "/").split("/")
            if ".." in parts or not parts[0]:
                raise Refuse("mutation-run: archive member %r is not relative" % name)
            target = os.path.normpath(os.path.join(dest, name))
            if not (target == dest or target.startswith(dest_prefix)):
                raise Refuse("mutation-run: archive member %r escapes the copy" % name)
            if member.issym() or member.islnk():
                raise Refuse("mutation-run: git archive member is a link")
            if not (member.isdir() or member.isreg()):
                raise Refuse("mutation-run: archive member %r is not a file or folder" % name)
        for member in members:
            if member.isdir():
                os.makedirs(os.path.join(dest, member.name), exist_ok=True)
                continue
            target = os.path.join(dest, member.name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            extracted = tf.extractfile(member)
            if extracted:
                with open(target, "wb") as out:
                    shutil.copyfileobj(extracted, out)
    finally:
        tf.close()


def archive_checkpoint(workspace, commit, dest, new_tests, untracked):
    data = git("archive", "--format=tar", commit, cwd=workspace, binary=True)
    extract_archive_tar(data, dest)
    copied_conftest = set()
    for item in new_tests or []:
        if "::" in item:
            fpart = item.split("::", 1)[0]
        else:
            fpart = item
        fpart = normalize_rel(fpart)
        src = os.path.join(workspace, fpart)
        if os.path.isfile(src):
            dst = os.path.join(dest, fpart)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        ws_abs = os.path.abspath(workspace)
        for cp in conftest_paths(fpart):
            if cp in copied_conftest:
                continue
            conf_src = os.path.join(workspace, cp)
            if os.path.lexists(conf_src):
                if link_on_path(conf_src, stop=ws_abs):
                    raise Refuse("mutation-run: %r is reached through a link" % cp)
                if os.path.isfile(conf_src):
                    conf_dst = os.path.join(dest, cp)
                    os.makedirs(os.path.dirname(conf_dst), exist_ok=True)
                    shutil.copy2(conf_src, conf_dst)
                    copied_conftest.add(cp)
    env_src = os.path.join(workspace, ".env")
    if os.path.isfile(env_src):
        shutil.copy2(env_src, os.path.join(dest, ".env"))
    for u in untracked:
        src = os.path.join(workspace, u)
        dst = os.path.join(dest, u)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst, symlinks=False)
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    remove_bytecode_from_copy(dest)
    return copied_conftest


def dotted_module_paths(rel, dotted_prefixes=None):
    rel = normalize_rel(rel)
    out = []
    for prefix in dotted_prefixes or DEFAULT_DOTTED_PREFIXES:
        if prefix and not rel.startswith(prefix):
            continue
        rest = rel[len(prefix):] if prefix else rel
        if not rest.endswith(".py"):
            continue
        modpath = rest[:-3]
        if not modpath:
            continue
        parts = modpath.split("/")
        if all(p.isidentifier() for p in parts):
            name = ".".join(parts)
            if name not in out:
                out.append(name)
    return out


def conftest_paths(test_file):
    parts = test_file.replace("\\", "/").split("/")
    paths = ["conftest.py"]
    for i in range(len(parts) - 1):
        paths.append("/".join(parts[: i + 1]) + "/conftest.py")
    return paths


def key_file_set(mutant, workspace, tracked_set):
    rels = set()
    mdir = os.path.dirname(mutant["file"])
    if mdir:
        for t in tracked_set:
            if t == mutant["file"] or t.startswith(mdir + "/"):
                rels.add(t)
    else:
        rels.update(tracked_set)
    for tf in mutant["tests"]:
        tdir = os.path.dirname(tf)
        if tdir:
            for t in tracked_set:
                if t == tf or t.startswith(tdir + "/"):
                    rels.add(t)
        else:
            rels.update(tracked_set)
        for cf in conftest_paths(tf):
            if cf in tracked_set:
                rels.add(cf)
    for cfg in (
        "conftest.py", "pytest.toml", ".pytest.toml", "pytest.ini", ".pytest.ini",
        "pyproject.toml", "setup.cfg", "tox.ini",
    ):
        if cfg in tracked_set:
            rels.add(cfg)
    return sorted(rels)


def key_bytes(tree_root, rels):
    parts = []
    for rel in rels:
        path = os.path.join(tree_root, rel)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as f:
            data = f.read()
        rb = rel.encode("utf-8")
        parts.append(struct.pack(">Q", len(rb)))
        parts.append(rb)
        parts.append(struct.pack(">Q", len(data)))
        parts.append(data)
    return b"".join(parts)


def mutant_key_part(mutant):
    payload = {
        "file": mutant["file"],
        "tests": mutant["tests"],
        "pairs": mutant["pairs"],
        "expect_fail": mutant["expect_fail"],
        "survive": mutant["survive"] is not None,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_path_key_part(import_roots_norm, mapped_roots_norm):
    payload = {
        "import_roots": list(import_roots_norm),
        "mapped_roots": list(mapped_roots_norm),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_key(tree_root, mutant, tracked_set, import_roots_norm=(), mapped_roots_norm=()):
    rels = key_file_set(mutant, tree_root, tracked_set)
    h = hashlib.sha256()
    h.update(key_bytes(tree_root, rels))
    rk = run_path_key_part(import_roots_norm, mapped_roots_norm)
    h.update(struct.pack(">Q", len(rk)))
    h.update(rk)
    mp = mutant_key_part(mutant)
    h.update(struct.pack(">Q", len(mp)))
    h.update(mp)
    return h.hexdigest()


def validate_cache_file(cache_path):
    if not os.path.lexists(cache_path):
        return
    rel = "run/supervisor/mutation-cache/" + os.path.basename(cache_path)
    if bridge_env.is_link(cache_path):
        raise Refuse("mutation-run: %s is a link" % rel)
    if os.path.isfile(cache_path) and os.stat(cache_path).st_nlink > 1:
        raise Refuse("mutation-run: %s is a link" % rel)


def read_cache(cache_path):
    validate_cache_file(cache_path)
    entries = {}
    if not os.path.isfile(cache_path):
        return entries
    with open(cache_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                mid, key, outcome, ts = rec["mutant"], rec["key"], rec["outcome"], rec["time"]
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
            entries[(mid, key)] = (outcome, ts)
    return entries


def append_cache(cache_path, mid, key, outcome):
    validate_cache_file(cache_path)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    rec = {
        "mutant": mid,
        "key": key,
        "outcome": outcome,
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(cache_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())


def normalize_pair_text(s, crlf):
    s = s.replace("\r\n", "\n")
    if crlf:
        return s.replace("\n", "\r\n")
    return s


def apply_mutant(copy_root, mutant):
    path = os.path.join(copy_root, mutant["file"])
    if not os.path.isfile(path):
        return False
    with open(path, "rb") as f:
        original = f.read()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError:
        return False
    crlf = b"\r\n" in original
    norm_orig = text.replace("\r\n", "\n")
    for pair in mutant["pairs"]:
        if norm_orig.count(pair["old"].replace("\r\n", "\n")) != 1:
            return False
    for pair in mutant["pairs"]:
        old = normalize_pair_text(pair["old"], crlf)
        new = normalize_pair_text(pair["new"], crlf)
        text = text.replace(old, new, 1)
    nl = "\r\n" if crlf else "\n"
    out = text.replace("\r\n", "\n").replace("\n", nl) if crlf else text
    with open(path, "wb") as f:
        f.write(out.encode("utf-8"))
    return True


def restore_mutant(copy_root, mutant, original_bytes):
    path = os.path.join(copy_root, mutant["file"])
    with open(path, "wb") as f:
        f.write(original_bytes)


def read_original(copy_root, mutant):
    path = os.path.join(copy_root, mutant["file"])
    with open(path, "rb") as f:
        return f.read()


def ensure_outcomes_plugin(plugin_dir):
    path = os.path.join(plugin_dir, OUTCOMES_PLUGIN_NAME)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(OUTCOMES_PLUGIN_CODE)
    return path


_PYTEST_CONFIG_NAMES = (
    "pytest.toml", ".pytest.toml", "pytest.ini", ".pytest.ini",
    "pyproject.toml", "tox.ini", "setup.cfg",
)

_INICONFIG_SHADOW_REFUSE = (
    "mutation-run: a top-level iniconfig in the project would shadow pytest's iniconfig"
)

_PYTEST_CONFIG_SHADOW_MODULES = (
    "pytest", "_pytest", "pluggy", "py", "iniconfig", "tomllib", "tomli",
)


def _refuse_if_copy_root_shadows_iniconfig(config_dir):
    for entry in os.listdir(config_dir):
        if os.name == "nt":
            low = entry.lower()
            if low == "iniconfig" or low.startswith("iniconfig."):
                raise Refuse(_INICONFIG_SHADOW_REFUSE)
        elif entry == "iniconfig" or entry.startswith("iniconfig."):
            raise Refuse(_INICONFIG_SHADOW_REFUSE)


def _pytest_config_dict_from_file(filepath):
    name = os.path.basename(filepath)
    suffix = os.path.splitext(name)[1]
    if suffix == ".ini":
        _refuse_if_copy_root_shadows_iniconfig(os.path.dirname(filepath))
        try:
            import iniconfig
        except ImportError:
            raise Refuse("mutation-run: pytest's iniconfig is not importable")
        try:
            ini = iniconfig.IniConfig(str(filepath))
            if name in ("pytest.ini", ".pytest.ini"):
                if "pytest" in ini:
                    return {k: v for k, v in ini["pytest"].items()}
                return {}
            if name == "tox.ini":
                if "pytest" not in ini:
                    return None
                return {k: v for k, v in ini["pytest"].items()}
            return None
        except (iniconfig.ParseError, UnicodeDecodeError):
            raise Refuse("mutation-run: invalid ini file %s" % name)
    if suffix == ".cfg":
        _refuse_if_copy_root_shadows_iniconfig(os.path.dirname(filepath))
        try:
            import iniconfig
        except ImportError:
            raise Refuse("mutation-run: pytest's iniconfig is not importable")
        try:
            ini = iniconfig.IniConfig(str(filepath))
            if "tool:pytest" not in ini.sections:
                return None
            return {k: v for k, v in ini["tool:pytest"].items()}
        except (iniconfig.ParseError, UnicodeDecodeError):
            raise Refuse("mutation-run: invalid cfg file %s" % name)
    if suffix == ".toml":
        try:
            with open(filepath, "rb") as f:
                config = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise Refuse("mutation-run: invalid toml file %s (%s)" % (name, e))
        if name in ("pytest.toml", ".pytest.toml"):
            pytest_config = config.get("pytest", {})
            if pytest_config:
                return dict(pytest_config)
            return {}
        tool_pytest = config.get("tool", {}).get("pytest", {})
        toml_config = {k: v for k, v in tool_pytest.items() if k != "ini_options"}
        ini_config = tool_pytest.get("ini_options")
        if toml_config and ini_config is not None:
            raise Refuse("mutation-run: pyproject.toml has conflicting pytest tables")
        if toml_config:
            return dict(toml_config)
        if ini_config is not None:
            return dict(ini_config)
        return None
    return None


def _refuse_if_copy_root_shadows_importable_module(copy_root):
    suffixes = importlib.machinery.all_suffixes()
    if os.name == "nt":
        shadow_names = frozenset(n.lower() for n in _PYTEST_CONFIG_SHADOW_MODULES)
    else:
        shadow_names = frozenset(_PYTEST_CONFIG_SHADOW_MODULES)
    for entry in os.listdir(copy_root):
        path = os.path.join(copy_root, entry)
        names = []
        if os.path.isfile(path):
            for suf in suffixes:
                if entry.endswith(suf) and len(entry) > len(suf):
                    mod = entry[: -len(suf)]
                    if mod.isidentifier():
                        names.append(mod)
        elif os.path.isdir(path):
            for suf in suffixes:
                if os.path.isfile(os.path.join(path, "__init__" + suf)):
                    if entry.isidentifier():
                        names.append(entry)
                    break
        for mod in names:
            if not mod.isidentifier():
                continue
            key = mod.lower() if os.name == "nt" else mod
            if key not in shadow_names:
                continue
            if mod == "iniconfig" or (os.name == "nt" and mod.lower() == "iniconfig"):
                raise Refuse(_INICONFIG_SHADOW_REFUSE)
            raise Refuse(
                "mutation-run: a top-level module %s in the project would shadow "
                "an installed or standard-library module" % mod
            )


def copy_pytest_config_file(copy_root):
    _refuse_if_copy_root_shadows_importable_module(copy_root)
    for name in _PYTEST_CONFIG_NAMES:
        p = os.path.join(copy_root, name)
        if not os.path.isfile(p):
            continue
        cfg = _pytest_config_dict_from_file(p)
        if cfg is not None:
            return p
    return None


def pytest_config_argv(plugin_dir, copy_root):
    cfg_file = copy_pytest_config_file(copy_root)
    if cfg_file is None:
        cfg_file = os.path.join(plugin_dir, "pytest-empty.ini")
        if not os.path.isfile(cfg_file):
            with open(cfg_file, "wb"):
                pass
    return ["-c", cfg_file, "--rootdir", copy_root]


def read_pytest_results(results_path):
    if not os.path.isfile(results_path):
        return None
    try:
        with open(results_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not data.get("session_finished"):
        return None
    return data


def outcome_map_from_results(data):
    statuses = {}
    for rec in data.get("tests", []):
        nid = rec.get("nodeid")
        out = rec.get("outcome")
        if not nid or not out:
            continue
        if out == "failed":
            statuses[nid] = "FAILED"
        elif out == "error":
            statuses[nid] = "ERROR"
        elif out == "passed":
            statuses[nid] = "PASSED"
        elif out == "skipped":
            statuses[nid] = "SKIPPED"
    return statuses


def classify_outcome(data, expect_fail, timed_out):
    if timed_out:
        return "error", "timed out"
    if data is None:
        return "error", "no pytest result"
    if data.get("collect_errors"):
        return "error", "collection error"
    statuses = outcome_map_from_results(data)
    ef_set = set(expect_fail)
    reported = set(statuses)
    for tid in ef_set:
        if tid not in reported:
            return "error", "expected id absent"
    for tid, st in statuses.items():
        if st == "ERROR":
            return "error", "test error"
        if st == "FAILED" and tid not in ef_set:
            return "error", "unexpected failure"
    for tid in expect_fail:
        if statuses.get(tid) == "FAILED":
            return "killed", None
    return "survived", None


def checkpoint_label_for_test(nodeid, outcome):
    if outcome == "passed":
        return "passing on old code"
    if outcome in ("failed", "error"):
        return "failing"
    return "not run"


def checkpoint_records_for_item(item, tests_run):
    out = []
    for rec in tests_run:
        nid = rec.get("nodeid")
        if not nid:
            continue
        if nid == item or nid.startswith(item + "[") or nid.startswith(item + "::"):
            out.append(rec)
    return out


def write_resolution_plugin(plugin_dir, copy_root, mutated_files, workspace_tracked, workspace_abs, dotted_prefixes):
    out_json = os.path.join(plugin_dir, "_resolution_out.json")
    try:
        workspace_real = os.path.realpath(os.path.abspath(workspace_abs))
    except OSError:
        workspace_real = os.path.abspath(workspace_abs)
    code = '''import json
import os
import sys

MUTATED = %s
TRACKED = set(%s)
DOTTED_PREFIXES = %s
OUT = %r
ROOT = os.getcwd()
WORKSPACE = %r
WORKSPACE_REAL = %r

def _dotted(rel):
    rel = rel.replace("\\\\", "/")
    for prefix in DOTTED_PREFIXES:
        if prefix and not rel.startswith(prefix):
            continue
        rest = rel[len(prefix):] if prefix else rel
        if not rest.endswith(".py"):
            continue
        modpath = rest[:-3]
        if not modpath:
            continue
        parts = modpath.split("/")
        if all(p.isidentifier() for p in parts):
            yield ".".join(parts)

loaded_ws = []
path_ahead = []
resolved = {}

def pytest_configure(config):
    import importlib
    import importlib.util
    croot = os.path.abspath(ROOT)
    for mf in MUTATED:
        for modname in _dotted(mf):
            try:
                spec = importlib.util.find_spec(modname)
                if spec is None:
                    resolved[modname] = None
                    continue
                if spec.origin is not None:
                    origin = os.path.abspath(spec.origin)
                    resolved[modname] = origin
                elif spec.submodule_search_locations:
                    for loc in spec.submodule_search_locations:
                        aloc = os.path.abspath(loc)
                        if not aloc.startswith(croot + os.sep) and aloc != croot:
                            resolved[modname] = aloc
                            break
            except Exception:
                pass

def _norm(p):
    return os.path.normcase(os.path.abspath(p))

def _under(ap, a, b):
    return ap == a or ap.startswith(a + os.sep) or ap == b or ap.startswith(b + os.sep)

def pytest_sessionfinish(session, exitstatus):
    import sys as _sys
    wroot = os.path.abspath(WORKSPACE)
    wroot_real = os.path.abspath(WORKSPACE_REAL)
    croot = os.path.abspath(ROOT)
    try:
        croot_real = os.path.realpath(croot)
    except OSError:
        croot_real = croot
    nw = _norm(wroot)
    nwr = _norm(wroot_real)
    nc = _norm(croot)
    ncr = _norm(croot_real)
    raw_path = []
    norm_path = []
    for p in _sys.path:
        raw_path.append(p)
        if not p:
            norm_path.append(None)
            continue
        try:
            norm_path.append(_norm(p))
        except (OSError, TypeError):
            norm_path.append(None)
    copy_indices = []
    for i, ap in enumerate(norm_path):
        if ap is None:
            continue
        if _under(ap, nc, ncr):
            copy_indices.append(i)
    min_copy = min(copy_indices) if copy_indices else None
    for i, ap in enumerate(norm_path):
        if ap is None:
            continue
        if _under(ap, nw, nwr):
            if min_copy is None or i < min_copy:
                path_ahead.append(raw_path[i])
    for name, mod in list(_sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        af = _norm(f)
        if not _under(af, nw, nwr):
            continue
        if _under(af, nc, ncr):
            continue
        for t in TRACKED:
            wp = _norm(os.path.join(wroot, t.replace("/", os.sep)))
            wpr = _norm(os.path.join(wroot_real, t.replace("/", os.sep)))
            if af == wp or af == wpr:
                loaded_ws.append({"module": name, "path": t})
                break
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"resolved": resolved, "loaded_ws": loaded_ws, "path_ahead": path_ahead}, f)
''' % (json.dumps([m["file"] for m in mutated_files]),
       json.dumps(sorted(workspace_tracked)),
       json.dumps(list(dotted_prefixes)),
       out_json.replace("\\", "/"),
       os.path.abspath(workspace_abs),
       workspace_real)
    path = os.path.join(plugin_dir, PLUGIN_NAME)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(code)
    return out_json


def pytest_env(plugin_dir, tree_root, env, results_path=None, import_roots_rel=(), mapped_roots_rel=()):
    parts = [plugin_dir]
    seen = set()
    for rel in list(import_roots_rel) + list(mapped_roots_rel):
        p = os.path.join(tree_root, rel.replace("/", os.sep))
        if os.path.isdir(p):
            ap = os.path.abspath(p)
            nk = os.path.normcase(ap)
            if nk not in seen:
                parts.append(ap)
                seen.add(nk)
    tr = os.path.abspath(tree_root)
    nk = os.path.normcase(tr)
    if nk not in seen:
        parts.append(tr)
    run_env = dict(env)
    run_env["PYTHONPATH"] = os.pathsep.join(parts)
    run_env["PYTHONDONTWRITEBYTECODE"] = "1"
    if results_path:
        run_env["MUTATION_PYTEST_RESULTS"] = results_path
    return run_env


def module_file_at_commit(workspace, commit, modname, dotted_prefixes=None):
    parts = modname.split(".")
    for prefix in dotted_prefixes or DEFAULT_DOTTED_PREFIXES:
        rel = prefix + "/".join(parts) + ".py"
        if git_try("cat-file", "-e", "%s:%s" % (commit, rel), cwd=workspace) is not None:
            return True
        pkg = prefix + "/".join(parts)
        if git_try("cat-file", "-e", "%s:%s/__init__.py" % (commit, pkg), cwd=workspace) is not None:
            return True
    return False


_CONFTEST_LOAD_RX = re.compile(r"ImportError while loading conftest '([^']+)'\.")


def _stderr_lines(err):
    if isinstance(err, bytes):
        text = err.decode("utf-8", "replace")
    elif err:
        text = err
    else:
        text = ""
    lines = []
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        lines.append(line)
    return lines


def _conftest_load_failure_path(err):
    abs_path = None
    for line in _stderr_lines(err):
        m = _CONFTEST_LOAD_RX.fullmatch(line)
        if m:
            abs_path = m.group(1)
    return abs_path


def conftest_changed_by_increment(workspace, commit, rel):
    listing = git_try("ls-tree", "-z", commit, "--", rel, cwd=workspace)
    if listing is None:
        return False
    if not listing:
        return True
    wt_path = os.path.join(workspace, rel.replace("/", os.sep))
    if not os.path.isfile(wt_path):
        return False
    wt_hash = git_try("hash-object", wt_path, cwd=workspace)
    commit_hash = git_try("rev-parse", "%s:%s" % (commit, rel), cwd=workspace)
    if wt_hash is None or commit_hash is None:
        return False
    return wt_hash != commit_hash


def copied_conftest_load_failure(copy_root, copied_conftest, workspace, commit, rc, err):
    if rc != 4 or not copied_conftest:
        return None
    abs_path = _conftest_load_failure_path(err)
    if not abs_path:
        return None
    try:
        rel = normalize_rel(os.path.relpath(abs_path, os.path.abspath(copy_root)))
    except ValueError:
        return None
    if rel not in copied_conftest:
        return None
    if not conftest_changed_by_increment(workspace, commit, rel):
        return None
    return rel


def _remove_resolution_plugin(plugin_dir):
    for name in (PLUGIN_NAME,):
        p = os.path.join(plugin_dir, name)
        if os.path.isfile(p):
            os.remove(p)


def checkpoint_collect_refused(workspace, commit, rc, err, out, new_tests, dotted_prefixes=None):
    if rc != 2 or not new_tests:
        return False
    parts = []
    for blob in (out, err):
        if isinstance(blob, bytes):
            parts.append(blob.decode("utf-8", "replace"))
        elif blob:
            parts.append(blob)
    text = "".join(parts)
    prefixes = dotted_prefixes or DEFAULT_DOTTED_PREFIXES
    for m in re.finditer(r"No module named '([^']+)'", text):
        mod = m.group(1)
        if module_file_at_commit(workspace, commit, mod, prefixes):
            return True
        top = mod.split(".")[0]
        for prefix in prefixes:
            if git_try("cat-file", "-e", "%s:%s/__init__.py" % (commit, prefix + top), cwd=workspace) is not None:
                if mod == top:
                    return True
            rel = prefix + top + ".py"
            if git_try("cat-file", "-e", "%s:%s" % (commit, rel), cwd=workspace) is not None:
                if mod == top:
                    return True
    return False


def run_resolution_check(plugin_dir, copy_root, mutants, test_files, workspace_tracked, workspace, env, timeout_sec,
                         checkpoint=False, checkpoint_commit=None, new_tests=None, copied_conftest=None,
                         import_roots_rel=(), mapped_roots_rel=(), dotted_prefixes=None):
    mutated_files = [{"file": m["file"]} for m in mutants]
    dp = dotted_prefixes or DEFAULT_DOTTED_PREFIXES
    out_json = write_resolution_plugin(
        plugin_dir, copy_root, mutated_files, workspace_tracked, workspace, dp)
    if os.path.isfile(out_json):
        os.remove(out_json)
    test_files = sorted(set(test_files))
    if not test_files:
        return None
    run_env = pytest_env(
        plugin_dir, copy_root, env, import_roots_rel=import_roots_rel, mapped_roots_rel=mapped_roots_rel)
    run_env["PY_COLORS"] = "0"
    run_env.pop("FORCE_COLOR", None)
    cfg = pytest_config_argv(plugin_dir, copy_root)
    argv = interpreter_argv() + ["-m", "pytest", "--collect-only", "-q",
                                 "-p", PLUGIN_MOD, "-p", "no:cacheprovider"] + cfg + test_files
    rc, out, err, timed = run_process(argv, run_env, copy_root, timeout_sec)
    if timed:
        raise ResolutionTimeout(timeout_sec)
    if checkpoint and checkpoint_collect_refused(
            workspace, checkpoint_commit, rc, err, out, new_tests, dp):
        raise Refuse("mutation-run: resolution check failed (pytest exit %d)" % rc)
    load_fail = None
    if checkpoint and copied_conftest is not None:
        load_fail = copied_conftest_load_failure(
            copy_root, copied_conftest, workspace, checkpoint_commit, rc, err)
    if load_fail:
        _remove_resolution_plugin(plugin_dir)
        return load_fail
    if rc not in (0, 2):
        raise Refuse("mutation-run: resolution check failed (pytest exit %d)" % rc)
    if not os.path.isfile(out_json):
        raise Refuse("mutation-run: resolution check produced no report")
    with open(out_json, encoding="utf-8") as f:
        report = json.load(f)
    croot_abs = os.path.abspath(copy_root) + os.sep
    for m in mutants:
        for modname in dotted_module_paths(m["file"], dp):
            origin = report.get("resolved", {}).get(modname)
            if not origin:
                if not checkpoint:
                    raise Refuse("mutation-run: module %s does not resolve inside the copy" % modname)
                continue
            if not os.path.abspath(origin).startswith(croot_abs):
                raise Refuse("mutation-run: module %s resolves outside the copy at %s" % (modname, origin))
    for mod, origin in report.get("resolved", {}).items():
        if origin is None:
            continue
        if not os.path.abspath(origin).startswith(croot_abs):
            raise Refuse("mutation-run: module %s resolves outside the copy at %s" % (mod, origin))
    for entry in report.get("path_ahead", []):
        raise Refuse(
            "mutation-run: import path entry %r stands ahead of the copy on the import path" % entry)
    for item in report.get("loaded_ws", []):
        if isinstance(item, dict):
            mod = item.get("module", "")
            place = item.get("path", "")
        else:
            mod = ""
            place = repr(item)
        raise Refuse(
            "mutation-run: module from Workspace path %s was loaded (module %s; an editable install of the "
            "project is the usual cause; use import_roots for a finder-style install)" % (place, mod))
    _remove_resolution_plugin(plugin_dir)
    return None


def mutant_cached_kill(cache, mutant, key, run_all):
    cached = cache.get((mutant["id"], key))
    return cached and cached[0] == "killed" and not run_all


def uncached_test_lists(mutants, cache, mutant_keys, run_all):
    found = []
    for m in mutants:
        if mutant_cached_kill(cache, m, mutant_keys[m["id"]], run_all):
            continue
        if m["tests"] not in found:
            found.append(m["tests"])
    return found


def baseline_failing_ids(data):
    found = []
    if not data:
        return found
    for rec in data.get("tests", []):
        nid = rec.get("nodeid")
        if nid and rec.get("outcome") in ("failed", "error") and nid not in found:
            found.append(nid)
    for nid in data.get("collect_errors", []):
        if nid and nid not in found:
            found.append(nid)
    return found


def baseline_failure(rc, data):
    ids = baseline_failing_ids(data)
    bad_rc = rc if rc not in (0, 1) else None
    failed = bool(ids) or bad_rc is not None or data is None or rc != 0
    return failed, ids, bad_rc


def format_baseline_failure(tests, failing_ids, bad_rc):
    head = "baseline failed"
    if bad_rc is not None:
        head = "baseline failed (pytest exit %d)" % bad_rc
    line = "%s: %s" % (head, " ".join(tests))
    if failing_ids:
        line = "%s: %s" % (line, " ".join(failing_ids))
    return line


def print_baseline_failures(failures):
    for tests, failing_ids, bad_rc in failures:
        print(format_baseline_failure(tests, failing_ids, bad_rc))


def run_baselines(plugin_dir, copy_root, lists, env, timeout_sec,
                  import_roots_rel=(), mapped_roots_rel=()):
    failures = []
    timed_out = []
    for i, tests in enumerate(lists):
        results_path = os.path.join(plugin_dir, "pytest-outcomes-base-%d.json" % i)
        rc, _out, _err, timed, alive, data = run_mutant_tests(
            plugin_dir, copy_root, tests, env, timeout_sec, results_path,
            import_roots_rel=import_roots_rel, mapped_roots_rel=mapped_roots_rel)
        if alive:
            return failures, timed_out, tests
        if timed:
            timed_out.append(tests)
            continue
        failed, ids, bad_rc = baseline_failure(rc, data)
        if failed:
            failures.append((tests, ids, bad_rc))
    return failures, timed_out, None


def run_mutant_tests(plugin_dir, copy_root, tests, env, timeout_sec, results_path,
                     import_roots_rel=(), mapped_roots_rel=()):
    if os.path.isfile(results_path):
        os.remove(results_path)
    run_env = pytest_env(
        plugin_dir, copy_root, env, results_path,
        import_roots_rel=import_roots_rel, mapped_roots_rel=mapped_roots_rel)
    cfg = pytest_config_argv(plugin_dir, copy_root)
    argv = interpreter_argv() + ["-m", "pytest", "-p", OUTCOMES_PLUGIN_MOD, "-p", "no:cacheprovider"] + cfg + tests
    rc, out, err, timed = run_process(argv, run_env, copy_root, timeout_sec)
    data = read_pytest_results(results_path)
    return rc, out, err, timed, run_process_still_alive_after_timeout(), data


def validate_checkpoint(commit, new_tests, workspace, tracked_set):
    if commit.startswith("-"):
        raise Refuse("mutation-run: checkpoint commit must not start with -")
    if git_try("rev-parse", "--verify", "--quiet", commit + "^{commit}", cwd=workspace) is None:
        raise Refuse("mutation-run: checkpoint %r does not resolve to a commit" % commit)
    if not new_tests:
        raise Refuse("mutation-run: --checkpoint requires non-empty new_tests")
    for item in new_tests:
        if "::" in item:
            fpart = normalize_rel(item.split("::", 1)[0])
        else:
            fpart = normalize_rel(item)
        if path_bad(fpart):
            raise Refuse("mutation-run: new_tests entry is not a valid path")
        if fpart not in tracked_set:
            raise Refuse("mutation-run: new_tests file %r is not in the git index" % fpart)
        if "::" not in item:
            if git_try("cat-file", "-e", "%s:%s" % (commit, fpart), cwd=workspace) is not None:
                raise Refuse(
                    "mutation-run: new_tests lists file %r which exists at the checkpoint; "
                    "list new tests by id" % fpart)


def checkpoint_new_test_items(new_tests):
    items = []
    for item in new_tests:
        if "::" in item:
            items.append(item)
        else:
            items.append(normalize_rel(item))
    return items


def build_parser():
    desc = (
        "Apply mutants from a JSON file in a scratch copy of the Workspace and run each mutant's "
        "tests with pytest. Usage: python mutation-run.py <mutants file> [--all] [--checkpoint <commit>] "
        "[--scratch <folder>] [--mutant-timeout <seconds>]. Default scratch is "
        "~/.cursor-bridge/scratch/<project>/. Exit 0 when every mutant is killed; 1 when any "
        "survived, was not applied, or an expect-survive mutant was killed; 2 for malformed input, "
        "refused paths, or failed resolution check; 3 when any mutant errored; 4 in --checkpoint "
        "mode when a listed new test passed on the old code; 5 when a tests list fails or errors "
        "on the unmutated code before any mutant runs. A mutant whose tests list times out on the "
        "unmutated code is an error and is not run."
    )
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("mutants_file", help="run/supervisor/<id>-mutants.json")
    ap.add_argument("--all", action="store_true", help="run every mutant, ignoring cached kills")
    ap.add_argument("--checkpoint", metavar="commit", help="run new_tests on code at commit")
    ap.add_argument("--scratch", default=None, help="scratch folder (default under ~/.cursor-bridge/scratch/)")
    ap.add_argument("--mutant-timeout", type=int, default=900, metavar="seconds",
                    help="per-mutant pytest timeout (default 900)")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.all and args.checkpoint:
        print("mutation-run: --all with --checkpoint is not allowed", file=sys.stderr)
        return 2
    timeout_sec = parse_mutant_timeout(args.mutant_timeout)
    workspace = os.getcwd()
    if git_try("rev-parse", "--is-inside-work-tree", cwd=workspace) is None:
        raise Refuse("mutation-run: not inside a git work tree")
    assert_worktree_top(workspace)
    refuse_cache_links(workspace)
    run_id = mutants_file_ok(workspace, args.mutants_file)
    commit_for_roots = args.checkpoint if args.checkpoint else None
    mutants, new_tests, untracked, import_roots = load_mutants(
        args.mutants_file, bool(args.checkpoint), workspace, commit_for_roots)
    tracked_list = ls_files_index(workspace)
    tracked_set = set(tracked_list)
    for m in mutants:
        validate_tracked([m["file"]] + m["tests"], workspace, tracked_set, "mutant")
    validate_untracked(untracked, workspace)
    if args.checkpoint:
        validate_checkpoint(args.checkpoint, new_tests, workspace, tracked_set)
    scratch_base = args.scratch if args.scratch else default_scratch(workspace, os.environ)
    scratch_base, work_sub = validate_scratch(scratch_base, workspace, run_id)
    run_lock_path = os.path.join(scratch_base, ".mutation-run-%s.lock" % run_id)
    os.makedirs(scratch_base, exist_ok=True)
    lock_fd = None
    run_lock_held = False
    try:
        if os.path.lexists(run_lock_path) and bridge_env is not None and bridge_env.is_link(run_lock_path):
            raise Refuse("mutation-run: existing mutation run lock is a link")
        try:
            lock_flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
            lock_fd = os.open(run_lock_path, lock_flags, 0o600)
        except OSError as e:
            raise Refuse("mutation-run: refused - could not open the run lock (%s)" % e)
        st = os.fstat(lock_fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            try:
                os.close(lock_fd)
            except OSError:
                pass
            lock_fd = None
            raise Refuse("mutation-run: refused - %s (OSError)" % os.path.basename(run_lock_path))
        if not _try_lock_byte(lock_fd):
            try:
                os.close(lock_fd)
            except OSError:
                pass
            lock_fd = None
            raise Refuse("mutation-run: refused - this mutants file is already running (%s); wait for it to end" % run_id)
        run_lock_held = True
        if os.path.isdir(work_sub):
            shutil.rmtree(work_sub, ignore_errors=True)
        os.makedirs(work_sub, exist_ok=True)
        copy_root = os.path.join(work_sub, "tree")
        os.makedirs(copy_root, exist_ok=True)
        cache_path = os.path.join(workspace, "run", "supervisor", "mutation-cache", run_id + ".jsonl")
        validate_cache_file(cache_path)
        cache = read_cache(cache_path)
        plugin_dir = work_sub
        ensure_outcomes_plugin(plugin_dir)
        env = dict(os.environ)
        results = []
        counts = {"run": 0, "cached": 0, "killed": 0, "survived": 0, "not applied": 0,
                  "error": 0, "expected survive": 0}
        if args.checkpoint:
            validate_tracked_copy(workspace, tracked_list)
            copied_conftest = archive_checkpoint(workspace, args.checkpoint, copy_root, new_tests, untracked)
            ir_active, mapped_active, path_kw = run_paths(plugin_dir, copy_root, workspace, import_roots, env, timeout_sec)
            chk_test_files = []
            for item in new_tests or []:
                if "::" in item:
                    fpart = normalize_rel(item.split("::", 1)[0])
                else:
                    fpart = normalize_rel(item)
                if fpart not in chk_test_files:
                    chk_test_files.append(fpart)
            file_blocked_conftest = {}
            rc_kwargs = dict(
                checkpoint=True, checkpoint_commit=args.checkpoint, new_tests=new_tests,
                copied_conftest=copied_conftest,
            )
            load_fail = run_resolution_check(
                plugin_dir, copy_root, mutants, chk_test_files, tracked_set, workspace, env, timeout_sec,
                **rc_kwargs, **path_kw)
            if load_fail:
                clear_files = []
                for fpart in chk_test_files:
                    per_fail = run_resolution_check(
                        plugin_dir, copy_root, mutants, [fpart], tracked_set, workspace, env, timeout_sec,
                        **rc_kwargs, **path_kw)
                    if per_fail:
                        if per_fail not in conftest_paths(normalize_rel(fpart)):
                            raise Refuse("mutation-run: resolution check failed (pytest exit 4)")
                        file_blocked_conftest[normalize_rel(fpart)] = per_fail
                    else:
                        clear_files.append(fpart)
                if clear_files:
                    combined_fail = run_resolution_check(
                        plugin_dir, copy_root, mutants, clear_files, tracked_set, workspace, env, timeout_sec,
                        **rc_kwargs, **path_kw)
                    if combined_fail:
                        raise Refuse("mutation-run: resolution check failed (pytest exit 4)")
            items = checkpoint_new_test_items(new_tests)
            any_pass = False
            for chk_idx, item in enumerate(items):
                if "::" in item:
                    item_fpart = normalize_rel(item.split("::", 1)[0])
                else:
                    item_fpart = normalize_rel(item)
                blocked = file_blocked_conftest.get(item_fpart)
                if blocked:
                    print("%s: not run (%s)" % (item, blocked))
                    continue
                chk_results = os.path.join(plugin_dir, "pytest-outcomes-chk-%d.json" % chk_idx)
                rc, out, err, timed, _, data = run_mutant_tests(
                    plugin_dir, copy_root, [item], env, timeout_sec, chk_results,
                    import_roots_rel=ir_active, mapped_roots_rel=mapped_active)
                if timed or data is None:
                    if "::" in item:
                        print("%s: not run" % item)
                    continue
                tests_run = data.get("tests", [])
                if "::" in item:
                    matched = checkpoint_records_for_item(item, tests_run)
                    if not matched:
                        print("%s: not run" % item)
                        continue
                    for rec in matched:
                        nid = rec.get("nodeid")
                        raw = rec.get("outcome")
                        if not nid:
                            continue
                        label = checkpoint_label_for_test(nid, raw)
                        print("%s: %s" % (nid, label))
                        if label == "passing on old code":
                            any_pass = True
                else:
                    if not tests_run:
                        print("%s: not run" % item)
                        continue
                    for rec in tests_run:
                        nid = rec.get("nodeid")
                        raw = rec.get("outcome")
                        if not nid:
                            continue
                        label = checkpoint_label_for_test(nid, raw)
                        print("%s: %s" % (nid, label))
                        if label == "passing on old code":
                            any_pass = True
            return 4 if any_pass else 0
        validate_tracked_copy(workspace, tracked_list)
        copy_tracked(workspace, copy_root, tracked_list, untracked)
        ir_active, mapped_active, path_kw = run_paths(plugin_dir, copy_root, workspace, import_roots, env, timeout_sec)
        res_tests = []
        for m in mutants:
            res_tests.extend(m["tests"])
        run_resolution_check(
            plugin_dir, copy_root, mutants, res_tests, tracked_set, workspace, env, timeout_sec, **path_kw)
        mutant_keys = {
            m["id"]: compute_key(copy_root, m, tracked_set, import_roots, mapped_active) for m in mutants}
        base_lists = uncached_test_lists(mutants, cache, mutant_keys, args.all)
        base_root = copy_root
        if base_lists:
            base_root = os.path.join(work_sub, "base")
            os.makedirs(base_root, exist_ok=True)
            copy_tracked(workspace, base_root, tracked_list, untracked)
        base_failures, base_timed, base_alive = run_baselines(
            plugin_dir, base_root, base_lists, env, timeout_sec,
            import_roots_rel=ir_active, mapped_roots_rel=mapped_active)
        originals = {}
        pytest_still_alive = False
        if base_alive is not None:
            pytest_still_alive = True
            print_baseline_failures(base_failures)
            for m in mutants:
                if m["tests"] == base_alive and not mutant_cached_kill(
                        cache, m, mutant_keys[m["id"]], args.all):
                    results.append((m["id"], "error (timed out)", None))
                    counts["error"] += 1
        elif base_failures:
            print_baseline_failures(base_failures)
            return 5
        for mut_idx, m in enumerate(mutants):
            if pytest_still_alive:
                break
            key = mutant_keys[m["id"]]
            cached = cache.get((m["id"], key))
            if cached and cached[0] == "killed" and not args.all:
                counts["cached"] += 1
                if not m["survive"]:
                    counts["killed"] += 1
                if m["survive"]:
                    counts["expected survive"] += 1
                    results.append((m["id"], "killed (wrong equivalence claim, cached %s)" % cached[1], False))
                else:
                    results.append((m["id"], "killed (cached %s)" % cached[1], False))
                continue
            if m["tests"] in base_timed:
                results.append((m["id"], "error (timed out)", None))
                counts["error"] += 1
                continue
            counts["run"] += 1
            orig_path = os.path.join(copy_root, m["file"])
            if m["file"] not in originals:
                with open(orig_path, "rb") as f:
                    originals[m["file"]] = f.read()
            applied = apply_mutant(copy_root, m)
            if not applied:
                restore_mutant(copy_root, m, originals[m["file"]])
                results.append((m["id"], "not applied", True))
                counts["not applied"] += 1
                append_cache(cache_path, m["id"], key, "not applied")
                continue
            mut_results = os.path.join(plugin_dir, "pytest-outcomes-%d.json" % mut_idx)
            rc, out, err, timed, alive, data = run_mutant_tests(
                plugin_dir, copy_root, m["tests"], env, timeout_sec, mut_results,
                import_roots_rel=ir_active, mapped_roots_rel=mapped_active)
            restore_mutant(copy_root, m, originals[m["file"]])
            if alive:
                pytest_still_alive = True
                outcome, reason = "error", "timed out"
            elif rc not in (0, 1) and not timed:
                outcome, reason = "error", "pytest exit %d" % rc
            else:
                outcome, reason = classify_outcome(data, m["expect_fail"], timed)
            if m["survive"]:
                counts["expected survive"] += 1
                if outcome == "killed":
                    results.append((m["id"], "killed (wrong equivalence claim)", True))
                    append_cache(cache_path, m["id"], key, "killed")
                elif outcome == "survived":
                    results.append((m["id"], "expected survive (%s)" % m["survive"], True))
                    append_cache(cache_path, m["id"], key, "survived")
                else:
                    results.append((m["id"], outcome + ((" (%s)" % reason) if reason else ""), True))
                    counts[outcome] += 1
                    append_cache(cache_path, m["id"], key, outcome)
            else:
                if outcome == "killed":
                    results.append((m["id"], "killed", True))
                    counts["killed"] += 1
                else:
                    disp = outcome + ((" (%s)" % reason) if reason else "")
                    results.append((m["id"], disp, True))
                    counts[outcome] += 1
                append_cache(cache_path, m["id"], key, outcome)
            if pytest_still_alive:
                break
        for mid, outcome, ran in results:
            if ran is None:
                tag = "not run"
            else:
                tag = "ran" if ran else "cached"
            print("%s: %s (%s)" % (mid, outcome, tag))
        print("counts: run=%d cached=%d killed=%d survived=%d not applied=%d error=%d expected survive=%d" % (
            counts["run"], counts["cached"], counts["killed"], counts["survived"],
            counts["not applied"], counts["error"], counts["expected survive"]))
        if pytest_still_alive:
            print(
                "mutation-run: pytest did not exit within %d s after the mutant timeout"
                % timeout_sec,
                file=sys.stderr,
            )
            return 3
        if counts["error"]:
            return 3
        if counts["survived"] or counts["not applied"]:
            return 1
        for mid, outcome, _ in results:
            if "wrong equivalence" in outcome:
                return 1
        return 0
    finally:
        if run_lock_held:
            if os.path.isdir(work_sub):
                shutil.rmtree(work_sub, ignore_errors=True)
            if lock_fd is not None:
                _unlock_byte(lock_fd)
        if lock_fd is not None:
            try:
                os.close(lock_fd)
            except OSError:
                pass


def run_main():
    if _IMPORT_ERRORS:
        parts = ["cannot import %s: %s: %s" % (name, type(exc).__name__, exc) for name, exc in _IMPORT_ERRORS]
        print("mutation-run: internal error - " + "; ".join(parts), file=sys.stderr)
        return 3
    try:
        return main()
    except ResolutionTimeout as e:
        print("mutation-run: resolution check timed out after %d s" % e.seconds, file=sys.stderr)
        return 3
    except Refuse as e:
        msg = str(e)
        if not msg.startswith("mutation-run:"):
            msg = "mutation-run: " + msg
        print(msg, file=sys.stderr)
        return 2
    except Exception as e:
        print("mutation-run: internal error - %s" % e, file=sys.stderr)
        return 3


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(run_main())
