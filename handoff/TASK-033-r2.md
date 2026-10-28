# TASK-033-r2: One reading of a squash subject — round 2, the fixes from round 1's reviews

## Objective
Round 1 (commit 80c2a8b on this branch) built the one squash-subject reader in `bridge_env.py`, `plan-check.py`'s import of it and `pace-report.py`. Its two reviews (Review A and the security audit) found defects, listed below with their file:line in round 1's code. This round fixes each of them and nothing else. `handoff/TASK-033.md` still governs everything this brief does not change: read it whole first, then this file. Where the two differ, this file wins.

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
- handoff/TASK-033-r2-report.md

Do not modify anything else.

**Read-only, the supervisor's:** `tests/test_task033_supervisor.py` (unchanged since commit `858da29`) and `tests/test_task033_supervisor_r2.py` (committed with a `supervisor:` subject before this run). Read them, run them, never edit them. They are the supervisor's acceptance tests of this increment; the second holds one test per finding below, each naming the finding.

## Out of scope
- Everything `handoff/TASK-033.md` puts out of scope, unchanged.
- `tests/test_dump_cli.py`: round 1's change to it is done; do not touch it again.
- `bridge-run.py`, `review-guard.py`, `evaluate-reports.py` and every other program: read them, do not change them. Do not import from `review-guard.py`.
- The reader's two form orders (see Requirement 1): they stay as round 1 wrote them.

## Context

### What round 1 left, by finding (the reviews' own words, condensed)
Each item names the round-1 line and the supervisor's test in `tests/test_task033_supervisor_r2.py` that fails on it today.
- **R1. The parenthesis under the grammar's pattern** (`bridge_env.py:531-549`, `_parenthesis_merged_ids`). Under `GRAMMAR_ID_PATTERN` any capitalised word fully matches the pattern, so `docs: x (TASK-031, Scope) (#5)` merges {TASK-031, Scope} and `docs: x (B3, TASK-031)` merges {B3, TASK-031}. The grammar is the pattern `_claim_lapsed` uses, so the ISS-013 class survives there. Tests: `test_task033r2_grammar_parenthesis_with_a_capitalised_word_merges_nothing`, `..._of_bare_ids_still_merges`.
- **R2. A quadratic regex** (`bridge_env.py:520`, `_TRAIL_SUBJECT_RX`). After `\)`, the two adjacent `\s*` (the second inside the optional version group, the third before `$`) make a subject `x (a)` followed by 20,000 spaces take 0.76 s. Test: `..._a_long_whitespace_run_is_read_in_linear_time`.
- **R3. plan-check.py's git call has no limit** (`plan-check.py:179`). Test: `..._plan_check_gives_its_git_command_a_limit`.
- **R4. pace-report.py's own commit parsing** (`pace-report.py:235-253`). It runs `git log` with `%ct%x1f%s%x1f%(trailers...)` and splits each output line on `\x1f`, so a second `Merges:` trailer line (it has no separator) is dropped, and a subject holding `\x1f` is split into two subjects (`docs: x<US>TASK-050` merges TASK-050). Tests: `..._two_merges_trailer_lines_both_count`, `..._a_separator_character_in_a_subject_merges_nothing`.
- **R5. A missing ref read as a timeout** (`pace-report.py:103-112`, `:236-238`, `:425-429`, `:675`). Every non-zero git exit and every `OSError` is reported as `git command timed out after 120 seconds`. A Workspace with no `main` says it timed out. Test: `..._a_missing_main_is_no_timeout`.
- **R6. A project's git configuration runs programs** (`pace-report.py:103-112`, `:417`). git runs under the other project's `.git/config`; a `core.fsmonitor` there ran a script on the `git ls-files` call. Test: `..._a_projects_git_configuration_runs_no_program`.
- **R7. Default roots exit 2** (`pace-report.py:661-664` against `:670`). The "no project, exit 2" check runs over the default roots too, so the "(not present on this computer)" line is unreachable; run from outside the bridge's tree, `bridge_root()` falls back to the current folder, which then fails the check. Test: `..._a_default_root_missing_or_no_project_is_a_named_line`.
- **R8. The untracked-handoff rule** (`pace-report.py:123-131`, `:134-145`, `:441-442`, `:565`). `_handoff_untracked` returns True when any one `.md` under `handoff/` is untracked, so one new uncommitted brief beside a tracked folder prints `n/a (handoff/ untracked)` everywhere; `_ids_with_brief` reads `os.listdir`, not tracked files; in untracked mode the merged column still counts only IDs with a brief file; the total row prints `0` instead of `n/a`. Tests: `..._one_new_brief_beside_a_tracked_handoff_is_no_untracked_handoff`, `..._untracked_handoff_counts_every_id_the_reader_finds`.
- **R9. Malformed transcript lines crash the run** (`pace-report.py:358-387`, `_read_tokens`; both reviews). A line `[1,2]`, a `message` that is a string, a `usage` that is a list, `"input_tokens": Infinity` (an `OverflowError`), a message id that is a dict (unhashable) each raise; output is written only at the end, so one such line loses every project. `int(usage.get(f) or 0)` also sums a negative value, truncates a float and accepts a string of Arabic-Indic digits. Test: `..._malformed_transcript_lines_are_skipped`.
- **R10. Timestamps sliced, weeks not in UTC** (`pace-report.py:76-78`, `:374-379`). `_iso_week` uses `dt.date()` without converting to UTC, and the transcript time is parsed through `ts[:19]`. Test: `..._a_timestamp_with_an_offset_is_read_in_utc`.
- **R11. The header does not say which sources were found** (`pace-report.py:486-504`). `token_keys` is assigned and never printed. Test: `..._the_header_says_which_session_sources_were_found`.
- **R12. The session walk is outside the limit and follows links** (`pace-report.py:326-348`; both reviews). The two globs run before the deadline is set, and `**` with `recursive=True` follows directory symlinks and junctions out of the key folder; one huge line is read whole. Tests: `..._the_session_walk_follows_no_link`, `..._the_session_walk_is_inside_the_limit`, `..._a_timed_out_session_read_keeps_exit_0`.
- **R13. Non-ASCII names printed** (`pace-report.py:581-611`, `:657`). Stage IDs from `rounds-<name>.json` file names and the project's folder name can put non-ASCII on stdout. Test: `..._non_ascii_names_are_printed_ascii`.
- **R14. Bytecode written** (`pace-report.py:42`, `:58-63`; both reviews). Importing `bridge_env` and loading `evaluate-reports.py` write `__pycache__` beside the program. Test: `..._a_run_writes_no_bytecode`.
- **R15. Rounds and days on odd records** (`pace-report.py:442`, `:481`; Review A's C4). The merge week is taken from the newest merging commit; a start later than the merge gives negative days; a merged increment with no round reading prints `0 / 0`. Tests: `..._an_increment_merged_twice_counts_in_its_first_merge_week`, `..._a_start_after_the_merge_gives_no_negative_days`, `..._a_merged_increment_with_no_reading_of_rounds_is_left_out_of_the_rounds`.
- **R16. Builder tests.** `tests/test_pace_report.py::test_r044_usage_error_on_bad_weeks` passes against the checkpoint's code, where `pace-report.py` does not exist (Python exits 2 on a missing script): it proves nothing. `os.chdir` without restoring the folder at `tests/test_plan_check.py:175`, `:193`, `:207` and `tests/test_pace_report.py:146`. Subprocess calls with no `timeout` at `tests/test_plan_check.py:60`, `:83`, `:129`, `:169`, `:170`, `:199`, `:204` and `tests/test_pace_report.py:68`, `:77`, `:78`. The `# windowless: visible-ok` comments on the test files' launches are untrue (the windows serve no user; `tests/conftest.py`'s default makes them windowless): the round-1 brief asked for `windowless-check.py` over the test files, which was the supervisor's mistake, corrected in the acceptance criteria below. The regression test over `main` (`tests/test_plan_check.py:197-214`) compares sets, so it still passes with the narrowing reverted (c81c5a3 merges TASK-031 on its own).
- **R17. Dead and copied code** (`pace-report.py:55` `_ERR_R_RX` unused; `:161-163` unreachable). `plan-check.py`'s `merged_ids` now returns `None` on `OSError`, where it raised before (an unrequested change).

### The reader's two orders stay (Review A's S1, settled)
Round 1's reader tries the forms in one order under the plan pattern (subject, plan Merge, parenthesis, trailer) and another under the grammar's (grammar Merge, subject, parenthesis, trailer), with a Merge regex of each. That is what `handoff/TASK-033.md` Requirement 2 asked: the plan pattern gives `plan-check.py`'s former answers (the three divergences), the grammar gives every answer TASK-032's tests pin. The supervisor keeps it and records it; do not change the orders or the Merge regexes. What changes is the parenthesis rule under the grammar (R1).

## Requirements
1. **The reader (R1 to R3, R17).**
   - Under either pattern, a parenthesis item is a bare ID only when it fully matches the pattern **and** holds a hyphen and a digit: the test `_subject_leading_ids` already applies (`bridge_env.py:509-510`); reuse that test, do not write a second. `R-nnn` stays a bare item that merges nothing under the plan pattern. So under the grammar `(TASK-031, Scope)`, `(B3, TASK-031)` and `(Scope)` merge nothing, and `(TASK-100, R-027)`, `(BUG-018)` and `( TASK-100 ,  BUG-018 )` merge their IDs.
   - Rewrite `_TRAIL_SUBJECT_RX` so that it reads the same subjects in time linear in the subject's length; the forms it accepts stay exactly the same (`(...)` at the end, an optional `- v1.2` style version, an optional `(#nn)`, trailing spaces).
   - `plan-check.py`'s `merged_ids` gives its git command `timeout=120` and returns `None` on `subprocess.TimeoutExpired`; on `OSError` it raises again, as before round 1.
2. **pace-report's commits (R4, R15).** Read the Workspace's `main` so that each commit's subject and trailer lines reach the one reader whole and are never split on a character a subject can hold. For example: `git log main -- --format=%x00%H %ct%n%s%n%(trailers:key=Merges,valueonly)`, split on `\x00`, the first line of each record matched by `^[0-9a-f]{40} ([0-9]+)$` and read with `int`, the rest passed to `bridge_env.squash_merged_ids_from_lines`. An increment's merge week is the week of the **earliest** commit that merges it.
3. **handoff/ tracked or not (R8).** `handoff/` is untracked when `git ls-files handoff/` lists nothing. "An ID that has a brief" is read from that list of tracked files, never from `os.listdir`. With `handoff/` untracked, the merged column counts every ID the reader finds in the week's subjects (no brief needed), and the total row's started and rounds cells print `n/a (handoff/ untracked)` too.
4. **git: status and configuration (R5, R6).**
   - The git helper returns the outcome apart: done, timed out, failed with an exit code, or could not start. A timeout prints `git command timed out after 120 seconds: <command>`; a non-zero exit prints `git command failed (exit <n>): <command>`; a start failure prints `git command could not start: <command>`. Each fails that project: its section holds the line instead of its table, the other projects are printed, and the run exits 1. Print no git stderr text (it can hold paths). Write the ref unambiguously (`git log main -- ...`).
   - Every git command pace-report runs is started as `git -c core.fsmonitor=false -c core.untrackedCache=false -c log.showSignature=false -C <Workspace> ...`, with `--no-textconv --no-ext-diff` on `log` and `diff` commands that print a diff or numstat, and with `GIT_OPTIONAL_LOCKS=0` in a copy of the environment passed to it.
5. **Project roots (R7).** The exit-2 check applies to roots given on the command line only. With no root given, a default root that does not exist prints the section heading and the line `(not present on this computer)`; one that exists and is no project prints the heading and `(not a project: no Workspace/.git)`; neither changes the exit code. `bridge_root()`'s answer is a default root like the others, so a run from outside the bridge's tree names that folder in a line and exits 0.
6. **Transcripts (R9, R10).**
   - A line is used only when `json.loads` gives a dict whose `message` is a dict, whose `message.id` is a `str`, whose `message.usage` is a dict, and whose `timestamp` is a `str` that `datetime.fromisoformat` reads (a trailing `Z` read as `+00:00`; a time without a zone read as UTC). Each of the four usage fields must be absent or an `int` (`type(v) is int`, so never a `bool`) between 0 and 10**12 inclusive; a record with any field outside that is skipped whole. Anything else skips the line; nothing raises. Catch nothing broader than the exceptions `json.loads` and `fromisoformat` raise on bad text (`ValueError`, `TypeError`, `RecursionError`).
   - Every time read by the program, for every source, is converted to UTC before its ISO week is taken. Times are never parsed by slicing a string.
7. **The token sources line (R11).** With `--tokens`, the section prints one line before its table: `Token sources: <n> session file(s), <m> subagent file(s)` — the counts of `<key>/*.jsonl` and `<key>/**/subagents/*.jsonl` files found over the project's keys. Never print a key (a key is a path of this computer).
8. **The session walk (R12).** The 120-second session limit starts before the folders are walked and covers the walk and the reading. Walk with `os.scandir` (no `glob` with `**`), never entering an entry that is a symlink or a junction (`entry.is_symlink()`, `entry.is_junction()` where it exists, `entry.is_dir(follow_symlinks=False)`), checking the deadline at every directory entered, every file opened and every line read. Read lines with a cap of 64 MiB: a longer line is skipped to its end, unread. On the limit: empty tokens cells, the line naming the project and the limit, exit unchanged (0 when nothing else failed).
9. **Output, writes, odd records (R13 to R15).**
   - Every name printed that comes from a file or folder name (a project's folder name, a stage ID from a rounds file) is printed ASCII-escaped (`name.encode("ascii", "backslashreplace").decode("ascii")`); a stage ID is listed only when `bridge_env.parse_review_name` accepts it.
   - `sys.dont_write_bytecode = True` is set in `pace-report.py` before it imports `bridge_env` or loads `evaluate-reports.py`.
   - An increment whose start is later than its merge is left out of the mean days (no negative number is printed). A merged increment with no reading of its rounds (no report, `.err` file, launcher row with `brief` or rounds record) is left out of the rounds mean and maximum; a week whose merged increments have no reading prints blank rounds cells.
   - Remove `_ERR_R_RX` and the unreachable lines in `_letter_err_belongs`.
10. **Your tests (R16).** In `tests/test_pace_report.py` and `tests/test_plan_check.py`:
    - make `test_r044_usage_error_on_bad_weeks` assert what only `pace-report.py` prints (the usage line naming `--weeks`), so it fails where the program does not exist;
    - replace every `os.chdir` with `monkeypatch.chdir`;
    - give every `subprocess` call a `timeout`;
    - remove every `# windowless: visible-ok` comment;
    - make the regression test over `main` compare per commit: for each commit on `main`, the new reader's answer equals the former rule's, except 9f6ace6, whose answer loses exactly TASK-031; keep its skip conditions.
    Every test function you add starts with `test_r044_` and names R-044.

## Acceptance criteria
- [ ] `python -m pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py -q -p no:cacheprovider` passes whole.
- [ ] `git diff --quiet 858da29 -- tests/test_task033_supervisor.py` and `git diff --quiet HEAD -- tests/test_task033_supervisor_r2.py` both exit 0.
- [ ] `python -m pytest tests/test_plan_check.py tests/test_pace_report.py -q -p no:cacheprovider` passes, and no `# windowless: visible-ok` remains in either file.
- [ ] `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider` passes.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/plan-check.py bridge/cursor-bridge/pace-report.py` reports no FAIL (the programs only; the tests take conftest's default).
- [ ] `python tools/dump-cli.py --check` passes after regeneration, and `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` ends OK.
- [ ] Run from the Workspace root, `python bridge/cursor-bridge/plan-check.py` still runs: same exit code as before, no traceback.
- [ ] No new dependency; `pace-report.py` and `bridge_env.py` stay ASCII.

## Constraints
All of `handoff/TASK-033.md`'s Constraints hold, with these changes:
- **Verification commands.** Run exactly these, from the Workspace root, never the whole suite:
  - `python -m pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py -q -p no:cacheprovider`
  - `python -m pytest tests/test_plan_check.py tests/test_pace_report.py -q -p no:cacheprovider`
  - `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider`
  - `git diff --quiet 858da29 -- tests/test_task033_supervisor.py` and `git diff --quiet HEAD -- tests/test_task033_supervisor_r2.py` (each prints nothing; check that the exit code is 0)
  - `python bridge/cursor-bridge/plan-check.py`
  - `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/plan-check.py bridge/cursor-bridge/pace-report.py`
  - `python tools/dump-cli.py`, then `python tools/dump-cli.py --check`
  - `python tools/make-manifest.py`, last, after every program edit
  - `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` (must end OK)
- **Mutation check, by hand, in your own run.** After the tests pass, apply each mutation below to the code, one at a time; run the two supervisor files and your two files; restore the code before the next. List each with the test that caught it, or "survived". No script of this lands in the diff.
  1. The parenthesis item test without the hyphen-and-digit condition.
  2. `_TRAIL_SUBJECT_RX` back to round 1's.
  3. The commit records split on a character a subject can hold.
  4. A non-zero git exit reported as a timeout.
  5. `core.fsmonitor=false` dropped.
  6. The exit-2 check applied to default roots.
  7. handoff/ untracked when any one brief is untracked.
  8. A usage field accepted when it is a `bool` or a negative.
  9. The session limit started after the walk.
  10. `sys.dont_write_bytecode` removed.
  11. The merge week taken from the newest merging commit.
- Do not refactor anything the Requirements above do not name.

## Done
Your report is the file `handoff/TASK-033-r2-report.md`, which you write as you go. When you finish, it holds: every file you changed; what you changed, with file:line, under the finding's number (R1 to R17); every verification command with its pass, fail and skip counts; the mutation list with what caught each; every test file outside your Scope that fails under your change, and at which lines, without editing it; a one-paragraph summary; and a section headed exactly `Assumed, not verified`, one item per line (what you assumed · why · what would confirm it), or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
