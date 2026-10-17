# SCOPE — BUG-007 (stage B2 review, round 6)

## Gate round 3 (BUG-007 r3)

Round 2 of this gate: Review A APPROVE (0 blocking, 1 should-fix, 3 considers), Review B REJECT. The change since the reviewed head 42b483a is in run/review/DELTA-BUG-007.diff; the whole branch is in run/review/REVIEW-BUG-007.diff.
- **REVIEWERS DISAGREED** on whether the survivor list in docs/HARDENING.md is reliable (correctness of the records); decided for Review B. Its example was misread: line 190's survivor is `.strip()` read as `.rstrip()` (run/supervisor/sweep_workflow_check_r7.out), and the `.lstrip()` mutant it ran is killed by the no-trailing-pipe case, as it found. But the list named lines without operators, and its count (52) was stale after r2 (Review A's consider), so the point converged and is blocking.
- **Taken:** the sweep rerun after this change (run/supervisor/sweep_workflow_check_r8.out, local): 756 mutants, 711 compile, 51 survivors. The list in HARDENING's round 6 section is written from that output by a script that fails on any survivor without a reason, each survivor with its line and operator: 46 equivalent, 4 held on CI's ubuntu leg, 1 lead.
- **Review A, should-fix:** 342 and 360 are separated on a POSIX host by a folder name holding a backslash (workflow-check.py:323 turns it into a slash); both reasons say so, and a lead for the next program change records it.
- **Review A, considers:** the driver's count states its round (196 at round 6, 198 after gate round 1); the three remaining unread files under `traits/` (form-not-markdown's installable.txt, form-traits-folder's two extra.md) hold a failing change, pinned in ROUND6_PRECONDITIONS.
- **Drivers:** mutate_workflow_check.py 198 of 198 killed (no new mutant; the change is records and fixture bodies). Suite: 1344 passed, 23 skipped.

## Gate round 2 (BUG-007 r2)

Round 1 of this gate: Review A REJECT, Review B REJECT. The change since the reviewed head 144842c is in run/review/DELTA-BUG-007.diff; the whole branch is in run/review/REVIEW-BUG-007.diff as before.
- **Review A, blocking:** the sweep's 342 with `parts[0] == "types"` dropped is not equivalent (a folder under `traits/` hid a type file of its name): form-traits-folder now holds `types/odd.md` with a failing change, two lines added to its FILE_EXACT entry, a precondition added, the mutant added to the driver.
- **Review A, blocking:** 335 was not killed on Linux: the dangling link in test_r014_link_among_a_folders_files_is_form is named `gone.md` now, its expected line and docstring changed.
- **Review A, should-fix:** 381 listed with 380 in HARDENING.
- **Review A, noted, taken:** the order case's comment; the key-shape caveat on 342 and 360; form-not-markdown's two unread files hold a failing change (preconditions added).
- **Review B, blocking:** test_r014_conditional_file_not_utf8_stops_the_check has a readable failing file beside the unreadable one: reported while the file is UTF-8, not once it is not. The driver has the mutant "readable files checked after an unreadable one".
- **Drivers:** mutate_workflow_check.py 198 of 198 killed.
- **Records:** HARDENING (the triage corrected, the gate round 1 paragraph), PROJECT_STATUS (r2 on the increment line).

BUG-007 is the supervisor's own branch. It holds tests, fixtures, two sentences of registry text and one rewording, and the records. No builder ran. No program under bridge/ changed except MANIFEST.json, which tools/make-manifest.py regenerated for extension-points.md (VERSION unchanged).

## What it answers
Stage B2's review, round 6, ran on the stage's whole change (origin/main 6b51ccd).
- Review A ran in eight parts:
  - tests: REJECT (5 blocking, 7 should-fix, 8 consider): a section ending at a prose `##` heading; text or a space after a key, and ADD_FOR's kind read as `.+`; trait order against the highest trait so far; no (e) case among the malformed lines; a missing registry; and should-fix items (non-.md files under types/, a non-UTF-8 conditional file, escaped path fields, a default-root test that cannot fail, an addition at intake.delivery-kind, several findings per input, the judge's line order, the sweep's operators);
  - fixtures 1: REJECT: no fence opening at three spaces; no heading at three spaces;
  - fixtures 2: REJECT: a three-space heading; an empty Set before a prose heading; a leading backtick; non-.md type and sub files; a three-space fence; an unknown-key file's changes still checked;
  - programs, texts, fixtures 3, 4, 5: APPROVE, with should-fix and consider items.
- Converged (blocking): a section ends at a prose heading (tests B1, fixtures 2 B1b); a three-space heading (fixtures 1, fixtures 2); three Workflows lines naming one part (programs, fixtures 3); an unreadable conditional-workflow file untested (programs S, tests S).
- Review B's reply was "APPROVE" naming no file or line of the diff: per the policy a failed launch, rerun with the stage's next round.

The supervisor widened its operator sweep of workflow-check.py (run/supervisor/sweep_workflow_check.py, local, temporary copies) with the operators the tests part asked for: bounds moved by one both ways, numbers compared moved by one, `== 2` read as `>= 2`, a character set made smaller, the error and found appends deleted, every if/elif condition forced true and false, and every `and` clause dropped. It made 756 mutants, 711 compile; 78 survived before this branch, 52 after. Each of the 52 is triaged in docs/HARDENING.md, section "Stage B2 — the stage review (round 6, 2026-10-17)": round 5's list, new equivalents with their reasons, and four held on CI's ubuntu leg only.

## Tests the supervisor wrote or changed, with the paragraph each enforces
- **tests/test_workflow_check.py, FILE_EXACT** (R-014; extension-points.md, "How a conditional workflow names a point"; handoff/TASK-006.md). Each case asserts the check's whole output:
  - **form-empty-set-before-prose** (new): a Set right above a prose heading is empty, at a value point and at intake.delivery-kind;
  - **form-heading-trailing-text** (new): text after the key, a space after it, text after the delivery kind: each is not one of the four forms;
  - **form-indented-heading:** a third heading, indented three spaces; **form-indented-fence-open:** the opening fence now indented three spaces;
  - **form-not-markdown:** non-.md files under types/ and under a type's folder;
  - **form-traits-folder:** a folder named `odd.md` under traits/;
  - **kind-set-value:** a leading backtick only; **kind-two-backticks** (new): two backticks are unwrapped to nothing and printed `-`;
  - **unknown-type-file, unknown-trait-file, d-sub-type-of-another, d-type-file-missing:** each file's changes are still checked, an (a) after its identity finding.
- **The pass root**: an addition at intake.delivery-kind in a trait; `## - notes` and `## ...` are prose.
- **STATUS_EXACT** (R-015; supervisor.md, "Project state"): form-trait-order-highest, form-traits-empty, form-traits-trailing-comma, e-same-part-three, e-same-part-checked, unknown-workflow-name-case (new); the comment on the two name cases reworded (fixtures 5).
- **test_r014_indented_or_tabbed_change_heading_is_form:** three candidates, the three-space precondition; **test_r014_unclosed_indented_fence_is_form:** the three-space precondition.
- **New tests** (round 6 section at the end of the file):
  - test_r014_round6_fixtures_hold_their_controls, test_r015_round6_byte_cases_keep_their_bytes: the texts and bytes the cases depend on, the status open list's rows included;
  - test_r014_four_backtick_fence_and_shorter_tilde_run, test_r014_form_feed_after_a_closing_run_does_not_close (the fence rules in the registry);
  - test_r014_single_dash_separator_cells, test_r014_table_with_only_its_header_has_no_separator (both rule files' "How this file is read");
  - test_r014_registry_missing, test_r014_rule_file_that_is_a_folder_cannot_be_read, test_r014_conditional_file_not_utf8_stops_the_check (the program's exit-2 list; the registry's new sentence);
  - test_r014_path_fields_are_escaped (R-014 output is ASCII, path fields included);
  - test_r014_default_root_is_read_when_no_root_is_given (the program's usage: the default root, and only the status file with --status);
  - test_r014_root_with_a_trailing_slash_prints_one_slash;
  - test_r014_link_among_a_folders_files_is_form (the registry's file and link sentence);
  - test_r014_part_name_ends_at_the_first_colon_space, test_r014_part_with_nothing_after_its_prefix_lacks_the_traits_marker (the part-prefix rule).
- **tests/test_workflows_line_check.py** (R-015; handoff/TASK-008.md): MALFORMED gains "two-types", an (e) case, for both programs; test_r015_inventory_prints_each_finding_in_order; check_placement of a text with neither line is empty.
- **tests/test_extension_points.py** pins the two new sentences, the reworded "A `##` heading other than the four forms is prose", and the paragraph's order exactly (a blank line before it, the term's first use at its own sentence).

## Mutation drivers (run/supervisor/, local; the supervisor's, run on temporary copies)
- **mutate_workflow_check.py:** 196 of 196 killed at round 6 (198 of 198 after gate round 1, the two added in r2); its BUG-007 block names 35 mutants, one or more for each rule above. A link among a folder's files read as a file is left out: on this Windows host the case's link is listed as a folder, so it is held on CI's ubuntu leg only.
- **mutate_workflows_line.py:** 42 of 42 killed (unchanged).
- **sweep_workflow_check.py:** widened as above.

## Files expected in the diff
- tests/test_workflow_check.py, tests/test_workflows_line_check.py, tests/test_extension_points.py.
- Fixtures under tests/fixtures/workflows/, modified and new. Some bytes are deliberate:
  - status/form-traits-empty.md and status/form-traits-trailing-comma.md end their line with a space;
  - fail/form-heading-trailing-text's `## Set at intake.budget-kind ` ends with a space;
  - fail/form-not-markdown/types/host-extensionabc has no extension; fail/form-traits-folder/traits/odd.md is a folder.
- bridge/cursor-bridge/workflow/extension-points.md: the four-forms sentence, the reworded prose-heading sentence, the UTF-8 sentence.
- bridge/cursor-bridge/MANIFEST.json (regenerated).
- docs/HARDENING.md (the round-6 section; round 5's 89 survivors placed in time) and docs/PROJECT_STATUS.md (records).
- run/review/ (these review files).

## Out of scope
- Every program under bridge/cursor-bridge/ (*.py). The leads (626; the program's usage text not naming an unreadable conditional file) are recorded for the next change of the check.
- CI configuration.
- Design for later stages.
