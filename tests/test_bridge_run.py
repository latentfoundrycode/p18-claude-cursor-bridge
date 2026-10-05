"""bridge-run.py: the limit kills the whole process tree (KP-033), exit codes and output
pass through, only the loop's commands are accepted, and the stripped environment reaches
the child (KP-032). The tests point LOCALAPPDATA at a temporary folder so nothing is
written into the real profile (release 0a review, F4)."""
import os
import subprocess
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
TREE = os.path.join(HERE, "helpers", "sleep_tree.py")


def env_for(tmp_path, **extra):
    env = dict(os.environ)
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    env.update(extra)
    return env


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
                       capture_output=True, text=True, env=env_for(tmp_path))
    assert p.returncode == 124, p.stderr
    assert time.time() - t0 < 20
    assert p.stderr.startswith("bridge-run: started 20") and "Z\n" in p.stderr.splitlines()[0] + "\n"
    assert "LIMIT 3s reached" in p.stderr
    time.sleep(1)
    pids = [int(x) for x in pidfile.read_text().split()]
    assert len(pids) == 2, "parent and child both recorded their pid"
    survivors = [pid for pid in pids if alive(pid)]
    for pid in survivors:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"] if sys.platform == "win32" else ["kill", "-9", str(pid)], capture_output=True)
    assert survivors == []


@pytest.mark.skipif(sys.platform != "win32", reason="the job object is Windows")
def test_an_orphan_left_at_a_normal_end_is_killed(tmp_path):
    pidfile = str(tmp_path / "orphan.txt").replace(chr(92), "/")
    inner = "import time,os; open('%s','a').write(str(os.getpid())); time.sleep(600)" % pidfile
    code = ("import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',%r]); time.sleep(1.5); sys.exit(7)" % inner)
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path))
    assert p.returncode == 7
    time.sleep(1)
    pid = int(open(pidfile).read().strip())
    if alive(pid):
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        pytest.fail("the orphan survived the launcher's normal end")


def test_exit_code_and_output_pass_through(tmp_path):
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c",
                        "import sys; print('out line'); sys.stderr.write('err line' + chr(10)); sys.exit(7)"],
                       capture_output=True, text=True, env=env_for(tmp_path))
    assert p.returncode == 7
    assert "out line" in p.stdout and "err line" in p.stderr


def test_only_the_loops_commands_are_accepted(tmp_path):
    env = env_for(tmp_path)
    env.pop("BRIDGE_RUN_ALLOW_ANY")
    p = subprocess.run([sys.executable, PROG, "--limit", "5", "--", sys.executable, "-c", "print(1)"],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 125 and "refused" in p.stderr
    p = subprocess.run([sys.executable, PROG, "--limit", "5", "--", "powershell", "-c", "Remove-Item x"],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 125


def test_usage_errors(tmp_path):
    p = subprocess.run([sys.executable, PROG, "--limit", "x", "--", "echo"], capture_output=True, text=True, env=env_for(tmp_path))
    assert p.returncode == 2
    p = subprocess.run([sys.executable, PROG], capture_output=True, text=True, env=env_for(tmp_path))
    assert p.returncode == 2


def test_stripped_environment_reaches_the_child(tmp_path):
    """With --strip the child sees no token and gh's empty config folder (what cursor-agent gets)."""
    code = "import os; print(os.environ.get('GH_TOKEN','absent'), os.environ.get('GH_CONFIG_DIR',''), os.environ.get('GIT_TERMINAL_PROMPT',''), repr(os.environ.get('GIT_CONFIG_VALUE_0')))"
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--strip", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path, GH_TOKEN="secret"))
    assert p.returncode == 0, p.stderr
    token, gh_dir, prompt, helper = p.stdout.split()
    assert token == "absent" and prompt == "0" and helper == "''"
    assert gh_dir.startswith(str(tmp_path / "localappdata")) and gh_dir.endswith("gh-empty")
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path, GH_TOKEN="secret"))
    assert p.stdout.split()[0] == "secret", "without --strip (and not cursor-agent) the environment is untouched"


def test_stripped_environment_recipe(program, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    env = program("bridge_env").stripped_env({"GH_TOKEN": "x", "GITHUB_TOKEN": "y", "PATH": os.environ.get("PATH", ""), "HOME": "h"})
    assert "GH_TOKEN" not in env and "GITHUB_TOKEN" not in env
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GIT_CONFIG_KEY_0"] == "credential.helper" and env["GIT_CONFIG_VALUE_0"] == ""
    assert env["GH_CONFIG_DIR"] == os.path.join(str(tmp_path), "cursor-bridge", "gh-empty")


def test_shim_and_python_apply_the_same_recipe(program):
    """cursor-agent.shim (for the Bash tool) and bridge_env (for the Python launchers) must
    withhold the same things, or one path would leak what the other withholds."""
    shim = open(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "cursor-agent.shim"), encoding="utf-8").read()
    be = program("bridge_env")
    for var in be.TOKEN_VARS:
        assert var in shim, "the shim does not unset " + var
    assert 'export GH_CONFIG_DIR="$BRIDGE_GH_EMPTY"' in shim and "cursor-bridge/gh-empty" in shim
    assert "GIT_TERMINAL_PROMPT=0" in shim
    assert "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=credential.helper GIT_CONFIG_VALUE_0=" in shim
    assert shim.startswith("#!/bin/sh\n") and "\r" not in shim
    assert shim.rstrip().endswith('exec cursor-agent.cmd "$@"')


def test_bridge_run_resolves_cursor_agent_to_the_stripped_launcher(program, monkeypatch):
    br = program("bridge-run")
    monkeypatch.setattr(br.bridge_env, "cursor_agent_launcher", lambda: ["cmd.exe", "/d", "/c", "X:/cursor-agent.cmd"])
    argv, is_agent = br.resolve(["cursor-agent", "-p", "--force"])
    assert is_agent and argv[-2:] == ["-p", "--force"] and argv[0] == "cmd.exe"
    assert br.accepted(["cursor-agent", "-p"]) and br.accepted(["gh", "pr", "checks", "12", "--watch"])
    monkeypatch.delenv("BRIDGE_RUN_ALLOW_ANY", raising=False)
    assert not br.accepted(["gh", "pr", "merge", "12"]) and not br.accepted(["python", "x.py"])
