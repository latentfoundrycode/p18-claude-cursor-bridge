#!/usr/bin/env python3
"""invisible-check: characters a reader cannot see in the files a diff changed (release A4, 13.1).

  python invisible-check.py [<base-ref>] [--all] [--non-ascii]

Run from the Workspace root. Reads the text files changed against <base-ref> (default HEAD:
the checkpoint) plus the untracked ones, or every tracked text file with --all, and lists
each line holding a character whose Unicode category is Cc, Cf, Zl or Zp, or Zs other than
U+0020, except U+0009, U+000A and U+000D anywhere and U+FEFF as the file's first character
(a character with no Unicode name is named by its code point alone). Such a character hides a token from a
reviewer's eye and from a grep, and reorders what a reviewer reads. Exit 0 = none, 1 = at
least one, 2 = cannot verify. ASCII output; the character is named by its code point.

  --non-ascii  also lists EVERY non-ASCII character of those files, one line each (path,
               line, column, U+XXXX and its Unicode name), so the author confirms each was
               meant: a backslash-u escape typed through a tool arrives as the character
               itself (KP-052, FB-029). The listing does not change the exit code.
"""
import os
import re
import subprocess
import sys
import unicodedata

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".7z", ".exe", ".dll", ".so", ".dylib",
              ".woff", ".woff2", ".ttf", ".otf", ".mp3", ".mp4", ".wav", ".mov", ".bin", ".pyc", ".lockb", ".sqlite", ".db"}


def git(args):
    try:
        return subprocess.run(["git"] + args, capture_output=True, text=True, check=True, encoding="utf-8",
                              errors="replace", creationflags=NO_WINDOW).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("CANNOT VERIFY: git %s failed (%s)" % (" ".join(args), e))
        sys.exit(2)


def changed_files(base):
    files = set(l.strip() for l in git(["diff", "--name-only", "--no-renames", base]).splitlines() if l.strip())
    for l in git(["status", "--porcelain", "-uall"]).splitlines():
        if l.startswith("??"):
            files.add(l[3:].strip())
    return sorted(files)


def findings(path, non_ascii=False):
    """[(line, column, code point, name)] in one file; [] for a binary or unreadable file. With
    non_ascii, every character above U+007F instead, named by its Unicode name."""
    if os.path.splitext(path)[1].lower() in BINARY_EXT or not os.path.isfile(path):
        return []
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        return []
    if b"\0" in raw[:8000]:
        return []
    text = raw.decode("utf-8", errors="replace")
    out = []
    for n, line in enumerate(text.split("\n"), 1):
        for i, ch in enumerate(line):
            cp = ord(ch)
            if non_ascii:
                if cp > 0x7F:
                    out.append((n, i + 1, cp, unicodedata.name(ch, "(no name)")))
            else:
                cat = unicodedata.category(ch)
                if (cat == "Cc" or cat == "Cf" or cat == "Zl" or cat == "Zp" or (cat == "Zs" and cp != 0x0020)) and not (
                        cp == 0x0009 or cp == 0x000A or cp == 0x000D or (cp == 0xFEFF and n == 1 and i == 0)):  # a byte-order mark at the start is a file's own
                    out.append((n, i + 1, cp, unicodedata.name(ch, "").lower()))
    return out


def main(argv):
    base = next((a for a in argv if not a.startswith("--")), "HEAD")
    paths = sorted(l.strip() for l in git(["ls-files"]).splitlines() if l.strip()) if "--all" in argv else changed_files(base)
    total = 0
    for p in paths:
        p = p.replace("\\", "/")
        for n, col, cp, name in findings(p):
            print("INVISIBLE: %s:%d:%d U+%04X%s" % (p, n, col, cp, " " + name if name else ""))
            total += 1
    if "--non-ascii" in argv:
        listed = 0
        for p in paths:
            p = p.replace("\\", "/")
            for n, col, cp, name in findings(p, non_ascii=True):
                print("NON-ASCII: %s:%d:%d U+%04X %s" % (p, n, col, cp, name))
                listed += 1
        print("NON-ASCII: %d character(s) above U+007F in %d file(s) - confirm each was meant (a typed backslash-u escape arrives as the character, KP-052)" % (listed, len(paths)))
    if total:
        print("RESULT: %d invisible character(s) in the %s - a reviewer cannot see them; remove each or show why it belongs (a right-to-left word in a user-facing string)" % (total, "tree" if "--all" in argv else "changed files"))
        return 1
    print("RESULT: OK - no invisible character in %d file(s)" % len(paths))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main(sys.argv[1:]))
