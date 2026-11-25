---
record: brief
header: 1
id: "TASK-087b"
round: 1
satisfies: [R-109]
scope: ["bridge/cursor-bridge/session-start.py", "bridge/cursor-bridge/settings.bridge.json", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_digest_parts.py", "tests/test_session_start.py", "tests/test_loop_text_pace.py", "tests/test_a5_followups.py", "tests/test_b2_least_confident.py", "tests/test_release_s_budgets.py", "tests/test_allowlist.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-087b-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-087b: The digest in two parts (R-109)

## Objective
The SessionStart hook `bridge/cursor-bridge/session-start.py` puts the supervisor's core back after a compaction, a resume or a fork. It prints two things today, each from its own registration of the hook: `--part pointers` (the project's position and what to re-read) and `--part digest` (the digest between the markers `<!-- digest:start -->` and `<!-- digest:end -->` at the head of `~/.claude/commands/supervisor.md`), each cut at `MAX_OUTPUT` because Claude Code caps a hook's plain output at 10,000 characters. The digest has outgrown one part: its cap of 9,500 characters forced every new line to be paid for with a trim. The owner decided on 2026-11-24 (R-109) that nothing is trimmed to fit a cap: the digest is printed in **two parts**, the whole at most 10,500 characters and each part at most 8,800. The supervisor's host probe passed (`run/supervisor/probe-087b.md`: Claude Code 2.1.330 delivered three SessionStart outputs of 2,700, 8,800 and 8,800 characters whole after a compaction), so the two-part form is built. The probe also showed that the commands of one group arrive in no fixed order, so each part names itself in its own header and nothing relies on the order. This increment makes the hook print the second part on `--part digest-2`, adds the second registration to the hook settings, and moves the existing tests from the old one-part cap to the two new caps. The supervisor's acceptance tests and the marker line in `supervisor.md` are committed before your checkpoint, with three existing tests the split would otherwise break or that held the old cap outside your Scope (`tests/test_session_start.py` and `tests/test_reads_only_applicable.py` now read the standing rules from both parts; `tests/test_workflow_model.py` holds the whole digest at 10,500); your work is to make the acceptance tests pass without changing any other answer of the hook.

Satisfies: R-109

The requirement is `docs/REQUIREMENTS.md` line 139 ("The rulebook's budget is treated as the owner decided on 2026-11-24 (instruction text and the budget's test): ..."); read it whole. This increment builds its digest clause; the rest of the row is other increments' and the row stays `planned` after this merge (the plan says so). You do not edit the register.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/session-start.py
- bridge/cursor-bridge/settings.bridge.json
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_digest_parts.py
- tests/test_session_start.py
- tests/test_loop_text_pace.py
- tests/test_a5_followups.py
- tests/test_b2_least_confident.py
- tests/test_release_s_budgets.py
- tests/test_allowlist.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-087b-r1-report.md

Limits on these paths:
- `bridge/cursor-bridge/session-start.py`: `main()`'s handling of `--part`, `digest_part`, `read_digest` and `cap`'s note where the part must be named, and the module docstring's description of the parts and of the registrations (it says today that the bridge registers the hook "TWICE"). `MAX_OUTPUT` (9800) stays as it is. Nothing of the pointers part changes: not `pointers_part`, not the workflow-file walk, not the bridge_env loading, not `status_candidates`.
- `bridge/cursor-bridge/settings.bridge.json`: one new group appended to `hooks.SessionStart` (Requirement R5), nothing else; no permission entry and no `retired` entry changes.
- `tests/test_improve_digest_parts.py`: the supervisor's acceptance tests, committed before your checkpoint. Listed so the scope check reads it as part of the increment. Read it whole and run it. **Do not edit it.** If a case seems wrong, stop and report it by its test id. A case you find missing is named in your report, never added.
- `tests/test_session_start.py`, `tests/test_loop_text_pace.py`, `tests/test_a5_followups.py`, `tests/test_b2_least_confident.py`: only the assertions that hold the digest's cap of 9,500 characters, each changed to the two new caps (Requirement R7), and the message words beside them; nothing else in these files.
- `tests/test_release_s_budgets.py`: only the module docstring's sentence on the digest's cap (lines 8 and 9: "The digest's own cap (9,500 characters, under Claude Code's 10,000 for a hook's output) stays where it is, in tests/test_session_start.py."). Not `RULEBOOK_WORDS`, not `STEP_FILE_WORDS`, not any test.
- `tests/test_allowlist.py`: only where it holds the hook settings' entries. As built it reads `settings.bridge.json` for its permission rules and holds no hook entry, so no edit is expected; if you find none to change, leave it untouched and say so in the report.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand. `bridge/cursor-bridge/VERSION` is outside Scope, reads `2026.11.24a` and must come out unchanged.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), never by hand. The reference quotes `session-start.py`'s module docstring, so a change to the docstring changes them.
- `docs/BUILDER_NOTES.md`: only by appending dated lines at its end (Constraints).

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration: nothing under `.github/`.
- docs/ and handoff/, except the files the Scope section names. `docs/HARDENING.md`, `docs/REQUIREMENTS.md` and `docs/PROJECT_STATUS.md` are the supervisor's records commit; `docs/DESIGN.md`, `docs/BUILD_PLAN.md`, `docs/INVENTORY.md` and `docs/diagrams/` are read, never edited.
- **The supervisor's own commits, before your checkpoint, which you do not edit:** `bridge/commands/supervisor.md` (the marker line `<!-- digest:part -->` inside the digest and the maintainer's comment above the digest), `docs/TRACE_MOVES.md` (the comment's entry, where the move mode asks for one), `bridge/cursor-bridge/workflow/trace-exceptions.md` (the comment's reword entry), and in `tests/test_session_start.py` the test `test_both_parts_fit_under_the_cap_for_every_phase_on_a_realistic_status_file` (it runs `--part digest-2` too), in `tests/test_reads_only_applicable.py` the test `test_r030_the_other_part_is_the_core_and_names_no_workflow_file`, and in `tests/test_workflow_model.py` the test `test_the_digest_keeps_its_limits` (10,500). The plan lists them in the increment's Scope for those commits; they are not yours. If the work seems to need a change in any of them, stop and report it.
- `bridge/cursor-bridge/bridge-install.py`: its merge and rollback already handle a second group (Context); do not edit it, nor `bridge/cursor-bridge/bridge-check.py` nor any other program under `bridge/`.
- `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every other test file, `tests/test_workflow_model.py` and `tests/test_reads_only_applicable.py` among them. A failure in one is reported by its test id, never fixed in that file.
- `~/.claude` and every installed copy of the bridge: never read, run or change them (Context, "Development data").

## Context
**This checkout.** You work in a git worktree of the repository, `Worktrees/TASK-087b`, beside another increment's merge gate in the main checkout. Its root is the Workspace root for every path and command in this brief. It has no project virtual environment; the system Python (`python`) runs the tests, as in other increments.

**The design and the plan.** `docs/DESIGN.md`, section "Change: the improvements release", line 736, the paragraph that names `--part digest-2`: read it whole. The plan entry is `docs/BUILD_PLAN.md`, `### TASK-087b` (line 2549); its Done when (line 2558) is the list of clauses the acceptance tests enforce: read it whole. Its opening clauses (the probe, and what happens where the probe fails) are the supervisor's and settled: the probe passed, so the "otherwise" branch is the one built. The release's standing constraints are the paragraph at line 2499 (the gate is release S's; the programs are the builder's and their acceptance tests the supervisor's, committed before the checkpoint and named here as fixed points; nothing is trimmed to fit a cap).

**Development data.** `docs/INVENTORY.md`, Decisions: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (section 15 condition 1, A1a condition 1)". For you: `session-start.py` runs only through the tests, each with a scratch home under pytest's `tmp_path` (as `tests/test_session_start.py`'s `home` fixture and `run_hook` do, setting `HOME` and `USERPROFILE`); the installer's merge runs only in a test, on scratch settings. Never run `session-start.py` or `bridge-install.py` against the real home folder.

**The hook as built** (`bridge/cursor-bridge/session-start.py`, line numbers on the checkpoint):
- `MAX_OUTPUT = 9800           # per part; Claude Code's cap is 10,000` (line 87).
- `read_digest(path)` (line 233) returns the text between `<!-- digest:start -->` and `<!-- digest:end -->`, stripped, or `""`.
- `cap(text, limit, what)` (line 240), quoted:
  ```
  if len(text) <= limit:
      return text
  return text[:limit - 90] + "\n[%s cut at %d characters by the hook's cap; re-read it in the file]" % (what, limit)
  ```
- `digest_part(digest, version)` (line 608), quoted:
  ```
  head = "CLAUDE-CURSOR BRIDGE core digest (bridge %s) - the condensed core of ~/.claude/commands/supervisor.md; the full text governs:" % version
  return head + "\n\n" + (digest if digest else "(no digest found in supervisor.md; re-read the whole file)")
  ```
- `main()` (line 613): `part` defaults to `"all"`; it prints nothing outside a bridge project or where `supervisor.md` is missing; `if part in ("pointers", "all")` appends the pointers, capped `"the section pointers"`; `if part in ("digest", "all")` appends `cap(digest_part(digest, version), MAX_OUTPUT, "the digest")`; the parts are joined by a blank line and written with one final line feed; exit 0 always. `installed_version()` (line 209) reads the `VERSION` file beside the program.
- `tests/test_session_start.py`'s `test_both_parts_fit_under_the_cap_for_every_phase_on_a_realistic_status_file` reads `"(bridge %s)" % installed in digest` from `--part digest`'s output; keep the first part's header as it is.

**The digest as the supervisor commits it.** In `bridge/commands/supervisor.md` the digest runs from line 9 (`<!-- digest:start -->`) to the end marker. Its paragraphs are, in order: `## The core, in brief`, `**Role.**`, `**Founding rules.**`, `**The loop (Phase 6, one increment).**`, `**Escalate to the owner only**`, `**Report**`, `**Standing rules.**`, `**Permissions.**`. The supervisor's commit puts the one line `<!-- digest:part -->` directly before `**Standing rules.**`, so the first part is everything before that line and the second part the standing rules and the permissions. The plan quotes the digest's length before the marker as 9,477 characters; it was written before hotfix 2026.11.24a, and on `main` as you start (`c76ea93`) the slice from the start marker to the end marker is 9,500 characters. The marker line takes it to 9,523, so the three cap assertions of R7 are red on your checkpoint and your change makes them green. The maintainer's comment on line 8 is rewritten by the same commit to name the two caps (10,500 for the whole, 8,800 a part) and the tests that hold them.

**The hook settings as built** (`bridge/cursor-bridge/settings.bridge.json`, lines 128 to 144): one `SessionStart` group, `"matcher": "compact|resume|fork"`, with two commands, `python "$HOME/.claude/cursor-bridge/session-start.py" --part pointers` and `... --part digest`, each `"type": "command"`, `"timeout": 20`.

**The installer's merge as built** (`bridge/cursor-bridge/bridge-install.py`; read, never edited). `merge_settings` (line 266) appends a bridge group to the owner's event only where the group holds a command the owner's file lacks, and never changes a group already there; `remove_settings` (line 296), used by the rollback, takes out the hook commands the leaving release has and the staying one lacks, and drops a group left empty. So a second group holding the one command `--part digest-2` is appended once by a first merge, a second merge changes nothing, and a rollback to 2026.11.23a removes that group alone. That is why the new command is a group of its own and not a third command in the existing group (which the installer would never add to an owner's file that holds the group). The acceptance tests hold this on a scratch home; it needs no installer change. If you find otherwise, stop and report it; do not edit the installer.

**The acceptance tests** (`tests/test_improve_digest_parts.py`, the supervisor's; read it whole, its module docstring first). They hold each part's command and header, a digest without the marker, the two caps, a part at its cap under the host's number in characters and in bytes (a digest whose larger part is exactly 8,800 characters, 300 of them characters of three bytes in UTF-8, printed with its header with no cut mark and in fewer than 10,000 characters and fewer than 10,000 bytes), the same of each part of the digest as it stands, and the settings' merge and rollback. They fix the second part's header words; follow them. They are red on the checkpoint by design: run the file before your first edit (Done, step 2) and quote its summary line and its failing ids; the cases that pass there must still pass after your change.

**The tests that held the digest at 9,500** (as built at the checkpoint):
- `tests/test_session_start.py` line 27: `assert len(TEXT[a:b]) <= 9500, "the digest part (digest + its header line) must stay under the hook's cap with margin"`.
- `tests/test_loop_text_pace.py` line 217: `assert len(d) <= 9500, len(d)` (in `test_r042_the_digest_stays_within_its_cap_with_every_rule_number`).
- `tests/test_a5_followups.py` line 100: `assert len(SV[a:b]) <= 9500, "a text release adds nothing to the digest"`.
- `tests/test_b2_least_confident.py`: the plan names it among the four; read it and change only an assertion that holds the digest's cap. Where a `9500` in it is not the digest's cap (line 55 holds `"chars": 9500` in a status file's shape), leave it unchanged and name it in the report.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions: "The builder's secure-coding rule is ASVS level 2"); the threat model is the Decisions row "The bridge's threat model as a whole". The hook reads files a builder or a reviewer can write in a project (the status file, read by the pointers part, unchanged here) and the installed `supervisor.md`; its output goes into the supervisor's context. The properties this increment keeps: the hook never blocks (exit 0 always), never writes anything, prints nothing outside a bridge project, and keeps each part under the host's cap whatever the digest holds (a marker missing, repeated, or placed so that a part is empty or too long). `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc` are in force for you.

**External services.** None. No network call.

**The host's version.** The supervisor's session has no `claude` on PATH (`claude --version`: command not found); the probe's host was Claude Code 2.1.330 (the desktop app's), the version these tests are written for.

**Values.** The caps 10,500 (the whole digest) and 8,800 (a part) are the owner's decision of 2026-11-24 as the plan states it (R-109); the acceptance tests pin them. Do not change either number or the tests that hold them, and report it if the work seems to need a change (rule 52). `MAX_OUTPUT` stays 9800 characters.

## Diagrams
None. The plan's `Diagrams:` line for this increment reads `none`.

## Requirements
1. **R1. `--part digest`.** Prints the first part's header (the existing header, unchanged) and the digest's text before the line `<!-- digest:part -->`; it does not print the marker line nor any text after it. Where the digest holds no such line, it prints the whole digest, as on the checkpoint.
2. **R2. `--part digest-2`.** Where the digest holds the line `<!-- digest:part -->`, prints a header of its own that names the second part and the installed version (`installed_version()`), then the digest's text after that line, without the marker line (red on the checkpoint, which prints nothing for this part). Where the digest holds no such line, it prints nothing. Outside a bridge project, or where `supervisor.md` is missing, it prints nothing, as the other parts do.
3. **R3. `--part all` and no `--part`.** Print the pointers and both parts, each part as R1 and R2 print it; `--part pointers` is unchanged.
4. **R4. The cap.** Each part is cut by `cap` at `MAX_OUTPUT` as on the checkpoint, `MAX_OUTPUT` unchanged, and the cut's note names the part (the first part and the second part are told apart in the note). No marker line, header or note pushes a part past `MAX_OUTPUT`.
5. **R5. The hook settings.** `hooks.SessionStart` in `settings.bridge.json` gains a second group, after the existing one: the existing group's matcher (`compact|resume|fork`) and the one command `python "$HOME/.claude/cursor-bridge/session-start.py" --part digest-2`, `"type": "command"`, `"timeout": 20`, the first group unchanged. The merge into a scratch home that holds 2026.11.23a's entries leaves the older group unchanged and appends the new one once; a second merge changes nothing; the rollback removes the new group alone (the acceptance tests).
6. **R6. The docstring.** The module docstring says the hook is registered three times for the event (the pointers and the digest's two parts, the second part in a group of its own), describes `--part digest-2` and `--part all`, and stays ASCII. The command reference is regenerated from it.
7. **R7. The four tests' numbers.** Each assertion that held the digest at 9,500 characters holds the whole digest (the slice it measured) at 10,500 and each part (the digest's text on either side of the line `<!-- digest:part -->`) at 8,800, with message words that say so; nothing else in those files changes. `tests/test_release_s_budgets.py`'s docstring sentence names the two caps as the maintainer's comment in `supervisor.md` does (10,500 for the whole, 8,800 a part, and the test that holds them). The report quotes the plan's 9,477 characters, `main`'s 9,500 before the marker (Context) and the whole's and each part's count as the tree now stands, each read from a test's output or an assertion message, never computed by a script of your own.
8. **R8. The old number.** After your edits, the command of Done step 9 searches `bridge/` and `tests/` for the old number in both its written forms, `9,500` and `9500`; the report quotes its output whole and says, line by line, which are history (a release note, a comment about a past release) and which are not. A hit outside the files this brief lets you edit is reported, never fixed.
9. **R9. Nothing else changes.** No new dependency, no new import; the pointers part, the exit code, the silence outside a bridge project and the reading of the status file are unchanged. MANIFEST regenerated with `python tools/make-manifest.py`; the command reference regenerated with `python tools/dump-cli.py` and `--check` green.

## Acceptance criteria
- [ ] Every test in `tests/test_improve_digest_parts.py` passes (it names R-109 and TASK-087b), unedited; a skip only by the test's own condition, its reason quoted from `-rs`; the cases that passed on the checkpoint still pass (the runs before your first edit and after your last, both quoted).
- [ ] Every test file of Done steps 6 and 7 passes; the files you edited changed only as the Scope's limits allow.
- [ ] `--part digest`, `--part digest-2`, `--part all` and the cap behave as R1 to R4 say; the settings hold the second group as R5 says.
- [ ] The search of Done step 9 is quoted whole, each hit classed as history or not.
- [ ] `python tools/dump-cli.py --check` passes; MANIFEST regenerated; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `bridge/cursor-bridge/VERSION` reads `2026.11.24a` and is not listed by `git status --short`.
- [ ] Every line you add is ASCII.
- [ ] R-109's digest clause is fully met, with no stand-in, placeholder or "later" text; the tests naming R-109 are the supervisor's acceptance tests.
- [ ] No new dependency. No new Semgrep high finding. The hook exits 0 and prints no traceback on any digest, marker placement or status file (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- This checkout is a separate worktree without the project's virtual environment. Do not install packages or create environments. The system Python, as `python`, runs every command of the Done section.
- Do not commit. Leave every change in the working tree: the supervisor commits after your run, so that no ref moves while another increment's review reads the repository.
- No secret is needed or used. Refer to `.env` and configuration keys by name only; never reproduce a value.
- Do not edit `tests/test_improve_digest_parts.py`, `bridge/commands/supervisor.md`, `docs/TRACE_MOVES.md`, `bridge/cursor-bridge/workflow/trace-exceptions.md` or any test file beyond the Scope's limits. If an acceptance test and this brief seem to disagree, or a test seems to pin something this brief does not say, stop and report it by its test id; do not work around it.
- **Known failures.** The acceptance file is red on the checkpoint by design (the supervisor's run: `12 failed, 66 passed`, nine of them the acceptance file's and the three cap assertions of R7, `assert 9523 <= 9500`). An existing test that fails because `--part digest` no longer prints the second part (an assertion that a standing rule's words, or the whole digest, appear in `--part digest`'s output) is reported by its test id with its failure lines and is not edited, even in a file within Scope, whose limits allow the cap numbers alone. The same for any other test that fails and that your change did not cause.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`, at its end. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No paths of this computer, no user names.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the worktree folder, `<tmp>` for a temporary folder and `~` for the home folder, including in quoted command output.
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). The hook launches none today; add none.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"): the hook and the installer's merge run only through the tests, with a scratch home.
- The caps 10,500 and 8,800 are the owner's (Context, "Values"): do not change them or the tests that pin them; report it if the work seems to need a change (rule 52).
- Follow existing conventions in the files you touch: the hook's plain ASCII output, `cap` for every part, exit 0 always, the settings file's two-space JSON layout.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff`, `git log` and, for Done step 9 alone, `git grep`. The single other exception is `git restore bridge/cursor-bridge/VERSION` in the Done section, where that file is listed after the manifest's regeneration.
- Numbers: a length is `len()` of a `str` (characters) or of its UTF-8 `bytes` (bytes); `MAX_OUTPUT` is a count of characters; nothing is parsed by slicing a string.
- **A probe runs only as a test.** Run no Python other than the Done section's commands: no `python -c`, no here-document, no script of your own. Where you need a scratch check, write it as a test file under `tests/` (a name starting `test_task087b_scratch_`), run it with `python -m pytest -p no:cacheprovider -q <that file>`, and delete it after the run; none stays in the change, and the report names each one, what it showed and that it was deleted.
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root (this worktree's root), with no `PYTHONPATH` or other environment change. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation: name the code points, run nothing.** The supervisor's mutants file sweeps the split after your run. Your report lists, for each label, the function and the line(s), as the file stands after your change, that the mutation would touch, and the acceptance test id you expect to catch it: K1 the second part never printed; K2 the marker printed inside a part; K3 the first part printing the whole digest beside the second; K4 the second part printed uncut by the cap. Write no mutation script and change no code to try one.
- Prefer reuse over new code: `read_digest`, `cap`, `digest_part`, `installed_version`, the standard library; write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-087b-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name (Constraints).

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for R1 to R9, one line each on what meets it, naming the functions and their lines as the file stands after your change; for R1, R2 and R4 the header line and the cut note as a test prints them; for R7 the plan's 9,477, `main`'s 9,500 and the whole's and each part's count now, each with the output line it is read from;
- for each of the four tests of R7, the assertion before and after, and every `9500` in them you left unchanged, with the reason;
- whether `tests/test_allowlist.py` needed an edit, and if so which lines;
- the search of Done step 9, quoted whole, each hit classed as history or not;
- every scratch test file you wrote under `tests/`, what it showed, and that it was deleted (or `no scratch test file`);
- the code points of K1 to K4 (Constraints), each with the function, the lines and the test id you expect to catch it;
- any case you found missing from the acceptance file, named;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: what you assumed | why | what would confirm it, one item per line. Examples of the kind expected: what the second part prints where the marker stands but the text after it is empty; what `--part digest` prints where the marker stands twice; whether the host counts a hook's output cap in characters or in bytes; that the installer appends the new group after the owner's own SessionStart groups. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root (this worktree's root), each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change. Steps 1 and 2 before your first edit; steps 3 to 12 after your last edit, in this order:
1. `git status --short`
2. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_digest_parts.py` (the checkpoint's run: quote the summary line and every failing id)
3. `python tools/dump-cli.py` then `python tools/dump-cli.py --check` (it must pass)
4. `python tools/make-manifest.py`
5. `git status --short` (if `bridge/cursor-bridge/VERSION` is listed, run `git restore bridge/cursor-bridge/VERSION` and run `git status --short` again)
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_digest_parts.py tests/test_session_start.py tests/test_loop_text_pace.py tests/test_a5_followups.py tests/test_b2_least_confident.py tests/test_release_s_budgets.py tests/test_allowlist.py`
7. `python -m pytest -p no:cacheprovider -q -rs tests/test_session_start_module.py tests/test_reads_only_applicable.py tests/test_workflow_model.py tests/test_header_status.py tests/test_rollback.py tests/test_dump_cli.py`
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `git grep -n -e "9,500" -e "9500" -- bridge tests`
10. `git diff --stat`
11. `git diff -- bridge/cursor-bridge/session-start.py bridge/cursor-bridge/settings.bridge.json` (read it for any non-ASCII character you added; say in the report that none was added, or name it)
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed, and no `tests/test_task087b_scratch_` file; if either is, report it)

Step 7 covers the existing tests that run the hook, read the digest or merge the settings, all outside Scope; a failure in any of them is reported by test id, never fixed in that file.

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Each pytest summary line is quoted verbatim; never restate a count in prose. A claim that a check passed quotes the output line that shows it, and a number of failing or skipped cases is backed by the pytest lines naming them (`-rs` prints each skip's reason). A command you did not run is written `not run`, never described as run. Run this brief's test commands once more after your last edit, and write the report's results after step 12, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`; it will, since you do not commit).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
