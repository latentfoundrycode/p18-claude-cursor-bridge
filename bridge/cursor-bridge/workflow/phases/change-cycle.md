## The change cycle — a request on a finished project

A project whose status is `Phase: done` and whose owner asks for a change runs the same
phases as the original build, **scaled to the delta**: everything already approved stays
approved, everything the change touches goes through its gate again, and nothing else is
re-presented. Set `Phase: changing` and record the request in `PROJECT_STATUS.md` under
`Change cycle:` with a short name and the date.

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
   through the gates as a change to that decision. A report of **several defects** is triaged before any of them is diagnosed — the `root-cause-first` skill's step 0: shared cause binned only on evidence, otherwise one at a time. Gate: summarise the change back and get confirmation.
2. **Design revision** (Phase 2, scaled). Append a dated **Change: <name>** section to
   `docs/DESIGN.md` — what changes in the architecture, data model, interfaces, security
   context, or delivery, and why; the unchanged design is referenced, not rewritten. **Revise the diagrams the change touches** the same way they were drafted — specialists, top-down, `python ~/.claude/cursor-bridge/diagram-check.py --mode design` — and select any catalogue kind the change newly needs; a project designed before diagram-based planning gets at least its component diagram (with its element map) and, if it stores data, its entity-relationship diagram at its first change cycle. Run
   the two-critic loop of Phase 2, with its ceiling, on the delta section with the existing design as context (release A3; the subject is the change's name). Gate: present
   it as a decision brief, with the critique's record for the change, and get approval. Patch the Project Summary at this gate.
3. **UI mockups** (Phase 3) **only if the change touches the UI**, and only for the
   affected screens and states; the visual system is amended, not replaced. Gate as in
   Phase 3.
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
7. **Project end again.** The close of the addendum's last stage is project end: the User
   Manual is patched for every `CHANGES.md` entry, the deliverable is rebuilt and verified
   under the new version, the release is attached, the Issues and Feedback files are
   completed, and `Phase: done` is set. Report "Project complete — <Name> <new version>".

The gates of a change cycle are the same approvals the original build had — the change
design, the mockup if any, the plan addendum. They are the only questions a change cycle
asks the owner. Whether the workflow applies is not one of them.
