# SCOPE - TASK-029

TASK-029, the builder's increment for R-040: one heavy job at a time on the computer, the launcher's machine-wide slot (docs/BUILD_PLAN.md, "### TASK-029"). Briefs: handoff/TASK-029.md (round 1), handoff/TASK-029-r2.md (round 2), handoff/TASK-029-r3.md (round 3, a code-only fix brief) and handoff/TASK-029-r4.md (round 4, a code-only fix brief: a driver's program checked again after the slot's wait). Each later brief corrects the earlier ones; where they differ, the later governs. The builder is composer-2.5 in every round. The loop's text is TASK-030's and mutation-run.py TASK-031's: design for those is not this diff's defect.

This review reads the whole increment past the owner's three-round review ceiling: only the five blocking classes send the work back (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism, a failing test); every other finding is recorded in docs/HARDENING.md, Stage B5, under "TASK-029", where the findings of rounds 1 to 3 not taken already stand.

## Scope (rounds 1 and 2; rounds 3's and 4's are a subset: bridge-run.py, docs/BUILDER_NOTES.md and the round's report)

- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/loop-guard.py
- bridge/cursor-bridge/MANIFEST.json (regenerated only)
- tests/test_bridge_run_slot.py
- tests/test_loop_guard.py
- docs/cli-reference.json and docs/CLI_REFERENCE.md (regenerated only)
- docs/BUILDER_NOTES.md
- handoff/TASK-029-r1-report.md, handoff/TASK-029-r2-report.md, handoff/TASK-029-r3-report.md, handoff/TASK-029-r4-report.md

## Out of scope (round 2's, quoted in substance; round 3 adds that the builder edits no test)

- .env and anything under secrets/; CI configuration (.github/, .githooks/).
- docs/ and handoff/ except the files above (the records are the supervisor's: docs/INVENTORY.md, docs/HARDENING.md, docs/REQUIREMENTS.md, docs/PROJECT_STATUS.md, docs/archive/STATUS_HISTORY.md).
- bridge/cursor-bridge/VERSION; bridge_env.py, bridge-stop.py, settings.bridge.json, review-guard.py, wake-timer.py, mutation-run.py (TASK-031's), and every text file of the loop (TASK-030's).
- The POSIX limitation recorded, not taken (HARDENING, "TASK-029 (round 1's reviews; recorded, not taken)"): off Windows a launcher killed alone frees the slot while its command runs.
- The round ceiling (R-042; TASK-032).
- Done when (e) of the build plan (a run waiting more than thirty minutes, started from the Bash tool): the supervisor's, recorded under ISS-011 in the Issues document.

## The tests and the driver the supervisor wrote

- tests/test_bridge_run_slot.py, rewritten by the supervisor in round 3 (b2cdc9d2) and extended after round 3's reviews (the head commit before this file's): every test's docstring names the requirement it enforces (handoff/TASK-029-r2.md's requirements unless handoff/TASK-029-r3.md is named). Against round 2's code 8 of them failed, each on the fix round 3 awaited, and 43 passed. The floor test test_r040_bound_never_before_own_kind_floor (enforces round 1's Requirement 5's fixing rule) is the supervisor's, though committed in 2ef10606.
- tests/test_a4_followups.py, test_bridge_stop_ends_a_launcher_run_and_its_tree (enforces handoff/TASK-029.md's paragraph on the stop test): its environment built inside the test, heavy.lock asserted under the tests' temporary home while its launcher runs, the launcher killed in a finally, off Windows the child killed first.
- Round 4 (57e34e3, the supervisor's): test_r040_driver_rechecked_after_the_wait[swap] (enforces handoff/TASK-029-r4.md, Requirement 1, and docs/INVENTORY.md's "checked again just before the start"): a driver waiting on a held slot whose program is replaced during the wait by a hard link to an outside file is refused (125, the driver refusal, no log row), the outside program never runs, a heavy run starts at once afterwards; the twin without the swap runs its program. It failed on round 3's code (the outside program ran, exit 0). 234e4de makes it skip only where Python has no os.link.
- The same commit fixes a race in four of the supervisor's tests that started a waiter and read its first waiting line before the holder's record was published (the launcher prints `slot taken` before it publishes): test_r040_holder_that_waited_publishes_slot_taken_start (a4cb89c, after CI's Windows job failed it once), test_r040_wellformed_record_named_in_wait_line, test_r040_bound_stays_first_fixed and test_r040_two_heavy_runs_serialize_commands; each now waits until the record reads live (or names the holder) before the waiter starts; no assertion after it changed.
- Review B's second reading (on 5db7579) rejected round 3 for the driver's missing second check; that is round 4's one fix. Its earlier reading (on 1d3d99d) approved round 3.
- run/supervisor/task029_mutants.py (gitignored; not in the diff): 18 mutants of bridge-run.py and loop-guard.py, each restored byte for byte; at round 3's code all 17 killed (M6 after the floor test); at round 4's, M18 (no second check) killed, and M2, M3, M5 re-run on the changed tests, killed.

## Bookkeeping and records expected in the diff

- docs/BUILDER_NOTES.md (if touched), the builder's three reports under handoff/, the three briefs.
- docs/HARDENING.md (rounds 1 to 3, recorded, not taken), docs/INVENTORY.md (the BRIDGE_RUN_SLOT_SCALE Resources row, the Features row), docs/REQUIREMENTS.md (R-040 built), docs/PROJECT_STATUS.md (as at this pull request's merge) and docs/archive/STATUS_HISTORY.md.
- run/review/ (this file, the diff and the assumptions file).
