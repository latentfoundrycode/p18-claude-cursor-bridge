# SCOPE - PLAN-windowless (pull request #57)

## What this pull request is

A records-only plan revision of release B (subject `windowless`): the owner's fix for the window flood of 2026-10-19/20 (ISS-011), placed as four increments in stage B5 before the acceptance increment TASK-025. No program, no test and no governance text under `bridge/` changes; the increments it plans build those later.

## Scope (the files the diff may touch)

- `docs/REQUIREMENTS.md` — the register's revision note; rows R-039, R-040, R-041, each with the owner's words as its source.
- `docs/BUILD_PLAN.md` — the plan's revision note; stage B5's `Demonstration:` line; TASK-028, TASK-029, TASK-031, TASK-030 (new); TASK-025's `Depends on` (gains TASK-030 and TASK-031); TASK-027's `Done when` (the windowless default among the changelog's items; the trial's floor criterion).
- `docs/INVENTORY.md` — Decisions rows: the fix's placement (the owner's words of 2026-10-20), the post-B release where no window can exist (WSL), and what "rate limit" means (the owner's answer at the gate); the Deferred row for the Node runners' windowless default (the owner's dated deferral at the gate).
- `docs/DESIGN_CRITIQUE.md` — the subject `windowless` block: what is criticised, the accepted findings with reasons, rounds 1 to 4 and the confirming read (round 5) per critic, the resolution (none due) and the owner's gate; the ceiling's trailing paragraph re-headed `## Subject: ceiling — after the critique` so the windowless block stands between.
- `docs/PROJECT_STATUS.md` — the position as at this pull request's merge (ISS-009's rule, the file's "How this file is written" section).
- `run/review/DESIGN-windowless-1.md` to `-5.md` — the critique's round files, committed with `git add -f` for each round and removed with `git rm` in the commit that records the gate (Merge-Verification-Policy, Review B's design mode); net absent from the diff.

## Out of scope

- The design of the four increments themselves: settled by the two-critic critique and the owner's gate ("1. Approve / 2. (a) / 3. (a)", 2026-10-20). Design for later increments is not this diff's defect.
- Any program, test or governance file: none changes here.

## Tests the supervisor wrote

None: a records change. The records' own tests run in CI (tests/test_release_b_bootstrap.py, among them test_r001_status_names_its_own_merge and test_r001_no_deferred_row_reopens_a_settled_decision, which caught an open-question cell on the Deferred row before this commit; tests/test_text_consistency.py).

## Expected bookkeeping

The status file's rewrite; the DESIGN files' add-and-remove; `docs/ROSTER.resolved.json`'s `resolved_at` stamp (the roster check before the critique's first Review B launch); `run/review/` (these review files).
