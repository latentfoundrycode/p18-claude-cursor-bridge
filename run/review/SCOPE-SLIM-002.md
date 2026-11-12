# SCOPE: SLIM-002, release S (2 of 3), the retirements

Pull request #153, branch `slim-002`, base `origin/main` at 22dc72d (the squash of #152). The diff is `run/review/REVIEW-SLIM-002-r1.diff`, taken from committed state. There was no builder and no handoff brief: the bridge's maintainer wrote this diff in a separate clone, on the owner's word of 2026-11-11, to the terms of the pace audit of 2026-11-09 (S1) and the agreement with the bridge's supervisor of 2026-11-10. This file stands in for the brief's Scope and Out of scope.

**The owner's approval of the list, by file and count:** given on 2026-11-12 in the maintainer's chat, after the list by kind and count, what stays, what is given up and why the tests had been written were put to them: "I see. Then I approve of your recommendation to drop them." It is recorded in the pull request's description in the same words. It is the owner's decision on the release's terms, not a reviewer's question: a reviewer judges whether each retired test is of the kind the terms name.

## Scope (what this pull request is to do)

1. **Retire 48 test functions (185 collected cases)**, and nothing else of the tests' behaviour: size and hash pins of instruction text (6 functions, 122 cases), per-file size caps (5, 18), prose-literal tests (34, 42), record pins (3, 3). The suite goes from 5,289 collected cases on `origin/main` to 5,104. Kept on purpose: the digest's 9,500-character cap, every value the owner chose, every line a program parses, the two word budgets #152 added (`tests/test_release_s_budgets.py`).

   By file (functions / cases): `tests/test_b3_least_confident.py` 2 / 109; `tests/test_phase_modules_close.py` 4 / 17; `tests/test_phase_modules_build.py` 4 / 11; `tests/test_phase_modules_intake_design.py` 2 / 4; `tests/test_phase_modules_interface_planning.py` 2 / 8; `tests/test_core_carve.py` 1 / 1; `tests/test_trace_full_split.py` 1 / 1; `tests/test_bug043.py` 2 / 2; `tests/test_a5_followups.py` 1 / 1; `tests/test_bug040.py` 3 / 3; `tests/test_hotfix_intake.py` 1 / 1; `tests/test_leads_b3.py` 2 / 2; `tests/test_loop_text_pace.py` 13 / 15; `tests/test_release_t_ceiling.py` 6 / 6; `tests/test_release_t_merge.py` 1 / 1; `tests/test_release_t_stage_close.py` 2 / 2; `tests/test_workflow_model.py` 1 / 1. The names are listed in this pull request's description and in the changelog entry the third pull request carries.
2. **What stays of a touched function.** `tests/test_core_carve.py::test_r003_the_carve_traces_with_exactly_its_excuses` keeps its run of `trace-check.py` (exit 0, `RESULT: OK`, `0 dropped`) and loses the pinned count line and the list of notes. `tests/test_bug040.py`'s fourth literal of R-045's Evidence now names `test_bug040_b1_the_lift_line_reads_as_the_behaviour_class`. The helper `assert_survival_list` (`tests/phase_modules.py`) goes with its last caller.
3. **The register's Evidence cells for the labels whose tests are retired** (`docs/REQUIREMENTS.md`; the grammar test asks one entry per label): R-042 (P2, the revision's entry), R-045 (P7), R-049 (T11, P17), R-050 (P1, P2, P3, T20), R-051 (P12, T10) take the text form #152 added, `text: <file>.md :: <heading> (#<pull request>)`, each naming an already merged pull request whose squash changed the file (#119, #120, #121); R-047 (T1), R-004 and R-026 are reworded where they named a retired test. R-032's sentence is revised in place, with its history: 8,000 words per step file and 150,000 words for the rulebook replace 1,500 lines and 60,000 characters, which the retired caps held.
4. **The declaration the text form needs**: `project.json` gains `"instruction_texts": ["bridge/"]`.
5. **The grammar test reads the text form**: `tests/test_release_t_stamp.py::test_r056_every_row_is_built_with_evidence_in_the_grammar` accepts, for a label, an entry that names a test or one `completion-check.py`'s `TEXT_EVIDENCE` reads.

## Out of scope (not this diff's defect)

- The instruction texts themselves and the assertions that leave eleven further functions with them: the third pull request.
- The register's sentences for rules the third pull request's texts remove (R-045's P7 clause, R-051's P12 sentence, R-049's and R-050's stage lift): the supervisor's records, revised by the supervisor after calibration (the handover agreed on 2026-11-10). Until then their text entries name a heading whose text still states the rule on this base.
- Any program. No file under `bridge/` changes.
- Design for later releases.

## Threat model

The diff changes no program and no gate. The register is read by `completion-check.py`: a text entry counts only in a project that declares its instruction texts, under a declared folder, for a heading outside a code block, with the pull request's squash on `origin/main` having changed the file, never for a row whose sentence names a program (#152). For the five blocking classes: a retired test that was the only thing holding a behaviour of a program, an owner's value or a program-parsed line is a finding of the class "defeated safety mechanism"; a retired test that held wording, a size or a hash of instruction text is the release's purpose.

## What Review A found (two fresh readers, the diff reviewer and the security auditor; both APPROVE, nothing blocking)

- Each retired assertion that touched a program's behaviour, an owner's value or a program-parsed line has a kept test, named by the readers after running it: the lift line (`tests/test_bug040.py::test_bug040_b1_the_lift_line_reads_as_the_behaviour_class`), the class-line grammar, the five classes and the ceiling figure (`tests/test_loop_text_pace.py`), the guard's input names (`tests/test_loop_text_pace.py`), the stripped launch (`tests/test_release_t_floor.py`), `stage-diff.py` (`tests/test_hotfix25a_stage_records_install.py`), the digest's cap (`tests/test_loop_text_pace.py`).
- Advisories taken in this diff: four test files' docstrings say what was retired; R-049's T11 names the test that runs `stage-diff.py` beside its text entry; R-042's revision entry no longer names a test file that holds none of its labels.
- Advisories recorded, not this diff's (leads for the supervisor's HARDENING, in the maintainer's handover message): with the hash pins and the notes list gone, a passage deleted under a section a trace exception already excuses (the Standing rules among them) shows only in the excused count, with `RESULT: OK`: a reviewer's read, as the release's terms say (the retired pins ran only where the baseline commit is present, never in CI's shallow checkout); the phrase "Fix the following confirmed defect", shared by three instruction files and read by reviewers only, is held by no test; `project.json`'s `bridge/` also lets a text entry cite the changelog and the vendored `.md` files, all still full-gate files, no program file; R-042's P2 and R-051's P12 and T10 have a text entry only in rows that name a program, where it counts as zero and the row stands on its other tests.

## Tests, each with what it enforces

No new test. Kept and run: `tests/test_release_t_stamp.py` (the register's grammar and `completion-check.py --mode done` on this repository), `tests/test_release_s_budgets.py` (the two budgets), `tests/test_release_s_evidence.py` (the text form). No mutants file and no mutation driver.

## Counts

- On this branch, the 21 touched and bearing test files with the pull-request variables: `242 passed in 42.98s`. Collected: `5104 tests collected`. After the advisory edits, ten bearing files: `129 passed in 51.25s`.
- `completion-check.py --mode done` on this branch: `RESULT: OK` (63 built, 2 deferred).
- The whole suite on the prepared change, once, in the preparation clone on an earlier base (before #152's later rounds): `5019 passed, 46 skipped in 2065.11s (0:34:25)`. On this head the whole suite is CI's run of the pull request.

## Expected bookkeeping and records in the diff

- `docs/REQUIREMENTS.md` (item 3), `project.json` (item 4).
- `docs/PROJECT_STATUS.md`: one line, `Last accepted:`, names this pull request first, which `tests/test_release_b_bootstrap.py::test_r001_status_names_its_own_merge` requires of every pull request into main until the third pull request retires the line.
- `run/review/` (this file, the diff, the assumptions file), removed before the merge.
