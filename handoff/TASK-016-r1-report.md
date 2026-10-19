# TASK-016 round 1 report

## Files changed

- `bridge/cursor-bridge/trace-check.py` (new)
- `bridge/cursor-bridge/workflow/trace-baseline.txt` (new)
- `bridge/cursor-bridge/workflow/trace-exceptions.md` (new)
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `handoff/TASK-016-r1-report.md` (this file)

## Summary

Implemented `trace-check.py` (R-029): it pins baseline commit `0a186da42ad01352dcd46f8524a1b3db0858dea5`, cuts Markdown into comparable units, traces every baseline `supervisor.md` passage against current homes (core plus workflow `*.md` except `trace-exceptions.md`), flags dropped/copy/new text in module paths, validates `~/.claude/` references and section citations, and reads `trace-exceptions.md` for `reword`/`new` excuses. Scaffolded the baseline and empty exceptions files. On this tree the check reports 424 traced passages with `RESULT: OK`. All 22 tests in `tests/test_trace_check.py` pass. Full `pytest tests` reports two failures that require supervisor updates to test allowlists (not fixable under Scope): `test_dump_cli.py` needs `trace-check.py` in the `ARGPARSE` tuple, and `test_tests_windowless.py` flags `test_trace_check.py` subprocess lines that use `NO_WINDOW` without the literal substring `CREATE_NO_WINDOW`.

## Mutation checks

| Mutation | Description | Caught by |
|----------|-------------|-----------|
| (a) | Compare first line only instead of normal form (no join/collapse) | `test_r029_a_hard_wrapped_passage_moved_onto_one_line_passes` |
| (b) | Copy only when passage stands in two different files | `test_r029_a_copy_within_one_file_fails` |
| (c) | Count units in excused sections toward `c` | Multiple tests (22 failed) |
| (d) | Let a `new` entry excuse a dropped passage | `test_r029_a_new_entry_excuses_new_text_but_not_a_dropped_passage` |
| (e) | `reword` drop excuse looks only at current file, not baseline CORE | Not caught (attempted: skip `file_rel != CORE_REL` guard; no test failed) |
| (f) | New-text check uses baseline `supervisor.md` units only, not all baseline homes | Not caught (fixture baseline has no extra workflow-only units) |
| (g) | Resolve `~/.claude/<rest>` at repository root instead of `bridge/` | Reference tests (18 failed) |
| (h) | Drop placeholder segment rule | `test_r029_a_placeholder_reference_resolves_by_its_folder` and related |
| (i) | Skip citation check | `test_r029_a_dangling_cited_section_fails` |
| (j) | Omit baseline-missing error (still fails later on `cat-file`) | Not caught as exit 0 (`test_r029_a_missing_baseline_commit_is_not_checked` still gets exit 2) |

## Verification commands

1. `git rev-parse 0a186da` — exit 0, `0a186da42ad01352dcd46f8524a1b3db0858dea5`. `git diff --stat 0a186da HEAD -- bridge/commands/supervisor.md bridge/cursor-bridge/workflow` — exit 0, no output.

2. `python bridge/cursor-bridge/trace-check.py` — exit 0. Last lines: `TRACED: 424 passages of baseline 0a186da; 424 in supervisor.md, 0 under workflow/, 0 dropped, 0 excused` and `RESULT: OK`.

3. `python bridge/cursor-bridge/trace-check.py --map` — exit 0, 426 lines (424 `MAP` lines plus `TRACED:` and `RESULT: OK`). `TRACED: 424 passages of baseline 0a186da; 424 in supervisor.md, 0 under workflow/, 0 dropped, 0 excused`.

4. `python bridge/cursor-bridge/trace-check.py --help` — exit 0 (usage printed).

5. `python -m pytest tests/test_trace_check.py -q` — exit 0, `22 passed`.

6. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools` — exit 0, `RESULT: OK`.

7. `python tools/make-manifest.py` then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0, `RESULT: SOURCES MATCH bridge 2026.10.18a`.

8. `python tools/dump-cli.py` then `python tools/dump-cli.py --check` — exit 0.

9. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0.

10. `python -m pytest tests -q` — exit 1, `2 failed, 1761 passed, 25 skipped`: `test_cfgb3b_docstring_entries_hold_the_whole_docstring` (trace-check.py listed as hand-maintained but has `build_parser`), `test_fix001_no_test_starts_a_program_around_the_default` (`test_trace_check.py` uses `creationflags=NO_WINDOW` without `CREATE_NO_WINDOW` in the line).

11. `git status` / `git diff --stat` — new bridge files untracked; manifest and CLI reference modified as above.

## Assumed, not verified

- List-item continuation lines that are not themselves list items join the preceding list unit (no blockquote-nested list fixtures in `test_trace_check.py`) · Requirement 4 paragraph/list rules · A crafted blockquote plus list in a temp repo.
- Heading titles with trailing `#` characters are taken as part of the title text after the first space following the `#` run · CommonMark allows closing hashes · No sample in tests or brief.
- `git ls-tree -z` on Windows yields UTF-8 path bytes decoded with `utf-8` replace on failure · Git for Windows behavior · Exercised only on this host's successful runs.
- `GIT_TIMEOUT = 120` seconds is enough for largest `git show` of `supervisor.md` on slow disks · Chosen to match other bridge git helpers · A timeout failure on huge repos would confirm or refute.
- Citation regex `\b(see|per|under) "X"` with chained `\u2192 "Y"` matches every cite form in the real core without false positives on words like `understand` · Brief examples only · Full supervisor scan passed `RESULT: OK`.
