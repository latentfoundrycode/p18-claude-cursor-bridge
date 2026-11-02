"""Supervisor-side reproduction tests of BUG-039 (R-042, R-055; D-003 and D-004); written by the supervisor; the builder reads and runs them, never edits them.

R-042: a flagged round spends nothing, whichever of `verify`'s checks flagged it and whenever. D-003 draws that; as built
(docs/debug/BUG-039.md) `review-guard.py` did not hold it at four sites, and D-004 draws every git command of the guard
with the hooks and the file monitor off, which `premerge`'s one direct call did not hold. The names these tests call are
the fix's fixed points: `flagged_launch` (the round's key holding the voided launch's start time), `_git_proc` (the one
call site of git). The helpers are tests/test_task032_supervisor_guard.py's, imported, so the fixtures are the same.
"""
import ast
import importlib.util
import os
import re
import stat
import subprocess
import sys

import pytest

import test_task032_supervisor_guard as G

NAME = "TASK-001"


def start_of(repo, name=NAME):
    """The launch's start time as the launcher's first line gives it, without its Z."""
    with open(str(repo / "run" / "review" / ("REVIEW-%s.err" % name)), encoding="utf-8") as f:
        return re.search(r"started (\S+?)Z?$", f.readline().strip()).group(1)


def add_exit_0(repo, name=NAME):
    """The run that was still going ends: the launcher appends its exit line to the same .err."""
    with open(str(repo / "run" / "review" / ("REVIEW-%s.err" % name)), "a", encoding="utf-8") as f:
        f.write("bridge-run: exit 0\n")


def flagged_key(repo):
    return (G.entry(repo, NAME, 1).get("flagged_launch") or "").rstrip("Z")


def flagged_round(tmp_path):
    """A round whose verify flagged it at the end (a ref left behind), with its Review B exited 0."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.git(repo, "branch", "left-by-the-reviewer")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    return repo


def assert_voided_and_round_not_spent(repo):
    """The launch is voided by its start time, no reply is counted, and round 1 may be taken again on a changed tree."""
    assert flagged_key(repo) == start_of(repo), G.entry(repo, NAME, 1)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    G.bump(repo)
    G.snap_ok(repo, NAME)


def load_guard(monkeypatch):
    """review-guard.py loaded in this process, so one of its calls can be watched or stubbed."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.syspath_prepend(os.path.dirname(G.PROG))
    for key, value in G.env().items():
        monkeypatch.setenv(key, value)
    spec = importlib.util.spec_from_file_location("review_guard_bug039", G.PROG)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- Site 1: the four early returns of cmd_verify ------------------------------------------

def rewrite_the_snapshot(repo):
    snap = G.bridge_dir(repo) / ("review-%s.json" % NAME)
    text = snap.read_text(encoding="utf-8")
    snap.write_text(text.replace('"nnn"', '"nnn" ', 1), encoding="utf-8")


def change_the_config(repo):
    G.git(repo, "config", "bug039.left", "by-the-reviewer")


def plant_a_hook(repo):
    G.put(repo / ".git" / "hooks" / "post-checkout", "#!/bin/sh\nexit 0\n")


@pytest.mark.parametrize("left_behind", [rewrite_the_snapshot, change_the_config, plant_a_hook],
                         ids=["snapshot-rewritten", "config-changed", "hook-changed"])
def test_bug039_site1_a_flag_before_any_git_command_voids_the_launch(tmp_path, left_behind):
    """R-042, D-003 (`reply_arrived` to `flagged_gate_integrity`). enforces: docs/BUILD_PLAN.md TASK-043 Done when (1):
    `cmd_verify`'s early GATE-INTEGRITY returns on the snapshot rewritten and on `.git/config` or a hook changed call
    `record_flagged_launch`, so the launch is voided and round 1 is not spent."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    left_behind(repo)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    assert_voided_and_round_not_spent(repo)


@pytest.mark.parametrize("rewritten", ["[]", "{}", '{"taken": 5}'], ids=["not-an-object", "no-taken", "taken-not-a-string"])
def test_bug039_site1_negative_a_snapshot_rewritten_to_any_shape_stays_a_clean_flag(tmp_path, rewritten):
    """R-042, D-003. enforces: TASK-043's brief, Requirement 8: the snapshot's content is untrusted at the first early
    return, which now calls `record_flagged_launch`; a snapshot rewritten to valid JSON of another shape still ends in the
    GATE-INTEGRITY line and exit 1, with no traceback. An invariant (it holds on the unfixed guard, which reads no field
    there; a mutant of the fixed guard shows it strong)."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    (G.bridge_dir(repo) / ("review-%s.json" % NAME)).write_text(rewritten, encoding="utf-8")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "rewritten after it was taken" in out, out
    assert "Traceback" not in out, out


def test_bug039_site1_the_branch_held_in_another_worktree_voids_the_launch(tmp_path):
    """R-042, D-003. enforces: TASK-043 Done when (1), the third early return: the recorded branch checked out in another
    worktree."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.git(repo, "checkout", "-q", "-b", "other")
    wt = tmp_path / "wt"
    G.git(repo, "worktree", "add", "-q", str(wt), "task-001")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "another worktree" in out, out
    G.git(repo, "worktree", "remove", str(wt))
    G.git(repo, "checkout", "-q", "task-001")
    assert_voided_and_round_not_spent(repo)


def test_bug039_site1_the_branch_not_put_back_voids_the_launch(tmp_path, monkeypatch, capsys):
    """R-042, D-003. enforces: TASK-043 Done when (1), the fourth early return: the checkout could not be put back on the
    recorded branch. Git's checkout is stubbed to do nothing, the one way to reach that return on an ordinary repository."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.git(repo, "checkout", "-q", "-b", "other")
    guard = load_guard(monkeypatch)
    real_run_git = guard.run_git
    monkeypatch.setattr(guard, "run_git",
                        lambda args, root, common: "" if args[:1] == ["checkout"] else real_run_git(args, root, common))
    assert guard.cmd_verify(NAME, str(repo)) == 1
    assert "could not be put back" in capsys.readouterr().out
    G.git(repo, "checkout", "-q", "task-001")
    assert_voided_and_round_not_spent(repo)


def test_bug039_site1_negative_no_path_clears_a_recorded_flag(tmp_path):
    """R-042, D-003. enforces: TASK-043 Done when, the negative case of site 1: a flag once recorded is cleared by no path
    of the fix: a verify that now finds nothing to flag, and a re-snapshot, leave it where it was and count no reply."""
    repo = flagged_round(tmp_path)
    voided = flagged_key(repo)
    assert voided == start_of(repo)
    G.guard(repo, "verify", NAME)
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    G.snap_ok(repo, NAME)
    G.guard(repo, "verify", NAME)
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)


# --- Site 2: a flag raised while the run still goes on ------------------------------------

def test_bug039_site2_a_flag_during_the_run_voids_the_launch_that_later_exits_0(tmp_path):
    """R-042, D-003 (`review_launched` to `flagged_gate_integrity`). enforces: TASK-043 Done when (2):
    `record_flagged_launch` records the void by the launch's start time whatever the `.err` file's exit so far, so a flag
    raised while the run goes on voids the launch that later exits 0, and the next snapshot of the round on a changed tree
    is admitted."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME, exit_code=None)
    G.git(repo, "branch", "left-by-the-reviewer")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    add_exit_0(repo)
    assert_voided_and_round_not_spent(repo)


def test_bug039_site2_negative_no_path_admits_a_flagged_launch(tmp_path):
    """R-042, D-003. enforces: TASK-043 Done when, the negative case of site 2: a flagged round's launch is admitted by no
    path. A flag raised during the run, the run then exiting 0, and a verify that finds nothing left to flag (the first
    verify repaired the ref): no reply, no verified mark, exit 1, and `premerge` refuses. A new Review B run on the same
    snapshot is a launch of its own, and it is admitted."""
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME, exit_code=None)
    G.git(repo, "branch", "left-by-the-reviewer")
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1, out
    add_exit_0(repo)
    rc, out = G.guard(repo, "verify", NAME)
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    assert not (G.bridge_dir(repo) / ("verified-%s.json" % NAME)).exists(), out
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 2 and "no verified mark" in out, out
    G.launched(repo, NAME, offset=3)
    G.verify_ok(repo, NAME)
    assert G.entry(repo, NAME, 1).get("reply") == 0, G.entry(repo, NAME, 1)
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 0, out


# --- Site 3: premerge's git call ----------------------------------------------------------

def verified_round(tmp_path):
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, NAME)
    G.launched(repo, NAME)
    G.verify_ok(repo, NAME)
    return repo


def test_bug039_site3_every_git_command_of_premerge_runs_with_both_switches(tmp_path, monkeypatch, capsys):
    """R-042, D-004 (`p_review_guard` to `ds_checkout`, hooks off). enforces: TASK-043 Done when (3): `cmd_premerge`'s
    `git merge-base --is-ancestor` runs through the guard's git helper, with the hooks folder emptied and
    `core.fsmonitor=false` like every other git command of the guard. Every git process `premerge` starts is watched."""
    repo = verified_round(tmp_path)
    guard = load_guard(monkeypatch)
    started = []
    real_run = subprocess.run

    def watching(cmd, *args, **kwargs):
        if cmd and cmd[0] == "git":
            started.append(list(cmd))
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", watching)
    assert guard.cmd_premerge(NAME, str(repo)) == 0, capsys.readouterr().out
    assert any("merge-base" in cmd for cmd in started), started
    for cmd in started:
        assert any(word.startswith("core.hooksPath=") for word in cmd), cmd
        assert "core.fsmonitor=false" in cmd, cmd


def test_bug039_site3_no_git_call_of_the_guard_bypasses_the_helper():
    """R-042, D-004. enforces: TASK-043 Done when (3): no `subprocess.run` of git in `review-guard.py` bypasses the helper,
    the helper's own call site (`_git_proc`) the one exemption and nothing else. A process call outside `_git_proc` must
    name its program as a literal, and that literal is not git; os.system and os.popen appear nowhere."""
    with open(G.PROG, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    in_helper = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_git_proc":
            in_helper = {id(n) for n in ast.walk(node)}
    assert in_helper, "the helper _git_proc is gone"
    helper_calls = 0
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)):
            continue
        owner, name = node.func.value.id, node.func.attr
        assert (owner, name) not in (("os", "system"), ("os", "popen")), "line %d" % node.lineno
        if owner != "subprocess":
            continue
        if id(node) in in_helper:
            helper_calls += 1
            continue
        first = node.args[0] if node.args else None
        assert isinstance(first, ast.List) and first.elts and isinstance(first.elts[0], ast.Constant), "line %d" % node.lineno
        assert first.elts[0].value != "git", "line %d: a git command outside _git_proc" % node.lineno
    assert helper_calls == 1


def test_bug039_site3_negative_premerge_runs_no_planted_hook_or_monitor(tmp_path):
    """R-042, D-004, KP-032. enforces: TASK-043 Done when, the negative case of site 3: `premerge` runs with a planted hook
    and a planted file monitor, each shown not to have run. An invariant (the accept commit names its hand mutation)."""
    repo = verified_round(tmp_path)
    marker = tmp_path / "planted-ran"
    script = "#!/bin/sh\necho ran >> '%s'\nexit 0\n" % marker.as_posix()
    planted = tmp_path / "planted.sh"
    G.put(planted, script)
    os.chmod(str(planted), os.stat(str(planted)).st_mode | stat.S_IXUSR)
    for hook in ("post-index-change", "reference-transaction"):
        G.put(repo / ".git" / "hooks" / hook, script)
        os.chmod(str(repo / ".git" / "hooks" / hook), 0o755)
    G.git(repo, "config", "core.fsmonitor", planted.as_posix())
    rc, out = G.guard(repo, "premerge", NAME)
    assert rc == 0, out
    assert not marker.exists(), "a planted program ran during premerge: " + marker.read_text(encoding="utf-8")


# --- Site 4: the re-snapshot --------------------------------------------------------------

def test_bug039_site4_a_resnapshot_keeps_the_flag(tmp_path):
    """R-042, D-003 (`flagged_gate_integrity` to `resnapshotted`). enforces: TASK-043 Done when (4): `cmd_snapshot`'s
    replacement of a round's entry keeps `flagged_launch` beside `reply`, `lift`, `lift_line` and `time`, so a flagged round
    taken again counts no reply and spends nothing (found by Review B of PR #116)."""
    repo = flagged_round(tmp_path)
    voided = flagged_key(repo)
    G.snap_ok(repo, NAME)
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)
    G.bump(repo)
    G.snap_ok(repo, NAME)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)


@pytest.mark.parametrize("change_the_tree", [False, True], ids=["same-tree", "changed-tree"])
def test_bug039_site4_negative_a_resnapshot_counts_no_reply_on_either_tree(tmp_path, change_the_tree):
    """R-042, D-003. enforces: TASK-043 Done when, the negative case of site 4: a re-snapshot of a flagged round, on the
    same tree and on a changed one, keeps `flagged_launch` and counts no reply: the round's next snapshot on another tree
    is admitted under its own number, never refused as reviewed."""
    repo = flagged_round(tmp_path)
    voided = flagged_key(repo)
    if change_the_tree:
        G.bump(repo)
    G.snap_ok(repo, NAME)
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)
    assert G.entry(repo, NAME, 1).get("reply") is None, G.entry(repo, NAME, 1)
    G.bump(repo)
    rc, out = G.guard(repo, "snapshot", NAME)
    assert rc == 0, out
    assert flagged_key(repo) == voided, G.entry(repo, NAME, 1)
