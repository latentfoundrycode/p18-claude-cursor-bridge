# SCOPE - H1-CLOSE: stage H1's close records, with two tests of its least-confident parts

## What this pull request is
Release B2's stage H1 close, on the installed bridge 2026.11.09a: a records pull request with two supervisor tests, no builder run, no brief, no shipped program or text under `bridge/`. It takes the same round as any pull request (merge.md: a pull request that changes only records). Its procedure is reflection.md (the stage review, the demonstration, items 1 to 6) in the installed tree and at `bridge/cursor-bridge/workflow/phases/`.

The increment ends with the status file as at this pull request's merge (ISS-009): Last accepted names PR #145, Increment and In flight none, Next stage H2 (TASK-051 to TASK-054). The Documents folder (Issues ISS-031 and ISS-032, Feedback FB-085 to FB-091, the Project Summary, the User Manual, the Guide) lies outside the repository and is not in the diff.

## Scope: the files expected in the diff
- `tests/test_header_currency.py`: retired reading (8) also fails on any `<expr>.split("|")` call in plan-check.py (new helper `pipe_splits`), not only on the absence of `diagram_index_selected_ids`; the module docstring names the four readings matched in one program, (2), (4), (5) and (8). Supervisor-written; least confident item 2.
- `tests/test_header_plan.py`: `test_r059_the_launcher_refuses_a_disagreeing_merge_unit`, with its agreeing control. Supervisor-written; least confident item 1.
- `docs/HARDENING.md`: stage H1's review round 1, the demonstration, least confident (three items), HOTFIX-003's carry with Review A's two records findings put right and Review B's lead.
- `docs/INVENTORY.md`: `Updated:`; the session-start hook's threat-model row revised for its load of bridge_env since TASK-047 (stage H1's review, records part, Should fix); the header reader's row corrected (it no longer says no program reads a header, and names the one place it differs from `yaml.safe_load`, which DESIGN.md states).
- `docs/DESIGN.md`: the hotfix's Delivery paragraph names the three files changed on main since the stamp, not one.
- `docs/REQUIREMENTS.md`: R-065's Evidence adds `tests/test_core_carve.py`, which the design's table names.
- `docs/PROJECT_STATUS.md`: as at the merge of this pull request, predicted #145 (newest pull request 144, no issues).
- `docs/archive/STATUS_HISTORY.md`: the old Last accepted and Stage lines moved word for word.
- `project.json`: `state`.
- `run/review/`: this file, the round's diff and its assumptions file, removed before the merge.

## Out of scope
Everything under `bridge/`. Any requirement's status. Any change of behaviour. TASK-051 to TASK-054 are later work. The findings HARDENING records for later edits (the command reference's exit lines, the program docstrings, the parity tests, the quadratic pattern) are recorded, not fixed here, by the stage review's round decision (below the ceiling, no REJECT, no finding of the five).

## The threat model
`docs/INVENTORY.md`, Decisions: the session-start hook's threat model (the row beginning "The session-start hook's threat model"), revised in this diff; the launcher's header refusals sit inside the launcher's own rows. Nothing else in this diff has a threat model of its own: it is records and tests.

## The tests and their proof
- `tests/test_header_currency.py::test_r057_no_program_keeps_a_retired_reading[reading-8-plan-check]` enforces docs/DESIGN.md, "Change: release B2", "The retired readings, enumerated", item (8), and R-057. Proof that it bites: `reading_8` run on plan-check.py as it stood before stage H1 (commit b732a9f) returns `['no call of bridge_env.diagram_index_selected_ids', "split('|') at line 394"]` (the old read `line.strip().strip("|").split("|")`); on HEAD it returns `[]`.
- `tests/test_header_plan.py::test_r059_the_launcher_refuses_a_disagreeing_merge_unit` enforces DESIGN.md's brief header and its agreement rule, R-059: header `merge_unit: [TASK-001]` against the line `Merge unit: TASK-001 TASK-002` is refused with exit 125, nothing launched, no runs.jsonl line, the refusal starting `bridge-run: refused - header: disagrees merge_unit`; the control with `merge_unit: [TASK-001, TASK-002]` runs. Both tests exercise code that is already right, so there is no checkpoint run and no mutants file; the reading's run on the old plan-check is its proof, and the merge-unit test's control is its.
- The two files' own run through the launcher, stripped: `run/agent/H1-CLOSE-own.out`, "156 passed in 19.83s". The suite on this head, stripped, with the pull request's variables: `run/agent/H1-CLOSE-suite.out` on 2842b81 (run 2026-11-11T00:14:16Z), "4949 passed, 40 skipped in 1863.94s (0:31:03)", "bridge-run: exit 0".

## The evidence for the claims in HARDENING
- The stage review: tag `stage-review/H1-1` (local, d58e57f) holds `run/review/STAGE-H1-r1.diff`, its parts and `SCOPE-STAGE-H1.md`; the verdicts are quoted from the reviewers' replies.
- The demonstration: `run/supervisor/demo_h1.py` and `run/agent/STAGE-H1-demo.out` ("TALLY: 54 of 54 checks passed", "bridge-run: exit 0"); its first supervisor run scored 53 of 54, its one difference the order of the merge IDs the launcher records, which the script then compared sorted (HARDENING says so).
- The full suite on main d40e6d2: `run/agent/STAGE-H1-demo-suite.out`, "4947 passed, 41 skipped in 1907.29s (0:31:47)", "bridge-run: exit 0".
- Conformance at the reflection point: 25 OK, 0 MISSING, 5 NOTE.

## Review A
Review A read 1538583: REJECT, one blocking finding (INVENTORY's session-start hook row said the hook falls back to the prose where bridge_env cannot be used; the hook prints one plain line in place of its pointers), two Should fix (HARDENING's incidents bullet: the runs.jsonl lines are written by every full-suite run through tests/test_bridge_run.py:43 and remain; three scratch folders, not four), two Consider (`pipe_splits` matches only a constant `.split("|")`, to widen at the next edit; the suite line to quote). All taken in 2842b81, wording only. Its confirming read of `git diff 1538583 2842b81`: APPROVE, nothing blocking.
