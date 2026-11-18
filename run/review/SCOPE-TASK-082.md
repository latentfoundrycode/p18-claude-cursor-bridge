# SCOPE — TASK-082, round 1

TASK-082 is a supervisor-authored text increment: no builder, no brief. Its specification is the plan entry, quoted below from docs/BUILD_PLAN.md (### TASK-082). The increment ends at the texts and records listed in its Scope; the programs those texts name merged earlier in stage P2 (TASK-059, TASK-062, TASK-064, TASK-065, TASK-067, TASK-083, TASK-084) and are not under review here.

## Scope (quoted)

bridge/commands/supervisor.md; bridge/cursor-bridge/workflow/phases/delegation-loop/merge.md; bridge/cursor-bridge/workflow/phases/delegation-loop.md; bridge/cursor-bridge/workflow/phases/reflection.md; bridge/agents/secret-sentinel.md; bridge/agents/spec-packager.md; bridge/cursor-bridge/Merge-Verification-Policy.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; docs/TRACE_MOVES.md; tests/test_allowlist.py; tests/test_release_t_merge.py; tests/test_a5_followups.py; tests/test_bug043.py

The last three tests were added at the increment's checkpoint (2026-11-19, the supervisor): each pins word for word a sentence this increment retires, and each pin is rewritten to the new sentence (the plan's Scope notes say so; prose and header agree).

## Done when (quoted, abridged to its items)

Each sentence of the Scope notes stands once, in the file named; no instruction still tells the supervisor to confirm the checks by a hand-typed `gh pr view` after the watch, to scan the commits by a hand-run `git log -p`, or to arm a merge before the watch; `spec-packager.md` says that a merge unit is two or more increments and that a brief of one increment has no `Merge unit:` line and `merge_unit: null`; the digest's step 8 names `ready` between the watch and the merge and is no longer than it was; every instructed command passes tests/test_allowlist.py; `trace-check.py --moves` OK, each retired or reworded passage with its entry in docs/TRACE_MOVES.md, and the pinned mode green; the rulebook's word count after is at most the count before less 100; `workflow-check.py` exits 0; MANIFEST regenerated; rows R-078, R-081, R-083, R-085, R-087 and R-105 read built in the records commit.

## Out of scope

Known-Pitfalls.md (KP-051's Correction, lead 1), run-parameters.md's `supervisor` gloss (lead 4) and every program: docs/HARDENING.md, TASK-082, records them as leads for TASK-078.

## The threat model

docs/INVENTORY.md, Decisions: "The bridge's threat model as a whole" (outside input is what the builder and reviewers write, what a program reads from GitHub or another service, and a project's record as an agent left it; a deliberate reach by a process running as the owner's account is outside it, KP-032), narrowed for the permission guard by "The permission guard's threat model" (R-082) and for GitHub's replies by "GitHub's replies are outside input to the rule's reader" (R-083). This diff changes instruction text, four test pins and records; it changes no program.

## The tests the supervisor wrote or changed

- tests/test_allowlist.py: the ordinary-command example takes the direct merge form (the armed form retired); every instructed command, `review-guard.py ready <n>` and `push-scan.py origin/<the base>` among them, is collected and checked against the allow rules and the guard by the existing parametrized tests.
- tests/test_release_t_merge.py: P5 pins the sentinel's new push-scan sentence and step 8's push-scan sentence; P4 pins step 8's "arm no merge" sentence and that step 8 holds no `--auto`.
- tests/test_a5_followups.py: the watch test pins "A watch's return is never the proof that CI passed", `ready`'s command and KP-051's pointer, and that step 8 holds no `statusCheckRollup`.
- tests/test_bug043.py: step 4's sentence pinned with the GIT-CONFIG sentence in place of "the launcher's comparison ... is a program item".

No mutants file and no mutation driver: the increment changes no program; its tests are pins of text.

## Expected bookkeeping and record files in the diff

docs/HARDENING.md, docs/PROJECT_STATUS.md, docs/BUILD_PLAN.md (the Scope widened), docs/REQUIREMENTS.md (six rows built), docs/TRACE_MOVES.md (13 entries), bridge/cursor-bridge/MANIFEST.json (regenerated), and run/review/.
