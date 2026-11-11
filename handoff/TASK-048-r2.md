---
record: brief
header: 1
id: TASK-048
round: 2
satisfies: [R-059]
scope: ["bridge/cursor-bridge/plan-check.py", "bridge/cursor-bridge/scope-check.py", "bridge/cursor-bridge/completion-check.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_header_plan.py", "tests/test_header_plan_r2.py", "tests/test_plan_check.py", "tests/test_scope_check.py", "tests/test_completion_check.py", "tests/test_bridge_run_review_ceiling.py", "tests/test_review_guard_ceiling.py", "tests/test_task032_supervisor_launcher.py", "docs/BUILDER_NOTES.md", "handoff/TASK-048-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-048-r2: The plan's and the briefs' headers, round 2 (the reviewers' findings)

## Objective
Fix the following confirmed defect — repair the named cause, nothing else. This brief covers the findings that the security audit (FAIL) and Review A (REJECT) raised on round 1 of TASK-048 (the builder's commit 46c7dc0 on branch `task-048`). Every finding below is to be fixed in this round. Each names its evidence at `file:line` (the lines are those of the current HEAD, bd47c5e, which holds round 1's code unchanged plus the supervisor's new test file), the required behaviour, and the cases in `tests/test_header_plan_r2.py` that fail today and must pass. The increment itself is unchanged: round 1's brief, `handoff/TASK-048.md`, stays in force (its Objective, Satisfies line, Context, Requirements and Constraints). This brief restates what you need from it. Where the two differ, this brief governs.

**What the increment is (unchanged).** Release B2 gives every `docs/BUILD_PLAN*.md` file a YAML front-matter header (`record: build-plan`) and every brief under `handoff/` a header (`record: brief`). TASK-046 built the header reader, the schemas and the agreement helper in `bridge/cursor-bridge/bridge_env.py`; TASK-047 made the status file's readers read its header first. This increment makes the five programs that read the plan and the briefs (`plan-check.py`, `scope-check.py`, `completion-check.py`, `bridge-run.py`, `review-guard.py`) read the header first through `bridge_env`, compare it with the prose, and fall back to one prose reading per field, kept in `bridge_env`, for a record with no header. The retired readings (5) `completion-check.py`'s whole-text `Satisfies` search, (6) `plan-check.py`'s `brief_scope` and (11) `plan-check.py`'s own `merged_ids` stay gone. The aim: each field of the plan and of a brief has one home, one reader and one type, so two programs can never read the same line two ways.

**The root cause (confirmed, common to most findings).** Header handling lives in each program instead of in one place.
- Each of the five programs has its own pre-filter on the `record:` kind (`header.get("record") == "brief"` or `== "build-plan"` before it calls `check_header`). So a header of the wrong kind, a header with no `record:` line, or an empty `---` / `---` block is treated as "no header" and the prose is read without a word, although `check_header` itself returns `['record']` for each of them (probed: `{}`, `{'record': 'breif', ...}` and `{'header': 1, 'id': ...}` all give `['record']`; `read_header("---\n---\n...")` returns `{}`).
- Each program chooses on its own whether to read the whole text or the body after the header, and some swallow `HeaderError` or `OSError`.
- There are two plan prose walkers (`plan-check.py`'s `parse` and `bridge_env.plan_prose_fallback`) plus a third inline one in `completion-check.py`, so the agreement check and the enforcement read different text.

**The fix is structural.**
- **One brief reading in `bridge_env`, called by every program.** For a brief it reads the header; it refuses a `HeaderError` and every `check_header("brief", ...)` finding, `record` included, as malformed; it returns the body; it builds the prose fallback from the body only, never re-parsing a header found in the body; and it returns the agreement result. `scope-check.py`, `plan-check.py`'s brief comparison, `bridge-run.py`, `review-guard.py` and the merge-unit and blocking-class readers all use that one reading. So what is checked is what is enforced: `scope-check.py` enforces the same body Scope it compared with the header.
- **One plan body walker in `bridge_env`.** It is used by `plan-check.py`'s `parse` and `stages_without_demonstration`, by the agreement fallback, and by `completion-check.py`'s header-less planned set. Each reads the body after the header, never the header block.
- **The blocking-class reading for the gates is prose-only.** A class with no prose `Blocking class:` line carrying a finding never reads as a lift. The launcher and the guard refuse a class lift whose line or finding is empty.
- **`review-guard.py` reuses `bridge_env.brief_header_refusal`** (with its `keys` parameter) rather than an inline copy.
- **Revert the out-of-scope edit** to TASK-046's `_plan_field_value` so that it is byte-identical to the checkpoint 4bdac19.

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
- tests/test_header_plan_r2.py
- tests/test_plan_check.py
- tests/test_scope_check.py
- tests/test_completion_check.py
- tests/test_bridge_run_review_ceiling.py
- tests/test_review_guard_ceiling.py
- tests/test_task032_supervisor_launcher.py
- docs/BUILDER_NOTES.md
- handoff/TASK-048-r2-report.md

Limits on these files:
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py`. Never edit it by hand.
- `tests/test_header_plan.py` and `tests/test_header_plan_r2.py` are the supervisor's. In each, you add your own cases only below its marker line, which stands exactly as follows: `# ---------------------------------------------------------------- builder's cases below this line`. You edit nothing above that line in either file.
- In the other six test files, you may only add cases. Do not rewrite an existing test. If you find an existing test that pins a retired reading, do not rewrite it: name it by its test id in your report and in your last message.
- In `bridge/cursor-bridge/bridge_env.py`, TASK-046's reader code and TASK-047's status readers stay out of scope (see Out of scope), with one required edit: the revert of `_plan_field_value` (finding RA-5).

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's: BUILD_PLAN.md, DESIGN.md, REQUIREMENTS.md, INVENTORY.md, PROJECT_STATUS.md, HARDENING.md and the diagrams. So are `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`; this increment changes no command. `handoff/TASK-048-r1-report.md` is round 1's and stays as it is.
- Every test file not listed in the Scope.
- TASK-046's reader code in `bridge_env.py`: `read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS` and their private helpers (`_plan_agrees`, `_plan_field_value`, `_kind_norm`, `_derived_historic`, `_demonstration_present`, `_find_block` and the rest). You add new functions beside them and call them. Two exceptions: (a) the required revert of `_plan_field_value` (RA-5); (b) if the existing `build-plan` or `brief` branch of `header_agrees` genuinely cannot meet a case in `tests/test_header_plan.py` or `tests/test_header_plan_r2.py`, you may fix that branch, and you report the change by line and by the case that needed it.
- TASK-047's status readers in `bridge_env.py`: `status_fallback`, `status_workflows`, `status_values` and their helpers.
- The tabular records' headers (TASK-049): `completion-check.py`'s `parse_register` and its register checks, and `plan-check.py`'s column-position read of `docs/diagrams/INDEX.md`, stay as they are.
- The run parameters' header and its lifts (`review_owner_lifts`, `Ceiling above twice:` and the rest): TASK-050.
- `records-migrate.py`: TASK-051.
- The duplicated helpers that `docs/HARDENING.md`'s TASK-047 section names (the `escape_field` copies, `_safe_exc_type_name` / `_bridge_env_refuse_line`). Do not add another copy of these or of any helper. Each reading you need has one copy, in `bridge_env`.
- Any mutation script. The mutants file and the mutation run are the supervisor's.

## Context
**The design that binds this increment.** In `docs/DESIGN.md`, section "## Change: release B2 (2026-11-04)", read: the `docs/BUILD_PLAN.md ...` and `handoff/<ID>[-r<N>].md` rows of the table under "### The records and their headers"; the paragraph "Three kinds of record, one rule each", items (1) and (2); the paragraph "The fallback readers, one copy each", with the enumerated retired readings, of which (5), (6) and (11) are this increment's; the paragraph "Header first; fallback; malformed"; and the paragraph "The reader". Three sentences there decide this round:
- "A header the reader cannot parse, or that fails its schema (... a `record:` kind the program did not expect ...) is **malformed** ... never silently falling back, since a typo would otherwise switch a record's parsing without a word."
- "The comparison in every kind is made by the fallback reader: *agreement* means the fallback's reading of the prose equals the header, so the one piece of code that reads prose is the one that migrated it and the one that checks it."
- "The header is never read past the first `---`...`---` block, and the body is everything after it; a `---` line later in a file (a Markdown rule) is body." A second front-matter block inside the body is therefore prose, never a header.

Also read `docs/REQUIREMENTS.md` row R-059, and TASK-048's entry in `docs/BUILD_PLAN.md`: its Scope, Scope notes and Done when. Round 1's brief `handoff/TASK-048.md` holds the full Requirements 1 to 12. Round 1's report is `handoff/TASK-048-r1-report.md`.

**What exists in `bridge/cursor-bridge/bridge_env.py` at HEAD (round 1's code).**
- TASK-046's reader, unchanged and to be called:
  - `class HeaderError(Exception)`, with `.line` (1-based, in the whole text); its message reads `line <n>: <what>`.
  - `def read_header(text)` returns `(mapping or None, body)` and raises `HeaderError` on a malformed block; an empty block (`---` then `---`) returns `({}, body)`.
  - `def check_header(kind, header)` returns a list of schema findings, empty when valid (kinds `"build-plan"` and `"brief"`).
  - `def header_agrees(kind, header, fallback)` returns a list of disagreement tokens. For `"brief"` the fallback dict holds `"name"`, `"satisfies"` (list), `"scope"` (list), `"merge_unit"` (list, tuple or `None`) and `"blocking_class"` (string or `None`); the tokens are `id`, `round`, `satisfies`, `scope`, `merge_unit`, `blocking_class`. For `"build-plan"` it calls `_plan_agrees(header, fallback)` with `{"merged": set or None, "stages": [{"name", "demonstration", "increments": [{"id", "title", "fields": {...}}]}]}`; the tokens are `<stage> name`, `<stage> demonstration`, `<ID> <field>`. `_plan_agrees` pairs stages and increments by position (existing behaviour). `tests/test_header_reader.py`'s `fallback_brief()`, `plan_header()` and `plan_fallback()` (lines 556, 594 and 603) are worked examples.
- Round 1 added, and this round reworks:
  - `HEAD_RX`, `FIELD_RX`, `STAGE_RX`, `DEMO_RX` (lines 320-326). `FIELD_RX` (line 321-324) reads `r"^\s*(?:[-*]\s+)?(Kind|Parent|Depends on|Parallel|Satisfies|Diagrams|Scope|Deferred)\s*:\s*(.*?)\s*$"`, `re.I`.
  - `read_blocking_class_line(text)` (line 388), `plan_increment_ids(folder)` (line 446), `merge_unit_line_present(text)` (line 482), `_merge_unit_from_prose(text)` (line 494), `_brief_well_formed_header(text)` (line 511), `_merge_unit_from_header(header)` (line 524), `merge_unit_ids(text)` (line 543).
  - `class ScopeAgreementError(ValueError)` (line 2478), `split_entry(entry)` (line 2482, returns `None` for an ellipsis, else `(paths, unread)`), `parse_scope(brief_text)` (line 2500, returns `(paths, refusal, unread)` with refusal `None`, `"ellipsis"` or `"empty"`), `brief_satisfies(text)` (line 2539), `plan_r_ids_outside_headers(text)` (line 2557), `plan_scope_agreement_entries(value)` (line 2586, raises `ScopeAgreementError`), `_plan_normalize_field` (line 2604), `plan_prose_fallback(text, merged=None)` (line 2641), `brief_prose_fallback(text, brief_name)` (line 2705), `brief_header_refusal(text, shown_path, keys=None)` (line 2732, returns `"header: <path>:<line> <what>"`, `"header: disagrees <key>"` or `None`), `plan_header_inc_ids(header)` (line 2755).
- Already present before this increment and used here: `PLAN_ID_PATTERN = r"TASK-\d{3,}[a-z]?"`, `parse_review_name(name)`, `squash_merged_ids(folder, id_rx, git_runner=None, ref="main")` (a set, or `None` when the log cannot be read), `squash_merged_ids_from_lines`, `declared_set_for_id`, `handoff_brief_tokens(argv)`, `BLOCKING_CLASSES`, `BLOCKING_CLASS_RE`, `MERGE_UNIT_RE`.

**Public names the tests call; keep them, with these signatures.** `bridge_env.brief_header_refusal(text, shown_path, keys=None)` (returns a string beginning `header: ` or `None`); `bridge_env.read_blocking_class_line(text)` (`(class, finding, line)` or `None`); `bridge_env.merge_unit_ids(text)` (a tuple or `None`, header first: `tests/test_header_plan.py::test_r059_merge_unit_ids_reads_the_header_first`); `bridge_env.plan_increment_ids(folder)` (returns the IDs; `test_r059_plan_increment_ids_reads_every_plan_file` compares `set(...)` of its result); `bridge_env.brief_satisfies(text)`; `bridge_env.plan_r_ids_outside_headers(text)`; and the moved names `parse_scope`, `split_entry`, `HEAD_RX`, `FIELD_RX`, `DEMO_RX` (`test_r059_the_moved_readers_live_in_bridge_env`). `tests/test_bug040.py` line 98 and `tests/test_loop_text_pace.py` line 123 call `read_blocking_class_line` on a lone prose line and must keep their result.

**Where the programs read today (round 1's code).**
- `plan-check.py`: `parse(paths)` (line 115) and `stages_without_demonstration(paths)` (line 145) read the whole file; `brief_scope_for(text, brief_name)` (line 182); `brief_findings(path, item)` (line 198); `plan_header_findings(path, text, merged)` (line 218); `historic_header_ids(header)` (line 249); `main()` (line 267), with the shape loop (lines 308-341), the parent / depends loop (lines 343-360) and the brief loop (lines 446-454). `scope_paths(value)` (line 81) stays as it is, for readiness, PARALLEL and BRIEF.
- `scope-check.py`: `_norm(p)` (line 74, strips a leading `./`, swaps backslashes); module-level `UNREAD` (line 90); `parse_scope(brief_path)` (line 93), the program's wrapper around `bridge_env.parse_scope`; `main(argv)` (line 259).
- `completion-check.py`: plan coverage (lines 153-215).
- `bridge-run.py`: `builder_review_refusal(argv, folder, kind)` (line 612); brief header check (lines 659-663); merge-unit check (lines 664-686); class lift (lines 704-732); `main` writes `bridge-run: refused - <reason>` to stderr and returns 125.
- `review-guard.py`: `scope_blocking_line(root, id_part)` (line 665) reads the SCOPE files (`run/review/SCOPE-<id>.md`, no header, read as today); `snapshot_review_refusal(nnn, root, common)` (line 682); `cmd_snapshot` (line 791) prints a refusal to stdout as its first line and exits 125.

**The supervisor's tests (fixed points).**
- `tests/test_header_plan_r2.py` (commit bd47c5e) holds the reproduction tests of this round. It names R-059 and D-002 and reuses `tests/test_header_plan.py`'s helpers and `tests/test_task032_supervisor_launcher.py`'s lab. On 46c7dc0 it gave `29 failed, 1 passed in 16.26s`. Every case must pass. Each finding below names the cases that pin it.
- `tests/test_header_plan.py` holds round 1's acceptance tests, which passed on round 1 and must stay green. Its module docstring pins the fixed lines (repeated in Requirement 13 below).
- The full suite on 46c7dc0 gave `4641 passed, 41 skipped in 1735.56s` (the skips environmental). So no failure is known in the files the Done section runs, apart from the 29 red cases of `tests/test_header_plan_r2.py` at bd47c5e.

**No regression on header-less records.** Review A confirmed that this repository's own header-less plan, register, diagrams index and all 138 briefs gave byte-identical `plan-check.py` and `completion-check.py` output, and identical brief Scope readings, between round 0 and round 1. That must still hold after round 2: a record with no header is read exactly as before. The supervisor checks this on copies of the records; you do not (see Development data).

**Security context.** The project's ASVS level is 2 (INVENTORY, Decisions; D-004). The trust boundary: the plan and the briefs are text the supervisor writes, but a builder or a reviewer can write them too. So the header reader's refusals stand. A gate program (the launcher, the guard) must refuse rather than guess between two readings: it never launches a builder on a brief whose `## Scope` and `scope` differ, never lifts a review ceiling on a class with no finding line, and never snapshots on a first brief whose `merge_unit`, `id` or `round` disagrees or that it cannot read. The reader executes nothing. No exception is swallowed: a `HeaderError` or an `OSError` becomes the stated refusal or finding, never a silent fallback in a checker or a gate. Output stays ASCII as today, apart from what a program already quotes from a record. `.cursor/rules/secure-coding.mdc` is in force for you.

**Development data.** The development build is the Workspace sources under `bridge/`. A session in this repository always runs the installed bridge, never the one being edited, and no record of this repository carries a header before TASK-054. For you, this means:
- Never run a program of this increment over this repository's own `docs/BUILD_PLAN.md`, `docs/BUILD_PLAN*.md` files, briefs under `handoff/`, or any other record. The supervisor runs the header-less regression check above.
- Every test runs on fixtures written under pytest's `tmp_path`, in temporary git repositories the test builds.

**Host.** Nothing in this increment depends on a host fact. The design's Version section records Claude Code 2.1.317.

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

A solid edge is a plain `import bridge_env` statement, which `check:components` sees; all five programs have it now (each after `sys.path.insert(0, HERE)`, so it works when `tools/dump-cli.py` loads `completion-check.py` and `plan-check.py` by file, the dotted edges). No program may gain any other import or load by file. If the task cannot be done within the diagram, stop and report the conflict instead of deviating.

## Requirements
The findings, each with its evidence, its fix and its pinning cases (`tests/test_header_plan_r2.py::<name>` unless another file is named; a bracketed list names the parametrized ids). The labels (B1, RA-1, AD-1, ...) are the ones to use in your report.

1. **B1 (blocking, security). scope-check enforces a different Scope from the one the header was checked against.**
   - Evidence: the agreement check (`scope-check.py` lines 102-116) compares the header with `parse_scope(body)` through `brief_prose_fallback`, but the enforcement at line 118 calls `bridge_env.parse_scope(text)` on the whole file, header block included. A brief can put a `## Scope` comment as the header's last line and a `- **` line straight after the closing `---`. Header and prose then agree on `src/a.py`, the launcher launches and plan-check uses `src/a.py`, but scope-check reads `**` and prints `VERDICT: SCOPE CLEAN` on a commit touching `bridge/evil.py` (reproduced end to end; the control brief gives SCOPE DRIFT).
   - Required: scope-check enforces the body's Scope, the same reading the fallback compared with the header, taken from the one brief reading (the root cause's fix). plan-check's brief comparison and the launcher read that same Scope.
   - Pinned by: `test_r059_r2_scope_check_enforces_the_scope_the_header_was_checked_against`.
2. **B2 (blocking, security / defeated safety mechanism). A header class with no prose line reads as a lift with an empty line.**
   - Evidence: `read_blocking_class_line` (`bridge_env.py` lines 388-405) returns `(bc, "", "")` from its header-first branch when no body line carries the class (line 403). `brief_prose_fallback` (line 2721) calls `read_blocking_class_line(body)`, which parses the body again for a header. A brief with two well-formed front-matter blocks, both `blocking_class: "security"`, and no prose `Blocking class:` line: the agreement check passes (the fallback reads the second block's class); `bridge-run.py` line 712 gets `("security", "", "")`, which is truthy, so line 722 sets `lift = "class"` with `lift_line = ""`. The class-used set (line 708) records only truthy `lift_line` values, line 1580 never writes an empty one, and `review-guard.py` line 748 has the same truthiness test. Result: unlimited builder rounds above the ceiling, and the reviewers get no finding text to confirm or deny.
   - Required: `read_blocking_class_line` returns a class only from a prose `Blocking class: <class> - <finding>` line (in the body, where the text has a header), with a non-empty finding and line, else `None`; it never returns an empty finding or line and never re-parses a header found in the body. The brief fallback reads the class the same prose-only way, so a header `blocking_class` with no such prose line disagrees (`header: disagrees blocking_class`). `builder_review_refusal` and `review-guard.py`'s ceiling check refuse a class lift whose line or finding is empty, whatever the reader returns.
   - Pinned by: `test_r059_r2_a_class_with_no_prose_line_never_reads_as_a_lift` [one-header, two-headers], `test_r059_r2_a_header_class_with_no_prose_line_is_refused` [one-header, two-headers], `test_r059_r2_the_launcher_never_lifts_the_ceiling_on_a_second_header`.
3. **RA-1 (blocking). Five programs silently fall back on a header of the wrong `record:` kind.**
   - Evidence: the pre-filters at `bridge_env.py` line 2738 (`brief_header_refusal`), line 517 (`_brief_well_formed_header`), line 468 (`plan_increment_ids`), `review-guard.py` line 701, `scope-check.py` line 106, `plan-check.py` line 227, and `completion-check.py` lines 168 and 201. Each treats `record: breif`, a missing `record:` line or an empty block as no header.
   - Required: whenever `read_header` returns a mapping (not `None`), the reading runs `check_header(kind, header)`; any finding, `record` included, is malformed: `HEADER MALFORMED: <path>:1 <what>` (exit 2) in the checkers, the `refused - header: ` line (exit 125) in the gates. No program tests `header.get("record")` itself.
   - Pinned by: `test_r059_r2_a_brief_header_of_the_wrong_kind_is_refused` [typo, missing, empty], `test_r059_r2_scope_check_refuses_a_header_of_the_wrong_kind` [typo, missing, empty], `test_r059_r2_the_launcher_refuses_a_header_of_the_wrong_kind`, `test_r059_r2_the_guard_refuses_a_first_brief_of_the_wrong_kind`, `test_r059_r2_a_plan_header_of_the_wrong_kind_is_malformed` [plan-check, completion-check].
4. **RA-2 (blocking) and the audit's advisory. plan-check crashes on a headed plan whose `Scope:` has an unbalanced parenthesis.**
   - Evidence: `plan_header_findings` (`plan-check.py` line 233) calls `plan_prose_fallback`, which calls `_plan_normalize_field`, which calls `plan_scope_agreement_entries`, which raises `ScopeAgreementError` (`bridge_env.py` line 2599), uncaught: a traceback, exit 1, no SHAPE line. The merged case gives the same traceback, where round 1's Requirement 5 says it is "read as today and no failure is printed".
   - Required: the fallback records the refusal per increment instead of raising. plan-check prints `SHAPE: <id> has an unbalanced parenthesis in its Scope` (a `SHAPE: <id>` line containing `parenthes`) for an unmerged increment and prints no parenthesis line for a merged one. No traceback in either case. What the header comparison reports for such an increment's `scope` is yours to decide; report it under `Assumed, not verified`.
   - Pinned by: `test_r059_r2_a_headed_plan_with_an_unbalanced_unmerged_scope_gets_the_shape_line`, `test_r059_r2_a_headed_plan_with_an_unbalanced_merged_scope_is_read_as_today`.
5. **RA-3 (blocking). scope-check's ellipsis line lost its entry.**
   - Evidence: round 0 printed `CANNOT VERIFY: a Scope entry carries an ellipsis (src/core/a.py, src/core/b.py, ...); name every path or a glob.` (the entry, cut at 80 characters, `entry[:80]`). Round 1 prints it without the entry (`scope-check.py` line 121). Round 1's Requirement 1 kept the `CANNOT VERIFY:` lines unchanged.
   - Required: `bridge_env.parse_scope` gives the refused entry with the ellipsis refusal (an ellipsis is three dots or U+2026), and scope-check prints the round-0 line, exit 2, as before. The `bridge_env` copy still prints nothing, never exits and keeps no module-level state.
   - Pinned by: `test_r059_r2_the_ellipsis_refusal_quotes_its_entry`.
6. **RA-4 (should fix). A leading `./` on a Scope bullet gives a false SCOPE DRIFT.**
   - Evidence: round 0's scope-check passed every entry through `_norm` (strips a leading `./`, swaps backslashes); the moved `bridge_env.parse_scope` (line 2530) only swaps backslashes, and scope-check no longer calls `_norm` on entries.
   - Required: the leading `./` strip lives in the one copy, `bridge_env.parse_scope`, so every reader of a brief's Scope gets the same entries.
   - Pinned by: `test_r059_r2_a_leading_dot_slash_on_a_scope_bullet_is_stripped`.
7. **RA-5 (should fix). Out-of-scope edit to TASK-046's private helper.**
   - Evidence: `bridge_env.py` lines 2002-2003 in `_plan_field_value` add `if fk in ("depends_on", "diagrams", "scope", "satisfies") and isinstance(val, list): return val`, and round 1's report said "none".
   - Required: revert it, so that `_plan_field_value` is byte-identical to the checkpoint 4bdac19 (`git diff 4bdac19 -- bridge/cursor-bridge/bridge_env.py` shows no hunk inside it). If a case then fails because the fallback hands `_plan_agrees` a list it does not expect, fix the fallback's values, not the helper.
   - Pinned by: no test; the supervisor checks the diff.
8. **RA-6 (should fix). The historic exemption goes beyond the shape rules.**
   - Evidence: `plan-check.py` lines 345-346 (`if tid in historic_exempt: continue`) skip the readability check and also the PARENT existence check, the not-a-group check and the registration of the child under its group. Results: a false `SHAPE: group TASK-010 has no child increments`, and a dropped `PARENT: TASK-011 names parent TASK-099, which does not exist`.
   - Required: a `historic: true` increment whose ID the merged set holds is exempt from the shape rules only: a missing `Scope:` line, the `Kind:` value check, `Parallel`'s value, and the `Parent` / `Depends on` readability (`DEPENDS: ... unreadable ...`). The PARENT checks and the child registration run for it as for any increment.
   - Pinned by: `test_r059_r2_a_historic_childs_parent_is_still_checked`, `test_r059_r2_a_historic_child_still_counts_as_its_groups_child`.
9. **RA-7 (should fix). The unbalanced-parenthesis check is skipped under `--no-git` or an unreadable log.**
   - Evidence: `plan-check.py` line 330 (`if not exempt and merged_set is not None and tid not in merged_set`).
   - The supervisor's ruling: under `--no-git` or an unreadable log, nothing counts as merged for the parenthesis rule (as readiness does: "readiness assumes nothing merged"), so the rule applies to every increment there that is not historic-exempt. The historic mark keeps its own rule: under `--no-git` or an unreadable log it is accepted, never a failure, with the `note:` line naming the increments not re-checked.
   - Pinned by: `test_r059_r2_under_no_git_an_unbalanced_scope_is_a_shape_failure`.
10. **RA-8 (should fix) and the audit's advisory. `HeaderError` and `OSError` are swallowed.**
    - Evidence (plan-check): `brief_scope_for` (`plan-check.py` lines 182-195; the `except` at line 186) falls back to the prose on a malformed brief header. It also reads inverted (Review A, advisory 12): an agreeing header returns the header's scope, a disagreeing one the prose's.
    - Required (plan-check): a brief whose header is malformed (a `HeaderError` or any `check_header` finding, `record` included) is a finding in the brief comparison, printed as a `BRIEF: <brief path> ...` line that names the brief file and the header fault (suggested: `BRIEF: handoff/TASK-003.md header: handoff/TASK-003.md:<line> <what>`) and counted with the other failures before `RESULT:`, never a silent fallback. For a brief with a well-formed header, the Scope plan-check compares is the body's Scope from the one brief reading, the same one scope-check enforces and the launcher checks (equal to the header's `scope` where they agree). A disagreeing brief header is scope-check's finding and the launcher's refusal; plan-check adds no line for it. `brief_scope_for`, if it survives, reads plainly.
    - Evidence (guard): `review-guard.py` lines 690-695: `os.path.isfile(brief_path)` is false for a path that exists but is not a regular file, and an existing first brief that cannot be read (`OSError`) becomes `""`; either way the header check is skipped.
    - Required (guard): a first brief `handoff/<id>.md` that exists (any kind of filesystem entry) but cannot be read as a file is a refusal, exit 125, with a line beginning `review-guard: refused - `. Where `handoff/<id>.md` does not exist, or exists and has no header, the guard behaves as today.
    - Pinned by: `test_r059_r2_plan_check_reports_a_malformed_brief_header`, `test_r059_r2_the_guard_refuses_a_first_brief_it_cannot_read`.
11. **RA-9 (should fix) and the audit's advisory. More than one plan walker; the walkers read the header block.**
    - Evidence: `completion-check.py` lines 179-193 walk the increments themselves (`HEAD_RX`, a `#` reset, `FIELD_RX`). `bridge_env.plan_prose_fallback` (line 2641) walks the plan a second time beside `plan-check.py`'s `parse` (line 115), and the two can diverge (`plan_prose_fallback` drops increments before the first `##` heading, `parse` keeps them). `plan-check.py` lines 120 (`parse`) and 151 (`stages_without_demonstration`) read the whole file, header block included: a `### TASK-099 - x` comment inside a plan header became a phantom increment with the header's YAML lines as its fields.
    - Required: one plan body walker in `bridge_env`, used by `plan-check.py`'s `parse` and `stages_without_demonstration`, by the agreement fallback, and by `completion-check.py`'s header-less planned set. Each reads the body after the header, never the header block. `completion-check.py` uses none of `bridge_env.HEAD_RX`, `FIELD_RX`, `DEMO_RX` or `STAGE_RX` itself. For a header-less file, the walker's reading gives exactly round 1's answers in each program (which are round 0's in plan-check, and round 1's FIELD_RX-inside-an-increment reading in completion-check): for example, `parse`'s keeping of an increment before the first `##` heading, its duplicate-ID check across files, and `stages_without_demonstration`'s per-file stages stay as they are.
    - Pinned by: `test_r059_r2_completion_check_walks_no_plan_of_its_own`, `test_r059_r2_a_heading_comment_inside_a_plan_header_is_no_increment`.
12. **The audit's other advisories.**
    - **AD-1. `FIELD_RX` is quadratic.** Evidence: `bridge_env.py` line 321, `(.*?)\s*$`, on a value followed by a long run of spaces, a word and another run (40,000 spaces took 2.9 s; 20,000 took 0.7 s); it now runs on every brief line through `brief_satisfies` in the launcher. Required: capture the value with `(.*)$` and remove its trailing whitespace in code, so every consumer gets the same value the old capture gave (the rule is unchanged). Pinned by: `test_r059_r2_the_field_reading_is_linear_on_a_long_run_of_spaces`.
    - **AD-2. The launcher's plan reading trusts a header alone and falls back silently.** Evidence: `plan_increment_ids` (`bridge_env.py` lines 461-479) uses a well-formed plan header's IDs without checking them against the headings, and on a `HeaderError` falls back to scanning the whole text, header included. The supervisor's ruling: when the merge-unit check reads the plan files (`bridge-run.py` lines 670-686), the launcher refuses with exit 125 and a line beginning `bridge-run: refused - header: ` that names the plan file (for example `docs/BUILD_PLAN-2026-11-04.md`) where a plan file has a malformed header (a `HeaderError` or any `check_header("build-plan", ...)` finding, `record` included) or a well-formed header whose increment IDs differ from the IDs of the body's `###` headings. A header-less plan file is read by its body headings as today. How `plan_increment_ids` reports the refusal to the launcher (an exception the launcher turns into its line, or a companion function) is yours, as long as no caller silently falls back and `set(plan_increment_ids(folder))` still gives the IDs for readable plans. Pinned by: `test_r059_r2_the_launcher_refuses_a_malformed_plan_header`, `test_r059_r2_the_launcher_refuses_a_plan_header_whose_increments_have_no_heading`.
    - **AD-3 (informational, optional, no test).** `bridge-run.py` lines 672 and 686 name only `docs/BUILD_PLAN.md`, although addendum files are read too. You may name the plan files read; if you do, every existing test in Done step 3 must stay green.
    - **Review A, advisory 14 (ruled: no change).** For a header-less plan, completion-check counts an increment's own `Satisfies:` line as `FIELD_RX` reads it, so a bold `**Satisfies**:` line is no field, as plan-check never read one either. Keep it so.
13. **Round 1's requirements stand** (full text in `handoff/TASK-048.md`, Requirements 1 to 12). In short, and with the fixed lines the tests pin:
    - The fallback readers live in `bridge_env`, one copy each: `HEAD_RX`, `FIELD_RX`, `DEMO_RX`, `parse_scope`, `split_entry`, `brief_satisfies`, `plan_r_ids_outside_headers`. The `bridge_env` copies print nothing, never call `sys.exit` and keep no module-level state. `plan-check.py` compiles none of `HEAD_RX`, `FIELD_RX`, `DEMO_RX`, defines no `brief_scope` or `merged_ids`, and calls `bridge_env.squash_merged_ids(os.getcwd(), bridge_env.PLAN_ID_PATTERN, ref=<--base>)`. `completion-check.py` keeps no `Satisfies` regex and calls `bridge_env.plan_r_ids_outside_headers`.
    - plan-check: `HEADER MALFORMED: <path>:<line> <what>`, exit 2 (`<path>` with forward slashes, `<line>` the `HeaderError`'s line or `1` for a schema finding); `HEADER DISAGREES: <id> <field>` or `HEADER DISAGREES: <stage> <field>`, a failure, exit 1; an increment in the header with no heading, or a heading with no header entry, is a failure naming the ID; a `--base` beginning with `-` exits 2 with one line and no traceback, before any git command; the note `could not read git log of <base> - readiness assumes nothing merged` stays; the historic mark on an unmerged increment is a failure naming it, and under `--no-git` it is accepted with a `note:` line naming the increments not re-checked.
    - scope-check: `HEADER MALFORMED: <path>:<line> <what>` and `HEADER DISAGREES: <key>`, each exit 2; `NOT READ AS A PATH: ...`, the `CANNOT VERIFY: ...` lines and `sys.exit(2)` for an unreadable brief, an ellipsis and an empty Scope, as in round 0; `VERDICT: SCOPE CLEAN` (exit 0) or `VERDICT: SCOPE DRIFT` (exit 1).
    - completion-check: `HEADER MALFORMED: <path>:<line> <what>`, exit 2; `HEADER DISAGREES: satisfies`, exit 1, where an R-id on any `Satisfies:` line in a headed plan file's body stands in no increment's header `satisfies` across the headed plan files; for a file with no header, only an increment's own `Satisfies:` line counts.
    - The launcher: `bridge-run: refused - header: <path>:<line> <what>` and `bridge-run: refused - header: disagrees <key>`, exit 125, every key, before any launch, slot or `runs.jsonl` line. The guard: `review-guard: refused - header: <path>:<line> <what>` and `review-guard: refused - header: disagrees <key>` on the branch's first brief, comparing `merge_unit`, `id` and `round` only, printed to stdout as the first line, exit 125. The guard gets its refusal from `bridge_env.brief_header_refusal(text, shown_path, keys=("merge_unit", "id", "round"))` (or the one brief reading behind it), not from an inline copy of the steps.
    - `merge_unit_ids`, `merge_unit_line_present` and `read_blocking_class_line` never raise `HeaderError` to a caller; the gates refuse a malformed brief header themselves before they rely on these readers.
    - An agreeing header gives the same answer as the header-less file in each of the five programs. A header-less record is read exactly as before.
    - No program's prose quotes a retired pattern (KP-073): no pattern in a docstring, a comment or a help text.
14. **One reading per record kind, and nothing read twice.** After this round, none of the five programs calls `bridge_env.read_header`, `bridge_env.check_header` or `bridge_env.header_agrees` for a brief or a plan itself, and none tests `header.get("record")`: each calls `bridge_env`'s one reading for the kind. No function re-parses a header inside a body it was handed.
15. **Housekeeping.** Do not edit the module docstring, the argparse help or any option of the five programs; `python tools/dump-cli.py --check` must stay green with the reference unchanged. Regenerate `bridge/cursor-bridge/MANIFEST.json` with `python tools/make-manifest.py` (no `--version`) and quote its output. Add no dependency; `pyyaml` stays test-only and no program imports it.

## Acceptance criteria
- [ ] `python -m pytest -q tests/test_header_plan.py tests/test_header_plan_r2.py` passes whole: every supervisor case above each marker, and your own cases below them.
- [ ] Each finding above is fixed at the mechanism its evidence names: B1 (scope-check enforces the body Scope it compared), B2 (the class read from a prose line with a finding only; the gates refuse an empty lift line or finding), RA-1 (every `check_header` finding, `record` included, is malformed in all five programs), RA-2 (no traceback; the SHAPE line for an unmerged increment), RA-3, RA-4, RA-5 (`_plan_field_value` byte-identical to 4bdac19), RA-6, RA-7, RA-8, RA-9 (one plan body walker), AD-1, AD-2.
- [ ] The bundles of Done steps 2 to 5 pass. Every existing test in them is green, and no test file outside the Scope is edited.
- [ ] No program of the five calls `read_header`, `check_header` or `header_agrees` for a brief or a plan itself, or tests `header.get("record")` (Requirement 14).
- [ ] Readings (5), (6) and (11) stay gone as uses; the moved readers live in `bridge_env`, one copy each, printing nothing, never exiting, with no module-level state.
- [ ] Each fixed line holds as Requirement 13 lists it, with its exit code. A header-less plan, register or brief is read exactly as before (the supervisor checks this on this repository's records).
- [ ] `python tools/dump-cli.py --check` is green with `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` unchanged. MANIFEST is regenerated. No option is added, removed or reworded, and no dependency is added.
- [ ] `python bridge/cursor-bridge/diagram-check.py --mode code` gives `RESULT: OK`.
- [ ] R-059 is fully met, with no stand-in or placeholder. Every case you add names R-059 in its name, docstring or a comment, and the cases you add for a rule include the negative path (a case that would fail if the rule were broken), not the positive path alone (Review A, 15).
- [ ] No new Semgrep high findings. No exception is swallowed. The gate programs refuse rather than fall back on a malformed or disagreeing brief header, an unreadable first brief, a malformed or disagreeing plan header in the merge-unit check, and an empty class lift (ASVS L2).

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Do not fix by suppressing the symptom: no retry, no broad `try/except`, no widened tolerance, no added `sleep`, no null-check that hides a wrong value. A caught exception becomes the stated finding or refusal line.
- Do not edit the reproduction tests: nothing above the marker line in `tests/test_header_plan_r2.py` or `tests/test_header_plan.py` changes. Leave no debug line or stray print.
- If you believe the real cause of a finding is different from the one named here, stop, do not change code for that finding, and report why in your summary; the supervisor will re-diagnose.
- Any console process your code launches on Windows is created windowless: the program's existing `NO_WINDOW`, and in tests `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)`, spelled literally in each call, as `tests/test_header_plan.py`'s `run()` and `git()` do (`tests/test_tests_windowless.py` checks the spelling). Every git call gets a timeout.
- A parametrized test you add takes a plain `ids=` list (as the supervisor's cases do).
- **Run every command in the foreground and wait for it to end.** Start nothing in the background or asynchronously, and leave no process running when you finish. Never start a server, a watcher or a daemon.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). An earlier round of this release ran it asynchronously and ran out its two-hour limit (ISS-030). The supervisor runs the full suite. Run only the commands the Done section lists.
- **Run the Done commands exactly as written, with no `PYTHONPATH` or other environment change.** Round 1's report took its counts from a run with `PYTHONPATH=bridge/cursor-bridge` and named a stale commit; the supervisor's commit 90f1b8f set the two harnesses that needed it right, so no environment change is needed.
- An increment that starts a process: your tests start the programs and git as children through `subprocess.run`, with output captured and a timeout. Each child is windowless and ends before the test does, and nothing outlives the test.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. Run the programs only on fixtures under `tmp_path`, never on this repository's plan, briefs or records (the Development data paragraph in Context).
- No value in this brief is marked as the owner's.
- Follow existing conventions in the files you touch: ASCII output, the `SHAPE:` / `BRIEF:` / `note:` / `RESULT:` lines of `plan-check.py`, the `CANNOT VERIFY:` lines of `scope-check.py`, and the `bridge-run: refused - ` and `review-guard: refused - ` prefixes. The five programs' fixed lines and exit codes stay as Requirement 13 lists them.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- Numbers from text are parsed with the language's own parser, never by slicing a string. A brief's `round` is the header's integer, compared with `parse_review_name`'s integer. A header line number comes from `HeaderError.line` (an int, 1-based) or is the literal `1`.
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root. The supervisor checks this increment's tests by mutation in its own run, with its own mutants file. You may mutate by hand in-process in your own run to test your cases; if you do, list each mutation and what caught it. No mutation script lands in the diff.
- No failure is known in the files the Done section runs, apart from the 29 cases of `tests/test_header_plan_r2.py` this round is to turn green. If another test there fails and this change did not cause it, report it by its test id and fix none.
- Prefer reuse over new code: call `header_agrees` rather than writing a second comparison, keep one copy of each reading, and write the minimum that meets the acceptance criteria. This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-048-r2-report.md`. Write it as you go, so that nothing of it is lost if your run ends early. It records what you did, what you changed, what you ran and what it printed, and what you could not do.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for each finding label (B1, B2, RA-1 to RA-9, AD-1, AD-2, AD-3), one sentence on how the change addresses the named cause at its mechanism;
- every change to TASK-046's or TASK-047's code in `bridge_env.py`, by line, compared with 4bdac19 (expected: none, once `_plan_field_value` is reverted), with the case that needed it, or "none";
- any existing test you found that pins a retired reading, by test id (or "none");
- the manifest command you ran and its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value or a wording you chose (for example what the header comparison reports for a `scope` the fallback refused in RA-2, or how `plan_increment_ids` reports a refusal in AD-2). Write one item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item. Make it accurate: round 1's assumption 3 ("`read_blocking_class_line` returns `None` when the header names a class but the prose line is absent") was wrong, and that is how B2 shipped. State as assumed only what you did not check, and check what you can.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change:
1. `python -m pytest -q tests/test_header_plan.py tests/test_header_plan_r2.py`
2. `python -m pytest -q tests/test_plan_check.py tests/test_plan_demonstration.py tests/test_scope_check.py tests/test_completion_check.py tests/test_a4_review_fixes.py tests/test_a4_followups.py tests/test_a5_followups.py`
3. `python -m pytest -q tests/test_bridge_run.py tests/test_bridge_run_review_ceiling.py tests/test_bridge_run_design_ceiling.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_r4.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_hotfix25a_roster_launcher.py`
4. `python -m pytest -q tests/test_review_guard.py tests/test_review_guard_ceiling.py tests/test_review_guard_a4.py tests/test_task032_supervisor_guard.py tests/test_d003_review_round_states.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_bug036.py tests/test_bug038.py tests/test_bug039.py tests/test_bug041.py tests/test_bug042.py tests/test_bug043.py`
5. `python -m pytest -q tests/test_header_reader.py tests/test_header_schemas.py tests/test_header_status.py tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_mutation_run.py`
6. `python tools/dump-cli.py --check`
7. `python tools/make-manifest.py`
8. `python bridge/cursor-bridge/diagram-check.py --mode code`. This is the Workspace copy, and it is read-only.
9. `git rev-parse HEAD` and `git status --short`

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Each pytest summary line is quoted verbatim in a fenced block; never restate a count in prose. A claim that a check passed quotes the output line that shows it, and a number of failing or skipped cases is backed by the pytest lines naming them. A command you did not run is written `not run`, never described as run. Write the report's results after step 9, naming the commit its counts belong to (the `git rev-parse HEAD` output) and whether the working tree then held uncommitted changes (the `git status --short` output).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
