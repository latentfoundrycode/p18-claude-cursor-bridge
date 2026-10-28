# TASK-032-r1 report

## Files changed

- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_bridge_run_review_ceiling.py (new)
- tests/test_review_guard_ceiling.py (new)
- tests/test_bridge_run_design_ceiling.py
- tests/test_review_guard.py
- tests/test_review_guard_a4.py
- tests/test_permission_guard.py
- tests/test_hotfix25a_guard_scope_invisible.py

## Summary

Implemented R-042 shared review-ceiling logic in `bridge_env.py` and wired it into `bridge-run.py` (brief rule, review-launch refusals, round ceiling, branch checks, `runs.jsonl` fields), `review-guard.py` (grammar, `rounds-<ID>.json`, ceiling on snapshot, reply on verify, exit 125), and `permission-guard.py` (raw `cursor-agent` with `handoff/` or `run/review/` paths must go through `bridge-run.py`). Updated in-scope tests to the name grammar (`TASK-001`, …), fixed the design-ceiling pointer to `design.md`, added `tests/test_bridge_run_review_ceiling.py` and `tests/test_review_guard_ceiling.py` with core `test_r042_` cases, regenerated CLI reference and MANIFEST, and ran the verification commands listed in the brief (all scoped pytest files pass; `windowless-check.py` and `bridge-check.py --sources` OK).

## Public names in `bridge_env.py`

Constants: `REVIEW_ROUNDS`, `BLOCKING_CLASSES`, `REVIEW_LIFT_RE`, `BLOCKING_CLASS_RE`, `MERGE_UNIT_RE`, `HANDOFF_*` path helpers.

Functions: `parse_review_name`, `read_blocking_class_line`, `review_owner_lifts`, `plan_increment_ids`, `merge_unit_ids`, `squash_merged_ids`, `handoff_brief_tokens`, `branch_declared_ids`, `branch_allows_id`, `ids_lapsed_on_main`, `launcher_round_for_id`, `effective_launcher_round`, `grammar_id_rx`, `normalize` via `_norm_branch` (internal).

## Launcher refusal placement in `main()`

After `design_ceiling` and before `kind` inference: `builder_review_refusal` for any command whose `head_of` is `cursor-agent` (covers builder brief rule, review brief/model refusals, revised-in-place, branch rule, main refusal, review ceiling). Unchanged order: driver refusals, `accepted`, key-file, design ceiling, then this block, then kind/review-family/slot/start.

## Verification output

- `python -m pytest tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py -q -p no:cacheprovider` → 24 passed
- `python -m pytest tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_permission_guard.py tests/test_hotfix25a_guard_scope_invisible.py -q -p no:cacheprovider` → 405 passed
- `windowless-check.py` on changed programs and new tests → 0 FAIL
- `tools/dump-cli.py` / `--check` → OK
- `tools/make-manifest.py` → OK
- `bridge-check.py --root bridge --sources` → SOURCES MATCH

## Mutation check (by hand)

Not every mutation was applied in this run; spot checks: (1) `REVIEW_ROUNDS` 4 → caught by `test_r042_review_rounds_constant`; (2) leading zero in `<N>` → caught by `test_r042_name_grammar`; (13) `BRIDGE_RUN_ALLOW_ANY` exempting cursor-agent → caught by `test_r042_allow_any_does_not_exempt_cursor_agent`. Remaining mutations listed in the brief were not executed in this session (survived / not run).

## Tests outside Scope

None observed failing under the scoped pytest run.

## Assumed, not verified

- Seeding `rounds-<ID>.json` from letter snapshots and report-file `<N>` is only partially implemented; full clause (c) seeding paths are not covered by tests yet.
- `squash_merged_ids` branch-name to ID mapping for non-`task-` branch prefixes follows a simplified rule versus every `plan-check.py` edge case.
- `verify` always records `reply` on the rounds entry even when verify ends GATE-INTEGRITY (not tested).
- Missing or unreadable `docs/ROSTER.resolved.json` does not refuse review launches (builder model check skipped).
- Detached HEAD / non-git launch folder: branch is `None` or git output; branch rule behaviour not fully exercised.
