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
  snapshot  refuses a dirty tree (commit first); lists the review's input files (the files
            directly under run/review/ whose name contains <nnn>, the launcher's
            REVIEW-<nnn>.err excepted) with their sizes and refuses when one is empty, since
            both reviewers would read an empty input (KP-067: `git show <rev>:<path>
            --output=<file>` creates the file empty; none found is a NOTE); records HEAD,
            the branch, every ref, the stash list, a hash of `.git/config`, of every file in
            the ACTIVE hooks folder (`core.hooksPath`, read from the config file, or
            `.git/hooks`) and in `.git/hooks`, and every ignored file with its size and
            mtime (cache folders such as `.venv`, `node_modules` and `__pycache__` are
            skipped); writes
            <git common dir>/bridge/review-<nnn>.json and a copy of its sha256 outside the
            checkout the reviewer runs in (~/.cursor-bridge/review-hashes/<key>-<nnn>.sha256,
            FB-037), and prints that file's hash. `verify` and `premerge` compare the copy
            themselves: a mismatch is GATE-INTEGRITY, a missing copy CANNOT VERIFY (take the
            snapshot again).
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
            is a note. Before all of this it compares the snapshot file's hash with the copy
            `snapshot` wrote: a difference is GATE-INTEGRITY (the snapshot was rewritten after
            it was taken; nothing is restored from it), a missing copy CANNOT VERIFY (take the
            snapshot again; a snapshot taken by an older release has none). It prints the snapshot file's hash again: compare it with the
            one `snapshot` printed, since the reviewer could rewrite the snapshot.
  premerge  needs the verified mark `verify` wrote for this snapshot (release A1b, second and
            third passes: Review B launched after the snapshot through the launcher and ended
            with exit 0, the last `verify` OK; `snapshot` and `verify` remove an older mark), so a
            merge that skipped the cross-family review has no way through; compares the
            snapshot's hash with its copy as `verify` does; refuses a dirty
            tree; the head about to merge must descend from the reviewed head and differ from
            it only under run/review/ (the review files removed with `git rm`); with <pr>, the
            pull request's head on GitHub must equal the local HEAD (push first; a branch
            updated from main needs the reviews again). GitHub can lag a push: a head that
            differs is read again every 15 seconds for up to 90 before it is flagged, and the
            wait is printed either way (2026-10-18 C2). It writes the record the permission
            guard reads (<git common dir>/bridge/premerge/<head>) and prints the merge command
            with `--match-head-commit`.

Exit 0 = OK; 1 = GATE-INTEGRITY (open the flag, condition 4, and an issue; do not merge);
2 = cannot verify (no snapshot, dirty tree, git or gh failure); 125 = refused (review round
ceiling, grammar, branch rule; writes no snapshot). Never prints a value of anything.
ASCII-only.

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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env  # noqa: E402

GIT_TIMEOUT = 120
GIT_SHORT = bridge_env.GIT_TIMEOUT
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
CACHE_DIRS = {".venv", "venv", "env", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
              ".tox", ".nox", "dist", "build", ".cache", "target", ".next", ".turbo", "coverage", "site-packages", ".ipynb_checkpoints"}
PROTECTED_PREFIXES = ("docs/", "handoff/", "run/review/")
MAX_IGNORED_FILES = 50000
PR_HEAD_WAIT, PR_HEAD_STEP = 90, 15                # premerge: how long, and how often, GitHub's head is read again
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


def held_elsewhere(branch_ref, root, common):
    """The path of another worktree that has `branch_ref` checked out, else None (release A4)."""
    try:
        out = run_git(["worktree", "list", "--porcelain"], root, common)
    except RuntimeError:
        return None
    here = os.path.normcase(os.path.realpath(root))
    path = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):].strip()
        elif line.startswith("branch ") and line[len("branch "):].strip() == branch_ref and path:
            if os.path.normcase(os.path.realpath(path)) != here:
                return path
    return None


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


def hash_copy_path(common, nnn):
    """~/.cursor-bridge/review-hashes/<the repository's key>-<nnn>.sha256: outside the checkout the
    reviewer runs in (the snapshot itself lies in its .git/, within the reviewer's reach). The
    bridge's own test suite points BRIDGE_REVIEW_HASHES at a temporary folder."""
    key = hashlib.sha256(os.path.normcase(os.path.abspath(common)).encode("utf-8")).hexdigest()[:16]
    folder = os.environ.get("BRIDGE_REVIEW_HASHES") or os.path.join(os.path.expanduser("~"), ".cursor-bridge", "review-hashes")
    return os.path.join(folder, "%s-%s.sha256" % (key, nnn))


def snapshot_rewritten(common, nnn):
    """'rewritten' when the snapshot file's hash differs from the copy `snapshot` wrote outside the
    checkout (FB-037), 'missing' when there is no copy (fail closed: a snapshot taken before this
    release or a deleted copy is taken again), None when it matches."""
    try:
        with open(hash_copy_path(common, nnn), encoding="utf-8") as f:
            recorded = f.read().strip()
    except OSError:
        print("review-guard: CANNOT VERIFY - no copy of the snapshot hash (%s): take the snapshot again and run Review B on it (a snapshot taken before 2026.10.25a has none)" % hash_copy_path(common, nnn))
        return "missing"
    if sha256_file(snapshot_path(common, nnn)) != recorded:
        print("  GATE-INTEGRITY  the snapshot was rewritten after it was taken: %s no longer matches the hash in %s" % (snapshot_path(common, nnn), hash_copy_path(common, nnn)))
        return "rewritten"
    return None


def review_inputs(root, nnn):
    """[(name, size)] of the files directly under run/review/ whose name contains <nnn>, the
    launcher's own REVIEW-<nnn>.err excepted: what the two reviewers are told to read."""
    folder = os.path.join(root, "run", "review")
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    out = []
    for name in names:
        p = os.path.join(folder, name)
        if str(nnn) in name and name != "REVIEW-%s.err" % nnn and os.path.isfile(p):
            out.append((name, os.path.getsize(p)))
    return out


def mark_path(common, nnn):
    return os.path.join(common, "bridge", "verified-%s.json" % nnn)


def launch_info(err_path):
    """(launch time, exit code) from run/review/REVIEW-<nnn>.err: the launcher's first line
    `bridge-run: started <UTC>Z` and its last `bridge-run: exit <code>` (None while it runs)."""
    try:
        with open(err_path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return None, None
    m = None
    for line in lines[:5]:                                 # the launcher writes it first; a few lines of slack
        m = re.search(r"bridge-run: started\s+(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)", line)
        if m:
            break
    code = None
    for line in reversed(lines):
        e = re.match(r"bridge-run: exit (\d+)", line.strip())
        if e:
            code = int(e.group(1))
            break
    return (m.group(1) if m else None), code


def rounds_path(common, id_part):
    return os.path.join(common, "bridge", "rounds-%s.json" % id_part)


def rounds_hash_copy_path(common, id_part):
    key = hashlib.sha256(os.path.normcase(os.path.abspath(common)).encode("utf-8")).hexdigest()[:16]
    folder = os.environ.get("BRIDGE_REVIEW_HASHES") or os.path.join(os.path.expanduser("~"), ".cursor-bridge", "review-hashes")
    return os.path.join(folder, "%s-rounds-%s.sha256" % (key, id_part))


def _validate_rounds_data(data, id_part):
    if not isinstance(data, dict):
        return "rounds record is not an object"
    rounds = data.get("rounds")
    if rounds is None:
        data["rounds"] = []
        return None
    if not isinstance(rounds, list):
        return "rounds is not a list"
    for r in rounds:
        if not isinstance(r, dict):
            return "round entry is not an object"
        rn = r.get("round")
        if rn is None or isinstance(rn, bool) or not isinstance(rn, int):
            return "round field is not an int"
    return None


def _seed_refuse_snapshots(common, id_part):
    bridge = os.path.join(common, "bridge")
    if not os.path.isdir(bridge):
        return None
    for name in os.listdir(bridge):
        if not name.startswith("review-%s" % id_part) or not name.endswith(".json"):
            continue
        if name == "review-%s.json" % id_part or re.match(r"^review-%s-r\d+\.json$" % re.escape(id_part), name):
            try:
                with open(os.path.join(bridge, name), encoding="utf-8", errors="replace") as f:
                    snap = json.load(f)
            except (OSError, ValueError):
                continue
            if isinstance(snap, dict) and snap.get("round") is not None:
                return "review-guard: refused - rounds record missing beside snapshot with round field: %s" % id_part
    return None


def _snapshot_counts_for_id(root, id_part, snap_token):
    if snap_token == id_part:
        return True
    if snap_token.startswith(id_part) and len(snap_token) > len(id_part):
        extra = snap_token[len(id_part) :]
        if re.fullmatch(r"[a-z]+", extra):
            if os.path.isfile(os.path.join(root, "handoff", "%s.md" % snap_token)):
                return False
            return os.path.isfile(os.path.join(root, "handoff", "%s.md" % id_part))
    return False


def _letter_snapshot_rounds(common, root, id_part):
    bridge = os.path.join(common, "bridge")
    entries = []
    if os.path.isdir(bridge):
        for name in os.listdir(bridge):
            if not name.startswith("review-") or not name.endswith(".json"):
                continue
            token = name[len("review-") : -len(".json")]
            if "-r" in token:
                continue
            if not _snapshot_counts_for_id(root, id_part, token):
                continue
            sort_key = token[len(id_part) :] if token.startswith(id_part) else token
            entries.append((sort_key, token, name))
    entries.sort(key=lambda x: x[0])
    if not entries:
        return 0, None
    branches = []
    for _, _, fname in entries:
        try:
            with open(os.path.join(bridge, fname), encoding="utf-8", errors="replace") as f:
                snap = json.load(f)
        except (OSError, ValueError):
            return 0, None
        if not isinstance(snap, dict):
            return 0, None
        branches.append(bridge_env.norm_branch(snap.get("branch") or ""))
    if branches and any(b != branches[0] for b in branches):
        return 0, None
    return len(entries), branches[0] if branches else ""


def _report_file_rounds(root, common, id_part):
    try:
        out = run_git(["ls-files", "handoff/"], root, common)
    except RuntimeError:
        return 0
    lines = out.splitlines()
    pat = re.compile(r"^handoff/%s-r(\d+)[a-z]?-report\.md$" % re.escape(id_part))
    best = 0
    for line in lines:
        m = pat.match(line.replace("\\", "/"))
        if m:
            best = max(best, int(m.group(1)))
    return best


def _seed_rounds(common, root, id_part):
    refuse = _seed_refuse_snapshots(common, id_part)
    if refuse:
        return None, refuse
    letter_n, branch = _letter_snapshot_rounds(common, root, id_part)
    report_n = _report_file_rounds(root, common, id_part)
    n = max(letter_n, report_n)
    if n <= 0:
        return {"id": id_part, "rounds": []}, None
    rounds = []
    for i in range(1, n + 1):
        rounds.append(
            {
                "round": i,
                "name": id_part if i == 1 else "%s-r%d" % (id_part, i),
                "branch": branch or "",
                "tree": "",
                "time": "",
                "lift": None,
                "reply": 0,
                "seeded": True,
            }
        )
    return {"id": id_part, "rounds": rounds}, None


def _rounds_tamper(common, id_part, path):
    copy = rounds_hash_copy_path(common, id_part)
    if os.path.isfile(copy) and not os.path.isfile(path):
        return "review-guard: refused - rounds record changed outside the guard: %s" % id_part
    if not os.path.isfile(path):
        return None
    digest = sha256_file(path)
    if not digest:
        return "review-guard: refused - rounds record unreadable: %s" % id_part
    try:
        with open(copy, encoding="utf-8") as f:
            recorded = f.read().strip()
    except OSError:
        os.makedirs(os.path.dirname(copy), exist_ok=True)
        with open(copy, "w", encoding="utf-8") as f:
            f.write(digest + "\n")
        return None
    if recorded != digest:
        return "review-guard: refused - rounds record changed outside the guard: %s" % id_part
    return None


def load_rounds(common, id_part, root=None):
    path = rounds_path(common, id_part)
    if not os.path.isfile(path) and root is not None:
        seeded, err = _seed_rounds(common, root, id_part)
        if err:
            return None, path, err
        if seeded and seeded.get("rounds"):
            write_rounds(common, id_part, seeded)
        elif seeded:
            return seeded, path, None
    tamper = _rounds_tamper(common, id_part, path) if os.path.isfile(path) else None
    if tamper:
        return None, path, tamper
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None, path, "review-guard: refused - rounds record unreadable: %s" % id_part
    err = _validate_rounds_data(data, id_part)
    if err:
        return None, path, "review-guard: refused - %s: %s" % (err, id_part)
    data.setdefault("id", id_part)
    return data, path, None


def write_rounds(common, id_part, data):
    import tempfile
    path = rounds_path(common, id_part)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".rounds-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, sort_keys=True)
        os.replace(tmp, path)
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    digest = sha256_file(path)
    if digest:
        copy = rounds_hash_copy_path(common, id_part)
        os.makedirs(os.path.dirname(copy), exist_ok=True)
        with open(copy, "w", encoding="utf-8") as f:
            f.write(digest + "\n")


def scope_blocking_line(root, id_part):
    for name in ("SCOPE-%s.md" % id_part, "SCOPE-STAGE-%s.md" % id_part):
        p = os.path.join(root, "run", "review", name)
        if os.path.isfile(p):
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            blk = bridge_env.read_blocking_class_line(text)
            if blk:
                return blk
    return None


def snapshot_review_refusal(nnn, root, common):
    if str(nnn).startswith("DESIGN-"):
        return None
    parsed = bridge_env.parse_review_name(str(nnn))
    if not parsed:
        return "review-guard: refused - the name cannot be read by the grammar"
    id_part, name_round = parsed
    log_folder = bridge_env.launcher_log_folder(common, root)
    id_rx = bridge_env.grammar_id_rx()
    owner_lifts = bridge_env.review_owner_lifts(root)
    br = bridge_env.norm_branch(run_git(["rev-parse", "--abbrev-ref", "HEAD"], root, common).strip())
    if br == "main":
        return "review-guard: refused - branch rule: reviews run on a branch, not main"
    if br == "HEAD":
        return "review-guard: refused - branch rule: reviews run on a branch, not a detached HEAD"
    ok, why = bridge_env.branch_allows_id(log_folder, common, root, br, id_part, owner_lifts, id_rx)
    if not ok:
        if isinstance(why, frozenset):
            return "review-guard: refused - branch rule: %s is not on this branch (counted: %s)" % (id_part, ", ".join(sorted(why)))
        return "review-guard: refused - branch rule"
    data, _, err = load_rounds(common, id_part, root)
    if err:
        return err
    rounds = data.get("rounds") or []
    by_num = {r.get("round"): r for r in rounds if isinstance(r.get("round"), int)}
    current = max(by_num) if by_num else 0
    tree = run_git(["rev-parse", "HEAD^{tree}"], root, common).strip()
    if name_round not in (current, current + 1) and not (name_round == 1 and current == 0):
        return "review-guard: refused - round %d is off the count (current %d)" % (name_round, current)
    if name_round in by_num:
        prev = by_num[name_round]
        if prev.get("reply") is not None and prev.get("tree") and prev.get("tree") != tree:
            return "review-guard: refused - round %d is reviewed: write %s-r%d" % (name_round, id_part, name_round + 1)
    scope_text = ""
    scope_path = os.path.join(root, "run", "review", "SCOPE-%s.md" % id_part)
    if os.path.isfile(scope_path):
        try:
            scope_text = open(scope_path, encoding="utf-8", errors="replace").read()
        except OSError:
            pass
    blk = bridge_env.read_blocking_class_line(scope_text)
    used_class = {r.get("lift_line") for r in rounds if r.get("lift") == "class" and r.get("lift_line")}
    if blk and blk[2] in used_class and name_round > current:
        return "review-guard: refused - class line already recorded for %s" % id_part
    owner_entry = owner_lifts.get(id_part)
    owner_cap = owner_entry[0] if owner_entry else bridge_env.REVIEW_ROUNDS
    test_round = name_round if name_round > current else name_round
    if name_round > bridge_env.REVIEW_ROUNDS:
        if name_round <= owner_cap:
            return None
        if blk and blk[2] not in used_class:
            return None
        return (
            "review-guard: refused - review ceiling: %s (id %s, branch %s, round %d, ceiling %d)"
            % (nnn, id_part, br, name_round, bridge_env.REVIEW_ROUNDS)
        )
    return None


def remove_mark(common, nnn):
    """Only the last verify of the last snapshot counts: the mark goes before either runs."""
    try:
        os.remove(mark_path(common, nnn))
    except OSError:
        pass


def clear_verified_marks(common, id_part):
    bridge = os.path.join(common, "bridge")
    if not os.path.isdir(bridge):
        return
    for name in os.listdir(bridge):
        if name == "verified-%s.json" % id_part or (
            name.startswith("verified-%s-r" % id_part) and name.endswith(".json")
        ):
            try:
                os.remove(os.path.join(bridge, name))
            except OSError:
                pass


def cmd_snapshot(nnn, cwd):
    root, git_dir, common = find_git_dirs(cwd)
    if not root:
        print("review-guard: not inside a git checkout")
        return 2
    refusal = snapshot_review_refusal(nnn, root, common)
    if refusal:
        print(refusal)
        return 125
    if run_git(["status", "--porcelain"], root, common).strip():
        print("review-guard: CANNOT SNAPSHOT - the tree is not clean; commit everything of yours first (rule 2)")
        return 2
    # The review's input files, with their sizes (2026-10-25 C4, FB-003): an empty one is
    # refused before anything is written, since both reviewers would read nothing (KP-067).
    inputs = review_inputs(root, nnn)
    for name, size in inputs:
        print("review-guard: review input run/review/%s  %d bytes" % (name, size))
    if not inputs:
        print("  NOTE no review input file under run/review/ names %s" % nnn)
    empty = [name for name, size in inputs if size == 0]
    if empty:
        print("review-guard: CANNOT SNAPSHOT - run/review/%s is empty: both reviewers would read an empty input (KP-067: `git show <rev>:<path> --output=<file>` creates the file empty); write it again, commit, then snapshot" % ", run/review/".join(empty))
        return 2
    parsed_pre = bridge_env.parse_review_name(str(nnn)) if not str(nnn).startswith("DESIGN-") else None
    rounds_data = None
    if parsed_pre:
        rounds_data, _, err = load_rounds(common, parsed_pre[0], root)
        if err:
            print(err)
            return 125
    head = run_git(["rev-parse", "HEAD"], root, common).strip()
    try:
        branch = run_git(["symbolic-ref", "-q", "HEAD"], root, common).strip()
    except RuntimeError:
        branch = ""                               # detached
    parsed = bridge_env.parse_review_name(str(nnn)) if not str(nnn).startswith("DESIGN-") else None
    round_n = parsed[1] if parsed else None
    snap = {
        "nnn": str(nnn), "taken": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": root, "head": head, "branch": branch,
        "refs": refs(root, common), "stashes": stashes(root, common),
        "git": config_state(common, root), "ignored": ignored_entries(root, common),
    }
    if round_n is not None:
        snap["round"] = round_n
    os.makedirs(os.path.join(common, "bridge"), exist_ok=True)
    remove_mark(common, nnn)
    if parsed:
        clear_verified_marks(common, parsed[0])
    path = snapshot_path(common, nnn)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=1, sort_keys=True)
    os.makedirs(os.path.dirname(hash_copy_path(common, nnn)), exist_ok=True)
    with open(hash_copy_path(common, nnn), "w", encoding="utf-8") as f:
        f.write(sha256_file(path) + "\n")                   # the copy verify and premerge compare with (FB-037)
    print("review-guard: snapshot %s taken at %s on %s (%d refs, %d stashes, %d ignored entries, hooks at %s)" % (
        head[:12], snap["taken"], branch or "detached HEAD", len(snap["refs"]), len(snap["stashes"]), len(snap["ignored"]),
        snap["git"]["hooks_path"] or os.path.join(common, "hooks")))
    print("review-guard: snapshot hash %s - compare it with the hash `verify` prints" % sha256_file(path)[:16])
    if parsed:
        id_part, rnd = parsed
        data = rounds_data
        tree = run_git(["rev-parse", "HEAD^{tree}"], root, common).strip()
        br_short = bridge_env.norm_branch(branch)
        entry = {
            "round": rnd,
            "name": str(nnn),
            "branch": br_short,
            "tree": tree,
            "time": snap["taken"],
            "lift": None,
            "lift_line": None,
            "reply": None,
        }
        replaced = False
        for i, r in enumerate(data["rounds"]):
            if r.get("round") == rnd:
                entry["reply"] = r.get("reply")
                entry["lift"] = r.get("lift")
                entry["lift_line"] = r.get("lift_line")
                data["rounds"][i] = entry
                replaced = True
                break
        if not replaced:
            owner_lifts = bridge_env.review_owner_lifts(root)
            owner_entry = owner_lifts.get(id_part)
            blk = scope_blocking_line(root, id_part)
            if rnd > bridge_env.REVIEW_ROUNDS:
                if owner_entry and rnd <= owner_entry[0]:
                    entry["lift"], entry["lift_line"] = "owner", owner_entry[1]
                elif blk:
                    entry["lift"], entry["lift_line"] = "class", blk[2]
            data["rounds"].append(entry)
        write_rounds(common, id_part, data)
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
    remove_mark(common, nnn)                           # a failed verify leaves no mark behind
    # 0. the snapshot itself: a rewritten one would restore what the reviewer chose
    state = snapshot_rewritten(common, nnn)
    if state == "missing":
        return 2
    if state:
        print("review-guard: GATE-INTEGRITY - the snapshot was rewritten after it was taken; the checkout was NOT restored from it and no git command was run")
        return 1
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
            held = held_elsewhere(snap["branch"], root, common)
            if held:                                   # P3 (second pass of the plan review): a reset here would rewind the branch we are on
                print("review-guard: GATE-INTEGRITY - %s is checked out in another worktree (%s); the checkout was NOT restored and nothing was reset: tear that worktree down first (worktree-teardown.py), then verify again" % (snap["branch"], held))
                return 1
            run_git(["checkout", "-q", "-f", snap["branch"][len("refs/heads/"):] if snap["branch"].startswith("refs/heads/") else snap["branch"]], root, common)
            try:
                now_on = run_git(["symbolic-ref", "-q", "HEAD"], root, common).strip()
            except RuntimeError:
                now_on = ""
            if now_on != snap["branch"]:
                print("review-guard: GATE-INTEGRITY - the checkout could not be put back on %s (it is on %s); nothing was reset" % (snap["branch"], now_on or "a detached HEAD"))
                return 1
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
    # The verified mark premerge needs (second pass of the A1b review, S2): this snapshot's hash
    # and the launch time of the Review B run, so a merge that skipped the review has no mark.
    launched_at, exit_code = launch_info(err_path)
    snap_taken = (snap.get("taken") or "").rstrip("Z")
    launch_ok = launched_at and launched_at >= snap_taken
    if (
        not str(nnn).startswith("DESIGN-")
        and bridge_env.parse_review_name(str(nnn))
        and exit_code == 0
        and launch_ok
    ):
        id_part, rnd = bridge_env.parse_review_name(str(nnn))
        data, _, err = load_rounds(common, id_part, root)
        if not err:
            for r in data.get("rounds") or []:
                if r.get("round") == rnd and r.get("reply") is None:
                    r["reply"] = 0
                    break
            write_rounds(common, id_part, data)
    mark = {"nnn": str(nnn), "snapshot": snap_hash, "head": snap["head"], "taken": snap["taken"],
            "launched": launched_at, "exit": exit_code, "verified": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        with open(mark_path(common, nnn), "w", encoding="utf-8") as f:
            json.dump(mark, f, indent=1, sort_keys=True)
    except OSError as e:
        print("review-guard: CANNOT VERIFY - the verified mark could not be written (%s)" % e)
        return 2
    print("review-guard: OK - checkout restored to %s on %s (%d item(s) restored or removed, %d ignored entr%s left behind); verified mark written%s" % (
        snap["head"][:12], snap["branch"] or "detached HEAD", len(dirty) + len(cleaned), left, "y" if left == 1 else "ies",
        " (Review B launched %s, exit %s)" % (mark["launched"], mark["exit"]) if mark["launched"] else " (no launch time: run/review/REVIEW-%s.err missing, premerge will refuse)" % nnn))
    return 0


def pr_head(pr, root):
    """(the pull request's head sha on GitHub, None) or (None, the reason gh failed)."""
    try:
        g = subprocess.run(["gh", "pr", "view", str(pr), "--json", "headRefOid", "--jq", ".headRefOid"], cwd=root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, " (%s)" % e
    if g.returncode != 0:
        return None, ": %s" % (g.stderr.strip() or g.stdout.strip())[:200]
    return g.stdout.strip(), None


def cmd_premerge(nnn, cwd, pr=None):
    snap, root, common, snap_hash = load_snapshot(nnn, cwd)
    if snap is None:
        return 2
    state = snapshot_rewritten(common, nnn)
    if state == "missing":
        return 2
    if state:
        print("review-guard: GATE-INTEGRITY - do not merge; the snapshot was rewritten after it was taken")
        return 1
    try:
        with open(mark_path(common, nnn), encoding="utf-8") as f:
            mark = json.load(f)
    except (OSError, ValueError):
        mark = None
    if not isinstance(mark, dict):
        print("review-guard: CANNOT CHECK - no verified mark for %s: Review B runs after the snapshot (through the launcher, `2> run/review/REVIEW-%s.err`) and `review-guard.py verify %s` must print OK before any merge, a records-only change included" % (nnn, nnn, nnn))
        return 2
    if mark.get("snapshot") != snap_hash:
        print("review-guard: CANNOT CHECK - the verified mark for %s belongs to another snapshot (%s, now %s): run Review B and `verify` again on this snapshot" % (nnn, mark.get("snapshot"), snap_hash))
        return 2
    launched = (mark.get("launched") or "").rstrip("Z")
    if not launched or launched < (snap.get("taken") or "").rstrip("Z"):
        print("review-guard: CANNOT CHECK - no Review B launch after the snapshot of %s (run/review/REVIEW-%s.err missing, or its launch time %s is before the snapshot %s)" % (nnn, nnn, launched or "unknown", snap.get("taken")))
        return 2
    if mark.get("exit") != 0:
        print("review-guard: CANNOT CHECK - the Review B run of %s ended with exit %s (no verdict; a run that failed at once, or one still running): run it again, then `verify`" % (nnn, mark.get("exit")))
        return 2
    print("review-guard: verified mark for %s: snapshot %s, Review B launched %sZ and ended with exit 0, verified %s" % (nnn, snap_hash, launched, mark.get("verified")))
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
        remote_head, err = pr_head(pr, root)
        waited = 0
        while err is None and remote_head != head and waited < PR_HEAD_WAIT:
            time.sleep(PR_HEAD_STEP)                       # GitHub can lag a push (2026-10-18 C2)
            waited += PR_HEAD_STEP
            remote_head, err = pr_head(pr, root)
        if err is not None:
            print("review-guard: CANNOT CHECK - gh pr view failed%s" % err)
            return 2
        if waited:
            print("review-guard: the pull request's head on GitHub differed from the local head; waited %d seconds, read every %d, %s" % (
                waited, PR_HEAD_STEP, "now it matches" if remote_head == head else "it still differs"))
        if remote_head != head:
            print("  GATE-INTEGRITY  the pull request's head on GitHub (%s) is not the local head (%s), after waiting %d seconds: push first; if the branch was updated from main on GitHub, the reviews run again on that head" % (remote_head[:12], head[:12], waited))
            print("review-guard: NOT READY - do not merge yet")
            return 1
    print("review-guard: OK - %s descends from the reviewed %s and differs only under run/review/ (%d file(s))%s" % (
        head[:12], snap["head"][:12], len(changed), "; the pull request's head matches" if pr else ""))
    # The record the permission guard reads before it lets a merge through (release A1b): a
    # merge that skipped this check has no record and is refused; the sha alone proves nothing.
    folder = os.path.join(common, "bridge", "premerge")
    try:
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, head), "w", encoding="utf-8") as f:
            json.dump({"pr": pr, "review": nnn, "snapshot": snap_hash, "written": time.strftime("%Y-%m-%dT%H:%M:%S")}, f)
    except OSError as e:
        print("review-guard: CANNOT CHECK - the pre-merge record could not be written (%s)" % e)
        return 2
    print("review-guard: merge with  gh pr merge %s--squash --match-head-commit %s" % ((str(pr) + " ") if pr else "", head))
    return 0


def main():
    argv = sys.argv[1:]
    if len(argv) < 2 or argv[0] not in ("snapshot", "verify", "premerge"):
        print(__doc__.split("\n\n")[1])
        return 2
    if not str(argv[1]).startswith("DESIGN-") and not bridge_env.parse_review_name(str(argv[1])):
        print("review-guard: refused - the name cannot be read by the grammar")
        return 125
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
