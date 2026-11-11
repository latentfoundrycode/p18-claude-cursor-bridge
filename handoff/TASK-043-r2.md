---
record: brief
header: 1
id: TASK-043
round: 2
satisfies: [R-042, R-055]
scope: ["bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-043-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-043, round 2: BUG-039, what round 1's reviews confirmed beyond the four sites

## Objective
Fix the following confirmed defect — repair the named cause, nothing else. Round 1 repaired the four sites of `handoff/TASK-043.md` and that code stays. Review A and the security audit of round 1 then reproduced five more causes in `bridge/cursor-bridge/review-guard.py`, each below with its evidence and its tests, each a way for a flagged round to be spent or admitted against R-042, or for a git command of the guard to run a hook against D-004. Each is its own confirmed cause; no instrumentation round is needed. They are recorded in `docs/debug/BUG-039.md`, sites 1, 2, 5, 6 and 7.

**Cause 1 (site 1's correction): the void at the rewritten-snapshot return trusts the snapshot it has just found rewritten.**
- Root cause: `record_flagged_launch` compares the launch with `snap["taken"]`, and at the first return of `cmd_verify` the snapshot is known to be rewritten. Separately, `load_snapshot` raises on text that is not JSON and returns `None` for a file holding `null`, which the callers read as "no snapshot", so those rewrites never reach that return.
- Evidence: a snapshot rewritten with `taken` set to `9999-01-01T00:00:00Z` or `zzz` gives exit 1 and no `flagged_launch`, and the next snapshot on a changed tree is refused `round 1 is reviewed`; with the original bytes put back, the next `verify` writes a mark and `premerge` exits 0. A snapshot rewritten to `{}` voids a launch from before the round. `null` exits 2 with nothing printed; `not json` ends in a traceback.
- Tests: `test_bug039_site1_negative_a_snapshot_rewritten_to_any_shape_stays_a_clean_flag` (all seven cases), `test_bug039_site1_negative_a_rewritten_snapshot_voids_no_launch_before_the_round`.

**Cause 2 (site 2's correction): the admission check fails open on a changed or deleted rounds record.**
- Root cause: the end of `cmd_verify` reads the record only `if os.path.isfile(rpath)` and acts only `if not err`, so `load_rounds`'s tamper report, which `snapshot` already refuses on, is dropped and the mark is written.
- Evidence: a launch flagged during the run, its exit 0, then the record deleted or one byte appended, its hash copy standing: the clean `verify` exits 0 with a mark, and `premerge` exits 0. `handoff/TASK-043.md` told you to keep today's handling here; this brief reverses that on the reviewers' reproduction, so the builder's round 1 was right to keep it.
- Test: `test_bug039_site2_negative_a_tampered_record_admits_no_launch` (two cases).

**Cause 3 (site 5): flags already found are lost when a later git step fails.**
- Root cause: `cmd_verify` collects `flags` in its step 2 and prints them only after its step 4; `run_git` raises on a failure in between, `main` prints CANNOT VERIFY and exits 2, and the flags and the void are gone.
- Evidence: a reviewer's new branch and a file `git clean` cannot remove: refs repaired, `clean` fails, exit 2, no GATE-INTEGRITY line, no void. Once the file is released the next `verify` finds nothing left, exits 0 and writes a mark.
- Tests: `test_bug039_site5_a_git_failure_after_a_flag_keeps_the_flag`; its negative `test_bug039_site5_negative_a_git_failure_with_no_flag_voids_nothing` holds today, which you keep green.

**Cause 4 (site 6): the guard's own "empty" hooks folder lies where the reviewer's run writes.**
- Root cause: `no_hooks_dir` returns `<git common dir>/bridge/no-hooks`, a fixed path inside `.git/`, and nothing hashes it or checks that it is empty.
- Evidence: `post-index-change` and `reference-transaction` planted there ran under `verify`, which printed OK, and `post-index-change` ran under `premerge`'s `git status`. That process inherits the owner's environment. D-004 draws these commands with the hooks off.
- Tests: `test_bug039_site6_a_hook_planted_in_the_guard_s_folder_never_runs` (verify, premerge), `test_bug039_site6_the_hooks_folder_lies_outside_the_repository`.

**Cause 5 (site 7): an exit line past `int()`'s limit raises.**
- Root cause: `launch_info` runs `int()` on `bridge-run: exit (\d+)`, unbounded, and Python raises `ValueError` above 4,300 digits; `main` does not catch it. Round 1's calls make this reachable at the four early returns.
- Evidence: the `.err` holding a 5,000-digit exit line at the config-changed return: the GATE-INTEGRITY line, then a traceback, no void.
- Test: `test_bug039_site7_an_exit_line_too_long_to_read_is_no_exit`.

Satisfies: R-042 — a flagged round (GATE-INTEGRITY) spends nothing whichever of `verify`'s checks flagged it and whenever. R-055 — D-004 draws every git command of the guard with the hooks and the file monitor off.

## Scope
One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.
Files and directories you may create or modify:
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-043-r2-report.md

Do not modify anything else. `tests/test_bug039.py` is the supervisor's: you read it and run it, and you never edit it. `MANIFEST.json`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running their generators (Requirement 6).

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names
- every test file under tests/, `tests/test_bug039.py` included
- `docs/debug/BUG-039.md`, every file under `docs/diagrams/`, `docs/BUILD_PLAN.md` and `docs/REQUIREMENTS.md`: the supervisor's records
- `bridge/cursor-bridge/VERSION` (its content stays `2026.10.30d`) and `bridge/cursor-bridge/CHANGELOG.md`
- `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`
- every part of `review-guard.py` other than what Requirements 1 to 5 name. In particular, leave these as they stand, recorded on the supervisor's side: the `.err` started line as the launch's only identity; a `DESIGN-` name, which has no rounds record and is not voided; `write_rounds` raising OSError at a flag's return; a reply already counted when a later verify flags the same launch.

## Context
All paths are relative to the Workspace root, the folder you were started in. Read `handoff/TASK-043.md`, the first brief, for the fixed points (`record_flagged_launch`, `flagged_launch`, `_git_proc`), the functions and the tests' helpers; all of it stands except where this brief says otherwise. Round 1's code is committed; you build on it.

**Development data:** the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet. The guard is exercised only by the tests, each on a temporary git repository, with `BRIDGE_REVIEW_HASHES` pointed at a temporary folder by `tests/conftest.py`. Never run `review-guard.py snapshot`, `verify` or `premerge` in this Workspace itself.

**A new fixed point:** `no_hooks_dir(common)` keeps its name and its parameter; `tests/test_bug039.py` calls it.

**Security context.** The project's ASVS level is 2. `.cursor/rules/secure-coding.mdc` is in force. This program is the gate's own and `security-auditor` reads the diff. What the reviewer's run can write is untrusted input to this program: HEAD, refs, stashes, `.git/config`, hooks, everything under `.git/` including `.git/bridge/`, ignored files, the snapshot file (hash-checked against a copy outside the checkout), the rounds record (likewise), and the `.err` file. The guard's stated limit stands (its docstring, KP-032): it does not cover anything outside the checkout. No secret, key or credential is read or needed: the guard prints no value.

## Diagrams
This increment implements `docs/diagrams/D-003-review-round-states.md` and `docs/diagrams/D-004-context-dfd.md`, as in `handoff/TASK-043.md`. The supervisor redraws D-003's labels as built after your run: the differences this brief makes (a tampered record as GATE-INTEGRITY at the end of `verify`, a flag kept beside CANNOT VERIFY) are not conflicts, and you do not stop for them. D-004's `p_review_guard` to `ds_checkout` edge, "restore: reset, clean, refs back, hooks off", is what Requirement 4 makes true. If the task cannot be done within them otherwise, stop and report the conflict instead of deviating.

## Requirements
**The existing behaviour you may change is what these five causes name, and nothing else.**

1. **Cause 1.** At `cmd_verify`'s snapshot-rewritten return the void reads nothing of the snapshot: `record_flagged_launch(common, root, nnn, None)`. There `record_flagged_launch` compares the launch's start with the round entry's `time` from the hash-checked rounds record, with the existing helper `_launch_time_ge_round`: voided where it is at or after that time, not voided where it is before it or where the entry has no time. At the other returns, where the snapshot is authentic, the comparison with `taken` stays as Requirement 3 of the first brief states it, and the two `isinstance` guards round 1 added go, since an authentic snapshot needs neither. `load_snapshot` returns an empty dict in place of the snapshot for a file whose content is not valid JSON or not a JSON object (a `ValueError` from the read included, an undecodable file among them), so `cmd_verify` and `cmd_premerge` both reach their rewritten-snapshot returns; `None` stays the answer for no snapshot file alone. No git command runs on this path.
2. **Cause 2.** For a name that is not `DESIGN-`, the end of `cmd_verify` reads the record once with `load_rounds(common, id_part, root=None, seed=False)`, with no `isfile` guard in front of it, and that one read serves both the voided-launch check and the reply's write. Where it returns an error, `verify` prints one line starting `review-guard: GATE-INTEGRITY - ` that holds the words `rounds record`, writes no reply and no mark, and returns 1. A record and its hash copy both missing is no error, as today: `verify` goes on and never creates the file (`test_task032_guard_r11_verify_never_creates_missing_rounds_file`), so the reply's write stays behind `os.path.isfile`.
3. **Cause 3.** Where a `RuntimeError`, `subprocess.TimeoutExpired` or `OSError` raises after `cmd_verify` has begun collecting `flags` and before they are printed, the flags found so far are printed as `  GATE-INTEGRITY  <flag>` and, if there are any, `record_flagged_launch` is called with the authentic snapshot; the exception then propagates unchanged, so `main` prints its CANNOT VERIFY line and exits 2. With no flags found, nothing is printed and nothing voided, as today. An error from the void itself does not replace the original exception. Choose the smallest form that does this and read the same on the page: a `try`/`except` around those steps or an inner function, whichever moves fewer lines.
4. **Cause 4.** `no_hooks_dir(common)` returns an empty folder outside the repository, made fresh once per process by `tempfile.mkdtemp`, kept in the module's existing `_NO_HOOKS` dict so every git command of the process uses the same one, and removed at the process's exit by `os.rmdir` through `atexit`, an `OSError` there ignored. `<git common dir>/bridge/no-hooks` is no longer created or read. A failure of `mkdtemp` is an `OSError`, which `main` already turns into exit 2.
5. **Cause 5.** `launch_info`'s exit line is bounded, at most nine digits with no digit after them: `bridge-run: exit (\d{1,9})(?!\d)`. A longer run of digits does not match, and the search goes on to the line before it, as for any line that does not match.
6. **Generators.** Run after the code is final, from the Workspace root: `python tools/dump-cli.py`, then `python tools/make-manifest.py`. No command changes: `snapshot`, `verify` and `premerge` keep their arguments and their exit codes' meanings. If `make-manifest.py` changes `bridge/cursor-bridge/VERSION`, stop and report it.

**Everything else stays unchanged.** Round 1's repair of the four sites stands. The tests of round 1 stay green.

## Acceptance criteria
- [ ] Every test in `tests/test_bug039.py` passes, the file unedited.
- [ ] Every existing guard test stays green: `tests/test_review_guard.py`, `tests/test_review_guard_a4.py`, `tests/test_review_guard_ceiling.py`, `tests/test_bug036.py`, `tests/test_hotfix25a_guard_scope_invisible.py`, `tests/test_task032_supervisor_guard.py`. The supervisor runs the full suite after your run.
- [ ] The named causes are addressed at the mechanisms the evidence points at.
- [ ] `python tools/dump-cli.py --check` exits 0, and `bridge/cursor-bridge/MANIFEST.json` is regenerated after the last edit of `review-guard.py`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` exits 0, no FAIL line.
- [ ] No new dependency; the only new imports are the standard library's `atexit` and `tempfile` where a requirement names them.

## Constraints
- Do not fix by suppressing the symptom — no retry, broad `try/except`, widened tolerance, added `sleep`, or null-check that hides a wrong value.
- Do not edit `tests/test_bug039.py` or any other test file.
- Do not leave any `DEBUG-BUG-` line or stray print.
- **If you believe the real cause is different from the one named, stop, do not change code, and report why in your summary** — the supervisor will re-diagnose.
- `review-guard.py` is ASCII-only and never prints a value of anything (its docstring); what you add keeps both.
- No secret or key is read: do not open `.env` or anything under `secrets/`, and do not print or log a credential.
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in), other than what the tests and the program itself do in the system's temporary folder.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall.
- In any Markdown you write, never break a line inside a paragraph or a list item.
- Any console process your code launches on Windows is created windowless. `_git_proc` already passes `creationflags=NO_WINDOW`. This round starts no new kind of process.
- Never start a server, a watcher or a daemon that outlives a test.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (the Development data paragraph in Context).
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only.
- The strength of the tests is checked on the supervisor's side after your run; no mutation is asked of you, and no mutation script lands in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security requirement stated above.

## Done
Run these from the Workspace root, in this order, once the code is final, and quote each command's last line in your report:

```
python -m pytest tests/test_bug039.py -q -p no:cacheprovider
python -m pytest tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_review_guard_ceiling.py tests/test_bug036.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider
python tools/dump-cli.py
python tools/make-manifest.py
python tools/dump-cli.py --check
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
```

Your report is the file `handoff/TASK-043-r2-report.md`, which you write as you go, so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary, one sentence for each of the five causes stating how the change addresses it, and a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm, an ambiguous requirement you resolved one way included. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific.

Your last message is the summary and the report file's path, and nothing follows it.
