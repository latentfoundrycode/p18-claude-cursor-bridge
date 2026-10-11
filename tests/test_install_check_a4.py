"""bridge-install.py (release A4, the 2026.10.05a review's second pass S2 to S4): a checkout whose
main-as-merged state git cannot confirm is refused instead of installed without a word; Python's
cache folder is not an uncommitted change; a release that could not be taken back afterwards is
not installed. Scratch checkouts and targets."""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_rollback import make_old_release, install_new, install_old, OLD_VERSION  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")


def git(folder, *args):
    p = subprocess.run(["git", "-C", str(folder)] + list(args), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr


def run(prog, tmp_path, *args):
    env = dict(ENV, LOCALAPPDATA=str(tmp_path / "localappdata"))
    p = subprocess.run([sys.executable, str(prog)] + list(args), capture_output=True, text=True, env=env, cwd=str(tmp_path))
    return p.returncode, p.stdout + p.stderr


def checkout(tmp_path, with_origin=True):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    shutil.copytree(RELEASE, repo / "bridge", ignore=shutil.ignore_patterns("__pycache__"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a release")
    if with_origin:
        git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def test_a_checkout_without_a_readable_origin_main_is_refused(tmp_path):
    repo = checkout(tmp_path, with_origin=False)
    installer, target = repo / "bridge" / "cursor-bridge" / "bridge-install.py", tmp_path / ".claude"
    rc, out = run(installer, tmp_path, "--target", str(target))
    assert rc == 2 and "cannot be confirmed" in out and "nothing was changed" in out and not target.exists(), "installed without a word although git could not say whether main is merged (S2): " + out


def test_pythons_cache_folder_is_not_an_uncommitted_change(tmp_path):
    repo = checkout(tmp_path)
    (repo / "bridge" / "cursor-bridge" / "__pycache__").mkdir()
    (repo / "bridge" / "cursor-bridge" / "__pycache__" / "x.cpython-312.pyc").write_bytes(b"\x00")
    installer, target = repo / "bridge" / "cursor-bridge" / "bridge-install.py", tmp_path / ".claude"
    rc, out = run(installer, tmp_path, "--target", str(target))
    assert rc == 0 and "RESULT: INSTALLED TREE MATCHES" in out, "__pycache__ was read as an uncommitted change (S3): " + out


def test_a_release_that_could_not_be_taken_back_is_not_installed(tmp_path, program):
    old = make_old_release(tmp_path / "old-release", program)
    target = tmp_path / ".claude"
    rc, out = install_new(tmp_path, target)
    assert rc == 0, out
    (target / "cursor-bridge" / "scope-check.py").write_text("changed on this computer\n", encoding="utf-8")
    rc, out = install_old(tmp_path, old, target)
    assert rc == 2 and "could not be taken back" in out and "Nothing was changed" in out, "the release was installed although the way back would refuse (S4): " + out
    assert (target / "cursor-bridge" / "scope-check.py").read_text(encoding="utf-8") == "changed on this computer\n", "the target was replaced"
    rc, out = run(old / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target), "--anyway")
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, "the maintainer's rehearsals install regardless: " + out
