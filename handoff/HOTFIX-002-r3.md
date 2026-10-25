# HOTFIX-002 round 3: the docstring names the backslash form of a drive-letter path

## Objective
Round 2 (`handoff/HOTFIX-002-r2.md`, your report `handoff/HOTFIX-002-r2-report.md`) is accepted and committed: `conformance-check.py`'s docstring no longer carries a computer path into the command reference. Review A found one Should fix in it, and this round makes that fix only. It is the third and last round. The docstring now says the check treats "a drive letter with a colon and a slash" as an absolute path. The check's own regex, `ABSOLUTE_PATH`, matches a backslash after the colon too (`[\\/]`), and the backslash is the usual Windows form. Round 2's Requirement 1 also asked for "a colon and a backslash or a slash". The fix is that the drive-letter phrase reads "a drive letter followed by a colon and a backslash or a slash", re-wrapped to fit. Nothing else in the file changes.

Satisfies: there is no build-plan increment and no requirements register entry for this work (HOTFIX-002, the owner's decision D5 of 2026-10-25, as in rounds 1 and 2). The trace is Review A's Should fix on round 2. The docstring must describe exactly what `ABSOLUTE_PATH` matches.

## Scope
Files you may modify:
- bridge/cursor-bridge/conformance-check.py (the module docstring's lines 38 to 40 only)
- handoff/HOTFIX-002-r3-report.md

Do not modify anything else. Leave the round-1 and round-2 reports and both round-1 programs as they are.

## Out of scope
- `.env` and anything under `secrets/`.
- CI configuration (`.github/`).
- `docs/` and `handoff/`, except the report file the Scope section names. That includes `docs/BUILDER_NOTES.md` (your notes go in the report, as before), `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`. The supervisor regenerates the reference after your run.
- `tests/`, all of it. Do not edit any test.
- `tools/`, all of it. Do not run `tools/dump-cli.py` or `tools/make-manifest.py` against this repository. The pytest test named below runs `dump-cli.py` on a copy under pytest's temporary folder, and running that test is allowed.
- `bridge/cursor-bridge/MANIFEST.json`, `bridge/cursor-bridge/VERSION`, and every file under `bridge/` other than `conformance-check.py`.
- In `conformance-check.py`: every line outside the docstring's lines 38 to 40. That includes the `ABSOLUTE_PATH` regex at line 92, every message and all code.
- `run/` and `.git/`.

## Context
**Where you are.** This is the same checkout as rounds 1 and 2: the bridge's own source repository, on branch `hotfix-002`, with round 2 committed. The development data decision from round 1 holds: you run only the commands under Constraints, and the pytest tests build their own scratch folders under pytest's temporary folder. Never run `conformance-check.py` against this repository, a real project or `~/.claude/`.

**The lines to change.** `bridge/cursor-bridge/conformance-check.py`, lines 37 to 42 on this branch, quoted exactly:
```
    docs/diagrams/INDEX.md (missing = a diagram retrofit item); a tracked (or, outside a git
    repository, any) docs/PROJECT_STATUS.md holding an absolute path (a drive letter with a
    colon and a slash, or a macOS home under root Users, or a Linux home under root home) is
    MISSING (rule 54: no computer path enters a commit; FB-026);
  - the Workflows: line in docs/PROJECT_STATUS.md: missing, malformed, or not right after
    Phase: is MISSING (R-015);
```
The code the docstring describes, line 92, quoted exactly (it stays as it is):
```python
ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/home/")   # a drive letter path, or a macOS or Linux home
```

**What the reference test still refuses** (`tests/test_dump_cli.py`, lines 276 to 278, as in round 2): any match of `(?<![A-Za-z])[A-Za-z]:[\\/]`, the string `/home/` and the string `/Users/`. It also refuses the user's folder name between separators, and the repository's, home, current and temporary folders. The new phrase uses words only. Write "backslash" and "slash" as words, never the characters.

**Style of the docstring.** Its lines are at most 95 characters wide. The continuation lines of a list item are indented four spaces. It is ASCII-only (line 67 says so).

**Security context.** The project's ASVS level is 2 (`docs/INVENTORY.md`). This change touches documentation text only. It leaves the check's behaviour, its trust boundary and its output unchanged. `.cursor/rules/secure-coding.mdc` is in force. No secret, key or token is involved; do not read any.

**Rules already in force:** `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc`, and the frozen minimal-code rule (`bridge/cursor-bridge/minimal-code.snapshot.md`).

## Diagrams
None, as in rounds 1 and 2.

## Requirements
1. In the module docstring, "a drive letter with a colon and a slash" becomes "a drive letter followed by a colon and a backslash or a slash", with exactly those words.
2. All the other words of lines 38 to 40 stay as they are, in the same order: "repository, any) docs/PROJECT_STATUS.md holding an absolute path (", then ", or a macOS home under root Users, or a Linux home under root home) is MISSING (rule 54: no computer path enters a commit; FB-026);".
3. Lines 38 to 40 are re-wrapped as needed. They may become four lines. Every line is at most 95 characters wide, every continuation line has the four-space indent, and the text is ASCII. Line 37 and line 41 onwards do not change.
4. Afterwards, the module docstring contains no match of `(?<![A-Za-z])[A-Za-z]:[\\/]`, no `/Users/` and no `/home/`.
5. Nothing else in the file changes, byte for byte. That covers the code, the messages, the `ABSOLUTE_PATH` regex and the line endings (keep the ones the file has now).

## Acceptance criteria
- [ ] `python -m pytest "tests/test_dump_cli.py::test_cfgb3b_output_is_identical_on_two_computers_and_holds_no_path" -q -p no:cacheprovider` passes.
- [ ] `python -m pytest tests/test_hotfix25a_conformance_semgrep.py tests/test_conformance_check.py -q -p no:cacheprovider` passes.
- [ ] The docstring check (Constraints, command 3) prints `False False False`.
- [ ] `git diff -- bridge/cursor-bridge/conformance-check.py` shows one hunk, which replaces lines 38 to 40 with three or four lines. There is no whole-file change caused by line endings.
- [ ] Compared with the `git status --porcelain` output from before your run, the only change is `conformance-check.py` modified and your report file added.

## Constraints
- Do not modify any other file: not `tests/`, `docs/`, `tools/`, `MANIFEST.json`, `VERSION`, settings or CI.
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). The one exception is the temporary folder that pytest uses on its own.
- Any scratch file or test cache goes to the system temporary folder, never into the workspace. Run pytest with `-p no:cacheprovider`.
- No secret, key or token is involved. Do not read any.
- **No computer path in the report.** The report must not paste any command output or path that holds this computer's folders: no drive-letter path, no path of the user's home or profile folder, not the user name, not the temporary folder. Describe such a file in words, for example "the c0822c0 copy in the temporary folder". Paste a diff with its header lines rewritten to `a/<file>` and `b/<file>`, the file given relative to the workspace root. A pytest summary line can be pasted as printed. If a failure message shows a full path, describe it in words instead. Round 1's report pasted the temporary folder's full path, and the secret scan blocked it.
- If the brief, the rules or the tooling got in your way, write one dated line describing it under a heading `Builder notes` in your report. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not write to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Add one dated line the same way for anything you learned about a defect or a pitfall.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service, and the change launches no process.
- Never start a server, a watcher or a daemon that outlives a test.
- Do not refactor code outside the scope, even if it looks wrong. Report anything you notice in your summary instead.
- Never run `conformance-check.py`, `dump-cli.py` or `make-manifest.py` against this repository, a real project or `~/.claude/`. Run only the commands below.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff`, `git log` and `git show` only.
- Verification commands. Run them from the workspace root (the folder that holds `bridge/`, `tests/` and `tools/`), exactly as written. Each runs the same way in bash and in PowerShell:
  1. Before you change anything, run `git status --porcelain` and copy its output into the report.
  2. After your change, run `python -m pytest "tests/test_dump_cli.py::test_cfgb3b_output_is_identical_on_two_computers_and_holds_no_path" -q -p no:cacheprovider` and `python -m pytest tests/test_hotfix25a_conformance_semgrep.py tests/test_conformance_check.py -q -p no:cacheprovider`. Both must pass. Copy both summary lines into the report.
  3. The docstring check, which must print `False False False`: `python -c "import ast,re; d=ast.get_docstring(ast.parse(open('bridge/cursor-bridge/conformance-check.py',encoding='utf-8').read()),clean=False); print(bool(re.search(r'(?<![A-Za-z])[A-Za-z]:[\\\\/]', d)), '/Users/' in d, '/home/' in d)"`
  4. A width check, which must print `0`: `python -c "import ast; d=ast.get_docstring(ast.parse(open('bridge/cursor-bridge/conformance-check.py',encoding='utf-8').read()),clean=False); print(sum(1 for l in d.splitlines()[36:41] if len(l) > 95))"`. (The docstring's line 37 is the file's line 38, because the docstring starts on line 2. The slice `[36:41]` covers the file's lines 38 to 42, so it also takes in one or two unchanged lines.)
  5. `git diff -- bridge/cursor-bridge/conformance-check.py`. Copy its output into the report as printed; its headers are already `a/bridge/...` and `b/bridge/...`.
  6. After your change, run `git status --porcelain` again and copy its output into the report.
- Prefer the minimum: change only the phrase and the wrapping it needs (the frozen minimal-code rule).
- Do not test this by mutation. The tests and the checks above are the verification.

## Done
Your report is the file `handoff/HOTFIX-002-r3-report.md`. Write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing is lost if your run ends early. Follow the "no computer path in the report" constraint throughout. When you finish, the report holds:
- a list of every file you changed
- a one-paragraph summary of what you did
- the output of each verification command above: both `git status --porcelain` outputs, both pytest summary lines, the two printed check lines, and the `git diff`
- one sentence on why the program's behaviour is unchanged
- a `Builder notes` heading with your dated lines, or `Builder notes: none`
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, so a message printed earlier and then followed by more work is lost.
