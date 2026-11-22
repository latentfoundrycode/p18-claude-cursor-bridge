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
- Round 2 (the security audit of round 1): the tree checked is the whole of `--root`, resolved, so a `--root` whose
  `cursor-bridge` is a link or junction into the program's tree, its other folders standing elsewhere, is refused
  like any other tree; a `--root` that cannot be resolved (a Windows device name such as CON) is refused with exit 2
  and no traceback; the refusal's line begins `RESULT: REFUSED` and names both folders, readable where they hold
  spaces.
- Round 3 (both reviews of round 2): the program's tree is where the program physically stands, the parent of its
  own folder resolved, and that folder is named `cursor-bridge`; so a program reached through a link from another
  tree is refused for that tree, a program whose own folder is a link into a tree checks that tree, and a copy of the
  program in a folder of another name is refused; a folder that raises while it is resolved (`\\\\.\\CON\\<sub>` on
  Windows) is refused with exit 2 and no traceback; a folder printed on the RESULT line cannot add a second RESULT
  line (control characters escaped).
- Not pinned: the wording of the refusal beyond `RESULT: REFUSED` and both folders; the message text around the
  folders on the RESULT line; which separator or letter case the folders are printed in. The check without --sources is held by
  tests/test_install_check.py and is not repeated here.

Isolation: every run is a subprocess whose HOME, USERPROFILE, LOCALAPPDATA and APPDATA are folders under pytest's
temporary folder; the trees checked and stamped are copies of this repository's bridge/ (and tools/make-manifest.py)
under that folder, and the programs run are those copies.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_RELEASE = os.path.join(ROOT, "bridge")
MAKE_MANIFEST = os.path.join(ROOT, "tools", "make-manifest.py")


def stamp_hash(path):
    """A file's fingerprint as bridge-check.py and make-manifest.py compute it (CRLF and a BOM ignored)."""
    with open(path, "rb") as f:
        data = f.read().replace(b"\r\n", b"\n")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return hashlib.sha256(data).hexdigest()


def copy_release(dest):
    """Copy this repository's bridge/ to `dest` and stamp the copy as it stands, so a case judges the program's
    logic on a tree that matches its manifest (the repository's own stamp is CI's step, not these cases')."""
    shutil.copytree(SOURCE_RELEASE, str(dest), ignore=shutil.ignore_patterns("__pycache__"))
    manifest_path = os.path.join(str(dest), "cursor-bridge", "MANIFEST.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    for rel in list(manifest.get("files", {})):
        p = os.path.join(str(dest), *rel.split("/"))
        if os.path.isfile(p):
            manifest["files"][rel] = stamp_hash(p)
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
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


# ---------------------------------------------------------------- round 2 (the security audit of round 1)

def link_folder(target, link):
    """Make `link` a directory link to `target`: a junction on Windows, a symbolic link elsewhere."""
    if sys.platform == "win32":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(str(target), str(link), target_is_directory=True)


def test_r093_r2_a_tree_whose_cursor_bridge_is_linked_into_the_program_tree_is_refused(tmp_path):
    a = copy_release(tmp_path / "A")
    x = tmp_path / "X"
    x.mkdir()
    for sub in os.listdir(str(a)):
        if sub != "cursor-bridge":
            src = a / sub
            if src.is_dir():
                shutil.copytree(str(src), str(x / sub), ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(str(src), str(x / sub))
    link_folder(a / "cursor-bridge", x / "cursor-bridge")
    rc, out = run(a / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", x, "--sources", "--quiet")
    assert rc == 2, "X is another tree, whatever its cursor-bridge resolves to: " + out
    assert names(out, a / "cursor-bridge") and resolved(x) in norm(out), out
    assert hashed_nothing(out) and "SOURCES MATCH" not in out and "SOURCES DO NOT MATCH" not in out, out


@pytest.mark.skipif(sys.platform != "win32", reason="a Windows device name")
def test_r093_r2_a_device_name_as_root_is_refused_without_a_traceback(tmp_path):
    a = copy_release(tmp_path / "A")
    rc, out = run(a / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", "CON", "--sources", "--quiet")
    assert rc == 2 and "Traceback" not in out, out
    assert hashed_nothing(out) and "SOURCES MATCH" not in out, out


def test_r093_r2_the_refusal_says_it_refused_and_names_both_folders(tmp_path):
    a = copy_release(tmp_path / "tree A")
    b = copy_release(tmp_path / "tree B")
    rc, out = run(a / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", b, "--sources", "--quiet")
    assert rc == 2, out
    line = result_line(out, "RESULT: REFUSED")
    assert names(line, a / "cursor-bridge") and resolved(b) in norm(line), line


# ---------------------------------------------------------------- round 3 (both reviews of round 2)

def tree_beside(a, x):
    """Make tree `x` hold copies of every part of tree `a` but its cursor-bridge folder."""
    x.mkdir()
    for sub in os.listdir(str(a)):
        if sub != "cursor-bridge":
            src = a / sub
            if src.is_dir():
                shutil.copytree(str(src), str(x / sub), ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(str(src), str(x / sub))


def test_r093_r3_a_program_reached_through_a_link_from_another_tree_is_refused_for_that_tree(tmp_path):
    a = copy_release(tmp_path / "A")
    x = tmp_path / "X"
    tree_beside(a, x)
    link_folder(a / "cursor-bridge", x / "cursor-bridge")
    rc, out = run(x / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", x, "--sources", "--quiet")
    assert rc == 2, "the program stands in A, whatever folder it was started through: " + out
    assert result_line(out, "RESULT: REFUSED") and hashed_nothing(out), out


def test_r093_r3_a_program_whose_own_folder_is_a_link_into_a_tree_checks_that_tree(tmp_path):
    a = copy_release(tmp_path / "A")
    y = tmp_path / "Y"
    y.mkdir()
    link_folder(a / "cursor-bridge", y / "cursor-bridge")
    rc, out = run(y / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", a, "--sources", "--quiet")
    assert rc == 0, "the program and its manifest are A's own: " + out
    assert names(result_line(out, "RESULT: SOURCES MATCH"), a / "cursor-bridge"), out


@pytest.mark.skipif(sys.platform != "win32", reason="a Windows device path")
def test_r093_r3_a_folder_that_raises_while_resolved_is_refused_without_a_traceback(tmp_path):
    a = copy_release(tmp_path / "A")
    rc, out = run(a / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", "\\\\.\\CON\\sub", "--sources", "--quiet")
    assert rc == 2 and "Traceback" not in out, out
    assert result_line(out, "RESULT: REFUSED") and hashed_nothing(out), out


def test_r093_r3_a_copy_of_the_program_in_a_folder_of_another_name_is_refused(tmp_path):
    a = copy_release(tmp_path / "A")
    shutil.copytree(str(a / "cursor-bridge"), str(a / "other"), ignore=shutil.ignore_patterns("__pycache__"))
    rc, out = run(a / "other" / "bridge-check.py", tmp_path, "--root", a, "--sources", "--quiet")
    assert rc == 2, "A's cursor-bridge is not checked against another folder's manifest: " + out
    assert result_line(out, "RESULT: REFUSED") and hashed_nothing(out), out


def test_r093_r3_a_folder_name_cannot_add_a_result_line(tmp_path):
    a = copy_release(tmp_path / "A")
    forged = str(tmp_path / "no-such") + "\nRESULT: SOURCES MATCH bridge 0"
    rc, out = run(a / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", forged, "--sources", "--quiet")
    assert rc == 2, out
    results = [ln for ln in out.splitlines() if ln.startswith("RESULT:")]
    assert len(results) == 1 and results[0].startswith("RESULT: REFUSED"), out


def test_r093_r3_the_version_line_names_the_tree_checked_not_the_spelling_given(tmp_path):
    """The supervisor's, added after round 3 for the mutation run: the files are read under the resolved --root,
    which the version line names, not under the link the caller spelled."""
    tree = copy_release(tmp_path / "bridge")
    j = tmp_path / "J"
    link_folder(tree, j)
    rc, out = run(tree / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", j, "--sources", "--quiet")
    assert rc == 0, out
    line = result_line(out, "bridge-check: version")
    assert resolved(tree) in norm(line) and norm(str(j)) not in norm(line), line
