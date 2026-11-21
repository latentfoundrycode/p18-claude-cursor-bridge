---
record: brief
header: 1
id: "TASK-069"
round: 1
satisfies: [R-089]
scope: ["bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/pace-report.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_program_pace_rounds.py", "tests/test_pace_report.py", "tests/test_review_guard.py", "tests/test_review_guard_ceiling.py", "tests/test_d003_review_round_states.py", "docs/BUILDER_NOTES.md", "handoff/TASK-069-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-069: Review passes and round causes in the pace report (R-089)

## Objective
The pace report (`bridge/cursor-bridge/pace-report.py`) is blind to work that has no builder brief: in the field, a week in which a project merged a calibration in three review rounds, a dependency fix, a records pull request and a configuration increment read as 0 started, 0 merged and no cause line, because the report counts an ID only where a brief stands under a tracked `handoff/` and reads a round's cause only from a builder's launcher row. This increment makes the report count every increment and every recorded round. Three changes: (1) the one list of round causes in `bridge_env.py` gains an eighth cause, `base update`; (2) `review-guard.py snapshot` writes the round's cause, read from the round's SCOPE file, into the round's entry of the guard's rounds record, beside its time, as a new field `cause` that no count, lift or verdict reads; (3) the pace report counts a name (an increment's ID, or `PR-<n>` for a pull request) from four sources by one set of rules, counts round causes over all recorded rounds (not only builder rounds), and prints one line per week of recorded review passes by reviewer kind. The HARDENING column reads `refs/heads/main` as the commit list does.

Satisfies: R-089 - The pace report counts every increment and every recorded round (C20 as reshaped, F1, F6, C14): `review-guard.py snapshot` reads `Round cause: <cause>` from the round's SCOPE file into the round's entry of the rounds record, deciding no count and no lift; `pace-report.py` counts a name, an increment's ID or `PR-<n>`, where it has a brief, a rounds record of the guard or a tagged pass line, and `PR-<n>` also by a commit of main that closes with `(#<n>)` and whose subject names no name counted by one of those three; it counts round causes over rounds, under a heading that says rounds; it prints a line of recorded review passes per week by reviewer kind; the round causes stand once, in `bridge_env.py`, and gain `base update`; the HARDENING column reads `refs/heads/main`. (Its row in `docs/REQUIREMENTS.md`, line 115, holds the whole text. The part "there and in step 7's list" is a workflow text, not this brief's.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_program_pace_rounds.py
- tests/test_pace_report.py
- tests/test_review_guard.py
- tests/test_review_guard_ceiling.py
- tests/test_d003_review_round_states.py
- docs/BUILDER_NOTES.md
- handoff/TASK-069-r1-report.md

Limits on these paths:
- `bridge/cursor-bridge/bridge_env.py`: add `"base update"` as the eighth and last member of `ROUND_CAUSES` (lines 4403-4411). You may add one reader there if the guard and the report share it (for example the reading of a `Round cause:` value, or of a pass line); change nothing else in the file.
- `bridge/cursor-bridge/review-guard.py`: the snapshot's round entry and the reading of the cause (R2), and the docstring's description of `snapshot` if you mention the field. No other behaviour changes.
- `bridge/cursor-bridge/pace-report.py`: R3-R9.
- `tests/test_program_pace_rounds.py`: the supervisor's acceptance tests, committed at 85ad45b. Read it whole and run it. **Do not edit it.** If a case seems wrong, stop and report it by its test id.
- `tests/test_review_guard_ceiling.py` and `tests/test_d003_review_round_states.py`: listed so that you run them. Change nothing in either; they must pass unedited (the plan's Scope notes: the new field decides no count).
- `tests/test_review_guard.py`: you may add tests naming R-089; change no existing test.
- `tests/test_pace_report.py`: you may add tests naming R-089. One existing assertion is expected to change by R-089's rule (Context, "The one existing case R-089 changes"); change only that assertion, as described there, and no other existing test.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done); never by hand. The generator records each program's docstring, so a docstring change regenerates them.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done); never by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`; `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, `docs/diagrams/` included (D-003's note already lists the new field and its readers; Context).
- `tests/test_program_in_flight.py` and `tests/test_release_s_launcher.py`: the supervisor edited them in commit 85ad45b (they now hold the seven causes as the first seven and the new heading). They must pass unedited. Do not edit them; report a failure there by its test id.
- `bridge/cursor-bridge/bridge-run.py` and `bridge/cursor-bridge/in-flight.py`: they read `bridge_env.ROUND_CAUSES` already and take the eighth cause with no edit of theirs. Do not edit them.
- Every other program under `bridge/cursor-bridge/`, the texts under `bridge/commands/`, `bridge/agents/` and `bridge/cursor-bridge/workflow/` (the delegation loop's step 7 list included), and `bridge/cursor-bridge/CHANGELOG.md`.
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them and edit neither).
- Any new command-line option of `pace-report.py` or `review-guard.py` (the plan: no option added).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this increment:** `docs/DESIGN.md`, "Change: the program release", "Measurement", the bullet beginning `- *C20 as reshaped, F1, F6, C14.*` (line 352): read it whole; its *Counted*, *Started*, *Merged*, *Rounds and causes*, *Passes* and *Weeks* rules are the specification, and R3-R8 below restate them. The plan entry is `docs/BUILD_PLAN.md`, `### TASK-069` (line 1881), its Scope notes and its Done when (line 1890).

**The reality check (the supervisor's side, on this branch's checkpoint 85ad45b).**
- `bridge/cursor-bridge/bridge_env.py`: `ROUND_CAUSES` (lines 4403-4411) holds the seven `"defect", "security", "fix-induced", "no external path", "records", "builder incomplete", "brief error"`. `GRAMMAR_ID_PATTERN = r"[A-Z][A-Za-z0-9-]*"` (line 428). `squash_merged_ids_from_lines(lines, id_rx, plan_style=None)` (line 1237) is the reader of subjects; it returns a **set** of IDs, so it does not tell which ID a subject names first. `_valid_rounds_file(data)` (line 1439) checks only `round` (int) and `time` (str) per entry and `merge_ids`; `_read_rounds_files(common)` (line 1462) returns `{id_part: data}` for every valid `<common>/bridge/rounds-<id>.json`. `read_runs_jsonl(log_folder)` (line 1417) reads `run/launcher/runs.jsonl`.
- `bridge/cursor-bridge/bridge-run.py` line 990 is `ROUND_CAUSES = bridge_env.ROUND_CAUSES`, and `round_cause(brief_text)` (lines 994-1007) reads a brief's `Round cause:` line as quoted here:

```python
ROUND_CAUSE_RE = re.compile(r"^Round cause:[ \t]*(.*?)[ \t]*$", re.M)
...
    m = ROUND_CAUSE_RE.search(brief_text or "")
    if not m:
        return "unstated", ...
    value = m.group(1).lower()
    for cause in sorted(ROUND_CAUSES, key=len, reverse=True):
        rest = value[len(cause):].lstrip()
        if value.startswith(cause) and (not rest or rest[0] in "-:(,;" + <U+2013> + <U+2014>):
            return cause, None
    return "unstated", ...
```

  (In the source the last two separators are the characters U+2013 and U+2014, typed literally; `bridge-run.py` is outside Scope.)
- `bridge/cursor-bridge/in-flight.py` validates `--cause` against `bridge_env.ROUND_CAUSES` (line 261) and writes a pass line `<stamp> PASS <name> r<n> <reviewer> <cause>` (from line 263), where `<stamp>` is `YYYY-MM-DDTHH:MMZ` (17 characters, UTC to the minute), ` r<n>` is left out when no round was given and ` <cause>` is left out when no cause was given; `<name>` fullmatches `GRAMMAR_ID_PATTERN`; `<reviewer>` is one of `review-a`, `review-b`, `security-auditor`, `design-auditor`, `plan-critic`, `design-critic-b`, `supervisor`; `<cause>` may be two words (`no external path`, `base update`). The log is `<project root>/Workspace/run/supervisor/in-flight.md`; it also holds free-text lines (`<stamp> <text>`) and unstamped `Paused:` lines, which are not pass lines.
- `bridge/cursor-bridge/review-guard.py`: `cmd_snapshot(nnn, cwd)` (lines 860-962) builds the round's entry at lines 927-936 (`round`, `name`, `branch`, `tree`, `time`, `lift`, `lift_line`, `reply`) and, on a re-snapshot of a recorded round (lines 940-950), rebuilds it, keeping the round's first `time`, its `reply`, `lift`, `lift_line` and `flagged_launch`; then `write_rounds(common, id_part, data)` writes the record and its hash copy. `scope_blocking_line(root, id_part)` (lines 737-751) reads the round's SCOPE file: `run/review/SCOPE-<ID>.md`, then, for an ID that does not begin `STAGE-`, `run/review/SCOPE-STAGE-<ID>.md`. The guard imports `bridge_env` (line 113); `GIT_TIMEOUT = 120` (line 115). It holds no list of the causes today.
- `bridge/cursor-bridge/pace-report.py`: `ROUND_CAUSES = bridge_env.ROUND_CAUSES + ("unstated",)` (line 431); `_builder_rounds` and `_cause_and_model_lines` (lines 434-472) read the cause from builder rows only and write `Round causes (%d builder rounds after the first): %s` (line 462) and `Builder rounds per model: ...` (line 471). `_project_section` (lines 664-914) counts merged only for IDs with a brief (lines 691-700, `if untracked or ident in brief_ids`) and started only for IDs with a brief (lines 702-710). `_start_times` (lines 294-314) takes the earliest launcher row and non-`seeded` guard round. `_commits` (lines 317-354) reads `refs/heads/main`; `_hardening_by_week` (lines 357-391) runs `git log main ...` (line 360), not `refs/heads/main`. Every git call goes through `_git` with `GIT_LIMIT = 120` seconds (line 51). The program's source is ASCII (`test_r044_ascii_output_and_build_parser` asserts it); `review-guard.py` and `bridge_env.py` are ASCII too: keep all three so.
- `docs/diagrams/D-003-review-round-states.md` already lists the field: line 5 (the round's fields, `cause` the eleventh, written by `snapshot`, read by `pace-report.py`, deciding no count, lift or verdict), line 11 (the readers of the rounds record) and line 13. The Done when's clause "D-003's note lists the field and its readers" is met by the record as it stands; D-003 is not in your Scope and you do not edit it.

**The supervisor's acceptance tests.** `tests/test_program_pace_rounds.py` (ten cases) fixes the interface; read it whole. Each case builds a scratch project under pytest's `tmp_path` (`<tmp>/<name>/Workspace`, a git repository on `main` with `run/` ignored): launcher rows in `run/launcher/runs.jsonl`, guard records in `.git/bridge/rounds-<ID>.json` (entries with or without `cause`), pass lines in `run/supervisor/in-flight.md`, briefs under a tracked `handoff/`, commits with fixed dates. It runs `pace-report.py <root>` and reads: the table's week rows and `Total` row by their cells; the cause line, the line starting `Round causes`, whose counts it reads by the regex `(?<![\w-])<cause> (\d+)`; the passes lines, every line whose right-stripped text ends with `recorded passes only`, chosen per week by the week's label `YYYY-Www` occurring in the line (at most one line per label), each kind's count read by the regex `(?<![\w-])<kind>[\s:=]*(\d+)` (absent kind = 0). The guard case runs `review-guard.py snapshot` in scratch repositories with `HOME`, `USERPROFILE` and `BRIDGE_REVIEW_HASHES` redirected into `tmp_path`.

**Known failures before your change** (the supervisor's run on checkpoint 1a27fa0 with the acceptance file and the supervisor's edits, implementation stripped): `9 failed, 90 passed, 1 skipped` over `tests/test_program_pace_rounds.py`, `tests/test_program_in_flight.py` and `tests/test_release_s_launcher.py`: eight cases of the acceptance file red (`test_r089_the_builder_rounds_per_model_line_is_unchanged` and `test_r089_the_hardening_column_reads_refs_heads_main` pass, holding what stands), and in `tests/test_release_s_launcher.py` the heading case red (it expects `Round causes (4 rounds after the first): defect 1 (25%); fix-induced 2 (50%); unstated 1 (25%)`). The skip is `test_r088_a_file_reached_through_a_link_is_refused` (this account cannot create a symbolic link). After your change every command of the Done list passes, with only that skip.

**The one existing case R-089 changes.** `tests/test_pace_report.py::test_r044_iss013_form_merges_nothing_with_plan_check` commits a brief for TASK-031 and then, in week 2, the subject `docs: fixes (pointers, TASK-031's Scope, survival lists, records) (#61)` (line 15), and asserts the week's merged cell is `0` (line 155). The reader of subjects finds no ID in that subject (that is why the case passes today), so by R-089's *Counted* rule this commit is `PR-61`: it closes with `(#61)` and its subject names no counted name. It is then started and merged in week 2, and the merged cell becomes `1`. If that is what your change gives, change only line 155's expected value, with a one-line comment naming R-089 and `PR-61`, keep the plan-check half of the case unchanged, and name the change in the report. "Names" in R3 means the IDs the reader of subjects returns for the subject that are counted names, not any text in the subject (the design's parenthesis: the reader takes a leading capitalised word for an ID, so naming an ID alone would decide by a subject's spelling).

**External services.** None. This increment adds no call to an external service and no network call. Every git call of the report keeps the 120-second limit (`GIT_LIMIT`, through `_git`), and every git call of the guard keeps its `GIT_TIMEOUT` of 120 seconds; no new git call is needed beyond those the programs make today, and any you add goes through the same helper and limit, with no retry. This session has no `claude` on PATH; nothing in this increment calls it, and no test here needs it.

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions, line 138). `.cursor/rules/secure-coding.mdc` is in force for you. Outside input crossing into the programs: the SCOPE file's text (the guard), and, for the report, the launcher log, the guard's rounds records, the in-flight log and the commit subjects of `refs/heads/main`. Each may be malformed, huge, non-UTF-8 or hold a name or a word outside its list: the readers skip what they cannot read, never refuse, never print a traceback, and never print a word from these files unless it matched its pattern (a name `GRAMMAR_ID_PATTERN` fullmatches, a cause on the list, a reviewer kind on the list); the report's output stays ASCII. The guard's snapshot is never refused for the cause.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`, line 133) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: run `pace-report.py` and `review-guard.py` only through the tests, on their scratch projects under `tmp_path`. Never run `pace-report.py` with no roots (its default roots are the owner's live projects) and never run `review-guard.py snapshot` in this repository (it writes into this repository's `.git/bridge/`). Never install anything and never copy anything under `~/.claude`.

**Host.** Windows 11 with the owner's Python; CI also runs on Linux.

## Diagrams
`docs/diagrams/D-003-review-round-states.md` (the review round's states) is the normative diagram. The elements this increment touches are the rounds record's entry written at `snapshot_taken` and `resnapshotted`, and its readers. Line 5 (quoted in part): "each round: `round`, `name`, `branch`, `tree`, `time`, `lift`, `lift_line`, `reply`, `flagged_launch` once a flagged verify voided its launch, `seeded` for a seeded one, and ... `cause`, the round's cause, written by `snapshot` from the round's SCOPE file line `Round cause: <cause>` (or `unstated`), read by `pace-report.py`, deciding no count, lift or verdict". Line 13: "no count, lift or verdict reads it, so it adds no state and no transition". So: the field adds no state and no transition; no refusal, no ceiling decision, no reply or lift reading looks at it; only `pace-report.py` reads it. `docs/diagrams/D-002-components.md` keeps `review_guard --> bridge_env` and `pace_report --> bridge_env` (lines 139, 144): the guard and the report import `bridge_env` and no other bridge program for this work (the guard does not load `bridge-run.py`). If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
1. **R1. The eighth cause.** `bridge_env.ROUND_CAUSES` is exactly `("defect", "security", "fix-induced", "no external path", "records", "builder incomplete", "brief error", "base update")`; `"unstated"` is not a member. `pace-report.py` keeps `ROUND_CAUSES = bridge_env.ROUND_CAUSES + ("unstated",)` under that module-level name. `review-guard.py` reads the list as `bridge_env.ROUND_CAUSES` (its source names `bridge_env.ROUND_CAUSES`) and holds no copy of it: no source of yours may match the regex `["']builder incomplete["']\s*,\s*["']brief error["']` outside `bridge_env.py`.
2. **R2. The guard writes the round's cause.** `review-guard.py snapshot <name>` (for a name the grammar reads, so a round entry is written) adds the field `cause` to the round's entry, beside `time`. Its value: from the first line of the round's SCOPE file (the files `scope_blocking_line` reads, in its order, the first that exists) that begins `Round cause:`, the cause that line names, read as the launcher's `round_cause` reads a brief's line (case-insensitive cause, the longest cause first, followed by the end of the line or one of the separators `-`, `:`, `(`, `,`, `;`, U+2013, U+2014), so the same line gives the same cause in both programs; `unstated` where no SCOPE file exists, the file cannot be read, no line begins `Round cause:`, or the line names a word outside `bridge_env.ROUND_CAUSES`. A re-snapshot of a recorded round reads the line again and writes the new cause, keeping the round's first `time` as today. The cause never refuses a snapshot and never changes its exit code or output lines' meaning. No count, ceiling, lift, reply, verify, premerge or flag decision reads the field. The source stays ASCII (write U+2013 and U+2014 without typing them).
3. **R3. Counted names.** For each project the report counts names. A name is an increment's ID (a string `GRAMMAR_ID_PATTERN` fullmatches) or `PR-<n>` (`PR-` followed by a whole number from 1 up, parsed with `int`), the report's reserved form for a pull request. A name is counted where it has any of: a brief under a tracked `handoff/` (as `_ids_with_brief` reads it today); a rounds record of the guard (`_read_rounds_files`, a record named `STAGE-...` excepted: a stage review is not an increment and stays in the stage list as today); a pass line in `run/supervisor/in-flight.md` naming it. `PR-<n>` is also counted by a commit of `refs/heads/main` whose subject closes with `(#<n>)` and names no name counted by those three sources ("names" = the IDs the reader of subjects returns for that subject, Context). Where such a commit's subject names one or more counted names, `PR-<n>` is not a name of its own: its pass lines and their causes fold into the first counted name the subject names, by position in the subject (the reader returns a set; you find the order). A `PR-<n>` that main holds no `(#<n>)` commit for is a name of its own (started, not merged). One merge is never two names, and one pass never two passes.
4. **R4. Started.** A counted name starts at the earliest of its launcher rows (as `_start_times` reads them), its guard rounds (non-`seeded`, as today) and its pass lines (those folded into it included); a `PR-<n>` with none of them starts at its commit's time on main. The Started column counts names whose start falls in the week.
5. **R5. Merged.** By the commits of `refs/heads/main` alone: an ID by a subject the reader of subjects says names it (as today, its earliest such commit), `PR-<n>` by a subject closing with `(#<n>)` where it is a name of its own. A rounds record or a pass line never makes a name merged. In the field-week case, `Records: the week's status and the in-flight log (#24)` is read by the reader as naming `Records`, which is no counted name: it is `PR-24`, merged.
6. **R6. Rounds and causes.** One round per name and round number. Its records are: the builder's launcher rows (`kind` `builder`, not `slot` `not free`) with that `brief` and `round` (a row with no round is round 1), the guard's entry of that `round`, and the pass lines of that name and round (a pass line with no round number is round 1; folded pass lines count under the name they fold into). The round's cause is the first **stated** cause among, in this order, the builder's row, the guard's round, the pass lines; a value is stated when it is on `bridge_env.ROUND_CAUSES` (`unstated`, a missing field or a word outside the list is not stated); `unstated` only where none of them states one. Rounds after the first (round number 2 and up) are counted in the cause line.
7. **R7. The cause line.** Exactly one line, printed only where the window holds at least one round after the first, starting `Round causes (<n> rounds after the first): `, where `<n>` is the number of those rounds, followed by the parts `<cause> <count> (<pct>%)` joined by `; `, in the order of the report's `ROUND_CAUSES` (the list, then `unstated`), causes with a count of 0 left out, `<pct>` computed as today (`round(100.0 * count / n)`). This is today's form with the word `builder` gone from the heading. The tests `tests/test_release_s_launcher.py` and the acceptance file pin it.
8. **R8. The passes lines.** Below the cause line (or where it would stand), one line per week of the window that holds at least one recorded pass, in the table's week order. A pass is one per name, reviewer kind and round: a guard round is a `review-b` pass of its name and round; a pass line is a pass of its name, kind and round, counted only where the guard holds no round of that name and number when its kind is `review-b`, so a round that has both a guard round and a `review-b` pass line (with its number or without one, read as round 1) is one pass; the same name, kind and round written twice is one pass. A guard round's pass stands in the week of its `time`; a pass line's in the week of its line's time (for a pass written twice, its earliest). Each line holds its own week's label in the table's form `YYYY-Www` and no other week label, then each reviewer kind that has passes that week followed by its count (between the kind and its count only spaces, `:` or `=`; the regex `(?<![\w-])<kind>[\s:=]*(\d+)` must read it), and ends with exactly the words `recorded passes only`, with nothing after them (no full stop). Kinds are the seven of the in-flight program. The separators you choose are stated in the module docstring. No passes line starts with `Round causes` or `Builder rounds per model`.
9. **R9. Weeks.** A round, with its cause, stands in the week of its earliest record (its builder row, guard round or pass line), as a name's start does; it is in the cause line where that week is in the window. A pass stands in the week of its own record's time (R8). So a round whose builder row is on a Sunday and whose guard round is on the next Monday is counted once in the cause line, in the Sunday's week, and its `review-b` pass once, in the Monday's week (`test_r089_a_round_that_crosses_a_week_s_end_is_counted_once`).
10. **R10. What stays.** The `Builder rounds per model:` line keeps its form and counts builder launcher rows only (`test_r089_the_builder_rounds_per_model_line_is_unchanged` pins the exact line). The table's columns, header and Total row keep their form. The Rounds column, the over-ceiling list, the stage list and the `Starts unknown:` line keep their present rules (say in the report if your change alters what any of them shows, and how). With an untracked `handoff/` the table's cells keep today's rules (`n/a (handoff/ untracked)` for started and rounds); state in the report what the cause and passes lines do in that mode.
11. **R11. HARDENING reads `refs/heads/main`.** `_hardening_by_week` runs its `git log` on `refs/heads/main`, as `_commits` does; the failure messages name the command it runs. The column's numbers do not change (`test_r089_the_hardening_column_reads_refs_heads_main`).
12. **R12. The in-flight log is read safely.** The report reads `run/supervisor/in-flight.md` as UTF-8 with errors replaced; a missing or unreadable file is no pass lines; a line that does not match the pass-line form (Context) entirely is skipped; a malformed rounds record or launcher row is skipped as today. Any bound you put on the read is stated in the docstring.
13. **R13. The docstring.** `pace-report.py`'s module docstring describes the columns and lines as they now are: the counted names and their four sources, `PR-<n>` and its folding, started and merged, the cause line's sources and order, the passes lines and their limit (recorded passes only), the weeks rule, and that the HARDENING column reads `refs/heads/main`. No option is added. Regenerate the command reference (Done).
14. **R14. Tests of your own.** Any test you add names R-089 in its name or docstring. You add no test file.

## Acceptance criteria
- [ ] `tests/test_program_pace_rounds.py` passes whole, unedited (ten cases).
- [ ] `tests/test_pace_report.py`, `tests/test_review_guard.py`, `tests/test_review_guard_ceiling.py` and `tests/test_d003_review_round_states.py` pass; the ceiling and D-003 files unedited; in `tests/test_pace_report.py` at most the one assertion of the ISS-013 case changed, as Context says.
- [ ] `tests/test_program_in_flight.py`, `tests/test_release_s_launcher.py`, `tests/test_bridge_run.py` and `tests/test_dump_cli.py` pass unedited (only the link case of the in-flight file skipped on this account).
- [ ] `bridge_env.ROUND_CAUSES` is the seven and `base update`; the launcher, the guard, the in-flight program and the report read it and none holds a copy (R1).
- [ ] `review-guard.py snapshot` writes `cause` beside `time` in the round's entry, `unstated` for a missing line or a word outside the list, re-read on a re-snapshot, never a refusal, read by no decision (R2, D-003).
- [ ] The field's week reads 5 started, 4 merged and `Round causes (2 rounds after the first): ` with `records` 1 and `unstated` 1; a guard-recorded name that never merged is started and not merged (R3-R7).
- [ ] One passes line per week of recorded passes, each ending `recorded passes only`; a pass counted once per name, kind and round; a round crossing a week's end counted once (R8, R9).
- [ ] The model line unchanged; the HARDENING column reads `refs/heads/main` (R10, R11).
- [ ] `python tools/dump-cli.py --check` exits 0; MANIFEST regenerated; `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] `pace-report.py`, `review-guard.py` and `bridge_env.py` stay ASCII.
- [ ] R-089 (the parts this brief serves) is fully met: no stand-in, placeholder or "later" text. The acceptance tests naming R-089 are the supervisor's; any test you add names R-089 too.
- [ ] No new dependency, option, configuration key or environment variable. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- Do not edit `tests/test_program_pace_rounds.py`, `tests/test_review_guard_ceiling.py`, `tests/test_d003_review_round_states.py`, `tests/test_program_in_flight.py`, `tests/test_release_s_launcher.py`, `docs/diagrams/`, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- If this increment talked to an external service its tests would replay recorded responses; it talks to none. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms); both programs already do so through their git helpers (`NO_WINDOW`). Capturing output does not prevent the window. You need no new process; if you find you do, it goes through the existing helper.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"): never run `pace-report.py` with no root, never run `review-guard.py` in this repository.
- Follow existing conventions in the files you touch: ASCII program text, module docstrings that hold the usage, results returned as values, `main()` returning the exit code.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- Numbers from text are parsed with the language's own parser: a round number (`r<n>`, a whole number from 1 to 999, as the in-flight program writes it), `PR-<n>`'s number (a whole number from 1 up), a pass line's stamp (`datetime.strptime` with `%Y-%m-%dT%H:%MZ`, UTC), a guard round's `time` and a launcher row's `id` (as `_parse_run_time` reads them), a commit's `%ct` (seconds since the epoch, as `_commits` reads it). A value outside its range or form is skipped, never guessed.
- Every verification command the Done section asks you to run is written there in full; run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps your change after your run, and every mutant must fail a test. Before you finish, apply each of these by hand, one at a time, run `python -m pytest -p no:cacheprovider -q tests/test_program_pace_rounds.py` from the Workspace root, and revert. List each in the report by its label and text, with the test id that caught it, or `not caught`:
  - M1 `"base update"` removed from `bridge_env.ROUND_CAUSES`;
  - M2 the guard reads the last `Round cause:` line instead of the first;
  - M3 the guard writes a word outside the list as given instead of `unstated`;
  - M4 a re-snapshot keeps the round's earlier `cause`;
  - M5 the cause order guard round before builder row;
  - M6 a builder row's `unstated` taken as a stated cause;
  - M7 a `review-b` pass line counted beside a guard round of the same name and number;
  - M8 a pass line with no round number skipped instead of read as round 1;
  - M9 `PR-<n>` kept as a name of its own where its squash names a counted name;
  - M10 a pull request's pass folded into the last counted name its squash names instead of the first;
  - M11 a round placed in the week of its latest record instead of its earliest;
  - M12 a name with a guard record and no commit on main counted merged;
  - M13 a subject's leading capitalised word (`Records`) taken as a counted name, so `PR-24` is not counted.

  You cannot add a test to `tests/test_program_pace_rounds.py`. A mutant no test catches is reported as `not caught`, with one line on the case that would catch it; you may add that case to `tests/test_pace_report.py` or `tests/test_review_guard.py` (naming R-089) and then report what caught it.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- A value the brief marks as the owner's: none in this increment.
- Prefer reuse over new code: `bridge_env.ROUND_CAUSES`, `GRAMMAR_ID_PATTERN`, `squash_merged_ids_from_lines`, `_read_rounds_files`, `read_runs_jsonl`, the report's `_git`, `_parse_run_time` and `_iso_week`, the guard's `scope_blocking_line` file order, and the standard library; write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-069-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for R1-R14, one line each on what meets it, naming the functions and their lines as the files stand after your change; for R8, the separators you chose; for R10, what the Rounds column, the over-ceiling list, `Starts unknown:` and the untracked-handoff mode now show for names without a brief;
- the change to `tests/test_pace_report.py`'s ISS-013 case, if you made it, quoted as a diff;
- the mutation self-check list, M1-M13, each with the test id that caught it (or `not caught` and the case that would);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: an ambiguous requirement you resolved one way, a library or git behaviour you expected, a value you chose. Examples: how a `seeded` guard round counts for passes and causes; how a subject that names a counted name only through a trailer is ordered for folding. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py`
3. `python tools/dump-cli.py --check` (expect exit 0)
4. `python tools/make-manifest.py`
5. `git restore bridge/cursor-bridge/VERSION`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_pace_rounds.py tests/test_pace_report.py tests/test_review_guard.py tests/test_review_guard_ceiling.py tests/test_d003_review_round_states.py`
7. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_in_flight.py tests/test_release_s_launcher.py tests/test_bridge_run.py tests/test_dump_cli.py` (`tests/test_program_in_flight.py` and `tests/test_release_s_launcher.py` are outside Scope; a failure there is reported by test id, never fixed in those files.)
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
10. `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/pace-report.py','bridge/cursor-bridge/review-guard.py','bridge/cursor-bridge/bridge_env.py')]; print('ascii ok')"` (expect `ascii ok`)
11. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them (`-rs` prints the skip's reason).
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 11, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
