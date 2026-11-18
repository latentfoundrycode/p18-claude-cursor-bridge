---
record: brief
header: 1
id: "TASK-067"
round: 1
satisfies: [R-087]
scope: ["bridge/cursor-bridge/push-scan.py", "bridge/cursor-bridge/settings.bridge.json", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-067-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-067: the pre-push scan as a program (R-087)

Round cause: first round (no earlier round)

## Objective
Before every push the supervisor checks that no commit of the branch carries a path of this computer or one of the owner's account names, because the repository is public. Today that check is a hand-run `git log -p` read by eye. This increment makes it a program, `bridge/cursor-bridge/push-scan.py`, installed as `python ~/.claude/cursor-bridge/push-scan.py [<base>]`. It reads every commit of `<base>..HEAD` with read-only git commands: the message, the author and committer lines, the added lines, and the added or renamed file names. It reports each place that holds a path of this computer (by general patterns) or one of the owner's account names (derived at run time, never taken from the command line). A hit names the commit, the place and the kind, and never the matched text, the line, or a path that holds a hit: the supervisor's terminal is recorded in the session's transcript, so a printed hit would put the name where the scan exists to keep it from. Exit 0 clean, 1 on any hit, 2 where git or the base cannot be read, never a pass. The program gets its allow entry, and the generated files (the command reference and MANIFEST) are regenerated. The texts that call the program (`secret-sentinel.md`, step 8's "Before every push") are TASK-082's, not yours.

Satisfies: R-087 - The pre-push scan is a program (C2): `push-scan.py [<base>]` (default `origin/<the default branch>`) reads every commit of `<base>..HEAD`, its message, author and committer lines, added lines and added file names, for a path of this computer (a drive-letter path, `/Users/`, `/home/`, `AppData`; a placeholder segment such as `<name>` passes) and for the owner's account names, which are never on the command line but derived at run time (the profile folder's name, `USERNAME` or `USER`) and extended by the optional per-computer file `~/.cursor-bridge/names.txt`, a name equal to the owner segment of the remote's address or to a name of the repository's configured identity (`git config user.name`, the local part of `user.email`) dropped as public (the owner's decision of 2026-11-18 for the identity's names) and a commit's author and committer lines no finding where they carry the repository's configured identity; exit 0 clean, 1 on a hit, which prints the commit, the place, the line's number and whether a path or a name was found and never the matched text, a hit in a file's own name placed by that file's position in the commit's list and not by its path, 2 where git cannot be read; [...]. (Full text: its row in `docs/REQUIREMENTS.md`, line 113. This brief serves the program. The sentence in `secret-sentinel.md` and step 8 is TASK-082's.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/push-scan.py
- bridge/cursor-bridge/settings.bridge.json
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-067-r1-report.md

Limits on these paths:
- `bridge/cursor-bridge/push-scan.py` is new. You write all of it.
- `bridge/cursor-bridge/settings.bridge.json`: add exactly one line to the `allow` list, the entry `"Bash(python ~/.claude/cursor-bridge/push-scan.py:*)",` placed directly after the line `"Bash(python ~/.claude/cursor-bridge/records-migrate.py:*)",` (line 72), beside the other cursor-bridge program entries. Change nothing else in the file. It must stay valid JSON.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done). Afterwards `python tools/dump-cli.py --check` must exit 0. Never edit either by hand.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`. `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Read-only for you (already done and committed by the supervisor on this branch, before this brief; the plan's Scope names them, this brief does not):
- `docs/diagrams/D-002-components.md` (the edge `dump_cli -.-> push_scan` and the count fourteen, commit 7c73585);
- `tests/test_program_push_scan.py` (the acceptance tests, the supervisor's commits on this branch);
- `tests/test_dump_cli.py` (its `ARGPARSE` tuple gains `push-scan.py`, line 34);
- `tests/test_allowlist.py` (the pin `test_r087_push_scan_rule_in_allow`, line 257).

Read and run them. Edit none of them.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, the diagrams included.
- Every test file. You add no test file and edit none; the acceptance tests are the supervisor's, and so is any further case (report a gap instead, Constraints, mutation self-check).
- `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`. If `bridge_env` lacks something you need, write it in `push-scan.py` or stop and report it; do not change `bridge_env`.
- `bridge/agents/secret-sentinel.md`, `bridge/commands/supervisor.md`, the loop's text under `bridge/cursor-bridge/workflow/` (TASK-082).
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them, Done, and edit neither).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this increment:** `docs/DESIGN.md`, "Change: the program release", the bullet *C2* (line 347): read it whole. The privacy paragraph at line 433 says the names reach the program from the environment and a per-computer file and are never printed. The plan entry is `docs/BUILD_PLAN.md`, `### TASK-067` (line 1844), its Done when.

**The owner's decision of 2026-11-18 (rule 52, the owner's value).** `docs/INVENTORY.md`, Decisions (line 232), and `docs/CHANGES.md` (2026-11-18): the names of the repository's configured git identity (`git config user.name`, and the local part of `git config user.email`, before the `@`) are public. Such a name is dropped from the names searched, like the owner segment of the remote's address, counted in the note, and never printed. The author line and the committer line that carry the configured identity are no finding. The names searched are the profile folder's name, `USERNAME` or `USER`, and the lines of `~/.cursor-bridge/names.txt`; the identity's names are never added to them. The tests `test_r087_owner_2026_11_18_the_configured_identity_is_no_finding_anywhere` and `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped` pin it (the second has a profile folder name and a login equal to the identity's names, and a further searched name in the identity's address domain). Do not change this behaviour or that test; if the work seems to need a change, stop and report it.

**The reality check (the supervisor's, on this branch's checkpoint).**
- `bridge/cursor-bridge/push-scan.py` does not exist yet.
- `bridge/cursor-bridge/bridge_env.py` has **no general git-run helper**, although the plan's Done when says "importing `bridge_env` for its git helper". What it has, and what you use: `NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0` (line 37) for every `creationflags`, and `GIT_TIMEOUT = 30` (line 416, seconds) for every subprocess `timeout`. The program writes its own small read-only git runner with `subprocess.run` (never `Popen`), every call with `timeout=bridge_env.GIT_TIMEOUT` and `creationflags=bridge_env.NO_WINDOW`.
- The import follows the pattern of `bridge/cursor-bridge/records-migrate.py` (lines 15-17): `HERE = os.path.dirname(os.path.abspath(__file__))`, `sys.path.insert(0, HERE)`, `import bridge_env` (a plain `import`, which the static test reads).
- argparse, with `def build_parser():` at module top level taking no argument and returning the parser, and `def main():` (no argument) calling it and building no parser of its own, as `records-migrate.py` lines 26-31 do. The module has a docstring and an `if __name__ == "__main__":` block. `tools/dump-cli.py` loads every program of `bridge/cursor-bridge/` that has a `__main__` block and a top-level `build_parser` (D-002, line 20), imports it and calls `build_parser()`: importing the module must run nothing, read nothing and write nothing.

**The supervisor's acceptance tests.** `tests/test_program_push_scan.py` fixes the interface; read it whole. Each case builds a scratch repository under pytest's `tmp_path` (`Scratch`), with a made-up profile folder (`HOME` and `USERPROFILE` point at it), `USERNAME` and `USER` set, a `names.txt` under the profile folder's `.cursor-bridge`, a remote `origin` whose address names a made-up owner, `origin/main` and `origin/HEAD` set to the base commit, and a global git config (`GIT_CONFIG_GLOBAL`) holding a made-up identity. It runs the program as a child with `sys.executable` from the repository folder and reads stdout and stderr together. The helper `silent(out)` asserts that none of the made-up names or path segments appears in the output, in any letter case. The two static cases read the program's source with `ast`.

**Known failures before your change** (the supervisor's run on this branch; quote your own runs): every case of `tests/test_program_push_scan.py` fails because there is no program (`Scratch.run` first asserts that the program file exists, since Python itself exits 2 on a missing script); in `tests/test_dump_cli.py` the `push-scan.py` case of `test_cfgb3b_argparse_entry_matches_its_parser` and `test_r055_d002_the_programs_dump_cli_loads_equal_the_diagrams_edges` fail for the same reason (`test_cfgb3b_committed_reference_is_current` passes now and fails once the program exists, until you regenerate the reference); in `tests/test_allowlist.py`, `test_r087_push_scan_rule_in_allow` fails on the missing entry. All must pass after your change.

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions, line 131). `.cursor/rules/secure-coding.mdc` is in force for you. Outside input, each crossing a boundary into the program: the commits' contents (D-004 marks them `UNTRUSTED`), the names file, the environment variables, git's configuration values, and the `<base>` argument. The program writes nothing anywhere: no file, no git ref, no network. Its only output is its lines on the terminal.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: run `push-scan.py` only through the tests, on their scratch repositories under `tmp_path`. Never run it on this repository: it would read the owner's real account names from this computer. Never install anything and never copy anything under `~/.claude`. `python tools/dump-cli.py` imports the module (Done), which is why importing it must do nothing.

**Host.** Windows 11, with Python as on the owner's interpreter. Git as installed. This session has no `claude` on PATH (`claude --version`: command not found), so no Claude Code version is tested on.

## Diagrams
`docs/diagrams/D-002-components.md` (the component diagram) draws the program and its one edge to the library, and the generator's load of it (lines 104, 158, 174, quoted):

```mermaid
        push_scan["push-scan.py"]
    push_scan --> bridge_env
    dump_cli -.-> push_scan
```

`push-scan.py` imports `bridge_env` and no other bridge program. `tests/test_dump_cli.py` checks that `dump-cli.py` loads exactly the programs the `dump_cli` edges name, so the program must be one `dump-cli.py` loads (a `__main__` block and a top-level `build_parser`).

`docs/diagrams/D-004-context-dfd.md` (the context data-flow diagram) draws its flows (lines 204-209, quoted):

```mermaid
p_supervisor -->|"before every push: the range"| p_push_scan
ds_checkout -->|"UNTRUSTED: commits of base..HEAD: messages, author and committer lines, added lines, added file names"| p_push_scan
ds_names_file -->|"the owner's further account names"| p_push_scan
ext_user_env -->|"USERNAME, the profile folder's name"| p_push_scan
ext_owner_profile -->|"git config user.name, the local part of user.email"| p_push_scan
p_push_scan -->|"hits to the terminal only: commit, place, line number, never the matched text; nothing leaves the computer (R-087)"| p_supervisor
```

No other flow: nothing leaves the computer, nothing is written. If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
1. **R1. The command.** `python push-scan.py [<base>]`, run from inside a repository. The parser takes one optional positional argument, the base, and no option besides argparse's own `-h`. A names option or any other word is a usage error (exit 2, argparse's). The parser's description and help name no path and no name.
2. **R2. The base.**
   - A base that begins with `-` (reachable as `push-scan.py -- -x`) is refused with exit 2 before any git command reads it.
   - With no base, the base is the remote-tracking branch `refs/remotes/origin/HEAD` points to (for example `origin/main`). Where `origin/HEAD` is not set, exit 2.
   - A base that is not a commit in the repository exits 2. A base given by its hash reads the same range as the ref.
   - The base reaches git only as a revision, never as an option.
3. **R3. The range.** Every commit of `<base>..HEAD` is read. `<n>` in the OK line is their number (0 for an empty range, which is exit 0). The base commit itself is outside the range.
4. **R4. What is read, for each commit.** The whole message; the author line and the committer line (each its name and its address); each added or renamed file's new name; each added line. For a merge commit, the files and lines are those git shows for it by default (`git show` of a merge shows the combined form, the lines the merge itself introduces).
5. **R5. A path of this computer** (kind `path`). A place holds a path where it contains one of these:
   - a drive letter (one ASCII letter, not preceded by a letter or a digit), then `:`, then one or more `/` or `\`, then a segment;
   - `/Users/` followed by a segment;
   - `/home/` followed by a segment;
   - the segment `AppData`, with a `/` or `\` directly before it or directly after it.

   A segment begins with a letter (any script), a digit, `_`, `.` or `-`. A segment that begins with `<` (a placeholder such as `<name>`) passes. So `https://` is no drive path (the letter before `:` follows a letter), and a backticked `/Users/` with no segment after it is no path.
6. **R6. The owner's names** (kind `name`).
   - The list, in this order: the profile folder's name (the last part of `os.path.expanduser("~")`); `USERNAME`, or `USER` where `USERNAME` is unset or empty; each non-blank line of `~/.cursor-bridge/names.txt`, stripped of surrounding whitespace, where that file exists. A source that is absent takes no place in the list. Names that are equal ignoring letter case count once, the first kept.
   - Never from the command line, never printed, never written anywhere.
   - A name shorter than four characters is skipped, with the note N1 giving its 1-based position in the list.
   - A name equal, ignoring letter case, to the owner segment of `origin`'s address (the part before the repository name, in the https form `https://<host>/<owner>/<repo>` and in the scp-like form `git@<host>:<owner>/<repo>`), to `git config user.name`, or to the local part of `git config user.email`, is dropped, and N2 counts it. An unset value drops nothing.
   - A name matches as literal text (never as a pattern), in any letter case, as a whole word: neither the character before it nor the one after it is a letter or a digit. A name inside a longer word is no hit.
   - Where `names.txt` exists and cannot be read as UTF-8 text, exit 2 (never a scan with fewer names).
7. **R7. The configured identity's lines.** An author line, or a committer line, whose name equals `git config user.name` and whose address equals `git config user.email` (the address ignoring letter case) is no finding: it is not scanned. Every other author and committer line is scanned for both kinds, its name and its address. No other line is ever exempted.
8. **R8. The places.** Exactly these words:
   - `message`;
   - `author`;
   - `committer`;
   - `file #<k>`: the file's own (new) name, `<k>` its 1-based position in the commit's list of files, which is the order of the lines `git show --name-status -M --format= <hash>` prints, so the supervisor can find it;
   - `line <path>:<n>`: an added line, `<path>` the file's new path as git prints it in that list, `<n>` the line's number in the new file;
   - `line #<k>:<n>`: the same, where that file's own path holds a hit of either kind; the path is then never printed.

   Renames are detected (`-M`). A path holding characters outside ASCII is read as its real characters (git's quoting of unusual names undone) and printed without the program failing.
9. **R9. The lines.** Each line is printed whole, on stdout, and flushed. Never a matched text, a name, an added line, a message, an author or committer value, or a path that holds a hit.
   - A hit: `push-scan: HIT <short hash> <place> <kind>`. `<short hash>` is git's `%h` for the commit; `<kind>` is `path` or `name`. One line per place and kind: a message holding a path and a name gives two lines; a line holding two names gives one.
   - Clean: `push-scan: OK - <n> commit(s)`, exit 0.
   - Any hit: after the hit lines, `push-scan: FOUND - <h> hit(s) in <c> of <n> commit(s)`, exit 1.
   - N1: `push-scan: note - name #<k> is shorter than four characters and is skipped` (the test reads `shorter than four`).
   - N2, where at least one name was dropped: `push-scan: note - <m> name(s) dropped as public with the repository`.
   - Exit 2: `push-scan: CANNOT SCAN - <reason>`, `<reason>` one of `not inside a git repository`, `the base must not begin with "-"`, `origin/HEAD is not set; name the base, e.g. origin/main`, `the base is not a commit here`, `the names file cannot be read`, `git cannot be started`, `git <subcommand> failed (exit <code>)`, `git <subcommand> took longer than <GIT_TIMEOUT>s`. Git's own error text, the base's words and any path are never printed (git's messages can hold a path of this computer).
   - The OK line never appears with exit 1 or 2.

   The words of FOUND, N1's sentence after `shorter than four`, N2 and CANNOT SCAN are the supervisor's choice (no test reads them beyond the quoted parts); keep them as written.
10. **R10. Git, read only and bounded.** Only read-only git commands. Each is `subprocess.run` with `timeout=bridge_env.GIT_TIMEOUT` and `creationflags=bridge_env.NO_WINDOW`, never `Popen`, never through a shell, its output decoded so that bytes that are not UTF-8 do not stop the scan. A timeout, a non-zero exit where a value was needed, or git missing is exit 2. No external diff driver or text conversion runs (`--no-ext-diff`, `--no-textconv`), no colour, no pager. The repository's own config is read by git as usual; nothing is written to it.
11. **R11. The source scans clean.** The program's own source holds no literal the scan would read as a path (R5), nor any literal of those shapes at all: a drive letter with a colon and a slash or backslash, `/Users/`, `/home/`, `AppData`. Build each such pattern from parts (as the acceptance tests build their paths), and describe the patterns in words in the docstring and help. A URL literal (`https:` and the slashes after it) is such a shape too. The source is ASCII only. Done's grep and ASCII check verify this, since you do not commit and the program cannot read your working tree's changes as commits.
12. **R12. The allow entry and the generated files.** The entry in `settings.bridge.json` exactly as the Scope's limits say. Regenerate the command reference with `python tools/dump-cli.py`; `python tools/dump-cli.py --check` then exits 0. Regenerate MANIFEST with `python tools/make-manifest.py` and restore VERSION.

## Acceptance criteria
- [ ] The Done section's first pytest command passes whole: `tests/test_program_push_scan.py`, `tests/test_dump_cli.py` and `tests/test_allowlist.py` give no failure.
- [ ] The exits are 0 clean with the OK line, 1 on any hit, 2 for each case of R2, R6 and R10, never a pass where git, the base or the names file cannot be read (R1-R3, R9, R10).
- [ ] Each place of R8 is read and named as R8 says, both kinds in each (R4-R8).
- [ ] No output line holds a matched text, a name, a line, or a path that holds a hit (R9); the tests' `silent` checks pass.
- [ ] The configured identity's names are dropped and its lines are no finding, and nothing else is exempted (R6, R7; the owner's decision of 2026-11-18).
- [ ] `push-scan.py` imports `bridge_env` plainly and no other bridge program; `build_parser` stands at top level; every subprocess call is `subprocess.run` with `timeout=` and `creationflags=bridge_env.NO_WINDOW` (D-002, D-004, R10).
- [ ] Done's grep over `bridge/cursor-bridge/push-scan.py` prints nothing, and its ASCII check exits 0 (R11).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] `settings.bridge.json` gains exactly the one allow line and stays valid JSON.
- [ ] R-087 (the parts this brief serves) is fully met: no stand-in, placeholder or "later" text in the program. The tests naming R-087 are the supervisor's.
- [ ] No new dependency (standard library only), configuration key or environment variable beyond those R6 names. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit any test file, `docs/diagrams/D-002-components.md`, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall: one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (the program, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- **Windowless launches.** Every process the program starts is created with `creationflags=bridge_env.NO_WINDOW`. Capturing output does not prevent the window.
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section names, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- **Never run `push-scan.py` on this repository** or on any folder but the tests' scratch repositories (Context, "Development data").
- Never run the product, a migration, a seed or a test against the owner's live data. Never install anything.
- The owner's value (Context, the decision of 2026-11-18, pinned by the two `test_r087_owner_2026_11_18_` tests) is fixed: do not change it or those tests; report it if the work seems to need a change (rule 52).
- Follow existing conventions of `bridge/cursor-bridge/` programs: a module docstring, ASCII program text and ASCII output apart from path names, results returned as values, `main()` returning the exit code through `sys.exit(main())` in the `__main__` block.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. The program itself runs only read-only git commands (R10).
- Numbers from git's output (a hunk header's line numbers, a count) are parsed with `int`, never by slicing a string by position; a line number is a whole number of at least 1, a count at least 0.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the scan after your run, and every mutant must fail a test. Before you finish, apply each of these to `push-scan.py` by hand, one at a time, run `python -m pytest -p no:cacheprovider -q tests/test_program_push_scan.py` from the Workspace root, and revert. List each in the report by its label and text, with the test id that caught it, or `not caught`:
  - M1 a place skipped (the committer line not read);
  - M2 a place skipped (a renamed file's new name not read);
  - M3 the committer line exempted for any identity;
  - M4 the owner segment of the remote kept as a name;
  - M5 the matched text printed in the hit line;
  - M6 a placeholder segment flagged;
  - M7 a name matched inside a longer word;
  - M8 a name shorter than four characters searched;
  - M9 the line number counted in the old file;
  - M10 a file whose own path holds a hit placed by its path in its line hits;
  - M11 a base beginning with `-` accepted;
  - M12 the configured identity's names not dropped;
  - M13 the configured identity's author and committer lines not exempted.

  You cannot add a test (no test file is in your Scope). A mutant no test catches is reported as `not caught`, with one line on the case that would catch it; the supervisor adds it. M12 and M13 are expected to be caught by `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped`.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `bridge_env.NO_WINDOW` and `bridge_env.GIT_TIMEOUT`, the standard library (`argparse`, `subprocess`, `re`, `os`), git's own output formats, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-067-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for R1-R12, one line each on what meets it, naming the functions and their lines as the file stands after your change;
- the mutation self-check list, M1-M13, each with the test id that caught it (or `not caught` and the case that would);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a git behaviour you expected, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. Examples:
- that `git show` of a merge commit in the range lists in `--name-status` exactly the files whose added lines the scan read for it;
- that `os.path.expanduser("~")` on Windows reads `USERPROFILE` before `HOME`, so the profile folder's name is the one the owner's account has.

One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py`
3. `python tools/dump-cli.py --check` (expect exit 0)
4. `python tools/make-manifest.py`
5. `git restore bridge/cursor-bridge/VERSION`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
10. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py` (expect no output and exit 1: the source holds none of the shapes R11 names. Quote the empty output and the exit code.)
11. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 12, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
