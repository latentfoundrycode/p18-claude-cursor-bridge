# TASK-029, round 3: One heavy job at a time: the launcher's machine-wide slot (code-only fixes)

## Objective

This is round 3 of TASK-029, and the last full review round under the owner's three-round ceiling (Context). It is a code-only round. `handoff/TASK-029.md` (round 1) and `handoff/TASK-029-r2.md` (round 2) stay in force: their Requirements stand, and this brief corrects them in place. Where they differ, this brief governs. Round 2's code is the commit `8460ea6` on this branch. Both reviews of round 2 rejected it. A holder record that is not UTF-8, is nested deeply, or holds a 400-digit `created` crashes a waiter with a traceback that prints the program's absolute path. Off Windows, a FIFO at the record's path blocks the waiter forever, and a link to `/dev/zero` is read without end. `--kind review` lets a named test suite run without the slot. Publishing the record can raise after `slot taken`. Off Windows, a link at `heavy.lock` is followed and its target's mode is changed. A Windows process that exited with code 259 reads as alive. The supervisor has already written every test for this round, and they are in the working tree. Against today's code exactly 8 of them fail, and two of those 8 run only off Windows. You make them pass by changing `bridge/cursor-bridge/bridge-run.py` only. You change no test file.

Satisfies: R-040: One heavy job at a time on the computer: a builder run, a test suite and a mutation run each hold one machine-wide slot in the launcher while they run (an exclusive lock on a file under the bridge's state folder in the owner's home, `~/.cursor-bridge/`, where the agent home already lives), which every session and the owner's own programs see alike, released by the operating system the instant the holder ends; a second heavy run waits for it, saying what it waits for, as long as the holder's own ceiling allows and never counting the wait against its own; a review and a CI watch take none.

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- docs/BUILDER_NOTES.md
- handoff/TASK-029-r3-report.md

Do not modify anything else.

## Out of scope

- .env and anything under secrets/
- CI configuration (`.github/`, `.githooks/`)
- docs/ and handoff/, except the files the Scope section names. The supervisor regenerates `docs/cli-reference.json`, `docs/CLI_REFERENCE.md` and `bridge/cursor-bridge/MANIFEST.json` after your run. Do not run `python tools/dump-cli.py` or `tools/make-manifest.py`.
- Every test file, in particular `tests/test_bridge_run_slot.py`, `tests/test_a4_followups.py`, `tests/test_bridge_run.py`, `tests/test_loop_guard.py` and `tests/conftest.py`. The supervisor wrote this round's tests. They are fixed, and you may not edit, add, rename, skip or mark any test.
- A mutation driver, a mutation script or a mutation table. The supervisor's driver runs after your run. Do not mutate the code and do not report mutants.
- `bridge/cursor-bridge/loop-guard.py`, `bridge_env.py`, `bridge-stop.py`, `VERSION` and every other file under `bridge/`.
- The module docstring of `bridge-run.py` (lines 1-88). Leave it unchanged. It stays true after this round, because "What it accepts" already names Review B as a `cursor-agent` command with `--kind review` and lists 125 as "refused or could not start". So the command reference stays current.
- The items the supervisor recorded and did not take, in `docs/HARDENING.md` under "TASK-029 (round 2's reviews; recorded, not taken)". Do not do any of them: (1) tightening the mode of an existing `~/.cursor-bridge/` (`os.makedirs(mode=0o700)` sets the mode only when it creates the folder; leave it so); (2) one process handle for both liveness and creation time (the two `OpenProcess` calls in `process_alive` and `process_creation_epoch` stay two); (3) the bound's clock conversion (`deadline_mono = wait_mono + (bound_wall - wait_wall)` at :944 stays as it is); (4) Linux `btime` drift in `process_creation_epoch`.
- The POSIX limitation recorded in round 1 (`docs/HARDENING.md`, "TASK-029 (round 1's reviews; recorded, not taken)"). Do not pass the lock descriptor to the command (`pass_fds`), and do not change how the command's session or process group is made.
- Done when (e) of the build plan (a wait of more than thirty minutes). It stays the supervisor's. Do not start any run that waits for minutes.

## Context

**The round ceiling.** This is the last full review round. The owner's decision is in `docs/INVENTORY.md`, Decisions, the 2026-10-25 row ("The three-round review ceiling ... applies by hand from 2026-10-25"). After a review's third round, only the five blocking classes send the work back, and every other finding goes to `docs/HARDENING.md`. So this round has to close every ruling below completely. No round 4 exists to finish a half-done fix.

**What your report is checked against.** Round 2's report claimed six mutant kills, and the supervisor's driver disproved them. It also gave test durations that were false. The supervisor's driver and both reviewers check every claim in your report against a run of their own. Report only what you ran, and quote pytest's own output for it.

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/bridge-run.py` by file path. `tests/conftest.py`'s autouse fixture `home_of_the_tests` gives every test a fresh temporary `HOME`/`USERPROFILE`. The owner's real `~/.cursor-bridge/heavy.lock` and its record are never read, created or locked.

**Security context.** ASVS level 2 (INVENTORY, Decisions: "The builder's secure-coding rule is ASVS level 2"). `.cursor/rules/secure-coding.mdc` is in force for you. The trust boundaries:
- (1) The record `~/.cursor-bridge/heavy.lock.holder` is data from outside. Any program of the owner's account can write it, as any kind of file. Whatever it holds must not crash, block or exhaust the launcher, and must not put a raw control character on stderr. The lock decides who holds the slot, never the record.
- (2) The caller supplies `--kind`, and it must not let a heavy command skip the slot.
- (3) No traceback may escape the slot code, because a traceback prints the program's absolute path, and the installed copy's path holds the owner's user name. Messages name the lock as `~/.cursor-bridge/heavy.lock`.
- (4) Off Windows, a link planted in `~/.cursor-bridge/` is never followed, either by the lock's open or by the record's write.

**The code as it stands (bridge/cursor-bridge/bridge-run.py at 8460ea6; the working tree's copy is that commit's).** I checked each line number below against the file:
- Constants at :114-124. `HEAVY_KINDS` :114, `SLOT_GRACE` :115, `SLOT_CLOCK_SKEW` :118, `SLOT_LIMIT_MAX` :119, `PID_MAX` :120, `WATCH_ONLY_REFUSE = ("bridge-run: refused - a watch run is only a gh pr checks command\n")` :124.
- `head_of(argv)` :144. `kind_of(argv)` :337 returns `"builder"` for `cursor-agent`, `"watch"` for `gh pr checks`, `"test"` for a `named_suite`, and `None` otherwise.
- `process_alive(pid)` :625-661. On Windows it opens with `0x1000 | 0x00100000` (:638), then asks `GetExitCodeProcess` (:632-633 declared, :643-646 used, `259` reads alive), then `WaitForSingleObject(handle, 0) == 258` (:647), and closes the handle in a `finally` (:650-651). The POSIX branch is :652-661.
- `process_creation_epoch(pid)` :664-706.
- `_slot_start_epoch(start)` :709-724.
- `read_holder_record(holder_path)` :727-770. It reads with `open(holder_path, encoding="utf-8")` and `f.read()`, catching `OSError` only (:729-733), so a `UnicodeDecodeError` escapes. It calls `json.loads(raw)` catching `ValueError` only (:734-737), so a `RecursionError` escapes. Its `created` check calls `float(created)` catching `(TypeError, ValueError)` only (:755-761), so a 400-digit integer's `OverflowError` escapes. It returns `{"kind", "run_id", "pid", "created", "start", "limit"}` (:770).
- `run_id_epoch(run_id)` :773-783. Nothing calls it: a search of every `.py` file in the Workspace finds only its definition.
- `holder_end_time` :786.
- `publish_holder_record(holder_path, record)` :798-820. `os.makedirs` (:800) and `tempfile.mkstemp(dir=folder, prefix=".heavy.holder.", suffix=".tmp")` (:802) sit outside any `try`. The mkstemp descriptor is closed (:803-806) and the name reopened with `open(tmp, "w", ...)` (:809). Five attempts of write plus `os.replace` with `time.sleep(0.02)` between them (:807-814). Then `os.remove(tmp)` and the one note line `bridge-run: note - could not publish the slot holder record` (:815-820). It returns `True` or `False`.
- `_try_lock_byte` :823.
- `_open_heavy_lock(lock_path, state_dir)` :877-887. On Windows it is `os.open(lock_path, os.O_RDWR | os.O_CREAT)`. Off Windows it is `os.makedirs(state_dir, mode=0o700, exist_ok=True)`, then `os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)` (which follows a link), then `os.chmod(lock_path, 0o600)` (:884, by path, which also follows a link).
- `acquire_heavy_slot(kind, run_id, limit, scale)` :890-960. An `OSError` from `_open_heavy_lock` prints `bridge-run: refused - ~/.cursor-bridge/heavy.lock (<class>)` and returns `"refused"` (:904-908), and `main` then exits 125 (:1328-1329). The record is published at :929, and its return value is ignored. The waiter calls `read_holder_record` once per poll (:935).
- `main()` :1189. The `--kind review` family check is at :1236-1240 (`review_family_refusal` returns `None` for any command that is not `cursor-agent`). `bridge-run: started` is printed at :1254. The limit's cap refusal is :1268-1270. The watch refusal is :1271-1273 (`if kind == "watch" and kind_of(cmd) != "watch":`). The slot is :1324-1334.
- `tests/test_bridge_run.py:206` runs `--kind review` with `sys.executable -c "print(1)"` under `BRIDGE_RUN_ALLOW_ANY=1`, and `kind_of` names no kind for that command. It must keep passing, and so must `tests/test_bridge_run.py:193-195` (the cap refusal of a `--kind watch` helper comes before the watch refusal).

**The tests that fail against today's code, and why.** All are in `tests/test_bridge_run_slot.py`:
- `test_r040_untrusted_records_in_process` (:293). Today it raises `RecursionError` on the planted `"[" * 100000` first. It also plants a `created` that is a 400-digit integer, a record padded with 8,192 spaces past the 4,096-byte cap (`json.loads` accepts trailing whitespace, so only the size cap refuses it), a UTF-16 encoding of the well-formed record, the bytes `ff fe 7b 00 7d 00`, and ten `0x80` bytes. The test asserts that each reads as `None` and that nothing is raised.
- `test_r040_exit_code_259_reads_as_dead` (:371). A child that exited with code 259 still reads live on Windows. The test holds its `Popen`, so the process's handle stays open, and `OpenProcess` and `GetProcessTimes` both still succeed.
- `test_r040_untrusted_records_by_launch` (:438), in three cases. `[deep:100000]` and `[hex:fffe7b007d00]` each get a parameter id from pytest; the 400-digit-`created` case is the last parameter. Each launches a waiter under a helper that holds the lock and plants the record, and asserts exit 123, no `Traceback`, no control character, and only `held by unknown` waiting lines.
- `test_r040_review_refuses_a_heavy_command[False]` and `[True]` (:530). `--kind review` with `python -m pytest --version`, `pytest -q` and `gh pr checks 1`, both with and without `BRIDGE_RUN_ALLOW_ANY`. Each must exit 125 with the review refusal, the command must never start, and there must be no `heavy.lock`. `--limit 99999 --kind review` must still get the cap refusal first.
- `test_r040_publication_failure_is_a_note` (:938). The record's folder path is an existing file. The test expects `False` and exactly one note line. Today `os.makedirs` raises.
- Off Windows only (skipped on Windows): `test_r040_special_file_records_posix` (:412) and `test_r040_lock_link_not_followed_posix` (:817). The first plants a FIFO and a link to `/dev/zero` as the record, and reads each in a child that must print `None` within 4 s. The second puts a link at `heavy.lock` to a 0o644 file, expects exit 125 with the refusal line and no marker, and expects the target's mode to stay 0o644.

**The tests that pass today and must keep passing.** These pass now, and Requirements 3 to 5 must not break them: `test_r040_record_published_while_read` (:893: 40 publications under a concurrent reader, all `True`, and the record the only file left in the folder), `test_r040_unpublishable_record_keeps_the_slot` (:949), `test_r040_posix_lock_modes` (:1012), `test_r040_review_and_watch_skip_slot` (:486), `test_r040_lock_folder_refused` (:801), and every other test in the file.

**Platform facts you may rely on.**
- `json.loads` given `bytes` detects UTF-16 and UTF-32 on its own. Given bytes, the UTF-16 record above would therefore parse. The record is parsed from a `str` decoded as strict UTF-8.
- `UnicodeDecodeError` is a `ValueError`. `RecursionError`, `MemoryError` and `OverflowError` are not. `float()` of an integer of 400 digits raises `OverflowError`.
- On POSIX, `os.open` of a FIFO with `O_RDONLY | O_NONBLOCK` returns at once even with no writer. Without `O_NONBLOCK` it blocks until a writer appears. `O_NOFOLLOW` makes an open whose last component is a symbolic link fail with `OSError` (`ELOOP`). `os.fstat(fd).st_mode` with `stat.S_ISREG` tells a regular file from a FIFO, a device or a folder. `os.fchmod` exists only off Windows.
- On Windows, `os.O_NONBLOCK`, `os.O_NOFOLLOW` and `os.fchmod` do not exist, so use `getattr(os, name, 0)` for the flags. A descriptor from `os.open` opens in the C runtime's text mode unless `os.O_BINARY` is given, so add `getattr(os, "O_BINARY", 0)` to the record's open. `os.open` of a folder fails with `PermissionError`.
- `os.fdopen(fd, ...)` takes ownership of the descriptor, and closing the file object closes it.
- `WaitForSingleObject(handle, 0)` returns `WAIT_TIMEOUT` (258) for a process that is still running, `WAIT_OBJECT_0` (0) for one that has exited, and `WAIT_FAILED` (0xFFFFFFFF) on error. It needs `SYNCHRONIZE` (0x00100000) in the access mask, which :638 already has.

**Rule in force.** `.cursor/rules/secure-coding.mdc` (above). The frozen `minimal-code.mdc` is also in force.

## Diagrams

None. The build plan's `Diagrams:` field for TASK-029 is `none`.

## Requirements

These are the supervisor's six rulings. They are settled; do not reopen them. Each names the tests that prove it.

1. **The record's read never raises and never blocks.**
   - `read_holder_record` opens the record without following a link. Off Windows it also opens without blocking: `os.O_RDONLY | O_NONBLOCK | O_NOFOLLOW` where they exist, each via `getattr(os, ..., 0)`, plus `O_BINARY` where it exists (Context).
   - It refuses anything `os.fstat` does not call a regular file.
   - It reads at most 4,097 bytes. A record of more than 4,096 bytes is no record.
   - It decodes the bytes as strict UTF-8 inside the guarded block and parses the resulting `str` with `json.loads`.
   - `OSError`, `ValueError` (`UnicodeDecodeError` included), `RecursionError`, `MemoryError` and `OverflowError` all mean no record (`None`). This includes `float()` of a 400-digit integer at the `created` check, and any of these errors raised anywhere between the open and the returned record.
   - The descriptor is closed on every path.
   - The validation rules of round 2's Requirement 5 are otherwise unchanged.
   - Tests: `test_r040_untrusted_records_in_process`, `test_r040_untrusted_records_by_launch` (all its cases), `test_r040_special_file_records_posix`.
2. **`--kind review` carries only cursor-agent.**
   - A run given `--kind review` whose command `kind_of` names a kind (a named test suite, a `gh pr checks` command), and whose `head_of` is not `cursor-agent`, is refused with exit 125 and exactly the line `bridge-run: refused - a review run is only a cursor-agent command`.
   - That line is a module constant beside `WATCH_ONLY_REFUSE`, written the same way (with its newline).
   - The refusal sits with the watch refusal: after the limit's cap refusal and before the slot, whatever `BRIDGE_RUN_ALLOW_ANY` says.
   - A helper that `kind_of` names no kind for (`python -c ...` under `BRIDGE_RUN_ALLOW_ANY=1`, as `tests/test_bridge_run.py:206` and the slot tests run) still runs.
   - Tests: `test_r040_review_refuses_a_heavy_command[False]` and `[True]`; `test_r040_review_and_watch_skip_slot` and `tests/test_bridge_run.py` unchanged and passing.
3. **Publication never raises.**
   - `publish_holder_record` makes the folder and the temporary file (`tempfile.mkstemp` in the record's folder) inside its failure handling.
   - It writes the record through the mkstemp descriptor (`os.fdopen`) and never reopens the temporary file by name. Then it calls `os.replace` with the existing retries (five attempts, 0.02 s apart).
   - Any `OSError` at any step does three things: it removes the temporary file if one was made, prints the existing note line `bridge-run: note - could not publish the slot holder record` once, and returns `False`.
   - The caller keeps the slot and runs its command, as now.
   - On success no temporary file is left, and it returns `True`.
   - Tests: `test_r040_publication_failure_is_a_note`, `test_r040_unpublishable_record_keeps_the_slot`, `test_r040_record_published_while_read`.
4. **The lock file is opened without following a link off Windows.**
   - `_open_heavy_lock` opens with `O_NOFOLLOW` (via `getattr`, 0 elsewhere) and sets the mode with `os.fchmod(fd, 0o600)`, never `os.chmod` by path.
   - A link at `heavy.lock` makes the open fail and takes the existing path: `bridge-run: refused - ~/.cursor-bridge/heavy.lock (<class>)`, exit 125, the command never started.
   - On Windows the open is unchanged.
   - Tests: `test_r040_lock_link_not_followed_posix`, `test_r040_posix_lock_modes`, `test_r040_lock_folder_refused`.
5. **Windows liveness by WaitForSingleObject alone.**
   - `process_alive` on Windows says alive only when `WaitForSingleObject(handle, 0)` returns `WAIT_TIMEOUT` (258).
   - `GetExitCodeProcess` is no longer consulted or declared, because by it a process that exited with code 259 reads as running.
   - Every handle is still closed on every path. The access mask and the POSIX branch are unchanged.
   - Test: `test_r040_exit_code_259_reads_as_dead`.
6. **`run_id_epoch`, which nothing calls, is removed.**

Nothing else in `bridge-run.py` changes. This round adds no new line and no exit code other than Requirement 2's, and it changes no message, constant, default or duration.

## Acceptance criteria

- [ ] On Windows, these tests pass, each by its own run: `test_r040_untrusted_records_in_process`, `test_r040_exit_code_259_reads_as_dead`, `test_r040_untrusted_records_by_launch[deep:100000]`, `test_r040_untrusted_records_by_launch[hex:fffe7b007d00]`, the `test_r040_untrusted_records_by_launch` case whose `created` is 400 digits, `test_r040_review_refuses_a_heavy_command[False]` and `[True]`, and `test_r040_publication_failure_is_a_note`.
- [ ] `test_r040_special_file_records_posix` and `test_r040_lock_link_not_followed_posix` skip on Windows. The report says, from reading the code, why each would pass on Linux (the open flags, the `fstat` check, the refusal path).
- [ ] `python -m pytest tests/test_bridge_run_slot.py tests/test_a4_followups.py tests/test_bridge_run.py tests/test_loop_guard.py -q -p no:cacheprovider --durations=0` passes. Every test of `tests/test_bridge_run_slot.py` takes under ten seconds by its durations lines, and the report quotes those lines and the summary line as pytest printed them.
- [ ] `git status --porcelain` shows no changed or new file outside `bridge/cursor-bridge/bridge-run.py`, `docs/BUILDER_NOTES.md` and `handoff/TASK-029-r3-report.md`, apart from the supervisor's uncommitted changes that were already there when you started (`docs/HARDENING.md`, `tests/test_a4_followups.py`, `tests/test_bridge_run_slot.py`). Leave those as you found them.
- [ ] `bridge-run.py` holds no `GetExitCodeProcess`, no `run_id_epoch`, no `os.chmod(` in `_open_heavy_lock`, and no reopening of the temporary file by name. Its module docstring (lines 1-88) is byte-for-byte unchanged.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py` prints `0 FAIL`.
- [ ] R-040 is fully met in this round's part (Requirements 1 to 6), with no stand-in. The tests that name R-040 are the supervisor's, already present.

## Constraints

- Do not add dependencies. The program text is ASCII only, as the program says.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it. The only exception is the tests' temporary folders and temporary home, which come from pytest's `tmp_path` and `home_of_the_tests`.
- Change only `bridge/cursor-bridge/bridge-run.py`. Do not edit any test file, even where a test looks wrong to you. If a test cannot pass without editing it, or contradicts this brief, stop, leave the tree as it is, and report the test, its failure and why.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall, such as a cause you found or a platform quirk that cost you a round: one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). Capturing output does not prevent the window. This round adds no launch and no `windowless: visible-ok` exemption.
- Never start a server, a watcher or a daemon that outlives a test. Every process the tests start is stopped in its own `finally`; do not start any other.
- Do not refactor code outside the six Requirements, even if it looks wrong. Report it instead.
- Never run the product, a migration, a seed or a test against the owner's live data. Never run the launcher with the Workspace (or any real project) as its working folder. Never read, create or lock the real `~/.cursor-bridge/heavy.lock` or `heavy.lock.holder`, and never touch the real `~/.claude`. Run the launcher only through the tests named below.
- No value in this round is marked as the owner's. The figures (4,096 and 4,097 bytes, 0o600, 258, exit 125, five attempts 0.02 s apart) are this brief's or the existing code's.
- Follow existing conventions in the file: the `bridge-run: ` line prefix, the `bridge-run: refused - ` and `bridge-run: note - ` forms, refusal texts as module constants (as `WATCH_ONLY_REFUSE`, `DRIVER_REFUSE`), and Windows API calls through `ctypes` with declared `restype`/`argtypes`.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff`, `git show` and `git log` only.
- Numbers from the record are parsed with `json` (and checked by the existing type and range rules), never by slicing or splitting a string. The units and ranges are round 2's Requirement 5, unchanged. The record's size cap is 4,096 bytes, and a larger file is no record.
- An increment that starts a process meets every point of this checklist. The process is windowless. It is stopped in a `finally` or a fixture's teardown, and its whole tree with it. Nothing it started outlives the test or the command. Its output pipes are closed or drained. The tests already meet it; your code adds no process.
- No mutation testing in this round. Do not mutate the code, write no mutation script, and report no mutant. The supervisor's driver runs after your run.
- Prefer reuse over new code (the standard library's `os`, `stat`, `tempfile`, `json`, and the existing helpers), and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security requirement stated above.
- Verification commands. Run each from the Workspace folder (the folder you were started in), in this order, once your work is done:
  - The failing tests first: `python -m pytest tests/test_bridge_run_slot.py -q -p no:cacheprovider -k "untrusted_records or exit_code_259 or review_refuses or publication_failure or special_file or lock_link"`
  - The listed files with their durations: `python -m pytest tests/test_bridge_run_slot.py tests/test_a4_followups.py tests/test_bridge_run.py tests/test_loop_guard.py -q -p no:cacheprovider --durations=0`. This must pass.
  - The windowless check: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py`
  - The diff: `git diff -- bridge/cursor-bridge/bridge-run.py`. Read it whole, and confirm it holds Requirements 1 to 6 and nothing else.
  - The tree: `git status --porcelain`
  - After the runs, on Windows: `tasklist /FI "IMAGENAME eq python.exe"`. Say whether any process the tests started is still running.
  - `python tools/dump-cli.py --check` and the manifest are the supervisor's. Do not run them.

## Done

Your report is the file `handoff/TASK-029-r3-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do), so that nothing of it is lost when your run ends early. Never paste a computer path or a user name into it. Write `<temporary folder>`, `<home>` or `<Workspace>` instead.

State only what you ran. For every run you report, quote pytest's own output as it printed it: the summary line and, for the durations run, the durations lines of `tests/test_bridge_run_slot.py`. Do not round, summarise or reconstruct a figure. The supervisor's driver and both reviewers re-run every command and check every claim. A claim they cannot reproduce rejects the round, and this is the last full round.

When you finish, the report holds:
- a list of every file you changed (and only those; `git status` tells you);
- a one-paragraph summary of what you did;
- for each of Requirements 1 to 6, the function(s) changed and the test(s) that prove it;
- for the two POSIX-only tests, why each passes on Linux, from reading the code (they skip here);
- the quoted output of each verification command, and the leftover-process check;
- a section headed exactly `Assumed, not verified`. List every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: how `O_NONBLOCK` affects a later read of a regular file; whether a single `os.read` returns the whole of a regular file up to the count asked; how `os.replace` behaves on Linux under a concurrent reader; a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
