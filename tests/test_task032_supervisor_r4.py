"""Supervisor-side acceptance tests of TASK-032's round 4 (R-042); written by the supervisor; the builder reads and runs them, never edits them.

Two blocking-class defects found after round 3: an identical-bytes relaunch counted as a new round when the brief
name's first logged run had other bytes (Review A, N1: behaviour against the brief), and a reviewed round re-read
without limit when `verify` never ran (the security audit: a defeated safety mechanism). The helpers are those of
the two supervisor files of round 3, imported, so the fixtures are the same.
"""
import test_task032_supervisor_guard as G
import test_task032_supervisor_launcher as L


def test_task032_r4_identical_relaunch_after_a_revision_adds_no_round(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (b): "identical bytes relaunching freely (KP-038's exit 0
    with no work done) and any other exit leaving the name open", and the launcher's round "so that an identical-bytes
    relaunch adds no round". TASK-001 and TASK-001-r2 completed; TASK-001-r3 ran with bytes v1 and exited 1, was
    revised to v2 (allowed after a failed exit), and v2 ran and exited 0 with no work done; the relaunch of v2 with
    identical bytes runs as round 3, never refused as a round 4."""
    lab = L.Lab(tmp_path)
    L.write_row(lab, "TASK-001", 0)
    L.write_row(lab, "TASK-001-r2", 0)
    v1 = L.write_brief(lab.root, "TASK-001-r3", tag="v1")
    L.write_row(lab, "TASK-001-r3", 1, brief_sha=L.sha(v1))
    v2 = L.write_brief(lab.root, "TASK-001-r3", tag="v2")
    L.write_row(lab, "TASK-001-r3", 0, brief_sha=L.sha(v2))
    L.check_row(L.assert_ran(L.launch(lab, L.build("TASK-001-r3"))), "TASK-001", 3, v2)


def test_task032_r4_identical_relaunch_of_a_revised_lifted_brief_allowed(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (b): a later, different brief whose class line repeats a
    recorded text refused, "an identical-bytes relaunch of the same brief name excepted, since it adds no round
    (KP-038)", and handoff/TASK-032-r2.md R8 (whatever the earlier run's exit). Three rounds completed; TASK-001-r4
    ran with a class line (v1) and exited 1; it was revised to v2 with another class line's text and ran, exit 0; the
    identical relaunch of v2 runs, lifted by its own line."""
    lab = L.Lab(tmp_path)
    L.three_completed(lab)
    line1 = "Blocking class: behaviour - the first finding"
    line2 = "Blocking class: behaviour - the revised finding"
    v1 = L.write_brief(lab.root, "TASK-001-r4", extra=line1 + "\n", tag="v1")
    L.write_row(lab, "TASK-001-r4", 1, brief_sha=L.sha(v1), lift="class", lift_line=line1)
    v2 = L.write_brief(lab.root, "TASK-001-r4", extra=line2 + "\n", tag="v2")
    L.write_row(lab, "TASK-001-r4", 0, brief_sha=L.sha(v2), lift="class", lift_line=line2)
    L.check_row(L.assert_ran(L.launch(lab, L.build("TASK-001-r4"))), "TASK-001", 4, v2, lift="class", lift_line=line2)


def test_task032_r4_a_reply_never_verified_still_spends_the_round(tmp_path):
    """R-042 ("a Review B read that review-guard.py snapshot <ID>-r<N> opens, a round spent when its reply arrived").
    enforces: docs/BUILD_PLAN.md TASK-032 clause (c): a re-snapshot of round <N> "is refused once it has a reply on
    another tree", the reply being "the Review B run's exit from the .err file; a reply is one with exit 0". Round 1
    is snapshotted, its Review B run ends with exit 0 after the snapshot, and verify is never run; a snapshot of a
    changed tree under the same name is refused as reviewed and writes nothing, and the next round opens."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, "TASK-001")
    G.launched(repo, "TASK-001", exit_code=0)
    G.bump(repo)
    G.refuse_and_nothing(repo, "TASK-001", G.REFUSED, "round 1 is reviewed: write TASK-001-r2")
    G.snap_ok(repo, "TASK-001-r2")


def test_task032_r4_a_failed_or_flagged_unverified_run_spends_nothing(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (c) ("a reply is one with exit 0"; the relaunch of a failed
    launch allowed) and handoff/TASK-032-r2.md R11 (a flagged review spends no round). An unverified run that ended
    with exit 1 leaves the round open; and a run with exit 0 whose verify ended GATE-INTEGRITY leaves it open too, so
    a snapshot of a changed tree under the same name is allowed in both cases."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, "TASK-001")
    G.launched(repo, "TASK-001", exit_code=1)
    G.bump(repo)
    G.snap_ok(repo, "TASK-001")
    G.launched(repo, "TASK-001", offset=2, exit_code=0)
    G.git(repo, "branch", "left-by-the-reviewer")
    rc, out = G.guard(repo, "verify", "TASK-001")
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    if "left-by-the-reviewer" in G.git(repo, "branch", "--list", "left-by-the-reviewer"):
        G.git(repo, "branch", "-D", "left-by-the-reviewer")
    G.bump(repo)
    G.snap_ok(repo, "TASK-001")
