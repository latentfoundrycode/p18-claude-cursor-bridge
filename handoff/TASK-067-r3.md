---
record: brief
header: 1
id: "TASK-067"
round: 3
satisfies: [R-087]
scope: ["bridge/cursor-bridge/push-scan.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-067-r3-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-067 round 3: what git shows is never narrowed (R-087)

Round cause: security - Review A rejected and the security audit failed round 2: log.showRoot=false empties a root commit's patch and file list, and a submodule entry hidden by diff.ignoreSubmodules or by the commit's own .gitmodules (ignore = all) is never read, so the scan prints OK.

Blocking class: security - against the brief and the register (R-087: every commit of `<base>..HEAD` is read, its added lines and added file names, and the scan never prints OK where it did not read): a user setting (`log.showRoot`, `diff.ignoreSubmodules`) or a commit's own content (its `.gitmodules`) narrows what `git show` prints, so a root commit's lines and a submodule entry's name are never read and the scan exits 0; held by the supervisor's round-3 cases, the last section of `tests/test_program_push_scan.py` (their run on round 2's tree: Context, "Known failures before your change").

## Objective
Fix the following confirmed defects in the pre-push scan, and nothing else.

This is round 3 of TASK-067, the last round the review ceiling allows. Rounds 1 and 2 built `bridge/cursor-bridge/push-scan.py`, its allow entry and the generated files, and round 2 rewrote the reading of the patch and the file list. All of that stays except what G1 to G7 below change. The supervisor commits round 2's tree together with this brief and the round-3 test cases before your run, so the line numbers below hold when you start.

**The confirmed defects** (Review A and the security audit of round 2; each is now a case of the supervisor's, the round-3 section of `tests/test_program_push_scan.py`): the scan reads what `git show` prints, and git lets the user's configuration and the commit's own `.gitmodules` narrow that. With `log.showRoot=false` set, `git show` of a root commit prints no patch and no file list, so a root commit brought into the range (a merge of an unrelated history) is read as empty. With `diff.ignoreSubmodules=all` in the user's configuration, or `ignore = all` for that submodule in the commit's own `.gitmodules`, a submodule entry (a gitlink, mode 160000) is left out of both the file list and the patch, so its own name is never scanned. With `diff.submodule` set to `diff` or `log`, git inlines a submodule's own changes under paths that are not files of the commit's list. With `diff.suppressBlankEmpty=true`, a blank context line is printed without its leading space, which `added_lines` (round 2's F1, lines 506-507) refuses as `the patch cannot be read`. Further: whether a file's lines are placed by position (`line #<k>:<n>`) is decided on the real path only (line 677), but the printed form can hold a name the real path does not (a vertical tab, U+000B, prints as a backslash and a `v`, which can complete a name); `quote_path` (614-637) leaves a format character (Unicode category `Cf`, such as U+202E, the right-to-left override) raw in a printed path, so a terminal can show a hit line reordered; and `take_token` (366-383) has been unused since round 2.

Satisfies: R-087 - The pre-push scan is a program (C2): `push-scan.py [<base>]` (default `origin/<the default branch>`) reads every commit of `<base>..HEAD`, its message, author and committer lines, added lines and added file names, for a path of this computer (a drive-letter path, `/Users/`, `/home/`, `AppData`; a placeholder segment such as `<name>` passes) and for the owner's account names, [...]; exit 0 clean, 1 on a hit, which prints the commit, the place, the line's number and whether a path or a name was found and never the matched text, a hit in a file's own name placed by that file's position in the commit's list and not by its path, 2 where git cannot be read; [...]. (Full text: its row in `docs/REQUIREMENTS.md`, line 113. This round serves "every commit" and "added file names" against the user's settings and the commit's own `.gitmodules`, and the printed path.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/push-scan.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-067-r3-report.md

Limits on these files:
- `bridge/cursor-bridge/push-scan.py`: only what G1 to G7 change: the runner `git` (lines 50-66, its argv at line 51), `quote_path` (614-637), in `scan_commit` (640-691) the two `git show` calls (646-651 and 654-659) and the line that decides whether a file's lines are placed by position (677), and the removal of `take_token` (366-383). Every other function, refusal, message, note and exit stays byte-identical to round 2's tree; in particular `added_lines`, `_parse_hunk_header`, `parse_name_status`, the file-name hit (678-680) and the disagreement check (688-690) do not change. The module docstring and the parser's description and help do not change.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), and only if the parser's text changed (it should not). Afterwards `python tools/dump-cli.py --check` must exit 0. Never edit either by hand.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`; restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Do not modify anything else. `bridge/cursor-bridge/settings.bridge.json` is done (round 1) and must not change. Every test file is read-only for you: read and run `tests/test_program_push_scan.py`, `tests/test_dump_cli.py` and `tests/test_allowlist.py`, edit none of them.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, the diagrams included. Round 1's and round 2's briefs (`handoff/TASK-067.md`, `handoff/TASK-067-r2.md`) and reports (`handoff/TASK-067-r1-report.md`, `handoff/TASK-067-r2-report.md`) stay as they are.
- `bridge/cursor-bridge/settings.bridge.json`, `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`.
- Every test file. You add no test file and edit none; a gap is reported (Constraints, mutation self-check).
- `bridge/agents/secret-sentinel.md`, `bridge/commands/supervisor.md`, the loop's text under `bridge/cursor-bridge/workflow/` (TASK-082).
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them, Done, and edit neither).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.
- The disagreement check (round 2's F4, `scan_commit` lines 688-690) stays exactly as written. After G3 no commit the supervisor knows of reaches it; it is a second line of defence, and the supervisor's mutants file marks its removal as expected to survive. Do not remove, weaken or "simplify" it.
- **Not in this round** (recorded leads; do not change their behaviour): binary files, files marked `-diff`, and `core.bigFileThreshold`, which show no lines; spaces in a printed path faking fields inside one hit line; `owner_of` on remotes with more than two path segments; resolving git's absolute path; git's stripping of trailing punctuation from an ident's name; copy (`C`) statuses (`if status[:1] in ("A", "R"):` at line 678 stays as it is).

## Context
**Rounds 1 and 2 govern everything this brief does not change:** `handoff/TASK-067.md` (R1-R12, M1-M13) and `handoff/TASK-067-r2.md` (F1-F10, N1-N9). Read both whole. Their Context sections (the design `docs/DESIGN.md` C2, the privacy paragraph, the import pattern, the trust boundaries, development data, host) and their Constraints hold for this round unchanged, except where G1 to G7 change them. Three of them in particular:
- **The owner's decision of 2026-11-18 (rule 52, the owner's value):** the names of the repository's configured git identity (`git config user.name`, the local part of `git config user.email`) are public, dropped from the names searched and counted in N2, and the author and committer lines that carry the configured identity are no finding. The tests `test_r087_owner_2026_11_18_the_configured_identity_is_no_finding_anywhere` and `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped` pin it. Do not change this behaviour or those tests; if the work seems to need a change, stop and report it.
- **R11, the source scans clean:** the program's own source holds no literal of the shapes the scan reads as a path (a drive letter with a colon and a slash or backslash, `/Users/`, `/home/`, `AppData`, a URL literal such as `https:` with its slashes), and the source is ASCII only. Done steps 11 and 12 verify it. G6 names a Unicode category by its name (`Cf`); no character outside ASCII is typed in the source.
- **The printed reasons are round 2's closed list.** No reason is added this round.

**The supervisor's round-3 cases.** `tests/test_program_push_scan.py`, the section headed `# ---------------------------------------------------------------- round 3: what git shows is never narrowed (the reviews of round 2)` (line 480 to the end), read it whole; they fix the expected outputs. `_index_add` (line 482) adds one index entry by `git update-index --cacheinfo` (a path the file system may refuse, or a gitlink):
- `test_r087_a_submodule_hidden_by_the_user_s_setting_is_still_read` (line 491): G2. The user's global config sets `diff.ignoreSubmodules = all`; the commit adds one gitlink whose own name holds a name; expected exactly `HIT <h> file #1 name`.
- `test_r087_a_submodule_hidden_by_the_commit_s_own_gitmodules_is_still_read` (line 504): G2. The commit adds `.gitmodules` (file #1) with `ignore = all` for the submodule (its path written in git-config quoting split in two, so the file's own text holds no name) and the gitlink (file #2); expected `HIT <h> file #2 name` among the hits.
- `test_r087_a_root_commit_in_the_range_is_read_whatever_log_show_root_says` (line 520): G1. The user's config sets `log.showRoot = false`; an orphan root commit is merged in with `--allow-unrelated-histories`; expected exactly the root's `line imported.md:2 path`.
- `test_r087_a_blank_context_line_is_read_whatever_diff_suppress_blank_empty_says` (line 536): G4. The user's config sets `diff.suppressBlankEmpty = true`; the hunk's context holds a blank line; expected exactly `line notes.md:4 path`.
- `test_r087_a_path_whose_escaped_form_holds_a_name_is_placed_by_its_position` (line 546): G5. The file's name is U+000B followed by the login without its first letter, then `.md`; the real path holds no name, the text `quote_path` prints for it does; expected exactly `line #1:2 path` (and no `file #1` hit: the file-name hit is decided on the real path only).
- `test_r087_a_format_character_in_a_printed_path_is_escaped` (line 558): G6. The file's name is `a`, U+202E, `b.md`; expected exactly the place `line "a\342\200\256b.md":2` (a double quote, `a`, a backslash and `342`, a backslash and `200`, a backslash and `256`, `b.md`, a double quote), and U+202E nowhere in the output.
- `test_r087_a_submodule_s_own_diff_is_never_inlined` (line 571): G2, G3, a static read of the source: `src.count("--submodule=short") >= 2 and src.count("--ignore-submodules=none") >= 2`. Each of the two option texts must therefore stand written out in the source once per `git show` call, not once in a shared constant.

The test file stays ASCII (KP-052): each character outside ASCII in it is written by `chr()`. Your own source and report stay ASCII.

**The code as it stands** (round 2's tree, line numbers verified):
- `git(sub, args)` (50-66) is the one `subprocess.run`; its argv (51) is `["git", "--no-pager", "-c", "color.ui=never", "-c", "log.showSignature=false", sub] + list(args)`.
- `scan_commit` (640-691): the short hash from `git rev-parse --short` (641); the commit object from `git cat-file -p` (642); the file list from `git show` with `["-z", "--name-status", "-M", "--format=", "--no-ext-diff", "--no-textconv", "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/", "--end-of-options", full]` (646-651); the patch from `git show` with `["-M", "--format=", "--no-ext-diff", "--no-textconv", "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/", "--end-of-options", full]` (654-659); `hidden = bool(kinds_of(path, names))` (677); the file-name hit for an `A` or `R` status on `kinds_of(path, names)` (678-680); the place `"line #%d:%d"` where `hidden`, otherwise `"line %s:%d" % (quote_path(path), number)` (683-686); the disagreement check (688-690).
- `quote_path(path)` (614-637): quotes where the path holds a double quote, a backslash, or a character of category `Cc`, `Zl` or `Zp` (the check at 618); inside the quotes the nine single-character escapes, then three-digit octal for each UTF-8 byte of any other character of those categories (the branch at 631-633).
- `added_lines` (478-560): inside a hunk a body line shorter than its prefix columns is refused (506-507), so an empty line, which `diff.suppressBlankEmpty=true` writes for a blank context line, is `the patch cannot be read`. G4 removes the cause in the runner; this refusal stays.
- `take_token` (366-383): no caller in the program or in any test.

**Known failures before your change.** The supervisor's known run on round 2's tree (`run/agent/TASK-067-r3-known.out`) printed: `7 failed, 32 passed`, the seven round-3 cases, each on its assertion (the two submodule cases and the root-commit case printed `push-scan: OK`; the blank-context case `CANNOT SCAN - the patch cannot be read`; the escaped-path case printed the path; the format-character case printed U+202E raw; the static case found no `--submodule=short`). Every round-1 and round-2 case of `tests/test_program_push_scan.py`, and `tests/test_dump_cli.py` and `tests/test_allowlist.py`, passed in round 2's own run (`373 passed, 20 skipped`). All must pass after your change.

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. The commits' contents (D-004 marks them `UNTRUSTED`), a commit's own `.gitmodules` and file names included, the names file, the environment, git's configuration values and the `<base>` argument are outside input. Round 2's rule stands and this round extends it: no commit content, file name or user setting may narrow what git shows the scan, make it miss a place, misplace a hit, forge or reorder an output line, or print OK where it could not read; where the program cannot read what git wrote, it ends with exit 2, never with a pass.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: run `push-scan.py` only through the tests, on their scratch repositories under `tmp_path`. Never run it on this repository (it would read the owner's real account names). Never install anything and never copy anything under `~/.claude`.

**Host.** Windows 11, with Python as on the owner's interpreter, git as installed.

## Diagrams
Unchanged from rounds 1 and 2 (`handoff/TASK-067.md`, Diagrams): `docs/diagrams/D-002-components.md` draws `push_scan --> bridge_env` and `dump_cli -.-> push_scan`; `docs/diagrams/D-004-context-dfd.md` draws the flows into `p_push_scan` and the one flow out:

```mermaid
p_push_scan -->|"hits to the terminal only: commit, place, line number, never the matched text; nothing leaves the computer (R-087)"| p_supervisor
```

`push-scan.py` imports `bridge_env` and no other bridge program, writes nothing, and reaches nothing beyond read-only git. If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
1. **G1. A root commit is always read** (blocking; answers: `log.showRoot=false` empties a root commit's patch and file list). The runner `git` adds `-c log.showRoot=true` beside `-c log.showSignature=false`, so every git call carries it and a root commit in the range is read, its file list and its added lines.
2. **G2. No submodule entry is hidden** (blocking; answers: a submodule entry hidden by `diff.ignoreSubmodules` or by the commit's own `.gitmodules`). Both `git show` calls (the name-status list and the patch) pass `--ignore-submodules=none`, so neither the user's `diff.ignoreSubmodules` nor a commit's own `.gitmodules` `ignore` setting hides a submodule entry. A submodule entry is a file of the commit's list like any other: its own name is scanned and a hit in it is placed by position (`file #<k>`), and its patch's added line is read like any added line.
3. **G3. A submodule's own changes are never inlined.** Both `git show` calls pass `--submodule=short`, so the user's `diff.submodule` (`diff` or `log`) never inlines a submodule's own changes under paths outside the file list. Each of `--ignore-submodules=none` and `--submodule=short` is written out in each call's argument list (the static case counts at least two of each in the source).
4. **G4. A blank context line keeps its space.** The runner `git` adds `-c diff.suppressBlankEmpty=false`, so a blank context line keeps its leading space and a hunk beside a blank line is read, not refused. The parser (`added_lines`) does not change.
5. **G5. The printed form decides placement too.** Whether a file's lines are placed by position (`line #<k>:<n>`) is decided on the real path and also on the text `quote_path` would print for it: where either holds a hit of either kind, the path is never printed. The file-name hit itself (`file #<k>`, lines 678-680) is still decided on the real path only.
6. **G6. A format character is escaped.** `quote_path`'s set of characters that force quoting gains Unicode category `Cf` (format characters, such as U+202E), and inside the quotes each such character is escaped by three-digit octal for each of its UTF-8 bytes, as the other control characters are (U+202E gives a backslash and `342`, a backslash and `200`, a backslash and `256`). The quoting test and the escaping branch name the same set of categories.
7. **G7. `take_token` goes** (minimal code). The function, unused since round 2, is removed. Nothing else is removed.

## Acceptance criteria
- [ ] The Done section's pytest commands pass whole: `tests/test_program_push_scan.py` gives no failure (its seven round-3 cases included), and `tests/test_dump_cli.py` and `tests/test_allowlist.py` give no failure.
- [ ] G1-G7 hold as written; every requirement of rounds 1 and 2 (R1-R12 of `handoff/TASK-067.md`, F1-F10 of `handoff/TASK-067-r2.md`) still holds, the owner's decision of 2026-11-18 included.
- [ ] Every git call carries `-c log.showRoot=true` and `-c diff.suppressBlankEmpty=false` beside `-c log.showSignature=false`; both `git show` calls carry `--ignore-submodules=none` and `--submodule=short` (G1-G4).
- [ ] No output line holds a matched text, a name, a line, a path whose real or printed form holds a hit, or a raw control, separator or format character; every line of the output begins with `push-scan: ` (R9, F9, G5, G6).
- [ ] `take_token` is gone; the disagreement check (688-690) is unchanged; no other function outside the Scope's limits changed.
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
- **Windowless launches.** Every process the program starts is created with `creationflags=bridge_env.NO_WINDOW`, with `timeout=bridge_env.GIT_TIMEOUT`, through `subprocess.run`, never `Popen`, never through a shell. Capturing output does not prevent the window.
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section and the mutation self-check name, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- **Never run `push-scan.py` on this repository** or on any folder but the tests' scratch repositories (Context, "Development data").
- Never run the product, a migration, a seed or a test against the owner's live data. Never install anything.
- The owner's value (Context, the decision of 2026-11-18, pinned by the two `test_r087_owner_2026_11_18_` tests) is fixed: do not change it or those tests; report it if the work seems to need a change (rule 52).
- Do not refactor code outside the parts the Scope's limits name, even if it looks wrong. The items under "Not in this round" and the disagreement check stay as they are.
- Follow existing conventions of `push-scan.py`: ASCII program text, ASCII output apart from path names, results returned as values, `ScanError(reason)` for every exit 2, `main()` returning the exit code.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. The program itself runs only read-only git commands.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the scan after your run, and every mutant but the one it marks as expected to survive must fail a test. Before you finish, apply each of these to `push-scan.py` by hand, one at a time, run `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` from the Workspace root, and revert. List each in the report by its label and text, with the test id that caught it, or `not caught`:
  - P1 `-c log.showRoot=true` removed from the runner (G1);
  - P2 `--ignore-submodules=none` removed from both `git show` calls (G2);
  - P3 `--submodule=short` removed from both `git show` calls (G3);
  - P4 `-c diff.suppressBlankEmpty=false` removed from the runner (G4);
  - P5 the escaped-text check of G5 removed (placement decided on the real path only);
  - P6 `Cf` removed from `quote_path`'s set (G6).

  Re-run an earlier mutant by its label only where your change touched the code it changes: N5 (`log.showSignature` left on; the runner's argv), N6 (`--no-relative` dropped; the two `git show` calls), N9 (a printed path not escaped; `quote_path`) and M10 (a file whose own path holds a hit placed by its path; line 677). For every other mutant of rounds 1 and 2 (M1-M13, N1-N9), say in one line that its code is unchanged; N4 (the disagreement check removed) stays expected to survive and is not re-run. You cannot add a test. A mutant no test catches is reported as `not caught`, with one line on the case that would catch it; the supervisor adds it.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: round 2's helpers (`kinds_of`, `quote_path`), `bridge_env.NO_WINDOW` and `bridge_env.GIT_TIMEOUT`, the standard library (`unicodedata`), git's own options, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-067-r3-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for G1-G7, one line each on what meets it, naming the functions and their lines as the file stands after your change;
- the mutation self-check list, P1-P6, each with the test id that caught it (or `not caught` and the case that would), and the N5, N6, N9 and M10 lines and the unchanged-code lines the mutation self-check asks for;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a git behaviour you expected, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. Examples:
- that `--ignore-submodules=none` on the command line overrides a submodule's `ignore` setting that git reads from a `.gitmodules` present only in the index or the commit, not in the work tree, in the git installed here;
- that `--submodule=short` on the command line overrides `diff.submodule` for both the name-status list and the patch;
- that `-c log.showRoot=true` makes `git show` of a root commit print its file list and its patch whatever the user's configuration holds.

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
