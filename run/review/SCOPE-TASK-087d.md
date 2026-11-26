# SCOPE - TASK-087d (R-107): `--review-alt` acts on the profile the resolve picks

Where the increment ends: the request (`roster-check.py --review-alt <reason>`) acts on the profile the resolve picks, one per-run record of the alternate's probe answers, and the module docstring's roster example. Design for later increments (the full profile's alternate, a design revision due before 2026-12-16; one record across roles) is not this diff's defect.

Rounds: three builder rounds (briefs handoff/TASK-087d.md, -r2.md, -r3.md); round 3 approved by Review A; the security audit passed every round. The round count at the guard is the Review B round this snapshot opens.

## Scope (round 3's brief, quoted)

Files and directories you may create or modify:
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_review_alt_profile.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-087d-r3-report.md

Do not modify anything else.

Limits on these paths: `tests/test_improve_review_alt_profile.py` is the supervisor's acceptance file, committed before the checkpoint: read it whole and run it, **do not edit it**. `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`, and `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` only by running `python tools/dump-cli.py` (Done), never by hand; `roster-check.py` has no argument parser, so `tools/dump-cli.py` quotes its module docstring. Round 3 needs no docstring change, so these two files are expected to come out unchanged; `python tools/dump-cli.py --check` must pass. `docs/BUILDER_NOTES.md`: new dated lines at its end only. In `roster-check.py`, change only what the per-run record of the alternate's answers needs: the record's creation in `main()` (before the request path and the plain resolve loop, beside the other helpers), `_evaluate_profile`'s probe of the alternate (lines 1305 to 1320) and what it returns about it, and the request path's reading of the alternate's answer (lines 1398 to 1412). Leave the rest of rounds 1 and 2 as it stands.

## Out of scope (round 3's brief, quoted)

- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names
- `bridge/cursor-bridge/bridge-run.py`, `bridge/cursor-bridge/bridge_env.py`, every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/`, `bridge/cursor-bridge/workflow/`, `bridge/cursor-bridge/Merge-Verification-Policy.md`, `bridge/cursor-bridge/VERSION` (reads `2026.11.24a` and must come out unchanged), `docs/ROSTER.json`, `docs/ROSTER.resolved.json`
- every test file; `tools/make-manifest.py` and `tools/dump-cli.py` (you run them, you edit neither)
- the `--record-failure`, `--record-success`, `--mark-exhausted`, `--mark-reset`, `--clear-unavailable` and `--repair-record` modes, the built-set reading (`built_families`, `built_by`), the state file's format, `probe` and its judgement of one reply, `_probe_roles`, and every output line form the existing tests read
- the probes of the roles `builder` and `review_b`: the per-run record covers the role `review_b_alt` alone; leave the builder's and Review B's probes as they stand, even where two profiles share one of those models
- the module docstring (round 1's correction stands), the skips and their order inside `_evaluate_profile`, the request's static refusals and their order, the plain resolve loop (lines 1426 to 1445) and its printing

## Threat model (docs/INVENTORY.md, Decisions)

| A roster profile may name a second reviewer, and an exhausted pool never parks or pauses work (design revision `improvements`, R-107): the families that built a branch are read from the launcher's run record, every builder run counting but one that a later run started without (a clean tree, the resolved roster file apart, at the earlier run's start commit or an ancestor of that commit), a record with a line that does not parse, or one that lacks the row of a report the branch adds, reading as every builder's family having built, and, inside a repository, a record that cannot be opened, a detached head, a git that does not answer or, where the tree holds a report file, a base that cannot be found resolving nothing and refusing every review; Review B is the first of the profile's `review_b` and `review_b_alt` whose family is in neither that set nor Review A's and whose pool allows it, the alternate recorded as a `deviation` in the resolved roster; where neither can review the profile's builder rebuilds the change, as before; the launcher refuses a review by any family that built and lets the profile's builder model review only where that deviation names it for the branch and its recorded families equal the set read at the launch; a row is written after its run has ended, and four limits stay: a later run that rewrites an earlier run's row so that the record still parses, a base found through `origin/main`, a ref a builder's run can move, a row dropped by where a later run started, never by what was brought onto the branch afterwards, and the resolved roster file, which the clean-tree test disregards; the rule is held per branch, a stage's review reading a branch that holds no builder row; both profiles name `composer-2.5` as the alternate, a third family in the full profile and the builder's own model in the native one, the one family of the native pool beside the fallback reviewer's; a provider's safety refusal moves one review to the alternate and marks no pool | the owner, 2026-11-21: "You will work with the fallback suite when it comes to reviewing code and proceed right now.", and 2026-11-22, on a pause until the pool's reset: "I would never tolerate a pause that is almost a month long"; a bare launcher exception would let a builder's own family review its work, so the exception is a record a reviewer of the roster's diff reads | 2026-11-21 and 2026-11-22, owner (the standing word, this chat); 2026-11-24, supervisor (the form, design revision improvements) | a third family joins the native pool, or a review by the alternate is seen to pass what the fallback reviewer would have refused |

The roster file, the roster state file under the git common folder and the launcher's run record are inputs a builder or reviewer can write (KP-078).

## The supervisor's tests

tests/test_improve_review_alt_profile.py (17 tests), each enforcing docs/BUILD_PLAN.md TASK-087d's Done when (R-107; DESIGN.md C39):

- test_task087d_an_exhausted_pool_the_request_acts_on_the_native_profile
- test_task087d_the_plain_resolve_and_the_request_name_the_same_profile
- test_task087d_a_marked_review_b_skips_the_profile_for_the_request_too
- test_task087d_after_a_grok_build_the_request_records_the_built_family
- test_task087d_after_a_composer_build_the_request_is_refused_by_the_family_cause
- test_task087d_with_the_pool_available_the_request_stays_on_the_full_profile
- test_task087d_a_full_profile_that_names_an_alternate_keeps_it_on_request
- test_task087d_a_review_b_that_did_not_answer_skips_the_profile_for_the_request_too
- test_task087d_r2_after_a_grok_build_the_alternate_is_probed_once_on_request
- test_task087d_r2_a_marked_review_b_the_alternate_is_probed_once_on_request
- test_task087d_r2_an_alternate_that_did_not_answer_is_refused_on_its_one_answer
- test_task087d_r2_an_alternate_the_evaluation_did_not_probe_is_probed_once_by_the_request
- test_task087d_r3_an_alternate_that_did_not_answer_for_an_earlier_profile_is_not_probed_again
- test_task087d_r2_no_profile_in_use_refuses_the_request
- test_task087d_a_sign_in_ends_the_request_with_exit_5
- test_task087d_this_repositorys_roster_resolves_the_native_alternate_on_request
- test_task087d_the_docstrings_roster_example_names_no_alternate_in_the_full_profile

Red on the stage checkpoint 0484070 (the mutation engine's checkpoint run): the eleven listed in run/supervisor/TASK-087d-mutants.json's new_tests. The round-2 test of the refused alternate on its one answer was red on round 1's code and the round-3 test on round 2's code; both pass on the stage checkpoint by its other path, a regression guard of the rounds' own defects. Three tests hold what stands (the pool available; a full profile that names an alternate; the sign-in exit 5).

## The mutants

run/supervisor/TASK-087d-mutants.json: 7 mutants, all killed (run/agent/TASK-087d-mutants.out). Each mutant's expect_fail was set from a scratch run listing the tests failing under it (run/supervisor/mutant_failures_087d.py).

## Expected bookkeeping and records in the diff

- docs/BUILD_PLAN.md: stage I2's plan revision (TASK-087d added first, TASK-088 depending on it), the supervisor's commit before the checkpoint
- handoff/TASK-087d.md, -r2.md, -r3.md (the briefs) and handoff/TASK-087d-r1-report.md, -r2-report.md, -r3-report.md (the builder's reports; two quoted paths of this computer replaced with <Workspace> in r1 and r2)
- docs/HARDENING.md, docs/PROJECT_STATUS.md, docs/REQUIREMENTS.md (the records commit)
- docs/cli-reference.json, docs/CLI_REFERENCE.md, bridge/cursor-bridge/MANIFEST.json (regenerated)
- run/review/ (these review files)
