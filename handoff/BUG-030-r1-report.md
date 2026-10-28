# BUG-030 round 1 builder report

## Summary

Fixed all eight stage B5 round-1 program defects in scope-check, roster-check, bridge-run, mutation-run, bridge_env, and review-guard: builder scope windows include slot wait time, exit-123 slot rows no longer affect roster built-by or class-line accounting, the launcher re-reads and compares brief sha256 after acquiring the heavy slot (using the path captured before command resolution), mutation-run maps import failures to exit 3 and copies conftest.py files into checkpoint archives, report filenames are excluded from brief tokens, and review-guard input matching uses ID boundaries. Regenerated MANIFEST.json via make-manifest.py.

## Files changed

- bridge/cursor-bridge/scope-check.py
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/mutation-run.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json (regenerated)

## Causes

1. **scope-check `builder_windows`:** each window end adds numeric `waited` (or 0) before `seconds` and the 120 s slack.
2. **roster-check `built_by`:** skips builder rows with `slot` equal to `"not free"`.
3. **bridge-run `builder_review_refusal`:** rows with `slot` `"not free"` no longer add to `class_used`.
4. **bridge-run `main`:** after the slot is taken, re-hashes the brief at `brief_recheck_path` (same path as the brief rule, stored before `resolve()`); mismatch or unreadable file releases the slot and returns 125 with no log row.
5. **mutation-run imports:** `tomllib` and `bridge_env` load inside `run_main` with ImportError mapped to stderr `mutation-run: internal error - …` and exit 3.
6. **mutation-run `archive_checkpoint`:** copies each working-tree `conftest.py` on the path to every listed new test via `conftest_paths`, deduplicated, before bytecode removal.
7. **bridge_env `HANDOFF_REPORT_NAME`:** also matches `<ID>-report.md` and `-r<N><letter>-report.md` in addition to `-r<N>-report.md`.
8. **review-guard `review_inputs`:** matches the ID only at word boundaries per the brief rule (not substring `str(nnn) in name`).

## Verification

1. `python -m pytest tests/test_bug030.py tests/test_task032_supervisor_launcher.py tests/test_mutation_run_supervisor.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_hotfix25a_roster_launcher.py -q` — exit 0, `213 passed in 333.41s`
2. `python -m pytest` (16 named reproduction tests) `-v` — exit 0, `16 passed in 17.11s`
3. `python tools/make-manifest.py` — exit 0, `make-manifest: version 2026.10.25a, 144 files hashed, VERSION + MANIFEST.json written`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0, `RESULT: SOURCES MATCH bridge 2026.10.25a`
5. `python tools/dump-cli.py --check` — exit 0 (no regeneration needed)
6. `git diff --quiet HEAD --` (five test files) — exit 0; `git diff --quiet -- bridge/cursor-bridge/VERSION` — exit 0; `git status --porcelain`:

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/mutation-run.py
 M bridge/cursor-bridge/review-guard.py
 M bridge/cursor-bridge/roster-check.py
 M bridge/cursor-bridge/scope-check.py
?? handoff/BUG-030-r1-report.md
```

## Assumed, not verified

- An untracked conftest.py on the way to a new test can reach `archive_checkpoint` without `validate_tracked_copy` refusing it first · the brief asked to confirm this · only the tracked-new-test path was exercised by the reproduction tests, which passed for both new and changed root conftest.py.
- `make-manifest.py` leaves `bridge/cursor-bridge/VERSION` byte-identical to HEAD · brief Context asked to confirm · `git diff --quiet -- bridge/cursor-bridge/VERSION` exited 0 after regeneration.
