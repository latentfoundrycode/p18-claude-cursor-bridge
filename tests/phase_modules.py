"""The phase modules as the phase-module tests read them (tests/test_phase_modules_*.py): a module's text with its
line endings made "\n", its headings and sections, and the extension points the registry names a module as declaring.
Not a test file; the tests import it as they import instructions.py."""
import os
import re

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
    assert len(same) == 1 and same[0][1] == level, (title, level, [(lines[i], lv) for i, lv in same])
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


def registry_points(module_key):
    text = read(REGISTRY)
    table = text.split("\n## Extension points\n", 1)[1].split("\n## ", 1)[0]
    rows = [l for l in table.split("\n") if l.startswith("|")]
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    out = []
    for row in rows[2:]:
        cells = dict(zip(header, [c.strip() for c in row.strip("|").split("|")]))
        if cells["Declared by"] == module_key:
            out.append(cells["Key"])
    return out
