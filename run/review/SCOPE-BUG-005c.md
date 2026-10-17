# SCOPE — BUG-005, gate round 3

BUG-005 is the supervisor's own branch for stage B2's review, round 4. It holds tests, fixtures, governance text and records. No builder ran, and no program under bridge/ changed except MANIFEST.json, which tools/make-manifest.py regenerated; VERSION is unchanged.

Round 2 (945c515) reviewed:
- Review B: APPROVE, 0/0/0.
- Review A: APPROVE, with three should-fix items, all taken here.

Round 3's own change is in run/review/DELTA-BUG-005c.diff (945c515 to the fix commit 0005913, excluding run/review/). The whole branch is in run/review/REVIEW-BUG-005c.diff.

## Round 3's changes, each with the paragraph it enforces
- **The "each point" reading was untested.** The test fixture tests/fixtures/workflows/pass/types/host-extension.md now also holds `## Set at intake.target-environment`, beside its `## Set at intake.delivery-kind`. The new test tests/test_workflow_check.py::test_r014_a_file_sets_each_point_at_most_once enforces the sentence in extension-points.md, "How a conditional workflow names a point": "A file sets each point, and replaces each module, at most once". Its precondition asserts that both Sets stand outside a fence. It then asserts that the pass root's whole output is RESULT: OK, standard error is empty, and the exit code is 0. fail/form-two-sets already covers the same point set twice.
- **docs/HARDENING.md, the round-4 section.** The record now says that the unknown type folder's file holds a change the check would refuse with (a); it used to say "accept". The fence lead now records that it was taken. The replace-and-add question is routed to TASK-019's brief.
- **The registry's fence sentence.** bridge/cursor-bridge/workflow/extension-points.md:72 adds: "A `##` line inside a fenced code block (opened by three or more backticks or tildes) is not a heading and changes nothing." This is pinned in tests/test_extension_points.py::test_r006_the_registry_names_the_change_words_the_check_reads. The check's fence handling is TASK-006 R5-3; its known gaps (container blocks, HTML blocks) are HARDENING leads.
- **New driver mutants** in run/supervisor/mutate_workflow_check.py (local; run on temporary copies):
  - "one Set per file": `if target in seen_set:` becomes `if seen_set:`. Killed by the new test.
  - "unknown type folder's files read": drops the `continue` after the d-folder item in `collect`. Killed by test_r014_unknown_type_folder_is_reported_without_its_files.
  - Result: 106 of 106 killed. mutate_workflows_line.py stands at 42 of 42.
- The four review files from round 2 are removed.

## Earlier rounds (unchanged; the whole branch)
Round 1's scope and tests: git show be12dcb:run/review/SCOPE-BUG-005.md. Round 2's: git show 945c515:run/review/SCOPE-BUG-005b.md.

Suite: 1251 passed, 23 skipped. The skips are environmental: the symlink privilege, POSIX permissions, and prose rows.

## Files expected in the diff
- tests/test_workflow_check.py, tests/test_workflows_line_check.py, tests/test_open_list.py, tests/test_extension_points.py
- the fixtures named in rounds 1 to 3
- bridge/cursor-bridge/workflow/extension-points.md, bridge/cursor-bridge/workflow/open-list.md, bridge/commands/supervisor.md, bridge/cursor-bridge/MANIFEST.json
- docs/HARDENING.md, docs/PROJECT_STATUS.md
- run/review/ (these review files)

## Out of scope
- every program under bridge/cursor-bridge/ (*.py)
- CI configuration
- leads routed in HARDENING to later tasks
- design for later stages
