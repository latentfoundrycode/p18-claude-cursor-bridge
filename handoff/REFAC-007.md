---
record: brief
header: 1
id: REFAC-007
round: 1
satisfies: [R-077]
scope: ["bridge/cursor-bridge/trace-check.py", "bridge/cursor-bridge/MANIFEST.json", "docs/CLI_REFERENCE.md", "docs/cli-reference.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-007-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-007: one helper for trace-check.py's two instruction-path listings

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries one candidate of stage P1's refactoring pass (the refactor scout's range `d211e33..6fb2eb9`): a repeat that TASK-057 (the trace check's move mode) added to `bridge/cursor-bridge/trace-check.py`, and the manifest regenerated after it. Behaviour stays exactly the same: every printed line, every error string, every exit code. Line numbers below are as the file stands at `6fb2eb9` (the head of `main` that branch `refactor/P1` was cut from), before your edit.

**The sites.** `instruction_paths_in_rev(root, rev)` (lines 635-652) and `changed_instruction_paths(root, base, head)` (lines 655-672) have the same body apart from the argument list each passes to `git_run`. Each: calls `git_run(root, <args>)`; returns `None, err` when `proc is None`; returns `None, "command failed"` when `proc.returncode != 0`; splits `proc.stdout` on the NUL byte (U+0000), skips empty parts, decodes each part with `decode_git_bytes`, returning `None, "cannot be read as UTF-8"` on `UnicodeDecodeError`; keeps `slash(rel)` for each part where `is_instruction_md(rel)` holds; sorts the list; returns `paths, None`. Their two argument lists, which must reach `git_run` byte-identical and in the same order, are:

```python
["ls-tree", "-r", "--name-only", "-z", rev, "--", "bridge/"]
["diff", "--name-only", "--no-renames", "-z", base, head, "--", "bridge/"]
```

**The proposed shape.** The shared body lives once, in one module-level helper that takes the git argument list (and `root`); the order of the steps, the two error strings, the empty-part skip, the filter and the sort are as today. Then either (a) `instruction_paths_in_rev` and `changed_instruction_paths` keep their names and signatures and each becomes a one-line wrapper that calls the helper with its argument list, or (b) the two functions go and their two callers call the helper directly. Choose one; (a) changes no caller.

**Callers to update** (only under option b): `head_passage_norms` line 677 (`paths, err = instruction_paths_in_rev(root, head)`) and `run_moves` line 738 (`changed_paths, err = changed_instruction_paths(root, base, head)`). Under option (b) each changes in that one line only, and its left-hand side and every line around it stay as they are. No other caller exists: `git grep -n -e instruction_paths_in_rev -e changed_instruction_paths` finds only these four lines in `bridge/` and nothing under `tests/` or `tools/`.

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.12a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as it is R-077 (a moved or retired instruction passage caught by `trace-check.py --moves`), built by TASK-057.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/trace-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/CLI_REFERENCE.md
- docs/cli-reference.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-007-r1-report.md

Do not modify anything else. `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` are in Scope only for the case Requirements 5 names (`python tools/dump-cli.py --check` reports a difference after your edit); otherwise leave both untouched. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included: this change needs no diagram change (see Diagrams); `docs/TRACE_MOVES.md` included
- every file under `tests/`: no test file may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.12a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- every other function of trace-check.py (in particular `git_run`, `decode_git_bytes`, `is_instruction_md`, `slash`, `head_passage_norms` and `run_moves` apart from the one line each under option b, the full mode's own `git ls-tree` reading near line 953, and `build_parser`), the module docstring, and every other file under `bridge/`

## Context
**What the code is today** (`6fb2eb9`). `bridge/cursor-bridge/trace-check.py` has CRLF line endings on every line; keep them, and add no trailing whitespace. The module docstring (lines 2-50) describes the move mode's output and exit codes and names neither function; neither function has a docstring. Neighbours used by the body, all unchanged: `slash(path)` (line 85), `git_run(root, args)` (line 263, returns `(proc, None)` or `(None, "<reason>")`), `decode_git_bytes(data)` (line 279, raises `UnicodeDecodeError` on a non-UTF-8 part), `is_instruction_md(rel)` (line 555).

**What the callers do with the results, unchanged.** `head_passage_norms` returns `None, None, err` when the listing fails, and `run_moves` prints `ERROR: git: <err>` for it (line 734); for the diff listing `run_moves` prints `ERROR: git diff: <err>` (line 740); both then print `RESULT: not checked` and return 2. These lines and their text stay as they are, so each error string the helper returns must be exactly the one the replaced function returned.

**How the tests reach this code.** `tests/test_program_trace_moves.py` (23 tests) runs `trace-check.py --moves` from the Workspace source against git repositories it builds under pytest's `tmp_path`; it reaches both listings on their success paths. The two error branches (`"command failed"` and `"cannot be read as UTF-8"` in these two functions) are not covered by any test: they move unchanged, and the reviewer reads them by eye, so keep them textually as they are. `tests/test_trace_check.py` and `tests/test_trace_full_split.py` cover the full mode of the same program (its own `git ls-tree` reading near line 953, which you do not touch). No test refers to either function by name or by syntax tree.

**The command reference.** `tools/dump-cli.py` builds `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` from each program's `build_parser()` and module docstring; this change touches neither, so `python tools/dump-cli.py --check` is expected to print nothing and exit 0. It prints the path of each reference file that differs and exits 1.

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for trace-check.py; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.12a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.12a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.12a`.

**Security context.** This is a logic surface (a program that launches git and decodes the path names a repository holds): `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). The trust boundary here is the repository content git reports (path names in commits, possibly not UTF-8) and the `--base` value, which `git_merge_base` checks before either listing runs; this change moves no boundary: the same git commands run with the same arguments (the `--` before `bridge/`, `--no-renames` on the diff), git is still launched only through `git_run` (windowless, stdin closed, with its timeout), and a non-UTF-8 path still ends the check with the same error.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders. Never run trace-check.py yourself against this repository, and never run `bridge-install.py`.

## Diagrams
`docs/diagrams/D-002-components.md` — the element `trace_check` (`bridge/cursor-bridge/trace-check.py`, drawn as `trace_check["trace-check.py"]`). The program keeps its imports and gains none; no edge is added or removed, so the diagram does not change. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -e instruction_paths_in_rev -e changed_instruction_paths` and confirm it shows exactly four lines, all in `bridge/cursor-bridge/trace-check.py` (the two definitions at lines 635 and 655, the calls at lines 677 and 738), and that the name you choose for the helper is not already used in the file (`git grep -n -e <name> -- bridge/cursor-bridge/trace-check.py` shows nothing). If a check does not hold, stop, change nothing, and report it.
2. The shared body exists once, in one helper; both listings go through it; the two argument lists reach `git_run` byte-identical to the two quoted in the Objective.
3. Under option (a) the two functions keep their names and signatures as one-line wrappers; under option (b) they are gone and only lines 677 and 738 of their callers change. Either way, every caller gets the same `(paths, None)` or `(None, err)` pair as today for every input, with the same `err` text.
4. No other line of trace-check.py changes beyond the two functions (and, under option b, the two caller lines). The file keeps its CRLF line endings and gains no trailing whitespace. No docstring or comment you leave states something the code no longer does.
5. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints. If `python tools/dump-cli.py --check` prints a path (it should not), run `python tools/dump-cli.py` once to regenerate both reference files, run `--check` again, and report both outputs and why the reference changed; otherwise do not touch either file.

## Acceptance criteria
- [ ] Behaviour is identical: the same printed lines, error strings and exit codes for every input of `trace-check.py`, in both modes.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the three named test files pass before and after the edit with the same count passed, none failed, none newly skipped, both summary lines quoted in the report. No test file edited.
- [ ] Both listings use the single implementation; the duplicate body is gone (the strings `"command failed"` and `"cannot be read as UTF-8"` each appear once fewer in trace-check.py than today, and `proc.stdout.split(` once fewer).
- [ ] No public signature outside the listed sites changed; the only new name is the one helper.
- [ ] `--no-renames` still appears in the diff listing's argument list, and both argument lists are byte-identical to today's.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output (or, if it did not, Requirements 5 was followed and reported).
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.12a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.12a`).
- [ ] `git diff --stat` shows only `bridge/cursor-bridge/trace-check.py`, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the bridge programs, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch: git is still launched only through the existing `git_run`.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none beyond the existing `git_run`.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_program_trace_moves.py tests/test_trace_check.py tests/test_trace_full_split.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example the full mode's own listing near line 953, or an `--end-of-options` the git calls do not have); report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: one helper taking the git argument list; no class, no new parameter for the filter or the error text, nothing new outside trace-check.py.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-007-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did, naming the option you chose, (a) or (b), and the helper's name;
- the Requirements 1 grep commands with their output as the evidence;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check and `git diff --numstat -- bridge/cursor-bridge/VERSION`, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
