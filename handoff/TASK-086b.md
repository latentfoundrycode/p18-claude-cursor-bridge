---
record: brief
header: 1
id: "TASK-086b"
round: 1
satisfies: [R-107]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_roster_launch.py", "tests/test_hotfix25a_roster_launcher.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-086b-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-086b: The launcher's two review refusals read the built set and the recorded deviation (R-107)

## Objective
`bridge/cursor-bridge/bridge-run.py` (the launcher) refuses two kinds of review launch today: `review_launch_refusal` (line 1244) refuses a review on the resolved roster's builder model, and `review_family_refusal` (line 2438) refuses a review whose model is of the family of the branch's **last** builder run alone, swallowing any failure into a note and launching anyway. TASK-086a (merged) gave `bridge/cursor-bridge/roster-check.py` one function, `built_families` (line 468), that returns the **set of families that built a branch** from the run record `run/launcher/runs.jsonl`, and tells a set that is known, empty, unknown, or cannot be read; and it lets the roster resolve a profile's second reviewer `review_b_alt` with a `deviation` entry in `docs/ROSTER.resolved.json`. This increment makes the launcher's side agree: the family refusal reads that set (every family that built, not the last run), refuses by any builder's family where the set is unknown, refuses every review where the set cannot be read or the roster program cannot be loaded; the builder-model refusal lets a review on the builder model through only on a matching, current `deviation` entry, failing closed; and every builder row the launcher writes gains two keys, `start_commit` and `clean`, which `built_families` already reads to drop a rebuilt run. A row is also appended on a line of its own even after a torn last line. The supervisor's acceptance tests are written and committed before your checkpoint; your work is to make them pass without changing any answer of the launcher that the existing tests read.

Satisfies: R-107

The requirement's row is `docs/REQUIREMENTS.md` line 137; read it whole. Its launcher sentences are this increment's: "`bridge-run.py` refuses a review by a model of any family in the built set, of any builder's family, the roster file's or a parsing builder row's of the branch, where the set is unknown, and every review where the roster program cannot be loaded, and lets a review on the profile's builder model through only where the resolved file's `deviation` names that model for the current branch and its recorded families equal the known set as read at the launch", and "where, inside a repository, the set cannot be read at all ... the launcher refuses every review". The roster's part was TASK-086a's; the text's part is TASK-087c's. The requirement stays `planned` after this merge (the plan says so); you do not edit the register.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_roster_launch.py
- tests/test_hotfix25a_roster_launcher.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-086b-r1-report.md

Limits on these paths:
- `bridge/cursor-bridge/bridge-run.py`: only `review_launch_refusal` (line 1244), `review_family_refusal` (line 2438), the building of the run's row `entry` (line 3372, "the place a run's row is first written") for its two new keys, and `write_log` (line 1044) for the new-line rule of Requirement 7; small helpers of your own beside them where needed. Nothing else in the file changes: not `builder_review_refusal`, not the call sites at lines 3230 and 3253 beyond what a changed return value needs, not the heavy-slot code, not `branch_of`, `workspace_of` or `roster_program`'s loading. The built set is read from the roster program's one function, `built_families`; do not copy its logic into the launcher.
- `tests/test_improve_roster_launch.py`: the supervisor's acceptance tests, committed before the checkpoint. It is listed so the scope check reads it as part of the increment. Read it whole and run it. **Do not edit it.** If a case seems wrong, stop and report it by its test id. A case you find missing is named in your report, never added.
- `tests/test_hotfix25a_roster_launcher.py`: the supervisor's change before the checkpoint, in the one test that pinned the last builder run alone (`test_the_launcher_refuses_a_review_b_of_the_family_that_built_the_change`), and the case added beside it (Context). Listed for the scope check. **Do not edit it.**
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand. `bridge/cursor-bridge/VERSION` is outside Scope, reads `2026.11.24a` and must come out unchanged.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), never by hand; they change only if a text the reference quotes from `bridge-run.py` changes.
- `docs/BUILDER_NOTES.md`: only by appending dated lines at its end (Constraints).

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration: nothing under `.github/`.
- docs/ and handoff/, except the files the Scope section names. `docs/REQUIREMENTS.md`, `docs/HARDENING.md`, `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md` are the supervisor's records commit; `docs/DESIGN.md`, `docs/BUILD_PLAN.md` and `docs/diagrams/` are read, never edited.
- `bridge/cursor-bridge/roster-check.py` (TASK-086a's, merged; you call it, you do not edit it, its `roster_models` lead included), `bridge/cursor-bridge/bridge_env.py`, `bridge/cursor-bridge/mutation-run.py`, every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/` and `bridge/cursor-bridge/workflow/`, `bridge/cursor-bridge/Merge-Verification-Policy.md`, `bridge/cursor-bridge/CHANGELOG.md`, `bridge/cursor-bridge/VERSION`.
- `docs/ROSTER.json`, `docs/ROSTER.resolved.json` and `run/` of this repository: never run `roster-check.py` or `bridge-run.py` here except through the tests (Context, "Development data"). Write nothing under `run/`; the mutants file and the mutation run are the supervisor's, after your run; write no mutation script.
- `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every other test file, `tests/test_task032_supervisor_launcher.py` among them. A failure in one is reported by its test id, never fixed in that file.

## Context
**The design that binds this increment.** `docs/DESIGN.md`, section "Change: the improvements release", the paragraph beginning `- *C39 (first), with T108 and T103.*` (line 598) and the table under it (lines 600 to 611): read both whole. The launcher's part, quoted from line 598: "A builder row gains two keys for that, `start_commit`, the commit the launch started on, and `clean`, whether the working tree and the index showed no change then outside `docs/ROSTER.resolved.json`, the one file the resolve itself rewrites between a reset to the checkpoint and the launch (step 3b's order), an uncommitted change to any other tracked file and an untracked file that is not ignored making it false; both are read in the folder the row's branch is read in, a worktree builder's among them (the record's `head` is taken: it holds the command's program name)." ... "The launcher appends each row on a line of its own, beginning a new line first where the record's last byte is not one, so a torn last line damages no later row." ... "The launcher's family refusal reads the same built set, where today it reads the last builder run alone, and where the set is unknown it refuses a review by a model of any builder's family the roster file names or a builder row of the branch shows, the resolved file's builder standing in where the roster file cannot be read and every review refused where neither can, where today an unreadable record refuses nothing. Its refusal of a review on the profile's builder model lets the launch through only where the resolved file's `deviation` names that model for this branch, the set is known, the model's family is not in it, and the entry's recorded families equal the set as read at the launch; otherwise the refusal says to resolve again. That exception fails closed: nothing the launcher cannot read opens it."

The plan entry is `docs/BUILD_PLAN.md`, `### TASK-086b` (line 2527); its Done when (line 2536) is the list of clauses the acceptance tests enforce: read it whole. The release's standing constraints are the paragraph at line 2499.

**Development data.** `docs/INVENTORY.md`, Decisions: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (section 15 condition 1, A1a condition 1)". For you: `bridge-run.py` and `roster-check.py` run only through the tests, in their scratch repositories under pytest's `tmp_path`, with a stand-in for `cursor-agent`. Never launch `bridge-run.py` or `roster-check.py` in this repository, never call the real `cursor-agent`, and never read or copy anything under `~/.claude` or `~/.cursor-bridge`.

**The launcher as built (line numbers on the tree of hotfix 2026.11.24a carried onto main; the supervisor's checkpoint commits change only tests).**
- `LOG = os.path.join("run", "launcher", "runs.jsonl")` (line 132); `read_log(folder)` (line 1040) reads it through `bridge_env.read_runs_jsonl`; `write_log(folder, entry)` (line 1044) appends `json.dumps(entry) + "\n"` in text mode, only where `<folder>/run` exists, and an `OSError` never stops a run.
- `roster_builder_model(folder)` (line 1189): the `builder` string of `<folder>/docs/ROSTER.resolved.json`, `None` where unreadable.
- `review_launch_refusal(argv, folder)` (line 1244), quoted:
  ```
  if not is_agent_argv(argv):
      return None
  builder = roster_builder_model(folder)
  model = model_of(argv)
  if builder and model == builder:
      return "review launch on the roster builder model (%s) is refused; Review B uses a reviewer model" % builder
  for token in bridge_env.handoff_brief_tokens(argv):
      if bridge_env.parse_review_name(token):
          return "a review launch must not name a brief (%s); only the launcher counts builder briefs" % token
  return None
  ```
  It is called from `builder_review_refusal` (line 1277) for `--kind review`; its text is passed through `_ascii_refusal` and printed as `bridge-run: refused - <reason>`, exit 125.
- `roster_program()` (line 2426) loads `roster-check.py` beside the launcher through `importlib` as module `roster_check`.
- `review_family_refusal(argv, folder)` (line 2438), quoted in its core:
  ```
  try:
      roster = roster_program()
      built = roster.built_by(os.path.join(folder, LOG), branch_of(workspace_of(argv, folder)))
      if not built:
          return None
      built_fam, review_fam = roster.family_of(built), roster.family_of(model)
  except Exception as e:
      NOTES.append("the review-family check could not run (%s); check the family by hand" % e)
      return None
  if built_fam and built_fam == review_fam:
      return ("Review B %s is of the %s family, which built this change (%s, the branch's last builder run): rebuild it "
              "with the builder in docs/ROSTER.resolved.json first (step 3b; roster-check prints REBUILD)" % (model, review_fam, built))
  ```
  It is called at line 3253 only where `kind == "review"`; a reason is printed as `bridge-run: refused - <reason>` with exit 125, before the started line and before any row is written.
- `branch_of(folder)` (line 2389): `git -C <folder> rev-parse --abbrev-ref HEAD`, windowless, `timeout=bridge_env.GIT_TIMEOUT`. `workspace_of(argv, folder)` (line 2404): the `--workspace` folder of a `cursor-agent` command, else the launch folder.
- The row: `entry` is built at line 3372 (`{"id", "kind", "head", "model", "branch", "limit", "seconds", "exit", "healthy"}` plus the brief's keys from `brief_meta`), before the heavy-slot wait; it is written by `write_log` at the end of the run (lines 3500, 3526, 3571, 3591) or at once for a launch that never got the slot (`"slot": "not free"`, line 3419). The key `head` holds the command's program name and stays as it is. The row's branch `log_branch` is `brief_meta["branch"]` for a builder launch, which `builder_review_refusal` read as `branch_of(ws)` with `ws = workspace_of(argv, folder)` on the command **before** `resolve(cmd)` (line 3357). Read `start_commit` and `clean` in that same folder, `workspace_of` on the command as given, not on the resolved command (a recorded lead, docs/HARDENING.md, hotfix 2026.11.24a: `workspace_of` after `resolve` does not recognise a resolved `cursor-agent`). Read them before the child is started.

**The roster program you call (`bridge/cursor-bridge/roster-check.py`, as merged).**
- `built_families(run_log, branch=None, cwd=None, roster=None, profiles=None)` (line 468) returns a dict: `status` one of `"known"`, `"empty"`, `"unknown"`, `"unreadable"`; `families` (a set of family names; meaningful for `known` and `empty`); `unknown_causes` (a list of `(needle, label)` pairs); `unreadable_cause` (one of `"detached"`, `"git"`, `"main"`, or the record's file name `runs.jsonl`); `parsing_rows` (every builder row of the branch that parses, `slot not free` excluded); `counted_rows`; `branch`; `run_log_base`. `cwd` is the folder the branch is read in; where `branch` is not given it is read there by `git symbolic-ref`. Outside any repository (no `.git` in `cwd` or above) the status is `"empty"`. Its docstring: "TASK-086b's launcher must pass the roster and its profiles for the same set the resolve reads; without them a row whose family only the roster names reads as unknown."
- `family_of(model_id, override=None)` (line 718); `norm_entry(entry)` (line 143); `_roster_builder_families(roster, profiles)` (line 379, the families of every profile's `builder` and of a top-level `builder` and `review_b`); `_parsing_row_families(rows, roster, profiles)` (line 602); `_roster_model_family(roster, profiles, model_id)` (line 395). The leading underscore marks them private to that module; calling them from the launcher is your choice, copying their logic is not.
- `load_roster(path)` (line 871) **writes** the roster's state file (`save_state`) on its way; the launcher must write nothing to the roster's state, so do not call it. The roster file `docs/ROSTER.json` is read as JSON for its builders only. A v1 roster has no `profiles` and a top-level `builder` and `review_b` (`main()` builds one implicit profile from them, line 1153).
- `built_by(run_log, branch=None)` (line 156) keeps its answer for the tests that call it; the launcher no longer needs it.
- `_valid_commit_name` (line 229) accepts a `start_commit` only as a full object name, 40 or 64 hexadecimal digits; any other value is a row that is never dropped. So `start_commit` is written as `git rev-parse HEAD` prints it in full, never abbreviated.

**The acceptance tests** (`tests/test_improve_roster_launch.py`, the supervisor's; read it whole, its module docstring first). Every launch is a stand-in for `cursor-agent`; the run records and resolved files are written by the test. They were committed in d58bd2a with the two other test changes below; the supervisor's run of the three files on that commit printed `62 failed, 133 passed in 114.53s (0:01:54)` (the new file 90 cases, 61 failing; the hotfix25a file's new case failing; the task032 file passing). They are red on the checkpoint by design: run the file before your first edit (Done, step 2) and quote its summary line and its failing ids, so the report shows which were red; the cases that pass there pin answers of the checkpoint and must still pass after your change.

**The change to `tests/test_hotfix25a_roster_launcher.py`** (the supervisor's, before the checkpoint). Its test `test_the_launcher_refuses_a_review_b_of_the_family_that_built_the_change` wrote a grok builder row, then a composer row on the same branch, and let a grok review through: it pinned the last builder run alone. The composer row now carries `clean` true and the grok row's `start_commit` (a rebuild's row), so the grok row is dropped and its assertion stands; a case beside it writes the same two rows without the keys, where the grok review is refused (red on the checkpoint).

**A precondition in `tests/test_task032_supervisor_launcher.py`.** Its helper `check_row` (line 272) asserts that a builder row holds no key outside `OLD_FIELDS | NEW_FIELDS` (lines 32 to 35), and about thirty builder-launch tests there and in `tests/test_task032_supervisor_r4.py` call it. The new keys `start_commit` and `clean` must stand in that set at your checkpoint (the supervisor's). If at your checkpoint `NEW_FIELDS` does not name both, those tests fail by your change alone: do not edit that file; report the failing ids in your report and append a line to `docs/BUILDER_NOTES.md`.

**The answers of the checkpoint that must stand** (the survey of the existing tests, `docs/HARDENING.md` line 2570, the critique's round 4). Each of these files passes unedited after your change:
- The refusal of a brief named in a review launch and of a review on the builder model with no entry: `tests/test_task032_supervisor_launcher.py::test_task032_launcher_review_on_builder_model_refused`, `::test_task032_launcher_review_naming_brief_refused`, and `::test_task032_launcher_review_naming_resolution_or_report_allowed`. The last launches a review naming an untracked report file in a repository with `main`, a resolved roster whose builder is `composer-2.5`, no `docs/ROSTER.json` and no run record: its set is unknown (a report without its row), the roster file cannot be read, so the resolved file's builder stands in, and its reviewer `gpt-5.5-high` is of no builder's family, so it runs.
- `tests/test_d003_review_round_states.py::test_d003_transition_a_review_launch_refused_leaves_no_started_line` (three cases) expects the words `review launch on the roster builder model`, `must not name a brief` and `is of the xai family` in the refusals, exit 125, no started line and no row.
- `tests/test_hotfix25a_roster_launcher.py::test_a_launch_that_never_got_the_slot_did_not_build_the_change`: a grok row and a `slot not free` composer row; the grok review refused with the word `rebuild`.
- The review launches of `tests/test_bridge_run_review_ceiling.py` and `tests/test_bridge_run_design_ceiling.py`, the latter in a folder that lies in no repository (refused on none of the new grounds).
- `tests/test_bug030.py`, `tests/test_bridge_run_slot.py` and `tests/test_hotfix24a_heavy_slots.py` read the launcher's rows and slot lines; `tests/test_improve_roster_alt.py` and the roster files of Done step 8 load `roster-check.py`, which you do not edit.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions: "The builder's secure-coding rule is ASVS level 2"); the threat model is the Decisions row "The bridge's threat model as a whole" (the agents run as the owner's Windows user, so the boundary is what the programs refuse, check and record) and the row "The roster's resolve's threat model", whose four limits stay (a later run that rewrites an earlier row so that the record still parses; the base found through a ref a builder's run can move; a row dropped by where a later run started, never by what was brought onto the branch afterwards; `clean` disregarding the resolved roster file). **Untrusted inputs, each read strictly:** the run record (it lies in the checkout, where a builder or a reviewer can write); `docs/ROSTER.resolved.json` and its `deviation` entry (a builder or reviewer can write it: a missing, unreadable, malformed or wrongly typed entry, a `built` that is not a list of strings, another model or another branch, never opens the exception); `docs/ROSTER.json`; the report files under `handoff/` (names only, through `built_families`); git's answers (data; a failure is a git that does not answer, never a folder in no repository). The property this increment protects is the reviewer's independence: a review never runs by a model of a family that built the branch, and unknown is never read as nobody having built. `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc` are in force for you. The security auditor reads the diff.

**External services.** None. No network call; `cursor-agent` is a stand-in in every test.

**Values.** No value in this increment is the owner's (rule 52). Every git call the launcher adds is bounded by `bridge_env.GIT_TIMEOUT` (the launcher's existing bound for its git calls, a whole number of seconds) and windowless.

## Diagrams
- `docs/diagrams/D-003-review-round-states.md`, the transition `snapshot_taken --> snapshot_taken` (line 51), which this increment's refusals implement; quoted in part: "review launch refused 125 (... the roster builder model unless the resolved roster's deviation names it as review_b_alt for this branch and the built set is known and the model's family is not in it and the entry's recorded families equal the set as read at the launch, otherwise the refusal says to resolve again, the exception failing closed, a brief named, any family that built the branch, ... or where the set is unknown ... a review by a model of any builder's family the roster file names or a parsing builder row of the branch shows, or every review where the set cannot be read ... or the roster program cannot be loaded), no started line, no run log row". D-003 gains no state or transition. The tests name D-003 in their docstrings as the existing state tests do (the supervisor's).
- `docs/diagrams/D-004-context-dfd.md`, `p_bridge_run` with `ds_runs_log` and `ds_checkout` (lines 167 to 170), quoted:
  ```
  p_bridge_run -->|"kind, limit, seconds, exit, model, branch, boundary, the optional retries, on a builder row the launch's head and clean; never the prompt (R-107)"| ds_runs_log
  ds_runs_log -->|"UNTRUSTED: learned limits; the built set, every builder run of the branch's briefs and never the last alone, ... a review by any builder's family then refused; every review refused where, inside a repository, the record cannot be opened, the head is detached, git does not answer, or the tree holds a report file and the branch's base cannot be found (R-107)"| p_bridge_run
  ds_checkout -->|"UNTRUSTED: the report files the branch adds under handoff/, each needing its brief's builder row, and docs/ROSTER.json's builder families, for the built set (R-107)"| p_bridge_run
  ds_checkout -->|"UNTRUSTED: docs/ROSTER.resolved.json with its deviation entry (...), honoured only where the built set is known, the model's family is not in it and the entry's families equal the set read at the launch; otherwise refused, resolve again (R-107)"| p_bridge_run
  ```
  In the first label, "the launch's head" is the commit the launch started on, written under the key `start_commit` (the design, line 598, and the plan: the existing key `head` holds the program name and stays). The launcher reads `docs/ROSTER.json` and `docs/ROSTER.resolved.json` and writes neither, and writes nothing to the roster's state. If the task cannot be done within these flows, stop and report the conflict instead of deviating.

## Requirements
1. **R1. The family refusal reads the built set.** For a `--kind review` launch of `cursor-agent` with a `--model`, the launcher reads the branch's built set by calling `built_families` once per launch with the record `<folder>/run/launcher/runs.jsonl`, the folder the branch is read in (`workspace_of(argv, folder)`), and the roster's contents and profiles read from `<that folder>/docs/ROSTER.json` where it can be read. Where the status is `known`, a review by a model whose family (`family_of`) is in `families` is refused; a branch built by two families refuses a reviewer of either. Where the status is `empty` (no builder row, or a folder in no repository) nothing is refused on this ground, as on the checkpoint.
2. **R2. An unknown set.** Where the status is `unknown`, a review is refused where the model's family is the family of any builder the roster file names (every profile's `builder`, and a v1 roster's top-level `builder`) or of a builder row of the branch that parses (`parsing_rows`). Where the roster file cannot be read, the resolved file's `builder` stands in for the roster file's builders; where neither can be read, every review is refused. A v1 roster's top-level `review_b` may be counted beside its `builder` (the roster program's `_roster_builder_families` counts it); the acceptance tests pass either way. The refusal names the cause (each unknown cause's label) and says that the roster is resolved again.
3. **R3. A set that cannot be read.** Where the status is `unreadable` (inside a repository: the record cannot be opened, the head is detached, git does not answer, or a report file in the tree and the branch's base not to be found), every review launch is refused, the refusal naming the cause (`detached`, `runs.jsonl`, `git` or `main`). A launch from a folder that lies in no repository is refused on none of these grounds, as on the checkpoint.
4. **R4. The roster program cannot be loaded.** Where `roster_program()` raises, or the module lacks `built_families` or `family_of`, a review launch is refused with exit 125, the refusal naming the cause and `bridge-check.py` (the installed tree's check); no note-and-launch path remains for a review. A builder launch is unaffected (it never loads the roster program for this).
5. **R5. The family refusal's words.** Every family refusal (R1, R2) names the model, its family and the built set (or the families it is refused for), and keeps the family's name, the word `rebuild`, and the words `is of the <family> family` (for example `is of the xai family`), which existing tests read. Every refusal text is ASCII (through `_ascii_refusal` as today) and prints no traceback on any record, roster, resolved file or git answer.
6. **R6. The builder-model refusal and its one exception.** `review_launch_refusal` keeps refusing a review on the resolved roster's builder model, and lets it through only where all hold: the resolved file reads as a JSON object whose `deviation` is an object; `deviation["review_b_alt"]` equals the model; `deviation["branch"]` equals the current branch (the branch the built set is read for); the built set's status is `known`, or `empty` with `deviation["built"]` an empty list (the design's table row 4 resolves the alternate where nothing was built; the supervisor's ruling, so that the resolve and the launcher never deadlock); the model's family is not in it; and `deviation["built"]` is a list of strings equal, as a set, to the set read at this launch. Otherwise it refuses, the refusal saying to resolve the roster again: no entry, another branch's entry, another model's entry, an unreadable or malformed resolved file or entry, an unknown or unreadable set, a set that differs from the entry's `built`, and a set that holds the model's family. The refusal of a brief named in a review launch stands as it is. A model let through by the exception still meets the family refusal (R1 to R4); nothing skips it for the alternate.
7. **R7. A row on a line of its own.** `write_log` begins a new line first where the record exists and its last byte is not a line feed, then appends the row and its line feed, so a torn last line damages no later row; a record that is empty or ends with a line feed gets no extra blank line. Its other behaviour stays (written only where `<folder>/run` exists; an `OSError` never stops a run).
8. **R8. `start_commit` and `clean` on every builder row.** Every row of `kind` `builder` the launcher writes (the `slot not free` row included) carries `start_commit`, the full object name of the commit `HEAD` names when the launch starts, and `clean`, JSON `true` exactly where the working tree and the index show no change outside `docs/ROSTER.resolved.json`: an uncommitted change (staged or not) to any other tracked file, or an untracked file that is not ignored, makes it `false`; a change to `docs/ROSTER.resolved.json` alone leaves it `true`. Both are read in the folder the row's branch is read in (Context: `workspace_of` on the command as given, a worktree builder's among them), before the child starts. Where git does not answer or the folder lies in no repository, `start_commit` is `null` and `clean` is `false`, never `true`. No other key of the row changes; `head` stays the program name. Rows of other kinds gain neither key.
9. **R9. Step 3b's order holds.** Through the launcher, with a stand-in for `cursor-agent`: a grok builder row, the reset to the checkpoint, a resolve that rewrites the resolved roster, the builder launch writing its own row, and the next resolve printing no REBUILD (the acceptance test of this order; it is red where `clean` is taken from git's status as it stands, unfiltered).
10. **R10. Git calls.** Every git call you add is a list of arguments, never a shell, `creationflags=NO_WINDOW`, bounded by `bridge_env.GIT_TIMEOUT`, its output captured and decoded without raising (a path that is not valid UTF-8 in git's output must not raise); a timeout, a failure to start or an unexpected exit is git not answering.
11. **R11. Nothing else changes.** No new dependency, no new import of a bridge module (the launcher already loads `roster-check.py` through `roster_program()` and imports `bridge_env`), no change to the other refusals, the ceilings, the heavy slots, the started line (the first line on standard error) or the exit codes. MANIFEST regenerated with `python tools/make-manifest.py`; the command reference regenerated with `python tools/dump-cli.py` and `--check` green.

## Acceptance criteria
- [ ] Every test in `tests/test_improve_roster_launch.py` passes (it names R-107 and TASK-086b), unedited; a skip only by the test's own condition, its reason quoted from `-rs`; the cases that passed on the checkpoint still pass (the runs before your first edit and after your last, both quoted).
- [ ] Every test in `tests/test_hotfix25a_roster_launcher.py` passes, unedited (the changed test and the case beside it among them).
- [ ] Every test file of Done steps 7 and 8 passes unedited (a failure of `check_row` in the task032 files only where the Context's precondition is missing, reported by id).
- [ ] The family refusal, the unknown and unreadable sets, the loader failure, the builder-model exception, the row's two keys and the new-line rule behave as R1 to R10 say.
- [ ] `python tools/dump-cli.py --check` passes; MANIFEST regenerated; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `bridge/cursor-bridge/VERSION` reads `2026.11.24a` and is not listed by `git status --short`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes; every git call you add is windowless and bounded.
- [ ] Every line you add is ASCII.
- [ ] R-107's launcher part is fully met, with no stand-in, placeholder or "later" text; the tests naming R-107 are the supervisor's acceptance tests.
- [ ] No new dependency. No new Semgrep high finding. No exception escapes as a traceback on any record, roster file, resolved file or git answer (ASVS L2).

## Constraints
- Do not add dependencies (the standard library, `bridge_env` and the roster program as already loaded only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- No secret is needed or used. Refer to `.env` and configuration keys by name only; never reproduce a value.
- Do not edit `tests/test_improve_roster_launch.py`, `tests/test_hotfix25a_roster_launcher.py` or any other test file. If an acceptance test and this brief seem to disagree, or a test seems to pin something this brief does not say, stop and report it by its test id; do not work around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`, at its end. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No paths of this computer, no user names.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder, `<tmp>` for a temporary folder and `~` for the home folder, including in quoted command output.
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; the module's `NO_WINDOW`). Capturing output does not prevent the window.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"): `bridge-run.py` and `roster-check.py` run only through the tests, in their scratch repositories.
- No value in this increment is the owner's (rule 52).
- Follow existing conventions in the file you touch: refusals returned as a reason string and printed by the caller as `bridge-run: refused - <reason>` with exit 125, `_ascii_refusal` for their text, `NO_WINDOW` and `bridge_env.GIT_TIMEOUT` for git calls.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section, where that file is listed after the manifest's regeneration.
- Numbers: an exit code is the integer `subprocess` returns; the record's and the resolved file's contents are read with `json.load`/`json.loads`; `start_commit` is written as git prints it, stripped of its line end, and accepted only as 40 or 64 hexadecimal digits; nothing is parsed by slicing a string.
- **A probe runs only as a test.** Run no Python other than the Done section's commands: no `python -c`, no here-document, no script of your own. Where you need a scratch check, write it as a test file under `tests/` (a name starting `test_task086b_scratch_`), run it with `python -m pytest -p no:cacheprovider -q <that file>`, and delete it after the run; none stays in the diff, and the report names each one, what it showed and that it was deleted.
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root, with no `PYTHONPATH` or other environment change. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation: name the code points, run nothing.** The supervisor's mutants file sweeps the two functions and the row's keys after your run. Your report lists, for each rule by its label, the function and the line(s), as the file stands after your change, that a mutation of the rule would touch, and the acceptance test id you expect to catch it: M1 a change outside the resolved roster ignored for `clean`; M2 the resolved roster's own change counted against `clean`; M3 the last run read in place of the set; M4 the branch not compared (the deviation's `branch`); M5 the entry honoured for any model; M6 the entry honoured from an unreadable file; M7 the entry honoured where the set is unknown; M8 the entry honoured where its `built` differs; M9 the family refusal skipped for the alternate. Add, for R3, R4 and R7: M10 an unreadable set read as empty; M11 the loader failure noted and the review launched; M12 the new line not begun after a torn last line.
- **Known failures.** The acceptance file and the changed hotfix25a case are red on the checkpoint by design. If any other test fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `built_families`, `family_of`, `norm_entry`, `roster_builder_model`, `branch_of`, `workspace_of`, `_ascii_refusal`, `NO_WINDOW`, the standard library; write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-086b-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name (Constraints).

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for R1 to R11, one line each on what meets it, naming the functions and their lines as the file stands after your change; for R2, R3, R4 and R6 one refusal line of each kind as a test prints it; for R8 one builder row as a test writes it;
- every scratch test file you wrote under `tests/`, what it showed, and that it was deleted (or `no scratch test file`);
- the code points of M1 to M12 (Constraints), each with the function, the lines and the test id you expect to catch it;
- any case you found missing from the acceptance file, named;
- the output of `claude --version` (Done step 13), or the line saying the command is not on PATH in this session;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: what you assumed · why · what would confirm it, one item per line. Examples of the kind expected: how `git status --porcelain` names `docs/ROSTER.resolved.json` where the launch folder is a subfolder of the repository or a worktree; whether an ignored `run/` folder in every project keeps the launcher's own pid file and record out of `clean`; how `git rev-parse HEAD` answers on an unborn branch; that `built_families` reads a branch given by the launcher the same as the one it reads itself. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change. Steps 1 and 2 before your first edit; steps 3 to 14 after your last edit, in this order:
1. `git status --short`
2. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_launch.py tests/test_hotfix25a_roster_launcher.py` (the checkpoint's run: quote the summary line and every failing id)
3. `python tools/dump-cli.py` then `python tools/dump-cli.py --check` (it must pass)
4. `python tools/make-manifest.py`
5. `git status --short` (if `bridge/cursor-bridge/VERSION` is listed, run `git restore bridge/cursor-bridge/VERSION` and run `git status --short` again)
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_launch.py tests/test_hotfix25a_roster_launcher.py`
7. `python -m pytest -p no:cacheprovider -q -rs tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_r4.py tests/test_task032_supervisor_guard.py tests/test_d003_review_round_states.py tests/test_bridge_run_review_ceiling.py tests/test_bridge_run_design_ceiling.py tests/test_bug030.py tests/test_bridge_run_slot.py tests/test_hotfix24a_heavy_slots.py`
8. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_alt.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_a4_review_fixes.py tests/test_program_roster_sign_in.py tests/test_dump_cli.py`
9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `git diff --stat HEAD`
12. `git diff HEAD -- bridge/cursor-bridge/bridge-run.py` (read it for any non-ASCII character you added; say in the report that none was added, or name it)
13. `claude --version` (quote its line; where the command is not found, quote the shell's line saying so; nothing else depends on it)
14. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed, and no `tests/test_task086b_scratch_` file; if either is, report it)

Steps 7 and 8 cover the existing tests that launch reviews and builders through `bridge-run.py`, or load or read `roster-check.py`. All of them are outside Scope, and a failure in any of them is reported by test id, never fixed in that file.

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Each pytest summary line is quoted verbatim; never restate a count in prose. A claim that a check passed quotes the output line that shows it, and a number of failing or skipped cases is backed by the pytest lines naming them (`-rs` prints each skip's reason). A command you did not run is written `not run`, never described as run. Run this brief's test commands once more after your last edit, and write the report's results after step 14, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
