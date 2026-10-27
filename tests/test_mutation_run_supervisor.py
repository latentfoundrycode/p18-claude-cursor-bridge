"""TASK-031: the supervisor's tests of mutation-run.py (handoff/TASK-031.md; R-041). Each test names the
Requirement it enforces. They build their own fixture Workspaces under tmp_path and share no helper with
tests/test_mutation_run.py, so a change to the builder's helpers cannot weaken them."""
import json
import os
import re
import signal
import subprocess
import sys
import time

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


def _run(ws, mutants_file, *extra, timeout=60, env=None, scratch=True):
    cmd = [sys.executable, PROG, str(mutants_file)]
    if scratch:
        cmd += ["--scratch", str(ws.parent.parent / "scratch")]
    cmd += list(extra)
    kw = {"capture_output": True, "text": True, "timeout": timeout}
    if env is not None:
        kw["env"] = env
    return subprocess.run(cmd, cwd=str(ws), **test_conftest.windowless_kwargs(kw))


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
    mf = _mutants(ws, "lnk", {"mutants": [{
        "id": "m", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]}],
        "untracked": ["fixtures"]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert "fixtures/leak" in p.stderr.replace("\\", "/"), p.stderr      # the refusal names the link
    assert _cache_lines(ws, "lnk") == []
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
    assert "timed out" in p.stderr and "3 s" in p.stderr, p.stderr   # the bound, never the internal-error line
    assert "internal error" not in p.stderr
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


def test_task031_req8_a_module_the_increment_adds_does_not_refuse_the_checkpoint_run(tmp_path):
    """R-041, TASK-031 Requirement 8 and 5 (i) (handoff/TASK-031-r3.md, item 1): in --checkpoint mode the mutants'
    files are checked only for resolving outside the copy; a mutated module the increment adds is absent at the
    checkpoint, so it resolves nowhere there, and the run goes on: its new test fails to collect on the old code
    and is listed `not run`, exit 0, never the refusal's 2."""
    ws = _fixture(tmp_path, CALC)
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "demo/newmod.py", "def triple(x):\n    return 3 * x\n")
    _write(ws, "tests/test_newmod.py", "from demo.newmod import triple\n\ndef test_triple():\n"
           "    assert triple(2) == 6\n")
    _git(ws, "add", "demo/newmod.py", "tests/test_newmod.py")
    mf = _mutants(ws, "cknew", {"mutants": [{
        "id": "m", "file": "demo/newmod.py", "pairs": [{"old": "return 3 * x", "new": "return 2 * x"}],
        "tests": ["tests/test_newmod.py"], "expect_fail": ["tests/test_newmod.py::test_triple"]}],
        "new_tests": ["tests/test_newmod.py"]})
    p = _run(ws, mf, "--checkpoint", sha)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "not run" in p.stdout
    normal = _run(ws, mf)                                          # the same file in normal mode: killed
    assert normal.returncode == 0, normal.stdout + normal.stderr


# Round 4 (handoff/TASK-031-r4.md): the blocking findings of Review A and the security audit on round 3's head.

KILL_CALC = {"id": "m", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
             "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]}


@pytest.mark.parametrize("variant", ["addopts -q", "colour forced"])
def test_task031_r4_b1_a_kill_is_read_from_the_outcomes_not_the_terminal_text(tmp_path, variant):
    """R-041 (a kill is a named expected test failing in the report), TASK-031 Requirement 6 (handoff/TASK-031-r4.md,
    B1): a project whose pytest configuration says `addopts = -q`, or a run whose environment forces colour, still
    reads its expected test's failure as a kill: exit 0, the outcome `killed` recorded, never `error`."""
    files = dict(CALC)
    env = dict(os.environ)
    if variant == "addopts -q":
        files["pytest.ini"] = "[pytest]\naddopts = -q\n"
    else:
        env["PY_COLORS"] = "1"
        env["FORCE_COLOR"] = "1"
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "b1", {"mutants": [KILL_CALC]})
    p = _run(ws, mf, env=env)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "b1")] == ["killed"]


def test_task031_r4_b2_a_new_test_in_an_existing_file_is_checked_at_the_checkpoint(tmp_path):
    """R-041, TASK-031 Requirements 1 and 8 (handoff/TASK-031-r4.md, B2): a listed new test *id* whose file the
    checkpoint already holds is the intended case, never refused; the file's working-tree version is copied over the
    checkpoint's, and an id that passes on the old code gives exit 4."""
    ws = _fixture(tmp_path, CALC)
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "tests/test_calc.py", CALC["tests/test_calc.py"] + "\ndef test_new():\n    assert add(0, 0) == 0\n")
    _git(ws, "add", "tests/test_calc.py")
    mf = _mutants(ws, "b2", {"mutants": [], "new_tests": ["tests/test_calc.py::test_new"]})
    p = _run(ws, mf, "--checkpoint", sha)
    assert p.returncode == 4, p.stdout + p.stderr
    assert "tests/test_calc.py::test_new" in p.stdout


def test_task031_r4_b3_each_listed_test_is_judged_alone_at_the_checkpoint(tmp_path):
    """R-041, TASK-031 Requirements 8 and 9 (each test that passes is listed as passing; exit 4 when any listed test
    passed; handoff/TASK-031-r4.md, B3): a listed new file holding one test that passes on the old code and one that
    fails there lists the passing one by id and exits 4, never 0."""
    ws = _fixture(tmp_path, CALC)
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "tests/test_new.py", "from demo.calc import add\n\ndef test_passes_on_old():\n    assert add(1, 1) == 2\n"
           "\ndef test_fails_on_old():\n    assert add(1, 1) == 3\n")
    _git(ws, "add", "tests/test_new.py")
    mf = _mutants(ws, "b3", {"mutants": [], "new_tests": ["tests/test_new.py"]})
    p = _run(ws, mf, "--checkpoint", sha)
    assert p.returncode == 4, p.stdout + p.stderr
    assert "tests/test_new.py::test_passes_on_old" in p.stdout


def test_task031_r4_b4_a_kill_is_keyed_by_the_bytes_that_ran(tmp_path):
    """R-041 (a kill is kept only for keyed inputs byte-identical to those of the run that killed it; handoff/TASK-031-
    r4.md, B4): a keyed file edited in the Workspace while a run is under way leaves no later mutant kept as killed
    under the edited bytes, which never ran; the next run runs every mutant whose keyed bytes changed."""
    started = tmp_path / "gate-started"
    go = tmp_path / "gate-go"
    files = dict(CALC)
    files["tests/test_gate.py"] = (
        "import time\nfrom pathlib import Path\n\ndef test_gate():\n    Path(%r).write_text('x')\n"
        "    while not Path(%r).is_file():\n        time.sleep(0.05)\n    assert False\n"
        % (str(started), str(go)))
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "b4", {"mutants": [
        {"id": "gate", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
         "tests": ["tests/test_gate.py"], "expect_fail": ["tests/test_gate.py::test_gate"]},
        dict(KILL_CALC, id="later")]})
    cmd = [sys.executable, PROG, str(mf), "--scratch", str(tmp_path / "scratch")]
    proc = subprocess.Popen(cmd, cwd=str(ws), **test_conftest.windowless_kwargs(
        {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True}))
    try:
        for _ in range(1200):
            if started.is_file() or proc.poll() is not None:
                break
            time.sleep(0.05)
        assert started.is_file(), "the gate test never started"
        _write(ws, "demo/calc.py", CALC["demo/calc.py"] + "# edited while the run was under way\n")
        go.write_text("go", encoding="utf-8")
        out, err = proc.communicate(timeout=60)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate(timeout=30)
    assert proc.returncode == 0, out + err
    assert len(_cache_lines(ws, "b4")) == 2
    again = _run(ws, mf)
    assert again.returncode == 0, again.stdout + again.stderr
    assert sorted(line["mutant"] for line in _cache_lines(ws, "b4")[2:]) == ["gate", "later"], again.stdout


@pytest.mark.skipif(sys.platform != "win32", reason="the case-insensitive file system is Windows'")
def test_task031_r4_s1_a_scratch_folder_inside_the_workspace_in_another_case_is_refused(tmp_path):
    """R-041, TASK-031 Requirement 2 (a scratch folder inside the Workspace is refused; handoff/TASK-031-r4.md, S1):
    on Windows a `--scratch` naming a folder inside the Workspace in other letter case exits 2 and creates nothing
    inside the Workspace."""
    ws = _fixture(tmp_path, CALC)
    mf = _mutants(ws, "s1", {"mutants": [KILL_CALC]})
    inside = str(ws / "scratch-inside").swapcase()
    cmd = [sys.executable, PROG, str(mf), "--scratch", inside]
    p = subprocess.run(cmd, cwd=str(ws), **test_conftest.windowless_kwargs(
        {"capture_output": True, "text": True, "timeout": 60}))
    assert p.returncode == 2, p.stdout + p.stderr
    assert not (ws / "scratch-inside").exists()
    assert _cache_lines(ws, "s1") == []


@pytest.mark.parametrize("listed", [".", ".git", "fixtures/./data.txt"])
def test_task031_r4_s3_an_untracked_entry_naming_the_workspace_or_git_is_refused(tmp_path, listed):
    """R-041, TASK-031 Requirements 1 and 2 (nothing else is copied: no `.git`; handoff/TASK-031-r4.md, S3): an
    `untracked` entry that is `.`, `.git` or holds a `.` component exits 2 and caches nothing."""
    ws = _fixture(tmp_path, CALC)
    _write(ws, "fixtures/data.txt", "payload\n")
    mf = _mutants(ws, "s3", {"mutants": [KILL_CALC], "untracked": [listed]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert _cache_lines(ws, "s3") == []


def test_task031_r4_s2_a_cache_file_that_is_a_link_is_refused(tmp_path):
    """R-041, TASK-031 Context, trust boundaries (the run cache: a link anywhere on that path would carry a write out
    of the Workspace; handoff/TASK-031-r4.md, S2): a cache file `<id>.jsonl` that is a hard link to a file outside the
    Workspace exits 2, and the outside file is unchanged."""
    ws = _fixture(tmp_path, CALC)
    outside = tmp_path / "outside.jsonl"
    outside.write_text("", encoding="utf-8")
    cache_dir = ws / "run" / "supervisor" / "mutation-cache"
    cache_dir.mkdir(parents=True)
    try:
        os.link(str(outside), str(cache_dir / "s2.jsonl"))
    except (OSError, NotImplementedError) as e:
        pytest.skip("no hard link can be made here (%s)" % e)
    mf = _mutants(ws, "s2", {"mutants": [KILL_CALC]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert outside.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize("case", ["expect_fail outside tests", "file not a string", "new_tests not a string"])
def test_task031_r4_b7_a_malformed_mutant_is_refused_with_2(tmp_path, case):
    """R-041, TASK-031 Requirement 1 (a missing or wrong-typed field exits 2; each `expect_fail` id is in one of the
    mutant's `tests` files; a refusal writes nothing, not even a cache line; handoff/TASK-031-r4.md, B7): exit 2,
    never the internal error's 3, and no cache line."""
    ws = _fixture(tmp_path, CALC)
    extra = []
    if case == "expect_fail outside tests":
        body = {"mutants": [dict(KILL_CALC, expect_fail=["tests/test_other.py::test_add"])]}
    elif case == "file not a string":
        body = {"mutants": [dict(KILL_CALC, file=123)]}
    else:
        body = {"mutants": [], "new_tests": [7]}
        extra = ["--checkpoint", _git(ws, "rev-parse", "HEAD")]
    mf = _mutants(ws, "b7", body)
    p = _run(ws, mf, *extra)
    assert p.returncode == 2, p.stdout + p.stderr
    assert "internal error" not in p.stderr
    assert _cache_lines(ws, "b7") == []


def test_task031_r4_b8_a_pytest_configuration_above_the_copy_is_not_read(tmp_path, home_of_the_tests):
    """R-041 (every mutant gets a result against the version the gate reads), TASK-031 Requirement 4 (handoff/TASK-031-
    r4.md, B8): the copy lies under the owner's home, so pytest's search for a configuration file climbs there; a
    `pytest.ini` in the home that deselects every test must not configure the mutant's run, which the gate's run from
    the Workspace never reads: the mutant is killed, exit 0."""
    (home_of_the_tests / "pytest.ini").write_text("[pytest]\naddopts = -k nothing_matches_this\n", encoding="utf-8")
    ws = _fixture(tmp_path, CALC)
    mf = _mutants(ws, "b8", {"mutants": [KILL_CALC]})
    p = _run(ws, mf, scratch=False)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "b8")] == ["killed"]


def test_task031_r4_b6_an_expected_survivor_killed_is_not_counted_killed(tmp_path):
    """R-041, TASK-031 Requirement 6 (an `expect: survive` mutant counts as neither killed nor survived;
    handoff/TASK-031-r2.md item 1; handoff/TASK-031-r4.md, B6): one that is killed gives exit 1 and adds nothing to
    the summary's killed count."""
    ws = _fixture(tmp_path, CALC)
    mf = _mutants(ws, "b6", {"mutants": [dict(KILL_CALC, expect="survive claimed equivalent")]})
    p = _run(ws, mf)
    assert p.returncode == 1, p.stdout + p.stderr
    counts = [line for line in p.stdout.splitlines() if line.startswith("counts:")]
    assert counts and re.search(r"\bkilled=0\b", counts[0]), p.stdout


# After round 4: the tests for the three mutants of the supervisor's driver that survived round 4's code (M30, M38,
# M39 in run/supervisor/task031_mutants.py).

def test_task031_r4_b6_a_cached_kill_of_an_expected_survivor_is_not_counted_killed(tmp_path):
    """R-041, TASK-031 Requirement 6 (an `expect: survive` mutant counts as neither killed nor survived; S4: a cached
    kill of one still gives exit 1; handoff/TASK-031-r4.md, B6): on the rerun that skips it as a kept kill, the
    summary's killed count stays 0 and the exit stays 1."""
    ws = _fixture(tmp_path, CALC)
    mf = _mutants(ws, "b6c", {"mutants": [dict(KILL_CALC, expect="survive claimed equivalent")]})
    first = _run(ws, mf)
    assert first.returncode == 1, first.stdout + first.stderr
    again = _run(ws, mf)
    assert again.returncode == 1, again.stdout + again.stderr
    assert len(_cache_lines(ws, "b6c")) == 1, again.stdout
    counts = [line for line in again.stdout.splitlines() if line.startswith("counts:")]
    assert counts and re.search(r"\bkilled=0\b", counts[0]), again.stdout


def test_task031_r4_b4_a_workspace_edit_before_the_mutants_run_is_not_keyed(tmp_path):
    """R-041 (a kill is kept only for keyed inputs byte-identical to those of the run that killed it; handoff/TASK-031-
    r4.md, B4: the keys are computed from the copy's bytes): a keyed file edited in the Workspace after the copy is
    made, while the resolution check collects, is not the file the mutant ran on, so the kill is kept under the
    copy's bytes and the next run, whose copy holds the edit, runs the mutant again."""
    started = tmp_path / "collect-started"
    go = tmp_path / "collect-go"
    files = dict(CALC)
    files["tests/conftest.py"] = (
        "import time\nfrom pathlib import Path\n\n_started = Path(%r)\n_go = Path(%r)\nif not _started.is_file():\n"
        "    _started.write_text('x')\n    while not _go.is_file():\n        time.sleep(0.05)\n"
        % (str(started), str(go)))
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "b4c", {"mutants": [KILL_CALC]})
    cmd = [sys.executable, PROG, str(mf), "--scratch", str(tmp_path / "scratch")]
    proc = subprocess.Popen(cmd, cwd=str(ws), **test_conftest.windowless_kwargs(
        {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True}))
    try:
        for _ in range(1200):
            if started.is_file() or proc.poll() is not None:
                break
            time.sleep(0.05)
        assert started.is_file(), "the collection never started"
        _write(ws, "demo/calc.py", CALC["demo/calc.py"] + "# edited after the copy was made\n")
        go.write_text("go", encoding="utf-8")
        out, err = proc.communicate(timeout=60)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate(timeout=30)
    assert proc.returncode == 0, out + err
    assert len(_cache_lines(ws, "b4c")) == 1
    again = _run(ws, mf)
    assert again.returncode == 0, again.stdout + again.stderr
    assert [line["mutant"] for line in _cache_lines(ws, "b4c")[1:]] == ["m"], again.stdout


PIPE_TARGET = """import subprocess
import sys
import time

subprocess.run([sys.executable, sys.argv[1], sys.argv[2]], stdin=subprocess.DEVNULL, stdout=sys.stdout.fileno(),
               stderr=sys.stderr.fileno(), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=60)
while True:
    time.sleep(0.2)
"""

PIPE_MIDDLE = """import subprocess
import sys

kw = {} if sys.platform == "win32" else {"start_new_session": True}
holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"], stdin=subprocess.DEVNULL,
                          stdout=sys.stdout.fileno(), stderr=sys.stderr.fileno(), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), **kw)
with open(sys.argv[1], "w") as f:
    f.write(str(holder.pid))
"""

PIPE_DRIVER = """import importlib.util
import sys
import time

spec = importlib.util.spec_from_file_location("mutation_run_under_test", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
t0 = time.time()
rc, out, err, timed = mod.run_process([sys.executable, sys.argv[2], sys.argv[3], sys.argv[4]], None, sys.argv[5], 2)
print("timed=%s elapsed=%.1f" % (timed, time.time() - t0))
"""


def test_task031_r4_item12_a_pipe_holder_outside_the_killed_tree_cannot_hold_the_run(tmp_path):
    """R-041 (each mutant's run is bounded), TASK-031 S7 (the per-mutant bound; handoff/TASK-031-r4.md, item 12: the
    bound's kill cannot hang): a process that holds the test run's pipes and is outside the tree the bound kills (its
    parent gone; on POSIX a session of its own) cannot keep run_process waiting: it returns timed out within the
    bound plus its 30-second waits, and only after the hold has lasted out the second wait."""
    for name, text in (("target.py", PIPE_TARGET), ("middle.py", PIPE_MIDDLE), ("driver.py", PIPE_DRIVER)):
        (tmp_path / name).write_text(text, encoding="utf-8")
    pidfile = tmp_path / "holder.pid"
    cmd = [sys.executable, str(tmp_path / "driver.py"), os.path.abspath(PROG), str(tmp_path / "target.py"),
           str(tmp_path / "middle.py"), str(pidfile), str(tmp_path)]
    try:
        p = subprocess.run(cmd, cwd=str(tmp_path), **test_conftest.windowless_kwargs(
            {"capture_output": True, "text": True, "timeout": 120}))
    except subprocess.TimeoutExpired:
        pytest.fail("run_process waited on the pipes past the bound")
    finally:
        if pidfile.is_file():
            try:
                os.kill(int(pidfile.read_text(encoding="utf-8")), signal.SIGTERM)
            except (OSError, ValueError):
                pass
    assert pidfile.is_file(), p.stdout + p.stderr
    m = re.search(r"timed=(\w+) elapsed=([\d.]+)", p.stdout)
    assert m, p.stdout + p.stderr
    assert m.group(1) == "True"
    assert 30 <= float(m.group(2)) < 90, "the hold did not happen, or it held the run past the bound"


# Round 6 (handoff/TASK-031-r6.md): the blocking findings of the security audit on rounds 4 and 5.

@pytest.mark.skipif(sys.platform != "win32", reason="the extended and the admin-share path forms are Windows'")
@pytest.mark.parametrize("form", ["extended", "admin share"])
def test_task031_r6_b1_a_scratch_folder_inside_the_workspace_in_another_path_form_is_refused(tmp_path, form):
    """R-041, TASK-031 Requirement 2 (a scratch folder inside the Workspace is refused; handoff/TASK-031-r6.md, B-1):
    on Windows a `--scratch` naming a folder inside the Workspace through the `\\\\?\\` extended form or the drive's
    administrative share exits 2 and creates nothing inside the Workspace."""
    ws = _fixture(tmp_path, CALC)
    inside = os.path.abspath(str(ws / "scratch-inside"))
    if form == "extended":
        given = "\\\\?\\" + inside
    else:
        drive, rest = os.path.splitdrive(inside)
        given = "\\\\localhost\\" + drive[0] + "$" + rest
        if not os.path.isdir("\\\\localhost\\" + drive[0] + "$" + os.path.splitdrive(str(ws))[1]):
            pytest.skip("the drive's administrative share is not reachable here")
    mf = _mutants(ws, "r6b1", {"mutants": [KILL_CALC]})
    cmd = [sys.executable, PROG, str(mf), "--scratch", given]
    p = subprocess.run(cmd, cwd=str(ws), **test_conftest.windowless_kwargs(
        {"capture_output": True, "text": True, "timeout": 120}))
    assert p.returncode == 2, p.stdout + p.stderr
    assert not (ws / "scratch-inside").exists()
    assert _cache_lines(ws, "r6b1") == []


@pytest.mark.skipif(sys.platform != "win32", reason="these names reach .git through Windows' name rules")
@pytest.mark.parametrize("listed", [".git.", ".git ", ".git::$INDEX_ALLOCATION", "short name"])
def test_task031_r6_b2_an_untracked_entry_reaching_git_by_another_name_is_refused(tmp_path, listed):
    """R-041, TASK-031 Requirements 1 and 2 (nothing else is copied: no `.git`; handoff/TASK-031-r6.md, B-2): on
    Windows an `untracked` entry that names the Workspace's `.git` folder another way (a trailing dot or space, a
    stream name, the 8.3 short name) exits 2 and caches nothing."""
    ws = _fixture(tmp_path, CALC)
    if listed == "short name":
        listed = "GIT~1"
        if not (os.path.isdir(str(ws / listed)) and os.path.samefile(str(ws / listed), str(ws / ".git"))):
            pytest.skip("8.3 short names are not made on this volume")
    mf = _mutants(ws, "r6b2", {"mutants": [KILL_CALC], "untracked": [listed]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert _cache_lines(ws, "r6b2") == []


@pytest.mark.parametrize("root_file", ["pyproject.toml", "setup.cfg", "tox.ini"])
def test_task031_r6_b3_a_root_file_with_no_pytest_section_keeps_the_configuration_above_unread(
        tmp_path, home_of_the_tests, root_file):
    """R-041 (every mutant gets a result against the version the gate reads), TASK-031 Requirement 4
    (handoff/TASK-031-r4.md, B8; handoff/TASK-031-r6.md, B-3): a copy whose root holds a `pyproject.toml`, `setup.cfg`
    or `tox.ini` with no pytest section has no pytest configuration of its own, so a `pytest.ini` in the home that
    deselects every test still configures nothing: the mutant is killed, exit 0."""
    (home_of_the_tests / "pytest.ini").write_text("[pytest]\naddopts = -k nothing_matches_this\n", encoding="utf-8")
    files = dict(CALC)
    files[root_file] = {"pyproject.toml": "[project]\nname = \"demo\"\nversion = \"0.0.0\"\n",
                        "setup.cfg": "[metadata]\nname = demo\n",
                        "tox.ini": "[tox]\nenvlist = py312\n"}[root_file]
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "r6b3", {"mutants": [KILL_CALC]})
    p = _run(ws, mf, scratch=False)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "r6b3")] == ["killed"]


@pytest.mark.parametrize("config", [".pytest.ini", "pytest.toml", "pyproject.toml"])
def test_task031_r6_b3_the_copys_own_pytest_configuration_is_read(tmp_path, config):
    """R-041 (every mutant gets a result against the version the gate reads), TASK-031 Requirement 4
    (handoff/TASK-031-r6.md, B-3): a project whose pytest configuration is a `.pytest.ini`, a `pytest.toml` or a
    `pyproject.toml` `[tool.pytest.ini_options]` table, which the gate's own run reads, configures the mutant's run
    too: its tests, collected only through that configuration, kill the mutant, exit 0."""
    files = {
        "demo/__init__.py": "",
        "demo/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from demo.calc import add\n\ndef check_add():\n    assert add(1, 2) == 3\n",
        config: {".pytest.ini": "[pytest]\npython_functions = check_*\n",
                 "pytest.toml": "[pytest]\npython_functions = [\"check_*\"]\n",
                 "pyproject.toml": "[tool.pytest.ini_options]\npython_functions = \"check_*\"\n"}[config],
    }
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "r6cfg", {"mutants": [dict(KILL_CALC, expect_fail=["tests/test_calc.py::check_add"])]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "r6cfg")] == ["killed"]


@pytest.mark.parametrize("listed", ["tests/test_calc.py::test_p", "tests/test_calc.py::TestNew"])
def test_task031_r6_a1_a_parametrized_or_class_id_is_judged_by_its_tests_at_the_checkpoint(tmp_path, listed):
    """R-041, TASK-031 Requirements 8 and 9 (each test that passes on the old code is listed as passing; exit 4
    when any did; handoff/TASK-031-r4.md, B3: a listed file or a parametrized id; handoff/TASK-031-r6.md, A-1): a
    listed parametrized function id or class id whose tests ran at the checkpoint, one of them passing on the old
    code, lists that test by its own id as passing and exits 4, never `not run` and 0."""
    ws = _fixture(tmp_path, CALC)
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "tests/test_calc.py", CALC["tests/test_calc.py"]
           + "\nimport pytest\n\n@pytest.mark.parametrize(\"n\", [1, 2])\ndef test_p(n):\n    assert add(n, 0) == 1\n"
           + "\nclass TestNew:\n    def test_passes(self):\n        assert add(1, 1) == 2\n\n"
           + "    def test_fails(self):\n        assert add(1, 1) == 3\n")
    _git(ws, "add", "tests/test_calc.py")
    mf = _mutants(ws, "r6a1", {"mutants": [], "new_tests": [listed]})
    p = _run(ws, mf, "--checkpoint", sha)
    assert p.returncode == 4, p.stdout + p.stderr
    passing = "tests/test_calc.py::test_p[1]" if listed.endswith("test_p") else "tests/test_calc.py::TestNew::test_passes"
    assert re.search(re.escape(passing) + r": passing on old code", p.stdout), p.stdout


def test_task031_r6_a3_a_collection_error_beside_a_kill_is_an_error(tmp_path):
    """R-041 (a crash is an error, never a kill), TASK-031 Requirement 6 (error: the tests did not collect;
    handoff/TASK-031-r6.md, A-3): under `--continue-on-collection-errors`, a mutant that breaks one listed test
    file's import while its expected test fails is an error, exit 3, never a kept kill."""
    files = {
        "demo/__init__.py": "",
        "demo/calc.py": "def add(a, b):\n    return a + b\n\n\ndef sub(a, b):\n    return a - b\n",
        "tests/test_calc.py": "from demo.calc import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        "tests/test_sub.py": "from demo.calc import sub\n\ndef test_sub():\n    assert sub(3, 2) == 1\n",
        "pytest.ini": "[pytest]\naddopts = --continue-on-collection-errors\n",
    }
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "r6a3", {"mutants": [{
        "id": "m", "file": "demo/calc.py",
        "pairs": [{"old": "return a + b", "new": "return a - b"}, {"old": "def sub(", "new": "def sub2("}],
        "tests": ["tests/test_calc.py", "tests/test_sub.py"], "expect_fail": ["tests/test_calc.py::test_add"]}]})
    p = _run(ws, mf)
    assert p.returncode == 3, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "r6a3")] != ["killed"]
    assert "collection error" in p.stdout, p.stdout


# Round 6's mutation run: the survivors that showed a gap in the tests above.

@pytest.mark.skipif(sys.platform != "win32", reason="the extended and the admin-share path forms are Windows'")
@pytest.mark.parametrize("form", ["extended", "admin share"])
def test_task031_r6_b1_a_scratch_folder_in_the_extended_or_unc_form_is_refused_outside_the_workspace_too(
        tmp_path, form):
    """R-041, TASK-031 Requirement 2 (handoff/TASK-031-r6.md, B-1: a `--scratch` in the extended, device or UNC
    form is refused): the form alone refuses it, wherever it points, so a `--scratch` naming a folder outside the
    Workspace through the `\\\\?\\` extended form or the drive's administrative share exits 2 and creates nothing."""
    ws = _fixture(tmp_path, CALC)
    outside = os.path.abspath(str(tmp_path / "outside-scratch"))
    if form == "extended":
        given = "\\\\?\\" + outside
    else:
        drive, rest = os.path.splitdrive(outside)
        given = "\\\\localhost\\" + drive[0] + "$" + rest
        if not os.path.isdir("\\\\localhost\\" + drive[0] + "$" + os.path.splitdrive(str(tmp_path))[1]):
            pytest.skip("the drive's administrative share is not reachable here")
    mf = _mutants(ws, "r6b1o", {"mutants": [KILL_CALC]})
    cmd = [sys.executable, PROG, str(mf), "--scratch", given]
    p = subprocess.run(cmd, cwd=str(ws), **test_conftest.windowless_kwargs(
        {"capture_output": True, "text": True, "timeout": 120}))
    assert p.returncode == 2, p.stdout + p.stderr
    assert not os.path.exists(outside)
    assert _cache_lines(ws, "r6b1o") == []


@pytest.mark.skipif(sys.platform != "win32", reason="Windows' name rules drop a component's trailing space")
def test_task031_r6_b1_a_scratch_folder_reaching_the_workspace_through_a_trailing_space_is_refused(tmp_path):
    """R-041, TASK-031 Requirement 2 (a scratch folder inside the Workspace is refused; handoff/TASK-031-r6.md, B-1:
    the overlap compared by file identity): on Windows `<Workspace> \\scratch-inside` names a folder inside the
    Workspace, which a comparison of the path strings misses; it exits 2 and creates nothing inside the Workspace."""
    ws = _fixture(tmp_path, CALC)
    given = os.path.abspath(str(ws)) + " \\scratch-inside"
    assert os.path.samefile(os.path.abspath(str(ws)) + " ", str(ws))       # precondition: the form reaches ws
    mf = _mutants(ws, "r6b1s", {"mutants": [KILL_CALC]})
    cmd = [sys.executable, PROG, str(mf), "--scratch", given]
    p = subprocess.run(cmd, cwd=str(ws), **test_conftest.windowless_kwargs(
        {"capture_output": True, "text": True, "timeout": 120}))
    assert p.returncode == 2, p.stdout + p.stderr
    assert not (ws / "scratch-inside").exists()
    assert _cache_lines(ws, "r6b1s") == []


@pytest.mark.parametrize("listed", ["notes.txt.", "notes.txt "])
def test_task031_r6_b2_an_untracked_entry_ending_in_a_dot_or_a_space_is_refused(tmp_path, listed):
    """R-041, TASK-031 Requirements 1 and 2 (handoff/TASK-031-r6.md, B-2: an untracked entry whose component ends in
    a dot or a space is refused): such an entry exits 2 and caches nothing, even where Windows' name rules make it
    name a file that exists (`notes.txt` here)."""
    ws = _fixture(tmp_path, CALC)
    _write(ws, "notes.txt", "untracked notes\n")
    control = _run(ws, _mutants(ws, "r6b2c", {"mutants": [KILL_CALC], "untracked": ["notes.txt"]}))
    assert control.returncode == 0, control.stdout + control.stderr   # precondition: the plain name is accepted
    mf = _mutants(ws, "r6b2d", {"mutants": [KILL_CALC], "untracked": [listed]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert _cache_lines(ws, "r6b2d") == []


def test_task031_r6_b3_a_pyproject_toml_with_no_pytest_section_leaves_tox_ini_in_force(tmp_path):
    """R-041 (every mutant gets a result against the version the gate reads), TASK-031 Requirement 4
    (handoff/TASK-031-r6.md, B-3: the configuration found as pytest 9.1.1 finds it): pytest passes over a root
    `pyproject.toml` with no pytest table to the `tox.ini` with a `[pytest]` section, so the mutant's run is
    configured by `tox.ini` too: its tests, collected only through it, kill the mutant, exit 0."""
    files = {
        "demo/__init__.py": "",
        "demo/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from demo.calc import add\n\ndef check_add():\n    assert add(1, 2) == 3\n",
        "pyproject.toml": "[project]\nname = \"demo\"\nversion = \"0.0.0\"\n",
        "tox.ini": "[tox]\nenvlist = py312\n\n[pytest]\npython_functions = check_*\n",
    }
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "r6tox", {"mutants": [dict(KILL_CALC, expect_fail=["tests/test_calc.py::check_add"])]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "r6tox")] == ["killed"]


@pytest.mark.parametrize("config", ["pytest.toml", ".pytest.ini"])
def test_task031_r6_b3_a_change_to_a_root_pytest_configuration_reruns_its_mutant(tmp_path, config):
    """R-041 (a kill is kept only while its keyed inputs are unchanged), TASK-031 Requirement 7 (handoff/TASK-031-
    r6.md, B-3: the key set holds the configuration names pytest reads): an edit of a root `pytest.toml` or
    `.pytest.ini` reruns a mutant kept as killed."""
    files = dict(CALC)
    files[config] = "[pytest]\n"
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "r6key", {"mutants": [KILL_CALC]})
    first = _run(ws, mf)
    assert first.returncode == 0, first.stdout + first.stderr        # precondition: killed and recorded
    assert len(_cache_lines(ws, "r6key")) == 1
    _write(ws, config, "[pytest]\n# touched\n")
    second = _run(ws, mf)
    assert second.returncode == 0, second.stdout + second.stderr
    assert len(_cache_lines(ws, "r6key")) == 2, second.stdout


@pytest.mark.skipif(sys.platform != "win32", reason="a junction, which needs no privilege, is Windows'")
def test_task031_r6_b1_a_scratch_folder_holding_the_workspaces_target_through_a_junction_is_refused(tmp_path):
    """R-041, TASK-031 Requirement 2 (a scratch folder that contains the Workspace is refused; handoff/TASK-031-r6.md,
    B-1): a Workspace reached through a junction (`jdir\\J\\Workspace`, J leading to `P\\proj`) with `--scratch P`,
    a folder holding the Workspace's real location though no folder on the way to the Workspace as named, exits 2
    and creates nothing in P (Review A, round 6: M20 and M33 are not equivalent)."""
    import _winapi
    real_ws = _fixture(tmp_path / "P", CALC)
    jdir = tmp_path / "jdir"
    jdir.mkdir()
    junction = jdir / "J"
    _winapi.CreateJunction(str(real_ws.parent), str(junction))
    try:
        ws = junction / "Workspace"
        mf = _mutants(ws, "r6jn", {"mutants": [KILL_CALC]})
        cmd = [sys.executable, PROG, str(mf), "--scratch", str(tmp_path / "P")]
        p = subprocess.run(cmd, cwd=str(ws), **test_conftest.windowless_kwargs(
            {"capture_output": True, "text": True, "timeout": 120}))
        assert p.returncode == 2, p.stdout + p.stderr
        assert "scratch folder must not lie inside the Workspace or contain it" in p.stdout + p.stderr
        assert not (tmp_path / "P" / "mutation-run-r6jn").exists()
        assert _cache_lines(real_ws, "r6jn") == []
    finally:
        os.rmdir(str(junction))                          # the link itself; its target is left as it is
    assert real_ws.is_dir()


# Round 7 (handoff/TASK-031-r7.md): the blocking findings of round 6's security audit.

def test_task031_r7_n1_a_mutant_id_that_is_not_a_plain_name_is_refused(tmp_path):
    """R-041, TASK-031 Requirement 1 (the mutants file is checked whole first; handoff/TASK-031-r7.md, N-1): a mutant
    id holding a path separator and `..` components exits 2 before any test, and a `.json` file the id's path would
    reach above the scratch folder is left as it was."""
    ws = _fixture(tmp_path, CALC)
    victim = tmp_path / "victim.json"
    victim.write_text("{\"keep\": true}\n", encoding="utf-8")
    bad_id = os.sep.join(["x", "..", "..", "..", "victim"])
    mf = _mutants(ws, "r7n1", {"mutants": [dict(KILL_CALC, id=bad_id)]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert victim.read_text(encoding="utf-8") == "{\"keep\": true}\n"
    assert _cache_lines(ws, "r7n1") == []


@pytest.mark.parametrize("config", ["pytest.ini", "tox.ini", "setup.cfg"])
def test_task031_r7_n2_a_pytest_configuration_holding_a_percent_sign_is_read_as_pytest_reads_it(tmp_path, config):
    """R-041 (every mutant gets a result against the version the gate reads), TASK-031 Requirement 4
    (handoff/TASK-031-r6.md, B-3, and handoff/TASK-031-r7.md, N-2: the configuration found as pytest 9.1.1 finds it):
    a root `pytest.ini`, `tox.ini` or `setup.cfg` whose pytest section holds logging formats with `%` signs, which
    pytest reads without interpolation, configures the mutant's run: its tests, collected only through that
    section, kill the mutant, exit 0."""
    section = {"pytest.ini": "[pytest]\n", "tox.ini": "[tox]\nenvlist = py312\n\n[pytest]\n",
               "setup.cfg": "[metadata]\nname = demo\n\n[tool:pytest]\n"}[config]
    files = {
        "demo/__init__.py": "",
        "demo/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from demo.calc import add\n\ndef check_add():\n    assert add(1, 2) == 3\n",
        config: section + "python_functions = check_*\nlog_cli_format = %(asctime)s %(message)s\n"
                          "log_date_format = %Y-%m-%d %H:%M:%S\n",
    }
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "r7n2", {"mutants": [dict(KILL_CALC, expect_fail=["tests/test_calc.py::check_add"])]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "r7n2")] == ["killed"]


def test_task031_r7_n1_a_mutant_id_ending_in_a_newline_is_refused(tmp_path):
    """R-041, TASK-031 Requirement 1 (handoff/TASK-031-r7.md, N-1: the id must match MUTANT_ID_RX as a whole
    string): an id that is a plain name followed by a newline exits 2 before any test, where a match that lets `$`
    stop before a trailing newline would take it."""
    ws = _fixture(tmp_path, CALC)
    mf = _mutants(ws, "r7n1n", {"mutants": [dict(KILL_CALC, id="x\n")]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert "not a valid plain name" in p.stdout + p.stderr
    assert _cache_lines(ws, "r7n1n") == []


@pytest.mark.parametrize("config,kind", [("pytest.ini", "ini"), ("tox.ini", "ini"), ("setup.cfg", "cfg")])
def test_task031_r7_n2_a_pytest_configuration_that_does_not_decode_is_refused(tmp_path, config, kind):
    """R-041, TASK-031 Requirement 4 (handoff/TASK-031-r7.md, N-2: a configuration file that does not decode or
    parse is a refusal, exit 2, never an internal error): a root `pytest.ini`, `tox.ini` or `setup.cfg` holding a
    byte that is not UTF-8 exits 2 with the file named, and no mutant is run."""
    section = {"pytest.ini": "[pytest]\n", "tox.ini": "[pytest]\n", "setup.cfg": "[tool:pytest]\n"}[config]
    ws = _fixture(tmp_path, CALC)
    (ws / config).write_bytes(section.encode("ascii") + b"python_functions = test_\xe9\n")
    _git(ws, "add", config)
    _git(ws, "commit", "-q", "-m", "a configuration that does not decode")
    mf = _mutants(ws, "r7n2d", {"mutants": [KILL_CALC]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert "invalid %s file %s" % (kind, config) in p.stdout + p.stderr
    assert _cache_lines(ws, "r7n2d") == []


def test_task031_r7_n1_a_long_plain_mutant_id_runs_its_mutant(tmp_path):
    """R-041, TASK-031 Requirement 1 (handoff/TASK-031-r7.md, N-1: each mutant's results file is named by its index
    in the loop, never from its id): a plain id of 240 characters, valid under MUTANT_ID_RX, runs and kills its
    mutant, exit 0, where a results file named from the id would pass the 255-character limit on one name
    (Review A, round 7: M53 is not equivalent)."""
    ws = _fixture(tmp_path, CALC)
    long_id = "m" * 240
    mf = _mutants(ws, "r7n1l", {"mutants": [dict(KILL_CALC, id=long_id)]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [(line["mutant"], line["outcome"]) for line in _cache_lines(ws, "r7n1l")] == [(long_id, "killed")]


@pytest.mark.parametrize("config,header", [("tox.ini", "[pytest] # the ready fixture]"),
                                           ("setup.cfg", "[tool:pytest] ; the ready fixture]")])
def test_task031_r8_a_section_header_holding_a_comment_is_not_read_otherwise_than_pytest_reads_it(
        tmp_path, config, header):
    """R-041 (a result against the version the gate reads), TASK-031 Requirement 4 (handoff/TASK-031-r6.md, B-3:
    the configuration found as pytest 9.1.1 finds it; handoff/TASK-031-r8.md): a pytest section header followed by
    a comment holding `]`, which pytest's iniconfig reads as the pytest section, is either read as pytest reads it
    or refused with exit 2; it never configures the mutant's run otherwise. Here the section's `usefixtures` makes
    the tests pass and an equivalent mutant survive under pytest's reading, so a run reading the file otherwise
    records a false kill (the security audit, round 7)."""
    files = dict(CALC)
    files["demo/__init__.py"] = "READY = False\n"
    files["tests/conftest.py"] = ("import pytest\nimport demo\n\n@pytest.fixture\ndef ready():\n"
                                  "    demo.READY = True\n")
    files["tests/test_calc.py"] = ("import demo\nfrom demo.calc import add\n\ndef test_add():\n"
                                   "    assert demo.READY\n    assert add(1, 2) == add(2, 1)\n")
    prefix = "[tox]\nenvlist = py312\n\n" if config == "tox.ini" else "[metadata]\nname = demo\n\n"
    files[config] = prefix + header + "\nusefixtures = ready\n"
    ws = _fixture(tmp_path, files)
    gate = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], cwd=str(ws),
                          **test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 120}))
    assert gate.returncode == 0, gate.stdout + gate.stderr          # pytest itself reads the header as its section
    swap = {"id": "swap", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return b + a"}],
            "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]}
    mf = _mutants(ws, "r8hd", {"mutants": [swap]})
    p = _run(ws, mf)
    outcomes = [line["outcome"] for line in _cache_lines(ws, "r8hd")]
    assert "killed" not in outcomes, p.stdout + p.stderr
    assert (p.returncode == 2 and outcomes == []) or outcomes == ["survived"], p.stdout + p.stderr


@pytest.mark.parametrize("config,kind,section", [("pytest.ini", "ini", "[pytest]"), ("tox.ini", "ini", "[pytest]"),
                                                 ("setup.cfg", "cfg", "[tool:pytest]")])
def test_task031_r9_a_pytest_configuration_iniconfig_cannot_parse_is_refused(tmp_path, config, kind, section):
    """R-041, TASK-031 Requirement 4 (handoff/TASK-031-r9.md: an `iniconfig.ParseError` is a refusal with the
    existing message, exit 2, never an internal error): a root `pytest.ini`, `tox.ini` or `setup.cfg` holding a line
    that is neither a key nor a section, which pytest 9.1.1 refuses to read as well, exits 2 with the file named, and
    no mutant is run."""
    ws = _fixture(tmp_path, dict(CALC, **{config: section + "\nthis line has no separator\n"}))
    mf = _mutants(ws, "r9pe", {"mutants": [KILL_CALC]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert "invalid %s file %s" % (kind, config) in p.stdout + p.stderr
    assert _cache_lines(ws, "r9pe") == []


@pytest.mark.parametrize("header", ["[pytest] x # the old section", "[pytest] trailing", "[pytest]x"])
def test_task031_r9_a_header_line_pytest_reads_as_a_value_is_not_read_as_a_section(tmp_path, header):
    """R-041 (a result against the version the gate reads), TASK-031 Requirement 4 (handoff/TASK-031-r6.md, B-3;
    handoff/TASK-031-r8.md, the criterion: the section names the program decides on are the ones pytest's iniconfig
    reads, or the file is refused; handoff/TASK-031-r9.md): a tox.ini line `[pytest] ...` that does not end in `]`
    once its comment is cut is, to iniconfig, a continuation of the key above it, so tox.ini holds no pytest section
    and pytest uses setup.cfg; configparser reads it as the section `pytest`. The run is either refused with exit 2
    or configured as pytest is, where setup.cfg's `usefixtures` makes an equivalent mutant survive; it never records
    a kill (Review A, round 8)."""
    files = dict(CALC)
    files["demo/__init__.py"] = "READY = False\n"
    files["tests/conftest.py"] = ("import pytest\nimport demo\n\n@pytest.fixture\ndef ready():\n"
                                  "    demo.READY = True\n")
    files["tests/test_calc.py"] = ("import demo\nfrom demo.calc import add\n\ndef test_add():\n"
                                   "    assert demo.READY\n    assert add(1, 2) == add(2, 1)\n")
    files["tox.ini"] = "[tox]\nenvlist = py312\n\n" + header + "\nminversion = 7\n"
    files["setup.cfg"] = "[tool:pytest]\nusefixtures = ready\n"
    ws = _fixture(tmp_path, files)
    gate = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], cwd=str(ws),
                          **test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 120}))
    assert gate.returncode == 0, gate.stdout + gate.stderr          # pytest itself takes setup.cfg's section
    swap = {"id": "swap", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return b + a"}],
            "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]}
    mf = _mutants(ws, "r9hd", {"mutants": [swap]})
    p = _run(ws, mf)
    outcomes = [line["outcome"] for line in _cache_lines(ws, "r9hd")]
    assert "killed" not in outcomes, p.stdout + p.stderr
    assert (p.returncode == 2 and outcomes == []) or outcomes == ["survived"], p.stdout + p.stderr


@pytest.mark.parametrize("separator", ["\x1c", "\x0c"])
def test_task031_r9_a_pytest_section_after_a_line_separator_only_iniconfig_splits_on_is_read(tmp_path, separator):
    """R-041 (a result against the version the gate reads), TASK-031 Requirement 4 (handoff/TASK-031-r6.md, B-3;
    handoff/TASK-031-r9.md): iniconfig splits a file's lines with `str.splitlines`, so a `[pytest]` header after a
    file separator or a form feed is a section to pytest, where a reader splitting on `\\n` and `\\r` only sees none;
    the tox.ini section's `usefixtures` makes an equivalent mutant survive under pytest's reading. The run is either
    refused with exit 2 or configured as pytest is; it never records a kill (the security audit, round 8)."""
    files = dict(CALC)
    files["demo/__init__.py"] = "READY = False\n"
    files["tests/conftest.py"] = ("import pytest\nimport demo\n\n@pytest.fixture\ndef ready():\n"
                                  "    demo.READY = True\n")
    files["tests/test_calc.py"] = ("import demo\nfrom demo.calc import add\n\ndef test_add():\n"
                                   "    assert demo.READY\n    assert add(1, 2) == add(2, 1)\n")
    files["tox.ini"] = "[tox]\nenvlist = py312" + separator + "[pytest]\nusefixtures = ready\n"
    ws = _fixture(tmp_path, files)
    gate = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], cwd=str(ws),
                          **test_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 120}))
    assert gate.returncode == 0, gate.stdout + gate.stderr          # pytest itself reads tox.ini's pytest section
    swap = {"id": "swap", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return b + a"}],
            "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]}
    mf = _mutants(ws, "r9sp", {"mutants": [swap]})
    p = _run(ws, mf)
    outcomes = [line["outcome"] for line in _cache_lines(ws, "r9sp")]
    assert "killed" not in outcomes, p.stdout + p.stderr
    assert (p.returncode == 2 and outcomes == []) or outcomes == ["survived"], p.stdout + p.stderr


def test_task031_r9_iniconfig_not_importable_while_reading_setup_cfg_is_refused(tmp_path, home_of_the_tests):
    """R-041, TASK-031 Requirement 4 (handoff/TASK-031-r9.md: iniconfig not importable is a refusal, exit 2):
    the `.cfg` branch, which the builder's test of the `.ini` branch does not reach (Review A, round 9): with an
    `iniconfig` that raises ImportError first on the program's PYTHONPATH, a root `setup.cfg` exits 2 with the
    message, and no mutant is run."""
    block = tmp_path / "block_iniconfig" / "iniconfig"
    block.mkdir(parents=True)
    (block / "__init__.py").write_text("raise ImportError('blocked')\n", encoding="ascii")
    ws = _fixture(tmp_path, dict(CALC, **{"setup.cfg": "[metadata]\nname = demo\n\n[tool:pytest]\n"}))
    mf = _mutants(ws, "r9ic", {"mutants": [KILL_CALC]})
    env = dict(os.environ)
    env["PYTHONPATH"] = str(block.parent) + os.pathsep + env.get("PYTHONPATH", "")
    p = _run(ws, mf, env=env)
    assert p.returncode == 2, p.stdout + p.stderr
    assert "mutation-run: pytest's iniconfig is not importable" in p.stdout + p.stderr
    assert _cache_lines(ws, "r9ic") == []


@pytest.mark.parametrize("shadow", ["iniconfig.py", "iniconfig/__init__.py"])
def test_task031_r10_a_top_level_iniconfig_in_the_project_is_refused(tmp_path, shadow):
    """R-041 (a result against the version the gate reads), TASK-031 Requirement 4 (handoff/TASK-031-r10.md): the
    gate's `python -m pytest`, started at the project's top, imports a top-level `iniconfig` module or package of the
    project before the installed one, so pytest reads its configuration with it while the program reads with the
    installed iniconfig; such a project, with a `.ini` or `.cfg` candidate at its root, exits 2 with the refusal
    naming it before any mutant runs (Review A and the security audit, round 9; convergent)."""
    ws = _fixture(tmp_path, dict(CALC, **{"tox.ini": "[tox]\nenvlist = py312\n\n[pytest]\n",
                                          shadow: "from importlib import import_module\n"}))
    mf = _mutants(ws, "r10sh", {"mutants": [KILL_CALC]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert "would shadow pytest's iniconfig" in p.stdout + p.stderr
    assert _cache_lines(ws, "r10sh") == []


@pytest.mark.parametrize("shadow,name,config", [
    ("tomllib.py", "tomllib", {"pyproject.toml": "[tool.pytest.ini_options]\n"}),
    ("pluggy/__init__.py", "pluggy", {"tox.ini": "[tox]\nenvlist = py312\n\n[pytest]\n"}),
    ("_pytest/__init__.py", "_pytest", {}),
    ("pytest.py", "pytest", {}),
])
def test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused(tmp_path, shadow, name, config):
    """R-041 (a result against the version the gate reads), TASK-031 Requirement 4 (handoff/TASK-031-r11.md): the
    gate's `python -m pytest`, started at the project's top, imports the project's own top-level module or regular
    package before a standard-library or installed one of the same name (pytest's `tomllib`, `pluggy`, `_pytest`,
    any other), while the program decides with the modules of its own environment; such a project exits 2 with the
    refusal naming the module, before any mutant runs (Review A, round 10: `tomllib`, one module along from
    round 10's `iniconfig`)."""
    files = dict(CALC, **config)
    files[shadow] = "VALUE = 1\n"
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "r11sh", {"mutants": [KILL_CALC]})
    p = _run(ws, mf)
    assert p.returncode == 2, p.stdout + p.stderr
    assert "would shadow" in p.stdout + p.stderr and name in p.stdout + p.stderr
    assert _cache_lines(ws, "r11sh") == []


@pytest.mark.parametrize("entry", ["r11_own_helper.py", "r11_notes/readme.txt", "tests_data/tomllib.json",
                                   "test/__init__.py", "tests/__init__.py"])
def test_task031_r11_a_top_level_name_shadowing_nothing_runs_its_mutant(tmp_path, entry):
    """R-041, TASK-031 Requirement 4 (handoff/TASK-031-r11.md and handoff/TASK-031-r12.md: only a module pytest
    imports to find its configuration is refused): a top-level module no such module is named after, a folder with
    no `__init__.py`, a nested file named after a standard module, a `test/` or `tests/` package (CPython ships a
    `test` package of its own, which pytest never imports; the security audit, round 11: a regression on an ordinary
    layout) run and kill their mutant, exit 0."""
    files = dict(CALC, **{entry: "VALUE = 1\n"})
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "r11ok", {"mutants": [KILL_CALC]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "r11ok")] == ["killed"]


def test_task031_r12_the_projects_own_package_installed_elsewhere_runs_its_mutant(tmp_path):
    """R-041, TASK-031 Requirement 4 (handoff/TASK-031-r12.md: only a module pytest imports to find its
    configuration is refused): the project's own package found by the program's environment outside the project,
    as after `pip install .` or an editable install from another checkout (here another copy of `demo/` on the
    caller's PYTHONPATH), is not a shadow; the run kills its mutant, exit 0 (Review A, round 11: a regression on an
    ordinary layout, round 10 ran it)."""
    other = tmp_path / "elsewhere"
    (other / "demo").mkdir(parents=True)
    (other / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (other / "demo" / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    ws = _fixture(tmp_path, CALC)
    mf = _mutants(ws, "r12own", {"mutants": [KILL_CALC]})
    env = dict(os.environ)
    env["PYTHONPATH"] = str(other) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    p = _run(ws, mf, env=env)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "r12own")] == ["killed"]


def test_task031_r13_no_test_run_of_the_program_writes_bytecode(tmp_path):
    """R-041 (each mutant's result is the result of the mutated bytes), TASK-031 round 13, Requirement 1 (handoff/TASK-031-r13.md):
    a `.pyc` records its source's size and modification time to the second, so a same-size mutant (`+` to `-`)
    written within the second after its original was compiled, or an original restored within the second after the
    mutant was, runs the stale bytecode: a mutant that never ran survives, or the next mutant's tests run the last
    one's code. CI's Windows job showed six such false survivors on round 12's code. Every pytest the program starts
    writes no bytecode: a test of the fixture asserts `sys.dont_write_bytecode` beside the killed test, so a run
    whose pytest may write bytecode is an error, exit 3, and a run that writes none kills the mutant, exit 0."""
    files = dict(CALC)
    files["tests/test_calc.py"] = ("import sys\nfrom demo.calc import add\n\ndef test_add():\n"
                                   "    assert add(1, 2) == 3\n\ndef test_no_bytecode():\n"
                                   "    assert sys.dont_write_bytecode\n")
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "r13pyc", {"mutants": [KILL_CALC]})
    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    p = _run(ws, mf, env=env)
    assert p.returncode == 0, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "r13pyc")] == ["killed"]


def test_task031_r14_a_tracked_pyc_the_tests_read_stays_in_the_copy(tmp_path):
    """R-041 (each mutant's result is the result of the mutated bytes; a kill is a test catching the mutant),
    TASK-031 round 14, Requirement 1 (handoff/TASK-031-r14.md): a project that reads bytecode (a decompiler, a
    disassembler, a packaging tool) commits `.pyc` files as test data outside any `__pycache__`; round 13 removed
    every `.pyc` from the copy, so such a test failed for a reason that is not the mutant and an equivalent mutant
    was recorded killed, exit 0. A loose `.pyc` beside its source is never read for the module, so only `__pycache__`
    folders are removed: the equivalent mutant survives, exit 1."""
    files = {"demo/__init__.py": "",
             "demo/magic.py": "def head(b):\n    return b[:4]\n",
             "tests/data/sample.pyc": "abcdefgh",
             "tests/test_magic.py": ("import os\nfrom demo.magic import head\n\n"
                                     "def test_head():\n"
                                     "    path = os.path.join(os.path.dirname(__file__), 'data', 'sample.pyc')\n"
                                     "    with open(path, 'rb') as f:\n"
                                     "        data = f.read()\n"
                                     "    assert head(data) == data[:4] == b'abcd'\n")}
    ws = _fixture(tmp_path, files)
    assert "tests/data/sample.pyc" in _git(ws, "ls-files").splitlines()
    mf = _mutants(ws, "r14pyc", {"mutants": [{
        "id": "equiv", "file": "demo/magic.py", "pairs": [{"old": "return b[:4]", "new": "return b[0:4]"}],
        "tests": ["tests/test_magic.py"], "expect_fail": ["tests/test_magic.py::test_head"]}]})
    p = _run(ws, mf)
    assert p.returncode == 1, p.stdout + p.stderr
    assert [line["outcome"] for line in _cache_lines(ws, "r14pyc")] == ["survived"]
