# TASK-032-r2: The code-review ceiling held by the launcher and the guard — round 2

## Objective
Finish TASK-032. Round 1 (your run of `handoff/TASK-032.md`, committed as 2dddd9b) delivered part of the increment: the reviewer (Review A) found the seeding of the rounds record unbuilt, about 40 of clause (e)'s cases without a test, 12 of the 15 hand mutations not run, and the defects listed below. This round implements everything still missing and fixes every defect, on top of the round-1 code that is already in the tree. `handoff/TASK-032.md` stays normative, every word of it: **read it whole first**, then this file, which adds the corrections and the supervisor's rulings on what the first brief left open. Where this file and `handoff/TASK-032.md` disagree, this file wins.

Satisfies: R-042 (docs/REQUIREMENTS.md, line 48), as `handoff/TASK-032.md` says.

This is round 2 of the increment's three. The work is done only when every case of clause (e) is a passing test, every defect below is fixed and covered, and all seventeen hand mutations below have been run. A partial delivery costs the increment its last round. Write the tests first, then make them pass.

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
- handoff/TASK-032-r2-report.md

Do not modify anything else.

## Out of scope
Everything `handoff/TASK-032.md` lists under "Out of scope", unchanged. Do not edit `handoff/TASK-032.md` or `handoff/TASK-032-r1-report.md`.

## Context
Read `handoff/TASK-032.md`'s Context section: it describes the code as it stood at the checkpoint (cec417a), and still holds for every line you did not change in round 1. Your round-1 changes are `git diff cec417a 2dddd9b`; read them before you start. The line numbers below are those of 2dddd9b.

## Rulings (the supervisor's decisions on what the first brief left open)
Implement these exactly. Each is a requirement of this round.

R1. **Which run log.** The launcher reads `run/launcher/runs.jsonl` from its launch folder, the folder `write_log` writes to, never from the `--workspace` folder. The brief's bytes and the branch are still read from the `workspace_of` folder. The guard reads the launcher's log from the main checkout: the parent of the git common directory (`common`), not the worktree `root`.

R2. **Increment headings.** Only the IDs a `Merge unit:` line declares must be increment headings of `docs/BUILD_PLAN.md`. A brief with no such line (`handoff/BUG-019.md`, a HOTFIX, CONFIG or REFAC brief) is never refused for its ID not being a heading, and a workspace without `docs/BUILD_PLAN.md` refuses only a brief whose `Merge unit:` line it cannot check. Headings are read exactly as `plan-check.py` reads them: its `HEAD_RX` with its own ID pattern `TASK-\d{3,}[a-z]?`, so `### Notes` is no heading.

R3. **The branch's events, in time order.** The branch rule reads both records as one list of events ordered by time: the launcher's lines by their run id (the launch time) and the guard's rounds by their recorded time. The branch's declared set is the set of its earliest event whose claim has not lapsed. Once the counted IDs have lapsed (merged on `main`, or the branch gone), every earlier event of that branch is ignored, and the next brief or snapshot on the branch claims it afresh.

R4. **The guard's declared set without a launcher line.** Where the branch has no launcher line, the guard reads the declared set from the branch's first brief: the `handoff/<ID>.md` (or `<ID>-r<N>.md`) of the ID its first event names, read from the checkout, its `Merge unit:` line giving the set. For a records subject with no brief, the set is the `Merge unit:` line of its `run/review/SCOPE-<ID>.md`, else the one ID. As clause (c) says, an increment's own SCOPE file never supplies the set; a SCOPE file supplies it only where no brief of that ID exists.

R5. **The lapse.** The claim lapses once a commit on `main` merges every counted ID, or once the branch no longer exists (`git rev-parse --verify --quiet refs/heads/<branch>` fails). Merged IDs compare with declared IDs ignoring case, the trailing letter kept (`config-b3b` equals `CONFIG-B3b`, never `CONFIG-B3`). Every git call runs `git -C <folder>` on the folder whose repository is meant, windowless, with a timeout (30 s). In the guard it goes through `run_git`. A git failure or a timeout lapses nothing.

R6. **The squash-subject reader.** In `squash_merged_ids(folder, id_pattern)`, try the `Merge pull request ... from x/<branch>` / `Merge branch '<branch>'` form before the subject form. Under the grammar's pattern, the subject form takes only leading tokens that hold a hyphen and a digit, so `Merge` and `Plan` are never IDs. The Merge form's branch ID is kept only when it matches `id_pattern` (case-insensitively). Under `plan-check.py`'s own pattern the reader therefore returns exactly what `plan-check.py`'s `merged_ids` returns today. Add a test that runs the reader with `TASK-\d{3,}[a-z]?` on a fixture repository and compares it with `plan-check.py`'s `merged_ids` on the same repository.

R7. **The launcher's round.** The launcher's round is the larger of the name's `<N>` and one plus the distinct completed brief names (ID and `<N>`, exit 0) of that ID on the branch, read from the launcher's own log only. Do not add the guard's rounds into it. Both records are read together for the branch rule only (R3).

R8. **The class-line repeat rule.** A brief's class line is refused when its text equals a text already recorded for the ID by a run of a *different* brief name, or of the same name with different bytes, whatever that run's exit. A relaunch of the same brief name with identical bytes is always allowed, whatever the earlier run's exit, and adds no round. In the guard: a lift is recorded on the round it lifted (`lift` set to `"class"` or `"owner"`, and `lift_line` set to the line's text). A new round is refused while `run/review/SCOPE-<ID>.md` holds a text already recorded on an earlier round. A re-snapshot of an already-lifted round reuses its recorded lift and needs no new line.

R9. **The owner's line's text.** `review_owner_lifts` returns, per ID, the rounds and the matched line's text. The launcher and the guard both record that text, never a text they build themselves. The owner's line lifts the branch rule for its ID as well as the ceiling. Its form needs `<rounds>` above 3, and that is accepted: the owner states a number.

R10. **The guard's round arithmetic.** Let `current` be the highest round in `rounds-<ID>.json`. `snapshot <ID>-r<N>` (no `-r<N>` reads as round 1) is accepted only for `N == current` (a re-snapshot) or `N == current + 1` (a new round). Every other `N` is refused with the count. A re-snapshot of `current` is allowed while that round has no reply, or while the tree hash equals the round's. Otherwise it is refused with `round <N> is reviewed: write <ID>-r<N+1>`. The ceiling tests `N` itself: a new round `N` above `REVIEW_ROUNDS` needs a lift, while a re-snapshot reuses the round's recorded lift.

R11. **A reply.** A reply is a Review B run with exit 0, read from `run/review/REVIEW-<name>.err` and recorded only when that file's launch time is at or after the round's snapshot time. `verify` writes `reply: 0` on the round's entry when it reads such a reply, and otherwise leaves the entry as it was. It never clears or overwrites a recorded reply, and never creates a rounds file that is missing. A `verify` that ends GATE-INTEGRITY records no reply: a flagged review spends no round.

R12. **The tree hash.** The record's `tree` is `git rev-parse HEAD^{tree}`, not the commit hash. A records-only re-commit that leaves the tree unchanged keeps it equal. The snapshot file gains a `round` field (the round `N`), so a rounds file deleted beside it is refused (clause (c)).

R13. **Tamper evidence for the rounds record.** This is the supervisor's decision: the record is the ceiling's whole memory, and `.git/bridge/` is within a reviewer's reach. Each time it writes `rounds-<ID>.json`, the guard keeps a copy of the record's sha256 in the same hash folder as the snapshot's (`BRIDGE_REVIEW_HASHES`, else `~/.cursor-bridge/review-hashes/`), named by the ID. Every read compares the file's hash with that copy. A mismatch, or a hash copy present beside a missing rounds file, refuses with exit 125 (`review-guard: refused - rounds record changed outside the guard: <ID>`). A missing copy beside a present file is seeded once (the release's first run). The write is a `tempfile.mkstemp` in the same folder, then `os.replace`, the temporary file removed on failure.

R14. **Seeding** is built exactly as clause (c) says, case by case (Missing, item 1 below).

R15. **`main`, a detached HEAD and a folder outside git.** The loop builds and reviews on a branch.
- The launcher refuses a builder launch (a `cursor-agent` launch that is not `--kind review`) from `main`, from a detached HEAD (`--abbrev-ref` printing `HEAD`) or from a folder outside git, naming the rule (`bridge-run: refused - brief rule: builds run on a branch, not <main|a detached HEAD|a folder outside git>`). `--kind test` and `--kind driver` launches start anywhere.
- The guard refuses a counted `snapshot` on `main`, on a detached HEAD or outside git with exit 125 and a message naming the rule (`review-guard: refused - branch rule: reviews run on a branch, not <...>`). A `DESIGN-` name is exempt.
- `main` is never claimed and never counted by the branch rule.

R16. **The permission guard** (clause (b2)).
- A `cursor-agent` head (bare, behind a wrapper shell, `eval`, a chain or `find -exec`, as `check()` recurses today) is refused whenever any of its arguments names `handoff` or `run/review` as a path segment, with either separator. Match `(?:^|[^A-Za-z0-9_])handoff[/\\]` and `(?:^|[^A-Za-z0-9_])run[/\\]+review[/\\]`, case-insensitively. That covers `./handoff/`, `.\handoff\`, `E:\repo\handoff\`, `docs/../handoff/`, `(handoff/`, `@handoff/` and quoted forms.
- Remove the probe exception and the launcher exemption (`_inside_bridge_run_cursor_agent`). A probe names no such path and is allowed by that alone: `cursor-agent --version` and `cursor-agent -p hi` stay allowed, with a test each. `check()` never reaches the `cursor-agent` inside a `python ... bridge-run.py ... -- cursor-agent` command, whose head is `python`, so the launcher form stays allowed; keep the tests at :141 and :182 that show it.
- The reason names the launcher (`python ~/.claude/cursor-bridge/bridge-run.py`).

R17. **Malformed input never crashes.**
- Read `docs/RUN_PARAMETERS.md`, the brief, the SCOPE file, `docs/BUILD_PLAN.md`, `runs.jsonl` and the rounds files as bytes, decoded with `errors="replace"`, or catch `ValueError` beside `OSError`.
- Check every field's type before use: `branch` and `brief` a str, `round` and `exit` an int (not a bool), `merge_ids` a list of str, `rounds` a list of dicts with an int `round`.
- A launcher line that fails a check is skipped. A rounds file that fails one refuses with exit 125, a named message and no traceback.
- Add tests for each shape Review A probed: a non-UTF-8 byte in RUN_PARAMETERS.md and in a runs.jsonl line; `branch` as a list; `merge_ids: 5`; `round: [1]`; `round: "2"`; `rounds` as a dict, a string or a list of non-dicts; mixed-type rounds.

R18. **One copy, ASCII.**
- `bridge_env.py` is ASCII-only: write the dashes as `\u2014\u2013` escapes, as `plan-check.py`'s `TRAIL_RX` does.
- The design finder's normalisation (`DESIGN_PATH_NORM`, `DESIGN_TOKEN_RE`, `DESIGN_TRIM_BEFORE_SEP`) moves into `bridge_env.py`, and `bridge-run.py`'s design ceiling and the brief finder both use that one copy.
- The ID pattern is one constant in `bridge_env.py`, from which every regex that needs it is built: the grammar, `REVIEW_LIFT_RE`, `MERGE_UNIT_RE` and `grammar_id_rx`.
- `review-guard.py` uses `bridge_env`'s branch normaliser, not a copy of its own.
- Remove `effective_launcher_round` if it is a one-line wrapper.

R19. **Exact matching.**
- `parse_review_name` uses `fullmatch` (a trailing newline is refused).
- `MERGE_UNIT_RE` is case-sensitive, and every ID on the line must pass `parse_review_name` as a bare ID.
- The class line's class is matched exactly, in lower case as written in the five (`Behaviour` and `SECURITY` are refused).
- The class-line reader returns the first well-formed `Blocking class:` line, skipping malformed ones.
- `DESIGN-` is matched case-sensitively in the guard (`design-x` is read by the grammar and refused).

R20. **Messages.** Every new refusal line is passed through `.encode("ascii", "backslashreplace").decode("ascii")`, as `design_refusal` does. The brief rule's pointer names `workflow/phases/delegation-loop.md, "3. Delegate to Cursor"`. The ceiling's message names the brief, the ID, the branch, the round, the ceiling, and the two lifts by their forms (`Blocking class: <class> - <finding>` in the brief, `Review rounds above the ceiling: <ID> <rounds> (<their words>, <date>)` in docs/RUN_PARAMETERS.md).

R21. **The run log's extra fields** `brief_name`, `merge_ids` and `lift_line` are accepted. Keep them, and add nothing else to the line.

R22. **The verified marks of earlier rounds.** `snapshot <ID>-r<N>` removes `verified-<ID>.json` and every `verified-<ID>-r<k>.json` of that ID, as today's snapshot removes the older mark, so one verified mark of an ID is live at a time. `tests/test_review_guard.py`'s `test_premerge_refuses_a_snapshot_without_its_verified_mark` keeps its point:
- revert the extra commit you added (`a.py` changed, "after review") unless the test needs it;
- after the `TASK-001-r2` snapshot, assert that `premerge TASK-001` is refused and that `verified-TASK-001.json` is gone.

R23. **Test-setup drift.** In `tests/test_review_guard.py`, revert the `REVIEW-TASK-002.diff` and `REVIEW-TASK-003.diff` input files and their commits (round 1, :113-116, :173-186), unless the snapshot now requires a review input, which it must not. Name the second ID's branch `task-002`.

R24. **Timeouts.** Every new git call (launcher and `bridge_env`) carries `timeout=30` beside `creationflags=NO_WINDOW`. A timeout counts as the git failure of R5.

## Missing (implement and test)
1. **Seeding (clause (c))**, in `review-guard.py`, on reading a missing `rounds-<ID>.json`:
   - It is refused (exit 125) when any present `review-<ID>.json` or `review-<ID>-r<N>.json` carries a `round` field.
   - Otherwise it is seeded from the larger of two readings:
     - the letter snapshots `review-<ID>.json`, `review-<ID>a.json`, `review-<ID>b.json` and so on, with the same recorded branch (`refs/heads/` stripped before comparing), letters in order. A trailing letter is a sub-round only where the longer token (`TASK-010b`) has no brief `handoff/TASK-010b.md` and the shorter ID (`TASK-010`) has one;
     - the greatest `<N>` of the tracked `handoff/<ID>-r<N>[a-z]?-report.md` files (`git ls-files`).
   - That count of rounds is written, one entry each in order, marked `seeded: true`, with `reply: 0` (each seeded round was reviewed).
   - Tests:
     - four letter snapshots, their branch stored as `refs/heads/<branch>`, seed four rounds, and the next `<N>` accepted is 5 (and needs a lift);
     - `TASK-010`'s letters `a` and `b` beside a `TASK-010c` that has its own brief seed `TASK-010` only, and `TASK-010c` is counted under its own ID;
     - five report files outrank two snapshots;
     - a snapshot carrying `round` with the rounds file deleted refuses.
2. **Every case of clause (e)** that round 1 left untested. Review A's case-by-case reading, which this list follows, found these. Each is a test through the program's command line (a subprocess of `bridge-run.py` or `review-guard.py`), never only a call into the loaded module.
   - **Launcher, accepted and refused names.** Run the launcher on `TASK-001`, `TASK-010c`, `CONFIG-B3b`, `HOTFIX-001`, `B3-CLOSE` and `TASK-001-r2` (accepted). Run it on `TASK-001-r0`, `TASK-001-r05`, `TASK-001-R2`, `TASK 001` and `TASK-001-r2\n` (refused, exit 125, nothing logged).
   - **Two briefs named.** A launch naming two briefs is refused.
   - **The `--workspace` folder.** A brief present only in the `--workspace` folder is read from there, and one present only in the launch folder is not.
   - **`BRIDGE_RUN_ALLOW_ANY=1`.** It refuses a bare and a path-qualified `cursor-agent` without a brief.
   - **Rounds 1 to 4.** Rounds 1, 2 and 3 run with no line. Round 4 is refused without a class line (exit 125, the message's names asserted) and runs with one.
   - **The five classes.** Each of the five classes is accepted. A sixth word, a capitalised class and an empty finding are refused.
   - **The owner's line.** It allows up to its `<rounds>` and refuses `<rounds>+1`. A second line for the same ID is ignored.
   - **Revised in place and relaunches.** A revised brief is refused after a run with exit 0 and relaunched after exit 1 and after exit 124. A relaunch with identical bytes runs and leaves the next numbered brief's round unchanged.
   - **Another ID on a counted branch.** It is refused without a lift, and allowed once the counted ID is merged on `main` (a fixture repository whose `main` holds a squash subject naming it) and once the branch is deleted.
   - **Merge units.** A two-ID merge unit's briefs are allowed. A third ID is refused without the owner's line, refused under a class line, and allowed under the owner's line naming it, the declared set unchanged. A later brief naming more IDs is refused, with that message. A unit naming an ID that is no increment heading is refused. A BUG brief with no unit line in a folder without BUILD_PLAN.md is allowed (R2).
   - **The guard's record and the class-line repeat.** A guard snapshot of one ID refuses a launch of another ID on that branch. A repeated class-line text is refused in a different brief, and the identical-bytes relaunch of the lifted brief is allowed after exit 0 and after exit 1 (R8).
   - **Review launches.** A `--kind review` launch naming a brief is refused. One naming `handoff/RESOLUTION-x.md` or `handoff/TASK-001-r2-report.md` is allowed. One on the roster's builder model is refused.
   - **Two worktrees.** Two launches from one folder naming two worktrees on two branches are each counted as round 1.
   - **`main`, detached and outside git.** A builder launch from `main`, from a detached HEAD and from a folder outside git is refused (R15), while a `--kind test` and a `--kind driver` launch start on `main`: assert exit 0 and the `started` line.
   - **The log.** The runs.jsonl fields are checked: `brief`, `round`, `brief_sha256` equal to the sha256 of the brief's bytes, `lift` null on an unlifted run, `"class"` or `"owner"` with `lift_line` on a lifted one, `branch`, and the prompt's text nowhere in the line.
   - **Refusals start nothing.** Every refusal test asserts all three: the stand-in's marker absent, no `bridge-run: started` line, and no runs.jsonl line written.
   - **The constants.** `bridge_env.REVIEW_ROUNDS == 3`, and `BLOCKING_CLASSES` equals exactly the five names.
   - **Guard re-snapshots.**
     - A re-snapshot of an unreviewed round with a changed tree is allowed.
     - The sequence reply, re-snapshot on the same tree (allowed), then a snapshot of a changed tree under the same `<N>` is refused at its last step, so the reply survives the re-snapshot.
     - A re-snapshot of a reviewed round 3 on the same tree is allowed (R10).
     - `<N>` off the count, both below `current` and above `current + 1`, is refused with the count in the message.
   - **Guard lifts.**
     - A fourth round with the class line is allowed, and the lift recorded with `lift_line`.
     - The same line refuses a fifth round, and the next round's line, replacing it, allows it.
     - The owner's line lifts to its `<rounds>`.
   - **Guard names.** `STAGE-B5-r2` is counted under `STAGE-B5`.
   - **Guard branch rule.**
     - A snapshot under another ID on a counted branch is refused, and allowed once the counted ID is merged on `main`.
     - A merge unit's two IDs are allowed, with `SCOPE-TASK-010.md` present and holding no merge line, and `TASK-015` allowed on that branch with no launcher line (R4).
     - A third ID is refused under a class line and allowed under the owner's line.
     - A launcher line of one ID refuses a snapshot of another.
     - A records subject (`B3-CLOSE`, no brief) is allowed and counted under its own ID.
   - **Guard, `DESIGN-` and refused snapshots.**
     - A `DESIGN-` name writes no rounds file.
     - A refused snapshot writes no rounds file, no `review-<name>.json` and no hash copy, shown beside the same repository writing all three on an accepted snapshot.
   - **Guard records and replies.**
     - The record survives `verify` and a later `verify` with a non-zero exit (R11), and is written atomically.
     - Changing the rounds file by hand refuses (R13).
     - A reply whose `.err` launch time precedes the snapshot is not recorded.
     - A GATE-INTEGRITY verify records no reply.
   - **Guard full names.** `verify` and `premerge` work under `TASK-001-r2` and refuse an unreadable name with 125.
   - **Guard `main`.** A snapshot on `main` is refused naming the rule (R15).
   - **Permission guard.** The refused forms of R16 each have a test, among them `cursor-agent -p hi --force "Read handoff/TASK-001.md"`, `cursor-agent --version "Read handoff/TASK-001.md"`, `cursor-agent -p handoff/TASK-001.md` and the chained form after a launcher command. The probes `cursor-agent --version` and `cursor-agent -p hi` are allowed.
   - **The design pointer.** `tests/test_bridge_run_design_ceiling.py` asserts the full phrase `design.md, "The launcher holds the ceiling"`.
3. **Docstrings (requirement 14).** The module docstrings of `bridge-run.py`, `review-guard.py`, `permission-guard.py` and `bridge_env.py` describe the new rules, refusals and exit codes, in ASCII. Then regenerate the command reference.

## Test defects to fix
- **Stand-ins.** Every test that launches a `cursor-agent` head puts a stand-in on `PATH` (as `tests/test_bug029_agent_name.py:68-103` does) and asserts its marker's absence or presence. Today `test_r042_allow_any_does_not_exempt_cursor_agent` and `test_r042_review_on_builder_model_refused` have none.
- **`tests/test_review_guard_ceiling.py:97`.** `... or True` asserts nothing; replace it as Missing item 2 says.
- **`tests/test_bridge_run_review_ceiling.py:243`.** Assert rc 0 and `started` (Missing item 2, `main`).
- **The environment.** Build each test's environment inside the helper that launches the subprocess (after the autouse fixture has set `HOME` and `USERPROFILE`), never at import. Do this in `tests/test_review_guard_ceiling.py`, and in `tests/test_review_guard.py` where you touch it.
- **Through the command line.** The round-4, owner and revised-in-place cases run through the launcher's command line. A direct call may stay beside them.

## Acceptance criteria
- [ ] Every item of "Rulings", "Missing" and "Test defects to fix" is implemented, and covered by a passing test where it can be tested.
- [ ] Every acceptance criterion of `handoff/TASK-032.md` holds.
- [ ] All seventeen mutations below were applied by hand, one at a time, and each was caught by a test in the two new files or in `tests/test_permission_guard.py`, the catching test named in your report. A mutation that survives gets a test that catches it before you finish.
- [ ] `bridge_env.py`, `bridge-run.py`, `review-guard.py` and `permission-guard.py` are ASCII-only (`python -c "open(p,'rb').read().decode('ascii')"` on each).

## Constraints
Every constraint of `handoff/TASK-032.md` holds unchanged, among them:
- no real `cursor-agent` or model;
- no real home;
- windowless launches;
- no git command of yours in this Workspace beyond `status`, `diff` and `log`;
- the owner's number, 3;
- no new dependency;
- no hard line wraps in Markdown.

Run these verification commands, from the Workspace root:
- `python -m pytest tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py -q -p no:cacheprovider`
- `python -m pytest tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_permission_guard.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_bug029_agent_name.py tests/test_bridge_run_slot.py tests/test_bridge_run_driver.py tests/test_hotfix25a_roster_launcher.py -q -p no:cacheprovider`. The last four are outside your Scope: run them, never edit them, and name any failure in your report.
- `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py bridge/cursor-bridge/permission-guard.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py`
- `python tools/dump-cli.py`, then `python tools/dump-cli.py --check`
- `python tools/make-manifest.py`, last, after every program edit
- `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` (must end OK)

**Mutation check, by hand, in your own run.** Apply each mutation, run the two new test files and `tests/test_permission_guard.py`, and restore the code before the next. No script of this lands in the diff. The mutations:
1. `REVIEW_ROUNDS` 3 to 4.
2. The grammar accepting a leading zero in `<N>`.
3. The launcher's round as `<N>` alone.
4. "Completed" as any exit instead of exit 0.
5. The class-line repeat check removed, first in the launcher, then in the guard (two runs).
6. The owner's line read last-wins.
7. The branch rule reading only its own program's record.
8. The lapse never applying.
9. The lapse applying on any commit on `main`.
10. The permission guard matching only `/`.
11. The guard re-snapshotting a reviewed round on a changed tree.
12. Seeding by counting snapshot files instead of letters and report `<N>`.
13. `BRIDGE_RUN_ALLOW_ANY=1` exempting `cursor-agent`.
14. The `main` refusal applied to `--kind test`.
15. The `--workspace` folder ignored when reading the brief.
16. A reply counted at any exit (R11).
17. The guard accepting any `<N>` already in the record (R10).

## Done
Your report is `handoff/TASK-032-r2-report.md`. Write it as you go, so nothing is lost if the run ends early. When you finish, it holds:
- the files you changed;
- a one-paragraph summary;
- the public names in `bridge_env.py`;
- where each launcher refusal sits in `main()`;
- a table of every case of clause (e) and every "Missing" and "Rulings" item, each with the test that covers it;
- the seventeen mutations with the test that caught each;
- the output of each verification command (pass counts);
- every failure in the out-of-scope test files named above, with its lines;
- a section headed exactly `Assumed, not verified`: one item per line, in the form what you assumed · why · what would confirm it, or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
