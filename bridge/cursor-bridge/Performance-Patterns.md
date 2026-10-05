# Performance Patterns — the bridge's catalogue of recurring causes of slowness and cost

A companion to `Known-Pitfalls.md`, with the same discipline: **small, generalizable, evidence-backed, maintained by the maintainer.** Each entry is one recurring cause of slowness, memory growth, or spend, in a fixed shape — pattern, symptom, fix, measure, applies to, evidence — so the three readers below can use it mechanically.

**Who reads it, and when**
- **`plan-critic`** at Phase 2 checks each budgeted mechanism in `docs/DESIGN.md` against the patterns and flags a design that walks into one before it is built.
- **`refactor-scout`**'s performance lens at stage close uses the *symptom* column as its search list over profiles and the stage's diff, and names the matching entry (`PP-nnn`) in each optimization candidate.
- **The supervisor**, when the benchmark floor fails in the gate, writes the corrected brief from the named pattern and its fix, not from "make it faster".

**What it is not.** A pattern here never justifies a change on its own. A change happens only with a budget behind it and a benchmark proving it (`Performance-Conventions.md`); the catalogue says what to look for and how to prove it, the numbers decide.

**Admission rule.** An entry enters only if it recurs across projects (or plainly will), is not covered by an existing entry, and has a fix that can be measured. A pattern seen once stays in that project's Issues file. Entries come from two sources: the seed below (from the performance guides every stack shares), and the **promotion pass** at project end, which proposes an entry for any optimization commit whose before/after numbers proved a pattern, with the project and the numbers as evidence — the owner approves it into this file. Prune entries a later stack change makes obsolete.

---

### PP-001 — A query or remote call per item inside a loop (the N+1 pattern)
- **Pattern:** the code fetches a set, then for each element issues another database query, HTTP request, or model call.
- **Symptom:** time grows linearly with item count; the profile shows thousands of short calls to the same function; a cost meter shows one billed call per item.
- **Fix:** fetch the whole set in one query (a join or an `IN` list), or batch the remote calls (the API's batch endpoint, or a bounded concurrent pool); the loop then works on in-memory results.
- **Measure:** the budgeted operation at the stated item count; expect time (or cost) to stop scaling with the count.
- **Applies to:** any stack with a database, an HTTP API, or a model API in the loop.
- **Evidence:** every ORM and API vendor performance guide; the most common cause of a failing latency or cost budget.

### PP-002 — Full scan where the access pattern wants an index or a map
- **Pattern:** a lookup by key or a filter runs over the whole collection or table each time (`for x in rows: if x.id == wanted`, a `WHERE` on an unindexed column, `list.index` in a hot loop).
- **Symptom:** time grows with the size of the whole dataset rather than with the size of the result; the profile shows a scan function dominating.
- **Fix:** build the index once (a database index on the filtered column; a dictionary or set keyed by the lookup field; a sorted structure for range queries) and look up through it.
- **Measure:** the budgeted operation at the stated dataset size; expect near-constant time per lookup.
- **Applies to:** any stack; databases, in-memory collections, file indexes.
- **Evidence:** database indexing guides ("Use The Index, Luke"), every language's collections documentation.

### PP-003 — Recomputation of an unchanged value
- **Pattern:** an expensive result (a parse, a hash, a rendered template, an embedding, a config read) is computed again on every call although its inputs did not change.
- **Symptom:** the profile shows the same expensive function called far more often than its inputs change; identical arguments repeat.
- **Fix:** compute once and keep it — a memoized function, a cached property, a precomputed table at startup, a persisted artifact keyed by a content hash — with an explicit invalidation rule.
- **Measure:** the budgeted operation on a repeated workload; expect the expensive function's call count to drop to the number of distinct inputs.
- **Applies to:** any stack. Note PP-005: the cache must be bounded.
- **Evidence:** standard in every performance guide; embeddings and model calls are the costly case in AI-backed projects.

### PP-004 — Synchronous input-output on a hot path
- **Pattern:** a request handler, a UI event, or a per-item step waits on disk, network, or a subprocess before continuing, one at a time.
- **Symptom:** wall-clock time far exceeds CPU time; the profile shows waiting; throughput is limited by latency per call rather than by work.
- **Fix:** move the wait off the hot path (async IO with bounded concurrency, a background worker, a queue), or batch the IO; on a UI, never on the interface thread (PP-007).
- **Measure:** the budgeted throughput or latency; expect wall-clock time to approach CPU time or the slowest single IO, not their sum.
- **Applies to:** servers, CLIs over many files, anything calling external services.
- **Evidence:** Node, Python asyncio, and .NET async guidance; the dominant cause of "fast machine, slow program".

### PP-005 — Unbounded growth: a cache, buffer, or list that only grows
- **Pattern:** items are appended or cached and never evicted — a results cache with no size limit, a log kept in memory, a list of everything ever seen.
- **Symptom:** memory rises with uptime or with items processed and never falls; a long run gets slower (garbage collection) then fails; the peak-memory budget breaks only on large inputs.
- **Fix:** bound it — an LRU cache with a size, a ring buffer, streaming instead of accumulating, writing through to disk — and free what is no longer referenced.
- **Measure:** the peak-memory benchmark on the stated input size and on 10× that size; expect the peak to plateau.
- **Applies to:** any long-running process, batch jobs over large inputs, servers.
- **Evidence:** the standard cause of memory budgets failing late; every memory-profiling guide.

### PP-006 — Serializing or copying large objects on every call
- **Pattern:** a large structure is converted to JSON, deep-copied, re-encoded, or passed through a process boundary on each operation although only a small part is needed.
- **Symptom:** the profile shows serialization, encoding, or copy functions high in the list; time scales with the object's size, not with the work.
- **Fix:** pass references or views, serialize once and reuse, send only the needed fields, use a binary or streaming format at the boundary.
- **Measure:** the budgeted operation with a large payload; expect time to stop scaling with payload size.
- **Applies to:** APIs, worker boundaries, IPC, anything with a JSON layer.
- **Evidence:** serialization guides for every stack; common in Electron and Python multiprocessing designs.

### PP-007 — Work on the interface thread
- **Pattern:** a UI performs parsing, indexing, network waits, or heavy rendering on the thread that draws and handles input.
- **Symptom:** the interface freezes or stutters during an operation; the observability driver's time-to-interactive budget fails; input events queue up.
- **Fix:** move the work to a worker (a web worker, a background thread, a separate process) and post results back; render progressively.
- **Measure:** time-to-interactive and frame timing for the affected screen state under the stated data; expect the interface to stay responsive while the work runs.
- **Applies to:** desktop and web UIs, mobile.
- **Evidence:** every UI framework's threading guidance.

### PP-008 — Per-item model calls where one batched or cheaper call would do (cost)
- **Pattern:** an AI-backed step calls the model once per item, re-sends an unchanged long context on every call, or uses the most capable model for a task a smaller one handles.
- **Symptom:** the cost meter scales with item count; token counts show the same prefix billed repeatedly; the cost budget fails while latency looks fine.
- **Fix:** batch items per call where the task allows; cache the unchanged prefix (prompt caching); route by task to the cheapest adequate model; cut the context to what the task needs.
- **Measure:** the accounted cost of the budgeted operation against recorded cassettes; expect cost per item to fall and the billed prefix to be cached.
- **Applies to:** any project spending on model calls.
- **Evidence:** model vendors' cost guidance (caching, batching, routing); the Technical Documentation Provider's own sync-cost accounting.

### PP-009 — Startup does everything eagerly
- **Pattern:** the program imports, connects, loads models, or scans directories at launch that only some commands or screens need.
- **Symptom:** the startup budget fails; the profile of `--version` or of the first screen shows work unrelated to it.
- **Fix:** lazy-load by command or screen; defer connections until first use; precompute at build time what is static.
- **Measure:** the startup benchmark; expect launch time to be independent of features not used.
- **Applies to:** CLIs, desktop apps, servers.
- **Evidence:** CLI and desktop framework startup guides; the usual cause of a slow `--version`.

---

*Promoted entries go below this line with their project, commit, and before/after numbers as evidence.*
