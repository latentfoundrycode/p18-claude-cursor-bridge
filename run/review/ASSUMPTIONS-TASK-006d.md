# ASSUMPTIONS-TASK-006d

The builder's `Assumed, not verified` list (handoff/TASK-006-r1-report.md), with the supervisor's disposition of each (from the accept commit's message). Extra places to look, never the review's scope.

- (Round 1, answered by both reviewers: a defect; corrected in round 2, R2-1.) A change heading is one whose first word is exactly `Add`, `Set` or `Replace`; the brief's example `## Adds at x` (listed as form) contradicts its definition (a heading "whose next word is Add, Set or Replace") → **council: the reviewers are asked** whether a misspelt change word (`## Adds at`, `## Sets at`, `## Replacing`) read as prose, so that a conditional workflow's change silently does nothing, is a defect of this increment.
- A fence is a line starting with three backticks at column 0 → accepted (the brief's wording; an indented fence is not a fence).
- A change heading with trailing spaces is form → accepted (the four forms are exact).
- The traits text is stripped before reading `none` → accepted (a trailing space cannot change a name).
- A Workflow name is matched before a Sub-workflow name and a trait Name → accepted (no name is in two tables of the open list).
- An unknown head name that leaves no product type also gives (e) → accepted (Requirement 4's e includes a part with no product type).
- A folder deeper than `types/<t>/` is form itself, and so is each file under it → accepted (Requirement 6).
- Spaces inside a backticked delivery kind are kept → accepted (the value then fails as kind).
- `types/<t>.md` exists by `os.path.isfile`, case-insensitive on Windows → accepted (CI also runs on Linux, case-sensitive).

Round 2 (handoff/TASK-006-r2-report.md):
- `os.walk`'s `onerror` receives an `OSError` naming the unlistable folder, and recording it ends the run at exit 2 → test (`test_r014_unreadable_folder_stops_the_check`, POSIX-only, run on CI's ubuntu leg; the supervisor reads that job's log before the merge).

Round 3 (handoff/TASK-006-r3-report.md):
- An `OSError` from `os.lstat` in the Windows fallback counts the path as a link → accepted (fail closed, as R3-7 says).
- A part bounded by a tab or other whitespace `str.strip()` removes is invalid like a space → accepted (R3-5 says whitespace).
- A link at `types/<name>` whose name is not a product-type key is `form`, not also `d` → accepted (a link is never walked; R3-3 reports it at its own path).

Round 4 (handoff/TASK-006-r4-report.md):
- The builder listed none.
- Found at inspection, unlisted: `os.path.lexists` is false on any `lstat` error, so a layer path that cannot be lstat-ed is skipped as absent rather than reported → accepted (nothing is walked, so no link is followed; docs/HARDENING.md).
