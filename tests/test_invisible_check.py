"""invisible-check.py (release A4, 13.1): zero-width and bidirectional characters in changed files are
listed by code point; a leading byte-order mark and binary files are not findings."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "invisible-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr


def test_invisible_characters_in_changed_files_are_listed(tmp_path):
    r = tmp_path / "ws"
    r.mkdir()
    (r / "clean.py").write_text("x = 1\n", encoding="utf-8")
    (r / "bom.py").write_text("﻿y = 2\n", encoding="utf-8")
    (r / "img.png").write_bytes(b"\x89PNG\x00\x00" + "​".encode("utf-8"))   # a binary file holding the bytes of a zero-width space
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    p = subprocess.run([sys.executable, PROG, "HEAD"], cwd=str(r), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0 and "RESULT: OK" in p.stdout, p.stdout
    (r / "clean.py").write_text("x = 1\nif access_level != 'user‮' and True: # ​hidden\n", encoding="utf-8")
    (r / "new.md").write_text("soft­hyphen\n", encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, "HEAD"], cwd=str(r), capture_output=True, text=True, env=ENV)
    out = p.stdout
    assert p.returncode == 1 and "clean.py:2:" in out and "U+202E" in out and "U+200B" in out and "new.md:1:" in out and "U+00AD" in out, out
    assert "bom.py" not in out and "img.png" not in out, out
    p = subprocess.run([sys.executable, PROG, "--all"], cwd=str(r), capture_output=True, text=True, env=ENV)
    assert p.returncode == 1 and "clean.py" in p.stdout and "bom.py" not in p.stdout, p.stdout
