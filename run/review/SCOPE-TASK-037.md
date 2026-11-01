# SCOPE - TASK-037: reports, run sheets, the critique's record and project state (R-047, R-048, R-053) (pull request #118)

Supervisor-authored governance text in release T's stage T1 (docs/BUILD_PLAN.md, "### TASK-037", and the release T constraints paragraph above "## Stage T1"). No builder ran, so there is no brief and no builder report. No program changes.

## Scope (the plan's, quoted)
bridge/commands/supervisor.md (rules 12, 43 and 48; "Project state": the Decisions row's sentence and the status template); bridge/cursor-bridge/session-start.py (the digest's rule 12 in the question form, the digest within 9,500 characters with every rule number kept, trimmed elsewhere as TASK-034 trimmed it, the trims named in the trace entry); bridge/skills/explain-for-decision/SKILL.md (the run sheet: a vendor console from documentation fetched at the time, with the exact path); bridge/commands/calibrate-bridge.md (step 5: the `Calibrated:` line rewritten at each calibration, the earlier text living in git); bridge/cursor-bridge/workflow/phases/design.md (T1 one subject for a design with its addendum; T3 the record's definitions; T7 the snapshot id `DESIGN-<subject>-<round>` and the `.err` name from it; P9 the worked-scenario lens); bridge/cursor-bridge/workflow/phases/change-cycle.md (item 2: the pause before planning work, the model named, a push notification where Remote Control is on, T26); bridge/agents/plan-critic.md (P9's lens); bridge/cursor-bridge/Diagram-Planning-Conventions.md (§8: the all-omitted index, the minimum set binding every project whose code has components, the calibration's retrofit reading the same rows, P20); bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_release_t_records.py; tests/test_session_start.py; tests/test_core_carve.py; tests/test_phase_modules_intake_design.py; tests/test_phase_modules_close.py; tests/test_b3_least_confident.py; tests/test_calibrate_text.py; tests/test_leads_b3.py (pins re-taken).

Settled points:
- The digest lives in bridge/commands/supervisor.md between its markers, and session-start.py reads it there. So session-start.py and tests/test_session_start.py are unchanged; that test's cap and rule-number checks pass on the new text (digest 9,493 of 9,500).
- **A widened region.** calibrate-bridge.md's region widens beyond step 5 to its diagram-coverage bullet (commit 8088f24). The bullet now counts a kind of the minimum set that the diagram index omits as selected, when its reason is recorded in the index's Why column and in the inventory's Decisions. This is P20's "the calibration's retrofit reading the same rows", which the Scope names under §8. It removes the contradiction Review A found at round 2 (Should fix 1), and Review A has no objection to it standing.

## What the text must do (the plan's Done when, in short)
Each item's sentence stands in the home the design's table names:
- R-047: T1, T3, T7 and T26.
- R-048: D11 in rule 43, D10 in the run sheet, D7 in the digest's rule 12 and the core's, D6 in step 5 and the template.
- R-053:
  - P10, in "Project state": the Decisions-row sentence, the next report naming every decided-but-unbuilt rule, and the `Running projects must` sentence for a release that adds a safety mechanism.
  - P9's lens, in design.md and plan-critic.md.
  - P20, in the conventions' §8 and the calibration's coverage bullet.

The digest stays within its cap with every rule number. Every reworded passage has its `reword` entry and every new section its `new` entry, and trace-check is green. tests/test_release_t_records.py is written first and red on the checkpoint. The pins on reworded sentences are re-taken. MANIFEST is regenerated. No program's behaviour changes.

## The tests the supervisor wrote first
tests/test_release_t_records.py names R-047, R-048 and R-053. It enforces docs/REQUIREMENTS.md R-047, R-048 and R-053 and TASK-037's Done when, with one test per item label:
- `test_r047_t1_a_plan_addendum_from_round_1_is_one_subject_with_the_design` (T1, design.md "The procedure")
- `test_r047_t3_the_records_definitions` (T3, design.md, with the failed-launch paragraph reconciled and the old "the round recorded as not run" and "the round stays not run" absent)
- `test_r047_t7_the_snapshot_id_and_the_err_name_together` (T7, design.md)
- `test_r047_t26_the_pause_before_planning_work_with_a_push_notification` (T26, rule 48 and the change cycle's item 2)
- `test_r048_d11_a_turn_ending_on_a_run_names_its_limit` (D11, rule 43, with a run still waiting for the slot, and the old "earliest" wording absent)
- `test_r048_d10_a_vendor_console_from_documentation_fetched_at_the_time` (D10, the run sheet)
- `test_r048_d7_rule_12_in_the_question_form_in_the_core_and_the_digest` (D7)
- `test_r048_d6_the_calibrated_line_is_rewritten` (D6, step 5 and the template line)
- `test_r053_p10_a_decided_rule_not_yet_built` (P10, "Project state")
- `test_r053_p9_the_worked_scenario_lens_in_both_critics` (P9)
- `test_r053_p20_the_all_omitted_index_and_the_minimum_sets_binding` (P20, the conventions' §8 and the calibration's coverage bullet)

All eleven were shown failing on the checkpoint d6c1f35 by `mutation-run.py --checkpoint`. The per-test lines are in the accept commit's message. Review A's fixes later strengthened six of them; no assertion was loosened.

Pins re-taken, each an exact equality as before:
- tests/test_core_carve.py: the trace NOTES list gains six lines, the TRACED line becomes 139 / 222 / 0 dropped / 63 excused (424 in all, as before), and the docstring is updated.
- tests/test_phase_modules_close.py and tests/test_b3_least_confident.py: the change cycle's procedure, its length and sha256.
- tests/test_b3_least_confident.py: design.md's "The procedure" is pinned, newly excused by TASK-037's `new` entry. It was re-taken after round 1's B1 fix.

The mutants file is run/supervisor/TASK-037-mutants.json (gitignored, not in the diff). It holds 28 mutants, each undoing one pinned sentence and naming the test that must fail:
- m1: T1's "is no subject of its own"
- m2: T3's `not run (<the reason>)` row
- m3: T7's ".err file's name follows from it"
- m4: T26's push notification in rule 48
- m5: T26's "Pause before it" in the change cycle
- m6: D11's "names the run's limit"
- m7: D10's "fetched at the time"
- m8: D7's digest clause
- m9: D7's `AskUserQuestion` in the core
- m10: D6's "never appended to"
- m11: D6's template suffix
- m12: P10's "the next report"
- m13: P9's "both critics"
- m14: P9's **Blocking** grade in plan-critic
- m15: P20's "every project"
- m16: T3's commit definition
- m17: T7's snapshot id
- m18: P10's release sentence ("names")
- m19: P20's retrofit "same rows"
- m20: D10's "never sent"
- m21: B1's "either critic" (round 1)
- m22: S1's planning-work exception in rule 48 (round 1)
- m23: S2's `slot taken` for a heavy run (round 1)
- m24: the calibration bullet's clause (round 2, S1)
- m25: §8's "both places" (round 2, C2)
- m26: rule 43's waiting-run sentence (round 2, C1; re-anchored after the re-read)
- m27: rule 43's "latest" read back as "earliest" (the re-read's B1)
- m28: rule 43's `unknown`-holder clause (the re-read's C2)

Its run's result is under "Before this round".

## Bookkeeping and records expected in the diff
- docs/REQUIREMENTS.md: R-047, R-048 and R-053 built, with Evidence per item label.
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009), and the six lines it replaces archived word for word in docs/archive/STATUS_HISTORY.md.
- project.json's stage.
- docs/HARDENING.md: a TASK-037 section with two leads, both outside this Scope (commit ed9b8a5):
  - the merge policy's and KP-062's "the round stays not run" wording, for TASK-038's brief or a later text release;
  - the digest's 7 remaining characters.

## Before this round
- Full suite with this pull request's variables, in P7's documented `--key-file` form, on ed9b8a5 (before Review A round 2's text fixes): 3,295 passed, 40 skipped, exit 0 (run/agent/TASK-037-suite.out, not in the diff). After 8088f24 and 8d86819, the increment's tests and the Scope's pin files: 215 passed. CI runs the full suite on the pull request's head.
- trace-check: OK (424, 0 dropped, 63 excused).
- diagram-check --mode design: OK.
- bridge-check --sources: 144 OK.
- Review A (diff-reviewer):
  - Round 1: REJECT, Blocking 1 / Should fix 2 / Consider 5, all taken but C1 and C4 (commit e1ad914; C4 recorded as a HARDENING lead).
  - Round 2: APPROVE, Should fix 1 / Consider 2, all taken (8088f24).
  - Re-read of 8088f24: REJECT, Blocking 1 (rule 43's `ends by` read as the earliest) / Consider 2, all taken (8d86819).
  - Re-read of 8d86819: APPROVE, no findings.
  - The re-reads were fixes before this snapshot, so they open no round.
- Mutation run on 8d86819 (the mutants file as listed above; no duplicates cut, about 29 processes estimated): exit 0, 28 run, 28 killed, 0 survived, 0 not applied, 0 errors (run/agent/TASK-037-mutation.out, not in the diff).

This is Review B's round 1, below the ceiling. Release T's later increments (TASK-038 to TASK-045) are later work, not this diff's defect.
