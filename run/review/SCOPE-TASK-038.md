# SCOPE - TASK-038: the merge step in its own sub-file; the merge mechanics and where reviewers write (R-045, R-046) (pull request #119)

Supervisor-authored governance text in release T's stage T1 (docs/BUILD_PLAN.md, "### TASK-038", and the release T constraints paragraph above "## Stage T1"). No builder ran, so there is no brief and no builder report. No program's behaviour changes: session-start.py gains one line of the hook's text, and settings.bridge.json, the installer's data, gains three allow rules.

The branch's commits, in order:
- 9dec83d: the move. Step 8 (the verified gate) moved verbatim from delegation-loop.md into the new delegation-loop/merge.md, with a "Where this sub-file belongs" header, the module keeping a one-paragraph pointer "8. Merge — in a sub-file" and naming the sub-file third on its `Sub-files:` line. Its diff shows the passage leaving one file and arriving unchanged in the other; read it apart from the rewording.
- d3fb793: the accept. The rewording of (b), the allow rules of (c), the tests of (d), the pins re-taken, the trace entries, MANIFEST.
- 0d97666: records (R-045 and R-046 built; the status file as at this pull request's merge).
- 9f6e372: records (Review A round 1's leads in HARDENING).

## Scope (the plan's, quoted)
bridge/cursor-bridge/workflow/phases/delegation-loop.md; bridge/cursor-bridge/workflow/phases/delegation-loop/merge.md (new); bridge/commands/supervisor.md (rule 43 and the status template: the status file as at the merge, `in-flight.md` between merges, T11 and T17); bridge/cursor-bridge/session-start.py (the hook's text on `in-flight.md`, T17; its module table unchanged, the sub-file read from the pointer line); bridge/cursor-bridge/Merge-Verification-Policy.md ("Invocation": T5's clauses, T8's bare commands, T4's title form; its convergence paragraph untouched here); bridge/cursor-bridge/workflow/phases/design.md (the constant prompt and the receipt check: T5, T2); bridge/cursor-bridge/workflow/phases/reflection.md (steps 4 and 6: T16, T25); bridge/agents/diff-reviewer.md (T5, T2); bridge/agents/secret-sentinel.md (P5: every pushed commit scanned for computer paths and account names); bridge/cursor-bridge/settings.bridge.json (the allow rules `Bash(git branch -D:*)`, `Bash(gh pr list:*)` and `Bash(gh issue list:*)`; the test kind's `--key-file` form where TASK-036's launch was prompted); bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_release_t_merge.py; tests/test_allowlist.py; tests/permission_rules.py (in that case); tests/test_phase_modules_build.py; tests/test_session_start_module.py; tests/test_session_start.py; tests/test_core_carve.py; tests/test_b3_least_confident.py; tests/test_loop_text_pace.py; tests/test_phase_modules_close.py; tests/test_a5_followups.py (pins re-taken: the sub-file pointers, step 8's names and sentences, the stage review's part sentence T25 edits)

Out of scope: every other file. Release T's later increments (TASK-039 to TASK-045) are later work, not this diff's defect; in particular rule 6 and the convergence text (TASK-039), the `--strip` launch forms and KP-061's command line (TASK-041), Known-Pitfalls.md as a whole, and every program (loop-guard.py among them).

Settled points (the accept commit d3fb793 lists them too):
- TASK-034's trace entry for step 8 moves with the text to merge.md (no duplicate entry); TASK-038's own `reword` and `new` entries record each reworded section.
- **A widened region.** The policy's region widens from "Invocation" to its design mode: the constant prompt's copy kept equal to design.md's, and a failed last launch worded as design.md words it ("Review B's row stays `not run (<the reason>)`"), one half of TASK-037's HARDENING lead; KP-062's half stays a lead (Known-Pitfalls.md is outside this Scope).
- The policy's two pointers to step 8 name delegation-loop/merge.md, and the core's sentence on sub-files ("The phase modules") names step 8's (the pointer sweep; its `new` entry in trace-exceptions.md).
- T16 and T25 stand in reflection.md's step 4, where the parts are read (the plan names steps 4 and 6; step 6 is verify).
- T4 follows the evaluation of 2026-10-25, row 6; ISS-013's rule kept.
- (c)'s conditional `--key-file` rule is not taken: TASK-036's first P7 launch ran with no prompt and no refusal (DESIGN.md's host table), as TASK-037's two and this increment's did, so tests/permission_rules.py is unchanged.
- The new pin of the module's pointer section, whose parametrised id holds an em dash, came back `not run` from `--checkpoint` in both id forms, so it is not listed in `new_tests`; the pointer's text is pinned by test_r045_a, failing on the checkpoint (a HARDENING lead, 9f6e372).

## What the text must do (the plan's Done when, in short)
(a) step 8 moved verbatim first, then reworded; the module within R-032's bound (now 41,737 characters, 69.6%); merge.md in the bound test's list; trace finding every moved passage; the hook naming the sub-file after the module. (b) R-045's T4, T8, P7, P5, P4's text, T11 and T17, and R-046's T5, T16, T25 and T2, each in the home the plan names. (c) the three allow rules. (d) tests/test_release_t_merge.py written first and red on the checkpoint; the trace entries; MANIFEST regenerated.

## The tests the supervisor wrote first
tests/test_release_t_merge.py names R-045 and R-046. It enforces docs/REQUIREMENTS.md R-045 and R-046 and TASK-038's Done when, one test per item label:
- `test_r045_a_step_8_stands_in_its_own_sub_file` ((a): the pointer, the `Sub-files:` line, merge.md's heading and header)
- `test_r045_t4_the_title_form` (T4, merge.md and the policy's Invocation)
- `test_r045_t8_push_and_merge_bare` (T8, merge.md)
- `test_r045_p7_the_suite_with_the_pull_request_variables` (P7, merge.md; the command `tests/test_allowlist.py` reads)
- `test_r045_p5_every_pushed_commit_scanned` (P5, merge.md and secret-sentinel.md)
- `test_r045_p4_the_merged_branch_deleted_and_the_armed_form_skipped` (P4's text, merge.md)
- `test_r045_t11_t17_the_status_file_as_at_the_merge` (T11 and T17: rule 43, the template's `In flight:` line, the hook's line, merge.md's overtaken pull request)
- `test_r045_c_the_three_allow_rules_and_the_commands_they_admit` ((c), settings.bridge.json)
- `test_r046_t5_where_a_reviewer_may_write` (T5: merge.md's directive clauses, the policy's Invocation, design.md's constant prompt and the policy's copy of it, diff-reviewer.md)
- `test_r046_t16_single_test_files_beside_review_b` (T16, reflection.md step 4 and merge.md)
- `test_r046_t25_each_parts_turn_budget` (T25, reflection.md step 4)
- `test_r046_t2_a_clean_reply_names_three_verified_statements` (T2: design.md's prompt and receipt check, diff-reviewer.md)
- `test_policy_design_mode_the_failed_launch_as_design_md_words_it` (the widened region's failed-launch sentence)

Besides these, three new parametrised ids in existing files, listed by their bracketed ids:
- `tests/test_phase_modules_build.py::test_r032_the_module_and_its_sub_file_are_read_whole[delegation-loop/merge.md]` (R-032's bound for the new sub-file)
- `tests/test_b3_least_confident.py::test_item2_each_excused_module_section_has_one_heading_and_is_pinned[delegation-loop/merge.md-8. Merge (the verified gate)]` and `[delegation-loop/merge.md-Where this sub-file belongs]`

All sixteen were shown failing on the checkpoint ca0ee2c by `mutation-run.py --checkpoint` (run/agent/TASK-038-checkpoint3.out, exit 0; the per-test lines are in the accept commit's message). The rerun with the mutants file as it now stands is under "Before this round".

Pins re-taken (each an exact equality as before; run/supervisor/rt038_pins.py and rt038_carve_pin.py, not in the diff):
- tests/test_phase_modules_build.py: the sub-files line, the module's headings (the pointer's), the procedure sentence ("steps 7 and 8 in sub-files of this module"), the bound list, the hook's names, the core's sub-file sentence.
- tests/test_session_start_module.py: the delegation loop's sub-files.
- tests/test_loop_text_pace.py: step 8 read from merge.md; the directive's "sixth clause".
- tests/test_b3_least_confident.py: the pins derived from the entries (delegation-loop.md's step 8 dropped; its pointer and merge.md's two sections added; delegation-loop.md's, design.md's and reflection.md's "The procedure" re-taken).
- tests/test_core_carve.py: three NOTE lines; the TRACED line 139 / 219 / 0 dropped / 66 excused.

The mutants file is run/supervisor/TASK-038-mutants.json (gitignored, not in the diff). It holds 30 mutants, each undoing one pinned sentence and naming the test that must fail:
- m1: the `Sub-files:` line drops merge.md (a)
- m2: T4 allows a plan ID in the parentheses (merge.md)
- m3: T4's ISS-013 clause dropped (the policy)
- m4: T8's "run bare" undone
- m5: P7's event `pull_request` made `push`
- m6: P7's `<n>` read as the latest pull request, not one above the latest pull request or issue
- m7: P5's "never covered by a later commit" allowed
- m8: P5's sentinel back to the staged diff only
- m9: P4 arms the auto-merge anyway
- m10: P4 keeps the remote branch
- m11: T11's resume reads the status file, not `in-flight.md`
- m12: T17's overtaken pull request dropped from the core
- m13: T11's template `In flight:` line put back
- m14: T17's hook line dropped (session-start.py)
- m15: T17's merge of `main` with no new review
- m16: (c)'s `gh pr list` rule dropped
- m17: (c)'s `git branch -D` rule dropped
- m18: T5's "edit nothing" made "edit freely" (merge.md)
- m19: T5's clause dropped from the policy
- m20: T5's clause dropped from design.md's prompt
- m21: T5's clause dropped from the policy's copy of design.md's prompt, so the copy differs
- m22: T5's cache clause loosened (diff-reviewer.md)
- m23: T16 allows the suite beside a stage review
- m24: T16 dropped from merge.md
- m25: T25's turn budget dropped
- m26: T2's receipt check made lax
- m27: T2's design prompt back to "say so"
- m28: T2's clean reply names nothing (diff-reviewer.md)
- m29: the policy's failed launch back to "the round stays not run"
- m30: the directive back to four clauses

Five mutants change a sentence two tests pin, so each names both tests in `expect_fail` (corrected after the first mutation run, below): m7 also P7's test (it pins the whole paragraph), m10 also (c)'s (the remote-delete command), m20 also T2's (the same prompt), m23 also T25's (the same sentence), m27 also T5's (the policy's copy of the prompt no longer equals design.md's).

## Bookkeeping and records expected in the diff
- docs/REQUIREMENTS.md: R-045 and R-046 built, with Evidence per item label.
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009), and the six lines it replaces archived word for word in docs/archive/STATUS_HISTORY.md.
- project.json's stage.
- docs/INVENTORY.md: the module-size row and the build-phase modules' row.
- docs/HARDENING.md: a TASK-038 section with five leads, each outside this Scope or for a later increment: TASK-037's failed-launch lead, its policy half done here and KP-062's half open (0d97666); and Review A round 1's two Should fix and two Considers (9f6e372).

## Before this round
- Full suite with this pull request's variables, in P7's documented `--key-file` form (`GITHUB_REF=refs/pull/119/merge`, `GITHUB_BASE_REF=main`, `GITHUB_EVENT_NAME=pull_request`, from a file outside the Workspace), on 0d97666: 3,324 passed, 40 skipped, exit 0 (run/agent/TASK-038-suite.out, not in the diff). The launch ran with no prompt and no refusal. The later commit 9f6e372 changes only docs/HARDENING.md, which no test reads. CI runs the full suite on the pull request's head.
- trace-check: OK (424; 139 traced, 219, 0 dropped, 66 excused).
- Review A (diff-reviewer), round 1 on ca0ee2c...0d97666: APPROVE, Blocking 0, Should fix 2, Consider 11. Both Should fix and three Considers are recorded as HARDENING leads (9f6e372); the others need no change (T4's "every squash setting keeps" holds because a gated pull request carries two or more commits; `git branch -D main` is admitted and acceptable; the rest are notes).
- Checkpoint rerun with the mutants file as committed for the accept (`--checkpoint ca0ee2c`, run/agent/TASK-038-checkpoint4.out, not in the diff): the same sixteen failing, none `not run`, exit 0. The mutants file's later correction changed only `expect_fail` lists, not `new_tests`.
- Mutation run 1 on 9f6e372 (30 mutants, no duplicates cut, about 31 processes estimated): exit 3, 25 killed, 0 survived, 5 errors. Each error was a second pinning test failing beside the listed one (m7, m10, m20, m23, m27), so the mutants file was corrected, as above. Mutation run 2: exit 0, 30 killed (5 run, 25 kept kills), 0 survived, 0 not applied, 0 errors (run/agent/TASK-038-mutation.out and TASK-038-mutation2.out, not in the diff).

This is Review B's round 1, below the ceiling.
