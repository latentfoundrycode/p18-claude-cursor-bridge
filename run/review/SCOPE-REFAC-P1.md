# SCOPE - REFAC-P1 (stage P1's refactoring pass)

## What the branch is
Stage P1's refactoring pass (bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md): removing duplication with the same functionality, one gate pass for the whole branch, one squash. There is no `docs/CHANGES.md` in this project and no behaviour entry: a refactoring changes no behaviour. The question for the reviewers: **is this behaviour-preserving?**

The base is origin/main 6fb2eb9 (TASK-058, PR #161). Stage P1's own change is its four squash commits 77dbdf3 d6a6a00 4f4a9b3 6fb2eb9 (TASK-055 to TASK-058, PRs #158 to #161, consecutive on main from d211e33, the program release's design and plan, PR #157). jscpd 5.4.2 did not run (its launch was refused by the session's permission classifier); refactor-scout read the stage's change against the 400-line budget and named two candidates in the production lane and none in the tests lane, kept in run/supervisor/refactor-P1-candidates.md (gitignored) and recorded in docs/HARDENING.md, "Stage P1's refactoring pass". One brief, handoff/REFAC-007.md, took the first; the second is a recorded lead.

## Brief REFAC-007: Scope and Out of scope
Quoted from handoff/REFAC-007.md, whose whole text is in the diff:

> ## Scope
> Files and directories you may create or modify:
> - bridge/cursor-bridge/trace-check.py
> - bridge/cursor-bridge/MANIFEST.json
> - docs/CLI_REFERENCE.md
> - docs/cli-reference.json
> - docs/BUILDER_NOTES.md
> - handoff/REFAC-007-r1-report.md
>
> Do not modify anything else.

Its `## Out of scope` section names .env and secrets/; CI, pre-commit and `tools/`; the other docs/ and handoff/ files, docs/diagrams/ and docs/TRACE_MOVES.md included; every file under `tests/`; `VERSION`; everything under `run/`; the change logs; every other function of trace-check.py (`git_run`, `decode_git_bytes`, `is_instruction_md`, `slash`, `head_passage_norms` and `run_moves` apart from one line each under option b, the full mode's own `git ls-tree` reading, `build_parser`), the module docstring, and every other file under `bridge/`. Read it in the diff for its exact words.

## The commits
1. `REFAC-007: the brief (stage P1's refactoring pass)` (d078757), the brief.
2. `REFAC-007: one helper lists trace-check's instruction files from git` (4f9d73b), the builder (composer-2.5, exit 0), option (a) of the brief: `instruction_paths_from_git(root, git_args)` holds the body `instruction_paths_in_rev` and `changed_instruction_paths` each held; the two stay one-line wrappers passing their same argument lists, so their callers in the move mode (`head_passage_norms` and `run_moves`) are unchanged. MANIFEST.json regenerated. The command reference needed no change (no parser or docstring line moved). Evidence: scope-check "SCOPE CLEAN"; `refactor-check.py main --max-lines 400` "PURE", 30 changed lines; the builder's three trace test files "78 passed, 4 skipped" before and after; its assumptions list reads none.
3. `Records: stage P1's refactoring pass, as at PR #162's merge` (6d04f13): docs/HARDENING.md (the pass's section, with the leads), docs/INVENTORY.md (the jscpd row: chosen, not run), docs/PROJECT_STATUS.md written as at this pull request's merge (the project's rule, ISS-009).

## Evidence already taken
- Review A, refactoring mode: APPROVE, nothing blocking, nothing to fix. The helper's body is the removed body word for word but for `git_args`; both argument lists byte-identical to the originals at d078757, `--no-renames` kept; the counts of `"command failed"` 2 to 1, `cannot be read as UTF-8` 6 to 5, `proc.stdout.split(` 2 to 1; CRLF kept, `git diff --check` clean; the manifest's two lines only, the hash recomputed. Noted, none of the five: the report's first grep carries a `-- bridge/` pathspec the brief's command lacks (the reviewer's own grep over tests and tools found no caller); an uncaught exception from the listing would show one more traceback frame.
- Mutation (D1): TASK-057's mutants, the stage's only driver on trace-check.py, run again on 4f9d73b, cut none: every anchor found once (m6's, the diff argument list, now in its wrapper), "counts: run=13 cached=0 killed=13 survived=0 not applied=0 error=0 expected survive=0". The mutants file is under run/supervisor/ (gitignored).
- The full suite on 4f9d73b, through the launcher stripped: "5104 passed, 42 skipped in 1910.25s (0:31:50)", exit 0.

## Out of scope
- The scout's second candidate (the exit-2 lines repeated in `run_moves`) and the builder's two notes (the full mode's own listing; the listings' error branches untested): leads in docs/HARDENING.md, not taken.
- Stage P1's review, its demonstration and reflection, the field finding F7's design and plan revision, and stages P2 to P4 are later work, not this diff's defect.

## Threat model
docs/INVENTORY.md (Decisions) records ASVS level 2. trace-check.py reads the repository's own git history and instruction files through `git_run`, with the revisions given on its command line (a revision beginning with `-` refused before any git call, TASK-057). This change moves no boundary: the same git commands run with the same arguments on the same inputs.

## Tests the supervisor wrote, each with the paragraph it enforces
None new.

## Expected bookkeeping files in the diff
docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, handoff/REFAC-007.md, handoff/REFAC-007-r1-report.md, bridge/cursor-bridge/MANIFEST.json, and run/review/ (this file, the diff, the assumptions file).
