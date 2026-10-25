# HOTFIX-002: the hotfix's two new programs, with a top-level build_parser()

## Objective
This increment is one part of carrying the bridge's hotfix 2026.10.25a onto main (HOTFIX-002, the owner's decision D5 of 2026-10-25). The hotfix was merged on branch `release/2026.10.11` as commit `c0822c0`. It adds two command programs, `bridge/cursor-bridge/records-check.py` and `bridge/cursor-bridge/stage-diff.py`. This branch (`hotfix-002`) already holds the rest of the carry, including the tests for both programs, but not the two programs themselves. They were left out because main's command reference rule refuses them as written. `tools/dump-cli.py` requires every program that uses `argparse.ArgumentParser` to define a module-level `def build_parser():` that returns the parser without parsing. In `c0822c0`'s text, both programs build their parser inside `main()` instead. Your job is to create both files from `c0822c0`'s text with exactly one change in each: the parser's construction moves into a top-level `build_parser()` placed directly above `main()`, and `main()` calls `build_parser().parse_args()`. Nothing else in either file changes, and both programs behave exactly as they did.

Satisfies: there is no build-plan increment and no requirements register entry for this work. The supervisor defined the increment under the owner's decision D5 (2026-10-25). The trace is `tests/test_hotfix25a_stage_records_install.py`, which is already on the branch. Its module docstring names hotfix 2026.10.25a, `stage-diff.py` (2026-10-25 C7) and `records-check.py` (2026-10-18 C1). Do not add a test.

## Scope
Files you may create:
- bridge/cursor-bridge/records-check.py
- bridge/cursor-bridge/stage-diff.py
- handoff/HOTFIX-002-r1-report.md

Do not modify anything else. Neither program exists on this branch today, so both are new files.

## Out of scope
- `.env` and anything under `secrets/`.
- CI configuration (`.github/`).
- `docs/` and `handoff/`, except the report file the Scope section names. That includes `docs/BUILDER_NOTES.md`: your builder notes go in the report instead (see Constraints). It also includes `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`, which the supervisor regenerates with `tools/dump-cli.py` after your run. Do not run `tools/dump-cli.py` at all.
- `tests/`, all of it. `tests/test_hotfix25a_stage_records_install.py` is the acceptance test. Do not edit it, `tests/conftest.py`, or any other test.
- `tools/`, all of it (`dump-cli.py`, `make-manifest.py` and the rest).
- `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/VERSION`. The supervisor restamps them after your run. Do not run `tools/make-manifest.py`.
- Every other file under `bridge/`, including `bridge-install.py`, `sync-check.py`, `CHANGELOG.md` and `settings.bridge.json`.
- `run/`, which holds the supervisor's records (including `run/supervisor/`), and `.git/`.

## Context
**Where you are.** This checkout is the bridge's own source repository, on branch `hotfix-002` (checkpoint commit `04d4b3f`). It is not a supervised product. The commit `c0822c0` can be reached from here. Read the hotfix's text with `git show c0822c0:bridge/cursor-bridge/records-check.py` and `git show c0822c0:bridge/cursor-bridge/stage-diff.py`. That text is the source of truth. Any other copy you may find in the repository is not.

**Development data:** the inventory's decision (`docs/INVENTORY.md`, Resources) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For this increment, that means you run only the acceptance test and the checks listed under Constraints. The acceptance test builds scratch git repositories under pytest's `tmp_path` and runs the two programs there. Never run `records-check.py`, `stage-diff.py` or `bridge-install.py` against this repository, against a real project, or against `~/.claude/`.

**The rule the files must pass.** It is in `tools/dump-cli.py`. Quoted exactly:
```python
def has_top_level_build_parser(path):
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    return any(isinstance(n, ast.FunctionDef) and n.name == "build_parser" for n in tree.body)
```
and, in `classify_program`:
```python
    if has_top_level_build_parser(path):
        return "argparse"
    if "ArgumentParser" in text:
        print("dump-cli: %s uses ArgumentParser but has no top-level build_parser()" % name, file=sys.stderr)
        raise DumpCliError(1)
```
`dump-cli.py` loads the module and calls `mod.build_parser()` with no arguments. It then reads the returned parser's `description` and `_actions`. So `build_parser()` takes no parameters, parses nothing, and returns the `argparse.ArgumentParser`.

**The house pattern.** This is `bridge/cursor-bridge/sync-check.py`, lines 58 to 68, quoted exactly:
```python
def build_parser():
    ap = argparse.ArgumentParser(description="Compare local <base> with the remote's <base>.")
    ap.add_argument("--apply", action="store_true", help="fast-forward local <base> when BEHIND")
    ap.add_argument("--strict", action="store_true", help="project end: OFFLINE/UNPUBLISHED fail")
    ap.add_argument("--base", default="main")
    ap.add_argument("--remote", default="origin")
    return ap


def main():
    a = build_parser().parse_args()
```

**What moves, in `c0822c0`'s text.**

- `records-check.py`: `def main():` is at line 91. Lines 92 to 95 build the parser: `ap = argparse.ArgumentParser(description="Every TASK/BUG/FIX id merged since a commit has its docs/CHANGES.md line.")` and three `ap.add_argument` lines, for `--since`, `--ref` and `--changes`. Line 96 is `    a = ap.parse_args()`. The function before `main()` is `def commits(since, ref):`, which ends at line 88.
- `stage-diff.py`: `def main():` is at line 147. Lines 148 to 153 build the parser: `ap = argparse.ArgumentParser(description="Write a stage's whole change and its parts from its squash commits.")` and five `ap.add_argument` lines, for `commits`, `--from-file`, `--out`, `--name` and `--ref`. Line 154 is `    a = ap.parse_args()`. The function before `main()` is `def whole_tree(last, setback):`, which ends at line 144.

Check these line numbers against `git show` before you edit. If they do not match, stop and report.

**Text pitfalls in the source.**

- `records-check.py`, line 36 (`TRAIL_RX`), holds two non-ASCII characters inside a character class: an em dash and an en dash (`[-—–]`). They must stay the same UTF-8 bytes. A shell redirection or an editor that re-encodes the file would change them, and the `git diff --no-index` check below would show it.
- The line endings must be the ones in `c0822c0`'s blobs. `.gitattributes` sets an eol only for `.githooks/**`, so nothing in this repository normalises these two paths for you. In Windows PowerShell, `git show ... > file` re-encodes the output (UTF-16 or a BOM, and CRLF), so do not create the files that way. Any method that writes the blob's bytes unchanged is fine. The diff check below proves the result.

**Security context.** This increment changes nothing in the security picture. The project's ASVS level is 2 (`docs/INVENTORY.md`). The trust boundary of both programs is their command line and the git repository they read. Both programs only read, except that `stage-diff.py` writes into its `--out` folder. Every subprocess in them is already windowless (`NO_WINDOW`). This increment changes none of that and adds no new surface. `.cursor/rules/secure-coding.mdc` is in force. No secret, key or token is involved; do not read any.

**Rules already in force:** `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc`, and the frozen minimal-code rule (`bridge/cursor-bridge/minimal-code.snapshot.md`). Read them as the rules in force. Do not copy them anywhere.

## Diagrams
None. This repository has no normative diagrams for this work, and the increment is not in `docs/BUILD_PLAN.md`.

## Requirements
1. `bridge/cursor-bridge/records-check.py` exists. It is `c0822c0`'s `bridge/cursor-bridge/records-check.py` with exactly one change. The parser construction (lines 92 to 95 there) becomes the body of a module-level `def build_parser():`, which ends with `return ap`. That function stands directly above `def main():` and after `commits()`, with two blank lines before and after it, as in `sync-check.py`. The first line of `main()` is `    a = build_parser().parse_args()`. It replaces the four construction lines and `    a = ap.parse_args()`.
2. `bridge/cursor-bridge/stage-diff.py` exists. It is `c0822c0`'s `bridge/cursor-bridge/stage-diff.py` with the same single change, applied to its lines 148 to 153. `build_parser()` stands directly above `def main():` and after `whole_tree()`, with two blank lines before and after it. The first line of `main()` is `    a = build_parser().parse_args()`.
3. Inside each `build_parser()`, the construction lines are exactly as in `c0822c0`: the same order, the same four-space indentation, every argument name, `nargs`, `required`, `default`, `help` and `description` unchanged, and the same variable name `ap`.
4. Everything else in both files is byte-for-byte `c0822c0`'s. That covers the shebang, the module docstring, the imports, the constants, every other function, every message, every exit code, the `if __name__ == "__main__":` block, the non-ASCII characters on line 36 of `records-check.py`, the line endings and the final newline. Add no comment, no docstring and no import.
5. Both programs behave exactly as before: they accept the same arguments, with the same defaults, and give the same output and the same exit codes.

## Acceptance criteria
- [ ] `python -m pytest tests/test_hotfix25a_stage_records_install.py -q -p no:cacheprovider` passes in full. Its four stage-diff tests and two records-check tests exercise the two programs. Its install test (`test_a_release_branch_as_merged_is_installed_and_nothing_else_it_refused`) copies the whole of `bridge/` into a scratch repository and stamps it there, so it sees your files too.
- [ ] The `build_parser` check (Constraints, command 4) exits 0: both files have a top-level `def build_parser`. That is the exact test `tools/dump-cli.py` applies. Do not run `dump-cli.py` itself: it writes `docs/`, and its `--check` mode fails until the supervisor regenerates the reference.
- [ ] For each file, `git diff --no-index` against `c0822c0`'s blob (Constraints, command 5) shows only the move. It adds `def build_parser():`, the construction lines, `    return ap` and the blank lines around them. Inside `main()`, it replaces the construction lines and `    a = ap.parse_args()` with `    a = build_parser().parse_args()`. There is no other hunk, no whole-file change caused by line endings, and no `\ No newline at end of file` marker that the blob does not already have.
- [ ] No file outside the Scope is changed or created. Compared with the `git status --porcelain` output from before your run, the only new entries are the two programs and your report file.

## Constraints
- Do not modify any other file: not `tests/`, `docs/`, `tools/`, `MANIFEST.json`, `VERSION`, settings, or CI.
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). The one exception is the system temporary folder, for the scratch files named below. Everything you need is inside the workspace, and everything you produce goes inside it.
- Any scratch file or test cache goes to the system temporary folder (`$env:TEMP` in PowerShell, which is the folder Python's `tempfile.gettempdir()` returns), never into the workspace. Run pytest with `-p no:cacheprovider`. Delete your scratch files from the temporary folder when you are done.
- No secret, key or token is involved. Do not read any.
- If the brief, the rules or the tooling got in your way, write one dated line describing it under a heading `Builder notes` in your report. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. This increment's scope keeps `docs/` closed, so do not write to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Add one dated line the same way for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round), so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless. This change adds no process launch. Keep it that way: the existing `NO_WINDOW` calls stay as they are.
- Never start a server, a watcher or a daemon that outlives a test.
- Do not refactor code outside the scope, even if it looks wrong. That applies inside both programs too: the move is the only change. If you notice something worth changing (a message, a regex, an edge case), report it in your summary instead.
- Never run the product against the owner's live data. Here that means: never run `records-check.py`, `stage-diff.py` or `bridge-install.py` against this repository, a real project or `~/.claude/`. Run only the commands below.
- Follow the existing conventions: the `build_parser()` / `main()` shape of `sync-check.py`, quoted under Context.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff`, `git log` and `git show` only.
- Verification commands. Run them from the workspace root (the folder that holds `bridge/`, `tests/` and `tools/`), in PowerShell, exactly as written:
  1. Before you change anything, run `git status --porcelain`. Copy its output into the report.
  2. Write `c0822c0`'s two blobs, byte for byte, to the temporary folder for the comparison: `python -c "import os,subprocess,tempfile; [open(os.path.join(tempfile.gettempdir(),'hotfix002-c0822c0-'+n),'wb').write(subprocess.run(['git','show','c0822c0:bridge/cursor-bridge/'+n],capture_output=True,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)).stdout) for n in ('records-check.py','stage-diff.py')]"`
  3. The acceptance test: `python -m pytest tests/test_hotfix25a_stage_records_install.py -q -p no:cacheprovider`. Copy its last summary line into the report.
  4. The `build_parser` check, which must exit 0: `python -c "import ast,sys; [sys.exit(1) for p in ('bridge/cursor-bridge/records-check.py','bridge/cursor-bridge/stage-diff.py') if not any(isinstance(n, ast.FunctionDef) and n.name=='build_parser' for n in ast.parse(open(p,encoding='utf-8').read()).body)]"`, then `echo $LASTEXITCODE`.
  5. The move-only diffs: `git diff --no-index "$env:TEMP\hotfix002-c0822c0-records-check.py" bridge/cursor-bridge/records-check.py` and `git diff --no-index "$env:TEMP\hotfix002-c0822c0-stage-diff.py" bridge/cursor-bridge/stage-diff.py`. Each exits 1 because the files differ. Copy both outputs whole into the report.
  6. After your change, run `git status --porcelain` again. Copy its output into the report.
  7. Delete the two `hotfix002-c0822c0-*` files from `$env:TEMP`.
- Prefer reuse over new code: the move reuses the existing lines, and the shape is the one `sync-check.py` uses. Write the minimum (the frozen minimal-code rule).
- Do not test this by mutation. The acceptance test and the diff check are the verification.

## Done
Your report is the file `handoff/HOTFIX-002-r1-report.md`. Write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing is lost if your run ends early. When you finish, the report holds:
- a list of every file you changed or created
- a one-paragraph summary of what you did
- the output of each verification command above: both `git status --porcelain` outputs, the pytest summary line, the exit code of the `build_parser` check, and both `git diff --no-index` outputs whole
- one sentence on why both programs behave exactly as `c0822c0`'s do
- a `Builder notes` heading with your dated lines, or `Builder notes: none`
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: how you wrote the files without re-encoding them, which line endings the blobs have, and whether the pytest result depended on anything outside the two files. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, so a message printed earlier and then followed by more work is lost.
