"""Supervisor-side reproduction tests of BUG-041 (R-042; D-003); written by the supervisor; the builder reads and runs them, never edits them.

A snapshot deleted after it was taken, its hash copy standing outside the checkout, reads as a snapshot never taken: `verify`
exits 2 with no flag and no void, and nothing says the guard's own record was removed (docs/debug/BUG-041.md). It is the
snapshot rewritten by another route, and takes that return. The helpers are tests/test_task032_supervisor_guard.py's.
"""
import os
import subprocess
import sys

import test_task032_supervisor_guard as G
from test_bug039 import load_guard

NAME = "TASK-001"
ID = "TASK-001"


def snapshot_file(repo):
    return G.bridge_dir(repo) / ("review-%s.json" % NAME)


def mark_file(repo):
    return G.bridge_dir(repo) / ("verified-%s.json" % NAME)


def premerge_records(repo):
    folder = G.bridge_dir(repo) / "premerge"
    return sorted(os.listdir(str(folder))) if folder.is_dir() else []


def snap_noting_the_hash_copy(repo):
    """The snapshot taken, and the name of the hash copy it wrote in the folder other tests' copies share."""
    before = set(G.hash_files())
    G.snap_ok(repo, NAME)
    written = [n for n in set(G.hash_files()) - before if n.endswith("-%s.sha256" % NAME) and "-rounds-" not in n]
    assert len(written) == 1, written
    return written[0]


def start_of(repo):
    with open(str(repo / "run" / "review" / ("REVIEW-%s.err" % NAME)), encoding="utf-8") as f:
        return f.readline().split("started ")[1].strip().rstrip("Z")


def test_bug041_a_deleted_snapshot_is_a_flag_and_voids_the_launch(tmp_path):
    """R-042, D-003 (`reply_arrived` to `flagged_gate_integrity`). enforces: handoff/BUG-041.md, Requirement 1 (the security audit's
    A1 of TASK-043's round 3): the snapshot deleted, its hash copy standing, is GATE-INTEGRITY, exit 1, naming the deletion, with
    no traceback; the launch is voided, no reply counted, no mark, and round 1 may be taken again on a changed tree."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    os.remove(str(snapshot_file(repo)))
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out and "the snapshot was deleted" in out, out
    assert "Traceback" not in out, out
    entry = G.entry(repo, ID, 1)
    assert (entry.get("flagged_launch") or "").rstrip("Z") == start_of(repo), entry
    assert entry.get("reply") is None, entry
    assert not mark_file(repo).exists(), out
    G.bump(repo)
    G.snap_ok(repo, NAME)


def test_bug041_negative_a_deleted_snapshot_restores_nothing_and_runs_no_git(tmp_path, monkeypatch, capsys):
    """R-042, D-003, KP-032. enforces: handoff/BUG-041.md, Requirement 1: as at the snapshot rewritten, with no baseline nothing is
    restored and no git command runs once the deletion is read, as the printed line says: every git process started from
    `snapshot_rewritten` on is watched, and a branch left behind still stands for the supervisor to read."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.git(repo, "branch", "left-by-the-reviewer")
    os.remove(str(snapshot_file(repo)))
    guard = load_guard(monkeypatch)
    started = []
    real_run, real_rewritten = subprocess.run, guard.snapshot_rewritten

    def watching(cmd, *args, **kwargs):
        if cmd and cmd[0] == "git":
            started.append(list(cmd))
        return real_run(cmd, *args, **kwargs)

    def rewritten_then_watch(*args):
        del started[:]
        return real_rewritten(*args)

    monkeypatch.setattr(guard.subprocess, "run", watching)
    monkeypatch.setattr(guard, "snapshot_rewritten", rewritten_then_watch)
    monkeypatch.chdir(str(repo))
    monkeypatch.setattr(sys, "argv", ["review-guard.py", "verify", NAME])
    assert guard.main() == 1
    out = capsys.readouterr().out
    assert "NOT restored" in out and "no git command" in out, out
    assert started == [], started
    assert "left-by-the-reviewer" in G.git(repo, "branch", "--list", "left-by-the-reviewer"), out


def test_bug041_premerge_refuses_a_deleted_snapshot_as_a_flag(tmp_path):
    """R-042, D-003. enforces: handoff/BUG-041.md, Requirement 2: a round verified and then its snapshot deleted: `premerge` is
    GATE-INTEGRITY, exit 1, no traceback and no record of the head, so the permission guard refuses the merge."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.verify_ok(repo, NAME)
    os.remove(str(snapshot_file(repo)))
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    assert "Traceback" not in out, out
    assert premerge_records(repo) == [], out


def test_bug041_negative_the_voided_launch_stays_voided_under_the_next_snapshot(tmp_path):
    """R-042, D-003. enforces: handoff/BUG-041.md, Requirement 1: the route the audit reproduced: the snapshot deleted, then taken
    again on the same tree. The launch it flagged is admitted by neither `verify` nor `premerge`: no later snapshot launders it."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    os.remove(str(snapshot_file(repo)))
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1, out
    G.snap_ok(repo, NAME)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "voided" in out, out
    assert not mark_file(repo).exists(), out
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 2 and "no verified mark" in out, out


def test_bug041_negative_a_launch_before_the_round_is_not_voided(tmp_path):
    """R-042, D-003. enforces: handoff/BUG-041.md, Requirement 1: the void reads the round's recorded time, as at the snapshot
    rewritten: an `.err` from before the round is another launch's, and stays unvoided."""
    repo = G.make_repo(tmp_path)
    G.launched(repo, NAME, offset=-3600)
    G.snap_ok(repo, NAME)
    os.remove(str(snapshot_file(repo)))
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out and "NOT restored" in out, out
    assert "flagged_launch" not in G.entry(repo, ID, 1), G.entry(repo, ID, 1)


def test_bug041_negative_a_snapshot_never_taken_stays_a_cannot_verify(tmp_path):
    """R-042, D-003. enforces: handoff/BUG-041.md, Requirement 3, an invariant: no snapshot and no hash copy is a snapshot never
    taken: CANNOT VERIFY, exit 2, no flag, under `verify` and `premerge`."""
    repo = G.make_repo(tmp_path)
    for command in ("verify", "premerge"):
        rc, out = G.guard(repo, command, NAME)
        assert rc == 2 and "no snapshot" in out, out
        assert "GATE-INTEGRITY" not in out, out


def test_bug041_negative_the_snapshot_and_its_copy_both_gone_stays_a_cannot_verify(tmp_path):
    """R-042, D-003. enforces: handoff/BUG-041.md, Requirement 3, an invariant and a stated limit: the hash copy lies outside the
    checkout, so with both gone the guard cannot tell a deletion from a snapshot never taken: CANNOT VERIFY, exit 2, no mark."""
    repo = G.make_repo(tmp_path)
    copy = snap_noting_the_hash_copy(repo)
    G.launched(repo, NAME)
    os.remove(str(snapshot_file(repo)))
    os.remove(os.path.join(G.hash_dir(), copy))
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 2 and "no snapshot" in out, out
    assert not mark_file(repo).exists(), out


def test_bug041_negative_a_standing_snapshot_is_unchanged(tmp_path):
    """R-042, D-003. enforces: handoff/BUG-041.md, Requirement 3, an invariant: a snapshot in place, its hash matching, verifies
    and premerges as before: the fix reads the hash copy only where the snapshot file is gone."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.verify_ok(repo, NAME)
    assert mark_file(repo).exists()
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 0 and len(premerge_records(repo)) == 1, out
