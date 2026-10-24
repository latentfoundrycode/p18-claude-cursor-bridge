*Answer every open question in this file; raise no new finding; your reply answers each question in place of findings, with no counts.*

# Design critique: stage B4's trait increments revised (subject `traits`), the resolution round R1

## What this round is

Four critique rounds and the confirming read are done (the record below). Two questions are still open: one non-convergent (a critic reversed its own earlier finding), one a Blocking finding the supervisor did not take on a reading of the text. Each question states the candidate answers, each side's position and the material it turns on. Answer each question with a reasoned vote for one candidate and its decisive reason, engaging the other position directly. The supervisor decides on the two votes and records the decision and its reasoning in docs/DESIGN_CRITIQUE.md and docs/INVENTORY.md; then the revision goes to the owner's gate.

## Question 1: the `Installer verification` template gloss (non-convergent)

**The text.** run-parameters.md's template fence, the record of docs/RUN_PARAMETERS.md every project writes, has the line `Installer verification: local | ci-only | n/a (not a desktop application)`. The parameter's own item 4 names installable software as desktop applications, command-line tools and local servers; the gloss, read alone, says `n/a` is for anything that is not a desktop application, so a command-line tool would be recorded `n/a`.

**The positions.** Review B, round 1 (Should fix 3): change the gloss to `n/a (nothing installs)`; the supervisor took it in round 2. Review B, round 2 (Blocking 2) and plan-critic, round 2 (Should fix 3a): leave the fence as it stands; the fence is one unit to the traceability check (`normal_form_fence`), a one-word change drops the baseline unit, and the only `reword` entry that excuses the drop names a baseline heading in the unit's chain, which for the run parameters is a whole-phase heading (the baseline core has no sub-heading there), so the entry would excuse every later drop under that phase; the heading text `The procedure` is also every carved module's, and a core `reword` is matched by heading text in the chain. The supervisor's position (round 3): leave the fence as it stands, record the misreading as a lead for the next edit of that fence that pays its `reword` anyway (docs/HARDENING.md, stage B4; INVENTORY, Decisions, the parameter row).

**Candidates.** (a) Leave the fence as it stands, the misreading a recorded lead. (b) Change the gloss now, paying a core `reword` at the run parameters' baseline heading and a `new` entry on run-parameters.md's section, and record in the Decisions row that the entry excuses every later drop under that phase. (c) Change the gloss now and give the template a `####` heading of its own so the module-side `new` entry is narrow (the core-side `reword` stays whole-phase).

**The fence as it stands (run-parameters.md:57-70):**

````markdown
Record the answers in **`docs/RUN_PARAMETERS.md`**, which you read at every resume and
before every stage close and merge:

```markdown
# Run parameters
Set: <date>   (owner may change any of these at any time by saying so; update this file)
Stage pause: run | pause
Merge authority: supervisor | owner
Refactoring pass: on | off | off for <stages>
Installer verification: local | ci-only | n/a (not a desktop application)
Parallel increments: off | on
```

Three optional lines are never asked and are written only on the owner's recorded word (release A2; the third 2026.10.18a): `Agent ceiling: <seconds>` raises the hour a background agent may run before the loop guard stops counting it, `Ceiling above twice: <kind> <seconds> (<the owner's words>, <date>)` lets the launcher's learned limit for one kind of run (builder, review, watch, test) exceed twice its default, and `Design rounds above five: <subject> <rounds> (<the owner's words>, <date>)` lets one subject's design critique run past its ceiling (Phase 2; written before this step when the subject is the design or the plan).
````

## Question 2: the reach of the `new` entry on delegation-loop.md's "2. Package the brief" (Review B, round 4, Blocking 1)

**The text.** TASK-017 splits step 2's brief paragraph: its frozen-rule sentences ("For a UI-bearing increment, the brief must name the exact approved mockup file(s) ... applicable rule.") go to has screens under a `###` in its `## Add at delegation-loop.brief-constraints` section; the remainder stays in delegation-loop.md. The remainder is not a baseline unit, so it needs a `new` entry; the Done when names `new TASK-017 bridge/cursor-bridge/workflow/phases/delegation-loop.md 2. Package the brief`, and a core `reword` at "2. Package the brief" excuses the drop of the baseline paragraph.

**The positions.** Review B, round 4 (Blocking 1): the section "2. Package the brief" runs to "### 3. Delegate to Cursor" and holds four paragraphs (the brief paragraph, the Workspace-boundary paragraph, the reality-check paragraph, the plan-check paragraph), so the `new` entry would excuse all four and take three of them out of the copy check, and the derivation test would pin the whole span; the remainder should stand under a heading holding only it, with the entry on that heading, and no entry on "2. Package the brief". The supervisor (round 4, holding the finding open for this round) and plan-critic (round 3, "delegation-loop.md's steps are `###` siblings of `### The procedure`, so '2. Package the brief' holds only its one paragraph (L57-71) and the step-2 `new` entry is needed and sufficient"): as the module stands the section holds one paragraph, delegation-loop.md:59-71, one unit to the check (lines joined until a blank line), the next heading at :73; the sentences Review B names as four paragraphs are sentences of that one paragraph; the entry excuses exactly the split's remainder.

**Candidates.** (a) The `new` entry on "2. Package the brief" as planned, the section holding the one paragraph. (b) A heading of its own for the remainder (a `####` inside step 2 would be the step's only paragraph anyway), the `new` entry naming it, and the STRUCTURE pin of tests/test_phase_modules_build.py re-taken for the added heading.

**The section as it stands (delegation-loop.md:55-75, line numbers in the margin):**

````markdown
55: whatever was already there.
56: 
57: ### 2. Package the brief
58: 
59: Delegate to **spec-packager** to write `handoff/TASK-<nnn>.md`. The brief must be
60: self-contained — Cursor gets no conversation history, only this file. For a UI-bearing
61: increment, the brief must name the exact approved mockup file(s) and the relevant
62: `docs/design/DESIGN.md` sections, and list the frozen `vercel-interface.mdc` as an
63: applicable rule. Every brief carries the Workspace boundary and the standing invitation to
64: note tooling friction in `docs/BUILDER_NOTES.md` (spec-packager's constraints template).
65: spec-packager's **reality check** runs first: the schema, configuration, data, and
66: interfaces the increment assumes must exist in the codebase *as built*; "approved in the
67: plan" is not "fits the data" (KP-019). A mismatch comes back to you as a scope question,
68: not as a brief. Once the brief is written, `python ~/.claude/cursor-bridge/plan-check.py`
69: compares it with its increment: a Scope path outside the increment's Scope or a requirement
70: the increment satisfies that the brief does not name is a `BRIEF` failure, fixed in the brief
71: before the checkpoint commit (release A4: a brief once silently dropped planned work).
72: 
73: ### 3. Delegate to Cursor
74: 
75: ```bash
````

## The check's rules the two questions turn on (trace-check.py:755-830)

````python
            current_counts_all[nf] = current_counts_all.get(nf, 0) + 1
            if rel not in current_paths_all.get(nf, []):
                current_paths_all.setdefault(nf, []).append(rel)
            if not unit_excused(rel, u, excused_current):
                current_counts_c[nf] = current_counts_c.get(nf, 0) + 1
                if rel not in current_paths_for_norm.get(nf, []):
                    current_paths_for_norm.setdefault(nf, []).append(rel)

    fails_dropped = []
    fails_copy = []
    fails_new = []
    fails_ref = []
    fails_cite = []
    notes = []
    seen_norm_finding = set()
    dropped_count = 0
    excused_count = 0

    def reword_excuses_drop(traced):
        chain = traced["chain"]
        for file_rel, heading, inc_id in reword_baseline:
            if file_rel != CORE_REL:
                continue
            if in_section(chain, heading):
                return inc_id
        return None

    for traced in baseline_supervisor_traced:
        nf = traced["normal"]
        b = baseline_units_by_norm.get(nf, 0)
        c_all = current_counts_all.get(nf, 0)
        c = current_counts_c.get(nf, 0)
        bh = traced["baseline_heading"]

        if nf in seen_norm_finding:
            continue

        if c_all == 0:
            rid = reword_excuses_drop(traced)
            if rid:
                notes.append(
                    "NOTE (reword %s) %s: %s - %s"
                    % (rid, CORE_REL, bh, excerpt(nf))
                )
                excused_count += 1
                seen_norm_finding.add(nf)
            else:
                fails_dropped.append(
                    "FAIL (dropped) %s: %s - %s" % (CORE_REL, bh, excerpt(nf))
                )
                dropped_count += 1
                seen_norm_finding.add(nf)
        elif c > b:
            paths = sorted(current_paths_for_norm.get(nf, []))
            fails_copy.append(
                "FAIL (copy) %s: %s - %s"
                % (", ".join(escape_field(p) for p in paths), bh, excerpt(nf))
            )
            seen_norm_finding.add(nf)

    module_files = sorted(
        rel for rel in current_workflow_paths if is_module_path(rel)
    )
    baseline_set = set(baseline_units_by_norm.keys())

    for rel in module_files:
        for u in current_file_units.get(rel, []):
            if unit_excused(rel, u, excused_current):
                continue
            nf = u["normal"]
            if nf not in baseline_set:
                h = deepest_heading(u["chain"])
                fails_new.append(
                    "FAIL (new) %s: %s - %s" % (escape_field(rel), h, excerpt(nf))
                )

````

## The record so far

## Subject: traits (stage B4's trait increments revised before TASK-017's first edit: the Scopes, the home of every passage, two registry refinements; a scoped revision mid-build, 2026-10-24)

**What is criticised:** a scoped revision of release B's plan before stage B4's TASK-017, prompted by the supervisor's reality check of the text as built (the delegation loop's step 2 rule, applied to its own text; run/supervisor/task017-reality-check.md, quoted in the critique's file): TASK-017's Scope missed files that hold or pin passages it moves (project-end.md, run-parameters.md, bridge/agents/plan-critic.md, the registry, seven test files), named reflection.md as a has-screens source (it holds none), gave no home to passages no registry point places (the UI acceptance criteria, the benchmark and contract-capture increments, the refactoring pass's optimization candidates, the manual's chapters and the Performance-Patterns entries at project end), named the deployed-layout and bounded-remote-wait checks as passages to move where no module holds them (the plan's P11 puts them under external services, its §13.1 the bounded wait under spends money), and said nothing of the units two traits share (design's performance and code-signing sentences; step 6; project end's manual) or of the `Installer verification` parameter the five-names pin holds. The revision: TASK-017's Scope and Done when rewritten passage by passage with the extension point each goes to; two §6.4 refinements of the registry (`planning.stages` widened to increments, `planning.acceptance-criteria` new), made by TASK-017 with planning.md; five INVENTORY Decisions rows (the moving rule and what stays; the refinements; the parameter kept; the two checks as external services' new text with spends money pointing at them; the plan critic's lenses moved); TASK-018 depending on TASK-017 for its pointer; TASK-019 and TASK-021 naming their delivery kinds by key with the kind's procedure at `project-end.delivery`; a HARDENING placement block. No requirement row changes. The Decisions rows are the design revision (a refinement of §6.4), the increments the plan revision; one subject holds both. The critics read `run/review/DESIGN-traits-<round>.md`, built from the committed records.

**Accepted** (finding, critic, round, the reason):
- TASK-022 should depend on TASK-017, both Scopes naming the same four files (Review B, round 1, Should fix 4): TASK-022 merged on 2026-10-24 (PR #66) before this revision, and status is derived from `origin/main`, so the order is settled; no field changes.
- interface.md's mockup sentence should move into the trait (Review B, round 1, Should fix 5): interface.md's sentences state the activation model, which workflow activates which variant, and are pinned as R-010's and R-012's built half; the trait's addition at `interface.variants` names the variant it activates, as the point's line asks, in its own words; the two are not one text, and the registry's prose says an addition adds what its workflow needs, never a second copy of the procedure.
- The registry refinement should be an increment of its own before TASK-017 (plan-critic, round 1, Should fix 5): kept in TASK-017; the refinement is four files, a REJECT on a trait's move costs a round and not the refinement, and an increment of its own costs a gate pass (INVENTORY, Decisions).
- Cost budgets land in a trait whose definition names speed, size and frame rate (plan-critic, round 1, Consider 1): intended and recorded (INVENTORY, Decisions): a cost budget is one operation, one condition, one number measured by a benchmark, like a speed budget; spends money's cap is the project's total.
- The `Installer verification` template gloss `n/a (not a desktop application)` misreads a command-line tool (Review B, round 1, Should fix 3, taken in round 2; reversed by Review B's round-2 Blocking 2 and plan-critic's round-2 Should fix 3a, which found the one-word change drops a fenced baseline unit under a whole-phase heading): **non-convergent** under design.md's rule, recorded here, starting no round and held for the resolution round; the records meanwhile read as round 3 wrote them, the fence standing as it is and the misreading a lead (INVENTORY, Decisions; docs/HARDENING.md, stage B4).
- configuration.md's security-tooling paragraph keeps "the same way", which pointed at the design-tooling paragraph has screens takes (Review B, round 3, Should fix 3; plan-critic, round 3, Consider 1): the unit is a baseline unit under a whole-phase heading, a `reword` there would excuse every later drop under it, and the paragraph's own list of files states the work; a lead (docs/HARDENING.md, stage B4).

**Rounds** (round, kind, the commit its file was built from, critic, Blocking / Should fix / Consider, what was fixed):
- 1, critique, file at 31e74db, Review B (grok-4.7-medium): 2 / 6 / 1. Fixed: the split rule rewritten on the trace check's own mechanics, a unit moving whole into a section of moved units only, two units split (design's performance-and-code-signing paragraph under the standing "Phase 2 — Design" reword; step 2's brief paragraph under a new "2. Package the brief" reword) with three entries each, the trait's half under a `###` of its own, and every other mixed unit kept whole (the configurator paragraph, the routing table, intake's security-context paragraph, the manual item); installable's delivery procedure written once, the `for installer` section the passage word for word and the `for install-script` section one new sentence (B1, with plan-critic's S1 and S3); TASK-019's sub-type sets one key, `installer`, a local web app wanted as an install script pausing at intake (B2, with plan-critic's B2); `planning.stages`' declaring line reworded for increments (S1, with plan-critic's C2); the design-document performance lens stays in plan-critic.md, the plan lenses move, and plan-critic.md gains the missing-trait sentence (S2, with plan-critic's B1); the template gloss `n/a (nothing installs)` (S3); TASK-019, TASK-020 and TASK-021 take trace-exceptions.md and tests/test_b3_least_confident.py with `new` entries for their type files (S6); the HARDENING stay list completed (C1). S4 and S5 accepted above.
- 1, critique, file at 31e74db, plan-critic: 2 / 5 / 4. Fixed: the design-document performance lens stays in plan-critic.md, only the plan-section lenses move (B1, with Review B's S2); TASK-019 sets `installer` (B2, with Review B's B2); the three trace entries per split, the trait's half under a `###` (S1, with Review B's B1); installable's stage text scoped to the kinds `installer` and `install-script`, `n/a` passing the check over (S2); the manual's chapters stay in project-end.md, the per-kind sections holding only the final check and the attach step (S3, with Review B's B1); step 6's fate stated: title and first sentence kept, the place of test-check additions, its pin standing (S4); the new point's position named, the stages line saying where an increment addition goes (C2); the spends-money pointer made checkable at the design gate (C3); interface.md dropped from the Scope, run-parameters.md kept for its gloss (C4). S5 and C1 accepted above.
- 2, critique, file at 56ba77b, Review B (grok-4.7-medium): 2 / 4 / 1. Fixed: design's split paragraph leaves design.md whole, so the module takes no entry for it and the standing reword excuses the drop; the critique-file sentence goes into "Traits at the design gate", a section already excused, and says each lens is collected once for the project (B1, with plan-critic's S2); the template fence stands as it is (B2, with plan-critic's S3a; the reversal recorded above as non-convergent); step 6's title and first sentence stand, nothing added (S1, with plan-critic's S3b); project-end.md's `project-end.delivery` line no longer anchors on "Deliver the installer": the delivery for the named kind, after the User Manual item and before the promotion pass, its pin re-taken (S2, with plan-critic's S4); the Observability & Verifiability paragraph's closing sentences, the non-UI opt-out and the driver escalation, stay in design.md under a `###` with a `new` entry, the UI sentences moving word for word (S3); TASK-018's Done when names each `## Add at` key and the `new` entry for every section (S4); the missing-trait sentence's budget arm points at a plan's critique file with no benchmark-increments lens (C1).
- 2, critique, file at 56ba77b, plan-critic: 0 / 6 / 3. Fixed: the four `planning.critic-lenses` sections take `new` entries, the trace check not reading plan-critic.md, and test_traits_existing.py asserts their words equal the bullets plan-critic.md loses (S1); the design split's entry count corrected and the critique-file sentence placed in the excused section (S2, with Review B's B1); the gloss kept and the step 6 sentence dropped, so neither needs an entry, and the carve test's NOTE lines and excused count named among the re-taken pins (S3, with Review B's B2 and S1); the project-end anchor (S4, with Review B's S2); the registry's paragraph on the points added to §6.4's list names the new point and the widening, its pin re-taken (S5); the scoping sentence reads "the packaging stage its type workflow adds, if any", and the Decisions row says the bridge's own release has none by design (S6); the sub-file folder dropped from the Scope (C1); `###` headings unique within a file (C2); planning's two-critic paragraph named among what stays (C3).
- 3, critique, file at cbfb618, Review B (grok-4.7-medium): 2 / 3 / 1. Fixed: the Observability paragraph's UI sentences go to has screens under a `###` of their own with a `new` entry, a fragment being new text to the check, and its closing sentences stay in design.md under a `####` inside "The procedure", placed directly before `### The delivery kind` so that no other paragraph falls under it; in a trait file every `###` stands last in its section, after every moved unit, and test_traits_existing.py asserts no moved unit lies under one (B1, with plan-critic's S1); planning's packaging paragraph moves untouched, the scoping sentence under a `###` of its own after it (B2, with plan-critic's S1); intake's delivery paragraph gets the same scoping `###` for a part of another kind (S1); TASK-019 to TASK-021 say the derivation and the pins cover their type files' entries, the first to merge widening the reading to `types/` (S2); the revision note no longer lists run-parameters.md (C1). S3 accepted above.
- 3, critique, file at cbfb618, plan-critic: 0 / 3 / 5. Fixed: the placement rule for `###` sub-sections in trait files and the `####` before `### The delivery kind` in design.md, the Observability UI half and installable's scoping sentence each named as a `###` of its own (S1, with Review B's B1 and B2); the parameter's Decisions row says project end's item keeps its words and planning's paragraph is untouched, the reference standing in the scoping sentence (S2); the Observability remainder reworded to name what it opts out of, the driver sentence a pointer (S3); planning.md's and project-end.md's survival-list pointers reworded in their excused sections, configuration.md's "the same way" accepted above (C1); TASK-018's parenthetical says design.md is not changed (C2); tests/test_phase_modules_close.py's whole-file-entry test extended to `traits/` and `types/` (C3); the manual's command-reference chapter read as installable with a command-line surface, recorded (C4); the S64 assertion message named (C5).
- 4, critique, file at 48616da, Review B (grok-4.7-medium): 1 / 4 / 1. **Open for the resolution round** (B1): the `new` entry on delegation-loop.md's "2. Package the brief" would, Review B holds, excuse four paragraphs and take three of them out of the copy check; as the module stands the section holds one unit, the brief paragraph (delegation-loop.md:59-71, the next heading at :73), which plan-critic's round 3 read the same way, so the entry excuses exactly the split's remainder; a Blocking finding the supervisor does not take goes to the resolution round. Fixed: the planning pointer named by its section, "What the interface phase hands to the plan" (S1, with plan-critic's C1); intake's scoping sentence keyed off the kinds `installer` and `install-script`, as planning's is, so a local web app's delivery questions are asked (S2); the split paragraph's middle sentence homed with performance budgets, its first three sentences (S3); the test clause reads: moved units with new text only under a following `###`, or new text throughout under its own `new` entry (S4); the four split fragments get the words-equal assertion against constants (C1, with plan-critic's S2 and C3).
- 4, critique, file at 48616da, plan-critic: 0 / 5 / 3. Fixed: the STRUCTURE pin of design.md in tests/test_phase_modules_intake_design.py named among the re-taken pins, the `####` being a heading it lists (S1); the words-equal assertion extended to the four fragments, the pre-move text as constants (S2, with Review B's C1, and C3); design's Delivery section followed by its own scoping `###`, keyed off the kinds (S3); the missing-trait sentence catches an absence: a `Delivery kind:` of `installer` or `install-script` with no packaging lens, an external input named with no external-service lens, a screen-and-state inventory with no design-criteria lens, a budget with no benchmark-increments lens (S4); a trait added at the design gate has its `intake.questions` additions asked before the design is presented again, in "Traits at the design gate" (S5); the planning pointer's section named (C1, with Review B's S1); the one-increment reason corrected to the registry's coupling with planning.md and the gate-pass cost (C2).
- 5, confirming read (final), file at e06694e, Review B (grok-4.7-medium): 0 / 3 / 1. Fixed: design's split paragraph is three sentences, its first two to performance budgets and its code-signing sentence to installable, the constants cut there (S1, with plan-critic's S1); the missing-trait sentence's screen trigger is the design showing screens, interface.md's condition, since the inventory itself moves (S2); the Decisions row pairs each trigger with its lens (S3); the design and the register are revised from a gate-added trait's new answers before the presentation (C1).
- 5, confirming read (final), file at e06694e, plan-critic: 0 / 3 / 2. Fixed: the split's sentence count (S1, with Review B's S1); the external-services trigger keyed off the trait's definition, a service run by others (S2); a trait added at the gate also has its `design.sections` and `design.mandatory-diagrams` additions written before the presentation (S3); intake's scoping sentence says the passage confirms the kind first (C1); each split's fragments, concatenated, equal the baseline unit as trace-check.py reads it (C2).

**Resolution**: due, the confirming read leaving nothing Blocking; `run/review/DESIGN-traits-R1.md` holds two questions: the template gloss (non-convergent, above) and Review B's round-4 Blocking 1 on the step-2 entry's reach (open, above).

**Gate**: not yet held.
