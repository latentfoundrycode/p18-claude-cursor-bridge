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
    assert "LIMIT 3s reached" in p.stderr and "bridge-run: exit 124" in p.stderr
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
    assert p.stderr.rstrip().endswith("bridge-run: exit 7"), "the last line is the exit code, which review-guard.py reads"


def test_only_the_loops_commands_are_accepted(tmp_path):
    env = env_for(tmp_path)
    env.pop("BRIDGE_RUN_ALLOW_ANY")
    p = subprocess.run([sys.executable, PROG, "--limit", "5", "--", sys.executable, "-c", "print(1)"],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 125 and "refused" in p.stderr
    p = subprocess.run([sys.executable, PROG, "--limit", "5", "--", "powershell", "-c", "Remove-Item x"],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 125


def test_test_suites_are_accepted_by_name_and_their_kind_is_inferred(program):
    br = program("bridge-run")
    for cmd in (["pytest", "-q"], ["python", "-m", "pytest", "tests"], ["uv", "run", "pytest"], ["npm", "test"],
                ["npx", "vitest", "run"], ["go", "test", "./..."], ["cargo", "test"], ["dotnet", "test"]):
        assert br.kind_of(cmd) == "test" and br.accepted(cmd), cmd
    assert br.kind_of(["cursor-agent", "-p"]) == "builder" and br.kind_of(["gh", "pr", "checks", "12"]) == "watch"
    for cmd in (["python", "-c", "x"], ["npm", "run", "dev"], ["npx", "serve"], ["go", "run", "."]):
        assert br.kind_of(cmd) is None, cmd


def runs_of(tmp_path):
    import json
    log = tmp_path / "run" / "launcher" / "runs.jsonl"
    return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()] if log.is_file() else []


def test_every_run_is_logged_without_its_prompt_and_can_be_marked_healthy(tmp_path):
    (tmp_path / "run").mkdir()                             # the log is written only where a project's run/ exists
    code = "import sys; print(1)"
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--kind", "test", "--", sys.executable, "-c", code, "a prompt with spaces that is not logged"],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 0, p.stderr
    run_id = p.stderr.splitlines()[0].split()[-1]
    runs = runs_of(tmp_path)
    assert len(runs) == 1 and runs[0]["id"] == run_id and runs[0]["kind"] == "test" and runs[0]["exit"] == 0
    assert runs[0]["healthy"] is None and "prompt" not in runs[0]["head"] and runs[0]["limit"] == 30
    p = subprocess.run([sys.executable, PROG, "--healthy", run_id[:16]], capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 0 and "marked healthy" in p.stderr, p.stderr
    assert runs_of(tmp_path)[0]["healthy"] is True
    p = subprocess.run([sys.executable, PROG, "--healthy", "2000-01-01"], capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 1


def test_a_run_ended_at_its_limit_is_logged_before_the_tree_dies(tmp_path):
    (tmp_path / "run").mkdir()
    pidfile = tmp_path / "pids.txt"
    p = subprocess.run([sys.executable, PROG, "--limit", "2", "--kind", "test", "--", sys.executable, TREE, str(pidfile)],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 124
    runs = runs_of(tmp_path)
    assert len(runs) == 1 and runs[0]["exit"] == 124 and runs[0]["seconds"] >= 2
    time.sleep(1)
    for pid in [int(x) for x in pidfile.read_text().split()]:
        if alive(pid):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"] if sys.platform == "win32" else ["kill", "-9", str(pid)], capture_output=True)


def test_the_learned_limit_grows_only_from_healthy_runs_and_never_past_the_cap(program, tmp_path):
    import json
    br = program("bridge-run")
    log = tmp_path / "run" / "launcher"
    log.mkdir(parents=True)
    rows = [{"id": "2026-10-07T10:00:00Z", "kind": "test", "seconds": 2400, "exit": 0, "healthy": None},
            {"id": "2026-10-07T11:00:00Z", "kind": "test", "seconds": 900, "exit": 0, "healthy": True},
            {"id": "2026-10-07T12:00:00Z", "kind": "test", "seconds": 5000, "exit": 124, "healthy": True},
            {"id": "2026-10-07T13:00:00Z", "kind": "builder", "seconds": 7000, "exit": 0, "healthy": True}]
    (log / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    assert br.learned_limit("test", str(tmp_path))[0] == 1800 and "default" in br.learned_limit("test", str(tmp_path))[1], "900 s healthy: 1.5x is below the default"
    assert br.learned_limit("watch", str(tmp_path)) == (3600, "the default for watch"), "no run of the kind: the default"
    rows[1]["seconds"] = 1600
    (log / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    limit, why = br.learned_limit("test", str(tmp_path))
    assert limit == 2400 and "2026-10-07T11:00:00Z" in why, (limit, why)
    rows[1]["seconds"] = 3000
    (log / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    assert br.learned_limit("test", str(tmp_path))[0] == 3600, "capped at twice the default (1.5 x 3000 = 4500)"
    assert br.learned_limit("builder", str(tmp_path))[0] == 10500, "1.5 x 7000 under the cap of 14400"
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "RUN_PARAMETERS.md").write_text("Merge authority: supervisor\nCeiling above twice: test 6000 (the owner: 'let the suite run', 2026-10-07)\n", encoding="utf-8")
    assert br.learned_limit("test", str(tmp_path))[0] == 4500, "the owner's words lift the cap"
    p = subprocess.run([sys.executable, PROG, "--limit", "auto", "--kind", "test", "--", sys.executable, "-c", "print(1)"],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 0 and "bridge-run: limit 4500s for test (learned from run 2026-10-07T11:00:00Z" in p.stderr, p.stderr
    p = subprocess.run([sys.executable, PROG, "--limit", "9999", "--kind", "watch", "--", sys.executable, "-c", "print(1)"],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 125 and "above twice the default" in p.stderr, "an explicit limit above the cap needs the owner's words"


def test_the_key_file_reaches_the_child_only_and_must_lie_outside_the_workspace(tmp_path):
    ws = tmp_path / "Workspace"
    ws.mkdir()
    outside = tmp_path / "keys.txt"
    outside.write_text("# the key file\nTHING_API_KEY=value-never-printed\nnot a key line\n", encoding="utf-8")
    code = "import os; print(os.environ.get('THING_API_KEY', 'absent'))"
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--kind", "test", "--key-file", str(outside), "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(ws))
    assert p.returncode == 0 and p.stdout.strip() == "value-never-printed", p.stderr
    assert "THING_API_KEY" in p.stderr and "value-never-printed" not in p.stderr, "names are printed, values never"
    assert "THING_API_KEY" not in os.environ
    inside = ws / "keys.txt"
    inside.write_text("THING_API_KEY=x\n", encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--kind", "test", "--key-file", str(inside), "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(ws))
    assert p.returncode == 125 and "outside" in p.stderr
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--kind", "test", "--key-file", str(tmp_path / "missing.txt"), "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(ws))
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
    code = "import os; print(os.environ['HOME']); print(os.environ.get('USERPROFILE', ''))"
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--strip", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path))
    home = os.path.join(os.environ["USERPROFILE"], ".cursor-bridge", "agent-home")
    assert p.returncode == 0 and os.path.normcase(p.stdout.splitlines()[0].strip()) == os.path.normcase(home), "the child runs in the agent's own home (KP-038): " + p.stdout + p.stderr
    assert os.path.lexists(os.path.join(home, ".cursor"))


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
