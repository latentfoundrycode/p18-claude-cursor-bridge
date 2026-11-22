# TASK-075 round 1 report (R-095)

## Files changed or created

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `make-manifest.py`)
- `docs/cli-reference.json` (via `dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `dump-cli.py`)
- `handoff/TASK-075-r1-report.md`

## Summary

`roster-check.py` now detects the Cursor CLI's own sign-in line as a whole-line prefix match on stdout or stderr in `probe` and in `--record-failure`, prints the fixed `SIGN-IN` message, writes no roster state, and exits 5; the module docstring exit list and regenerated CLI reference describe exit 5 for a signed-out tool. All eight supervisor acceptance tests and all existing `test_roster_check.py` / `test_roster_check_a4.py` cases pass unedited.

## R1–R8

- **R1** — `tool_sign_in_line_present` (lines 182–188): splits text with `splitlines()`, strips each line with `strip()`, true when `line.strip().startswith(SIGN_IN_PREFIX)` and `SIGN_IN_PREFIX` is exactly `Error: Authentication required. Please run 'agent login' first` (line 91).
- **R2** — `probe` (212–213) returns `PROBE_SIGN_IN` when the line appears on stdout or stderr; `main` (576–579) prints `SIGN_IN_LINE` and returns 5 without resolving. The probe stops after the **first** model probe that hits sign-in (the builder of the first profile), not after both models of that profile.
- **R3** — `record_failure` (396–398) checks sign-in before model validation and before any `save_state`; prints `SIGN_IN_LINE`, returns 5, changes nothing.
- **R4** — All other paths in `probe`, `classify_failure`, and `record_failure` unchanged; connection `ESCALATE` exit 5 preserved.
- **R5** — Docstring probe note (lines 26–27) and exit list (line 65); `dump-cli.py` regenerated roster-check entry only.
- **R6** — No new options, env vars, or dependencies; output ASCII.
- **R7** — `make-manifest.py` run after edits; version `2026.11.12a`; `VERSION` diff empty.
- **R8** — `bare LF 0` check; CRLF retained.

## Builder-appended tests

None.

## Mutation self-check

### M1 — sign-in line matched anywhere in text instead of as a whole line

Before:

```python
    for line in text.splitlines():
        if line.strip().startswith(SIGN_IN_PREFIX):
            return True
    return False
```

After:

```python
    return SIGN_IN_PREFIX in (text or "")
```

```
1 failed, 19 passed in 7.71s
```

Caught by: `test_r095_the_tools_whole_line_quoted_inside_a_model_sentence_is_counted_as_today`

### M2 — probe stdout shape not checked (stderr only)

Before:

```python
    if tool_sign_in_line_present(p.stdout or "") or tool_sign_in_line_present(p.stderr or ""):
```

After:

```python
    if tool_sign_in_line_present(p.stderr or ""):
```

```
1 failed, 19 passed in 8.06s
```

Caught by: `test_r095_probe_sign_in_line_on_stdout_with_exit_0`

### M3 — `--record-failure` counts (and saves) before the sign-in check

Before:

```python
    if tool_sign_in_line_present(text):
        print(SIGN_IN_LINE)
        return 5
    if model not in roster_models(roster):
```

After:

```python
    if model not in roster_models(roster):
        ...
    kind, pat = classify_failure(text)
    roster.setdefault("failures", {})[model] = {"count": 1, "last": stamp(now_utc())}
    save_state(path, roster)
    if tool_sign_in_line_present(text):
        print(SIGN_IN_LINE)
        return 5
```

```
9 failed, 11 passed in 7.87s
```

Caught by: `test_r095_record_failure_reads_the_sign_in_line_in_a_stderr_file`

### M4 — sign-in exit is 1 instead of 5

Before:

```python
        return 5
```

After (in `record_failure` sign-in branch):

```python
        return 1
```

```
3 failed, 17 passed in 7.87s
```

Caught by: `test_r095_record_failure_reads_the_sign_in_line_in_a_stderr_file`

## Verification commands

Commit for counts: `6a1434df93e1db8486fcf2b8747397f1d413805b`. Working tree held uncommitted changes (see step 11).

### 1. git status --short

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

### 2. python tools/make-manifest.py

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 3. python tools/dump-cli.py

```
(no stdout)
```

### 4. python -m pytest -p no:cacheprovider -q tests/test_program_roster_sign_in.py tests/test_roster_check.py tests/test_roster_check_a4.py

```
....................                                                     [100%]
20 passed in 7.55s
```

### 5. python tools/dump-cli.py --check

```
exit code 0
(no stdout)
```

### 6. python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet

```
bridge-check: version 2026.11.12a (2026-11-22 06:27) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
exit code 0
```

### 7. python -c "open('bridge/cursor-bridge/roster-check.py','rb').read().decode('ascii'); print('ascii ok')"

```
ascii ok
```

### 8. python -c "d=open('bridge/cursor-bridge/roster-check.py','rb').read(); print('bare LF', d.count(b'\n')-d.count(b'\r\n'))"

```
bare LF 0
```

### 9. git diff -- bridge/cursor-bridge/VERSION

```
(no output)
```

### 10. git diff --stat

```
 bridge/cursor-bridge/MANIFEST.json   |  4 ++--
 bridge/cursor-bridge/roster-check.py | 32 ++++++++++++++++++++++++++++----
 docs/CLI_REFERENCE.md                |  8 +++++---
 docs/cli-reference.json              |  2 +-
 4 files changed, 36 insertions(+), 10 deletions(-)
```

### 11. git rev-parse HEAD && git status --short

```
6a1434df93e1db8486fcf2b8747397f1d413805b
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

## Notes

The module docstring still says "within 2 hours" for consecutive failures (line 43) while `FAILURE_WINDOW_HOURS = 8` (line 80); left unchanged per brief.

## Assumed, not verified

Assumed, not verified: the live Cursor CLI will keep printing lines that begin exactly with `Error: Authentication required. Please run 'agent login' first` — matching is prefix-only on a whole line — because only the fixture and the brief describe the shape; a future wording change would need a new fixture capture.
Assumed, not verified: when the real tool is signed out in `-p -f` mode it may emit that line on stdout with exit 0 as well as on stderr with a non-zero exit — acceptance tests cover both shapes via the stand-in only.
Assumed, not verified: error files written by the launcher place the tool's line at the start of a physical line — R1 tests line starts after strip, not substring match inside a line.