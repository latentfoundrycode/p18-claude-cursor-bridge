# TASK-086a round 4 report

## Files changed

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `docs/BUILDER_NOTES.md` (one dated line appended)
- `handoff/TASK-086a-r4-report.md`

## Summary

Round 4 corrects the family-deviation probe judgement (Review A, round 3, B1): the builder, `review_b`, and `review_b_alt` are still probed once each in that order, but each answer is kept separately. Under reason `family`, an alternate that answers resolves with the deviation regardless of whether `review_b` answered; an alternate that does not answer takes the existing REBUILD path and judges `review_b` only on its first-probe answer, with no second probe of `review_b`. The module docstring and CLI reference describe this behaviour; everything else from round 3 is unchanged.

## Requirements (R1-R16)

- R1: `built_families(run_log, branch=None, cwd=None, roster=None, profiles=None)` at line 468.
- R2: `_apply_drop_rule()` lines 346-375 unchanged.
- R3: `built_families()` empty outside git unchanged.
- R4: `FAIL  cannot read the families that built this branch (git)` unchanged.
- R5: Unknown-cause lines unchanged from round 3.
- R6: Profile loop in `main()` lines 1307-1434; table unchanged except probe judgement at 1387-1422.
- R7: Collision skip unchanged.
- R8: `DEVIATION  review_b is gpt-5.6-sol-high instead of grok-4.7-medium (family)` unchanged.
- R9: REBUILD closing forms at lines 1466-1472 unchanged.
- R10: `repair_record()` unchanged.
- R11: `--review-alt` refusal paths unchanged.
- R12: Builder, `review_b`, and `review_b_alt` each probed once; judgements at lines 1387-1422 use separate `ok_b`, `ok_rb`, and `ok_alt` flags per the correction.
- R13: `built_by()`, `family_of()`, `pool_of()`, `probe()` unchanged.
- R14: `_git_run()` unchanged.
- R15: Module docstring lines 30-35 updated; `dump-cli.py` regenerated.
- R16: MANIFEST regenerated.

`rebuild.built_by` is unchanged from round 3 (latest counted or parsing builder row of `review_b`'s family, else `built_by()`'s answer).

## Scratch tests

no scratch test file

## Mutation code points (N1-N32)

- N1-N30: as round 3 report (unchanged code paths).
- N31: `main()` lines 1391-1392 and 1419-1420 (`ok_rb` held from the single `review_b` probe for family-deviation REBUILD) — `test_task086a_an_alternate_silent_under_the_family_deviation_judges_review_b_on_its_first_answer`, `test_task086a_both_reviewers_silent_under_the_family_deviation_skip_the_profile`.
- N32: absence of a second `_probe_roles([("review_b", r_id)])` after the family-deviation REBUILD line (round 3 had it at line 1416) — `test_task086a_review_b_silent_under_the_family_deviation_leaves_the_alternate_resolved`, `test_task086a_an_alternate_silent_under_the_family_deviation_judges_review_b_on_its_first_answer`.

## Missing acceptance cases

none found

## Commands

### 1. git status --short (before edit)

```
```

### 2. Checkpoint acceptance tests (expected 3 failed, 3 skipped for round-4 cases)

```
3 failed, 120 passed, 3 skipped in 90.65s (0:01:30)
```

Failing ids: `test_task086a_review_b_silent_under_the_family_deviation_leaves_the_alternate_resolved`, `test_task086a_an_alternate_silent_under_the_family_deviation_judges_review_b_on_its_first_answer`, `test_task086a_both_reviewers_silent_under_the_family_deviation_skip_the_profile`.

### 3. python tools/dump-cli.py

```
(no output)
```

### 3b. python tools/dump-cli.py --check

```
(exit 0, no output)
```

### 4. python tools/make-manifest.py

```
make-manifest: version 2026.11.23a, 148 files hashed, VERSION + MANIFEST.json written
```

### 5. git status --short (after manifest)

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

### 6. python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_alt.py

```
123 passed, 3 skipped in 78.70s (0:01:18)
```

```
SKIPPED [1] tests\test_improve_roster_alt.py:1501: no symbolic link here: [WinError 1314] A required privilege is not held by the client: ...
SKIPPED [1] tests\test_improve_roster_alt.py:1501: no symbolic link here: [WinError 1314] A required privilege is not held by the client: ...
SKIPPED [1] tests\test_improve_roster_alt.py:1572: a file name holding a line feed is POSIX-only; CI's Linux job runs it
```

### 7. Checkpoint regression batch

```
458 passed in 304.26s (0:05:04)
```

### 8. Second regression batch

```
155 passed in 199.27s (0:03:19)
```

### 9. python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet

```
bridge-check: version 2026.11.23a (2026-11-24 18:56) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.23a <Workspace>/bridge/cursor-bridge
```

### 10. python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 11. ASCII check

```
ascii ok
```

### 12. git diff --stat HEAD

```
 bridge/cursor-bridge/MANIFEST.json   |  4 ++--
 bridge/cursor-bridge/roster-check.py | 40 ++++++++++++++++++------------------
 docs/BUILDER_NOTES.md                |  2 ++
 docs/CLI_REFERENCE.md                |  7 +++++--
 docs/cli-reference.json              |  2 +-
 5 files changed, 30 insertions(+), 25 deletions(-)
```

### 13. git rev-parse HEAD and git status --short

```
06461af1ee1bfea1fdaab516a865bfea7371fba4
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

Counts above belong to commit `06461af1ee1bfea1fdaab516a865bfea7371fba4` with uncommitted changes listed in step 13.

## Assumed, not verified

- The POSIX-only case `test_task086a_a_record_line_split_only_at_its_line_feed` and the two symbolic-link repair cases were not exercised on this host (skipped with reasons quoted in step 6); their behaviour is unchanged from round 3 code paths outside the probe block.
- CI Linux git and Windows git agree on the family-deviation resolve outcomes exercised here — only scratch repos on this host were run.