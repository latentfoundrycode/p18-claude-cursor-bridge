# SCOPE - BUG-038: the completion check finds no stand-in in its own docstring, stamped 2026.10.30d

A defect found after a merge, at project end on the bridge itself (2026-10-31): `completion-check.py --mode done` printed `STAND-IN: bridge/cursor-bridge/completion-check.py:30` and `:31`, both lines of the program's own module docstring, which quoted the phrases its stand-in scan `STANDIN_RX` matches. The bridge ships the program as tracked, non-test code, so its project end could never pass. Pull request #114, branch bug-038 from origin/main 6dd47ef; checkpoint 43f3a03 ("checkpoint before BUG-038", the brief and the reproduction test).

## The briefs (read whole: handoff/BUG-038.md, handoff/BUG-038-r2.md, handoff/BUG-038-r3.md)
Scope of every round: bridge/cursor-bridge/completion-check.py (the module docstring's STAND-IN paragraph only), docs/BUILDER_NOTES.md, the round's report handoff/BUG-038-r<N>-report.md.
Out of scope: every file under tests/ (the reproduction is the supervisor's); docs/cli-reference.json and docs/CLI_REFERENCE.md (generated from the parser, not the docstring; `tools/dump-cli.py --check` passes without regenerating); MANIFEST.json, VERSION, CHANGELOG.md (the supervisor's stamp); `STANDIN_RX`, `NOTE_RX`, `SKIP_PATH`, `TEST_PATH`, `CODE_EXT`, every function, the parser and every output line; the installed bridge. Banned as symptom suppression: a skip of the program's own file, of `bridge/` or of docstrings; an owner-deferred ID added to excuse the paragraph.
Round 1 reworded the paragraph (no line matched); Review A rejected the wording (the macro clause's "with arguments" excluded the bare `todo!()`; other clauses named phrases the scan misses). Round 2 reworded it again; Review A rejected "will land soon" and a not-ready-yet clause without its "yet". Round 3's brief gave the paragraph whole, written and checked by the supervisor against `STANDIN_RX` line by line and with the lines joined; Review A approved it. These are the launcher's builder rounds 1 to 3; this is the guard's Review B round 1.

## The supervisor's tests (tests/test_bug038.py; helpers from tests/test_completion_check.py)
- test_bug038_the_completion_check_finds_no_stand_in_in_its_own_source — enforces ~/.claude/cursor-bridge/workflow/phases/project-end.md, "Prove the product is complete" (`completion-check.py --mode done` prints `RESULT: OK`, no stand-in in shipped code): a scratch repository shipping a tracked copy at bridge/cursor-bridge/completion-check.py passes at done, run by the copy and by the release folder's program.
- test_bug038_a_stand_in_elsewhere_is_still_found — enforces completion-check.py's STAND-IN contract and the brief's ban on suppression: seven stand-ins planted beside the program in bridge/cursor-bridge/screen.py (a module docstring line among them, a `PlaceholderSection` identifier and `todo!()`) are all found, and one `# coming soon` appended to the shipped copy is found at its line, the only STAND-IN line for that file.
- test_bug038_the_docstring_still_names_each_kind_it_scans_for — enforces the first brief's Requirements 2 and 3: the paragraph names each kind, the six suffixes included, and ends on `Allowed only on a line that names the ID of an owner-deferred requirement.` unchanged.
Tests 1 and 2 fail on 43f3a03 (mutation-run.py --checkpoint). The supervisor fixed test 3's slice after round 1 (it read only the shebang line, as the builder's report found) and strengthened test 2 before each Review A read.

## The mutants (run/supervisor/BUG-038-mutants.json, the supervisor's; not in the diff)
m1 a scanned phrase back in the docstring ("coming directly followed by soon;" to "coming soon;"); m2 the owner-deferred sentence dropped; m3 `bridge` added to `SKIP_PATH`; m4 the program's own file added to `SKIP_PATH`. Mutation run on the final code: 4 killed of 4.

## Expected bookkeeping and records in the diff
docs/BUILDER_NOTES.md (round 1's dated line); handoff/BUG-038.md, -r2.md, -r3.md and the three reports; the stamp (bridge/cursor-bridge/CHANGELOG.md's 2026.10.30d entry, VERSION, MANIFEST.json, 144 files); records as at this pull request's merge (ISS-009): docs/PROJECT_STATUS.md (its `Bridge version:` moved with the stamp, as at PRs #110 and #112, since conformance-check holds it to the release folder's VERSION; cap 12,000 characters), docs/archive/STATUS_HISTORY.md, docs/HARDENING.md (BUG-038's section; stage B6's least confident 1 settled by the TDP's report of 2026.10.30b's field check), docs/REQUIREMENTS.md (R-037's evidence; R-031 and R-037 stay planned until the owner's deferral), project.json (its `version`; `state.bridge` stays the installed 2026.10.30b); run/review/ (this round's files).

## What to check
- The cause repaired at its mechanism, nothing suppressed: no line of completion-check.py matches `STANDIN_RX` (line by line, as the program scans), the scan and its outputs unchanged, a stand-in anywhere else still found.
- Each clause of the new paragraph true to its branch of `STANDIN_RX`: it neither excludes text the branch matches nor gives as an example text the branch misses.
- The tests check what their docstrings say and are not vacuous; no test, assertion or CI step weakened.
- The 2026.10.30d entry true to the change (one program, its docstring only; against 2026.10.30c no file new or removed; the If rolled back item).
- The records agree with each other and with the change; no key and no computer path or user name in a tracked file (rule 54).

Later releases (T, B2, the progress graph, W) and project end's own items are later work, not this increment's defect. This is the increment's Review B round 1, below the guard's ceiling.
