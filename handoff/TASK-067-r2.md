---
record: brief
header: 1
id: "TASK-067"
round: 2
satisfies: [R-087]
scope: ["bridge/cursor-bridge/push-scan.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-067-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-067 round 2: the patch read as git writes it (R-087)

Round cause: security - Review A rejected and the security audit failed round 1: commit content can make the scan drop a hit and print OK (an added line beginning with ++ read as a file header; a path with a space cut at the space; a merge's combined statuses read as renames; a patch path missing from the file list skipped), and log.showSignature puts signature text into a hit line.

## Objective
Fix the following confirmed defects in the pre-push scan, and nothing else.

This is round 2 of TASK-067. Round 1 built `bridge/cursor-bridge/push-scan.py`, its allow entry and the generated files. All of that stays except what F1 to F10 below change. The supervisor commits round 1's tree together with this brief and the round-2 test cases before your run, so the line numbers below hold when you start.

**The confirmed defects** (Review A and the security audit of round 1; each is now a red case of the supervisor's, the round-2 section of `tests/test_program_push_scan.py`): the commits' contents are untrusted, and round 1 lets them steer the parser. `added_lines` (lines 419-470) reads every line beginning with `+++ ` or `@@` as a header, even inside a hunk, so an added line whose text begins with `++ ` changes the file the following lines are placed in; `take_token` (373-390) cuts an unquoted path at its first space; `parse_name_status` (473-495) reads two paths for any status beginning with `R` or `C`, so a merge's combined status (`RM`) eats the next record; `scan_commit` (547-555) silently skips the lines of a patch path missing from the file list when that path holds a hit; the git calls honour the user's `log.showSignature`, `diff.relative`, `diff.noprefix` and prefix settings; `has_name` (126-144) indexes the original text with positions found in a lower-cased copy, which shift after a letter that lower-cases to two characters; `text.splitlines()` (427) splits a patch at form feeds and Unicode separators; a path holding a newline is printed raw, so a file name can forge an output line.

Satisfies: R-087 - The pre-push scan is a program (C2): `push-scan.py [<base>]` (default `origin/<the default branch>`) reads every commit of `<base>..HEAD`, its message, author and committer lines, added lines and added file names, for a path of this computer (a drive-letter path, `/Users/`, `/home/`, `AppData`; a placeholder segment such as `<name>` passes) and for the owner's account names, [...]; exit 0 clean, 1 on a hit, which prints the commit, the place, the line's number and whether a path or a name was found and never the matched text, a hit in a file's own name placed by that file's position in the commit's list and not by its path, 2 where git cannot be read; [...]. (Full text: its row in `docs/REQUIREMENTS.md`, line 113. This round serves the reading of the patch and the file list, the git calls' settings, the name match and the printed path.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/push-scan.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-067-r2-report.md

Limits on these files:
- `bridge/cursor-bridge/push-scan.py`: only what F1 to F10 change: `git` (lines 49-65), `has_name` (126-144), `unquote_git` (336-370), `take_token` (373-390), `strip_side` (393-397), `hunk_new_start` (400-416), `added_lines` (419-470), `parse_name_status` (473-495), `scan_commit` (502-556) and the catch-all in `main` (630-632), and any new helper these need. Every other function, refusal, message, note and exit stays byte-identical to round 1's tree. The module docstring and the parser's description and help may stay as they are; if you change them, they still name no path and no name (round 1's R1 and R11).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), and only if the parser's text changed. Afterwards `python tools/dump-cli.py --check` must exit 0. Never edit either by hand.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`; restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Do not modify anything else. `bridge/cursor-bridge/settings.bridge.json` is done (round 1, committed at the checkpoint) and must not change. Every test file is read-only for you: read and run `tests/test_program_push_scan.py`, `tests/test_dump_cli.py` and `tests/test_allowlist.py`, edit none of them.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, the diagrams included. Round 1's brief `handoff/TASK-067.md` and report `handoff/TASK-067-r1-report.md` stay as they are.
- `bridge/cursor-bridge/settings.bridge.json`, `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`. If `bridge_env` lacks something you need, write it in `push-scan.py` or stop and report it.
- Every test file. You add no test file and edit none; a gap is reported (Constraints, mutation self-check).
- `bridge/agents/secret-sentinel.md`, `bridge/commands/supervisor.md`, the loop's text under `bridge/cursor-bridge/workflow/` (TASK-082).
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them, Done, and edit neither).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.
- **Not in this round** (recorded leads; do not change their behaviour): binary files, or files marked `-diff`, that show no lines; `owner_of` on remotes with more than two path segments; resolving git's absolute path; git's stripping of trailing punctuation from an ident's name; copy (`C`) statuses at line 537 (`if status[:1] in ("A", "R"):` stays as it is).

## Context
**Round 1's brief governs everything this brief does not change:** `handoff/TASK-067.md`, read it whole: its Requirements R1-R12, its Context (the design `docs/DESIGN.md` C2 at line 347, the privacy paragraph at line 433, the reality check on `bridge_env`, the import pattern, the trust boundaries, development data, host) and its Constraints hold for this round unchanged, except where F1 to F10 change them. Two of them in particular:
- **The owner's decision of 2026-11-18 (rule 52, the owner's value):** the names of the repository's configured git identity (`git config user.name`, the local part of `git config user.email`) are public, dropped from the names searched and counted in N2, and the author and committer lines that carry the configured identity are no finding. The tests `test_r087_owner_2026_11_18_the_configured_identity_is_no_finding_anywhere` and `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped` pin it. Do not change this behaviour or those tests; if the work seems to need a change, stop and report it.
- **R11, the source scans clean:** the program's own source holds no literal of the shapes the scan reads as a path (a drive letter with a colon and a slash or backslash, `/Users/`, `/home/`, `AppData`, a URL literal such as `https:` with its slashes), each built from parts as round 1 does (lines 30-36), and the source is ASCII only. Done steps 11 and 12 verify it. A character F9 names is written in the source by an escape or by `chr()`, never typed.

**The supervisor's round-2 cases.** `tests/test_program_push_scan.py`, the section headed `# ---------------------------------------------------------------- round 2: the patch read as git writes it (the reviews of round 1)` (line 372 to the end), read it whole; they fix the expected outputs:
- `test_r087_an_added_line_that_reads_like_a_file_header_is_scanned_in_its_hunk` (line 379): F1.
- `test_r087_a_changed_file_with_a_space_in_its_name_is_read_by_its_whole_name` (line 390): F2, F4; `other file.md` is printed with its space, unquoted (F9 quotes no space).
- `test_r087_a_merge_where_one_side_renamed_a_file_reads_each_file_by_its_own_position` (line 402): F1 (a combined hunk), F3.
- `test_r087_a_control_character_in_a_printed_path_is_escaped` (line 422): F9; the file name holds two newlines and a forged `push-scan: OK` line.
- `test_r087_the_user_s_diff_settings_neither_hide_nor_misplace_a_hit` (line 439): F6, run from a subfolder with `diff.relative` and `diff.noprefix` set.
- `test_r087_a_name_after_a_letter_that_lowercases_to_two_characters_is_found` (line 449): F7.
- `test_r087_a_form_feed_inside_an_added_line_moves_no_line_number` (line 459): F8.
- `test_r087_a_commit_s_signature_is_never_read_into_a_hit` (line 468): F5, a static read of the source for `log.showSignature=false`.

Two of these cases use a character outside ASCII (line 453: U+0130, a capital I with a dot above; line 463: U+2028, a line separator, between `c` and `d`), each written as an escape in the test file, which stays ASCII (KP-052). Your own source and report stay ASCII.

**The code as it stands** (round 1's tree, line numbers verified):
- `git(sub, args)` (49-65) is the one `subprocess.run`; its argv begins `["git", "--no-pager", "-c", "color.ui=never", sub]`.
- `scan_commit` (502-556): the short hash from `git log -1 --format=%h` (503); the commit object from `git cat-file -p` (504); the file list from `git show -z --name-status -M --format= --no-ext-diff --no-textconv --no-color --end-of-options <full>` (508-512); the patch from `git show -M --format= --no-ext-diff --no-textconv --no-color --end-of-options <full>` (515-519); `added_lines(patch)` grouped by path (521-523); the places (525-546); the unlisted-path loop (547-555).
- `added_lines` (419-470) iterates `text.splitlines()` and reads `diff --git `, `rename to `, `+++ ` and `@@` lines anywhere; `hunk_new_start` (400-416) takes the last `+<digits>` of a hunk header; `take_token` (373-390) and `unquote_git` (336-370) read a path token; `unquote_git` appends `int(digits, 8)` to a bytearray, which raises for a value above 255.
- `has_name` (126-144) finds in `text.lower()` and reads the neighbours in `text` at the same index.
- `main` (623-632): `ScanError` prints `push-scan: CANNOT SCAN - <reason>` and returns 2; any other exception prints `git cannot be started`.
- `say(line)` (44-46) writes each line as UTF-8 and flushes.

**Known failures before your change.** The supervisor's known run on round 1's tree (`run/agent/TASK-067-r2-known2.out`, then the control-character case alone after its setup was fixed, `run/agent/TASK-067-r2-known3.out`): `8 failed, 24 passed`, the eight round-2 cases, each on its assertion (the merge case printed `push-scan: OK - 3 commit(s)`; the control-character case printed the forged line). Every round-1 case of `tests/test_program_push_scan.py`, and `tests/test_dump_cli.py` and `tests/test_allowlist.py`, passed in round 1's own run. All must pass after your change.

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. The commits' contents (D-004 marks them `UNTRUSTED`), file names included, the names file, the environment, git's configuration values and the `<base>` argument are outside input. This round's rule: no commit content, file name or user setting may make the scan miss a place, misplace a hit, forge an output line, or print OK where it could not read; where the program cannot read what git wrote, it ends with exit 2, never with a pass.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: run `push-scan.py` only through the tests, on their scratch repositories under `tmp_path`. Never run it on this repository (it would read the owner's real account names). Never install anything and never copy anything under `~/.claude`.

**Host.** Windows 11, with Python as on the owner's interpreter, git as installed.

## Diagrams
Unchanged from round 1 (`handoff/TASK-067.md`, Diagrams): `docs/diagrams/D-002-components.md` draws `push_scan --> bridge_env` and `dump_cli -.-> push_scan`; `docs/diagrams/D-004-context-dfd.md` draws the flows into `p_push_scan` and the one flow out:

```mermaid
p_push_scan -->|"hits to the terminal only: commit, place, line number, never the matched text; nothing leaves the computer (R-087)"| p_supervisor
```

`push-scan.py` imports `bridge_env` and no other bridge program, writes nothing, and reaches nothing beyond read-only git. If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
1. **F1. The patch is parsed by hunks** (answers: an added line beginning with `++` read as a file header).
   - Each hunk header (`@@ ... @@` for a single-parent diff; `@@@ ... @@@`, and longer for more parents, for a combined diff) gives the new side's start and line count and each old side's line count. Inside a hunk every line is a body line until those counts are used up, so a body line is never read as a header, whatever its text. A line `\ No newline at end of file` uses no count.
   - File headers (lines starting with `diff `, `---`, `+++`, `rename to`, `index`, the mode lines and the rest) are read only outside a hunk.
   - Every line starting with `diff ` (`diff --git`, `diff --cc`, `diff --combined`) ends any hunk and starts a new file; the new path of the file before it never carries over to it.
   - The numbers are parsed with `int`, never by slicing at a position; a start is a whole number of at least 0 (git writes 0 for an empty side), a count at least 0; an omitted count is 1, as git's format says.
   - Packager's addition, beside F10's reason: a hunk header whose numbers cannot be read is CANNOT SCAN reason `the patch cannot be read`; the body after it is never skipped silently.
2. **F2. A file's new path is the whole rest of its line** (answers: a path with a space cut at the space).
   - The new path is taken from the `+++ ` line, or from the `rename to ` line, or from the path of a `diff --cc ` or `diff --combined ` header, as the whole rest of the line after that prefix: one trailing tab dropped (git writes one after a path that holds a space), git's quoting undone where the rest begins and ends with a double quote, then, for the `+++ ` line only, the `b/` prefix removed (the `rename to` line and the combined headers carry no prefix). It is never split at a space.
   - A `+++ ` line whose path is the null device (`/dev/null`, built from parts as round 1's `_NULL_PATH`) gives no new path; such a file has no added lines.
   - The path from the `diff --git` line is never used as the new path.
3. **F3. A combined status has one path** (answers: a merge's combined statuses read as renames). The `-z` name-status list reads two paths (the old, then the new) only for a single-parent rename or copy status: `R` or `C` followed by one or more digits and nothing else. Any other status, including a merge's combined status of two or more letters (`RM`, `MM`, `AM`), has one path.
4. **F4. A patch path missing from the file list ends the scan** (answers: a patch path missing from the file list skipped). Every new path the patch names (F2) is in the commit's name-status list; where one is not, whether or not it holds a hit and whether or not it has added lines, the scan ends with exit 2, `push-scan: CANNOT SCAN - the patch and the file list disagree`, and prints no hit and no OK. The unlisted-path loop (547-555) goes; no added line is ever dropped.
5. **F5. No signature text, and a checked short hash** (answers: log.showSignature puts signature text into a hit line).
   - Every git call carries `-c log.showSignature=false` beside `-c color.ui=never`, in the one runner `git`.
   - The short hash is taken with `git rev-parse --short --end-of-options <full>`, stripped of its trailing newline, and must be hexadecimal (one or more of `0-9a-f`); a non-zero exit is `git rev-parse failed (exit <code>)`, and an output that is not hexadecimal is CANNOT SCAN reason `internal error`. It replaces round 1's `git log -1 --format=%h` (R9's `<short hash>` is now rev-parse's, the same abbreviation).
6. **F6. The user's diff settings change nothing** (answers: the user's diff.relative and prefix settings). Both `git show` calls (the name-status list and the patch) pass `--no-relative --src-prefix=a/ --dst-prefix=b/` in addition to round 1's options, so `diff.relative` (run from a subfolder), `diff.noprefix`, `diff.srcPrefix` and `diff.dstPrefix` change neither the files read nor the paths printed.
7. **F7. A name matches by one regular expression** (answers: the index shift after a letter that lower-cases to two characters). Each name matches through `re.compile("(?<![^\\W_])" + re.escape(name) + "(?![^\\W_])", re.IGNORECASE)`: a literal name, in any letter case, neither neighbour a letter or a digit. Never by indexes into a lower-cased copy.
8. **F8. A patch splits at newlines only** (answers: a form feed or a Unicode separator moving the line numbers). The patch is split into lines at `"\n"` only, one trailing `"\r"` stripped from each line; never with `str.splitlines`.
9. **F9. A printed path is escaped** (answers: a file name forging an output line). A path printed in a `line <path>:<n>` place is printed as it is where it holds none of these characters: a character of Unicode category `Cc`, `Zl` or `Zp`, a double quote, a backslash. Where it holds one, the whole path is printed inside double quotes, with `\a \b \t \n \v \f \r \" \\` for those characters, and a backslash and three octal digits for each UTF-8 byte of any other such character (U+0085 gives `\302\205`, U+2028 gives `\342\200\250`). Every other character is printed as it is. The hit test on the path (`line #<k>:<n>`, `file #<k>`) reads the real path, never the escaped one.
10. **F10. Two more reasons** (answers: an unexpected error reported as git missing, and an octal escape that raises).
    - The catch-all `except Exception` in `main` prints `push-scan: CANNOT SCAN - internal error`, not `git cannot be started` (which stays for git that cannot be started, in `git`).
    - `unquote_git` refuses an octal escape above 377 (a value above 255) with CANNOT SCAN reason `the patch cannot be read`.
    - The three new reasons `the patch and the file list disagree` (F4), `internal error` (F5, F10) and `the patch cannot be read` (F1, F10) join R9's closed list. No other reason is added; git's own text, a path and the base's words are still never printed.

## Acceptance criteria
- [ ] The Done section's pytest commands pass whole: `tests/test_program_push_scan.py` gives no failure (its eight round-2 cases included), and `tests/test_dump_cli.py` and `tests/test_allowlist.py` give no failure.
- [ ] F1-F10 hold as written; every round-1 requirement (R1-R12 of `handoff/TASK-067.md`) still holds, the owner's decision of 2026-11-18 included.
- [ ] No body line of a hunk is read as a header; no path is cut at a space; no combined status reads two paths; no patch path outside the file list is skipped; every git call carries `log.showSignature=false` (F1-F5).
- [ ] No output line holds a matched text, a name, a line, a path that holds a hit, or a raw control or separator character; every line of the output begins with `push-scan: ` (R9, F9).
- [ ] Done's grep over `bridge/cursor-bridge/push-scan.py` prints nothing, and its ASCII check prints `ascii ok` (R11).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `bridge/cursor-bridge/settings.bridge.json` is unchanged. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-087 (the parts this brief serves) is fully met: no stand-in, placeholder or "later" text in the program. The tests naming R-087 are the supervisor's.
- [ ] No new dependency (standard library only), option, configuration key or environment variable. No new Semgrep high finding. No exception escapes as a traceback, and none is turned into a pass (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit any test file or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall: one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (the program, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- **Windowless launches.** Every process the program starts is created with `creationflags=bridge_env.NO_WINDOW`, with `timeout=bridge_env.GIT_TIMEOUT`, through `subprocess.run`, never `Popen`, never through a shell. Capturing output does not prevent the window.
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section and the mutation self-check name, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- **Never run `push-scan.py` on this repository** or on any folder but the tests' scratch repositories (Context, "Development data").
- Never run the product, a migration, a seed or a test against the owner's live data. Never install anything.
- The owner's value (Context, the decision of 2026-11-18, pinned by the two `test_r087_owner_2026_11_18_` tests) is fixed: do not change it or those tests; report it if the work seems to need a change (rule 52).
- Do not refactor code outside the functions the Scope's limits name, even if it looks wrong. The items under "Not in this round" stay as they are.
- Follow existing conventions of `push-scan.py`: ASCII program text, ASCII output apart from path names, results returned as values, `ScanError(reason)` for every exit 2, `main()` returning the exit code.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. The program itself runs only read-only git commands.
- Numbers from git's output (a hunk header's starts and counts, an octal escape) are parsed with `int` (base 10, or base 8 for an escape), never by slicing a string at a fixed position; a start is a whole number of at least 0, a count at least 0, an octal escape at most 377 (F10).
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the scan after your run, and every mutant must fail a test. Before you finish, apply each of these to `push-scan.py` by hand, one at a time, run `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` from the Workspace root, and revert. List each in the report by its label and text, with the test id that caught it, or `not caught`:
  - N1 a `+++` line read inside a hunk (F1);
  - N2 a path cut at its first space (F2);
  - N3 a combined status read with two paths (F3);
  - N4 an unlisted patch path skipped (F4);
  - N5 `log.showSignature` left on (F5);
  - N6 `diff.relative` honoured (`--no-relative` dropped) (F6);
  - N7 the lower-cased index match restored (F7);
  - N8 `str.splitlines` restored for the patch (F8);
  - N9 a printed path not escaped (F9).

  Re-run round 1's M1-M13 (listed in `handoff/TASK-067.md`, Constraints) by label only where your change touched the code a mutant changes, and say for each of the others that its code is unchanged. You cannot add a test. A mutant no test catches is reported as `not caught`, with one line on the case that would catch it; the supervisor adds it.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: round 1's helpers, `bridge_env.NO_WINDOW` and `bridge_env.GIT_TIMEOUT`, the standard library (`re`, `unicodedata`), git's own output formats, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-067-r2-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for F1-F10, one line each on what meets it, naming the functions and their lines as the file stands after your change;
- the mutation self-check list, N1-N9, each with the test id that caught it (or `not caught` and the case that would), and the M1-M13 lines the mutation self-check asks for;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a git behaviour you expected, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. Examples:
- how each body line of a combined hunk uses the parents' counts and the new side's count (which column marks a line as present in which parent);
- that `git show -z --name-status` of a merge lists every path the merge's combined patch names, so F4 never fires on a merge git wrote itself;
- that `--src-prefix` and `--dst-prefix` on the command line override `diff.noprefix` in the git installed here.

One item per line: what you assumed | why | what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py`
3. `python tools/dump-cli.py --check` (expect exit 0)
4. `python tools/make-manifest.py`
5. `git restore bridge/cursor-bridge/VERSION`
6. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
10. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json` (expect no output: the file is unchanged)
11. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py` (expect no output and exit 1: the source holds none of the shapes R11 names. Quote the empty output and the exit code.)
12. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
13. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Where a failure body would print a temporary path, replace it with `<tmp>`.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 13, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
