#!/usr/bin/env python3
"""completion-check: is every specified requirement planned, built and tested - or deferred by
the owner - and does the shipped code contain no stand-ins presented as features?

  python completion-check.py [--mode plan|done] [--requirements docs/REQUIREMENTS.md]

Run from the Workspace root. Deterministic; reads only. ASCII output.

docs/REQUIREMENTS.md holds one table (see supervisor.md, "The requirements register"):
  | ID | Requirement | Source | Status | Evidence |
  ID      R-001, R-002, ...                 (never reused, never renumbered)
  Status  planned | built | deferred - owner YYYY-MM-DD | dropped - owner YYYY-MM-DD

--mode plan  (plan gate, every stage close)
  REGISTER    the register exists, rows are well-formed, IDs unique.
  UNPLANNED   a planned/built requirement that no docs/BUILD_PLAN*.md mentions.
  UNAPPROVED  a deferred/dropped row without "owner" and a date.
  stand-ins are listed as notes (mid-build a later stage may legitimately be pending).
--mode done  (project end, and the start of every change cycle) - everything above, plus:
  NOT BUILT   a requirement still `planned`.
  NO EVIDENCE a `built` requirement whose ID appears in no tracked test file. Tests carry the
              requirement ID (a comment, docstring, or test name) - that is the trace.
  STAND-IN    shipped (non-test) code shows a user-visible stand-in: "arrives in a later
              stage", "coming soon", "not yet implemented/available", "under construction",
              a *Placeholder{View,Page,Screen,Tab,Panel} component, todo!()/unimplemented!().
              Allowed only on a line that names the ID of an owner-deferred requirement.
Notes never fail: TODO/FIXME counts and NotImplementedError sites (often legitimate
abstract methods) in shipped code.
Exit 0 = OK, 1 = at least one failure.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

ID_RX = re.compile(r"\bR-\d{3,}\b")
STATUS_OK = re.compile(r"^(planned|built|(deferred|dropped)\b.*)$", re.I)
OWNER_DATED = re.compile(r"\bowner\b.*\d{4}-\d{2}-\d{2}", re.I)
STANDIN_RX = re.compile(
    r"arrives?\s+in\s+a\s+later\s+(stage|version|release|update)"
    r"|coming\s+soon"
    r"|not\s+yet\s+(implemented|available|built|supported)"
    r"|\bnot\s+implemented\s+yet\b"
    r"|under\s+construction"
    r"|to\s+be\s+implemented"
    r"|\b\w*Placeholder(View|Page|Screen|Tab|Panel|Section)\b"
    r"|\btodo!\s*\(|\bunimplemented!\s*\(", re.I)
NOTE_RX = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b|NotImplementedError")
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte", ".html",
            ".htm", ".css", ".scss", ".cs", ".rs", ".go", ".java", ".kt", ".swift", ".dart",
            ".rb", ".php", ".ps1", ".xaml", ".qml"}
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs|e2e|testing|fixtures)(/|$)"
                       r"|(^|/)test_[^/]*$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$", re.I)
SKIP_PATH = re.compile(r"(^|/)(docs|\.claude|\.cursor|\.github|node_modules|vendor|third_party|"
                       r"dist|build|bench|benchmarks|scripts/dev)(/|$)", re.I)


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def tracked():
    p = subprocess.run(["git", "ls-files", "-z"], capture_output=True, creationflags=NO_WINDOW)
    if p.returncode != 0:
        return None
    return [f for f in p.stdout.decode("utf-8", "replace").split("\0") if f]


def parse_register(text):
    rows, header = [], None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if header is None:
            header = [c.lower() for c in cells]
            continue
        rows.append(cells)
    return header, rows


def main():
    ap = argparse.ArgumentParser(description="Check requirements coverage and shipped stand-ins.")
    ap.add_argument("--mode", choices=("plan", "done"), default="done")
    ap.add_argument("--requirements", default="docs/REQUIREMENTS.md")
    a = ap.parse_args()
    fails, notes = [], []
    done = a.mode == "done"

    reqs = {}
    if not os.path.exists(a.requirements):
        fails.append("REGISTER: %s does not exist" % a.requirements)
    else:
        header, rows = parse_register(read(a.requirements))
        want = ["id", "requirement", "source", "status", "evidence"]
        if header is None or [h.split()[0] if h else "" for h in header][:5] != want:
            fails.append("REGISTER: header must be | ID | Requirement | Source | Status | Evidence |")
        for r in rows:
            if len(r) < 5 or not all(r[:4]):
                fails.append("REGISTER: malformed row: %s" % " | ".join(r)[:120])
                continue
            rid = r[0].strip("`* ")
            if not re.fullmatch(r"R-\d{3,}", rid):
                fails.append("REGISTER: bad ID '%s' (use R-001 ...)" % rid)
                continue
            if rid in reqs:
                fails.append("REGISTER: duplicate ID %s" % rid)
                continue
            status = r[3].strip("`* ")
            if not STATUS_OK.match(status):
                fails.append("REGISTER: %s has status '%s' (planned | built | deferred - owner <date> | dropped - owner <date>)" % (rid, status[:40]))
                continue
            kind = status.split()[0].lower()
            if kind in ("deferred", "dropped") and not OWNER_DATED.search(status):
                fails.append("UNAPPROVED: %s is %s without the owner's approval and a date (%s)" % (rid, kind, status[:60]))
            reqs[rid] = (kind, r[1])
        if not reqs and not any(f.startswith("REGISTER") for f in fails):
            fails.append("REGISTER: %s has no requirement rows" % a.requirements)

    # plan coverage
    plans = sorted(glob.glob("docs/BUILD_PLAN*.md"))
    plan_text = "\n".join(read(p) for p in plans)
    if not plans:
        notes.append("no docs/BUILD_PLAN*.md found - plan coverage not checked")
    else:
        for rid, (kind, text) in sorted(reqs.items()):
            if kind in ("planned", "built") and not re.search(r"\b%s\b" % re.escape(rid), plan_text):
                fails.append("UNPLANNED: %s (%s) is in no build plan increment" % (rid, text[:70]))

    files = tracked()
    if files is None:
        notes.append("not a git repository - evidence and stand-ins not checked")
        files = []
    tests = [f for f in files if TEST_PATH.search(f.replace("\\", "/"))]
    shipped = [f for f in files if os.path.splitext(f)[1].lower() in CODE_EXT
               and not TEST_PATH.search(f.replace("\\", "/")) and not SKIP_PATH.search(f.replace("\\", "/"))]

    # completion
    if done:
        test_ids = set()
        for f in tests:
            try:
                test_ids.update(ID_RX.findall(read(f)))
            except OSError:
                pass
        for rid, (kind, text) in sorted(reqs.items()):
            if kind == "planned":
                fails.append("NOT BUILT: %s (%s) is still planned" % (rid, text[:70]))
            elif kind == "built" and rid not in test_ids:
                fails.append("NO EVIDENCE: %s (%s) is marked built but no tracked test names it" % (rid, text[:60]))

    # stand-ins
    deferred_ids = {rid for rid, (kind, _) in reqs.items() if kind in ("deferred", "dropped")}
    standins, note_count, nie = [], 0, 0
    for f in shipped:
        try:
            text = read(f)
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if STANDIN_RX.search(line):
                if set(ID_RX.findall(line)) & deferred_ids:
                    continue
                standins.append("%s:%d: %s" % (f.replace("\\", "/"), n, line.strip()[:100]))
            elif NOTE_RX.search(line):
                if "NotImplementedError" in line:
                    nie += 1
                else:
                    note_count += 1
    for s in standins[:40]:
        (fails if done else notes).append(("STAND-IN: " if done else "stand-in (fails at done): ") + s)
    if len(standins) > 40:
        (fails if done else notes).append("... and %d more stand-ins" % (len(standins) - 40))
    if note_count or nie:
        notes.append("shipped code: %d TODO/FIXME/XXX/HACK markers, %d NotImplementedError sites (review, not a failure)" % (note_count, nie))

    counts = {}
    for kind, _ in reqs.values():
        counts[kind] = counts.get(kind, 0) + 1
    notes.insert(0, "mode %s; requirements: %s" % (a.mode, ", ".join("%d %s" % (v, k) for k, v in sorted(counts.items())) or "none"))
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
