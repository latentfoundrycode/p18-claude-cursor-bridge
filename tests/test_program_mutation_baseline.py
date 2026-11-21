"""TASK-070: the supervisor's acceptance tests of mutation-run.py's ids and its baseline (R-090).

Committed before the builder changes bridge/cursor-bridge/mutation-run.py. Each test names R-090 and the Done-when
clause of TASK-070 (docs/BUILD_PLAN.md) it enforces. Like tests/test_mutation_run_supervisor.py, they build their
own fixture Workspaces under tmp_path and share no helper with the builder's tests, so a change to those helpers
cannot weaken them. Every line is ASCII: a non-ASCII character is built with chr()."""
import json
import os
import subprocess
import sys

import conftest as test_conftest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "mutation-run.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
       "-c", "commit.gpgsign=false"]
BS = chr(92)
# pytest's id for parametrize('word', ['caf' + chr(0xE9)]): the non-ASCII character escaped as backslash, x, e, 9
ESCAPED = "caf" + BS + "xe9"

MOD = "def double(x):\n    return x * 2\n"
PARAM_TEST = (
    "import pytest\n"
    "import mod\n"
    "\n"
    "\n"
    "@pytest.mark.parametrize('word', ['caf' + chr(0xE9)])\n"
    "def test_double(word):\n"
    "    assert mod.double(2) == 4\n"
)
PLAIN_TEST = "import mod\n\n\ndef test_double():\n    assert mod.double(2) == 4\n"


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


def _run(ws, mutants_file, *extra, timeout=60, env_extra=None):
    cmd = [sys.executable, PROG, str(mutants_file), "--scratch", str(ws.parent.parent / "scratch")] + list(extra)
    env = dict(os.environ)
    env.update(env_extra or {})
    kw = {"capture_output": True, "text": True, "timeout": timeout, "env": env}
    return subprocess.run(cmd, cwd=str(ws), **test_conftest.windowless_kwargs(kw))


def _cache_path(ws, run_id):
    return ws / "run" / "supervisor" / "mutation-cache" / ("%s.jsonl" % run_id)


def _mutant(mid, old, new, tests, expect_fail):
    return {"id": mid, "file": "mod.py", "pairs": [{"old": old, "new": new}],
            "tests": tests, "expect_fail": expect_fail}


def _mutant_lines(p, mid):
    return [ln for ln in p.stdout.splitlines() if ln.startswith(mid + ":")]


def _lines_naming(p, needle):
    return [ln for ln in (p.stdout + "\n" + p.stderr).splitlines() if needle in ln]


def _baseline_line(p, failing_id, tests_list, passing_ids=()):
    """The one line that names failing_id: it names every file of its tests list and no passing id."""
    found = _lines_naming(p, failing_id)
    assert len(found) == 1, (failing_id, p.stdout + p.stderr)
    line = found[0]
    for rel in tests_list:
        assert rel in line, (rel, line)
    for pid in passing_ids:
        assert pid not in line, (pid, line)
    return line


# --- the escaped id ------------------------------------------------------------------------------------------


def test_r090_escaped_id_matches_expect_fail_in_the_ordinary_mode(tmp_path):
    """R-090, TASK-070 Done when (the outcomes record replaces backslashes in the file part of a node id only,
    before the first `::`, in the ordinary mode, so that such an id matches its `expect_fail` entry): a mutant whose
    expect_fail names a parametrized test with a backslash escape in its id (pytest's id for 'caf' + chr(0xE9)) is
    killed and the run exits 0, never `error (expected id absent)` and exit 3."""
    ws = _fixture(tmp_path, {"mod.py": MOD, "tests/test_mod.py": PARAM_TEST})
    tid = "tests/test_mod.py::test_double[" + ESCAPED + "]"
    mf = _mutants(ws, "esc", {"mutants": [_mutant("m1", "x * 2", "x * 3", ["tests/test_mod.py"], [tid])]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert _mutant_lines(p, "m1") and "killed" in _mutant_lines(p, "m1")[0], p.stdout
    assert "expected id absent" not in p.stdout


def test_r090_escaped_id_ascii_control_is_killed(tmp_path):
    """R-090, TASK-070 Done when (such an id matches its `expect_fail` entry), the control of the test above: the
    same mutant with an ASCII parametrize id is killed and exits 0, today as after the change, so the escaped case
    fails for its id alone."""
    ws = _fixture(tmp_path, {"mod.py": MOD,
                             "tests/test_mod.py": PARAM_TEST.replace("'caf' + chr(0xE9)", "'cafe'")})
    mf = _mutants(ws, "asc", {"mutants": [_mutant(
        "m1", "x * 2", "x * 3", ["tests/test_mod.py"], ["tests/test_mod.py::test_double[cafe]"])]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "killed" in _mutant_lines(p, "m1")[0], p.stdout


def _checkpoint_fixture(tmp_path, new_test_body):
    ws = _fixture(tmp_path, {"mod.py": MOD, "tests/test_mod.py": PLAIN_TEST})
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "mod.py", MOD + "\n\ndef triple(x):\n    return x * 3\n")
    _write(ws, "tests/test_new.py",
           "import pytest\nimport mod\n\n\n"
           "@pytest.mark.parametrize('word', ['caf' + chr(0xE9)])\n"
           "def test_new(word):\n" + new_test_body)
    _git(ws, "add", "mod.py", "tests/test_new.py")
    return ws, sha


def test_r090_escaped_id_matches_new_tests_in_checkpoint_mode_failing(tmp_path):
    """R-090, TASK-070 Done when (the file-part-only replacement holds in the `--checkpoint` mode, so that such an id
    matches its `new_tests` entry): a new_tests entry naming a parametrized test by its escaped id, a test that fails
    on the checkpoint's code (mod.triple does not exist there), is reported `<id>: failing` and the run exits 0;
    today the recorded id no longer equals the entry and the run reports `<id>: not run`."""
    ws, sha = _checkpoint_fixture(tmp_path, "    assert mod.triple(2) == 6\n")
    tid = "tests/test_new.py::test_new[" + ESCAPED + "]"
    mf = _mutants(ws, "ckf", {"mutants": [], "new_tests": [tid]})
    p = _run(ws, mf, "--checkpoint", sha)
    assert p.returncode == 0, p.stdout + p.stderr
    assert tid + ": failing" in p.stdout.splitlines(), p.stdout
    assert "not run" not in p.stdout, p.stdout


def test_r090_escaped_id_matches_new_tests_in_checkpoint_mode_passing(tmp_path):
    """R-090, TASK-070 Done when (the `--checkpoint` mode: such an id matches its `new_tests` entry): the same entry
    naming a test that passes on the checkpoint's code is reported `<id>: passing on old code` and the run exits 4;
    today it reads as not run and the run exits 0, so a new test that proves nothing goes unflagged."""
    ws, sha = _checkpoint_fixture(tmp_path, "    assert mod.double(3) == 6\n")
    tid = "tests/test_new.py::test_new[" + ESCAPED + "]"
    mf = _mutants(ws, "ckp", {"mutants": [], "new_tests": [tid]})
    p = _run(ws, mf, "--checkpoint", sha)
    assert p.returncode == 4, p.stdout + p.stderr
    assert tid + ": passing on old code" in p.stdout.splitlines(), p.stdout


# --- the baseline ----------------------------------------------------------------------------------------------


def test_r090_baseline_failing_tests_list_exits_5(tmp_path):
    """R-090, TASK-070 Done when (before the mutant loop each distinct `tests` list runs once on the unmutated copy,
    and a failure in any of them ends the run with exit 5 and one line per list naming it and the failing ids, no
    mutant run and the cache untouched): a tests list holding a test that fails unmutated gives exit 5, one line
    naming both files of the list and the failing id (no passing id), no mutant outcome line, and the cache file
    byte for byte as it was."""
    files = {
        "mod.py": MOD,
        "tests/test_a.py": PLAIN_TEST,
        "tests/test_bad.py": ("import mod\n\n\ndef test_ok():\n    assert mod.double(0) == 0\n\n\n"
                              "def test_broken():\n    assert mod.double(1) == 5\n"),
    }
    ws = _fixture(tmp_path, files)
    tests = ["tests/test_a.py", "tests/test_bad.py"]
    mf = _mutants(ws, "bfail", {"mutants": [_mutant(
        "m1", "x * 2", "x * 3", tests, ["tests/test_a.py::test_double"])]})
    cache = _cache_path(ws, "bfail")
    cache.parent.mkdir(parents=True)
    seed = json.dumps({"mutant": "other", "key": "0" * 64, "outcome": "killed",
                       "time": "2026-01-01T00:00:00Z"}, separators=(",", ":")) + "\n"
    cache.write_bytes(seed.encode("utf-8"))
    p = _run(ws, mf)
    assert p.returncode == 5, p.stdout + p.stderr
    _baseline_line(p, "tests/test_bad.py::test_broken", tests,
                   passing_ids=("tests/test_bad.py::test_ok", "tests/test_a.py::test_double"))
    assert _mutant_lines(p, "m1") == [], p.stdout
    assert cache.read_bytes() == seed.encode("utf-8")


def test_r090_baseline_erroring_tests_list_exits_5(tmp_path):
    """R-090, TASK-070 Done when (a failure or an error in any of them ends the run with exit 5): a test whose
    fixture raises (an error, not a failure) on the unmutated copy gives exit 5, one line naming it, no mutant run
    and no cache file; today the mutant runs and reads `error (test error)`, exit 3."""
    files = {
        "mod.py": MOD,
        "tests/test_err.py": ("import pytest\nimport mod\n\n\n@pytest.fixture\ndef broken():\n"
                              "    raise RuntimeError('setup')\n\n\n"
                              "def test_double():\n    assert mod.double(2) == 4\n\n\n"
                              "def test_uses(broken):\n    assert broken is None\n"),
    }
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "berr", {"mutants": [_mutant(
        "m1", "x * 2", "x * 3", ["tests/test_err.py"], ["tests/test_err.py::test_double"])]})
    p = _run(ws, mf)
    assert p.returncode == 5, p.stdout + p.stderr
    _baseline_line(p, "tests/test_err.py::test_uses", ["tests/test_err.py"],
                   passing_ids=("tests/test_err.py::test_double",))
    assert _mutant_lines(p, "m1") == [], p.stdout
    assert not _cache_path(ws, "berr").exists()


def test_r090_baseline_expect_fail_failing_unmutated_is_not_a_kill(tmp_path):
    """R-090, TASK-070 Done when (an `expect_fail` test that fails unmutated is such a failure, where it read as a
    kill): the mutant's expect_fail test already fails on the unmutated code; the run exits 5 with one line naming
    the list and that id, runs no mutant and writes no cache; today the mutant reads `killed` and exits 0."""
    files = {"mod.py": MOD,
             "tests/test_mod.py": "import mod\n\n\ndef test_double():\n    assert mod.double(2) == 5\n"}
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "bef", {"mutants": [_mutant(
        "m1", "x * 2", "x * 3", ["tests/test_mod.py"], ["tests/test_mod.py::test_double"])]})
    p = _run(ws, mf)
    assert p.returncode == 5, p.stdout + p.stderr
    _baseline_line(p, "tests/test_mod.py::test_double", ["tests/test_mod.py"])
    assert _mutant_lines(p, "m1") == [], p.stdout
    assert not _cache_path(ws, "bef").exists()


ENV_FILES = {
    "mod.py": MOD,
    "tests/test_a.py": ("import os\nimport mod\n\n\ndef test_double():\n    assert mod.double(2) == 4\n\n\n"
                        "def test_env():\n    assert os.environ.get('R090_BREAK') != '1'\n"),
    "tests/test_b.py": "import mod\n\n\ndef test_double5():\n    assert mod.double(5) == 10\n",
}


def _env_cached_fixture(tmp_path, run_id, mutants):
    """A Workspace whose mutants all ran and were cached as killed. tests/test_a.py::test_env fails only when
    R090_BREAK=1 is in the environment, which no cache key covers: the code and the keys stay as they were."""
    ws = _fixture(tmp_path, ENV_FILES)
    mf = _mutants(ws, run_id, {"mutants": mutants})
    first = _run(ws, mf)
    assert first.returncode == 0, first.stdout + first.stderr      # precondition: every mutant killed and cached
    cache = _cache_path(ws, run_id)
    assert len([ln for ln in cache.read_text(encoding="utf-8").splitlines() if ln.strip()]) == len(mutants)
    return ws, mf, cache


M_A = _mutant("ma", "x * 2", "x * 3", ["tests/test_a.py"], ["tests/test_a.py::test_double"])
M_B = _mutant("mb", "x * 2", "x * 4", ["tests/test_b.py"], ["tests/test_b.py::test_double5"])


def test_r090_baseline_skipped_when_every_mutant_is_cached(tmp_path):
    """R-090, TASK-070 Done when (a run whose every mutant is served from the cache runs no baseline): with every
    mutant cached as killed and its tests list now failing unmutated (an environment variable the key does not
    cover), the run serves the mutant from the cache and exits 0, never 5. Expected to pass today as well."""
    ws, mf, cache = _env_cached_fixture(tmp_path, "bskip", [M_A])
    before = cache.read_bytes()
    p = _run(ws, mf, env_extra={"R090_BREAK": "1"})
    assert p.returncode == 0, p.stdout + p.stderr
    assert "cached" in _mutant_lines(p, "ma")[0], p.stdout
    assert "counts: run=0" in p.stdout, p.stdout
    assert _lines_naming(p, "tests/test_a.py::test_env") == [], p.stdout + p.stderr
    assert cache.read_bytes() == before


def test_r090_baseline_leaves_out_the_cached_mutants_lists(tmp_path):
    """R-090, TASK-070 Done when (each distinct `tests` list of the mutants about to run, those served from the
    cache left out): mutant ma is cached and its list now fails unmutated; mutant mb is not cached and its list
    passes. The baseline runs mb's list only, so the run is not stopped: mb runs and is killed, exit 0. Expected
    to pass today as well."""
    ws, mf, cache = _env_cached_fixture(tmp_path, "bpart", [M_A, M_B])
    lines = [ln for ln in cache.read_text(encoding="utf-8").splitlines() if ln.strip()]
    kept = [ln for ln in lines if json.loads(ln)["mutant"] == "ma"]
    assert len(kept) == 1
    cache.write_text(kept[0] + "\n", encoding="utf-8", newline="\n")
    p = _run(ws, mf, env_extra={"R090_BREAK": "1"})
    assert p.returncode == 0, p.stdout + p.stderr
    assert "cached" in _mutant_lines(p, "ma")[0], p.stdout
    mb = _mutant_lines(p, "mb")
    assert mb and "killed" in mb[0] and "cached" not in mb[0], p.stdout


def test_r090_baseline_runs_under_all_and_leaves_the_cache_untouched(tmp_path):
    """R-090, TASK-070 Done when (the baseline runs under the same environment as a mutant's run; a failure ends the
    run with exit 5, no mutant run and the cache untouched): with --all no mutant is served from the cache, so the
    baseline runs, sees the environment that breaks tests/test_a.py::test_env, exits 5 naming it, runs no mutant
    and leaves the existing cache byte for byte as it was; today the mutant runs, reads `error (unexpected
    failure)`, exits 3 and appends to the cache."""
    ws, mf, cache = _env_cached_fixture(tmp_path, "ball", [M_A])
    before = cache.read_bytes()
    p = _run(ws, mf, "--all", env_extra={"R090_BREAK": "1"})
    assert p.returncode == 5, p.stdout + p.stderr
    _baseline_line(p, "tests/test_a.py::test_env", ["tests/test_a.py"],
                   passing_ids=("tests/test_a.py::test_double",))
    assert _mutant_lines(p, "ma") == [], p.stdout
    assert cache.read_bytes() == before


def test_r090_baseline_green_mutants_run_as_before(tmp_path):
    """R-090, TASK-070 Done when (a baseline that passes changes nothing): two mutants on ordinary passing tests
    lists both run and are killed, the cache records both, and the run exits 0. A control, green today."""
    ws = _fixture(tmp_path, {"mod.py": MOD, "tests/test_a.py": PLAIN_TEST,
                             "tests/test_b.py": ENV_FILES["tests/test_b.py"]})
    mf = _mutants(ws, "bgreen", {"mutants": [
        _mutant("ma", "x * 2", "x * 3", ["tests/test_a.py"], ["tests/test_a.py::test_double"]),
        _mutant("mb", "x * 2", "x * 4", ["tests/test_b.py"], ["tests/test_b.py::test_double5"]),
    ]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    for mid in ("ma", "mb"):
        got = _mutant_lines(p, mid)
        assert got and "killed" in got[0] and "cached" not in got[0], p.stdout
    lines = [ln for ln in _cache_path(ws, "bgreen").read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert sorted(json.loads(ln)["mutant"] for ln in lines) == ["ma", "mb"]


# A conftest that logs every pytest session that runs tests (not the resolution check's --collect-only) to the file
# R090_LOG names, outside the copied tree: whether mod is unmutated, and the test files the session collected.
LOG_CONFTEST = (
    "import os\n"
    "\n"
    "\n"
    "def pytest_collection_finish(session):\n"
    "    log = os.environ.get('R090_LOG')\n"
    "    if not log or session.config.option.collectonly:\n"
    "        return\n"
    "    import mod\n"
    "    state = 'unmutated' if mod.double(2) == 4 and mod.double(5) == 10 else 'mutated'\n"
    "    files = sorted(set(item.nodeid.split('::', 1)[0] for item in session.items))\n"
    "    with open(log, 'a', encoding='utf-8') as f:\n"
    "        f.write(state + ' ' + ','.join(files) + '\\n')\n"
)


def test_r090_baseline_runs_each_distinct_tests_list_once(tmp_path):
    """R-090, TASK-070 Done when (before the mutant loop each distinct `tests` list of the mutants about to run runs
    once on the unmutated copy): m1 and m2 share one tests list, m3 has another. A conftest logs each test session:
    exactly two sessions run on unmutated code, one per distinct list, both before the first mutated session, and
    the three mutants then run and are killed, exit 0. Today no session runs on unmutated code."""
    files = {"mod.py": MOD, "conftest.py": LOG_CONFTEST, "tests/test_a.py": PLAIN_TEST,
             "tests/test_b.py": ENV_FILES["tests/test_b.py"]}
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "bonce", {"mutants": [
        _mutant("m1", "x * 2", "x * 3", ["tests/test_a.py"], ["tests/test_a.py::test_double"]),
        _mutant("m2", "x * 2", "x * 4", ["tests/test_a.py"], ["tests/test_a.py::test_double"]),
        _mutant("m3", "x * 2", "x * 5", ["tests/test_b.py"], ["tests/test_b.py::test_double5"]),
    ]})
    log = tmp_path / "sessions.log"
    p = _run(ws, mf, env_extra={"R090_LOG": str(log)})
    assert p.returncode == 0, p.stdout + p.stderr
    for mid in ("m1", "m2", "m3"):
        assert "killed" in _mutant_lines(p, mid)[0], p.stdout
    sessions = log.read_text(encoding="utf-8").splitlines() if log.is_file() else []
    unmutated = [ln for ln in sessions if ln.startswith("unmutated ")]
    mutated = [ln for ln in sessions if ln.startswith("mutated ")]
    assert sorted(unmutated) == ["unmutated tests/test_a.py", "unmutated tests/test_b.py"], sessions
    assert len(mutated) == 3, sessions
    assert all(ln.startswith("unmutated ") for ln in sessions[:2]), sessions


def test_r090_baseline_names_each_failing_list_on_its_own_line(tmp_path):
    """R-090, TASK-070 Done when (a failure in any of them ends the run with exit 5 and one line per list naming it
    and the failing ids): two distinct tests lists, each with its own test failing unmutated, give exit 5 and two
    lines, each naming its own list's failing id and not the other's; no mutant runs and no cache is written."""
    files = {
        "mod.py": MOD,
        "tests/test_a.py": PLAIN_TEST + "\n\ndef test_bad_a():\n    assert mod.double(1) == 3\n",
        "tests/test_b.py": ENV_FILES["tests/test_b.py"] + "\n\ndef test_bad_b():\n    assert mod.double(1) == 4\n",
    }
    ws = _fixture(tmp_path, files)
    mf = _mutants(ws, "btwo", {"mutants": [
        _mutant("m1", "x * 2", "x * 3", ["tests/test_a.py"], ["tests/test_a.py::test_double"]),
        _mutant("m2", "x * 2", "x * 4", ["tests/test_a.py"], ["tests/test_a.py::test_double"]),
        _mutant("m3", "x * 2", "x * 5", ["tests/test_b.py"], ["tests/test_b.py::test_double5"]),
    ]})
    p = _run(ws, mf)
    assert p.returncode == 5, p.stdout + p.stderr
    line_a = _baseline_line(p, "tests/test_a.py::test_bad_a", ["tests/test_a.py"],
                            passing_ids=("tests/test_a.py::test_double",))
    line_b = _baseline_line(p, "tests/test_b.py::test_bad_b", ["tests/test_b.py"],
                            passing_ids=("tests/test_b.py::test_double5",))
    assert line_a != line_b
    assert "test_bad_b" not in line_a and "test_bad_a" not in line_b
    for mid in ("m1", "m2", "m3"):
        assert _mutant_lines(p, mid) == [], p.stdout
    assert not _cache_path(ws, "btwo").exists()


# --- round 2: the baseline leaves the copy as it found it ------------------------------------------------------

REWRITE_MOD_TEST = (
    "import os\n"
    "import mod\n"
    "\n"
    "\n"
    "def test_double():\n"
    "    assert mod.double(2) == 4\n"
    "    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mod.py')\n"
    "    with open(path, encoding='utf-8') as f:\n"
    "        text = f.read()\n"
    "    with open(path, 'w', encoding='utf-8', newline='\\n') as f:\n"
    "        f.write(text.replace('x * 2', '2 * x'))\n"
)

REWRITE_SELF_TEST = (
    "import os\n"
    "import mod\n"
    "\n"
    "\n"
    "def test_double():\n"
    "    assert mod.double(2) == 4\n"
    "    path = os.path.abspath(__file__)\n"
    "    with open(path, encoding='utf-8') as f:\n"
    "        text = f.read()\n"
    "    with open(path, 'w', encoding='utf-8', newline='\\n') as f:\n"
    "        f.write(text.replace('mod.double(2) == ' + '4', 'mod.double(2) == ' + '4 or True', 1))\n"
)


def _cache_outcomes(ws, run_id):
    path = _cache_path(ws, run_id)
    if not path.is_file():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def test_r090_r2_baseline_that_rewrites_the_mutated_file_leaves_it_pristine(tmp_path):
    """R-090, TASK-070 Done when (each distinct tests list runs once on the unmutated copy; the mutants then run as
    before), round 2 (Review B r1): a baseline test that passes and rewrites mod.py (x * 2 becomes 2 * x) must not
    change what the mutants run on. m1 replaces x * 2 and is killed, exit 0, its cache line `killed`; a second run
    serves m1 from the cache. Today the baseline's rewrite is taken as mod.py's original, m1 is `not applied`, exit 1,
    and `not applied` is cached under the key of the bytes before the baseline."""
    ws = _fixture(tmp_path, {"mod.py": MOD, "tests/test_mod.py": REWRITE_MOD_TEST})
    mf = _mutants(ws, "brw", {"mutants": [_mutant(
        "m1", "x * 2", "x * 3", ["tests/test_mod.py"], ["tests/test_mod.py::test_double"])]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert _mutant_lines(p, "m1") and "killed" in _mutant_lines(p, "m1")[0], p.stdout
    assert "not applied" not in _mutant_lines(p, "m1")[0], p.stdout
    assert [c.get("outcome") for c in _cache_outcomes(ws, "brw")] == ["killed"]
    p2 = _run(ws, mf)
    assert p2.returncode == 0, p2.stdout + p2.stderr
    assert _mutant_lines(p2, "m1") and "cached" in _mutant_lines(p2, "m1")[0], p2.stdout
    assert (ws / "mod.py").read_text(encoding="utf-8") == MOD


def test_r090_r2_baseline_that_rewrites_a_test_file_leaves_it_pristine(tmp_path):
    """R-090, TASK-070 Done when (the mutants run as before, on the copy the cache key read), round 2 (Review B r1):
    a baseline test that passes and rewrites its own test file so that it can no longer fail must not weaken the
    mutants' tests. m1 is killed by the test as committed, exit 0, its cache line `killed`. Today the mutants run
    the rewritten test, m1 survives and the run exits 1."""
    ws = _fixture(tmp_path, {"mod.py": MOD, "tests/test_mod.py": REWRITE_SELF_TEST})
    mf = _mutants(ws, "brs", {"mutants": [_mutant(
        "m1", "x * 2", "x * 3", ["tests/test_mod.py"], ["tests/test_mod.py::test_double"])]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert _mutant_lines(p, "m1") and "killed" in _mutant_lines(p, "m1")[0], p.stdout
    assert [c.get("outcome") for c in _cache_outcomes(ws, "brs")] == ["killed"]
    assert (ws / "tests" / "test_mod.py").read_text(encoding="utf-8") == REWRITE_SELF_TEST


# --- round 3: the baseline runs in a copy of its own ---------------------------------------------------------

REPLACE_SELF_WITH_DIR_TEST = (
    "import os\n"
    "import mod\n"
    "\n"
    "\n"
    "def test_double():\n"
    "    assert mod.double(2) == 4\n"
    "    path = os.path.abspath(__file__)\n"
    "    os.remove(path)\n"
    "    os.mkdir(path)\n"
)

ADD_CONFTEST_TEST = (
    "import os\n"
    "import mod\n"
    "\n"
    "\n"
    "def test_double():\n"
    "    assert mod.double(2) == 4\n"
    "    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conftest.py')\n"
    "    with open(path, 'w', encoding='utf-8', newline='\\n') as f:\n"
    "        f.write('import pytest' + chr(10) + chr(10) + chr(10) + 'def pytest_runtest_setup(item):' + chr(10)\n"
    "                + '    pytest.skip(' + repr('added by the baseline') + ')' + chr(10))\n"
)


def test_r090_r3_baseline_that_replaces_a_test_file_with_a_folder_leaves_the_mutants_copy_alone(tmp_path):
    """R-090, TASK-070 Done when (each distinct tests list runs once on the unmutated copy; the mutants then run as
    before), round 3 (Review B r2): a baseline test that passes and replaces its own file with a folder of the same
    name must not change what the mutants run on. m1 is killed by the test as committed, exit 0, its cache line
    `killed`. On round 2's code the rebuild copies the file into that folder, the recorded id no longer matches, and
    m1 reads `error (expected id absent)`, exit 3."""
    ws = _fixture(tmp_path, {"mod.py": MOD, "tests/test_mod.py": REPLACE_SELF_WITH_DIR_TEST})
    mf = _mutants(ws, "brd", {"mutants": [_mutant(
        "m1", "x * 2", "x * 3", ["tests/test_mod.py"], ["tests/test_mod.py::test_double"])]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert _mutant_lines(p, "m1") and "killed" in _mutant_lines(p, "m1")[0], p.stdout
    assert [c.get("outcome") for c in _cache_outcomes(ws, "brd")] == ["killed"]
    assert (ws / "tests" / "test_mod.py").is_file()


def test_r090_r3_baseline_that_adds_a_conftest_leaves_the_mutants_copy_alone(tmp_path):
    """R-090, TASK-070 Done when (the mutants then run as before, on the copy the cache key read), round 3 (Review B
    r2; HARDENING lead 9): a baseline test that passes and adds a tests/conftest.py skipping every test must not
    change what the mutants run on. m1 is killed, exit 0, its cache line `killed`. On round 2's code the added
    conftest stays in the copy, the mutant's test is skipped, and m1 survives, exit 1."""
    ws = _fixture(tmp_path, {"mod.py": MOD, "tests/test_mod.py": ADD_CONFTEST_TEST})
    mf = _mutants(ws, "brc", {"mutants": [_mutant(
        "m1", "x * 2", "x * 3", ["tests/test_mod.py"], ["tests/test_mod.py::test_double"])]})
    p = _run(ws, mf)
    assert p.returncode == 0, p.stdout + p.stderr
    assert _mutant_lines(p, "m1") and "killed" in _mutant_lines(p, "m1")[0], p.stdout
    assert [c.get("outcome") for c in _cache_outcomes(ws, "brc")] == ["killed"]
    assert not (ws / "tests" / "conftest.py").exists()
