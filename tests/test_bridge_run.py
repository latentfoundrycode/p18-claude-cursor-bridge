"""bridge-run.py: the limit kills the whole process tree (KP-033), exit codes and output
pass through, and cursor-agent gets the stripped environment (KP-032)."""
import os
import subprocess
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, ".claude", "cursor-bridge", "bridge-run.py")
TREE = os.path.join(HERE, "helpers", "sleep_tree.py")


def alive(pid):
    if sys.platform == "win32":
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True).stdout
        return (" %d " % pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def test_limit_kills_parent_and_child(tmp_path):
    pidfile = tmp_path / "pids.txt"
    t0 = time.time()
    p = subprocess.run([sys.executable, PROG, "--limit", "3", "--", sys.executable, TREE, str(pidfile)],
                       capture_output=True, text=True)
    assert p.returncode == 124, p.stderr
    assert time.time() - t0 < 20
    assert "LIMIT 3s reached" in p.stderr
    time.sleep(1)
    pids = [int(x) for x in pidfile.read_text().split()]
    assert len(pids) == 2, "parent and child both recorded their pid"
    survivors = [pid for pid in pids if alive(pid)]
    for pid in survivors:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"] if sys.platform == "win32" else ["kill", "-9", str(pid)], capture_output=True)
    assert survivors == []


def test_exit_code_and_output_pass_through():
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c",
                        "import sys; print('out line'); sys.stderr.write('err line\\n'); sys.exit(7)"],
                       capture_output=True, text=True)
    assert p.returncode == 7
    assert "out line" in p.stdout and "err line" in p.stderr


def test_usage_errors():
    p = subprocess.run([sys.executable, PROG, "--limit", "x", "--", "echo"], capture_output=True, text=True)
    assert p.returncode == 2
    p = subprocess.run([sys.executable, PROG], capture_output=True, text=True)
    assert p.returncode == 2


def test_stripped_environment(program):
    env = program("bridge_env").stripped_env({"GH_TOKEN": "x", "GITHUB_TOKEN": "y", "PATH": os.environ.get("PATH", ""), "HOME": "h"})
    assert "GH_TOKEN" not in env and "GITHUB_TOKEN" not in env
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GIT_CONFIG_KEY_0"] == "credential.helper" and env["GIT_CONFIG_VALUE_0"] == ""
    assert env["GH_CONFIG_DIR"].endswith(os.path.join("cursor-bridge", "gh-empty"))


def test_bridge_run_resolves_cursor_agent_to_the_stripped_launcher(program, monkeypatch):
    br = program("bridge-run")
    be = program("bridge_env")
    monkeypatch.setattr(br.bridge_env, "cursor_agent_launcher", lambda: ["cmd.exe", "/d", "/c", "X:/cursor-agent.cmd"])
    argv, is_agent = br.resolve(["cursor-agent", "-p", "--force"])
    assert is_agent and argv[-2:] == ["-p", "--force"] and argv[0] == "cmd.exe"
