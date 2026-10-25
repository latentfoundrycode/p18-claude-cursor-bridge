# SCOPE — BUG-027 (stage B4's stage review, round 7's fixes)

This is the supervisor's fix of stage B4's stage review, round 7. On 2026-10-25 the owner chose to apply the three-round review cap (INVENTORY, Decisions) by hand, before the programs that hold it are built. Past a review's third round, only five blocking classes send the work back: behaviour against the brief or the register, security, data integrity, a defeated safety mechanism, and a failing test. Every other finding goes to docs/HARDENING.md. The stage review therefore closes at round 7, with no round 8, and this fix carries the round 7 findings that fall in those five classes.

No builder ran and no program changed. The diff holds governance text (bridge/cursor-bridge/workflow/traits/spends-money.md and its trace entry), tests and records only. The round's findings and the disposition of each are in the diff's new docs/HARDENING.md section, "The stage review, round 7 (2026-10-25): closed under the owner's three-round cap, its blocking classes fixed by BUG-027". Read that section first.

This fix is an increment of its own, with its own three rounds under the cap.

## What the fix must do
1. **The test step runs on the stand-in provider.** This closes a defeated safety mechanism: a test the loop ran could spend unapproved before the inspect check saw it.
   - spends-money.md gains `## Add at delegation-loop.test-checks`, with a `new BUG-027` entry in trace-exceptions.md.
   - Every run of the test step runs on the stand-in, with no key the part's code could reach.
   - A test that must reach the paid service is a live smoke, run under its own approval.
   - The new tests are read for such a call before their first run.
   - Such a call, or a test step that bought anything, is a blocking finding.
2. **A charged call that was never answered is not bought again.** This also closes a defeated safety mechanism.
   - Each request is written to the store before it is sent (configuration, brief, inspect).
   - A request found with no result is put to the owner with the provider's record of it, and never bought again unasked.
3. **The store tells accounts apart** (data integrity, new with BUG-026).
   - Each result is kept with the account it was charged to, named by its role.
   - The store is read on the same account.
   - A reply read for another account is a blocking finding.

## Also taken (no class of the five; done in the files the fix edits)
- These sections are each held whole by one `==`:
  - every section of spends-money.md;
  - ai-models.md's test-checks section;
  - external-services.md's inspect, test and brief sections;
  - plan-critic.md's missing-trait bullet.
- plan-critic.md's added-lenses sentence is held from its first word.
- The leftover own store is named as the dry run's, a benchmark's or a test run's.
- R-020's statement now says "the development data".
- Round 6's Review A count is corrected, and so is TASK-022's lead citation.
- The leads keyed to Glossary.md, interface.md's unit or Performance-Conventions.md are placed at the next plan revision.
- INVENTORY Decisions records the owner's decision.

## Round 2 (Review A, round 1: REJECT 3/2/3, all taken)
- The brief's section has every test the builder writes or runs use the stand-in provider, its configuration a value the test sets, never the place of a key; a test that must reach the paid service is a live smoke the brief names, the supervisor's.
- The test step's section: a live smoke the brief names fails the step while skipped, as any skipped test of the increment does, until the supervisor has run it under its approval; a test presented as a live smoke the brief does not name is a blocking finding; the new tests are read before the test step's first run; the deployed-layout test differs from the deployed configuration only by the stand-in's endpoint and key.
- The store keeps each result with the account and the user or caller it was made for, each by an identifier that is no secret, and reads on all of them; two requests that differ only in a value left out are never read for each other; the product's own waiting requests go to the owner as the design states with the cap.
- The inspect list adds a reply read for another account, user or caller, and a waiting request bought again without the owner's answer.

## Round 3 (Review A, round 2: REJECT 1/1/2, all taken)
- A live smoke runs only when the supervisor's approved run switches it on with a value no other run sets, and names the key only then, so it is skipped in the builder's runs, the test step's and CI's; one that runs without that value is a blocking finding; one approved run serves the increment's later rounds unless the code it exercises changes. The brief's section says it is skipped unless the approved run switches it on.
- Two requests made for different accounts, users or callers are never read for each other, whatever the values left out (a re-signed rerun still reads its paid result).
- The intake notes ask the design how a request the product finds with no result reaches the owner.

## Out of scope
- Every lead HARDENING records for rounds 1 to 7.
- Any program, brief or phase module.

## Tests the supervisor changed, and the paragraph each enforces
- tests/test_traits_new.py:
  - test_r020_spends_money_asks_for_approval_the_worst_case_the_cap_and_the_account: spends-money.md's intake section, held whole.
  - test_r020_spends_money_keeps_paid_results_records_the_cap_and_runs_dry_first: items 2 and 3, the configuration, brief and inspect sections, held whole.
  - test_r020_the_test_step_runs_on_the_stand_in_provider (new): item 1, the test-checks section, held whole.
  - test_r020_r022_each_file_is_a_title_and_add_at_sections_only and test_r020_r022_every_section_has_its_own_new_entry_and_no_other_entry_names_the_file: the new section and its BUG-027 entry.
  - test_r022_ai_models_judge_by_evaluation_on_pinned_models_and_recorded_outputs: ai-models.md's test-checks section, held whole.
- tests/test_traits_existing.py:
  - test_r019_the_two_checks_exist_only_in_external_services: external services' three loop sections, held whole.
  - test_r016_r019_the_plan_critic_keeps_its_design_lenses_and_catches_a_missing_trait: the missing-trait bullet, held whole.
  - test_r017_the_command_reference_reaches_every_approved_command_design: the added-lenses sentence, from its first word.
- tests/test_b3_least_confident.py: the three edited spends-money pins re-taken, and the new section's pin added.

The `==` literals were written from the edited files with the tests' own readers (run/supervisor/bug027_edits.py).

Against origin/main's text, 9 tests fail:
- the two structural tests for spends money;
- the configuration, brief and inspect `==`;
- the new test-checks test;
- the pins.

The intake, ai-models, external-services and plan-critic `==` pass there, because their text is unchanged.

## Expected files
- The records: docs/HARDENING.md, docs/INVENTORY.md, docs/REQUIREMENTS.md, and docs/PROJECT_STATUS.md, written as at this pull request's merge (ISS-009).
- bridge/cursor-bridge/workflow/trace-exceptions.md, for the new entry.
- bridge/cursor-bridge/MANIFEST.json, regenerated.
- run/review/, the review files.
