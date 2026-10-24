# Performance budgets

## Add at intake.questions

**Performance and cost budgets** (`~/.claude/cursor-bridge/Performance-Conventions.md` §1).
Turn the stated performance, scale, and cost expectations into numbered budgets — one
operation, one condition, one number, one measurement: "a search over 10,000 documents
answers within 2 s at p95", "startup under 1 s", "syncing 1,000 files costs at most $0.50".
Propose the numbers from the platform and the expected data; the owner sets them (a
decision brief: what each number means for the user and what meeting it costs). "No
budgets" is a legitimate answer for software with no operation the owner cares about the
speed or cost of — it must be an answer, not a default. The budgets are recorded as prose
in `docs/DESIGN.md` and as `bench/budgets.json` at configuration.

## Add at design.sections

### The mechanism and the hot path

For every **performance or cost budget** the design names the **mechanism** that meets it and the **hot path** it runs on — the index or data structure, caching, batching, streaming, concurrency, where the work happens, what is precomputed (`Performance-Conventions.md` §2). These are the choices that are cheap now and expensive after the build, so they are decided here, and `plan-critic`'s performance lens checks them against the stated data sizes.

## Add at planning.stages

For every **budget** the plan carries a **benchmark increment** — a benchmark in `bench/`
that drives the budgeted operation with a fixed dataset and seed and reports the metric —
scheduled in the stage where the operation first exists, so a baseline is committed before
anything is optimized (`Performance-Conventions.md` §3). From that stage on the checker
runs in the gate.

## Add at planning.critic-lenses

- **Benchmark increments (where budgets exist).** Is there a benchmark increment per
  budget, in the stage where the budgeted operation first exists, so a baseline is
  committed before any optimization? A budget with no benchmark in the plan is **Blocking**:
  it can never be checked.

## Add at delegation-loop.test-checks

Where budgets exist and their benchmarks are built, the **benchmark floor** runs with the
tests: `scripts/bench.ps1` then
`python ~/.claude/cursor-bridge/bench-check.py bench/budgets.json bench/baseline.json bench/results/latest.json`.
`OVER BUDGET`, `REGRESSION`, or `NOT MEASURED` is a correctness-class block: re-delegate
with the numbers in the brief, never route it to the user, and never fix it by loosening a
budget or moving the baseline (`Merge-Verification-Policy.md` §Anti-gaming). Write the
corrected brief from a **named cause**: profile the failing benchmark, match the hot spot
against `~/.claude/cursor-bridge/Performance-Patterns.md`, and put the entry's fix and
measure in the brief — never "make it faster". A hot spot that matches no entry goes through
`root-cause-first` like any other defect.
