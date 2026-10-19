# CONFIG-B3b round 4 report

## Files changed

- `tools/dump-cli.py`
- `docs/BUILDER_NOTES.md`

## Summary

Round 4 adds `path_canonical` (normcase plus collapsed slash runs), builds forbidden fragments from each of the three folders with and without the drive letter, walks dict keys and choices through `default_for_json` with distinct-string key checks and NaN or infinity refusal, checks the action `type` name in the string pass, and refuses an absolute default whose relpath to the bridge folder is `.` so a choice of `HERE` still fails while subpaths take the placeholder.

## Mutation check

| Mutation | Caught by |
| --- | --- |
| (u) compare without merging runs of separators | `test_cfgb3b_r4_a_folder_written_with_doubled_backslashes_is_refused`, `test_cfgb3b_r4_a_folder_written_with_doubled_forward_slashes_is_refused` |
| (v) drop the fragment without the drive | `test_cfgb3b_r4_the_home_folder_without_its_drive_is_refused` (parametrized `rest` and `"/mnt/" + d[:1].lower() + rest.replace(os.sep, "/")`; the Git Bash `/c/...` form still matches the whole-folder fragment) |
| (w) let a key that is not a string through | `test_cfgb3b_r4_a_dict_default_whose_keys_are_not_distinct_strings_is_refused` (integer-key cases; tuple and duplicate PathLike cases are caught by the duplicate-key check) |
| (x) skip the type field in the string check | `test_cfgb3b_r4_a_type_named_by_a_path_is_refused` |
| (y) check only the choices that are strings | none (non-string choices are refused during `default_for_json` before validation strings run) |
| (z) let a NaN default through | `test_cfgb3b_r4_a_default_that_is_not_a_json_number_is_refused` (all three parametrized values) |

## Verification

```
$ python tools/dump-cli.py
(exit 0, no stdout)

$ python tools/dump-cli.py --check
(exit 0, no stdout)

$ python -m pytest tests/test_dump_cli.py -q
89 passed in 65.96s (0:01:05)

$ python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools
windowless-check: 36 file(s) scanned, 0 FAIL, 0 NOTE

$ python -m pytest tests -q
1719 passed, 25 skipped in 373.32s (0:06:13)
```

## Assumed, not verified

- `os.path.normcase` on Windows lowercases drive letters and normalizes separators enough that Git Bash `/c/Users/...` fragments align with `splitdrive` tail `/Users/...` after canonical merge · round-4 home-without-drive tests passed on this Windows host · Linux CI would confirm cross-platform normcase behaviour.
- Mutation (y) has no dedicated test separating the choices string walk from the choices value walk · both paths refuse bad paths in this implementation · a test that only broke the post-walk string pass on a choice already accepted by the walk would confirm the advisory requirement in isolation.
