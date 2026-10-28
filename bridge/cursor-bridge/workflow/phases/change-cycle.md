## The change cycle — a request on a finished project

### What must survive a compaction

After a compaction or a resume in a change cycle, read these before your next action:

- this module, whole, and the module of the step the change has reached, whole: its intake runs `intake.md`'s procedure, its design revision `design.md`'s, its interface variants `interface.md`'s with the variant files its `Variants:` line names, its plan addendum `planning.md`'s, its run parameters `run-parameters.md`'s, with `docs/RUN_PARAMETERS.md`, which holds the original run's answers, and any new tooling `configuration.md`'s, each scaled to the change; its new stages run `delegation-loop.md` with its sub-files, and their closes `reflection.md` and `project-end.md`, which the session-start hook names with this module while the phase is `changing`;
- `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, whole (rule 41): the `Change cycle:` line names the change, its date and the step it has reached, and `Awaiting user on:` a gate, or an intake question, that waits for the owner; the inventory's Features answer a request already satisfied, and its Decisions name one the change reverses (item 1);
- `docs/REQUIREMENTS.md`, with the failures `completion-check.py --mode done` printed at item 1: each is a gap in the previous delivery, reported to the owner first and planned ahead of the request unless the owner defers it;
- the change's records as far as they are written, whole: its `Change: <name>` section of `docs/DESIGN.md`, its record in `docs/DESIGN_CRITIQUE.md` under the change's subject and under `<the change's name>-plan`, the interface artifacts it amends, and its stages in `docs/BUILD_PLAN.md`;
- while its intake runs, this project's own Issues file, `Documents/<Name> Issues During Development and Their Solutions.md`, whole: it takes the place of the prior-project lessons step.

### The procedure

A project whose status is `Phase: done` and whose owner asks for a change runs the same
phases as the original build, **scaled to the delta**: everything already approved stays
approved, everything the change touches goes through its gate again, and nothing else is
re-presented. Set `Phase: changing` and record the request in `PROJECT_STATUS.md` under
`Change cycle:` with a short name and the date.

Keep the step the change has reached on the `Change cycle:` line, rewritten as each step is reached or its gate passes, so that a resume after a compaction starts where the change stands and asks no approval twice.

1. **Intake of the change** (Phase 1, scaled). The session is on Opus 5.5 from the build:
   your first report leads with *set this session to Fable 5.1 before the design work* (rule
   48), and the design gate's report says *back to Opus 5.5*. Interrogate the request the
   same way as a new project's description — gaps, contradictions, better options — but only about the
   delta: what changes, what explicitly stays, and the **impact on existing behaviour**
   (which current features, screens, data, or commands the change touches, and whether any
   existing behaviour is altered or removed). Read this project's own Issues file in place
   of the prior-project lessons step: the issues already recorded are the ones this change
   must not repeat. **Verify the inherited "done" before anything else:** run `python ~/.claude/cursor-bridge/completion-check.py --mode done` on the product as it stands. Every failure is a gap in the previous delivery — a requirement never built, a stand-in shipped as a feature — and it is reported to the owner first, plainly, as such ("the previous release was marked complete but R-012 Settings tab was never built"), then planned into this cycle ahead of the new request unless the owner defers it. A project with no register gets one built from its requirements document, design, and mockup before the check runs. Read `docs/INVENTORY.md` whole next: a request that
   Features already satisfies is answered by pointing at the feature, not by proposing it;
   a request that reverses a Decision is named as such, with the recorded reason, and goes
   through the gates as a change to that decision. A report of **several defects** is triaged before any of them is diagnosed — the `root-cause-first` skill's step 0: shared cause binned only on evidence, otherwise one at a time. The item ends with a confirmation inside intake, not a gate: `intake.md`'s closing confirmation, its "The gate" step, which this item runs with the rest of `intake.md`'s procedure, is the confirmation a change cycle runs, outside the three gates rule 34 names. Read the change back to the owner — what changes, what stays, which existing behaviour alters — and take their confirmation, named on `Awaiting user on:` while it waits, as any intake question is.
2. **Design revision** (Phase 2, scaled). Append a dated **Change: <name>** section to
   `docs/DESIGN.md` — what changes in the architecture, data model, interfaces, security
   context, or delivery, and why; the unchanged design is referenced, not rewritten. **Revise the diagrams the change touches** the same way they were drafted — specialists, top-down, `python ~/.claude/cursor-bridge/diagram-check.py --mode design` — and select any catalogue kind the change newly needs; a project designed before diagram-based planning gets at least its component diagram (with its element map) and, if it stores data, its entity-relationship diagram at its first change cycle. Run
   the two-critic loop of Phase 2, with its ceiling, on the delta section with the existing design as context (release A3; the subject is the change's name). Gate: present
   it as a decision brief, with the critique's record for the change, and get approval. Patch the Project Summary at this gate.
3. **The interface variants** (Phase 3) **only for the kinds of interface the change touches** — screens, commands, a protocol other software calls, play — each kind by the variant `interface.md` gives it ("The variants", "Which variants a part runs"), or by the replacement of a part whose type workflow replaces the interface phase, and each run only for the screens and states, the commands or the operations the change adds or alters. An artifact already approved is amended, not replaced (for screens, the mockups and the visual system); an artifact the part does not have yet is written for what the change touches; a kind the change does not touch is not re-presented. Gate as in Phase 3, for the variants run; a change that touches no kind of interface runs no variant and holds no interface gate.
4. **Plan addendum** (Phase 4, scaled). Append one or more new **stages** to
   `docs/BUILD_PLAN.md` for the change, with the same increment discipline, and bump the
   **version** in the single version source (a fix → patch; a feature → minor; a change
   that alters or removes existing behaviour → say so plainly in the brief and the
   change log). The Packaging & installer stage is re-run as the last stage when the
   deliverable must be rebuilt (it always must for a shipped version bump). Run
   the two-critic loop, with its ceiling, on the addendum (the subject `<the change's name>-plan`). Gate: present it and get approval.
5. **Run parameters** are kept from the original run; ask only for one that is missing.
   **Configuration** (Phase 5) is skipped unless the change needs new tooling, in which
   case only the additions are configured, append-only.
6. **The loop** (Phase 6) runs the new stages exactly as before — briefs, scope check,
   reviewers, gate, refactoring pass, reflection points. Every increment's brief states
   which existing behaviour it may change and that everything else is unchanged, and the
   tests that pin the existing behaviour must stay green.
7. **Project end again.** The close of the addendum's last stage is project end, run by `project-end.md` with the additions at its points, scaled to the change: the User
   Manual is patched for every `CHANGES.md` entry, not written anew, the deliverable is rebuilt and verified
   under the new version, the release is attached, the Issues and Feedback files are
   completed, and `Phase: done` is set. Report "Project complete — <Name> <new version>".

The gates of a change cycle are the same approvals the original build had — the change design, the artifact of each interface variant the change runs, the plan addendum. They are the only gates a change cycle has, and whether the workflow applies is never a question.

This module declares no extension points: a conditional workflow changes a change cycle through the modules whose procedures it runs, each at its own points.
