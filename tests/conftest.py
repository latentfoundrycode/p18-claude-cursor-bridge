"""Shared fixtures: load a bridge program as a module by its file name; every program a test starts is windowless."""
import importlib.util
import os
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CURSOR_BRIDGE = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")

import subprocess
import sys

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def windowless_kwargs(kwargs):
    """The keyword arguments of a launch, with CREATE_NO_WINDOW as its creation flags when it sets none.

    FIX-001 (rule 24, KP-014): the suite starts thousands of console programs. Run from a process with no console
    (a headless builder, a hook), Windows gives each one a visible console window; on 2026-10-19 a builder's suite run
    coincided with a crash that followed a flood of terminal windows. A launch that sets creation flags of its own
    keeps them; a grandchild inherits its parent's windowless console, so one level is enough. A launch that redirects
    none of its standard streams gets stdin=DEVNULL as well: Python then hands the child the suite's own output
    handles, where with the new console alone its output would go to that hidden console (lost from a failure report)
    and a read of its input would wait there for ever (bridge-run.py does the same)."""
    if not kwargs.get("creationflags"):
        kwargs = dict(kwargs, creationflags=NO_WINDOW)
        if all(kwargs.get(name) is None for name in ("stdin", "stdout", "stderr")):
            kwargs["stdin"] = subprocess.DEVNULL
    return kwargs


if sys.platform == "win32" and not getattr(subprocess.Popen.__init__, "windowless_default", False):
    _popen_init = subprocess.Popen.__init__

    def _windowless_init(self, *args, **kwargs):
        _popen_init(self, *args, **windowless_kwargs(kwargs))

    _windowless_init.windowless_default = True
    subprocess.Popen.__init__ = _windowless_init

# Set before any test module is imported, so the environments some modules copy at import carry it too:
# review-guard.py's snapshot-hash copies (2026.10.25a) never reach the owner's ~/.cursor-bridge.
os.environ["BRIDGE_REVIEW_HASHES"] = tempfile.mkdtemp(prefix="bridge-review-hashes-")


def load_program(name):
    """Import ~/.claude/cursor-bridge/<name>.py (a dash in the name is fine) as a module."""
    path = os.path.join(CURSOR_BRIDGE, name + ".py")
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def program():
    return load_program


@pytest.fixture(autouse=True)
def home_of_the_tests(tmp_path_factory, monkeypatch):
    """No test touches the owner's home: ~ is a temporary folder with an empty .cursor, so the
    agent's home folder (KP-038) links to that and never to the owner's real ~/.cursor."""
    home = tmp_path_factory.mktemp("home")
    (home / ".cursor").mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home
