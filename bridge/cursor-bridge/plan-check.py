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
subject whose closing parenthesis holds only bare IDs (`feat(x): ... (TASK-100, R-027) - v0.2.0`
merges TASK-100; `(TASK-031's Scope)` and `(pointers, TASK-031's Scope, ...)` merge nothing),
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

ID = bridge_env.PLAN_ID_PATTERN
ID_RX = re.compile(ID)
D_RX = re.compile(r"\bD-\d{3,}\b")


def read(path):
    return bridge_env.read_record_text(path)


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
    return bridge_env.plan_check_parse(paths, read)


def stages_without_demonstration(paths):
    return bridge_env.plan_stages_without_demonstration(paths, read)


BOOKKEEPING = ("docs/BUILDER_NOTES.md", "docs/BOUNDARY_VIOLATIONS.md", "run/")   # every brief names them; no plan lists them
REPORT_RX = re.compile(r"handoff/[A-Z]+-\w+-r\d+-report\.md$")                 # the builder's report file, named in every Scope (2026.10.11d)


def unreadable(value):
    """What is left of a Depends on / Parent value once the IDs and the fillers are removed."""
    rest = re.sub(r"\([^()]*\)", "", value or "")                          # a dated note in parentheses is not an ID
    rest = ID_RX.sub("", rest)
    rest = re.sub(r"\bnone\b|(?<!\S)-(?!\S)", "", rest, flags=re.I)        # the fillers, never the hyphen inside TASK-02
    return re.sub(r"[,;\s]+", " ", rest).strip()


def brief_findings(path, item):
    """The brief's Scope paths outside the increment's Scope, and the increment's requirements the brief does not name."""
    text = read(path)
    brief_name = os.path.basename(path)
    if brief_name.endswith(".md"):
        brief_name = brief_name[:-3]
    shown = path.replace("\\", "/")
    mal = bridge_env.brief_malformed_brief_line(text, shown)
    if mal:
        return [mal]
    scope = bridge_env.brief_enforced_scope_paths(text, brief_name)
    if scope is None:
        return []
    found = []
    inc = item["scope"]
    for p in scope:
        if REPORT_RX.match(p) or any(p == b or (b.endswith("/") and p.startswith(b)) for b in BOOKKEEPING):
            continue                                           # the files every brief must name (the packager's constraints)
        if not any(p == s or p.startswith(s + "/") or (s == "" ) for s in inc):
            found.append("names %s in its Scope, outside %s's Scope (%s)" % (p, item["id"], ", ".join(inc) or "none"))
    body_src = text
    rec = bridge_env.read_brief_record(text, brief_name)
    if rec.refusal is None:
        body_src = rec.body if rec.header is not None else text
    for rid in re.findall(r"\bR-\d{3,}\b", item["fields"].get("satisfies") or ""):
        if not re.search(r"\b%s\b" % rid, body_src):
            found.append("does not name %s, which %s satisfies" % (rid, item["id"]))
    return found


def historic_header_ids(header):
    ids = []
    for st in header.get("stages") or []:
        for inc in st.get("increments") or []:
            if inc.get("historic") and inc.get("id"):
                ids.append(inc["id"])
    return ids


def build_parser():
    ap = argparse.ArgumentParser(description="Validate the build plan and list ready increments.")
    ap.add_argument("--plan", default="docs/BUILD_PLAN*.md")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--no-git", action="store_true", help="skip deriving merged increments from git")
    ap.add_argument("--briefs", default="handoff", help="folder of the briefs compared with their increments")
    return ap


def main():
    a = build_parser().parse_args()
    if a.base.startswith("-"):
        print("plan-check: refusing --base %s (a base must not begin with '-')" % a.base)
        return 2
    paths = sorted(glob.glob(a.plan))
    if not paths:
        print("plan-check: no plan matches %s" % a.plan)
        return 1
    merged_set = None
    if not a.no_git:
        merged_set = bridge_env.squash_merged_ids(os.getcwd(), bridge_env.PLAN_ID_PATTERN, ref=a.base)
    header_fatal, headers_by_path = [], {}
    fails = []
    for p in paths:
        fatal, disagree, hdr = bridge_env.plan_header_findings(p, read(p), merged_set)
        header_fatal.extend(fatal)
        fails.extend(disagree)
        headers_by_path[p] = hdr
    if header_fatal:
        for line in header_fatal:
            print(line)
        return 2

    items, order, parse_fails = parse(paths)
    fails.extend(parse_fails)
    notes = []
    historic_exempt = set()
    historic_marked = []
    for p, hdr in headers_by_path.items():
        if hdr is not None:
            for iid in historic_header_ids(hdr):
                historic_marked.append(iid)
                if merged_set is None or iid in merged_set:
                    historic_exempt.add(iid)
    if merged_set is None and historic_marked:
        notes.append("historic increments not re-checked against a merged set: %s" % ", ".join(sorted(set(historic_marked))))
    for p in paths:
        if re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(p)):
            notes.append("addendum %s read with the plan" % p.replace("\\", "/"))

    kinds = {}
    paren_note_ids = []
    for tid in order:
        fl = items[tid]["fields"]
        scope_raw = fl.get("scope")
        exempt = tid in historic_exempt
        kind = (fl.get("kind") or "increment").strip().lower()
        if not exempt:
            if kind not in ("increment", "group"):
                fails.append("SHAPE: %s has Kind '%s' (increment | group)" % (tid, kind))
                kind = "increment"
        else:
            kind = "increment"
        kinds[tid] = kind
        par = (fl.get("parallel") or "no").strip().lower()
        if not exempt and par not in ("yes", "no"):
            fails.append("SHAPE: %s has Parallel '%s' (yes | no)" % (tid, par))
        if exempt:
            par = "no"
        scope = scope_paths(fl.get("scope")) if not exempt else []
        if not exempt and kind == "increment" and not scope:
            fails.append("SHAPE: %s has no Scope" % tid)
        if not exempt and kind == "group" and scope:
            fails.append("SHAPE: group %s has a Scope (groups are not delegated)" % tid)
        if not exempt and scope_raw and merged_set is not None and tid not in merged_set:
            if bridge_env.plan_scope_paren_unbalanced(scope_raw):
                fails.append("SHAPE: %s has an unbalanced parenthesis in its Scope" % tid)
        if not exempt and merged_set is None and scope_raw and bridge_env.plan_scope_paren_unbalanced(scope_raw):
            paren_note_ids.append(tid)
        items[tid]["scope"] = scope
        items[tid]["parallel"] = par == "yes"
        items[tid]["deferred"] = bool((fl.get("deferred") or "").strip())
        if items[tid]["deferred"] and not re.search(r"owner.*\d{4}-\d{2}-\d{2}", fl.get("deferred"), re.I):
            fails.append("SHAPE: %s is deferred without the owner's dated answer" % tid)

    children = {}
    for tid in order:
        if tid not in historic_exempt:
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
        index_text = read(index)
        shown_index = index.replace("\\", "/")
        index_header = None
        index_body = index_text
        try:
            index_header, index_body = bridge_env.read_header(index_text)
        except bridge_env.HeaderError as err:
            print("HEADER MALFORMED: %s:%d %s" % (shown_index, err.line, str(err)))
            print("RESULT: not checked")
            return 2
        if index_header is not None:
            findings = bridge_env.check_header("diagram-index", index_header)
            if findings:
                print("HEADER MALFORMED: %s:1 %s" % (shown_index, "; ".join(findings)))
                print("RESULT: not checked")
                return 2
            selected = bridge_env.diagram_index_selected_ids(index_body or "", index_header)
        else:
            selected = bridge_env.diagram_index_selected_ids(index_text, None)
        for tid in order:
            for d in D_RX.findall(items[tid]["fields"].get("diagrams") or ""):
                if d not in selected:
                    fails.append("DIAGRAMS: %s names %s, which is not a selected diagram in %s" % (tid, d, index))
    else:
        notes.append("no docs/diagrams/INDEX.md - diagram references not checked")

    merged_ready = set() if merged_set is None else merged_set
    if merged_set is None and not a.no_git:
        notes.append("could not read git log of %s - readiness assumes nothing merged" % a.base)
    inc = [t for t in order if kinds[t] == "increment"]
    done = {t for t in inc if t in merged_ready}
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
        if any(t not in merged_ready for t in ids):                 # a closed stage is not noted
            notes.append("stage '%s' names no Demonstration: line; the stage close runs it live (release A1b), add one from the stage's increments" % s[:60])
    ready = [t for t in inc if t not in done and not items[t]["deferred"] and deps[t] <= done]
    if paren_note_ids:
        notes.append(
            "unbalanced parenthesis in Scope not checked against a merged set: %s"
            % ", ".join(sorted(set(paren_note_ids)))
        )
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
