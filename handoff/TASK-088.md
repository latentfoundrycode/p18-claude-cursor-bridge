---
record: brief
header: 1
id: "TASK-088"
round: 1
satisfies: [R-110]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/plan-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_satisfies_reader.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-088-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-088: One reader for a brief's Satisfies ids

## Objective
A brief names the requirement rows it satisfies on its `Satisfies:` line, and its front-matter header repeats them as `satisfies: [...]`. Today `bridge/cursor-bridge/bridge_env.py` reads that line in two places, each its own way (`_brief_fallback_from_body` and `brief_satisfies`), both reading only the one line, and the header's agreement compares the header's list with that reading as ordered lists, repeats counting. So the launcher refuses a brief that lists its rows as bullets beneath the line, one that names a row twice, and one that names the same rows in another order; a `Satisfies: none` line followed by row ids is refused without the line or the remedy being named; and `plan-check.py` never names a brief whose header disagrees. This increment makes one function of `bridge_env.py` the only reader of a brief's `Satisfies` ids (the line and the bullet lines directly beneath it, each id once, plus a flag for a `none` that carries ids), has both readers call it, compares the header's list with it as sets, gives the launcher's two refusals their remedy text, and has `plan-check.py` print a `BRIEF` line for an unmerged brief whose header's `satisfies` disagrees with its prose or whose `none` carries ids. A build plan's own `Satisfies:` lines are not briefs and keep their one-line reading.

Satisfies: R-110

That row (its full text in `docs/REQUIREMENTS.md`) reads: a brief's `Satisfies` ids are read one way by every program; one reader in `bridge_env.py` returns the ids on the line and on the bullet lines directly beneath it, each id once; the launcher compares them with the header's list as sets and its refusal prints both lists and the remedy; a none followed by an id is refused by name; `plan-check.py` prints a `BRIEF` line for an unmerged brief whose header disagrees and for a none that carries ids. Its last clause (the packager's refactoring variant writing exactly the none form) is instruction text for a later increment, not yours. The row stays planned after this increment (until TASK-096); you change no record of it.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_satisfies_reader.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-088-r1-report.md

Do not modify anything else.

Limits on these paths: `tests/test_improve_satisfies_reader.py` is the supervisor's acceptance file, written before this brief: read it whole and run it, **do not edit it**. `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`, and `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` only by running `python tools/dump-cli.py` (Done), never by hand. `docs/BUILDER_NOTES.md`: new dated lines at its end only. In `bridge_env.py`, `bridge-run.py` and `plan-check.py`, change only what the Requirements need.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names (`docs/REQUIREMENTS.md`, `docs/HARDENING.md`, `docs/PROJECT_STATUS.md` are the supervisor's records)
- `bridge/cursor-bridge/review-guard.py` (it calls `brief_header_refusal` and is not edited; its answers must stand, Requirement 6), `bridge/cursor-bridge/records-migrate.py`, every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/`, `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/VERSION` (must come out unchanged)
- every test file; `tools/make-manifest.py` and `tools/dump-cli.py` (you run them, you edit neither)
- every brief under `handoff/` other than your report, even one the new reading would read differently (report it, Constraints)
- `plan_collect_satisfies_ids`, `plan_r_ids_outside_headers`, `walk_plan_prose_body` and `FIELD_RX` in `bridge_env.py`: a plan's reading stays as it is
- every option of every program: none is added, removed or renamed

## Context
- **The two readers today** (`bridge/cursor-bridge/bridge_env.py`, line numbers as on the checkpoint `0823019`):
  - `FIELD_RX` (lines 432 to 435) matches `Kind|Parent|Depends on|Parallel|Satisfies|Diagrams|Scope|Deferred` at a line's start, an optional `- ` or `* ` bullet before it, case-insensitive; `_PLAN_R_RX = re.compile(r"\bR-\d{3,}\b")` (line 439).
  - `_brief_fallback_from_body(body, brief_name)` (lines 574 to 594) builds the prose fallback `{"name", "satisfies", "scope", "merge_unit", "blocking_class"}`; its `satisfies` is `_PLAN_R_RX.findall(...)` on the value of the first line `FIELD_RX` matches as `Satisfies`, nothing beneath it.
  - `brief_satisfies(text)` (lines 3548 to 3558), docstring "R-ids named on the brief's Satisfies: line, in order; empty when there is no line.": reads the record with `read_brief_record(text, "")`, returns `[]` on a refusal, reads the body of a headed brief or the whole text of a header-less one, and repeats the same one-line reading.
  - `read_brief_record(text, brief_name)` (lines 614 to 631) returns `BriefRecord(header, body, refusal, fallback, disagrees)`; for a headed brief `disagrees = header_agrees("brief", header, fallback)`; a header-less brief gets `disagrees = []`.
  - `header_agrees(kind, header, fallback)`, the `kind == "brief"` branch (lines 2670 to 2702): for `satisfies`, `scope`, `merge_unit`, `blocking_class` it appends the key when `hv != fv` (line 2700), so for `satisfies` order and repeats count today. Only `satisfies` changes to a set comparison; `scope`, `merge_unit`, `blocking_class`, `id` and `round` compare as today.
  - `brief_header_refusal(text, shown_path, keys=None)` (lines 3693 to 3709): returns the malformed or schema refusal line, `None` for a header-less brief, else `"header: disagrees %s" % disagrees[0]` for the first disagreeing key in `keys` (all keys when `keys` is None), else `None`.
  - `brief_prose_fallback` (ending at line 3690) and the other callers of `read_brief_record` (lines 841, 997, 1032, 1083, 3817, 3823, 3833) read scope, merge unit and blocking class; they inherit the new reading through the fallback.
  - `plan_collect_satisfies_ids(body)` (lines 3724 to 3735) and `plan_r_ids_outside_headers(text)` (from line 3561) read a plan; they stay as they are.
- **The launcher** (`bridge/cursor-bridge/bridge-run.py`): `_ascii_refusal(msg)` (line 1434) is `msg.encode("ascii", "backslashreplace").decode("ascii")`. In `builder_review_refusal`, lines 1489 to 1508: `brief_text = bridge_env.decode_record_bytes(brief_bytes)`; `brief_shown = "handoff/<name>.md"`; the first call `bridge_env.brief_header_refusal(brief_text, brief_shown, keys=("id", "round", "satisfies", "scope"))`, then the one-side merge-unit check, then the second call `bridge_env.brief_header_refusal(brief_text, brief_shown)`; each non-empty answer is returned as `_ascii_refusal(header_reason)`, which the launcher prints on one stderr line as `bridge-run: refused - <reason>`, exit 125, nothing started.
- **The review guard** (`bridge/cursor-bridge/review-guard.py`, lines 826 to 830, outside Scope): `bridge_env.brief_header_refusal(brief_text, shown, keys=("merge_unit", "id", "round"))`, printed as `review-guard: refused - <reason>`. `tests/test_header_plan.py` line 619 asserts `out.startswith("review-guard: refused - header: disagrees %s" % key)`.
- **plan-check** (`bridge/cursor-bridge/plan-check.py`): `brief_findings(path, item)` (lines 136 to 163) returns the malformed-header line (`bridge_env.brief_malformed_brief_line`), Scope paths outside the increment's Scope, and the increment's rows the brief does not name; it reports no header disagreement today. The loop at lines 377 to 384 calls it only for a brief whose increment is in the plan, not merged, and of kind increment, and prints each finding as `BRIEF: <path> <finding>`, each such line a failure (exit 1). `plan-check.py` holds two non-ASCII characters today; leave them.
- **Other readers of the changed functions**: `records-migrate.py` line 541 calls `header_agrees(kind, header, fb)` and so compares a brief's `satisfies` as sets after your change (intended; not edited). `tests/test_program_own_records.py` reads every headed record of this repository, every brief under `handoff/` among them, through `read_brief_record` and asserts none disagrees. Thirty merged briefs (BUG-002, BUG-003, BUG-010, TASK-006, TASK-008, TASK-015 and its rounds r2 to r7, TASK-016, TASK-024 and r2, TASK-029-r4, TASK-031 and its rounds r2 to r14) list their rows as bullets beneath a bare `Satisfies:` line; the supervisor's checkpoint commit set their headers' `satisfies` to those rows, so on the checkpoint that test fails for those thirty briefs (the old one-line reading gives `[]`) and passes once the new reader reads the bullets. If the new reading makes any other brief disagree with its header, that test shows it; report the brief, edit none.
- **The design** (`docs/DESIGN.md`, "Change: the improvements release", C29 with T96): "One reader in `bridge_env` returns a brief's `Satisfies` ids from its line and from the bullet lines directly beneath it, each id once; the launcher's comparison with the header and the brief's own readers use it, comparing as sets. `Satisfies: none` followed by an id is a finding of its own [...] The launcher's refusal prints both lists and the remedy, and `plan-check.py` prints a `BRIEF` line for an unmerged brief whose header disagrees and for a `none` that carries ids. A plan's own `Satisfies:` stays one line." Its table, one acceptance test a row (Requirements 4):

  | The brief's prose | The header's `satisfies` | Read as | Answer |
  |---|---|---|---|
  | `Satisfies: R-077, R-078` | `[R-077, R-078]` | R-077, R-078 | launched |
  | `Satisfies:` with `- R-077` and `- R-078` beneath | `[R-077, R-078]` | R-077, R-078 | launched (refused today) |
  | `Satisfies: R-077, R-077` | `[R-077]` | R-077 | launched (refused today) |
  | `Satisfies: R-078, R-077` | `[R-077, R-078]` | the same set | launched (refused today) |
  | `Satisfies: none` | `[]` | none | launched |
  | `Satisfies: none (R-105 ...)` | `[]` | a `none` that carries ids | refused, the line and the remedy named (refused today without them) |
  | `Satisfies: R-077` | `[R-078]` | differ | refused, both lists printed |

- **The acceptance tests**, `tests/test_improve_satisfies_reader.py`, 21 tests. They launch `bridge-run.py` on a scratch Workspace with the stand-in for cursor-agent from `tests/test_task032_supervisor_launcher.py` (`Lab`, `launch`, `build`, `assert_ran`, `assert_refused`: a refusal is exit 125 and the first stderr line beginning with the prefix, so the whole refusal text, remedy included, must be on that one line), run plan-check on the scratch plan of `tests/test_plan_check.py` (`make`, `run`; its increment TASK-003 is unmerged and satisfies R-003 and R-004), and run the review guard on the scratch repository of `tests/test_header_plan.py` (`brief_header`, `brief_prose`, `guard_repo`, `run`, `GUARD`). Run on the checkpoint `0823019` (2026-11-26): 15 failed, 6 passed.
  - red: `test_task088_the_reader_reads_the_line_and_the_bullets_directly_beneath`
  - red: `test_task088_the_reader_names_each_id_once_in_first_seen_order`
  - red: `test_task088_the_reader_flags_a_none_that_carries_ids[none]`, `[none-carries-an-id-on-the-line]`, `[none-carries-an-id-beneath]`
  - red: `test_task088_the_briefs_two_readers_call_the_one_reader` (monkeypatches `bridge_env.brief_satisfies_ids` and expects `brief_satisfies` and `read_brief_record(...).fallback["satisfies"]` to answer what it answers)
  - red: `test_task088_brief_satisfies_reads_the_bullets`
  - red: `test_task088_row2_bullets_beneath_the_line_are_launched`, `test_task088_row3_a_repeated_id_is_launched`, `test_task088_row4_the_same_set_in_another_order_is_launched`, `test_task088_row6_a_none_that_carries_ids_is_refused_with_the_remedy`, `test_task088_row7_a_disagreeing_list_is_refused_with_both_lists`
  - red: `test_task088_a_none_with_a_non_ascii_line_is_refused_in_ascii` (its fixture line holds an em dash, U+2014)
  - red: `test_task088_plan_check_names_an_unmerged_brief_whose_header_disagrees`, `test_task088_plan_check_names_an_unmerged_brief_whose_none_carries_ids`
  - holds: `test_task088_row1_a_line_of_two_ids_beside_the_same_header_is_launched`, `test_task088_row5_none_beside_an_empty_header_is_launched`, `test_task088_a_brief_with_no_header_keeps_its_reading_and_no_check_at_launch`, `test_task088_plan_check_passes_an_agreeing_brief_with_bullets`, `test_task088_the_review_guard_answers_as_on_the_checkpoint`, `test_task088_a_plans_satisfies_line_is_read_as_on_the_checkpoint`
- **Trust boundary and security level.** A brief is text a builder or a reviewer can write (KP-078): the reader treats it as untrusted input, every existing refusal of the launcher, the guard and plan-check stays, and text quoted from the brief into a refusal is printed in ASCII. The project's ASVS level is 2 (`docs/INVENTORY.md`). Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.
- **Development data** (`docs/INVENTORY.md`): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: never run `bridge-run.py`, `plan-check.py` or `review-guard.py` from `bridge/` against this repository; only the tests run them, on their scratch repositories.
- This increment talks to no external service and touches no Claude Code host behaviour.

## Diagrams
None: the plan names no diagram for this increment.

## Requirements
1. **The one reader.** `bridge_env.brief_satisfies_ids(body)` returns a tuple `(ids, none_carries_ids)`. `ids`: the R-ids (as `_PLAN_R_RX` matches them) on the brief's `Satisfies:` line (the first line `FIELD_RX` matches as `Satisfies`, as today) and on the bullet lines (`-` or `*`) directly beneath it, reading down to the first line that is neither a bullet nor blank; blank lines between bullets do not end it; each id once, in first-seen order; empty where there is no line. `none_carries_ids`: True where the line's value has `none` as its first word and an R-id follows on the line or on the bullets beneath it; False otherwise (`Satisfies: none` alone gives `([], False)`).
2. **No second copy.** `brief_satisfies` and `_brief_fallback_from_body` get their ids by calling `brief_satisfies_ids`, looked up through the module at call time (the acceptance test monkeypatches `bridge_env.brief_satisfies_ids`), and no other code of `bridge_env.py` reads a brief's `Satisfies` line. `brief_satisfies` keeps its signature, still returns `[]` for a refused record, and reads the body of a headed brief or the whole text of a header-less one, as today; its docstring says it reads the line and the bullets beneath it.
3. **Sets.** The brief header's agreement for `satisfies` compares the header's list and the reader's ids as sets; every other key of the brief branch compares as today.
4. **The design's seven rows** answer as the table says, at the launcher, each by its acceptance test (rows 1 to 7).
5. **The launcher's two refusals**, both returned through `_ascii_refusal`, each on one line:
   - a headed brief whose `satisfies` disagrees as sets: the line still begins `bridge-run: refused - header: disagrees satisfies`, then names both lists (the header's and the prose's) and says that the header and the prose name the same rows (the acceptance test looks for the words `the header and the prose name the same rows`);
   - a headed brief whose `none` carries ids: refused, whatever its header's list, with words that include `a brief that satisfies no row reads exactly` and `Satisfies: none`, and the brief's line named; where its header's list also disagrees, this refusal is the one printed.
   Where the text is composed is yours (one place in `bridge_env.py` that both launcher calls get it from is expected), so long as Requirement 6 holds.
6. **What stands.** `brief_header_refusal` called with `keys` that do not include `satisfies` answers every brief as on the checkpoint: the review guard's answers on `merge_unit`, `id` and `round` stand, and a disagreement on `satisfies` or a `none` that carries ids is no refusal of the guard's. Every other refusal of the launcher, its order and its wording stand. A header-less brief is read through the same reader and gets no header check and no `none` refusal at launch, as on the checkpoint. A plan's `Satisfies:` lines are read as on the checkpoint (`plan_collect_satisfies_ids` unchanged).
7. **plan-check's `BRIEF` lines.** For an unmerged headed brief (the briefs `brief_findings` reads today) `plan-check.py` prints a `BRIEF: <path> ...` line, counted as a failure (exit 1), where the header's `satisfies` disagrees with the reader's ids as sets (the line names `satisfies` and both lists), and one where its `none` carries ids (the line contains `Satisfies: none` and the remedy). An agreeing brief, bullets or not, gives no such line. Brief text quoted into a new line is printed in ASCII form. Every existing finding of `brief_findings` stands; a header-less brief's answer is as on the checkpoint.
8. **Nothing else changes**: no option added or removed, no new dependency, no new import outside the standard library already imported; the text you add to `bridge_env.py` and `bridge-run.py` is ASCII (both files are ASCII today and stay so). If a module docstring that `tools/dump-cli.py` quotes changes, the command reference is regenerated (Done).

## Acceptance criteria
- [ ] All 21 tests of `tests/test_improve_satisfies_reader.py` pass, the file unedited (R-110: its module docstring names the row).
- [ ] Every test of `tests/test_header_plan.py`, `tests/test_header_plan_r2.py`, `tests/test_plan_check.py`, `tests/test_program_merge_unit_one.py` and `tests/test_task032_supervisor_launcher.py` passes, or skips by its own condition, each unedited.
- [ ] The other test files that read the changed functions (Done, step 7, and those your search adds) pass, each unedited; a failure you did not cause, or an existing brief under `handoff/` that the new reading makes disagree, is reported by test id and path, not fixed.
- [ ] `brief_satisfies_ids` is the only code of `bridge_env.py` that reads a brief's `Satisfies` line (named in the report with its lines, and the two callers with theirs).
- [ ] The header's `satisfies` agreement compares sets; `scope`, `merge_unit`, `blocking_class`, `id`, `round` compare as on the checkpoint.
- [ ] `python tools/dump-cli.py --check` passes after `python tools/dump-cli.py`; MANIFEST regenerated; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `bridge/cursor-bridge/VERSION` unchanged and not listed by `git status --short`.
- [ ] Every requirement under "Satisfies" is fully met for this increment's part - no stand-in, placeholder or "arrives in a later stage" text.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- Write the report as you go, so that nothing is lost if the run ends early.
- No secret is needed or used. Nothing you write (code, the notes line, the report) holds a path of this computer or a user name: write `<Workspace>`, `<tmp>` and `~` instead, also in quoted output.
- Do not edit any test file. If an acceptance test and this brief seem to disagree, stop and report it by its test id; do not work around it.
- If the brief, the rules, or the tooling got in your way - an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason - append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service; add no call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms); you are not expected to add any process launch.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end; leave nothing running.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- No value in this increment is the owner's (rule 52).
- Follow existing conventions in the files you touch: ASCII program text in `bridge_env.py` and `bridge-run.py`, refusal tokens returned as strings, the existing output line forms kept.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only. The one exception is `git restore bridge/cursor-bridge/VERSION` in Done, step 5.
- Numbers: no number is read from text in this increment; R-ids are matched by `_PLAN_R_RX`, never sliced out of a string by position.
- **A probe runs only as a test.** Run no Python other than the Done section's commands: no script of your own, no here-document, no `python -c` but step 10's. Where you need a scratch check, write it as a test file under `tests/` named `test_task088_scratch_*.py`, run it with `python -m pytest -p no:cacheprovider -q <that file>`, and delete it; none stays in the diff, and the report names each one, what it showed and that it was deleted.
- Run the tests with `python -m pytest` directly as Done lists, not through `bridge-run.py` (the stripped run through the launcher is the supervisor's step 4), and only the files Done names or your search adds. **Do NOT run the whole `tests/` tree**: the whole suite is CI's run.
- **Mutation: name the code points, run nothing.** The report lists, for each label, the function and lines (as the file stands after your change) a mutation would touch and the test id you expect to catch it: M1 the bullets beneath the line not read; M2 a blank line ending the bullets; M3 a non-bullet line not ending them; M4 the repeat removal dropped; M5 the set comparison turned back into a list comparison; M6 the `none` flag never set; M7 the launcher's `none` refusal removed; M8 the both-lists text removed from the disagreement refusal; M9 `_ascii_refusal` dropped from either launcher call; M10 plan-check's disagreement line removed; M11 plan-check's `none` line removed; M12 the `none` refusal reaching a call whose keys omit `satisfies`.
- **Known failures.** The acceptance file is red on the checkpoint (15 failed, 6 passed). If any other test fails that your change did not cause, report it by test id with its failure lines and fix none.
- Prefer reuse over new code - the existing helpers, the standard library - and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.

## Done
Your report is the file `handoff/TASK-088-r1-report.md`, which you write as you go - what you did, what you changed, what you ran and what it printed, what you could not do - so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, for Requirements 1 to 8 one line each naming the functions and lines that meet it, the code points of M1 to M12, the test files your search added and the search you ran, every scratch test file (or `no scratch test file`), and a section headed exactly `Assumed, not verified`, the report's last section: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm - for example how you matched `none` (case, punctuation after it), what a bullet holding no R-id does, a header-less brief at plan-check. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change. Steps 1 and 2 before your first edit; steps 3 to 12 after your last edit, in this order:
1. `git status --short`
2. `python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py` (expect 15 failed, 6 passed; quote the summary line and the failing ids)
3. `python tools/dump-cli.py` then `python tools/dump-cli.py --check` (it must pass)
4. `python tools/make-manifest.py`
5. `git status --short` (if `bridge/cursor-bridge/VERSION` is listed, run `git restore bridge/cursor-bridge/VERSION` and `git status --short` again)
6. `python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_plan_check.py tests/test_program_merge_unit_one.py tests/test_task032_supervisor_launcher.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_bug044.py tests/test_release_b2_text.py tests/test_program_own_records.py tests/test_records_migrate.py tests/test_header_reader.py tests/test_header_plan_r3.py tests/test_header_run_parameters.py tests/test_release_s_plan_size.py tests/test_plan_demonstration.py tests/test_dump_cli.py`; then search `tests/` for further files that call or run `brief_satisfies`, `brief_satisfies_ids`, `read_brief_record`, `header_agrees`, `brief_header_refusal`, `brief_prose_fallback`, `plan-check.py` or the launcher's brief rules (for example a content search for `brief_satisfies|read_brief_record|header_agrees|brief_header_refusal|brief_prose_fallback|plan-check`), and run the files it finds that steps 6 and 7 do not name in one more command of the same form, quoted in the report
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
10. `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge_env.py','bridge/cursor-bridge/bridge-run.py')]; print('ascii ok')"` (expect `ascii ok`)
11. `git diff --stat HEAD`
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed, nor any `tests/test_task088_scratch_` file)

A failure in a file outside Scope is reported by test id, never fixed there.

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. Each mutation code point is listed by this brief's own label. A command you did not run is written `not run`, never described as run. Run this brief's test commands once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
