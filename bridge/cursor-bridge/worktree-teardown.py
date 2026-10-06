#!/usr/bin/env python3
"""worktree-teardown: remove a git worktree safely (supervisor rule 19, release A1b).

  python ~/.claude/cursor-bridge/worktree-teardown.py <worktree path> [--dry-run]

`git worktree remove --force` follows a live junction or symbolic link inside the worktree
(a per-worktree venv, a linked node_modules) and deletes the real target; one project lost
its main checkout's installed packages that way, and forced the removal fourteen times in
four days. This program never forces:

  1. the path must be a worktree of the repository the current folder belongs to;
  2. every entry inside it is looked at without following links; a junction or a symbolic
     link anywhere inside refuses the teardown and is listed with its target, so the link
     can be removed by itself first (rmdir on the link, never through it);
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
    """{normalised path: branch} of the repository's worktrees."""
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


def main(argv):
    dry = "--dry-run" in argv
    args = [a for a in argv if a != "--dry-run"]
    if len(args) != 1:
        print("usage: python worktree-teardown.py <worktree path> [--dry-run]")
        return 2
    path = os.path.abspath(args[0])
    known = worktrees()
    if known is None:
        print("worktree-teardown: not inside a git repository")
        return 2
    key = os.path.normcase(path)
    if key not in known:
        print("worktree-teardown: refused - %s is not a worktree of this repository (git worktree list shows: %s)" % (path, ", ".join(sorted(known)) or "none"))
        return 2
    main_tree = sorted(known)[0]
    if key == os.path.normcase(os.path.abspath(git("rev-parse", "--show-toplevel")[1].strip() or main_tree)):
        print("worktree-teardown: refused - %s is the main checkout, not a worktree" % path)
        return 2
    links = links_inside(path)
    if links:
        print("worktree-teardown: refused - %d link(s) inside %s; a forced removal would follow them into their targets. Remove each link by itself first (rmdir on the link, never through it), then run again:" % (len(links), path))
        for p, t in links[:20]:
            print("  %s -> %s" % (p, t))
        return 2
    if dry:
        print("worktree-teardown: %s holds no link; would run git worktree remove (without --force) and git worktree prune (dry run)" % path)
        return 0
    rc, out, err = git("worktree", "remove", path)
    if rc != 0:
        print("worktree-teardown: git refused to remove %s: %s" % (path, (err or out).strip()))
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
