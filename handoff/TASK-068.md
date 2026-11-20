---
record: brief
header: 1
id: "TASK-068"
round: 1
satisfies: [R-088]
scope: ["bridge/cursor-bridge/in-flight.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/pace-report.py", "bridge/cursor-bridge/loop-guard.py", "bridge/cursor-bridge/settings.bridge.json", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_loop_guard.py", "tests/test_bridge_run.py", "tests/test_pace_report.py", "tests/test_dump_cli.py", "tests/test_allowlist.py", "docs/BUILDER_NOTES.md", "handoff/TASK-068-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-068: the in-flight program (R-088)

Round cause: first round (no earlier round)

## Objective
Between merges the supervisor keeps its live position (what is in flight, since when, a pause) in the untracked file `run/supervisor/in-flight.md` of the Workspace. Today it writes that file by hand, with a time it types itself. This increment makes the writing a program, `bridge/cursor-bridge/in-flight.py`, installed as `python ~/.claude/cursor-bridge/in-flight.py`. It appends one clock-stamped line to the log of the Workspace the current folder belongs to: a text given as one argument, or the text of a file under `run/supervisor/` (`--file`), or, with `--pass <name> <reviewer>` and the optional `--round <n>` and `--cause <cause>`, a tagged line recording a review pass, which the pace report reads later (TASK-069). It prints what it wrote and refuses, writing nothing, outside a Workspace, with no text, with two sources, or with a word outside its lists. The round causes, which the launcher and the pace report each hold a copy of today, move to one list in `bridge_env.py` that both read and this program reads. The loop guard's refusal, which still sends the supervisor to the status file's `In flight:` line, names the in-flight log and this program instead. The program gets its allow entry, and the generated files (the command reference and MANIFEST) are regenerated. The texts that still send the live position to the status file (rule 54, calibration's step 0, the parallel builders' paragraph) and KP-041's retirement are TASK-078's, not yours.

Satisfies: R-088 - The live position is written by a program (C15, J3): `in-flight.py` appends one line, `<UTC time from the clock> <text>`, to the Workspace's `run/supervisor/in-flight.md`, the text from a file under `run/supervisor/` (`--file`) or from one argument, and with `--pass <name> <reviewer>` and the optional `--round <n>` and `--cause <cause>` a tagged line for a review pass; it refuses outside a Workspace or with no text and prints what it wrote; the loop guard's refusal and the three texts that sent the live position to the status file's `In flight:` line (rule 54, calibration's step 0, the parallel builders' paragraph) name the in-flight log and this program, and KP-041 is retired. (Its row in `docs/REQUIREMENTS.md`, line 114. This brief serves the program, the one list of causes and the loop guard's refusal. The three texts and KP-041 are TASK-078's.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/in-flight.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/loop-guard.py
- bridge/cursor-bridge/settings.bridge.json
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_loop_guard.py
- tests/test_bridge_run.py
- tests/test_pace_report.py
- tests/test_dump_cli.py
- tests/test_allowlist.py
- docs/BUILDER_NOTES.md
- handoff/TASK-068-r1-report.md

Limits on these paths:
- `bridge/cursor-bridge/in-flight.py` is new. You write all of it.
- `bridge/cursor-bridge/bridge_env.py`: add exactly two things, the constant `ROUND_CAUSES` (R9) and one function that finds the Workspace (R2). Change nothing else in the file.
- `bridge/cursor-bridge/bridge-run.py`: line 990 (`ROUND_CAUSES = ("defect", ...)`) becomes a reading of `bridge_env.ROUND_CAUSES`; the module keeps a module-level name `ROUND_CAUSES` equal to it. Nothing else changes; `round_cause` (lines 994-1007) is untouched.
- `bridge/cursor-bridge/pace-report.py`: line 431 becomes `bridge_env.ROUND_CAUSES` with `"unstated"` appended, kept under the module-level name `ROUND_CAUSES`. Nothing else changes.
- `bridge/cursor-bridge/loop-guard.py`: only the text of the refusal at line 638 (R10). Its decision, every other message and the docstring stay as they are.
- `bridge/cursor-bridge/settings.bridge.json`: add exactly one line to the `allow` list, the entry `"Bash(python ~/.claude/cursor-bridge/in-flight.py:*)",` placed directly after the line `"Bash(python ~/.claude/cursor-bridge/push-scan.py:*)",` (line 73). Change nothing else in the file. It must stay valid JSON.
- `tests/test_dump_cli.py`: add `"in-flight.py"` to the `ARGPARSE` tuple (lines 33-34) and change nothing else. Without it, `test_cfgb3b_docstring_entries_hold_the_whole_docstring` expects a docstring entry for the new program and fails.
- `tests/test_allowlist.py`: add one test, `test_r088_in_flight_rule_in_allow`, beside `test_r087_push_scan_rule_in_allow` (line 257) and in its form (R11). Change nothing else.
- `tests/test_loop_guard.py`: add one test naming R-088 that pins the refusal (R10). Change nothing else.
- `tests/test_bridge_run.py` and `tests/test_pace_report.py`: the plan lists them so that you run them. Change nothing in either: they must pass unedited (the plan's Scope notes).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done). Afterwards `python tools/dump-cli.py --check` must exit 0. Never edit either by hand.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`. `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Read-only for you (already done and committed by the supervisor on this branch, commit 48bcfa6; the plan's Scope names them, this brief does not):
- `docs/diagrams/D-002-components.md` (the element `in_flight`, the edges `in_flight --> bridge_env` and `dump_cli -.-> in_flight`, the count fifteen);
- `tests/test_program_in_flight.py` (the acceptance tests).

Read and run them. Edit neither.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, the diagrams included.
- `tests/test_program_in_flight.py` and every test file the Scope does not name. You add no test file. If a case of the acceptance tests seems wrong, report it by its test id.
- Every other program under `bridge/cursor-bridge/`, `review-guard.py` included (the guard reads the list from TASK-069 on).
- The texts under `bridge/commands/`, `bridge/agents/` and `bridge/cursor-bridge/workflow/` (TASK-078), and `bridge/cursor-bridge/CHANGELOG.md`.
- The eighth cause, `base update` (TASK-069). The list stays the seven.
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them, Done, and edit neither).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this increment:** `docs/DESIGN.md`, "Change: the program release", "Measurement", the bullet *C15* and *J3* (line 351), and in the next bullet (line 352) the sentence beginning "The round causes stand once, in `bridge_env.py`". The plan entry is `docs/BUILD_PLAN.md`, `### TASK-068` (line 1870), its Scope notes and Done when.

**The reality check (the supervisor's, on this branch's checkpoint).**
- `bridge/cursor-bridge/in-flight.py` does not exist yet. `bridge_env.py` has no `ROUND_CAUSES` and no function that finds a Workspace from a folder.
- `bridge/cursor-bridge/bridge-run.py` line 990 and `bridge/cursor-bridge/pace-report.py` line 431 each hold their own tuple of the causes (the report's with `"unstated"` appended). Both already import `bridge_env` at module level (`bridge-run.py` line 115, `pace-report.py` line 48).
- `tests/test_release_s_launcher.py` (outside Scope) line 485 asserts `program("pace-report").ROUND_CAUSES == program("bridge-run").ROUND_CAUSES + ("unstated",)`: both modules keep the name `ROUND_CAUSES`, both tuples. It must pass unedited.
- `bridge/cursor-bridge/loop-guard.py` line 638 writes the refusal for a background agent with no timer; it tells the supervisor to "write it on the status file's `In flight:` line". The guard also reads a pause from the log: `paused_in_flight(cwd)` (line 272) finds the Workspace with `workspace_of` (line 258) and reads the log with `field(text, "Paused")` (line 191), whose pattern `^\s*(?:[-*]\s+)?[*_`]*Paused[*_`]*\s*:` (multiline, any letter case) matches only a line that begins with `Paused:` (after spaces, a bullet or emphasis marks). A `Paused:` line behind a time stamp is not read. The test `test_r088_a_paused_line_in_the_file_stays_a_line_the_loop_guard_reads` loads the guard and calls `paused_in_flight` on the scratch Workspace.
- `tests/test_loop_guard.py` line 276-280 drives `lg.main()` into this refusal (stdin JSON with an agent and no timer) and asserts `The computer's clock reads`, `KP-043` and `wake-timer` in stderr: the pattern for your pin.
- `tools/dump-cli.py` loads every program of `bridge/cursor-bridge/` that has a `__main__` block and a top-level `build_parser`, imports it and calls `build_parser()`: importing `in-flight.py` must run nothing, read nothing and write nothing. `test_r055_d002_the_programs_dump_cli_loads_equal_the_diagrams_edges` compares those loads with D-002's `dump_cli` edges and fails until the program exists.
- The program follows `bridge/cursor-bridge/push-scan.py`: a shebang, a module docstring, `HERE = os.path.dirname(os.path.abspath(__file__))`, `sys.path.insert(0, HERE)`, `import bridge_env` (lines 28-30, a plain import); `def build_parser():` at module top level with no argument, returning the parser, and `def main():` (no argument) calling it and building no parser of its own (lines 1240-1258); `if __name__ == "__main__": sys.exit(main())` (lines 1261-1262).

**The supervisor's acceptance tests.** `tests/test_program_in_flight.py` fixes the interface; read it whole. Each case builds a scratch Workspace under pytest's `tmp_path` (`<tmp>/proj/Workspace` holding `docs/PROJECT_STATUS.md`), runs the program as a child with `sys.executable` from a folder inside it, and reads the log `run/supervisor/in-flight.md`. The stamp form is `STAMP = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z"`; the tests read the stamp from a line's first 17 characters and the text from character 18 on. The reviewer kinds are `REVIEWERS` and the causes `SEVEN` (lines 29-30). The three static cases read the sources of `bridge-run.py`, `pace-report.py` and `in-flight.py`: each must contain the text `bridge_env.ROUND_CAUSES`, and none may match the regex `["']builder incomplete["']\s*,\s*["']brief error["']` anywhere (comments and docstrings included). One case reads `loop-guard.py`'s source for `in-flight.py` and `run/supervisor/in-flight.md`, and for the absence of the words "status file's `In flight:` line".

**Known failures before your change** (the supervisor's run on the checkpoint; quote your own runs): `tests/test_program_in_flight.py` 36 failed, 1 skipped; in `tests/test_dump_cli.py`, `test_r055_d002_the_programs_dump_cli_loads_equal_the_diagrams_edges` fails (the edge to `in_flight` has no program). After your change: `tests/test_program_in_flight.py` all pass except `test_r088_a_file_reached_through_a_link_is_refused`, which is skipped on an account that cannot create a symbolic link (this computer's), and every other command of the Done list passes.

**External services.** None. The program calls no service, no network and no git, and starts no process, so no time limit or retry applies to it. This session has no `claude` on PATH (`claude --version`: command not found); nothing in this increment calls it.

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions, line 137). `.cursor/rules/secure-coding.mdc` is in force for you. Outside input, each crossing a boundary into the program: the command-line words (the text, the path, the name, the reviewer, the round, the cause), the content of the `--file` file, and the file system it walks (the folders above the current folder, a link under `run/supervisor/`). The log is read later by the supervisor, the loop guard, the session-start hook and the pace report, so what it writes must not be able to forge a line: no control character reaches it, and only the lines R5 names are written. The program writes one file, the log, and creates its folder; nothing else.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: run `in-flight.py` only through the tests, on their scratch Workspaces under `tmp_path`. Never run it from inside this repository: this Workspace's `run/supervisor/in-flight.md` is the supervisor's live log, and a run from here would append to it. Never install anything and never copy anything under `~/.claude`. `python tools/dump-cli.py` imports the module (Done), which is why importing it must do nothing.

**Host.** Windows 11, with Python as on the owner's interpreter; CI also runs on Linux. On Windows, Python's append mode is the C runtime's move to the end of the file followed by a write, which is not one operation across processes; R6's guarantee must hold on both systems.

## Diagrams
`docs/diagrams/D-002-components.md` (the component diagram) draws the program, its one edge to the library and the generator's load of it (lines 105, 159, 171, quoted):

```mermaid
        in_flight["in-flight.py"]
    in_flight --> bridge_env
    dump_cli -.-> in_flight
```

`in-flight.py` imports `bridge_env` and no other bridge program: it does not load `loop-guard.py` or any sibling by file. `bridge_run --> bridge_env` and `pace_report --> bridge_env` exist already, so the move of the list adds no edge. The program must be one `dump-cli.py` loads (a `__main__` block and a top-level `build_parser`). If the task cannot be done within this diagram, stop and report the conflict instead of deviating.

## Requirements
1. **R1. The command.** `python in-flight.py <text>`, `python in-flight.py --file <path>`, or `python in-flight.py --pass <name> <reviewer> [--round <n>] [--cause <cause>]`, with argparse, a top-level `build_parser()` and `main()` as Context says. Exactly one of the three sources: none, two of them (a text with `--file`, a text or `--file` with `--pass`), or `--round` or `--cause` without `--pass` is refused (R7). The parser's description and help name no path of this computer and no user name.
2. **R2. The Workspace.** The Workspace is the current folder or its nearest parent that holds `docs/PROJECT_STATUS.md` as a file, found by one new function in `bridge_env.py` that takes the start folder as its argument and returns the folder's absolute path or `None`; `in-flight.py` calls it with the current folder. No Workspace: refused (R7), and no `run/` folder is created anywhere. The log is `<Workspace>/run/supervisor/in-flight.md`; its folder and the file are created where absent.
3. **R3. The stamp.** The UTC time from the clock when the program runs, to the minute, written `YYYY-MM-DDTHH:MMZ` (17 characters, for example `2026-11-20T09:05Z`), followed by one space and the text.
4. **R4. The text.**
   - From the argument: the one word as given, its leading and trailing spaces removed.
   - From `--file`: the file's text read as UTF-8 (a leading byte-order mark dropped), split into lines at CR LF, LF or CR, blank lines dropped, the rest joined by one space, leading and trailing spaces removed (so `first part\r\nsecond part\nthird part\n` gives `first part second part third part`). The file holds at most 65,536 bytes; a larger one, one that is not UTF-8, a missing path or a folder is refused (R7).
   - `--file` names a file under that Workspace's `run/supervisor/` by its resolved path: the path, resolved (`..` and links followed), must lie inside the resolved `<Workspace>/run/supervisor/` folder, at any depth, and is not the log itself. A path that reaches the file through a link (the file a symbolic link, or a folder between `run/supervisor/` and the file a symbolic link or a junction) is refused, even when the link stands under `run/supervisor/`. Path comparison follows the platform's case rules (`os.path.normcase`).
   - A text (either source, after the line breaks of a file are made spaces) that is empty, or that holds a character of Unicode category Cc, Cf, Zl or Zp (a tab, an escape, a line break in the argument, a right-to-left override U+202E), is refused (R7).
5. **R5. The lines written.**
   - A text: one line, `<stamp> <text>`.
   - Where a line of the text (a line of the `--file` file, or the argument) begins with `Paused:` in any letter case after leading spaces, that line is written once more, after the stamped line, as a line of its own with no stamp, its leading spaces removed, so that the loop guard's `paused_in_flight` reads it. Several such lines follow in their order. The stamped line still holds the whole text.
   - `--pass <name> <reviewer>`: one line, `<stamp> PASS <name> r<n> <reviewer> <cause>`, where ` r<n>` is left out when `--round` is not given and ` <cause>` is left out when `--cause` is not given (the pace report reads a pass line with no round as round 1 and with no cause as `unstated`, TASK-069).
     - `<name>` matches `bridge_env.GRAMMAR_ID_PATTERN` (`[A-Z][A-Za-z0-9-]*`, bridge_env.py line 428) whole: an increment's ID (`TASK-068`) or a pull request's `PR-<n>` (`PR-7`).
     - `<reviewer>` is exactly one of `review-a`, `review-b`, `security-auditor`, `design-auditor`, `plan-critic`, `design-critic-b`, `supervisor`.
     - `<n>` is a whole number from 1 to 999, parsed with `int` (`zero`, `0`, `-1`, `1.5` are refused).
     - `<cause>` is exactly one of `bridge_env.ROUND_CAUSES`, given as one word (`--cause "no external path"`); the source names `bridge_env.ROUND_CAUSES` and holds no copy of the list. `unstated` is not accepted.
   - Each line ends with LF; the file is written as UTF-8.
6. **R6. One append.** All the lines of one run reach the file in one append, so runs started together never interleave within a line and never lose a line (`test_r088_concurrent_runs_never_interleave_within_a_line`: eight runs, each with a text of about 3,600 characters). Where the existing file is not empty and does not end with a line break, the appended block begins with LF, so the new line is a line of its own. What stands in the file is never rewritten. Any wait for the file is bounded: at most 10 seconds, then refused (R7) with nothing written.
7. **R7. Refusals.** Every refusal exits 2 and writes nothing: no log line, no `run/` or `run/supervisor/` folder created. All checks (R1, R2, R4, R5) run before the first write. Argparse's own usage errors exit 2 as well. A refusal prints one line to stderr, `in-flight: REFUSED - <reason>`, naming the reason and never a traceback; it never prints a path of this computer.
8. **R8. The output.** On success, exit 0 and print every line it wrote, each whole, to stdout, encoded as UTF-8 whatever the console's code page (as `push-scan.py`'s `say` does).
9. **R9. The one list of round causes.** `bridge_env.py` gains `ROUND_CAUSES`, a tuple of exactly the seven causes in this order: `"defect", "security", "fix-induced", "no external path", "records", "builder incomplete", "brief error"`. `bridge-run.py` keeps a module-level `ROUND_CAUSES` that is `bridge_env.ROUND_CAUSES` (its `round_cause` unchanged); `pace-report.py` keeps a module-level `ROUND_CAUSES` that is `bridge_env.ROUND_CAUSES` with `"unstated"` appended (the report's word for none). Neither holds a tuple of the causes of its own; `"unstated"` is not added to bridge_env's list. `in-flight.py` reads `bridge_env.ROUND_CAUSES` for `--cause`.
10. **R10. The loop guard's refusal.** In the refusal at `loop-guard.py` line 638, the words "write it on the status file's `In flight:` line" give way to words that send the supervisor to the in-flight log through the program, naming both `run/supervisor/in-flight.md` and `python ~/.claude/cursor-bridge/in-flight.py`. The refusal's first words stay `Loop guard (Claude-Cursor Bridge, rule 43): you are waiting on a background agent with no timer running to its ceiling:`; the rest of it, its exit code and the guard's decision are unchanged; the output stays ASCII. The source no longer holds "status file's `In flight:` line". In `tests/test_loop_guard.py`, one new test whose name begins `test_r088_` drives `lg.main()` into this refusal as lines 276-280 do and asserts that stderr begins with those first words and holds `run/supervisor/in-flight.md` and `in-flight.py`.
11. **R11. The allow entry and its pin.** The entry in `settings.bridge.json` exactly as the Scope's limits say. `test_r088_in_flight_rule_in_allow` in `tests/test_allowlist.py` asserts the rule `Bash(python ~/.claude/cursor-bridge/in-flight.py:*)` is in `ALLOW` and that `decide(cmd, ALLOW, DENY)[0] == "allow"` for each of `python ~/.claude/cursor-bridge/in-flight.py "TASK-068 builder r1 launched"`, `python ~/.claude/cursor-bridge/in-flight.py --file run/supervisor/line.txt`, `python ~/.claude/cursor-bridge/in-flight.py --pass PR-7 review-a --round 2 --cause records` and `python ~/.claude/cursor-bridge/in-flight.py --pass TASK-068 review-b --round 1 --cause "no external path"`. If `decide` does not allow one of them, stop and report it by the command; do not change the permission rules or the guard.
12. **R12. The generated files.** `tests/test_dump_cli.py`'s `ARGPARSE` gains `"in-flight.py"` (Scope's limits). Regenerate the command reference with `python tools/dump-cli.py`; `python tools/dump-cli.py --check` then exits 0. Regenerate MANIFEST with `python tools/make-manifest.py` and restore VERSION.
13. **R13. The source.** `in-flight.py` is ASCII only, imports only the standard library and `bridge_env`, starts no process and makes no network call.

## Acceptance criteria
- [ ] The Done section's first pytest command passes whole: `tests/test_program_in_flight.py` with only the link case skipped where the account cannot create a symbolic link; `tests/test_dump_cli.py`, `tests/test_allowlist.py` and `tests/test_loop_guard.py` give no failure.
- [ ] The Done section's second pytest command passes whole: `tests/test_bridge_run.py`, `tests/test_pace_report.py` and `tests/test_release_s_launcher.py`, unedited.
- [ ] One appended line per text, `<YYYY-MM-DDTHH:MMZ> <text>`, from the argument or from a file under `run/supervisor/`, a `Paused:` line kept as its own line, the log and its folder created where absent, the lines printed (R3-R5, R8).
- [ ] The pass line `<stamp> PASS <name> r<n> <reviewer> <cause>` with the seven reviewer kinds and the seven causes, each word outside its list refused (R5).
- [ ] Each refusal of R1, R2, R4, R5 and R6 exits 2 and writes nothing, no folder included (R7).
- [ ] Runs started together leave whole lines, none lost, on Windows and Linux (R6).
- [ ] `bridge_env.ROUND_CAUSES` is the seven, read by the launcher, the report and the program, none holding a copy (R9).
- [ ] The loop guard's refusal names `run/supervisor/in-flight.md` and `in-flight.py`, its first words pinned by a `test_r088_` test, its decision unchanged (R10).
- [ ] `in-flight.py` imports `bridge_env` plainly and no other bridge program; `build_parser` stands at top level; importing it does nothing (D-002).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] `settings.bridge.json` gains exactly the one allow line and stays valid JSON; `test_r088_in_flight_rule_in_allow` passes (R11).
- [ ] R-088 (the parts this brief serves) is fully met: no stand-in, placeholder or "later" text in the program. The acceptance tests naming R-088 are the supervisor's; your two new tests name R-088 too.
- [ ] No new dependency (standard library only), configuration key or environment variable. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_in_flight.py`, `docs/diagrams/D-002-components.md`, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall: one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (the program, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- **Never run `in-flight.py` from inside this repository** or on any folder but the tests' scratch Workspaces (Context, "Development data"): it would append to the supervisor's live log.
- **Windowless launches.** The program starts no process. If you find you need one, stop and report it.
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section names, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- Never run the product, a migration, a seed or a test against the owner's live data. Never install anything.
- Follow existing conventions of `bridge/cursor-bridge/` programs: a module docstring holding the usage, ASCII program text, results returned as values, `main()` returning the exit code through `sys.exit(main())` in the `__main__` block.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- Numbers from the command line (`--round`) are parsed with `int`, never by slicing; the round is a whole number from 1 to 999. The file bound is 65,536 bytes; the wait bound is 10 seconds.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the program after your run, and every mutant must fail a test. Before you finish, apply each of these by hand, one at a time, run `python -m pytest -p no:cacheprovider -q tests/test_program_in_flight.py` from the Workspace root (for M12, `tests/test_loop_guard.py`), and revert. List each in the report by its label and text, with the test id that caught it, or `not caught`:
  - M1 the stamp written in local time instead of UTC;
  - M2 the stamp written to the second;
  - M3 the log opened for writing instead of appending;
  - M4 the Workspace taken to be the current folder, with no walk to its parents;
  - M5 a `Paused:` line of the file joined into the stamped line only;
  - M6 a `--file` path accepted without resolving `..`;
  - M7 a `--file` path outside `run/supervisor/` but inside the Workspace accepted;
  - M8 a text holding an escape character accepted;
  - M9 a reviewer outside the list accepted;
  - M10 `--cause` accepted outside `bridge_env.ROUND_CAUSES`;
  - M11 the log's folder created before the checks run;
  - M12 the loop guard's refusal's first words changed.

  You cannot add a test to `tests/test_program_in_flight.py`. A mutant no test catches is reported as `not caught`, with one line on the case that would catch it; the supervisor adds it. The link refusal is skipped on this computer: say in the report that it was not exercised.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `bridge_env.GRAMMAR_ID_PATTERN`, the standard library (`argparse`, `datetime`, `os`, `unicodedata`), and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-068-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for R1-R13, one line each on what meets it, naming the functions and their lines as the files stand after your change (the name of the new `bridge_env` function among them), and one sentence on how R6's one append holds on Windows;
- the mutation self-check list, M1-M12, each with the test id that caught it (or `not caught` and the case that would);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a platform behaviour you expected, an ambiguous requirement you resolved one way, a library behaviour you expected, a value you chose. Examples:
- that the way you append keeps one run's lines whole against another process on Windows and on Linux beyond the eight runs the test starts;
- that a junction under `run/supervisor/` is refused as a link, since the link case is skipped on this account.

One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py`
3. `python tools/dump-cli.py --check` (expect exit 0)
4. `python tools/make-manifest.py`
5. `git restore bridge/cursor-bridge/VERSION`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_in_flight.py tests/test_dump_cli.py tests/test_allowlist.py tests/test_loop_guard.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_pace_report.py tests/test_release_s_launcher.py` (`tests/test_release_s_launcher.py` is outside Scope. A failure there is reported by test id, never fixed in that file.)
8. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `python -c "open('bridge/cursor-bridge/in-flight.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them (`-rs` prints the skip's reason).
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 12, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
