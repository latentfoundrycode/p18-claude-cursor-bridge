"""The retrofit's enforcement of D-003, the Review B round of an increment (R-055, R-042); supervisor-authored.

enforces: docs/BUILD_PLAN.md TASK-044 Done when: one test per state of D-003 and one per transition the diagram lists as
unexercised, each naming the state or transition it drives. The flag's early and in-run voids are tests/test_bug039.py's,
which D-003's Enforced by names beside this file. These tests characterise behaviour release B built, so the red-on-checkpoint
proof does not apply; their strength is shown by run/supervisor/TASK-044-mutants.json.

The guard runs as a subprocess on a temporary repository, with tests/test_task032_supervisor_guard.py's helpers. A launch is
the real launcher with a stand-in `cursor-agent`, its stderr in run/review/REVIEW-<name>.err as the loop's command leaves it.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

import pytest

import test_bug039 as B
import test_release_s_records_gate as S
import test_task032_supervisor_guard as G
import test_task032_supervisor_launcher as L

NAME = "TASK-001"
ID = "TASK-001"
OWNER_LINE = "Review rounds above the ceiling: TASK-001 5 (the owner's words, 2026-11-02)\n"
CLASS_LINE = "Blocking class: security - Review A, round 3, B1"
OTHER_CLASS_LINE = "Blocking class: behaviour - Review B, round 4, B2"
PROMPT = "Read run/review/REVIEW-TASK-001.diff %s" % L.PROMPT_TAG
HOLD_SCRIPT = """import os, sys, time
open(sys.argv[1], "w").close()
deadline = time.time() + 90
while not os.path.exists(sys.argv[2]) and time.time() < deadline:
    time.sleep(0.1)
"""


class Lab(object):
    """What tests/test_task032_supervisor_launcher.py's helpers read of a launch folder, over a guard test's repository."""

    def __init__(self, tmp_path, repo):
        self.tmp = tmp_path
        self.root = repo
        self.bin = tmp_path / "bin"
        self.marker = tmp_path / "stand-in-ran.txt"
        self.running = tmp_path / "stand-in-running.txt"
        self.release = tmp_path / "stand-in-release.txt"
        L.write_stand_in(self.bin, self.marker)

    @property
    def log(self):
        return self.root / "run" / "launcher" / "runs.jsonl"

    def hold(self):
        """The stand-in becomes one that runs until it is released, so a launch can be seen in flight or reach its limit."""
        script = self.tmp / "hold.py"
        script.write_text(HOLD_SCRIPT, encoding="utf-8")
        args = '"%s" "%s" "%s" "%s"' % (sys.executable, script, self.running, self.release)
        if sys.platform == "win32":
            (self.bin / "cursor-agent.cmd").write_text("@echo off\r\n%s\r\nexit /b %%ERRORLEVEL%%\r\n" % args, encoding="ascii")
        else:
            for name in ("cursor-agent", "cursor-agent.exe"):
                path = self.bin / name
                path.write_text("#!/bin/sh\nexec %s\n" % args, encoding="ascii")
                path.chmod(0o755)


def make(tmp_path):
    repo = G.make_repo(tmp_path)
    return repo, Lab(tmp_path, repo)


def err_of(repo, name=NAME):
    return repo / "run" / "review" / ("REVIEW-%s.err" % name)


def launcher_argv(limit, model):
    return [sys.executable, L.PROG, "--limit", limit, "--kind", "review", "--"] + L.agent(PROMPT, model=model)


def review(lab, name=NAME, stub_exit=0, limit="300", model=L.REVIEW_MODEL):
    """The launch as the loop's step 8 gives it, stderr to the round's `.err`; the launcher's exit."""
    with open(str(err_of(lab.root, name)), "w", encoding="utf-8") as f:
        p = subprocess.run(launcher_argv(limit, model), cwd=str(lab.root), env=L.launch_env(lab, stub_exit=stub_exit),
                           stdout=subprocess.DEVNULL, stderr=f, timeout=L.TIMEOUT)
    return p.returncode


def rows(repo):
    log = repo / "run" / "launcher" / "runs.jsonl"
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()] if log.is_file() else []


def err_lines(repo, name=NAME):
    return err_of(repo, name).read_text(encoding="utf-8").splitlines()


def mark(repo, name=NAME):
    path = G.bridge_dir(repo) / ("verified-%s.json" % name)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def premerge_refused(repo, words, name=NAME):
    before = G.bridge_dir(repo) / "premerge"
    rc, out = G.guard(repo, "premerge", name)
    assert rc == 2 and "CANNOT CHECK" in out and words in out, out
    assert not before.exists() or not list(before.iterdir()), "a refused premerge wrote a record"


def in_process(guard, monkeypatch, capsys, repo, *argv):
    """The guard's own main in this process, so one of its calls can be made to fail."""
    monkeypatch.chdir(str(repo))
    monkeypatch.setattr(sys, "argv", ["review-guard.py"] + list(argv))
    rc = guard.main()
    return rc, capsys.readouterr().out


def flagged(repo, words, command="verify", name=NAME):
    """The guard's own GATE-INTEGRITY exit, 1, which is an uncaught traceback's exit too."""
    rc, out = G.guard(repo, command, name)
    assert rc == 1 and words in out and "Traceback" not in out, out
    return out


def snapshot_copies(before):
    """The hash copies written since `before` that are the snapshot's: the rounds record's copy, `<key>-rounds-<ID>.sha256`, ends alike."""
    return [n for n in G.new_hash_files(before) if "-rounds-" not in n]


def write_scope(repo, line):
    """run/review/SCOPE-<ID>.md committed, as the loop commits it before a snapshot."""
    G.put(repo / "run" / "review" / ("SCOPE-%s.md" % ID), line + "\n")
    G.git(repo, "add", "-f", "run/review/SCOPE-%s.md" % ID)
    G.git(repo, "commit", "-q", "-m", "scope")


def three_rounds_reviewed(repo):
    for name in (ID, ID + "-r2", ID + "-r3"):
        G.reviewed(repo, name)


# --- the states ----------------------------------------------------------------------------------


def test_d003_state_no_record_a_refused_snapshot_leaves_it_so(tmp_path):
    """R-042, D-003 (`no_record`): no rounds record, and a snapshot refused off the count writes nothing, so it stays."""
    repo, _ = make(tmp_path)
    assert not G.rounds_file(repo, ID).exists()
    G.refuse_and_nothing(repo, ID + "-r2", G.REFUSED, "round 2 is off the count (current 0)")
    assert not G.rounds_file(repo, ID).exists()


def test_d003_state_snapshot_taken_opens_the_round(tmp_path):
    """R-042, D-003 (`round_open` at `snapshot_taken`): the first snapshot writes the snapshot, its hash copy and the round's
    entry with its tree, its time and no reply."""
    repo, _ = make(tmp_path)
    before = G.hash_files()
    G.snap_ok(repo, NAME)
    copies = snapshot_copies(before)
    assert len(copies) == 1 and copies[0].endswith("-%s.sha256" % NAME), copies
    snapshot = (G.bridge_dir(repo) / ("review-%s.json" % NAME)).read_bytes()
    assert G.hash_files()[copies[0]].strip() == hashlib.sha256(snapshot).hexdigest().encode("ascii")
    entry = G.entry(repo, ID, 1)
    assert entry["tree"] == G.git(repo, "rev-parse", "HEAD^{tree}") and entry["time"] and entry["reply"] is None, entry
    assert not entry.get("seeded") and entry["name"] == NAME, entry


def test_d003_state_review_launched_in_flight_and_its_log_row(tmp_path):
    """R-042, D-003 (`review_launched`, then `reply_arrived`; `review_launched --> verified_ok`): the real launcher's `.err`
    holds its started line and no exit line while the run goes on, no finished row is logged, and a verify then writes a mark
    with no exit, which premerge refuses, and no reply. Once the run ends, the last line is its exit and the row is logged:
    kind review, the model, no brief, no round, never the prompt."""
    repo, lab = make(tmp_path)
    lab.hold()
    G.snap_ok(repo, NAME)
    with open(str(err_of(repo)), "w", encoding="utf-8") as f:
        proc = subprocess.Popen(launcher_argv("300", L.REVIEW_MODEL), cwd=str(repo), env=L.launch_env(lab), stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=f)
        try:
            deadline = time.time() + 60
            while not lab.running.exists() and time.time() < deadline:
                time.sleep(0.1)
            assert lab.running.exists(), "the stand-in never started"
            lines = err_lines(repo)
            assert lines[0].startswith("bridge-run: started 20"), lines
            assert not [line for line in lines if line.startswith("bridge-run: exit")], lines
            assert [r for r in rows(repo) if r.get("exit") is not None] == []
            G.verify_ok(repo, NAME)
            assert mark(repo)["launched"] and mark(repo)["exit"] is None, mark(repo)
            assert G.entry(repo, ID, 1)["reply"] is None
            premerge_refused(repo, "ended with exit None")
            lab.release.write_text("go\n", encoding="utf-8")
            assert proc.wait(timeout=60) == 0
        finally:
            lab.release.write_text("go\n", encoding="utf-8")
            proc.wait(timeout=60)
    assert err_lines(repo)[-1] == "bridge-run: exit 0"
    row = rows(repo)[-1]
    assert row["kind"] == "review" and row["exit"] == 0 and row["model"] == L.REVIEW_MODEL, row
    assert "brief" not in row and "round" not in row and L.PROMPT_TAG not in json.dumps(row), row


def test_d003_state_reply_arrived_the_err_counts_before_any_verify(tmp_path):
    """R-042, D-003 (`reply_arrived`; the re-snapshot reading the `.err` as a reply): the launcher's exit 0, launched at or after
    the round's snapshot, makes round 1 replied with no verify run yet, so a snapshot of it on a changed tree is refused."""
    repo, lab = make(tmp_path)
    G.snap_ok(repo, NAME)
    assert review(lab) == 0
    assert G.entry(repo, ID, 1)["reply"] is None
    G.bump(repo)
    G.refuse_and_nothing(repo, NAME, G.REFUSED, "round 1 is reviewed: write %s-r2" % ID)
    G.snap_ok(repo, ID + "-r2")


def test_d003_state_reply_arrived_a_launch_before_the_round_is_no_reply(tmp_path):
    """R-042, D-003 (`reply_arrived`, its condition): an exit 0 left in the `.err` from before the round's first snapshot is no
    reply, so the round is taken again on a changed tree."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME, offset=-3600)
    G.bump(repo)
    G.snap_ok(repo, NAME)
    assert G.entry(repo, ID, 1)["reply"] is None


def test_d003_state_resnapshotted_a_launch_before_it_still_counts_against_the_round(tmp_path):
    """R-042, D-003 (`resnapshotted`, the round's first time kept): an exit 0 launched after the round's first snapshot and before
    its re-snapshot on the same tree stays the round's reply, so a changed tree is refused, naming the next round."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME, offset=0)
    G.next_second()
    G.next_second()
    G.snap_ok(repo, NAME)
    G.bump(repo)
    G.refuse_and_nothing(repo, NAME, G.REFUSED, "round 1 is reviewed: write %s-r2" % ID)


@pytest.mark.parametrize("stub_exit,limit,expected", [(3, "300", 3), (0, "2", 124)], ids=["the-agent-fails", "the-limit"])
def test_d003_state_no_verdict_the_launchers_own_exit(tmp_path, stub_exit, limit, expected):
    """R-042, D-003 (`no_verdict`, `no_verdict --> verified_ok`): the launcher's own non-zero exit, and its limit, end the `.err`
    with that exit and log the row with it; verify writes a mark holding it, no reply is written, and premerge refuses."""
    repo, lab = make(tmp_path)
    if limit == "2":
        lab.hold()
    G.snap_ok(repo, NAME)
    assert review(lab, stub_exit=stub_exit, limit=limit) == expected
    assert err_lines(repo)[-1] == "bridge-run: exit %d" % expected
    assert rows(repo)[-1]["kind"] == "review" and rows(repo)[-1]["exit"] == expected, rows(repo)
    G.verify_ok(repo, NAME)
    assert mark(repo)["exit"] == expected and G.entry(repo, ID, 1)["reply"] is None, mark(repo)
    premerge_refused(repo, "ended with exit %d" % expected)


def test_d003_transition_no_verdict_to_resnapshotted(tmp_path):
    """R-042, D-003 (`no_verdict --> resnapshotted`): a failed launch counts no reply, so the round is taken again, on a changed
    tree too, and a Review B on it then spends it."""
    repo, lab = make(tmp_path)
    G.snap_ok(repo, NAME)
    assert review(lab, stub_exit=3) == 3
    G.bump(repo)
    G.snap_ok(repo, NAME)
    assert G.entry(repo, ID, 1)["tree"] == G.git(repo, "rev-parse", "HEAD^{tree}")
    assert review(lab) == 0
    G.verify_ok(repo, NAME)
    assert G.entry(repo, ID, 1)["reply"] == 0


def test_d003_state_verified_ok_the_spent_arm(tmp_path):
    """R-042, D-003 (`reply_arrived --> verified_ok`): exit 0 launched after the snapshot writes reply 0, spending round 1, and a
    mark holding the launch and exit 0; a temporary file the reviewer left is removed and the `.err` is kept."""
    repo, lab = make(tmp_path)
    G.snap_ok(repo, NAME)
    assert review(lab) == 0
    G.put(repo / "reproduction.py", "print(1)\n")
    out = G.verify_ok(repo, NAME)
    assert "launch time line kept" in out and not (repo / "reproduction.py").exists() and err_of(repo).is_file(), out
    assert G.entry(repo, ID, 1)["reply"] == 0
    assert mark(repo)["exit"] == 0 and mark(repo)["launched"].rstrip("Z") == B.start_of(repo), mark(repo)


def test_d003_transition_verified_ok_with_no_launch(tmp_path):
    """R-042, D-003 (`snapshot_taken --> verified_ok`, the no-launch arm): verify with no `.err` writes a mark with no launch
    time and no reply, and premerge refuses it."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    out = G.verify_ok(repo, NAME)
    assert "no launch time" in out and mark(repo)["launched"] is None and G.entry(repo, ID, 1)["reply"] is None, out
    premerge_refused(repo, "no Review B launch after the snapshot")


def test_d003_transition_verified_ok_with_no_exit_yet(tmp_path):
    """R-042, D-003 (`review_launched --> verified_ok`, the no-exit arm, on the `.err` alone): a started line and no exit line
    write a mark with no exit and no reply; a second snapshot of the round on a changed tree is admitted, nothing having replied."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME, exit_code=None)
    G.verify_ok(repo, NAME)
    assert mark(repo)["exit"] is None and G.entry(repo, ID, 1)["reply"] is None, mark(repo)
    premerge_refused(repo, "ended with exit None")
    G.bump(repo)
    G.snap_ok(repo, NAME)


def test_d003_state_flagged_gate_integrity_after_restoring(tmp_path):
    """R-042, D-003 (`flagged_gate_integrity`, `reply_arrived --> flagged_gate_integrity` after restoring): a commit and a ref
    left by the reviewer flag the round at the end of verify: the tree is back and the ref gone, no mark and no reply, and the
    launch is voided by its start time, so the same launch is refused again and round 1 stays unspent."""
    repo, lab = make(tmp_path)
    G.snap_ok(repo, NAME)
    head = G.git(repo, "rev-parse", "HEAD")
    assert review(lab) == 0
    G.git(repo, "branch", "left-by-the-reviewer")
    G.put(repo / "a.py", "x = 'the reviewer'\n")
    G.git(repo, "commit", "-q", "-am", "the reviewer's commit")
    flagged(repo, "the tree is back at")
    assert G.git(repo, "rev-parse", "HEAD") == head and "left-by-the-reviewer" not in G.git(repo, "branch", "--list")
    assert mark(repo) is None
    entry = G.entry(repo, ID, 1)
    assert entry["reply"] is None and entry["flagged_launch"].rstrip("Z") == B.start_of(repo), entry
    flagged(repo, "voided")
    assert mark(repo) is None
    G.bump(repo)
    G.snap_ok(repo, NAME)


def test_d003_state_resnapshotted_keeps_the_time_and_clears_the_marks(tmp_path):
    """R-042, D-003 (`resnapshotted`, `snapshot_taken --> resnapshotted`, `verified_ok --> resnapshotted`): the tree is rewritten,
    the round's first time is kept, so a launch before the new snapshot still counts against the round, and the ID's marks go."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    first = G.entry(repo, ID, 1)
    G.next_second()
    G.bump(repo)
    G.snap_ok(repo, NAME)
    again = G.entry(repo, ID, 1)
    assert again["time"] == first["time"] and again["tree"] != first["tree"], again
    G.verify_ok(repo, NAME)
    assert mark(repo) is not None
    G.snap_ok(repo, NAME)
    assert mark(repo) is None, "a re-snapshot clears the ID's verified marks"
    G.launched(repo, NAME)
    G.verify_ok(repo, NAME)
    assert mark(repo) is not None
    G.bump(repo)
    G.snap_ok(repo, ID + "-r2")
    assert mark(repo) is None, "the next round's snapshot clears the mark of the round before it too"


def test_d003_transition_a_resnapshot_keeps_reply_and_lift_on_the_tree_it_reviewed(tmp_path):
    """R-042, D-003 (`verified_ok --> resnapshotted`): a spent round may be taken again on the tree it reviewed, its reply kept, and a
    lifted round so too, its lift and its line kept."""
    repo, lab = make(tmp_path)
    G.snap_ok(repo, NAME)
    assert review(lab) == 0
    G.verify_ok(repo, NAME)
    G.snap_ok(repo, NAME)
    assert G.entry(repo, ID, 1)["reply"] == 0
    G.bump(repo)
    G.reviewed(repo, ID + "-r2")
    G.reviewed(repo, ID + "-r3")
    G.bump(repo)
    G.put(repo / "docs" / "RUN_PARAMETERS.md", OWNER_LINE)
    G.snap_ok(repo, ID + "-r4")
    G.snap_ok(repo, ID + "-r4")
    entry = G.entry(repo, ID, 4)
    assert entry["lift"] == "owner" and entry["lift_line"] == OWNER_LINE.strip(), entry


def test_d003_state_premerged_writes_the_record_for_the_head(tmp_path):
    """R-042, D-003 (`premerged`, `verified_ok --> premerged`): after the review files' removal, the head descends from the reviewed
    one and differs only under run/review, the record the permission guard reads is written and the merge command printed."""
    repo, lab = make(tmp_path)
    G.put(repo / "run" / "review" / ("REVIEW-%s-r1.diff" % ID), "d\n")
    G.git(repo, "add", "-f", "run/review/REVIEW-%s-r1.diff" % ID)
    G.git(repo, "commit", "-q", "-m", "the review files")
    G.snap_ok(repo, NAME)
    assert review(lab) == 0
    G.verify_ok(repo, NAME)
    G.git(repo, "rm", "-q", "run/review/REVIEW-%s-r1.diff" % ID)
    G.git(repo, "commit", "-q", "-m", "remove the review files")
    head = G.git(repo, "rev-parse", "HEAD")
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 0 and "--squash --match-head-commit %s" % head in out, out
    record = json.loads((G.bridge_dir(repo) / "premerge" / head).read_text(encoding="utf-8"))
    assert record["review"] == NAME, record


# --- the transitions D-003 lists as unexercised ----------------------------------------------------


def test_d003_transition_the_owners_line_lifts_rounds_up_to_its_number(tmp_path):
    """R-042, D-003 (`round_open --> round_open`, lift owner): the owner's line admits rounds 4 and 5, recording the lift and the
    line on each; round 6 is above it and refused, nothing written."""
    repo, _ = make(tmp_path)
    three_rounds_reviewed(repo)
    G.bump(repo)
    G.refuse_and_nothing(repo, ID + "-r4", G.CEILING, ID + "-r4")
    G.put(repo / "docs" / "RUN_PARAMETERS.md", OWNER_LINE)
    for n in (4, 5):
        G.reviewed(repo, "%s-r%d" % (ID, n), change=n != 4)
        entry = G.entry(repo, ID, n)
        assert entry["lift"] == "owner" and entry["lift_line"] == OWNER_LINE.strip(), entry
    G.bump(repo)
    G.refuse_and_nothing(repo, ID + "-r6", G.CEILING, ID + "-r6")


@pytest.mark.parametrize("verified", [False, True], ids=["reply_arrived", "verified_ok"])
def test_d003_transition_the_changed_tree_refusal_names_the_next_round(tmp_path, verified):
    """R-042, D-003 (`reply_arrived --> reply_arrived`, `verified_ok --> verified_ok`): a replied round taken on a changed tree is
    refused, 125, naming the next round's name, and nothing is written; the same name on the reviewed tree is admitted."""
    repo, lab = make(tmp_path)
    G.snap_ok(repo, NAME)
    reviewed_tree = G.git(repo, "rev-parse", "HEAD^{tree}")
    assert review(lab) == 0
    if verified:
        G.verify_ok(repo, NAME)
    head = G.git(repo, "rev-parse", "HEAD")
    G.bump(repo)
    G.refuse_and_nothing(repo, NAME, G.REFUSED, "round 1 is reviewed: write %s-r2" % ID)
    G.git(repo, "reset", "-q", "--hard", head)
    assert G.git(repo, "rev-parse", "HEAD^{tree}") == reviewed_tree
    G.snap_ok(repo, NAME)


def test_d003_transition_a_class_line_lifts_one_round_and_is_then_recorded(tmp_path):
    """R-042, D-003 (`round_open --> round_open`, lift class; a Blocking class line already recorded): the line lifts round 4 and
    is recorded on it; the same line does not lift round 5, refused with nothing written; another line does."""
    repo, _ = make(tmp_path)
    three_rounds_reviewed(repo)
    write_scope(repo, CLASS_LINE)
    G.snap_ok(repo, ID + "-r4")
    entry = G.entry(repo, ID, 4)
    assert entry["lift"] == "class" and entry["lift_line"] == CLASS_LINE, entry
    G.launched(repo, ID + "-r4")
    G.verify_ok(repo, ID + "-r4")
    G.bump(repo)
    G.refuse_and_nothing(repo, ID + "-r5", G.CEILING, ID + "-r5")
    write_scope(repo, OTHER_CLASS_LINE)
    G.snap_ok(repo, ID + "-r5")
    assert G.entry(repo, ID, 5)["lift_line"] == OTHER_CLASS_LINE


def test_d003_transition_a_class_line_recorded_refuses_a_round_below_the_ceiling(tmp_path, monkeypatch):
    """R-042, D-003 (`round_open --> round_open`, a Blocking class line already recorded): the line a round's record already holds
    refuses the next round below the ceiling too, by its own message. The record is planted here: the guard writes a class lift only
    above the ceiling, so its own records do not reach this branch (a lead in docs/HARDENING.md)."""
    repo, _ = make(tmp_path)
    G.reviewed(repo, NAME)
    guard = B.load_guard(monkeypatch)
    root, _git, common = guard.find_git_dirs(str(repo))
    data = G.rounds(repo, ID)
    data["rounds"][0].update(lift="class", lift_line=CLASS_LINE)
    guard.write_rounds(common, ID, data)
    write_scope(repo, CLASS_LINE)
    G.refuse_and_nothing(repo, ID + "-r2", G.CEILING, "class line already recorded for %s" % ID)


REFUSALS = {"the-roster-builder-model": "review launch on the roster builder model", "a-brief-named": "must not name a brief",
            "the-family-that-built": "is of the xai family"}


@pytest.mark.parametrize("refusal", sorted(REFUSALS))
def test_d003_transition_a_review_launch_refused_leaves_no_started_line(tmp_path, refusal):
    """R-042, D-003 (`snapshot_taken --> snapshot_taken`): a review launch on the roster's builder model, naming a brief, or of the
    family that built the change is refused, 125, the stand-in not run, with no started line and no row, and `verify` then sees no launch."""
    repo, lab = make(tmp_path)
    (repo / "docs").mkdir(exist_ok=True)
    L.write_roster(lab)
    G.git(repo, "add", "-f", "docs/ROSTER.resolved.json")
    G.git(repo, "commit", "-q", "-m", "the roster")
    G.snap_ok(repo, NAME)
    model, prompt = L.REVIEW_MODEL, PROMPT
    if refusal == "the-roster-builder-model":
        model = L.BUILDER_MODEL
    elif refusal == "a-brief-named":
        prompt = "Read handoff/%s.md %s" % (NAME, L.PROMPT_TAG)
    else:
        model = "grok-4.7-high"
        G.append_log(repo, json.dumps({"id": "2026-11-01T10:00:00Z", "kind": "builder", "head": "cursor-agent", "model": "grok-4.7-medium",
                                       "branch": "task-001", "limit": 7200, "seconds": 5, "exit": 0, "healthy": None}) + "\n")
    before = L.log_lines(lab.log)
    with open(str(err_of(repo)), "w", encoding="utf-8") as f:
        p = subprocess.run([sys.executable, L.PROG, "--limit", "300", "--kind", "review", "--"] + L.agent(prompt, model=model),
                           cwd=str(repo), env=L.launch_env(lab), stdout=subprocess.DEVNULL, stderr=f, timeout=L.TIMEOUT)
    text = err_of(repo).read_text(encoding="utf-8")
    assert p.returncode == 125 and text.startswith(L.REFUSED) and "bridge-run: started" not in text, text
    assert not lab.marker.exists() and L.log_lines(lab.log) == before
    assert REFUSALS[refusal] in text, text
    G.verify_ok(repo, NAME)
    assert mark(repo)["launched"] is None and G.entry(repo, ID, 1)["reply"] is None, mark(repo)


@pytest.mark.parametrize("flag", ["snapshot-rewritten", "config-changed", "at-the-end-of-verify"])
def test_d003_transition_a_void_write_failing_at_a_pre_git_or_end_of_verify_return(tmp_path, monkeypatch, capsys, flag):
    """R-042, D-003 (`reply_arrived --> reply_arrived`, the stated limit): the void's write failing at a pre-git return or at the end
    of verify prints the flag, then main's CANNOT VERIFY, exit 2, with no not-recorded line, no void, no reply and no mark."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    if flag == "snapshot-rewritten":
        B.rewrite_the_snapshot(repo)
    elif flag == "config-changed":
        B.change_the_config(repo)
    else:
        G.git(repo, "branch", "left-by-the-reviewer")
    guard = B.load_guard(monkeypatch)

    def failing_write(*_args):
        raise OSError("the record cannot be written")

    monkeypatch.setattr(guard, "write_rounds", failing_write)
    rc, out = in_process(guard, monkeypatch, capsys, repo, "verify", NAME)
    assert rc == 2 and "GATE-INTEGRITY" in out and "CANNOT VERIFY" in out and "not recorded" not in out, out
    assert "flagged_launch" not in G.entry(repo, ID, 1) and G.entry(repo, ID, 1)["reply"] is None, G.entry(repo, ID, 1)
    assert mark(repo) is None
    if flag == "at-the-end-of-verify":
        G.verify_ok(repo, NAME)
        assert G.entry(repo, ID, 1)["reply"] == 0, "the launch stays admissible at the next verify, the limit D-003 states"


def test_d003_transition_a_flag_while_the_rounds_record_is_tampered_with(tmp_path):
    """R-042, D-003 (`reply_arrived --> flagged_gate_integrity`, the rounds record changed outside the guard): the flag is printed with
    its own exit, nothing is voided since the record is what cannot be read, no mark is written, and the next snapshot is refused."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.git(repo, "branch", "left-by-the-reviewer")
    path = G.rounds_file(repo, ID)
    tampered = path.read_text(encoding="utf-8").replace('"reply": null', '"reply": 0')
    assert '"reply": 0' in tampered
    path.write_text(tampered, encoding="utf-8")
    flagged(repo, "left-by-the-reviewer")
    assert path.read_text(encoding="utf-8") == tampered, "nothing is written to a record that cannot be trusted"
    assert mark(repo) is None
    G.refuse_and_nothing(repo, NAME, G.TAMPER, ID)


def test_d003_transition_the_snapshot_rewritten_voids_an_earlier_launch_at_resnapshotted(tmp_path):
    """R-042, D-003 (`resnapshotted --> flagged_gate_integrity`): with no launch since the re-snapshot, the rewritten snapshot's return
    voids the round's earlier failed launch still in the `.err`, by the round's recorded time, exit 1, no mark."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME, offset=0, exit_code=1)
    G.next_second()
    G.next_second()
    G.snap_ok(repo, NAME)
    B.rewrite_the_snapshot(repo)
    flagged(repo, "rewritten after it was taken")
    entry = G.entry(repo, ID, 1)
    assert entry["flagged_launch"].rstrip("Z") == B.start_of(repo) and entry["reply"] is None, entry
    assert mark(repo) is None


@pytest.mark.parametrize("launch", ["no-err", "an-err-with-no-started-line", "a-launch-before-the-snapshot"])
def test_d003_transition_a_flagged_round_with_nothing_voided_verifies_clean(tmp_path, launch):
    """R-042, D-003 (`flagged_gate_integrity --> verified_ok`): a flag with no launch to void leaves no `flagged_launch`; the next
    verify finds nothing left, exit 0, and writes a mark premerge refuses, no Review B having run on this snapshot."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    if launch == "a-launch-before-the-snapshot":
        G.launched(repo, NAME, offset=-3600)
    elif launch == "an-err-with-no-started-line":
        G.put(err_of(repo), "reviewer output\n")
    G.git(repo, "branch", "left-by-the-reviewer")
    flagged(repo, "left-by-the-reviewer")
    assert "flagged_launch" not in G.entry(repo, ID, 1), G.entry(repo, ID, 1)
    G.verify_ok(repo, NAME)
    assert G.entry(repo, ID, 1)["reply"] is None
    premerge_refused(repo, "no Review B launch after the snapshot")


def _verified_and_clean(tmp_path):
    repo, lab = make(tmp_path)
    G.snap_ok(repo, NAME)
    assert review(lab) == 0
    G.verify_ok(repo, NAME)
    return repo


def test_d003_transition_premerge_refused_on_no_hash_copy(tmp_path):
    """R-042, D-003 (`verified_ok --> verified_ok`): the snapshot's hash copy gone, premerge cannot verify, exit 2, and writes no record."""
    before = G.hash_files()
    repo = _verified_and_clean(tmp_path)
    copies = snapshot_copies(before)
    assert copies
    for name in copies:
        os.remove(os.path.join(G.hash_dir(), name))
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 2 and "no copy of the snapshot hash" in out, out
    assert not (G.bridge_dir(repo) / "premerge").exists()


def test_d003_transition_premerge_refused_on_a_git_failure(tmp_path, monkeypatch, capsys):
    """R-042, D-003 (`verified_ok --> verified_ok`): a git failure inside premerge is CANNOT VERIFY, exit 2, and writes no record."""
    repo = _verified_and_clean(tmp_path)
    guard = B.load_guard(monkeypatch)

    def failing(args, root, common):
        raise RuntimeError("git %s failed" % args[0])

    monkeypatch.setattr(guard, "run_git", failing)
    rc, out = in_process(guard, monkeypatch, capsys, repo, "premerge", NAME)
    assert rc == 2 and "CANNOT VERIFY - git " in out, out
    assert not (G.bridge_dir(repo) / "premerge").exists()


def test_d003_transition_premerge_refused_when_the_record_cannot_be_written(tmp_path):
    """R-042, D-003 (`verified_ok --> verified_ok`): the premerge record not written is CANNOT CHECK, exit 2, with no merge command."""
    repo = _verified_and_clean(tmp_path)
    G.put(G.bridge_dir(repo) / "premerge", "a file where the folder must be made\n")
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 2 and "the pre-merge record could not be written" in out and "--match-head-commit" not in out, out


@pytest.mark.parametrize("command", ["verify", "premerge"])
def test_d003_transition_verify_or_premerge_at_no_record_with_a_hash_copy_standing(tmp_path, command):
    """R-042, D-003 (`no_record --> no_record`): `.git/bridge` cleared with the hash copies standing, the name that had a snapshot is
    GATE-INTEGRITY, exit 1, nothing voided since no rounds record holds the launch, no mark and no record; and the record gone behind
    its hash copy refuses the next snapshot."""
    repo, _ = make(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    bridge = pathlib.Path(G.bridge_dir(repo))
    for path in bridge.iterdir():
        path.unlink()
    flagged(repo, "the snapshot was deleted after it was taken", command=command)
    assert not G.rounds_file(repo, ID).exists() and mark(repo) is None
    assert not (bridge / "premerge").exists()
    G.refuse_and_nothing(repo, NAME, G.TAMPER, ID)


# --- the short gate's path, as release S built it (TASK-056, R-067) ---------------------------------------


def records_repo(tmp_path):
    """main as merged beside origin/main and a branch `records` with one record changed: the status file. The helpers are
    tests/test_release_s_records_gate.py's."""
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\n", encoding="utf-8")
    (r / "docs" / "REQUIREMENTS.md").write_text(S.REGISTER, encoding="utf-8")
    S.git(r, "init", "-q", "-b", "main")
    S.git(r, "add", "-A")
    S.git(r, "commit", "-q", "-m", "base")
    S.git(r, "update-ref", "refs/remotes/origin/main", "HEAD")
    S.git(r, "checkout", "-q", "-b", "records")
    S.change(r, "docs/PROJECT_STATUS.md", "Phase: done\n")
    return r


def guard_files(repo):
    folder = repo / ".git" / "bridge"
    return sorted(os.path.relpath(os.path.join(d, f), str(folder)).replace("\\", "/") for d, _, files in os.walk(str(folder)) for f in files)


def test_d003_state_records_branch_premerge_records_cannot_check_a_dirty_tree(tmp_path):
    """R-067, D-003 (`records_branch`, `records_branch --> records_branch`): a branch of records alone, no rounds record, no snapshot;
    `premerge-records` before the push on a tree not clean is CANNOT CHECK, exit 2, and writes nothing."""
    repo = records_repo(tmp_path)
    (repo / "docs" / "PROJECT_STATUS.md").write_text("Phase: done, edited\n", encoding="utf-8")
    rc, out = S.run(repo, "premerge-records")
    assert rc == 2 and "CANNOT CHECK - the tree is not clean" in out and guard_files(repo) == [], out


def test_d003_state_short_gate_answered_before_the_push_writes_nothing(tmp_path):
    """R-067, D-003 (`records_branch --> short_gate`): `premerge-records` before the push answers SHORT GATE, exit 0, and writes
    nothing: no snapshot, no rounds record, no premerge record yet."""
    repo = records_repo(tmp_path)
    rc, out = S.run(repo, "premerge-records")
    assert rc == 0 and "SHORT GATE - 1 changed file(s)" in out and "nothing was written" in out, out
    assert guard_files(repo) == []


def test_d003_state_records_premerged_writes_the_record_for_the_head(tmp_path, program, monkeypatch, capsys):
    """R-067, D-003 (`short_gate --> records_premerged`): `premerge-records <pr>` with the pull request's head equal to the local head
    answers OK - records only, writes `premerge/<head>` with review `records` and the files, and prints the merge command."""
    for k in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"):
        monkeypatch.setenv(k, os.devnull)
    repo = records_repo(tmp_path)
    mod = program("review-guard")
    head = S.git(repo, "rev-parse", "HEAD")
    monkeypatch.setattr(mod, "pr_state", lambda pr, root: (S.state(repo, ["docs/PROJECT_STATUS.md"]), None))
    rc = mod.cmd_premerge_records(str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 0 and "OK - records only, 1 file(s)" in out and "gh pr merge 12 --squash --match-head-commit %s" % head in out, out
    assert guard_files(repo) == ["premerge/" + head]
    record = json.loads((repo / ".git" / "bridge" / "premerge" / head).read_text(encoding="utf-8"))
    assert record["review"] == "records" and record["pr"] == "12" and record["files"] == ["docs/PROJECT_STATUS.md"], record
