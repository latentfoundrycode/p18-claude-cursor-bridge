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

    --base   commit to diff against (default HEAD - i.e. the pre-delegation checkpoint).

Exit codes:
    0  every changed file is inside the declared Scope
    1  SCOPE DRIFT - one or more changed files are outside Scope (listed on stdout)
    2  cannot verify (brief missing, no Scope section, or git failed) - treat as
       needs-attention; do NOT proceed as if scope were clean.

Scope entries (bullets under "## Scope") may be exact files, directories (trailing "/" or
a bare directory name), or globs (*, ?, [..]). Paths are compared with forward slashes.
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
    return p.strip().replace("\\", "/").lstrip("./")


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
        if in_scope and re.match(r"^##\s+", line):
            break
        if in_scope:
            m = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
            if m:
                entry = m.group(1).strip()
                # Strip a trailing annotation: "path  (new)", "path - comment", "path # note",
                # "path -- note". Only the leading path token is the scope entry.
                entry = re.split(r"\s+(?:\(|#|--|-\s|—)", entry, maxsplit=1)[0]
                entry = entry.strip().strip("`").strip().rstrip(",;")
                if entry and not entry.lower().startswith("do not"):
                    entries.append(_norm(entry))
    if not entries:
        print("CANNOT VERIFY: no Scope entries found under '## Scope' in %s "
              "(spec-packager defect - the brief must fence its scope)." % brief_path)
        sys.exit(2)
    return entries


def changed_files(base):
    files = set()
    # Tracked files modified/added/deleted/renamed relative to the checkpoint.
    for line in _run_git(["diff", "--name-only", base]).splitlines():
        if line.strip():
            files.add(_norm(line))
    # Untracked new files (git diff does not show these) - list individually.
    for line in _run_git(["status", "--porcelain", "-uall"]).splitlines():
        if line.startswith("??"):
            files.add(_norm(line[3:]))
    return sorted(files)


def in_scope(path, entries):
    for e in entries:
        if any(ch in e for ch in "*?["):
            if fnmatch.fnmatch(path, e) or fnmatch.fnmatch(path, e.rstrip("/") + "/*"):
                return True
            continue
        e_dir = e.rstrip("/")
        if path == e or path == e_dir:
            return True
        if path.startswith(e_dir + "/"):
            return True
    return False


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        sys.exit(2)
    brief = argv[1]
    base = "HEAD"
    if "--base" in argv:
        i = argv.index("--base")
        if i + 1 < len(argv):
            base = argv[i + 1]

    entries = parse_scope(brief)
    changed = changed_files(base)

    inside = [p for p in changed if in_scope(p, entries)]
    drift = [p for p in changed if not in_scope(p, entries)]

    print("BRIEF:        %s" % brief)
    print("BASE:         %s" % base)
    print("SCOPE:        %s" % ", ".join(entries))
    print("CHANGED (%d): %s" % (len(changed), ", ".join(changed) if changed else "(none)"))
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
    main(sys.argv)
