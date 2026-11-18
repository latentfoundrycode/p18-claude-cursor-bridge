---
record: brief
header: 1
id: "TASK-067"
round: 5
satisfies: [R-087]
scope: ["bridge/cursor-bridge/push-scan.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-067-r5-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-067 round 5: content decides how a file is read (R-087)

Round cause: security - both reviewers of round 4 rejected it: a merge's combined diff ignores --text, so a resolved line in a file marked -diff or binary is still hidden (B1), and --text read real binaries, whose bytes matched the path patterns (B2, a regression round 4 caused, decided by the resolution round of 2026-11-18, docs/CHANGES.md).

Blocking class: security - Review A and the security audit, round 4, B1: a merge's combined diff (diff --cc) ignores --text, so a merge whose resolution adds a line holding a path to a file a committed .gitattributes, the user's attributes or .git/info/attributes marks -diff or binary prints Binary files differ and the scan prints OK: untrusted commit content reaches a pass against R-087.

B2, the regression round 4's `--text` caused, is not lifted by this line; it is answered by the design the resolution round decided (`handoff/RESOLUTION-TASK-067.md` and `docs/CHANGES.md`, 2026-11-18), which this round builds. The reviewers confirm or deny the class line against round 4's code: the commit this brief was committed in, which is the commit you are started on (`git rev-parse HEAD` at your start).

## Objective
Build the resolution round's decision, and nothing else.

This is round 5 of TASK-067. Rounds 1 to 4 built `bridge/cursor-bridge/push-scan.py`, its allow entry and the generated files; round 4 added `--no-replace-objects` to every git call (H1, which stays) and `--text` to the patch read (H2, which this round removes). Both reviewers of round 4 found that `--text` does not reach a merge's combined diff (B1: a resolved line in a file an attribute marks `-diff` or `binary` is still shown as `Binary files differ`, and the scan prints OK) and that it reads real binaries as text, whose bytes match the path patterns about 1.5 times per MB (B2: a push adding an image ends `FOUND`, and the owner cannot clear it). The resolution round decided the design: **content decides how a file is read; how git shows a file never does.** No tree's attributes and no user attributes file reach the reads; every file's result blob is classified by its own bytes (text, UTF-16 with a byte-order mark, or binary); a text file is read from its hunks where git shows them and otherwise by the scan's own line diffs against each preimage; a binary file is never read, only counted in one note.

Read `handoff/RESOLUTION-TASK-067.md` whole and the entry "2026-11-18 TASK-067: content decides how the pre-push scan reads a file, a resolution round (R-087)" at the top of `docs/CHANGES.md` whole. They govern wherever this brief is silent; where this brief and that `docs/CHANGES.md` entry disagree, the entry wins and you report the disagreement. Round 4's tree and the round-5 test cases are committed before this brief, and this brief is committed before your run, so the line numbers below hold when you start.

Satisfies: R-087 - The pre-push scan is a program (C2): `push-scan.py [<base>]` reads every commit of `<base>..HEAD`, its message, author and committer lines, added lines and added file names, [...]; "how a file is read rests on its content, never on an attributes file: a file whose content is binary (a NUL in its first 8000 bytes, unless it begins with a UTF-16 byte-order mark and decodes as UTF-16) is counted in a note and not read, and a text file git shows as binary is read by its lines added against every parent (the resolution round of 2026-11-18); a path compiled into a binary, a text file holding a NUL in its first 8000 bytes and UTF-16 without a byte-order mark are accepted limits"; [...]. (Full text: its row in `docs/REQUIREMENTS.md`, line 113. This round serves that clause, and "added lines" for merges and for files a local setting shows as binary.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/push-scan.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-067-r5-report.md

Limits on these files:
- `bridge/cursor-bridge/push-scan.py` changes only where K1 to K6 need it:
  - the runner `git` (50-66), only so that a call can carry extra global options before the subcommand (K1, K2) and can be given explicit empty input (K1's `hash-object --stdin`, which must never read the stdin the program inherited). Its existing global options (`--no-pager`, `--no-replace-objects`, the four `-c` pairs), its `capture_output`, `timeout=bridge_env.GIT_TIMEOUT`, `creationflags=bridge_env.NO_WINDOW` and its exception handling stay;
  - `scan_commit` (620-673): its signature and return value (to take the per-run values and to return the binary count beside what it returns now), the two `git show` calls (626-632 and 635-641), the file list's parsing (642), the patch reading (643) and what follows it, for K1 to K6. The patch call cannot go through `git_need` (frozen, and it takes no global options): call the runner `git(...)` directly and repeat `git_need`'s exit check with its exact reason (`git show failed (exit %d)`) and the decode K2 needs. `hash-object`, `rev-parse --show-object-format` and `cat-file blob` likewise go through the runner directly. Do not add a parameter to `git_need` or `git_text`;
  - `execute` (699-728), only to compute the per-run values (the empty tree's id and the hash length, once per run), to pass them in its call of `scan_commit` (715), to total the binary count over the range and to print K6's note; its base check, its names handling, its hit and FOUND/OK lines stay;
  - `added_lines` (458-540), only where K3 and K5 hook in (recording, per section, its path, its `index` ids and whether it shows hunks or a `Binary files` line). Its hunk reading, its numbering and every one of its refusals stay;
  - `_two_path_status` and `parse_name_status` (543-574), replaced by K2's raw parser;
  - `unquote_git` (326-363), only its final decode (line 363), and only if K2's lossless paths need it;
  - new functions (the raw parser, the classifier, the line diff) and one `import difflib` line beside the existing imports.

  Everything else stays byte-identical to round 4's tree, in particular: the module docstring (lines 2-19) and `build_parser` (731-737), whose text is the command reference; `say`, `ScanError`, `git_text` (69-71), `git_need` (74-78), the path and name matching (`has_path`, `has_name`, `kinds_of`, `kinds_of_parts`), the names and identity functions, `parse_commit`, `strip_side`, `_patch_lines` (373-379), `_path_from_rest`, `_parse_hunk_header`, `hit_line`, `_checked_short`, `quote_path` (594-617), `default_base`, `ensure_repository`, `ensure_commit` and `main`. Inside `scan_commit`, the placement rule (line 659, `hidden = bool(kinds_of(path, names) or kinds_of(quote_path(path), names))`, and the place strings at 665-668), the file-name hit (660-662, its condition `if status[:1] in ("A", "R"):` unchanged) and the disagreement check (670-672, its reason unchanged) keep their logic and their wording.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`; restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are not in Scope this round. Do not change the module docstring or the parser's description or help (the supervisor updates the docstring later if wanted), so neither file changes. Do not run `python tools/dump-cli.py` without `--check`; Done runs only its read-only `--check`.

Do not modify anything else. `bridge/cursor-bridge/settings.bridge.json` is done (round 1) and must not change. Every test file is read-only for you: read and run `tests/test_program_push_scan.py`, `tests/test_dump_cli.py` and `tests/test_allowlist.py`, edit none of them.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, the diagrams, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` included. The briefs of rounds 1 to 4 (`handoff/TASK-067.md`, `handoff/TASK-067-r2.md`, `handoff/TASK-067-r3.md`, `handoff/TASK-067-r4.md`), their reports (`handoff/TASK-067-r1-report.md` to `handoff/TASK-067-r4-report.md`) and `handoff/RESOLUTION-TASK-067.md` stay as they are.
- `bridge/cursor-bridge/settings.bridge.json`, `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`.
- Every test file. You add no test file and edit none; a gap is reported (Constraints, mutation self-check).
- `bridge/agents/secret-sentinel.md`, `bridge/commands/supervisor.md`, the loop's text under `bridge/cursor-bridge/workflow/` (TASK-082).
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them as Done says, and edit neither).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.
- The disagreement check (round 2's F4, `scan_commit` lines 670-672) stays exactly as written; the supervisor's mutants file marks its removal as expected to survive. Do not remove, weaken or "simplify" it.
- **Not in this round** (recorded leads; do not change their behaviour): characters of categories `Zs`, `Mn`, `Co` and filler characters printed raw in a path; a default-ignorable `Cf` character inside a name; a commit with an `encoding` header; partial-clone lazy fetch (`GIT_NO_LAZY_FETCH`); the round-3 static case for `--submodule=short` lacking a behaviour case; spaces in a printed path faking fields inside one hit line; `owner_of` on remotes with more than two path segments; resolving git's absolute path; git's stripping of trailing punctuation from an ident's name; copy (`C`) statuses (the file-name hit's condition at line 660 stays as it is).
- **Accepted limits (K9), not to be handled otherwise:** a path compiled into a binary; a text file with a NUL in its first 8000 bytes and no UTF-16 byte-order mark; UTF-16 without a byte-order mark; UTF-32 and other encodings; a binary that begins with a UTF-16 byte-order mark and decodes strictly is read as UTF-16.

## Context
**Rounds 1 to 4 govern everything this brief does not change:** `handoff/TASK-067.md` (R1-R12, M1-M13), `handoff/TASK-067-r2.md` (F1-F10, N1-N9), `handoff/TASK-067-r3.md` (G1-G7, P1-P6) and `handoff/TASK-067-r4.md` (H1-H3, Q1-Q2). Read all four whole. Their Context sections (the design `docs/DESIGN.md` C2, the privacy paragraph, the import pattern, the trust boundaries, development data, host) and their Constraints hold for this round unchanged, except where K1 to K6 change them. In particular:
- **The owner's decision of 2026-11-18 (rule 52, the owner's value):** the names of the repository's configured git identity (`git config user.name`, the local part of `git config user.email`) are public, dropped from the names searched and counted in N2, and the author and committer lines that carry the configured identity are no finding. The tests `test_r087_owner_2026_11_18_the_configured_identity_is_no_finding_anywhere` and `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped` pin it. Do not change this behaviour or those tests; if the work seems to need a change, stop and report it.
- **R11, the source scans clean:** the program's own source holds no literal of the shapes the scan reads as a path (a drive letter with a colon and a slash or backslash, `/Users/`, `/home/`, `AppData`, a URL literal such as `https:` with its slashes), and the source is ASCII only. Done steps 9 and 10 verify it.
- **The printed reasons are a closed list:** round 1's R9 (`handoff/TASK-067.md`, R9, the exit-2 line: `not inside a git repository`, `the base must not begin with "-"`, `origin/HEAD is not set; name the base, e.g. origin/main`, `the base is not a commit here`, `the names file cannot be read`, `git cannot be started`, `git <subcommand> failed (exit <code>)`, `git <subcommand> took longer than <GIT_TIMEOUT>s`) and round 2's three (`the patch and the file list disagree`, `internal error`, `the patch cannot be read`). This round adds exactly one: `a file too large to compare` (K5). Every other exit 2 this round adds (a malformed raw record, a bad id, an `index` line that disagrees, a failed read) uses a reason already on the list; name in the report which reason each one uses.

**The decision, and why.** Every attribute route (a committed `.gitattributes`, a user attributes file, `.git/info/attributes`, a diff driver's `binary` setting, `core.bigFileThreshold`) changes only how git shows a file. `--attr-source=<the empty tree>` and an empty `core.attributesFile` keep commit content and the user's attributes file out of the reads; `.git/info/attributes`, drivers and `core.bigFileThreshold` cannot be turned off by any git option, so the scan classifies each file by its result blob's own bytes and reads it by class, never by how git shows its section. A text file git shows as binary is read (never refused, never passed); a real binary is never read, even where a local `diff` attribute or a driver's `binary = false` makes git print its bytes as hunks. For a file read by line diffs, a line counts where it is added against every preimage, position by position, so a duplicate added line counts once per added copy (the combined diff's own meaning; a set difference would lose it, Review B's blocking point in the second vote). The supervisor's probe on git 2.53 (`handoff/RESOLUTION-TASK-067.md`, "The supervisor's probe") showed `--attr-source` removing a committed `-diff` for an ordinary and a combined diff, and `.git/info/attributes` still applying under it; that `-c core.attributesFile=` set empty disables a user attributes file was not probed.

**The supervisor's round-5 cases.** `tests/test_program_push_scan.py`, the section headed `# ---------------------------------------------------------------- round 5: content decides how a file is read (the resolution round)` (line 607 to the end), read it whole; they fix the expected outputs. The scratch helper `Scratch` gained `object_format` (line 61-62, `git init --object-format=`) and `write` takes bytes (96-100) in the supervisor's checkpoint. Its helpers: `NOTE_ONE` (609) is `push-scan: note - 1 binary file(s) not read`; `BINARY` (611) is a real binary by the NUL rule whose bytes hold a path on a line of their own; `_force(s, how)` (627-641) sets one route: `committed-diff` (a committed `.gitattributes` with `*.bin diff` and `*.md -diff`), `info-diff` (`.git/info/attributes` `*.bin diff`), `driver-text` (`*.bin diff=raw` with `[diff "raw"] binary = false`), `info-nodiff` (`*.md -diff`), `info-binary` (`*.md binary`), `big-file` (`core.bigFileThreshold = 1`); `_merge_ours_then` (644-650) writes a merge's result by hand so it differs from both parents; each case's `_shown` precondition (619-624) asserts how git shows the commit with the user's settings before the scan runs. The cases:
- `test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it[None]`, `[committed-diff]`, `[info-diff]`, `[driver-text]` (654): one commit adds `img/blob.bin` and `img/other.bin`, both binary by content, shown as hunks where a route forces it. Expected: exit 0, no HIT line, `push-scan: OK - 1 commit(s)` and `push-scan: note - 2 binary file(s) not read`, and neither file name in the output.
- `test_r087_a_real_binary_a_merge_writes_is_counted_and_never_read[None]`, `[info-diff]`, `[driver-text]` (670): a merge writes `BINARY` to `blob.bin`, which both parents changed, shown as combined hunks where a route forces it. Side's and main's commits each write a binary too. Expected: exit 0, no HIT line, `push-scan: OK - 3 commit(s)`, `push-scan: note - 3 binary file(s) not read` (the total over the range, K6), `blob.bin` not in the output.
- `test_r087_a_text_file_a_local_setting_shows_as_binary_is_read[info-nodiff]`, `[info-binary]`, `[big-file]` (689): a commit adds a second line holding a path to `notes.md`, which git shows as `Binary files`. Expected exactly `HIT <h> line notes.md:2 path`, exit 1.
- `test_r087_a_merge_s_resolved_line_in_a_text_file_shown_as_binary_is_read[info-nodiff]`, `[info-binary]` (702): B1. A merge resolves `m.md`'s line 2 (side `SIDE`, main `MAIN`) to a path, shown as `Binary files`. Expected exactly `HIT <merge's h> line m.md:2 path`, exit 1.
- `test_r087_a_merge_s_resolved_line_in_a_file_the_commit_marks_binary_is_read` (717): B1 through commit content: main's commit adds `.gitattributes` `*.md -diff`; the merge resolves line 2 to a path. Expected exactly `HIT <merge's h> line m.md:2 path`, exit 1.
- `test_r087_a_duplicate_added_line_counts_however_git_shows_the_file[None]`, `[info-nodiff]` (732): the parent holds `see <path>`, `base`; the commit appends `see <path>` again. Expected exactly `HIT <h> line notes.md:3 path`, exit 1 (the old line 1 is no hit), from hunks and from the line diff alike.
- `test_r087_a_duplicate_line_a_merge_adds_against_both_parents_counts` (745): under `info-nodiff`, side has `L,a,b`, main `a,b,L`, the merge `L,a,b,L,L` (L a line holding a path). Expected exit 1, exactly one HIT of the merge at `line m.md:4` or `line m.md:5`, and two other HIT lines (side's and main's).
- `test_r087_a_utf16_file_with_a_byte_order_mark_is_read_as_text[\xff\xfe-utf-16-le]`, `[\xfe\xff-utf-16-be]` (764): one commit adds `list.txt`, a byte-order mark then `Directory: x` CR LF and a backslash drive path CR LF in UTF-16, shown as `Binary files`. Expected exactly `HIT <h> line list.txt:2 path`, exit 1.
- `test_r087_a_changed_utf16_file_reports_only_its_new_lines` (774): a UTF-16LE file whose parent already holds a path on line 2 gains `two` and a `/Users/` line. Expected exactly `HIT <h> line list.txt:4 path`, exit 1.
- `test_r087_a_utf16_file_rewritten_as_utf8_is_read_never_refused` (784): a UTF-16LE parent rewritten as UTF-8 text with a path on line 2. Expected exactly `HIT <h> line list.txt:2 path`, exit 1 (read, never a refusal).
- `test_r087_git_s_content_rule_decides_at_its_8000th_byte[7999-True]`, `[8000-False]` (795): a NUL at byte offset 7999 (inside the first 8000 bytes: binary, expected exit 0, no HIT line, `NOTE_ONE`) or 8000 (text: expected exactly `HIT <h> line data.txt:2 path`, exit 1).
- `test_r087_entries_without_content_to_read_never_end_the_scan` (808): a deletion, a mode change, a pure rename, a symbolic link with a submodule entry, a type change (`t.md` made a symbolic link to `new.md`) and an octopus merge. Expected exit 0, no HIT line, `push-scan: OK - 8 commit(s)`.
- `test_r087_a_type_change_reads_the_new_entry`: `t.md` made a symbolic link whose target is a drive path (precondition: `git show --raw` lists ` T`). Expected exactly `HIT <h> line t.md:1 path`, exit 1 (K3's type change: two sections, the addition read by class).
- `test_r087_a_sha256_repository_is_read_with_its_own_ids` (832): a SHA-256 repository under `info-nodiff`; one commit adds a path line to `notes.md` and adds `BINARY` as `blob.bin`. Expected exactly `HIT <h> line notes.md:2 path`, exit 1, and `NOTE_ONE` in the output (the note is printed with FOUND too).
- `test_r087_no_attribute_decides_and_ids_are_full` (843, static): the source holds `--attr-source`, `core.attributesFile=`, `--full-index`, `--no-abbrev` and `--raw`, and neither `"--text"` nor `'--text'`.

Round 4's cases stay and must keep passing: `test_r087_a_replaced_commit_is_read_as_the_push_sends_it` (582) and `test_r087_a_text_file_the_commit_marks_binary_is_still_read[-diff]` and `[binary]` (597-598; a commit's own `.gitattributes` marks `notes.md`; expected exactly `HIT <h> line notes.md:2 path`). The round-3 static case `test_r087_a_submodule_s_own_diff_is_never_inlined` (572-577) counts `--submodule=short` and `--ignore-submodules=none` at least twice each in the source, and `test_r087_d004_every_child_process_is_bounded_by_a_timeout` (361-370) requires every `subprocess` call to be `run` with `timeout=`.

**Known failures before your change.** The supervisor's known run on round 4's tree (`run/agent/TASK-067-r5-known.out`, run with a `-k` expression selecting the round-5 cases and round 4's marks_binary pair) printed:

```
17 failed, 11 passed, 40 deselected in 22.23s
```

Its FAILED lines:

```
FAILED tests/test_program_push_scan.py::test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it[None]
FAILED tests/test_program_push_scan.py::test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it[committed-diff]
FAILED tests/test_program_push_scan.py::test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it[info-diff]
FAILED tests/test_program_push_scan.py::test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it[driver-text]
FAILED tests/test_program_push_scan.py::test_r087_a_real_binary_a_merge_writes_is_counted_and_never_read[None]
FAILED tests/test_program_push_scan.py::test_r087_a_real_binary_a_merge_writes_is_counted_and_never_read[info-diff]
FAILED tests/test_program_push_scan.py::test_r087_a_real_binary_a_merge_writes_is_counted_and_never_read[driver-text]
FAILED tests/test_program_push_scan.py::test_r087_a_merge_s_resolved_line_in_a_text_file_shown_as_binary_is_read[info-nodiff]
FAILED tests/test_program_push_scan.py::test_r087_a_merge_s_resolved_line_in_a_text_file_shown_as_binary_is_read[info-binary]
FAILED tests/test_program_push_scan.py::test_r087_a_merge_s_resolved_line_in_a_file_the_commit_marks_binary_is_read
FAILED tests/test_program_push_scan.py::test_r087_a_duplicate_line_a_merge_adds_against_both_parents_counts
FAILED tests/test_program_push_scan.py::test_r087_a_utf16_file_with_a_byte_order_mark_is_read_as_text[\xff\xfe-utf-16-le]
FAILED tests/test_program_push_scan.py::test_r087_a_utf16_file_with_a_byte_order_mark_is_read_as_text[\xfe\xff-utf-16-be]
FAILED tests/test_program_push_scan.py::test_r087_a_changed_utf16_file_reports_only_its_new_lines
FAILED tests/test_program_push_scan.py::test_r087_git_s_content_rule_decides_at_its_8000th_byte[7999-True]
FAILED tests/test_program_push_scan.py::test_r087_a_sha256_repository_is_read_with_its_own_ids
FAILED tests/test_program_push_scan.py::test_r087_no_attribute_decides_and_ids_are_full
```

No precondition assertion failed (each failure is the scan's output). The 11 that passed hold what stands: round 4's two marks_binary instances, and round-5 cases round 4's code already met (the three `a_text_file_a_local_setting_shows_as_binary_is_read` instances, both `a_duplicate_added_line_counts_however_git_shows_the_file` instances, `a_utf16_file_rewritten_as_utf8_is_read_never_refused`, `git_s_content_rule_decides_at_its_8000th_byte[8000-False]`, `entries_without_content_to_read_never_end_the_scan` and `a_type_change_reads_the_new_entry`). They must keep passing once `--text` is removed and K3 matches sections to records. Every round-1 to round-4 case passed in round 4's own run (`run/agent/TASK-067-r4-own.out`):

```
408 passed, 20 skipped in 162.81s (0:02:42)
```

All must pass after your change.

**The code as it stands** (round 4's tree, line numbers verified):
- `git(sub, args)` (50-66) is the one `subprocess.run`; its argv (51) is `["git", "--no-pager", "--no-replace-objects", "-c", "color.ui=never", "-c", "log.showSignature=false", "-c", "log.showRoot=true", "-c", "diff.suppressBlankEmpty=false", sub] + list(args)`, run with `capture_output=True, timeout=bridge_env.GIT_TIMEOUT, creationflags=bridge_env.NO_WINDOW` and no `input` or `stdin` argument, so a child that reads stdin reads the program's inherited stdin. It has no place for a per-call global option today. It returns `(returncode, stdout bytes)`.
- `git_text` (69-71) decodes with `out.decode("utf-8", errors="replace")`; `git_need` (74-78) raises `ScanError("git %s failed (exit %d)" % (sub, code))` on a non-zero exit. The patch is read through `git_need` today; after K1 it is read through the runner directly (Scope).
- `unquote_git` (326-363) undoes git's quoting into bytes and ends with `return raw.decode("utf-8", errors="replace")` (363); `_path_from_rest` (391-401) uses it for `+++`, `rename to` and `diff --cc` paths.
- `_patch_lines` (373-379) splits on LF only and drops one trailing CR from each line.
- `added_lines(text)` (458-540) returns `(found, named)`: `found` is `(new path, line number in the new file, text)` per added line, read only from hunks, and `named` every new path the patch names (from `diff --cc `, `diff --combined `, `rename to ` and `+++ ` lines). It ignores `diff --git` header lines beyond ending a hunk, `index` lines and `Binary files ... differ` lines. A section without a `+++` line (a file git shows as `Binary files a/<old> and b/<new> differ`, a pure rename, a mode change) gives its path only in its `diff --git a/<old> b/<new>` header (ambiguous where a path holds a space; quoted where git quotes) and, for a rename, in `rename to`.
- `_two_path_status` (543-549) and `parse_name_status(raw)` (552-574) read the `-z --name-status` list, decoding each path with `errors="replace"`, and return `(status, new path)` records.
- `scan_commit(full, names, cfg_name, cfg_email)` (620-673): the short hash (621); `cat-file -p` (622); the name-status call (626-632), `git("show", ["-z", "--name-status", "-M", "--format=", "--no-ext-diff", "--no-textconv", "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/", "--ignore-submodules=none", "--submodule=short", "--end-of-options", full])`, its failure raising `git show failed (exit %d)` (633-634); the patch call (635-641), `git_need("show", ["-M", "--format=", "--no-ext-diff", "--no-textconv", "--text", "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/", "--ignore-submodules=none", "--submodule=short", "--end-of-options", full])`, `--text` at line 637; `records = parse_name_status(status_raw)` (642); `found, named_paths = added_lines(patch)` (643); the message, author and committer hits (648-655); the loop over records with `position` from 1 (657-669): the placement line (659), the file-name hit (660-662), the line hits with their places (663-669); the disagreement check (670-672), `for path in named_paths: if path not in seen: raise ScanError("the patch and the file list disagree")`.
- `execute(args)` (699-728): `rev-list` (710); the loop over commits (714-718); the name notes (719-720), the hit lines (721-722), then `push-scan: FOUND - ...` (725, exit 1) or `push-scan: OK - %d commit(s)` (727, exit 0).

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. The commits' contents (D-004 marks them `UNTRUSTED`), a commit's own `.gitattributes`, `.gitmodules`, file names and blob bytes included, the repository's refs (`refs/replace/` included), attribute files outside the commit (`.git/info/attributes`, `core.attributesFile`), git's configuration values (`core.bigFileThreshold`, diff drivers), the names file, the environment and the `<base>` argument are outside input. Rounds 2 to 4's rule stands and this round extends it: no commit content, ref, attribute or user setting may make the scan read objects other than the ones a push sends, decide how a file is read, narrow what it reads, make it miss a place, misplace a hit, forge or reorder an output line, or print OK where it could not read; where the program cannot read what git wrote, or what git wrote does not match itself (an id, a record, an `index` line), it ends with exit 2, never with a pass.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: run `push-scan.py` only through the tests, on their scratch repositories under `tmp_path`. Never run it on this repository (it would read the owner's real account names). Never install anything and never copy anything under `~/.claude`.

**Host.** Windows 11, with Python as on the owner's interpreter, git as installed (the supervisor's probe ran git 2.53).

## Diagrams
Unchanged from rounds 1 to 4 (`handoff/TASK-067.md`, Diagrams): `docs/diagrams/D-002-components.md` draws `push_scan --> bridge_env` and `dump_cli -.-> push_scan`; `docs/diagrams/D-004-context-dfd.md` draws the flows into `p_push_scan` and the one flow out:

```mermaid
p_push_scan -->|"hits to the terminal only: commit, place, line number, never the matched text; nothing leaves the computer (R-087)"| p_supervisor
```

`push-scan.py` imports `bridge_env` and no other bridge program (`difflib` is the standard library), writes nothing, and reaches nothing beyond read-only git. If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
1. **K1. The patch read.** The patch call is `git --attr-source=<E> -c core.attributesFile= show --cc --full-index ...` with the options it has now except `--text`, which is removed. `<E>` is the empty tree's id, computed once per run by `git hash-object -t tree --stdin` given empty input (never the inherited stdin), so a SHA-256 repository gets its own; it is passed through the runner as a global option before the subcommand, beside the runner's own. A git that refuses `--attr-source` (older than 2.40) fails the call: exit 2 through `ScanError`, never a pass. `--ignore-submodules=none` and `--submodule=short` stay written out in both `git show` calls.
2. **K2. The file list.** The name-status call is replaced by `show -z --raw --no-abbrev -M --format= ...` under the same global options (`--attr-source=<E>`, `-c core.attributesFile=`) and the diff options of the patch call that apply to it (`--no-ext-diff --no-textconv --no-color --no-relative --ignore-submodules=none --submodule=short --end-of-options <commit>`). Both `git show` calls also carry `-c core.quotePath=true` as a per-call global option, so git quotes every non-ASCII byte of a path in the patch and the user's `core.quotePath=false` cannot hand the patch reader raw bytes. Its parser reads each record exactly: an ordinary record is `:<mode> <mode> <id> <id> <status>`, then NUL, then the path (two paths, NUL-separated, for R and C statuses); a merge record has one colon per parent and as many modes and ids as parents plus one (the result's last), then the combined status letters (one per parent), then NUL and the path. The number of colons equals the commit's number of parents as `cat-file -p` gives them (a root commit counts as one, its preimage all zero). The status letters allowed: for an ordinary record `A`, `D`, `M`, `T`, and `R` or `C` followed by one to three digits; for a merge record one letter per parent, each one of `A`, `D`, `M`, `T`, `R`, `C`. The parser checks the colons, the count of modes and ids, each mode as six octal digits, each id as exactly the repository's hash length in lower-case hex (`git rev-parse --show-object-format` once per run: `sha1` is 40, `sha256` is 64; any other answer is exit 2), the status letters, the NUL framing, and that no path is listed twice in one commit; any of them wrong raises `ScanError` (exit 2). Paths are kept losslessly (bytes, or text decoded with `surrogateescape`), never decoded with replacement, for every comparison and lookup, the patch's paths included where they are compared with the list's; only printing goes through `quote_path` as now. The file-name hits and the `file #k` positions keep their round-1 to round-4 meaning (the position in this list; a hit in an added or renamed name as now; copy statuses stay as they are, a recorded lead).
3. **K3. Sections matched with records.** Every patch section is matched to its record by path, never by position (`--cc` drops sections and `diff.orderFile` reorders them). A section's path is read from its `+++ b/` line, its `rename to` line or its `diff --cc` header where it has one; otherwise (a `Binary files` section, a deletion with `+++ /dev/null`, a mode change) from its `diff --git a/<X> b/<Y>` header, unquoted where git quotes it, and where it is unquoted and holds a space, split where the two halves after `a/` and `b/` are equal, as git itself does; a header that cannot be split so raises `ScanError`. A type change (status `T`) is one record and two sections for its path: a deletion whose `index` line is `<pre>..<all zeros>` and which holds no added line, and an addition whose `index` line is `<all zeros>..<result>`, read by its class (K4, K5); both are matched to the one record, neither overwrites the other, and neither is a disagreement. A section that shows hunks or a `Binary files` line carries an `index` line whose ids (full length, by `--full-index`) equal the record's: for an ordinary commit `<pre>..<result>`, for a merge `<parent1>,<parent2>[,...]..<result>` in parent order; a root commit has one all-zero preimage. A missing, short or disagreeing id raises `ScanError`. A deleted file (an all-zero result id) holds no added line, else `ScanError`, and is not classified. A section with neither hunks nor a `Binary files` line (a pure rename or a mode change) needs no `index` line. The existing check that every patch path is a listed path (670-672) stays.
4. **K4. Classification.** Every record whose result is neither deleted nor a submodule (result mode `160000`, whose `Subproject commit` lines are read as now) is classified by its result blob's bytes, read with `git cat-file blob <id>` through the runner: UTF-16 where the bytes begin with `FF FE` (little-endian) or `FE FF` (big-endian) and the rest decodes strictly in that byte order; else binary where a NUL byte stands in the first 8000 bytes (`data[:8000]`); else text. A failed read raises `ScanError`. git's own size threshold plays no part (reproduce only the NUL rule).
5. **K5. Reading by class, never by how git shows the section.**
   - Text, and its section shows hunks: its added lines are read from the hunks exactly as now (`added_lines` and its numbering).
   - Text whose section shows no hunk (git showed `Binary files ... differ`, or listed no section), and UTF-16 however git shows it, each only where its result id differs from every preimage id (a pure rename or a mode change reads nothing): read by line diffs. The result's lines and each preimage's lines are split on LF only (never `str.splitlines`); one trailing CR is treated exactly as `_patch_lines` (373-379) treats it, so a line reads the same by either route. Each blob is decoded by its own class: a UTF-16 blob strictly, after its byte-order mark; a text blob as the patch lines are (UTF-8 with replacement); a preimage that is binary, absent (an all-zero id) or a submodule contributes an empty list and is not read for the diff (so it never meets the size bound below). For each preimage, `difflib.SequenceMatcher(None, preimage_lines, result_lines, autojunk=False).get_opcodes()` gives the result positions in its `insert` and `replace` blocks; a result line counts as added where it is added against every preimage (the intersection of the position sets), so a duplicate added line counts once per added copy. Each counted line is scanned as an added line, placed by its 1-based line number in the result, under the file's place as now (its printed path, or `#k` where its real or printed name holds a hit).
   - A text or UTF-16 result or preimage blob larger than 1 MiB (1024 * 1024 bytes) that a line diff needs raises `ScanError("a file too large to compare")`, the one new reason; never a pass. The bound is on size because `SequenceMatcher` has no time limit of its own and can take quadratic time; 1 MiB keeps an ordinary file quick, and a file git shows as binary while being text is rare outside UTF-16 files.
   - Binary: its hunks, if git forced any (a local `diff` attribute or a driver's `binary = false`), are never read. It is counted.
   - The `Binary files ... differ` wording decides nothing: it is only recognised as a section body line so that the parser accepts it.
6. **K6. The note.** Where any binary result was counted in the commit range, the program prints once, after the HIT lines and immediately before the OK or FOUND line, `push-scan: note - <n> binary file(s) not read`, `<n>` the total of binary results over every commit of the range (a file that two commits each change to a binary counts twice), naming no file. Nothing else of the output changes.
7. **K7. Everything of rounds 1 to 4 that K1 to K6 do not change stays:** H1 (`--no-replace-objects` in the runner), G1-G7, F1-F10, R1-R12, the owner's decision of 2026-11-18, `quote_path`, the short hash, the hit format, the exits, the notes, the disagreement check. The only new printed reason is K5's.
8. **K8. No change to the command reference.** The module docstring and the parser's description and help stay byte-identical; `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` stay out of Scope and unchanged.
9. **K9. The accepted limits** (Out of scope) are not handled otherwise.

## Acceptance criteria
- [ ] The Done section's pytest commands pass whole: `tests/test_program_push_scan.py` gives no failure (the 17 known failures and the 11 round-5 and round-4 cases that passed before included), and `tests/test_dump_cli.py` and `tests/test_allowlist.py` give no failure.
- [ ] K1 to K9 hold as written; every requirement of rounds 1 to 4 (R1-R12, F1-F10, G1-G7, H1) still holds, the owner's decision of 2026-11-18 included.
- [ ] The source holds no `--text`; both `git show` calls carry `--attr-source=<E>` and `-c core.attributesFile=` as global options before the subcommand, and `--ignore-submodules=none` and `--submodule=short`; the patch call carries `--cc` and `--full-index`; the file list carries `-z --raw --no-abbrev -M`; the runner still carries `--no-replace-objects`; `hash-object --stdin` is given empty input.
- [ ] Every malformed raw record, bad id, missing or disagreeing `index` id, added line in a deleted file, failed blob read and oversized line diff ends with exit 2 and a reason from the closed list (K5's being `a file too large to compare`), never a pass and never a traceback.
- [ ] Done's `git diff` of `push-scan.py` shows changes only in the places the Scope's limits name.
- [ ] No output line holds a matched text, a name, a line, a path whose real or printed form holds a hit, a binary file's name, or a raw control, separator or format character; every line of the output begins with `push-scan: ` (R9, F9, G5, G6, K6).
- [ ] Done's grep over `bridge/cursor-bridge/push-scan.py` prints nothing, and its ASCII check prints `ascii ok` (R11).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `bridge/cursor-bridge/settings.bridge.json` is unchanged. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-087 (the clause this brief serves) is fully met: no stand-in, placeholder or "later" text in the program. The tests naming R-087 are the supervisor's.
- [ ] No new dependency (standard library only), option, configuration key or environment variable, and no CANNOT SCAN reason but `a file too large to compare`. No new Semgrep high finding. No exception escapes as a traceback, and none is turned into a pass (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only; `difflib` is in it).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit any test file or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a git behaviour that surprised you included): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (the program, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- **Windowless launches.** Every process the program starts is created with `creationflags=bridge_env.NO_WINDOW`, with `timeout=bridge_env.GIT_TIMEOUT`, through `subprocess.run`, never `Popen`, never through a shell. Capturing output does not prevent the window. Every new git call (`hash-object`, `rev-parse --show-object-format`, `cat-file blob`) goes through the runner, which already does this.
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section and the mutation self-check name, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- **Never run `push-scan.py` on this repository** or on any folder but the tests' scratch repositories (Context, "Development data").
- Never run the product, a migration, a seed or a test against the owner's live data. Never install anything.
- The owner's value (Context, the decision of 2026-11-18, pinned by the two `test_r087_owner_2026_11_18_` tests) is fixed: do not change it or those tests; report it if the work seems to need a change (rule 52).
- Do not refactor code outside the places the Scope's limits name, even if it looks wrong. The items under "Not in this round" and the disagreement check stay as they are.
- Follow existing conventions of `push-scan.py`: ASCII program text, ASCII output apart from path names, results returned as values, `ScanError(reason)` for every exit 2, `main()` returning the exit code. Numbers read from git's output (modes, ids, hunk counts) are checked by their exact shape and parsed with `int(..., 8)` or `int(..., 10)`, never by slicing a guess.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `replace`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. The program itself runs only read-only git commands.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the scan after your run, and every mutant but the one it marks as expected to survive must fail a test. Before you finish, apply each of these to `push-scan.py` by hand, one at a time, run `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` from the Workspace root, and revert to the exact bytes from before the mutant. List each in the report by its label and text, with the test id that caught it, or `not caught`:
  - S1 `--attr-source` dropped from the patch call;
  - S2 `-c core.attributesFile=` dropped;
  - S3 the classification skipped (every result treated as text);
  - S4 the NUL window changed from `data[:8000]` to `data[:7999]`;
  - S5 the UTF-16 branch removed;
  - S6 the line diff's intersection replaced by a union (added against any preimage);
  - S7 the line diff replaced by a set membership test (a result line counts where no preimage holds it);
  - S8 the `index` id equality check removed;
  - S9 the id length check removed;
  - S10 the binary count not printed;
  - S11 `--full-index` dropped;
  - S12 the deleted-file added-line check removed;
  - S13 a type change's addition section not read (its deletion section kept as the record's only section);
  - S14 `-c core.quotePath=true` dropped from both `git show` calls.

  Re-run Q1 (`--no-replace-objects` removed from the runner), since the runner changes; Q2 (`--text` removed) no longer applies, since K1 removes `--text`: say so in one line. Re-run an earlier mutant by its label wherever your change touched the code it changes: at least N5 (`log.showSignature` left on; the runner), P1 (`-c log.showRoot=true` removed from the runner), P4 (`-c diff.suppressBlankEmpty=false` removed from the runner), N6 (`--no-relative` dropped from both `git show` calls), P2 (`--ignore-submodules=none` removed from both `git show` calls), P3 (`--submodule=short` removed from both `git show` calls) and N3 (a combined status read with two paths: apply it to K2's parser as a merge record read as a two-path record); and M2, M9, M10, M11, N1, N2, N8, P5 if your change touched their code. For every other mutant of rounds 1 to 4 (M1-M13, N1-N9, P5, P6), say in one line that its code is unchanged; N4 (the disagreement check removed) stays expected to survive and is not re-run. You cannot add a test. A mutant no test catches is reported as `not caught`, with one line on the case that would catch it; the supervisor adds it.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: git's own options, the existing runner, `added_lines`, `_patch_lines` and `difflib`, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-067-r5-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for K1 to K8, one line each on what meets it, naming the function and its line as the file stands after your change, and, for each new exit 2, the reason it prints;
- the mutation self-check list, S1 to S12, each with the test id that caught it (or `not caught` and the case that would), the Q1 and Q2 lines, the re-run lines and the unchanged-code lines the mutation self-check asks for;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a git behaviour you expected, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. Examples:
- that `--attr-source` with the empty tree disables tree attributes for the combined diff as for an ordinary one in the git installed here;
- that `-c core.attributesFile=` set empty disables a user attributes file rather than failing or being ignored;
- that `--cc --full-index` prints full ids on a combined `index` line;
- that `--raw --no-abbrev -z` on a merge prints one record per path in combined format;
- that git prints no section for a merge's file whose result equals one parent.

One item per line: what you assumed | why | what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py --check` (expect exit 0; if it does not, stop and report it, and do not run `python tools/dump-cli.py` without `--check`)
3. `python tools/make-manifest.py`
4. `git restore bridge/cursor-bridge/VERSION`
5. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
8. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
9. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py` (expect no output and exit 1: the source holds none of the shapes R11 names. Quote the empty output and the exit code.)
10. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
11. `python -c "import difflib; print('difflib ok')"` (expect `difflib ok`: the standard library, nothing installed)
12. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json` (expect no output: the file is unchanged)
13. `git diff HEAD -- bridge/cursor-bridge/push-scan.py` (expect hunks only in the runner, `scan_commit`, `execute`, the new raw parser in place of `_two_path_status` and `parse_name_status`, the new classifier and line-diff functions, `added_lines` where K3 and K5 hook in, `unquote_git`'s last line if K2 needed it, and the `import difflib` line; quote it whole)
14. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Where a failure body would print a temporary path, replace it with `<tmp>`.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 14, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
