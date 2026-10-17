# SCOPE — BUG-005, gate round 2

BUG-005 is the supervisor's own branch for stage B2's review, round 4: tests, fixtures, four sentences of governance text in three files, and the records. No builder ran, and no program under bridge/ changed. The only exception is MANIFEST.json, which tools/make-manifest.py regenerated (VERSION is unchanged).

Round 1 of this gate reviewed be12dcb:
- Review A: APPROVE, with 2 should-fix and 5 consider.
- Review B: REJECT, with 1 blocking: extension-points.md:72 read "A file sets one point, and replaces one module, at most once", which says one target per file. Review A raised the same sentence as a consider, so the two converge.

Round 2's own change is in run/review/DELTA-BUG-005b.diff (be12dcb to the fix commit 577d51c, excluding run/review/). The whole branch is in run/review/REVIEW-BUG-005b.diff.

## Round 2's changes
- bridge/cursor-bridge/workflow/extension-points.md:72 now reads "A file sets each point, and replaces each module, at most once." It is pinned in tests/test_extension_points.py::test_r006_the_registry_names_the_change_words_the_check_reads, which enforces the registry against workflow-check.py's CHANGE_FIRST, TRAILING_PUNCT and its two-Set/two-Replace findings.
- docs/HARDENING.md, round-4 section: the record of a one-line status file with a tab beside the traits marker now names the finding the check actually gives, "Workflows line breaks the part-prefix rule" (reproduced by the supervisor). Three considers are recorded for TASK-017 and TASK-019: the registry's fence sentence, a file adding at a module it replaces, and the "workflows" word test.
- tests/test_workflow_check.py::test_r014_unknown_type_folder_is_reported_without_its_files (new) enforces R-014: a folder under types/ that is no product type gives the (d) finding alone. Its precondition asserts that the folder's file holds `## Add at nowhere.at-all`, and the test checks the whole output and an empty standard error.
- tests/fixtures/workflows/status/ok-multi-unclassified.md now has `Phase: intake` (was `building`). Per supervisor.md's Workflows paragraph, a part reads `not yet classified` until intake has classified it.
- The three round-1 review files are removed.

## Round 1's scope (unchanged; the whole branch)
Round 1 covered the following:
- fence controls for each CommonMark rule the workflow check reads;
- status cases: a multi-part file with a prefixed `not yet classified` part, a leading space and a tab in a part name, a trailing space in a trait, and a sub-type's key where its name belongs;
- presence checks in the pass root;
- conformance-check stays silent about the line when no status file exists;
- the registry's change-heading sentence and its TASK-014 sentence;
- the open list's pause for a part fitting two sibling sub-types equally;
- supervisor.md's "such as".

Each test and the paragraph it enforces are listed in round 1's SCOPE (git show be12dcb:run/review/SCOPE-BUG-005.md).

Mutation drivers (run/supervisor/, local; they run on temporary copies):
- mutate_workflow_check.py: 104 of 104 killed, re-run after round 2;
- mutate_workflows_line.py: 42 of 42 killed.

Suite: 1250 passed, 23 skipped (environmental: symlink privilege, POSIX permissions, prose rows).

## Files expected in the diff
- tests/test_workflow_check.py, tests/test_workflows_line_check.py, tests/test_open_list.py, tests/test_extension_points.py
- the fixtures named in round 1, and ok-multi-unclassified.md
- bridge/cursor-bridge/workflow/extension-points.md, bridge/cursor-bridge/workflow/open-list.md, bridge/commands/supervisor.md, bridge/cursor-bridge/MANIFEST.json
- docs/HARDENING.md, docs/PROJECT_STATUS.md
- run/review/ (these review files)

## Out of scope
- every program under bridge/cursor-bridge/ (*.py);
- CI configuration;
- leads routed in HARDENING to later tasks;
- design for later stages.
