---
record: brief
header: 1
id: "TASK-091"
round: 1
satisfies: [R-113]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_slot_line.py", "tests/test_bridge_run_slot.py", "tests/test_hotfix24a_heavy_slots.py", "tests/test_loop_text_windowless.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-091-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-091: The heavy slot's line names the holder's limit, project and branch

## Objective
The launcher, `bridge/cursor-bridge/bridge-run.py`, makes a heavy run (`builder`, `driver`, `test`) wait for a machine-wide slot, and while it waits it prints who holds the slot. Today that line names the holder's kind, run id, start and end time. A waiter needs to know more: how long the holder may run, and which project and branch it belongs to. This increment adds two fields to the holder record a heavy run publishes, `project` (the holder's project folder's name, never a path) and `branch` (the run's branch, the same value its run row records). The record's reader accepts them only under a strict character list and length bound. Every line that names a holder then goes on with the holder's limit in seconds, its project and its branch. A record written by the released version, without the two fields, is still read, and its line names the limit only. There is no queue, no priority, no new option, and no change to how long a waiter waits.

Satisfies: R-113

That row of `docs/REQUIREMENTS.md` reads: "A waiter for the heavy slot is told who holds it and for how long (C51): the holder record and the waiter's line carry the holder's limit in seconds and its project folder's name with its branch; no queue and no priority." You change no record of the row. R-113 stays `planned`; the supervisor's records commit writes it built.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_slot_line.py
- tests/test_bridge_run_slot.py
- tests/test_hotfix24a_heavy_slots.py
- tests/test_loop_text_windowless.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-091-r1-report.md

Do not modify anything else.

Limits on these paths:
- `tests/test_improve_slot_line.py` is the supervisor's acceptance file. `tests/test_bridge_run_slot.py` and `tests/test_hotfix24a_heavy_slots.py` hold the line by a whole match; the supervisor changed those matches to the new line before the checkpoint (marked `TASK-091`). `tests/test_loop_text_windowless.py` is unchanged and must stay so. All four were committed at the checkpoint and are listed in Scope only because the plan lists them. Read them and run them. **Do not edit any of the four.**
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py`. Never edit any of the three by hand (Done). If `dump-cli.py` leaves the two reference files unchanged, that is the expected outcome (Requirement 7); say so in the report.
- `docs/BUILDER_NOTES.md`: add new dated lines at its end only.
- In `bridge-run.py`, change only what Requirements 1 to 7 need.

## Out of scope
- .env and anything under secrets/
- CI configuration
- `docs/` and `handoff/`, except the files the Scope section names. `docs/REQUIREMENTS.md`, `docs/HARDENING.md` and `docs/PROJECT_STATUS.md` are the supervisor's records, written in its records-only commit.
- The loop's text under `bridge/cursor-bridge/workflow/` (including `workflow/phases/delegation-loop.md`, which quotes the waiting line's form). It is not edited here; the report names it for TASK-096 (Done).
- `bridge/cursor-bridge/CHANGELOG.md`, `bridge/cursor-bridge/VERSION` (which must come out unchanged), `bridge/cursor-bridge/bridge_env.py`, every other program under `bridge/`, and every text under `bridge/commands/` and `bridge/agents/`.
- Every test file, the four in Scope included. Also `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every option of the launcher: none is added, removed or renamed. No queue, no priority, no new environment name, and no change to the wait bound's arithmetic or to `holder_end_time`'s result.
- Every brief under `handoff/` other than your report.

## Context
Line numbers are those of `1e6a696`, on which `bridge-run.py` is unchanged. The supervisor's checkpoint commit adds only test files and this brief, so they still hold; check each against the file before you rely on it.

- **The acceptance file**, `tests/test_improve_slot_line.py`. Read it whole: it is the authority for the line forms, the field names, the character lists and the bounds. By the brief writer's reading it holds 21 tests (the record-breaking test has 12 parameters); pytest's collection gives the real count. By reading, not by a run, all are expected red on the checkpoint except two controls, `test_r113_a_name_outside_the_list_is_not_written` and `test_r113_no_new_option`. Done step 2 records the real split. Its tests launch the program with `BRIDGE_RUN_ALLOW_ANY=1` and `BRIDGE_RUN_SLOT_SCALE`, in temporary launch folders, some of them git checkouts on a named branch (`feat/x`, `main`), and some plant a holder record directly (`HOLD_SRC`, limit 3) with extra fields.
- **The changed whole matches.** `tests/test_bridge_run_slot.py` lines 731 (a waiter's line ending `, limit 30s, project a`: the launch folder is named `a` and is no git checkout, so no branch), 847 (a planted record without the fields: `..., limit 3s`), and 910 to 913 (`_waiting_line` / `_slot_not_free_line` called on a dict with no `project` and no `branch` key, ending `, limit 10s`). `tests/test_hotfix24a_heavy_slots.py` line 48: `TAIL_RE = r", limit \d+s(?:, project [A-Za-z0-9._-]{1,64})?(?:, branch [A-Za-z0-9._/-]{1,100})?"`, appended to six whole matches (lines 309, 335, 355, 448, 491, 775), among them the folder lock's waiter (448) and the several-slot line (335 to 337).
- **`tests/test_loop_text_windowless.py`** (unchanged) line 153 checks that the program's source holds the substrings `waiting for the slot held by`, `slot taken`, `slot not free - held by` and `unknown`; keep each as one literal in the source. Line 155 checks that the loop's text holds `` `bridge-run: waiting for the slot held by <kind> <run id> since <start>, ends by <end>` ``, which stays a true prefix of the new line.
- **The reader**, `read_holder_record(holder_path)`, lines 2049 to 2107. It reads at most 4096 bytes, parses JSON, validates `kind`, `run_id` (`RUN_ID_RE`, line 154), `start`, `pid`, `limit` (`int`, 1 to `SLOT_LIMIT_MAX`), `created`, checks the process is alive with that creation time, returns None for anything that fails, and returns a newly built dict at line 2102: `{"kind": kind, "run_id": run_id, "pid": pid, "created": created_f, "start": start, "limit": limit}`. Extra keys are ignored today. `_plain_record_text` is at line 1944. A record the reader returns None for is shown as `held by unknown`.
- **The lines.** `holder_end_time(record, grace)` (line 2110) gives the `ends by` time. `_waiting_line(record, grace)` (line 2195), `_slot_not_free_line(record, grace)` (line 2205) and `_waiting_line_multi(num_slots, records, grace)` (line 2215, clauses joined by `"; "`, a None or endless record shown as `unknown`) build the three line forms. Each is called with a record from `read_holder_record`, or, in `tests/test_bridge_run_slot.py` line 906, with a plain dict that has no `project` or `branch` key. `_earliest_live_record` (line 2230) picks the record the several-slot `slot not free` line names, so that record must carry the fields too.
- **The writer.** `_publish_slot_taken(kind, run_id, limit, holder_path, taken_suffix="")` (line 2290) builds the record at lines 2298 to 2299 (`"limit": pub_limit`, `pub_limit = max(1, int(limit))`), publishes it with `publish_holder_record` (line 2122, JSON through a temporary file and `os.replace`) and returns `(taken, record)`. Its callers: `_acquire_heavy_slot_one` (line 2337), reached only through `acquire_heavy_slot(kind, run_id, limit, scale)` (line 2385), and `acquire_heavy_for_launch(kind, run_id, limit, scale, argv, folder, num_slots)` (line 2502), which then publishes the same record as the folder lock's holder record (lines 2503 to 2504). `acquire_heavy_slot` is called by tests with four positional arguments (`tests/test_bridge_run_slot.py` line 251, `tests/test_bug029_agent_name.py` line 126); it must stay callable that way. `acquire_heavy_for_launch` is called only from `main`, at line 3655.
- **The launch folder and the branch in `main`.** `main` (line 3376) sets `folder = os.getcwd()` at line 3378. Line 3607: `log_branch = brief_meta.get("branch") if brief_meta else branch_of(workspace_of(cmd, folder))`; line 3608 writes it into the run row as `"branch": log_branch`. `log_branch` may be None (no checkout, or git failed). `branch_of` is at line 2578. The slot is taken at lines 3653 to 3662, after `log_branch` is computed.
- **The docstring and the usage text.** The module docstring's Heavy runs bullet (lines 82 to 94) says the launcher "prints who holds a busy slot once a minute" and names `bridge-run: slot not free - ...`; by the brief writer's reading it does not spell the waiting line's form, so it is not changed (Requirement 7). The usage text names the options `--limit`, `--kind`, `--strip`, `--key-file`, `--healthy`; `test_r113_no_new_option` holds that set.
- **Trust boundary and security level.** The holder record lives under the user's `~/.cursor-bridge/`, where any process of the same user can write it, so its reader treats it as untrusted input: whatever passes the reader is printed on stderr, which the supervisor's loop reads. That is why both new fields are held to a character list (no path separator but the branch's `/`, no space, no control character, ASCII only) and a length bound, and why `project` is a name and never a path (a path would carry the owner's user name). The project's ASVS level is 2 (`docs/INVENTORY.md`). Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.
- **A pitfall.** In Python's `re`, `$` also matches before one trailing newline, so `re.match(r"^[...]{1,100}$", "main\n")` succeeds. The acceptance cases include a value with a newline inside it; a value ending in a newline must be refused as well.
- **Development data** (`docs/INVENTORY.md`): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". What this means for you: never run `bridge/cursor-bridge/bridge-run.py` yourself against this repository. Every launcher run is a test's, inside its own temporary launch folder and home folder.
- This increment talks to no external service and changes no Claude Code host behaviour. No value in it is the owner's (rule 52): the bounds and character lists are the design's (C51), fixed by the acceptance file.

## Diagrams
None: the plan names no diagram for this increment.

## Requirements
1. **The record's two fields.** The holder record a heavy run publishes (the slot's record and the folder lock's record, which is the same record) holds, beside its existing keys and its `limit`, `project` and `branch` as JSON strings. A field whose value would break Requirement 4's rule is not written: the record goes without that field and is still published. A record is never refused or left unpublished because of these fields.
2. **`project`.** Where the launch folder (`folder` in `main`) is named `Workspace`, `project` is its parent folder's name; otherwise it is the launch folder's own name. It is a name, written with its case as it stands, never a path and never lowered or uppered. Examples from the acceptance file: launch folder `<tmp>/proj-x/Workspace` gives `proj-x`; `<tmp>/plain-folder` gives `plain-folder`; `<tmp>/my proj/Workspace` gives no `project` (a space is outside the list). No path of the computer appears anywhere in the record's text.
3. **`branch`.** `branch` is the run's branch, the same value the run's row records as `branch` (`log_branch` in `main`). Where that value is None or breaks Requirement 4's rule, the record has no `branch`.
4. **The reader's rule.** `read_holder_record` accepts `project` only as a string of 1 to 64 characters, each one of `A-Z a-z 0-9 . _ -`, and `branch` only as a string of 1 to 100 characters, each one of `A-Z a-z 0-9 . _ / -`. A record in which either field is present and breaks its rule (any other type, `null` included, an empty string, a longer string, a character outside the list, a non-ASCII letter such as U+00E9, a newline anywhere) is no live record: the reader returns None, exactly as for a malformed record today, so the waiter's lines say `held by unknown`. A record that passes returns its `project` and `branch` in the dict the reader returns. The writer of Requirement 1 uses the same rule, so every record it writes reads back live.
5. **An older record.** A record without either field, as the released 2026.11.23a writes it, is read as today, and its lines name its limit and nothing more. A record with only one of the two fields names only that one.
6. **The lines.** Every line that names a holder (the one-slot waiting line `bridge-run: waiting for the slot held by ...`, the line printed at the bound `bridge-run: slot not free - held by ...`, and each holder's clause of the several-slot line `bridge-run: waiting for a slot (<n> of <n> held): ...`) reads exactly as on the checkpoint and then goes on with `, limit <seconds>s` (the record's `limit`, a whole number), then `, project <name>` where the record holds `project`, then `, branch <branch>` where it holds `branch`. Example from the acceptance file, with `SLOT_GRACE` 120: `bridge-run: slot not free - held by test 2026-01-01T00:00:00Z since 2026-01-01T00:00:00Z, ends by 2026-01-01T00:02:10Z, limit 10s, project proj, branch main`. This holds at the first waiting line, at each repeat, and for the folder lock's waiter. The `unknown` forms (`held by unknown`, an `unknown` clause) are unchanged. The functions work on a record given as a plain dict without the two keys (`tests/test_bridge_run_slot.py` line 906).
7. **Nothing else changes.** No option is added, removed or renamed; no queue, no priority. The wait bound, the report interval, `holder_end_time` and the `ends by` time are computed as today. `acquire_heavy_slot(kind, run_id, limit, scale)` stays callable with its four positional arguments. No new environment name (every `BRIDGE_\w+` in the source stays `BRIDGE_RUN_ALLOW_ANY` or `BRIDGE_RUN_SLOT_SCALE`), no dependency and no new import beyond the standard library modules the file already imports. The run row is unchanged. The usage text is unchanged. The module docstring is unchanged, because by reading it does not spell the line's form; if you find that it does spell it, state the new tail there instead and say so in the report. `bridge-run.py` stays ASCII, and the four literal substrings of Context (`tests/test_loop_text_windowless.py` line 153) stay in it.

## Acceptance criteria
- [ ] Every test of `tests/test_improve_slot_line.py` passes, the file unedited. Its module docstring names R-113.
- [ ] Every test of `tests/test_bridge_run_slot.py`, `tests/test_hotfix24a_heavy_slots.py`, `tests/test_loop_text_windowless.py` and `tests/test_tests_windowless.py` passes, or is skipped by its own condition, each file unedited.
- [ ] Every test of `tests/test_bridge_run.py`, `tests/test_bridge_run_driver.py`, `tests/test_program_launcher_forms.py` and `tests/test_improve_launcher_small.py` passes, or is skipped by its own condition, each file unedited. A test whose expectation the change alters is not edited: name it in the report by id, with its failure lines, as a changed expectation for the supervisor to review. A failure you did not cause is reported by test id, not fixed.
- [ ] `tests/test_program_review_rows.py::test_r079_the_launcher_tests_write_no_row_into_the_checkout` passes, the file unedited: every test file that names the launcher (this increment's included) passes in its one subprocess, and the checkout's real `run/launcher/runs.jsonl` and `run/launcher/pids/` are untouched.
- [ ] `python tools/dump-cli.py --check` passes after `python tools/dump-cli.py`. MANIFEST is regenerated after the last edit under `bridge/`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`. `bridge/cursor-bridge/VERSION` is unchanged and not listed by `git status --short`.
- [ ] Every requirement under "Satisfies" is fully met, with no stand-in, placeholder or "arrives in a later stage" text.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- Write the report as you go, so that nothing is lost if the run ends early.
- No secret is needed or used. Nothing you write (code, the notes line, the report) may hold a path of this computer or a user name. Write `<Workspace>`, `<tmp>` and `~` instead, also in quoted output.
- Do not edit any test file. If an acceptance test and this brief seem to disagree, stop and report it by its test id. Do not work around it.
- If the brief, the rules, or the tooling got in your way - an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason - append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service. Add no call to any service or to the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). You are not expected to add any process launch; the branch is the value `main` already has.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- No value in this increment is the owner's (rule 52).
- Follow existing conventions in the file you touch: ASCII program text, lines written to stderr starting `bridge-run: `, strict validation in the reader with None for anything untrusted, and the existing output line forms kept as the start of each new line.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The one exception is `git restore bridge/cursor-bridge/VERSION` in Done step 5.
- Numbers: the only number in the new text is the record's `limit`, already validated by the reader as an `int` from 1 to `SLOT_LIMIT_MAX` seconds; it is written as that integer, never parsed from a string.
- **A probe runs only as a test.** Run no Python other than the Done section's commands: no script of your own, no here-document, and no `python -c` other than step 9's. Where you need a scratch check, write it as a test file under `tests/` named `test_task091_scratch_*.py`, run it with `python -m pytest -p no:cacheprovider -q <that file>`, and delete it. Such a file must not name the launcher's file name in any form the guard test matches (its pattern is `bridge[-_]run`, which also matches `bridge_run`), or the guard test would pick it up. None may stay in the diff. The report names each one, what it showed, and that it was deleted.
- Run the tests directly, with `python -m pytest -p no:cacheprovider -q` as Done lists, not through `bridge-run.py`. Run only the files Done names. **Do NOT run the whole `tests/` tree**: the whole suite is CI's run.
- **Mutation: name the code points, run nothing.** For each label below, the report gives the function and lines (as the file stands after your change) that the mutation would touch, and the test id you expect to catch it. Where no test of the files Done names would catch a mutation, say so for that label.
  - M1: the record is built without `project`.
  - M2: the record is built without `branch`.
  - M3: a full path is written as `project`.
  - M4: the reader does not bound `project`'s length.
  - M5: the reader accepts a character outside `branch`'s list.
  - M6: the tail is omitted from the not-free line.
  - M7: the tail is omitted from the several-slot line.
  - M8: a record without the two fields is refused as malformed.
  - M9: the project name is taken from the launch folder even where it is named `Workspace`.
- **Known failures.** The acceptance file and the changed whole matches are red on the checkpoint (Context). If any other test fails that your change did not cause, report it by test id with its failure lines, and fix none.
- Prefer reuse over new code - the existing helpers, the standard library - and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.

## Done
Your report is the file `handoff/TASK-091-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for Requirements 1 to 7, one line each naming the lines that meet it;
- the code points of M1 to M9;
- every changed expectation, or `no changed expectation`;
- for TASK-096: one line naming the loop's text that quotes the waiting line's form (`bridge/cursor-bridge/workflow/phases/delegation-loop.md`, and `tests/test_loop_text_windowless.py` line 155, which holds it), with the new tail it does not yet show; you edit neither;
- every scratch test file, or `no scratch test file`;
- a section headed exactly `Assumed, not verified`, which is the report's last section.

That last section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: whether a launch folder named `workspace` in another case counts as `Workspace`, what `project` is for a launch folder at a drive root, or what `branch` holds for a detached checkout. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change. Steps 1 and 2 come before your first edit. Steps 3 to 13 come after your last edit, in this order:
1. `git status --short`
2. `python -m pytest -p no:cacheprovider -q tests/test_improve_slot_line.py` (quote the summary line and the failing ids)
3. `python tools/dump-cli.py`, then `python tools/dump-cli.py --check` (it must pass)
4. `python tools/make-manifest.py`
5. `git status --short`. If `bridge/cursor-bridge/VERSION` is listed, run `git restore bridge/cursor-bridge/VERSION` and then `git status --short` again.
6. `python -m pytest -p no:cacheprovider -q tests/test_improve_slot_line.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run_slot.py tests/test_hotfix24a_heavy_slots.py tests/test_loop_text_windowless.py tests/test_tests_windowless.py`
8. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_program_launcher_forms.py tests/test_improve_launcher_small.py`
9. `python -c "open('bridge/cursor-bridge/bridge-run.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
10. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`), then `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. Write the report's results for steps 1 to 10 first. Then run the guard test once: `python -m pytest -p no:cacheprovider -q "tests/test_program_review_rows.py::test_r079_the_launcher_tests_write_no_row_into_the_checkout"`. It runs every test file that names the launcher in one subprocess and takes about 33 minutes; wait for it in the foreground. Quote its summary line. It reports `skipped` only where the checkout has no `run/` folder; say so if it does.
12. `git diff --stat HEAD`
13. `git rev-parse HEAD` and `git status --short`. Neither `bridge/cursor-bridge/VERSION` nor any `tests/test_task091_scratch_` file may be listed.

A failure in a file outside Scope is reported by test id, never fixed there.

Quote every command you ran in the report, verbatim in a fenced block, with the lines it printed. A count, or a claim that a check passed, quotes the output line that shows it. List each mutation code point by this brief's own label. Write a command you did not run as `not run`; never describe it as run. Run this brief's test commands (steps 6 to 8, and step 11) once more after your last edit if you edited after running them. Write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
