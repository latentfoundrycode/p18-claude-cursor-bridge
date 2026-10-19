#!/usr/bin/env python3
"""plan-check: is the build plan well-formed, and which increments are ready to build?

  python plan-check.py [--plan "docs/BUILD_PLAN*.md"] [--base origin/main] [--no-git] [--briefs handoff]

Run from the Workspace root. Deterministic; reads only. ASCII output.

An increment is a heading `### TASK-nnn — <title>` (or `### TASK-nnn: <title>`) inside a
stage heading (`## ...`), followed by field lines (`Key: value`, optionally as `- Key: value`):

  Kind:        increment | group                  (default increment; a group is a parent
                                                   task with child increments, never delegated)
  Parent:      TASK-nnn | none                    (the group this increment helps fulfil)
  Depends on:  TASK-nnn, TASK-mmm | none          (must be merged first; a group = all its children)
  Parallel:    yes | no                           (may be built alongside other ready increments)
  Satisfies:   R-nnn, ...                         (checked by completion-check.py)
  Diagrams:    D-nnn, ...  | none                 (the normative diagrams its brief carries)
  Scope:       path/, path/file.py, ...           (required for increments, absent for groups)
  Deferred:    owner YYYY-MM-DD                   (optional; skipped when computing readiness)

A stage heading is followed by a line `Demonstration: <what is shown live, on the product as
built, when the stage closes>` (release A1b); a stage with increments and no such line is noted.

Status is not written in the plan; it is derived from git. An increment counts as merged
when a commit on <base> has a subject that STARTS with its ID or IDs (a squash commit, a PR
title: `TASK-103 TASK-104: ...`), a merge commit whose branch name starts with the ID, a
subject whose IDs stand in parentheses at its end (`feat(x): ... (TASK-100, R-027) - v0.2.0`),
or a `Merges: TASK-nnn` trailer; a subject that merely mentions an ID ("docs: plan split
TASK-003 out of TASK-004") merges nothing (release A4). A group is merged when all its children are. A dated addendum file
(`docs/BUILD_PLAN-<date>*.md`) is read with the plan and noted as such.

Checks (exit 1 on any):
  SHAPE       duplicate IDs, unknown fields' values, increments without Scope, groups with Scope.
  PARENT      a parent that does not exist or is not a group.
  DEPENDS     a dependency that does not exist; a dependency cycle.
  PARALLEL    two `Parallel: yes` increments, neither depending on the other, whose scopes
              overlap (one path is a prefix of the other). Disjoint scopes are what let two
              builders work at once without touching the same files.
  DIAGRAMS    a named diagram missing from docs/diagrams/INDEX.md or not selected there.
  DEPENDS     also a Depends on / Parent value the parser cannot read whole (`TASK-02`): it
              fails instead of vanishing (release A4).
  BRIEF       a brief under --briefs (default handoff/) for an unmerged increment whose Scope
              reaches outside the increment's Scope, or which does not name every requirement
              the increment satisfies (release A4, 13.1). A builder's report file beside the
              brief (`TASK-nnn-rN-report.md`, 2026.10.11d) is not a brief and is not read.
Report: MERGED count, READY increments (not merged, all dependencies merged, not deferred),
and which ready increments may run together.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

ID = r"TASK-\d{3,}[a-z]?"
HEAD_RX = re.compile(r"^###\s+(%s)\s*(?:[-:—–]+)?\s*(.*)$" % ID)
FIELD_RX = re.compile(r"^\s*(?:[-*]\s+)?(Kind|Parent|Depends on|Parallel|Satisfies|Diagrams|Scope|Deferred)\s*:\s*(.*?)\s*$", re.I)
ID_RX = re.compile(ID)
D_RX = re.compile(r"\bD-\d{3,}\b")


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def ids_in(value):
    return ID_RX.findall(value or "")


def scope_paths(value):
    """The paths of a Scope field. `folder/ (a.py, b.py: note)` names folder/a.py and folder/b.py
    (the TDP's form, second pass N4); a non-breaking space is whitespace; a wildcard's prefix counts."""
    value = (value or "").replace("\u00a0", " ")
    value = re.sub(r"[*_]\([^()]*\)[*_]", "", value)           # an emphasised note `*(amended …)*` is not a path (third pass, T4)

    def expand(m):
        folder, inner = m.group(1), m.group(2)
        names = [re.split(r"[:\s]", x.strip(), 1)[0] for x in inner.split(",")]
        names = [n for n in names if n and "." in n]
        return ", ".join(folder + n for n in names) if names else folder

    value = re.sub(r"(\S+/)\s*\(([^()]*)\)", expand, value)
    out = []
    for part in re.split(r"[,;]", value):
        p = part.strip().strip("`").replace("\\", "/")
        if not p or p.lower() in ("none", "-"):
            continue
        p = re.split(r"[*?\[]", p, maxsplit=1)[0].strip()  # prefix before the first wildcard
        if p.endswith(")") and "(" not in p:
            continue                                       # the tail of a note whose opening bracket was split off
        if p:
            out.append(p.rstrip("/"))
    return out


def overlap(a, b):
    for x in a:
        for y in b:
            if x == "" or y == "" or x == y or x.startswith(y + "/") or y.startswith(x + "/"):
                return True
    return False


def parse(paths):
    items, order, fails = {}, [], []
    stage = None
    for path in paths:
        cur = None
        for line in read(path).splitlines():
            if line.startswith("## "):
                stage, cur = line[3:].strip(), None
                continue
            m = HEAD_RX.match(line)
            if m:
                tid = m.group(1)
                if tid in items:
                    fails.append("SHAPE: duplicate increment ID %s" % tid)
                    cur = None
                    continue
                cur = items[tid] = {"id": tid, "title": m.group(2).strip(), "stage": stage,
                                    "file": path, "fields": {}}
                order.append(tid)
                continue
            if line.startswith("#"):
                cur = None
                continue
            if cur is not None:
                f = FIELD_RX.match(line)
                if f:
                    cur["fields"][f.group(1).lower()] = f.group(2)
    return items, order, fails


STAGE_RX = re.compile(r"^##\s+(\S.*?)\s*$")
DEMO_RX = re.compile(r"^(?:[-*]\s+)?\**Demonstration\**\s*:\s*(\S.*)$", re.I)


def stages_without_demonstration(paths):
    """[(stage, its increment IDs)] for the stage headings (`## ...`) that hold increments and
    no `Demonstration:` line (release A1b)."""
    missing = []
    for path in paths:
        stage, seen, ids = None, False, []
        for line in read(path).splitlines():
            m = STAGE_RX.match(line)
            if m:
                if stage is not None and ids and not seen:
                    missing.append((stage, ids))
                stage, seen, ids = m.group(1).strip(), False, []
                continue
            if stage is None:
                continue
            h = HEAD_RX.match(line)
            if h:
                ids.append(h.group(1))
            elif DEMO_RX.match(line.strip()):
                seen = True
        if stage is not None and ids and not seen:
            missing.append((stage, ids))
    return missing


SUBJECT_RX = re.compile(r"^\s*((?:%s[\s,:]*)+)" % ID)                     # one or more IDs at the start: `TASK-103 TASK-104: ...`
TRAIL_RX = re.compile(r"\(([^()]*%s[^()]*)\)\s*(?:[-\u2014\u2013]\s*v?[\w.]+\s*)?(?:\(#\d+\))?\s*$" % ID)   # `feat(x): ... (TASK-100, R-027) - v0.2.0 (#148)`
MERGE_RX = re.compile(r"^\s*Merge (?:pull request #\d+ from \S+?/|branch ')(task-\d{3,}[a-z]?)\b", re.I)
BOOKKEEPING = ("docs/BUILDER_NOTES.md", "docs/BOUNDARY_VIOLATIONS.md", "run/")   # every brief names them; no plan lists them
REPORT_RX = re.compile(r"handoff/[A-Z]+-\w+-r\d+-report\.md$")                 # the builder's report file, named in every Scope (2026.10.11d)


def merged_ids(base):
    p = subprocess.run(["git", "log", base, "--format=%s%n%(trailers:key=Merges,valueonly)"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    if p.returncode != 0:
        return None
    out = set()
    for line in p.stdout.splitlines():
        m = SUBJECT_RX.match(line)
        if m:
            out.update(ID_RX.findall(m.group(1)))              # the case as written: TASK-010c is not TASK-010C
            continue
        m = MERGE_RX.match(line)
        if m:
            out.add("TASK-" + m.group(1)[5:])                  # a branch name's lower-case prefix, its letter kept
            continue
        m = TRAIL_RX.search(line)
        if m:
            out.update(ID_RX.findall(m.group(1)))              # the one extra form: the IDs in parentheses at the end
            continue
        if re.match(r"^\s*(%s)(\s*,\s*%s)*\s*$" % (ID, ID), line):      # a Merges: trailer line
            out.update(ID_RX.findall(line))
    return out


def unreadable(value):
    """What is left of a Depends on / Parent value once the IDs and the fillers are removed."""
    rest = re.sub(r"\([^()]*\)", "", value or "")                          # a dated note in parentheses is not an ID
    rest = ID_RX.sub("", rest)
    rest = re.sub(r"\bnone\b|(?<!\S)-(?!\S)", "", rest, flags=re.I)        # the fillers, never the hyphen inside TASK-02
    return re.sub(r"[,;\s]+", " ", rest).strip()


def brief_scope(text):
    """The paths of a brief's Scope, read as scope-check.py reads them (third pass, T7): top-level
    bullets up to the first non-indented line that is no bullet, an indented line continuing its
    bullet, a sub-bullet ignored; several paths per bullet; a token without a slash, a dot or a
    glob is prose, not a path."""
    raw, in_scope = [], False
    for line in text.splitlines():
        if re.match(r"^##\s+Scope\b", line, re.I):
            in_scope = True
            continue
        if not in_scope:
            continue
        if re.match(r"^#+\s", line):
            break
        if line.strip() and line[0] in " \t":
            if raw and not re.match(r"^\s*[-*]\s", line):
                raw[-1] += " " + line.strip()
            continue
        if raw and line.strip() and not re.match(r"^[-*]\s", line):
            break
        m = re.match(r"^[-*]\s+(.+?)\s*$", line)
        if m:
            raw.append(m.group(1).strip())
    out = []
    for entry in raw:
        if entry.lower().startswith("do not"):
            continue
        entry = re.split(r"\s+(?:\(|#|--|-\s|\u2014)", entry, maxsplit=1)[0]
        for piece in re.split(r"\s*,\s*|\s+and\s+|\s*;\s*", entry):
            piece = piece.strip().strip("`'\"").strip()
            if not piece:
                continue
            tok = piece.split()[0].rstrip(",;:").strip("`'\"").rstrip(",;:")
            if tok and re.match(r"^[\w.@~\[\]()*?/-]+$", tok) and re.search(r"[./*?\[]", tok):
                out.append(tok.replace("\\", "/"))
    return out


def brief_findings(path, item):
    """The brief's Scope paths outside the increment's Scope, and the increment's requirements the brief does not name."""
    text = read(path)
    scope = brief_scope(text)
    found = []
    inc = item["scope"]
    for p in scope:
        if REPORT_RX.match(p) or any(p == b or (b.endswith("/") and p.startswith(b)) for b in BOOKKEEPING):
            continue                                           # the files every brief must name (the packager's constraints)
        if not any(p == s or p.startswith(s + "/") or (s == "" ) for s in inc):
            found.append("names %s in its Scope, outside %s's Scope (%s)" % (p, item["id"], ", ".join(inc) or "none"))
    for rid in re.findall(r"\bR-\d{3,}\b", item["fields"].get("satisfies") or ""):
        if not re.search(r"\b%s\b" % rid, text):
            found.append("does not name %s, which %s satisfies" % (rid, item["id"]))
    return found


def build_parser():
    ap = argparse.ArgumentParser(description="Validate the build plan and list ready increments.")
    ap.add_argument("--plan", default="docs/BUILD_PLAN*.md")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--no-git", action="store_true", help="skip deriving merged increments from git")
    ap.add_argument("--briefs", default="handoff", help="folder of the briefs compared with their increments")
    return ap


def main():
    a = build_parser().parse_args()
    paths = sorted(glob.glob(a.plan))
    if not paths:
        print("plan-check: no plan matches %s" % a.plan)
        return 1
    items, order, fails = parse(paths)
    notes = []
    for p in paths:
        if re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(p)):
            notes.append("addendum %s read with the plan" % p.replace("\\", "/"))

    kinds = {}
    for tid in order:
        fl = items[tid]["fields"]
        kind = (fl.get("kind") or "increment").strip().lower()
        if kind not in ("increment", "group"):
            fails.append("SHAPE: %s has Kind '%s' (increment | group)" % (tid, kind))
            kind = "increment"
        kinds[tid] = kind
        par = (fl.get("parallel") or "no").strip().lower()
        if par not in ("yes", "no"):
            fails.append("SHAPE: %s has Parallel '%s' (yes | no)" % (tid, par))
        scope = scope_paths(fl.get("scope"))
        if kind == "increment" and not scope:
            fails.append("SHAPE: %s has no Scope" % tid)
        if kind == "group" and scope:
            fails.append("SHAPE: group %s has a Scope (groups are not delegated)" % tid)
        items[tid]["scope"] = scope
        items[tid]["parallel"] = par == "yes"
        items[tid]["deferred"] = bool((fl.get("deferred") or "").strip())
        if items[tid]["deferred"] and not re.search(r"owner.*\d{4}-\d{2}-\d{2}", fl.get("deferred"), re.I):
            fails.append("SHAPE: %s is deferred without the owner's dated answer" % tid)

    children = {}
    for tid in order:
        for key in ("parent", "depends on"):
            rest = unreadable(items[tid]["fields"].get(key))
            if rest:
                fails.append("DEPENDS: %s has an unreadable %s value '%s' (IDs are TASK-nnn, three digits or more)" % (tid, key.title(), rest[:40]))
        for p in ids_in(items[tid]["fields"].get("parent")):
            if p not in items:
                fails.append("PARENT: %s names parent %s, which does not exist" % (tid, p))
            elif kinds[p] != "group":
                fails.append("PARENT: %s names parent %s, which is not a group" % (tid, p))
            else:
                children.setdefault(p, []).append(tid)
    for g in [t for t in order if kinds[t] == "group"]:
        if not children.get(g):
            fails.append("SHAPE: group %s has no child increments" % g)

    def expand(tid, seen=None):
        """A dependency on a group is a dependency on all its (transitive) children."""
        if kinds.get(tid) != "group":
            return {tid}
        seen = seen or set()
        out = set()
        for c in children.get(tid, []):
            if c not in seen:
                seen.add(c)
                out |= expand(c, seen)
        return out

    deps = {}
    for tid in order:
        d = set()
        for x in ids_in(items[tid]["fields"].get("depends on")):
            if x not in items:
                fails.append("DEPENDS: %s depends on %s, which does not exist" % (tid, x))
            elif x == tid:
                fails.append("DEPENDS: %s depends on itself" % tid)
            else:
                d |= expand(x)
        deps[tid] = d - {tid}

    # cycle detection over increments (groups expanded)
    state, cycle = {}, []

    def visit(n, stack):
        state[n] = 1
        stack.append(n)
        for m in sorted(deps.get(n, ())):
            if state.get(m) == 1:
                cycle.append(stack[stack.index(m):] + [m])
            elif not state.get(m):
                visit(m, stack)
        stack.pop()
        state[n] = 2

    for tid in order:
        if not state.get(tid):
            visit(tid, [])
    for c in cycle[:5]:
        fails.append("DEPENDS: cycle %s" % " -> ".join(c))

    reach = {}

    def reachable(n):
        if n in reach:
            return reach[n]
        reach[n] = set()
        acc = set()
        for m in deps.get(n, ()):
            acc |= {m} | reachable(m)
        reach[n] = acc
        return acc

    if not cycle:
        par_items = [t for t in order if kinds[t] == "increment" and items[t]["parallel"]]
        for i, x in enumerate(par_items):
            for y in par_items[i + 1:]:
                if y in reachable(x) or x in reachable(y):
                    continue
                if overlap(items[x]["scope"], items[y]["scope"]):
                    fails.append("PARALLEL: %s and %s are both Parallel: yes, unordered, and their scopes overlap" % (x, y))

    index = "docs/diagrams/INDEX.md"
    if os.path.exists(index):
        selected = set()
        for line in read(index).splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and D_RX.fullmatch(cells[0].strip("`* ")) and cells[3].lower().startswith("selected"):
                selected.add(cells[0].strip("`* "))
        for tid in order:
            for d in D_RX.findall(items[tid]["fields"].get("diagrams") or ""):
                if d not in selected:
                    fails.append("DIAGRAMS: %s names %s, which is not a selected diagram in %s" % (tid, d, index))
    else:
        notes.append("no docs/diagrams/INDEX.md - diagram references not checked")

    merged = set()
    if not a.no_git:
        m = merged_ids(a.base)
        if m is None:
            notes.append("could not read git log of %s - readiness assumes nothing merged" % a.base)
        else:
            merged = m
    inc = [t for t in order if kinds[t] == "increment"]
    done = {t for t in inc if t in merged}
    if a.briefs and os.path.isdir(a.briefs):
        for bp in sorted(glob.glob(os.path.join(a.briefs, "TASK-*.md"))):
            if bp.endswith("-report.md"):                    # the builder's report beside its brief (2026.10.11d)
                continue
            m = ID_RX.search(os.path.basename(bp))
            tid = m.group(0) if m else None
            if tid in items and tid not in done and kinds.get(tid) == "increment":
                for finding in brief_findings(bp, items[tid]):
                    fails.append("BRIEF: %s %s" % (bp.replace("\\", "/"), finding))
    for s, ids in stages_without_demonstration(paths):
        if any(t not in merged for t in ids):                 # a closed stage is not noted
            notes.append("stage '%s' names no Demonstration: line; the stage close runs it live (release A1b), add one from the stage's increments" % s[:60])
    ready = [t for t in inc if t not in done and not items[t]["deferred"] and deps[t] <= done]
    notes.insert(0, "%d increments in %d file(s); %d merged, %d deferred" % (
        len(inc), len(paths), len(done), sum(1 for t in inc if items[t]["deferred"])))

    for n in notes:
        print("note: " + n)
    for t in ready:
        print("READY: %s  %s  [%s]%s" % (t, items[t]["title"][:60], ", ".join(items[t]["scope"])[:70],
                                        "  parallel" if items[t]["parallel"] else ""))
    rp = [t for t in ready if items[t]["parallel"]]
    for i, x in enumerate(rp):
        for y in rp[i + 1:]:
            if not overlap(items[x]["scope"], items[y]["scope"]):
                print("TOGETHER: %s + %s may be built at once (disjoint scopes)" % (x, y))
    if not ready and len(done) < len([t for t in inc if not items[t]["deferred"]]):
        print("note: nothing is ready - every remaining increment waits on an unmerged dependency")
    for f in fails:
        print(f)
    print("RESULT: %s" % ("OK" if not fails else "%d problem(s)" % len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
