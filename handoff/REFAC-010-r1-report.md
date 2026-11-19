# REFAC-010 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `handoff/REFAC-010-r1-report.md` (this file)

## Summary

`bridge-run.py` now resolves a `git rev-parse` path in one private helper, `_git_rev_parse_path`, and `GitConfigWatch.after` is the same method as `before`. `_git_dir` and `_git_resolved_path` are gone. `MANIFEST.json` was regenerated at version `2026.11.12a`. Behaviour is unchanged: the same files are watched in the same order, the same `bridge-run: GIT-CONFIG` lines are printed, and the same failures still leave the watch inactive or the entry `unreadable`.

## Start state

Working tree before edits: clean (no uncommitted changes). HEAD is `cadcbdfa1020b41c0cbae6478d9cb9a42ae7c66c`, the commit that adds this brief, one commit after `822212f` (REFAC-009). The helper sites were at the line numbers the Objective names.

```text
git status --short && echo "---HEAD---" && git rev-parse HEAD && echo "---GREP1---" && git grep -n -e _git_dir -e _git_resolved_path -e _git_rev_parse -e "def after" -- bridge tools tests docs; echo "GREP1_EXIT:$?" && echo "---GREP2---" && git grep -n -w _git_rev_parse_path; echo "GREP2_EXIT:$?"
---HEAD---
cadcbdfa1020b41c0cbae6478d9cb9a42ae7c66c
---GREP1---
bridge/cursor-bridge/bridge-install.py:160:        if has_git_dir(release):
bridge/cursor-bridge/bridge-install.py:194:def has_git_dir(folder):
bridge/cursor-bridge/bridge-run.py:2444:def _git_rev_parse(folder, *args):
bridge/cursor-bridge/bridge-run.py:2463:def _git_dir(folder):
bridge/cursor-bridge/bridge-run.py:2464:    raw = _git_rev_parse(folder, "--git-dir")
bridge/cursor-bridge/bridge-run.py:2472:def _git_resolved_path(folder, git_path_name):
bridge/cursor-bridge/bridge-run.py:2474:    raw = _git_rev_parse(folder, "--git-path", git_path_name)
bridge/cursor-bridge/bridge-run.py:2547:            git_dir = _git_dir(folder)
bridge/cursor-bridge/bridge-run.py:2553:            top = _git_rev_parse(folder, "--show-toplevel")
bridge/cursor-bridge/bridge-run.py:2560:            for hooks in (_git_resolved_path(folder, "hooks"), os.path.join(common, "hooks")):
bridge/cursor-bridge/bridge-run.py:2602:    def after(self):
bridge/cursor-bridge/review-guard.py:181:def find_git_dirs(start):
bridge/cursor-bridge/review-guard.py:861:    root, git_dir, common = find_git_dirs(cwd)
bridge/cursor-bridge/review-guard.py:966:    root, git_dir, common = find_git_dirs(cwd)
bridge/cursor-bridge/review-guard.py:1685:    root, _git_dir, common = find_git_dirs(cwd)
bridge/cursor-bridge/review-guard.py:1716:    root, _, common = find_git_dirs(cwd)
docs/BUILDER_NOTES.md:46:2026-11-15 TASK-062-r2: `git rev-parse --git-path hooks` from a worktree sub-folder returns a path relative to the launch folder (for example `../.githooks`), not to `--show-toplevel`; `_git_resolved_path` must join against `os.getcwd()` or the hook watch misses the planted file.
docs/HARDENING.md:2119:- **Recorded from the reviews, not fixed in TASK-062 (non-blocking; leads).** (1) `_git_resolved_path`'s docstring still says "relative answers resolve against the worktree top" (Review A, round 2; records): fixed by the next increment that edits `bridge-run.py`, TASK-084. (2) The limit path's after-read runs before `killer()`, the child tree alive: a write timed after it is unseen, and the read's cost delays the kill (both reviewers; the job ends the launcher with the tree, so the order stands). (3) Between `lstat` and `open`, a regular hook swapped for a FIFO blocks `open` on POSIX, before the kill on the limit path; `os.open` with `O_NOFOLLOW | O_NONBLOCK` and an `fstat` of the same device and inode would close it (both reviewers; a deliberate race, KP-032). (4) The same gap between the folder's `lstat` and `os.listdir`: a junction swapped in between is listed through. (5) A hooks folder or hook that is a link at both reads gives `unreadable` both times and no line, so a retarget, or a hook planted in a linked folder's target, is unseen; an owner's own linked hooks folder is never read (a link's state as its target would close it). (6) Only the hooks folder's last component is checked for links: with `core.hooksPath` at `tools/hooks`, a `tools` swapped for a junction is listed through. (7) A MemoryError from `os.listdir` or from building the state still empties the read (only per-entry failures are caught). (8) No cap on entries or bytes: a hooks folder of many or huge files costs every later launch twice. (9) A path outside the folder that holds the common git folder (a linked worktree's `.git` file, an absolute `core.hooksPath`) is printed absolute, a computer path on the run's standard error. (10) Before-read git calls run on the cannot-start paths that return 125 after them. (11) `_git_rev_parse` repeats `git_common_dir`'s body; `before()` and `after()` are the same; `_git_hooks_dir_listable`'s `lexists` repeats `_snapshot`'s; `import stat` stands inside two functions: the stage's refactoring pass. (12) `bridge_env.is_link` takes any nonzero reparse tag as a link: by the audit, Python 3.12's `lstat` resolves the non-surrogate kinds (OneDrive placeholders, deduplicated files), so no false `unreadable`; a Workspace in a OneDrive folder is the layout to check. (13) The sub-folder join relies on a git that answers `--git-path` relative to the current folder (2.13 and later, unverified). (14) On POSIX a hook name holding a newline prints a forged `bridge-run:` line (the exit line still last); escaping control characters would close it. (15) An `include.path` present before the run that points at a file in the checkout is not read. (16) D-004's edge says "the hooks folders' names" where J17 and the code compare name and content (the brief's packager's note, not a review's). (17) The builder reports: round 1's quotes G1 to G3 by their FAILED lines without a summary line and does not list itself; round 2's says "four cases" where it changed two cases and two helpers, its step 9 omits the report itself, and it calls H1 "not run" where it ran unkilled; `docs/BUILDER_NOTES.md` keeps two blank lines where round 1's line was removed. (18) The in-process case `test_r081_one_entry_whose_read_fails_in_any_way_silences_no_other_line` does not prove chunking: a whole read inside `except Exception` passes it, and mutant m2 is the whole read catching only `OSError` (Review A, round 2); chunking is checked by reading the code. (19) Hooks folders are de-duplicated by `normcase(normpath)` only (`GitConfigWatch.__init__`): a junction, a `subst` drive or an 8.3 name for the same folder reads it twice, one change printing two lines (Review A, round 1; unchanged in round 2). (20) 4db20db's message disposes of the builder's first assumption (a relative `core.hooksPath` from a linked worktree) as "test", where no case covers that layout: the sub-folder cases run in the main worktree and the worktree cases set no `core.hooksPath` (Review A's re-read of the records); its disposition is accepted, a lead, until a case of it is written.
docs/HARDENING.md:2124:- **Recorded from the reviews, not fixed in TASK-084 (non-blocking; leads).** (1) `MERGE_UNIT_RE` backtracks quadratically on a line that holds `Merge unit:`, then a long run of white space, then a character the pattern does not match: about 20 s per pass on 100,000 spaces. A brief is read some five times per launch now where it was three before (the keys-filtered header call and the rule each read the prose). The pattern's text is held frozen by a test. A cap on a line's length before the match, or one reading of the brief passed along, would close it (the security audit, round 1; a local cost to someone who can already write the checkout). (2) The other forms of a `Merge unit:` line that the pattern does not read stay unread, as the design's non-goals keep them: an ID in lower case, a comma between IDs, words after them. A unit of two or more so mistyped meets what it met before: beside a header that lists its IDs, `header: disagrees merge_unit`; beside `merge_unit: null`, or in a brief with no header, a launch as a single increment (the design's lead). A mistyped line of one word beside a header listing one is now answered by the rule for the header, as the plan's Done when asks (the acceptance case `word-not-id-header-one`). (3) Two or more is counted as written. A line naming one ID twice, beside a header listing it twice, passes the rule and the agreement, and the branch rule's declared set holds the one ID: a unit that reads as one increment, launched as on the checkpoint. Counting the distinct IDs the readers return would close it if the requirement is ever tightened (the security audit, round 2). A brief with a line of one ID and a line of two passes the rule too. Beside a header listing one, the whole header call refuses it `header: disagrees merge_unit`, as on the checkpoint, since the prose reader skips the line of one and returns the line of two. Beside a header listing the two, it launches as a unit of two, the line of one unread. (Review A's re-read of the records corrected the records' first reading of this case.) (4) The lead `_git_resolved_path`'s docstring (TASK-062, lead 1) was meant for TASK-084, the next increment to edit `bridge-run.py`, but its brief named no such line; it goes to TASK-065, the next increment whose Scope holds `bridge-run.py`. (5) The builder's reports have gaps. Round 1's says `Assumed, not verified: none` and gives no hand mutations. Round 2's selected its mutation runs with `-k`, beyond the Done section's commands; two of its three assumptions omit what would confirm them; and its correction 3 names no lines. (6) Not a lead but a correction, made before the full run on Review A's notes of round 2: the supervisor's mutants file. m03 now drops the whole match of the rule's pattern, so it is true to its name, and its list gains the four kept cases whose line names two. m13 and m14 list only the 17 reader cases whose brief holds a line of one word of the ID form.
tests/test_d003_review_round_states.py:453:    root, _git, common = guard.find_git_dirs(str(repo))
tests/test_program_review_rows.py:191:def after_verdict(out):
tests/test_release_s_records_gate.py:188:    root, _, common = mod.find_git_dirs(str(repo))
tests/test_review_guard.py:411:    monkeypatch.setattr(mod, "find_git_dirs", boom)
GREP1_EXIT:0
---GREP2---
handoff/REFAC-010.md:55:- bridge-run.py gains one private function, `_git_rev_parse_path(folder, *args)`: `raw = _git_rev_parse(folder, *args)`; `None` gives `None`; an absolute `raw` gives `os.path.normpath(raw)`; otherwise `os.path.normpath(os.path.join(os.path.abspath(folder or "."), raw))`. Its docstring says what it does: the absolute path of a `git rev-parse` answer, a relative answer resolved against the launch folder (`folder`, or the current folder), `None` where git gives none. Its placement near `_git_rev_parse` is yours.
handoff/REFAC-010.md:56:- `_git_dir` and `_git_resolved_path` are deleted, with `_git_resolved_path`'s docstring. Line 2547 calls `_git_rev_parse_path(folder, "--git-dir")`; line 2560's first tuple entry is `_git_rev_parse_path(folder, "--git-path", "hooks")`.
handoff/REFAC-010.md:57:- Site 4 becomes `top = _git_rev_parse_path(folder, "--show-toplevel")` followed by the existing `if top:` block without its own `isabs` test and join (the `dot_git` lines unchanged).
handoff/REFAC-010.md:89:**Names.** At `822212f` the string `_git_rev_parse_path` appears nowhere in the repository's tracked files outside this brief; the name is free. No file under `tests/` or `tools/` names `_git_dir`, `_git_resolved_path`, `_git_rev_parse` or `GitConfigWatch.after`'s body; the tests reach them only through `GitConfigWatch(...)`, `watch.before()`, `watch.after()` and the launcher's standard error.
handoff/REFAC-010.md:111:1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -e _git_dir -e _git_resolved_path -e _git_rev_parse -e "def after" -- bridge tools tests docs`. Expected (line numbers may differ by a few): in `bridge/cursor-bridge/bridge-run.py`, lines 2444, 2463, 2464, 2472, 2474, 2547, 2553, 2560 and 2602, the sites and calls of the Objective. Every other line is an expected hit that is **not** a site: `bridge/cursor-bridge/bridge-install.py` lines 160 and 194 (`has_git_dir`); `bridge/cursor-bridge/review-guard.py` lines 181, 861, 966, 1685 and 1716 (`find_git_dirs`, and line 1685's local variable `_git_dir`); `docs/BUILDER_NOTES.md` line 46 and `docs/HARDENING.md` lines 2119 and 2124 (records naming `_git_resolved_path` and `_git_rev_parse`); `tests/test_d003_review_round_states.py` line 453, `tests/test_release_s_records_gate.py` line 188 and `tests/test_review_guard.py` line 411 (`find_git_dirs`); `tests/test_program_review_rows.py` line 191 (`def after_verdict`). Then run `git grep -n -w _git_rev_parse_path` and confirm it shows nothing outside `handoff/REFAC-010.md`. If a check does not hold (a hit that is neither a site nor in this expected list), stop, change nothing, and report it.
handoff/REFAC-010.md:112:2. bridge-run.py defines `_git_rev_parse_path(folder, *args)` once, private, with the semantics and a docstring true to the code as the Objective states.
handoff/REFAC-010.md:113:3. bridge-run.py no longer defines `_git_dir` or `_git_resolved_path`, and `GitConfigWatch` no longer has an `after` method body: `after = before` in the class body. `_git_rev_parse` and `git_common_dir` are unchanged. The three call sites (line 2547, site 4, line 2560's first tuple entry) call `_git_rev_parse_path` with the arguments the Objective states. Every caller gets, for every input, the value it got before, except site 4's absolute answer, now normalized, which the Objective shows to be unobservable.
handoff/REFAC-010.md:121:- [ ] The duplicate code is gone: `git grep -n -e "def _git_dir" -e "def _git_resolved_path" -e "def after" -- bridge` shows nothing; `git grep -n -w _git_rev_parse_path -- bridge` shows four lines, all in `bridge/cursor-bridge/bridge-run.py` (the definition and its three calls); `git grep -n -w _git_rev_parse -- bridge` shows two lines, both in bridge-run.py (the definition and the one call inside `_git_rev_parse_path`); `git grep -n "after = before" -- bridge` shows one line, in bridge-run.py.
handoff/REFAC-010.md:122:- [ ] No public signature outside the listed sites changed; the only new name is the private `_git_rev_parse_path`; `GitConfigWatch(folder)`, `before()`, `after()` and `active` keep their names and signatures.
handoff/REFAC-010.md:152:- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example `git_common_dir` repeating `_git_rev_parse`'s body, the `import stat` inside two functions, `_git_hooks_dir_listable`'s `lexists` repeating `_snapshot`'s, or hooks folders de-duplicated by `normcase(normpath)` only); report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: the one helper `_git_rev_parse_path` and the class-body alias `after = before`; no class, no new parameter (in particular no flag on the helper to skip the normalization), no other alias, nothing new outside bridge-run.py except the regenerated manifest.
GREP2_EXIT:0
```

`git status --short` printed no lines. Every GREP1 line is a site in `bridge-run.py` or an expected non-site named in Requirement 1. `git grep -n -w _git_rev_parse_path` prints only lines in `handoff/REFAC-010.md`.

```text
git log -8 --oneline && python -c "p=r'bridge/cursor-bridge/bridge-run.py'; d=open(p,'rb').read(); print('crlf', d.count(b'\r\n'), 'lf_only', d.count(b'\n')-d.count(b'\r\n'), 'len', len(d))"
cadcbdf REFAC-010: the brief (stage P2's refactoring pass, candidate 4)
822212f REFAC-009: one reading of a reader's reply bits and a rule's contexts, in bridge_env
3cc411a REFAC-009: the brief (stage P2's refactoring pass, candidate 2)
ff5786e REFAC-008: one reader of a check's app id and suite id, in bridge_env
deed43f REFAC-008: the brief (stage P2's refactoring pass, candidate 1)
45e4322 TASK-082: stage P2's texts (R-078, R-081, R-083, R-085, R-087, R-105) (#181)
b213ea6 TASK-067: the pre-push scan as a program (R-087) (#180)
667c646 TASK-066: the invisible-character check refuses by category (R-086) (#179)
crlf 3146 lf_only 0 len 141999
```

## Pytest (before the edit)

Counts belong to commit `cadcbdfa1020b41c0cbae6478d9cb9a42ae7c66c` with a clean working tree.

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_git_config.py tests/test_bridge_run.py tests/test_header_currency.py
..................s..................................................... [ 43%]
........................................................................ [ 86%]
......................                                                   [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_program_git_config.py:283: a named pipe in a folder is POSIX's mkfifo
165 passed, 1 skipped in 49.58s
```

Summary line: `165 passed, 1 skipped in 49.58s`.

## Line endings after the source edit

```text
python -c "p=r'bridge/cursor-bridge/bridge-run.py'; d=open(p,'rb').read(); print('crlf', d.count(b'\r\n'), 'lf_only', d.count(b'\n')-d.count(b'\r\n'), 'cr_only', d.count(b'\r')-d.count(b'\r\n')); text=d.decode('utf-8'); bad=[i for i,line in enumerate(text.split('\n'),1) if (line[:-1] if line.endswith('\r') else line).rstrip(' \t')!=(line[:-1] if line.endswith('\r') else line)]; print('trailing', bad[:20], 'count', len(bad))"
crlf 3129 lf_only 0 cr_only 0
trailing [] count 0
```

Every line is CRLF. No line has trailing whitespace.

## Why a normalized absolute `--show-toplevel` changes neither the file read nor the printed path

`_git_file_state` decides the entry with `os.path.lexists`, `os.lstat`, `bridge_env.is_link`, and `open` on the path it is given. Site 4 still builds `dot_git` with `os.path.join(top, ".git")` and still appends that pair next, in the same place in `self._files`. An absolute `--show-toplevel` answer used to be kept as git printed it; it now goes through `os.path.normpath`. Git prints that top as a resolved absolute path (on Windows with forward slashes, with no `.` or `..` part and no trailing separator), so `normpath` changes only the separators. Those four calls name the same file either way. `_git_display_path` tries `os.path.relpath(abs_path, parent)`, which makes both arguments absolute and normalized before it compares them, then turns backslashes into `/`; a separator-only difference in `top` therefore does not change the relative text. On `ValueError`, or when that relative result starts with `..`, it returns `os.path.normpath(abs_path)` with backslashes turned into `/`, which is the same string once the only difference was separators. `if top:` is taken in the same cases: `_git_rev_parse` returns `None` rather than an empty string, and `normpath` of a non-empty string is non-empty. The hooks tuple, the `None` skip, and the `os.path.normcase(os.path.normpath(...))` dedupe are unchanged, and the `--git-path` and `--git-dir` answers were already normalized by the deleted helpers. No case turned up where the printed path, the file read, or the order or dedupe of `self._files` and `self._hooks_dirs` differs.

Behaviour is identical because every caller still receives the path it received before, the watch still reads the same files in the same order and prints the same `bridge-run: GIT-CONFIG <path> <word>` lines, and the same exceptions are still swallowed.

## After the last source edit

```text
python tools/make-manifest.py && echo "---DUMP---" && python tools/dump-cli.py --check; echo "DUMP_EXIT:$?" && echo "---CHECK---" && python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet && echo "---NUMSTAT---" && git diff --numstat -- bridge/cursor-bridge/VERSION; echo "NUMSTAT_DONE" && echo "---VERSION---" && python -c "print(repr(open(r'bridge/cursor-bridge/VERSION','rb').read()))" && echo "---GREP-A---" && git grep -n -e "def _git_dir" -e "def _git_resolved_path" -e "def after" -- bridge; echo "GREP_A_EXIT:$?" && echo "---GREP-B---" && git grep -n -w _git_rev_parse_path -- bridge && echo "---GREP-C---" && git grep -n -w _git_rev_parse -- bridge && echo "---GREP-D---" && git grep -n "after = before" -- bridge
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
---DUMP---
DUMP_EXIT:0
---CHECK---
bridge-check: version 2026.11.12a (2026-11-19 04:53) at <Workspace>\bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
---NUMSTAT---
warning: in the working copy of 'bridge/cursor-bridge/VERSION', LF will be replaced by CRLF the next time Git touches it
NUMSTAT_DONE
---VERSION---
b'2026.11.12a\n'
---GREP-A---
GREP_A_EXIT:1
---GREP-B---
bridge/cursor-bridge/bridge-run.py:2463:def _git_rev_parse_path(folder, *args):
bridge/cursor-bridge/bridge-run.py:2538:            git_dir = _git_rev_parse_path(folder, "--git-dir")
bridge/cursor-bridge/bridge-run.py:2544:            top = _git_rev_parse_path(folder, "--show-toplevel")
bridge/cursor-bridge/bridge-run.py:2549:            for hooks in (_git_rev_parse_path(folder, "--git-path", "hooks"), os.path.join(common, "hooks")):
---GREP-C---
bridge/cursor-bridge/bridge-run.py:2444:def _git_rev_parse(folder, *args):
bridge/cursor-bridge/bridge-run.py:2465:    raw = _git_rev_parse(folder, *args)
---GREP-D---
bridge/cursor-bridge/bridge-run.py:2591:    after = before
```

`python tools/dump-cli.py --check` printed no lines and exited 0 (`DUMP_EXIT:0`). `git grep -n -e "def _git_dir" -e "def _git_resolved_path" -e "def after" -- bridge` printed no lines (`GREP_A_EXIT:1`). `git diff --numstat -- bridge/cursor-bridge/VERSION` printed no numstat line; it printed the LF warning quoted above. The file's bytes are `2026.11.12a` followed by a line feed. `git grep -n -w _git_rev_parse_path -- bridge` shows four lines, all in `bridge/cursor-bridge/bridge-run.py`. `git grep -n -w _git_rev_parse -- bridge` shows two lines, both in that file. `git grep -n "after = before" -- bridge` shows one line, in that file.

## Pytest (after the last edit)

Counts belong to commit `cadcbdfa1020b41c0cbae6478d9cb9a42ae7c66c`. The working tree then held uncommitted changes, shown by the `git status --short` lines in the same command: `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/bridge-run.py` modified, and `handoff/REFAC-010-r1-report.md` untracked.

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_git_config.py tests/test_bridge_run.py tests/test_header_currency.py; echo "PYTEST_EXIT:$?" && echo "---STATUS---" && git status --short && echo "---STAT---" && git diff --stat && echo "---HEAD---" && git rev-parse HEAD
..................s..................................................... [ 43%]
........................................................................ [ 86%]
......................                                                   [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_program_git_config.py:283: a named pipe in a folder is POSIX's mkfifo
165 passed, 1 skipped in 49.66s
PYTEST_EXIT:0
---STATUS---
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
?? handoff/REFAC-010-r1-report.md
---STAT---
warning: in the working copy of 'bridge/cursor-bridge/MANIFEST.json', LF will be replaced by CRLF the next time Git touches it
 bridge/cursor-bridge/MANIFEST.json |  4 ++--
 bridge/cursor-bridge/bridge-run.py | 31 +++++++------------------------
 2 files changed, 9 insertions(+), 26 deletions(-)
---HEAD---
cadcbdfa1020b41c0cbae6478d9cb9a42ae7c66c
```

Summary line: `165 passed, 1 skipped in 49.66s`. The skip is the same POSIX named-pipe case as before the edit. None failed.

## End state

HEAD is still `cadcbdfa1020b41c0cbae6478d9cb9a42ae7c66c`. The working tree holds uncommitted changes. This command was run after the sections above were written. `git diff --stat` lists only `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/bridge-run.py`. The report is untracked, so it is absent from that stat. `docs/BUILDER_NOTES.md` was not written. No file under `tests/` changed. No mutation script is in the diff.

```text
git status --short && echo "---STAT---" && git diff --stat && echo "---HEAD---" && git rev-parse HEAD
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
?? handoff/REFAC-010-r1-report.md
---STAT---
warning: in the working copy of 'bridge/cursor-bridge/MANIFEST.json', LF will be replaced by CRLF the next time Git touches it
 bridge/cursor-bridge/MANIFEST.json |  4 ++--
 bridge/cursor-bridge/bridge-run.py | 31 +++++++------------------------
 2 files changed, 9 insertions(+), 26 deletions(-)
---HEAD---
cadcbdfa1020b41c0cbae6478d9cb9a42ae7c66c
```

## Noticed and not changed

`git_common_dir` still repeats the body of `_git_rev_parse`. `import stat` still stands inside `_git_hooks_dir_listable` and `_git_file_state`. `_git_hooks_dir_listable`'s `lexists` still repeats the one in `_snapshot`. Hooks folders are still de-duplicated by `os.path.normcase(os.path.normpath(...))` only.

## Assumed, not verified

Assumed, not verified: none
