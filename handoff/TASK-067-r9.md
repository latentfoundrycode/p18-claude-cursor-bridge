---
record: brief
header: 1
id: "TASK-067"
round: 9
satisfies: [R-087]
scope: ["bridge/cursor-bridge/push-scan.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-067-r9-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-067 round 9: a name matched under Unicode's compatibility caseless matching (R-087)

Round cause: security - Review B, the pull request's round on round 8's tree (snapshot TASK-067-r6), rejected it on a finding as old as round 1, not a regression: a searched name holding a sharp s written SS in a commit's text, a name in fullwidth letters, and a name whose accented letter is composed on one side and decomposed on the other print OK; decided 2026-11-18, docs/CHANGES.md.

Blocking class: security - Review B, the pull request's round on round 8's tree (snapshot TASK-067-r6): a searched name holding a sharp s written SS in a commit's added line printed OK on round 8's code; the supervisor reproduced it with the round-9 cases (5 failed, 1 passed on round 8's code, run/agent/TASK-067-r9-known.out); round 9's builder is launched on the round-9 brief's commit, which holds round 8's code.

The finding is not a regression of round 8; the class line lifts this round. The reviewers confirm or deny the class line against round 8's code: the commit this brief was committed in.

## Objective
Build the decision in the top entry of `docs/CHANGES.md`, headed "2026-11-18 TASK-067: a name is matched under Unicode's compatibility caseless matching (R-087)", and nothing else.

This is round 9 of TASK-067. Rounds 1 to 8 built `bridge/cursor-bridge/push-scan.py`, its allow entry and the generated files. This round changes one small place: `has_name` (133-140) matches a searched name with `re.IGNORECASE`, the regular expression engine's simple one-to-one case folding, so a name holding a sharp s (U+00DF) written `SS` or `ss`, a name written in fullwidth letters (U+FF21 to U+FF5A), and a name whose accented letter is one code point on one side and a letter plus a combining accent (U+0301) on the other all print OK. After this round, a name is found where the text and the name are equal under Unicode's compatibility caseless matching: each side normalized to NFKC, case-folded with `str.casefold`, and normalized to NFKC again, then searched as a whole word with the same boundaries as now (P1). Read that CHANGES entry whole. The entry governs wherever this brief is silent; where this brief and the entry disagree, the entry wins and you report the disagreement. Rounds 1 to 8's design stands unchanged. Round 8's tree and the round-9 test cases are committed before this brief, and this brief is committed before your run, so the line numbers below hold when you start; re-read them before you edit.

Satisfies: R-087 - The pre-push scan is a program (C2): `push-scan.py [<base>]` reads every commit of `<base>..HEAD`, its message, author and committer lines, added lines and added file names, [...]; "a name is found where the text and the name are equal under Unicode's compatibility caseless matching (NFKC, case-folded, NFKC again), as a whole word; a path compiled into a binary, a text file holding a NUL in its first 8000 bytes, a name spelled with other characters (a look-alike letter of another script, an inserted character, a transliteration), [...] are accepted limits"; [...]. (Full text: its row in `docs/REQUIREMENTS.md`, line 113; the same clause in `docs/DESIGN.md`, the C2 bullet, line 347. This round serves that clause.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/push-scan.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-067-r9-report.md

Limits on these files:
- `bridge/cursor-bridge/push-scan.py` changes only where P1 needs it:
  - one new helper function, placed directly above `has_name`, between `has_path`'s end (130) and `has_name` (133), with the blank lines that separate functions;
  - `has_name` (133-140), its body only; its signature `def has_name(text, names):` stays.

  Everything else stays byte-identical to round 8's tree, in particular: the module docstring (2-19) and `build_parser` (1234-1240), whose text is the command reference (the docstring's "An account name is a whole word, in any letter case." stays as written); the imports (20-30), since `unicodedata` is already imported at line 26 and no import is added; the runner `git` (51-72), `git_text` (75-77), `git_need` (80-84); `_bound` (87-88); `_segment_start` (91-92); `has_path` (95-130), every line of it; `kinds_of` (143-149), `kinds_of_parts` (152-153); `read_names_file` (172-199), `deduped_names` (202-219), `public_names` (263-278), `select_names` (281-297, the four-character length check at 288 and the public-name drop at 283 and 291 included), `carries_identity` (300-303), `split_ident` (306-311), `parse_commit` (314-329); `scan_commit` (1107-1170), the disagreement check (1167-1169) included; `execute` (1196-1231) and `main` (1243-1252).
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`; restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are not in Scope. Do not change the module docstring or the parser's description or help, so neither file changes. Do not run `python tools/dump-cli.py` without `--check`; Done runs only its read-only `--check`.

Do not modify anything else. `bridge/cursor-bridge/settings.bridge.json` is done (round 1) and must not change. Every test file is read-only for you: read and run `tests/test_program_push_scan.py`, `tests/test_dump_cli.py` and `tests/test_allowlist.py`, edit none of them.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, the diagrams, `docs/CHANGES.md`, `docs/HARDENING.md`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` included. The briefs of rounds 1 to 8 (`handoff/TASK-067.md`, `handoff/TASK-067-r2.md` to `handoff/TASK-067-r8.md`), their reports (`handoff/TASK-067-r1-report.md` to `handoff/TASK-067-r8-report.md`) and `handoff/RESOLUTION-TASK-067.md` stay as they are; the decisions of the three resolution rounds stand.
- `bridge/cursor-bridge/settings.bridge.json`, `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`.
- Every test file. You add no test file and edit none; a gap is reported (Constraints, mutation self-check).
- `bridge/agents/secret-sentinel.md`, `bridge/commands/supervisor.md`, the loop's text under `bridge/cursor-bridge/workflow/` (TASK-082).
- `tools/make-manifest.py`, `tools/dump-cli.py` (you run them as Done says, and edit neither).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.
- The disagreement check (round 2's F4, `scan_commit` lines 1167-1169) stays exactly as written; the supervisor's mutants file marks its removal as expected to survive. Do not remove, weaken or "simplify" it.
- **The identity and public-name comparisons stay as they are**, even where a folded name would compare differently: `carries_identity` (exact name, email by `.lower()`), the public-name drop in `select_names` (by `.lower()`), the de-duplication in `deduped_names` (by `.lower()`), and the four-character length check on the name as read (`len(name) < 4`). The folding applies inside `has_name` only.
- **Leads, not in this round** (`docs/HARDENING.md`, the section "TASK-067: the pre-push scan as a program", and the leads every earlier CHANGES entry of TASK-067 names): every lead stays a lead, including "a drive letter or a name directly after a CJK or kana character is bounded (`_bound`, `has_name`)", legacy two-byte pairs decoding as U+00A0 or U+0085 at a segment's start, the over-read of unique lines, the unmarked file with a BOM-less UTF-16 path appended, and batched classification reads.
- **Accepted limits, not to be handled** (R-087, DESIGN C2; the CHANGES entry, verbatim): "a name spelled with other characters is not matched: a letter from another script that looks alike, a character inserted inside it, a transliteration." Every limit of rounds 1 to 8 stands, round 8's (a non-ASCII name in text in an encoding other than UTF-8; text whose ASCII characters are not their ASCII bytes; UTF-7 and HZ) included.

## Context
**Rounds 1 to 8 govern everything this brief does not change:** `handoff/TASK-067.md` to `handoff/TASK-067-r8.md`. Their Context sections (the design `docs/DESIGN.md` C2, the privacy paragraph, the import pattern, the trust boundaries, development data, host) and their Constraints hold for this round unchanged. In particular:
- **The owner's decision of 2026-11-18 (rule 52, the owner's value):** the names of the repository's configured git identity are public, and the author and committer lines that carry the configured identity are no finding. The tests `test_r087_owner_2026_11_18_the_configured_identity_is_no_finding_anywhere` and `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped` pin it, and `test_r087_a_non_ascii_identity_stays_exempt_under_another_encoding_header` pins it under an encoding header. Do not change this behaviour or those tests; if the work seems to need a change, stop and report it.
- **R11, the source scans clean:** the program's own source holds no literal of the shapes the scan reads as a path (a drive letter with a colon and a slash or backslash, `/Users/`, `/home/`, `AppData`, a URL literal), and the source is ASCII only. This round needs no non-ASCII character in the source; if you write one in a comment or a literal, it is a failure. Done steps 8 and 9 verify it.
- **The printed reasons are a closed list** (`handoff/TASK-067-r6.md`, Context): round 1's R9 and round 2's three. This round adds no reason, no output line and no note. A hit line never holds the matched text or the name, folded or not.

**The decision, and why** (`docs/CHANGES.md`, the top entry, "Decision" and "Reasoning"). The case rule was one engine's approximation of a standard that already says which spellings are the same name. Unicode's compatibility caseless matching (NFKC, `casefold`, NFKC again) covers every case pair Unicode equates (sharp s and SS, final sigma), every compatibility form (fullwidth letters, ligatures) and every composed or decomposed spelling, with one rule. What stays open is a different spelling (the accepted limit).

**The code as it stands** (round 8's tree at HEAD, line numbers verified):
- Line 26: `import unicodedata` (already imported, standard library; it is used by the path quoting at 788 and 801).
- `has_name(text, names)` (133-140):

```python
def has_name(text, names):
    for name in names:
        if not name:
            continue
        pattern = re.compile("(?<![^\\W_])" + re.escape(name) + "(?![^\\W_])", re.IGNORECASE)
        if pattern.search(text):
            return True
    return False
```

- `has_name` is called only by `kinds_of(text, names)` (143-149), which `kinds_of_parts` (152-153) and `scan_commit` (1107-1170) call for every place a hit can stand. It returns a boolean; no position or matched text leaves it.
- `names` reaches `has_name` from `select_names(ordered, public)` (281-297) through `execute` (1206): names as read from the profile folder, the login and `~/.cursor-bridge/names.txt` (`read_names_file`, 172-199, decoded as UTF-8 and stripped), not normalized.

**P1, what must be true** (the CHANGES entry's decision, as R-087 and DESIGN C2 word it): `has_name` returns true exactly where some searched name, normalized to NFKC, case-folded with `str.casefold` and normalized to NFKC again, occurs as a whole word in the text normalized the same way (`unicodedata.normalize('NFKC', unicodedata.normalize('NFKC', s).casefold())` applied to each side, through one helper). The whole-word boundaries are the existing lookbehind `(?<![^\W_])` and lookahead `(?![^\W_])`, unchanged, applied to the folded text. An empty name is still skipped. Nothing else in the program changes.

**The supervisor's cases.** `tests/test_program_push_scan.py`, its last section, `# ---...--- round 9: a name under Unicode's caseless matching` (1258 to the end); read it whole, it fixes the expected outputs:
- `test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching` (1275), 5 instances: `sharp-s-upper`, `sharp-s-lower`, `fullwidth`, `decomposed-in-text`, `decomposed-in-names-file`. Each expects exit 1, exactly one `HIT <h> line notes.md:1 name`, and neither the name nor its written form in the output.
- `test_r087_a_folded_name_inside_a_longer_word_is_still_no_hit` (1286), a guard: the folded name inside a longer word (before and after) is no hit; it expects exit 0, no HIT line and `push-scan: OK - 1 commit(s)`.

The file holds 120 test cases, parametrized instances included (114 of rounds 1 to 8 and these 6).

**Known failures before your change** (round 8's tree, this brief's commit; `run/agent/TASK-067-r9-known.out`, a run of the round-9 section only):

```
PASSED tests/test_program_push_scan.py::test_r087_a_folded_name_inside_a_longer_word_is_still_no_hit
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-lower]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[fullwidth]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-names-file]
5 failed, 1 passed, 114 deselected in 4.45s
```

Every other case of the file (115 of the 120) passes on round 8's tree and must keep passing: all 120 cases of `tests/test_program_push_scan.py` pass after your change. Round 8's report (`handoff/TASK-067-r8-report.md`) quotes Done step 5 as `455 passed, 20 skipped` and step 6 as `25 passed`; after this round, step 5 is expected to print 461 passed and 20 skipped, and step 6 25 passed. Quote pytest's own count line for each; never restate a count in prose.

**Trust boundaries and security context.** The ASVS level is 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. The commits' contents (D-004 marks them `UNTRUSTED`), the commit object's header, blob bytes, the repository's refs, git's configuration values, the names file, the environment and the `<base>` argument are outside input. Rounds 2 to 8's rule stands: no commit content or user setting may make the scan miss a place, misplace a hit, forge an output line, or print OK where it could not read. This round adds: no spelling of a searched name that Unicode's compatibility caseless matching equates with it hides it (P1).

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: run `push-scan.py` only through the tests, on their scratch repositories under `tmp_path`. Never run it on this repository (it would read the owner's real account names). Never install anything and never copy anything under `~/.claude`.

**Host.** Windows 11, with Python as on the owner's interpreter, git as installed (the supervisor's probe ran git 2.53).

## Diagrams
Unchanged from rounds 1 to 8 (`handoff/TASK-067.md`, Diagrams): `docs/diagrams/D-002-components.md` draws `push_scan --> bridge_env` and `dump_cli -.-> push_scan`; `docs/diagrams/D-004-context-dfd.md` draws the flows into `p_push_scan` and the one flow out:

```mermaid
p_push_scan -->|"hits to the terminal only: commit, place, line number, never the matched text; nothing leaves the computer (R-087)"| p_supervisor
```

`push-scan.py` imports `bridge_env` and no other bridge program, writes nothing, and reaches nothing beyond read-only git. If the task cannot be done within these diagrams, stop and report the conflict instead of deviating.

## Requirements
1. **P1. A name is matched under Unicode's compatibility caseless matching.** `has_name` compares the text and each name after one helper has turned each into `unicodedata.normalize('NFKC', unicodedata.normalize('NFKC', s).casefold())`, and searches the folded name in the folded text with the existing whole-word lookbehind and lookahead (Context, P1). `unicodedata` is the standard library's, already imported; no import is added. The source stays ASCII only.
2. **P2. Nothing else changes:** no new output line, reason or note; the module docstring and `build_parser` unchanged, so `python tools/dump-cli.py --check` stays green without regenerating the command reference; the four-character length check, the identity exemption (`carries_identity`), the public-name drop, the de-duplication, `has_path`, `_segment_start` and `_bound` untouched. Everything of rounds 1 to 8 (R1-R12, F1-F10, G1-G7, H1, K1-K9 as round 6 changed them, L1-L7, round 7's M1, round 8's N1 and N2), the owner's decision of 2026-11-18, the disagreement check, the hit format and the exits stay.
3. **P3. The accepted limits and the leads** (Out of scope) are not handled otherwise.

## Acceptance criteria
- [ ] The Done section's pytest command passes whole: `tests/test_program_push_scan.py` gives no failure (all 120 cases: the 5 known failures, the guard and the 114 that passed before), and `tests/test_dump_cli.py` and `tests/test_allowlist.py` give no failure.
- [ ] P1 to P3 hold as written; every requirement of rounds 1 to 8 still holds, the owner's decision of 2026-11-18 included.
- [ ] Done's `git diff HEAD -- bridge/cursor-bridge/push-scan.py` shows changes only between `has_path`'s end and `kinds_of`: the new helper and `has_name`'s body.
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
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a Unicode or regular-expression behaviour that surprised you included): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (the program, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output. The test names in the round-9 section are invented; do not copy them into the report either (a test id is fine).
- **Windowless launches, bounded by a timeout.** Every process the program starts is created with `creationflags=bridge_env.NO_WINDOW`, with `timeout=bridge_env.GIT_TIMEOUT`, through `subprocess.run`, never `Popen`, never through a shell. Every git call goes through the runner `git` (51-72), which already does this; this round adds no git call and no process.
- Never start a server, a watcher or a daemon. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section and the mutation self-check name, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run. One run of `tests/test_program_push_scan.py` takes about two minutes; wait for it in the foreground.
- **Never run `push-scan.py` on this repository** or on any folder but the tests' scratch repositories (Context, "Development data").
- Never run the product, a migration, a seed or a test against the owner's live data. Never install anything.
- The owner's value (Context, the decision of 2026-11-18, pinned by the two `test_r087_owner_2026_11_18_` tests and the identity case) is fixed: do not change it or those tests; report it if the work seems to need a change (rule 52).
- Do not refactor code outside the places the Scope's limits name, even if it looks wrong. The leads under Out of scope, the identity and public-name comparisons and the disagreement check stay as they are.
- Follow existing conventions of `push-scan.py`: ASCII program text, results returned as values, `ScanError(reason)` for every exit 2, `main()` returning the exit code.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `replace`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. The program itself runs only read-only git commands.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the scan after your run. Before you finish, apply each of these to `push-scan.py` by hand, one at a time, run `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` from the Workspace root, and revert to the exact bytes from before the mutant. List each in the report by its label and text, with the test id that caught it, or `not caught` with one line on the case that would catch it (you cannot add a test; the supervisor adds it):
  - W1 `str.casefold` replaced by `str.lower` in the helper;
  - W2 the inner NFKC dropped (the helper case-folds the raw string, then normalizes to NFKC);
  - W3 the outer NFKC dropped (the helper normalizes to NFKC, then case-folds, and returns that);
  - W4 the name searched as read (only the text folded);
  - W5 the text searched as read (only the name folded);
  - W6 the whole-word lookbehind and lookahead dropped from the pattern.

  For every mutant of rounds 1 to 8, say in one line that its code is unchanged, unless your change touched the code it changes (a mutant of `has_name`, such as `re.IGNORECASE` dropped or a boundary dropped); then re-run it on your code and list it as above.
- **Known failures.** Context lists the cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: the standard library's `unicodedata.normalize` and `str.casefold`, the existing pattern, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-067-r9-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for P1 and P2, one line each on what meets it, naming the function and its lines as the file stands after your change;
- a summary of step 12's `git diff HEAD` showing that only the new helper and `has_name`'s body differ from round 8;
- the mutation self-check list, W1 to W6, each with the test id that caught it (or `not caught` and the case that would), and the one-line notes for the earlier rounds' mutants;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: a Unicode or `re` behaviour you expected, an ambiguous requirement you resolved one way, a platform behaviour you expected, a value you chose. Examples:
- that one pass of NFKC, `casefold` and NFKC is enough for the five cases (that applying the helper to its own result changes nothing for them);
- that the whole-word boundaries behave on folded text as on the text as written: a combining mark after a name is not a word character in Python's `re`, so a name followed by a combining mark that NFKC does not compose still counts as a whole word;
- whether `re.IGNORECASE` stays on the pattern after folding, and what keeping or dropping it changes;
- that `str.casefold` and `unicodedata` use the interpreter's own Unicode tables, so the result depends on the interpreter's Unicode version.

One item per line: what you assumed | why it matters | the check that would settle it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py --check` (expect exit 0; if it does not, stop and report it, and do not run `python tools/dump-cli.py` without `--check`)
3. `python tools/make-manifest.py`
4. `git restore bridge/cursor-bridge/VERSION`
5. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py` (expect 461 passed and 20 skipped)
6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py` (expect 25 passed; outside Scope. A failure here is reported by test id, never fixed in those files.)
7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
8. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py` (expect no output and exit 1: the source holds none of the shapes R11 names. Quote the empty output and the exit code.)
9. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json` (expect no output: the file is unchanged)
12. `git diff HEAD -- bridge/cursor-bridge/push-scan.py` (expect hunks only between `has_path`'s end and `kinds_of`: the new helper and `has_name`'s body; quote it whole)
13. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block. Where a failure body would print a temporary path, replace it with `<tmp>`.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 13, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
