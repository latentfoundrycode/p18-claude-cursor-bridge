---
record: brief
header: 1
id: "TASK-070"
round: 3
satisfies: [R-090]
scope: ["bridge/cursor-bridge/mutation-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-070-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-070 round 3: the baseline runs in a copy of its own (R-090)

Round cause: defect - bridge/cursor-bridge/mutation-run.py:1645-1646 with copy_tracked at 568-589, round 2's rebuild of the mutants' copy over itself after the baselines cannot undo every change a baseline test makes to that copy: a tracked file a baseline test replaced with a folder of the same name gets the original copied inside the folder, so the mutant's recorded id no longer matches and the run reads `error (expected id absent)`, exit 3, under the key of the bytes before the baseline; a file a baseline test adds stays and changes what the mutants run (data integrity)

## Objective
This is round 3 of TASK-070, the review ceiling's round. Rounds 1 and 2 are accepted and committed; Review B's round 2 found the defect above. The fix is a change of place, not a better rebuild: the baselines run in a scratch copy of their own, so the copy the cache keys read and the mutants run on is never touched by a baseline test. Round 2's rebuild goes. The supervisor's two new cases are at the end of `tests/test_program_mutation_baseline.py`, after the comment `# --- round 3: the baseline runs in a copy of its own`, each named `test_r090_r3_...`; the supervisor also moved one Windows assertion of `tests/test_mutation_run.py::test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out` from the mutants' copy to the baseline copy (Context). Make the one correction below, keep every test green, and edit no test file. Round 1's brief, `handoff/TASK-070.md`, and round 2's, `handoff/TASK-070-r2.md`, stay in force for everything this brief does not change.

Satisfies: R-090 - as round 1's brief.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-070-r3-report.md

Limits on these files: `mutation-run.py`, the one correction alone; `MANIFEST.json` only through its generator, as round 1 (`python tools/make-manifest.py`, then `git restore bridge/cursor-bridge/VERSION`). Every other file is read only, every test file among them. The help text and the docstring do not change, so the command reference is not regenerated.

## Out of scope
As round 1's brief. Nothing beyond the correction: no refactoring, no other finding (the supervisor records the rest in `docs/HARDENING.md` under TASK-070), no option, no environment variable, no new dependency. What a mutant's own test run does to the mutants' copy is unchanged.

## Correction
1. **The baseline runs in a copy of its own (data integrity).** In `main()`'s ordinary mode, when `base_lists` (line 1629) is not empty, build a second copy of the Workspace at `os.path.join(work_sub, "base")`, exactly as the mutants' copy is built at line 1623 (`copy_tracked(workspace, <that folder>, tracked_list, untracked)`, after creating the folder), and pass that folder to `run_baselines` in place of `copy_root`. The folder's name is `base`, directly under `work_sub`: the supervisor's moved assertion names it. When `base_lists` is empty, build no such copy. Remove round 2's rebuild (`elif base_lists: copy_tracked(workspace, copy_root, tracked_list, untracked)`, lines 1645-1646). Nothing writes into `copy_root` between line 1623 and the mutant loop except what did before TASK-070 (the resolution check). Do not remove the baseline copy before the `finally` that removes `work_sub` (lines 1734-1736): on Windows a process a baseline test left may hold its working folder there, and that `finally` already removes what it can with `ignore_errors=True`. Every other rule of rounds 1 and 2 stands: the lists, their order, the limit and environment of each run, exit 5, the timed-out and the still-alive handling, the results files under `work_sub`. Cases: `test_r090_r3_baseline_that_replaces_a_test_file_with_a_folder_leaves_the_mutants_copy_alone` (on round 2's code `m1: error (expected id absent) (ran)`, exit 3), `test_r090_r3_baseline_that_adds_a_conftest_leaves_the_mutants_copy_alone` (on round 2's code `m1: survived (ran)`, exit 1), round 2's two `test_r090_r2_...` cases, and `tests/test_mutation_run.py::test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out` (on round 2's code its moved assertion fails: no `base` folder).

## Context
The supervisor's run of the three cases on round 2's code (stripped, `-k "r3 or pipe_holder_outside_tree"`): `3 failed, 84 deselected`, quoted in the commit that added them ("TASK-070 r3: Review B's round 2 finding as tests"). The moved assertion: on Windows, the test used to assert that `work_sub / "tree"` stays while the holder lives, because the holder's working folder was the folder pytest ran in, the mutants' copy, where the timed-out baseline ran. With the baseline in its own copy, the holder's working folder is the baseline copy, so the assertion now reads `assert (work_sub / "base").is_dir()`; the test's other assertions are unchanged (`work_sub` stays, the copied `.env` under `tree` is gone, exit 3, `phc: error (timed out)`, no `internal error`). The places in `main()` as the file stands: `copy_tracked` at line 1623, the resolution check at 1627, `mutant_keys` at 1628, `uncached_test_lists` at 1629, `run_baselines` at 1630-1631, round 2's rebuild at 1645-1646, the `finally` at 1734-1736.

## Acceptance criteria
- [ ] Every test in `tests/test_program_mutation_baseline.py` passes (seventeen cases), unedited.
- [ ] Every test of round 1's Done list passes, unedited, `test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out` among them.
- [ ] The correction met, named in the report with its function and lines; round 2's rebuild gone.
- [ ] `mutation-run.py` stays ASCII; every line added is ASCII.

## Constraints
Round 1's Constraints all stand. Mutations by hand, in process, each reverted, listed by label with the pytest summary line and the id of a test it made fail, else `not caught`: (H8) the baselines run in `copy_root` again (the baseline copy built but not used); (H9) the baseline copy built only from the tracked files, without `.env` and the untracked entries. Command for both: `python -m pytest -p no:cacheprovider -q tests/test_program_mutation_baseline.py`. Prefer the smallest change.

## Done
Your report is `handoff/TASK-070-r3-report.md`, in round 1's form (files changed; summary; the correction with its function and lines; every command of round 1's Done list with its output, verbatim, in fenced blocks; the mutations H8 and H9; a last section headed exactly `Assumed, not verified`). It is ASCII only: no dash, quote or other character above 127. It names no computer path: `<Workspace>` for the repository folder, `<tmp>` for a temporary folder.

Run round 1's Done list (`handoff/TASK-070.md`, Done, commands 1-12), in order, from the Workspace root, after your last edit, each in the foreground, with no environment change; `python tools/dump-cli.py` is expected to change nothing, and `git status --short` then lists no file under `docs/` but `docs/BUILDER_NOTES.md` if you wrote a line there. Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
