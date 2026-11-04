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
import time
import tracemalloc

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
    text = "---\r\na: word\r\nb: [x, z]\r\nc:\r\n  - p\r\n---\r\nbody\r\nmore\r\n"
    assert need("read_header")(text) == ({"a": "word", "b": ["x", "z"], "c": ["p"]}, "body\r\nmore\r\n")


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


# --- what round 1 read wrongly: the supervisor's probe against yaml.safe_load (TASK-046-r2) ---
# enforces: docs/DESIGN.md, "The reader"; handoff/TASK-046.md, Requirements 1, 2, 4, 6, 8, 10, 14, 16, 17.

TAB = chr(9)
BOM = chr(0xFEFF)


def block_of(lines):
    return "".join(line + "\n" for line in lines)


def equals_pyyaml(lines):
    expected = yaml.safe_load(block_of(lines))
    assert need("read_header")(head(*lines))[0] == ({} if expected is None else expected)


@pytest.mark.parametrize("text", [
    "R&D", "the *main* point", "*main", "wow!! yes", "uses {b: c} here", "{b: c}", "see [[name]] here", "[[name]]",
    "a | b", "|", ">", "&x", "!!str word", "x - y", "- y", "key: value",
])
def test_r057_r2_a_quoted_string_is_text_whatever_it_holds(text):
    equals_pyyaml(['a: "%s"' % text])
    equals_pyyaml(['a: ["%s", z]' % text])
    equals_pyyaml(["a:", '  - "%s"' % text])
    equals_pyyaml(["a:", '  - k: "%s"' % text])


@pytest.mark.parametrize("comment", ["R&D", "the *main* point", "wow!!", "{b: c}", "see [[name]]", "|", "- y", "key: value"])
def test_r057_r2_a_comment_is_ignored_whatever_it_holds(comment):
    equals_pyyaml(["a: word # " + comment])
    equals_pyyaml(["# " + comment, "a: word"])
    equals_pyyaml(["a:", "  # " + comment, "  b: word"])


@pytest.mark.parametrize("name,lines,line", [
    ("a doubled quote", ['a: "x""y"'], 2),
    ("a doubled quote in a flow list", ['a: ["x""y"]'], 2),
    ("no space after the colon", ["a:b"], 2),
    ("no space after the colon before a flow list", ["a:[x]"], 2),
    ("no space after the colon in a list item", ["a:", "  - b:c"], 3),
    ("a flow list's leading comma", ["a: [,x]"], 2),
    ("a flow list's double comma", ["a: [x,,y]"], 2),
    ("an indent of one", ["a:", " b: c"], 3),
    ("an indent of three", ["a:", "   b: c"], 3),
    ("an indent of four", ["a:", "    b: c"], 3),
    ("a list indented by four", ["a:", "    - x"], 3),
    ("a list at its key's column", ["a:", "- x"], 3),
    ("a root key indented", [" a: 1", "b: 2"], 2),
    ("a line deeper than the key before it", ["a:", "  b: 1", "    c: 2"], 4),
    ("a line deeper than a scalar key", ["a: 1", "  b: 2"], 3),
    ("a list item deeper than the one before it", ["a:", "  - x", "    - y"], 4),
    ("a key deeper than its list item's first", ["a:", "  - k: 1", "      j: 2"], 4),
    ("a key shallower than its list item's first", ["a:", "  - k: 1", "   j: 2"], 4),
    ("a tab before a key", [TAB + "b: c"], 2),
    ("a tab before a child", ["a:", TAB + "b: c"], 3),
    ("a tab after spaces", ["a:", "  " + TAB + "b: c"], 3),
    ("a tab before a list item", ["a:", TAB + "- x"], 3),
])
def test_r057_r2_refused_where_round_1_read_it_otherwise_than_pyyaml(name, lines, line):
    refused(head(*lines), line)


@pytest.mark.parametrize("form", TYPED_BY_PYYAML + NEVER_WRITTEN_PLAIN + TYPED_ELSEWHERE)
def test_r057_r2_a_flow_item_is_held_to_the_plain_scalar_rule(form):
    error = refused(head("a: [x, %s]" % form), 2)
    assert "quote" in str(error).lower(), "no advice to quote: %s" % error


@pytest.mark.parametrize("lines", [
    ["a:", "  - k:", "    j: 2"],
    ["a:", "  - k:", "      inner: 1"],
    ["a:", "  - k:"],
    ["a:", "  - k:", "      - x"],
    ["a:", "  - k:", "    j:", "      inner: 1"],
    ["a:", "# a comment", "  b: x"],
    ["a:", "", "  b: x"],
    ["a:", "", "  - p"],
    ["a:", "  - p", "# a comment", "  - q"],
    ["a:", "  - k: 1", "", "    j: 2"],
])
def test_r057_r2_a_list_items_first_key_and_a_line_between_a_key_and_its_child(lines):
    equals_pyyaml(lines)


def test_r057_r2_a_null_key_at_the_eighth_level_reads():
    lines = chain(8)
    lines[-1] = lines[-1].replace(": word", ":")
    equals_pyyaml(lines)


def test_r057_r2_a_list_of_scalars_at_the_eighth_level_reads_and_at_the_ninth_is_refused():
    lines = chain(7)
    lines[-1] = lines[-1].replace(": word", ":")
    equals_pyyaml(lines + ["  " * 7 + "- x"])
    lines = chain(8)
    lines[-1] = lines[-1].replace(": word", ":")
    refused(head(*(lines + ["  " * 8 + "- x"])), 10)


def test_r057_r2_a_flow_list_at_the_eighth_level_is_no_level_of_its_own():
    lines = chain(8)
    lines[-1] = lines[-1].replace(": word", ": [x, z]")
    equals_pyyaml(lines)


def test_r057_r2_a_lone_carriage_return_ends_no_line():
    cr = chr(13)
    text = "---" + cr + "a: 1" + cr + "---" + cr + "body" + cr
    assert need("read_header")(text) == (None, text)
    refused("---\na: x" + cr + "y: 1\n---\n", 2)


@pytest.mark.parametrize("text", ["plain\n", "# Title\n---\na: b\n---\n", ""])
def test_r057_r2_a_headerless_body_keeps_its_byte_order_mark(text):
    assert need("read_header")(BOM + text) == (None, BOM + text)


FRAGMENTS = [
    "a: word", "b: 1", "a:", "c:", "  b: x", "  c:", "    d: z", "  - p", "  - k: 1", "    j: 2", "  - k:", "      m: 1",
    "- q", " e: 1", "   f: 1", "# note", "", "g: [x, 1]", 'h: "R&D"', "j:k",
    TAB, "a: 1" + TAB, "a: word" + chr(0xA0) + "#z", chr(0x3000), "# c" + chr(0x2028) + "b: 2",
]


def test_r057_r2_every_block_the_reader_accepts_of_these_fragments_equals_pyyaml():
    """Every sequence of up to three fragments: what read_header accepts, yaml.safe_load reads the same.

    A refusal is allowed (the subset is narrower); a different reading, or a reading of what pyyaml refuses, is not.
    """
    read, error = need("read_header"), need("HeaderError")
    sequences = [[a] for a in FRAGMENTS]
    sequences += [[a, b] for a in FRAGMENTS for b in FRAGMENTS]
    sequences += [[a, b, c] for a in FRAGMENTS for b in FRAGMENTS for c in FRAGMENTS]
    wrong = []
    for lines in sequences:
        try:
            ours = read(head(*lines))[0]
        except error:
            continue
        try:
            theirs = yaml.safe_load(block_of(lines))
        except yaml.YAMLError as caught:
            wrong.append((lines, ours, type(caught).__name__))
            continue
        if ours != ({} if theirs is None else theirs):
            wrong.append((lines, ours, theirs))
    assert not wrong, "%d blocks read otherwise than pyyaml, the first: %r" % (len(wrong), wrong[:5])


@pytest.mark.parametrize("key", ["open_issues", "workflows"])
def test_r057_r2_status_an_absent_list_line_agrees_with_the_empty_list(key):
    header = valid("project-status")
    header[key] = []
    fallback = fallback_status()
    del fallback[key]
    assert need("header_agrees")("project-status", header, fallback) == []
    fallback[key] = None
    assert need("header_agrees")("project-status", header, fallback) == []


@pytest.mark.parametrize("key", ["satisfies", "scope", "merge_unit"])
def test_r057_r2_brief_an_absent_list_line_agrees_with_the_empty_list(key):
    header = valid("brief")
    header[key] = []
    fallback = fallback_brief()
    del fallback[key]
    assert need("header_agrees")("brief", header, fallback) == []
    fallback[key] = None
    assert need("header_agrees")("brief", header, fallback) == []


def test_r057_r2_brief_a_null_merge_unit_agrees_with_an_absent_line_and_not_with_a_filled_one():
    header = valid("brief")
    header["merge_unit"] = None
    fallback = fallback_brief()
    del fallback["merge_unit"]
    assert need("header_agrees")("brief", header, fallback) == []
    fallback["merge_unit"] = ["TASK-046", "TASK-047"]
    assert need("header_agrees")("brief", header, fallback) == ["merge_unit"]


@pytest.mark.parametrize("key", ["ceiling_above_twice", "design_rounds_above_five", "review_rounds_above_ceiling"])
def test_r057_r2_run_parameters_an_absent_list_line_agrees_with_the_empty_list(key):
    header = valid("run-parameters")
    header[key] = []
    fallback = fallback_run_parameters()
    del fallback[key]
    assert need("header_agrees")("run-parameters", header, fallback) == []
    fallback[key] = None
    assert need("header_agrees")("run-parameters", header, fallback) == []


def test_r057_r2_a_filled_list_against_an_absent_line_disagrees_in_every_line_record():
    agrees = need("header_agrees")
    header = valid("run-parameters")
    header["review_rounds_above_ceiling"] = [{"id": "TASK-001", "rounds": 4, "words": "w", "date": "2026-11-04"}]
    fallback = fallback_run_parameters()
    del fallback["review_rounds_above_ceiling"]
    assert agrees("run-parameters", header, fallback) == ["review_rounds_above_ceiling"]
    header = valid("project-status")
    header["open_issues"] = ["ISS-001"]
    fallback = fallback_status()
    del fallback["open_issues"]
    assert agrees("project-status", header, fallback) == ["open_issues"]


def test_r057_r2_an_absent_agent_ceiling_agrees_with_null():
    header = valid("run-parameters")
    header["agent_ceiling"] = None
    fallback = fallback_run_parameters()
    del fallback["agent_ceiling"]
    assert need("header_agrees")("run-parameters", header, fallback) == []


def test_r057_r2_an_id_standing_on_one_side_at_the_same_position_disagrees():
    fallback = plan_fallback()
    fallback["stages"][0]["increments"][0]["id"] = "TASK-999"
    assert need("header_agrees")("build-plan", plan_header(), fallback) != []


def test_r057_r2_two_increments_in_another_order_disagree():
    agrees = need("header_agrees")
    other = dict(plan_header()["stages"][0]["increments"][0], id="TASK-047")
    header = plan_header()
    header["stages"][0]["increments"].append(other)
    fallback = plan_fallback()
    first = fallback["stages"][0]["increments"][0]
    fallback["stages"][0]["increments"] = [dict(first, id="TASK-047"), first]
    assert agrees("build-plan", header, fallback) != []


@pytest.mark.parametrize("key,prose,value", [
    ("scope", ["b.py"], ["a.py"]), ("kind", "group", "increment"), ("kind", None, "group"), ("satisfies", ["R-058"], ["R-057"]),
])
def test_r057_r2_a_merged_set_not_read_still_compares_every_field(key, prose, value):
    got = need("header_agrees")("build-plan", plan_header(**{key: value}), plan_fallback({key: prose}, merged=None))
    assert got == ["TASK-046 %s" % key]


def test_r057_r2_a_merged_set_not_read_unmarked_and_without_lines_agrees():
    assert need("header_agrees")("build-plan", historic_header(False), historic_fallback(None)) == []


def test_r057_r2_a_merged_set_not_read_a_mark_where_a_line_stands_disagrees_on_the_mark_alone():
    got = need("header_agrees")("build-plan", plan_header(historic=True), plan_fallback(merged=None))
    assert got == ["TASK-046 historic"]


# --- Review A's findings on round 1 and the supervisor's rulings on them (TASK-046-r2) ---
# enforces: docs/DESIGN.md, "The reader", the character rule; D-005, "Notes on values"; handoff/TASK-046-r2.md.

REFUSED_CHARACTERS = [
    (0x00, "NUL"), (0x07, "BEL"), (0x09, "tab"), (0x0C, "form feed"), (0x0D, "lone CR"), (0x1F, "C0"), (0x7F, "DEL"),
    (0x80, "C1"), (0x85, "NEL"), (0x2028, "LS"), (0x2029, "PS"), (0xD800, "surrogate"), (0xFFFE, "noncharacter"), (0xFFFF, "noncharacter"),
]


@pytest.mark.parametrize("code,name", REFUSED_CHARACTERS)
def test_r057_r2_a_refused_character_is_refused_at_its_own_line_in_a_string_and_in_a_comment(code, name):
    c = chr(code)
    refused(head("a: 1", 'b: "x%sy"' % c), 3)
    refused(head("a: 1", "# x%sy" % c), 3)
    refused(head("a: 1", "b: word # x%sy" % c), 3)


@pytest.mark.parametrize("code,name", REFUSED_CHARACTERS)
def test_r057_r2_a_refused_character_is_left_alone_in_a_body_and_a_headerless_text(code, name):
    c = chr(code)
    body = "x%sy\n" % c
    assert need("read_header")("---\na: 1\n---\n" + body) == ({"a": 1}, body)
    assert need("read_header")(body) == (None, body)


@pytest.mark.parametrize("line", [
    "a: word" + chr(0xA0) + "#z", "a: " + chr(0x2003) + "word", "k" + chr(0x2003) + ": v", chr(0x3000), "a: " + chr(0xE9), chr(0xE9) + ": v",
])
def test_r057_r2_outside_a_string_or_a_comment_only_ascii_is_read(line):
    refused(head(line), 2)


@pytest.mark.parametrize("lines", [
    ['a: "caf%s %s"' % (chr(0xE9), chr(0x2192))],
    ["# caf%s %s" % (chr(0xE9), chr(0xA0)), "a: word"],
    ["a: word # %s%s" % (chr(0x2003), chr(0x3000))],
    ['a: ["caf%s", z]' % chr(0xE9)],
    ["a:", '  - "caf%s"' % chr(0xE9)],
])
def test_r057_r2_other_text_stands_in_a_string_and_a_comment(lines):
    equals_pyyaml(lines)


@pytest.mark.parametrize("lines,line", [
    (["a: 1", TAB, "b: 2"], 3), ([TAB + "# c", "a: 1"], 2), (["a: word" + TAB], 2), (["a: word" + TAB + "# c"], 2),
    (["a:" + TAB + "word"], 2), (['a: "x"' + TAB + "# c"], 2),
])
def test_r057_r2_a_tab_anywhere_is_refused(lines, line):
    refused(head(*lines), line)


@pytest.mark.parametrize("name,lines,line", [
    ("two spaces after a dash before a key", ["a:", "  -  k: 1", "    j: 2"], 3),
    ("two spaces after a dash before a scalar", ["a:", "  -  x"], 3),
    ("a space before a colon", ["a : 1"], 2),
    ("a space before a list item key's colon", ["a:", "  - k : 1"], 3),
    ("a flow list as a list item", ["a:", "  - [x, z]"], 3),
    ("a flow list's trailing comma", ["a: [x, z,]"], 2),
    ("a dash and a space alone", ["a:", "  - "], 3),
    ("a dash alone", ["a:", "  -"], 3),
    ("no space between a colon and a comment", ["a:#x"], 2),
])
def test_r057_r2_a_form_the_subset_does_not_state_is_refused(name, lines, line):
    refused(head(*lines), line)


@pytest.mark.parametrize("item", ["'x: y'", "2026-11-04T10:00", "1:30", "b:c", "'word'", "yes"])
def test_r057_r2_a_list_item_refused_as_a_scalar_carries_the_advice(item):
    error = refused(head("a:", "  - " + item), 3)
    assert "quote" in str(error).lower(), "no advice to quote: %s" % error


def test_r057_r2_the_block_bound_is_exact():
    read = need("read_header")
    assert read("---\n# " + "x" * 262141 + "\n---\n")[0] == {}
    refused("---\n# " + "x" * 262142 + "\n---\n")


@pytest.mark.parametrize("opening,character,closing", [
    ('a: "', "{", '"'), ('a: "', "[", '"'), ('a: "', "*", '"'), ("# ", "{", ""), ("a: ", "{", ""),
])
def test_r057_r2_a_block_under_the_bound_is_read_in_linear_time(opening, character, closing):
    read, error, start = need("read_header"), need("HeaderError"), time.perf_counter()
    try:
        read("---\n" + opening + character * 262000 + closing + "\n---\n")
    except error:
        pass
    assert time.perf_counter() - start < 5, "read_header took over five seconds on a block under its bound"


@pytest.mark.parametrize("value", [b"---\na: 1\n---\n", None, 3])
def test_r057_r2_a_value_that_is_not_a_string_is_a_callers_mistake(value):
    with pytest.raises(TypeError):
        need("read_header")(value)


def test_r057_r2_the_filler_reads_as_an_absent_line_only_for_the_three_keys():
    agrees = need("header_agrees")
    assert agrees("build-plan", plan_header(scope=[]), plan_fallback({"scope": "none"})) == ["TASK-046 scope"]
    assert agrees("build-plan", plan_header(satisfies=[]), plan_fallback({"satisfies": "None"})) == ["TASK-046 satisfies"]


def test_r057_r2_an_inventory_section_that_is_none_is_absent():
    fallback = fallback_inventory()
    fallback["sections"]["deferred"] = None
    assert need("header_agrees")("inventory", valid("inventory"), fallback) == ["tables.deferred"]


@pytest.mark.parametrize("kind,key,reader", [
    ("project-status", "stage", fallback_status), ("project-status", "bridge_version", fallback_status),
    ("run-parameters", "stage_pause", fallback_run_parameters), ("run-parameters", "merge_authority", fallback_run_parameters),
    ("run-parameters", "refactoring_pass", fallback_run_parameters), ("run-parameters", "installer_verification", fallback_run_parameters),
    ("run-parameters", "parallel_increments", fallback_run_parameters), ("inventory", "development_data", fallback_inventory),
])
def test_r057_r2_a_never_null_strings_absent_line_is_the_empty_string(kind, key, reader):
    agrees = need("header_agrees")
    header = valid(kind)
    header[key] = ""
    assert need("check_header")(kind, header) == []
    fallback = reader()
    del fallback[key]
    assert agrees(kind, header, fallback) == []
    fallback[key] = None
    assert agrees(kind, header, fallback) == []
    assert agrees(kind, valid(kind), fallback) == [key]


@pytest.mark.parametrize("prose", ["-", "   ", " - ", "<none>", " <nothing> "])
def test_r057_r2_the_loop_guards_no_wait_forms_agree_with_the_empty_string(prose):
    fallback = fallback_status()
    fallback["awaiting_user_on"] = prose
    assert need("header_agrees")("project-status", valid("project-status"), fallback) == []


def test_r057_r2_angle_brackets_are_stripped_at_the_ends_only():
    fallback = fallback_status()
    fallback["awaiting_user_on"] = "no<ne of it"
    assert need("header_agrees")("project-status", valid("project-status"), fallback) == ["awaiting_user_on"]


@pytest.mark.parametrize("prose,value", [("Group", "group"), (" group ", "group"), ("", "increment"), ("   ", "increment")])
def test_r057_r2_kind_read_as_the_plan_check_reads_it(prose, value):
    assert need("header_agrees")("build-plan", plan_header(kind=value), plan_fallback({"kind": prose})) == []


def two_stage_plan():
    header, fallback = plan_header(), plan_fallback()
    second = dict(header["stages"][0]["increments"][0], id="TASK-047", title="Second")
    header["stages"].append({"name": "Later", "demonstration": True, "increments": [second]})
    fallback["stages"].append({
        "name": "Later", "demonstration": "shown", "increments": [{"id": "TASK-047", "title": "Second", "fields": {"scope": ["a.py"], "satisfies": ["R-057"]}}],
    })
    return header, fallback


def test_r057_r2_an_extra_increment_masks_nothing_else():
    header, fallback = two_stage_plan()
    fallback["stages"][0]["increments"][0]["title"] = "Changed"
    fallback["stages"][0]["increments"].append({"id": "TASK-099", "title": "x", "fields": {}})
    fallback["stages"][1]["increments"][0]["title"] = "Changed too"
    got = need("header_agrees")("build-plan", header, fallback)
    assert "TASK-046 title" in got and "TASK-047 title" in got and len(got) == 3


def test_r057_r2_an_extra_stage_masks_nothing_else():
    header, fallback = two_stage_plan()
    fallback["stages"][0]["increments"][0]["title"] = "Changed"
    fallback["stages"].append({"name": "Third", "demonstration": None, "increments": []})
    got = need("header_agrees")("build-plan", header, fallback)
    assert "TASK-046 title" in got and len(got) == 2


def test_r057_r2_run_parameters_compare_every_key_of_the_schema():
    fallback = fallback_run_parameters()
    got = need("header_agrees")("run-parameters", {"record": "run-parameters", "header": 1}, fallback)
    assert set(got) == {k for k, v in fallback.items() if v not in (None, "", [])}


def test_r057_r2_inventory_compares_every_section_of_either_side():
    agrees = need("header_agrees")
    header = valid("inventory")
    header["tables"] = {}
    assert sorted(agrees("inventory", header, fallback_inventory())) == ["tables.decisions", "tables.deferred", "tables.features", "tables.resources"]
    fallback = fallback_inventory()
    fallback["sections"]["surplus"] = ["A"]
    assert agrees("inventory", valid("inventory"), fallback) == ["tables.surplus"]


def test_r057_r2_two_sections_differing_give_columns_once():
    fallback = fallback_inventory()
    fallback["sections"]["features"] = ["Other"]
    fallback["sections"]["resources"] = ["Other"]
    assert need("header_agrees")("inventory", valid("inventory"), fallback) == ["columns"]


def test_r057_r2_statuses_in_another_order_are_no_finding():
    header = valid("requirements")
    header["statuses"] = ["dropped", "planned", "built", "deferred"]
    assert need("check_header")("requirements", header) == []


@pytest.mark.parametrize("statuses", [
    ["planned", "built", "deferred", "planned"],
    ["planned", "built", "deferred", {"a": 1}],
    ["planned", "built", "deferred", ["dropped"]],
    ["planned", "built", "deferred", None],
])
def test_r057_r2_statuses_with_a_repeat_or_a_nested_item_are_a_finding_and_no_exception(statuses):
    header = valid("requirements")
    header["statuses"] = statuses
    assert need("check_header")("requirements", header) != []


@pytest.mark.parametrize("kind", [("a", "b"), ("a",), None, 3, ""])
def test_r057_r2_a_kind_with_no_table_is_a_finding_whatever_it_is(kind):
    assert need("check_header")(kind, {}) != []


@pytest.mark.parametrize("key", ["record", "statuses", "roles", "columns"])
def test_r057_r2_a_missing_key_is_one_finding(key):
    header = valid("requirements")
    del header[key]
    got = need("check_header")("requirements", header)
    assert len(got) == 1 and key in got[0], got


def test_r057_r2_a_null_is_a_wrong_type_never_a_missing_key():
    header = valid("brief")
    header["scope"] = None
    got = need("check_header")("brief", header)
    assert len(got) == 1 and "scope" in got[0] and "missing" not in got[0], got


def test_r057_r2_a_value_outside_its_set_says_so():
    header = valid("project-status")
    header["phase"] = "elsewhere"
    got = need("check_header")("project-status", header)
    assert len(got) == 1 and "phase" in got[0] and "set" in got[0], got


def test_r057_r2_a_wrong_record_is_one_finding():
    header = valid("brief")
    header["record"] = "inventory"
    got = need("check_header")("brief", header)
    assert len(got) == 1 and "record" in got[0], got


# --- what round 2 read wrongly: the supervisor's second probe (TASK-046-r3) ---
# enforces: docs/DESIGN.md, "The reader" (what the subset reads, indentation, comments, the character rule, a line ends
# at LF or CRLF); handoff/TASK-046-r2.md's rulings it repeats; D-005, "Notes on values" (Kind), and the value rule on header.
# The earlier tests compared what the reader accepts and let every refusal pass, so a false refusal went unseen.
# Here every shape of the stated subset is written out and must be read as written, in both line endings.

E_ACUTE = chr(0xE9)
FLOW_LIST = ["x", "z"]
BLOCK_LIST = ["p", "q"]
LEAVES = ["word", 1, None, FLOW_LIST, "R&D # x" + E_ACUTE]


def scalar_text(value):
    if isinstance(value, str) and not value.isalnum():
        return '"%s"' % value
    return str(value)


def key_lines(start, value, column):
    """The lines of one key, `start` holding it up to its colon, `column` the column its name stands at."""
    if value is None:
        return [start]
    if value == FLOW_LIST:
        return [start + " [x, z]"]
    if isinstance(value, dict):
        return [start] + mapping_lines(value, column + 2)
    if isinstance(value, list):
        return [start] + list_lines(value, column + 2)
    return [start + " " + scalar_text(value)]


def mapping_lines(mapping, column):
    lines = []
    for key, value in mapping.items():
        lines += key_lines(" " * column + key + ":", value, column)
    return lines


def list_lines(items, column):
    lines = []
    for item in items:
        if isinstance(item, dict):
            keys = list(item)
            lines += key_lines(" " * column + "- " + keys[0] + ":", item[keys[0]], column + 2)
            lines += mapping_lines({k: item[k] for k in keys[1:]}, column + 2)
        else:
            lines.append(" " * column + "- " + scalar_text(item))
    return lines


def subset_shapes():
    first = list(LEAVES) + [BLOCK_LIST, ["p", {"k": "word"}], [{"k": 1}, {"k": None}]]
    first += [{"k": v} for v in LEAVES]
    first += [{"k": v, "j": w} for v in LEAVES for w in LEAVES]
    first += [[{"k": v}] for v in LEAVES]
    first += [[{"k": v, "j": w}] for v in LEAVES for w in LEAVES]
    second = []
    for v in first:
        second += [
            {"k": v}, {"k": v, "j": "word"}, [{"k": v}], [{"k": v, "j": "word"}], [{"k": "word", "j": v}],
            [{"k": v, "j": "word"}, {"k": v}], {"k": [{"k": v, "j": "word"}], "j": "word"},
        ]
    return first + second


SUBSET_SHAPES = subset_shapes()
TRAILING = " # caf" + E_ACUTE + ' it"s: [x'
BETWEEN_LINES = {
    "as written": None,
    "a blank line": "",
    "spaces alone": "   ",
    "a comment at column 0": "# note",
    "a comment at an odd column": "   # note",
    "non-ASCII and a quote in a comment at column 0": "# caf" + E_ACUTE + ' it"s',
    "non-ASCII and a quote in a deep comment": "          # caf" + E_ACUTE + ' it"s',
}


def with_between(lines, between):
    if between is None:
        return list(lines)
    out = [between]
    for line in lines:
        out += [line, between]
    return out


def read_as_written_failures(lines_of, ending):
    read, error = need("read_header"), need("HeaderError")
    wrong = []
    for shape in SUBSET_SHAPES:
        document = {"a": shape}
        lines = lines_of(mapping_lines(document, 0))
        assert yaml.safe_load(block_of(lines)) == document, "the test's own writer is wrong: %r" % (lines,)
        text = ("---\n" + block_of(lines) + "---\nbody\n").replace("\n", ending)
        try:
            header = read(text)[0]
        except error as caught:
            wrong.append((lines, str(caught)))
            continue
        if header != document:
            wrong.append((lines, header))
    return wrong


@pytest.mark.parametrize("ending", ["\n", "\r\n"], ids=["LF", "CRLF"])
@pytest.mark.parametrize("between", list(BETWEEN_LINES))
def test_r057_r3_every_shape_of_the_subset_is_read_as_written(between, ending):
    wrong = read_as_written_failures(lambda lines: with_between(lines, BETWEEN_LINES[between]), ending)
    assert not wrong, "%d of %d shapes not read as written, the first: %r" % (len(wrong), len(SUBSET_SHAPES), wrong[:3])


@pytest.mark.parametrize("ending", ["\n", "\r\n"], ids=["LF", "CRLF"])
def test_r057_r3_a_comment_after_every_line_of_every_shape_is_read_as_written(ending):
    wrong = read_as_written_failures(lambda lines: [line + TRAILING for line in lines], ending)
    assert not wrong, "%d of %d shapes not read as written, the first: %r" % (len(wrong), len(SUBSET_SHAPES), wrong[:3])


@pytest.mark.parametrize("moved", [1, 3, -1], ids=["one deeper", "three deeper", "one shallower"])
def test_r057_r3_a_line_at_an_odd_column_is_refused_at_that_line_in_every_shape(moved):
    read, error = need("read_header"), need("HeaderError")
    wrong = []
    for shape in SUBSET_SHAPES:
        lines = mapping_lines({"a": shape}, 0)
        for i, line in enumerate(lines):
            if moved < 0 and not line.startswith(" "):
                continue
            changed = list(lines)
            changed[i] = line[1:] if moved < 0 else " " * moved + line
            try:
                wrong.append((changed, read(head(*changed))[0]))
            except error as caught:
                if caught.line != i + 2:
                    wrong.append((changed, str(caught)))
    assert not wrong, "%d not refused at the moved line, the first: %r" % (len(wrong), wrong[:3])


@pytest.mark.parametrize("lines", [
    ["a:", "  - k:", "      m: 1", "    j: 2"],
    ["a:", "  - k:", "      - p", "    j: 2"],
    ["a:", "  - k:", "      - p", "      - q", "    j:", "      m: 1", "    i: 3", "  - k: 4"],
    ["a:", "  - k:", "", "      m: 1"],
    ["a:", "  - k:", "      # a comment", "      m: 1"],
    ["a:", "  - k:", "# a comment", "      - p"],
])
def test_r057_r3_a_list_items_first_key_keeps_its_child_and_its_later_keys(lines):
    equals_pyyaml(lines)


@pytest.mark.parametrize("lines", [
    ["a:", "    b: x"],
    ["a:", "    - x"],
    ["a:", "  - k:", "        - x"],
    ["a:", "  - k:", "        m: 1"],
    ["a:", "  - k: 1", "      j: 2"],
    ["a:", "  - k:", "", "        - x"],
    ["a:", "  - k:", "      m:", "          - x"],
])
def test_r057_r3_a_child_two_levels_deeper_is_refused_at_its_line(lines):
    refused(head(*lines), len(lines) + 1)


@pytest.mark.parametrize("lines", [
    ["a:", "  - k:", "      m: 1", "    k: 2"],
    ["a:", "  - k:", "      - p", "    j: 1", "    j: 2"],
    ["a:", "  - j: 1", "    k:", "      m: 1", "    j: 2"],
])
def test_r057_r3_a_duplicate_key_after_a_nested_first_key_is_refused(lines):
    refused(head(*lines), len(lines) + 1)


def item_chain(levels):
    """`levels` containers, the root and the list and the item among them, through a list item's first key."""
    lines, column, level = ["a:", "  - k:"], 6, 4
    while level < levels:
        lines.append(" " * column + "b%d:" % level)
        column += 2
        level += 1
    lines.append(" " * column + "b%d: word" % level)
    return lines


def test_r057_r3_nesting_through_a_list_items_first_key_is_counted_alike():
    equals_pyyaml(item_chain(8))
    lines = item_chain(9)
    refused(head(*lines), len(lines) + 1)


@pytest.mark.parametrize("ending", ["\n", "\r\n"], ids=["LF", "CRLF"])
@pytest.mark.parametrize("lines,expected", [
    (["a: 1 # note", "b: 2"], {"a": 1, "b": 2}),
    (["# note", "a: 1"], {"a": 1}),
    (["a:", "  # note", "  b: 1"], {"a": {"b": 1}}),
    (['a: "x" # note', "b: [p, q] # note"], {"a": "x", "b": ["p", "q"]}),
    (["a: 1", "# caf" + E_ACUTE], {"a": 1}),
    ([" # caf" + E_ACUTE, "a: 1"], {"a": 1}),
])
def test_r057_r3_a_comment_is_read_past_in_either_line_ending(lines, expected, ending):
    text = ("---\n" + block_of(lines) + "---\nbody\n").replace("\n", ending)
    assert need("read_header")(text) == (expected, "body" + ending)


@pytest.mark.parametrize("ending", ["\n", "\r\n"], ids=["LF", "CRLF"])
@pytest.mark.parametrize("code,name", REFUSED_CHARACTERS)
def test_r057_r3_a_refused_character_is_refused_in_every_place_a_comment_stands(code, name, ending):
    c = chr(code)
    for lines in (
        ["# x%sy" % c, "a: 1"],
        ["a: 1", "# x%sy" % c],
        ["a: 1", "   # x%sy" % c],
        ["a: 1 # x%sy" % c],
        ['# it"s', "a: 1 # x%sy" % c],
        ["a:", "  - k:", "      # x%sy" % c, "      m: 1"],
    ):
        at = next(i for i, line in enumerate(lines) if c in line) + 2
        refused(("---\n" + block_of(lines) + "---\n").replace("\n", ending), at)


@pytest.mark.parametrize("lines", [
    ['a: "x""'],
    ['a: """'],
    ['a: """"'],
    ['a: "x"""'],
    ['a: ""x'],
    ['a: "x""y"'],
    ["z:", '  - k: "x""'],
    ["z:", '  - "x""'],
    ['a: ["x""]'],
    ['a: ["x"", z]'],
    ['a: "x', 'b: y"'],
])
def test_r057_r3_a_doubled_quote_is_no_form_of_the_subset(lines):
    at = next(i for i, line in enumerate(lines) if '"' in line) + 2
    refused(head(*lines), at)


@pytest.mark.parametrize("lines", [['a: ""'], ['a: "" # note'], ['a: ["", ""]'], ["z:", '  - ""'], ["z:", '  - k: ""']])
def test_r057_r3_the_empty_string_still_reads(lines):
    equals_pyyaml(lines)


@pytest.mark.parametrize("key,value", [
    ("header", 2), ("header", "1"), ("header", None), ("header", [1]), ("record", 3), ("record", None), ("record", "brief"), ("record", "bogus"),
])
def test_r057_r3_a_wrong_record_or_header_value_is_one_finding(key, value):
    header = valid("requirements")
    header[key] = value
    got = need("check_header")("requirements", header)
    assert len(got) == 1 and key in got[0], got


@pytest.mark.parametrize("key", ["header", "record"])
def test_r057_r3_a_missing_record_or_header_is_one_finding(key):
    header = valid("brief")
    del header[key]
    got = need("check_header")("brief", header)
    assert len(got) == 1 and key in got[0], got


@pytest.mark.parametrize("prose", ["bogus", "Merge unit", "increment group"])
def test_r057_r3_a_kind_the_plan_check_would_not_accept_disagrees(prose):
    assert need("header_agrees")("build-plan", plan_header(), plan_fallback({"kind": prose})) == ["TASK-046 kind"]


# --- Review A's and the security audit's findings on round 2, and the rulings on them (TASK-046-r3) ---
# enforces: docs/DESIGN.md, "The reader" and its Security paragraph; D-005, "Notes on values"; handoff/TASK-046.md, Requirements 1, 2, 18, 29, 33.

BACKSLASH = chr(92)


def text_with(lines, ending="\n"):
    return ("---\n" + block_of(lines) + "---\n").replace("\n", ending)


@pytest.mark.parametrize("ending", ["\n", "\r\n"], ids=["LF", "CRLF"])
@pytest.mark.parametrize("code,name", REFUSED_CHARACTERS)
def test_r057_r3_a_quote_in_a_comment_opens_nothing_and_a_backslash_skips_nothing(code, name, ending):
    """Both reviewers: a `# "` line opened a string in the scanner, whose backslash skipped a line separator, hiding key b."""
    c = chr(code)
    for lines in (
        ["a: 1", '# "' + BACKSLASH + c + "b: 2"],
        ["z: 1", '# "', "c: 2 # " + BACKSLASH + c + "b: 3"],
        ["z: 1", '# "', "agent_ceiling: 5 # " + BACKSLASH + c + "review_rounds_above_ceiling: 9"],
        ['# it"s', 'a: "x' + BACKSLASH + c + 'y"'],
        ['a: "x' + BACKSLASH + c + 'y"'],
        ['# "', 'a: "x"', "b: 1 # " + BACKSLASH + c + "y"],
    ):
        at = next(i for i, line in enumerate(lines) if c in line) + 2
        refused(text_with(lines, ending), at)


@pytest.mark.parametrize("space", [chr(0xA0), chr(0x3000), chr(0x2003)], ids=["NBSP", "ideographic", "em"])
def test_r057_r3_a_unicode_space_is_no_whitespace_whatever_a_comment_before_it_holds(space):
    """Both reviewers: past the scanner, a bare strip() read `round: <NBSP>5` as the integer 5, and pyyaml as a string."""
    for lines, at in (
        (["z: 0", '# "', "a: 1" + space], 4),
        (["z: 0", '# "', "a: word" + space], 4),
        (["z: 0", '# "', "b: [x" + space + ", q]"], 4),
        (["z: 0", '# "', space, "b: 1"], 4),
        (["z: 0", '# "', "round: " + space + "5"], 4),
        (["z: 0", '# "', "x: " + space + "true" + space], 4),
        (["z: 0", '# "', "a:", "  " + space], 5),
        (["z: 0", '# "', "a: 3", "  " + space], 5),
        (['# "', 'a: "x"', "b: " + space], 4),
        (['a: "x""', "b: 1" + space], None),
    ):
        refused(text_with(lines), at)


def test_r057_r3_a_refused_character_is_named_at_its_own_line_after_a_backslash_at_a_line_end():
    refused(text_with(["z: 0", '# "' + BACKSLASH, "a: 1", "b: " + chr(0x85)]), 5)
    refused(text_with(['a: "x' + BACKSLASH, "b: 1", TAB]), 4)
    refused(text_with(["z: 1", '# "' + BACKSLASH] + ["# " + BACKSLASH] * 50 + [TAB]), 54)


MEBIBYTE = 1024 * 1024


@pytest.mark.parametrize("text", [
    "\n" * MEBIBYTE,
    "x\n" * (MEBIBYTE // 2),
    "---\na: 1\n---\n" + "\n" * MEBIBYTE,
    "---\na: 1\n---\n" + "x\n" * (MEBIBYTE // 2),
    "---\n" + "\n" * MEBIBYTE,
    "---\n" + "\n" * MEBIBYTE + "---\n",
    "---\n" + "# x\n" * (MEBIBYTE // 4) + "---\n",
], ids=["headerless newlines", "headerless lines", "body newlines", "body lines", "unterminated", "over the bound", "over the bound, comments"])
def test_r057_r3_reading_a_text_holds_no_more_than_about_the_text_in_memory(text):
    """The security audit: a tuple per line of the whole file, 437 MB for 4 MB of newlines, with a MemoryError outside the handlers."""
    read, error = need("read_header"), need("HeaderError")
    tracemalloc.start()
    try:
        try:
            read(text)
        except error:
            pass
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak <= 3 * len(text), "peak %d bytes for a text of %d characters" % (peak, len(text))


@pytest.mark.parametrize("last", [TAB, chr(0xD800), chr(0x2028)], ids=["tab", "surrogate", "LS"])
def test_r057_r3_the_byte_bound_is_held_before_the_characters_are_read(last):
    lines = ["# " + "x" * 1000] * 300 + [last]
    refused(text_with(lines), 2)


def test_r057_r3_a_key_is_at_most_pyyamls_limit():
    equals_pyyaml(["a" * 1024 + ": 1"])
    refused(head("a" * 1025 + ": 1"), 2)
    equals_pyyaml(["z:", "  - " + "a" * 1024 + ": 1"])
    refused(head("z:", "  - " + "a" * 1025 + ": 1"), 3)


@pytest.mark.parametrize("lines", [["a: b c"], ["z:", "  - b c"], ["z:", "  - k: b c"], ["z:", "  - a b: c"]])
def test_r057_r3_a_word_with_a_space_carries_the_advice_and_is_not_called_multi_line(lines):
    message = str(refused(head(*lines), len(lines) + 1))
    assert "quote" in message and "multi-line" not in message, message


@pytest.mark.parametrize("line", ["a: [] x", "a: [x]#c", "a: [x] y"])
def test_r057_r3_a_closed_flow_list_with_text_after_it_is_not_called_multi_line(line):
    message = str(refused(head(line), 2))
    assert "multi-line" not in message, message


@pytest.mark.parametrize("lines", [["a: R&D"], ["a: x&y"], ["a: x!!y"], ["a: x*y"], ["z:", "  - R&D"], ["z:", "  - k: R&D"]])
def test_r057_r3_a_word_holding_a_marker_is_a_plain_scalar_with_the_advice(lines):
    message = str(refused(head(*lines), len(lines) + 1))
    assert "quote" in message and "anchor" not in message and "alias" not in message and "tag" not in message, message


@pytest.mark.parametrize("statuses,word", [
    (["planned", "built", "deferred", "bogus"], "set"),
    (["planned", "built", "deferred", "planned"], None),
    (["planned", "built", "deferred"], None),
    (["planned", "built", "deferred", {"a": 1}], None),
    (["planned", "built", "deferred", ["dropped"]], None),
    (["planned", "built", "deferred", None], None),
    ("planned", None),
    (None, None),
    ({"a": 1}, None),
])
def test_r057_r3_one_fault_in_statuses_is_one_finding(statuses, word):
    header = valid("requirements")
    header["statuses"] = statuses
    got = need("check_header")("requirements", header)
    assert len(got) == 1 and "statuses" in got[0], got
    if word:
        assert word in got[0], got


def test_r057_r3_a_key_of_any_type_is_a_finding_and_no_exception():
    check = need("check_header")
    header = valid("brief")
    header[(1, 2)] = 3
    assert len(check("brief", header)) == 1
    header = valid("requirements")
    header["roles"] = dict(header["roles"])
    header["roles"][(1, 2)] = "x"
    assert len(check("requirements", header)) == 1


def test_r057_r3_a_role_is_one_finding_whichever_its_fault():
    check = need("check_header")
    header = valid("requirements")
    header["roles"] = dict(header["roles"], extra="nope")
    got = check("requirements", header)
    assert len(got) == 1 and "extra" in got[0], got
    header = valid("requirements")
    header["roles"] = dict(header["roles"], id="nope")
    got = check("requirements", header)
    assert len(got) == 1 and "id" in got[0], got
    header = valid("requirements")
    header["roles"] = dict(header["roles"], id=3)
    got = check("requirements", header)
    assert len(got) == 1 and "id" in got[0], got


@pytest.mark.parametrize("columns", [[{"a": 1}], [["x"]], [None], "text", 5])
def test_r057_r3_columns_of_the_wrong_shape_are_a_finding_and_no_exception(columns):
    header = valid("requirements")
    header["columns"] = columns
    assert need("check_header")("requirements", header) != []


def test_r057_r3_many_roles_and_columns_are_checked_in_about_linear_time():
    header = valid("requirements")
    header["columns"] = ["c%d" % i for i in range(20000)]
    header["roles"] = {"r%d" % i: "absent%d" % i for i in range(20000)}
    started = time.perf_counter()
    assert need("check_header")("requirements", header) != []
    assert time.perf_counter() - started < 2.0


@pytest.mark.parametrize("key,value", [("parallel", False), ("parent", None), ("deferred", None), ("depends_on", []), ("diagrams", [])])
def test_r057_r3_a_blank_field_line_reads_as_an_absent_line(key, value):
    """The ruling on Review A's S2: plan-check.py's FIELD_RX gives "" for a blank line, and its `or` defaults read that as absent."""
    assert need("header_agrees")("build-plan", plan_header(**{key: value}), plan_fallback({key: ""})) == []


def test_r057_r3_a_blank_parallel_line_disagrees_with_a_true_header_and_a_word_with_either():
    agrees = need("header_agrees")
    assert agrees("build-plan", plan_header(parallel=True), plan_fallback({"parallel": ""})) == ["TASK-046 parallel"]
    assert agrees("build-plan", plan_header(parallel=False), plan_fallback({"parallel": "maybe"})) == ["TASK-046 parallel"]
    assert agrees("build-plan", plan_header(parallel=True), plan_fallback({"parallel": "maybe"})) == ["TASK-046 parallel"]


def test_r057_r3_a_merge_unit_read_as_a_tuple_compares_as_a_list():
    """Review A's S1: bridge_env.merge_unit_ids returns a tuple, and the header holds a list."""
    agrees = need("header_agrees")
    header = valid("brief")
    header["merge_unit"] = ["TASK-046", "TASK-047"]
    assert agrees("brief", header, dict(fallback_brief(), merge_unit=("TASK-046", "TASK-047"))) == []
    assert agrees("brief", header, dict(fallback_brief(), merge_unit=("TASK-047", "TASK-046"))) == ["merge_unit"]
    assert agrees("brief", header, dict(fallback_brief(), merge_unit=("TASK-046",))) == ["merge_unit"]


@pytest.mark.parametrize("lines", [
    ["1: x"], ["aB: 1"], ['"a": 1'], ["z:", "  - on: x"], ["z:", "  -x"], ['a: "x' + BACKSLASH], ['a: ["x]'], ['a: ["x" q]'],
    ["a: ['x']"], ["a: [x"], ['a: "x' + BACKSLASH + 'n"'],
])
def test_r057_r3_these_forms_are_refused_at_their_line(lines):
    refused(head(*lines), len(lines) + 1)


@pytest.mark.parametrize("lines", [
    ['a: ["x' + BACKSLASH + '"y", z]'],
    ["z:", '  - "a' + BACKSLASH + '"b"'],
    ["z:", '  - "a' + BACKSLASH + '"b: c"'],
    ["z:", '  - k: "a' + BACKSLASH + '"b: c"'],
    ['a: "b' + BACKSLASH + BACKSLASH + '" # c'],
    ['a: ["b' + BACKSLASH + BACKSLASH + '", z]'],
    ['a: "x # y" # z', 'b: "c: d"'],
])
def test_r057_r3_an_escaped_quote_ends_no_string_in_any_of_the_readings(lines):
    equals_pyyaml(lines)


@pytest.mark.parametrize("header", [
    {"record": "build-plan", "header": 1, "stages": ["x"]},
    {"record": "build-plan", "header": 1, "stages": [{"name": "S", "demonstration": True, "increments": ["x"]}]},
    {"record": "build-plan", "header": 1, "stages": "x"},
    {"record": "inventory", "header": 1, "reflected_through": None, "development_data": "", "tables": "x"},
    {"record": "inventory", "header": 1, "reflected_through": None, "development_data": "", "tables": {"features": "x", "resources": 1, "decisions": None, "deferred": []}},
    {"record": "requirements", "header": 1, "columns": [], "roles": "x", "statuses": []},
])
def test_r057_r3_a_nested_value_of_the_wrong_shape_is_a_finding_and_no_exception(header):
    assert need("check_header")(header["record"], header) != []


@pytest.mark.parametrize("header", [[], "x", None, 3])
def test_r057_r3_a_header_that_is_no_mapping_is_a_finding_and_no_exception(header):
    assert need("check_header")("brief", header) != []


def test_r057_r3_a_brief_whose_name_cannot_be_read_disagrees_on_id_and_round():
    got = need("header_agrees")("brief", valid("brief"), dict(fallback_brief(), name="notes"))
    assert got == ["id", "round"]


def test_r057_r3_a_kind_with_no_agreement_is_said():
    assert need("header_agrees")("nonsense", {}, {}) != []


def test_r057_r3_a_stage_or_an_increment_on_the_header_side_only_is_said():
    agrees = need("header_agrees")
    header, fallback = two_stage_plan()
    del fallback["stages"][1]
    assert agrees("build-plan", header, fallback) == ["Later name"]
    header, fallback = two_stage_plan()
    fallback["stages"][1]["increments"] = []
    assert agrees("build-plan", header, fallback) == ["TASK-047 id"]


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
    lines.append("%s- word" % indent)
    assert need("read_header")(head(*lines))[0] is not None
    lines[-1] = "%s- leaf: word" % indent
    refused(head(*lines), 7)


def test_r057_a_key_pyyaml_would_type_is_refused():
    refused(head("on: word"), 2)


def test_r057_an_integer_over_the_digit_limit_is_a_header_error():
    err = refused(head("a: " + "9" * 5000), 2)
    assert "integer" in str(err).lower()


def test_r057_a_lone_surrogate_in_the_block_is_a_header_error():
    refused(head("a: 1", 'b: "x%sy"' % chr(0xD800)), 3)


def test_r057_a_form_feed_inside_a_quoted_string_is_refused_at_its_line():
    refused(head('a: "a' + chr(0x0C) + 'b"'), 2)


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
    got = need("header_agrees")("build-plan", historic_header(True), fallback)
    assert set(got) == {"TASK-046 historic", "TASK-046 scope"}


def test_r057_flow_mapping_refusal_names_flow_mapping():
    err = refused(head("a: {b: c}"), 2)
    assert "flow mapping" in str(err).lower()

