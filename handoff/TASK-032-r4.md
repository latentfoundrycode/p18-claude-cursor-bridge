# TASK-032-r4: The code-review ceiling held by the launcher and the guard — round 4, blocking-class fixes only

Blocking class: behaviour - an identical-bytes relaunch of a brief name whose first logged run had other bytes is counted as a new round, and its class line as already used (Review A, round 3, N1)

## Objective
Round 3 (f735a24) passed every supervisor test of rounds 1 to 3. This round is past the three-round ceiling (R-042), and fixes exactly two defects, each of a blocking class. Change nothing else. Every other finding of round 3's reviews is recorded by the supervisor in docs/HARDENING.md and is not yours to fix in this round.

1. **Behaviour against the brief (the class line above).** `prior_brief_run` (bridge/cursor-bridge/bridge-run.py:546-556) returns the *first* logged run of the brief name. Its two callers then compare the current bytes with that run only:
   - the round, at :683-684;
   - the class-line exemption, at :699.

   So the following sequence ends refused at the ceiling: a name ran with bytes v1 and exited 1, was revised to v2 (allowed after a failed exit), v2 ran (exit 0, no work done, KP-038), and then v2 is relaunched with identical bytes. The same sequence refuses a lifted round-4 brief as "class line already used".

   **Fix:** look for a logged run of the same brief name with the *same* `brief_sha256`, at any exit, and use it in both places. When one exists, the launch is an identical-bytes relaunch: it adds no round, and its own class line is not "already used". The revised-in-place rule is unchanged: a launch is refused when the name has a completed run (exit 0) whose bytes differ from the current bytes and no run with the current bytes.

2. **A defeated safety mechanism (the guard's count).** Today a round is spent only when `verify` records its reply (review-guard.py:904-922). If `verify` is never run, `snapshot` of the same `<N>` on a changed tree is accepted however often a Review B has replied in the meantime.

   **Fix, in `review-guard.py`:**
   - In the re-snapshot check, take a round (`N == current`) with no recorded reply. If `run/review/REVIEW-<that round's recorded name>.err` shows a launch at or after the round's recorded `time` and the exit 0 (read with `launch_info`), treat the round as having a reply: refuse a changed tree with today's `round <N> is reviewed: write <ID>-r<N+1>`, and accept the same tree as today. The refusal writes nothing, as every refusal.
   - The exception: a launch that a `verify` ending GATE-INTEGRITY read. That review is void and spends no round (R11). So that the check can tell it apart, `verify` writes `flagged_launch: <that launch time>` on the round's entry when it ends GATE-INTEGRITY with such a launch. The re-snapshot check ignores a launch whose time equals the recorded `flagged_launch`.

## Satisfies
R-042 (docs/REQUIREMENTS.md, line 48). `handoff/TASK-032.md`, `-r2.md` and `-r3.md` stay normative, in the precedence r4 > r3 > r2 > the first.

## Scope
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-032-r4-report.md

Do not modify anything else.

**Read-only, the supervisor's:** `tests/test_task032_supervisor_r4.py`, `tests/test_task032_supervisor_launcher.py` and `tests/test_task032_supervisor_guard.py`. Read them, run them, never edit them. On round 3's code, three tests of `tests/test_task032_supervisor_r4.py` fail, for the two defects above, and one passes.

## Out of scope
Everything else. That includes every other finding of the round-3 reviews, the docstrings, and every test file outside the read-only list (no test file is yours to edit in this round).

## Acceptance criteria
- [ ] `python -m pytest tests/test_task032_supervisor_r4.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider` passes whole: 4 + 88 + 143 tests.
- [ ] Those three files are unchanged: `git diff --quiet b1ad478 -- tests/test_task032_supervisor_r4.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py`.
- [ ] `python -m pytest tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_permission_guard.py tests/test_hotfix25a_guard_scope_invisible.py -q -p no:cacheprovider` passes.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py` reports 0 FAIL.
- [ ] Then, last: `python tools/make-manifest.py` and `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` (must end OK), and `python tools/dump-cli.py --check` passes.

## Constraints
Every constraint of `handoff/TASK-032.md` holds:
- no real `cursor-agent` or model;
- no real home;
- windowless launches;
- no git command of yours in this Workspace beyond `status`, `diff` and `log`;
- the owner's number, 3;
- no new dependency;
- no hard line wraps in Markdown.

The diff is the minimum that removes the two causes.

**Mutation check, by hand:** apply each mutation, run `tests/test_task032_supervisor_r4.py`, and restore the code before the next. List each with its catching test.
1. Match the first logged run again.
2. Ignore an unverified `.err` reply.
3. Ignore `flagged_launch`.

## Done
Your report is `handoff/TASK-032-r4-report.md`. It holds:
- the files you changed;
- what you changed, with file:line;
- the three mutations with their catching tests;
- every verification command's pass and fail counts;
- `Assumed, not verified`, one item per line, or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
