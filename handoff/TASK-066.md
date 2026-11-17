---
record: brief
header: 1
id: "TASK-066"
round: 1
satisfies: [R-086]
scope: ["bridge/cursor-bridge/invisible-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_invisible.py", "tests/test_invisible_check.py", "tests/test_hotfix25a_guard_scope_invisible.py", "docs/BUILDER_NOTES.md", "handoff/TASK-066-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-066: the invisible-character check refuses by category (R-086)

Round cause: first round (no earlier round)

## Objective
`bridge/cursor-bridge/invisible-check.py` is the loop's control against characters a reader cannot see: it runs before every commit and in the secret-sentinel's scan, and it refuses a character that hides a token from a reviewer, reorders what a reviewer reads, or splits a line for some readers. Today it decides by a list of named code points (`INVISIBLE`, plus a loop adding U+2000..U+200A). A list misses what it does not name: the field met a test file holding a raw U+2028 and U+2029, which the program passed with `RESULT: OK` and the sentinel's own category scan caught (ISS-031, from TASK-050's security audit). The same class misses U+0085 and the C0 controls the list does not name. This increment replaces the list by a rule on the Unicode category, read from the standard library's `unicodedata`: a character is a finding when its category is Cc, Cf, Zl or Zp, or Zs other than U+0020, except U+0009, U+000A and U+000D anywhere and U+FEFF as the file's first character (line 1, column 1, as today). Every character the old list held is in those categories, so the list goes. Each finding prints as today, with the character's Unicode name in lower case, or with the code point alone where the character has no Unicode name. Nothing else about the program changes: its options, its exit codes, what it reads, its `--non-ascii` listing and its `RESULT:` lines stay exactly as built.

Satisfies: R-086 - `invisible-check.py` refuses by Unicode category (J1, ISS-031): every character of the categories Cc, Cf, Zl and Zp, and of Zs other than the plain space, is a finding, but for tab, line feed and carriage return and for the byte-order mark as a file's first character; a character with no Unicode name is named by its code point; the repository's own tracked files pass. (Full row: `docs/REQUIREMENTS.md`, line 112. The sweep of the repository's tracked files is already done by the supervisor, Context; your part is the program and its tests.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/invisible-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_invisible.py
- tests/test_invisible_check.py
- tests/test_hotfix25a_guard_scope_invisible.py
- docs/BUILDER_NOTES.md
- handoff/TASK-066-r1-report.md

Limits on these paths:
- `tests/test_program_invisible.py` is the supervisor's acceptance test file. Read it and run it. Edit nothing in it.
- `tests/test_invisible_check.py` and `tests/test_hotfix25a_guard_scope_invisible.py`: you may add cases of your own. Change no existing case, no existing helper and no existing line.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`. `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `bridge/cursor-bridge/invisible-check.py`: you change three things only: (a) in the module docstring, the part that lists the characters (lines 7-12, from `and lists each line holding a zero-width character` to `2026-10-25 C8, FB-010).`), rewritten to state the category rule and its allow-list; (b) `INVISIBLE` and its `for _cp in range(0x2000, 0x200B)` loop (lines 28-35), removed; (c) in `findings()`, the branch that decides a finding and its name (lines 77-78, the `elif cp in INVISIBLE ...` branch). Every other line stays as it is: the docstring's first line, the usage line `python invisible-check.py [<base-ref>] [--all] [--non-ascii]`, every other docstring sentence and the `--non-ascii` paragraph; `NO_WINDOW`, `BINARY_EXT`, `git()`, `changed_files()`, the binary and unreadable-file tests and the decoding in `findings()`, its `non_ascii` branch, `main()` and its output and exits (except as Requirement 3 says for the unnamed character's line), and the console reconfigure under `__main__`.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`. They are generated from this program's docstring by `tools/dump-cli.py`, and they are outside this increment's Scope (a Scope gap of the plan, recorded by the supervisor). Do NOT run `python tools/dump-cli.py` and do not edit either file. The supervisor regenerates the reference after your run, in a commit of its own. If you run `python tools/dump-cli.py --check`, it is expected to report the reference stale after your docstring edit; that is not your failure, and you fix nothing for it.
- `.githooks/pre-commit`, `tools/make-manifest.py`, `tools/dump-cli.py`, every other program under `bridge/cursor-bridge/`, and every test file not named in Scope (you run some of them, Done, and edit none).
- Any tracked file the program flags. The repository sweep is the supervisor's: a tracked file the program flags after your change is reported by path, line and code point, and fixed by the supervisor in a commit of its own, never by you.
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this increment:** `docs/DESIGN.md`, "Change: the program release", the bullet group **The scans** (line 345), bullet *J1 (ISS-031)* (line 346), quoted: "`invisible-check.py` refuses by Unicode category, Cc, Cf, Zl, Zp, and Zs other than the plain space, with a short allow-list (tab, line feed, carriage return; the byte-order mark as a file's first character, as today); a character with no Unicode name is named by its code point. It is the control TASK-050's audit names for a separator smuggled into an owner-written line." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-066` (line 1833): Scope, Scope notes and Done when.

**The plan's wording against the code as built (the code governs).** The plan's Done when says the program reads "the staged files, or the paths given". As built, it reads the text files changed against `<base-ref>` (default `HEAD`) plus the untracked ones, or every tracked text file with `--all`. Its options are `[<base-ref>] [--all] [--non-ascii]`. Its exits are 0 (none), 1 (at least one), 2 (cannot verify). Its output is ASCII. A binary file (by extension in `BINARY_EXT`, or a NUL byte in the first 8000 bytes) is skipped. The text is decoded as UTF-8 with replacement and split on LF only. All of that stays exactly as it is: add no option and no exit code, change nothing in what it reads, change nothing in the `--non-ascii` listing (its lines, its names in upper case with `(no name)` for an unnamed character, its count line, its exit behaviour), and change nothing in the `RESULT:` lines. The plan also speaks of fixtures "read through the paths the pre-commit gate gives": `.githooks/pre-commit` does not call `invisible-check.py`, so that clause has no object here and you do nothing for it.

**The repository sweep, already done.** Before this brief, in a commit of its own on this branch, the supervisor replaced 15 flagged characters in 5 tracked files with escape text: `handoff/BUG-032-r3.md`, `handoff/TASK-031-r9.md`, `handoff/TASK-033-r3.md`, `tests/test_invisible_check.py` and `tests/test_workflow_check.py`. A test fixture that needs such a character builds it at run time with `chr()`. Your own test cases must do the same: every character outside printable ASCII in a test file is built with `chr()` (or `bytes`), never typed, and never written as a backslash-u escape through your file-writing tool, which may write the real character in its place (KP-052). The program's own source stays printable ASCII; in its docstring a character is named by its code point as text, `U+2028`.

**The supervisor's acceptance tests.** `tests/test_program_invisible.py` names R-086 and fixes the interface; read it whole. It holds 23 cases:
- `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point`, parametrized over 18 characters (Cc: U+0001, U+0007, U+0008, U+000B, U+000C, U+001B, U+001F, U+007F, U+0085, U+009F; Cf: U+200E, U+2061, U+FFF9, U+E0041; Zl: U+2028; Zp: U+2029; Zs: U+1680, U+205F). Each writes `plain`, LF, `a<char>b`, LF to a changed file and expects exit 1 and exactly one line. Where `unicodedata.name` gives a name, the line is `INVISIBLE: doc.md:2:2 U+XXXX ` followed by the name, compared without regard to case. Where it gives none (every Cc character), the line is exactly `INVISIBLE: doc.md:2:2 U+XXXX`, nothing after the code point, not even a space.
- `test_r086_the_allow_list_passes_and_only_the_other_characters_are_findings`: U+FEFF at line 1 column 1, tab, CR, the plain space, U+00E9, U+2014 and U+4E2D pass; U+2028 on line 2 and U+FEFF at the start of line 3 are the two findings.
- `test_r086_every_tracked_file_is_read_with_all`, `test_r086_the_files_changed_against_a_base_and_the_untracked_files_are_read` and `test_r086_the_non_ascii_listing_keeps_the_exit_code` pin what it reads and the `--non-ascii` listing, unchanged.
- `test_r086_the_repository_s_tracked_files_pass` runs the Workspace's own program with `--all` over the Workspace and expects exit 0 and `RESULT: OK`. It runs where the Workspace is a git work tree and skips otherwise.

The file's docstring states that every case is red on the checkpoint code but the last. You will see the count in your first run; quote it in your report.

**The existing tests that pin the old behaviour, still in force:**
- `tests/test_invisible_check.py`, `test_invisible_characters_in_changed_files_are_listed`: U+202E, U+200B and U+00AD in changed files are findings; a leading U+FEFF and a binary `.png` are not.
- `tests/test_hotfix25a_guard_scope_invisible.py`, lines 319-356: `test_no_break_and_fixed_width_spaces_are_flagged` expects U+00A0, U+2007, U+202F, U+2000, U+2005, U+200A and U+3000 flagged and the lower-case names `no-break space`, `ideographic space` and `figure space` in the output; `test_non_ascii_lists_every_non_ascii_character_with_its_name` pins the `--non-ascii` lines and that only those lines appear on request.
- `tests/test_release_t_ceiling.py` line 128 asserts the program's source holds `invisible-check.py [<base-ref>]` (the usage line, which stays).

**Security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. The program is the loop's control against characters that hide a token from a reviewer or split a line for some readers (ISS-031; TASK-050's audit found `splitlines` reading a smuggled line across U+2028). Trust boundary: the files it reads are outside input, possibly written by a tool or an agent; a file it cannot read or decode is handled as today. It reads files and prints ASCII; it writes nothing, runs only `git` (windowless, as today), reaches no network and adds no dependency. `unicodedata`'s database is the running Python's, and the rule follows it: a character the running Python's database places in one of the five categories is a finding, whatever its Unicode version. No secret, no key and no computer path appears in anything you write.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: run the program from the Workspace's `bridge/cursor-bridge/` only, through the tests (scratch repositories under pytest's `tmp_path`) and the one `--all` run over the Workspace that the Done section names, which reads and writes nothing else. Never install anything and never touch anything under `~/.claude`.

**No owner's value** in this increment (rule 52).

## Diagrams
None (the plan's `Diagrams:` field is `none`).

## Requirements
1. **The rule.** `findings(path)` (without `non_ascii`) returns a finding for each character whose `unicodedata.category` is `Cc`, `Cf`, `Zl` or `Zp`, or is `Zs` and is not U+0020, except: U+0009, U+000A and U+000D anywhere, and U+FEFF at line 1, column 1 (the existing first-character test, `n == 1 and i == 0`). A U+FEFF anywhere else, the start of any other line among them, is a finding. No other character is a finding, and no character in those categories is exempt beyond that allow-list.
2. **No list.** `INVISIBLE` and its `range(0x2000, 0x200B)` loop are gone; no list or set of code points decides a finding. The decision reads `unicodedata` only.
3. **The name.** A finding's name is `unicodedata.name(ch).lower()` where the character has a Unicode name (so the existing lower-case names stand, `no-break space` and `right-to-left override` among them). Where it has none (every Cc character), the finding prints as `INVISIBLE: <path>:<line>:<column> U+XXXX`, the line ending at the code point: no trailing space, no placeholder text such as `(no name)`. Every named finding prints exactly as today, `INVISIBLE: <path>:<line>:<column> U+XXXX <name>`. The output stays ASCII.
4. **Everything else unchanged.** The options, the exits, the files read, the binary skip, the decoding and the LF split, the `--non-ascii` listing and its count line, and both `RESULT:` lines are byte-for-byte as today (Context, "The plan's wording against the code as built").
5. **The docstring.** The part named in Scope as (a) is rewritten to state the category rule (Cc, Cf, Zl, Zp, and Zs other than U+0020) and its allow-list (U+0009, U+000A, U+000D anywhere; U+FEFF as the file's first character), and that a character with no Unicode name is named by its code point alone. The usage line `  python invisible-check.py [<base-ref>] [--all] [--non-ascii]` and every other sentence of the docstring stay word for word. The docstring stays printable ASCII.
6. **Your tests.** Add cases of your own to `tests/test_invisible_check.py` or `tests/test_hotfix25a_guard_scope_invisible.py` only where the acceptance tests leave a gap you find (for example a Cf character from the old list, U+180E, still named as before, or a CR at the end of each line of a CRLF file giving no finding). Each case you add names `R-086` in its name, docstring or a comment, builds every non-ASCII character with `chr()`, and follows the file's existing helpers (`changed_repo`, `run`, `git`). A parametrized case has a plain `ids=` list.
7. **The manifest.** Regenerate `bridge/cursor-bridge/MANIFEST.json` with `python tools/make-manifest.py`, then restore `bridge/cursor-bridge/VERSION` (Done).

## Acceptance criteria
- [ ] `tests/test_program_invisible.py` passes whole: 23 cases, the last run (not skipped) here because the Workspace is a git work tree.
- [ ] `tests/test_invisible_check.py`, `tests/test_hotfix25a_guard_scope_invisible.py`, `tests/test_workflow_check.py` and `tests/test_release_t_ceiling.py` pass.
- [ ] `python bridge/cursor-bridge/invisible-check.py --all`, run from the Workspace root, exits 0 and prints `RESULT: OK`. If it flags a tracked file, you fix nothing in that file: report each line it printed, and the supervisor fixes the file.
- [ ] `INVISIBLE` and its loop are gone; the decision is the category rule of Requirement 1; an unnamed character's line ends at its code point (Requirements 1-3).
- [ ] The options, exits, files read, `--non-ascii` listing and `RESULT:` lines are unchanged (Requirement 4); the usage line and every docstring sentence outside the rewritten part are unchanged (Requirement 5).
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` exits 0.
- [ ] MANIFEST is regenerated; `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`; `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are not listed by `git status --short` as changed by you.
- [ ] R-086 (the program's part) is fully met: no stand-in, placeholder or "later" text, and every test you add names R-086.
- [ ] No option added. No new dependency, configuration key or environment variable. No new Semgrep high finding.

## Constraints
- Do not add dependencies (the standard library only: `unicodedata` is already imported).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_invisible.py`. If a case there seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **Characters by code point (KP-052).** Every character outside printable ASCII in a file you write is built at run time with `chr()` or given as bytes, never typed and never written as a backslash-u escape through your file-writing tool. The program's source and the report stay printable ASCII; name a character by its code point as text, `U+2028`.
- **Windowless launches.** The program's only process, `git`, keeps `creationflags=NO_WINDOW`. In tests a launch needs no `creationflags` argument, because `tests/conftest.py` makes every launch windowless; where a test does write one, that line carries the literal text `CREATE_NO_WINDOW` (`tests/test_tests_windowless.py` refuses it otherwise). Every subprocess and git call in a test of yours has a timeout, and each child ends before its test does.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section names, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- Do not refactor code outside the parts the Scope's limits name, even if it looks wrong. Do not "improve" the `--non-ascii` listing, the messages or the binary test.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"). Do not run `tools/dump-cli.py`.
- Follow existing conventions in the files you touch: ASCII program text, ASCII output, the existing comment style.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. Your tests may run git inside their own temporary folders.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the category test after your run, and every mutant must fail a test. Before you finish, apply each of these by hand to `invisible-check.py`, one at a time, run `python -m pytest -p no:cacheprovider -q tests/test_program_invisible.py` from the Workspace root, and revert. List each in the report by its label, with the test id that caught it:
  - M1 the category Cc dropped from the rule;
  - M2 the category Cf dropped;
  - M3 the category Zl dropped;
  - M4 the category Zp dropped;
  - M5 the category Zs dropped;
  - M6 the allow-list widened by U+000B;
  - M7 the allow-list widened by U+0085;
  - M8 the first-character rule applied anywhere (U+FEFF allowed at the start of any line);
  - M9 the name dropped for a named character (the line ending at the code point);
  - M10 a placeholder printed for an unnamed character (for example `(no name)` after the code point).

  Each must make a case of `tests/test_program_invisible.py` fail. A mutant no case catches is reported as `not caught` with why; do not edit that file. Confirm after the last revert that `git diff bridge/cursor-bridge/invisible-check.py` shows your intended change only.
- **Known failures.** On the checkpoint code, the cases of `tests/test_program_invisible.py` are red but the last (its docstring). None is known in the other files of the Done section. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `unicodedata.category` and `unicodedata.name`, the existing `findings()` loop and `main()`'s print, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-066-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for Requirements 1-7, one line each on what meets it, naming the function and its lines as the file stands after your change;
- the mutation self-check list, M1-M10, each with the test id that caught it (or `not caught` and why);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a behaviour of `unicodedata` you expected (for example, that every Cc character has no name in the running Python's database while every Cf, Zl, Zp and Zs character has one), an ambiguous requirement you resolved one way, a value you chose. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python -c "import sys, unicodedata; print(sys.version); print(unicodedata.unidata_version)"`
3. `python tools/make-manifest.py`
4. `git restore bridge/cursor-bridge/VERSION`
5. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_invisible.py tests/test_invisible_check.py tests/test_hotfix25a_guard_scope_invisible.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_workflow_check.py tests/test_release_t_ceiling.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
7. `python bridge/cursor-bridge/invisible-check.py --all` (expect exit 0 and `RESULT: OK`; quote every line it printed)
8. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` (expect exit 0)
9. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` must not be listed; if one is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block, and with its exit code where the step names one.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 9, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
