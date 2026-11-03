# SCOPE - TASK-044: the retrofit's enforcement, the tests that name D-002, D-003 and D-004 (R-055), and the weekly scan's proof (R-052) (pull request #129)

Tests over behaviour release B built, plus the records that flip two requirements to built. Supervisor-authored by the plan, so there is no builder run and no brief. Your question: do these tests hold the behaviour and the diagrams they name, or do they pass whatever the code or the diagram says? The code under test is not in the diff; read it at this tree (bridge/cursor-bridge/review-guard.py, bridge-run.py, bridge_env.py, tools/dump-cli.py) and try mutating it.

The branch's commits, in order:
- 8eeb1dd: the tests, the three diagram files and the index.
- ab24945: the records.
- this round's review files, committed last.

## Scope (the plan's, quoted)
tests/test_dump_cli.py; tests/test_review_guard_ceiling.py; tests/test_bug036.py; tests/test_review_guard.py; tests/test_account_keys.py; tests/test_bridge_run.py; tests/test_d003_review_round_states.py (new); docs/diagrams/INDEX.md (the Enforced-by cells naming the new file, D-003's naming `tests/test_bug039.py` beside it)

## Beyond that list, kept and named
- docs/diagrams/D-002-components.md: `%% external: project_cursor_hooks` and one Grouping sentence. `diagram-check.py --mode done` failed on main, "component 'project_cursor_hooks' matches no source file - drawn but not built", the checker's `SKIP_PATH` leaving out `.cursor/`; the Done when requires that mode OK. The comment stretches the conventions, which define it for a sequence participant: a program lead in docs/HARDENING.md.
- docs/diagrams/D-003-review-round-states.md: the table's open points and the transitions paragraph, as built, by the diagram specialist's as-built variant, since the transitions are now exercised.

## Done when (read docs/BUILD_PLAN.md, "### TASK-044", whole; it is long and every clause counts)
In short: test_dump_cli.py names D-002 and compares the programs dump-cli.py loads with the diagram's `dump_cli` edges read from the file; the three guard files name D-003 in their docstrings; tests/test_d003_review_round_states.py holds one test per state and one per transition the diagram listed as unexercised; test_account_keys.py and test_bridge_run.py name D-004 and pin the withheld and set names read from its note against `bridge_env`'s; `diagram-check.py --mode code` OK with no TESTS line and `--mode done` OK with no deviation; the mutants on the code and the two hand mutations on the diagrams; the dispatch on main read green and its id in the accept commit and the inventory; R-052 and R-055 built in the records-only commit.

The plan's exception: these tests characterise behaviour already built, so the red-on-checkpoint proof does not apply; the mutants are their proof.

Three readings of the plan, for you to judge:
- The plan's "hand mutations" were run through `mutation-run.py` on its scratch copy, m18 and m19, so nothing edited the tree.
- The plan's "`--strip` from TASK-041's merge" is not how the mutation run was launched: docs/INVENTORY.md's Decisions row on the stripped launches says they apply from release T's install, not from the decision (P10), so the run went unstripped as the installed text states.
- The plan's "holding no `dependency-scan: OSV-Scanner exit` line" reads as no printed exit line: the one match in the log is GitHub's script listing with a literal `$code`; the one secret-word match is the runner's "Secret source: Actions". A lead in docs/HARDENING.md.

Later increments are later work, not this diff's defect: TASK-045 the stamp, the install run sheet and the trial's calibration, and R-056 stays planned until then. The evidence's grammar is read by TASK-045's stamp test.

## The project's threat model, as docs/INVENTORY.md's Decisions record it for what the diff changes
Row 166, the review guard's threat model: what a reviewer does in passing in the checkout is inside it; a deliberate reach past that is recorded and never blocks by itself. Row 167: R-050's grading of a convergent finding is held by hand ahead of the install. This diff changes no program; a test's fixture is no attack surface unless it runs something from outside its temporary folder. You may disagree with these rulings.

## The tests the supervisor wrote
Each names the paragraph it enforces, by R-055 and the diagram.
- tests/test_d003_review_round_states.py (new, 37 test ids): `test_d003_state_*`, one per state; `test_d003_transition_*`, one per transition the retrofit found unexercised; the launcher run for real with a stand-in agent.
- tests/test_dump_cli.py: `test_r055_d002_the_programs_dump_cli_loads_equal_the_diagrams_edges`.
- tests/test_account_keys.py: `test_r055_d004_the_withheld_names_are_the_notes`, `test_r055_d004_the_set_names_are_the_notes`; WITHHELD gained seven names. This widens a test's input: check it against the anti-gaming list.
- tests/test_bridge_run.py: `test_r055_d004_a_stripped_run_gets_the_notes_names`.
- tests/test_review_guard_ceiling.py, tests/test_bug036.py, tests/test_review_guard.py: D-003 in the docstring and nothing else.

The mutants file is run/supervisor/TASK-044-mutants.json (gitignored, not in the diff; you may read it), written by run/supervisor/task044_mutants.py: 47 mutants, the number m42 unused, cut none, none alike. Each lists the exact tests that must fail; 13 mutants' lists were corrected after a first run from the failing sets in run/agent/TASK-044-lists.out, each read and judged, Review A concurring. m30's and m31's kills of tests outside their aim are no proof of those tests' own transitions, which have mutants of their own.

## Bookkeeping and records expected in the diff
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009), the line it replaces archived in docs/archive/STATUS_HISTORY.md.
- docs/REQUIREMENTS.md: R-052 and R-055 built, with their Evidence; each entry is a label and a test file or node id.
- docs/INVENTORY.md: a Features row "The retrofit's enforcement", a Resources row for the dispatch's run, the scan's row naming it.
- docs/HARDENING.md: TASK-044's section, the findings not taken.
- run/review/: this round's files.

## Before this round
- The dispatch: GitHub Actions run 41538774550, workflow_dispatch on main at d34f76c, conclusion success; its log "found 7 packages", "No issues found" (run/agent/TASK-044-dispatch.log, not in the diff).
- Review A: REJECT on one finding (the time gate on the re-snapshot's reply unenforced), taken with its should-fix findings and the audit's advisories, then APPROVE on the confirming read. Security audit: PASS, 0 blocking, five advisories, all taken.
- Mutation run (run/agent/TASK-044-mutation.out, not in the diff): "counts: run=20 cached=27 killed=47 survived=0 not applied=0 error=0 expected survive=0", "bridge-run: exit 0". Estimate on in-flight: order of 10^5 processes.
- P7's suite, on ab24945 (run/agent/TASK-044-suite.out, not in the diff): "3500 passed, 41 skipped in 1671.50s", "bridge-run: exit 0"; no skip names test_d003 or a test_r055 test; one skip is `tests/test_release_t_strip.py`, an environment test that needs a stripped launch, as before.
- `diagram-check.py --mode code`: RESULT OK, no TESTS line. `--mode done`: RESULT OK, no deviation. inventory-check: OK. plan-check: OK. completion-check --mode plan: OK. windowless-check: 0 FAIL. No workflow text under bridge/ changed, so the traceability check has nothing new to read.

## An incident to know of
During Review A the audit ran `rm -rf` on a fixed-name scratch folder that was Review A's live export. Nothing in the checkout was touched; Review A re-ran in a fresh folder. docs/HARDENING.md, TASK-044. Make any export of yours in a new folder from `tempfile.mkdtemp`, outside the checkout.

## The round
The guard's count is 0 before this snapshot and 1 once it opens, so this is Review B's first read. The launcher's count of builder rounds is 0, there being no builder. This round is below the ceiling; grade every finding by the five blocking classes all the same (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test), and say for each which class it is or that it is none.

Never run review-guard.py snapshot, verify or premerge in this Workspace itself.
