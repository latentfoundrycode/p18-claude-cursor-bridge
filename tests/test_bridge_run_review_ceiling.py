"""R-042: the launcher holds the code gate's round ceiling (docs/REQUIREMENTS.md line 48)."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
sys.path.insert(0, os.path.join(HERE, os.pardir, "bridge", "cursor-bridge"))
import bridge_env  # noqa: E402


def ws(tmp_path):
    root = tmp_path / "ws"
    (root / "run").mkdir(parents=True)
    (root / "handoff").mkdir()
    (root / "docs").mkdir()
    return root


def roster(root, builder="composer-2.5"):
    (root / "docs" / "ROSTER.resolved.json").write_text(
        json.dumps({"profile": "native", "builder": builder, "review_a": "x", "review_b": "y"}),
        encoding="utf-8",
    )


def plan(root, *ids):
    lines = ["# Plan\n"]
    for i in ids:
        lines.append("### %s — title\n" % i)
    (root / "docs" / "BUILD_PLAN.md").write_text("".join(lines), encoding="utf-8", newline="\n")


def brief(root, name, extra=""):
    body = "# %s\n\n## Scope\n- x\n%s" % (name.replace(".md", ""), extra)
    (root / "handoff" / name).write_text(body, encoding="utf-8", newline="\n")


def git_init(root, branch):
    env = dict(
        os.environ,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_SYSTEM=os.devnull,
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@x",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@x",
    )
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(root), env=env, check=True, creationflags=NO_WINDOW)
    subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=str(root), env=env, check=True, creationflags=NO_WINDOW)
    (root / "README").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=str(root), env=env, check=True, creationflags=NO_WINDOW)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(root), env=env, check=True, creationflags=NO_WINDOW)


def run_launch(root, env, *cmd, kind=None, limit="30"):
    flags = ["--limit", limit]
    if kind:
        flags += ["--kind", kind]
    return subprocess.run(
        [sys.executable, PROG] + flags + ["--"] + list(cmd),
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        creationflags=NO_WINDOW,
    )


def stub_agent(bin_dir, marker):
    stub = bin_dir / ("cursor-agent.cmd" if sys.platform == "win32" else "cursor-agent")
    if sys.platform == "win32":
        stub.write_text('@echo off\r\necho ran> "%s"\r\n' % marker, encoding="ascii")
    else:
        stub.write_text('#!/bin/sh\necho ran > "%s"\n' % marker, encoding="ascii")
        stub.chmod(0o755)


def agent_cmd(prompt, model="composer-2.5"):
    return ["cursor-agent", "-p", "--force", "--model", model, prompt]


def test_r042_review_rounds_constant():
    assert bridge_env.REVIEW_ROUNDS == 3
    assert len(bridge_env.BLOCKING_CLASSES) == 5


@pytest.mark.parametrize(
    "name,ok",
    [
        ("TASK-001", True),
        ("TASK-010c", True),
        ("CONFIG-B3b", True),
        ("TASK-001-r2", True),
        ("-r0", False),
        ("TASK-001-r05", False),
        ("TASK-001-R2", False),
        ("task-001", False),
    ],
)
def test_r042_name_grammar(name, ok):
    assert (bridge_env.parse_review_name(name) is not None) == ok


def test_r042_refuses_launch_without_brief(tmp_path):
    root = ws(tmp_path)
    roster(root)
    plan(root, "TASK-001")
    git_init(root, "task-001")
    env = dict(os.environ)
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "ran.txt"
    stub_agent(bin_dir, marker)
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    p = run_launch(root, env, "cursor-agent", "-p", "x")
    assert p.returncode == 125 and "brief rule" in p.stderr
    assert "bridge-run: started" not in p.stderr
    assert not marker.exists()


def test_r042_allow_any_does_not_exempt_cursor_agent(tmp_path):
    root = ws(tmp_path)
    roster(root)
    plan(root, "TASK-001")
    git_init(root, "task-001")
    env = dict(os.environ, BRIDGE_RUN_ALLOW_ANY="1")
    p = run_launch(root, env, "cursor-agent", "-p", "x")
    assert p.returncode == 125 and "brief rule" in p.stderr


def test_r042_review_on_builder_model_refused(tmp_path):
    root = ws(tmp_path)
    roster(root, builder="composer-2.5")
    plan(root, "TASK-001")
    git_init(root, "task-001")
    env = dict(os.environ)
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    p = run_launch(root, env, *agent_cmd("review only"), kind="review")
    assert p.returncode == 125 and "builder model" in p.stderr


def test_r042_class_line_allows_round_four(program, tmp_path):
    root = ws(tmp_path)
    roster(root)
    plan(root, "TASK-001")
    git_init(root, "task-001")
    log = root / "run" / "launcher" / "runs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    for rnd, name in ((1, "TASK-001"), (2, "TASK-001-r2"), (3, "TASK-001-r3")):
        parts.append(json.dumps({"brief": "TASK-001", "round": rnd, "brief_name": name, "exit": 0, "branch": "task-001"}))
    log.write_text("\n".join(parts) + "\n", encoding="utf-8")
    brief(
        root,
        "TASK-001-r4.md",
        "\nBlocking class: behaviour - missing check\n",
    )
    br = program("bridge-run")
    reason, meta = br.builder_review_refusal(
        agent_cmd("Read handoff/TASK-001-r4.md"),
        str(root),
        "builder",
    )
    assert reason is None and meta and meta.get("lift") == "class"


def test_r042_owner_line_allows_high_round(program, tmp_path):
    root = ws(tmp_path)
    roster(root)
    plan(root, "TASK-001")
    git_init(root, "task-001")
    log = root / "run" / "launcher" / "runs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    for rnd, name in ((1, "TASK-001"), (2, "TASK-001-r2"), (3, "TASK-001-r3"), (4, "TASK-001-r4")):
        parts.append(json.dumps({"brief": "TASK-001", "round": rnd, "brief_name": name, "exit": 0, "branch": "task-001"}))
    log.write_text("\n".join(parts) + "\n", encoding="utf-8")
    (root / "docs" / "RUN_PARAMETERS.md").write_text(
        "Review rounds above the ceiling: TASK-001 5 (owner words, 2026-10-24)\n",
        encoding="utf-8",
    )
    brief(root, "TASK-001-r5.md")
    br = program("bridge-run")
    reason, meta = br.builder_review_refusal(
        agent_cmd("Read handoff/TASK-001-r5.md"),
        str(root),
        "builder",
    )
    assert reason is None and meta and meta.get("lift") == "owner"


def test_r042_revised_in_place_refused(program, tmp_path):
    root = ws(tmp_path)
    roster(root)
    plan(root, "TASK-001")
    git_init(root, "task-001")
    brief(root, "TASK-001.md", "")
    log = root / "run" / "launcher" / "runs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        json.dumps(
            {
                "id": "t",
                "brief": "TASK-001",
                "round": 1,
                "brief_name": "TASK-001",
                "brief_sha256": "dead",
                "exit": 0,
                "branch": "task-001",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    br = program("bridge-run")
    reason, _ = br.builder_review_refusal(agent_cmd("Read handoff/TASK-001.md"), str(root), "builder")
    assert reason and "revised in place" in reason


def test_r042_builder_on_main_refused(program, tmp_path):
    root = ws(tmp_path)
    roster(root)
    plan(root, "TASK-001")
    git_init(root, "main")
    brief(root, "TASK-001.md")
    br = program("bridge-run")
    reason, _ = br.builder_review_refusal(agent_cmd("Read handoff/TASK-001.md"), str(root), "builder")
    assert reason and "main" in reason


def test_r042_test_kind_on_main_starts(program, tmp_path):
    root = ws(tmp_path)
    git_init(root, "main")
    env = dict(os.environ, BRIDGE_RUN_ALLOW_ANY="1")
    p = run_launch(root, env, "python", "-c", "pass", kind="test", limit="5")
    assert p.returncode == 0 and "bridge-run: started" in p.stderr


def test_r042_log_fields_on_builder(program, tmp_path):
    root = ws(tmp_path)
    roster(root)
    plan(root, "TASK-001")
    git_init(root, "task-001")
    brief(root, "TASK-001.md")
    env = dict(os.environ)
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub_agent(bin_dir, tmp_path / "m.txt")
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    p = run_launch(root, env, *agent_cmd("Read handoff/TASK-001.md"))
    assert "started" in p.stderr
    row = json.loads((root / "run" / "launcher" / "runs.jsonl").read_text(encoding="utf-8").strip())
    assert row.get("brief") == "TASK-001" and row.get("round") == 1
    assert row.get("brief_sha256") and "lift" in row
    assert "Read handoff" not in json.dumps(row)


def _launch_env(tmp_path, root, with_stub=True):
    env = dict(os.environ)
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    if with_stub:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        marker = tmp_path / "stub-ran.txt"
        stub_agent(bin_dir, marker)
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        return env, marker
    return env, None


@pytest.mark.parametrize("brief_name", ["TASK-001", "TASK-010c", "CONFIG-B3b", "HOTFIX-001", "B3-CLOSE", "TASK-001-r2"])
def test_r042_accepted_brief_names_launch(tmp_path, brief_name):
    root = ws(tmp_path)
    roster(root)
    plan(root, "TASK-001", "TASK-010c", "CONFIG-B3b", "HOTFIX-001", "B3-CLOSE")
    git_init(root, "task-001")
    brief(root, "%s.md" % brief_name)
    env, marker = _launch_env(tmp_path, root)
    p = run_launch(root, env, *agent_cmd("Read handoff/%s.md" % brief_name))
    assert p.returncode == 0 and "bridge-run: started" in p.stderr
    assert marker.exists()


@pytest.mark.parametrize("bad", ["TASK-001-r0", "TASK-001-r05", "TASK-001-R2", "TASK 001", "TASK-001-r2\n"])
def test_r042_refused_brief_names(tmp_path, bad):
    root = ws(tmp_path)
    roster(root)
    plan(root, "TASK-001")
    git_init(root, "task-001")
    brief(root, "TASK-001.md")
    env, marker = _launch_env(tmp_path, root)
    p = run_launch(root, env, *agent_cmd("Read handoff/%s.md" % bad))
    assert p.returncode == 125
    assert "bridge-run: started" not in p.stderr
    assert not (root / "run" / "launcher" / "runs.jsonl").exists()
    assert not marker.exists()
