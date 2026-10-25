#!/usr/bin/env python3
"""stage-diff: write a stage's whole change and its parts from the stage's own squash commits.

  python ~/.claude/cursor-bridge/stage-diff.py <commit> [<commit> ...] --out run/review/
                                               [--name <stage>] [--ref origin/main]
  python ~/.claude/cursor-bridge/stage-diff.py --from-file <path> --out run/review/ [--name <stage>]

Run from the Workspace root, at the stage close's step 2 (2026-10-25 C7; the bridge's FB-005,
FB-017). A stage's change is `git diff <its first checkpoint> origin/main` only while no other
stage's increment merged in between. When stages interleave on main (an earlier stage closing
after a later stage's ready increments merged), the stage's change is the union of its own
squash commits, and each review round's diff was written by a script nobody reviewed and a
restart lost. This program is that writer:

  1. the commits are given as arguments or with --from-file (one sha per line; a blank line
     and a line starting with # are skipped; any text after the sha is ignored). Each must be
     on <ref>'s first-parent line (default origin/main): a squash commit as merged; they are
     put in that line's order, whatever order they were given in;
  2. the whole change runs from the first commit's parent to the last commit, with every path
     an OTHER commit between them changed (one not in the list: a later stage's increment, a
     hotfix) left at its state before that commit, so the whole change holds the stage's own
     commits only. It is built in a temporary index (GIT_INDEX_FILE) from git's own trees,
     so the checkout, the real index and every ref stay as they are (git keeps the written
     tree as an unreferenced object, which its housekeeping removes);
  3. a path the stage changed AGAIN after another commit changed it cannot be separated by
     paths: it is kept as of the stage's last commit, the other commit's change inside it, and
     named as OVERLAP (exit 1): read that path in the parts, which are exact;
  4. it writes, into --out (made if missing), the whole change as STAGE-<name>.diff and one
     diff per commit as STAGE-<name>-<nn>-<sha7>.diff (nn in the stage's order); parts of a
     former run of the same name are removed first, so a folder never holds a stale part.
     Without --name the files are STAGE.diff and STAGE-<nn>-<sha7>.diff. Every diff is git's
     own unified output, written as git printed it (no log lines inside, FB-017);
  5. it prints a short index: per part its number, commit, subject, files and lines (+added
     -removed), the whole change alike, and the other commits left out with how many of their
     paths were set back.

Git only, through subprocess (no third-party library). Exit 0 = written; 1 = written, but a
path is named OVERLAP or the whole change is empty (look before the review); 2 = refused
before anything was written (not a git repository, a commit that is no commit or is not on
<ref>'s first-parent line, an unreadable --from-file, no commit given), or git or a write
failed on the way (the same command can be run again). ASCII-only on purpose (cp1252 consoles).
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"           # git's empty tree: the parent of a root commit
DIFF = ("diff", "--no-color", "--no-ext-diff", "--no-textconv")
NAME_RX = re.compile(r"^[A-Za-z0-9._-]+$")


class GitFailed(Exception):
    pass


def git(*args, env=None, data=None, binary=False):
    """git's output (bytes when binary, else text); GitFailed with its stderr when it fails."""
    try:
        p = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", "core.quotepath=false"] + list(args), input=data,
                           capture_output=True, env=env, creationflags=NO_WINDOW)
    except OSError as e:
        raise GitFailed("git could not be started (%s)" % e)
    if p.returncode != 0:
        raise GitFailed("git %s: %s" % (" ".join(args[:3]), p.stderr.decode("utf-8", "replace").strip()[:300]))
    return p.stdout if binary else p.stdout.decode("utf-8", "replace")


def resolve(sha):
    try:
        return git("rev-parse", "--verify", "--quiet", sha + "^{commit}").strip()
    except GitFailed:
        return None


def parent(sha):
    try:
        return git("rev-parse", "--verify", "--quiet", sha + "^1").strip()
    except GitFailed:
        return EMPTY_TREE


def paths_changed(old, new):
    """The paths that differ between two commits or trees, renames read as a removal and an addition."""
    out = git("diff-tree", "-r", "-z", "--no-renames", "--name-only", old, new)
    return [p for p in out.split("\0") if p]


def numstat(old, new):
    files, added, removed = 0, 0, 0
    for line in git("diff", "--numstat", "--no-renames", old, new).splitlines():
        cells = line.split("\t")
        if len(cells) >= 3:
            files += 1
            added += int(cells[0]) if cells[0].isdigit() else 0
            removed += int(cells[1]) if cells[1].isdigit() else 0
    return files, added, removed


def tree_entries(rev):
    """{path: index-info line} of every file in `rev`'s tree."""
    entries = {}
    for rec in git("ls-tree", "-r", "-z", "--full-tree", rev).split("\0"):
        if "\t" in rec:
            path = rec.split("\t", 1)[1]
            entries[path] = rec
    return entries


def subject(sha):
    return git("show", "-s", "--format=%s", sha).strip()


def ascii_line(text, width=70):
    return text.encode("ascii", "replace").decode("ascii")[:width]


def read_list(path):
    with open(path, encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    return [l.split()[0] for l in lines if l.strip() and not l.lstrip().startswith("#")]


def whole_tree(last, setback):
    """The tree of `last` with each path of `setback` ({path: rev}) as it stands in rev (gone when rev lacks it)."""
    work = tempfile.mkdtemp(prefix="stage-diff-")
    try:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(work, "index"))
        git("read-tree", last, env=env)
        lines, cache = [], {}
        for path, rev in sorted(setback.items()):
            if rev not in cache:
                cache[rev] = tree_entries(rev)
            lines.append(cache[rev].get(path) or ("0 %s\t%s" % ("0" * 40, path)))   # mode 0: the path leaves the index
        if lines:
            git("update-index", "-z", "--index-info", env=env, data=("\0".join(lines) + "\0").encode("utf-8"))
        return git("write-tree", env=env).strip()
    finally:
        shutil.rmtree(work, ignore_errors=True)


def build_parser():
    ap = argparse.ArgumentParser(description="Write a stage's whole change and its parts from its squash commits.")
    ap.add_argument("commits", nargs="*")
    ap.add_argument("--from-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--ref", default="origin/main")
    return ap


def main():
    a = build_parser().parse_args()
    if a.name and not NAME_RX.match(a.name):
        print("stage-diff: --name %r holds a character a file name should not; use letters, digits, '.', '_' or '-'. Nothing was written." % a.name)
        return 2
    given = list(a.commits)
    if a.from_file:
        try:
            given += read_list(a.from_file)
        except OSError as e:
            print("stage-diff: %s cannot be read (%s); nothing was written." % (a.from_file, e))
            return 2
    if not given:
        print("stage-diff: no commit given (as arguments or with --from-file); nothing was written.")
        return 2
    try:
        git("rev-parse", "--is-inside-work-tree")
    except GitFailed:
        print("stage-diff: not inside a git repository; nothing was written.")
        return 2
    ref = resolve(a.ref)
    if ref is None:
        print("stage-diff: --ref %s names no commit (fetched?); nothing was written." % a.ref)
        return 2
    try:
        line = git("rev-list", "--first-parent", "--reverse", ref).split()
        place = {sha: i for i, sha in enumerate(line)}
        stage = []
        for g in given:
            full = resolve(g)
            if full is None:
                print("stage-diff: %s names no commit; nothing was written." % g)
                return 2
            if full not in place:
                print("stage-diff: %s is not on %s's first-parent line (not a squash commit as merged); nothing was written." % (g, a.ref))
                return 2
            if full not in stage:
                stage.append(full)
        stage.sort(key=place.get)
        first, last = stage[0], stage[-1]
        base = parent(first)
        others = [sha for sha in line[place[first]:place[last] + 1] if sha not in stage]
        touched = {sha: set(paths_changed(parent(sha), sha)) for sha in stage}
        setback, overlap, left_out = {}, {}, []
        for other in others:
            mine = 0
            for path in paths_changed(parent(other), other):
                if path in setback or path in overlap:
                    continue                                   # an earlier other commit decided this path
                later = [s for s in stage if place[s] > place[other] and path in touched[s]]
                if later:
                    overlap[path] = (other, later[0])
                else:
                    setback[path] = parent(other)              # as it stood before that commit
                    mine += 1
            left_out.append((other, mine))
        whole = whole_tree(last, setback)
        prefix = "STAGE-%s" % a.name if a.name else "STAGE"
        os.makedirs(a.out, exist_ok=True)
        stale = [p for p in glob.glob(os.path.join(glob.escape(a.out), prefix + "-*.diff"))
                 if re.match(re.escape(prefix) + r"-\d{2,}-[0-9a-f]{7}\.diff$", os.path.basename(p))]
        for p in stale:
            os.remove(p)
        whole_path = os.path.join(a.out, prefix + ".diff")
        text = git(*(DIFF + (base, whole)), binary=True)
        with open(whole_path, "wb") as f:
            f.write(text)
        rows = []
        for n, sha in enumerate(stage, 1):
            part = os.path.join(a.out, "%s-%02d-%s.diff" % (prefix, n, sha[:7]))
            with open(part, "wb") as f:
                f.write(git(*(DIFF + (parent(sha), sha)), binary=True))
            rows.append((n, sha, subject(sha), numstat(parent(sha), sha), part))
        total = numstat(base, whole)
        print("stage-diff: %d commit(s) of the stage, %s..%s on %s" % (len(stage), base[:7], last[:7], a.ref))
        for n, sha, subj, (files, plus, minus), part in rows:
            print("  %02d  %s  %-70s %3d file(s) +%d -%d" % (n, sha[:7], ascii_line(subj), files, plus, minus))
        print("  whole change  %s  %d file(s) +%d -%d" % (whole_path.replace("\\", "/"), total[0], total[1], total[2]))
        for other, count in left_out:
            print("  left out  %s  %-60s %d path(s) set back to before it" % (other[:7], ascii_line(subject(other), 60), count))
        if stale:
            print("  removed %d part(s) of a former run of %s" % (len(stale), prefix))
        for path, (other, again) in sorted(overlap.items()):
            print("OVERLAP  %s: changed by %s and after it by the stage's %s; the whole change holds it as of %s, %s's change inside it. Read it in the parts." % (
                ascii_line(path, 200), other[:7], again[:7], last[:7], other[:7]))
        if not text:
            print("EMPTY    the whole change holds nothing; a review of it reads nothing")
        return 1 if overlap or not text else 0
    except GitFailed as e:
        print("stage-diff: %s; nothing more was written." % e)
        return 2
    except OSError as e:
        print("stage-diff: %s; nothing more was written (the same command can be run again)." % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
