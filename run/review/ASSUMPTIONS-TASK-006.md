# ASSUMPTIONS-TASK-006

The builder's `Assumed, not verified` list (handoff/TASK-006-r1-report.md), with the supervisor's disposition of each (from the accept commit's message). Extra places to look, never the review's scope.

- A change heading is one whose first word is exactly `Add`, `Set` or `Replace`; the brief's example `## Adds at x` (listed as form) contradicts its definition (a heading "whose next word is Add, Set or Replace") → **council: the reviewers are asked** whether a misspelt change word (`## Adds at`, `## Sets at`, `## Replacing`) read as prose, so that a conditional workflow's change silently does nothing, is a defect of this increment.
- A fence is a line starting with three backticks at column 0 → accepted (the brief's wording; an indented fence is not a fence).
- A change heading with trailing spaces is form → accepted (the four forms are exact).
- The traits text is stripped before reading `none` → accepted (a trailing space cannot change a name).
- A Workflow name is matched before a Sub-workflow name and a trait Name → accepted (no name is in two tables of the open list).
- An unknown head name that leaves no product type also gives (e) → accepted (Requirement 4's e includes a part with no product type).
- A folder deeper than `types/<t>/` is form itself, and so is each file under it → accepted (Requirement 6).
- Spaces inside a backticked delivery kind are kept → accepted (the value then fails as kind).
- `types/<t>.md` exists by `os.path.isfile`, case-insensitive on Windows → accepted (CI also runs on Linux, case-sensitive).
