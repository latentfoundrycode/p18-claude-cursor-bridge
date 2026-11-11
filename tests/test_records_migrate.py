"""TASK-051, the supervisor's acceptance tests (R-062; D-002): records-migrate.py, the migration that writes each
dual-read record's header from bridge_env's fallback reading of its prose, atomically, and lists what it wrote,
what has a header already, what it cannot read and what it cannot write.

enforces: docs/BUILD_PLAN.md, TASK-051's Done when; docs/DESIGN.md, "Change: release B2", "Writing" (the
migration), "The reader" (the subset the migration writes, `yaml.safe_load` reading it the same) and "Header first;
fallback; malformed"; R-062.

The oracle is bridge_env and nothing else: every written header is read back with `read_header`, checked with
`check_header` and compared with `header_agrees(kind, header, <the kind's fallback of the original text>)`, the
fallback being `status_fallback`, `plan_prose_fallback`, `brief_prose_fallback`, `inventory_fallback`,
`register_fallback`, `diagram_index_fallback`, `deviations_fallback` or `run_parameters_fallback` over the original
bytes decoded by `decode_record_bytes`; the merged set of the `historic` case is `squash_merged_ids`'.

The interface these tests assume, which the brief repeats:
- `python bridge/cursor-bridge/records-migrate.py [--check] [--base <ref>] [<project root>|<record>...]`, run with
  the project as the current folder; nothing given is the current folder as the root; one folder given is the root,
  a second folder exits 2; given record paths are taken alone, in the order given.
- in process: the module loaded from its path with `importlib.util.spec_from_file_location` exposes `build_parser()`
  at top level (an `argparse.ArgumentParser` with `--check` and `--base`) and `main(argv)`, `argv` a list of strings
  without the program's name, returning the exit code as an int (a `SystemExit` is tolerated and read as the code).
- each write: the whole new file written to a temporary file opened with the built-in `open()` (or `io.open`, the
  same function; `tempfile` and `os.fdopen` reach it too) in the record's own folder, read back through
  `bridge_env.read_header`, `bridge_env.check_header` and `bridge_env.header_agrees`, then moved into place with
  `os.replace(<temporary>, <record>)`, called as `os.replace` so a test can replace it; a read-back that fails exits 3
  and leaves the record untouched, the run stopping there.
- lines printed, one per enumerated record: `would write <path>` (with `--check`), `has a header <path>`,
  `cannot read <path>: <reason>` (`not a record kind`; `merged set unreadable (<reason>)`; `unbalanced parenthesis
  in <id>'s Scope`; a brief's Scope refusal), `cannot write <path>: <n> characters with the header, over the older
  cap; trim the body first` or `cannot write <path>: <n> lines ...`; a malformed header `HEADER MALFORMED: <path>...`
  (exit 2, the run stopping at that record). `<path>` may be shown relative to the root or as given or absolute: the
  tests accept any form whose tail, with backslashes read as slashes, is the record's path relative to the root.
  The line a real write prints is not pinned beyond naming the record's path.
- exits: `--check` 1 where any record would be written or cannot be written, else 0; the run 1 where a `cannot
  write` stands, else 0; a `cannot read` line never changes either; 2 for a malformed header, a second folder or a
  `--base` beginning with `-`; 3 for a failed read-back.

The supervisor's cases stand above the marker at the end of this file. The builder adds its own cases below the
marker and edits nothing above it.
"""
import argparse
import builtins
import errno
import importlib.util
import io
import os
import re
import subprocess
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

PROGRAM = os.path.join(BRIDGE, "records-migrate.py")
DASH = "—"
ARROW = "→"
PREFIXES = ("would write ", "has a header ", "cannot read ", "cannot write ")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def git_env():
    return dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
                GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def migrate(cwd, *args):
    """Run records-migrate.py from cwd; (exit code, stdout and stderr)."""
    assert os.path.isfile(PROGRAM), "bridge/cursor-bridge/records-migrate.py is missing (TASK-051)"
    p = subprocess.run([sys.executable, PROGRAM] + [str(a) for a in args], cwd=str(cwd), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=git_env(), timeout=120,
                       creationflags=NO_WINDOW)
    return p.returncode, p.stdout + p.stderr


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=git_env(),
                       timeout=120, creationflags=NO_WINDOW)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def same_path(shown, rel):
    s = shown.strip().strip("`'\"").replace("\\", "/")
    return s == rel or s.endswith("/" + rel)


def listed(out, prefix, rel):
    """The reasons (or "" for a line without one) of every `<prefix><path>` line naming rel."""
    hits = []
    for line in out.splitlines():
        if not line.startswith(prefix):
            continue
        rest = line[len(prefix):]
        if prefix.startswith("cannot"):
            cut = rest.find(": ")
            if cut < 0:
                continue
            path, reason = rest[:cut], rest[cut + 2:]
        else:
            path, reason = rest, ""
        if same_path(path, rel):
            hits.append(reason)
    return hits


def every_listing(out, rel):
    """Every (prefix, reason) line of the four kinds that names rel."""
    return [(p, r) for p in PREFIXES for r in listed(out, p, rel)]


def snapshot(root):
    out = {}
    for dirpath, dirs, files in os.walk(str(root)):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            path = os.path.join(dirpath, name)
            with open(path, "rb") as f:
                out[os.path.relpath(path, str(root)).replace("\\", "/")] = f.read()
    return out


# ---------------------------------------------------------------- the records, in their present header-less shapes

STATUS = """# Project Status
Last updated: 2026-11-11
Phase: changing
Workflows: Host Extension Development {arrow} Claude Code Extension; traits: Installable
Change cycle: release B2 (machine-readable headers), begun 2026-11-04
Stage: H2 {dash} the migration
Increment: TASK-051
Awaiting user on: nothing
Bridge version: 2026.11.09a (installed 2026-11-09)
Open issues: ISS-023: a report read as a brief; ISS-024 (two parts; one fix).
Next: TASK-052 to TASK-054 as plan-check.py gives them.

## Layout
- bridge/ {dash} the sources
---
A Markdown rule above, which is body.
""".format(arrow=ARROW, dash=DASH)

PLAN = """# Build plan {dash} Example

Intro prose. The increments follow.

## Standing constraints (every increment)
- no new dependency.

## Stage A1 {dash} the parser
Demonstration: the parser reads a file.

### TASK-001 {dash} the reader
Author: builder
Parent: none
Depends on: none
Parallel: no
Diagrams: D-002
Scope: src/reader.py; tests/test_reader.py
Satisfies: R-001, R-002
Done when: the reader reads.

### TASK-002 {dash} the writer
Kind: increment
Depends on: TASK-001
Parallel: yes
Scope: src/writer.py; src/out/
Satisfies: R-003
Deferred: until the owner says (2026-12-01)

## Stage A2 {dash} the export

### TASK-003: the export
Depends on: TASK-001, TASK-002
Diagrams: none
Scope: src/export.py
Satisfies: R-004
""".format(dash=DASH)

ADDENDUM = """# Build plan addendum {dash} release B2 (2026-11-04)

## Stage H1 {dash} the headers
Demonstration: the headers are read first.

### TASK-010 {dash} headers
Depends on: TASK-003
Parallel: no
Diagrams: D-002, D-005
Scope: bridge/a.py; tests/test_a.py
Satisfies: R-010
""".format(dash=DASH)

BRIEF = """# TASK-007: the writer (R-007)

## Objective
Build the writer.

Satisfies: R-007 - the writer writes each record.

## Scope
Files you may modify:
- src/writer.py
- tests/test_writer.py
- docs/

Limits on these files:
- none beyond this brief.

## Out of scope
- .env and anything under secrets/
"""

BRIEF_R3 = """# TASK-007 round 3: the writer, round 2's findings fixed (R-062)

## Objective
Fix the two confirmed causes.

Satisfies: R-062, R-062 - the migration (the ID named twice, kept twice).

Merge unit: TASK-007 TASK-008

Blocking class: data integrity - a record half-written

## Scope
Files you may modify:
- src/writer.py
- tests/test_writer.py

## Out of scope
- everything else
"""

INVENTORY = """# Inventory {dash} Example
Reflected through: none

What the project holds.

## Features
| Feature | What it does | Where | Tests | Since |
|---|---|---|---|---|
| Reader | reads a record | `src/reader.py` | tests/test_reader.py | TASK-001 |

## Resources
| Name | Kind | Where it lives | Used by | Provided |
|---|---|---|---|---|
| pyyaml | library | requirements.lock | tests | owner |

## Decisions
| Decision | Reason | Settled | Revisit only if |
|---|---|---|---|
| Development data: the dev build is the sources under `src/` | never load half-edited code | 2026-10-11, owner | {dash} |

## Deferred
| Item | Why deferred | Since | Owner decision needed |
|---|---|---|---|
| Export to PDF | later | 2026-10-11 | yes |
""".format(dash=DASH)

REQUIREMENTS = """# Requirements {dash} Example

The register.

| ID | Requirement | Source | Status | Evidence |
|---|---|---|---|---|
| R-001 | The reader reads. | owner | built | tests/test_reader.py |
| R-002 | The writer writes. | owner | planned | {dash} |
""".format(dash=DASH)

INDEX = """# Diagram index

The normative diagrams.

| ID | Level | Kind | Status | File | Refines | Realizes | Enforced by | Why |
|---|---|---|---|---|---|---|---|---|
| D-001 | 1 | use-case | approved | D-001-use-cases.md | {dash} | R-001 | tests/test_reader.py | the context |
""".format(dash=DASH)

DEVIATIONS = """# Known deviations

One open.

| Diagram | From | To | As built | Since | Resolved by |
|---|---|---|---|---|---|
| D-002 | reader | writer | a direct call | TASK-002 | {dash} |
""".format(dash=DASH)

RUN_PARAMETERS = """# Run parameters
Set: 2026-10-11   (owner may change any of these at any time by saying so; update this file)
Stage pause: run
Merge authority: supervisor   (owner's instruction 2026-10-12)
Refactoring pass: on
Installer verification: n/a (host extension)
Parallel increments: off
Agent ceiling: 2400
Ceiling above twice: builder 28800 (the owner said "take the night")
Design rounds above five: pace 7 (owner: seven rounds, 2026-11-04)
Review rounds above the ceiling: TASK-046 4 (the owner's word, 2026-11-05)
"""


def b(text, crlf=False):
    if crlf:
        text = text.replace("\n", "\r\n")
    return text.encode("utf-8")


# rel path -> (kind, original bytes); the register carries CRLF line endings, the rest LF.
FIXTURES = {
    "docs/PROJECT_STATUS.md": ("project-status", b(STATUS)),
    "docs/BUILD_PLAN.md": ("build-plan", b(PLAN)),
    "docs/BUILD_PLAN-2026-11-04.md": ("build-plan", b(ADDENDUM)),
    "handoff/TASK-007.md": ("brief", b(BRIEF)),
    "handoff/TASK-007-r3.md": ("brief", b(BRIEF_R3)),
    "docs/INVENTORY.md": ("inventory", b(INVENTORY)),
    "docs/REQUIREMENTS.md": ("requirements", b(REQUIREMENTS, crlf=True)),
    "docs/diagrams/INDEX.md": ("diagram-index", b(INDEX)),
    "docs/diagrams/DEVIATIONS.md": ("deviations", b(DEVIATIONS)),
    "docs/RUN_PARAMETERS.md": ("run-parameters", b(RUN_PARAMETERS)),
}

# Files under handoff/ that are not briefs: never listed, never written.
NOT_BRIEFS = {
    "handoff/TASK-007-report.md": b("# TASK-007 report\n\n## Scope\n- src/writer.py\n\nSatisfies: R-007\n"),
    "handoff/TASK-007-r2-report.md": b("# TASK-007 round 2 report\n\n## Scope\n- src/writer.py\n"),
    "handoff/RESOLUTION-x.md": b("# Resolution x\n\n## Scope\n- src/writer.py\n"),
}

# A well-formed header written by hand above the register (checked by bridge_env when this file was written).
HEADED_REQUIREMENTS = b("""---
record: requirements
header: 1
columns: [ID, Requirement, Source, Status, Evidence]
roles:
  id: ID
  status: Status
  evidence: Evidence
statuses: [planned, built, deferred, dropped]
---
""" + REQUIREMENTS)

ELLIPSIS_BRIEF = b("""# TASK-020: an old brief

Satisfies: R-020 - something old.

## Scope
- src/...
- tests/test_old.py

## Out of scope
- everything else
""")

EMPTY_SCOPE_BRIEF = b("""# TASK-021: a brief with an empty Scope

Satisfies: R-021 - something.

## Scope

## Out of scope
- everything
""")

UNBALANCED_PLAN = b("""# Build plan

## Stage A1 {dash} the parser
Demonstration: it parses.

### TASK-001 {dash} the reader
Depends on: none
Scope: src/reader.py (the reader; its tests); tests/test_reader.py
Satisfies: R-001
""".format(dash=DASH))


def status_over_chars():
    """A status file whose body fits 12,000 characters and whose header pushes it over."""
    text = STATUS
    n = 0
    while len(text) + 201 < 11900:
        n += 1
        text += "Note %03d: %s\n" % (n, "x" * 190)
    assert len(text) < 12000 and text.count("\n") < 100
    return b(text)


def status_over_lines():
    """A status file of 112 short lines: within 120 lines alone, over it with any header."""
    text = STATUS
    n = 0
    while text.count("\n") < 112:
        n += 1
        text += "- item %03d\n" % n
    assert text.count("\n") == 112 and len(text) < 4000
    return b(text)


def write(root, rel, data):
    path = os.path.join(str(root), *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return path


def read(root, rel):
    with open(os.path.join(str(root), *rel.split("/")), "rb") as f:
        return f.read()


def project(tmp_path, files, name="proj"):
    """A project folder holding the named fixtures (a rel from FIXTURES or NOT_BRIEFS, or a (rel, bytes) pair)."""
    root = tmp_path / name
    root.mkdir()
    for item in files:
        if isinstance(item, tuple):
            write(root, item[0], item[1])
        elif item in FIXTURES:
            write(root, item, FIXTURES[item][1])
        else:
            write(root, item, NOT_BRIEFS[item])
    return root


# ---------------------------------------------------------------- the oracle: bridge_env's own reading

def fallback_of(kind, rel, original, merged=None):
    text = bridge_env.decode_record_bytes(original)
    if kind == "project-status":
        return bridge_env.status_fallback(text)
    if kind == "build-plan":
        return bridge_env.plan_prose_fallback(text, merged)
    if kind == "brief":
        return bridge_env.brief_prose_fallback(text, os.path.splitext(os.path.basename(rel))[0])
    if kind == "inventory":
        return bridge_env.inventory_fallback(text)
    if kind == "requirements":
        return bridge_env.register_fallback(text)
    if kind == "diagram-index":
        return bridge_env.diagram_index_fallback(text)
    if kind == "deviations":
        return bridge_env.deviations_fallback(text)
    if kind == "run-parameters":
        return bridge_env.run_parameters_fallback(text)
    raise AssertionError(kind)


def schema_order(table_name, value, where="header"):
    """Places where a mapping's keys are not in its schema's order (the subset writes them in that order)."""
    table = bridge_env.HEADER_SCHEMAS[table_name]
    out = []
    if list(value.keys()) != list(table.keys()):
        out.append("%s: %s" % (where, list(value.keys())))
    for key, type_str in table.items():
        spec = type_str.replace(" or null", "")
        child = value.get(key)
        if spec.startswith("list of ") and spec[len("list of "):] in bridge_env.HEADER_SCHEMAS:
            for i, item in enumerate(child or []):
                if isinstance(item, dict):
                    out += schema_order(spec[len("list of "):], item, "%s.%s[%d]" % (where, key, i))
        elif spec in bridge_env.HEADER_SCHEMAS and isinstance(child, dict):
            out += schema_order(spec, child, "%s.%s" % (where, key))
    return out


def header_part(new, original):
    assert new.endswith(original) and len(new) > len(original), "the original bytes are not kept below the header"
    return new[:len(new) - len(original)]


def yaml_block(head):
    """The text between the opening and the closing `---` lines of the written header."""
    lines = head.decode("utf-8").split("\n")
    assert lines[0].rstrip("\r") == "---" and lines[-1] == "" and lines[-2].rstrip("\r") == "---", head[:200]
    return "\n".join(lines[1:-2]) + "\n"


def assert_migrated(kind, rel, original, new, merged=None):
    """The written record: a header the reader reads, the schema accepts, the fallback agrees with and
    yaml.safe_load reads the same; the original bytes below it unchanged, the file's own line endings kept."""
    assert new.startswith(b"---"), "%s was not given a header: %r" % (rel, new[:80])
    head = header_part(new, original)
    if b"\r\n" in original:
        assert re.search(rb"(?<!\r)\n", head) is None, "the CRLF file's header has a bare LF line ending"
        assert head.endswith(b"\r\n---\r\n")
    else:
        assert b"\r" not in head, "the LF file's header has a CR"
        assert head.endswith(b"\n---\n")
    text = new.decode("utf-8")
    header, body = bridge_env.read_header(text)
    assert header is not None
    assert body == original.decode("utf-8"), "the body below the header changed"
    assert bridge_env.check_header(kind, header) == []
    assert bridge_env.header_agrees(kind, header, fallback_of(kind, rel, original, merged)) == []
    assert schema_order(kind, header) == []
    if header != {}:  # DESIGN.md: the one exception, a block read as empty (pyyaml reads null)
        assert yaml.safe_load(yaml_block(head)) == header
    return header, head.decode("utf-8")


# ---------------------------------------------------------------- per kind: the migration, the read-back, idempotence

@pytest.mark.parametrize("rel", list(FIXTURES), ids=[r.replace("/", "_") for r in FIXTURES])
def test_r062_each_kind_is_migrated_to_the_fallbacks_reading(tmp_path, rel):
    """Done when: a record whose first line is not `---` gets the header from bridge_env's fallback reading of its
    prose, in the subset (keys in the schema's order), read back by read_header, accepted by check_header, agreeing
    with header_agrees, read the same by yaml.safe_load; nothing below it changed, its line endings (CRLF for the
    register) kept; a plan file whose increments all carry a Scope migrates with no git history (the merged set is
    read lazily)."""
    kind, original = FIXTURES[rel]
    root = project(tmp_path, [rel])
    code, out = migrate(root)
    assert code == 0, out
    assert_migrated(kind, rel, original, read(root, rel))


@pytest.mark.parametrize("rel", list(FIXTURES), ids=[r.replace("/", "_") for r in FIXTURES])
def test_r062_a_second_run_changes_no_byte_and_lists_has_a_header(tmp_path, rel):
    """Done when: a record with a header is left unchanged (`has a header <path>`), so a second run is a no-op,
    with and without --check."""
    root = project(tmp_path, [rel])
    code, out = migrate(root)
    assert code == 0, out
    first = snapshot(root)
    code, out = migrate(root)
    assert code == 0, out
    assert snapshot(root) == first
    assert listed(out, "has a header ", rel) == [""], out
    code, out = migrate(root, "--check")
    assert code == 0, out
    assert snapshot(root) == first
    assert listed(out, "has a header ", rel) == [""], out


# ---------------------------------------------------------------- the brief's id, round and satisfies

@pytest.mark.parametrize("rel,want_id,want_round", [("handoff/TASK-007.md", "TASK-007", 1),
                                                    ("handoff/TASK-007-r3.md", "TASK-007", 3)])
def test_r062_a_briefs_id_and_round_come_from_its_file_name(tmp_path, rel, want_id, want_round):
    """Done when: a brief's `id` and `round` from its file name by parse_review_name, `round` an integer, 1 for a
    plain name."""
    root = project(tmp_path, [rel])
    code, out = migrate(root)
    assert code == 0, out
    header, head = assert_migrated("brief", rel, FIXTURES[rel][1], read(root, rel))
    assert header["id"] == want_id
    assert type(header["round"]) is int and header["round"] == want_round
    assert re.search(r"(?m)^round: %d$" % want_round, head), head


def test_r062_a_satisfies_id_named_twice_is_kept_twice_in_order(tmp_path):
    """The supervisor's ruling for TASK-051: the migration writes the fallback's reading exactly, so a brief whose
    `Satisfies:` line names an ID twice keeps both, in order, and the read-back agrees; the merge unit and the
    blocking class are written from their lines too."""
    rel = "handoff/TASK-007-r3.md"
    root = project(tmp_path, [rel])
    code, out = migrate(root)
    assert code == 0, out
    header, _head = assert_migrated("brief", rel, FIXTURES[rel][1], read(root, rel))
    assert header["satisfies"] == ["R-062", "R-062"]
    assert header["merge_unit"] == ["TASK-007", "TASK-008"]
    assert header["blocking_class"] == "data integrity"
    assert header["scope"] == ["src/writer.py", "tests/test_writer.py"]


# ---------------------------------------------------------------- the subset's quoting

def test_r062_the_empty_string_is_written_quoted_and_read_back_empty(tmp_path):
    """Done when: the empty string written as `""` (a blank value reads as null) and read back as the empty string:
    the status file's `Awaiting user on: nothing` is the header's `awaiting_user_on: ""`."""
    rel = "docs/PROJECT_STATUS.md"
    root = project(tmp_path, [rel])
    code, out = migrate(root)
    assert code == 0, out
    header, head = assert_migrated("project-status", rel, FIXTURES[rel][1], read(root, rel))
    assert header["awaiting_user_on"] == ""
    assert re.search(r'(?m)^awaiting_user_on: ""$', head), head
    assert yaml.safe_load(yaml_block(head.encode("utf-8")))["awaiting_user_on"] == ""


def test_r062_strings_the_plain_form_refuses_are_written_double_quoted(tmp_path):
    """Done when: every string the plain form would refuse double-quoted, dates first: a date, a value holding
    `: `, a version beginning with a digit, a typed word (`on`, `off`), a path with a slash, and a string holding a
    double quote (escaped `\\"`), each read back as the string it was."""
    root = project(tmp_path, ["docs/PROJECT_STATUS.md", "docs/RUN_PARAMETERS.md"])
    code, out = migrate(root)
    assert code == 0, out
    status, shead = assert_migrated("project-status", "docs/PROJECT_STATUS.md",
                                    FIXTURES["docs/PROJECT_STATUS.md"][1], read(root, "docs/PROJECT_STATUS.md"))
    assert '"ISS-023: a report read as a brief"' in shead
    assert "ISS-023: a report read as a brief" in status["open_issues"]
    assert re.search(r'(?m)^bridge_version: "2026\.11\.09a"$', shead), shead
    assert status["bridge_version"] == "2026.11.09a"
    rp, rhead = assert_migrated("run-parameters", "docs/RUN_PARAMETERS.md", FIXTURES["docs/RUN_PARAMETERS.md"][1],
                                read(root, "docs/RUN_PARAMETERS.md"))
    assert re.search(r'(?m)^ +date: "2026-11-04"$', rhead), rhead
    assert re.search(r'(?m)^ +date: "2026-11-05"$', rhead), rhead
    assert rp["design_rounds_above_five"][0]["date"] == "2026-11-04"
    assert re.search(r'(?m)^ +words: "owner: seven rounds"$', rhead), rhead
    assert re.search(r'(?m)^refactoring_pass: "on"$', rhead), rhead
    assert re.search(r'(?m)^parallel_increments: "off"$', rhead), rhead
    assert re.search(r'(?m)^installer_verification: "n/a"$', rhead), rhead
    assert rp["ceiling_above_twice"] == [{"kind": "builder", "seconds": 28800,
                                          "words": 'the owner said "take the night"'}]
    assert '\\"take the night\\"' in rhead
    assert rp["agent_ceiling"] == 2400


# ---------------------------------------------------------------- --check and the exit codes

def test_r062_check_writes_nothing_and_lists_one_line_per_record(tmp_path):
    """Done when: with --check it writes nothing and prints one line per record (`would write <path>`, `has a
    header <path>`, `cannot read <path>: <reason>`, `cannot write <path>: ...`), exit 1 where any record would be
    written or cannot be written."""
    root = project(tmp_path, ["docs/INVENTORY.md", ("docs/REQUIREMENTS.md", HEADED_REQUIREMENTS),
                              ("handoff/TASK-020.md", ELLIPSIS_BRIEF), ("docs/PROJECT_STATUS.md", status_over_chars())])
    before = snapshot(root)
    code, out = migrate(root, "--check")
    assert snapshot(root) == before, "--check wrote"
    assert code == 1, out
    assert every_listing(out, "docs/INVENTORY.md") == [("would write ", "")], out
    assert every_listing(out, "docs/REQUIREMENTS.md") == [("has a header ", "")], out
    got = every_listing(out, "handoff/TASK-020.md")
    assert len(got) == 1 and got[0][0] == "cannot read " and got[0][1], out
    got = every_listing(out, "docs/PROJECT_STATUS.md")
    assert len(got) == 1 and got[0][0] == "cannot write ", out
    assert re.fullmatch(r"\d+ characters with the header, over the older cap; trim the body first", got[0][1]), out


CHECK_CASES = {
    "would-write-only": (["docs/INVENTORY.md"], 1),
    "cannot-write-only": ([("docs/PROJECT_STATUS.md", status_over_chars())], 1),
    "has-a-header-only": ([("docs/REQUIREMENTS.md", HEADED_REQUIREMENTS)], 0),
    "cannot-read-and-has-a-header": ([("docs/REQUIREMENTS.md", HEADED_REQUIREMENTS),
                                      ("handoff/TASK-020.md", ELLIPSIS_BRIEF),
                                      ("handoff/TASK-021.md", EMPTY_SCOPE_BRIEF),
                                      ("docs/BUILD_PLAN.md", UNBALANCED_PLAN)], 0),
}


@pytest.mark.parametrize("case", list(CHECK_CASES))
def test_r062_check_exit_code(tmp_path, case):
    """Done when: --check exits 1 where any enumerated record would be written or cannot be written and 0
    otherwise, a `cannot read` line (a refused merged brief among them) affecting that exit not at all; nothing
    written in any case."""
    files, want = CHECK_CASES[case]
    root = project(tmp_path, files)
    before = snapshot(root)
    code, out = migrate(root, "--check")
    assert snapshot(root) == before, "--check wrote"
    assert code == want, out


RUN_CASES = {
    "writes-only": (["docs/INVENTORY.md", "docs/RUN_PARAMETERS.md"], 0),
    "cannot-read-beside-writes": (["docs/INVENTORY.md", ("handoff/TASK-020.md", ELLIPSIS_BRIEF)], 0),
    "cannot-write-stands": (["docs/INVENTORY.md", ("docs/PROJECT_STATUS.md", status_over_lines())], 1),
}


@pytest.mark.parametrize("case", list(RUN_CASES))
def test_r062_the_runs_own_exit(tmp_path, case):
    """Done when: the run's exit 1 where a `cannot write` stands and 0 otherwise, a `cannot read` affecting it not
    at all, so a project with a refused merged brief gets a clean run; the writable records written either way."""
    files, want = RUN_CASES[case]
    root = project(tmp_path, files)
    code, out = migrate(root)
    assert code == want, out
    assert read(root, "docs/INVENTORY.md").startswith(b"---"), out


# ---------------------------------------------------------------- enumeration

def test_r062_from_a_project_root_every_kind_is_found_and_reports_passed_over(tmp_path):
    """Done when: from a project root (the current folder where nothing is given) the eight kinds' records are
    enumerated by the kind rule: the status file, every docs/BUILD_PLAN*.md, every handoff/*.md but a report
    (`<ID>-report.md`, `<ID>-r<N>-report.md`, by HANDOFF_REPORT_NAME) or a resolution file (HANDOFF_RESOLUTION), the
    inventory, the register, the index, the deviations file, the run parameters; a report or a resolution file is
    never listed and never written."""
    root = project(tmp_path, list(FIXTURES) + list(NOT_BRIEFS) + [("docs/HARDENING.md", b("# Hardening\n"))])
    before = snapshot(root)
    code, out = migrate(root, "--check")
    assert code == 1, out
    assert snapshot(root) == before
    for rel in FIXTURES:
        assert every_listing(out, rel) == [("would write ", "")], (rel, out)
    for rel in list(NOT_BRIEFS) + ["docs/HARDENING.md"]:
        name = rel.rsplit("/", 1)[1]
        assert not [l for l in out.splitlines() if name in l], (rel, out)
    code, out = migrate(root)
    assert code == 0, out
    after = snapshot(root)
    assert sorted(after) == sorted(before), "the run left a file behind or removed one"
    for rel, (kind, original) in FIXTURES.items():
        assert_migrated(kind, rel, original, after[rel])
    for rel, data in NOT_BRIEFS.items():
        assert after[rel] == data, rel
    assert after["docs/HARDENING.md"] == before["docs/HARDENING.md"]


def test_r062_a_folder_given_is_the_root(tmp_path):
    """Done when: a given path that is a folder is the root: its records are migrated, the current folder's are
    not."""
    root = project(tmp_path, ["docs/INVENTORY.md", "handoff/TASK-007.md"])
    elsewhere = project(tmp_path, ["docs/INVENTORY.md"], name="elsewhere")
    code, out = migrate(elsewhere, root)
    assert code == 0, out
    assert_migrated("inventory", "docs/INVENTORY.md", FIXTURES["docs/INVENTORY.md"][1],
                    read(root, "docs/INVENTORY.md"))
    assert_migrated("brief", "handoff/TASK-007.md", FIXTURES["handoff/TASK-007.md"][1],
                    read(root, "handoff/TASK-007.md"))
    assert read(elsewhere, "docs/INVENTORY.md") == FIXTURES["docs/INVENTORY.md"][1]


def test_r062_a_second_folder_is_refused(tmp_path):
    """Done when: one folder at most; a second refused with exit 2, nothing written in either."""
    one = project(tmp_path, ["docs/INVENTORY.md"], name="one")
    two = project(tmp_path, ["docs/INVENTORY.md"], name="two")
    before = (snapshot(one), snapshot(two))
    code, out = migrate(tmp_path, one, two)
    assert code == 2, out
    assert (snapshot(one), snapshot(two)) == before


def test_r062_given_record_paths_take_only_those(tmp_path):
    """Done when: given record paths, the run takes those and no other record of the project."""
    root = project(tmp_path, ["docs/INVENTORY.md", "docs/RUN_PARAMETERS.md", "handoff/TASK-007.md"])
    code, out = migrate(root, "docs/RUN_PARAMETERS.md", "handoff/TASK-007.md")
    assert code == 0, out
    assert read(root, "docs/INVENTORY.md") == FIXTURES["docs/INVENTORY.md"][1]
    assert not every_listing(out, "docs/INVENTORY.md"), out
    assert_migrated("run-parameters", "docs/RUN_PARAMETERS.md", FIXTURES["docs/RUN_PARAMETERS.md"][1],
                    read(root, "docs/RUN_PARAMETERS.md"))
    assert_migrated("brief", "handoff/TASK-007.md", FIXTURES["handoff/TASK-007.md"][1],
                    read(root, "handoff/TASK-007.md"))


def test_r062_a_given_path_of_no_kind_is_listed_and_changes_no_exit(tmp_path):
    """Done when: a given path under no kind is listed `cannot read <path>: not a record kind`, affecting no exit,
    the run going on to the next record."""
    stray = b("# Hardening\n\nScope: src/a.py\n")
    root = project(tmp_path, ["docs/INVENTORY.md", ("docs/HARDENING.md", stray)])
    code, out = migrate(root, "--check", "docs/HARDENING.md")
    assert code == 0, out
    assert listed(out, "cannot read ", "docs/HARDENING.md") == ["not a record kind"], out
    code, out = migrate(root, "docs/HARDENING.md", "docs/INVENTORY.md")
    assert code == 0, out
    assert listed(out, "cannot read ", "docs/HARDENING.md") == ["not a record kind"], out
    assert read(root, "docs/HARDENING.md") == stray
    assert read(root, "docs/INVENTORY.md").startswith(b"---"), out


# ---------------------------------------------------------------- refusals and stops

MALFORMED = {
    "tab": b("---\nrecord: brief\nheader:\t1\n---\n" + BRIEF),
    "schema": b("---\nrecord: brief\nheader: 1\n---\n" + BRIEF),
}


@pytest.mark.parametrize("case", list(MALFORMED))
def test_r062_a_malformed_header_stops_the_run_after_the_records_before_it(tmp_path, case):
    """Done when: a malformed header (one the reader refuses, a tab inside it; or one the schema refuses) is
    refused, `HEADER MALFORMED`, exit 2, the run stopping at that record, the records before it written and listed,
    the records after it neither written nor listed, the malformed record unchanged."""
    bad = MALFORMED[case]
    root = project(tmp_path, ["docs/PROJECT_STATUS.md", ("handoff/TASK-009.md", bad), "docs/INVENTORY.md"])
    code, out = migrate(root, "docs/PROJECT_STATUS.md", "handoff/TASK-009.md", "docs/INVENTORY.md")
    assert code == 2, out
    malformed = [l for l in out.splitlines() if "HEADER MALFORMED" in l]
    assert malformed and "TASK-009.md" in malformed[0], out
    assert read(root, "handoff/TASK-009.md") == bad
    assert_migrated("project-status", "docs/PROJECT_STATUS.md", FIXTURES["docs/PROJECT_STATUS.md"][1],
                    read(root, "docs/PROJECT_STATUS.md"))
    assert [l for l in out.splitlines() if "PROJECT_STATUS.md" in l], "the record written before was not listed"
    assert read(root, "docs/INVENTORY.md") == FIXTURES["docs/INVENTORY.md"][1]
    assert not [l for l in out.splitlines() if "INVENTORY.md" in l], out


@pytest.mark.parametrize("args", [("--base", "-x"), ("--base=-x",), ("--base=--all",)],
                         ids=["separate", "joined", "joined-long"])
def test_r062_a_base_beginning_with_a_dash_is_refused(tmp_path, args):
    """Done when: a `--base` beginning with `-` refused, exit 2, nothing written."""
    root = project(tmp_path, ["docs/INVENTORY.md"])
    code, out = migrate(root, *args)
    assert code == 2, out
    assert read(root, "docs/INVENTORY.md") == FIXTURES["docs/INVENTORY.md"][1]


# ---------------------------------------------------------------- cannot read: nothing written, the run going on

def test_r062_records_the_fallback_refuses_are_listed_and_left_headerless(tmp_path):
    """Done when: a record the fallback refuses is listed `cannot read <path>: <reason>` and left header-less, the
    run going on to the next record: a brief whose Scope holds an ellipsis, a brief whose Scope is empty, a plan
    whose `Scope:` line holds an unbalanced parenthesis (`unbalanced parenthesis in <id>'s Scope`); the run exits 0
    (a merged brief among them is never repaired and never fails the run)."""
    root = project(tmp_path, [("handoff/TASK-020.md", ELLIPSIS_BRIEF), ("handoff/TASK-021.md", EMPTY_SCOPE_BRIEF),
                              ("docs/BUILD_PLAN.md", UNBALANCED_PLAN), "docs/INVENTORY.md"])
    for args in (("--check",), ()):
        code, out = migrate(root, *args)
        assert code == (1 if args else 0), out
        for rel in ("handoff/TASK-020.md", "handoff/TASK-021.md"):
            got = listed(out, "cannot read ", rel)
            assert len(got) == 1 and got[0], (rel, out)
        assert listed(out, "cannot read ", "docs/BUILD_PLAN.md") == ["unbalanced parenthesis in TASK-001's Scope"], out
    assert read(root, "handoff/TASK-020.md") == ELLIPSIS_BRIEF
    assert read(root, "handoff/TASK-021.md") == EMPTY_SCOPE_BRIEF
    assert read(root, "docs/BUILD_PLAN.md") == UNBALANCED_PLAN
    assert_migrated("inventory", "docs/INVENTORY.md", FIXTURES["docs/INVENTORY.md"][1],
                    read(root, "docs/INVENTORY.md"))


# ---------------------------------------------------------------- cannot write: the older caps

@pytest.mark.parametrize("case", ["characters", "lines"])
def test_r062_a_status_file_over_the_older_cap_is_not_written(tmp_path, case):
    """Done when: a status file whose header and body together would exceed either older cap, 12,000 characters
    or 120 lines, is listed `cannot write <path>: <n> characters with the header, over the older cap; trim the body
    first` (or `<n> lines`) by the run and by --check, left unchanged, the exit 1 on both."""
    data = status_over_chars() if case == "characters" else status_over_lines()
    rel = "docs/PROJECT_STATUS.md"
    root = project(tmp_path, [(rel, data)])
    for args in (("--check",), ()):
        code, out = migrate(root, *args)
        assert code == 1, out
        got = listed(out, "cannot write ", rel)
        assert len(got) == 1, out
        if case == "characters":
            m = re.fullmatch(r"(\d+) characters with the header, over the older cap; trim the body first", got[0])
            assert m and int(m.group(1)) > 12000, out
        else:
            m = re.match(r"(\d+) lines\b", got[0])
            assert m and int(m.group(1)) > 120, out
        assert read(root, rel) == data


# ---------------------------------------------------------------- historic, in a git repository the test builds

HISTORIC_PLAN = b("""# Build plan {dash} an early project

## Stage 1 {dash} the start
Demonstration: the tool starts.

### TASK-003 {dash} the first parser
Parent: none
Depends on: none
The parser, written before the plan had fields.

### TASK-004 {dash} the second parser
Depends on: TASK-003
Scope: src/second.py
Satisfies: R-004
""".format(dash=DASH))


def merged_repo(tmp_path):
    """A repository whose branch `done` holds the squash subject `TASK-003: something (#12)`; main does not."""
    repo = tmp_path / "proj"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "checkout", "-q", "-b", "main")
    (repo / "README.md").write_bytes(b"x\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "initial")
    git(repo, "checkout", "-q", "-b", "done")
    (repo / "first.py").write_bytes(b"x = 1\n")
    git(repo, "add", "first.py")
    git(repo, "commit", "-q", "-m", "TASK-003: something (#12)")
    git(repo, "checkout", "-q", "main")
    write(repo, "docs/BUILD_PLAN.md", HISTORIC_PLAN)
    return repo


def test_r062_a_merged_increment_without_scope_or_kind_is_marked_historic(tmp_path):
    """Done when: `historic: true` on a plan increment the fallback reads with no Scope or Kind whose ID is in the
    merged set read by bridge_env.squash_merged_ids(<root>, PLAN_ID_PATTERN, ref=<--base>), `--base` naming the
    branch whose history holds the squash subject; its `kind` `increment`, `parallel` `false`, its lists `[]`, the
    read-back passing; the unmerged increment beside it not historic."""
    repo = merged_repo(tmp_path)
    merged = bridge_env.squash_merged_ids(str(repo), bridge_env.PLAN_ID_PATTERN, ref="done")
    assert merged is not None and "TASK-003" in merged and "TASK-004" not in merged
    code, out = migrate(repo, "--base", "done")
    assert code == 0, out
    header, head = assert_migrated("build-plan", "docs/BUILD_PLAN.md", HISTORIC_PLAN, read(repo, "docs/BUILD_PLAN.md"),
                                   merged=merged)
    first, second = header["stages"][0]["increments"]
    assert first["id"] == "TASK-003" and first["historic"] is True
    assert first["kind"] == "increment" and first["parallel"] is False
    for key in ("depends_on", "diagrams", "scope", "satisfies"):
        assert first[key] == [], key
        assert re.search(r"(?m)^ +%s: \[\]$" % key, head), (key, head)
    assert second["id"] == "TASK-004" and second["historic"] is False


def test_r062_an_unreadable_merged_set_leaves_the_plan_untouched(tmp_path):
    """Done when: where the merged set cannot be read (a `--base` naming no ref) the plan file holding such an
    increment is listed `cannot read <path>: merged set unreadable (<reason>)` and left untouched, by the run and by
    --check, the exit unchanged by it."""
    repo = merged_repo(tmp_path)
    for args in (("--check", "--base", "no-such-ref"), ("--base", "no-such-ref")):
        code, out = migrate(repo, *args)
        assert code == 0, out
        got = listed(out, "cannot read ", "docs/BUILD_PLAN.md")
        assert len(got) == 1 and got[0].startswith("merged set unreadable ("), out
        assert read(repo, "docs/BUILD_PLAN.md") == HISTORIC_PLAN


# ---------------------------------------------------------------- the atomic write, in process

def load_migrate():
    assert os.path.isfile(PROGRAM), "bridge/cursor-bridge/records-migrate.py is missing (TASK-051)"
    spec = importlib.util.spec_from_file_location("records_migrate", PROGRAM)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(getattr(mod, "main", None)), "records-migrate.py has no main(argv)"
    return mod


def call_main(mod, argv):
    try:
        return mod.main(list(argv))
    except SystemExit as exc:
        return exc.code


class Killed(BaseException):
    """The process killed between the temporary file's write and the replace."""


def norm(path):
    return os.path.normcase(os.path.abspath(os.fsdecode(os.fspath(path))))


def test_r062_build_parser_is_top_level_with_check_and_base():
    """Done when: argparse, `build_parser` at top level (so dump-cli.py loads it), with `--check` and `--base`."""
    mod = load_migrate()
    parser = mod.build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
    options = {s for a in parser._actions for s in a.option_strings}
    assert {"--check", "--base"} <= options, options


def test_r062_a_crash_before_the_replace_leaves_the_record_whole(tmp_path, monkeypatch):
    """Done when: each write atomic, so a crash never leaves a half-written record: the whole file is written to a
    temporary file beside the record (in its folder) and moved with os.replace only then; killed after the
    temporary file is written and before the replace, the record is byte-identical."""
    root = project(tmp_path, ["docs/INVENTORY.md"])
    record = os.path.join(str(root), "docs", "INVENTORY.md")
    before = read(root, "docs/INVENTORY.md")
    mod = load_migrate()
    seen = []

    def killed_replace(src, dst, *args, **kwargs):
        with open(os.fspath(src), "rb") as f:
            seen.append((norm(src), norm(dst), f.read()))
        raise Killed()

    monkeypatch.chdir(str(root))
    monkeypatch.setattr(os, "replace", killed_replace)
    try:
        call_main(mod, ["docs/INVENTORY.md"])
    except Killed:
        pass
    monkeypatch.undo()
    assert read(root, "docs/INVENTORY.md") == before, "the record changed before the replace"
    assert seen, "os.replace was never called"
    src, dst, content = seen[0]
    assert dst == norm(record)
    assert os.path.dirname(src) == os.path.dirname(norm(record)) and src != dst, "the temporary file is not beside it"
    assert content.startswith(b"---") and content.endswith(before), "the temporary file was not the whole new file"


def test_r062_a_failed_temporary_write_leaves_the_record_whole(tmp_path, monkeypatch, capsys):
    """Done when: a full disk never leaves a half-written record: the temporary file's write (opened with open()
    in the record's folder) failing with OSError leaves the record byte-identical, and the run exits 3 or reports
    the error with a failing exit."""
    root = project(tmp_path, ["docs/INVENTORY.md"])
    record = norm(os.path.join(str(root), "docs", "INVENTORY.md"))
    folder = os.path.dirname(record)
    before = read(root, "docs/INVENTORY.md")
    mod = load_migrate()
    real_open = builtins.open
    hits = []

    def full_disk_open(file, mode="r", *args, **kwargs):
        if any(c in mode for c in "wax+"):
            if isinstance(file, int):
                hits.append(file)
                raise OSError(errno.ENOSPC, "No space left on device")
            p = norm(file)
            if p != record and os.path.dirname(p) == folder:
                hits.append(p)
                raise OSError(errno.ENOSPC, "No space left on device")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.chdir(str(root))
    monkeypatch.setattr(builtins, "open", full_disk_open)
    monkeypatch.setattr(io, "open", full_disk_open)
    raised = None
    try:
        code = call_main(mod, ["docs/INVENTORY.md"])
    except OSError as exc:
        code, raised = None, exc
    monkeypatch.undo()
    out = capsys.readouterr()
    assert read(root, "docs/INVENTORY.md") == before, "the record changed after a failed temporary write"
    assert hits, "no temporary file was opened for writing with open() in the record's folder"
    if raised is None:
        assert code in (1, 3), (code, out)
        assert code == 3 or "INVENTORY.md" in (out.out + out.err), (code, out)


def test_r062_a_failed_read_back_exits_3_and_leaves_the_records_untouched(tmp_path, monkeypatch, capsys):
    """Done when: the temporary file read back through read_header, check_header and header_agrees before the move;
    a read-back that fails (check_header returning a finding) leaves the record untouched, nothing replaced, and
    exits 3, the run stopping there."""
    root = project(tmp_path, ["docs/INVENTORY.md", "docs/REQUIREMENTS.md"])
    before = snapshot(root)
    mod = load_migrate()
    replaced = []
    real_replace = os.replace

    def recording_replace(src, dst, *args, **kwargs):
        replaced.append((src, dst))
        return real_replace(src, dst, *args, **kwargs)

    def failing_check(kind, header):
        return ["missing key record"]

    monkeypatch.chdir(str(root))
    monkeypatch.setattr(os, "replace", recording_replace)
    if hasattr(mod, "check_header"):
        monkeypatch.setattr(mod, "check_header", failing_check)
    if hasattr(mod, "bridge_env"):
        monkeypatch.setattr(mod.bridge_env, "check_header", failing_check)
    monkeypatch.setattr(bridge_env, "check_header", failing_check)
    code = call_main(mod, ["docs/INVENTORY.md", "docs/REQUIREMENTS.md"])
    monkeypatch.undo()
    capsys.readouterr()
    assert code == 3
    assert not replaced, "a record was replaced after a failed read-back"
    after = snapshot(root)
    for rel in ("docs/INVENTORY.md", "docs/REQUIREMENTS.md"):
        assert after[rel] == before[rel], rel


# ---------------------------------------------------------------- builder's cases below this line
