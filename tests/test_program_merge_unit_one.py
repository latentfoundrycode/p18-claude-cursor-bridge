"""R-105: a merge unit of one increment is refused with its cause (TASK-084, the field finding F7).

The supervisor's acceptance tests, written before the builder's run. The launcher is started on a scratch Workspace
with the stand-in for cursor-agent the other brief-rule tests use (tests/test_task032_supervisor_launcher.py), so no
builder runs.

enforces: docs/DESIGN.md, "Change: the one-increment merge unit"; docs/BUILD_PLAN.md, TASK-084's Done when; R-105.
"""
import ast
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

import test_task032_supervisor_launcher as t32  # noqa: E402  (the launcher's lab, reused as it stands)

RULE = "bridge-run: refused - brief rule: a merge unit names two or more increments"
REMEDY = "a brief of one increment carries no Merge unit: line and merge_unit: null in its header"
POINTER = 'workflow/phases/delegation-loop.md, "3. Delegate to Cursor"'
SIDES = ("(the line)", "(the header)", "(the line and the header)")
HEADER_REFUSED = "bridge-run: refused - header: "
DISAGREES_MERGE_UNIT = "bridge-run: refused - header: disagrees merge_unit"
SHOWN = "handoff/TASK-001.md"

ONE = "Merge unit: TASK-001\n"
TWO = "Merge unit: TASK-001 TASK-002\n"
THREE = "Merge unit: TASK-001 TASK-002 TASK-003\n"


def _q(s):
    return '"%s"' % s


def _flow(items):
    return "[" + ", ".join(_q(x) for x in items) + "]"


def header(merge_unit=None, scope=("a.py",), blocking_class=None, raw_merge_unit=None):
    """A brief header that agrees with body()'s prose except where an argument says otherwise."""
    if raw_merge_unit is not None:
        mu = raw_merge_unit
    else:
        mu = _flow(merge_unit) if merge_unit is not None else "null"
    out = ["---", "record: brief", "header: 1", "id: TASK-001", "round: 1", "satisfies: []",
           "scope: " + _flow(scope), "merge_unit: " + mu,
           "blocking_class: " + (_q(blocking_class) if blocking_class else "null"), "---"]
    return "\n".join(out) + "\n"


def body(extra=""):
    """The prose of the fixture brief: no Satisfies line, Scope a.py, `extra` before the Scope heading."""
    return "# TASK-001\n\n## Objective\nFixture brief.\n%s\n## Scope\n- a.py\n" % extra


SENTENCE = "The packager once wrote Merge unit: TASK-001 TASK-002 TASK-003 inside a sentence like this one.\n"

# Every brief of the cases; the readers' values on each are recorded from the checkpoint below.
BRIEFS = {
    # the three cases of the design (docs/DESIGN.md, the table under "The cause")
    "field": header(("TASK-001",)) + body(ONE),
    "line-null": header() + body(ONE),
    "line-no-header": body(ONE),
    "header-no-line": header(("TASK-001",)) + body(),
    # refused by the rule: the other forms
    "line-and-header-differ": header(("TASK-002",)) + body(ONE),
    "word-not-id-header-one": header(("TASK-001",)) + body("Merge unit: task-001\n"),
    "no-space-after-colon": header() + body("Merge unit:TASK-001\n"),
    "space-after-id": header() + body("Merge unit: TASK-001   \n"),
    "field-beside-sentence": header(("TASK-001",)) + body(ONE + SENTENCE),
    "the-word-none": header() + body("Merge unit: None\n"),
    "bullet-dash": header() + body("- " + ONE),
    "bullet-star": header() + body("* " + ONE),
    # kept as header: disagrees merge_unit
    "two-line-one-header": header(("TASK-001",)) + body(TWO),
    "one-line-two-header": header(("TASK-001", "TASK-002")) + body(ONE),
    "line-second-not-id-form": header(("TASK-001",)) + body("Merge unit: TASK-001 task-002\n"),
    "line-second-rejected": header(("TASK-001",)) + body("Merge unit: TASK-001 TASK-002-r2\n"),
    "header-second-rejected": header(("TASK-001", "TASK-002-r2")) + body(ONE),
    # pass the brief rules as on the checkpoint
    "word-not-id-null": header() + body("Merge unit: task-001\n"),
    "unit-of-two": header(("TASK-001", "TASK-002")) + body(TWO),
    "unit-of-three": header(("TASK-001", "TASK-002", "TASK-003")) + body(THREE),
    "unit-of-two-no-space": header(("TASK-001", "TASK-002")) + body("Merge unit:TASK-001 TASK-002\n"),
    "no-line-null": header() + body(),
    "empty-line": header() + body("Merge unit:\n"),
    "placeholder": header() + body("Merge unit: <ID>\n"),
    # the order of the header's refusals
    "order-scope": header(("TASK-001",), scope=("b.py",)) + body(ONE),
    "order-malformed": header(("TASK-001",)).replace("round: 1", "round:\t1") + body(ONE),
    "order-schema": header(raw_merge_unit=_q("TASK-001")) + body(ONE),
    "order-blocking-class": header(blocking_class="behaviour") + body(ONE),
}

PLAN_IDS = {
    "unit-of-two": ("TASK-001", "TASK-002"),
    "unit-of-three": ("TASK-001", "TASK-002", "TASK-003"),
    "unit-of-two-no-space": ("TASK-001", "TASK-002"),
}


def launch_brief(tmp_path, name):
    lab = t32.Lab(tmp_path)
    if name in PLAN_IDS:
        t32.write_plan(lab, *PLAN_IDS[name])
    (lab.root / "handoff" / "TASK-001.md").write_bytes(BRIEFS[name].encode("ascii"))
    return t32.launch(lab, t32.build("TASK-001"))


def assert_rule(res, side):
    """Refused by the rule's line, exit 125, nothing started, naming `side` and no other."""
    line = t32.assert_refused(res, "bridge-run: refused - ")
    assert line.startswith(RULE), line
    assert REMEDY in line, line
    assert line.endswith(POINTER), line
    assert side in line, line
    for other in SIDES:
        if other != side:
            assert other not in line, line
    return line


# ---------------------------------------------------------------- the three cases of the design, red on the checkpoint

def test_r105_the_fields_case_is_refused_by_the_rule_for_both_sides(tmp_path):
    """The line of one ID beside a header listing that ID: the checkpoint answers `header: disagrees merge_unit`."""
    assert_rule(launch_brief(tmp_path, "field"), "(the line and the header)")


@pytest.mark.parametrize("name", ["line-null", "line-no-header"])
def test_r105_a_line_of_one_id_beside_null_or_with_no_header_is_refused_for_the_line(tmp_path, name):
    """The line of one ID beside `merge_unit: null`, and in a brief with no header: the checkpoint launches."""
    assert_rule(launch_brief(tmp_path, name), "(the line)")


def test_r105_a_header_listing_one_id_with_no_line_is_refused_for_the_header(tmp_path):
    """A header listing one ID and no line: the checkpoint answers `header: disagrees merge_unit`."""
    assert_rule(launch_brief(tmp_path, "header-no-line"), "(the header)")


# ---------------------------------------------------------------- the other forms the rule refuses

REFUSED = [
    ("line-and-header-differ", "(the line and the header)"),
    ("word-not-id-header-one", "(the header)"),
    ("no-space-after-colon", "(the line)"),
    ("space-after-id", "(the line)"),
    ("field-beside-sentence", "(the line and the header)"),
    ("the-word-none", "(the line)"),
    ("bullet-dash", "(the line)"),
    ("bullet-star", "(the line)"),
]


@pytest.mark.parametrize("name,side", REFUSED, ids=[n for n, _ in REFUSED])
def test_r105_the_rule_refuses_the_form_and_names_its_side(tmp_path, name, side):
    assert_rule(launch_brief(tmp_path, name), side)


# ---------------------------------------------------------------- the refusals kept

KEPT = ["two-line-one-header", "one-line-two-header", "line-second-not-id-form", "line-second-rejected",
        "header-second-rejected"]


@pytest.mark.parametrize("name", KEPT, ids=KEPT)
def test_r105_a_side_naming_two_or_more_as_written_keeps_the_disagreement(tmp_path, name):
    """Two or more is counted as written, whatever the readers make of it: the brief keeps the refusal it has."""
    line = t32.assert_refused(launch_brief(tmp_path, name), HEADER_REFUSED)
    assert line.startswith(DISAGREES_MERGE_UNIT), line
    assert "brief rule" not in line, line


# ---------------------------------------------------------------- the forms that pass

PASS = ["word-not-id-null", "unit-of-two", "unit-of-three", "unit-of-two-no-space", "no-line-null", "empty-line",
        "placeholder"]


@pytest.mark.parametrize("name", PASS, ids=PASS)
def test_r105_the_form_passes_the_brief_rules_as_on_the_checkpoint(tmp_path, name):
    t32.assert_ran(launch_brief(tmp_path, name))


# ---------------------------------------------------------------- the order of the header's refusals

def test_r105_a_unit_of_one_that_disagrees_on_its_scope_is_told_of_the_scope(tmp_path):
    line = t32.assert_refused(launch_brief(tmp_path, "order-scope"), HEADER_REFUSED)
    assert line.startswith("bridge-run: refused - header: disagrees scope"), line


def test_r105_a_malformed_header_keeps_its_own_line(tmp_path):
    line = t32.assert_refused(launch_brief(tmp_path, "order-malformed"), HEADER_REFUSED)
    assert line.startswith(HEADER_REFUSED + SHOWN + ":5"), line
    assert "brief rule" not in line, line


def test_r105_a_header_that_breaks_its_schema_keeps_its_own_line(tmp_path):
    line = t32.assert_refused(launch_brief(tmp_path, "order-schema"), HEADER_REFUSED)
    assert line.startswith(HEADER_REFUSED + SHOWN + ":"), line
    assert "brief rule" not in line and "disagrees" not in line, line


def test_r105_a_line_of_one_beside_null_and_a_disagreeing_blocking_class_is_told_of_the_unit(tmp_path):
    """The checkpoint, not reading the line, answers `header: disagrees blocking_class`."""
    assert_rule(launch_brief(tmp_path, "order-blocking-class"), "(the line)")


# ---------------------------------------------------------------- the pattern and its two constants

CHECKPOINT_PATTERN = r"^\s*(?:[-*]\s+)?Merge unit:\s*((?:[A-Z][A-Za-z0-9-]*\s+)+[A-Z][A-Za-z0-9-]*)?\s*$"
ID_FORM = "[A-Z][A-Za-z0-9-]*"
BULLET_CLASS = "[-*]"


def test_r105_merge_unit_re_keeps_the_checkpoints_text():
    assert bridge_env.MERGE_UNIT_RE.pattern == CHECKPOINT_PATTERN


def _literal_parts(node):
    """A walk of its own over an expression: every string literal inside it, wherever it stands."""
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _names(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def test_r105_both_patterns_are_composed_of_the_two_constants():
    """Every re.compile call of bridge_env.py whose argument's literal parts hold `Merge unit:`: exactly two,
    MERGE_UNIT_RE's and the rule's; both name the constant of the ID form and the constant of the bullet mark, and
    neither holds a character class of either in a literal of its own (ISS-021)."""
    with open(os.path.join(BRIDGE, "bridge_env.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    module_strings = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            module_strings[node.targets[0].id] = node.value.value
    mu_calls = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MERGE_UNIT_RE"
                                                for t in node.targets):
            mu_calls.add(id(node.value))
    calls = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "compile"
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "re" and node.args
                and any("Merge unit:" in s for s in _literal_parts(node.args[0]))):
            calls.append(node)
    assert len(calls) == 2, "re.compile calls holding 'Merge unit:': %d" % len(calls)
    mine = [c for c in calls if id(c) in mu_calls]
    assert len(mine) == 1, "MERGE_UNIT_RE is not one of the two compile calls"
    rule = [c for c in calls if id(c) not in mu_calls][0]
    mu_arg = mine[0].args[0]
    id_names = [n for n in _names(mu_arg) if ID_FORM in module_strings.get(n, "")]
    bullet_names = [n for n in _names(mu_arg) if BULLET_CLASS in module_strings.get(n, "")]
    assert len(id_names) == 1, "MERGE_UNIT_RE names no one constant of the ID form: %r" % id_names
    assert len(bullet_names) == 1, "MERGE_UNIT_RE names no one constant of the bullet mark: %r" % bullet_names
    for which, arg in (("MERGE_UNIT_RE", mu_arg), ("the rule", rule.args[0])):
        names = _names(arg)
        assert id_names[0] in names and bullet_names[0] in names, "%s does not name both constants" % which
        for part in _literal_parts(arg):
            for cls in ("[A-Z", "A-Za-z0-9", BULLET_CLASS):
                assert cls not in part, "%s holds %r in a literal of its own: %r" % (which, cls, part)


# ---------------------------------------------------------------- the readers, unchanged

def reader_values(text):
    """What each reader of a brief returns on `text`, each as its repr (a tuple stays a tuple)."""
    rec = bridge_env.read_brief_record(text, "TASK-001")
    hdr = rec.header
    return [
        repr(bridge_env._merge_unit_from_prose(text)),
        repr(bridge_env._merge_unit_from_header(hdr)) if hdr is not None else "no header",
        repr(bridge_env.merge_unit_ids(text)),
        repr(bridge_env.merge_unit_line_present(text)),
        repr(bridge_env.header_agrees("brief", hdr, rec.fallback)) if hdr is not None else "no header",
        repr(bridge_env.brief_header_refusal(text, SHOWN)),
    ]


# Recorded by the supervisor on the checkpoint (each brief above, reader_values in order).
RECORDED = json.loads(r"""
{
 "bullet-dash": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ],
 "bullet-star": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ],
 "empty-line": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ],
 "field": [
  "None",
  "('TASK-001',)",
  "('TASK-001',)",
  "False",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "field-beside-sentence": [
  "None",
  "('TASK-001',)",
  "('TASK-001',)",
  "False",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "header-no-line": [
  "None",
  "('TASK-001',)",
  "('TASK-001',)",
  "False",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "header-second-rejected": [
  "None",
  "None",
  "None",
  "False",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "line-and-header-differ": [
  "None",
  "('TASK-002',)",
  "('TASK-002',)",
  "False",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "line-no-header": [
  "None",
  "no header",
  "None",
  "False",
  "no header",
  "None"
 ],
 "line-null": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ],
 "line-second-not-id-form": [
  "None",
  "('TASK-001',)",
  "('TASK-001',)",
  "False",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "line-second-rejected": [
  "None",
  "('TASK-001',)",
  "('TASK-001',)",
  "True",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "no-line-null": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ],
 "no-space-after-colon": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ],
 "one-line-two-header": [
  "None",
  "('TASK-001', 'TASK-002')",
  "('TASK-001', 'TASK-002')",
  "False",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "order-blocking-class": [
  "None",
  "None",
  "None",
  "False",
  "['blocking_class']",
  "'header: disagrees blocking_class'"
 ],
 "order-malformed": [
  "None",
  "no header",
  "None",
  "False",
  "no header",
  "'header: handoff/TASK-001.md:5 line 5: refused character'"
 ],
 "order-schema": [
  "None",
  "no header",
  "None",
  "False",
  "no header",
  "'header: handoff/TASK-001.md:1 wrong type for merge_unit'"
 ],
 "order-scope": [
  "None",
  "('TASK-001',)",
  "('TASK-001',)",
  "False",
  "['scope', 'merge_unit']",
  "'header: disagrees scope'"
 ],
 "placeholder": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ],
 "space-after-id": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ],
 "the-word-none": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ],
 "two-line-one-header": [
  "('TASK-001', 'TASK-002')",
  "('TASK-001',)",
  "('TASK-001',)",
  "True",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "unit-of-three": [
  "('TASK-001', 'TASK-002', 'TASK-003')",
  "('TASK-001', 'TASK-002', 'TASK-003')",
  "('TASK-001', 'TASK-002', 'TASK-003')",
  "True",
  "[]",
  "None"
 ],
 "unit-of-two": [
  "('TASK-001', 'TASK-002')",
  "('TASK-001', 'TASK-002')",
  "('TASK-001', 'TASK-002')",
  "True",
  "[]",
  "None"
 ],
 "unit-of-two-no-space": [
  "('TASK-001', 'TASK-002')",
  "('TASK-001', 'TASK-002')",
  "('TASK-001', 'TASK-002')",
  "True",
  "[]",
  "None"
 ],
 "word-not-id-header-one": [
  "None",
  "('TASK-001',)",
  "('TASK-001',)",
  "False",
  "['merge_unit']",
  "'header: disagrees merge_unit'"
 ],
 "word-not-id-null": [
  "None",
  "None",
  "None",
  "False",
  "[]",
  "None"
 ]
}
""")


@pytest.mark.parametrize("name", sorted(BRIEFS), ids=sorted(BRIEFS))
def test_r105_the_readers_return_what_they_return_on_the_checkpoint(name):
    assert reader_values(BRIEFS[name]) == RECORDED[name]
