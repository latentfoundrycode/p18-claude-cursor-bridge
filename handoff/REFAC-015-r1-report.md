# REFAC-015 round 1 report

## Files changed

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `handoff/REFAC-015-r1-report.md` (this file)

## Summary

Refactored `roster-check.py` in three parts without behaviour change: added nested `_rebuild_entry` as the sole caller of `_rebuild_line_open` (dropped unused `rb_model` parameter) and `_rebuild_needs_new_branch`, returning `(rb_line, rebuild, end_marker, new_branch_git_fail)` where `new_branch_git_fail` is `True` when the new-branch question was asked and `_rebuild_needs_new_branch` returned `None`; added module-level `_unreadable` and merged the two `head_fail` exits in `built_families`; routed `built_by`'s run-log loop through `_parse_run_line`. Regenerated `MANIFEST.json` via `make-manifest.py`.

## Behaviour

Each helper delegates to the same logic as before (same REBUILD/FAIL paths, same unreadable causes, same line filtering); call sites still print FAIL and return 1, assign `rebuild` and `profile_rebuild_end`, and keep site C's ordering unchanged, so printed lines, exit codes, `built_families` dicts, and `built_by` answers stay the same.

## Git at start

Working tree: clean (no output from `git status --short`).

```
git rev-parse HEAD
```

```
203352f19f42ce3fa491acc8fa2db68442c5fc2d
```

## Requirement 1 (before edit)

```
git diff --stat 8b03c32 -- bridge/cursor-bridge/roster-check.py
```

```
(empty)
```

```
git grep -n -F -e "_rebuild_line_open(" -e "_rebuild_needs_new_branch(" -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:572:def _rebuild_needs_new_branch(counted, branch, cwd):
bridge/cursor-bridge/roster-check.py:1184:    def _rebuild_line_open(r_id, r_fam, rb_model, builder_id):
bridge/cursor-bridge/roster-check.py:1348:                    rb_line, rb_model = _rebuild_line_open(r_id, r_fam, built_model, b_id)
bridge/cursor-bridge/roster-check.py:1351:                        nb = _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd)
bridge/cursor-bridge/roster-check.py:1370:                        rb_line, rb_model = _rebuild_line_open(r_id, r_fam, built_model, b_id)
bridge/cursor-bridge/roster-check.py:1372:                        nb = _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd)
bridge/cursor-bridge/roster-check.py:1408:                        rb_line, rb_model = _rebuild_line_open(r_id, r_fam, built_model, b_id)
bridge/cursor-bridge/roster-check.py:1410:                        nb = _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd)
```

```
git grep -n -F -e "cannot read the families that built this branch" -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:1175:        print("FAIL  cannot read the families that built this branch (%s)" % cause)
bridge/cursor-bridge/roster-check.py:1353:                            print("FAIL  cannot read the families that built this branch (git)")
bridge/cursor-bridge/roster-check.py:1374:                            print("FAIL  cannot read the families that built this branch (git)")
bridge/cursor-bridge/roster-check.py:1412:                            print("FAIL  cannot read the families that built this branch (git)")
```

```
git grep -n -F -e "new branch" -e rebuild_with -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:1349:                    rebuild = {"built_by": rb_model, "rebuild_with": b_id}
bridge/cursor-bridge/roster-check.py:1356:                            profile_rebuild_end = "new branch"
bridge/cursor-bridge/roster-check.py:1371:                        rebuild = {"built_by": rb_model, "rebuild_with": b_id}
bridge/cursor-bridge/roster-check.py:1377:                            profile_rebuild_end = "new branch"
bridge/cursor-bridge/roster-check.py:1409:                        rebuild = {"built_by": rb_model, "rebuild_with": b_id}
bridge/cursor-bridge/roster-check.py:1415:                            profile_rebuild_end = "new branch"
bridge/cursor-bridge/roster-check.py:1472:        elif end == "new branch":
bridge/cursor-bridge/roster-check.py:1473:            print(base + "; run the same rebuild under a new branch name (new branch)")
```

```
git grep -n -w -e unreadable -e unreadable_cause -e head_fail -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:469:    """Families that built the branch, or empty / unknown / unreadable.
bridge/cursor-bridge/roster-check.py:472:    status, families, unknown_causes, unreadable_cause, parsing_rows, counted_rows, rebuild_end.
bridge/cursor-bridge/roster-check.py:482:              "unreadable_cause": None, "parsing_rows": [], "counted_rows": [],
bridge/cursor-bridge/roster-check.py:487:    branch_name, head_fail = _branch_from_head(cwd)
bridge/cursor-bridge/roster-check.py:488:    if head_fail == "git":
bridge/cursor-bridge/roster-check.py:489:        result["status"] = "unreadable"
bridge/cursor-bridge/roster-check.py:490:        result["unreadable_cause"] = "git"
bridge/cursor-bridge/roster-check.py:492:    if head_fail == "detached":
bridge/cursor-bridge/roster-check.py:493:        result["status"] = "unreadable"
bridge/cursor-bridge/roster-check.py:494:        result["unreadable_cause"] = "detached"
bridge/cursor-bridge/roster-check.py:500:        result["status"] = "unreadable"
bridge/cursor-bridge/roster-check.py:501:        result["unreadable_cause"] = rep_fail
bridge/cursor-bridge/roster-check.py:507:            result["status"] = "unreadable"
bridge/cursor-bridge/roster-check.py:508:            result["unreadable_cause"] = fail
bridge/cursor-bridge/roster-check.py:511:            result["status"] = "unreadable"
bridge/cursor-bridge/roster-check.py:512:            result["unreadable_cause"] = "main"
bridge/cursor-bridge/roster-check.py:516:            result["status"] = "unreadable"
bridge/cursor-bridge/roster-check.py:517:            result["unreadable_cause"] = "git"
bridge/cursor-bridge/roster-check.py:523:        result["status"] = "unreadable"
bridge/cursor-bridge/roster-check.py:524:        result["unreadable_cause"] = open_fail
bridge/cursor-bridge/roster-check.py:531:        result["status"] = "unreadable"
bridge/cursor-bridge/roster-check.py:532:        result["unreadable_cause"] = "git"
bridge/cursor-bridge/roster-check.py:1173:    if set_status == "unreadable":
bridge/cursor-bridge/roster-check.py:1174:        cause = bset["unreadable_cause"]
```

```
git grep -n -F -e "json.loads(" -e "_parse_run_line(" -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:176:            e = json.loads(line)
bridge/cursor-bridge/roster-check.py:410:def _parse_run_line(line_b):
bridge/cursor-bridge/roster-check.py:420:        e = json.loads(text)
bridge/cursor-bridge/roster-check.py:445:        parsed = _parse_run_line(line_b)
bridge/cursor-bridge/roster-check.py:666:        parsed = _parse_run_line(line_b)
```

```
git grep -n -w -e _unreadable -e _rebuild_entry -- bridge
```

```
(exit 1, no output)
```

```
git grep -n -w -e _rebuild_line_open -e _rebuild_needs_new_branch -e _parse_run_line -e _unreadable -e _rebuild_entry -- tests
```

```
(exit 1, no output)
```

## Pytest before edit

Commit: `203352f19f42ce3fa491acc8fa2db68442c5fc2d`, working tree clean.

```
python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_alt.py tests/test_improve_roster_launch.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_hotfix25a_roster_launcher.py tests/test_program_roster_sign_in.py
```

```
281 passed, 3 skipped in 172.14s (0:02:52)
```

## Post-edit verification

```
python tools/make-manifest.py
```

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

```
python tools/dump-cli.py --check
```

```
(empty output, exit 0)
```

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

```
bridge-check: version 2026.11.24a (2026-11-26 03:26) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>/bridge/cursor-bridge
```

```
git diff --numstat -- bridge/cursor-bridge/VERSION
```

```
(empty)
```

```
git diff --numstat -- bridge/cursor-bridge/roster-check.py
```

```
45	58	bridge/cursor-bridge/roster-check.py
```

## Requirement 1 / acceptance (after edit)

```
git grep -n -F -e "_rebuild_line_open(" -e "_rebuild_needs_new_branch(" -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:553:def _rebuild_needs_new_branch(counted, branch, cwd):
bridge/cursor-bridge/roster-check.py:1165:    def _rebuild_line_open(r_id, r_fam, builder_id):
bridge/cursor-bridge/roster-check.py:1178:        rb_line, rb_model = _rebuild_line_open(r_id, r_fam, builder_id)
bridge/cursor-bridge/roster-check.py:1183:            nb = _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd)
```

```
git grep -n -F -e "cannot read the families that built this branch" -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:1156:        print("FAIL  cannot read the families that built this branch (%s)" % cause)
bridge/cursor-bridge/roster-check.py:1344:                        print("FAIL  cannot read the families that built this branch (git)")
bridge/cursor-bridge/roster-check.py:1363:                            print("FAIL  cannot read the families that built this branch (git)")
bridge/cursor-bridge/roster-check.py:1399:                            print("FAIL  cannot read the families that built this branch (git)")
```

```
git grep -n -F -e "new branch" -e rebuild_with -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:1179:        rebuild = {"built_by": rb_model, "rebuild_with": builder_id}
bridge/cursor-bridge/roster-check.py:1187:                end_marker = "new branch"
bridge/cursor-bridge/roster-check.py:1459:        elif end == "new branch":
bridge/cursor-bridge/roster-check.py:1460:            print(base + "; run the same rebuild under a new branch name (new branch)")
```

```
git grep -n -w -e unreadable -e unreadable_cause -e head_fail -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:462:    result["status"] = "unreadable"
bridge/cursor-bridge/roster-check.py:463:    result["unreadable_cause"] = cause
bridge/cursor-bridge/roster-check.py:468:    """Families that built the branch, or empty / unknown / unreadable.
bridge/cursor-bridge/roster-check.py:471:    status, families, unknown_causes, unreadable_cause, parsing_rows, counted_rows, rebuild_end.
bridge/cursor-bridge/roster-check.py:481:              "unreadable_cause": None, "parsing_rows": [], "counted_rows": [],
bridge/cursor-bridge/roster-check.py:486:    branch_name, head_fail = _branch_from_head(cwd)
bridge/cursor-bridge/roster-check.py:487:    if head_fail:
bridge/cursor-bridge/roster-check.py:488:        return _unreadable(result, head_fail)
bridge/cursor-bridge/roster-check.py:1154:    if set_status == "unreadable":
bridge/cursor-bridge/roster-check.py:1155:        cause = bset["unreadable_cause"]
```

```
git grep -n -F -e "json.loads(" -e "_parse_run_line(" -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:169:        e = _parse_run_line(line_b)
bridge/cursor-bridge/roster-check.py:403:def _parse_run_line(line_b):
bridge/cursor-bridge/roster-check.py:413:        e = json.loads(text)
bridge/cursor-bridge/roster-check.py:438:        parsed = _parse_run_line(line_b)
bridge/cursor-bridge/roster-check.py:647:        parsed = _parse_run_line(line_b)
```

```
git grep -n -w -e _unreadable -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:461:def _unreadable(result, cause):
bridge/cursor-bridge/roster-check.py:488:        return _unreadable(result, head_fail)
bridge/cursor-bridge/roster-check.py:493:        return _unreadable(result, rep_fail)
bridge/cursor-bridge/roster-check.py:498:            return _unreadable(result, fail)
bridge/cursor-bridge/roster-check.py:500:            return _unreadable(result, "main")
bridge/cursor-bridge/roster-check.py:503:            return _unreadable(result, "git")
bridge/cursor-bridge/roster-check.py:508:        return _unreadable(result, open_fail)
bridge/cursor-bridge/roster-check.py:514:        return _unreadable(result, "git")
```

```
git grep -n -w -e _rebuild_entry -- bridge/cursor-bridge/roster-check.py
```

```
bridge/cursor-bridge/roster-check.py:1177:    def _rebuild_entry(r_id, r_fam, builder_id, ask_new_branch):
bridge/cursor-bridge/roster-check.py:1342:                    rb_line, rebuild, end_marker, new_branch_git_fail = _rebuild_entry(r_id, r_fam, b_id, family_only_unknown)
bridge/cursor-bridge/roster-check.py:1361:                        rb_line, rebuild, end_marker, new_branch_git_fail = _rebuild_entry(r_id, r_fam, b_id, True)
bridge/cursor-bridge/roster-check.py:1397:                        rb_line, rebuild, end_marker, new_branch_git_fail = _rebuild_entry(r_id, r_fam, b_id, True)
```

## Pytest after edit

Commit: `203352f19f42ce3fa491acc8fa2db68442c5fc2d`, working tree had uncommitted changes (`M bridge/cursor-bridge/MANIFEST.json`, `M bridge/cursor-bridge/roster-check.py`, plus this report after write).

```
python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_alt.py tests/test_improve_roster_launch.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_hotfix25a_roster_launcher.py tests/test_program_roster_sign_in.py
```

```
281 passed, 3 skipped in 173.99s (0:02:53)
```

## Git at end

```
git status --short
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
```

```
git diff --stat
```

```
 bridge/cursor-bridge/MANIFEST.json   |   4 +-
 bridge/cursor-bridge/roster-check.py | 103 +++++++++++++++--------------------
 2 files changed, 47 insertions(+), 60 deletions(-)
```

```
git rev-parse HEAD
```

```
203352f19f42ce3fa491acc8fa2db68442c5fc2d
```

## Not changed (noted only)

`built_by` previously decoded with default UTF-8; `_parse_run_line` uses strict UTF-8 — brief states both skip the same lines and tests stayed green.

## Assumed, not verified

Assumed, not verified: none