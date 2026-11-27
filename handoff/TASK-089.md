---
record: brief
header: 1
id: "TASK-089"
round: 1
satisfies: [R-111]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/plan-check.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/records-migrate.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-089-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-089: Plan headings take the bridge's other increment prefixes

## Objective
Today a build plan's increment is only a `### TASK-nnn` heading: `bridge/cursor-bridge/bridge_env.py` holds `PLAN_ID_PATTERN = r"TASK-\d{3,}[a-z]?"`, and the walker, the plan check, the completion check's reading of `Satisfies`, records-migrate's plan header and the launcher's merge-unit rule all read through it, while the merged-id readers of `bridge_env.py` hold TASK-only forms of their own (a merge branch named `task-...`, a candidate id built as `"TASK-" + ...`), and `plan-check.py` reads only `handoff/TASK-*.md` as briefs. The bridge's other increment prefixes (BUG, DEP, CONFIG, FIX) are therefore no plan increments. This increment puts one tuple of increment prefixes, TASK, BUG, DEP, CONFIG and FIX, in `bridge_env.py`, composes `PLAN_ID_PATTERN` of it, has every reader of a plan id take the prefixes from that tuple or that pattern, has `plan-check.py` read the brief of an increment of any prefix, and keeps everything else, this repository's answers included, as on the checkpoint. A squash subject's id counts as merged for the plan only where the plan holds a heading of that id.

Satisfies: R-111

That row (its full text in `docs/REQUIREMENTS.md`) reads: a plan heading's increment id takes the prefixes TASK, BUG, DEP, CONFIG and FIX (C30): one list in `bridge_env.py`, shared by `plan-check.py`, the launcher's merge-unit rule and the merged-id readers, `records-check.py` keeping its own list of TASK, BUG and FIX; a merged subject's id counts as a plan id only where the plan holds its heading; REFAC ids stay outside the plan. You change no record of the row (the supervisor's records commit does).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/records-migrate.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-089-r1-report.md

Do not modify anything else.

Limits on these paths: `tests/test_improve_plan_prefixes.py` is the supervisor's acceptance file, committed at the checkpoint and not a path of yours: read it whole and run it, **do not edit it**. `bridge/cursor-bridge/bridge-run.py` and `bridge/cursor-bridge/records-migrate.py` are edited only where each holds a TASK-only pattern of its own, which then reads the shared tuple or pattern; the supervisor's scan found none in either (both read `bridge_env.PLAN_ID_PATTERN`), so confirm that by a content search of each file (for example `TASK|task-|\\d\{3`), quote the search and its result in the report, and edit neither unless the search finds one. `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`, and `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` only by running `python tools/dump-cli.py` (Done), never by hand. `docs/BUILDER_NOTES.md`: new dated lines at its end only. In `bridge_env.py` and `plan-check.py`, change only what the Requirements need.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names (`docs/REQUIREMENTS.md`, `docs/HARDENING.md`, `docs/PROJECT_STATUS.md` are the supervisor's records)
- `bridge/cursor-bridge/records-check.py`: it keeps its own list, `ID = r"(?:TASK|BUG|FIX)-\d{3,}[a-z]?"`, loads no sibling, and is not edited (a merged DEP or CONFIG subject needs no `docs/CHANGES.md` line, as on the checkpoint)
- `bridge/cursor-bridge/permission-guard.py`: its `INCREMENT_RX` names REFAC for branch and commit names, another rule; not edited
- every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/`, `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/VERSION` (must come out unchanged)
- every test file, `tests/test_improve_plan_prefixes.py` among them; `tools/make-manifest.py` and `tools/dump-cli.py` (you run them, you edit neither)
- every brief under `handoff/` other than your report
- every option of every program: none is added, removed or renamed

## Context
Line numbers are as on the checkpoint (the supervisor's checkpoint commit adds only the acceptance file and this brief, so they are the lines of `5c044d9`).

- **The pattern** (`bridge/cursor-bridge/bridge_env.py`): line 428 `GRAMMAR_ID_PATTERN = r"[A-Z][A-Za-z0-9-]*"`; line 429 `PLAN_ID_PATTERN = r"TASK-\d{3,}[a-z]?"`; line 431 `HEAD_RX` embeds it as `^###\s+(%s)...` with the heading's separators (hyphen, colon, em dash U+2014, en dash U+2013) and the title as group 2; line 438 `_PLAN_TASK_RX = re.compile(PLAN_ID_PATTERN)`. Readers that go through it: `walk_plan_prose_body(body)` (line 686, `id_rx = re.compile(PLAN_ID_PATTERN)`, and `HEAD_RX.match` at lines 719 and 781), `plan_increment_ids(folder)` (line 995), the header's `parent` and `depends_on` reading in `_plan_normalize_field(key, val)` (lines 3670 to 3685, `_PLAN_TASK_RX.findall`), and `plan_header_inc_ids(header)` (line 3829, `id_rx = re.compile(PLAN_ID_PATTERN)`). `completion-check.py` reads the plan through `bridge_env.plan_collect_satisfies_ids` (line 3841) and `plan_r_ids_outside_headers` (line 3614), which read the headings through the same walker and `HEAD_RX`.
- **The merged-id readers' own TASK-only forms** (`bridge_env.py`):
  - `_branch_name_to_id(branch, id_rx)`, lines 1162 to 1176: `if re.match(r"^task-\d", branch, re.I): cand = "TASK-" + branch[5:]` (lines 1164 to 1167), then the branch as it stands, its upper case, and its first part upper-cased.
  - `_PLAN_MERGE_RX`, lines 1208 to 1210: `r"^\s*Merge (?:pull request #\d+ from \S+?/|branch ')(task-\d{3,}[a-z]?)\b"`, `re.I`.
  - `_grammar_merge_id(branch, id_rx)`, lines 1268 to 1278: `re.match(r"^task-\d", ...)`, `re.match(r"(task-\d{3,}[a-z]?)", branch, re.I)` and `cand = "TASK-" + bm.group(1)[5:]`, else `_branch_name_to_id`.
  - `_plan_merge_id(line, id_rx)`, lines 1281 to 1286: `cand = "TASK-" + m.group(1)[5:]`, returned only where `id_rx.fullmatch(cand)`.
  - `_is_plan_id_rx(id_rx)`, lines 1238 to 1239: `return id_rx.pattern == PLAN_ID_PATTERN`; `squash_merged_ids(folder, id_rx, git_runner=None, ref="main")` (line 1337) and `squash_merged_ids_from_lines` (line 1289) decide the plan style by it. It must keep working: a caller passing `bridge_env.PLAN_ID_PATTERN` gets the plan style, the grammar pattern the grammar style.
  - The plan style's subject-start (`_subject_leading_ids`, line 1184), closing-parenthesis (`_parenthesis_merged_ids`, line 1251) and `Merges:` trailer forms (`_TRAILER_LINE_TEMPLATE`, line 1234) are built from `id_rx.pattern` and follow the pattern already; they are case-sensitive (a subject starting `fix(walker):` is no id).
- **plan-check** (`bridge/cursor-bridge/plan-check.py`): line 66 `ID = bridge_env.PLAN_ID_PATTERN`, line 67 `ID_RX = re.compile(ID)`; line 202 `merged_set = bridge_env.squash_merged_ids(os.getcwd(), bridge_env.PLAN_ID_PATTERN, ref=a.base)`; line 382 `done = {t for t in inc if t in merged_ready}` (only the plan's increments count as merged; the `note: <n> increments in <k> file(s); <m> merged, <d> deferred` line at 410 counts them); the brief loop, lines 383 to 391, globs `os.path.join(a.briefs, "TASK-*.md")`, skips names ending `-report.md`, takes the id by `ID_RX.search` on the file name (numbered round briefs such as `TASK-088-r2.md` included) and calls `brief_findings` only where the id is an unmerged increment of the plan; line 273 the DEPENDS message ends `(IDs are TASK-nnn, three digits or more)` (no test pins that text); the module docstring (line 8 on) describes an increment as `### TASK-nnn` and the merged forms with TASK examples. `plan-check.py` holds non-ASCII characters today (em dashes in its docstring); leave them. Its command-reference entry comes from its argparse description, so a docstring change may leave `docs/cli-reference.json` as it is; run `tools/dump-cli.py` either way (Done).
- **The launcher's merge-unit rule** (`bridge/cursor-bridge/bridge-run.py`, lines 1532 to 1550): `plan_ids = bridge_env.plan_increment_ids(ws)`, `plan_id_rx = re.compile(bridge_env.PLAN_ID_PATTERN)`, and a unit id is refused with `brief rule: <id> is not an increment heading in docs/BUILD_PLAN.md` where it does not fullmatch the pattern or is not in `plan_ids`. The launcher's brief and branch rule uses `bridge_env.grammar_id_rx()` (line 1450). Line 78's `run/agent/TASK-nnn.err` is docstring text.
- **records-migrate** (`bridge/cursor-bridge/records-migrate.py`): walks the plan with `bridge_env.walk_plan_prose_body` (lines 266, 289, 308), marks `historic` by `bridge_env._derived_historic(fields, iid, merged_set)` (line 337), and reads the merged set with `bridge_env.squash_merged_ids(root, bridge_env.PLAN_ID_PATTERN, ref=args.base)` (lines 744 to 745). `--check` lists what would be written and writes nothing.
- **This repository**: its history holds `BUG-nnn` and `FIX-nnn` squash subjects, and REFAC, HOTFIX and `CONFIG-B3b` ones; its plans hold no BUG, DEP, CONFIG or FIX heading, and `handoff/` holds `BUG-nnn.md` briefs. After the change the merged set read on this repository may hold BUG and FIX ids and plan-check will glob the BUG briefs; since only the plan's increments count as merged and only a brief of a plan increment is compared, every answer must stay as on the checkpoint (Requirement 7).
- **The design** (`docs/DESIGN.md`, "Change: the improvements release", C30): "A plan heading's increment id takes the prefixes TASK, BUG, DEP, CONFIG and FIX, one explicit list in `bridge_env` that `plan-check.py`, the launcher's merge-unit rule and the merged-id readers share; `records-check.py` keeps its own list, TASK, BUG and FIX, and loads no sibling, so a merged DEP or CONFIG increment needs no `docs/CHANGES.md` line, as today; REFAC stays outside the plan by design, and DEV and TEST stand in no bridge text. A merged subject's id counts as a plan id only where the plan holds its heading."
- **The acceptance tests**, `tests/test_improve_plan_prefixes.py`, 67 tests. They reuse the labs of `tests/test_header_plan.py` (`hp.git`, `hp.run`, `hp.plan_check`, `hp.plan_repo`, `hp.plan_text`, `hp.answer`, `hp.COMPLETION_CHECK`) and of `tests/test_task032_supervisor_launcher.py` (`t32.Lab`, `write_plan`, `write_brief`, `launch`, `build`, `assert_ran`, `assert_refused`), and `code_tree` from `tests/test_header_currency.py` for the source tests (docstrings out). The supervisor's run on the checkpoint, 2026-11-27: 34 failed, 33 passed.
  - red: `test_task089_one_tuple_of_prefixes_in_bridge_env`, `test_task089_the_plan_id_pattern_is_the_explicit_alternation_of_the_tuple`
  - red: `test_task089_the_pattern_accepts_each_prefix[BUG-001]`, `[DEP-002]`, `[CONFIG-003]`, `[FIX-004]`, `[FIX-1234b]`; `test_task089_the_pattern_composes_inside_a_larger_pattern`
  - red: `test_task089_a_heading_of_each_prefix_is_read[BUG]`, `[DEP]`, `[CONFIG]`, `[FIX]`
  - red: `test_task089_no_task_only_pattern_stands_in_the_program[bridge_env.py]`, `[plan-check.py]`
  - red: `test_task089_the_walker_reads_each_prefix_and_no_other_heading`, `test_task089_plan_increment_ids_reads_each_prefix`
  - red: `test_task089_plan_check_reads_each_prefix_as_an_increment`, `test_task089_a_subject_counts_as_merged_only_where_the_plan_holds_its_heading`, `test_task089_each_merged_form_names_a_bug_increment[merge-pull-request]`, `[merge-branch]`, `[closing-parenthesis]`, `[trailer]`, `test_task089_a_headed_plan_with_a_bug_increment_agrees`, `test_task089_plan_check_reads_a_bug_increments_brief`
  - red: `test_task089_the_completion_check_reads_satisfies_under_each_prefix[BUG]`, `[DEP]`, `[CONFIG]`, `[FIX]`
  - red: `test_task089_records_migrate_writes_a_bug_increment_into_the_header`
  - red: `test_task089_a_merge_unit_may_name_an_increment_of_each_prefix[BUG]`, `[DEP]`, `[CONFIG]`, `[FIX]`, `test_task089_a_bug_brief_naming_its_unit_runs_on_its_branch`
  - holds, and must keep holding: every other test of the file, among them `test_task089_the_pattern_refuses_the_other_forms[...]` (REFAC-001, DEV-001, TEST-001, R-027, HOTFIX-004, BUG-01, BUG-001ab, BUG-001A, bug-001, Task-001, TASKBUG-001, BUG001), `test_task089_the_other_headings_are_no_increment_headings[...]`, `test_task089_no_task_only_pattern_stands_in_the_program[bridge-run.py]` and `[records-migrate.py]`, `test_task089_the_programs_compile_no_plan_id_pattern_of_their_own[...]`, `test_task089_records_check_keeps_its_own_list`, `test_task089_satisfies_under_another_heading_plans_nothing[...]`, `test_task089_a_merge_unit_naming_another_heading_is_refused[...]`, `test_task089_a_merged_dep_or_config_subject_needs_no_changes_line`, `test_task089_a_merged_bug_subject_still_needs_its_changes_line`.
- **Trust boundary and security level.** A plan, a brief and a commit subject are text a builder or a reviewer can write (KP-078): the readers treat them as untrusted input, and every existing refusal of plan-check, the launcher and records-migrate stays. The project's ASVS level is 2 (`docs/INVENTORY.md`). Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.
- **Development data** (`docs/INVENTORY.md`): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: never run `bridge-run.py`, `review-guard.py` or `records-migrate.py` without `--check` from `bridge/` against this repository; the only runs against this repository are the three read-only reads of Requirement 7 (`plan-check.py` and `completion-check.py` read only; `records-migrate.py --check` writes nothing); every other run is a test's, on its scratch repository.
- This increment talks to no external service and touches no Claude Code host behaviour.

## Diagrams
None: the plan names no diagram for this increment.

## Requirements
1. **One tuple.** `bridge_env.py` holds `PLAN_ID_PREFIXES = ("TASK", "BUG", "DEP", "CONFIG", "FIX")`, a tuple, and `PLAN_ID_PATTERN` is composed of it as the grouped alternation followed by the digits and the optional letter as on the checkpoint; its value is exactly `(?:TASK|BUG|DEP|CONFIG|FIX)-\d{3,}[a-z]?`. Upper case only, as today. REFAC, DEV, TEST, HOTFIX and R ids are no plan ids.
2. **Every reader takes the prefixes from the tuple or the pattern**: the walker, `HEAD_RX`, `plan_increment_ids`, `plan_header_inc_ids`, the header's `parent` and `depends_on` reading, the plan-style merged forms (a merge of a branch named for an increment of any prefix, in any letter case, gives that id: `Merge pull request #7 from someone/bug-001` and `Merge branch 'bug-001'` give `BUG-001`; the subject-start, closing-parenthesis and `Merges:` trailer forms follow the pattern already), and the grammar-style branch mapping (the `task-` behaviour unchanged, the other four prefixes mapped the same way). No string constant of `bridge_env.py`, `plan-check.py`, `bridge-run.py` or `records-migrate.py` (docstrings aside) is a TASK-only pattern (`TASK-\d`, `TASK-*`, `task-[`, `(?:task|`, any case) or the bare `"TASK-"` a candidate id is built from, and none of `plan-check.py`, `bridge-run.py`, `records-migrate.py` spells the prefix list itself (a prefix name joined to another by `|`); `_is_plan_id_rx` keeps telling the plan style from the grammar style.
3. **plan-check reads every increment's brief.** It reads the brief of every increment as `handoff/<id>.md` and its numbered round briefs (as today for TASK): the files under `--briefs` whose name begins with an increment id of any prefix; a `REFAC-001.md` is not read; report files (`-report.md`) stay skipped; a brief is compared only where its id is an unmerged increment of the plan, as today. Its DEPENDS message and its module docstring name the five prefixes (the message takes them from `bridge_env.PLAN_ID_PREFIXES`, not from a list of its own); regenerate the command reference if the text `tools/dump-cli.py` quotes changes (Done).
4. **A heading of each prefix is an increment.** A plan heading `### BUG-001`, `### DEP-002`, `### CONFIG-003` or `### FIX-004` is an increment to the walker, the plan check, the completion check's reading of `Satisfies`, records-migrate's header and the launcher's merge-unit rule; `### REFAC-001`, `### DEV-001`, `### TEST-001` and `### R-027` are not.
5. **Merged only where the plan holds the heading.** A squash subject's id counts as merged for the plan only where the plan holds a heading of that id: plan-check's merged count and readiness, and records-migrate's `historic`, consider only the plan's increments (an id in the merged set that the plan does not hold changes no answer).
6. **Nothing else changes**: `records-check.py` and `permission-guard.py` untouched; no option added or removed; no dependency; no new import outside the standard library already imported; `bridge_env.py` and `bridge-run.py` stay ASCII; every existing output line form kept (the DEPENDS line keeps its form, only its list of prefixes changes).
7. **This repository reads as on the checkpoint.** Before your first edit and after your last, run from the Workspace root `python bridge/cursor-bridge/plan-check.py`, `python bridge/cursor-bridge/completion-check.py --mode plan` and `python bridge/cursor-bridge/records-migrate.py --check`, and quote both outputs of each; each pair must be identical line for line. The report says so for each of the three, or names each differing line.

## Acceptance criteria
- [ ] All 67 tests of `tests/test_improve_plan_prefixes.py` pass, the file unedited (R-111: its module docstring names the row).
- [ ] Every test of the files Done steps 8 to 10 name, and of the files your search adds (step 11), passes or skips by its own condition, each unedited. A test whose expectation the change alters is not edited: it is named in the report by id, with its failure lines, as a changed expectation for the supervisor to review; a failure you did not cause is reported by test id, not fixed.
- [ ] The three repository reads of Requirement 7 give identical output before and after, quoted in the report.
- [ ] The report names the search of `bridge-run.py` and `records-migrate.py` (Scope, Limits) and its result, and either says neither was edited or names the TASK-only pattern found and the change.
- [ ] `python tools/dump-cli.py --check` passes after `python tools/dump-cli.py`; MANIFEST regenerated; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `bridge/cursor-bridge/VERSION` unchanged and not listed by `git status --short`.
- [ ] Every requirement under "Satisfies" is fully met - no stand-in, placeholder or "arrives in a later stage" text.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- Write the report as you go, so that nothing is lost if the run ends early.
- No secret is needed or used. Nothing you write (code, the notes line, the report) holds a path of this computer or a user name: write `<Workspace>`, `<tmp>` and `~` instead, also in quoted output.
- Do not edit any test file. If an acceptance test and this brief seem to disagree, stop and report it by its test id; do not work around it.
- If the brief, the rules, or the tooling got in your way - an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason - append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service; add no call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms); you are not expected to add any process launch.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end; leave nothing running.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- No value in this increment is the owner's (rule 52).
- Follow existing conventions in the files you touch: ASCII program text in `bridge_env.py` and `bridge-run.py`, refusal tokens returned as strings, the existing output line forms kept.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only. The one exception is `git restore bridge/cursor-bridge/VERSION` in Done, step 6.
- Numbers: no number is read from text in this increment; ids are matched by the pattern, never sliced out of a string by position (a candidate id is not built by cutting a fixed number of characters off a branch name).
- **A probe runs only as a test.** Run no Python other than the Done section's commands: no script of your own, no here-document, no `python -c` but step 15's. Where you need a scratch check, write it as a test file under `tests/` named `test_task089_scratch_*.py`, run it with `python -m pytest -p no:cacheprovider -q <that file>`, and delete it; none stays in the diff, and the report names each one, what it showed and that it was deleted.
- Run the tests with `python -m pytest -p no:cacheprovider -q` directly as Done lists, not through `bridge-run.py` (the stripped run through the launcher is the supervisor's step), and only the files Done names or your search adds. **Do NOT run the whole `tests/` tree**: the whole suite is CI's run.
- **Mutation: name the code points, run nothing.** The report lists, for each label, the function and lines (as the file stands after your change) a mutation would touch and the test id you expect to catch it: M1 a prefix dropped from the tuple (name the test that catches each of BUG, DEP, CONFIG and FIX dropped); M2 the alternation left ungrouped; M3 the merge-branch form (`_PLAN_MERGE_RX` or what replaces it) back to task only; M4 the grammar mapping back to task only; M5 plan-check's brief files back to TASK only; M6 the walker's or `HEAD_RX`'s pattern bypassed by a literal; M7 the header's `depends_on` reading back to TASK only; M8 the launcher's unit check reading a TASK-only pattern. Where no test of the files Done names would catch a mutation, say so for that label.
- **Known failures.** The acceptance file is red on the checkpoint (34 failed, 33 passed). If any other test fails that your change did not cause, report it by test id with its failure lines and fix none.
- Prefer reuse over new code - the existing helpers, the standard library - and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.

## Done
Your report is the file `handoff/TASK-089-r1-report.md`, which you write as you go - what you did, what you changed, what you ran and what it printed, what you could not do - so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, for Requirements 1 to 7 one line each naming the functions and lines that meet it, the search of `bridge-run.py` and `records-migrate.py` and its result, the code points of M1 to M8, the test files your search added and the search you ran, every changed expectation (or `no changed expectation`), every scratch test file (or `no scratch test file`), and a section headed exactly `Assumed, not verified`, the report's last section: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm - for example how a branch with a suffix after the id (`bug-001-x`) is mapped in the grammar style, a mixed-case branch name, a brief file name that holds an id not at its start. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change. Steps 1 to 3 before your first edit; steps 4 to 17 after your last edit, in this order:
1. `git status --short`
2. `python -m pytest -p no:cacheprovider -q tests/test_improve_plan_prefixes.py` (expect 34 failed, 33 passed; quote the summary line and the failing ids)
3. `python bridge/cursor-bridge/plan-check.py`, then `python bridge/cursor-bridge/completion-check.py --mode plan`, then `python bridge/cursor-bridge/records-migrate.py --check` (quote each output whole, with its exit code)
4. `python tools/dump-cli.py` then `python tools/dump-cli.py --check` (it must pass)
5. `python tools/make-manifest.py`
6. `git status --short` (if `bridge/cursor-bridge/VERSION` is listed, run `git restore bridge/cursor-bridge/VERSION` and `git status --short` again)
7. `python -m pytest -p no:cacheprovider -q tests/test_improve_plan_prefixes.py`
8. `python -m pytest -p no:cacheprovider -q tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py tests/test_plan_check.py`
9. `python -m pytest -p no:cacheprovider -q tests/test_task032_supervisor_launcher.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_program_merge_unit_one.py`
10. `python -m pytest -p no:cacheprovider -q tests/test_records_migrate.py tests/test_program_own_records.py tests/test_pace_report.py tests/test_bug044.py tests/test_release_s_plan_size.py tests/test_plan_demonstration.py tests/test_dump_cli.py tests/test_header_reader.py tests/test_improve_satisfies_reader.py`
11. A content search of `tests/` for `squash_merged_ids|walk_plan_prose_body|plan_increment_ids|plan_header_inc_ids|PLAN_ID_PATTERN|HEAD_RX|plan-check|records-migrate|completion-check`; then run the files it finds that steps 7 to 10 do not name in one more command of the same form, `python -m pytest -p no:cacheprovider -q <those files>` (two commands if the list is long), each quoted in the report
12. Step 3's three commands again, each output quoted whole, and each compared line for line with step 3's (Requirement 7)
13. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
14. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
15. `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge_env.py','bridge/cursor-bridge/bridge-run.py')]; print('ascii ok')"` (expect `ascii ok`)
16. `git diff --stat HEAD`
17. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed, nor any `tests/test_task089_scratch_` file)

A failure in a file outside Scope is reported by test id, never fixed there.

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. Each mutation code point is listed by this brief's own label. A command you did not run is written `not run`, never described as run. Run this brief's test commands once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
