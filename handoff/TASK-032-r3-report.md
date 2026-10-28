# TASK-032-r3 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/review-guard.py`
- `bridge/cursor-bridge/permission-guard.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `tests/test_bridge_run_review_ceiling.py`
- `tests/test_bridge_run_design_ceiling.py`
- `tests/test_review_guard.py`
- `docs/cli-reference.json`
- `docs/CLI_REFERENCE.md`

## Summary

Round 3 closes the launcher and guard defects from TASK-032-r3: workspace-folder branch and brief for logging and refusals, strict merge-unit and heading rules, exact blocking-class matching, squash reader parity with plan-check, malformed-record hardening, ASCII brief-rule refusals with the delegation-loop pointer, owner lifts read from the launch folder, and guard tamper-before-seed, in-memory seeding only on accepted snapshots, verify without creating rounds files, re-snapshot lift reuse, outside-git exit 125, neutralised lapse git calls, and letter-seeding that skips foreign-branch snapshots. Supervisor suites (231 tests) and all in-scope tests pass.

## Defect fixes

| ID | What we did | Where |
|----|-------------|-------|
| L1 | `brief_meta["branch"]` from pre-resolve `workspace_of`; log uses it not post-resolve argv | bridge-run.py:1512-1513, builder_review_refusal :604-688 |
| L2 | Heading check only on `merge_ids`; invalid unit line refuses; scope ID exempt | bridge-run.py:647-667, bridge_env.py:426-448 |
| L3 | Merge tokens must be bare IDs via `parse_review_name` | bridge_env.py:436-441 |
| L4 | Proper superset refusal `existing < declared` | bridge-run.py:668-675 |
| L5 | `prior_brief_run` exempts identical-bytes class repeat at any exit | bridge-run.py:546-556, 698-700 |
| L6 | `BLOCKING_CLASS_RE` case-sensitive; no lowercasing class | bridge_env.py:322-325, 370-374 |
| L7 | Merge-first squash; task-014 branch trim; hyphen+digit subject tokens | bridge_env.py:488-530 |
| L8 | `read_runs_jsonl`, `errors=replace`, skip bad rounds, `ValueError` on int, timeouts | bridge_env.py:348-361, 602-622, bridge-run.py:378, 418-428, 523-539 |
| L9 | `_brief_rule_refusal` / `_ascii_refusal`; ceiling names both lift forms | bridge-run.py:580-707 |
| L10 | `review_owner_lifts(folder)` not workspace | bridge-run.py:606 |
| G1 | Tamper before seed in `load_rounds` | review-guard.py:497-508 |
| G2 | Seed in memory only; `verify` uses `seed=False` | review-guard.py:497-508, 899-908 |
| G3 | Seeded empty `tree` with reply blocks re-snapshot | review-guard.py:592-596 |
| G4 | Re-snapshot reuses recorded lift; preserves `time` | review-guard.py:614-626, 719-726 |
| G5 | Class repeat message uses `review-guard: refused - review ceiling:` | review-guard.py:626 |
| G6 | `merge_ids` on write; `declared_set_for_id` in `_branch_events` | review-guard.py:714-716, bridge_env.py:652-678 |
| G7 | Outside git counted snapshot exit 125 | review-guard.py:648-652 |
| G8 | `git_runner` on squash/branch_exists via `_git_proc` | bridge_env.py:488-548, review-guard.py:100-120, 577-578 |
| G9 | Letter seed skips wrong-branch/unreadable snaps | review-guard.py:403-422 |
| C1 | Single `GRAMMAR_ID_PATTERN` drives regexes | bridge_env.py:309-328 |
| C2 | Removed dead probe/launcher helpers and `GIT_SHORT` | permission-guard.py:104-133, review-guard.py:85 |
| C3 | `rounds_hash_copy_path` reuses key; `scope_blocking_line` only | review-guard.py:349-352, 549-556 |
| C4 | `bridge_env` ASCII; pre-existing non-ASCII in other files unchanged | bridge_env.py |
| D1 | Module docstrings updated; `dump-cli` regenerated | bridge_env.py:15-18, docs/cli-reference.json |
| E1 | Detached DESIGN snapshot + verify hook test | tests/test_review_guard.py:155-167 |
| E2 | Premerge after TASK-001-r2; no extra commit | tests/test_review_guard.py:243-252 |
| E3 | task-002/003 without REVIEW diff commits | tests/test_review_guard.py:113-117, 178-182 |
| E4 | Trailing newline in refused name test | tests/test_bridge_run_review_ceiling.py:300 |
| E5 | Full design pointer phrase | tests/test_bridge_run_design_ceiling.py:47 |

## Hand mutations (catching supervisor tests)

| Mutation | Catching test |
|----------|----------------|
| 1. Class match case-insensitive again | `test_task032_launcher_bad_class_lines_refused[Blocking class: Behaviour - ...]` |
| 2. Tamper check after seeding | `test_task032_guard_r13_hash_copy_beside_deleted_rounds_file_refused` |
| 3. `verify` creates missing rounds file | `test_task032_guard_r11_verify_never_creates_missing_rounds_file` |
| 4. Seeded empty tree not reviewed | `test_task032_guard_r14_seeded_round_resnapshot_on_changed_tree_refused` |
| 5. Re-snapshot ignores recorded lift | `test_task032_guard_r8_resnapshot_of_lifted_round_reuses_its_lift` |
| 6. Superset check inverted | `test_task032_launcher_later_brief_naming_more_ids_refused` |
| 7. Merge form after subject form | `test_task032_launcher_squash_reader_parity_with_plan_check` |
| 8. Workspace branch replaced by launch folder | `test_task032_launcher_brief_read_from_workspace_folder` |

## Verification output

```
python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider
231 passed

python -m pytest tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_permission_guard.py tests/test_hotfix25a_guard_scope_invisible.py -q -p no:cacheprovider
450 passed (681 with supervisor files included in combined run)

python -m pytest tests/test_bug029_agent_name.py tests/test_bridge_run_slot.py tests/test_bridge_run_driver.py tests/test_hotfix25a_roster_launcher.py tests/test_allowlist.py tests/test_loop_guard.py -q -p no:cacheprovider
415 passed, 23 skipped

python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py bridge/cursor-bridge/permission-guard.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py
windowless-check: 6 file(s) scanned, 0 FAIL, 0 NOTE

python tools/dump-cli.py && python tools/dump-cli.py --check
OK

python tools/make-manifest.py
make-manifest: version 2026.10.25a, 143 files hashed

python bridge/cursor-bridge/bridge-check.py --root bridge --sources
RESULT: SOURCES MATCH bridge 2026.10.25a
```

## Supervisor tests believed wrong

None.

## Assumed, not verified

Assumed, not verified: none.
