# Performance Conventions — speed, memory, and money are budgets, and a budget is measured

"Optimization" in this file means one thing: making the software faster, lighter, or cheaper to run — latency, throughput, memory, startup time, artifact size, and money or tokens spent per operation. Simpler code is the minimal-code rule and the refactoring pass; this file is not about that.

The governing principle: **an optimization exists only if it is measured.** No target, no optimization. No baseline, no optimization. No before-and-after numbers, no optimization commit. Code made "faster" on intuition is code made more complicated for no proven gain, and a model is more prone to that than a person.

## 1. Budgets — set at intake, owned by the owner

A budget is a numbered, measurable statement of what "fast enough" or "cheap enough" means for one operation under one stated condition. They are product decisions, so the owner sets them at Phase 1 from defaults the supervisor proposes; the supervisor never invents them silently.

`bench/budgets.json` — the machine-readable source the checker reads:

```json
{
  "budgets": [
    { "id": "PERF-001", "benchmark": "search_10k_docs", "metric": "p95_ms",   "max": 2000, "tolerance_pct": 10,
      "description": "A search over 10,000 indexed documents answers within 2 s at the 95th percentile" },
    { "id": "PERF-002", "benchmark": "startup",         "metric": "ms",       "max": 1000, "tolerance_pct": 15,
      "description": "The application is usable within 1 s of launch" },
    { "id": "PERF-003", "benchmark": "sync_1k_files",   "metric": "usd",      "max": 0.50, "tolerance_pct": 10,
      "description": "Syncing 1,000 files costs at most $0.50 in model calls" },
    { "id": "PERF-004", "benchmark": "index_100mb",     "metric": "peak_mb",  "max": 1500, "tolerance_pct": 10,
      "description": "Indexing 100 MB of source peaks under 1.5 GB of memory" }
  ]
}
```

Rules: one budget per operation-and-condition; `max` for "lower is better" metrics (`ms`, `p95_ms`, `peak_mb`, `usd`, `tokens`, `bytes`), `min` for "higher is better" (`ops_per_s`); the condition (data size, corpus, device) is part of the benchmark's fixed dataset; the tolerance is the regression band the checker allows against the baseline (§3). The same budgets appear in `docs/DESIGN.md` as prose for the human reader.

**Cost is a budget like any other.** Money or tokens per operation are measured from the application's own accounting (which the design must expose in test mode), against recorded cassettes so the number is deterministic; a budget in `usd` uses the price table pinned in the project.

## 2. Design for the budgets — the choices that are cheap now and expensive later

For every budget, `docs/DESIGN.md` names the **mechanism** that meets it and the **hot path** it runs on: the data structure or index, caching, batching, streaming, concurrency, where the work happens (client, server, background), and what is precomputed. The plan critic's performance lens checks the design and the plan against the budgets:

- Does the chosen algorithm or query scale to the stated data size? An O(n²) step over 10,000 items, a full scan where an index is implied, a per-item network or model call inside a loop.
- Is anything unbounded — a list that grows with every operation, a cache with no eviction, a log kept forever in memory?
- Does the hot path block the UI thread or the request thread on IO?
- Is every budget's operation actually measurable in isolation (a benchmark can drive it with fixed inputs)? If not, the design changes until it is.
- Does the plan contain a **benchmark increment for every budget**, scheduled in the stage where the operation first exists — so a baseline exists before anything is optimized?

## 3. The benchmark floor — deterministic, in the gate

| Item | Requirement |
|---|---|
| Suite | `bench/` in the workspace: one benchmark per budget (plus any the supervisor adds), each driving the real operation with a **fixed dataset and fixed seed** under the project's test-mode determinism. Built by the builder as ordinary increments with acceptance criteria. |
| One command | `scripts/bench.ps1` (or the stack's runner) runs the suite and writes `bench/results/latest.json`: `{"generated": "<iso>", "commit": "<sha>", "results": [{"benchmark": "search_10k_docs", "metric": "p95_ms", "value": 1450}]}`. Each timed benchmark reports the **median of at least 5 runs** (noise on a desktop machine is real); memory reports the peak; cost reports the accounted total. |
| Baseline | `bench/baseline.json`, same shape, **committed**. It changes only in a commit that is an optimization (§5) or that deliberately accepts a slower result with the reason in the commit message. |
| Checker | `python ~/.claude/cursor-bridge/bench-check.py bench/budgets.json bench/baseline.json bench/results/latest.json` — for every budget: `OVER BUDGET` if the value exceeds `max` (or falls below `min`); `REGRESSION` if it is worse than the baseline by more than the tolerance; `IMPROVED` if better by more than the tolerance (a note: the baseline should move in an optimization commit); a benchmark named by a budget but missing from the results is `NOT MEASURED` and fails. Metrics with a baseline but no budget are still regression-checked. Exit `0` clean, `1` any failure, `2` cannot read. `--update-baseline` copies the results into the baseline and is used only inside an optimization commit. |
| Where it runs | In the CI `gate` job on every PR (a regression blocks like a failing test), and locally at every stage close before the pass in §5. Where CI runners are too noisy for a budget's absolute number, the budget is checked locally at stage close and CI checks the regression band only — say so in `PROJECT_STATUS.md`. |
| UI projects | The observability tests (Tier A) gain **load-time budgets**: time to first render and time to interactive for each inventory screen, measured by the driver (Playwright timing), recorded in the same results file. |
| Tooling per stack | Python: `pytest-benchmark` for timing, `tracemalloc` / `memray` for memory, `cProfile` / `py-spy` for profiles. Node: `--cpu-prof`, `autocannon` for servers, `process.memoryUsage()`. .NET: `BenchmarkDotNet`, `dotnet-counters`. Rust: `criterion`. Browser: Lighthouse / Playwright timing, bundle-size report. All pinned; none a runtime dependency of the product. |

## 4. Anti-gaming — a budget passes by getting faster, never by getting looser

Both reviewers treat as a gate-integrity flag: raising a `max` (or lowering a `min`) or widening a `tolerance_pct` in `budgets.json` without an owner decision recorded in `CHANGES.md`; updating `baseline.json` in a commit that is not an optimization with its numbers in the message; deleting or skipping a benchmark; shrinking the fixed dataset or changing the seed to make a number pass; measuring a warm cache where the budget stated a cold one. A budget the owner genuinely wants relaxed is a product decision — it goes through the change cycle's intake, not through an edit.

## 5. Optimization at stage close — the performance lens of the same pass

The stage-close pass (supervisor Phase 6 step 9) gains a second lens beside duplication. `refactor-scout` receives, in addition to its usual inputs, the latest benchmark results, the baseline, the budgets, and a profile of each budgeted operation (`scripts/profile.ps1 <benchmark>` writes `bench/profiles/<benchmark>.txt`). It looks for:

- a budget that is failing or within its tolerance band of failing;
- a hot spot in a profile that the stage's diff introduced or touched;
- the known patterns: repeated queries or model calls inside a loop, recomputation of an unchanged value, synchronous IO on a hot path, unbounded growth, serialization of large objects on every call, a missing index or the wrong data structure for the access pattern, blocking the UI thread.

It ranks candidates by **measured impact** on a budgeted metric — never by how elegant the change would be — and marks each with the benchmark that will prove it. Candidates then follow the pass's mechanics unchanged: one branch per stage, one small brief and one commit per candidate, the purity check (an optimization is behaviour-preserving; the tests do not change), and **one gate pass** for the whole branch. Two additions:

- **Every optimization commit carries its numbers.** The brief names the metric, the current value, and the target; the commit message states before and after (`search_10k_docs p95_ms 1450 → 910, budget 2000`); the same commit updates `bench/baseline.json` via `--update-baseline`. A commit whose measured gain is within the noise band, or that adds complexity without a measured gain, is **rejected** — the minimal-code rule wins.
- **Reviewers check the numbers, not the story.** `diff-reviewer` and Review B confirm the commit's before/after came from the checker's output on this branch, that the baseline change matches, and that no anti-gaming item (§4) occurred.

Beyond-budget candidates go to `docs/HARDENING.md` under the stage, as before.

## 6. Where it lands in the loop

- **Phase 1** — the supervisor proposes budgets from the stated performance, scale, and cost expectations and the platform; the owner sets them (a decision brief: what each number means for the user, what it costs to meet). Recorded in `bench/budgets.json` at configuration and in `DESIGN.md` as prose. A project with no operation the owner cares about the speed or cost of records "no budgets" and skips the floor — that is a legitimate answer, not a default.
- **Phase 2** — the mechanism and hot path per budget; `plan-critic`'s performance lens.
- **Phase 4** — a benchmark increment per budget, in the stage where the operation first exists; the checker in the gate from that stage on.
- **Phase 5** — `bench/budgets.json`, the runner script, the checker step in CI, the profiler pinned.
- **Phase 6** — the checker runs with the tests; a regression is a correctness-class block; the stage-close pass runs the performance lens.
- **Project end** — the User Manual states the budgets the software meets in plain language ("a search over ten thousand documents answers within two seconds"), because that is a promise the owner can hold the software to.
