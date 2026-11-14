"""FIX-005: a stripped launch withholds a secret-like name end to end (R-052; stage P1's least-confident item 1).

enforces: docs/REQUIREMENTS.md R-052 (the loop's suite and driver launches carry `--strip`, which withholds the owner's
login and every variable named like an account key from the code a builder wrote); docs/diagrams/D-004-context-dfd.md,
the note "Stripped environment": every name `SECRET_LIKE` matches is withheld, beside the names it lists; docs/HARDENING.md,
"Least confident (stage P1's close, 2026-11-14)", item 1.

Since TASK-055, tests/test_release_t_strip.py no longer reads secret-like names in the run it is launched in, since the
launcher adds a key file's names after the strip. tests/test_bridge_run.py's
`test_r055_d004_a_stripped_run_gets_the_notes_names` launches through `--strip` with the names the note lists by name.
What no test held through a real launch: a name the note does not list, withheld only because `SECRET_LIKE` matches it,
set in the launching environment. These tests launch `bridge-run.py --strip --kind test` with such names, made up, and
read the child's environment: alone, and beside a key file that names another variable, so that a launcher which put
the launching environment back after the strip, or with the key file's lines, would fail them. Each case runs once
without `--strip` too, so the names are shown to reach the child when nothing withholds them.
"""
import json
import os
import subprocess
import sys

import pytest

from test_account_keys import d004_stripped_note

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")

# Made up for this test, one for each kind of word SECRET_LIKE reads: a whole-word token and secret, a password, an
# access key, and a name ending in _KEY. None is a name D-004's note lists or a token variable bridge_env names.
MADE_UP = {
    "FIX005_PROBE_TOKEN": "t-never-printed",
    "FIX005_PROBE_SECRET": "s-never-printed",
    "FIX005_PROBE_PASSWORD": "p-never-printed",
    "FIX005_PROBE_ACCESS_KEY": "a-never-printed",
    "FIX005_PROBE_KEY": "k-never-printed",
}
KEY_FILE_NAME = "FIX005_KEYFILE_API_KEY"
CODE = "import json, os; print(json.dumps(sorted(os.environ)))"


def env_for(tmp_path, **extra):
    """The launching environment: the test's own, LOCALAPPDATA in tmp_path (nothing written to the real profile), the
    tests' helper flag the launcher reads to accept `python -c`, and the made-up names."""
    env = dict(os.environ)
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    env.update(extra)
    return env


def child_names(tmp_path, strip, key_file=None):
    """The names the child sees when bridge-run.py --kind test launches it from a Workspace in tmp_path."""
    ws = tmp_path / "Workspace"
    ws.mkdir(exist_ok=True)
    argv = [sys.executable, PROG, "--limit", "30"]
    if strip:
        argv.append("--strip")
    argv += ["--kind", "test"]
    if key_file is not None:
        argv += ["--key-file", str(key_file)]
    argv += ["--", sys.executable, "-c", CODE]
    p = subprocess.run(argv, capture_output=True, text=True, env=env_for(tmp_path, **MADE_UP), cwd=str(ws))
    assert p.returncode == 0, p.stderr
    for value in MADE_UP.values():
        assert value not in p.stdout and value not in p.stderr, "a value is never printed"
    return set(json.loads(p.stdout.strip().splitlines()[-1]))


def test_r052_the_made_up_names_are_withheld_only_by_the_pattern(program):
    """The precondition: each made-up name is one SECRET_LIKE matches, and none is withheld by name, so the cases below
    hold the pattern's path through the launcher and not the list's (a negative test must show its precondition)."""
    be = program("bridge_env")
    withheld, _, _, _ = d004_stripped_note()
    for name in list(MADE_UP) + [KEY_FILE_NAME]:
        assert be.secret_like(name), name
        assert name not in withheld and name not in be.TOKEN_VARS, name


def test_r052_a_stripped_launch_withholds_a_secret_like_name_set_in_the_launching_environment(tmp_path):
    """No key file: through `--strip` the child holds none of the made-up names; without it, all of them."""
    assert not set(MADE_UP) & child_names(tmp_path, strip=True), "a secret-like name reached a stripped run"
    assert set(MADE_UP) <= child_names(tmp_path, strip=False), "the control: without --strip the names reach the child"


def test_r052_a_key_file_adds_its_own_names_and_never_brings_the_stripped_ones_back(tmp_path):
    """A key file naming another variable (the route the loop allows a suite): the child gets the key file's name, which
    the launcher adds after the strip, and still none of the made-up names from the launching environment."""
    keys = tmp_path / "keys.txt"
    keys.write_text("%s=kf-never-printed\n" % KEY_FILE_NAME, encoding="utf-8")
    names = child_names(tmp_path, strip=True, key_file=keys)
    assert KEY_FILE_NAME in names, "the key file's name reaches the child"
    assert not set(MADE_UP) & names, "a secret-like name of the launching environment came back with the key file"
    assert set(MADE_UP) <= child_names(tmp_path, strip=False, key_file=keys), "the control: without --strip they reach it"


@pytest.mark.parametrize("name", sorted(MADE_UP))
def test_r052_each_made_up_name_is_withheld_alone(name, tmp_path, monkeypatch):
    """Each name on its own, so that a strip which caught one word of the pattern and missed another shows which."""
    monkeypatch.setattr(sys.modules[__name__], "MADE_UP", {name: MADE_UP[name]})
    assert name not in child_names(tmp_path, strip=True), name
