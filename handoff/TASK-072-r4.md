---
record: brief
header: 1
id: "TASK-072"
round: 4
satisfies: [R-092]
scope: ["bridge/cursor-bridge/conformance-check.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-072-r4-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-072 round 4: a gitdir in the NT object-manager form is never touched (R-092)

Round cause: security - the security audit of rebuild round 2 BLOCK: in `_own_git_dir`, a `gitdir:` value in the NT object-manager form (`\??\UNC\<host>\...`, `\??\GLOBALROOT\Device\Mup\<host>\...`) passes the two-separator refusal, is absolute to Python 3.12's ntpath.isabs, is not joined to the Workspace and reaches os.lstat raw, which hands it to the object manager and opens SMB to the host; above the ceiling under the class line.

Blocking class: security - the security audit, rebuild round 2: a gitdir: value in the NT object-manager form reaches os.lstat

## Objective
This is round 4 of TASK-072 (R-092, `conformance-check.py`'s Weekly dependency scan row), the native rebuild on branch `task-072-native`. Rounds 1 and 2 of the rebuild are committed as built. Round 2 closed the mixed-slash network `gitdir:` forms (`/\` and `\/`). (`handoff/TASK-072-r3.md` belongs to the original build and does not apply to this rebuild.) The security audit of rebuild round 2 blocked on one form that round 2's refusal does not catch. This round refuses that form with one minimal edit, and nothing else changes.

Satisfies: R-092 - as round 1's brief (`handoff/TASK-072.md`).

## Scope
Files you may create or modify:
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-072-r4-report.md

Limits on these files:
- `conformance-check.py`: the one correction below, inside `_own_git_dir`, and nothing else. The module docstring does not change.
- `MANIFEST.json`: only through its generator, as round 1 (`python tools/make-manifest.py`, then `git restore bridge/cursor-bridge/VERSION`).

Every other file is read only, every test file among them. `tests/test_program_weekly_floor.py` is the supervisor's.

## Out of scope
As round 1's and round 2's briefs. Beyond this one correction:
- no other refusal widened or narrowed;
- no refactoring;
- no other finding;
- no option, environment variable or new dependency;
- no `.github` file.

## Context
**The fault**, in `_own_git_dir` as built at rebuild round 2 (about lines 834-840 of `bridge/cursor-bridge/conformance-check.py`; check the lines against your tree). After reading the `gitdir:` value, it does three things:
1. It refuses a value that is empty, starts with `-` or holds a NUL.
2. It refuses a value whose first two characters are both separators (`/` or `\`, in any order).
3. If `os.path.isabs(gitdir)` is false, it joins the value to the Workspace; it then calls `_git_entry_is_link_or_reparse(gitdir)` (an `os.lstat`) and `os.path.isdir(gitdir)`.

A value such as `\??\UNC\host\share` or `\??\GLOBALROOT\Device\Mup\host\share` passes the two-separator refusal, since its second character is `?`. It is absolute to Python 3.12's `ntpath.isabs` (the project pins 3.12), so it is not joined and reaches `os.lstat` raw. Win32 passes the `\??\` prefix to the NT object manager unchanged, which opens an SMB connection to the host. That is the same harm the rebuild's round 1 was blocked for.

**The test:** the supervisor's `test_rebuild_r2_a_network_gitdir_in_either_slash_order_is_never_touched` in `tests/test_program_weekly_floor.py` (around line 675). It is parametrized with seven forms. Three are new: ids `nt-object-unc`, `nt-object-globalroot` and `nt-object-forward-slashes`. It runs the check under a guard runner that refuses, and reports as `TOUCHED-NETWORK-PATH`, any filesystem call, file open or git launch naming `nohost.invalid`, and it expects the row to read `NOTE`. The three new forms are red on round 2's code.

**Trust boundary:** a project's `.git` file is untrusted input (a checkout the owner cloned). ASVS level 2 (docs/INVENTORY.md, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you.

**Development data:** as round 1's brief. The check runs only through the test files in Done, on projects the tests build under pytest's temporary folders.

## Requirements
1. **A `gitdir:` value in the NT object-manager form is read as no git folder** (security; the security audit, rebuild round 2). In `_own_git_dir`, a value whose first four characters are a separator, `??`, and a separator is read as no git folder (the function returns `None`). Either slash counts, in any combination: `\??\`, `/??/`, `\??/`, `/??\`. The value is refused before any `os.path`, `os.lstat`, `open` or git call touches it, on every platform, beside the existing two-separator refusal. Nothing else of the function changes. No other refusal is widened or narrowed.

## Acceptance criteria
- [ ] Every test in `tests/test_program_weekly_floor.py` passes, unedited, including `test_rebuild_r2_a_network_gitdir_in_either_slash_order_is_never_touched[nt-object-unc]`, `[nt-object-globalroot]` and `[nt-object-forward-slashes]`.
- [ ] Every other test file of the Done list passes, unedited.
- [ ] `python tools/dump-cli.py --check` passes. The module docstring is unchanged.
- [ ] The one correction and nothing else. The diff of `conformance-check.py` touches only `_own_git_dir`'s refusals.
- [ ] MANIFEST regenerated by `tools/make-manifest.py`. `bridge/cursor-bridge/VERSION` is not listed by `git status --short`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `conformance-check.py` stays ASCII.

## Constraints
As round 1's brief (`handoff/TASK-072.md`), every one of them. Among them:
- Do not run the whole `tests/` tree.
- No path of this computer or user name in anything you write (`<Workspace>`, `<tmp>`).
- Read and write nothing outside this workspace.
- Do not add dependencies.
- In Markdown, one paragraph is one line.
- Any dated line on a hindrance or a pitfall goes to `docs/BUILDER_NOTES.md`.
- The git commands that are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. The single exception is `git restore bridge/cursor-bridge/VERSION` in Done.
- No server, watcher or process left running.
- No network call: the test's host, `nohost.invalid`, answers no resolver, and nothing you run may name a real host.

**Mutation self-check**, by hand, in process, no script in the diff. The label is:
- R4-M1: the `\??\` refusal is dropped (the value reaches `os.path.isabs` again).

Apply it by hand. Run `python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py`. Revert it by hand and confirm the revert with `git diff`. List it in the report with its pytest summary line and the id of a case it made fail, or `not caught` with one line on the case that would catch it (add none).

## Done
Your report is the file `handoff/TASK-072-r4-report.md`, written as you go, so that nothing of it is lost if your run ends early. When you finish, it holds:
- the files changed;
- a one-paragraph summary;
- one line on the correction, naming the function and its lines after your change, with the changed lines quoted in a fenced block;
- the mutation self-check;
- every command below with its output, verbatim, in fenced blocks;
- a section headed exactly `Assumed, not verified`, as the report's last section.

`Assumed, not verified` lists every fact this change relies on that neither this brief nor the existing code settled and that you did not confirm. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. One example item: that no other Win32 path prefix (for instance `\\?\` or `\\.\`, already caught by the two-separator refusal) reaches `os.lstat` raw.

Run these from the Workspace root, after your last edit, in this order, each on its own, synchronously in the foreground:
1. `git status --short`
2. `python tools/make-manifest.py`
3. `git restore bridge/cursor-bridge/VERSION`
4. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_weekly_floor.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_diagram_check.py tests/test_bug042.py`
5. `python -m pytest -p no:cacheprovider -q -rs tests/test_hotfix25a_conformance_semgrep.py tests/test_a4_followups.py tests/test_a4_review_fixes.py tests/test_b2_least_confident.py tests/test_program_branch_rule.py tests/test_calibrate_program.py tests/test_conformance_windowless.py`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_workflows_line_check.py tests/test_header_status.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_currency.py tests/test_program_strip_names.py tests/test_loop_text_windowless.py tests/test_running_projects_classify.py`
7. `python -m pytest -p no:cacheprovider -q -rs tests/test_dump_cli.py` (expect it to pass whole)
8. `python tools/dump-cli.py --check` (expect it to pass)
9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `python -c "open('bridge/cursor-bridge/conformance-check.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed, and no `.github` file; if either is, report it)

Quoting rules:
- Each pytest summary line is quoted verbatim. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it.
- A command you did not run is written `not run`.
- Write the results after command 12, naming the commit (`git rev-parse HEAD`) and whether the working tree held uncommitted changes.

Your last message is the summary and the report file's path, and nothing follows it.
