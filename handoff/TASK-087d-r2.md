---
record: brief
header: 1
id: "TASK-087d"
round: 2
satisfies: [R-107]
scope: ["bridge/cursor-bridge/roster-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_review_alt_profile.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-087d-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-087d: `--review-alt` acts on the profile the resolve picks

Round cause: Review A, round 1, blocking 1 (behaviour): the request probes review_b_alt twice in one role (bridge/cursor-bridge/roster-check.py).

## Objective
`roster-check.py --review-alt <reason>` resolves a profile's alternate reviewer (`review_b_alt`) on request, for a provider's safety refusal of Review B. Round 1 of this increment made the request act on exactly the profile the resolve without the request picks: in `main()` of `bridge/cursor-bridge/roster-check.py` it replaced the helper `_profile_in_use` with one reading of the profile in use, `_evaluate_profile(prof, verbose)` (lines 1220 to 1351), which the request path (lines 1353 to 1411) and the plain resolve loop (lines 1416 to 1435) both call, and it corrected the module docstring's roster example. Round 1's work stands in this checkout as committed; Review A approved Requirements 1, 2, 3, 5, 6 and 7 and found the plain resolve's output unchanged, and all of that is kept. Round 2 repairs one defect Review A found and reproduced: with probes on, where the profile in use already resolves a deviation (Review B's family built the change, reason `family`; or Review B excluded by a mark or its pool, reason `unavailable`), `_evaluate_profile` probes the alternate in the role `review_b_alt` (line 1316) and the request path then probes it again in the same role (line 1394). That is a second paid call, and the two answers can disagree: in the family case a failed first probe makes the evaluation fall back to a REBUILD and keep the profile (lines 1328 to 1342, the deviation reset to None), and a second probe that answers then grants the alternate the resolve had just judged not answering. After this round the alternate is probed at most once per run in that role, and the request acts on that one answer.

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
- handoff/TASK-087d-r2-report.md

Do not modify anything else.

Limits on these paths: `tests/test_improve_review_alt_profile.py` is the supervisor's acceptance file, committed before the checkpoint: read it whole and run it, **do not edit it**. `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`, and `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` only by running `python tools/dump-cli.py` (Done), never by hand; `roster-check.py` has no argument parser, so `tools/dump-cli.py` quotes its module docstring. Round 2 needs no docstring change, so these two files are expected to come out unchanged; `python tools/dump-cli.py --check` must pass. `docs/BUILDER_NOTES.md`: new dated lines at its end only. In `roster-check.py`, change only what the request's reuse of the alternate's one probe answer needs: what `_evaluate_profile` returns about the alternate's probe, and the request path's probe of the alternate (lines 1393 to 1402). Leave the rest of round 1's code as it stands.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names
- `bridge/cursor-bridge/bridge-run.py`, `bridge/cursor-bridge/bridge_env.py`, every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/`, `bridge/cursor-bridge/workflow/`, `bridge/cursor-bridge/Merge-Verification-Policy.md`, `bridge/cursor-bridge/VERSION` (reads `2026.11.24a` and must come out unchanged), `docs/ROSTER.json`, `docs/ROSTER.resolved.json`
- every test file; `tools/make-manifest.py` and `tools/dump-cli.py` (you run them, you edit neither)
- the `--record-failure`, `--record-success`, `--mark-exhausted`, `--mark-reset`, `--clear-unavailable` and `--repair-record` modes, the built-set reading (`built_families`, `built_by`), the state file's format, `probe` and its judgement of one reply, and every output line form the existing tests read
- the module docstring (round 1's correction stands), the skips and their order inside `_evaluate_profile`, the plain resolve loop (lines 1416 to 1435) and its output

## Context
- **The program as round 1 left it.** `bridge/cursor-bridge/roster-check.py`, `main()` from line 1108: `--review-alt` reason parsed at lines 1111 to 1119 (exit 2 on a malformed reason); the built set read at line 1141; a set that cannot be read refused at lines 1154 to 1157 and an unknown set refused for the request at lines 1159 to 1163, both before any profile is read. Helpers inside `main()`: `_rebuild_entry` (1177), `_probe_roles(roles)` (1197, returns `(usable, sign_in)`, printing the probe lines and `SIGN_IN_LINE`), `_alt_pool_ok` (1210), `_r_excluded` (1215), `_evaluate_profile(prof, verbose)` (1220 to 1351; returns None for a skipped profile, the strings `"sign-in"` and `"git-fail"`, or a dict with the keys `profile`, `builder`, `review_a`, `review_b`, `families`, `deviation`, `rebuild`, `profile_rebuild_end`, `a_id`, `a_fam`, `a_pool`, `r_id`, `r_fam`). Its probe block is lines 1305 to 1346: the builder probed (1306), then `review_b` where `_r_excluded` does not hold (1311 to 1314), then the alternate where a deviation resolves it and `_alt_pool_ok` holds (1315 to 1318); then a deviation for reason `unavailable` whose alternate did not answer skips the profile (1323 to 1327), and a family deviation whose alternate did not answer falls back to a REBUILD with `deviation = None` and keeps the profile where `review_b` answered (1328 to 1342). The request path (1353 to 1411): it loops the profiles through `_evaluate_profile(prof, False)` and stops at the first in use (1355 to 1364), refuses on no profile in use (1365 to 1367), then refuses in this order: no alternate named (1370 to 1372), its family unknown (1376 to 1378), Review A's family (1379 to 1381), a family that built the branch (1382 to 1384), marked unavailable (1385 to 1387), its pool exhausted (1388 to 1390); then, with probes, it calls `probe(a_id)` itself (1393 to 1402), printing `    probe review_b_alt <id>: <detail>`, SIGN-IN with exit 5, or `FAIL  --review-alt refused: review_b_alt <id> did not answer its probe` with exit 1. That last call is the second probe this round removes where the evaluation already probed the alternate.
- **The fix shape (the supervisor's decision; follow it).** `_evaluate_profile` returns the alternate's probe answer where it probed the alternate, including the family case where the alternate did not answer and the deviation was reset to None, and returns no answer where it did not probe the alternate (probes off, no deviation, or `_alt_pool_ok` false). The request reuses that answer: on a recorded failure it refuses with the existing line `FAIL  --review-alt refused: review_b_alt <id> did not answer its probe`, exit 1; on a recorded answer it grants without a second probe; it probes the alternate itself only where the evaluation did not. The request's static refusals (no alternate, family unknown, Review A's family, built family, marked, pool) keep their place and order before the answer is read. A sign-in from any probe still ends the run with SIGN-IN and exit 5, the resolved file unchanged. The plain resolve's output and resolved file stay unchanged in every case (the dict may gain a key; the plain loop does not print or write it).
- **Trust boundary and security level.** The roster file, the state file under the git common folder and the run record `run/launcher/runs.jsonl` are inputs a builder or reviewer can write (KP-078): every refusal is kept. The project's ASVS level is 2 (`docs/INVENTORY.md`). Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.
- **Development data** (`docs/INVENTORY.md`): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: never run `roster-check.py` in this repository; only the tests run it, on their scratch repositories.
- **The acceptance tests**, `tests/test_improve_review_alt_profile.py`, now 14 tests, importing helpers from `tests/test_improve_roster_alt.py` and constants from `tests/roster_rows.py`. The 11 of round 1 all pass on round 1's code and must keep passing. Three are new and red on round 1's code (with `tests/test_tests_windowless.py` the supervisor's run printed `3 failed, 21 passed`):
  - red: `test_task087d_r2_after_a_grok_build_the_alternate_is_probed_once_on_request` (the family case, probes on, every probe answering: exit 0, one DEVIATION line on request, exactly one `probe review_b_alt` line)
  - red: `test_task087d_r2_a_marked_review_b_the_alternate_is_probed_once_on_request` (Review B marked unavailable, the alternate resolved for that cause: exit 0, one DEVIATION line on request, exactly one `probe review_b_alt` line)
  - red: `test_task087d_r2_an_alternate_that_did_not_answer_is_refused_on_its_one_answer` (a native profile naming `review_b_alt` the GPT model, a grok build, the alternate's first probe failing and any later one answering: exit 1, no DEVIATION line, the `did not answer its probe` FAIL line naming the alternate, the alternate probed exactly once, the resolved file unchanged)
- **Tests that must pass unedited**: every test of `tests/test_improve_roster_alt.py` (among them `test_task086a_review_alt_acts_on_the_profile_in_use_alone`, line 1363, and the refusal tests at lines 704 to 755 and 1337 to 1466), `tests/test_improve_roster_launch.py` and `tests/test_program_roster_sign_in.py`; and the other tests that run or read the program (Done, step 7).
- No `claude --version` is relevant: the increment touches no Claude Code host behaviour. It talks to no external service; every probe in the tests is switched off or replaced in-process.

## Diagrams
None: the plan names no diagram for this increment.

## Requirements
Requirements 1, 2, 3, 5, 6 and 7 were met in round 1 and approved by Review A: keep each as it stands. Requirement 4 is the one this round completes.
1. **One reading of the profile in use.** `--review-alt <reason>` acts on the profile the resolve without the request picks, named by the same skips in the same order, by one function the resolve loop calls too (`_evaluate_profile`); no second copy of those skips stands.
2. **The request never passes to a later profile** than the one the resolve picks: where that profile names no alternate, or its alternate is refused, the request ends with exit 1 and the cause; where no profile is in use it ends with exit 1 and a cause.
3. **Every refusal stands**, each with exit 1 (or the exit named), the cause on a `FAIL` line, no RESOLVED line, no DEVIATION line and the resolved file unchanged: (a) the malformed reason (exit 2); (b) the built set unknown; (c) the built set that cannot be read; (d) no alternate in the profile in use (`no review_b_alt named in profile '<name>'`); (e) an alternate of Review A's family; (f) of a family that built the branch; (g) of an unknown family (`its family is unknown`); (h) marked unavailable; (i) in an exhausted pool; (j) an alternate that did not answer its probe; (k) a sign-in, exit 5. Keep the existing wording of each `FAIL` line.
4. **Probes.** With probes, each answer is read as the resolve reads it; a skipped profile's models are probed once each; **no model is probed twice in one role in one run, the alternate included across `_evaluate_profile` and the request path**: where the evaluation probed the alternate, the request reads that answer (a failure refused with the line of 3(j), an answer granted without a further probe) and never calls `probe` for it again; where the evaluation did not probe it, the request probes it once, as today. A sign-in from any probe ends the run with SIGN-IN and exit 5, the resolved file unchanged.
5. **Output of a granted request**: one DEVIATION line, `DEVIATION  review_b is <alt> on request (<reason>)`, no other DEVIATION line and no REBUILD line; the resolved file holds the profile in use with `review_b` the alternate and the `deviation` entry `{review_b_alt, reason, branch, built}` (`built` the known set, sorted). The plain resolve's output and resolved file are unchanged in every case.
6. **The module docstring** stays as round 1 left it: its roster example names `review_b_alt` in the native profile alone, and the `--review-alt <reason>` paragraph says the request acts on the profile the resolve without it picks and never passes to a later one. ASCII only.
7. **Nothing else changes**: no new dependency, no new import, no option added or removed.

## Acceptance criteria
- [ ] All 14 tests of `tests/test_improve_review_alt_profile.py` pass, the file unedited; among them the three round-2 tests named in Context.
- [ ] Every test of `tests/test_improve_roster_alt.py`, `tests/test_improve_roster_launch.py` and `tests/test_program_roster_sign_in.py` passes or skips only by its own condition, each file unedited; `test_task086a_review_alt_acts_on_the_profile_in_use_alone` passes.
- [ ] With probes, in the family case and in the marked case, the request's output holds exactly one `probe review_b_alt` line; where the evaluation recorded the alternate not answering, the request is refused by the existing `did not answer its probe` line with no second call of `probe` for it.
- [ ] The plain resolve's output and resolved file are unchanged against round 1 (the plain-resolve tests of step 6 and step 7 pass unedited).
- [ ] `python tools/dump-cli.py --check` passes; MANIFEST regenerated; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `bridge/cursor-bridge/VERSION` unchanged and not listed by `git status --short`.
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
- **Mutation: name the code points, run nothing.** The report holds a table with one row per label: the label, the function and lines (as the file stands after your change) the mutation would touch, and the full id (`file::test_name`) of a test that actually exercises that code point and would fail under the mutation. Name a test only after reading it and confirming it reaches that code point with the input the mutation changes; never a group ("the refusal tests") and never a test that exercises a different refusal (round 1's M6a row named the sign-in test for the malformed reason, which Review A rejected). Where no test in the files of Done steps 6 and 7 exercises a label, write `no test exercises it` in that row. The labels: M1 the `review_b` pool exclusion dropped from the profile reading; M2 the mark exclusion dropped; M3 a `review_b` that did not answer not skipping the profile; M4 the request passing to a later profile; M5 the request taking the first profile whose builder is usable; M6a to M6k each refusal of Requirement 3 removed, one label each, in Requirement 3's lettering (M6a the malformed reason, M6b the built set unknown, M6c the built set that cannot be read, M6d no alternate, M6e Review A's family, M6f a built family, M6g an unknown family, M6h marked unavailable, M6i an exhausted pool, M6j the alternate that did not answer, M6k the sign-in); M7 the request probing the alternate a second time where the evaluation probed it.
- **Known failures.** The acceptance file is red on the checkpoint (3 failed, 11 passed: the three round-2 tests). If any other test fails that your change did not cause, report it by test id with its failure lines and fix none.
- Prefer reuse over new code - the existing helpers, the standard library - and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.

## Done
Your report is the file `handoff/TASK-087d-r2-report.md`, which you write as you go - what you did, what you changed, what you ran and what it printed, what you could not do - so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, one sentence on how the change removes the second probe of the alternate, for Requirements 1 to 7 one line each naming the functions and lines that meet it, the mutation table of M1 to M7 (Constraints), every scratch test file (or `no scratch test file`), and a section headed exactly `Assumed, not verified`, the report's last section: every fact or choice this change relies on that neither this brief nor the existing code settled, and that you did not confirm - for instance the form in which `_evaluate_profile` returns the alternate's answer and what it holds where no probe was made, a case the acceptance file does not cover that you resolved one way (probes on with the alternate's pool excluded, the empty built set, a later profile naming the same alternate), and any ordering of the refusals against the recorded answer that you chose. One item per line: what you assumed · why · what would confirm it. Write `Assumed, not verified: none` only where there is truly none; Review A will hold the section against the diff. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change. Steps 1 and 2 before your first edit; steps 3 to 12 after your last edit, in this order:
1. `git status --short`
2. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_review_alt_profile.py` (expect 3 failed, 11 passed; quote the summary line and the failing ids)
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
