# Has screens

## Add at intake.questions

For every **UI-bearing** feature, capture a **screen-and-state inventory** — the screens
it needs and, for each, the states that must exist: empty, sparse, dense, and error. This
is what makes the mockup (Phase 3) complete rather than a happy-path shell, and it is what
each screen's mockup is later mapped back onto.

## Add at design.sections

For a UI-bearing project, record in `docs/INVENTORY.md` (Decisions) whether the stack is
**React/Next** (Vercel's React-specific interface items apply in full) or otherwise (the
framework-agnostic subset applies), and the **styling approach**. A resumed session needs
to know which interface ruleset is in force.

### The Observability & Verifiability section

Also for a UI-bearing project, add an **"Observability & Verifiability" section** to `docs/DESIGN.md`, instantiating `~/.claude/cursor-bridge/Observability-Conventions.md` (read it by that absolute path). It records, per Phase-1 inventory state, its **reachability mechanism** (deep-link URL on web; a shared scriptable action path on mobile/desktop; a test-mode-only, prod-compiled-out hook only as a last resort — so your observability driver can reach every state *through the real render path*); the **runtime invariant list** (baseline: no undefined/NaN/`[object Object]`/untranslated-key rendered, `console.error` fails the run, plus project-specific); and the log/test-mode/redaction conventions. **Choose the tier** and record it: Tier A (deterministic assertions + reachability — the default) always; Tier B (screenshots as `design-auditor` evidence) at your discretion for higher-stakes UI.

## Add at interface.variants

A part with this trait runs the interface phase's mockups variant for its screens, `~/.claude/cursor-bridge/workflow/phases/interface/mockups.md`: the variant this trait activates, an addition and never a replacement. Design quality is measured, never asked (founding rule N7), and the running render is part of the gate (N9); both rules stay in the core, and the additions below are where the loop carries them out: the approved mockup and the frozen interface rules in every brief, the design auditor at the inspect step, the observability tests at the test step.

## Add at planning.acceptance-criteria

Each **UI-bearing** increment additionally **cites the approved mockup screen(s) and the
relevant `docs/design/DESIGN.md` sections** it implements, and carries **design acceptance
criteria** beside its functional ones ("matches mockup screen X", "passes
`impeccable detect` with no primary findings", "satisfies the relevant Vercel
interaction/forms items"). Where the increment adds or changes a screen-state, it also carries
**observability acceptance criteria** (Tier A): "state X is driver-reachable through the real
render path", "the observability test for X passes — no fired invariant, no `console.error`",
"required empty/sparse/dense/error states present" — checkable, not "renders fine".

## Add at planning.critic-lenses

- **Design criteria (UI increments).** Does each UI-bearing increment cite an approved
  mockup screen and the relevant `docs/design/DESIGN.md` sections, and are its design
  acceptance criteria actually checkable (a specific observable outcome — "matches mockup
  screen X", "passes `impeccable detect` with no primary findings") rather than "looks
  good"?
- **Observability criteria (UI increments).** Does each increment that adds/changes a
  screen-state carry checkable observability criteria — the state is driver-reachable through
  the real render path, its observability test passes (no fired invariant, no `console.error`),
  the required empty/sparse/dense/error states exist — rather than "renders fine"? Is each
  state's reachability mechanism named in `docs/DESIGN.md`'s Observability section?

## Add at configuration.items

For a UI-bearing project, also work the **design-tooling** steps in
`Cursor-Project-Configuration.md` §5b: the configurator writes `.impeccable/config.json`,
the frozen `.cursor/rules/vercel-interface.mdc`, and the second `afterFileEdit` detect hook.
**You** run the Vercel fetch-and-freeze here (validate the fetch or fall back to the bundled
`~/.claude/cursor-bridge/vercel-interface.snapshot.md`, and hand the configurator the
frozen body), pin the Impeccable CLI version, and record both source date and pinned
version in `docs/INVENTORY.md` (Resources). None of this escalates — it is all local, file-based,
Apache-2.0/MIT, no secrets.

For a UI-bearing project, also work the **observability** steps in
`Cursor-Project-Configuration.md` §5d (per `~/.claude/cursor-bridge/Observability-Conventions.md`):
the configurator wires the observability e2e tests into the CI `gate` job, sets test-mode fixed
clock/seed/locale, gitignores the screenshot/log artifacts, and confirms logs redact secrets.
**You** write the observability tests (they are reviewer-independent, like any test you author);
the instrumentation + reachability they exercise is product code Cursor builds from the brief. A
fired runtime invariant, a `console.error`, or an unreachable inventory state is a
correctness-class block, re-delegated like any REJECT — never a user question. The one
escalation is the **driver dependency** (Playwright for web, CI-primary; a per-platform driver
for mobile/desktop) — a new dependency, admitted and recorded under the one dependency rule
(rule 56), put to the user only for the consequence they bear. Record the tier,
driver + version, invariant set, and state→reachability map in `docs/INVENTORY.md` (Resources).

## Add at delegation-loop.inspect-checks

For a **UI-bearing** diff, also delegate to **design-auditor** after `diff-reviewer` — it
reviews design conformance (mockup fidelity, visual system, the frozen interface rules)
that `diff-reviewer` deliberately leaves alone. A **blocking** design finding re-delegates
like any correctness `REJECT` (a corrected brief, step 7) — it does **not** escalate.
**Advisory** findings go to `docs/CHANGES.md`, not a re-delegation.

## Add at delegation-loop.test-checks

For a UI-bearing increment, the tests you write include the **observability tests** (Tier A):
drive the app to each affected inventory state *through the real render path* and assert no
runtime invariant fired, no `console.error`, and the required states exist (see
`~/.claude/cursor-bridge/Observability-Conventions.md`). These run under `test-runner`/CI like
any test — no daemon. A fired invariant / `console.error` / unreachable state is a
**correctness-class block** (re-delegate, step 7), never a user question. If Tier B is on, the
tests capture per-state screenshots; hand those to **design-auditor** as evidence for its
existing mockup-fidelity judgement (they do not add a new pass).

## Add at delegation-loop.brief-constraints

### The approved mockup and the frozen rule

For a UI-bearing increment, the brief must name the exact approved mockup file(s) and the relevant `docs/design/DESIGN.md` sections, and list the frozen `vercel-interface.mdc` as an applicable rule.
