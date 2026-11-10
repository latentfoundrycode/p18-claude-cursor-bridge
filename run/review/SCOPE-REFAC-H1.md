# SCOPE - REFAC-H1 (stage H1's refactoring pass)

## What the branch is
Stage H1's refactoring pass (bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md): removing duplication and dead code with the same functionality, one gate pass for the whole branch, one squash. There is no `docs/CHANGES.md` in this project and no behaviour entry: a refactoring changes no behaviour. The question for the reviewers: **is this behaviour-preserving?**

The base is origin/main 6426650 (HOTFIX-003's carry, PR #143). Stage H1's own change is its five squash commits a7b52fd 3555c51 4dac0f8 52d18be 855a8e9 (TASK-046 to TASK-050, PRs #137 to #141, consecutive on main from 990251b); HOTFIX-003's carry merged after them and is not the stage's. The candidates came from jscpd 5.4.2 over bridge and tests (175 clones, 1.75%), filtered to the files the stage changed (67 clones), and refactor-scout's ranking against the 400-line budget (nine candidates, about 205 lines, nothing cut), kept in run/supervisor/refactor-H1-candidates.md (gitignored) and recorded in docs/HARDENING.md, "Stage H1's refactoring pass". Two briefs in the production lane, handoff/REFAC-005.md and handoff/REFAC-006.md; the rest in the tests lane.

## Brief REFAC-005: Scope and Out of scope
Quoted from handoff/REFAC-005.md, whose whole text is in the diff:

> ## Scope
> Files and directories you may create or modify:
> - bridge/cursor-bridge/bridge_env.py
> - bridge/cursor-bridge/session-start.py
> - bridge/cursor-bridge/workflow-check.py
> - bridge/cursor-bridge/diagram-check.py
> - bridge/cursor-bridge/MANIFEST.json
> - docs/BUILDER_NOTES.md
> - handoff/REFAC-005-r1-report.md
>
> Do not modify anything else.

Its `## Out of scope` section names .env and secrets/; CI, pre-commit and `tools/`; other docs/ and handoff/ files, docs/diagrams/ included; every file under `tests/`; `bridge/cursor-bridge/loop-guard.py` (its `read_status` has a caller, tests/test_loop_guard.py:83); `VERSION`; the mutants files under `run/`; the change logs; the command reference; in bridge_env.py `diagram_index_body_table`, `diagram_index_table`, `diagram_index_fallback`, `deviations_fallback`, `_first_markdown_table`, `split_entry` and every line not named in its Objective; every other file under `bridge/`. Read it in the diff for its exact words.

## Brief REFAC-006: Scope and Out of scope
Quoted from handoff/REFAC-006.md, whose whole text is in the diff:

> ## Scope
> Files and directories you may create or modify:
> - bridge/cursor-bridge/conformance-check.py
> - bridge/cursor-bridge/completion-check.py
> - bridge/cursor-bridge/MANIFEST.json
> - docs/BUILDER_NOTES.md
> - handoff/REFAC-006-r1-report.md
>
> Do not modify anything else.

Its `## Out of scope` section names the same families, and in bridge_env.py `inventory_development_data`, `plan_header_findings` and `plan_r_ids_outside_headers`; every other line of the two programs not named in its Objective. Its Context names the one difference it does not defend: completion-check's disagreement loop used to read each plan file a second time and now uses the text of the first read; the two differ only if a plan file changes on disk between the two reads within one run of a one-shot check. Check whether you read that as a behaviour change.

## The commits
1. `REFAC-H1 tests lane: one copy of the header tests' syntax-tree helpers` (cc9d664), the supervisor's test-infrastructure lane (step 3b). tests/test_header_status.py, test_header_plan.py and test_header_tables.py import `code_tree`, `names`, `constant_sets`, `call_args` and `re_patterns` from tests/test_header_currency.py in place of their copies (import-as aliases keep each file's names, which other test files import from them); tests/test_header_run_parameters.py takes `write` from its sibling module `th`, test_header_run_parameters_r2.py takes `need` from `t1`. Evidence: the collected set identical, 4,988 ids, before and after (run/supervisor/refactor-H1-collect-before.txt and -after.txt); `refactor-check.py --lane tests` "PURE", 5 files, 100 changed lines; the eight header test files 491 passed.
2. `REFAC-005: the brief, stage H1's dead code` (c2f3ef2), the brief.
3. `REFAC-005: stage H1's dead code goes from bridge_env, session-start, workflow-check and diagram-check` (1f124de), the builder (composer-2.5, run 2026-11-10T19:40:03Z, exit 0): bridge_env.py's `parse_diagram_index_rows`, `_SCOPE_PAREN` and `ScopeAgreementError` deleted (no caller) and `deviations_table`, a bare alias of `_first_markdown_table`, inlined into `parse_deviation_keys`; session-start.py's uncalled `read_status` became `read_status_file(cwd)`, returning (path, text) or (None, None), which `main` now calls in place of its own copy of the loop; workflow-check.py `check_status`'s `if len(line_problems) > 1 and p3 not in line_problems: continue` deleted (after the p0/p1 continue the one two-item list left is [p2, p3]); diagram-check.py `known_deviations`'s `elif hdr is not None:` after `if hdr is None:` became `else:`. MANIFEST.json regenerated. Evidence: scope-check "SCOPE CLEAN"; `refactor-check.py HEAD` "PURE", 47 lines; the brief's 13 test files 1,910 passed, 8 skipped; the builder's assumptions list reads none.
4. `REFAC-006: the brief, the two repeats stage H1 added` (0723dc2), the brief.
5. `REFAC-006: conformance-check's Development data verdict and completion-check's plan read, each once` (2354ade), the builder (composer-2.5, run 2026-11-10T19:54:15Z, exit 0): conformance-check.py `dev_ok` is the header's value where the inventory carries one, else `inventory_development_data`'s (called only then, as before), and the OK and MISSING lines are written once each, their text unchanged; completion-check.py's first loop keeps each headed plan's text in `headed_texts`, the disagreement loop reads that list, so the second read and second `plan_header_findings` call go (its `fatal` test could not fire, the first loop having returned 2). MANIFEST.json regenerated. Evidence: scope-check "SCOPE CLEAN"; `refactor-check.py HEAD` "PURE", 22 lines; the brief's 13 test files 531 passed, 2 skipped; the builder's assumptions list reads none.
6. `Records: stage H1's refactoring pass, as at PR #144's merge` (afaffa1): docs/HARDENING.md (the pass's section), docs/INVENTORY.md (the jscpd row, the date), docs/PROJECT_STATUS.md written as at this pull request's merge (the project's rule, ISS-009).

## The purity readings
`refactor-check.py main` reads this branch as IMPURE by commit 1, the tests lane, which edits test files; that is how the pass's two lanes read on one branch, as at stage T2's pass. The readings that hold are per lane: the production lane `refactor-check.py cc9d664 --max-lines 400` "PURE", 11 files, 67 changed lines; the tests lane's commit changes the five test files and nothing else, its collected set identical.

## Evidence already taken
- Review A, refactoring mode: APPROVE, nothing blocking, nothing to fix. It collected the six affected test files at origin/main and at HEAD (432 ids each, the diff empty) and ran them (432 passed) and ten more of the changed programs' files (1,511 passed, 8 skipped); confirmed no caller of the four bridge_env deletions remains, by name or by string; that workflow-check's deleted guard could never fire; that completion-check's second `fatal` could never be true and `plan_header_findings` has no side effect; the manifest SOURCES MATCH. One advisory, not of the five: the shared `code_tree` that tests/test_header_tables.py now imports drops a leading string only from a module, function or class body, where the old copy dropped one from any node with a body, and the shared `re_patterns` returns a list of strings where the old returned a set of constants; every existing use is unaffected.
- Mutation (D1): TASK-049's k05 was anchored on the deleted `parse_diagram_index_rows`, and five TASK-047 anchors had become ambiguous through later stage code; all six were re-anchored on the code they were written for, every anchor of the stage then found once (316 of 316). TASK-047's first run errored on c04 (the p0/p1 skip removed), which now also fails `test_r058_r3_workflow_check_refuses_a_part_named_twice_as_bridge_env_does[no-traits-mark]`: the line REFAC-005 deleted had caught that case only once c04 removed the skip before it. Reproduced on an export of the branch (3 failed, 154 passed) and the test added to c04's expected failures. Then, cut none, every file exit 0: TASK-047 47 killed, 1 expected survive; TASK-049 49 of 49; TASK-046 131 killed, 18 expected survive; TASK-048 37 of 37; TASK-050 29 killed, 4 expected survive. The mutants files are under run/supervisor/ (gitignored).
- The full suite on afaffa1, through the launcher with the pull request's variables (run 2026-11-10T21:22:17Z): "4948 passed, 40 skipped in 1903.77s (0:31:43)", exit 0. That is 4,988 tests, the collected count before and after the tests lane.

## Out of scope
- Dropped candidates: the no-op branches in `header_agrees`, `plan_body` and `_brief_fallback_from_body`; the `_fallback_list` and `_fallback_string` hoist; conformance-check loading workflow-check.py twice. Optimization: none. Beyond budget: none.
- Leads recorded in docs/HARDENING.md, not taken.
- Stage H1's review, its demonstration and reflection, and TASK-051 to TASK-054 are later work, not this diff's defect.

## Threat model
docs/INVENTORY.md (Decisions) records ASVS level 2; the trust boundary these programs sit on is the records a session or a builder writes (docs/PROJECT_STATUS.md, docs/INVENTORY.md, docs/BUILD_PLAN*.md, docs/diagrams/DEVIATIONS.md), which they read. This change moves no boundary: every header check runs on the same paths and inputs as before.

## Tests the supervisor wrote, each with the paragraph it enforces
None new. Commit 1 changes how five test files obtain their helpers; every assertion stays as it was.

## Expected bookkeeping files in the diff
docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, handoff/REFAC-005.md, handoff/REFAC-005-r1-report.md, handoff/REFAC-006.md, handoff/REFAC-006-r1-report.md, bridge/cursor-bridge/MANIFEST.json, and run/review/ (this file, the diff, the assumptions file).
