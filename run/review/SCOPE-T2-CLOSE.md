# SCOPE - T2-CLOSE: the closing records of release T

## What this pull request is
Stage T2's close and release T's project end, on the installed bridge 2026.11.03a: a records pull request and one supervisor test, no builder run, no brief, no shipped program or text under `bridge/`. It takes the same round as any pull request (merge.md: a pull request that changes only records). Its procedure is project-end.md, reflection.md and change-cycle.md item 7, in the installed tree and at `bridge/cursor-bridge/workflow/phases/`.

The increment ends with the status file as at this pull request's merge (Phase: done). `sync-check.py --apply --strict`, `completion-check.py --mode done` and `diagram-check.py --mode done` are run again after the merge; the status file says the strict check comes after it. The Documents folder (Issues, Feedback, Project Summary, User Manual) lies outside the repository and is not in the diff.

## Scope: the files expected in the diff
- `tests/test_bug039.py`: one test added, `test_bug039_the_void_lands_on_the_round_flagged_never_on_round_1`, least confident item 3's. Supervisor-written.
- `docs/HARDENING.md`: TASK-045's closing verdict; stage T2's demonstration; project end of release T; earlier least-confident items read again; least confident of the release.
- `docs/PROJECT_STATUS.md`: as at the merge of this pull request, predicted #134 (newest pull request 133, no issues).
- `docs/archive/STATUS_HISTORY.md`: three lines moved word for word.
- `docs/INVENTORY.md`: `Updated:`; the rows of the strip (in force), BUG-039's rule and R-050's grading (each held by hand until the install, now met).
- `docs/BUILD_PLAN.md`: stage T2's `Demonstration:` line gains a dated note of its departure.
- `project.json`: `state`.
- `run/review/`: this file, the round's diff and its assumptions file, removed before the merge.

## Out of scope
Everything under `bridge/`. Any requirement's row. Any change of behaviour.

## The threat model
`docs/INVENTORY.md`, Decisions, holds the review guard's threat model (the row beginning "The review guard's threat model") and the strip's limits (the row beginning "The strip reaches only what goes through the launcher"). The new test exercises the guard inside that model. Nothing else in this diff has a threat model of its own: it is records.

## The test and its mutants
- `tests/test_bug039.py::test_bug039_the_void_lands_on_the_round_flagged_never_on_round_1` enforces R-042 and D-003's `reply_arrived` to `flagged_gate_integrity` at a later round: a flag on round 2 voids round 2's launch, round 1's replied entry stays as it stood, and the same launch verified again gets no mark and no reply. It passes on the code as it stands, the code being right, so there is no checkpoint run; its mutants are its proof.
- Mutants: `run/supervisor/T2CLOSE-mutants.json`, m01 (`review-guard.py`, the void landing on round 1) and m02 (the void read from round 1). `run/agent/T2CLOSE-mutation.out`: "counts: run=2 cached=0 killed=2 survived=0 not applied=0 error=0 expected survive=0".
- The own file: `run/agent/T2CLOSE-tests.out`, "61 passed in 95.39s (0:01:35)". The suite on this head, stripped, with the pull request's variables: `run/agent/T2CLOSE-suite.out`, "3561 passed, 40 skipped in 1708.57s (0:28:28)".

## The demonstration's evidence, for the claims in HARDENING
`run/agent/demo-t2.out` ("RESULT: 9 of 9 passed"), `run/agent/demo-t2-strip.out` ("13 passed in 0.98s"), `run/supervisor/demo_t2.py`; the plan's line at `docs/BUILD_PLAN.md`, stage T2's `Demonstration:`.

## Review A
Review A read db5ccb9: REJECT, one blocking finding (project.json's stage changing the conformance check's NOTE count, against what the records quote), three Should fix, three Consider, all taken in 730f9f6 and c120148. Its confirming read of `git diff db5ccb9 c120148`: APPROVE, nothing blocking.

## A known open item, stated in the diff
R-056 reads "with the TDP paused once at a merge boundary and calibrated". The TDP has not calibrated: only the owner's `/calibrate-bridge` in its own session can do that. HARDENING and the status file say so, and the closing report puts it beside the "Project complete" line. The owner's deferral covers reAngle and the video factory, not the TDP.
