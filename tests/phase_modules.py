"""The phase modules as the phase-module tests read them (tests/test_phase_modules_*.py): a module's text with its
line endings made "\n", its headings and sections, the extension points the registry names a module as declaring, and
the R-004 and R-006 shapes every module's test asserts, and the files the session-start hook names for a phase (stage
B5's refactoring pass). Not a test file; the tests import
it as they import instructions.py."""
import json
import os
import re
import shutil
import subprocess
import sys

BRIDGE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "bridge"))
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")
REGISTRY = os.path.join(BRIDGE, "cursor-bridge", "workflow", "extension-points.md")


def read(path):
    return open(path, encoding="utf-8").read().replace("\r\n", "\n")


def module(rel):
    return read(os.path.join(PHASES, rel if rel.endswith(".md") else rel + ".md"))


def flat(text):
    return re.sub(r"\s+", " ", text)


def trace_headings(lines):
    """(index, level, title) of each heading as trace-check.py reads one: up to three spaces before the hashes
    (its HEADING_RE), the title stripped, and no line inside a fenced block (its FENCE_OPEN_RE, closed by a line that
    starts with a run of the same character at least as long, whatever follows the run, as trace-check.py closes
    one). The one reading of a heading in the phase-module tests: trace-check.py excuses a passage under every heading
    its reading finds, so a test that read headings another way could miss one it excuses (HARDENING, Stage B3, the
    least-confident item 1; FIX-004)."""
    out, fence = [], None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if fence:
            c = re.match(r"^(`{3,}|~{3,})", stripped)
            if c and c.group(1)[0] == fence[0] and len(c.group(1)) >= fence[1]:
                fence = None
            continue
        f = re.match(r"^(`{3,}|~{3,})", stripped) if line.lstrip().startswith(("```", "~~~")) else None
        if f:
            fence = (f.group(1)[0], len(f.group(1)))
            continue
        h = re.match(r"^ {0,3}(#{1,6}) (.*)$", line)
        if h:
            out.append((i, len(h.group(1)), h.group(2).strip()))
    return out


def headings(text):
    """(level, title) of every heading as trace-check.py reads one (trace_headings), in order."""
    return [(level, title) for _i, level, title in trace_headings(text.split("\n"))]


def section_span(lines, title, level):
    """(start, end) line indexes of the one section titled `title`, its heading line at `start`, to the next heading
    of `level` or higher as trace_headings reads them (a heading in a fenced block not counting). The file has exactly
    one heading of that title at any level, and it is at `level`: trace-check.py excuses a passage under every heading
    of an entry's title, so a second one would hide text a test of the first never reads (FIX-004)."""
    found = trace_headings(lines)
    same = [(i, lv) for i, lv, t in found if t == title]
    if not (len(same) == 1 and same[0][1] == level):  # an explicit raise: `python -O` strips an assert
        raise AssertionError((title, level, [(lines[i], lv) for i, lv in same]))
    start = same[0][0]
    end = len(lines)
    for i, lv, _t in found:
        if i > start and lv <= level:
            end = i
            break
    return start, end


def section(text, title, level):
    """The body of the one heading `title` at `level` (section_span), without its heading line."""
    lines = text.split("\n")
    start, end = section_span(lines, title, level)
    return "\n".join(lines[start + 1:end])


def registry_rows(heading="## Extension points"):
    """The rows of the registry's table under `heading`, each a {column: cell} dict."""
    text = read(REGISTRY)
    table = text.split("\n" + heading + "\n", 1)[1].split("\n## ", 1)[0]
    rows = [l for l in table.split("\n") if l.startswith("|")]
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    return [dict(zip(header, [c.strip() for c in row.strip("|").split("|")])) for row in rows[2:]]


def registry_points(module_key):
    """The point keys the registry names `module_key` as declaring, in the table's order."""
    return [r["Key"] for r in registry_rows() if r["Declared by"] == module_key]


EXT_PROSE = ("This module offers the points below, each by its key in the extension-point registry "
             "(`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and "
             "whether it applies per part or per project. A conditional workflow's additions at a point are made where the "
             "point's line places them, in the order the core states in \"Main and conditional workflows\".")


def assert_survival_list(key, structure, intro, survival):
    """R-004's shape for one module: its headings are `structure`; its first section, straight after its heading, is
    the compaction-survival list, opening with `intro` and holding exactly the items `survival`."""
    text = module(key)
    assert headings(text) == structure, headings(text)
    lines = text.split("\n")
    assert lines[1] == "" and lines[2] == "### What must survive a compaction", lines[:3]
    body = section(text, "What must survive a compaction", 3).strip().split("\n")
    assert body[0] == intro, body[0]
    assert all(l.startswith("- ") for l in body[1:] if l), body
    items = [l[2:] for l in body[1:] if l]
    assert items == survival, items


def assert_declares_registry_points(key, may_set=False):
    """R-006's shape for one module: a `## Extension points` section, one line per point giving its key, exactly the
    points the registry names the module as declaring, in the table's order, its prose EXT_PROSE; no point line says
    "may set" unless `may_set` (a module whose points a type workflow may set). Returns the keys."""
    body = section(module(key), "Extension points", 2).strip().split("\n")
    keys = [re.match(r"^- `([a-z0-9.-]+)` — \S", l).group(1) for l in body if l.startswith("- ")]
    want = registry_points(key)
    assert want and keys == want, (keys, want)
    assert flat(" ".join(l for l in body if l and not l.startswith("- "))) == EXT_PROSE
    if not may_set:
        assert "may set" not in "\n".join(body)
    return want


def assert_points_placed(key, points):
    """R-006: each point line of the module is `points`' text for its key, and says what the registry's Applies cell
    states: a point that applies per project is made once for the whole project; one that applies per part names the
    part."""
    applies = {r["Key"]: r["Applies"] for r in registry_rows()}
    body = section(module(key), "Extension points", 2).strip().split("\n")
    for line in [l for l in body if l.startswith("- ")]:
        k = re.match(r"^- `([a-z0-9.-]+)` — ", line).group(1)
        assert line == "- `%s` — %s" % (k, points[k]), line
        if applies[k] == "project":
            assert line.endswith("; made once for the whole project."), (k, line)
        else:
            assert applies[k] == "part" and re.search(r"\b(of|for) the part\b", line), (k, applies[k], line)
            assert "whole project" not in line, line


def hook_named(tmp_path, phase):
    """R-005: the phase-module files the installed session-start hook names after a compaction for `Phase: <phase>`,
    the bridge's commands and cursor-bridge folders copied under a home of their own in `tmp_path` and a status file
    with no classification; the hook exits 0 with nothing on stderr. Each path as the hook prints it, in its order."""
    home = tmp_path / "home"
    cb = os.path.join(BRIDGE, "cursor-bridge")
    shutil.copytree(os.path.join(BRIDGE, "commands"), str(home / ".claude" / "commands"))
    shutil.copytree(cb, str(home / ".claude" / "cursor-bridge"), ignore=shutil.ignore_patterns("__pycache__"))
    ws = tmp_path / "proj" / "Workspace"
    (ws / "docs").mkdir(parents=True)
    (ws / "docs" / "PROJECT_STATUS.md").write_text(
        "# Project Status\nPhase: %s\nWorkflows: not yet classified\nAwaiting user on: nothing\n" % phase,
        encoding="utf-8")
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    data = {"cwd": str(ws), "hook_event_name": "SessionStart", "source": "compact"}
    p = subprocess.run([sys.executable, os.path.join(cb, "session-start.py"), "--part", "pointers"],
                       input=json.dumps(data), capture_output=True, text=True, encoding="utf-8", env=env)
    assert p.returncode == 0 and p.stderr == "", p.stderr
    w = "~/.claude/cursor-bridge/workflow/phases/"
    return [re.match(r"  - (\S+)", l).group(1) for l in p.stdout.split("\n") if l.startswith("  - " + w)]
