"""TASK-041 (a), TASK-055: the environment a stripped suite launch hands the suite (R-052, R-076).

enforces: docs/REQUIREMENTS.md R-052 (the loop's suite and driver launches carry `--strip`) and R-076 (the bridge's suite
passes in a stripped run, the test assuming nothing of the shell it runs in); docs/diagrams/D-004-context-dfd.md, the note
"Stripped environment" (what is withheld and what is set).

The environment test reads the environment this pytest process was launched with, read when the module is collected,
before tests/conftest.py's autouse fixture `home_of_the_tests` points HOME and USERPROFILE at a temporary folder for the
test itself. tests/conftest.py replaces APPDATA when it is imported, before this module is, and keeps the launch value
first under its own name (`BRIDGE_TESTS_LAUNCH_APPDATA`), which is read here where the launcher's APPDATA is claimed
(TASK-055: until then a stripped run of the suite failed this test on conftest's temporary folder). Under
`bridge-run.py --strip` the launcher sets GH_CONFIG_DIR to the empty folder and HOME to the agent home, and since release
S (C1) APPDATA and LOCALAPPDATA to that folder's skeleton (docs/diagrams/D-004-context-dfd.md's note). Where GH_CONFIG_DIR
is set and HOME is an agent home, the run is a stripped one: USERPROFILE and the two application folders must agree with
it, git must not prompt, and the owner's GitHub login must be absent. Anywhere else (CI, a plain local run, a shell that
points HOME elsewhere) it skips and says why.

What a later hand may put into a stripped run is not the launcher's doing and is not read as a leak (TASK-055, R-076):
an agent's shell inside the run sets Git for Windows' SSH_ASKPASS helper and the GIT_CONFIG_COUNT, GIT_CONFIG_KEY_0 and
GIT_CONFIG_VALUE_0 triple (Review B's runs of TASK-041 and of the carry, docs/HARDENING.md), and a key file
(`--key-file`, the route the loop allows a suite) adds its names, which may be named like an account key. That the strip
itself withholds each of those names, whatever its value, is held by the pins below over `bridge_env.stripped_env`, and by
tests/test_bridge_run.py's `test_r055_d004_a_stripped_run_gets_the_notes_names` through a real launch. The conditions are
held by tests of their own on environments `stripped_env` makes: each set, the check finds nothing; each thing the check
reads changed, it finds a problem."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bridge", "cursor-bridge"))
import bridge_env  # noqa: E402

LAUNCH_APPDATA = "BRIDGE_TESTS_LAUNCH_APPDATA"     # tests/conftest.py's name for the launch value of APPDATA (TASK-055)


def launch_env(environ):
    """The environment as the launcher handed it: `environ` with APPDATA put back from conftest's kept launch value, and
    conftest's own name dropped."""
    env = dict(environ)
    if LAUNCH_APPDATA in env:
        env["APPDATA"] = env.pop(LAUNCH_APPDATA)
    return env


LAUNCH_ENV = launch_env(os.environ)  # as the launcher handed it, before any fixture runs

# D-004's note, "Stripped environment": the names withheld by name; every other name SECRET_LIKE matches is withheld too,
# but CURSOR_* and GIT_CONFIG_KEY_* (bridge_env.secret_like)
WITHHELD = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS",
            "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0")
# The three an agent's shell inside a stripped run sets again (Review B of the carry, docs/HARDENING.md); any value.
SHELL_SETS = ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0")
APP_FOLDERS = (("APPDATA", os.path.join("AppData", "Roaming")), ("LOCALAPPDATA", os.path.join("AppData", "Local")))


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
    is excused here; that the launcher withholds the name is the pins'."""
    return name == "SSH_ASKPASS" and os.path.basename(value.replace("\\", "/")).lower() == "git-askpass.exe"


def stripped_launch_check(env):
    """(skip reason, problems) of a launch environment: a reason where it is not a stripped launch's, else None and the
    list of what disagrees with D-004's note, empty where nothing does."""
    home = env.get("HOME", "")
    if not env.get("GH_CONFIG_DIR"):
        return "GH_CONFIG_DIR is not set: this run was not launched with --strip", []
    if not home or not is_agent_home(home):
        return "HOME is not an agent home: this run was not launched with --strip, or a shell inside it moved HOME", []
    problems = []
    if not _same(env.get("USERPROFILE", ""), home):
        problems.append("USERPROFILE is not the agent home")
    for name, rel in APP_FOLDERS:
        if env.get(name) and not _same(env[name], os.path.join(home, rel)):   # release S (C1): the run's own folders
            problems.append("%s is not the agent home's skeleton: %s" % (name, env[name]))
    present = [name for name in WITHHELD
               if name in env and name not in SHELL_SETS and not git_bash_put_it_back(name, env[name])]
    if present:
        problems.append("withheld names present: " + ", ".join(present))
    if env.get("GIT_TERMINAL_PROMPT") != "0":
        problems.append("GIT_TERMINAL_PROMPT is not 0")
    return None, problems


def test_r052_the_strip_itself_withholds_git_bash_s_helper(tmp_path, monkeypatch):
    """The name the check excuses for its one value: stripped_env removes it whatever its value, so the excuse hides
    no launcher that keeps it. tmp_path stands in for the profile, as tests/test_account_keys.py's sample does, and for
    LOCALAPPDATA, where `stripped_env` makes its empty `gh` folder, so the owner's profile gets none (stage T2's review)."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "HOME": str(tmp_path),
           "USERPROFILE": str(tmp_path), "SSH_ASKPASS": "C:/somewhere/git-askpass.exe"}
    (tmp_path / ".cursor").mkdir()
    assert "SSH_ASKPASS" not in bridge_env.stripped_env(env)


def test_r052_a_stripped_suite_launch_gets_the_agent_home_and_no_withheld_name():
    """R-052, R-076: the environment this run was launched with, read through conftest's kept APPDATA."""
    reason, problems = stripped_launch_check(LAUNCH_ENV)
    if reason:
        pytest.skip(reason)
    assert not problems, "; ".join(problems)


def test_r076_conftest_keeps_the_launch_appdata_under_its_own_name():
    """TASK-055: where the run was launched with an APPDATA, conftest replaced it with a temporary folder of the tests'
    own and kept the launch value under its name, which the launch environment read here carries back; where it was
    launched with none (CI's Linux leg), neither is set."""
    if os.environ.get(LAUNCH_APPDATA):
        assert os.path.basename(os.path.normpath(os.environ["APPDATA"])).startswith("bridge-tests-appdata-")
        assert LAUNCH_ENV["APPDATA"] == os.environ[LAUNCH_APPDATA] != os.environ["APPDATA"]
    else:
        assert not os.environ.get("APPDATA") and not LAUNCH_ENV.get("APPDATA")
    assert LAUNCH_APPDATA not in LAUNCH_ENV
    assert launch_env({"APPDATA": "temporary", LAUNCH_APPDATA: "launched", "X": "1"}) == {"APPDATA": "launched", "X": "1"}
    assert launch_env({"X": "1"}) == {"X": "1"}


def a_stripped_env(tmp_path, monkeypatch):
    """An environment `bridge_env.stripped_env` makes from a sample owner's: tmp_path's profile with its `.cursor`, an
    APPDATA of its own and a LOCALAPPDATA under `<profile>/AppData/Local`."""
    profile = tmp_path / "profile"
    (profile / ".cursor").mkdir(parents=True)
    appdata = tmp_path / "appdata"
    appdata.mkdir()
    local = profile / "AppData" / "Local"
    os.makedirs(str(local), exist_ok=True)
    monkeypatch.setenv("LOCALAPPDATA", str(local))     # where stripped_env makes its empty gh folder
    owner = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "HOME": str(profile),
             "USERPROFILE": str(profile), "APPDATA": str(appdata), "LOCALAPPDATA": str(local)}
    return bridge_env.stripped_env(owner)


# What a later hand adds to a stripped run, which the check must pass: two of R-076's four assumptions of the shell (a
# shell's GIT_CONFIG triple, a key file's secret-like name), each red on the checkpoint (TASK-055's accept commit), and
# Git Bash's helper, release T's case (R-052). R-076's other two were a skip and green on the checkpoint already, release
# S's rewrite (22dc72d) having removed the readings that made them: a moved HOME is pinned below as a skip; the profile
# layout has no test, since the check reads no profile path and such a test would only repeat the control.
CONDITIONS = {
    "a shell's GIT_CONFIG triple": {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.quotepath", "GIT_CONFIG_VALUE_0": "false"},
    "Git Bash's helper": {"SSH_ASKPASS": "C:/Program Files/Git/mingw64/bin/git-askpass.exe"},
    "a key file's secret-like name": {"SAMPLE_API_KEY": "x"},
}


@pytest.mark.parametrize("condition", sorted(CONDITIONS))
def test_r076_the_check_finds_nothing_in_a_stripped_run_a_later_hand_added_to(condition, tmp_path, monkeypatch):
    env = a_stripped_env(tmp_path, monkeypatch)
    assert stripped_launch_check(env) == (None, []), "the control: what the strip makes passes"
    env.update(CONDITIONS[condition])
    assert stripped_launch_check(env) == (None, []), condition


def test_r076_a_shell_that_moves_home_skips_rather_than_fails(tmp_path, monkeypatch):
    """A shell inside the run that points HOME elsewhere (Review B's own run of stage H2, docs/HARDENING.md): no longer a
    stripped launch's environment to judge, so the check skips and says why."""
    env = a_stripped_env(tmp_path, monkeypatch)
    env["HOME"] = str(tmp_path / "moved")
    reason, problems = stripped_launch_check(env)
    assert reason and "HOME" in reason and problems == []


BREAKS = {
    "the GitHub token": ("GH_TOKEN", "x", "withheld names present: GH_TOKEN"),
    "the enterprise token": ("GITHUB_ENTERPRISE_TOKEN", "x", "withheld names present: GITHUB_ENTERPRISE_TOKEN"),
    "git's askpass": ("GIT_ASKPASS", "C:/somewhere/askpass.exe", "withheld names present: GIT_ASKPASS"),
    "another SSH_ASKPASS": ("SSH_ASKPASS", "C:/somewhere/other.exe", "withheld names present: SSH_ASKPASS"),
    "USERPROFILE the owner's": ("USERPROFILE", "PROFILE", "USERPROFILE is not the agent home"),
    "APPDATA the owner's": ("APPDATA", "APPDATA", "APPDATA is not the agent home's skeleton"),
    "LOCALAPPDATA the owner's": ("LOCALAPPDATA", "LOCAL", "LOCALAPPDATA is not the agent home's skeleton"),
    "git may prompt": ("GIT_TERMINAL_PROMPT", None, "GIT_TERMINAL_PROMPT is not 0"),
}


@pytest.mark.parametrize("change", sorted(BREAKS))
def test_r076_the_check_still_finds_what_the_strip_must_not_leave(change, tmp_path, monkeypatch):
    """Each thing the check reads, changed from what the strip makes, is a problem it names: the excuses above reach
    no further."""
    env = a_stripped_env(tmp_path, monkeypatch)
    name, value, problem = BREAKS[change]
    stand_ins = {"PROFILE": str(tmp_path / "profile"), "APPDATA": str(tmp_path / "appdata"),
                 "LOCAL": str(tmp_path / "profile" / "AppData" / "Local")}
    if value is None:
        env.pop(name, None)
    else:
        env[name] = stand_ins.get(value, value)
    reason, problems = stripped_launch_check(env)
    assert reason is None and len(problems) == 1 and problems[0].startswith(problem), (change, problems)


@pytest.mark.parametrize("name,value", [("GIT_CONFIG_COUNT", "1"), ("GIT_CONFIG_KEY_0", "core.quotepath"),
                                        ("GIT_CONFIG_VALUE_0", "false"), ("SAMPLE_API_KEY", "x"), ("GH_TOKEN", "x")])
def test_r076_the_strip_itself_withholds_each_name_the_check_excuses(name, value, tmp_path, monkeypatch):
    """The names the check no longer reads as a leak, and the login it still does: stripped_env removes each whatever
    its value, so an excuse hides no launcher that keeps one (as the pin above does for Git Bash's helper)."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "HOME": str(tmp_path),
           "USERPROFILE": str(tmp_path), name: value}
    (tmp_path / ".cursor").mkdir()
    assert name not in bridge_env.stripped_env(env)
