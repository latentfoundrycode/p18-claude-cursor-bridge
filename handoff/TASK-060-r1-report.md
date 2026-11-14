# TASK-060 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/conformance-check.py`
- `bridge/cursor-bridge/cursor-agent.shim`
- `bridge/cursor-bridge/MANIFEST.json`
- `docs/diagrams/D-004-context-dfd.md`
- `tests/test_account_keys.py`
- `tests/test_bridge_run.py`
- `tests/test_conformance_check.py`
- `handoff/TASK-060-r1-report.md`

## Summary

R-080 is implemented in the scoped bridge sources and tests: key files naming home variables are refused before `bridge-run: started`, `SECRET_LIKE` in `bridge_env.py` is the single name test (wider patterns, `stripped_env(kind=...)` withholding secret-like `CURSOR_*` from test and driver runs), conformance-check and `cursor-agent.shim` read that test, D-004's "Stripped environment" note matches the code, and supervisor acceptance plus extended tests are green at commit `03f8c1c59dd93ec9e34d2d0934dddd5258fa0918` with uncommitted changes listed below.

## Requirements (1–14)

1. `key_file_home_refusal` and pre-`started` reads in `bridge-run.py` (`main`, named suite block and the block before `bridge-run: started`) refuse any `--key-file` line whose name is one of the six home variables, case-insensitive, exit 125, name only.
2. Non-home key files still merge after the strip via the existing `env.update(keys)` path; missing or inside-Workspace files still raise through `key_file_env` with exit 125.
3. `SECRET_LIKE` and `secret_like` in `bridge_env.py` add bounded `PAT`, `CREDS`, `AUTH`, plus `DATABASE_URL` and `SSH_AUTH_SOCK`.
4. Only `bridge_env.py` defines the pattern; launcher, conformance-check, and shim consume it (shim by parallel awk).
5. `stripped_env(env=None, kind=None)` sets `keep_cursor` for builder/review (default and `is_agent` paths); test/driver/watch stripped runs pass `kind=` from `bridge-run.py` line 2289.
6. `ENV_SECRET` removed from `conformance-check.py`; floors call `bridge_env.secret_like` / `SECRET_LIKE`.
7. Keys floor continues `SECRET_NAME` OR `bridge_env.secret_like` on each `.env` name (lines 1218–1221).
8. Session NOTE uses `bridge_env.secret_like(k)`; inventory floor uses `SECRET_LIKE.search` without prefix exclusion.
9. `cursor-agent.shim` awk line 25 mirrors the new pattern; comment lines 21–24 updated.
10. `WITHHELD` / `KEPT` in `tests/test_account_keys.py` updated; `fold_whole_names` in `test_r055_d004_the_withheld_names_are_the_notes` aligns D-004 words with the pattern.
11. D-004 line 8 only: note lists new forms, CURSOR kept/withheld by kind, key-file refusal after `Passed:`; no "The program release adds" clause.
12. Conformant `make_workspace` uses `DATABASE_HOST=localhost`; non-conformant assert expects `DATABASE_URL` on the keys floor.
13. R-080 cases added in `tests/test_bridge_run.py`, `tests/test_account_keys.py`, `tests/test_conformance_check.py`.
14. `python tools/make-manifest.py` run; `VERSION` unchanged; `dump-cli.py --check` clean.

## Existing tests changed (10–12)

- `tests/test_account_keys.py` — `WITHHELD` / `KEPT` and `fold_whole_names` in `test_r055_d004_the_withheld_names_are_the_notes` for J11 and D-004 agreement.
- `tests/test_conformance_check.py` — conformant `.env` host name and non-conformant keys-floor assert for `DATABASE_URL`.
- `tests/test_release_t_strip.py` — not edited; comment at lines 49–50 is now partly stale (still says `CURSOR_*` is kept for every stripped run).

## Verification commands

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

```
...........................................................              [100%]
59 passed in 24.01s
```

```
........................                                                 [100%]
24 passed in 16.03s
```

```
........................                                                 [100%]
24 passed in 9.33s
```

```
...................                                                      [100%]
19 passed in 10.95s
```

```
.....................................................                    [100%]
53 passed in 10.10s
```

```
441 passed, 4 skipped in 88.79s (0:01:28)
```

```
374 passed in 344.50s (0:05:44)
```

```
bridge-check: version 2026.11.12a (2026-11-14 20:06) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

```
 bridge/cursor-bridge/MANIFEST.json        |  10 +-
 bridge/cursor-bridge/bridge-run.py        |  28 ++++-
 bridge/cursor-bridge/bridge_env.py        |  20 +++-
 bridge/cursor-bridge/conformance-check.py |  11 +-
 bridge/cursor-bridge/cursor-agent.shim    |   7 +-
 docs/diagrams/D-004-context-dfd.md        |   2 +-
 handoff/TASK-060.md                       | 193 ++++++++++++++++++++++++++++++
 tests/test_account_keys.py                |  54 ++++++++-
 tests/test_bridge_run.py                  |  28 +++++
 tests/test_conformance_check.py           |  29 ++++-
 10 files changed, 357 insertions(+), 25 deletions(-)
```

```
03f8c1c59dd93ec9e34d2d0934dddd5258fa0918
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/conformance-check.py
 M bridge/cursor-bridge/cursor-agent.shim
 M docs/diagrams/D-004-context-dfd.md
 M tests/test_account_keys.py
 M tests/test_bridge_run.py
 M tests/test_conformance_check.py
```

`python tools/dump-cli.py --check` produced no output (reference current).

Pytest counts above are for commit `03f8c1c59dd93ec9e34d2d0934dddd5258fa0918`; working tree held uncommitted changes to the nine implementation files plus this report (`git status --short`).

`test_shim_withholds_exactly_what_the_python_recipe_does` was not skipped (Git Bash `sh` on PATH).

## Mutations (M1–M8)

- **M1** — Unbounded `PAT` in `SECRET_LIKE`: `FAILED tests/test_program_strip_names.py::test_r080_the_name_test_tells_the_boundary_cases_apart[PATH]`
- **M2** — Drop `CREDS` or `SSH_AUTH_SOCK`: not run
- **M3** — Remove case fold: not run
- **M4** — Keep `CURSOR_*` for test runs: `FAILED tests/test_program_strip_names.py::test_r080_a_secret_like_cursor_name_is_withheld_from_a_test_run`
- **M5** — Drop one home name from refusal: not run
- **M6** — Case-sensitive home refusal: not run
- **M7** — Refusal after `started` or skip watch: not run
- **M8** — Shim missing one new form: not run

## Assumed, not verified

- Git Bash `awk` on Windows treats `(^|_)PAT(_|$)` like Python for every name in `NOT_SECRET` and `NEW_FORMS` · acceptance and account-keys tests passed on this host · a fuller matrix on other shells would confirm.
- Where `conformance-check.py` loads the stand-in module without `bridge_env.py`, inventory and session floors skip or degrade · `_load_bridge_env` unchanged per brief · not exercised offline here.
- No `cursor-agent` build needs a `CURSOR_*` name other than those kept for builder/review besides `CURSOR_TRACE_LEVEL` · only names exercised in tests · a live agent enumeration would confirm.