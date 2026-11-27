"""TASK-090, the supervisor's acceptance tests: the launcher's small repairs (R-112).

enforces: docs/REQUIREMENTS.md R-112; docs/DESIGN.md, Change: the improvements release, C36, C37, C54's first part,
T74; docs/BUILD_PLAN.md, TASK-090's Done when.

- A run that is not a watch and ends at its limit leaves no pid file: the file is removed before the process tree is
  ended (on Windows the job ends the launcher too, so a removal after it never runs). Behavioural on every system,
  red on the checkpoint on Windows; the order is held on every system by the program's own steps (the source).
- A driver's and a test's child see `PYTHONIOENCODING=utf-8` where the caller set none, and the caller's value where
  it set one; a builder's and a reviewer's environment are unchanged; no kind sets `PYTHONUTF8`.
- A `--kind test` launch of `python <program>` under `<launch folder>/run/supervisor/`, or of the installed mutation
  engine, is refused with exit 125 by a line that names `--kind driver`; another program's refusal names no kind.
- The usage text and the docstring say a stripped run sees none of the owner's files under APPDATA, LOCALAPPDATA or
  the home folder, and that a driver that needs the owner's key file is launched unstripped under a recorded decision.
- No environment name moves the run record or the pid folder.

The builder reads and runs these tests and edits nothing in this file.
"""
import ast
import json
import os
import subprocess
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
DROPPED = ("BRIDGE_RUN_ALLOW_ANY", "BRIDGE_RUN_SLOT_SCALE", "PYTHONIOENCODING", "PYTHONUTF8")


@pytest.fixture
def lab(tmp_path):
    """A launch folder with run/ (so the launcher writes its record and pid files there) and a home of its own (so
    the heavy slot and the installed mutation engine are the test's, never the real ones)."""
    ws = tmp_path / "ws"
    (ws / "run" / "supervisor").mkdir(parents=True)
    (ws / "tests").mkdir()
    (ws / "tools").mkdir()
    home = tmp_path / "home"
    (home / ".claude" / "cursor-bridge").mkdir(parents=True)
    return ws, home


def env_of(lab, allow_any=False, **extra):
    ws, home = lab
    env = {k: v for k, v in os.environ.items() if k.upper() not in DROPPED}
    env["LOCALAPPDATA"] = str(ws.parent / "localappdata")
    env["HOME"] = env["USERPROFILE"] = str(home)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    if allow_any:
        env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    env.update(extra)
    return env


def launch(lab, words, kind=None, limit="120", strip=False, allow_any=False, extra=None, timeout=300):
    ws, _ = lab
    argv = [sys.executable, PROG, "--limit", limit] + (["--strip"] if strip else [])
    argv += (["--kind", kind] if kind else []) + ["--"] + list(words)
    return subprocess.run(argv, capture_output=True, text=True, cwd=str(ws), env=env_of(lab, allow_any, **(extra or {})),
                          timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def pid_files(ws):
    d = ws / "run" / "launcher" / "pids"
    return sorted(os.listdir(str(d))) if d.is_dir() else []


def rows(ws):
    log = ws / "run" / "launcher" / "runs.jsonl"
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------- C36: the pid file at a limit


SLEEP = "import time\ntime.sleep(120)\n"


def sleeper(lab, kind):
    ws, _ = lab
    if kind == "test":
        (ws / "tests" / "test_sleep.py").write_text("import time\n\n\ndef test_sleep():\n    time.sleep(120)\n",
                                                    encoding="utf-8")
        return ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_sleep.py"], False
    if kind == "driver":
        (ws / "run" / "supervisor" / "sleep.py").write_text(SLEEP, encoding="utf-8")
        return ["python", "run/supervisor/sleep.py"], False
    return [sys.executable, "-c", "import time; time.sleep(120)"], True


@pytest.mark.parametrize("kind", ["test", "driver", "builder"])
def test_r112_a_run_ended_at_its_limit_leaves_no_pid_file(lab, kind):
    """C36. A run that is not a watch and ends at its limit leaves `run/launcher/pids/` empty; its record row is
    written with exit 124 as before. Red on the checkpoint on Windows, where the job ends the launcher before the
    removal that follows `killer()`."""
    ws, _ = lab
    words, allow_any = sleeper(lab, kind)
    t0 = time.time()
    p = launch(lab, words, kind=kind, limit="8", allow_any=allow_any)
    assert p.returncode == 124, (p.returncode, p.stderr)
    assert "LIMIT 8s reached" in p.stderr and "bridge-run: exit 124" in p.stderr, p.stderr
    assert time.time() - t0 < 90, "the limit did not end the run"
    deadline = time.time() + 10
    while pid_files(ws) and time.time() < deadline:
        time.sleep(0.5)
    assert pid_files(ws) == [], "a pid file was left at the limit: %r\n%s" % (pid_files(ws), p.stderr)
    mine = [r for r in rows(ws) if r.get("kind") == kind]
    assert mine and mine[-1].get("exit") == 124, rows(ws)


def test_r112_a_run_that_ends_normally_leaves_no_pid_file_either(lab):
    """The control: a driver that ends by itself removes its pid file, as on the checkpoint."""
    ws, _ = lab
    (ws / "run" / "supervisor" / "quick.py").write_text("print('quick')\n", encoding="utf-8")
    p = launch(lab, ["python", "run/supervisor/quick.py"], kind="driver")
    assert p.returncode == 0 and "quick" in p.stdout, p.stderr
    assert pid_files(ws) == [], pid_files(ws)


def _calls(node, name):
    """The calls inside `node` to a function named `name`, or to a subscript like box["name"]."""
    found = []
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        f = sub.func
        if isinstance(f, ast.Name) and f.id == name:
            found.append(sub)
        elif isinstance(f, ast.Subscript) and isinstance(f.slice, ast.Constant) and f.slice.value == name:
            found.append(sub)
    return found


def _limit_handlers(tree):
    """Every `except subprocess.TimeoutExpired:` handler whose body ends the tree with `killer()`."""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler) or node.type is None:
            continue
        t = node.type
        if not (isinstance(t, ast.Attribute) and t.attr == "TimeoutExpired"):
            continue
        if any(_calls(stmt, "killer") for stmt in node.body):
            out.append(node)
    return out


def test_r112_every_limit_branch_removes_the_pid_file_before_it_ends_the_tree():
    """C36, on every system: in each limit branch that ends the process tree by `killer()` (the watch's and the one
    every other kind takes), a `remove_pid_file(...)` statement comes before the statement that calls `killer()`.
    Red on the checkpoint: the branch that is not a watch removes the file only after it."""
    src = open(PROG, encoding="utf-8").read()
    handlers = _limit_handlers(ast.parse(src))
    assert len(handlers) >= 2, "expected the watch's limit branch and the other kinds' limit branch"
    for h in handlers:
        killer_at = min(i for i, stmt in enumerate(h.body) if _calls(stmt, "killer"))
        removed_at = [i for i, stmt in enumerate(h.body) if _calls(stmt, "remove_pid_file")]
        assert removed_at and min(removed_at) < killer_at, (
            "the limit branch at line %d ends the tree before it removes the pid file" % h.lineno)


# ---------------------------------------------------------------- C37: the child's encoding


PROBE = ("import os\nprint('ENC=%r UTF8=%r' % (os.environ.get('PYTHONIOENCODING'), 'PYTHONUTF8' in os.environ))\n")


def probe_driver(lab, strip, caller):
    ws, _ = lab
    (ws / "run" / "supervisor" / "probe.py").write_text(PROBE, encoding="utf-8")
    extra = {"PYTHONIOENCODING": caller} if caller is not None else {}
    p = launch(lab, ["python", "run/supervisor/probe.py"], kind="driver", strip=strip, extra=extra)
    assert p.returncode == 0, (p.stdout, p.stderr)
    return p.stdout


@pytest.mark.parametrize("strip", [False, True])
def test_r112_a_driver_s_child_gets_utf_8_where_the_caller_set_none(lab, strip):
    """C37. Red on the checkpoint: the child sees no PYTHONIOENCODING."""
    out = probe_driver(lab, strip, None)
    assert "ENC='utf-8' UTF8=False" in out, out


@pytest.mark.parametrize("strip", [False, True])
def test_r112_a_driver_s_child_keeps_the_caller_s_value(lab, strip):
    out = probe_driver(lab, strip, "cp1252")
    assert "ENC='cp1252' UTF8=False" in out, out


def probe_suite(lab, strip, caller, expected):
    ws, _ = lab
    (ws / "tests" / "test_enc.py").write_text(
        "import os\n\n\ndef test_enc():\n    assert os.environ.get('PYTHONIOENCODING') == %r, os.environ.get('PYTHONIOENCODING')\n"
        "    assert 'PYTHONUTF8' not in os.environ\n" % expected, encoding="utf-8")
    extra = {"PYTHONIOENCODING": caller} if caller is not None else {}
    return launch(lab, ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_enc.py"], kind="test",
                  strip=strip, extra=extra)


@pytest.mark.parametrize("strip", [False, True])
def test_r112_a_test_s_child_gets_utf_8_where_the_caller_set_none(lab, strip):
    """C37. Red on the checkpoint."""
    p = probe_suite(lab, strip, None, "utf-8")
    assert p.returncode == 0 and "1 passed" in p.stdout, (p.stdout, p.stderr)


@pytest.mark.parametrize("strip", [False, True])
def test_r112_a_test_s_child_keeps_the_caller_s_value(lab, strip):
    p = probe_suite(lab, strip, "latin-1", "latin-1")
    assert p.returncode == 0 and "1 passed" in p.stdout, (p.stdout, p.stderr)


@pytest.mark.parametrize("kind", ["builder", "review"])
@pytest.mark.parametrize("caller", [None, "cp1252"])
def test_r112_a_builder_s_and_a_reviewer_s_environment_unchanged(lab, kind, caller):
    """C37. The builder and the reviewer see the caller's PYTHONIOENCODING as it was, none where it set none, and no
    PYTHONUTF8 (run as the tests run their own helpers, by BRIDGE_RUN_ALLOW_ANY)."""
    extra = {"PYTHONIOENCODING": caller} if caller is not None else {}
    p = launch(lab, [sys.executable, "-c", PROBE], kind=kind, allow_any=True, extra=extra)
    assert p.returncode == 0, (p.stdout, p.stderr)
    assert "ENC=%r UTF8=False" % caller in p.stdout, p.stdout


def test_r112_the_launcher_sets_no_pythonutf8():
    """C37. No string of the launcher's code names PYTHONUTF8 (its prose may), so it never writes it."""
    tree = ast.parse(open(PROG, encoding="utf-8").read())
    docs = {id(n.body[0].value) for n in ast.walk(tree)
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
            and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    named = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and "PYTHONUTF8" in n.value and id(n) not in docs]
    assert named == [], named


# ---------------------------------------------------------------- C54: the refusal's hint


def refused_line(p):
    assert "Traceback" not in p.stderr, p.stderr
    assert p.returncode == 125, (p.returncode, p.stderr)
    lines = [line for line in p.stderr.splitlines() if line.startswith("bridge-run: refused")]
    assert lines, p.stderr
    return " ".join(lines)


def test_r112_a_test_launch_of_a_supervisor_program_names_the_driver_kind(lab):
    """C54. Red on the checkpoint: the refusal names no kind."""
    ws, _ = lab
    (ws / "run" / "supervisor" / "x.py").write_text("print('x')\n", encoding="utf-8")
    for words in (["python", "run/supervisor/x.py"], ["python", str(ws / "run" / "supervisor" / "x.py")],
                  ["python", "run/supervisor/x.py", "--flag", "value"]):
        p = launch(lab, words, kind="test")
        line = refused_line(p)
        assert "--kind driver" in line, (words, line)
        assert "x\n" not in p.stdout, (words, p.stdout)


def test_r112_a_test_launch_of_the_installed_mutation_engine_names_the_driver_kind(lab):
    """C54. The installed engine, by its absolute path and by the home form the loop writes."""
    _, home = lab
    engine = home / ".claude" / "cursor-bridge" / "mutation-run.py"
    engine.write_text("print('engine')\n", encoding="utf-8")
    for words in (["python", str(engine), "run/supervisor/m.json"],
                  ["python", "~/.claude/cursor-bridge/mutation-run.py", "run/supervisor/m.json"]):
        p = launch(lab, words, kind="test")
        line = refused_line(p)
        assert "--kind driver" in line, (words, line)
        assert "engine" not in p.stdout, (words, p.stdout)


def test_r112_another_program_s_refusal_names_no_kind(lab):
    """C54. The hint is given only where the driver kind would accept the program."""
    ws, _ = lab
    (ws / "tools" / "y.py").write_text("print('y')\n", encoding="utf-8")
    p = launch(lab, ["python", "tools/y.py"], kind="test")
    line = refused_line(p)
    assert "--kind driver" not in line, line


def test_r112_the_driver_kind_still_runs_the_supervisor_program(lab):
    """The control: the same program under `--kind driver` runs."""
    ws, _ = lab
    (ws / "run" / "supervisor" / "x.py").write_text("print('ran x')\n", encoding="utf-8")
    p = launch(lab, ["python", "run/supervisor/x.py"], kind="driver")
    assert p.returncode == 0 and "ran x" in p.stdout, (p.stdout, p.stderr)


# ---------------------------------------------------------------- T74: the help text


TOLD = ("appdata", "localappdata", "home folder", "unstripped", "key file", "recorded decision", "driver")


def told(text):
    low = " ".join(text.lower().split())
    return [w for w in TOLD if w not in low]


def test_r112_the_usage_text_names_the_owner_s_folders_a_stripped_run_does_not_see(lab):
    """T74. Red on the checkpoint: the usage text names none of them."""
    ws, _ = lab
    p = subprocess.run([sys.executable, PROG], capture_output=True, text=True, cwd=str(ws), env=env_of(lab), timeout=120)
    assert p.returncode == 2, (p.returncode, p.stderr)
    assert "usage: bridge-run.py" in p.stderr, p.stderr
    assert "--strip" in p.stderr, p.stderr
    assert told(p.stderr) == [], (told(p.stderr), p.stderr)


def test_r112_the_docstring_names_them_too(program):
    """T74. The module's docstring, which the command reference is generated from."""
    doc = program("bridge-run").__doc__ or ""
    assert told(doc) == [], told(doc)


# ---------------------------------------------------------------- C36: no environment name moves the record


MOVERS = ("BRIDGE_RUN_LOG", "BRIDGE_RUN_RECORD", "BRIDGE_RUN_FOLDER", "BRIDGE_RUN_HOME", "BRIDGE_RUN_PIDS",
          "BRIDGE_RUN_LOG_DIR", "BRIDGE_RUN_RUNS", "BRIDGE_RUN_DIR", "CURSOR_BRIDGE_RUN_LOG", "BRIDGE_LOG")


def test_r112_no_environment_name_moves_the_record(lab, tmp_path):
    """C36. With every plausible name pointing elsewhere, the row and the pid file are the launch folder's, and the
    other folder stays empty."""
    ws, _ = lab
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "run" / "launcher").mkdir(parents=True)
    (ws / "run" / "supervisor" / "quick.py").write_text("print('quick')\n", encoding="utf-8")
    extra = {name: str(elsewhere) for name in MOVERS}
    p = launch(lab, ["python", "run/supervisor/quick.py"], kind="driver", extra=extra)
    assert p.returncode == 0, p.stderr
    assert [r for r in rows(ws) if r.get("kind") == "driver"], rows(ws)
    left = [os.path.join(d, f) for d, _, fs in os.walk(str(elsewhere)) for f in fs]
    assert left == [], left


def test_r112_the_launcher_reads_no_environment_name_but_its_two_test_names():
    """C36. The launcher reads, of its own names, only BRIDGE_RUN_ALLOW_ANY and BRIDGE_RUN_SLOT_SCALE; the record's
    and the pid folder's writers read no environment at all."""
    import re
    src = open(PROG, encoding="utf-8").read()
    names = set(re.findall(r"BRIDGE_\w+", src))
    assert names <= {"BRIDGE_RUN_ALLOW_ANY", "BRIDGE_RUN_SLOT_SCALE"}, names
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in ("write_log", "write_pid_file", "remove_pid_file",
                                                                "create_pid_file_exclusive"):
            body = ast.get_source_segment(src, node) or ""
            assert "environ" not in body and "getenv" not in body, node.name


def test_r112_merge_ids_is_written_sorted():
    """C37's second half: `merge_ids` is written sorted (the program release's J9); held here by the source, beside
    its existing test, which is not edited."""
    src = open(PROG, encoding="utf-8").read()
    assert any('"merge_ids"' in line and "sorted(" in line for line in src.splitlines()), "merge_ids is not written sorted"
