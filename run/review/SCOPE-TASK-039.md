# SCOPE - TASK-039: rule 6, convergence and the ceiling's text; briefs, reports and the accept step (R-050, R-051; R-042 revised) (pull request #120)

Supervisor-authored governance text in release T's stage T1 (docs/BUILD_PLAN.md, "### TASK-039", `Author: supervisor.`). No builder ran, so there is no brief and no builder report. No program's behaviour changes.

The branch's commits, in order:
- c128706: the accept. The text of R-050 and R-051 in every home, R-042's convergence and membership sentences as revised, tests/test_release_t_ceiling.py, the rewritten convergence tests of tests/test_loop_text_pace.py, the pins re-taken, the trace entries, MANIFEST.
- 65c7601: records (R-050 and R-051 built; R-042's Evidence; the status file as at this pull request's merge; the inventory's size and Features rows; two HARDENING leads).
- 8a032b7, 432b3e8: Review A round 1's fixes and their records (below).
- e50f0a1, 64a95ff: the fixes of Review A's re-read and their records (below).
- 9975a34, 2cc444c: the fix of Review A's second re-read and its records (below).

## Scope (the plan's, quoted)
bridge/commands/supervisor.md (rule 6); bridge/cursor-bridge/Merge-Verification-Policy.md (the re-delegation paragraph's threat model, the convergence paragraph, the invocation's fifth clause); bridge/cursor-bridge/workflow/phases/delegation-loop/merge.md (step 8's convergence paragraph, the directive's clauses); bridge/cursor-bridge/workflow/phases/delegation-loop.md (steps 3b, 4 and 5 and the survival list: T15, T24, P6, P13); bridge/cursor-bridge/workflow/phases/delegation-loop/decide.md ("When to stop re-delegating", "The review ceiling", the Accept bullet: P1, P2, P3, T20, T18, T10); bridge/cursor-bridge/workflow/phases/reflection.md (step 7); bridge/agents/diff-reviewer.md; bridge/agents/security-auditor.md; bridge/agents/design-auditor.md (the five first, the threat model with the diff, P11's count check); bridge/agents/spec-packager.md (T21, P12, T13, P6); bridge/agents/secret-sentinel.md (T24, P6); bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_release_t_ceiling.py; tests/test_loop_text_pace.py (the `test_bug033_` and `test_r042_` convergence tests rewritten first, each red on the increment's checkpoint by the by-id run); tests/test_phase_modules_build.py; tests/test_phase_modules_close.py; tests/test_core_carve.py; tests/test_session_start.py; tests/test_b3_least_confident.py (pins re-taken)

Widened, each for a finding Review A raised: bridge/commands/supervisor.md's rule 36 (round 1, B2: it said two reviewers converging on one line is blocking, against P1), and bridge/cursor-bridge/workflow/phases/design.md's paraphrase of the convergence rule in its procedure (round 1, S4).

Out of scope: every other file. Release T's later increments (TASK-040 to TASK-045) are later work, not this diff's defect; in particular the stage close and the stage review (TASK-040), the `--strip` launch forms (TASK-041), and every program. invisible-check.py has no `--staged` option: the text runs it in its default form, which reads what a commit takes, and R-051's row records the deviation (docs/HARDENING.md, TASK-039).

## The project's threat model, as docs/INVENTORY.md's Decisions record it for what the diff changes
The inventory records one threat model, the session-start hook's: "a partial, mismatched or hand-edited install, not a hostile checker: workflow-check.py runs in the hook's process and could write to its output directly. Inside it, nothing the checker returns reaches the output except as an exact str matching its pattern; what lies outside it is docs/HARDENING.md's". This diff does not change the hook. None is recorded for anything this diff changes (governance text and tests), so the five blocking classes stand unbounded for every finding.

## What the text must do (the plan's Done when, in short)
R-050's sentences in every home the design's table names: P1 (two reviewers naming the same defect, one defect per fault, blocking where its content is of the five; a convergent finding of another class fixed by the next increment that edits its file or recorded), T20 (the recorded threat model bounds the five, given to the reviewers with the diff, read before P1 and P2), P2 (membership by reproduction on an ordinary layout; a security finding by reach of untrusted input), P3 (the class line confirmed against the round it lifted), T18 (the test-strength rule for a supervisor-authored increment). R-051's: T21, P11, P12, T10, T15, P13, T24 and P6, T13 in spec-packager.md, secret-sentinel.md, decide.md's Accept bullet, delegation-loop.md's steps 3b and 5 and survival list, and the three reviewers. R-042 as revised, built, its Evidence gaining the rewritten tests. The digest within its cap (rule 6's digest line is unchanged). The trace entries, the pins, MANIFEST.

## The tests the supervisor wrote first
tests/test_release_t_ceiling.py names R-050, R-051 and R-042. It enforces docs/REQUIREMENTS.md R-050 and R-051 and TASK-039's Done when, one test per item label:
- `test_r050_p1_one_defect_class_gated_in_every_home` (P1: rule 6, rule 36, both convergence paragraphs, the brake, the policy's re-delegation paragraph, reflection.md's step 7, design.md's paraphrase, the three reviewers)
- `test_r050_p2_membership_by_reproduction_on_an_ordinary_layout` (P2)
- `test_r050_p3_the_class_line_against_the_round_it_lifted` (P3: decide.md's class-line bullet, merge.md's sixth clause and SCOPE item, the policy's two statements, step 4, the three reviewers)
- `test_r050_t20_the_recorded_threat_model_bounds_the_five` (T20: the policy, the brake, both convergence paragraphs, rule 6 and its order, step 4, merge.md's first clause and SCOPE item, the policy's invocation, the three reviewers)
- `test_r050_t18_a_supervisor_authored_increment_takes_the_test_strength_rule` (T18, step 4)
- `test_r051_t21_printed_lines_verbatim_mutations_by_label_not_run` (T21, spec-packager.md)
- `test_r051_p11_every_count_quotes_its_line_and_the_reviewer_compares` (P11)
- `test_r051_p12_the_suite_once_after_the_last_edit_and_known_failures_named` (P12)
- `test_r051_t10_the_records_in_a_records_only_commit_after_the_accept` (T10)
- `test_r051_t15_the_rebuild_at_a_profile_switch` (T15, step 3b)
- `test_r051_p13_the_resume_reads_the_output_and_err_first` (P13, the survival list)
- `test_r051_t24_invisible_check_against_origin_main_in_the_sentinel` (T24)
- `test_r051_p6_invisible_check_before_every_commit_and_escapes_as_text` (P6)
- `test_r051_t13_the_briefs_non_ascii_characters_listed_before_the_checkpoint` (T13)

tests/test_loop_text_pace.py, rewritten first (R-042 as revised): `test_r042_the_convergence_rule_grades_certainty_never_class_in_both_homes`, `test_r042_rule_6_states_the_outcomes_and_the_programs`, `test_bug033_a_late_finding_two_reviewers_name_blocks_only_of_the_five_in_every_home` (renamed from `..._blocks_too_in_every_home`), and the pins of `test_r042_the_class_line_the_text_gives_is_the_one_the_programs_read`, `test_r042_step_8_commits_the_scope_file_before_the_round_named_snapshot` and `test_r042_the_policy_carries_the_ceiling_the_names_and_the_breach` re-taken.

Pins re-taken (exact equalities as before; scripts under run/supervisor/, not in the diff): tests/test_phase_modules_build.py (step 7's length and hash; the survival list's P13 item); tests/test_b3_least_confident.py (the excused sections' lengths and hashes, delegation-loop.md's "The reviewers" added); tests/test_core_carve.py (six NOTE lines; the TRACED line 138 / 214 / 0 dropped / 72 excused; the docstring's count and tail).

The mutants file is run/supervisor/TASK-039-mutants.json (gitignored, not in the diff). Every mutant runs the two test files above and names in `expect_fail` every test that pins the sentence it breaks; every `old` text occurs once in its file and no two mutants are alike (the builder script asserts both). 84 mutants:
- rule 6 and 36 (m01 to m06): P1's, P2's and T20's clauses dropped, the unbounded clause dropped, rule 36 and design.md's paraphrase put back to "two reviewers converging/naming ... is blocking";
- both convergence paragraphs (policy, merge), six each: the same line back, one fault dropped, the class gate at any grade, a recorded class made new, the threat-model sentence dropped, its unbounded clause dropped;
- the policy's re-delegation paragraph and the brake, five each: THREAT dropped, its unbounded clause dropped, "none recorded" widened back to the whole diff, the label deciding, the late convergent finding blocking of itself; the policy's two P3 statements and its invocation's threat model dropped;
- decide.md's class line: P3 dropped, P3's commit put back to the previous snapshot's tree; merge.md: the sixth clause's P3, the first clause's threat model, the SCOPE item's threat model dropped and unscoped, the SCOPE item's commit dropped and put back to the previous snapshot's head; reflection.md's arm (a) at any class;
- the three reviewers, seven each: the threat model optional, its unbounded clause dropped, the label deciding, the convergent finding blocking, P3 against the fixed code, P3's commit in the SCOPE file only, the count unchecked;
- delegation-loop.md: step 4's threat model and class line not given, T18 dropped and its kill unjudged, T15 dropped and the launcher silent, P13's verify at any time and with no wait, T24's base dropped in step 5 and in secret-sentinel.md, P6's `--staged` put back;
- spec-packager.md: P6's shell escapes, T13 by name, T21 in summary, by the packager's own name and described as run, P11's bare count, P12's suite after each edit, the tree assumed clean and the known failures unnamed;
- decide.md's Accept bullet: P11's counts summarised, T10's same commit and the change log in the accept.

## Bookkeeping and records expected in the diff
- docs/REQUIREMENTS.md: R-050 and R-051 built, with Evidence per item label; R-042's Evidence; the as-built notes of Review A's rounds (R-050, R-042) and R-051's deviation note.
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009), the six lines it replaces archived word for word in docs/archive/STATUS_HISTORY.md; project.json's stage.
- docs/INVENTORY.md: the module-size row (TASK-038's core size corrected to 100,701, Review B's round-2 Should fix on PR #119; the sizes after TASK-039's accept) and the loop-text Features row.
- docs/HARDENING.md: a TASK-039 section with seven leads (invisible-check's missing `--staged`; the project's one recorded threat model; Review A's declined Considers C1, C3, C5, C7; the stage round's class line with no commit).

## Before this round
- New tests against the checkpoint d39dcfd (`mutation-run.py --checkpoint`, run/agent/TASK-039-checkpoint.out, not in the diff): exit 0, 20 failing, none `not run`. The rerun after the fixes is below.
- Review A (diff-reviewer), round 1 on d39dcfd...65c7601: REJECT, before this snapshot (a fix the supervisor makes and Review A re-reads before step 8's snapshot is no round). Taken: B1 (T20's bound unscoped: it bounds the parts the model names, the five unbounded where none is recorded), B2 (rule 36), S1 (step 4 gives Review A and the auditors the threat model), S2 (P3's tree), S3 and C6 (spec-packager's suite sentence conditional; whether the tree held changes), S4 (design.md's paraphrase), S5 (R-051's `--staged`, a deviation note), C2 (P6's test pins text only), C4 (rule 6 reads the threat model first). Declined to HARDENING: C1, C3, C5, C7. Fixed in 8a032b7, records 432b3e8.
- Review A's re-read of 8a032b7: REJECT. Taken: B1 (P3's commit had been the previous snapshot's head, wrong when a Review A rejection came between; now the commit the lifted round's builder was launched on, its brief's commit, the previous snapshot's head only for a round of the supervisor's own fix with no builder run), S1 (step 4 tells Review A and the auditors the round is at or above the ceiling and gives the class line with its commit), C1 (the SCOPE item's threat model for what the diff changes), C2 ("none recorded" for the part a finding is in, in every home). Fixed in e50f0a1, records 64a95ff.
- Review A's second re-read of e50f0a1: APPROVE, one Should fix taken (the brief cannot hold the commit it is committed in: the commit is named at step 4 and in the SCOPE file, the brief carrying the line alone; 9975a34), two Considers taken in records (2cc444c).
- Review A's look at 9975a34 and 2cc444c: APPROVE, no Blocking, no Should fix. One Consider declined: step 4's "the commit beside it" relies on its pointer to step 7, which names the commit; correct as written.
- Full suite with this pull request's variables in P7's `--key-file` form (`GITHUB_REF=refs/pull/120/merge`, `GITHUB_BASE_REF=main`, `GITHUB_EVENT_NAME=pull_request`, from a file outside the Workspace), on 64a95ff: 3342 passed, 40 skipped in 1533.98s, exit 0 (run/agent/TASK-039-suite.out, not in the diff). 9975a34 changes one phrase of decide.md and its three pins; the increment's test files ran after it (275 passed), with tests/test_install_check.py and tests/test_release_b_stamp.py for the manifest (21 passed). CI runs the full suite on the pull request's head.
- trace-check: RESULT: OK; TRACED: 424 passages of baseline 0a186da; 138 in supervisor.md, 214 under workflow/, 0 dropped, 72 excused.
- Mutation run on 2cc444c (84 mutants, no duplicates cut, one tests list with no launch site, about 85 processes estimated): exit 0, "counts: run=84 cached=0 killed=84 survived=0 not applied=0 error=0 expected survive=0" (run/agent/TASK-039-mutation.out, not in the diff).
- New tests against the checkpoint d39dcfd, rerun with the tests as they now stand (`--checkpoint d39dcfd`, run/agent/TASK-039-checkpoint2.out, not in the diff): exit 0, all 20 listed tests `failing`, none `not run`.

This is Review B's round 1, below the ceiling (the guard's count is 0).
