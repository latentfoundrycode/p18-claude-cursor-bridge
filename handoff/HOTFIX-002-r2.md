# HOTFIX-002 round 2: no computer path in conformance-check.py's docstring

## Objective
Round 1 (`handoff/HOTFIX-002.md`, your report `handoff/HOTFIX-002-r1-report.md`) is accepted: `records-check.py` and `stage-diff.py` are the `build_parser()` move alone. This round fixes one defect that the full suite found on branch `hotfix-002`. The failing test is `tests/test_dump_cli.py::test_cfgb3b_output_is_identical_on_two_computers_and_holds_no_path`. It fails because of the module docstring of `bridge/cursor-bridge/conformance-check.py`. `conformance-check.py` is a docstring program (it has no `ArgumentParser`), so `tools/dump-cli.py` copies its whole module docstring into `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`. The test keeps every real computer path out of that committed reference. To do so, it refuses three things anywhere in the generated text: a drive-letter path (line 276, `re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]", text)`), the string `/home/` and the string `/Users/` (lines 277 and 278). The docstring's lines 37 to 39 on this branch give example paths that contain all three. This round rewords those examples in words, and changes nothing else.

Satisfies: there is no build-plan increment and no requirements register entry for this work (HOTFIX-002, the owner's decision D5 of 2026-10-25, as in round 1). The trace is the failing test above, and rule 54, which the docstring itself cites: "no computer path enters a commit".

## Scope
Files you may modify:
- bridge/cursor-bridge/conformance-check.py (the module docstring's lines 37 to 39 only)
- handoff/HOTFIX-002-r2-report.md

Do not modify anything else. Leave `handoff/HOTFIX-002-r1-report.md` and both round-1 programs as they are.

## Out of scope
- `.env` and anything under `secrets/`.
- CI configuration (`.github/`).
- `docs/` and `handoff/`, except the report file the Scope section names. That includes `docs/BUILDER_NOTES.md` (your notes go in the report, as in round 1), and `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`, which the supervisor regenerates after your run.
- `tests/`, all of it. The failing test is the acceptance test. Do not edit it or any other test.
- `tools/`, all of it. Do not run `tools/dump-cli.py` or `tools/make-manifest.py` against this repository. The supervisor regenerates the reference and restamps `MANIFEST.json` after your run. Running the pytest test named below is allowed: it runs `dump-cli.py` on a copy under pytest's temporary folder.
- `bridge/cursor-bridge/MANIFEST.json`, `bridge/cursor-bridge/VERSION`, and every file under `bridge/` other than `conformance-check.py`.
- In `conformance-check.py`: every line outside the docstring's lines 37 to 39. That includes the `ABSOLUTE_PATH` regex at line 91, every message and all code.
- `run/` and `.git/`.

## Context
**Where you are.** This is the same checkout as round 1: the bridge's own source repository, on branch `hotfix-002`. The development data decision from round 1 holds. The only things you run are the commands under Constraints. The pytest tests build their own scratch folders under pytest's temporary folder. Never run `conformance-check.py` against this repository, a real project or `~/.claude/`.

**The lines to change.** These are `bridge/cursor-bridge/conformance-check.py`, lines 36 to 41 on this branch, quoted exactly. The docstring is a plain (not raw) string, so the source text `E:\\` is `E:\` in the docstring:
```
    ROSTER.json, DESIGN.md (a design under other names is a NOTE naming them), and
    docs/diagrams/INDEX.md (missing = a diagram retrofit item); a tracked (or, outside a git
    repository, any) docs/PROJECT_STATUS.md holding an absolute path (`E:\\`, `C:/`, `/Users/`,
    `/home/`) is MISSING (rule 54: no computer path enters a commit; FB-026);
  - the Workflows: line in docs/PROJECT_STATUS.md: missing, malformed, or not right after
    Phase: is MISSING (R-015);
```
The parenthesis `(`E:\\`, `C:/`, `/Users/`, `/home/`)` names what the check treats as an absolute path. The code that does it is `ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/home/")` (line 91; it stays as it is). That is: a drive letter followed by a colon and a backslash or a forward slash, a macOS home under the root `Users` folder, or a Linux home under the root `home` folder.

**What the test refuses.** This is `tests/test_dump_cli.py`, lines 276 to 278, quoted exactly. `text` is the whole generated reference:
```python
        assert not re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]", text), re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/].{0,40}", text).group(0)
        for home_root in ("/home/", "/Users/"):
            assert home_root not in text
```
The same test also refuses the user's folder name between separators, the repository's folder, the home folder, the current folder and the temporary folder (lines 255 to 275). So the new words must name the patterns without writing any of them. The supervisor suggested "(a drive letter followed by a colon and a slash, or a path under `/Users/` or `/home/`)". That wording still holds `/Users/` and `/home/`, which lines 277 and 278 refuse, so it does not pass. Name the macOS and Linux home folders in words too, with no `/` on either side of `Users` or `home`.

**Style of the docstring.** Its lines are wrapped at most 95 characters wide. A list item starts with `  - `, and its continuation lines are indented four spaces. The docstring is ASCII-only ("ASCII-only on purpose (cp1252 consoles)", line 67).

**Security context.** The project's ASVS level is 2 (`docs/INVENTORY.md`). This change touches documentation text only. It leaves the check's behaviour, its trust boundary (the project files it reads) and its output unchanged. `.cursor/rules/secure-coding.mdc` is in force. No secret, key or token is involved; do not read any.

**Rules already in force:** `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc`, and the frozen minimal-code rule (`bridge/cursor-bridge/minimal-code.snapshot.md`).

## Diagrams
None, as in round 1.

## Requirements
1. In `bridge/cursor-bridge/conformance-check.py`'s module docstring, the parenthesised examples on lines 38 and 39 are replaced by words. The words name the same patterns `ABSOLUTE_PATH` matches: a drive letter followed by a colon and a backslash or a slash, and a home folder on macOS (under `Users` at the root) or on Linux (under `home` at the root).
2. Afterwards, the module docstring contains no match of `(?<![A-Za-z])[A-Za-z]:[\\/]`, no `/Users/`, and no `/home/`. It holds no other path of a real computer either.
3. Everything else on lines 37 to 39 keeps its meaning and its words: "a tracked (or, outside a git repository, any) docs/PROJECT_STATUS.md holding an absolute path ... is MISSING (rule 54: no computer path enters a commit; FB-026);". The list item may grow from three lines to four. Its lines keep the four-space continuation indent and are at most 95 characters wide. The new text is ASCII.
4. Nothing else in the file changes, byte for byte: line 36, line 40 onwards, every other docstring line, the code, the messages, the `ABSOLUTE_PATH` regex and the line endings (keep the ones the file has now).

## Acceptance criteria
- [ ] `python -m pytest "tests/test_dump_cli.py::test_cfgb3b_output_is_identical_on_two_computers_and_holds_no_path" -q -p no:cacheprovider` passes. Today it fails at line 276.
- [ ] `python -m pytest tests/test_hotfix25a_conformance_semgrep.py tests/test_conformance_check.py -q -p no:cacheprovider` passes.
- [ ] The docstring check (Constraints, command 4) prints `False False False`.
- [ ] `git diff -- bridge/cursor-bridge/conformance-check.py` shows a single hunk, covering lines 37 to 39 only (as replaced by three or four lines). There is no whole-file change caused by line endings.
- [ ] Compared with the `git status --porcelain` output from before your run, the only change is `conformance-check.py` modified and your report file added.

## Constraints
- Do not modify any other file: not `tests/`, `docs/`, `tools/`, `MANIFEST.json`, `VERSION`, settings, or CI.
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). The only exception is the temporary folder that pytest uses on its own.
- Any scratch file or test cache goes to the system temporary folder, never into the workspace. Run pytest with `-p no:cacheprovider`.
- No secret, key or token is involved. Do not read any.
- If the brief, the rules or the tooling got in your way, write one dated line describing it under a heading `Builder notes` in your report. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not write to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Add one dated line the same way for anything you learned about a defect or a pitfall.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service, and the change launches no process.
- Never start a server, a watcher or a daemon that outlives a test.
- Do not refactor code outside the scope, even if it looks wrong. If you notice another docstring or text that could carry a computer path into the reference, report it in your summary instead of changing it.
- Never run `conformance-check.py`, `dump-cli.py` or `make-manifest.py` against this repository, a real project or `~/.claude/`. Run only the commands below.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff`, `git log` and `git show` only.
- Verification commands. Run them from the workspace root (the folder that holds `bridge/`, `tests/` and `tools/`), exactly as written. Each one runs the same way in bash and in PowerShell:
  1. Before you change anything, run `git status --porcelain`. Copy its output into the report.
  2. Before you change anything, run `python -m pytest "tests/test_dump_cli.py::test_cfgb3b_output_is_identical_on_two_computers_and_holds_no_path" -q -p no:cacheprovider`. Copy its last summary line into the report; it should fail.
  3. After your change, run the same command again; it must pass. Then run `python -m pytest tests/test_hotfix25a_conformance_semgrep.py tests/test_conformance_check.py -q -p no:cacheprovider`, which must also pass. Copy both summary lines into the report.
  4. The docstring check, which must print `False False False`: `python -c "import ast,re; d=ast.get_docstring(ast.parse(open('bridge/cursor-bridge/conformance-check.py',encoding='utf-8').read()),clean=False); print(bool(re.search(r'(?<![A-Za-z])[A-Za-z]:[\\\\/]', d)), '/Users/' in d, '/home/' in d)"`
  5. `git diff -- bridge/cursor-bridge/conformance-check.py`. Copy its output whole into the report.
  6. After your change, run `git status --porcelain` again. Copy its output into the report.
- Prefer the minimum: change only the words of the parenthesis and the wrapping it needs (the frozen minimal-code rule).
- Do not test this by mutation. The tests and the checks above are the verification.

## Done
Your report is the file `handoff/HOTFIX-002-r2-report.md`. Write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing is lost if your run ends early. When you finish, the report holds:
- a list of every file you changed
- a one-paragraph summary of what you did
- the output of each verification command above: both `git status --porcelain` outputs, every pytest summary line, the docstring check's printed line, and the `git diff` whole
- one sentence on why the program's behaviour is unchanged
- a `Builder notes` heading with your dated lines, or `Builder notes: none`
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, so a message printed earlier and then followed by more work is lost.
