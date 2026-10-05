#!/usr/bin/env python3
"""review-guard: the committed checkpoint a reviewer with execution runs on, snapshotted
before the launch, verified and restored after it, and checked once more before the merge.

  python ~/.claude/cursor-bridge/review-guard.py snapshot <nnn>          before launching Review B
  python ~/.claude/cursor-bridge/review-guard.py verify   <nnn>          after it returns
  python ~/.claude/cursor-bridge/review-guard.py premerge <nnn> [<pr>]   after the review files are removed, committed and pushed

Why (release 0b review, finding 2 and its second pass): Review B keeps `--force` so it can
run the tests and build reproductions (the owner's decision), and it acts after Review A and
right before the merge, so what it leaves behind has no gate after it. `git status` followed
by `git checkout -- .` and `git clean -fd` restores tracked and untracked files only: it does
not see a moved HEAD, a commit, a new ref or stash, a changed `.git/config` or hook (which
would make the supervisor's next git command run the reviewer's program with the owner's
identity), or a changed ignored file (`.env`, a record a project keeps gitignored, a brief).

What each step does:
  snapshot  refuses a dirty tree (commit first); records HEAD, the branch, every ref, the
            stash list, a hash of `.git/config`, of every file in the ACTIVE hooks folder
            (`core.hooksPath`, read from the config file, or `.git/hooks`) and in
            `.git/hooks`, and every ignored file with its size and mtime (cache folders
            such as `.venv`, `node_modules` and `__pycache__` are skipped); writes
            <git common dir>/bridge/review-<nnn>.json and prints that file's hash.
  verify    reads the configuration and the hooks folders FIRST, as files, without running
            git: a change is GATE-INTEGRITY and nothing else runs. Every git command the
            guard runs is given `-c core.hooksPath=<an empty folder> -c core.fsmonitor=false`,
            so no hook of the repository runs inside the guard. It then compares HEAD, the
            branch, the local refs (heads, tags, stash) and the stashes - a difference is
            GATE-INTEGRITY, and each ref is put back - restores the tree (`git reset --hard
            <sha>`, `git clean -fd`, keeping the launcher's own `run/review/REVIEW-<nnn>.err`,
            whose first line it prints), lists what it removed, and compares the ignored
            files: a change under docs/, handoff/, run/review/ or to `.env*` is
            GATE-INTEGRITY, any other is LEFT BEHIND. A moved remote-tracking ref (a fetch)
            is a note. It prints the snapshot file's hash again: compare it with the one
            `snapshot` printed, since the reviewer could rewrite the snapshot.
  premerge  refuses a dirty tree; the head about to merge must descend from the reviewed
            head and differ from it only under run/review/ (the review files removed with
            `git rm`); with <pr>, the pull request's head on GitHub must equal the local
            HEAD (push first; a branch updated from main needs the reviews again). It prints
            the merge command with `--match-head-commit`.

Exit 0 = OK; 1 = GATE-INTEGRITY (open the flag, condition 4, and an issue; do not merge);
2 = cannot verify (no snapshot, dirty tree, git or gh failure). Never prints a value of
anything. ASCII-only.

What it does not cover, said plainly (KP-032): the contents of cache folders, anything
outside the checkout (the owner's profile, the installed bridge, other projects), and a
reviewer that deliberately reaches for the credential store. It is a guard against what a
reviewer does in passing, not a sandbox.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

GIT_TIMEOUT = 120
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
CACHE_DIRS = {".venv", "venv", "env", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
              ".tox", ".nox", "dist", "build", ".cache", "target", ".next", ".turbo", "coverage", "site-packages", ".ipynb_checkpoints"}
PROTECTED_PREFIXES = ("docs/", "handoff/", "run/review/")
MAX_IGNORED_FILES = 50000
_NO_HOOKS = {}


def no_hooks_dir(common):
    d = os.path.join(common, "bridge", "no-hooks")
    os.makedirs(d, exist_ok=True)
    return d


def run_git(args, root, common):
    """Every git command of the guard runs with the repository's hooks and file monitor
    switched off: a hook a reviewer left in the active hooks folder must never run here."""
    cmd = ["git", "-c", "core.hooksPath=" + no_hooks_dir(common), "-c", "core.fsmonitor=false"] + list(args)
    p = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=GIT_TIMEOUT, creationflags=NO_WINDOW)
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


def hooks_path_from_config(common, root):
    """core.hooksPath read from the config FILE (never through git), resolved against the
    worktree root as git does; None when unset."""
    try:
        with open(os.path.join(common, "config"), encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return None
    section = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^\[([^\]]+)\]", s)
        if m:
            section = m.group(1).strip().lower()
            continue
        m = re.match(r"^hookspath\s*=\s*(.+?)\s*$", s, re.I)
        if m and section == "core":
            p = m.group(1).strip().strip('"')
            return p if os.path.isabs(p) else os.path.normpath(os.path.join(root, p))
    return None


def folder_hashes(folder):
    out = {}
    if not folder or not os.path.isdir(folder):
        return out
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if d not in CACHE_DIRS)
        for name in sorted(filenames):
            p = os.path.join(dirpath, name)
            out[os.path.relpath(p, folder).replace("\\", "/")] = sha256_file(p)
    return out


def config_state(common, root):
    hp = hooks_path_from_config(common, root)
    return {"config": sha256_file(os.path.join(common, "config")), "hooks_path": hp,
            "active_hooks": folder_hashes(hp), "git_hooks": folder_hashes(os.path.join(common, "hooks"))}


def ignored_entries(root, common):
    """Every ignored file with size:mtime (cache folders skipped, bounded), directories that
    were skipped or too large recorded by name."""
    out, count = {}, 0
    text = run_git(["status", "--porcelain", "--ignored", "-unormal"], root, common)
    for line in text.splitlines():
        if not line.startswith("!! "):
            continue
        rel = line[3:].strip()
        full = os.path.join(root, rel.rstrip("/"))
        if os.path.isfile(full):
            try:
                st = os.stat(full)
                out[rel] = "%d:%d" % (st.st_size, int(st.st_mtime))
            except OSError:
                out[rel] = "?"
            continue
        if not os.path.isdir(full):
            out[rel] = "?"
            continue
        base = os.path.basename(rel.rstrip("/"))
        if base in CACHE_DIRS or base.endswith("_cache") or base.endswith(".egg-info"):
            out[rel] = "cache-dir"
            continue
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = sorted(d for d in dirnames if d not in CACHE_DIRS and not d.endswith("_cache") and not d.endswith(".egg-info"))
            for name in sorted(filenames):
                p = os.path.join(dirpath, name)
                r = os.path.relpath(p, root).replace("\\", "/")
                try:
                    st = os.stat(p)
                    out[r] = "%d:%d" % (st.st_size, int(st.st_mtime))
                except OSError:
                    out[r] = "?"
                count += 1
                if count > MAX_IGNORED_FILES:
                    out[rel] = "dir:large"
                    break
            if count > MAX_IGNORED_FILES:
                break
    return out


def refs(root, common):
    return dict(line.split(" ", 1)[::-1] for line in run_git(["for-each-ref", "--format=%(objectname) %(refname)"], root, common).splitlines() if " " in line)


def local_ref(name):
    return not name.startswith("refs/remotes/")


def stashes(root, common):
    return [l.strip() for l in run_git(["stash", "list"], root, common).splitlines() if l.strip()]


def snapshot_path(common, nnn):
    return os.path.join(common, "bridge", "review-%s.json" % nnn)


def cmd_snapshot(nnn, cwd):
    root, git_dir, common = find_git_dirs(cwd)
    if not root:
        print("review-guard: not inside a git checkout")
        return 2
    if run_git(["status", "--porcelain"], root, common).strip():
        print("review-guard: CANNOT SNAPSHOT - the tree is not clean; commit everything of yours first (rule 2)")
        return 2
    head = run_git(["rev-parse", "HEAD"], root, common).strip()
    try:
        branch = run_git(["symbolic-ref", "-q", "HEAD"], root, common).strip()
    except RuntimeError:
        branch = ""                               # detached
    snap = {
        "nnn": str(nnn), "taken": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": root, "head": head, "branch": branch,
        "refs": refs(root, common), "stashes": stashes(root, common),
        "git": config_state(common, root), "ignored": ignored_entries(root, common),
    }
    os.makedirs(os.path.join(common, "bridge"), exist_ok=True)
    path = snapshot_path(common, nnn)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=1, sort_keys=True)
    print("review-guard: snapshot %s taken at %s on %s (%d refs, %d stashes, %d ignored entries, hooks at %s)" % (
        head[:12], snap["taken"], branch or "detached HEAD", len(snap["refs"]), len(snap["stashes"]), len(snap["ignored"]),
        snap["git"]["hooks_path"] or os.path.join(common, "hooks")))
    print("review-guard: snapshot hash %s - compare it with the hash `verify` prints" % sha256_file(path)[:16])
    return 0


def load_snapshot(nnn, cwd):
    root, git_dir, common = find_git_dirs(cwd)
    if not root:
        print("review-guard: not inside a git checkout")
        return None, None, None, None
    p = snapshot_path(common, nnn)
    if not os.path.isfile(p):
        print("review-guard: CANNOT VERIFY - no snapshot %s (run `review-guard.py snapshot %s` before the launch)" % (p, nnn))
        return None, None, None, None
    with open(p, encoding="utf-8") as f:
        return json.load(f), root, common, sha256_file(p)[:16]


def diff_hashes(before, after):
    changed = sorted(set(before) ^ set(after))
    changed += sorted(k for k in before if k in after and before[k] != after[k])
    return changed


def cmd_verify(nnn, cwd):
    snap, root, common, snap_hash = load_snapshot(nnn, cwd)
    if snap is None:
        return 2
    flags, notes = [], []
    # 1. the repository's configuration and hooks, read as files, before any git command runs
    now = config_state(common, root)
    if now["config"] != snap["git"]["config"]:
        flags.append(".git/config changed during the review - do not run git until you have read it (a core.fsmonitor or core.hooksPath line runs a program with your identity)")
    if now["hooks_path"] != snap["git"]["hooks_path"]:
        flags.append("core.hooksPath changed during the review: %s -> %s" % (snap["git"]["hooks_path"], now["hooks_path"]))
    for label, key in (("the active hooks folder", "active_hooks"), (".git/hooks", "git_hooks")):
        changed = diff_hashes(snap["git"].get(key) or {}, now.get(key) or {})
        if changed:
            flags.append("hook files changed in %s during the review: %s - read them before any git command runs" % (label, ", ".join(changed[:6])))
    if flags:
        for f in flags:
            print("  GATE-INTEGRITY  " + f)
        print("review-guard: GATE-INTEGRITY - the checkout was NOT restored and no git command was run; inspect the configuration and the hooks first")
        return 1
    # 2. where HEAD is, and the refs
    head = run_git(["rev-parse", "HEAD"], root, common).strip()
    try:
        branch = run_git(["symbolic-ref", "-q", "HEAD"], root, common).strip()
    except RuntimeError:
        branch = ""
    if branch != snap["branch"]:
        flags.append("the branch changed during the review: %s -> %s" % (snap["branch"] or "detached", branch or "detached"))
    if head != snap["head"]:
        flags.append("HEAD moved during the review: %s -> %s (a checkout or a commit)" % (snap["head"][:12], head[:12]))
    now_refs = refs(root, common)
    repairs = []                                   # (ref, old sha or None)
    for name, sha in sorted(now_refs.items()):
        if name not in snap["refs"]:
            if local_ref(name):
                flags.append("new ref during the review: %s" % name)
                repairs.append((name, None))
            else:
                notes.append("NOTE remote-tracking ref appeared during the review (a fetch): %s" % name)
        elif snap["refs"][name] != sha:
            if local_ref(name):
                flags.append("ref moved during the review: %s" % name)
                repairs.append((name, snap["refs"][name]))
            else:
                notes.append("NOTE remote-tracking ref moved during the review (a fetch): %s" % name)
    for name in sorted(set(snap["refs"]) - set(now_refs)):
        if local_ref(name):
            flags.append("ref deleted during the review: %s" % name)
            repairs.append((name, snap["refs"][name]))
        else:
            notes.append("NOTE remote-tracking ref gone during the review: %s" % name)
    now_stashes = stashes(root, common)
    if len(now_stashes) != len(snap["stashes"]):
        flags.append("the stash list changed during the review (%d -> %d entries)" % (len(snap["stashes"]), len(now_stashes)))
    # 3. restore the tree: the recorded branch first (a reset on another branch would move it), then the refs
    dirty = [l for l in run_git(["status", "--porcelain"], root, common).splitlines() if l.strip()]
    if snap["branch"]:
        if snap["branch"] not in now_refs:         # the reviewer deleted the task branch itself
            run_git(["update-ref", snap["branch"], snap["head"]], root, common)
            notes.append("repaired: %s recreated at %s" % (snap["branch"], snap["head"][:12]))
        if branch != snap["branch"]:
            run_git(["checkout", "-q", "-f", snap["branch"][len("refs/heads/"):] if snap["branch"].startswith("refs/heads/") else snap["branch"]], root, common)
        run_git(["reset", "-q", "--hard", snap["head"]], root, common)
    else:
        run_git(["checkout", "-q", "-f", "--detach", snap["head"]], root, common)
    for name, old in repairs:
        if name == snap["branch"] or name == "refs/stash":
            continue
        if old is None:
            run_git(["update-ref", "-d", name], root, common)
            notes.append("repaired: %s deleted (it did not exist at the snapshot)" % name)
        else:
            run_git(["update-ref", name, old], root, common)
            notes.append("repaired: %s back to %s" % (name, old[:12]))
    err_rel = "run/review/REVIEW-%s.err" % nnn
    err_path = os.path.join(root, "run", "review", "REVIEW-%s.err" % nnn)
    if os.path.isfile(err_path):
        try:
            with open(err_path, encoding="utf-8", errors="replace") as f:
                first = f.readline().strip()
            notes.append("launch time line kept (%s): %s" % (err_rel, first[:120]))
        except OSError:
            pass
    cleaned = [l.strip() for l in run_git(["clean", "-fd", "-e", err_rel], root, common).splitlines() if l.strip()]
    for l in dirty:
        notes.append("restored: " + l.strip())
    for l in cleaned:
        notes.append(l)
    # 4. ignored files: records, briefs and review material are protected even when ignored
    now_ign = ignored_entries(root, common)
    for rel in sorted(set(now_ign) | set(snap["ignored"])):
        before, after = snap["ignored"].get(rel), now_ign.get(rel)
        if before == after or rel == err_rel:
            continue
        what = "new" if before is None else ("removed" if after is None else "changed")
        base = os.path.basename(rel.rstrip("/"))
        if base == ".env" or base.startswith(".env.") or rel.startswith(PROTECTED_PREFIXES):
            flags.append("%s %s during the review (ignored by git, so not restored) - inspect it before anything runs" % (rel, what))
        else:
            notes.append("LEFT BEHIND (ignored, %s): %s" % (what, rel))
    for n in notes:
        print("  " + n)
    for f in flags:
        print("  GATE-INTEGRITY  " + f)
    print("review-guard: snapshot hash %s - must equal the hash `snapshot` printed" % snap_hash)
    left = sum(1 for n in notes if n.startswith("LEFT BEHIND"))
    if flags:
        print("review-guard: GATE-INTEGRITY - the tree is back at %s on %s and the refs are repaired, but the review left the marks above: open the flag (condition 4) and an issue; do not merge" % (snap["head"][:12], snap["branch"] or "detached HEAD"))
        return 1
    print("review-guard: OK - checkout restored to %s on %s (%d item(s) restored or removed, %d ignored entr%s left behind)" % (
        snap["head"][:12], snap["branch"] or "detached HEAD", len(dirty) + len(cleaned), left, "y" if left == 1 else "ies"))
    return 0


def cmd_premerge(nnn, cwd, pr=None):
    snap, root, common, snap_hash = load_snapshot(nnn, cwd)
    if snap is None:
        return 2
    if run_git(["status", "--porcelain"], root, common).strip():
        print("review-guard: CANNOT CHECK - the tree is not clean; commit the removal of the review files first")
        return 2
    head = run_git(["rev-parse", "HEAD"], root, common).strip()
    p = subprocess.run(["git", "-c", "core.hooksPath=" + no_hooks_dir(common), "merge-base", "--is-ancestor", snap["head"], head], cwd=root, capture_output=True, timeout=GIT_TIMEOUT, creationflags=NO_WINDOW)
    if p.returncode != 0:
        print("  GATE-INTEGRITY  the head about to merge (%s) does not descend from the reviewed head (%s)" % (head[:12], snap["head"][:12]))
        print("review-guard: GATE-INTEGRITY - do not merge; the reviews approved a different history")
        return 1
    changed = [l.strip() for l in run_git(["diff", "--name-only", snap["head"], head], root, common).splitlines() if l.strip()]
    other = [c for c in changed if not c.replace("\\", "/").startswith("run/review/")]
    if other:
        for c in other:
            print("  GATE-INTEGRITY  changed since the review outside run/review/: %s" % c)
        print("review-guard: GATE-INTEGRITY - do not merge; re-run the reviews on the new head")
        return 1
    if pr:
        try:
            g = subprocess.run(["gh", "pr", "view", str(pr), "--json", "headRefOid", "--jq", ".headRefOid"], cwd=root, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=60, creationflags=NO_WINDOW)
        except (OSError, subprocess.TimeoutExpired) as e:
            print("review-guard: CANNOT CHECK - gh pr view failed (%s)" % e)
            return 2
        if g.returncode != 0:
            print("review-guard: CANNOT CHECK - gh pr view failed: %s" % (g.stderr.strip() or g.stdout.strip())[:200])
            return 2
        remote_head = g.stdout.strip()
        if remote_head != head:
            print("  GATE-INTEGRITY  the pull request's head on GitHub (%s) is not the local head (%s): push first; if the branch was updated from main on GitHub, the reviews run again on that head" % (remote_head[:12], head[:12]))
            print("review-guard: NOT READY - do not merge yet")
            return 1
    print("review-guard: OK - %s descends from the reviewed %s and differs only under run/review/ (%d file(s))%s" % (
        head[:12], snap["head"][:12], len(changed), "; the pull request's head matches" if pr else ""))
    print("review-guard: merge with  gh pr merge %s--squash --match-head-commit %s" % ((str(pr) + " ") if pr else "", head))
    return 0


def main():
    argv = sys.argv[1:]
    if len(argv) < 2 or argv[0] not in ("snapshot", "verify", "premerge"):
        print(__doc__.split("\n\n")[1])
        return 2
    try:
        if argv[0] == "premerge":
            return cmd_premerge(argv[1], os.getcwd(), argv[2] if len(argv) > 2 else None)
        return {"snapshot": cmd_snapshot, "verify": cmd_verify}[argv[0]](argv[1], os.getcwd())
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as e:
        print("review-guard: CANNOT VERIFY - %s" % e)
        return 2


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
