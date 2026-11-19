---
record: brief
header: 1
id: REFAC-010
round: 1
satisfies: [R-081]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-010-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-010: one resolver of a git rev-parse path, and one snapshot read, in the git-config watch

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries the fourth candidate of stage P2's refactoring pass: copies that TASK-062 (the launcher's git-config watch, R-081) left in `bridge/cursor-bridge/bridge-run.py`. Three places turn a `git rev-parse` answer into an absolute path with the same lines, and the watch's `before()` and `after()` have the same body. The three resolutions become one private helper and `after` becomes the same method as `before`; the manifest is regenerated after it. Behaviour stays exactly the same: the same files watched in the same order, the same printed `bridge-run: GIT-CONFIG <path> <word>` lines, the same exit codes, the same exceptions swallowed. Line numbers below are as the file stands at `822212f` (REFAC-009, the head of branch `refactor/P2`), before your edit.

**The sites.**

1. `_git_rev_parse(folder, *args)`, lines 2444-2460: runs `git -C <folder or "."> rev-parse <args>` windowless with `bridge_env.GIT_TIMEOUT`, returns the stripped standard output, or `None` on a nonzero exit, an empty output, an `OSError` or a timeout. **It stays exactly as it is**; it is the helper's source.

2. `_git_dir(folder)`, lines 2463-2469:

```python
def _git_dir(folder):
    raw = _git_rev_parse(folder, "--git-dir")
    if raw is None:
        return None
    if os.path.isabs(raw):
        return os.path.normpath(raw)
    return os.path.normpath(os.path.join(os.path.abspath(folder or "."), raw))
```

Its one caller: line 2547, inside `GitConfigWatch.__init__` (`git_dir = _git_dir(folder)`).

3. `_git_resolved_path(folder, git_path_name)`, lines 2472-2479: the same four lines over `_git_rev_parse(folder, "--git-path", git_path_name)`, with the docstring `"""Absolute path for `git rev-parse --git-path <name>`; relative answers resolve against the worktree top."""`. That docstring is not what the code does: a relative answer is joined against the launch folder (`folder`, or the current folder), not the worktree top (`docs/BUILDER_NOTES.md` line 46 records why: git answers `--git-path` relative to the folder it was run in; `docs/HARDENING.md`, TASK-062's lead (1), records the stale docstring). The docstring goes with the function. Its one caller: line 2560, inside `GitConfigWatch.__init__` (`_git_resolved_path(folder, "hooks")`, the first entry of the hooks tuple).

4. Inside `GitConfigWatch.__init__`, lines 2553-2556:

```python
            top = _git_rev_parse(folder, "--show-toplevel")
            if top:
                if not os.path.isabs(top):
                    top = os.path.normpath(os.path.join(os.path.abspath(folder or "."), top))
```

followed (2557-2558) by `dot_git = os.path.join(top, ".git")` and its `self._files.append(...)`. Note the one difference from sites 2 and 3: an **absolute** `top` is used as git printed it, not passed through `os.path.normpath`.

5. `GitConfigWatch.before(self)` (lines 2594-2600) and `GitConfigWatch.after(self)` (lines 2602-2608): identical bodies, `if not self.active: return None`, then `try: return self._snapshot()` / `except Exception: return None`. Their callers: `main`, lines 2960-2966 (`git_watch.before()`, `git_watch.after()`), and `tests/test_program_git_config.py` lines 356 and 379 (`watch.before()`, `watch.after()`).

**Not a site.** `git_common_dir(folder)` (lines 1162-1180) runs its own `git rev-parse --git-common-dir` with its own error handling and is used by the BOUNDARY code (line 1266) and by `GitConfigWatch.__init__` (line 2539). It stays exactly as it is and does not call the new helper.

**The proposed shape.**

- bridge-run.py gains one private function, `_git_rev_parse_path(folder, *args)`: `raw = _git_rev_parse(folder, *args)`; `None` gives `None`; an absolute `raw` gives `os.path.normpath(raw)`; otherwise `os.path.normpath(os.path.join(os.path.abspath(folder or "."), raw))`. Its docstring says what it does: the absolute path of a `git rev-parse` answer, a relative answer resolved against the launch folder (`folder`, or the current folder), `None` where git gives none. Its placement near `_git_rev_parse` is yours.
- `_git_dir` and `_git_resolved_path` are deleted, with `_git_resolved_path`'s docstring. Line 2547 calls `_git_rev_parse_path(folder, "--git-dir")`; line 2560's first tuple entry is `_git_rev_parse_path(folder, "--git-path", "hooks")`.
- Site 4 becomes `top = _git_rev_parse_path(folder, "--show-toplevel")` followed by the existing `if top:` block without its own `isabs` test and join (the `dot_git` lines unchanged).
- `GitConfigWatch.after` becomes `after = before` in the class body, after `before`'s definition; `after`'s own body is deleted. `watch.after()` and `git_watch.after()` keep working unchanged.

**The one behaviour point to confirm.** Site 4 now passes an absolute `--show-toplevel` answer through `os.path.normpath`, where it did not before. This changes nothing observable: git prints the top as a resolved absolute path (on Windows with forward slashes, with no `.` or `..` part and no trailing separator), so `normpath` changes only its separators. The `.git` path built from it names the same file for `_git_file_state` (`os.path.lexists`, `os.lstat`, `bridge_env.is_link`, `open`). Its display key comes from `_git_display_path(abs_path, parent)` (lines 2482-2489), which either returns `os.path.relpath(abs_path, parent)` with backslashes turned to `/` (`relpath` makes both arguments absolute and normalized first) or, on a `ValueError` or a result starting with `..`, returns `os.path.normpath(abs_path)` with backslashes turned to `/`; so the printed `GIT-CONFIG <path>` text is the same string. `if top:` is also unchanged: `_git_rev_parse` never returns an empty string, and `normpath` of a non-empty string is non-empty. Confirm this by reading `_git_display_path` and `_git_file_state`, and state it in the report. If you find a case where the printed path, the file read, or the order or dedupe of `self._files` and `self._hooks_dirs` differs, stop, change nothing, and report it (an objection).

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.12a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as it is R-081 (the launcher detects a change of git's configuration made by a test or driver run (J17) and prints one `bridge-run: GIT-CONFIG <path> <word>` line per difference on standard error, built by TASK-062).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-010-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/HARDENING.md` included (its lead about the stale docstring is the supervisor's to close); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser` and no module docstring)
- every file under `tests/`: no test file may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.12a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- in bridge-run.py: `git_common_dir` and every caller of it; `boundary_listing`, `boundary_changes` and the rest of the BOUNDARY code; `_git_rev_parse` itself; `_git_display_path`, `_git_hooks_dir_listable`, `_git_file_state`, `GitConfigWatch._snapshot`, the rest of `GitConfigWatch.__init__` beyond the three call lines and site 4's two lines named in the Objective, `git_config_changes`, and `main`'s use of the watch (lines 2960-2971); the CI watch's wait (`_watch_bits`, `_watch_name`, `watch_loop` and the rest: a separate brief, REFAC-011); the module docstring, `build_parser`, and every other function
- every other file under `bridge/`, `bridge_env.py` and `review-guard.py` among them

## Context
**What the code is today** (`822212f`). bridge-run.py has CRLF line endings on every line; keep them, and add no trailing whitespace. It imports `os`, `subprocess` and `bridge_env` already; nothing new is imported. `_git_rev_parse` runs git with `creationflags=NO_WINDOW` (line 117) and `timeout=bridge_env.GIT_TIMEOUT` (30 seconds, `bridge_env.py` line 416); the new helper adds no call of its own and no retry, and those values are not to be touched. `GitConfigWatch.__init__` (lines 2533-2570) builds `self._files` in this order: the common folder's `config`, its `info/attributes`, then (where `--git-dir` answers) the git folder's `config.worktree` and `commondir`, then (where `--show-toplevel` answers) the top's `.git`; then `self._hooks_dirs` from the tuple `(<--git-path hooks>, os.path.join(common, "hooks"))`, skipping a `None` and de-duplicating by `os.path.normcase(os.path.normpath(...))`; then `self.active = True`; the whole body sits in `try: ... except Exception: pass`. That order, that dedupe and that `try` stay as they are. REFAC-008 and REFAC-009, the two commits before HEAD, are this stage's earlier refactoring briefs; this one touches none of their code.

**Names.** At `822212f` the string `_git_rev_parse_path` appears nowhere in the repository's tracked files outside this brief; the name is free. No file under `tests/` or `tools/` names `_git_dir`, `_git_resolved_path`, `_git_rev_parse` or `GitConfigWatch.after`'s body; the tests reach them only through `GitConfigWatch(...)`, `watch.before()`, `watch.after()` and the launcher's standard error.

**How the tests reach this code.** `tests/test_program_git_config.py` (TASK-062) runs the launcher on a test or driver run in temporary repositories (a plain checkout, a sub-folder launch with and without a relative `core.hooksPath`, a linked worktree whose `.git` file and `commondir` are rewritten, hooks folders swapped for links, unreadable entries) and asserts the exact `GIT-CONFIG` lines; one case (`test_r081_one_entry_whose_read_fails_in_any_way_silences_no_other_line`) builds `GitConfigWatch` in-process and calls `before()` and `after()`. `tests/test_bridge_run.py` holds the launcher's other cases, the four `test_r081_` ones among them. `tests/test_header_currency.py` reads, by syntax tree, the names the programs under `bridge/cursor-bridge/` define and use; it is in the command below because this change removes and adds names. The tests make no network call. Some cases are marked POSIX-only and are skipped on Windows (the FIFO case among them); that is expected, and the skip count must be the same before and after.

**The expected count.** The supervisor ran the pytest command below at `822212f` with this brief untracked: `165 passed, 1 skipped` (the skip: `tests\test_program_git_config.py:283: a named pipe in a folder is POSIX's mkfifo`). Your before-edit run is the baseline, and the after-edit run must match it (the same count passed, none failed, the same count skipped).

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for bridge-run.py; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.12a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.12a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.12a`. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** This is a logic and path-handling surface: the watch turns git's answers (paths printed by `git rev-parse` in the launch folder's repository, which a test or driver run may have steered) into the files it reads and the paths it prints. `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). This change moves no boundary: the same files are read the same way (no link followed, no non-regular file opened), every failure still leaves the watch inactive or the entry `unreadable`, and nothing new is printed.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders and the repositories they create there. Never run bridge-run.py, review-guard.py or `bridge-install.py` yourself, against this repository or any other, and never call GitHub.

## Diagrams
`docs/diagrams/D-002-components.md` — the element `bridge_run` (`bridge/cursor-bridge/bridge-run.py`), whose edge to bridge_env already exists:

```mermaid
    bridge_run --> bridge_env
```

The change is internal to `bridge_run`: it adds no import and no edge, so the diagram does not change. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -e _git_dir -e _git_resolved_path -e _git_rev_parse -e "def after" -- bridge tools tests docs`. Expected (line numbers may differ by a few): in `bridge/cursor-bridge/bridge-run.py`, lines 2444, 2463, 2464, 2472, 2474, 2547, 2553, 2560 and 2602, the sites and calls of the Objective. Every other line is an expected hit that is **not** a site: `bridge/cursor-bridge/bridge-install.py` lines 160 and 194 (`has_git_dir`); `bridge/cursor-bridge/review-guard.py` lines 181, 861, 966, 1685 and 1716 (`find_git_dirs`, and line 1685's local variable `_git_dir`); `docs/BUILDER_NOTES.md` line 46 and `docs/HARDENING.md` lines 2119 and 2124 (records naming `_git_resolved_path` and `_git_rev_parse`); `tests/test_d003_review_round_states.py` line 453, `tests/test_release_s_records_gate.py` line 188 and `tests/test_review_guard.py` line 411 (`find_git_dirs`); `tests/test_program_review_rows.py` line 191 (`def after_verdict`). Then run `git grep -n -w _git_rev_parse_path` and confirm it shows nothing outside `handoff/REFAC-010.md`. If a check does not hold (a hit that is neither a site nor in this expected list), stop, change nothing, and report it.
2. bridge-run.py defines `_git_rev_parse_path(folder, *args)` once, private, with the semantics and a docstring true to the code as the Objective states.
3. bridge-run.py no longer defines `_git_dir` or `_git_resolved_path`, and `GitConfigWatch` no longer has an `after` method body: `after = before` in the class body. `_git_rev_parse` and `git_common_dir` are unchanged. The three call sites (line 2547, site 4, line 2560's first tuple entry) call `_git_rev_parse_path` with the arguments the Objective states. Every caller gets, for every input, the value it got before, except site 4's absolute answer, now normalized, which the Objective shows to be unobservable.
4. No other line of bridge-run.py changes. It keeps its CRLF line endings and gains no trailing whitespace. No docstring or comment you leave states something the code does not do.
5. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: the same `bridge-run: GIT-CONFIG <path> <word>` lines, in the same order, the same exit codes and the same other standard-error lines of `bridge-run.py` around a test or driver run, for every layout, including a launch outside any repository, a launch from a sub-folder with and without a relative `core.hooksPath`, a linked worktree, an absolute `core.hooksPath`, a hooks folder that is a link, and a read that fails.
- [ ] The report states, from reading `_git_display_path` and `_git_file_state`, why normalizing an absolute `--show-toplevel` answer changes neither the file read nor the printed path.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] The duplicate code is gone: `git grep -n -e "def _git_dir" -e "def _git_resolved_path" -e "def after" -- bridge` shows nothing; `git grep -n -w _git_rev_parse_path -- bridge` shows four lines, all in `bridge/cursor-bridge/bridge-run.py` (the definition and its three calls); `git grep -n -w _git_rev_parse -- bridge` shows two lines, both in bridge-run.py (the definition and the one call inside `_git_rev_parse_path`); `git grep -n "after = before" -- bridge` shows one line, in bridge-run.py.
- [ ] No public signature outside the listed sites changed; the only new name is the private `_git_rev_parse_path`; `GitConfigWatch(folder)`, `before()`, `after()` and `active` keep their names and signatures.
- [ ] bridge-run.py imports nothing new.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.12a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.12a`).
- [ ] `git diff --stat` shows only `bridge/cursor-bridge/bridge-run.py`, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service: its tests run git locally in pytest's temporary folders; do not invent a mock of git's answers, and do not add or change a fixture.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch; the one git launch, in `_git_rev_parse`, stays as it is.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_program_git_config.py tests/test_bridge_run.py tests/test_header_currency.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; the four `git grep` commands of the fourth acceptance criterion.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example `git_common_dir` repeating `_git_rev_parse`'s body, the `import stat` inside two functions, `_git_hooks_dir_listable`'s `lexists` repeating `_snapshot`'s, or hooks folders de-duplicated by `normcase(normpath)` only); report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: the one helper `_git_rev_parse_path` and the class-body alias `after = before`; no class, no new parameter (in particular no flag on the helper to skip the normalization), no other alias, nothing new outside bridge-run.py except the regenerated manifest.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-010-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the Requirements 1 grep commands with their output as the evidence;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, `git diff --numstat -- bridge/cursor-bridge/VERSION` and the fourth acceptance criterion's four `git grep` commands, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- the statement, from your reading of `_git_display_path` and `_git_file_state`, of why the normalized `--show-toplevel` answer changes neither the file read nor the printed path;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
