"""TASK-060, the supervisor's acceptance tests: the strip's names (R-080).

enforces: docs/REQUIREMENTS.md R-080; docs/DESIGN.md, "Change: the program release", J10 and J11; docs/BUILD_PLAN.md,
TASK-060's Done when.

- J10: a key file's values are applied after the strip, so a key file line naming a home variable (`USERPROFILE`,
  `HOME`, `HOMEDRIVE`, `HOMEPATH`, `APPDATA`, `LOCALAPPDATA`), in any letter case, would undo it: the run is refused
  before it starts (exit 125, no `bridge-run: started` line), the name printed and the value never, for every kind that
  takes a key file (the test kind's named suite, the watch kind); the control: a key file of ordinary names runs.
- J11: the secret-like name test, one copy in `bridge_env.py`, also matches `PAT`, `CREDS` and `AUTH` as name parts
  (bounded by `_` or the name's ends, so `PATH`, `PATTERN`, `AUTHOR_NAME` and their kin stay apart), `DATABASE_URL` and
  `SSH_AUTH_SOCK`, beside every name it matched before; a secret-like `CURSOR_` name is withheld from test and driver
  runs (a `CURSOR_` name that is not secret-like passes); `conformance-check.py` holds no copy of its own and its floor
  on keys within the builder's reach names the new forms.

At the checkpoint every case is red but the controls. The builder adds its cases to tests/test_bridge_run.py,
tests/test_account_keys.py and tests/test_conformance_check.py and edits nothing in this file.
"""
import os
import re
import subprocess
import sys

import pytest

import test_conformance_check as tc

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
CONFORMANCE = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "conformance-check.py")
HIDDEN = "VALUE-NEVER-PRINTED"
HOME_NAMES = ["USERPROFILE", "HOME", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA"]
NEW_FORMS = ["PAT", "GITHUB_PAT", "PAT_FOR_CI", "MY_PAT_2", "CREDS", "AWS_CREDS", "CREDS_FILE", "AUTH", "GH_AUTH",
             "AUTH_HEADER", "NO_AUTH_X", "DATABASE_URL", "SSH_AUTH_SOCK", "github_pat", "Aws_Creds"]
NOT_SECRET = ["PATH", "PATHEXT", "PATTERN", "SPAT", "PATHS_X", "AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "AUTHORITY", "OAUTHLIB_X",
              "CREDSTORE", "SCREDS", "DATABASE_HOST", "SSH_AGENT_PID", "LOG_LEVEL", "TOKENIZERS_PARALLELISM", "SECRETARY"]
BEFORE = ["ANTHROPIC_API_KEY", "HF_TOKEN", "STRIPE_SECRET_KEY", "PGPASSWORD", "SFVF_SECRETS_PASSPHRASE", "DEPLOY_KEYS"]


@pytest.fixture
def be(program):
    return program("bridge_env")


def project(tmp_path):
    """A launch folder whose one test writes the names of the environment it got to run/names.txt."""
    ws = tmp_path / "ws"
    (ws / "tests").mkdir(parents=True)
    (ws / "run").mkdir()
    out = (ws / "run" / "names.txt").as_posix()
    (ws / "tests" / "test_names.py").write_text(
        "import os\n\ndef test_names():\n    open(%r, 'w', encoding='utf-8').write('\\n'.join(sorted(os.environ)))\n" % out,
        encoding="utf-8")
    return ws


def launcher_env(tmp_path, **extra):
    """The launching environment: this interpreter first on PATH (a named suite's head is the word `python`), and before
    it a stand-in `gh` that prints and exits, so a watch never reaches GitHub."""
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("BRIDGE_RUN_ALLOW_ANY", "BRIDGE_RUN_SLOT_SCALE")}
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    if sys.platform == "win32":
        (bin_dir / "gh.cmd").write_text("@echo off\r\necho STAND-IN gh\r\nexit /b 0\r\n", encoding="ascii")
    else:
        (bin_dir / "gh").write_text("#!/bin/sh\necho STAND-IN gh\n", encoding="ascii")
        (bin_dir / "gh").chmod(0o755)
    env["PATH"] = os.pathsep.join([str(bin_dir), os.path.dirname(sys.executable), env.get("PATH", "")])
    env.update(extra)
    return env


def launch(ws, words, env, kind="test", key_file=None, strip=True):
    argv = [sys.executable, PROG, "--limit", "120"] + (["--strip"] if strip else []) + ["--kind", kind]
    argv += (["--key-file", str(key_file)] if key_file is not None else []) + ["--"] + list(words)
    return subprocess.run(argv, capture_output=True, text=True, cwd=str(ws), env=env, timeout=300)


def suite(ws):
    return ["python", "-m", "pytest", "-p", "no:cacheprovider", "-q", "tests/test_names.py"]


def names_seen(ws):
    return set(open(str(ws / "run" / "names.txt"), encoding="utf-8").read().split())


def key_file(tmp_path, lines):
    path = tmp_path / "keys" / "keys.env"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return path


def assert_refused_before_start(p, name):
    assert "Traceback" not in p.stderr, p.stderr
    assert p.returncode == 125, (name, p.returncode, p.stderr)
    assert "bridge-run: started" not in p.stderr, (name, p.stderr)
    assert name in p.stderr, (name, p.stderr)
    assert HIDDEN not in p.stderr and HIDDEN not in p.stdout, "the value must never be printed"


# ---------------------------------------------------------------- J10: a key file's home variables


@pytest.mark.parametrize("name", HOME_NAMES + ["home", "Home", "userprofile", "LocalAppData"])
def test_r080_a_key_file_naming_a_home_variable_is_refused_before_the_test_run(tmp_path, name):
    """A key file's values are applied after the strip: a home variable among them would undo it. The control: the same
    launch with a key file of ordinary names runs and the run gets them."""
    ws = project(tmp_path)
    env = launcher_env(tmp_path)
    ok = launch(ws, suite(ws), env, key_file=key_file(tmp_path, ["FIX060_SETTING=1"]))
    assert ok.returncode == 0 and "bridge-run: started" in ok.stderr, ok.stderr
    assert "FIX060_SETTING" in names_seen(ws)
    os.remove(str(ws / "run" / "names.txt"))
    p = launch(ws, suite(ws), env, key_file=key_file(tmp_path, ["FIX060_SETTING=1", "%s=%s" % (name, HIDDEN)]))
    assert_refused_before_start(p, name)
    assert not (ws / "run" / "names.txt").exists(), "the suite must not have run"


@pytest.mark.parametrize("name", HOME_NAMES)
def test_r080_a_key_file_naming_a_home_variable_is_refused_before_a_watch(tmp_path, name):
    """The watch kind takes a key file too. The control: a key file of ordinary names starts the stand-in."""
    ws = project(tmp_path)
    env = launcher_env(tmp_path)
    words = ["gh", "pr", "checks", "1"]                      # without --watch: no wait for GitHub's first check
    ok = launch(ws, words, env, kind="watch", strip=False, key_file=key_file(tmp_path, ["FIX060_SETTING=1"]))
    assert ok.returncode == 0 and "bridge-run: started" in ok.stderr and "STAND-IN gh" in ok.stdout, ok.stdout + ok.stderr
    p = launch(ws, words, env, kind="watch", strip=False, key_file=key_file(tmp_path, ["%s=%s" % (name, HIDDEN)]))
    assert_refused_before_start(p, name)
    assert "STAND-IN gh" not in p.stdout


# ---------------------------------------------------------------- J11: the name test


@pytest.mark.parametrize("name", NEW_FORMS)
def test_r080_the_name_test_matches_the_new_forms(be, name):
    assert be.secret_like(name), name


@pytest.mark.parametrize("name", NOT_SECRET)
def test_r080_the_name_test_tells_the_boundary_cases_apart(be, name):
    """`PAT`, `CREDS` and `AUTH` count only bounded by `_` or the name's ends."""
    assert not be.secret_like(name), name


@pytest.mark.parametrize("name", BEFORE)
def test_r080_the_name_test_still_matches_what_it_matched(be, name):
    assert be.secret_like(name), name


def test_r080_the_new_forms_never_reach_a_stripped_test_run(tmp_path):
    ws = project(tmp_path)
    env = launcher_env(tmp_path, **{n: HIDDEN for n in ["GITHUB_PAT", "AWS_CREDS", "GH_AUTH", "DATABASE_URL", "SSH_AUTH_SOCK"]})
    env.update({"PATTERN": "kept", "AUTHOR_NAME": "kept"})
    p = launch(ws, suite(ws), env)
    assert p.returncode == 0, p.stderr
    seen = names_seen(ws)
    for n in ("GITHUB_PAT", "AWS_CREDS", "GH_AUTH", "DATABASE_URL", "SSH_AUTH_SOCK"):
        assert n not in seen, n
    for n in ("PATTERN", "AUTHOR_NAME"):
        assert n in seen, n


def test_r080_a_secret_like_cursor_name_is_withheld_from_a_test_run(tmp_path):
    """Cursor's own variables were kept for every stripped run; a test run needs none of them. A `CURSOR_` name that is
    not secret-like passes."""
    ws = project(tmp_path)
    env = launcher_env(tmp_path, CURSOR_API_KEY=HIDDEN, CURSOR_TOKEN=HIDDEN, CURSOR_TRACE_LEVEL="1")
    p = launch(ws, suite(ws), env)
    assert p.returncode == 0, p.stderr
    seen = names_seen(ws)
    assert "CURSOR_API_KEY" not in seen and "CURSOR_TOKEN" not in seen, sorted(n for n in seen if n.startswith("CURSOR"))
    assert "CURSOR_TRACE_LEVEL" in seen


def test_r080_a_secret_like_cursor_name_is_withheld_from_a_driver_run(tmp_path):
    ws = tmp_path / "launch"
    (ws / "run" / "supervisor").mkdir(parents=True)
    (ws / "run" / "launcher").mkdir(parents=True)
    out = (ws / "run" / "names.txt").as_posix()
    (ws / "run" / "supervisor" / "names.py").write_text(
        "import os\nopen(%r, 'w', encoding='utf-8').write('\\n'.join(sorted(os.environ)))\n" % out, encoding="utf-8")
    env = launcher_env(tmp_path, CURSOR_API_KEY=HIDDEN, CURSOR_TRACE_LEVEL="1")
    p = subprocess.run([sys.executable, PROG, "--limit", "120", "--strip", "--kind", "driver", "--", "python", "run/supervisor/names.py"],
                       capture_output=True, text=True, cwd=str(ws), env=env, timeout=300)
    assert p.returncode == 0, p.stderr
    seen = names_seen(ws)
    assert "CURSOR_API_KEY" not in seen and "CURSOR_TRACE_LEVEL" in seen


# ---------------------------------------------------------------- J11: the one copy


def test_r080_conformance_check_holds_no_copy_of_the_name_test():
    """The one copy is bridge_env's: conformance-check reads it through its load of bridge_env by file."""
    text = open(CONFORMANCE, encoding="utf-8").read()
    assert "PASSPHRASE" not in text and "TOKENS?" not in text, "conformance-check.py still holds a copy of the name test"
    assert re.search(r"bridge_env\.(secret_like|SECRET_LIKE)\b", text), "conformance-check.py does not read bridge_env's test"


def test_r080_the_keys_floor_names_the_new_forms(tmp_path):
    tc.make_workspace(tmp_path)
    (tmp_path / ".env").write_text("GITHUB_PAT=%s\nAWS_CREDS=%s\nLOG_LEVEL=debug\n" % (HIDDEN, HIDDEN), encoding="utf-8")
    rc, out = tc.run(tmp_path)
    v, line = tc.verdict(out, "Keys out of the builder's reach")
    assert v == "MISSING" and "GITHUB_PAT" in line and "AWS_CREDS" in line, (v, line)
    assert HIDDEN not in out, "values must never be printed"


def test_r080_the_session_note_names_the_new_forms(tmp_path):
    tc.make_workspace(tmp_path)
    env = dict(os.environ)
    env.update(GITHUB_PAT=HIDDEN, AWS_CREDS=HIDDEN)
    p = subprocess.run([sys.executable, CONFORMANCE, str(tmp_path), "--offline"], capture_output=True, text=True, env=env)
    v, line = tc.verdict(p.stdout, "Account keys in the session's environment")
    assert v == "NOTE" and "GITHUB_PAT" in line and "AWS_CREDS" in line, (v, line)
    assert HIDDEN not in p.stdout
