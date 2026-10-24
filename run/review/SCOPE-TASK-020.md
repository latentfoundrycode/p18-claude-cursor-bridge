# SCOPE — TASK-020

Supervisor-authored (governance text and tests are the supervisor's, §15 condition 3); no builder run, so there is no builder report and no `Assumed, not verified` list.

## The brief's Scope (docs/BUILD_PLAN.md, TASK-020)

bridge/cursor-bridge/workflow/types/own-computer.md; bridge/cursor-bridge/workflow/types/own-computer/local-service.md; bridge/cursor-bridge/workflow/open-list.md; tests/fixtures/workflows/tdp.status.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_own_computer.py; bridge/cursor-bridge/workflow/trace-exceptions.md; tests/test_b3_least_confident.py

## Done when (read it sentence by sentence)

The type names its GUI/CLI/pipeline/local-service sub-types; local-service *adds* the contract-design interface variant and, where the part also has administrative commands (the TDP), the command-design variant too (variants added per interface kind, not set as one value); every section of the two files is new text, each under a `new` entry in trace-exceptions.md, and tests/test_b3_least_confident.py's derivation and excused-section pins cover the type files' entries; both rows flip to written; `workflow-check.py` passes and classifies the TDP (committed fixture, performance-budgets held per §6.3 until its code map carries one) without pausing; `test_type_own_computer.py` (names R-024) asserts the sub-types and the added variants.

## Out of scope

The other sub-types' workflows (GUI, CLI, pipeline: written when the first project of each arrives, open list); the host-extension type (TASK-021); a delivery kind for the type or the sub-type (the Done when names none: installable's intake passage confirms a part's kind with the owner where no conditional workflow sets it); the long-running-process lead of TASK-018 (a local service's lifetime against N1's idle stop, a test instance's port), which stays in docs/HARDENING.md for the next plan revision. Design for later increments is not this diff's defect.

## What the files say

- types/own-computer.md, `## Add at intake.questions`: the type's four sub-types, told apart by what the user meets (a window: GUI; a terminal: CLI; nothing, jobs run unattended with files or records as output: pipeline; other software on the same computer through a protocol: local service), asked where the owner's description leaves it open; a part met through several takes the sub-type of the surface it exists for, the interface phase running a variant for each of its other kinds; one that exists for two equally pauses by intake's own rule (phases/intake.md, "A part that does not fit pauses the project before design").
- types/own-computer/local-service.md, `## Add at interface.variants`: the contract design variant for the protocol, an addition; for administrative commands (the TDP's), the command design variant too; each added for its own kind of interface, so a part with both runs both.

## Tests the supervisor wrote, and the paragraph each enforces

tests/test_type_own_computer.py (twelve test_r024_ tests, R-024), each docstring naming its paragraph: BUILD_PLAN TASK-020's Done when; open-list.md, "Default traits" and the Sub-types table's definitions; extension-points.md, `interface.variants` (add only, per part); phases/interface.md, "The variants" (every variant is an addition); phases/intake.md, the pause on two sub-types fitting equally. tests/test_b3_least_confident.py gains two excused-section pins (the type files' entries, read under `types/` since TASK-019). Against the checkpoint 8ba0e78 the new and changed tests are 14 failed, 92 passed; the new file's one pass there is the workflow-check guard.

## Also in this diff, expected

Review A's first read (APPROVE, two should-fixes and five considers) is answered in the commit after f027ea9: the parallel records say no increment is marked `Parallel: yes`, so nothing runs concurrently until a plan revision marks some; the TDP's status file measured (about 430 characters below the cap once it has its line); local-service.md names no project and calls the contract design the first of its variants; one docstring narrowed; one date cell. The roster stamp is in the checkpoint commit, 8ba0e78, before the diff's base.


- The owner's run-parameter change, in their words on 2026-10-25 ("I'd like to turn on parallelism for this project then."): docs/RUN_PARAMETERS.md (`Parallel increments: on`), tests/test_release_b_bootstrap.py's OWNER_RUN_PARAMETERS (rule 52: a value the owner chose is fixed in a test), and docs/INVENTORY.md's run-parameters Decisions row plus a new row: builders run concurrently only once TASK-028 and TASK-029 have merged (ISS-011). It is outside the increment's Scope by the owner's decision, carried here so that it needs no gate of its own. A change of an owner's value with its test is the owner's (test_r001's docstring), not a weakened test.
- Records: docs/REQUIREMENTS.md (R-024 built), docs/INVENTORY.md (a Features row), docs/HARDENING.md (TASK-020's section; TASK-019's closing line), docs/PROJECT_STATUS.md and project.json as they will read at this pull request's merge (ISS-009), bridge/cursor-bridge/MANIFEST.json (two new files hashed, 136 in all), run/review/ (these files).
