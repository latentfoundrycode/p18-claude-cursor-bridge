# SCOPE for TASK-084 (Review B, round 1)

TASK-084 is the launcher's refusal of a merge unit of one increment (R-105, the field finding F7). Before any run of a builder brief, the launcher refuses with exit 125 a brief that names a merge unit of one increment and no unit of two or more: its prose holds a line, read as the prose reader reads it, of the words `Merge unit:` followed by exactly one word of the pattern's ID form and nothing else, or its header's `merge_unit` is a list of exactly one entry, while neither side names two or more as written. The refusal reads `bridge-run: refused - brief rule: a merge unit names two or more increments; a brief of one increment carries no Merge unit: line and merge_unit: null in its header`, then the side that named the one, `(the line)`, `(the header)` or `(the line and the header)`, then the pointer every brief-rule refusal carries. Its place: the launcher asks `bridge_env.brief_header_refusal` first with the keys `id`, `round`, `satisfies` and `scope`, then applies the rule, then asks the function whole. A unit of one is not made valid, and no reader of a brief changes what it returns.

The branch is task-084, from main 7443257 (PR #169's merge, TASK-062). There were two builder rounds. This is the review guard's first round for TASK-084, below the code gate's ceiling, so there is no Blocking class line.

Where the increment ends:
- `bridge/cursor-bridge/bridge-run.py`: in `builder_review_refusal`, the keys-filtered header call, the rule, then the whole header call (round 1's lines; round 2 left the file unchanged).
- `bridge/cursor-bridge/bridge_env.py`: the constants `MERGE_UNIT_ID_FORM` and `MERGE_UNIT_BULLET_CLASS`; `MERGE_UNIT_RE` composed of them, its text unchanged; the rule's pattern `MERGE_UNIT_ONE_LINE_RE`, which has two alternatives after the colon (one word of the ID form then the end of the line, or two or more words); and the one new function `brief_merge_unit_one_side`, the launcher its one caller.
- `MANIFEST.json`, regenerated.
- `tests/test_program_merge_unit_one.py`, the supervisor's.
- The records.

The reviews' leads (HARDENING, TASK-084, leads 1 to 6) are recorded; they are not defects of this diff. Among them:
- `MERGE_UNIT_RE`'s quadratic backtracking, on the checkpoint's code, its text held frozen;
- the unread forms of the line (lower case, commas, words after the IDs), kept so by the design's non-goals;
- a line naming one ID twice, beside a header listing it twice, passing the rule as written;
- `_git_resolved_path`'s stale docstring (TASK-062's lead 1), not in this brief, carried to TASK-065.

Read the commit messages (git log, the full bodies) for the quoted lines. The branch's assumption lists are in run/review/ASSUMPTIONS-TASK-084-r1.md.

## Out of scope (the briefs, in short)
- `.env`, `secrets/` and CI configuration.
- Every reader of a brief: `MERGE_UNIT_RE`'s text, `_merge_unit_from_prose`, `_merge_unit_from_header`, `merge_unit_ids`, `merge_unit_line_present`, `read_brief_record`, `header_agrees` and `brief_header_refusal`, none edited.
- Every other program under `bridge/` (`review-guard.py`, `records-migrate.py`, `plan-check.py` and `scope-check.py` included), `tools/`, `CHANGELOG.md` and `VERSION`.
- Every other test file. `tests/test_header_plan.py` is unedited and green.
- No option, environment variable, dependency, log field, module docstring or header schema change.
- The packager's clause in `agents/spec-packager.md` is TASK-082's.

## The threat model
`docs/INVENTORY.md`, Decisions, "The bridge's threat model as a whole". Outside input is what the builder and the reviewers write, and a brief in the checkout counts as outside input once an agent has worked there (D-004). The agents run as the owner's Windows user, so the boundary is what the programs refuse, check and record. For this diff: the change adds a refusal and removes none, and no brief the checkpoint refused may now be launched. The rule reads the brief's text and its parsed header alone, by a pattern over one line that repeats no group and by a list's length.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-084)
Scope: bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/bridge_env.py; bridge/cursor-bridge/MANIFEST.json; tests/test_program_merge_unit_one.py; docs/BUILDER_NOTES.md; handoff/TASK-084-r<N>-report.md
Satisfies: R-105
Done when: see docs/BUILD_PLAN.md, TASK-084, the Done when line, read whole. In short: the rule's refusal, its text and its side; its place in the order of the header's refusals, `brief_header_refusal` not edited; the three cases of the design, each red on the checkpoint by node id and each asserting its side; the disagreements kept; the forms that pass; one function, the launcher its caller; the ID form and the bullet mark as two named constants, `MERGE_UNIT_RE` and the rule's pattern both composed of them (ISS-021), held by a pattern-text test and a walk over the module's `re.compile` calls; the readers unchanged, held by a comparison with the values the supervisor recorded on the checkpoint; the mutants file sweeping the rule, every mutant killed; HARDENING's lead on the other forms of the line, and R-059's clause; MANIFEST regenerated; no option added; no new dependency.

## The supervisor's tests, each with the clause it enforces
- `tests/test_program_merge_unit_one.py` names R-105. It was committed at the checkpoint 070b307, where it was red: 14 failed, 44 passed. The 14 are the 13 refusal cases of the rule and the walk. It covers:
  - the three cases of the design, each with its side;
  - the other refused forms: a line and a header naming one ID each, not the same; a word not of the ID form beside a header listing one; no white space after the colon; white space after the ID; the field's case beside a sentence holding the words mid-line; the word None; the bulleted forms;
  - the disagreements kept: two beside one, one beside two, a second word not of the ID form, a second ID the readers reject (in the line and in the header);
  - the forms that pass: a word not of the ID form beside null; units of two and three; a unit of two with no space after the colon; no line; an empty line; a placeholder;
  - the order of the header's refusals: scope first; a malformed header and a schema-breaking one keep their lines; a line of one beside null with a disagreeing blocking_class is told of the unit;
  - `MERGE_UNIT_RE`'s text;
  - the walk: exactly two compile calls holding the words, both composed of the two constants;
  - the six readers' values on every brief, held to the values recorded on the checkpoint.
- Two cases were added after round 1's builder (d075d5f): a tab after the bullet, refused for the line; and a tab-bulleted line of two beside a header of one, which keeps the disagreement. The second was red on round 1's code. Against 070b307, all 15 new tests fail on the old code (`mutation-run.py --checkpoint`).

## The mutants
`run/supervisor/TASK-084-mutants.json`: 15 mutants over the acceptance file.
`counts: run=15 cached=0 killed=15 survived=0 not applied=0 error=0 expected survive=0`

## Evidence
- Review A: round 1 REJECT (the one-space bullet; a second function; the bullet class written again), round 2 APPROVE on the whole increment; its re-read of the records REJECT on records only (lead 3's first example misread, lead 2's qualifier, lead 6's wording), fixed in the commit after the records, and its confirming read.
- Security audit: round 1 PASS (advisories), round 2 PASS (the pattern linear).
- Own run on round 2: 219 passed.
- Whole suite on round 2's code: 5403 passed, 43 skipped.

## Expected bookkeeping and records in the diff
- `handoff/TASK-084.md` and `handoff/TASK-084-r2.md`, with their reports.
- `docs/HARDENING.md`.
- `docs/REQUIREMENTS.md`: R-059's clause. R-105 stays planned until TASK-082 writes the packager's clause.
- `docs/PROJECT_STATUS.md`, as at PR #170's merge.
- `run/review/` (these files).
- No `docs/CHANGES.md` entry: nothing was taken beyond the plan.
