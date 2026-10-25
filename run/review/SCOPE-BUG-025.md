# SCOPE — BUG-025 (stage B4's stage review, round 5's fixes)

The supervisor's fix of stage B4's stage review, round 5. Review B approved it with no findings and every part of Review A approved it, and the convergence rule rejected it because two parts (core, tests) named the same defect. No builder ran and no program changed: governance text (bridge/cursor-bridge/workflow/traits/spends-money.md), tests and records only. The round's findings and the disposition of each are in the diff's new docs/HARDENING.md section "The stage review, round 5 (2026-10-25): rejected by convergence, fixed by BUG-025". Read it first.

## What the fix must do
1. **The missing-trait test reads its pairs from the bullet** (convergent): tests/test_traits_existing.py's test_r016_r019 searches each trigger and its lens in the bullet "A trait missing." of plan-critic.md's plan-review section, not in the whole file. A trigger moved out of the bullet now fails the test. Before this fix it passed.
2. **The class swept** (tests, considers): every stage test the tests part found reading a whole file where it names a section now reads that section:
   - the design-document performance lens (plan-critic.md, "When reviewing a design document");
   - intake.md's "Classifying each part";
   - interface.md's "The variants";
   - the core's "Main and conditional workflows";
   - the registry's "Extension points";
   - installable's "Add at project-end.delivery for install-script".
   The redundant whole-file assertion "is a finding that a trait is missing" is removed, because the bullet's asserted ending holds those words in place.
3. **Three runs do not read the store of paid results** (conditional, should fix): traits/spends-money.md's configuration addition names them:
   - an approved capture or re-recording, which buys its reply on purpose and writes it in place of the old one;
   - the dry run, whose stand-in replies are never written there;
   - a benchmark, which runs with an empty store of its own.
   The brief constraint points at them. The inspect check takes a capture's write without a read as expected, and treats a stand-in's reply in the store as a blocking finding.

## Tests the supervisor changed, and the paragraph each enforces
- tests/test_traits_existing.py::test_r016_r019_the_plan_critic_keeps_its_design_lenses_and_catches_a_missing_trait: items 1 and 2 (plan-critic.md, both review sections).
- tests/test_type_own_computer.py: the misfit-pause and variants assertions (item 2; intake.md and interface.md).
- tests/test_type_web_app.py::test_r023_the_sub_workflow_inherits_and_leaves_the_types_delivery_behind: item 2 (installable, the core, the registry).
- tests/test_traits_new.py::test_r020_spends_money_keeps_paid_results_records_the_cap_and_runs_dry_first: item 3, the configuration sentence, the brief's pointer and the inspect clause.
- tests/test_b3_least_confident.py: the three edited sections' pins re-taken (spends money's configuration items, brief constraints and inspect checks), nothing else.
- Checkpoint run against origin/main: the spends-money test and the three pins fail, and the section readings pass. They should pass there, because the text is placed right and only the tests were loose.
- Mutants on the old code: test_r016_r019 fails with the benchmark clause dropped from the bullet, with it moved under the design review, and with the performance lens moved under the plan review.

## Also in this diff, expected
- docs/HARDENING.md: the round-5 section; round 2's leads each naming its event; TASK-022's consider 4 noting that TASK-017 passed it.
- docs/INVENTORY.md: the reason for the manual's command-reference chapter after BUG-021's reversal; the part asked twice narrowed to one with an approved command design; the new trait files' row naming the rules the review built.
- docs/PROJECT_STATUS.md as at PR #79's merge (ISS-009).
- bridge/cursor-bridge/MANIFEST.json, regenerated.
- docs/ROSTER.resolved.json's stamp, in its own commit.

## Review A on the fix
APPROVE (0/2/6), all eight findings taken in the second commit except where a paid benchmark keeps its replies, which is a lead:
- The mockups test reads each build condition from its delegation-loop section.
- N7 and N9 are read as founding rules, and N1's conditions from N1's own bullet.
- The host-extension tests read the registry's "Extension points".
- spends money:
  - the store's exception sits on the reading;
  - an interrupted capture resumes from what it wrote, or runs again only as a newly approved paid action;
  - the dry run and a benchmark each get an empty, discarded store of their own;
  - only an approved capture turns the reading off, and the inspect check says so.
Mutants on the new readings: has screens' design-auditor sentence moved under interface.variants, the N7 bullet deleted, and N1's "spends nothing unless asked" dropped from its bullet. Each is now caught.

## Confirming reads
- **The first confirming read** returned APPROVE (0/2/2). The store-of-paid-results passage was then cut back to a plain rule, as BUG-022's speed-budget sentence was:
  - an approved capture or re-recording reads only the replies its own run bought, each written with that run;
  - the dry run and a benchmark keep their results in a store of their own, outside the store's folder, empty at the start and deleted at the end;
  - every other run reads the store before it buys.
  The brief points at the rule. The inspect check makes these findings: a capture reading a reply its own run did not buy, another run skipping the store, a stand-in's reply in the store, and a dry run's or benchmark's own store left behind.
- **The second confirming read** returned APPROVE (0/0/4), and all four findings were taken: the store's place, the capture finding as its own item, the inspect list held in one assertion with its grade, and the HARDENING record.

## Out of scope
- The leads the HARDENING sections record (round 5's included).
- The bridge's traits, which the owner decides at the stage close.
