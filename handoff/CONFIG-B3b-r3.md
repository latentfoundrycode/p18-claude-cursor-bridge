# CONFIG-B3b round 3: the computer-path check, made real; the Markdown list items back

## Objective
Round 2 (handoff/CONFIG-B3b-r2.md) is committed. Both reviewers then found the same blocking defect, independently: Requirement 3's string check reads a default through `json.dumps`, which doubles every backslash and escapes non-ASCII. On Windows, the computer that generates the files, a home or repository path inside a default therefore never matches, and the user's name reaches the public reference. A dict default is never judged at all. Review A also found that the Markdown action lines lost their list marker and separators, so each Options section renders as one paragraph. This round fixes those and the advisories below. All of it is in `tools/dump-cli.py` and its regenerated files.

Satisfies: no requirement ID (the calibration item of handoff/CONFIG-B3b.md). Tests name it `CONFIG-B3b`.

## Scope
Files you may create or modify:
- tools/dump-cli.py
- docs/cli-reference.json (regenerated)
- docs/CLI_REFERENCE.md (regenerated)
- docs/BUILDER_NOTES.md
- handoff/CONFIG-B3b-r3-report.md

Do not modify anything else.

## Out of scope
- Every file under `tests/`. The supervisor has added nineteen round-3 tests to `tests/test_dump_cli.py` (the functions named `test_cfgb3b_r3_*`). Seven of them are red today; twelve are green guards for mutants the reviewers found surviving. Do not edit any test file.
- Everything else, as in rounds 1 and 2: `bridge/`, `.github/`, `.githooks/`, `.cursor/`, the records under `docs/` other than the three files in Scope, `handoff/` other than your report. No dependency, no subprocess.

## Context
- Rounds 1 and 2's briefs (`handoff/CONFIG-B3b.md`, `handoff/CONFIG-B3b-r2.md`) still hold where this file does not change them. Read `tools/dump-cli.py` whole first.
- `os.path.normcase` lowers the case and turns `/` into `\` on Windows, and returns its argument unchanged elsewhere. Comparing `os.path.normcase(text)` with `os.path.normcase(fragment)` therefore matches a Windows path in any case and with either separator.
- An `os.PathLike` default (for example `pathlib.Path`) is a path: `os.fspath(value)` gives its string.

## Requirements
1. **One walk over a default (both reviewers, blocking).**
   - A default is walked as a value. A string is a leaf. An `os.PathLike` is a leaf, taken as `os.fspath(value)`. A list, a tuple or a dict is walked through every element (for a dict: every key and every value), at any depth.
   - Each string leaf that is an absolute path is judged by round 2's rule. Under the program's own folder it becomes `<bridge folder>/<relative path with forward slashes>`. Anywhere else, including another drive, the generator refuses, naming the program and the option.
   - The walk returns the JSON value: a list for a list or a tuple, a dict with the same keys for a dict, the string or placeholder for a leaf, the value itself for a number, a boolean or `null`.
   - Any other type the walk meets makes the generator refuse, naming the program and the option, never a traceback.
2. **The string check reads strings, never JSON text (both reviewers, blocking).** Requirement 3 of round 2 is applied to every string of the built data as a string:
   - each command's usage and description;
   - each sub-command's name and description;
   - each action's option strings, dest and help;
   - each choice;
   - every string inside its default, walked as in Requirement 1 after the placeholder.

   Nothing is checked through `json.dumps`.
3. **Every folder in every form (Review A S1, the security advisory, convergent).** The three folders are the repository, the home folder (`os.path.expanduser("~")`) and the current folder (`os.getcwd()`). Each is compared with `os.path.normcase` on both sides, so on Windows a folder written in another case or with forward slashes is caught. A folder that is a filesystem root is still skipped. Remove round 2's separate forward-slash fragment for the repository; `normcase` covers it.
4. **One helper per thing (Review A's noted 1, the C3 class).**
   - One function checks one action's strings, used for top-level and sub-command actions alike.
   - One expression computes an action's label, used everywhere a label is needed.
   - One function renders one Positionals or Options section, used for commands and sub-commands alike.
5. **Markdown action lines are list items (Review A B2, blocking).** Each action line starts with `- ` and separates its fields with `; `, as round 1 did, in round 2's order:
   - the label in backticks;
   - `default: ` and the JSON of the default (`null` included);
   - `required: true` or `required: false`;
   - when it has choices, `choices: ` and the JSON list;
   - its help, when there is one.

   For example: ``- `--mode`; default: "done"; required: false; choices: ["plan", "done"]``.
6. **Regenerate** both reference files after your last change, with `python tools/dump-cli.py`.

## Acceptance criteria
- [ ] All tests of `tests/test_dump_cli.py` pass, the nineteen `test_cfgb3b_r3_*` among them (one is skipped off Windows).
- [ ] `python tools/dump-cli.py --check` exits 0 on the repository.
- [ ] The full suite passes: `python -m pytest tests -q`.

## Constraints
Rounds 1 and 2's Constraints all hold. In particular:
- ASCII-only program text.
- Standard library only.
- No subprocess.
- Nothing outside the Workspace.
- No git command but `status`, `diff`, `log`.
- No edit to any test.
- One paragraph per line in Markdown you write.
- Record friction and lessons in `docs/BUILDER_NOTES.md`, one dated line each.
- The minimum code.

Run, from the Workspace root:
1. `python tools/dump-cli.py`
2. `python tools/dump-cli.py --check`
3. `python -m pytest tests/test_dump_cli.py -q`
4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools`
5. `python -m pytest tests -q`, last

**Mutation check, by hand, in your own run.** Apply each mutation to `tools/dump-cli.py`, run `python -m pytest tests/test_dump_cli.py -q`, record which test caught it (or that none did), and restore the code. No mutation script goes in the diff. The mutations:
- (o) check a default through `json.dumps` again;
- (p) skip dict values in the walk;
- (q) compare without `normcase`;
- (r) skip sub-command names;
- (s) drop the `- ` list marker;
- (t) let an `os.PathLike` reach `json.dumps`.

A mutation no test caught is reported, not fixed by editing a test.

## Done
Your report is `handoff/CONFIG-B3b-r3-report.md`. Write it as you go. When you finish, it holds:
- the files you changed (only those that have a diff);
- a one-paragraph summary;
- the mutation list with what caught each mutation;
- the printed result of each verification command;
- a section headed exactly `Assumed, not verified`: one item per line (what you assumed · why · what would confirm it), including any library behaviour your check relies on, or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
