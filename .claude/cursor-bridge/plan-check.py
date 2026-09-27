#!/usr/bin/env python3
"""plan-check: is the build plan well-formed, and which increments are ready to build?

  python plan-check.py [--plan "docs/BUILD_PLAN*.md"] [--base origin/main] [--no-git]

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

Status is not written in the plan; it is derived from git. An increment counts as merged
when a commit on <base> names its ID in the subject (PR titles and squash commits start with
the increment ID). A group is merged when all its children are.

Checks (exit 1 on any):
  SHAPE       duplicate IDs, unknown fields' values, increments without Scope, groups with Scope.
  PARENT      a parent that does not exist or is not a group.
  DEPENDS     a dependency that does not exist; a dependency cycle.
  PARALLEL    two `Parallel: yes` increments, neither depending on the other, whose scopes
              overlap (one path is a prefix of the other). Disjoint scopes are what let two
              builders work at once without touching the same files.
  DIAGRAMS    a named diagram missing from docs/diagrams/INDEX.md or not selected there.
Report: MERGED count, READY increments (not merged, all dependencies merged, not deferred),
and which ready increments may run together.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

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
    out = []
    for part in re.split(r"[,;]", value or ""):
        p = part.strip().strip("`").replace("\\", "/")
        if not p or p.lower() in ("none", "-"):
            continue
        p = re.split(r"[*?\[]", p, maxsplit=1)[0]          # prefix before the first wildcard
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


def merged_ids(base):
    p = subprocess.run(["git", "log", base, "--format=%s"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return None
    return set(ID_RX.findall(p.stdout))


def main():
    ap = argparse.ArgumentParser(description="Validate the build plan and list ready increments.")
    ap.add_argument("--plan", default="docs/BUILD_PLAN*.md")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--no-git", action="store_true", help="skip deriving merged increments from git")
    a = ap.parse_args()
    paths = sorted(glob.glob(a.plan))
    if not paths:
        print("plan-check: no plan matches %s" % a.plan)
        return 1
    items, order, fails = parse(paths)
    notes = []

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
    sys.exit(main())
