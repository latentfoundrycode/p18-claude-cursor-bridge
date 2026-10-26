"""Release 2026.10.11c, the report cycle's program items: each test fails on 2026.10.11b."""
import inspect
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_conformance_check import make_workspace, run as run_conf, verdict  # noqa: E402
from test_evaluate_reports import ISSUES, common, project, run as run_eval  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CB = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")


def test_the_pr_activity_check_reads_gh_as_utf8(program):
    pac = program("pr-activity-check")
    assert 'encoding="utf-8"' in inspect.getsource(pac.gh) and 'errors="replace"' in inspect.getsource(pac.gh), "a cp1252 console crashed on one character (item 1)"


def test_a_wrapper_marked_wake_builder_gets_the_builders_ceiling(program):
    import time as t
    lg = program("loop-guard")
    assert lg.command_ceiling("python run/tools/delegate_pg.py TASK-059 # wake builder") == 7200
    assert lg.command_ceiling("python run/tools/review_pg.py 010c # wake review") == 3600
    assert lg.command_ceiling("python run/tools/suite.sh # wake") == 1800
    now = t.time()
    wrapper = {"id": "w1", "type": "shell", "status": "running", "description": "delegate", "command": "python run/tools/delegate_pg.py TASK-059 # wake builder", "started_at": int((now - 3000) * 1000)}
    pending, _ = lg.pending_from_hook({"background_tasks": [wrapper], "session_crons": []}, now, ".")
    assert "background command w1" in pending, "a wrapper marked # wake builder counts under the builder's ceiling (item 2): " + str(pending)
    plain = dict(wrapper, command="python run/tools/suite.sh # wake")
    pending, _ = lg.pending_from_hook({"background_tasks": [plain], "session_crons": []}, now, ".")
    assert not pending, "a plain # wake past its 1800 s no longer counts"


def test_bridge_stop_ends_a_launcher_run_and_its_tree(tmp_path):
    (tmp_path / "run").mkdir()
    launcher = os.path.join(CB, "bridge-run.py")
    # built here, not at import: the launcher's heavy-run slot lives under the home, and the
    # tests' temporary home (conftest.py's home_of_the_tests) is set only once the test runs (TASK-029)
    env_now = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    env = dict(env_now, BRIDGE_RUN_ALLOW_ANY="1")
    p = subprocess.Popen([sys.executable, launcher, "--limit", "120", "--kind", "test", "--", sys.executable, "-c", "import time; time.sleep(100)"],
                         cwd=str(tmp_path), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    child_pid = None
    try:
        pid_dir = tmp_path / "run" / "launcher" / "pids"
        for _ in range(40):
            if pid_dir.exists() and list(pid_dir.iterdir()):
                break
            time.sleep(0.25)
        files = list(pid_dir.iterdir()) if pid_dir.exists() else []
        assert files, "the launcher writes its pid file while it runs (item 4)"
        run_id = files[0].name
        launcher_pid, child_pid = (int(x) for x in files[0].read_text(encoding="utf-8").split())
        assert launcher_pid == p.pid
        lock = os.path.join(os.environ["USERPROFILE"], ".cursor-bridge", "heavy.lock")
        assert os.path.exists(lock), "the launcher's slot is under the tests' temporary home, so this test never touches the owner's"
        q = subprocess.run([sys.executable, os.path.join(CB, "bridge-stop.py"), run_id[:10]], cwd=str(tmp_path), capture_output=True, text=True, env=env_now)
        assert q.returncode == 0 and "ended" in q.stdout, q.stdout + q.stderr
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            raise AssertionError("the launcher survived bridge-stop")
        stop = subprocess.run([sys.executable, os.path.join(CB, "bridge-stop.py"), "--pid", str(child_pid)], capture_output=True, text=True, env=env_now)
        assert "is not running" in stop.stdout, "the child is gone with its tree: " + stop.stdout
    finally:
        if child_pid is not None and sys.platform != "win32":
            try:
                os.kill(child_pid, 9)              # off Windows no Job ends the child with the launcher; first, since it holds the pipes
            except OSError:
                pass
        if p.poll() is None:
            p.kill()
        p.communicate(timeout=10)                  # waits for the launcher and closes its pipes


def test_the_credential_helper_is_reset_in_the_bridges_git_config_file(program, tmp_path):
    be = program("bridge_env")
    home = tmp_path / "home"
    (home / ".cursor").mkdir(parents=True)
    (home / ".gitconfig").write_text("[user]\n\tname = owner\n", encoding="utf-8")
    out = be.stripped_env({"PATH": os.environ.get("PATH", ""), "USERPROFILE": str(home), "HOME": str(home), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")})
    path = out["GIT_CONFIG_GLOBAL"]
    text = open(path, encoding="utf-8").read()
    assert path.replace("\\", "/").endswith("/.cursor-bridge/gitconfig") and "\thelper =\n" in text and "[include]" in text, text
    assert "GIT_CONFIG_VALUE_0" not in out and "GIT_CONFIG_COUNT" not in out
    p = subprocess.run(["git", "config", "--global", "--get-all", "credential.helper"], capture_output=True, text=True, env=out)
    assert p.stdout.strip() == "", "git reads an empty helper list from the file: " + p.stdout
    p = subprocess.run(["git", "config", "--get", "user.name"], capture_output=True, text=True, env=out, cwd=str(tmp_path))
    assert p.stdout.strip() == "owner", "the owner's global config is included (a normal lookup follows the include; `--global --list` shows the key only): " + p.stdout
    assert out["GIT_CONFIG_PARAMETERS"] == "'credential.helper='"
    repo = tmp_path / "repo"
    repo.mkdir()
    marker = "!f() { echo username=MARKER; echo password=x; }; f"       # a helper a builder could write into the checkout's own config
    for args in (["init", "-q"], ["config", "credential.helper", marker]):
        subprocess.run(["git"] + args, cwd=str(repo), check=True, env=ENV)
    ask = "protocol=https\nhost=example.invalid\n\n"
    control = dict(out)
    control.pop("GIT_CONFIG_PARAMETERS")
    p = subprocess.run(["git", "credential", "fill"], input=ask, capture_output=True, text=True, env=control, cwd=str(repo))
    assert "MARKER" in p.stdout, "the control: without the parameter the local helper answers: " + p.stdout + p.stderr
    p = subprocess.run(["git", "credential", "fill"], input=ask, capture_output=True, text=True, env=out, cwd=str(repo))
    assert "MARKER" not in p.stdout, "a helper written into the checkout's own config is reset by GIT_CONFIG_PARAMETERS (review of 11c, M1): " + p.stdout + p.stderr


def test_bridge_stop_refuses_an_ended_run_and_removes_a_stale_pid_file(tmp_path):
    (tmp_path / "run" / "launcher" / "pids").mkdir(parents=True)
    (tmp_path / "run" / "launcher" / "runs.jsonl").write_text(json.dumps({"id": "2026-10-11T10:00:00Z", "kind": "test", "head": "python", "pid": 999999, "child_pid": 999998, "limit": 60, "seconds": 3, "exit": 0, "healthy": True}) + "\n", encoding="utf-8")
    q = subprocess.run([sys.executable, os.path.join(CB, "bridge-stop.py"), "2026-10-11T10"], cwd=str(tmp_path), capture_output=True, text=True, env=ENV)
    assert q.returncode == 2 and "has ended" in q.stdout, "an ended run is never killed by its old pid (review of 11c, M2): " + q.stdout
    stale = tmp_path / "run" / "launcher" / "pids" / "2026-10-11T11-00-00Z"
    stale.write_text("999999 999998\n", encoding="utf-8")
    q = subprocess.run([sys.executable, os.path.join(CB, "bridge-stop.py"), "2026-10-11T11"], cwd=str(tmp_path), capture_output=True, text=True, env=ENV)
    assert q.returncode == 2 and "stale" in q.stdout and not stale.exists(), "a stale pid file is removed, nothing is ended: " + q.stdout


def test_refactor_check_budget_and_test_file_rule(tmp_path):
    r = tmp_path / "ws"
    (r / "src").mkdir(parents=True)
    (r / "tests").mkdir()
    (r / "handoff").mkdir()
    (r / "src" / "test_runner.py").write_text("X = 1\n", encoding="utf-8")       # a product module named like a test
    (r / "src" / "a.py").write_text("A = 1\n", encoding="utf-8")
    (r / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    (r / "handoff" / "REFAC-001.md").write_text("brief\n", encoding="utf-8")
    for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "base"]):
        subprocess.run(["git"] + args, cwd=str(r), check=True, env=ENV)
    (r / "src" / "test_runner.py").write_text("X = 2\n", encoding="utf-8")
    (r / "handoff" / "REFAC-001.md").write_text("brief\n" + "line\n" * 500, encoding="utf-8")
    p = subprocess.run([sys.executable, os.path.join(CB, "refactor-check.py"), "HEAD", "--max-lines", "100"], cwd=str(r), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0 and "PURE" in p.stdout, "handoff lines are not product change, and src/test_runner.py is product (item 6): " + p.stdout
    (r / "tests" / "test_a.py").write_text("def test_a():\n    assert 1\n", encoding="utf-8")
    p = subprocess.run([sys.executable, os.path.join(CB, "refactor-check.py"), "HEAD"], cwd=str(r), capture_output=True, text=True, env=ENV)
    assert p.returncode == 1 and "tests/test_a.py" in p.stdout


def test_conformance_reads_sockets_npm_pin_and_a_fixture_folder(tmp_path):
    make_workspace(tmp_path)
    wf_dir = tmp_path / ".github" / "workflows"
    for wf in wf_dir.glob("*.yml"):
        text = wf.read_text(encoding="utf-8")
        lines = text.splitlines()
        out = []
        for l in lines:
            if "socket" in l.lower() and "run:" in l:
                indent = l[:len(l) - len(l.lstrip())]
                out.append(indent + "run: npm install -g @socketsecurity/cli@1.2.3")
                out.append(indent + "run: socket scan create .")
            else:
                out.append(l)
        wf.write_text("\n".join(out) + "\n", encoding="utf-8")
    rc, out = run_conf(tmp_path)
    assert verdict(out, "Socket in the gate")[0] == "OK" and verdict(out, "Socket version pinned")[0] is None, "the pin in `npm install -g @socketsecurity/cli@<version>` (item 7): " + out
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "llm.py").write_text('import httpx2\nURL = "https://openrouter.ai/api/v1"\n', encoding="utf-8")
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "tests" / "helpers.py").write_text('def load_contract(name):\n    return open("tests/fixtures/openrouter_contract/" + name).read()\n', encoding="utf-8")
    (tmp_path / "tests" / "test_llm.py").write_text("from app import llm\nfrom tests.helpers import load_contract\n\ndef test_llm_replays():\n    assert load_contract('ask.json')\n", encoding="utf-8")
    rc, out = run_conf(tmp_path)
    assert verdict(out, "Adapters tested against recorded replies")[0] == "OK", "a fixture folder loaded through a helper is evidence (item 7): " + out


def test_a_bare_stage_heading_is_not_an_entry_and_a_cut_entry_says_so(tmp_path):
    feedback = "# Thing — Claude-Cursor Bridge Feedback\n\n## Stage 2 (2026-10-05)\n\n2026-10-05\n\n## Stage 3\n\n" + ("A long entry. " * 600) + "\n"
    root = project(tmp_path, feedback)
    rc, out = run_eval(tmp_path, "collect", "--out", str(tmp_path / "out"), *common(tmp_path, root))
    assert rc == 0 and "Thing feedback: 1 entries" in out, "a heading with a date line only is not an entry (item 8): " + out
    text = (tmp_path / "out" / "unprocessed.md").read_text(encoding="utf-8")
    assert "[cut at 6,000 characters; the document holds the rest]" in text, "a cut entry says so (item 8)"
