# TASK-006: The workflow check

## Objective
The bridge is being split into a main workflow and conditional workflows: a type workflow per product type, a sub-workflow per sub-type, and trait additions per trait. They change the main workflow only at named extension points. Two canonical tables already exist: the open list (`bridge/cursor-bridge/workflow/open-list.md`, every product type, sub-type and trait) and the extension-point registry (`bridge/cursor-bridge/workflow/extension-points.md`, every phase module and every point). This increment writes `bridge/cursor-bridge/workflow-check.py`, the deterministic program that keeps the conditional workflows honest against those two tables, and checks a project's `Workflows:` status lines against the open list. It runs at intake, at every bridge release (in the bridge's CI) and at every calibration. Its purpose: a bridge release that renames an extension point fails loudly instead of silently breaking a conditional workflow nobody is looking at; a trait can never replace or set; a project whose product type has no written workflow is stopped. This increment also adds the check to the bridge's CI.

Satisfies:
- R-014 — `workflow-check.py` verifies: every change targets an existing extension point; replace/set appears only in a type or sub-workflow and replace only on a replaceable phase; trait additions only add; every sub-workflow names an existing type workflow; every project's `Workflows:` line names, per part, exactly one product type, at most one sub-type of that type, and traits, all in the open list. An unwritten type or sub-type fails (pauses the project). An unwritten trait is flagged, non-fatal (§6.7).
- R-033 — The workflow check runs at every bridge release (CI) and at every calibration.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/workflow-check.py
- .github/workflows/tests.yml
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-006-r1-report.md

Do not modify anything else.

## Written by the supervisor; do not edit
These files are committed with this brief. They were written from the interface below. Do not edit, move, rename or add to them:
- tests/test_workflow_check.py (names R-014 and R-033; it covers every finding code, the FLAG line, the exit codes and the CI step)
- everything under tests/fixtures/workflows/ (the sample fixtures, the passing root `tests/fixtures/workflows/pass/`, and the failing cases)
- tests/test_release_b_ci_floor.py. **Expected failure:** this test pins the whole workflow file verbatim (`WORKFLOW_PIN`, checked by `test_r002_workflow_is_the_pinned_one`). Your CI step makes that one test fail. That is expected. Do not edit the test or its pin to make it pass. The supervisor regenerates the pin after your run. Any *other* failure in that file is caused by your workflow edit, and you fix it in the workflow, not in the test.

Suppose a supervisor test or fixture contradicts this brief, or cannot pass without breaking a requirement below. Then stop, change no test, and report the contradiction (test name, brief requirement, what each says).

## Out of scope
- .env and anything under secrets/
- CI configuration other than the one new step in Requirement 14
- docs/ and handoff/, except the files the Scope section names
- Everything under `bridge/` except `bridge/cursor-bridge/workflow-check.py` and `bridge/cursor-bridge/MANIFEST.json`. In particular these stay unedited: `workflow/open-list.md`, `workflow/extension-points.md`, `bridge/commands/supervisor.md`, `settings.bridge.json`, `CHANGELOG.md`, `VERSION`.
- `inventory-check.py` and `conformance-check.py`. Their own reading of the `Workflows:` line is TASK-008.
- The registry-to-module cross-check (every phase module declares exactly its registry points). That is TASK-014; nothing reads `workflow/phases/` here.
- Checking a type or sub-workflow's statement of its default traits against the open list. No form for that statement exists yet; do not invent one.
- Reading a part's delivery kind from anywhere (a status file, a design document). See Requirement 10.
- The bridge's own `docs/PROJECT_STATUS.md`. Never pass it to the check in CI or in a test.

## Context
The repository root is the folder you were started in. Paths are relative to it.

**The design, quoted (Restructuring Plan §6.5, §6.6, §6.7; this is the whole of what you need from it):**
- "Each change a conditional workflow makes is one of three kinds: Add … Replace: a whole phase module, only where the phase declares that it may be replaced. Set: a value the main workflow leaves open, such as the kind of performance budget (page load, frame time) or the delivery kind."
- "Only type workflows and sub-workflows may replace or set; trait additions may only add."
- "A sub-workflow inherits its type workflow and changes only what differs, at the same extension points. It may override its type workflow's replacement or setting … That is inheritance, not a collision."
- §6.6, the check, "run at every bridge release and every calibration": "every change in every conditional workflow targets an extension point that exists; a replacement or a setting appears only in a type workflow or a sub-workflow, and a replacement targets a phase declared replaceable; trait additions only add; every sub-workflow names a type workflow that exists; every project's `Workflows:` lines name, for each part, exactly one product type, at most one of its sub-types, and traits, all present in the open list; a product type or sub-type whose workflow is not yet written fails the check."
- §6.7: "A new product type or sub-type pauses the project … A new trait is flagged, and the work continues … The same holds for a trait that is defined but not yet written."

**Where the files live (plan §6.11, and the open list's "How this file is read").** Under a workflow folder:
- the type workflow of product type `<key>` is `types/<key>.md`;
- the sub-workflow of sub-type `<key>` of type `<type key>` is `types/<type key>/<key>.md`;
- a trait's additions are `traits/<key>.md`.

The path alone says which layer a file is and which entry it is for. There is no front matter. The bridge's own workflow folder is `bridge/cursor-bridge/workflow/` (installed copy: `~/.claude/cursor-bridge/workflow/`). Today it holds only `open-list.md` and `extension-points.md`; no `types/` or `traits/` exist yet. Later increments add `phases/`, `trace-exceptions.md` and others there. This check reads none of those.

**The open list's tables** (`bridge/cursor-bridge/workflow/open-list.md`, section "How this file is read", quoted): "`workflow-check.py` reads the three tables below and nothing else in this file … Each table is the first table after its heading (`## Product types`, `## Sub-types`, `## Traits`), its rows running to the first line that is not a table line; its columns are found by their header names; no cell contains a `|`." The columns:
- Product types: `| Key | Name | Definition | Workflow name | Default traits | Written | Planned |`
- Sub-types: `| Key | Name | Of type | Definition | Sub-workflow name | Default traits | Written | Planned |`
- Traits: `| Key | Name | Definition | Written | Planned |`

The second table line is the `|---|` separator. **Written** is `yes` or `no`; treat any value other than `yes` as unwritten. **Of type** is the sub-type's product-type key. The Traits table's row order is the order traits apply in. `tests/test_open_list.py`, function `table()` (lines 87–106), is a working parse of this shape.

**The registry's tables** (`bridge/cursor-bridge/workflow/extension-points.md`, same reading rule, headings `## Phase modules` and `## Extension points`):
- `| Module | Phase | Replaceable |` — Replaceable is `yes` or `no`; today only `interface` is `yes`.
- `| Key | Phase | Point | Declared by | Changes | Applies |` — Key is the point key, e.g. `intake.questions`. Changes is `add` or `add, set`. Today exactly three points accept `set`: `intake.target-environment`, `intake.budget-kind`, `intake.delivery-kind`.

**How a conditional workflow names a change** (registry, "How a conditional workflow names a point", quoted): "A conditional workflow file states each change it makes under a heading of its own, naming the kind of change and its target, and nothing else in the file changes the main workflow:"
- "`## Add at <point key>` — its additions there. Any conditional workflow may add."
- "`## Set at <point key>` — the value it sets there, at a point whose Changes cell includes `set`. Only a type workflow or a sub-workflow may set."
- "`## Replace <module key>` — its own version of the whole phase, for a module marked replaceable. Only a type workflow or a sub-workflow may replace."

**Replaced modules keep their points** (registry, below the Phase modules table, quoted): "A replacement keeps the points of the module it replaces, without declaring them again under its `## Replace` heading, so the additions of the layers below it, such as the trait *has screens* adding the mockup variant at `interface.variants`, still apply to it."

**Delivery kinds** (registry, paragraph after the Extension points table, quoted): "The delivery kinds are one list …: `installer`, `install-script`, `package`, `web-deployment`, `store-package` and `host-installation`; the value set at `intake.delivery-kind` and the kind an addition at `project-end.delivery` names are both drawn from it … Where no type workflow or sub-workflow sets a part's kind, the kind the supervisor confirms with the owner at intake (Phase 1) is the part's kind, recorded by its key from this list. Each addition at `project-end.delivery` names the delivery kind it is for and applies only to a part of that kind."

That last sentence is about how the supervisor applies additions. This check enforces only that every such addition names a valid kind (Requirement 9).

**The `Workflows:` status line** (`bridge/commands/supervisor.md`, "Project state", lines 1817–1828, quoted):

`Workflows: [<part>: ]<Workflow name>[ → <Sub-workflow name>]; traits: <Trait name>[, <Trait name>…]`

- "the product type is named by its **Workflow name**, the sub-type by its **Sub-workflow name** and each trait by its **Name**, spelled exactly as … `open-list.md` spells them; every name on the line is in the open list;"
- "exactly one product type and at most one of its sub-types; ` → <Sub-workflow name>` (the arrow is `→`) is left out when the part has no sub-type;"
- "the traits follow `; traits: `, separated by a comma and a space, in the order the open list gives them; a part with no trait reads `; traits: none`;"
- "`<part>: `, the part's name and a colon, follows `Workflows: ` only when the project has more than one part; a project with one part has one line without it; a part's name contains no `:`, `;` or `→`;"
- "until intake has classified a part, its line reads `not yet classified` in place of the names (`Workflows: not yet classified` in a project with one part)."

Example (the bridge itself): `Workflows: Host Extension Development → Claude Code Extension; traits: Installable`.

**House style of the bridge's programs** (see `bridge/cursor-bridge/diagram-check.py` lines 1–40 and 733–961):
- Python 3.12 standard library only, `argparse`.
- A module docstring that is the usage text.
- Deterministic, read-only, ASCII output.
- Finding lines, then one final `RESULT:` line (`RESULT: OK` / `RESULT: <n> problem(s)`).
- `return 0`/`1` from `main()`, and `2` for a usage or input error (as in `bridge-check.py`, `roster-check.py`).
- The `if __name__ == "__main__":` block reconfigures stdout/stderr with `errors="backslashreplace"`, then `sys.exit(main())`.

This program launches no subprocess.

**The manifest.** Any change under `bridge/` regenerates `bridge/cursor-bridge/MANIFEST.json` with `python tools/make-manifest.py`, run after your last edit under `bridge/`. It takes the version from the newest `## <version>` heading in `bridge/cursor-bridge/CHANGELOG.md` (today `2026.10.11d`, which equals `bridge/cursor-bridge/VERSION`), so `VERSION` is rewritten unchanged. CI's `bridge-check.py --root bridge --sources --quiet` fails if the manifest does not match the tree. Never write a `__pycache__` under `bridge/` into the manifest (make-manifest skips it).

**The CI workflow today** (`.github/workflows/tests.yml`):
- The job `tests`, named `bridge programs (${{ matrix.os }})`, runs on windows-latest and ubuntu-latest. Its steps are: checkout; setup-python 3.12; `python -m pip install -r requirements.lock`; `python -m pytest tests -q`; the windowless check; the manifest check.
- A second job, `security-floor` (named `security floor`), holds Semgrep, OSV-Scanner and Socket. The Socket step is the only step in the workflow that refers to a secret.

**Security context.** The surface is reading local Markdown files named on the command line; there is no network, no secret and no write. Trust boundary: the files read are maintainer-authored or project-authored text. The program must not execute, import or evaluate anything from them, and must fail cleanly (exit 2) on an unreadable or malformed input rather than crash with a traceback. No ASVS level is recorded for the bridge. There is no `.cursor/rules/` folder in this repository, so the constraints below are the whole set.

**Development data** (copied from `docs/INVENTORY.md` Decisions): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet." For this increment: run the program and the tests from this repository's sources only; never against `~/.claude`, the bridge's own `docs/PROJECT_STATUS.md`, or any other project. `tests/conftest.py` already redirects `HOME`/`USERPROFILE` for every test.

## Diagrams
None. The build plan names no diagram for this increment.

## Requirements

### The command line
1. The command line is exactly:

   `python workflow-check.py [--open-list FILE] [--registry FILE] [--status FILE]... [ROOT ...]`

   - `ROOT` is zero or more workflow folders. In each, the files under `ROOT/types/` and `ROOT/traits/` are the conditional workflows checked. Nothing else in a root is read. A root without `types/` or `traits/` simply has no files of that layer.
   - With no `ROOT` and no `--status`, the root is the `workflow` folder beside the program (`os.path.dirname(os.path.abspath(__file__))` + `workflow`).
   - With `--status` and no `ROOT`, no conditional-workflow files are checked; only the status files are.
   - `--open-list` defaults to `workflow/open-list.md` beside the program, and `--registry` to `workflow/extension-points.md` beside the program. The same two tables are used for every root and every status file of one run.
   - `--status FILE` may be repeated. Each named file's `Workflows:` lines are checked (Requirements 11–13).
2. The module docstring is the usage text, printed by `--help` through argparse's description or epilog. It states:
   - the command line above;
   - that the check is one program, run at intake (the project's status file), at every bridge release (CI, over the bridge's workflow folder and the sample fixtures) and at every calibration (the installed workflow folder and the project's status file);
   - each finding code of Requirement 4, written as it appears in a finding line: `(a)` to `(f)`, `(set)`, `(kind)`, `(unknown)`, `(form)`, and the `FLAG (trait)` line;
   - the exit codes of Requirement 3.

### Exit codes and output
3. Exit codes:
   - `0` when no `FAIL` line was printed. `FLAG` lines may have been printed.
   - `1` when at least one `FAIL` line was printed.
   - `2` when the check cannot run. Causes: a `ROOT` that is not a folder; an open list, registry or status file that does not exist or cannot be read as UTF-8; a required heading or required column missing; a table row whose cell count differs from its header's.

   On exit 2, print one or more lines `ERROR: <path>: <reason>` and then `RESULT: not checked`. Do not print a traceback.

   Required columns:
   - Product types: Key, Name, Workflow name, Written.
   - Sub-types: Key, Of type, Sub-workflow name, Written.
   - Traits: Key, Name, Written.
   - Phase modules: Module, Replaceable.
   - Extension points: Key, Changes.
4. Every finding is one line on standard output:

   `FAIL (<code>) <path>: <name> - <reason>`

   - `<path>` is the file's path as built from the argument given (the `ROOT` argument joined with the file's path inside it, or the `--status` argument as given), with `/` as separator.
   - `<name>` is the offending name: a point key, module key, file key, Workflow/Sub-workflow/trait name, delivery kind, or part name. Where no single name exists (a missing line), use `-`.
   - `<reason>` is free plain-language text.

   `<code>` is exactly one of:
   - `a` — an `Add at` or `Set at` names a point key that is not a Key of the registry's Extension points table.
   - `b` — a trait file (`traits/<key>.md`) contains a `Set at` or a `Replace` heading.
   - `c` — a `Replace` names a module that is not in the Phase modules table, or whose Replaceable is not `yes`.
   - `d` — a sub-workflow `types/<t>/<s>.md` fails one of these:
     - `<t>` is a Product types key;
     - `types/<t>.md` exists in the same root;
     - `<s>` is a Sub-types key whose Of type is `<t>`.
   - `e` — on a `Workflows:` line, a part has no product type, two or more product types, two or more sub-types, or a sub-type whose Of type is not the line's product type; or two `Workflows:` lines in one status file name the same part (Requirement 12).
   - `f` — a `Workflows:` line names a product type or a sub-type whose Written is not `yes`.
   - `set` — a `Set at` names a registry point whose Changes cell, split on commas and stripped, does not contain `set`.
   - `kind` — the delivery-kind cases of Requirement 9.
   - `unknown` — a type file `types/<key>.md` whose key is not a Product types key, a trait file whose key is not a Traits key, or a name on a `Workflows:` line that is none of the open list's Workflow names, Sub-workflow names or trait Names.
   - `form` — the form cases of Requirements 6, 7 and 11.

   One input may produce several findings (a trait's `Set at` at an unknown point gives both `b` and `a`). Print each. Finding lines come in a deterministic order: roots in argument order, files in sorted path order, then status files in argument order.
5. An unwritten trait is not a failure. For each trait on a `Workflows:` line whose Written is not `yes`, print one line:

   `FLAG (trait) <path>: <trait name> - trait not yet written; flagged, work continues (non-fatal)`

   It does not affect the exit code. The last line printed is always exactly one `RESULT:` line: `RESULT: OK` when there is no `FAIL` line (whatever the flags), else `RESULT: <n> problem(s)` with `<n>` the number of `FAIL` lines.

### Conditional-workflow files
6. Every file under `ROOT/types/` and `ROOT/traits/` is one of:
   - `types/<key>.md`
   - `types/<type key>/<key>.md`
   - `traits/<key>.md`

   Any other file there is `FAIL (form)`. That includes a deeper path (a third level), a non-`.md` file, or a folder under `traits/`. The one exception is a `types/<t>/` folder whose own name does not match a Product types key, which is reported once as `d`. Keys are matched exactly against the open list.
7. In a conditional-workflow file, a change heading is a line outside a fenced code block (fences are lines starting with three backticks) that starts with `## ` and whose next word is `Add`, `Set` or `Replace`. It must match exactly one of these forms, with single spaces:
   - `## Add at <point key>`
   - `## Add at project-end.delivery for <kind>`
   - `## Set at <point key>`
   - `## Replace <module key>`

   A change heading of any other shape is `FAIL (form)`, for example `## Add to x`, `## Adds at x`, or `## Replace` with no key. Other `## ` headings, and all `###`-and-deeper headings, are prose and are not checked.

   A section runs from its heading to the next `## ` heading or the end of the file. These are also `FAIL (form)`:
   - two `Set at` headings for the same point in one file;
   - two `Replace` headings for the same module in one file;
   - a `Set at` section with no non-blank line.

   Several `Add at` headings for the same point in one file are allowed, and keep their file order.
8. Type workflows and sub-workflows may add, set and replace. Trait files may only add (code `b`). A sub-workflow setting or replacing what its type workflow already sets or replaces is inheritance, never a finding.
9. Delivery kinds. The list is exactly `installer`, `install-script`, `package`, `web-deployment`, `store-package`, `host-installation`, matched exactly. Every addition at `project-end.delivery`, in any layer, names its kind in its heading: `## Add at project-end.delivery for <kind>`, e.g. `## Add at project-end.delivery for installer`. Each of these is `FAIL (kind)`:
   - an `## Add at project-end.delivery` heading with no ` for <kind>`;
   - a ` for <kind>` whose kind is not in the list;
   - a ` for <kind>` on a heading for any other point;
   - a `## Set at intake.delivery-kind` section whose first non-blank line is not exactly one kind from the list. Strip surrounding whitespace and at most one pair of enclosing backticks before comparing.

   One file may hold several `project-end.delivery` additions for different kinds.
10. A replacement keeps the replaced module's points. An `Add at` (and a `Set at`) at a point whose declaring module some type workflow or sub-workflow replaces is checked exactly like any other addition, in every layer. This includes a trait adding at `interface.variants` while a type workflow replaces `interface`, and a sub-workflow adding at a point of a module its type workflow replaces. Such an addition is never a finding because of the replacement. A replacement adds no points either: an `Add at` naming a key absent from the registry is `a`, whatever a `Replace` section's body says.

    The check does not read a part's delivery kind: which part an addition reaches is the supervisor's application rule, not this check's.

### Status files
11. A `Workflows:` line is a line of the status file that starts with exactly `Workflows: ` at column 0. Each line is checked in this order:
    1. **Prefix.** If the status file has more than one `Workflows:` line, each must carry a part prefix `<part>: ` right after `Workflows: `. The part is the text up to the first `: `, non-empty, and contains no `;` or `→`. If the file has exactly one line, it must carry no prefix. A line breaking this rule is `FAIL (form)` and is not checked further.
    2. **Unclassified.** The rest reading exactly `not yet classified` is accepted with no finding.
    3. **Traits marker.** Otherwise the rest must contain `; traits: ` exactly once. Missing it is `FAIL (form)`, and the line is not checked further.
    4. **Head.** The text before `; traits: ` is split on `→`, each segment stripped, and each segment split on `,`, each name stripped.
       - A name that is not a Workflow name, Sub-workflow name or trait Name is `unknown`.
       - Names that are Workflow names count as product types, and names that are Sub-workflow names count as sub-types. Their counts and the Of type relation decide `e` as Requirement 4 states.
       - When the counts are right (exactly one product type, at most one sub-type of it), the shape must be: the product type alone in the first segment and the sub-type alone in a second and last segment. Any other shape is `form`, for example the sub-type first, an empty segment, or a trait Name in the head.
       - The product type, and the sub-type if any, with Written not `yes` give `f`, one finding each.
    5. **Traits.** The text after `; traits: ` is `none` or trait Names separated by `, `. A name that is not a trait Name is `unknown`. A repeated trait, or traits not in the Traits table's row order, is `form`. Each unwritten trait gives the `FLAG` line of Requirement 5.
12. In a status file with several `Workflows:` lines, two lines with the same part name are `FAIL (e)`. In a file with one unprefixed line, there is one part. A status file with no `Workflows:` line is `FAIL (form)` with name `-`.
13. The check reads only the `Workflows:` lines of a status file. It does not check where they stand relative to `Phase:` (that is TASK-008's) and reads no other field.

### The CI step and the manifest
14. In `.github/workflows/tests.yml`, add one step at the end of the `tests` job (`bridge programs`), after the manifest step, and change nothing else in the file:

    ```yaml
          - name: workflow check over the bridge's workflow files and the sample fixtures
            run: python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass
    ```

    The step carries:
    - no `env:`;
    - no secret or `secrets` expression;
    - no `if:`;
    - no `continue-on-error`;
    - nothing that swallows the exit code.

    It never names `docs/PROJECT_STATUS.md` or `--status`. It is not added to the `security floor` job.
15. `bridge/cursor-bridge/MANIFEST.json` is regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`. Its only change is the new `cursor-bridge/workflow-check.py` entry and the `generated` stamp.

## Acceptance criteria
- [ ] `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` exits 0 and its last line is `RESULT: OK`.
- [ ] The check exits 1 with a `FAIL (<code>)` line naming the file and the offending name for each of:
  - (a) an undeclared or renamed extension point;
  - (b) a trait that replaces or sets;
  - (c) a replace on a non-replaceable phase, read from the registry;
  - (d) a sub-workflow naming a missing type;
  - (e) two product types, two sub-types, or a sub-type not of its type on one part;
  - (f) a `Workflows:` line naming an unwritten type or sub-type;
  - a `Set at` a point whose Changes lack `set`;
  - a `project-end.delivery` addition with no kind or an unlisted kind.
- [ ] An unwritten trait on a `Workflows:` line prints a `FLAG (trait)` line, and the exit code stays 0 when nothing else fails.
- [ ] A trait's addition at a point of a module that a type workflow replaces passes (Requirement 10).
- [ ] Unreadable or malformed inputs exit 2 with `ERROR:` lines and `RESULT: not checked`, never a traceback.
- [ ] `--help` prints the usage text naming the three times the check runs (intake, release, calibration).
- [ ] The `tests` job has the step of Requirement 14 and nothing else in the workflow changed. `tests/test_release_b_ci_floor.py` fails only in `test_r002_workflow_is_the_pinned_one`.
- [ ] `tests/test_workflow_check.py` passes. The full suite passes except `test_r002_workflow_is_the_pinned_one`.
- [ ] `windowless-check.py` and `bridge-check.py --sources` pass.
- [ ] R-014 and R-033 are fully met: no stand-in, placeholder, or "arrives in a later stage" text. The supervisor's test names both IDs; your program's docstring names R-014 and R-033 as well.

## Constraints
- Do not add dependencies: standard library only.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW`, `0` elsewhere). This program should launch none.
- Never start a server, a watcher or a daemon that outlives a test.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. See the Development data paragraph in Context. Never run the check on `~/.claude` or on `docs/PROJECT_STATUS.md`.
- Follow existing conventions in the files you touch (see the house style in Context).
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- Do not edit `tests/test_workflow_check.py`, anything under `tests/fixtures/workflows/`, or `tests/test_release_b_ci_floor.py` (see "Written by the supervisor; do not edit").
- Do not edit `open-list.md` or `extension-points.md` even if a fixture or the check would be simpler. If either table cannot be parsed in the stated shape, stop and report it.
- Read every table cell as text. No number is parsed from any input. The program never executes, imports or evaluates input content.
- Do not hard-code any key, name, point or module from the tables. Everything comes from the open list and the registry given on the command line. The one exception is the delivery-kind list of Requirement 9, which is fixed in the program.
- Every verification command the Done section asks you to run is written there in full. Run exactly those.
- Prefer reuse over new code (the standard library, the parse shape already shown in `tests/test_open_list.py`), and write the minimum that meets the acceptance criteria.

## Done
Run each of these from the repository root (the folder you were started in), in this order. Paste each command with its exit code and the relevant output lines into your report:
1. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` (expected exit 0, `RESULT: OK`)
2. `python bridge/cursor-bridge/workflow-check.py --help`
3. `python -m pytest tests/test_workflow_check.py -q`
4. `python -m pytest tests -q` (expected: only `test_r002_workflow_is_the_pinned_one` fails)
5. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`
6. `python tools/make-manifest.py`, then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
7. `git diff --stat` (expected files: the program, the workflow, the manifest, your report, and possibly `docs/BUILDER_NOTES.md`)

Your report is the file `handoff/TASK-006-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- a section headed exactly `Assumed, not verified`. List every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: an ambiguous requirement you resolved one way, a parse rule you chose where the brief was silent (how a heading with trailing spaces or a CRLF line ending is read), or a platform behaviour you expected. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
