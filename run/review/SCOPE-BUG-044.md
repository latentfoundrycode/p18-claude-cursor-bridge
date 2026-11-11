# SCOPE for BUG-044 (Review B, round 2)

## Round 1 and its disposition
Review B, round 1 (BUG-044-r1), REJECT on one finding, behaviour: bridge/commands/calibrate-bridge.md step 4 said a run stopping on HEADER MALFORMED (exit 2) is repaired at the line the message names, while records-migrate.py prints check_header's findings for a header that breaks its schema, which name keys and no line. It confirmed the program repairs the named cause at the read-back, the reproduction tests unedited and run-parameters.md's sentence. The supervisor's fix (this round, the guard's round 2, no builder run; below the ceiling, so no Blocking class line): the sentence names the line for a header that cannot be read and the keys for a schema break; test_bug044_the_calibration_s_malformed_stop_says_what_the_message_names (at the end of tests/test_bug044.py) enforces it, running the program on a brief whose header holds only record and header (exit 2, keys, no line number) and on one with a tab in its header (exit 2, line N), and asserting the text's wording, which the earlier commit lacks. Review A's confirming read APPROVE. The rest of this file is round 1's, unchanged but for the evidence.

The fix: BUG-044, a defect found after TASK-051's and TASK-052's merges by stage H2's review, round 1 (both reviewers' blocking findings, one cause). Branch bug-044 from main 86a37e3 (PR #147's merge). The fix brief is handoff/BUG-044.md (spec-packager's fix variant), committed as 2770867, the builder's checkpoint; one builder round (composer-2.5). This is the review guard's first round for BUG-044, below the code gate's ceiling: there is no Blocking class line.

The confirmed cause (docs/debug/BUG-044.md): records-migrate.py's read-back checked only header_agrees against the composer's own prose reading, never what the headed plan's readers check, so it wrote headers that plan-check.py (an increment heading outside any stage) and completion-check.py (an R-id on a bold Satisfies line) then refuse. The fix-mode question: does the change repair that cause at that mechanism, or make the symptom disappear?

Where the fix ends: records-migrate.py alone among the programs (bridge_env.py is out of its Scope); the supervisor's text corrections that ride from the stage review (calibrate-bridge.md step 4, run-parameters.md's lift lists, D-002's wording). Stage H2's review round 2 runs after this merge on the stage's whole change; TASK-053 stamps the release; TASK-054 migrates this repository's records with the installed program after the owner's install. Those are not this diff's defect. records-migrate.py must never be run over this repository's records or with the checkout as its folder: fixtures in the system temporary folder only.

## The brief's Scope and Out of scope, quoted
## Scope
Files you may create or modify:
- bridge/cursor-bridge/records-migrate.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_bug044.py
- docs/BUILDER_NOTES.md
- handoff/BUG-044-report.md

Limits on these files:
- `bridge/cursor-bridge/records-migrate.py`: the fixes F1 to F5 and nothing else.
- `bridge/cursor-bridge/MANIFEST.json` changes only by being regenerated with `python tools/make-manifest.py` (Done, step 2). Never edit it by hand.
- `bridge/cursor-bridge/VERSION` is outside your Scope. `make-manifest.py` rewrites its line endings; restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done, step 3), and edit it in no other way.
- `tests/test_bug044.py` is the supervisor's above the marker line quoted in the Objective. Edit nothing above that line, the module docstring, imports and helpers included. Your cases go below it.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, `docs/debug/BUG-044.md` included.
- `bridge/cursor-bridge/bridge_env.py` (the supervisor's ruling on F2: call its functions, change none, and add no Satisfies pattern of the program's own), every other program under `bridge/cursor-bridge/`, `tools/make-manifest.py` and `tools/dump-cli.py`.
- The texts `bridge/commands/calibrate-bridge.md` and the run-parameters text. The supervisor updates them after your run.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`. The program's command line does not change in this fix. If `python tools/dump-cli.py --check` fails, say so in the report and change nothing.
- `tests/test_records_migrate.py`, `tests/test_header_plan.py`, `tests/test_header_plan_r2.py`, `tests/test_header_plan_r3.py` and every other test file: you run them and edit none.
- What `handoff/TASK-051-r3.md` recorded for later stays as it is. That includes `compose_header`'s own unbalanced-parenthesis check (lines 419-421), the program's use of private `bridge_env` names, and the check-then-act windows.
- Any mutation script. The mutation run is the supervisor's, after your run.

## The supervisor's tests, each with the paragraph it enforces
- tests/test_bug044.py above the marker line (committed in ea02b0b and 34e65ec before the brief; red on 86a37e3, "6 failed, 2 passed", the two passing the plain plan's guards): enforces handoff/BUG-044.md F1 and F2 (a plan outside any stage, a bold Satisfies line, each listed cannot read and not written, the reason as the brief gives it), the plain-plan guard (the repair the reason names migrates and its readers accept the header), the gate cases (plan-check --no-git and completion-check --mode plan pass before and after the migration, for the plain, outside-stage and bold-satisfies plans), F4 (a root named proj[1] still finds its plan) and F5 (merge_unit: null where a brief has no Merge unit line). Each docstring names its finding.
- tests/test_bug044.py at the end, after the builder's cases: test_bug044_f3_the_read_back_runs_the_readers_shape_rule_on_its_own (enforces F3: with F1's and F2's refusals patched away and the outside-stage increment carrying no Satisfies line, only plan_header_refusal in the read-back stops the write) and test_bug044_f4_a_sibling_folder_the_raw_pattern_matches_is_never_listed (enforces F4, from the security audit: beside proj[1] a sibling proj1 the unescaped pattern matches, shown first, is never listed).
- The builder's cases below the marker are the builder's own (the brief's Requirement 6).
- tests/test_b3_least_confident.py: the pin of run-parameters.md's procedure re-taken for the lift-list sentence.

## The mutants
run/supervisor/BUG-044-mutants.json (7 mutants, written by run/supervisor/bug044_mutants.py: F1's refusal off, F2's refusal off, F3's read-back net off, F3's satisfies coverage off, F3's shape rule off, glob.escape off, merge_unit null off). "counts: run=7 cached=0 killed=7 survived=0 not applied=0 error=0 expected survive=0", exit 0. The new tests against the checkpoint 2770867: all 12 failing, exit 0 (the F3 cases fail there on the names they patch; their precondition is shown by mutants m03 to m05).

## The threat model
None is recorded in docs/INVENTORY.md (Decisions) for records-migrate.py, so the five blocking classes stand unbounded. A security finding is judged by whether untrusted input can reach it: the records' text is written by builders, reviewers and supervisors, and a project may be a cloned or third-party repository.

## Recorded already, not this round's blocking findings unless the code shows worse
docs/HARDENING.md, Release B2's stage H2 (in the diff): TASK-051's recorded items (the check-then-act windows, the close failure's removal, the private bridge_env names and the rest); BUG-044's recorded items (the launcher's and plan_increment_ids' unescaped glob, the unreachable branches, the thin --check case, F2 per file, the report's inaccuracies).

## Evidence
- scope-check: SCOPE CLEAN (base 2770867).
- the fix's own test files: "1021 passed, 1 skipped in 54.09s" (the skip is the symlink privilege on this account).
- Review A: APPROVE ("148 passed in 3.72s", "186 passed, 1 skipped in 112.10s", "RESULT: SOURCES MATCH bridge 2026.11.09a"); its should-fix (m02's expected list) and wording items taken before this round. Security audit: PASS, two advisories (one a test, taken; one a HARDENING lead).
- the texts and the fix after those items: "202 passed in 4.68s".
- the full suite with the pull request's variables (GITHUB_REF=refs/pull/148/merge), on round 1's head: 5080 passed, 41 skipped in 1899.68s (0:31:39)
- round 2's fix: tests/test_bug044.py "22 passed in 3.80s"; Review A's confirming read "22 passed in 3.68s" and "106 passed, 1 skipped in 42.09s".

## Expected bookkeeping and records in the diff
handoff/BUG-044.md (the brief) and handoff/BUG-044-report.md (the builder's report); docs/debug/BUG-044.md (the root-cause record); bridge/cursor-bridge/MANIFEST.json (regenerated); the supervisor's records commit: docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md (as at PR #148's merge), docs/archive/STATUS_HISTORY.md, docs/BUILDER_NOTES.md, project.json; and run/review/ (these files).
