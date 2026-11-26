---
record: brief
header: 1
id: "TASK-087d"
round: 1
satisfies: [R-107]
scope: ["bridge/cursor-bridge/roster-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_review_alt_profile.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-087d-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-087d: `--review-alt` acts on the profile the resolve picks

## Objective
`roster-check.py --review-alt <reason>` resolves a profile's alternate reviewer (`review_b_alt`) on request, for a provider's safety refusal of Review B. Today it reads the wrong profile: inside `main()` of `bridge/cursor-bridge/roster-check.py`, the helper `_profile_in_use` (lines 1218 to 1242, used at lines 1244 to 1255) takes the first profile whose builder is usable and does not apply the main resolve loop's skip of a profile whose `review_b` is excluded by its pool or a mark with no independent usable alternate (lines 1327 to 1374), nor the loop's reading of probe answers (lines 1376 to 1409). So with the other pool exhausted, `python bridge/cursor-bridge/roster-check.py docs/ROSTER.json --no-probe --review-alt safety-refusal` exits 1 with `FAIL  --review-alt refused: no review_b_alt named in profile 'full'`, while the plain resolve picks the native profile, which names `composer-2.5` as its alternate (recorded in `docs/HARDENING.md`, TASK-087c's section, "`--review-alt` reads the wrong profile"). This increment makes the request act on exactly the profile the resolve without the request picks, by one reading of "which profile is in use" that both paths call, and corrects the module docstring's roster example, which shows `review_b_alt` in the full profile although the policy's template and `docs/ROSTER.json` name it in the native profile alone (stage I1's review, round 1, should fix 1).

Satisfies: R-107

That row is the roster's alternate reviewer (its full text in `docs/REQUIREMENTS.md`); it stays planned after this increment, until a later design revision, so you change no record of it.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_review_alt_profile.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-087d-r1-report.md

Do not modify anything else.

Limits on these paths: `tests/test_improve_review_alt_profile.py` is the supervisor's acceptance file, committed before the checkpoint: read it whole and run it, **do not edit it**. `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`, and `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` only by running `python tools/dump-cli.py` (Done), never by hand; `roster-check.py` has no argument parser, so `tools/dump-cli.py` quotes its module docstring, and the docstring you change is what these two files carry. `docs/BUILDER_NOTES.md`: new dated lines at its end only. In `roster-check.py`, change only what the profile `--review-alt` acts on needs, and the module docstring (Requirements 5 and 6).

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names
- `bridge/cursor-bridge/bridge-run.py`, `bridge/cursor-bridge/bridge_env.py`, every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/`, `bridge/cursor-bridge/workflow/`, `bridge/cursor-bridge/Merge-Verification-Policy.md`, `bridge/cursor-bridge/VERSION` (reads `2026.11.24a` and must come out unchanged), `docs/ROSTER.json`, `docs/ROSTER.resolved.json`
- every test file; `tools/make-manifest.py` and `tools/dump-cli.py` (you run them, you edit neither)
- the `--record-failure`, `--record-success`, `--mark-exhausted`, `--mark-reset`, `--clear-unavailable` and `--repair-record` modes, the built-set reading (`built_families`, `built_by`), the state file's format, `probe` and its judgement of one reply, and every output line form the existing tests read

## Context
- **The program.** `bridge/cursor-bridge/roster-check.py`, `main()` from line 1108: `--review-alt` reason parsed at lines 1111 to 1119 (exit 2 on a malformed reason); the built set read at line 1141; a set that cannot be read refused at lines 1154 to 1157 and an unknown set refused for the request at lines 1159 to 1163, both before any profile is read (keep both, in that place and order). Helpers inside `main()`: `_probe_roles(roles)` (line 1197, returns `(usable, sign_in)`, printing the probe lines and `SIGN_IN_LINE`), `_alt_pool_ok` (1210), `_r_excluded` (1215), `_profile_in_use` (1218), `_rebuild_entry` (1177). The request path is lines 1244 to 1299; the plain resolve loop is lines 1304 to 1421; the resolved-file write, `--command` check and RESOLVED line follow (1422 to 1465). Module-level helpers used: `norm_entry`, `family_of`, `pool_of`, `_alt_independent`, `probe`, `PROBE_SIGN_IN`, `SIGN_IN_LINE`, `stamp`, `now_utc`.
- **The resolve loop's skips, in its order** (lines 1316 to 1409), which name the profile in use: a family that cannot be named; the builder's pool exhausted; a mark on the builder; a family collision among builder, Review A and `review_b`; `review_b` excluded by its pool or a mark with no independent usable alternate (and, on a known or empty set, `review_b` itself marked); with probes, a model that did not answer as the loop reads the answer (the builder probed first, then `review_b` where no mark or pool excludes it, then the alternate where a deviation would resolve it, every probe planned for the profile made before a builder that did not answer skips it, each model probed once, a sign-in from any probe ending the run with exit 5 at once). Round 2 of TASK-086a broke `tests/test_program_roster_sign_in.py` by stopping a profile's probes once its builder did not answer (`docs/HARDENING.md`, TASK-086a, round 2's reviews): keep every planned probe.
- **Held refactoring candidates** (`docs/HARDENING.md`, Stage I1's refactoring pass, "Held"): 9, two inline probe blocks repeating `_probe_roles` (lines 1233 to 1241 in `_profile_in_use`, and 1281 to 1290 for the alternate under the request); 12, `_profile_in_use` repeating the loop's builder-side skips. They go only where the one reading removes them; refactor nothing else.
- **The roster as resolved today**: builder `composer-2.5`, the native profile, the other pool exhausted until 2026-12-16. `docs/ROSTER.json` reads: full `builder grok-4.7-medium, review_b gpt-5.6-sol-high` (no alternate); native `builder composer-2.5, review_b grok-4.7-medium, review_b_alt composer-2.5`. The policy's template (`bridge/cursor-bridge/Merge-Verification-Policy.md`, lines 146 and 147) holds full `grok-4.7-high / gpt-5.6-sol-high` with no alternate and native `composer-2.5 / grok-4.7-high` with `"review_b_alt": "composer-2.5"`.
- **The design's rows for the request** (`docs/DESIGN.md`, C39 table, lines 609 and 610): "known, on `--review-alt <reason>` | refused by its provider (T103) | independent and usable | the alternate, with `deviation` (the reason given)"; "known or unknown, on `--review-alt <reason>` | - | none, or not independent, or not usable, or the set unknown | exit 1, the cause named".
- **Trust boundary and security level.** The roster file, the state file under the git common folder and the run record `run/launcher/runs.jsonl` are inputs a builder or reviewer can write (KP-078): every refusal below is kept. The project's ASVS level is 2 (`docs/INVENTORY.md`). Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.
- **Development data** (`docs/INVENTORY.md`): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: never run `roster-check.py` in this repository; only the tests run it, on their scratch repositories.
- **The acceptance tests**, `tests/test_improve_review_alt_profile.py`, 11 tests, importing helpers from `tests/test_improve_roster_alt.py` (`scratch_repo`, `write_roster`, `resolve` with `--no-probe`, `assert_deviation`, `_main_in_process`, `fail_text`, `plant_resolved`, ...) and constants from `tests/roster_rows.py` (`FULL`, `NATIVE`, `COMPOSER`, `GPT`, `GROK_B`, `GROK_R`). On the checkpoint 8 fail, each by the full-profile refusal or the docstring, and 3 pass, holding what stands:
  - red: `test_task087d_an_exhausted_pool_the_request_acts_on_the_native_profile` (exactly one DEVIATION line, `DEVIATION  review_b is composer-2.5 on request (safety-refusal)`, the native profile written)
  - red: `test_task087d_the_plain_resolve_and_the_request_name_the_same_profile`
  - red: `test_task087d_a_marked_review_b_skips_the_profile_for_the_request_too`
  - red: `test_task087d_after_a_grok_build_the_request_records_the_built_family`
  - red: `test_task087d_after_a_composer_build_the_request_is_refused_by_the_family_cause`
  - red: `test_task087d_a_review_b_that_did_not_answer_skips_the_profile_for_the_request_too` (the skipped full profile's builder and Review B probed once each)
  - red: `test_task087d_this_repositorys_roster_resolves_the_native_alternate_on_request`
  - red: `test_task087d_the_docstrings_roster_example_names_no_alternate_in_the_full_profile`
  - holds: `test_task087d_with_the_pool_available_the_request_stays_on_the_full_profile`
  - holds: `test_task087d_a_full_profile_that_names_an_alternate_keeps_it_on_request`
  - holds: `test_task087d_a_sign_in_ends_the_request_with_exit_5`
- **Tests that must pass unedited**: every test of `tests/test_improve_roster_alt.py` (among them `test_task086a_review_alt_acts_on_the_profile_in_use_alone`, line 1363: with the pool available the request acts on the full profile and never passes to a later one; and the refusal tests at lines 704 to 755 and 1337 to 1466), `tests/test_improve_roster_launch.py` and `tests/test_program_roster_sign_in.py`; and the other tests that run or read the program (Done, step 7).
- No `claude --version` is relevant: the increment touches no Claude Code host behaviour. It talks to no external service; every probe in the tests is switched off or replaced in-process.

## Diagrams
None: the plan names no diagram for this increment.

## Requirements
1. **One reading of the profile in use.** `--review-alt <reason>` acts on the profile the resolve without the request picks, named by the same skips in the same order (Context, "The resolve loop's skips"), by one function the resolve loop calls too; no second copy of those skips stands (`_profile_in_use` as it is today does not survive).
2. **The request never passes to a later profile** than the one the resolve picks: where that profile names no alternate, or its alternate is refused, the request ends with exit 1 and the cause; where no profile is in use it ends with exit 1 and a cause, as today.
3. **Every refusal stands**, each with exit 1 (or the exit named), the cause on a `FAIL` line, no RESOLVED line, no DEVIATION line and the resolved file unchanged: the malformed reason (exit 2); the built set unknown; the built set that cannot be read; no alternate in the profile in use (`no review_b_alt named in profile '<name>'`); an alternate of Review A's family; of a family that built the branch; of an unknown family (`its family is unknown`); marked unavailable; in an exhausted pool; an alternate that did not answer its probe; a sign-in, exit 5. Keep the existing wording of each `FAIL` line.
4. **Probes.** With probes, each answer is read as the resolve reads it; a skipped profile's models are probed once each; no model is probed twice in one role in one run; a sign-in from any probe ends the run with SIGN-IN and exit 5, the resolved file unchanged.
5. **Output of a granted request**: one DEVIATION line, `DEVIATION  review_b is <alt> on request (<reason>)`, no other DEVIATION line and no REBUILD line; the resolved file holds the profile in use with `review_b` the alternate and the `deviation` entry `{review_b_alt, reason, branch, built}` as today (`built` the known set, sorted). The plain resolve's output and resolved file are unchanged in every case.
6. **The module docstring**: its roster example (lines 15 to 19) names `review_b_alt` in the native profile alone, as the policy's template does (the full profile with no alternate); the `--review-alt <reason>` paragraph (lines 55 to 57) says the request acts on the profile the resolve without it picks and never passes to a later one. ASCII only.
7. **Nothing else changes**: no new dependency, no new import, no option added or removed.

## Acceptance criteria
- [ ] All 11 tests of `tests/test_improve_review_alt_profile.py` pass, the file unedited.
- [ ] Every test of `tests/test_improve_roster_alt.py`, `tests/test_improve_roster_launch.py` and `tests/test_program_roster_sign_in.py` passes or skips only by its own condition, each file unedited; `test_task086a_review_alt_acts_on_the_profile_in_use_alone` passes.
- [ ] The skips that name the profile in use exist once, in one function both the plain resolve and the request call (named in the report with its lines).
- [ ] With the other pool exhausted, on a roster whose full profile names no alternate and whose native profile names `composer-2.5`, an empty built set: `--review-alt safety-refusal --no-probe` prints `DEVIATION  review_b is composer-2.5 on request (safety-refusal)`, writes the native profile with its `deviation` entry, exit 0; after a composer builder row, refused by the family cause, the resolved file unchanged.
- [ ] The docstring's example names `review_b_alt` in the native profile alone; `python tools/dump-cli.py --check` passes after regeneration; MANIFEST regenerated; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `bridge/cursor-bridge/VERSION` unchanged and not listed by `git status --short`.
- [ ] Every requirement under "Satisfies" is fully met - no stand-in, placeholder or "arrives in a later stage" text - and the acceptance file's tests name the requirement (its module docstring does).

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- Your run has a budget of 40 turns. Write the report as you go, so that nothing is lost if the run ends early.
- No secret is needed or used. Nothing you write (code, the notes line, the report) holds a path of this computer or a user name: write `<Workspace>`, `<tmp>` and `~` instead, also in quoted output.
- Do not edit any test file. If an acceptance test and this brief seem to disagree, stop and report it by its test id; do not work around it.
- If the brief, the rules, or the tooling got in your way - an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason - append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service; add no call to any service or the network.
- Any console process your code launches on Windows is created windowless (the module's `NO_WINDOW`, `creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). Capturing output does not prevent the window.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end; leave nothing running.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"): never run `roster-check.py` in this repository; only the tests run it.
- No value in this increment is the owner's (rule 52).
- Follow existing conventions in the file: ASCII program text, `main()` returning the exit code, options read from `argv`, the existing output line forms kept.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only. The one exception is `git restore bridge/cursor-bridge/VERSION` in Done, step 5.
- Numbers: an exit code is the integer `subprocess` or `main()` returns; JSON is read with `json.loads`/`json.load`; nothing is parsed by slicing a string.
- **A probe runs only as a test.** Run no Python other than the Done section's commands: no script of your own, no here-document, no `python -c` but step 10's. Where you need a scratch check, write it as a test file under `tests/` named `test_task087d_scratch_*.py`, run it with `python -m pytest -p no:cacheprovider -q <that file>`, and delete it; none stays in the diff, and the report names each one, what it showed and that it was deleted.
- Run the tests with `python -m pytest` directly as Done lists, not through `bridge-run.py`; the stripped run through the launcher is the supervisor's step 4. **Do NOT run the whole `tests/` tree**: the whole suite is CI's run.
- **Mutation: name the code points, run nothing.** The report lists, for each label, the function and lines (as the file stands after your change) a mutation would touch and the test id you expect to catch it: M1 the `review_b` pool exclusion dropped from the profile reading; M2 the mark exclusion dropped; M3 a `review_b` that did not answer not skipping the profile; M4 the request passing to a later profile; M5 the request taking the first profile whose builder is usable; M6 each refusal of Requirement 3 removed, one label each (M6a to M6k).
- **Known failures.** The acceptance file is red on the checkpoint (8 failed, 3 passed). If any other test fails that your change did not cause, report it by test id with its failure lines and fix none.
- Prefer reuse over new code - the existing helpers, the standard library - and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.

## Done
Your report is the file `handoff/TASK-087d-r1-report.md`, which you write as you go - what you did, what you changed, what you ran and what it printed, what you could not do - so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, for Requirements 1 to 7 one line each naming the functions and lines that meet it, the code points of M1 to M6k, every scratch test file (or `no scratch test file`), and a section headed exactly `Assumed, not verified`, the report's last section: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm - a probe ordering you chose, a case the acceptance file does not cover that you resolved one way. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change. Steps 1 and 2 before your first edit; steps 3 to 12 after your last edit, in this order:
1. `git status --short`
2. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_review_alt_profile.py` (expect 8 failed, 3 passed; quote the summary line and the failing ids)
3. `python tools/dump-cli.py` then `python tools/dump-cli.py --check` (it must pass)
4. `python tools/make-manifest.py`
5. `git status --short` (if `bridge/cursor-bridge/VERSION` is listed, run `git restore bridge/cursor-bridge/VERSION` and `git status --short` again)
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_review_alt_profile.py tests/test_improve_roster_alt.py tests/test_improve_roster_launch.py tests/test_program_roster_sign_in.py`
7. `python -m pytest -p no:cacheprovider -q -rs tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_a4_review_fixes.py tests/test_hotfix25a_roster_launcher.py tests/test_agent_models.py tests/test_release_t_ceiling.py tests/test_bug030.py tests/test_bug032.py tests/test_dump_cli.py`
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
10. `python -c "open('bridge/cursor-bridge/roster-check.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
11. `git diff --stat HEAD`
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed, nor any `tests/test_task087d_scratch_` file)

Steps 6 and 7 cover the tests that run, load or read `roster-check.py`; a failure in a file outside Scope is reported by test id, never fixed there.

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. Each mutation code point is listed by this brief's own label. A command you did not run is written `not run`, never described as run. Run this brief's test commands once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
