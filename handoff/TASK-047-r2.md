# TASK-047-r2: The status file's header in its six readers, round 2 (the reviewers' findings)

## Objective
Fix the following confirmed defect — repair the named cause, nothing else. This brief covers thirteen findings that both reviewers and the security review raised on round 1 of TASK-047 (commit f68a883). Each finding below names its root cause, its evidence, and the cases in `tests/test_header_status.py` (or the other named test) that fail today and must pass. The increment itself is unchanged.

Release B2 gives `docs/PROJECT_STATUS.md` a YAML front-matter header (`record: project-status`) with six typed values: `phase`, `workflows`, `awaiting_user_on`, `bridge_version`, `stage` and `open_issues`. Six programs read the status file: `loop-guard.py`, `session-start.py`, `conformance-check.py`, `workflow-check.py --status`, `inventory-check.py` and `evaluate-reports.py`. Each reads the header first through `bridge/cursor-bridge/bridge_env.py`, and falls back to the one prose reading per field kept in `bridge_env`. Each reacts to a malformed or disagreeing header as the design states. Round 1 built this. Round 2 repairs what the reviewers found in it.

The defects, each with its cause, its evidence and the required behaviour:

1. **(Blocking) An unterminated header block crashes the fallback.**
   - Cause: `_status_prose_body` (bridge_env.py about lines 2148-2156) calls `_find_block`. For a block that is never closed, `_find_block` raises `HeaderError`. The exception passes through `status_fallback` and then `status_values`, because `status_values` calls `status_fallback` before its `try` (about line 2310).
   - Evidence: conformance-check and inventory-check exit 1 with a traceback, and evaluate-reports crashes. loop-guard allows a stop the prose refuses, which is a regression from f68a883. session-start prints nothing.
   - The three cases: a block opened and never closed; a closing line with a trailing space; a lone Markdown rule on line 1.
   - Required: the fallback never raises. Where the text starts with a `---` line, the prose body starts after the first later line that is `---` with nothing after it but spaces, tabs or a carriage return. Where no such line follows, the body starts after the first line. `status_values` reads the header first, and names a `HeaderError` of any kind as malformed `(line, what)`; the fallback governs.
   - The checkers then print `HEADER MALFORMED: <path>:<line> <what>` and exit 2. session-start prints `header malformed: <path>:<line>`. loop-guard prints nothing for a malformed header and decides by the prose.
2. **(Blocking) The Workflows grammar exists twice.** It is in `bridge_env.status_workflows` (about lines 2244-2280) and in `workflow-check.py`'s `check_status`, `prefix_of` and `check_head` (about lines 583-705). The two already differ: bridge_env splits with `str.splitlines`, and workflow-check's `file_lines` splits at the line feed only. Required: one copy, in bridge_env. Requirements 2 to 4 give the details.
3. **(Blocking) session-start drops one of the four wordings.** Its `PLAIN_REASON` filter (line 116, used about line 510) drops `Workflows line must contain '; traits: ' exactly once`. Required: a refusal is printed when it is a member of `bridge_env.STATUS_WORKFLOWS_PROBLEMS`. See Requirement 5.
4. **(Blocking) session-start's import of bridge_env has no load discipline.** The import (lines 123-139) has no sink and does not set `sys.dont_write_bytecode`. Evidence: a module that prints at import reaches stdout and stderr, and `__pycache__` is written. Required: see Requirement 6.
5. **(Blocking) session-start shows a header line read as prose.** At about lines 513 and 518, `phase_show = field(status, "Phase")` and the awaiting fallback read the whole text, so on a malformed header the hook shows the header's own phase. Required: it shows the governing values. See Requirement 5.
6. **(Should fix) The checkers skip the header check silently.** workflow-check (lines 48-52 and 823), inventory-check (lines 38-43 and 263) and conformance-check (about line 799) import bridge_env softly. When it is missing or lacks `status_values`, they skip the header check without a word. Required: see Requirement 7.
7. **(Should fix) A part named twice still counts.** A line naming a part a second time is reported, yet still adds a part (bridge_env about lines 2259-2279). Required: it adds no part.
8. **(Should fix) A test launch is not windowless.** In `tests/test_session_start.py` about lines 204-206, the launch round 1 added has no `creationflags`, so `tests/test_tests_windowless.py` fails. Required: the launch spells `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)`.
9. **(Should fix) A count in the round-1 report had no output behind it.** The report wrote "(7 cases)" with no output line to back it. Required: every count in the report quotes the output line it comes from.
10. **A changed signature breaks an existing test.** Round 1 made `conformance-check.py`'s `calibration_workflows_grades(path, text, phase)` (line 703) require `phase`. `tests/test_running_projects_classify.py` line 119 calls it with two arguments and fails with `TypeError` (4 cases). Required: see Requirement 8.
11. **(Security, advisory) An absent field costs quadratic time.** The status patterns anchored with `^` under `re.M` begin with a whitespace class that crosses lines: `_status_hook_field` (about line 2160) and `_OPEN_ISSUES_RX` (about line 2145) with `^\s*`, and `_status_stage_field` (about line 2168) with `^[\s*_-]*`. Evidence: 3.2 s at 10,000 blank lines. Required: see Requirement 9.
12. **(Consider) loop-guard does not fail open on a missing bridge_env.** Its module-level `import bridge_env` (lines 47-49) sits outside its fail-open handler (lines 631-636), so a missing module gives a traceback. Required: see Requirement 10.
13. **(Security, advisory) `<what>` is printed unescaped.** conformance-check (about line 806) and inventory-check (about line 267) print `<what>` as it comes. Required: see Requirement 11.

Each defect is pinned by these cases, all in `tests/test_header_status.py` unless another file is named:

| Defect | Cases that pin it |
|---|---|
| 1 | The `BAD` kinds `lone-rule`, `trailing-space` and `unterminated`, in every test parametrized over `BAD_IDS`. |
| 2 | `test_r058_bridge_env_holds_the_four_workflows_wordings`, `test_r058_the_workflows_grammar_is_worded_only_in_bridge_env`, `test_r058_workflow_check_refuses_a_workflows_line_as_bridge_env_does`. |
| 3 | `test_r058_retired_1_session_start_refuses_a_line_the_grammar_refuses`. |
| 4 | `test_r058_session_start_sinks_what_bridge_env_prints_and_writes_no_bytecode`, `test_r058_session_start_prints_one_line_where_bridge_env_lacks_the_status_readers`. |
| 5 | The `PROJECT STATE: Phase: building.` assertion in `test_r058_session_start_falls_back_on_a_malformed_header_and_names_its_line`. |
| 6 | `test_r058_a_checker_without_the_status_readers_refuses_and_never_skips_the_header`. |
| 7 | `test_r058_a_line_naming_a_part_twice_is_a_problem_and_adds_no_part`. |
| 8 | `tests/test_tests_windowless.py`. |
| 10 | `tests/test_running_projects_classify.py`. |
| 11 | `test_r058_the_status_values_of_a_padded_file_take_linear_time`. |
| 12 | `test_r058_loop_guard_without_bridge_env_fails_open_with_one_plain_line`. |

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
- handoff/TASK-047-r2-report.md

Limits on the test files:
- **`tests/test_header_status.py`** is the supervisor's, and its cases are the reproduction tests of this round. You edit nothing above its marker line, `# --- THE BUILDER'S CASES GO BELOW THIS LINE; NOTHING ABOVE IT IS EDITED ---`. You may add cases below that line.
- **`tests/test_workflow_check.py` and `tests/test_workflows_line_check.py`** each have a harness that copies a checker into a folder of its own: `test_workflow_check.py` about line 1820, `test_workflows_line_check.py` about lines 279-283. The one change you may make to either harness is to copy `bridge/cursor-bridge/bridge_env.py` beside the checker as well. Beyond that you may only add cases.
- **`tests/test_session_start.py`**: you may change the launch at about lines 204-206 to add `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)`, and you may add cases.
- **The other test files listed above**: you may only add cases.
- **`tests/test_running_projects_classify.py` and `tests/test_tests_windowless.py`** are not in Scope. They must pass unedited.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, including PROJECT_STATUS.md, INVENTORY.md, REQUIREMENTS.md, BUILD_PLAN.md, DESIGN.md, HARDENING.md and the diagrams.
- Any edit of `read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS`, or the reader's private helpers in `bridge_env.py` (`_find_block` among them). You call them; you do not change them.
- The other records' headers (TASK-048 to TASK-050), `records-migrate.py` (TASK-051), and retired readings (5) to (11).
- The loop guard's run-parameters comparisons (`agent_ceiling`, `ceiling_above_twice`) and its `Ceiling above twice:` regex.
- Keeping a `bridge_env` package or `.pyd` beside the hook from being loaded instead of `bridge_env.py`. The supervisor records that in HARDENING; it is not this round's work.
- Any mutation script. The mutants file and the mutation run are the supervisor's.

## Context
**The design that binds this increment.** `docs/DESIGN.md`, section "## Change: release B2 (2026-11-04)":
- the `docs/PROJECT_STATUS.md` row of "The records and their headers";
- "The fallback readers, one copy each";
- "Header first; fallback; malformed";
- the D-002 bullet on `session_start`'s import.

Also read `docs/REQUIREMENTS.md` row R-058, and the `docs/INVENTORY.md` Decisions rows "The session-start hook's threat model", "The header policy", "A malformed header ..." and "The status file's caps".

**The supervisor's tests.** The module docstring of `tests/test_header_status.py` pins the fixed forms. Its "Round 2" paragraph pins this round's decisions, repeated here:
- **The fallback never raises.** Where the text starts with a `---` line, the prose body starts after the first later line that is `---` with nothing after it but spaces, tabs or a carriage return. Where no such line follows, it starts after the first line. `status_values` reads the header first and names a `HeaderError` of any kind, an unterminated block included, as malformed; the fallback governs.
- **`bridge_env.STATUS_WORKFLOWS_PROBLEMS`** is the tuple of the four wordings, in this order:
  1. `"Workflows line breaks the part-prefix rule"`
  2. `"Workflows line must contain '; traits: ' exactly once"`
  3. `"two Workflows lines name the same part"`
  4. `"empty name in the Workflows head"`

  They are worded nowhere else: workflow-check, session-start and conformance-check take them from bridge_env. workflow-check's `--status` refuses exactly the lines `status_workflows` refuses. A line naming a part a second time is a problem and adds no part.
- **The fallback of a file padded with blank or space-only lines takes linear time.**
- **session-start loads bridge_env under the same discipline it uses for workflow-check.** Nothing the module prints reaches either part, and no bytecode is written. A module without the status readers gives one plain line: `~/.claude/cursor-bridge/bridge_env.py: cannot be loaded (<type>)` or `... cannot be used (<type>)`. The phase it shows is the governing value, never a header line read as prose.
- **The checkers need a usable bridge_env.** Without one (missing, or without `status_values`), workflow-check and inventory-check exit 2 with a line naming bridge_env, never skipping the header check. Without one, loop-guard allows the stop with exactly one stderr line naming it, and no traceback.

The `BAD` dictionary (about line 168) runs five malformed kinds through every malformed test:
- `tab`: a tab inside the block.
- `schema`: a value the schema refuses, named on line 1.
- `unterminated`: `"---\nrecord: project-status\n"` followed by the prose.
- `trailing-space`: a block whose closing line is `--- ` (with a trailing space). Its block says `phase: done`; the prose after it says `building`, and the prose governs.
- `lone-rule`: `"---\n"` and then the prose.

`bad_line` gives the expected line: 1 for `schema`, otherwise the line of the `HeaderError` that `read_header` raises.

**What exists at HEAD (round 1), with the fixed forms you keep.**
- **`bridge_env.py`** (lines 2143-2333): `_status_prose_body`, `_status_hook_field`, `_status_stage_field`, `_status_bridge_stamp`, `_status_segments`, `_status_prefix_of`, `_status_workflow_part`, `status_workflows(text)` returning `(parts, problems)`, `status_fallback(text)` returning the six-key dict, and `status_values(text)` returning `(values, malformed, disagrees)`. The fixed forms of these three public functions stay as round 1's brief and the test docstring state them. `status_workflows` keeps its `(parts, problems)` return; each part is `{"type", "subtype", "traits"}` and `subtype` is `None` where absent. The type and sub-type are split at the arrow, U+2192.
- **`workflow-check.py`**:
  - `file_lines(text)` (line 100) splits at the line feed only (R-015, R6-2). `read_utf8` reads with universal newlines.
  - `escape_field(value)` (line 134).
  - `prefix_of(rest, multi)` (583) returns `(part or None, body, bad)`.
  - `check_head(head, path, tables, findings)` (608) appends `("form", path, "-", "empty name in the Workflows head")` among its other findings.
  - `check_traits` (649).
  - `check_status(path, text, tables)` (679) emits these findings: `("form", shown, bad, <part-prefix wording>)`, `("e", shown, part, <same-part wording>)` and `("form", shown, "-", <traits wording>)`.
  - `print_findings` prints `FAIL (<code>) <path>: <name> - <reason>`.
  - `main()` checks the header at about line 823.
- **`conformance-check.py`**:
  - `_load_bridge_env()` (line 97) loads bridge_env by file. That is D-002's dotted edge, and it stays.
  - `calibration_workflows_grades(path, text, phase)` (703) loads `workflow-check.py` by file and walks the Workflows lines with `mod.file_lines`, `mod.prefix_of`, `mod.TRAITS_MARK`, `mod.check_head` and `mod.check_traits` (about lines 745-771).
  - `main()` reads the header at about lines 797-808, and calls the grades at about line 1046.
- **`inventory-check.py`**: the soft import is at lines 38-43. It already formats fields through workflow-check's `escape_field` (`mod.escape_field`, about line 203). It checks the header at about lines 263-272.
- **`session-start.py`**:
  - `CHECKER_SHOWN` (110), `BRIDGE_ENV_SHOWN` (111), `PLAIN_REASON` (116).
  - The bridge_env import with its link check (123-139).
  - `field()` (174).
  - `load_checker_module()` (217-234): `sys.dont_write_bytecode` set and restored in `finally`, `contextlib.redirect_stdout(sink)` and `contextlib.redirect_stderr(sink)`, `except BaseException`, and the line `"%s: cannot be loaded (%s)" % (CHECKER_SHOWN, safe_exc_type_name(err))`.
  - `safe_exc_type_name(err)` (243).
  - `pointers_part` (497-576).
  - `main()` prints the one plain line alone on `--part pointers` when the import failed (619-623).
- **`loop-guard.py`**: the module-level `import bridge_env` (47-49), the unused `read_status` (163), `read_status_file` (171), `main()` (567-624), and the fail-open wrapper (631-636).
- **`evaluate-reports.py`**: `status_entries` calls `status_values` (about line 282), then calls `status_fallback` again on a malformed header (about line 287). Since `status_values` already returns the fallback values in that case, the second call is redundant.

**Security context.** The project's ASVS level is 2 (INVENTORY, Decisions; D-004). The trust boundary is the session-start hook's threat model (INVENTORY, Decisions): a partial, mismatched or hand-edited install, not a hostile module. Nothing an in-process module returns reaches the hook's output except as an exact `str` the hook checks. The status file is text the supervisor writes; the reader executes nothing. `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force for you.

**Development data.** The development build is the Workspace sources under `bridge/`. A session in the repository runs the *installed* bridge (`~/.claude`), never the one being edited. Every test runs on fixtures and temporary copies. The four projects' status fixtures are `tests/fixtures/workflows/{bridge,tdp,reangle,video-factory}.status.md`. They are CRLF files, stay header-less, and are not edited. Never run a program of this increment over this repository's own `docs/PROJECT_STATUS.md` or over another project's records.

## Diagrams
`docs/diagrams/D-002-components.md` covers the elements `bridge_env`, `loop_guard`, `session_start`, `conformance_check`, `workflow_check`, `inventory_check` and `evaluate_reports`:

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

A solid edge is "an `import bridge_env` statement, which `check:components` sees". The five programs `loop_guard`, `session_start`, `workflow_check`, `inventory_check` and `evaluate_reports` keep their plain `import bridge_env` statements:
- session-start keeps its plain import. It does not switch to a `spec_from_file_location` load, because the diagram draws no dotted `session_start -.-> bridge_env`.
- loop-guard keeps its plain import too, inside its fail-open handling.

`conformance_check` keeps its load of bridge_env by file (`_load_bridge_env`), and gains no plain import. No program gains an import or a `spec_from_file_location` load the diagram does not draw. If the work cannot be done within the diagram, stop and report the conflict instead of deviating.

## Requirements
1. **The fallback never raises (defect 1).**
   - `status_fallback`, `status_workflows` and `status_values` raise nothing on any `str`.
   - Where the text, after a dropped byte-order mark, starts with a line that is `---` with nothing after it but spaces, tabs or a carriage return, the prose body starts after the first later line of that same form. Where no such later line exists, the body starts after the first line.
   - `status_values` reads the header first, by `read_header` and `check_header`. A `HeaderError` of any kind gives `malformed = (err.line, str(err))` with `values = status_fallback(text)` and `disagrees = []`. Every other fixed form of round 1 stays.
2. **One grammar, in bridge_env (defects 2 and 7).**
   - `bridge_env.STATUS_WORKFLOWS_PROBLEMS` is the tuple of the four wordings, in the order the Context gives.
   - No string constant holding any of the four wordings remains in `workflow-check.py`, `session-start.py` or `conformance-check.py`, docstrings included. The test matches substrings of every string constant, and drops a leading `Workflows line ` from the first two wordings first.
   - bridge_env holds the one per-line reading of the `Workflows: ` lines: the part prefix, the duplicate part, the `"; traits: "` count, and the empty name in the head. Both `status_workflows` and workflow-check's `check_status` use it.
   - A line naming a part a second time is a problem and adds no part.
3. **workflow-check's `--status` refuses what bridge_env refuses (defect 2).**
   - It refuses exactly the lines `status_workflows` refuses, with the same wording. It keeps its `FAIL (<code>) <path>: <name> - <reason>` format, its codes (`form` for the prefix, traits-count and empty-name refusals; `e` for the same part), and the part name it prints today (the bad part text or `-` for a prefix refusal, the part for a duplicate).
   - Its open-list checks of names and traits (`check_head`'s other findings, `check_traits`) and `check_placement` stay in workflow-check and keep their findings.
   - The status text is split at the line feed only, as `file_lines` does (R-015). A carriage return just before a line feed counts as part of the line ending, so a CRLF file reads like the same file with LF endings. A form feed, a vertical tab, the file, group and record separators, NEL, U+2028 and U+2029 stay inside the line.
   - The existing tests in `tests/test_workflow_check.py` and `tests/test_workflows_line_check.py` keep passing unedited, apart from the harness copy the Scope allows.
4. **conformance-check takes the Workflows parts from bridge_env (defect 2).** Its Workflows classification reading in `calibration_workflows_grades` (about lines 745-771) gets each line's part, body or refusal from bridge_env's per-line reading, through its existing load by file. It uses no `prefix_of`, `TRAITS_MARK` or own split of the grammar. Its open-list checks of names and traits keep using workflow-check's checkers, and its grades and notes are unchanged on every existing test.
5. **session-start prints only checked strings and shows the governing values (defects 3 and 5).**
   - A refusal from `status_workflows` is printed as `workflows line refused: <reason>` exactly when all three hold: `type(reason) is str`, the reason is a member of `bridge_env.STATUS_WORKFLOWS_PROBLEMS`, and it is printable ASCII. All four wordings, the traits wording included, are printed.
   - `PROJECT STATE: Phase: <phase>.` shows the governing `phase` from `status_values`, or `unknown` where it is `""`. `Awaiting user on: <value>` shows the governing `awaiting_user_on`, or `nothing` where it is `""`. The same governing values feed the phase-module line, the wait line and the calibration line.
   - session-start reads no value from the status text itself. It makes no `field()` call on the status text; remove `field` if it becomes unused.
6. **session-start's import of bridge_env (defect 4).**
   - It keeps its plain `import bridge_env` statement from its own folder (`os.path.dirname` of its real path, on `sys.path`), and its link check on `bridge_env.py` before the import.
   - Around the import: `sys.dont_write_bytecode` is set to `True` and restored afterwards (in a `finally`); stdout and stderr are redirected to a sink, as `load_checker_module` does; and `BaseException` is caught.
   - On any failure (a link, a missing file, an exception of any kind at import), `--part pointers` prints exactly one line, `~/.claude/cursor-bridge/bridge_env.py: cannot be loaded (<safe type name>)`, and nothing else.
   - A module that imports but lacks any of `status_values`, `status_workflows` or `STATUS_WORKFLOWS_PROBLEMS` gives exactly one line on `--part pointers`, `~/.claude/cursor-bridge/bridge_env.py: cannot be used (<safe type name>)`, and nothing else. The type name is shown only through `safe_exc_type_name`.
   - In every one of these cases: nothing the module printed and no traceback appears; stderr is empty; the exit is 0; and no `__pycache__` is written beside the hook. `--part digest` is unaffected.
   - The threat-model tests in `tests/test_session_start_module.py`, and the fail-open tests in `tests/test_session_start.py`, stay green unchanged.
7. **The checkers refuse rather than skip (defects 6 and 13).**
   - `workflow-check.py --status`, without a usable bridge_env (missing, raising at import, or lacking `status_values`), exits 2 with one line naming `bridge_env.py`: `cannot be loaded (<safe type name>)` or `cannot be used (<safe type name>)`. No traceback.
   - `inventory-check.py` behaves the same whenever it has a status file to check. The line is printed even where its other inputs are missing.
   - Neither prints a traceback in any mode for a missing bridge_env.
   - `conformance-check.py`, where `_load_bridge_env` gives no module with `status_values`, prints a `NOT CHECKED` or `MISSING` row naming `bridge_env.py` for each status row it cannot grade. It never silently drops `Calibrated to the installed bridge` or the `project.json` comparison.
   - The `<what>` (and the path) of `HEADER MALFORMED: <path>:<line> <what>` passes through workflow-check's `escape_field`, or an equivalent producing the same output, in conformance-check (about line 806) and inventory-check (about line 267), as workflow-check already does.
8. **`calibration_workflows_grades` keeps its callers (defect 10).** Every existing caller and test can call it, `tests/test_running_projects_classify.py`'s two-argument call included. Make `phase` optional, or pass it another way. Where no phase is passed, it uses the phase bridge_env reads from that text through `status_values`, never a reading of its own; retired reading (4) stays gone.
9. **Linear time (defect 11).** In the patterns `status_fallback` applies with `^` under `re.M`, the leading whitespace class matches only spaces and tabs (`[ \t]` in place of `\s`): the hook field pattern, `_OPEN_ISSUES_RX`, and the leading class of the Stage pattern. Nothing else in those patterns changes. `status_values` of a file of 20,000 blank lines, or 20,000 space-only lines, returns in well under 2 seconds.
10. **loop-guard fails open without bridge_env (defect 12).** Without a usable bridge_env (missing, raising at import, or lacking `status_values`), loop-guard allows the stop (exit 0) and writes exactly one stderr line naming `bridge_env.py`, with no traceback. It keeps its plain `import bridge_env` statement. Remove the unused `read_status`. Remove evaluate-reports' second `status_fallback` call, using the values `status_values` returns.
11. **Everything round 1 required still holds.** Round 1's Requirements 1 to 13 are the frozen forms: the six keys and their one fallback reading each, `status_values`' three-part return, and the fixed output lines. In addition:
    - session-start prints `header disagrees: <key>` for `phase`, `awaiting_user_on`, `bridge_version` and `workflows`.
    - loop-guard refuses the stop (exit 2) on a disagreeing `phase` or `awaiting_user_on`, after its `stop_hook_active` check.
    - inventory-check prints `HEADER DISAGREES: <key>` (exit 1), and its caps count the body after the header.
    - The retired readings (1) to (4) stay gone.
    - No option is added or removed, and no dependency is added.
    - Output stays ASCII.
    - The command reference and MANIFEST are regenerated: `python tools/make-manifest.py` with no `--version`, so the version stays 2026.11.03a.

## Acceptance criteria
- [ ] `python -m pytest -q tests/test_header_status.py` passes whole: every case above the marker, and any you add below it.
- [ ] `python -m pytest -q tests/test_running_projects_classify.py tests/test_tests_windowless.py` passes, with both files unedited.
- [ ] Defect 1: the `lone-rule`, `trailing-space` and `unterminated` kinds pass in every malformed test. The checkers print `HEADER MALFORMED` with exit 2 and no traceback. The hooks and evaluate-reports fall back and name the line where the design says so, and loop-guard decides by the prose. The fallback raises nothing; the mechanism is the prose-body rule in Requirement 1.
- [ ] Defect 2: the grammar has one copy, in bridge_env. `STATUS_WORKFLOWS_PROBLEMS` holds the four wordings in order, and none of the three programs holds a string constant containing one. workflow-check refuses exactly the lines `status_workflows` refuses, the form-feed case included.
- [ ] Defect 3: session-start prints all four refusals, the traits wording included.
- [ ] Defect 4: a bridge_env that prints at import leaks nothing, and no bytecode is written. A bridge_env lacking the status readers gives exactly one plain line.
- [ ] Defect 5: the phase shown is the governing value (`PROJECT STATE: Phase: building.` on every malformed kind).
- [ ] Defect 6: workflow-check and inventory-check without a usable bridge_env exit 2, naming it, with no traceback. conformance-check names bridge_env.py in a row instead of dropping its status rows. The two harnesses copy bridge_env.py beside the checker.
- [ ] Defect 7: a duplicate part line adds no part.
- [ ] Defect 8: the launch in `tests/test_session_start.py` spells `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)`.
- [ ] Defect 9: every count in the report quotes the output line it comes from.
- [ ] Defect 10: `calibration_workflows_grades` accepts the existing two-argument call.
- [ ] Defect 11: the padded-file test passes on both pads.
- [ ] Defect 12: loop-guard without bridge_env exits 0 with one stderr line naming it. Its dead `read_status` and evaluate-reports' second `status_fallback` call are gone.
- [ ] Defect 13: `<what>` is escaped in conformance-check and inventory-check.
- [ ] The scope bundle (Done step 3) passes. `python tools/dump-cli.py --check` is green. MANIFEST is regenerated. `check:components` prints OK (Done step 6).
- [ ] The full `tests/` tree passes (Done step 7).
- [ ] R-058 stays fully met, with no stand-in or placeholder. Any case you add names R-058 in its name, docstring or a comment.
- [ ] No new Semgrep high findings. Only exact `str` lines the hook composes from fixed wordings, and from the four checked wordings, reach the hook's output (ASVS L2, the threat-model row).

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall, such as a cause you found or a platform quirk that cost you a round: one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code or your tests launch on Windows is created windowless: `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)`, as `tests/test_header_status.py`'s `run()` does.
- Never start a server, a watcher or a daemon that outlives a test. Your tests start the programs as children through `subprocess.run` with output captured. Each child is windowless and ends before the test does.
- Do not fix by suppressing the symptom. That rules out a retry, a broad `try/except` around a reader, a widened tolerance, an added `sleep`, and a null-check that hides a wrong value. Catching `HeaderError` inside `status_values` is the named behaviour, not a suppression. The fallback must not raise because its body rule never calls a raising reader, not because an exception is swallowed.
- Do not edit the reproduction tests: nothing above the marker in `tests/test_header_status.py`, nothing in `tests/test_running_projects_classify.py` or `tests/test_tests_windowless.py`.
- Do not leave any `DEBUG-BUG-` line or stray print.
- If you believe the real cause of a defect is different from the one named, stop, do not change code for that defect, and report why in your report and your last message. The supervisor will re-diagnose.
- Do not refactor code outside the scope, even if it looks wrong. The bridge_env reader's own dead code and its three quote walkers stay.
- Never run the product, a migration, a seed or a test against the owner's live data. Run the programs only on fixtures and temporary copies, never on this repository's `docs/PROJECT_STATUS.md`.
- No value in this brief is marked as the owner's.
- Follow existing conventions in the files you touch: ASCII output, fail-open hooks, and the plain-line policy in `session-start.py`.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- Numbers from text are parsed with the language's own parser, never by slicing a string. The header line numbers you print come from `HeaderError.line` (an int, 1-based) or are the literal `1`.
- Every verification command is written in the Done section in full; run exactly those. The supervisor checks the increment's tests by mutation in its own run. You may mutate by hand in-process in your own run; if you do, list each mutation and what caught it. No mutation script lands in the diff.
- No failure outside the Scope is known: round 1's two (`tests/test_running_projects_classify.py` and `tests/test_tests_windowless.py::test_fix001_no_test_starts_a_program_around_the_default`) are this round's to fix. If the full `tests/` run shows a failure in a test outside the Scope's files that this change did not cause, report it by its test id and fix none.
- Prefer reuse over new code: move the existing readers rather than rewriting them, and write the minimum that meets the acceptance criteria. This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc`.

## Done
Your report is the file `handoff/TASK-047-r2-report.md`. Write it as you go, so that nothing is lost if your run ends early. It records what you did, what you changed, what you ran and what it printed, and what you could not do.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for each of the thirteen defects, one sentence on how the change addresses the named cause;
- the tests you changed in the existing files, each with the reason (the harness copy, the `creationflags` line), or "none";
- the manifest command you ran and its output;
- a section headed exactly `Assumed, not verified`.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples are an ambiguous requirement you resolved one way, a platform or library behaviour you expected, or a value you chose. Write one item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit:
1. `python -m pytest -q tests/test_header_status.py`
2. `python -m pytest -q tests/test_running_projects_classify.py tests/test_tests_windowless.py`
3. `python -m pytest -q tests/test_loop_guard.py tests/test_session_start.py tests/test_session_start_module.py tests/test_conformance_check.py tests/test_workflows_line_check.py tests/test_workflow_check.py tests/test_evaluate_reports.py tests/test_header_reader.py tests/test_header_schemas.py`
4. `python tools/dump-cli.py` and then `python tools/dump-cli.py --check`
5. `python tools/make-manifest.py`
6. `python bridge/cursor-bridge/diagram-check.py --mode code`. This is the Workspace copy, and it is read-only.
7. `python -m pytest -q tests`, the full `tests/` tree, once.
8. `git rev-parse HEAD` and `git status --short`

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. A count, or a claim that a check passed, quotes the output line that shows it: a number of failing cases is backed by the pytest lines naming them, never written on its own. A command you did not run is written `not run`, never described as run. Write the report's results after the full run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
