"""Supervisor-side acceptance tests of TASK-032's launcher half (R-042); written by the supervisor; the builder reads and runs them, never edits them.

Every test runs `python bridge/cursor-bridge/bridge-run.py ...` as a subprocess, with its working folder a temporary
launch folder (its own run/, docs/ and handoff/) that is a temporary git repository where the case needs one. A
stand-in `cursor-agent` (a .cmd on Windows, a shell file elsewhere) is put first on PATH; it appends a line to a
marker file and exits with the code in STUB_EXIT. LOCALAPPDATA points at a temporary folder, so the launcher's
fallback location of the real cursor-agent is never found either.
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CB = os.path.abspath(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge"))
PROG = os.path.join(CB, "bridge-run.py")
GUARD = os.path.join(CB, "review-guard.py")
TIMEOUT = 120

REFUSED = "bridge-run: refused - "
CEILING = "bridge-run: refused - review ceiling: "
POINTER = 'workflow/phases/delegation-loop.md, "3. Delegate to Cursor"'
PROMPT_TAG = "PROMPT-TEXT-zq81"
BUILDER_MODEL = "composer-2.5"
REVIEW_MODEL = "gpt-5.5-high"
CLASSES = ("behaviour", "security", "data integrity", "safety mechanism", "failing test")
OLD_FIELDS = {"id", "kind", "head", "model", "branch", "limit", "seconds", "exit", "healthy", "boundary", "waited", "slot",
              "pid", "child_pid"}
NEW_FIELDS = {"brief", "round", "brief_sha256", "lift", "brief_name", "merge_ids", "lift_line"}
NAME_RX = re.compile(r"^(.*?)(?:-r([1-9][0-9]*))?$")
DASH = chr(0x2014)
E_ACUTE = chr(0xE9)


# ---------------------------------------------------------------- fixtures and helpers


def git_env():
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def git(folder, *args):
    p = subprocess.run(["git", "-C", str(folder)] + list(args), env=git_env(), capture_output=True, text=True,
                       timeout=TIMEOUT)
    assert p.returncode == 0, "fixture git %s failed: %s" % (" ".join(args), p.stderr)
    return p.stdout


def make_repo(folder, branch="task-001"):
    """A temporary repository: init on main, one commit, then a switch to `branch` (unless it is main)."""
    folder.mkdir(parents=True, exist_ok=True)
    git(folder, "init", "-q", "-b", "main")
    git(folder, "config", "user.name", "Supervisor Fixture")
    git(folder, "config", "user.email", "supervisor@example.invalid")
    git(folder, "config", "commit.gpgsign", "false")
    (folder / "README.md").write_text("fixture\n", encoding="ascii")
    git(folder, "add", "README.md")
    git(folder, "commit", "-q", "-m", "init")
    if branch and branch != "main":
        git(folder, "switch", "-q", "-c", branch)
    return folder


def main_commit(folder, subject, body=None):
    """A commit on main (the squash or merge subject that merges an ID), the checkout put back after."""
    here = git(folder, "rev-parse", "--abbrev-ref", "HEAD").strip()
    git(folder, "switch", "-q", "main")
    args = ["commit", "-q", "--allow-empty", "-m", subject]
    if body:
        args += ["-m", body]
    git(folder, *args)
    git(folder, "switch", "-q", here)


def commit_all(folder, message="fixture: briefs and plan"):
    gi = folder / ".gitignore"
    if not gi.exists():
        gi.write_text("run/\n", encoding="ascii")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "--allow-empty", "-m", message)


def write_stand_in(bin_dir, marker):
    bin_dir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        text = ('@echo off\r\necho ran>> "%s"\r\nif "%%STUB_EXIT%%"=="" exit /b 0\r\nexit /b %%STUB_EXIT%%\r\n' % marker)
        (bin_dir / "cursor-agent.cmd").write_text(text, encoding="ascii")
    else:
        text = '#!/bin/sh\necho ran >> "%s"\nexit "${STUB_EXIT:-0}"\n' % marker
        for name in ("cursor-agent", "cursor-agent.exe"):     # .exe is looked up before the bare name
            p = bin_dir / name
            p.write_text(text, encoding="ascii")
            p.chmod(0o755)


class Lab(object):
    """A temporary launch folder (tmp/p/<name>) with run/, handoff/ and docs/, and the stand-in."""

    def __init__(self, tmp_path, branch="task-001", name="launch", git_repo=True):
        self.tmp = tmp_path
        self.root = tmp_path / "p" / name
        (self.root / "run").mkdir(parents=True)
        (self.root / "handoff").mkdir()
        (self.root / "docs").mkdir()
        self.bin = tmp_path / "bin"
        self.marker = tmp_path / "stand-in-ran.txt"
        if not (self.bin / ("cursor-agent.cmd" if sys.platform == "win32" else "cursor-agent")).exists():
            write_stand_in(self.bin, self.marker)
        self.counter = 0
        if git_repo:
            make_repo(self.root, branch)

    @property
    def log(self):
        return self.root / "run" / "launcher" / "runs.jsonl"


class Result(object):
    def __init__(self, p, before, lab, log):
        self.rc = p.returncode
        self.raw = p.stderr
        self.err = p.stderr.decode("utf-8", "replace")
        self.out = p.stdout.decode("utf-8", "replace")
        self.before = before
        self.lab = lab
        self.logfile = log


def log_lines(path):
    if not path.exists():
        return []
    return [l for l in path.read_bytes().split(b"\n") if l.strip()]


def launch_env(lab, allow_any=False, stub_exit=0):
    """Built at call time from os.environ (the autouse fixture has set HOME and USERPROFILE by then)."""
    env = dict(os.environ)
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    env.pop("BRIDGE_RUN_SLOT_SCALE", None)
    if allow_any:
        env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    env["PATH"] = str(lab.bin) + os.pathsep + os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env["LOCALAPPDATA"] = str(lab.tmp / "localappdata")
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_CEILING_DIRECTORIES"] = str(lab.tmp)
    env["STUB_EXIT"] = str(stub_exit)
    return env


def launch(lab, cmd, kind=None, limit="300", allow_any=False, stub_exit=0):
    """One launcher run from the lab's launch folder; the marker is removed first, the log read before."""
    if lab.marker.exists():
        lab.marker.unlink()
    before = log_lines(lab.log)
    flags = ["--limit", limit] + (["--kind", kind] if kind else [])
    p = subprocess.run([sys.executable, PROG] + flags + ["--"] + list(cmd), cwd=str(lab.root),
                       env=launch_env(lab, allow_any, stub_exit), capture_output=True, timeout=TIMEOUT)
    return Result(p, before, lab, lab.log)


def agent(prompt, model=BUILDER_MODEL, workspace=None):
    cmd = ["cursor-agent"]
    if workspace is not None:
        cmd += ["--workspace", str(workspace)]
    return cmd + ["-p", "--force", "--model", model, prompt]


def build(name):
    return agent("Read handoff/%s.md and do the work %s" % (name, PROMPT_TAG))


def refusal_line(res, prefix):
    lines = [l for l in res.err.splitlines() if l.startswith(prefix)]
    assert lines, "no line beginning %r in stderr:\n%s" % (prefix, res.err)
    return lines[0]


def assert_refused(res, prefix=REFUSED):
    """A refusal: exit 125, the prefix, nothing started (no marker, no started line), no runs.jsonl line."""
    assert "Traceback" not in res.err, res.err
    assert res.rc == 125, "rc %r, stderr:\n%s" % (res.rc, res.err)
    line = refusal_line(res, prefix)
    assert "bridge-run: started" not in res.err, res.err
    assert not res.lab.marker.exists(), "the stand-in ran"
    assert log_lines(res.logfile) == res.before, "a runs.jsonl line was written"
    return line


def assert_ran(res, rc=0):
    """An accepted launch: the stand-in ran, exit rc, the started line, one new runs.jsonl line."""
    assert "Traceback" not in res.err, res.err
    assert res.rc == rc, "rc %r, stderr:\n%s" % (res.rc, res.err)
    assert "bridge-run: started" in res.err, res.err
    assert res.lab.marker.exists(), "the stand-in did not run"
    lines = log_lines(res.logfile)
    assert len(lines) == len(res.before) + 1 and lines[:len(res.before)] == res.before, lines
    assert PROMPT_TAG.encode("ascii") not in lines[-1], "the prompt is in the run log"
    return json.loads(lines[-1].decode("utf-8"))


def write_brief(folder, name, extra="", tag=""):
    text = "# %s\n\n## Objective\nFixture brief %s %s.\n\n## Scope\n- a.py\n%s" % (name, name, tag, extra)
    data = text.encode("ascii")
    (folder / "handoff").mkdir(exist_ok=True)
    (folder / "handoff" / (name + ".md")).write_bytes(data)
    return data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def split_name(name):
    m = NAME_RX.match(name)
    return m.group(1), int(m.group(2)) if m.group(2) else 1


def write_row(lab, brief_name, exit_code, brief_sha=None, branch="task-001", lift=None, lift_line=None,
              merge_ids=None, run_id=None, log=None):
    """A runs.jsonl line in exactly the shape bridge-run.py's write_log writes for a builder run
    (json.dumps(entry) + newline, appended, UTF-8)."""
    lab.counter += 1
    id_part, rnd = split_name(brief_name)
    entry = {"id": run_id or "2020-01-01T00:%02d:%02dZ" % (lab.counter // 60, lab.counter % 60), "kind": "builder",
             "head": "cursor-agent", "model": BUILDER_MODEL, "branch": branch, "limit": 7200, "seconds": 5,
             "exit": exit_code, "healthy": None, "brief": id_part, "round": rnd,
             "brief_sha256": brief_sha or sha(("earlier bytes of %s" % brief_name).encode("ascii")),
             "brief_name": brief_name, "lift": lift, "merge_ids": list(merge_ids or [id_part]),
             "waited": 0, "pid": 4242, "child_pid": 4343}
    if lift_line:
        entry["lift_line"] = lift_line
    path = log or lab.log
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def three_completed(lab, id_part="TASK-001", branch="task-001", log=None):
    for name in (id_part, id_part + "-r2", id_part + "-r3"):
        write_row(lab, name, 0, branch=branch, log=log)


def write_plan(lab, *ids, extra=""):
    lines = ["# Build plan\n\n"]
    for i in ids:
        lines.append("### %s %s the increment %s\n\nKind: feature\n\n" % (i, DASH, i))
    (lab.root / "docs" / "BUILD_PLAN.md").write_bytes(("".join(lines) + extra).encode("utf-8"))


def write_params(lab, text):
    (lab.root / "docs" / "RUN_PARAMETERS.md").write_bytes(text.encode("utf-8") if isinstance(text, str) else text)


def write_roster(lab):
    (lab.root / "docs" / "ROSTER.resolved.json").write_text(
        json.dumps({"profile": "native", "builder": BUILDER_MODEL, "review_a": "claude-opus", "review_b": REVIEW_MODEL,
                    "families": {}}), encoding="utf-8")


def check_row(row, brief_id, rnd, data, branch="task-001", lift=None, lift_line=None):
    assert row.get("brief") == brief_id, row
    assert isinstance(row.get("round"), int) and not isinstance(row.get("round"), bool) and row["round"] == rnd, row
    assert row.get("brief_sha256") == sha(data), row
    assert row.get("branch") == branch, row
    assert "lift" in row and row["lift"] == lift, row
    assert row.get("lift_line") == lift_line, row
    assert set(row) <= OLD_FIELDS | NEW_FIELDS, "fields beyond R21: %s" % sorted(set(row) - OLD_FIELDS - NEW_FIELDS)


def guard_snapshot(root, name):
    p = subprocess.run([sys.executable, GUARD, "snapshot", name], cwd=str(root), env=git_env(), capture_output=True,
                       text=True, timeout=TIMEOUT)
    return p.returncode, p.stdout + p.stderr


# ---------------------------------------------------------------- clause (e): names and the brief rule


@pytest.mark.parametrize("name", ["TASK-001", "TASK-010c", "CONFIG-B3b", "HOTFIX-001", "B3-CLOSE", "TASK-001-r2"])
def test_task032_launcher_accepted_name_forms(tmp_path, name):
    """R-042. The grammar's accepted names launch, and the run's line records brief, round, brief_sha256 (the brief's
    bytes), lift null and the branch, with no field beyond R21's and never the prompt.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): the accepted name forms, the runs.jsonl fields and the absence of the prompt"""
    lab = Lab(tmp_path)
    data = write_brief(lab.root, name)
    row = assert_ran(launch(lab, build(name)))
    id_part, rnd = split_name(name)
    check_row(row, id_part, rnd, data)


@pytest.mark.parametrize("bad,prompt_name,file_name", [
    ("TASK-001-r0", "TASK-001-r0", "TASK-001-r0"),
    ("TASK-001-r05", "TASK-001-r05", "TASK-001-r05"),
    ("TASK-001-R2", "TASK-001-R2", "TASK-001-R2"),
    ("TASK 001", "TASK 001", "TASK 001"),
    ("TASK-001-r2\n", "TASK-001-r2\n", "TASK-001-r2"),
])
def test_task032_launcher_refused_name_forms(tmp_path, program, bad, prompt_name, file_name):
    """R-042. A name the grammar cannot read is refused with 125 before anything starts, nothing logged, even with a
    file of that spelling present (the trailing-newline form names handoff/TASK-001-r2<newline>.md, the file
    TASK-001-r2.md exists). Beside it, bridge_env.parse_review_name refuses the name itself.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): the refused name forms (-r0, -r05, -R2, a space, a trailing newline)"""
    lab = Lab(tmp_path)
    write_brief(lab.root, file_name)
    assert_refused(launch(lab, agent("Read handoff/%s.md and do the work %s" % (prompt_name, PROMPT_TAG))))
    assert program("bridge_env").parse_review_name(bad) is None


def test_task032_launcher_no_brief_refused(tmp_path):
    """R-042. A cursor-agent builder launch naming no brief is refused (125), and the refusal names the brief rule's
    pointer (R20).
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a launch naming no brief refused"""
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001")
    line = assert_refused(launch(lab, agent("Build the parser %s" % PROMPT_TAG)))
    assert POINTER in line, line


def test_task032_launcher_two_briefs_refused(tmp_path):
    """R-042. A launch naming two briefs (both present) is refused (125), naming the brief rule's pointer (R20).
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a launch naming two briefs refused"""
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001")
    write_brief(lab.root, "TASK-001-r2")
    line = assert_refused(launch(lab, agent("Read handoff/TASK-001.md and handoff\\TASK-001-r2.md %s" % PROMPT_TAG)))
    assert POINTER in line, line


def test_task032_launcher_brief_read_from_workspace_folder(tmp_path):
    """R-042. A brief present only in the --workspace folder is read from there (its bytes and its branch are logged),
    and one present only in the launch folder is not read (refused).
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a brief read from the --workspace folder"""
    lab = Lab(tmp_path, branch="launch-side")
    wa = make_repo(tmp_path / "wsA", "task-001")
    data = write_brief(wa, "TASK-001")
    row = assert_ran(launch(lab, agent("Read handoff/TASK-001.md %s" % PROMPT_TAG, workspace=wa)))
    check_row(row, "TASK-001", 1, data, branch="task-001")
    wb = make_repo(tmp_path / "wsB", "task-002")
    write_brief(lab.root, "TASK-002")
    assert_refused(launch(lab, agent("Read handoff/TASK-002.md %s" % PROMPT_TAG, workspace=wb)))


@pytest.mark.parametrize("form", ["bare", "path"])
def test_task032_launcher_allow_any_refuses_agent_without_brief(tmp_path, form):
    """R-042. Under BRIDGE_RUN_ALLOW_ANY=1 a bare and a path-qualified cursor-agent naming no brief are refused (125) and
    the stand-in never runs: the switch never exempts a command whose head is cursor-agent.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): BRIDGE_RUN_ALLOW_ANY=1 refusing a cursor-agent head without a brief"""
    lab = Lab(tmp_path)
    head = "cursor-agent" if form == "bare" else str(lab.bin / ("cursor-agent.cmd" if sys.platform == "win32" else "cursor-agent"))
    cmd = [head, "-p", "--force", "--model", BUILDER_MODEL, "Build it %s" % PROMPT_TAG]
    assert_refused(launch(lab, cmd, allow_any=True))


# ---------------------------------------------------------------- clause (e): review launches


def test_task032_launcher_review_on_builder_model_refused(tmp_path):
    """R-042. A --kind review launch whose --model is docs/ROSTER.resolved.json's builder is refused (125), while the same
    launch on the reviewer's model runs (the control shows the stand-in is found).
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a --kind review launch on the roster's builder model refused"""
    lab = Lab(tmp_path)
    write_roster(lab)
    prompt = "Review run/review/REVIEW-TASK-001.diff %s" % PROMPT_TAG
    assert_refused(launch(lab, agent(prompt, model=BUILDER_MODEL), kind="review"))
    assert_ran(launch(lab, agent(prompt, model=REVIEW_MODEL), kind="review"))


@pytest.mark.parametrize("name", ["TASK-001", "TASK-001-r2"])
def test_task032_launcher_review_naming_brief_refused(tmp_path, name):
    """R-042. A --kind review launch naming a brief by the grammar is refused (125), nothing started.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a --kind review launch naming a brief refused"""
    lab = Lab(tmp_path)
    write_roster(lab)
    write_brief(lab.root, name)
    assert_refused(launch(lab, agent("Read handoff/%s.md %s" % (name, PROMPT_TAG), model=REVIEW_MODEL), kind="review"))


@pytest.mark.parametrize("path", ["handoff/RESOLUTION-x.md", "handoff/TASK-001-r2-report.md"])
def test_task032_launcher_review_naming_resolution_or_report_allowed(tmp_path, path):
    """R-042. A --kind review launch naming handoff/RESOLUTION-<id>.md or handoff/<ID>-r<N>-report.md is no brief and runs.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): one naming handoff/RESOLUTION-<id>.md or handoff/<ID>-r<N>-report.md allowed"""
    lab = Lab(tmp_path)
    write_roster(lab)
    (lab.root / path).write_text("# file\n", encoding="ascii")
    row = assert_ran(launch(lab, agent("Read %s %s" % (path, PROMPT_TAG), model=REVIEW_MODEL), kind="review"))
    assert row.get("kind") == "review", row


# ---------------------------------------------------------------- clause (e): the ceiling and its lifts


def test_task032_launcher_rounds_one_to_four(tmp_path):
    """R-042. Rounds 1, 2 and 3 run with no line; round 4 is refused without a class line (the message begins
    `bridge-run: refused - review ceiling: ` and names the brief, the ID, the branch, the round 4 and the ceiling 3) and
    runs with one, the lift recorded with the line's text.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): rounds 1 to 3 allowed with no line, round 4 refused without a class line and run with one, the message's names"""
    lab = Lab(tmp_path)
    for n, name in enumerate(("TASK-001", "TASK-001-r2", "TASK-001-r3"), 1):
        data = write_brief(lab.root, name)
        check_row(assert_ran(launch(lab, build(name))), "TASK-001", n, data)
    write_brief(lab.root, "TASK-001-r4")
    line = assert_refused(launch(lab, build("TASK-001-r4")), CEILING)
    assert "TASK-001-r4" in line and "task-001" in line, line
    rest = line.replace("TASK-001-r4", "").replace("task-001", "")
    assert "TASK-001" in rest, line
    assert re.search(r"(?<![\w-])4(?![\w-])", rest) and re.search(r"(?<![\w-])3(?![\w-])", rest), line
    cls = "Blocking class: behaviour - the parser drops the last record"
    data = write_brief(lab.root, "TASK-001-r4", "\n%s\n" % cls)
    check_row(assert_ran(launch(lab, build("TASK-001-r4"))), "TASK-001", 4, data, lift="class", lift_line=cls)


def test_task032_launcher_constants_and_the_ceiling_number(tmp_path, program):
    """R-042. bridge_env.REVIEW_ROUNDS is the owner's 3 and BLOCKING_CLASSES is exactly the five names; beside it the
    launcher holds that number: round 3 runs with no line, round 4 is refused.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): bridge_env.REVIEW_ROUNDS 3 with the five classes"""
    be = program("bridge_env")
    assert be.REVIEW_ROUNDS == 3
    assert set(be.BLOCKING_CLASSES) == set(CLASSES) and len(be.BLOCKING_CLASSES) == 5
    lab = Lab(tmp_path)
    write_row(lab, "TASK-001", 0)
    write_row(lab, "TASK-001-r2", 0)
    write_brief(lab.root, "TASK-001-r3")
    assert_ran(launch(lab, build("TASK-001-r3")))
    write_brief(lab.root, "TASK-001-r4")
    assert_refused(launch(lab, build("TASK-001-r4")), CEILING)


@pytest.mark.parametrize("cls", CLASSES)
def test_task032_launcher_each_class_lifts_round_four(tmp_path, cls):
    """R-042. Each of the five classes, written exactly, lifts round 4: it runs, lift "class", lift_line the line's text.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): each of the five classes accepted"""
    lab = Lab(tmp_path)
    three_completed(lab)
    line = "Blocking class: %s - the reader drops the last record" % cls
    data = write_brief(lab.root, "TASK-001-r4", "\n%s\n" % line)
    check_row(assert_ran(launch(lab, build("TASK-001-r4"))), "TASK-001", 4, data, lift="class", lift_line=line)


@pytest.mark.parametrize("bad", [
    "Blocking class: style - the reader drops the last record",
    "Blocking class: Behaviour - the reader drops the last record",
    "Blocking class: SECURITY - the reader drops the last record",
    "Blocking class: behaviour - ",
    "Blocking class: behaviour -",
])
def test_task032_launcher_bad_class_lines_refused(tmp_path, bad):
    """R-042. A sixth word, a capitalised class (R19: `Behaviour`, `SECURITY`) and an empty finding lift nothing: round 4
    is refused with the ceiling's message.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a sixth word or an empty finding refused (and handoff/TASK-032-r2.md R19, the class matched exactly in lower case)"""
    lab = Lab(tmp_path)
    three_completed(lab)
    write_brief(lab.root, "TASK-001-r4", "\n%s\n" % bad)
    assert_refused(launch(lab, build("TASK-001-r4")), CEILING)


def test_task032_launcher_first_well_formed_class_line_stands(tmp_path):
    """R-042. The class-line reader skips a malformed line (a capitalised class) and returns the first well-formed one:
    the run's lift_line is the second line's text.
    enforces: handoff/TASK-032-r2.md R19"""
    lab = Lab(tmp_path)
    three_completed(lab)
    good = "Blocking class: security - the token reaches the log"
    data = write_brief(lab.root, "TASK-001-r4", "\nBlocking class: Behaviour - wrong case\n%s\n" % good)
    check_row(assert_ran(launch(lab, build("TASK-001-r4"))), "TASK-001", 4, data, lift="class", lift_line=good)


def test_task032_launcher_owner_line_lifts_to_its_rounds(tmp_path):
    """R-042. The owner's line `Review rounds above the ceiling: TASK-001 5 (...)` allows rounds 4 and 5 (lift "owner",
    lift_line the line's text) and refuses round 6; a second line for the same ID (9 rounds) is ignored.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): the owner's line lifting to its <rounds> and a second line ignored"""
    lab = Lab(tmp_path)
    three_completed(lab)
    first = "Review rounds above the ceiling: TASK-001 5 (the owner allows two more rounds, 2026-10-28)"
    second = "Review rounds above the ceiling: TASK-001 9 (a later line, 2026-10-28)"
    write_params(lab, "# Run parameters\n\n%s\n%s\n" % (first, second))
    for n in (4, 5):
        data = write_brief(lab.root, "TASK-001-r%d" % n)
        check_row(assert_ran(launch(lab, build("TASK-001-r%d" % n))), "TASK-001", n, data, lift="owner", lift_line=first)
    write_brief(lab.root, "TASK-001-r6")
    assert_refused(launch(lab, build("TASK-001-r6")), CEILING)


def test_task032_launcher_owner_line_malformed_does_not_use_the_lift(tmp_path):
    """R-042. An owner's line whose <rounds> is not above 3, one with empty words and one whose number is too long for
    int are skipped without using up the ID's lift, and without a traceback; the next well-formed line stands and its
    own text is recorded.
    enforces: handoff/TASK-032-r2.md R9"""
    lab = Lab(tmp_path)
    three_completed(lab)
    good = "Review rounds above the ceiling: TASK-001 4 (the owner's words, 2026-10-28)"
    write_params(lab, "Review rounds above the ceiling: TASK-001 3 (not above, 2026-10-28)\n"
                      "Review rounds above the ceiling: TASK-001 6 ( )\n"
                      "Review rounds above the ceiling: TASK-001 %s (too long, 2026-10-28)\n%s\n" % ("9" * 5000, good))
    data = write_brief(lab.root, "TASK-001-r4")
    check_row(assert_ran(launch(lab, build("TASK-001-r4"))), "TASK-001", 4, data, lift="owner", lift_line=good)


def test_task032_launcher_ceiling_message_names_the_two_lifts(tmp_path):
    """R-042. The ceiling's refusal is ASCII and names the two lifts by their forms: `Blocking class: <class> - <finding>`
    in the brief and `Review rounds above the ceiling: <ID> <rounds> (<their words>, <date>)` in docs/RUN_PARAMETERS.md.
    enforces: handoff/TASK-032-r2.md R20"""
    lab = Lab(tmp_path)
    three_completed(lab)
    write_brief(lab.root, "TASK-001-r4")
    res = launch(lab, build("TASK-001-r4"))
    line = assert_refused(res, CEILING)
    res.raw.decode("ascii")
    assert "Blocking class: <class> - <finding>" in line, line
    assert re.search(r"Review rounds above the ceiling: (?:<ID>|TASK-001) <rounds> \(<their words>, <date>\)", line), line
    assert "docs/RUN_PARAMETERS.md" in line, line


def test_task032_launcher_refusal_text_is_ascii(tmp_path):
    """R-042. A refusal naming an unreadable brief name with a non-ASCII letter (e-acute) is written in ASCII, the letter
    backslash-escaped (`\\xe9`), as design_refusal does.
    enforces: handoff/TASK-032-r2.md R20"""
    lab = Lab(tmp_path)
    res = launch(lab, agent("Read handoff/TASK-001%s.md %s" % (E_ACUTE, PROMPT_TAG)))
    assert_refused(res)
    text = res.raw.decode("ascii")
    assert "\\xe9" in text, text


# ---------------------------------------------------------------- clause (e): revised in place and relaunches


def test_task032_launcher_revised_in_place_after_exit_zero_refused(tmp_path):
    """R-042. A brief name with a completed run (exit 0) relaunched with different bytes is refused (125): "revised in
    place: write handoff/TASK-001-r2.md".
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a revised brief refused after a run with exit 0"""
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001")
    assert_ran(launch(lab, build("TASK-001")))
    write_brief(lab.root, "TASK-001", tag="revised")
    line = assert_refused(launch(lab, build("TASK-001")))
    assert "revised in place" in line and "TASK-001-r2" in line, line


@pytest.mark.parametrize("code", [1, 124])
def test_task032_launcher_revised_after_failed_exit_relaunches(tmp_path, code):
    """R-042. After a run that ended with exit 1 or 124 the name stays open: the revised brief launches and runs.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): relaunched after any other exit (1, 124)"""
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001")
    row = assert_ran(launch(lab, build("TASK-001"), stub_exit=code), rc=code)
    assert row.get("exit") == code, row
    data = write_brief(lab.root, "TASK-001", tag="revised")
    check_row(assert_ran(launch(lab, build("TASK-001"))), "TASK-001", 1, data)


def test_task032_launcher_identical_relaunch_adds_no_round(tmp_path):
    """R-042. Identical bytes relaunch freely after exit 0 (logged round 1 each time) and add no round: after three runs
    of TASK-001 and one of TASK-001-r2, TASK-001-r3 runs with no line and TASK-001-r4 is refused.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): identical bytes relaunching and leaving the next numbered brief's round unchanged"""
    lab = Lab(tmp_path)
    data = write_brief(lab.root, "TASK-001")
    for _ in range(3):
        check_row(assert_ran(launch(lab, build("TASK-001"))), "TASK-001", 1, data)
    write_brief(lab.root, "TASK-001-r2")
    assert_ran(launch(lab, build("TASK-001-r2")))
    data = write_brief(lab.root, "TASK-001-r3")
    check_row(assert_ran(launch(lab, build("TASK-001-r3"))), "TASK-001", 3, data)
    write_brief(lab.root, "TASK-001-r4")
    assert_refused(launch(lab, build("TASK-001-r4")), CEILING)


# ---------------------------------------------------------------- clause (e): the branch rule and its lapse


MERGED_FORMS = [
    ("TASK-001: the first increment (#5)", None),
    ("Merge pull request #5 from x/task-001", None),
    ("Merge branch 'task-001'", None),
    ("feat(launcher): the first increment (TASK-001) (#5)", None),
    ("chore: the merge (#5)", "Merges: TASK-001"),
]


@pytest.mark.parametrize("subject,body", MERGED_FORMS)
def test_task032_launcher_other_id_refused_until_merged(tmp_path, subject, body):
    """R-042. On a branch TASK-001 claimed, a TASK-002 brief is refused (125) naming the counted ID, and allowed once a
    commit on main merges TASK-001 under the squash-subject reader (each of its forms).
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a brief under another ID on a counted branch refused without a lift and allowed once the counted ID is merged on main"""
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001")
    assert_ran(launch(lab, build("TASK-001")))
    data = write_brief(lab.root, "TASK-002")
    line = assert_refused(launch(lab, build("TASK-002")))
    assert "TASK-001" in line, line
    main_commit(lab.root, subject, body)
    check_row(assert_ran(launch(lab, build("TASK-002"))), "TASK-002", 1, data)


def test_task032_launcher_lapse_needs_every_counted_id(tmp_path):
    """R-042. The claim lapses only once a commit on main merges every counted ID: an unrelated squash subject and one
    merging half of the unit TASK-010 TASK-015 lapse nothing (TASK-020 refused), the second half's does.
    enforces: handoff/TASK-032-r2.md R5"""
    lab = Lab(tmp_path)
    write_plan(lab, "TASK-010", "TASK-015", "TASK-020")
    write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-015\n")
    assert_ran(launch(lab, build("TASK-010")))
    write_brief(lab.root, "TASK-020")
    main_commit(lab.root, "TASK-099: an unrelated increment (#3)")
    main_commit(lab.root, "TASK-010: half of the unit (#4)")
    line = assert_refused(launch(lab, build("TASK-020")))
    assert "TASK-010" in line and "TASK-015" in line, line
    main_commit(lab.root, "TASK-015: the other half (#6)")
    assert_ran(launch(lab, build("TASK-020")))


@pytest.mark.parametrize("claimed,lapses", [("CONFIG-B3b", True), ("CONFIG-B3", False)])
def test_task032_launcher_lapse_keeps_trailing_letter(tmp_path, claimed, lapses):
    """R-042. `Merge pull request #7 from x/config-b3b` merges CONFIG-B3b (case ignored, the trailing letter kept), so a
    CONFIG-B3b claim lapses and TASK-002 runs, while a CONFIG-B3 claim does not lapse and TASK-002 is refused.
    enforces: handoff/TASK-032-r2.md R5"""
    lab = Lab(tmp_path)
    write_brief(lab.root, claimed)
    assert_ran(launch(lab, build(claimed)))
    write_brief(lab.root, "TASK-002")
    main_commit(lab.root, "Merge pull request #7 from x/config-b3b")
    res = launch(lab, build("TASK-002"))
    if lapses:
        assert_ran(res)
    else:
        assert claimed in assert_refused(res)


def test_task032_launcher_claim_after_lapse_is_fresh(tmp_path):
    """R-042. Once the counted ID is merged, the earlier event is ignored and the next brief on the branch claims it
    afresh: TASK-002 runs, then TASK-003 is refused naming TASK-002.
    enforces: handoff/TASK-032-r2.md R3"""
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001")
    assert_ran(launch(lab, build("TASK-001")))
    main_commit(lab.root, "TASK-001: done (#5)")
    write_brief(lab.root, "TASK-002")
    assert_ran(launch(lab, build("TASK-002")))
    write_brief(lab.root, "TASK-003")
    assert "TASK-002" in assert_refused(launch(lab, build("TASK-003")))


def test_task032_launcher_branch_events_in_time_order(tmp_path):
    """R-042. The launcher's lines are read in time order (by run id), not file order: the earlier-timed TASK-001 line,
    written second, declares the branch, so TASK-002-r2 is refused naming TASK-001.
    enforces: handoff/TASK-032-r2.md R3"""
    lab = Lab(tmp_path)
    write_row(lab, "TASK-002", 0, run_id="2020-01-01T00:00:10Z")
    write_row(lab, "TASK-001", 0, run_id="2020-01-01T00:00:05Z")
    write_brief(lab.root, "TASK-002-r2")
    assert "TASK-001" in assert_refused(launch(lab, build("TASK-002-r2")))


def test_task032_launcher_plan_is_never_a_merged_id(tmp_path):
    """R-042. Under the grammar's pattern the subject form takes only tokens holding a hyphen and a digit: a commit on
    main `Plan the next stage` merges nothing, so a claim by the brief `Plan` does not lapse and TASK-002 is refused.
    enforces: handoff/TASK-032-r2.md R6"""
    lab = Lab(tmp_path)
    write_brief(lab.root, "Plan")
    assert_ran(launch(lab, build("Plan")))
    main_commit(lab.root, "Plan the next stage")
    write_brief(lab.root, "TASK-002")
    assert "Plan" in assert_refused(launch(lab, build("TASK-002")))


PARITY_SUBJECTS = [
    ("TASK-001: one (#1)", None),
    ("TASK-002 TASK-003: two (#2)", None),
    ("Merge pull request #4 from x/task-004b", None),
    ("Merge branch 'task-005'", None),
    ("feat(x): thing (TASK-006, R-027) - v0.2.0 (#7)", None),
    ("chore: a unit (#8)", "Merges: TASK-007, TASK-008"),
    ("TASK-011a: lettered (#11)", None),
    ("Merge pull request #12 from x/TASK-012", None),
    ("Merge pull request #14 from x/task-014-retry", None),
    ("Plan the next stage", None),
    ("Merge pull request #9 from x/feature-z", None),
    ("docs: nothing (#10)", None),
]


def test_task032_launcher_squash_reader_parity_with_plan_check(tmp_path, program, monkeypatch):
    """R-042. bridge_env.squash_merged_ids(folder, r"TASK-\\d{3,}[a-z]?") returns exactly what plan-check.py's
    merged_ids("main") returns on the same fixture repository; beside it, the launcher lapses a TASK-004b claim on the
    Merge form `Merge pull request #4 from x/task-004b` (tried before the subject form).
    enforces: handoff/TASK-032-r2.md R6"""
    lab = Lab(tmp_path)
    for subject, body in PARITY_SUBJECTS:
        main_commit(lab.root, subject, body)
    write_row(lab, "TASK-004b", 0)
    write_brief(lab.root, "TASK-050")
    assert_ran(launch(lab, build("TASK-050")))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.chdir(str(lab.root))
    expected = program("plan-check").merged_ids("main")
    assert expected and "TASK-004b" in expected       # precondition: the fixture reads under plan-check
    got = program("bridge_env").squash_merged_ids(str(lab.root), r"TASK-\d{3,}[a-z]?")
    assert set(got) == set(expected), (sorted(got), sorted(expected))


# ---------------------------------------------------------------- clause (e): merge units


def test_task032_launcher_merge_unit(tmp_path):
    """R-042. A two-ID merge unit's briefs (TASK-010, TASK-015) run; a third ID (TASK-020) is refused without the owner's
    line, refused under a class line, and runs under the owner's line naming it, the declared set unchanged: TASK-025 is
    then refused naming TASK-010 and TASK-015, and with the owner's line removed TASK-020-r2 is refused too.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a two-ID merge unit's briefs allowed and a third ID without the line refused (refused under a class line too, allowed under the owner's line naming it with the set unchanged)"""
    lab = Lab(tmp_path)
    write_plan(lab, "TASK-010", "TASK-015", "TASK-020", "TASK-025")
    unit = "\nMerge unit: TASK-010 TASK-015\n"
    write_brief(lab.root, "TASK-010", unit)
    row = assert_ran(launch(lab, build("TASK-010")))
    assert sorted(row.get("merge_ids") or []) == ["TASK-010", "TASK-015"], row
    write_brief(lab.root, "TASK-015", unit)
    assert_ran(launch(lab, build("TASK-015")))
    write_brief(lab.root, "TASK-020")
    line = assert_refused(launch(lab, build("TASK-020")))
    assert "TASK-010" in line and "TASK-015" in line, line
    write_brief(lab.root, "TASK-020", "\nBlocking class: behaviour - the unit needs it\n")
    assert_refused(launch(lab, build("TASK-020")))
    write_params(lab, "Review rounds above the ceiling: TASK-020 4 (the owner lets it join this branch, 2026-10-28)\n")
    assert_ran(launch(lab, build("TASK-020")))
    write_brief(lab.root, "TASK-025")
    line = assert_refused(launch(lab, build("TASK-025")))
    assert "TASK-010" in line and "TASK-015" in line, line
    write_params(lab, "# no owner's line now\n")
    write_brief(lab.root, "TASK-020-r2")
    assert_refused(launch(lab, build("TASK-020-r2")))


def test_task032_launcher_later_brief_naming_more_ids_refused(tmp_path):
    """R-042. After TASK-010 declared the unit TASK-010 TASK-015, a later brief whose unit line names TASK-020 too is
    refused (125).
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a later brief naming more IDs refused"""
    lab = Lab(tmp_path)
    write_plan(lab, "TASK-010", "TASK-015", "TASK-020")
    write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-015\n")
    assert_ran(launch(lab, build("TASK-010")))
    write_brief(lab.root, "TASK-010-r2", "\nMerge unit: TASK-010 TASK-015 TASK-020\n")
    assert_refused(launch(lab, build("TASK-010-r2")))


def test_task032_launcher_unit_id_not_a_heading_refused(tmp_path):
    """R-042. A merge unit naming an ID that is no increment heading of docs/BUILD_PLAN.md (TASK-016) is refused.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a unit naming an ID that is no increment heading refused"""
    lab = Lab(tmp_path)
    write_plan(lab, "TASK-010", "TASK-015")
    write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-016\n")
    assert_refused(launch(lab, build("TASK-010")))


def test_task032_launcher_notes_is_no_heading(tmp_path):
    """R-042. Headings are read as plan-check.py reads them (HEAD_RX, TASK-\\d{3,}[a-z]?): `### Notes` is no heading, so a
    unit naming `Notes` is refused.
    enforces: handoff/TASK-032-r2.md R2"""
    lab = Lab(tmp_path)
    write_plan(lab, "TASK-010", extra="### Notes\n\nfree text\n")
    write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 Notes\n")
    assert_refused(launch(lab, build("TASK-010")))


def test_task032_launcher_bug_brief_without_plan(tmp_path):
    """R-042. In a folder without docs/BUILD_PLAN.md a BUG brief with no unit line runs, while a brief whose Merge unit:
    line cannot be checked is refused.
    enforces: handoff/TASK-032-r2.md R2 (and docs/BUILD_PLAN.md TASK-032 clause (e), Missing item 2: a BUG brief with no unit line in a folder without BUILD_PLAN.md allowed)"""
    lab = Lab(tmp_path, branch="bug-019")
    data = write_brief(lab.root, "BUG-019")
    check_row(assert_ran(launch(lab, build("BUG-019"))), "BUG-019", 1, data, branch="bug-019")
    other = Lab(tmp_path, branch="task-010", name="launch2")
    write_brief(other.root, "TASK-010", "\nMerge unit: TASK-010 TASK-015\n")
    assert_refused(launch(other, build("TASK-010")))


@pytest.mark.parametrize("name", ["TASK-001", "BUG-019", "HOTFIX-002", "CONFIG-B3b", "REFAC-B3"])
def test_task032_launcher_brief_without_unit_needs_no_heading(tmp_path, name):
    """R-042. Only the IDs a Merge unit: line declares must be increment headings: a brief with no such line runs in a
    folder whose docs/BUILD_PLAN.md has no heading for its ID.
    enforces: handoff/TASK-032-r2.md R2"""
    lab = Lab(tmp_path)
    write_plan(lab, "TASK-002")
    data = write_brief(lab.root, name)
    check_row(assert_ran(launch(lab, build(name))), name, 1, data)


def test_task032_launcher_merge_unit_line_is_case_sensitive(tmp_path):
    """R-042. `merge unit:` in lower case is no unit line: the brief declares its own ID only, so TASK-015 is then
    refused on the branch.
    enforces: handoff/TASK-032-r2.md R19"""
    lab = Lab(tmp_path)
    write_plan(lab, "TASK-010", "TASK-015")
    write_brief(lab.root, "TASK-010", "\nmerge unit: TASK-010 TASK-015\n")
    row = assert_ran(launch(lab, build("TASK-010")))
    assert (row.get("merge_ids") or ["TASK-010"]) == ["TASK-010"], row
    write_brief(lab.root, "TASK-015")
    assert "TASK-010" in assert_refused(launch(lab, build("TASK-015")))


def test_task032_launcher_merge_unit_ids_are_bare(tmp_path):
    """R-042. Every ID on a Merge unit: line must read as a bare ID: a unit token carrying `-r<N>` (`TASK-015-r2`)
    refuses the brief, exit 125 with the brief rule's prefix, nothing started.
    enforces: handoff/TASK-032-r2.md R19"""
    lab = Lab(tmp_path)
    write_plan(lab, "TASK-010", "TASK-015")
    write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-015-r2\n")
    assert_refused(launch(lab, build("TASK-010")), "bridge-run: refused - brief rule: ")


# ---------------------------------------------------------------- clause (e): the guard's record and the round count


def _guard_ready(lab):
    commit_all(lab.root)


def test_task032_launcher_guard_snapshot_claims_branch(tmp_path):
    """R-042. A review-guard snapshot of TASK-005 (the guard's record) claims the branch: a launch of TASK-006 there is
    refused naming TASK-005, while TASK-005's own brief runs.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a snapshot of one ID (the guard's record) refusing a launch of another on that branch"""
    lab = Lab(tmp_path, branch="task-005")
    write_brief(lab.root, "TASK-005")
    write_brief(lab.root, "TASK-006")
    _guard_ready(lab)
    rc, out = guard_snapshot(lab.root, "TASK-005")
    assert rc == 0, "fixture: the guard's snapshot failed: %s" % out
    assert "TASK-005" in assert_refused(launch(lab, build("TASK-006")))
    assert_ran(launch(lab, build("TASK-005")))


def test_task032_launcher_guard_and_launcher_events_by_time(tmp_path):
    """R-042. Both records are one list of events ordered by time: a guard round of TASK-005 taken before a launcher line
    of TASK-006 on the same branch declares the branch, so TASK-006-r2 is refused naming TASK-005.
    enforces: handoff/TASK-032-r2.md R3"""
    lab = Lab(tmp_path, branch="task-005")
    write_brief(lab.root, "TASK-006-r2")
    _guard_ready(lab)
    rc, out = guard_snapshot(lab.root, "TASK-005")
    assert rc == 0, "fixture: the guard's snapshot failed: %s" % out
    rec = json.loads((lab.root / ".git" / "bridge" / "rounds-TASK-005.json").read_text(encoding="utf-8"))
    taken = datetime.datetime.strptime(rec["rounds"][0]["time"], "%Y-%m-%dT%H:%M:%SZ")
    later = (taken + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_row(lab, "TASK-006", 0, branch="task-005", run_id=later)
    assert "TASK-005" in assert_refused(launch(lab, build("TASK-006-r2")))


def test_task032_launcher_round_ignores_guard_rounds(tmp_path):
    """R-042. The launcher's round is read from its own log only: three guard rounds of TASK-001 on the branch do not
    make the launcher's first TASK-001 brief a fourth round (it runs, logged round 1).
    enforces: handoff/TASK-032-r2.md R7"""
    lab = Lab(tmp_path)
    data = write_brief(lab.root, "TASK-001")
    _guard_ready(lab)
    for name in ("TASK-001", "TASK-001-r2", "TASK-001-r3"):
        rc, out = guard_snapshot(lab.root, name)
        assert rc == 0, "fixture: the guard's snapshot %s failed: %s" % (name, out)
    check_row(assert_ran(launch(lab, build("TASK-001"))), "TASK-001", 1, data)


def test_task032_launcher_round_counts_distinct_completed_names(tmp_path):
    """R-042. The round is the larger of <N> and one plus the distinct completed names: with TASK-001, TASK-001-r3 and
    TASK-001-r4 completed (exit 0), TASK-001-r2 is round 4 and refused without a line.
    enforces: handoff/TASK-032-r2.md R7"""
    lab = Lab(tmp_path)
    for name in ("TASK-001", "TASK-001-r3", "TASK-001-r4"):
        write_row(lab, name, 0)
    write_brief(lab.root, "TASK-001-r2")
    assert_refused(launch(lab, build("TASK-001-r2")), CEILING)


def test_task032_launcher_round_counts_only_exit_zero_on_this_branch(tmp_path):
    """R-042. Only exit 0 completes a name, and only on this branch: with TASK-001 completed, TASK-001-r3 ended 1,
    TASK-001-r4 ended 124 and TASK-001-r5 completed on another branch, TASK-001-r2 is round 2 and runs.
    enforces: handoff/TASK-032-r2.md R7"""
    lab = Lab(tmp_path)
    write_row(lab, "TASK-001", 0)
    write_row(lab, "TASK-001-r3", 1)
    write_row(lab, "TASK-001-r4", 124)
    write_row(lab, "TASK-001-r5", 0, branch="elsewhere")
    data = write_brief(lab.root, "TASK-001-r2")
    check_row(assert_ran(launch(lab, build("TASK-001-r2"))), "TASK-001", 2, data)


@pytest.mark.parametrize("code", [0, 1])
def test_task032_launcher_class_line_repeat(tmp_path, code):
    """R-042. After TASK-001-r4 ran lifted by a class line (exit 0, or exit 1), a different brief TASK-001-r5 repeating that
    text is refused, and the identical-bytes relaunch of TASK-001-r4 runs whatever the earlier exit.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a repeated class-line text refused in a different brief and the identical-bytes relaunch of the lifted brief allowed (handoff/TASK-032-r2.md R8: after exit 0 and after exit 1)"""
    lab = Lab(tmp_path)
    three_completed(lab)
    cls = "Blocking class: data integrity - the record loses a round"
    data = write_brief(lab.root, "TASK-001-r4", "\n%s\n" % cls)
    row = assert_ran(launch(lab, build("TASK-001-r4"), stub_exit=code), rc=code)
    assert row.get("lift") == "class" and row.get("lift_line") == cls, row
    write_brief(lab.root, "TASK-001-r5", "\n%s\n" % cls)
    assert_refused(launch(lab, build("TASK-001-r5")))
    check_row(assert_ran(launch(lab, build("TASK-001-r4"))), "TASK-001", 4, data, lift="class", lift_line=cls)


def test_task032_launcher_class_line_repeat_same_name_new_bytes(tmp_path):
    """R-042. A class-line text already recorded by a run of the same name with different bytes is refused: TASK-001-r4
    ran with the line and ended 1, the revised TASK-001-r4 with the same line is refused.
    enforces: handoff/TASK-032-r2.md R8"""
    lab = Lab(tmp_path)
    three_completed(lab)
    cls = "Blocking class: failing test - the suite fails on Windows"
    write_brief(lab.root, "TASK-001-r4", "\n%s\n" % cls)
    assert_ran(launch(lab, build("TASK-001-r4"), stub_exit=1), rc=1)
    write_brief(lab.root, "TASK-001-r4", "\n%s\n" % cls, tag="revised")
    assert_refused(launch(lab, build("TASK-001-r4")))


def test_task032_launcher_class_line_recorded_by_failed_run_of_other_name(tmp_path):
    """R-042. A class-line text recorded for the ID by a different brief name is refused whatever that run's exit: a
    logged TASK-001-r4 run lifted by the line that ended 124 makes TASK-001-r5 with the same line refused.
    enforces: handoff/TASK-032-r2.md R8"""
    lab = Lab(tmp_path)
    three_completed(lab)
    cls = "Blocking class: safety mechanism - the guard skips the hash"
    write_row(lab, "TASK-001-r4", 124, lift="class", lift_line=cls)
    write_brief(lab.root, "TASK-001-r5", "\n%s\n" % cls)
    assert_refused(launch(lab, build("TASK-001-r5")))


# ---------------------------------------------------------------- clause (e): worktrees, main, the log folder


def test_task032_launcher_two_worktrees_each_round_one(tmp_path):
    """R-042. Two launches from one folder naming two worktrees on two branches are each counted as round 1, each line
    recording its worktree's branch and brief bytes.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): two launches from one folder naming two worktrees on two branches each counted as round 1"""
    lab = Lab(tmp_path, branch="main")
    wa, wb = tmp_path / "wt" / "a", tmp_path / "wt" / "b"
    git(lab.root, "worktree", "add", "-q", "-b", "task-001", str(wa))
    git(lab.root, "worktree", "add", "-q", "-b", "task-002", str(wb))
    da = write_brief(wa, "TASK-001")
    db = write_brief(wb, "TASK-002")
    ra = assert_ran(launch(lab, agent("Read handoff/TASK-001.md %s" % PROMPT_TAG, workspace=wa)))
    check_row(ra, "TASK-001", 1, da, branch="task-001")
    rb = assert_ran(launch(lab, agent("Read handoff/TASK-002.md %s" % PROMPT_TAG, workspace=wb)))
    check_row(rb, "TASK-002", 1, db, branch="task-002")


@pytest.mark.parametrize("where", ["main", "a detached HEAD", "a folder outside git"])
def test_task032_launcher_builder_refused_off_branch(tmp_path, where):
    """R-042. A builder launch from main, from a detached HEAD or from a folder outside git is refused naming the rule:
    `bridge-run: refused - brief rule: builds run on a branch, not <main|a detached HEAD|a folder outside git>`.
    enforces: handoff/TASK-032-r2.md R15 (and docs/BUILD_PLAN.md TASK-032 clause (e): a builder launch from a checkout on main refused)"""
    if where == "a folder outside git":
        lab = Lab(tmp_path, git_repo=False)
    else:
        lab = Lab(tmp_path, branch="main" if where == "main" else "task-001")
        if where == "a detached HEAD":
            git(lab.root, "checkout", "-q", "--detach")
    write_brief(lab.root, "TASK-001")
    assert_refused(launch(lab, build("TASK-001")), "bridge-run: refused - brief rule: builds run on a branch, not %s" % where)


@pytest.mark.parametrize("kind", ["test", "driver"])
def test_task032_launcher_test_and_driver_start_on_main(tmp_path, kind):
    """R-042. A --kind test and a --kind driver launch start on main as anywhere: exit 0 and the started line, the run
    logged.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a --kind test and a --kind driver launch there start (handoff/TASK-032-r2.md R15)"""
    lab = Lab(tmp_path, branch="main")
    if kind == "test":
        (lab.root / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="ascii")
        cmd = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_ok.py"]
    else:
        (lab.root / "run" / "supervisor").mkdir(parents=True)
        (lab.root / "run" / "supervisor" / "ok.py").write_text("print('ok')\n", encoding="ascii")
        cmd = ["python", "run/supervisor/ok.py"]
    res = launch(lab, cmd, kind=kind)
    assert "Traceback" not in res.err, res.err
    assert res.rc == 0 and "bridge-run: started" in res.err, (res.rc, res.err, res.out)
    rows = [json.loads(l.decode("utf-8")) for l in log_lines(lab.log)]
    assert rows and rows[-1].get("kind") == kind and rows[-1].get("exit") == 0 and rows[-1].get("branch") == "main", rows


def test_task032_launcher_reads_its_own_launch_folder_log(tmp_path):
    """R-042. The launcher reads run/launcher/runs.jsonl from its launch folder, never from the --workspace folder: rounds
    logged only in the workspace's own run/ do not count (TASK-001-r2 runs, logged in the launch folder), and rounds
    logged in the launch folder do (TASK-001-r2 is then round 4 and refused).
    enforces: handoff/TASK-032-r2.md R1"""
    lab = Lab(tmp_path, branch="launch-side")
    wa = make_repo(tmp_path / "wsA", "task-001")
    ws_log = wa / "run" / "launcher" / "runs.jsonl"
    for name in ("TASK-001", "TASK-001-r3", "TASK-001-r4"):
        write_row(lab, name, 0, log=ws_log)
    ws_before = ws_log.read_bytes()
    data = write_brief(wa, "TASK-001-r2")
    row = assert_ran(launch(lab, agent("Read handoff/TASK-001-r2.md %s" % PROMPT_TAG, workspace=wa)))
    check_row(row, "TASK-001", 2, data, branch="task-001")
    assert ws_log.read_bytes() == ws_before
    lab2 = Lab(tmp_path, branch="launch-side", name="launch2")
    wb = make_repo(tmp_path / "wsB", "task-001")
    for name in ("TASK-001", "TASK-001-r3", "TASK-001-r4"):
        write_row(lab2, name, 0)
    write_brief(wb, "TASK-001-r2")
    assert_refused(launch(lab2, agent("Read handoff/TASK-001-r2.md %s" % PROMPT_TAG, workspace=wb)), CEILING)


# ---------------------------------------------------------------- R17: malformed input never crashes


def test_task032_launcher_non_utf8_run_parameters(tmp_path):
    """R-042. A non-UTF-8 byte in docs/RUN_PARAMETERS.md never crashes the launcher: the file is decoded with
    replacement, the owner's line on it still lifts round 4, and the run ends 0 with no traceback.
    enforces: handoff/TASK-032-r2.md R17"""
    lab = Lab(tmp_path)
    three_completed(lab)
    good = "Review rounds above the ceiling: TASK-001 4 (the owner's words, 2026-10-28)"
    write_params(lab, b"# Run parameters\n- a note: caf\xe9 \xff\n" + good.encode("ascii") + b"\n")
    data = write_brief(lab.root, "TASK-001-r4")
    check_row(assert_ran(launch(lab, build("TASK-001-r4"))), "TASK-001", 4, data, lift="owner", lift_line=good)


def test_task032_launcher_non_utf8_runs_jsonl_line(tmp_path):
    """R-042. A non-UTF-8 byte in a runs.jsonl line never crashes the launcher: the launch runs and logs its line.
    enforces: handoff/TASK-032-r2.md R17"""
    lab = Lab(tmp_path)
    lab.log.parent.mkdir(parents=True)
    lab.log.write_bytes(b'{"id": "2020-01-01T00:00:01Z", "kind": "test", "head": "caf\xe9", "exit": 0}\n')
    data = write_brief(lab.root, "TASK-001")
    check_row(assert_ran(launch(lab, build("TASK-001"))), "TASK-001", 1, data)


@pytest.mark.parametrize("field,value", [
    ("branch", ["task-001"]),
    ("merge_ids", 5),
    ("round", [1]),
    ("round", "2"),
])
def test_task032_launcher_malformed_runs_jsonl_line_skipped(tmp_path, field, value):
    """R-042. A launcher line failing a type check (branch a list, merge_ids 5, round [1], round "2") is skipped, never a
    traceback: the malformed TASK-009 line on the branch claims nothing, so TASK-001 runs.
    enforces: handoff/TASK-032-r2.md R17"""
    lab = Lab(tmp_path)
    write_row(lab, "TASK-009", 0)
    rows = [json.loads(l.decode("utf-8")) for l in log_lines(lab.log)]
    rows[0][field] = value
    lab.log.write_text(json.dumps(rows[0]) + "\n", encoding="utf-8")
    data = write_brief(lab.root, "TASK-001")
    check_row(assert_ran(launch(lab, build("TASK-001"))), "TASK-001", 1, data)


def write_slot_not_free_row(lab, brief_name, data, lift=None, lift_line=None, branch="task-001"):
    """The row bridge-run.py writes when a heavy run ended waiting for the slot: the brief's fields as computed
    before the wait, then `waited`, `seconds` 0, exit 123 and `"slot": "not free"`; the command never started."""
    entry = write_row(lab, brief_name, 0, brief_sha=sha(data), branch=branch, lift=lift, lift_line=lift_line)
    lines = log_lines(lab.log)
    entry.update(exit=123, seconds=0, waited=7320, slot="not free")
    lab.log.write_bytes(b"".join(l + b"\n" for l in lines[:-1]) + (json.dumps(entry) + "\n").encode("utf-8"))
    return entry


def test_bug030_a_launch_that_never_got_the_slot_spends_no_class_line(tmp_path):
    """BUG-030 (stage B5's review, round 1; launcher C6 and tests-launcher S1, convergent): a lifted round-4 launch that
    ended at exit 123 with `"slot": "not free"` never ran, so it spends no class line: the brief revised after it
    (different bytes, the same line) runs lifted. The same revision after a lifted run that did start (exit 1) is
    refused, as R8 rules (test_task032_launcher_class_line_repeat_same_name_new_bytes).
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e), a round being a builder run of a brief; handoff/TASK-032-r2.md R8"""
    lab = Lab(tmp_path)
    three_completed(lab)
    cls = "Blocking class: behaviour - the reader drops the last record"
    data = write_brief(lab.root, "TASK-001-r4", "\n%s\n" % cls)
    write_slot_not_free_row(lab, "TASK-001-r4", data, lift="class", lift_line=cls)
    revised = write_brief(lab.root, "TASK-001-r4", "\n%s\n" % cls, tag="revised")
    check_row(assert_ran(launch(lab, build("TASK-001-r4"))), "TASK-001", 4, revised, lift="class", lift_line=cls)


def test_bug030_a_launch_that_never_got_the_slot_still_claims_its_branch(tmp_path):
    """BUG-030 (the supervisor's ruling on tests-launcher S1(b)): a launch that ended at exit 123 states the IDs its
    brief declares for its branch as a run that started would, so its claim stands: another ID's brief on that
    branch is refused after it. A claim is what the launch meant to build, which the relaunch builds.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e), the branch rule (one ID, or a `Merge unit:` line's)"""
    lab = Lab(tmp_path)
    data = write_brief(lab.root, "TASK-001")
    write_slot_not_free_row(lab, "TASK-001", data)
    write_brief(lab.root, "TASK-002")
    assert_refused(launch(lab, build("TASK-002")), prefix="bridge-run: refused - branch rule: ")


LOCK_HOLDER_SRC = r'''
import os, sys, time
import importlib.util
spec = importlib.util.spec_from_file_location("bridge_run", os.path.join(sys.argv[1], "bridge-run.py"))
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)
lock_path, _ = br.heavy_state_paths()
os.makedirs(os.path.dirname(lock_path), exist_ok=True)
fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
if not br._try_lock_byte(fd):
    sys.exit(2)
open(sys.argv[2], "w").write("held")
time.sleep(float(sys.argv[3]))
'''


def hold_the_slot(lab, env, hold=60):
    """A process holding heavy.lock (the slot) under the lab's home, with no holder record; returns it once it holds."""
    script = lab.tmp / "lock_holder.py"
    script.write_text(LOCK_HOLDER_SRC, encoding="utf-8")
    flag = lab.tmp / "lock_held.txt"
    proc = subprocess.Popen([sys.executable, str(script), CB, str(flag), str(hold)], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = datetime.datetime.now() + datetime.timedelta(seconds=15)
    while not flag.exists():
        assert datetime.datetime.now() < end, "the holder did not take the slot"
        try:
            proc.wait(timeout=0.05)
        except subprocess.TimeoutExpired:
            continue
        raise AssertionError("the holder ended before it took the slot (exit %r)" % proc.returncode)
    return proc


def end_process(proc):
    if proc is not None and proc.poll() is None:
        proc.kill()
        proc.wait(timeout=10)


@pytest.mark.parametrize("revise", [False, True])
def test_bug030_the_brief_is_checked_again_after_the_slot_wait(tmp_path, revise):
    """BUG-030 (stage B5's review, round 1; launcher S3 and tests-launcher C5, convergent): the brief rules are judged
    on the brief's bytes before the slot wait; a brief changed during the wait is refused when the slot is taken
    (125, a `bridge-run: refused - ` line, the command never run, no runs.jsonl line), so the run never builds
    bytes that were not checked and logged; the twin whose brief did not change runs it.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e) (the launch logs `brief_sha256`, a brief revised after a run
    refused); TASK-028's rule, docs/INVENTORY.md "Windowless launches enforced by the bridge": checked again just
    before the start"""
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001")
    env = launch_env(lab, allow_any=True)
    env["BRIDGE_RUN_SLOT_SCALE"] = "0.02"
    holder = launcher = None
    try:
        holder = hold_the_slot(lab, env)
        launcher = subprocess.Popen([sys.executable, PROG, "--limit", "300", "--"] + build("TASK-001"), cwd=str(lab.root),
                                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        first = launcher.stderr.readline()
        while first and not first.startswith("bridge-run: waiting"):
            assert not first.startswith("bridge-run: refused"), first
            first = launcher.stderr.readline()
        assert first.startswith("bridge-run: waiting"), "the launch did not wait for the slot"
        if revise:
            write_brief(lab.root, "TASK-001", tag="changed while it waited")
        end_process(holder)
        err = first + launcher.communicate(timeout=60)[1]
    finally:
        end_process(holder)
        end_process(launcher)
    if revise:
        assert launcher.returncode == 125, err
        assert [l for l in err.splitlines() if l.startswith(REFUSED)], err
        assert not lab.marker.exists(), "the stand-in ran: " + err
        assert log_lines(lab.log) == [], "a refused launch writes no runs.jsonl line"
    else:
        assert launcher.returncode == 0, err
        assert lab.marker.exists(), err


def test_bug030_a_ceiling_refusal_does_not_wait_for_the_slot(tmp_path):
    """BUG-030 (stage B5's review, round 1; tests-launcher S2): every brief, branch and ceiling refusal comes before the
    slot, so while another run holds heavy.lock a fourth round with no class line is refused at once (125, the
    ceiling's line, no waiting line), never after the slot's bound.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e); handoff/TASK-029.md (the slot is taken just before the command)"""
    lab = Lab(tmp_path)
    three_completed(lab)
    write_brief(lab.root, "TASK-001-r4")
    env = launch_env(lab, allow_any=True)
    env["BRIDGE_RUN_SLOT_SCALE"] = "1"
    holder = None
    try:
        holder = hold_the_slot(lab, env)
        start = datetime.datetime.now()
        p = subprocess.run([sys.executable, PROG, "--limit", "300", "--"] + build("TASK-001-r4"), cwd=str(lab.root),
                           env=env, capture_output=True, text=True, timeout=60)
        took = (datetime.datetime.now() - start).total_seconds()
    finally:
        end_process(holder)
    assert p.returncode == 125, p.stderr
    assert [l for l in p.stderr.splitlines() if l.startswith(CEILING)], p.stderr
    assert "bridge-run: waiting" not in p.stderr and took < 30, (took, p.stderr)
