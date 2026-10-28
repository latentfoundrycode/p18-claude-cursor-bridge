"""Hotfix 2026.10.25a: the roster's switch rules (2026-10-25 C3, 2026-10-18 C3 and C4) and the launcher's
review-family refusal, CI watch wait, boundary listing and pytest option (2026-10-25 C5 and C10)."""
import json
import os
import subprocess
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROSTER_PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "roster-check.py")
RUN_PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")

ROSTER = {
    "other_pool": "available",
    "review_a": "claude-opus-5-5",
    "profiles": [
        {"name": "full", "builder": "grok-4.7-high", "review_b": "gpt-5.6-sol-high"},
        {"name": "native", "builder": "composer-2.5", "review_b": "grok-4.7-high"},
    ],
}


def git_repo(path, branch="task-1"):
    subprocess.run(["git", "init", "-q", "-b", branch, str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "c"],
                   check=True, capture_output=True)


def builder_run(model, branch):
    return json.dumps({"id": "b-" + model, "kind": "builder", "head": "cursor-agent", "model": model, "branch": branch,
                       "limit": 7200, "seconds": 100, "exit": 0, "healthy": True}) + "\n"


def roster_run(cwd, roster_path, *args):
    p = subprocess.run([sys.executable, ROSTER_PROG, str(roster_path), "--no-probe"] + list(args), capture_output=True, text=True, cwd=str(cwd))
    return p.returncode, p.stdout + p.stderr


# --- roster-check.py ---------------------------------------------------------------------------

def test_a_branch_with_no_builder_run_has_no_built_family(program, tmp_path, monkeypatch):
    """2026-10-18 C3: another branch's builder did not build this branch's change (a design review)."""
    rc = program("roster-check")
    log = tmp_path / "runs.jsonl"
    log.write_text(builder_run("grok-4.7-high", "task-9"), encoding="utf-8")
    monkeypatch.setattr(rc, "current_branch", lambda: "design-x")
    assert rc.built_by(str(log)) is None
    monkeypatch.setattr(rc, "current_branch", lambda: "task-9")
    assert rc.built_by(str(log)) == "grok-4.7-high"


def test_the_services_unavailable_line_is_a_connection_error(program):
    """2026-10-18 C4: an outage of the service is not the model's failure."""
    rc = program("roster-check")
    assert rc.classify_failure("[unavailable] Error: the model is temporarily unavailable")[0] == "CONNECTION"


def test_clear_unavailable_removes_an_automatic_mark(tmp_path):
    """2026-10-18 C4: a wrong six-hour mark has a remedy."""
    git_repo(tmp_path)
    roster = tmp_path / "ROSTER.json"
    roster.write_text(json.dumps(ROSTER), encoding="utf-8")
    state = tmp_path / ".git" / "bridge" / "roster-state.json"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"other_pool": "available", "unavailable": {"grok-4.7-high": "2026-10-25T08:00 UTC: 2 consecutive failures -- x"}}), encoding="utf-8")
    rc, out = roster_run(tmp_path, roster, "--clear-unavailable", "grok-4.7-high")
    assert rc == 0 and "CLEARED" in out, out
    assert "unavailable" not in json.loads(state.read_text(encoding="utf-8")), state.read_text(encoding="utf-8")


def fake_probe_run(monkeypatch, rc_module, returncode, stdout, stderr=""):
    monkeypatch.setattr(rc_module, "cursor_agent_cmd", lambda: ["cursor-agent"])
    monkeypatch.setattr(rc_module.bridge_env, "stripped_env", lambda: {})
    fake = types.SimpleNamespace(run=lambda *a, **k: types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr),
                                 TimeoutExpired=subprocess.TimeoutExpired)
    monkeypatch.setattr(rc_module, "subprocess", fake)


def test_an_off_script_probe_reply_counts_as_answered(program, monkeypatch):
    """2026-10-25 C3 (FB-001): a sentence instead of the word is a model that is there; FAIL sends the owner to buy usage."""
    rc = program("roster-check")
    fake_probe_run(monkeypatch, rc, 0, "Sure - OK, I am here.")
    ok, detail = rc.probe("grok-4.7-high")
    assert ok and "off-script" in detail, detail


def test_a_usage_limit_reply_an_empty_reply_and_a_refusal_still_fail(program, monkeypatch):
    rc = program("roster-check")
    for code, out in ((0, "You've hit your usage limit for this model."), (0, ""), (1, "OK"),
                      (0, "[unavailable] Error: model temporarily unavailable"), (0, "Error: request failed (connection reset)")):
        fake_probe_run(monkeypatch, rc, code, out)
        ok, detail = rc.probe("grok-4.7-high")
        assert not ok, (code, out, detail)


def test_the_resolved_roster_is_rewritten_only_when_it_changes(tmp_path):
    """2026-10-25 C3 (FB-008): a check before every snapshot no longer dirties the tree; the time goes to the state."""
    git_repo(tmp_path)
    roster = tmp_path / "ROSTER.json"
    roster.write_text(json.dumps(ROSTER), encoding="utf-8")
    resolved = tmp_path / "ROSTER.resolved.json"
    env = dict(os.environ, ROSTER_NOW="2026-10-25T08:00")
    p = subprocess.run([sys.executable, ROSTER_PROG, str(roster), "--no-probe"], capture_output=True, text=True, cwd=str(tmp_path), env=env)
    assert p.returncode == 0, p.stdout
    first = resolved.read_bytes()
    env["ROSTER_NOW"] = "2026-10-25T09:30"
    p = subprocess.run([sys.executable, ROSTER_PROG, str(roster), "--no-probe"], capture_output=True, text=True, cwd=str(tmp_path), env=env)
    assert p.returncode == 0 and "not rewritten" in p.stdout, p.stdout
    assert resolved.read_bytes() == first
    state = json.loads((tmp_path / ".git" / "bridge" / "roster-state.json").read_text(encoding="utf-8"))
    assert state.get("last_resolved") == "2026-10-25T09:30 UTC", state


def test_a_switch_resolves_the_new_builder_for_the_change_in_flight(tmp_path):
    """2026-10-25 C3 (ISS-008 / FB-013): the pool runs out at Review B of a change the full profile's builder made;
    the native profile resolves, its builder rebuilds the change, and only then may its Review B run."""
    git_repo(tmp_path)
    exhausted = dict(ROSTER, other_pool="exhausted")
    roster = tmp_path / "ROSTER.json"
    roster.write_text(json.dumps(exhausted), encoding="utf-8")
    (tmp_path / "run" / "launcher").mkdir(parents=True)
    (tmp_path / "run" / "launcher" / "runs.jsonl").write_text(builder_run("grok-4.7-medium", "task-1"), encoding="utf-8")
    rc, out = roster_run(tmp_path, roster)
    assert rc == 0 and "RESOLVED profile 'native'" in out and "REBUILD" in out, out
    assert json.loads((tmp_path / "ROSTER.resolved.json").read_text(encoding="utf-8"))["rebuild"]["rebuild_with"] == "composer-2.5"


# --- bridge-run.py -----------------------------------------------------------------------------

def test_the_launcher_refuses_a_review_b_of_the_family_that_built_the_change(program, tmp_path, monkeypatch):
    """The family rule held by a program: until the rebuild, Review B grok on a grok-built change is refused."""
    git_repo(tmp_path)
    (tmp_path / "run" / "launcher").mkdir(parents=True)
    log = tmp_path / "run" / "launcher" / "runs.jsonl"
    log.write_text(builder_run("grok-4.7-medium", "task-1"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    br = program("bridge-run")
    cmd = ["cursor-agent", "-p", "--force", "--model", "grok-4.7-high", "review the diff"]
    reason = br.review_family_refusal(cmd, str(tmp_path))
    assert reason and "xai" in reason and "rebuild" in reason, reason
    log.write_text(builder_run("grok-4.7-medium", "task-1") + builder_run("composer-2.5", "task-1"), encoding="utf-8")
    assert br.review_family_refusal(cmd, str(tmp_path)) is None, "after the rebuild by composer the grok review may run"


def test_pytest_without_its_cache_is_accepted_after_python_m_pytest(program):
    """2026-10-25 C5 (FB-034): the reviewers are told to use -p no:cacheprovider."""
    br = program("bridge-run")
    assert br.accepted(["python", "-m", "pytest", "-p", "no:cacheprovider", "-q"])
    assert br.accepted(["python", "-m", "pytest", "-pno:cacheprovider"])
    assert not br.accepted(["python", "-m", "pytest", "-p", "evil_plugin"])
    assert not br.accepted(["python", "-p", "no:x", "-m", "pytest"])


def test_the_watch_waits_for_the_pushed_heads_first_check(program, monkeypatch):
    """2026-10-25 C5 (FB-002, KP-051): no "no checks reported" at once, never the previous commit's run."""
    br = program("bridge-run")
    states = iter([("old", 3), ("new", 0), ("new", 2)])
    monkeypatch.setattr(br, "gh_pr_state", lambda args, folder: next(states))
    monkeypatch.setattr(br, "local_head", lambda folder: "new")
    monkeypatch.setattr(br.time, "sleep", lambda s: None)
    line = br.wait_for_first_check(["gh", "pr", "checks", "12", "--watch", "--required"], ".")
    assert line.startswith("waited 20s") and "2 check(s)" in line, line


def test_the_watch_starts_anyway_after_two_minutes_and_says_so(program, monkeypatch):
    br = program("bridge-run")
    monkeypatch.setattr(br, "gh_pr_state", lambda args, folder: ("old", 1))
    monkeypatch.setattr(br, "local_head", lambda folder: "new")
    monkeypatch.setattr(br.time, "sleep", lambda s: None)
    line = br.wait_for_first_check(["gh", "pr", "checks", "12", "--watch"], ".")
    assert line.startswith("waited 120s") and "starts anyway" in line, line
    assert br.wait_for_first_check(["gh", "pr", "checks", "12"], ".") is None, "a one-off check is not a watch"


def test_a_builder_run_reports_a_write_outside_the_workspace(tmp_path):
    """2026-10-25 C10 (ISS-010): a builder told to write outside the Workspace did, undetected."""
    root = tmp_path / "project"
    work = root / "Workspace"
    (work / "run").mkdir(parents=True)
    (root / "Documents").mkdir()
    (root / "Documents" / "kept.md").write_text("x", encoding="utf-8")
    (root / "Worktrees" / "TASK-1").mkdir(parents=True)
    script = ("import pathlib; pathlib.Path(r'%s').write_text('y'); pathlib.Path(r'%s').write_text('z'); pathlib.Path('inside.txt').write_text('i')"
              % (root / "Documents" / "planted.md", root / "Worktrees" / "TASK-1" / "other-builder.txt"))
    env = dict(os.environ, LOCALAPPDATA=str(tmp_path / "localappdata"), BRIDGE_RUN_ALLOW_ANY="1")
    p = subprocess.run([sys.executable, RUN_PROG, "--limit", "60", "--kind", "builder", "--", sys.executable, "-c", script],
                       capture_output=True, text=True, cwd=str(work), env=env)
    assert p.returncode == 0, p.stderr
    assert "BOUNDARY new outside the Workspace: Documents/planted.md" in p.stderr, p.stderr
    assert "other-builder" not in p.stderr and "inside.txt" not in p.stderr and "kept.md" not in p.stderr, p.stderr
    runs = [json.loads(l) for l in (work / "run" / "launcher" / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert runs[-1].get("boundary") == ["new Documents/planted.md"], runs[-1]
    assert p.stderr.strip().splitlines()[-1] == "bridge-run: exit 0", "the exit line stays the last line"


def slot_not_free_run(model, branch):
    """The row the launcher writes when a heavy run ended waiting for the slot (bridge-run.py, exit 123):
    the command never started."""
    return json.dumps({"id": "n-" + model, "kind": "builder", "head": "cursor-agent", "model": model, "branch": branch,
                       "limit": 7200, "waited": 7320, "seconds": 0, "exit": 123, "slot": "not free", "healthy": None}) + "\n"


def test_a_launch_that_never_got_the_slot_did_not_build_the_change(program, tmp_path, monkeypatch):
    """BUG-030 (stage B5's review, round 1, Blocking): a builder launch that ended at exit 123 with
    `"slot": "not free"` never started its command, so its model built nothing; the change in flight is
    still the last started builder's, and a Review B of that builder's family stays refused."""
    git_repo(tmp_path)
    (tmp_path / "run" / "launcher").mkdir(parents=True)
    log = tmp_path / "run" / "launcher" / "runs.jsonl"
    log.write_text(builder_run("grok-4.7-medium", "task-1") + slot_not_free_run("composer-2.5", "task-1"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    rc = program("roster-check")
    monkeypatch.setattr(rc, "current_branch", lambda: "task-1")
    assert rc.built_by(str(log)) == "grok-4.7-medium"
    br = program("bridge-run")
    cmd = ["cursor-agent", "-p", "--force", "--model", "grok-4.7-high", "review the diff"]
    reason = br.review_family_refusal(cmd, str(tmp_path))
    assert reason and "rebuild" in reason, "a rebuild that never started is no rebuild: %r" % reason
