# SCOPE: TASK-087a (Review B, round 2)

Increment: TASK-087a, "The rule budget: the rulebook's and the step file's caps raised, ten passages retired, three sentences corrected (R-109)". Supervisor-written instruction text: no builder, no brief; the plan entry is the specification (docs/BUILD_PLAN.md, TASK-087a), with docs/DESIGN.md, Change: the improvements release, the paragraph "The rule budget." under Data model and development data, its bullets and the paragraph after them on the three corrected sentences. The diff is the branch against origin/main at 0cb7846 (TASK-087b merged), the merged main's commits and the review files left out: run/review/REVIEW-TASK-087a-r2.diff. Since round 1, one commit answers its one finding: HARDENING's proofs line quotes the trace check's count with TASK-087b merged in (0 dropped, 119 excused) beside the fix commit's 118: run/review/DELTA-TASK-087a-r2.diff. Where the increment ends: R-109's rule budget. R-109 stays planned until TASK-118 (the stamp lowers the caps); the release's new text comes in later increments.

## The owner's rule (2026-11-24, intake, quoted in the accept commit)
Retire only what the latest release made redundant or deprecated, with care; never cut useful guidance to make room; then add the new text and raise the limit.

## Scope (the plan's)
- tests/test_release_s_budgets.py: RULEBOOK_WORDS 158,000 and STEP_FILE_WORDS 8,500 with their comments, nothing else.
- bridge/commands/supervisor.md: rule 39's parenthesis retired; the three corrected sentences (the status file, the bridge version on start, the boundary detector in the boundary paragraph and rule 22).
- bridge/cursor-bridge/Known-Pitfalls.md: KP-051's body to a pointer; the superseded fragments of KP-069, KP-074 and KP-083; no new entry.
- bridge/cursor-bridge/workflow/phases/delegation-loop.md: four retirements (git commands one a line, the --model hint, the healthy mark at a limit, the home-variable clause) and the boundary correction at step 4.
- bridge/cursor-bridge/workflow/phases/reflection.md: the lessons-file sentence.
- bridge/cursor-bridge/workflow/trace-exceptions.md (two entries for the baseline check), docs/TRACE_MOVES.md (18 entries, each pasted from the move mode's failure line), bridge/cursor-bridge/MANIFEST.json (regenerated).
- Outside the plan's Scope line, named by its Done when: tests/test_bug043.py, whose one assertion held retirement 4 whole, reduced to what a program reads.
- The records commit: docs/HARDENING.md, docs/REQUIREMENTS.md (R-066's clause), docs/PROJECT_STATUS.md (as at this merge, next TASK-087c).

## Each retirement and its program (the accept commit's list, read by Review A against each)
1. Git commands one a line: permission-guard.py chain_reason refuses a chain with a state-changing git or gh command, naming rule 8.
2. The --model hint: the constant command carries the resolved roster's model; roster-check.py fails a differing or missing --model.
3. The healthy mark for a run that ended at its limit: bridge-run.py mark_healthy refuses it; merge.md says so.
4. The home-variable clause: bridge-run.py key_file_home_refusal (R-080).
5. and 6. A lessons file and release A5's worktree: things long gone.
7. KP-051's body: the launcher's watch waits for the pushed head; review-guard.py ready proves CI on it. The sentence "handed over only after its checks ran green on the pushed head" kept.
8. to 10. KP-069's, KP-074's and KP-083's superseded fragments.

## The threat model
Instruction text only: no program changes. The relevant risk is a retirement that removes a safety instruction no program holds, or a correction that states something no program holds, so that a supervisor relies on a check it does not have.

## Reviews so far
Review A round 1: REJECT on one records finding (the accept commit's after count, 149,701, taken before trace-exceptions' entries; 149,720 at the accept commit) and two should-fix (the corrected status sentence claimed a CI test only this repository has; the move entries fall in four files, not five), answered by one commit; round 2 APPROVE. The counts: 149,858 before; 149,716 after the fix; 149,754 with TASK-087b merged in.

## Proofs
trace-check.py RESULT: OK (0 dropped, 118 excused); trace-check.py --moves RESULT: OK (18 excused); the 49 test files that read the edited texts: 1786 passed, 31 skipped.

## Round
Review B's second round (the guard's count 1). Round 1: REJECT on one records finding (the trace check's excused count in HARDENING), answered by the delta commit; it confirmed the ten retirements, the three corrections, the word counts and the caps against the programs.
