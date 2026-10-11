#!/usr/bin/env python3
"""
Bridge scope check - deterministic changeset-vs-brief verification.

After a delegation (run from the clean checkpoint commit), this compares what the builder
ACTUALLY changed - derived from git, never from the builder's own summary - against the
Scope the handoff brief declared. Any changed file outside that Scope is SCOPE DRIFT, and
it is surfaced deterministically here rather than discovered by eyeballing a diff.

Why git-derived: the builder's printed "files I changed" list is a self-report and has been
wrong in practice (claimed fixes not made, unrequested edits described as requested ones).
The working tree is the only trustworthy manifest. Region-level drift *within* an in-scope
file is still diff-reviewer's judgement; this tool owns the file-level floor.

Usage:
    python scope-check.py handoff/TASK-<nnn>.md [--base <git-ref>]

    --base   commit to diff against. Default: the commit that last touched the brief (the
             checkpoint commits the brief), so a builder's own commits are inside the diff;
             HEAD when the brief is not committed.

Exit codes:
    0  every changed file is inside the declared Scope
    1  SCOPE DRIFT - one or more changed files are outside Scope (listed on stdout)
    2  cannot verify (brief missing, no Scope section, or git failed) - treat as
       needs-attention; do NOT proceed as if scope were clean.

Scope entries (bullets under "## Scope", up to the next heading of any level) may be exact
files, directories (trailing "/" or a bare directory name), or globs (* and ?; brackets are
literal, as in a route folder `[id]`). A bullet may name several paths (commas, "and"),
quoted or in backticks; prose after a path is dropped; an ellipsis cannot be verified.
The bookkeeping files a builder must write (docs/BUILDER_NOTES.md, docs/BOUNDARY_VIOLATIONS.md,
anything under run/) are never drift. Paths are compared with forward slashes.
"""

import fnmatch
import re
import subprocess
import sys

# Windows: never pop a console window (bridge windowless-by-default policy).
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _run_git(args):
    try:
        out = subprocess.run(["git"] + args, capture_output=True, text=True, check=True,
                             creationflags=NO_WINDOW)
        return out.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("CANNOT VERIFY: git command failed: git %s (%s)" % (" ".join(args), e))
        sys.exit(2)


def _norm(p):
    p = p.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


BOOKKEEPING = ("docs/BUILDER_NOTES.md", "docs/BOUNDARY_VIOLATIONS.md", "run/")
PATH_RX = re.compile(r"^[\w.@~\[\]()*?/-]+$")


def bookkeeping(path):
    return any(path == b or (b.endswith("/") and path.startswith(b)) for b in BOOKKEEPING)


def split_entry(entry):
    """The paths one bullet names: `a.py`, `b.py` and "c.py" -> three; prose after a path dropped."""
    entry = re.split(r"\s+(?:\(|#|--|-\s|—)", entry, maxsplit=1)[0]
    out = []
    for piece in re.split(r"\s*,\s*|\s+and\s+|\s*;\s*", entry):
        piece = piece.strip().strip("`'\"").strip()
        if not piece:
            continue
        tok = piece.split()[0].rstrip(",;:").strip("`'\"").rstrip(",;:")
        if "..." in tok or "\u2026" in tok:
            return None
        if tok and PATH_RX.match(tok) and re.search(r"[./*?\[]", tok):   # a path has a slash, a dot or a glob; a bare word is prose
            out.append(tok)
        else:
            UNREAD.append(piece[:60])                          # reported, never dropped in silence
    return out


UNREAD = []


def parse_scope(brief_path):
    try:
        text = open(brief_path, encoding="utf-8-sig").read()
    except OSError as e:
        print("CANNOT VERIFY: brief not readable: %s (%s)" % (brief_path, e))
        sys.exit(2)

    # Collect bullet lines under the "## Scope" heading, up to the next "## " heading.
    in_scope, entries = False, []
    for line in text.splitlines():
        if re.match(r"^##\s+Scope\b", line, re.IGNORECASE):
            in_scope = True
            continue
        if in_scope and re.match(r"^#+\s+", line):
            break                                          # any heading ends the Scope, a `### Out of scope` included
        if in_scope:
            m = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
            if m:
                entry = m.group(1).strip()
                if entry.lower().startswith("do not"):
                    continue
                paths = split_entry(entry)
                if paths is None:
                    print("CANNOT VERIFY: a Scope entry carries an ellipsis (%s); name every path or a glob." % entry[:80])
                    sys.exit(2)
                entries.extend(_norm(p) for p in paths)
    if not entries:
        print("CANNOT VERIFY: no Scope entries found under '## Scope' in %s "
              "(spec-packager defect - the brief must fence its scope)." % brief_path)
        sys.exit(2)
    return entries


RECORDS = ("docs/BUILD_PLAN", "docs/INVENTORY.md", "docs/CHANGES.md", "docs/REQUIREMENTS.md", "docs/PROJECT_STATUS.md",
           "docs/RUN_PARAMETERS.md", "docs/DESIGN.md", "docs/diagrams/", "handoff/")


def checkpoint_of(brief):
    """(the commit that first added the brief, the number of later commits that touched it): the
    checkpoint commits the brief before the delegation; a brief fixed and committed later must
    not move the base past the builder's commits. (None, 0) when the brief is not committed."""
    added = _run_git(["log", "--diff-filter=A", "--format=%H", "--", brief]).split()
    if not added:
        return None, 0
    base = added[-1]
    later = _run_git(["log", "--format=%H", base + "..HEAD", "--", brief]).split()
    return base, len(later)


def is_record(path):
    return any(path == r or path.startswith(r) for r in RECORDS)


def supervisors_own(path, base, uncommitted):
    """A records file changed only by the supervisor's own commits since the checkpoint (every
    author is the checkout's user.email) and not in the working tree: the supervisor's bookkeeping,
    not the builder's drift. A builder's commit carries another identity (the owner's is withheld)."""
    if path in uncommitted:
        return False
    mine = _run_git(["config", "user.email"]).strip()
    authors = _run_git(["log", "--format=%ae", base + "..HEAD", "--", path]).split()
    return bool(mine) and bool(authors) and all(a == mine for a in authors)


def changed_files(base):
    files = set()
    # Tracked files modified/added/deleted relative to the checkpoint; a rename shows both paths.
    for line in _run_git(["diff", "--name-only", "--no-renames", base]).splitlines():
        if line.strip():
            files.add(_norm(line))
    # Untracked new files (git diff does not show these) - list individually.
    for line in _run_git(["status", "--porcelain", "-uall"]).splitlines():
        if line.startswith("??"):
            files.add(_norm(line[3:]))
    return sorted(files)


def in_scope(path, entries):
    for e in entries:
        e_dir = e.rstrip("/")
        if path == e or path == e_dir or path.startswith(e_dir + "/"):
            return True                                    # literal first: a bracketed folder is a folder
        if any(ch in e for ch in "*?"):
            g = e.replace("[", "[[]")                      # brackets stay literal inside the glob
            if fnmatch.fnmatch(path, g) or fnmatch.fnmatch(path, g.rstrip("/") + "/*"):
                return True
    return False


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        sys.exit(2)
    brief = argv[1]
    base = None
    if "--base" in argv:
        i = argv.index("--base")
        if i + 1 < len(argv):
            base = argv[i + 1]
    note = ""
    if base is None:
        base, later = checkpoint_of(_norm(brief))
        note = " (the checkpoint: the commit that first added the brief%s)" % ("; the brief was changed in %d later commit(s), the base stays" % later if later else "") if base else ""
        if base is None:
            base = "HEAD"
            note = " (the brief is not committed; HEAD. A builder's own commit is inside the diff only with --base <checkpoint>)"

    entries = parse_scope(brief)
    changed = changed_files(base)
    uncommitted = {_norm(l[3:]) for l in _run_git(["status", "--porcelain", "-uall"]).splitlines() if len(l) > 3}

    books = [p for p in changed if bookkeeping(p)]
    changed = [p for p in changed if not bookkeeping(p)]
    records = [p for p in changed if is_record(p) and not in_scope(p, entries) and base != "HEAD" and supervisors_own(p, base, uncommitted)]
    changed = [p for p in changed if p not in records]
    inside = [p for p in changed if in_scope(p, entries)]
    drift = [p for p in changed if not in_scope(p, entries)]

    print("BRIEF:        %s" % brief)
    print("BASE:         %s%s" % (base, note))
    print("SCOPE:        %s" % ", ".join(entries))
    for u in UNREAD:
        print("NOT READ AS A PATH: %s" % u)
    print("CHANGED (%d): %s" % (len(changed), ", ".join(changed) if changed else "(none)"))
    if books:
        print("BOOKKEEPING (%d), never drift: %s" % (len(books), ", ".join(books)))
    if records:
        print("RECORDS (%d), the supervisor's own commits since the checkpoint, not drift: %s" % (len(records), ", ".join(records)))
    print("IN SCOPE (%d): %s" % (len(inside), ", ".join(inside) if inside else "(none)"))
    if drift:
        print("SCOPE DRIFT (%d) - outside the brief's Scope:" % len(drift))
        for p in drift:
            print("  - %s" % p)
        print("VERDICT: SCOPE DRIFT")
        sys.exit(1)
    print("VERDICT: SCOPE CLEAN")
    sys.exit(0)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    main(sys.argv)
