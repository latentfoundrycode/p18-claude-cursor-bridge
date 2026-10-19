# CONFIG-B3b round 4: every written form of a folder; dict keys, choices, the type field and non-JSON numbers

## Objective
Round 3 (handoff/CONFIG-B3b-r3.md) is committed. Its walk and its string check work, but the security re-check found that a folder of this computer is still found only when it is written in one form. A help text holding a list of paths (Python writes each backslash twice), a JSON example in a description, the Git Bash form `/c/Users/<name>/...`, the WSL form `/mnt/c/Users/<name>/...` and a path written without its drive letter all reach the public reference with the user's name in them. Three reviews also found, independently, that a dict default whose keys cannot be JSON keys ends in a traceback. This round fixes those, with the advisories below. All of it is in `tools/dump-cli.py` and its regenerated files.

Satisfies: no requirement ID (the calibration item of handoff/CONFIG-B3b.md). Tests name it `CONFIG-B3b`.

## Scope
Files you may create or modify:
- tools/dump-cli.py
- docs/cli-reference.json (regenerated)
- docs/CLI_REFERENCE.md (regenerated)
- docs/BUILDER_NOTES.md
- handoff/CONFIG-B3b-r4-report.md

Do not modify anything else.

## Out of scope
- Every file under `tests/`. The supervisor has added round-4 tests to `tests/test_dump_cli.py` (the functions named `test_cfgb3b_r4_*`, 23 cases with their parameters). Sixteen of them are red today; seven are green guards for mutants the reviewers found surviving. Do not edit any test file.
- Everything else, as in rounds 1 to 3: `bridge/`, `.github/`, `.githooks/`, `.cursor/`, the records under `docs/` other than the three files in Scope, `handoff/` other than your report. No dependency, no subprocess.
- A link (symlink or junction) placed at one of the two output files, and folders of this computer other than the three named below: recorded by the supervisor, not this round's work.

## Context
- Rounds 1 to 3's briefs (`handoff/CONFIG-B3b.md`, `-r2.md`, `-r3.md`) still hold where this file does not change them. Read `tools/dump-cli.py` whole first.
- `os.path.normcase` lowers the case and turns `/` into `\` on Windows, and returns its argument unchanged elsewhere. It does not merge a doubled separator and does not add or remove a drive letter.
- `os.path.splitdrive("C:\\Users\\x")` gives `("C:", "\\Users\\x")`; off Windows the drive is always empty.
- JSON has no NaN and no infinity; `json.dumps(float("nan"))` writes `NaN`, which is not JSON. JSON object keys are strings.

## Requirements
1. **One canonical form for comparing (security re-check, blocking).** Before a text is compared with a folder, both are put in one canonical form: `os.path.normcase`, then every run of one or more `\` or `/` replaced by a single `/`. One function does this, used for the text and for every folder.
2. **Every folder with and without its drive (security re-check, blocking).** The three folders stay as in round 3: the repository, the home folder and the current folder. For each, two fragments are compared, both in the canonical form: the whole folder, and the folder without its drive (`os.path.splitdrive(folder)[1]`). A fragment that is empty or is the root (`/` in the canonical form) is skipped, so a folder at the root of its drive leaves only the whole-folder fragment, or none. The Git Bash and WSL forms are caught by the fragment without the drive.
3. **Dict keys are distinct strings (the supervisor, the security re-check and Review A S1, convergent).** In the walk of Requirement 1 of round 3, a dict key is walked like any leaf. After the walk, a key that is not a string makes the generator refuse, naming the program and the option. So does a key whose walked string another key of the same dict already gave. A string or an `os.PathLike` key is walked to a string (the placeholder under the program's folder, a refusal elsewhere).
4. **No number JSON cannot hold (Review A, noted 2).** A float that is NaN or an infinity, anywhere in a default or a choice, makes the generator refuse, naming the program and the option.
5. **Choices are walked like a default (security re-check, advisory).** An action's choices are walked exactly as its default is (round 3's Requirement 1 and Requirements 3 and 4 here): a tuple becomes a list, an `os.PathLike` its string, an absolute path under the program's folder the placeholder, any other absolute path or type a refusal by name. The string check then reads every string inside them, as it reads a default's.
6. **The type field is checked (security re-check, advisory).** The action's `type` name written to the reference goes through the string check like its dest.
7. **Regenerate** both reference files after your last change, with `python tools/dump-cli.py`.

## Acceptance criteria
- [ ] All tests of `tests/test_dump_cli.py` pass, the `test_cfgb3b_r4_*` among them.
- [ ] `python tools/dump-cli.py --check` exits 0 on the repository.
- [ ] The full suite passes: `python -m pytest tests -q`.

## Constraints
Rounds 1 to 3's Constraints all hold. In particular:
- ASCII-only program text.
- Standard library only.
- No subprocess.
- Nothing outside the Workspace.
- No git command but `status`, `diff`, `log`.
- No edit to any test.
- One paragraph per line in Markdown you write.
- Record friction and lessons in `docs/BUILDER_NOTES.md`, one dated line each.
- The minimum code: one canonical-form function, one fragment list, the walk extended rather than a second walk.

Run, from the Workspace root:
1. `python tools/dump-cli.py`
2. `python tools/dump-cli.py --check`
3. `python -m pytest tests/test_dump_cli.py -q`
4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools`
5. `python -m pytest tests -q`, last

**Mutation check, by hand, in your own run.** Apply each mutation to `tools/dump-cli.py`, run `python -m pytest tests/test_dump_cli.py -q`, record which test caught it (or that none did), and restore the code. No mutation script goes in the diff. The mutations:
- (u) compare without merging runs of separators;
- (v) drop the fragment without the drive;
- (w) let a key that is not a string through;
- (x) skip the type field in the string check;
- (y) check only the choices that are strings;
- (z) let a NaN default through.

A mutation no test caught is reported, not fixed by editing a test.

## Done
Your report is `handoff/CONFIG-B3b-r4-report.md`. Write it as you go. When you finish, it holds:
- the files you changed (only those whose content has a diff: a file git shows as modified for its line endings alone is not one);
- a one-paragraph summary;
- the mutation list with what caught each mutation;
- the printed result of each verification command;
- a section headed exactly `Assumed, not verified`: one item per line (what you assumed · why · what would confirm it), including any library behaviour your check relies on, or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
