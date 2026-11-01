# SCOPE - TASK-036: the pitfalls (R-054), and D-004's first deviation closed by the corrected text (pull request #117)

Supervisor-authored governance text in release T's stage T1 (docs/BUILD_PLAN.md, "### TASK-036", and the release T constraints paragraph above stage T1); no builder ran, so there is no brief and no builder report. The diagram redraw was made by diagram-specialist's as-built variant. No program changes.

## Scope (the plan's, quoted)
bridge/cursor-bridge/Known-Pitfalls.md; bridge/cursor-bridge/MANIFEST.json; docs/diagrams/D-004-context-dfd.md; docs/diagrams/DEVIATIONS.md; tests/test_release_t_pitfalls.py; tests/test_a5_followups.py (re-taken only if KP-061's heading changes; it did not, so it is unchanged).

## What the text must do (the plan's Done when, in short)
- Known-Pitfalls.md, each entry in the catalogue's four-part shape (misconception or mistake, how it surfaced, the correction, where it applies):
  - KP-061's outcome line corrected (D5).
  - KP-063 to KP-065 (D13).
  - KP-066 to KP-070 and the KP-058 addendum (T27). KP-067 is the entry review-guard.py's empty-input refusal already cites.
  - KP-052 corrected (T13).
  - KP-071 to KP-074 (P21).
  - KP-038 narrowed to what the code does: the stores under the profile root are not found by default; a store reached through APPDATA or LOCALAPPDATA is, until a probed release redirects them.
- D-004's note on the agents' edge to the owner's profile stores is drawn as built, and DEVIATIONS.md's row for it is removed (conventions §8, second case: the design corrected to the code).
- MANIFEST regenerated.
- The increment's first P7 suite launch, in the documented `--key-file` form, is observed and recorded in the design's host table.

## The tests the supervisor wrote first
tests/test_release_t_pitfalls.py names R-054 and D-004. It enforces docs/REQUIREMENTS.md R-054 and TASK-036's Done when, one test per item label of R-054's row:
- `test_r054_d5_kp061_outcome_line_corrected` (D5)
- `test_r054_d13_kp063_to_kp065` (D13)
- `test_r054_t27_kp066_to_kp070_and_the_kp058_addendum` (T27)
- `test_r054_t13_kp052_corrected` (T13)
- `test_r054_p21_kp071_to_kp074` (P21)
- `test_r054_kp038_narrowed_and_d004_first_deviation_closed` (KP-038 with D-004's edge and DEVIATIONS.md)

Each pins an entry's heading once, its number once, one sentence, and the four parts. All six were shown failing on the checkpoint 46caed5 by `mutation-run.py --checkpoint`; the per-test lines are in the accept commit's message.

The mutants file is run/supervisor/TASK-036-mutants.json. It holds 13 text mutants, each undoing a pinned sentence or heading, each with the test that must fail; m12 and m13 were added after Review A's round 2. Its run's result is under "Before this round". The file is gitignored and not in the diff. Its mutants, by id, with the text each replaces (all in bridge/cursor-bridge/Known-Pitfalls.md except m9):
- m1: KP-061's "and the result was waited for and read, not lost"
- m2: KP-061's Mistake label
- m3: KP-063's "every failed or retried attempt counted at its price"
- m4: KP-067's heading number
- m5: KP-058's Addendum label
- m6: KP-052's "the Write and Edit tools included"
- m7: KP-072's "a seed names what writes its files before and after the release that seeds it"
- m8: KP-038's "a store a tool reaches through `APPDATA` or `LOCALAPPDATA` still is"
- m9: D-004's "which stay the owner's until a probed release redirects them (KP-038)" (docs/diagrams/D-004-context-dfd.md)
- m10: KP-038's "until a probed release redirects them into the skeleton below"
- m11: KP-058's Mistake label
- m12: KP-038's Mistake label
- m13: KP-038's "a program item for the maintainer"

## Bookkeeping and records expected in the diff
- docs/REQUIREMENTS.md: R-054 built, its Evidence per item label.
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009), and the six lines it replaces archived word for word in docs/archive/STATUS_HISTORY.md.
- project.json's stage.
- docs/INVENTORY.md: one cross-reference fixed, carried from Review B of PR #116.
- docs/HARDENING.md: the APPDATA lead's note, and a TASK-036 section with two leads on text outside every release T Scope.
- docs/DESIGN.md: the host table's `--key-file` row.

## Before this round
- Full suite with this pull request's variables, in the documented form `bridge-run.py --limit auto --key-file <a file outside the Workspace> --kind test -- python -m pytest -q tests`: 3283 passed, 40 skipped. It ran with no prompt and no refusal (run/agent/TASK-036-suite.out, not in the diff).
- Review A (diff-reviewer), round 1: REJECT, Blocking 1 / Should fix 5 / Consider 6.
  - Blocking: the key-file launch was recorded nowhere. It is now in the host-table row and the records commit.
  - Should fix and Consider: the text fixes are in "TASK-036: Review A's round 1 findings on the catalogue's text taken". The two out-of-Scope findings are HARDENING leads.
- Review A, round 2 (the delta since the first records commit): APPROVE, Blocking 0 / Should fix 1 / Consider 2.
  - Should fix: R-052's assumption paragraph in docs/DESIGN.md disagreed with the new `--key-file` row. It is reworded in "Records: TASK-036, Review A's round 2 finding on R-052's assumption taken".
  - Consider 1: mutants m12 and m13 were added.
  - Consider 2: KP-063's source was checked; the evaluation of 2026-10-18, section 2 F, names the leftover server.
- These were supervisor fixes made before this snapshot, so they are not rounds.
- Mutation run on the final text (2026-11-01T13:50:24Z): 13 run, 13 killed, 0 survived, 0 not applied, 0 errors, exit 0. Before it, no duplicates were cut and the estimate was about 14 processes (one tests list, no launches).

This is Review B's round 1, below the ceiling. Release T's later increments (TASK-037 to TASK-045) are later work, not this diff's defect: TASK-041 rewrites KP-061's command line and the loop's launch commands, and TASK-043 fixes the review guard.
