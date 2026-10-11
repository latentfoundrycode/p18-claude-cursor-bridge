"""lock-check.py (release A4, 13.1): no alarm when a manifest changed outside its dependencies, and
none when no lockfile is in use beside it; the alarm stays for a dependency change without its
lockfile. Scratch repositories."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "lock-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")

PYPROJECT = """[project]
name = "thing"
version = "0.1.0"
description = "a thing"
dependencies = [
  "requests>=2.31",
]

[tool.pytest.ini_options]
addopts = "-q"
"""
PACKAGE = '{"name": "thing", "version": "1.0.0", "scripts": {"test": "jest"}, "dependencies": {"left-pad": "^1.0.0"}}\n'


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr


def make(tmp_path, with_lock=True):
    r = tmp_path / "ws"
    r.mkdir()
    (r / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (r / "package.json").write_text(PACKAGE, encoding="utf-8")
    if with_lock:
        (r / "poetry.lock").write_text("# lock\n", encoding="utf-8")     # Poetry's lock does not record the root version; uv.lock does (first pass, F11)
        (r / "package-lock.json").write_text("{}\n", encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    return r


def run(repo):
    p = subprocess.run([sys.executable, PROG, "HEAD"], cwd=str(repo), capture_output=True, text=True, env=ENV)
    return p.returncode, p.stdout


def test_a_change_outside_the_dependencies_needs_no_lockfile(tmp_path):
    r = make(tmp_path)
    (r / "pyproject.toml").write_text(PYPROJECT.replace('version = "0.1.0"', 'version = "0.2.0"').replace('addopts = "-q"', 'addopts = "-q -x"'), encoding="utf-8")
    (r / "package.json").write_text(PACKAGE.replace('"version": "1.0.0"', '"version": "1.1.0"'), encoding="utf-8")
    rc, out = run(r)
    assert rc == 0 and "outside its dependencies" in out, "a version bump raised the lockfile alarm (13.1): " + out


def test_a_dependency_change_without_its_lockfile_is_still_refused(tmp_path):
    r = make(tmp_path)
    (r / "pyproject.toml").write_text(PYPROJECT.replace('"requests>=2.31",', '"requests>=2.31",\n  "httpx>=0.27",'), encoding="utf-8")
    rc, out = run(r)
    assert rc == 1 and "LOCKFILE MISSING" in out and "pyproject.toml" in out, out


def test_no_lockfile_in_use_means_nothing_can_go_stale(tmp_path):
    r = make(tmp_path, with_lock=False)
    (r / "pyproject.toml").write_text(PYPROJECT.replace('"requests>=2.31",', '"requests>=2.31",\n  "httpx>=0.27",'), encoding="utf-8")
    rc, out = run(r)
    assert rc == 0 and "no lockfile" in out.lower(), "a project that locks nothing raised the alarm (13.1): " + out
