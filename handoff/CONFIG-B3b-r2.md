# CONFIG-B3b round 2: the reviewers' corrections to tools/dump-cli.py

## Objective
Round 1 (handoff/CONFIG-B3b.md, whose Context, Constraints and conventions still hold) is committed and works. Three reviews then found holes in what it guarantees, and two of them converged, which makes them blocking: a computer path inside a list default reaches the public reference unnoticed, and a default on another drive crashes the generator with a traceback instead of naming the program and the option. This round closes those and the smaller findings below. All of them are in `tools/dump-cli.py` and its generated files; nothing else changes.

Satisfies: no requirement ID (the calibration item of handoff/CONFIG-B3b.md). Tests name it `CONFIG-B3b`.

## Scope
Files you may create or modify:
- tools/dump-cli.py
- docs/cli-reference.json (regenerated)
- docs/CLI_REFERENCE.md (regenerated)
- docs/BUILDER_NOTES.md
- handoff/CONFIG-B3b-r2-report.md

Do not modify anything else.

## Out of scope
- Every file under `tests/`. The supervisor has added ten round-2 tests to `tests/test_dump_cli.py` (the functions named `test_cfgb3b_r2_*`); they hold the criteria. Do not edit any test file.
- Every file under `bridge/` (the six `build_parser()` extractions of round 1 are accepted as they are), `.github/`, `.githooks/`, `.cursor/`, the records under `docs/` other than the three files in Scope, `handoff/` other than your report.
- Any dependency; any subprocess.

## Context
- Round 1's generator is `tools/dump-cli.py` as committed. Read it whole first.
- **Security context, corrected.** Round 1's brief said the generator imports "only the seven argparse programs". Requirement 4 of that brief (discovery from the source) means it imports every command program in its own repository's `bridge/cursor-bridge/` that defines a top-level `build_parser()`, today seven. That is accepted: the pre-commit hook and CI already run that folder's code. Hand-parsed programs are still never imported.
- The project's precedent for importing a program without writing bytecode is `bridge/cursor-bridge/inventory-check.py` lines 199-210: `sys.dont_write_bytecode` set to `True` around the load and restored in `finally`.
- On every platform, a text-mode `open(...).read()` with the default `newline=None` translates `\r\n` to `\n`. So round 1's mutation (a) (dropping `normalise()`) was an equivalent mutant everywhere, not only on Windows. The Ubuntu runner checks files out with LF.

## Requirements
1. **Defaults at any depth (Review A S1, the security auditor's advisory 1, converged).** A list or tuple default is judged element by element, at any depth, by the same rule as a string default. An absolute path under the program's own folder becomes `<bridge folder>/<relative path with forward slashes>`. Any other absolute path makes the generator exit 1, printing one line that names the program's file name and the option (its first option string, or its dest for a positional), and write nothing.
2. **Another drive (Review A S2, advisory 2, converged).** When `os.path.relpath` raises `ValueError` (a default on another drive on Windows), refuse exactly as for a path outside the folder: exit 1, one line naming the program and the option, no traceback, nothing written. Judge "outside" as `rel == os.pardir or rel.startswith(os.pardir + os.sep)`, not `rel.startswith("..")`.
3. **No computer path in any string (advisory 1, Requirement 5 of round 1).** After the reference data is built, every string in it is checked: each command's usage and description, each sub-command's description, every action's help, choices and default (after the placeholder). A string that contains any of the following makes the generator exit 1, printing one line naming the program's file name (and the option, where the string belongs to one), and write nothing:
   - the repository's folder (as `repo_root()` returns it, and the same with forward slashes);
   - the home folder (`os.path.expanduser("~")`);
   - the current folder (`os.getcwd()`).

   A folder that is a filesystem root (equal to its own drive or anchor, such as `/` or `C:\`) is not checked, since every path would match it.
4. **A command with no module docstring (Review A S3)** makes the generator exit 1, printing one line naming its file name, and write nothing. No traceback.
5. **`--check` returns the refusal (Review A S5).** In `--check`, any refusal of Requirements 1 to 4 (and round 1's `ArgumentParser`-without-`build_parser()` rule) exits 1 with the same line, never 0. Round 1 already does this; keep it.
6. **No bytecode (Review A C1).** Neither a run nor `--check` writes `__pycache__` or any `.pyc` under `bridge/cursor-bridge/`, whatever `PYTHONDONTWRITEBYTECODE` says. Set `sys.dont_write_bytecode = True` around the imports and restore the previous value in `finally`, as `inventory-check.py` does.
7. **Usage errors by argparse itself (Review A C2).** Parse with `parse_args`, the parser built with `allow_abbrev=False`, so `--che` is a usage error. Drop round 1's `parse_known_args` plus hand check. An unknown argument or a stray positional exits 2 with argparse's usage line, and nothing is written.
8. **One place for each (Review A C3).** One function renders an action's Markdown line (used for top-level actions and sub-command actions alike), and one function produces the JSON text (used by the writing run and by `--check`).
9. **Markdown, whole (Review A S6, C4, C5).** `docs/CLI_REFERENCE.md` keeps round 1's layout, with these rules made exact:
   - Each command's section starts with a heading line (starting with `#`) holding the command's file name. Each sub-command's part starts with a heading line holding the sub-command's name.
   - A command's description, a sub-command's description, and a docstring command's usage are each shown in a fenced block: a line of three backticks, the text's lines (`text.splitlines()`), and a line of three backticks. A description that is `null` is left out.
   - Each action (argument or option) is exactly one line holding, in this order:
     - its label in backticks (its option strings joined by one space, or its dest for a positional);
     - `default: ` and the JSON of its default (`null` included);
     - `required: ` and `true` or `false`;
     - when it has choices, `choices: ` and the JSON list;
     - its help, when there is one.
10. **Builder notes (Review A S4).** Rewrite your own `2026-10-19 CONFIG-B3b` line in `docs/BUILDER_NOTES.md` so it states the fact in the Context above (mutation (a) is equivalent on every platform; the Ubuntu runner checks out LF). Change no other line.
11. **Regenerate** `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` with `python tools/dump-cli.py` after your last change. Do not edit them by hand.

## Acceptance criteria
- [ ] All 47 tests of `tests/test_dump_cli.py` pass, the ten `test_cfgb3b_r2_*` among them.
- [ ] `python tools/dump-cli.py --check` exits 0 on the repository.
- [ ] The full suite passes: `python -m pytest tests -q`.

## Constraints
Round 1's Constraints all hold. In particular:
- ASCII-only program text.
- Standard library only.
- No subprocess.
- Nothing read or written outside the Workspace.
- No git command but `status`, `diff`, `log`.
- No edit to any test.
- One paragraph per line in Markdown you write.
- Record friction and lessons in `docs/BUILDER_NOTES.md`, one dated line each.
- Write the minimum that meets the requirements.

Run these verification commands exactly, from the Workspace root:
1. `python tools/dump-cli.py`
2. `python tools/dump-cli.py --check`
3. `python -m pytest tests/test_dump_cli.py -q`
4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools`
5. `python -m pytest tests -q`, last, before you finish

**Mutation check, by hand, in your own run.** Once the tests pass, apply each mutation to `tools/dump-cli.py`, run `python -m pytest tests/test_dump_cli.py -q`, record which test caught it (or that none did), and restore the code. No mutation script goes in the diff. The mutations:
- (h) judge only string defaults (skip lists);
- (i) let `ValueError` from `relpath` propagate;
- (j) skip the string check of Requirement 3 for help texts;
- (k) render a `null` default as nothing;
- (l) leave `sys.dont_write_bytecode` unset;
- (m) `allow_abbrev=True`;
- (n) return 0 from `--check` on a refusal.

A mutation no test caught is reported, not fixed by editing a test.

## Done
Your report is the file `handoff/CONFIG-B3b-r2-report.md`. Write it as you go. When you finish, it holds:
- the files you changed;
- a one-paragraph summary;
- the mutation list with what caught each mutation;
- the printed result of each verification command;
- a section headed exactly `Assumed, not verified`, one item per line (what you assumed · why · what would confirm it), or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
