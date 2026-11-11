"""TASK-041 (a): the environment a stripped suite launch hands the suite (R-052).

enforces: docs/REQUIREMENTS.md R-052 (the loop's suite and driver launches carry `--strip`); docs/diagrams/D-004-context-dfd.md,
the note "Stripped environment" (what is withheld and what is set).

One environment test beside a pin of `stripped_env`, neither in a mutants file's new_tests (m42 the pin's proof): it reads the environment this pytest process was
given. Under `bridge-run.py --strip` the launcher sets GH_CONFIG_DIR to the empty folder and HOME to the agent home, and
since release S (C1) APPDATA and LOCALAPPDATA to that folder's skeleton (docs/diagrams/D-004-context-dfd.md's note). Where
GH_CONFIG_DIR is set and HOME is an agent home, the run is a stripped one: USERPROFILE and the two application folders must
agree with it and every name the note lists as withheld be absent. Anywhere else (CI, a plain local run) it skips and says why. The environment is read when
the module is collected, before tests/conftest.py's autouse fixture `home_of_the_tests` points HOME and USERPROFILE at a
temporary folder for the test itself."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bridge", "cursor-bridge"))
import bridge_env  # noqa: E402

LAUNCH_ENV = dict(os.environ)  # as the launcher handed it, before any fixture runs

# D-004's note, "Stripped environment": the names withheld by name; every other name SECRET_LIKE matches is withheld too,
# but CURSOR_* and GIT_CONFIG_KEY_* (bridge_env.secret_like)
WITHHELD = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS",
            "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0")


def _same(a, b):
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def is_agent_home(home):
    """True when `home` is `<some profile>/.cursor-bridge/agent-home`, the folder a stripped launch hands the run. Since
    release S (C1) the strip points LOCALAPPDATA into that folder too, so the owner's profile can no longer be read from
    it; the folder's own two last names are the tell."""
    parts = os.path.normcase(os.path.normpath(home)).replace("\\", "/").rstrip("/").split("/")
    return parts[-2:] == [".cursor-bridge", "agent-home"]


def git_bash_put_it_back(name, value):
    """Git for Windows' login shell sets SSH_ASKPASS to its own helper, so a shell an agent opens inside a stripped run
    (Review B's, TASK-041 round 1) holds it though the launcher withheld it. The helper holds no secret and only that value
    is excused here; that the launcher withholds the name is the next test's."""
    return name == "SSH_ASKPASS" and os.path.basename(value.replace("\\", "/")).lower() == "git-askpass.exe"


def test_r052_the_strip_itself_withholds_git_bash_s_helper(tmp_path, monkeypatch):
    """The name the test below excuses for its one value: stripped_env removes it whatever its value, so the excuse hides
    no launcher that keeps it. tmp_path stands in for the profile, as tests/test_account_keys.py's sample does, and for
    LOCALAPPDATA, where `stripped_env` makes its empty `gh` folder, so the owner's profile gets none (stage T2's review)."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "HOME": str(tmp_path),
           "USERPROFILE": str(tmp_path), "SSH_ASKPASS": "C:/somewhere/git-askpass.exe"}
    (tmp_path / ".cursor").mkdir()
    assert "SSH_ASKPASS" not in bridge_env.stripped_env(env)


def test_r052_a_stripped_suite_launch_gets_the_agent_home_and_no_withheld_name():
    env = LAUNCH_ENV
    home = env.get("HOME", "")
    if not env.get("GH_CONFIG_DIR"):
        pytest.skip("GH_CONFIG_DIR is not set: this run was not launched with --strip")
    if not home or not is_agent_home(home):
        pytest.skip("HOME is not an agent home: this run was not launched with --strip")
    assert _same(env.get("USERPROFILE", ""), home), "USERPROFILE is not the agent home"
    for name, rel in (("APPDATA", os.path.join("AppData", "Roaming")), ("LOCALAPPDATA", os.path.join("AppData", "Local"))):
        if env.get(name):                                  # release S (C1): the run's own application folders, never the owner's
            assert _same(env[name], os.path.join(home, rel)), "%s is not the agent home's skeleton: %s" % (name, env[name])
    present = [name for name in WITHHELD if name in env and not git_bash_put_it_back(name, env[name])]
    assert not present, "withheld names present: " + ", ".join(present)
    secret = sorted(name for name in env if bridge_env.secret_like(name))
    assert not secret, "names SECRET_LIKE matches present: " + ", ".join(secret)
    assert env.get("GIT_TERMINAL_PROMPT") == "0"
