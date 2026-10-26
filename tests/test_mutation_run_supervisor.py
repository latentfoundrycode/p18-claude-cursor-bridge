"""TASK-031: the supervisor's tests of mutation-run.py (handoff/TASK-031.md; R-041). Each test names the
Requirement it enforces. They build their own fixture Workspaces under tmp_path and share no helper with
tests/test_mutation_run.py, so a change to the builder's helpers cannot weaken them."""
import json
import os
import subprocess
import sys

import pytest

import conftest as test_conftest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "mutation-run.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
       "-c", "commit.gpgsign=false"]


def _git(ws, *args):
    p = subprocess.run(GIT + list(args), cwd=str(ws),
                       **test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 60}))
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def _write(ws, rel, text):
    path = ws / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _fixture(tmp_path, files):
    ws = tmp_path / "proj" / "Workspace"
    (ws / "run" / "supervisor").mkdir(parents=True)
    for rel, text in files.items():
        _write(ws, rel, text)
    _git(ws, "init", "-q", "-b", "main")
    _git(ws, "add", "-A")
    _git(ws, "commit", "-q", "-m", "init")
    return ws


def _mutants(ws, run_id, body):
    path = ws / "run" / "supervisor" / ("%s-mutants.json" % run_id)
    path.write_text(json.dumps(body), encoding="utf-8")
    return path


def _run(ws, mutants_file, *extra, timeout=60):
    cmd = [sys.executable, PROG, str(mutants_file), "--scratch", str(ws.parent.parent / "scratch")] + list(extra)
    return subprocess.run(cmd, cwd=str(ws),
                          **test_conftest.windowless_kwargs({"capture_output": True, "text": True,
                                                             "timeout": timeout}))


def _cache_lines(ws, run_id):
    path = ws / "run" / "supervisor" / "mutation-cache" / ("%s.jsonl" % run_id)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


CALC = {
    "demo/__init__.py": "",
    "demo/calc.py": "def add(a, b):\n    return a + b\n",
    "tests/test_calc.py": "from demo.calc import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
}


def test_task031_req9_an_expected_survivor_that_survives_exits_0(tmp_path):
    """R-041, TASK-031 Requirement 6 and 9 (handoff/TASK-031.md): an `expect: survive` mutant is reported apart and
    counts as neither killed nor survived, so one that survives, alone in its file, gives exit 0, never 1."""
    ws = _fixture(tmp_path, CALC)
    mf = _mutants(ws, "eqs", {"mutants": [{
        "id": "swap", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return b + a"}],
        "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"],
        "expect": "survive addition commutes"}]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "swap" in p.stdout


def test_task031_req7_a_root_level_file_keys_its_whole_folder(tmp_path):
    """R-041, TASK-031 Requirement 7 (the key covers the tracked files under the mutated file's own folder,
    recursively): for a mutated file at the root that folder is the whole tree, so a change to a sibling at the
    root reruns its mutant; the mutant is never kept as killed on a key that left the sibling out."""
    files = {"calc.py": "from helper import one\n\ndef add(a, b):\n    return a + b\n",
             "helper.py": "def one():\n    return 1\n",
             "tests/test_calc.py": "from calc import add\n\ndef test_add():\n    assert add(1, 2) == 3\n"}
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "root", {"mutants": [{
        "id": "m", "file": "calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]}]})
    first = _run(ws, mf)
    assert first.returncode == 0, first.stdout + first.stderr        # precondition: killed and recorded
    assert len(_cache_lines(ws, "root")) == 1
    _write(ws, "helper.py", "def one():\n    return 2\n")
    second = _run(ws, mf)
    assert second.returncode == 0, second.stdout + second.stderr
    assert len(_cache_lines(ws, "root")) == 2, second.stdout


def test_task031_req7_a_change_reruns_only_the_mutants_it_keys(tmp_path):
    """R-041, TASK-031 Done when (d) (a change to a mutated file reruns only that file's mutants): after a change
    to demo/calc.py, its mutant runs again and the mutant of lib/util.py stays cached."""
    files = dict(CALC)
    files["lib/__init__.py"] = ""
    files["lib/util.py"] = "def double(x):\n    return 2 * x\n"
    files["tests/test_util.py"] = "from lib.util import double\n\ndef test_double():\n    assert double(2) == 4\n"
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "only", {"mutants": [
        {"id": "calc", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
         "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]},
        {"id": "util", "file": "lib/util.py", "pairs": [{"old": "return 2 * x", "new": "return 3 * x"}],
         "tests": ["tests/test_util.py"], "expect_fail": ["tests/test_util.py::test_double"]}]})
    assert _run(ws, mf).returncode == 0                              # precondition: both killed and recorded
    _write(ws, "demo/calc.py", "def add(a, b):\n    return a + b  # touched\n")
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    ran = [line["mutant"] for line in _cache_lines(ws, "only")[2:]]
    assert ran == ["calc"], ran


def _outside_file(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("outside the Workspace\n", encoding="utf-8")
    return outside, secret


def test_task031_req1_a_link_inside_an_untracked_folder_is_refused(tmp_path):
    """R-041, TASK-031 Requirement 1 and 2 (an `untracked` path reached through a link, any component or anything
    inside a listed folder, is refused with exit 2; nothing outside the Workspace is read through a link while
    copying): a listed folder holding a link to a file outside the Workspace exits 2 and copies nothing."""
    ws = _fixture(tmp_path, CALC)
    outside, secret = _outside_file(tmp_path)
    (ws / "fixtures").mkdir()
    (ws / "fixtures" / "plain.txt").write_text("in\n", encoding="utf-8")
    try:
        os.symlink(str(secret), str(ws / "fixtures" / "leak.txt"))
    except (OSError, NotImplementedError) as e:
        if sys.platform != "win32":
            pytest.skip("this account cannot create a symbolic link here (%s)" % e)
        # a junction needs no privilege on Windows; it holds the same outside file, one folder down
        j = subprocess.run(["cmd", "/c", "mklink", "/J", str(ws / "fixtures" / "leak"), str(outside)],
                           **test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 30}))
        if j.returncode != 0:
            pytest.skip("neither a symbolic link nor a junction could be made here (%s)" % j.stderr)
        assert (ws / "fixtures" / "leak" / "secret.txt").is_file()     # precondition: the junction leads outside
    secret_name = "secret.txt" if not (ws / "fixtures" / "leak.txt").exists() else "leak.txt"
    mf = _mutants(ws, "lnk", {"mutants": [{
        "id": "m", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]}],
        "untracked": ["fixtures"]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert _cache_lines(ws, "lnk") == []
    assert secret_name in ("secret.txt", "leak.txt")
    assert secret.read_text(encoding="utf-8") == "outside the Workspace\n"   # the outside file is untouched


def test_task031_req4_a_resolution_check_past_its_bound_exits_3(tmp_path):
    """R-041, TASK-031 Requirement 4 (a timed-out resolution check exits 3, naming the bound; S7): a conftest that
    never finishes importing holds the collection past `--mutant-timeout`, and the run exits 3, never 2."""
    files = dict(CALC)
    files["tests/conftest.py"] = "import time\n\nwhile True:\n    time.sleep(0.2)\n"
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "slow", {"mutants": [{
        "id": "m", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]}]})
    p = _run(ws, mf, "--mutant-timeout", "3")
    assert p.returncode == 3, p.stdout + p.stderr
    assert "3" in p.stderr
    assert _cache_lines(ws, "slow") == []


def _workspace_insert_test(ws):
    return ("import sys\nsys.path.insert(0, %r)\nimport demo.calc\n\ndef test_new():\n"
            "    assert demo.calc.add(1, 2) == 3\n" % str(ws))


def test_task031_req5_a_test_loading_the_workspace_is_refused(tmp_path):
    """R-041, TASK-031 Requirement 5 (ii) (no module loaded during collection comes from a tracked path inside the
    Workspace; a test or conftest that inserts the Workspace's absolute path is refused): exit 2, nothing cached."""
    ws = _fixture(tmp_path, CALC)
    _write(ws, "checks/test_leak.py", _workspace_insert_test(ws))
    _git(ws, "add", "checks/test_leak.py")
    mf = _mutants(ws, "leak", {"mutants": [{
        "id": "m", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["checks/test_leak.py"], "expect_fail": ["checks/test_leak.py::test_new"]}]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert _cache_lines(ws, "leak") == []


def test_task031_req8_the_checkpoint_check_collects_the_listed_new_tests(tmp_path):
    """R-041, TASK-031 Requirement 8 and 5 (in --checkpoint mode the resolution check runs on the checkpoint's tree
    over the listed new tests): a new test outside tests/ that loads the Workspace's own module is refused with
    exit 2, in --checkpoint mode too."""
    ws = _fixture(tmp_path, CALC)
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "checks/test_leak.py", _workspace_insert_test(ws))
    _git(ws, "add", "checks/test_leak.py")
    mf = _mutants(ws, "ckleak", {"mutants": [], "new_tests": ["checks/test_leak.py::test_new"]})
    p = _run(ws, mf, "--checkpoint", sha)
    assert p.returncode == 2, p.stdout + p.stderr
