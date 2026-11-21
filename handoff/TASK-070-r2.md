---
record: brief
header: 1
id: "TASK-070"
round: 2
satisfies: [R-090]
scope: ["bridge/cursor-bridge/mutation-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-070-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-070 round 2: the baseline leaves the copy as it found it (R-090)

Round cause: defect - bridge/cursor-bridge/mutation-run.py:1628-1631 and 1665-1668, the baseline runs its tests in the scratch copy the mutants then run on, after the cache keys read that copy and before the mutant loop reads a mutated file's original bytes, so a baseline test that rewrites a file of the copy changes what the mutants run on, what is restored after each mutant, and what the cache records under a key computed from the bytes before the baseline (data integrity)

## Objective
This is round 2 of TASK-070. Round 1's code is accepted and committed; Review B's round 1 found the defect above. The supervisor's two new cases are at the end of `tests/test_program_mutation_baseline.py`, after the comment `# --- round 2: the baseline leaves the copy as it found it`, each named `test_r090_r2_...`. Make the one correction below, keep every test green, and edit nothing in the acceptance file. Round 1's brief, `handoff/TASK-070.md`, stays in force for everything this brief does not change: its rulings R1-R9, its Context, its Constraints.

Satisfies: R-090 - as round 1's brief.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-070-r2-report.md

Limits on these files: `mutation-run.py`, the one correction alone; `MANIFEST.json` only through its generator, as round 1 (`python tools/make-manifest.py`, then `git restore bridge/cursor-bridge/VERSION`). Every other file is read only, every test file among them (`tests/test_program_mutation_baseline.py` is the supervisor's; `tests/test_mutation_run.py` and `tests/test_mutation_run_supervisor.py` are not edited this round, for any reason). The help text and the docstring do not change, so the command reference is not regenerated.

## Out of scope
As round 1's brief. Nothing beyond the correction: no refactoring, no other finding (the supervisor records the rest in `docs/HARDENING.md`, among them its TASK-070 leads 1 to 6), no option, no environment variable, no new dependency. What a mutant's own test run does to the copy (it is restored only in the mutated file after each mutant, as before TASK-070) is unchanged.

## Correction
1. **The baseline leaves the copy as it found it (data integrity).** In `main()`'s ordinary mode, after `run_baselines` returns and before the first mutant is applied, every file the copy (`copy_root`) held when `mutant_keys` were computed holds again the bytes it held then, whatever the baseline's tests wrote: the mutated files, the test files and every other file `copy_tracked` put there. So each mutant's `originals[...]` are the bytes the key read, the mutant is applied to them, and its cache line is keyed by the bytes that ran. Put the copy back by building it again over itself with the calls that built it (`copy_tracked(workspace, copy_root, tracked_list, untracked)`, which overwrites every tracked file and every untracked entry and then removes bytecode), only when at least one baseline list ran and the mutant loop is about to run (not on exit 5, not after a baseline pytest that outlived its kill). Do not remove the copy folder itself (`shutil.rmtree(copy_root)` or the like): on Windows a process the baseline left behind may hold its working folder inside it, as `tests/test_mutation_run.py::test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out` arranges, and the removal would fail. If you find a cheaper way that meets the same sentence (every file the copy held put back to the bytes the keys read) and keeps every test green, you may use it and say why in the report. Files a baseline test adds that the copy did not hold may stay, as a mutant's run leaves them today. Cases: `test_r090_r2_baseline_that_rewrites_the_mutated_file_leaves_it_pristine` (a baseline test rewrites `mod.py`; today `m1: not applied (ran)`, exit 1) and `test_r090_r2_baseline_that_rewrites_a_test_file_leaves_it_pristine` (a baseline test rewrites its own test file so it cannot fail; today `m1: survived (ran)`, exit 1).

## Context
The two cases are red on round 1's code; the supervisor's run (stripped, `-k r2`): `2 failed, 13 deselected`, quoted in the commit that added them ("TASK-070 r2: Review B's finding as tests"). The places in `main()` as the file stands: `copy_tracked` at line 1623, the resolution check at 1627, `mutant_keys` at 1628, `uncached_test_lists` at 1629, `run_baselines` at 1630-1631, the still-alive branch at 1634-1641, exit 5 at 1642-1644, the mutant loop from 1645, the original bytes read at 1665-1668. Read `copy_tracked` (lines 568-589) before you use it again: it copies `.env` and the untracked entries too, and the copy it rebuilds must be the copy the keys read.

## Acceptance criteria
- [ ] Every test in `tests/test_program_mutation_baseline.py` passes (fifteen cases), unedited.
- [ ] Every test of round 1's Done list passes, unedited.
- [ ] The correction met, named in the report with its function and lines.
- [ ] `mutation-run.py` stays ASCII; every line added is ASCII.

## Constraints
Round 1's Constraints all stand. Mutations by hand, in process, each reverted, listed by label with the pytest summary line and the id of a test it made fail, else `not caught`: (H6) the copy not put back after the baseline (the correction removed); (H7) only the mutated files put back, not the test files. Command for both: `python -m pytest -p no:cacheprovider -q tests/test_program_mutation_baseline.py`. Prefer the smallest change.

## Done
Your report is `handoff/TASK-070-r2-report.md`, in round 1's form (files changed; summary; the correction with its function and lines; every command of round 1's Done list with its output, verbatim, in fenced blocks; the mutations H6 and H7; a last section headed exactly `Assumed, not verified`). It is ASCII only: no dash, quote or other character above 127. It names no computer path: `<Workspace>` for the repository folder, `<tmp>` for a temporary folder.

Run round 1's Done list (`handoff/TASK-070.md`, Done, commands 1-12), in order, from the Workspace root, after your last edit, each in the foreground, with no environment change; `python tools/dump-cli.py` is expected to change nothing, and `git status --short` then lists no file under `docs/`. Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
