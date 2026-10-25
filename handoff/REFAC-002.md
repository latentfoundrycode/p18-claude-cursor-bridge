# REFAC-002: loop-guard.py imports only the datetime name it uses

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

The loop guard (`bridge/cursor-bridge/loop-guard.py`, a Claude Code Stop hook) imports three names from `datetime` on line 36 and uses one. Since BUG-020 (PR #73) no code in the file uses `timedelta`, and `timezone` was already unused before that (the `.astimezone()` call at line 308 is a method of the `datetime` object and does not use the imported name). This is refactor-scout's candidate P1 for stage B4, and `docs/HARDENING.md` names it as a lead for this pass (the BUG-020 section, line 314: "the `timedelta` import of loop-guard.py is used by no code since the fix ... for the next refactoring pass").

Site: `bridge/cursor-bridge/loop-guard.py`, line 36, which today reads exactly:

```python
from datetime import datetime, timedelta, timezone
```

Proposed shape: the line becomes exactly:

```python
from datetime import datetime
```

Callers to update: none. No code in the repository reads `timedelta` or `timezone` from the loaded program (see Context). Nothing else changes in this file or in any other file.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/loop-guard.py (line 36 only)
- docs/BUILDER_NOTES.md (append only)
- handoff/REFAC-002-r1-report.md

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/`. In particular, do **not** run `tools/make-manifest.py`
- docs/ and handoff/, except the files the Scope section names
- every file under `tests/`: no test file may be edited, renamed or created. This branch already carries the supervisor's tests-lane commit (`ebd3ade REFAC-B4 tests lane: ...`), and you must not touch it
- `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/VERSION`: the supervisor regenerates the manifest after your run
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`: no command changes
- every other line of loop-guard.py (the module docstring, lines 1-30; the other imports, lines 31-35; every function) and every other file under `bridge/`

## Context
**What the code is today** (branch `refactor/B4`, cut from `origin/main` 0c34622, plus the tests-lane commit ebd3ade). The import block of `bridge/cursor-bridge/loop-guard.py`, lines 31-36, verbatim:

```python
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
```

The supervisor's reality check before this brief, on this branch:
- A search of the whole of loop-guard.py for `timedelta` and for `timezone` matches only line 36. The one other related match is line 308, `t = datetime.fromtimestamp(unix).astimezone()`, in `def local_clock(unix):`. That is a method call on a `datetime` instance and does not use the imported `timezone` name.
- `datetime` itself stays in use (for example lines 308 and 315, `datetime.fromtimestamp(...)`).
- No file under `tests/` or `bridge/` reads `timedelta` or `timezone` as an attribute of the loaded loop guard: no `lg.timedelta`, no `lg.timezone`, and no `getattr(..., "timedelta"/"timezone")`. `tests/test_loop_guard.py` line 6 has its own `from datetime import datetime, timezone`, which this change does not affect. The `datetime.timezone.utc` uses in `bridge-run.py`, `roster-check.py` and `sync-check.py` are those programs' own `import datetime`, and this change does not affect them either.
- The program runs `main()` only under `if __name__ == "__main__":` (line 529), so importing it through importlib runs nothing.

**How the tests load the program.** `tests/conftest.py` `def load_program(name):` imports `bridge/cursor-bridge/<name>.py` (the Workspace source, `CURSOR_BRIDGE = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")`) through `importlib.util.spec_from_file_location`. The `program` fixture returns it, and `tests/test_loop_guard.py` uses it as `program("loop-guard")`.

**The manifest.** `bridge/cursor-bridge/MANIFEST.json` holds a sha256 of every file under `bridge/` (today `"cursor-bridge/loop-guard.py": "a4a07191..."`). After your edit that hash no longer matches. Any test that compares the sources with the manifest fails on loop-guard.py until the supervisor regenerates the manifest after your run. That is expected: you do not run those tests and you do not regenerate the manifest. Name the expectation in your report.

**Security context.** The loop guard is logic surface: `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions: "The builder's secure-coding rule is ASVS level 2"). The trust boundary is the hook's stdin JSON and the project files it reads. This change removes two unused imported names and does not touch that boundary.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: the test below imports the Workspace source and runs against pytest's temporary folders. Never run the hook, the installer or any test against the real `~/.claude` (your user profile's `.claude` folder), and never run `bridge-install.py`.

## Diagrams
No normative diagram covers this file (the repository has no `docs/diagrams/`). Removing two unused imported names touches no component, data, state or sequence element.

## Requirements
1. Line 36 of `bridge/cursor-bridge/loop-guard.py` reads exactly `from datetime import datetime`, with the file's existing line ending and no trailing whitespace.
2. No other line of loop-guard.py changes. The import order, the blank lines, the docstring and every function stay byte-identical.
3. No other file changes, apart from your report and (if you have something to note) one appended line in `docs/BUILDER_NOTES.md`.

## Acceptance criteria
- [ ] Behaviour is identical: every output of the loop guard (exit code, stderr reason, stdout) is byte-for-byte unchanged for every input. Removing names that no code reads cannot change any executed path.
- [ ] `python -m pytest tests/test_loop_guard.py -q -p no:cacheprovider` passes, before and after the edit, with the **same** test set: 57 passed, none skipped (on a computer with zone data; if the BUG-020 Europe/Berlin test skips for missing zone data, record the skip and its reason in the report, and the before and after counts must still be identical).
- [ ] The importlib check (the command in Constraints) prints `ok` and exits 0.
- [ ] `git diff --stat` shows `bridge/cursor-bridge/loop-guard.py | 2 +-` (one line changed) among product files and no other product file. `git diff bridge/cursor-bridge/loop-guard.py` shows exactly the one line replaced.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` reports 0 FAIL.
- [ ] No test file changed; `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/VERSION` unchanged; no entry in `docs/CHANGES.md`.
- [ ] The duplicate/dead code is gone: neither `timedelta` nor `timezone` appears anywhere in loop-guard.py.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way — an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason — append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python — `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change launches no process and must not add one.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, quoted in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only, never the real `~/.claude`.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. (This change parses no number.)
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally`/teardown with its tree, nothing outlives the test, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in):
  - Before the edit, and again after it: `python -m pytest tests/test_loop_guard.py -q -p no:cacheprovider`
  - After the edit: `python -c "import importlib.util; s = importlib.util.spec_from_file_location('loop_guard', 'bridge/cursor-bridge/loop-guard.py'); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); print('ok')"`
  - After the edit: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`
  - At the end: `git status` and `git diff --stat`, both pasted into the report.
  - Do not run the full suite, any other test file, or `tools/make-manifest.py`. The supervisor regenerates the manifest and runs the full suite after your run, and the manifest-comparing tests fail on loop-guard.py until then.
  Mutation checking is not asked for in this task.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md` (or to `bridge/cursor-bridge/CHANGELOG.md`). Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way; report them in your summary instead. Do not introduce an abstraction: this change only removes two names from one import line.

## Done
Your report is the file `handoff/REFAC-002-r1-report.md`, which you write as you go — what you did, what you changed, what you ran and what it printed, what you could not do — so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the before and after outputs of the pytest command;
- the output of the importlib check and of the windowless check;
- `git status` and `git diff --stat`;
- one sentence stating why the behaviour is identical;
- a line saying that `bridge/cursor-bridge/MANIFEST.json` is now stale for `cursor-bridge/loop-guard.py`, and that the manifest-comparing tests are expected to fail on it until the supervisor regenerates the manifest;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm — the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
