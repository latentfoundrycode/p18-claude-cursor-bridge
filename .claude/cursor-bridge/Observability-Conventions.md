# Observability & Verifiability Conventions — Bridge

The gate today sees the diff, the static mockup, and the test results — never the **running,
rendered app**. So a build can pass the detector, `design-auditor`, and the tests and still
render `[object Object]`, a collapsed layout, an untranslated key, or a mockup-promised state
the real app never reaches. This convention closes that gap by giving the gate a view of the
running render — as **measurable checks**, not a screen for the human to eyeball.

It is a **design-time default for UI-bearing projects** (those that produced a Phase-1
screen-and-state inventory), **not a universal law**: a CLI or library has no inventory and
opts out. The **supervisor owns the dial** and records the choice in Phase 2
(`DESIGN.md`/`PROJECT_STATUS.md`); it escalates to the user only where a new dependency/cost is
involved (drivers — see §Escalations). This doc is the master contract; each project
instantiates it as a **`DESIGN.md` "Observability & Verifiability" section**.

---

## Two tiers

- **Tier A — deterministic runtime observability (the default for UI-bearing projects).**
  Runtime invariant assertions + a state-reachability contract + structured logs, exercised by
  observability tests. Deterministic pass/fail; extends the executable floor.
- **Tier B — screenshots as `design-auditor` evidence (opt-in; the supervisor's dial for
  higher-stakes UI).** The tests capture screenshots that `design-auditor` may consult for its
  *existing* mockup-fidelity judgement. **Not** a pixel diff and **not** a new reviewer.

A trivial 2-screen tool takes Tier A (assertions) and skips Tier B; a data-dense product with
many states takes both. Record which in `PROJECT_STATUS.md`.

---

## The reachability contract (product — Cursor builds; supervisor drives)

**Every state in the Phase-1 screen-and-state inventory must be reachable by the supervisor's
observability driver *through the real render path*** — so a clean screenshot/assertion proves
the *real* path renders, not a parallel reconstruction. The contract is platform-agnostic; the
**mechanism is platform-appropriate**:

- **Web:** deep-linkable URLs (already a Vercel MUST) + a browser driver. The URL *is* the
  shared path.
- **Mobile / desktop:** a **scriptable shared action/command path the GUI itself dispatches
  through** — so the driver reaches a deep state the same way a user's taps/clicks do. This is
  where a shared action path earns its place (there is no URL, and scripting raw interactions
  to a deep state is fragile). Do **not** build a parallel CLI that rebuilds state its own way —
  the point is the *shared* path.
- **Any platform — last resort only:** a **test-mode-only** hook to set an otherwise-unreachable
  state, **compiled out of production** (ASVS V13 — no debug endpoints in prod, or it is a
  backdoor). Mark these explicitly and keep them few.

The **supervisor** drives this (a review input; **never Cursor** — Cursor must not observe its
own work). In practice the supervisor navigates by authoring and running the observability
tests (below); its own browser tools are fine for an ad-hoc look, but the *gate* is the
reproducible tests.

---

## The instrumentation contract (product — Cursor builds, brief-specified)

Cursor implements these as product features; the brief specifies them:

- **Structured JSON logs** — greppable, one event per line. **Never log secrets/PII** (already
  required by `secure-coding.mdc`, ASVS V14/V16) — redact at the logging boundary.
- **Dev/test-mode invariant assertions** — the app *throws* (or fails the run) rather than
  rendering a defect, so the check is deterministic instead of OCR'd off a screen. Baseline
  catalogue (extend per project):
  - no `undefined` / `NaN` / `[object Object]` / `null` rendered into visible text;
  - no untranslated i18n key rendered (raw `key.path` in the DOM/label);
  - **`console.error` (or the platform equivalent) fails the run**;
  - no unhandled promise rejection / uncaught error during a driven flow.
  These are **dev/test-mode only** — never change production behaviour.
- **A state-dump command on the same action path** — emits the current app state as JSON, so a
  test can assert on state, and logs-vs-render mismatches can be diagnosed.
- **Fixed clock / seed / locale in test mode** — so screenshots and state dumps are comparable
  across runs (no wall-clock, no random, one locale unless the test sets it).

---

## The observability tests (reviewer — the supervisor writes them)

Reviewer-independent per N4 (the supervisor may write tests; tests authored by the reviewer are
worth more). They **drive the app to each inventory state through the real path** and assert:
no invariant fired, no `console.error`, the state-dump matches expectations, the required
empty/sparse/dense/error states exist. Tier B additionally **captures a screenshot per state**
(comparable thanks to fixed clock/seed/locale) for `design-auditor`.

They run **on demand, under `test-runner` and the CI `gate` job** — spin the app up, drive,
assert, tear down, within one invocation. **No daemon** (N1): this is an e2e/integration test,
not a watcher. The one product requirement it implies: the app must be **startable headlessly
and reproducibly** in CI (a build + serve/launch command).

---

## Where it sits in the gate (N7 — extend, don't duplicate)

- **Deterministic floor — NEW coverage.** The runtime invariant assertions + reachability are a
  running-render correctness class the static detector and the Vercel-rules-on-diff cannot see.
  A fired invariant, a `console.error`, or an unreachable inventory state is a **correctness
  block** — re-delegated like any REJECT, never a user question.
- **Judgement — existing, richer evidence.** Tier B screenshots feed `design-auditor`'s
  *existing* mockup-fidelity pass — **same verdict classes, better input.** No pixel diff, no
  second design reviewer, no new subagent.

## Author/reviewer split (N4) and single-actor (N5)

- **Product (Cursor builds):** reachability support, instrumentation, invariant assertions,
  state-dump, test-mode fixed clock/seed/locale. The invariant *contract* is the brief's;
  Cursor implements; the supervisor's tests verify.
- **Reviewer (supervisor writes/runs):** the observability tests + the driving. Cursor never
  drives its own observation.
- Artifacts (screenshots/logs) are **not product-tree changes** — they land in a gitignored
  artifacts dir, never committed.

---

## Secret surface (a new runtime surface — guard it)

A log line or screenshot can expose a secret, and `secret-sentinel` guards diffs, not runtime
output. Layered guards:
1. **Test-mode synthetic data + fixed seed** — driven states contain no real secrets/PII.
2. **Gitignored, ephemeral artifacts** — screenshots/logs never reach history.
3. **`secure-coding.mdc` "never log secrets/PII"** (ASVS V14/V16) — product-side, already in
   force.
4. **`secret-sentinel` scans retained runtime logs** for secret shapes before they enter the
   supervisor's context (extension of its remit — see `secret-sentinel.md`).
Plus: **test-mode reachability hooks are compiled out of production** (ASVS V13) or they are a
backdoor.

---

## Drivers & escalations (the user's calls)

- **Web:** a browser driver (**Playwright** recommended), **run in CI on Linux** (primary),
  local optional — mirrors the Semgrep-in-CI posture. New dependency + CI minutes.
- **Mobile / desktop:** a platform driver (Appium / WinAppDriver / Playwright-for-Electron) —
  heavier deps + CI runners. Adopt per-platform; for a first cut, gate the web path fully and
  treat mobile/desktop reachability as Tier-A-where-a-driver-exists.
- **Assertions:** hand-rolled predicates (no new dependency) — the invariants are simple.
- These are dependency/cost decisions → the supervisor escalates them to the user like any
  dependency, at Phase 2/Configure; everything else here it decides and records.

---

## Resumability

Record in `PROJECT_STATUS.md`: the observability **tier**, the **driver + pinned version**, the
**invariant set** in force, and the **state → reachability-mechanism map**. A resumed session
must know what is being asserted and how each state is reached.

---

## The per-project `DESIGN.md` "Observability & Verifiability" section

Each UI-bearing project's `DESIGN.md` instantiates this doc: the **inventory states** and, per
state, its **reachability mechanism** (URL / action-path command / test-hook); the **invariant
list** (baseline + project-specific); and the **log / test-mode / redaction conventions**. This
section is what `spec-packager` cites in UI briefs and `plan-critic` checks for.
