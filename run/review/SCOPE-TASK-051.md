# SCOPE for TASK-051 (Review B, round 2)

Blocking class: failing test - CI, PR #146's first run 42960332750, job bridge programs (ubuntu-latest): tests/test_records_migrate.py::test_r062_ruling2_given_path_shown_as_given failed ("1 failed, 5018 passed, 60 skipped")
The code of the round this line lifts: 8a6def5, the head the previous round's snapshot (TASK-051-r1) recorded; a round of the supervisor's own fix, no builder run.

The increment: TASK-051, records-migrate.py, R-062's program. Branch task-051 from main 08ceb66 (PR #145's merge). Three builder rounds (composer-2.5, native profile): round 1 (handoff/TASK-051.md, checkpoint 3a32346), round 2 (handoff/TASK-051-r2.md, checkpoint bfdde5e), round 3 (handoff/TASK-051-r3.md, checkpoint 4f93944). Review B's round 1 (TASK-051-r1, on 8a6def5) approved. Then CI's ubuntu job on PR #146 failed one test, the builder's round-1 test test_r062_ruling2_given_path_shown_as_given: it passed the given path docs backslash INVENTORY.md, and on Linux a backslash is a file-name character, not a separator, so the program's line "cannot read docs\INVENTORY.md: no such file" was right there and the test assumed Windows. This round is the supervisor's fix: the test writes the path with os.path.join (on Windows the same string as before); the backslash form stays covered by test_r062_r2_a_given_path_with_backslashes_is_shown_as_given, skipped off Windows. No program change. Confirm or deny the Blocking class line above against the code of 8a6def5 (on Linux the test as written there fails; this host is Windows, so show it by the path rules, for instance posixpath against ntpath, or any run of your own outside the checkout), never against the fixed code.

The launcher's builder count is three and the guard's count becomes two with this round; taking the larger, the round is ABOVE the code gate's ceiling: grade every finding by the five blocking classes first (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism, a failing test); only those send work back, every other finding goes to docs/HARDENING.md.

Where the increment ends: the program bridge/cursor-bridge/records-migrate.py, its manifest, allowlist and command-reference entries, and D-002's dump_cli edge to it. R-062's text half (the templates, calibrate-bridge.md's step) is TASK-052's; this repository's records gaining headers is TASK-054's, by the installed program after the owner's install; R-062 stays planned in docs/REQUIREMENTS.md until TASK-052. Those are not this diff's defect. The program must never be run over this repository's records (the inventory's Development data decision): run it only on fixtures in the system temporary folder.

## The supervisor's tests, each with the paragraph it enforces
- tests/test_records_migrate.py above the builder's marker (the supervisor's whole; below the marker the builder's cases, one of which, test_r062_ruling2_given_path_shown_as_given, this round's fix edits):
  - the acceptance tests (committed before the brief): enforce docs/BUILD_PLAN.md TASK-051's Done when, docs/DESIGN.md Change: release B2, "Writing" (the migration), "The reader" and "Header first; fallback; malformed", R-062, and round 1's ten rulings (run/supervisor/task051-rulings.md as handoff/TASK-051.md states them); the oracle is bridge_env alone (read_header, check_header, header_agrees against the kind's fallback);
  - the section "round 2: the reviewers' findings on round 1" (18 cases): enforces handoff/TASK-051-r2.md F1 to F14;
  - the section "round 3: the reviewers' findings on round 2" (3 cases): enforces handoff/TASK-051-r3.md G1 and G2.

## The mutants
run/supervisor/TASK-051-mutants.json (31 mutants over records-migrate.py). The mutation run: "counts: run=15 cached=16 killed=31 survived=0 not applied=0 error=0 expected survive=0", exit 0. This round changes no program line.

## The threat model
None is recorded in docs/INVENTORY.md (Decisions) for records-migrate.py, so the five blocking classes stand unbounded. The brief's Security context gives the trust boundary (ASVS level 2): the records are text files a supervisor, a builder or a reviewer may each have written, and the program rewrites them; a builder can commit a directory symbolic link.

## Recorded already, not this round's blocking findings unless the code shows worse
docs/HARDENING.md, Release B2's stage H2, TASK-051 (in the diff), and the INVENTORY Decisions row of TASK-051's accepted items.

## Evidence
- tests/test_records_migrate.py on this round's tree, on this Windows host: "87 passed, 1 skipped in 14.11s".
- the full suite with the pull request's variables (GITHUB_REF=refs/pull/146/merge), on round 1's tree: "5038 passed, 41 skipped in 1912.64s (0:31:52)", exit 0 (Windows).
- CI's first run on 7844bde: security floor pass; bridge programs (ubuntu-latest) "1 failed, 5018 passed, 60 skipped", the one test above.

## Expected bookkeeping and records in the diff
docs/BUILDER_NOTES.md, handoff/TASK-051.md, handoff/TASK-051-r2.md, handoff/TASK-051-r3.md, handoff/TASK-051-r1-report.md, handoff/TASK-051-r2-report.md, handoff/TASK-051-r3-report.md, bridge/cursor-bridge/MANIFEST.json (regenerated), docs/diagrams/D-002-components.md, and the supervisor's records commits: docs/HARDENING.md (with this round's line), docs/INVENTORY.md, docs/PROJECT_STATUS.md (as at PR #146's merge), docs/archive/STATUS_HISTORY.md, project.json; and run/review/ (these files).

## The briefs' Scope and Out of scope, quoted

### handoff/TASK-051.md

#### Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/records-migrate.py
- bridge/cursor-bridge/MANIFEST.json
- bridge/cursor-bridge/settings.bridge.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_records_migrate.py
- tests/test_dump_cli.py
- tests/test_allowlist.py
- docs/BUILDER_NOTES.md
- handoff/TASK-051-r1-report.md

Limits on these files:
- `bridge/cursor-bridge/records-migrate.py` is new.
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py`. Never edit it by hand.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only as regenerated by `python tools/dump-cli.py`. Never edit either by hand.
- `bridge/cursor-bridge/settings.bridge.json`: the one change is one new entry in `permissions.allow` (Requirement R13). Nothing else in the file changes.
- `tests/test_records_migrate.py` is the supervisor's, committed at the checkpoint 1ff0648. Add your own cases only below its marker line, which reads exactly `# ---------------------------------------------------------------- builder's cases below this line`. Edit nothing above that line, its module docstring included.
- `tests/test_dump_cli.py`: the one change is `"records-migrate.py"` added to the `ARGPARSE` tuple (Requirement R14). Nothing else changes.
- `tests/test_allowlist.py`: add one test for the new rule (Requirement R13). Do not change an existing test.

Do not modify anything else.

#### Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's: `BUILD_PLAN.md`, `DESIGN.md`, `REQUIREMENTS.md` (the requirement's row is flipped by the supervisor's records commit), `INVENTORY.md`, `PROJECT_STATUS.md`, `RUN_PARAMETERS.md`, `HARDENING.md`.
- `docs/diagrams/D-002-components.md`. The edge `dump_cli -.-> records_migrate` and the note's count are drawn by the supervisor's commit on this branch after your run (the plan's Scope note for this increment). Do not edit the diagram, even though one test needs it (Constraints, "Known failures").
- `bridge/cursor-bridge/bridge_env.py`, every other program under `bridge/cursor-bridge/`, and `tools/dump-cli.py`. Call `bridge_env`'s functions; change none. If the work seems to need a change there, stop and report it.
- Writing a header into any record of this repository (TASK-054, by the installed program at the calibration). The templates, the core's "Project state" rule and `calibrate-bridge.md`'s step (TASK-052).
- Every test file not listed in the Scope.
- Any mutation script. The mutants file and the mutation run are the supervisor's.

### handoff/TASK-051-r2.md

#### Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/records-migrate.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_records_migrate.py
- docs/BUILDER_NOTES.md
- handoff/TASK-051-r2-report.md

Limits on these files:
- `bridge/cursor-bridge/records-migrate.py`: the fixes of F1 to F16 and nothing else.
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py` (Done, step 2). Never edit it by hand.
- `bridge/cursor-bridge/VERSION` is outside your Scope. `make-manifest.py` rewrites its line endings; leave the file as the command leaves it, edit it in no other way, and say in the report whether `git status --short` lists it. The supervisor restores it after your run.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only if the program's command line changes, which this round should not do (no argument, option, default or help text is added, removed or renamed). Then, and only then, regenerate both with `python tools/dump-cli.py` and say in the report why the command line changed. Never edit either by hand.
- `tests/test_records_migrate.py` is the supervisor's above its marker line, which reads exactly `# ---------------------------------------------------------------- builder's cases below this line`. Edit nothing above that line, the round-2 section and the module docstring included. Your own cases, round 1's and any you add now, live below it; round 1's cases below the marker stay and stay green.

Do not modify anything else.

#### Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, `docs/diagrams/D-002-components.md` among them.
- `bridge/cursor-bridge/bridge_env.py`, every other program under `bridge/cursor-bridge/`, `bridge/cursor-bridge/settings.bridge.json`, `tools/dump-cli.py` and `tools/make-manifest.py`. Call `bridge_env`'s functions; change none. If a fix seems to need a change there, stop and report it.
- F17, not taken in this round: the program uses private `bridge_env` names (`_derived_historic`, `_PLAIN_WORD_RE`, `_PLAIN_TYPED_WORDS`, and others such as `_kind_norm`, `_plan_field_value`, `_demonstration_present`, `_REQ_STATUSES`). It is recorded for a later increment (to `docs/HARDENING.md`, by the supervisor). Leave those uses as they are and leave `bridge_env.py` untouched; do not replace them with copies of their logic.
- `tests/test_dump_cli.py`, `tests/test_allowlist.py` and every test file other than `tests/test_records_migrate.py` (round 1 finished its changes to the first two).
- Writing a header into any record of this repository (TASK-054). The templates and the calibration step (TASK-052).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run; this brief asks for the code fix only.

### handoff/TASK-051-r3.md

#### Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/records-migrate.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_records_migrate.py
- docs/BUILDER_NOTES.md
- handoff/TASK-051-r3-report.md

Limits on these files:
- `bridge/cursor-bridge/records-migrate.py`: the fixes of G1 to G3 and nothing else.
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py` (Done, step 2). Never edit it by hand.
- `bridge/cursor-bridge/VERSION` is outside your Scope. `make-manifest.py` rewrites its line endings; leave the file as the command leaves it, edit it in no other way, and say in the report whether `git status --short` lists it. The supervisor restores it after your run.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only if the program's command line changes, which this round should not do (no argument, option, default or help text is added, removed or renamed). Then, and only then, regenerate both with `python tools/dump-cli.py` and say in the report why the command line changed. Never edit either by hand.
- `tests/test_records_migrate.py` is the supervisor's above its marker line, which reads exactly `# ---------------------------------------------------------------- builder's cases below this line`. Edit nothing above that line, the round-2 and round-3 sections and the module docstring included. Your own cases, those of earlier rounds and any you add now, live below it; the cases below the marker stay and stay green.

Do not modify anything else.

#### Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, `docs/diagrams/D-002-components.md` and `docs/HARDENING.md` among them.
- `bridge/cursor-bridge/bridge_env.py`, every other program under `bridge/cursor-bridge/`, `bridge/cursor-bridge/settings.bridge.json`, `tools/dump-cli.py` and `tools/make-manifest.py`. Call `bridge_env`'s functions; change none. If a fix seems to need a change there, stop and report it.
- **Recorded for later, not in this round** (to `docs/HARDENING.md` under TASK-051, by the supervisor). Leave each as it is:
  - `compose_header`'s own unbalanced-parenthesis check (lines 419-421) is unreachable from `main` for plans, since `main` checks first (lines 667-670). It stays: do not remove it or change it.
  - The check-then-act windows: a record or a folder swapped for a link between the check and the open, or between the read-back and `os.replace`, and no re-read of the record before `os.replace`.
  - `os.replace` gives the new file the folder's default permissions, not the record's own.
  - An enumerated entry that is not a file (a folder named like a record) is listed `cannot read <path>: not a file`; accepted, one line per record.
  - The `OSError` reason is `str(exc)`, which carries the absolute path on stdout; accepted for a local program's own output.
  - The builder's F15 case below the marker (`test_r062_r2_a_given_path_on_another_drive_is_listed`) stubs `os.path.relpath` and asserts neither the record untouched nor the absence of a traceback; leave it as it is.
- The program's use of private `bridge_env` names (`_derived_historic`, `_PLAIN_WORD_RE`, `_PLAIN_TYPED_WORDS`, `_kind_norm`, `_plan_field_value`, `_demonstration_present`, `_REQ_STATUSES`), recorded for a later increment: leave those uses as they are and do not replace them with copies of their logic.
- `tests/test_dump_cli.py`, `tests/test_allowlist.py` and every test file other than `tests/test_records_migrate.py`.
- Writing a header into any record of this repository (TASK-054). The templates and the calibration step (TASK-052).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run; this brief asks for the code fix only.
