"""Shared fixtures: load a bridge program as a module by its file name."""
import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CURSOR_BRIDGE = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")


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
