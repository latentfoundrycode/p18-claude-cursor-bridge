# SCOPE of TASK-086a (R-107): the roster resolves an alternate reviewer

Blocking class: behaviour - Review A, round 3, B1

The round it lifted is round 4. Its builder was launched on 06461af, the commit of its brief handoff/TASK-086a-r4.md. Confirm or deny this line against round 3's code as that builder found it (06461af's bridge/cursor-bridge/roster-check.py, the probe block at lines 1384 to 1422), never against the fixed code under review.

## Where the increment ends

TASK-086a is the resolve's half of R-107: `roster-check.py` reads the families that built the branch from the launcher's run record (`built_families`), applies C39's table (docs/DESIGN.md, C39, about lines 596 to 611), resolves `review_b_alt` with a `deviation`, prints the REBUILD with its end form, adds `--repair-record` and `--review-alt <reason>`. The launcher's two review refusals, passing the roster and its profiles to `built_families`, and `roster_models` naming `review_b_alt` are TASK-086b's, the next increment: their absence here is not this diff's defect. R-107 stays planned until TASK-086b.

## The brief's Scope (round 1, handoff/TASK-086a.md; rounds 2 to 4 the same, with the round's own report file)

Files and directories you may create or modify:
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_roster_alt.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-086a-r1-report.md (and -r2-, -r3-, -r4-report.md in their rounds)

Limits on these paths:
- `bridge/cursor-bridge/roster-check.py`: Requirements 1 to 16 below; nothing else in it changes.
- `tests/test_improve_roster_alt.py`: the supervisor's acceptance tests, committed before the checkpoint. It is listed so the scope check reads it as part of the increment; read it whole and run it. Do not edit it.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`, never by hand. `bridge/cursor-bridge/VERSION` is outside Scope.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py`, never by hand.
- `docs/BUILDER_NOTES.md`: only by appending a dated line at its end.

Do not modify anything else.

## The brief's Out of scope (round 1)

- .env and anything under secrets/
- CI configuration: nothing under `.github/`.
- docs/ and handoff/, except the files the Scope section names. `docs/REQUIREMENTS.md`, `docs/HARDENING.md`, `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md` (its threat-model row on the reviewer's independence included) are the supervisor's records commit; `docs/DESIGN.md`, `docs/BUILD_PLAN.md` and `docs/diagrams/` are read, never edited.
- `bridge/cursor-bridge/bridge-run.py` (TASK-086b's), `bridge/cursor-bridge/bridge_env.py`, every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/` and `bridge/cursor-bridge/workflow/`, `bridge/cursor-bridge/Merge-Verification-Policy.md`, `bridge/cursor-bridge/CHANGELOG.md`, `bridge/cursor-bridge/VERSION`.
- `docs/ROSTER.json` and `docs/ROSTER.resolved.json` of this repository.
- `tools/make-manifest.py` and `tools/dump-cli.py`: run, never edited.
- Every other test file.
- `run/`: the builder writes nothing there.

## The threat model

docs/INVENTORY.md, Decisions: the row "The roster's resolve's threat model (R-107, TASK-086a ...)", added by this pull request's records commit, and the decision row "A roster profile may name a second reviewer ... (design revision `improvements`, R-107)", within "The bridge's threat model as a whole". Outside input: the run record `run/launcher/runs.jsonl`, the report files a branch adds, the roster's entries, as a builder or a reviewer may have written them; git's answers. The four limits named there (a later run rewriting an earlier row so that the record still parses; the base found through `origin/main`, a ref a builder's run can move, KP-032; a row dropped by where a later run started; `clean` disregarding the resolved roster file) and the rule held per branch are outside it and are not defects of the five by themselves.

## The tests the supervisor wrote

All in tests/test_improve_roster_alt.py (126 cases; the builder never edited it):
- Rounds 1's section (74 cases): the brief's acceptance criteria and C39's ten table rows, each case's docstring quoting the Done-when line or table row it enforces; the review guard's first snapshot after a repair and a rebuild (`test_task086a_after_the_repair_and_the_rebuild_the_review_guards_first_snapshot_seeds_no_round`).
- Round 2's section: round 1's confirmed defects (the rebuild form out of the resolved file, review_b's family's model named in the REBUILD, an unavailable reviewer's silent alternate skipping, git answering neither yes nor no, the repair failing part way, hostile record lines, report names with or without a round and in any case, a roster family override, a row of no known family, full refs, full start commits, a silent builder skipping, `--review-alt` naming its cause, acting on the profile in use alone, refusing a detached head, recording the built families, refusing malformed reasons).
- Round 3's section: falsy models, a row of no known family taking a new branch, `--review-alt` refusing an alternate of no known family, the repair refusing links (two cases skip on Windows without the symbolic-link privilege; CI's Linux job runs them), a report name and a branch beyond the console's code page, a report name holding a line feed (POSIX-only).
- Round 4's section (3 cases): under the family deviation, review_b silent leaves the alternate resolved; the alternate silent judges review_b on its one answer; both silent skip the profile; each model probed once.
- tests/test_program_roster_sign_in.py (not this increment's file) pins that every model of a profile is probed and a sign-in answer ends the run with exit 5.

The mutants file: run/supervisor/TASK-086a-mutants.json, the supervisor's mutants N1 to N32 over round 4's code, written by run/supervisor/write_task086a_mutants.py, run by mutation-run.py on a copy outside the checkout (the counts are in docs/HARDENING.md, TASK-086a's proofs).

## Bookkeeping and records in the diff, expected

- docs/BUILDER_NOTES.md (the builder's dated lines, one per round)
- handoff/TASK-086a.md, handoff/TASK-086a-r2.md, -r3.md, -r4.md (the briefs) and handoff/TASK-086a-r1-report.md to -r4-report.md (the builder's reports)
- docs/INVENTORY.md (the threat-model row), docs/HARDENING.md (TASK-086a's entry), docs/PROJECT_STATUS.md (as it reads at the merge): the supervisor's records commit
- run/review/ (this file, the round's diff and assumptions file), removed before the merge
