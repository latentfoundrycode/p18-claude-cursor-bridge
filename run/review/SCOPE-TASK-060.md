# SCOPE for TASK-060 (Review B, round 1)

TASK-060 is the strip's names (R-080): a key file naming a home variable is refused before the run, the secret-like name test widened in its one copy, Cursor's secret-like names kept only for a cursor-agent run, conformance-check reading that copy, the shell recipe and D-004's note following. Branch task-060 from main 295d4fd (PR #166's merge, TASK-059). Two builder rounds; this is the review guard's first round for TASK-060, below the code gate's ceiling: there is no Blocking class line.

Where the increment ends: the four programs bridge-run.py, bridge_env.py, conformance-check.py and cursor-agent.shim, MANIFEST.json, D-004's note "Stripped environment" (line 8 only), four test files and the records. The plan's Scope gained cursor-agent.shim and D-004's note at the checkpoint (commit bec5499, HARDENING "TASK-060: the plan's Scope at the checkpoint"), since the Done when's agreement of D-004 and tests/test_account_keys.py with the code needs both. The reviews' leads (HARDENING, TASK-060, leads 1 to 10) are recorded, not this diff's defects: among them a key file naming GH_CONFIG_DIR or the git configuration names, DATABASE_URL's kin, Windows OpenSSH's fixed agent pipe, the stand-in module of conformance-check, resolve's current-folder search, and no test launching a real cursor-agent. The INVENTORY Decisions row on a diagram's design decision is the owner's placement of a later item, unrelated to the code.

Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-060)
Scope: bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/bridge_env.py; bridge/cursor-bridge/conformance-check.py; bridge/cursor-bridge/cursor-agent.shim; bridge/cursor-bridge/MANIFEST.json; docs/diagrams/D-004-context-dfd.md; tests/test_program_strip_names.py; tests/test_bridge_run.py; tests/test_account_keys.py; tests/test_conformance_check.py; docs/BUILDER_NOTES.md; handoff/TASK-060-r<N>-report.md
Satisfies: R-080
Done when: a key file line that names `USERPROFILE`, `HOME`, `HOMEDRIVE`, `HOMEPATH`, `APPDATA` or `LOCALAPPDATA`, in any letter case, refuses the run before it starts with exit 125, the name printed and the value never, for every kind that takes a key file; the secret-like name test stands once, in `bridge_env.py`, and matches, beside what it matched, `PAT`, `CREDS` and `AUTH` as name parts (bounded by `_` or the name's ends, so `PATH` and `AUTHOR_NAME`'s kin are told apart, each boundary case a test), `DATABASE_URL` and `SSH_AUTH_SOCK`; a secret-like `CURSOR_` name is withheld from test and driver runs and kept for builder and review runs, which need the tool's own; `conformance-check.py` reads the one copy and its floor on keys within the builder's reach names the new forms; D-004's note on the withheld names and `tests/test_account_keys.py` agree with the code; `tests/test_program_strip_names.py` names R-080; the mutants file sweeps the name test and the key-file refusal, every mutant killed; MANIFEST regenerated; no option added; no new dependency.

## The supervisor's tests, each with the clause it enforces
- tests/test_program_strip_names.py (names R-080; committed at the checkpoint bec5499, two cases added after round 1's reviews in 5daeb55): the key-file refusal of the six home names in any case before `started` for a named suite and a watch, each with a control that an ordinary key file runs; every home name a key file names is named; the new forms matched, the boundary cases (PATH, PATTERN, AUTHOR_NAME and their kin) not, the old forms still; the new forms and a secret-like CURSOR_ name withheld from a stripped test run and a driver run, a non-secret CURSOR_ name passing; the `--kind` word does not keep Cursor's names for a stripped suite; conformance-check holds no copy and reads bridge_env's; the keys floor and the session NOTE name the new forms.
- The supervisor's fix after round 2's Review A (cd891a7): tests/test_conformance_check.py's inventory-floor case writes its boundary row into the inventory, where the floor reads.

## Round 2's departure from its brief
Round 2 moved the `bridge-run: started` line below the cap and limit computation and the review-only and watch-only refusals, so those refusals exit 125 before it. Review A judged it needed and harmless (HARDENING, round 2's reviews).

## The mutants
run/supervisor/TASK-060-mutants.json (22 mutants over the four test files). counts: run=22 cached=0 killed=20 survived=0 not applied=0 error=0 expected survive=2 (m18: the named suite's own refusal, repeated by the check before started for every kind; m22: the launcher withholding Cursor's key from a cursor-agent run, no test launching the real tool, lead 7)

## Evidence
- Review A: round 1 REJECT, round 2 REJECT on one finding (a test that does not test) fixed by the supervisor in cd891a7; its re-read of the increment at 468b3d1: APPROVE (its two records should-fixes taken in the commit after the records)
- security audit: round 1 FAIL, round 2 PASS
- targeted run on round 2: 1064 passed, 7 skipped; whole suite with the records: 5264 passed, 42 skipped
- completion-check.py --mode plan OK (79 built, 2 deferred, 24 planned); inventory-check.py OK

## Expected bookkeeping and records in the diff
handoff/TASK-060.md, handoff/TASK-060-r2.md and their reports, docs/BUILD_PLAN.md (the Scope gain), docs/HARDENING.md, docs/INVENTORY.md, docs/REQUIREMENTS.md, docs/PROJECT_STATUS.md (as at PR #167's merge), and run/review/ (these files).
