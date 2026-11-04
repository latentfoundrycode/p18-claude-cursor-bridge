# TASK-046-r2: The header reader, schema check and agreement helper repaired (R-057, round 2)

## Objective
Fix the following confirmed defect — repair the named cause, nothing else. The root cause of most of what follows: round 1's parser read a line by partitioning it and guarded it with regular expressions over the raw line, so a quoted string or a comment was judged as structure, Unicode space was taken for whitespace, and a line's column was never held to its container's. Every defect in groups A to J under Requirements is its own cause, proven by a failing test or a probe; no diagnosis round is needed.

Evidence: at checkpoint f4e12e7 the supervisor's tests print `138 failed, 458 passed in 53.88s` on round 1's code. The reproduction tests are every test above the marker in `tests/test_header_reader.py` and all of `tests/test_header_schemas.py`. The acceptance test is that all of them pass.

This is the increment's second brief. Release B2 gives every record that both the supervisor and a bridge program read a small YAML front-matter header. This increment builds the foundation in `bridge/cursor-bridge/bridge_env.py`: the reader of a stated subset of YAML (`read_header`, `HeaderError`), the schemas (`HEADER_SCHEMAS`), the schema check (`check_header`) and the agreement helper (`header_agrees`), with the fixtures under `tests/fixtures/headers/`. No program reads a header yet, so nothing imports the new names except the tests, and the code must be right on its tests alone. A hook will later depend on this reader failing only one way on a string: `HeaderError`.

Satisfies: R-057

R-057's text: `bridge_env.py` holds the one reader of a record's YAML front-matter header, the schemas and the one copy of every fallback reader. This increment builds the reader, the schemas, `check_header`, `header_agrees`, the `pyyaml` cross-check and the D-005 comparison; the fallback readers' move and the currency test are TASK-047 to TASK-050's, R-057's row flips built at TASK-050, so `docs/REQUIREMENTS.md` is not touched and the row stays `planned`.

## Scope
One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_header_reader.py
- tests/test_header_schemas.py
- tests/fixtures/headers/
- docs/BUILDER_NOTES.md
- handoff/TASK-046-r2-report.md

Do not modify anything else. `tests/test_header_reader.py` changes only below the marker line (see Context). `tests/test_header_schemas.py` is a fixed point: read it, change nothing in it. `MANIFEST.json` changes only by running its generator (Requirement 48), never by hand.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names; in particular `handoff/TASK-046.md` (the first brief, never revised), `docs/REQUIREMENTS.md`, `docs/BUILD_PLAN.md`, `docs/DESIGN.md`, `docs/INVENTORY.md`, `docs/PROJECT_STATUS.md` and every file under `docs/diagrams/`, which are the supervisor's records
- `bridge/cursor-bridge/VERSION` (its content stays `2026.11.03a`) and `bridge/cursor-bridge/CHANGELOG.md`
- every program under `bridge/cursor-bridge/` other than `bridge_env.py`: no program changes its reading in this increment, and no fallback reader moves
- every line of `bridge_env.py` above the line `# --- R-057 header reader, schemas, check and agreement (TASK-046) ---`: every existing function, constant and pattern stays byte-identical
- `HEADER_SCHEMAS`: its 19 tables were checked equal to D-005, key by key, order and type, by the reviewer, and do not change
- every other test file, and every line of `tests/test_header_reader.py` above the marker
- adding a header to any record of this repository (no record carries one before TASK-054)

## Context
All paths are relative to the Workspace root, the folder you were started in. Read these in full before you write code: `tests/test_header_reader.py`, `tests/test_header_schemas.py`, `docs/diagrams/D-005-header-schemas.md`, `handoff/TASK-046-r1-report.md`, and in `docs/DESIGN.md` the section "Change: release B2", its parts "The records and their headers", "Three kinds of record, one rule each", "Header first; fallback; malformed" and "The reader". Your reading of the design stops short of the migration: `records-migrate.py` is TASK-051's and is not yours.

**You may rewrite your own code, and you are advised to.** Everything round 1 added below the line `# --- R-057 header reader, ...` in `bridge_env.py` is yours to rewrite, `HEADER_SCHEMAS` apart; nothing existing is. The advised shape: first apply the character rule to the block; then split each physical line once, by one left-to-right scan, into its indentation, its code part and its comment, respecting double quotes, and judge only the code part; then a stack of (column, container), so that every line's column must equal its container's exactly. Linear time over the block. The body is never scanned character by character: find the closing line with `str.find` on line ends or a compiled pattern, the design saying the body is not read. The smallest clear code wins; remove what is dead.

**Development data:** the inventory's decision reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (the copy under the agent's home folder), never the one being edited, and installs reach running projects only through the owner's install run sheet". For this task that means: `read_header`, `check_header` and `header_agrees` are exercised only by the tests, on strings the tests hold and on the fixtures under `tests/fixtures/headers/`. Do not run any of them over this repository's live records, and do not run anything against another project.

**The host version.** `claude --version` is not on this session's PATH. Claude Code 2.1.317, read 2026-11-04 from the session's transcript records, as `docs/DESIGN.md`'s "Version" (under "Change: release B2") states. This increment relies on no host behaviour. Your report names this version.

**The fixed points, checkpoint f4e12e7.**
- `tests/test_header_schemas.py`: entirely the supervisor's.
- `tests/test_header_reader.py`: every line above this exact line is the supervisor's: `# --- THE BUILDER'S CASES GO BELOW THIS LINE; NOTHING ABOVE IT IS EDITED ---`. You edit your own cases below that marker (group I), and the file's helpers (`need`, `head`, `refused`, `chain`, `valid`, `mutate`, `plan_header`, `plan_fallback`, `historic_fallback`, `historic_header`, and so on) are yours to call.
- **If you believe a fixed test is wrong, you do not edit it.** You write the objection in your report, leave that test failing, and go on with the rest.

**What exists in `bridge_env.py` that matters** (quoted as built): `def parse_review_name(name):` with the docstring `Read a review increment name: (id, round) or None when the grammar refuses.` (a plain name gives round 1). The module imports `json, os, re, shutil, subprocess, sys`, its docstring says `ASCII-only on purpose (cp1252 consoles)`, and the file holds no non-ASCII character. `session-start.py`'s `PHASE_MODULES` is what `test_r057_phase_set_is_the_hook_table` reads the eleven phases from.

**What the agreement readings copy, quoted as built.** `loop-guard.py`: `NOTHING = ("nothing", "none", "-", "")` and `a = (value or "").strip().strip("<>").strip().lower()` then `return a not in NOTHING and not a.startswith(("nothing", "none", "n/a"))`. `plan-check.py`: `kind = (fl.get("kind") or "increment").strip().lower()`, its field reader having already stripped the value. Read them; do not import them: `bridge_env` stays a leaf.

**A settled point.** The design's plain-scalar rule refuses `y` and `n` although `pyyaml` reads them as strings, and `0o7`, `1e3`, `1a` likewise. The reader follows the design, not `pyyaml`; the test's `TYPED_ELSEWHERE` list says why. Do not raise this as an objection. This now holds in a flow list too: round 1's exception for `y` and `n` there came from a test of the supervisor's that was wrong and is corrected.

**Who supplies a fallback.** TASK-047 to TASK-050's readers will produce the fallback mappings that `header_agrees` takes (the shapes are Requirement 44). In this increment only the tests produce them. Do not write a prose reader to produce one.

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

### The defects, each with what must hold

**A. The character rule** (`docs/DESIGN.md`, "The reader", as revised; it replaces the first brief's Requirement on line endings for the block).

1. Only the ASCII space is whitespace to the reader. `isspace`, `strip` and `rstrip` without an argument treat Unicode space as whitespace, which is round 1's defect: `a: word` U+00A0 `#z` drops text as a comment.
2. Refused anywhere in the block, in a quoted string and in a comment too, each at its own 1-based line: a tab, any other C0 control, a lone carriage return, DEL, the C1 range with U+0085, U+2028, U+2029, a surrogate, U+FFFE, U+FFFF. Round 1 read tabs, and `a: 1 # c` U+2028 `b: 2` hid a key `pyyaml` reads.
3. A line ends at LF or CRLF and nowhere else, so a lone CR is inside its line. That holds for the first line and the closing line too: `---` followed by a lone CR is neither, at the very end of the text as well, where no LF follows it.
4. Any other non-ASCII character is refused outside a quoted string or a comment, and stands as text inside them.
5. A body and a headerless text are left exactly as they are, a byte-order mark of a headerless text included: `read_header` then returns `None` and the whole text, unchanged.

**B. Structural guards apply to the code part only.**

6. A quoted string or a comment holding `&x`, `*x`, `!!`, `{b: c}`, `[[x]]`, `|` or `>` is text; round 1 refused it.
7. No guard is quadratic. Review A's S3: the flow-mapping guard took 17.8 s on a quoted run of 262000 `{`; the tests give five seconds.

**C. Forms read otherwise than `pyyaml` or not stated, each refused with its line.** The tests pin each line.

8. `"x""y"`: `""` is the empty string only, not a doubled quote.
9. `a:b`, `a:[x]`, `a:#x`, `- b:c`: a colon needs a following space or the line's end.
10. `a : 1`, `- k : 1`: no space before a colon.
11. `-  x`, `-  k: 1`: exactly one space after a dash. `- ` and `-` alone are refused.
12. `- [x, z]`: a flow list is no list item. `[,x]`, `[x,,y]`, `[x, z,]`: no empty flow item.
13. A flow item is held to the plain-scalar rule, `y` and `n` included.
14. Indentation is exactly two spaces per mapping level, and a list item's mapping keys stand at the item's column plus two. Refused: an indent of one, three or four; a list at its key's column; a list indented by four; a root key indented; a line deeper than the key before it; a list item deeper than the one before it; a key deeper or shallower than its list item's first key.

**D. Forms round 1 read wrongly, which must read as `pyyaml` does.**

15. `- k:` with no value keeps `k` (null, or its nested mapping or list); round 1 dropped it.
16. A blank or comment line between a key and its child changes nothing; round 1 lost the child.
17. The nesting bound counts containers only. The top mapping is level 1 and each block mapping and each block list is a level. A null key at level 8 reads, a list of scalars at level 8 reads, a flow list is no level of its own (round 1 refused the first two). The refusal names the line that opens the ninth container.

**E. Messages.**

18. A list item refused as a scalar carries the advice holding `quote`, as every refused plain or single-quoted scalar does (`- 'x: y'`, `- 1:30`, `- yes`, `- b:c`); round 1 said `bad key`. A word with a space is not called multi-line.

**F. `read_header` takes a string.**

19. A value that is not a string raises `TypeError` rather than being coerced (remove the `str(text)`). A string's one failure stays `HeaderError`. Keep one last-resort `except Exception` at most, on a real line where it can be known.

**G. `header_agrees`.** State in its docstring that its header is one `check_header` found nothing in.

20. An absent line is an absent key or `None` in every kind: an absent list line agrees with `[]` in the status file, a brief and the run parameters, and a brief's null `merge_unit` agrees with an absent line. A list the header fills disagrees with an absent line.
21. Ruling, new since the first brief: a key typed `string` and never null whose line is absent (`stage`, `bridge_version`, the five run-parameter values, the inventory's `development_data`) agrees with `""`, as `awaiting_user_on` does; a filled one disagrees.
22. No-wait reads as `loop-guard.py`'s `names_a_wait` reads it: stripped, `<` and `>` stripped at the ends only, stripped, lower-cased; then `nothing`, `none`, `-` and empty, or starting `nothing`, `none`, `n/a`. Such a value agrees with `""`; any other is compared as it stands.
23. `kind` reads as `plan-check.py` reads it: stripped and lower-cased, with absent, empty or only spaces the default `increment` (`test_r057_r2_kind_read_as_the_plan_check_reads_it`).
24. The filler `none`, in any case, applies to `parent`, `depends_on` and `diagrams` only: `scope: none` and `satisfies: None` disagree against `[]`. This corrects the first brief.
25. `merged` `None` compares every field as usual and only the merged part of the mark is skipped: a mark where a `scope` or `kind` line stands still disagrees, and otherwise the mark agrees. Round 1's skip of `scope` and `kind` is the defect; nothing asked for it. Remove `_derived_historic`'s unreachable branch.
26. An increment's ID differing at the same position, and increments in another order, disagree. The form is yours; state it in your report.
27. No early return: an extra increment or stage is reported beside every disagreement of the paired part.
28. Run parameters compare every key of the schema bar `record` and `header`. The inventory compares every section of either side: a section absent from either side, a surplus fallback section and a section that is `None` each give `tables.<section>`. `columns` is reported once however many sections differ.

**H. `check_header`.**

29. `statuses` in any order is no finding; a repeat or a nested item is a finding and no exception. A kind with no table is a finding whatever it is, a tuple included (`%` formatting raises today); only the eight kinds are kinds. A missing key is exactly one finding. A null where the type is not nullable is `wrong type`, never `missing`. A value outside its set says `set` in its text and names the key. A wrong `record` is one finding.

**I. Your own cases below the marker.** The other cases stay as they are.

- `test_r057_an_integer_over_the_digit_limit_is_a_header_error` is vacuous, its key `n` being refused first: use key `a` and assert the line and that the message says integer.
- `test_r057_a_lone_surrogate_in_the_block_is_a_header_error`: quoted, on a later line, the line asserted.
- `test_r057_mixed_list_mapping_depth_eight_reads_nine_refused` miscounts and passes only through the dropped key. These lines are 8 levels and equal `pyyaml`: `root:`, `  - k0:`, `      inner:`, `        - k1:`, `            inner:`, `              - word`. With the last line `              - leaf: word` they are 9, refused at line 7.
- `test_r057_a_form_feed_inside_a_quoted_string_is_text` now contradicts the character rule: a form feed in a quoted string is refused at its own line, and stands untouched in a body. Rewrite the case and its name to say so.
- `test_r057_historic_with_merged_none_and_scope_line_disagrees` asserts exactly `["TASK-046 historic"]` and passes only through the skip Requirement 25 removes: its header's `scope` is `[]` against a fallback's `["a.py"]`, so the result now also holds `TASK-046 scope`. Assert both, in any order.
- `test_r057_historic_mark_when_merged_set_is_empty` duplicates a supervisor's test: remove it.

**J. Dead code goes:** `_PHASES`, `_INCREMENT_KINDS`, `in_string_state`, `_count_indent`, `_ParseFrame.expect` and `.indent` where unused, `self.block`, `label`, `si`, `_bom`, `_first_line_exact` and its re-check, `len(stack) != 1`, `out or [...]`.

### What else must hold: the first brief's requirements as these defects leave them

**The reader: `read_header(text)`**

30. `read_header(text)` returns the pair `(header, body)`. The header is the mapping, or `None` where the first line is not exactly `---` (a byte-order mark before it tolerated). `---` then `---` is an empty mapping. The block ends at the next line that is exactly `---`, and everything after that line is the body, a later `---` line included. A CRLF record reads like an LF one, and its body keeps its own line endings.
31. `HeaderError` carries `.line`, an `int`, the 1-based line of the whole text (the opening `---` is line 1, and a byte-order mark shifts nothing), and its message names that number. A refused plain scalar and a single-quoted scalar carry advice holding the word `quote`.
32. The subset it reads (`docs/DESIGN.md`, "The reader"): `key: value` lines with a scalar; a double-quoted string, with `""` and exactly the two escapes `\"` and `\\` (any other escape refused); a decimal integer; exactly `true`, `false` or `null`; nothing (null); or a plain word. A flow list `[a, b]` of such scalars on one line. Block lists (`- ` items, scalars or mappings). Nested mappings and block lists by two-space indentation. `#` comments: a comment starts at a `#` outside a quoted string that opens the line or follows a space, so `"PR #135"` is text and `word#z` is refused.
33. A plain scalar is a string only where it is a word of letters, digits, `_`, `-` and `.` that starts with a letter and is not, in any case, one of YAML 1.1's typed words (`yes`, `no`, `on`, `off`, `y`, `n`, `true`, `false`, `null`, `~`), the exact lower-case `true`, `false` and `null` being the three scalars of Requirement 32. Every other plain scalar is refused with its line and the advice to double-quote it: a date, a signed or pointed number, an octal, hex, underscored or sexagesimal form, a word with a space, a colon or a slash, a typed word in another case. The forms are `TYPED_BY_PYYAML`, `NEVER_WRITTEN_PLAIN` and `TYPED_ELSEWHERE` in the test.
34. Refused, each with its line (`test_r057_structural_refusals` pins the lines): a single-quoted scalar, an anchor, an alias, a tag, a flow mapping alone or inside a list, a flow list inside a flow list, a multi-line plain, quoted or flow scalar, a block scalar (`|`, `>`), a duplicate key at any level, a line that is not a key line, text after a closing quote, and an unterminated block. Your case `test_r057_flow_mapping_refusal_names_flow_mapping` keeps the words `flow mapping` in that message.
35. The byte bound: a block above 262,144 bytes is refused, the bytes being its UTF-8 bytes and not its characters. The block is the text from after the opening line's end up to the closing line's start, its line endings included (`test_r057_the_block_bound_is_in_bytes`, `test_r057_r2_the_block_bound_is_exact`).
36. The nesting bound: at most eight levels deep, as Requirement 17 counts them. A chain of 8 nested keys reads, a chain of 9 is refused, the schemas' own six levels read (`test_r057_the_schemas_own_depth_reads`). A deep block under the byte bound is a `HeaderError`, never a `RecursionError` (`test_r057_a_very_deep_block_is_a_refusal_not_a_recursion_error`, 480 levels).
37. On a string, `read_header`'s one failure is `HeaderError`: no `ValueError` from an integer over Python's digit limit, no `UnicodeEncodeError` from a lone surrogate while counting bytes, no `RecursionError`, no `IndexError`.
38. A form the subset does not state is refused with its line, never read a way `pyyaml` would not. A key is a lower-case word of letters, digits and `_`; one `pyyaml` would type (`on:`, `null:`, `1:`) or a quoted key is refused. Keep `read_header`'s reading equal to `yaml.safe_load` on everything it accepts (`test_r057_r2_every_block_the_reader_accepts_of_these_fragments_equals_pyyaml`).

**The schema check: `check_header(kind, header)`**

39. `check_header(kind, header)` returns a list of strings, empty where all is well, recursing into every nested class. The findings are these and no others: an unknown key (the string names it), a missing key (the string names it; a nullable key is still required), a wrong type, a value outside its set, a `record` other than `kind`, a `header` other than exactly `1`, a `statuses` list other than exactly the four words `planned`, `built`, `deferred`, `dropped` in any order (fewer, others or a repeat are findings), a `roles` value naming a column absent from the header's own `columns` (the string names the role).
40. A bool is not an integer under `check_header`: `header: true` and `round: true` are findings. An integer has no range rule beyond `header`'s: `round` and `rounds` are counts, `agent_ceiling` and `seconds` are seconds, and `check_header` checks their type only.

**The agreement helper: `header_agrees(kind, header, fallback)`**

41. `header_agrees(kind, header, fallback)` returns a list of strings, empty where all is well. Each string is what follows `HEADER DISAGREES: ` in a program's line: `<key>` for a line record (project-status, run-parameters) or a brief; `<id> <field>` for an increment and `<stage name> <field>` for a stage, the stage name being the header's, stages paired by position, so a renamed stage gives only `<header's name> name`; `columns`, `roles.<role>` and `tables.<section>` for a tabular record, and the inventory's `reflected_through` and `development_data`. A section whose header row differs from its declared `columns` gives exactly `columns`. For a table with roles, a role's column absent from the header row gives `roles.<role>`, and a header row differing from `columns`, order included, gives `columns`.
42. The other normalisations (`docs/DESIGN.md`, "Three kinds of record, one rule each"; D-005's "Notes on values"): a brief's `name` is read by `parse_review_name` and compared with `id` and `round`, which gives `id` or `round`; `scope` entries are compared exactly, a folder's `/` never added or removed on either side; `parallel` prose `yes` against `true`, `no` against `false`, an absent line against `false`; `title` against the heading's title, a stage's `name` against its heading; a stage's `demonstration` against the presence of a `Demonstration:` line with text, `None`, `""` and whitespace-only being absent.
43. `historic` has no prose line and is compared with its derivation: true exactly where the fallback has no `scope` line, no `kind` line and the ID is in `merged`. An increment or a stage standing on only one side is a non-empty result, in a form you choose and state in your report.
44. A fallback's shape, per kind: project-status `{phase, workflows (already the structured list), awaiting_user_on (the prose), bridge_version, stage, open_issues}`; brief `{name (the file's stem, read by parse_review_name for id and round), satisfies, scope, merge_unit, blocking_class}`; build-plan `{merged (a set, or None where it could not be read), stages: [{name, demonstration (the line's text or None), increments: [{id, title, fields: {kind, parent, depends_on, parallel, diagrams, scope, satisfies, deferred}}]}]}`, list fields already lists or the filler `none` in any case; requirements, diagram-index and deviations `{header_row}`; inventory `{reflected_through, development_data, sections: {<section>: <its header row>}}`; run-parameters the same keys as its header, bar `record` and `header`.

**The fixtures, the prose and the release files**

45. `tests/fixtures/headers/` holds `.md` files with invented content: one valid header per kind and one file whose name holds `forms`. They stay as they are unless the character rule touches one; today none holds a refused character. A fixture you change keeps its first line `---` and a line ending after its closing `---`, and stays non-empty.
46. Your own cases go below the marker in `tests/test_header_reader.py`, each named `test_r057_...`, following the file's own convention for a non-ASCII character (`chr()`, never typed).
47. A program's prose (a docstring, a comment, a help text) never quotes a retired pattern (KP-073; `bridge/cursor-bridge/Known-Pitfalls.md`): the enumerated list stands in `docs/DESIGN.md`, "The fallback readers, one copy each", "The retired readings, enumerated". What you write in `bridge_env.py` describes the rule in its own words. `bridge_env.py` stays ASCII-only: a non-ASCII character your code has to name is written as a Python escape sequence in the source, as `plan_increment_ids` does in its heading pattern.
48. `MANIFEST.json` is regenerated this way, after your last edit of anything under `bridge/`, from the Workspace root: `python tools/make-manifest.py`. It takes the version from the newest `## <version>` entry of `bridge/cursor-bridge/CHANGELOG.md` (`2026.11.03a`, today's `VERSION`), rewrites `bridge/cursor-bridge/VERSION` and rewrites `MANIFEST.json`. `VERSION`'s content must not change: if it does, stop and report it. Git may warn that LF in `VERSION` will become CRLF; that is not a change. If your final `git status --short` lists `VERSION`, as round 1's did, read the file, state in your report that it still reads `2026.11.03a`, and leave it for the supervisor.
49. No command is added or changed and no dependency is added. `yaml` is imported by no program: it is imported by the tests only.

## Acceptance criteria
- [ ] `python -m pytest tests/test_header_schemas.py tests/test_header_reader.py -q -p no:cacheprovider` passes, every test in both, or a failing fixed test carries your written objection in the report.
- [ ] `git diff -- tests/test_header_schemas.py` is empty, and `git diff -- tests/test_header_reader.py` changes only lines below the marker line.
- [ ] `git diff -- bridge/cursor-bridge/bridge_env.py` changes nothing above the line `# --- R-057 header reader, schemas, check and agreement (TASK-046) ---` and nothing in `HEADER_SCHEMAS`, and `bridge_env.py` holds no non-ASCII character.
- [ ] The named cause is addressed at its mechanism: no structural judgment reads a quoted string or a comment, no Unicode space counts as whitespace, every line's column is held to its container's, and nothing in group J remains.
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
- A value the brief marks as **the owner's** (a threshold, a price, a limit, a default, a wording) is fixed: the Context section names the test that pins it; do not change the value or that test, and report it if the work seems to need a change (rule 52). This brief marks none; the bounds (262,144 bytes, eight levels) and the schemas are the design's and the diagram's, and are fixed the same way.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only, and `git rev-parse HEAD`, which the Done section names.
- Numbers from text are parsed with the language's own parser (`int`), never by slicing or splitting a string. The one number this reader reads is a decimal integer: no sign, no point, `0` or no leading zero, no unit at the reader; its range is what `int` accepts, and one it refuses is a `HeaderError` at its line whose message says integer. (Three defects in one project came from numbers read by hand.)
- This increment starts no process other than the tests and the checks named in Done, and adds no new kind of process.
- Every verification command the Done section asks you to run is written there in full, with its options and its working folder, so you run exactly it. You do NOT run the full suite this round: the supervisor runs it through the launcher. You write no hand-mutation table this round, and round 1's table is not repeated: the supervisor's mutants file follows this round. No script of a mutation lands in the diff.
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

Your report is the file `handoff/TASK-046-r2-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, one sentence stating how the change addresses the named cause, a line naming the host version (Claude Code 2.1.317, as Context says), the forms you chose for Requirements 26 and 43, any objection to a fixed test, and, as its last section, a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run; the full suite is one of those this round. Write the report's results after the commands above, naming the commit their counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
