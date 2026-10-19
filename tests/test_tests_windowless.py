"""FIX-001 - every program the suite starts is windowless (rule 24, KP-014).

enforces: supervisor.md standing rule 24 (windowless by default) and Known-Pitfalls KP-014 for the test suite itself;
the default lives in tests/conftest.py (windowless_kwargs and the Popen wrapper it installs on Windows).
Supervisor-authored. A child started without flags gets a console of its own with no window (GetConsoleWindow() is 0
and the console holds the child alone, where an inherited console would also hold the test's own process; verified
2026-10-19 on the owner's computer: inherited 0 4, CREATE_NO_WINDOW 0 1); its own child shares that windowless console.
"""
import subprocess
import sys

import pytest

import conftest

PRINT_WINDOW = ("import ctypes; k = ctypes.windll.kernel32; a = (ctypes.c_uint * 16)(); "
                "print(k.GetConsoleWindow(), k.GetConsoleProcessList(a, 16))")
GRANDCHILD = ("import subprocess, sys; "
              "print(subprocess.run([sys.executable, '-c', %r], capture_output=True, text=True).stdout.strip())"
              % PRINT_WINDOW)


def test_fix001_a_launch_without_flags_gets_no_window_flags():
    assert conftest.windowless_kwargs({}) == {"creationflags": conftest.NO_WINDOW}
    assert conftest.windowless_kwargs({"creationflags": 0, "cwd": "x"}) == {"creationflags": conftest.NO_WINDOW,
                                                                            "cwd": "x"}


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
    assert p.stdout.strip() == "0 1"


@pytest.mark.skipif(sys.platform != "win32", reason="console windows exist only on Windows")
def test_fix001_a_grandchild_inherits_the_windowless_console():
    """The child's own child, started without flags by a program the suite does not patch, shares the child's
    windowless console: no window, two processes on it."""
    p = subprocess.run([sys.executable, "-c", GRANDCHILD], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    assert p.stdout.strip() == "0 2"
