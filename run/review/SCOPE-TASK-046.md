# SCOPE — TASK-046 (release B2's header reader), Review B round 1

Where the increment ends: the header reader, the schemas, the check and the agreement in `bridge/cursor-bridge/bridge_env.py`, from the line `# --- R-057 header reader, schemas, check and agreement (TASK-046) ---` to the end of the file, with `MANIFEST.json`'s hash. No program reads a header in this increment; the programs adopt the reader from TASK-047 on, the migration is TASK-054. Design for those later increments is not this diff's defect.

## The brief's Scope, quoted (handoff/TASK-046-r3.md, round 3; rounds 1 and 2 had the same files)

Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_header_reader.py
- tests/test_header_schemas.py
- tests/fixtures/headers/
- docs/BUILDER_NOTES.md
- handoff/TASK-046-r3-report.md

Do not modify anything else. `tests/test_header_reader.py` changes only below the marker line (see Context). `tests/test_header_schemas.py` is a fixed point: read it, change nothing in it. `MANIFEST.json` changes only by running its generator (the last brief's Requirement 48), never by hand.

## The brief's Out of scope, quoted

- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names; in particular `handoff/TASK-046.md`, `handoff/TASK-046-r2.md` and `handoff/TASK-046-r2-report.md` (never revised), `docs/REQUIREMENTS.md`, `docs/BUILD_PLAN.md`, `docs/DESIGN.md`, `docs/INVENTORY.md`, `docs/PROJECT_STATUS.md` and every file under `docs/diagrams/`, which are the supervisor's records
- `bridge/cursor-bridge/VERSION` (its content stays `2026.11.03a`) and `bridge/cursor-bridge/CHANGELOG.md`
- every program under `bridge/cursor-bridge/` other than `bridge_env.py`: no program changes its reading in this increment, and no fallback reader moves
- every line of `bridge_env.py` above the line `# --- R-057 header reader, schemas, check and agreement (TASK-046) ---`: every existing function, constant and pattern stays byte-identical
- `HEADER_SCHEMAS`: its 19 tables were checked equal to D-005, key by key, order and type, by the reviewer, and do not change
- every other test file, and every line of `tests/test_header_reader.py` above the marker
- adding a header to any record of this repository

## The threat model

None is recorded in `docs/INVENTORY.md`'s Decisions for `bridge_env.py`'s new header code, so the five blocking classes stand unbounded. The records the reader will read can be written by a builder or a reviewer, so untrusted input reaches it once the programs adopt it: a security finding is judged by whether such input can reach it.

## The rounds and the ceiling

The review guard has counted 0 rounds for TASK-046; this snapshot, `TASK-046-r1`, opens round 1. The launcher has counted 3 builder rounds (2026-11-04T18:24:08Z, T20:13:07Z, T21:23:28Z), so a fix needing a fourth builder round needs a `Blocking class:` line: grade every finding by the five blocking classes first (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test). This round carries no `Blocking class:` line.

## The tests the supervisor wrote, and the paragraph each enforces

The tests are the supervisor's, written before the builder's first round, not the builder's: `tests/test_header_reader.py` (above its marker line; below it stand the builder's cases, two of them edited by the supervisor for Requirement 13 of the round-3 brief) and `tests/test_header_schemas.py` (a fixed point). Each test carries the paragraph it enforces in its docstring or a comment (`enforces: <document> <section>`): `docs/DESIGN.md`, Change: release B2, "The reader"; D-005 under `docs/diagrams/`; the requirement R-057 in `docs/REQUIREMENTS.md`; the numbered requirements of `handoff/TASK-046.md`, `-r2.md` and `-r3.md`; and the rulings of rounds 1 and 2 recorded in DESIGN, D-005's notes, INVENTORY's reader row and `docs/DESIGN_CRITIQUE.md` "After the gate". The supervisor's commits of tests: 27d321f, 4d98b93, ae2961c, bd1225a, c5dc909, 42b9e19 and 40b0050. (The branch's history was rewritten before its first push to redact a computer path in two builder reports; the briefs and reports cite some old ids, which `docs/HARDENING.md`, TASK-046's section, maps to the new ones.)

The new tests were run against the checkpoint fed9aad (`mutation-run.py --checkpoint`): of 859, 847 failing on old code, none passing, and 12 not run. The 12 are parametrized ids holding escape characters that do not pass as a node id (for example `test_r057_only_the_exact_marker_opens_a_header[----\na: b\n----\n]` and the `test_r057_r2_outside_a_string_or_a_comment_only_ascii_is_read` cases); their bodies call the reader as their neighbours do.

## The mutants and the driver

`run/supervisor/TASK-046-mutants.json`, written by the supervisor's driver `run/supervisor/task046_mutants_make.py` (not in this diff; gitignored working files), whose docstring states the operator set by each id's first letter: K a key dropped from a schema, T a type widened (t02 narrows one), R a refusal removed, C a comparison inverted (c35 and c36 invert a word and a default), B a bound raised (b05 counts the bound in characters), H a retired reading restored. 149 mutants: 131 expected killed on a named set of failing tests, 18 `expect: survive`, each with its equivalence reason. The mutation run (`run/agent/TASK-046-mutation.out`): "counts: run=149 cached=0 killed=131 survived=0 not applied=0 error=0 expected survive=18", exit 0.

## Bookkeeping and record files in the diff that are expected

- `handoff/TASK-046.md`, `handoff/TASK-046-r2.md`, `handoff/TASK-046-r3.md` (the briefs) and the builder's reports `handoff/TASK-046-r1-report.md`, `handoff/TASK-046-r2-report.md`, `handoff/TASK-046-r3-report.md` (one computer path in the last one's line 75 redacted by the supervisor before its commit, rule 54)
- the supervisor's records: `docs/DESIGN.md`, `docs/DESIGN_CRITIQUE.md`, `docs/INVENTORY.md`, `docs/BUILD_PLAN.md` (the plan's `Scope:` lines), `docs/diagrams/` (D-005's notes), `docs/HARDENING.md` (TASK-046's section), `docs/PROJECT_STATUS.md` (as at this pull request's merge, #137)
- `run/review/` (this file, the round's diff and its assumptions file)
- `tests/fixtures/headers/` (nine fixture records, one per kind and one of header forms, the supervisor's)

## Already recorded, not new

`docs/HARDENING.md`, TASK-046's section: Requirement 1's shape (three quote walkers that agree), Requirement 12's dead code, the redundancy the mutants show, the empty block at the end of a text refused (fails closed), the security audit's two advisories (roles compared by presence, not by column; Unicode format characters accepted inside strings and comments, as pyyaml does), the report's wrong words.
