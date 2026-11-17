---
record: brief
header: 1
id: "TASK-083"
round: 2
satisfies: [R-083]
scope: ["bridge/cursor-bridge/permission-guard.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_ready.py", "tests/test_permission_guard.py", "docs/BUILDER_NOTES.md", "handoff/TASK-083-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-083 round 2: the permission guard reads a merge command as gh reads it (R-083)

Round cause: security

## Objective
Fix the following confirmed defects in the permission guard's merge rule, and nothing else.

This is round 2 of TASK-083. Round 1 built `review-guard.py ready <pr>`, the ready record, `premerge-records`' same proof and the permission guard's rule that a merge needs the ready record for its pull request's number and its head; all of that stays as it is except what H1 to H3 below change. Review A and the security audit of round 1 found that the guard reads the words of `gh pr merge` differently from the way gh's flag parser (pflag) reads them, so one command can name one head or one pull request to the guard and another to gh. The supervisor commits round 1's tree together with this brief and the new tests before your run, so the line numbers below hold when you start.

**The confirmed defects** (each reproduced in process on round 1's tree, each now a red test):
1. `merge_reason` (`bridge/cursor-bridge/permission-guard.py`, 2479-2515) reads `--match-head-commit` at 2488-2493 from every word, the last one winning, without skipping the value of a flag. pflag gives a value-taking flag (`--subject`, `-t`, `--body`, `-b`, `--body-file`, `-F`, `--author-email`, `-A`, `--repo`, `-R`) the next word as its value even where that word begins with `-`. So `gh pr merge 12 --squash --match-head-commit B --subject --match-head-commit=A` is read by the guard as head A, whose records stand, while gh takes `--match-head-commit=A` as the subject and merges head B, which has none.
2. `if "--disable-auto" in args: return None` (2483) allows the command before any record is read, even where `--disable-auto` is only a flag's value: `gh pr merge 12 --squash --subject --disable-auto` merges with no premerge record and no ready record.
3. The number walk (2498-2508) skips every word that begins with `-` as one option. pflag reads a word of one dash and several letters as a cluster of short flags, letter by letter: at the first letter that takes a value, the rest of the word is that value, or, where that letter is the last, the next word is. So in `gh pr merge -sb 12 34 --match-head-commit A` gh merges pull request 34 with the body `12`, while the guard reads 12 as the number: pull request 34 merges on pull request 12's ready record, which the design says proves nothing for it (two pull requests sharing one head, S14). Round 1's brief (R11, "the value of an option in GH_VALUE_FLAGS given as a separate word") caused this; this brief replaces that wording.

**One weak test and one hardening:** round 1's `tests/test_permission_guard.py::test_r083_ready_recorded_fails_closed_outside_a_repository` never shows `ready_recorded` true anywhere, so a body of `return False` passes it (H4); and `ready_recorded`'s prefix match accepts the temporary file `<pr>-<head>.tmp` that `review-guard.py`'s `_write_json` leaves where a write is killed between its dump and its rename (H3).

**The reproduction tests:** `tests/test_program_ready.py`, the section headed `# ---------------------------------------------------------------- round 2: the merge command read as gh reads it`, at the end of the file. On round 1's tree the result is quoted under Constraints, "Known failures"; every case in the file must pass.

Satisfies: R-083 - One reader of a repository's branch rule, and the proof that CI passed as a program (T-CONTEXT, C7): [...] the permission guard requires the ready record for the merge command's pull request number and its `--match-head-commit` head, after and in the same way as its check of the premerge record, and refuses a merge that names no number. (Full text: its row in `docs/REQUIREMENTS.md`. This brief serves the guard's reading of the merge command's words.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_ready.py
- tests/test_permission_guard.py
- docs/BUILDER_NOTES.md
- handoff/TASK-083-r2-report.md

Limits on these files:
- `bridge/cursor-bridge/permission-guard.py`: only `merge_reason` (2479-2515) and `ready_recorded` (2451-2476), as H1 to H3 say, and a new helper beside them if H1 needs one. `GH_VALUE_FLAGS` (line 68) keeps its value; read it, do not edit it. Every other function, the hook's `main`, and every other refusal keep their behaviour.
- `tests/test_program_ready.py` is the supervisor's acceptance file. It is in Scope only so that its new section counts as this round's; you read and run it and **edit nothing in it**.
- `tests/test_permission_guard.py`: delete the case `test_r083_ready_recorded_fails_closed_outside_a_repository` (lines 272-276; its ground is now `tests/test_program_ready.py::test_r083_r2_ready_recorded_is_true_only_for_its_pull_request_and_head_inside_the_repository`, which shows both sides). You may add cases below the existing R-083 cases; change no other case.
- `bridge/cursor-bridge/MANIFEST.json` changes only by being regenerated with `python tools/make-manifest.py` (Done). Never edit it by hand.
- `bridge/cursor-bridge/VERSION` is outside Scope; it reads `2026.11.12a`. Restore it with `git restore bridge/cursor-bridge/VERSION` right after the manifest (Done), and edit it in no other way.
- `handoff/TASK-083-r2-report.md` is your report. Round 1's report, `handoff/TASK-083-r1-report.md`, is the supervisor's record now; do not edit it.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, `docs/diagrams/` included.
- `bridge/cursor-bridge/review-guard.py` (round 1's `ready`, `prove_ci` and `premerge-records` stand as they are), `bridge/cursor-bridge/bridge_env.py`, `tests/test_review_guard.py`, `tests/test_release_s_records_gate.py`, `tests/test_d003_review_round_states.py`, `tests/fixtures/github/`, `docs/cli-reference.json`, `docs/CLI_REFERENCE.md`, and every other program and test file.
- The `--admin` refusal (2481-2482) stays as it is: it refuses the word wherever it stands, a flag's value included, which fails closed.
- The audit's other advisories (`-R`/`--repo` and the environment variable `GH_REPO` aiming the merge at another repository; `premerge-records` passing its argument to `gh pr view` before a digit check): the supervisor records them.
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this round** is round 1's: `docs/DESIGN.md`, "Change: the program release", the review guard's `ready` (T-CONTEXT) and the permission guard's rule on the ready record; `docs/diagrams/D-003-review-round-states.md`, the edge `premerged --> premerged` (a merge before READY refused, or one naming no number) and `ready_recorded --> [*]` (the number taken from the merge command); the brief `handoff/TASK-083.md` (round 1), whose R1-R14 and Security context stand except where this brief rules otherwise.

**How gh reads the words after `gh pr merge`** (pflag, the parser gh is built on; this is the rule H1 implements):
- A word that is exactly `--` ends the options: every word after it is a positional, whatever it begins with.
- A word `--name=value` is the option `name` with that value; it takes no further word.
- A word `--name` with no `=`: where `--name` is a long form in `GH_VALUE_FLAGS`, the next word is its value, whatever it begins with; otherwise it is an option that takes no value.
- A word of one dash and one or more letters (`-s`, `-sb`, `-stdone`) is a cluster of short flags, read letter by letter from the left: a letter that is a short form in `GH_VALUE_FLAGS` (`t`, `b`, `F`, `A`, `R`) takes the rest of the word as its value where any rest remains (`-stdone`: `t` takes `done`), or else the next word (`-st done`); the letters before it take no value; the cluster ends there.
- A word that is exactly `-`, and every other word, is a positional.
- A string option given twice keeps the last value given.

**The code as of round 1's tree** (`bridge/cursor-bridge/permission-guard.py`): `GH_VALUE_FLAGS` at line 68 (`-t`, `--subject`, `-b`, `--body`, `-F`, `--body-file`, `-A`, `--author-email`, `-R`, `--repo`, `--match-head-commit`, `--hostname`); `premerge_recorded` ends at 2448; `ready_recorded` 2451-2476; `merge_reason` 2479-2515: the `--admin` refusal 2481-2482, the `--disable-auto` exemption 2483-2484, the help exemption 2485-2487, the sha loop 2488-2493, the sha's two refusals 2494-2497, the number walk 2498-2508, the number refusal 2509-2510, then `premerge_recorded` 2511-2512 and `ready_recorded` 2513-2514.

**Security context.** As round 1: ASVS level 2 (V4.1.3, V4.2: an access-control decision is taken on the same reading of the request as the executor's); the hook's command text is outside input; where the guard cannot read the command it refuses, never passes. The guard's verdicts under Bash and PowerShell agree for every case of the new section.

**Development data.** As round 1: run the programs only from tests, on scratch folders under `tmp_path`; never run them against this repository's folder or its GitHub repository; never run `gh`; never install anything.

**Host.** Windows 11; Python as on the owner's interpreter. `claude` is not on PATH in this session; nothing here needs it.

## Diagrams
`docs/diagrams/D-003-review-round-states.md` (the supervisor's, already drawn as built): the merge is reachable only from `ready_recorded`, the guard reading the premerge record by the head the command names and the ready record by that head and the pull request's number. The fix adds no state, no edge and no import between bridge programs. If the fix cannot be done within the diagram, stop and report the conflict.

## Requirements
Use the labels H1-H4 in your report.

1. **H1. One reading of the merge command's words.** `merge_reason` reads the words after `merge` once, by the rule under Context, "How gh reads the words after `gh pr merge`", and takes from that one reading: (a) the sha, the value of the last `--match-head-commit` option (`--match-head-commit X` or `--match-head-commit=X`); (b) the exemptions, `--disable-auto` and the help (`--help`, or the cluster `-h` alone), only where the reading finds them as options, never as a flag's value or after `--`; (c) the number, the one positional. The order of the refusals and every message stay as round 1 has them: `--admin`; then the exemptions; then no sha, a malformed sha; then the number (none, more than one positional, or one that is not ASCII digits `0`-`9`: refused with round 1's message holding `gh pr merge <n> --squash --match-head-commit <sha>`); then `premerge_recorded`; then `ready_recorded`. A value-taking flag that is the last word (no value follows) is read as having the empty value. Tests: every id of `test_r083_r2_a_word_that_is_a_flags_value_is_never_the_sha_the_exemption_or_the_number` and of `test_r083_r2_the_forms_gh_reads_as_pull_request_12_at_sha_pass`; every round-1 case of the file stays green, `test_r083_the_guard_s_other_forms_are_unchanged` among them.
2. **H2. No other exemption.** Nothing returns None from `merge_reason` before the records are read except `--disable-auto` and the help found as options by H1. Tests: the `--disable-auto` and `--help` ids of the H1 refused case; `gh pr merge 12 --disable-auto` and `gh pr merge --help` still pass (round 1's unchanged-forms case).
3. **H3. A half-written ready record is no record.** `ready_recorded` never counts a name that ends in `.tmp`. Its other behaviour stays: a short sha of 7 to 64 hex digits matches the start of the head in the name, the `-` keeping `12` apart from `123`. Tests: both ids of `test_r083_r2_a_ready_record_left_half_written_is_no_record`, and `test_r083_r2_ready_recorded_is_true_only_for_its_pull_request_and_head_inside_the_repository`.
4. **H4. The weak case goes.** Delete `test_r083_ready_recorded_fails_closed_outside_a_repository` from `tests/test_permission_guard.py`, as the Scope limit says.

You may add cases of your own to `tests/test_permission_guard.py` below its R-083 cases; each names `R-083` in its name or docstring and holds a Bash and a PowerShell id where it drives the hook. The supervisor's new cases cover H1 to H3; add one only where you find a gap, and say which.

## Acceptance criteria
- [ ] Every case in `tests/test_program_ready.py` passes: round 1's 65 and the round-2 section's cases (the red ones named under Constraints, "Known failures", turn green; the others stay green).
- [ ] `python -m pytest -q tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_program_permission_guard.py` passes whole.
- [ ] `python -m pytest -q tests/test_d003_review_round_states.py tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_program_branch_rule.py tests/test_program_release_s_rows.py tests/test_tests_windowless.py` passes whole.
- [ ] Each defect is fixed at the mechanism named in the Objective: the sha, the exemptions and the number come from one reading of the words that skips every flag's value as pflag does, clusters included; `ready_recorded` refuses a `.tmp` name.
- [ ] Every line of `permission-guard.py` outside `merge_reason`, `ready_recorded` and a helper H1 adds is byte-identical to round 1's tree; `review-guard.py` and `bridge_env.py` are byte-identical to it.
- [ ] Bash and PowerShell give the same verdict for every id of the round-2 section (each case runs under both).
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `python tools/dump-cli.py --check` exits 0; `git status --short` does not list `bridge/cursor-bridge/VERSION` at the end.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-083 is met for this reading: no stand-in, placeholder or "later" text in the program.

## Constraints
- Fix the causes; never suppress a test's symptom. No special case for a test's values (no test of `12`, `34`, the shas, `done` or `x`), no broad `try/except`, no `sleep`.
- Do not edit `tests/test_program_ready.py` or anything under `tests/fixtures/github/`.
- **Known failures.** On round 1's tree, `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py` gives the result in `run/agent/TASK-083-r2-known.out`, quoted here: `22 failed, 82 passed in 47.88s`. The 22 red are the 20 ids of `test_r083_r2_a_word_that_is_a_flags_value_is_never_the_sha_the_exemption_or_the_number` other than the two of `gh pr merge 12 --squash -t --help --match-head-commit <OTHER>` (which round 1 already refuses and which must still be refused), and the 2 ids of `test_r083_r2_a_ready_record_left_half_written_is_no_record`; the 14 ids of `test_r083_r2_the_forms_gh_reads_as_pull_request_12_at_sha_pass`, `test_r083_r2_ready_recorded_is_true_only_for_its_pull_request_and_head_inside_the_repository` and round 1's 65 pass on round 1's tree and must still pass. Every case in the file must pass after your change. If a case fails that this change did not cause, report it by its test id with its failure lines and fix none.
- **If you believe a defect's cause is different from the one named, stop, do not change code, and report why in your summary.** Likewise if an existing case requires the guard to pass a form H1 reads as another head or another pull request: stop and report it by its test id.
- Prefer reuse: `GH_VALUE_FLAGS` names the value-taking flags; `premerge_recorded` and `ready_recorded` stay the record readers. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security requirement stated above.
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
- **Mutation, by hand only.** Round 1's note in `docs/BUILDER_NOTES.md` says a script applied mutants to the product files in place; this round writes no mutation script, in `handoff/` or anywhere, and applies none. You may change a line by hand in your editor to see a case fail, then restore it by hand; if you do, list each change and the test that caught it, and confirm with `git diff` before Done that no such change is left.
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root.

## Done
Your report is the file `handoff/TASK-083-r2-report.md`. Write it as you go. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for each of H1 to H4, one sentence on what changed, naming the functions and their lines as the file stands after your change;
- one sentence per defect of the Objective (1 to 3) stating how the change addresses its named cause;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section: one item per line, what you assumed · why · what would confirm it, or `Assumed, not verified: none`. Examples: whether gh's `pr merge` has a short flag that takes a value beyond `t`, `b`, `F`, `A` and `R`; whether pflag reads `-` alone as a positional; whether gh refuses a second positional before it merges.

Run these from the Workspace root, in this order, after your last edit, each synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py`
3. `git restore bridge/cursor-bridge/VERSION`
4. `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)
5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
6. `python tools/dump-cli.py --check`
7. `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py`
8. `python -m pytest -p no:cacheprovider -q tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_program_permission_guard.py`
9. `python -m pytest -p no:cacheprovider -q tests/test_d003_review_round_states.py tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_program_branch_rule.py tests/test_program_release_s_rows.py tests/test_tests_windowless.py`
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `git rev-parse HEAD` and `git status --short`

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; each pytest summary line verbatim; never restate a count in prose.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 11, naming the commit its counts belong to and whether the working tree then held uncommitted changes.

Your last message is the summary and the report file's path, and nothing follows it.
