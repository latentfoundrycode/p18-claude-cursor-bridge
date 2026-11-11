---
record: run-parameters
header: 1
stage_pause: run
merge_authority: supervisor
refactoring_pass: "on"
installer_verification: "n/a"
parallel_increments: "on"
agent_ceiling: null
ceiling_above_twice: []
design_rounds_above_five: []
review_rounds_above_ceiling: []
---
# Run parameters
Set: 2026-10-11   (owner may change any of these at any time by saying so; update this file)
Stage pause: run
Merge authority: supervisor   (owner's instruction 2026-10-12: as a supervised project the bridge's supervisor completes the merge itself through the gate — the pre-supervised-project barrier, no premerge record possible, is gone; the supervisor never uses --admin or force-push, which the guard and branch rules refuse)
Refactoring pass: on
Installer verification: n/a (host extension — the bridge's install program is rehearsed on a copy and run by the owner from a run sheet, not a desktop installer-check)
Parallel increments: on   (the owner's word, 2026-10-25: "I'd like to turn on parallelism for this project then."; off from 2026-10-11 until then; the launcher's one heavy slot (R-040, TASK-029) holds every builder run, so builders build one after the other all the same, and the build plan marks no increment `Parallel: yes` today, INVENTORY Decisions)
