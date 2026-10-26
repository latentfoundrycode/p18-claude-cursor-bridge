# TASK-031 round 5: the bound's kill cannot hang, a pipe holder outside the killed tree

## Objective

Fix the following confirmed defect - repair the named cause, nothing else.

Round 4 is past the owner's three-round review ceiling, and so is this round. Only the five blocking classes send work back: behaviour against the brief or the register, security, data integrity, a defeated safety mechanism, and a failing test. This round carries exactly one item. Its class is "a defeated safety mechanism": the per-mutant bound (S7 of `handoff/TASK-031.md`), which round 4's item 12 ("the bound's kill cannot hang") was meant to make safe. Every other finding is recorded in `docs/HARDENING.md` and is not yours to fix. `handoff/TASK-031.md`, `-r2.md`, `-r3.md` and `-r4.md` still govern everything this file does not change.

**Root cause, confirmed by the supervisor.** After the bound expires and the tree is killed, `run_process` closes `proc.stdout` and `proc.stderr` while `communicate`'s reader threads are still blocked reading them, so the close waits on the reader thread's lock until whatever holds the pipes exits.

**Evidence, as the supervisor reproduced it:**
- `bridge/cursor-bridge/mutation-run.py`, `run_process` (about lines 434-457): after the first `proc.communicate(timeout=timeout_sec)` times out, `kill_tree(proc)` runs, then `proc.communicate(timeout=30)`. When that also times out, the code calls `proc.stdout.close()` and `proc.stderr.close()`, then `proc.wait(timeout=30)`.
- A process outside the killed tree may still hold the pipes. On Windows that is a grandchild whose parent has exited, which `taskkill /T` does not reach. On POSIX it is a process in a session of its own, which `os.killpg` does not reach. Then the second communicate's reader threads stay blocked in their reads. `proc.stdout.close()` blocks behind them, because the reader thread holds the buffered file's lock. So `run_process` does not return until that process exits, and the bound is defeated.
- A probe with `faulthandler.dump_traceback_later(70)` showed the main thread at `mutation-run.py` line 451 (`proc.stdout.close()`), and both reader threads in `subprocess.py` `_readerthread`. That was 70 s after a 2 s bound. `run_process` had not returned after 150 s. The holder sleeps 600 s.
- Round 4's own test, `tests/test_mutation_run.py::test_r041_grandchild_holding_pipes_times_out`, did not reach this path. Its holder is a child of pytest, inside the killed tree.

**Reproduction test (the supervisor's; it fails today for this reason and must pass):** `tests/test_mutation_run_supervisor.py::test_task031_r4_item12_a_pipe_holder_outside_the_killed_tree_cannot_hold_the_run`. It loads `mutation-run.py` by path and calls `run_process` with a 2 s bound. The target's orphaned grandchild holds the target's pipes. The test requires a return with `timed=True` within 90 s.

Satisfies:
- R-041 (quoted whole in `handoff/TASK-031.md`). Here the clause is S7: each mutant's run is bounded, and at the bound the mutant is `error` (`timed out`), never a kill.

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- tests/test_mutation_run.py
- docs/cli-reference.json and docs/CLI_REFERENCE.md (only through `python tools/dump-cli.py`, and only if the parser's text changes)
- docs/BUILDER_NOTES.md
- handoff/TASK-031-r5-report.md

Do not modify anything else.

## Out of scope

- `tests/test_mutation_run_supervisor.py`: read and run it, never edit it. A test you believe wrong is reported with the reason, never changed or skipped. This covers the reproduction test.
- `tests/conftest.py`, `tests/test_dump_cli.py` and every other existing test file
- `bridge/cursor-bridge/MANIFEST.json` and every other file under `bridge/`. Never run `tools/make-manifest.py`.
- `run/supervisor/`
- Every finding not listed below, including the advisories the reviewers raised: they are recorded, not yours.
- The orphan's own lifetime. When the driver run ends, the launcher's Job object ends the orphan. A Job object inside `mutation-run.py` is not asked for.

## Context

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/mutation-run.py` by file path, on fixtures under `tmp_path`. `tests/conftest.py`'s autouse fixture `home_of_the_tests` sets `HOME` and `USERPROFILE` to a fresh temporary folder, so the scratch copy falls under that temporary home. Never run `mutation-run.py` with this Workspace or a real project as its working folder. Never touch the real `~/.cursor-bridge/` or `~/.claude/`.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force, and so is the frozen minimal-code rule (`bridge/cursor-bridge/minimal-code.snapshot.md`). This item touches one trust boundary: the scratch folder in the owner's home. The program writes and removes only its own `mutation-run-<id>/` subfolder. The copy under it holds the root `.env`, which holds local service passwords (KP-032), and the `.env` is never printed, logged or keyed.

**The code as it is (checked on this branch's working tree).**
- `kill_tree(proc)` (:418-431): on Windows it runs `taskkill /T /F /PID <pid>` windowless with `capture_output=True` and `timeout=30`. Elsewhere it runs `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)`, falling back to `proc.kill()`.
- `run_process(argv, env, cwd, timeout_sec)` (:434-457) returns `(returncode, out, err, timed)`, with `(None, out, err, True)` on a timeout. On POSIX it starts the run with `start_new_session=True`. Its callers are `run_mutant_tests`, the resolution check and the `--checkpoint` loop (:1133-1136). They read outcomes from the plugin's JSON results file, not from `out`, so empty output on a timeout changes no outcome. Keep the signature and the return shape.
- Mutant test runs start with `cwd=copy_root`, which is `mutation-run-<id>/tree`. A holder that the mutant's test starts therefore has its working folder inside the copy, unless it changes it.
- The copy is removed at :1242-1244 in a `finally`, with `shutil.rmtree(work_sub, ignore_errors=True)`. At the start of a run, :1096-1098 removes a leftover `mutation-run-<id>/` the same way, then `os.makedirs(work_sub, exist_ok=True)`. `run_main` (:1247-1261) maps `Refuse` to 2, `ResolutionTimeout` to 3, and any other exception to `mutation-run: internal error - ...` with exit 3.
- Requirement 9 of `handoff/TASK-031.md` defines the exit codes: 3 for an error, 1 for a survivor, 0, 4 in `--checkpoint` mode, and 2 for a refusal. An internal error is 3 too, but it is the wrong message for this case.

**A platform fact that bears on the means.** CPython's `Popen.communicate` behaves differently by platform. On Windows it reads each pipe in a daemon thread (`_readerthread`). A second `communicate` call after a `TimeoutExpired` joins the same threads again. On POSIX it reads with a selector in the calling thread. The blocking close is therefore the Windows mechanism. Both platforms must meet the requirement, because CI runs the suite on Windows and Ubuntu.

**This brief overrides one clause.** Requirement 4 of `handoff/TASK-031.md` says that after the tree is ended, "the pipes are then drained and closed". In the case this brief names, where the pipes are still held after the second timeout, that clause gives way to Requirement 1 below.

## Requirements

1. `run_process` returns timed out within the bound plus 90 s (taskkill's 30 s, the second communicate's 30 s and the process wait's 30 s at the most), whatever holds the pipes. It never closes or reads a file object a reader thread may be blocked on. It does not wait on the pipes again after the second timeout. The outcome is the mutant's `error (timed out)`, as today, and a timed-out resolution check still exits 3 naming the bound. You choose the means. One way: after the second timeout, leave `communicate`'s daemon reader threads to end on their own, return with empty output, and wait only on the process itself, with a bound.
2. Find out what happens to the copy's removal at the run's end while such a holder still runs with its working folder inside the copy. On Windows, a process's working folder cannot be removed. State the answer in your report: which parts of `mutation-run-<id>/` remain, whether the copied `.env` is among them, and what the next run of the same id does with the leftover. Make sure this case ends the run with the program's documented exit code, 3 for a timed-out mutant, and its normal summary, never `mutation-run: internal error - ...` from the removal. If that needs a code change, it is in scope. If you find it already holds, show it with a test in `tests/test_mutation_run.py`. Either way, add that test. A mutant's test starts a holder that outlives its parent, holds the pipes and has its working folder in the copy. The program must end within its bound plus 90 s, with exit 3 and `error (timed out)` in its summary, and with no `internal error` on stderr. The test ends the holder in its own `finally` or teardown, for example from a pid file the holder writes under `tmp_path` outside the copy, so the holder does not outlive the test. Its docstring names `R-041` and `TASK-031 S7`.

## Acceptance criteria

- [ ] `tests/test_mutation_run_supervisor.py::test_task031_r4_item12_a_pipe_holder_outside_the_killed_tree_cannot_hold_the_run` passes. `git diff --quiet -- tests/test_mutation_run_supervisor.py` holds.
- [ ] `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0` passes whole, each test within its ceiling.
- [ ] The cause is fixed at the mechanism the evidence points at. After the second timeout, no file object a reader thread may be blocked on is closed or read, and nothing waits on the pipes. This is never done by special-casing the test's fixture.
- [ ] The new test of Requirement 2 passes, and the report states what remains of the copy in that case.
- [ ] `python tools/dump-cli.py --check` exits 0. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py` prints `0 FAIL`. The program is ASCII only.
- [ ] `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider` passes.
- [ ] `git status --porcelain` shows no changed or new file outside Scope.
- [ ] `handoff/TASK-031-r5-report.md` exists, with its `Assumed, not verified` section.

## Constraints

Every constraint of the four earlier briefs holds. There is no by-hand mutation in this round: the supervisor's driver runs after you. Write no mutation script.

This round adds the following:
- Do not fix by suppressing the symptom. That rules out a retry, a broad `try/except`, a widened tolerance, an added `sleep`, a longer or removed bound, and a check that hides a wrong value. A `try/except` that swallows the removal's failure counts as a broad one unless it is limited to the named case and the report says so.
- Do not edit the reproduction test or any other test in `tests/test_mutation_run_supervisor.py`.
- Do not leave any `DEBUG-BUG-` line, `faulthandler` probe or stray print in the program or the tests.
- **If you believe the real cause is different from the one named, stop, do not change code, and report why in your summary.** The supervisor will re-diagnose.
- Every process your code or your test starts is windowless (`creationflags=subprocess.CREATE_NO_WINDOW`, `0` elsewhere), respecting the scan of `tests/test_tests_windowless.py` described in `handoff/TASK-031.md`. Nothing it starts outlives the test, and its pipes are closed or drained. The orphan of Requirement 2's test is ended by the test itself.
- Do not read or write any file outside this workspace, except pytest's `tmp_path` and the tests' temporary home.
- If the brief, the rules or the tooling got in your way, append one dated line to `docs/BUILDER_NOTES.md`. Do the same for anything you learned about a defect or a pitfall. In any Markdown you write, one paragraph is one line.
- Only `git status`, `git diff`, `git show` and `git log` are yours to run in this Workspace.

## Verification commands

Run each from the Workspace folder, in this order:
1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0`
2. `python tools/dump-cli.py --check`
3. `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider`
4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`
5. `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"`
6. `git status --porcelain`

## Done

Your report is the file `handoff/TASK-031-r5-report.md`. Write it as you go. Never paste a computer path or a user name into it. State only what you ran, quoting pytest's own output, at least its summary line, for every run. Do not repeat a figure from an earlier round's report.

The report holds:
- the files you changed;
- one paragraph on what you did;
- one sentence stating how the change addresses the named cause;
- Requirement 2's answer: what remains of `mutation-run-<id>/` when a holder's working folder is inside it, whether the copied `.env` remains, what the next run of the same id does, and the test that holds it;
- the quoted output of each verification command, including the reproduction test's line from `-rA` and its duration;
- a section headed exactly `Assumed, not verified`, one item per line (what you assumed · why · what would confirm it). Name at least:
  - what becomes of the abandoned reader threads and the open pipe handles when the holder is still alive as `mutation-run.py` exits;
  - whether the POSIX path behaves as the Windows one, if you could not run it there.

Your last message is the summary and the report file's path, and nothing follows it.
