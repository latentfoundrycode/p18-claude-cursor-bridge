---
record: brief
header: 1
id: "TASK-060"
round: 2
satisfies: [R-080]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/conformance-check.py", "bridge/cursor-bridge/cursor-agent.shim", "bridge/cursor-bridge/MANIFEST.json", "docs/diagrams/D-004-context-dfd.md", "tests/test_program_strip_names.py", "tests/test_bridge_run.py", "tests/test_account_keys.py", "tests/test_conformance_check.py", "docs/BUILDER_NOTES.md", "handoff/TASK-060-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-060 round 2: The strip's names: a key file's home variables and the secret-like names (R-080)

Round cause: security - bridge/cursor-bridge/bridge_env.py:288 and bridge/cursor-bridge/bridge-run.py:2301, a stripped run keeps Cursor's key by the `--kind` word typed, not by being cursor-agent (security audit B1); correctness - bridge/cursor-bridge/bridge-run.py:1463, only the first home name is named (Review A B1); test that does not test - tests/test_account_keys.py:279, tests/test_bridge_run.py:420 and 432, tests/test_account_keys.py:330 (Review A B2 to B5)

## Objective
This is round 2 of TASK-060. Round 1's code is committed ("checkpoint before TASK-060-r2", `git log` shows it) and was rejected: Review A returned REJECT and the security auditor FAIL. The supervisor's acceptance file `tests/test_program_strip_names.py` gained two cases after the reviews (committed, HEAD); both fail on round 1's code and pin corrections 1 and 2 below. Your work is the minimum change to round 1's code and tests that makes every test in that file pass, meets corrections 1 to 8, keeps every existing test green, and edits nothing in the acceptance file. Round 1's brief, `handoff/TASK-060.md`, stays in force for everything this brief does not change (read it for the full requirements, context and Done list); its Requirements 1 to 14 must stay met.

Satisfies: R-080 - The strip cannot be undone by a key file, and its name test knows more names (J10, J11): a key file that names `USERPROFILE`, `HOME`, `HOMEDRIVE`, `HOMEPATH`, `APPDATA` or `LOCALAPPDATA` is refused before the run (exit 125, the name printed, the value never); the secret-like name test, one copy in `bridge_env.py` read by the launcher and by `conformance-check.py`, also matches `PAT`, `CREDS` and `AUTH` as name parts, `DATABASE_URL` and `SSH_AUTH_SOCK`, and a secret-like `CURSOR_` name is withheld from test and driver runs.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/cursor-agent.shim
- bridge/cursor-bridge/MANIFEST.json
- docs/diagrams/D-004-context-dfd.md
- tests/test_program_strip_names.py
- tests/test_bridge_run.py
- tests/test_account_keys.py
- tests/test_conformance_check.py
- docs/BUILDER_NOTES.md
- handoff/TASK-060-r2-report.md

Limits on these files: as round 1's brief (`handoff/TASK-060.md`, Scope); `tests/test_program_strip_names.py` is the supervisor's, read only. `bridge/cursor-bridge/cursor-agent.shim` and `docs/diagrams/D-004-context-dfd.md` need no change this round unless correction 3 makes one; D-004 stays line 8 only.

Do not modify anything else.

## Out of scope
As round 1's brief. In particular: no launcher option added or changed, no new dependency, no module docstring of a program changed, `bridge/cursor-bridge/roster-check.py` and every test file not listed untouched; the supervisor's mutants file is not yours.

## Corrections
1. **Cursor's key follows the run, not the label (security audit B1; Review A B5 and its should-fix).** Whether a stripped run keeps a secret-like `CURSOR_` name is decided by whether the command is `cursor-agent` (`is_agent` in `main`, from `resolve`), never by the `--kind` word: a stripped run that is not `cursor-agent` withholds it whatever `--kind` says (`builder` and `review` included), and a `cursor-agent` run keeps it. `stripped_env` called as `roster-check.py` and the existing tests call it (no argument, or one positional environment) keeps today's behaviour. The acceptance case `test_r080_the_kind_label_does_not_keep_cursor_names_for_a_suite` launches a stripped named suite with `--kind builder` and `--kind review`: each is either refused before `bridge-run: started` (exit 125) or runs without `CURSOR_API_KEY`; either is accepted, choose the smaller change. Your own cases: in-process, the argument your design uses for a cursor-agent run keeps `CURSOR_API_KEY` and the one for any other run withholds it, so that a mutant keeping it for every run and a mutant withholding it from the cursor-agent run each fail a test.
2. **Every home name is named (Review A B1).** `key_file_home_refusal` returns every name of the key file that is a home variable, in the file's order, as the file writes it, and the refusal line names them all (joined with `, `); still exit 125, before `started`, no value. The acceptance case `test_r080_every_home_variable_a_key_file_names_is_named` pins it.
3. **`KEEP_PREFIXES` governs (Review A should-fix).** `secret_like` reads its kept prefixes from `KEEP_PREFIXES`, not from literals of its own: the non-`CURSOR_` prefixes are kept for every run, `CURSOR_` only where the caller keeps Cursor's names. So the constant `tests/test_account_keys.py` compares with D-004's note is the one that decides.
4. **The D-004 test catches a hand edit of `AUTH` (Review A B2).** `fold_whole_names` in `tests/test_account_keys.py` (round 1, lines 279 to 293) deletes `SSH`, `AUTH` and `SOCK` from both sides, so dropping `AUTH` from the note's parenthesis or `|(^|_)AUTH(_|$)` from the pattern still compares equal. Read the whole names first: take the anchored names (`^NAME$`) out of the pattern text before its `[A-Z]{3,}` scan, treat a note word with an inner underscore (`DATABASE_URL`, `SSH_AUTH_SOCK`) as a whole name, and compare the whole names and the bare words separately, so the bounded `AUTH` stays on both sides. After the change the test fails on each of: `AUTH`, `PAT` or `CREDS` dropped from the pattern or from the note; `DATABASE_URL` or `SSH_AUTH_SOCK` dropped from either side; a word added on either side; a kept prefix added or dropped on either side. Check each by hand in-process and report the failing line (constraint below).
5. **Your launcher case under the constraints (Review A B3).** The R-080 case in `tests/test_bridge_run.py` (round 1, lines 420 to 429) starts the launcher with no `cwd`, no `timeout` and no `creationflags`, so it runs in the Workspace and a regressed refusal would write the Workspace's own run log. Give it `cwd` under `tmp_path`, `LOCALAPPDATA` under `tmp_path`, a timeout and `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)`, and a positive control first: the same `python -c` form with a key file of an ordinary name starts (`bridge-run: started`) and the child prints that name's value, asserted.
6. **Your shim case asserts every parameter (Review A B4).** The parametrized case in `tests/test_account_keys.py` (round 1, lines 330 to 345) asserts nothing for names in neither `WITHHELD` nor `KEPT` (`PAT`, `SCREDS`) and never compares the two recipes directly; its `if name != "PATH"` is dead. For every parameter assert an explicit expected value (withheld or kept) for both the shim and `stripped_env`, and that the two agree.
7. **The conformance cases (Review A should-fix).** The inventory-floor case in `tests/test_conformance_check.py` (round 1, lines 444 to 454) adds a boundary name (`AUTHOR_NAME` or `DATABASE_HOST`) and asserts it is not named; the session-NOTE case (round 1, line 461) passes a timeout and `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` and builds a small environment of its own (the interpreter's needs, `SYSTEMROOT` and the like where present, plus the names under test) instead of the whole session environment, since the NOTE lists only the first eight names.
8. **Housekeeping.** `conformance-check.py`'s keys floor: drop the repeated `name = m.group(1)` (use the one name). Nothing else.

## Context
Round 1's code, as committed: `bridge_env.py` lines 46 to 63 (`SECRET_LIKE`, `KEEP_PREFIXES`, `secret_like(name, keep_cursor=True)`), line 288 (`keep_cursor = kind is None or kind in ("builder", "review")`); `bridge-run.py` lines 1460 to 1468 (`HOME_KEY_VARS`, `key_file_home_refusal`), 2193 and 2261 to 2271 (the two refusals), 2301 (`bridge_env.stripped_env(kind=kind) if (is_agent or strip) else dict(os.environ)`). In `main`, `kind` comes from `--kind` (or `kind_of(cmd)` without the flag), and nothing refuses `--kind builder` for a command that is not `cursor-agent`; `is_agent` is set by `cmd, is_agent = resolve(cmd)` just before the strip. The reviews' other observations are the supervisor's records, not this round's work: the names `stripped_env` sets beside the home variables (`GH_CONFIG_DIR`, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_PARAMETERS`) in a key file, `DATABASE_URL`'s kin (`PG_DATABASE_URL`, `REDIS_URL`), Windows OpenSSH's fixed agent pipe, and conformance-check's floors where `bridge_env.py` is absent.

## Acceptance criteria
- [ ] Every test in `tests/test_program_strip_names.py` passes (61 at HEAD; it names R-080).
- [ ] Corrections 1 to 8 met, each named in the report with the function or line.
- [ ] Round 1's Requirements 1 to 14 stay met; every test of round 1's Done list passes, unchanged but for the cases corrections 4 to 7 change.
- [ ] No value printed; every refusal exit 125 before anything starts; every line added to the three Python programs ASCII; no option, no dependency.

## Constraints
Round 1's brief's Constraints all stand (foreground commands only, named test files only with the Done commands, no `python -c` or script of your own, no git command that writes, ASCII, windowless subprocesses with a timeout in tests, the report's form). Mutations by hand, in-process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (R1) a secret-like `CURSOR_` name kept for every stripped run; (R2) it withheld from the cursor-agent run; (R3) the refusal naming only the first home name; (R4) `AUTH` dropped from the pattern; (R5) `AUTH` dropped from D-004's parenthesis; (R6) `CURSOR_` removed from `KEEP_PREFIXES`. Prefer the smallest change; refactor nothing else.

## Done
Your report is `handoff/TASK-060-r2-report.md`, written as you go, in round 1's form (files changed; summary; corrections 1 to 8 each in one sentence with the function or line; the tests you changed and why; every command below with its output, verbatim, in fenced blocks; the mutations R1 to R6; a last section headed exactly `Assumed, not verified`). It names no computer path: `<Workspace>` for the repository folder, `~` for the home folder.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change:
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check` (expect the reference current)
3. `python -m pytest -p no:cacheprovider -q tests/test_program_strip_names.py`
4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py`
5. `python -m pytest -p no:cacheprovider -q -rs tests/test_account_keys.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_conformance_check.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_program_strip_end_to_end.py tests/test_release_t_strip.py tests/test_bug043.py tests/test_hotfix25a_roster_launcher.py`
8. `python -m pytest -p no:cacheprovider -q tests/test_a4_followups.py tests/test_header_status.py tests/test_header_tables.py tests/test_workflows_line_check.py tests/test_a4_review_fixes.py tests/test_bug042.py tests/test_b2_least_confident.py tests/test_calibrate_program.py tests/test_hotfix25a_conformance_semgrep.py tests/test_conformance_check_a4.py tests/test_release_t_floor.py tests/test_conformance_windowless.py`
9. `python -m pytest -p no:cacheprovider -q tests/test_program_launcher_forms.py tests/test_bridge_run_driver.py tests/test_release_s_launcher.py tests/test_task032_supervisor_launcher.py tests/test_dump_cli.py`
10. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect the sources to match)
11. `git diff --stat HEAD`
12. `git rev-parse HEAD` and `git status --short`

Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
