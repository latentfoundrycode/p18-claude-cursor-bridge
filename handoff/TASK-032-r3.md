# TASK-032-r3: The code-review ceiling held by the launcher and the guard — round 3

## Objective
Finish TASK-032, round 3 of its three. Rounds 1 and 2 (your runs of `handoff/TASK-032.md` and `handoff/TASK-032-r2.md`, committed as 2dddd9b and e28721f) left the defects listed below. The supervisor has since written the acceptance tests itself:
- `tests/test_task032_supervisor_launcher.py`: 88 tests, of which 20 fail on round 2's code;
- `tests/test_task032_supervisor_guard.py`: 143 tests, of which 13 fail.

They cover every case of clause (e) and every ruling of round 2. This round makes every one of them pass, fixes every defect below, and touches nothing else.

`handoff/TASK-032.md` and `handoff/TASK-032-r2.md` stay normative. Read both whole first, then this file. Where they disagree, this file wins, then r2, then the first brief.

This is the last round under the ceiling. After it, only a defect of one of the five blocking classes (behaviour against the brief, security, data integrity, a defeated safety mechanism, a failing test) can send the work back. Any other finding stays recorded. Fix everything listed here now.

Satisfies: R-042 (docs/REQUIREMENTS.md, line 48).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_bridge_run_review_ceiling.py
- tests/test_review_guard_ceiling.py
- tests/test_bridge_run_design_ceiling.py
- tests/test_permission_guard.py
- tests/test_review_guard.py
- tests/test_review_guard_a4.py
- tests/test_bridge_run.py
- tests/test_hotfix25a_guard_scope_invisible.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-032-r3-report.md

Do not modify anything else.

**Read-only, the supervisor's:** `tests/test_task032_supervisor_launcher.py` and `tests/test_task032_supervisor_guard.py`. Read them, run them, never edit them. If you believe a test there is wrong, say so in your report with the reason; never change it, skip it or work around it.

## Out of scope
Everything `handoff/TASK-032.md` lists under "Out of scope", unchanged. Do not edit any earlier brief or report.

## How to work
1. Run the two supervisor files: `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider -rf`. Read each failure, and read the test: its docstring names the paragraph it enforces.
2. Fix the code, defect by defect, following the list below. Run the two files after each group of fixes.
3. Then fix the existing tests listed under "Existing tests". Update the docstrings and regenerate the command reference and the manifest.
4. Run every verification command. Write the report.

## Defects to fix, all of them
Line numbers are those of e28721f.

**Launcher (`bridge-run.py`, `bridge_env.py`)**

L1. **The branch logged and counted is the `--workspace` folder's.** `main()` calls `workspace_of` on the already-resolved argv (`cmd.exe /d /c ...`, bridge-run.py:1511-1512), where `is_agent_argv` is false, so the launch folder's branch is logged. Compute the workspace folder, its branch and the brief once, from the original `cursor-agent` argv, before `resolve()`, and use those values for the refusals and for the log line. This fails the supervisor's `brief_read_from_workspace_folder`, `two_worktrees_each_round_one` and `reads_its_own_launch_folder_log`.

L2. **The heading check (R2).**
- The brief's own ID is never checked against the headings.
- Only the IDs a `Merge unit:` line declares are checked, and every one of them is checked: a non-TASK token (`Notes`, `FOO-1`) or a `TASK-010X` that is no heading refuses (bridge-run.py:635-641).
- A records subject's own ID, on its SCOPE file's unit line, is exempt.

L3. **Merge-unit tokens are bare IDs (R19).** Every token on a `Merge unit:` line must parse to `(token, 1)` with no `-r<N>` part. `TASK-015-r2`, `TASK-015-r05` and `TASK-015-R2` refuse the brief with the brief-rule prefix (bridge_env.py:436). The line is matched case-sensitively.

L4. **A later brief naming more IDs (clause (b)).** When a later brief's declared set is a proper superset of the branch's declared set, it is refused with its own message ("names more IDs than the branch's first brief: <set>"), and the owner's line does not change that. The owner's line for an outside ID allows that ID's own briefs, which declare no unit line of their own, and leaves the set unchanged. A brief under an outside ID with no lift gets the branch-rule message naming the counted IDs. Fix the inverted condition (bridge-run.py:643-646).

L5. **The class-line repeat rule (R8).** A relaunch of the same brief name with identical bytes is always allowed, whatever the earlier run's exit, and adds no round. Today only a relaunch matching an exit-0 run is exempt (bridge-run.py:670).

L6. **The class line matched exactly (R19).** `BLOCKING_CLASS_RE` loses `re.I`, and the class is never lower-cased: only the five names exactly as written are accepted (bridge_env.py:322-325, :370). The prefix `Blocking class:` is matched case-sensitively too. The reader returns the first well-formed line, skipping malformed ones.

L7. **The squash reader (R6).** `squash_merged_ids(folder, id_pattern)` takes the pattern as a string (a compiled pattern may also be accepted).
- The Merge form is tried first, with the branch ID read as `plan-check.py` reads it. Under `TASK-\d{3,}[a-z]?`, `Merge pull request #14 from x/task-014-retry` gives `TASK-014`, as `plan-check.py` does (bridge_env.py:490, :457-467).
- Under the grammar's pattern, the Merge form's branch is matched against the grammar's ID (case-insensitively, lower-cased branch), and the trailing letter is kept.
- The subject form takes only tokens holding a hyphen and a digit, so `Plan`, `Fix`, `Revert` and `Merge` are never IDs.
- The closing-parenthesis form reads `Fix it (BUG-020)` as `BUG-020`.
- Under `plan-check.py`'s pattern, the reader returns exactly what `plan-check.py`'s `merged_ids` returns, on every subject.

L8. **Malformed records never crash (R17).**
- `read_log`, `owner_cap`, the RUN_PARAMETERS.md readers and the brief reader decode with `errors="replace"`, or catch `UnicodeDecodeError` and `ValueError` beside `OSError` (bridge-run.py:381-382, :421-422).
- `completed_brief_run` and `class_used` read through `bridge_env.read_runs_jsonl`, so every field is type-checked in one place (bridge-run.py:558-560, :661).
- Type-check `id` (str) in `_event_time_launcher` (bridge_env.py:600-601), and `brief_name` (str) at bridge_env.py:724-725.
- Another ID's malformed rounds file (`{"rounds": 5}`, a list `branch`, an int `time` mixed with str times, `merge_ids: 5`) is skipped by the launcher, never a traceback (bridge_env.py:646-661).
- `int()` on a long digit string: `parse_review_name` catches `ValueError` and refuses (bridge_env.py:358). The 5,000-digit `<N>` refuses in the launcher and the guard.
- `roster_builder_model` catches `RecursionError` (bridge-run.py:541-549).
- `git_common_dir` and `branch_of` catch `subprocess.TimeoutExpired`, and decode with `errors="replace"` (bridge-run.py:523-539).

L9. **Messages (R20).**
- Every refusal line in `bridge-run.py`, the brief rule's included (bridge-run.py:602, 605, 607, 611, 615, 627, 671, 673, 674, 675), goes through `_ascii_refusal`.
- Every brief-rule refusal ends with the pointer `workflow/phases/delegation-loop.md, "3. Delegate to Cursor"` (the two-brief refusal at :607 too).
- The ceiling's message names both lifts in their forms: `Blocking class: <class> - <finding>` in the brief, and `Review rounds above the ceiling: <ID> <rounds> (<their words>, <date>)` in docs/RUN_PARAMETERS.md (bridge-run.py:675).

L10. **The owner's line is read from the launch folder** (the folder the launcher reads its records from), not from the `--workspace` folder (bridge-run.py:593).

**Guard (`review-guard.py`)**

G1. **Tamper check before seeding (R13).** `load_rounds` runs the tamper check first.
- A hash copy present beside a missing rounds file refuses with `review-guard: refused - rounds record changed outside the guard: <ID>`, before any seeding (review-guard.py:487-495).
- Seeding happens only when neither the file nor its copy exists.

G2. **Nothing written by a refused snapshot or by `verify` (clause (c), R11).**
- Seeding builds the record in memory. It is written only when the snapshot is accepted (review-guard.py:491-492).
- `verify` never creates or seeds a rounds file: with no rounds file, it records nothing in it (review-guard.py:884-890).
- A refused snapshot does not create `.git/bridge/no-hooks/` either: make every refusal check before the first `run_git` call that creates it, or create that folder only on the accepted path. If that cannot be done without weakening the guard's hook neutralisation, say so in your report and leave it.

G3. **A seeded round with a reply counts as reviewed (R14, R10).** A seeded round's tree is empty (review-guard.py:453). A re-snapshot of a round that has a reply and an empty tree is refused like one on another tree (review-guard.py:578).

G4. **A re-snapshot reuses the round's recorded lift (R8, R10).** For `N == current`, the ceiling is satisfied by the round's recorded `lift`. No class line is needed, and the round's own recorded line does not count as "already recorded" (review-guard.py:594-602). The round's `time` is not rewritten by a re-snapshot (review-guard.py:697, :708).

G5. **The class-line repeat refusal's message** begins `review-guard: refused - review ceiling: ` (review-guard.py:590).

G6. **The declared set without a launcher line (R4).**
- The guard writes `merge_ids` on the round it opens: the set read from the branch's first brief `handoff/<ID>.md` (or `<ID>-r<N>.md`), its `Merge unit:` line, read from the checkout.
- For a records subject with no brief, the set comes from its `run/review/SCOPE-<ID>.md` unit line, else the one ID.
- `_branch_events` uses that set (bridge_env.py:646-660). Call or remove `_declared_from_brief_folder` (bridge_env.py:605).
- An increment's own SCOPE file never supplies the set.

G7. **Outside git (R15):** the guard refuses a counted snapshot with exit 125 and `review-guard: refused - branch rule: reviews run on a branch, not a folder outside git` (review-guard.py:629-632). The other commands keep today's behaviour outside git.

G8. **The guard's lapse git calls** (`git log main`, `rev-parse --verify`, bridge_env.py:473, :522, reached from review-guard.py:562) run with hooks and the file monitor neutralised. Give the `bridge_env` helpers a parameter for the git runner, and have the guard pass its `run_git`.

G9. **Letter seeding** counts the letter snapshots whose branch equals the base snapshot's branch, in order, up to the first gap. One snapshot of another branch, or one unreadable file, does not make the count 0 (review-guard.py:412-418).

**One copy, dead code (R16, R18)**

C1. **One ID pattern.** The ID pattern is one constant in `bridge_env.py`, and `_REVIEW_NAME_RX`, `REVIEW_LIFT_RE` and `MERGE_UNIT_RE` are built from it (bridge_env.py:315, :319, :328).

C2. **Remove dead code.**
- `_cursor_agent_probe` and `_inside_bridge_run_cursor_agent` (permission-guard.py:104-133);
- `GIT_SHORT` (review-guard.py:85);
- the unused `test_round` (review-guard.py:593).

C3. **No second copies.**
- `rounds_hash_copy_path` reuses `hash_copy_path`'s key computation (review-guard.py:336-339, :265-271).
- The SCOPE file's class line is read by one function, not inline at :580-587 as well as in `scope_blocking_line`.
- `SCOPE-STAGE-<id>` is not tried for an ID that already begins `STAGE-`.

C4. **ASCII.** `bridge_env.py` stays ASCII-only, and no non-ASCII byte is added to the other three programs. The non-ASCII bytes already present at cec417a (bridge-run.py:19-20; permission-guard.py:5, 6, 33, 36, 39, 40, 331) stay as they are: that is the supervisor's ruling, replacing r2's criterion that all four be ASCII-only.

**Docstrings (requirement 14)**

D1. The module docstrings of `bridge-run.py`, `review-guard.py`, `permission-guard.py` and `bridge_env.py` describe the new rules, refusals and exit codes:
- `bridge-run.py`: the brief rule, the review-launch refusals, the branch rule and its lapse, `main`, detached and outside git, the ceiling and its two lifts, the revised-in-place rule, the class-line repeat rule, and the log's new fields;
- `review-guard.py`: the grammar, the rounds record and its hash copy, the round arithmetic, seeding, the ceiling and its lifts, the branch rule, and exit 125;
- `permission-guard.py`: the `handoff/` and `run/review/` rule;
- `bridge_env.py`: its new contents. Its "Writes nothing but ..." sentence is made true.

Then regenerate the command reference (`python tools/dump-cli.py`).

## Existing tests to fix
E1. `tests/test_review_guard.py:155-158`. `test_detached_snapshot_with_a_planted_hook` lost its point. Restore its assertion that `verify` never runs the reviewer's planted hook on a detached snapshot, using a `DESIGN-` name, which R15 exempts, so the snapshot is accepted on the detached HEAD. Keep the 125 refusal of a counted name beside it.

E2. `tests/test_review_guard.py:225-249`, as R22 ruled.
- Revert the extra "after review" commit unless the test needs it.
- After the `TASK-001-r2` snapshot, assert that `premerge TASK-001` is refused and that `verified-TASK-001.json` is gone.

E3. `tests/test_review_guard.py:113-117` and `:168-182`, as R23 ruled.
- Remove the `REVIEW-TASK-002.diff` and `REVIEW-TASK-003.diff` input files and their commits.
- The second ID's branch is `task-002`.

E4. `tests/test_bridge_run_review_ceiling.py:300`. Drop `bad.strip()`: the trailing-newline case must reach the grammar as written.

E5. `tests/test_bridge_run_design_ceiling.py:47`. Assert the full phrase `design.md, "The launcher holds the ceiling"`.

## Acceptance criteria
- [ ] `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider` reports 0 failed. Both files are unchanged: `git diff --quiet 88a60a6 -- tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py`.
- [ ] Every defect L1-L10, G1-G9, C1-C4 and D1, and every fix E1-E5, is done.
- [ ] Every acceptance criterion of `handoff/TASK-032.md` and `handoff/TASK-032-r2.md` still holds, except r2's all-four-ASCII criterion, which C4 replaces.
- [ ] All the verification commands below pass.

## Constraints
Every constraint of `handoff/TASK-032.md` holds, among them:
- no real `cursor-agent` or model;
- no real home;
- windowless launches;
- no git command of yours in this Workspace beyond `status`, `diff` and `log`;
- the owner's number, 3;
- no new dependency;
- no hard line wraps in Markdown;
- do not refactor outside what this file asks.

Run these verification commands, from the Workspace root:
- `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider`
- `python -m pytest tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_permission_guard.py tests/test_hotfix25a_guard_scope_invisible.py -q -p no:cacheprovider`
- `python -m pytest tests/test_bug029_agent_name.py tests/test_bridge_run_slot.py tests/test_bridge_run_driver.py tests/test_hotfix25a_roster_launcher.py tests/test_allowlist.py tests/test_loop_guard.py -q -p no:cacheprovider`. These are outside your Scope: run them, never edit them, and name any failure.
- `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py bridge/cursor-bridge/permission-guard.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py`
- `python tools/dump-cli.py`, then `python tools/dump-cli.py --check`
- `python tools/make-manifest.py`, last, after every program edit
- `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` (must end OK)

**Mutation check, by hand, in your own run.** Apply each mutation, run the two supervisor files, and restore the code before the next. List each with the test that caught it. No script lands in the diff. The mutations:
1. The class match made case-insensitive again.
2. The tamper check moved after seeding.
3. `verify` allowed to create a missing rounds file.
4. A seeded round's empty tree treated as "not reviewed".
5. A re-snapshot ignoring the recorded lift.
6. The superset check inverted again.
7. The Merge form tried after the subject form.
8. The workspace branch replaced by the launch folder's branch.

## Done
Your report is `handoff/TASK-032-r3-report.md`. Write it as you go. When you finish, it holds:
- the files you changed;
- a one-paragraph summary;
- a table of L1-L10, G1-G9, C1-C4, D1 and E1-E5, each with what you did and file:line;
- the eight mutations with their catching tests;
- every verification command's output (pass and fail counts);
- every supervisor test you believe wrong, with the reason (expected: none);
- a section headed exactly `Assumed, not verified`: one item per line, in the form what you assumed · why · what would confirm it, or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
