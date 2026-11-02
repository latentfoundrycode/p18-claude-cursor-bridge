# TASK-043: BUG-039, the review guard's four sites (the early flags void the launch; the void during the run; premerge's git call through the helper; the re-snapshot keeps the flag)

## Objective
Fix the following confirmed defect — repair the named cause, nothing else. The defect has four sites in one program, `bridge/cursor-bridge/review-guard.py`, each its own confirmed cause: a round flagged GATE-INTEGRITY was spent or admitted where R-042 says a flagged round spends nothing, and one git command of the guard ran with the file monitor on. The causes, their evidence and their reproduction tests are below, copied from `docs/debug/BUG-039.md`, read from the code at 67e79b9. No instrumentation round is needed.

**Site 1: four early GATE-INTEGRITY returns never void the launch.**
- Root cause: `cmd_verify` returns 1 at four places without calling `record_flagged_launch`.
- Evidence: the four returns are the snapshot rewritten (`snapshot_rewritten`), `.git/config` or a hook changed (`if flags:` before any git command), the branch held in another worktree (`held_elsewhere`), the branch not put back (`now_on != snap["branch"]`). Only the flags at the end of the function call it. `err_counts_as_reply` then counts the exit 0 at the next snapshot, which is refused `round N is reviewed`.
- Reproduction tests in `tests/test_bug039.py`: `test_bug039_site1_a_flag_before_any_git_command_voids_the_launch` (three cases), `test_bug039_site1_the_branch_held_in_another_worktree_voids_the_launch`, `test_bug039_site1_the_branch_not_put_back_voids_the_launch`. Negative cases: `test_bug039_site1_negative_no_path_clears_a_recorded_flag` and `test_bug039_site1_negative_a_snapshot_rewritten_to_any_shape_stays_a_clean_flag` (Requirement 8), an invariant that passes before the fix too, which you keep green.

**Site 2: a flag raised while the run still goes on leaves its launch unvoided, and a later clean verify admits it. Two lines of cause, two parts of the fix.**
- Root cause, first line: `record_flagged_launch` returns on `exit_code != 0`, and an `.err` with no exit line reads `None`, so nothing is recorded while the run goes on.
- Root cause, second line: the end of `cmd_verify` writes `reply` 0 and the verified mark for any launch with exit 0 at or after the snapshot, without reading `flagged_launch`, so even a recorded void does not stop a clean `verify`.
- Evidence: `verify` during the run flags GATE-INTEGRITY and repairs what it found; the run then exits 0; a second `verify` finds nothing left to flag, writes `reply` 0 and a mark `premerge` accepts: a flagged review reaches the merge.
- Reproduction test: `test_bug039_site2_a_flag_during_the_run_voids_the_launch_that_later_exits_0`. Negative case: `test_bug039_site2_negative_no_path_admits_a_flagged_launch`.

**Site 3: `premerge`'s git call bypasses the helper.**
- Root cause: `cmd_premerge` calls `subprocess.run(["git", "-c", "core.hooksPath=" + ..., "merge-base", "--is-ancestor", ...])` directly, not `_git_proc`, so it is the one git command of the guard run without `core.fsmonitor=false`.
- Evidence: `review-guard.py` line 1080 at 67e79b9. The caller reads the return code, and `run_git` raises on a non-zero exit, so the helper to use is `_git_proc`, not `run_git`.
- Reproduction tests: `test_bug039_site3_every_git_command_of_premerge_runs_with_both_switches`, `test_bug039_site3_no_git_call_of_the_guard_bypasses_the_helper`. Negative case: `test_bug039_site3_negative_premerge_runs_no_planted_hook_or_monitor`, an invariant that passes before the fix too (`merge-base` reads no index), which you keep green.

**Site 4: a re-snapshot drops the flag.**
- Root cause: `cmd_snapshot` rebuilds the round's entry keeping `reply`, `lift`, `lift_line` and `time`, and not `flagged_launch`.
- Evidence: a flagged round taken again on the same tree counts the flagged launch's exit 0 as its reply, so its next snapshot on a changed tree is refused as reviewed (found by Review B of PR #116, reproduced on a temporary repository).
- Reproduction test: `test_bug039_site4_a_resnapshot_keeps_the_flag`. Negative case: `test_bug039_site4_negative_a_resnapshot_counts_no_reply_on_either_tree` (same tree, changed tree).

Satisfies: R-042 — the code gate has a round ceiling held by programs, and a flagged round (GATE-INTEGRITY) spends nothing whichever of `verify`'s checks flagged it and whenever, a flag raised while the Review B run still goes on included, the void recorded by the launch's start time whatever its exit so far. R-055 — the minimum set of diagrams is drawn as built and enforced; D-003's three deviations and D-004's second are fixed by BUG-039 (this brief is the code side; the diagram files and the deviations list are the supervisor's).

## Scope
One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.
Files and directories you may create or modify:
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-043-r1-report.md

Do not modify anything else. `tests/test_bug039.py` is the reproduction test file: you read it and run it, and you never edit it. `MANIFEST.json`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running their generators (Requirement 9); they are never edited by hand.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names
- every test file under tests/, `tests/test_bug039.py` included
- `docs/debug/BUG-039.md`, every file under `docs/diagrams/` (`docs/diagrams/DEVIATIONS.md` included), `docs/BUILD_PLAN.md` and `docs/REQUIREMENTS.md`: the supervisor's records, updated by the supervisor
- `bridge/cursor-bridge/VERSION` (its content stays `2026.10.30d`) and `bridge/cursor-bridge/CHANGELOG.md`
- `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`
- every part of `review-guard.py` other than the flagged-round handling named in Requirements 1 to 7

## Context
All paths are relative to the Workspace root, the folder you were started in.

**Development data:** the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet. For this task that means: the guard is exercised only by the tests, each on a temporary git repository they create, with `BRIDGE_REVIEW_HASHES` pointed at a temporary folder by `tests/conftest.py`. Never run `review-guard.py snapshot`, `verify` or `premerge` in this Workspace itself: it would write to this repository's `.git/bridge/` and to the owner's `~/.cursor-bridge/`.

**Fixed points of the fix.** `tests/test_bug039.py` calls these names, and you may not edit it, so the fix keeps them exactly:
- `record_flagged_launch`: the module-level function that records the void. Its signature today, kept: `def record_flagged_launch(common, root, nnn, snap):`
- `flagged_launch`: the round entry's key in `<git common dir>/bridge/rounds-<ID>.json`, holding the voided launch's start time as `launch_info` reads it.
- `_git_proc`: the helper, and the one call site of git in the program. Signature today, kept: `def _git_proc(args, root, common):`. It returns the `subprocess.run` result and runs `["git", "-c", "core.hooksPath=" + no_hooks_dir(common), "-c", "core.fsmonitor=false"] + list(args)`. `test_bug039_site3_no_git_call_of_the_guard_bypasses_the_helper` walks the program's syntax tree: exactly one `subprocess.*` call inside a function named `_git_proc`, and every other `subprocess.*` call names a literal program that is not git.

**Functions you will read, all in `bridge/cursor-bridge/review-guard.py`:**
- `launch_info(err_path)` returns `(launch time, exit code)` from `run/review/REVIEW-<nnn>.err`: the launcher's first line `bridge-run: started <UTC>Z` (the time returned without its Z, to the second, format `YYYY-MM-DDTHH:MM:SS`, or `None` when no started line) and its last `bridge-run: exit <code>` (an int, `None` while the run goes on).
- `err_counts_as_reply(root, round_entry)` already refuses a launch whose start equals the entry's `flagged_launch` (both compared with `rstrip("Z")`). It needs no change.
- `snapshot_review_refusal` reads `err_counts_as_reply`. It needs no change.
- `load_rounds(common, id_part, root=None, seed=False)` and `write_rounds(common, id_part, data)` are the record's reader and writer; `write_rounds` also rewrites the record's hash copy.
- `record_flagged_launch` runs no git command today (`bridge_env.parse_review_name`, `launch_info`, `load_rounds` with `seed=False`, `write_rounds`).
- `cmd_verify` removes the verified mark first, so a return before its end leaves no mark.

**The tests' helpers** are `tests/test_task032_supervisor_guard.py`'s (`make_repo`, `snap_ok`, `launched(repo, name, offset=1, exit_code=0)`, `verify_ok`, `entry`, `bump`, `guard`), imported by `tests/test_bug039.py` as `G`. `launched(..., exit_code=None)` writes an `.err` with a started line and no exit line, as a run still going leaves it.

**Security context.** The project's ASVS level is 2 (`docs/DESIGN.md`, "Change: release T"; INVENTORY, Decisions). `.cursor/rules/secure-coding.mdc` is an applicable rule already in force. This program is the gate's own: `security-auditor` reads the diff. The trust boundary is D-004's: what the reviewer's run can write is untrusted input to this program, namely HEAD, refs, stashes, `.git/config`, hooks and ignored files in the checkout, the snapshot file (hash-checked against the copy outside the checkout), and the `.err` file. The guard's stated limit stands (`review-guard.py`'s docstring, KP-032): it is a guard against what a reviewer does in passing, not a sandbox. No secret, key or credential is read or needed by this task: the guard prints no value, and nothing here touches `.env`.

## Diagrams
This increment implements these normative diagrams.

`docs/diagrams/D-003-review-round-states.md`: states `flagged_gate_integrity`, `resnapshotted`, `review_launched`, `reply_arrived`, `verified_ok`. The transitions that matter, as the diagram draws the design:
```
reply_arrived --> flagged_gate_integrity : verify GATE-INTEGRITY before restoring (the snapshot rewritten, .git/config or a hook changed, the branch held in another worktree or not put back), nothing restored, no reply, no mark, the launch voided as flagged_launch
review_launched --> flagged_gate_integrity : verify GATE-INTEGRITY while the run goes on, the launch voided as flagged_launch by its start time, no mark
flagged_gate_integrity --> resnapshotted : snapshot nnn again, no reply counted, round N not spent
flagged_gate_integrity --> review_launched : Review B run again on the same snapshot
reply_arrived --> reply_arrived : verify CANNOT VERIFY 2 (no copy of the snapshot hash, a git failure), no mark
```

`docs/diagrams/D-004-context-dfd.md`: elements `p_review_guard`, `ds_checkout`, `ds_run_outputs`:
```
ds_checkout -->|"UNTRUSTED: HEAD, refs, stashes, .git config, hooks, ignored files"| p_review_guard
p_review_guard -->|"restore: reset, clean, refs back, hooks off"| ds_checkout
ds_run_outputs -->|"UNTRUSTED: exit line of REVIEW-nnn.err"| p_review_guard
```

Conform to them: a state or transition the state machine does not draw, or a git command with the hooks and the file monitor on, is a failure at review. Everything the diagrams do not fix is yours to decide. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

Two known label differences are not conflicts, and you do not stop for them; the supervisor redraws these labels as built after your run. First, D-003 draws no transition for a clean `verify` of a voided launch; Requirement 4 states that behaviour, and the state's row already says "verify exit 1, no mark, no reply". Second, D-003's `no_verdict --> flagged_gate_integrity` is labelled "no launch to void", drawn from the code before this fix; Requirement 3 follows R-042 and the bug record, "whatever its exit so far". Some labels also read "as built not, DEVIATIONS.md, BUG-039": those clauses describe the code before this fix and are what you are removing the cause of.

## Requirements
**The existing behaviour you may change is the flagged-round handling at these four sites, and nothing else.**

1. **Site 1.** Each of `cmd_verify`'s four early GATE-INTEGRITY returns calls `record_flagged_launch` before returning 1: the snapshot rewritten; `.git/config` or a hook changed; the branch held in another worktree; the branch not put back. Each still prints what it prints today and still restores nothing, as today.
2. **No git on the pre-git returns.** At the snapshot-rewritten and the config-or-hook returns no git command runs, the void included; their printed lines say so.
3. **Site 2, first part.** `record_flagged_launch` records the void by the launch's start time whatever the `.err` file's exit so far (no exit line included), where the `.err` holds a started line at or after the snapshot. A launch with no started line, or one before the snapshot, is not voided, as today. Writing `flagged_launch` touches only that key of that round's entry; an existing `reply` is left as it is.
4. **Site 2, second part.** A `verify` that finds nothing to flag and whose launch start equals the round's `flagged_launch` (compared without the trailing Z, as `err_counts_as_reply` does) still restores the tree and repairs as it does today, but writes no `reply` and no verified mark, prints a line containing `GATE-INTEGRITY` saying the launch was voided and Review B runs again, and exits 1. This holds whatever the launch's exit, and whether or not the launch is at or after the current snapshot. `flagged_launch` stays recorded.
5. **A new launch is admitted.** A launch with a start time of its own, on the same snapshot of the flagged round, goes through `verify` as today: `reply` 0, a mark, exit 0, and `premerge` accepts it. An older `flagged_launch` left in the entry does not stop it.
6. **Site 3.** `cmd_premerge`'s `git merge-base --is-ancestor <reviewed head> <head>` runs through `_git_proc`, its return code read as today. A non-ancestor still prints the same two GATE-INTEGRITY lines and returns 1. After the fix `_git_proc` holds the program's only git process call.
7. **Site 4.** `cmd_snapshot`'s replacement of a round's entry, on a re-snapshot of the same round, keeps `flagged_launch` beside `reply`, `lift`, `lift_line` and `time`, on the same tree and on a changed one. No path of the fix clears a recorded flag. An entry that has no flag gains no new content that changes what any other reader of the record sees (`_validate_rounds_data`, `bridge_env`'s branch rule, `pace-report.py`).
8. **The rewritten snapshot stays a clean exit.** At the snapshot-rewritten return the snapshot's content is untrusted, and calling `record_flagged_launch` there is new. Any snapshot that today reaches that return and exits 1 with its GATE-INTEGRITY line, including one rewritten to valid JSON that is not an object or whose `taken` is not a string, still does so, with no traceback (`test_bug039_site1_negative_a_snapshot_rewritten_to_any_shape_stays_a_clean_flag`).
9. **Generators.** Run after the code is final, from the Workspace root: `python tools/dump-cli.py` regenerates `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`; `python tools/make-manifest.py` regenerates `bridge/cursor-bridge/MANIFEST.json`. No command changes: `snapshot`, `verify` and `premerge` keep their arguments and their exit codes' meanings (0 OK; 1 GATE-INTEGRITY; 2 cannot verify; 125 refused). If `make-manifest.py` changes `bridge/cursor-bridge/VERSION`, stop and report it.

**Everything else stays unchanged.** In particular: the exit-2 returns of `cmd_verify` and `cmd_premerge` void nothing (a missing hash copy, a git failure); a `DESIGN-` name has no rounds record and is not voided; a missing rounds record is never created by `verify` (`test_task032_guard_r11_verify_never_creates_missing_rounds_file` pins it, with exit 0); a rounds record that is unreadable or changed outside the guard keeps today's handling in `verify`; the marks with no launch, no exit yet or a failed exit, for a launch never flagged, are written as today and `premerge` refuses them; `snapshot`'s refusals and the ceiling's count are as today.

## Acceptance criteria
- [ ] Every test in `tests/test_bug039.py` passes, the file unedited (`git diff` shows no change to it): every reproduction test and negative case named in the Objective.
- [ ] The full suite passes with no other change in results. Every existing guard test stays green: `tests/test_review_guard.py`, `tests/test_review_guard_a4.py`, `tests/test_review_guard_ceiling.py`, `tests/test_bug036.py`, `tests/test_hotfix25a_guard_scope_invisible.py`, `tests/test_task032_supervisor_guard.py`.
- [ ] The named causes are addressed at the mechanisms the evidence points at: site 1, the void is recorded on each of the four early return paths; site 2, the record no longer depends on the exit, and the admission path at the end of `cmd_verify` reads `flagged_launch`; site 3, the call goes through `_git_proc`; site 4, the rebuilt entry carries `flagged_launch`.
- [ ] Every requirement under "Satisfies" is fully met for this increment's part, with no stand-in or placeholder. The trace is already in place and you do not add to it: `tests/test_bug039.py` names R-042 and R-055 in its module docstring, and R-042, D-003 or D-004 in each test's docstring.
- [ ] `python tools/dump-cli.py --check` exits 0, and `bridge/cursor-bridge/MANIFEST.json` is regenerated by `python tools/make-manifest.py` after the last edit of `review-guard.py`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` exits 0, no FAIL line.
- [ ] No new dependency; no new import beyond the standard library and what `review-guard.py` imports today.

## Constraints
- Do not fix by suppressing the symptom — no retry, broad `try/except`, widened tolerance, added `sleep`, or null-check that hides a wrong value.
- Do not edit the reproduction test file `tests/test_bug039.py`, or any other test file.
- Do not leave any `DEBUG-BUG-` line or stray print.
- **If you believe the real cause is different from the one named, stop, do not change code, and report why in your summary** — the supervisor will re-diagnose.
- Keep the fixed points named in Context. If the fix cannot keep them, stop and report it.
- `review-guard.py` is ASCII-only and never prints a value of anything (its docstring); what you add keeps both.
- No secret or key is read: do not open `.env` or anything under `secrets/`, and do not print or log a credential.
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way — an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason — append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python — `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. `_git_proc` already passes `creationflags=NO_WINDOW`.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the Development data paragraph in Context) and refuses the installed product's data; if the brief does not say where the development data is, stop and report it (rule 55).
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only. The temporary repositories the tests create are the tests' own affair.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser (`int`, `float`, `Decimal`, `parseInt` with its radix, a date library), never by slicing or splitting a string; the brief states each value's unit and its range, and the code rejects a value outside it. The launch's start time and exit code here come only through `launch_info`; add no second reader of the `.err` file.
- This increment starts no process other than the git processes through `_git_proc`, and adds no new kind of process.
- Every verification command the Done section asks you to run is written there in full, with its options and its working folder, so you run exactly it. The strength of the tests is checked on the supervisor's side after your run; no mutation is asked of you, and no mutation script lands in the diff.
- Prefer reuse over new code — existing helpers, the standard library, native platform features, already-installed dependencies — and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.

## Done
Run these from the Workspace root, in this order, once the code is final, and quote each command's last line in your report:

```
python -m pytest tests/test_bug039.py -q -p no:cacheprovider
python -m pytest tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_review_guard_ceiling.py tests/test_bug036.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider
python tools/dump-cli.py
python tools/make-manifest.py
python tools/dump-cli.py --check
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
python -m pytest tests -q -p no:cacheprovider
```

Your report is the file `handoff/TASK-043-r1-report.md`, which you write as you go — what you did, what you changed, what you ran and what it printed, what you could not do — so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, one sentence for each of the four sites stating how the change addresses the named cause, and a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm — the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
