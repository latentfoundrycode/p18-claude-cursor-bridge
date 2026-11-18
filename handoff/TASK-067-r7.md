---
record: brief
header: 1
id: "TASK-067"
round: 7
satisfies: [R-087]
scope: ["bridge/cursor-bridge/push-scan.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-067-r7-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-067 round 7: text that is not UTF-8 (R-087)

Round cause: security - Review B rejected the pull request's round on round 6's tree: a commit whose message git records as ISO-8859-1 (i18n.commitEncoding) and holds a drive path whose first segment begins with a non-ASCII letter passes, because the commit object is decoded as UTF-8 with replacement and the replacement character begins no path segment; the supervisor's probe found the same pass in an ISO-8859-1 text file's added line.

Blocking class: security - Review B, the pull request's round 4: with i18n.commitEncoding=ISO-8859-1, an ordinary git commit -F whose message holds a drive path beginning with a non-ASCII letter makes round 6's scan print OK: untrusted commit content and the user's git configuration reach a pass against R-087.

The finding is older than round 6 (the segment rule and the message's decoding stand since round 1), so it is no regression and its class line lifts this round. The reviewers confirm or deny the class line against round 6's code: the commit this brief was committed in.

## Objective
Build the decision in the top entry of `docs/CHANGES.md`, and nothing else.

This is round 7 of TASK-067. Rounds 1 to 6 built `bridge/cursor-bridge/push-scan.py`, its allow entry and the generated files. This round changes two small places: the rule for where a path's segment begins (M1) and how the commit object is decoded (M2). Read the top entry of `docs/CHANGES.md`, headed "2026-11-18 TASK-067: a byte no decoding reads begins a path's segment, a message read in the encoding git records (R-087)", whole. It governs wherever this brief is silent; where this brief and that entry disagree, the entry wins and you report the disagreement. Rounds 1 to 6's design stands unchanged: the classification, the two views of a marked file, the line diff, its trimming and bounds, the raw records, the runner's options. Round 6's tree and the round-7 test cases are committed before this brief, and this brief is committed before your run, so the line numbers below hold when you start; re-read them before you edit.

Satisfies: R-087 - The pre-push scan is a program (C2): `push-scan.py [<base>]` reads every commit of `<base>..HEAD`, its message, author and committer lines, added lines and added file names, [...]; "a path's segment begins with a letter, a digit, `_`, `.`, `-` or any other non-ASCII character that is not a space, and a commit object is read in the encoding its header records (the review round of 2026-11-18); a path compiled into a binary, a text file holding a NUL in its first 8000 bytes, UTF-16 without a byte-order mark and a non-ASCII name in text written in an encoding other than UTF-8 that git does not record are accepted limits"; [...]. (Full text: its row in `docs/REQUIREMENTS.md`, line 113. This round serves that clause.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/push-scan.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-067-r7-report.md

Limits on these files:
- `bridge/cursor-bridge/push-scan.py` changes only where M1 and M2 need it:
  - `_segment_start` (91-92), its body only (M1);
  - inside `scan_commit` (1107-1170), the read of the commit object (1109-1111: `code, commit_text = git_text("cat-file", ["-p", "--end-of-options", full])` and its exit check) (M2);
  - at most one new helper function for M2's decoding, beside `parse_commit` (314) or `scan_commit`.

  Everything else stays byte-identical to round 6's tree, in particular: the module docstring (2-19) and `build_parser` (1234-1240), whose text is the command reference; the runner `git` (51-72), `git_text` (75-77, still used by other callers), `git_need` (80-84); `_bound` (87-88); `has_path` (95-130), every line of it; `has_name`, `kinds_of` (143-149), `kinds_of_parts` (152-153); `parse_commit` (314-329); `_parent_count` (810-819); every line of `scan_commit` but 1109-1111, the disagreement check (1167-1169) included; `execute` (from 1196) and `main`.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`; restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are not in Scope. Do not change the module docstring or the parser's description or help, so neither file changes. Do not run `python tools/dump-cli.py` without `--check`; Done runs only its read-only `--check`.

Do not modify anything else. `bridge/cursor-bridge/settings.bridge.json` is done (round 1) and must not change. Every test file is read-only for you: read and run `tests/test_program_push_scan.py`, `tests/test_dump_cli.py` and `tests/test_allowlist.py`, edit none of them.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, the diagrams, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` included. The briefs of rounds 1 to 6 (`handoff/TASK-067.md`, `handoff/TASK-067-r2.md` to `handoff/TASK-067-r6.md`), their reports (`handoff/TASK-067-r1-report.md` to `handoff/TASK-067-r6-report.md`) and `handoff/RESOLUTION-TASK-067.md` stay as they are; the decisions of the two resolution rounds stand.
- `bridge/cursor-bridge/settings.bridge.json`, `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`.
- Every test file. You add no test file and edit none; a gap is reported (Constraints, mutation self-check).
- `bridge/agents/secret-sentinel.md`, `bridge/commands/supervisor.md`, the loop's text under `bridge/cursor-bridge/workflow/` (TASK-082).
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them as Done says, and edit neither).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.
- The disagreement check (round 2's F4, `scan_commit` lines 1167-1169) stays exactly as written; the supervisor's mutants file marks its removal as expected to survive. Do not remove, weaken or "simplify" it.
- **Leads, not in this round** (HARDENING, TASK-067): they stay leads, including the over-read of unique lines, the unmarked file with a BOM-less UTF-16 path appended, and batched classification reads. Every lead rounds 5 and 6 named stays as it is.
- **Accepted limit, not to be handled:** a non-ASCII name in text written in an encoding other than UTF-8 that git does not record (a file's lines, a message without an `encoding` header that git did not convert) is not matched; a path in it is found by M1. Round 6's accepted limits (`handoff/TASK-067-r6.md`, Out of scope, L6) stand.

## Context
**Rounds 1 to 6 govern everything this brief does not change:** `handoff/TASK-067.md` to `handoff/TASK-067-r6.md`. Their Context sections (the design `docs/DESIGN.md` C2, the privacy paragraph, the import pattern, the trust boundaries, development data, host) and their Constraints hold for this round unchanged. In particular:
- **The owner's decision of 2026-11-18 (rule 52, the owner's value):** the names of the repository's configured git identity are public, and the author and committer lines that carry the configured identity are no finding. The tests `test_r087_owner_2026_11_18_the_configured_identity_is_no_finding_anywhere` and `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped` pin it. Do not change this behaviour or those tests; if the work seems to need a change, stop and report it.
- **R11, the source scans clean:** the program's own source holds no literal of the shapes the scan reads as a path (a drive letter with a colon and a slash or backslash, `/Users/`, `/home/`, `AppData`, a URL literal), and the source is ASCII only. Done steps 8 and 9 verify it.
- **The printed reasons are a closed list** (`handoff/TASK-067-r6.md`, Context): round 1's R9 and round 2's three. This round adds no reason, no output line and no note. A failed `cat-file -p` still raises `ScanError("git cat-file failed (exit %d)" % code)`.

**The decision, and why** (`docs/CHANGES.md`, the top entry, "Reasoning"). The pass came from one rule meeting every decoding at once: whatever the scan cannot decode it replaces with a non-letter (U+FFFD under replacement, a lone surrogate under `surrogateescape`), and the segment rule asked for a letter. Widening the rule to every non-ASCII character that is not whitespace makes the decoding irrelevant to paths, with no list of encodings; ASCII punctuation and the space keep their meaning, so code that names a bare drive and the placeholder `<name>` still pass. Names cannot be matched without knowing the encoding, so the scan uses the one record git keeps (the commit's `encoding` header) and names the rest a limit. A message with no `encoding` header is converted to UTF-8 by git itself and is already found.

**The code as it stands** (round 6's tree at HEAD, line numbers verified):
- `git(sub, args, options=None, feed=None)` (51-72) returns `(returncode, stdout bytes)`; `git_text(sub, args)` (75-77) is `code, out = git(sub, args)` then `return code, out.decode("utf-8", errors="replace")`.
- `_bound(ch)` (87-88): `return bool(ch) and (ch.isalpha() or ch.isdigit())`.
- `_segment_start(ch)` (91-92): `return ch.isalpha() or ch.isdigit() or ch in "_.-"`. It is called by `has_path` (95-130) at 106 (after a drive letter, a colon and its slashes or backslashes) and at 116 (after `/Users/` or `/home/`).
- `parse_commit(text)` (314-329) splits the decoded object on LF, drops one trailing CR per line, reads `author ` and `committer ` header lines up to the first empty line, and returns `(author, committer, message)`.
- `_parent_count(text)` (810-819) counts `parent ` lines in the decoded header.
- `scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len, work)` (1107-1170) reads the object at 1109 through `git_text("cat-file", ["-p", "--end-of-options", full])`, raises on a non-zero exit (1110-1111), calls `parse_commit(commit_text)` (1112) and later `_parent_count(commit_text)` (1139). The message, author and committer hits are 1143-1150.

**The supervisor's round-7 cases.** `tests/test_program_push_scan.py`, the last section, headed `# ---------------------------------------------------------------- round 7: text that is not UTF-8 (Review B, round 4)` (line 1099 to the end); read it whole, it fixes the expected outputs. `E_FORMS` (1103-1108) holds four paths whose first segment begins with a non-ASCII letter; `_commit_with_encoding` (1111-1116) commits a message's bytes with `git -c i18n.commitEncoding=<encoding> commit -F`. The cases:
- `test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[drive-back]`, `[drive-forward]`, `[home]`, `[users]` (1120): the message written in ISO-8859-1 and recorded so. Expected exactly `HIT <h> message path`, exit 1.
- `test_r087_a_non_ascii_name_in_a_message_git_records_in_another_encoding_is_found` (1129): a searched name holding a non-ASCII letter, in a message recorded as ISO-8859-1. Expected exactly `HIT <h> message name`, exit 1, and the name nowhere in the output.
- `test_r087_a_message_whose_encoding_python_does_not_know_is_read_as_utf8` (1139): a UTF-8 message recorded under an encoding name Python does not know. Expected exactly `HIT <h> message path`, exit 1.
- `test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-back]`, `[drive-forward]`, `[home]`, `[users]` (1149): a file written in ISO-8859-1 whose line 2 is the path. Expected exactly `HIT <h> line latin.txt:2 path`, exit 1.
- `test_r087_ascii_punctuation_after_a_drive_still_begins_no_segment[backslash-quote]`, `[slash-quote]`, `[space]` (1161): a drive followed by ASCII punctuation or a space. Expected exit 0, no HIT line, `push-scan: OK - 1 commit(s)`.

The test file also gained, after round 6's reviews, `test_r087_a_file_under_a_folder_named_like_a_prefix_is_read_whatever_the_user_s_prefixes[noprefix]` and `[swapped]` (456, the prefix pins); they pass and must keep passing.

**Known failures before your change.** The supervisor's known run of the round-7 cases on round 6's code (`run/agent/TASK-067-r7-known.out`) printed `9 failed, 6 passed, 87 deselected in 10.94s`. Its FAILED lines:

```
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[drive-back]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[drive-forward]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[home]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[users]
FAILED tests/test_program_push_scan.py::test_r087_a_non_ascii_name_in_a_message_git_records_in_another_encoding_is_found
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-back]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-forward]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[home]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[users]
```

Each failure is the scan printing `push-scan: OK`. The unknown-encoding case and the three punctuation controls pass on round 6's code and must still pass. Every other case of the file passes on round 6's code (89 cases outside the round-7 section) and must still pass: all 102 cases of `tests/test_program_push_scan.py` pass after your change.

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. The commits' contents (D-004 marks them `UNTRUSTED`), the commit object's header (its `encoding` line included), blob bytes, the repository's refs, git's configuration values (`i18n.commitEncoding` included), the names file, the environment and the `<base>` argument are outside input. Rounds 2 to 6's rule stands: no commit content or user setting may make the scan miss a place, misplace a hit, forge an output line, or print OK where it could not read. This round adds: no encoding a commit's header names may hide a path or a name that a UTF-8 reading would find in ASCII (hence M2's ASCII check), and no undecodable byte may end a path's segment before it starts (M1).

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: run `push-scan.py` only through the tests, on their scratch repositories under `tmp_path`. Never run it on this repository (it would read the owner's real account names). Never install anything and never copy anything under `~/.claude`.

**Host.** Windows 11, with Python as on the owner's interpreter, git as installed (the supervisor's probe ran git 2.53).

## Diagrams
Unchanged from rounds 1 to 6 (`handoff/TASK-067.md`, Diagrams): `docs/diagrams/D-002-components.md` draws `push_scan --> bridge_env` and `dump_cli -.-> push_scan`; `docs/diagrams/D-004-context-dfd.md` draws the flows into `p_push_scan` and the one flow out:

```mermaid
p_push_scan -->|"hits to the terminal only: commit, place, line number, never the matched text; nothing leaves the computer (R-087)"| p_supervisor
```

`push-scan.py` imports `bridge_env` and no other bridge program, writes nothing, and reaches nothing beyond read-only git. If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
1. **M1. Where a segment begins.** `_segment_start(ch)` (91) returns true for a letter, a digit, `_`, `.`, `-` (as now) and also for any character that is not ASCII and not whitespace (`not ch.isascii() and not ch.isspace()`). Every caller keeps calling it as now (the drive form, `/Users/`, `/home/`): no other line of `has_path` changes, `_bound` does not change, and no ASCII punctuation is added. Effect: U+FFFD (what a replacing decode makes of an undecodable byte) and a lone surrogate (what `surrogateescape` makes of one) begin a segment, in a message, an added line, a view of a marked file and a file's name alike.
2. **M2. The commit object in the encoding git records.** The commit object (`cat-file -p`, `scan_commit` line 1109, read today through `git_text`, which decodes UTF-8 with replacement at line 77) is read as bytes through the one runner `git(...)` with the same options, and decoded so: the header is the lines before the first empty line; where one header line is `encoding <name>`, and `<name>` is an encoding Python knows (a `LookupError` means not) and it reads ASCII as ASCII (decoding the bytes of every printable ASCII character and LF in it gives the same text back), the whole object is decoded in it with `errors="replace"`; otherwise it is decoded as UTF-8 with `errors="replace"`, exactly as today. `parse_commit`, `_parent_count` and everything that reads the decoded text are unchanged. A failed `cat-file` still raises the same `ScanError`. No new import beyond Python's standard library; prefer none (`bytes.decode` raises `LookupError` itself).
3. **M3. Nothing else changes:** no new output line, reason or note; the module docstring and `build_parser` unchanged, so `python tools/dump-cli.py --check` stays green without regenerating the command reference. Everything of rounds 1 to 6 (R1-R12, F1-F10, G1-G7, H1, K1-K9 as round 6 changed them, L1-L7), the owner's decision of 2026-11-18, the disagreement check, the hit format and the exits stay.
4. **M4. The accepted limit** (Out of scope) is not handled otherwise.

## Acceptance criteria
- [ ] The Done section's pytest command passes whole: `tests/test_program_push_scan.py` gives no failure (the 9 known failures, the 4 round-7 cases that passed before and the 89 cases outside the round-7 section, all 102), and `tests/test_dump_cli.py` and `tests/test_allowlist.py` give no failure.
- [ ] M1 to M4 hold as written; every requirement of rounds 1 to 6 still holds, the owner's decision of 2026-11-18 included.
- [ ] Done's `git diff` of `push-scan.py` shows changes only in the places the Scope's limits name.
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
- **Windowless launches, bounded by a timeout.** Every process the program starts is created with `creationflags=bridge_env.NO_WINDOW`, with `timeout=bridge_env.GIT_TIMEOUT`, through `subprocess.run`, never `Popen`, never through a shell. Every git call goes through the runner `git` (51-72), which already does this; this round adds no git call (M2 changes how the one `cat-file -p` call's output is decoded, not the call).
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section and the mutation self-check name, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run. One run of `tests/test_program_push_scan.py` takes minutes; wait for it in the foreground.
- **Never run `push-scan.py` on this repository** or on any folder but the tests' scratch repositories (Context, "Development data").
- Never run the product, a migration, a seed or a test against the owner's live data. Never install anything.
- The owner's value (Context, the decision of 2026-11-18, pinned by the two `test_r087_owner_2026_11_18_` tests) is fixed: do not change it or those tests; report it if the work seems to need a change (rule 52).
- Do not refactor code outside the places the Scope's limits name, even if it looks wrong. The leads under Out of scope and the disagreement check stay as they are.
- Follow existing conventions of `push-scan.py`: ASCII program text, results returned as values, `ScanError(reason)` for every exit 2, `main()` returning the exit code.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `replace`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. The program itself runs only read-only git commands.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the scan after your run. Before you finish, apply each of these to `push-scan.py` by hand, one at a time, run `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` from the Workspace root, and revert to the exact bytes from before the mutant. List each in the report by its label and text, with the test id that caught it, or `not caught` with one line on the case that would catch it (you cannot add a test; the supervisor adds it):
  - U1 M1's non-ASCII clause dropped (`_segment_start` as in round 6);
  - U2 M1 widened to ASCII punctuation (any non-space character begins a segment; a punctuation control must catch it);
  - U3 M2's header ignored (the object always decoded as UTF-8);
  - U4 M2's ASCII check dropped (any encoding Python knows is used);
  - U5 M2's fallback to UTF-8 dropped (an encoding Python does not know is not caught, or the object is decoded in some other fixed encoding).

  For every mutant of rounds 1 to 6, say in one line that its code is unchanged, unless your change touched the code it changes; then re-run it and list it as above.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: the existing runner, `parse_commit`, `bytes.decode`, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-067-r7-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for M1 to M3, one line each on what meets it, naming the function and its lines as the file stands after your change;
- the mutation self-check list, U1 to U5, each with the test id that caught it (or `not caught` and the case that would), and the unchanged-code line for the earlier rounds' mutants;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a git behaviour you expected, an ambiguous requirement you resolved one way, a codec or platform behaviour you expected, a value you chose. Examples:
- that git writes the `encoding` header line as `encoding <name>` in ASCII bytes, and how you treated a header line whose name is not ASCII or carries a trailing CR;
- that git leaves a message without an `encoding` header in UTF-8 (converting it itself), so the UTF-8 fallback reads it as round 6 did;
- that no codec Python knows passes M2's ASCII check while hiding an ASCII path that UTF-8 would show.

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
12. `git diff HEAD -- bridge/cursor-bridge/push-scan.py` (expect hunks only in `_segment_start`, `scan_commit`'s read of the commit object, and the one new helper if you added it; quote it whole)
13. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Where a failure body would print a temporary path, replace it with `<tmp>`.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 13, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
