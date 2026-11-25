---
record: brief
header: 1
id: "HOTFIX-004"
round: 2
satisfies: []
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/mutation-run.py", "tests/test_hotfix24a_heavy_slots.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/HOTFIX-004-r2-report.md"]
merge_unit: null
blocking_class: null
---
# HOTFIX-004 round 2: the heavy slots, round 1's review

## Objective
Round 1 (`handoff/HOTFIX-004.md`, your report `handoff/HOTFIX-004-r1-report.md`) built hotfix 2026.11.24a's heavy slots, and most of it stands: the setting, the slots, the waiting and not-free lines, the one-slot path and the mutation lock. Review A and the security audit rejected it for the defects listed under Requirements. The worst: the one-heavy-run-per-checkout lock is keyed on the wrong folder, so a builder launched with `--workspace` into a worktree locks the supervisor's checkout instead of the worktree. This round fixes those defects, and changes nothing else. Round 1's brief still governs every requirement it states (1 to 25), its Constraints and its out-of-scope list; read it again whole, then this brief. Where the two seem to disagree, this brief wins for the items it names; for anything else, stop and report rather than choose.

Satisfies: there is no build-plan increment and no requirements register row for this work (HOTFIX-004, the owner's two decisions of 2026-11-24, as in round 1). The trace is the acceptance file `tests/test_hotfix24a_heavy_slots.py`: round 1's 31 cases, plus the cases the supervisor added after round 1's review (the section headed `round 2: round 1's review`, every test named `test_hotfix24a_r2_*`), which fail on round 1's code. Do not add a test.

## Scope
Files you may create or modify, each only as the paragraph after the list allows:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/mutation-run.py
- tests/test_hotfix24a_heavy_slots.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/HOTFIX-004-r2-report.md

What each entry allows, exactly: `bridge-run.py` and `mutation-run.py` are the two programs you change, only as the requirements below say. `tests/test_hotfix24a_heavy_slots.py` is the supervisor's acceptance test: read it and run it, never edit it. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py`. `docs/BUILDER_NOTES.md` takes dated lines appended at its end. `handoff/HOTFIX-004-r2-report.md` is your report, a new file. Leave `handoff/HOTFIX-004-r1-report.md` as it is. Do not modify anything else.

## Out of scope
- Everything round 1's brief puts out of scope, unchanged: `.env`, `secrets/`, `.github/`, the rest of `docs/` and `handoff/`, `MANIFEST.json`, `VERSION`, `CHANGELOG.md`, every other file under `bridge/`, every other test file (`tests/test_bridge_run_slot.py` included: its line 866 now expects `"slot": 1`, the supervisor's edit), `tools/` (you only run `dump-cli.py`), `run/` and `.git/`.
- The design's Known limits stay unbuilt. In particular, what a waiter prints when it moves from the folder wait to the slot wait (round 1's fourth assumption) stays as round 1 built it.
- Never run `bridge-run.py`, `mutation-run.py` or `bridge-install.py` against the real home folder, this repository's real `run/` record or the real `cursor-agent`.

## Context
**Where you are.** The same checkout as round 1: the bridge's own source repository, on branch `hotfix-004`. Round 1's work is committed; the supervisor's checkpoint for this round is the commit that adds this brief. The development data decision of round 1's brief holds.

**What the reviewers found** (line numbers on this branch, round 1's code):
- `main` calls `acquire_heavy_for_launch(kind, run_id, limit, slot_scale, argv, folder, num_slots)` at line 3439 with `argv`, the launcher's whole argument list. It starts with `--limit`, so `workspace_of(argv, folder)` in `checkout_identity_hash` (lines 1680 to 1690) never sees `cursor-agent` as its first word and always answers the launch folder. Line 1683 also runs `_git_rev_parse_path(folder, "--show-toplevel")` on the launch folder rather than on `ws`, and the fallback at line 1685 uses `os.path.abspath`, not `os.path.realpath`. The command `cmd` itself is no better by line 3439: `resolve(cmd)` (line 3382) has replaced a `cursor-agent` first word with the launcher's path, so `is_agent_argv` is false on it too. The identity needs the command as written after `--`, before `resolve`.
- The pid file is reserved at lines 3306 to 3316, before five refusals that still end with a plain `return 125`: the key file (3323), a key file naming a home variable (3327), a limit above the cap (3335), the review-only refusal (3338) and the watch-only refusal (3341). Each leaves `run/launcher/pids/<run id>` behind, holding the launcher's own pid twice; `bridge-stop.py` matches pid files by prefix.
- `run_heavy_slots_option` (line 1702) tests `"--heavy-slots" not in argv` over the whole argument list, so a command after `--` that carries the word `--heavy-slots` is refused.
- `_open_heavy_lock` (line 2040) opens with plain `os.O_RDWR | os.O_CREAT` on Windows, so a link at `heavy.lock`, `heavy-<k>.lock` or `heavy-folder-<h>.lock` is followed: a hard link needs no privilege, and the launcher then creates or byte-locks the file it points at for the whole run. `mutation-run.py` (lines 1552 to 1557) checks `is_link` before its open, which misses a hard link and leaves a race on Windows (no `O_NOFOLLOW`).
- `write_heavy_slots_setting` (lines 1657 to 1677) leaves its `.heavy-slots.*.tmp` file when `os.replace` fails (a folder at `heavy-slots.json`, or a reader holding the file on Windows), and creates `~/.cursor-bridge` without `mode=0o700` on POSIX.
- `mutation-run.py`'s `finally` (lines 1799 to 1806) unlocks the run lock before it removes the run's scratch folder, so a second run of the same id can start while the first is still deleting it. A `Refuse` raised after the lock is taken but before the `try` at line 1589 (`validate_cache_file`, for example) leaves the lock held by an in-process caller.
- `except Exception` at lines 2228 to 2230 and 2415 to 2417 closes the lock fds without `_unlock_byte`, unlike every other path.
- At the child's start, when `write_pid_file` answers `None`, the reserved pid file (line 3315) is never removed.
- `_acquire_heavy_slot_many` (lines 2158 to 2231) duplicates the multi-slot loop of `acquire_heavy_for_launch` and is reached only through `acquire_heavy_slot` with a setting present; no product path calls it. `acquire_heavy_slot(kind, run_id, limit, scale)` is called by `tests/test_bridge_run_slot.py` (line 251) and `tests/test_bug029_agent_name.py` (line 126), always with no setting.
- Your report quoted a `git diff --stat` from before your last edit and a re-check line that is not pytest output: round 1's Done asked for commands 2 to 7 once more after the last edit.
- `bridge-run.py` lines 20 and 21 (the module docstring) hold two U+2026 ellipsis characters from before this hotfix, so the ASCII criterion fails.

## Diagrams
None. The behaviour is round 1's.

## Requirements
26. **The checkout identity follows the run's folder.** `checkout_identity_hash(folder, argv)` keeps its name and its two parameters. Its `argv` is the command as written after `--`, before `resolve`: keep a copy of the command before line 3382 replaces it and pass that copy to `acquire_heavy_for_launch` (whose `argv` parameter passes it on), never the launcher's own options. Inside it, `ws = workspace_of(argv, folder)` as now; then `git rev-parse --show-toplevel` runs on `ws` (through `_git_rev_parse_path(ws, ...)`), and whichever folder is used (git's answer, or `ws` where git gives none) goes through `os.path.realpath`, then `casefold()` on Windows, then SHA-256 as now. Tests: `test_hotfix24a_r2_identity_follows_the_builders_workspace`, `test_hotfix24a_r2_the_identity_reads_the_command_never_the_launchers_options`.
27. **No refusal leaves the pid file.** Every exit between reserving the pid file and starting the child removes it: the five refusals at lines 3323, 3327, 3335, 3338 and 3341 included. Either reserve the pid file after them (just before `bridge-run: started <run id>`, keeping the id's uniqueness loop as it is) or remove it on each; a launch's stderr lines and exits stay as they are. At the child's start, when `write_pid_file` cannot rewrite the file, the reserved file is still removed when the launcher ends. Test: `test_hotfix24a_r2_an_early_refusal_leaves_no_pid_file` (`cap`, `watch-only`, `key-file`).
28. **`--heavy-slots` is read among the launcher's own words only.** `run_heavy_slots_option` looks for `--heavy-slots` only in the words before the first `--` (the whole list when there is none); a `--heavy-slots` after `--` belongs to the command, which runs as any other. Round 1's refusals stay: `--heavy-slots` with `--` or with another launcher option exits 125 and writes nothing. Test: `test_hotfix24a_r2_heavy_slots_after_the_separator_belongs_to_the_command`, and round 1's `test_hotfix24a_heavy_slots_option_alone_only`.
29. **No link followed at a lock file.** `_open_heavy_lock`, which opens `heavy.lock`, every `heavy-<k>.lock` and every `heavy-folder-<h>.lock`: on Windows, refuse when `bridge_env.is_link(lock_path)` before the open; on every platform, after the open, `os.fstat(fd)` must show a regular file (`stat.S_ISREG`) with `st_nlink == 1`, else close the fd and raise `OSError`, so the existing callers print their refusal line, `bridge-run: refused - ~/.cursor-bridge/<that file> (<error class>)`, and exit 125. `mutation-run.py`'s run lock gets the same check after its open (regular file, one link), refusing through `Refuse` with a line beginning `mutation-run: refused - `, exit 2, writing nothing. Tests: `test_hotfix24a_r2_a_linked_lock_file_is_refused` (`heavy.lock`, `heavy-2.lock`, `folder`), `test_hotfix24a_r2_a_linked_mutation_lock_is_refused`.
30. **The setting's write leaves nothing behind.** In `write_heavy_slots_setting`, a failed `os.replace` removes the temporary file and raises, so `--heavy-slots` prints its existing refusal and exits 125; retry the replace a few times on `PermissionError` as `publish_holder_record` retries its own replace. On POSIX the state folder is created with `mode=0o700`, as `_open_heavy_lock` creates it. Test: `test_hotfix24a_r2_a_failed_setting_write_leaves_no_temporary_file`.
31. **The mutation engine keeps its lock until its scratch folder is gone.** In `mutation-run.py`, remove the run's scratch folder first, then unlock and close the run lock. A `Refuse` or any exception raised after the lock is taken releases and closes it before it propagates (move the lock under the existing `try`/`finally`, or add one). No test (the race is narrow); name the code point in your report.
32. **Every lock is unlocked before it is closed.** The `except Exception` paths of the slot loop unlock (`_unlock_byte`) every fd they hold before closing it, as every other path does. No test.
33. **One multi-slot loop.** Remove `_acquire_heavy_slot_many`. `acquire_heavy_slot(kind, run_id, limit, scale)` keeps its signature and takes slot 1 as 2026.11.23a did (`_acquire_heavy_slot_one`), whatever the setting says; only `main`'s path through `acquire_heavy_for_launch` takes several slots. Tests: the existing callers in `tests/test_bridge_run_slot.py` and `tests/test_bug029_agent_name.py` stay green.
34. **ASCII.** Replace the two U+2026 characters in `bridge-run.py`'s module docstring (lines 20 and 21) with three full stops each, then regenerate the command reference with `python tools/dump-cli.py`.

## Acceptance criteria
- [ ] `python -m pytest tests/test_hotfix24a_heavy_slots.py -q -p no:cacheprovider` passes every case, round 2's included (command 2).
- [ ] The regression batch (command 3) passes with no failure, no test file edited.
- [ ] `python tools/dump-cli.py --check` exits 0 after regeneration (command 4).
- [ ] `windowless-check.py` reports no FAIL in the two programs (command 5).
- [ ] Both programs are ASCII-only (command 6 prints `ascii ok`).
- [ ] `git status --short` shows changes only to the Scope's files (command 7).
- [ ] Requirements 26 to 34 are fully met, and round 1's requirements 1 to 25 still are; with no `heavy-slots.json`, every line and exit is byte-identical to 2026.11.23a's except the row's `"slot": 1`.

## Constraints
- Round 1's Constraints all hold, with every `HOTFIX-004-r1` in them read as `HOTFIX-004-r2` (the BUILDER_NOTES line form `YYYY-MM-DD HOTFIX-004-r2: <text>`, the report's name).
- Do not add dependencies; `stat` and `hashlib` are standard library.
- Verification commands: round 1's commands 1 to 7, exactly as written there, from the workspace root, in PowerShell, in the foreground. Run commands 2 to 7 once more after your last edit of any file, and quote that run's output verbatim, never an earlier run's and never a summary of your own wording.

## Done
Your report is the file `handoff/HOTFIX-004-r2-report.md`, which you write as you go. When you finish, it holds:
- every file you changed;
- a one-paragraph summary of what you did;
- each requirement (26 to 34) with the file and line that meets it;
- the mutation code points: for each requirement 26 to 34, the code point whose removal or change would break it, and the acceptance test (by name and parameter id) that would catch it, or `no test`;
- the output of every verification command from the run after your last edit, verbatim, in fenced blocks (both `git status --short` outputs, the last lines of both pytest runs with the summary line quoted whole and every failure's test id, the dump-cli check's exit code, the windowless-check output and exit code, the ASCII check's output, `git diff --stat`, `git rev-parse HEAD`); a command you did not run is written `not run`;
- the dated lines you appended to `docs/BUILDER_NOTES.md`, or `Builder notes: none`;
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief, round 1's brief, the design nor the existing code settled, and that you did not confirm, one per line (what you assumed; why; what would confirm it), or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
