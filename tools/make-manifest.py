#!/usr/bin/env python3
"""make-manifest: maintainer-side release stamp for the bridge tree.

Run from the staging repo root before every commit that changes .claude/:

    python tools/make-manifest.py [--version YYYY.MM.DD[x]]

It (1) takes the version from the newest "## <version>" entry in
.claude/cursor-bridge/CHANGELOG.md (so a release starts by writing its note;
--version overrides), (2) refuses a version with no entry, (3) writes .claude/cursor-bridge/VERSION, and (4) writes
.claude/cursor-bridge/MANIFEST.json with a normalized sha256 of every file under
.claude/ except the manifest itself and settings.json (compared by entries, see bridge-check.py). bridge-check.py on an installed machine then
proves whether the copy landed. ASCII-only on purpose.
"""
import datetime
import hashlib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TREE = os.path.join(ROOT, ".claude")
CB = os.path.join(TREE, "cursor-bridge")
CHANGELOG = os.path.join(CB, "CHANGELOG.md")


def norm_hash(path):
    with open(path, "rb") as f:
        data = f.read()
    data = data.replace(b"\r\n", b"\n")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return hashlib.sha256(data).hexdigest()


def changelog_versions():
    if not os.path.isfile(CHANGELOG):
        return []
    with open(CHANGELOG, encoding="utf-8") as f:
        return re.findall(r"^## (\d{4}\.\d{2}\.\d{2}[a-z]?)\b", f.read(), re.M)


def pick_version(explicit):
    """The version to stamp is the newest CHANGELOG entry (its first '## ' heading),
    unless given explicitly. A new release therefore starts by writing its entry."""
    if explicit:
        return explicit
    versions = changelog_versions()
    if not versions:
        raise SystemExit("make-manifest: CHANGELOG.md has no '## <version>' entry yet")
    return versions[0]


def read_version():
    p = os.path.join(CB, "VERSION")
    if os.path.isfile(p):
        return open(p, encoding="utf-8").read().strip().split()[0]
    return ""


def main():
    argv = sys.argv[1:]
    explicit = argv[argv.index("--version") + 1] if "--version" in argv else ""
    version = pick_version(explicit)
    if version not in changelog_versions():
        print("make-manifest: CHANGELOG.md has no '## %s' entry - write the release note first." % version)
        return 1
    # settings.json is shared with the owner and Claude Code (KP-030): the bridge's part of it
    # lives in cursor-bridge/settings.bridge.json, which is the source; the tree's own
    # settings.json is regenerated from it here (for sessions run inside this Workspace) and
    # is not fingerprinted, because an installed copy legitimately holds the owner's keys too.
    src = os.path.join(CB, "settings.bridge.json")
    with open(src, encoding="utf-8-sig") as f:
        bridge_settings = json.load(f)
    bridge_settings.pop("_comment", None)
    with open(os.path.join(TREE, "settings.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(bridge_settings, f, indent=2)
        f.write("\n")
    files = {}
    for dirpath, dirs, names in os.walk(TREE):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for n in names:
            if n == "MANIFEST.json" or n.endswith(".pyc"):
                continue
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, TREE).replace("\\", "/")
            if rel in ("cursor-bridge/VERSION", "settings.json"):
                continue  # VERSION is written below and hashed after; settings.json is compared by entries
            files[rel] = norm_hash(p)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(os.path.join(CB, "VERSION"), "w", encoding="utf-8", newline="\n") as f:
        f.write("%s\n" % version)
    files["cursor-bridge/VERSION"] = norm_hash(os.path.join(CB, "VERSION"))
    manifest = {"version": version, "generated": stamp, "files": dict(sorted(files.items()))}
    with open(os.path.join(CB, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print("make-manifest: version %s, %d files hashed, VERSION + MANIFEST.json written" % (version, len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
