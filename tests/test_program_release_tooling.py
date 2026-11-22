"""TASK-074, the supervisor's acceptance tests (R-093): the release tooling checks the tree it stands in.

enforces: docs/REQUIREMENTS.md R-093; docs/BUILD_PLAN.md, TASK-074's Done when; docs/DESIGN.md, C21 and J5.

The forms these tests pin:
- bridge/cursor-bridge/bridge-check.py --sources compares the folder the program stands in, resolved, with
  `<--root>/cursor-bridge`, resolved. Where they differ it exits 2, names both folders and has hashed nothing: no
  per-file verdict (OK, STALE, MISSING, EXTRA) and no `bridge-check: ... OK, ...` count line, even where the tree it
  was pointed at holds a stale file. Where they agree, in any spelling of --root (a relative `.`, a path with a `..`),
  the check runs as today, exit 0 with `RESULT: SOURCES MATCH` or exit 1 with `RESULT: SOURCES DO NOT MATCH`, and
  that RESULT line names the folder.
- tools/make-manifest.py writes bridge/cursor-bridge/VERSION with the line ending the file already has: a CRLF file
  stays CRLF, and a second run leaves its bytes and its MANIFEST.json entry as the first run wrote them.
- Not pinned: the wording of the refusal beyond naming both folders; the message text around the folders on the
  RESULT line; which separator or letter case the folders are printed in. The check without --sources is held by
  tests/test_install_check.py and is not repeated here.

Isolation: every run is a subprocess whose HOME, USERPROFILE, LOCALAPPDATA and APPDATA are folders under pytest's
temporary folder; the trees checked and stamped are copies of this repository's bridge/ (and tools/make-manifest.py)
under that folder, and the programs run are those copies.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_RELEASE = os.path.join(ROOT, "bridge")
MAKE_MANIFEST = os.path.join(ROOT, "tools", "make-manifest.py")


def copy_release(dest):
    shutil.copytree(SOURCE_RELEASE, str(dest), ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def run(prog, tmp_path, *args, cwd=None):
    env = dict(os.environ)
    for name in ("LOCALAPPDATA", "APPDATA", "HOME", "USERPROFILE"):
        folder = tmp_path / ("scratch-" + name.lower())
        folder.mkdir(exist_ok=True)
        env[name] = str(folder)
    p = subprocess.run([sys.executable, str(prog)] + [str(a) for a in args], capture_output=True, text=True,
                       errors="replace", env=env, cwd=str(cwd) if cwd else None)
    return p.returncode, p.stdout + p.stderr


def norm(text):
    text = text.replace("\\", "/")
    return text.lower() if sys.platform == "win32" else text


def resolved(folder):
    return norm(os.path.realpath(str(folder)))


def names(text, folder):
    """True where `text` names `folder`, resolved, in either separator (and any case on Windows)."""
    return resolved(folder) in norm(text)


def result_line(out, start):
    lines = [ln for ln in out.splitlines() if ln.startswith(start)]
    assert lines, "no line starting %r in:\n%s" % (start, out)
    return lines[-1]


def hashed_nothing(out):
    for ln in out.splitlines():
        s = ln.strip()
        if ln.startswith("bridge-check:") and "OK," in ln:
            return False
        if s.split(" ")[0] in ("OK", "STALE", "MISSING", "EXTRA"):
            return False
    return True


# ---------------------------------------------------------------- bridge-check.py --sources

def test_r093_a_check_of_another_tree_is_refused_naming_both_folders(tmp_path):
    a = copy_release(tmp_path / "A")
    b = copy_release(tmp_path / "B")
    rc, out = run(a / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", b, "--sources", "--quiet")
    assert rc == 2, out
    assert names(out, a / "cursor-bridge") and names(out, b / "cursor-bridge"), out
    assert hashed_nothing(out), "the refusal comes before any file is hashed: " + out
    assert "RESULT: SOURCES MATCH" not in out, out


def test_r093_a_stale_other_tree_is_refused_not_judged(tmp_path):
    a = copy_release(tmp_path / "A")
    b = copy_release(tmp_path / "B")
    with open(b / "commands" / "supervisor.md", "a", encoding="utf-8") as f:
        f.write("\nedited after the stamp\n")
    rc, out = run(a / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", b, "--sources", "--quiet")
    assert rc == 2, "the other tree is refused, not judged stale: " + out
    assert names(out, a / "cursor-bridge") and names(out, b / "cursor-bridge"), out
    assert "STALE" not in out and hashed_nothing(out), out


def test_r093_the_tree_the_program_stands_in_matches_and_its_result_names_the_folder(tmp_path):
    tree = copy_release(tmp_path / "bridge")
    rc, out = run(tree / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", tree, "--sources", "--quiet")
    assert rc == 0, out
    assert names(result_line(out, "RESULT: SOURCES MATCH"), tree / "cursor-bridge"), out


@pytest.mark.parametrize("spelling", ["dot", "dotdot"])
def test_r093_another_spelling_of_the_same_tree_is_not_refused(tmp_path, spelling):
    tree = copy_release(tmp_path / "bridge")
    prog = tree / "cursor-bridge" / "bridge-check.py"
    if spelling == "dot":
        rc, out = run(prog, tmp_path, "--root", ".", "--sources", "--quiet", cwd=tree)
    else:
        rc, out = run(prog, tmp_path, "--root", os.path.join(str(tree), "cursor-bridge", os.pardir), "--sources", "--quiet")
    assert rc == 0, out
    assert names(result_line(out, "RESULT: SOURCES MATCH"), tree / "cursor-bridge"), out


def test_r093_an_unlisted_file_in_the_tree_it_stands_in_fails_with_the_folder_named(tmp_path):
    tree = copy_release(tmp_path / "bridge")
    (tree / "cursor-bridge" / "left-behind.md").write_text("x", encoding="utf-8")
    rc, out = run(tree / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", tree, "--sources", "--quiet")
    assert rc == 1 and "EXTRA    cursor-bridge/left-behind.md" in out, out
    assert names(result_line(out, "RESULT: SOURCES DO NOT MATCH"), tree / "cursor-bridge"), out


# ---------------------------------------------------------------- tools/make-manifest.py

def test_r093_make_manifest_keeps_a_crlf_version_file_crlf(tmp_path):
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    shutil.copy2(MAKE_MANIFEST, str(repo / "tools" / "make-manifest.py"))
    copy_release(repo / "bridge")
    version_file = repo / "bridge" / "cursor-bridge" / "VERSION"
    manifest_file = repo / "bridge" / "cursor-bridge" / "MANIFEST.json"
    version = version_file.read_bytes().decode("ascii").split()[0]
    version_file.write_bytes(version.encode("ascii") + b"\r\n")
    prog = repo / "tools" / "make-manifest.py"

    rc, out = run(prog, tmp_path, "--version", version)
    assert rc == 0, out
    first = version_file.read_bytes()
    assert first.endswith(b"\r\n") and b"\n" not in first.replace(b"\r\n", b""), first
    first_entry = json.loads(manifest_file.read_text(encoding="utf-8"))["files"]["cursor-bridge/VERSION"]

    rc, out = run(prog, tmp_path, "--version", version)
    assert rc == 0, out
    assert version_file.read_bytes() == first
    second_entry = json.loads(manifest_file.read_text(encoding="utf-8"))["files"]["cursor-bridge/VERSION"]
    assert second_entry == first_entry
