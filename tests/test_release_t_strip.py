"""TASK-041 (a): the environment a stripped suite launch hands the suite (R-052).

enforces: docs/REQUIREMENTS.md R-052 (the loop's suite and driver launches carry `--strip`); docs/diagrams/D-004-context-dfd.md,
the note "Stripped environment" (what is withheld and what is set).

One environment test, not a pin and not in a mutants file's new_tests: it reads the environment this pytest process was
given. Under `bridge-run.py --strip` the launcher sets GH_CONFIG_DIR to the empty folder and HOME to the agent home, while
LOCALAPPDATA stays the owner's real folder (D-004's deviation), so the owner's profile is read from it. Where GH_CONFIG_DIR
is set and HOME is not the owner's profile, the run is a stripped one, and HOME must be the agent home and every name the
note lists as withheld absent. Anywhere else (CI, a plain local run) it skips and says why. The environment is read when
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


def owner_profile():
    """The owner's profile folder, read from LOCALAPPDATA (<profile>/AppData/Local), which the strip leaves the owner's;
    None where it is not set."""
    local = LAUNCH_ENV.get("LOCALAPPDATA")
    if not local:
        return None
    return os.path.dirname(os.path.dirname(os.path.normpath(local)))


def git_bash_put_it_back(name, value):
    """Git for Windows' login shell sets SSH_ASKPASS to its own helper, so a shell an agent opens inside a stripped run
    (Review B's, TASK-041 round 1) holds it though the launcher withheld it. The helper holds no secret and only that value
    is excused here; that the launcher withholds the name is the next test's."""
    return name == "SSH_ASKPASS" and os.path.basename(value.replace("\\", "/")).lower() == "git-askpass.exe"


def test_r052_the_strip_itself_withholds_git_bash_s_helper(tmp_path):
    """The name the test below excuses for its one value: stripped_env removes it whatever its value, so the excuse hides
    no launcher that keeps it. tmp_path stands in for the profile, as tests/test_account_keys.py's sample does."""
    env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "HOME": str(tmp_path),
           "USERPROFILE": str(tmp_path), "SSH_ASKPASS": "C:/somewhere/git-askpass.exe"}
    (tmp_path / ".cursor").mkdir()
    assert "SSH_ASKPASS" not in bridge_env.stripped_env(env)


def test_r052_a_stripped_suite_launch_gets_the_agent_home_and_no_withheld_name():
    env = LAUNCH_ENV
    profile = owner_profile()
    home = env.get("HOME", "")
    if not env.get("GH_CONFIG_DIR"):
        pytest.skip("GH_CONFIG_DIR is not set: this run was not launched with --strip")
    if profile is None:
        pytest.skip("LOCALAPPDATA is not set: the owner's profile cannot be read, so a stripped run cannot be told apart")
    if not home or _same(home, profile):
        pytest.skip("HOME is the owner's profile: this run was not launched with --strip")
    assert _same(home, os.path.join(profile, ".cursor-bridge", "agent-home")), "HOME is not the agent home: " + home
    assert _same(env.get("USERPROFILE", ""), home), "USERPROFILE is not the agent home"
    present = [name for name in WITHHELD if name in env and not git_bash_put_it_back(name, env[name])]
    assert not present, "withheld names present: " + ", ".join(present)
    secret = sorted(name for name in env if bridge_env.secret_like(name))
    assert not secret, "names SECRET_LIKE matches present: " + ", ".join(secret)
    assert env.get("GIT_TERMINAL_PROMPT") == "0"
