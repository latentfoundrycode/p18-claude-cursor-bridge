---
record: brief
header: 1
id: TASK-048
round: 1
satisfies: [R-059]
scope: ["bridge/cursor-bridge/plan-check.py", "bridge/cursor-bridge/scope-check.py", "bridge/cursor-bridge/completion-check.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_header_plan.py", "tests/test_plan_check.py", "tests/test_scope_check.py", "tests/test_completion_check.py", "tests/test_bridge_run_review_ceiling.py", "tests/test_review_guard_ceiling.py", "tests/test_task032_supervisor_launcher.py", "docs/BUILDER_NOTES.md", "handoff/TASK-048-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-048: The plan's and the briefs' headers

## Objective
Release B2 gives every `docs/BUILD_PLAN*.md` file a YAML front-matter header (`record: build-plan`) and every brief under `handoff/` a header (`record: brief`). TASK-046 (merged, PR #137) built the header reader, the schemas and the agreement helper in `bridge/cursor-bridge/bridge_env.py`. TASK-047 (merged, PR #138) made the status file's six readers read its header first. This increment does the same for the plan and the briefs. Five programs read these records: `plan-check.py`, `scope-check.py`, `completion-check.py`, `bridge-run.py` and `review-guard.py`. After this increment each reads the header first through `bridge_env`, and each record's checker compares the header with its prose. Where a record has no header, the program falls back to one prose reading per field, moved into `bridge_env` from the program that holds it today and unchanged in rule. Three retired second readings disappear: (5) `completion-check.py`'s whole-text `Satisfies` search, (6) `plan-check.py`'s `brief_scope`, and (11) `plan-check.py`'s own `merged_ids`. `plan-check.py` also exempts a `historic: true` increment that is merged on its `--base` from the shape rules. `bridge_env.plan_increment_ids` reads every plan file, and the launcher and the guard refuse a malformed or disagreeing brief header before they act. The aim is that each field of the plan and of a brief has one home, one reader and one type, so two programs can never read the same line two ways.

Satisfies: R-059 - The plan's and the briefs' headers. Every `docs/BUILD_PLAN*.md` file carries `record: build-plan` with its `stages` (name, demonstration, increments with `id`, `title`, `kind`, `parent`, `depends_on`, `parallel`, `diagrams`, `scope`, `satisfies`, `deferred`, `historic`). Three programs read it first:
- `plan-check.py` compares each increment's header fields with its prose field lines where the prose has them, under the normalisations (`parallel`'s `yes` and `no` as `true` and `false`; an absent optional scalar's line as `null` and an absent list's line as the empty list; the filler `none` as an absent line; `kind` against `increment` where the `Kind:` line is absent; an increment's `title` against its heading's title; each stage's `name` and `demonstration` against its heading and the presence of its `Demonstration:` line). It fails a difference. It reports a `Scope:` entry with an unbalanced parenthesis as a shape failure for an unmerged increment. It exempts a `historic: true` increment from the shape rules, and from nothing else, only where the merged set holds the ID. That set is read by the one function `bridge_env.squash_merged_ids(folder, PLAN_ID_PATTERN, ref=<--base>)`, `origin/main` by default, and the program's own `merged_ids` is retired. A mark on an unmerged increment is a finding, the mark is accepted with a note under `--no-git` or an unreadable log, and a `--base` beginning with `-` is refused.
- `completion-check.py` reads `satisfies`. Its agreement rule: every R-id its retired whole-text search would have found in a plan file stands in some increment's header `satisfies`, else `HEADER DISAGREES: satisfies`. The sweep is one function in `bridge_env`, and the program's own whole-text regex is gone.
- `bridge_env.plan_increment_ids`, the one reader over every plan file, for `bridge-run.py`.

Every brief carries `record: brief` with `id` and `round` (an integer, equal to the file's name as `parse_review_name` reads it, 1 for a plain name), `satisfies` (its prose is the brief's `Satisfies:` line), `scope`, `merge_unit` and `blocking_class` (their prose is the `Merge unit:` and `Blocking class:` lines). Four readers read it first:
- `scope-check.py` is the brief's checker. It compares every key with its prose or with the file's name (`scope` with the `## Scope` bullets as `parse_scope` reads them, with its refusals) and fails a difference with `HEADER DISAGREES: <key>`, exit 2, as an unreadable Scope exits.
- `plan-check.py` reads `scope` and `satisfies`, and its own `brief_scope` is retired.
- `bridge_env`'s merge-unit and blocking-class readers, for `bridge-run.py` and `review-guard.py`.
- `bridge-run.py` and `review-guard.py` themselves refuse a malformed brief header with exit 125 and a message beginning `bridge-run: refused - header: ` or `review-guard: refused - header: `. They refuse a header that disagrees with its prose or its name the same way (`... refused - header: disagrees <key>`): the launcher checks every key before any builder is launched; the guard checks `merge_unit`, `id` and `round` of the branch's first brief before a snapshot.

Each program's fallback is kept in `bridge_env` and tested on a header-less plan and brief. The checkers refuse a malformed header as R-058 says.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/scope-check.py
- bridge/cursor-bridge/completion-check.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_header_plan.py
- tests/test_plan_check.py
- tests/test_scope_check.py
- tests/test_completion_check.py
- tests/test_bridge_run_review_ceiling.py
- tests/test_review_guard_ceiling.py
- tests/test_task032_supervisor_launcher.py
- docs/BUILDER_NOTES.md
- handoff/TASK-048-r1-report.md

Limits on these files:
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py`. Never edit it by hand.
- `tests/test_header_plan.py` is the supervisor's. You add your own cases only below its marker line, which stands exactly as follows: `# ---------------------------------------------------------------- builder's cases below this line`. You edit nothing above that line.
- In the other six test files, you may only add cases. The supervisor has already rewritten every test that pinned a retired reading, in commit 4bdac19, this brief's checkpoint. If you find another existing test that pins a retired reading, do not rewrite it: name it by its test id in your report and in your last message.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's: BUILD_PLAN.md, DESIGN.md, REQUIREMENTS.md, INVENTORY.md, PROJECT_STATUS.md, HARDENING.md and the diagrams. So are `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`; this increment changes no command.
- Every test file not listed in the Scope.
- TASK-046's reader code in `bridge_env.py`: `read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS` and their private helpers (`_plan_agrees`, `_plan_field_value`, `_kind_norm`, `_derived_historic`, `_demonstration_present`, `_find_block` and the rest). You add new functions beside them and call them. There is one exception. If the existing `build-plan` or `brief` branch of `header_agrees` genuinely cannot meet a test in `tests/test_header_plan.py`, you may fix that branch. If you do, report the change by line and by the test that needed it.
- TASK-047's status readers in `bridge_env.py`: `status_fallback`, `status_workflows`, `status_values` and their helpers.
- The tabular records' headers (the inventory, the register, the index, the deviations file): TASK-049. That includes `completion-check.py`'s `parse_register`, its register checks, and `plan-check.py`'s column-position read of `docs/diagrams/INDEX.md`, which stay as they are.
- The run parameters' header and its lifts (`review_owner_lifts`, `Ceiling above twice:` and the rest): TASK-050.
- `records-migrate.py`: TASK-051.
- The duplicated helpers that `docs/HARDENING.md`'s TASK-047 section names: the `escape_field` copies and `_safe_exc_type_name` / `_bridge_env_refuse_line`, copied between programs. Do not add another copy of these or of any helper. Each reading you need has one copy, in `bridge_env`.
- Any mutation script. The mutants file and the mutation run are the supervisor's.

## Context
**The design that binds this increment.** In `docs/DESIGN.md`, section "## Change: release B2 (2026-11-04)", read:
- the `docs/BUILD_PLAN.md ...` and `handoff/<ID>[-r<N>].md` rows of the table under "### The records and their headers";
- the paragraph "Three kinds of record, one rule each", items (1) for the briefs and (2) for the plan;
- the paragraph "The fallback readers, one copy each", with the enumerated retired readings, of which (5), (6) and (11) are this increment's;
- the paragraph "Header first; fallback; malformed";
- the paragraph "The reader".

Also read `docs/REQUIREMENTS.md` row R-059, and TASK-048's entry in `docs/BUILD_PLAN.md`: its Scope, Scope notes and Done when.

**What exists in `bridge/cursor-bridge/bridge_env.py`. Call these; do not edit TASK-046's reader.**
- `class HeaderError(Exception)`, with `.line` (1-based, in the whole text). Its message reads `line <n>: <what>`.
- `def read_header(text)` returns `(mapping or None, body)` and raises `HeaderError` on a malformed block.
- `def check_header(kind, header)` returns a list of schema findings, empty when the header is valid. The kinds here are `"build-plan"` and `"brief"`.
- `def header_agrees(kind, header, fallback)` returns a list of disagreement tokens.
  - For `"brief"`, the `fallback` dict holds `"name"` (the file's name without `.md`, read by `parse_review_name`), `"satisfies"` (a list), `"scope"` (a list), `"merge_unit"` (a list, a tuple or `None`) and `"blocking_class"` (a string or `None`). The tokens are the key names: `id`, `round`, `satisfies`, `scope`, `merge_unit`, `blocking_class`. `tests/test_header_reader.py`'s `fallback_brief()` (line 556) is a worked example.
  - For `"build-plan"` it calls `_plan_agrees(header, fallback)`. The fallback is `{"merged": set or None, "stages": [{"name": str, "demonstration": the Demonstration line's text or None, "increments": [{"id": str, "title": str, "fields": {...}}]}]}`.
    - `fields` holds only the lines present, keyed `kind`, `parallel`, `parent`, `depends_on`, `diagrams`, `scope`, `satisfies` and `deferred`.
    - `kind`, `parallel`, `parent` and `deferred` are the raw line values.
    - `depends_on`, `diagrams`, `scope` and `satisfies` are lists of strings. The filler `none` on `Parent:`, `Depends on:` or `Diagrams:` counts as absent.
    - `tests/test_header_reader.py`'s `plan_header()` and `plan_fallback()` (lines 594 and 603) are worked examples.
    - The tokens are `<stage> name`, `<stage> demonstration`, `<ID> <field>` (including `<ID> title`, `<ID> id` and `<ID> historic`).
    - Existing behaviour, not a change: `_plan_agrees` pairs stages and increments by position, not by ID. So an increment present on one side only surfaces as `<ID> id`, and `historic` is compared by its derivation only where `merged` is not `None` (or where the increment has a `Scope:` or `Kind:` line).
- `HEADER_SCHEMAS["brief"]` holds `id`, `round` (int), `satisfies`, `scope`, `merge_unit` (list or null) and `blocking_class` (an enumeration of `BLOCKING_CLASSES`, or null). `HEADER_SCHEMAS["build-plan"]` holds `stages`, each `{name, demonstration (bool), increments}`, and each increment `{id, title, kind (increment | group), parent, depends_on, parallel (bool), diagrams, scope, satisfies, deferred, historic (bool)}`.
- Already present and used here:
  - `PLAN_ID_PATTERN = r"TASK-\d{3,}[a-z]?"`;
  - `parse_review_name(name)` returns `(id, round)` or `None`;
  - `read_blocking_class_line(text)` returns `(class, finding, line)` or `None`;
  - `merge_unit_line_present(text)`;
  - `merge_unit_ids(text)` returns a tuple or `None`;
  - `plan_increment_ids(folder)` reads only `docs/BUILD_PLAN.md` today, by a heading regex of its own;
  - `squash_merged_ids(folder, id_rx, git_runner=None, ref="main")` returns a set, or `None` when the log cannot be read;
  - `squash_merged_ids_from_lines`;
  - `declared_set_for_id`;
  - `handoff_brief_tokens(argv)`.

**Where each reader lives today.**
- `plan-check.py`:
  - `ID = r"TASK-\d{3,}[a-z]?"` (line 63), `HEAD_RX` (line 64), `FIELD_RX` (line 65, `re.I`), `STAGE_RX` (line 143) and `DEMO_RX` (line 144).
  - `parse(paths)` (line 113) and `stages_without_demonstration(paths)` (line 147).
  - `scope_paths(value)` (line 79).
  - `merged_ids(base)` (line 176, reading (11)). It runs `git log` itself and then calls `squash_merged_ids_from_lines(..., plan_style=True)`. When it returns `None`, `main` prints the note `could not read git log of <base> - readiness assumes nothing merged`.
  - `brief_scope(text)` (line 210, reading (6)), used by `brief_findings` (line 248).
  - `build_parser()` (line 265): `--plan` (default `docs/BUILD_PLAN*.md`), `--base` (default `origin/main`), `--no-git`, `--briefs` (default `handoff`).
  - Failures are printed as `SHAPE: ...`, `PARENT: ...`, `DEPENDS: ...`, `PARALLEL: ...`, `DIAGRAMS: ...` and `BRIEF: ...`. The last line is `RESULT: OK` or `RESULT: <n> problem(s)`, with exit 1 or 0.
  - It imports bridge_env by `sys.path.insert(0, HERE)` and then `import bridge_env` (lines 57-59).
- `scope-check.py`:
  - It does not import `bridge_env` today, and has no argparse: `main(argv)` takes `<brief> [--base <commit>]`.
  - `split_entry(entry)` (line 86) appends unread pieces to the module-level list `UNREAD` (line 104).
  - `parse_scope(brief_path)` (line 107) opens the file and prints `CANNOT VERIFY: ...`, then calls `sys.exit(2)`, for an unreadable brief (line 111), an ellipsis (line 137) and no entries (line 141).
  - It prints `NOT READ AS A PATH: ...` for each `UNREAD` piece. It ends with `VERDICT: SCOPE CLEAN` (exit 0) or `VERDICT: SCOPE DRIFT` (exit 1).
- `completion-check.py`:
  - It does not import `bridge_env` today.
  - `ID_RX = re.compile(r"\bR-\d{3,}\b")` (line 50) is the register reader's R-id pattern.
  - Plan coverage (lines 149-160) joins every `docs/BUILD_PLAN*.md` and runs the whole-text `Satisfies` regex over it at line 156 (reading (5)). It prints `UNPLANNED: <R-id> (<text>) is in no increment's Satisfies: field`.
  - Options: `--mode {plan,done}`, `--requirements`, `--only`.
- `bridge-run.py`:
  - `builder_review_refusal(argv, folder, kind)` (line 612) reads the brief at `os.path.join(ws, "handoff", brief_name + ".md")` (line 637) into `brief_text` (line 659).
  - The merge-unit check is at lines 660-682. It requires `docs/BUILD_PLAN.md` and checks each ID against `bridge_env.plan_increment_ids(ws)`.
  - It reads `read_blocking_class_line(brief_text)` at line 708.
  - `main` writes `bridge-run: refused - <reason>` to stderr and returns 125 (line 1486), before the slot, the launch and any `runs.jsonl` line.
- `review-guard.py`:
  - `snapshot_review_refusal(nnn, root, common)` (line 682) takes the id and round from `parse_review_name(nnn)` and reads no brief today.
  - `scope_blocking_line` (line 665) reads the `Blocking class:` line of the SCOPE files under `run/review/`.
  - `cmd_snapshot` (line 771) prints a refusal to stdout and returns 125 before anything else is printed or written.
- The SCOPE files (`run/review/SCOPE-<id>.md`) carry no header and are read as today.

**The supervisor's acceptance tests (fixed points).** `tests/test_header_plan.py` names R-059 and D-002, and was committed before this brief. Its run: `python -m pytest -q tests/test_header_plan.py` from the Workspace root. It reuses `tests/test_task032_supervisor_launcher.py`'s lab (`Lab`, `launch`, `build`, `assert_ran`, `assert_refused`, `write_plan`, `write_brief`). On the earlier checkpoint it gave 54 failing and 8 passing, and every case must pass. Its module docstring pins these fixed forms, repeated here:
- **plan-check, malformed and disagreeing headers.** `plan-check.py` prints `HEADER MALFORMED: <path>:<line> <what>` and exits 2 on a malformed plan header. It prints `HEADER DISAGREES: <id> <field>` or `HEADER DISAGREES: <stage> <field>` (a shape failure, exit 1) where a header field differs from its prose under the design's normalisations. An increment in the header with no heading, or a heading with no header entry, is a failure naming the ID.
- **plan-check, the historic mark.** A `historic: true` increment is exempt from the shape rules only where the merged set read from `--base` holds its ID. The mark on an unmerged increment is a failure naming it. Under `--no-git` the mark is accepted, with a `note:` line naming the increments not re-checked. A `--base` beginning with `-` exits 2.
- **plan-check, unbalanced parentheses.** A `Scope:` entry with an unbalanced parenthesis is a shape failure (`SHAPE: <id> ...`) for an unmerged increment, and is read as today for a merged one.
- **scope-check.** `scope-check.py` prints `HEADER MALFORMED: <path>:<line> <what>` and `HEADER DISAGREES: <key>`, each with exit 2.
- **completion-check.** `completion-check.py` prints `HEADER MALFORMED: <path>:<line> <what>` (exit 2). It prints `HEADER DISAGREES: satisfies` (exit 1) where an R-id named by a `Satisfies:` line anywhere in a plan file's body stands in no increment's header `satisfies`. For a file with no header, only an increment's own `Satisfies:` line counts.
- **The launcher and the guard.** `bridge-run.py` refuses with exit 125 and `bridge-run: refused - header: ` naming the brief and the line for a malformed brief header, and with `bridge-run: refused - header: disagrees <key>` for a disagreeing one. `review-guard.py` refuses a snapshot the same way (`review-guard: refused - header: `) on the branch's first brief, comparing `merge_unit`, `id` and `round`.
- **The bridge_env readers.** `bridge_env.plan_increment_ids(folder)` reads every `docs/BUILD_PLAN*.md`. `bridge_env.brief_satisfies(text)` returns the R-ids of the brief's `Satisfies:` line, in order. `bridge_env.merge_unit_ids(text)` reads a brief's header first.

**Tests the supervisor rewrote at the checkpoint (4bdac19).** These tests pinned readings (6) and (11), and the supervisor rewrote them before this brief:
- in `tests/test_plan_check.py`, `tests/test_task032_supervisor_launcher.py`, `tests/test_task033_supervisor.py`, `tests/test_task033_supervisor_r2.py` and `tests/test_pace_report.py`, the merged-set tests now read `bridge_env.squash_merged_ids(<the current folder>, PLAN_ID_PATTERN, ref="main")`;
- `tests/test_a4_review_fixes.py`'s brief test now asserts through plan-check's printed `BRIEF:` findings.

No test now calls `plan-check.py`'s `merged_ids` or `brief_scope`, and no test reaches `HEAD_RX`, `FIELD_RX`, `DEMO_RX`, `split_entry`, `parse_scope` or `UNREAD` inside a program.

**Security context.** The project's ASVS level is 2 (INVENTORY, Decisions; D-004). The trust boundary: the plan and the briefs are text the supervisor writes, but a builder or a reviewer can write them too. So the header reader's refusals stand. A gate program (the launcher, the guard) must refuse rather than guess between two readings: it never launches a builder on a brief whose `## Scope` and `scope` differ, and never snapshots on a first brief whose `merge_unit`, `id` or `round` disagrees. The reader executes nothing. No exception is swallowed: a `HeaderError` becomes the stated refusal line, never a silent fallback in a checker or a gate. Output stays ASCII as today, apart from what a program already quotes from a record (a title, a stage name). `.cursor/rules/secure-coding.mdc` is in force for you.

**Development data.** The development build is the Workspace sources under `bridge/`. A session in this repository always runs the installed bridge, never the one being edited, and no record of this repository carries a header before TASK-054. For you, this means:
- Never run a program of this increment over this repository's own `docs/BUILD_PLAN.md`, `docs/BUILD_PLAN*.md` files, briefs under `handoff/`, or any other record.
- Every test runs on fixtures written under pytest's `tmp_path`, in temporary git repositories the test builds.

**Host.** `claude --version` is not on PATH in the supervisor's session (checked 2026-11-08), so this brief records no Claude Code version tested on. The design's Version section records 2.1.317. Nothing in this increment depends on a host fact.

## Diagrams
`docs/diagrams/D-002-components.md` covers the elements `bridge_env`, `plan_check`, `scope_check`, `completion_check`, `bridge_run`, `review_guard` and `dump_cli`. These are the edges that matter:

```mermaid
    bridge_run --> bridge_env
    review_guard --> bridge_env
    plan_check --> bridge_env
    completion_check --> bridge_env
    scope_check --> bridge_env
    dump_cli -.-> completion_check
    dump_cli -.-> plan_check
```

A solid edge is a plain `import bridge_env` statement, which `check:components` sees. `plan-check.py`, `bridge-run.py` and `review-guard.py` import `bridge_env` today. `scope-check.py` and `completion-check.py` do not: each gains a plain `import bridge_env`, and those are D-002's designed edges `scope_check --> bridge_env` and `completion_check --> bridge_env`. `tools/dump-cli.py` loads `completion-check.py` and `plan-check.py` by file (the dotted edges), so the new import must work when the program is loaded that way, as `plan-check.py`'s `sys.path.insert(0, HERE)` before `import bridge_env` does. No program may gain any other import or load by file. If the task cannot be done within the diagram, stop and report the conflict instead of deviating.

## Requirements
1. **The fallback readers move into `bridge_env.py`, one copy each.**
   - `HEAD_RX`, `FIELD_RX` and `DEMO_RX` move from `plan-check.py`, unchanged in rule. `plan-check.py` then uses `bridge_env`'s copies and compiles none of its own (the test matches an assignment of `re.compile` to any of those three names).
   - `parse_scope` and `split_entry` move from `scope-check.py`, unchanged in rule. The `bridge_env` copies carry no module-level state, print nothing and never call `sys.exit`. They return their reading, or raise or return a value the program can tell apart, for each refusal: an ellipsis (three dots or U+2026), an empty Scope, and the unread pieces.
   - `scope-check.py` keeps, unchanged: its `UNREAD` reporting (`NOT READ AS A PATH: ...`), its `CANNOT VERIFY: ...` lines, and `sys.exit(2)` for an unreadable brief, an ellipsis and an empty Scope.
   - `brief_satisfies(text)` is new. It returns the R-ids of the brief's `Satisfies:` line, read as `FIELD_RX` reads the plan's `Satisfies:` line, in order, and the empty list where there is no line.
   - `plan_r_ids_outside_headers(text)` is new; see Requirement 6.
2. **`plan-check.py` reads the plan's headers first.** For each `docs/BUILD_PLAN*.md` file that `--plan` matches, each with its own header:
   - **Malformed.** A header `read_header` refuses, or one `check_header("build-plan", ...)` finds faults in, prints `HEADER MALFORMED: <path>:<line> <what>` and exits 2. `<path>` is the path read, with forward slashes (`docs/BUILD_PLAN.md`). `<line>` is the `HeaderError`'s line, or `1` for a schema fault.
   - **Agreement.** A well-formed header is compared with the fallback's reading of the same file's prose through `header_agrees("build-plan", header, fallback)`, with `merged` the merged set of Requirement 3 (`None` under `--no-git` or an unreadable log). Each token prints `HEADER DISAGREES: <token>` (for example `HEADER DISAGREES: TASK-002 parallel`, or `HEADER DISAGREES: Stage 2 ... name`). Each is a failure, counted with the others before the `RESULT:` line, exit 1.
   - **Pairing.** An increment in the header with no `### <id>` heading, or a heading with no header entry, is a failure that names the ID (`SHAPE: ...` or `HEADER DISAGREES: ...`).
   - **Header-less files.** A file with no header is read as today through `bridge_env`'s `HEAD_RX`, `FIELD_RX` and `DEMO_RX`, and gives the same answer as today.
   - **Same answer.** An agreeing header gives exactly the answer of the same file without it (READY, TOGETHER and every failure, notes aside).
3. **The one merged set.**
   - `plan-check.py`'s `merged_ids` is deleted. The program calls `bridge_env.squash_merged_ids(os.getcwd(), bridge_env.PLAN_ID_PATTERN, ref=<--base>)`, with `--base` defaulting to `origin/main` as today. The same set marks an increment merged for readiness and for the `historic` exemption in the same run.
   - `squash_merged_ids`'s own default `ref="main"` stays for its other callers.
   - A `--base` beginning with `-` (for example `--base=-c`) is refused with a one-line message and exit 2, no traceback, before any git command.
   - Where the function returns `None`, the existing note `could not read git log of <base> - readiness assumes nothing merged` stays.
4. **The historic mark.**
   - A `historic: true` increment whose ID the merged set holds is exempt from the shape rules (a missing `Scope:` line, the `Kind:` value check, `Parallel`'s value, the `Parent` / `Depends on` readability) and from nothing else. Its `kind` is `increment` and its `parallel` `false`, the absent lines' defaults, never null, and its lists are empty.
   - The mark on an increment the merged set does not hold is a failure naming the ID.
   - Under `--no-git` or an unreadable log, the mark is accepted and never a failure, with a `note:` line naming the increments not re-checked. A suggested form: `note: historic increments not re-checked against a merged set: TASK-001, TASK-002`.
5. **Scope lines: two readings, each kept where it serves.**
   - `plan-check.py`'s `scope_paths(value)` stays in `plan-check.py`, unchanged, for the readiness, the PARALLEL overlap and the BRIEF comparison. It splits on `,` and `;`, drops a trailing `/`, and expands the folder form.
   - The header comparison reads the `Scope:` line through the fallback that the header is compared with: split on `;` as today, each entry stripped, and a folder's trailing `/` kept on both sides, never added or removed. The `scope-folder-slash` case pins this: `src/out/` in the prose against `src/out` in the header disagrees.
   - That fallback refuses an entry with an unbalanced parenthesis. `plan-check.py` reports it as a shape failure for an unmerged increment (suggested: `SHAPE: <id> has an unbalanced parenthesis in its Scope`; the test requires a `SHAPE: <id>` line containing `parenthes`). For a merged increment, the Scope is read as today and no failure is printed.
6. **`completion-check.py` reads `satisfies` from the headers.**
   - It gains a plain `import bridge_env` that works when it is loaded by file (see Diagrams).
   - For each plan file with a well-formed header, the planned set is the union of every increment's header `satisfies`. For a file with no header, it is the R-ids of each increment's own `Satisfies:` line, read by `bridge_env`'s one reading (`FIELD_RX` inside an increment), so a bold `**Satisfies**:` line outside an increment counts for nothing.
   - A malformed plan header prints `HEADER MALFORMED: <path>:<line> <what>` and exits 2.
   - `bridge_env.plan_r_ids_outside_headers(text)` returns the R-ids named on any `Satisfies:` line anywhere in the plan file's body: the retired whole-text search's matches, bold and bulleted forms included. The header block is excluded. It uses the register reader's R-id pattern (`\bR-\d{3,}\b`, as `completion-check.py`'s `ID_RX` holds it) and returns them in order of first appearance.
   - For each plan file with a header, `completion-check.py` calls it and prints `HEADER DISAGREES: satisfies` (a failure, exit 1) where any R-id it returns stands in no increment's header `satisfies` across all plan files that have a header.
   - An R-id mentioned in prose that is not on a `Satisfies:` line (a heading's title) is no disagreement.
   - `completion-check.py` keeps no `Satisfies` regex of its own. The test matches any `re` call whose pattern contains `Satisfies` as a use of reading (5).
7. **`scope-check.py` reads the brief's header first.**
   - It gains a plain `import bridge_env`.
   - A malformed header prints `HEADER MALFORMED: <path>:<line> <what>` (`<path>` as given on the command line, with forward slashes) and exits 2.
   - A well-formed header is compared through `header_agrees("brief", header, fallback)`, where the fallback is: the file's name, for `id` and `round` through `parse_review_name`; `brief_satisfies(text)`; `parse_scope`'s reading of the `## Scope` bullets, each entry a path as `split_entry` reads it, with its refusals; and `merge_unit_ids` / `read_blocking_class_line` of the prose lines, the class word only.
   - Each disagreeing key prints `HEADER DISAGREES: <key>`, and the program exits 2, as an unreadable Scope exits.
   - A brief with no header is checked exactly as today. An agreeing header gives the same verdict as today.
8. **`plan-check.py`'s brief comparison.** `brief_scope` is deleted. `brief_findings` reads the brief's Scope through `bridge_env`'s `parse_scope` reading, header first where the brief has a well-formed header. Its other rules and its `BRIEF:` lines stay as they are.
9. **The bridge_env brief and plan readers, header first.**
   - `merge_unit_ids(text)`, `merge_unit_line_present(text)` and `read_blocking_class_line(text)` read the brief's header first where the text has a well-formed one (`merge_unit`, `blocking_class`), else the line, as today. `merge_unit_ids` still returns a tuple or `None`.
   - These three never raise `HeaderError` to a caller. The gate programs refuse a malformed brief header themselves (Requirement 10) before they rely on these readers.
   - The SCOPE files carry no header and are read as today.
   - `plan_increment_ids(folder)` reads every `docs/BUILD_PLAN*.md` under `folder/docs/`: the IDs from a well-formed header's increments, else the headings by `bridge_env`'s `HEAD_RX`. `bridge-run.py`'s merge-unit check therefore sees an addendum file's increments.
10. **The launcher's and the guard's refusals.**
    - `bridge-run.py`, in `builder_review_refusal`, once it has read the brief and before any launch, slot or `runs.jsonl` line:
      - a malformed header returns the refusal `header: <path>:<line> <what>`, so `main` prints `bridge-run: refused - header: <path>:<line> <what>` to stderr and exits 125. `<path>` names the brief file, for example `handoff/TASK-001.md`.
      - a header that disagrees with its prose or its name, on any key, returns `header: disagrees <key>`, so `main` prints `bridge-run: refused - header: disagrees <key>`, exit 125.
    - `review-guard.py`, in `snapshot_review_refusal`, before any snapshot is written:
      - it reads the branch's first brief, `handoff/<id>.md` (the id from `parse_review_name`), where that file exists.
      - a malformed header returns `review-guard: refused - header: <path>:<line> <what>`.
      - a header whose `merge_unit`, `id` or `round` disagrees with the `Merge unit:` line or the file's name returns `review-guard: refused - header: disagrees <key>`. It compares no other key.
      - `cmd_snapshot` prints the refusal to stdout as its first line and exits 125.
      - Where `handoff/<id>.md` is absent or has no header, the guard behaves as today.
    - Both are stops, not a model's failure.
11. **No program's prose quotes a retired pattern** (KP-073). The tests strip docstrings and match uses, and a pattern quoted in a docstring, a comment or a help text would be a hidden copy.
12. **Housekeeping.**
    - Do not edit the module docstring, the argparse help or any option of the five programs. `tools/dump-cli.py` renders the command reference from them, and the reference is not in your Scope. `python tools/dump-cli.py --check` must stay green with the reference unchanged.
    - Regenerate `bridge/cursor-bridge/MANIFEST.json` with `python tools/make-manifest.py` (no `--version`), and quote the command and its output in your report.
    - Add no dependency. `pyyaml` stays a test-only package, and no program imports it.

## Acceptance criteria
- [ ] `python -m pytest -q tests/test_header_plan.py` passes whole: every supervisor case above the marker, and your own cases below it.
- [ ] The bundles of Done steps 2 to 5 pass. Every existing test in them is green, and no test file outside the Scope is edited.
- [ ] Readings (5), (6) and (11) are gone as uses. `plan-check.py` defines no `brief_scope` or `merged_ids`, compiles no `HEAD_RX`, `FIELD_RX` or `DEMO_RX`, and calls `bridge_env.squash_merged_ids`. `completion-check.py` keeps no `Satisfies` regex and calls `bridge_env.plan_r_ids_outside_headers`.
- [ ] `parse_scope`, `split_entry`, `brief_satisfies`, `plan_r_ids_outside_headers`, `HEAD_RX`, `FIELD_RX` and `DEMO_RX` live in `bridge_env`, one copy each. The `bridge_env` copies print nothing, never exit and keep no module-level state.
- [ ] Each fixed line holds as the Context lists it, with its exit code.
- [ ] A header that agrees with its prose gives the same answer as the header-less file in each of the five programs.
- [ ] `python tools/dump-cli.py --check` is green with `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` unchanged. MANIFEST is regenerated. No option is added, removed or reworded, and no dependency is added.
- [ ] `python bridge/cursor-bridge/diagram-check.py --mode code` gives RESULT OK. `check:components` (the supervisor's run) is OK: the two new plain imports are D-002's designed edges.
- [ ] R-059 is fully met, with no stand-in or placeholder, and at least one test you add names R-059 in its name, docstring or a comment.
- [ ] No new Semgrep high findings. No exception is swallowed. The gate programs refuse rather than fall back on a malformed or disagreeing brief header (ASVS L2).

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless: `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` in tests, or the program's existing `NO_WINDOW`. The tests you add pass it, as `tests/test_header_plan.py`'s `run()` and `git()` do. Every git call gets a timeout.
- **Run every command in the foreground and wait for it to end.** Start nothing in the background or asynchronously, and leave no process running when you finish. Never start a server, a watcher or a daemon.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). An earlier round of this release ran it asynchronously and ran out its two-hour limit (ISS-030). The supervisor runs the full suite. Run only the commands the Done section lists.
- An increment that starts a process: your tests start the programs and git as children through `subprocess.run`, with output captured and a timeout. Each child is windowless and ends before the test does, and nothing outlives the test.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. Run the programs only on fixtures under `tmp_path`, never on this repository's plan, briefs or records (the Development data paragraph in Context).
- No value in this brief is marked as the owner's.
- Follow existing conventions in the files you touch: ASCII output, the `SHAPE:` / `note:` / `RESULT:` lines of `plan-check.py`, the `CANNOT VERIFY:` lines of `scope-check.py`, and the `bridge-run: refused - ` and `review-guard: refused - ` prefixes.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- Numbers from text are parsed with the language's own parser, never by slicing a string. A brief's `round` is the header's integer, compared with `parse_review_name`'s integer. A header line number comes from `HeaderError.line` (an int, 1-based) or is the literal `1`.
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root. The supervisor checks this increment's tests by mutation in its own run, with its own mutants file. You may mutate by hand in-process in your own run to test your cases; if you do, list each mutation and what caught it. No mutation script lands in the diff.
- No failure is known in the files the Done section runs. If a test there fails and this change did not cause it, report it by its test id and fix none.
- Prefer reuse over new code: move the existing readers rather than rewriting them, call `header_agrees` rather than writing a second comparison, and write the minimum that meets the acceptance criteria. This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc`.

## Done
Your report is the file `handoff/TASK-048-r1-report.md`. Write it as you go, so that nothing of it is lost if your run ends early. It records what you did, what you changed, what you ran and what it printed, and what you could not do.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- any change to `header_agrees`'s `build-plan` or `brief` branch, by line, with the test that needed it (or "none");
- any existing test you found that pins a retired reading, by test id (or "none");
- the manifest command you ran and its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples are an ambiguous requirement you resolved one way, a platform or library behaviour you expected, or a value you chose (for example what `plan_increment_ids` does with a malformed plan header, or the exact wording of a suggested line). Write one item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each in the foreground:
1. `python -m pytest -q tests/test_header_plan.py`
2. `python -m pytest -q tests/test_plan_check.py tests/test_plan_demonstration.py tests/test_scope_check.py tests/test_completion_check.py tests/test_a4_review_fixes.py tests/test_a4_followups.py tests/test_a5_followups.py`
3. `python -m pytest -q tests/test_bridge_run.py tests/test_bridge_run_review_ceiling.py tests/test_bridge_run_design_ceiling.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_r4.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_hotfix25a_roster_launcher.py`
4. `python -m pytest -q tests/test_review_guard.py tests/test_review_guard_ceiling.py tests/test_review_guard_a4.py tests/test_task032_supervisor_guard.py tests/test_d003_review_round_states.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_bug036.py tests/test_bug038.py tests/test_bug039.py tests/test_bug041.py tests/test_bug042.py tests/test_bug043.py`
5. `python -m pytest -q tests/test_header_reader.py tests/test_header_schemas.py tests/test_header_status.py tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_mutation_run.py`
6. `python tools/dump-cli.py --check`
7. `python tools/make-manifest.py`
8. `python bridge/cursor-bridge/diagram-check.py --mode code`. This is the Workspace copy, and it is read-only.
9. `git rev-parse HEAD` and `git status --short`

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Each pytest summary line is quoted verbatim in a fenced block; never restate a count in prose. A claim that a check passed quotes the output line that shows it, and a number of failing or skipped cases is backed by the pytest lines naming them. A command you did not run is written `not run`, never described as run. Write the report's results after step 9, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
