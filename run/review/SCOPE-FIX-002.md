# SCOPE — FIX-002 (stage B2's least-confident items 2 and 3, settled by tests)

No builder increment, no brief: supervisor-written tests (N4 permits tests), the stage-close rule that each least-confident item a test can settle becomes a test written before the next stage's first delegation (supervisor.md, "Reflection points", item 2b). The items are docs/HARDENING.md, "Stage B2 — least confident (stage close, 2026-10-19)", 2 and 3. PR #50.

## Scope

- `tests/test_b2_least_confident.py` — new, 19 tests (below).
- Records: `docs/HARDENING.md` (items 2 and 3 marked "Settled by FIX-002"; one lead added under Stage B3, CONFIG-B3b: the Windows 8.3 short-name form of a folder, from CONFIG-B3b's Review B round 2); `docs/INVENTORY.md` (one Decisions row: the shapes are built, not copied); `docs/PROJECT_STATUS.md` (written as it reads at this pull request's merge, the ISS-009 convention: Last accepted names PR #50 first, In flight none, Next TASK-016); `docs/BUILD_PLAN.md` (TASK-017's and TASK-021's Scope and Done-when name the pin they change, Review A's findings).

## Why shapes, not copies

Item 2 asked for "a copy of each project's real status file". Those files (the TDP's, reAngle's, the video factory's) hold those projects' records and this computer's paths, and this repository is public (rule 54: no computer path enters a commit). So each shape is built in the test from what the judges could trip on, read from the real file on 2026-10-19 as counts and names only: its line endings (reAngle CRLF, the others LF), its field names in their order (27, 26 and 23 fields), its headed sections (1, 1 and 2), its size (about 10,400, 11,800 and 9,500 characters; the real files are 30 to 43 lines, not the "long histories" item 2 assumed) and non-ASCII text; its sections hold bullets that start like `Phase:` and `Workflows:`. The content is invented; the constructed Workflows lines use the classifications of INVENTORY's decision 6 (reAngle and the video factory: Web App Development → Local Web App; the TDP: Own-Computer Software Development → Local Service Software).

## Tests the supervisor wrote, and what each enforces

All enforce docs/REQUIREMENTS.md R-015 (a Workflows line per part right after Phase:, judged by inventory-check.py and conformance-check.py through workflow-check.py) for item 2, and docs/BUILD_PLAN.md:84 and :242 for item 3.

1. `test_fix002_each_shape_holds_what_the_judges_could_trip_on` ×3 — each shape has its line endings, non-ASCII text, its size within 600 characters of the real file's (under 12,000), the Workflows line right after Phase, and exactly its field names in order.
2. `test_fix002_inventory_check_judges_a_shaped_status_file_by_its_line_alone` ×3 — a valid constructed line: no WORKFLOWS LINE finding and no other finding but the absent inventory the shared helper passes on purpose (RESULT 1 problem).
3. `test_fix002_conformance_check_judges_a_shaped_status_file_by_its_line_alone` ×3 — the Workflows-line row OK, RESULT CONFORMANT, and the NOTE rows equal to those on make_workspace's minimal status file in the same environment.
4. `test_fix002_a_broken_line_in_a_shaped_file_is_the_one_finding` ×9 (3 shapes × unknown name, the line after Change cycle, no traits) — inventory-check names the reason and reports nothing else about the file; conformance-check's only MISSING row is the Workflows line's, with the reason, and its NOTE rows equal the minimal file's.
5. `test_fix002_the_bridge_status_line_fails_for_the_stated_reasons_only` — `workflow-check.py --status docs/PROJECT_STATUS.md` from the checkout: exit 1, empty stderr, exactly the two (f) findings and the Installable FLAG, RESULT 2 problems. TASK-017 and TASK-021 take this test into their Scope and change the pin.

The tests characterize existing behaviour (no program changes), so they pass against origin/main by design. Mutation driver (the supervisor's, on a scratch copy of bridge/, tests/ and docs/, restore byte-checked, the Workspace untouched): nine mutants on the tests as they merge, all killed — CR kept by inventory-check.py's read (2 failed), CR kept by conformance-check.py's read (12), inventory-check.py reading cp1252 (6), a `- Workflows:` bullet read as a Workflows line by check_status (15), check_placement never failing (3), check_traits skipped (1), a line without '; traits: ' accepted (3), conformance's stage comparison always stale (12), the shape's Stage not naming Stage 1 (12).

## How the review rounds so far were settled

- secret-sentinel on 4e4946e: PASS (CLEAR). The full suite on 4e4946e: 1741 passed, 25 skipped, 348 s.
- Review A on 4e4946e: APPROVE 0/3/8. Should-fix, all taken in 2edf1b2: (1) the bridge version was hard-coded, now `VERSION` from test_conformance_check; (2) the record said "no other finding" while conformance was checked for MISSING only: the shapes' Stage reads "Stage 1 (...)" to match make_workspace's project.json, and conformance's NOTE rows on a shape must equal those on make_workspace's minimal status file in the same environment (`plain_notes`); (3) TASK-017 and TASK-021 must change the pin but their Scope lines in docs/BUILD_PLAN.md did not name the test file (plan-check.py would refuse their briefs): now they do. Notes recorded as HARDENING leads (the TDP's margin to the 12,000-character cap, the NOTE code-page mojibake, the unverifiable reading of the real files; the 8.3 lead names the temporary folder).
- Two mutants added for fix (2), both killed: conformance's stage comparison always stale (12 failed), the shape's Stage not naming Stage 1 (12 failed). Nine in all.
- secret-sentinel on 2edf1b2: PASS (CLEAR). The full suite on 2edf1b2: 1741 passed, 25 skipped, 346 s.
- Review A on 2edf1b2: APPROVE 0/0/4. Its note taken in 0647f55: TASK-017's and TASK-021's Done-when state the new pin (the FLAG line dropped; then `RESULT: OK`, exit 0).
- The edit to docs/BUILD_PLAN.md is in Scope as a record: two Scope lines gain the test file, two Done-when lines gain one sentence each; nothing else in the plan changes.

## Out of scope

Any program under `bridge/` (no defect of the judges was found, so none is changed), the CI workflow, `.githooks/`. Stage B4's real classifications of the three projects (TASK-019, TASK-020) and of the bridge (TASK-021) are later increments' work, not this diff's defect.

## Expected files in the diff

The five files above and `run/review/` (these review files, removed before the merge).
