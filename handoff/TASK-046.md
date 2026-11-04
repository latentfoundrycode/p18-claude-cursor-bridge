# TASK-046: The header reader and the schemas in bridge_env (R-057)

## Objective
Release B2 gives every record that both the supervisor and a bridge program read a small YAML front-matter header, so that a field has one home, one reader and one stated type. This increment builds the foundation and nothing that uses it: in `bridge/cursor-bridge/bridge_env.py`, the reader of a stated subset of YAML (`read_header`, `HeaderError`), the schemas of the eight record kinds as plain data (`HEADER_SCHEMAS`), the schema check (`check_header`) and the agreement helper (`header_agrees`), together with the fixtures under `tests/fixtures/headers/` that the `pyyaml` cross-check reads. No program reads a header yet and no fallback reader moves: TASK-047 to TASK-050 do that. So nothing imports the new names except the tests, and the new code must be right on its tests alone. A hook will later depend on this reader failing only one way, so a broken header is always a `HeaderError` and never any other exception.

Satisfies: R-057 - `bridge_env.py` holds the one reader of a record's YAML front-matter header, the schemas and the one copy of every fallback reader. This increment builds R-057's reader, schemas, `check_header`, `header_agrees`, the `pyyaml` cross-check and the D-005 comparison. The fallback readers' move and the currency test are TASK-047 to TASK-050's, and R-057's row flips built at TASK-050, so this brief does not touch `docs/REQUIREMENTS.md` and the row stays `planned`.

## Scope
One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_header_reader.py (only below the marker line, see Context)
- tests/test_header_schemas.py (a fixed point: read only, you change nothing in it)
- tests/fixtures/headers/
- docs/BUILDER_NOTES.md
- handoff/TASK-046-r1-report.md

Do not modify anything else. `MANIFEST.json` changes only by running its generator (Requirement 22), never by hand.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names; in particular `docs/REQUIREMENTS.md`, `docs/BUILD_PLAN.md`, `docs/DESIGN.md`, `docs/INVENTORY.md`, `docs/PROJECT_STATUS.md` and every file under `docs/diagrams/`, which are the supervisor's records
- `bridge/cursor-bridge/VERSION` (its content stays `2026.11.03a`) and `bridge/cursor-bridge/CHANGELOG.md`
- every program under `bridge/cursor-bridge/` other than `bridge_env.py`: no program changes its reading in this increment, and no fallback reader moves
- every existing function, constant and pattern of `bridge_env.py`: you only add to the file
- every other test file, and every line of `tests/test_header_reader.py` above the marker
- adding a header to any record of this repository (no record carries one before TASK-054)

## Context
All paths are relative to the Workspace root, the folder you were started in. Read these in full before you write code: `tests/test_header_reader.py`, `tests/test_header_schemas.py`, `docs/diagrams/D-005-header-schemas.md`, and in `docs/DESIGN.md` the section "Change: release B2", its parts "The records and their headers", "Three kinds of record, one rule each", "Header first; fallback; malformed" and "The reader". Your reading of the design stops short of the migration: `records-migrate.py` is TASK-051's and is not yours.

**Development data:** the inventory's decision reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For this task that means: `read_header`, `check_header` and `header_agrees` are exercised only by the tests, on strings the tests hold and on the fixtures you write under `tests/fixtures/headers/`. Do not run any of them over this repository's live records, and do not run anything against another project.

**The host version.** `claude --version` is not on this session's PATH. Claude Code 2.1.317, read 2026-11-04 from the session's transcript records, as `docs/DESIGN.md`'s "Version" (under "Change: release B2") states. The two facts the design re-observed on it stand, and this increment relies on no host behaviour. Your report names this version.

**The fixed points.** The supervisor committed the acceptance tests at 27d321f, on this branch, and they are red today because the names do not exist yet:
- `tests/test_header_schemas.py`: entirely fixed.
- `tests/test_header_reader.py`: every line above this exact line is fixed: `# --- THE BUILDER'S CASES GO BELOW THIS LINE; NOTHING ABOVE IT IS EDITED ---`. You add your own cases below that marker, and the file's helpers (`need`, `head`, `refused`, `chain`, `valid`, `mutate`, `plan_header`, `plan_fallback`, and so on) are yours to call.
- **If you believe a fixed test is wrong, you do not edit it.** You write the objection in your report, leave that test failing, and go on with the rest.

**What exists in `bridge_env.py` that matters** (quoted as built): `BLOCKING_CLASSES = frozenset(("behaviour", "security", "data integrity", "safety mechanism", "failing test",))`; `def parse_review_name(name):` with the docstring `Read a review increment name: (id, round) or None when the grammar refuses.` (a plain name gives round 1). The module imports `json, os, re, shutil, subprocess, sys`, and its docstring says `ASCII-only on purpose (cp1252 consoles)`; the file holds no non-ASCII character today. `session-start.py`'s `PHASE_MODULES` is what `test_r057_phase_set_is_the_hook_table` reads the eleven phases from, and they already equal D-005's `phase` set.

**A settled point.** The design's plain-scalar rule refuses `y` and `n` although `pyyaml` reads them as strings, and `0o7`, `1e3`, `1a` likewise. The reader follows the design, not `pyyaml`; the test's `TYPED_ELSEWHERE` list says why. Do not raise this as an objection.

**Who supplies a fallback.** TASK-047 to TASK-050's readers will produce the fallback mappings that `header_agrees` takes (the shapes are Requirement 18). In this increment only the tests produce them. Do not write a prose reader to produce one.

**Security context.** The project's ASVS level is 2 (`docs/DESIGN.md`, "Change: release B2", "Security and secret handling"; INVENTORY, Decisions). `.cursor/rules/secure-coding.mdc` is an applicable rule already in force. The trust boundary: the reader parses text from a file in the owner's checkout, so the header's text is input, possibly hostile or broken. It executes nothing, resolves no anchor, loads no module and bounds the block it reads, so a hostile header can at most fail a check or make a hook fall back. No secret, key or credential is read or needed: nothing here touches `.env`. The repository is public: no computer path or account name enters a fixture.

## Diagrams
This increment implements these normative diagrams.

`docs/diagrams/D-005-header-schemas.md`: all of its classes. `tests/test_header_schemas.py` reads the classes and attributes from that file and compares them with `HEADER_SCHEMAS`, key by key and type by type, either side's extra failing. The classes the test expects as tables are the eight kinds by their `record` value and the eleven nested classes `WorkflowPart`, `Stage`, `Increment`, `InventoryTables`, `TableShape`, `RequirementsRoles`, `DiagramIndexRoles`, `DeviationsRoles`, `CeilingLift`, `DesignLift`, `ReviewLift`; `HeaderRecord` itself is not a table, its two keys open each kind. The lines that set the pattern:
```
class HeaderRecord {
    <<abstract>>
    record : enum of project-status, build-plan, brief, inventory, requirements, diagram-index, deviations, run-parameters
    header : integer
}
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
The type grammar is D-005's section "How the attributes are written": `string`, `integer`, `boolean`; `enum of a, b, c` (items separated by `, `, an item may hold a space); a class name of the diagram; `list of <type>`; and `<type> or null`, where `or null` applies to the whole type before it. D-005's section "Notes on values, from the design" holds the normalisations and value rules.

`docs/diagrams/D-002-components.md`: element `bridge_env` (`bridge/cursor-bridge/bridge_env.py`). The diagram draws edges into it and none out of it:
```
bridge_run --> bridge_env
plan_check --> bridge_env
```
`bridge_env` stays a leaf: it imports no program and nothing outside the standard library.

Conform to them: a key or a type in `HEADER_SCHEMAS` that D-005 does not draw, or an import from `bridge_env` to another component, is a failure at review. Everything the diagrams do not fix is yours to decide. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
**Which existing behaviour you may change: none.** Everything here is an addition, and every existing test stays green.

**The reader: `read_header(text)`**

1. `read_header(text)` returns the pair `(header, body)`. The header is the mapping, or `None` where the first line is not exactly `---` (a byte-order mark before it tolerated); in that case the body is the whole text, unchanged. `---` then `---` is an empty mapping. The block ends at the next line that is exactly `---`, and everything after that line is the body, a later `---` line included.
2. A CRLF record reads like an LF one, and its body keeps its own line endings. A line ends at LF or CRLF and nowhere else: a form feed or a Unicode separator such as U+2028 inside a line does not end it, so that line numbers and the body stay true (the note of 2026-10-16 TASK-006-r6 in `docs/BUILDER_NOTES.md` is the same pitfall).
3. `HeaderError` carries `.line`, an `int`, the 1-based line of the whole text (the opening `---` is line 1, and a byte-order mark shifts nothing), and its message names that number. A refused plain scalar and a single-quoted scalar carry advice holding the word `quote`.
4. The subset it reads (`docs/DESIGN.md`, "The reader"): `key: value` lines with a scalar; a double-quoted string, with `""` and exactly the two escapes `\"` and `\\` (any other escape refused); a decimal integer; exactly `true`, `false` or `null`; nothing (null); or a plain word. A flow list `[a, b]` of such scalars on one line. Block lists (`- ` items, scalars or mappings). Nested mappings and block lists by two-space indentation. `#` comments: a comment starts at a `#` outside a quoted string that opens the line or follows whitespace, so `"PR #135"` is text and `word#z` is refused.
5. A plain scalar is a string only where it is a word of letters, digits, `_`, `-` and `.` that starts with a letter and is not, in any case, one of YAML 1.1's typed words (`yes`, `no`, `on`, `off`, `y`, `n`, `true`, `false`, `null`, `~`), the exact lower-case `true`, `false` and `null` being the three scalars of Requirement 4. Every other plain scalar is refused with its line and the advice to double-quote it: a date, a signed or pointed number, an octal, hex, underscored or sexagesimal form, a word with a space, a colon or a slash, a typed word in another case. The forms are `TYPED_BY_PYYAML`, `NEVER_WRITTEN_PLAIN` and `TYPED_ELSEWHERE` in the test.
6. Refused, each with its line (`test_r057_structural_refusals` pins the lines): a single-quoted scalar, a tab in indentation, an anchor, an alias, a tag, a flow mapping alone or inside a list, a flow list inside a flow list, a multi-line plain, quoted or flow scalar, a block scalar (`|`, `>`), a duplicate key at any level, a line that is not a key line, text after a closing quote, and an unterminated block.
7. The byte bound: a block above 262,144 bytes is refused, the bytes being its UTF-8 bytes and not its characters (`test_r057_the_block_bound_is_in_bytes`).
8. The nesting bound: at most eight levels deep. Each mapping and each block list is a level of its own, the top mapping included: a chain of 8 nested keys reads, a chain of 10 is refused, the schemas' own six levels read (`test_r057_the_schemas_own_depth_reads`), and a list of mappings nested as in `test_r057_the_nesting_bound_holds_for_lists` is refused. A deep block under the byte bound is a `HeaderError`, never a `RecursionError` (`test_r057_a_very_deep_block_is_a_refusal_not_a_recursion_error`, 480 levels).
9. `read_header`'s one failure on any string is `HeaderError`: no `ValueError` from an integer over Python's digit limit, no `UnicodeEncodeError` from a lone surrogate while counting bytes, no `RecursionError`, no `IndexError`.
10. A form the subset does not state is refused with its line, never read a way `pyyaml` would not. In particular a key: a key is a lower-case word of letters, digits and `_`, and one `pyyaml` would type (`on:`, `null:`, `1:`) or a quoted key is refused, since the cross-check promises the same value in both readers. Keep `read_header`'s reading equal to `yaml.safe_load` on everything it accepts.

**The schemas: `HEADER_SCHEMAS`**

11. `HEADER_SCHEMAS` is plain data: `{<kind or class name>: {<key>: <type string>}}`. It holds the eight kinds by their `record` value, each opening with `record` and `header` (in that order, then D-005's attributes in D-005's order, since TASK-051 writes keys in the schema's order), and each nested class of D-005 by its class name. A type string is written as D-005 writes it. `record` on every kind is HeaderRecord's enum of the eight kinds; the value rule that a kind's `record` equals that kind is `check_header`'s.

**The schema check: `check_header(kind, header)`**

12. `check_header(kind, header)` returns a list of strings, empty where all is well, recursing into every nested class. The findings are the plan's list and no others: an unknown key (the string names it), a missing key (the string names it; a nullable key is still required), a wrong type, a value outside its set, a `record` other than `kind`, a `header` other than exactly `1`, a `statuses` list other than exactly the four words `planned`, `built`, `deferred`, `dropped` (fewer, others or a repeat are findings), a `roles` value naming a column absent from the header's own `columns` (the string names the role).
13. A bool is not an integer under `check_header`: `header: true` and `round: true` are findings. An integer has no range rule beyond `header`'s: `round` and `rounds` are counts, `agent_ceiling` and `seconds` are seconds, and `check_header` checks their type only. A kind `check_header` has no table for is a finding, not an exception.

**The agreement helper: `header_agrees(kind, header, fallback)`**

14. `header_agrees(kind, header, fallback)` returns a list of strings, empty where all is well. Each string is what follows `HEADER DISAGREES: ` in a program's line:
    - `<key>` for a line record (project-status, run-parameters) or a brief.
    - `<id> <field>` for an increment and `<stage name> <field>` for a stage, the stage name being the header's; stages are paired by position, so a renamed stage gives only `<header's name> name`.
    - `columns`, `roles.<role>` and `tables.<section>` for a tabular record, and the inventory's `reflected_through` and `development_data`. For the inventory, a section absent from the fallback gives exactly `tables.<section>`, and a section whose header row differs from its declared `columns` gives exactly `columns`. For a table with roles, a role's column absent from the header row gives `roles.<role>`, and a header row differing from `columns`, order included, gives `columns`.
15. The normalisations (`docs/DESIGN.md`, "Three kinds of record, one rule each"; D-005's "Notes on values"):
    - `awaiting_user_on`: a prose value that, stripped of `<` and `>`, starts with `nothing`, `none` or `n/a` in any case is no wait and agrees with `""`, as an absent line does, the hooks reading no line as no wait; any other value is compared as it stands.
    - A brief's `name` is read by `parse_review_name` and compared with `id` and `round`, which gives `id` or `round` respectively.
    - `scope`: entries compared exactly, a folder's `/` never added or removed on either side.
    - `parallel`: prose `yes` against `true`, `no` against `false`, an absent line against `false`.
    - `kind`: an absent line against `increment`.
    - `title` against the heading's title, a stage's `name` against its heading.
    - A stage's `demonstration` against the presence of a `Demonstration:` line with text: `None`, `""` and whitespace-only are absent.
    - `parent`, `depends_on`, `diagrams`: the filler `none`, in any case, reads as an absent line.
16. An absent line is an absent key or `None`, in every kind. An absent list line agrees with the empty list and an absent optional scalar's line with `null`; a list key the header fills and the fallback does not disagrees.
17. `historic` has no prose line and is compared with its derivation: true exactly where the fallback has no `scope` line, no `kind` line and the ID is in `merged`. Where `merged` is `None` (it could not be read) a mark is not compared on the merged part, so the mark is still a disagreement where a `scope` or `kind` line stands, and otherwise agrees. An increment or a stage standing on only one side is a non-empty result, in a form you choose and state in your report.
18. A fallback's shape, per kind:
    - project-status: `{phase, workflows (already the structured list), awaiting_user_on (the prose), bridge_version, stage, open_issues}`.
    - brief: `{name (the file's stem, read by parse_review_name for id and round), satisfies, scope, merge_unit, blocking_class}`.
    - build-plan: `{merged (a set, or None where it could not be read), stages: [{name, demonstration (the line's text or None), increments: [{id, title, fields: {kind, parent, depends_on, parallel, diagrams, scope, satisfies, deferred}}]}]}`, list fields already lists or the filler `none` in any case.
    - requirements, diagram-index and deviations: `{header_row}`.
    - inventory: `{reflected_through, development_data, sections: {<section>: <its header row>}}`.
    - run-parameters: the same keys as its header, bar `record` and `header`.

**The fixtures and your cases**

19. `tests/fixtures/headers/` holds `.md` files with invented content: one valid header per kind (each file's first line `---`; each passes `check_header` for its kind; no file name of these holding `forms`), and one file whose name holds `forms`, with the forms the subset admits, the strings `"PR #135"` and `""` among them, written with their double quotes. Every fixture's closing `---` is followed by a line ending, and no fixture has an empty header: `yaml.safe_load` of an empty block is `None` where the reader gives `{}`, so `test_r057_every_fixture_header_equals_pyyaml` would fail on one.
20. Your own cases go below the marker in `tests/test_header_reader.py`, each named `test_r057_...`. At the least: a chain of exactly 9 nested keys refused, and a mixed list-and-mapping block of exactly 8 levels read and of 9 refused; a key `pyyaml` would type refused; an integer over Python's digit limit and a lone surrogate each a `HeaderError`; a form feed inside a quoted string neither ending the line nor changing a later line's number; a `HeaderError`'s line right on a CRLF record and on one with a byte-order mark; a `historic` mark with `merged` `None` where a `scope` line stands, disagreeing. In the test file, follow its own convention for a non-ASCII character (`chr()`, never typed).

**The prose and the release files**

21. A program's prose (a docstring, a comment, a help text) never quotes a retired pattern (KP-073; `bridge/cursor-bridge/Known-Pitfalls.md`): the enumerated list stands in `docs/DESIGN.md`, "The fallback readers, one copy each", "The retired readings, enumerated". What you write in `bridge_env.py` describes the rule in its own words. `bridge_env.py` stays ASCII-only: a non-ASCII character your code has to name is written as a Python escape sequence in the source, as `plan_increment_ids` does in its heading pattern.
22. `MANIFEST.json` is regenerated this way, after your last edit of anything under `bridge/`, from the Workspace root: `python tools/make-manifest.py`. It takes the version from the newest `## <version>` entry of `bridge/cursor-bridge/CHANGELOG.md` (`2026.11.03a`, today's `VERSION`), rewrites `bridge/cursor-bridge/VERSION` and rewrites `MANIFEST.json`. `VERSION`'s content must not change: if it does, stop and report it. `bridge-check.py --sources` in CI and the install and rollback tests refuse a tree whose hashes do not match, which is why the full suite runs after this step. Git may warn that LF in `VERSION` will become CRLF; that is not a change (the note of 2026-10-17 BUG-002-r1).
23. No command is added or changed and no dependency is added. `yaml` is imported by no program: it is imported by the tests only.

## Acceptance criteria
- [ ] `python -m pytest tests/test_header_schemas.py tests/test_header_reader.py -q -p no:cacheprovider` passes, every test in both, or a failing fixed test carries your written objection in the report.
- [ ] `git diff -- tests/test_header_schemas.py` is empty, and `git diff -- tests/test_header_reader.py` shows only added lines below the marker line.
- [ ] `tests/fixtures/headers/` holds one valid header per kind and one `forms` file, as Requirement 19 states; every fixture header read by `read_header` equals `yaml.safe_load`.
- [ ] `read_header`, `HeaderError`, `HEADER_SCHEMAS`, `check_header` and `header_agrees` exist in `bridge_env.py` in the forms the Requirements state, and no program under `bridge/cursor-bridge/` other than `bridge_env.py` differs from the checkpoint.
- [ ] Every existing function of `bridge_env.py` is byte-identical: the diff of the file holds additions only, a docstring sentence naming the new names apart.
- [ ] `python bridge/cursor-bridge/diagram-check.py --mode code` prints `RESULT: OK` and no line starting `TESTS` (this run includes `check:components`).
- [ ] `python tools/make-manifest.py` was run after the last edit under `bridge/`, `VERSION` still reads `2026.11.03a`, and `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` reports the sources match.
- [ ] `python tools/dump-cli.py --check` exits 0, with `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` untouched.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` exits 0, no FAIL line.
- [ ] No program imports `yaml`; no new dependency; `bridge_env.py` imports nothing new outside the standard library and no program.
- [ ] The full suite passes, every existing test green.
- [ ] R-057's clauses this increment builds (the Objective says which) are fully met, with no stand-in or placeholder, and every test of yours names R-057 in its name, so the trace is checkable.

## Constraints
- Do not edit `tests/test_header_schemas.py`, or `tests/test_header_reader.py` above its marker. An objection goes in your report, and the test stays failing.
- Do not move a fallback reader, change a program's reading, or import the new names into any program.
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way — an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason — append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python — `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This increment's new code starts no process at all.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the Development data paragraph in Context) and refuses the installed product's data; if the brief does not say where the development data is, stop and report it (rule 55).
- A value the brief marks as **the owner's** (a threshold, a price, a limit, a default, a wording) is fixed: the Context section names the test that pins it; do not change the value or that test, and report it if the work seems to need a change (rule 52). This brief marks none; the bounds (262,144 bytes, eight levels) and the schemas are the design's and the diagram's, and are fixed the same way.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only, and `git rev-parse HEAD`, which the Done section names.
- Numbers from text are parsed with the language's own parser (`int`), never by slicing or splitting a string. The one number this reader reads is a decimal integer: no sign, no point, `0` or no leading zero, no unit at the reader; its range is what `int` accepts, and one it refuses is a `HeaderError`. (Three defects in one project came from numbers read by hand.)
- This increment starts no process other than the tests and the checks named in Done, and adds no new kind of process.
- Every verification command the Done section asks you to run is written there in full, with its options and its working folder, so you run exactly it. The increment's tests are checked by mutation: you mutate by hand, in-process, in your own run (the list in Done), restoring the file after each, and you list each mutation with what caught it; no script of it lands in the diff. The mutation run itself (the supervisor's mutants file, applied by the bridge's `mutation-run.py` on a scratch copy of the Workspace) is the supervisor's side's, written after your run. The full suite runs in Done, and no failure outside the Scope is on record at this checkpoint, so none is named here: if one appears, report it by its test id as an unexpected result and fix nothing outside the Scope. A test gated on the CI variables skips locally (KP-074), and that skip is not a failure.
- If `import yaml` fails in your environment, stop and report it: `pyyaml` is in `requirements.lock` and you install nothing.
- Prefer reuse over new code — existing helpers, the standard library, native platform features, already-installed dependencies — and write the minimum that meets the acceptance criteria. This never overrides a security, observability, or accessibility requirement stated above.

## Done
Run these from the Workspace root, in this order, once the code is final and the hand mutations below are done and restored, and quote each command and the lines it printed in your report:

```
python -m pytest tests/test_header_schemas.py tests/test_header_reader.py -q -p no:cacheprovider
python tools/make-manifest.py
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
python bridge/cursor-bridge/diagram-check.py --mode code
python tools/dump-cli.py --check
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
python -m pytest tests -q -p no:cacheprovider
git rev-parse HEAD
git status --short
```

The hand mutations, each applied to `bridge_env.py` in your run, the first pytest command above run, the file restored, and listed in your report by its label and text with the test that caught it. A mutation nothing catches gets a case of yours below the marker, and the report says so.
- M1: drop the key `historic` from the `Increment` table of `HEADER_SCHEMAS`.
- M2: widen a type: the brief's `round` becomes `integer or null`.
- M3: remove the refusal of a flow mapping.
- M4: remove the refusal of a duplicate key.
- M5: compare the typed words in lower case only, so that `Yes` reads as a string.
- M6: count the byte bound in characters and not in UTF-8 bytes.
- M7: raise the nesting bound from eight to nine.
- M8: accept a bool as an integer under `check_header`.
- M9: treat a repeat in `statuses` as no finding (compare as a set).
- M10: invert the `parallel` comparison in `header_agrees`.
- M11: reduce the no-wait normalisation of `awaiting_user_on` to equality with `nothing`.
- M12: treat `merged` `None` as the empty set in the `historic` derivation.

Your report is the file `handoff/TASK-046-r1-report.md`, which you write as you go — what you did, what you changed, what you ran and what it printed, what you could not do — so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, a line naming the host version (Claude Code 2.1.317, as Context says), any objection to a fixed test, and, as its last section, a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm — the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. Each mutation is listed by this brief's own label and text, with what caught it. A command you did not run is written `not run`, never described as run. Run the suite once, after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
