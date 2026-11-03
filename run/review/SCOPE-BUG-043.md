# SCOPE - BUG-043: the increment's own test files run stripped, and the claim says what the flag withholds (pull request #132)

A fix of a confirmed defect in the loop's text, found by stage T2's review, round 2 (Review A's bridge part, its B1, a REJECT, graded security; Review B silent). The confirmed cause and its evidence are `docs/debug/BUG-043.md`. It is the supervisor's text and tests with no builder round, so there is no brief: `bridge-run.py` has logged no builder run for this ID, and no program changes in this diff. Your question: does this repair the named cause at the named mechanism, or does it make the symptom disappear? It is also the fix increment of a stage review: below the ceiling, arm (a), the stage's round 3 reads the new whole change after this merges, so stage-wide design is not this diff's question.

The branch's commits, in order:
- c29b649, e599e70: the first text and its records.
- 9ae43ee, 4c547a2: the second text and its records, after Review A's and the audit's first rejections.
- 664cb27, 2abcc07: the third text and its records, after their second rejections.
- 01461e9, 8bf976f: the third text's corrections, and the row's limit split from the act, after their third rejections.
- ec6d4b7: the last wording, after Review A's APPROVE and the audit's PASS on 8bf976f.
- 27fe45c: the proofs and the reviews, in the records.
- 6aaa8e3: three section pins in `tests/test_b3_least_confident.py`, which the first full suite found (below).
- this round's review files, committed last.

## Scope
No brief, so nothing to quote. What the fix changes: `bridge/cursor-bridge/workflow/phases/delegation-loop.md` (a new paragraph at the head of step 4; the suite sentence; the paragraph on the increment's own test files; the survival list), `bridge/agents/test-runner.md`, `bridge/cursor-bridge/workflow/trace-exceptions.md` (one `new` entry for step 4), `bridge/cursor-bridge/MANIFEST.json` (regenerated, version unchanged).

## Out of scope
Every program under `bridge/cursor-bridge/`: none changes, on purpose; the launcher's comparison before and after a run, a refusal of a home variable in a key file, the launcher's 125 message and the secret-like name test's gaps are program items for the next program release, named at `docs/BUILD_PLAN.md`'s TASK-045. `bridge/cursor-bridge/VERSION` and `CHANGELOG.md`: TASK-045, the stamp. `.github/workflows/`. The stage's round 3. The text applies only from release T's install: this session runs the installed text, so the launches here ran as that text states them, unstripped (P10, INVENTORY Decisions).

## Beyond the fix's own lines: read it as you read the code
**Stated limits to check, you may disagree (rule 58, the owner told).** The fix does not close the whole exposure. Whatever else runs what a builder wrote on this computer runs in a session's own environment, stated as a class in step 4, `docs/DESIGN.md`, D-004 and INVENTORY's row "The strip reaches only what goes through the launcher". A stripped test can still write the checkout's `.git`, so that the next git command of the session runs its program with the owner's login: step 4's read of `.git/config` and the hooks folders is a check, not a boundary. Is any limit stated falsely, or is a limit stated where the text could close it?

**The carried findings, each its own cause, from the same round (Review A's records part):** R-042's Evidence gains a `P2:` entry, which TASK-045's stamp test reads; DESIGN's `--mode code` sentence and R-052's homes; the inventory's trace series.

## The project's threat model, as docs/INVENTORY.md's Decisions record it
The strip row, the last Decisions row, recorded for R-050, with the guard's row before it (KP-032): the strip withholds what a run is handed, never what it can reach on purpose. That neither the strip nor the loop's text can stop a run writing the checkout's `.git`, or asking the credential store, is a stated limit, no blocking finding by itself; the launcher's comparison is a program item. The act is not the limit: code in a diff that writes the checkout's `.git` or asks the credential store for the owner's login, or a line step 4's check finds, is a gate-integrity flag and a security finding. The agents run as the owner's Windows user: not a sandbox.

## The tests the supervisor wrote first
`tests/test_bug043.py`, 11 test functions, its module docstring naming the paragraph (docs/debug/BUG-043.md; docs/REQUIREMENTS.md R-052, R-042). Reproduction, red on 603b2d4: `test_bug043_the_loop_runs_the_increment_s_own_files_through_the_launcher`, `test_bug043_the_test_runner_reads_their_file`, `test_bug043_the_claim_says_what_the_flag_withholds`, `test_bug043_every_home_states_a_class_not_a_count`, `test_bug043_step_4_reads_the_git_config_as_a_file_first`, `test_bug043_every_home_states_what_the_strip_does_not_stop`. Negative cases: `test_bug043_negative_the_own_file_launch_runs_on_the_heavy_launch_rules`, `test_bug043_negative_a_stripped_launch_of_one_test_file_gets_no_account_key` (a real launch through the launcher, with a control arm without `--strip`). The carried findings: `test_bug043_r042_names_its_p2_entry`, `test_bug043_the_design_is_past_the_retrofit`, `test_bug043_the_inventory_keeps_the_trace_series`.

Other tests changed, each pinning text this diff moved: `tests/test_allowlist.py` (the documented strip launches, four to five, the new one being the own-file launch), `tests/test_loop_text_windowless.py`, `tests/test_phase_modules_build.py` (the survival list), `tests/test_release_t_floor.py` (the suite's sentence), `tests/test_b3_least_confident.py` (the two excused sections the text moved, re-taken, and the new one, step 4, pinned). Read each for a weakening.

The mutants file is run/supervisor/BUG-043-mutants.json (gitignored, not in the diff): 53 mutants, none alike, each a named weakening, written by the supervisor, on text, with `pairs` of `old` and `new`.

## Bookkeeping and records expected in the diff
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009), the lines it replaces archived in docs/archive/STATUS_HISTORY.md. project.json does not change.
- docs/debug/BUG-043.md; docs/REQUIREMENTS.md R-042's `P2:` entry, R-050's as-built note, R-052's clause.
- docs/INVENTORY.md: Features rows 25, 31 (the trace series) and 46, Decisions row 162, the new row 172.
- docs/DESIGN.md (the limits, the homes, the retrofit's tense) and docs/BUILD_PLAN.md (TASK-045's program items).
- docs/diagrams/D-004-context-dfd.md: the note, the table, the key-file edge, the supervisor's edge, the dotted `p_test_suite` write edge and the reach to the credential store.
- docs/HARDENING.md: stage T2's review round 2, BUG-043's section, the leads not taken.
- run/review/: this round's files.

## Before this round
- New tests against the checkpoint (`mutation-run.py --checkpoint`, not in the diff), against 603b2d4 each time: run/agent/BUG-043-r1-checkpoint.out seven failing, then after each read six, seven and seven (`-r2-`, `-r3-`, `-r4-`), exit 0.
- Review A (fix mode) and the security audit read four texts. Both rejected the first three (a count disproved by its next sentence; an absolute against `# wake` and the key file; the row filing the act under the limit); Review A APPROVE and the audit PASS on the fourth, reading the delta 2abcc07..8bf976f, their last notes taken in ec6d4b7, reviewed by neither since. HARDENING has each.
- Mutation runs on the code as it stands at 6aaa8e3 (not in the diff), cuts none: BUG-043 "counts: run=53 cached=0 killed=53 survived=0 not applied=0 error=0 expected survive=0"; TASK-041 "counts: run=47 cached=0 killed=47 survived=0 not applied=0 error=0 expected survive=0". Estimate for BUG-043's: about 266 processes. Both ran first at 27fe45c with the same counts; the pins invalidated those kills, so they ran again. Every driver's mutants applied at ec6d4b7, 282 of 282.
- P7's suite, with the pull request's variables (not in the diff): on 27fe45c "3 failed, 3541 passed, 41 skipped", exit 1, all three `tests/test_b3_least_confident.py`'s pins, which no focused run had named; on 6aaa8e3 (run/agent/BUG-043-suite.out) "3545 passed, 41 skipped in 1708.64s", exit 0; no skip names tests/test_bug043.py. The local suite runs unstripped until the install (P10), so `tests/test_release_t_strip.py`'s environment test skips here.

## The round
The guard's count is 0 before this snapshot and 1 once it opens, so this is Review B's first read. The launcher's count of builder rounds is 0. This round is below the ceiling; grade every finding by the five blocking classes all the same (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test), and say for each which class it is or that it is none. Judge a security finding by whether untrusted input, files a builder or reviewer writes, can reach it, and by the threat model above: the limit itself is recorded, so name a sentence that states a limit falsely, not the limit again.

Never run review-guard.py snapshot, verify or premerge in this Workspace itself: each on a temporary git repository, as tests/test_bug039.py does. Make any export in a NEW folder from tempfile.mkdtemp, never a fixed name, and remove only what you made, by exact path and never by a glob. Write no file under the checkout and point no cache there.
