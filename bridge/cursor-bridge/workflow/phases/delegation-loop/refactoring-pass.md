## The refactoring pass (Phase 6, step 9)

This file is a sub-file of the delegation-loop module (`delegation-loop.md`, "The procedure"), read whole with it. It holds the loop's step 9, which runs at a stage's close, before the stage's reflection point (`reflection.md`), when `docs/RUN_PARAMETERS.md` turns the refactoring pass on for the stage.

### 9. Refactoring and optimization pass (at stage close)

When the last increment of a stage has merged and `docs/RUN_PARAMETERS.md` says
**Refactoring pass: on** for that stage, run one refactoring pass **before** the stage's reflection point.
"Refactoring" means one thing here: removing duplication or simplifying code while keeping
the same functionality. Every per-increment review saw one diff at a time, so a helper
written twice in two increments was invisible to both; this is the only step that looks at
the stage as a whole. Cursor's runs are cheap; the gate is not — so the pass is designed
around **one gate pass per stage**. **Normative diagrams are constraints on it:** a candidate that would change what a diagram draws — a component boundary, a class a Level 4 diagram fixes, a schema — is a design change, raised as an objection, never slipped in as a refactoring.

1. **Deterministic floor.** Run the duplicate detector over the source tree and the
   project's linter complexity rules in report-only mode:
   ```bash
   npx --yes jscpd@<pinned> <src-dirs> --min-lines 5 --min-tokens 50 --reporters json --output docs/refactor/<stage> --silent
   ```
   Record the pinned `jscpd` version in `docs/INVENTORY.md` (Resources); verify-first on the first
   use (KP-008). The report is input for the scout, not a verdict.
2. **Scout.** Delegate to **refactor-scout** with the stage base commit, the detector
   report, the complexity report, and the size budget (default **400 changed lines**) —
   and, where budgets exist, the **performance inputs**: `bench/budgets.json`,
   `bench/baseline.json`, the latest `bench/results/latest.json`, and a profile of each
   budgeted operation (`scripts/profile.ps1 <benchmark>` → `bench/profiles/<benchmark>.txt`;
   `Performance-Conventions.md` §5). It returns two ranked lists — refactoring candidates
   and **optimization candidates ranked by measured impact on a budgeted metric**, each
   naming the benchmark that will prove it — marked COVERED or UNCOVERED, costed in lines,
   cut at the size budget together. **NO CANDIDATES** is a normal result — skip to the
   reflection point.
3. **Cover first.** For an UNCOVERED candidate you want, write characterization tests that
   pin its current behaviour (you may write tests), run them green, and **commit them on
   `main` through the gate before the refactoring branch is cut** — so they sit under the
   base ref and the purity check does not see them as test edits. Or skip the candidate.
3b. **The test-infrastructure lane.** Duplication in the *tests* — helpers copied across
   test files — is yours to consolidate, since you own the tests. Do it in its own commit on
   the same branch, checked with `refactor-check.py <base> --lane tests` (no production file
   may change) and by proving the **collected test set is identical** before and after
   (`pytest --collect-only -q` or the stack's equivalent, diffed). Never mix it into a
   production-lane commit; the two lanes share the one gate pass.
4. **One branch, many small commits.** Cut `refactor/<stage>` from `main`. For each
   candidate, in payoff order: package a **refactoring brief** (`handoff/REFAC-<nnn>.md`,
   spec-packager's refactoring variant), delegate, inspect (git-derived changeset + scope
   check as always), run the full test suite, and commit that candidate alone. A candidate
   that fails its tests or drifts is re-delegated or dropped — a Cursor round is cheap,
   so be strict. Never mix a candidate into a feature increment.
   An **optimization candidate** is a refactoring candidate with numbers: its brief names
   the metric, the current value, and the target; its commit message states before and
   after; the same commit moves `bench/baseline.json` with `--update-baseline`; a gain
   inside the tolerance band, or complexity added without a measured gain, is dropped — the
   minimal-code rule wins. Never touch `bench/budgets.json`, a benchmark, its dataset, or
   its seed in this pass.
5. **Purity check — deterministic, before any reviewer:**
   ```bash
   python ~/.claude/cursor-bridge/refactor-check.py main --max-lines 400
   ```
   It fails the branch on any test-file change (unless a mechanical rename was listed in
   the brief with `--allow-test`, which the reviewer must then read), on any
   `docs/CHANGES.md` change, or on exceeding the size budget. `IMPURE` never reaches a
   reviewer: drop or fix the offending commit first.
6. **One gate pass.** The whole branch goes through step 8 once as a single pure
   refactoring diff: `diff-reviewer` in refactoring mode (behaviour preservation, every
   caller updated, no smuggled behaviour change), `secret-sentinel`, `security-auditor` or
   `design-auditor` only if the diff touches their surface, CI, and Review B with the
   explicit question "is this behaviour-preserving?". Merge as one squash. No
   `CHANGES.md` entry — there is no behaviour change to log; the refactoring is noted in
   the Project Summary at the reflection point instead.
7. **Beyond budget** candidates go to `docs/HARDENING.md` under the stage name, and are
   the first thing the next stage's scout reads.

The pass never escalates. It never introduces an abstraction for hypothetical reuse, never
touches a required security, observability, or accessibility control because it "looks
repetitive", and never changes a public interface other callers use unless every caller is
inside the diff. At **project end** run one final pass over the whole tree before the User
Manual is written.
