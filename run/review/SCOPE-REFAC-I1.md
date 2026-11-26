# SCOPE-REFAC-I1: stage I1's refactoring pass (branch refactor/I1)

Blocking class: none (round 1, below the ceiling)

The question for every reviewer: is this behaviour-preserving? The branch is one pure refactoring diff in two lanes: the tests lane (4568aa9, the supervisor's) and the production lane (REFAC-015, REFAC-016, REFAC-017, one commit each, builder composer-2.5). No CHANGES.md entry: no behaviour changes.

## REFAC-015 (handoff/REFAC-015.md)

### Scope (quoted)

Files and directories you may create or modify:
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-015-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

### Out of scope (quoted)

- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser` and no module docstring)
- every file under `tests/`, `tests/fixtures/` included: no test file or fixture may be edited, renamed or created (the supervisor's purity check fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.24a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's and the launcher's, gitignored; you write nothing there
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- in roster-check.py: `_profile_in_use` and the two inline probe blocks (lines 1224-1250, 1240-1247 and 1287-1295 at `8b03c32`: the nested `_profile_in_use` with its builder probe, and the `review_b_alt` probe in the `--review-alt` branch) are not touched, not even to reuse `_probe_roles`; a later fix changes them (R-107's open item, planned at stage I2's start). `_probe_roles`, `_alt_pool_ok`, `_r_excluded`, `_rebuild_needs_new_branch`, `_rebuild_built_by_model`, `_parse_run_line`, `_parse_run_log_raw`, `_branch_from_head`, `repair_record`, the rest of `built_families` and of `main()`, and every other function stay as they are
- `bridge/cursor-bridge/bridge-run.py` and every other file under `bridge/`

## REFAC-016 (handoff/REFAC-016.md)

### Scope (quoted)

Files and directories you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-016-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

### Out of scope (quoted)

- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches neither `build_parser` nor the module docstring)
- every file under `tests/`, `tests/fixtures/` included: no test file or fixture may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.24a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's and the launcher's, gitignored; none of this brief's commands writes a file there, and you write none
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- `bridge/cursor-bridge/roster-check.py` (REFAC-015's) and every other file under `bridge/`
- in mutation-run.py, every line but those the five parts name: the two seven-line sites in `main()` and the added `run_paths`; the checkpoint loop's lines 1901-1911; `pytest_env`'s two loops; the five prefix sites and the added constant; the generated text's two definitions and four calls. `OUTCOMES_PLUGIN_CODE`, `run_baselines`, `run_resolution_check`'s other lines, the module docstring and `build_parser` stay exactly as they are

## REFAC-017 (handoff/REFAC-017.md)

### Scope (quoted)

Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-017-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only. `MANIFEST.json` is written only by `python tools/make-manifest.py`, never by hand.

### Out of scope (quoted)

- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/`, `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser`, no usage text and no module docstring)
- every file under `tests/`, `tests/fixtures/` included: no test file or fixture may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is and report it
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.24a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored; this brief asks you to write no file there (every output goes into the report)
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- `bridge/cursor-bridge/roster-check.py` and `bridge/cursor-bridge/mutation-run.py` (REFAC-015's and REFAC-016's), and every other file under `bridge/`
- in bridge-run.py, every line but Part 1's block in `_git_launch_state` and Part 2's three bodies and the added `_read_docs_json`. In particular these stay exactly as they are, though they look alike: the other git readers `git_common_dir` (line 1180, `rev-parse --git-common-dir`), `branch_of` (line 2580, `rev-parse --abbrev-ref HEAD`) and `local_head` (line 2698, a one-line `rev-parse HEAD` with other options); `_git_rev_parse` and `_git_rev_parse_path`; `_run_parameters_values` (line 1069, which reads `docs/RUN_PARAMETERS.md` as text); the status block of `_git_launch_state`; and every caller of the touched functions

## The tests lane (4568aa9)

tests/roster_rows.py takes the helpers and constants tests/test_improve_roster_alt.py and tests/test_improve_roster_launch.py both carried (row, review_row, rebuild_text, lies_in_no_repository, the model ids, FULL, NATIVE, the row counter). No assertion changed. Proof: the collected set of the two files before and after, 232 and 232, identical; refactor-check.py --lane tests PURE (103 lines).

## Purity

refactor-check.py main reads the whole branch IMPURE by the tests lane's commit (399 lines); per lane: refactor-check.py 4568aa9 --max-lines 400 PURE (10 files, 240 lines), the tests lane PURE above. The records commit (docs/HARDENING.md, docs/PROJECT_STATUS.md) comes after.

## Threat model

docs/INVENTORY.md's Decisions record no threat model for roster-check.py, mutation-run.py or bridge-run.py beyond the bridge's standing ones: the launcher keeps every subprocess windowless (creationflags with NO_WINDOW, R-039) and fails closed on what it cannot read (R-107's review refusals). The refactoring must keep both.

## Tests the supervisor ran (no test written in the production lane)

- REFAC-015: tests/test_improve_roster_alt.py, test_improve_roster_launch.py, test_roster_check.py, test_roster_check_a4.py, test_hotfix25a_roster_launcher.py, test_program_roster_sign_in.py: 281 passed, 3 skipped (the same before the change, the builder's report).
- REFAC-016: tests/test_improve_mutation_editable.py, test_mutation_run.py, test_mutation_run_supervisor.py, test_program_mutation_baseline.py, test_bug032.py, test_dump_cli.py: 324 passed, 2 skipped.
- REFAC-017: tests/test_improve_roster_launch.py, test_hotfix25a_roster_launcher.py, test_task032_supervisor_launcher.py, test_bridge_run.py, test_bridge_run_design_ceiling.py, test_bridge_run_review_ceiling.py, test_bridge_run_driver.py, test_bridge_run_slot.py, test_hotfix24a_heavy_slots.py, test_header_currency.py: 622 passed, 4 skipped.
- The status and records tests with the pull request's environment: 222 passed.

## Mutants (D1)

Stage I1's 95 mutants (run/supervisor/TASK-085, TASK-086a, TASK-086b, TASK-086b-r3, TASK-087b -mutants.json) re-checked at the branch's tree: five moved by the pass, re-anchored keeping their meaning, collected in run/supervisor/REFAC-I1-mutants.json and run on this tree: run=5 killed=5 survived=0.

## Expected bookkeeping and records in the diff

bridge/cursor-bridge/MANIFEST.json (regenerated by each production commit), handoff/REFAC-015.md, REFAC-016.md, REFAC-017.md (the briefs; REFAC-017's header reordered in its own records commit), handoff/REFAC-015-r1-report.md, REFAC-016-r1-report.md, REFAC-017-r1-report.md (the builders' reports), docs/HARDENING.md and docs/PROJECT_STATUS.md (the supervisor's records), run/review/ (these review files, removed before the merge).

## Held, not in this diff

The scout's candidates 9 and 12 (roster-check.py's _profile_in_use and its probe blocks) are held for stage I2's fix of --review-alt, which changes that function.
