# Hardening

Leads the gate drew a line under, and the parts of each stage the supervisor is least sure of, each with the check that would settle it. The next stage's refactor-scout reads this file first. A lead a test can settle becomes a test before the next stage's first delegation.

## Stage B1 — supervised-project bootstrap

### Least confident (stage close, 2026-10-16)
1. **The floor's teeth against a real bad dependency.** OSV-Scanner and Socket have run green on the real lockfile, but neither has been seen to fail: no planted known-vulnerable or known-malicious pin has been put through them (Semgrep's teeth were proven with a planted SQL-concat fixture in TASK-002 r2). Check: a throwaway pull request pinning a version with a published advisory in requirements.lock must turn `security floor` red at the OSV step, and one adding a package Socket flags must turn it red at the Socket step; close the pull requests unmerged and delete their branches.
2. **The runner image change.** `ubuntu-latest` is to move to the next Ubuntu image (2026-10-19 by a reviewer's reading during TASK-002, not yet confirmed against GitHub's runner-images notice); the Semgrep step relies on `pipx` being on the image and Node 22 from setup-node. Check: the first `security floor` run after 2026-10-19 shows the Semgrep step running `pipx run semgrep==1.176.1` and the Socket step scanning; if pipx is gone the step fails red (it cannot pass silently, the tests pin its last line).
3. **What Socket's scan actually covers.** The supported-file list shows `requirements.lock` matches, and the scan reports "Found 3 files", unnamed. Check: open the scan of the next `security floor` run in the Socket dashboard (latent-foundry) and confirm pytest, pyyaml and their closure are listed, and which other two files were read.

### Leads (stage B1's review, 2026-10-16)
- The Semgrep rule packs `p/python` and `p/secrets` are fetched from the registry on every run; only the engine is pinned. An upstream rule change can turn an unrelated pull request red or drop coverage unseen. Settle: vendor a dated copy of the two packs into the repository, or accept the drift as a Decision.
- `npm install -g` of the Socket CLI resolves its transitive dependencies afresh on each run (24 packages, no lockfile for a global install). BUG-001 closed the install-time exposure only: whatever of them the CLI loads runs inside `socket ci`, with `SOCKET_CLI_API_TOKEN` in that process's environment, so an unpinned dependency is a risk of BUG-001's kind at scan time. Settle: install the CLI from a committed package-lock in a tool folder (`npm ci --ignore-scripts`), or record the drift as an accepted Decision with its reason; the first changes `test_r002_no_install_runs_beside_a_secret`'s pin, which reads the version on the install line, in the same increment.
- The structural CI test pins the whole workflow verbatim (BUG-001 rounds 5 and 6); its pattern checks remain as a second line that explains what a change breaks, and do not model every install form (pnpm or yarn installs have no script check; an npm option whose value starts with `-`). They matter only when the pin is regenerated: the reviewers of that diff read the workflow change itself.
- The workflow pin is compared through PyYAML, which reads YAML 1.1; GitHub's parser differs on some spellings (`true:`/`yes:`/`On:` for `on:`, a `<<:` merge key, a duplicated key, `off`/`no` for a boolean, `00` for a number), which parse to the pinned values here (BUG-001 round 6, Review A). In each case worked through, the scanners behave the same or GitHub refuses the workflow, so the required checks never report and the merge is blocked. Settle: a throwaway pull request with each spelling, closed unmerged; or compare the raw text as well as the parsed form.
- The scanners' own configuration files (`osv-scanner.toml`, `socket.yml`, `.semgrep.yml`, `bridge/cursor-bridge/semgrep-bridge-rules.yml`, which the workflow passes to Semgrep with `--config`, a new `.semgrepignore`) sit outside the workflow pin; any could narrow a scanner to nothing with every test green (BUG-001 round 6, Review A; main has the same gap). Settle: pin their hashes in the structural test, so a change to one changes the test in the same diff.
- The structural tests guard the merge, not the run: a same-repository pull request that adds a workflow or edits `tests.yml` runs it on its own CI run, with the repository's secrets available, before any test can fail (PR #22, Review A; true on main before). Settle: put SOCKET_SECURITY_API_KEY in a GitHub Environment with required reviewers, or supply it only on pushes to main; either is a change to how the owner's key is reached, so it comes with its run sheet. The cost of each (PR #22, Review A): on pushes only, a pull request's Socket step runs without the key, so it must be skipped there and the required check changes shape; with an Environment, every pull request's CI waits for an approval click.
- The full-tree Semgrep audit (2026-10-16, one accepted finding) is a point-in-time result; diff-aware scans never see code a pull request does not touch. Re-run it at each release (recorded in INVENTORY Decisions).
- The repository secret SEMGREP_APP_TOKEN is stored but unused (OSS engine); the owner could delete it and revoke the token (least privilege; not a defect).

## Stage B2 — carried to its close (test lane)
- Done on BUG-002 (stage B2's review fixes), not in the refactoring pass, whose test lane only consolidates: tests/test_open_list.py pins "filled, including" and its comment at :25 is corrected (TASK-004 r3 Consider); tests/test_extension_points.py pins the configuration.items CI route, the inspect step's members and the placement sentence (TASK-005 r6 Consider).

## Stage B2 — TASK-006, the workflow check (by-class line, review round 3)
- A change word wrapped in markup or joined by another character is still prose: `## **Set** intake.x`, `` ## `Replace` design ``, `## Set:at intake.x`, `## Set` with an em dash. Strip leading and trailing `*`, `_`, backticks and any dash before the comparison (Review A, round 3 Consider 2; the tail of heading parsing, low likelihood).
- Every reparse point counts as a link on Windows (one `os.lstat` rule on every Python since round 5): OneDrive placeholders and deduplicated files under `types/` or `traits/` fail as `form`. Fail-closed by design; a workflow folder is not expected in a synced folder (Review A, round 3 Consider 3, settled for version dependence by R5-2).
- Container blocks are not modelled: a fence opened inside a list item stays open for the check after Markdown ends the item, a heading inside a block quote or list item (`> ## Set at x`, `- ## Set at x`) is not a heading candidate, and a fence line inside any HTML block (types 1 to 7: `<pre>`, `<div>`, `<!-- -->`) is read as a fence; each can hide a change heading Markdown displays. A fail-closed rule (a container marker before `##`, or an indented fence followed by a less-indented line, as `form`) would close most of it (the security auditor rounds 4 and 5, Review A round 5 Consider 2; converged, and both graded it for recording; the tail of heading parsing).
- Line-break characters Markdown does not end a line at (vertical tab, form feed, `\x1c` to `\x1e`, NEL, U+2028, U+2029) are now inside a line for the check, as for Markdown, so `prose<FF>## Set at x` or `note<FF>Workflows: …` is not read, where a raw-text reader would see a line; reporting any such character in a types/, traits/ or status file as `form` would close it both ways (Review A, round 6 Consider).
- Table cells are trimmed with `str.strip()` (any Unicode whitespace); Markdown trims spaces and tabs only, so a separator followed by a form feed, NEL, U+2028 or a no-break space is accepted where Markdown shows no table; trim `" \t"` only (the security auditor, round 6).
- An escaped pipe (`\|`) inside a cell is split as a cell boundary; the tables' own rule says no cell contains a pipe, which the check does not enforce (the security auditor, round 6).

## Stage B2 — TASK-008, the Workflows line enforced
- conformance-check.py reads an existing but unreadable docs/PROJECT_STATUS.md as empty text, so its Workflows line row says "missing" where "not checked" would be exact; the row is MISSING either way and the verdict is the same (the builder's assumption, accepted at the accept commit).
- `judge_workflows_line` is written twice, identically, in inventory-check.py and conformance-check.py; a lead for stage B2's refactoring pass (one shared helper beside workflow-check.py). Closed at the pass, kept on purpose (refactor-scout, 2026-10-17; Review A of the pass): of its roughly forty code lines, about fourteen load workflow-check.py by path with no bytecode and fail closed, and the rest judge the line (read the rules, load_tables, check_status, check_placement, the outcome). A new shared file would need that same guarded loader in each program to load it, for about ten lines saved, against a new installed file, its manifest entry and three new not-loadable cases per program. Moving the judging into workflow-check.py itself, which both programs already load and the manifest lists, has none of those costs, but it changes a tested failure: with escape_field missing from the checker, the not-loadable cause would read NameError where it reads AttributeError today (tests/test_workflows_line_check.py, no-escape-field), and a refactoring pass carries no behaviour change. A lead for a later change to these programs: the judging in workflow-check.py, the two programs keeping the loader and one call, the case's expected cause changed with it; until then a change to one copy is made to both, or the divergence is recorded as intended. TASK-024's Scope holds conformance-check.py but not inventory-check.py, and it reports a line naming an unwritten workflow, findings both copies drop today: its brief either widens its Scope to inventory-check.py where the judge changes, or records the conformance copy's divergence as intended (Review A, round 2 of the refactoring pass). The pass's second candidate, one `load_rules` function in workflow-check.py for the rule-reading block written in main, both judges and a test helper (about ten net lines), was dropped: its payoff is the place a third rule file would be added, a reuse that no planned increment needs.
- Names and reasons echoed from a status file can carry text such as `RESULT: OK` or `RESULT: CONFORMANT` inside one output line (`WORKFLOWS LINE: malformed: RESULT: OK - not a trait name`); no line can be forged, since every field is escaped. Readers of either program take the verdict from the exit code or the last line, never from a search of the whole output (the security auditor, round 1).
- `Workflows: not yet classified` passes both programs at any phase; nothing forces classification after intake. By design: intake classifies a new project, calibration adds the line to a running one (TASK-023); a check that the line is classified past intake would close it (the security auditor, round 1, out of lane).
- Loading the checker writes no bytecode since round 2, but a `__pycache__/workflow_check.*.pyc` already in the bridge folder would still be read in place of the source the manifest verifies; the same class as the bridge's other module loads, and it needs write access to the bridge folder (the security auditor, round 1).

## Stage B2 — TASK-009, the glossary's terms
- Other texts still use "phase" in the module sense the glossary now separates from the `Phase:` value: workflow/extension-points.md's "Phase" column (its values include Run parameters, Reflection points, Definition of done and Delivery); supervisor.md's "Main and conditional workflows" calls each phase module "the procedure for one phase" and says a replacement is allowed "where the phase declares" it, where the registry marks the module replaceable; its opening sentence says conditional workflows change the main workflow "only at the extension points", the layer table's Type workflow row says "its changes at named extension points", and the inheritance paragraph says a sub-workflow "changes only what differs, at the same extension points", where a replacement targets a whole module. workflow/open-list.md's procedure for adding a conditional workflow says it names "what it adds, replaces or sets at each" extension point (step 2). The glossary's Phase module entry names "the interface phase", not a `Phase:` value, and Glossary.md is in neither increment's scope: when those texts are renamed, the glossary follows in the same change. Routed by file (Review A round 6 and its review of the refactoring pass): supervisor.md's sentences go to TASK-010 (the carve), whose Done when is a verbatim move under the traceability comparison, so its brief carries the rewording as an added requirement, with `reword` entries in trace-exceptions.md; open-list.md's step 2 to TASK-017, the first increment with open-list.md in scope; extension-points.md's Phase column and the glossary's "the interface phase" to TASK-010's brief, which widens its Scope for the rename to extension-points.md, Glossary.md and tests/test_extension_points.py (which asserts the column's header and values; workflow-check.py does not read it), the widening recorded when the brief is written (Review A rounds 2, 3 and 6, Review B round 3).

## Stage B2 — the stage review (round 1, 2026-10-17)
- A project's parts have no declaration besides the status file's own `Workflows:` lines, so a part whose line is left out is not detected (Review B, blocking; decided by the supervisor as design for later: the plan's §7, product aggregates, gives a project several parts with `Parts\<part>` clones and an aggregate design; the check that every declared part has its line belongs to that release).
- TASK-010's brief carries, beside the TASK-009 lead's rewordings: the core cites the registry's `project` Applies exception (extension-points.md's Applies entry asks for it; the core's order paragraph states the per-part rule without it), and its Scope widens to tests/test_workflow_model.py, which pins the phase headings, the until-the-carve sentence and the layer table's module row that the carve moves.
- A type workflow's or sub-workflow's statement of its default traits has no form and no check (open-list.md now says so). The first increment whose type workflow states default traits (TASK-019 is the first type workflow) gives the statement a form and adds the check; its brief widens its Scope to workflow-check.py and tests/test_workflow_check.py, and the fixture open list's Default traits (tests/fixtures/workflows/status/open-list.md: web-app, local-web-app) are brought into line with the real list then.
- Where a resumed or compacted session re-reads a phase module (on entering the phase and at calibration, against the core's start, resume and calibration, and the compaction-survival list) is said three ways; TASK-015, which makes the hook name the modules, settles it in one sentence.
- workflow-check.py trusts the Written flag; test_open_list's invariant (Written is `yes` exactly when the file exists at the key's path) guards the bridge's own list, and each increment that writes a workflow runs it.
- tests/test_workflows_line_text.py judges the bridge's status line with a grammar checker of its own (TASK-007's proof that the grammar is coherent); it accepts spacing check_status refuses. The shipped check is the authority; a lead to retire the private one when TASK-010 moves the paragraph.
- test_r033_ci_runs_the_check_last_in_the_tests_job requires the workflow check to be the tests job's last step; a later CI step goes before it.
- tests/test_open_list.py bounds open-list.md at under 300 lines and 30,000 characters; TASK-017 to TASK-021 all add to it, so their briefs check the headroom.
- The failing-fixture tests assert the named finding and that the RESULT count agrees, not the number of findings, so a second defect added to a fixture later would pass unseen; and a misspelt type (status/unknown-name.md) also gives a follow-on (e) "part must name exactly one product type". [Closed by BUG-003 and BUG-004: every case's whole standard output is asserted, RESULT line included.]
- inventory-check.py prints a traceback when `--status` names a folder (its pre-release-B `read()`); the exit is still non-zero.

## Stage B2 — BUG-002, the stage review's fixes
- Carried to stage B2's reflection (item 3): the per-part completeness lead above goes also into the Restructuring Plan's §16 follow-up lists, where the aggregate release is planned (Review A, BUG-002 round 1).
- TASK-019's brief is packaged with the default-traits line above (form, check, Scope widening, fixture open list); BUILD_PLAN's TASK-019 entry does not repeat it (Review A, BUG-002 round 2).
- One failing fixture now has its exact findings asserted (`form-trait-in-head.md`, test_r014_trait_in_head_is_only_the_shape_finding); the lead above on the others (the named finding and the count, not the number of findings) stands. [Closed by BUG-003: every case's whole output is asserted.]

## Stage B2 — the stage review (round 2, 2026-10-17)
- Taken on BUG-003: every failing root and status case asserts its whole output (three fixture parts converged on cases that a second finding could hide); new cases for a valid sub-workflow's changes (Review B, blocking) and for the part-name rules in a file of several lines (Review B and fixtures part 3, converged); the output is ASCII on every console and a `types` or `traits` path that is a file is (form) (Review B; the builder's part); the placement and part-name sentences of supervisor.md's Workflows paragraph (texts part; the placement wording had been routed to TASK-010); the open list states that a part fitting a sub-type takes it and that the names a `Workflows:` line reads are unique across the tables (texts part).
- Review B's round-1 blocking item (an omitted part's line) still holds as the aggregate release's, Review B agreeing in round 2.
- TASK-024 (conformance-check reports an unclassified line or one naming an unwritten workflow): tests/test_workflows_line_check.py (the conformance halves at :333, :378, :388 and :416, the last the no-status test's positive control; line numbers of 2026-10-17, stage B2 review round 5) and tests/test_conformance_check.py (the conformant baseline at about :69 and :104-109) pin today's `Workflows line` OK for those lines; the supervisor's tests for TASK-024, written before its delegation, re-pin them to the report TASK-024 adds, and its brief names both files (tests part).
- The default-traits line above also widens TASK-019's Scope to tests/test_open_list.py, which pins open-list.md's "No form for that statement exists yet" sentence (tests part).
- TASK-010's brief checks which of these read the paragraphs it moves or rewords, and widens its Scope to those it changes: tests/test_workflows_line_text.py (the Workflows paragraph), tests/test_open_list.py (the r034 order paragraph), tests/test_glossary_terms.py (the `Phase:` template); the private grammar checker lead above is not tied to TASK-010, whose Done when keeps project state in the core (tests part).
- TASK-017's brief checks tests/test_open_list.py's pin of step 2's second sentence when it rewords step 2's first (tests part).
- workflow-check.py reads a status file as strict UTF-8 and stops (exit 2); inventory-check.py and conformance-check.py read it with replacement and judge the line, so invalid bytes outside the `Workflows:` line give different outcomes; bytes inside it are refused by all three (programs part, noted).
- inventory-check.py prints its `--status` argument with only non-ASCII escaped; a control character in that operator-given path prints raw (programs part, noted).
- "Part" has no glossary entry; the term belongs to the plan's §7 and enters the glossary's closed set with the aggregate release (texts part, consider).

## Stage B2 — BUG-003, round 2's fixes
- workflow-check.py's `escape_field` keeps a literal backslash, so a name that contains the four characters backslash, x, e, 9 prints exactly like a name holding é (escaped as backslash-x-e-9), and the text backslash, x, 0, a like an escaped line feed; no line or RESULT can be forged (the field never holds a raw line break). Escaping the backslash itself would depart from the agreed escape forms (those of Python's backslashreplace) and change what inventory-check and conformance-check print; no current fixture holds a literal backslash, so no exact-output entry would change (the entries' backslashes are escapes, such as form-part-arrow.md's arrow). A lead for a later change to the check's output (security auditor, BUG-003, advisory; the cost restated at round 3).
- `collect` records a layer path that is not a folder with the kind `link`, which gives the required line today; recording it as `file` gives byte-identical output and keeps the label true if link handling ever gets a reason of its own, and the docstring would then name it (Review A, BUG-003, consider).

## Stage B2 — the stage review (round 3, 2026-10-17)
- Taken on BUG-004 (the supervisor's tests, fixtures and two open-list sentences): with no status file, inventory-check's note and a normal end are asserted and conformance-check is tested not to judge the line (tests part, blocking); the exact-case tests compare the whole standard output with the RESULT line and an empty standard error (Review B); roots and status files are tested in argument order, roots first (tests part); a whitespace-only Set section and a fence closed by spaces and a tab (fixtures part 1); presence checks for the pass root's deeper heading and backticked Set value (fixtures part 2); a traits marker given twice (fixtures part 3); a key where a name belongs, for a trait and for a product type (fixtures part 4); a lone trait as the head (tests part); the two no-carriage-return assertions read the text with newline translation off (`newline=""`) and refuse a lone carriage return (tests part); the open list says no name a `Workflows:` line reads contains `,`, `;`, `:` or the arrow, and the pause rule names an unwritten sub-type (texts part).
- workflow-check.py accepts a table separator of single dashes (`|-|-|`), which Markdown accepts too; the open list's own separators use three. A lead if the tables' reader ever needs to be stricter than Markdown (Review B, consider).
- `check_sub_identity` tests the type file with `os.path.isfile`, which follows a link, so a `types/<key>.md` that is a link satisfies a sub-workflow's (d) test while the link itself is reported (form); the run fails either way (programs part, consider).
- workflow-check.py run alone (`--status`) does not check placement; only inventory-check and conformance-check do (TASK-008 Requirement 1). TASK-011's intake module must not say intake checks the line's placement (programs part, noted).
- TASK-010's rename list (the TASK-009 lead above) also takes extension-points.md's prose that uses "phase" for a module: "replaces a phase not marked replaceable", "A point's phase is replaceable", "may replace the phase with its own" (texts part, consider).
- TASK-017's rewording of the procedure also takes step 4's "running projects of that product type", which should name a sub-type or trait too (texts part, consider).
- TASK-011 names where the delivery kind confirmed at intake is recorded (extension-points.md says it is recorded by its key; no field holds it yet), and TASK-019's brief says which delivery-kind key the local web app's `Set at intake.delivery-kind` uses (open-list.md's "delivered by an installer" is a plain word, the key `installer` is a desktop application's kind) (texts part, noted).
- form-part-empty.md and form-prefix-missing.md print the same finding (`- - Workflows line breaks the part-prefix rule`), so an operator cannot tell which rule broke; a lead for the check's wording (fixtures part 3, consider).
- tests/test_workflow_check.py's FILE_CASES and STATUS_CASES are now covered by FILE_EXACT and STATUS_EXACT, which alone are forced to list every case; a new case is added to the exact tables and need not be added to the older ones (tests part, noted).
- Beside the separators open-list.md now forbids, one value is reserved, by its position: a trait Name `none` would be read as "no traits" (workflow-check.py's check_traits), so the increment that adds a trait checks its Name is not `none`. `not yet classified` reserves no name: only a line whose rest, after the part prefix where several lines carry one, reads exactly that is skipped, and a classified line always carries `; traits: `, so its head is read (BUG-004, Review A consider; corrected in its round 3, Review A and Review B).
- The repository has no .gitattributes: with core.autocrlf the Windows checkout holds CRLF and CI's ubuntu leg LF; the programs and the tests read with universal newlines and the BOM checks read bytes, so both pass (several parts, noted).

## Stage B2 — the stage review (round 4, 2026-10-17)
- Taken on BUG-005 (the supervisor's fixtures, tests and text): a control for the fence rules then named (corrected in round 5: it was not each rule; a closing run indented four spaces had none, and the supervisor's operator sweep found more), a backtick fence with an ordinary info string hiding a heading beside the refused one, a fence closed by a longer run, a shorter tilde run that does not close (fixtures parts 1 and 2, converged as one class: fixture coverage of the fence rules); a multi-part status file with a part prefixed `not yet classified` (fixtures part 4: a mutant refusing it would refuse a valid project at intake); a part name with a leading space and with a tab, a trait with a trailing space, a sub-type's key where its name belongs (fixtures parts 3 and 4); the unknown type folder's file holds a change the check would refuse with (a) if it read the file (fixtures part 1); presence checks for the pass root's sub-workflow Set, its repeated Add at, its two delivery kinds and a sub-workflow's Replace of a module its type replaces (fixtures part 2); conformance-check says nothing about the line when the status file is absent, under any name, and the delivery-kinds test reads its paragraph only (tests part); the registry states which headings are read as change headings and that a file sets a point, and replaces a module, at most once, and no longer says workflow-check.py checks the modules' declarations (TASK-014's cross-check is its own test); the open list pauses a part that fits two sub-types of its type equally; the core's Add list reads "such as" (texts part).
- A change heading at level 1, at level 3 or deeper, or in Setext form is prose to the check (TASK-006's R7), so `# Set at intake.x` or `### Replace interface` changes nothing and is reported as nothing. A fail-closed rule (such a heading whose first word is a change word, or whose second is `at`, is `form`) would close it; it belongs with TASK-006's heading-parsing leads above, beside the container-block lead (a change heading inside a block quote or a list item is unseen too: programs part, round 5), and the reverse case, a change heading inside an HTML comment, is read and fails closed (programs part, consider).
- A one-line status file with a tab beside the traits marker (`Workflows: Web App Development;<TAB>traits: none`) is reported as "Workflows line breaks the part-prefix rule" (the `: ` after `traits` is read as a part prefix, which a one-line file may not carry), a reason that names neither the tab nor the marker on a file that has no parts; "must contain '; traits: ' exactly once" appears only when the tab follows the colon or the file has several parts. A lead for the check's wording, with form-part-empty's above (programs part, noted; the message corrected by Review A, BUG-005).
- The exact-output tests assert an empty standard error; a Python warning or another program's message on standard error in the test's environment would fail them without a defect in the check. None occurs on the Windows workstation or on CI; a lead if one appears (round 4, the supervisor).
- review-guard.py verify given an older snapshot's id on the branch compares against that snapshot and reports what changed since (a GATE-INTEGRITY on `.git/config` in round 3, read as a file, no git command run); a warning when the id is not the newest snapshot would have named the mistake. Recorded for the bridge feedback at the reflection (round 3, the supervisor).
- The registry's "How a conditional workflow names a point" now says that a `##` line inside a fenced code block is not a heading (Review A, BUG-005, consider; taken in its gate round 3, TASK-017's Scope not holding the registry).
- One file may replace a module and add at that module's points (the pass root's sub-workflow replaces `interface` and adds at `interface.variants`), and the check accepts it; whether the file's own additions apply to its own replacement is not stated. The first type workflow or sub-workflow brief that writes a `## Replace` settles it in the registry's "How a conditional workflow names a point", its brief widening its Scope to extension-points.md (no planned task names a Replace yet: Review A, BUG-005 round 3); the same brief decides whether an empty `## Replace` section, which the check accepts today, is (form) as an empty `## Set at` section is (texts part, round 5) (Review A, BUG-005, consider; TASK-017's and TASK-019's planned Scopes hold neither the registry nor the core's paragraph).
- test_r015_conformance_no_status_file_no_check refuses the word "workflows" anywhere in conformance-check's output with no status file; a later row naming `.github/workflows` would fail it for its wording, not a defect (Review A, BUG-005, noted).

## Stage B2 — the stage review (round 5, 2026-10-17)

**Taken on BUG-006 (the supervisor's fixtures, tests and registry text, no program change).** Round 5 rejected for the class round 4 had: rules of the workflow check that no test fails for. Rather than wait for each reviewer to find one, the supervisor ran an operator sweep of workflow-check.py: run/supervisor/sweep_workflow_check.py, local, temporary copies only. It made 425 mutants, of which 381 compile, and found 89 of those surviving the workflow-check and Workflows-line tests before that round's cases were written (36 after them, listed below). Every reviewer finding and each sweep survivor that a test can separate now has its case, with exact output.

**Fences and headings:**
- a closing run indented four spaces is content (fixtures 1, blocking);
- two backticks and two tildes open no fence;
- a heading indented four spaces and an empty `## ` heading are prose.

**Change words** (fixtures 1):
- each change word without `at`;
- each stripped mark, and two marks together;
- a two-word heading ending `at`, and `AT` in capitals.

**Set values:**
- a Set value right under its heading, with spaces around it and prose after it, is its first non-blank line, stripped;
- a backtick on one side only is not unwrapped.

**Files and folders:**
- a sub-workflow file whose key is no sub-type (tests, blocking);
- two different modules replaced in one file;
- a folder under `traits/`;
- a folder inside an unknown type folder;
- an unlisted kind named on another point (fixtures 2).

**Workflows lines:**
- a rest only starting as `not yet classified`, or differing from it by case or a space, is read as names (tests and fixtures 4, converged);
- an indented or lower-case `Workflows:` line is not one (fixtures 3);
- trait order and repeats beyond neighbouring traits (fixtures 3);
- a product type's Name, a sub-type's Name in another case, and a traits text with a space before it or `None` (fixtures 4);
- a status file with no final line feed;
- each head separator case's whole output.

**The two rule files' table reader:**
- a table right under its heading;
- alignment colons;
- rows without a trailing pipe;
- a table with no row;
- the heading given twice;
- a prose line ending in a pipe;
- a section with no table.

**Output escaping:** the escape at each width's boundary.

**Mutation drivers:** run/supervisor/mutate_workflow_check.py names a mutant for each of these, 151 of 151 killed at this round (161 of 161 after BUG-006's gate rounds below: 159 at r2, 160 at r3, 161 at r4), and mutate_workflows_line.py stands at 42 of 42.

**Registry text** (texts part; Review B's should-fix): the registry now states that a section runs to the next `##` heading, so a replacement's own structure uses `###`, and (since BUG-006 r4) what a `##` heading is: at most three spaces, `##`, then a space or a tab, so a line of `##` alone is text. It states the fence rules in full (indent, info string, closing run) and what else fails:
- an unclosed fence;
- an empty Set;
- a non-workflow file under `types/` or `traits/`;
- an unknown type folder.

It also says workflow-check.py's `DELIVERY_KINDS` changes with the list. The delivery-kinds test reads every kind the list names however it is described. test_open_list holds that no name is `none` or `not yet classified` (tests part).

**The sweep's 36 survivors of the 381 mutants that compile, after BUG-006** (425 made; the 44 that do not compile are counted apart, never as killed: r3, Review B of gate round 2), line numbers of workflow-check.py at 0e7813e (the program is unchanged). The first version of this list called nine survivors equivalent or untestable that an input separates: 285, 605, 126, 299, 300, 312, 349, 354, and 626, which is now a lead. Review A of BUG-006 found them (below), and each of the first eight now has its case; it also moved 313 and 322 from "held on CI only" to equivalent. The rest:
- **Equivalent** (no input separates them):
  - 83: a closing run of two (a close must be at least as long as its opening, at least three).
  - 134: U+0080 is not printable.
  - 170: separator cells are stripped already by cells_of.
  - 190: a table line starts with a pipe.
  - 381: is_change_heading is only called on heading candidates.
  - 420, 422, 436: a marker is one character repeated.
  - 456, 459: a fence line cannot be a heading candidate.
  - 478: any strip of a blank line is empty.
  - 604: a segment is used only through its names, which are stripped again.
  - 313: a layer that cannot be examined has its error recorded, and the errors alone decide exit 2.
  - 322: links are pruned from the folders walked, so following links reaches nothing.
  - 625, 627 to 641: the lists read there hold exactly one entry (626 is a lead, below).
  - 662, 664: an equal index is a repeat, caught first.
  - 795: a root that is not a folder already ends the run with exit 2.
- **Held on CI's ubuntu leg only** (162): a symbolic link is known by its mode there, while the links test makes junctions on this Windows host.
- **Unreachable** (548): check_sub_identity's "type key is not a product type". collect never yields a sub-workflow item under an unknown type folder (fixtures 1, noted). It can go when the check is next changed.
- **Leads:**
  - 83: a form feed or NEL after a closing run would close a fence under a `\s` reading, where the check (and Markdown) does not. It belongs with the Unicode-whitespace table-cell lead above (fixtures 1, consider).
  - 485: a Set value of two backticks prints `-` rather than the two backticks in its (kind) finding.
  - 626: a head whose sub-type belongs to another type reports (e) and stops there. An unwritten product type or sub-type it names therefore gets no (f), which handoff/TASK-006.md R4's (f) reads as asking for. Example: against the status fixtures' open list, `Workflows: Library Development → Claude Code Extension` gives one (e) where the brief gives (e) and (f). This is a possible program defect, for the next change of workflow-check.py; the line fails either way (Review A of BUG-006).

**Review B returned no verdict**, a should-fix alone. Per the policy that is a failed launch, rerun with the stage's next round, and its finding was taken.

**Scratch folders:** several Review A parts used the same scratchpad folder (`ws`). One part's mutant appeared in another's copy, and a part's own results had to be redone. The checkout was never touched. Each reviewer gets a folder of its own from the next round on, and the point goes to the bridge feedback at the reflection (round 5, the supervisor).

**The sweep is rerun before each later stage review of this check.** A new survivor is either a test, or a line here with its reason. The sweep runs test_workflow_check.py, test_workflows_line_check.py and, since BUG-006 r2, test_extension_points.py, which imports the program too.

**BUG-006's gate, round 1:** Review A REJECT, Review B APPROVE. REVIEWERS DISAGREED on whether the survivor list above was honest, a correctness question. The supervisor decided for Review A: it separated each named survivor with one input, and the supervisor's run confirmed all eight are killed by the new cases. Taken in BUG-006 r2:
- **Cases (blocking):**
  - 605: a space before a comma in the head; the name is read stripped and only the shape fails.
  - 285: a Changes cell reading `set , add` accepts a Set, and `add` alone refuses it.
  - 126: a refused read names the system's reason.
  - 312: a layer that cannot be examined gives its exact ERROR line.
  - 299 and 300: a folder that cannot be listed is named with its reason, on every host.
  - 349 and 354: each link is named, one of them inside a folder that is no product type, in the links test's exact output.
  - The list above is corrected to match.
- **Text (should-fix):** both rule files' "How this file is read" now say a table is the first after its heading and before the next line starting `## `, as the reader does (worded so in r3; r2's "the next `##` heading" also covered `##` with a tab or nothing after it, which the reader reads past, Review B of gate round 2). The separators test's comment names the mutant it kills.
- **Text (considers):**
  - The registry says a Set value is stripped, and names exactly the files, links and folders that fail, a `types` or `traits` path that is itself a file or a link included (r3, Review A of gate round 2).
  - The open list says no name is `none` or `not yet classified`.
  - The sweep runs test_extension_points.py too.
- **The named driver** has the eight mutants (159 of 159 killed).
- **Recorded, not taken:** the delivery-kinds test finds a kind only when a `(` follows it, so a kind added to the list bare escapes the comparison with `DELIVERY_KINDS`. This is for whoever next changes the list (tests/test_extension_points.py).

**BUG-006's gate, round 2:** Review A APPROVE (0/1/4), Review B REJECT. Taken in BUG-006 r3:
- **Review B:** r2's "before the next `##` heading" also covered a `##` line with a tab or nothing after it, which the reader reads past. Both rule files now say "before the next line that starts with two hashes and a space (`## `)", and the table-reader test has a case for `##`+tab and a bare `##`.
- **Review B:** the sweep counted the 44 mutants that do not compile as killed (every test that runs the program fails on them). It now counts them apart and reports its survivors of the 381 that compile; the survivors are the same 36.
- **Review A (should-fix):** the equivalent range now reads 625, 627 to 641, so 626 is a lead only.
- **Review A (considers):** the registry names a `types` or `traits` path that is itself a file or a link; the list's intro says 313 and 322 moved.
- **The named driver** has r3's mutant (160 of 160 killed).

**BUG-006's gate, round 3:** Review A REJECT (1/0/3), Review B APPROVE (the reviewers disagreed; decided for Review A, whose mutant no test killed). Review A: the registry never said what a `##` heading is. The check reads `^ {0,3}##[ \t]`, so a line of `##` alone is text to it, where Markdown reads an empty heading; the mutant `##(?:[ \t]|$)` survived every test, and no sweep operator makes it. Taken in BUG-006 r4: the registry states the shape; the case kind-bare-hashes (a Set section whose first line is `##` alone) gives the exact (kind) line for `##`; the driver has the mutant (161 of 161 killed). A Markdown reading of a bare `##` would be a program change, not made here.

**BUG-006's gate, round 4:** Review A APPROVE (0/1/3), Review B REJECT. Review B: the round-5 paragraph's driver count (151 of 151) was that round's own, not the final count. This converged with Review A's consider that the round-3 record give its count, so it was blocking. Taken in BUG-006 r5:
- each record states the driver's count at its round;
- the delivery-kinds item is back under gate round 1, where it was raised (Review A's should-fix);
- the registry's heading sentence reads "a line that starts with" and now opens its paragraph, before the term's first use (considers).

Recorded from Review A, for the later program change that reads a line of `##` alone as Markdown does: under a Set whose value the check does not validate (`intake.budget-kind`), such a line passes as the value `##`.

## Stage B2 — the stage review (round 6, 2026-10-17)

**Taken on BUG-007 (the supervisor's fixtures, tests and registry text, no program change).** Round 6 rejected for round 5's class: rules of the workflow check that no test fails for. Review A's tests part rejected (5 blocking, 7 should-fix, 8 consider), fixtures parts 1 and 2 rejected, the programs, texts and fixtures parts 3 to 5 approved. Review B's reply was "APPROVE" with no line of the diff named: per the policy a failed launch, rerun with the stage's next round. Every finding below has its case with exact output, or is recorded with its reason.

**Sections and headings:**
- a section ends at the next `##` heading, a prose one too, so a Set right above one is empty, at the delivery-kind point too (tests and fixtures 2, converged);
- the four forms are matched exactly: text after the key, a space after it, and text after the delivery kind (tests);
- a change heading and an opening fence indented three spaces, the most either may be (fixtures 1 and 2, converged);
- a fence opened by four backticks, a shorter tilde run inside a fence of four, and a form feed after a closing run, which leaves the fence open (the sweep; round 5's lead on 83 is now a test);
- a heading whose first word is only punctuation, and one of punctuation alone, is prose (tests).

**Files and folders:**
- a file that is not `.md` under `types/` and under a type's folder (tests, fixtures 2);
- a folder named like a trait file under `traits/` (the sweep);
- a file of an unknown key, and a sub-workflow failing its identity, still have their changes checked (tests, fixtures 2);
- a link the walk lists among a folder's files, and a link named like a trait file (the sweep);
- a conditional-workflow file that cannot be read as UTF-8 stops the check with its ERROR line (programs and tests, converged); without that line the check printed a traceback;
- a missing registry, and a rule file that is a folder, each with its exact ERROR line (tests, the sweep);
- the default root is read when no root is given, proved by a program copy whose workflow folder fails (tests: the existing test passes whether it is read or not);
- a root with a trailing slash, and path fields holding a non-ASCII character in FAIL and ERROR lines (tests).

**Set values:**
- a backtick on the leading side only is not unwrapped (fixtures 2);
- two backticks are unwrapped to nothing and printed `-` (round 5's lead on 485, now pinned; whether the finding should print the two backticks stays a lead);
- an addition at a value point is an addition (tests).

**Workflows lines:**
- trait order is judged against the highest trait so far (tests);
- an empty traits text, and one ending `, ` (tests);
- a part named three times gives one (e), and the repeated line is still checked (fixtures 3 and programs, converged);
- a part's name ends at the first `: `, and a line holding only its prefix lacks the traits marker (tests, the sweep);
- a Workflow name in another case (fixtures 5);
- the open list's rows the status cases read are pinned (fixtures 5);
- inventory-check prints one line per finding in the judge's order, and an (e) case is among the malformed lines (tests).

**The table reader:** a separator cell of a single dash, and a header with no line after it (tests, the sweep).

**Registry text** (texts part): the four forms are matched exactly; "A `##` heading other than the four forms is prose" (carried from BUG-006's gate); an unreadable conditional-workflow file stops the check. The heading paragraph's order pin is exact: a blank line before it and the term's first use at its own sentence (carried).

**The sweep, widened** (run/supervisor/sweep_workflow_check.py, local; Review A, tests part): the bounds `{0,3}` and `{3,}` moved by one each way, the numbers compared moved by one, `== 2` read as `>= 2`, a character set made smaller, the deleted appends of errors and found items, each condition forced true and false, and each `and` clause dropped. It made 756 mutants, of which 711 compile (the 45 that do not are counted apart): 78 survived before BUG-007's cases, 50 after its last round (the list below is written by run/supervisor/write_survivor_list.py from that run's output, run/supervisor/sweep_workflow_check_r9.out, each survivor with its line of workflow-check.py at 6b51ccd and its operator; a line's other operators were killed or did not compile). 42 are equivalent, 4 held on CI only, 4 leads:
- **Equivalent** (no input separates them):
  - 83, `{3,} -> {2,}` (twice): a closing run must be at least as long as its opening, which is at least three.
  - 103, `if condition -> False`: a final empty line kept adds a blank line, which no reader acts on.
  - 134, `< -> <=`: U+0080 is not printable.
  - 170, `.strip() -> .rstrip()`, `.strip() -> .lstrip()`: separator cells are stripped already by cells_of.
  - 181, `drop and-clause bool(cells)`: cells_of always returns at least one cell.
  - 190, `.strip() -> .rstrip()`: a table line starts with a pipe, so nothing on its left is stripped (`.lstrip()` there is killed by the no-trailing-pipe case).
  - 191, `if condition -> True`: a table line starts with a pipe.
  - 313, `delete`: a layer that cannot be examined has its error recorded, and the errors alone decide exit 2.
  - 322, `False -> True`: links are pruned from the folders walked, so following links reaches nothing.
  - 357, `drop and-clause len(parts) >= 2`: a folder under `traits/` has at least two parts.
  - 364, `drop and-clause parts[0] == "traits"`: a two-part `types/` path ending `.md` is taken by the line before.
  - 380, `if condition -> False`: is_change_heading is only called on heading candidates.
  - 381, `False -> True`: is_change_heading is only called on heading candidates.
  - 420, `[0] -> [-1]`: a marker is one character repeated.
  - 422, `[0] -> [-1]`: a marker is one character repeated.
  - 436, `[0] -> [-1]`: a marker is one character repeated.
  - 456, `delete`: a fence line cannot be a heading candidate.
  - 459, `delete`: a fence line cannot be a heading candidate.
  - 478, `.strip() -> .rstrip()`, `.strip() -> .lstrip()`: any strip of a blank line is empty.
  - 538, `elif condition -> True`: the change kinds are add, set and replace.
  - 547, `if condition -> False`: collect never yields a sub-workflow item under an unknown type folder, so 548 is unreachable (it can go when the check is next changed).
  - 548, `delete`: unreachable, as for 547.
  - 604, `.strip() -> .rstrip()`, `.strip() -> .lstrip()`: a segment is used only through its names, which are stripped again.
  - 625, `[0] -> [-1]` (twice): the lists read there hold exactly one entry.
  - 627, `[0] -> [-1]`: the lists read there hold exactly one entry.
  - 632, `[0] -> [-1]`: the lists read there hold exactly one entry.
  - 634, `[0] -> [-1]` (twice): the lists read there hold exactly one entry.
  - 638, `[0] -> [-1]`: the lists read there hold exactly one entry.
  - 639, `[0] -> [-1]`: the lists read there hold exactly one entry.
  - 640, `[0] -> [-1]`: the lists read there hold exactly one entry.
  - 641, `[0] -> [-1]`: the lists read there hold exactly one entry.
  - 662, `< -> <=`: an equal index is a repeat, caught first.
  - 664, `> -> >=`: an equal index is a repeat, caught first.
  - 688, `if condition -> True`: a part is None only in a one-line file.
  - 795, `delete`: a root that is not a folder already ends the run with exit 2.
  - 833, `if condition -> False`: every printed field is ASCII already, so the error handler the reconfiguration sets is never used (with the condition forced true it is killed: a closed standard output, test_r014_closed_standard_output_gives_no_traceback).
- **Held on CI's ubuntu leg only** (the driver leaves them out on this host):
  - 161, `if condition -> False`: a symbolic link is known by its mode on CI's ubuntu leg; this host makes junctions.
  - 162, `True -> False`: as 161.
  - 335, `if condition -> False`: the dangling link `gone.md` lands among a folder's files on Linux, where reading it as a file is an ERROR; this host's junction is listed as a folder.
  - 336, `delete`: as 335.
- **Leads** (an input separates them, through a program defect the next change of the check settles):
  - 342, `drop and-clause len(parts) == 2`, `== 2 -> >= 2`: an input separates it on a POSIX host only: a folder whose name holds a backslash, directly under `types/`, whose contents the original reports under paths that do not exist (the lead on line 323 below) and the mutant drops; it dies when line 323 is fixed. With keys of the open list's shape and names without a backslash no input separates it.
  - 360, `== 2 -> >= 2`: as 342, with a folder named like `zz.md\q` under `types/`: the mutant reads a path that does not exist and stops with exit 2.
  - 626, `False -> True`: the lead below: a head whose sub-type belongs to another type stops at (e).

**Mutation driver:** run/supervisor/mutate_workflow_check.py names a mutant for each new rule: 196 of 196 killed at this round (161 before, 35 new), 198 of 198 after its gate round 1 and 199 of 199 after its gate round 3 (below); mutate_workflows_line.py stands at 42 of 42.

**Leads:**
- 626 stands (fixtures 4 converged on it with Review A of BUG-006): a possible program defect, for the next change of workflow-check.py.
- The program's usage text (lines 31 to 35) and the registry's list of what stops the check did not name an unreadable conditional-workflow file; the registry now does, and the usage text is the builder's, for the next change of the program (programs part).
- Line 323 turns every backslash of a folder's path into a slash, so on a POSIX host a folder named `zz\q` directly under `types/` (itself an unknown type folder) has its contents reported under paths that do not exist (`types/zz/q/sub`), where they should be skipped with their folder; reading only the separator of the host would close it, for the next change of the program (BUG-007's gate round 2: Review A, under WSL; worded so in its gate round 3). The sweep's survivors 342 and 360 are separated only by this input and die with the fix (gate round 3: Review B).
- The fixtures' 24 headers: the 25th file, status/ok-bom.md, was added in TASK-006 and deleted in BUG-002, so it has no net change in the stage (fixtures 4, noted).

**For TASK-023's brief** (programs part, noted): the calibration that installs release B adds a running project's `Workflows:` line, so the brief names that step.

**Reviewer folders:** each Review A part had a scratch folder of its own this round; none saw another's mutant.

**BUG-007's gate, round 1:** Review A REJECT (2 blocking, 1 should-fix, notes), Review B REJECT (1 blocking). Taken in BUG-007 r2:
- **Blocking (Review B):** the registry says an unreadable conditional-workflow file stops the check and checks nothing, and no test could see more being checked: a mutant reporting the readable files' findings after the ERROR passed. The UTF-8 case now has a readable failing file beside it, reported while the file is UTF-8 and not once it is not; the driver has that mutant.
- **Blocking (Review A):** 342 with `parts[0] == "types"` dropped was called equivalent and is not: a folder under `traits/` then hides a type file of the same name. form-traits-folder now holds `types/odd.md` with a failing change beside `traits/odd.md/`, and the driver has the mutant.
- **Blocking (Review A):** 335 was said to be held on CI and survived there: the case's dangling link had no `.md` in its name, so read as a file it failed as a path all the same. It is named `gone.md` now; read as a file it is an ERROR.
- **Should-fix (Review A):** 381 was missing from the list of 52; it stands with 380.
- **Noted (Review A), taken:** the order case's comment says what it separates (a highest trait that never rises); 342 and 360 hold for keys of the open list's shape; form-not-markdown's files that are no conditional workflow hold a failing change, so a read of them would show.
- **The named driver** has the two mutants, 342's and the readable files checked after an unreadable one (198 of 198 killed).

**BUG-007's gate, round 2:** Review A APPROVE (0 blocking, 1 should-fix, 3 considers), Review B REJECT. REVIEWERS DISAGREED on whether the survivor list is reliable, a correctness question of the records. Review B's example was misread: line 190's survivor is `.strip()` read as `.rstrip()`, and the `.lstrip()` mutant it ran is killed, as it found. But the list named lines without their operators, and its count (52) was stale after r2, which Review A's consider also said; converged, so blocking. Taken in BUG-007 r3:
- the sweep rerun after r3 and the list above written from its output by a script that fails on a survivor without a reason, each survivor with its operator;
- **Should-fix (Review A):** 342 and 360 are separated on a POSIX host by a folder name holding a backslash; both reasons say so, and line 323's splitting is a lead above;
- **Considers (Review A):** the driver's count states its round; the remaining unread files under `traits/` (form-not-markdown's installable.txt, form-traits-folder's two extra.md) hold a failing change, pinned as preconditions.

**BUG-007's gate, round 3:** Review A REJECT, Review B REJECT, converged on one class: survivors listed as equivalent that an input separates. Taken in BUG-007 r4:
- **Review A (blocking):** 833 with its condition forced true is not equivalent: with standard output closed (a launch with no standard handles, where Python sets sys.stdout to None) the mutant ends in a traceback and exit 1. test_r014_closed_standard_output_gives_no_traceback runs the check so on a passing and a failing root and asserts each exit code and no traceback; the driver has the mutant.
- **Review B (blocking):** 342 (twice) and 360 named the POSIX backslash input that separates them and stood under Equivalent; they are leads now, beside 626, dying when line 323 is fixed.
- **Considers (Review A), taken:** the backslash lead names a folder directly under `types/`; the list says a line's other operators were killed or did not compile; the scope file's round-6 count is marked as that round's.
- **Noted (Review A), taken:** the script that writes the list is kept beside the sweep, run/supervisor/write_survivor_list.py (local), and the list above is its output on the sweep rerun after r4.

