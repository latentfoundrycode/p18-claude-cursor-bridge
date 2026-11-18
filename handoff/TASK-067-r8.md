---
record: brief
header: 1
id: "TASK-067"
round: 8
satisfies: [R-087]
scope: ["bridge/cursor-bridge/push-scan.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-067-r8-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-067 round 8: the third resolution (R-087)

Round cause: security - both reviewers of round 7 rejected it on a regression round 7 caused (a commit's encoding header naming a multibyte or stateful codec hides a path or a name round 6 found; a non-ASCII identity loses its exemption under an ISO-8859-1 header), decided by the third resolution round of 2026-11-18, docs/CHANGES.md.

Blocking class: security - Review A's vote in the third resolution round: an ISO-2022-JP or ISO-2022-KR file line, or a message git records with no encoding header, holding a drive or /Users/ path whose first segment begins with a non-ASCII character makes round 7's scan print OK, since the encoding writes an ASCII shift (ESC or SO) before that character: untrusted commit content reaches a pass against R-087.

Round 7's findings are a regression round 7 caused; a class line never lifts a round for one, so this round builds the decision of the third resolution round (handoff/RESOLUTION-TASK-067.md, from the heading 'The third resolution', and docs/CHANGES.md's top entry), and the class line names the older finding that decision also answers. The reviewers confirm or deny the class line against round 7's code: the commit this brief was committed in.

## Objective
Build the decision in the top entry of `docs/CHANGES.md`, headed "2026-11-18 TASK-067: the encoding header withdrawn, ESC and SO begin a segment, the third resolution round (R-087)", and nothing else.

This is round 8 of TASK-067. Rounds 1 to 7 built `bridge/cursor-bridge/push-scan.py`, its allow entry and the generated files. This round changes two small places: round 7's M2 (the commit object decoded in the encoding its header records) is withdrawn, so the commit object is read exactly as in round 6 (N1), and the rule for where a path's segment begins also accepts ESC and SO (N2). Read that CHANGES entry whole, and `handoff/RESOLUTION-TASK-067.md` from the heading "# The third resolution: round 7's regression (2026-11-18)" to its end. The entry governs wherever this brief is silent; where this brief and the entry disagree, the entry wins and you report the disagreement. Rounds 1 to 6's design and round 7's M1 (a non-ASCII character that is not whitespace begins a segment) stand unchanged. Round 7's tree and the round-8 test cases are committed before this brief, and this brief is committed before your run, so the line numbers below hold when you start; re-read them before you edit.

Satisfies: R-087 - The pre-push scan is a program (C2): `push-scan.py [<base>]` reads every commit of `<base>..HEAD`, its message, author and committer lines, added lines and added file names, [...]; "a path's segment begins with a letter, a digit, `_`, `.`, `-`, ESC, SO or any other non-ASCII character that is not a space (the third resolution round of 2026-11-18); a path compiled into a binary, a text file holding a NUL in its first 8000 bytes, a non-ASCII name in text in an encoding other than UTF-8, and text whose ASCII characters are not their ASCII bytes (UTF-16 without a byte-order mark, UTF-32, EBCDIC) or that writes a non-ASCII character with other ASCII bytes (UTF-7, HZ) are accepted limits"; [...]. (Full text: its row in `docs/REQUIREMENTS.md`, line 113. This round serves that clause.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/push-scan.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-067-r8-report.md

Limits on these files:
- `bridge/cursor-bridge/push-scan.py` changes only where N1 and N2 need it:
  - `_segment_start` (91-92), its body only (N2);
  - `_decode_commit` (314-336) removed, with the blank lines that separate it, so that `split_ident` and `parse_commit` stand as in round 6 (N1);
  - inside `scan_commit` (1132-1196), the read of the commit object (1134-1137) put back to round 6's lines exactly (N1).

  Everything else stays byte-identical to round 7's tree, in particular: the module docstring (2-19) and `build_parser` (1260-1266), whose text is the command reference; the runner `git` (51-72), `git_text` (75-77), `git_need` (80-84); `_bound` (87-88); `has_path` (95-130), every line of it; `has_name` (from 133), `kinds_of` (143-149), `kinds_of_parts` (152-153); `parse_commit` (339-354); `_parent_count` (835-844); every line of `scan_commit` but 1134-1137, the disagreement check (1193-1195) included; `execute` (from 1222) and `main` (from 1269).
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`; restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are not in Scope. Do not change the module docstring or the parser's description or help, so neither file changes. Do not run `python tools/dump-cli.py` without `--check`; Done runs only its read-only `--check`.

Do not modify anything else. `bridge/cursor-bridge/settings.bridge.json` is done (round 1) and must not change. Every test file is read-only for you: read and run `tests/test_program_push_scan.py`, `tests/test_dump_cli.py` and `tests/test_allowlist.py`, edit none of them.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, the diagrams, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` included. The briefs of rounds 1 to 7 (`handoff/TASK-067.md`, `handoff/TASK-067-r2.md` to `handoff/TASK-067-r7.md`), their reports (`handoff/TASK-067-r1-report.md` to `handoff/TASK-067-r7-report.md`) and `handoff/RESOLUTION-TASK-067.md` stay as they are; the decisions of the three resolution rounds stand.
- `bridge/cursor-bridge/settings.bridge.json`, `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`.
- Every test file. You add no test file and edit none; a gap is reported (Constraints, mutation self-check).
- `bridge/agents/secret-sentinel.md`, `bridge/commands/supervisor.md`, the loop's text under `bridge/cursor-bridge/workflow/` (TASK-082).
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them as Done says, and edit neither).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.
- The disagreement check (round 2's F4, `scan_commit` lines 1193-1195 in round 7's tree) stays exactly as written; the supervisor's mutants file marks its removal as expected to survive. Do not remove, weaken or "simplify" it.
- **Leads, not in this round** (docs/HARDENING.md, TASK-067; the CHANGES entry's item 4, verbatim): "legacy two-byte pairs decoding as U+00A0 or U+0085 at a segment's start; a drive letter or a name directly after a CJK or kana character is bounded (`_bound`, `has_name`)." Every lead rounds 5 to 7 named stays a lead, including the over-read of unique lines, the unmarked file with a BOM-less UTF-16 path appended, and batched classification reads.
- **Accepted limits, not to be handled** (R-087, DESIGN C2; the CHANGES entry's item 3, verbatim, replacing round 7's): "a non-ASCII name in text in an encoding other than UTF-8 is not matched, whatever a header records; a path is found in any encoding that stores ASCII as ASCII; text whose ASCII characters are not their ASCII bytes (UTF-16 without a byte-order mark, UTF-32, EBCDIC) and text that writes a non-ASCII character with ASCII bytes other than ESC and SO (UTF-7, whose backslash is `+AFw-`, and HZ) are not decoded." Round 6's accepted limits (`handoff/TASK-067-r6.md`, Out of scope, L6) stand.

## Context
**Rounds 1 to 7 govern everything this brief does not change:** `handoff/TASK-067.md` to `handoff/TASK-067-r7.md`. Their Context sections (the design `docs/DESIGN.md` C2, the privacy paragraph, the import pattern, the trust boundaries, development data, host) and their Constraints hold for this round unchanged, except where round 7's M2 is withdrawn. In particular:
- **The owner's decision of 2026-11-18 (rule 52, the owner's value):** the names of the repository's configured git identity are public, and the author and committer lines that carry the configured identity are no finding. The tests `test_r087_owner_2026_11_18_the_configured_identity_is_no_finding_anywhere` and `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped` pin it, and `test_r087_a_non_ascii_identity_stays_exempt_under_another_encoding_header` pins it under an encoding header. Do not change this behaviour or those tests; if the work seems to need a change, stop and report it.
- **R11, the source scans clean:** the program's own source holds no literal of the shapes the scan reads as a path (a drive letter with a colon and a slash or backslash, `/Users/`, `/home/`, `AppData`, a URL literal), and the source is ASCII only. ESC (U+001B) and SO (U+000E) are written in the source as Python escape sequences, never as the raw control characters. Done steps 8 and 9 verify it.
- **The printed reasons are a closed list** (`handoff/TASK-067-r6.md`, Context): round 1's R9 and round 2's three. This round adds no reason, no output line and no note. A failed `cat-file -p` still raises `ScanError("git cat-file failed (exit %d)" % code)`.

**The decision, and why** (`docs/CHANGES.md`, the top entry, "Reasoning"). Every way of honouring the commit's `encoding` header lets the commit choose its reader; round 7's M2 opened 85 codecs, and both reviewers found a header (ISO-2022-JP, Shift_JIS, Big5, `unicode_escape`) that hides a path or a name round 6 found, and an ISO-8859-1 header that costs a non-ASCII identity its exemption (git writes the author and committer lines in UTF-8). So the commit object is read as UTF-8 with replacement, as in rounds 1 to 6, and the identity exemption is decided on that reading. The ISO-2022 encodings write an ASCII shift (ESC, or SO) before a segment's non-ASCII first character, which round 7's widened rule missed; making ESC and SO begin a segment closes that family in messages and files alike, with no codec. ASCII punctuation and the space still begin no segment.

**The code as it stands** (round 7's tree at HEAD, line numbers verified):
- `git(sub, args, options=None, feed=None)` (51-72) returns `(returncode, stdout bytes)`; `git_text(sub, args)` (75-77) is `code, out = git(sub, args)` then `return code, out.decode("utf-8", errors="replace")`.
- `_bound(ch)` (87-88): `return bool(ch) and (ch.isalpha() or ch.isdigit())`.
- `_segment_start(ch)` (91-92): `return ch.isalpha() or ch.isdigit() or ch in "_.-" or (not ch.isascii() and not ch.isspace())`. It is called by `has_path` (95-130) at 106 (after a drive letter, a colon and its slashes or backslashes) and at 116 (after `/Users/` or `/home/`).
- `_decode_commit(raw)` (314-336): round 7's M2, which reads the `encoding` header line and decodes the object in it.
- `parse_commit(text)` (339-354) and `_parent_count(text)` (835-844) read the decoded text; unchanged.
- `scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len, work)` (1132-1196) reads the object at 1134-1137 as `code, commit_raw = git("cat-file", ["-p", "--end-of-options", full])`, the exit check (1135-1136), and `commit_text = _decode_commit(commit_raw)` (1137); then `parse_commit(commit_text)` (1138) and later `_parent_count(commit_text)` (1165).
- **Round 6's form**, which N1 restores (the commit `f4f4e11`, `scan_commit` lines 1109-1112; see it with `git diff f4f4e11 -- bridge/cursor-bridge/push-scan.py`): `code, commit_text = git_text("cat-file", ["-p", "--end-of-options", full])`, then `if code != 0:` and `raise ScanError("git cat-file failed (exit %d)" % code)`, then `author, committer, message = parse_commit(commit_text)`.

**The supervisor's cases.** `tests/test_program_push_scan.py`, its last three sections; read them whole, they fix the expected outputs:
- `# ---...--- round 7: text that is not UTF-8 (Review B, round 4)` (1099-1178), 14 cases: `test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found` (4 instances), `test_r087_a_message_whose_encoding_python_does_not_know_is_read_as_utf8`, `test_r087_a_path_in_a_file_written_in_another_encoding_is_found` (4), `test_r087_ascii_punctuation_after_a_drive_still_begins_no_segment` (3), and the two guard cases `test_r087_a_message_header_naming_an_encoding_that_changes_ascii_is_read_as_utf8` (1161) and `test_r087_a_non_ascii_name_in_an_ordinary_utf8_message_is_found` (1170). M2's own case (a non-ASCII name in an ISO-8859-1 message) is retired by the decision and no longer in the file.
- `# ---...--- the third resolution: a header never hides a hit` (1180-1217), 7 cases: `test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds` (5 instances: `iso2022jp-users`, `iso2022jp-home`, `shiftjis-drive`, `big5-drive`, `unicode-escape-drive`), `test_r087_an_encoding_header_never_hides_a_name_the_utf8_reading_finds` and `test_r087_a_non_ascii_identity_stays_exempt_under_another_encoding_header`. Each expects exactly one `HIT <h> message path` or `HIT <h> message name` and exit 1, except the identity case, which expects exit 0, no HIT line and `push-scan: OK - 1 commit(s)`.
- `# ---...--- the third resolution: ESC and SO begin a segment` (1220 to the end), 4 cases: `test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found` (`jp-message-with-header`, `jp-message-without-header`, `jp-file-line`, `kr-file-line`). Each expects exactly one HIT (`message` or `line jp.txt:2`, kind `path`) and exit 1.

The file holds 114 test cases, parametrized instances included (89 before the round-7 section, 14, 7 and 4).

**Known failures before your change** (round 7's tree, this brief's commit). The third resolution's section, all 7 of its cases (`run/agent/TASK-067-r8-known-r7.out`; its selection also ran the two guard cases and round 6's two byte-order-mark cases, which passed):

```
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[iso2022jp-users]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[iso2022jp-home]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[shiftjis-drive]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[big5-drive]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[unicode-escape-drive]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_name_the_utf8_reading_finds
FAILED tests/test_program_push_scan.py::test_r087_a_non_ascii_identity_stays_exempt_under_another_encoding_header
7 failed, 4 passed, 100 deselected (that run was on the test file before M2's case was retired and the ESC and SO section added) in 9.41s
```

The ESC and SO section, 3 of its 4 cases (`run/agent/TASK-067-r8b-known.out`):

```
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[jp-message-without-header]
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[jp-file-line]
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[kr-file-line]
3 failed, 1 passed, 110 deselected in 4.34s
```

`jp-message-with-header` passes on round 7's tree only because M2 decodes it; after N1 it must pass through N2. Every other case of the file (104 of the 114) passes on round 7's tree and must keep passing: all 114 cases of `tests/test_program_push_scan.py` pass after your change. Quote pytest's own count line for it; never restate a count in prose.

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. The commits' contents (D-004 marks them `UNTRUSTED`), the commit object's header (its `encoding` line included), blob bytes, the repository's refs, git's configuration values (`i18n.commitEncoding` included), the names file, the environment and the `<base>` argument are outside input. Rounds 2 to 7's rule stands: no commit content or user setting may make the scan miss a place, misplace a hit, forge an output line, or print OK where it could not read. This round adds: no `encoding` header changes how a commit is read (N1), and an ISO-2022 shift (ESC or SO) before a segment's first character begins the segment (N2).

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: run `push-scan.py` only through the tests, on their scratch repositories under `tmp_path`. Never run it on this repository (it would read the owner's real account names). Never install anything and never copy anything under `~/.claude`.

**Host.** Windows 11, with Python as on the owner's interpreter, git as installed (the supervisor's probe ran git 2.53).

## Diagrams
Unchanged from rounds 1 to 7 (`handoff/TASK-067.md`, Diagrams): `docs/diagrams/D-002-components.md` draws `push_scan --> bridge_env` and `dump_cli -.-> push_scan`; `docs/diagrams/D-004-context-dfd.md` draws the flows into `p_push_scan` and the one flow out:

```mermaid
p_push_scan -->|"hits to the terminal only: commit, place, line number, never the matched text; nothing leaves the computer (R-087)"| p_supervisor
```

`push-scan.py` imports `bridge_env` and no other bridge program, writes nothing, and reaches nothing beyond read-only git. If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
1. **N1. M2 withdrawn.** `_decode_commit` (314-336) is removed, and `scan_commit`'s read of the commit object (1134-1137) goes back to round 6's form exactly: `code, commit_text = git_text("cat-file", ["-p", "--end-of-options", full])`, the same `ScanError` on a non-zero exit, `parse_commit(commit_text)` as before (round 6's lines are `f4f4e11:bridge/cursor-bridge/push-scan.py`, 1109-1112). No `encoding` header is read anywhere; the identity exemption is decided on the UTF-8 reading, as in round 6.
2. **N2. ESC and SO begin a segment.** `_segment_start(ch)` (91-92) also returns true for ESC (U+001B) and SO (U+000E), written in the source as Python escape sequences (the program stays ASCII, R11). Round 7's non-ASCII clause stays. No other ASCII character is added; `_bound`, `has_path` and every other line stay.
3. **N3. Nothing else changes:** no new output line, reason or note; the module docstring and `build_parser` unchanged, so `python tools/dump-cli.py --check` stays green without regenerating the command reference. Everything of rounds 1 to 6 (R1-R12, F1-F10, G1-G7, H1, K1-K9 as round 6 changed them, L1-L7), round 7's M1, the owner's decision of 2026-11-18, the disagreement check, the hit format and the exits stay.
4. **N4. The accepted limits and the leads** (Out of scope) are not handled otherwise.

## Acceptance criteria
- [ ] The Done section's pytest command passes whole: `tests/test_program_push_scan.py` gives no failure (all 114 cases: the 10 known failures and the 104 that passed before), and `tests/test_dump_cli.py` and `tests/test_allowlist.py` give no failure.
- [ ] N1 to N4 hold as written; every requirement of rounds 1 to 6 and round 7's M1 still hold, the owner's decision of 2026-11-18 included.
- [ ] Done's `git diff f4f4e11 -- bridge/cursor-bridge/push-scan.py` shows one hunk, in `_segment_start`: against round 6, nothing else differs. Done's `git diff HEAD -- bridge/cursor-bridge/push-scan.py` shows changes only in the places the Scope's limits name.
- [ ] Every exit 2 prints a reason from the closed list of Context; no new reason, output line or note; every line of the output begins with `push-scan: ` and no output line holds a matched text or a name.
- [ ] Done's grep over `bridge/cursor-bridge/push-scan.py` prints nothing, and its ASCII check prints `ascii ok` (R11).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `bridge/cursor-bridge/settings.bridge.json` is unchanged. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-087 (the clause this brief serves) is fully met: no stand-in, placeholder or "later" text in the program. The tests naming R-087 are the supervisor's.
- [ ] No new dependency (standard library only), import, option, configuration key or environment variable. No new Semgrep high finding. No exception escapes as a traceback, and none is turned into a pass (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit any test file or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a git or codec behaviour that surprised you included): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (the program, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- **Windowless launches, bounded by a timeout.** Every process the program starts is created with `creationflags=bridge_env.NO_WINDOW`, with `timeout=bridge_env.GIT_TIMEOUT`, through `subprocess.run`, never `Popen`, never through a shell. Every git call goes through the runner `git` (51-72), which already does this; this round adds no git call (N1 changes the one `cat-file -p` call back to `git_text`, which calls the runner).
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section and the mutation self-check name, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run. One run of `tests/test_program_push_scan.py` takes minutes; wait for it in the foreground.
- **Never run `push-scan.py` on this repository** or on any folder but the tests' scratch repositories (Context, "Development data").
- Never run the product, a migration, a seed or a test against the owner's live data. Never install anything.
- The owner's value (Context, the decision of 2026-11-18, pinned by the two `test_r087_owner_2026_11_18_` tests and the identity case) is fixed: do not change it or those tests; report it if the work seems to need a change (rule 52).
- Do not refactor code outside the places the Scope's limits name, even if it looks wrong. The leads under Out of scope and the disagreement check stay as they are.
- Follow existing conventions of `push-scan.py`: ASCII program text, results returned as values, `ScanError(reason)` for every exit 2, `main()` returning the exit code.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `replace`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. The program itself runs only read-only git commands.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the scan after your run. Before you finish, apply each of these to `push-scan.py` by hand, one at a time, run `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` from the Workspace root, and revert to the exact bytes from before the mutant. List each in the report by its label and text, with the test id that caught it, or `not caught` with one line on the case that would catch it (you cannot add a test; the supervisor adds it):
  - V1 the non-ASCII clause dropped from `_segment_start`;
  - V2 ESC dropped from `_segment_start` (SO kept);
  - V3 SO dropped from `_segment_start` (ESC kept);
  - V4 ASCII punctuation added (any non-space character begins a segment; a punctuation control must catch it);
  - V5 a header read again as round 7 did (round 7's `_decode_commit` and its call put back).

  Round 7's U3 to U5 changed M2's code, which this round removes: say so in one line. For every other mutant of rounds 1 to 7, say in one line that its code is unchanged, unless your change touched the code it changes; then re-run it and list it as above.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: the existing `git_text`, `parse_commit`, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-067-r8-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for N1 to N3, one line each on what meets it, naming the function and its lines as the file stands after your change;
- a summary of step 12's `git diff f4f4e11` showing that against round 6 only `_segment_start` differs;
- the mutation self-check list, V1 to V5, each with the test id that caught it (or `not caught` and the case that would), and the one-line notes for the earlier rounds' mutants;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a git behaviour you expected, an ambiguous requirement you resolved one way, a codec or platform behaviour you expected, a value you chose. Examples:
- which byte Python's `iso2022_jp` and `iso2022_kr` encoders write directly after the separator in the tests' paths (a designation beginning with ESC, or SO), which decides whether V2 and V3 are each caught;
- that git writes the author and committer lines in UTF-8 whatever `i18n.commitEncoding` says, so the identity exemption holds on the UTF-8 reading;
- that no ASCII-compatible encoding outside the accepted limits writes an ASCII control character other than ESC or SO before a segment's first non-ASCII character.

One item per line: what you assumed | why it matters | the check that would settle it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py --check` (expect exit 0; if it does not, stop and report it, and do not run `python tools/dump-cli.py` without `--check`)
3. `python tools/make-manifest.py`
4. `git restore bridge/cursor-bridge/VERSION`
5. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
8. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py` (expect no output and exit 1: the source holds none of the shapes R11 names. Quote the empty output and the exit code.)
9. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json` (expect no output: the file is unchanged)
12. `git diff f4f4e11 -- bridge/cursor-bridge/push-scan.py` (expect one hunk, in `_segment_start`; quote it whole)
13. `git diff HEAD -- bridge/cursor-bridge/push-scan.py` (expect hunks only in `_segment_start`, the removed `_decode_commit`, and `scan_commit`'s read of the commit object; quote it whole)
14. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Where a failure body would print a temporary path, replace it with `<tmp>`.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 14, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
