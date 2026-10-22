## Project end

### What must survive a compaction

After a compaction or a resume at project end, read these before your next action:

- this module and `reflection.md`, each whole: project end runs after the reflection points' items 1 to 5 at the last stage's close, in the same turn;
- the last entries of `run/supervisor/in-flight.md`: the project-end items finished so far ("Keeping the position");
- `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, whole (rule 41): the `Workflows:` lines name each part's conditional workflows, whose additions at `project-end.completion-conditions` and `project-end.delivery` this module runs, and the deferred increments the status file lists are the ones the report lists; the inventory's `Delivery kind:` rows give each part's delivery kind, and its `Flagged trait:` rows the traits the promotion pass puts forward;
- `docs/REQUIREMENTS.md`, `docs/CHANGES.md` and `docs/RUN_PARAMETERS.md`: the completion check reads the register, whose deferred and dropped requirements the "Project complete" line lists by ID and name, the User Manual is written from the change log, and the installer's last verification follows the `Installer verification` parameter;
- the Issues and Feedback documents under `Documents/`, whole: the promotion pass reads both and writes its proposals as the Feedback document's last section.

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

### Flagged traits in the promotion pass

The promotion pass reads a third source beside the Issues and Feedback documents: every row of `docs/INVENTORY.md` → Decisions that begins `Flagged trait:`, written at the design gate for a new trait or one defined but not yet written, whose handling the project's design carries (`design.md`, "Traits at the design gate"). For each, "Proposed bridge changes" proposes the trait as the maintainer could write it: for a new trait, its entry in the open list (`~/.claude/cursor-bridge/workflow/open-list.md`), with its definition; for a new trait and an unwritten one alike, its additions, each under the `## Add at <point key>` heading of the extension point at which the project's design handled it, drafted from that handling and naming the design section and the row they come from. Each is written in general terms, for every project the trait may reach: no path of this computer, no key and none of the project's data (rules 53 and 54); and each proposed file stands in a fenced block whose first line reads `Proposal — not in force`, so that no later reading of the Feedback document takes its `## Add at` headings for additions in force. The maintainer writes the trait or not; you write no trait file and change nothing in the open list (the open list, "A new trait is flagged, and the work continues").

### Keeping the position

Keep the position as the reflection points keep theirs (`reflection.md`, "Keeping the position"): as each item above finishes, one line in `run/supervisor/in-flight.md` naming it, so that a resume after a compaction starts at the next item and writes nothing under `Documents/` twice.

## Extension points

This module offers the points below, each by its key in the extension-point registry (`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and whether it applies per part or per project. A conditional workflow's additions at a point are made where the point's line places them, in the order the core states in "Main and conditional workflows".

- `project-end.completion-conditions` — completion conditions a conditional workflow adds for the part, each checked with "Prove the product is complete" above, before anything else at project end: a condition not met means, as a failure of `completion-check.py` does, that the project has not ended; a condition the plan must build toward is also added at intake (`intake.requirement-sources`), as the registry says.
- `project-end.delivery` — the delivery procedure for the part's delivery kind, which an addition names (`## Add at project-end.delivery for <kind>`) and which runs for each part whose `Delivery kind:` row in `docs/INVENTORY.md` names that kind, beside "Deliver the installer" above and before the promotion pass; the report and the User Manual name what was delivered and where it is.
