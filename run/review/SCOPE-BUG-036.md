# SCOPE - BUG-036: the review guard seeds no Review B round from release B's builder rounds, stamped 2026.10.30b

A fix of a defect found after release B's merge and install, by its trial on the TDP (2026-10-30, the TDP's ISS-016). Its brief is `handoff/BUG-036.md` (spec-packager's fix variant). Pull request #110, branch bug-036 from origin/main e1052e3.

## The increment's Scope and Out of scope (the brief's, quoted)

Scope:
- bridge/cursor-bridge/review-guard.py
- docs/BUILDER_NOTES.md
- handoff/BUG-036-r1-report.md

Out of scope:
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. The governance texts (Merge-Verification-Policy.md, the workflow phase modules, docs/INVENTORY.md, docs/REQUIREMENTS.md, docs/CHANGES.md, docs/debug/) are the supervisor's.
- every file under tests/. Above all, `tests/test_bug036.py` is the supervisor's reproduction: it goes from red to green and is never edited.
- bridge/cursor-bridge/bridge_env.py and bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json, bridge/cursor-bridge/VERSION and bridge/cursor-bridge/CHANGELOG.md: the stamp is the supervisor's step after your run.
- in review-guard.py: every function except `_report_file_rounds` and `_seed_rounds` (a new private helper beside them allowed).

## The commits
- `ce1c67a` checkpoint before BUG-036: the brief and tests 1 to 3 of `tests/test_bug036.py`.
- `518e600` BUG-036, the builder's accept commit: `review-guard.py` (`_release_b_builder_rounds`, `_report_file_rounds`) and the builder's report `handoff/BUG-036-r1-report.md`. `scope-check.py` printed SCOPE CLEAN on it.
- `c6e0fef` and `c9cb904`, the supervisor's:
  - the tests;
  - the stamp (the CHANGELOG entry 2026.10.30b, VERSION, MANIFEST.json from `tools/make-manifest.py`);
  - the records, as at this pull request's merge (ISS-009).

  `scope-check.py` reads that commit's stamp files and `docs/archive/` as drift, because its records list names neither. This is recorded in HARDENING (BUG-036) and expected.

## The tests, written by the supervisor, each with the paragraph it enforces
`tests/test_bug036.py` (its helpers imported from `tests/test_task032_supervisor_guard.py`):
1. `test_bug036_three_builder_rounds_under_release_b_open_review_round_one`: delegation-loop.md step 8 ("<N> the round it opens: one more than the rounds the guard has counted"); Merge-Verification-Policy.md ("review-guard.py, which counts the Review B rounds"). This is the TDP's BUG-004.
2. `test_bug036_one_builder_round_under_release_b_first_snapshot_is_round_one`: the same paragraphs, one builder round.
3. `test_bug036_rounds_before_the_install_still_seeded_rounds_after_it_not`: CHANGELOG 2026.10.30a, Running projects must (the in-flight seed); the mixed increment; another ID's row.
4. `test_bug036_a_lettered_report_of_a_logged_round_seeds_nothing`: 2026.10.30a's "a letter after <N> included".
5. `test_bug036_the_earlier_launchers_builder_rows_still_seed`: the in-flight seed with the earlier launcher's rows. It is a preservation test and passes on the old guard by design.
6. `test_bug036_the_fix_release_entry_stands_above_release_b_with_its_four_parts`: the CHANGELOG header's parts, and the installer's rollback note.

`mutation-run.py --checkpoint ce1c67a` printed `failing` for tests 1 to 4.

`tests/test_release_b_stamp.py`: release B's entry is read by its heading, 2026.10.30a, now that 2026.10.30b stands above it. VERSION and the manifest are still held to the newest heading.

## The mutants file
`run/supervisor/BUG-036-mutants.json` (gitignored; the supervisor's), six mutants:
- m1: the row exclusion dropped;
- m2: another ID's rows counted;
- m3: the earlier launcher's rows read as round 1;
- m4: round off by one;
- m5: the kind check dropped, expected to survive;
- m6: the bool check dropped, expected to survive.

The run of 2026-10-30T13:11:02Z killed 4 and 2 survived as expected, with no error (exit 0). The reasons m5 and m6 survive are in the file and in HARDENING.

## Expected files in the diff beyond the Scope
The supervisor's:
- tests/test_bug036.py and tests/test_release_b_stamp.py;
- bridge/cursor-bridge/CHANGELOG.md, VERSION and MANIFEST.json (the stamp);
- docs/PROJECT_STATUS.md, docs/REQUIREMENTS.md, docs/INVENTORY.md, docs/HARDENING.md and docs/archive/STATUS_HISTORY.md (the records);
- run/review/ (this file and the round's diff and assumptions file, removed before the merge).

The bookkeeping: handoff/BUG-036-r1-report.md. No docs/BUILDER_NOTES.md line was written.

## The review guard for this round
The installed guard is 2026.10.30a, which has this very defect: it would seed this increment's own report `handoff/BUG-036-r1-report.md` as a replied round. So `rounds-BUG-036.json` was written by hand before the first snapshot, as `{"id": "BUG-036", "rounds": []}`, the remedy 2026.10.30a's entry gives, since no Review B has replied. This round is round 1, below the ceiling, with no class line.

## Checks run
- The full suite with GITHUB_REF=refs/pull/110/merge, GITHUB_BASE_REF=main and GITHUB_EVENT_NAME=pull_request: 3268 passed, 40 skipped.
- The security auditor: PASS, three advisories (HARDENING).
- Review A:
  - round 1: REJECT on the mutants file only (m4's expect_fail), plus one Should fix and its Considers, all taken;
  - confirming read: APPROVE.
- secret-sentinel: PASS. invisible-check: OK. The path scan: 0 hits.
- inventory-check (status 11,932 characters), completion-check --mode plan and workflow-check --status: OK.
