# Assumptions, TASK-072

The builders' `Assumed, not verified` lists (handoff/TASK-072-r1-report.md, handoff/TASK-072-r2-report.md, handoff/TASK-072-r3-report.md) and the supervisor's, each with its disposition. Extra places to look, never the review's scope.

## Round 1
- Several scheduled workflows that differ from the gate: the detail names the first in glob order -> accepted.
- An OSV-Scanner workflow with neither push, pull_request nor schedule (release only) reads the `has no schedule:` MISSING, which loses to a differing scheduled workflow -> accepted.
- A .git file is read for its gitdir: line -> the B1 defect (a path with a space cut at the space), fixed in round 2, held by test_r2_a_git_dir_whose_path_holds_a_space_is_read.
- `Weekly scan:` matched case-sensitively, the first Decisions row in table order quoted -> accepted.
- A remote URL is GitHub's when its host is github.com or ends .github.com, case-insensitive, in the URL and the scp-like form -> accepted.
- A top-level on: as a flow mapping or a block scalar reads no trigger -> accepted (HARDENING, TASK-072 lead 3).

## Round 2
- `"on" :` with a space before the colon is not read -> accepted.
- The first `gitdir:` line in the .git file is used, wherever it stands -> accepted (HARDENING lead 8: git requires it first; git's failure then reads as no remote).
- The four two-slash prefixes (`//`, `\\`, `/\`, `\/`) are refused as a network path, with no test -> accepted, read by both reviewers in the code.

## Round 3
- `stat.FILE_ATTRIBUTE_REPARSE_POINT` exists only on Windows, so it is read with getattr -> wrong: Lib/stat.py defines it on every platform (line 184); the guard is harmless; the comment and the notes line recorded (HARDENING lead 10).
- A relative `gitdir:` value is joined to the Workspace and its last component checked -> accepted, untested (HARDENING lead 12).

## The supervisor's
- An empty gate set equals an empty weekly set, so steps using the `--lockfile` space form or `-L` read OK -> accepted, the brief's `--lockfile=` reading (HARDENING lead 1; the configurator writes the `=` form).
- A workflow triggered by both push and schedule counts as gate and weekly -> accepted, ruling 2's letter (HARDENING lead 2).
- Each of --local, --no-includes and the GIT_CONFIG* withholding is redundant alone on git 2.53 -> accepted, kept as defence in depth; the mutants drop the three together.
- Every reparse point, not only links and junctions, reads as no git folder -> accepted, the brief's choice (HARDENING lead 11: a OneDrive placeholder would read NOTE).
