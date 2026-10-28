"""Supervisor-side acceptance tests of TASK-032's guard half (R-042); written by the supervisor; the builder reads and runs them, never edits them.

Every guard test runs `python bridge/cursor-bridge/review-guard.py ...` as a subprocess on a
temporary git repository (GIT_CONFIG_GLOBAL and GIT_CONFIG_SYSTEM set to os.devnull, user.name
and user.email set in the repository). The environment is built at call time from os.environ,
after conftest's autouse fixture has set HOME and USERPROFILE to a temporary folder;
BRIDGE_REVIEW_HASHES is conftest's temporary folder. A launcher line is pre-written into the
main checkout's run/launcher/runs.jsonl in the format bridge-run.py's write_log writes
(json.dumps of the run's entry, one line). The permission-guard tests feed the hook's JSON on
stdin as tests/test_permission_guard.py does. Nothing here touches the real ~/.cursor-bridge/
or this repository's run/, .git/bridge/, docs/ or handoff/.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.normpath(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "review-guard.py"))
PGUARD = os.path.normpath(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py"))
TIMEOUT = 120

REFUSED = "review-guard: refused - "
CEILING = "review-guard: refused - review ceiling: "
TAMPER = "review-guard: refused - rounds record changed outside the guard: "
BRANCH_RULE_NOT = "review-guard: refused - branch rule: reviews run on a branch, not "
LAUNCHER = "python ~/.claude/cursor-bridge/bridge-run.py"


# --- helpers -------------------------------------------------------------------------------

def env():
    """The subprocess environment, built at call time (after the autouse fixture ran)."""
    assert os.environ.get("BRIDGE_REVIEW_HASHES"), "conftest must point BRIDGE_REVIEW_HASHES at a temporary folder"
    e = dict(os.environ)
    e["GIT_CONFIG_GLOBAL"] = os.devnull
    e["GIT_CONFIG_SYSTEM"] = os.devnull
    e["GIT_TERMINAL_PROMPT"] = "0"
    return e


def git(repo, *args):
    p = subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True, env=env(),
                       timeout=TIMEOUT)
    assert p.returncode == 0, (args, p.stderr)
    return p.stdout.strip()


def guard(repo, *args):
    """rc and stdout+stderr of review-guard.py run in `repo`."""
    p = subprocess.run([sys.executable, PROG] + list(args), cwd=str(repo), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env(), timeout=TIMEOUT)
    return p.returncode, p.stdout + p.stderr


def put(path, text):
    """Write text with LF line ends, creating the folders."""
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    data = text if isinstance(text, bytes) else text.encode("utf-8")
    with open(str(path), "wb") as f:
        f.write(data)


def make_repo(tmp_path, branch="task-001", files=None, name="ws"):
    """A checkout like the projects': run/ and docs/RUN_PARAMETERS.md ignored, `files` tracked,
    then a branch off main (None: stay on main)."""
    r = tmp_path / name
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.name", "Supervisor Test")
    git(r, "config", "user.email", "supervisor@example.invalid")
    git(r, "config", "core.autocrlf", "false")
    put(r / ".gitignore", "run/\ndocs/RUN_PARAMETERS.md\n")
    put(r / "a.py", "x = 0\n")
    (r / "run" / "review").mkdir(parents=True)
    for rel, text in (files or {}).items():
        put(r / rel, text)
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    if branch:
        git(r, "checkout", "-q", "-b", branch)
    return r


_bump = {"n": 0}


def bump(repo):
    """A commit that changes the tree."""
    _bump["n"] += 1
    put(repo / "a.py", "x = %d\n" % (_bump["n"] + 1000))
    git(repo, "commit", "-q", "-am", "change %d" % _bump["n"])


def stamp(offset=0):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() + offset))


def launched(repo, name, offset=1, exit_code=0):
    """run/review/REVIEW-<name>.err as the launcher leaves it: `bridge-run: started <UTC>Z`
    first, `bridge-run: exit <code>` last (None: no exit line)."""
    text = "bridge-run: started %sZ\nreviewer output\n" % stamp(offset)
    if exit_code is not None:
        text += "bridge-run: exit %d\n" % exit_code
    put(repo / "run" / "review" / ("REVIEW-%s.err" % name), text)


def snap_ok(repo, name):
    rc, out = guard(repo, "snapshot", name)
    assert rc == 0, out
    return out


def next_second():
    """Wait until the UTC clock's second changes. A round's `time` is kept to the second, and the
    branch rule takes the branch's first record by that time, so two snapshots in one second tie
    and their order is the bridge folder's listing order, which Linux does not keep alphabetical;
    a test that relies on which record came first takes its later snapshot in a later second."""
    start = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    while time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) == start:
        time.sleep(0.05)


def verify_ok(repo, name):
    rc, out = guard(repo, "verify", name)
    assert rc == 0 and "verified mark written" in out, out
    return out


def reviewed(repo, name, change=True):
    """A round opened and replied to: (a tree change,) snapshot, a Review B with exit 0 after it, verify OK."""
    if change:
        bump(repo)
    snap_ok(repo, name)
    launched(repo, name)
    verify_ok(repo, name)


def opened(repo, id_part, upto, start=1):
    """Rounds start..upto of id_part opened in order, each on a changed tree, no reply."""
    for n in range(start, upto + 1):
        bump(repo)
        snap_ok(repo, id_part if n == 1 else "%s-r%d" % (id_part, n))


_COMMON = {}


def bridge_dir(repo):
    """<git common dir>/bridge: for a linked worktree, the main checkout's .git/bridge."""
    key = str(repo)
    if key not in _COMMON:
        out = git(repo, "rev-parse", "--git-common-dir")
        _COMMON[key] = os.path.normpath(out if os.path.isabs(out) else os.path.join(key, out))
    return pathlib.Path(_COMMON[key]) / "bridge"


def rounds_file(repo, id_part):
    return bridge_dir(repo) / ("rounds-%s.json" % id_part)


def rounds(repo, id_part):
    with open(str(rounds_file(repo, id_part)), encoding="utf-8") as f:
        return json.load(f)


def entry(repo, id_part, n):
    hits = [r for r in rounds(repo, id_part)["rounds"] if r.get("round") == n]
    assert len(hits) == 1, rounds(repo, id_part)
    return hits[0]


def hash_dir():
    return os.environ["BRIDGE_REVIEW_HASHES"]


def hash_files():
    d = hash_dir()
    out = {}
    if os.path.isdir(d):
        for name in os.listdir(d):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                with open(p, "rb") as f:
                    out[name] = f.read()
    return out


def state(repo):
    """Every file under .git/bridge/ (bytes) and every file of the hash folder (bytes)."""
    files = {}
    d = bridge_dir(repo)
    if d.is_dir():
        for p in d.rglob("*"):
            if p.is_file():
                files[str(p.relative_to(d))] = p.read_bytes()
    return files, hash_files()


def assert_refused(rc, out, prefix, *names):
    assert rc == 125, (rc, out)
    assert "Traceback" not in out, out
    assert any(line.startswith(prefix) for line in out.splitlines()), (prefix, out)
    for n in names:
        assert n in out, (n, out)


def assert_nothing_written(before, repo):
    files_before, hashes_before = before
    files_after, hashes_after = state(repo)
    assert files_after == files_before, "the refusal wrote under .git/bridge/: %s" % sorted(set(files_after.items()) ^ set(files_before.items()))[:6]
    assert hashes_after == hashes_before, "the refusal wrote a hash copy: %s" % sorted(set(hashes_after) ^ set(hashes_before))


def refuse_and_nothing(repo, name, prefix, *names):
    before = state(repo)
    rc, out = guard(repo, "snapshot", name)
    assert_refused(rc, out, prefix, *names)
    assert_nothing_written(before, repo)
    return out


def new_hash_files(before):
    return sorted(set(hash_files()) - set(before))


def launcher_line(brief, branch, brief_bytes=b"brief\n", exit_code=0, round_n=1, brief_name=None,
                  merge_ids=None, offset=0, lift=None, lift_line=None):
    """One runs.jsonl line exactly as bridge-run.py builds and write_log writes it: the entry of
    main() (id, kind, head, model, branch, limit, seconds, exit, healthy), the brief fields,
    pid and child_pid, then the end's seconds, exit and healthy, dumped with json.dumps."""
    run_id = stamp(offset) + "Z"
    entry_ = {"id": run_id, "kind": "builder", "head": "cursor-agent", "model": None, "branch": branch,
              "limit": 7200, "seconds": None, "exit": None, "healthy": None}
    entry_.update(brief=brief, round=round_n, brief_sha256=hashlib.sha256(brief_bytes).hexdigest(),
                  brief_name=brief_name or brief, lift=lift, merge_ids=list(merge_ids or [brief]))
    if lift_line:
        entry_["lift_line"] = lift_line
    entry_.update(pid=4242, child_pid=4243)
    entry_.update(seconds=12, exit=exit_code, healthy=None)
    return json.dumps(entry_) + "\n"


def append_log(main_checkout, *lines):
    path = os.path.join(str(main_checkout), "run", "launcher", "runs.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "ab") as f:
        for line in lines:
            f.write(line if isinstance(line, bytes) else line.encode("utf-8"))


def old_snapshot(repo, name, branch_ref):
    """A snapshot file as the pre-TASK-032 `snapshot` wrote it (review-guard.py at cec417a,
    :354-363): no `round` field, the branch as `git symbolic-ref -q HEAD` gives it."""
    snap = {"nnn": name, "taken": "2026-10-20T10:00:00Z", "root": str(repo), "head": git(repo, "rev-parse", "HEAD"),
            "branch": branch_ref, "refs": {}, "stashes": [],
            "git": {"config": None, "hooks_path": None, "active_hooks": {}, "git_hooks": {}}, "ignored": {}}
    bridge_dir(repo).mkdir(parents=True, exist_ok=True)
    with open(str(bridge_dir(repo) / ("review-%s.json" % name)), "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=1, sort_keys=True)


def git_above(path):
    d = os.path.abspath(str(path))
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return True
        parent = os.path.dirname(d)
        if parent == d:
            return False
        d = parent


def to_main(repo, subject, back):
    """A commit on main with `subject` (a squash merge's), then back on branch `back`."""
    git(repo, "checkout", "-q", "main")
    put(repo / ("main-%d.txt" % (len(git(repo, "log", "--format=%H", "main").splitlines()))), subject + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", subject)
    git(repo, "checkout", "-q", back)


# --- clause (e): rounds 1 to 3, re-snapshots, the count -------------------------------------

def test_task032_guard_rounds_one_to_three_opened_in_order_and_recorded(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): rounds 1 to 3 opened in order;
    each round recorded in rounds-<ID>.json with round, name, branch (--abbrev-ref form), tree
    hash (HEAD^{tree}), time, lift and reply."""
    repo = make_repo(tmp_path)
    trees = {}
    for n, name in ((1, "TASK-001"), (2, "TASK-001-r2"), (3, "TASK-001-r3")):
        reviewed(repo, name)
        trees[n] = git(repo, "rev-parse", "HEAD^{tree}")
    data = rounds(repo, "TASK-001")
    assert sorted(r["round"] for r in data["rounds"]) == [1, 2, 3]
    for n, name in ((1, "TASK-001"), (2, "TASK-001-r2"), (3, "TASK-001-r3")):
        e = entry(repo, "TASK-001", n)
        assert e["name"] == name and e["branch"] == "task-001" and e["tree"] == trees[n], e
        assert e.get("time") and e.get("lift") is None and e.get("reply") == 0, e
        assert "seeded" not in e or not e["seeded"], e


def test_task032_guard_resnapshot_of_unreviewed_round_on_changed_tree_allowed(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a re-snapshot of an unreviewed
    round with a changed tree allowed (the relaunch of a failed launch: the Review B run ended
    with exit 1, so the round has no reply)."""
    repo = make_repo(tmp_path)
    snap_ok(repo, "TASK-001")
    launched(repo, "TASK-001", exit_code=1)
    verify_ok(repo, "TASK-001")
    bump(repo)
    snap_ok(repo, "TASK-001")
    assert [r["round"] for r in rounds(repo, "TASK-001")["rounds"]] == [1]


def test_task032_guard_reviewed_round_same_tree_allowed_changed_tree_refused(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): the sequence reply, re-snapshot
    on the same tree (allowed), snapshot of a changed tree under the same <N> refused at its last
    step with `round <N> is reviewed: write <ID>-r<N+1>`: the reply survives the re-snapshot."""
    repo = make_repo(tmp_path)
    reviewed(repo, "TASK-001")
    snap_ok(repo, "TASK-001")                                   # same tree: an APPROVE-shaped reply that read nothing
    assert entry(repo, "TASK-001", 1).get("reply") == 0, "the re-snapshot cleared the reply"
    bump(repo)
    refuse_and_nothing(repo, "TASK-001", REFUSED, "round 1 is reviewed: write TASK-001-r2")
    snap_ok(repo, "TASK-001-r2")


def test_task032_guard_n_off_the_count_refused_with_the_count(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): <N> off the count refused (with
    the count): above current + 1 (no round yet and -r2; one round and -r3) and below current
    (two rounds and TASK-001, round 1)."""
    repo = make_repo(tmp_path)
    refuse_and_nothing(repo, "TASK-001-r2", REFUSED, "0")
    snap_ok(repo, "TASK-001")
    bump(repo)
    refuse_and_nothing(repo, "TASK-001-r3", REFUSED, "1")
    snap_ok(repo, "TASK-001-r2")
    bump(repo)
    refuse_and_nothing(repo, "TASK-001", REFUSED, "2")


def test_task032_guard_r10_reviewed_round_three_resnapshot_same_tree_allowed(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R10: a reviewed round 3 re-snapshotted on the same
    tree is allowed (N == current, tree hash equal) and adds no round; N below current refused."""
    repo = make_repo(tmp_path)
    for name in ("TASK-001", "TASK-001-r2", "TASK-001-r3"):
        reviewed(repo, name)
    snap_ok(repo, "TASK-001-r3")
    assert sorted(r["round"] for r in rounds(repo, "TASK-001")["rounds"]) == [1, 2, 3]
    assert entry(repo, "TASK-001", 3).get("reply") == 0
    refuse_and_nothing(repo, "TASK-001-r2", REFUSED, "3")


# --- the ceiling and the lifts ----------------------------------------------------------------

def test_task032_guard_r8_fourth_round_refused_then_lifted_and_recorded_with_lift_line(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R8: the fourth round refused without the class line
    (`review-guard: refused - review ceiling: `, the ID named, nothing written) and allowed with
    it, the lift recorded on round 4 with lift `class` and lift_line the line's text."""
    repo = make_repo(tmp_path)
    opened(repo, "TASK-001", 3)
    bump(repo)
    refuse_and_nothing(repo, "TASK-001-r4", CEILING, "TASK-001")
    line = "Blocking class: security - the token is logged in clear"
    put(repo / "run" / "review" / "SCOPE-TASK-001.md", "# Scope of TASK-001\n\n" + line + "\n")
    snap_ok(repo, "TASK-001-r4")
    e = entry(repo, "TASK-001", 4)
    assert e.get("lift") == "class" and e.get("lift_line") == line, e


def test_task032_guard_r8_resnapshot_of_lifted_round_reuses_its_lift(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R8: a re-snapshot of an already-lifted round reuses
    its recorded lift and needs no new line (R10: a re-snapshot reuses the round's recorded lift),
    here with the SCOPE file's class line removed after round 4 was opened."""
    repo = make_repo(tmp_path)
    opened(repo, "TASK-001", 3)
    line = "Blocking class: behaviour - the guard counts the wrong branch"
    put(repo / "run" / "review" / "SCOPE-TASK-001.md", line + "\n")
    bump(repo)
    snap_ok(repo, "TASK-001-r4")
    os.remove(str(repo / "run" / "review" / "SCOPE-TASK-001.md"))
    rc, out = guard(repo, "snapshot", "TASK-001-r4")
    assert rc == 0, "a re-snapshot of the lifted round 4 must reuse its lift: " + out
    e = entry(repo, "TASK-001", 4)
    assert e.get("lift") == "class" and e.get("lift_line") == line, e


def test_task032_guard_r8_repeated_class_line_refused_and_replacing_line_allowed(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R8: the same class line refuses a fifth round (the
    text is recorded on round 4; a class line lifts one round; exit 125, nothing written), and the
    next round's line, replacing it, allows it, recorded with its own lift_line. Last, the
    refusal's line: a round above the ceiling that no line lifts is the ceiling's refusal, whose
    message begins `review-guard: refused - review ceiling: ` (clause (c))."""
    repo = make_repo(tmp_path)
    opened(repo, "TASK-001", 3)
    first = "Blocking class: security - the token is logged in clear"
    put(repo / "run" / "review" / "SCOPE-TASK-001.md", first + "\n")
    bump(repo)
    snap_ok(repo, "TASK-001-r4")
    bump(repo)
    out = refuse_and_nothing(repo, "TASK-001-r5", REFUSED, "TASK-001")
    second = "Blocking class: data integrity - the record loses a round on restart"
    put(repo / "run" / "review" / "SCOPE-TASK-001.md", second + "\n")
    snap_ok(repo, "TASK-001-r5")
    assert entry(repo, "TASK-001", 4).get("lift_line") == first
    e = entry(repo, "TASK-001", 5)
    assert e.get("lift") == "class" and e.get("lift_line") == second, e
    assert any(line.startswith(CEILING) for line in out.splitlines()), "the repeat refusal is not the ceiling's line: " + out


@pytest.mark.parametrize("bad", [
    "Blocking class: Behaviour - capitalised class",
    "Blocking class: SECURITY - upper-case class",
    "Blocking class: performance - a sixth word",
    "Blocking class: security - ",
    "Blocking class: security",
])
def test_task032_guard_malformed_class_line_lifts_nothing(tmp_path, bad):
    """R-042. enforces: handoff/TASK-032-r2.md R19: the class is matched exactly, in lower case as
    written in the five; a sixth word, a capitalised class or an empty finding lifts nothing, so
    the fourth round stays refused at the ceiling."""
    repo = make_repo(tmp_path)
    opened(repo, "TASK-001", 3)
    put(repo / "run" / "review" / "SCOPE-TASK-001.md", bad + "\n")
    bump(repo)
    refuse_and_nothing(repo, "TASK-001-r4", CEILING, "TASK-001")


def test_task032_guard_r9_owner_line_lifts_to_its_rounds_first_line_stands(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R9: the owner's line lifts to its <rounds> (rounds
    4 and 5 allowed, 6 refused at the ceiling), a second line for the same ID ignored, and the
    lift recorded as `owner` with the matched line's text."""
    repo = make_repo(tmp_path)
    first = "Review rounds above the ceiling: TASK-001 5 (I allow five for this one, 2026-10-28)"
    later = "Review rounds above the ceiling: TASK-001 9 (a later line, 2026-10-28)"
    put(repo / "docs" / "RUN_PARAMETERS.md", "# Run parameters\n\n" + first + "\n" + later + "\n")
    opened(repo, "TASK-001", 3)
    bump(repo)
    snap_ok(repo, "TASK-001-r4")
    e = entry(repo, "TASK-001", 4)
    assert e.get("lift") == "owner" and e.get("lift_line") == first, e
    bump(repo)
    snap_ok(repo, "TASK-001-r5")
    bump(repo)
    refuse_and_nothing(repo, "TASK-001-r6", CEILING, "TASK-001")


def test_task032_guard_r17_non_utf8_run_parameters_still_read(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R17: a non-UTF-8 byte in docs/RUN_PARAMETERS.md is
    read with replacement, never a traceback, and the owner's line beside it still lifts."""
    repo = make_repo(tmp_path)
    line = b"Review rounds above the ceiling: TASK-001 4 (four, 2026-10-28)"
    put(repo / "docs" / "RUN_PARAMETERS.md", b"# Run parameters \xff\xfe caf\xe9\n" + line + b"\n")
    opened(repo, "TASK-001", 3)
    bump(repo)
    rc, out = guard(repo, "snapshot", "TASK-001-r4")
    assert rc == 0 and "Traceback" not in out, out
    assert entry(repo, "TASK-001", 4).get("lift") == "owner"


def test_task032_guard_stage_name_counted_under_stage_id(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): `STAGE-<name>-r<N>` counted:
    STAGE-B5 and STAGE-B5-r2 are rounds 1 and 2 of STAGE-B5 on stage/B5; the fourth round
    refused without and allowed with the class line in SCOPE-STAGE-B5.md."""
    repo = make_repo(tmp_path, branch="stage/B5")
    opened(repo, "STAGE-B5", 3)
    data = rounds(repo, "STAGE-B5")
    assert [(r["round"], r["name"], r["branch"]) for r in sorted(data["rounds"], key=lambda r: r["round"])] == [
        (1, "STAGE-B5", "stage/B5"), (2, "STAGE-B5-r2", "stage/B5"), (3, "STAGE-B5-r3", "stage/B5")]
    bump(repo)
    refuse_and_nothing(repo, "STAGE-B5-r4", CEILING, "STAGE-B5")
    put(repo / "run" / "review" / "SCOPE-STAGE-B5.md", "Blocking class: failing test - the stage suite fails on Windows\n")
    snap_ok(repo, "STAGE-B5-r4")


# --- the branch rule -----------------------------------------------------------------------

def test_task032_guard_r5_other_id_refused_until_merged_on_main_then_claimed_afresh(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R5: a snapshot under another ID on a counted branch
    refused with the counted IDs (a renamed TASK-010b too), still refused after a commit on main
    that merges another ID, allowed once a commit on main merges the counted ID; then (R3) that
    snapshot claims the branch afresh and a third ID is refused naming it."""
    repo = make_repo(tmp_path, branch="task-010", files={"handoff/TASK-010.md": "# TASK-010\n"})
    snap_ok(repo, "TASK-010")
    refuse_and_nothing(repo, "TASK-011", REFUSED, "TASK-010")
    refuse_and_nothing(repo, "TASK-010b", REFUSED, "TASK-010")
    to_main(repo, "TASK-009: another increment (#4)", "task-010")
    refuse_and_nothing(repo, "TASK-011", REFUSED, "TASK-010")
    to_main(repo, "TASK-010: the increment (#5)", "task-010")
    snap_ok(repo, "TASK-011")
    refuse_and_nothing(repo, "TASK-012", REFUSED, "TASK-011")


def test_task032_guard_launcher_line_refuses_snapshot_of_other_id(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a launch of one ID (the launcher's
    record, a runs.jsonl line naming the branch) refusing a snapshot of another, the counted ID
    named; the launched ID's own snapshot allowed."""
    repo = make_repo(tmp_path, branch="task-010", files={"handoff/TASK-010.md": "# TASK-010\n"})
    append_log(repo, launcher_line("TASK-010", "task-010", (repo / "handoff" / "TASK-010.md").read_bytes()))
    refuse_and_nothing(repo, "TASK-011", REFUSED, "TASK-010")
    snap_ok(repo, "TASK-010")


def test_task032_guard_r1_reads_launcher_log_from_main_checkout(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R1: in a linked worktree, the guard reads the
    launcher's log from the main checkout (the parent of the common dir): a line there naming
    the worktree's branch refuses a snapshot of another ID in the worktree."""
    repo = make_repo(tmp_path, branch=None, files={"handoff/TASK-010.md": "# TASK-010\n"})
    wt = tmp_path / "Worktrees" / "TASK-010"
    git(repo, "worktree", "add", "-q", "-b", "task-010", str(wt))
    append_log(repo, launcher_line("TASK-010", "task-010", (repo / "handoff" / "TASK-010.md").read_bytes()))
    refuse_and_nothing(wt, "TASK-011", REFUSED, "TASK-010")
    snap_ok(wt, "TASK-010")


def test_task032_guard_r1_ignores_a_log_in_the_worktree_root(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R1: the launcher's log is read from the main
    checkout, not the worktree root: a runs.jsonl line found only under the worktree's own run/
    claims nothing, so a snapshot of another ID there is allowed."""
    repo = make_repo(tmp_path, branch=None)
    wt = tmp_path / "Worktrees" / "TASK-020"
    git(repo, "worktree", "add", "-q", "-b", "task-020", str(wt))
    append_log(wt, launcher_line("TASK-020", "task-020"))
    rc, out = guard(wt, "snapshot", "TASK-021")
    assert rc == 0, "a log under the worktree root is not the launcher's: " + out


def test_task032_guard_r3_earliest_event_declares_the_set(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R3: both records are read as one list in time
    order: the guard's TASK-010 round precedes a later launcher line of TASK-020 on the same
    branch, so the branch's set is TASK-010's: a TASK-020 snapshot is refused naming TASK-010."""
    repo = make_repo(tmp_path, branch="task-010")
    snap_ok(repo, "TASK-010")
    append_log(repo, launcher_line("TASK-020", "task-010", offset=5))
    refuse_and_nothing(repo, "TASK-020", REFUSED, "TASK-010")


def _unit_repo(tmp_path):
    plan = "# Build plan\n\n### TASK-010: the first\n\n### TASK-015 - the second\n\n### TASK-016: the third\n\n### TASK-017: the fourth\n\n### Notes\n"
    return make_repo(tmp_path, branch="task-010", files={
        "handoff/TASK-010.md": "# TASK-010\n\nMerge unit: TASK-010 TASK-015\n",
        "handoff/TASK-015.md": "# TASK-015\n",
        "docs/BUILD_PLAN.md": plan,
    })


def test_task032_guard_r4_merge_unit_from_first_brief_without_launcher_line(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R4: with no launcher line, the guard reads the
    declared set from the branch's first brief (handoff/TASK-010.md, `Merge unit: TASK-010
    TASK-015`): with SCOPE-TASK-010.md present and holding no merge line, snapshots of TASK-010
    and TASK-015 on that branch are both allowed, each counted under its own ID."""
    repo = _unit_repo(tmp_path)
    put(repo / "run" / "review" / "SCOPE-TASK-010.md", "# Scope of TASK-010\n\nThe files of the increment.\n")
    snap_ok(repo, "TASK-010")
    rc, out = guard(repo, "snapshot", "TASK-015")
    assert rc == 0, "TASK-015 is in the branch's declared set (the first brief's Merge unit line): " + out
    assert rounds_file(repo, "TASK-010").exists() and rounds_file(repo, "TASK-015").exists()


def test_task032_guard_r4_third_id_class_line_refused_owner_line_allowed_set_unchanged(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): with a two-ID merge unit declared,
    a third ID is refused under a class line (no reviewer confirms it below the ceiling) and
    allowed under the owner's line naming it, the declared set unchanged (a fourth ID still
    refused, the counted IDs TASK-010 and TASK-015 named)."""
    repo = _unit_repo(tmp_path)
    snap_ok(repo, "TASK-010")
    put(repo / "run" / "review" / "SCOPE-TASK-016.md", "Blocking class: security - the third increment's finding\n")
    refuse_and_nothing(repo, "TASK-016", REFUSED, "TASK-010")
    put(repo / "docs" / "RUN_PARAMETERS.md", "Review rounds above the ceiling: TASK-016 4 (allow it on this branch, 2026-10-28)\n")
    next_second()
    snap_ok(repo, "TASK-016")
    refuse_and_nothing(repo, "TASK-017", REFUSED, "TASK-010", "TASK-015")


def test_task032_guard_r4_increment_scope_file_never_supplies_the_set(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R4: an increment's own SCOPE file never supplies
    the set: TASK-010 has a brief with no Merge unit line, so `Merge unit: TASK-010 TASK-015` in
    run/review/SCOPE-TASK-010.md is not read, and a TASK-015 snapshot on that branch is refused."""
    repo = make_repo(tmp_path, branch="task-010", files={
        "handoff/TASK-010.md": "# TASK-010\n",
        "docs/BUILD_PLAN.md": "### TASK-010: one\n\n### TASK-015: two\n"})
    put(repo / "run" / "review" / "SCOPE-TASK-010.md", "Merge unit: TASK-010 TASK-015\n")
    snap_ok(repo, "TASK-010")
    refuse_and_nothing(repo, "TASK-015", REFUSED, "TASK-010")


def test_task032_guard_records_subject_counted_under_its_own_id(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a records subject with no brief
    (B3-CLOSE) is allowed and counted under its own ID (rounds-B3-CLOSE.json), and an ID outside
    it on that branch is refused."""
    repo = make_repo(tmp_path, branch="b3-close")
    snap_ok(repo, "B3-CLOSE")
    bump(repo)
    snap_ok(repo, "B3-CLOSE-r2")
    assert sorted(r["round"] for r in rounds(repo, "B3-CLOSE")["rounds"]) == [1, 2]
    refuse_and_nothing(repo, "B3-OTHER", REFUSED, "B3-CLOSE")


def test_task032_guard_r4_records_subject_scope_merge_unit_supplies_set(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R4: for a records subject with no brief, the set
    is the `Merge unit:` line of its run/review/SCOPE-<ID>.md: `Merge unit: B3-CLOSE TASK-040`
    lets TASK-040 be snapshotted on b3-close, while TASK-041 is refused."""
    repo = make_repo(tmp_path, branch="b3-close", files={"docs/BUILD_PLAN.md": "### TASK-040: the stage's last\n\n### TASK-041: another\n"})
    put(repo / "run" / "review" / "SCOPE-B3-CLOSE.md", "# Records close of B3\n\nMerge unit: B3-CLOSE TASK-040\n")
    snap_ok(repo, "B3-CLOSE")
    next_second()
    rc, out = guard(repo, "snapshot", "TASK-040")
    assert rc == 0, "the records subject's SCOPE Merge unit line declares TASK-040: " + out
    refuse_and_nothing(repo, "TASK-041", REFUSED, "B3-CLOSE")


@pytest.mark.parametrize("shape", [
    {"branch": ["task-001"]},
    {"merge_ids": 5},
    {"round": [1]},
    {"round": "2"},
    {"exit": True},
])
def test_task032_guard_r17_malformed_launcher_line_skipped(tmp_path, shape):
    """R-042. enforces: handoff/TASK-032-r2.md R17: a launcher line that fails a type check
    (branch a list, merge_ids 5, round [1] or "2", exit a bool) is skipped, never a traceback; an
    old line without `brief` claims nothing; a line with a non-UTF-8 byte is read without error.
    None of them claims task-001 for TASK-050, so the TASK-001 snapshot is allowed."""
    repo = make_repo(tmp_path)
    old = {"id": stamp(-60) + "Z", "kind": "builder", "head": "cursor-agent", "model": None, "branch": "task-001",
           "limit": 7200, "seconds": 3, "exit": 0, "healthy": None}
    bad = json.loads(launcher_line("TASK-050", "task-001", offset=-30))
    bad.update(shape)
    raw = launcher_line("TASK-060", "other-branch", offset=-20).replace("cursor-agent", "cursor-agent \\u00e9").encode("utf-8")
    raw = raw.replace(b"\\u00e9", b"\xff\xfe")
    append_log(repo, json.dumps(old) + "\n", json.dumps(bad) + "\n", raw, "not json at all\n")
    rc, out = guard(repo, "snapshot", "TASK-001")
    assert rc == 0 and "Traceback" not in out, out


# --- DESIGN-, main, detached, outside git ----------------------------------------------------

def test_task032_guard_design_name_not_counted(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a `DESIGN-` name is not counted:
    it writes no rounds file and claims no branch (a TASK-001 snapshot on the branch is allowed
    after it)."""
    repo = make_repo(tmp_path)
    snap_ok(repo, "DESIGN-plan-1")
    assert not list(bridge_dir(repo).glob("rounds-*.json")), list(bridge_dir(repo).iterdir())
    snap_ok(repo, "DESIGN-plan-1")
    snap_ok(repo, "TASK-001")


def test_task032_guard_r15_snapshot_on_main_refused_design_exempt(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R15: a counted snapshot on main is refused with
    exit 125 and `review-guard: refused - branch rule: reviews run on a branch, not main`,
    nothing written; a DESIGN- name is exempt and snapshots on main."""
    repo = make_repo(tmp_path, branch=None)
    refuse_and_nothing(repo, "TASK-001", BRANCH_RULE_NOT + "main")
    snap_ok(repo, "DESIGN-plan-1")


def test_task032_guard_r15_snapshot_on_detached_head_refused(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R15: a counted snapshot on a detached HEAD is
    refused with exit 125 and `... branch rule: reviews run on a branch, not a detached HEAD`,
    nothing written."""
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "--detach")
    refuse_and_nothing(repo, "TASK-001", BRANCH_RULE_NOT + "a detached HEAD")


def test_task032_guard_r15_snapshot_outside_git_refused(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R15: a counted snapshot in a folder outside git is
    refused with exit 125 and `... branch rule: reviews run on a branch, not a folder outside
    git`, and writes nothing to the hash folder."""
    folder = tmp_path / "plain"
    folder.mkdir()
    if git_above(folder):
        pytest.skip("the temporary folder lies inside a git checkout here, so no folder outside git can be made")
    before = hash_files()
    rc, out = guard(folder, "snapshot", "TASK-001")
    assert_refused(rc, out, BRANCH_RULE_NOT + "a folder outside git")
    assert hash_files() == before
    assert not (folder / ".git").exists()


# --- names (R19) ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["TASK-001-r0", "TASK-001-r05", "TASK-001-R2", "TASK 001", "task-001",
                                  "TASK-001\n", "TASK-001-r2\n", "TASK-001-r2-r3", "design-plan-1"])
def test_task032_guard_r19_unreadable_name_refused(tmp_path, name):
    """R-042. enforces: handoff/TASK-032-r2.md R19: a name the grammar cannot read is refused by
    snapshot with exit 125, nothing written: -r0, -r05, -R2, a space, a lower-case start, a
    trailing newline (fullmatch), a second -r part, and `design-` (DESIGN- matched
    case-sensitively, so design-plan-1 is read by the grammar and refused)."""
    repo = make_repo(tmp_path)
    refuse_and_nothing(repo, name, REFUSED)


@pytest.mark.parametrize("name,id_part", [("TASK-010c", "TASK-010c"), ("CONFIG-B3b", "CONFIG-B3b"),
                                          ("HOTFIX-001", "HOTFIX-001"), ("B3-CLOSE", "B3-CLOSE"),
                                          ("Design-plan", "Design-plan")])
def test_task032_guard_r19_readable_names_counted(tmp_path, name, id_part):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (c): every name other than a DESIGN- one
    is read by the grammar and counted: TASK-010c, CONFIG-B3b, HOTFIX-001, B3-CLOSE and
    `Design-plan` (not `DESIGN-`, case-sensitive) each open round 1 in rounds-<ID>.json."""
    repo = make_repo(tmp_path, branch="work")
    snap_ok(repo, name)
    assert [r["round"] for r in rounds(repo, id_part)["rounds"]] == [1]


def test_task032_guard_verify_and_premerge_under_full_name(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): verify and premerge under the full
    name (`TASK-001-r2`: its snapshot, its .err file, its verified mark), and both refuse a name
    the grammar cannot read with 125 (a trailing newline, -R2, -r05)."""
    repo = make_repo(tmp_path)
    reviewed(repo, "TASK-001")
    bump(repo)
    snap_ok(repo, "TASK-001-r2")
    launched(repo, "TASK-001-r2")
    verify_ok(repo, "TASK-001-r2")
    assert (bridge_dir(repo) / "verified-TASK-001-r2.json").exists()
    rc, out = guard(repo, "premerge", "TASK-001-r2")
    assert rc == 0 and "verified mark for TASK-001-r2" in out, out
    for cmd, bad in (("verify", "TASK-001-r2\n"), ("premerge", "TASK-001-R2"), ("verify", "TASK-001-r05"), ("premerge", "TASK-001\n")):
        before = state(repo)
        rc, out = guard(repo, cmd, bad)
        assert_refused(rc, out, REFUSED)
        assert_nothing_written(before, repo)


# --- refused snapshots write nothing ------------------------------------------------------

def test_task032_guard_refused_snapshot_writes_nothing_beside_accepted_one(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (e): a refused snapshot writing nothing
    (no rounds file change, no review-<name>.json, no hash copy), shown beside the same repository
    writing all three on an accepted snapshot."""
    repo = make_repo(tmp_path)
    before_hashes = hash_files()
    snap_ok(repo, "TASK-001")
    assert rounds_file(repo, "TASK-001").exists() and (bridge_dir(repo) / "review-TASK-001.json").exists()
    added = new_hash_files(before_hashes)
    assert any(n.endswith("-TASK-001.sha256") and "rounds" not in n for n in added), added
    assert any("rounds" in n and "TASK-001" in n for n in added), "no hash copy of the rounds record (R13): %s" % added
    bump(repo)
    refuse_and_nothing(repo, "TASK-001-r3", REFUSED, "1")
    assert not (bridge_dir(repo) / "review-TASK-001-r3.json").exists()


# --- replies (R11), the tree (R12), marks (R22) -------------------------------------------------

def test_task032_guard_r11_only_exit_0_is_a_reply(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R11: a Review B run with exit 1 is no reply: verify
    leaves the round's reply unset, so a re-snapshot of round 1 on a changed tree is allowed."""
    repo = make_repo(tmp_path)
    snap_ok(repo, "TASK-001")
    launched(repo, "TASK-001", exit_code=1)
    verify_ok(repo, "TASK-001")
    assert entry(repo, "TASK-001", 1).get("reply") is None, entry(repo, "TASK-001", 1)
    bump(repo)
    snap_ok(repo, "TASK-001")


def test_task032_guard_r11_reply_never_cleared_by_later_verify(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R11: a recorded reply (exit 0) is never cleared or
    overwritten by a later verify of a run with a non-zero exit or with no exit line, and the
    record survives every verify; the reply still spends the round (a changed tree under the
    same <N> refused)."""
    repo = make_repo(tmp_path)
    snap_ok(repo, "TASK-001")
    launched(repo, "TASK-001", offset=1, exit_code=0)
    verify_ok(repo, "TASK-001")
    assert entry(repo, "TASK-001", 1).get("reply") == 0
    launched(repo, "TASK-001", offset=2, exit_code=3)
    verify_ok(repo, "TASK-001")
    assert entry(repo, "TASK-001", 1).get("reply") == 0, entry(repo, "TASK-001", 1)
    launched(repo, "TASK-001", offset=3, exit_code=None)
    guard(repo, "verify", "TASK-001")
    assert entry(repo, "TASK-001", 1).get("reply") == 0, entry(repo, "TASK-001", 1)
    bump(repo)
    refuse_and_nothing(repo, "TASK-001", REFUSED, "round 1 is reviewed: write TASK-001-r2")


def test_task032_guard_r11_launch_before_snapshot_not_recorded(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R11: a Review B run whose .err launch time precedes
    the round's snapshot is no reply of that round: verify records nothing."""
    repo = make_repo(tmp_path)
    launched(repo, "TASK-001", offset=-120, exit_code=0)
    snap_ok(repo, "TASK-001")
    guard(repo, "verify", "TASK-001")
    assert entry(repo, "TASK-001", 1).get("reply") is None, entry(repo, "TASK-001", 1)


def test_task032_guard_r11_gate_integrity_records_no_reply(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R11: a verify that ends GATE-INTEGRITY records no
    reply (a flagged review spends no round), even with a Review B run with exit 0 after the
    snapshot."""
    repo = make_repo(tmp_path)
    snap_ok(repo, "TASK-001")
    launched(repo, "TASK-001")
    git(repo, "branch", "left-by-the-reviewer")
    rc, out = guard(repo, "verify", "TASK-001")
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    assert entry(repo, "TASK-001", 1).get("reply") is None, entry(repo, "TASK-001", 1)


def test_task032_guard_r11_verify_never_creates_missing_rounds_file(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R11: verify never creates a rounds file that is
    missing: a snapshot without a `round` field (as an older release wrote it, its hash copy
    consistent) and no rounds-<ID>.json; a verify reading a reply with exit 0 writes no rounds
    file."""
    repo = make_repo(tmp_path)
    before = hash_files()
    snap_ok(repo, "TASK-001")
    added = new_hash_files(before)
    snap_copy = [n for n in added if n.endswith("-TASK-001.sha256") and "rounds" not in n]
    assert len(snap_copy) == 1, added
    p = bridge_dir(repo) / "review-TASK-001.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data.pop("round", None)
    with open(str(p), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    with open(os.path.join(hash_dir(), snap_copy[0]), "w", encoding="utf-8") as f:
        f.write(hashlib.sha256(p.read_bytes()).hexdigest() + "\n")
    os.remove(str(rounds_file(repo, "TASK-001")))
    for n in added:
        if n not in snap_copy:
            os.remove(os.path.join(hash_dir(), n))
    launched(repo, "TASK-001")
    rc, out = guard(repo, "verify", "TASK-001")
    assert rc == 0, out
    assert not rounds_file(repo, "TASK-001").exists(), "verify created the missing rounds record"


def test_task032_guard_r12_tree_hash_and_snapshot_round_field(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R12: the record's tree is `git rev-parse
    HEAD^{tree}`, not the commit; a records-only empty re-commit keeps the same tree, so the
    reviewed round re-snapshots; the snapshot file carries the `round` field (1, then 2)."""
    repo = make_repo(tmp_path)
    reviewed(repo, "TASK-001")
    e = entry(repo, "TASK-001", 1)
    assert e["tree"] == git(repo, "rev-parse", "HEAD^{tree}") and e["tree"] != git(repo, "rev-parse", "HEAD"), e
    git(repo, "commit", "-q", "--allow-empty", "-m", "records only")
    snap_ok(repo, "TASK-001")
    assert entry(repo, "TASK-001", 1)["tree"] == e["tree"]
    assert json.loads((bridge_dir(repo) / "review-TASK-001.json").read_text(encoding="utf-8")).get("round") == 1
    bump(repo)
    snap_ok(repo, "TASK-001-r2")
    assert json.loads((bridge_dir(repo) / "review-TASK-001-r2.json").read_text(encoding="utf-8")).get("round") == 2


def test_task032_guard_r22_one_verified_mark_of_an_id_live(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R22: `snapshot <ID>-r<N>` removes verified-<ID>.json
    and every verified-<ID>-r<k>.json, so one verified mark of an ID is live: premerge of the
    earlier round's name is refused after the next snapshot."""
    repo = make_repo(tmp_path)
    reviewed(repo, "TASK-001")
    assert (bridge_dir(repo) / "verified-TASK-001.json").exists()
    bump(repo)
    snap_ok(repo, "TASK-001-r2")
    assert not (bridge_dir(repo) / "verified-TASK-001.json").exists()
    rc, out = guard(repo, "premerge", "TASK-001")
    assert rc == 2 and "no verified mark" in out, out
    launched(repo, "TASK-001-r2")
    verify_ok(repo, "TASK-001-r2")
    bump(repo)
    snap_ok(repo, "TASK-001-r3")
    assert not (bridge_dir(repo) / "verified-TASK-001-r2.json").exists()
    assert not list(bridge_dir(repo).glob("verified-TASK-001*.json"))


# --- the record's integrity (R13) and shapes (R17) ---------------------------------------------

def test_task032_guard_r13_hand_edit_of_rounds_file_refused(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R13: a hand edit of rounds-<ID>.json (its rounds
    emptied to reset the count) is refused with exit 125 and `review-guard: refused - rounds
    record changed outside the guard: <ID>`, nothing written."""
    repo = make_repo(tmp_path)
    snap_ok(repo, "TASK-001")
    bump(repo)
    snap_ok(repo, "TASK-001-r2")
    data = rounds(repo, "TASK-001")
    data["rounds"] = []
    with open(str(rounds_file(repo, "TASK-001")), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    bump(repo)
    refuse_and_nothing(repo, "TASK-001", TAMPER + "TASK-001")


def test_task032_guard_r13_hash_copy_beside_deleted_rounds_file_refused(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R13: the hash copy present beside a deleted rounds
    file refuses (exit 125, `... rounds record changed outside the guard: <ID>`), even with the
    snapshot and mark files gone too, so a deletion cannot reset the count."""
    repo = make_repo(tmp_path)
    snap_ok(repo, "TASK-001")
    bump(repo)
    snap_ok(repo, "TASK-001-r2")
    for p in list(bridge_dir(repo).glob("review-TASK-001*.json")) + list(bridge_dir(repo).glob("verified-*.json")):
        os.remove(str(p))
    os.remove(str(rounds_file(repo, "TASK-001")))
    refuse_and_nothing(repo, "TASK-001", TAMPER + "TASK-001")


def test_task032_guard_r13_missing_copy_seeded_once(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R13: a missing hash copy beside a present rounds
    file is seeded once (the release's first run): the snapshot is accepted and the copy exists
    again, after which a hand edit is refused."""
    repo = make_repo(tmp_path)
    before = hash_files()
    snap_ok(repo, "TASK-001")
    copies = [n for n in new_hash_files(before) if "rounds" in n and "TASK-001" in n]
    assert len(copies) == 1, new_hash_files(before)
    os.remove(os.path.join(hash_dir(), copies[0]))
    bump(repo)
    snap_ok(repo, "TASK-001-r2")
    assert os.path.isfile(os.path.join(hash_dir(), copies[0]))
    with open(str(rounds_file(repo, "TASK-001")), "a", encoding="utf-8") as f:
        f.write("\n")
    bump(repo)
    refuse_and_nothing(repo, "TASK-001-r3", TAMPER + "TASK-001")


WRAP = r'''
import json, os, runpy, sys
prog, log_path, mode = sys.argv[1], sys.argv[2], sys.argv[3]
real = os.replace
calls = []
def spy(src, dst):
    calls.append([os.fspath(src), os.fspath(dst)])
    if mode == "fail" and os.path.basename(os.fspath(dst)).startswith("rounds-"):
        raise OSError("simulated failure of the move into place")
    return real(src, dst)
os.replace = spy
sys.argv = [prog] + sys.argv[4:]
try:
    runpy.run_path(prog, run_name="__main__")
finally:
    with open(log_path, "w") as f:
        json.dump(calls, f)
'''


def test_task032_guard_r13_rounds_record_written_atomically_and_survives_verify(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R13: the record is written to a temporary file in
    the same folder and moved into place with os.replace (the program run as __main__ with
    os.replace observed); the record survives verify; when the move of a later write fails, the
    record on disk is the old one, whole, and no temporary file is left."""
    wrap = tmp_path / "wrap.py"
    put(wrap, WRAP)
    repo = make_repo(tmp_path)
    log = tmp_path / "calls.json"

    def run(mode, *args):
        p = subprocess.run([sys.executable, str(wrap), PROG, str(log), mode] + list(args), cwd=str(repo), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env=env(), timeout=TIMEOUT)
        with open(str(log), encoding="utf-8") as f:
            return p.returncode, p.stdout + p.stderr, json.load(f)

    rc, out, calls = run("ok", "snapshot", "TASK-001")
    assert rc == 0, out
    target = os.path.normcase(os.path.abspath(str(rounds_file(repo, "TASK-001"))))
    moves = [(s, d) for s, d in calls if os.path.normcase(os.path.abspath(d)) == target]
    assert moves, "rounds-TASK-001.json was not moved into place with os.replace: %s" % calls
    assert os.path.normcase(os.path.dirname(os.path.abspath(moves[-1][0]))) == os.path.dirname(target)
    launched(repo, "TASK-001")
    verify_ok(repo, "TASK-001")
    assert entry(repo, "TASK-001", 1).get("reply") == 0, "the record did not survive verify"
    record = rounds_file(repo, "TASK-001").read_bytes()
    bump(repo)
    rc, out, calls = run("fail", "snapshot", "TASK-001-r2")
    assert rc != 0 and "Traceback" not in out, out
    assert rounds_file(repo, "TASK-001").read_bytes() == record, "a failed move changed the record on disk"
    left = sorted(p.name for p in bridge_dir(repo).iterdir() if p.is_file()
                  and not (p.name.endswith(".json") and p.name.split("-", 1)[0] in ("review", "verified", "rounds")))
    assert left == [], "a failed move left files behind: %s" % left


@pytest.mark.parametrize("label,payload", [
    ("rounds a dict", {"id": "TASK-001", "rounds": {"round": 1}}),
    ("rounds a string", {"id": "TASK-001", "rounds": "1"}),
    ("rounds of non-dicts", {"id": "TASK-001", "rounds": [1, 2]}),
    ("round a list", {"id": "TASK-001", "rounds": [{"round": [1], "name": "TASK-001"}]}),
    ("round a string", {"id": "TASK-001", "rounds": [{"round": "2", "name": "TASK-001-r2"}]}),
    ("round a bool", {"id": "TASK-001", "rounds": [{"round": True, "name": "TASK-001"}]}),
    ("mixed types", {"id": "TASK-001", "rounds": [{"round": 1, "name": "TASK-001"}, "x", {"round": None}]}),
    ("top level a list", [{"round": 1}]),
    ("not json", None),
    ("non-UTF-8", b'{"id": "TASK-001", "rounds": [{"round": 1, "name": "\xff\xfe"}], "x": \xff}'),
])
def test_task032_guard_r17_malformed_rounds_file_refused_without_traceback(tmp_path, label, payload):
    """R-042. enforces: handoff/TASK-032-r2.md R17: a rounds file that fails a type check (rounds
    a dict, a string or a list of non-dicts; round [1], "2" or a bool; mixed types; not an object;
    not JSON; non-UTF-8 bytes), its hash copy kept consistent so the shape itself is read, refuses
    the next snapshot with exit 125, a named message and no traceback, nothing written."""
    repo = make_repo(tmp_path)
    before = hash_files()
    snap_ok(repo, "TASK-001")
    copies = [n for n in new_hash_files(before) if "rounds" in n and "TASK-001" in n]
    if payload is None:
        raw = b"{ this is not json"
    elif isinstance(payload, bytes):
        raw = payload
    else:
        raw = json.dumps(payload).encode("utf-8")
    with open(str(rounds_file(repo, "TASK-001")), "wb") as f:
        f.write(raw)
    for n in copies:                                              # keep R13's copy consistent: the shape is what is tested
        with open(os.path.join(hash_dir(), n), "w", encoding="utf-8") as f:
            f.write(hashlib.sha256(raw).hexdigest() + "\n")
    bump(repo)
    refuse_and_nothing(repo, "TASK-001-r2", REFUSED, "TASK-001")


# --- seeding (R14, Missing item 1) -------------------------------------------------------------

def test_task032_guard_r14_missing_rounds_beside_snapshot_with_round_refused(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R14: a missing rounds-<ID>.json beside a present
    review-<ID>.json that carries a `round` field is refused (exit 125, the ID named), the hash
    copy of the record removed as well so the refusal is the seeding rule's; nothing written."""
    repo = make_repo(tmp_path)
    before = hash_files()
    snap_ok(repo, "TASK-001")
    for n in new_hash_files(before):
        if "rounds" in n:
            os.remove(os.path.join(hash_dir(), n))
    os.remove(str(rounds_file(repo, "TASK-001")))
    bump(repo)
    refuse_and_nothing(repo, "TASK-001-r2", REFUSED, "TASK-001")
    assert not rounds_file(repo, "TASK-001").exists()


def test_task032_guard_r14_four_letter_snapshots_seed_four_rounds(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R14: four letter snapshots (review-TASK-010.json,
    -010a, -010b, -010c, no rounds field, branch stored as refs/heads/task-010; TASK-010 has a
    brief, the letters none) seed four rounds marked seeded with reply 0, so the next <N> is 5:
    refused at the ceiling without a lift, allowed with the class line."""
    repo = make_repo(tmp_path, branch="task-010", files={"handoff/TASK-010.md": "# TASK-010\n"})
    for name in ("TASK-010", "TASK-010a", "TASK-010b", "TASK-010c"):
        old_snapshot(repo, name, "refs/heads/task-010")
    bump(repo)
    rc, out = guard(repo, "snapshot", "TASK-010-r5")
    assert_refused(rc, out, CEILING, "TASK-010")
    assert not (bridge_dir(repo) / "review-TASK-010-r5.json").exists()
    put(repo / "run" / "review" / "SCOPE-TASK-010.md", "Blocking class: failing test - the seeded count\n")
    snap_ok(repo, "TASK-010-r5")
    data = sorted(rounds(repo, "TASK-010")["rounds"], key=lambda r: r["round"])
    assert [r["round"] for r in data] == [1, 2, 3, 4, 5], data
    assert all(r.get("seeded") is True and r.get("reply") == 0 for r in data[:4]), data
    assert not data[4].get("seeded") and data[4].get("lift") == "class", data[4]


def test_task032_guard_r14_sub_increment_with_own_brief_is_its_own_id(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R14: TASK-010's letter snapshots (TASK-010, a, b)
    beside a TASK-010c that has its own brief seed TASK-010 with three rounds, not four (-r5 off
    the count, -r4 opened), and TASK-010c is counted under its own ID on its own branch."""
    repo = make_repo(tmp_path, branch="task-010", files={"handoff/TASK-010.md": "# TASK-010\n", "handoff/TASK-010c.md": "# TASK-010c\n"})
    git(repo, "branch", "task-010c", "main")
    for name in ("TASK-010", "TASK-010a", "TASK-010b"):
        old_snapshot(repo, name, "refs/heads/task-010")
    old_snapshot(repo, "TASK-010c", "refs/heads/task-010c")
    put(repo / "run" / "review" / "SCOPE-TASK-010.md", "Blocking class: security - the fourth round's finding\n")
    bump(repo)
    rc, out = guard(repo, "snapshot", "TASK-010-r5")
    assert_refused(rc, out, REFUSED, "3")
    snap_ok(repo, "TASK-010-r4")
    data = rounds(repo, "TASK-010")["rounds"]
    assert sorted(r["round"] for r in data if r.get("seeded")) == [1, 2, 3], data
    git(repo, "checkout", "-q", "task-010c")
    snap_ok(repo, "TASK-010c-r2")
    assert sorted(r["round"] for r in rounds(repo, "TASK-010c")["rounds"]) == [1, 2]


def test_task032_guard_r14_seeded_round_resnapshot_on_changed_tree_refused(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R14: rounds 1 to 3 seeded from three letter
    snapshots (TASK-001, TASK-001a, TASK-001b; TASK-001 has a brief) carry reply 0, so a seeded
    round counts as reviewed whatever its stored tree: `snapshot TASK-001-r3` on a changed tree is
    refused with `round 3 is reviewed: write TASK-001-r4`, nothing written (no rounds file
    seeded by the refusal)."""
    repo = make_repo(tmp_path, files={"handoff/TASK-001.md": "# TASK-001\n"})
    for name in ("TASK-001", "TASK-001a", "TASK-001b"):
        old_snapshot(repo, name, "refs/heads/task-001")
    bump(repo)
    refuse_and_nothing(repo, "TASK-001-r3", REFUSED, "round 3 is reviewed: write TASK-001-r4")


def test_task032_guard_r14_refused_snapshot_beside_old_snapshots_seeds_nothing(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (c): a refused snapshot writes no round
    record: with four letter snapshots and no rounds file, `snapshot TASK-001-r6` (off the count:
    four seeded rounds) is refused with exit 125, and afterwards no rounds file and no hash copy
    exist."""
    repo = make_repo(tmp_path, files={"handoff/TASK-001.md": "# TASK-001\n"})
    for name in ("TASK-001", "TASK-001a", "TASK-001b", "TASK-001c"):
        old_snapshot(repo, name, "refs/heads/task-001")
    bump(repo)
    before = hash_files()
    refuse_and_nothing(repo, "TASK-001-r6", REFUSED)
    assert not rounds_file(repo, "TASK-001").exists(), "the refused snapshot seeded a rounds file"
    assert new_hash_files(before) == []


def test_task032_guard_r19_five_thousand_digit_round_refused(tmp_path):
    """R-042. enforces: docs/BUILD_PLAN.md TASK-032 clause (c): a name the grammar cannot read is
    refused with exit 125: `TASK-001-r` followed by 5,000 nines (a value too long for int, refused,
    never a traceback), nothing written."""
    repo = make_repo(tmp_path)
    refuse_and_nothing(repo, "TASK-001-r" + "9" * 5000, REFUSED)


def test_task032_guard_r14_five_report_files_outrank_two_snapshots(tmp_path):
    """R-042. enforces: handoff/TASK-032-r2.md R14: five tracked report files
    handoff/TASK-010-r1..r5-report.md outrank two letter snapshots: five rounds are seeded, so
    -r3 is off the count (5 named) and -r6 is the next round (allowed with the class line)."""
    files = {"handoff/TASK-010.md": "# TASK-010\n"}
    for n in range(1, 6):
        files["handoff/TASK-010-r%d-report.md" % n] = "report %d\n" % n
    repo = make_repo(tmp_path, branch="task-010", files=files)
    for name in ("TASK-010", "TASK-010a"):
        old_snapshot(repo, name, "refs/heads/task-010")
    put(repo / "run" / "review" / "SCOPE-TASK-010.md", "Blocking class: behaviour - the sixth round's finding\n")
    bump(repo)
    rc, out = guard(repo, "snapshot", "TASK-010-r3")
    assert_refused(rc, out, REFUSED, "5")
    snap_ok(repo, "TASK-010-r6")
    data = rounds(repo, "TASK-010")["rounds"]
    assert sorted(r["round"] for r in data if r.get("seeded")) == [1, 2, 3, 4, 5], data


# --- permission guard (clause b2, R16) --------------------------------------------------------

def pguard(tmp_path, tool, command):
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto", "cwd": str(tmp_path)}
    p = subprocess.run([sys.executable, PGUARD], input=json.dumps(payload), capture_output=True, text=True,
                       cwd=str(tmp_path), env=env(), timeout=TIMEOUT)
    return p.returncode, p.stderr


PERMISSION_REFUSED = [
    'cursor-agent -p hi --force "Read handoff/TASK-001.md"',
    'cursor-agent --version "Read handoff/TASK-001.md"',
    "cursor-agent -p handoff/TASK-001.md",
    'python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force x && cursor-agent -p --force "Read handoff/TASK-001.md"',
    'python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p x; cursor-agent -p "Read handoff/TASK-001.md"',
    r'cursor-agent -p --force "Read handoff\TASK-010.md"',
    'cursor-agent -p --force "Read ./handoff/TASK-001.md"',
    r'cursor-agent -p --force "Read .\handoff\TASK-001.md"',
    r'cursor-agent -p --force "Read E:\repo\handoff\TASK-001.md"',
    'cursor-agent -p --force "Read docs/../handoff/TASK-001.md"',
    'cursor-agent -p --force "Read the brief (handoff/TASK-001.md)"',
    "cursor-agent -p --force @handoff/TASK-001.md",
    "cursor-agent -p --force 'Read handoff/TASK-001.md'",
    'cursor-agent -p --force "Read HANDOFF/TASK-001.md"',
    'cursor-agent --model x -p "Read handoff/TASK-001-r2.md"',
    'cursor-agent -p --force "Read run/review/REVIEW-TASK-001.diff"',
    r'cursor-agent -p --force "Read run\review\REVIEW-TASK-001.err"',
    'cursor-agent -p --force "Read run//review/REVIEW-TASK-001.diff"',
    'cursor-agent -p --force "Read Run/Review/REVIEW-TASK-001.diff"',
    "bash -c 'cursor-agent -p \"Read handoff/TASK-001.md\"'",
    'cmd /c cursor-agent -p "Read handoff/TASK-001.md"',
    "powershell -Command cursor-agent -p handoff/TASK-001.md",
    "eval cursor-agent -p handoff/TASK-001.md",
    "find . -maxdepth 0 -exec cursor-agent -p handoff/TASK-001.md ;",
    "git status; cursor-agent -p run/review/REVIEW-TASK-001.diff",
    '/usr/local/bin/cursor-agent -p "Read handoff/TASK-001.md"',
]


@pytest.mark.parametrize("command", PERMISSION_REFUSED)
@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
def test_task032_permission_r16_cursor_agent_naming_handoff_or_review_refused(tmp_path, tool, command):
    """R-042. enforces: handoff/TASK-032-r2.md R16: a cursor-agent head (bare, path-qualified,
    behind a wrapper shell, eval, a chain or find -exec, chained after a launcher command) whose
    arguments name handoff or run/review as a path segment, with either separator and in any
    case, is refused (exit 2), the reason naming the launcher; a probe's flag does not exempt it."""
    rc, err = pguard(tmp_path, tool, command)
    assert rc == 2 and "permission-guard (Claude-Cursor Bridge): refused - " in err, (tool, command, rc, err)
    assert LAUNCHER in err, (tool, command, err)


@pytest.mark.parametrize("command", [
    "cursor-agent --version",
    "cursor-agent -p hi",
    'python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force "Read handoff/TASK-012.md"',
    'python ~/.claude/cursor-bridge/bridge-run.py --kind review --limit 3600 -- cursor-agent -p "Read run/review/REVIEW-TASK-001.diff"',
    'cursor-agent -p "summarise the handoff in one line"',
    'cursor-agent -p "Read myhandoff/notes.md"',
])
@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
def test_task032_permission_r16_probes_and_launcher_form_allowed(tmp_path, tool, command):
    """R-042. enforces: handoff/TASK-032-r2.md R16: the probes `cursor-agent --version` and
    `cursor-agent -p hi` are allowed, the launcher form `python ... bridge-run.py ... --
    cursor-agent ... handoff/...` is allowed (its head is python), and an argument that names no
    handoff or run/review path segment is allowed."""
    rc, err = pguard(tmp_path, tool, command)
    assert rc == 0, (tool, command, err)
