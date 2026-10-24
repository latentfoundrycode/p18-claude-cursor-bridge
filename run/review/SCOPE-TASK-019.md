# SCOPE - TASK-019

A supervisor-authored increment of governance text and its tests, with no builder run and no program change. Its brief is docs/BUILD_PLAN.md, "### TASK-019 — Type workflow: web app and local web app" (Scope, Satisfies R-023, Done when). Its sources are the Restructuring Plan's §6.3 (web app and its local sub-type, their definitions and default traits), §6.8 and §6.9 ("Web app → local web app": delivery an installer and a local server the user starts and stops, in place of a deployment), the extension-point registry (`intake.delivery-kind`, `project-end.delivery for <kind>`, the delivery kinds) and the core's "Main and conditional workflows" (a sub-workflow inherits its type workflow and may override its setting).

## Scope (quoted from the plan)
bridge/cursor-bridge/workflow/types/web-app.md; bridge/cursor-bridge/workflow/types/web-app/local-web-app.md; bridge/cursor-bridge/workflow/open-list.md; tests/fixtures/workflows/reangle.status.md; tests/fixtures/workflows/video-factory.status.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_web_app.py; bridge/cursor-bridge/workflow/trace-exceptions.md; tests/test_b3_least_confident.py

## Out of scope
- Every phase module, the core, the registry and the plan critic: unchanged.
- The trait files: unchanged; installable's procedure for `install-script` (TASK-017) is what a local web app takes at project end, and long-running process (TASK-018) carries the local server's start, stop and health.
- The trait personal data, a default of web app, is not written (the open list: when a project first needs it); a part that has it is flagged and the work continues (§6.7).
- The type files of TASK-020 and TASK-021. Design for those increments is not this diff's defect.
- Every program under bridge/.

## A deviation from the Done when
The Done when says local web app overrides the kind to `installer`. It sets `install-script`: a local web app is a local server, which Delivery-Conventions.md §1 ships the install-script way and the registry's kinds list glosses as `install-script` ("a command-line tool or a local server"); and the video factory, one of the two projects the sub-type was written for, ships `install.cmd` and `install.ps1` (its own docs/DELIVERY.md, read 2026-10-24), so `installer` would have given it the single-file installer's procedure at its next project end, against §6.8's "so that none of them pauses". The open list's plain-word "delivered by an installer" stands, the install script being that project's double-clickable installer. A local web app wanted as a single-file `.exe` installer now fits no written sub-type and pauses at intake (the Done when's sentence, with the two kinds exchanged). Recorded in docs/INVENTORY.md, Decisions, and told to the owner (rule 58).

## A choice the Done when leaves open
The open list says a type workflow "that states its default traits states the ones given here", and that no form for that statement exists yet, "the form and its check come together, in the change that writes the first such statement". Neither type file states its default traits: the open list's Default traits cell is their one source, which intake and the design gate read, so a copy in the type file would be a second statement of one fact with a check to keep them equal. The Done when's "has default traits has-screens + personal-data" and "replaces personal-data with installable + long-running process" are asserted on the open list's rows. Recorded in docs/INVENTORY.md, Decisions, and docs/HARDENING.md, TASK-019.

## The tests the supervisor wrote, and the paragraph each enforces
tests/test_type_web_app.py (new, 15 tests, naming R-023), each enforcing TASK-019's Done when:
- each file is one `#` title and its change headings in order (web app: `## Set at intake.delivery-kind`, `## Add at project-end.delivery for web-deployment`; local web app: `## Set at intake.delivery-kind`), and no other heading;
- the Set sections' values: `web-deployment` and `install-script`, each the section's only non-blank line;
- each section has its own `new TASK-019` entry naming the file and the heading, and no other entry names the file;
- no unit of a file, as trace-check.py reads units, is a unit of the core, a phase module, the plan critic, a trait file or the other type file (new text, never a copy);
- both open-list rows written; local web app of type web app, delivered by an installer, with a local server to start and stop;
- the default traits as the open list gives them, the sub-type's set being its type's with personal-data replaced by installable and long-running-process, and neither type file restating them;
- inheritance: the sub-workflow names no delivery procedure, the type's procedure names `web-deployment` only, installable has the procedure for `install-script`, and the core's and the registry's sentences on inheritance and on a sub-workflow leaving its type's procedure behind stand;
- the web-deployment procedure, six numbered steps each run only after the one before it has succeeded, their order checked: the owner's yes first, naming the pause and the way back; the procedure recorded with its platform and account before the first deployment, a key the session lacks handled by a run sheet; a migration rehearsed on a restored copy, a failed rehearsal stopping before anything live is touched; the live data backed up immediately before, to storage outside the repository and the Workspace, and writes held with no exception until the check passes; the release deployed, and the live data migrated, only after that pause; the check at the address that changes no user's data and reads the version where the design gives it a place; on a failed deployment or check the backup restored before the previous release is deployed; the address and version named;
- `workflow-check.py` passes over workflow/; both fixtures pass `--status` with nothing but `RESULT: OK` (no FAIL: nothing pauses; no FLAG: every trait named is written).

tests/test_b3_least_confident.py pins the three new sections; its derivation (widened to types/ by TASK-017) covers every new entry.

Review A's first read (REJECT, one blocking, three should-fix, five considers) was answered in the commit after 4419d90, every item taken: the blocking one was the way back restoring the backup over the owner's live data with no yes. Its note on the delivery kind gave the deviation above.

Review A's confirming read approved de327b2, judging the kind change on its merits; of its four considers, two are taken in the last commit before these files (while a restore waits for the owner's yes the product is taken offline unless the owner chooses otherwise; the Set test's name) and two kept as docs/HARDENING.md leads (the plan's Done when still naming `installer`; what pauses a part whose confirmed kind differs from its sub-workflow's).

Your first read (REJECT, four findings) was answered in the commit after 9d46fa0, which this read checks first: the section is now six numbered steps, each run only after the one before it has succeeded; a failed rehearsal stops before anything live is touched; writes are held with no exception from the backup until the check passes (so the clauses for a product that could not hold them, the lossy-restore yes and the product offline while it waits, are gone, the case no longer arising); the test checks the six steps' order and that the release is deployed only after the pause. The test's assertions on the removed clauses are removed with them and replaced by an assertion that the exception is gone.

Run once against the checkpoint 5bbdba7 (with the two fixtures): 18 failed, 89 passed across the two files; the new file's one pass there is the workflow-check guard, which holds on both sides; the three new pins and the derivation test fail and the earlier pins pass.

## Expected bookkeeping and record files in the diff
docs/REQUIREMENTS.md (R-023 built), docs/INVENTORY.md (a Features row and the two Decisions rows above), docs/HARDENING.md (TASK-019's section with its round and two leads, and TASK-018's last Review B round), docs/PROJECT_STATUS.md and project.json as at this pull request's merge, bridge/cursor-bridge/MANIFEST.json regenerated, docs/ROSTER.resolved.json (the roster check's resolved_at stamp, rewritten at each check), and run/review/ (these three files, removed before the merge).

## What to judge
Does the diff meet every clause of the Done when? Is the web-deployment procedure sound guidance a supervisor will follow on a real project, safe for the owner's live data, consistent with the core (founding rule N1, the escalation of an irreversible or out-of-repository action, the rule that every cost names its platform and account), with the registry's delivery kinds and with installable's procedures? Is leaving the default traits in the open list alone a sound reading of the open list's own text? Is `install-script` the right kind for a local web app, given the deviation above? Can each check be carried out from what the supervisor can see? Do the tests enforce their paragraphs and fail on a regression? Are the records accurate? Apply the anti-gaming checks.
