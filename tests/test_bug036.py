"""Supervisor-side reproduction tests of BUG-036 (R-042); written by the supervisor; the builder reads and runs them, never edits them.

Release B's trial (the TDP, 2026-10-30, its ISS-016): the review guard refused BUG-004's first Review B, `round 1 is
off the count (current 3)`. With no rounds-<ID>.json, `_seed_rounds` takes the highest <N> of the tracked
handoff/<ID>-r<N>-report.md files and seeds that many rounds as replied (reply 0). Under release B every builder round
writes such a report, so an increment begun under it has its first Review B pushed up by its builder rounds: one
builder round makes the first snapshot `<ID>-r2`, three make it `<ID>-r4`, above the ceiling. The seeding is for an
increment in flight at the install (CHANGELOG 2026.10.30a, Running projects must: "an increment in flight at the
install ... the ID's first snapshot seeds it"; docs/INVENTORY.md, the R-042 row: "seeds an increment in flight from its
letter snapshots and report files"). A builder round the installed launcher logged (a runs.jsonl builder row carrying
`brief` and `round`) is a round of release B, which the guard never counted as a Review B round. The helpers are
tests/test_task032_supervisor_guard.py's, imported, so the fixtures are the same.
"""
import test_release_b_stamp as S
import test_task032_supervisor_guard as G

FIX_RELEASE = "2026.10.30b"


def _repo_with_reports(tmp_path, id_part, branch, report_rounds):
    """A checkout on `branch` with handoff/<id>.md and handoff/<id>-r<N>-report.md tracked for each N."""
    files = {"handoff/%s.md" % id_part: "# %s\n" % id_part}
    for n in report_rounds:
        files["handoff/%s-r%d-report.md" % (id_part, n)] = "report %d\n" % n
    return G.make_repo(tmp_path, branch=branch, files=files)


def _builder_rows(repo, id_part, branch, logged_rounds, offset=-600):
    """runs.jsonl builder rows as release B's launcher writes them: brief <id>, round N, brief_name <id> or <id>-rN."""
    lines = []
    for i, n in enumerate(logged_rounds):
        name = id_part if n == 1 else "%s-r%d" % (id_part, n)
        lines.append(G.launcher_line(id_part, branch, brief_bytes=("brief %d\n" % n).encode("utf-8"), round_n=n,
                                     brief_name=name, offset=offset + i))
    G.append_log(repo, *lines)


def test_bug036_three_builder_rounds_under_release_b_open_review_round_one(tmp_path):
    """R-042. enforces: bridge/cursor-bridge/workflow/phases/delegation-loop.md step 8: "<N> the round it opens: one
    more than the rounds the guard has counted for the increment", and Merge-Verification-Policy.md: review-guard.py
    "counts the Review B rounds". The TDP's BUG-004: three builder rounds logged by release B's launcher, three report
    files, no Review B yet and no rounds file. `snapshot BUG-004-r4` is off the count (current 0); `snapshot
    BUG-004-r1` is admitted, and the rounds record holds round 1 alone, not seeded."""
    repo = _repo_with_reports(tmp_path, "BUG-004", "bug-004", (1, 2, 3))
    _builder_rows(repo, "BUG-004", "bug-004", (1, 2, 3))
    G.bump(repo)
    G.refuse_and_nothing(repo, "BUG-004-r4", G.REFUSED, "round 4 is off the count (current 0)")
    G.snap_ok(repo, "BUG-004-r1")
    data = G.rounds(repo, "BUG-004")["rounds"]
    assert [r["round"] for r in data] == [1], data
    assert not data[0].get("seeded"), data


def test_bug036_one_builder_round_under_release_b_first_snapshot_is_round_one(tmp_path):
    """R-042. enforces: delegation-loop.md step 8 (as above): one builder round logged by release B's launcher and its
    report file; the first snapshot under the bare name `TASK-040` is admitted as round 1, never refused with
    `round 1 is reviewed: write TASK-040-r2`."""
    repo = _repo_with_reports(tmp_path, "TASK-040", "task-040", (1,))
    _builder_rows(repo, "TASK-040", "task-040", (1,))
    G.bump(repo)
    G.snap_ok(repo, "TASK-040")
    data = G.rounds(repo, "TASK-040")["rounds"]
    assert [r["round"] for r in data] == [1], data
    assert not data[0].get("seeded"), data


def test_bug036_rounds_before_the_install_still_seeded_rounds_after_it_not(tmp_path):
    """R-042. enforces: CHANGELOG 2026.10.30a, Running projects must ("an increment in flight at the install ... the
    ID's first snapshot seeds it ... the highest <N> of a tracked handoff/<ID>-r<N>-report.md"): an increment in flight
    at the install, built twice before it (report files r1 and r2, no launcher row with a brief) and once after it
    (report file r3 and release B's builder row for round 3). Rounds 1 and 2 are seeded as replied; round 3 is not,
    so `snapshot TASK-041-r3` is admitted as the next round (never `round 3 is reviewed: write TASK-041-r4`) and is
    recorded unseeded. A builder row of another ID's round 2, on its own branch, seeds nothing away from TASK-041."""
    repo = _repo_with_reports(tmp_path, "TASK-041", "task-041", (1, 2, 3))
    _builder_rows(repo, "TASK-041", "task-041", (3,))
    G.append_log(repo, G.launcher_line("TASK-099", "task-099", round_n=2, brief_name="TASK-099-r2", offset=-300))
    G.bump(repo)
    G.snap_ok(repo, "TASK-041-r3")
    data = sorted(G.rounds(repo, "TASK-041")["rounds"], key=lambda r: r["round"])
    assert [r["round"] for r in data] == [1, 2, 3], data
    assert all(r.get("seeded") is True and r.get("reply") == 0 for r in data[:2]), data
    assert not data[2].get("seeded"), data[2]


def test_bug036_a_lettered_report_of_a_logged_round_seeds_nothing(tmp_path):
    """R-042. enforces: CHANGELOG 2026.10.30a ("a letter after <N> included (handoff/<ID>-r<N>b-report.md)") read with
    delegation-loop.md step 8 (as above): a lettered report is its round's, so handoff/TASK-042-r1-report.md and
    handoff/TASK-042-r1b-report.md beside release B's builder row for round 1 seed nothing, and the first snapshot
    `TASK-042` is admitted as round 1, unseeded (the builder's report, Assumed, not verified, item 1)."""
    files = {"handoff/TASK-042.md": "# TASK-042\n", "handoff/TASK-042-r1-report.md": "report 1\n",
             "handoff/TASK-042-r1b-report.md": "report 1b\n"}
    repo = G.make_repo(tmp_path, branch="task-042", files=files)
    _builder_rows(repo, "TASK-042", "task-042", (1,))
    G.bump(repo)
    G.snap_ok(repo, "TASK-042")
    data = G.rounds(repo, "TASK-042")["rounds"]
    assert [r["round"] for r in data] == [1] and not data[0].get("seeded"), data


def test_bug036_the_earlier_launchers_builder_rows_still_seed(tmp_path):
    """R-042. enforces: CHANGELOG 2026.10.30a, Running projects must (as above): the launcher before release B logged
    builder rows with no `brief` and no `round`; such a row is not release B's, so an increment in flight at the install
    with one such row and report file r1 is seeded with round 1 as replied, and `snapshot TASK-043-r2` is admitted as
    the next round (the builder's report, Assumed, not verified, item 2). It passes on the old guard by design: it pins
    the in-flight seed the fix keeps, and kills a fix that reads a row without `brief` or `round` as round 1."""
    repo = _repo_with_reports(tmp_path, "TASK-043", "task-043", (1,))
    row = {"id": G.stamp(-900) + "Z", "kind": "builder", "head": "cursor-agent", "model": None, "branch": "task-043",
           "limit": 7200, "seconds": 12, "exit": 0, "healthy": None, "pid": 4242, "child_pid": 4243}
    G.append_log(repo, G.json.dumps(row) + "\n")
    G.bump(repo)
    G.snap_ok(repo, "TASK-043-r2")
    data = sorted(G.rounds(repo, "TASK-043")["rounds"], key=lambda r: r["round"])
    assert [r["round"] for r in data] == [1, 2], data
    assert data[0].get("seeded") is True and data[0].get("reply") == 0, data
    assert not data[1].get("seeded"), data[1]


def test_bug036_the_fix_release_entry_stands_above_release_b_with_its_four_parts():
    """R-042. enforces: bridge/cursor-bridge/CHANGELOG.md's header ("Each entry has three parts ... A release with new
    mechanisms also names its field acceptance"): the fix release 2026.10.30b is VERSION's and the newest heading,
    directly above release B's 2026.10.30a; its entry holds What changed, Running projects must, If rolled back and
    Field acceptance, each on a line of its own, in order, every item phase-marked; it names the seed's rule and the
    hand seed a rollback needs; and bridge-install.py's rolled_back_note for a rollback to 2026.10.30a holds its items."""
    found = S.headings()
    assert found.index(FIX_RELEASE) + 1 == found.index(S.RELEASE_B), found[:3]
    assert found[0] == S.version() and FIX_RELEASE <= found[0], "the fix release, or a later one, is VERSION's: %s" % found[:3]
    body = S.entry(FIX_RELEASE)
    lines = body.split("\n")
    at = [lines.index(p) for p in S.PARTS]
    assert at == sorted(at), at
    for p in S.PARTS:
        assert body.count(p) == 1 and [l for l in S.part(body, p) if l.startswith("- ")], p
    S.marks_are_phases([l for l in S.part(body, "**Running projects must**") if l.strip()])
    rolled = [l for l in S.part(body, "**If rolled back**") if l.startswith("- ")]
    S.marks_are_phases(rolled)
    joined = S.flat(body)
    for words in ("`review-guard.py`; BUG-036", "`brief` is the ID and whose `round` is `<N>`",
                  "`{\"id\": \"<ID>\", \"rounds\": []}`", "`/calibrate-bridge` before the next increment"):
        assert words in joined, words
    note, ok = S.load(S.INSTALL, "bridge_install_for_bug036").rolled_back_note(S.CHANGELOG, FIX_RELEASE, S.RELEASE_B)
    assert ok and "## " + FIX_RELEASE in note and "## " + S.RELEASE_B not in note, note[:200]
    for item in rolled:
        assert item in note, item[:60]
