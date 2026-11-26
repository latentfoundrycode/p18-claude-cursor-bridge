"""TASK-086b (R-107; docs/DESIGN.md, "Change: the improvements release", C39 and its table): the launcher's two
review refusals read the branch's built set and the resolved roster's recorded deviation, and every builder row
the launcher writes carries `start_commit` and `clean`. The supervisor's acceptance tests, written before the
brief's run and committed before the checkpoint; the builder reads and runs them, never edits them.

D-003 (`snapshot_taken --> snapshot_taken`): a review launch refused is exit 125, the stand-in never run, no
started line and no run log row; the refusals are a review by a model of any family in the built set, of any
builder's family where the set is unknown, every review where the set cannot be read inside a repository or the
roster program cannot be loaded, and a review on the roster builder model unless the resolved roster's deviation
names it for this branch, the set is known, the model's family is not in it and the entry's families equal the set
read at the launch (the refusal then says to resolve again). D-004 (`p_bridge_run --> ds_runs_log`): on a builder
row "the launch's head and clean", the head written under the key `start_commit` (the key `head` keeps the
command's program name); `ds_runs_log --> p_bridge_run`: the built set, never the last builder run alone.

Every launch is `python bridge/cursor-bridge/bridge-run.py ...` started as a windowless subprocess
(CREATE_NO_WINDOW on Windows) from a scratch git repository under pytest's temporary folder: a `main` with one
commit holding a `.gitignore` that ignores `run/` (as the project's own does) and a README, the branch `task-1`
checked out, and a `run/` folder so the launcher writes its record. A stand-in `cursor-agent` (a .cmd on Windows, a
shell file elsewhere) is first on PATH; it appends a line to a marker file outside the repository and exits with the
code in STUB_EXIT. HOME and USERPROFILE are the suite's temporary home (tests/conftest.py), LOCALAPPDATA a
temporary folder, git's global and system configuration empty, every GIT_ variable of the suite's own environment
removed and GIT_CEILING_DIRECTORIES the test's temporary folder. The run record `run/launcher/runs.jsonl`,
`docs/ROSTER.json` and `docs/ROSTER.resolved.json` are written by the test (a builder row has the launcher's shape,
and TASK-086b's two keys only where the test gives them). Nothing is launched in this repository; the real
cursor-agent is never called; `roster-check.py` runs only in step 3b's test, from its scratch repository, with
`--no-probe` and ROSTER_NOW fixed.

The words the tests read: a refusal is the first line of standard error and begins `bridge-run: refused - `, exit
125, its text ASCII; the family refusal (R1, R2) names the model and keeps `is of the <family> family` and the word
`rebuild`; a refusal that says to resolve again holds the word `resolve` (the file name `ROSTER.resolved.json` not
counted) and the word `again`; an unknown set's refusal names its cause (the report file's name, or `runs.jsonl`); a
set that cannot be read names `detached`, `runs.jsonl`, `git` or `main`; the loader's refusal names `bridge-check.py`.

enforces: docs/BUILD_PLAN.md, TASK-086b, Done when; docs/REQUIREMENTS.md R-107; docs/DESIGN.md C39 and its table;
D-003; D-004
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

import pytest

from roster_rows import (BRANCH, COMPOSER, FULL, GIT, GPT, GROK_B, GROK_R, NATIVE, REVIEW_A,  # noqa: F401
                         lies_in_no_repository, rebuild_text, review_row, row)

HERE = os.path.dirname(os.path.abspath(__file__))
CB = os.path.abspath(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge"))
PROG = os.path.join(CB, "bridge-run.py")
ROSTER_PROG = os.path.join(CB, "roster-check.py")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
TIMEOUT = 120

REFUSED = "bridge-run: refused - "
STARTED_RX = re.compile(r"^bridge-run: started \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
COMMIT_RX = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
NOW = "2026-11-25T09:00"

MYSTERY = "mystery-builder-2"       # a model whose family no rule names

REVIEW_PROMPT = "Review run/review/REVIEW-TASK-001.diff"
REPORT2 = "handoff/TASK-002-r1-report.md"
OLD_KEYS = {"id", "kind", "head", "model", "branch", "limit", "seconds", "exit", "healthy", "boundary", "waited", "slot",
            "pid", "child_pid", "brief", "round", "brief_sha256", "lift", "brief_name", "merge_ids", "lift_line", "cause"}
NEW_KEYS = {"start_commit", "clean"}

HOLDER_SRC = r'''
import importlib.util, os, sys, time
spec = importlib.util.spec_from_file_location("bridge_run_slot_holder", sys.argv[1])
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)
lock_path, _holder = br.heavy_state_paths()
os.makedirs(os.path.dirname(lock_path), exist_ok=True)
fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
if not br._try_lock_byte(fd):
    sys.exit(2)
open(sys.argv[2], "w").close()
deadline = time.time() + 90
while time.time() < deadline and not os.path.exists(sys.argv[3]):
    time.sleep(0.1)
'''


# --- helpers -------------------------------------------------------------------------------------

def base_env():
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run_quiet(args, cwd, env=None, timeout=TIMEOUT):
    return subprocess.run(args, cwd=str(cwd), env=env or base_env(), capture_output=True, timeout=timeout,
                          stdin=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def git(ws, *args):
    p = run_quiet(GIT + list(args), ws)
    assert p.returncode == 0, "fixture git %s failed: %s" % (" ".join(args), p.stderr.decode("utf-8", "replace"))
    return p.stdout.decode("utf-8", "replace").strip()


def head(ws):
    return git(ws, "rev-parse", "HEAD")


def write(ws, rel, data):
    path = ws / rel.replace("/", os.sep)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8", newline="\n")
    return path


def brief_text(name="TASK-001"):
    return "# %s\n\n## Objective\nFixture brief %s.\n\n## Scope\n- a.py\n" % (name, name)


def roster_text(profiles=None, other_pool="available"):
    return json.dumps({"other_pool": other_pool, "review_a": REVIEW_A, "profiles": profiles or [NATIVE]}, indent=2) + "\n"


def resolved_text(builder=COMPOSER, review_b=GPT, deviation=None):
    data = {"profile": "native", "builder": builder, "review_a": REVIEW_A, "review_b": review_b, "families": {}}
    if deviation is not None:
        data["deviation"] = deviation
    return json.dumps(data, indent=2) + "\n"


def scratch_repo(tmp_path, main=True, files=None, name="ws"):
    """A repository with `main` (one commit: the .gitignore, a README and `files`) and the branch `task-1` checked
    out; with main=False it is made on `task-1` alone and has no `main`. A `run/` folder (ignored) is made after."""
    ws = tmp_path / "p" / name
    ws.mkdir(parents=True)
    git(ws, "init", "-q", "-b", "main" if main else BRANCH)
    write(ws, ".gitignore", "run/\n")
    write(ws, "README.md", "fixture\n")
    for rel, text in (files or {}).items():
        write(ws, rel, text)
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "base")
    if main:
        git(ws, "checkout", "-q", "-b", BRANCH)
    (ws / "run").mkdir(exist_ok=True)
    return ws


def commit(ws, msg, files=None):
    for rel, text in (files or {}).items():
        write(ws, rel, text)
        git(ws, "add", "--", rel)
    git(ws, "commit", "-q", "--allow-empty", "-m", msg)
    return head(ws)


def record(ws):
    return ws / "run" / "launcher" / "runs.jsonl"


def record_bytes(ws):
    path = record(ws)
    return path.read_bytes() if path.is_file() else None


def write_record(ws, *lines, tail=b"\n"):
    """The record as JSON lines; `tail` ends the last line (b"" leaves it torn, without its line feed)."""
    data = b"\n".join(l if isinstance(l, bytes) else l.encode("utf-8") for l in lines)
    write(ws, "run/launcher/runs.jsonl", data + (tail if lines else b""))


def write_stand_in(tmp_path, touch=None):
    """The stand-in `cursor-agent`; with `touch` it also writes that file in the folder it runs in, as a builder
    run changes the tree after it started."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    marker = tmp_path / "stand-in-ran.txt"
    if sys.platform == "win32":
        extra = 'echo made> "%s"\r\n' % touch if touch else ""
        text = ('@echo off\r\necho ran>> "%s"\r\n%sif "%%STUB_EXIT%%"=="" exit /b 0\r\nexit /b %%STUB_EXIT%%\r\n'
                % (marker, extra))
        (bin_dir / "cursor-agent.cmd").write_text(text, encoding="ascii")
    else:
        extra = 'echo made > "%s"\n' % touch if touch else ""
        text = '#!/bin/sh\necho ran >> "%s"\n%sexit "${STUB_EXIT:-0}"\n' % (marker, extra)
        for name in ("cursor-agent", "cursor-agent.exe"):
            p = bin_dir / name
            p.write_text(text, encoding="ascii")
            p.chmod(0o755)


def launch_env(tmp_path, stub_exit=0, allow_any=False, path=None, extra=None):
    env = base_env()
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    env.pop("BRIDGE_RUN_SLOT_SCALE", None)
    if allow_any:
        env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    rest = os.environ.get("PATH", "") if path is None else path
    env["PATH"] = os.pathsep.join([str(tmp_path / "bin"), os.path.dirname(sys.executable), rest])
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    env["GIT_CEILING_DIRECTORIES"] = str(tmp_path)
    env["STUB_EXIT"] = str(stub_exit)
    env.update(extra or {})
    return env


class Run(object):
    def __init__(self, p, ws, before, marker):
        self.rc = p.returncode
        self.raw = p.stderr
        self.err = p.stderr.decode("utf-8", "replace")
        self.ws = ws
        self.before = before
        self.marker = marker


def launch(tmp_path, ws, cmd, kind, limit="300", prog=PROG, **env_kw):
    """One launcher run from `ws`, windowless; the marker removed first, the record read before."""
    if not (tmp_path / "bin").exists():
        write_stand_in(tmp_path)
    marker = tmp_path / "stand-in-ran.txt"
    if marker.exists():
        marker.unlink()
    before = record_bytes(ws)
    p = subprocess.run([sys.executable, prog, "--limit", limit, "--kind", kind, "--"] + list(cmd), cwd=str(ws),
                       env=launch_env(tmp_path, **env_kw), capture_output=True, timeout=TIMEOUT,
                       stdin=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return Run(p, ws, before, marker)


def agent(model, prompt, workspace=None):
    cmd = ["cursor-agent"]
    if workspace is not None:
        cmd += ["--workspace", str(workspace)]
    return cmd + ["-p", "--force", "--model", model, prompt]


def review(tmp_path, ws, model, workspace=None, **kw):
    return launch(tmp_path, ws, agent(model, REVIEW_PROMPT, workspace), "review", **kw)


def build(tmp_path, ws, model=COMPOSER, brief="TASK-001", workspace=None, **kw):
    return launch(tmp_path, ws, agent(model, "Read handoff/%s.md and do the work" % brief, workspace), "builder", **kw)


def python_build(tmp_path, ws, **kw):
    """A builder row from a command that is not cursor-agent (BRIDGE_RUN_ALLOW_ANY, as the tests' own helpers do)."""
    return launch(tmp_path, ws, [sys.executable, "-c", "pass"], "builder", allow_any=True, **kw)


def refused(res):
    """A refusal: exit 125, the refusal the first line, ASCII, no traceback, nothing started, no row written."""
    assert "Traceback" not in res.err, res.err
    assert res.rc == 125, "rc %r, stderr:\n%s" % (res.rc, res.err)
    assert res.err.startswith(REFUSED), res.err
    assert "bridge-run: started" not in res.err, res.err
    assert not res.marker.exists(), "the stand-in ran"
    assert record_bytes(res.ws) == res.before, "a run log row was written"
    try:
        res.raw.decode("ascii")
    except UnicodeDecodeError:
        pytest.fail("the refusal is not ASCII: %r" % res.raw)
    return res.err


def new_row(res):
    """The one row the launch appended to the record (after any torn last line it began a new line for)."""
    after = record_bytes(res.ws) or b""
    before = res.before or b""
    assert after.startswith(before), "the earlier record changed:\n%r\n%r" % (before, after)
    added = after[len(before):].strip(b"\r\n")
    lines = [l for l in added.split(b"\n") if l.strip()]
    assert len(lines) == 1, "one row expected, got %r" % added
    return json.loads(lines[0].decode("utf-8"))


def ran(res, rc=0, stand_in=True):
    """An accepted launch: the started line first, the exit line last, exit rc, the stand-in run, one new row."""
    assert "Traceback" not in res.err, res.err
    assert res.rc == rc, "rc %r, stderr:\n%s" % (res.rc, res.err)
    lines = res.err.splitlines()
    assert lines and STARTED_RX.match(lines[0]), res.err
    assert lines[-1] == "bridge-run: exit %d" % rc, res.err
    if stand_in:
        assert res.marker.exists(), "the stand-in did not run"
    return new_row(res)


def says_resolve_again(text):
    t = text.replace("ROSTER.resolved.json", "").lower()
    return "resolve" in t and "again" in t


def assert_family_refusal(text, model, family):
    assert model in text, text
    assert "is of the %s family" % family in text, text
    assert "rebuild" in text, text


def unknown_by_report(tmp_path, files=None):
    """A branch that adds a report file whose brief has no builder row: the set is unknown, its cause the report."""
    ws = scratch_repo(tmp_path, files=files)
    commit(ws, "a report without its row", {REPORT2: "round 1\n"})
    return ws


def path_without_git(tmp_path, how):
    """A PATH on which `git` fails (a script that prints a fatal line and exits 128) or does not start (no git at
    all); on Windows a program started by name without a shell is found as an .exe only, so the .bat stands for
    "does not start" there. The stand-in's folder and the interpreter's lead it (launch_env); the system folder
    stays on Windows for cmd.exe."""
    fake = tmp_path / ("fake-git-" + how)
    fake.mkdir()
    if how == "fails":
        if sys.platform == "win32":
            for name in ("git.bat", "git.cmd"):
                (fake / name).write_text("@echo off\r\necho fatal: git is not answering 1>&2\r\nexit /b 128\r\n",
                                         encoding="ascii")
        else:
            script = fake / "git"
            script.write_text("#!/bin/sh\necho 'fatal: git is not answering' >&2\nexit 128\n", encoding="ascii")
            os.chmod(str(script), 0o755)
    parts = [str(fake)]
    if sys.platform == "win32" and os.environ.get("SystemRoot"):
        parts.append(os.path.join(os.environ["SystemRoot"], "System32"))
    path = os.pathsep.join(parts)
    full = os.pathsep.join([str(tmp_path / "bin"), os.path.dirname(sys.executable), path])
    found = shutil.which("git", path=full)
    if found and not os.path.abspath(found).startswith(str(fake)):
        pytest.skip("a real git lies on the reduced PATH: %s" % found)
    return path


def broken_copy(tmp_path, breakage):
    """A copy of bridge/cursor-bridge under the temporary folder whose roster-check.py cannot be loaded as the
    launcher needs it; the real file is never touched."""
    cb = tmp_path / "cb"
    shutil.copytree(CB, str(cb), ignore=shutil.ignore_patterns("__pycache__"))
    target = cb / "roster-check.py"
    if breakage == "raises":
        target.write_text("raise RuntimeError('the roster program is broken on purpose')\n", encoding="ascii")
    elif breakage == "lacks-built-families":
        target.write_text("def family_of(model_id, override=None):\n    return None\n", encoding="ascii")
    elif breakage == "lacks-family-of":
        target.write_text("def built_families(*args, **kwargs):\n    return {'status': 'empty', 'families': set()}\n",
                          encoding="ascii")
    elif breakage == "built-families-raises":
        target.write_text("def family_of(model_id, override=None):\n    return None\n"
                          "def built_families(*args, **kwargs):\n"
                          "    raise RuntimeError('the built set is broken on purpose')\n", encoding="ascii")
    else:
        target.unlink()
    return str(cb / "bridge-run.py")


def resolve(ws):
    env = base_env()
    env["ROSTER_NOW"] = NOW
    p = run_quiet([sys.executable, ROSTER_PROG, "docs/ROSTER.json", "--no-probe"], ws, env=env)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


# --- R1: the family refusal reads the built set ------------------------------------------------------

def test_r1_a_branch_built_by_one_family_refuses_its_reviewer(tmp_path):
    """R1, R5: a known set of one family (a grok builder row of the branch) refuses a review by a model of that
    family, the refusal naming the model and keeping `is of the xai family` and `rebuild`; a reviewer of another
    family runs (pins an answer of the checkpoint)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, review_row(), row(GROK_B))
    assert_family_refusal(refused(review(tmp_path, ws, GROK_R)), GROK_R, "xai")
    assert ran(review(tmp_path, ws, GPT))["kind"] == "review"


def test_r1_a_branch_built_by_two_families_refuses_a_reviewer_of_either(tmp_path):
    """R1, R5; M3 (the last run read in place of the set): a grok row, then a composer row of the same branch, both
    counted (neither carries the keys), refuse a review of either family, each refusal naming the built set (both
    families); the checkpoint reads the last run alone and lets the grok review through (red there)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GROK_B), row(COMPOSER, rnd=2))
    text = refused(review(tmp_path, ws, GROK_R))
    assert_family_refusal(text, GROK_R, "xai")
    assert "cursor" in text, text
    text = refused(review(tmp_path, ws, COMPOSER))
    assert_family_refusal(text, COMPOSER, "cursor")
    assert "xai" in text, text
    ran(review(tmp_path, ws, GPT))


def test_r1_a_run_dropped_by_a_clean_rebuild_no_longer_refuses(tmp_path):
    """R1: the set is TASK-086a's, read with the folder the branch is read in, so git drops a grok run that a clean
    rebuild from the same commit replaced: the grok review runs and a composer review is refused (pins an answer of
    the checkpoint, whose last run is the composer's)."""
    ws = scratch_repo(tmp_path)
    c1 = head(ws)
    write_record(ws, row(GROK_B, start=c1, clean=True), row(COMPOSER, start=c1, clean=True))
    ran(review(tmp_path, ws, GROK_R))
    assert_family_refusal(refused(review(tmp_path, ws, COMPOSER)), COMPOSER, "cursor")


@pytest.mark.parametrize("case", ["no-record", "empty-record", "review-rows-only", "another-branch", "slot-not-free"])
def test_r1_a_branch_with_no_builder_row_refuses_nothing_on_this_ground(tmp_path, case):
    """R1: an empty set (no builder row of the branch: no record, an empty one, review rows alone, another branch's
    builder, a launch that never got the slot) refuses nothing on this ground, as on the checkpoint."""
    ws = scratch_repo(tmp_path)
    if case == "empty-record":
        write(ws, "run/launcher/runs.jsonl", b"")
    elif case == "review-rows-only":
        write_record(ws, review_row(GROK_R), review_row(GPT))
    elif case == "another-branch":
        write_record(ws, row(GROK_B, branch="task-9"))
    elif case == "slot-not-free":
        write_record(ws, row(GROK_B, slot="not free"))
    ran(review(tmp_path, ws, GROK_R))


def test_r1_r3_a_folder_in_no_repository_is_refused_on_none_of_these_grounds(tmp_path):
    """R1, R3: a launch folder that lies in no repository has the empty set, whatever its record holds (a grok row,
    a line that does not parse), so a grok review runs, as on the checkpoint."""
    plain = tmp_path / "p" / "plain"
    (plain / "run").mkdir(parents=True)
    if not lies_in_no_repository(plain):
        pytest.skip("the temporary folder lies inside a git repository on this computer")
    write_record(plain, row(GROK_B, branch=None), row(GROK_B), '{"id": "torn", "kind": "bui')
    ran(review(tmp_path, plain, GROK_R))


def test_r1_the_set_is_read_for_the_branch_of_the_workspace_folder(tmp_path):
    """R1: the branch is read in `workspace_of(argv, folder)`: a review given `--workspace` of a worktree on
    `task-2`, which a grok row built, is refused; the same review from the launch folder on `task-1` runs (pins an
    answer of the checkpoint)."""
    ws = scratch_repo(tmp_path)
    wt = tmp_path / "p" / "wt"
    git(ws, "worktree", "add", "-q", "-b", "task-2", str(wt))
    write_record(ws, row(GROK_B, branch="task-2"))
    assert_family_refusal(refused(review(tmp_path, ws, GROK_R, workspace=wt)), GROK_R, "xai")
    ran(review(tmp_path, ws, GROK_R))


# --- R2: an unknown set ----------------------------------------------------------------------------

@pytest.mark.parametrize("cause", ["report-without-row", "record-line-not-parsing"])
def test_r2_an_unknown_set_refuses_a_reviewer_of_a_roster_builders_family(tmp_path, cause):
    """R2, R5: where the set is unknown (a report file the branch adds without its builder row, or a line of the
    record that does not parse), a review by a model of the family of any builder the roster file names (every
    profile's `builder`) is refused, the refusal naming the cause and saying the roster is resolved again; a reviewer
    of no builder's family runs. The checkpoint refuses nothing there (red)."""
    if cause == "report-without-row":
        ws = unknown_by_report(tmp_path)
        needle = "TASK-002-r1-report.md"
    else:
        ws = scratch_repo(tmp_path)
        write_record(ws, review_row(), '{"id": "torn", "kind": "build')
        needle = "runs.jsonl"
    write(ws, "docs/ROSTER.json", roster_text([FULL, NATIVE]))
    for model, family in ((GROK_R, "xai"), (COMPOSER, "cursor")):
        text = refused(review(tmp_path, ws, model))
        assert_family_refusal(text, model, family)
        assert needle in text, "the cause named: " + text
        assert says_resolve_again(text), text
    ran(review(tmp_path, ws, GPT))


def test_r2_an_unknown_set_reads_a_v1_rosters_top_level_builder(tmp_path):
    """R2: a v1 roster (no profiles, a top-level `builder`) names its builder's family: on an unknown set a review of
    that family is refused; a reviewer of a family neither its builder nor its reviewer has runs (red on the
    checkpoint)."""
    ws = unknown_by_report(tmp_path)
    write(ws, "docs/ROSTER.json", json.dumps({"builder": GROK_B, "review_b": GPT, "review_a": REVIEW_A}) + "\n")
    text = refused(review(tmp_path, ws, GROK_R))
    assert_family_refusal(text, GROK_R, "xai")
    assert "TASK-002-r1-report.md" in text and says_resolve_again(text), text
    ran(review(tmp_path, ws, COMPOSER))


@pytest.mark.parametrize("cause", ["row-of-no-family", "report-without-row"])
def test_r2_an_unknown_set_refuses_a_reviewer_of_a_parsing_builder_rows_family(tmp_path, cause):
    """R2, R5: on an unknown set a review by a model of the family of a builder row of the branch that parses is
    refused although the roster file names no builder of that family (its one profile's builder is composer); the
    refusal names the cause and says to resolve again. With a later row whose model names no family the checkpoint's
    last run has no family and lets the review through (red)."""
    if cause == "row-of-no-family":
        ws = scratch_repo(tmp_path)
        write_record(ws, row(GROK_B), row(MYSTERY, rnd=2))
        needle = "runs.jsonl"
    else:
        ws = unknown_by_report(tmp_path)
        write_record(ws, row(GROK_B))
        needle = "TASK-002-r1-report.md"
    write(ws, "docs/ROSTER.json", roster_text([{"name": "native", "builder": COMPOSER, "review_b": GPT}]))
    text = refused(review(tmp_path, ws, GROK_R))
    assert_family_refusal(text, GROK_R, "xai")
    assert needle in text and says_resolve_again(text), text
    if cause == "report-without-row":
        ran(review(tmp_path, ws, GPT))


@pytest.mark.parametrize("roster", ["absent", "malformed"])
def test_r2_the_resolved_builder_stands_in_where_the_roster_file_cannot_be_read(tmp_path, roster):
    """R2: where docs/ROSTER.json cannot be read (absent, not JSON), the resolved file's `builder` stands in for the
    roster file's builders: on an unknown set a review of its family is refused, naming the cause; a reviewer of no
    builder's family runs (the case tests/test_task032_supervisor_launcher.py's report review pins). Red on the
    checkpoint for the refusal."""
    ws = unknown_by_report(tmp_path)
    if roster == "malformed":
        write(ws, "docs/ROSTER.json", "{ this is not json\n")
    write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=GROK_B, review_b=GPT))
    text = refused(review(tmp_path, ws, GROK_R))
    assert_family_refusal(text, GROK_R, "xai")
    assert "TASK-002-r1-report.md" in text and says_resolve_again(text), text
    ran(review(tmp_path, ws, GPT))


@pytest.mark.parametrize("roster", ["absent", "malformed"])
def test_r2_parsing_rows_count_where_the_roster_file_cannot_be_read(tmp_path, roster):
    """R2 (round 2, Review A B1, the security audit's blocking 2); M14 (a parsing row's family dropped where the
    roster file cannot be read): on an unknown set (a report without its row) with a grok builder row of the branch
    that parses, docs/ROSTER.json absent or not JSON and the resolved builder gpt (openai), a grok review is refused
    by the row's family, naming the cause; the resolved builder stands in for the roster file's builders only, so a
    composer review (cursor: neither the row's family nor the resolved builder's) runs. Red on round 1, where the
    resolved builder alone was refused."""
    ws = unknown_by_report(tmp_path)
    write_record(ws, row(GROK_B))
    if roster == "malformed":
        write(ws, "docs/ROSTER.json", "{ this is not json\n")
    write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=GPT, review_b=COMPOSER))
    text = refused(review(tmp_path, ws, GROK_R))
    assert_family_refusal(text, GROK_R, "xai")
    assert "TASK-002-r1-report.md" in text and says_resolve_again(text), text
    ran(review(tmp_path, ws, COMPOSER))


def test_r2_the_refusal_names_each_unknown_cause(tmp_path):
    """R2, R5 (round 2, Review A S3); M17 (only the first cause named): where the set is unknown for two causes, a
    report file the branch adds without its row and a record line that does not parse, the family refusal names
    both (the report file's name and runs.jsonl). Red on round 1, which named the first cause alone."""
    ws = unknown_by_report(tmp_path)
    write_record(ws, row(GROK_B), '{"id": "torn", "kind": "build')
    write(ws, "docs/ROSTER.json", roster_text([{"name": "native", "builder": COMPOSER, "review_b": GPT}]))
    text = refused(review(tmp_path, ws, GROK_R))
    assert_family_refusal(text, GROK_R, "xai")
    assert "TASK-002-r1-report.md" in text and "runs.jsonl" in text, "each cause named: " + text


def test_r2_a_roster_file_naming_no_builder_family_lets_the_resolved_builder_stand_in(tmp_path):
    """R2 (round 2, the supervisor's ruling on the security audit's advisory: unknown is never read as nobody having
    built, DESIGN D-003); M19 (an empty refused set read as nobody having built): on an unknown set with no parsing
    builder row, a roster file that reads but names no builder of a known family stands as one that cannot be read
    for this rule: the resolved file's builder (grok) stands in, so a grok review is refused, naming the cause. Red on
    round 1, where the refused set came out empty and every review ran."""
    ws = unknown_by_report(tmp_path)
    write(ws, "docs/ROSTER.json", json.dumps({"other_pool": "available", "profiles": []}) + "\n")
    write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=GROK_B, review_b=GPT))
    text = refused(review(tmp_path, ws, GROK_R))
    assert_family_refusal(text, GROK_R, "xai")
    assert "TASK-002-r1-report.md" in text and says_resolve_again(text), text


@pytest.mark.parametrize("case", ["both-absent", "both-malformed", "resolved-without-builder"])
def test_r2_every_review_is_refused_where_neither_roster_can_be_read(tmp_path, case):
    """R2: on an unknown set where neither docs/ROSTER.json nor the resolved file's builder can be read, every
    review is refused, a reviewer of a family no one named among them, the refusal naming the cause and saying to
    resolve again (red on the checkpoint)."""
    ws = unknown_by_report(tmp_path)
    if case == "both-malformed":
        write(ws, "docs/ROSTER.json", "[not json\n")
        write(ws, "docs/ROSTER.resolved.json", "{not json either\n")
    elif case == "resolved-without-builder":
        write(ws, "docs/ROSTER.resolved.json", json.dumps({"profile": "native", "review_b": GPT}) + "\n")
    text = refused(review(tmp_path, ws, GPT))
    assert "TASK-002-r1-report.md" in text, "the cause named: " + text
    assert says_resolve_again(text), text


# --- R3: a set that cannot be read -------------------------------------------------------------------

def test_r3_a_detached_head_refuses_every_review(tmp_path):
    """R3; M10 (an unreadable set read as empty): inside a repository with the head detached the set cannot be
    read, so every review launch is refused, naming `detached` (red on the checkpoint, which reads no branch row)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GROK_B))
    git(ws, "checkout", "-q", "--detach")
    text = refused(review(tmp_path, ws, GPT))
    assert re.search(r"\bdetached\b", text.lower()), text


def test_r3_a_record_that_cannot_be_opened_refuses_every_review(tmp_path):
    """R3; M10: a record that exists and cannot be opened (a folder named run/launcher/runs.jsonl) makes the set
    unreadable: every review launch is refused, naming `runs.jsonl` (red on the checkpoint, which launches)."""
    ws = scratch_repo(tmp_path)
    record(ws).mkdir(parents=True)
    text = refused(review(tmp_path, ws, GPT))
    assert "runs.jsonl" in text, text


@pytest.mark.parametrize("where", ["committed", "untracked"])
def test_r3_a_report_file_without_a_base_refuses_every_review(tmp_path, where):
    """R3; M10: a tree that holds a report file (committed, or still in the working tree) in a repository with
    neither `origin/main` nor `main` cannot find the branch's base: every review launch is refused, naming `main`
    (red on the checkpoint)."""
    ws = scratch_repo(tmp_path, main=False)
    if where == "committed":
        commit(ws, "the brief's work", {"handoff/TASK-001-r1-report.md": "round 1\n"})
    else:
        write(ws, "handoff/TASK-001-r1-report.md", "round 1, not committed\n")
    text = refused(review(tmp_path, ws, GPT))
    assert re.search(r"\bmain\b", text), text


@pytest.mark.parametrize("how", ["fails", "does-not-start"])
def test_r3_git_that_does_not_answer_refuses_every_review(tmp_path, how):
    """R3, R10; M10: inside a repository (its `.git` entry found) a git that fails or does not start is a set that
    cannot be read, never an empty one: every review launch is refused, naming `git` (red on the checkpoint)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GROK_B))
    path = path_without_git(tmp_path, how)
    text = refused(review(tmp_path, ws, GPT, path=path))
    assert re.search(r"\bgit\b", text.lower()), text


# --- R4: the roster program cannot be loaded -----------------------------------------------------------

@pytest.mark.parametrize("breakage", ["raises", "lacks-built-families", "lacks-family-of", "missing"])
def test_r4_a_roster_program_that_cannot_be_loaded_refuses_the_review(tmp_path, breakage):
    """R4; M11 (the loader failure noted and the review launched): where roster-check.py beside the launcher raises
    as it loads, lacks `built_families` or `family_of`, or is missing (a copy of bridge/cursor-bridge under the
    temporary folder), a review launch is refused with exit 125, naming the cause and `bridge-check.py`, with no
    started line and no row (red on the checkpoint, which notes it and launches)."""
    prog = broken_copy(tmp_path, breakage)
    ws = scratch_repo(tmp_path)
    write_record(ws, review_row())
    text = refused(review(tmp_path, ws, GPT, prog=prog))
    assert "bridge-check.py" in text, text
    if breakage == "raises":
        assert "broken on purpose" in text or "RuntimeError" in text, "the cause named: " + text
    elif breakage == "lacks-built-families":
        assert "built_families" in text, "the cause named: " + text
    elif breakage == "lacks-family-of":
        assert "family_of" in text, "the cause named: " + text


def test_r4_a_roster_program_whose_built_set_raises_refuses_every_review(tmp_path):
    """R4 (round 2, Review A B3, the security audit's blocking 2, path B); M16 (an exception of built_families read as
    an unknown set): where the roster program loads but its `built_families` raises, the roster program cannot answer:
    every review is refused with exit 125, naming the exception and `bridge-check.py`, a reviewer of a family no one
    named among them. Red on round 1, which made up an unknown set and let the review through."""
    prog = broken_copy(tmp_path, "built-families-raises")
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GROK_B))
    write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=COMPOSER, review_b=GPT))
    text = refused(review(tmp_path, ws, GPT, prog=prog))
    assert "bridge-check.py" in text, text
    assert "broken on purpose" in text or "RuntimeError" in text, "the exception named: " + text


@pytest.mark.parametrize("profiles", ["a-number-and-null", "a-model-not-a-string"])
def test_r4_a_roster_file_of_the_wrong_shape_never_opens_a_review_of_the_building_family(tmp_path, profiles):
    """R2, R4 (round 2, Review A B3, the security audit's blocking 2, path B): a roster file whose profiles hold a
    non-object, or a profile whose builder model is not a string, beside a grok builder row of the branch: the grok
    review is refused (by the family refusal on the row, or by the roster program that cannot answer), never run.
    Red on round 1, where the exception became an unknown set with no rows and composer stood in."""
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GROK_B))
    if profiles == "a-number-and-null":
        write(ws, "docs/ROSTER.json", json.dumps({"profiles": [5, None]}) + "\n")
    else:
        write(ws, "docs/ROSTER.json", json.dumps({"profiles": [{"name": "x", "builder": {"model": 5},
                                                                "review_b": GPT}]}) + "\n")
    write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=COMPOSER, review_b=GPT))
    text = refused(review(tmp_path, ws, GROK_R))
    assert GROK_R in text, text


def test_r4_a_builder_launch_does_not_need_the_roster_program(tmp_path):
    """R4: a builder launch never loads the roster program for the review refusals, so it runs where the program
    cannot be loaded (pins an answer of the checkpoint)."""
    prog = broken_copy(tmp_path, "raises")
    ws = scratch_repo(tmp_path, files={"handoff/TASK-001.md": brief_text()})
    assert ran(build(tmp_path, ws, prog=prog))["kind"] == "builder"


# --- R5: the refusal's words --------------------------------------------------------------------------

def test_r5_a_family_refusal_naming_a_model_beyond_ascii_is_ascii(tmp_path):
    """R5: every refusal text is ASCII, the family refusal's too: a review model holding an e-acute, of the xai
    family that built the branch, is refused with the letter backslash-escaped (red on the checkpoint, which prints
    the family refusal unescaped)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GROK_B))
    text = refused(review(tmp_path, ws, "grok-4.7-h" + chr(0xE9)))
    assert "is of the xai family" in text and "rebuild" in text, text
    assert "\\xe9" in text, text


HOSTILE = {
    "record-bytes-not-utf8": lambda ws: write_record(ws, b"\xff\xfe junk \x80", row(GROK_B)),
    "record-deeply-nested": lambda ws: write_record(ws, "[" * 50000, row(GROK_B)),
    "roster-profiles-a-string": lambda ws: write(ws, "docs/ROSTER.json", json.dumps({"profiles": "native"})),
    "roster-profile-not-an-object": lambda ws: write(ws, "docs/ROSTER.json", json.dumps({"profiles": [5, None]})),
    "roster-a-list": lambda ws: write(ws, "docs/ROSTER.json", "[1, 2]\n"),
    "roster-builder-model-a-number": lambda ws: write(
        ws, "docs/ROSTER.json", json.dumps({"profiles": [{"name": "x", "builder": {"model": 5}, "review_b": GPT}]})),
    "resolved-builder-a-list": lambda ws: write(ws, "docs/ROSTER.resolved.json", json.dumps({"builder": ["x"]})),
    "resolved-deviation-mistyped": lambda ws: write(ws, "docs/ROSTER.resolved.json", resolved_text(
        builder=GPT, deviation={"review_b_alt": GPT, "branch": [BRANCH], "built": {"xai": 1}})),
}


@pytest.mark.parametrize("hostile", sorted(HOSTILE))
def test_r5_no_record_roster_or_resolved_file_prints_a_traceback(tmp_path, hostile):
    """R5 (ASVS L2: no exception escapes as a traceback on any record, roster file, resolved file or git answer):
    on an unknown set with a grok row of the branch, a record with bytes that are not UTF-8 or a line nested beyond
    the parser, a roster file of the wrong shape and a resolved file of the wrong types end in a run or a refusal,
    never a traceback."""
    ws = unknown_by_report(tmp_path)
    write_record(ws, row(GROK_B))
    HOSTILE[hostile](ws)
    res = review(tmp_path, ws, GPT)
    assert "Traceback" not in res.err, res.err
    assert res.rc in (0, 125), "rc %r, stderr:\n%s" % (res.rc, res.err)
    if res.rc == 125:
        refused(res)


# --- R6: the builder-model refusal and its one exception ---------------------------------------------------

def deviation(alt=COMPOSER, branch=BRANCH, built=("xai",), reason="family"):
    return {"review_b_alt": alt, "reason": reason, "branch": branch, "built": list(built)}


def test_r6_a_matching_deviation_lets_the_builder_model_review(tmp_path):
    """R6: a review on the resolved roster's builder model runs where the resolved file's `deviation` names that
    model as `review_b_alt` and the current branch as `branch`, the built set is known ({xai}, a grok row), the
    model's family (cursor) is not in it and the entry's `built` equals the set (red on the checkpoint, which
    refuses)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GROK_B))
    write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=COMPOSER, review_b=COMPOSER, deviation=deviation()))
    r = ran(review(tmp_path, ws, COMPOSER))
    assert r["kind"] == "review" and r["model"] == COMPOSER, r


def test_r6_an_empty_set_and_an_empty_built_let_the_builder_model_review(tmp_path):
    """R6; M8 (the supervisor's ruling, the design's table row 4): where the set is empty (no builder row of the
    branch, no record) and the resolved file's `deviation` names the builder model for this branch with `built` an
    empty list (the reason `unavailable`), the review on the builder model runs (red on the checkpoint, which
    refuses)."""
    ws = scratch_repo(tmp_path)
    write(ws, "docs/ROSTER.resolved.json", resolved_text(
        builder=COMPOSER, review_b=COMPOSER, deviation=deviation(built=(), reason="unavailable")))
    r = ran(review(tmp_path, ws, COMPOSER))
    assert r["kind"] == "review" and r["model"] == COMPOSER, r


def test_r6_an_empty_set_and_a_built_that_names_a_family_refuse_the_builder_model(tmp_path):
    """R6; M8 (the entry honoured where its `built` differs): where the set is empty (no builder row of the branch,
    no record) and the deviation names the builder model for this branch with `built` ["xai"], the review on the
    builder model is refused, the refusal saying to resolve the roster again (red on the checkpoint for the words)."""
    ws = scratch_repo(tmp_path)
    write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=COMPOSER, review_b=COMPOSER, deviation=deviation()))
    out = refused(review(tmp_path, ws, COMPOSER))
    assert COMPOSER in out, out
    assert says_resolve_again(out), "the refusal says to resolve the roster again: " + out


R6_REFUSED = {
    "no-entry": "the resolved file has no deviation",
    "another-branch": "M4: the entry names another branch",
    "branch-missing": "M4: the entry names no branch",
    "another-model": "M5: the entry names another model",
    "entry-bytes-not-utf8": "M6: the entry's branch holds bytes that are not UTF-8",
    "deviation-a-list": "M6: the entry is a list",
    "deviation-a-string": "M6: the entry is a string",
    "built-not-a-list": "M6: built is a string",
    "built-not-strings": "M6: built holds a number beside the family",
    "unknown-set": "M7: a line of the record does not parse",
    "unreadable-set": "M10: the record cannot be opened",
    "built-differs-by-more": "M8: built names a family the set lacks",
    "built-differs-empty": "M8: built is empty, the set is not",
    "set-holds-the-models-family": "the set holds cursor, the model's family",
}


@pytest.mark.parametrize("case", sorted(R6_REFUSED))
def test_r6_the_builder_model_is_refused_unless_the_entry_matches(tmp_path, case):
    """R6; M4 (another-branch, branch-missing), M5 (another-model), M6 (entry-bytes-not-utf8, deviation-a-list,
    deviation-a-string, built-not-a-list, built-not-strings), M7 (unknown-set), M8 (built-differs-by-more,
    built-differs-empty), M10 (unreadable-set): the builder model's review is refused, the refusal naming the model
    and saying to resolve the roster again, for no entry, another branch's or a branchless entry, another model's, an
    entry that cannot be read or is malformed (not an object, `built` not a list of strings), an unknown set, a set
    that cannot be read, a set that differs from `built`, and a set holding the model's family (R6_REFUSED names each
    case). The checkpoint refuses each, saying nothing of resolving again (red for the words)."""
    ws = scratch_repo(tmp_path)
    lines = [row(GROK_B)]
    dev = deviation()
    raw = None
    if case == "no-entry":
        dev = None
    elif case == "another-branch":
        dev = deviation(branch="task-9")
    elif case == "branch-missing":
        dev.pop("branch")
    elif case == "another-model":
        dev = deviation(alt=GPT)
    elif case == "entry-bytes-not-utf8":
        dev = deviation(branch="@@BRANCH@@")
    elif case == "deviation-a-list":
        dev = [COMPOSER, BRANCH, "xai"]
    elif case == "deviation-a-string":
        dev = COMPOSER
    elif case == "built-not-a-list":
        dev["built"] = "xai"
    elif case == "built-not-strings":
        dev["built"] = ["xai", 7]
    elif case == "unknown-set":
        lines.append('{"id": "torn", "kind": "bui')
    elif case == "built-differs-by-more":
        dev = deviation(built=("xai", "openai"))
    elif case == "built-differs-empty":
        dev = deviation(built=())
    elif case == "set-holds-the-models-family":
        lines.append(row(COMPOSER, rnd=2))
        dev = deviation(built=("cursor", "xai"))
    text = resolved_text(builder=COMPOSER, review_b=COMPOSER, deviation=dev)
    if case == "entry-bytes-not-utf8":
        raw = text.encode("ascii").replace(b"@@BRANCH@@", b"task-1\xff")
    write(ws, "docs/ROSTER.resolved.json", raw if raw is not None else text)
    if case == "unreadable-set":
        record(ws).mkdir(parents=True)
    else:
        write_record(ws, *lines)
    out = refused(review(tmp_path, ws, COMPOSER))
    assert COMPOSER in out, out
    assert says_resolve_again(out), "the refusal says to resolve the roster again: " + out
    if case == "no-entry":
        assert "review launch on the roster builder model" in out, out


def test_r6_an_unknown_set_never_opens_the_exception_where_the_family_refusal_would_not(tmp_path):
    """R6; M7 (the entry honoured where the set is unknown), found by the supervisor's mutation run (M7 survived:
    elsewhere the family refusal on an unknown set refuses the builder model too, the roster's builders holding its
    family): the set is unknown (a grok row and a torn line), the roster file names grok alone as a builder, the
    resolved builder is composer and the deviation names composer for this branch with `built` ["xai"]; the family
    refusal would let composer (cursor) through, so the builder-model refusal alone holds: the review is refused,
    saying to resolve the roster again (pins round 2's answer)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GROK_B), '{"id": "torn", "kind": "bui')
    write(ws, "docs/ROSTER.json", roster_text([FULL]))
    write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=COMPOSER, review_b=COMPOSER, deviation=deviation()))
    out = refused(review(tmp_path, ws, COMPOSER))
    assert COMPOSER in out and says_resolve_again(out), out


def test_r6_the_alternate_still_meets_the_family_refusal(tmp_path):
    """R6; M9 (the family refusal skipped for the alternate): the resolved file's deviation names gpt as the
    alternate for this branch with `built` equal to the set, and gpt's family built the branch: the alternate's
    review is refused by the family refusal, `is of the openai family` (pins an answer of the checkpoint, whose last
    run is gpt's)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GPT))
    write(ws, "docs/ROSTER.resolved.json",
          resolved_text(builder=COMPOSER, review_b=GPT, deviation=deviation(alt=GPT, built=("openai",))))
    assert_family_refusal(refused(review(tmp_path, ws, GPT)), GPT, "openai")


@pytest.mark.parametrize("model", [GPT, COMPOSER])
def test_r6_a_brief_named_in_a_review_launch_stays_refused(tmp_path, model):
    """R6; M15 (the brief-named refusal skipped for the alternate): the refusal of a brief named in a review launch
    stands as it is, beside a matching deviation, for another reviewer (gpt) and for the alternate the deviation lets
    through (composer, the builder model; round 2, Review A B2, the security audit's blocking 1: red on round 1, which
    returned before the brief check)."""
    ws = scratch_repo(tmp_path, files={"handoff/TASK-001.md": brief_text()})
    write_record(ws, row(GROK_B))
    write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=COMPOSER, review_b=COMPOSER, deviation=deviation()))
    out = refused(launch(tmp_path, ws, agent(model, "Read handoff/TASK-001.md"), "review"))
    assert "must not name a brief" in out, out


# --- R7: a row on a line of its own -------------------------------------------------------------------

def test_r7_a_row_after_a_torn_last_line_begins_a_new_line(tmp_path):
    """R7; M12 (the new line not begun after a torn last line): where the record's last byte is not a line feed, the
    launcher begins a new line first, so the torn line stays as it was and the new row is a line of its own that
    parses (red on the checkpoint, which appends the row to the torn line)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, review_row(), '{"id": "torn", "kind": "bui', tail=b"")
    before = record_bytes(ws)
    res = python_build(tmp_path, ws)
    assert res.rc == 0 and "Traceback" not in res.err, res.err
    after = record_bytes(ws)
    assert after.startswith(before), after
    rest = after[len(before):]
    assert rest[:1] == b"\n" or rest[:2] == b"\r\n", "no new line begun after the torn line: %r" % after
    lines = [l.rstrip(b"\r") for l in after.split(b"\n") if l.strip()]
    assert lines[-2] == b'{"id": "torn", "kind": "bui', lines
    assert json.loads(lines[-1].decode("utf-8"))["kind"] == "builder", lines


def test_r7_a_last_byte_of_a_carriage_return_is_a_torn_line(tmp_path):
    """R7 (round 2, Review A S4, the security audit's advisory); M18 (a carriage return taken for a line end): R7's
    test is the line feed: a record whose last byte is a carriage return (a torn CRLF) gets a line feed first, so the
    new row is a line of its own that parses. Red on round 1, which glued the row on after the carriage return."""
    ws = scratch_repo(tmp_path)
    write_record(ws, review_row(), review_row(), tail=b"\r")
    before = record_bytes(ws)
    res = python_build(tmp_path, ws)
    assert res.rc == 0 and "Traceback" not in res.err, res.err
    after = record_bytes(ws)
    assert after.startswith(before), after
    assert after[len(before):len(before) + 1] == b"\n", "no line feed begun after the carriage return: %r" % after
    last = after.split(b"\n")[-2] if after.endswith(b"\n") else after.split(b"\n")[-1]
    assert json.loads(last.decode("utf-8"))["kind"] == "builder", after


@pytest.mark.parametrize("case", ["ends-with-a-line-feed", "empty", "absent"])
def test_r7_a_record_that_ends_its_line_gets_no_blank_line(tmp_path, case):
    """R7: a record that ends with a line feed, an empty one and none at all get the row and its line feed and no
    blank line (pins an answer of the checkpoint)."""
    ws = scratch_repo(tmp_path)
    if case == "ends-with-a-line-feed":
        write_record(ws, review_row(), review_row())
    elif case == "empty":
        write(ws, "run/launcher/runs.jsonl", b"")
    before = record_bytes(ws) or b""
    res = python_build(tmp_path, ws)
    assert res.rc == 0 and "Traceback" not in res.err, res.err
    after = record_bytes(ws)
    assert after.startswith(before) and after.endswith(b"\n"), after
    assert not re.search(rb"(?:^|\n)\r?\n", after), "a blank line: %r" % after
    added = [l for l in after[len(before):].split(b"\n") if l.strip()]
    assert len(added) == 1 and json.loads(added[0].decode("utf-8"))["kind"] == "builder", after


# --- R8: start_commit and clean on every builder row ----------------------------------------------------

def assert_builder_keys(r, start, clean):
    assert r["kind"] == "builder", r
    assert "start_commit" in r and "clean" in r, "the row lacks TASK-086b's keys: %r" % r
    if start is None:
        assert r["start_commit"] is None, r
    else:
        assert isinstance(r["start_commit"], str) and COMMIT_RX.fullmatch(r["start_commit"]), r
        assert r["start_commit"] == start, r
    assert r["clean"] is clean, r
    assert set(r) <= OLD_KEYS | NEW_KEYS, "keys beyond the row's: %s" % sorted(set(r) - OLD_KEYS - NEW_KEYS)


def test_r8_a_builder_row_carries_the_commit_it_started_on_and_clean(tmp_path):
    """R8: a cursor-agent builder launch on a clean tree writes `start_commit`, the full object name `git rev-parse
    HEAD` prints, and `clean` true; `head` stays the program's name and the branch the brief's (red on the
    checkpoint, which writes neither key)."""
    ws = scratch_repo(tmp_path, files={"handoff/TASK-001.md": brief_text()})
    r = ran(build(tmp_path, ws))
    assert_builder_keys(r, head(ws), True)
    assert r["head"] == "cursor-agent" and r["branch"] == BRANCH and r["model"] == COMPOSER, r


CLEAN_CASES = {
    "clean": True,
    "unstaged-change": False,
    "staged-change": False,
    "deleted-file": False,
    "untracked-file": False,
    "ignored-file": True,
    "resolved-modified": True,
    "resolved-staged": True,
    "resolved-untracked": True,
    "resolved-and-another-change": False,
}


@pytest.mark.parametrize("case", sorted(CLEAN_CASES))
def test_r8_clean_reads_the_tree_and_the_index_apart_from_the_resolved_roster(tmp_path, case):
    """R8; M1 (a change outside the resolved roster ignored for `clean`: the unstaged, staged, deleted, untracked and
    resolved-and-another cases), M2 (the resolved roster's own change counted against it: the three resolved
    cases): `clean` is true exactly where the working tree and the index show no change outside
    docs/ROSTER.resolved.json; an uncommitted change to another tracked file, staged or not, and an untracked file
    that is not ignored make it false; a file under the ignored run/ does not (red on the checkpoint)."""
    files = {"handoff/TASK-001.md": brief_text(), "docs/ROSTER.json": roster_text()}
    if case != "resolved-untracked":
        files["docs/ROSTER.resolved.json"] = resolved_text()
    ws = scratch_repo(tmp_path, files=files)
    start = head(ws)
    if case in ("unstaged-change", "staged-change", "resolved-and-another-change"):
        write(ws, "README.md", "changed\n")
    if case == "staged-change":
        git(ws, "add", "README.md")
    if case == "deleted-file":
        (ws / "README.md").unlink()
    if case == "untracked-file":
        write(ws, "notes.txt", "an untracked file\n")
    if case == "ignored-file":
        write(ws, "run/notes.txt", "an ignored file\n")
    if case.startswith("resolved-"):
        write(ws, "docs/ROSTER.resolved.json", resolved_text(builder=GROK_B))
    if case == "resolved-staged":
        git(ws, "add", "docs/ROSTER.resolved.json")
    r = ran(build(tmp_path, ws))
    assert_builder_keys(r, start, CLEAN_CASES[case])


def test_r8_a_staged_rename_into_the_resolved_roster_is_not_clean(tmp_path):
    """R8 (round 2, Review A's should-fix, the security audit's advisory); M20 (a rename's source ignored): a staged
    rename of another tracked file onto docs/ROSTER.resolved.json removes that file from the tree, so `clean` is
    false; only the resolved roster's own change is set aside. Red on round 1, which read the rename's target
    alone."""
    files = {"handoff/TASK-001.md": brief_text(), "docs/ROSTER.json": roster_text(), "other.json": resolved_text()}
    ws = scratch_repo(tmp_path, files=files)
    start = head(ws)
    git(ws, "mv", "other.json", "docs/ROSTER.resolved.json")
    r = ran(build(tmp_path, ws))
    assert_builder_keys(r, start, False)


def test_r8_the_builders_own_changes_do_not_enter_clean(tmp_path):
    """R8: `start_commit` and `clean` are read before the child starts: a builder that leaves an untracked file
    behind still has `clean` true on its row (red on the checkpoint)."""
    ws = scratch_repo(tmp_path, files={"handoff/TASK-001.md": brief_text()})
    write_stand_in(tmp_path, touch="made-by-the-builder.txt")
    r = ran(build(tmp_path, ws))
    assert (ws / "made-by-the-builder.txt").exists(), "the stand-in did not run in the launch folder"
    assert_builder_keys(r, head(ws), True)


def worktree(ws, tmp_path):
    wt = tmp_path / "p" / "wt"
    git(ws, "worktree", "add", "-q", "-b", "task-2", str(wt))
    c = commit(wt, "the worktree's brief", {"handoff/TASK-002.md": brief_text("TASK-002")})
    return wt, c


@pytest.mark.parametrize("dirty", ["launch-folder", "worktree"])
def test_r8_a_worktree_builders_keys_are_read_in_its_workspace(tmp_path, dirty):
    """R8: a worktree builder (`--workspace` a worktree on `task-2`) has `start_commit` and `clean` read in the
    folder its branch is read in, never the launch folder: a change in the launch folder leaves `clean` true, an
    untracked file in the worktree makes it false, and `start_commit` is the worktree's head (red on the
    checkpoint)."""
    ws = scratch_repo(tmp_path)
    wt, c = worktree(ws, tmp_path)
    assert c != head(ws)
    if dirty == "launch-folder":
        write(ws, "README.md", "changed in the launch folder\n")
    else:
        write(wt, "notes.txt", "an untracked file in the worktree\n")
    r = ran(build(tmp_path, ws, brief="TASK-002", workspace=wt))
    assert r["branch"] == "task-2", r
    assert_builder_keys(r, c, dirty == "launch-folder")


def test_r8_the_row_of_a_launch_that_never_got_the_slot_carries_both_keys(tmp_path):
    """R8: the `slot not free` row (a builder launch that waited for a machine-wide slot another process holds, under
    the suite's temporary home, and ended at exit 123 with the command never started) is a builder row too and
    carries `start_commit` and `clean` (red on the checkpoint)."""
    ws = scratch_repo(tmp_path, files={"handoff/TASK-001.md": brief_text()})
    write_stand_in(tmp_path)
    script = tmp_path / "hold.py"
    script.write_text(HOLDER_SRC, encoding="utf-8")
    holding, release = tmp_path / "holding.txt", tmp_path / "release.txt"
    scale = {"BRIDGE_RUN_SLOT_SCALE": "0.0003"}
    holder = subprocess.Popen([sys.executable, str(script), PROG, str(holding), str(release)], cwd=str(tmp_path),
                              env=launch_env(tmp_path, allow_any=True, extra=scale), stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        deadline = time.time() + 60
        while not holding.exists() and holder.poll() is None and time.time() < deadline:
            time.sleep(0.1)
        assert holding.exists(), "the slot holder did not take the slot (exit %r)" % holder.poll()
        res = build(tmp_path, ws, allow_any=True, extra=scale)
    finally:
        release.write_text("go\n", encoding="utf-8")
        try:
            holder.wait(timeout=30)
        except subprocess.TimeoutExpired:
            holder.kill()
            holder.wait(timeout=30)
    assert "Traceback" not in res.err, res.err
    assert res.rc == 123, "rc %r, stderr:\n%s" % (res.rc, res.err)
    assert not res.marker.exists(), "the stand-in ran"
    r = new_row(res)
    assert r.get("slot") == "not free", r
    assert_builder_keys(r, head(ws), True)


def test_r8_a_builder_row_of_another_command_carries_both_keys(tmp_path):
    """R8: every row of kind builder carries the keys, one from a command that is not cursor-agent too (red on the
    checkpoint)."""
    ws = scratch_repo(tmp_path)
    r = ran(python_build(tmp_path, ws), stand_in=False)
    assert_builder_keys(r, head(ws), True)


def test_r8_a_builder_row_in_a_folder_in_no_repository_has_no_commit_and_is_not_clean(tmp_path):
    """R8: where the folder lies in no repository, `start_commit` is null and `clean` false, never true (red on the
    checkpoint)."""
    plain = tmp_path / "p" / "plain"
    (plain / "run").mkdir(parents=True)
    if not lies_in_no_repository(plain):
        pytest.skip("the temporary folder lies inside a git repository on this computer")
    r = ran(python_build(tmp_path, plain), stand_in=False)
    assert_builder_keys(r, None, False)


@pytest.mark.parametrize("how", ["fails", "does-not-start"])
def test_r8_r10_a_builder_row_where_git_does_not_answer(tmp_path, how):
    """R8, R10: where git fails or does not start, `start_commit` is null and `clean` false, never true, and the run
    goes on without a traceback (red on the checkpoint)."""
    ws = scratch_repo(tmp_path)
    path = path_without_git(tmp_path, how)
    r = ran(python_build(tmp_path, ws, path=path), stand_in=False)
    assert_builder_keys(r, None, False)


@pytest.mark.parametrize("kind", ["review", "test"])
def test_r8_rows_of_other_kinds_gain_neither_key(tmp_path, kind):
    """R8: rows of other kinds (a review, a test run) gain neither key (pins an answer of the checkpoint)."""
    ws = scratch_repo(tmp_path)
    if kind == "review":
        r = ran(review(tmp_path, ws, GPT))
    else:
        r = ran(launch(tmp_path, ws, [sys.executable, "-c", "pass"], "test", allow_any=True), stand_in=False)
    assert r["kind"] == kind, r
    assert "start_commit" not in r and "clean" not in r, r


# --- R9: step 3b's order -------------------------------------------------------------------------------

def test_r9_step_3b_a_rebuild_after_the_resolve_reads_no_rebuild(tmp_path):
    """R9; M2: step 3b's order through the launcher: a grok builder launch writes its row; the resolve (the native
    profile, its Review B grok) prints REBUILD; the branch is reset to the checkpoint; the resolve rewrites the
    tracked docs/ROSTER.resolved.json; the composer builder launch writes its own row, `clean` true although the
    resolved roster is changed; and the next resolve prints no REBUILD. Red on the checkpoint (no keys) and where
    `clean` is taken from git's status as it stands."""
    sentinel = '{"sentinel": "the resolved roster as the checkpoint holds it"}\n'
    ws = scratch_repo(tmp_path, files={"handoff/TASK-001.md": brief_text(),
                                       "docs/ROSTER.json": roster_text([FULL, NATIVE], other_pool="exhausted"),
                                       "docs/ROSTER.resolved.json": sentinel})
    write(ws, ".git/bridge/roster-state.json", json.dumps({
        "other_pool": "exhausted", "exhausted_at": "2026-11-25T08:00 UTC",
        "exhausted_reason": "owner said usage exhausted"}, indent=2) + "\n")
    c1 = head(ws)
    first = ran(build(tmp_path, ws, model=GROK_B))
    assert first["model"] == GROK_B, first
    commit(ws, "the grok builder's work", {"a.py": "x = 1\n"})
    rc, out = resolve(ws)
    assert rc == 0 and "RESOLVED profile 'native'" in out and "REBUILD" in out, "the precondition: " + out
    git(ws, "reset", "-q", "--hard", c1)
    rc, out = resolve(ws)
    assert rc == 0 and "REBUILD" in out, out
    assert (ws / "docs" / "ROSTER.resolved.json").read_text(encoding="utf-8") != sentinel, "the resolve rewrote it"
    assert "ROSTER.resolved.json" in git(ws, "status", "--porcelain"), "the precondition: the resolved roster changed"
    rebuilt = ran(build(tmp_path, ws, model=COMPOSER))
    assert_builder_keys(rebuilt, c1, True)
    commit(ws, "the rebuild's work", {"a.py": "x = 2\n"})
    rc, out = resolve(ws)
    assert rc == 0 and "RESOLVED profile 'native'" in out, out
    assert "REBUILD" not in out, "the rebuild ended the REBUILD: " + rebuild_text(out)


# --- R10: git calls -------------------------------------------------------------------------------------

def test_r10_untracked_names_beyond_ascii_are_read_without_raising(tmp_path):
    """R10: git's output is decoded without raising: untracked files named beyond ASCII and beyond the console's
    code page make `clean` false, with no traceback (red on the checkpoint)."""
    ws = scratch_repo(tmp_path, files={"handoff/TASK-001.md": brief_text()})
    write(ws, "caf" + chr(0xE9) + ".txt", "x\n")
    write(ws, chr(0x4E2D) + chr(0x6587) + ".txt", "x\n")
    r = ran(build(tmp_path, ws))
    assert_builder_keys(r, head(ws), False)


# --- R11: nothing else changes ----------------------------------------------------------------------------

@pytest.mark.parametrize("stub_exit", [0, 3])
def test_r11_an_accepted_review_keeps_its_started_line_and_exit(tmp_path, stub_exit):
    """R11: where nothing is refused, a review launch's first line is the started line, its last the exit line, and
    the launcher's exit is the reviewer's (pins an answer of the checkpoint)."""
    ws = scratch_repo(tmp_path)
    write_record(ws, row(GROK_B))
    r = ran(review(tmp_path, ws, GPT, stub_exit=stub_exit), rc=stub_exit)
    assert r["kind"] == "review" and r["exit"] == stub_exit, r


@pytest.mark.parametrize("stub_exit", [0, 1])
def test_r11_an_accepted_builder_launch_keeps_its_started_line_and_exit(tmp_path, stub_exit):
    """R11: a builder launch keeps its started line first, its exit line last and the builder's exit (pins an
    answer of the checkpoint)."""
    ws = scratch_repo(tmp_path, files={"handoff/TASK-001.md": brief_text()})
    r = ran(build(tmp_path, ws, stub_exit=stub_exit), rc=stub_exit)
    assert r["kind"] == "builder" and r["exit"] == stub_exit, r

# --- Round 3 (handoff/TASK-086b-r3.md): a branch name outside the code page ---------------------------------
# Review B, round 1: branch_of read `git rev-parse --abbrev-ref HEAD` in the system's code page; a name outside it
# raised in the two refusals, which call it outside any try, and the launch ended in a traceback (exit 1). On the
# checkpoint the family refusal called it inside its try. Each name below holds characters whose UTF-8 bytes include
# 0x81, 0x8D, 0x8F, 0x90 and 0x9D, which code page 1252 does not decode. Mutation label M21: the branch read in the
# code page (or not at all) where git prints UTF-8.

WIDE_BRANCH = "task-\u0101\u010d\u010f\u0110\u011d"


def wide_branch_repo(tmp_path, files=None):
    ws = scratch_repo(tmp_path, files=files)
    git(ws, "checkout", "-q", "-b", WIDE_BRANCH)
    return ws


def test_r3_a_branch_name_outside_the_code_page_is_read_and_judged(tmp_path):
    """R10 (handoff/TASK-086b-r3.md, Requirement 1; Review B, round 1, behaviour, path: git's output): on a branch
    whose name holds characters outside the system's code page, a review by the family of the branch's grok builder
    row is refused by name, with no traceback, and a review of another family runs and its row names the branch as
    git prints it. Mutation M21 (the branch read in the code page or not at all)."""
    ws = wide_branch_repo(tmp_path)
    write_record(ws, row(GROK_B, branch=WIDE_BRANCH))
    assert_family_refusal(refused(review(tmp_path, ws, GROK_R)), GROK_R, "xai")
    r = ran(review(tmp_path, ws, GPT))
    assert r["kind"] == "review" and r["branch"] == WIDE_BRANCH, r


def test_r3_a_deviation_on_such_a_branch_opens_the_builder_models_review(tmp_path):
    """R6 with R10 (handoff/TASK-086b-r3.md, Requirement 1): the builder-model exception reads the same branch: a
    deviation entry naming the branch, the builder model and the set read at the launch lets the builder model's
    review run on a branch whose name lies outside the code page, with no traceback. Mutation M21."""
    ws = wide_branch_repo(tmp_path)
    write_record(ws, row(GROK_B, branch=WIDE_BRANCH))
    write(ws, "docs/ROSTER.resolved.json",
          resolved_text(builder=COMPOSER, review_b=COMPOSER, deviation=deviation(branch=WIDE_BRANCH)))
    r = ran(review(tmp_path, ws, COMPOSER))
    assert r["kind"] == "review" and r["model"] == COMPOSER and r["branch"] == WIDE_BRANCH, r


def test_r3_a_builder_launch_on_such_a_branch_writes_its_name_and_both_keys(tmp_path):
    """R8 with R10 (handoff/TASK-086b-r3.md, Requirement 1): a builder launch on a branch whose name lies outside the
    code page runs with no traceback and writes the branch as git prints it, `start_commit` and `clean`. Mutation
    M21."""
    ws = wide_branch_repo(tmp_path, files={"handoff/TASK-001.md": brief_text()})
    r = ran(build(tmp_path, ws))
    assert r["branch"] == WIDE_BRANCH, r
    assert_builder_keys(r, head(ws), True)
