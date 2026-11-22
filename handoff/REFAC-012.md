---
record: brief
header: 1
id: REFAC-012
round: 1
satisfies: [R-097]
scope: ["bridge/cursor-bridge/evaluate-reports.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-012-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-012: one failed-read block, and one rerun text, in the security step's scan

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries the first candidate of stage P3's refactoring pass, in `bridge/cursor-bridge/evaluate-reports.py`: `scan_project(owner, repo, entry, meta, had_entry_before_seed)`, the per-project scan of `evaluate-reports.py security` that TASK-077 built (R-097). The same five-line failed-read block is written eight times in it, a flag is kept that always equals another, one test inside the scan is always true, two shape checks repeat what `_validate_runs_list` already returns, and the rerun command's text is built three times in the file. Each is reduced to one place; the manifest is regenerated after it. Behaviour stays exactly the same: every line `evaluate-reports.py security` writes to `security.md` and prints, every exit code, every GitHub read made (their number and their order, against the recorded replies under `tests/fixtures/github/`), the ledger entry written or left as it stood in each case, and `_meta.last_extract` untouched. Line numbers below are as the file stands at `c530abd` (TASK-078, the head of branch `refactor/P3`), before your edit; the functions named are the anchors.

**The sites.**

1. The failed-read block, eight times in `scan_project` (lines 913-1064). Each is a failed read, and each sets the same four things and appends a tuple, which is the only part that differs:

```python
        scan_unreadable = True
        ledger_skip = True
        kind = "finding"
        remedy = read_failure_remedy(False)
        read_failures.append(("workflows list", _api_failure_phrase(reason, body)))
```

The eight, by their first line and the tuple they append: lines 928-932 (`("workflows list", _api_failure_phrase(reason, body))`, the workflows read failed), 936-940 (`("workflows list", wf_err)`), 958-962 (`("runs list", _api_failure_phrase(reason, runs_body))`, the runs read failed), 964-968 (`("runs list", "reply could not be parsed")`, the runs body not a dict), 972-976 (`("runs list", "reply could not be parsed")`, `workflow_runs` not a list), 980-984 (`("runs list", runs_err)`), 997-1001 (`fail`, a jobs or log read of a failed run inside the `for run in failures:` loop, followed by `break`), and 1027-1031 (`fail`, the pending-failure read of `completed[-1]`).

   (a) `ledger_skip` (set `False` at line 919, `True` at lines 929, 937, 959, 965, 973, 981, 998 and 1028) is set `True` on exactly the lines `scan_unreadable` is (918 `False`; 928, 936, 958, 964, 972, 980, 997, 1027 `True`), and never apart. Its one reader is lines 1060-1063 (`if ledger_skip: update = None else: update = {...}`). `ledger_skip` is deleted and that test reads `scan_unreadable`.

   (b) Inside `for run in failures:` (line 994), whose `else:` is line 1009, line 1010 `if not scan_unreadable:` is always true: every path that reaches line 986 has `scan_unreadable` still `False` (each earlier failure sits in a sibling branch of the nested `if`/`else` chain), and inside the loop it is set `True` only on the line before `break`, which skips the loop's `else:`. The test at line 1010 is deleted and its body (lines 1011-1040) kept, one indent level out.

   (c) The two branches at lines 963-968 (`elif not isinstance(runs_body, dict):`) and 970-976 (`all_runs = runs_body.get("workflow_runs")`, then `if not isinstance(all_runs, list):`) fold into the call to `_validate_runs_list(runs)` (lines 747-760), which returns `"reply could not be parsed"` for any argument that is not a list. Both branches append `("runs list", "reply could not be parsed")` today, and the branch at lines 979-984 appends `("runs list", runs_err)`, so passing `_validate_runs_list` the value `runs_body.get("workflow_runs") if isinstance(runs_body, dict) else None` appends the identical tuple for a body that is not a dict, for a dict whose `workflow_runs` is not a list, and for every list exactly as now. `runs_body` is a plain `dict` from `json.loads` in `bridge_env._gh_get` (`bridge/cursor-bridge/bridge_env.py`, line 3901 on), so `.get` only reads it. On the success path `all_runs` keeps its value, `runs_body.get("workflow_runs")`, for its readers at lines 986, 1011 and 1012.

   (d) Each failing branch now records only its tuple, the one it appends today, unchanged, in one local (for example `failure`; the name `failures`, line 991, is already the list of failed runs and keeps that meaning), and one block after the scan's reads and before `_read_alerts` (line 1041) sets `scan_unreadable = True`, `kind = "finding"` and `remedy = read_failure_remedy(False)` and appends that tuple to `read_failures`. The order of the reads, and the point after which no later read runs once one has failed, stay exactly as now: no runs read after a failed workflows read, no jobs read after a failed runs read, the `break` out of the loop on the first failed jobs or log read (so no later run's jobs and no pending-failure read), and the pending-failure read only when the loop ended without `break`. `_read_alerts` (lines 893-910) still runs for every project whose origin was read, after the scan's reads, so `read_failures` holds the scan's failure, when there is one, before any alerts failure, as now.

2. The rerun command's text, `"gh workflow run dependency-scan.yml --repo %s/%s"`, built three times: line 835 (`classify_window_runs(window_runs, owner, repo)`, lines 833-847, `rerun = ...`), line 949 (`scan_project`, the disabled-workflow branch, `rerun = ...`) and line 1037 (`scan_project`, the pending-failure branch's `scanner failure`, `remedy = ...`). It becomes one module-level constant (or one small module-level function) used at the three sites, its text byte for byte as now, each site producing the same string from the same `owner` and `repo`. Line 948's `enable` text (`"gh workflow enable dependency-scan.yml --repo %s/%s"`) is a different command and stays as it is.

**Kept as it is.** `new_last` still advances (lines 989-990, `if advance_last and completed: new_last = completed[-1].get("created_at")`) before the exit-code loop, so it is still written as `last run read:` in the section (`format_security_section`, line 1104, from `info["last_run_read"]`) even when the ledger update is skipped (`update = None`). `info`'s keys and values and the pair `scan_project` returns are unchanged.

**Not taken** (noticed; leave each exactly as it is and name it in your report): (e) `classify_window_runs`' third value, `marker_at` at line 987, is unpacked and never read, and its fourth, `advance_last`, equals `bool(completed)`; the pending-failure path (line 1025) reads `_run_exit_code` a second time on `completed[-1]`, a run the loop at lines 994-1008 has already read (its conclusion is `failure`, so it is in `failures`): removing that read changes the number of GitHub reads, a change in behaviour.

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.12a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as it is R-097 (the Sunday evaluation's security step is a program: `evaluate-reports.py security` reads, for each of the bridge's projects and by GET alone, the weekly workflow's state and its runs since the last read and the open Dependabot alerts, and writes `Reports/Evaluations/<date>/security.md` in the three kinds and green; a read that fails is a finding with its remedy, never an empty section; the window's state stands in the ledger's `_meta`; built by TASK-077).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/evaluate-reports.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-012-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser` and no module docstring)
- every file under `tests/`, `tests/fixtures/github/` included: no test file or fixture may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.12a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- in evaluate-reports.py, everything but `scan_project`, line 835 of `classify_window_runs`, and the one module-level constant or function of site 2: `classify_window_runs`' other lines (its unused `marker_at` and `advance_last` among them), `_validate_runs_list`, `_validate_workflows_body`, `_validate_jobs_body`, `_run_exit_code`, `_completed_runs`, `_standing_cleared`, `read_failure_remedy`, `_read_alerts`, `_api_failure_phrase`, `_raw_failure_phrase`, the `gh` readers (`_gh_api_raw`, `_gh_api_include`, `_gh_paginate_json`), `project_security_section`, `format_security_section`, `cmd_security`, `DEP_SCAN_SUFFIX` and the other module constants, the module docstring, `build_parser`, and every other function; in `scan_project`, line 948's `enable` text, line 945's `not configured` remedy, line 955's runs path, the second `_run_exit_code` read at line 1025, and the `info` dict
- every other file under `bridge/`, `bridge_env.py` and `pace-report.py` among them (pace-report.py loads evaluate-reports.py for its project keys and reads none of the names this change touches)

## Context
**What the code is today** (`c530abd`). evaluate-reports.py has CRLF line endings on every line; keep them, and add no trailing whitespace. Nothing new is imported. Names: `ledger_skip` is removed; one local for the failed read's tuple and one module-level name for the rerun text (site 2) are added; no other name is added, renamed or removed. `scan_project` and `classify_window_runs` keep their signatures and their return values. `read_failure_remedy(alerts=False)` (lines 850-854) keeps its two callers' forms: `read_failure_remedy(False)` once in `scan_project` after the edit (eight times today) and `read_failure_remedy(True)` at line 1042. This is the first brief on branch `refactor/P3`, cut from `c530abd`.

**How the tests reach this code.** `tests/test_program_security_step.py` (TASK-077, R-097) loads `bridge/cursor-bridge/evaluate-reports.py` and runs its `main()` with `security --date 2026-11-22 [...]` in process, inside a scratch bridge root of its own, with `bridge_env.GH_COMMAND` pointed at a stand-in `gh` (a Python script) that records each call's arguments and answers from the recorded replies `tests/fixtures/github/security-*.json`. It checks `security.md`, the printed output, the exit code, the calls made and the ledger. No test names `scan_project`, `classify_window_runs`, `ledger_skip`, `scan_unreadable`, `read_failure_remedy` or `_validate_runs_list`; the code is reached only through `main()`. Site 1 is reached by the failed-read cases, among them `test_r097_a_failed_read_is_a_finding_with_its_remedy_never_green`, `test_r097_a_failed_read_names_which_read_failed_and_how` (the workflows list, the runs list, the jobs list and the job log, each by how it failed), `test_r097_the_alerts_are_read_after_a_failed_workflows_read`, `test_r097_a_run_id_that_is_not_digits_is_a_failed_read_and_never_a_path`, `test_r097_a_malformed_run_fails_the_runs_read`, `test_r097_a_field_of_the_wrong_type_is_a_failed_read`, `test_r097_a_body_without_its_list_is_a_failed_read` (its case `a runs body without workflow_runs` is the `workflow_runs`-not-a-list branch of (c); no recorded case gives a runs body that is not a dict) and `test_r097_a_run_time_without_an_offset_is_a_failed_runs_read`; several assert the ledger entry as it stood after a failed read, which is (a). Site 1 (b) and site 2 are reached by the window's cases, among them `test_r097_a_finding_names_a_dep_increment_and_only_the_exit_line_enters`, `test_r097_a_scanner_failure_names_the_rerun`, `test_r097_no_completed_run_is_a_finding_of_its_own_with_its_remedy`, `test_r097_a_finding_stands_until_a_later_run_ends_success` and `test_r097_a_later_success_clears_the_standing_finding`; the test file's `RERUN` constant is the rerun text with `OWNER/REPO`. Of `git grep -l -e "security" -- tests/test_program_security_step.py tests/test_evaluate*`, only `tests/test_program_security_step.py` matches (`tests/test_evaluate_reports.py` drives the module's other commands and does not reach `security`). `tests/test_header_currency.py` reads, by syntax tree, the names the programs under `bridge/cursor-bridge/` define and use, evaluate-reports.py among them; it is in the command below as the guard that no retired reading is introduced. The tests make no network call.

**The expected count.** The supervisor's baseline run of the pytest command below at `c530abd`, with this brief untracked, ended "192 passed" (none skipped). Your before-edit run is the baseline, and the after-edit run must match it (the same count passed, none failed, the same count skipped).

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for evaluate-reports.py; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.12a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.12a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print a count line and a line beginning `RESULT: SOURCES MATCH bridge 2026.11.12a` followed by the folder it checked, and exit 0. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** This is a logic surface over untrusted input: the scan reads GitHub's replies through `bridge_env._gh_get` and the module's `gh` readers, by GET alone, and decides from them what to write to `security.md` and whether to move the ledger's window. The trust boundary is GitHub's reply (and the project's git origin, read before `scan_project`). `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). This change moves no boundary: every reply is validated by the same functions before it is used, a reply of an unexpected shape is still a failed read with its remedy, never green, the ledger is still left as it stood after any failed scan read, no read is added or removed, and no text reaches the file except through `format_security_section`'s `ascii_line`, as now.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders, the scratch bridge roots and ledgers they create there, and the recorded replies. Never run evaluate-reports.py, pace-report.py or `bridge-install.py` yourself, against this repository, the owner's `Reports/` or any other, never run `gh`, and never call GitHub.

## Diagrams
`docs/diagrams/D-002-components.md` — the element `evaluate_reports` (`bridge/cursor-bridge/evaluate-reports.py`), whose edge already exists:

```mermaid
    evaluate_reports --> bridge_env
```

The change is internal to `evaluate_reports`: it adds no import and no edge, and no read to GitHub (`docs/diagrams/D-004-context-dfd.md`'s flows from the evaluation to GitHub stay GET only, the same reads), so no diagram changes. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run:
   - `git grep -n -w ledger_skip -- bridge`. Expected: ten lines, all `bridge/cursor-bridge/evaluate-reports.py`, at lines 919, 929, 937, 959, 965, 973, 981, 998, 1028 and 1060.
   - `git grep -n -F "read_failure_remedy(False)" -- bridge`. Expected: eight lines, all in evaluate-reports.py, at lines 931, 939, 961, 967, 975, 983, 1000 and 1030.
   - `git grep -n -F "gh workflow run dependency-scan.yml --repo %s/%s" -- bridge`. Expected: three lines, all in evaluate-reports.py, at lines 835, 949 and 1037.
   - `git grep -n -F -e "if not scan_unreadable:" -e "not isinstance(runs_body, dict)" -e "not isinstance(all_runs, list)" -- bridge`. Expected: three lines, all in evaluate-reports.py, at lines 1010, 963 and 971.
   - `git grep -n -w -e ledger_skip -e scan_unreadable -e scan_project -e classify_window_runs -e read_failure_remedy -e _validate_runs_list -- tests`, and `git grep -n -F "dependency-scan.yml --repo %s" -- tests`. Expected: both print nothing.
   If a check does not hold (another hit, a missing hit, or a line number other than these), stop, change nothing, and report it.
2. Site 1: `ledger_skip` is gone and `update` is `None` exactly when `scan_unreadable` is true; line 1010's test is gone and its body kept; the two shape branches (lines 963-968 and 970-976) are gone and `_validate_runs_list` is called with `runs_body.get("workflow_runs") if isinstance(runs_body, dict) else None`; each failing branch records its tuple, unchanged, and one block after the scan's reads and before `_read_alerts` sets `scan_unreadable`, `kind` and `remedy` and appends it, the order of reads and the stopping points as described under site 1 (d).
3. Site 2: the rerun text is written once in the file, as a module-level constant or a small module-level function, and the three sites (lines 835, 949, 1037) use it.
4. No other line of evaluate-reports.py changes. It keeps its CRLF line endings and gains no trailing whitespace. No comment is added in place of the deleted lines.
5. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: for every case of `tests/test_program_security_step.py`, the same `security.md`, the same printed lines, the same exit code, the same `gh` calls in the same order, the same ledger written or left as it stood, `_meta.last_extract` untouched; for a failed scan read, the same `read failed:` lines in the same order (the scan's before the alerts'), the same `finding` kind and the same login's-scope remedy; `last run read:` still the advanced `new_last` when the ledger update is skipped.
- [ ] The report states, for (a), (b) and (c), why the deleted code always produced the value already in hand, from your reading of `scan_project`, `_validate_runs_list` and `bridge_env._gh_get`, and for (d) why each failed read still stops the same later reads.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] The duplicates are gone: `git grep -n -w ledger_skip -- bridge` prints nothing; `git grep -n -F "read_failure_remedy(False)" -- bridge` prints one line, in evaluate-reports.py, inside `scan_project`; `git grep -n -F "gh workflow run dependency-scan.yml --repo %s/%s" -- bridge` prints one line, in evaluate-reports.py; `git grep -n -F -e "if not scan_unreadable:" -e "not isinstance(runs_body, dict)" -e "not isinstance(all_runs, list)" -- bridge` prints nothing; `git grep -n -F "scan_unreadable = True" -- bridge` prints one line, in evaluate-reports.py, inside `scan_project`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/evaluate-reports.py` shows more lines deleted than added.
- [ ] No public signature changed (`scan_project`, `classify_window_runs` and every other function keep theirs); no name is renamed; the names added and removed are only those the Context section lists; evaluate-reports.py imports nothing new.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints a line beginning `RESULT: SOURCES MATCH bridge 2026.11.12a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.12a`).
- [ ] `git diff --stat` shows only `bridge/cursor-bridge/evaluate-reports.py`, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment's tests replay the **recorded real responses** in `tests/fixtures/github/` through the tests' own stand-in `gh`; do not invent a mock of GitHub's responses, hosts, fields, or next-step URLs, and do not add or change a fixture.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources, pytest's temporary folders and the recorded replies only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number and changes no parsing.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_program_security_step.py tests/test_header_currency.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; `git diff --numstat -- bridge/cursor-bridge/evaluate-reports.py`; the five `git grep` commands of the fourth acceptance criterion.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example (e) above, the second `_run_exit_code` read on `completed[-1]`, or line 948's `enable` text); report them in your summary instead. Do not introduce an abstraction beyond what these duplicates need: one local for the failed read's tuple, one module-level constant or small function for the rerun text, and no other helper, parameter, alias or comment; nothing new outside evaluate-reports.py except the regenerated manifest.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-012-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the Requirements 1 grep commands with their output as the evidence;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, the two `git diff --numstat` commands and the fourth acceptance criterion's five `git grep` commands, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- for (a), (b) and (c), the statement, from your reading of the functions the second acceptance criterion names, of why the deleted code always produced the value already in hand, and for (d) why each failed read still stops the same later reads;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints), (e) and the second pending-failure read among them;
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
