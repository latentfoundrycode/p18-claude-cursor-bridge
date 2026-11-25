# TASK-086b round 3 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json`

## Summary

Round 3 fixes `branch_of` so `git rev-parse --abbrev-ref HEAD` output is read as raw bytes and decoded as UTF-8 with replacement, with any failure returning `None` instead of raising; on Windows this lets branch names whose UTF-8 bytes are undefined in the system code page be read for the two review refusals, the brief-rule branch check, and builder row logging without a launch traceback. The two refusal call sites were unchanged because `branch_of` no longer raises and existing unreadable-set handling already covers a `None` branch. All 116 acceptance tests and the Done regression slices pass unchanged.

## Requirements (round 3)

- **1 (branch read as git prints it):** `branch_of` (2580–2593) runs the same git argument list windowless under `GIT_TIMEOUT`, omits `text=True`, decodes `stdout` as UTF-8 with `errors="replace"`, returns the stripped name on exit 0 and `None` otherwise, and catches `Exception` so the function never raises.
- **2 (no traceback from refusals' branch read):** `_deviation_allows_builder_review` (1359) and `review_family_refusal` (2639) still call `branch_of` unchanged; a `None` branch closes the deviation exception (`1359–1361`) and lets `built_families` yield unreadable/`unknown` outcomes that existing refusal text already handles (`2648–2650`, `2663–2664`).
- **3 (other callers unchanged):** `builder_review_refusal` (1490–1494) and the run row's `log_branch` (3605) use the same `branch_of`; ASCII branches behave as before, and the wide-branch acceptance cases get the UTF-8 name git stores.

## Scratch tests

no scratch test file

## Mutation code points

| Label | Function / lines | Expected test id |
|-------|------------------|------------------|
| M21 | `branch_of` 2583–2593 | `test_r3_a_branch_name_outside_the_code_page_is_read_and_judged` |
| M21 | `branch_of` 2583–2593 | `test_r3_a_deviation_on_such_a_branch_opens_the_builder_models_review` |
| M21 | `branch_of` 2583–2593 | `test_r3_a_builder_launch_on_such_a_branch_writes_its_name_and_both_keys` |

(M1–M20 unchanged from round 2 at their post-round-2 lines except where line numbers shifted by three after `branch_of`; no launcher logic for those labels was edited this round.)

## Missing acceptance cases

none

## `claude --version`

```
--: line 1: claude: command not found
```

## Commands and output

### Step 1 — `git status --short`

```
(no output)
```

### Step 2 — checkpoint pytest (before edits)

```
3 failed, 113 passed in 72.49s (0:01:12)
```

Failing ids:

```
tests/test_improve_roster_launch.py::test_r3_a_branch_name_outside_the_code_page_is_read_and_judged
tests/test_improve_roster_launch.py::test_r3_a_deviation_on_such_a_branch_opens_the_builder_models_review
tests/test_improve_roster_launch.py::test_r3_a_builder_launch_on_such_a_branch_writes_its_name_and_both_keys
```

### Step 3 — `python tools/dump-cli.py` then `python tools/dump-cli.py --check`

```
(no output)
```

(exit code 0 for both)

### Step 4 — `python tools/make-manifest.py`

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

### Step 5 — `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

(`bridge/cursor-bridge/VERSION` not listed; `git restore` not run)

### Step 6 — acceptance pytest after edits

```
116 passed in 74.70s (0:01:14)
```

### Step 7 — regression slice 1

```
494 passed, 4 skipped in 485.90s (0:08:05)
```

Skip reasons (`-rs`):

```
SKIPPED [1] tests\test_bridge_run_slot.py:411: POSIX special files
SKIPPED [1] tests\test_bridge_run_slot.py:930: POSIX links and permission bits
SKIPPED [1] tests\test_bridge_run_slot.py:1125: POSIX permission bits
SKIPPED [1] tests\test_hotfix24a_heavy_slots.py:1102: POSIX file modes
```

### Step 8 — regression slice 2

```
280 passed, 3 skipped in 231.99s (0:03:51)
```

Skip reasons (`-rs`, paths shortened):

```
SKIPPED [1] tests\test_improve_roster_alt.py:1520: no symbolic link here: [WinError 1314] A required privilege is not held by the client: '<tmp>/.../planted.txt' -> '<tmp>/.../ws/run/launcher/runs.damaged.jsonl'
SKIPPED [1] tests\test_improve_roster_alt.py:1520: no symbolic link here: [WinError 1314] A required privilege is not held by the client: '<tmp>/.../elsewhere.jsonl' -> '<tmp>/.../ws/run/launcher/runs.jsonl'
SKIPPED [1] tests\test_improve_roster_alt.py:1591: a file name holding a line feed is POSIX-only; CI's Linux job runs it
```

### Step 9 — `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.24a (2026-11-25 18:30) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>/bridge/cursor-bridge
```

### Step 10 — `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 11 — `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json | 4 ++--
 bridge/cursor-bridge/bridge-run.py | 7 ++++---
 2 files changed, 6 insertions(+), 5 deletions(-)
```

(`docs/cli-reference.json` and `docs/CLI_REFERENCE.md` appear in `git status --short` with no content diff against HEAD; help text unchanged.)

### Step 12 — non-ASCII in `bridge-run.py` diff

No non-ASCII characters were added in `bridge-run.py`; the diff is ASCII-only.

### Step 13 — `claude --version`

```
--: line 1: claude: command not found
```

### Step 14 — `git rev-parse HEAD` and `git status --short`

```
64ec8ee3532fa5f05b3037d5bbd23762571e38d2
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

Results above are for commit `64ec8ee3532fa5f05b3037d5bbd23762571e38d2` with uncommitted changes listed in step 14. No `tests/test_task086b_scratch_` file. `bridge/cursor-bridge/VERSION` not listed.

## Assumed, not verified

Assumed, not verified: none