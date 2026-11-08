# TASK-048-r3 report

## Files changed

- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/scope-check.py
- bridge/cursor-bridge/completion-check.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json
- handoff/TASK-048-r3-report.md

## Summary

Round 3 centralised brief and plan reading in `bridge_env` through `read_brief_record`, `walk_plan_prose_body`, and `read_record_text`, then routed the five gate and check programs through those paths so agreeing headers, orphan headings, scope agreement, universal newlines, unreadable plan files, malformed brief headers, parenthesis notes without a merged set, and SCOPE-file prose reads all behave as the brief requires.

## The structure

**`read_brief_record`** (`bridge_env.py`): `read_blocking_class_line`, `merge_unit_line_present`, `merge_unit_ids`, `brief_satisfies`, `brief_prose_fallback`, `brief_header_refusal`, `brief_malformed_brief_line`, `brief_enforced_scope_paths`, `brief_scope_enforcement`, and `plan-check.py` `brief_findings` (via `brief_enforced_scope_paths` / `read_brief_record`).

**`walk_plan_prose_body`** (`bridge_env.py`): `plan_check_parse` and `plan_stages_without_demonstration` (used by `plan-check.py` `parse` and `stages_without_demonstration`), `plan_prose_fallback`, `plan_collect_satisfies_ids`, `plan_header_refusal`, `plan_header_findings`, and `plan_increment_ids`.

**`read_record_text` / `decode_record_bytes`** (`bridge_env.py`): `plan-check.py` `read`, `completion-check.py` `read`, `scope-check.py` `parse_scope`, `bridge-run.py` merge-unit plan loop and `decode_record_bytes` for the brief after `brief_sha256`, `review-guard.py` `snapshot_review_refusal`.

## The findings

- **S-1:** `read_brief_record` is the sole brief `read_header` path; malformed headers yield refusal with no prose fallback; all listed brief readers consume its result.
- **S-2:** `walk_plan_prose_body` walks plan bodies once; `plan-check.py` and `completion-check.py` no longer reference `HEAD_RX`, `FIELD_RX`, `DEMO_RX`, or `STAGE_RX`.
- **R3-1:** `brief_enforced_scope_paths` always parses Scope from the body when the header is not malformed, so plan-check BRIEF lines run for agreeing headers; R-id search uses the body.
- **R3-2:** Headed plans treat `outside_stage` increments as SHAPE/header refusals and exclude them from `plan_increment_ids` and parse items.
- **R3-3:** `plan_scope_agreement_entries` splits on `;` without parenthesis refusal; `plan_scope_paren_unbalanced` is plan-check-only for shape.
- **R3-4:** `read_record_text` / `decode_record_bytes` normalise `\r` and `\r\n` to `\n` with UTF-8-sig and replacement decoding in all five programs for plan/brief records.
- **R3-5:** `bridge-run.py` refuses unreadable plan paths; `plan_increment_ids` raises `PlanFileReadRefusal`; brief readers return nothing on malformed headers.
- **R3-6:** With `merged_set is None`, unbalanced Scope parentheses emit a `note:` listing increment IDs instead of `SHAPE:` failures.
- **R3-T1:** SCOPE files use `_blocking_class_from_prose` and `_merge_unit_from_prose` on the whole text, not brief header stripping.
- **R3-T2:** Removed `_brief_well_formed_header` and the no-op `plan_body` handler; docstrings match behaviour.

## TASK-046 and TASK-047 code

none (no edits to `_plan_field_value` or TASK-047 status readers compared with 4bdac19).

## Existing tests

none

## Manifest

```
python tools/make-manifest.py
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

## Commands and output

State after `git rev-parse HEAD` and `git status --short` at the end of this section (commit `62ee96c27904d86f072e0b7a42372b62a931c501` plus the uncommitted changes listed there).

```
python -m pytest -q tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py
```
```
105 passed in 71.22s (0:01:11)
```

```
python -m pytest -q tests/test_plan_check.py tests/test_plan_demonstration.py tests/test_scope_check.py tests/test_completion_check.py tests/test_a4_review_fixes.py tests/test_a4_followups.py tests/test_a5_followups.py
```
```
56 passed in 33.45s
```

```
python -m pytest -q tests/test_bridge_run.py tests/test_bridge_run_review_ceiling.py tests/test_bridge_run_design_ceiling.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_r4.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_hotfix25a_roster_launcher.py
```
```
430 passed in 154.37s (0:02:34)
```

```
python -m pytest -q tests/test_review_guard.py tests/test_review_guard_ceiling.py tests/test_review_guard_a4.py tests/test_task032_supervisor_guard.py tests/test_d003_review_round_states.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_bug036.py tests/test_bug038.py tests/test_bug039.py tests/test_bug041.py tests/test_bug042.py tests/test_bug043.py
```
```
331 passed in 367.37s (0:06:07)
```

```
python -m pytest -q tests/test_header_reader.py tests/test_header_schemas.py tests/test_header_status.py tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_mutation_run.py
```
```
1193 passed, 1 skipped in 412.23s (0:06:52)
```

```
python tools/dump-cli.py --check
```
```
exit=0
```

```
python tools/make-manifest.py
```
```
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

```
python bridge/cursor-bridge/diagram-check.py --mode code
```
```
note: mode code; 5 diagrams selected across 5 kinds; 13 kinds omitted
RESULT: OK
```

```
git rev-parse HEAD
```
```
62ee96c27904d86f072e0b7a42372b62a931c501
```

```
git status --short
```
```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/completion-check.py
 M bridge/cursor-bridge/plan-check.py
 M bridge/cursor-bridge/review-guard.py
 M bridge/cursor-bridge/scope-check.py
?? handoff/TASK-048-r3-report.md
```

## Assumed, not verified

- `PlanFileReadRefusal` line wording on plan `HeaderError` inside `plan_increment_ids` · bridge-run already refused via `plan_header_refusal` on each file first · a headed malformed plan in merge-unit check only; supervisor launcher case uses unreadable directory, which is covered by step 1 tests.
- R3-6 note wording `unbalanced parenthesis in Scope not checked against a merged set: <ids>` · matches the brief suggestion · supervisor r2 rewritten case passes with this wording.
- R3-2 SHAPE line `SHAPE: <id> has a ### heading but stands outside any stage` · brief allows SHAPE or HEADER DISAGREES · r3 orphan cases accept this SHAPE form.
