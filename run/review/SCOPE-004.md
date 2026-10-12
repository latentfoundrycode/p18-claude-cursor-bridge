# TASK-004 — scope of the review (round 1)

Branch `task-004`, from `origin/main` f00f12e. The diff is `run/review/REVIEW-004.diff`, the branch's whole change against `origin/main`. The plan's §6.3–§6.11 are copied verbatim to `run/review/PLAN-6-004.md` (the plan itself lives outside the Workspace).

## What this increment is

Supervisor-authored governance text, not a builder run: release B's plan (docs/BUILD_PLAN.md, TASK-004, "Author: supervisor") assigns governance text to the supervisor and gates it by the two-critic design review (§15 condition 3). This round serves as both that design review and the merge gate. Grade findings as **Blocking**, **Should fix** or **Consider**, then give one verdict: APPROVE, REJECT or ESCALATE-INTENT.

## Scope (from docs/BUILD_PLAN.md, TASK-004)

- Scope: `bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/MANIFEST.json; tests/test_open_list.py`
- Satisfies: R-011
- Done when: every §6.3 product type, sub-type, and trait is listed with its definition, its default traits, its fixed workflow name / sub-workflow name, and a written/unwritten flag (all unwritten at first); the open list is the canonical source of a type's default traits (a type file's statement is checked against it by `workflow-check`); the §6.10 add/change procedure is recorded; `test_open_list.py` (names R-011) asserts each entry has definition, default-traits, name, and flag, and the file parses in the shape `workflow-check.py` reads.
- Standing constraints: MANIFEST.json regenerated on any `bridge/` edit; tests name their R-IDs; no hard line wraps in Markdown; the written flag is flipped by the later increments that write each file.
- Carried from TASK-003's round 2 (docs/DESIGN_CRITIQUE.md): the open list carries "a sub-type must earn its place" (§6.5), and its trait order is cross-checked against the order `bridge/commands/supervisor.md` states ("The order additions apply in").

## Choices the text makes that the plan leaves open (check them)

- **Workflow names.** §6.3 fixes the shape and gives two names (Game Development, Roblox Game, the owner's, 2026-10-01). The other type and sub-workflow names are the supervisor's, in the same shape (the file's "Names" section says so).
- **Keys.** Each entry has a lowercase hyphenated key that is also its workflow file's base name under §6.11's paths (`workflow/types/<key>.md`, `workflow/types/<type key>/<key>.md`, `workflow/traits/<key>.md`).
- **A sub-type's Default traits cell is the complete default set** for a part with that sub-type, in place of its type's (so the local web app has has-screens, installable, long-running-process and not personal-data, as §6.3 says "instead of personal data"; GUI adds has-screens to installable; local service adds long-running-process; Roblox adds multiplayer to the game's two). A sub-type §6.3 adds nothing to carries its type's set.
- **Planned column.** From §6.8 (release B writes web app + local web app, software on your own computer + local service, host extension + Claude Code extension, and the seven traits other than personal data and multiplayer), §6.8/§16 release E (video game, Roblox, multiplayer), §6.9 (iOS on a Mac); "when a project first needs it" for personal data; the rest "when the first project of this type arrives".
- **The table shape** `workflow-check.py` will read (TASK-006): each table found by its `##` heading, the first Markdown table under it, the columns named in "How this file is read".

## Out of scope (later increments; not this diff's defect)

- Any conditional workflow file (`workflow/types/...`, `workflow/traits/...`): TASK-017 onward; their written flags flip there.
- The extension-point registry (TASK-005); `workflow-check.py` itself and its reading of these tables (TASK-006); the `Workflows:` status line template (TASK-007); intake's classification questions in `supervisor.md` (a later intake-module increment).
- The digest is not touched.

## Tests the supervisor wrote

`tests/test_open_list.py` — enforces docs/BUILD_PLAN.md TASK-004 Done when and plan §6.3, §6.5, §6.7, §6.8, §6.10, §6.11; names R-011 (and R-034 for the order):
- the file at the §6.11 path, bounded, no CR characters;
- the three tables parse with exactly the stated columns, one heading each;
- every entry: well-formed unique key, name, definition, planned, written ∈ {yes, no};
- the eight product types in §6.3's order with workflow names and default traits as §6.3 states; Game Development pinned;
- the ten sub-types, each of its §6.3 type, with names and default traits; Roblox Game pinned; a sub-type §6.3 adds nothing to carries at least its type's defaults;
- every default trait names a listed trait;
- the trait order equals §6.3's and the order `supervisor.md` states, and "a trait added later goes at the end";
- every written flag is `no`;
- §6.8's release-B entries are planned for release B; video game, Roblox, multiplayer for release E; iOS on a Mac;
- the canonical-source sentence (checked by `workflow-check.py`);
- the intake tests, "a sub-type must earn its place", siblings, two levels, the §6.7 rules;
- the §6.10 procedure: four steps, the maintainer's session, the check, calibration reopening no gate, changing one, the supervisor never writes one, the promotion pass.
Against `origin/main` the file is absent, so every test fails. No mutation driver (a text test).

## Expected bookkeeping in the diff

`docs/PROJECT_STATUS.md` (position rewrite: TASK-003 merged at f00f12e, TASK-004 in progress), `docs/DESIGN_CRITIQUE.md` (TASK-003's round-4 record, which the post-merge records move puts on this branch), `docs/REQUIREMENTS.md` (R-011 → built with this test as evidence), `docs/INVENTORY.md` (feature rows for TASK-003's model and this open list), `bridge/cursor-bridge/MANIFEST.json` (the new file's hash), `run/review/` (these review files).
