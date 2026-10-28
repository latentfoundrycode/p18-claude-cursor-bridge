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

    --base   commit to diff against. Default: the commit that FIRST added the brief (the
             checkpoint commits the brief; a brief fixed and committed later never moves the
             base past the builder's commits); HEAD when the brief is not committed. For a
             re-delegation, give the commit that committed THAT round's brief, so the
             supervisor's commits between rounds are not measured (FB-014). A --base without a
             value, or one that names no commit, cannot be verified (exit 2).

Output lines: BASE (with how it was chosen), SCOPE, NOT READ AS A PATH (a Scope bullet that
names no path, reported and ignored), CHANGED, BOOKKEEPING (the files a builder must write),
RECORDS (the supervisor's record files changed only by commits that touched records alone
since the checkpoint: not drift; a commit that mixes code with a record is the builder's),
SUPERVISOR TESTS (test files changed only by the supervisor's commits: a commit of records and
test files alone whose subject starts with `supervisor:`, rule N4; such a commit's records are
the supervisor's too. The subject is a convention the supervisor writes, not proof: every
commit carries the owner's identity), IN SCOPE, SCOPE DRIFT, VERDICT. The Scope is the
brief's top-level bullets up to the first line that is neither a bullet nor blank (a bold
note, prose): sub-bullets are not paths.

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
anything under run/, its report file handoff/<brief>-rN-report.md) are never drift. Paths are compared with forward slashes.
"""

import fnmatch
import os
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
REPORT_RX = re.compile(r"handoff/[A-Z]+-\w+-r\d+-report\.md$")          # the builder's report, written as it runs (2026.10.11d)
PATH_RX = re.compile(r"^[\w.@~\[\]()*?/-]+$")


def bookkeeping(path):
    return bool(REPORT_RX.match(path)) or any(path == b or (b.endswith("/") and path.startswith(b)) for b in BOOKKEEPING)


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
    in_scope, entries, raw = False, [], []
    for line in text.splitlines():
        if re.match(r"^##\s+Scope\b", line, re.IGNORECASE):
            in_scope = True
            continue
        if in_scope and re.match(r"^#+\s+", line):
            break                                          # any heading ends the Scope, a `### Out of scope` included
        if in_scope:
            if line.strip() and line[0] in " \t":
                if raw and not re.match(r"^\s*[-*]\s", line):
                    raw[-1] += " " + line.strip()          # an indented line continues its bullet (third pass, T2)
                continue                                   # an indented bullet is a sub-bullet, not a path
            if raw and line.strip() and not re.match(r"^[-*]\s", line):
                break                                      # a bold note or prose after the path list ends the Scope (N8)
            m = re.match(r"^[-*]\s+(.+?)\s*$", line)      # top-level bullets only
            if m:
                raw.append(m.group(1).strip())
    for entry in raw:
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
           "docs/RUN_PARAMETERS.md", "docs/DESIGN.md", "docs/diagrams/", "handoff/",
           "docs/DESIGN_CRITIQUE.md", "docs/HARDENING.md", "project.json")           # FB-009: the supervisor writes these too
TEST_DIRS = ("tests", "test", "__tests__", "spec")
TEST_NAME_RX = re.compile(r"^(test_.+\.py|.+_test\.(py|go)|.+\.(test|spec)\.[A-Za-z]+|conftest\.py)$")
SUPERVISOR_SUBJECT = "supervisor:"


def is_test(path):
    """A test file: under a tests folder, or named as one (test_x.py, x_test.py, x.test.ts, x.spec.js)."""
    parts = path.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME_RX.match(parts[-1]))


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
    """A records or test file changed, since the checkpoint, only by the supervisor's commits and
    not in the working tree: a commit that touched records and bookkeeping alone (the record
    keeping), or one of records, bookkeeping and test files alone whose subject starts with
    `supervisor:` (its tests, rule N4; 2026-10-25 C6). A commit that mixes code with a record is
    the builder's, and its record edit is drift. Authorship cannot tell the two apart: every commit
    on the computer carries the owner's git identity (second pass, N1)."""
    if path in uncommitted:
        return False
    shas = _run_git(["log", "--format=%H", base + "..HEAD", "--", path]).split()
    if not shas:
        return False
    for sha in shas:
        files = [_norm(f) for f in _run_git(["show", "--name-only", "--format=", sha]).splitlines() if f.strip()]
        if files and all(is_record(f) or bookkeeping(f) for f in files):
            continue
        subject = _run_git(["show", "-s", "--format=%s", sha]).strip()
        if not files or not subject.lower().startswith(SUPERVISOR_SUBJECT) or not all(is_record(f) or bookkeeping(f) or is_test(f) for f in files):
            return False
        if any(is_test(f) for f in files) and during_a_builder_run(sha):
            return False                               # a builder commits in the parallel variant: a test commit made while one ran is not the supervisor's
    return True


def builder_windows():
    """[(start, end)] in epoch seconds of every builder run in the launcher's log (run/launcher/runs.jsonl,
    read from the current folder, the Workspace), each end at id + waited + seconds + two minutes of slack; None when the log
    cannot be read, so the `supervisor:` test exemption fails closed (the review of 2026.10.25a)."""
    import datetime
    import json
    try:
        with open(os.path.join("run", "launcher", "runs.jsonl"), encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    out = []
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    for line in lines:
        try:
            e = json.loads(line)
            if not isinstance(e, dict) or e.get("kind") != "builder":
                continue
            if e.get("branch") and branch and e.get("branch") != branch:
                continue                               # another branch's builder (the parallel variant) did not commit here
            start = datetime.datetime.strptime(str(e.get("id", ""))[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()
        except (ValueError, TypeError):
            continue
        seconds = e.get("seconds") if isinstance(e.get("seconds"), (int, float)) else e.get("limit") or 7200
        waited = e.get("waited") if isinstance(e.get("waited"), (int, float)) else 0
        out.append((start, start + float(waited) + float(seconds) + 120))
    return out


def during_a_builder_run(sha):
    windows = builder_windows()
    if windows is None:
        return True
    try:
        when = int(_run_git(["show", "-s", "--format=%ct", sha]).strip())
    except ValueError:
        return True
    return any(a <= when <= b for a, b in windows)


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
    base = None
    if "--base" in argv:
        i = argv.index("--base")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            print("CANNOT VERIFY: --base needs a commit (for a re-delegation, the commit that committed the round's brief)")
            sys.exit(2)
        base = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) < 2:
        print(__doc__)
        sys.exit(2)
    brief = argv[1]
    note = ""
    if base is not None:
        try:
            subprocess.run(["git", "rev-parse", "-q", "--verify", base + "^{commit}"], capture_output=True, text=True, check=True,
                           creationflags=NO_WINDOW)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("CANNOT VERIFY: --base %s names no commit" % base)
            sys.exit(2)
        note = " (given with --base: measured from that commit, not from the brief's first commit)"
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
    own = [p for p in changed if (is_record(p) or is_test(p)) and not in_scope(p, entries) and base != "HEAD" and supervisors_own(p, base, uncommitted)]
    records = [p for p in own if is_record(p)]
    tests = [p for p in own if not is_record(p)]
    changed = [p for p in changed if p not in own]
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
        print("RECORDS (%d), changed only by records-only commits or the supervisor's since the checkpoint, not drift: %s" % (len(records), ", ".join(records)))
    if tests:
        print("SUPERVISOR TESTS (%d), changed only by `supervisor:` commits of records and tests since the checkpoint, not drift: %s" % (len(tests), ", ".join(tests)))
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
