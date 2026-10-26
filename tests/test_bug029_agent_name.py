"""BUG-029: the launcher knows cursor-agent by one exact name, and a holder's record is published before its
slot-taken line (handoff/BUG-029.md; docs/HARDENING.md, TASK-029 rounds 3 and 4). The supervisor's tests."""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")


def load_br():
    spec = importlib.util.spec_from_file_location("bridge_run_bug029", PROG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def br(monkeypatch):
    monkeypatch.delenv("BRIDGE_RUN_ALLOW_ANY", raising=False)
    return load_br()


def test_bug029_head_of_strips_one_trailing_suffix(br):
    """BUG-029 (handoff/BUG-029.md, the exact name): head_of strips one trailing .exe or .cmd only, so the
    other runners' names read as before and a doubled suffix is not the agent."""
    assert br.head_of(["C:/py/python.exe", "-m", "pytest"]) == "python"
    assert br.head_of(["npx.cmd", "vitest"]) == "npx"
    assert br.head_of(["gh.exe", "pr", "checks", "1"]) == "gh"
    assert br.head_of(["cursor-agent"]) == "cursor-agent"
    assert br.head_of(["cursor-agent.cmd"]) == "cursor-agent"
    assert br.head_of(["cursor-agent.exe"]) == "cursor-agent"
    assert br.head_of(["cursor-agent.exe.cmd"]) != "cursor-agent"
    assert br.head_of(["cursor-agent.cmd.exe"]) != "cursor-agent"


def test_bug029_only_the_exact_agent_names_are_the_agent(br, tmp_path):
    """BUG-029 (handoff/BUG-029.md, the exact name; a cursor-agent given by path refused): the agent is one of
    cursor-agent, cursor-agent.cmd and cursor-agent.exe, bare; a doubled suffix or a path is not accepted as it."""
    for name in ("cursor-agent", "cursor-agent.cmd", "cursor-agent.exe", "Cursor-Agent.CMD"):
        assert br.kind_of([name, "-p"]) == "builder", name   # precondition: the real names stay the agent
        assert br.accepted([name, "-p"]), name
    for name in ("cursor-agent.exe.cmd", "cursor-agent.cmd.cmd", "cursor-agent.exe.exe"):
        assert br.kind_of([name, "-p"]) is None, name
        assert not br.accepted([name, "-p"]), name
    for path in (str(tmp_path / "cursor-agent"), str(tmp_path / "cursor-agent.cmd"), "./cursor-agent",
                 "C:/tools/cursor-agent.exe", "sub\\cursor-agent"):
        assert not br.accepted([path, "-p"]), path


def test_bug029_resolve_swaps_in_the_agent_for_an_exact_name_only(br, monkeypatch, tmp_path):
    """BUG-029 (handoff/BUG-029.md, the exact name in resolve): resolve puts the stripped agent launcher in place
    only for a bare exact agent name; a doubled suffix or a path keeps its own argv[0] and is not the agent."""
    monkeypatch.setattr(br.bridge_env, "cursor_agent_launcher", lambda: ["cmd.exe", "/d", "/c", "X:/cursor-agent.cmd"])
    for name in ("cursor-agent", "Cursor-Agent.CMD", "cursor-agent.exe"):
        argv, is_agent = br.resolve([name, "-p"])
        assert is_agent and argv[:4] == ["cmd.exe", "/d", "/c", "X:/cursor-agent.cmd"], name   # precondition
    for name in ("cursor-agent.exe.cmd", str(tmp_path / "cursor-agent"), "./cursor-agent"):
        argv, is_agent = br.resolve([name, "-p"])
        assert not is_agent, name
        assert "X:/cursor-agent.cmd" not in argv, name


def _stub(folder, name, marker):
    stub = folder / name
    if sys.platform == "win32":
        stub.write_text('@echo off\r\necho ran> "%s"\r\n' % marker, encoding="ascii")
    else:
        stub.write_text('#!/bin/sh\necho ran > "%s"\n' % marker, encoding="ascii")
        stub.chmod(0o755)
    return stub


@pytest.mark.parametrize("kind", ["review", None])
def test_bug029_a_doubled_suffix_never_runs_as_the_agent(tmp_path, kind):
    """BUG-029 (handoff/BUG-029.md; docs/HARDENING.md, TASK-029 round 3, the security audit's advisory 1): a
    file named cursor-agent.exe.cmd on PATH, launched as `--kind review` or with no kind, is refused (125, the
    launcher's refusal of an unknown command) and never runs; today it passes as the agent and runs as itself."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "ran.txt"
    _stub(bin_dir, "cursor-agent.exe.cmd", marker)
    root = tmp_path / "launch"
    (root / "run").mkdir(parents=True)
    env = dict(os.environ)
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    flags = ["--limit", "30"] + (["--kind", kind] if kind else [])
    p = subprocess.run([sys.executable, PROG] + flags + ["--", "cursor-agent.exe.cmd", "-p", "--force", "--model",
                                                         "grok-4.7-medium", "x"],
                       cwd=str(root), env=env, capture_output=True, text=True, timeout=60)
    assert p.returncode == 125, p.stderr
    assert "bridge-run: refused - the launcher runs only cursor-agent" in p.stderr
    assert not marker.exists()


def test_bug029_record_published_before_the_slot_taken_line(br, monkeypatch):
    """BUG-029 (handoff/BUG-029.md, the record before the line; docs/HARDENING.md, TASK-029 round 4): when a
    launcher takes the slot, its holder record already names it when its `slot taken` line is written, so a
    waiter started on that line reads it."""
    _, holder_path = br.heavy_state_paths()
    seen = {}

    class Err(object):
        def write(self, text):
            if text.startswith("bridge-run: slot taken "):
                try:
                    with open(holder_path, encoding="utf-8") as f:
                        seen["run_id"] = json.loads(f.read()).get("run_id")
                except (OSError, ValueError):
                    seen["run_id"] = None

        def flush(self):
            pass

    monkeypatch.setattr(sys, "stderr", Err())
    result = br.acquire_heavy_slot("test", "2026-10-26T12:00:00Z", 60, 1.0)
    monkeypatch.undo()
    assert isinstance(result, tuple), result               # precondition: the free slot was taken
    br._unlock_byte(result[0])
    os.close(result[0])
    assert "run_id" in seen, "no slot-taken line was written"
    assert seen["run_id"] == "2026-10-26T12:00:00Z"
