#!/usr/bin/env python3
"""review-guard: the committed checkpoint a reviewer with execution runs on, snapshotted
before the launch, verified and restored after it, and checked once more before the merge.

  python ~/.claude/cursor-bridge/review-guard.py snapshot <nnn>     before launching Review B
  python ~/.claude/cursor-bridge/review-guard.py verify   <nnn>     after it returns
  python ~/.claude/cursor-bridge/review-guard.py premerge <nnn>     before `gh pr merge`

Why (release 0b review, finding 2): Review B keeps `--force` so it can run the tests and
build reproductions (the owner's decision), and it acts after Review A and right before the
merge, so what it leaves behind has no gate after it. `git status --porcelain` followed by
`git checkout -- .` and `git clean -fd` restores tracked and untracked files only: it does
not see a moved HEAD, a commit, a new ref or stash, a changed `.git/config` (where a
`core.fsmonitor` or `core.hooksPath` line makes the supervisor's next git command run the
reviewer's program with the owner's identity), or changed ignored files (`.env`, parked work).

What each step does:
  snapshot  refuses a dirty tree (commit first); records HEAD, the branch, every ref, the
            stash list, a hash of `.git/config` and of every file under the hooks folder,
            and the ignored entries with size and mtime; writes <git common dir>/bridge/review-<nnn>.json.
  verify    reads `.git/config` and the hooks folder FIRST, without running git: a change is
            GATE-INTEGRITY and nothing else runs. Then compares HEAD, the branch, refs and
            stashes (a difference is GATE-INTEGRITY, and HEAD is put back), restores the
            tree (`git reset --hard <sha>`, `git clean -fd`) listing what it removed, and
            lists ignored entries that changed (LEFT BEHIND; `.env*` changed is GATE-INTEGRITY).
  premerge  the head about to merge must descend from the reviewed head and differ from it
            only under run/review/ (the review files removed with `git rm`).

Exit 0 = OK; 1 = GATE-INTEGRITY (open the flag, condition 4, and an issue; do not merge);
2 = cannot verify (no snapshot, dirty tree at snapshot, git failure). Never prints a value
of anything. ASCII-only.

What it does not cover, said plainly (KP-032): the contents of ignored folders (a venv, a
cache), anything outside the checkout (the owner's profile, the installed bridge, other
projects), and a reviewer that deliberately reaches for the credential store. It is a guard
against what a reviewer does in passing, not a sandbox.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

GIT_TIMEOUT = 120
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def run_git(args, cwd):
    p = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=GIT_TIMEOUT, creationflags=NO_WINDOW)
    if p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), p.stderr.strip()[:300]))
    return p.stdout


def find_git_dirs(start):
    """(worktree root, git dir, common dir) found by walking up from `start`, without running
    git: `.git` may be a folder or a worktree's `gitdir: <path>` file."""
    d = os.path.abspath(start)
    while True:
        dot = os.path.join(d, ".git")
        if os.path.isdir(dot):
            git_dir = dot
            break
        if os.path.isfile(dot):
            with open(dot, encoding="utf-8", errors="replace") as f:
                first = f.read().strip()
            if first.startswith("gitdir:"):
                git_dir = os.path.normpath(os.path.join(d, first[len("gitdir:"):].strip()))
                break
        parent = os.path.dirname(d)
        if parent == d:
            return None, None, None
        d = parent
    common = git_dir
    cd = os.path.join(git_dir, "commondir")
    if os.path.isfile(cd):
        with open(cd, encoding="utf-8", errors="replace") as f:
            common = os.path.normpath(os.path.join(git_dir, f.read().strip()))
    return d, git_dir, common


def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def config_state(common):
    hooks_dir = os.path.join(common, "hooks")
    hooks = {}
    if os.path.isdir(hooks_dir):
        for name in sorted(os.listdir(hooks_dir)):
            p = os.path.join(hooks_dir, name)
            if os.path.isfile(p):
                hooks[name] = sha256_file(p)
    return {"config": sha256_file(os.path.join(common, "config")), "hooks": hooks}


def ignored_entries(root):
    out = {}
    text = run_git(["status", "--porcelain", "--ignored", "-unormal"], root)
    for line in text.splitlines():
        if not line.startswith("!! "):
            continue
        rel = line[3:].strip()
        full = os.path.join(root, rel.rstrip("/"))
        if os.path.isdir(full):
            out[rel] = "dir"
        else:
            try:
                st = os.stat(full)
                out[rel] = "%d:%d" % (st.st_size, int(st.st_mtime))
            except OSError:
                out[rel] = "?"
    return out


def refs(root):
    return dict(line.split(" ", 1)[::-1] for line in run_git(["for-each-ref", "--format=%(objectname) %(refname)"], root).splitlines() if " " in line)


def stashes(root):
    return [l.strip() for l in run_git(["stash", "list"], root).splitlines() if l.strip()]


def snapshot_path(common, nnn):
    return os.path.join(common, "bridge", "review-%s.json" % nnn)


def cmd_snapshot(nnn, cwd):
    root, git_dir, common = find_git_dirs(cwd)
    if not root:
        print("review-guard: not inside a git checkout")
        return 2
    if run_git(["status", "--porcelain"], root).strip():
        print("review-guard: CANNOT SNAPSHOT - the tree is not clean; commit everything of yours first (rule 2)")
        return 2
    head = run_git(["rev-parse", "HEAD"], root).strip()
    try:
        branch = run_git(["symbolic-ref", "-q", "HEAD"], root).strip()
    except RuntimeError:
        branch = ""                               # detached
    snap = {
        "nnn": str(nnn), "taken": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": root, "head": head, "branch": branch,
        "refs": refs(root), "stashes": stashes(root),
        "git": config_state(common), "ignored": ignored_entries(root),
    }
    os.makedirs(os.path.join(common, "bridge"), exist_ok=True)
    with open(snapshot_path(common, nnn), "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=1, sort_keys=True)
    print("review-guard: snapshot %s taken at %s on %s (%d refs, %d stashes, %d ignored entries)" % (
        head[:12], snap["taken"], branch or "detached HEAD", len(snap["refs"]), len(snap["stashes"]), len(snap["ignored"])))
    return 0


def load_snapshot(nnn, cwd):
    root, git_dir, common = find_git_dirs(cwd)
    if not root:
        print("review-guard: not inside a git checkout")
        return None, None, None
    p = snapshot_path(common, nnn)
    if not os.path.isfile(p):
        print("review-guard: CANNOT VERIFY - no snapshot %s (run `review-guard.py snapshot %s` before the launch)" % (p, nnn))
        return None, None, None
    with open(p, encoding="utf-8") as f:
        return json.load(f), root, common


def cmd_verify(nnn, cwd):
    snap, root, common = load_snapshot(nnn, cwd)
    if snap is None:
        return 2
    flags, notes = [], []
    # 1. the repository's configuration, read as files, before any git command runs
    now = config_state(common)
    if now["config"] != snap["git"]["config"]:
        flags.append(".git/config changed during the review - do not run git until you have read it (a core.fsmonitor or core.hooksPath line runs a program with your identity)")
    if now["hooks"] != snap["git"]["hooks"]:
        changed = sorted(set(now["hooks"]) ^ set(snap["git"]["hooks"]) | {k for k in now["hooks"] if snap["git"]["hooks"].get(k) != now["hooks"][k]})
        flags.append("hook files changed during the review: %s" % ", ".join(changed))
    if flags:
        for f in flags:
            print("  GATE-INTEGRITY  " + f)
        print("review-guard: GATE-INTEGRITY - the checkout was NOT restored; inspect %s/config and %s/hooks first" % (common, common))
        return 1
    # 2. where HEAD is
    head = run_git(["rev-parse", "HEAD"], root).strip()
    try:
        branch = run_git(["symbolic-ref", "-q", "HEAD"], root).strip()
    except RuntimeError:
        branch = ""
    if branch != snap["branch"]:
        flags.append("the branch changed during the review: %s -> %s" % (snap["branch"] or "detached", branch or "detached"))
    if head != snap["head"]:
        flags.append("HEAD moved during the review: %s -> %s (a checkout or a commit)" % (snap["head"][:12], head[:12]))
    now_refs = refs(root)
    for name, sha in sorted(now_refs.items()):
        if name not in snap["refs"]:
            flags.append("new ref during the review: %s" % name)
        elif snap["refs"][name] != sha:
            flags.append("ref moved during the review: %s" % name)
    for name in sorted(set(snap["refs"]) - set(now_refs)):
        flags.append("ref deleted during the review: %s" % name)
    now_stashes = stashes(root)
    if len(now_stashes) != len(snap["stashes"]):
        flags.append("the stash list changed during the review (%d -> %d entries)" % (len(snap["stashes"]), len(now_stashes)))
    # 3. restore the tree to the snapshot
    dirty = [l for l in run_git(["status", "--porcelain"], root).splitlines() if l.strip()]
    if snap["branch"]:
        # back on the recorded branch BEFORE the reset: a reset while another branch is
        # checked out would move that branch's tip (local main, for instance)
        if branch != snap["branch"]:
            run_git(["checkout", "-q", "-f", snap["branch"][len("refs/heads/"):] if snap["branch"].startswith("refs/heads/") else snap["branch"]], root)
        run_git(["reset", "-q", "--hard", snap["head"]], root)
    else:
        run_git(["checkout", "-q", "-f", "--detach", snap["head"]], root)
    cleaned = [l.strip() for l in run_git(["clean", "-fd"], root).splitlines() if l.strip()]
    for l in dirty:
        notes.append("restored: " + l.strip())
    for l in cleaned:
        notes.append(l)
    # 4. ignored entries
    now_ign = ignored_entries(root)
    for rel in sorted(set(now_ign) | set(snap["ignored"])):
        before, after = snap["ignored"].get(rel), now_ign.get(rel)
        if before == after:
            continue
        what = "new" if before is None else ("removed" if after is None else "changed")
        base = os.path.basename(rel.rstrip("/"))
        if base == ".env" or base.startswith(".env."):
            flags.append("%s %s during the review - inspect it before anything runs" % (rel, what))
        else:
            notes.append("LEFT BEHIND (ignored, %s): %s" % (what, rel))
    for n in notes:
        print("  " + n)
    for f in flags:
        print("  GATE-INTEGRITY  " + f)
    if flags:
        print("review-guard: GATE-INTEGRITY - the tree is back at %s on %s, but the review left the marks above: open the flag (condition 4) and an issue; do not merge" % (snap["head"][:12], snap["branch"] or "detached HEAD"))
        return 1
    print("review-guard: OK - checkout restored to %s on %s (%d item(s) restored or removed, %d ignored entr%s left behind)" % (
        snap["head"][:12], snap["branch"] or "detached HEAD", len(dirty) + len(cleaned),
        sum(1 for n in notes if n.startswith("LEFT BEHIND")), "y" if sum(1 for n in notes if n.startswith("LEFT BEHIND")) == 1 else "ies"))
    return 0


def cmd_premerge(nnn, cwd):
    snap, root, common = load_snapshot(nnn, cwd)
    if snap is None:
        return 2
    head = run_git(["rev-parse", "HEAD"], root).strip()
    p = subprocess.run(["git", "merge-base", "--is-ancestor", snap["head"], head], cwd=root, capture_output=True, timeout=GIT_TIMEOUT, creationflags=NO_WINDOW)
    if p.returncode != 0:
        print("  GATE-INTEGRITY  the head about to merge (%s) does not descend from the reviewed head (%s)" % (head[:12], snap["head"][:12]))
        print("review-guard: GATE-INTEGRITY - do not merge; the reviews approved a different history")
        return 1
    changed = [l.strip() for l in run_git(["diff", "--name-only", snap["head"], head], root).splitlines() if l.strip()]
    other = [c for c in changed if not c.replace("\\", "/").startswith("run/review/")]
    if other:
        for c in other:
            print("  GATE-INTEGRITY  changed since the review outside run/review/: %s" % c)
        print("review-guard: GATE-INTEGRITY - do not merge; re-run the reviews on the new head")
        return 1
    print("review-guard: OK - %s descends from the reviewed %s and differs only under run/review/ (%d file(s))" % (head[:12], snap["head"][:12], len(changed)))
    return 0


def main():
    argv = sys.argv[1:]
    if len(argv) < 2 or argv[0] not in ("snapshot", "verify", "premerge"):
        print(__doc__.split("\n\n")[1])
        return 2
    cwd = argv[2] if len(argv) > 2 else os.getcwd()
    try:
        return {"snapshot": cmd_snapshot, "verify": cmd_verify, "premerge": cmd_premerge}[argv[0]](argv[1], cwd)
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as e:
        print("review-guard: CANNOT VERIFY - %s" % e)
        return 2


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
