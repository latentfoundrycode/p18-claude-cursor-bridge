# Builder notes


2026-10-12 TASK-002-r2: Semgrep CLI 1.176.1 rejects `semgrep scan --dry-run` (suggests `--dryrun`, which is autofix-only); used `semgrep --validate --config …` to confirm rule load counts per the handoff report.

2026-10-12 TASK-002-r3: Push-to-`main` Semgrep uses `--baseline-commit ${{ github.event.before }}` (skip baseline when `before` is the all-zero SHA) so the floor gates only code introduced by the push; PR path still uses `git merge-base`.

2026-10-12 TASK-002-r4: `@socketsecurity/cli@2.1.0` `socket ci` has no `--files` flag (it is ignored); the step runs `socket ci` from the repo root and the CLI scans `.`, picking up `requirements.lock` as a supported manifest.

2026-10-12 TASK-002-r5: Pin `@socketsecurity/cli@1.7.0` (npm `latest`, not deprecated; 2.1.0 is a deprecated bad build). Set `SOCKET_CLI_ORG_SLUG` from `vars.SOCKET_ORG_SLUG` so `socket ci` can resolve the org (404 without it on PR #16).

2026-10-12 TASK-002-r6: Run `socket ci --no-banner` so the CLI compact header does not print the first five characters of `SOCKET_CLI_API_TOKEN` (GitHub masks only whole secrets; the repo is public).

2026-10-16 TASK-006: `tests/test_workflow_check.py::test_r014_registry_heading_missing` replaces the first `## Extension points` in `extension-points.md`, which is the prose citation on the "How this file is read" line, not the heading on its own line, so a heading-line parser still sees the table and exits 0.

2026-10-16 TASK-006-r4: a missing `types/` or `traits/` is skipped with `os.path.lexists` before `is_link`. On both the `os.path.isjunction` branch and the Windows `lstat` fallback, `FileNotFoundError` and `NotADirectoryError` are not links; any other `OSError` is a link. A fence is zero to three leading spaces then three backticks; four spaces is not a fence.

2026-10-16 TASK-006-r5: a `types/` or `traits/` path is examined with `os.lstat` (missing means skip; any other `OSError` is `ERROR` and exit 2). `is_link` uses one `os.lstat` on every Python: `S_ISLNK`, or on Windows `FILE_ATTRIBUTE_REPARSE_POINT`. A fence is a CommonMark opening run of backticks or tildes, closed only by an equal or longer run of the same character with nothing after it but spaces or tabs.

2026-10-16 TASK-006-r6: `cells_of` removes one leading `|` and one trailing `|`, so a row ending or starting `||` keeps its empty cell. File text is split only at `\n` (`file_lines`); a final line feed does not add an empty line. Form feed, vertical tab, and the other `splitlines` breaks stay inside the line.

2026-10-16 TASK-008: Done runs `python -m pytest tests -q` before `python tools/make-manifest.py`, and the install and rollback tests refuse a bridge tree whose edited programs do not match MANIFEST.json, so that ordered run exits 1 until the manifest is regenerated and the suite is run again.

2026-10-17 TASK-008-r2: while `judge_workflows_line` loads `workflow-check.py`, `sys.dont_write_bytecode` is `True` and restored in `finally`. The checker path is `os.path.realpath` of the program file. `field` calls `escape_field` directly; a missing one, or `SystemExit` during or after load, is not-checked. The post-load handler prints through `ascii_text` only.

2026-10-17 BUG-002-r1: after `python tools/make-manifest.py`, `git diff --stat` warns that LF in `bridge/cursor-bridge/VERSION` will be replaced by CRLF the next time Git touches it, but VERSION is not a diff entry and `git diff -- bridge/cursor-bridge/VERSION` is empty.

2026-10-19 CONFIG-B3b: text-mode `open(...).read()` with default `newline=None` translates CRLF to LF on every platform, so dropping explicit line-ending normalisation in `dump-cli.py --check` is an equivalent mutant everywhere, not only on Windows; the Ubuntu runner checks files out with LF.

2026-10-19 CONFIG-B3b-r3: `json.dumps` on a default double-escapes backslashes, so a home path embedded in a string default never matched the fragment check on Windows; walking defaults as values and comparing fragments with `os.path.normcase` fixes that without a separate forward-slash repository fragment.

2026-10-19 CONFIG-B3b-r4: refusing `relpath` `.` in `absolute_default_to_placeholder` keeps round-3 choice refusal for `HERE` while round-4 walks choices to placeholders for paths under the bridge folder; mutation (y) survived for lack of a test (a tuple choice holding a non-absolute string with a path in it passes the walk, and only the string check catches it); the supervisor's `test_cfgb3b_r4_a_choice_holding_a_path_inside_a_string_is_refused` now catches it (corrected by the supervisor after Review A, round 4).

2026-10-25 BUG-020-r1: Done step 1 (`python -m pytest tests -q`) takes ~6 minutes here; the `cron_next` edit landed while that run was near 30% progress, so the logged pre-edit counts mix stale-manifest failures with post-fix loop-guard behaviour and do not capture `test_bug020` TypeError (HEAD still rejects `tz`, verified with `git show`).

2026-10-26 TASK-031-r5: `test_fix001_no_test_starts_a_program_around_the_default` fails on the round-4 supervisor reproduction strings in `tests/test_mutation_run_supervisor.py` (`creationflags=NO_WINDOW` without the `CREATE_NO_WINDOW` substring); that file is out of scope for r5, so verification step 3 cannot pass here until those embedded literals are fixed elsewhere.

2026-10-27 TASK-031-r11: on Python 3.12, only an empty `PYTHONPATH` entry puts the working folder on `sys.path`; round 11's `find_spec` check still refused ordinary layouts when another copy of the project package was on `PYTHONPATH`, which round 12 replaced with a fixed list of names pytest imports for configuration.

2026-10-31 BUG-038-r1: `tests/test_bug038.py` test 3 uses `text[:text.index('"""', 3)]`, which on `completion-check.py` (shebang then opening `"""` on line 2) slices only the shebang line, so `STAND-IN` is never in `doc` and the test fails before and after the docstring fix; keyword checks pass with `ast.get_docstring`-style extraction.

2026-11-11 TASK-051: `test_fix001_no_test_starts_a_program_around_the_default` fails on supervisor `tests/test_records_migrate.py` lines 76 and 81 (`creationflags=NO_WINDOW`); Scope forbids editing above the builder marker, so the supervisor should spell `getattr(subprocess, "CREATE_NO_WINDOW", 0)` there. Closed 2026-11-11 (stage H2's review): the file no longer holds those lines.

2026-11-13 TASK-057-r2: `test_r077_the_help_names_the_move_mode_and_its_base` asserts the substring `SUPPRESS` is absent from the whole of `docs/cli-reference.json`, but `tools/dump-cli.py` on Python 3.12 records every argparse `-h` default as the string `==SUPPRESS==` (17 occurrences after `--moves`/`--base` help is fixed); the test's first assertion and the trace-check section of the reference already match S1, while the second assertion cannot pass without a dump-cli change (out of scope for r2). Closed 2026-11-14 (stage P1's review): the supervisor's test now asserts that no option's help is `==SUPPRESS==` (TASK-057, 1916e72; HARDENING, TASK-057).

2026-11-15 TASK-062-r2: `git rev-parse --git-path hooks` from a worktree sub-folder returns a path relative to the launch folder (for example `../.githooks`), not to `--show-toplevel`; `_git_resolved_path` must join against `os.getcwd()` or the hook watch misses the planted file.

2026-11-15 TASK-063-r3: subagent pass extended `read_shell` with `unreadable`, `cmd_words`, `sub_chains`, and `gh_amp` hooks and updated `check`/`chain_reason`/`commit_message`, but quote-aware `cmd_words` (merged `"a b"`, `--fo"rce"`) remain wrong; 45 failures still in `tests/test_program_permission_guard.py`; a full positive-grammar replacement is still required.

2026-11-16 TASK-063-r9: an empty or edge-whitespace argument of powershell.exe has to be refused in the switch walk before those words are joined into the inner command, because the join re-reads the real command and a dangerous one is then refused for the action rather than as unreadable.

2026-11-16 BUG-045-r2: `git --help` on this host prints a short usage line that omits `--attr-source`, `--super-prefix`, `--literal-pathspecs`, `--glob-pathspecs`, `--noglob-pathspecs`, `--icase-pathspecs` and `--list-cmds=`, which the ruled known list keeps; the usage line showed no option the list lacked.

2026-11-16 BUG-045-r3: F9 asks the PowerShell tool to refuse `git -c 'alias.cm="commit" -n -am' cm x` and `git -c 'alias.cm=c"ommit" -n -am' cm x` with `alias` in the reason, but `_read_powershell` refuses a literal double quote inside the word before the git alias loop runs, so the reason is `a literal double quote` and does not contain `alias`; that reader is outside this round's scope.

2026-11-16 BUG-045-r4: git accepts a 3-character prefix of `--mirror` and reads the characters `4` and `6` inside a short-flag cluster, so one 4-character floor and a letters-only cluster check both let a force push through; the digit allowance is an extra argument of `_short_letters_hold` that defaults to empty, so commit's `-n` stays letters-only (`git commit -4n -m x` still exits 0). The starting-tree reading was taken by launching the guard as `tests/test_bug045.py` does, with cwd a folder under the system temporary directory, because the brief forbids this repository folder as cwd and the workspace boundary forbids a file outside it.

2026-11-16 TASK-064: a 300-second wait on the six-file side-effect pytest returned while that process was still running; it was not hung and later exited 0 (about 328 seconds). The same command is in Done and has to be waited out past five minutes on this host.

2026-11-17 TASK-083: `review-guard.py` and `permission-guard.py` are CRLF, so a mutation search written with `\n` only matches nothing, and a long bash heredoc of a Python driver was cut off on this host; the self-check had to be a file under `handoff/` that was deleted before the Done commands.

2026-11-17 TASK-083-r2: a foreground wait of 30 seconds backgrounds the shell while `python -m pytest -p no:cacheprovider -q -rfE tests/test_permission_guard.py --tb=line` is still printing progress; that run then exited 0 (`296 passed in 30.21s`), and the Done run of the four permission-guard files was given a longer wait.

2026-11-17 TASK-083-r3: a foreground wait of 30 seconds backgrounds the shell while `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py -k "r083_r3 or r083_r2 or disable_auto or help" tests/test_permission_guard.py -k "r083_r3 or r083_r2 or test_allowed or test_refused"` is still printing progress; that run then exited 0 (`365 passed, 79 deselected in 41.37s`), and the Done pytest runs were given a longer wait.

2026-11-17 TASK-083-r4: an empty word is falsy, so returning it as the group neither marks the command unreadable (`startswith("-")` is false) nor state-changing (`bool("")` is false); `gh_words` returns the existing `INNER_UNREADABLE` sentinel with the word beside it, and `any()` over that empty number is false so the number test refuses `""` on its own.

2026-11-17 BUG-046: an unquoted `?` in a gh api endpoint is a glob to the Bash reader and never reaches the merge-endpoint refusal, so the query spelling in tests/test_bug046.py is single-quoted, the same way the supervisor's paged dependabot call is.

2026-11-17 TASK-065: `tests/test_program_watch_wait.py::test_r085_a_poll_that_keeps_failing_ends_at_the_limit` counts every stderr line containing `a poll failed`, and R10's limit left is the same words, so printing both W4 and that left fails the count; the limit line's left is `poll failed (<source>: <reason>)` and W4 keeps `a poll failed (<source>: <reason>); retrying every <WATCH_POLL>s until the limit`.

2026-11-17 TASK-065: a mutant that holds the wait until the 3600s default, with each poll spawning the stand-in, takes about two minutes for one case (`test_r085_a_run_that_completed_without_a_check_does_not_hold_the_wait`) and about three for the two failed-check cases; the fake clock does not make those polls free.

2026-11-17 TASK-065-r2: when no time is left the loop returns before the first poll, so a limit of 0 never calls GitHub; the limit line has to read the local head itself on that path, or the head stays `?`.

2026-11-17 TASK-066: the new R-086 case uses `changed_repo` and `run` in `tests/test_hotfix25a_guard_scope_invisible.py`, and those helpers call `subprocess.run` with no timeout; adding a timeout would edit an existing helper, which the brief forbids, so the case does not add its own timeout.

2026-11-18 TASK-067: `test_r087_git_or_the_base_unreadable_exits_2_never_a_pass` with case `dash-base` accepts any exit 2, so a mutant that lets a base beginning with "-" through still passes when git then rejects that revision; a catch is an assertion that the output contains the dash refusal and not the missing-commit refusal.

2026-11-18 TASK-067-r2: no case builds a patch path that is absent from that commit's name-status list, so dropping the disagreement check (exit 2, `the patch and the file list disagree`) still passes the scan tests.

2026-11-18 TASK-067-r5: a combined `Binary files differ` section has no `+++` line (its path is only on `diff --cc`), an ordinary binary `index` line omits the mode a text `index` line prints, and `git show -z --raw` of a merge is already one combined record per path (one colon per parent), empty when every file matches one parent.

2026-11-18 TASK-067-r6: sending a merge record that has no patch section back through the line diff still passes the clean-merge case, because the intersection over the parents is empty and the trimmed middles stay under the pair bound; no case builds a single-parent record with no section, so dropping that refusal also passes.

2026-11-18 TASK-067-r7: `b"".decode` of an unknown encoding name returns an empty string and does not raise `LookupError`, so an empty probe cannot tell whether Python knows the encoding; decoding the printable-ASCII sample does raise `LookupError`.

2026-11-18 TASK-067-r7: a path whose first segment is a byte UTF-8 replaces with U+FFFD is still found by the widened segment rule when the commit object is decoded as UTF-8, so ignoring the `encoding` header still passes the ISO-8859-1 path cases; the non-ASCII name case is what requires that header.

2026-11-18 TASK-067-r8: Python's `iso2022_jp` encoder writes ESC `$` `B` (bytes 1B 24 42) directly after a path separator before the non-ASCII segment, and the round-8 ISO-2022-KR file line (one designation, then the encoder's shift) puts SO (byte 0E) directly after the separator, so dropping only ESC fails the three JP cases and dropping only SO fails the KR file line.

2026-11-18 TASK-067-r9: the outer NFKC is what keeps a character whose case fold is a letter plus a combining mark (U+01F0 folds to j plus U+030C) one word character; without it Python's `re` treats the mark as a boundary, so the base letters match as a whole word. The inner NFKC has to run before `casefold`, or a modifier letter such as U+1D2C becomes a capital letter (NFKC after `casefold` yields `A`) and misses the ASCII spelling.

2026-11-18 TASK-067-r10: with both readings kept, dropping the outer NFKC makes the folded reading hit a name ending in `j` before U+01F0 (the raw reading does not), and dropping the inner NFKC misses a name holding U+1D2C written in plain letters (the raw reading misses it too). Replacing only the raw reading with the lower-cased index match still finds an ASCII name after U+0130, because the folded reading matches that name; a dotted or dotless `i` in the name's own letters is what that mutant misses.

2026-11-19 REFAC-008: `git grep -n -w -e app_id_of -e suite_id -e is_int_id` matches the committed brief in handoff/REFAC-008.md, and `git grep` of `_check_app` also matches tests/test_loop_guard.py's `test_the_run_sheet_check_applies_in_every_phase_and_blocks_the_stop` because that name contains the substring `_check_app`; the helpers themselves are only in the three programs.

2026-11-19 REFAC-009: `git grep -n -w -e reply_bits -e rule_contexts` matches only the committed brief in handoff/REFAC-009.md; the two names are unused in bridge, tools, tests and docs, so the move continued.

2026-11-21 TASK-068: on Windows `msvcrt.locking` locks a byte range from the current file position, so a handle already at the end of an append does not exclude another append; `in-flight.py` seeks to offset 0 before `LK_NBLCK` and unlocks that same byte.

2026-11-21 TASK-068-r2: `paused_in_flight` keeps the first `Paused:` line for the life of an append-only log, so a later `Paused: resumed` never lifts it; the guard has to read the last match of `field`'s pattern. The append also has to set `O_BINARY`, or Windows turns each LF into CR LF.

2026-11-21 TASK-068-r3: since round 2, the Windows lock sits on the byte at `2**31`, not byte 0 as round 1's line says.

2026-11-21 TASK-069: a pass line's stamp is `YYYY-MM-DDTHH:MMZ` with no seconds, so pace-report's `_parse_run_time` (which requires seconds) does not read it; the stamp is parsed with `strptime` and `%Y-%m-%dT%H:%MZ`.
