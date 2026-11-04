"""Supervisor-side reproduction tests of BUG-039 (R-042, R-055; D-003 and D-004); written by the supervisor; the builder reads and runs them, never edits them.

R-042: a flagged round spends nothing, whichever of `verify`'s checks flagged it and whenever. D-003 draws that; as built
(docs/debug/BUG-039.md) `review-guard.py` did not hold it at four sites, and D-004 draws every git command of the guard
with the hooks and the file monitor off, which `premerge`'s one direct call did not hold. The names these tests call are
the fix's fixed points: `flagged_launch` (the round's key holding the voided launch's start time), `_git_proc` (the one
call site of git). The helpers are tests/test_task032_supervisor_guard.py's, imported, so the fixtures are the same.
"""
import ast
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys

import pytest

import test_task032_supervisor_guard as G

NAME = "TASK-001"
ID = "TASK-001"


def start_of(repo, name=NAME):
    """The launch's start time as the launcher's first line gives it, without its Z."""
    with open(str(repo / "run" / "review" / ("REVIEW-%s.err" % name)), encoding="utf-8") as f:
        return re.search(r"started (\S+?)Z?$", f.readline().strip()).group(1)


def add_exit_0(repo, name=NAME):
    """The run that was still going ends: the launcher appends its exit line to the same .err."""
    with open(str(repo / "run" / "review" / ("REVIEW-%s.err" % name)), "a", encoding="utf-8") as f:
        f.write("bridge-run: exit 0\n")


def flagged_key(repo):
    return (G.entry(repo, NAME, 1).get("flagged_launch") or "").rstrip("Z")


def flagged_round(tmp_path, **launch):
    """A round whose verify flagged it (a ref left behind), its Review B launched as `launch` says, by default exited 0."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME, **launch)
    G.git(repo, "branch", "left-by-the-reviewer")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    return repo


def watch_git(monkeypatch):
    """Every git process `subprocess.run` starts from here on recorded and run as asked; the record is returned."""
    started = []
    real_run = subprocess.run

    def watching(cmd, *args, **kwargs):
        if cmd and cmd[0] == "git":
            started.append(list(cmd))
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", watching)
    return started


def assert_voided_and_round_not_spent(repo):
    """The launch is voided by its start time, no reply is counted, and round 1 may be taken again on a changed tree."""
    assert flagged_key(repo) == start_of(repo), G.entry(repo, NAME, 1)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    G.bump(repo)
    G.snap_ok(repo, NAME)


def load_guard(monkeypatch):
    """review-guard.py loaded in this process, so one of its calls can be watched or stubbed."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.syspath_prepend(os.path.dirname(G.PROG))
    for key, value in G.env().items():
        monkeypatch.setenv(key, value)
    spec = importlib.util.spec_from_file_location("review_guard_bug039", G.PROG)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- Site 1: the four early returns of cmd_verify ------------------------------------------

def rewrite_the_snapshot(repo):
    snap = G.bridge_dir(repo) / ("review-%s.json" % NAME)
    text = snap.read_text(encoding="utf-8")
    snap.write_text(text.replace('"nnn"', '"nnn" ', 1), encoding="utf-8")


def change_the_config(repo):
    G.git(repo, "config", "bug039.left", "by-the-reviewer")


def plant_a_hook(repo):
    G.put(repo / ".git" / "hooks" / "post-checkout", "#!/bin/sh\nexit 0\n")


@pytest.mark.parametrize("left_behind", [rewrite_the_snapshot, change_the_config, plant_a_hook],
                         ids=["snapshot-rewritten", "config-changed", "hook-changed"])
def test_bug039_site1_a_flag_before_any_git_command_voids_the_launch(tmp_path, left_behind):
    """R-042, D-003 (`reply_arrived` to `flagged_gate_integrity`). enforces: docs/BUILD_PLAN.md TASK-043 Done when (1):
    `cmd_verify`'s early GATE-INTEGRITY returns on the snapshot rewritten and on `.git/config` or a hook changed call
    `record_flagged_launch`, so the launch is voided and round 1 is not spent."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    left_behind(repo)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    assert_voided_and_round_not_spent(repo)


@pytest.mark.parametrize("rewritten", ["[]", "{}", '{"taken": 5}', '{"taken": "9999-01-01T00:00:00Z"}', '{"taken": "zzz"}', "null", "not json", "[" * 200000],
                         ids=["not-an-object", "no-taken", "taken-not-a-string", "taken-in-the-future", "taken-not-a-time", "json-null", "not-json", "too-deep"])
def test_bug039_site1_negative_a_snapshot_rewritten_to_any_shape_stays_a_clean_flag(tmp_path, rewritten):
    """R-042, D-003. enforces: TASK-043's r2 brief, Requirement 1: the snapshot's content is untrusted at the first early
    return, so neither its shape nor its value decides the void: whatever it was rewritten to, `verify` ends in the
    GATE-INTEGRITY line and exit 1 with no traceback, the launch is voided, and round 1 may be taken again on a changed
    tree (Review A and the security audit, round 1)."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    (G.bridge_dir(repo) / ("review-%s.json" % NAME)).write_text(rewritten, encoding="utf-8")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "rewritten after it was taken" in out, out
    assert "Traceback" not in out, out
    assert_voided_and_round_not_spent(repo)


def test_bug039_site1_negative_a_rewritten_snapshot_voids_no_launch_before_the_round(tmp_path):
    """R-042, D-003. enforces: TASK-043's r2 brief, Requirement 1: at the rewritten return the launch is compared with the
    round entry's `time` from the hash-checked record, so a snapshot rewritten to hold no time does not void a launch
    from before the round."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME, offset=-3600)
    (G.bridge_dir(repo) / ("review-%s.json" % NAME)).write_text("{}", encoding="utf-8")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "rewritten after it was taken" in out, out
    assert "flagged_launch" not in G.entry(repo, NAME, 1), G.entry(repo, NAME, 1)


@pytest.mark.parametrize("rewritten", [True, False], ids=["snapshot-rewritten", "config-changed"])
def test_bug039_site1_negative_the_void_runs_no_git_on_the_pre_git_returns(tmp_path, monkeypatch, capsys, rewritten):
    """R-042, D-003. enforces: TASK-043's brief, Requirement 2: at the snapshot-rewritten and the config-or-hook returns the
    void runs no git command, as their printed lines say. Every git process started during the void is watched."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    if rewritten:
        rewrite_the_snapshot(repo)
    else:
        change_the_config(repo)
    guard = load_guard(monkeypatch)
    during = []
    real_record = guard.record_flagged_launch
    started = watch_git(monkeypatch)

    def watched_record(*args):
        del started[:]
        real_record(*args)
        during.append(list(started))

    monkeypatch.setattr(guard, "record_flagged_launch", watched_record)
    assert guard.cmd_verify(NAME, str(repo)) == 1
    assert "no git command was run" in capsys.readouterr().out
    assert during == [[]]


@pytest.mark.parametrize("rewritten", ["null", "not json"], ids=["json-null", "not-json"])
def test_bug039_site1_negative_premerge_reaches_its_rewritten_return(tmp_path, rewritten):
    """R-042, D-003. enforces: TASK-043's r2 brief, Requirement 1: `premerge` reads the same snapshot, so a rewrite to anything
    reaches its rewritten return too: GATE-INTEGRITY, exit 1, no traceback."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.verify_ok(repo, NAME)
    (G.bridge_dir(repo) / ("review-%s.json" % NAME)).write_text(rewritten, encoding="utf-8")
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    assert "Traceback" not in out, out


def test_bug039_site1_negative_an_unreadable_snapshot_stays_a_cannot_verify(tmp_path, monkeypatch, capsys):
    """R-042, D-003. enforces: TASK-043's r3 brief, Requirement 1 (Review A's Blocking 1 and the security audit's B1, round 2):
    a snapshot that cannot be read, as a scanner holding it open makes it, has not been shown rewritten: exit 2 with the
    CANNOT VERIFY line, as `main` gives every OSError, never a traceback and never exit 1."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    guard = load_guard(monkeypatch)

    def held(_file):
        raise PermissionError(13, "held open")

    monkeypatch.setattr(guard.json, "load", held)
    monkeypatch.chdir(str(repo))
    monkeypatch.setattr(sys, "argv", ["review-guard.py", "verify", NAME])
    assert guard.main() == 2
    assert "CANNOT VERIFY" in capsys.readouterr().out


def test_bug039_site1_the_branch_held_in_another_worktree_voids_the_launch(tmp_path):
    """R-042, D-003. enforces: TASK-043 Done when (1), the third early return: the recorded branch checked out in another
    worktree."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.git(repo, "checkout", "-q", "-b", "other")
    wt = tmp_path / "wt"
    G.git(repo, "worktree", "add", "-q", str(wt), "task-001")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "another worktree" in out, out
    G.git(repo, "worktree", "remove", str(wt))
    G.git(repo, "checkout", "-q", "task-001")
    assert_voided_and_round_not_spent(repo)


def test_bug039_site1_the_branch_not_put_back_voids_the_launch(tmp_path, monkeypatch, capsys):
    """R-042, D-003. enforces: TASK-043 Done when (1), the fourth early return: the checkout could not be put back on the
    recorded branch. Git's checkout is stubbed to do nothing, the one way to reach that return on an ordinary repository."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.git(repo, "checkout", "-q", "-b", "other")
    guard = load_guard(monkeypatch)
    real_run_git = guard.run_git
    monkeypatch.setattr(guard, "run_git",
                        lambda args, root, common: "" if args[:1] == ["checkout"] else real_run_git(args, root, common))
    assert guard.cmd_verify(NAME, str(repo)) == 1
    assert "could not be put back" in capsys.readouterr().out
    G.git(repo, "checkout", "-q", "task-001")
    assert_voided_and_round_not_spent(repo)


def test_bug039_site1_negative_no_path_clears_a_recorded_flag(tmp_path):
    """R-042, D-003. enforces: TASK-043 Done when, the negative case of site 1: a flag once recorded is cleared by no path
    of the fix: a verify that now finds nothing to flag, and a re-snapshot, leave it where it was and count no reply."""
    repo = flagged_round(tmp_path)
    voided = flagged_key(repo)
    assert voided == start_of(repo)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1, out
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    G.snap_ok(repo, NAME)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1, out
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)


# --- Site 2: a flag raised while the run still goes on ------------------------------------

def test_bug039_site2_a_flag_during_the_run_voids_the_launch_that_later_exits_0(tmp_path):
    """R-042, D-003 (`review_launched` to `flagged_gate_integrity`). enforces: TASK-043 Done when (2):
    `record_flagged_launch` records the void by the launch's start time whatever the `.err` file's exit so far, so a flag
    raised while the run goes on voids the launch that later exits 0, and the next snapshot of the round on a changed tree
    is admitted."""
    repo = flagged_round(tmp_path, exit_code=None)
    add_exit_0(repo)
    assert_voided_and_round_not_spent(repo)


def test_bug039_site2_negative_no_path_admits_a_flagged_launch(tmp_path):
    """R-042, D-003. enforces: TASK-043 Done when, the negative case of site 2: a flagged round's launch is admitted by no
    path. A flag raised during the run, the run then exiting 0, and a verify that finds nothing left to flag (the first
    verify repaired the ref): no reply, no verified mark, exit 1, and `premerge` refuses. A new Review B run on the same
    snapshot is a launch of its own, and it is admitted."""
    repo = flagged_round(tmp_path, exit_code=None)
    add_exit_0(repo)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    assert not (G.bridge_dir(repo) / ("verified-%s.json" % NAME)).exists(), out
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 2 and "no verified mark" in out, out
    G.launched(repo, NAME, offset=3)
    G.verify_ok(repo, NAME)
    assert G.entry(repo, NAME, 1).get("reply") == 0, G.entry(repo, NAME, 1)
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 0, out


@pytest.mark.parametrize("exit_code", [None, 0, 1], ids=["no-exit-yet", "exit-0", "exit-1"])
def test_bug039_site2_the_void_holds_whatever_the_exit(tmp_path, exit_code):
    """R-042, D-003. enforces: TASK-043's brief, Requirements 3 and 4: the flag voids the launch whatever the `.err` file's
    exit so far, and a verify that finds nothing left to flag refuses that launch whatever its exit: exit 1, a line saying
    it was voided, no reply, no mark."""
    repo = flagged_round(tmp_path, exit_code=exit_code)
    assert flagged_key(repo) == start_of(repo), G.entry(repo, NAME, 1)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out and "voided" in out, out
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    assert not (G.bridge_dir(repo) / ("verified-%s.json" % NAME)).exists(), out


def test_bug039_site2_negative_a_voided_launch_stays_voided_under_a_later_snapshot(tmp_path):
    """R-042, D-003. enforces: TASK-043's brief, Requirement 4, "whether or not the launch is at or after the current
    snapshot": the same round taken again after the launch, its exit 0 and its flag still refuse it."""
    repo = flagged_round(tmp_path)
    for _ in range(3):
        G.next_second()
    G.snap_ok(repo, NAME)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "voided" in out, out
    assert not (G.bridge_dir(repo) / ("verified-%s.json" % NAME)).exists(), out


def test_bug039_site2_negative_a_voided_verify_still_restores_the_tree(tmp_path):
    """R-042, D-003. enforces: TASK-043's brief, Requirement 4: the refusal comes after the restore, so what the run left in
    the tree is gone though the launch is refused."""
    repo = flagged_round(tmp_path)
    G.put(repo / "left-by-the-reviewer.txt", "left\n")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "voided" in out, out
    assert not (repo / "left-by-the-reviewer.txt").exists(), out


def delete_the_record(path):
    os.remove(str(path))


def append_to_the_record(path):
    with open(str(path), "ab") as f:
        f.write(b" ")


@pytest.mark.parametrize("tamper", [delete_the_record, append_to_the_record], ids=["record-deleted", "record-changed"])
def test_bug039_site2_negative_a_tampered_record_admits_no_launch(tmp_path, tamper):
    """R-042, D-003. enforces: TASK-043's r2 brief, Requirement 2 (Review A and the security audit, round 1): the record the
    void lives in is changed or deleted outside the guard, its hash copy still standing. `verify` says so as GATE-INTEGRITY,
    exit 1, no mark, and `premerge` refuses."""
    repo = flagged_round(tmp_path, exit_code=None)
    add_exit_0(repo)
    tamper(G.bridge_dir(repo) / ("rounds-%s.json" % ID))
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out and "rounds record" in out, out
    assert not (G.bridge_dir(repo) / ("verified-%s.json" % NAME)).exists(), out
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 2 and "no verified mark" in out, out


def test_bug039_site2_negative_the_tamper_line_is_the_fixed_sentence(tmp_path, monkeypatch):
    """R-042, D-003. enforces: TASK-043's r3 brief, Requirement 4 (Review A's Should fix 3 of round 2, and both reviewers' note of
    round 3 that nothing pinned it): a record of the wrong shape with its hash copy gone reaches `load_rounds`' own message, which
    holds no such words as `rounds record`. The line printed is the one fixed sentence naming the ID, the message not printed."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    guard = load_guard(monkeypatch)
    os.remove(guard.rounds_hash_copy_path(os.path.realpath(str(G.bridge_dir(repo).parent)), ID))
    (G.bridge_dir(repo) / ("rounds-%s.json" % ID)).write_text('{"rounds": 5}', encoding="utf-8")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1, out
    assert ("review-guard: GATE-INTEGRITY - the rounds record of %s was changed outside the guard or cannot be read" % ID) in out, out
    assert "is not a list" not in out, out
    assert not (G.bridge_dir(repo) / ("verified-%s.json" % NAME)).exists(), out
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 2 and "no verified mark" in out, out


def test_bug039_site2_a_launch_in_the_snapshot_s_own_second_is_voided(tmp_path):
    """R-042, D-003. enforces: TASK-043's brief, Requirement 3, "at or after" the snapshot (stage T2's review, Review A's tests part):
    `G.launched` starts a launch a second later by default, so `<=` for `<` at the comparison survived this file."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    with open(str(G.bridge_dir(repo) / ("review-%s.json" % NAME)), encoding="utf-8") as f:
        taken = json.load(f)["taken"].rstrip("Z")
    G.put(repo / "run" / "review" / ("REVIEW-%s.err" % NAME), "bridge-run: started %sZ\nbridge-run: exit 0\n" % taken)
    G.git(repo, "branch", "left-by-the-reviewer")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    assert flagged_key(repo) == taken, G.entry(repo, NAME, 1)


def in_the_snapshot_s_own_second(tmp_path):
    """A round whose Review B started in the second the snapshot was taken and exited 0; `G.launched` starts one a second later."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    with open(str(G.bridge_dir(repo) / ("review-%s.json" % NAME)), encoding="utf-8") as f:
        taken = json.load(f)["taken"].rstrip("Z")
    G.put(repo / "run" / "review" / ("REVIEW-%s.err" % NAME), "bridge-run: started %sZ\nbridge-run: exit 0\n" % taken)
    return repo, taken


def test_bug042_a_clean_launch_in_the_snapshot_s_own_second_gets_its_reply(tmp_path):
    """R-042, D-003. enforces: docs/debug/BUG-042.md, stage T2's review, Review A's tests part, C3: at or after, at verify's mark."""
    repo, _ = in_the_snapshot_s_own_second(tmp_path)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 0, out
    assert G.entry(repo, NAME, 1)["reply"] == 0


def test_bug042_an_unverified_launch_at_the_round_s_own_time_counts_as_its_reply(tmp_path, monkeypatch):
    """R-042, D-003. enforces: docs/debug/BUG-042.md, stage T2's review, Review A's tests part, C3: at or after, where an unverified run is read."""
    repo, taken = in_the_snapshot_s_own_second(tmp_path)
    guard = load_guard(monkeypatch)
    assert guard.err_counts_as_reply(str(repo), {"name": NAME, "time": taken + "Z"}) is True


def test_bug039_site2_negative_a_launch_before_the_snapshot_is_not_voided(tmp_path):
    """R-042, D-003. enforces: TASK-043's brief, Requirement 3: a launch before the snapshot, or an `.err` with no started
    line, is no launch of this snapshot, and a flag voids neither. An invariant (a mutant of the fixed guard shows it
    strong)."""
    repo = flagged_round(tmp_path, offset=-3600)
    assert "flagged_launch" not in G.entry(repo, NAME, 1), G.entry(repo, NAME, 1)
    G.put(repo / "run" / "review" / ("REVIEW-%s.err" % NAME), "reviewer output\n")
    G.git(repo, "branch", "left-by-the-reviewer-again")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out and "Traceback" not in out, out
    assert "flagged_launch" not in G.entry(repo, NAME, 1), G.entry(repo, NAME, 1)


def test_bug039_site2_negative_a_void_touches_only_its_key(tmp_path):
    """R-042, D-003. enforces: TASK-043's brief, Requirement 3: writing `flagged_launch` touches only that key of that
    round's entry, an existing `reply` left as it is. An invariant (a mutant of the fixed guard shows it strong)."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.verify_ok(repo, NAME)
    before = dict(G.entry(repo, NAME, 1))
    assert before.get("reply") == 0, before
    G.git(repo, "branch", "left-by-the-reviewer")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    after = dict(G.entry(repo, NAME, 1))
    assert after.pop("flagged_launch").rstrip("Z") == start_of(repo), after
    assert after == before


def void_path_call(tmp_path, monkeypatch, snap, rounds=None):
    """`record_flagged_launch` called directly on round 1 of a launched round, the record's read and write stubbed: returns the
    reads and the writes it made. With `rounds` None the read fails the test, so a call that returns before it passes."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    guard = load_guard(monkeypatch)
    reads, writes = [], []

    def read(*args, **kwargs):
        assert rounds is not None, "the record was read"
        reads.append(args)
        return {"rounds": rounds}, None, None

    monkeypatch.setattr(guard, "load_rounds", read)
    monkeypatch.setattr(guard, "write_rounds", lambda common, id_part, data: writes.append(data))
    guard.record_flagged_launch(os.path.realpath(str(G.bridge_dir(repo).parent)), str(repo), NAME, snap)
    return reads, writes


def test_bug039_void_path_a_launch_before_the_snapshot_reads_no_record(tmp_path, monkeypatch):
    """R-042, D-003. enforces: handoff/REFAC-004.md, a characterization of the void path: with a snapshot given, a launch before
    it returns before any read of the record, whose read can raise on what `load_rounds` does not catch."""
    assert void_path_call(tmp_path, monkeypatch, {"taken": "2999-01-01T00:00:00Z"}) == ([], [])


def test_bug039_void_path_no_entry_with_a_snapshot_still_writes(tmp_path, monkeypatch):
    """R-042, D-003. enforces: handoff/REFAC-004.md, a characterization of the void path: with a snapshot given and no entry for the
    round, the record is written back as it was read, no entry gaining a void."""
    reads, writes = void_path_call(tmp_path, monkeypatch, {"taken": ""}, rounds=[{"round": 2, "time": "2000-01-01T00:00:00Z"}])
    assert reads and writes == [{"rounds": [{"round": 2, "time": "2000-01-01T00:00:00Z"}]}]


def test_bug039_void_path_no_entry_without_a_snapshot_writes_nothing(tmp_path, monkeypatch):
    """R-042, D-003. enforces: handoff/REFAC-004.md, a characterization of the void path: with no snapshot, no entry for the round gives
    no write."""
    reads, writes = void_path_call(tmp_path, monkeypatch, None, rounds=[{"round": 2, "time": "2000-01-01T00:00:00Z"}])
    assert reads and writes == []


@pytest.mark.parametrize("entry", [{"round": 1, "time": ""}, {"round": 1, "time": None}, {"round": 1}], ids=["empty", "none", "missing"])
def test_bug039_void_path_an_entry_with_no_time_and_no_snapshot_writes_nothing(tmp_path, monkeypatch, entry):
    """R-042, D-003. enforces: handoff/REFAC-004.md, a characterization of the void path: the round's recorded time is what a call
    with no snapshot voids by, so an entry with an empty or missing time gives no write."""
    reads, writes = void_path_call(tmp_path, monkeypatch, None, rounds=[entry])
    assert reads and writes == []


def test_bug039_void_path_of_two_entries_for_a_round_the_first_decides_and_is_voided(tmp_path, monkeypatch):
    """R-042, D-003. enforces: handoff/REFAC-004.md, a characterization of the void path: of two entries for one round, which the
    guard's own records never hold, the first decides by its time and alone takes the void."""
    early, late = "2000-01-01T00:00:00Z", "2999-01-01T00:00:00Z"
    reads, writes = void_path_call(tmp_path, monkeypatch, None, rounds=[{"round": 1, "time": early}, {"round": 1, "time": late}])
    assert reads and len(writes) == 1
    first, second = writes[0]["rounds"]
    assert first["time"] == early and first.get("flagged_launch"), first
    assert second == {"round": 1, "time": late}


# --- Site 3: premerge's git call ----------------------------------------------------------

def verified_round(tmp_path):
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.verify_ok(repo, NAME)
    return repo


def test_bug039_site3_every_git_command_of_premerge_runs_with_both_switches(tmp_path, monkeypatch, capsys):
    """R-042, D-004 (`p_review_guard` to `ds_checkout`, hooks off). enforces: TASK-043 Done when (3): `cmd_premerge`'s
    `git merge-base --is-ancestor` runs through the guard's git helper, with the hooks folder emptied and
    `core.fsmonitor=false` like every other git command of the guard. Every git process `premerge` starts is watched."""
    repo = verified_round(tmp_path)
    guard = load_guard(monkeypatch)
    started = watch_git(monkeypatch)
    assert guard.cmd_premerge(NAME, str(repo)) == 0, capsys.readouterr().out
    assert any("merge-base" in cmd for cmd in started), started
    for cmd in started:
        assert any(word.startswith("core.hooksPath=") for word in cmd), cmd
        assert "core.fsmonitor=false" in cmd, cmd


def test_bug039_site3_no_git_call_of_the_guard_bypasses_the_helper():
    """R-042, D-004. enforces: TASK-043 Done when (3): no `subprocess.run` of git in `review-guard.py` bypasses the helper,
    the helper's own call site (`_git_proc`) the one exemption and nothing else. A process call outside `_git_proc` must
    name its program as a literal, and that literal is not git; os.system and os.popen appear nowhere."""
    with open(G.PROG, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    in_helper = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_git_proc":
            in_helper = {id(n) for n in ast.walk(node)}
    assert in_helper, "the helper _git_proc is gone"
    helper_calls = 0
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)):
            continue
        owner, name = node.func.value.id, node.func.attr
        assert (owner, name) not in (("os", "system"), ("os", "popen")), "line %d" % node.lineno
        if owner != "subprocess":
            continue
        if id(node) in in_helper:
            helper_calls += 1
            continue
        first = node.args[0] if node.args else None
        assert isinstance(first, ast.List) and first.elts and isinstance(first.elts[0], ast.Constant), "line %d" % node.lineno
        assert first.elts[0].value != "git", "line %d: a git command outside _git_proc" % node.lineno
    assert helper_calls == 1


def test_bug039_site3_negative_premerge_runs_no_planted_hook_or_monitor(tmp_path):
    """R-042, D-004, KP-032. enforces: TASK-043 Done when, the negative case of site 3: `premerge` runs with a planted hook
    and a planted file monitor, each shown not to have run. An invariant (the accept commit names its hand mutation)."""
    repo = verified_round(tmp_path)
    marker = tmp_path / "planted-ran"
    script = "#!/bin/sh\necho ran >> '%s'\nexit 0\n" % marker.as_posix()
    planted = tmp_path / "planted.sh"
    G.put(planted, script)
    os.chmod(str(planted), os.stat(str(planted)).st_mode | stat.S_IXUSR)
    for hook in ("post-index-change", "reference-transaction"):
        G.put(repo / ".git" / "hooks" / hook, script)
        os.chmod(str(repo / ".git" / "hooks" / hook), 0o755)
    G.git(repo, "config", "core.fsmonitor", planted.as_posix())
    os.utime(str(repo / "a.py"), (1700000000, 1700000000))  # so `status` rewrites the index, the event the hook is planted on
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 0, out
    assert not marker.exists(), "a planted program ran during premerge: " + marker.read_text(encoding="utf-8")


def plant_in_the_guard_s_own_folder(repo, tmp_path):
    marker = tmp_path / "planted-ran"
    script = "#!/bin/sh\necho ran >> '%s'\nexit 0\n" % marker.as_posix()
    for hook in ("post-index-change", "reference-transaction"):
        G.put(repo / ".git" / "bridge" / "no-hooks" / hook, script)
        os.chmod(str(repo / ".git" / "bridge" / "no-hooks" / hook), 0o755)
    os.utime(str(repo / "a.py"), (1700000000, 1700000000))
    return marker


@pytest.mark.parametrize("command", ["verify", "premerge"])
def test_bug039_site6_a_hook_planted_in_the_guard_s_folder_never_runs(tmp_path, command):
    """R-042, D-004 (`p_review_guard` to `ds_checkout`, hooks off), KP-032. enforces: TASK-043's r2 brief, Requirement 4 (the
    security audit, round 1, B4): the folder the guard points `core.hooksPath` at lay inside `.git/`, where the reviewer's
    run writes, unchecked. A hook planted at that path runs under neither command."""
    repo = verified_round(tmp_path)
    marker = plant_in_the_guard_s_own_folder(repo, tmp_path)
    if command == "verify":
        G.launched(repo, NAME)
    rc, out = G.guard(repo, command, NAME)
    assert rc == 0, out
    assert not marker.exists(), "a planted program ran during %s: %s" % (command, marker.read_text(encoding="utf-8"))


def test_bug039_site6_the_hooks_folder_lies_outside_the_repository(tmp_path, monkeypatch):
    """R-042, D-004, KP-032. enforces: TASK-043's r2 brief, Requirement 4: `no_hooks_dir` gives an empty folder outside the
    repository, so nothing the reviewer's run writes in the checkout can be in it."""
    repo = G.make_repo(tmp_path)
    guard = load_guard(monkeypatch)
    folder = guard.no_hooks_dir(str(repo / ".git"))
    assert os.path.isdir(folder) and os.listdir(folder) == []
    assert not os.path.normcase(os.path.abspath(folder)).startswith(os.path.normcase(os.path.abspath(str(repo))))


def test_bug039_site6_the_hooks_folder_is_gone_at_exit(tmp_path, monkeypatch):
    """R-042, D-004. enforces: TASK-043's r2 brief, Requirement 4: the fresh folder is removed at the process's exit, so a
    run of the guard leaves nothing in the temporary folder. An invariant (a mutant of the fixed guard shows it strong)."""
    repo = verified_round(tmp_path)
    temp = tmp_path / "temp"
    temp.mkdir()
    for name in ("TEMP", "TMP", "TMPDIR"):
        monkeypatch.setenv(name, str(temp))
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 0, out
    assert os.listdir(str(temp)) == []


# --- Site 5: flags already found when a later git step fails --------------------------------

CLEAN_FAILED = "git clean failed: a file is held open"


def run_verify_with_clean_failing(repo, monkeypatch, failure=None, change_the_guard=None):
    """`verify` through the program's own main, its `git clean` failing, as a file held open makes it fail."""
    guard = load_guard(monkeypatch)
    real_run_git = guard.run_git

    def failing(args, root, common):
        if args[:1] == ["clean"]:
            raise failure or RuntimeError(CLEAN_FAILED)
        return real_run_git(args, root, common)

    monkeypatch.setattr(guard, "run_git", failing)
    if change_the_guard:
        change_the_guard(guard)
    monkeypatch.chdir(str(repo))
    monkeypatch.setattr(sys, "argv", ["review-guard.py", "verify", NAME])
    return guard.main()


@pytest.mark.parametrize("failure", [RuntimeError(CLEAN_FAILED), subprocess.TimeoutExpired("git clean", 120), OSError(CLEAN_FAILED)],
                         ids=["git-failed", "git-timed-out", "os-error"])
def test_bug039_site5_a_git_failure_after_a_flag_keeps_the_flag(tmp_path, monkeypatch, capsys, failure):
    """R-042, D-003. enforces: TASK-043's r2 brief, Requirement 3 (the security audit, round 1, B3): a flag already found when
    a later git step fails, whichever of the three failures `main` reads as CANNOT VERIFY, is printed and voids the launch,
    the exit staying 2, so the next verify, the tree now back and nothing left to find, does not write a mark for it."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.git(repo, "branch", "left-by-the-reviewer")
    assert run_verify_with_clean_failing(repo, monkeypatch, failure) == 2
    out = capsys.readouterr().out
    assert "CANNOT VERIFY" in out and "GATE-INTEGRITY" in out and "left-by-the-reviewer" in out, out
    assert flagged_key(repo) == start_of(repo), G.entry(repo, NAME, 1)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "voided" in out, out
    assert not (G.bridge_dir(repo) / ("verified-%s.json" % NAME)).exists(), out


def test_bug039_site5_negative_a_void_that_cannot_be_written_leaves_the_git_failure_named(tmp_path, monkeypatch, capsys):
    """R-042, D-003. enforces: TASK-043's r3 brief, Requirement 2 (Review A's Should fix 1 and the security audit's A3, round 2):
    the void's own write failing does not replace the git failure, and it says the void was not recorded, so the supervisor
    knows the next verify cannot refuse this launch."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.git(repo, "branch", "left-by-the-reviewer")

    def no_write(guard):
        def failing_write(*_args):
            raise OSError("the record cannot be written")
        monkeypatch.setattr(guard, "write_rounds", failing_write)

    assert run_verify_with_clean_failing(repo, monkeypatch, change_the_guard=no_write) == 2
    out = capsys.readouterr().out
    assert "left-by-the-reviewer" in out and CLEAN_FAILED in out, out
    assert any(line.startswith("review-guard: GATE-INTEGRITY - ") and "not recorded" in line for line in out.splitlines()), out


def test_bug039_site5_negative_a_git_failure_with_no_flag_voids_nothing(tmp_path, monkeypatch, capsys):
    """R-042, D-003. enforces: TASK-043's r2 brief, Requirement 3: a git failure with nothing flagged stays what it was, exit 2
    and no void, and the verify after it goes through. An invariant (a mutant of the fixed guard shows it strong)."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    assert run_verify_with_clean_failing(repo, monkeypatch) == 2
    assert "GATE-INTEGRITY" not in capsys.readouterr().out
    assert "flagged_launch" not in G.entry(repo, NAME, 1), G.entry(repo, NAME, 1)
    G.verify_ok(repo, NAME)


# --- Site 7: the exit line --------------------------------------------------------------------

def test_bug039_site7_an_exit_line_too_long_to_read_is_no_exit(tmp_path):
    """R-042, D-003, D-004 (`ds_run_outputs` to `p_review_guard`, untrusted). enforces: TASK-043's r2 brief, Requirement 5 (the
    security audit, round 1, A3): the early returns now read the `.err` file, and an exit line past int()'s limit must not
    turn a clean flag into a traceback: the flag stands and the launch is voided."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME, exit_code=None)
    add_a_long_exit_line(repo)
    change_the_config(repo)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    assert "Traceback" not in out, out
    assert flagged_key(repo) == start_of(repo), G.entry(repo, NAME, 1)


def test_bug039_site7_a_real_windows_exit_code_is_read(tmp_path):
    """R-042, D-003. enforces: TASK-043's r3 brief, Requirement 3 (Review A's Should fix 2 and the security audit's A1, round 2):
    a crash's exit code on Windows has ten digits (0xC000013A is 3221225786). The last exit line decides, so an earlier exit 0
    does not make a crashed run a reply, and `premerge` refuses it."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    with open(str(repo / "run" / "review" / ("REVIEW-%s.err" % NAME)), "a", encoding="utf-8") as f:
        f.write("bridge-run: exit 3221225786\n")
    G.verify_ok(repo, NAME)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 2 and "3221225786" in out, out


def add_a_long_exit_line(repo):
    with open(str(repo / "run" / "review" / ("REVIEW-%s.err" % NAME)), "a", encoding="utf-8") as f:
        f.write("bridge-run: exit " + "9" * 5000 + "\n")


# --- Site 4: the re-snapshot --------------------------------------------------------------

def test_bug039_site4_a_resnapshot_keeps_the_flag(tmp_path):
    """R-042, D-003 (`flagged_gate_integrity` to `resnapshotted`). enforces: TASK-043 Done when (4): `cmd_snapshot`'s
    replacement of a round's entry keeps `flagged_launch` beside `reply`, `lift`, `lift_line` and `time`, so a flagged round
    taken again counts no reply and spends nothing (found by Review B of PR #116)."""
    repo = flagged_round(tmp_path)
    voided = flagged_key(repo)
    G.snap_ok(repo, NAME)
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)
    G.bump(repo)
    G.snap_ok(repo, NAME)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)


def test_bug039_site4_negative_a_resnapshot_of_an_unflagged_round_gains_no_key(tmp_path):
    """R-042, D-003. enforces: TASK-043's brief, Requirement 7: an entry with no flag gains no new content on a re-snapshot,
    so no other reader of the record sees a change. An invariant (a mutant of the fixed guard shows it strong)."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.snap_ok(repo, NAME)
    assert "flagged_launch" not in G.entry(repo, NAME, 1), G.entry(repo, NAME, 1)


@pytest.mark.parametrize("change_the_tree", [False, True], ids=["same-tree", "changed-tree"])
def test_bug039_site4_negative_a_resnapshot_counts_no_reply_on_either_tree(tmp_path, change_the_tree):
    """R-042, D-003. enforces: TASK-043 Done when, the negative case of site 4: a re-snapshot of a flagged round, on the
    same tree and on a changed one, keeps `flagged_launch` and counts no reply: the round's next snapshot on another tree
    is admitted under its own number, never refused as reviewed."""
    repo = flagged_round(tmp_path)
    voided = flagged_key(repo)
    if change_the_tree:
        G.bump(repo)
    G.snap_ok(repo, NAME)
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    G.bump(repo)
    rc, out = G.guard(repo, "snapshot", NAME)
    assert rc == 0, out
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)


def test_bug039_the_void_lands_on_the_round_flagged_never_on_round_1(tmp_path):
    """R-042, D-003 (`reply_arrived` to `flagged_gate_integrity`), at a later round. enforces: a flag on round 2 voids
    round 2's launch and leaves round 1's replied entry as it stood, and the same launch verified again gets no mark.
    Stage T2's review, round 3, found every other void test flagging round 1 (docs/HARDENING.md, Project end)."""
    repo = G.make_repo(tmp_path)
    G.reviewed(repo, NAME, change=False)
    G.next_second()
    G.bump(repo)
    later = NAME + "-r2"
    G.snap_ok(repo, later)
    G.launched(repo, later)
    first = G.entry(repo, ID, 1)
    assert first.get("reply") == 0, first
    G.git(repo, "branch", "left-by-the-reviewer")
    rc, out = G.guard(repo, "verify", later)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    second = G.entry(repo, ID, 2)
    assert (second.get("flagged_launch") or "").rstrip("Z") == start_of(repo, later), second
    assert second.get("reply") is None, second
    assert G.entry(repo, ID, 1) == first, G.entry(repo, ID, 1)
    rc, out = G.guard(repo, "verify", later)
    assert rc == 1 and "voided by an earlier GATE-INTEGRITY verify" in out, out
    assert "verified mark written" not in out, out
    assert G.entry(repo, ID, 2).get("reply") is None, G.entry(repo, ID, 2)
