"""Hotfix 2026.10.25a: review-guard.py refuses an empty review input and keeps a copy of the
snapshot hash outside the checkout (2026-10-25 C4), premerge waits for GitHub's head (2026-10-18 C2);
scope-check.py knows three more records, the supervisor's `supervisor:` test commits and a --base
for a re-delegation (2026-10-25 C6); invisible-check.py flags the non-breaking and fixed-width spaces
and lists every non-ASCII character with --non-ascii (2026-10-25 C8). Each case failed on 18a.

KP-052: every non-ASCII character in this file is built with chr(), never typed."""
import hashlib
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")
GUARD = os.path.join(BRIDGE, "review-guard.py")
SCOPE = os.path.join(BRIDGE, "scope-check.py")
INVISIBLE = os.path.join(BRIDGE, "invisible-check.py")
def env():
    """Read at call time, after the conftest pointed HOME at a temporary folder (the hash copy lives under ~)."""
    return dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x",
                GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=env())
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def run(prog, repo, *args):
    p = subprocess.run([sys.executable, prog] + list(args), cwd=str(repo), capture_output=True, text=True, env=env(),
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


# ---------------------------------------------------------------- review-guard.py

@pytest.fixture
def repo(tmp_path):
    """A task branch whose review files are under run/review/ (ignored, the diff force-added)."""
    r = tmp_path / "ws"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / ".gitignore").write_text("run/\n", encoding="utf-8")
    (r / "a.py").write_text("x = 1\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    git(r, "checkout", "-q", "-b", "task-001")
    (r / "a.py").write_text("x = 2\n", encoding="utf-8")
    (r / "run" / "review").mkdir(parents=True)
    (r / "run" / "review" / "REVIEW-001.diff").write_bytes(b"diff\n")
    git(r, "add", "-f", "run/review/REVIEW-001.diff")
    git(r, "commit", "-q", "-am", "TASK-001")
    return r


def launched(repo, nnn="001"):
    import time
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() + 1))
    (repo / "run" / "review" / ("REVIEW-%s.err" % nnn)).write_text("bridge-run: started %sZ\nbridge-run: exit 0\n" % stamp, encoding="utf-8")


def test_snapshot_refuses_an_empty_review_input_and_prints_the_sizes(repo):
    """C4 (rows 23, 36; KP-067): an empty input under run/review/ named for the id is refused,
    nothing written; the launcher's own .err is not an input; no input at all is a NOTE."""
    (repo / "run" / "review" / "PLAN-001.md").write_bytes(b"")
    (repo / "run" / "review" / "REVIEW-001.err").write_bytes(b"")          # the launcher's file, not an input
    (repo / "run" / "review" / "PLAN-002.md").write_bytes(b"")             # another review's
    rc, out = run(GUARD, repo, "snapshot", "001")
    assert rc == 2 and "PLAN-001.md" in out and "empty" in out and "both reviewers" in out, out
    assert "REVIEW-001.diff  5 bytes" in out, out
    assert "PLAN-002" not in out and "REVIEW-001.err" not in out, out
    assert not (repo / ".git" / "bridge" / "review-001.json").exists(), "nothing is written on a refusal"
    (repo / "run" / "review" / "PLAN-001.md").write_bytes(b"sections\n")
    rc, out = run(GUARD, repo, "snapshot", "001")
    assert rc == 0 and "PLAN-001.md  9 bytes" in out, out
    rc, out = run(GUARD, repo, "snapshot", "003")
    assert rc == 0 and "NOTE no review input" in out, out


def hash_copy(repo, nnn="001"):
    """This repository's copy: the key is the hash of its git common dir, as review-guard.py names it."""
    folder = os.environ["BRIDGE_REVIEW_HASHES"]
    key = hashlib.sha256(os.path.normcase(os.path.abspath(str(repo / ".git"))).encode("utf-8")).hexdigest()[:16]
    path = os.path.join(folder, "%s-%s.sha256" % (key, nnn))
    assert os.path.isfile(path), (path, os.listdir(folder))
    return path


def test_the_snapshot_hash_has_a_copy_and_a_rewritten_snapshot_is_gate_integrity(repo):
    """C4 (row 70, FB-037): snapshot writes the hash outside the checkout the reviewer runs in;
    verify and premerge compare with it."""
    rc, out = run(GUARD, repo, "snapshot", "001")
    assert rc == 0, out
    snap = repo / ".git" / "bridge" / "review-001.json"
    copy = hash_copy(repo)
    assert os.path.commonpath([copy, str(repo)]) != str(repo), "the copy lies outside the checkout"
    with open(copy, encoding="utf-8") as f:
        assert f.read().strip() == hashlib.sha256(snap.read_bytes()).hexdigest()
    assert re.search(r"snapshot hash [0-9a-f]{16}", out), "the hash is still printed"
    launched(repo)
    snap.write_text(snap.read_text(encoding="utf-8").replace('"nnn"', '"nnn" ', 1), encoding="utf-8")
    rc, out = run(GUARD, repo, "verify", "001")
    assert rc == 1 and "GATE-INTEGRITY" in out and "rewritten after it was taken" in out, out
    assert not (repo / ".git" / "bridge" / "verified-001.json").exists()
    rc, out = run(GUARD, repo, "premerge", "001")
    assert rc == 1 and "rewritten after it was taken" in out, out


def test_a_snapshot_without_a_hash_copy_cannot_be_verified(repo):
    """C4: a deleted copy (or a snapshot taken before this release) fails closed: take the snapshot again."""
    rc, out = run(GUARD, repo, "snapshot", "001")
    assert rc == 0, out
    os.remove(hash_copy(repo))
    launched(repo)
    rc, out = run(GUARD, repo, "verify", "001")
    assert rc == 2 and "CANNOT VERIFY" in out and "take the snapshot again" in out, out
    assert not (repo / ".git" / "bridge" / "verified-001.json").exists()
    rc, out = run(GUARD, repo, "premerge", "001")
    assert rc == 2 and "take the snapshot again" in out, out


@pytest.fixture
def ready(repo, program, monkeypatch):
    """Reviewed, the review files removed and committed: premerge with a pull request number
    run in this process, gh replaced by pr_head and the guard's own time.sleep recorded: the guard
    gets a stand-in time whose sleep records and whose other names are the real module's, so a
    sleep elsewhere in the process (subprocess's wait on POSIX) is not recorded (ISS-016)."""
    for k in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"):
        monkeypatch.setenv(k, os.devnull)
    rc, out = run(GUARD, repo, "snapshot", "001")
    assert rc == 0, out
    launched(repo)
    rc, out = run(GUARD, repo, "verify", "001")
    assert rc == 0, out
    git(repo, "rm", "-q", "run/review/REVIEW-001.diff")
    git(repo, "commit", "-q", "-m", "remove review files")
    mod = program("review-guard")
    sleeps = []
    real_time = mod.time

    class GuardTime:
        sleep = staticmethod(sleeps.append)

        def __getattr__(self, name):
            return getattr(real_time, name)

    monkeypatch.setattr(mod, "time", GuardTime())
    head = git(repo, "rev-parse", "HEAD")

    def answers(*shas):
        seq = list(shas)
        monkeypatch.setattr(mod, "pr_head", lambda pr, root: (seq.pop(0) if len(seq) > 1 else seq[0], None))
    return mod, head, sleeps, answers


def test_premerge_reads_a_lagging_head_on_github_again_before_it_flags(ready, repo, capsys):
    """2026-10-18 C2 (reAngle FB-006): a head that differs right after a push is read again every
    15 seconds; it matches after 30, so premerge is OK and says how long it waited."""
    mod, head, sleeps, answers = ready
    answers("0" * 40, "0" * 40, head)
    rc = mod.cmd_premerge("001", str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 0 and "waited 30 seconds" in out and "now it matches" in out, out
    assert sleeps == [15, 15]


def test_premerge_flags_a_head_that_still_differs_after_ninety_seconds(ready, repo, capsys):
    mod, head, sleeps, answers = ready
    answers("0" * 40)
    rc = mod.cmd_premerge("001", str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 1 and "NOT READY" in out and "waited 90 seconds" in out and "still differs" in out, out
    assert sum(sleeps) == 90 and set(sleeps) == {15}


def test_premerge_does_not_wait_when_the_heads_match(ready, repo, capsys):
    mod, head, sleeps, answers = ready
    answers(head)
    rc = mod.cmd_premerge("001", str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 0 and "waited" not in out and sleeps == [], out


def test_the_fixture_records_the_guards_sleeps_and_no_others(ready):
    """ISS-016 (BUG-028): only review-guard's own time.sleep is recorded. A sleep elsewhere in the
    process is not the guard's: on POSIX, CPython's subprocess wait polls a child that has not exited
    yet through time.sleep with a first delay of 1 ms, which made the lagging-head test record
    [0.001, 15, 15] on Linux CI (PR #86). The guard's other uses of time stay the real module's."""
    import time
    mod, head, sleeps, answers = ready
    time.sleep(0)
    assert sleeps == []
    mod.time.sleep(15)
    assert sleeps == [15]
    assert mod.time.strftime is time.strftime and mod.time.gmtime is time.gmtime


# ---------------------------------------------------------------- scope-check.py

def drift_list(out):
    return [l.strip()[2:] for l in out.splitlines() if l.startswith("  - ")]


def builder_run(start, seconds=600):
    import json
    return json.dumps({"id": start, "kind": "builder", "head": "cursor-agent", "model": "composer-2.5", "seconds": seconds, "exit": 0}) + "\n"


@pytest.fixture
def ws(tmp_path):
    r = tmp_path / "proj"
    for d in ("src", "docs", "handoff", "tests"):
        (r / d).mkdir(parents=True)
    (r / "src" / "a.py").write_text("A = 1\n", encoding="utf-8")
    (r / "src" / "b.py").write_text("B = 1\n", encoding="utf-8")
    (r / "tests" / "test_a.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    (r / "project.json").write_text("{}\n", encoding="utf-8")
    (r / ".gitignore").write_text("run/\n", encoding="utf-8")
    (r / "run" / "launcher").mkdir(parents=True)
    (r / "run" / "launcher" / "runs.jsonl").write_text(builder_run("2000-01-01T00:00:00Z"), encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    return r


def commit_brief(repo, scope, name="TASK-001.md"):
    (repo / "handoff" / name).write_text("# TASK-001\n\n## Scope\n- %s\n\n## Constraints\n- none\n" % scope, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "checkpoint: " + name)
    return "handoff/" + name


def builder_change(repo, path="src/a.py"):
    (repo / path).write_text("changed\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "TASK-001 accept")


def test_design_critique_hardening_and_project_json_are_records(ws):
    """C6 (row 42, FB-009): a records-only commit holding the three is not drift."""
    b = commit_brief(ws, "src/a.py")
    builder_change(ws)
    (ws / "docs" / "DESIGN_CRITIQUE.md").write_text("critique\n", encoding="utf-8")
    (ws / "docs" / "HARDENING.md").write_text("hardening\n", encoding="utf-8")
    (ws / "docs" / "CHANGES.md").write_text("changes\n", encoding="utf-8")
    (ws / "project.json").write_text('{"phase": 4}\n', encoding="utf-8")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "records: TASK-001")
    rc, out = run(SCOPE, ws, b)
    assert rc == 0 and "SCOPE CLEAN" in out, out
    for p in ("docs/DESIGN_CRITIQUE.md", "docs/HARDENING.md", "project.json"):
        assert p in out.split("RECORDS (")[1].splitlines()[0], out


def test_a_supervisor_commit_of_records_and_tests_is_not_drift(ws):
    """C6 (row 42): `supervisor:` + records and test files only = the supervisor's (rule N4)."""
    b = commit_brief(ws, "src/a.py")
    builder_change(ws)
    (ws / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    (ws / "tests" / "test_new.py").write_text("def test_new():\n    pass\n", encoding="utf-8")
    (ws / "docs" / "CHANGES.md").write_text("changes\n", encoding="utf-8")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "supervisor: regression tests for TASK-001")
    rc, out = run(SCOPE, ws, b)
    assert rc == 0 and "SCOPE CLEAN" in out and "SUPERVISOR TESTS (2)" in out, out
    import time
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 60))
    (ws / "run" / "launcher" / "runs.jsonl").write_text(builder_run(now), encoding="utf-8")
    rc, out = run(SCOPE, ws, b)
    assert rc == 1 and "tests/test_new.py" in drift_list(out), "a test commit made while a builder ran may be the builder's (parallel variant): " + out
    (ws / "run" / "launcher" / "runs.jsonl").unlink()
    rc, out = run(SCOPE, ws, b)
    assert rc == 1, "no run log: the test exemption fails closed: " + out


def test_a_test_commit_without_the_marker_or_with_code_stays_drift(ws):
    b = commit_brief(ws, "src/a.py")
    builder_change(ws)
    (ws / "tests" / "test_a.py").write_text("def test_a():\n    assert 1\n", encoding="utf-8")
    git(ws, "commit", "-q", "-am", "regression tests")                      # no `supervisor:` subject
    rc, out = run(SCOPE, ws, b)
    assert rc == 1 and drift_list(out) == ["tests/test_a.py"], out
    (ws / "tests" / "test_new.py").write_text("x = 1\n", encoding="utf-8")
    (ws / "src" / "b.py").write_text("B = 2\n", encoding="utf-8")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "supervisor: tests and a code change")   # code in it: not the supervisor's
    rc, out = run(SCOPE, ws, b)
    assert rc == 1 and sorted(drift_list(out)) == ["src/b.py", "tests/test_a.py", "tests/test_new.py"], out


def test_base_measures_a_re_delegation_from_the_rounds_brief_commit(ws):
    """C6 (row 47, FB-014): round 2 rewrites the same brief; the supervisor's commits between
    rounds are outside the diff when --base names round 2's brief commit, given before or after
    the brief; a --base without a commit cannot be verified."""
    b = commit_brief(ws, "src/a.py")
    builder_change(ws)
    (ws / "tests" / "test_a.py").write_text("def test_a():\n    assert 2\n", encoding="utf-8")
    git(ws, "commit", "-q", "-am", "tests between rounds")
    commit_brief(ws, "src/a.py\n- src/b.py")                                # round 2, same file
    r2 = git(ws, "rev-parse", "HEAD")
    (ws / "src" / "b.py").write_text("B = 3\n", encoding="utf-8")
    rc, out = run(SCOPE, ws, b)
    assert rc == 1 and "tests/test_a.py" in drift_list(out), "from the first commit the round-1 tests show: " + out
    rc, out = run(SCOPE, ws, "--base", r2, b)
    assert rc == 0 and "SCOPE CLEAN" in out and "given with --base" in out, out
    rc, out = run(SCOPE, ws, b, "--base", r2)
    assert rc == 0 and "SCOPE CLEAN" in out, out
    rc, out = run(SCOPE, ws, b, "--base")
    assert rc == 2 and "--base needs a commit" in out, out
    rc, out = run(SCOPE, ws, b, "--base", "no-such-commit")
    assert rc == 2 and "names no commit" in out, out


# ---------------------------------------------------------------- invisible-check.py

SPACES = [0x00A0, 0x2007, 0x202F, 0x2000, 0x2005, 0x200A, 0x3000]


def changed_repo(tmp_path, text):
    r = tmp_path / "inv"
    r.mkdir()
    (r / "doc.md").write_text("plain\n", encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    (r / "doc.md").write_bytes(text.encode("utf-8"))
    return r


def test_no_break_and_fixed_width_spaces_are_flagged(tmp_path):
    """C8 (row 43, FB-010)."""
    r = changed_repo(tmp_path, "".join("a%sb\n" % chr(cp) for cp in SPACES))
    rc, out = run(INVISIBLE, r, "HEAD")
    assert rc == 1, out
    for n, cp in enumerate(SPACES, 1):
        assert "INVISIBLE: doc.md:%d:2 U+%04X" % (n, cp) in out, out
    assert "no-break space" in out and "ideographic space" in out and "figure space" in out, out


def test_non_ascii_lists_every_non_ascii_character_with_its_name(tmp_path):
    """C8 (row 62, FB-029): visible characters too, by path, line, column, code point and name."""
    r = changed_repo(tmp_path, "caf%s ok\nplain\nx %s y\n" % (chr(0x00E9), chr(0x2014)))
    rc, out = run(INVISIBLE, r, "HEAD", "--non-ascii")
    assert rc == 0, "visible characters do not change the exit code: " + out
    assert "NON-ASCII: doc.md:1:4 U+00E9 LATIN SMALL LETTER E WITH ACUTE" in out, out
    assert "NON-ASCII: doc.md:3:3 U+2014 EM DASH" in out, out
    assert "NON-ASCII: 2 character(s)" in out, out
    rc, out = run(INVISIBLE, r, "HEAD")
    assert "NON-ASCII" not in out, "listed only on request: " + out
    assert all(ord(c) < 128 for c in out), "the output is ASCII"
