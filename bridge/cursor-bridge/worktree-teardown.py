#!/usr/bin/env python3
"""worktree-teardown: remove a git worktree safely (supervisor rule 19, release A1b).

  python ~/.claude/cursor-bridge/worktree-teardown.py <worktree path> [--dry-run]

`git worktree remove` follows a gitignored junction or symbolic link inside the worktree
(a per-worktree venv, a linked node_modules) and deletes the real target, in an ordinary
removal as in a forced one (Git for Windows 2.53, verified 2026-10-06); one project lost
its main checkout's installed packages that way, and forced the removal fourteen times in
four days. The permission guard refuses the git command; this program is the one way:

  1. every entry inside the folder is looked at without following links, whether git still
     lists it or not (a leftover of a failed removal too); a junction or a symbolic link
     anywhere inside refuses the teardown and is listed with its target, so the link can be
     removed by itself first (rmdir on the link, never through it);
  2. the path must be a worktree of the repository the current folder belongs to: a leftover
     (a folder whose .git file points to a git folder that is gone, or under Worktrees/) is
     named as such, and a folder that holds a registered worktree is refused;
  3. `git worktree remove <path>` without --force; git's own refusal (a dirty or locked
     worktree) is printed and ends the program, because forcing is what destroys data;
  4. `git worktree prune`, and the path must be gone.

Exit 0 = removed; 1 = git refused (commit or clean the worktree, never force); 2 = refused
here (not a worktree, or a link inside). ASCII-only on purpose (cp1252 consoles).
"""
import os
import stat
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def git(*args):
    p = subprocess.run(["git", "-c", "core.fsmonitor=false"] + list(args), capture_output=True, text=True, creationflags=NO_WINDOW)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def is_link(path):
    try:
        st = os.lstat(path)
    except OSError:
        return False
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_reparse_tag", 0))


def link_target(path):
    try:
        return os.readlink(path)
    except OSError:
        return "?"


def worktrees():
    """{normalised path: branch} of the repository's worktrees, the main checkout first."""
    rc, out, _ = git("worktree", "list", "--porcelain")
    if rc != 0:
        return None
    found, path = {}, None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = os.path.normcase(os.path.abspath(line[9:].strip()))
            found[path] = ""
        elif line.startswith("branch ") and path:
            found[path] = line[7:].strip()
    return found


def links_inside(root):
    out = []
    for dirpath, dirs, names in os.walk(root):
        for n in list(dirs) + names:
            p = os.path.join(dirpath, n)
            if is_link(p):
                out.append((p, link_target(p)))
                if n in dirs:
                    dirs.remove(n)              # never walk into a link
    return out


def leftover(path):
    """A folder that was a worktree and that git no longer lists: its .git file points to a git
    folder that is gone, or it lies under a Worktrees folder."""
    dot = os.path.join(path, ".git")
    if os.path.isfile(dot):
        try:
            with open(dot, encoding="utf-8", errors="replace") as f:
                first = f.read().strip()
        except OSError:
            first = ""
        if first.startswith("gitdir:"):
            return not os.path.isdir(first[7:].strip())
    return os.path.basename(os.path.dirname(path)).lower() == "worktrees"


def main(argv):
    dry = "--dry-run" in argv
    args = [a for a in argv if a != "--dry-run"]
    if len(args) != 1:
        print("usage: python worktree-teardown.py <worktree path> [--dry-run]")
        return 2
    path = os.path.abspath(args[0])
    links = links_inside(path) if os.path.isdir(path) else []      # any folder: a leftover too
    if links:
        print("worktree-teardown: refused - %d link(s) inside %s; git would follow them into their targets, forced or not. Remove each link by itself first (rmdir on the link, never through it), then run again:" % (len(links), path))
        for p, t in links[:20]:
            print("  %s -> %s" % (p, t))
        return 2
    known = worktrees()
    if known is None:
        print("worktree-teardown: not inside a git repository")
        return 2
    key = os.path.normcase(path)
    if key not in known:
        inside = [k for k in known if k.startswith(key.rstrip(os.sep) + os.sep)]
        if inside:
            print("worktree-teardown: refused - %s holds a registered worktree (%s); name the worktree itself" % (path, ", ".join(inside)))
        elif os.path.isdir(path) and leftover(path):
            print("worktree-teardown: refused - %s is not a worktree of this repository any more (git worktree list shows: %s); it holds no link, so this leftover may go with a plain recursive delete" % (path, ", ".join(sorted(known)) or "none"))
        else:
            print("worktree-teardown: refused - %s is not a worktree of this repository (git worktree list shows: %s), nor a leftover of one; nothing here to remove" % (path, ", ".join(sorted(known)) or "none"))
        return 2
    main_tree = next(iter(known))                      # git lists the main checkout first
    if key == main_tree:
        print("worktree-teardown: refused - %s is the main checkout, not a worktree" % path)
        return 2
    if dry:
        print("worktree-teardown: %s holds no link; would run git worktree remove (without --force) and git worktree prune (dry run)" % path)
        return 0
    rc, out, err = git("worktree", "remove", path)
    if rc != 0:
        reason = (err or out).strip()
        print("worktree-teardown: git refused to remove %s: %s" % (path, reason))
        if "locked" in reason.lower():
            print("  the worktree is locked: git worktree unlock <path> once nothing needs it any more, then run again; never --force")
        else:
            print("  commit or clean the worktree (git -C <path> status), then run again; never --force")
        return 1
    git("worktree", "prune")
    if os.path.exists(path):
        print("worktree-teardown: git removed the worktree but %s still exists; look at it before doing anything else" % path)
        return 1
    print("worktree-teardown: removed %s (branch %s) and pruned" % (path, known[key] or "detached"))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main(sys.argv[1:]))
