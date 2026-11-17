"""bridge-run.py: the limit kills the whole process tree (KP-033), exit codes and output
pass through, only the loop's commands are accepted, and the stripped environment reaches
the child (KP-032), the withheld and set names D-004's note lists among them. The tests point
LOCALAPPDATA at a temporary folder so nothing is written into the real profile (release 0a
review, F4)."""
import json
import os
import subprocess
import sys
import time

import pytest

from test_account_keys import d004_stripped_note

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
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
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
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 7
    time.sleep(1)
    pid = int(open(pidfile).read().strip())
    if alive(pid):
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        pytest.fail("the orphan survived the launcher's normal end")


def test_exit_code_and_output_pass_through(tmp_path):
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c",
                        "import sys; print('out line'); sys.stderr.write('err line' + chr(10)); sys.exit(7)"],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 7
    assert "out line" in p.stdout and "err line" in p.stderr
    assert p.stderr.rstrip().endswith("bridge-run: exit 7"), "the last line is the exit code, which review-guard.py reads"


def test_only_the_loops_commands_are_accepted(tmp_path):
    env = env_for(tmp_path)
    env.pop("BRIDGE_RUN_ALLOW_ANY")
    p = subprocess.run([sys.executable, PROG, "--limit", "5", "--", sys.executable, "-c", "print(1)"],
                       capture_output=True, text=True, env=env, cwd=str(tmp_path),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 125 and "refused" in p.stderr
    p = subprocess.run([sys.executable, PROG, "--limit", "5", "--", "powershell", "-c", "Remove-Item x"],
                       capture_output=True, text=True, env=env, cwd=str(tmp_path),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 125


def test_test_suites_are_accepted_by_name_and_their_kind_is_inferred(program):
    br = program("bridge-run")
    for cmd in (["pytest", "-q"], ["python", "-m", "pytest", "tests"], ["uv", "run", "pytest"], ["npm", "test"],
                ["npx", "vitest", "run"], ["go", "test", "./..."], ["cargo", "test"], ["dotnet", "test"]):
        assert br.kind_of(cmd) == "test" and (cmd[0] == "npx" or br.accepted(cmd)), cmd   # npx only with a local install
    assert br.kind_of(["cursor-agent", "-p"]) == "builder" and br.kind_of(["gh", "pr", "checks", "12"]) == "watch"
    for cmd in (["python", "-c", "x"], ["npm", "run", "dev"], ["npx", "serve"], ["go", "run", "."]):
        assert br.kind_of(cmd) is None, cmd
    # review of 2026.10.10a, finding 9: options that run another program, and npx without a local install
    for cmd in (["go", "test", "-exec", "evil", "./..."], ["pytest", "-p", "evil"], ["pytest", "-pevil"], ["pytest", "--basetemp=../.."], ["cargo", "test", "--config", "x"], ["pytest", "-c", "x.ini"],
                ["go", "test", "-toolexec", "evil"], ["node", "--test", "--require", "evil.js"], ["./tools/pytest", "-q"], ["C:/x/pytest.exe"]):
        assert not br.test_suite(cmd), cmd
    for cmd in (["pytest", "-p", "no:cacheprovider", "-q"], ["pytest", "-pno:cacheprovider"], ["dotnet", "test", "-c", "Release"],
                ["uv", "run", "--project", "backend", "pytest", "-q"], ["uv", "run", "--frozen", "pytest"],
                ["uv", "run", "--project=backend", "pytest"], ["uv", "run", "--project", "x", "pytest", "-p", "no:cacheprovider"]):
        assert br.test_suite(cmd, os.getcwd()), cmd        # second pass, S2, and reAngle's forms: ordinary options stay allowed
    here = os.getcwd().replace("\\", "/")
    assert br.test_suite([here + "/backend/.venv/Scripts/python.exe", "-m", "pytest", "-q"], os.getcwd()), "the project's own venv python is the interpreter, not the runner"
    for cmd in (["uv", "run", "--with", "pytest", "python", "script.py"], ["uv", "run", "python", "evil.py", "pytest"], ["uv", "run", "--python", "3.12", "pytest"], ["uv", "run", "-p", "3.12", "pytest"],
                ["C:/anywhere/python.exe", "-m", "pytest"], [here + "/tools/python.exe", "-m", "pytest"]):
        assert not br.test_suite(cmd, os.getcwd()), cmd    # the first review of A3, finding 9
    assert br.head_text(["pytest", "login", "-q"]) == "pytest" and br.head_text(["gh", "pr", "checks", "12"]) == "gh pr checks" and br.head_text(["npm", "run", "test:e2e"]) == "npm run test:e2e"
    assert not br.test_suite(["npx", "vitest"], folder=os.getcwd()) or os.path.isfile(os.path.join(os.getcwd(), "node_modules", ".bin", "vitest"))
    for cmd in (["npm", "run", "test:e2e"], ["pnpm", "test"], ["yarn", "test"], ["node", "--test"], ["python", "-m", "unittest"]):
        assert br.test_suite(cmd), cmd


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
    assert p.stderr.startswith("bridge-run: started 20"), "the launch line is the FIRST line, whatever else is printed: " + p.stderr
    run_id = p.stderr.splitlines()[0].split()[-1]
    runs = runs_of(tmp_path)
    assert len(runs) == 1 and runs[0]["id"] == run_id and runs[0]["kind"] == "test" and runs[0]["exit"] == 0
    assert runs[0]["healthy"] is True, "a passing test run is its own gate (finding 5)"
    assert "prompt" not in runs[0]["head"] and runs[0]["head"].startswith("python") and "-c" not in runs[0]["head"] and runs[0]["limit"] == 30
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--kind", "builder", "--", sys.executable, "-c", "print(2)"],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 0 and runs_of(tmp_path)[1]["healthy"] is None, "a builder run is marked by the supervisor after the merge"
    run_id2 = p.stderr.splitlines()[0].split()[-1]
    p = subprocess.run([sys.executable, PROG, "--healthy", run_id2[:10]], capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 1 and "fits 2 runs" in p.stderr, "a prefix that fits two runs is refused (finding 2): " + p.stderr
    p = subprocess.run([sys.executable, PROG, "--healthy", run_id2[:10], "--kind", "builder"], capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 0 and "marked healthy" in p.stderr and runs_of(tmp_path)[1]["healthy"] is True, p.stderr
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
            {"id": "2026-10-07T12:00:00Z", "kind": "test", "seconds": 5000, "exit": 124, "healthy": None},
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
    rows[2]["healthy"] = True                              # finding 5: a run ended at its limit whose kept work merged counts
    (log / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    assert br.learned_limit("test", str(tmp_path))[0] == 3600 and "2026-10-07T12:00:00Z" in br.learned_limit("test", str(tmp_path))[1]
    rows[2]["healthy"] = None
    (log / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    assert br.learned_limit("builder", str(tmp_path))[0] == 10500, "1.5 x 7000 under the cap of 14400"
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "RUN_PARAMETERS.md").write_text("Merge authority: supervisor\nCeiling above twice: test 240 (a slip: minutes, 2026-10-07)\n", encoding="utf-8")
    assert br.learned_limit("test", str(tmp_path))[0] == 3600, "an owner's value below twice the default is ignored (finding 6)"
    (tmp_path / "docs" / "RUN_PARAMETERS.md").write_text("Merge authority: supervisor\nCeiling above twice: test 6000 (the owner: 'let the suite run', 2026-10-07)\n", encoding="utf-8")
    assert br.learned_limit("test", str(tmp_path))[0] == 4500, "the owner's words lift the cap"
    p = subprocess.run([sys.executable, PROG, "--limit", "auto", "--kind", "test", "--", sys.executable, "-c", "print(1)"],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 0 and "bridge-run: limit 4500s for test (learned from run 2026-10-07T11:00:00Z" in p.stderr, p.stderr
    p = subprocess.run([sys.executable, PROG, "--limit", "9999", "--kind", "watch", "--", sys.executable, "-c", "print(1)"],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 125 and "above twice the default" in p.stderr, "an explicit limit above the cap needs the owner's words"


def test_the_launch_line_comes_first_and_review_guard_reads_it(program, tmp_path):
    """Review of 2026.10.10a, finding 1: with --limit auto the launch time stayed the first line
    that review-guard.py and pr-activity-check.py read; otherwise every merge is refused."""
    (tmp_path / "run" / "review").mkdir(parents=True)
    keys = tmp_path.parent / (tmp_path.name + "-keys.txt")   # outside the folder the launcher runs in
    keys.write_text("X_TOKEN=never-printed\n", encoding="utf-8")
    err = tmp_path / "run" / "review" / "REVIEW-001.err"
    with open(err, "w", encoding="utf-8") as f:
        p = subprocess.run([sys.executable, PROG, "--limit", "auto", "--kind", "review", "--key-file", str(keys), "--", sys.executable, "-c", "print(1)"],
                           stdout=subprocess.DEVNULL, stderr=f, env=env_for(tmp_path / "elsewhere"), cwd=str(tmp_path))
    assert p.returncode == 0
    lines = err.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("bridge-run: started 20") and lines[-1] == "bridge-run: exit 0" and any("limit " in l for l in lines), lines
    rg = program("review-guard")
    launched, code = rg.launch_info(str(err))
    assert launched and code == 0, (launched, code)
    pac = program("pr-activity-check")
    assert pac.parse_ts(lines[0].split()[-1]) is not None, "pr-activity-check --since takes the first line's time"
    assert "never-printed" not in err.read_text(encoding="utf-8")


def test_a_key_file_never_goes_to_the_agent(tmp_path):
    keys = tmp_path / "keys.txt"
    keys.write_text("X_TOKEN=x\n", encoding="utf-8")
    env = env_for(tmp_path)
    env.pop("BRIDGE_RUN_ALLOW_ANY")
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--key-file", str(keys), "--", "cursor-agent", "-p", "x"],
                       capture_output=True, text=True, env=env, cwd=str(tmp_path / "ws") if (tmp_path / "ws").mkdir() is None else str(tmp_path))
    assert p.returncode == 125 and "never goes to a cursor-agent run" in p.stderr, p.stderr


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
    p = subprocess.run([sys.executable, PROG, "--limit", "x", "--", "echo"], capture_output=True, text=True, env=env_for(tmp_path),
                       cwd=str(tmp_path), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 2
    p = subprocess.run([sys.executable, PROG], capture_output=True, text=True, env=env_for(tmp_path),
                       cwd=str(tmp_path), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 2


def test_stripped_environment_reaches_the_child(tmp_path):
    """With --strip the child sees no token and gh's empty config folder (what cursor-agent gets)."""
    code = "import os; print(os.environ.get('GH_TOKEN','absent'), os.environ.get('GH_CONFIG_DIR',''), os.environ.get('GIT_TERMINAL_PROMPT',''), repr('' if os.environ.get('GIT_CONFIG_GLOBAL','').replace(chr(92),'/').endswith('/.cursor-bridge/gitconfig') and 'GIT_CONFIG_VALUE_0' not in os.environ else None))"
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--strip", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path, GH_TOKEN="secret"), cwd=str(tmp_path),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 0, p.stderr
    token, gh_dir, prompt, helper = p.stdout.split()
    assert token == "absent" and prompt == "0" and helper == "''"
    assert gh_dir.startswith(str(tmp_path / "localappdata")) and gh_dir.endswith("gh-empty")
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path, GH_TOKEN="secret"), cwd=str(tmp_path),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.stdout.split()[0] == "secret", "without --strip (and not cursor-agent) the environment is untouched"
    code = "import os; print(os.environ['HOME']); print(os.environ.get('USERPROFILE', ''))"
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--strip", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(tmp_path),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    home = os.path.join(os.environ["USERPROFILE"], ".cursor-bridge", "agent-home")
    assert p.returncode == 0 and os.path.normcase(p.stdout.splitlines()[0].strip()) == os.path.normcase(home), "the child runs in the agent's own home (KP-038): " + p.stdout + p.stderr
    assert os.path.lexists(os.path.join(home, ".cursor"))


def test_r055_d004_a_stripped_run_gets_the_notes_names(tmp_path):
    """R-055, D-004 (`p_bridge_run` to `p_test_suite`). enforces: docs/BUILD_PLAN.md TASK-044 Done when: through the
    launcher's `--strip`, the child holds none of the withheld names the diagram's note lists, and every name it says is set,
    the owner's caches being present here (the three under the home, and since release S the eight under the two application
    folders), its home the agent's and not the owner's; without the flag the same variables reach the child, so the test can fail."""
    withheld, _, _, set_names = d004_stripped_note()
    home = tmp_path / "home"
    for rel in (".cursor", os.path.join(".cache", "huggingface", "hub"), os.path.join(".cache", "torch"), os.path.join(".cache", "puppeteer")):
        (home / rel).mkdir(parents=True)
    for base, rel in (("localappdata", "uv/cache"), ("appdata", "uv/python"), ("localappdata", "pip/Cache"), ("appdata", "Python"),
                      ("localappdata", "npm-cache"), ("localappdata", "Yarn/Cache"), ("localappdata", "ms-playwright"), ("localappdata", "go-build")):
        (tmp_path / base / rel).mkdir(parents=True)        # bridge_env.APP_CACHES: the owner's folders the strip passes by the tool's own variable
    extra = {name: "v" for name in withheld}
    extra.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(tmp_path / "appdata"))
    env = env_for(tmp_path, **extra)
    for name in set_names:
        if name not in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
            env.pop(name, None)
    code = "import json, os; print(json.dumps({'names': sorted(os.environ), 'homes': [os.environ.get('HOME'), os.environ.get('USERPROFILE')]}))"
    launch = tmp_path / "launch"
    launch.mkdir()
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--strip", "--", sys.executable, "-c", code], capture_output=True, text=True, env=env,
                       cwd=str(launch), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 0, p.stderr
    seen = json.loads(p.stdout)
    names = set(seen["names"])
    assert [os.path.basename(h) for h in seen["homes"]] == ["agent-home", "agent-home"], "the run's home is the agent's"
    assert not set(withheld) & names, "a name the note withholds reached the child"
    missing = set(set_names) - names if os.name == "nt" else set(set_names) - names - {"HOMEDRIVE", "HOMEPATH"}
    assert not missing, "a name the note says is set did not reach the child: " + ", ".join(sorted(missing))
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", code], capture_output=True, text=True, env=env,
                       cwd=str(launch), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 0 and set(withheld) <= set(json.loads(p.stdout)["names"]), p.stderr


def test_stripped_environment_recipe(program, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    env = program("bridge_env").stripped_env({"GH_TOKEN": "x", "GITHUB_TOKEN": "y", "PATH": os.environ.get("PATH", ""), "HOME": "h"})
    assert "GH_TOKEN" not in env and "GITHUB_TOKEN" not in env
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert "GIT_CONFIG_VALUE_0" not in env and env["GIT_CONFIG_GLOBAL"].replace("\\", "/").endswith("/.cursor-bridge/gitconfig"), "the helper is reset in the bridge's git config file (2026.10.11c)"
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
    assert "unset GIT_CONFIG_COUNT GIT_CONFIG_KEY_0 GIT_CONFIG_VALUE_0" in shim and "[credential]" in shim and 'export GIT_CONFIG_GLOBAL="$BRIDGE_REAL_HOME_M/.cursor-bridge/gitconfig"' in shim and "GIT_CONFIG_PARAMETERS=\"'credential.helper='\"" in shim
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


def test_r078_npm_prefix_and_c_count_as_one_folder_option(program, tmp_path):
    """R-078: npm's -C and --prefix are the same folder option for the duplicate rule."""
    br = program("bridge-run")
    base = str(tmp_path / "ws")
    os.makedirs(os.path.join(base, "frontend"), exist_ok=True)
    assert br.test_suite(["npm", "--prefix", "frontend", "test"], base)
    assert not br.test_suite(["npm", "--prefix", "frontend", "test", "-C", "frontend"], base)
    assert br.known_runner_refuse_word(["npm", "--prefix", "frontend", "test", "-C", "frontend"], base) == "--prefix"


def test_r078_npm_prefix_value_beginning_with_tilde_is_refused(program, tmp_path):
    """R-078: a folder option value that starts with ~ is refused before any filesystem call."""
    br = program("bridge-run")
    base = str(tmp_path / "ws")
    os.makedirs(os.path.join(base, "frontend"), exist_ok=True)
    os.makedirs(os.path.join(base, "~", "frontend"), exist_ok=True)
    assert br.test_suite(["npm", "--prefix", "frontend", "test"], base)
    assert not br.test_suite(["npm", "--prefix", "~/frontend", "test"], base)


def test_r078_npm_prefix_folder_value_held_to_character_list(program, tmp_path):
    """R-078: folder option values outside the allowed character list are refused by text."""
    br = program("bridge-run")
    base = str(tmp_path / "ws")
    os.makedirs(os.path.join(base, "frontend"), exist_ok=True)
    for bad in (chr(0xA0) + "~/frontend", "a${OS}"):
        try:
            os.makedirs(os.path.join(base, bad.strip(chr(0xA0))), exist_ok=True)
            os.makedirs(os.path.join(base, bad), exist_ok=True)
        except OSError:
            pass
    assert br.test_suite(["npm", "--prefix", "frontend", "test"], base)
    assert not br.test_suite(["npm", "--prefix", chr(0xA0) + "~/frontend", "test"], base)
    assert not br.test_suite(["npm", "--prefix", "a${OS}", "test"], base)


def test_r078_folder_option_value_rewritten_to_rule_checked_path(program, tmp_path):
    """R-078: an accepted npm suite gets folder option values rewritten to the rule-checked folder relative to launch."""
    br = program("bridge-run")
    base = str(tmp_path / "ws")
    os.makedirs(os.path.join(base, "frontend"), exist_ok=True)
    rel = os.path.join(".", "frontend")
    assert br._package_folder_rewrite(["npm", "test", "--prefix", "frontend"], base) == (
        ["npm", "test", "--prefix", rel], None,
    )
    assert br._package_folder_rewrite(["npm", "--prefix=frontend", "test", "--", "--prefix", "x"], base) == (
        ["npm", "--prefix=" + rel, "test", "--", "--prefix", "x"], None,
    )
    assert br._package_folder_rewrite(["npm", "--prefix", "frontend/..", "test"], base) == (
        ["npm", "--prefix", ".", "test"], None,
    )


def test_r078_folder_option_rewrite_refused_when_relpath_raises(program, tmp_path, monkeypatch):
    """R-078: when os.path.relpath cannot compute the relative folder, the rewrite refuses naming the option."""
    br = program("bridge-run")
    base = str(tmp_path / "ws")
    os.makedirs(os.path.join(base, "frontend"), exist_ok=True)

    def bad_relpath(path, start):
        raise ValueError

    monkeypatch.setattr(br.os.path, "relpath", bad_relpath)
    for argv in (
        ["npm", "test", "--prefix", "frontend"],
        ["npm", "--prefix=frontend", "test"],
    ):
        result, refuse = br._package_folder_rewrite(argv, base)
        assert refuse == "--prefix"
        assert result is None


HIDDEN = "VALUE-NEVER-PRINTED"


def test_r080_a_key_file_home_variable_is_refused_before_start_for_a_test_run(tmp_path):
    """R-080 (J10): a key file naming a home variable is refused before `bridge-run: started` for a test-kind launch that is not a named suite."""
    launch = tmp_path / "launch"
    launch.mkdir()
    keys = tmp_path / "keys.env"
    keys.write_text("FIX060_OK=works\n", encoding="utf-8")
    env = env_for(tmp_path)
    ok_code = "import os; print(os.environ.get('FIX060_OK', ''))"
    ok = subprocess.run([sys.executable, PROG, "--limit", "30", "--kind", "test", "--key-file", str(keys), "--", sys.executable, "-c", ok_code],
                        capture_output=True, text=True, cwd=str(launch), env=env, timeout=120,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert ok.returncode == 0 and "bridge-run: started" in ok.stderr and ok.stdout.strip() == "works", ok.stderr
    keys.write_text("USERPROFILE=%s\nSAFE_KEY=1\n" % HIDDEN, encoding="utf-8")
    code = "import os; print(os.environ.get('SAFE_KEY', ''))"
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--kind", "test", "--key-file", str(keys), "--", sys.executable, "-c", code],
                       capture_output=True, text=True, cwd=str(launch), env=env, timeout=120,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert p.returncode == 125 and "bridge-run: started" not in p.stderr and "USERPROFILE" in p.stderr, p.stderr
    assert HIDDEN not in p.stderr and HIDDEN not in p.stdout


def test_r080_stripped_cursor_agent_keeps_cursor_keys_while_stripped_test_does_not(program, tmp_path, monkeypatch):
    """R-080 (J11): secret-like CURSOR_ names follow is_agent, not the kind label; default stripped_env keeps them for cursor-agent probes."""
    be = program("bridge_env")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    base = {"PATH": os.environ.get("PATH", ""), "HOME": str(tmp_path / "home"), "USERPROFILE": str(tmp_path / "home"),
            "CURSOR_API_KEY": HIDDEN, "CURSOR_TRACE_LEVEL": "1"}
    (tmp_path / "home" / ".cursor").mkdir(parents=True)
    stripped_test = be.stripped_env({**base}, kind="test")
    assert "CURSOR_API_KEY" not in stripped_test and "CURSOR_TRACE_LEVEL" in stripped_test
    stripped_builder_label = be.stripped_env({**base}, kind="builder")
    assert "CURSOR_API_KEY" not in stripped_builder_label
    agent_run = be.stripped_env({**base}, is_agent=True)
    assert "CURSOR_API_KEY" in agent_run and "CURSOR_TRACE_LEVEL" in agent_run
    non_agent = be.stripped_env({**base}, is_agent=False)
    assert "CURSOR_API_KEY" not in non_agent
    default = be.stripped_env({**base})
    assert "CURSOR_API_KEY" in default and "CURSOR_TRACE_LEVEL" in default


# ---------------------------------------------------------------- R-079 learned_limit


def _write_learn_rows(tmp_path, rows):
    log = tmp_path / "run" / "launcher"
    log.mkdir(parents=True, exist_ok=True)
    (log / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_r079_learned_limit_row_at_review_end_is_inside(program, tmp_path):
    """R-079: both ends of a review run are inclusive, so a row at the end is ignored."""
    br = program("bridge-run")
    review = {"id": "2026-10-07T10:00:00Z", "kind": "review", "seconds": 1200, "exit": 0, "healthy": True}
    at_end = {"id": "2026-10-07T10:20:00Z", "kind": "test", "seconds": 3000, "exit": 0, "healthy": True}
    outside = {"id": "2026-10-07T12:00:00Z", "kind": "test", "seconds": 1600, "exit": 0, "healthy": True}
    _write_learn_rows(tmp_path, [at_end, outside, review])
    limit, why = br.learned_limit("test", str(tmp_path))
    assert limit == 2400 and outside["id"] in why and at_end["id"] not in why, (limit, why)


def test_r079_learned_limit_row_at_review_start_with_suffix(program, tmp_path):
    """R-079: a suffixed id at the review start is inside the review run and teaches nothing."""
    br = program("bridge-run")
    review = {"id": "2026-10-07T10:00:00Z", "kind": "review", "seconds": 1200, "exit": 0, "healthy": True}
    inside = {"id": "2026-10-07T10:00:00Z-2", "kind": "test", "seconds": 3000, "exit": 0, "healthy": True}
    outside = {"id": "2026-10-07T12:00:00Z", "kind": "test", "seconds": 1600, "exit": 0, "healthy": True}
    _write_learn_rows(tmp_path, [inside, outside, review])
    limit, why = br.learned_limit("test", str(tmp_path))
    assert limit == 2400 and outside["id"] in why, (limit, why)


@pytest.mark.parametrize("seconds", ["600", True, -1, "NaN", "1e400"])
def test_r079_learned_limit_bad_review_seconds_ignores_nothing(program, tmp_path, seconds):
    """R-079: a review row with no valid end does not exclude other rows (including at the review start)."""
    br = program("bridge-run")
    at_start = {"id": "2026-10-07T10:00:00Z-2", "kind": "test", "seconds": 2500, "exit": 0, "healthy": True}
    inside = {"id": "2026-10-07T10:05:00Z", "kind": "test", "seconds": 2000, "exit": 0, "healthy": True}
    if seconds in ("NaN", "1e400"):
        launcher = tmp_path / "run" / "launcher"
        launcher.mkdir(parents=True, exist_ok=True)
        review = '{"id": "2026-10-07T10:00:00Z", "kind": "review", "seconds": %s, "exit": 0, "healthy": true}\n' % seconds
        (launcher / "runs.jsonl").write_text(
            "\n".join(json.dumps(r) for r in [at_start, inside]) + "\n" + review, encoding="utf-8")
    else:
        review = {"id": "2026-10-07T10:00:00Z", "kind": "review", "seconds": seconds, "exit": 0, "healthy": True}
        _write_learn_rows(tmp_path, [at_start, inside, review])
    limit, why = br.learned_limit("test", str(tmp_path))
    assert at_start["id"] in why, (limit, why)


def test_r079_learned_limit_non_launcher_id_still_teaches(program, tmp_path):
    """R-079: a row whose id is not the launcher's form is taught as today."""
    br = program("bridge-run")
    row = {"id": "not-a-stamp", "kind": "test", "seconds": 2000, "exit": 0, "healthy": True}
    review = {"id": "2026-10-07T10:00:00Z", "kind": "review", "seconds": 1200, "exit": 0, "healthy": True}
    _write_learn_rows(tmp_path, [row, review])
    limit, why = br.learned_limit("test", str(tmp_path))
    assert limit == 3000 and row["id"] in why, (limit, why)


def test_r079_learned_limit_review_kind_keeps_learning(program, tmp_path):
    """R-079: the review kind still learns from its own healthy rows."""
    br = program("bridge-run")
    long = {"id": "2026-10-07T11:00:00Z", "kind": "review", "seconds": 4000, "exit": 0, "healthy": True}
    _write_learn_rows(tmp_path, [long])
    limit, why = br.learned_limit("review", str(tmp_path))
    assert limit > br.KINDS["review"] and long["id"] in why, (limit, why)


# ---------------------------------------------------------------- R-081 git config detection


def _r081_repo(tmp_path):
    ws = tmp_path / "proj" / "Workspace"
    ws.mkdir(parents=True)
    (ws / "run").mkdir()
    for args in (
        ["init", "-q"],
        ["config", "user.email", "test@example.invalid"],
        ["config", "user.name", "test"],
        ["config", "commit.gpgsign", "false"],
    ):
        p = subprocess.run(["git", "-C", str(ws)] + args, capture_output=True, text=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
        assert p.returncode == 0, p.stderr
    (ws / "a.txt").write_text("a\n", encoding="utf-8")
    p = subprocess.run(["git", "-C", str(ws), "add", "a.txt"], capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 0, p.stderr
    p = subprocess.run(["git", "-C", str(ws), "commit", "-q", "-m", "init"], capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 0, p.stderr
    return ws


def _r081_env(tmp_path, **extra):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = dict(os.environ)
    env.update(HOME=str(home), USERPROFILE=str(home), LOCALAPPDATA=str(tmp_path / "localappdata"),
               BRIDGE_RUN_ALLOW_ANY="1", GIT_CEILING_DIRECTORIES=str(tmp_path))
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        env.pop(name, None)
    env.update(extra)
    return env


def test_r081_limit_path_prints_git_config_before_exit_124(tmp_path):
    """R-081: on the limit path a test run that changed `.git/config` prints `.git/config changed` before `bridge-run: exit 124`."""
    import re
    line = re.compile(r"^bridge-run: GIT-CONFIG (.+) (new|removed|changed|unreadable)$")
    ws = _r081_repo(tmp_path)
    code = (
        "import pathlib, time, sys\n"
        "pathlib.Path('.git/config').write_text(\n"
        "    pathlib.Path('.git/config').read_text(encoding='utf-8')\n"
        "    + '\\n\\tfsmonitor = echo limit\\n', encoding='utf-8')\n"
        "time.sleep(30)\n"
        "sys.exit(0)\n"
    )
    p = subprocess.run([sys.executable, PROG, "--limit", "5", "--kind", "test", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=_r081_env(tmp_path), cwd=str(ws),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 124, p.stderr
    lines = [m.group(1).replace("\\", "/") + " " + m.group(2)
             for m in (line.match(x) for x in p.stderr.splitlines()) if m]
    assert lines == [".git/config changed"], p.stderr
    assert p.stderr.splitlines()[-1] == "bridge-run: exit 124", p.stderr


def test_r081_child_exit_124_still_prints_git_config_hook_new(tmp_path):
    """R-081: a child that exits 124 within its limit after adding a hook prints that hook's `new` line (no exit line)."""
    import re
    line = re.compile(r"^bridge-run: GIT-CONFIG (.+) (new|removed|changed|unreadable)$")
    ws = _r081_repo(tmp_path)
    code = (
        "import pathlib, sys\n"
        "pathlib.Path('.git/hooks/post-commit').write_text('exit 0' + chr(10))\n"
        "sys.exit(124)\n"
    )
    p = subprocess.run([sys.executable, PROG, "--limit", "60", "--kind", "test", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=_r081_env(tmp_path), cwd=str(ws),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 124, p.stderr
    git_lines = sorted(m.group(1).replace("\\", "/") + " " + m.group(2)
                       for m in (line.match(x) for x in p.stderr.splitlines()) if m)
    assert git_lines == [".git/hooks/post-commit new"], p.stderr
    assert "bridge-run: exit" not in p.stderr, p.stderr


def test_r081_hook_without_hooks_path_one_line(tmp_path):
    """R-081: without `core.hooksPath`, a hook added gives exactly one GIT-CONFIG line (hooks folder read once)."""
    import re
    line = re.compile(r"^bridge-run: GIT-CONFIG (.+) (new|removed|changed|unreadable)$")
    ws = _r081_repo(tmp_path)
    code = "import pathlib\npathlib.Path('.git/hooks/pre-commit').write_text('#!/bin/sh' + chr(10))"
    p = subprocess.run([sys.executable, PROG, "--limit", "60", "--kind", "test", "--", sys.executable, "-c", code],
                       capture_output=True, text=True, env=_r081_env(tmp_path), cwd=str(ws),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 0, p.stderr
    git_lines = sorted(m.group(1).replace("\\", "/") + " " + m.group(2)
                       for m in (line.match(x) for x in p.stderr.splitlines()) if m)
    assert git_lines == [".git/hooks/pre-commit new"], p.stderr


def test_r081_refused_driver_prints_no_git_config(tmp_path):
    """R-081: a refused driver run makes no GIT-CONFIG line; the refused program would plant a hook under run/supervisor/."""
    import re
    line = re.compile(r"^bridge-run: GIT-CONFIG (.+) (new|removed|changed|unreadable)$")
    ws = _r081_repo(tmp_path)
    plant = "import pathlib\npathlib.Path('.git/hooks/post-merge').write_text('exit 0' + chr(10))"
    config_before = (ws / ".git" / "config").read_bytes()
    rogue = ws / "rogue.py"
    rogue.write_text(plant, encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, "--limit", "60", "--kind", "driver", "--", "python", str(rogue)],
                       capture_output=True, text=True, env=_r081_env(tmp_path), cwd=str(ws),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert p.returncode == 125, p.stderr
    assert "GIT-CONFIG" not in p.stderr, p.stderr
    assert not (ws / ".git" / "hooks" / "post-merge").exists()
    assert (ws / ".git" / "config").read_bytes() == config_before
    prog = ws / "run" / "supervisor" / "plant.py"
    prog.parent.mkdir(parents=True, exist_ok=True)
    prog.write_text(plant, encoding="utf-8")
    ok = subprocess.run([sys.executable, PROG, "--limit", "60", "--kind", "driver", "--", "python", str(prog)],
                        capture_output=True, text=True, env=_r081_env(tmp_path), cwd=str(ws),
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=120)
    assert ok.returncode == 0, ok.stderr
    git_lines = sorted(m.group(1).replace("\\", "/") + " " + m.group(2)
                       for m in (line.match(x) for x in ok.stderr.splitlines()) if m)
    assert git_lines == [".git/hooks/post-merge new"], ok.stderr


# ---------------------------------------------------------------- R-085, the wait before a CI watch (D-004)


def test_r085_d004_a_watch_with_no_pull_request_number_starts_without_the_wait(tmp_path, monkeypatch, capsys, program):
    """R-085, D-004: the word after checks is not a pull-request number, so nothing is read and the watch is started as given."""
    import test_program_watch_wait as wait

    case = wait.Case(tmp_path, monkeypatch, capsys, program)
    argv = ["gh", "pr", "checks", "--watch", "--required"]
    rc = case.run([wait.GREEN], argv=argv, limit=600)
    assert rc == 0, case.err
    assert case.watch.calls == [(argv, 600)], case.watch.calls
    assert case.calls() == [], case.calls()
    assert case.lines() == ["bridge-run: the watch names no pull request number; it starts without the wait"], case.err


def test_r085_d004_every_completed_run_after_a_watch_prints_that_the_exit_stands(tmp_path, monkeypatch, capsys, program):
    """R-085, D-004: where no list could be named and the watch returns 0 with every latest run completed, that exit stands."""
    import test_program_watch_wait as wait

    case = wait.Case(tmp_path, monkeypatch, capsys, program)
    rc = case.run([dict(wait.NONE_ANYWHERE, **wait.GREEN)], exits=(0,))
    assert rc == 0 and len(case.started()) == 1 and case.polls() == 2, case.err
    line = "bridge-run: every latest workflow run of head %s is completed; the watch's exit 0 stands" % case.head[:12]
    assert line in case.lines(), case.err


def test_r085_d004_the_limit_stops_the_wait_before_a_later_green_head(tmp_path, monkeypatch, capsys, program):
    """R-085, D-004: the run's limit ends the wait, so a head that would pass only on a later poll is not watched."""
    import test_program_watch_wait as wait

    case = wait.Case(tmp_path, monkeypatch, capsys, program)
    rc = case.run([dict(checks="wait-checks-floor-only.json", runs="wait-runs-in-progress.json"), wait.GREEN], limit=10)
    assert rc == 124 and case.started() == [], case.err
    assert case.polls() == 1, case.calls()
    assert any(l.startswith("bridge-run: LIMIT") for l in case.lines()), case.err


@pytest.mark.parametrize("extra", [["--repo", "octo/other"], ["-Rocto/other"]], ids=["repo-before-number", "R-joined-before-number"])
def test_r085_d004_a_repository_named_before_the_pull_request_number_starts_without_the_wait(tmp_path, monkeypatch, capsys, program, extra):
    """R-085, D-004: --repo or a joined -R before the number is the repository line, and nothing is read from GitHub."""
    import test_program_watch_wait as wait

    case = wait.Case(tmp_path, monkeypatch, capsys, program)
    argv = ["gh", "pr", "checks"] + extra + ["12", "--watch", "--required"]
    rc = case.run([wait.GREEN], argv=argv, limit=600)
    assert rc == 0, case.err
    assert case.watch.calls == [(argv, 600)], case.watch.calls
    assert case.calls() == [], case.calls()
    assert case.lines() == ["bridge-run: the watch names another repository; it starts without the wait"], case.err


def test_r085_d004_a_repository_flag_without_watch_runs_as_given(tmp_path, monkeypatch, capsys, program):
    """R-085, D-004: without --watch a --repo word is not the wait's repository line; the command runs as given."""
    import test_program_watch_wait as wait

    case = wait.Case(tmp_path, monkeypatch, capsys, program)
    argv = ["gh", "pr", "checks", "12", "--repo", "octo/other"]
    rc = case.run([wait.GREEN], argv=argv, limit=600)
    assert rc == 0, case.err
    assert case.watch.calls == [(argv, 600)], case.watch.calls
    assert case.calls() == [] and case.lines() == [], (case.calls(), case.err)


def test_r085_d004_no_time_left_names_the_local_head_and_reads_nothing(tmp_path, monkeypatch, capsys, program):
    """R-085, D-004: limit 0 reads nothing from GitHub and names the pushed head, not a failed poll and not ?."""
    import test_program_watch_wait as wait

    case = wait.Case(tmp_path, monkeypatch, capsys, program)
    rc = case.run([wait.GREEN], limit=0)
    assert rc == 124 and case.started() == [] and case.calls() == [], case.err
    limit_lines = [l for l in case.lines() if l.startswith("bridge-run: LIMIT")]
    assert len(limit_lines) == 1 and "on head %s" % case.head[:12] in limit_lines[0], case.err
    assert "no time left before the first poll" in limit_lines[0] and "poll failed" not in limit_lines[0], case.err


def test_r085_d004_no_time_left_and_no_local_head_names_the_question_mark(tmp_path, monkeypatch, capsys, program):
    """R-085, D-004: limit 0 reads no GitHub reply, and a head the checkout cannot name is shown as ?."""
    import test_program_watch_wait as wait

    folder = tmp_path / "not-a-checkout"
    folder.mkdir()
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    case = wait.Case(tmp_path, monkeypatch, capsys, program)
    rc = case.run([wait.GREEN], limit=0, folder=str(folder))
    assert rc == 124 and case.started() == [] and case.calls() == [], case.err
    limit_lines = [l for l in case.lines() if l.startswith("bridge-run: LIMIT")]
    assert len(limit_lines) == 1 and "on head ?" in limit_lines[0] and "no time left before the first poll" in limit_lines[0], case.err
    assert not any("poll failed" in l for l in case.lines()), case.err


def test_r085_d004_a_ready_poll_past_the_limit_names_the_reading_it_would_have_started_for(tmp_path, monkeypatch, capsys, program):
    """R-085, D-004: a poll that finds the head ready after the limit is spent names that reading and does not say the watch starts."""
    import test_program_watch_wait as wait

    case = wait.Case(tmp_path, monkeypatch, capsys, program)
    read = case.br.bridge_env.head_state

    def slow(*args, **kwargs):
        got = read(*args, **kwargs)
        case.clock.now += 40
        return got

    monkeypatch.setattr(case.br.bridge_env, "head_state", slow)
    rc = case.run([wait.GREEN], limit=30)
    assert rc == 124 and case.started() == [], case.err
    assert not any("the watch starts" in l for l in case.lines()), case.err
    left = "ready (every required context has a check or a status), but no time left to start the watch"
    limit_lines = [l for l in case.lines() if l.startswith("bridge-run: LIMIT")]
    assert len(limit_lines) == 1 and left in limit_lines[0] and "poll failed" not in limit_lines[0], case.err
