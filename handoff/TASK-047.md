---
record: brief
header: 1
id: TASK-047
round: 1
satisfies: [R-058]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/loop-guard.py", "bridge/cursor-bridge/session-start.py", "bridge/cursor-bridge/conformance-check.py", "bridge/cursor-bridge/workflow-check.py", "bridge/cursor-bridge/inventory-check.py", "bridge/cursor-bridge/evaluate-reports.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_header_status.py", "tests/test_loop_guard.py", "tests/test_session_start.py", "tests/test_session_start_module.py", "tests/test_conformance_check.py", "tests/test_workflows_line_check.py", "tests/test_workflow_check.py", "tests/test_evaluate_reports.py", "docs/BUILDER_NOTES.md", "handoff/TASK-047-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-047: The status file's header in its six readers

## Objective
Release B2 gives `docs/PROJECT_STATUS.md` a YAML front-matter header (`record: project-status`) holding six typed values: `phase`, `workflows`, `awaiting_user_on`, `bridge_version`, `stage`, `open_issues`. TASK-046 (merged, PR #137) built the header reader, the schemas and the agreement helper in `bridge/cursor-bridge/bridge_env.py`. This increment makes the six programs that read the status file (`loop-guard.py`, `session-start.py`, `conformance-check.py`, `workflow-check.py --status`, `inventory-check.py`, `evaluate-reports.py`) read the header first through `bridge_env`. Where the file has no header, they fall back to one prose reading per field, moved into `bridge_env` from the program that holds it today and unchanged in rule. The four retired second readings, (1) to (4) of the design's list, disappear. Each program reacts to a malformed or disagreeing header in the way the design states. The aim is that each status field has one home, one reader and one type, so two programs can never read the same line two ways.

Satisfies: R-058 - The status file's header (`phase`, `workflows`, `awaiting_user_on`, `bridge_version`, `stage`, `open_issues`, typed as the design's table states them) is read first by every program that reads the file. Each falls back to the one reading `bridge_env` keeps for a file with no header, and the retired second readings are gone. The hooks fall back on a malformed header and print `header malformed: <path>:<line>` and `header disagrees: <key>`, and the loop guard refuses the stop on a disagreeing `phase` or `awaiting_user_on`. The checkers print `HEADER MALFORMED: <path>:<line> <what>` and exit 2. `inventory-check.py` compares every key and fails `HEADER DISAGREES: <key>`, and its caps count the body after the header, with its help text saying so and the command reference regenerated.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/loop-guard.py
- bridge/cursor-bridge/session-start.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/workflow-check.py
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/evaluate-reports.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_header_status.py
- tests/test_loop_guard.py
- tests/test_session_start.py
- tests/test_session_start_module.py
- tests/test_conformance_check.py
- tests/test_workflows_line_check.py
- tests/test_workflow_check.py
- tests/test_evaluate_reports.py
- docs/BUILDER_NOTES.md
- handoff/TASK-047-r1-report.md

Limits on the test files:
- `tests/test_header_status.py` is the supervisor's. You add your own cases only below its last line, `# --- THE BUILDER'S CASES GO BELOW THIS LINE; NOTHING ABOVE IT IS EDITED ---`, and you edit nothing above that line.
- In the other test files listed above, you may only add cases, or correct a test that pinned one of the retired readings (1) to (4). Name each such corrected test in your report.
- `tests/test_evaluate_reports.py`: the supervisor searched it, and no existing test there pins a retired reading. Rewrite nothing in it; add your header-path cases beside the existing tests.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ (PROJECT_STATUS.md, INVENTORY.md, REQUIREMENTS.md, BUILD_PLAN.md, DESIGN.md, the diagrams) is the supervisor's.
- The other records' headers: the plan, the briefs, the inventory, the register, the index, the deviations file and the run parameters (TASK-048 to TASK-050).
- `records-migrate.py` (TASK-051).
- Retired readings (5) to (11) of the design's list. Reading (7), `conformance-check.py`'s heading-word guess of the inventory's sections, stays as it is (TASK-049).
- Any edit of `read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS` or the reader's private helpers in `bridge_env.py`. You add new functions beside them and call them.
- The loop guard's run-parameters comparisons (`agent_ceiling`, `ceiling_above_twice`) and its `Ceiling above twice:` regex (TASK-049/TASK-050).
- `docs/HARDENING.md`'s TASK-046 leads that concern the reader itself (format characters in quoted strings, Requirement 12's dead code, the three quote walkers) and its advisory A1. These belong to later increments.
- Any mutation script. The mutants file and the mutation run are the supervisor's (`run/supervisor/TASK-047-mutants.json`).

## Context
**The design that binds this increment.** `docs/DESIGN.md`, section "## Change: release B2 (2026-11-04)":
- the `docs/PROJECT_STATUS.md` row of "The records and their headers" table: the six keys, their types, and which program reads which key;
- "The fallback readers, one copy each", with the enumerated retired readings (1) to (4);
- "Header first; fallback; malformed";
- the D-002 bullet under "Architecture - the diagrams the change touches", on `session_start`'s import.

Also read `docs/REQUIREMENTS.md` row R-058, and the `docs/INVENTORY.md` Decisions rows "The session-start hook's threat model", "The header policy", "A malformed header ..." and "The status file's caps".

**What exists in `bridge/cursor-bridge/bridge_env.py` (TASK-046). Call these; do not edit them.**
- `class HeaderError(Exception)`, with `.line` (1-based line in the whole text). Its message reads `line <n>: <what>`.
- `def read_header(text)` returns `(mapping or None, body)` and raises `HeaderError` on a malformed block. The block is located by the private `_find_block(text)`, which returns `(block, body, base_line)` or `(None, whole, None)`. For an unterminated block it raises `HeaderError` at line 1.
- `def check_header(kind, header)` returns a list of schema findings, empty when valid.
- `def header_agrees(kind, header, fallback)`. For `"project-status"` it returns the disagreeing keys from `phase`, `bridge_version`, `stage`, `open_issues`, `workflows` and `awaiting_user_on`, comparing `header` with the `fallback` dict.
- `HEADER_SCHEMAS["project-status"]` holds `record`, `header`, `phase` (an enumeration of the eleven phases), `workflows` (list of `WorkflowPart {type, subtype, traits}`), `awaiting_user_on`, `bridge_version`, `stage` and `open_issues`.
- `_no_wait(prose)` and `_normalize_wait(prose)` already hold the loop guard's no-wait rule: the value stripped of `<` and `>`, in any case, is one of `nothing`, `none`, `-` or empty, or starts with `nothing`, `none` or `n/a`.

**Where each prose reading lives today. Each one moves into bridge_env and stays the same in rule.**
- `loop-guard.py` `def field(text, name)` (line 167), and `session-start.py` `def field(text, name)` (line 155), use the same pattern: `r"^\s*(?:[-*]\s+)?[*_`]*%s[*_`]*\s*:[*_`]*\s*(.*?)\s*$"` with `re.M | re.I`. The value is then `.strip().strip("*_`").strip()`.
- `loop-guard.py` `def names_a_wait(value)` (line 242) and `NOTHING = ("nothing", "none", "-", "")` form the no-wait rule.
- `session-start.py` `pointers_part` (line 506) reads the stamp with `re.search(r"[0-9]{4}\.[0-9]{2}\.[0-9]{2}[a-z]?", field(status, "Bridge version") or "")`. This is the one stamp reading.
- `workflow-check.py`: `def prefix_of(rest, multi)` (line 578), `def check_head` (603), `def check_traits` (644), `def check_status(path, text, tables)` (674), `def check_placement(path, text)` (703). `check_status`'s refusal wordings are `"Workflows line breaks the part-prefix rule"`, `"two Workflows lines name the same part"`, `"Workflows line must contain '; traits: ' exactly once"` and, from `check_head`, `"empty name in the Workflows head"`.
- `conformance-check.py` `def status_field(ws, name)` (line 624) uses the pattern `r"^[\s*_-]*%s[*_]*\s*:[*_\s`]*([^`\n]+)"` with `re.M | re.I`, and the value is stripped. After this increment it stays only as the `Stage` reading.
- `evaluate-reports.py`: `def status_segments(value)` (line 269), and `status_entries` (line 288) with its line pattern `r"^\s*(?:[-*]\s+)?[*_`]*Open issues[*_`]*\s*:[*_`]*\s*(.*)$"` (`re.M | re.I`). It writes the report line `"%s status: %d incident(s) named on the Open issues: line as still to write"` from `collect_entries` (line 346).

**The retired readings this increment removes as uses.** These are the design's enumerated list, (1) to (4):
1. `session-start.py`'s forgiving `Workflows:` parse: `parse_workflows_tail` and `workflows_lines_parsed`.
2. `session-start.py`'s equality of the `Awaiting user on:` value with its four exact values (`waiting = awaiting.lower() not in ("nothing", "none", "", "-")`).
3. `conformance-check.py`'s `Bridge version:` regex: the `([0-9.]+[a-z]?)` search at about line 1303.
4. `conformance-check.py`'s `status_field(ws, "Phase")`: the `project.json` comparison at about line 1070, and the grades' `line.startswith("Phase: ")` in `calibration_workflows_grades` at about line 747.

**How the programs import bridge_env today.**
- `plan-check.py` uses `sys.path.insert(0, HERE)` and then `import bridge_env`. This is the plain-import form, and `check:components` sees it.
- `conformance-check.py` loads `bridge_env` by file in `_load_bridge_env()` (line 97). It keeps doing so; that is D-002's dotted edge.
- `session-start.py` loads `workflow-check.py` in `load_checker_module()` (line 198). It loads by `importlib.util.spec_from_file_location` with `sys.dont_write_bytecode = True`, with stdout and stderr redirected to a sink, and it catches `BaseException`. On failure it returns the plain line `"%s: cannot be loaded (%s)" % (CHECKER_SHOWN, safe_exc_type_name(err))`.
- The hook makes no link check of the checker file itself. Its link checks (`wc.is_link`) are on the workflow folder and the tables.

**Security context.** ASVS level 2 (INVENTORY, Decisions; D-004). The relevant trust boundary is the session-start hook's threat model (INVENTORY, Decisions): a partial, mismatched or hand-edited install, not a hostile module. Nothing an in-process module returns reaches the hook's output except as an exact `str` the hook checks. This increment revises that model, without widening it, by a second installed module read the same way. The status file is text the supervisor writes; the reader executes nothing. `.cursor/rules/secure-coding.mdc` is in force for you.

**Development data:** the dev build is the Workspace sources under `bridge/`. A session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet. For you, this means:
- Every test runs on fixtures and temporary copies. The four projects' status fixtures are `tests/fixtures/workflows/{bridge,tdp,reangle,video-factory}.status.md`; they stay header-less and are not edited.
- Never run a program of this increment over this repository's own `docs/PROJECT_STATUS.md` or another project's records.

**The supervisor's acceptance tests (fixed points; red on the checkpoint).** `tests/test_header_status.py` names R-058 and D-002, and is committed before this brief. It is run by `python -m pytest -q tests/test_header_status.py` from the Workspace root.

Its module docstring pins these fixed forms, repeated here exactly:
- `bridge_env.status_fallback(text)` returns a dict of exactly the six keys (phase, workflows, awaiting_user_on, bridge_version, stage, open_issues), each read from the prose by its one copy:
  - phase: the first word of the `Phase:` value (the hooks' field() regex), in lower case;
  - awaiting_user_on: "" for no wait (the loop guard's rule), else the value;
  - bridge_version: the first YYYY.MM.DD stamp with an optional letter in the value, else "";
  - workflows: the parts status_workflows reads;
  - stage: the `Stage:` value (conformance-check's status_field regex);
  - open_issues: the segments of the `Open issues:` value (evaluate-reports' status_segments).

  An absent line gives "" or [].
- `bridge_env.status_workflows(text)` returns (parts, problems). parts is a list of {"type", "subtype", "traits"} in line order; a `not yet classified` line gives none. problems is a list of strings, one per line the strict grammar refuses, worded as workflow-check's check_status words it, never a silent none.
- `bridge_env.status_values(text)` returns (values, malformed, disagrees):
  - values: the header's six keys where the text has a well-formed header (read_header raises nothing and check_header finds nothing), else status_fallback(text);
  - malformed: None, or (line, what), where line is a HeaderError's line, or 1 for a schema fault;
  - disagrees: the keys header_agrees names against status_fallback(text), else [].
- The hooks print `header malformed: <path>:<line>`, `header disagrees: <key>` and `workflows line refused: <reason>`. The checkers print `HEADER MALFORMED: <path>:<line> <what>` and exit 2. inventory-check prints `HEADER DISAGREES: <key>`.

**Host.** `claude --version` is not on PATH in the supervisor's session, so this brief records no Claude Code version tested on. The design's Version section records 2.1.317, read on 2026-11-04 from the session transcript. Nothing in this increment depends on a host fact.

## Diagrams
`docs/diagrams/D-002-components.md` covers the elements `bridge_env`, `loop_guard`, `session_start`, `conformance_check`, `workflow_check`, `inventory_check` and `evaluate_reports`. These are the edges that matter:

```mermaid
    inventory_check --> bridge_env
    workflow_check --> bridge_env
    loop_guard --> bridge_env
    session_start --> bridge_env
    evaluate_reports --> bridge_env
    conformance_check -.-> bridge_env
    conformance_check -.-> workflow_check
    inventory_check -.-> workflow_check
    session_start -.-> workflow_check
```

The diagram's notes fix three things:
- A solid edge is "an `import bridge_env` statement, which `check:components` sees". The five programs `loop_guard`, `session_start`, `workflow_check`, `inventory_check` and `evaluate_reports` therefore each gain a plain `import bridge_env` statement.
- `conformance_check` keeps its load by file and gains no plain import.
- `session_start` imports `bridge_env` "from its own installed folder, `~/.claude/cursor-bridge/`, through no link, after the same path checks it makes for `workflow-check.py`, and keeps its one plain line on any failure".

No program may gain an import or a `spec_from_file_location` load the diagram does not draw. If the task cannot be done within the diagram, stop and report the conflict instead of deviating.

## Requirements
1. **`bridge_env.status_fallback(text)`** returns a dict of exactly the six keys:
   - `phase`: the first word of the `Phase:` value as the hooks' `field()` regex reads it, in lower case; `""` when absent.
   - `awaiting_user_on`: `""` where the no-wait rule holds (`_no_wait`/`_normalize_wait`: stripped of `<` and `>`, in any case, `nothing`, `none`, `n/a`, a dash or empty, or starting with `nothing`, `none` or `n/a`), else the value as `field()` reads it.
   - `bridge_version`: the first `[0-9]{4}\.[0-9]{2}\.[0-9]{2}[a-z]?` found in the `Bridge version:` value read by `field()`, else `""`.
   - `workflows`: the parts `status_workflows` returns.
   - `stage`: `conformance-check.py`'s `status_field` regex applied to `Stage`, the value stripped, `""` when absent.
   - `open_issues`: `evaluate-reports.py`'s `Open issues:` line regex and its `status_segments`, both moved into `bridge_env`; `[]` when absent.

   Where the text opens with a `---` ... `---` block, `status_fallback` reads only the body after that block, whether or not the block parses. This matters because `field()` and `status_field` are case-insensitive, so the header's own `phase:` and `stage:` lines would otherwise be read as prose. The acceptance tests' malformed cases depend on it.
2. **`bridge_env.status_workflows(text)`** returns `(parts, problems)`. It reads the same body as Requirement 1.
   - `parts` is a list of `{"type", "subtype", "traits"}` in line order, one per `Workflows: ` line the strict grammar reads:
     - the prefix rule as `prefix_of` states it;
     - a `not yet classified` line gives no part;
     - the line holds exactly one `"; traits: "`;
     - the head is split at the arrow U+2192 into the type and an optional sub-type, with `None` when there is no sub-type;
     - `none` gives an empty trait list; otherwise the traits are split at `", "`.
   - `problems` is a list of strings, one per line the grammar refuses. Each holds `check_status`'s own wording for that refusal: `"Workflows line breaks the part-prefix rule"`, `"Workflows line must contain '; traits: ' exactly once"`, `"two Workflows lines name the same part"` or `"empty name in the Workflows head"`.
   - A refused line contributes no part.
   - Names are not checked against the open list here. `workflow-check.py`'s `check_status` keeps checking them and keeps all its findings. `workflow-check.py` keeps `check_placement`, the `Phase: ` placement check of the prose line.
   - The grammar has one copy, in `bridge_env`. `workflow-check.py`'s printed findings for a header-less status file stay as they are today.
3. **`bridge_env.status_values(text)`** returns `(values, malformed, disagrees)`:
   - `values` is a dict of exactly the six keys. Where the text has a well-formed header (`read_header` raises nothing and `check_header("project-status", header)` finds nothing), it holds the header's six values, without `record` and `header`. Otherwise it is `status_fallback(text)`.
   - `malformed` is `None`, or `(line, what)`. For a `HeaderError`, line is its `.line` and what is its message. For a schema fault, line is `1` and what is `check_header`'s findings joined by `"; "`.
   - `disagrees` is the list `header_agrees("project-status", header, status_fallback(text))` returns for a well-formed header, else `[]`.
   - A record with no header gives `(status_fallback(text), None, [])`.

   No program reads the status file except through these three functions, and each program reads only the keys the design's table gives it:
   - `loop-guard.py`: phase, awaiting_user_on.
   - `session-start.py`: phase, awaiting_user_on, bridge_version, workflows.
   - `conformance-check.py`: phase, stage, bridge_version, workflows.
   - `workflow-check.py --status`: workflows.
   - `inventory-check.py`: every key, for the agreement check.
   - `evaluate-reports.py`: open_issues.

   The status file's other checks stay prose checks: `check_placement`, `conformance-check.py`'s absolute-path scan and the caps.
4. **The fixed output lines.**
   - The hooks print `header malformed: <path>:<line>`, `header disagrees: <key>` and `workflows line refused: <reason>`, each on a line of its own.
   - The checkers print `HEADER MALFORMED: <path>:<line> <what>` and exit 2: `conformance-check.py`, `workflow-check.py --status` and `inventory-check.py`.
   - `inventory-check.py`'s agreement line is `HEADER DISAGREES: <key>`, a failure (exit 1).
   - `<path>` is the path the program read.
5. **`session-start.py`**:
   - The header's value governs three things: the phase modules (and the conventions) it names, the wait line (`WAITING FOR THE OWNER on: ...` against `Continue from where the status file says the work is.`), and the calibration line (`the status file records <stamp>`).
   - For each of `phase`, `awaiting_user_on`, `bridge_version` and `workflows` in `disagrees`, it prints `header disagrees: <key>` beside the pointers.
   - On a malformed header it falls back to the prose and prints `header malformed: <path>:<line>`.
   - A `Workflows:` line the grammar refuses is printed as `workflows line refused: <reason>` and names no conditional file. `<reason>` is the fixed `check_status` wording the problem holds, and the hook prints only one of the four wordings above, as an exact `str`.
   - The no-wait decision is the one normalisation (`awaiting_user_on == ""`). Retired readings (1) and (2) are gone as uses.
   - Its other output, the plain-line policy for the checker, and the cap stay as they are.
6. **`session-start.py`'s import of `bridge_env`**:
   - It imports `bridge_env` from its own folder (`os.path.dirname` of its real path) with a plain `import bridge_env` statement.
   - Before the import, it checks that `bridge_env.py` there is not a link (a symbolic link or a junction).
   - It follows the same load discipline it uses for `workflow-check.py`: no bytecode written, stdout and stderr redirected to a sink, `BaseException` caught, and the type name shown only through `safe_exc_type_name`.
   - On any failure of that import (a link, a missing file, an exception of any kind at import), `--part pointers` prints exactly one line, `~/.claude/cursor-bridge/bridge_env.py: cannot be loaded (<type name or "an exception">)`, and nothing else. Nothing the module printed and no traceback appear, stderr is empty, and the exit is 0. `--part digest` is unaffected.
   - Add one test to `tests/test_session_start.py` that runs a hook copy whose folder holds a `bridge_env.py` that raises at import, and asserts the plain line and nothing else.
   - The threat-model tests stay green unchanged: the `BROKEN` cases and their neighbours in `tests/test_session_start_module.py`, and the fail-open tests in `tests/test_session_start.py`.
7. **`loop-guard.py`**:
   - On a malformed header it allows or refuses the stop as the prose says.
   - Where `phase` or `awaiting_user_on` is in `disagrees`, it refuses the stop (exit 2) with `header disagrees: <key>` in its stderr message, one line per key, whatever else the stop would have been. This check comes after its `stop_hook_active` check.
   - It compares no other key.
   - With an agreeing header, it decides from the header's values exactly as it decides from the prose today.
   - It still fails open on every other error.
8. **`evaluate-reports.py`**:
   - With a well-formed header, it reads `open_issues` from it.
   - On a malformed header it falls back to the prose `Open issues:` line and writes `header malformed: <path>:<line>` into its collect report beside the project's lines.
   - Its other sources are unchanged.
9. **`inventory-check.py`**:
   - `--max-chars` and `--max-lines` count the body after the header. The `status: <n> lines / <m> chars` note and the `STATUS TOO LONG` failure report the body's counts.
   - Each option's help text contains the phrase `after the header`. The acceptance test counts that phrase in the printed `--help` output, which argparse wraps, so the phrase must not be broken across a line there.
   - It compares every key through `header_agrees` and fails `HEADER DISAGREES: <key>` for each disagreeing key.
   - On a malformed header it prints `HEADER MALFORMED: <path>:<line> <what>` and exits 2.
   - Regenerate the command reference: `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`.
10. **`conformance-check.py`**:
    - It keeps loading `bridge_env` by file (`_load_bridge_env`).
    - Its grades (`calibration_workflows_grades`, the `Workflows classification` note's phase) and its `project.json` phase comparison read the one `phase` value.
    - Its `project.json` stage comparison reads `stage`.
    - Its calibration row (`Calibrated to the installed bridge`) reads `bridge_version`, with no row where it is `""`.
    - Retired readings (3) and (4) are gone as uses.
    - On a malformed header it prints `HEADER MALFORMED: <path>:<line> <what>` and exits 2.
    - With an agreeing header, its status lines equal those for the same file without the header.
11. **`workflow-check.py --status`**:
    - On a malformed header it prints `HEADER MALFORMED: <path>:<line> <what>` and exits 2.
    - With an agreeing header, its output and exit equal those for the file without the header.
12. **No program's prose quotes a retired pattern.** This covers docstrings, comments and help texts. The currency test matches uses with docstrings and comments stripped, and a quoted pattern would be a hidden copy (KP-073).
13. **Housekeeping.**
    - Regenerate `bridge/cursor-bridge/MANIFEST.json` by running `python tools/make-manifest.py` from the Workspace root, as TASK-046 did (no `--version`: the version stays 2026.11.03a, read from the CHANGELOG), and quote the command and its output in your report.
    - Add or remove no option in any program, and add no dependency.
    - Output stays ASCII as today, apart from what a program already quotes.

## Acceptance criteria
- [ ] `python -m pytest -q tests/test_header_status.py` passes whole: every supervisor case above the marker and your own below it.
- [ ] Each of the six programs reads the header first through `bridge_env` and falls back to the one reading per field. Each gives the same answer on the four projects' status fixtures with and without a header written from the design's table.
- [ ] Retired readings (1) to (4) are gone as uses (`test_r058_retired_*` green). `session-start.py` refuses a `Workflows:` line the grammar refuses, and reads `Awaiting user on: Nothing`, `n/a`, `<nothing>` and `None yet` as no wait.
- [ ] Malformed headers are handled as stated:
  - the checkers print `HEADER MALFORMED: <path>:<line> <what>` with exit 2, on a tab in the block (the `HeaderError` line) and on a schema fault (line 1);
  - the hooks and the evaluation fall back, `session-start.py` and `evaluate-reports.py` naming the line.
- [ ] Disagreements are handled as stated:
  - `session-start.py` prints `header disagrees: <key>` for each of its four keys, and the header governs;
  - `loop-guard.py` refuses the stop for `phase` and `awaiting_user_on` and for no other key;
  - `inventory-check.py` prints `HEADER DISAGREES: <key>` for each of the six keys, exit 1.
- [ ] `inventory-check.py`'s caps count the body. Its `--help` holds `after the header` at least twice, unbroken. `python tools/dump-cli.py --check` is green with the regenerated `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`.
- [ ] A `bridge_env` that raises at import gives `session-start.py`'s plain line and nothing else (your new test in `tests/test_session_start.py`). The hook's threat-model tests are green.
- [ ] `check:components` prints OK: the five new plain imports are D-002's solid edges, and `conformance_check` keeps its dotted load. `python ~/.claude/cursor-bridge/diagram-check.py --mode code` gives RESULT OK, or is written `not run` with the reason.
- [ ] The full suite passes, apart from failures you report as outside the Scope. Every existing test in the Scope's files is green, and each one you corrected is named with the retired reading it pinned.
- [ ] MANIFEST is regenerated. No option is added or removed, and no dependency is added.
- [ ] R-058 is fully met, with no stand-in or placeholder, and at least one test you add names R-058 in its name, docstring or a comment.
- [ ] No new Semgrep high findings. The hook's output channel is unchanged: only exact `str` lines the hook composes from fixed wordings reach its output (ASVS L2, the threat-model row).

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. The one exception is running the installed diagram checker named in the Done section, which reads this workspace.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). Tests that run the programs pass it, as `tests/test_header_status.py`'s `run()` does.
- Never start a server, a watcher or a daemon that outlives a test.
- Do not refactor code outside the scope, even if it looks wrong. The `bridge_env.py` reader's own dead code and its three quote walkers stay.
- Never run the product, a migration, a seed or a test against the owner's live data. Run the programs only on fixtures and temporary copies (the Development data decision in Context); never on this repository's `docs/PROJECT_STATUS.md`.
- No value in this brief is marked as the owner's.
- Follow existing conventions in the files you touch: ASCII output, fail-open hooks, the plain-line policy in `session-start.py`.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- Numbers from text are parsed with the language's own parser, never by slicing a string. The header line numbers you print come from `HeaderError.line` (an int, 1-based) or are the literal `1`.
- An increment that starts a process: your tests start the programs as children through `subprocess.run` with output captured. Each child is windowless and ends before the test does, and nothing outlives the test.
- Every verification command is written in the Done section in full; run exactly those. The supervisor checks the increment's tests by mutation in its own run. You may mutate by hand in-process in your own run to test your cases; if you do, list each mutation and what caught it. No mutation script lands in the diff.
- The supervisor names no failure already known outside the Scope. If the full suite shows one in a test outside the Scope's files, report it by its test id as found and fix none of them.
- Prefer reuse over new code: move the existing readers rather than rewriting them, and write the minimum that meets the acceptance criteria. This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc`.

## Done
Your report is the file `handoff/TASK-047-r1-report.md`, which you write as you go, so that nothing of it is lost when your run ends early. It records what you did, what you changed, what you ran and what it printed, and what you could not do.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the tests you corrected in the existing files, each with the retired reading it pinned (or "none");
- the manifest command you ran;
- a section headed exactly `Assumed, not verified`.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples are an ambiguous requirement you resolved one way, a platform or library behaviour you expected, or a value you chose. Write one item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit:
1. `python -m pytest -q tests/test_header_status.py`
2. `python -m pytest -q tests/test_loop_guard.py tests/test_session_start.py tests/test_session_start_module.py tests/test_conformance_check.py tests/test_workflows_line_check.py tests/test_workflow_check.py tests/test_evaluate_reports.py tests/test_header_reader.py tests/test_header_schemas.py`
3. `python tools/dump-cli.py` and then `python tools/dump-cli.py --check`
4. `python tools/make-manifest.py`
5. `python ~/.claude/cursor-bridge/diagram-check.py --mode code`. This is the installed checker and is read-only. Write `not run` with the reason if it cannot run.
6. `python -m pytest -q`, the full suite, once.
7. `git rev-parse HEAD` and `git status --short`

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. A count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Write the report's results after the full-suite run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
