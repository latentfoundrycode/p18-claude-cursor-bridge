#!/usr/bin/env python3
"""records-check: has every increment merged since a commit its docs/CHANGES.md line?

  python ~/.claude/cursor-bridge/records-check.py --since <commit> [--ref origin/main]
                                                  [--changes docs/CHANGES.md]

Run from the Workspace root, before a stage review (2026-10-18 C1; reAngle ISS-022, FB-002:
two of five stage-review rounds rejected on a missing CHANGES.md line, which a script sees).
Deterministic; reads only. Every commit on <ref>'s first-parent line after <since> (the
stage's first checkpoint; `git log --first-parent <since>..<ref>`) whose subject carries a
TASK-nnn, BUG-nnn or FIX-nnn id must have a line in docs/CHANGES.md AS IT STANDS AT <ref>
(read with `git show`, never the working tree) that names that id. An id is three digits or
more and may carry one lower-case letter (TASK-059e); the case is kept as written, and
TASK-059 is not TASK-059e. The subject forms are plan-check.py's: ids at the start
(`TASK-103 TASK-104: ...`, `BUG-027: ... (#81)`), a merge of a branch whose name starts with
the id (`Merge pull request #12 from x/task-012-...`), ids in parentheses at the end
(`feat(x): ... (TASK-100, R-027) - v0.2.0 (#148)`), or a `Merges:` trailer. A subject that
merely mentions an id (`docs: plan split TASK-003 out of TASK-004`) carries none. A line names
an id when the id stands in it whole: `TASK-003 to TASK-007` names two ids, not five.

Output: one MISSING line per id without its line (commit, id, subject), then a RESULT line.
Exit 0 = every id has its line; 1 = at least one MISSING; 2 = cannot read (not a git
repository, <since> or <ref> names no commit, <since> is not an ancestor of <ref>, or the
changes file is not at <ref>). ASCII-only on purpose (cp1252 consoles).
"""
import argparse
import re
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

ID = r"(?:TASK|BUG|FIX)-\d{3,}[a-z]?"                                         # plan-check.py's TASK id, the BUG and FIX ids beside it
ID_RX = re.compile(ID)
SUBJECT_RX = re.compile(r"^\s*((?:%s[\s,:]*)+)" % ID)                          # one or more ids at the start: `TASK-103 TASK-104: ...`
TRAIL_RX = re.compile(r"\(([^()]*%s[^()]*)\)\s*(?:[-—–]\s*v?[\w.]+\s*)?(?:\(#\d+\))?\s*$" % ID)   # `feat(x): ... (TASK-100, R-027) - v0.2.0 (#148)`
MERGE_RX = re.compile(r"^\s*Merge (?:pull request #\d+ from \S+?/|branch ')((?:task|bug|fix)-\d{3,}[a-z]?)\b", re.I)
TRAILER_RX = re.compile(r"^\s*(%s)(\s*,\s*%s)*\s*$" % (ID, ID))                # a Merges: trailer line
NAMED_RX = re.compile(r"(?<![A-Za-z0-9])(%s)(?![A-Za-z0-9])" % ID)             # an id standing whole in a CHANGES.md line


def git(*args):
    try:
        p = subprocess.run(["git", "-c", "core.fsmonitor=false"] + list(args), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    except OSError:
        return None
    return p.stdout if p.returncode == 0 else None


def ids_of(subject, trailers):
    """The ids a commit carries, by plan-check.py's forms; [] for a subject that merely mentions one."""
    out = []
    m = SUBJECT_RX.match(subject)
    if m:
        out += ID_RX.findall(m.group(1))
    else:
        m = MERGE_RX.match(subject)
        if m:
            name = m.group(1)
            out.append(name[:name.index("-")].upper() + name[name.index("-"):])    # a branch name's lower-case prefix, its letter kept
        else:
            m = TRAIL_RX.search(subject)
            if m:
                out += ID_RX.findall(m.group(1))
    for line in trailers.splitlines():
        if TRAILER_RX.match(line):
            out += ID_RX.findall(line)
    seen = []
    for i in out:
        if i not in seen:
            seen.append(i)
    return seen


def commits(since, ref):
    """[(short sha, subject, ids)] of <ref>'s first-parent line after <since>, oldest first; None when git fails."""
    out = git("log", "--first-parent", "--reverse", "--format=%x1e%h%x1f%s%x1f%(trailers:key=Merges,valueonly)", "%s..%s" % (since, ref))
    if out is None:
        return None
    found = []
    for rec in out.split("\x1e"):
        if not rec.strip():
            continue
        parts = rec.split("\x1f")
        sha, subject, trailers = parts[0].strip(), parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else ""
        found.append((sha, subject.strip(), ids_of(subject, trailers)))
    return found


def main():
    ap = argparse.ArgumentParser(description="Every TASK/BUG/FIX id merged since a commit has its docs/CHANGES.md line.")
    ap.add_argument("--since", required=True, help="the stage's first checkpoint commit")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--changes", default="docs/CHANGES.md")
    a = ap.parse_args()
    if git("rev-parse", "--is-inside-work-tree") is None:
        print("records-check: not inside a git repository; cannot read")
        return 2
    for name, value in (("--since", a.since), ("--ref", a.ref)):
        if git("rev-parse", "--verify", "--quiet", value + "^{commit}") is None:
            print("records-check: %s %s names no commit (fetched?); cannot read" % (name, value))
            return 2
    try:
        p = subprocess.run(["git", "merge-base", "--is-ancestor", a.since, a.ref], capture_output=True, creationflags=NO_WINDOW)
    except OSError:
        p = None
    if p is None or p.returncode != 0:
        print("records-check: %s is not an ancestor of %s, so %s..%s is not the commits merged since it; cannot read" % (a.since, a.ref, a.since, a.ref))
        return 2
    changes_path = a.changes.replace("\\", "/")
    if changes_path.startswith("./"):
        changes_path = changes_path[2:]                       # a path in the tree at <ref>, as git show reads it
    text = git("show", "%s:%s" % (a.ref, changes_path))
    if text is None:
        print("records-check: %s is not readable at %s; cannot read" % (changes_path, a.ref))
        return 2
    named = set()
    for line in text.splitlines():
        named.update(NAMED_RX.findall(line))
    found = commits(a.since, a.ref)
    if found is None:
        print("records-check: git log %s..%s failed; cannot read" % (a.since, a.ref))
        return 2
    carried, missing = 0, []
    for sha, subject, ids in found:
        for i in ids:
            carried += 1
            if i not in named:
                missing.append((sha, i, subject))
    for sha, i, subject in missing:
        print("MISSING  %s  %-10s %s" % (sha, i, subject.encode("ascii", "replace").decode("ascii")[:100]))
    print("RESULT: %d commit(s) in %s..%s, %d id(s) carried, %d without a line in %s at %s" % (
        len(found), a.since, a.ref, carried, len(missing), changes_path, a.ref))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
