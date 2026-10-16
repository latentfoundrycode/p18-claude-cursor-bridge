# SCOPE-TASK-006f — the workflow check (PR #23), review round 6

The diff: `run/review/REVIEW-TASK-006f.diff` (`git diff origin/main...HEAD`, main at 4d0f77b). The brief: `handoff/TASK-006.md` (in the diff, read it whole). The builder: grok-4.7-medium, one round (run 2026-10-16T18:17:36Z); its report `handoff/TASK-006-r1-report.md`.

## Round 6: what changed since round 5's reviewed head (f90672d)
Round 5: Review A APPROVE (0/0/3), Review B REJECT (1/0/0), the security auditor PASS with 4 advisories; the disposition is in docs/DESIGN_CRITIQUE.md, "TASK-006 round 5 — disposition". `run/review/DELTA-TASK-006f.diff` (`git diff f90672d HEAD`, review files left out) shows exactly what changed:
- 884f5c3 — round 5's review files removed.
- 24fd98f — checkpoint: the corrections brief `handoff/TASK-006-r6.md` (R6-1 a table row loses exactly one pipe at each end; R6-2 lines end only at line feeds; the earlier briefs still hold except where it says otherwise), the supervisor's tests (11 failed against round 5's program) and a pass-root block pinning that a backtick in a tilde fence's info string still opens it (Review A's test gap; a guard).
- fa93a61 — the builder's round 6 (run 2026-10-16T21:05:50Z): workflow-check.py and the manifest; its report `handoff/TASK-006-r6-report.md`; a line in docs/BUILDER_NOTES.md.
- 6da2352 — the supervisor's two tests added after the run, for R6-2's split in parse_table and in the status check (each fails against 24fd98f's program); and the checkpoint's parametrize line restored to escape sequences where the editing tool had written raw U+2028 and U+2029.
- e1433dc — records: round 5's grades and disposition; HARDENING's container-block line (list items, block quotes, any HTML block), which both Review A and the auditor graded for recording.
Mutation driver (`run/supervisor/mutate_workflow_check.py`, not in the diff): 79 mutants, all killed (five added for round 6: every edge pipe stripped, and splitting at every line break in each of the three places, and the backtick rule applied to tilde info strings). tests/test_workflow_check.py 125 passed, 1 skipped (the POSIX-only test, run on CI's ubuntu leg); full suite 1077 passed, 21 skipped. The workflow does not change; the pin is unchanged.

## Round 5: what changed since round 4's reviewed head (d093d90)
Round 4: Review A APPROVE (0/0/2), Review B APPROVE (0/0/0), the security auditor PASS with 2 advisories. Review A's Consider 1 and the auditor's advisory 2 named the same fence defect, so it blocked (convergence); the disposition is in docs/DESIGN_CRITIQUE.md, "TASK-006 round 4 — disposition". `run/review/DELTA-TASK-006e.diff` (`git diff d093d90 HEAD`, review files left out) shows exactly what changed:
- e8cb8b4 — round 4's review files removed.
- 09dd175 — checkpoint: the corrections brief `handoff/TASK-006-r5.md` (R5-1 a layer path examined with `os.lstat`, an error other than a missing path stops the check; R5-2 one `os.lstat` link rule on every Python, no `isjunction`; R5-3 fences as CommonMark reads them; the earlier briefs still hold except where it says otherwise), the supervisor's tests (round 4's two `is_link` branch tests replaced by one lstat rule run with `isjunction` present and absent; new tests for R5-1 to R5-3; 14 failed against round 4's program), four fail fixtures (`fence-longer-opening`, `fence-info-string-not-closing`, `fence-backtick-in-info`, `fence-close-trailing-space`) and tilde fences added to `pass/traits/installable.md`.
- ae934f6 — the builder's round 5 (run 2026-10-16T20:34:18Z): workflow-check.py and the manifest; its report `handoff/TASK-006-r5-report.md`; a line in docs/BUILDER_NOTES.md.
- fcef06f — the supervisor's fixture change after the run: the backtick line inside the pass root's four-tilde fence is now four backticks, because the driver's `other character closes` mutant survived on a shorter line; the test's precondition and the fixture README follow.
- 23f1436 — records: round 4's grades and disposition; HARDENING: the `lexists` line removed (settled by R5-1), the version-dependence line rewritten (settled by R5-2), and a line for fences inside HTML `<pre>` blocks (not taken).
Mutation driver (`run/supervisor/mutate_workflow_check.py`, not in the diff): 74 mutants, all killed (round 4's re-anchored to round 5's code; the two `isjunction`-branch mutants replaced by `isjunction consulted`; new ones for R5-1 and each R5-3 rule). One mutant was left out on purpose: removing the `S_ISLNK` test cannot be killed on Windows, where every symbolic link is also a reparse point; the link tests on CI's ubuntu leg cover it. tests/test_workflow_check.py 112 passed, 1 skipped (the POSIX-only unreadable-folder test, run on CI's ubuntu leg); full suite 1064 passed, 21 skipped. The workflow does not change; the pin is unchanged.

## Round 4: what changed since round 3's reviewed head (0ed512b)
Round 3: Review A REJECT (1/0/3), Review B APPROVE (0/0/0), the security auditor PASS with 2 advisories; the findings and their disposition are in docs/DESIGN_CRITIQUE.md, "TASK-006 round 3 — disposition". `run/review/DELTA-TASK-006d.diff` (`git diff 0ed512b HEAD`, review files left out) shows exactly what changed:
- cc74754 — round 3's review files removed.
- c0b2a8a — checkpoint: the corrections brief `handoff/TASK-006-r4.md` (R4-1 a missing path is not a link and a missing layer is skipped, R4-2 one error rule on both branches of `is_link`, R4-3 fences indented up to three spaces; `TASK-006.md`, `-r2.md` and `-r3.md` still hold except where it says otherwise), the supervisor's tests extended (18 new: 10 failed against round 3's program, 8 guards held), and four fixtures (`fail/fence-indented-close`, `fail/fence-four-spaces`, `fail/form-indented-fence-open`, and an indented fence pair added to `pass/types/host-extension.md`).
- c260afe — the builder's round 4 (run 2026-10-16T20:06:54Z): workflow-check.py and the manifest; its report `handoff/TASK-006-r4-report.md`; a line in docs/BUILDER_NOTES.md.
- c762c3d — the supervisor's test `test_r014_missing_layer_is_skipped_before_the_link_test`, added after the run because the lexists skip and the `is_link` fix overlap and R4-1's own clause had no test of its own (fails against c0b2a8a's program, passes on round 4's).
- f2e6f65 — records: round 3's grades and disposition; three by-class lines in docs/HARDENING.md (markup-wrapped change words, version-dependent reparse points, `lexists` false on any lstat error).
Mutation driver (`run/supervisor/mutate_workflow_check.py`, not in the diff): 67 mutants, all killed (eight added for round 4's rules; the fence mutant re-anchored to `FENCE_LINE`). tests/test_workflow_check.py 104 passed, 1 skipped (the POSIX-only unreadable-folder test, which runs on CI's ubuntu leg); full suite 1056 passed, 21 skipped. The workflow does not change; the pin is unchanged.

## Round 3: what changed since round 2's reviewed head (2f03401)
Round 2: Review A APPROVE (0/2/4), Review B REJECT (1/2/0), the security auditor PASS with 2 advisories; the findings and their disposition are in docs/DESIGN_CRITIQUE.md, "TASK-006 round 2 — disposition". `run/review/DELTA-TASK-006c.diff` (`git diff 2f03401 HEAD`, review files left out) shows exactly what changed:
- 22d3ea1 — round 2's review files removed.
- eb6a76d — checkpoint: the corrections brief `handoff/TASK-006-r3.md` (R3-1 to R3-7; `TASK-006.md` and `TASK-006-r2.md` still hold except where it says otherwise), the supervisor's tests extended (12 new: 11 failed against round 2's program, one guard held), and round 3's fixtures (one holds a tab after `##` on purpose).
- dee34df — the builder's round 3 (run 2026-10-16T19:36:00Z): workflow-check.py and the manifest; its report `handoff/TASK-006-r3-report.md`.
- 6fc170e — records: round 2's grades and disposition.
Mutation driver (`run/supervisor/mutate_workflow_check.py`, not in the diff): 59 mutants, all killed (ten added for round 3's rules). Full suite 1039 passed, 21 skipped (the POSIX-only unreadable-folder test on Windows, and test_allowlist.py's twenty prose lines). The workflow does not change; the pin is unchanged.

## Round 2: what changed since round 1's reviewed head (aa0891a)
Round 1: Review A REJECT (1/1/8), Review B REJECT (2/1/1), the security auditor PASS with 5 advisories; the findings and their disposition are in docs/DESIGN_CRITIQUE.md, "TASK-006 round 1 — disposition". `run/review/DELTA-TASK-006b.diff` (`git diff aa0891a HEAD`, review files left out) shows exactly what changed:
- e9a1db9 — round 1's review files removed.
- c2faf7a — checkpoint: the corrections brief `handoff/TASK-006-r2.md` (R2-1 to R2-14; `handoff/TASK-006.md` still holds except where it says otherwise), the supervisor's tests extended (17 new; 14 failed against round 1's program, the other three are guards that held: prose headings stay prose, an empty segment is form, and the unreadable-folder test, which is POSIX-only and runs on CI's ubuntu leg), and round 2's fixtures (two of them deliberately begin with a UTF-8 byte-order mark).
- d64141b — the builder's round 2 (run 2026-10-16T19:03:23Z): workflow-check.py and the manifest; its report `handoff/TASK-006-r2-report.md`.
- eb7ec5c — records: round 1's grades and disposition.
Mutation driver (`run/supervisor/mutate_workflow_check.py`, not in the diff): 49 mutants, all killed (round 1's 30, the seven rules Review A found without a mutant, and twelve for round 2's rules). Full suite 1027 passed, 21 skipped (the unreadable-folder test on Windows, and test_allowlist.py's twenty prose lines). The workflow does not change this round; the pin is unchanged.

## Round 1's brief: Scope (the builder's)
- bridge/cursor-bridge/workflow-check.py
- .github/workflows/tests.yml — one step at the end of the `tests` (bridge programs) job, no secret, no env, no `if:`
- bridge/cursor-bridge/MANIFEST.json (regenerated; `VERSION` rewritten unchanged by the same tool)
- docs/BUILDER_NOTES.md, handoff/TASK-006-r1-report.md (bookkeeping)

## Out of scope (the brief's, quoted in short)
- The open list and the registry themselves; supervisor.md; settings.bridge.json; CHANGELOG/VERSION content.
- inventory-check.py / conformance-check.py reading the `Workflows:` line (TASK-008); the calibration run of the check (TASK-024, R-033's other half).
- The registry ↔ phase-module cross-check (TASK-014); reading `workflow/phases/`.
- A type or sub-workflow's statement of its default traits (no form exists yet).
- Reading a part's delivery kind (where it is recorded is TASK-011's question).
- The bridge's own `docs/PROJECT_STATUS.md`, never passed to the check in CI or a test.

## Written by the supervisor (tests and fixtures; each enforces docs/REQUIREMENTS.md R-014, the step test R-033)
- `tests/test_workflow_check.py` (59 tests), written from the brief's interface before the delegation (58 failed at the checkpoint 15c6a69, where no program existed; the one that passed is the guard that the check is not in the security floor). After the builder's run the supervisor changed two: `test_r014_registry_heading_missing` renamed the prose citation of the heading rather than the heading line (the builder reported it, rightly), and the `kind-missing` case now names its offending name (a driver mutant survived on it).
- `tests/fixtures/workflows/`: `pass/` (the CI root; every layer, a replaced module whose point a trait and a sub-workflow still add at, a fenced change heading, prose headings), `fail/<case>/` (one root per failing case, each checked against the bridge's real tables), `status/` (status-line cases with an open list of their own in which some entries are written).
- `tests/test_release_b_ci_floor.py`: `WORKFLOW_PIN` regenerated for the new step (the consequence recorded at BUG-001 round 5: an increment that changes the workflow regenerates the pin in the same diff). Compare the pin with the workflow yourself; nothing else in the file changed.
- Mutation driver (the supervisor's, not in the diff: `run/supervisor/mutate_workflow_check.py`): 30 mutants, each breaking one rule of the program in a temporary copy of the files the tests read; each killed by the tests named beside it.

## Records in the diff (expected)
- docs/PROJECT_STATUS.md (the position), docs/REQUIREMENTS.md (R-014 built; R-033's release half), docs/INVENTORY.md (the feature row), docs/HARDENING.md (PR #22 round 2's Consider: what each remedy for the key's reach costs), docs/DESIGN_CRITIQUE.md (PR #22 round 2; TASK-006's brief decisions).

## Results
Full suite 1011 passed, 20 skipped (the skips are tests/test_allowlist.py's prose lines, as on main); the check over the CI roots: RESULT: OK; windowless-check and bridge-check --sources: pass; secret-sentinel CLEAR.
