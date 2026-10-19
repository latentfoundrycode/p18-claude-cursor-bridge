"""FIX-001 - every program the suite starts is windowless (rule 24, KP-014).

enforces: supervisor.md standing rule 24 (windowless by default) and Known-Pitfalls KP-014 for the test suite itself;
the default lives in tests/conftest.py (windowless_kwargs and the Popen wrapper it installs on Windows).
Supervisor-authored. A child started without flags gets a console of its own with no window (GetConsoleWindow() is 0
and the test's own process is not on the child's console, where an inherited console would hold it; verified
2026-10-19 on the owner's computer: inherited, the console held the test's process; with CREATE_NO_WINDOW, not); its own
child shares that windowless console. The checks name processes, never count them: a virtual environment's python.exe
is a launcher that adds a process of its own to the console (Review A, FIX-001).
"""
import os
import re
import subprocess
import sys

import pytest

import conftest

PRINT_WINDOW = ("import ctypes, os; k = ctypes.windll.kernel32; a = (ctypes.c_uint * 64)(); "
                "n = k.GetConsoleProcessList(a, 64); print(k.GetConsoleWindow(), os.getpid(), *a[:n])")
GRANDCHILD = ("import os, subprocess, sys; "
              "print(os.getpid(), subprocess.run([sys.executable, '-c', %r], capture_output=True, text=True).stdout.strip())"
              % PRINT_WINDOW)
STREAMS = "import sys; print('to-out'); print('to-err', file=sys.stderr); print('read', repr(sys.stdin.read()))"
HERE = os.path.dirname(os.path.abspath(__file__))
# Launch paths that bypass subprocess.Popen and so the default (this file and conftest.py are not scanned).
BYPASS = re.compile(r"\bos\.(system|startfile|spawn\w*|exec\w*)\s*\(|\bfrom\s+os\s+import\b.*\b(system|startfile|spawn\w*|exec\w*)\b"
                    r"|\bmultiprocessing\b|\bProcessPoolExecutor\b|\bCreateProcess")
# Creation flags set by keyword or by a dictionary key.
FLAGS = re.compile(r"""\bcreationflags\s*=|["']creationflags["']\s*:""")
BYPASSING = ['os.system("x")', "os.startfile(p)", "os.spawnv(os.P_WAIT, exe, args)", "os.execv(exe, args)",
             "from os import system", "import multiprocessing", "with concurrent.futures.ProcessPoolExecutor() as pool:",
             "_winapi.CreateProcess(None, cmd, None, None, 0, 0, None, None, None)",
             "subprocess.run(cmd, creationflags=0x200)", "subprocess.run(cmd, creationflags = 0x200)",
             'subprocess.run(cmd, **{"creationflags": 0x200})', "subprocess.run(cmd, creationflags=0)  # not CREATE_NO_WINDOW"]
THROUGH_THE_DEFAULT = ['subprocess.run(cmd, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))',
                       "subprocess.run(cmd, check=True)", "# os.system is never used here"]


def bypasses_the_default(line):
    """True when one line of a test launches around the default: a path other than subprocess, or creation flags
    without CREATE_NO_WINDOW. A comment does not count, either way."""
    code = line.split("#", 1)[0]
    return bool(BYPASS.search(code)) or (bool(FLAGS.search(code)) and "CREATE_NO_WINDOW" not in code)


def window_and_console(line):
    """(GetConsoleWindow(), the printing process's id, the ids on its console) from one PRINT_WINDOW line."""
    window, me, *on_console = (int(n) for n in line.split())
    return window, me, on_console


def test_fix001_a_launch_without_flags_gets_no_window_flags():
    assert conftest.windowless_kwargs({}) == {"creationflags": conftest.NO_WINDOW, "stdin": subprocess.DEVNULL}
    assert conftest.windowless_kwargs({"creationflags": 0, "cwd": "x"}) == {
        "creationflags": conftest.NO_WINDOW, "cwd": "x", "stdin": subprocess.DEVNULL}


def test_fix001_a_launch_that_redirects_a_stream_keeps_its_streams():
    assert conftest.windowless_kwargs({"stdout": subprocess.PIPE}) == {"creationflags": conftest.NO_WINDOW,
                                                                      "stdout": subprocess.PIPE}
    assert conftest.windowless_kwargs({"stdin": None, "stderr": subprocess.PIPE}) == {
        "creationflags": conftest.NO_WINDOW, "stdin": None, "stderr": subprocess.PIPE}


def test_fix001_a_launch_with_its_own_flags_keeps_them():
    assert conftest.windowless_kwargs({"creationflags": 0x200}) == {"creationflags": 0x200}


def test_fix001_the_wrapper_is_installed_on_windows_only():
    installed = getattr(subprocess.Popen.__init__, "windowless_default", False)
    assert installed is (sys.platform == "win32")


@pytest.mark.skipif(sys.platform != "win32", reason="console windows exist only on Windows")
def test_fix001_a_child_started_without_flags_has_no_console_window():
    """No window, and a console of its own (the flag was applied, not merely a windowless console inherited)."""
    p = subprocess.run([sys.executable, "-c", PRINT_WINDOW], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    window, child, on_console = window_and_console(p.stdout)
    assert window == 0
    assert child in on_console
    assert os.getpid() not in on_console


@pytest.mark.skipif(sys.platform != "win32", reason="console windows exist only on Windows")
def test_fix001_a_grandchild_inherits_the_windowless_console():
    """The child's own child, started without flags by a program the suite does not patch, shares the child's
    windowless console: no window, the child on it, the test's process not."""
    p = subprocess.run([sys.executable, "-c", GRANDCHILD], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    child, grandchild_line = p.stdout.strip().split(" ", 1)
    window, grandchild, on_console = window_and_console(grandchild_line)
    assert window == 0
    assert {int(child), grandchild} <= set(on_console)
    assert os.getpid() not in on_console


@pytest.mark.skipif(sys.platform != "win32", reason="the default is installed on Windows only")
def test_fix001_a_child_that_redirects_nothing_writes_to_the_suite_and_reads_end_of_input(capfd):
    """Its output reaches the suite's own streams (a failure report shows it) and its input is at its end at once."""
    p = subprocess.run([sys.executable, "-c", STREAMS], timeout=30)
    out, err = capfd.readouterr()
    assert p.returncode == 0
    assert "to-out" in out and "read ''" in out
    assert "to-err" in err


def test_fix001_the_rule_flags_each_way_around_the_default():
    """The scan below can fail: each known way around the default is flagged, and a launch through it is not."""
    assert [line for line in BYPASSING if not bypasses_the_default(line)] == []
    assert [line for line in THROUGH_THE_DEFAULT if bypasses_the_default(line)] == []


def scan(folder):
    """(the lines around the default as "file:line: text", the files read, the count of flags lines) over every .py
    file under folder, this file and conftest.py apart."""
    found, read, flag_lines = [], set(), 0
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            relative = os.path.relpath(os.path.join(root, name), folder).replace(os.sep, "/")
            if not name.endswith(".py") or relative in ("conftest.py", "test_tests_windowless.py"):
                continue
            read.add(relative)
            with open(os.path.join(root, name), encoding="utf-8") as f:
                for number, line in enumerate(f, 1):
                    flag_lines += bool(FLAGS.search(line))
                    if bypasses_the_default(line):
                        found.append("%s:%d: %s" % (relative, number, line.strip()))
    return found, read, flag_lines


def test_fix001_the_scan_reports_a_launch_around_the_default(tmp_path):
    """A file holding a way around the default, in a subfolder, is reported at its line; the rest is not."""
    (tmp_path / "helpers").mkdir()
    (tmp_path / "helpers" / "planted.py").write_text('import os\nos.system("x")\n', encoding="utf-8")
    (tmp_path / "test_through.py").write_text(
        'subprocess.run(cmd, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))\n', encoding="utf-8")
    (tmp_path / "conftest.py").write_text('os.system("x")\n', encoding="utf-8")
    assert scan(str(tmp_path)) == (['helpers/planted.py:2: os.system("x")'], {"helpers/planted.py", "test_through.py"}, 1)


def test_fix001_no_test_starts_a_program_around_the_default():
    """Every launch in tests/ goes through subprocess, and one that sets its own flags includes CREATE_NO_WINDOW:
    the INVENTORY decision not to run windowless-check.py over tests/ holds only while this is so."""
    found, read, flag_lines = scan(HERE)
    assert {"test_bridge_run.py", "test_workflows_line_check.py", "helpers/sleep_tree.py"} <= read
    assert flag_lines > 0
    assert found == []
