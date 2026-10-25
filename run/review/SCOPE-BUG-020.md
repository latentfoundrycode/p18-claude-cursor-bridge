# SCOPE — BUG-020

A fix outside the build plan's increments (Issues entry ISS-014). The diagnosis is docs/debug/BUG-020.md; the fix brief, which the builder (composer-2.5) implemented, is handoff/BUG-020.md; the builder's report is handoff/BUG-020-r1-report.md. All three, and the reproduction test, are in the diff (the checkpoint commit b5453bd holds the brief, the diagnosis and the test).

## The brief's Scope (handoff/BUG-020.md)

bridge/cursor-bridge/loop-guard.py (only the function `cron_next`: its signature, docstring and body); docs/BUILDER_NOTES.md (append only); handoff/BUG-020-r1-report.md.

## Out of scope

Every test and fixture (the supervisor's); bridge/cursor-bridge/MANIFEST.json and VERSION (the supervisor regenerates the manifest); CHANGELOG.md; every other program; every other function of loop-guard.py, `cron_field` and `cron_at` included (the security audit's advisory on `cron_field` is a lead in docs/HARDENING.md, not this fix). Design for later work is not this diff's defect.

## The question for a fix diff

Does this repair the named cause (`cron_next` walking naive wall-clock minutes and converting the match back with `.timestamp()`) at the named mechanism (a walk through instants, each read with `datetime.fromtimestamp(instant, tz)`, the instant returned), or does it make the symptom disappear?

## Tests the supervisor wrote, and the paragraph each enforces

tests/test_loop_guard.py::test_bug020_a_one_shot_in_the_repeated_hour_is_found enforces docs/debug/BUG-020.md, "Confirmed cause" and "Reproduction": on Europe/Berlin through the new `tz` argument, five cases (02:09 the second time, 02:49 the first and 03:09 on 2026-10-25, when clocks went back at 01:00 UTC; 03:30 and 01:45 on 2027-03-28, when they go forward); it skips only where zoneinfo or its zone data is missing. Against the checkpoint b5453bd it fails with TypeError (no `tz`); on the fix it passes. No mutation driver was written (the brief named none).

## Also in this diff, expected

- The supervisor's records: bridge/cursor-bridge/MANIFEST.json regenerated (138 files); docs/HARDENING.md (the TASK-021 section's defect line marked fixed; a BUG-020 section with the reproduction, the corrected Windows evidence, two leads); docs/PROJECT_STATUS.md as at PR #73's merge (ISS-009); docs/ROSTER.resolved.json (the roster stamp); docs/debug/BUG-020.md.
- In the builder's report, this computer's Workspace path replaced once by `<the Workspace>` (rule 54).
- The review files under run/review/, in their own commit, removed with `git rm` before the merge.
- Review A (fix mode): APPROVE on 5ebcfe3, its one should-fix (the accept commit's Windows evidence, which proved nothing) answered by the next commit's corrected disposition. The security auditor: PASS, one advisory older than the fix (a lead). The secret sentinel: CLEAR. Full suite on 5ebcfe3: 2166 passed, 33 skipped.
