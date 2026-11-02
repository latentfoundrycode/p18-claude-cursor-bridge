# TASK-043, round 3: BUG-039, four corrections of round 2

## Objective
Fix the following confirmed defect — repair the named cause, nothing else. Round 2's five repairs stand. Review A and the security audit of round 2 reproduced four small defects in that code, in `bridge/cursor-bridge/review-guard.py`; the first and third were found by both.

**Cause 1: `load_snapshot`'s catch is both too wide and too narrow.**
- Root cause: `except (OSError, ValueError)` catches more than `handoff/TASK-043-r2.md` asked. `sha256_file` swallows an OSError and returns `None`, so `sha256_file(p)[:16]` raises `TypeError`. And `json.load` raises `RecursionError` on deeply nested text, a `RuntimeError`, which the catch misses.
- Evidence: a snapshot held open with no sharing: on the code before round 2, exit 2 with CANNOT VERIFY; now a traceback and exit 1, the exit that means GATE-INTEGRITY, with no such line. A snapshot rewritten to `"[" * 200000`: exit 2, no GATE-INTEGRITY line, no void, and the next snapshot on a changed tree is refused `round 1 is reviewed`.
- Tests: `test_bug039_site1_negative_an_unreadable_snapshot_stays_a_cannot_verify`, `test_bug039_site1_negative_a_snapshot_rewritten_to_any_shape_stays_a_clean_flag[too-deep]`.

**Cause 2: the void's own failure replaces the git failure.**
- Root cause: `record_flagged_launch` is called unguarded in `cmd_verify`'s `except`, so an `OSError` from `write_rounds` propagates in place of the original exception, against `handoff/TASK-043-r2.md`, Requirement 3's last sentence.
- Evidence: `git clean` failing and `write_rounds` raising: the flag lines, then `CANNOT VERIFY - <the write's error>`; the git failure is not named, and nothing says the void was not recorded.
- Test: `test_bug039_site5_negative_a_void_that_cannot_be_written_leaves_the_git_failure_named`.

**Cause 3: the exit line's bound is one digit short, a defect of `handoff/TASK-043-r2.md`'s number, not of the builder's work.**
- Root cause: the launcher writes the raw return code, a crash's code on Windows has ten digits (0xC000013A is 3221225786), and `(\d{1,9})(?!\d)` does not match it, so the search falls back to an earlier exit line.
- Evidence: an `.err` holding `bridge-run: exit 0` and then `bridge-run: exit 3221225786` reads as exit 0: reply 0, a mark, and `premerge` exits 0.
- Test: `test_bug039_site7_a_real_windows_exit_code_is_read`.

**Cause 4: the tamper line depends on `load_rounds`'s wording.**
- Root cause: the line at the end of `cmd_verify` is built from `load_rounds`' message by stripping two prefixes, and the messages of `_validate_rounds_data` do not hold the words `rounds record`, which `handoff/TASK-043-r2.md`, Requirement 2, asks of the line.
- Evidence: a record `{"rounds": 5}` with no hash copy prints `GATE-INTEGRITY - rounds is not a list: TASK-001`.
- Test: the existing `test_bug039_site2_negative_a_tampered_record_admits_no_launch` stays green.

Satisfies: R-042 — a flagged round (GATE-INTEGRITY) spends nothing whichever of `verify`'s checks flagged it and whenever. R-055 — D-003 is drawn as built; its redraw is the supervisor's, on this code.

## Scope
One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.
Files and directories you may create or modify:
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-043-r3-report.md

Do not modify anything else. `tests/test_bug039.py` is the supervisor's: you read it and run it, and you never edit it. `MANIFEST.json`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running their generators (Requirement 5).

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names
- every test file under tests/
- `docs/debug/BUG-039.md`, every file under `docs/diagrams/`, `docs/BUILD_PLAN.md` and `docs/REQUIREMENTS.md`: the supervisor's records
- `bridge/cursor-bridge/VERSION` (its content stays `2026.10.30d`) and `bridge/cursor-bridge/CHANGELOG.md`
- `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`
- every part of `review-guard.py` other than the four places Requirements 1 to 4 name. The limits `handoff/TASK-043-r2.md` lists stay, with these beside them, recorded on the supervisor's side: a record tampered with and later restored byte for byte; a `git` or `gh` program found in the current folder where the shell allows that search.

## Context
All paths are relative to the Workspace root, the folder you were started in. Read `handoff/TASK-043.md` and `handoff/TASK-043-r2.md` for the fixed points, the functions and the tests' helpers; they stand except where this brief says otherwise. Rounds 1 and 2 are committed; you build on them.

**Development data:** the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited. The guard is exercised only by the tests, each on a temporary git repository. Never run `review-guard.py snapshot`, `verify` or `premerge` in this Workspace itself.

**Security context.** The project's ASVS level is 2. `.cursor/rules/secure-coding.mdc` is in force. This program is the gate's own and `security-auditor` reads the diff. No secret, key or credential is read or needed: the guard prints no value.

## Diagrams
`docs/diagrams/D-003-review-round-states.md` and `docs/diagrams/D-004-context-dfd.md`, as in `handoff/TASK-043.md`. The supervisor redraws D-003's labels as built after your run. If the task cannot be done within them otherwise, stop and report the conflict instead of deviating.

## Requirements
**The existing behaviour you may change is what these four causes name, and nothing else.**

1. **Cause 1.** `load_snapshot` catches `ValueError` and `RecursionError` around the read and parse of the snapshot, and nothing else: an `OSError` propagates to `main`, which prints CANNOT VERIFY and exits 2, as it did before round 2.
2. **Cause 2.** In `cmd_verify`'s `except`, an `OSError` from `record_flagged_launch` is caught around that one call and prints one line starting `review-guard: GATE-INTEGRITY - ` that holds the words `not recorded`, saying the launch could not be voided; then the original exception is re-raised unchanged by a bare `raise`, so `main` names the git failure and exits 2.
3. **Cause 3.** `launch_info`'s exit line reads `bridge-run: exit (\d{1,10})(?!\d)`. Nothing else in `launch_info` changes.
4. **Cause 4.** Where `load_rounds` returns an error at the end of `cmd_verify`, the line printed is one fixed sentence, `review-guard: GATE-INTEGRITY - the rounds record of <the ID> was changed outside the guard or cannot be read: no reply and no verified mark`, with the increment's ID in place of `<the ID>`, and `load_rounds`' message is not printed. The two prefix-strips go.
5. **Generators.** Run after the code is final, from the Workspace root: `python tools/dump-cli.py`, then `python tools/make-manifest.py`. If `make-manifest.py` changes `bridge/cursor-bridge/VERSION`, stop and report it.

**Everything else stays unchanged.**

## Acceptance criteria
- [ ] Every test in `tests/test_bug039.py` passes, the file unedited.
- [ ] Every existing guard test stays green: `tests/test_review_guard.py`, `tests/test_review_guard_a4.py`, `tests/test_review_guard_ceiling.py`, `tests/test_bug036.py`, `tests/test_hotfix25a_guard_scope_invisible.py`, `tests/test_task032_supervisor_guard.py`. The supervisor runs the full suite after your run.
- [ ] `python tools/dump-cli.py --check` exits 0, and `bridge/cursor-bridge/MANIFEST.json` is regenerated after the last edit of `review-guard.py`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` exits 0, no FAIL line.
- [ ] No new dependency and no new import.

## Constraints
- Do not fix by suppressing the symptom — no retry, broad `try/except`, widened tolerance, added `sleep`, or null-check that hides a wrong value. Catch exactly the exceptions the Requirements name; a catch wider than a requirement says is what round 2's Cause 1 was.
- Do not edit `tests/test_bug039.py` or any other test file.
- Do not leave any `DEBUG-BUG-` line or stray print.
- **If you believe the real cause is different from the one named, stop, do not change code, and report why in your summary** — the supervisor will re-diagnose.
- `review-guard.py` is ASCII-only and never prints a value of anything; what you add keeps both.
- No secret or key is read: do not open `.env` or anything under `secrets/`, and do not print or log a credential.
- Do not add dependencies.
- Do not read or write any file outside this workspace, other than what the tests and the program itself do in the system's temporary folder.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling.
- In any Markdown you write, never break a line inside a paragraph or a list item.
- Never start a server, a watcher or a daemon that outlives a test.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only.
- No mutation is asked of you, and no mutation script lands in the diff.
- Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force).

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

Your report is the file `handoff/TASK-043-r3-report.md`, which you write as you go. When you finish, it holds a list of every file you changed, a one-paragraph summary, one sentence for each of the four causes, and a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled and that you did not confirm, an ambiguous requirement you resolved one way and any place you departed from a requirement's words included. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific.

Your last message is the summary and the report file's path, and nothing follows it.
