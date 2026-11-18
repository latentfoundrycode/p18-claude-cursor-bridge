---
record: brief
header: 1
id: "TASK-067"
round: 4
satisfies: [R-087]
scope: ["bridge/cursor-bridge/push-scan.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-067-r4-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-067 round 4: the objects a push sends (R-087)

Round cause: security - the security audit failed round 3 and Review A confirmed both findings: a commit's own .gitattributes marking a text file -diff or binary hides its added lines, and a replace ref makes the scan read a replacement object while a push sends the original, so the scan prints OK.

Blocking class: security - Security audit, round 3, the advisory on binary and -diff files, reproduced through commit content (a committed .gitattributes) by the audit and by Review A, round 3 (NOTED, second item): untrusted commit content reaches a pass against R-087; and Security audit, round 3, B1: a replace ref (refs/replace) makes cat-file, rev-list and git show read objects a push never sends.

This round is above the review ceiling and is lifted by the class line above. The reviewers confirm or deny that line against the code of round 3 as this round's builder finds it: the commit this brief was committed in, which is the commit you are started on (`git rev-parse HEAD` at your start).

## Objective
Fix the following confirmed defects in the pre-push scan, and nothing else.

This is round 4 of TASK-067. Rounds 1 to 3 built `bridge/cursor-bridge/push-scan.py`, its allow entry and the generated files; round 3 made sure a user setting or a commit's `.gitmodules` cannot narrow what `git show` prints. All of that stays except what H1 and H2 below change. The supervisor commits round 3's tree together with this brief and the round-4 test cases before your run, so the line numbers below hold when you start.

**The confirmed defects** (the security audit and Review A of round 3; each is now a case of the supervisor's, the round-4 section of `tests/test_program_push_scan.py`): the scan reads objects through git's object lookup and reads a file's added lines from `git show`'s patch, and both can be turned away from what a push sends. First, a replace ref (`git replace <original> <replacement>`, stored under `refs/replace/`) makes `rev-list`, `cat-file -p` and `git show` read the replacement object wherever the original is named, while `git push` sends the original: a commit whose own lines hold a path, hidden behind a clean replacement, is read as clean and the scan prints `push-scan: OK`. Second, `git show` prints `Binary files a/<path> and b/<path> differ` instead of the added lines for a file that an attribute marks `-diff` or `binary` (`binary` is `-diff -merge -text`), and an attribute can come from the commit's own `.gitattributes`, which is commit content; the same happens for a file a diff driver's `binary` setting or `core.bigFileThreshold` marks binary. Such a file's added lines are never read and the scan prints `push-scan: OK`.

Satisfies: R-087 - The pre-push scan is a program (C2): `push-scan.py [<base>]` (default `origin/<the default branch>`) reads every commit of `<base>..HEAD`, its message, author and committer lines, added lines and added file names, for a path of this computer (a drive-letter path, `/Users/`, `/home/`, `AppData`; a placeholder segment such as `<name>` passes) and for the owner's account names, [...]; exit 0 clean, 1 on a hit, which prints the commit, the place, the line's number and whether a path or a name was found and never the matched text, a hit in a file's own name placed by that file's position in the commit's list and not by its path, 2 where git cannot be read; [...]. (Full text: its row in `docs/REQUIREMENTS.md`, line 113. This round serves "every commit" and "added lines" against a replace ref and against a file's attributes: the scan reads the objects a push sends, and every added line of a text file.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/push-scan.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-067-r4-report.md

Limits on these files:
- `bridge/cursor-bridge/push-scan.py`: only what H1 and H2 change: the runner `git`'s argv (line 51) and, in `scan_commit` (620-673), the argument list of the patch call, the second `git show` (635-641, its list at 637-640). Every other line, function, refusal, message, note and exit stays byte-identical to round 3's tree (H3); in particular the name-status call (626-632), `git_text` (69-71), `added_lines`, `parse_name_status`, `quote_path`, the placement line (659), the file-name hit (660-662) and the disagreement check (670-672) do not change. The module docstring and the parser's description and help do not change.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`; restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are not in Scope this round: the parser's text must not change, so they do not change. Do not run `python tools/dump-cli.py` without `--check`; Done runs only its read-only `--check`.

Do not modify anything else. `bridge/cursor-bridge/settings.bridge.json` is done (round 1) and must not change. Every test file is read-only for you: read and run `tests/test_program_push_scan.py`, `tests/test_dump_cli.py` and `tests/test_allowlist.py`, edit none of them.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, the diagrams, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` included. The briefs of rounds 1 to 3 (`handoff/TASK-067.md`, `handoff/TASK-067-r2.md`, `handoff/TASK-067-r3.md`) and their reports (`handoff/TASK-067-r1-report.md`, `handoff/TASK-067-r2-report.md`, `handoff/TASK-067-r3-report.md`) stay as they are.
- `bridge/cursor-bridge/settings.bridge.json`, `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`.
- Every test file. You add no test file and edit none; a gap is reported (Constraints, mutation self-check).
- `bridge/agents/secret-sentinel.md`, `bridge/commands/supervisor.md`, the loop's text under `bridge/cursor-bridge/workflow/` (TASK-082).
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them as Done says, and edit neither).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.
- The disagreement check (round 2's F4, `scan_commit` lines 670-672) stays exactly as written; the supervisor's mutants file marks its removal as expected to survive. Do not remove, weaken or "simplify" it.
- **Not in this round** (recorded leads; do not change their behaviour): UTF-16 files (H2 does not recover them); characters of categories `Zs`, `Mn`, `Co` and filler characters printed raw in a path; a default-ignorable `Cf` character inside a name; a commit with an `encoding` header; partial-clone lazy fetch (`GIT_NO_LAZY_FETCH`); the round-3 static case for `--submodule=short` lacking a behaviour case; spaces in a printed path faking fields inside one hit line; `owner_of` on remotes with more than two path segments; resolving git's absolute path; git's stripping of trailing punctuation from an ident's name; and, carried from round 3, copy (`C`) statuses (`if status[:1] in ("A", "R"):` at line 660 stays as it is).

## Context
**Rounds 1 to 3 govern everything this brief does not change:** `handoff/TASK-067.md` (R1-R12, M1-M13), `handoff/TASK-067-r2.md` (F1-F10, N1-N9) and `handoff/TASK-067-r3.md` (G1-G7, P1-P6). Read all three whole. Their Context sections (the design `docs/DESIGN.md` C2, the privacy paragraph, the import pattern, the trust boundaries, development data, host) and their Constraints hold for this round unchanged, except where H1 and H2 change them. Three of them in particular:
- **The owner's decision of 2026-11-18 (rule 52, the owner's value):** the names of the repository's configured git identity (`git config user.name`, the local part of `git config user.email`) are public, dropped from the names searched and counted in N2, and the author and committer lines that carry the configured identity are no finding. The tests `test_r087_owner_2026_11_18_the_configured_identity_is_no_finding_anywhere` and `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped` pin it. Do not change this behaviour or those tests; if the work seems to need a change, stop and report it.
- **R11, the source scans clean:** the program's own source holds no literal of the shapes the scan reads as a path (a drive letter with a colon and a slash or backslash, `/Users/`, `/home/`, `AppData`, a URL literal such as `https:` with its slashes), and the source is ASCII only. Done steps 9 and 10 verify it.
- **The printed reasons are round 2's closed list.** No reason is added this round.

**The supervisor's round-4 cases.** `tests/test_program_push_scan.py`, the section headed `# ---------------------------------------------------------------- round 4: the objects a push sends (the reviews of round 3)` (line 579 to the end), read it whole; they fix the expected outputs. Three test instances:
- `test_r087_a_replaced_commit_is_read_as_the_push_sends_it` (line 581): H1. Commit X on `main` adds a line holding a path to `notes.md`; a commit Y with the same message and a clean line is made on another branch from the base; `git replace X Y` hides X behind Y. Expected exactly `HIT <X's short hash> line notes.md:2 path`, exit 1.
- `test_r087_a_text_file_the_commit_marks_binary_is_still_read[-diff]` and `test_r087_a_text_file_the_commit_marks_binary_is_still_read[binary]` (line 596-597, parametrized): H2. One commit adds `.gitattributes` holding `*.md -diff` (or `*.md binary`) and `notes.md` whose second line holds a path. Expected exactly `HIT <h> line notes.md:2 path`, exit 1 (`notes.md` is placed by its path: neither its real nor its printed path holds a hit).

**The code as it stands** (round 3's tree, line numbers verified):
- `git(sub, args)` (50-66) is the one `subprocess.run`; its argv (51) is `["git", "--no-pager", "-c", "color.ui=never", "-c", "log.showSignature=false", "-c", "log.showRoot=true", "-c", "diff.suppressBlankEmpty=false", sub] + list(args)`. Every git call of the program goes through it: `rev-parse` (`ensure_repository`, `ensure_commit`, the short hash in `scan_commit`), `symbolic-ref` (`default_base`), `config` and `remote` (the names and the identity), `rev-list` (`execute`, line 710), `cat-file -p` (`scan_commit`, 622) and both `git show` calls.
- `git_text` (69-71) decodes git's output with `out.decode("utf-8", errors="replace")`; `git_need` (74-78) uses it. The patch is read through `git_need` (635), so a byte that is not UTF-8 is already decoded with replacement, never an exit of its own.
- `scan_commit` (620-673): the name-status call (626-632) is `git("show", ["-z", "--name-status", "-M", "--format=", "--no-ext-diff", "--no-textconv", "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/", "--ignore-submodules=none", "--submodule=short", "--end-of-options", full])`; the patch call (635-641) is `git_need("show", ["-M", "--format=", "--no-ext-diff", "--no-textconv", "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/", "--ignore-submodules=none", "--submodule=short", "--end-of-options", full])`. The round-3 static case counts `--submodule=short` and `--ignore-submodules=none` at least twice each in the source; keep both written out in both calls.
- `added_lines` (458-540) reads a file's added lines only from its `+++` header and hunks; a `Binary files ... differ` line names no path and adds no line, which is why a file shown as binary is read as empty.

**Known failures before your change.** The supervisor's known run on round 3's tree (`run/agent/TASK-067-r4-known.out`) printed: `3 failed, 39 deselected` (run with `-k "replaced_commit or marks_binary"`): `test_r087_a_replaced_commit_is_read_as_the_push_sends_it`, `test_r087_a_text_file_the_commit_marks_binary_is_still_read[-diff]` and `test_r087_a_text_file_the_commit_marks_binary_is_still_read[binary]`, each printing `push-scan: OK - 1 commit(s)` with exit 0 where a hit was expected. Every round-1 to round-3 case of `tests/test_program_push_scan.py`, and `tests/test_dump_cli.py` and `tests/test_allowlist.py`, passed in round 3's own run (`380 passed, 20 skipped`). All must pass after your change.

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. The commits' contents (D-004 marks them `UNTRUSTED`), a commit's own `.gitattributes`, `.gitmodules` and file names included, the repository's refs (`refs/replace/` included), attribute files outside the commit (`.git/info/attributes`, `core.attributesFile`), the names file, the environment, git's configuration values and the `<base>` argument are outside input. Rounds 2 and 3's rule stands and this round extends it: no commit content, ref, attribute or user setting may make the scan read objects other than the ones a push sends, narrow what git shows it, make it miss a place, misplace a hit, forge or reorder an output line, or print OK where it could not read; where the program cannot read what git wrote, it ends with exit 2, never with a pass.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: run `push-scan.py` only through the tests, on their scratch repositories under `tmp_path`. Never run it on this repository (it would read the owner's real account names). Never install anything and never copy anything under `~/.claude`.

**Host.** Windows 11, with Python as on the owner's interpreter, git as installed.

## Diagrams
Unchanged from rounds 1 to 3 (`handoff/TASK-067.md`, Diagrams): `docs/diagrams/D-002-components.md` draws `push_scan --> bridge_env` and `dump_cli -.-> push_scan`; `docs/diagrams/D-004-context-dfd.md` draws the flows into `p_push_scan` and the one flow out:

```mermaid
p_push_scan -->|"hits to the terminal only: commit, place, line number, never the matched text; nothing leaves the computer (R-087)"| p_supervisor
```

`push-scan.py` imports `bridge_env` and no other bridge program, writes nothing, and reaches nothing beyond read-only git. If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
1. **H1. Every git call reads the objects a push sends** (blocking; answers: Security audit, round 3, B1, a replace ref). The runner `git` puts git's global option `--no-replace-objects` before the subcommand, beside `--no-pager`, so every git call of the program (`rev-parse`, `symbolic-ref`, `rev-list`, `cat-file`, both `git show` calls, `config`, `remote`) ignores `refs/replace/` and reads the original objects. No other change to the runner: its `-c` pairs, its `subprocess.run` arguments and its exception handling stay as they are.
2. **H2. A text file is read whatever its attributes say** (blocking; answers: the advisory on binary and `-diff` files, reproduced through a committed `.gitattributes`). The patch call (the second `git show` in `scan_commit`) passes `--text` beside `--no-textconv`, so a file that a commit's `.gitattributes`, the user's attributes, a diff driver's `binary` setting or `core.bigFileThreshold` marks binary or `-diff` is shown line by line and its added lines are read like those of any text file. The name-status call is unchanged. A file holding bytes that are not UTF-8 is decoded with replacement as every line already is (`git_text`), never an exit of its own and never a new reason. A UTF-16 file is not recovered by `--text` (NUL bytes separate its characters): a recorded lead, not this round.
3. **H3. Everything else is byte-identical to round 3's tree.** No other line of `push-scan.py` changes (Scope, limits).

## Acceptance criteria
- [ ] The Done section's pytest commands pass whole: `tests/test_program_push_scan.py` gives no failure (its three round-4 instances included), and `tests/test_dump_cli.py` and `tests/test_allowlist.py` give no failure.
- [ ] H1-H3 hold as written; every requirement of rounds 1 to 3 (R1-R12 of `handoff/TASK-067.md`, F1-F10 of `handoff/TASK-067-r2.md`, G1-G7 of `handoff/TASK-067-r3.md`) still holds, the owner's decision of 2026-11-18 included.
- [ ] The runner's argv carries `--no-replace-objects` before the subcommand; the patch call carries `--text`; the name-status call is unchanged; both `git show` calls still carry `--ignore-submodules=none` and `--submodule=short`.
- [ ] Done's `git diff` of `push-scan.py` shows changes at the runner's argv and the patch call's argument list only.
- [ ] No output line holds a matched text, a name, a line, a path whose real or printed form holds a hit, or a raw control, separator or format character; every line of the output begins with `push-scan: ` (R9, F9, G5, G6).
- [ ] Done's grep over `bridge/cursor-bridge/push-scan.py` prints nothing, and its ASCII check prints `ascii ok` (R11).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `bridge/cursor-bridge/settings.bridge.json` is unchanged. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-087 (the parts this brief serves) is fully met: no stand-in, placeholder or "later" text in the program. The tests naming R-087 are the supervisor's.
- [ ] No new dependency (standard library only), option, configuration key, environment variable or CANNOT SCAN reason. No new Semgrep high finding. No exception escapes as a traceback, and none is turned into a pass (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit any test file or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall: one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (the program, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- **Windowless launches.** Every process the program starts is created with `creationflags=bridge_env.NO_WINDOW`, with `timeout=bridge_env.GIT_TIMEOUT`, through `subprocess.run`, never `Popen`, never through a shell. Capturing output does not prevent the window. (The runner already does this; H1 does not change it.)
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section and the mutation self-check name, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- **Never run `push-scan.py` on this repository** or on any folder but the tests' scratch repositories (Context, "Development data").
- Never run the product, a migration, a seed or a test against the owner's live data. Never install anything.
- The owner's value (Context, the decision of 2026-11-18, pinned by the two `test_r087_owner_2026_11_18_` tests) is fixed: do not change it or those tests; report it if the work seems to need a change (rule 52).
- Do not refactor code outside the two places the Scope's limits name, even if it looks wrong. The items under "Not in this round" and the disagreement check stay as they are.
- Follow existing conventions of `push-scan.py`: ASCII program text, ASCII output apart from path names, results returned as values, `ScanError(reason)` for every exit 2, `main()` returning the exit code.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `replace`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. The program itself runs only read-only git commands.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the scan after your run, and every mutant but the one it marks as expected to survive must fail a test. Before you finish, apply each of these to `push-scan.py` by hand, one at a time, run `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` from the Workspace root, and revert to the exact bytes from before the mutant. List each in the report by its label and text, with the test id that caught it, or `not caught`:
  - Q1 `--no-replace-objects` removed from the runner (H1);
  - Q2 `--text` removed from the patch call (H2).

  Re-run an earlier mutant by its label only where your change touched the code it changes: N5 (`log.showSignature` left on; the runner's argv), N6 (`--no-relative` dropped; the two `git show` calls), P1 (`-c log.showRoot=true` removed from the runner), P2 (`--ignore-submodules=none` removed from both `git show` calls), P3 (`--submodule=short` removed from both `git show` calls) and P4 (`-c diff.suppressBlankEmpty=false` removed from the runner). For every other mutant of rounds 1 to 3 (M1-M13, N1-N9, P5, P6), say in one line that its code is unchanged; N4 (the disagreement check removed) stays expected to survive and is not re-run. You cannot add a test. A mutant no test catches is reported as `not caught`, with one line on the case that would catch it; the supervisor adds it.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: git's own options, the existing runner and decoding, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-067-r4-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for H1-H3, one line each on what meets it, naming the function and its line as the file stands after your change;
- the mutation self-check list, Q1 and Q2, each with the test id that caught it (or `not caught` and the case that would), the N5, N6, P1, P2, P3 and P4 lines, and the unchanged-code lines the mutation self-check asks for;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a git behaviour you expected, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. Examples:
- that `--no-replace-objects` before the subcommand makes `rev-list`, `cat-file -p`, `rev-parse --short` and `git show` read the original objects in the git installed here, whatever `core.useReplaceRefs` or `GIT_REPLACE_REF_BASE` says;
- that `--text` on `git show` overrides a `binary` or `-diff` attribute from every attribute source, a diff driver's `binary` setting and `core.bigFileThreshold`, with `--no-textconv` and `--no-ext-diff` still in force;
- that a file shown by `--text` whose bytes hold a CR or a NUL inside a line, or no final newline, is read by `added_lines` without a `the patch cannot be read` refusal.

One item per line: what you assumed | why | what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py --check` (expect exit 0; if it does not, stop and report it, and do not run `python tools/dump-cli.py` without `--check`)
3. `python tools/make-manifest.py`
4. `git restore bridge/cursor-bridge/VERSION`
5. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
8. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
9. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py` (expect no output and exit 1: the source holds none of the shapes R11 names. Quote the empty output and the exit code.)
10. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
11. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json` (expect no output: the file is unchanged)
12. `git diff HEAD -- bridge/cursor-bridge/push-scan.py` (expect hunks at the runner's argv and the patch call's argument list only; quote it whole)
13. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Where a failure body would print a temporary path, replace it with `<tmp>`.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 13, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
