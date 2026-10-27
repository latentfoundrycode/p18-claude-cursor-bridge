"""R-041: mutation-run.py applies mutants in a scratch copy and caches kills (TASK-031)."""
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time

import pytest

import conftest as test_conftest
from conftest import load_program

HERE = os.path.dirname(os.path.abspath(__file__))
MUTATION_RUN = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "mutation-run.py")
BRIDGE_RUN = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
       "-c", "commit.gpgsign=false"]


def workspace(tmp_path, project="proj"):
    ws = tmp_path / project / "Workspace"
    ws.mkdir(parents=True)
    (ws / "run" / "supervisor").mkdir(parents=True)
    (ws / "run" / "supervisor" / "mutation-cache").mkdir(parents=True)
    return ws


def git(ws, *args):
    kw = test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 60})
    p = subprocess.run(GIT + list(args), cwd=str(ws), **kw)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def write(ws, rel, text, binary=False):
    path = ws / rel.replace("/", os.sep)
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        path.write_bytes(text.encode("utf-8"))
    else:
        path.write_text(text, encoding="utf-8", newline="\n")


def init_pkg(ws, crlf=False):
    nl = "\r\n" if crlf else "\n"
    write(ws, "demo/__init__.py", "")
    write(ws, "demo/calc.py", "def add(a, b):%s    return a + b%s" % (nl, nl), binary=crlf)
    write(ws, "tests/test_calc.py",
          "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n\ndef test_sub():\n    assert add(2, 3) == 5\n")
    write(ws, "tests/conftest.py", "")
    git(ws, "init", "-q", "-b", "main")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "init")


def mutants_path(ws, run_id, body):
    p = ws / "run" / "supervisor" / ("%s-mutants.json" % run_id)
    p.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return p


def run_mr(ws, mutants_file, scratch=None, timeout=60, extra=(), home_env=None, harness_slack=30):
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    if home_env:
        env["HOME"] = env["USERPROFILE"] = str(home_env)
    cmd = [sys.executable, MUTATION_RUN, str(mutants_file)] + list(extra)
    if scratch:
        cmd += ["--scratch", str(scratch)]
    cmd += ["--mutant-timeout", str(timeout)]
    return subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env,
                          timeout=timeout + harness_slack, **test_conftest.windowless_kwargs({}))


def git_porcelain(ws):
    kw = test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 30})
    p = subprocess.run(GIT + ["status", "--porcelain"], cwd=str(ws), **kw)
    assert p.returncode == 0
    return p.stdout


def git_porcelain_excluding_cache(ws):
    lines = [ln for ln in git_porcelain(ws).splitlines() if "mutation-cache/" not in ln]
    return "\n".join(lines) + ("\n" if lines else "")


def pid_dead(pid):
    if sys.platform == "win32":
        SYNCHRONIZE = 0x00100000
        WAIT_OBJECT_0 = 0
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if not handle:
            return True
        rc = kernel32.WaitForSingleObject(handle, 0)
        kernel32.CloseHandle(handle)
        return rc == WAIT_OBJECT_0
    try:
        os.kill(pid, 0)
    except OSError:
        return True
    return False


def kill_proc_tree(proc):
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            capture_output=True,
            **test_conftest.windowless_kwargs({"stdin": subprocess.DEVNULL}),
        )
    else:
        import signal
        try:
            # never the test run's own group: a child started without a session of its own shares it, and on
            # a CI runner that group holds the runner itself (TASK-031: every Ubuntu job lost its runner)
            if os.getpgid(proc.pid) == os.getpgrp():
                proc.kill()
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            proc.kill()


def tree_bytes(ws):
    out = {}
    for root, dirs, files in os.walk(ws):
        dirs[:] = [d for d in dirs if d not in (".git", "mutation-cache")]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), ws).replace("\\", "/")
            if rel.startswith("run/supervisor/mutation-cache"):
                continue
            with open(os.path.join(root, f), "rb") as fh:
                out[rel] = fh.read()
    return out


def cache_last_outcome(ws, run_id):
    cache = ws / "run/supervisor/mutation-cache" / ("%s.jsonl" % run_id)
    lines = [json.loads(ln) for ln in cache.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return lines[-1]["outcome"] if lines else None


def basic_mutant(kill=True):
    new = "assert add(1, 1) == 99" if kill else "assert add(1, 1) == 2"
    return {
        "mutants": [{
            "id": "m1",
            "file": "tests/test_calc.py",
            "pairs": [{"old": "assert add(1, 1) == 2", "new": new}],
            "tests": ["tests/test_calc.py"],
            "expect_fail": ["tests/test_calc.py::test_add"],
        }]
    }


def test_r041_done_b_first_run_kills_and_records(tmp_path):
    """R-041, TASK-031 Done when (c): a first run kills and records."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "t1", basic_mutant())
    git(ws, "add", "run/supervisor/t1-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "m1: killed" in p.stdout
    cache = ws / "run/supervisor/mutation-cache/t1.jsonl"
    assert cache.is_file()
    assert "killed" in cache.read_text(encoding="utf-8")


def test_r041_done_c_unchanged_skips(tmp_path):
    """R-041, TASK-031 Done when (c): a run with nothing changed runs no mutant."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "t2", basic_mutant())
    git(ws, "add", "run/supervisor/t2-mutants.json")
    assert run_mr(ws, mp).returncode == 0
    p = run_mr(ws, mp)
    assert p.returncode == 0, p.stderr
    assert "cached" in p.stdout
    assert "counts: run=0" in p.stdout


def test_r041_done_c_mutated_file_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to a mutated file reruns only that file's mutants."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "lib/__init__.py", "")
    write(ws, "lib/util.py", "def double(x):\n    return 2 * x\n")
    write(ws, "tests/test_util.py", "from lib.util import double\n\ndef test_double():\n    assert double(2) == 4\n")
    git(ws, "add", "-A")
    body = {"mutants": [
        {"id": "calc", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
         "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]},
        {"id": "util", "file": "lib/util.py", "pairs": [{"old": "return 2 * x", "new": "return 3 * x"}],
         "tests": ["tests/test_util.py"], "expect_fail": ["tests/test_util.py::test_double"]},
    ]}
    mp = mutants_path(ws, "t3", body)
    git(ws, "add", "run/supervisor/t3-mutants.json")
    run_mr(ws, mp)
    write(ws, "demo/calc.py", "def add(a, b):\n    return a + b  # touched\n")
    git(ws, "add", "demo/calc.py")
    p = run_mr(ws, mp)
    assert "calc:" in p.stdout and "util: killed (cached" in p.stdout


def test_r041_malformed_exits_2(tmp_path):
    """R-041, TASK-031 Done when (d): a malformed file exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "bad", {"mutants": []})
    p = run_mr(ws, mp)
    assert p.returncode == 2


def test_r041_default_scratch_stale_removed(tmp_path, home_of_the_tests):
    """R-041, TASK-031 Requirement 2: the default scratch folder removes a left-behind mutation-run-<id>/ and uses the tests' temporary home."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    stale = home_of_the_tests / ".cursor-bridge" / "scratch" / "proj" / "mutation-run-sc" / "stale.txt"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("left behind\n", encoding="utf-8")
    bridge = os.path.normpath(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge"))
    real_cb_before = None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("bridge_env", os.path.join(bridge, "bridge_env.py"))
        be = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(be)
        rh = be.real_home(os.environ)
        real_root = os.path.join(rh, ".cursor-bridge")
        if os.path.isdir(real_root):
            real_cb_before = set(os.listdir(real_root))
    except Exception:
        pass
    mp = mutants_path(ws, "sc", basic_mutant())
    git(ws, "add", "run/supervisor/sc-mutants.json")
    p = run_mr(ws, mp, home_env=home_of_the_tests)
    assert p.returncode == 0
    assert not (home_of_the_tests / ".cursor-bridge" / "scratch" / "proj" / "mutation-run-sc").exists()
    if real_cb_before is not None:
        real_root = os.path.join(be.real_home(os.environ), ".cursor-bridge")
        if os.path.isdir(real_root):
            assert set(os.listdir(real_root)) == real_cb_before


def test_r041_all_with_checkpoint_exits_2(tmp_path):
    """R-041: --all with --checkpoint exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "x1", {"mutants": [], "new_tests": ["tests/test_calc.py"]})
    git(ws, "add", "-A")
    sha = git(ws, "rev-parse", "HEAD")
    p = run_mr(ws, mp, extra=["--all", "--checkpoint", sha])
    assert p.returncode == 2


def test_r041_internal_error_exits_3(tmp_path, monkeypatch):
    """R-041: an internal error exits 3."""
    bridge = os.path.normpath(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge"))
    monkeypatch.syspath_prepend(bridge)
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "ie", basic_mutant())
    git(ws, "add", "run/supervisor/ie-mutants.json")
    mod = load_program("mutation-run")
    monkeypatch.setattr(mod, "git", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("test boom")))
    monkeypatch.chdir(ws)
    monkeypatch.setattr(sys, "argv", ["mutation-run.py", str(mp)])
    rc = mod.run_main()
    assert rc == 3


def test_dump_cli_argparse_updated():
    """TASK-031 Requirement 10: mutation-run.py is in ARGPARSE."""
    from test_dump_cli import ARGPARSE
    assert "mutation-run.py" in ARGPARSE


def _seed(ws, run_id):
    mp = mutants_path(ws, run_id, basic_mutant())
    git(ws, "add", "run/supervisor/%s-mutants.json" % run_id)
    run_mr(ws, mp)
    return mp


def test_r041_done_c_test_file_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to a named test file reruns its mutants."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "tf")
    write(ws, "tests/test_calc.py",
          "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n\ndef test_sub():\n    assert add(2, 3) == 5\n# x\n")
    git(ws, "add", "tests/test_calc.py")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout and "cached" in p.stdout
    assert cache_last_outcome(ws, "tf") == "killed"


def test_r041_done_c_conftest_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to a conftest.py on its path reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "cf")
    write(ws, "tests/conftest.py", "# hook\n")
    git(ws, "add", "tests/conftest.py")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout
    assert cache_last_outcome(ws, "cf") == "killed"


def test_r041_done_c_sibling_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to a sibling of the mutated file reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "demo/other.py", "x = 1\n")
    git(ws, "add", "demo/other.py")
    body = {"mutants": [{
        "id": "m1", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a + b + 1"}],
        "tests": ["tests/test_calc.py"],
        "expect_fail": ["tests/test_calc.py::test_add", "tests/test_calc.py::test_sub"],
    }]}
    mp = mutants_path(ws, "sib", body)
    git(ws, "add", "run/supervisor/sib-mutants.json")
    run_mr(ws, mp)
    write(ws, "demo/other.py", "x = 2\n")
    git(ws, "add", "demo/other.py")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout
    assert cache_last_outcome(ws, "sib") == "killed"


def test_r041_done_c_pytest_ini_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to the root pytest.ini reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "pytest.ini", "[pytest]\n")
    git(ws, "add", "pytest.ini")
    mp = _seed(ws, "ini")
    write(ws, "pytest.ini", "[pytest]\naddopts = -q\n")
    git(ws, "add", "pytest.ini")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout
    assert cache_last_outcome(ws, "ini") == "killed"


def test_r041_done_c_expect_fail_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to expected test ids reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    mp = mutants_path(ws, "ef", body)
    git(ws, "add", "run/supervisor/ef-mutants.json")
    run_mr(ws, mp)
    body["mutants"][0]["expect_fail"] = ["tests/test_calc.py::test_sub"]
    mp.write_text(json.dumps(body), encoding="utf-8")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout


def test_r041_done_c_survive_flag_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to expect survive reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "sv")
    data = json.loads((ws / "run/supervisor/sv-mutants.json").read_text(encoding="utf-8"))
    data["mutants"][0]["expect"] = "survive reason"
    mutants_path(ws, "sv", data)
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout
    assert cache_last_outcome(ws, "sv") == "killed"


def test_r041_survived_reruns_every_time(tmp_path):
    """R-041, TASK-031 Done when (c): a survived mutant reruns every time."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant(kill=False)
    mp = mutants_path(ws, "sur", body)
    git(ws, "add", "run/supervisor/sur-mutants.json")
    assert run_mr(ws, mp).returncode == 1
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout and "survived" in p.stdout


def test_r041_two_mutants_same_file_original(tmp_path):
    """R-041, TASK-031 Done when (d): two mutants whose old texts match the original each apply."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = {"mutants": [
        {"id": "a", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a + b + 1"}],
         "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add", "tests/test_calc.py::test_sub"]},
        {"id": "b", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a + b + 2"}],
         "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add", "tests/test_calc.py::test_sub"]},
    ]}
    mp = mutants_path(ws, "two", body)
    git(ws, "add", "run/supervisor/two-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0
    assert "a: killed" in p.stdout and "b: killed" in p.stdout


def test_r041_crlf_mutant_killed(tmp_path):
    """R-041, TASK-031 Done when (d): a CRLF fixture's mutant is killed."""
    ws = workspace(tmp_path)
    init_pkg(ws, crlf=True)
    body = {"mutants": [{
        "id": "crlf", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a + b + 1"}],
        "tests": ["tests/test_calc.py"],
        "expect_fail": ["tests/test_calc.py::test_add", "tests/test_calc.py::test_sub"],
    }]}
    mp = mutants_path(ws, "crlf", body)
    git(ws, "add", "run/supervisor/crlf-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0 and "killed" in p.stdout


def test_r041_env_and_untracked_in_copy(tmp_path):
    """R-041, TASK-031 Done when (d): root .env and untracked fixture run in the copy."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, ".env", "SECRET=fixture-value\n")
    write(ws, "fixtures/data.txt", "payload\n")
    write(ws, "tests/test_env.py", textwrap.dedent("""
import os
from pathlib import Path
def test_env():
    assert os.environ.get("SECRET") or open(".env").read().strip().endswith("fixture-value")
def test_untracked():
    assert Path("fixtures/data.txt").read_text(encoding="utf-8").strip() == "payload"
"""))
    git(ws, "add", "tests/test_env.py")
    body = {"mutants": [{
        "id": "e1", "file": "tests/test_env.py",
        "pairs": [{"old": 'endswith("fixture-value")', "new": 'endswith("wrong")'}],
        "tests": ["tests/test_env.py"], "expect_fail": ["tests/test_env.py::test_env"],
    }], "untracked": ["fixtures/data.txt"]}
    mp = mutants_path(ws, "env", body)
    git(ws, "add", "run/supervisor/env-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0


def test_r041_crash_is_error_exit_3(tmp_path):
    """R-041, TASK-031 Done when (d): a crash is error with exit 3, outranking exit 1."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant(kill=False)
    body["mutants"].append({
        **basic_mutant()["mutants"][0], "id": "m2",
        "pairs": [{"old": "assert add(1, 1) == 2", "new": "import os; os._exit(9)"}],
    })
    mp = mutants_path(ws, "crash", body)
    git(ws, "add", "run/supervisor/crash-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 3


def test_r041_timeout_error_continues(tmp_path):
    """R-041, TASK-031 Done when (d): infinite loop is error timed out under short timeout, exit 3, then the next mutant runs and the hang process ends."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    pid_file = tmp_path / "hang.pid"
    write(ws, "tests/test_hang.py", textwrap.dedent("""
import os
def test_hang():
    open(%r, "w").write(str(os.getpid()))
    while True:
        pass
""" % str(pid_file).replace("\\", "/")))
    write(ws, "tests/test_ok.py", "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n")
    git(ws, "add", "tests/test_hang.py", "tests/test_ok.py")
    body = {"mutants": [
        {"id": "hang", "file": "tests/test_hang.py", "pairs": [{"old": "pass", "new": "pass"}],
         "tests": ["tests/test_hang.py"], "expect_fail": ["tests/test_hang.py::test_hang"]},
        {"id": "ok", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
         "tests": ["tests/test_ok.py"], "expect_fail": ["tests/test_ok.py::test_add"]},
    ]}
    mp = mutants_path(ws, "hang", body)
    git(ws, "add", "run/supervisor/hang-mutants.json")
    p = run_mr(ws, mp, timeout=3)
    assert p.returncode == 3 and "timed out" in p.stdout and "ok: killed" in p.stdout
    if pid_file.is_file():
        assert pid_dead(int(pid_file.read_text(encoding="utf-8").strip()))


def test_r041_unexpected_fail_is_error(tmp_path):
    """R-041, TASK-031 Done when (d): a test not expected to fail that fails is error."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = {"mutants": [{
        "id": "ux", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a + b + 1"}],
        "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"],
    }]}
    mp = mutants_path(ws, "ux", body)
    git(ws, "add", "run/supervisor/ux-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 3 and "error" in p.stdout


def test_r041_survive_killed_exit_1(tmp_path):
    """R-041, TASK-031 Done when (d): an equivalent mutant killed gives exit 1."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["expect"] = "survive same math"
    mp = mutants_path(ws, "eq", body)
    git(ws, "add", "run/supervisor/eq-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 1 and "wrong equivalence" in p.stdout


def test_r041_all_reruns(tmp_path):
    """R-041, TASK-031 Done when (d): --all reruns all."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "all")
    p = run_mr(ws, mp, extra=["--all"])
    assert "run=1" in p.stdout
    assert cache_last_outcome(ws, "all") == "killed"


def test_r041_not_applied_exit_1(tmp_path):
    """R-041, TASK-031 Done when (d): old text not found is not applied with exit 1."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["pairs"][0]["old"] = "no such text"
    mp = mutants_path(ws, "na", body)
    git(ws, "add", "run/supervisor/na-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 1 and "not applied" in p.stdout


def test_r041_tree_unchanged_after_run(tmp_path):
    """R-041, TASK-031 Done when (d): tracked tree byte-identical after a run."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "bt", basic_mutant())
    git(ws, "add", "run/supervisor/bt-mutants.json")
    before = tree_bytes(ws)
    porcelain_before = git_porcelain_excluding_cache(ws)
    run_mr(ws, mp)
    after = tree_bytes(ws)
    assert before == after
    assert git_porcelain_excluding_cache(ws) == porcelain_before


def test_r041_cache_torn_line_ignored(tmp_path):
    """R-041, TASK-031 Done when (d): a torn last cache line is ignored."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "torn")
    cache = ws / "run/supervisor/mutation-cache/torn.jsonl"
    cache.write_text(cache.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")
    p = run_mr(ws, mp)
    assert p.returncode == 0


def test_r041_refuse_absolute_path(tmp_path):
    """R-041: absolute path in mutants file exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["file"] = str(ws / "demo/calc.py").replace("\\", "/")
    mp = mutants_path(ws, "abs", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_dotdot(tmp_path):
    """R-041: .. path component exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["file"] = "demo/../demo/calc.py"
    mp = mutants_path(ws, "dd", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_untracked_mutated_file(tmp_path):
    """R-041: untracked mutated file exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "extra.py", "x=1\n")
    body = basic_mutant()
    body["mutants"][0]["file"] = "extra.py"
    mp = mutants_path(ws, "utm", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_bad_mutants_name(tmp_path):
    """R-041: mutants file name breaks S1 exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    p = ws / "run/supervisor/bad..-mutants.json"
    p.write_text(json.dumps(basic_mutant()), encoding="utf-8")
    assert run_mr(ws, p).returncode == 2


def test_r041_checkpoint_pass_exit_4(tmp_path):
    """R-041, TASK-031 Done when (d): checkpoint lists new test passing on old code, exit 4."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    sha = git(ws, "rev-parse", "HEAD")
    write(ws, "tests/test_new.py", "def test_new():\n    assert 1 == 1\n")
    git(ws, "add", "tests/test_new.py")
    mp = mutants_path(ws, "ck", {"mutants": [], "new_tests": ["tests/test_new.py::test_new"]})
    git(ws, "add", "run/supervisor/ck-mutants.json")
    p = run_mr(ws, mp, extra=["--checkpoint", sha])
    assert p.returncode == 4 and "passing on old code" in p.stdout


def test_r041_checkpoint_not_run(tmp_path):
    """R-041, TASK-031 Done when (d): new test importing absent module is not run."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    sha = git(ws, "rev-parse", "HEAD")
    write(ws, "tests/test_imp.py", "import missing_mod\ndef test_x():\n    pass\n")
    git(ws, "add", "tests/test_imp.py")
    mp = mutants_path(ws, "ck2", {"mutants": [], "new_tests": ["tests/test_imp.py::test_x"]})
    git(ws, "add", "run/supervisor/ck2-mutants.json")
    p = run_mr(ws, mp, extra=["--checkpoint", sha])
    assert "not run" in p.stdout


def test_r041_checkpoint_refuse_file_at_commit(tmp_path):
    """R-041, TASK-031 Done when (d): listed file at checkpoint refused exit 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    sha = git(ws, "rev-parse", "HEAD")
    mp = mutants_path(ws, "ck3", {"mutants": [], "new_tests": ["tests/test_calc.py"]})
    assert run_mr(ws, mp, extra=["--checkpoint", sha]).returncode == 2


def test_r041_relaunch_after_partial_cache(tmp_path):
    """R-041, TASK-031 Done when (d): relaunch runs only mutants not kept as killed."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = {"mutants": [
        basic_mutant()["mutants"][0],
        {**basic_mutant()["mutants"][0], "id": "m2"},
    ]}
    mp = mutants_path(ws, "rel", body)
    git(ws, "add", "run/supervisor/rel-mutants.json")
    run_mr(ws, mp)
    cache = ws / "run/supervisor/mutation-cache/rel.jsonl"
    lines = [l for l in cache.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 2
    cache.write_text(lines[0] + "\n", encoding="utf-8")
    p = run_mr(ws, mp)
    assert "m1: killed (cached" in p.stdout and "m2:" in p.stdout and "run=1" in p.stdout


def _venv_with_pth(tmp_path, ws, pth_target, tag="v"):
    vroot = tmp_path / ("%s-%s" % (tag, abs(hash(str(pth_target))) % 1000000))
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", "--system-site-packages", str(vroot)],
                   check=True, timeout=60,
                   **test_conftest.windowless_kwargs({"capture_output": True}))
    if sys.platform == "win32":
        vpy = vroot / "Scripts" / "python.exe"
        site = vroot / "Lib" / "site-packages"
    else:
        vpy = vroot / "bin" / "python"
        site = vroot / "lib" / ("python%d.%d" % sys.version_info[:2]) / "site-packages"
    site.mkdir(parents=True, exist_ok=True)
    (site / "demo.pth").write_text(str(pth_target) + "\n", encoding="utf-8")
    return vpy


def test_r041_editable_install_flat_kills_mutant(tmp_path):
    """R-041, TASK-031 Done when (d): editable install of the flat fixture package is overridden by the copy and the mutant on package code is killed."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "tests/test_one.py", "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n")
    git(ws, "add", "tests/test_one.py")
    vpy = _venv_with_pth(tmp_path, ws, ws)
    body = {"mutants": [{
        "id": "m1", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_one.py"], "expect_fail": ["tests/test_one.py::test_add"],
    }]}
    mp = mutants_path(ws, "edif", body)
    git(ws, "add", "run/supervisor/edif-mutants.json")
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    cmd = [str(vpy), MUTATION_RUN, str(mp), "--mutant-timeout", "60"]
    p = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env, timeout=120,
                       **test_conftest.windowless_kwargs({}))
    assert p.returncode == 0 and "killed" in p.stdout, p.stderr + p.stdout


def test_r041_editable_install_src_kills_mutant(tmp_path):
    """R-041, TASK-031 Done when (d): editable install of a src-layout fixture package is overridden by the copy and the mutant on package code is killed."""
    ws = workspace(tmp_path)
    write(ws, "src/demo/__init__.py", "")
    write(ws, "src/demo/calc.py", "def add(a, b):\n    return a + b\n")
    write(ws, "tests/test_one.py", "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n")
    write(ws, "pytest.ini", "[pytest]\npythonpath = src\n")
    git(ws, "init", "-q", "-b", "main")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "init")
    vpy = _venv_with_pth(tmp_path, ws, ws)
    body = {"mutants": [{
        "id": "m1", "file": "src/demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_one.py"], "expect_fail": ["tests/test_one.py::test_add"],
    }]}
    mp = mutants_path(ws, "edis", body)
    git(ws, "add", "run/supervisor/edis-mutants.json")
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    cmd = [str(vpy), MUTATION_RUN, str(mp), "--mutant-timeout", "60"]
    p = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env, timeout=120,
                       **test_conftest.windowless_kwargs({}))
    assert p.returncode == 0 and "killed" in p.stdout, p.stderr + p.stdout


def test_r041_editable_src_only_refused(tmp_path):
    """R-041, TASK-031 Requirement 5: a src-layout fixture that relies on the editable install alone is refused with exit 2."""
    ws = workspace(tmp_path)
    write(ws, "src/demo/__init__.py", "")
    write(ws, "src/demo/calc.py", "def add(a, b):\n    return a + b\n")
    write(ws, "tests/test_calc.py", "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n")
    git(ws, "init", "-q", "-b", "main")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "init")
    vpy = _venv_with_pth(tmp_path, ws, ws, tag="edir")
    body = {"mutants": [{
        "id": "m1", "file": "src/demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"],
    }]}
    mp = mutants_path(ws, "edir", body)
    git(ws, "add", "run/supervisor/edir-mutants.json")
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    cmd = [str(vpy), MUTATION_RUN, str(mp), "--mutant-timeout", "60"]
    p = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env, timeout=120,
                       **test_conftest.windowless_kwargs({}))
    assert p.returncode == 2, p.stderr + p.stdout
    sha = git(ws, "rev-parse", "HEAD")
    mp2 = mutants_path(ws, "edir2", {"mutants": [], "new_tests": ["tests/test_calc.py::test_add"]})
    git(ws, "add", "run/supervisor/edir2-mutants.json")
    cmd2 = [str(vpy), MUTATION_RUN, str(mp2), "--mutant-timeout", "60", "--checkpoint", sha]
    p2 = subprocess.run(cmd2, cwd=str(ws), capture_output=True, text=True, env=env, timeout=120,
                        **test_conftest.windowless_kwargs({}))
    assert p2.returncode == 2, p2.stderr + p2.stdout
    assert not (ws / "run/supervisor/mutation-cache/edir.jsonl").exists()
    assert not (ws / "run/supervisor/mutation-cache/edir2.jsonl").exists()


def test_r041_namespace_package_resolution_refused(tmp_path):
    """R-041, TASK-031 Requirement 5 (i): a namespace package whose search path lies outside the copy is refused."""
    ws = workspace(tmp_path)
    write(ws, "ns/pkg/mod.py", "VALUE = 1\n")
    write(ws, "tests/test_ns.py", "from ns.pkg import mod\n\ndef test_ns():\n    assert mod.VALUE == 1\n")
    git(ws, "init", "-q", "-b", "main")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "init")
    body = {"mutants": [{
        "id": "m1", "file": "ns/pkg/mod.py", "pairs": [{"old": "VALUE = 1", "new": "VALUE = 2"}],
        "tests": ["tests/test_ns.py"], "expect_fail": ["tests/test_ns.py::test_ns"],
    }]}
    mp = mutants_path(ws, "nsp", body)
    git(ws, "add", "run/supervisor/nsp-mutants.json")
    outside = tmp_path / "outside_ns"
    outside.mkdir()
    (outside / "ns").mkdir()
    (outside / "ns" / "pkg").mkdir(parents=True)
    (outside / "ns" / "pkg" / "mod.py").write_text("VALUE = 9\n", encoding="utf-8")
    write(ws, "tests/conftest.py", "import sys\nsys.path.insert(0, %r)\n" % str(outside))
    git(ws, "add", "tests/conftest.py")
    p = run_mr(ws, mp)
    assert p.returncode == 2, p.stdout + p.stderr


def test_r041_killed_run_keeps_partial_cache(tmp_path, home_of_the_tests):
    """R-041, TASK-031 Done when (d): a run stopped after N mutants keeps N cache lines, leaves the tree unchanged, and a relaunch runs only the rest."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    marker = tmp_path / "continue.marker"
    write(ws, "tests/test_gate.py", textwrap.dedent("""
import time
from pathlib import Path
def test_gate():
    p = Path(%r)
    while not p.is_file():
        time.sleep(0.05)
    assert False
""" % str(marker).replace("\\", "/")))
    write(ws, "tests/test_m1.py", "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n")
    write(ws, "tests/test_m3.py", "from demo.calc import add\n\ndef test_sub():\n    assert add(2, 3) == 5\n")
    git(ws, "add", "tests/test_gate.py", "tests/test_m1.py", "tests/test_m3.py")
    body = {"mutants": [
        {"id": "m1", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
         "tests": ["tests/test_m1.py"], "expect_fail": ["tests/test_m1.py::test_add"]},
        {"id": "m2", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
         "tests": ["tests/test_gate.py"], "expect_fail": ["tests/test_gate.py::test_gate"]},
        {"id": "m3", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
         "tests": ["tests/test_m3.py"], "expect_fail": ["tests/test_m3.py::test_sub"]},
    ]}
    mp = mutants_path(ws, "kill", body)
    git(ws, "add", "run/supervisor/kill-mutants.json")
    scratch = home_of_the_tests / "scr-kill"
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env["HOME"] = env["USERPROFILE"] = str(home_of_the_tests)
    cmd = [sys.executable, MUTATION_RUN, str(mp), "--scratch", str(scratch), "--mutant-timeout", "120"]
    before = tree_bytes(ws)
    porcelain_before = git_porcelain_excluding_cache(ws)
    # a session of its own on POSIX, so stopping its process group stops the program and never the test run
    session = {} if sys.platform == "win32" else {"start_new_session": True}
    proc = subprocess.Popen(cmd, cwd=str(ws), env=env, **session,
                            **test_conftest.windowless_kwargs({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True}))
    cache = ws / "run/supervisor/mutation-cache/kill.jsonl"
    try:
        for _ in range(600):
            if cache.is_file() and len([l for l in cache.read_text(encoding="utf-8").splitlines() if l.strip()]) >= 1:
                break
            time.sleep(0.05)
        kill_proc_tree(proc)
        proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            kill_proc_tree(proc)
            proc.wait(timeout=10)
    assert tree_bytes(ws) == before
    assert git_porcelain_excluding_cache(ws) == porcelain_before
    lines = [l for l in cache.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1
    marker.write_text("go\n", encoding="utf-8")
    p2 = run_mr(ws, mp, scratch=scratch, home_env=home_of_the_tests, timeout=120)
    assert "m1: killed (cached" in p2.stdout
    assert "m2:" in p2.stdout and "m3:" in p2.stdout
    assert "cached=1" in p2.stdout and "run=2" in p2.stdout


def test_r041_checkpoint_reads_root_env_exit_4(tmp_path):
    """R-041, TASK-031 Done when (d): --checkpoint with a new test that reads the root .env passes on old code with exit 4."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, ".env", "SECRET=fixture-value\n")
    sha = git(ws, "rev-parse", "HEAD")
    write(ws, "tests/test_env_ck.py", textwrap.dedent("""
def test_reads_env():
    assert open(".env", encoding="utf-8").read().strip().endswith("fixture-value")
"""))
    git(ws, "add", "tests/test_env_ck.py")
    mp = mutants_path(ws, "cken", {"mutants": [], "new_tests": ["tests/test_env_ck.py::test_reads_env"]})
    git(ws, "add", "run/supervisor/cken-mutants.json")
    p = run_mr(ws, mp, extra=["--checkpoint", sha])
    assert p.returncode == 4 and "passing on old code" in p.stdout


def test_r041_refuse_untracked_test_file(tmp_path):
    """R-041, TASK-031 Requirement 1: an untracked test file in mutants exits 2 with nothing cached."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "tests/extra.py", "def test_x():\n    pass\n")
    body = basic_mutant()
    body["mutants"][0]["tests"] = ["tests/extra.py"]
    body["mutants"][0]["expect_fail"] = ["tests/extra.py::test_x"]
    mp = mutants_path(ws, "utt", body)
    p = run_mr(ws, mp)
    assert p.returncode == 2
    assert not (ws / "run/supervisor/mutation-cache/utt.jsonl").exists()


def test_r041_refuse_untracked_path_is_link(tmp_path):
    """R-041, TASK-031 Requirement 1: an untracked path that is itself a link exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    target = tmp_path / "target.txt"
    target.write_text("x\n", encoding="utf-8")
    link = ws / "link.txt"
    try:
        os.symlink(str(target), str(link))
    except (OSError, NotImplementedError) as e:
        if sys.platform != "win32":
            pytest.skip("this account cannot create a symbolic link here (%s)" % e)
        j = subprocess.run(["cmd", "/c", "mklink", "/J", str(ws / "linkdir"), str(target.parent)],
                           **test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 30}))
        if j.returncode != 0:
            pytest.skip("neither a symbolic link nor a junction could be made here (%s)" % j.stderr)
        untracked = ["linkdir"]
    else:
        untracked = ["link.txt"]
    body = basic_mutant()
    body["untracked"] = untracked
    mp = mutants_path(ws, "utl", body)
    git(ws, "add", "run/supervisor/utl-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 2
    assert not (ws / "run/supervisor/mutation-cache/utl.jsonl").exists()


def test_r041_refuse_unknown_field(tmp_path):
    """R-041, TASK-031 Requirement 1: an unknown top-level field exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["extra"] = 1
    mp = mutants_path(ws, "unk", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_duplicate_id(tmp_path):
    """R-041, TASK-031 Requirement 1: a duplicate mutant id exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    m = basic_mutant()["mutants"][0]
    body = {"mutants": [m, dict(m)]}
    mp = mutants_path(ws, "dup", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_bad_expect(tmp_path):
    """R-041, TASK-031 Requirement 1: an expect that does not start with survive exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["expect"] = "kill me"
    mp = mutants_path(ws, "bex", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_empty_expect_fail(tmp_path):
    """R-041, TASK-031 Requirement 1: an empty expect_fail exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["expect_fail"] = []
    mp = mutants_path(ws, "eef", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_new_tests_not_tracked(tmp_path):
    """R-041, TASK-031 Requirement 1: a new_tests entry that is not tracked exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    sha = git(ws, "rev-parse", "HEAD")
    write(ws, "tests/new.py", "def test_n():\n    pass\n")
    mp = mutants_path(ws, "nnt", {"mutants": [], "new_tests": ["tests/new.py::test_n"]})
    p = run_mr(ws, mp, extra=["--checkpoint", sha])
    assert p.returncode == 2


def test_r041_scratch_contains_workspace_refused(tmp_path):
    """R-041, TASK-031 Requirement 2: a scratch folder that contains the Workspace exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "scw", basic_mutant())
    git(ws, "add", "run/supervisor/scw-mutants.json")
    scratch = ws.parent
    assert run_mr(ws, mp, scratch=scratch).returncode == 2


def test_r041_scratch_through_link_refused(tmp_path):
    """R-041, TASK-031 Requirement 2: a scratch path reached through a link exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    real_scratch = tmp_path / "real_scratch"
    real_scratch.mkdir()
    link_scratch = tmp_path / "link_scratch"
    try:
        os.symlink(str(real_scratch), str(link_scratch))
    except (OSError, NotImplementedError) as e:
        pytest.skip("this account cannot create a symbolic link here (%s)" % e)
    mp = mutants_path(ws, "scl", basic_mutant())
    git(ws, "add", "run/supervisor/scl-mutants.json")
    assert run_mr(ws, mp, scratch=link_scratch).returncode == 2


def test_r041_scratch_inside_workspace_refused(tmp_path):
    """R-041: scratch inside Workspace exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "si", basic_mutant())
    git(ws, "add", "run/supervisor/si-mutants.json")
    scratch = ws / "scratch"
    assert run_mr(ws, mp, scratch=scratch).returncode == 2


@pytest.mark.skipif(sys.platform != "win32", reason="console windows exist only on Windows")
def test_r041_pytest_process_windowless(tmp_path, home_of_the_tests):
    """R-041, TASK-031 Requirement 4 (M06): the pytest process mutation-run starts has no console window."""
    from test_tests_windowless import window_and_console
    ws = workspace(tmp_path)
    init_pkg(ws)
    hook = textwrap.dedent("""
def pytest_sessionstart(session):
    import ctypes, os
    k = ctypes.windll.kernel32
    a = (ctypes.c_uint * 64)()
    n = k.GetConsoleProcessList(a, 64)
    parts = [str(k.GetConsoleWindow()), str(os.getpid())]
    parts.extend(str(a[i]) for i in range(n))
    open("_win_probe.txt", "w").write(" ".join(parts))
""")
    write(ws, "tests/conftest.py", hook)
    git(ws, "add", "tests/conftest.py")
    mp = mutants_path(ws, "win2", basic_mutant())
    git(ws, "add", "run/supervisor/win2-mutants.json")
    scratch = home_of_the_tests / "scr-win2"
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env["HOME"] = env["USERPROFILE"] = str(home_of_the_tests)
    cmd = [sys.executable, MUTATION_RUN, str(mp), "--scratch", str(scratch), "--mutant-timeout", "60"]
    # the program starts windowless (the suite's default): it gets a console of its own with no window, so a
    # pytest child it starts without the flag inherits that console, and the program's pid is then on it
    proc = subprocess.Popen(
        cmd, cwd=str(ws), env=env,
        **test_conftest.windowless_kwargs({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True}),
    )
    line = None
    while proc.poll() is None:
        hits = list(scratch.rglob("_win_probe.txt"))
        if hits:
            line = hits[0].read_text(encoding="utf-8").strip()
            break
        time.sleep(0.05)
    out, err = proc.communicate(timeout=90)
    assert proc.returncode == 0, err or out
    assert line, "probe file missing"
    window, _pytest_pid, on_console = window_and_console(line)
    assert window == 0
    assert proc.pid not in on_console


def test_r041_crlf_multiline_mutant_killed(tmp_path):
    """R-041, TASK-031 Requirement 3 (M07): a CRLF mutant whose old and new span two lines is killed."""
    ws = workspace(tmp_path)
    init_pkg(ws, crlf=True)
    body = {"mutants": [{
        "id": "ml", "file": "demo/calc.py",
        "pairs": [{"old": "def add(a, b):\n    return a + b", "new": "def add(a, b):\n    return a - b"}],
        "tests": ["tests/test_calc.py"],
        "expect_fail": ["tests/test_calc.py::test_add", "tests/test_calc.py::test_sub"],
    }]}
    mp = mutants_path(ws, "ml", body)
    git(ws, "add", "run/supervisor/ml-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0 and "ml: killed" in p.stdout


def test_r041_parent_conftest_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c) (M11): a tracked tests/conftest.py above tests/unit/ is in the cache key."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "tests/unit/test_u.py", "from demo.calc import add\n\ndef test_u():\n    assert add(1, 1) == 2\n")
    git(ws, "add", "tests/unit/test_u.py")
    body = {"mutants": [{
        "id": "u1", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/unit/test_u.py"],
        "expect_fail": ["tests/unit/test_u.py::test_u"],
    }]}
    mp = mutants_path(ws, "ucf", body)
    git(ws, "add", "run/supervisor/ucf-mutants.json")
    assert run_mr(ws, mp).returncode == 0
    cache = ws / "run/supervisor/mutation-cache/ucf.jsonl"
    n1 = len([l for l in cache.read_text(encoding="utf-8").splitlines() if l.strip()])
    write(ws, "tests/conftest.py", "# changed\n")
    git(ws, "add", "tests/conftest.py")
    p2 = run_mr(ws, mp)
    assert "run=1" in p2.stdout
    assert cache_last_outcome(ws, "ucf") == "killed"
    n2 = len([l for l in cache.read_text(encoding="utf-8").splitlines() if l.strip()])
    assert n2 == n1 + 1


def test_r041_refuse_tracked_data_link(tmp_path):
    """R-041, TASK-031 Requirement 2 (M13): a tracked folder replaced by a link outside the Workspace is refused."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "data/x.txt", "payload\n")
    git(ws, "add", "data/x.txt")
    outside = tmp_path / "outside_data"
    outside.mkdir()
    (outside / "x.txt").write_text("payload\n", encoding="utf-8")
    data_dir = ws / "data"
    shutil.rmtree(data_dir)
    try:
        os.symlink(str(outside), str(data_dir), target_is_directory=True)
    except (OSError, NotImplementedError) as e:
        if sys.platform != "win32":
            pytest.skip("this account cannot create a symbolic link here (%s)" % e)
        j = subprocess.run(["cmd", "/c", "mklink", "/J", str(data_dir), str(outside)],
                           **test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 30}))
        if j.returncode != 0:
            pytest.skip("neither a symbolic link nor a junction could be made here (%s)" % j.stderr)
    mp = mutants_path(ws, "tdl", basic_mutant())
    git(ws, "add", "run/supervisor/tdl-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 2
    assert "link" in p.stderr.lower()
    assert "data" in p.stderr
    assert not (ws / "run/supervisor/mutation-cache/tdl.jsonl").exists()


def test_r041_refuse_dotdot_names_path_form(tmp_path):
    """R-041, TASK-031 Requirement 1 (M21): .. in a mutant file path is refused as not relative, not as untracked."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["file"] = "demo/../demo/calc.py"
    mp = mutants_path(ws, "ddm", body)
    p = run_mr(ws, mp)
    assert p.returncode == 2
    assert "git index" not in p.stderr
    assert ".." in p.stderr or "not relative" in p.stderr


def test_r041_duplicate_old_not_applied(tmp_path):
    """R-041, TASK-031 Requirement 3 (M22): old text found more than once yields not applied."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "demo/dup.py", "x = 1\nx = 1\n")
    write(ws, "tests/test_dup.py", "import demo.dup\n\ndef test_dup():\n    assert demo.dup.x == 1\n")
    git(ws, "add", "demo/dup.py", "tests/test_dup.py")
    body = {"mutants": [{
        "id": "dup", "file": "demo/dup.py",
        "pairs": [{"old": "x = 1", "new": "x = 2"}],
        "tests": ["tests/test_dup.py"],
        "expect_fail": ["tests/test_dup.py::test_dup"],
    }]}
    mp = mutants_path(ws, "dup", body)
    git(ws, "add", "run/supervisor/dup-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 1 and "dup: not applied" in p.stdout


def test_r041_root_env_copied_when_extra_test_runs(tmp_path):
    """R-041, TASK-031 Requirement 2 (M23): the root .env is copied so an extra listed test does not error the run."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, ".env", "SECRET=fixture-value\n")
    write(ws, "tests/test_calc.py", "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n")
    write(ws, "tests/test_env.py", textwrap.dedent("""
def test_env():
    assert open(".env", encoding="utf-8").read().strip().endswith("fixture-value")
"""))
    git(ws, "add", "tests/test_calc.py", "tests/test_env.py")
    body = {"mutants": [{
        "id": "env2", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_calc.py", "tests/test_env.py"],
        "expect_fail": ["tests/test_calc.py::test_add"],
    }]}
    mp = mutants_path(ws, "env2", body)
    git(ws, "add", "run/supervisor/env2-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0 and "env2: killed" in p.stdout


def test_r041_pytest_setup_error_is_run_error(tmp_path):
    """R-041, TASK-031 Requirement 4 (M25): a pytest ERROR in setup makes the mutant outcome error, not killed."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "tests/test_setup_err.py", textwrap.dedent("""
import pytest

@pytest.fixture
def broken():
    raise RuntimeError("setup failed")

def test_broken(broken):
    pass

def test_calc():
    from demo.calc import add
    assert add(1, 1) == 2
"""))
    git(ws, "add", "tests/test_setup_err.py")
    body = {"mutants": [{
        "id": "se", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_setup_err.py"],
        "expect_fail": ["tests/test_setup_err.py::test_calc"],
    }]}
    mp = mutants_path(ws, "se", body)
    git(ws, "add", "run/supervisor/se-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 3
    assert "se: error" in p.stdout


def test_r041_extract_archive_tar_well_formed(tmp_path):
    """R-041, TASK-031-r4 B5: a well-formed git-archive-style tar extracts under the copy root."""
    import io
    import tarfile
    mod = load_program("mutation-run")
    dest = tmp_path / "tree"
    dest.mkdir()
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode="w") as tf:
        data = b"payload\n"
        ti = tarfile.TarInfo("demo/calc.py")
        ti.size = len(data)
        tf.addfile(ti, io.BytesIO(data))
    mod.extract_archive_tar(bio.getvalue(), str(dest))
    assert (dest / "demo" / "calc.py").read_bytes() == b"payload\n"


@pytest.mark.parametrize("member_name", [
    "/etc/passwd",
    "demo/../../escape.txt",
    "bad\\name.txt",
    "bad:name.txt",
])
def test_r041_extract_archive_tar_refuses_bad_member(tmp_path, member_name):
    """R-041, TASK-031-r4 B5: unsafe archive member names are refused with exit 2."""
    import io
    import tarfile
    mod = load_program("mutation-run")
    dest = tmp_path / "tree"
    dest.mkdir()
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode="w") as tf:
        ti = tarfile.TarInfo(member_name)
        ti.size = 0
        tf.addfile(ti, io.BytesIO(b""))
    with pytest.raises(mod.Refuse):
        mod.extract_archive_tar(bio.getvalue(), str(dest))


def test_r041_extract_archive_tar_refuses_non_file(tmp_path):
    """R-041, TASK-031-r4 B5: archive members that are neither files nor directories are refused."""
    import io
    import tarfile
    mod = load_program("mutation-run")
    dest = tmp_path / "tree"
    dest.mkdir()
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode="w") as tf:
        ti = tarfile.TarInfo("weird")
        ti.type = tarfile.LNKTYPE
        ti.size = 0
        tf.addfile(ti)
    with pytest.raises(mod.Refuse):
        mod.extract_archive_tar(bio.getvalue(), str(dest))


def test_r041_grandchild_holding_pipes_times_out(tmp_path):
    """R-041, TASK-031 S7, handoff/TASK-031-r7.md item 3: a grandchild holding run_process's real pipes is bounded."""
    import signal

    holder_pid_file = tmp_path / "grandchild_holder.pid"
    pytest_pid_file = tmp_path / "grandchild_pytest.pid"
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "pytest.ini", "[pytest]\naddopts = -s\n")
    git(ws, "add", "pytest.ini")
    write(ws, "tests/test_pipe_hold.py", textwrap.dedent("""
import os
import subprocess
import sys
import time

_holder = None


def test_hold_pipes():
    global _holder
    _holder = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(3600)"],
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    with open(HOLDER_PID_JSON, "w", encoding="utf-8") as f:
        f.write(str(_holder.pid))
        f.flush()
    with open(PYTEST_PID_JSON, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
        f.flush()
    while True:
        time.sleep(0.2)


def teardown_module():
    global _holder
    if _holder is not None and _holder.poll() is None:
        _holder.kill()
        _holder.wait(timeout=10)
""").replace("HOLDER_PID_JSON", json.dumps(str(holder_pid_file))).replace(
        "PYTEST_PID_JSON", json.dumps(str(pytest_pid_file))))
    git(ws, "add", "tests/test_pipe_hold.py")
    body = {"mutants": [{
        "id": "pipe", "file": "tests/test_pipe_hold.py",
        "pairs": [{"old": "time.sleep(0.2)", "new": "time.sleep(0.2)"}],
        "tests": ["tests/test_pipe_hold.py"],
        "expect_fail": ["tests/test_pipe_hold.py::test_hold_pipes"],
    }]}
    mp = mutants_path(ws, "pipe", body)
    git(ws, "add", "run/supervisor/pipe-mutants.json")

    def _end_pid_tree(pid):
        if pid_dead(pid):
            return
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(pid)],
                capture_output=True,
                **test_conftest.windowless_kwargs({"stdin": subprocess.DEVNULL, "timeout": 30}),
            )
        else:
            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except (OSError, ValueError, ProcessLookupError):
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass

    def _read_pid(path):
        if not path.is_file():
            return None
        try:
            return int(path.read_text(encoding="utf-8").strip())
        except ValueError:
            return None

    try:
        t0 = time.time()
        p = run_mr(ws, mp, timeout=5, harness_slack=120)
        elapsed = time.time() - t0
        assert elapsed >= 5, "the run did not wait through the mutant bound"
        assert elapsed < 5 + 120, "run exceeded bound plus 120 s"
        assert p.returncode == 3
        assert "pipe: error (timed out)" in p.stdout
        assert holder_pid_file.is_file(), "holder pid file missing; the hold never started"
        holder_pid = _read_pid(holder_pid_file)
        pytest_pid = _read_pid(pytest_pid_file)
        assert holder_pid is not None
        assert pytest_pid is not None
        deadline = time.time() + 10
        while time.time() < deadline:
            if pid_dead(holder_pid) and pid_dead(pytest_pid):
                break
            time.sleep(0.1)
        assert pid_dead(holder_pid), "holder still alive after run"
        assert pid_dead(pytest_pid), "fixture pytest still alive after run"
    finally:
        for path in (holder_pid_file, pytest_pid_file):
            pid = _read_pid(path)
            if pid is not None:
                _end_pid_tree(pid)


def test_r041_pytest_survives_kill_stops_run(tmp_path, home_of_the_tests, monkeypatch):
    """R-041, TASK-031 S7, handoff/TASK-031-r6.md item 6: a pytest that outlives kill ends the run at exit 3 without running the next mutant."""
    import io
    import signal
    from contextlib import redirect_stderr, redirect_stdout

    mod = load_program("mutation-run")
    real_kill = mod.kill_tree
    ws = workspace(tmp_path)
    init_pkg(ws)
    loop_pid = tmp_path / "loop.pid"
    write(ws, "tests/test_loop.py", textwrap.dedent("""
import os

def test_loop():
    open(%r, "w", encoding="utf-8").write(str(os.getpid()))
    while True:
        pass
""" % str(loop_pid).replace("\\", "\\\\")))
    git(ws, "add", "tests/test_loop.py")
    body = {"mutants": [
        {"id": "loop", "file": "tests/test_loop.py", "pairs": [{"old": "pass", "new": "pass"}],
         "tests": ["tests/test_loop.py"], "expect_fail": ["tests/test_loop.py::test_loop"]},
        {"id": "two", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
         "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]},
    ]}
    mutants_path(ws, "surv", body)
    git(ws, "add", "run/supervisor/surv-mutants.json")
    scratch = home_of_the_tests / ".cursor-bridge" / "scratch" / "proj"
    scratch.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(ws)
    monkeypatch.setenv("HOME", str(home_of_the_tests))
    monkeypatch.setenv("USERPROFILE", str(home_of_the_tests))
    monkeypatch.setattr(mod, "kill_tree", lambda _proc: None)
    monkeypatch.setattr(
        sys, "argv",
        ["mutation-run.py", "run/supervisor/surv-mutants.json",
         "--scratch", str(scratch), "--mutant-timeout", "3"],
    )
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    try:
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = mod.run_main()
        stdout = out_buf.getvalue()
        stderr = err_buf.getvalue()
        assert rc == 3
        assert "loop: error (timed out)" in stdout
        assert "two:" not in stdout
        assert "mutation-run:" in stderr and "3" in stderr
        assert "internal error" not in stderr
    finally:
        mod.kill_tree = real_kill
        if loop_pid.is_file():
            try:
                lp = int(loop_pid.read_text(encoding="utf-8").strip())
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/T", "/F", "/PID", str(lp)],
                        capture_output=True,
                        **test_conftest.windowless_kwargs({"stdin": subprocess.DEVNULL, "timeout": 30}),
                    )
                else:
                    os.killpg(os.getpgid(lp), signal.SIGKILL)
            except (OSError, ValueError, ProcessLookupError):
                pass
        work = scratch / "mutation-run-surv"
        if work.is_dir():
            shutil.rmtree(work, ignore_errors=True)


def test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out(tmp_path, home_of_the_tests):
    """R-041, TASK-031 S7, handoff/TASK-031-r6.md item 7: a pipe holder outside the killed tree holds the real pipes until the bound."""
    import signal

    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "pytest.ini", "[pytest]\naddopts = -s\n")
    git(ws, "add", "pytest.ini")
    write(ws, ".env", "SECRET=copy\n")
    git(ws, "add", ".env")
    pid_file = tmp_path / "holder.pid"
    write(ws, "tests/pipe_hold_middle.py", textwrap.dedent("""
import os
import subprocess
import sys

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
root = os.getcwd()
kw = {} if sys.platform == "win32" else {"start_new_session": True}
holder = subprocess.Popen(
    [sys.executable, "-c", "import os, time; os.chdir(%r); time.sleep(3600)" % root],
    stdin=subprocess.DEVNULL,
    stdout=sys.stdout,
    stderr=sys.stderr,
    cwd=root,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    **kw,
)
open(sys.argv[1], "w").write(str(holder.pid))
"""))
    write(ws, "tests/test_pipe_hold_copy.py", textwrap.dedent("""
import subprocess
import sys
import time

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def test_hold_pipes():
    subprocess.run(
        [sys.executable, "tests/pipe_hold_middle.py", PIDFILE_JSON],
        stdin=subprocess.DEVNULL,
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        timeout=60,
    )
    while True:
        time.sleep(0.2)
""").replace("PIDFILE_JSON", json.dumps(str(pid_file))))
    git(ws, "add", "tests/pipe_hold_middle.py", "tests/test_pipe_hold_copy.py")
    body = {"mutants": [{
        "id": "phc", "file": "tests/test_pipe_hold_copy.py",
        "pairs": [{"old": "time.sleep(0.2)", "new": "time.sleep(0.2)"}],
        "tests": ["tests/test_pipe_hold_copy.py"],
        "expect_fail": ["tests/test_pipe_hold_copy.py::test_hold_pipes"],
    }]}
    mp = mutants_path(ws, "phc", body)
    git(ws, "add", "run/supervisor/phc-mutants.json")
    work_sub = home_of_the_tests / ".cursor-bridge" / "scratch" / "proj" / "mutation-run-phc"
    try:
        t0 = time.time()
        p = run_mr(ws, mp, timeout=5, home_env=home_of_the_tests, harness_slack=120)
        elapsed = time.time() - t0
        assert elapsed >= 30, "the hold on the real pipes did not last through the bounded wait"
        assert elapsed < 5 + 120, "run exceeded bound plus 120 s"
        assert p.returncode == 3
        assert "phc: error (timed out)" in p.stdout
        assert "internal error" not in p.stderr
        assert pid_file.is_file()
        assert not (work_sub / "tree" / ".env").exists(), "copied .env must be absent while the holder lives"
        if sys.platform == "win32":
            assert work_sub.is_dir(), "holder cwd should keep mutation-run-phc on disk until the holder ends"
            assert (work_sub / "tree").is_dir(), "the copy root stays while the holder's cwd is inside it"
    finally:
        if pid_file.is_file():
            try:
                hp = int(pid_file.read_text(encoding="utf-8").strip())
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(hp)],
                        capture_output=True,
                        **test_conftest.windowless_kwargs({"stdin": subprocess.DEVNULL, "timeout": 30}),
                    )
                else:
                    os.kill(hp, signal.SIGKILL)
            except (OSError, ValueError):
                pass
        if work_sub.is_dir():
            shutil.rmtree(work_sub, ignore_errors=True)


def test_task031_r9_iniconfig_not_importable_refused(tmp_path, home_of_the_tests):
    """R-041, TASK-031 S7, handoff/TASK-031-r9.md: when iniconfig cannot be imported while reading a root
    tox.ini, mutation-run exits 2 with the fixed refusal message and writes no cache line."""
    block = tmp_path / "block_iniconfig"
    pkg = block / "iniconfig"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("raise ImportError('blocked')\n", encoding="ascii")
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "tox.ini", "[tox]\nenvlist = py312\n\n[pytest]\n")
    git(ws, "add", "tox.ini")
    git(ws, "commit", "-q", "-m", "tox")
    mp = mutants_path(ws, "inicfg", {"mutants": [{"id": "m1", "file": "demo/calc.py",
                                                  "pairs": [{"old": "return a + b", "new": "return b + a"}],
                                                  "tests": ["tests/test_calc.py"],
                                                  "expect_fail": ["tests/test_calc.py::test_add"]}]})
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env["HOME"] = env["USERPROFILE"] = str(home_of_the_tests)
    env["PYTHONPATH"] = str(block) + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, MUTATION_RUN, str(mp), "--mutant-timeout", "60"]
    p = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env, timeout=90,
                       **test_conftest.windowless_kwargs({}))
    assert p.returncode == 2, p.stdout + p.stderr
    assert "mutation-run: pytest's iniconfig is not importable" in p.stdout + p.stderr
    assert not (ws / "run/supervisor/mutation-cache/inicfg.jsonl").exists()


@pytest.mark.skipif(os.name != "nt", reason="case-insensitive iniconfig shadow names are a Windows filesystem concern")
def test_task031_r10_iniconfig_shadow_case_insensitive_refused(tmp_path, home_of_the_tests):
    """R-041, TASK-031 S7, handoff/TASK-031-r10.md: a root tox.ini and a differently cased top-level IniConfig.py
    exit 2 with the shadow refusal and no cache line."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "tox.ini", "[tox]\nenvlist = py312\n\n[pytest]\n")
    write(ws, "IniConfig.py", "x = 1\n")
    git(ws, "add", "tox.ini", "IniConfig.py")
    git(ws, "commit", "-q", "-m", "tox and shadow")
    mp = mutants_path(ws, "r10case", {"mutants": [{"id": "m1", "file": "demo/calc.py",
                                                    "pairs": [{"old": "return a + b", "new": "return b + a"}],
                                                    "tests": ["tests/test_calc.py"],
                                                    "expect_fail": ["tests/test_calc.py::test_add"]}]})
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env["HOME"] = env["USERPROFILE"] = str(home_of_the_tests)
    cmd = [sys.executable, MUTATION_RUN, str(mp), "--mutant-timeout", "60"]
    p = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env, timeout=90,
                       **test_conftest.windowless_kwargs({}))
    assert p.returncode == 2, p.stdout + p.stderr
    assert "mutation-run: a top-level iniconfig in the project would shadow pytest's iniconfig" in p.stdout + p.stderr
    assert not (ws / "run/supervisor/mutation-cache/r10case.jsonl").exists()


def test_task031_r11_extension_suffix_shadow_refused(tmp_path, home_of_the_tests):
    """R-041, TASK-031 S7, handoff/TASK-031-r11.md: a top-level extension-module filename that also ends in a shorter
    suffix is refused with the Requirement 1 message naming tomllib and writes no cache line."""
    import importlib.machinery
    ext_suffixes = [s for s in importlib.machinery.EXTENSION_SUFFIXES if len(s) > len(".pyd")]
    if not ext_suffixes:
        pytest.skip("no platform extension suffix longer than .pyd")
    ext_name = "tomllib" + ext_suffixes[0]
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, ext_name, "not a real extension\n", binary=True)
    git(ws, "add", ext_name)
    git(ws, "commit", "-q", "-m", "shadow ext")
    mp = mutants_path(ws, "r11ext", {"mutants": [{"id": "m1", "file": "demo/calc.py",
                                                   "pairs": [{"old": "return a + b", "new": "return b + a"}],
                                                   "tests": ["tests/test_calc.py"],
                                                   "expect_fail": ["tests/test_calc.py::test_add"]}]})
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env["HOME"] = env["USERPROFILE"] = str(home_of_the_tests)
    cmd = [sys.executable, MUTATION_RUN, str(mp), "--mutant-timeout", "60"]
    p = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env, timeout=90,
                       **test_conftest.windowless_kwargs({}))
    assert p.returncode == 2, p.stdout + p.stderr
    assert (
        "mutation-run: a top-level module tomllib in the project would shadow "
        "an installed or standard-library module"
    ) in p.stdout + p.stderr
    assert not (ws / "run/supervisor/mutation-cache/r11ext.jsonl").exists()
