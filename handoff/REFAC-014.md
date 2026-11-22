---
record: brief
header: 1
id: REFAC-014
round: 1
satisfies: [R-088, R-089, R-097]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/in-flight.py", "bridge/cursor-bridge/pace-report.py", "bridge/cursor-bridge/evaluate-reports.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-014-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-014: the reviewer kinds of a PASS line and the read-only git environment, each one copy in bridge_env

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries the third and fourth candidates of stage P3's refactoring pass, in two named parts. Each part moves a copy that two programs hold into `bridge/cursor-bridge/bridge_env.py`, which both programs already import, and deletes both copies. The manifest is regenerated after it. Behaviour stays exactly the same: every PASS line `in-flight.py` writes and every refusal it prints, every PASS line `pace-report.py` reads or skips, every line pace-report prints (the per-week passes lines included, kinds in the same order), every exit code, and the environment every git command of `pace-report.py` and of `evaluate-reports.py`'s origin read is given. Line numbers below are as the files stand at `c530abd` (TASK-078, the base of branch `refactor/P3`). REFAC-012 (evaluate-reports.py's `scan_project`) and REFAC-013 (`bridge_env.round_cause_word`, bridge-run.py, review-guard.py) are committed on this branch before your run: they touch neither in-flight.py nor pace-report.py, but they may have moved lines in `bridge_env.py` and `evaluate-reports.py`, so the function and constant names are the anchors, and a line number in those two files that differs from the one given here is not a reason to stop.

**Part 1: the reviewer kinds of a PASS line.**

The two copies, the same seven strings in the same order (read character by character at `c530abd`; each line indented four spaces, each string followed by a comma, the closing `)` at column 0):

- `bridge/cursor-bridge/in-flight.py` lines 27-35, `REVIEWERS = (` then `"review-a"`, `"review-b"`, `"security-auditor"`, `"design-auditor"`, `"plan-critic"`, `"design-critic-b"`, `"supervisor"`, then `)`. Its one use is `_pass_text(args)`, line 257: `    if reviewer not in REVIEWERS:` followed by `        return None, "the reviewer is outside the list"`. The module docstring and `build_parser` (the `--pass` help is `"record a review pass of NAME by REVIEWER"`) do not list the kinds, and no message is built from the tuple.
- `bridge/cursor-bridge/pace-report.py` lines 103-111, `_REVIEWERS = (` with the same seven lines and `)`. Its uses: `_parse_pass_line(line)`, line 617, `    if m.group(4) not in _REVIEWERS:` (a kind outside the list makes the line no pass line), and `_format_pass_lines(by_week, weeks)`, line 739, `        parts = ["%s %d" % (kind, counts[kind]) for kind in _REVIEWERS if counts.get(kind)]` (the order of the kinds on each passes line).

The change: `bridge_env.py` gains a module-level tuple `REVIEWERS` holding the same seven strings in the same order, written in the same multi-line form, placed directly after the `ROUND_CAUSES` tuple (whatever REFAC-013 put after `ROUND_CAUSES` stays after `REVIEWERS`). Both copies are deleted. The three uses read `bridge_env.REVIEWERS`. No alias is kept: no test reads `REVIEWERS` from in-flight.py or `_REVIEWERS` from pace-report.py (`tests/test_program_in_flight.py` line 30 defines its own tuple of the seven names and parametrizes over it at line 143; `tests/test_release_t_ceiling.py` line 23 holds an unrelated `REVIEWERS` tuple of agent file names). `diagram-check.py`'s `REVIEWERS` (line 600, a compiled regex of review agents' names) is a different thing and stays exactly as it is.

**Part 2: the read-only git environment.**

The two copies, byte-identical (read at `c530abd`: the same 15 lines, each with CRLF, no tab and no trailing whitespace in either file):

```python
def _git_env():
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_NO_LAZY_FETCH"] = "1"
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
    ):
        env.pop(key, None)
    return env
```

- `bridge/cursor-bridge/evaluate-reports.py` lines 502-516 (TASK-077), called once, in `git_origin_repo(project_root)`, line 533: `            env=_git_env(),`.
- `bridge/cursor-bridge/pace-report.py` lines 199-213, called twice, in `_git(ws, args, diff_output=False, as_bytes=False)`, lines 243 and 254: `                env=_git_env(),`.

`bridge_env.py` has no function that builds this environment today (no `GIT_NO_LAZY_FETCH`, `GIT_OPTIONAL_LOCKS` or `os.environ.copy()` in it; `stripped_env` is a different thing, the agents' secret-stripped environment, and is not to be used or touched). The change: `bridge_env.py` gains a top-level function `git_read_env()`, no parameters, whose body is the copies' body, unchanged line for line (no docstring, no comment, nothing added); `bridge_env.py` already imports `os`. Both `_git_env` definitions are deleted, and the three calls become `env=bridge_env.git_read_env(),`. No alias is kept: no test names `_git_env` (see Requirement 1). Both programs already hold `import bridge_env` (pace-report.py line 98; evaluate-reports.py uses `bridge_env.NO_WINDOW` in `git_origin_repo` itself), so nothing new is imported.

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.12a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as they are R-088 (the live position is written by `in-flight.py`, and `--pass <name> <reviewer>` writes a tagged pass line, refused for a reviewer outside the list; TASK-068), R-089 (the pace report counts every increment and recorded round, and prints a line of recorded review passes per week by reviewer kind; TASK-069) and R-097 (the Sunday evaluation's security step is a program, `evaluate-reports.py security`, reading each project's repository from its Workspace's origin remote; TASK-077).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/in-flight.py
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/evaluate-reports.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-014-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser` and no module docstring)
- every file under `tests/`, `tests/fixtures/` included: no test file or fixture may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.12a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- in bridge_env.py, everything but the added `REVIEWERS` tuple and `git_read_env` function: `ROUND_CAUSES`, REFAC-013's `round_cause_word` and `_CAUSE_SEPS`, `stripped_env`, `NO_WINDOW`, the imports and every other name
- in in-flight.py, every line but the deleted `REVIEWERS` tuple and line 257's name; in pace-report.py, every line but the deleted `_REVIEWERS` tuple and `_git_env` function and the four lines that use them (617, 739, 243, 254); in evaluate-reports.py, every line but the deleted `_git_env` function and line 533 (`scan_project`, REFAC-012's, included)
- `diagram-check.py`'s `REVIEWERS` regex, and every other file under `bridge/`

## Context
**What the code is today** (`c530abd`, plus REFAC-012 and REFAC-013 on this branch). All four source files have CRLF line endings on every line; keep them, and add no trailing whitespace. `bridge_env.ROUND_CAUSES` is a module-level tuple written one string per line (four spaces of indent, a comma after each, the closing `)` at column 0), followed by two blank lines; pace-report.py keeps its own `ROUND_CAUSES = bridge_env.ROUND_CAUSES + ("unstated",)` (line 508), which this change does not touch. Neither in-flight.py nor pace-report.py nor evaluate-reports.py defines `__all__`, and no test or tool lists bridge_env's names.

**How the tests reach this code.** `tests/test_program_in_flight.py` (TASK-068, R-088) runs in-flight's `--pass` with each of the seven kinds and refuses one outside them. `tests/test_program_pace_rounds.py` (TASK-069, R-089) and `tests/test_pace_report.py` read pass lines and check the per-week passes lines and their order. `tests/test_task033_supervisor_r3.py`'s `test_task033r3_every_git_command_runs_without_lazy_fetch` records the `env` of every git process pace-report starts and asserts `GIT_NO_LAZY_FETCH` is `"1"` and `GIT_DIR` is absent, with `GIT_DIR` set in the test's own environment. `tests/test_program_security_step.py` (TASK-077, R-097) drives `evaluate-reports.py security` in process, against a stand-in `gh` answering from recorded replies under `tests/fixtures/`, and reaches `git_origin_repo` through real git in pytest's temporary repositories; `test_r097_git_dir_from_the_environment_does_not_choose_the_origin` sets `GIT_DIR` to a decoy checkout and checks the project's own origin is still read, and `test_r097_the_origin_read_runs_git_with_fsmonitor_off` records the git call. `tests/test_release_t_ceiling.py` is in the command because `git grep` names it (its `REVIEWERS` is unrelated). `tests/test_header_currency.py` reads, by syntax tree, the names the programs under `bridge/cursor-bridge/` define and use; it is in the command as the guard of those names. The tests make no network call. Some cases may be skipped on Windows; the skip count must be the same before and after.

**The expected count.** The supervisor's baseline run of the pytest command below at `c530abd`, with this brief untracked, ended "341 passed, 1 skipped". REFAC-012 and REFAC-013 change no test, so the count stands after them. Your before-edit run is the baseline, and the after-edit run must match it (the same count passed, none failed, the same count skipped).

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for the four source files; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.12a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.12a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.12a`. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** Part 1 is an input check: the reviewer word of `in-flight.py --pass` comes from the command line, and the reviewer kind of a pass line comes from the in-flight log, a file the agents' user can write; both are refused unless on the list. Part 2 is a confinement: the environment strips git's location redirections (`GIT_DIR` and the six others) so that a variable inherited from the caller cannot point git at another repository, and sets `GIT_NO_LAZY_FETCH=1` so that a read in a partial clone cannot fetch (and so run a project's `core.sshCommand`) and `GIT_OPTIONAL_LOCKS=0` so that a read takes no lock. The trust boundaries are the command line, the in-flight log and the caller's environment. `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). This change moves no boundary: the same seven kinds are accepted and every other word refused, and every git command gets exactly the environment it gets today, built at the time of the call from the process's environment of that moment.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders, the repositories they create there and the recorded replies. Never run in-flight.py, pace-report.py, evaluate-reports.py or `bridge-install.py` yourself, against this repository or any other, never run `gh`, and never call GitHub.

## Diagrams
`docs/diagrams/D-002-components.md`: the elements `in_flight`, `pace_report`, `evaluate_reports` and `bridge_env`, whose edges already exist:

```mermaid
    pace_report --> bridge_env
    evaluate_reports --> bridge_env
    in_flight --> bridge_env
```

The change adds no import and no edge (each program already imports `bridge_env`), so the diagram does not change. `docs/diagrams/D-004-context-dfd.md` draws no flow this change adds or removes: the git commands, their repositories and what they read are the same. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run:
   - `git grep -n -w -e REVIEWERS -e _REVIEWERS -- bridge/cursor-bridge/in-flight.py bridge/cursor-bridge/pace-report.py`. Expected: five lines, `in-flight.py:27:REVIEWERS = (`, `in-flight.py:257:` (`_pass_text`), `pace-report.py:103:_REVIEWERS = (`, `pace-report.py:617:` (`_parse_pass_line`) and `pace-report.py:739:` (`_format_pass_lines`).
   - `git grep -n -A 14 -e "^def _git_env" -- bridge`. Expected: the two 15-line blocks quoted in Part 2, one in evaluate-reports.py and one in pace-report.py at line 199; compare them line by line and state in the report that they are identical apart from the path and line prefix.
   - `git grep -n -w -e _git_env -- bridge`. Expected: five lines, two in evaluate-reports.py (the def and the call in `git_origin_repo`) and three in pace-report.py (199, 243, 254).
   - `git grep -n -w -e _git_env -e REVIEWERS -e _REVIEWERS -e git_read_env -- tests`. Expected: four lines, `tests/test_program_in_flight.py:30:` and `:143:`, `tests/test_release_t_ceiling.py:23:` and `:90:`; none of them reads a name from in-flight.py, pace-report.py or evaluate-reports.py.
   - `git grep -n -e "^REVIEWERS = " -e "def git_read_env" -e GIT_NO_LAZY_FETCH -- bridge/cursor-bridge/bridge_env.py`. Expected: nothing.
   - `git grep -n -F -e design-critic-b -- bridge`. Expected: three lines, `in-flight.py:33:`, `pace-report.py:61:` (the module docstring's list of kinds) and `pace-report.py:109:`.
   If a check does not hold (another hit, a missing hit, a body that differs, or a line number other than these in in-flight.py, pace-report.py or the tests), stop, change nothing, and report it.
2. `bridge_env.REVIEWERS` holds the seven strings in the order above, as a multi-line tuple directly after `ROUND_CAUSES`; in-flight.py's `REVIEWERS` and pace-report.py's `_REVIEWERS` are gone, and `_pass_text`, `_parse_pass_line` and `_format_pass_lines` read `bridge_env.REVIEWERS`; nothing else in those functions changes.
3. `bridge_env.git_read_env()` is a top-level function with no parameters and the copies' body line for line; both `_git_env` definitions are gone, and the three calls read `env=bridge_env.git_read_env(),` with their indentation unchanged.
4. No other line changes in the four source files. They keep their CRLF line endings and gain no trailing whitespace. No comment, docstring or alias is added; nothing is imported anew.
5. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: the same PASS lines written and the same refusals (`the reviewer is outside the list` among them) from in-flight.py, the same pass lines read or skipped and the same per-week passes lines, kinds in the same order, from pace-report.py, the same exit codes, and the same environment (built from the caller's environment at the call, `GIT_OPTIONAL_LOCKS=0`, `GIT_NO_LAZY_FETCH=1`, the seven `GIT_*` redirections absent) for every git command of pace-report.py's `_git` and evaluate-reports.py's `git_origin_repo`.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] One copy each: `git grep -n -w -e _git_env -e _REVIEWERS -- bridge` prints nothing; `git grep -n -e "def git_read_env" -- bridge` prints one line, in `bridge/cursor-bridge/bridge_env.py`; `git grep -n -w -e git_read_env -- bridge` prints four lines (the def in bridge_env.py, one call in evaluate-reports.py, two in pace-report.py); `git grep -n -F -e GIT_NO_LAZY_FETCH -- bridge` prints one line, in bridge_env.py; `git grep -n -e "^REVIEWERS = " -- bridge` prints two lines, `bridge/cursor-bridge/bridge_env.py` and `bridge/cursor-bridge/diagram-check.py:600:` (the unrelated regex); `git grep -n -F -e design-critic-b -- bridge` prints two lines, one in bridge_env.py and `bridge/cursor-bridge/pace-report.py:61:` (the docstring), where it printed three.
- [ ] No public signature changed outside the two added names; in-flight.py, pace-report.py and evaluate-reports.py import nothing new.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.12a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.12a`).
- [ ] `git diff --stat` shows only the four source files, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment's tests replay the **recorded real responses** in `tests/fixtures/` through the tests' own stand-in `gh`; do not invent a mock of GitHub's responses, hosts, fields, or next-step URLs, and do not add or change a fixture.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch and leaves each git call's `creationflags` as it is.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources, pytest's temporary folders and the recorded replies only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_program_in_flight.py tests/test_program_pace_rounds.py tests/test_pace_report.py tests/test_program_security_step.py tests/test_task033_supervisor_r3.py tests/test_release_t_ceiling.py tests/test_header_currency.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; `git diff --numstat -- bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/in-flight.py bridge/cursor-bridge/pace-report.py bridge/cursor-bridge/evaluate-reports.py`; the six `git grep` commands of the third acceptance criterion.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example the git options each program passes with `-c`, which differ between `_git` and `git_origin_repo`, pace-report's own `ROUND_CAUSES`, or the docstring's list of kinds); report them in your summary instead. Do not introduce an abstraction beyond the two names: no helper, no parameter, no alias, no comment, nothing new outside the four source files except the regenerated manifest.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-014-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the Requirement 1 commands with their output as the evidence, and your line-by-line comparison of the two `_git_env` bodies;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, the two `git diff --numstat` commands and the third acceptance criterion's six `git grep` commands, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
