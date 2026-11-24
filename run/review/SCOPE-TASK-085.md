# SCOPE for TASK-085 (Review B, round 2)

TASK-085 runs the mutation engine on a project installed into its environment in editable form (R-106, C27): mutation-run.py starts the interpreter it will use once, in the run's environment with the copy as working folder, reads the import path it prints (repr, parsed by ast.literal_eval), maps every entry inside the Workspace (compared by normcase after realpath, the folder keeping its case) to the same folder of the copy and puts it on PYTHONPATH ahead of the copy's root; a mutants file may name such roots itself under import_roots (a list of strings, each relative, refused where absolute, leaving the Workspace, passing through a link, the walk failing closed, or naming no folder in the ordinary mode); the same roots serve the dotted module name and join the cache key; a module still loaded from the Workspace is refused by a line naming the module, the place, an editable install as the usual cause and import_roots; a Workspace entry ahead of every copy entry, or with no copy entry on the path, is refused by a line of its own; -P is passed to each interpreter the program starts for the copy on Python 3.11 and later. Branch task-085 from main 1f8fab2 (PR #204's merge). Three builder rounds (Review A rejected rounds 1 and 2, approved round 3). This is the review guard's second round for TASK-085: there is no Blocking class line.

Round cause: defect

What changed since round 1 (Review B approved round 1 at 74795072789e): CI's first run of PR #205 failed one test on Linux, tests/test_improve_mutation_editable.py::test_task085_workspace_reached_through_a_link_still_maps_its_entries, with mutation-run: mutants file must be run/supervisor/<id>-mutants.json (exit 2): the supervisor's test named the mutants file through the symbolic link, and on POSIX os.getcwd() returns the link's resolved folder, so mutants_file_ok (unchanged by this increment) refused the path as outside run/supervisor/. Commit 1e4058c names the file relative to the folder the program starts in (on Windows the run still goes through the junction; on POSIX from the real folder) and adds one sentence to docs/HARDENING.md, whose lead the next commit states exactly on Review A's word (a mutants file named by an absolute path through a symbolic link to the Workspace is refused on POSIX). The review files' removal commit before it (a1f9b56) changed nothing else. mutation-run.py is unchanged since round 1. Review A read the fix.

Where the increment ends: bridge/cursor-bridge/mutation-run.py, MANIFEST.json through its generator, the supervisor's acceptance tests (tests/test_improve_mutation_editable.py), the three briefs and reports under handoff/, docs/BUILDER_NOTES.md (two dated lines), and the records (docs/REQUIREMENTS.md R-106 built, docs/HARDENING.md, docs/PROJECT_STATUS.md). The leads recorded in docs/HARDENING.md under TASK-085, 1 to 10, and the POSIX symbolic-link lead in its proofs bullet, are not this diff's defects. On Python before 3.11 no -P exists and the interpreter's -m puts the copy's root first: accepted, the acceptance case skips there (HARDENING, as built). Later increments of the improvements release (TASK-086a and after) are not this diff.

Read the commit messages (git log, the full bodies): the acceptance commit carries the dispositioned assumption lists, also in run/review/ASSUMPTIONS-TASK-085-r2.md.

## The brief's Scope, quoted (handoff/TASK-085.md; rounds 2 and 3 the same list with their own report file)
- bridge/cursor-bridge/mutation-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_mutation_editable.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-085-r1-report.md (r2, r3: their own)
Limits: no new command-line option, environment variable or exit code; the acceptance file the supervisor's, never edited by the builder; MANIFEST only regenerated; the command reference only if the help text changes (it did not).

## The brief's Out of scope, quoted in short (handoff/TASK-085.md)
- .env and anything under secrets/; nothing under .github/.
- docs/ and handoff/ except the files the Scope names; docs/REQUIREMENTS.md, docs/HARDENING.md and docs/PROJECT_STATUS.md are the supervisor's records commit.
- Every other program under bridge/ (bridge_env.py included), every text under bridge/commands/, bridge/agents/, bridge/cursor-bridge/workflow/, CHANGELOG.md and VERSION.
- Every other test file; run/; the supervisor's mutants file.

## The threat model (docs/INVENTORY.md, Decisions)
The bridge's threat model as a whole: the agents run as the owner's Windows user, so the boundary is what the programs refuse, check and record. For this program (Features, "Mutation reruns that skip what is unchanged", and the Decisions rows on mutation-run.py): the mutants file is the supervisor's, under run/supervisor/, checked whole before anything runs; import_roots joins that check. The scratch project's code and its environment (its tests and conftest.py files, its modules, the environment's .pth files, finders and sitecustomize) are untrusted to the extent the existing refusals treat them: they run only in the copy, windowless and bounded; the interpreter probe's output is such data, parsed strictly, never executed, and can only add folders of the copy to the path. The resolution check stays the proof of where the code under test came from, exit 2. ASVS level 2.

## The supervisor's tests (tests/test_improve_mutation_editable.py, names R-106; 26 cases)
- Round 1's sixteen, committed before the first brief (6c92cf7), each naming the Done-when clause of docs/BUILD_PLAN.md TASK-085 it enforces.
- Added after the builder's round 1 (brief R4, R3, R5, R8; Review A round 1): null refused; a missing folder and a file refused in the ordinary mode; mapped roots ahead of a stale pkg/ at the copy's root (skips before 3.11); a dotted name under import_roots refusing a module resolving outside; the Workspace entry ahead of the copy refused by its own line; an SDK/Src layout keeping its case; the program started through a junction to the Workspace (fixed in 1e4058c for POSIX).
- Added after the builder's round 2 (round 2's correction 6; R12): a Workspace entry with no copy entry on the path refused; a script started by a project test still imports the module beside it.
- On the checkpoint 6c92cf7 all 26 fail; after the fix, locally, 26 passed.

## The mutants file (run/supervisor/TASK-085-mutants.json, written by run/supervisor/write_task085_mutants.py)
22 mutants over round 3's code; 21 killed, m22 (an lstat error other than a missing path passing the walk) expected to survive (HARDENING lead 4).

## Evidence
- Review A: rounds 1 and 2 REJECT, round 3 APPROVE; the link test's fix read by Review A.
- Review B round 1: APPROVE, no finding.
- The security audit of the whole increment: PASS, four advisories (HARDENING leads 5 to 8).
- The own-file run, stripped through the launcher: 344 passed, 2 skipped (symbolic-link privilege, the tests' own conditions).
- CI run 45410241206 on round 1's head: security floor passed; bridge programs on Linux 1 failed (the test above), 7426 passed, 69 skipped.
- The mutation sweep: run 2 counts run=3 cached=19 killed=21 survived=0 not applied=0 error=0 expected survive=1.

## Expected bookkeeping and records in the diff
handoff/TASK-085.md, TASK-085-r2.md, TASK-085-r3.md and their three reports, docs/BUILDER_NOTES.md, docs/REQUIREMENTS.md, docs/HARDENING.md, docs/PROJECT_STATUS.md (as at this pull request's merge), and run/review/ (these files).
