---
record: brief
header: 1
id: "TASK-064"
round: 1
satisfies: [R-083, R-084]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/conformance-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_branch_rule.py", "tests/test_review_guard.py", "tests/test_release_s_records_gate.py", "tests/test_conformance_check.py", "tests/fixtures/github/", "docs/BUILDER_NOTES.md", "handoff/TASK-064-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-064: One reader of the branch rule, the auto-merge line and the closing word (R-083, R-084)

## Objective
Give the bridge one reading of what GitHub says about a repository, in `bridge/cursor-bridge/bridge_env.py`: a branch's required check contexts (the union of the classic branch protection and the rules that apply to the branch, each context with the app its rule names), the repository's auto-merge setting and default branch, a pull request's base and head, and a head's check runs, commit statuses and workflow runs, read page by page; beside them one function that keeps the latest entry of each source and one that classes an entry as passed, pending, skipped or failed. Every reading answers one of three things, told apart by the caller: a value, none, or cannot read (with its reason and its source), and cannot read is never returned as none. Three programs will use this reader; this increment wires two of them: `conformance-check.py` replaces its own reading of the required contexts with the call (printing a NOTE where it printed `MISSING` for a rule it could not read), and `review-guard.py`'s `premerge` and `premerge-records` print the repository's auto-merge setting as one more line after their verdict. In the same program, the closing `GATE-INTEGRITY` line of `verify` and of `premerge` says `deleted` where the snapshot was deleted and `rewritten` where it was rewritten. The `ready` command and the launcher's wait that will call the head readers are later increments (TASK-083 and others); they are not built here.

Satisfies: R-083 - One reader of a repository's branch rule, and the proof that CI passed as a program (T-CONTEXT, C7): `bridge_env.py` reads a branch's required check contexts, from the classic protection and from the rules that apply to the branch, each with the app its rule names, the branch's name percent-encoded in the path, and the repository's auto-merge setting, by GET through `gh api`, each returning the value, none, or cannot read with the reason, none only for the reply of a branch with no protection, matched exactly, and for a success from either source that names no required check, cannot read wherever a source answers anything else that is not a success, and `conformance-check.py` calls it for the reading it had, printing for a rule that cannot be read a NOTE that says so and that `ready` answers `CANNOT CHECK` on that branch for this login, where it printed `MISSING`; [...] `premerge` and `premerge-records` print, after their verdict and never changing it, `auto-merge is on for this repository`, `auto-merge is off for this repository` or `auto-merge setting not read`, and no armed form; [...]. (Full text: its row in `docs/REQUIREMENTS.md`. This brief serves the reader, the conformance check's use of it, the head readers and the two functions `ready` will use, and the auto-merge line; `ready`, its record, the permission guard's refusal and the loop's text are other increments.) R-084 - The closing line of `review-guard.py verify` and of `premerge` says `deleted` where the snapshot was deleted and `rewritten` where it was rewritten (C23); no branch of either changes.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_branch_rule.py
- tests/test_review_guard.py
- tests/test_release_s_records_gate.py
- tests/test_conformance_check.py
- tests/fixtures/github/
- docs/BUILDER_NOTES.md
- handoff/TASK-064-r1-report.md

Limits on these paths:
- `tests/test_program_branch_rule.py` and everything under `tests/fixtures/github/` are the supervisor's acceptance tests and recorded replies. They are in Scope because the plan lists them; you read and run them and **edit neither**: no change, no new file under `tests/fixtures/github/`, no deletion.
- `tests/test_review_guard.py`, `tests/test_release_s_records_gate.py` and `tests/test_conformance_check.py`: add your own cases where needed (Requirements 12-14); change no existing case, except where an existing case pins the very output this increment changes by design (the new auto-merge line, the `deleted` word), and then name that case and the change in the report.
- `bridge/cursor-bridge/MANIFEST.json` changes only by being regenerated with `python tools/make-manifest.py` (Done). Never edit it by hand.
- `bridge/cursor-bridge/VERSION` is outside Scope; it reads `2026.11.12a`. `make-manifest.py` rewrites its line endings; restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done), and edit it in no other way.
- `bridge/cursor-bridge/review-guard.py`: only `snapshot_rewritten` (line 318), the closing lines of `cmd_verify` (line 993) and `cmd_premerge` (line 1193), and the end of the success paths of `cmd_premerge` (after line 1259) and `cmd_premerge_records` (after line 1515). No other command, message or exit changes.
- `bridge/cursor-bridge/conformance-check.py`: only the block under `# --- the repository on GitHub (read-only)` (lines 905-929) that reads the required contexts. Its `gh` helper (line 494) stays for its other calls.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ belongs to the supervisor; `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` do not change (`python tools/dump-cli.py --check` must exit 0; if it fails, say so in the report and change nothing).
- `review-guard.py ready`, the ready record and the launcher's wait before a CI watch (TASK-083 and the launcher's increment): do not add a `ready` command, a ready record, or any caller of `pull_refs`, `head_state`, `latest_of_each` or `ci_class` outside `bridge_env.py`.
- `bridge/cursor-bridge/bridge-run.py` and `bridge/cursor-bridge/permission-guard.py`, and every other program under `bridge/cursor-bridge/`.
- The docstrings' exit lists of `review-guard.py` and `conformance-check.py` (J14 is TASK-083's and TASK-072's).
- `tools/make-manifest.py`, `tools/dump-cli.py`, and every test file not named in Scope (you run some of them, Done, and edit none).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this increment:** `docs/DESIGN.md`, "Change: the program release", section "What changes - the items by home", the bullet group **The review guard, `review-guard.py`, and the rule's reader in `bridge_env.py`**: the bullets *The rule's reader*, *C7* and *C23* (read them whole), and "GitHub's facts" (the table under "The host - Claude Code"), "Security and secret handling" (bullet **GitHub reads**), "Testing strategy" and "Failure modes" (its first sentence names this increment). The decision row: `docs/INVENTORY.md`, Decisions, the row beginning "The proof that CI passed is a program, and the branch rule has one reader".

**The supervisor's acceptance tests** (read the file whole; it fixes the interface): `tests/test_program_branch_rule.py`. It runs every case on GitHub's replies recorded once from this repository on 2026-11-16 (`tests/fixtures/github/*.json`; each file's `fixture` field says `captured` or `built`, a built one naming the captured reply it was made from, and each holds `request`, `status`, `gh_exit`, `gh_stderr` and `body`). A stand-in program the test writes plays `gh`: the test sets `bridge_env.GH_COMMAND` to `[sys.executable, <stand-in>, <routes file>]`; the stand-in answers `api <path>` by the path, its query (`per_page` aside, `page` 1 by default) and the owner and repository read as the placeholders `OWNER`/`REPO`; it writes the recorded `body` as JSON on standard output, `gh_stderr` on standard error, and exits with `gh_exit` (as real `gh api` does on an HTTP error: the reply's body on standard output, `gh: <message> (HTTP <n>)` on standard error, exit 1); a path it has no route for answers GitHub's 404 `Not Found`; anything but a plain GET (a `-X`/`--method` other than GET, `-f`, `-F`, `--field`, `--raw-field`, `--input`, `--paginate`) exits 99. On the code as it stands, `python -m pytest -q tests/test_program_branch_rule.py` gives `51 failed, 2 passed` (run/agent/TASK-064-known.out). All 53 must pass.

**The recorded replies you will meet** (examples, read the others in the folder): `protection-main.json` (200, `contexts` and `checks` each with `app_id` 15368); `protection-release-none.json` (captured: status 404, `gh_stderr` `gh: Branch not protected (HTTP 404)`, body `{"message": "Branch not protected", "status": "404"}`, the status in the body being a string); `protection-not-enabled.json` (built: 404 `Required status checks not enabled`); `not-found.json` (404 `Not Found`); `rules-unreadable.json` (built: 403 `Resource not accessible by integration`); `rules-app-lint.json` (a list of rules, each with `type` and `parameters.required_status_checks`, a context optionally with `integration_id`); `check-runs-two-page1.json` (`total_count` 2, one entry in `check_runs`); `status.json` (combined status: `state`, `total_count`, `statuses`); `runs.json` (`total_count`, `workflow_runs`, each with `workflow_id`, `event`, `run_number`, `run_attempt`, `status`, `conclusion`, `check_suite_id`).

**The code as it stands.**
- `bridge/cursor-bridge/bridge_env.py` has no GitHub call today. Its conventions: ASCII only (module docstring, line 23), `NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0` (line 36), subprocess calls with `capture_output=True`, `creationflags=NO_WINDOW` and a `timeout` (for example `squash_merged_ids`, lines 1284-1308), failures returned as values rather than raised (`except (OSError, subprocess.TimeoutExpired): return None`). `gh_empty_dir()` (line 67) is the folder `stripped_env` gives `gh` as `GH_CONFIG_DIR` to log a builder out; it is not a call helper and the reader does not use it (the reader runs with the owner's login, in the supervisor's session).
- `bridge/cursor-bridge/review-guard.py` imports `bridge_env` with a plain `import bridge_env` (line 104) and has `NO_WINDOW` (line 107). `snapshot_rewritten(common, nnn)` (lines 318-336) prints an indented `  GATE-INTEGRITY  the snapshot was deleted after it was taken: ...` or `  GATE-INTEGRITY  the snapshot was rewritten after it was taken: ...` line, but returns `"rewritten"` for both, so the callers cannot tell them apart. `cmd_verify` (line 983) then prints, at line 993, `review-guard: GATE-INTEGRITY - the snapshot was rewritten after it was taken; the checkout was NOT restored from it and no git command was run`, calls `record_flagged_launch(common, root, nnn, None)` and returns 1. `cmd_premerge` (line 1185) prints, at line 1193, `review-guard: GATE-INTEGRITY - do not merge; the snapshot was rewritten after it was taken` and returns 1. `cmd_premerge`'s success path ends (lines 1247-1260) with the `review-guard: OK - ...` verdict, the premerge record written under `<common>/bridge/premerge/<head>`, then `review-guard: merge with  gh pr merge ...` and `return 0`. `cmd_premerge_records(cwd, pr=None)` (line 1447) ends its success path (lines 1506-1516) with the record written, `review-guard: OK - records only, ...`, `review-guard: merge with  gh pr merge ...` and `return 0`. `main()` (line 1519) runs every command with `os.getcwd()`, the checkout.
- `bridge/cursor-bridge/conformance-check.py` loads `bridge_env` by file through `_load_bridge_env()` (lines 97-122), which falls back to a stub module holding only `is_link` when `bridge_env.py` is absent; the program already guards a newer helper with `hasattr(bridge_env, "status_values")` (line 758). Note: the module it loads is a separate module object from the one `import bridge_env` gives a test, so a test patches the conformance module's own `bridge_env` attribute. Its `gh(args, cwd)` helper (lines 494-501) runs `["gh"] + args` with `GH_TIMEOUT = 25` (line 131). The block at lines 905-929, quoted:

```python
    # --- the repository on GitHub (read-only)
    if offline:
        add("NOTE", "Required check on the default branch", "not checked (--offline)")
    else:
        out, err = gh(["repo", "view", "--json", "nameWithOwner,visibility,defaultBranchRef"], ws)
        if out is None:
            add("NOTE", "Required check on the default branch", "cannot verify through gh (%s)" % (err or "no output"))
        else:
            try:
                info = json.loads(out)
                nwo = info["nameWithOwner"]
                branch = (info.get("defaultBranchRef") or {}).get("name") or "main"
                if str(info.get("visibility", "")).lower() == "public":
                    add("NOTE", "Repository visibility", "%s is public: the diffs, briefs and records are readable by anyone (plan review R4)" % nwo)
                checks, err2 = gh(["api", "repos/%s/branches/%s/protection/required_status_checks" % (nwo, branch)], ws)
                if checks is None:
                    add("MISSING", "Required check on the default branch", "no branch protection with a required status check on %s (%s); N6 needs the gate job required" % (branch, (err2 or "")[:80]))
                else:
                    contexts = json.loads(checks).get("contexts") or [c.get("context") for c in json.loads(checks).get("checks") or []]
                    if contexts:
                        add("OK", "Required check on the default branch (%s)" % ", ".join(str(c) for c in contexts[:4]))
                    else:
                        add("MISSING", "Required check on the default branch", "branch protection exists but requires no status check; N6 needs the gate job required")
            except (ValueError, KeyError, TypeError) as e:
                add("NOTE", "Required check on the default branch", "cannot read gh's answer (%s)" % e)
```

  Today any reply that is not a success (a refusal, `Required status checks not enabled`, the network) prints `MISSING` as for a branch with no protection; that is the defect the NOTE replaces. `tests/test_conformance_check.py` today reaches this block only with `--offline` (line 114).

**External service (the trait External services).** GitHub's REST API, through `gh api`, is a service run by others. Each call has a **time limit of `GH_API_TIMEOUT` = 30 seconds** and a **retry limit of 0** (no retry of its own: a reply that is not a success is read once and answered as cannot read). "Done" means passing on the recorded replies in `tests/fixtures/github/` through the stand-in, never on a reply you invent. If a case you need has no recorded reply, do not make one up and do not add a fixture: stop and report it (a capture is the supervisor's to run). No test of yours, and no command you run, calls the real GitHub.

**Security context.** ASVS level 2 (INVENTORY, Decisions, "The builder's secure-coding rule is ASVS level 2"); `.cursor/rules/secure-coding.mdc` is in force for you. GitHub's reply is **outside input** (INVENTORY, Decisions, the row "The bridge's threat model as a whole": "outside input is ... what a program reads from GitHub or another service"): a reply the reader cannot read, or one it does not recognise, is never taken as none or as a pass; it is cannot read, with GitHub's message as the reason, cut to a bounded length and printed as text only. The reads are made with the owner's `gh` login, GET only (DESIGN, "Security and secret handling", **GitHub reads**); no token, account name or repository name is printed beyond what `gh` already prints today, and no reply is written to a file.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: run the programs only from tests, on scratch repositories under pytest's `tmp_path` and on the recorded replies; never install anything, never copy under `~/.claude`, never run `review-guard.py` or `conformance-check.py` against this repository's own folder or its GitHub repository.

**A side effect to watch.** Several existing test files run `review-guard.py premerge` as a child process in scratch repositories that have no GitHub remote (`tests/test_task032_supervisor_guard.py`'s `guard()` helper, used by `tests/test_bug039.py`, `tests/test_bug041.py`, `tests/test_hotfix25a_guard_scope_invisible.py`, `tests/test_d003_review_round_states.py` and others). After this change their premerge success path calls the real `gh api repos/{owner}/{repo}`, which cannot resolve `{owner}/{repo}` there and should answer `auto-merge setting not read`. Run the files the Done section names and report, by test id, any case this changes (a pinned last line, a slower run); edit none of them, and add no environment variable or option to avoid the call (the interface is fixed).

**Host.** Windows 11; Python as on the owner's interpreter; `gh` 2.97.0 was the version of the captures. Do not run `gh` yourself.

## Diagrams
`docs/diagrams/D-002-components.md`: elements `bridge_env` (`bridge/cursor-bridge/bridge_env.py`), `review_guard` (`bridge/cursor-bridge/review-guard.py`), `conformance_check` (`bridge/cursor-bridge/conformance-check.py`). The edges that stand and that this increment keeps, quoted:

```mermaid
    review_guard --> bridge_env
    conformance_check -.-> bridge_env
```

The rule's reader lives inside `bridge_env` (DESIGN, "Architecture - the diagrams the change touches", D-002: "`bridge_run` and `conformance_check` gain no edge ... the rule's reader is inside `bridge_env`"). Add no import between bridge programs: `review-guard.py` keeps its plain `import bridge_env`, `conformance-check.py` keeps its load by file, and `bridge_env.py` imports no bridge program. Standard-library imports in `bridge_env.py` (for example `urllib.parse` for the encoding) are allowed.

`docs/diagrams/D-004-context-dfd.md`: `ext_github` and `p_review_guard`, the flows quoted:

```mermaid
p_review_guard -->|"SECRET: owner's gh login, GET only, the rule's reader in bridge_env: ready, premerge-records (R-083)"| ext_github
ext_github -->|"a branch's required check contexts, the default branch's contexts, allow_auto_merge, the PR's head, its checks, commit statuses and workflow runs"| p_review_guard
p_review_guard -->|"READY, NOT READY, CANNOT CHECK; the auto-merge line"| p_supervisor
```

Every call is a GET; nothing is sent to GitHub but the path. The conformance check's read of the same rule is not drawn (DESIGN, D-004). If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
Use the labels R1-R14 in your report.

1. **R1. The one command and its limits.** `bridge_env.GH_COMMAND` is a list, default `["gh"]`; every GitHub call runs `GH_COMMAND + ["api", <path>]` and nothing else (no `-X`/`--method` other than GET, no `-f`/`-F`/`--field`/`--raw-field`/`--input`, no `--paginate`). `bridge_env.GH_API_TIMEOUT` = 30 (seconds) is the time limit of each call. Both are read **at call time** (the tests replace them on the module after it is imported). No retry: one call per path and page. Each call is windowless (`creationflags=NO_WINDOW`), its standard input not inherited (`stdin=subprocess.DEVNULL`), its output captured and decoded as UTF-8 with replacement. A call that cannot start (`gh` absent), that passes its time limit, that exits non-zero, or whose output is not the JSON shape expected is a reply that is not a success, answered by the reading as cannot read with a reason; nothing raises to the caller. The time-out ends the call: the test's slow stand-in with a 1-second limit must leave `branch_rule` answering within 5 seconds.
2. **R2. The three answers.** Constants `ANSWER_VALUE = "value"`, `ANSWER_NONE = "none"`, `ANSWER_CANNOT = "cannot read"`. Every reader below returns a dict with `answer` (one of the three), `reason` (a non-empty string where the answer is cannot read) and `source` (naming the source that could not be read where the answer is cannot read), plus its own keys.
3. **R3. `branch_rule(repo, branch)`** returns also `contexts`, a list of `{"context": str, "app_id": int or None}`. `repo` is `"OWNER/NAME"` or gh's own placeholder form `"{owner}/{repo}"`, passed through as given. The branch's name is percent-encoded (every character outside the unreserved set, the slash included) in both paths: `repos/<repo>/branches/<b>/protection/required_status_checks` and `repos/<repo>/rules/branches/<b>` (`release/2026.11.03` becomes `release%2F2026.11.03`; no call carries the raw slash). `contexts` is the union of the classic protection's checks (each `checks[].context` with its `app_id`; a context listed in `contexts` only, with no `checks` entry, carries `app_id` None) and the `parameters.required_status_checks` of every rule of type `required_status_checks` in the rules reply (each `context` with its `integration_id` as `app_id`, None where it names none). Answers:
   - **none** only for: the classic endpoint's reply for a branch with no protection (matched exactly: a 404 reply whose body's `message` is `Branch not protected` and whose `status` is `"404"`, as `protection-release-none.json` shows) together with a success from the rules endpoint; or successes that name no required check (an empty rule list, rules of other types only, a protection with no context); `contexts` is `[]`.
   - **cannot read** for every other reply that is not a success from either source (a 403 refusal, 404 `Required status checks not enabled`, 404 `Not Found`, a time-out, `gh` absent, an unreadable body), **whatever the other source names**: never none, and never the other source's contexts in its place; `source` holds `protection` or `rules` for the source that failed, `reason` GitHub's message or the failure.
   - **value** where at least one context was read and neither source failed.
4. **R4. `repo_settings(repo)`** reads `repos/<repo>` and returns also `allow_auto_merge` (the boolean as given) and `default_branch`; a reply that is not a success, or one without a boolean `allow_auto_merge`, is cannot read.
5. **R5. `pull_refs(repo, number)`** reads `repos/<repo>/pulls/<number>` and returns also `base` (the base ref's name) and `head` (the head commit's sha); otherwise cannot read.
6. **R6. `head_state(repo, sha)`** returns also `checks` (from `repos/<repo>/commits/<sha>/check-runs?filter=all`, the reply's `check_runs`), `statuses` (from `repos/<repo>/commits/<sha>/status`, the reply's `statuses`) and `runs` (from `repos/<repo>/actions/runs?head_sha=<sha>`, the reply's `workflow_runs`). Each list is asked page by page with `page=` and `per_page=` query parameters until the number of entries read reaches the `total_count` its reply states; a page that is not a success, a page that adds no entry before the count is reached, or a count that is not an integer makes that list, and so the whole answer, cannot read, **never a shorter list**. The loop ends in every case (it cannot ask pages without bound). Any one of the three lists not read whole makes `answer` cannot read with that list as `source`.
7. **R7. `latest_of_each(state)`** takes a dict with `checks`, `statuses` and `runs` and returns the same three keys, each holding only the latest of each source (DESIGN, *T-CONTEXT*; BUILD_PLAN TASK-064 "Done when"):
   - a run by its `workflow_id` and `event`, the latest by `run_number`, then `run_attempt`;
   - a check a workflow run made (its `check_suite.id` equals some run's `check_suite_id`) counts only where that run is a latest run; of several checks of one `name` in that run the last one, where a check that is not completed ranks after every completed one, and the completed are ordered by `started_at` then `id`, by `id` alone where one of them carries no `started_at`;
   - a check no workflow run made, by its `name` and its app id (`app.id`), in the same order;
   - a status by its `context`, the latest by `updated_at`.
   The function reads only these fields and keeps each kept entry as given.
8. **R8. `ci_class(item, kind)`**, `kind` one of `"check"`, `"run"`, `"status"`, returns `"passed"` (a check or run with `status` `completed` and `conclusion` `success`; a status with `state` `success`), `"pending"` (a check or run not `completed`; a status `pending`), `"skipped"` (a check or run completed with `skipped`) or `"failed"` (every other conclusion or state, a value the function does not know included). These are closed lists: nothing unknown is ever passed or pending.
9. **R9. The conformance row.** `conformance-check.py` keeps its `gh repo view` read and its visibility NOTE, and replaces its own protection read (lines 919-927) by `bridge_env.branch_rule(nwo, branch)` for the default branch: for **value** it prints the `OK` row as today (`Required check on the default branch (<the contexts, at most four>)`); for **none** it prints the `MISSING` row with the label `Required check on the default branch` and today's N6 detail; for **cannot read** it prints `NOTE` with the label `Required check on the default branch` and the detail `cannot read the branch rule (<source>: <reply>); review-guard.py ready answers CANNOT CHECK on this branch for this login`, where it printed `MISSING`. The `--offline` NOTE, the `cannot verify through gh` NOTE and the `cannot read gh's answer` NOTE stay as they are. Where the loaded `bridge_env` has no `branch_rule` (the stub of `_load_bridge_env`), the row is a NOTE that says the rule was not read, never `OK` and never `MISSING`. No exit code changes.
10. **R10. The auto-merge line.** `premerge` and `premerge-records`, on their success path, after the record is written and after their last line today (the `review-guard: merge with ...` line), print exactly one more line, read by `bridge_env.repo_settings("{owner}/{repo}")` in the checkout the command runs in: `auto-merge is on for this repository`, `auto-merge is off for this repository`, or `auto-merge setting not read` (any answer other than value). It changes neither the verdict nor the exit code nor the record; it prints no armed form (no `--auto` anywhere in the output). No other path of either command prints it. If you let `repo_settings` take an optional keyword (for example the folder to run in), its tested call `repo_settings(repo)` must work unchanged.
11. **R11. The closing word.** The closing line of `verify` (line 993) says `deleted after it was taken` where the snapshot file was deleted and `rewritten after it was taken` where it was rewritten; the same for `premerge` (line 1193). The rest of each line stays word for word (`review-guard: GATE-INTEGRITY - the snapshot was <word> after it was taken; the checkout was NOT restored from it and no git command was run` and `review-guard: GATE-INTEGRITY - do not merge; the snapshot was <word> after it was taken`). `snapshot_rewritten` may return a distinct value for the deletion so that its two callers tell them apart; its printed lines, its `"missing"` case and its `None` case stay as they are, and no branch of `cmd_verify` or `cmd_premerge` changes otherwise (the `record_flagged_launch` call, the return codes).
12. **R12. Your tests for the conformance row** in `tests/test_conformance_check.py`: the three answers of the row (value: `OK` with the contexts; none: `MISSING`; cannot read: `NOTE` whose detail begins `cannot read the branch rule (`, holding the source, and containing `review-guard.py ready answers CANNOT CHECK`), and that a cannot-read rule never prints `MISSING`. Drive them in process (replace the conformance module's `gh` and its `bridge_env` attribute's `GH_COMMAND`, or its `branch_rule`) or through a stand-in on the recorded replies; never through the real `gh`.
13. **R13. Your tests for the guard** in `tests/test_review_guard.py` and/or `tests/test_release_s_records_gate.py`, where the acceptance tests leave a gap you find: for example that a premerge path that is not a success prints no auto-merge line, and that `premerge-records` without a pull request number prints none. Use the stand-in pattern of `tests/test_program_branch_rule.py` (in process, `guard.bridge_env.GH_COMMAND` replaced) and the recorded replies only.
14. **R14. Naming.** Every case you add names `R-083` or `R-084` (and the D-002 element where it holds a diagram edge) in its name, docstring or a comment; a parametrized case has a plain `ids=` list.

## Acceptance criteria
- [ ] `python -m pytest -q -rA tests/test_program_branch_rule.py` passes whole: 53 passed (it gave `51 failed, 2 passed` before).
- [ ] `python -m pytest -q tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_conformance_check.py` passes whole, your new cases included.
- [ ] `python -m pytest -q tests/test_task032_supervisor_guard.py tests/test_bug039.py tests/test_bug041.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_d003_review_round_states.py tests/test_tests_windowless.py` passes whole; any case it changed is named in the report.
- [ ] Every GitHub call is `GH_COMMAND + ["api", <path>]`, a GET, with the 30-second time limit and no retry, windowless, standard input not inherited (R1).
- [ ] Cannot read is never returned as none and never hidden by the other source's contexts; a list not read whole is cannot read (R3, R6).
- [ ] `conformance-check.py` prints the NOTE for a rule it cannot read where it printed `MISSING`, and its value and none rows as today (R9).
- [ ] `premerge` and `premerge-records` print the auto-merge line after the verdict on their success path, verdict and exit unchanged, no `--auto` (R10).
- [ ] The closing `GATE-INTEGRITY` line of `verify` and `premerge` says `deleted` or `rewritten` as the snapshot was (R11).
- [ ] R-083 (for the parts this brief serves) and R-084 are fully met: no stand-in, placeholder or "later" text in the product code; at least one test names each ID.
- [ ] `python bridge/cursor-bridge/diagram-check.py --mode code` prints `RESULT: OK` (it runs `check:components`: the guard's and the conformance check's edges to `bridge_env` stand, no new edge).
- [ ] MANIFEST regenerated; `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `python tools/dump-cli.py --check` exits 0.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] No option added, no new dependency, no new configuration key or environment variable; no new Semgrep high finding; no exception from a GitHub reply escapes as a traceback, and none is swallowed into a pass (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- Do not edit `tests/test_program_branch_rule.py` or anything under `tests/fixtures/github/`. If a case there seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **External service.** Every call to GitHub has the time limit `GH_API_TIMEOUT` (30 seconds) and a retry limit of 0; add no other wait, no `sleep`, and no retry. Tests replay the recorded real replies in `tests/fixtures/github/` through the stand-in; do not invent a reply's shape, fields, hosts or messages, and add no fixture. If a reply you need is not recorded, stop and report it.
- **Windowless launches.** Every process your code starts is created with `creationflags=NO_WINDOW` (the module's existing constant). In tests a launch needs no `creationflags` argument, because `tests/conftest.py` makes every launch windowless; where a test does write one, that line carries the literal text `CREATE_NO_WINDOW` (`tests/test_tests_windowless.py` refuses it otherwise). Any string in a test that holds Python launch code is written in concatenated parts, so that `tests/test_tests_windowless.py` does not read it as a launch. Every subprocess and git call in a test has a timeout, and each child ends before its test does.
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end; leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section names, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- Do not refactor code outside the functions the Scope's limits name, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data or the real GitHub (Context, "Development data"); do not run `gh` yourself.
- No value in this increment is the owner's (rule 52). The 30-second time limit is the supervisor's, fixed by the interface.
- Follow existing conventions in the files you touch: ASCII program text and ASCII output; results returned as values, not raised.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. Your tests may run git inside their own temporary folders.
- Numbers from a reply are read as JSON gives them and checked for their type: `total_count` and `run_number`, `run_attempt` and `id` are integers (anything else makes the reading cannot read, or ranks as the closed lists say), `app_id`/`integration_id` an integer or absent; times (`started_at`, `updated_at`) are ISO 8601 UTC strings as GitHub gives them, compared with a date parser or as same-format strings, never sliced.
- Every verification command is written in the Done section in full; run exactly those. The mutation check is the supervisor's, after your run, with a mutants file that sweeps the reader (cannot-read taken as none, one source hidden by the other, a context dropped, a source skipped, the branch name not encoded, the first page taken for the list, a run or check kept beside its successor, an unknown conclusion taken as passed, a pending check ranked before a completed one, the conformance row printed `MISSING` for a rule that cannot be read, and more): every one of those must fail a test. You may mutate by hand in process to test a case of yours; if you do, list each mutation and what caught it, and leave no mutation script in the diff.
- **Known failures.** On the code as it stands, `tests/test_program_branch_rule.py` gives `51 failed, 2 passed`; none is known in the other files the Done section runs. If a case fails that this change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: one internal call helper in `bridge_env.py` for every GitHub read, the standard library (`urllib.parse.quote`, `json`, `subprocess`), and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-064-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, what you could not do, so that nothing of it is lost when your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for R1-R14, one line each on what meets it, naming the functions and their lines as the files stand after your change;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: the shape of a GitHub reply beyond the recorded ones, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. Examples: that real `gh api` writes an error reply's body on standard output as the stand-in does; that `gh` resolves `{owner}/{repo}` from the current folder's git remote and fails without one, without a network call, unless `GH_REPO` is set; that the combined-status endpoint honours `page`/`per_page`; the `per_page` value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python -m pytest -q -rA tests/test_program_branch_rule.py`
3. `python -m pytest -q tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_conformance_check.py`
4. `python -m pytest -q tests/test_task032_supervisor_guard.py tests/test_bug039.py tests/test_bug041.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_d003_review_round_states.py tests/test_tests_windowless.py`
5. `python tools/make-manifest.py`
6. `git restore bridge/cursor-bridge/VERSION`
7. `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `python tools/dump-cli.py --check` (expect exit 0; if it fails, say so and change nothing)
10. `python bridge/cursor-bridge/diagram-check.py --mode code` (expect `RESULT: OK`)
11. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
12. `git rev-parse HEAD` and `git status --short`

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block; never restate a count in prose.
- A claim that a check passed quotes the output line that shows it, and a number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 12, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
