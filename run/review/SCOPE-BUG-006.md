# SCOPE — BUG-006 (stage B2 review, round 5), gate round 4

BUG-006 is the supervisor's own branch. It holds tests, fixtures, registry and open-list text, and the records. No builder ran. No program under bridge/ changed except MANIFEST.json, which tools/make-manifest.py regenerated for the two rule texts (VERSION unchanged).

## Gate round 4 (commit 565cf41; the change since the reviewed head 64c0a13 is run/review/DELTA-BUG-006.diff)
Gate round 3 ended with Review B APPROVE and Review A REJECT (1/0/3). REVIEWERS DISAGREED on whether the heading shape needed stating. That is a correctness question, and the supervisor decided for Review A: its mutant `HEADING_CANDIDATE = re.compile(r"^ {0,3}##(?:[ \t]|$)(.*)$")` survived every test.
- **Registry text** (extension-points.md, "How a conditional workflow names a point"): one sentence, "A `##` heading is a line of at most three spaces, then `##`, then a space or a tab; a line of `##` alone is not one and is read as text." It states workflow-check.py:78 (HEADING_CANDIDATE) and is pinned in tests/test_extension_points.py.
- **New case** fail/kind-bare-hashes (FILE_EXACT, R-014 and that sentence): `## Set at intake.delivery-kind`, then `##` alone, then `installer`. The line of `##` alone is the Set's first non-blank line, so the check gives exactly `FAIL (kind) …: ## - Set at intake.delivery-kind is not one delivery kind`. ROUND5_PRECONDITIONS holds the fixture's three lines.
- **docs/HARDENING.md:** the gate-round-3 record, and the round-5 registry paragraph names the shape.
- **Review A's notes, recorded and not changed:**
  - the local driver's blocks run newest-first;
  - the round-1 text below says "after it 44 survive", which is unrelated to the 44 mutants that do not compile;
  - Review A did not rerun the sweep independently. The supervisor reran it after r4: 36 survivors of 381 compiling, 44 not compiling, unchanged.
- **Drivers:** mutate_workflow_check.py 161 of 161 killed, the new mutant included.
- **Suite:** 1299 passed, 23 skipped.

A reading of a line of `##` alone as an empty heading, as Markdown does, would be a program change, and none is made here.

## Gate round 3 (commit a85bbf2; the change from b754143 to 64c0a13)
Gate round 2 ended with Review A APPROVE (0/1/4) and Review B REJECT. Everything both raised is taken here:
- **Review B, the rule texts:** r2 wrote "before the next `##` heading" in both "How this file is read" paragraphs. parse_table stops only at a line starting `## ` (workflow-check.py:213) and reads past `##`+tab and a bare `##`. Both files now say "before the next line that starts with two hashes and a space (`## `)", and the pins in tests/test_extension_points.py and tests/test_open_list.py follow.
  - New case test_r014_table_reader_reads_the_first_table_after_its_heading[hashes-without-space] (both rule files' "How this file is read"): prose, `##`+tab and a bare `##` lie between the heading and its table, and the table is still found.
  - test_r014_table_reader_stops_at_the_next_section is unchanged in code; its docstring now names the `## ` line.
  - The driver's mutant `startswith("## ")` → `startswith("##")` is killed by the new case.
- **Review B, the sweep's count:** the 44 mutants that do not compile were counted as killed. sweep_workflow_check.py now compiles each mutant first and counts a non-compiling one apart. Result: 36 survivors of the 381 that compile, the same 36 lines as HARDENING's list. HARDENING's figures say so (the intro's 89 is "of those that compile").
- **Review A (should-fix):** HARDENING's equivalent range now reads "625, 627 to 641"; 626 is a lead only.
- **Review A (considers):**
  - extension-points.md's failing-paths sentence names "a `types` or `traits` path that is itself a file or a link" (workflow-check.py:316-321), with the pin updated;
  - HARDENING's intro says 313 and 322 moved;
  - the local driver's block headers are in order.
- **Drivers:** mutate_workflow_check.py 160 of 160 killed.
- **Suite:** 1297 passed, 23 skipped.

## Gate round 2 (commit 48c791e; the change from 62dfd10 to b754143)
Gate round 1 ended Review B APPROVE and Review A REJECT. Review A's blocking finding was that the round-5 survivor list in docs/HARDENING.md called separable rules equivalent or untestable; it separated each one with one input. The supervisor decided for Review A, and every finding below is taken. The new cases, each with the paragraph it enforces:
- **test_r015_separators_are_exact[space-before-comma]** (handoff/TASK-006.md R11.4, "each name stripped"): `Host Extension Development , Installable` finds the type, and only the shape fails. The comment above the assertion now names this mutant (sweep line 605).
- **test_r014_set_changes_cell_is_split_on_commas_and_stripped** (TASK-006, the `set` finding: "split on commas and stripped"): a registry copy whose cell reads `set , add` gives RESULT: OK on the pass root; `add` alone gives the exact (set) line (sweep line 285).
- **test_r014_unreadable_file_names_the_systems_reason** (TASK-006: `<reason>` is plain-language text): read_utf8 with `open` refused gives `cannot be read (Permission denied)` (sweep line 126).
- **test_r014_folder_that_cannot_be_listed_is_named_with_its_reason** (R2-3 and `<reason>`): with os.scandir refused for one folder, the ERROR line names that folder and the system's reason, on every host (sweep lines 299 and 300).
- **test_r014_layer_that_cannot_be_examined_stops_the_check**, last assertion: the exact `ERROR: <root>/<layer>: Permission denied` line, not the fallback (sweep line 312).
- **test_r014_links_are_not_followed** (R2-4): the whole output. It adds a link inside a folder that is no product type, so each link is named under its own path (sweep lines 349 and 354).
- **Text, each with a pin:**
  - extension-points.md and open-list.md, "How this file is read": "and before the next `##` heading" (Review A's should-fix: the table reader stops at the next section, as test_r014_table_reader_stops_at_the_next_section holds);
  - extension-points.md: "the section's first non-blank line, stripped";
  - extension-points.md: the failing paths named exactly ("a file or link under `types/` or `traits/` …; a folder under `traits/` or inside a type's folder; and a folder under `types/` that is no product type");
  - open-list.md: "No name is `none` or `not yet classified` …".
- **docs/HARDENING.md:** the survivor list corrected (36 of 425 after the sweep, each placed in a class), 626 restated as a lead (a possible missing (f), per TASK-006 R4), and the gate-round-1 record.
- **Drivers (local):**
  - mutate_workflow_check.py: 159 of 159 killed; eight new mutants, one per case above;
  - the sweep now runs test_extension_points.py as well: 36 survivors of 425, exactly the list's.
- **Suite:** 1296 passed, 23 skipped.

The scope of round 1 follows unchanged.

## What it answers
Stage B2's review, round 5, ran on the stage's whole change (origin/main 0e7813e).
- Review A ran in seven parts:
  - fixtures 1: REJECT, blocking: a closing fence indented four spaces had no control;
  - tests: REJECT, blocking: a sub-workflow file whose key is no sub-type had no case;
  - fixtures 2, 3, 4: APPROVE, with should-fix items;
  - programs and texts: APPROVE, with considers.
- Two reviewers converged: tests and fixtures 4 both found that `not yet classified` is matched only exactly by the code and never by a test.
- Review B's reply carried no verdict, only a should-fix: the registry's fence sentence omits the backtick-info exception. Per the policy that is a failed launch, rerun with the stage's next round. Its finding is taken here.

To catch the whole class rather than wait for reviewers to name each rule, the supervisor ran an operator sweep of workflow-check.py (run/supervisor/sweep_workflow_check.py, local, temporary copies). It produced 425 mutants. Before this branch 89 survived; after it 44 survive. Each of the 44 is triaged in docs/HARDENING.md, section "Stage B2 — the stage review (round 5, 2026-10-17)". The classes are:
- equivalent;
- a message fallback;
- held only on CI's ubuntu leg;
- one unreachable line;
- three recorded leads.

## Tests the supervisor wrote or changed, with the paragraph each enforces
- **tests/test_workflow_check.py, FILE_EXACT** (R-014; extension-points.md, "How a conditional workflow names a point"; handoff/TASK-006.md). Each case asserts the check's whole output:
  - **fence-indented-close:** a closing run indented four spaces is content, so the fence stays open.
  - **fence-four-spaces:** a four-space heading is prose, and two backticks or two tildes open no fence. The Set after them is read.
  - **form-misspelt-change-word**, 11 headings: each change word without `at` (Adds, Added, Sets, Replaces, Replaced), a two-word heading ending `at`, and `AT` in capitals.
  - **form-change-word-punctuation**, 10 headings: each stripped mark (. ; , - :) and two marks together.
  - **d-unknown-sub-type-key** (new): a sub-workflow file whose key is no sub-type of its type gives a (d) finding.
  - **c-not-replaceable:** two different modules replaced in one file; each is judged.
  - **form-traits-folder** (new): a folder under `traits/`.
  - **d-unknown-type-folder:** a folder inside an unknown type folder is not reported on its own.
  - **kind-on-another-point:** an unlisted kind named on another point gives both kind lines.
  - **kind-set-value:** a value with a backtick on one side only is not unwrapped.
- **The pass root** (pass/types/host-extension.md, pass/types/host-extension/claude-code-extension.md), held by test_r014_pass_root_holds_its_only_cases and test_r014_round5_fixtures_hold_their_controls:
  - an indented `    ## Replace design` and an empty `## ` heading are prose;
  - a Set value right under its heading, with spaces around it and prose after it, is its first non-blank line, stripped.
- **tests/test_workflow_check.py, STATUS_EXACT and test_r014_status_ok** (R-015; supervisor.md, "Project state", the `Workflows:` grammar):
  - form-unclassified-with-traits, -case and -trailing-space: only the exact `not yet classified` is the unclassified form;
  - form-no-line: an indented or lower-case `Workflows:` line is not one;
  - form-trait-order-three and form-trait-repeat-separated: order and repeats beyond neighbouring traits;
  - unknown-type-name: a product type's Name is not a workflow name;
  - unknown-sub-type-name: a sub-type's Name in another case;
  - form-traits-double-space and form-traits-none-case: traits spacing and `None`;
  - ok-no-final-newline: a file with no final line feed that starts with a blank line passes.
- **test_r015_separators_are_exact** asserts each head separator case's whole output.
- **test_r014_round5_fixtures_hold_their_controls** (new): each round-5 fixture holds the text that makes it a control.
- **test_r015_byte_cases_keep_their_bytes** (new): the trailing space and the missing final line feed are kept as bytes.
- **test_r014_escape_field_at_each_width_boundary** (new; R-014 output is ASCII): tab, DEL, U+0080, U+00FF, U+0100, an arrow, U+FFFF and U+10000.
- **test_r014_table_reader_reads_the_first_table_after_its_heading** (new; open-list.md and extension-points.md, "How this file is read"):
  - a blank line, or none, between the heading and its table;
  - alignment colons;
  - rows without a trailing pipe;
  - a table with no row;
  - the heading given twice;
  - a prose line ending in a pipe.
- **test_r014_table_reader_stops_at_the_next_section** (new): a heading with no table before the next section is an error.
- **tests/test_extension_points.py** pins the three new registry sentences (the section span; the fence rules; the other failures). The delivery-kinds test now reads every kind the list names, however it is described (`r"`([a-z0-9-]+)` \("`), and pins the `DELIVERY_KINDS` sentence.
- **tests/test_open_list.py:** no open-list name is `none` or `not yet classified` (R-015: those words are the grammar's own).

## Mutation drivers (run/supervisor/, local; the supervisor's, run on temporary copies)
- **mutate_workflow_check.py:** 151 of 151 killed. Its BUG-006 block names a mutant for each rule above.
  - Two older mutants, "head segments stripped" on the left or the right only, were removed as equivalent: the head's names are stripped again after the split.
  - "kind on another point accepted" now targets the exact-output case.
- **mutate_workflows_line.py:** 42 of 42 killed (unchanged).
- **sweep_workflow_check.py:** an operator sweep, with every survivor a test or a line in HARDENING with its reason.

## Files expected in the diff
- tests/test_workflow_check.py, tests/test_extension_points.py, tests/test_open_list.py.
- Fixtures under tests/fixtures/workflows/: the ones named above, modified and new. Some bytes are deliberate:
  - status/form-unclassified-trailing-space.md ends its line with a space;
  - status/ok-no-final-newline.md has no final line feed;
  - fail/d-unknown-sub-type-key's `claude-code-extention.md` is misspelt on purpose.
- bridge/cursor-bridge/workflow/extension-points.md: the three sentences replacing the fence sentence, and the `DELIVERY_KINDS` clause.
- bridge/cursor-bridge/MANIFEST.json (regenerated).
- docs/HARDENING.md (the round-5 section; TASK-024 line numbers; the round-4 claim corrected; routing of the empty-Replace lead) and docs/PROJECT_STATUS.md (records).
- run/review/ (these review files).

## Out of scope
- Every program under bridge/cursor-bridge/ (*.py). The sweep's leads (83 `\s*$`, 485 `> 2`) and the unreachable line 548 are recorded for the next change of the check, not changed here.
- CI configuration.
- Design for later stages.
