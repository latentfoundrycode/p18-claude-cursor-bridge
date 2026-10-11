#!/usr/bin/env python3
"""invisible-check: characters a reader cannot see in the files a diff changed (release A4, 13.1).

  python invisible-check.py [<base-ref>] [--all]

Run from the Workspace root. Reads the text files changed against <base-ref> (default HEAD:
the checkpoint) plus the untracked ones, or every tracked text file with --all, and lists
each line holding a zero-width character (U+200B..U+200D, U+2060, U+FEFF after the first
character), a bidirectional control (U+202A..U+202E, U+2066..U+2069: the "Trojan Source"
reordering), a soft hyphen (U+00AD) or a word joiner. Such a character hides a token from a
reviewer's eye and from a grep, and reorders what a reviewer reads. Exit 0 = none, 1 = at
least one, 2 = cannot verify. ASCII output; the character is named by its code point.
"""
import os
import re
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
INVISIBLE = {0x200B: "zero width space", 0x200C: "zero width non-joiner", 0x200D: "zero width joiner", 0x2060: "word joiner",
             0xFEFF: "zero width no-break space", 0x00AD: "soft hyphen", 0x202A: "left-to-right embedding", 0x202B: "right-to-left embedding",
             0x202C: "pop directional formatting", 0x202D: "left-to-right override", 0x202E: "right-to-left override",
             0x2066: "left-to-right isolate", 0x2067: "right-to-left isolate", 0x2068: "first strong isolate", 0x2069: "pop directional isolate",
             0x061C: "arabic letter mark", 0x180E: "mongolian vowel separator"}
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


def findings(path):
    """[(line, column, code point, name)] in one file; [] for a binary or unreadable file."""
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
            if cp in INVISIBLE and not (cp == 0xFEFF and n == 1 and i == 0):   # a byte-order mark at the start is a file's own
                out.append((n, i + 1, cp, INVISIBLE[cp]))
    return out


def main(argv):
    base = next((a for a in argv if not a.startswith("--")), "HEAD")
    paths = sorted(l.strip() for l in git(["ls-files"]).splitlines() if l.strip()) if "--all" in argv else changed_files(base)
    total = 0
    for p in paths:
        p = p.replace("\\", "/")
        for n, col, cp, name in findings(p):
            print("INVISIBLE: %s:%d:%d U+%04X %s" % (p, n, col, cp, name))
            total += 1
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
