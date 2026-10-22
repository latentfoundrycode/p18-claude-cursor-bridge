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


def headings(text):
    """(level, title) of every heading outside fenced blocks, in order."""
    out, fence = [], None
    for line in text.split("\n"):
        m = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if m:
            if fence is None:
                fence = m.group(1)[0]
            elif m.group(1)[0] == fence:
                fence = None
            continue
        if fence is None:
            h = re.match(r"^(#{1,6}) (.*)$", line)
            if h:
                out.append((len(h.group(1)), h.group(2).strip()))
    return out


def section(text, title, level):
    """The body of the heading `title` at `level`, to the next heading of that level or higher."""
    lines = text.split("\n")
    start = lines.index("#" * level + " " + title) + 1
    end = len(lines)
    for i in range(start, len(lines)):
        h = re.match(r"^(#{1,6}) ", lines[i])
        if h and len(h.group(1)) <= level:
            end = i
            break
    return "\n".join(lines[start:end])


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
