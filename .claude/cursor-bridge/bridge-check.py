#!/usr/bin/env python3
"""bridge-check: verify that the installed bridge tree matches its manifest.

The maintainer ships MANIFEST.json (file -> sha256, plus the version) with every
bridge release. This script hashes the live tree it is installed in and reports,
per file: OK, STALE (content differs), MISSING (not installed), and any EXTRA
governance files not in the manifest (informational). Line endings are normalized
before hashing, so a CRLF copy of an LF file is still OK.

Usage:  python ~/.claude/cursor-bridge/bridge-check.py [--root <path-to-.claude>] [--quiet]
Exit:   0 = every manifest file OK; 1 = at least one STALE or MISSING;
        2 = manifest unreadable.  ASCII-only on purpose (cp1252 consoles).
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def norm_hash(path):
    with open(path, "rb") as f:
        data = f.read()
    data = data.replace(b"\r\n", b"\n")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return hashlib.sha256(data).hexdigest()


def main():
    argv = sys.argv[1:]
    root = os.path.abspath(os.path.join(HERE, os.pardir))
    quiet = "--quiet" in argv
    if "--root" in argv:
        root = os.path.abspath(argv[argv.index("--root") + 1])
    manifest_path = os.path.join(HERE, "MANIFEST.json")
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print("bridge-check: cannot read %s (%s)" % (manifest_path, e))
        return 2

    files = manifest.get("files", {})
    ok = stale = missing = 0
    problems = []
    for rel, expected in sorted(files.items()):
        p = os.path.join(root, *rel.split("/"))
        if not os.path.isfile(p):
            missing += 1
            problems.append(("MISSING", rel))
            continue
        if norm_hash(p) != expected:
            stale += 1
            problems.append(("STALE", rel))
        else:
            ok += 1

    extras = []
    for sub in ("commands", "agents", "skills", "cursor-bridge"):
        base = os.path.join(root, sub)
        for dirpath, dirs, names in os.walk(base):
            for n in names:
                rel = os.path.relpath(os.path.join(dirpath, n), root).replace("\\", "/")
                if rel not in files and not rel.endswith("MANIFEST.json") and "__pycache__" not in rel:
                    extras.append(rel)

    print("bridge-check: version %s (%s) at %s" % (
        manifest.get("version", "?"), manifest.get("generated", "?"), root))
    for kind, rel in problems:
        print("  %-8s %s" % (kind, rel))
    if extras and not quiet:
        for rel in sorted(extras):
            print("  EXTRA    %s  (not in manifest; a local addition or a leftover)" % rel)
    print("bridge-check: %d OK, %d STALE, %d MISSING, %d EXTRA" % (ok, stale, missing, len(extras)))
    if stale or missing:
        print("RESULT: NOT CALIBRATED - re-copy the STALE/MISSING files from the bridge release, then re-run.")
        return 1
    print("RESULT: INSTALLED TREE MATCHES bridge %s" % manifest.get("version", "?"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
