# CONFIG-B3b round 1 report

## Files changed

- `tools/dump-cli.py` (new)
- `docs/cli-reference.json` (generated)
- `docs/CLI_REFERENCE.md` (generated)
- `.github/workflows/tests.yml`
- `.githooks/pre-commit`
- `bridge/cursor-bridge/completion-check.py`
- `bridge/cursor-bridge/plan-check.py`
- `bridge/cursor-bridge/diagram-check.py`
- `bridge/cursor-bridge/inventory-check.py`
- `bridge/cursor-bridge/sync-check.py`
- `bridge/cursor-bridge/evaluate-reports.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/BUILDER_NOTES.md`
- `handoff/CONFIG-B3b-r1-report.md`

## Summary

Added `tools/dump-cli.py` to discover all 29 bridge command programs (module-level `__main__` block), classify argparse vs docstring sources via AST, import only programs with `build_parser()`, and write `docs/cli-reference.json` plus human-readable `docs/CLI_REFERENCE.md` with stable placeholders for bridge-local absolute defaults. Extracted `build_parser()` from six argparse programs without changing `main()` behaviour; wired `python tools/dump-cli.py --check` into CI (after the manifest step) and pre-commit; extended CI windowless scan to `.cursor/hooks`; regenerated the manifest after bridge edits.

## build_parser() extraction (behaviour unchanged)

Each extraction moves the existing `ArgumentParser` construction into `build_parser()` and replaces it in `main()` with `build_parser().parse_args()` (or `ap = build_parser(); a = ap.parse_args()` for evaluate-reports, preserving `ap` for `print_usage()`), so the same parser object with the same arguments, defaults, and subcommands is parsed exactly as before.

## Mutation checks

| Mutation | Caught by |
| --- | --- |
| (a) Drop line-ending normalisation in `--check` | None on this Windows host (`open(..., encoding="utf-8").read()` normalises CRLF before compare); would be caught by `test_cfgb3b_check_accepts_a_crlf_copy` where reads preserve CRLF |
| (b) Return 0 when files differ | `test_cfgb3b_check_names_the_one_stale_file`, `test_cfgb3b_check_counts_a_missing_file_as_stale`, `test_cfgb3b_pre_commit_blocks_a_stale_reference` |
| (c) Record real `workflow-check.py` defaults | `test_cfgb3b_output_is_identical_on_two_computers_and_holds_no_path`, `test_cfgb3b_argparse_entry_matches_its_parser[workflow-check.py]`, `test_cfgb3b_markdown_is_rendered_from_the_json`, `test_cfgb3b_committed_reference_is_current` |
| (d) Skip one command program | `test_cfgb3b_covers_every_command_program_and_no_library` (and downstream failures) |
| (e) Include `bridge_env.py` | `test_cfgb3b_covers_every_command_program_and_no_library`, `test_cfgb3b_committed_reference_is_current` |
| (f) Drop `required` from action entries | `test_cfgb3b_argparse_entry_matches_its_parser` (`ACTION_KEYS` assertion) |
| (g) Accept unknown arguments | `test_cfgb3b_usage_error_exits_2_and_writes_nothing` (all three parameter sets) |

## Verification commands

```
$ python tools/dump-cli.py
(exit 0, no output)

$ python tools/dump-cli.py --check
(exit 0, no output)

$ python -m pytest tests/test_dump_cli.py -q
37 passed in ~17s

$ python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools
windowless-check: 36 file(s) scanned, 0 FAIL, 0 NOTE

$ python tools/make-manifest.py
make-manifest: version 2026.10.18a, 107 files hashed, VERSION + MANIFEST.json written

$ python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
bridge-check: version 2026.10.18a (...) at .../bridge
bridge-check: 107 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.10.18a

$ python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass
RESULT: OK

$ python -m pytest tests -q
1657 passed, 25 skipped in 325.14s (0:05:25)
```

An earlier full-suite run failed once on `tests/test_bridge_run.py::test_an_orphan_left_at_a_normal_end_is_killed` (orphan survived); a single-test re-run passed before the final full suite above.

## Assumed, not verified

- `argparse.SUPPRESS` serialises via `json.dumps` as the string `==SUPPRESS==` on Python 3.12 and the builder's Python 3.12 · matches test helper `_jsonable` · confirmed by passing criterion 2 tests.
- Subcommand order follows `SubParsersAction.choices` insertion order on all supported Python versions · matches `evaluate-reports.py` loop order · would be confirmed by a failure if order diverged on 3.12 vs local.
- CRLF acceptance test on Windows does not exercise raw CRLF in `--check` because text-mode reads normalise newlines · observed mutation (a) passing locally · Linux CI would confirm CRLF path.
