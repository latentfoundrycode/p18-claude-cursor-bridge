# CONFIG-B3b round 3 report

## Files changed

- `tools/dump-cli.py`
- `docs/cli-reference.json`
- `docs/CLI_REFERENCE.md`
- `docs/BUILDER_NOTES.md`

## Summary

Round 3 fixes the reference generator so defaults are walked as structured values (lists, tuples, dicts, `os.PathLike`, and strings) instead of being checked through `json.dumps`, which had doubled backslashes and skipped dict contents on Windows. Path-fragment detection now uses `os.path.normcase` on both sides for the repository, home, and current working directory, and every reference string—including sub-command names, option strings, dests, and each string inside a default—is checked directly. Markdown action lines again use `- ` list markers and `; ` field separators via shared helpers for labels, action-string validation, and section rendering.

## Mutation checks

| Mutation | Caught by |
|----------|-----------|
| (o) default checked through `json.dumps` again | `test_cfgb3b_r3_a_path_inside_a_string_default_is_refused` |
| (p) skip dict values in the default walk | `test_cfgb3b_r3_a_dict_default_is_judged_like_a_list` |
| (q) compare fragments without `normcase` | `test_cfgb3b_r3_the_repository_folder_in_forward_slashes_is_refused`, `test_cfgb3b_r3_a_docstring_holding_the_repository_folder_is_refused` |
| (r) skip sub-command names | `test_cfgb3b_r3_a_subcommand_named_by_a_path_is_refused` |
| (s) drop the `- ` list marker | `test_cfgb3b_r3_each_action_is_a_list_item` |
| (t) let `os.PathLike` reach `json.dumps` | `test_cfgb3b_r3_a_pathlike_default_is_a_path` |

## Verification

```
$ python tools/dump-cli.py
(exit 0)

$ python tools/dump-cli.py --check
(exit 0)

$ python -m pytest tests/test_dump_cli.py -q
..................................................................       [100%]
66 passed in 42.90s

$ python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools
windowless-check: 36 file(s) scanned, 0 FAIL, 0 NOTE

$ python -m pytest tests -q
1696 passed, 25 skipped in 335.25s (0:05:35)
```

## Assumed, not verified

- `os.path.normcase` on this Windows runner folds both case and forward slashes into backslashes for path comparison · handoff Context states this behaviour · a Linux CI run would not exercise the skipped `test_cfgb3b_r3_the_home_folder_in_another_case_is_refused` case.
- Mutation (q) on a case-only mismatch is caught by `test_cfgb3b_r3_the_home_folder_in_another_case_is_refused` on Windows · not re-run in this session after the normcase removal · that test failed when normcase was removed in the same mutation batch as the forward-slash cases.
