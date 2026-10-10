#!/usr/bin/env python3
"""diagram-check: are the normative design diagrams complete, consistent, and obeyed by the code?

  python diagram-check.py [--mode design|code|done] [--index docs/diagrams/INDEX.md]

Run from the Workspace root. Deterministic; reads only; no dependencies. ASCII output.
Conventions: ~/.claude/cursor-bridge/Diagram-Planning-Conventions.md.

--mode design  (design gate, change-cycle design revision)
  INDEX       the index table is well-formed; every catalogue kind is selected or omitted with a
              reason; levels match kinds; IDs are unique; Level 4-5 selections state a load-bearing
              category; every selected diagram realizes >= 1 existing requirement ID and names a
              valid enforcement.
  FILE        each selected diagram file exists, holds exactly one mermaid block, and uses a
              notation allowed for its kind.
  REFINES     refined diagrams exist, are selected, and sit at the same or a higher level.
  CONSISTENCY sequence-diagram participants exist in the diagrams they refine (actors and
              `%% external:` names excepted); element-map entries exist in the component diagram.
  TRACE       use cases (`uc_...`) and screens (`scr_...`) name requirement IDs; every requirement
              ID named in a diagram exists in docs/REQUIREMENTS.md.
--mode code    (loop step 4 on every increment, every stage close) - design checks, plus:
  IMPORT      `check:components`: an import between two components the diagram does not connect.
  SCHEMA      `check:schema <file>`: entities/tables and attributes/columns that differ.
  TESTS       `tests:` files that exist must name the diagram ID; for state machines every state
              must appear in them. Missing files are notes.
--mode done    (project end) - code checks, plus: a review item naming no reviewer, a deviation
              still listed in docs/diagrams/DEVIATIONS.md, missing enforcing test files, missing schema
              dumps, and components with no code fail.
Exit 0 = OK, 1 = at least one failure.
"""
import argparse
import fnmatch
import glob
import os
import re
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

CATALOGUE = {
    # kind: (level, allowed notations)
    "use-case": (1, ("flowchart", "graph")),
    "operational-activity": (1, ("flowchart", "graph")),
    "system-architecture": (2, ("flowchart", "graph", "C4Context", "C4Container", "architecture-beta")),
    "deployment": (2, ("flowchart", "graph", "C4Deployment", "architecture-beta")),
    "context-dfd": (2, ("flowchart", "graph")),
    "inter-system-sequence": (2, ("sequenceDiagram",)),
    "infrastructure-state": (2, ("stateDiagram-v2", "stateDiagram")),
    "component": (3, ("flowchart", "graph", "C4Component")),
    "inter-component-sequence": (3, ("sequenceDiagram",)),
    "component-dfd": (3, ("flowchart", "graph")),
    "component-state": (3, ("stateDiagram-v2", "stateDiagram")),
    "class": (4, ("classDiagram",)),
    "erd": (4, ("erDiagram",)),
    "domain-dfd": (4, ("flowchart", "graph")),
    "object": (5, ("classDiagram", "flowchart", "graph")),
    "micro-sequence": (5, ("sequenceDiagram",)),
    "algorithmic-activity": (5, ("flowchart", "graph")),
    "object-state": (5, ("stateDiagram-v2", "stateDiagram")),
}
SEQUENCE_KINDS = {"inter-system-sequence", "inter-component-sequence", "micro-sequence"}
STATE_KINDS = {"infrastructure-state", "component-state", "object-state"}
LOAD_BEARING = ("concurrency", "security", "integrity", "performance", "protocol", "prior-failure")
R_RX = re.compile(r"\bR-\d{3,}\b")
D_RX = re.compile(r"\bD-\d{3,}\b")
IDENT = r"[A-Za-z_]\w*"
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs|e2e|testing|fixtures)(/|$)"
                       r"|(^|/)test_[^/]*$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$", re.I)
SKIP_PATH = re.compile(r"(^|/)(docs|\.claude|\.cursor|\.github|node_modules|vendor|third_party|dist|build)(/|$)", re.I)
PY_EXT = {".py"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte"}
JS_RESOLVE = ["", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".d.ts",
              "/index.ts", "/index.tsx", "/index.js", "/index.jsx", "/index.mjs", "/index.vue"]


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def table_rows(text):
    header, rows = None, []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if header is not None and rows:
                break                                   # first table only
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if header is None:
            header = [c.lower() for c in cells]
        else:
            rows.append(cells)
    return header, rows


def blank(v):
    return v.strip().strip("`*").strip() in ("", "-", "—", "none", "n/a")


def mermaid_blocks(text):
    return re.findall(r"```mermaid[^\n]*\n(.*?)```", text, re.S)


def strip_comments(block):
    out, externals = [], set()
    for line in block.splitlines():
        m = re.match(r"\s*%%\s*external\s*:\s*(.*)$", line, re.I)
        if m:
            externals.update(x.strip() for x in m.group(1).split(",") if x.strip())
            continue
        out.append(re.sub(r"%%.*$", "", line))
    return "\n".join(out), externals


def notation(block):
    body, _ = strip_comments(block)
    lines = body.splitlines()
    i = 0
    if lines and lines[0].strip() == "---":                # front matter
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        i += 1
    for line in lines[i:]:
        s = line.strip()
        if s:
            return s.split()[0]
    return ""


# ------------------------------------------------------------------ notation parsers
ARROW = re.compile(r"\s*(<|(?<=\s)[xo])?(-{2,}|={2,}|-\.+-|~{3,})(>|[xo](?=\s|$))?\s*")
FC_SKIP = re.compile(r"^(flowchart|graph|classDef|class|style|linkStyle|click|direction|%%)\b")


def parse_flowchart(block):
    """Nodes, subgraph membership, directed dependency edges, labels."""
    body, externals = strip_comments(block)
    nodes, parent, edges, labels, order = set(), {}, set(), {}, []
    stack = []
    for raw in body.splitlines():
        s = raw.strip()
        if not s or FC_SKIP.match(s):
            continue
        m = re.match(r"^subgraph\s+(%s)" % IDENT, s)
        if m:
            sg = m.group(1)
            nodes.add(sg)
            if stack and sg not in parent:
                parent[sg] = stack[-1]
            stack.append(sg)
            continue
        if s.startswith("subgraph"):
            stack.append(None)
            continue
        if s == "end":
            if stack:
                stack.pop()
            continue
        # labels on node declarations (captured before stripping)
        for lm in re.finditer(r"\b(%s)\s*(?:\[\[|\[\(|\(\[|\(\(|\[/|\[\\|\{\{|\[|\(|\{|>)\s*\"?([^\]\)\}\"]*)" % IDENT, s):
            labels.setdefault(lm.group(1), lm.group(2))
        for lm in re.finditer(r"\b(%s)@\{[^}]*?label\s*:\s*\"([^\"]*)\"" % IDENT, s):
            labels.setdefault(lm.group(1), lm.group(2))
        s2 = re.sub(r"\|[^|]*\|", " ", s)                                 # edge labels
        s2 = re.sub(r"(--|==|-\.)\s*[^-=.>|\s][^>|]*?\s*(-->|---|==>|===|\.->|\.-)",
                    lambda m: " " + {"-->": "-->", "---": "---", "==>": "==>", "===": "===",
                                     ".->": "-.->", ".-": "-.-"}[m.group(2)] + " ", s2)
        seps = list(ARROW.finditer(s2))
        segs, pos = [], 0
        for sep in seps:
            segs.append(s2[pos:sep.start()])
            pos = sep.end()
        segs.append(s2[pos:])

        def ids(seg):
            out = []
            for part in seg.split("&"):
                m2 = re.match(r"\s*(%s)" % IDENT, part)
                if m2:
                    out.append(m2.group(1))
            return out

        seg_ids = [ids(x) for x in segs]
        for group in seg_ids:
            for n in group:
                if n not in nodes:
                    nodes.add(n)
                    order.append(n)
                    cur = next((x for x in reversed(stack) if x), None)
                    if cur and n not in parent:
                        parent[n] = cur
        for i, sep in enumerate(seps):
            left, right = seg_ids[i], seg_ids[i + 1]
            head, tail = sep.group(3) == ">", sep.group(1) == "<"
            for a in left:
                for b in right:
                    if head:
                        edges.add((a, b))
                    if tail:
                        edges.add((b, a))
    subgraphs = {p for p in parent.values()} | {n for n in nodes if any(v == n for v in parent.values())}
    return {"elements": nodes, "parent": parent, "edges": edges, "labels": labels,
            "subgraphs": subgraphs, "externals": externals, "leaves": [n for n in order if n not in subgraphs]}


def parse_c4(block):
    body, externals = strip_comments(block)
    elements, parent, edges, stack = set(), {}, set(), []
    for raw in body.splitlines():
        s = raw.strip()
        m = re.match(r"^(\w+)\(\s*(%s)\s*[,)]" % IDENT, s)
        if m and not m.group(1).startswith(("Rel", "BiRel", "UpdateRel", "Update", "Lay_")):
            elements.add(m.group(2))
            if stack:
                parent[m.group(2)] = stack[-1]
            if s.rstrip().endswith("{"):
                stack.append(m.group(2))
            continue
        m = re.match(r"^(BiRel|Rel)\w*\(\s*(%s)\s*,\s*(%s)" % (IDENT, IDENT), s)
        if m:
            edges.add((m.group(2), m.group(3)))
            if m.group(1) == "BiRel":
                edges.add((m.group(3), m.group(2)))
            continue
        if s == "}" and stack:
            stack.pop()
    subgraphs = set(parent.values())
    return {"elements": elements, "parent": parent, "edges": edges, "labels": {},
            "subgraphs": subgraphs, "externals": externals,
            "leaves": [e for e in elements if e not in subgraphs]}


def parse_architecture(block):
    body, externals = strip_comments(block)
    elements, parent = set(), {}
    for raw in body.splitlines():
        m = re.match(r"^\s*(group|service|junction)\s+(%s)(?:.*?\bin\s+(%s))?" % (IDENT, IDENT), raw)
        if m:
            elements.add(m.group(2))
            if m.group(3):
                parent[m.group(2)] = m.group(3)
    return {"elements": elements, "parent": parent, "edges": set(), "labels": {},
            "subgraphs": set(parent.values()), "externals": externals, "leaves": []}


SEQ_KEYWORDS = {"note", "loop", "alt", "else", "opt", "par", "and", "critical", "break", "rect",
                "end", "autonumber", "activate", "deactivate", "box", "destroy", "links", "link",
                "title", "sequencediagram", "option", "properties", "details"}


def parse_sequence(block):
    body, externals = strip_comments(block)
    participants, actors, classes = set(), set(), {}
    for raw in body.splitlines():
        s = raw.strip()
        m = re.match(r"^(?:create\s+)?(participant|actor)\s+(\S+?)(?:@\{.*\})?(?:\s+as\s+(.*))?$", s)
        if m:
            pid = m.group(2).strip('"')
            participants.add(pid)
            if m.group(1) == "actor":
                actors.add(pid)
            if m.group(3) and ":" in m.group(3):
                classes[pid] = m.group(3).split(":", 1)[1].strip().strip('"')
            continue
        if not s or s.split()[0].lower().rstrip(":") in SEQ_KEYWORDS:
            continue
        m = re.match(r"^([^\s:<>+\-()]+)\s*(?:<<)?(?:-->>|->>|-->|->|--x|-x|--\)|-\))(?:>>)?\s*[+-]?\s*([^\s:]+)\s*:", s)
        if m:
            participants.update({m.group(1), m.group(2)})
    return {"participants": participants, "actors": actors, "classes": classes, "externals": externals}


def parse_state(block):
    body, _ = strip_comments(block)
    states, pseudo, transitions = set(), set(), 0
    for raw in body.splitlines():
        s = raw.strip()
        if not s or re.match(r"^(stateDiagram|direction|note|end note|classDef|class)\b", s):
            continue
        m = re.match(r"^state\s+\"[^\"]*\"\s+as\s+(%s)" % IDENT, s)
        if m:
            states.add(m.group(1))
            continue
        m = re.match(r"^state\s+(%s)\s*(<<\s*(choice|fork|join)\s*>>)?" % IDENT, s)
        if m:
            (pseudo if m.group(2) else states).add(m.group(1))
            continue
        m = re.match(r"^(\[\*\]|%s)\s*-->\s*(\[\*\]|%s)" % (IDENT, IDENT), s)
        if m:
            transitions += 1
            for x in m.groups():
                if x != "[*]":
                    states.add(x)
            continue
        m = re.match(r"^(%s)\s*:" % IDENT, s)
        if m:
            states.add(m.group(1))
    return {"elements": states - pseudo, "pseudo": pseudo, "transitions": transitions}


def parse_class(block):
    body, _ = strip_comments(block)
    classes = set()
    rel = re.compile(r"^(%s)(?:~[^~]*~)?\s*(?:\"[^\"]*\"\s*)?[<*o|()]{0,2}(?:--|\.\.)[>*o|()]{0,2}\s*(?:\"[^\"]*\"\s*)?(%s)" % (IDENT, IDENT))
    for raw in body.splitlines():
        s = raw.strip()
        m = re.match(r"^class\s+(%s)" % IDENT, s)
        if m:
            classes.add(m.group(1))
            continue
        m = rel.match(s)
        if m:
            classes.update(m.groups())
            continue
        m = re.match(r"^(%s)\s*:" % IDENT, s)
        if m:
            classes.add(m.group(1))
    return {"elements": classes}


def parse_erd(block):
    body, _ = strip_comments(block)
    entities, attrs, cur = set(), {}, None
    for raw in body.splitlines():
        s = raw.strip()
        if not s or s.startswith("erDiagram"):
            continue
        if cur is not None:
            if s.startswith("}"):
                cur = None
                continue
            toks = s.split()
            if len(toks) >= 2:
                attrs.setdefault(cur, set()).add(toks[1].strip('"').lower())
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*(?:\[[^\]]*\])?\s*\{\s*$", s)
        if m:
            cur = m.group(1)
            entities.add(cur)
            attrs.setdefault(cur, set())
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s+[|}o]{1,2}(?:--|\.\.)[|{o]{1,2}\s+([A-Za-z_][\w-]*)", s)
        if m:
            entities.update(m.groups())
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s+[\w()+ ]+?\s+(?:optionally\s+)?to\s+[\w()+ ]+?\s+([A-Za-z_][\w-]*)\s*:", s)
        if m:
            entities.update(m.groups())
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*$", s)
        if m:
            entities.add(m.group(1))
    return {"elements": entities, "attributes": attrs}


def parse_structural(block, kind_notation):
    if kind_notation.startswith("C4"):
        return parse_c4(block)
    if kind_notation == "architecture-beta":
        return parse_architecture(block)
    if kind_notation == "classDiagram":
        d = parse_class(block)
        return {"elements": d["elements"], "parent": {}, "edges": set(), "labels": {}, "subgraphs": set(),
                "externals": set(), "leaves": list(d["elements"])}
    if kind_notation == "erDiagram":
        d = parse_erd(block)
        return {"elements": d["elements"], "parent": {}, "edges": set(), "labels": {}, "subgraphs": set(),
                "externals": set(), "leaves": list(d["elements"])}
    if kind_notation.startswith("stateDiagram"):
        d = parse_state(block)
        return {"elements": d["elements"], "parent": {}, "edges": set(), "labels": {}, "subgraphs": set(),
                "externals": set(), "leaves": list(d["elements"])}
    return parse_flowchart(block)


# ------------------------------------------------------------------ code conformance
def tracked():
    """Tracked files plus untracked, non-ignored ones: at loop step 4 the builder's new files
    are not committed yet, and an import in a new file must not escape the check."""
    p = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                       capture_output=True, creationflags=NO_WINDOW)
    if p.returncode != 0:
        return None
    files = {f.replace("\\", "/") for f in p.stdout.decode("utf-8", "replace").split("\0") if f}
    return sorted(f for f in files if os.path.isfile(f))


def glob_re(pattern):
    p = pattern.strip().strip("`").replace("\\", "/")
    if p.endswith("/"):
        p += "**"
    out, i = "", 0
    while i < len(p):
        if p.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif p.startswith("**", i):
            out += ".*"
            i += 2
        elif p[i] == "*":
            out += "[^/]*"
            i += 1
        elif p[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(p[i])
            i += 1
    return re.compile("^" + out + "$")


def element_map(text):
    """The first table in the diagram file whose header starts with Element | Paths."""
    for chunk in re.split(r"```mermaid.*?```", text, flags=re.S):
        header, rows = table_rows(chunk)
        if header and len(header) >= 2 and header[0].startswith("element") and header[1].startswith("path"):
            out = []
            for r in rows:
                if len(r) >= 2 and r[0]:
                    for g in re.split(r"[,;]", r[1]):
                        if g.strip():
                            out.append((r[0].strip("`* "), g.strip(), glob_re(g)))
            return out
    return None


def py_module_index(files):
    fileset = set(files)
    index = {}
    for f in files:
        if not f.endswith(".py"):
            continue
        parts = f[:-3].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            continue
        index.setdefault(".".join(parts), f)                       # full path form
        k = 0                                                      # strip leading non-package dirs
        while k < len(parts) - 1 and ("/".join(parts[:k + 1]) + "/__init__.py") not in fileset:
            k += 1
        index.setdefault(".".join(parts[k:]), f)
    return index


def py_imports(path, text, index):
    out = []
    pkg_dir = os.path.dirname(path)
    for n, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^\s*from\s+(\.*)([\w.]*)\s+import\s+\(?\s*([\w, ]*)", line)
        if m:
            dots, mod, names = m.group(1), m.group(2), [x.strip().split(" as ")[0] for x in m.group(3).split(",") if x.strip()]
            if dots:
                base = pkg_dir
                for _ in range(len(dots) - 1):
                    base = os.path.dirname(base)
                stem = "/".join(x for x in [base] + (mod.split(".") if mod else []) if x)
                cands = [stem + "/" + nm + ".py" for nm in names] + [stem + "/" + nm + "/__init__.py" for nm in names] \
                    + [stem + ".py", stem + "/__init__.py"]
                hit = next((c for c in cands if c in index.values()), None)
                if hit:
                    out.append((n, hit))
            else:
                hit = None
                for nm in names:
                    hit = index.get(mod + "." + nm)
                    if hit:
                        break
                hit = hit or index.get(mod)
                if hit:
                    out.append((n, hit))
            continue
        m = re.match(r"^\s*import\s+([\w., ]+)", line)
        if m:
            for mod in m.group(1).split(","):
                mod = mod.strip().split(" as ")[0].strip()
                parts = mod.split(".")
                for k in range(len(parts), 0, -1):
                    hit = index.get(".".join(parts[:k]))
                    if hit:
                        out.append((n, hit))
                        break
    return out


JS_IMPORT = re.compile(r"""(?:\bimport|\bexport)\s+(?:[^'";]*?\s+from\s+)?['"]([^'"]+)['"]|\brequire\(\s*['"]([^'"]+)['"]\s*\)|\bimport\(\s*['"]([^'"]+)['"]\s*\)""")


def js_imports(path, text, fileset):
    out = []
    for m in JS_IMPORT.finditer(text):
        spec = (m.group(1) or m.group(2) or m.group(3) or "").split("?")[0]
        if spec.startswith("."):
            base = os.path.normpath(os.path.join(os.path.dirname(path), spec)).replace("\\", "/")
        elif spec.startswith(("@/", "~/")):
            base = "src/" + spec[2:]
        else:
            continue
        hit = next((base + ext for ext in JS_RESOLVE if (base + ext) in fileset), None)
        if hit:
            out.append((text.count("\n", 0, m.start()) + 1, hit))
    return out


DEVIATIONS = os.path.join("docs", "diagrams", "DEVIATIONS.md")
REVIEWERS = re.compile(r"\b(diff-reviewer|design-auditor|security-auditor|plan-critic|refactor-scout|Review [AB])\b")


def known_deviations(path=DEVIATIONS):
    """{(diagram, from, to)} listed in docs/diagrams/DEVIATIONS.md (release A3, plan 8.7)."""
    out = set()
    if not os.path.isfile(path):
        return out
    header, rows = table_rows(read(path))
    if not header or not header[0].startswith("diagram"):
        return out
    for r in rows:
        if len(r) >= 3 and r[0] and r[1] and r[2]:
            out.add((r[0].strip("`* "), r[1].strip("`* "), r[2].strip("`* ")))
    return out


def component_violations(did, fc, emap, files, done, fails, notes, deviations=frozenset()):
    elements = fc["elements"]
    for name, pat, _ in emap:
        if name not in elements:
            fails.append("CONSISTENCY: %s element map names '%s', which is not in the diagram" % (did, name))
    ordered = sorted(emap, key=lambda e: -len(e[1]))
    fileset = set(files)

    def owner(f):
        for name, _, rx in ordered:
            if rx.match(f):
                return name
        return None

    ancestors = {}

    def anc(n):
        if n not in ancestors:
            chain, cur = [n], n
            while cur in fc["parent"]:
                cur = fc["parent"][cur]
                chain.append(cur)
            ancestors[n] = chain
        return ancestors[n]

    def allowed(a, b):
        return any((x, y) in fc["edges"] for x in anc(a) for y in anc(b))

    sources = [f for f in files if os.path.splitext(f)[1].lower() in (PY_EXT | JS_EXT)
               and not TEST_PATH.search(f) and not SKIP_PATH.search(f)]
    pyindex = py_module_index(files)
    mapped_any = {name: False for name, _, _ in emap}
    unmapped = 0
    violations = []
    for f in sources:
        src = owner(f)
        if src is None:
            unmapped += 1
            continue
        mapped_any[src] = True
        try:
            text = read(f)
        except OSError:
            continue
        ext = os.path.splitext(f)[1].lower()
        imps = py_imports(f, text, pyindex) if ext in PY_EXT else js_imports(f, text, fileset)
        for line, dst_file in imps:
            dst = owner(dst_file)
            if dst and dst != src and not allowed(src, dst):
                if (did, src, dst) in deviations:
                    notes.append("DEVIATION listed in %s: %s:%d (%s) imports %s (%s) - resolved when its fix merges" % (DEVIATIONS, f, line, src, dst_file, dst))
                    continue
                violations.append("IMPORT: %s:%d (%s) imports %s (%s) - %s draws no %s --> %s"
                                  % (f, line, src, dst_file, dst, did, src, dst))
    fails.extend(violations[:60])
    if len(violations) > 60:
        fails.append("IMPORT: ... and %d more" % (len(violations) - 60))
    if unmapped:
        notes.append("%s: %d tracked source file(s) belong to no component in the element map" % (did, unmapped))
    for leaf in fc["leaves"]:
        if leaf in fc["externals"]:
            continue
        if not any(name == leaf for name, _, _ in emap):
            (fails if done else notes).append("%s: component '%s' has no element-map entry%s"
                                              % (did, leaf, " (no code can be checked against it)" if done else ""))
        elif done and not mapped_any.get(leaf):
            fails.append("%s: component '%s' matches no source file - drawn but not built" % (did, leaf))


def sql_schema(text):
    text = re.sub(r"--[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    tables = {}
    for m in re.finditer(r"CREATE\s+(?:TEMP(?:ORARY)?\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`\"\[]?[\w.]+[`\"\]]?)\s*\(", text, re.I):
        name = m.group(1).strip('`"[]').split(".")[-1].lower()
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        body = text[m.end():i - 1]
        cols, depth, cur = set(), 0, ""
        for ch in body + ",":
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if ch == "," and depth == 0:
                tok = cur.strip().split()
                if tok and tok[0].upper() not in ("CONSTRAINT", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "KEY", "INDEX"):
                    cols.add(tok[0].strip('`"[]').lower())
                cur = ""
            else:
                cur += ch
        tables[name] = cols
    return tables


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description="Check the normative design diagrams.")
    ap.add_argument("--mode", choices=("design", "code", "done"), default="design")
    ap.add_argument("--index", default="docs/diagrams/INDEX.md")
    ap.add_argument("--requirements", default="docs/REQUIREMENTS.md")
    a = ap.parse_args()
    code_mode, done = a.mode in ("code", "done"), a.mode == "done"
    fails, notes = [], []

    if not os.path.exists(a.index):
        print("INDEX: %s does not exist" % a.index)
        print("RESULT: 1 problem(s)")
        return 1
    header, rows = table_rows(read(a.index))
    want = ["id", "level", "kind", "status", "file", "refines", "realizes", "enforced", "why"]
    if header is None or [h.split()[0] if h else "" for h in header][:9] != want:
        fails.append("INDEX: header must be | ID | Level | Kind | Status | File | Refines | Realizes | Enforced by | Why |")
        rows = []

    reqs = None
    if os.path.exists(a.requirements):
        reqs = set(R_RX.findall(read(a.requirements)))
    else:
        notes.append("no %s - requirement IDs not verified" % a.requirements)

    diagrams, seen_kinds = {}, set()
    for r in rows:
        if len(r) < 9:
            fails.append("INDEX: row has %d cells, expected 9: %s" % (len(r), " | ".join(r)[:100]))
            continue
        did, level, kind, status, path, refines, realizes, enforced, why = [c.strip() for c in r[:9]]
        did, kind, status = did.strip("`* "), kind.strip("`* ").lower(), status.strip("`* ").lower()
        if kind not in CATALOGUE:
            fails.append("INDEX: unknown kind '%s' (see the catalogue)" % kind)
            continue
        seen_kinds.add(kind)
        if level.strip("`* ") != str(CATALOGUE[kind][0]):
            fails.append("INDEX: %s %s is level %s in the catalogue, not %s" % (did, kind, CATALOGUE[kind][0], level))
        if status.startswith("omitted"):
            if blank(why):
                fails.append("INDEX: omitted %s has no reason in Why" % kind)
            continue
        if not status.startswith("selected"):
            fails.append("INDEX: %s status '%s' (selected | omitted)" % (did or kind, status))
            continue
        if not re.fullmatch(r"D-\d{3,}", did):
            fails.append("INDEX: selected %s has ID '%s' (use D-001 ...)" % (kind, did))
            continue
        if did in diagrams:
            fails.append("INDEX: duplicate ID %s" % did)
            continue
        d = {"id": did, "level": CATALOGUE[kind][0], "kind": kind, "path": path.strip("` "),
             "refines": D_RX.findall(refines), "realizes": R_RX.findall(realizes),
             "enforced": [e.strip() for e in enforced.split(";") if e.strip() and not blank(e)], "why": why}
        diagrams[did] = d
        if not d["realizes"]:
            fails.append("INDEX: %s realizes no requirement ID" % did)
        elif reqs is not None:
            for rid in d["realizes"]:
                if rid not in reqs:
                    fails.append("TRACE: %s realizes %s, which is not in %s" % (did, rid, a.requirements))
        if not d["enforced"]:
            fails.append("INDEX: %s names no enforcement (check:, tests:, or review:) - a diagram nothing enforces is not normative" % did)
        for e in d["enforced"]:
            if not re.match(r"^(check:components|check:schema\s+\S+|tests:\s*\S+|review:\s*\S+)", e):
                fails.append("INDEX: %s enforcement '%s' (check:components | check:schema <file> | tests: <paths> | review: <item>)" % (did, e[:40]))
            if e.startswith("check:components") and kind != "component":
                fails.append("INDEX: %s uses check:components but is a %s diagram" % (did, kind))
            if e.startswith("check:schema") and kind != "erd":
                fails.append("INDEX: %s uses check:schema but is a %s diagram" % (did, kind))
            if e.startswith("review:") and not REVIEWERS.search(e):
                (fails if done else notes).append("INDEX: %s review item '%s' names no reviewer; name who checks it (diff-reviewer, design-auditor, security-auditor, plan-critic or Review B; release A3)%s" % (
                    did, e[7:].strip()[:50], "" if done else " - a failure at project end"))
        if kind == "object" and not any(e.startswith("tests:") for e in d["enforced"]):
            fails.append("INDEX: object diagram %s must be enforced by tests (the example becomes a fixture)" % did)
        if d["level"] >= 4:
            w = why.strip().lower()
            if not any(w.startswith(c) for c in LOAD_BEARING) or ":" not in w or len(w.split(":", 1)[1].strip()) < 10:
                fails.append("INDEX: Level %d diagram %s needs a load-bearing reason in Why (%s: <one sentence>)"
                             % (d["level"], did, " | ".join(LOAD_BEARING)))
    if rows:
        for kind in CATALOGUE:
            if kind not in seen_kinds:
                fails.append("INDEX: catalogue kind '%s' is neither selected nor omitted" % kind)

    # files and parsed content
    for did, d in diagrams.items():
        if not d["path"] or not os.path.isfile(d["path"]):
            fails.append("FILE: %s file '%s' does not exist" % (did, d["path"]))
            continue
        text = read(d["path"])
        blocks = mermaid_blocks(text)
        if len(blocks) != 1:
            fails.append("FILE: %s holds %d mermaid blocks (exactly one)" % (did, len(blocks)))
            continue
        d["text"], d["block"] = text, blocks[0]
        d["notation"] = notation(blocks[0])
        if d["notation"] not in CATALOGUE[d["kind"]][1]:
            fails.append("FILE: %s is a %s diagram drawn as '%s' (allowed: %s)"
                         % (did, d["kind"], d["notation"], ", ".join(CATALOGUE[d["kind"]][1])))
            continue
        if d["notation"] in ("flowchart", "graph", "stateDiagram-v2", "stateDiagram"):
            body_lines = [l for l in strip_comments(blocks[0])[0].splitlines() if l.strip() != "end"]
            if re.search(r"(^|[\s&>])end\s*(\[|\(|\{|-->|---|==>|:|$)", "\n".join(body_lines), re.M):
                fails.append("FILE: %s names an element 'end', which breaks Mermaid flowcharts and state machines" % did)
        if d["kind"] in SEQUENCE_KINDS:
            d["parsed"] = parse_sequence(blocks[0])
        elif d["kind"] in STATE_KINDS:
            d["parsed"] = parse_state(blocks[0])
            if not d["parsed"]["transitions"]:
                fails.append("FILE: state machine %s has no transitions" % did)
        elif d["kind"] == "erd":
            d["parsed"] = parse_erd(blocks[0])
        else:
            d["parsed"] = parse_structural(blocks[0], d["notation"])
        if reqs is not None:
            for rid in set(R_RX.findall(blocks[0])):
                if rid not in reqs:
                    fails.append("TRACE: %s names %s, which is not in %s" % (did, rid, a.requirements))
        if d["kind"] in ("use-case", "operational-activity") and "labels" in d["parsed"]:
            prefix = "uc_" if d["kind"] == "use-case" else "scr_"
            ucs = [n for n in d["parsed"]["elements"] if n.startswith(prefix)]
            if d["kind"] == "use-case" and not ucs:
                fails.append("TRACE: use case diagram %s has no uc_ nodes" % did)
            for n in ucs:
                if not R_RX.search(d["parsed"]["labels"].get(n, "")):
                    fails.append("TRACE: %s %s '%s' names no requirement ID in its label"
                                 % (did, "use case" if prefix == "uc_" else "screen", n))

    # refines and cross-diagram consistency
    for did, d in diagrams.items():
        for ref in d["refines"]:
            if ref not in diagrams:
                fails.append("REFINES: %s refines %s, which is not a selected diagram" % (did, ref))
            elif diagrams[ref]["level"] > d["level"]:
                fails.append("REFINES: %s (level %d) refines %s (level %d) - diagrams refine only upward"
                             % (did, d["level"], ref, diagrams[ref]["level"]))
        if d["kind"] in SEQUENCE_KINDS and "parsed" in d:
            if not d["refines"]:
                fails.append("REFINES: sequence diagram %s refines no structural diagram" % did)
                continue
            pool = set()
            for ref in d["refines"]:
                pr = diagrams.get(ref, {}).get("parsed") or {}
                pool |= set(pr.get("elements", ()))
            p = d["parsed"]
            for part in sorted(p["participants"]):
                if part in p["actors"] or part in p["externals"]:
                    continue
                name = p["classes"].get(part, part) if d["kind"] == "micro-sequence" else part
                if name not in pool:
                    fails.append("CONSISTENCY: %s participant '%s' is not an element of %s"
                                 % (did, name, ", ".join(d["refines"])))

    # code conformance
    files = None
    if code_mode:
        files = tracked()
        if files is None:
            notes.append("not a git repository - code conformance not checked")
    deviations = known_deviations() if code_mode else frozenset()
    if deviations:
        notes.append("%d known deviation(s) listed in %s; each is resolved when its fix merges" % (len(deviations), DEVIATIONS))
    if done and deviations:
        fails.append("DEVIATIONS: %d deviation(s) still listed in %s at project end" % (len(deviations), DEVIATIONS))
    for did, d in diagrams.items():
        if "parsed" not in d:
            continue
        for e in d["enforced"]:
            if e.startswith("check:components"):
                emap = element_map(d["text"])
                if emap is None:
                    fails.append("FILE: %s is enforced by check:components but has no | Element | Paths | map" % did)
                elif files is not None:
                    component_violations(did, d["parsed"], emap, files, done, fails, notes, deviations)
                elif not code_mode:
                    for name, _, _ in emap:
                        if name not in d["parsed"]["elements"]:
                            fails.append("CONSISTENCY: %s element map names '%s', which is not in the diagram" % (did, name))
            elif e.startswith("check:schema") and code_mode:
                dump = e.split(None, 1)[1].strip() if len(e.split(None, 1)) > 1 else ""
                if not os.path.isfile(dump):
                    (fails if done else notes).append("SCHEMA: %s schema dump '%s' does not exist" % (did, dump))
                    continue
                tables = sql_schema(read(dump))
                ents = {x.lower(): x for x in d["parsed"]["elements"]}
                for low, orig in sorted(ents.items()):
                    if low not in tables:
                        fails.append("SCHEMA: %s entity %s has no table in %s" % (did, orig, dump))
                        continue
                    drawn = d["parsed"]["attributes"].get(orig, set())
                    if drawn:
                        for c in sorted(drawn - tables[low]):
                            fails.append("SCHEMA: %s %s.%s is drawn but not a column" % (did, orig, c))
                        for c in sorted(tables[low] - drawn):
                            fails.append("SCHEMA: %s %s.%s is a column but not drawn" % (did, orig, c))
                for t in sorted(set(tables) - set(ents)):
                    fails.append("SCHEMA: table %s in %s is not in %s" % (t, dump, did))
            elif e.startswith("tests:") and code_mode:
                pats = [x.strip().strip("`") for x in e[len("tests:"):].split(",") if x.strip()]
                paths = sorted({p for pat in pats for p in glob.glob(pat, recursive=True) if os.path.isfile(p)})
                if not paths:
                    (fails if done else notes).append("TESTS: %s enforcing tests %s do not exist yet" % (did, ", ".join(pats)))
                    continue
                body = "\n".join(read(p) for p in paths)
                if not re.search(r"\b%s\b" % re.escape(did), body):
                    fails.append("TESTS: no enforcing test of %s names the diagram ID" % did)
                if d["kind"] in STATE_KINDS:
                    for st in sorted(d["parsed"]["elements"]):
                        if not re.search(r"\b%s\b" % re.escape(st), body):
                            fails.append("TESTS: state '%s' of %s appears in no enforcing test" % (st, did))

    kinds_sel = len({d["kind"] for d in diagrams.values()})
    notes.insert(0, "mode %s; %d diagrams selected across %d kinds; %d kinds omitted"
                 % (a.mode, len(diagrams), kinds_sel, len(CATALOGUE) - kinds_sel))
    for n in notes:
        print("note: " + n)
    for f in fails:
        print(f)
    print("RESULT: %s" % ("OK" if not fails else "%d problem(s)" % len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
