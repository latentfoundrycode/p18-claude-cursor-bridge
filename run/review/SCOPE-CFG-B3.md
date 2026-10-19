# SCOPE — CFG-B3 (the builder's configuration at stage B3's start)

No builder increment. cursor-configurator wrote the configuration from run/supervisor/cfg-b3.md (gitignored; the instructions follow below in substance), append-only; the supervisor made the edits named here and wrote the records. PR #47.

## Scope

The calibration of 2026-10-19 (to bridge 2026.10.18a) found four conformance floors MISSING, applied as configuration work at stage B3's start (supervisor.md, calibrate-bridge step 4: configuration through cursor-configurator, append-only, its own checkpoint):

- `.cursor/rules/workspace-boundary.mdc` — the always-on Workspace boundary rule (Cursor-File-Formats.md's text).
- `.cursor/rules/secure-coding.mdc` — from the installed bridge's `secure-coding.snapshot.md`, OWASP ASVS 5.0.0 filtered to L2 (the supervisor's decision, recorded in INVENTORY Decisions); globs `**/*.py, **/*.ps1, **/*.yml, .githooks/*`.
- `.cursor/hooks/boundary-check.py`, `run-hidden.py`, `windowless-check.py` — byte-identical copies of the installed bridge's.
- `.cursor/hooks.json` — one advisory `afterFileEdit` entry (no failClosed) running the boundary check through run-hidden.py; the interpreter named as `python` (the configurator had written the user-profile interpreter path, which rule 54 keeps out of a commit; the repository is public; the bridge has no virtual environment).
- `.githooks/pre-commit` — `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` (CI's command, .github/workflows/tests.yml line 26, plus the hook folder); active through the local `core.hooksPath = .githooks`.
- `.gitattributes` — one line, `.githooks/** text eol=lf`.
- `.gitignore` — `docs/BOUNDARY_VIOLATIONS.md` appended (the boundary log holds this computer's absolute paths; read locally, never committed).
- Records: docs/INVENTORY.md (a Resources row, two Decisions rows: the ASVS level and the stand-in outside-write check), docs/HARDENING.md (a new "Stage B3" section), docs/PROJECT_STATUS.md (as at this pull request's merge).

## How the review rounds so far were settled

- secret-sentinel: CLEAR three times; its note (the boundary log could carry computer paths into a commit) converged with Review A's consider 3 and is fixed by the `.gitignore` line.
- Review A: APPROVE 0/2/3. Should-fix 1 (the gate did not scan `.cursor/hooks`): fixed. Considers 1 and 2 (the rule's globs; a dangling pointer): fixed. Should-fix 2 (nothing showed the hook fires inside Cursor): settled by a live probe, with the answer **no**: a builder run wrote `../Worktrees/hook-probe.txt` (deleted afterwards) and nothing was logged; three further diagnostic runs with uncommitted marker-only entries (between them: with and without the matcher, `python` and the full interpreter path, `--trust`; four runs in all where the hook should have fired) never ran a hook; the event stream shows the edit with no hook event. The cause is not separated; it is recorded as ISS-010 (Documents) and FB-025, and in HARDENING, Stage B3, CFG-B3; nothing relies on the hook. The diagnostic files were removed and never committed.
- Review B, round 1 (snapshot of 360b14f): APPROVE, no findings; verify OK.
- Review A, delta read of the fixes: APPROVE 0/2/3, all taken in this round's commit (records only):
  - Should-fix 1: docs/PROJECT_STATUS.md, Last accepted and Calibration pending, named the boundary hook as applied with no qualifier; both now say it is configured and does not run in builder runs (ISS-010), and that one of the conformance check's 21 OK is a floor configured but not engaging.
  - Should-fix 2: docs/HARDENING.md, Stage B3, said CI runs the same windowless check; CI scans bridge/cursor-bridge only, not .cursor/hooks. The sentence now says so; adding the folder to the CI step is left to the next increment that changes the workflow (the command-reference increment does).
  - Consider 1: docs/INVENTORY.md, the configuration row's "Used by" now says the hook does not run in builder runs.
  - Consider 2: a stand-in detector is recorded as an INVENTORY decision: a marker touched before each builder launch, then `find` over the project root with the Workspace pruned, listing anything newer; tested here on 2026-10-19 (silent with no change, lists a file written to ../Worktrees on purpose, the probe file removed).
  - Consider 3: the probe count; the records were right (four runs in all), the supervisor's message to the reviewer had said five.

## Verification

- The pre-commit gate ran on every commit since 1ee223b ("33 file(s) scanned, 0 FAIL"); Review A showed on a clone that it blocks a launch without the flag and lets a `--no-verify` checkpoint through.
- conformance-check --installable: 21 OK / 2 MISSING (the command reference, next; the recorded no-diagram-index decision) / 5 NOTE.
- test_r001_status_names_its_own_merge passes with PR #47's variables.

## Out of scope

The command reference (docs/cli-reference.json, the next increment); any program under bridge/, any test, the workflow. Design for later increments is not this diff's defect.

## Expected files in the diff

The files above and `run/review/` (these review files, removed before the merge).
