---
record: brief
header: 1
id: "TASK-062"
round: 2
satisfies: [R-081]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_git_config.py", "tests/test_bridge_run.py", "docs/BUILDER_NOTES.md", "handoff/TASK-062-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-062 round 2: The launcher detects a change of git's configuration (R-081)

Round cause: security - bridge/cursor-bridge/bridge-run.py:2123, `_git_file_state` hashes an entry with one whole `f.read()`, so one huge file a test run plants in a hooks folder raises MemoryError, which empties the whole after-read and silences every GIT-CONFIG line of the run, the `.git/config changed` of a planted `core.fsmonitor` included (security audit, round 1, B1); behaviour - bridge/cursor-bridge/bridge-run.py:2638-2642, `main()` creates a missing `run/` folder before `write_log`, defeating its rule of writing only where a project's `run/` folder exists (Review A B1, security audit B2)

## Objective
This is round 2 of TASK-062. Round 1's code is committed ("checkpoint before TASK-062-r2", `git log` shows it) with the supervisor's corrections to the acceptance file. Round 1 met most of the brief; this round makes the minimum changes the corrections below name, keeps every test green, and edits nothing in the acceptance file. Round 1's brief, `handoff/TASK-062.md`, stays in force for everything this brief does not change.

Satisfies: R-081 - The launcher detects a change of git's configuration made by a test or driver run (J17): it reads the repository's `config` and `info/attributes` in its common git folder, the worktree's own `config.worktree`, and every entry of the hooks folders by name and content (the folder `core.hooksPath` names and `.git/hooks`) before and after the run and prints one `bridge-run: GIT-CONFIG <path> <word>` line per difference on standard error, the word `new`, `removed` or `changed`, the run's exit unchanged and nothing restored; step 4 of the loop names the line beside its read of the same files.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_git_config.py
- tests/test_bridge_run.py
- docs/BUILDER_NOTES.md
- handoff/TASK-062-r2-report.md

Limits on these files: `bridge-run.py`: round 1's helpers (`_git_rev_parse` to `git_config_changes`, `GitConfigWatch`) and their use in `main()`, and the removal of round 1's `run/` hunk; nothing else. `MANIFEST.json` only as regenerated. `tests/test_program_git_config.py` is the supervisor's, read only. `tests/test_bridge_run.py`: your round-1 R-081 cases and their helpers, and cases you add; no other case changes. `docs/BUILDER_NOTES.md`: remove your round-1 line about the `run/` folder (the cause is fixed in the acceptance file); a new line goes at the file's end.

Do not modify anything else.

## Out of scope
As round 1's brief. In particular: `write_log`, `write_pid_file` and every other launcher function outside the limits above untouched; no option, no environment variable, no new dependency, no new import of a module outside the standard library, no module docstring changed; the supervisor's mutants file is not yours.

## Corrections
1. **Remove the `run/` hunk (behaviour; Review A B1, audit B2).** Delete round 1's lines in `main()` that create `run/` before `write_log` (lines 2638 to 2642). A launch folder with no `run/` gets no row and no new folder, as before this increment. The acceptance file's `make_repo` now creates `run/`, which is how a project's Workspace looks.
2. **One entry can never empty the read (security; audit B1).** `_git_file_state` hashes a regular file in fixed-size chunks (`hashlib.sha256` updated with reads of at most 65,536 bytes), never one whole read; and every failure of one path's read, of any exception type (MemoryError included), gives that path the state `unreadable`, so that every other path's line stands (round 1's Requirements 5 and 7).
3. **Never open what is not a regular file, never follow a link (security; audit advisory, Review A should-fix).** Each file and hooks entry is examined with `os.lstat` first: only a regular file that is not a link (`stat.S_ISREG` on the `lstat` result; on Windows a reparse point such as a junction is no regular file) is opened and hashed. Absent: no state (as today). Anything else (a folder, a FIFO, a device, a symbolic link, a junction): the state `unreadable`, and it is never opened. So a sub-folder of a hooks folder present before and after gives no line (the state is the same both times), a hook replaced by a folder gives `unreadable`, and a FIFO planted in a hooks folder never blocks the after-read. This replaces round 1's skipping of sub-folders.
4. **Never list a hooks folder through a link (security; audit advisory).** A hooks folder is listed only when, at that read, it is a folder and not a link or junction (examined with `os.lstat`). When it is not (swapped for a junction or a symbolic link, replaced by a file, removed), its own path gets the state `unreadable` (or no state when it is absent) and none of its entries is read, so its entries read as absent: a swap for a junction gives `<folder> unreadable` and a `removed` line for each entry it held before, and no entry of the link's target is ever named or hashed.
5. **Two more files of a linked worktree (security; audit advisory).** The fixed list gains the worktree's own `.git` file at the worktree's top (`git rev-parse --show-toplevel`, then its `.git`; in a main worktree that is the `.git` folder, `unreadable` both times by correction 3, so no line) and `commondir` in the worktree's own git folder (`git rev-parse --git-dir`). Both are read like the other files. In a linked worktree the `.git` file lies outside the folder that holds the common git folder; it is printed in round 1's form for such a path.
6. **Your refused-driver case tests something (test; Review A B2).** `test_r081_refused_driver_prints_no_git_config`: the refused program is one that would plant a hook (it writes `.git/hooks/post-merge`); after the refused launch assert the hook is absent and `.git/config`'s bytes are unchanged; and show the precondition: the same program placed under `run/supervisor/` and launched as a driver gives `.git/hooks/post-merge new`.
7. **Your limit-path case does not race (test; Review A should-fix).** `test_r081_limit_path_prints_git_config_before_exit_124`: the child writes `.git/config` through `pathlib` (no git process) before it sleeps, and the limit is at least 5 seconds.
8. **Your helper's environment (test; Review A advisory).** `_r081_env` pops `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR` and `GIT_INDEX_FILE` as the acceptance file's `env_for` does.

## Context
The acceptance file `tests/test_program_git_config.py` (the supervisor's, committed at the round-2 checkpoint) gained: `make_repo` creates `run/`; a launch from a sub-folder of the worktree with a relative `core.hooksPath` (`.githooks/pre-commit changed`) and without one (`.git/hooks/pre-push new`, once); a hook replaced by a folder (`.git/hooks/pre-commit unreadable`); a sub-folder of `.git/hooks` present before and after with a file changed inside it (no line); a FIFO planted in `.git/hooks` on POSIX (`.git/hooks/post-merge unreadable`, the run ends, the exit line last; skipped on Windows); the hooks folder swapped for a junction or symbolic link to a folder of other files (`.git/hooks unreadable`, `.git/hooks/pre-commit removed`, every other line `removed`, no name of the target's files); in a linked worktree `commondir` and the `.git` file rewritten (`.git/worktrees/wt/commondir changed` and a line ending `wt/.git changed`, exactly two lines). The supervisor's run of it on round 1's code is quoted in the round-2 checkpoint's commit message.

Threat model: as round 1's brief (`docs/INVENTORY.md` Decisions, "The bridge's threat model as a whole"). What a test or driver run writes into `.git` or a hooks folder, a huge file, a FIFO, a link or a junction among it, is outside input, and a junction needs no privilege on Windows.

## Acceptance criteria
- [ ] Every test in `tests/test_program_git_config.py` passes (the FIFO case skipped on Windows only), and every test of round 1's Done list passes.
- [ ] Corrections 1 to 8 met, each named in the report with its function and lines.
- [ ] Round 1's requirements and choices stand where this brief does not change them.
- [ ] Every line added ASCII; no option, environment variable or dependency.

## Constraints
Round 1's brief's Constraints all stand (foreground commands only, named test files only with the Done commands, no `python -c` or script of your own, no git command that writes, never point the launcher at the checkout or write its `.git` or `run/launcher/runs.jsonl`, ASCII, windowless subprocesses with a timeout in tests, the report's form; if an acceptance test and this brief seem to disagree, stop and report it, editing neither the test nor the product around it). Mutations by hand, in process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (H1) the `run/` hunk restored; (H2) the chunked read replaced by one whole read inside a `try` that catches only `OSError`; (H3) the `lstat` test dropped so a folder entry is skipped again; (H4) a hooks folder listed through a link. Prefer the smallest change; refactor nothing else.

## Done
Your report is `handoff/TASK-062-r2-report.md`, written as you go, in round 1's form (files changed, the report itself among them; summary; each correction in one sentence with the function and lines; every command below with its output, verbatim, in fenced blocks, each pytest summary line quoted; the mutations H1 to H4, each with the FAILED line and the summary line; a last section headed exactly `Assumed, not verified`). It names no computer path: `<Workspace>` for the repository folder, `~` for the home folder.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change; run them again in order if you edit anything after them, and quote the last run:
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check` (expect the reference current)
3. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_git_config.py`
4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_slot.py`
5. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run_driver.py tests/test_release_s_launcher.py tests/test_program_review_rows.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_review_guard.py tests/test_task032_supervisor_launcher.py tests/test_dump_cli.py`
7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect the sources to match)
8. `git diff --stat HEAD`
9. `git rev-parse HEAD` and `git status --short`

Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
