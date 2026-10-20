## Project end

### Where this module begins

This module was carved out of the reflection points (`~/.claude/cursor-bridge/workflow/phases/reflection.md`) and runs after them: "items 1–5 above" and "the project-end items below" in its first paragraph are the reflection points' items 1 to 5, in that module, and this module's own items.

### The trigger and what project end adds

**Project end is a defined trigger, not a judgement.** The project has ended when the
**last stage of the approved build plan closes** — its last increment merged, its
refactoring pass (if on) merged. Deferred increments do not postpone it: they are listed as
deferred in the report and in `PROJECT_STATUS.md`, and the owner can reopen the project by
adding work (the phase returns to `building`; the manual is then patched at reflection
points as usual). At that stage close, run items 1–5 above and then the project-end items
below **in the same turn** (under `Stage pause: run`; under `pause`, they run before the
pause). Set `Phase: done` in `PROJECT_STATUS.md`. The report's first line is
**"Project complete — <Name> <version>"** followed by the one thing the owner owns, if any
(a deferred item to decide on, a release to publish); everything else is FYI. A project
whose last stage has closed without this having run is in the wrong state: run it now.

**At project end**, additionally:

- **Prove the product is complete — before anything else.** `python ~/.claude/cursor-bridge/completion-check.py --mode done` must print `RESULT: OK`: every requirement `built` with a test that names it, or deferred or dropped by the owner with a date; no stand-in ("arrives in a later stage", "coming soon", "not yet implemented", a placeholder screen) in shipped code unless it names an owner-deferred requirement. Any failure means the project has **not** ended, whatever the plan says: the missing requirement is planned and built as a new stage, or put to the owner as a deferral. The "Project complete" line lists every deferred and dropped requirement by ID and name.
- **Prove the diagrams hold at the end.** `python ~/.claude/cursor-bridge/diagram-check.py --mode done` must print `RESULT: OK` (rule 45): every enforcing test file exists, every component drawn is built, every `review:` item names its reviewer, and no deviation is still listed in `docs/diagrams/DEVIATIONS.md` (release A3).
- **Confirm the remote holds the release.** `python ~/.claude/cursor-bridge/sync-check.py --apply --strict` must print IN SYNC, or NO REMOTE for a project that never had one, before the "Project complete" line is written. Anything else is resolved before the project is declared finished: a project whose local copy lags the remote, or whose last commits never left the machine, is not finished.

- **Write `Documents/<Name> User Manual.md`** from the finished software and `CHANGES.md`:
  what it does, how to use each feature, screen by screen where there are screens, in the
  user's language, with the plain-language limits and known gaps. Tier B screenshots, where
  they exist, may illustrate it. From then on it is patched at reflection points (item 4).
  For **installable software** its first chapter is *Install, upgrade, uninstall*: where the
  deliverable is (`dist/<Name>-Setup-<version>-x64.exe`, or `install.cmd`, or the release
  asset), the SmartScreen note for an unsigned installer, what running it again offers
  (Upgrade / Uninstall / Cancel), and where the user's data lives and that uninstalling
  keeps it. For anything with a command-line surface the next chapter is the **command
  reference rendered from `docs/cli-reference.json`** — never written from memory.
- **Deliver the installer** (installable software): run the lifecycle verification one
  final time on the release build (per the `Installer verification` parameter), exercise the
  "already installed" dialog once interactively, then attach the deliverable as a GitHub
  Release asset where a remote exists, or name its path in the report and the manual where
  there is none.
- **Run the promotion pass.** Read the Issues document and the Feedback document whole, and
  draft — as a final section of the Feedback document titled **"Proposed bridge changes"** —
  concrete proposed edits: which file in the governance tree, what wording, and which issue or
  feedback item motivates each. That section is a proposal for the maintainer to accept or
  reject; you change nothing in the bridge. (This replaces any automated skill optimiser: the
  scoring here is the maintainer's judgement, and the loop stays human-approved.) The same
  section proposes **Performance-Patterns entries**: for every optimization commit whose
  before/after numbers proved a pattern the catalogue lacks (`PP-new` in the scout's
  output) or sharpened one it has, draft the entry in the catalogue's shape — pattern,
  symptom, fix, measure, applies to — with this project, the commit, and the numbers as
  evidence. The admission rule applies: recurring across projects or plainly will, not
  already covered, measurable.
