# SCOPE - BUG-028

BUG-028, a supervisor increment (no builder, no brief): the fix of ISS-016, a flaky test.

## The change and where it ends
- tests/test_hotfix25a_guard_scope_invisible.py only: the `ready` fixture gives review-guard a stand-in `time` (class GuardTime: its `sleep` is the recording list's append; every other name is read from the real time module), replacing `monkeypatch.setattr(mod.time, "sleep", sleeps.append)`, which patched the process-wide `time.sleep`; and one new test.
- No program changes. bridge/cursor-bridge/review-guard.py is unchanged, as is every other test.

## Cause (confirmed from the sources)
- `mod.time` is the `time` module itself, so the old patch recorded every `time.sleep` in the process.
- CPython's `subprocess.Popen._wait` on POSIX, given a timeout, polls in a loop whose first delay is 1 ms (`delay = 0.0005 # 500 us -> initial delay of 1 ms`, then `time.sleep(delay)`). It sleeps only when the child has not exited at the first poll, so test_premerge_reads_a_lagging_head_on_github_again_before_it_flags failed at random on Linux. The failure was `assert [0.001, 15, 15] == [15, 15]`, on PR #86, run 40250837238. Windows waits with WaitForSingleObject, so the test cannot fail there.

## Tests the supervisor wrote
- test_the_fixture_records_the_guards_sleeps_and_no_others (enforces: the fixture's docstring, which says the guard's own time.sleep is recorded; ISS-016). It calls the process-wide time.sleep(0) and expects nothing recorded, then the guard's time.sleep(15) and expects [15]. It also checks that the guard's strftime and gmtime are the real module's. It fails on the old fixture with `assert [0] == []` and passes with the fix. Deterministic on every platform.

## Expected record files
- docs/PROJECT_STATUS.md, as at this pull request's merge (PR #87, ISS-009). Its Last accepted and Maintainer requests history moved to docs/archive/STATUS_HISTORY.md (two appended lines), because of the status cap.
- run/review/: these review files.
- Documents/ (outside git) holds ISS-016's entry; it is not in the diff.

## Evidence
- The guard test file: 13 passed; full suite 2244 passed, 33 skipped.
- Review A, round 1: APPROVE (0 Blocking / 0 Should fix / 2 Consider). The Considers: two tests in tests/test_hotfix25a_roster_launcher.py (lines 160, 169) make the process-wide sleep a no-op the same way, which cannot fail like ISS-016, recorded with ISS-016 as a related site; and the race itself is POSIX-only and not reproducible on Windows, the CI log being its evidence.
