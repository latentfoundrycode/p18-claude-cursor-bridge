---
record: brief
header: 1
id: TASK-046
round: 3
satisfies: [R-057]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_header_reader.py", "tests/test_header_schemas.py", "tests/fixtures/headers/", "docs/BUILDER_NOTES.md", "handoff/TASK-046-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-046-r3: The header reader made one scan, and the check and the agreement corrected (R-057, round 3)

## Objective
Fix the following confirmed defect — repair the named cause, nothing else. The root cause: `bridge_env.py` holds five hand-written quote lexers (at 157f914 lines 1288 `_scan_block_characters`, 1340 `_split_line_parts`, 1369 `_code_outside_quotes`, 1470 `_parse_flow_list`, 1567 `_find_colon`), and the character scan keeps its own quote state across lines and disagrees with the line splitter, so a column-0 comment holding a quote, on any line but the block's first, opens a "string" in the scan that runs on over later lines, inside which a backslash skips the next character unchecked: `# "` then `c: 2 # \<U+2028>b: 3` hides key `b`, which `pyyaml` reads. Separately, the parser's list-item branch handles a first key apart from the mapping path, and `.strip()` without an argument still treats Unicode space as whitespace. Round 2's brief advised one scan; now it is required.

Evidence: at checkpoint 934d14d's tests on round 2's code (157f914) the supervisor's run prints `132 failed, 679 passed in 51.04s`. Review A and the security audit both named the hidden key independently. The reproduction tests are every test above the marker in `tests/test_header_reader.py` and all of `tests/test_header_schemas.py`. The acceptance test is that all of them pass. The new ones are the two sections "what round 2 read wrongly" and "Review A's and the security audit's findings on round 2" in `tests/test_header_reader.py` (lines 1284 to 1798 at this checkpoint), named `test_r057_r3_*`: read those sections first.

A further round needs a reason it may not get, so read everything before writing.

This is the increment's third brief. Release B2 gives every record that both the supervisor and a bridge program read a small YAML front-matter header. This increment builds the foundation in `bridge/cursor-bridge/bridge_env.py`: the reader of a stated subset of YAML (`read_header`, `HeaderError`), the schemas (`HEADER_SCHEMAS`), the schema check (`check_header`) and the agreement helper (`header_agrees`), with the fixtures under `tests/fixtures/headers/`. No program reads a header yet, so nothing imports the new names except the tests, and the code must be right on its tests alone. A hook will later depend on this reader failing only one way on a string: `HeaderError`.

Satisfies: R-057

R-057's text: `bridge_env.py` holds the one reader of a record's YAML front-matter header, the schemas and the one copy of every fallback reader. This increment builds the reader, the schemas, `check_header`, `header_agrees`, the `pyyaml` cross-check and the D-005 comparison; the fallback readers' move and the currency test are other increments', so `docs/REQUIREMENTS.md` is not touched and the row stays `planned`.

## Scope
One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_header_reader.py
- tests/test_header_schemas.py
- tests/fixtures/headers/
- docs/BUILDER_NOTES.md
- handoff/TASK-046-r3-report.md

Do not modify anything else. `tests/test_header_reader.py` changes only below the marker line (see Context). `tests/test_header_schemas.py` is a fixed point: read it, change nothing in it. `MANIFEST.json` changes only by running its generator (the last brief's Requirement 48), never by hand.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names; in particular `handoff/TASK-046.md`, `handoff/TASK-046-r2.md` and `handoff/TASK-046-r2-report.md` (never revised), `docs/REQUIREMENTS.md`, `docs/BUILD_PLAN.md`, `docs/DESIGN.md`, `docs/INVENTORY.md`, `docs/PROJECT_STATUS.md` and every file under `docs/diagrams/`, which are the supervisor's records
- `bridge/cursor-bridge/VERSION` (its content stays `2026.11.03a`) and `bridge/cursor-bridge/CHANGELOG.md`
- every program under `bridge/cursor-bridge/` other than `bridge_env.py`: no program changes its reading in this increment, and no fallback reader moves
- every line of `bridge_env.py` above the line `# --- R-057 header reader, schemas, check and agreement (TASK-046) ---`: every existing function, constant and pattern stays byte-identical
- `HEADER_SCHEMAS`: its 19 tables were checked equal to D-005, key by key, order and type, by the reviewer, and do not change
- every other test file, and every line of `tests/test_header_reader.py` above the marker
- adding a header to any record of this repository

## Context
All paths are relative to the Workspace root, the folder you were started in. Read these in full before you write code: `tests/test_header_reader.py`, `tests/test_header_schemas.py`, `handoff/TASK-046-r2.md` (this brief keeps its requirements by reference, see Requirements), `handoff/TASK-046-r2-report.md`, `docs/diagrams/D-005-header-schemas.md`, and in `docs/DESIGN.md` the section "Change: release B2", its parts "The records and their headers", "Three kinds of record, one rule each", "Header first; fallback; malformed" and "The reader". Your reading of the design stops short of the migration, which is not yours.

**You may rewrite your own code, and the shape below is required.** Everything added below the line `# --- R-057 header reader, ...` in `bridge_env.py` is yours to rewrite, `HEADER_SCHEMAS` apart; nothing existing is. The shape under "The required shape" in Requirements is no longer advice. The body is never scanned character by character. The smallest clear code wins; remove what is dead.

**Development data:** the inventory's decision reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For this task that means: `read_header`, `check_header` and `header_agrees` are exercised only by the tests, on strings the tests hold and on the fixtures under `tests/fixtures/headers/`. Do not run any of them over this repository's live records, and do not run anything against another project.

**The host version.** `claude --version` is not on this session's PATH. Claude Code 2.1.317, read 2026-11-04 from the session's transcript records, as `docs/DESIGN.md`'s "Version" (under "Change: release B2") states. This increment relies on no host behaviour. Your report names this version.

**The fixed points, as this brief's commit holds them.**
- `tests/test_header_schemas.py`: entirely the supervisor's.
- `tests/test_header_reader.py`: every line above this exact line is the supervisor's: `# --- THE BUILDER'S CASES GO BELOW THIS LINE; NOTHING ABOVE IT IS EDITED ---`. You edit your own cases below that marker only as Requirement 13 says, and the file's helpers (`need`, `head`, `refused`, `block_of`, `text_with`, `equals_pyyaml`, `chain`, `valid`, `mutate`, `plan_header`, `plan_fallback`, `historic_fallback`, `historic_header`, and so on) are yours to call.
- **If you believe a fixed test is wrong, you do not edit it.** You write the objection in your report, leave that test failing, and go on with the rest.

**What exists in `bridge_env.py` that matters** (quoted as built): `def parse_review_name(name):` with the docstring `Read a review increment name: (id, round) or None when the grammar refuses.` (a plain name gives round 1). `def merge_unit_ids(text):` ends `return tuple(ids)`, which is why a `merge_unit` may reach `header_agrees` as a tuple. The module imports `json, os, re, shutil, subprocess, sys`, its docstring says `ASCII-only on purpose (cp1252 consoles)`, and the file holds no non-ASCII character. `session-start.py`'s `PHASE_MODULES` is what `test_r057_phase_set_is_the_hook_table` reads the eleven phases from.

**What the agreement readings copy, quoted as built.** `loop-guard.py`: `NOTHING = ("nothing", "none", "-", "")` and `a = (value or "").strip().strip("<>").strip().lower()` then `return a not in NOTHING and not a.startswith(("nothing", "none", "n/a"))`. `plan-check.py`: `kind = (fl.get("kind") or "increment").strip().lower()`, its field reader having already stripped the value. Read them; do not import them: `bridge_env` stays a leaf.

**The rulings this round rests on, already recorded by the supervisor.** `docs/DESIGN.md`, "The reader": "A block holding no key reads as the empty mapping" and "a key is at most 1,024 characters, `pyyaml`'s limit on a simple key". D-005, "Notes on values": a blank `Parallel:`, `Parent:`, `Depends on:`, `Diagrams:` or `Deferred:` line reads as an absent line, and a `Kind:` word outside the set disagrees with every header. You edit neither file.

**A settled point.** The design's plain-scalar rule refuses `y` and `n` although `pyyaml` reads them as strings, and `0o7`, `1e3`, `1a` likewise. The reader follows the design, not `pyyaml`; the test's `TYPED_ELSEWHERE` list says why. Do not raise this as an objection. This holds in a flow list too.

**Who supplies a fallback.** Other increments' readers will produce the fallback mappings that `header_agrees` takes (the shapes are the last brief's Requirement 44). In this increment only the tests produce them. Do not write a prose reader to produce one.

**Security context.** The project's ASVS level is 2 (`docs/DESIGN.md`, "Change: release B2", "Security and secret handling"; INVENTORY, Decisions). `.cursor/rules/secure-coding.mdc` is an applicable rule already in force. The trust boundary: the reader parses text from a file in the owner's checkout, so the header's text is input, possibly hostile or broken. It executes nothing, resolves no anchor, loads no module and bounds the block it reads, so a hostile header can at most fail a check or make a hook fall back. No secret, key or credential is read or needed: nothing here touches `.env`. The repository is public: no computer path or account name enters a fixture.

## Diagrams
This increment implements these normative diagrams.

`docs/diagrams/D-005-header-schemas.md`: all of its classes, already held by `HEADER_SCHEMAS`. Its section "Notes on values, from the design" holds the normalisations and value rules this round corrects to. The type grammar is its section "How the attributes are written": `string`, `integer`, `boolean`; `enum of a, b, c`; a class name of the diagram; `list of <type>`; and `<type> or null`, where `or null` applies to the whole type before it. The lines that set the pattern:
```
class BriefHeader {
    <<brief>>
    id : string
    round : integer
    satisfies : list of string
    scope : list of string
    merge_unit : list of string or null
    blocking_class : enum of behaviour, security, data integrity, safety mechanism, failing test or null
}
```

`docs/diagrams/D-002-components.md`: element `bridge_env` (`bridge/cursor-bridge/bridge_env.py`). The diagram draws edges into it and none out of it:
```
bridge_run --> bridge_env
plan_check --> bridge_env
```
`bridge_env` stays a leaf: it imports no program and nothing outside the standard library.

Conform to them: a key or a type in `HEADER_SCHEMAS` that D-005 does not draw, or an import from `bridge_env` to another component, is a failure at review. Everything the diagrams do not fix is yours to decide. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
"Requirement N" below is this brief's; "the last brief's Requirement N" is `handoff/TASK-046-r2.md`'s.

### The required shape (no longer advice)

1. One function splits one physical line into indentation, code and comment: one left-to-right scan respecting double quotes, with no state carried from a line to the next. A string opened on a line and not closed on it is that line's fault. Every reader of a line uses it, and the character rule uses it too: always-refused characters are refused anywhere in the raw line, with no skipping of any kind; any other non-ASCII character is refused outside the string and the comment the split found. One helper finds a string's end, and `_find_colon` and the flow list use it or the split, so there is one notion of a string. A backslash never skips a refused character or a line end.
2. The character rule runs per physical line, a line ending at LF or CRLF only, so a CR before an LF is the line's end in a comment as in code, a lone CR is a refused character, and each refusal names its own 1-based line. The scan of the whole block comes before the parse, as today: a refused character in an earlier line is named even if a later line is also wrong, and a refused character is named before the parse reaches a structural fault on an earlier line (`test_r057_r3_a_refused_character_is_named_at_its_own_line_after_a_backslash_at_a_line_end` has an unclosed string on line 2 and a tab on line 4, and names line 4).
3. `""` is the empty string only. Remove the doubled-quote branches everywhere: `"x""`, `"""`, `""""` are refused at their line. This replaces the last brief's Requirement 8 where it reads otherwise.
4. A list item's mapping uses the same path as any mapping: `- k:` is a key of a mapping whose column is the dash's plus two, so its child (at that column plus two, a blank or comment line between them changing nothing) and its later keys read, duplicates refused, depth counted alike. No frame takes a line's own column as its container's: `- k:` with a child list or mapping two levels too deep is refused at that line.
5. Every `.strip()`, `.rstrip()`, `.lstrip()` on block text takes the argument `" "` or is removed. The prose readings inside `header_agrees`, which are not block text, keep the readings quoted in Context.
6. `read_header` never lists the lines of the whole text. The first line is tested with `startswith` or `find`, the closing line found with `str.find` or one compiled multiline pattern keeping offsets, the body one slice. The `test_r057_r3_reading_a_text_holds_no_more_than_about_the_text_in_memory` cases bound the peak at three times the text. The byte bound is held before the block's characters are read, refused at the line after the opening one (its test, `test_r057_r3_the_byte_bound_is_held_before_the_characters_are_read`: a tab or a surrogate on a far line of an over-bound block is named line 2), and encoding a surrogate raises nothing.

### The other defects, each pinned by the tests

7. A key is at most 1,024 characters (`pyyaml`'s limit on a simple key), as a list item's key too; a longer one is refused at its line.
8. A block holding no key reads as the empty mapping, as today.
9. Messages. A word with a space, at a value, a list item or a list item's key, gives the plain-scalar advice holding `quote` and not `multi-line`; this replaces the last brief's Requirement 18 on that point, the rest of it standing. `a: [] x` and `a: [x]#c` are not called multi-line. `R&D`, `x&y`, `x!!y`, `x*y` are plain scalars with the advice, not `anchor`, `alias` or `tag`, those words kept for a marker that opens a value.
10. `check_header` gives one finding per fault: `record` missing, of another type, outside the set or other than the kind; `header` missing, of another type or other than 1; `statuses` however it is wrong, a word outside the four saying `set`; a role: an unknown role key is one finding, a known role naming a column absent from `columns` one finding naming the role, a non-string one finding. A key of any type (a tuple) raises nothing: `% (k,)`. Columns of any shape raise nothing, the comparison in about linear time (a frozenset built from hashable items), 20000 roles by 20000 columns under two seconds.
11. `header_agrees`. `_kind_norm` returns the stripped, lower-cased word, only absent or empty giving `increment`, so `bogus` disagrees. A blank `Parallel:`, `Parent:`, `Depends on:`, `Diagrams:` or `Deferred:` line (the value `""`) reads as an absent line. A `merge_unit` read as a tuple compares as a list, order kept.
12. Dead code goes, the last brief's group J first, which was not done: `_first_line_exact` and its re-check, `_bom`, `label` with the unused arguments that fill it. Then, at the line numbers of `bridge_env.py` as it stands at this checkpoint (157f914's): 1333, 1422, 1456, 1467, 1508, 1516, 1538, 1621, 1642-1645 (`except HeaderError: raise`), 1776-1779 (`except RecursionError` cannot fire under the eight-level bound), 1527-1530 (two branches, one effect), 1590 (`_line_col_for_frame`), 1845-1847, 1869-1871, 1878, 1892, 1912-1913, 1996-1997, 2036-2039, 2044-2045, and `_field_fallback` computed and unused for kind and parallel. Verify each is dead before removing it; whatever the rewrite makes unreachable goes too. The smallest clear code wins.
13. Your cases below the marker. `test_r057_mixed_list_mapping_depth_eight_reads_nine_refused` (the line ending `is not None`) asserts equality with `pyyaml`, as the last brief said. The form feed case's name and body also say it stands untouched in a body, as the last brief said. Other cases stay. If the rewrite makes one of your cases wrong by a requirement here, correct it and say which in the report.

### What still holds

Every requirement of `handoff/TASK-046-r2.md` under "What else must hold" and every ruling of its groups A to I still holds, with only the two changes stated at Requirements 3 and 9. `HEADER_SCHEMAS` does not change. Nothing above the `# --- R-057 header reader` line changes. No program changes. `tests/test_header_schemas.py` and everything above the marker in `tests/test_header_reader.py` are fixed points; an objection goes in the report with the test left failing.

## Acceptance criteria
- [ ] `python -m pytest tests/test_header_schemas.py tests/test_header_reader.py -q -p no:cacheprovider` passes, every test in both, or a failing fixed test carries your written objection in the report.
- [ ] `git diff -- tests/test_header_schemas.py` is empty, and `git diff -- tests/test_header_reader.py` changes only lines below the marker line.
- [ ] `git diff -- bridge/cursor-bridge/bridge_env.py` changes nothing above the line `# --- R-057 header reader, schemas, check and agreement (TASK-046) ---` and nothing in `HEADER_SCHEMAS`, and `bridge_env.py` holds no non-ASCII character.
- [ ] The named cause is addressed at its mechanism: one function splits a line and carries no state to the next, every reader of a line and the character rule use it, one helper finds a string's end, no doubled-quote branch remains, a list item's mapping goes the path of any mapping, no strip on block text lacks the argument `" "`, `read_header` lists no line of the whole text, and nothing in Requirement 12 that you verified dead remains.
- [ ] `tests/fixtures/headers/` holds one valid header per kind and one `forms` file; every fixture header read by `read_header` equals `yaml.safe_load`.
- [ ] No program under `bridge/cursor-bridge/` other than `bridge_env.py` differs from the checkpoint.
- [ ] `python bridge/cursor-bridge/diagram-check.py --mode code` prints `RESULT: OK` and no line starting `TESTS` (this run includes `check:components`).
- [ ] `python tools/make-manifest.py` was run after the last edit under `bridge/`, `VERSION` still reads `2026.11.03a`, and `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` reports the sources match.
- [ ] `python tools/dump-cli.py --check` exits 0, with `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` untouched.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` exits 0, no FAIL line.
- [ ] No program imports `yaml`; no new dependency; `bridge_env.py` imports nothing new outside the standard library and no program.
- [ ] R-057's clauses this increment builds (the Objective says which) are fully met, with no stand-in or placeholder, and every test of yours names R-057 in its name (`test_r057_...`), so the trace is checkable.
- [ ] The full suite, which the supervisor runs through the launcher after your run and you do not, passes with no other change in results.

## Constraints
- Do not edit `tests/test_header_schemas.py`, or `tests/test_header_reader.py` above its marker. An objection goes in your report, and the test stays failing.
- Do not fix by suppressing the symptom: no retry, broad `try/except`, widened tolerance, added `sleep`, or null-check that hides a wrong value. Do not leave any `DEBUG-BUG-` line or stray print.
- **If you believe the real cause is different from the one named, stop, do not change code, and report why in your summary:** the supervisor will re-diagnose.
- Do not move a fallback reader, change a program's reading, or import the new names into any program.
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This increment's new code starts no process at all.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the Development data paragraph in Context) and refuses the installed product's data; if the brief does not say where the development data is, stop and report it (rule 55).
- A value the brief marks as **the owner's** (a threshold, a price, a limit, a default, a wording) is fixed: the Context section names the test that pins it; do not change the value or that test, and report it if the work seems to need a change (rule 52). This brief marks none; the bounds (262,144 bytes, eight levels, a key of 1,024 characters) and the schemas are the design's and the diagram's, and are fixed the same way.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only, and `git rev-parse HEAD`, which the Done section names.
- Numbers from text are parsed with the language's own parser (`int`), never by slicing or splitting a string. The one number this reader reads is a decimal integer: no sign, no point, `0` or no leading zero, no unit at the reader; its range is what `int` accepts, and one it refuses is a `HeaderError` at its line whose message says integer. (Three defects in one project came from numbers read by hand.)
- This increment starts no process other than the tests and the checks named in Done, and adds no new kind of process.
- Every verification command the Done section asks you to run is written there in full, with its options and its working folder, so you run exactly it. You do NOT run the full suite this round: the supervisor runs it through the launcher. You write no hand-mutation table this round: the mutation run is the supervisor's. No script of a mutation lands in the diff.
- If `import yaml` fails in your environment, stop and report it: `pyyaml` is in `requirements.lock` and you install nothing.
- Prefer reuse over new code (existing helpers, the standard library, native platform features, already-installed dependencies) and write the minimum that meets the acceptance criteria. This never overrides a security, observability, or accessibility requirement stated above.

## Done
Run these from the Workspace root, the folder you were started in, in this order, once the code is final, and quote each command and the lines it printed in your report:

```
python -m pytest tests/test_header_schemas.py tests/test_header_reader.py -q -p no:cacheprovider
python tools/make-manifest.py
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
python bridge/cursor-bridge/diagram-check.py --mode code
python tools/dump-cli.py --check
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
git rev-parse HEAD
git status --short
```

Your report is the file `handoff/TASK-046-r3-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, one sentence stating how the change addresses the named cause, a line naming the host version (Claude Code 2.1.317, as Context says), the forms you chose for the last brief's Requirements 26 and 43, any objection to a fixed test, any case of yours corrected under Requirement 13 and any number of Requirement 12 you found not dead, with why, and, as its last section, a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`, which is acceptable only if it is true: the `merge_unit` tuple was an assumption last round's `none` omitted. Be specific: "edge cases" or "error handling" is not an item.

Check every statement your report makes about what the code does against the code as it stands before you write it. Last round's said "each container records the column", which was false for a first key's list.

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run; the full suite is one of those this round. Write the report's results after the commands above, naming the commit their counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
