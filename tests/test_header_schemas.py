"""TASK-046, the supervisor's acceptance test (R-057, D-005): docs/diagrams/D-005-header-schemas.md
against bridge_env.HEADER_SCHEMAS, key by key and type by type, either side's extra failing.

enforces: docs/diagrams/D-005-header-schemas.md, "How the attributes are written"; R-057.

HEADER_SCHEMAS is plain data: {<kind or class name>: {<key>: <type string>}}, holding the eight
kinds by their `record` value, each with `record` and `header`, and each nested class by its name.
A type string is written as D-005 writes it, so this test reads both sides with one reader.
A builder never edits this file (the brief's fixed points).
"""
import ast
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

DIAGRAM = os.path.join(ROOT, "docs", "diagrams", "D-005-header-schemas.md")
KINDS = ("project-status", "build-plan", "brief", "inventory", "requirements", "diagram-index", "deviations", "run-parameters")


def schemas():
    obj = getattr(bridge_env, "HEADER_SCHEMAS", None)
    assert obj is not None, "bridge_env.HEADER_SCHEMAS is missing (TASK-046)"
    return obj


def diagram_classes():
    """{class name: (annotation or None, {attribute: type string})} from the fenced classDiagram."""
    with open(DIAGRAM, encoding="utf-8") as f:
        text = f.read()
    fence = re.search(r"```mermaid\s*\n(.*?)```", text, re.S)
    assert fence, "D-005 holds no mermaid block"
    out = {}
    for name, body in re.findall(r"class\s+(\w+)\s*\{(.*?)\}", fence.group(1), re.S):
        annotation, attrs = None, {}
        for raw in body.splitlines():
            line = raw.strip()
            if not line:
                continue
            ann = re.fullmatch(r"<<([\w-]+)>>", line)
            if ann:
                annotation = ann.group(1)
                continue
            key, sep, value = line.partition(" : ")
            assert sep, "D-005 attribute without a type: %r" % line
            attrs[key.strip()] = value.strip()
        out[name] = (annotation, attrs)
    return out


def norm(type_string):
    """A type string read as D-005 says: a trailing ` or null` first, then `list of`, then an enum's items."""
    text = type_string.strip()
    nullable = text.endswith(" or null")
    if nullable:
        text = text[: -len(" or null")].strip()
    if text.startswith("list of "):
        inner = norm(text[len("list of "):])
    elif text.startswith("enum of "):
        inner = ("enum", frozenset(x.strip() for x in text[len("enum of "):].split(", ")))
    else:
        inner = text
    if text.startswith("list of "):
        inner = ("list", inner)
    return ("nullable", inner) if nullable else inner


def expected_tables():
    classes = diagram_classes()
    base = classes["HeaderRecord"][1]
    out = {}
    for name, (annotation, attrs) in classes.items():
        if name == "HeaderRecord":
            continue
        if annotation in KINDS:
            merged = dict(base)
            merged.update(attrs)
            out[annotation] = merged
        else:
            out[name] = attrs
    return out


def test_r057_d005_the_tables_are_the_eight_kinds_and_the_nested_classes():
    got, want = set(schemas()), set(expected_tables())
    assert got == want, "only in HEADER_SCHEMAS: %s; only in D-005: %s" % (sorted(got - want), sorted(want - got))
    assert set(KINDS) <= got


@pytest.mark.parametrize("table", sorted(
    list(KINDS) + ["WorkflowPart", "Stage", "Increment", "InventoryTables", "TableShape", "RequirementsRoles",
                   "DiagramIndexRoles", "DeviationsRoles", "CeilingLift", "DesignLift", "ReviewLift"]))
def test_r057_d005_every_key_and_type_equals_the_diagram(table):
    got, want = schemas().get(table), expected_tables()[table]
    assert got is not None, "HEADER_SCHEMAS has no table %s" % table
    assert set(got) == set(want), "%s: only in HEADER_SCHEMAS: %s; only in D-005: %s" % (
        table, sorted(set(got) - set(want)), sorted(set(want) - set(got)))
    for key in want:
        assert norm(got[key]) == norm(want[key]), "%s.%s: %r in HEADER_SCHEMAS, %r in D-005" % (table, key, got[key], want[key])


@pytest.mark.parametrize("table", sorted(
    list(KINDS) + ["WorkflowPart", "Stage", "Increment", "InventoryTables", "TableShape", "RequirementsRoles",
                   "DiagramIndexRoles", "DeviationsRoles", "CeilingLift", "DesignLift", "ReviewLift"]))
def test_r057_r2_every_tables_keys_stand_in_the_diagrams_order(table):
    """TASK-051 writes a header's keys in the schema's order (handoff/TASK-046.md, Requirement 11)."""
    assert list(schemas()[table]) == list(expected_tables()[table])


@pytest.mark.parametrize("kind", KINDS)
def test_r057_every_kind_opens_with_record_and_header(kind):
    keys = list(schemas()[kind])
    assert keys[:2] == ["record", "header"], "%s: the two keys every header opens with come first: %s" % (kind, keys[:2])
    assert norm(schemas()[kind]["header"]) == "integer"
    assert norm(schemas()[kind]["record"]) == ("enum", frozenset(KINDS))


def test_r057_phase_set_is_the_hook_table():
    """The design's `phase`: the eleven values session-start.py's PHASE_MODULES maps, read as code."""
    with open(os.path.join(BRIDGE, "session-start.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    keys = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PHASE_MODULES" for t in node.targets):
            keys = {k.value for k in node.value.keys}
    assert keys, "session-start.py holds no PHASE_MODULES mapping"
    assert norm(schemas()["project-status"]["phase"]) == ("enum", frozenset(keys))
    assert len(keys) == 11


def test_r057_blocking_class_set_is_the_five_classes():
    assert norm(schemas()["brief"]["blocking_class"]) == ("nullable", ("enum", frozenset(bridge_env.BLOCKING_CLASSES)))


@pytest.mark.parametrize("table,key", [
    ("Increment", "kind"), ("Increment", "parallel"), ("Increment", "historic"),
    ("Increment", "depends_on"), ("Increment", "scope"), ("Increment", "satisfies"), ("Increment", "diagrams"),
    ("brief", "round"), ("brief", "scope"), ("brief", "satisfies"),
])
def test_r057_values_the_design_says_are_never_null(table, key):
    assert not norm(schemas()[table][key])[0] == "nullable", "%s.%s is never null" % (table, key)


def test_r057_brief_round_is_an_integer():
    assert norm(schemas()["brief"]["round"]) == "integer"
