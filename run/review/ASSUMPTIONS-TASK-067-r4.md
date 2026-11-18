# ASSUMPTIONS: TASK-067, the builders' "Assumed, not verified" lists with the supervisor's dispositions

docs/HARDENING.md, TASK-067, carries the dispositions of rounds 5 and 6. Extra places to look, never the review's scope.

## Round 1 (handoff/TASK-067-r1-report.md)

- A combined-diff body line is added when its parent columns hold `+` and no `-`, and the merge's name-status list matches its patch. Disposition: superseded (round 2's column rule; from round 5 the file list is `--raw` and every section is matched to its record, a disagreement CANNOT SCAN).
- `os.path.expanduser("~")` on Windows reads `USERPROFILE` before `HOME`. Disposition: accepted (Python's documented order; the tests set both).
- The owner segment is the second-to-last non-empty path segment of the remote's address. Disposition: accepted (GitHub's two-segment form; a longer path drops a different word, never adds a finding).
- An email with no `@` has no local part. Disposition: accepted.
- The identity's name matches exactly; only the address ignores letter case. Disposition: accepted (a case variant is searched, the safe side).
- A short name equal to a public name is skipped as short. Disposition: accepted (both skip it).
- `git config --get` exit 1 means unset; any other non-zero exit fails the scan. Disposition: accepted (fails closed).
- A patch path absent from the file list is omitted. Disposition: superseded (round 2: a disagreement is CANNOT SCAN).

## Round 2 (handoff/TASK-067-r2-report.md)

- The combined-hunk column rule (space and minus consume a parent's count, plus only the new side). Disposition: accepted (the merge cases, the octopus case of round 6).
- The same rule for three or more parents. Disposition: accepted (round 6's octopus case).
- An unquoted path with a space ends at one trailing tab. Disposition: superseded (`core.quotePath=true` and sections matched by index line from round 5).
- A hunk line beginning with a backslash is only the no-newline marker. Disposition: accepted.
- `--src-prefix`/`--dst-prefix` override `diff.srcPrefix`/`diff.dstPrefix`. Disposition: verified (the supervisor's round-6 case `..._named_like_a_prefix_...[swapped]`, added after mutant n08 survived).

## Round 3 (handoff/TASK-067-r3-report.md)

- `--submodule=short` overrides a user's `diff.submodule` for the list and the patch. Disposition: accepted (a gitlink is read from its raw record, mode 160000 first from round 6; a patch that inlined a submodule's files would disagree with the list, CANNOT SCAN, the safe side).

## Round 4 (handoff/TASK-067-r4-report.md)

- `--no-replace-objects` holds under `core.useReplaceRefs` and `GIT_REPLACE_REF_BASE`. Disposition: accepted (git's option turns replacement off whatever names the refs).
- `--text` overrides every binary source. Disposition: superseded (the first resolution: `--text` dropped; content decides).
- A CR or NUL inside a line, or no final newline, under `--text`. Disposition: superseded (content classification from round 5).

## Round 5 (handoff/TASK-067-r5-report.md)

- An unquoted `diff --git` header holding a space splits at the equal ` b/`; claimed unreachable under `core.quotePath=true`. Disposition: rejected as stated (`core.quotePath` quotes only special characters, not a space), harmless (the split takes the equal sides; sections are matched by their index line).

## Round 6 (handoff/TASK-067-r6-report.md)

- git prints a section for every changed single-parent record. Disposition: accepted (Review A's probes: mode-only, 100% rename, empty add, delete, rename with mode, all OK; a missing one is CANNOT SCAN, the safe side).
- The NUL-removed view's line numbers equal the UTF-16 view's except where a code unit holds 0x0A or 0x0D (U+010A). Disposition: accepted (a decided limit: one hit at two numbers, never a pass).
- `lead + at` maps a trimmed middle's opcode index back. Disposition: accepted (read by Review A; the far-edit and one-line-edit cases).
