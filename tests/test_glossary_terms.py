"""The glossary gains the plan's terms (TASK-009).

enforces: docs/REQUIREMENTS.md R-028 (the glossary gains the terms of this plan): bridge/cursor-bridge/Glossary.md defines
the closed set of release B's terms, each in a table row of its own with a definition, and its Phase entry lists all
eight values the status template allows. A term is a row whose first cell is the term in bold.
"""
import pathlib
import re

import pytest

GLOSSARY = pathlib.Path(__file__).resolve().parent.parent / "bridge" / "cursor-bridge" / "Glossary.md"

CLOSED_SET = [
    "Conditional workflow", "Type workflow", "Sub-workflow", "Trait", "Trait addition", "Extension point",
    "Phase module", "Main workflow core", "Product type", "Sub-type", "Replace", "Set", "Add", "Open list",
    "Workflow check", "Workflow name", "Sub-workflow name", "Compaction-survival list",
]
PHASES = ["intake", "design", "mockups", "planning", "configuration", "building", "done", "changing"]
ROW = re.compile(r"^\| \*\*(?P<term>[^*|]+)\*\* \| (?P<meaning>[^|]*?) \|")


def entries():
    """Every glossary row's term and its meaning (the second cell), in file order."""
    found = []
    for line in GLOSSARY.read_text(encoding="utf-8").split("\n"):
        m = ROW.match(line.rstrip("\r"))
        if m:
            found.append((m.group("term"), m.group("meaning").strip()))
    return found


def test_r028_glossary_rows_are_read():
    terms = [term for term, _ in entries()]
    assert "Phase" in terms and "Supervisor" in terms, "the row reader must see the glossary's existing entries"


@pytest.mark.parametrize("term", CLOSED_SET)
def test_r028_each_term_has_one_definition(term):
    meanings = [meaning for t, meaning in entries() if t == term]
    assert len(meanings) == 1, "%r must be defined exactly once, found %d" % (term, len(meanings))
    words = meanings[0].split()
    assert len(words) >= 8, "%r needs a definition, not a label: %r" % (term, meanings[0])
    opening = [w.strip(".,;:*_`").lower() for w in words[:len(term.split())]]
    assert opening != term.lower().split(), "a definition does not open with its own term: %r" % meanings[0]


def test_r028_phase_lists_all_eight_template_values():
    """The Phase entry's list is exactly the eight values, in the template's order: nothing missing, nothing added."""
    meanings = [meaning for t, meaning in entries() if t == "Phase"]
    assert len(meanings) == 1
    m = re.search(r"`Phase:` line: ([^.]+)\.", meanings[0])
    assert m, "the Phase entry lists the values after \"`Phase:` line: \": %r" % meanings[0]
    assert [v.strip() for v in m.group(1).split(",")] == PHASES, m.group(1)


def test_r028_phase_values_match_the_status_template():
    """The eight values are the ones the core's status template allows, so the glossary and the template agree."""
    core = (GLOSSARY.parent.parent / "commands" / "supervisor.md").read_text(encoding="utf-8")
    m = re.search(r"^Phase: <([^>]+)>", core, re.M)
    assert m, "the status template's Phase line"
    template = [v.strip() for v in m.group(1).split("|")]
    assert template == PHASES, template
