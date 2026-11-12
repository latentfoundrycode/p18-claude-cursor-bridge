"""Stage B3's least-confident items 1 and 2, settled by tests before stage B4's first delegation (FIX-004).

enforces: docs/HARDENING.md, Stage B3, "Least confident (stage close, 2026-10-24)", items 1 and 2.

Item 1: the phase-module tests read a heading as trace-check.py reads one (tests/phase_modules.py's trace_headings,
which headings(), section() and section_span() use), so an indented heading of an excused title, which trace-check.py
excuses text under, is seen by every test that reads a module's headings or sections.
Item 2: every section an entry of trace-exceptions.md excuses in a phase module (the interface variant files apart,
which test_phase_modules_close.py pins) has one heading of its title and is pinned by its length and sha256, the set of
pins derived from the entries, so an edit of an excused passage fails until its pin is re-taken with the edit's own
`reword` entry, and a new entry fails until its section is pinned here.

Supervisor-written; no builder run."""
import importlib.util
import os

import pytest

from phase_modules import BRIDGE, PHASES, module, headings, section

TRACE_CHECK = os.path.join(BRIDGE, "cursor-bridge", "trace-check.py")


def trace_check():
    spec = importlib.util.spec_from_file_location("trace_check_b3_least_confident", TRACE_CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def phase_files():
    out = []
    for root, _dirs, files in os.walk(PHASES):
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.relpath(os.path.join(root, f), PHASES).replace(os.sep, "/"))
    return sorted(out)


@pytest.mark.parametrize("rel", phase_files())
def test_item1_the_helpers_read_each_module_s_headings_as_trace_check_does(rel):
    """Item 1: for every file under workflow/phases/, the headings the phase-module tests read are the headings
    trace-check.py's parse_units reads, in order, so no heading it excuses text under escapes the tests."""
    text = module(rel)
    _units, theirs = trace_check().parse_units(text)
    assert [t for _level, t in headings(text)] == theirs, rel


def test_item1_the_round4_probe_is_seen():
    """Item 1's own proof, stage B3's review round 4 (Review A, tests): an indented ` ### Keeping the position`, a new
    entry's title, added to a copy of configuration.md is a heading trace-check.py excuses text under; the column-0
    reading the tests used before missed it, and every phase-module test passed. Now headings() lists it, so the
    STRUCTURE tests' comparison fails, and section() refuses the title, which now has two headings."""
    text = module("configuration")
    probe = text.rstrip("\n") + "\n\n ### Keeping the position\n\nA paragraph a new entry would excuse unseen.\n"
    assert [l for l in probe.split("\n") if l == "### Keeping the position"] == ["### Keeping the position"]
    _units, theirs = trace_check().parse_units(probe)
    assert theirs.count("Keeping the position") == 2
    assert headings(probe) == headings(text) + [(3, "Keeping the position")]
    with pytest.raises(AssertionError):
        section(probe, "Keeping the position", 3)


def test_item1_fences_open_and_close_as_trace_check_reads_them():
    """Item 1: a fence opened by an indented run (four spaces, which the old reading did not take for a fence) hides
    the headings inside it, and a fence closes only on a run of its character at least as long, whatever follows the
    run, as trace-check.py's parse_units reads a fence, and a fence never closed hides the rest of the file; the
    helpers and trace-check.py agree on each case."""
    cases = {
        "## A\n    ```\n### B\n    ```\n### C\n": [(2, "A"), (3, "C")],
        "## A\n````\n### B\n```\n### C\n````text\n### D\n": [(2, "A"), (3, "D")],
        "## A\n~~~\n### B\n```\n~~~\n### C\n": [(2, "A"), (3, "C")],
        "## A\n    ### B\n   ### C\n": [(2, "A"), (3, "C")],
        "## A\n```\n### B\n## C\n": [(2, "A")],
    }
    tc = trace_check()
    for text, expected in cases.items():
        assert headings(text) == expected, text
        assert tc.parse_units(text)[1] == [t for _l, t in expected], text
