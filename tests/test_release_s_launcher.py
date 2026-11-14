"""Release S: the launcher's three additions (bridge-run.py).

C18 (ISS-030): a builder, review or watch run that ended at its limit measures the limit, not the work; it is never marked healthy and
never counts toward the learned limit, so one over-long run no longer lengthens every later one. A test run keeps its exit-124 rule.

The test target: a pytest or unittest run through the launcher reads the project's own tests; a target that resolves outside the launch
folder is refused before anything starts.

M1: a builder brief of round two or later carries `Round cause: <cause> - <one line>`; the launcher reads the cause into the run log
(`cause`) for pace-report.py, logs `unstated` with a note where the line is missing or names no known cause, and never refuses for it.

Register: R-074 is held by the test_c18_ tests; R-073's target rule (the command line, the environment, the key file) by the tests
of the test target; R-072's cause in the run log and the pace report's two lines by the test_m1_ and test_m1_m2_ tests."""
import json
import os
import subprocess
import sys

import pytest

import test_pace_report as P
from test_task032_supervisor_launcher import Lab, assert_ran, build, launch, write_brief

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
PACE = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "pace-report.py")


def write_rows(folder, rows):
    log = folder / "run" / "launcher"
    log.mkdir(parents=True, exist_ok=True)
    (log / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def rows_of(folder):
    return [json.loads(line) for line in (folder / "run" / "launcher" / "runs.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------- C18: the learned limit


@pytest.mark.parametrize("kind,default", [("builder", 7200), ("review", 3600), ("watch", 3600)])
def test_c18_a_run_ended_at_its_limit_never_raises_the_learned_limit(program, tmp_path, kind, default):
    """The row is on record as healthy (as the TDP's 7201-second builder run of 2026-10-12 is): it no longer counts. The same
    seconds at exit 0 do, so the test can fail."""
    br = program("bridge-run")
    row = {"id": "2026-10-12T10:00:00Z", "kind": kind, "seconds": default + 1, "exit": 124, "healthy": True}
    write_rows(tmp_path, [row])
    limit, why = br.learned_limit(kind, str(tmp_path))
    assert limit == default and why == "the default for %s" % kind, (limit, why)
    write_rows(tmp_path, [dict(row, exit=0)])
    assert br.learned_limit(kind, str(tmp_path))[0] == int(1.5 * (default + 1)), "a healthy run that ended by itself is learned from"


def test_c18_a_test_run_and_a_driver_run_keep_their_own_exits(program, tmp_path):
    """A test run ended at its limit whose kept work merged still counts (release A2's finding 5); a driver run counts at exit 0 or 1
    and never at 124."""
    br = program("bridge-run")
    write_rows(tmp_path, [{"id": "2026-10-07T12:00:00Z", "kind": "test", "seconds": 2000, "exit": 124, "healthy": True}])
    assert br.learned_limit("test", str(tmp_path))[0] == 3000
    write_rows(tmp_path, [{"id": "2026-10-07T12:00:00Z", "kind": "driver", "seconds": 6000, "exit": 1, "healthy": True}])
    assert br.learned_limit("driver", str(tmp_path))[0] == 9000
    write_rows(tmp_path, [{"id": "2026-10-07T12:00:00Z", "kind": "driver", "seconds": 7200, "exit": 124, "healthy": True}])
    assert br.learned_limit("driver", str(tmp_path))[0] == 7200


@pytest.mark.parametrize("kind", ["builder", "review", "watch"])
def test_c18_healthy_refuses_a_run_that_ended_at_its_limit(tmp_path, kind):
    """`--healthy` on such a run: exit 1, the reason, and the log untouched."""
    row = {"id": "2026-10-12T10:00:00Z", "kind": kind, "seconds": 7201, "exit": 124, "healthy": None}
    write_rows(tmp_path, [row])
    p = subprocess.run([sys.executable, PROG, "--healthy", row["id"]], capture_output=True, text=True, cwd=str(tmp_path))
    assert p.returncode == 1 and "refused - a %s run that ended at its limit is not marked healthy" % kind in p.stderr, p.stderr
    assert "explicit --limit" in p.stderr and rows_of(tmp_path) == [row]


def test_c18_healthy_still_marks_a_test_run_at_its_limit_and_a_builder_run_that_ended_by_itself(tmp_path):
    rows = [{"id": "2026-10-12T10:00:00Z", "kind": "test", "seconds": 1800, "exit": 124, "healthy": None},
            {"id": "2026-10-12T11:00:00Z", "kind": "builder", "seconds": 5000, "exit": 0, "healthy": None}]
    write_rows(tmp_path, rows)
    for row in rows:
        p = subprocess.run([sys.executable, PROG, "--healthy", row["id"]], capture_output=True, text=True, cwd=str(tmp_path))
        assert p.returncode == 0 and "marked healthy" in p.stderr, p.stderr
    assert [r["healthy"] for r in rows_of(tmp_path)] == [True, True]


# ---------------------------------------------------------------- the test target


def suite_run(folder, *target, allow_any=False):
    env = dict(os.environ, LOCALAPPDATA=str(folder.parent / "localappdata"))
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    if allow_any:
        env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    return subprocess.run([sys.executable, PROG, "--limit", "120", "--kind", "test", "--", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider"] + list(target),
                          capture_output=True, text=True, cwd=str(folder), env=env)


@pytest.fixture
def project(tmp_path):
    ws = tmp_path / "ws"
    (ws / "tests").mkdir(parents=True)
    (ws / "tests" / "test_inside.py").write_text("def test_inside():\n    assert True\n", encoding="utf-8")
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "test_probe.py").write_text("import pathlib\n\n\ndef test_probe():\n    pathlib.Path(__file__).with_name('probe-ran.txt').write_text('ran')\n", encoding="utf-8")
    return ws, outside


@pytest.mark.parametrize("form", ["absolute", "relative", "node"])
def test_a_test_target_outside_the_launch_folder_is_refused_before_it_runs(project, form):
    ws, outside = project
    target = {"absolute": str(outside / "test_probe.py"), "relative": os.path.join("..", "elsewhere", "test_probe.py"),
              "node": str(outside / "test_probe.py") + "::test_probe"}[form]
    p = suite_run(ws, target, allow_any=(form == "node"))      # the tests' own switch exempts nothing here
    assert p.returncode == 125 and "refused - the test target" in p.stderr and "lies outside the folder the launcher runs in" in p.stderr, p.stderr
    assert "bridge-run: started" not in p.stderr and not (outside / "probe-ran.txt").exists(), "the probe ran"
    assert not (ws / "run" / "launcher" / "runs.jsonl").exists(), "a refused run is not logged"


def _package_link(link, target):
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
    except (OSError, NotImplementedError):
        import _winapi
        _winapi.CreateJunction(str(target), str(link))


def test_r078_npm_prefix_through_an_inbound_link_is_refused(tmp_path):
    """R-078: the folder rule walks path components and refuses a junction that leads back inside."""
    ws = tmp_path / "ws"
    (ws / "frontend").mkdir(parents=True)
    (ws / "run").mkdir()
    target = ws / "frontend"
    link = ws / "in-link"
    try:
        _package_link(link, target)
    except (OSError, NotImplementedError):
        pytest.skip("this account can make neither a symbolic link nor a junction")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / ("npm.cmd" if sys.platform == "win32" else "npm")
    stub.write_text("@echo STAND-IN\n" if sys.platform == "win32" else "#!/bin/sh\necho STAND-IN\n", encoding="ascii")
    if sys.platform != "win32":
        stub.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.lower().startswith(("npm_config_", "pnpm_config_", "yarn_"))}
    env.update(LOCALAPPDATA=str(tmp_path / "localappdata"), PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        ok = subprocess.run([sys.executable, PROG, "--limit", "60", "--kind", "test", "--", "npm", "--prefix", "frontend", "test"],
                            capture_output=True, text=True, cwd=str(ws), env=env, timeout=120, creationflags=flags)
        assert ok.returncode == 0 and "STAND-IN" in ok.stdout, (ok.returncode, ok.stderr, ok.stdout)
        p = subprocess.run([sys.executable, PROG, "--limit", "60", "--kind", "test", "--", "npm", "--prefix", "in-link", "test"],
                           capture_output=True, text=True, cwd=str(ws), env=env, timeout=120, creationflags=flags)
        assert p.returncode == 125 and "defect" in p.stderr and "--prefix" in p.stderr and "bridge-run: started" not in p.stderr, p.stderr
    finally:
        if link.exists():
            os.rmdir(str(link)) if os.name == "nt" else os.unlink(str(link))


def test_a_target_inside_the_launch_folder_runs_whatever_its_form(project):
    """A file, a node of it, the folder, a `-k` expression with a slash and no target at all: each runs."""
    ws, _ = project
    for target in (["tests/test_inside.py"], [str(ws / "tests" / "test_inside.py") + "::test_inside"], ["tests", "-k", "inside or a/b"], []):
        p = suite_run(ws, *target)
        assert p.returncode == 0 and "bridge-run: exit 0" in p.stderr, (target, p.stderr)


def test_the_target_rule_reads_every_runner_form_of_pytest_and_unittest(program, tmp_path):
    """In-process, over the forms `named_suite` accepts: the word after which targets begin differs per runner."""
    br = program("bridge-run")
    base = str(tmp_path)
    out = str(tmp_path.parent / "x" / "test_a.py")
    for argv in (["pytest", out], ["python", "-m", "pytest", "-q", out], ["py", "-m", "pytest", out], ["uv", "run", "--frozen", "pytest", out],
                 ["python", "-m", "unittest", out], ["python3", "-m", "pytest", "tests/a.py", out + "::test_x"]):
        assert br.outside_target(argv, base) is not None, argv
    for argv in (["pytest"], ["pytest", "tests", "-k", "x"], ["python", "-m", "pytest", "tests/test_a.py::test_x", "--junitxml=" + out],
                 ["python", "-m", "unittest", "tests.test_a"], ["npm", "test", out], ["go", "test", out]):
        assert br.outside_target(argv, base) is None, argv


def test_the_target_rule_reads_what_leads_outside_by_another_word(program, tmp_path):
    """Review A, round 1 (both reviewers reproduced each): uv's own folder options before the word pytest, a file of
    arguments, the configuration file pytest is told to load. Each led a run outside and passed."""
    br = program("bridge-run")
    base = tmp_path / "ws"
    (base / "sub" / "tests").mkdir(parents=True)
    out = str(tmp_path / "elsewhere")
    for argv in (["uv", "run", "--project", out, "pytest", "tests"], ["uv", "run", "--directory", out, "pytest"],
                 ["uv", "run", "--directory=" + out, "--frozen", "pytest", "tests"], ["uv", "run", "--directory", "sub", "pytest", "../../elsewhere"],
                 ["python", "-m", "pytest", "@" + os.path.join(out, "args.txt")], ["pytest", "@args.txt"],
                 ["pytest", "--config-file=" + os.path.join(out, "pytest.ini")], ["pytest", "--config-file", os.path.join(out, "pytest.ini"), "tests"],
                 ["pytest", "--confcutdir", out, "tests"]):
        assert br.outside_target(argv, str(base)) is not None, argv
    for argv in (["uv", "run", "--project", "sub", "pytest", "sub/tests"], ["uv", "run", "--directory", "sub", "pytest", "tests", ".."],
                 ["pytest", "--config-file", "sub/pytest.ini", "sub/tests"]):
        assert br.outside_target(argv, str(base)) is None, argv


def test_unittest_s_start_and_top_folders_are_read_in_every_form_argparse_takes(program, tmp_path):
    """Review B, round 1: `-s=<dir> -t=<dir>`, `--start-directory=<dir>` and `-s<dir>` ran a TestCase outside the launch
    folder, because only the separate-word form met the target rule. argparse also takes a long option by its prefix and a
    short one behind flags in one word; `--rootdir` reaches `uv run pytest`, whose escape list does not hold it."""
    br = program("bridge-run")
    base = tmp_path / "ws"
    (base / "tests").mkdir(parents=True)
    out = str(tmp_path / "elsewhere")
    up = os.path.join("..", "elsewhere")
    for words in (["-s=" + out, "-t=" + out], ["-s" + out], ["-t" + out], ["-s=" + up, "-t=" + up], ["--start-directory=" + out],
                  ["--top-level-directory=" + out], ["--start=" + out], ["--top", out], ["--s", out], ["-vs" + out], ["-vs", out],
                  ["-bt=" + out], ["-s", out], ["-s", "tests", "-t", out]):
        argv = ["python", "-m", "unittest", "discover"] + words
        assert br.outside_target(argv, str(base)) is not None, argv
    for words in (["-s", "tests", "-t", "."], ["-s=tests"], ["-stests", "-v"], ["--start-directory=tests", "--top=."], ["-k", out], ["-vk", out],
                  ["--pattern", "test*.py"], ["-f", "-b"], ["-vs", "tests"]):
        argv = ["python", "-m", "unittest", "discover"] + words
        assert br.outside_target(argv, str(base)) is None, argv
    assert br.outside_target(["uv", "run", "pytest", "--rootdir=" + out, "tests"], str(base)) == "--rootdir=" + out
    assert br.outside_target(["uv", "run", "pytest", "--rootdir", out, "tests"], str(base)) == "--rootdir " + out
    assert br.outside_target(["uv", "run", "pytest", "--rootdir=.", "tests", "-s"], str(base)) is None, "pytest's own -s is a flag"


def test_an_ini_override_that_names_an_outside_folder_is_a_target_by_another_word(program, tmp_path):
    """`-o testpaths=<dir>` has pytest collect there when no target is given, and `-o pythonpath=<dir>` has it import from
    there: the same run as an outside target. Every form pytest reads the option in; another setting's value is no path."""
    br = program("bridge-run")
    base = tmp_path / "ws"
    (base / "tests").mkdir(parents=True)
    out = str(tmp_path / "elsewhere")
    for words in (["-o", "testpaths=" + out], ["-otestpaths=" + out], ["--override-ini=testpaths=" + out], ["--override-ini", "pythonpath=" + out],
                  ["-qo", "testpaths=" + out], ["-o", "testpaths=tests " + out], ["-o", "pythonpath=" + os.path.join("..", "elsewhere"), "tests"],
                  ["-o", "addopts=--rootdir " + out, "tests"], ["--override-ini=addopts=-q", "tests"]):   # options in a value are read by no rule
        argv = ["python", "-m", "pytest"] + words
        assert br.outside_target(argv, str(base)) is not None, argv
    for words in (["-o", "testpaths=tests"], ["-o", "pythonpath=. tests"], ["-o", "junit_family=xunit2"], ["-o", "cache_dir=" + out, "tests"],
                  ["--override-ini=addopts=", "tests"], ["-o", "addopts=", "tests"], ["-qo", "console_output_style=classic"]):
        argv = ["python", "-m", "pytest"] + words
        assert br.outside_target(argv, str(base)) is None, argv


def test_an_ini_value_is_read_as_pytest_reads_it_by_the_shell_s_rules(program, tmp_path):
    """Review B, round 2: `-o testpaths="../elsewhere"` with the quote marks inside the value ran the outside test, since the
    value was split at white space and pytest splits it as a shell does. Both readings are held to the rule, and a value
    the shell's rules cannot read (an open quote) is refused."""
    br = program("bridge-run")
    base = tmp_path / "ws"
    (base / "tests").mkdir(parents=True)
    out = str(tmp_path / "elsewhere").replace("\\", "/")
    for setting in ('testpaths="../elsewhere"', "testpaths='../elsewhere'", 'pythonpath="%s"' % out, 'testpaths=tests "../else where"',
                    'testpaths="../elsewhere', "pythonpath=tests '%s'" % out):
        for words in (["-o", setting], ["--override-ini=" + setting], ["-o" + setting]):
            assert br.outside_target(["python", "-m", "pytest"] + words, str(base)) is not None, words
    for setting in ('testpaths="tests"', "pythonpath='.' tests", 'testpaths="tests/sub dir"'):
        assert br.outside_target(["python", "-m", "pytest", "-o", setting], str(base)) is None, setting
    # pytest reads an ini path against the folder of the configuration file it found, which may lie deeper than the launch
    # folder: a relative one that climbs is refused wherever it lands when read from here.
    for setting in ("pythonpath=../ws/tests", 'testpaths="../ws/tests"', "pythonpath=tests/../../ws"):
        assert br.outside_target(["python", "-m", "pytest", "-o", setting, "tests"], str(base)) is not None, setting


def test_options_pytest_reads_from_the_environment_are_held_to_the_command_line_s_rules(program, tmp_path):
    """Review B, round 2: `PYTEST_ADDOPTS=../elsewhere` with a plain `python -m pytest` ran the outside test. Its words are
    read both ways a value's words can be and held to the escape list and the target rule; `PYTEST_PLUGINS` is `-p` by
    another route; names are compared as Windows reads them. A unittest run reads neither."""
    br = program("bridge-run")
    base = tmp_path / "ws"
    (base / "tests").mkdir(parents=True)
    out = str(tmp_path / "elsewhere").replace("\\", "/")
    run = ["python", "-m", "pytest", "-q"]
    for env in ({"PYTEST_ADDOPTS": "../elsewhere"}, {"PYTEST_ADDOPTS": '"%s"' % out}, {"PYTEST_ADDOPTS": "-p probeplugin"}, {"PYTEST_ADDOPTS": "--rootdir " + out},
                {"PYTEST_ADDOPTS": "-c %s/pytest.ini" % out}, {"PYTEST_ADDOPTS": "-o testpaths=" + out}, {"PYTEST_ADDOPTS": '-k "open'},
                {"pytest_addopts": "../elsewhere"}, {"PYTEST_PLUGINS": "probeplugin"}, {"Pytest_Plugins": "a,b"},
                {"PYTEST_ADDOPTS": "-q --"}):                              # a bare `--` would turn the command's own option values into targets
        for argv in (run, ["pytest"], ["uv", "run", "--frozen", "pytest", "tests"]):
            assert br.outside_by_environment(argv, env, str(base)) == list(env)[0].upper(), (env, argv)
    for env in ({}, {"PYTEST_ADDOPTS": ""}, {"PYTEST_ADDOPTS": "  "}, {"PYTEST_ADDOPTS": "--color=yes -p no:cacheprovider -q"}, {"PYTEST_ADDOPTS": '-k "a or b" tests'},
                {"PYTEST_PLUGINS": ""}, {"PYTHONPATH": out}):
        assert br.outside_by_environment(run, env, str(base)) is None, env
    (base / "sub").mkdir()
    there = ["uv", "run", "--directory", "sub", "pytest"]                  # the environment's targets are read against the folder the run's own are
    assert br.outside_by_environment(there, {"PYTEST_ADDOPTS": "../tests"}, str(base)) is None
    assert br.outside_by_environment(there, {"PYTEST_ADDOPTS": "../../elsewhere"}, str(base)) == "PYTEST_ADDOPTS"
    # Review A's reads of the round's fix: uv reads `UV_WORKING_DIR` as `--directory` and `UV_PROJECT` as `--project` where the
    # command gives none; its other variables are held to a list as the command's options are, so the interpreter, its
    # environment, a file of variables or of settings and a name the launcher does not know are refused. A run without uv
    # reads none of them.
    uv = ["uv", "run", "--frozen", "pytest", "tests"]
    for env, name in (({"UV_WORKING_DIR": out}, "UV_WORKING_DIR"), ({"UV_PROJECT": "../elsewhere"}, "UV_PROJECT"), ({"uv_working_dir": out}, "UV_WORKING_DIR"),
                      ({"UV_ENV_FILE": ".env"}, "UV_ENV_FILE"), ({"UV_WORKING_DIR": "sub", "PYTEST_ADDOPTS": "../../elsewhere"}, "PYTEST_ADDOPTS"),
                      ({"UV_PYTHON": out + "/Scripts/python.exe"}, "UV_PYTHON"), ({"uv_project_environment": out}, "UV_PROJECT_ENVIRONMENT"),
                      ({"UV_CONFIG_FILE": "uv.toml"}, "UV_CONFIG_FILE"), ({"UV_A_LATER_NAME": "1"}, "UV_A_LATER_NAME")):
        assert br.outside_by_environment(uv, env, str(base)) == name, env
    for env in ({"UV_WORKING_DIR": "sub"}, {"UV_PROJECT": "."}, {"UV_WORKING_DIR": "sub", "PYTEST_ADDOPTS": "../tests"}, {"UV_CACHE_DIR": out}, {"UV_FROZEN": "1"},
                {"UV_ENV_FILE": ""}, {"UV_LINK_MODE": "copy", "UV_PYTHON_INSTALL_DIR": out, "UV_NO_PROGRESS": "1"}, {"UVICORN_PORT": "1"},
                {"UV": "uv.exe", "UV_RUN_RECURSION_DEPTH": "1"}):          # what uv itself sets in a process it starts
        assert br.outside_by_environment(uv, env, str(base)) is None, env
    assert br.outside_by_environment(run, {"UV_WORKING_DIR": out, "UV_ENV_FILE": ".env", "UV_PYTHON": out}, str(base)) is None
    assert br.outside_by_environment(["python", "-m", "unittest", "discover"], {"PYTEST_ADDOPTS": "../elsewhere"}, str(base)) is None
    assert br.outside_by_environment(["npm", "test"], {"PYTEST_PLUGINS": "x"}, str(base)) is None


@pytest.mark.parametrize("route", ["environment", "key file", "uv's folder"])
def test_an_outside_target_in_the_environment_is_refused_before_the_run_starts(project, route):
    """Through the program, by the launcher's own environment, by a key file's line and by uv's own variable: exit 125,
    the variable named and its value not printed, nothing started, the probe not run."""
    ws, outside = project
    env = dict(os.environ, LOCALAPPDATA=str(ws.parent / "localappdata"))
    for name in ("BRIDGE_RUN_ALLOW_ANY", "PYTEST_ADDOPTS", "PYTEST_PLUGINS", "UV_WORKING_DIR", "UV_PROJECT", "UV_ENV_FILE"):
        env.pop(name, None)
    flags, name, run = ["--limit", "120", "--kind", "test"], "PYTEST_ADDOPTS", ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    if route == "environment":
        env["PYTEST_ADDOPTS"] = str(outside).replace("\\", "/")
    elif route == "key file":
        keys = ws.parent / "keys.env"
        keys.write_text("PYTEST_ADDOPTS=%s\n" % str(outside).replace("\\", "/"), encoding="utf-8")
        flags += ["--key-file", str(keys)]
    else:
        name, run = "UV_WORKING_DIR", ["uv", "run", "--frozen", "pytest", "-q", "-p", "no:cacheprovider"]
        env[name] = str(outside)
    p = subprocess.run([sys.executable, PROG] + flags + ["--"] + run, capture_output=True, text=True, cwd=str(ws), env=env)
    assert p.returncode == 125 and "refused - %s in this run's environment" % name in p.stderr, p.stderr
    assert "elsewhere" not in p.stderr, "the value is not printed"
    assert "bridge-run: started" not in p.stderr and not (outside / "probe-ran.txt").exists(), "the probe ran"


def test_a_key_file_that_cannot_be_read_refuses_a_test_run_before_it_starts(project):
    """The key file's lines are checked before the run starts and never read a second time for it: one that cannot be
    read at the check refuses there, so no line reaches a run unchecked."""
    ws, _ = project
    env = dict(os.environ, LOCALAPPDATA=str(ws.parent / "localappdata"))
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    for flags in (["--key-file", str(ws.parent / "no-such-keys.env")], ["--key-file", str(ws / "keys.env")], ["--key-file"]):
        p = subprocess.run([sys.executable, PROG, "--limit", "120", "--kind", "test"] + flags + ["--", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                           capture_output=True, text=True, cwd=str(ws), env=env)
        assert p.returncode == 125 and "refused - key file" in p.stderr and "bridge-run: started" not in p.stderr, (flags, p.stderr)


def test_a_unittest_discovery_started_outside_is_refused_before_it_runs(project):
    """The same through the program: the form that ran in the review exits 125 and the outside case never starts."""
    ws, outside = project
    (outside / "test_case.py").write_text("import pathlib\nimport unittest\n\n\nclass Probe(unittest.TestCase):\n    def test_probe(self):\n"
                                          "        pathlib.Path(__file__).with_name('probe-ran.txt').write_text('ran')\n", encoding="utf-8")
    env = dict(os.environ, LOCALAPPDATA=str(ws.parent / "localappdata"))
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    for words in (["-s=" + str(outside), "-t=" + str(outside)], ["-s" + str(outside)], ["--start-directory=" + str(outside)]):
        p = subprocess.run([sys.executable, PROG, "--limit", "120", "--kind", "test", "--", "python", "-m", "unittest", "discover"] + words,
                           capture_output=True, text=True, cwd=str(ws), env=env)
        assert p.returncode == 125 and "refused - the test target" in p.stderr, (words, p.stderr)
        assert "bridge-run: started" not in p.stderr and not (outside / "probe-ran.txt").exists(), "the outside case ran"


def test_an_option_s_value_is_no_target_wherever_it_points(program, tmp_path):
    """A report, a log or an ignored path named as a separate word: its value may lie in a temporary folder, and the run is
    not refused for it (Review A, round 1: each was refused with 125, which stops the loop)."""
    br = program("bridge-run")
    out = str(tmp_path.parent / "x" / "report.xml")
    for option in ("--junitxml", "--junit-xml", "--log-file", "--ignore", "--deselect", "--cov-report", "-o", "-W", "-k", "-m", "--html", "--alluredir",
                   "--json-report-file", "--benchmark-json"):
        assert br.outside_target(["python", "-m", "pytest", "tests", option, out, "tests/test_a.py"], str(tmp_path)) is None, option
    assert br.outside_target(["pytest", "--junitxml", out, out], str(tmp_path)) == out, "the word after the value is a target again"


def _link(link, target):
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
    except (OSError, NotImplementedError):
        try:
            import _winapi
            _winapi.CreateJunction(str(target), str(link))
        except (ImportError, OSError):
            pytest.skip("this account can make neither a symbolic link nor a junction")


def test_a_link_inside_the_launch_folder_that_leads_outside_is_outside(program, tmp_path):
    br = program("bridge-run")
    base, outside = tmp_path / "ws", tmp_path / "elsewhere"
    (base / "tests").mkdir(parents=True)
    outside.mkdir()
    _link(base / "tests" / "ext", outside)
    try:
        assert br.outside_target(["pytest", "tests/ext/test_probe.py"], str(base)) is not None
        assert br.outside_target(["pytest", "tests"], str(base)) is None
    finally:
        os.rmdir(str(base / "tests" / "ext")) if os.name == "nt" else os.unlink(str(base / "tests" / "ext"))


def test_a_worktree_of_the_same_repository_is_inside(program, tmp_path):
    """Rule 39 keeps a second live branch in a worktree under `<root>/Worktrees/`, beside the Workspace: its suite is
    launched from the Workspace by its path and is the project's own; a folder that is no worktree stays outside."""
    br = program("bridge-run")
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    ws, tree = tmp_path / "Workspace", tmp_path / "Worktrees" / "task-002"
    ws.mkdir()
    for args in (["init", "-q", "-b", "main"], ["commit", "-q", "--allow-empty", "-m", "base"], ["worktree", "add", "-q", "-b", "task-002", str(tree)]):
        p = subprocess.run(["git"] + args, cwd=str(ws), capture_output=True, text=True, env=env)
        assert p.returncode == 0, p.stderr
    for argv in (["python", "-m", "pytest", str(tree / "tests")], ["uv", "run", "--directory", str(tree), "pytest", "tests"],
                 ["pytest", os.path.join("..", "Worktrees", "task-002", "tests", "test_a.py") + "::test_a"]):
        assert br.outside_target(argv, str(ws)) is None, argv
    assert br.outside_target(["pytest", str(tmp_path / "Worktrees" / "probe" / "test_a.py")], str(ws)) is not None
    # a worktree registered anywhere else, as a run could make one in a temporary folder in passing, is outside (Review A, round 2)
    stray = tmp_path / "elsewhere" / "scratch"
    p = subprocess.run(["git", "worktree", "add", "-q", "--detach", str(stray)], cwd=str(ws), capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr
    assert br.outside_target(["pytest", str(stray / "tests")], str(ws)) is not None
    assert br.outside_target(["uv", "run", "--directory", str(stray), "pytest"], str(ws)) is not None
    assert br.outside_target(["python", "-m", "pytest", str(tree / "tests")], str(ws)) is None, "the one under Worktrees/ still is inside"
    # launched in the worktree itself, the Workspace and a sibling worktree are the same project (Review A's delta read: the
    # sibling folder was looked for beside the worktree, `Worktrees/Worktrees`, and neither counted)
    sibling = tmp_path / "Worktrees" / "task-003"
    p = subprocess.run(["git", "worktree", "add", "-q", "-b", "task-003", str(sibling)], cwd=str(ws), capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr
    for target in (str(ws / "tests"), str(sibling / "tests"), "tests"):
        assert br.outside_target(["python", "-m", "pytest", target], str(tree)) is None, target
    assert br.outside_target(["pytest", str(stray / "tests")], str(tree)) is not None
    assert br.outside_target(["pytest", str(tmp_path / "elsewhere" / "test_a.py")], str(tree)) is not None


def test_what_review_a_s_delta_read_found_in_the_target_rule(program, tmp_path):
    """Each form reproduced by a reviewer: a word `pytest` anywhere made a unittest run be read as pytest, so its `-s` went
    unread; a path after a bare `--` that starts with `-` was read as an option; `-c` behind flags in one word loaded an
    outside configuration; pytest expands `@file` in an option's value too."""
    br = program("bridge-run")
    base = tmp_path / "ws"
    (base / "tests").mkdir(parents=True)
    out = str(tmp_path / "elsewhere")
    for argv in (["python", "-m", "unittest", "discover", "-s", out, "-k", "pytest"],
                 ["pytest", "--", "-x/../../elsewhere/test_probe.py"], ["python", "-m", "unittest", "discover", "--", "-x/../../elsewhere"],
                 ["python", "-m", "pytest", "-vc" + os.path.join(out, "pytest.ini"), "tests"], ["pytest", "-qc", "pytest.ini", "tests"],
                 ["pytest", "-xp", "probeplugin", "tests"], ["uv", "run", "pytest", "-vc" + os.path.join(out, "pytest.ini")],
                 ["python", "-m", "pytest", "-Vc" + os.path.join(out, "pytest.ini"), "tests"], ["pytest", "-hc" + os.path.join(out, "pytest.ini")],
                 ["pytest", "-Vo", "testpaths=" + out],
                 ["python", "-m", "pytest", "-k", "@" + os.path.join(out, "args.txt"), "tests"], ["pytest", "--junitxml", "@args.txt"],
                 ["pytest", "-o", "@args.txt", "tests"], ["uv", "run", "--project", "pytest", "pytest", out]):
        assert br.outside_target(argv, str(base)) is not None, argv
    for argv in (["python", "-m", "pytest", "-p", "no:cacheprovider", "-rp", "-sv", "-xq", "tests"], ["pytest", "-rA", "-vv", "--", "tests/test_a.py"],
                 ["python", "-m", "unittest", "tests.test_a", "-k", "pytest"], ["python", "-m", "unittest", "discover", "-s", "tests", "--", "tests"],
                 ["python", "-m", "pytest", "tests", "-k", "a@b"]):
        assert br.outside_target(argv, str(base)) is None, argv


# ---------------------------------------------------------------- M1: the round's cause


@pytest.mark.parametrize("line,cause", [
    ("Round cause: defect - the save loses the last row", "defect"),
    ("Round cause: fix-induced - round 2's fix broke the import", "fix-induced"),
    ("Round cause: no external path", "no external path"),
    ("Round cause: Builder incomplete: the tests were not written", "builder incomplete"),
    ("Round cause:   security (the path is not checked)", "security"),
    ("Round cause: records", "records"),
    ("Round cause: brief error - the brief named the wrong file", "brief error"),
])
def test_m1_a_later_round_s_cause_is_read_into_the_run_log(tmp_path, line, cause):
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001-r2", extra="\n%s\n" % line)
    res = launch(lab, build("TASK-001-r2"))
    row = assert_ran(res)
    assert row["cause"] == cause and row["round"] == 2, row
    assert "Round cause" not in res.err, "a stated cause prints no note"


@pytest.mark.parametrize("extra,said", [("", "has no `Round cause:` line"), ("\nRound cause: polish - nicer names\n", "names none of"),
                                        ("\nRound cause: defective - close to a cause, not one\n", "names none of")])
def test_m1_a_missing_or_unknown_cause_is_logged_unstated_with_a_note_and_never_refused(tmp_path, extra, said):
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001-r2", extra=extra)
    res = launch(lab, build("TASK-001-r2"))
    row = assert_ran(res)
    assert row["cause"] == "unstated", row
    notes = [l for l in res.err.splitlines() if l.startswith("bridge-run: note - ") and said in l]
    assert len(notes) == 1 and "logged as unstated" in notes[0], res.err
    assert res.err.splitlines()[0].startswith("bridge-run: started "), "the launch line stays the first"


def test_m1_a_first_round_carries_no_cause(tmp_path):
    lab = Lab(tmp_path)
    write_brief(lab.root, "TASK-001", extra="\nRound cause: defect - written by mistake in a first brief\n")
    row = assert_ran(launch(lab, build("TASK-001")))
    assert "cause" not in row, row


def test_m1_the_launcher_and_the_pace_report_hold_one_list_of_causes(program):
    """pace-report.py counts what the launcher writes: its list is the launcher's and `unstated`."""
    assert program("pace-report").ROUND_CAUSES == program("bridge-run").ROUND_CAUSES + ("unstated",)


# ---------------------------------------------------------------- M1 and M2 in the pace report


def builder_row(ident, rnd, when, model="composer-2.5", cause=None, **more):
    row = {"id": P.run_id(when), "kind": "builder", "model": model, "branch": ident.lower(), "exit": 0, "brief": ident, "round": rnd,
           "brief_name": ident if rnd == 1 else "%s-r%d" % (ident, rnd), "merge_ids": [ident]}
    if cause:
        row["cause"] = cause
    row.update(more)
    return row


def pace_lines(tmp_path, rows):
    p = P.MiniProject(tmp_path)
    p.brief("TASK-501")
    p.commit("records: brief", P.at(6))
    write_rows(p.ws, rows)
    rc, out, err = P.pace([p.root], tmp_path)
    assert rc == 0, err
    return out.splitlines()


def test_m1_m2_the_pace_report_counts_causes_and_rounds_per_model(tmp_path):
    """Six builder rounds in the window over three increments: four after the first, of three causes and one row from before the
    release that carries none. A relaunch of one round counts once (its last row), a run that ended waiting for the slot and a run
    launched before the window not at all; a review run is no builder round."""
    rows = [builder_row("TASK-501", 1, P.at(3)),
            builder_row("TASK-501", 2, P.at(3, hour=13), cause="defect"),
            builder_row("TASK-501", 3, P.at(3, hour=14), cause="unstated"),
            builder_row("TASK-501", 3, P.at(3, hour=15), cause="fix-induced"),                       # the relaunch of round 3: counted once, this row
            builder_row("TASK-502", 1, P.at(2), model="grok-4.7-high"),
            builder_row("TASK-502", 2, P.at(2, hour=13), model="grok-4.7-high", cause="fix-induced"),
            builder_row("TASK-503", 2, P.at(1)),                                                    # written before release S: no cause
            builder_row("TASK-504", 2, P.at(1), cause="defect", slot="not free"),
            builder_row("TASK-505", 2, P.at(30), cause="security"),
            dict(builder_row("TASK-506", 2, P.at(1), cause="records"), kind="review")]
    lines = pace_lines(tmp_path, rows)
    causes = [l for l in lines if l.startswith("Round causes")]
    models = [l for l in lines if l.startswith("Builder rounds per model")]
    assert causes == ["Round causes (4 builder rounds after the first): defect 1 (25%); fix-induced 2 (50%); unstated 1 (25%)"], lines
    assert models == ["Builder rounds per model: composer-2.5 4 round(s) over 2 increment(s), mean 2; grok-4.7-high 2 round(s) over 1 increment(s), mean 2"], lines


def test_m1_m2_neither_line_where_the_window_holds_no_builder_round(tmp_path):
    lines = pace_lines(tmp_path, [dict(builder_row("TASK-501", 1, P.at(2)), kind="test")])
    assert not [l for l in lines if l.startswith(("Round causes", "Builder rounds per model"))], lines
    lines = pace_lines(tmp_path / "second", [builder_row("TASK-501", 1, P.at(2))])
    assert not [l for l in lines if l.startswith("Round causes")] and len([l for l in lines if l.startswith("Builder rounds per model")]) == 1, lines
