# TASK-050 round 2 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/inventory-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_header_run_parameters.py`
- `tests/test_bridge_run_design_ceiling.py`

## Summary

Round 2 repaired all eight confirmed causes from round 1's review: inventory-check now refuses through `_bridge_env_refuse_line` before touching run-parameters; header lifts at or below defaults are dropped in `design_lifts` and `review_owner_lifts`; fallback readers split prose at line feeds only with a linear per-line `Agent ceiling` scan that skips unreadable numbers; the defective builder test case was removed and the design-ceiling helper restored with its R-061 case creating parent folders first.

## R1–R8

- **R1.** Deleted `test_r061_loop_guard_reads_agent_ceiling_with_a_non_utf8_byte` from `tests/test_header_run_parameters.py` (lines 464–468); no product code change.
- **R2.** `inventory-check.main` at line 327 calls `_bridge_env_refuse_line()` before any `bridge_env` use on the run-parameters path; `_INVENTORY_BRIDGE_NAMES` at line 82 drops unused `run_parameters_values`.
- **R3.** `bridge-run.design_lifts` at line 431 requires `rounds > DESIGN_DEFAULT_ROUNDS`; `bridge_env.review_owner_lifts` at lines 758–761 skips header items with `rounds <= REVIEW_ROUNDS`.
- **R4.** `tests/test_bridge_run_design_ceiling.run_parameters` line 24 restored to `(folder / "docs").mkdir(exist_ok=True)`; `test_r061_design_lifts_read_header_first_when_agreeing` adds `plain.mkdir()` and `headed.mkdir()` before calling the helper.
- **R5.** `_run_param_body_lines` at line 706 and its use in `_review_lifts_from_lines` and `run_parameters_fallback` split at U+000A only (after CRLF/CR normalization).
- **R6.** `AGENT_CEILING_RE` at line 356 uses `[ \t]` instead of `\s` and no `re.M`; `run_parameters_fallback` at lines 2790–2797 matches one line at a time.
- **R7.** The same per-line loop at lines 2790–2797 continues past a `ValueError` from `int()` and takes the first later valid `Agent ceiling` line.
- **R8.** All Done pytest commands used `-rs`; SKIPPED lines are quoted verbatim under Verification.

## Verification

Commit for counts: `8d5c0937b854a81d7d1bca58dfbb3157e8ae057a`. Working tree after step 7 held uncommitted changes (`git status --short` below).

### 1. Header run-parameters and currency

```
python -m pytest -q -rs tests/test_header_run_parameters.py tests/test_header_run_parameters_r2.py tests/test_header_currency.py
```

```
........................................................................ [ 43%]
........................................................................ [ 86%]
......................                                                   [100%]
166 passed in 12.66s
```

### 2. Loop guard, design/review ceiling, release bootstrap

```
python -m pytest -q -rs tests/test_loop_guard.py tests/test_bridge_run_design_ceiling.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_release_b_bootstrap.py
```

```
........................................................................ [ 36%]
........................................................................ [ 73%]
..................................................s..                    [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_release_b_bootstrap.py:318: not a pull request into main, nor a squash on main
196 passed, 1 skipped in 20.64s
```

### 3. Broader named tests

```
python -m pytest -q -rs tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_loop_text_pace.py tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_bridge_run_slot.py tests/test_d003_review_round_states.py tests/test_task033_supervisor.py tests/test_a4_followups.py tests/test_header_reader.py tests/test_header_schemas.py tests/test_header_status.py tests/test_header_plan.py tests/test_header_tables.py tests/test_dump_cli.py tests/test_tests_windowless.py
```

```
........................................................................ [  4%]
........................................................................ [  8%]
........................................................................ [ 12%]
........................................................................ [ 16%]
.......................................................................s [ 20%]
............................s.............s............................. [ 24%]
........................................................................ [ 28%]
........................................................................ [ 32%]
........................................................................ [ 36%]
........................................................................ [ 40%]
........................................................................ [ 44%]
........................................................................ [ 48%]
........................................................................ [ 52%]
........................................................................ [ 56%]
........................................................................ [ 60%]
........................................................................ [ 64%]
........................................................................ [ 68%]
........................................................................ [ 72%]
........................................................................ [ 76%]
........................................................................ [ 81%]
........................................................................ [ 85%]
........................................................................ [ 89%]
........................................................................ [ 93%]
........................................................................ [ 97%]
.................................................                        [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_bridge_run_slot.py:411: POSIX special files
SKIPPED [1] tests\test_bridge_run_slot.py:930: POSIX links and permission bits
SKIPPED [1] tests\test_bridge_run_slot.py:1125: POSIX permission bits
1774 passed, 3 skipped in 551.83s (0:09:11)
```

### 4. make-manifest

```
python tools/make-manifest.py
```

```
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

### 5. bridge-check

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

```
bridge-check: version 2026.11.03a (2026-11-08 23:39) at <Workspace>/bridge
bridge-check: 145 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.03a
```

### 6. dump-cli

```
python tools/dump-cli.py --check
```

(exit 0, no output)

### 7. R4 diff and git state

```
git diff 52d18be -- tests/test_bridge_run_design_ceiling.py
```

```
diff --git a/tests/test_bridge_run_design_ceiling.py b/tests/test_bridge_run_design_ceiling.py
index 9fa8f80..55309e3 100644
--- a/tests/test_bridge_run_design_ceiling.py
+++ b/tests/test_bridge_run_design_ceiling.py
@@ -289,3 +289,21 @@ def test_the_launcher_refuses_with_125_before_it_starts_anything(tmp_path):
     assert p.stderr.startswith("bridge-run: refused - design ceiling: "), p.stderr
     assert "bridge-run: started" not in p.stderr, p.stderr
     assert not (tmp_path / "run" / "launcher" / "runs.jsonl").exists()
+
+
+def test_r061_design_lifts_read_header_first_when_agreeing(program, tmp_path):
+    """R-061: design_lifts returns the same ceiling from a agreeing header as from the owner's line alone."""
+    br = program("bridge-run")
+    line = "Design rounds above five: pace 8 (the owner, 2026-11-04)\n"
+    header = ("---\nrecord: run-parameters\nheader: 1\nstage_pause: \"\"\nmerge_authority: \"\"\n"
+              "refactoring_pass: \"\"\ninstaller_verification: \"\"\nparallel_increments: \"\"\n"
+              "agent_ceiling: null\nceiling_above_twice: []\n"
+              "design_rounds_above_five:\n  - subject: pace\n    rounds: 8\n    words: the owner\n"
+              "    date: \"2026-11-04\"\nreview_rounds_above_ceiling: []\n---\n")
+    plain = tmp_path / "plain"
+    headed = tmp_path / "head"
+    plain.mkdir()
+    headed.mkdir()
+    run_parameters(plain, line.strip())
+    run_parameters(headed, header + line)
+    assert br.design_lifts(str(headed)) == br.design_lifts(str(plain)) == {"pace": 8}
```

```
git rev-parse HEAD
```

```
8d5c0937b854a81d7d1bca58dfbb3157e8ae057a
```

```
git status --short
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/inventory-check.py
 M tests/test_bridge_run_design_ceiling.py
 M tests/test_header_run_parameters.py
```

## Assumed, not verified

- `_run_param_body_lines` normalizes CR and CRLF to LF before splitting on U+000A only · the brief requires direct calls with CRLF to match old `splitlines()` behaviour · step 1 keeps `test_header_currency.py` green.
- `run_parameters_values` was removed from `_INVENTORY_BRIDGE_NAMES` because `main()` never calls it · R2 requires the tuple to list only names `main()` uses · `test_r061_r2_inventory_check_refuses_through_its_guard_before_reading_the_run_parameters` passes for missing, unloadable, and old stubs.
- R6 uses per-line `AGENT_CEILING_RE.match` with `[ \t]` whitespace and no `re.M` rather than an alternate anchored pattern · either approach in the brief is linear · `test_r061_r2_the_fallback_of_a_whitespace_padded_file_takes_linear_time` passes within 2.0 s.
