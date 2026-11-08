# TASK-048-r3: The plan's and the briefs' headers, round 3 (the reviewers' findings on round 2)

## Objective
Fix the following confirmed defect — repair the named cause, nothing else. This brief covers the findings that the security audit and Review A raised on round 2 of TASK-048 (the builder's commit 7dacef3 on branch `task-048`, written against `handoff/TASK-048-r2.md`). Every finding below is to be fixed in this round. Each one gives its evidence at `file:line`, the required behaviour, and the cases that pin it. The lines are those of the current HEAD, 04e91ab, which holds round 2's code unchanged plus the supervisor's new tests. The increment itself is unchanged. Round 1's brief `handoff/TASK-048.md` and round 2's brief `handoff/TASK-048-r2.md` stay in force wherever this brief does not override them. This brief restates what you need from them, and where they differ, this brief governs.

**This is round 3, the last round under the three-round review ceiling.** After this round, only a finding of one of the five blocking classes can send the work back. So close each finding at the mechanism its evidence names, and finish the structure described below. Do not stop at the symptom a test happens to probe. Both reviewers confirmed these round-1 labels fixed at their mechanism on round 2: B1, B2, RA-1, RA-3, RA-4, RA-5, RA-6, RA-8, AD-1, AD-2, and round 2's Requirement 14 as written. Keep them fixed. The cases in `tests/test_header_plan.py` and `tests/test_header_plan_r2.py` that pin them must stay green.

**What the increment is (unchanged).** Release B2 gives every `docs/BUILD_PLAN*.md` file a YAML front-matter header (`record: build-plan`) and every brief under `handoff/` a header (`record: brief`). TASK-046 built the header reader, the schemas and the agreement helper in `bridge/cursor-bridge/bridge_env.py`. TASK-047 made the status file's readers read its header first. This increment makes the five programs that read the plan and the briefs (`plan-check.py`, `scope-check.py`, `completion-check.py`, `bridge-run.py`, `review-guard.py`) read the header first through `bridge_env`. Each compares the header with the prose, and for a record with no header each falls back to one prose reading per field, kept in `bridge_env`. The retired readings stay gone: (5) `completion-check.py`'s whole-text `Satisfies` search, (6) `plan-check.py`'s `brief_scope`, and (11) `plan-check.py`'s own `merged_ids`. The aim is that each field of the plan and of a brief has one home, one reader and one type, so that two programs can never read the same line two ways.

**The root cause (confirmed, still common to the findings).** Round 2 moved the header handling into `bridge_env`, but kept it in several places there. Every round-3 blocking finding below is a place where two of these readings disagree.
- **Six brief functions each call `read_header` and `check_header` themselves:** `brief_body` (`bridge_env.py` 388-396), `_brief_well_formed_header` (514-524), `brief_header_refusal` (2714-2734), `brief_malformed_brief_line` (2824-2835), `brief_enforced_scope_paths` (2838-2853) and `brief_scope_enforcement` (2856-2874). They already differ: `brief_body` and `_brief_well_formed_header` fall back to the whole text on a malformed header. `brief_prose_fallback` (2695-2711) also calls `brief_satisfies(text)`, which calls `brief_body` and so reads the header a second time.
- **There are still four plan readings:** `plan-check.py`'s `parse` (115-146) and `stages_without_demonstration` (149-175), `bridge_env.plan_prose_fallback` (2633-2692), the new `bridge_env.plan_collect_satisfies_ids` (2749-2765), and `bridge_env.plan_increment_ids` (459-482). `plan_body` (399-407) only strips the header.

**The structure to finish.**
- **One brief reading.** One function in `bridge_env` reads a brief once and returns one result: the header or `None`, the body, the refusal or `None`, and the prose fallback built from the body. The result also carries the agreement result (the list `header_agrees` gives; it is empty when there is no header). Every brief reader takes what it needs from that result. That covers `brief_header_refusal`, `read_blocking_class_line`, `merge_unit_ids`, `merge_unit_line_present`, `brief_satisfies`, scope-check's enforcement, plan-check's brief comparison, the launcher and the guard.
  - No second `read_header` call for a brief, anywhere.
  - No whole-text fallback on a malformed header.
- **One plan walker.** One function in `bridge_env` walks a plan file's body, the text after the header, never the header block. Per file, it returns the body's stages and their increments with their field lines, and the increments that stand outside any stage. These all consume it: `plan-check.py`'s `parse` and `stages_without_demonstration`, the agreement fallback, `completion-check.py`'s header-less planned set, and `plan_increment_ids`. `plan-check.py` and `completion-check.py` use none of `bridge_env`'s `HEAD_RX`, `FIELD_RX`, `DEMO_RX` or `STAGE_RX` themselves (a test pins this).
- **One text reading.** One function in `bridge_env` reads and decodes a record's text, used by all five programs for every brief and plan file they read (R3-4).

Satisfies: R-059 - The plan's and the briefs' headers. Every `docs/BUILD_PLAN*.md` file carries `record: build-plan` with its `stages` (name, demonstration, increments with `id`, `title`, `kind`, `parent`, `depends_on`, `parallel`, `diagrams`, `scope`, `satisfies`, `deferred`, `historic`). Three programs read it first:
- `plan-check.py` compares each increment's header fields with its prose field lines where the prose has them, under these normalisations:
  - `parallel`'s `yes` and `no` read as `true` and `false`;
  - an absent optional scalar's line reads as `null`, and an absent list's line as the empty list;
  - the filler `none` counts as an absent line;
  - `kind` is compared against `increment` where the `Kind:` line is absent;
  - an increment's `title` is compared against its heading's title;
  - each stage's `name` and `demonstration` are compared against its heading and the presence of its `Demonstration:` line.

  It fails a difference. It reports a `Scope:` entry with an unbalanced parenthesis as a shape failure for an unmerged increment. It exempts a `historic: true` increment from the shape rules, and from nothing else, only where the merged set holds the ID. That set is read by the one function `bridge_env.squash_merged_ids(folder, PLAN_ID_PATTERN, ref=<--base>)`, with `origin/main` as the default base, and the program's own `merged_ids` is retired. A mark on an unmerged increment is a finding. Under `--no-git` or an unreadable log, the mark is accepted with a note. A `--base` beginning with `-` is refused.
- `completion-check.py` reads `satisfies`. Its agreement rule: every R-id its retired whole-text search would have found in a plan file stands in some increment's header `satisfies`; otherwise it reports `HEADER DISAGREES: satisfies`. The sweep is one function in `bridge_env`, and the program's own whole-text regex is gone.
- `bridge_env.plan_increment_ids` is the one reader over every plan file, for `bridge-run.py`.

Every brief carries `record: brief` with these keys:
- `id` and `round` (`round` is an integer, equal to the file's name as `parse_review_name` reads it, 1 for a plain name);
- `satisfies` (its prose is the brief's `Satisfies:` line);
- `scope`;
- `merge_unit` and `blocking_class` (their prose is the `Merge unit:` and `Blocking class:` lines).

Four readers read it first:
- `scope-check.py` is the brief's checker. It compares every key with its prose or with the file's name (`scope` with the `## Scope` bullets as `parse_scope` reads them, with its refusals). It fails a difference with `HEADER DISAGREES: <key>` and exit 2, as an unreadable Scope exits.
- `plan-check.py` reads `scope` and `satisfies`, and its own `brief_scope` is retired.
- `bridge_env`'s merge-unit and blocking-class readers, for `bridge-run.py` and `review-guard.py`.
- `bridge-run.py` and `review-guard.py` themselves:
  - They refuse a malformed brief header with exit 125 and a message beginning `bridge-run: refused - header: ` or `review-guard: refused - header: `.
  - They refuse a header that disagrees with its prose or its name the same way (`... refused - header: disagrees <key>`). The launcher checks every key before any builder is launched. The guard checks `merge_unit`, `id` and `round` of the branch's first brief before a snapshot.

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
- tests/test_header_plan_r3.py
- tests/test_plan_check.py
- tests/test_scope_check.py
- tests/test_completion_check.py
- tests/test_bridge_run_review_ceiling.py
- tests/test_review_guard_ceiling.py
- tests/test_task032_supervisor_launcher.py
- docs/BUILDER_NOTES.md
- handoff/TASK-048-r3-report.md

Limits on these files:
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py`. Never edit it by hand.
- `tests/test_header_plan.py`, `tests/test_header_plan_r2.py` and `tests/test_header_plan_r3.py` are the supervisor's. In each of them:
  - you add your own cases only below its marker line, which stands exactly as follows: `# ---------------------------------------------------------------- builder's cases below this line`;
  - you edit nothing above that line.
- In the other six test files, you may only add cases. Do not rewrite an existing test. If you find an existing test that pins a retired reading, do not rewrite it: name it by its test id in your report and in your last message.
- In `bridge/cursor-bridge/bridge_env.py`, TASK-046's reader code and TASK-047's status readers stay out of scope (see Out of scope). `_plan_field_value` stays byte-identical to the checkpoint 4bdac19.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names.
  - Every record under docs/ is the supervisor's: BUILD_PLAN.md, DESIGN.md, REQUIREMENTS.md, INVENTORY.md, PROJECT_STATUS.md, HARDENING.md and the diagrams.
  - So are `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`; this increment changes no command.
  - `handoff/TASK-048-r1-report.md` and `handoff/TASK-048-r2-report.md` are the earlier rounds' and stay as they are.
- Every test file not listed in the Scope.
- TASK-046's reader code in `bridge_env.py`: `read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS` and their private helpers (`_plan_agrees`, `_plan_field_value`, `_kind_norm`, `_derived_historic`, `_demonstration_present`, `_find_block`, `_line_end_len`, `_split_physical_lines` and the rest). You add new functions beside them and call them. The one exception: if the existing `build-plan` or `brief` branch of `header_agrees` genuinely cannot meet a case in the three supervisor files, you may fix that branch, and you report the change by line and by the case that needed it.
- TASK-047's status readers in `bridge_env.py`: `status_fallback`, `status_workflows`, `status_values` and their helpers.
- The tabular records' headers (TASK-049). `completion-check.py`'s `parse_register`, its register checks and its own `read` for the register, test and code files, and `plan-check.py`'s column-position read of `docs/diagrams/INDEX.md`, all stay as they are.
- The run parameters' header and its lifts (`review_owner_lifts`, `Ceiling above twice:` and the rest): TASK-050.
- `records-migrate.py`: TASK-051.
- The duplicated helpers that `docs/HARDENING.md`'s TASK-047 section names (the `escape_field` copies, and `_safe_exc_type_name` / `_bridge_env_refuse_line`). Do not add another copy of these or of any helper. Each reading you need has one copy, in `bridge_env`.
- **The HARDENING item (recorded for a later increment, not this round).** These patterns are quadratic on a long run of spaces (20,000 characters: 2.45 s, 0.73 s and 0.48 s): `parse_scope` / `split_entry` (`bridge_env.py` about 2483-2540), `STAGE_RX` (325) and `BLOCKING_CLASS_RE` (343-345). It is a denial of service only, and their rule must stay unchanged. Do not rewrite these patterns in this round; the supervisor records the item in `docs/HARDENING.md`.
- Any mutation script. The mutants file and the mutation run are the supervisor's.

## Context
**The design that binds this increment.** In `docs/DESIGN.md`, section "## Change: release B2 (2026-11-04)", read:
- the `docs/BUILD_PLAN.md ...` and `handoff/<ID>[-r<N>].md` rows of the table under "### The records and their headers";
- the paragraph "Three kinds of record, one rule each", items (1) and (2);
- the paragraph "The fallback readers, one copy each", with its enumerated retired readings, of which (5), (6) and (11) are this increment's;
- the paragraph "Header first; fallback; malformed";
- the paragraph "The reader".

Three sentences there decide this round:
- "the one piece of code that reads prose is the one that migrated it and the one that checks it";
- a header that fails its schema is malformed, "never silently falling back";
- "The header is never read past the first `---`...`---` block, and the body is everything after it."

Also read `docs/REQUIREMENTS.md` row R-059, and TASK-048's entry in `docs/BUILD_PLAN.md`: its Scope, Scope notes and Done when. Round 1's brief holds Requirements 1 to 12 and round 2's brief holds its findings B1 to AD-3. Round 2's report is `handoff/TASK-048-r2-report.md`. Its summary claimed "one plan body walker", which the code did not have.

**What exists in `bridge/cursor-bridge/bridge_env.py` at HEAD (round 2's code).**
- TASK-046's reader, unchanged and to be called:
  - `class HeaderError(Exception)`, with `.line` (1-based, in the whole text). Its message reads `line <n>: <what>`.
  - `def read_header(text)` (line 1797) returns `(mapping or None, body)` and raises `HeaderError` on a malformed block. An empty block (`---` then `---`) returns `({}, body)`.
  - `def check_header(kind, header)` returns a list of schema findings, empty when the header is valid. A header with a wrong, missing or empty `record:` gives `['record']`.
  - `def header_agrees(kind, header, fallback)` returns a list of disagreement tokens.
    - For `"brief"`, the fallback dict holds `"name"`, `"satisfies"` (a list), `"scope"` (a list), `"merge_unit"` (a list, a tuple or `None`) and `"blocking_class"` (a string or `None`).
    - For `"build-plan"`, the fallback is `{"merged": set or None, "stages": [{"name", "demonstration", "increments": [{"id", "title", "fields": {...}}]}]}`.
      - `fields` holds only the lines present. `kind`, `parallel`, `parent` and `deferred` are raw line values. `depends_on`, `diagrams`, `scope` and `satisfies` are lists of strings.
      - `_plan_agrees` pairs stages and increments by position.
    - `tests/test_header_reader.py`'s `fallback_brief()`, `plan_header()` and `plan_fallback()` are worked examples.
  - `_line_end_len` (1280-1287) treats `\n` and `\r\n` as line ends, never a bare `\r`.
- Already present and used: `PLAN_ID_PATTERN = r"TASK-\d{3,}[a-z]?"`, `parse_review_name(name)`, `squash_merged_ids(folder, id_rx, git_runner=None, ref="main")` (a set, or `None` when the log cannot be read), `BLOCKING_CLASSES`, `BLOCKING_CLASS_RE`, `MERGE_UNIT_RE`.
- Round 1 and round 2 added, and this round reworks:
  - `HEAD_RX`, `FIELD_RX`, `STAGE_RX` and `DEMO_RX` (320-326), and `_SCOPE_PAREN = "ScopeAgreementError"` (331);
  - `brief_body` (388), `plan_body` (399), `_blocking_class_from_prose(body)` (410), `read_blocking_class_line(text)` (423), `plan_increment_ids(folder)` (459), `merge_unit_line_present(text)` (485), `_merge_unit_from_prose(text)` (497), `_brief_well_formed_header(text)` (514), `_merge_unit_from_header(header)` (527) and `merge_unit_ids(text)` (546);
  - `class ScopeAgreementError(ValueError)` (2479), `split_entry(entry)` (2483), `parse_scope(brief_text)` (2501; returns `(paths, refusal, unread)`, where refusal is `None`, the refused entry for an ellipsis, or `"empty"`), `brief_satisfies(text)` (2543), `plan_r_ids_outside_headers(text)` (2553), `plan_scope_agreement_entries(value)` (2578), `_plan_normalize_field` (2596), `plan_prose_fallback(text, merged=None)` (2633), `brief_prose_fallback(text, brief_name)` (2695), `brief_header_refusal(text, shown_path, keys=None)` (2714), `plan_header_inc_ids(header)` (2737), `plan_collect_satisfies_ids(body)` (2749), `plan_header_refusal(text, shown_path)` (2768), `plan_header_findings(path, text, merged)` (2793), `brief_malformed_brief_line(text, shown_path)` (2824), `brief_enforced_scope_paths(text, brief_name)` (2838) and `brief_scope_enforcement(text, brief_name, shown_path)` (2856).
  - No test outside the builder's own cases calls `brief_body`, `plan_body`, `plan_prose_fallback`, `brief_prose_fallback`, `plan_collect_satisfies_ids`, `plan_header_findings`, `brief_malformed_brief_line`, `brief_enforced_scope_paths`, `brief_scope_enforcement`, `plan_scope_agreement_entries` or `ScopeAgreementError`. You may rework, rename or remove them.

**Public names the tests call. Keep them, with these signatures and results.**
- `bridge_env.brief_header_refusal(text, shown_path, keys=None)` returns a string beginning `header: `, or `None`.
- `bridge_env.read_blocking_class_line(text)` returns `(class, finding, line)` or `None`. It reads prose only (B2). `tests/test_bug040.py` line 98 and `tests/test_loop_text_pace.py` line 123 call it on a lone prose line and must keep their result.
- `bridge_env.merge_unit_ids(text)` returns a tuple or `None`. It reads the header first for a well-formed header, even where the prose has no `Merge unit:` line (`tests/test_header_plan.py::test_r059_merge_unit_ids_reads_the_header_first`).
- `bridge_env.merge_unit_line_present(text)`.
- `bridge_env.plan_increment_ids(folder)`: `set(...)` of its result gives the IDs.
- `bridge_env.plan_header_refusal(text, shown_path)` returns a non-empty string for a refused plan, else `None`.
- `bridge_env.brief_satisfies(text)` and `bridge_env.plan_r_ids_outside_headers(text)`.
- The moved names `parse_scope`, `split_entry`, `HEAD_RX`, `FIELD_RX` and `DEMO_RX` stay in `bridge_env` (`test_r059_the_moved_readers_live_in_bridge_env`).

**Where the programs read today (round 2's code).**
- `plan-check.py`:
  - `read(path)` (72-74): `utf-8-sig`, `errors="replace"`, text mode.
  - The module aliases `HEAD_RX`, `FIELD_RX`, `DEMO_RX` and `STAGE_RX` (64-67).
  - `parse(paths)` (115-146): a stage is a line starting `## `; the stage carries over from the previous file; it keeps an increment before the first `##` heading; it fails a duplicate ID across files; a field dict keeps the last value per key.
  - `stages_without_demonstration(paths)` (149-175): per-file stages by `STAGE_RX`.
  - `brief_findings(path, item)` (190-213): the Scope check, then the R-id check `re.search(rid, text)` over the brief's text at 210-212.
  - `historic_header_ids` (216).
  - `main()` (234):
    - plan headers at 248-256;
    - the historic exemption and its note at 261-270;
    - the shape loop at 276-308, with the parenthesis check at 297-303;
    - the PARENT / DEPENDS loop at 310-326;
    - the brief loop at 412-420.
  - `scope_paths(value)` (81) stays as it is, for readiness, PARALLEL and BRIEF.
- `scope-check.py`: `parse_scope(brief_path)` (93-124) opens the brief with `utf-8-sig` and no `errors=` (95). It calls `bridge_env.brief_scope_enforcement` and keeps the `CANNOT VERIFY:` lines and `UNREAD`.
- `completion-check.py`: plan coverage at 153-196. It calls `plan_header_findings` twice (162, 183), and uses `plan_body` (175) and `plan_collect_satisfies_ids` (178).
- `bridge-run.py`: `builder_review_refusal` (612).
  - It reads the brief's bytes (641), keeps `brief_sha` over them (644), and decodes them with `utf-8`, `errors="replace"` and no newline translation (659).
  - The brief header check is at 660-663. The merge-unit check follows: the plan files at 675-683, `plan_increment_ids` at 684, the SCOPE file at 687-692 and the ID loop at 693-697.
  - The class lift is at 715-743.
- `review-guard.py`:
  - `scope_blocking_line` (665-679) reads the SCOPE files through `read_blocking_class_line`.
  - `snapshot_review_refusal` (682) opens the first brief with `utf-8` and `errors="replace"` (694), then calls `brief_header_refusal(..., keys=("merge_unit", "id", "round"))` (698-702).
  - Its ceiling check is at 747-757.

**The supervisor's tests (fixed points).**
- `tests/test_header_plan_r3.py` (commit 04e91ab) holds this round's reproduction tests, with the rewritten case `test_r059_r2_under_no_git_an_unbalanced_scope_is_a_note` in `tests/test_header_plan_r2.py`.
  - On 7dacef3, `python -m pytest -q tests/test_header_plan_r2.py tests/test_header_plan_r3.py` gave `12 failed, 30 passed in 12.03s`. The twelve are the rewritten case and every round-3 case except `test_r059_r3_the_program_walks_no_plan_itself[completion-check]`, which already passes.
  - Every case of the three supervisor files must pass.
- `tests/test_header_plan.py` (round 1) and the other cases of `tests/test_header_plan_r2.py` (round 2) passed on 7dacef3 (`93 passed`) and must stay green.
- The full suite on 7dacef3 gave `12 failed, 4671 passed, 41 skipped in 1748.92s`; the twelve were exactly the cases above.

**No regression on header-less records.** A header-less plan, register or brief is read exactly as before by every program. The supervisor compares 4bdac19's programs with round 3's on copies of this repository's records, with and without a readable merged set:
- `completion-check --mode plan` must be identical.
- `scope-check` over the briefs must be identical.
- `plan-check --no-git` (no merged set) may differ only by `note:` lines.
- `plan-check` with a readable merged set may differ only by a parenthesis `SHAPE:` line for an unmerged increment.

On round 2, the `--no-git` comparison differed by fifteen parenthesis `SHAPE:` lines (`RESULT: 6 problem(s)` became `RESULT: 21 problem(s)`). R3-6 below removes that difference. plan-check's existing header-less behaviours stay: `parse` keeps an increment before the first `##` heading, the duplicate-ID check runs across files, and `stages_without_demonstration` works on per-file stages.

**Security context.** The project's ASVS level is 2 (INVENTORY, Decisions; D-004). The trust boundary: the plan and the briefs are text the supervisor writes, but a builder or a reviewer can write them too, so the header reader's refusals stand.
- A gate program (the launcher, the guard) refuses rather than guess between two readings. It never launches a builder on a brief whose Scope reading differs from what the other programs read. It never accepts a Merge-unit ID that the plan header does not declare. It never lifts a review ceiling on a class with no finding line. It never snapshots on a first brief it cannot read, or whose `merge_unit`, `id` or `round` disagrees.
- The reader executes nothing.
- No exception is swallowed. A `HeaderError` or an `OSError` becomes the stated refusal or finding, never a skip and never a whole-text fallback.
- Output stays ASCII as today, apart from what a program already quotes from a record.
- `.cursor/rules/secure-coding.mdc` is in force for you.

**Development data** (the inventory's `Development data` decision). The development build is the Workspace sources under `bridge/`. A session in this repository always runs the installed bridge, never the one being edited, and no record of this repository carries a header before TASK-054. For you, this means:
- Never run a program of this increment over this repository's own `docs/BUILD_PLAN*.md` files, its briefs under `handoff/`, or any other record. The supervisor runs the header-less regression check above.
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

A solid edge is a plain `import bridge_env` statement, which `check:components` sees. All five programs have it, each after `sys.path.insert(0, HERE)`, so the import also works when `tools/dump-cli.py` loads `completion-check.py` and `plan-check.py` by file (the dotted edges). No program may gain any other import or load by file. If the task cannot be done within the diagram, stop and report the conflict instead of deviating.

## Requirements
Each finding gives its evidence, the fix, and the cases that pin it. Pinning cases are `tests/test_header_plan_r3.py::<name>` unless another file is named; a bracketed list gives the parametrized ids. Use these labels in your report.

1. **S-1. One brief reading (the root cause, brief side).** Build the one brief reading the Objective describes, and route every brief reader through it.
   - **Its result.** The header or `None`, the body, the refusal or `None`, the prose fallback built from the body, and the agreement tokens.
   - **Refused header.** A `HeaderError` or any `check_header("brief", ...)` finding, `record` included, is the refusal `header: <path>:<line> <what>`. Here `<line>` is the `HeaderError`'s line, or `1` for a schema finding.
   - **No re-parsing.** The fallback is built from the body only, and never re-parses a header found inside the body.
   - **No other reading.** After this round, `read_header` is called for a brief in that one function only. No brief reader falls back to the whole text.
   - **Readers on a refused header.** On a refused header, `read_blocking_class_line` returns `None`, `merge_unit_ids` returns `None`, `merge_unit_line_present` returns `False`, and `brief_satisfies` returns the empty list. The gates refuse a refused header first, as now.
   - **Header-less brief.** For a brief with no header, the body is the whole text, and every reader gives exactly round 2's answer (which is round 0's).
2. **S-2. One plan walker (the root cause, plan side).** Build the one plan walker the Objective describes.
   - **What it returns.** Per file, it returns the stages, each with its name, its `Demonstration:` lines and its increments. Each increment comes with its ID, its title and its field lines. It also returns the increments that stand outside any stage, with the same detail.
   - **Who consumes it.**
     - `plan-check.py`'s `parse` and `stages_without_demonstration`;
     - the agreement fallback that `header_agrees("build-plan", ...)` is given;
     - `completion-check.py`'s header-less planned set;
     - `plan_increment_ids`.

     Each takes what it needs, and none walks the lines itself.
   - **Header-less files.** For a header-less file, each consumer's answer stays exactly round 2's. That includes the case where an increment repeats a field line: `parse` keeps the last value per key, while completion-check's planned set takes the R-ids of every `Satisfies:` line of the increment.
   - **Body only.** The walker reads only the body of a well-formed header, or the whole text of a header-less file. A malformed plan header is refused by the caller first: plan-check and completion-check print `HEADER MALFORMED:` and exit 2, and the launcher refuses. No plan function falls back to the whole text on a malformed header. Today three do: `plan_increment_ids` 474-477, `plan_r_ids_outside_headers` 2556-2559, and `plan_prose_fallback` 2635-2638.
   - **The patterns stay in `bridge_env`.** `plan-check.py` and `completion-check.py` use none of `HEAD_RX`, `FIELD_RX`, `DEMO_RX` or `STAGE_RX`. Remove `plan-check.py`'s module aliases at 64-67.
   - Pinned by: `test_r059_r3_the_program_walks_no_plan_itself` [plan-check, completion-check] and `tests/test_header_plan_r2.py::test_r059_r2_completion_check_walks_no_plan_of_its_own`.
3. **R3-1 (audit, blocking: behaviour against the brief, security). plan-check's brief comparison is inverted.**
   - **Evidence.** `bridge_env.py` 2848 (`brief_enforced_scope_paths`) and `plan-check.py` 200-202. `header_agrees` returns the list of disagreements, so `if header_agrees(...)` parses the body Scope only when the header disagrees. When the header agrees, the function returns `None` and `brief_findings` returns `[]`. So the BRIEF check (a Scope path outside the increment's Scope) and the Satisfies coverage check (an R-id of the increment that the brief does not name) do nothing for any brief with an agreeing header. After TASK-054's migration, that is every brief.
   - **Reproduction.** The plan's Scope is `src/a.py`, and the brief's Scope is `src/a.py` and `src/evil/**`. Header-less, plan-check gives the BRIEF line and exit 1. With an agreeing header, it gives `RESULT: OK` and exit 0.
   - **Required.** For a brief with a well-formed header, plan-check compares exactly what it compares for the same brief without a header:
     - **Scope:** the body's Scope from the one brief reading, which equals the header's `scope` where they agree.
     - **R-ids:** the search runs over the body. For a header-less brief the body is the whole text, so its answer is unchanged.
     - **Disagreeing header:** it stays scope-check's finding and the launcher's refusal (round 2's ruling). plan-check adds no line for it, and still compares the body's Scope and body, never nothing.
     - **Malformed header:** it stays a `BRIEF: <brief path> header: ...` finding (RA-8).
   - Pinned by: `test_r059_r3_plan_check_compares_a_brief_with_an_agreeing_header` [scope-outside, satisfies-unnamed].
4. **R3-2 (audit and Review A, blocking: behaviour against the brief; RA-9 not fixed at its mechanism). The plan readings diverge.**
   - **Evidence.** The readings count increment headings differently:
     - `plan_prose_fallback` (`bridge_env.py` 2633, 2658) counts a `### TASK-` heading only under a `##` stage, and starts each file with no stage.
     - `plan_increment_ids` (459-482) and plan-check's `parse` (`plan-check.py` 115-146) count every heading, and `parse` carries the stage over from the previous file.
   - **Reproduction.** A headed plan whose header declares the stages' increments has `### TASK-009 - orphan` / `Scope: src/z.py` before its first `##` heading. `plan_header_refusal` returns `None`, `plan_increment_ids` includes TASK-009, and plan-check prints `READY: TASK-009` and `RESULT: OK`. Round 1's fixed line says that a heading with no header entry is a failure naming the ID.
   - **Required, with one walker (S-2), in a file with a header.** An increment heading outside any stage:
     - is a failure naming the ID in plan-check (a `SHAPE:` or `HEADER DISAGREES:` line containing it), with exit 1;
     - is never listed `READY:`;
     - makes `plan_header_refusal` refuse, so that the launcher never accepts that ID in a Merge unit.
   - **Required in a file with no header.** Every program's answer stays exactly as today: `parse` keeps an increment before the first `##` heading, the duplicate-ID check runs across files, and `stages_without_demonstration` works on per-file stages.
   - Pinned by: `test_r059_r3_a_heading_outside_any_stage_of_a_headed_plan_is_a_failure`, `test_r059_r3_the_launchers_plan_reading_refuses_a_heading_outside_any_stage`, `test_r059_r3_the_launcher_accepts_no_merge_unit_id_outside_any_stage`, and `test_r059_r3_the_program_walks_no_plan_itself` [plan-check, completion-check]. `tests/test_header_plan.py::test_r059_the_launcher_sees_an_addendums_increments` (a header-less addendum whose increment stands under no `##` stage) stays green.
5. **R3-3 (Review A, blocking: behaviour against the brief; a false result on a realistic layout). A merged increment whose `Scope:` line carries an unbalanced parenthesis can never agree with a header.**
   - **Evidence.** `bridge_env.py` 2686-2689 stores the string `"ScopeAgreementError"` (`_SCOPE_PAREN`, line 331) for such a line, and `_plan_agrees` compares it with the header's list. So every header value gives `HEADER DISAGREES: <id> scope`, while the header-less plan gives no failure.
   - **Impact.** This repository's plan has fifteen merged increments with such a line (TASK-010, 012-014, 016, 017, 030, 032, 036-038 and 040-043). All of them would fail once headed at TASK-054.
   - **The supervisor's ruling.** The agreement fallback reads a `Scope:` line as it reads any other: split on `;`, each entry stripped, a folder's trailing `/` kept, and no parenthesis refusal. A header can then hold the reading and match it. For example, `Scope: src/parse.py (the reader; its tests)` reads as `["src/parse.py (the reader", "its tests)"]`, and records-migrate will write that same reading. The unbalanced parenthesis is plan-check's shape rule alone (R3-6).
   - **What this overrides.** Round 1's Requirement 5, third bullet ("That fallback refuses an entry with an unbalanced parenthesis"), and round 2's RA-2 sentence leaving the `scope` comparison open.
   - **What stays.** The `scope-folder-slash` case still holds (`src/out/` in the prose against `src/out` in the header disagrees).
   - Pinned by: `test_r059_r3_a_merged_unbalanced_scope_can_agree_with_its_header`. `tests/test_header_plan_r2.py::test_r059_r2_a_headed_plan_with_an_unbalanced_unmerged_scope_gets_the_shape_line` and `::test_r059_r2_a_headed_plan_with_an_unbalanced_merged_scope_is_read_as_today` stay green.
6. **R3-4 (audit, security: two readings at a gate). The launcher reads a brief's lines differently from the others.**
   - **Evidence.** The launcher decodes the brief's raw bytes (`bridge-run.py` 659) and keeps a bare carriage return. scope-check (95), review-guard (694) and plan-check (73) open in text mode, which turns a bare carriage return into a line end. `bridge_env`'s `_line_end_len` (1280-1287) does not treat a bare carriage return as a line end. As a result, a brief with bare carriage returns and a disagreeing `scope` gets no refusal from the launcher, which launches the builder; scope-check and the guard refuse it later.
   - **Required.** Every program reads a brief's and a plan's text the same way: one `bridge_env` function, used by all five for every brief and plan file they read, so that the launcher refuses exactly what the others refuse.
     - It decodes UTF-8, drops a leading BOM, replaces an undecodable byte (`errors="replace"`, as plan-check's and completion-check's `read` and the launcher do today), and gives universal newlines (`\r\n` and a bare `\r` each become a line end).
     - The launcher keeps its `brief_sha256` over the raw bytes, as today.
     - An `OSError` stays each program's existing refusal or line: scope-check's `CANNOT VERIFY: brief not readable: ...`, the launcher's `brief rule: ... cannot be read`, and the guard's `review-guard: refused - cannot read handoff/<id>.md`.
     - The SCOPE files are not records of this kind (R3-T1).
   - Pinned by: `test_r059_r3_the_launcher_refuses_a_disagreeing_brief_with_bare_carriage_returns`.
7. **R3-5 (audit and Review A; round 2's "no exception swallowed"). Two silent paths remain.**
   - **(a) The launcher skips a plan file it cannot read.** `bridge-run.py` 676-679 and `plan_increment_ids` (`bridge_env.py` 470-473) `continue` on `OSError`. Required: a plan file that the merge-unit check cannot read is a refusal naming it, exit 125, with a line beginning `bridge-run: refused - ` that contains the file's name (for example `BUILD_PLAN-2026-11-04.md`). This covers any path the `docs/BUILD_PLAN*.md` glob matches that cannot be opened as a file, a directory among them. No caller of `plan_increment_ids` silently skips a file. How the refusal reaches the launcher is yours.
   - **(b) The brief readers fall back to the whole text on a malformed header.** `brief_body`, and `_brief_well_formed_header` for `merge_unit_line_present` and `merge_unit_ids`, do this. So `read_blocking_class_line` returns a class from a `Blocking class:` line inside a malformed header block, and `merge_unit_ids` returns a unit from inside it. Required: on a malformed header, the brief readers read nothing (S-1).
   - Pinned by: `test_r059_r3_the_launcher_refuses_a_plan_file_it_cannot_read`, `test_r059_r3_no_class_is_read_from_inside_a_malformed_header`, `test_r059_r3_no_merge_unit_is_read_from_inside_a_malformed_header`.
8. **R3-6 (Review A 7; the supervisor's ruling revised; this reverses round 2's RA-7 ruling, and says so). The parenthesis rule with no merged set.**
   - **What round 2 did.** It implemented the round-2 ruling: under `--no-git` or an unreadable log nothing counts as merged, so an unbalanced parenthesis is a SHAPE failure for every increment. Review A's comparison showed that this fails fifteen merged increments of this repository's plan history under `--no-git` or an unreadable `--base` (`RESULT: 6 problem(s)` becomes `RESULT: 21 problem(s)`).
   - **Revised, with no merged set (`merged_set is None`).** An unbalanced parenthesis is a `note:` line naming the increments, never a failure and never silence. Suggested: `note: unbalanced parenthesis in Scope not checked against a merged set: TASK-003`. The note names every increment that has such a `Scope:` line and is not historic-exempt.
   - **Revised, with a merged set.** It stays a `SHAPE: <id> has an unbalanced parenthesis in its Scope` failure for an unmerged increment, and nothing for a merged one.
   - **What an unbalanced entry is.** As today: an entry of the `Scope:` line split on `;` whose counts of `(` and `)` differ.
   - **Where the rule lives.** The rule is plan-check's alone. It no longer comes from the agreement fallback (R3-3). It is one copy, and it is no mirror of the fallback.
   - Pinned by: `tests/test_header_plan_r2.py::test_r059_r2_under_no_git_an_unbalanced_scope_is_a_note` (rewritten by the supervisor), with `tests/test_header_plan.py::test_r059_an_unbalanced_parenthesis_in_an_unmerged_scope_is_a_shape_failure` and the two r2 parenthesis cases above.
9. **R3-T1 (fix in this round too: the same cause). The SCOPE files are read through the brief readers.**
   - **Evidence.** The SCOPE files (`run/review/SCOPE-<id>.md`) carry no header and are read as today (round 1's Requirement 9). Today two paths break that:
     - `review-guard.py` 676 now passes them through `read_blocking_class_line`, and so through `brief_body`, which would drop a leading `---` block.
     - `merge_unit_ids` on a SCOPE file with a wrong-kind header falls back to the whole text (`bridge-run.py` 690; `bridge_env.py` 514-524).
   - **Required.** Read the SCOPE files' lines as before (4bdac19), opened as today, with no header handling: their `Blocking class:` line and their `Merge unit:` line are read from the whole text by the prose readers.
10. **R3-T2 (fix in this round too). Docstrings and dead code that no longer match.**
    - `plan_increment_ids`' "header first when well-formed" (`bridge_env.py` 460);
    - `brief_scope_enforcement`'s mention of `brief_scope_enforcement_status`, which does not exist (2857);
    - `plan_body`'s `except HeaderError: raise`, which does nothing (399-407).

    Required: no docstring or comment in your diff describes behaviour that the code lacks, and no no-op handler is left. Where a function goes away with S-1 or S-2, its docstring goes with it.
11. **Ruled: no change (as designed). Do not change these.**
    - **Header first for `satisfied`.** completion-check takes `satisfied` from the plan header alone when header and prose disagree. For example, header `satisfies` [R-001, R-002] with prose R-001 gives completion-check `RESULT: OK`. R-059 gives completion-check one agreement rule: every R-id on a `Satisfies:` line in a headed plan's body stands in some header `satisfies`. plan-check owns the field-by-field agreement, and fails this plan with `HEADER DISAGREES: <id> satisfies`.
    - **A missing first brief.** The guard passes a missing first brief: where `handoff/<id>.md` is absent or has no header, the guard behaves as today (round 1's Requirement 10).
    - **The historic mark under `--no-git`.** It exempts an increment with only a note (round 1's Requirement 4).
    - **A bold `**Satisfies**:` line.** For a header-less plan, completion-check counts an increment's own `Satisfies:` line as `FIELD_RX` reads it, so a bold `**Satisfies**:` line is no field (round 2, Review A advisory 14).
    - **AD-3.** It stays optional and informational: `bridge-run.py`'s merge-unit messages name only `docs/BUILD_PLAN.md`. You may name the plan files read; if you do, every existing test in Done step 3 must stay green.
12. **The earlier rounds' requirements stand.** The full text is in `handoff/TASK-048.md` (Requirements 1 to 12) and `handoff/TASK-048-r2.md` (Requirements 1 to 15). In short, with the fixed lines the tests pin:
    - **The fallback readers live in `bridge_env`, one copy each:** `HEAD_RX`, `FIELD_RX`, `DEMO_RX`, `parse_scope`, `split_entry`, `brief_satisfies` and `plan_r_ids_outside_headers`. The `bridge_env` copies print nothing, never call `sys.exit`, and keep no module-level state. `FIELD_RX` stays linear: it captures with `(.*)$` and the caller strips trailing whitespace (AD-1).
    - **plan-check's own code.** It compiles none of `HEAD_RX`, `FIELD_RX` or `DEMO_RX`, and defines no `brief_scope` or `merged_ids`. It calls `bridge_env.squash_merged_ids(os.getcwd(), bridge_env.PLAN_ID_PATTERN, ref=<--base>)`.
    - **completion-check's own code.** It keeps no `Satisfies` regex, and calls `bridge_env.plan_r_ids_outside_headers`.
    - **plan-check's lines:**
      - `HEADER MALFORMED: <path>:<line> <what>`, exit 2 (`<path>` with forward slashes; `<line>` is the `HeaderError`'s line, or `1` for a schema finding).
      - `HEADER DISAGREES: <id> <field>` or `HEADER DISAGREES: <stage> <field>`, a failure, exit 1.
      - An increment in the header with no heading, a heading with no header entry, or (R3-2) a heading outside any stage of a headed file, is a failure naming the ID.
      - The parenthesis rule is as R3-6 states.
      - A `--base` beginning with `-` exits 2 with one line and no traceback, before any git command.
      - The note `could not read git log of <base> - readiness assumes nothing merged` stays.
      - The historic mark on an unmerged increment is a failure naming it. Under `--no-git`, the mark is accepted with a `note:` line naming the increments not re-checked.
      - The historic exemption covers the shape rules only (RA-6).
      - A malformed brief header is a `BRIEF:` finding (RA-8).
    - **scope-check's lines:**
      - `HEADER MALFORMED: <path>:<line> <what>` and `HEADER DISAGREES: <key>`, each exit 2;
      - `NOT READ AS A PATH: ...`;
      - the `CANNOT VERIFY: ...` lines and `sys.exit(2)` for an unreadable brief, an empty Scope, and an ellipsis (quoting its entry, `entry[:80]`, RA-3);
      - a leading `./` stripped in `bridge_env.parse_scope` (RA-4);
      - `VERDICT: SCOPE CLEAN` (exit 0) or `VERDICT: SCOPE DRIFT` (exit 1).

      scope-check enforces the body's Scope, the same reading the header was compared with (B1).
    - **completion-check's lines:**
      - `HEADER MALFORMED: <path>:<line> <what>`, exit 2;
      - `HEADER DISAGREES: satisfies`, exit 1, where an R-id on any `Satisfies:` line in a headed plan file's body stands in no increment's header `satisfies` across the headed plan files.

      For a file with no header, only an increment's own `Satisfies:` line counts.
    - **The launcher:**
      - It prints `bridge-run: refused - header: <path>:<line> <what>` and `bridge-run: refused - header: disagrees <key>`, exit 125, for every key, before any launch, slot or `runs.jsonl` line.
      - In the merge-unit check, it refuses a malformed plan header, or a plan header whose IDs differ from the body's headings, with `bridge-run: refused - header: ` naming the plan file (AD-2).
      - It refuses a class lift whose line or finding is empty (B2).
    - **The guard:**
      - It prints `review-guard: refused - header: <path>:<line> <what>` and `review-guard: refused - header: disagrees <key>` on the branch's first brief, to stdout as the first line, exit 125. It compares `merge_unit`, `id` and `round` only, through `bridge_env.brief_header_refusal(text, shown_path, keys=("merge_unit", "id", "round"))` or the one brief reading behind it.
      - A first brief that exists but cannot be read as a file is a refusal (RA-8).
      - It refuses a class lift whose line or finding is empty (B2).
    - **The wrong `record:` kind.** It is malformed in all five programs (RA-1). No program tests `header.get("record")`.
    - **No program reads a header itself.** None of the five programs calls `bridge_env.read_header`, `bridge_env.check_header` or `bridge_env.header_agrees` for a brief or a plan itself (round 2's Requirement 14).
    - **Agreeing and absent headers.** An agreeing header gives the same answer as the header-less file in each of the five programs. A header-less record is read exactly as before (see Context).
    - **No retired pattern in prose.** No program's prose quotes a retired pattern (KP-073): no pattern in a docstring, a comment or a help text.
13. **Housekeeping.**
    - Do not edit the module docstring, the argparse help or any option of the five programs. `python tools/dump-cli.py --check` must stay green with the reference unchanged.
    - Regenerate `bridge/cursor-bridge/MANIFEST.json` with `python tools/make-manifest.py` (no `--version`), and quote its output.
    - Add no dependency. `pyyaml` stays test-only, and no program imports it.

## Acceptance criteria
- [ ] `python -m pytest -q tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py` passes whole: every supervisor case above each marker, and your own cases below them.
- [ ] One brief reading (S-1) and one plan walker (S-2) exist in `bridge_env`, and every reader the Objective names consumes them.
  - `read_header` is called for a brief in that one brief reading only.
  - No brief or plan reader falls back to the whole text on a malformed header.
  - `plan-check.py` and `completion-check.py` use none of `HEAD_RX`, `FIELD_RX`, `DEMO_RX` or `STAGE_RX`.
- [ ] Each finding is fixed at the mechanism its evidence names:
  - R3-1: the brief comparison runs for an agreeing header;
  - R3-2: one walker, and a heading outside any stage of a headed file is a failure and a launcher refusal;
  - R3-3: the agreement fallback reads `Scope:` split on `;` with no parenthesis refusal;
  - R3-4: one text reading with universal newlines, in all five programs;
  - R3-5: an unreadable plan file is a refusal, and nothing is read from inside a malformed header;
  - R3-6: a note with no merged set, SHAPE for an unmerged increment with one;
  - R3-T1: the SCOPE files are read as before;
  - R3-T2.
- [ ] The round-1 and round-2 labels stay fixed (B1, B2, RA-1 to RA-9, AD-1, AD-2), and `_plan_field_value` is byte-identical to 4bdac19.
- [ ] The bundles of Done steps 2 to 5 pass. Every existing test in them is green, and no test file outside the Scope is edited.
- [ ] Each fixed line holds as Requirement 12 lists it, with its exit code.
- [ ] A header-less plan, register or brief is read exactly as before, with the only allowed differences those that Context names. The supervisor checks this on this repository's records.
- [ ] `python tools/dump-cli.py --check` is green with `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` unchanged. MANIFEST is regenerated. No option is added, removed or reworded, and no dependency is added.
- [ ] `python bridge/cursor-bridge/diagram-check.py --mode code` gives `RESULT: OK`.
- [ ] R-059 is fully met, with no stand-in or placeholder. Every case you add names R-059 in its name, docstring or a comment. The cases you add for a rule include the negative path (a case that would fail if the rule were broken), not the positive path alone.
- [ ] No new Semgrep high findings. No exception is swallowed. The gate programs refuse rather than fall back on each of these: a malformed or disagreeing brief header, an unreadable first brief, an unreadable plan file, a malformed or disagreeing plan header in the merge-unit check, a Merge-unit ID outside any stage of a headed plan, and an empty class lift (ASVS L2).

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Do not fix by suppressing the symptom: no retry, no broad `try/except`, no widened tolerance, no added `sleep`, no null-check that hides a wrong value. A caught exception becomes the stated finding or refusal line.
- Do not edit the reproduction tests: nothing above the marker line in `tests/test_header_plan.py`, `tests/test_header_plan_r2.py` or `tests/test_header_plan_r3.py` changes. Leave no debug line or stray print.
- If you believe the real cause of a finding is different from the one named here, stop, do not change code for that finding, and report why in your summary. The supervisor will re-diagnose.
- Any console process your code launches on Windows is created windowless. Use the program's existing `NO_WINDOW`. In tests, use `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)`, spelled literally in each call, as `tests/test_header_plan.py`'s `run()` and `git()` do (`tests/test_tests_windowless.py` checks the spelling). Every git call gets a timeout.
- A parametrized test you add takes a plain `ids=` list, as the supervisor's cases do.
- **Run every command in the foreground and wait for it to end.** Start nothing in the background or asynchronously, and leave no process running when you finish. Never start a server, a watcher or a daemon.
- **Do NOT run the full `tests/` tree.** That means no `python -m pytest`, no `python -m pytest tests`, and no other command that collects all of it. An earlier round of this release ran it asynchronously and ran out its two-hour limit (ISS-030). The supervisor runs the full suite. Run only the commands the Done section lists.
- **Run the Done commands exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change.**
- When an increment starts a process, your tests start the programs and git as children through `subprocess.run`, with output captured and a timeout. Each child is windowless and ends before the test does, and nothing outlives the test.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. Run the programs only on fixtures under `tmp_path`, never on this repository's plan, briefs or records (see Development data in Context).
- No value in this brief is marked as the owner's.
- Follow the existing conventions in the files you touch:
  - ASCII output;
  - the `SHAPE:` / `BRIEF:` / `note:` / `RESULT:` lines of `plan-check.py`;
  - the `CANNOT VERIFY:` lines of `scope-check.py`;
  - the `bridge-run: refused - ` and `review-guard: refused - ` prefixes.

  The five programs' fixed lines and exit codes stay as Requirement 12 lists them.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- Numbers from text are parsed with the language's own parser, never by slicing a string. A brief's `round` is the header's integer, compared with `parse_review_name`'s integer. A header line number comes from `HeaderError.line` (an int, 1-based) or is the literal `1`.
- Every verification command is written in full in the Done section; run exactly those, from the Workspace root. The supervisor checks this increment's tests by mutation in its own run, with its own mutants file. You may mutate by hand, in-process, in your own run to test your cases. If you do, list each mutation and what caught it. No mutation script lands in the diff.
- No failure is known in the files the Done section runs, apart from the twelve red cases this round is to turn green: the rewritten case in `tests/test_header_plan_r2.py` and eleven cases of `tests/test_header_plan_r3.py`. If another test there fails and this change did not cause it, report it by its test id and fix none.
- Prefer reuse over new code. Call `header_agrees` rather than writing a second comparison, keep one copy of each reading, and write the minimum that meets the acceptance criteria. This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-048-r3-report.md`. Write it as you go, so that nothing of it is lost if your run ends early. It records what you did, what you changed, what you ran and what it printed, and what you could not do. Every claim in it must be accurate: round 2's summary claimed "one plan body walker" that the code did not have. Claim only what the diff shows.

When you finish, the report holds:
- **Files changed.** A list of every file you changed, the report itself (`handoff/TASK-048-r3-report.md`) among them.
- **Summary.** A one-paragraph summary of what you did.
- **The structure.** The name of the one brief reading function and the name of the one plan walker, each with every call site that consumes it (file and function), and the name of the one text-reading function, with its callers in the five programs.
- **The findings.** For each label (S-1, S-2, R3-1 to R3-6, R3-T1, R3-T2), one sentence on how the change closes it at its mechanism.
- **TASK-046 and TASK-047 code.** Every change to TASK-046's or TASK-047's code in `bridge_env.py`, by line, compared with 4bdac19, with the case that needed it, or "none" (expected: none).
- **Existing tests.** Any existing test you found that pins a retired reading, by test id, or "none".
- **Manifest.** The manifest command you ran and its output.
- **Assumed, not verified.** A section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. That covers an ambiguous requirement you resolved one way, a platform or library behaviour you expected, or a value or a wording you chose. Examples: how `plan_increment_ids` reports an unreadable file to the launcher, or the wording of the R3-6 note and of the R3-2 failure line. Write one item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item. Make it accurate. State as assumed only what you did not check, and check what you can: round 1's wrong assumption about `read_blocking_class_line` is how B2 shipped.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change:
1. `python -m pytest -q tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py`
2. `python -m pytest -q tests/test_plan_check.py tests/test_plan_demonstration.py tests/test_scope_check.py tests/test_completion_check.py tests/test_a4_review_fixes.py tests/test_a4_followups.py tests/test_a5_followups.py`
3. `python -m pytest -q tests/test_bridge_run.py tests/test_bridge_run_review_ceiling.py tests/test_bridge_run_design_ceiling.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_r4.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_hotfix25a_roster_launcher.py`
4. `python -m pytest -q tests/test_review_guard.py tests/test_review_guard_ceiling.py tests/test_review_guard_a4.py tests/test_task032_supervisor_guard.py tests/test_d003_review_round_states.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_bug036.py tests/test_bug038.py tests/test_bug039.py tests/test_bug041.py tests/test_bug042.py tests/test_bug043.py`
5. `python -m pytest -q tests/test_header_reader.py tests/test_header_schemas.py tests/test_header_status.py tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_mutation_run.py`
6. `python tools/dump-cli.py --check`
7. `python tools/make-manifest.py`
8. `python bridge/cursor-bridge/diagram-check.py --mode code`. This is the Workspace copy, and it is read-only.
9. `git rev-parse HEAD` and `git status --short`

Quote every command you ran in the report, with the lines it printed, verbatim, in a fenced block.
- Quote each pytest summary line verbatim in a fenced block, and never restate a count in prose.
- A claim that a check passed quotes the output line that shows it.
- A number of failing or skipped cases is backed by the pytest lines naming them.
- A command you did not run is written `not run`, never described as run.

Write the report's results after step 9. The counts belong to the state that step 9 names: the commit `git rev-parse HEAD` prints, plus the uncommitted changes `git status --short` lists. Quote both outputs and say so in those words. If you edit any file after step 9, run steps 1 to 9 again.

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
