"""The paths and helpers the tests of the conditional workflows (the trait and type files) share: the workflow folder's
files, the trace check's units, the workflow check's run, the open list's rows and the trace exceptions naming a file
(stage B4's refactoring pass, the tests lane). Not a test file."""
import importlib.util
import os
import re
import subprocess
import sys

from phase_modules import BRIDGE, read, section

REPO = os.path.dirname(BRIDGE)

WORKFLOW = os.path.join(BRIDGE, "cursor-bridge", "workflow")
TYPES = os.path.join(WORKFLOW, "types")
TRAITS = os.path.join(WORKFLOW, "traits")
PHASES = os.path.join(WORKFLOW, "phases")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
PLAN_CRITIC = os.path.join(BRIDGE, "agents", "plan-critic.md")
EXCEPTIONS = os.path.join(WORKFLOW, "trace-exceptions.md")
OPEN_LIST = os.path.join(WORKFLOW, "open-list.md")
REGISTRY = os.path.join(WORKFLOW, "extension-points.md")
TRACE_CHECK = os.path.join(BRIDGE, "cursor-bridge", "trace-check.py")
WORKFLOW_CHECK = os.path.join(BRIDGE, "cursor-bridge", "workflow-check.py")
FIXTURES = os.path.join(REPO, "tests", "fixtures", "workflows")
TRAIT_PREFIX = "bridge/cursor-bridge/workflow/traits/"


def flat(text):
    """The text with every run of white space one space, stripped at both ends."""
    return re.sub(r"\s+", " ", text).strip()


def trace_check():
    """trace-check.py, loaded afresh on each call."""
    spec = importlib.util.spec_from_file_location("trace_check_workflow_files", TRACE_CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def trace_units(text):
    """The normal form of each unit trace-check.py reads in the text."""
    return [u["normal"] for u in trace_check().parse_units(text)[0]]


def run_check(*args):
    """workflow-check.py run with the arguments."""
    return subprocess.run([sys.executable, WORKFLOW_CHECK] + list(args), capture_output=True, text=True,
                          encoding="utf-8")


def _table(table_heading):
    lines = [l for l in section(read(OPEN_LIST), table_heading, 2).split("\n") if l.startswith("|")]
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    return header, [[c.strip() for c in l.strip("|").split("|")] for l in lines[2:]]


def rows(table_heading):
    """The open list's rows in the table under `table_heading`, each a dict of its columns, keyed by the first (a
    repeated key keeps its last row)."""
    header, body = _table(table_heading)
    return {cells[0]: dict(zip(header, cells)) for cells in body}


def row(table_heading, key):
    """The open list's first row for `key` in the table under `table_heading`, as a dict of its columns."""
    header, body = _table(table_heading)
    for cells in body:
        if cells[0] == key:
            return dict(zip(header, cells))
    raise AssertionError(key)


def traits_of(cell):
    return set(t.strip() for t in cell.split(","))


def file_entries(rel):
    """The trace exceptions naming the file `rel`, each (kind, increment, heading), in their order."""
    got = []
    for line in read(EXCEPTIONS).split("\n"):
        m = re.match(r"^- (new|reword) (\S+) (\S+\.md) (.+)$", line)
        if m and m.group(3) == rel:
            got.append((m.group(1), m.group(2), m.group(4).strip()))
    return got
