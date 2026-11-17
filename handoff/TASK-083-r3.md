---
record: brief
header: 1
id: "TASK-083"
round: 3
satisfies: [R-083]
scope: ["bridge/cursor-bridge/permission-guard.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_ready.py", "tests/test_permission_guard.py", "docs/BUILDER_NOTES.md", "handoff/TASK-083-r3-report.md"]
merge_unit: null
blocking_class: "safety mechanism"
---
# TASK-083 round 3: an exemption switched off again is no exemption, and an option before a gh subcommand is unreadable (R-083)

Round cause: security

Blocking class: safety mechanism - Review A and the security audit of round 2, each reproduced in process: gh pr merge 12 --squash --match-head-commit <B> --disable-auto --disable-auto=false is allowed with neither record read while gh merges head B, and gh --subject xx pr merge 12 --squash --match-head-commit <B> is never read as a merge while gh merges pull request 12 at head B

## Objective
Fix the following confirmed defects in the permission guard, and nothing else.

This is round 3 of TASK-083, the last the ceiling gives. Round 1 built `review-guard.py ready <pr>`, the ready record and the guard's rule on it; round 2 made `merge_reason` read the words after `merge` once, as gh's flag parser (pflag) reads them (`_read_merge_words`). All of that stays as it is except what J1 and J2 below change. Review A and the security audit of round 2 found two more ways one command names one thing to the guard and another to gh. The supervisor commits round 2's tree together with this brief and the new tests before your run, so the line numbers below hold when you start.

**The confirmed defects** (each reproduced in process on round 2's tree by both reviewers and by the supervisor, each now a red test):
1. `_read_merge_words` (`bridge/cursor-bridge/permission-guard.py`, 2479-2548) sets `disable_auto` or `help_opt` when it meets the bare option `--disable-auto`, `--help` or `-h`, and never clears it. Its `=` branch (2501-2506) ignores every name but `--match-head-commit`, and `-h=false` falls through as a positional that is never checked because `merge_reason` (2550-2570) returns on the exemption at 2555 first. pflag sets a true/false option on each use, the last one standing, and reads `--disable-auto=false`, `=0`, `=f` and the like as false; cobra reads the help option's final value. So `gh pr merge 12 --squash --match-head-commit B --disable-auto --disable-auto=false` (and the same with `--help --help=false`, `-h -h=false`, `-h --help=false`) is allowed with neither record read, while gh merges head B. Round 2's brief (its rule "A string option given twice keeps the last value given") covered string options only; this brief adds the true/false ones.
2. `gh_words` (2056-2077), finding the group and the subcommand, skips every word beginning with `-` as one word, except `-R`, `--repo`, `--hostname` and, after any group, `GH_API_OPTS`. cobra, finding the subcommand, takes an option it does not know (a `--name` with no `=`, or a two-letter `-x`) as taking the next word, then hands every remaining word to the subcommand's own flag parser. So in `gh --subject xx pr merge 12 --squash --match-head-commit B` the guard reads the group as `xx`, never calls `merge_reason`, and allows, while gh merges pull request 12 at head B with the subject `xx`; the same with `-b xx`, `--author-email xx` before `pr`, and with `--subject xx` or `-t xx` between `pr` and `merge`. This function predates TASK-083 and was outside round 2's Scope; the merge gate rests on it.

**The reproduction tests:** `tests/test_program_ready.py`, the section headed `# ---------------------------------------------------------------- round 3: a true/false option given again, and an option before the subcommand`, at the end of the file. On round 2's tree the result is quoted under Constraints, "Known failures"; every case in the file must pass.

Satisfies: R-083 - One reader of a repository's branch rule, and the proof that CI passed as a program (T-CONTEXT, C7): [...] the permission guard requires the ready record for the merge command's pull request number and its `--match-head-commit` head, after and in the same way as its check of the premerge record, and refuses a merge that names no number. (Full text: its row in `docs/REQUIREMENTS.md`. This brief serves the guard's reading of a gh command's words.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_ready.py
- tests/test_permission_guard.py
- docs/BUILDER_NOTES.md
- handoff/TASK-083-r3-report.md

Limits on these files:
- `bridge/cursor-bridge/permission-guard.py`: only `_read_merge_words` and `merge_reason` (J1), and `gh_words`, the gh branch of `_check_word_list` (the lines from `elif head in ("gh", "gh.exe"):` at 2309 through its `gh api` merge-mutation refusal) and the gh branch of `state_changing` (2381-2383) (J2). `GH_VALUE_FLAGS`, `GH_API_OPTS`, `GH_READ` and every other function keep their value and behaviour; `ready_recorded`, `premerge_recorded` and round 2's reading of string options, clusters, `--` and positionals keep theirs.
- `tests/test_program_ready.py` is the supervisor's acceptance file. It is in Scope only so that its new section counts as this round's; you read and run it and **edit nothing in it**.
- `tests/test_permission_guard.py`: you may add cases below the existing R-083 cases; change no other case.
- `bridge/cursor-bridge/MANIFEST.json` changes only by being regenerated with `python tools/make-manifest.py` (Done). Never edit it by hand.
- `bridge/cursor-bridge/VERSION` is outside Scope; it reads `2026.11.12a`. Restore it with `git restore bridge/cursor-bridge/VERSION` right after the manifest (Done), and edit it in no other way.
- `handoff/TASK-083-r3-report.md` is your report. The reports of rounds 1 and 2 are the supervisor's records now; do not edit them.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, `docs/diagrams/` included.
- `bridge/cursor-bridge/review-guard.py`, `bridge/cursor-bridge/bridge_env.py`, `tests/test_review_guard.py`, `tests/test_release_s_records_gate.py`, `tests/test_d003_review_round_states.py`, `tests/fixtures/github/`, `docs/cli-reference.json`, `docs/CLI_REFERENCE.md`, and every other program and test file.
- `-R`/`--repo` and the environment variable `GH_REPO` aiming a merge at another repository stay allowed as today: the supervisor records them.
- The `gh api` walk after the group `api` (its options between `api` and the endpoint, `GH_API_OPTS`, `-X`/`--method` glued) stays exactly as it is.
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this round** is round 1's and round 2's: `docs/DESIGN.md`, "Change: the program release", the permission guard's rule on the ready record (T-CONTEXT); `docs/diagrams/D-003-review-round-states.md`, the merge reachable only from `ready_recorded`; the briefs `handoff/TASK-083.md` and `handoff/TASK-083-r2.md`, whose requirements and Security context stand except where this brief rules otherwise. The guard's precedent for J2 is `git_subcommand` (2389): an unknown dash word before git's subcommand is unreadable (`_GIT_UNREADABLE`), and `state_changing` counts such a command as one that changes state.

**How gh reads a true/false option** (pflag and cobra, added to round 2's rule): a true/false option (`--disable-auto`, `--help`, `-h`, and every other that takes no value) is set on each use, the last one standing; `--name=<v>` sets it to `<v>`, read as true or false by Go's `strconv.ParseBool` (`1`, `t`, `T`, `TRUE`, `true`, `True`, `0`, `f`, `F`, `FALSE`, `false`, `False`), any other `<v>` an error. A word of one dash and letters followed by `=` (`-h=false`, `-sh=false`) sets its last letter to the value after `=`.

**How gh finds the group and the subcommand** (cobra's `Find`, the root command not set to traverse children): words beginning with `-` before the subcommand are stripped; an option cobra does not know there (every option of the subcommand, `--subject` among them) is taken as taking the next word, unless it holds `=`; the remaining words go to the subcommand's flag parser, the options before the subcommand among them.

**The code as of round 2's tree** (`bridge/cursor-bridge/permission-guard.py`): `GH_VALUE_FLAGS` at 68; `INNER_UNREADABLE` at 74; `GH_API_OPTS` at 178; `_cannot(msg)` at 181 returns `the guard cannot read the command: <msg>`; `gh_words` 2056-2077; `check` 2104; the gh branch of `_check_word_list` at 2309-2315 (`group, sub, args = gh_words(w)`, then `merge_reason` where `group == "pr" and sub == "merge"`, then the `gh api` merge-mutation refusal); `state_changing` 2360, its gh branch 2381-2383; `git_subcommand` 2389; `ready_recorded` 2451; `_read_merge_words` 2479-2548; `merge_reason` 2550-2570, the exemption at 2555.

**Security context.** As rounds 1 and 2: ASVS level 2 (V4.1.3, V4.2: the access decision taken on the same reading of the request as the executor's); the hook's command text is outside input; where the guard cannot read the command it refuses, never passes. Bash and PowerShell give the same verdict for every case of the new section.

**Development data.** As round 1: run the programs only from tests, on scratch folders under `tmp_path`; never run them against this repository's folder or its GitHub repository; never run `gh`; never install anything.

**Host.** Windows 11; Python as on the owner's interpreter. `claude` is not on PATH in this session; nothing here needs it.

## Diagrams
`docs/diagrams/D-003-review-round-states.md` (the supervisor's, drawn as built): the merge is reachable only from `ready_recorded`. The fix adds no state, no edge and no import between bridge programs. If the fix cannot be done within the diagram, stop and report the conflict.

## Requirements
Use the labels J1-J3 in your report.

1. **J1. An exemption stands only where no `=` form of its option is given.** The `--disable-auto` exemption stands only where the reading finds the bare option `--disable-auto` and finds no option `--disable-auto=<v>`, whatever `<v>` is. The help exemption stands only where the reading finds `--help` or the word `-h` and finds no option `--help=<v>` and no single-dash word holding `=` whose letters before the `=` include `h` (`-h=false`, `-sh=false`), whatever `<v>` is. An `=` form found as an option clears the exemption and the command goes on to the record checks; a word that is a flag's value, or that stands after `--`, is not an option, as in round 2. Round 2's reading stays otherwise: a single-dash word holding `=` is still a positional for the number. Tests: the six `--disable-auto` and help ids of the round-3 section's refused case under each shell (twelve ids), and the two `=false` ids of `test_r083_r3_the_records_still_decide_and_the_other_gh_forms_pass` under each shell; round 2's `gh pr merge 12 --disable-auto`, `gh pr merge --help` and `gh pr merge -h` still pass.
2. **J2. An option before a gh subcommand is unreadable.** In `gh_words`, before the group is found, and after any group other than `api` before the subcommand is found, a word beginning with `-` other than `-R`, `--repo` or `--hostname` (with its value, as today) makes the command unreadable where any word follows it. `check` refuses an unreadable gh command with `_cannot`, its text naming the word (`the guard cannot read the command: an option before the gh subcommand (<word>)`), before any merge reading; `state_changing` counts it as a command that changes state, as it counts git's unreadable one. A word beginning with `-` that is the last word (`gh --help`, `gh --version`, `gh pr --help`) is read as today. After the group `api`, the walk is today's, unchanged. Tests: the five option-before-the-subcommand ids of the round-3 refused case under each shell (ten ids), both ids of `test_r083_r3_an_option_before_the_subcommand_is_unreadable_even_on_a_recorded_head`, and the seven other-form ids of `test_r083_r3_the_records_still_decide_and_the_other_gh_forms_pass` under each shell (fourteen ids).
3. **J3. The reading stated.** `_read_merge_words`' docstring and `gh_words`' (a docstring added) state the rules J1 and J2 implement in one sentence each.

You may add cases of your own to `tests/test_permission_guard.py` below its R-083 cases; each names `R-083` in its name or docstring and holds a Bash and a PowerShell id where it drives the hook. The supervisor's new cases cover J1 and J2; add one only where you find a gap, and say which.

## Acceptance criteria
- [ ] Every case in `tests/test_program_ready.py` passes: rounds 1 and 2's 104 and the round-3 section's cases (the red ones named under Constraints, "Known failures", turn green; the others stay green).
- [ ] `python -m pytest -q tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_program_permission_guard.py` passes whole.
- [ ] `python -m pytest -q tests/test_d003_review_round_states.py tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_program_branch_rule.py tests/test_program_release_s_rows.py tests/test_task032_supervisor_guard.py tests/test_tests_windowless.py` passes whole.
- [ ] Each defect is fixed at the mechanism named in the Objective: the exemptions are cleared by an `=` form of their option found by the one reading; `gh_words` makes an option before the subcommand unreadable and `check` refuses it.
- [ ] Every line of `permission-guard.py` outside the functions and branch the Scope limits name is byte-identical to round 2's tree; `review-guard.py` and `bridge_env.py` are byte-identical to it.
- [ ] Bash and PowerShell give the same verdict for every id of the round-3 section.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `python tools/dump-cli.py --check` exits 0; `git status --short` does not list `bridge/cursor-bridge/VERSION` at the end.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-083 is met for this reading: no stand-in, placeholder or "later" text in the program.

## Constraints
- Fix the causes; never suppress a test's symptom. No special case for a test's values (no test of `12`, `xx`, `OWNER/REPO` or the shas), no broad `try/except`, no `sleep`.
- Do not edit `tests/test_program_ready.py` or anything under `tests/fixtures/github/`.
- **Known failures.** On round 2's tree, `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py` gives the result in `run/agent/TASK-083-r3-known.out`, quoted here: `20 failed, 126 passed in 59.97s`. The 20 red are 18 ids of `test_r083_r3_an_exemption_switched_off_again_or_an_option_before_the_subcommand_is_refused` (every command under each shell except `... --disable-auto=true` and `gh pr -t xx merge ...`, which round 2 already refuses, the second only because `-t` is in `GH_API_OPTS`, and which must still be refused) and both ids of `test_r083_r3_an_option_before_the_subcommand_is_unreadable_even_on_a_recorded_head`; the 18 ids of `test_r083_r3_the_records_still_decide_and_the_other_gh_forms_pass` and rounds 1 and 2's 104 pass on round 2's tree and must still pass. Every case in the file must pass after your change. If a case fails that this change did not cause, report it by its test id with its failure lines and fix none.
- **If you believe a defect's cause is different from the one named, stop, do not change code, and report why in your summary.** Likewise if an existing case in a file of the acceptance criteria requires the guard to read or pass a gh command with an option before its subcommand other than `-R`, `--repo` or `--hostname` (outside `gh api`'s own walk): stop and report it by its test id.
- Prefer reuse: `_cannot` builds the refusal; round 2's `_read_merge_words` stays the one reading of the words after `merge`. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security requirement stated above.
- Do not add dependencies; standard-library imports only.
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
Your report is the file `handoff/TASK-083-r3-report.md`. Write it as you go. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for each of J1 to J3, one sentence on what changed, naming the functions and their lines as the file stands after your change;
- one sentence per defect of the Objective (1 and 2) stating how the change addresses its named cause;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section: one item per line, what you assumed - why - what would confirm it, or `Assumed, not verified: none`. Examples: whether any gh command the supervisor runs places an option other than the repository's before its subcommand; whether cobra reads `-h` before a subcommand as the root's help.

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
