# TASK-029, round 4: One heavy job at a time: a driver's program checked again after the slot's wait (code-only fix)

## Objective

This is round 4 of TASK-029 (`docs/BUILD_PLAN.md`, "### TASK-029 — One heavy job at a time: the launcher's machine-wide slot"). It is a code-only round with one defect to fix. `handoff/TASK-029.md`, `handoff/TASK-029-r2.md` and `handoff/TASK-029-r3.md` stay in force: their Requirements stand, and this brief adds one. Where they differ, this brief governs. TASK-028 built the launcher's `--kind driver` (R-039), and that run re-checks its program's absolute path once before it starts the command. TASK-029 then put the slot's wait, which can last hours, between that check and the start. Review B found the gap and the supervisor reproduced it. A driver run was waiting on a held slot. During the wait, its program under `run/supervisor/` was replaced by a hard link to a file outside that folder. Once the slot was free the run executed the outside file, which exited 0, and the run's log row was marked healthy. Your job is to make the driver's program get checked again after the slot is taken and immediately before the start, on both platforms. If that check fails, the run is refused the way the check before the wait refuses it. The supervisor has already written the test and committed it with this brief, and today it fails for `swap=True`. You make it pass by changing `bridge/cursor-bridge/bridge-run.py` only.

Satisfies:
- R-040: One heavy job at a time on the computer: a builder run, a test suite and a mutation run each hold one machine-wide slot in the launcher while they run (an exclusive lock on a file under the bridge's state folder in the owner's home, `~/.cursor-bridge/`), released by the operating system the instant the holder ends; a second heavy run waits for it, saying what it waits for, as long as the holder's own ceiling allows and never counting the wait against its own; a review and a CI watch take none.
- R-039, as TASK-028 built it: windowless launches enforced by the bridge, every heavy run (a mutation run included, the launcher's `--kind driver`) started through the launcher. This round touches only the part that `docs/INVENTORY.md` records in its row "Windowless launches enforced by the bridge": "the command started holds the checked absolute path, checked again just before the start" and "never a hard link".

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- docs/BUILDER_NOTES.md
- handoff/TASK-029-r4-report.md

Do not modify anything else.

## Out of scope

- .env and anything under secrets/
- CI configuration (`.github/`, `.githooks/`)
- docs/ and handoff/, except the files the Scope section names. The supervisor regenerates `bridge/cursor-bridge/MANIFEST.json` after your run. Do not run `tools/make-manifest.py`. Do not run `python tools/dump-cli.py` without `--check` either, because without it the script writes files.
- Every test file, in particular `tests/test_bridge_run_slot.py` (it holds the supervisor's new test, committed with this brief), `tests/test_bridge_run_driver.py`, `tests/test_bridge_run.py`, `tests/test_a4_followups.py`, `tests/test_loop_guard.py` and `tests/conftest.py`. You may not edit, add, rename, skip or mark any test.
- `bridge/cursor-bridge/loop-guard.py`, `bridge_env.py`, `bridge-stop.py`, `MANIFEST.json`, `VERSION` and every other file under `bridge/`.
- The module docstring of `bridge-run.py` (lines 1-88, ending with the closing `"""` at line 88) is frozen. Leave it byte-for-byte unchanged. It stays true after this round, because "refused or could not start" already covers exit 125, so the command reference stays current.
- The order of the `bridge-run: slot taken` line and the record's publication. It is recorded in `docs/HARDENING.md` (TASK-029, round 4's reviews) and taken with BUG-029. Do not change it.
- Every item in `docs/HARDENING.md` under the four "TASK-029 (round N's reviews ...)" headings, and BUG-029 (`head_of`'s `.exe`/`.cmd` stripping). Do none of them.
- The window that remains between the second check and `Popen`, because a path check followed by a start by path can always be raced. Closing it (by starting from an open descriptor or by a file identity) is not this round's work. Your fix only moves the check to just before the start.
- Any message text, constant, exit code, default or duration other than those Requirement 1 reuses.

## Context

**Where the round stands.** This is past the owner's three-round review ceiling (`docs/INVENTORY.md`, Decisions, the 2026-10-25 row). After round 3, only the five blocking classes send the work back. This defect is one of them: a heavy command runs that the launcher's own refusal is meant to stop. So the round has one fix, and the fix has to be complete.

**What your report is checked against.** In an earlier round a report claimed mutant kills that the supervisor's driver disproved, and it gave test durations that were false. The supervisor and both reviewers re-run every command in your report and check every claim against their own run. Report only what you ran, and quote pytest's own output for it.

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/bridge-run.py` by file path. `tests/conftest.py`'s autouse fixture `home_of_the_tests` gives every test a fresh temporary `HOME` and `USERPROFILE`, so the slot's lock is the tests' own `<home>/.cursor-bridge/heavy.lock`. You must never read, create or lock the owner's real `~/.cursor-bridge/heavy.lock` or `heavy.lock.holder`. Any launcher run you make outside pytest (a by-hand mutation check included) sets `HOME` and `USERPROFILE` to a temporary folder you created for it, and uses a temporary launch folder, never the Workspace.

**Security context.** ASVS level 2 (INVENTORY, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you, and so is the frozen `minimal-code.mdc`. The trust boundary in this round is the driver's program file. Any program of the owner's account can replace, link or rename `run/supervisor/<program>.py` at any time, including during the slot's wait. The check's verdict holds only for the moment it is made, so the check has to be the last thing before the start.

**The code as it stands (bridge/cursor-bridge/bridge-run.py on branch task-029, the working tree's copy).** I checked each line number below against the file:
- `DRIVER_REFUSE` :106-107 is the refusal text, a module constant that ends with `\n`. `KINDS` :105. `HEAVY_KINDS = frozenset(("builder", "driver", "test"))` :114, so a driver run takes the slot.
- `_supervisor_file_ok(prog, folder)` :245-259 accepts a program only when it lies under `<folder>/run/supervisor`, `os.path.isfile` says it is a file, `os.stat(prog).st_nlink == 1`, and the link walk passes. A hard link has `st_nlink` 2, so it is refused.
- `def verify_driver_program_abs(abs_prog, folder):` :291-300 has the docstring `"""Re-check (c)-(e) on the absolute program path already placed in the command to start."""`. It returns `True` or `False`.
- `def _unlock_byte(fd):` :853-865 unlocks the slot's byte and swallows `OSError` itself, on both platforms.
- `acquire_heavy_slot(kind, run_id, limit, scale)` :902. It returns `"refused"`, `None` (not free), or a pair `(fd, waited)`.
- `main()` :1201. At :1290-1292, a driver's `cmd[1]` is set to the resolved absolute program `driver_prog`. `cmd, is_agent = resolve(cmd)` is :1293. `entry` (the log row) is built at :1307, and is written only by `write_log(folder, entry)`.
- The check before the wait, :1335-1337:
  ```python
      if kind == "driver" and len(cmd) >= 2 and not verify_driver_program_abs(cmd[1], folder):
          sys.stderr.write(DRIVER_REFUSE)
          return 125
  ```
  It writes no log row.
- The slot, :1339-1349. It ends with `slot_fd, entry["waited"] = slot_result[0], slot_result[1]`.
- The Windows branch, :1351-1375. `killer = None` is at :1351, `if sys.platform == "win32":` at :1352, `Job()` and `job.assign_self()` at :1354-1355, and `subprocess.Popen(...)` at :1363-1364.
- The other branch, :1376-1388. `subprocess.Popen(cmd, env=env, preexec_fn=os.setsid, creationflags=NO_WINDOW)` is at :1378.
- Both `except OSError` arms after `Popen` (:1365-1373 and :1379-1387) release the slot the same way:
  ```python
              if slot_fd is not None:
                  _unlock_byte(slot_fd)
                  try:
                      os.close(slot_fd)
                  except OSError:
                      pass
              return 125
  ```
- Nothing between :1349 and the two `Popen` calls touches the file system today, except the Windows Job's creation and assignment.
- `healthy` for a driver is set at :1418 (`kind == "driver" and rc in (0, 1)`), then written by `write_log` at :1420. A run that returns before `Popen` never reaches either.

**The test this fix must turn green.** It is `tests/test_bridge_run_slot.py::test_r040_driver_rechecked_after_the_wait` (:776-824), parametrized `swap` False and True. Today `[True]` fails and `[False]` passes, and after your fix both pass. Here is what it enforces. A lock-only holder takes the slot. A launcher started with `--limit 60 --kind driver -- python run/supervisor/task.py` passes the first check and prints `bridge-run: waiting`. With `swap=True`, the test replaces the program by a hard link to `outside.py` and asserts that `verify_driver_program_abs` now returns `False`. Then it frees the slot. It asserts five things: exit 125; a `bridge-run: refused - driver kind:` line on stderr; neither marker file written, so nothing ran; no log row in `run/launcher/runs.jsonl`; and a follow-up heavy run `--limit 5 -- <python> -c pass` that exits 0 without `waiting for the slot`. With `swap=False` the launcher exits 0 and the program inside `run/supervisor/` ran. Its docstring states the paragraph it enforces: "a driver run that waited for the slot checks its program again after the slot is taken. A program replaced during the wait by a hard link to a file outside run/supervisor/ is refused like the check before the wait (125, the driver refusal, no log row), never started, and the slot is free again; the twin whose program was not replaced runs it." Hard links are made with `os.link`. If they are not supported the case skips, but on NTFS they are supported.

**The tests that pass today and must keep passing.** These are every test in `tests/test_bridge_run_slot.py` and `tests/test_bridge_run_driver.py` (TASK-028's driver tests: the refusal before the wait, its texts, ceiling and health), and the rest of the suite.

**Platform facts you may rely on.** A process's byte-range lock (`msvcrt.locking` on Windows, `fcntl.flock` elsewhere) is released by the operating system when the process exits. So the launcher's own exit also frees the slot, a few milliseconds after `return 125`. This matters for mutation 3 below.

## Diagrams

None. The build plan's `Diagrams:` field for TASK-029 is `none`.

## Requirements

1. **A driver run's program is checked again after the slot is taken, immediately before the start, on both platforms.**
   - Keep the check before the wait (:1335-1337) as it is, so a driver that is already refused does not wait.
   - For `kind == "driver"`, call `verify_driver_program_abs(cmd[1], folder)` again after `acquire_heavy_slot` has returned the slot and before `subprocess.Popen`, on Windows and elsewhere alike. Placing it before the Windows Job is created is acceptable. No file-system step may sit between this second check and `Popen` beyond the ones that exist there now (the Job's creation and assignment on Windows).
   - When the second check returns `False`, do all of the following:
     - release the slot exactly as the `Popen`-failure path does: `_unlock_byte(slot_fd)`, then `os.close(slot_fd)` with its `OSError` swallowed, both under `if slot_fd is not None`;
     - write `DRIVER_REFUSE` to stderr (the constant itself, no new text);
     - return 125;
     - write no log row, as the refusal before the wait writes none, and so leave no healthy mark;
     - do not start the command.
   - When the second check returns `True`, the run goes on exactly as today.
2. **Nothing else changes.** Do not move the `slot taken` line or the record's publication, and change no message, constant, exit code, default or duration. Do not touch the module docstring or any other function's behaviour. Do not change the check before the wait or the two `Popen`-failure arms. Do not add a dependency or a launch.

## Acceptance criteria

- [ ] `tests/test_bridge_run_slot.py::test_r040_driver_rechecked_after_the_wait[True]` and `[False]` both pass on Windows, each with its own pytest summary line quoted in the report. The report also quotes the `[True]` failure it printed before your change.
- [ ] `python -m pytest tests/test_bridge_run_slot.py -q` passes, and `python -m pytest tests -q` passes. The report quotes each summary line as pytest printed it.
- [ ] The second check runs for a driver on both the Windows branch and the other branch. The report says, from reading the diff, why the non-Windows path is covered even though only Windows runs here.
- [ ] On a refusal after the wait, the slot is released (`_unlock_byte` then a guarded `os.close`), the text is `DRIVER_REFUSE`, the exit is 125, and `write_log` is not called.
- [ ] `git diff -- bridge/cursor-bridge/bridge-run.py` holds Requirement 1 and nothing else. Lines 1-88 (the module docstring) are byte-for-byte unchanged.
- [ ] `python tools/dump-cli.py --check` passes (the command reference stays current).
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py` prints `0 FAIL`.
- [ ] `git status --porcelain` shows no changed or new file outside `bridge/cursor-bridge/bridge-run.py`, `docs/BUILDER_NOTES.md` and `handoff/TASK-029-r4-report.md`.
- [ ] R-040 and R-039 (the part this round touches) are fully met, with no stand-in. The test that names them, `test_r040_driver_rechecked_after_the_wait`, is the supervisor's and is already present.

## Constraints

- Do not add dependencies. The program text is ASCII only, as the program says.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it. The only exception is temporary folders: pytest's `tmp_path` and `home_of_the_tests`, and, for a by-hand launcher run, a temporary home and launch folder that you create and remove.
- Change only `bridge/cursor-bridge/bridge-run.py`. Do not edit any test file, even where a test looks wrong to you. If the test cannot pass without editing it, or if it contradicts this brief, stop, leave the tree as it is, and report the test, its failure and why.
- If the brief, the rules or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall, such as a cause you found or a platform quirk that cost you a round: one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). Capturing output does not prevent the window. This round adds no launch and no `windowless: visible-ok` exemption.
- Never start a server, a watcher or a daemon that outlives a test. The tests stop every process they start in their own `finally`. Do not start any other process, except a by-hand launcher run that you wait for to its end.
- Do not refactor code outside Requirement 1, even if it looks wrong. Report it instead.
- Never run the product, a migration, a seed or a test against the owner's live data. Never run the launcher with the Workspace (or any real project) as its working folder. Never read, create or lock the real `~/.cursor-bridge/heavy.lock` or `heavy.lock.holder`. Never touch the real `~/.claude`. Any launcher run you make outside pytest sets `HOME` and `USERPROFILE` to a temporary folder.
- No value in this round is marked as the owner's. The figures (exit 125, `DRIVER_REFUSE`) are the existing code's.
- Follow existing conventions in the file: the `bridge-run: ` line prefix, refusal texts as module constants (`DRIVER_REFUSE`), and the slot's release as the `Popen`-failure arms write it.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff`, `git show` and `git log` only.
- No number is parsed in this round.
- An increment that starts a process meets every point of this checklist. The process is windowless. It is stopped in a `finally` or a fixture's teardown, and its whole tree with it. Nothing it started outlives the test or the command. Its output pipes are closed or drained. The tests already meet it, and your code adds no process.
- **Mutation check, by hand, in your own run.** Once the fix passes, apply each mutant below to `bridge-run.py` in place, one at a time. Run `python -m pytest "tests/test_bridge_run_slot.py::test_r040_driver_rechecked_after_the_wait" -q -p no:cacheprovider`, then restore the fixed code exactly, and confirm with `git diff` that it is restored. Write no mutation script, and leave nothing of it in the diff. The supervisor's driver runs after your run. For each mutant, report what you changed, which test case caught it (or that none did), and pytest's summary line.
  1. Remove the second check. Expected: `[True]` fails.
  2. Do the second check only on the non-Windows branch. Expected: `[True]` fails on Windows. Also, from reading the code, say what the mirror mutant (the check only on the Windows branch) would do on Linux.
  3. Refuse after the wait without releasing the slot: no `_unlock_byte` and no `os.close`. The supervisor expects the test's follow-up heavy run to wait, so the test fails. But the launcher exits right after `return 125`, and the operating system releases its lock at that exit (Context). So this mutant may survive. Report what you observed. If it survives, say so plainly and do not edit any test to catch it.
  4. Write a log row on that refusal (`write_log(folder, entry)` before `return 125`). Expected: `[True]` fails on the no-log-row assertion.
- Prefer reuse over new code (the existing `verify_driver_program_abs`, `_unlock_byte`, `DRIVER_REFUSE`), and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security requirement stated above.
- **Verification commands.** Run each from the Workspace folder (the folder you were started in), in this order:
  - Before your change, once: `python -m pytest "tests/test_bridge_run_slot.py::test_r040_driver_rechecked_after_the_wait" -q -p no:cacheprovider`. Expected: `[True]` fails and `[False]` passes.
  - After your change, the same command. Expected: both pass.
  - The slot file: `python -m pytest tests/test_bridge_run_slot.py -q`
  - The full suite: `python -m pytest tests -q`
  - The mutation check above, then the last two commands again once the code is restored.
  - The command reference: `python tools/dump-cli.py --check`
  - The windowless check: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py`
  - The diff: `git diff -- bridge/cursor-bridge/bridge-run.py`. Read it whole, and confirm it holds Requirement 1 and nothing else.
  - The tree: `git status --porcelain`
  - After the runs, on Windows: `tasklist /FI "IMAGENAME eq python.exe"`. Say whether any process the tests started is still running.

## Done

Your report is the file `handoff/TASK-029-r4-report.md`. Write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing of it is lost if your run ends early. Never paste a computer path or a user name into it. Write `<temporary folder>`, `<home>` or `<Workspace>` instead.

State only what you ran. For every run you report, quote pytest's own output as it printed it, at least the summary line. Do not round, summarise or reconstruct a figure. The supervisor and both reviewers re-run every command and check every claim, and a claim they cannot reproduce rejects the round.

When you finish, the report holds:
- a list of every file you changed, and only those (`git status` tells you);
- a one-paragraph summary of what you did;
- one sentence on how the change closes the gap between the check and the start (where the second check sits relative to `acquire_heavy_slot` and to each `Popen`);
- why the non-Windows branch is covered, from reading the code;
- the quoted output of each verification command, and the leftover-process check;
- the mutation list: each mutant, what caught it or that nothing did, and pytest's summary line, plus confirmation that the code was restored;
- a section headed exactly `Assumed, not verified`. List every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: that the Job's creation on Windows touches no file the second check depends on; that `os.link` on this volume produced `st_nlink` 2 as the test asserts; that the operating system frees the lock at exit before the follow-up run takes it. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
