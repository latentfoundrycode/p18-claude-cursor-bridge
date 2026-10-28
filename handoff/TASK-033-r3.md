# TASK-033-r3: One reading of a squash subject — round 3, the fixes from round 2's reviews

## Objective
Round 2 (commit bd7c8bb on this branch) fixed most of round 1's findings. Its two reviews (Review A: REJECT; the security audit: FAIL) found what is still wrong, listed below with file:line in round 2's code. This round fixes each of them and nothing else. It is the increment's third round, the last the owner's ceiling allows without a class line: make every fix at its cause, and run every verification command before you finish. `handoff/TASK-033.md` and `handoff/TASK-033-r2.md` still govern everything this brief does not change: read both whole first, then this file. Where they differ, this file wins, then r2, then the first brief.

Satisfies: R-044 — the report cycle has a pace section for every project, computed by `pace-report.py`, read-only, from git and the launcher's and the guard's own records; the pace report and the plan check read a squash subject by one rule, one copy in `bridge_env.py`, under which a closing parenthesis merges an increment only when each of its comma-separated items is a bare ID (ISS-013). The full row is `docs/REQUIREMENTS.md` line 50.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_plan_check.py
- tests/test_pace_report.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-033-r3-report.md

Do not modify anything else.

**Read-only, the supervisor's:** `tests/test_task033_supervisor.py` (unchanged since `858da29`), `tests/test_task033_supervisor_r2.py` (unchanged since `a44c878`) and `tests/test_task033_supervisor_r3.py` (committed with a `supervisor:` subject before this run). Read them, run them, never edit them.

## Out of scope
- Everything the two earlier briefs put out of scope, unchanged.
- The reader's two form orders and Merge regexes (r2's settled S1).
- Formatting-only changes: change no line no Requirement below names.

## Context: what round 2 left, by finding
- **F1. The trailing parenthesis got wider and narrower** (`bridge_env.py:520-554`, `_trail_paren_inner`; both reviews). The version part ends in `(?:[ \t]+[\w.]*)?`, so a word after a dash now counts: `fix: y (TASK-031) - see notes`, `docs: x (TASK-050) - not done`, `x (TASK-1) - v1.2 extra` and `docs: x (TASK-050) — v2 wip (#7)` merge their IDs, where round 1's form merged nothing. These subjects feed `_claim_lapsed`, so a branch's claim lapses on an unmerged increment: the ISS-013 class. And the code strips only `" \t\r\n"` where `\s` matched any Unicode space, so `(TASK-1)` followed by a no-break space no longer merges. The `_TrailMatch` shim (`:540-554`) exists only to keep `.group(1)`. Test: `test_task033r3_the_trailing_parenthesis_accepts_exactly_round_1s_shapes` (round 1's regex is copied into it as the reference).
- **F2. One bad timestamp still crashes the run** (`pace-report.py:420-428`; both reviews). `fromisoformat` reads `0001-01-01T00:00:00+05:00` and `9999-12-31T23:59:59-05:00`; `astimezone` then raises `OverflowError`, which nothing catches. The r2 brief's list of exceptions missed it (the supervisor's mistake). Test: `..._a_timestamp_at_the_edge_of_the_calendar_is_skipped`.
- **F3. The 64 MiB cap caps nothing** (`pace-report.py:432-440`, `_read_line_capped`; both reviews). `f.readline()` is called with no size, so a line of any length is read whole and only then measured; no deadline check runs during that read. And `os.scandir` reads names starting with a dot, which round 1's `glob` skipped. Tests: `..._a_line_over_the_cap_is_skipped`, `..._a_hidden_session_file_is_not_read`.
- **F4. Lines split on more than `\n`** (security audit). `pace-report.py:139-149` with `:296`: `text=True` turns on universal newlines, so a lone `\r` inside a subject starts a new line (`docs: x\rTASK-050 later` merged TASK-050). `bridge_env.py:682` (TASK-032's reader, this increment's now): `p.stdout.splitlines()` splits on ` `, ` `, `\x85`, `\x0b`, `\x0c` and `\x1c`-`\x1e`, so `docs: x TASK-050` lapses a claim. Tests: `..._a_carriage_return_inside_a_subject_merges_nothing`, `..._the_reader_splits_git_output_on_newlines_only`.
- **F5. git's environment** (security audit). In a partial clone, the numstat `git log` fetches missing blobs lazily, which runs the project's `core.sshCommand`. Inherited `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and `GIT_OBJECT_DIRECTORY` make git read another repository than `-C` names. Tests: `..._inherited_git_variables_do_not_redirect_the_read`, `..._every_git_command_runs_without_lazy_fetch`.
- **F6. The ref is still ambiguous** (`pace-report.py:288`, `:576`; both reviews). The command is `["log", "main", "--format=..."]` with no `--`, while the message prints `git log main -- ...`. A tracked file or folder `main` fails the project. The r2 brief's own example (`git log main -- --format=...`) was wrong: it makes `--format` a pathspec (the supervisor's mistake). Test: `..._a_tracked_folder_named_main_is_no_failure`.
- **F7. A far-future commit crashes the run** (`pace-report.py:305`, `:343`; security audit). `datetime.fromtimestamp` sits outside any `try`: `GIT_COMMITTER_DATE="@33000000000 +0000"` raises `OSError` on Windows. Test: `..._a_commit_dated_past_the_calendar_is_skipped`.
- **F8. Stage IDs not filtered** (`pace-report.py:762-778`; both reviews). `_read_rounds_files` keeps any `rounds-*.json` name and `parse_review_name` is never applied: `rounds-STAGE-x y.json` is listed. Test: `..._a_stage_name_the_name_grammar_refuses_is_not_listed`.
- **F9. Brief reading** (Review A). `_ids_with_brief` (`pace-report.py:165-174`) counts `handoff/**/X.md`, where a brief is `handoff/<ID>.md` or `handoff/<ID>-r<N>.md` at the folder's top; the letter rule (`:178-179`, `:188-190`) decides "has a brief" with `os.path.isfile`, not the tracked list. The merge week is the last merging commit in git's log order (`:311`, `:593`), not the earliest committer time. Tests: `..._a_brief_in_a_sub_folder_is_no_brief`, `..._the_first_merge_is_the_earliest_commit_time`.
- **F10. One copy of the bare-ID test** (`bridge_env.py:563-571`; both reviews). `_parenthesis_bare_item` copies the hyphen-and-digit test of `_subject_leading_ids` (`:509`) instead of reusing it; the r2 report says "reused".
- **F11. The regression test over main** (`tests/test_plan_check.py:266`; Review A). `assert fset - nset <= {"TASK-031"}` also passes when nothing is lost, so the test passes with the parenthesis back to "any ID inside" (Review A ran that mutant over all 191 commits). `sys.path.insert(0, CB)` (`:171-172`) is never undone.
- **F12. Left over** (Review A). The unreachable `if "-r" in token: return False` / `return False` (`pace-report.py:191-193`) are still there; the r2 report says removed. `if status != "ok"` at `:569-570` and `:585-586` can no longer be reached. The module docstring (`:13`, `:26`) still says exit 1 is a timeout and that merged counts only IDs that have a brief. `_has_rounds_reading` (`:240-257`) re-implements `_err_rounds`' scan (`:209-225`).

### A reading the supervisor settles (Review A's S2)
The r2 brief's Requirement 9 named "a launcher row with `brief`" as a reading of an increment's rounds; the build plan's clause (b) defines the rounds as the largest of three readings (reports, `.err` files, the guard's rounds file), and a launcher row is none of them. Clause (b) holds: `_has_rounds_reading`'s three sources are right, and a launcher row is no reading of rounds.

## Requirements
1. **The trailing parenthesis (F1, F10).** The linear parser accepts exactly what round 1's `\(([^()]*)\)\s*(?:[-—–]\s*v?[\w.]+\s*)?(?:\(#\d+\))?\s*$` accepted, searched over the line: the last-matching parenthesis, an optional version that is one dash, any spaces, an optional `v` and one run of `[\w.]` and nothing after it but spaces and an optional `(#digits)`, every "space" being what Python's `\s` matches (`str.isspace()`; strip with an argument-less `rstrip()`/`lstrip()`). It returns the inner text as a `str` or `None`; remove `_TrailMatch` and update the two call sites. One helper, used by both `_subject_leading_ids` and the parenthesis rule, holds the test "fully matches the pattern, holds a hyphen and a digit".
2. **Timestamps (F2).** In the transcript validator, catch `OverflowError` with the exceptions `fromisoformat` and the UTC conversion raise (`ValueError`, `TypeError`, `OverflowError`), around the parse, the conversion and the week; a record that raises any of them is skipped.
3. **Line cap and names (F3).** A module-level `LINE_CAP = 64 * 1024 * 1024` (in the unit of the reads you make). Read each line with `f.readline(LINE_CAP + 1)`; when the result is longer than `LINE_CAP` and does not end in a newline, read on with `f.readline(65536)`, checking the deadline at every chunk, until a chunk ends in a newline or the file ends, and skip the whole line. Inside a key folder, never enter a folder or read a file whose name starts with `.`, as `glob` does not.
4. **Lines split on `\n` only (F4).** pace-report reads git's output as bytes, decodes it as UTF-8 with `errors="replace"`, splits records on `\x00` and lines on `\n` only. In `bridge_env.py`, `squash_merged_ids` (`:682`) splits on `\n` only, so its callers, `_claim_lapsed` and `plan-check.py`, read a subject whole: its own default runner captures bytes (no `text=True`, whose universal newlines turn a lone `\r` into a line end) and decodes them as UTF-8 with `errors="replace"`; output from a runner a caller passes in is split the same way, decoded first if it is bytes. Its signature and return values stay.
5. **git's environment (F5).** The environment pace-report gives every git command is a copy of its own with `GIT_NO_LAZY_FETCH=1` and `GIT_OPTIONAL_LOCKS=0` set and `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR` and `GIT_NAMESPACE` removed.
6. **The ref (F6).** The commit read is `git log --format=<the format> refs/heads/main --` (the options before the ref, `--` after it), and its failure line prints that command exactly as run (without `-c` and `-C`).
7. **Commit times (F7).** Every `datetime.fromtimestamp` of a commit time catches `(OverflowError, OSError, ValueError)`; such a commit is skipped, the others counted.
8. **Stage IDs (F8).** A stage ID from a rounds file is listed only when `bridge_env.parse_review_name` reads it; it is still printed ASCII-escaped.
9. **Briefs and merge weeks (F9).** A brief is a tracked path `handoff/<name>.md` with no further `/`, whose `<name>` `parse_review_name` reads; the letter rule asks the same tracked list. An increment's merge week is the week of the merging commit with the smallest committer time.
10. **Your tests (F11).** In `tests/test_plan_check.py`'s regression test over `main`: 9f6ace6's answer loses exactly `{"TASK-031"}` (`==`), every other commit's answer equals the former rule's, and the test asserts 9f6ace6 was visited; replace `sys.path.insert` with `monkeypatch.syspath_prepend`. Add no other test unless a Requirement here needs one the supervisor's files lack.
11. **Left over (F12).** Remove the unreachable lines at `:191-193` and the unreachable `status != "ok"` branches; make the module docstring say that exit 1 is a git command that failed (timed out, exited non-zero or could not start) and that with an untracked `handoff/` the merged column counts every ID the reader finds; make `_has_rounds_reading` call `_err_rounds` and the report and rounds readers instead of scanning again.

## Acceptance criteria
- [ ] `python -m pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py -q -p no:cacheprovider` passes whole.
- [ ] `git diff --quiet 858da29 -- tests/test_task033_supervisor.py`, `git diff --quiet a44c878 -- tests/test_task033_supervisor_r2.py` and `git diff --quiet HEAD -- tests/test_task033_supervisor_r3.py` each exit 0.
- [ ] `python -m pytest tests/test_plan_check.py tests/test_pace_report.py -q -p no:cacheprovider` passes.
- [ ] `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider` passes.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/plan-check.py bridge/cursor-bridge/pace-report.py` reports no FAIL.
- [ ] `python tools/dump-cli.py --check` passes, and `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` ends OK.
- [ ] Run from the Workspace root, `python bridge/cursor-bridge/plan-check.py` still runs: same exit code as before, no traceback.
- [ ] No new dependency; `pace-report.py` and `bridge_env.py` stay ASCII.

## Constraints
All of `handoff/TASK-033.md`'s and `handoff/TASK-033-r2.md`'s Constraints hold, with these changes:
- **Verification commands.** Run exactly these, from the Workspace root, never the whole suite:
  - `python -m pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py -q -p no:cacheprovider`
  - `python -m pytest tests/test_plan_check.py tests/test_pace_report.py -q -p no:cacheprovider`
  - `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider`
  - `git diff --quiet 858da29 -- tests/test_task033_supervisor.py`, `git diff --quiet a44c878 -- tests/test_task033_supervisor_r2.py`, `git diff --quiet HEAD -- tests/test_task033_supervisor_r3.py` (each prints nothing; check that each exit code is 0)
  - `python bridge/cursor-bridge/plan-check.py`
  - `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/plan-check.py bridge/cursor-bridge/pace-report.py`
  - `python tools/dump-cli.py --check` (regenerate with `python tools/dump-cli.py` only if it fails)
  - `python tools/make-manifest.py`, last, after every program edit
  - `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` (must end OK)
- **Mutation check, by hand.** After the tests pass, apply each mutation below, one at a time; run the three supervisor files and your two files; restore the code before the next. List each with the test that caught it, or "survived".
  1. The version part accepting one more word after the version.
  2. The trailing spaces stripped as `" \t"` only.
  3. `OverflowError` dropped from the timestamp catch.
  4. `f.readline()` with no size.
  5. `splitlines()` back in `squash_merged_ids`.
  6. `GIT_NO_LAZY_FETCH` not set.
  7. `--` dropped after the ref.
  8. The merge week from git's log order.
  9. The regression test's `==` back to `<=` (in your test, then restored), with the parenthesis back to "any ID inside".
- **Your report states only what the diff shows.** For each finding, name the lines that changed; for a claim like "reused" or "removed", the reviewers read the diff against it.

## Done
Your report is the file `handoff/TASK-033-r3-report.md`, which you write as you go. When you finish, it holds: every file you changed; what you changed, with file:line, under the finding's number (F1 to F12); every verification command with its pass, fail and skip counts; the mutation list with what caught each; every test file outside your Scope that fails under your change, and at which lines, without editing it; a one-paragraph summary; and a section headed exactly `Assumed, not verified`, one item per line (what you assumed · why · what would confirm it), or `Assumed, not verified: none`. An assumption about what a standard-library call raises or reads is such an item unless a test of yours shows it.

Your last message is the summary and the report file's path, and nothing follows it.
