# SCOPE — BUG-026 (stage B4's stage review, round 6's fixes)

The supervisor's fix of stage B4's stage review, round 6. Every reviewer approved and no two named one defect. Two findings fall in the classes standing rule 6 raises: a test claiming more than it checks (on the money check itself) and a security gap. The supervisor graded both blocking. No builder ran and no program changed: the diff holds governance text (bridge/cursor-bridge/workflow/traits/spends-money.md), tests and records only. The round's findings and the disposition of each are in the diff's new docs/HARDENING.md section "The stage review, round 6 (2026-10-25): two findings graded blocking by their class, fixed by BUG-026". Read that section first.

## What the fix must do
1. **The inspect list's test is held whole** (tests, should fix, graded blocking).
   - tests/test_traits_new.py's test_r020 asserts the whole "Add at delegation-loop.inspect-checks" section of spends-money.md with one `==`, and since Review A on the fix the whole "Add at configuration.items" section too.
   - Before this fix the list was held from its second item. The first item (a paid call with no approval naming it) and the closing duty (an unapproved call recorded as an issue and told to the owner with its amount, platform and account) were held only by the hash pin.
2. **The store of paid results is outside the Workspace and keeps no key** (conditional, should fix, graded blocking: security).
   - Configuration: the store's folder is outside the repository and the Workspace, and each result and its request are kept with every key, token and other secret left out, as a contract capture's are scrubbed.
   - Its Resources row names it by its role, never by a path of this computer (rule 54).
   - Brief: no result or request is kept with a secret in it.
   - Inspect: a store of paid results or a run's own store inside the repository or the Workspace, or a result or request kept with a secret in it, is a blocking finding; the runs that keep a store of their own and must not read the store are those on a stand-in provider.
3. **Also taken:**
   - A test run on a stand-in provider keeps a store of its own, as the dry run does (a paid run, whatever starts it, is a capture's or every other run's, so its replies are kept): outside the repository, the Workspace and the store's folder. It is empty when each run starts, and when each repetition of a benchmark starts. It is deleted whichever way the run ends. The dry run, a benchmark and a test run never read the store of paid results, and a reading is a finding.
   - An approved live smoke buys its replies afresh, as a capture does.
   - The plan critic's tests hold the missing-trait bullet's first trigger with its row's name, and the command-reference lens's opening condition.
   - The host-extension and own-computer registry rows, and the registry's refinement sentences, are read from "Extension points".
   - The records: INVENTORY's new trait files row and its manual reason, R-010's evidence, and HARDENING's round 6 section. Leads keyed to the next edit of plan-critic.md, installable.md or Delivery-Conventions.md are placed at the next plan revision, because no remaining increment's Scope names those files.

## Out of scope
- Any program, brief or phase module.
- Every lead HARDENING records for rounds 1 to 6, including round 6's two: Merge-Verification-Policy.md's design-mode list, at TASK-034; a re-recording's unreplaced replies, at the next plan revision.

## Tests the supervisor changed, and the paragraph each enforces
- tests/test_traits_new.py::test_r020_spends_money_keeps_paid_results_records_the_cap_and_runs_dry_first: items 1 to 3, spends-money.md's configuration, brief and inspect sections.
- tests/test_traits_existing.py::test_r016_r019_the_plan_critic_keeps_its_design_lenses_and_catches_a_missing_trait and test_r017_the_command_reference_reaches_every_approved_command_design: item 3, plan-critic.md's plan-review section.
- tests/test_type_host_extension.py (registry_row), tests/test_type_own_computer.py (the interface.variants row) and tests/test_extension_points.py (the refinement sentences): item 3, extension-points.md's "Extension points".
- tests/test_b3_least_confident.py: the three edited sections' pins re-taken (spends money's configuration items, brief constraints and inspect checks).

Against origin/main's text, test_r020 and the three pins fail. The tests that only tighten an assertion pass there, since the text they read is unchanged. Mutants of the new text in a checkpoint worktree were all killed by test_r020: the unapproved-call item dropped, the issue-and-report tail dropped, the key clause dropped, the test run left out of the runs that must not read the store.

## Expected files
- The records: docs/HARDENING.md, docs/INVENTORY.md, docs/REQUIREMENTS.md, docs/PROJECT_STATUS.md (written as at this pull request's merge, ISS-009).
- bridge/cursor-bridge/MANIFEST.json (regenerated).
- run/review/ (these review files).
