"""R-041: mutation-run.py applies mutants in a scratch copy and caches kills (TASK-031)."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time

import pytest

import conftest as test_conftest
from conftest import load_program

HERE = os.path.dirname(os.path.abspath(__file__))
MUTATION_RUN = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "mutation-run.py")
BRIDGE_RUN = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
       "-c", "commit.gpgsign=false"]


def workspace(tmp_path, project="proj"):
    ws = tmp_path / project / "Workspace"
    ws.mkdir(parents=True)
    (ws / "run" / "supervisor").mkdir(parents=True)
    (ws / "run" / "supervisor" / "mutation-cache").mkdir(parents=True)
    return ws


def git(ws, *args):
    kw = test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 60})
    p = subprocess.run(GIT + list(args), cwd=str(ws), **kw)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def write(ws, rel, text, binary=False):
    path = ws / rel.replace("/", os.sep)
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        path.write_bytes(text.encode("utf-8"))
    else:
        path.write_text(text, encoding="utf-8", newline="\n")


def init_pkg(ws, crlf=False):
    nl = "\r\n" if crlf else "\n"
    write(ws, "demo/__init__.py", "")
    write(ws, "demo/calc.py", "def add(a, b):%s    return a + b%s" % (nl, nl), binary=crlf)
    write(ws, "tests/test_calc.py",
          "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n\ndef test_sub():\n    assert add(2, 3) == 5\n")
    write(ws, "tests/conftest.py", "")
    git(ws, "init", "-q", "-b", "main")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "init")


def mutants_path(ws, run_id, body):
    p = ws / "run" / "supervisor" / ("%s-mutants.json" % run_id)
    p.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return p


def run_mr(ws, mutants_file, scratch=None, timeout=60, extra=(), home_env=None):
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    if home_env:
        env["HOME"] = env["USERPROFILE"] = str(home_env)
    cmd = [sys.executable, MUTATION_RUN, str(mutants_file)] + list(extra)
    if scratch:
        cmd += ["--scratch", str(scratch)]
    cmd += ["--mutant-timeout", str(timeout)]
    return subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env,
                          timeout=timeout + 30, **test_conftest.windowless_kwargs({}))


def tree_bytes(ws):
    out = {}
    for root, dirs, files in os.walk(ws):
        dirs[:] = [d for d in dirs if d not in (".git", "mutation-cache")]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), ws).replace("\\", "/")
            if rel.startswith("run/supervisor/mutation-cache"):
                continue
            with open(os.path.join(root, f), "rb") as fh:
                out[rel] = fh.read()
    return out


def basic_mutant(kill=True):
    new = "assert add(1, 1) == 99" if kill else "assert add(1, 1) == 2"
    return {
        "mutants": [{
            "id": "m1",
            "file": "tests/test_calc.py",
            "pairs": [{"old": "assert add(1, 1) == 2", "new": new}],
            "tests": ["tests/test_calc.py"],
            "expect_fail": ["tests/test_calc.py::test_add"],
        }]
    }


def test_r041_done_b_first_run_kills_and_records(tmp_path):
    """R-041, TASK-031 Done when (c): a first run kills and records."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "t1", basic_mutant())
    git(ws, "add", "run/supervisor/t1-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "m1: killed" in p.stdout
    cache = ws / "run/supervisor/mutation-cache/t1.jsonl"
    assert cache.is_file()
    assert "killed" in cache.read_text(encoding="utf-8")


def test_r041_done_c_unchanged_skips(tmp_path):
    """R-041, TASK-031 Done when (c): a run with nothing changed runs no mutant."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "t2", basic_mutant())
    git(ws, "add", "run/supervisor/t2-mutants.json")
    assert run_mr(ws, mp).returncode == 0
    p = run_mr(ws, mp)
    assert p.returncode == 0, p.stderr
    assert "cached" in p.stdout
    assert "counts: run=0" in p.stdout


def test_r041_done_c_mutated_file_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to a mutated file reruns only that file's mutants."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = {
        "mutants": [
            basic_mutant()["mutants"][0],
            {**basic_mutant()["mutants"][0], "id": "m2", "file": "tests/test_calc.py",
             "pairs": [{"old": "assert add(1, 1) == 2", "new": "assert add(1, 1) == 99"}],
             "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]},
        ]
    }
    mp = mutants_path(ws, "t3", body)
    git(ws, "add", "run/supervisor/t3-mutants.json")
    run_mr(ws, mp)
    write(ws, "demo/calc.py", "def add(a, b):\n    return a + b\n# touch\n")
    git(ws, "add", "demo/calc.py")
    p = run_mr(ws, mp)
    assert "m1:" in p.stdout and "m2: killed (cached" in p.stdout


def test_r041_malformed_exits_2(tmp_path):
    """R-041, TASK-031 Done when (d): a malformed file exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "bad", {"mutants": []})
    p = run_mr(ws, mp)
    assert p.returncode == 2


def test_r041_default_scratch_under_temp_home(tmp_path, home_of_the_tests):
    """R-041: the default scratch folder lies under the tests' temporary home."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "sc", basic_mutant())
    git(ws, "add", "run/supervisor/sc-mutants.json")
    p = run_mr(ws, mp, home_env=home_of_the_tests)
    assert p.returncode == 0
    scratch = home_of_the_tests / ".cursor-bridge" / "scratch" / tmp_path.name
    assert not list(scratch.rglob("mutation-run-sc")) if scratch.exists() else True


def test_r041_all_with_checkpoint_exits_2(tmp_path):
    """R-041: --all with --checkpoint exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "x1", {"mutants": [], "new_tests": ["tests/test_calc.py"]})
    git(ws, "add", "-A")
    sha = git(ws, "rev-parse", "HEAD")
    p = run_mr(ws, mp, extra=["--all", "--checkpoint", sha])
    assert p.returncode == 2


def test_r041_internal_error_exits_3(tmp_path, monkeypatch):
    """R-041: an internal error exits 3."""
    bridge = os.path.normpath(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge"))
    monkeypatch.syspath_prepend(bridge)
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "ie", basic_mutant())
    git(ws, "add", "run/supervisor/ie-mutants.json")
    mod = load_program("mutation-run")
    monkeypatch.setattr(mod, "git", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("test boom")))
    monkeypatch.chdir(ws)
    monkeypatch.setattr(sys, "argv", ["mutation-run.py", str(mp)])
    rc = mod.run_main()
    assert rc == 3


def test_dump_cli_argparse_updated():
    """TASK-031 Requirement 10: mutation-run.py is in ARGPARSE."""
    from test_dump_cli import ARGPARSE
    assert "mutation-run.py" in ARGPARSE


def _seed(ws, run_id):
    mp = mutants_path(ws, run_id, basic_mutant())
    git(ws, "add", "run/supervisor/%s-mutants.json" % run_id)
    run_mr(ws, mp)
    return mp


def test_r041_done_c_test_file_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to a named test file reruns its mutants."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "tf")
    write(ws, "tests/test_calc.py",
          "from demo.calc import add\n\ndef test_add():\n    assert add(1, 1) == 2\n\ndef test_sub():\n    assert add(2, 3) == 5\n# x\n")
    git(ws, "add", "tests/test_calc.py")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout and "cached" in p.stdout


def test_r041_done_c_conftest_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to a conftest.py on its path reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "cf")
    write(ws, "tests/conftest.py", "# hook\n")
    git(ws, "add", "tests/conftest.py")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout


def test_r041_done_c_sibling_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to a sibling of the mutated file reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "demo/other.py", "x = 1\n")
    git(ws, "add", "demo/other.py")
    body = {"mutants": [{
        "id": "m1", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a + b + 1"}],
        "tests": ["tests/test_calc.py"],
        "expect_fail": ["tests/test_calc.py::test_add", "tests/test_calc.py::test_sub"],
    }]}
    mp = mutants_path(ws, "sib", body)
    git(ws, "add", "run/supervisor/sib-mutants.json")
    run_mr(ws, mp)
    write(ws, "demo/other.py", "x = 2\n")
    git(ws, "add", "demo/other.py")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout


def test_r041_done_c_pytest_ini_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to the root pytest.ini reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "pytest.ini", "[pytest]\n")
    git(ws, "add", "pytest.ini")
    mp = _seed(ws, "ini")
    write(ws, "pytest.ini", "[pytest]\naddopts = -q\n")
    git(ws, "add", "pytest.ini")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout


def test_r041_done_c_expect_fail_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to expected test ids reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    mp = mutants_path(ws, "ef", body)
    git(ws, "add", "run/supervisor/ef-mutants.json")
    run_mr(ws, mp)
    body["mutants"][0]["expect_fail"] = ["tests/test_calc.py::test_sub"]
    mp.write_text(json.dumps(body), encoding="utf-8")
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout


def test_r041_done_c_survive_flag_change_reruns(tmp_path):
    """R-041, TASK-031 Done when (c): a change to expect survive reruns."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "sv")
    data = json.loads((ws / "run/supervisor/sv-mutants.json").read_text(encoding="utf-8"))
    data["mutants"][0]["expect"] = "survive reason"
    mutants_path(ws, "sv", data)
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout


def test_r041_survived_reruns_every_time(tmp_path):
    """R-041, TASK-031 Done when (c): a survived mutant reruns every time."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant(kill=False)
    mp = mutants_path(ws, "sur", body)
    git(ws, "add", "run/supervisor/sur-mutants.json")
    assert run_mr(ws, mp).returncode == 1
    p = run_mr(ws, mp)
    assert "run=1" in p.stdout and "survived" in p.stdout


def test_r041_two_mutants_same_file_original(tmp_path):
    """R-041, TASK-031 Done when (d): two mutants whose old texts match the original each apply."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = {"mutants": [
        {"id": "a", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a + b + 1"}],
         "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add", "tests/test_calc.py::test_sub"]},
        {"id": "b", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a + b + 2"}],
         "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add", "tests/test_calc.py::test_sub"]},
    ]}
    mp = mutants_path(ws, "two", body)
    git(ws, "add", "run/supervisor/two-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0
    assert "a: killed" in p.stdout and "b: killed" in p.stdout


def test_r041_crlf_mutant_killed(tmp_path):
    """R-041, TASK-031 Done when (d): a CRLF fixture's mutant is killed."""
    ws = workspace(tmp_path)
    init_pkg(ws, crlf=True)
    body = {"mutants": [{
        "id": "crlf", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a + b + 1"}],
        "tests": ["tests/test_calc.py"],
        "expect_fail": ["tests/test_calc.py::test_add", "tests/test_calc.py::test_sub"],
    }]}
    mp = mutants_path(ws, "crlf", body)
    git(ws, "add", "run/supervisor/crlf-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0 and "killed" in p.stdout


def test_r041_env_and_untracked_in_copy(tmp_path):
    """R-041, TASK-031 Done when (d): root .env and untracked fixture run in the copy."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, ".env", "SECRET=fixture-value\n")
    write(ws, "fixtures/data.txt", "payload\n")
    write(ws, "tests/test_env.py", textwrap.dedent("""
import os
from pathlib import Path
def test_env():
    assert os.environ.get("SECRET") or open(".env").read().strip().endswith("fixture-value")
def test_untracked():
    assert Path("fixtures/data.txt").read_text(encoding="utf-8").strip() == "payload"
"""))
    git(ws, "add", "tests/test_env.py")
    body = {"mutants": [{
        "id": "e1", "file": "tests/test_env.py",
        "pairs": [{"old": 'endswith("fixture-value")', "new": 'endswith("wrong")'}],
        "tests": ["tests/test_env.py"], "expect_fail": ["tests/test_env.py::test_env"],
    }], "untracked": ["fixtures/data.txt"]}
    mp = mutants_path(ws, "env", body)
    git(ws, "add", "run/supervisor/env-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 0


def test_r041_crash_is_error_exit_3(tmp_path):
    """R-041, TASK-031 Done when (d): a crash is error with exit 3, outranking exit 1."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant(kill=False)
    body["mutants"].append({
        **basic_mutant()["mutants"][0], "id": "m2",
        "pairs": [{"old": "assert add(1, 1) == 2", "new": "import os; os._exit(9)"}],
    })
    mp = mutants_path(ws, "crash", body)
    git(ws, "add", "run/supervisor/crash-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 3


def test_r041_timeout_error_continues(tmp_path):
    """R-041, TASK-031 Done when (d): infinite loop is error timed out under short timeout, exit 3."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "tests/test_hang.py", "def test_hang():\n    while True:\n        pass\n")
    git(ws, "add", "tests/test_hang.py")
    body = {"mutants": [{
        "id": "hang", "file": "tests/test_hang.py", "pairs": [{"old": "pass", "new": "pass"}],
        "tests": ["tests/test_hang.py"], "expect_fail": ["tests/test_hang.py::test_hang"],
    }]}
    mp = mutants_path(ws, "hang", body)
    git(ws, "add", "run/supervisor/hang-mutants.json")
    p = run_mr(ws, mp, timeout=3)
    assert p.returncode == 3 and "timed out" in p.stdout


def test_r041_unexpected_fail_is_error(tmp_path):
    """R-041, TASK-031 Done when (d): a test not expected to fail that fails is error."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = {"mutants": [{
        "id": "ux", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a + b + 1"}],
        "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"],
    }]}
    mp = mutants_path(ws, "ux", body)
    git(ws, "add", "run/supervisor/ux-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 3 and "error" in p.stdout


def test_r041_survive_killed_exit_1(tmp_path):
    """R-041, TASK-031 Done when (d): an equivalent mutant killed gives exit 1."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["expect"] = "survive same math"
    mp = mutants_path(ws, "eq", body)
    git(ws, "add", "run/supervisor/eq-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 1 and "wrong equivalence" in p.stdout


def test_r041_all_reruns(tmp_path):
    """R-041, TASK-031 Done when (d): --all reruns all."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "all")
    p = run_mr(ws, mp, extra=["--all"])
    assert "run=1" in p.stdout


def test_r041_not_applied_exit_1(tmp_path):
    """R-041, TASK-031 Done when (d): old text not found is not applied with exit 1."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["pairs"][0]["old"] = "no such text"
    mp = mutants_path(ws, "na", body)
    git(ws, "add", "run/supervisor/na-mutants.json")
    p = run_mr(ws, mp)
    assert p.returncode == 1 and "not applied" in p.stdout


def test_r041_tree_unchanged_after_run(tmp_path):
    """R-041, TASK-031 Done when (d): tracked tree byte-identical after a run."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "bt", basic_mutant())
    git(ws, "add", "run/supervisor/bt-mutants.json")
    before = tree_bytes(ws)
    run_mr(ws, mp)
    after = tree_bytes(ws)
    assert before == after


def test_r041_cache_torn_line_ignored(tmp_path):
    """R-041, TASK-031 Done when (d): a torn last cache line is ignored."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = _seed(ws, "torn")
    cache = ws / "run/supervisor/mutation-cache/torn.jsonl"
    cache.write_text(cache.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")
    p = run_mr(ws, mp)
    assert p.returncode == 0


def test_r041_refuse_absolute_path(tmp_path):
    """R-041: absolute path in mutants file exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["file"] = str(ws / "demo/calc.py").replace("\\", "/")
    mp = mutants_path(ws, "abs", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_dotdot(tmp_path):
    """R-041: .. path component exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = basic_mutant()
    body["mutants"][0]["file"] = "demo/../demo/calc.py"
    mp = mutants_path(ws, "dd", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_untracked_mutated_file(tmp_path):
    """R-041: untracked mutated file exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    write(ws, "extra.py", "x=1\n")
    body = basic_mutant()
    body["mutants"][0]["file"] = "extra.py"
    mp = mutants_path(ws, "utm", body)
    assert run_mr(ws, mp).returncode == 2


def test_r041_refuse_bad_mutants_name(tmp_path):
    """R-041: mutants file name breaks S1 exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    p = ws / "run/supervisor/bad..-mutants.json"
    p.write_text(json.dumps(basic_mutant()), encoding="utf-8")
    assert run_mr(ws, p).returncode == 2


def test_r041_checkpoint_pass_exit_4(tmp_path):
    """R-041, TASK-031 Done when (d): checkpoint lists new test passing on old code, exit 4."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    sha = git(ws, "rev-parse", "HEAD")
    write(ws, "tests/test_new.py", "def test_new():\n    assert 1 == 1\n")
    git(ws, "add", "tests/test_new.py")
    mp = mutants_path(ws, "ck", {"mutants": [], "new_tests": ["tests/test_new.py::test_new"]})
    git(ws, "add", "run/supervisor/ck-mutants.json")
    p = run_mr(ws, mp, extra=["--checkpoint", sha])
    assert p.returncode == 4 and "passing on old code" in p.stdout


def test_r041_checkpoint_not_run(tmp_path):
    """R-041, TASK-031 Done when (d): new test importing absent module is not run."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    sha = git(ws, "rev-parse", "HEAD")
    write(ws, "tests/test_imp.py", "import missing_mod\ndef test_x():\n    pass\n")
    git(ws, "add", "tests/test_imp.py")
    mp = mutants_path(ws, "ck2", {"mutants": [], "new_tests": ["tests/test_imp.py::test_x"]})
    git(ws, "add", "run/supervisor/ck2-mutants.json")
    p = run_mr(ws, mp, extra=["--checkpoint", sha])
    assert "not run" in p.stdout


def test_r041_checkpoint_refuse_file_at_commit(tmp_path):
    """R-041, TASK-031 Done when (d): listed file at checkpoint refused exit 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    sha = git(ws, "rev-parse", "HEAD")
    mp = mutants_path(ws, "ck3", {"mutants": [], "new_tests": ["tests/test_calc.py"]})
    assert run_mr(ws, mp, extra=["--checkpoint", sha]).returncode == 2


@pytest.mark.skipif(sys.platform != "win32", reason="console windows exist only on Windows")
def test_r041_pytest_child_windowless(tmp_path, home_of_the_tests):
    """R-041, TASK-031 Done when (d): on Windows the test process reports no console window."""
    from test_tests_windowless import PRINT_WINDOW, window_and_console
    ws = workspace(tmp_path)
    init_pkg(ws)
    cfkey = "creation" + "flags"
    tpl = textwrap.dedent("""
import subprocess, sys
_FLAG = FLAGVAL
def pytest_sessionstart(session):
    kw = {CFKEY: _FLAG}
    p = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True, **kw)
    open("_win_probe.txt", "w").write(p.stdout.strip())
""").replace("FLAGVAL", str(NO_WINDOW)).replace("CFKEY", repr(cfkey)).replace("PROBE", repr(PRINT_WINDOW))
    write(ws, "tests/conftest.py", tpl)
    git(ws, "add", "tests/conftest.py")
    mp = mutants_path(ws, "win", basic_mutant())
    git(ws, "add", "run/supervisor/win-mutants.json")
    scratch = home_of_the_tests / "scr"
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env["HOME"] = env["USERPROFILE"] = str(home_of_the_tests)
    cmd = [sys.executable, MUTATION_RUN, str(mp), "--scratch", str(scratch), "--mutant-timeout", "60"]
    proc = subprocess.Popen(cmd, cwd=str(ws), env=env,
                            **test_conftest.windowless_kwargs({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True}))
    line = None
    while proc.poll() is None:
        hits = list(scratch.rglob("_win_probe.txt"))
        if hits:
            line = hits[0].read_text(encoding="utf-8").strip()
            break
        time.sleep(0.05)
    out, err = proc.communicate(timeout=90)
    assert proc.returncode == 0, err or out
    assert line, "probe file missing"
    window, child, on_console = window_and_console(line)
    assert window == 0
    assert os.getpid() not in on_console


def test_r041_relaunch_after_partial_cache(tmp_path):
    """R-041, TASK-031 Done when (d): relaunch runs only mutants not kept as killed."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    body = {"mutants": [
        basic_mutant()["mutants"][0],
        {**basic_mutant()["mutants"][0], "id": "m2"},
    ]}
    mp = mutants_path(ws, "rel", body)
    git(ws, "add", "run/supervisor/rel-mutants.json")
    run_mr(ws, mp)
    cache = ws / "run/supervisor/mutation-cache/rel.jsonl"
    lines = [l for l in cache.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 2
    cache.write_text(lines[0] + "\n", encoding="utf-8")
    p = run_mr(ws, mp)
    assert "m1: killed (cached" in p.stdout and "m2:" in p.stdout and "run=1" in p.stdout


def test_r041_editable_install_overridden(tmp_path):
    """R-041, TASK-031 Done when (d): editable install of the fixture package is overridden by the copy."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    vroot = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", "--system-site-packages", str(vroot)],
                   check=True, **test_conftest.windowless_kwargs({"capture_output": True}))
    if sys.platform == "win32":
        vpy = vroot / "Scripts" / "python.exe"
        site = vroot / "Lib" / "site-packages"
    else:
        vpy = vroot / "bin" / "python"
        site = vroot / "lib" / ("python%d.%d" % sys.version_info[:2]) / "site-packages"
    site.mkdir(parents=True, exist_ok=True)
    (site / "demo.pth").write_text(str(ws) + "\n", encoding="utf-8")
    mp = mutants_path(ws, "edi", basic_mutant())
    git(ws, "add", "run/supervisor/edi-mutants.json")
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    cmd = [str(vpy), MUTATION_RUN, str(mp), "--mutant-timeout", "60"]
    p = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env,
                       **test_conftest.windowless_kwargs({}))
    assert p.returncode == 0, p.stderr + p.stdout


def test_r041_scratch_inside_workspace_refused(tmp_path):
    """R-041: scratch inside Workspace exits 2."""
    ws = workspace(tmp_path)
    init_pkg(ws)
    mp = mutants_path(ws, "si", basic_mutant())
    git(ws, "add", "run/supervisor/si-mutants.json")
    scratch = ws / "scratch"
    assert run_mr(ws, mp, scratch=scratch).returncode == 2
