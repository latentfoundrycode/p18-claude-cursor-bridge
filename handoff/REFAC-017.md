---
record: brief
header: 1
id: "REFAC-017"
round: 1
satisfies: [R-039, R-107]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-017-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-017: the launcher's HEAD reading through _git_rev_parse, and one reader of docs/*.json

## Objective
Refactoring - remove duplication / simplify **without any change in behaviour**.

This brief carries two candidates of stage I1's refactoring pass, both in `bridge/cursor-bridge/bridge-run.py` (the launcher), in two named parts. Part 1 makes `_git_launch_state` read the commit through the existing `_git_rev_parse` instead of its own copy of the same git call. Part 2 gives three readers of a JSON file under `docs/` one private reading function. The manifest is regenerated after it. Behaviour stays exactly the same: every line the launcher prints, every refusal and its text, every exit code, every field of every run-record row (`start_commit` and `clean` on a builder row included), and every git command the launcher starts (its arguments and its options). This is the launcher: every refusal that reads these values fails closed today and must still do so, and a value that is `None` or `False` today on a failure must stay `None` or `False` on the same failure. Line numbers below are as `bridge/cursor-bridge/bridge-run.py` stands at `8b03c32` (TASK-087c, the base of branch `refactor/I1`). REFAC-015 (`bridge/cursor-bridge/roster-check.py`) and REFAC-016 (`bridge/cursor-bridge/mutation-run.py`) may be committed on this branch before your run: they touch no file of this brief except `bridge/cursor-bridge/MANIFEST.json` (which you regenerate anyway), so `bridge-run.py` must be byte-identical to its `8b03c32` content when you start (Requirement 1 checks it). `bridge-run.py` loads `roster-check.py` at run time (`roster_program()`, line 2618), so REFAC-015 may run under your tests; it is itself a no-behaviour-change refactoring.

**Part 1: `_git_launch_state` reads HEAD through `_git_rev_parse`.**

The copy, `_git_launch_state(ws)`, lines 1241-1262 (the rev-parse HEAD block and its None test):

```python
def _git_launch_state(ws):
    """The commit and clean-tree reading for a builder row, before the child starts."""
    base = ws or "."
    start_commit = None
    try:
        p = subprocess.run(
            ["git", "-C", base, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=NO_WINDOW,
            timeout=bridge_env.GIT_TIMEOUT,
        )
        if p.returncode == 0:
            cand = p.stdout.strip()
            if len(cand) in (40, 64) and all(ch in "0123456789abcdef" for ch in cand.lower()):
                start_commit = cand
    except (OSError, subprocess.TimeoutExpired):
        return None, False
    if start_commit is None:
        return None, False
```

Lines 1263-1301 then run `["git", "-C", base, "status", "--porcelain", "-z", "--untracked-files=normal", "--ignore-submodules=none"]` with the same options and parse its answer (the status block).

The single implementation, `_git_rev_parse(folder, *args)`, lines 3135-3151:

```python
def _git_rev_parse(folder, *args):
    try:
        p = subprocess.run(
            ["git", "-C", folder or ".", "rev-parse"] + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=NO_WINDOW,
            timeout=bridge_env.GIT_TIMEOUT,
        )
        if p.returncode != 0:
            return None
        out = p.stdout.strip()
        return out if out else None
    except (OSError, subprocess.TimeoutExpired):
        return None
```

The packager compared the two at `8b03c32` and they agree exactly: the same argument list for `_git_rev_parse(ws, "HEAD")` (`["git", "-C", ws or ".", "rev-parse", "HEAD"]`, the folder in the `-C` form, no `cwd=`), the same `capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW, timeout=bridge_env.GIT_TIMEOUT` (`GIT_TIMEOUT = 30`, `bridge_env.py` line 416), and neither passes `env=`, so both inherit the process's environment. Each case `_git_rev_parse` turns into `None` (a non-zero exit, an empty answer after `strip()`, `OSError`, `subprocess.TimeoutExpired`) already ends in `(None, False)` in `_git_launch_state` today (an empty answer fails the length test). A non-empty answer is the same stripped string in both.

The change: in `_git_launch_state`, the `try`/`except` block holding the rev-parse call becomes a call `cand = _git_rev_parse(ws, "HEAD")`; the 40/64-hex test stays exactly as it is, written over `cand`; a `None` answer gives `(None, False)` without running the status command and without a `TypeError` (today `len()` is never called on `None`). The docstring, `base = ws or "."` (still used by the status block), the `if start_commit is None: return None, False` test and the whole status block (lines 1263-1301) stay exactly as they are. `_git_rev_parse` itself does not change.

**Part 2: one reader of `docs/<name>.json`.**

The three copies, each opening `os.path.join(<folder>, "docs", <name>)` with `encoding="utf-8", errors="replace"`, calling `json.load(f)`, catching `(OSError, ValueError, RecursionError)` and requiring a dict (read at `8b03c32`; the packager checked the encoding, the `errors` argument and the except tuple are character for character the same in all three):

```python
def roster_builder_model(folder):
    try:
        with open(os.path.join(folder, "docs", "ROSTER.resolved.json"), encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("builder"), str):
            return data["builder"]
    except (OSError, ValueError, RecursionError):
        pass
    return None


def _read_roster_json(ws):
    try:
        with open(os.path.join(ws, "docs", "ROSTER.json"), encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except (OSError, ValueError, RecursionError):
        return None, None
    if not isinstance(data, dict):
        return None, None
    profiles = data.get("profiles")
    ...
    return data, profiles
```

(`roster_builder_model` lines 1201-1209, `_read_roster_json` lines 1212-1228; its profiles checks, lines 1220-1227, stay as they are), and:

```python
def _load_deviation(folder):
    try:
        with open(os.path.join(folder, "docs", "ROSTER.resolved.json"), encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except (OSError, ValueError, RecursionError):
        return None
    if not isinstance(data, dict):
        return None
    deviation = data.get("deviation")
    return deviation if isinstance(deviation, dict) else None
```

(lines 1304-1314).

The change: one private top-level function `_read_docs_json(folder, name)` that returns the loaded object where it is a dict, and `None` where the file cannot be opened or read (`OSError`), does not parse (`ValueError`), is nested too deep (`RecursionError`) or is not a dict. It joins the path as the copies do, `os.path.join(folder, "docs", name)`, with `folder` passed through unchanged (no `or "."`, no normalisation), opens with `encoding="utf-8", errors="replace"`, and catches exactly `(OSError, ValueError, RecursionError)`, nothing wider: an exception none of the copies catches today (for example the `TypeError` of `os.path.join` given `None`) still propagates. Place it directly above `roster_builder_model`. The three functions keep their names, their signatures, their own field checks and their return values on every path: `roster_builder_model` the `builder` string or `None`; `_read_roster_json` `(data, profiles)` or `(None, None)`; `_load_deviation` the `deviation` dict or `None`. Their callers (lines 1329, 1353, 1432, 1439, 2678) do not change.

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.24a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as they are R-107 (an exhausted pool never parks or pauses work, and a reviewer is never of a family that built the change: the launcher writes `start_commit` and `clean` on every builder row, read before the child starts, and its two review refusals read the built set from `docs/ROSTER.json` and the run record and the recorded deviation from `docs/ROSTER.resolved.json`; TASK-086a, TASK-086b) and R-039 (windowless launches are enforced by the bridge: every git command the launcher starts keeps `creationflags=NO_WINDOW`).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-017-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only. `MANIFEST.json` is written only by `python tools/make-manifest.py`, never by hand.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/`, `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser`, no usage text and no module docstring)
- every file under `tests/`, `tests/fixtures/` included: no test file or fixture may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is and report it
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.24a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored; this brief asks you to write no file there (every output goes into the report)
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- `bridge/cursor-bridge/roster-check.py` and `bridge/cursor-bridge/mutation-run.py` (REFAC-015's and REFAC-016's), and every other file under `bridge/`
- in bridge-run.py, every line but Part 1's block in `_git_launch_state` and Part 2's three bodies and the added `_read_docs_json`. In particular these stay exactly as they are, though they look alike: the other git readers `git_common_dir` (line 1180, `rev-parse --git-common-dir`), `branch_of` (line 2580, `rev-parse --abbrev-ref HEAD`) and `local_head` (line 2698, a one-line `rev-parse HEAD` with other options); `_git_rev_parse` and `_git_rev_parse_path`; `_run_parameters_values` (line 1069, which reads `docs/RUN_PARAMETERS.md` as text); the status block of `_git_launch_state`; and every caller of the touched functions

## Context
**What the code is today** (`8b03c32`). `bridge-run.py` has CRLF line endings on every line (3840 lines); keep them, and add no trailing whitespace. It imports `json`, `os` and `subprocess` at the top (lines 109, 111, 116) and `bridge_env` (line 122); `NO_WINDOW` is module-level (line 124). Python resolves `_git_rev_parse` (defined at line 3135, after `_git_launch_state`) at call time, so nothing needs to move. No name touched here is used outside `bridge-run.py`: no program under `bridge/` and no file under `tests/` names `_git_rev_parse`, `_git_launch_state`, `roster_builder_model`, `_read_roster_json`, `_load_deviation` or `_read_docs_json` (Requirement 1 checks it), so no test patches them; the tests reach them through real launches.

**Where the values go, and why each failure must keep its answer.** `_git_launch_state(ws_build)` (line 3609) fills a builder row's `start_commit` and `clean`; R-107's built-set rule drops an earlier builder run only where a later one started on a clean tree at its start commit, so a failure must never give a commit or `clean: true`. `_read_roster_json(ws)` feeds `_built_set_at_launch` (line 1329). `_load_deviation(folder)` decides `_deviation_allows_builder_review` (line 1353, `None` refuses) and the refusal text in `review_launch_refusal` (line 1439, `None` picks the text naming Review B's reviewer model). `roster_builder_model` is read by `review_launch_refusal` (line 1432) and `review_family_refusal` (line 2678, `None` gives the refusal `cannot`).

**How the tests reach this code.** `tests/test_improve_roster_launch.py` (TASK-086b, R-107) launches builders against scratch repositories and checks `start_commit` and `clean` on the row: on a clean tree, with an untracked file, in a worktree, in a folder in no repository (`test_r8_a_builder_row_in_a_folder_in_no_repository_has_no_commit_and_is_not_clean`) and where git fails or does not start (`test_r8_r10_a_builder_row_where_git_does_not_answer`, both `None`/`False`); and it drives the two review refusals with and without a recorded deviation. `tests/test_hotfix25a_roster_launcher.py` and `tests/test_task032_supervisor_launcher.py` drive the launcher's roster and review refusals and check the row's keys (`start_commit`, `clean` among them). `tests/test_bridge_run.py`, `tests/test_bridge_run_design_ceiling.py`, `tests/test_bridge_run_review_ceiling.py`, `tests/test_bridge_run_driver.py`, `tests/test_bridge_run_slot.py` and `tests/test_hotfix24a_heavy_slots.py` cover the rest of the launcher (R-040's and R-137's slots, R-042's ceiling). `tests/test_header_currency.py` reads `bridge-run.py`'s syntax tree and is in the command as the guard of its names. All of these must stay green unedited. Some cases may be skipped on Windows (for example the no-repository case where the temporary folder lies inside a repository); the skip count must be the same before and after.

**The expected count.** No supervisor baseline is given for this command. Your before-edit run is the baseline, and the after-edit run must match it (the same count passed, none failed, the same count skipped). If a test fails before your edit, stop and report it.

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for `bridge-run.py`; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.24a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.24a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.24a`. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** The trust boundaries are the project's `docs/ROSTER.json` and `docs/ROSTER.resolved.json` (files an agent can write, so their content is untrusted: any shape, any size, any nesting) and git's answer about the Workspace. Each reading fails closed today: a file that is missing, unreadable, malformed, too deeply nested or not a JSON object gives `None` (or `(None, None)`), and a git that fails, times out, does not start or answers anything but a 40- or 64-hex object name gives `(None, False)`. The change moves no boundary: the same files are opened the same way, the same exceptions are caught (none wider), the same shapes are refused, and the git command is the same. `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions).

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders and the repositories they create there. Never run `bridge-run.py`, `roster-check.py` or `bridge-install.py` yourself, against this repository or any other, and never run `gh`.

## Diagrams
`docs/diagrams/D-002-components.md`: the element `bridge_run` (`bridge/cursor-bridge/bridge-run.py`), whose edges already exist:

```mermaid
    bridge_run --> bridge_env
    bridge_run -.-> roster_check
```

The change adds no import and no edge, so the diagram does not change. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run:
   - `git diff --stat 8b03c32 -- bridge/cursor-bridge/bridge-run.py tests`. Expected: nothing (the file and the tests are as at `8b03c32`).
   - `git grep -n -w -e _git_rev_parse -e _git_launch_state -e roster_builder_model -e _read_roster_json -e _load_deviation -e _read_docs_json -- bridge tests`. Expected: twelve lines, all in `bridge/cursor-bridge/bridge-run.py`, at lines 1201, 1212, 1241, 1304, 1329, 1353, 1432, 1439, 2678, 3135, 3156 and 3609; none in `tests/`, no `_read_docs_json`.
   - `git grep -n -F -e "json.load(" -- bridge/cursor-bridge/bridge-run.py`. Expected: three lines, 1204, 1215 and 1307.
   - `git grep -n -F -e "except (OSError, ValueError, RecursionError):" -- bridge/cursor-bridge/bridge-run.py`. Expected: three lines, 1207, 1216 and 1308.
   - `git grep -n -F -e rev-parse -- bridge/cursor-bridge/bridge-run.py`. Expected: six lines, 1183, 1247, 2584, 2700, 3138 and 3155 (the last a docstring).
   - `git grep -n -e "^GIT_TIMEOUT" -- bridge/cursor-bridge/bridge_env.py`. Expected: one line, `416:GIT_TIMEOUT = 30`.
   Then compare, in the file itself, the `subprocess.run` call of `_git_launch_state` (lines 1246-1254) with that of `_git_rev_parse` (lines 3137-3145) argument by argument, and the `open(...)` lines and except tuples of the three readers (1203/1207, 1214/1216, 1306/1308), and state in the report that each pair agrees as quoted in the Objective. If a check does not hold (another hit, a missing hit, an option or argument that differs, or a line number other than these), stop, change nothing, and report it.
2. Part 1: `_git_launch_state` obtains the commit by `cand = _git_rev_parse(ws, "HEAD")`; the hex test is the same expression over `cand`; a `None` answer returns `(None, False)` before the status command; the docstring, `base = ws or "."`, the `start_commit is None` test and the status block are unchanged; `_git_rev_parse` is unchanged.
3. Part 2: `_read_docs_json(folder, name)` is a private top-level function directly above `roster_builder_model`, holding the only `json.load(` and the only `except (OSError, ValueError, RecursionError):` of the file, with the path, encoding, `errors` argument and except tuple quoted in the Objective; `roster_builder_model`, `_read_roster_json` and `_load_deviation` each call it once and keep their names, signatures, field checks and return values on every path.
4. No other line changes in `bridge-run.py`. It keeps its CRLF line endings and gains no trailing whitespace. Nothing is imported anew. No comment is added; `_read_docs_json` may have a one-line docstring in the style of the file's others, or none.
5. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: the same lines printed, the same refusals with the same texts, the same exit codes, the same run-record rows (`start_commit` a 40- or 64-hex name only where git answered one, otherwise `None` with `clean` `False`), and the same git commands with the same options and environment.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] Every listed caller now uses the single implementation: `git grep -n -F -e "json.load(" -- bridge/cursor-bridge/bridge-run.py` prints one line, in `_read_docs_json`; `git grep -n -F -e "except (OSError, ValueError, RecursionError):" -- bridge/cursor-bridge/bridge-run.py` prints one line, in `_read_docs_json`; `git grep -n -w -e _read_docs_json -- bridge` prints four lines, all in `bridge-run.py` (the def and one call in each of the three readers); `git grep -n -w -e _git_rev_parse -- bridge` prints three lines (the def, the call in `_git_rev_parse_path`, the call in `_git_launch_state`); `git grep -n -F -e rev-parse -- bridge/cursor-bridge/bridge-run.py` prints five lines, none inside `_git_launch_state`.
- [ ] No public signature changed outside the one added private name; `bridge-run.py` imports nothing new.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.24a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.24a`).
- [ ] `git diff --stat` shows only `bridge/cursor-bridge/bridge-run.py`, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service, and its tests use no recorded replies; add no fixture and no mock of git.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch: the rev-parse call keeps `creationflags=NO_WINDOW` through `_git_rev_parse`, and the status call keeps its own.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none beyond the existing git call.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short`, `git rev-parse HEAD` and `git log --oneline -3`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_launch.py tests/test_hotfix25a_roster_launcher.py tests/test_task032_supervisor_launcher.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_bridge_run_review_ceiling.py tests/test_bridge_run_driver.py tests/test_bridge_run_slot.py tests/test_hotfix24a_heavy_slots.py tests/test_header_currency.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; `git diff --numstat -- bridge/cursor-bridge/bridge-run.py`; the five `git grep` commands of the third acceptance criterion.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example the other git readers named in Out of scope, `local_head`'s own options, `roster_builder_model`'s answer where the file is missing, or a reader that would accept a wider set of exceptions); report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: one private function for Part 2, no new function for Part 1, no parameter beyond `folder` and `name`, no alias, no comment.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-017-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the Requirement 1 commands with their output as the evidence, and your argument-by-argument comparison of the two git calls and of the three readers' `open` lines and except tuples;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, the two `git diff --numstat` commands and the third acceptance criterion's five `git grep` commands, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
