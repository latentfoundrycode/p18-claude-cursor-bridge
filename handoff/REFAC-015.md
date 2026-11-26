---
record: brief
header: 1
id: "REFAC-015"
round: 1
satisfies: [R-107, R-095, R-040]
scope: ["bridge/cursor-bridge/roster-check.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-015-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-015: roster-check's rebuild entry, its unreadable exits and built_by's line reader, each one copy

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries three candidates of stage I1's refactoring pass, all in `bridge/cursor-bridge/roster-check.py`, in three named parts. The manifest is regenerated after them. Behaviour stays exactly the same: every line roster-check.py prints (each REBUILD, FAIL, DEVIATION, RESOLVED, probe and skip line, in the same order), every exit code, every file it writes (`docs/ROSTER.resolved.json` with the same keys and values, the roster state), the dict `built_families` returns (the same keys, in the same insertion order, with the same values), and the answer of `built_by` for every run log. Line numbers below are as the file stands at `8b03c32` (TASK-087c, the base of branch `refactor/I1`); Requirement 1 checks that the file is still that one.

**Part 1: the rebuild entry in `main()`.**

The nested helper today, lines 1184-1194 (inside `main()`, after `bset`, `built_model`, `roster_b_fams`, `set_status` and `cwd` are set at lines 1159-1171):

```python
    def _rebuild_line_open(r_id, r_fam, rb_model, builder_id):
        rows_for_rb = bset["counted_rows"] if set_status != "unknown" else bset["parsing_rows"]
        rb = _rebuild_built_by_model(rows_for_rb, r_fam, roster, profiles, built_model)
        if rb and _roster_model_family(roster, profiles, rb) == r_fam:
            return ("    REBUILD  review_b %s is of the %s family, which built the change in flight (%s): this profile's builder %s rebuilds it before Review B (step 3b); the reviewer of a change is never of the family that built it (release A4)" % (
                r_id, r_fam, rb, builder_id)), rb
```

(two more `return` branches follow, each returning a REBUILD line and `rb`). Its third parameter `rb_model` is read nowhere in its body: the fallback model passed to `_rebuild_built_by_model` is the closure's `built_model`.

The three sites, each in the profile loop of `main()`:

- Site A, lines 1347-1357 (the built set is unknown); the new-branch question is asked only where `family_only_unknown` (lines 1340-1342) is true:

```python
                if r_fam in roster_b_fams or r_fam in parse_b_fams or parsing_unknown_family:
                    rb_line, rb_model = _rebuild_line_open(r_id, r_fam, built_model, b_id)
                    rebuild = {"built_by": rb_model, "rebuild_with": b_id}
                    if family_only_unknown:
                        nb = _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd)
                        if nb is None:
                            print("FAIL  cannot read the families that built this branch (git)")
                            return 1
                        if nb:
                            profile_rebuild_end = "new branch"
                    print(rb_line)
```

- Site B, lines 1369-1378 (a known set that holds review_b's family and no usable alternate); the question is always asked:

```python
                    else:
                        rb_line, rb_model = _rebuild_line_open(r_id, r_fam, built_model, b_id)
                        rebuild = {"built_by": rb_model, "rebuild_with": b_id}
                        nb = _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd)
                        if nb is None:
                            print("FAIL  cannot read the families that built this branch (git)")
                            return 1
                        if nb:
                            profile_rebuild_end = "new branch"
                        print(rb_line)
```

- Site C, lines 1407-1420 (the alternate did not answer its probe); the question is always asked, and two extra assignments sit between the question and the print:

```python
                    if not ok_alt:
                        rb_line, rb_model = _rebuild_line_open(r_id, r_fam, built_model, b_id)
                        rebuild = {"built_by": rb_model, "rebuild_with": b_id}
                        nb = _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd)
                        if nb is None:
                            print("FAIL  cannot read the families that built this branch (git)")
                            return 1
                        if nb:
                            profile_rebuild_end = "new branch"
                        deviation = None
                        use_r_id, use_r_fam = r_id, r_fam
                        print(rb_line)
                        if not ok_rb:
                            print("    skip: a model did not answer"); continue
```

`profile_rebuild_end` starts each profile as `global_rebuild_end` (line 1337, which is `bset["rebuild_end"]`: `None`, `"checkpoint"` or `"--repair-record"`) and is replaced only when the answer is yes; `main()` reads it at lines 1431-1433 and 1464-1475. `_rebuild_needs_new_branch(counted, branch, cwd)` (line 572) returns `False`, `True`, or `None` where git does not answer, and prints nothing.

The change: `_rebuild_line_open` loses its `rb_model` parameter and becomes `def _rebuild_line_open(r_id, r_fam, builder_id):`, its body unchanged. One more nested helper, named `_rebuild_entry`, is defined directly after it inside `main()`; it takes the reviewer's id and family, the builder's id, and whether to ask the new-branch question, and returns three things: the REBUILD line (from `_rebuild_line_open`), the rebuild dict `{"built_by": <the model _rebuild_line_open returned>, "rebuild_with": <the builder's id>}`, and the end marker: `"new branch"` where the question was asked and answered `True`, nothing (`None`) where it was not asked or answered `False`. Where `_rebuild_needs_new_branch` returns `None`, the helper tells its caller so in a way the caller can test (the representation is yours; state it in the report). The helper prints nothing and returns no exit code. Each of the three sites calls it once (site A with the question behind `family_only_unknown`, sites B and C always asking) and keeps, itself: the `print("FAIL  cannot read the families that built this branch (git)")` and `return 1` where git did not answer, setting `rebuild`, setting `profile_rebuild_end = "new branch"` only where the marker says so (otherwise leaving it as it was), its `print(rb_line)` after that, and site C's `deviation = None` and `use_r_id, use_r_fam = r_id, r_fam` before its print and its `if not ok_rb:` skip after it. Where site A's `family_only_unknown` is false, `_rebuild_needs_new_branch` is not called at all (it runs git; a git failure there must still not end the resolve).

**Part 2: the unreadable exits of `built_families`.**

`built_families(run_log, branch=None, cwd=None, roster=None, profiles=None)` (line 468) repeats one three-line exit eight times, at lines 489-491, 493-495, 500-502, 507-509, 511-513, 516-518, 523-525 and 531-533, each of this form:

```python
        result["status"] = "unreadable"
        result["unreadable_cause"] = "git"
        return result
```

(the causes, in order: `"git"`, `"detached"`, `rep_fail`, `fail`, `"main"`, `"git"`, `open_fail`, `"git"`). The first two are the two branches on `head_fail`, lines 487-495:

```python
    branch_name, head_fail = _branch_from_head(cwd)
    if head_fail == "git":
        result["status"] = "unreadable"
        result["unreadable_cause"] = "git"
        return result
    if head_fail == "detached":
        result["status"] = "unreadable"
        result["unreadable_cause"] = "detached"
        return result
```

`_branch_from_head(cwd)` (lines 304-313) returns its second value as exactly one of `"git"`, `"detached"` or `None` (its four `return` statements: `None, "git"`; `None, "detached"`; `ref[len("refs/heads/"):], None`; `None, "detached"`).

The change: a module-level private function `_unreadable(result, cause)`, placed directly before `built_families`, sets `result["status"] = "unreadable"` and `result["unreadable_cause"] = cause` and returns `result`. Each of the eight exits becomes a `return _unreadable(result, <the same cause>)` with its condition unchanged, except that the two `head_fail` branches merge into one, `if head_fail:` returning `_unreadable(result, head_fail)`. Nothing else in `built_families` changes; its docstring stays. The keys of `result` are only assigned, never added, so the returned dict keeps its keys and their order. `bridge/cursor-bridge/bridge-run.py`'s `_built_set_at_launch` (line 1319) calls `roster.built_families(log_path, branch=branch, cwd=ws, roster=roster_data or {}, profiles=profiles or [])`, and its callers read `status`, `families`, `unknown_causes` and `run_log_base` from the result: those fields and their values must stay the same, and bridge-run.py is not edited.

**Part 3: `built_by`'s line reader.**

`built_by(run_log, branch=None)` (line 156) re-parses each run-log line itself, lines 168-182:

```python
    for line_b in raw:
        if not line_b.strip():
            continue
        try:
            line = line_b.decode("utf-8")
        except UnicodeDecodeError:
            continue
        try:
            e = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if isinstance(e, dict) and e.get("kind") == "builder" and e.get("model"):
            if e.get("slot") == "not free":
                continue
            entries.append(e)
```

while `_parse_run_line(line_b)` (lines 410-425, the same file) already does that reading: it returns `None` for a blank line (bytes or text that strip to nothing), `False` for a line that does not decode as strict UTF-8, does not parse as JSON (`ValueError`, `RecursionError`) or is not a JSON object, and the dict otherwise. The change: `built_by`'s loop calls `_parse_run_line(line_b)` and skips a falsy result (`None` or `False`), then keeps the filter as it is (`kind == "builder"`, a truthy `model`, a `slot` of `"not free"` skipped). The `try`/`except OSError: return None` around the read, `branch = branch or current_branch()` after it (so git is asked only after the log was read), the reversed walk and the return value stay exactly as they are; the docstring stays. The two readers skip the same lines: each blank or undecodable or unparseable line and each non-object is skipped by both (`built_by` today skips a non-object through its `isinstance(e, dict)` test, and a line whose text strips to nothing through `json.loads` raising `ValueError`).

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.24a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as they are R-107 (an exhausted pool never parks or pauses work, and a reviewer is never of a family that built the change: `roster-check.py` reads the families that built a branch from the launcher's run record, prints REBUILD where what was built leaves no reviewer, and ends with the cause and no REBUILD where the set cannot be read at all; TASK-086a, TASK-086b), R-095 (a signed-out Cursor tool is told from a failing model: roster-check.py's probe prints the SIGN-IN line and ends with exit 5; TASK-075) and R-040 (one heavy job at a time: a launch refused the slot is no builder run, which `built_by`'s `slot == "not free"` skip keeps; tests/test_hotfix25a_roster_launcher.py).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-015-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser` and no module docstring)
- every file under `tests/`, `tests/fixtures/` included: no test file or fixture may be edited, renamed or created (the supervisor's purity check fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.24a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's and the launcher's, gitignored; you write nothing there
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- in roster-check.py: `_profile_in_use` and the two inline probe blocks (lines 1224-1250, 1240-1247 and 1287-1295 at `8b03c32`: the nested `_profile_in_use` with its builder probe, and the `review_b_alt` probe in the `--review-alt` branch) are not touched, not even to reuse `_probe_roles`; a later fix changes them (R-107's open item, planned at stage I2's start). `_probe_roles`, `_alt_pool_ok`, `_r_excluded`, `_rebuild_needs_new_branch`, `_rebuild_built_by_model`, `_parse_run_line`, `_parse_run_log_raw`, `_branch_from_head`, `repair_record`, the rest of `built_families` and of `main()`, and every other function stay as they are
- `bridge/cursor-bridge/bridge-run.py` and every other file under `bridge/`

## Context
**What the code is today** (`8b03c32`). roster-check.py has CRLF line endings on every line; keep them, and add no trailing whitespace. It defines no `__all__`. No test names `_rebuild_line_open`, `_rebuild_needs_new_branch`, `_parse_run_line`, `_unreadable` or `_rebuild_entry` (Requirement 1 checks it); tests call `built_by` directly (`tests/test_hotfix25a_roster_launcher.py` lines 47, 49, 221, 223; `tests/test_improve_roster_alt.py` lines 987-989) and reach `built_families` and `main()` through the program and through bridge-run.py's load of it by file. `tests/test_improve_roster_launch.py` (around line 393) writes stand-in copies of the roster program in its own temporary folders; that does not involve the Workspace file.

**The covering tests**, which must stay green and are not edited: `tests/test_improve_roster_alt.py` (TASK-086a, R-107: the resolve, REBUILD and DEVIATION lines, the rebuild dict `["built_by", "rebuild_with"]`, the new-branch, checkpoint and repair-record ends, `built_by`'s answer), `tests/test_improve_roster_launch.py` (TASK-086b, R-107: the launcher's refusals reading `built_families`, the unreadable set included), `tests/test_roster_check.py`, `tests/test_roster_check_a4.py` (release A4: the REBUILD line and `{"built_by": ..., "rebuild_with": ...}`), `tests/test_hotfix25a_roster_launcher.py` (R-040: `built_by` and the `slot` skip) and `tests/test_program_roster_sign_in.py` (TASK-075, R-095: the probe's sign-in line and exit 5). They make no network call and run git only in pytest's temporary repositories. Some cases may be skipped on Windows; the skip count must be the same before and after.

**The expected count.** No supervisor count is given for this set: your before-edit run of the pytest command below is the baseline, and the after-edit run must match it (the same count passed, none failed, the same count skipped).

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for roster-check.py; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.24a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.24a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.24a`. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** roster-check.py reads the launcher's run log (`run/launcher/runs.jsonl`, a file the agents' user can write, so every line is untrusted input), the checkout through git, and the roster; it writes the resolved roster that bridge-run.py's review refusals read. The trust boundaries are the run log, the checkout's git state and the roster file. `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). This change moves no boundary: Part 3 accepts and skips exactly the same run-log lines (strict UTF-8, JSON objects only, `RecursionError` caught), Part 2 ends in the same unreadable status with the same cause on every git or record failure (so the launcher still refuses every review on an unreadable set), and Part 1 still ends the resolve with FAIL and exit 1 where git does not answer the new-branch question.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders and the repositories they create there. Never run roster-check.py or bridge-run.py yourself, against this repository or any other: roster-check.py rewrites `docs/ROSTER.resolved.json` and the roster state, and its probe starts a model. Never run `cursor-agent` or `bridge-install.py`.

## Diagrams
`docs/diagrams/D-002-components.md`: the element `roster_check` (`bridge/cursor-bridge/roster-check.py`), whose edges already exist:

```mermaid
    roster_check --> bridge_env
    bridge_run -.-> roster_check
```

The change adds no import, no load and no edge, so the diagram does not change. `docs/diagrams/D-004-context-dfd.md` draws `p_roster_check`'s flows (the run record and the report files read, `--repair-record`'s rewrite, `docs/ROSTER.resolved.json` written; R-107); this change adds or removes none of them. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run:
   - `git diff --stat 8b03c32 -- bridge/cursor-bridge/roster-check.py`. Expected: nothing (the file is as at `8b03c32`).
   - `git grep -n -F -e "_rebuild_line_open(" -e "_rebuild_needs_new_branch(" -- bridge/cursor-bridge/roster-check.py`. Expected: eight lines, 572 (the def of `_rebuild_needs_new_branch`), 1184 (the def of `_rebuild_line_open`), 1348, 1351, 1370, 1372, 1408 and 1410.
   - `git grep -n -F -e "cannot read the families that built this branch" -- bridge/cursor-bridge/roster-check.py`. Expected: four lines, 1175, 1353, 1374 and 1412.
   - `git grep -n -F -e "new branch" -e rebuild_with -- bridge/cursor-bridge/roster-check.py`. Expected: eight lines, 1349, 1356, 1371, 1377, 1409, 1415, 1472 and 1473.
   - `git grep -n -w -e unreadable -e unreadable_cause -e head_fail -- bridge/cursor-bridge/roster-check.py`. Expected: 24 lines, 469, 472, 482, 487, 488, 489, 490, 492, 493, 494, 500, 501, 507, 508, 511, 512, 516, 517, 523, 524, 531, 532, 1173 and 1174.
   - `git grep -n -F -e "json.loads(" -e "_parse_run_line(" -- bridge/cursor-bridge/roster-check.py`. Expected: five lines, 176 (in `built_by`), 410 (the def), 420, 445 and 666.
   - `git grep -n -w -e _unreadable -e _rebuild_entry -- bridge`. Expected: nothing.
   - `git grep -n -w -e _rebuild_line_open -e _rebuild_needs_new_branch -e _parse_run_line -e _unreadable -e _rebuild_entry -- tests`. Expected: nothing.
   If a check does not hold (another hit, a missing hit, or another line number), stop, change nothing, and report it.
2. Part 1: `_rebuild_line_open` reads `def _rebuild_line_open(r_id, r_fam, builder_id):` with its body unchanged; `_rebuild_entry` is the one caller of `_rebuild_line_open` and of `_rebuild_needs_new_branch`; each of the three sites calls `_rebuild_entry` once and keeps its own FAIL print and `return 1`, its `rebuild` and `profile_rebuild_end` assignments as described in the Objective, its `print(rb_line)`, and (site C) its `deviation = None`, `use_r_id, use_r_fam = r_id, r_fam` and `ok_rb` skip, in the same order relative to the print as today. Site A asks the question only where `family_only_unknown` is true.
3. Part 2: `_unreadable(result, cause)` is a module-level function directly before `built_families`; the eight exits are seven `return _unreadable(...)` lines with the same causes in the same order, the two `head_fail` branches merged into one; nothing else in `built_families` changes.
4. Part 3: `built_by`'s loop uses `_parse_run_line` and skips a falsy result; the filter, the `OSError` return, the `current_branch()` call after the read, the reversed walk and the return value are unchanged.
5. No other line changes in roster-check.py. It keeps its CRLF line endings and gains no trailing whitespace. No comment, docstring or alias is added (the two new helpers carry none); nothing is imported anew.
6. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: the same lines printed in the same order (REBUILD, FAIL, DEVIATION, RESOLVED, probe, skip and NOTE lines), the same exit codes (0, 1, 5), the same `docs/ROSTER.resolved.json` and roster state written, the same dict from `built_families` (keys, order, values, `status` and `unreadable_cause` included) for every git and record outcome, and the same answer from `built_by` for every run log.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] One copy each, checked after the edit with the same commands as Requirement 1: the `_rebuild_line_open(` / `_rebuild_needs_new_branch(` grep prints four lines (the two defs and one call of each, both inside `_rebuild_entry`); the `cannot read the families that built this branch` grep still prints four lines (1175's and the three sites'); the `new branch` / `rebuild_with` grep prints four lines (one `rebuild_with` and one `"new branch"` in `_rebuild_entry`, and the two lines of the end's print, today's 1472 and 1473); the `unreadable` / `unreadable_cause` / `head_fail` grep prints ten lines (the docstring's two, the dict's initial `unreadable_cause`, the three `head_fail` lines: the unpacking, `if head_fail:` and its `return _unreadable(result, head_fail)`, the two assignments in `_unreadable`, and `main()`'s two); the `json.loads(` / `_parse_run_line(` grep prints five lines (the def, its `json.loads`, and the calls in `_parse_run_log_raw`, `repair_record` and `built_by`); `git grep -n -w -e _unreadable -- bridge/cursor-bridge/roster-check.py` prints eight lines (the def and seven calls); `git grep -n -w -e _rebuild_entry -- bridge/cursor-bridge/roster-check.py` prints four lines (the def and three calls). If your edit gives another count for a sound reason, quote it and explain it in the report.
- [ ] No public signature changed: `built_by`, `built_families`, `main` and every other module-level name keep their signatures; the only signature change is the nested `_rebuild_line_open`'s dropped `rb_model`. roster-check.py imports nothing new.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.24a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.24a`).
- [ ] `git diff --stat` shows only `bridge/cursor-bridge/roster-check.py`, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md`, `bridge/cursor-bridge/bridge-run.py` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This change talks to no external service and adds no test; do not invent a mock of anything, and do not add or change a fixture.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch and leaves `_git_run` and `probe` as they are.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_alt.py tests/test_improve_roster_launch.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_hotfix25a_roster_launcher.py tests/test_program_roster_sign_in.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; `git diff --numstat -- bridge/cursor-bridge/roster-check.py`; the Requirement 1 `git grep` commands on `bridge/cursor-bridge/roster-check.py` again, and the two of the third acceptance criterion.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example the wording of the REBUILD lines, the FAIL line's fixed `(git)` cause at the three sites, `_parse_run_line`'s handling of a line, or `_profile_in_use`'s probe); report them in your summary instead. Do not introduce an abstraction beyond the two helpers named here: no further helper, no parameter beyond what `_rebuild_entry` needs, no alias, no comment, nothing new outside roster-check.py except the regenerated manifest.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-015-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did, naming how `_rebuild_entry` tells its caller that git did not answer;
- the Requirement 1 commands with their output as the evidence;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, the two `git diff --numstat` commands and the after-edit `git grep` commands, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
