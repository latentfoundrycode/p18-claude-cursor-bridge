# SCOPE - TASK-018

A supervisor-authored increment of governance text and its tests, with no builder run and no program change. Its brief is docs/BUILD_PLAN.md, "### TASK-018 — Trait files: spends money, long-running process, AI models" (Scope, Satisfies R-020 to R-022, Done when), as revised and approved on 2026-10-24 (subject `traits`, PR #67). Its sources are the Restructuring Plan's §6.8 (the three traits), §8.1 (the background-process rule, N1) and §13.1 ("The owner's money": the store of paid results, the dry run on a copy with a stand-in provider, every remote wait bounded). The pointer at external services rests on docs/INVENTORY.md's Decisions row on the deployed-layout and bounded-remote-wait checks.

## Scope (quoted from the plan)
bridge/cursor-bridge/workflow/traits/spends-money.md; .../long-running-process.md; .../ai-models.md; bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_new.py; tests/test_b3_least_confident.py

## Out of scope
- Every phase module, the core and the plan critic: unchanged. design.md is not changed: the design gate's trait decision checks the classification sentence as it stands (BUILD_PLAN TASK-018; INVENTORY, Decisions).
- The four trait files TASK-017 wrote, external-services.md included: unchanged; spends money only points at its inspect-check addition.
- The type files of TASK-019 to TASK-021. Design for those increments is not this diff's defect.
- Every program under bridge/.

## The tests the supervisor wrote, and the paragraph each enforces
tests/test_traits_new.py (new, 17 tests, naming R-020 to R-022), each enforcing TASK-018's Done when:
- each file is one `#` title and the `## Add at` sections the Done when names, in order, and no other heading, so it adds only and at no other point;
- each section has its own `new TASK-018` entry naming the file and the heading, and no other entry names the file;
- no unit of a file, as trace-check.py reads units, is a unit of the core or a phase module (new text, never a copy);
- the three open-list rows are written; workflow-check.py passes over workflow/;
- spends money: the approval before any paid action, the worst case, the cap, the platform and account; the classification sentence and the pointer at external services' `delegation-loop.inspect-checks` addition, which exists and holds the bounded wait, spends money stating no bound of its own; the store of paid results that nothing discards, the cap recorded, no paid action in a builder run, the dry run on a copy with a stand-in provider, the check that no paid action ran unapproved;
- long-running process: points at N1 and §8.1, N1's eight conditions still in the core and in no trait file; the start, stop and health procedure; a run that leaves nothing running; the nothing-left-running check;
- AI models: evaluation sets and thresholds (rule 52), the Evaluation design section (rule 51), pinned models, recorded outputs, the evaluation on them.

The assertions also hold the text Review A's two rounds changed: the approval covers the loop's paid actions and a product that spends in the owner's use enforces the cap (rule 52); the intake notes carry the trait's two duties to the design; every paid call goes through the store, and the inspect check fails one that does not both read it and write to it; a capture's first paid run and a purchase run at the smallest size instead of dry; the provider's usage read only where a Resources row records a way; the process's commands recorded in the increment that builds them, and a run a test starts and stops part of that test; a model judge pinned, its verdicts recorded and judged again when the code shaping the judged result changes. The copy check reads the core, the phase modules, the plan critic and the other trait files; the N1 guard reads each of the eight conditions.

Review B's first read (REJECT) was answered by 5745ef4, which this read checks first: a test starts an instance of its own, on a port and data of its own, and the nothing-left-running check stops only what started during the tests, never the instance the owner runs; while nothing that shapes a model judge's judged result changes, the evaluation runs on recorded verdicts, and once it changes, the change is blocked at the test step until new verdicts are recorded. Both are asserted in tests/test_traits_new.py.

Your second read approved 083333b. Review A's read of the same fixes approved with four points, all taken in the commit after it, which this read checks first: the procedure's start and stop commands take the port and the data of the instance they start and stop (so a test's instance runs beside the owner's); the nothing-left-running check tells what the tests started by descent from the test run or by a test instance's port or data, never by start time alone, stops it by its process ID with its children or by the stop command given that instance's port and data, and leaves the owner's and another session's processes alone; each model judge's verdict is kept with the judged result it read, and where a model costs money the block waits on the run the owner approved, which the supervisor starts, never on a re-delegation. Each is asserted in tests/test_traits_new.py.

tests/test_b3_least_confident.py pins the eleven new sections; its derivation (widened by TASK-017) covers every new entry.

Run once against the checkpoint b03fd42: 28 failed, 78 passed across the two files; the new file's one pass there is the workflow-check guard, which holds on both sides; the eleven new pins fail and the earlier pins pass.

## Expected bookkeeping and record files in the diff
docs/REQUIREMENTS.md (R-020 to R-022 built), docs/INVENTORY.md (a Features row), docs/HARDENING.md (TASK-018's section: the checkpoint run), docs/PROJECT_STATUS.md and project.json as at this pull request's merge, bridge/cursor-bridge/MANIFEST.json regenerated, docs/ROSTER.resolved.json (the roster check's resolved_at stamp, rewritten at each check), and run/review/ (these three files, removed before the merge).

## What to judge
Does the diff meet every clause of the Done when? Is the text sound guidance a supervisor will follow on a real project, safe for the owner's money and machine, consistent with the core (founding rule N1, the rule that every cost names its platform and account, rules 51 and 52), with configuration's spending-limits item, with the registry's points and with external services' additions? Can each check be carried out from what the supervisor can see? Do the tests enforce their paragraphs and fail on a regression? Are the records accurate? Apply the anti-gaming checks.
