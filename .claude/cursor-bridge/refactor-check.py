#!/usr/bin/env python3
"""refactor-check: deterministic purity check for a REFACTORING diff.

A refactoring increment must keep the same functionality. Three things are
checkable without judgement, and this script checks them against a base ref:

  1. No test file changed.  Tests pin behaviour; a refactoring diff that edits
     one may be changing what "correct" means. (Characterization tests the
     supervisor writes are committed BEFORE the base ref, so they are not in
     the diff.)
  2. docs/CHANGES.md did not change.  That log records behaviour changes; a
     refactoring diff has none to record.
  3. The diff is within the size budget one reviewer can hold well
     (default 400 changed lines = insertions + deletions).

Usage:  python refactor-check.py <base-ref> [--max-lines N] [--allow-test <path> ...]
        --allow-test lists test files the brief explicitly allowed (a mechanical
        rename or an import path), each of which the reviewer must then read.

Prints PURE or IMPURE with the reasons. Exit 0 = pure, 1 = impure, 2 = cannot
verify (not a git repo, bad ref). ASCII-only on purpose (cp1252 consoles).
"""
import fnmatch
import re
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

TEST_PATTERNS = [
    "test_*.py", "*_test.py", "*.test.*", "*.spec.*", "conftest.py",
    "tests/*", "test/*", "__tests__/*", "e2e/*", "spec/*",
    "*/tests/*", "*/test/*", "*/__tests__/*", "*/e2e/*", "*/spec/*",
]


def git(args):
    try:
        out = subprocess.run(["git"] + args, capture_output=True, text=True, check=True,
                             creationflags=NO_WINDOW)
        return out.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        sys.stderr.write("refactor-check: git failed: %s\n" % e)
        return None


def is_test(path):
    p = path.replace("\\", "/")
    name = p.rsplit("/", 1)[-1]
    for pat in TEST_PATTERNS:
        if fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(name, pat):
            return True
    return False


def main():
    argv = sys.argv[1:]
    if not argv:
        print("usage: refactor-check.py <base-ref> [--max-lines N] [--allow-test <path> ...]")
        return 2
    base = argv[0]
    max_lines = 400
    allowed = set()
    i = 1
    while i < len(argv):
        if argv[i] == "--max-lines" and i + 1 < len(argv):
            max_lines = int(argv[i + 1]); i += 2
        elif argv[i] == "--allow-test" and i + 1 < len(argv):
            allowed.add(argv[i + 1].replace("\\", "/")); i += 2
        else:
            i += 1

    names = git(["diff", "--name-only", base])
    stat = git(["diff", "--shortstat", base])
    if names is None or stat is None:
        print("CANNOT VERIFY: git diff against %r failed" % base)
        return 2
    untracked = git(["status", "--porcelain", "-uall"]) or ""
    files = [l.strip() for l in names.splitlines() if l.strip()]
    files += [l[3:].strip() for l in untracked.splitlines() if l.startswith("??")]

    reasons = []
    tests = [f for f in files if is_test(f) and f.replace("\\", "/") not in allowed]
    if tests:
        reasons.append("test file(s) changed: " + ", ".join(tests))
    if any(f.replace("\\", "/") == "docs/CHANGES.md" for f in files):
        reasons.append("docs/CHANGES.md changed (a refactoring has no behaviour change to log)")
    ins = re.search(r"(\d+) insertion", stat)
    dels = re.search(r"(\d+) deletion", stat)
    changed = (int(ins.group(1)) if ins else 0) + (int(dels.group(1)) if dels else 0)
    if changed > max_lines:
        reasons.append("diff size %d changed lines exceeds budget %d" % (changed, max_lines))

    print("base: %s | files: %d | changed lines: %d (budget %d) | allowed test files: %d"
          % (base, len(files), changed, max_lines, len(allowed)))
    for a in sorted(allowed):
        print("  reviewer must read allowed test file: %s" % a)
    if reasons:
        print("IMPURE:")
        for r in reasons:
            print("  - " + r)
        return 1
    print("PURE: no test change, no CHANGES.md entry, within size budget.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
