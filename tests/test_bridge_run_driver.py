"""R-039: bridge-run.py --kind driver accepts only supervisor and mutation-run programs windowlessly."""
import json
import os
import subprocess
import sys

import pytest

from test_tests_windowless import GRANDCHILD, PRINT_WINDOW, window_and_console

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")


def launch_folder(tmp_path):
    root = tmp_path / "launch"
    (root / "run" / "supervisor").mkdir(parents=True)
    (root / "run" / "launcher").mkdir(parents=True)
    return root


def env_for(tmp_path, **extra):
    env = dict(os.environ)
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    env.update(extra)
    return env


def run_driver(folder, program, interpreter=None, limit="120", allow_any=False, kind="driver", home=None, **extra):
    interpreter = interpreter or "python"
    base = folder.parent if hasattr(folder, "parent") else folder
    env = env_for(base, **extra)
    if home is not None:
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
    if allow_any:
        env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    cmd = [sys.executable, PROG, "--limit", limit, "--kind", kind, "--", interpreter, str(program)]
    return subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(folder), timeout=120)


def runs_of(folder):
    log = folder / "run" / "launcher" / "runs.jsonl"
    return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()] if log.is_file() else []


def refuse_line(stderr):
    lines = [l for l in stderr.splitlines() if l.startswith("bridge-run: refused - driver kind:")]
    assert len(lines) == 1, stderr
    assert "run/supervisor/" in lines[0] and "mutation-run.py" in lines[0]
    return lines[0]


def _link_folder(link, target):
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(str(target), str(link), target_is_directory=True)


def _write_exit_script(path, code):
    path.write_text("import sys\nsys.exit(%d)\n" % code, encoding="utf-8")


@pytest.fixture
def br(program):
    return program("bridge-run")


def test_r039_accept_supervisor_relative(br, tmp_path):
    """R-039: program under run/supervisor/, relative path."""
    folder = launch_folder(tmp_path)
    prog = folder / "run" / "supervisor" / "task.py"
    _write_exit_script(prog, 0)
    p = run_driver(folder, "run/supervisor/task.py")
    assert p.returncode == 0, p.stderr


def test_r039_accept_supervisor_absolute(br, tmp_path):
    """R-039: program under run/supervisor/, absolute path."""
    folder = launch_folder(tmp_path)
    prog = folder / "run" / "supervisor" / "task.py"
    _write_exit_script(prog, 42)
    p = run_driver(folder, str(prog))
    assert p.returncode == 42, p.stderr


def test_r039_accept_supervisor_subfolder(br, tmp_path):
    """R-039: program in a subfolder of run/supervisor/."""
    folder = launch_folder(tmp_path)
    sub = folder / "run" / "supervisor" / "nested"
    sub.mkdir()
    prog = sub / "task.py"
    _write_exit_script(prog, 0)
    p = run_driver(folder, "run/supervisor/nested/task.py")
    assert p.returncode == 0, p.stderr


def test_r039_accept_mutation_run_absolute(br, tmp_path, home_of_the_tests):
    """R-039: ~/.claude/cursor-bridge/mutation-run.py, absolute."""
    folder = launch_folder(tmp_path)
    mut_dir = home_of_the_tests / ".claude" / "cursor-bridge"
    mut_dir.mkdir(parents=True)
    prog = mut_dir / "mutation-run.py"
    _write_exit_script(prog, 0)
    p = run_driver(folder, str(prog))
    assert p.returncode == 0, p.stderr


def test_r039_accept_mutation_run_tilde(br, tmp_path, home_of_the_tests):
    """R-039: mutation-run.py as ~/.claude/cursor-bridge/mutation-run.py."""
    folder = launch_folder(tmp_path)
    mut_dir = home_of_the_tests / ".claude" / "cursor-bridge"
    mut_dir.mkdir(parents=True)
    prog = mut_dir / "mutation-run.py"
    _write_exit_script(prog, 0)
    p = run_driver(folder, "~/.claude/cursor-bridge/mutation-run.py", home=home_of_the_tests)
    assert p.returncode == 0, p.stderr


@pytest.mark.parametrize("interpreter", ["python", "python3", "py"])
def test_r039_interpreter_bare_name_accepted(br, interpreter):
    """R-039: bare interpreter names pass driver_accepted."""
    assert br.driver_accepted([interpreter, "run/supervisor/x.py"], os.getcwd())


def test_r039_interpreter_venv_accepted(br, tmp_path):
    """R-039: the project's .venv python passes driver_accepted."""
    folder = launch_folder(tmp_path)
    if sys.platform == "win32":
        vpy = folder / ".venv" / "Scripts" / "python.exe"
    else:
        vpy = folder / ".venv" / "bin" / "python"
    vpy.parent.mkdir(parents=True)
    vpy.write_text("", encoding="utf-8")
    assert br.driver_accepted([str(vpy), "run/supervisor/x.py"], str(folder))


@pytest.mark.parametrize("allow_any", [False, True])
def test_r039_refuse_program_outside_supervisor(br, tmp_path, allow_any):
    """R-039: program outside run/supervisor/ is refused."""
    folder = launch_folder(tmp_path)
    prog = folder / "other.py"
    _write_exit_script(prog, 0)
    p = run_driver(folder, "other.py", allow_any=allow_any)
    assert p.returncode == 125
    refuse_line(p.stderr)
    assert runs_of(folder) == []


@pytest.mark.parametrize("allow_any", [False, True])
def test_r039_refuse_supervisor_parent_escape(br, tmp_path, allow_any):
    """R-039: run/supervisor/../x.py is refused."""
    folder = launch_folder(tmp_path)
    prog = folder / "x.py"
    _write_exit_script(prog, 0)
    p = run_driver(folder, "run/supervisor/../x.py", allow_any=allow_any)
    assert p.returncode == 125
    refuse_line(p.stderr)
    assert runs_of(folder) == []


@pytest.mark.parametrize("allow_any", [False, True])
def test_r039_refuse_link_at_supervisor(br, tmp_path, allow_any):
    """R-039: a junction or symlink at run/supervisor is refused."""
    folder = launch_folder(tmp_path)
    real = folder / "real"
    real.mkdir()
    (real / "task.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    sup = folder / "run" / "supervisor"
    sup.rmdir()
    _link_folder(sup, real)
    p = run_driver(folder, "run/supervisor/task.py", allow_any=allow_any)
    assert p.returncode == 125
    refuse_line(p.stderr)


@pytest.mark.parametrize("allow_any", [False, True])
def test_r039_refuse_link_in_subfolder(br, tmp_path, allow_any):
    """R-039: a link in a subfolder under run/supervisor is refused."""
    folder = launch_folder(tmp_path)
    real = folder / "real"
    real.mkdir()
    (real / "task.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    nested = folder / "run" / "supervisor" / "nested"
    _link_folder(nested, real)
    p = run_driver(folder, "run/supervisor/nested/task.py", allow_any=allow_any)
    assert p.returncode == 125
    refuse_line(p.stderr)


@pytest.mark.parametrize("argv", [
    ["python", "-c", "print(1)"],
    ["python", "-m", "pytest"],
    ["py", "-3", "run/supervisor/x.py"],
])
@pytest.mark.parametrize("allow_any", [False, True])
def test_r039_refuse_interpreter_options(br, tmp_path, argv, allow_any):
    """R-039: interpreter options before the program are refused."""
    folder = launch_folder(tmp_path)
    env = env_for(tmp_path)
    if allow_any:
        env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    cmd = [sys.executable, PROG, "--limit", "30", "--kind", "driver", "--"] + argv
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(folder), timeout=60)
    assert p.returncode == 125
    refuse_line(p.stderr)


@pytest.mark.parametrize("allow_any", [False, True])
def test_r039_refuse_txt_program(br, tmp_path, allow_any):
    """R-039: a non-.py program is refused."""
    folder = launch_folder(tmp_path)
    prog = folder / "run" / "supervisor" / "task.txt"
    prog.write_text("x\n", encoding="utf-8")
    p = run_driver(folder, "run/supervisor/task.txt", allow_any=allow_any)
    assert p.returncode == 125
    refuse_line(p.stderr)


@pytest.mark.parametrize("allow_any", [False, True])
def test_r039_refuse_foreign_python(br, tmp_path, allow_any):
    """R-039: C:/anywhere/python.exe is refused as the interpreter."""
    folder = launch_folder(tmp_path)
    prog = folder / "run" / "supervisor" / "task.py"
    _write_exit_script(prog, 0)
    p = run_driver(folder, "run/supervisor/task.py", interpreter="C:/anywhere/python.exe", allow_any=allow_any)
    assert p.returncode == 125
    refuse_line(p.stderr)


def test_r039_driver_form_under_test_kind_refused(tmp_path):
    """R-039: driver-shaped command without --kind driver uses the usual refusal."""
    folder = launch_folder(tmp_path)
    prog = folder / "run" / "supervisor" / "task.py"
    _write_exit_script(prog, 0)
    env = env_for(tmp_path)
    p = subprocess.run([sys.executable, PROG, "--limit", "30", "--kind", "test", "--", "python", str(prog)],
                       capture_output=True, text=True, env=env, cwd=str(folder), timeout=60)
    assert p.returncode == 125 and "refused" in p.stderr


def test_r039_driver_ceiling_defaults(br, tmp_path):
    """R-039: driver default limit 7200 and cap 14400."""
    folder = launch_folder(tmp_path)
    assert br.learned_limit("driver", str(folder)) == (7200, "the default for driver")
    assert br.cap_for("driver", str(folder))[0] == 14400
    prog = folder / "run" / "supervisor" / "task.py"
    _write_exit_script(prog, 0)
    p = subprocess.run([sys.executable, PROG, "--limit", "14401", "--kind", "driver", "--", "python", str(prog)],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(folder), timeout=60)
    assert p.returncode == 125 and "above twice the default" in p.stderr


@pytest.mark.parametrize("code, healthy", [(0, True), (1, True), (2, False), (3, False), (124, False)])
def test_r039_driver_health_logged(tmp_path, code, healthy):
    """R-039: driver healthy only at exit 0 and 1."""
    folder = launch_folder(tmp_path)
    prog = folder / "run" / "supervisor" / "task.py"
    _write_exit_script(prog, code)
    p = run_driver(folder, str(prog))
    assert p.returncode == code, p.stderr
    row = runs_of(folder)[-1]
    assert row["kind"] == "driver"
    if healthy:
        assert row["healthy"] is True
    else:
        assert row["healthy"] is not True


def test_r039_driver_learning_from_exit_1(br, tmp_path):
    """R-039: a healthy driver run at exit 1 teaches the limit."""
    folder = launch_folder(tmp_path)
    log = folder / "run" / "launcher" / "runs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps({"id": "t", "kind": "driver", "seconds": 6000, "exit": 1, "healthy": True}) + "\n",
                   encoding="utf-8")
    assert br.learned_limit("driver", str(folder))[0] == 9000


def test_r039_driver_learning_ignores_hand_marked_unhealthy_exit(br, tmp_path):
    """R-039: exit 3 marked healthy by hand is not learned from."""
    folder = launch_folder(tmp_path)
    log = folder / "run" / "launcher" / "runs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps({"id": "t", "kind": "driver", "seconds": 6000, "exit": 3, "healthy": True}) + "\n",
                   encoding="utf-8")
    assert br.learned_limit("driver", str(folder))[0] == 7200


def test_r039_healthy_refused_for_driver_exit_3(tmp_path):
    """R-039: --healthy on a driver run at exit 3 refuses."""
    folder = launch_folder(tmp_path)
    log = folder / "run" / "launcher" / "runs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    line = {"id": "2026-01-01T00:00:00Z", "kind": "driver", "seconds": 1, "exit": 3, "healthy": None}
    log.write_text(json.dumps(line) + "\n", encoding="utf-8")
    before = log.read_text(encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, "--healthy", "2026-01-01", "--kind", "driver"],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(folder), timeout=60)
    assert p.returncode == 1 and p.stderr.startswith("bridge-run: refused - ")
    assert log.read_text(encoding="utf-8") == before


def test_r039_log_head_is_interpreter_only(tmp_path):
    """R-039: runs.jsonl head names the interpreter, not the program."""
    folder = launch_folder(tmp_path)
    prog = folder / "run" / "supervisor" / "task.py"
    _write_exit_script(prog, 0)
    run_driver(folder, str(prog))
    row = runs_of(folder)[-1]
    assert row["head"] == "python" and "supervisor" not in row["head"] and "task" not in row["head"]


@pytest.mark.skipif(sys.platform != "win32", reason="console windows exist only on Windows")
def test_r039_driver_grandchild_windowless(tmp_path):
    """R-039: a driver run's grandchild has a windowless console; the launcher is not on it."""
    folder = launch_folder(tmp_path)
    prog = folder / "run" / "supervisor" / "probe.py"
    prog.write_text(GRANDCHILD, encoding="utf-8")
    env = env_for(tmp_path)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    p = subprocess.run([sys.executable, PROG, "--limit", "120", "--kind", "driver", "--", "python", str(prog)],
                       capture_output=True, text=True, env=env, cwd=str(folder), timeout=120)
    assert p.returncode == 0, p.stderr
    driver_pid, gc_line = p.stdout.strip().split(None, 1)
    window, gc_pid, on_console = window_and_console(gc_line)
    assert window == 0
    assert int(driver_pid) in on_console and int(gc_pid) in on_console
    launcher_pid = runs_of(folder)[-1]["pid"]
    assert launcher_pid not in on_console
