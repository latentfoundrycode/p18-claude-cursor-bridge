---
record: brief
header: 1
id: "TASK-083"
round: 4
satisfies: [R-083]
scope: ["bridge/cursor-bridge/permission-guard.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_ready.py", "tests/test_permission_guard.py", "docs/BUILDER_NOTES.md", "handoff/TASK-083-r4-report.md"]
merge_unit: null
blocking_class: "safety mechanism"
---
# TASK-083 round 4: before the subcommand, only a command's name is read as one (R-083)

Round cause: security

Blocking class: safety mechanism - Review A and the security audit of round 3, each reproduced in process: under Bash, gh pr '' merge --squash --match-head-commit <B> is allowed with neither record read, the guard taking the empty word for the subcommand, while cobra passes over the empty word, finds pr merge, and gh merges the current branch's pull request at head B

## Objective
Fix the following confirmed defect in the permission guard's `gh_words`, and nothing else.

This is round 4 of TASK-083, above the ceiling of three, opened by the class line above. Rounds 1 to 3 built `review-guard.py ready <pr>`, the ready record, the guard's rule on it, the one reading of the words after `merge` (`_read_merge_words`) and the refusal of an option before a gh subcommand; all of that stays as it is except what K1 to K3 below change. The supervisor commits round 3's tree together with this brief and the new tests before your run, so the line numbers below hold when you start.

**The confirmed defect** (reproduced in process on round 3's tree by both reviewers and by the supervisor, now red tests):
1. `gh_words` (`bridge/cursor-bridge/permission-guard.py`, 2056-2083), finding the group and the subcommand, appends every word that does not begin with `-` (2078), the empty word among them. cobra's command search passes over an empty word (it takes a word for a command only where `s != "" && !strings.HasPrefix(s, "-")`) and leaves it to the subcommand as a positional. So under Bash, where `''` and `""` give an empty word, `gh pr '' merge --squash --match-head-commit B` is read by the guard as group `pr`, subcommand `''`, and never as a merge: `merge_reason` is not called and the command is allowed; gh finds `pr merge`, takes the empty word as its selector, and merges the current branch's pull request at head B with no number named and neither record read. The same with `gh '' pr merge ...`, and after `-R <repo>` or `--repo <repo>`. PowerShell already refuses an empty quoted word, so the two shells disagree. Round 3's rule (J2) named only words beginning with `-`; this round replaces the shape-by-shape rule with one that admits only a command's name.

**One hardening on the same path** (K2): `merge_reason` (2568-2588) takes `''` as a number made of digits, since `any()` over an empty string is false (2580); only `ready_recorded`'s own check refuses it later. **One weak case** (K3): round 3's `tests/test_permission_guard.py::test_r083_r3_an_equals_form_before_the_bare_option_clears_it_and_the_option_is_state_changing` asserts a chain refused that round 2's code refused too (its gh word `--subject` was never in `GH_READ`), and shows no allowed chain beside it.

**The reproduction tests:** `tests/test_program_ready.py`, the section headed `# ---------------------------------------------------------------- round 4: a word cobra does not take for a command`, at the end of the file. On round 3's tree the result is quoted under Constraints, "Known failures"; every case in the file must pass.

Satisfies: R-083 - One reader of a repository's branch rule, and the proof that CI passed as a program (T-CONTEXT, C7): [...] the permission guard requires the ready record for the merge command's pull request number and its `--match-head-commit` head, after and in the same way as its check of the premerge record, and refuses a merge that names no number. (Full text: its row in `docs/REQUIREMENTS.md`. This brief serves the guard's reading of a gh command's group and subcommand.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_ready.py
- tests/test_permission_guard.py
- docs/BUILDER_NOTES.md
- handoff/TASK-083-r4-report.md

Limits on these files:
- `bridge/cursor-bridge/permission-guard.py`: only `gh_words` (2056-2083), the gh branch of `_check_word_list` (from `elif head in ("gh", "gh.exe"):` at 2315 through its `gh api` merge-mutation refusal), the gh branch of `state_changing` (2389-2393), and in `merge_reason` the number test at 2579-2580 (K2). Every other function, constant and line keeps its value and behaviour; `_read_merge_words`, `ready_recorded` and `premerge_recorded` among them.
- `tests/test_program_ready.py` is the supervisor's acceptance file. It is in Scope only so that its new section counts as this round's; you read and run it and **edit nothing in it**.
- `tests/test_permission_guard.py`: change the round-3 case named under K3 as K3 says; you may add cases below the R-083 cases; change no other case.
- `bridge/cursor-bridge/MANIFEST.json` changes only by being regenerated with `python tools/make-manifest.py` (Done). Never edit it by hand.
- `bridge/cursor-bridge/VERSION` is outside Scope; it reads `2026.11.12a`. Restore it with `git restore bridge/cursor-bridge/VERSION` right after the manifest (Done), and edit it in no other way.
- `handoff/TASK-083-r4-report.md` is your report. The reports of rounds 1 to 3 are the supervisor's records now; do not edit them.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- `bridge/cursor-bridge/review-guard.py`, `bridge/cursor-bridge/bridge_env.py`, every test file other than the two the Scope names, `tests/fixtures/github/`, `docs/cli-reference.json`, `docs/CLI_REFERENCE.md`.
- The `gh alias set` refusal and its ways round (a trailing option, a `!gh pr merge` expansion, `--shell`): outside this round, recorded by the supervisor. `-R`/`--repo` and `GH_REPO` aiming at another repository: recorded by the supervisor.
- The `gh api` walk after the group `api` (its options, and the endpoint, which is a path and not a command's name) stays exactly as it is.
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this round** is that of rounds 1 to 3: `docs/DESIGN.md`, "Change: the program release", the permission guard's rule on the ready record (T-CONTEXT); `docs/diagrams/D-003-review-round-states.md`, the merge reachable only from `ready_recorded`; the briefs `handoff/TASK-083.md`, `handoff/TASK-083-r2.md` and `handoff/TASK-083-r3.md`, whose requirements and Security context stand except where this brief rules otherwise.

**How gh finds the group and the subcommand** (cobra's `Find`, added to round 3's statement): a word is taken for a command only where it is not empty and does not begin with `-`; a gh command's name, and so every group and subcommand gh has, is made of ASCII letters, digits and `-`, beginning with a letter or digit. A word that is neither such a name nor an option is passed over by the search and handed to the subcommand.

**The code as of round 3's tree** (`bridge/cursor-bridge/permission-guard.py`): `gh_words` 2056-2083 (the repository options at 2063-2064, the `api` walk at 2065-2073, round 3's option refusal at 2074-2077 returning `(tok, None, [])`, the append at 2078); the gh branch of `_check_word_list` at 2315-2324, round 3's refusal at 2317-2318 (`_cannot("an option before the gh subcommand (%s)" % group)` where `group.startswith("-")`); `state_changing` 2368, its gh branch 2389-2393 (round 3's `return True` at 2391-2392); `_cannot(msg)` at 181; `merge_reason` 2568-2588, the number at 2579-2580.

**Security context.** As rounds 1 to 3: ASVS level 2 (V4.1.3, V4.2); the hook's command text is outside input; where the guard cannot read the command it refuses, never passes; Bash and PowerShell give the same verdict for every case of the new section.

**Development data.** As round 1: run the programs only from tests, on scratch folders under `tmp_path`; never run them against this repository's folder or its GitHub repository; never run `gh`; never install anything.

**Host.** Windows 11; Python as on the owner's interpreter. `claude` is not on PATH in this session; nothing here needs it.

## Diagrams
`docs/diagrams/D-003-review-round-states.md` (the supervisor's, drawn as built): the merge is reachable only from `ready_recorded`. The fix adds no state, no edge and no import between bridge programs. If the fix cannot be done within the diagram, stop and report the conflict.

## Requirements
Use the labels K1-K3 in your report.

1. **K1. Before the subcommand, only a command's name is read as one.** In `gh_words`, the word taken for the group, and, after a group other than `api`, the word taken for the subcommand, must match `[A-Za-z0-9][A-Za-z0-9-]*` whole; any other word standing there (the empty word, a word holding a space, a quote or any character outside that set) makes the command unreadable, as round 3's option before the subcommand does, wherever it stands before the subcommand. The repository options and their values (2063-2064) and round 3's last-word exception for an option (`gh --help`, `gh --version`, `gh pr --help`) stay as they are; after the group `api` the walk is today's. `gh_words` may mark an unreadable command in any way that does not depend on the word's first character (round 3's `group.startswith("-")` cannot carry an empty word); `check` refuses every unreadable gh command with `_cannot`, its text naming the word with Python's `repr` (`the guard cannot read the command: a word before the gh subcommand that is not a command's name ('')` for the empty word; round 3's text for an option may stay as it is), and `state_changing` counts every unreadable gh command as one that changes state. Tests: the first five commands of `test_r083_r4_a_word_that_is_not_a_command_name_before_the_subcommand_is_refused` under each shell (ten ids) and both ids of `test_r083_r4_an_empty_word_before_the_subcommand_is_unreadable_and_the_plain_merge_still_passes`; every round 1 to 3 case stays green, `test_r083_r3_the_records_still_decide_and_the_other_gh_forms_pass` among them.
2. **K2. An empty number is no number.** `merge_reason` refuses a number that is empty with round 1's no-number message (holding `gh pr merge <n> --squash --match-head-commit <sha>`), as it refuses one with a character outside `0`-`9`. Tests: the two ids of `gh pr merge '' --squash --match-head-commit <SHA>` in the round-4 refused case (they pass on round 3's tree through `ready_recorded` and must still pass); add one case of your own to `tests/test_permission_guard.py` under Bash that asserts the no-number message for `gh pr merge '' --squash --match-head-commit <SHA>` in a repository holding both records for that head.
3. **K3. Round 3's chain assertion tests what it says.** In `test_r083_r3_an_equals_form_before_the_bare_option_clears_it_and_the_option_is_state_changing`, replace the chain command `git status && gh --subject xx pr view 12` with `git status && gh --version pr view 12` (an option that `GH_READ` names, so only the unreadable branch of `state_changing` refuses the chain), and add beside it, in the same workspace, the chain `git status && gh pr view 12` asserted allowed. Keep the case's other assertions.

## Acceptance criteria
- [ ] Every case in `tests/test_program_ready.py` passes: rounds 1 to 3's 146 and the round-4 section's cases (the red ones named under Constraints, "Known failures", turn green; the others stay green).
- [ ] `python -m pytest -q tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_program_permission_guard.py` passes whole.
- [ ] `python -m pytest -q tests/test_d003_review_round_states.py tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_program_branch_rule.py tests/test_program_release_s_rows.py tests/test_task032_supervisor_guard.py tests/test_tests_windowless.py` passes whole.
- [ ] The defect is fixed at the mechanism named in the Objective: `gh_words` reads a word as the group or the subcommand only where it is a command's name, and `check` refuses every other word there.
- [ ] Every line of `permission-guard.py` outside the functions, branches and lines the Scope limits name is byte-identical to round 3's tree; `review-guard.py` and `bridge_env.py` are byte-identical to it.
- [ ] Bash and PowerShell give the same verdict for every id of the round-4 section.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `python tools/dump-cli.py --check` exits 0; `git status --short` does not list `bridge/cursor-bridge/VERSION` at the end.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-083 is met for this reading: no stand-in, placeholder or "later" text in the program.

## Constraints
- Fix the cause; never suppress a test's symptom. No special case for a test's values (no test of `''`, `12`, `OWNER/REPO` or the shas), no broad `try/except`, no `sleep`.
- Do not edit `tests/test_program_ready.py` or anything under `tests/fixtures/github/`.
- **Known failures.** On round 3's tree, `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py` gives the result in `run/agent/TASK-083-r4-known.out`, quoted here: `6 failed, 154 passed in 69.26s (0:01:09)`. The 6 red are the Bash ids of the first five commands of `test_r083_r4_a_word_that_is_not_a_command_name_before_the_subcommand_is_refused` and the Bash id of `test_r083_r4_an_empty_word_before_the_subcommand_is_unreadable_and_the_plain_merge_still_passes`; their PowerShell ids, the two ids of `gh pr merge '' ...`, and rounds 1 to 3's 146 pass on round 3's tree and must still pass. Every case in the file must pass after your change. If a case fails that this change did not cause, report it by its test id with its failure lines and fix none.
- **If you believe the defect's cause is different from the one named, stop, do not change code, and report why in your summary.** Likewise if an existing case in a file of the acceptance criteria requires the guard to read or pass a gh command whose group or subcommand is not a command's name: stop and report it by its test id.
- Prefer reuse: `_cannot` builds the refusal; round 3's handling of an option before the subcommand is the pattern. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security requirement stated above.
- Do not add dependencies; standard-library imports only (`re` is already imported).
- Do not read or write any file outside this workspace (the folder you were started in).
- No secret is needed or used.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`; do the same for anything you learned about a defect or a pitfall.
- In any Markdown you write, never break a line inside a paragraph or a list item.
- **Windowless launches.** In tests a launch needs no `creationflags` argument (`tests/conftest.py` makes every launch windowless); where a test does write one, that line carries the literal text `CREATE_NO_WINDOW`. Any string in a test that holds Python launch code is written in concatenated parts. Every subprocess call in a test has a timeout.
- **Run every command synchronously, in the foreground, and wait for it to end.** Start nothing in the background and leave no process running.
- **Do NOT run the full `tests/` tree.** Run only the test files the Done section names, exactly as written there, with no `PYTHONPATH` or other environment change.
- Do not refactor code outside the functions the requirements name.
- No value in this increment is the owner's (rule 52).
- ASCII program text and ASCII output, as the file's conventions are.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION`, at Done step 3. Never run `git -h`, `git help` or `git <cmd> --help` (on Git for Windows they open a browser window).
- **Mutation, by hand only.** Write no mutation script, in `handoff/` or anywhere, and apply none. You may change a line by hand in your editor to see a case fail, then restore it by hand; if you do, list each change and the test that caught it, and confirm with `git diff` before Done that no such change is left.
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root.

## Done
Your report is the file `handoff/TASK-083-r4-report.md`. Write it as you go. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for each of K1 to K3, one sentence on what changed, naming the functions and their lines as the file stands after your change;
- one sentence stating how the change addresses the defect's named cause;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section: one item per line, what you assumed - why - what would confirm it, or `Assumed, not verified: none`. Examples: whether any gh group or subcommand name holds a character outside letters, digits and `-`; whether an extension or alias the owner installs could carry such a name.

Run these from the Workspace root, in this order, after your last edit, each synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py`
3. `git restore bridge/cursor-bridge/VERSION`
4. `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)
5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
6. `python tools/dump-cli.py --check`
7. `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py`
8. `python -m pytest -p no:cacheprovider -q tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_program_permission_guard.py`
9. `python -m pytest -p no:cacheprovider -q tests/test_d003_review_round_states.py tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_program_branch_rule.py tests/test_program_release_s_rows.py tests/test_task032_supervisor_guard.py tests/test_tests_windowless.py`
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `git rev-parse HEAD` and `git status --short`

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; each pytest summary line verbatim; never restate a count in prose.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 11, naming the commit its counts belong to and whether the working tree then held uncommitted changes.

Your last message is the summary and the report file's path, and nothing follows it.
