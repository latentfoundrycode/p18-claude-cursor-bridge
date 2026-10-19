# CONFIG-B3b round 2 report

## Files changed

- `tools/dump-cli.py`
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `docs/BUILDER_NOTES.md`
- `handoff/CONFIG-B3b-r2-report.md`

## Summary

Round 2 hardens `tools/dump-cli.py` so list and tuple defaults get the same absolute-path rules as strings (including cross-drive `ValueError` from `relpath`), scans every reference string for repository, home, and current-directory paths after placeholders are applied, refuses docstring commands with no module docstring, wraps bridge imports in `sys.dont_write_bytecode`, uses `parse_args` with `allow_abbrev=False`, centralises JSON serialisation and Markdown action lines, and renders descriptions and usages in fenced blocks with one action line per argument showing JSON defaults including `null`; the committed reference files were regenerated and the CONFIG-B3b builder note was corrected for platform-neutral CRLF handling.

## Mutation checks

| Mutation | What caught it |
|----------|----------------|
| (h) judge only string defaults (skip lists) | `test_cfgb3b_r2_list_default_under_the_bridge_takes_the_placeholder`, `test_cfgb3b_r2_list_default_outside_the_bridge_is_refused` |
| (i) let `ValueError` from `relpath` propagate | `test_cfgb3b_r2_default_on_another_drive_is_refused_by_name` |
| (j) skip the string check for help texts | `test_cfgb3b_r2_help_or_description_holding_a_path_is_refused` |
| (k) render a `null` default as nothing | `test_cfgb3b_committed_reference_is_current`, `test_cfgb3b_r2_markdown_shows_each_action_whole` |
| (l) leave `sys.dont_write_bytecode` unset | `test_cfgb3b_r2_no_bytecode_is_written` |
| (m) `allow_abbrev=True` | `test_cfgb3b_r2_an_abbreviated_option_is_a_usage_error` |
| (n) return 0 from `--check` on a refusal | `test_cfgb3b_r2_check_exits_1_when_the_generator_refuses` (and other refusal tests in the same run) |

## Verification commands

```
$ python tools/dump-cli.py
(no output, exit 0)

$ python tools/dump-cli.py --check
(no output, exit 0)

$ python -m pytest tests/test_dump_cli.py -q
...............................................                          [100%]
47 passed in 25.82s

$ python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools
windowless-check: 36 file(s) scanned, 0 FAIL, 0 NOTE

$ python -m pytest tests -q
........................................................ss.............. [ 97%]
....................................                                     [100%]
1667 passed, 25 skipped in 321.60s (0:05:21)
```

## Assumed, not verified

Assumed, not verified: none.
