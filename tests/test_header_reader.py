"""TASK-046, the supervisor's acceptance tests (R-057): the header reader, the schema check and the
agreement helper in bridge_env, reached through getattr so that they collect on the checkpoint and
are red there, naming the missing name.

enforces: docs/DESIGN.md, "Change: release B2", "The reader", "Header first; fallback; malformed" and
"Three kinds of record, one rule each"; docs/BUILD_PLAN.md, TASK-046's Done when; R-057.

The fixed forms these tests pin, which the brief repeats:
- read_header(text) returns (header, body): the mapping, or None where the first line is not `---`.
- HeaderError carries `.line`, the 1-based line of the whole text, and names it in its message.
- check_header(kind, header) and header_agrees(kind, header, fallback) return lists of strings,
  empty where all is well. Each string of header_agrees is what follows `HEADER DISAGREES: `.
- A fallback is the fallback reader's reading of the prose. Its shape per kind is
  fallback_* below; an absent line is an absent key or None.

The supervisor's cases stand above the marker at the end of this file. The builder adds its own
cases below the marker and edits nothing above it.
"""
import glob
import os
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures", "headers")
KINDS = ("project-status", "build-plan", "brief", "inventory", "requirements", "diagram-index", "deviations", "run-parameters")


def need(name):
    obj = getattr(bridge_env, name, None)
    assert obj is not None, "bridge_env.%s is missing (TASK-046)" % name
    return obj


def head(*lines):
    """A record: line 1 is `---`, lines[0] is line 2."""
    return "---\n" + "".join(line + "\n" for line in lines) + "---\nbody\n"


def refused(text, line=None):
    error = need("HeaderError")
    with pytest.raises(error) as caught:
        need("read_header")(text)
    number = caught.value.line
    assert isinstance(number, int) and number >= 1
    if line is not None:
        assert number == line, "named line %s, expected %s: %s" % (number, line, caught.value)
    assert str(number) in str(caught.value), "the message does not name its line: %s" % caught.value
    return caught.value


# --- first line, body, line endings ---


def test_r057_a_record_whose_first_line_is_not_the_marker_has_no_header():
    text = "# Title\n---\na: b\n---\n"
    assert need("read_header")(text) == (None, text)


@pytest.mark.parametrize("text", ["", "----\na: b\n----\n", "--- a\nb: c\n---\n", " ---\na: b\n---\n"])
def test_r057_only_the_exact_marker_opens_a_header(text):
    assert need("read_header")(text) == (None, text)


def test_r057_header_and_body():
    assert need("read_header")(head("a: word")) == ({"a": "word"}, "body\n")


def test_r057_empty_header_is_an_empty_mapping():
    assert need("read_header")("---\n---\nbody\n") == ({}, "body\n")


def test_r057_a_later_rule_is_body():
    text = "---\na: word\n---\nbody\n---\nb: more\n---\n"
    assert need("read_header")(text) == ({"a": "word"}, "body\n---\nb: more\n---\n")


def test_r057_crlf_reads_as_lf_and_the_body_keeps_its_endings():
    """docs/ is CRLF in a Windows checkout (core.autocrlf), so a header there must read."""
    text = "---\r\na: word\r\nb: [x, y]\r\nc:\r\n  - p\r\n---\r\nbody\r\nmore\r\n"
    assert need("read_header")(text) == ({"a": "word", "b": ["x", "y"], "c": ["p"]}, "body\r\nmore\r\n")


def test_r057_byte_order_mark_tolerated():
    assert need("read_header")(chr(0xFEFF) + head("a: word"))[0] == {"a": "word"}


# --- what the subset reads, beside pyyaml ---

FORMS = r'''record: build-plan
header: 1
nothing:
quoted: "PR #135"
blank: ""
escapes: "say \"hi\" c:\\x"
number: 42
zero: 0
quoted_word: "yes"
quoted_date: "2026-11-04"
quoted_path: "bridge/cursor-bridge/bridge_env.py"
on_true: true
on_false: false
on_null: null
word: v1.2_x-y
upper: TASK-046
flow: [a, "b c", 3, true, null, ""]
flow_empty: []
block:
  - one
  - "two words"
  - 7
nested:
  inner:
    deep: x
  other: [p, q]
# a comment line

items:
  - id: TASK-001
    scope: [a, b]
    inner:
      - k: 1
      - k: 2
  - id: TASK-002
    scope: []
after: word # a trailing comment
last: "text" # another
'''


def test_r057_the_subset_equals_pyyaml_on_every_form():
    header, body = need("read_header")("---\n" + FORMS + "---\nrest\n")
    assert header == yaml.safe_load(FORMS)
    assert body == "rest\n"


@pytest.mark.parametrize("value,expected", [
    ("word", "word"), ("a1", "a1"), ("v1.2", "v1.2"), ("snake_case", "snake_case"), ("kebab-case", "kebab-case"),
    ("TASK-046", "TASK-046"), ('"PR #135"', "PR #135"), ('""', ""), ('"a \\"q\\" b"', 'a "q" b'), ('"c:\\\\x"', "c:\\x"),
    ("42", 42), ("0", 0), ("true", True), ("false", False), ("null", None), ("", None),
    ("[a, b]", ["a", "b"]), ("[]", []), ('["x y", 1]', ["x y", 1]),
])
def test_r057_scalar_and_flow_forms(value, expected):
    line = ("a: " + value).rstrip()
    assert need("read_header")(head(line))[0] == {"a": expected}


def test_r057_a_hash_in_a_string_is_text_and_a_comment_needs_whitespace_before_it():
    read = need("read_header")
    assert read(head('a: "x # y" # z'))[0] == {"a": "x # y"}
    assert read(head("a: word # z"))[0] == {"a": "word"}
    refused(head("a: word#z"), 2)


# --- every plain scalar the subset refuses, with the advice to quote it ---

# A form pyyaml's resolver types as other than a string.
TYPED_BY_PYYAML = [
    "2026-11-04", "-1", "+1", "1.5", ".5", "012", "0x1F", "1:30", "1_000",
    "yes", "no", "on", "off", "Yes", "NO", "On", "OFF", "True", "TRUE", "False", "FALSE", "Null", "NULL", "~",
]
# A form the schemas never write unquoted (a word with a space, a colon or a slash; the migration quotes it).
NEVER_WRITTEN_PLAIN = ["two words", "a:b", "a/b", "bridge/cursor-bridge/x.py", "docs/"]
# pyyaml reads these as strings, so they fall in neither half of the plan's disjunction: the YAML 1.1 words
# `y` and `n`, which the design lists and pyyaml's resolver does not type; `0o7` and `1e3`, numbers in YAML 1.2;
# `1a`, a word that does not start with a letter. The subset refuses them all the same and the migration quotes
# them (a settled point of TASK-046's supervisor's tests, told in the brief).
TYPED_ELSEWHERE = ["y", "n", "Y", "N", "0o7", "1e3", "1a"]


@pytest.mark.parametrize("form", TYPED_BY_PYYAML + NEVER_WRITTEN_PLAIN + TYPED_ELSEWHERE)
def test_r057_every_other_plain_scalar_is_refused_with_its_line_and_the_advice(form):
    error = refused(head("record: word", "a: " + form), 3)
    assert "quote" in str(error).lower(), "no advice to quote: %s" % error


@pytest.mark.parametrize("form", TYPED_BY_PYYAML)
def test_r057_refused_forms_pyyaml_types_are_really_typed(form):
    """The disjunction's first half: a value pyyaml would type is never read as a string here."""
    assert need("read_header")(head('a: "%s"' % form))[0] == {"a": form}
    assert not isinstance(yaml.safe_load("a: " + form)["a"], str), form


@pytest.mark.parametrize("form", NEVER_WRITTEN_PLAIN)
def test_r057_refused_forms_with_a_space_colon_or_slash_stay_strings_when_quoted(form):
    """The disjunction's second half: quoted, each reads the same in both readers."""
    text = 'a: "%s"\n' % form
    assert need("read_header")("---\n" + text + "---\n")[0] == yaml.safe_load(text)
    assert any(c in form for c in " :/"), form


def test_r057_a_single_quoted_scalar_is_refused_with_the_advice():
    error = refused(head("a: 'word'"), 2)
    assert "quote" in str(error).lower()


# --- the structural refusals, one per kind, each with its line ---


@pytest.mark.parametrize("name,lines,line", [
    ("tab in indentation", ["a:", "\t- x"], 3),
    ("anchor", ["a: &x word"], 2),
    ("alias", ["a: word", "b: *x"], 3),
    ("tag", ["a: !!str word"], 2),
    ("flow mapping", ["a: {b: c}"], 2),
    ("flow mapping in a list", ["a: [{b: c}]"], 2),
    ("flow list in a list", ["a: [[b]]"], 2),
    ("multi-line plain scalar", ["a: word", "  more"], 3),
    ("multi-line quoted scalar", ['a: "open'], 2),
    ("multi-line flow list", ["a: [x,", "  y]"], 2),
    ("block scalar literal", ["a: |", "  text"], 2),
    ("block scalar folded", ["a: >", "  text"], 2),
    ("duplicate key", ["a: word", "b: word", "a: word"], 4),
    ("duplicate nested key", ["a:", "  b: word", "  b: word"], 4),
    ("duplicate key in a list item", ["a:", "  - b: word", "    b: word"], 4),
    ("not a key line", ["justword"], 2),
    ("an unknown escape", ['a: "x\\ny"'], 2),
    ("text after a string", ['a: "x" y'], 2),
])
def test_r057_structural_refusals(name, lines, line):
    refused(head(*lines), line)


def test_r057_an_unterminated_block_is_refused():
    refused("---\na: word\nb: word\n")


def test_r057_the_block_bound_is_in_bytes():
    read = need("read_header")
    assert read("---\n# " + "x" * 262000 + "\n---\n")[0] == {}
    refused("---\n# " + "x" * 262200 + "\n---\n")
    refused("---\n# " + chr(0xE9) * 140000 + "\n---\n")


def chain(levels):
    lines, indent = [], ""
    for i in range(levels - 1):
        lines.append("%sk%d:" % (indent, i))
        indent += "  "
    lines.append("%sk%d: word" % (indent, levels - 1))
    return lines


def test_r057_the_nesting_bound_holds_for_mappings():
    assert need("read_header")(head(*chain(8)))[0] is not None
    refused(head(*chain(10)))


def test_r057_the_nesting_bound_holds_for_lists():
    lines, indent = ["a:"], "  "
    for i in range(6):
        lines.append("%s- k%d:" % (indent, i))
        indent += "    "
    lines.append("%s- word" % indent)
    refused(head(*lines))


def test_r057_a_very_deep_block_is_a_refusal_not_a_recursion_error():
    """480 levels stay under the byte bound, so the nesting bound has to answer, before any recursion limit."""
    text = head(*chain(480))
    assert len(text.encode("utf-8")) < 262144
    refused(text)


def test_r057_the_schemas_own_depth_reads():
    text = head(
        "record: build-plan", "header: 1", "stages:", "  - name: stage", "    demonstration: true", "    increments:",
        "      - id: TASK-001", "        scope:", "          - a", '          - "b/c"',
    )
    assert need("read_header")(text)[0]["stages"][0]["increments"][0]["scope"] == ["a", "b/c"]


# --- the fixtures: every header any reader accepts is read the same ---


def fixture_paths():
    return sorted(glob.glob(os.path.join(FIXTURES, "*.md")))


def test_r057_every_fixture_header_equals_pyyaml():
    read = need("read_header")
    paths = fixture_paths()
    assert paths, "tests/fixtures/headers/ holds no fixture"
    for path in paths:
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read().replace("\r\n", "\n")
        assert text.startswith("---\n"), path
        block = text[4:text.index("\n---\n", 3) + 1]
        assert read(text)[0] == yaml.safe_load(block), path


def test_r057_the_fixtures_hold_one_valid_header_per_kind():
    read, check = need("read_header"), need("check_header")
    seen = {}
    for path in fixture_paths():
        with open(path, encoding="utf-8") as f:
            header = read(f.read())[0]
        kind = header.get("record") if isinstance(header, dict) else None
        if kind in KINDS and "forms" not in os.path.basename(path):
            seen[kind] = path
            assert check(kind, header) == [], path
    assert sorted(seen) == sorted(KINDS)


def test_r057_the_fixtures_hold_the_hard_strings():
    joined = ""
    for path in fixture_paths():
        with open(path, encoding="utf-8") as f:
            joined += f.read()
    assert '"PR #135"' in joined
    assert '""' in joined


def test_r057_no_program_imports_pyyaml():
    need("read_header")
    for path in glob.glob(os.path.join(BRIDGE, "*.py")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                assert not stripped.startswith(("import yaml", "from yaml")), path


# --- check_header: the schema findings ---


def valid(kind):
    table = {
        "project-status": {
            "record": kind, "header": 1, "phase": "changing",
            "workflows": [{"type": "Host Extension Development", "subtype": "Claude Code Extension", "traits": ["Installable"]}],
            "awaiting_user_on": "", "bridge_version": "2026.11.03a", "stage": "H1", "open_issues": ["none new"],
        },
        "build-plan": {
            "record": kind, "header": 1,
            "stages": [{"name": "Stage", "demonstration": True, "increments": [{
                "id": "TASK-046", "title": "The reader", "kind": "increment", "parent": None, "depends_on": [],
                "parallel": False, "diagrams": ["D-002"], "scope": ["a.py"], "satisfies": ["R-057"], "deferred": None,
                "historic": False,
            }]}],
        },
        "brief": {
            "record": kind, "header": 1, "id": "TASK-046", "round": 2, "satisfies": ["R-057"], "scope": ["a.py", "docs/"],
            "merge_unit": None, "blocking_class": None,
        },
        "inventory": {
            "record": kind, "header": 1, "reflected_through": None, "development_data": "Development data: none",
            "tables": {
                "features": {"columns": ["Feature", "What"], "key": "Feature"},
                "resources": {"columns": ["Name", "Kind"], "key": "Name"},
                "decisions": {"columns": ["Decision", "Reason"], "key": "Decision"},
                "deferred": {"columns": ["Item", "Why"], "key": "Item"},
            },
        },
        "requirements": {
            "record": kind, "header": 1, "columns": ["ID", "Status", "Evidence"],
            "roles": {"id": "ID", "status": "Status", "evidence": "Evidence"},
            "statuses": ["planned", "built", "deferred", "dropped"],
        },
        "diagram-index": {
            "record": kind, "header": 1,
            "columns": ["ID", "Level", "Kind", "Status", "File", "Refines", "Realizes", "Enforced by", "Why"],
            "roles": {
                "id": "ID", "level": "Level", "kind": "Kind", "status": "Status", "file": "File", "refines": "Refines",
                "realizes": "Realizes", "enforced_by": "Enforced by", "why": "Why",
            },
        },
        "deviations": {
            "record": kind, "header": 1, "columns": ["Diagram", "From", "To", "As built", "Since", "Resolved by"],
            "roles": {
                "diagram": "Diagram", "from": "From", "to": "To", "as_built": "As built", "since": "Since",
                "resolved_by": "Resolved by",
            },
        },
        "run-parameters": {
            "record": kind, "header": 1, "stage_pause": "run", "merge_authority": "supervisor", "refactoring_pass": "on",
            "installer_verification": "n/a", "parallel_increments": "on", "agent_ceiling": None,
            "ceiling_above_twice": [{"kind": "builder", "seconds": 28800, "words": "their words"}],
            "design_rounds_above_five": [{"subject": "pace", "rounds": 7, "words": "w", "date": "2026-11-04"}],
            "review_rounds_above_ceiling": [{"id": "TASK-046", "rounds": 4, "words": "w", "date": "2026-11-04"}],
        },
    }
    return table[kind]


@pytest.mark.parametrize("kind", KINDS)
def test_r057_a_valid_header_has_no_finding(kind):
    assert need("check_header")(kind, valid(kind)) == []


@pytest.mark.parametrize("kind", KINDS)
def test_r057_an_unknown_key_is_a_finding_naming_it(kind):
    header = valid(kind)
    header["surplus_key"] = "word"
    assert any("surplus_key" in f for f in need("check_header")(kind, header))


@pytest.mark.parametrize("kind,key", [
    ("project-status", "phase"), ("project-status", "open_issues"), ("build-plan", "stages"), ("brief", "scope"),
    ("inventory", "tables"), ("requirements", "statuses"), ("diagram-index", "roles"), ("deviations", "columns"),
    ("run-parameters", "agent_ceiling"), ("brief", "record"), ("brief", "header"),
])
def test_r057_a_missing_key_is_a_finding_naming_it(kind, key):
    header = valid(kind)
    del header[key]
    assert any(key in f for f in need("check_header")(kind, header))


def mutate(kind, path, value):
    header = valid(kind)
    node = header
    for step in path[:-1]:
        node = node[step]
    node[path[-1]] = value
    return header


@pytest.mark.parametrize("kind,path,value", [
    ("project-status", ["phase"], 3),
    ("project-status", ["phase"], "doing"),
    ("project-status", ["phase"], None),
    ("project-status", ["workflows"], "Host Extension Development"),
    ("project-status", ["workflows", 0, "subtype"], 3),
    ("project-status", ["workflows", 0, "traits"], "Installable"),
    ("project-status", ["workflows", 0, "surplus"], "word"),
    ("project-status", ["open_issues"], [1]),
    ("project-status", ["awaiting_user_on"], None),
    ("build-plan", ["stages", 0, "demonstration"], "yes"),
    ("build-plan", ["stages", 0, "increments", 0, "kind"], None),
    ("build-plan", ["stages", 0, "increments", 0, "kind"], "task"),
    ("build-plan", ["stages", 0, "increments", 0, "parallel"], None),
    ("build-plan", ["stages", 0, "increments", 0, "parallel"], "yes"),
    ("build-plan", ["stages", 0, "increments", 0, "historic"], "yes"),
    ("build-plan", ["stages", 0, "increments", 0, "scope"], None),
    ("build-plan", ["stages", 0, "increments", 0, "parent"], 3),
    ("build-plan", ["stages", 0, "increments", 0, "surplus"], "word"),
    ("brief", ["round"], True),
    ("brief", ["round"], "1"),
    ("brief", ["round"], None),
    ("brief", ["merge_unit"], "TASK-046"),
    ("brief", ["blocking_class"], "speed"),
    ("brief", ["blocking_class"], 3),
    ("inventory", ["tables", "features", "columns"], "Feature"),
    ("inventory", ["tables", "features", "surplus"], "word"),
    ("requirements", ["roles", "evidence"], 3),
    ("run-parameters", ["agent_ceiling"], "3600"),
    ("run-parameters", ["agent_ceiling"], True),
    ("run-parameters", ["ceiling_above_twice", 0, "seconds"], "28800"),
    ("run-parameters", ["design_rounds_above_five", 0, "rounds"], None),
    ("run-parameters", ["review_rounds_above_ceiling", 0, "date"], 2026),
])
def test_r057_a_wrong_type_or_value_outside_its_set_is_a_finding(kind, path, value):
    assert need("check_header")(kind, mutate(kind, path, value)) != []


@pytest.mark.parametrize("kind,path,value", [
    ("project-status", ["workflows", 0, "subtype"], None),
    ("project-status", ["workflows"], []),
    ("project-status", ["open_issues"], []),
    ("inventory", ["reflected_through"], "2026-11-04"),
    ("run-parameters", ["agent_ceiling"], 3600),
    ("run-parameters", ["ceiling_above_twice"], []),
    ("brief", ["merge_unit"], ["TASK-046", "TASK-047"]),
    ("brief", ["blocking_class"], "data integrity"),
    ("build-plan", ["stages", 0, "increments", 0, "parent"], "TASK-045"),
    ("build-plan", ["stages", 0, "increments", 0, "deferred"], "owner 2026-11-04"),
    ("build-plan", ["stages"], []),
])
def test_r057_what_the_schema_admits_is_no_finding(kind, path, value):
    assert need("check_header")(kind, mutate(kind, path, value)) == []


@pytest.mark.parametrize("value", [2, 0, True, "1", None])
def test_r057_the_schema_version_is_exactly_one(value):
    header = valid("brief")
    header["header"] = value
    assert need("check_header")("brief", header) != []


def test_r057_a_record_the_program_did_not_expect_is_a_finding():
    header = valid("brief")
    header["record"] = "inventory"
    assert need("check_header")("brief", header) != []


@pytest.mark.parametrize("statuses", [
    ["planned", "built", "deferred"],
    ["planned", "built", "deferred", "dropped", "retired"],
    ["planned", "built", "deferred", "retired"],
    ["planned", "planned", "built", "deferred", "dropped"],
])
def test_r057_statuses_must_be_exactly_the_four_words(statuses):
    header = valid("requirements")
    header["statuses"] = statuses
    assert need("check_header")("requirements", header) != []


@pytest.mark.parametrize("kind,role", [
    ("requirements", "status"), ("diagram-index", "enforced_by"), ("deviations", "as_built"),
])
def test_r057_a_role_naming_a_column_absent_from_columns_is_malformed(kind, role):
    header = valid(kind)
    header["roles"][role] = "No Such Column"
    assert any(role in f for f in need("check_header")(kind, header))


# --- header_agrees: the fallback's reading against the header, under the design's normalisation ---


def fallback_status():
    return {
        "phase": "changing",
        "workflows": [{"type": "Host Extension Development", "subtype": "Claude Code Extension", "traits": ["Installable"]}],
        "awaiting_user_on": "nothing", "bridge_version": "2026.11.03a", "stage": "H1", "open_issues": ["none new"],
    }


def test_r057_status_agrees():
    assert need("header_agrees")("project-status", valid("project-status"), fallback_status()) == []


@pytest.mark.parametrize("prose", ["nothing", "none", "n/a", "Nothing", "NONE", "N/A", "<nothing>", "nothing yet", "none (the owner has answered)"])
def test_r057_every_no_wait_form_agrees_with_the_empty_string(prose):
    fallback = fallback_status()
    fallback["awaiting_user_on"] = prose
    assert need("header_agrees")("project-status", valid("project-status"), fallback) == []


def test_r057_a_real_wait_disagrees_with_the_empty_string_and_agrees_with_itself():
    agrees = need("header_agrees")
    fallback = fallback_status()
    fallback["awaiting_user_on"] = "the gate"
    assert agrees("project-status", valid("project-status"), fallback) == ["awaiting_user_on"]
    header = valid("project-status")
    header["awaiting_user_on"] = "the gate"
    assert agrees("project-status", header, fallback) == []


@pytest.mark.parametrize("key,value", [
    ("phase", "building"), ("bridge_version", "2026.11.04a"), ("stage", "H2"), ("open_issues", ["other"]),
    ("workflows", []),
])
def test_r057_status_each_key_compared(key, value):
    fallback = fallback_status()
    fallback[key] = value
    assert need("header_agrees")("project-status", valid("project-status"), fallback) == [key]


def fallback_brief():
    return {"name": "TASK-046-r2", "satisfies": ["R-057"], "scope": ["a.py", "docs/"], "merge_unit": None, "blocking_class": None}


def test_r057_brief_agrees_its_name_giving_id_and_round():
    agrees = need("header_agrees")
    assert agrees("brief", valid("brief"), fallback_brief()) == []
    header = valid("brief")
    header["round"] = 1
    fallback = fallback_brief()
    fallback["name"] = "TASK-046"
    assert agrees("brief", header, fallback) == []


@pytest.mark.parametrize("name,expected", [("TASK-047-r2", "id"), ("TASK-046-r3", "round"), ("TASK-046", "round")])
def test_r057_brief_name_against_id_and_round(name, expected):
    fallback = fallback_brief()
    fallback["name"] = name
    assert need("header_agrees")("brief", valid("brief"), fallback) == [expected]


@pytest.mark.parametrize("key,value", [
    ("satisfies", ["R-058"]), ("satisfies", None), ("scope", ["a.py"]), ("merge_unit", ["TASK-046", "TASK-047"]),
    ("blocking_class", "behaviour"),
])
def test_r057_brief_each_key_compared(key, value):
    fallback = fallback_brief()
    fallback[key] = value
    assert need("header_agrees")("brief", valid("brief"), fallback) == [key]


@pytest.mark.parametrize("scope", [["a.py", "docs"], ["a.py/", "docs/"]])
def test_r057_a_folder_slash_is_kept_on_both_sides_never_added_or_removed(scope):
    fallback = fallback_brief()
    fallback["scope"] = scope
    assert need("header_agrees")("brief", valid("brief"), fallback) == ["scope"]


def plan_header(**fields):
    increment = {
        "id": "TASK-046", "title": "The reader", "kind": "increment", "parent": None, "depends_on": [], "parallel": False,
        "diagrams": [], "scope": ["a.py"], "satisfies": ["R-057"], "deferred": None, "historic": False,
    }
    increment.update(fields)
    return {"record": "build-plan", "header": 1, "stages": [{"name": "Stage", "demonstration": True, "increments": [increment]}]}


def plan_fallback(fields=None, merged=(), demonstration="shown live", title="The reader", name="Stage"):
    lines = {"scope": ["a.py"], "satisfies": ["R-057"]}
    lines.update(fields or {})
    return {
        "merged": set(merged) if merged is not None else None,
        "stages": [{"name": name, "demonstration": demonstration, "increments": [{"id": "TASK-046", "title": title, "fields": lines}]}],
    }


def test_r057_plan_agrees_with_every_absent_line_at_its_default():
    assert need("header_agrees")("build-plan", plan_header(), plan_fallback()) == []


@pytest.mark.parametrize("prose,value", [("yes", True), ("no", False), (None, False)])
def test_r057_parallel_normalised(prose, value):
    assert need("header_agrees")("build-plan", plan_header(parallel=value), plan_fallback({"parallel": prose})) == []


@pytest.mark.parametrize("prose,value", [("yes", False), ("no", True), (None, True)])
def test_r057_parallel_differing_disagrees(prose, value):
    got = need("header_agrees")("build-plan", plan_header(parallel=value), plan_fallback({"parallel": prose}))
    assert got == ["TASK-046 parallel"]


@pytest.mark.parametrize("prose,value", [("group", "group"), ("increment", "increment"), (None, "increment")])
def test_r057_kind_against_its_default(prose, value):
    assert need("header_agrees")("build-plan", plan_header(kind=value), plan_fallback({"kind": prose})) == []


def test_r057_kind_differing_disagrees():
    got = need("header_agrees")("build-plan", plan_header(kind="group"), plan_fallback())
    assert got == ["TASK-046 kind"]


@pytest.mark.parametrize("key,filler_value", [("parent", None), ("depends_on", []), ("diagrams", [])])
@pytest.mark.parametrize("prose", ["none", "None", None])
def test_r057_the_filler_none_reads_as_an_absent_line(key, filler_value, prose):
    fields = {key: filler_value}
    assert need("header_agrees")("build-plan", plan_header(**fields), plan_fallback({key: prose})) == []


@pytest.mark.parametrize("key,prose,value", [
    ("parent", "TASK-045", None), ("depends_on", ["TASK-045"], []), ("diagrams", ["D-002"], []),
    ("satisfies", ["R-058"], ["R-057"]), ("scope", ["b.py"], ["a.py"]), ("deferred", "owner 2026-11-04", None),
])
def test_r057_plan_each_field_compared(key, prose, value):
    got = need("header_agrees")("build-plan", plan_header(**{key: value}), plan_fallback({key: prose}))
    assert got == ["TASK-046 %s" % key]


def test_r057_an_absent_list_line_against_the_empty_list():
    fallback = plan_fallback()
    del fallback["stages"][0]["increments"][0]["fields"]["satisfies"]
    assert need("header_agrees")("build-plan", plan_header(satisfies=[]), fallback) == []


def test_r057_an_increments_title_against_its_heading():
    got = need("header_agrees")("build-plan", plan_header(), plan_fallback(title="Another title"))
    assert got == ["TASK-046 title"]


def test_r057_a_stages_name_against_its_heading():
    assert need("header_agrees")("build-plan", plan_header(), plan_fallback(name="Other stage")) == ["Stage name"]


@pytest.mark.parametrize("line,value", [("shown live", True), (None, False), ("", False), ("   ", False)])
def test_r057_demonstration_against_the_presence_of_its_line(line, value):
    header = plan_header()
    header["stages"][0]["demonstration"] = value
    assert need("header_agrees")("build-plan", header, plan_fallback(demonstration=line)) == []


@pytest.mark.parametrize("line,value", [("shown live", False), (None, True), ("   ", True)])
def test_r057_demonstration_differing_disagrees(line, value):
    header = plan_header()
    header["stages"][0]["demonstration"] = value
    assert need("header_agrees")("build-plan", header, plan_fallback(demonstration=line)) == ["Stage demonstration"]


def historic_fallback(merged, **fields):
    fallback = plan_fallback(merged=merged)
    fallback["stages"][0]["increments"][0]["fields"] = dict(fields)
    return fallback


def historic_header(flag):
    return plan_header(scope=[], satisfies=[], historic=flag)


def test_r057_historic_by_its_derivation():
    agrees = need("header_agrees")
    assert agrees("build-plan", historic_header(True), historic_fallback(["TASK-046"])) == []
    assert agrees("build-plan", historic_header(False), historic_fallback(["TASK-046"])) == ["TASK-046 historic"]


def test_r057_a_mark_on_an_unmerged_increment_disagrees():
    assert need("header_agrees")("build-plan", historic_header(True), historic_fallback([])) == ["TASK-046 historic"]


def test_r057_a_mark_where_a_scope_or_kind_line_stands_disagrees():
    agrees = need("header_agrees")
    assert agrees("build-plan", plan_header(historic=True), plan_fallback(merged=["TASK-046"])) == ["TASK-046 historic"]
    fallback = historic_fallback(["TASK-046"], kind="increment")
    assert agrees("build-plan", historic_header(True), fallback) == ["TASK-046 historic"]


def test_r057_a_merged_set_not_read_compares_no_mark():
    """Under --no-git or an unreadable log `merged` is None: the mark is accepted (the program's note, TASK-048)."""
    assert need("header_agrees")("build-plan", historic_header(True), historic_fallback(None)) == []


def test_r057_an_increment_or_stage_only_on_one_side_disagrees():
    agrees = need("header_agrees")
    header = plan_header()
    fallback = plan_fallback()
    fallback["stages"][0]["increments"].append({"id": "TASK-047", "title": "x", "fields": {}})
    assert agrees("build-plan", header, fallback) != []
    fallback = plan_fallback()
    fallback["stages"].append({"name": "Second", "demonstration": None, "increments": []})
    assert agrees("build-plan", header, fallback) != []


@pytest.mark.parametrize("kind", ["requirements", "diagram-index", "deviations"])
def test_r057_a_table_agrees_with_its_header_row(kind):
    assert need("header_agrees")(kind, valid(kind), {"header_row": list(valid(kind)["columns"])}) == []


@pytest.mark.parametrize("kind", ["requirements", "diagram-index", "deviations"])
def test_r057_a_declared_column_the_table_lacks_disagrees(kind):
    row = list(valid(kind)["columns"])[:-1] + ["Renamed"]
    assert "columns" in need("header_agrees")(kind, valid(kind), {"header_row": row})


def test_r057_a_roles_column_absent_from_the_header_row_disagrees():
    header = valid("requirements")
    row = ["ID", "Status"]
    assert "roles.evidence" in need("header_agrees")("requirements", header, {"header_row": row})


def fallback_inventory():
    return {
        "reflected_through": None, "development_data": "Development data: none",
        "sections": {"features": ["Feature", "What"], "resources": ["Name", "Kind"], "decisions": ["Decision", "Reason"], "deferred": ["Item", "Why"]},
    }


def test_r057_inventory_agrees():
    assert need("header_agrees")("inventory", valid("inventory"), fallback_inventory()) == []


def test_r057_inventory_each_part_compared():
    agrees = need("header_agrees")
    fallback = fallback_inventory()
    fallback["reflected_through"] = "2026-11-04"
    assert agrees("inventory", valid("inventory"), fallback) == ["reflected_through"]
    fallback = fallback_inventory()
    fallback["development_data"] = "Development data: other"
    assert agrees("inventory", valid("inventory"), fallback) == ["development_data"]
    fallback = fallback_inventory()
    del fallback["sections"]["deferred"]
    assert agrees("inventory", valid("inventory"), fallback) == ["tables.deferred"]
    fallback = fallback_inventory()
    fallback["sections"]["features"] = ["Feature", "Other"]
    assert agrees("inventory", valid("inventory"), fallback) == ["columns"]


def fallback_run_parameters():
    header = valid("run-parameters")
    return {k: v for k, v in header.items() if k not in ("record", "header")}


def test_r057_run_parameters_agree():
    assert need("header_agrees")("run-parameters", valid("run-parameters"), fallback_run_parameters()) == []


@pytest.mark.parametrize("key,value", [
    ("stage_pause", "pause"), ("merge_authority", "owner"), ("refactoring_pass", "off"), ("installer_verification", "on"),
    ("parallel_increments", "off"), ("agent_ceiling", 7200), ("ceiling_above_twice", []), ("design_rounds_above_five", []),
    ("review_rounds_above_ceiling", []),
])
def test_r057_run_parameters_each_key_compared(key, value):
    fallback = fallback_run_parameters()
    fallback[key] = value
    assert need("header_agrees")("run-parameters", valid("run-parameters"), fallback) == [key]


# --- THE BUILDER'S CASES GO BELOW THIS LINE; NOTHING ABOVE IT IS EDITED ---


def test_r057_nine_nested_mapping_keys_are_refused():
    refused(head(*chain(9)), 10)


def test_r057_mixed_list_mapping_depth_eight_reads_nine_refused():
    lines, indent = ["root:"], "  "
    for i in range(2):
        lines.append("%s- k%d:" % (indent, i))
        indent += "    "
        lines.append("%sinner:" % indent)
        indent += "  "
    lines.append("%s- leaf: word" % indent)
    assert need("read_header")(head(*lines))[0] is not None
    lines.append("%s- k2:" % indent)
    indent += "    "
    lines.append("%sinner:" % indent)
    indent += "  "
    lines.append("%s- too: deep" % indent)
    refused(head(*lines))


def test_r057_a_key_pyyaml_would_type_is_refused():
    refused(head("on: word"), 2)


def test_r057_an_integer_over_the_digit_limit_is_a_header_error():
    refused(head("n: " + "9" * 5000))


def test_r057_a_lone_surrogate_in_the_block_is_a_header_error():
    refused("---\na: " + chr(0xD800) + "\n---\n")


def test_r057_a_form_feed_inside_a_quoted_string_is_text():
    text = head('a: "a' + chr(0x0C) + 'b"', "b: word")
    assert need("read_header")(text)[0] == {"a": "a" + chr(0x0C) + "b", "b": "word"}


def test_r057_header_error_line_on_crlf():
    text = "---\r\nbad:\r\n  \t- x\r\n---\r\n"
    err = refused(text)
    assert err.line == 3


def test_r057_header_error_line_with_byte_order_mark():
    text = chr(0xFEFF) + "---\na: 'x'\n---\n"
    err = refused(text)
    assert err.line == 2


def test_r057_historic_with_merged_none_and_scope_line_disagrees():
    fallback = historic_fallback(None, scope=["a.py"])
    assert need("header_agrees")("build-plan", historic_header(True), fallback) == ["TASK-046 historic"]


def test_r057_flow_mapping_refusal_names_flow_mapping():
    err = refused(head("a: {b: c}"), 2)
    assert "flow mapping" in str(err).lower()


def test_r057_historic_mark_when_merged_set_is_empty():
    assert need("header_agrees")("build-plan", historic_header(True), historic_fallback([])) == ["TASK-046 historic"]
