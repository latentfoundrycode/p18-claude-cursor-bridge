"""TASK-085 (R-106; docs/DESIGN.md, "Change: the improvements release", C27): the mutation engine on an editable
install. The supervisor's acceptance tests, written before the brief and committed before the checkpoint. Each scratch
project is built as tests/test_mutation_run.py builds R-041's: a git repository under a temporary folder, a virtual
environment made with `--without-pip --system-site-packages` (so pytest is the running one's), no package installed
and no network. An editable install is imitated by what it leaves in the environment: a `.pth` path entry that points
into the Workspace, or a `.pth` that installs a finder appended to `sys.meta_path`, as setuptools' editable finder is.

enforces: docs/BUILD_PLAN.md, TASK-085, Done when; docs/REQUIREMENTS.md R-106
"""
import json
import os
import subprocess
import sys

import pytest

import conftest as test_conftest

HERE = os.path.dirname(os.path.abspath(__file__))
MUTATION_RUN = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "mutation-run.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
       "-c", "commit.gpgsign=false"]

CALC = "def add(a, b):\n    return a + b\n"
TEST = "from pkg.calc import add\n\n\ndef test_add():\n    assert add(1, 1) == 2\n"
MUTANT = {
    "id": "m1", "file": "sdk/src/pkg/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
    "tests": ["tests/test_pkg.py"], "expect_fail": ["tests/test_pkg.py::test_add"],
}

FINDER = '''import importlib.machinery
import sys

ROOT = %r


class _EditableFinder:
    """Answers for the top-level package `pkg` from a folder that is on no path entry, as an editable install's
    finder does; appended to sys.meta_path, so the path finder is asked first."""

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if fullname != "pkg":
            return None
        return importlib.machinery.PathFinder.find_spec(fullname, [ROOT])


def install():
    if _EditableFinder not in sys.meta_path:
        sys.meta_path.append(_EditableFinder)
'''


def _kw(**extra):
    base = {"capture_output": True, "text": True, "timeout": 60}
    base.update(extra)
    return test_conftest.windowless_kwargs(base)


def git(ws, *args):
    p = subprocess.run(GIT + list(args), cwd=str(ws), **_kw())
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def write(ws, rel, text):
    path = ws / rel.replace("/", os.sep)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def nested_project(tmp_path, project="proj"):
    """A Workspace whose package lies under sdk/src/pkg/, imported as `pkg`, with no configuration that puts
    sdk/src on the path: only the environment can make it importable."""
    ws = tmp_path / project / "Workspace"
    (ws / "run" / "supervisor" / "mutation-cache").mkdir(parents=True)
    write(ws, "sdk/src/pkg/__init__.py", "")
    write(ws, "sdk/src/pkg/calc.py", CALC)
    write(ws, "tests/test_pkg.py", TEST)
    write(ws, "tests/conftest.py", "")
    git(ws, "init", "-q", "-b", "main")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "init")
    return ws


def venv(tmp_path, tag, pth_lines, extra_files=None):
    """A virtual environment that sees the running one's packages, with one `.pth` file holding `pth_lines` and any
    extra modules beside it in its site-packages folder; returns its interpreter."""
    root = tmp_path / ("venv-" + tag)
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", "--system-site-packages", str(root)],
                   check=True, **_kw(timeout=120))
    if sys.platform == "win32":
        python = root / "Scripts" / "python.exe"
        site = root / "Lib" / "site-packages"
    else:
        python = root / "bin" / "python"
        site = root / "lib" / ("python%d.%d" % sys.version_info[:2]) / "site-packages"
    site.mkdir(parents=True, exist_ok=True)
    (site / ("editable_%s.pth" % tag)).write_text("\n".join(pth_lines) + "\n", encoding="utf-8")
    for name, text in (extra_files or {}).items():
        (site / name).write_text(text, encoding="utf-8")
    return python


def path_entry_venv(tmp_path, ws, tag="pe", entry=None):
    """An editable install that leaves a path entry pointing into the Workspace at sdk/src."""
    return venv(tmp_path, tag, [entry or str(ws / "sdk" / "src")])


def finder_venv(tmp_path, ws, tag="fi"):
    """An editable install that answers through a finder alone and leaves no path entry."""
    return venv(tmp_path, tag, ["import _editable_finder_%s; _editable_finder_%s.install()" % (tag, tag)],
                {"_editable_finder_%s.py" % tag: FINDER % str(ws / "sdk" / "src")})


def mutants(ws, run_id, body):
    rel = "run/supervisor/%s-mutants.json" % run_id
    (ws / rel.replace("/", os.sep)).write_text(json.dumps(body, indent=2), encoding="utf-8")
    git(ws, "add", rel)
    return ws / rel.replace("/", os.sep)


def run_mr(ws, mutants_file, python, extra=(), timeout=120):
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(str(python)) + os.pathsep + env.get("PATH", "")
    cmd = [str(python), MUTATION_RUN, str(mutants_file)] + list(extra) + ["--mutant-timeout", str(timeout)]
    p = subprocess.run(cmd, cwd=str(ws), env=env, **_kw(timeout=timeout + 90))
    return p.returncode, p.stdout + p.stderr


def body(**top):
    b = {"mutants": [dict(MUTANT)]}
    b.update(top)
    return b


# --- the path entry into the Workspace -------------------------------------------------------------------------------

def test_task085_path_entry_under_nested_source_folder_kills_the_mutant(tmp_path):
    """TASK-085 Done when: "a scratch project whose package is importable only through a path entry into the
    Workspace has its mutant killed (red on the checkpoint, where the run ends with exit 2)"; the entry that resolves
    inside the Workspace is mapped to the same folder of the copy, ahead of the copy's root, and the same root serves
    the dotted module name, so sdk/src/pkg/calc.py is checked as pkg.calc; and the line `module from Workspace path
    sys.path was loaded` no longer appears for the path itself."""
    ws = nested_project(tmp_path)
    python = path_entry_venv(tmp_path, ws)
    rc, out = run_mr(ws, mutants(ws, "pe", body()), python)
    assert rc == 0, out
    assert "m1: killed" in out, out
    assert "Workspace path sys.path" not in out, out


@pytest.mark.skipif(sys.platform != "win32", reason="letter case is ignored by the file system on Windows alone")
def test_task085_path_entry_compared_without_regard_to_letter_case_on_windows(tmp_path):
    """TASK-085 Done when: "every entry that resolves inside the Workspace, compared without regard to letter case on
    Windows, is mapped to the same folder of the copy": an entry written in upper case is still the Workspace's."""
    ws = nested_project(tmp_path)
    python = path_entry_venv(tmp_path, ws, tag="pu", entry=str(ws / "sdk" / "src").upper())
    rc, out = run_mr(ws, mutants(ws, "pu", body()), python)
    assert rc == 0, out
    assert "m1: killed" in out, out


# --- the finder that leaves no path entry ----------------------------------------------------------------------------

def test_task085_finder_only_refused_with_the_cause_and_the_key_named(tmp_path):
    """TASK-085 Done when: "one reached through a finder alone is refused with exit 2 by a line that names the module,
    the place it was loaded from, an editable install as the usual cause and the `import_roots` key"; nothing is
    cached for a refused run."""
    ws = nested_project(tmp_path)
    python = finder_venv(tmp_path, ws)
    rc, out = run_mr(ws, mutants(ws, "fi", body()), python)
    assert rc == 2, out
    assert "editable install" in out, out
    assert "import_roots" in out, out
    assert "pkg" in out and "sdk" in out, out
    assert not (ws / "run" / "supervisor" / "mutation-cache" / "fi.jsonl").exists()


def test_task085_finder_only_runs_once_import_roots_names_its_root(tmp_path):
    """TASK-085 Done when: the finder-only project "runs once the key names its root": `import_roots` puts the copy's
    sdk/src ahead on the run's path, so the path finder answers from the copy before the editable finder does, and
    the root serves the dotted module name."""
    ws = nested_project(tmp_path)
    python = finder_venv(tmp_path, ws, tag="fk")
    rc, out = run_mr(ws, mutants(ws, "fk", body(import_roots=["sdk/src"])), python)
    assert rc == 0, out
    assert "m1: killed" in out, out


# --- the import_roots key's refusals ---------------------------------------------------------------------------------

def test_task085_import_roots_absolute_entry_refused(tmp_path):
    """TASK-085 Done when: "`import_roots` is a list of strings, each a folder relative to the Workspace root, refused
    with exit 2 where an entry is absolute"."""
    ws = nested_project(tmp_path)
    rc, out = run_mr(ws, mutants(ws, "ra", body(import_roots=[str(ws / "sdk" / "src")])), sys.executable)
    assert rc == 2, out
    assert "import_roots" in out and "absolute" in out.lower(), out


@pytest.mark.parametrize("entry", ["..", "../elsewhere", "sdk/../.."])
def test_task085_import_roots_entry_leaving_the_workspace_refused(tmp_path, entry):
    """TASK-085 Done when: `import_roots` "refused with exit 2 where an entry ... leaves the Workspace"."""
    ws = nested_project(tmp_path)
    rc, out = run_mr(ws, mutants(ws, "rl", body(import_roots=[entry])), sys.executable)
    assert rc == 2, out
    assert "import_roots" in out and ("outside" in out.lower() or "leaves" in out.lower()), out


def test_task085_import_roots_entry_through_a_link_refused(tmp_path):
    """TASK-085 Done when: `import_roots` "refused with exit 2 where an entry ... passes through a link": a folder of
    the Workspace that is a symbolic link or, where none can be made, a junction."""
    ws = nested_project(tmp_path)
    target = tmp_path / "elsewhere"
    target.mkdir()
    link = ws / "linked"
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
    except (OSError, NotImplementedError) as e:
        if sys.platform != "win32":
            pytest.skip("this account cannot create a symbolic link here (%s)" % e)
        j = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], **_kw(timeout=30))
        if j.returncode != 0:
            pytest.skip("neither a symbolic link nor a junction could be made here (%s)" % j.stderr)
    rc, out = run_mr(ws, mutants(ws, "rk", body(import_roots=["linked"])), sys.executable)
    assert rc == 2, out
    assert "import_roots" in out and "link" in out.lower(), out


@pytest.mark.parametrize("value", ["sdk/src", [5], [["sdk/src"]], {"sdk": "src"}])
def test_task085_import_roots_must_be_a_list_of_strings(tmp_path, value):
    """TASK-085 Done when: "`import_roots` is a list of strings": a bare string, a number, a nested list or an object
    is refused with exit 2, the line naming the key and what it must be."""
    ws = nested_project(tmp_path)
    rc, out = run_mr(ws, mutants(ws, "rt", body(import_roots=value)), sys.executable)
    assert rc == 2, out
    assert "import_roots" in out and ("list" in out.lower() or "string" in out.lower()), out
    assert "unknown field" not in out, out


def test_task085_import_roots_is_part_of_the_cache_key(tmp_path):
    """TASK-085 Done when: `import_roots` "is part of the cache key": a kept kill is served from the cache while the
    key is unchanged and run again once `import_roots` changes."""
    ws = nested_project(tmp_path)
    python = finder_venv(tmp_path, ws, tag="ck")
    first = mutants(ws, "ck", body(import_roots=["sdk/src"]))
    rc, out = run_mr(ws, first, python)
    assert rc == 0 and "m1: killed" in out, out
    rc, out = run_mr(ws, first, python)
    assert rc == 0 and "m1: killed (cached" in out, out
    changed = mutants(ws, "ck", body(import_roots=["sdk/src", "tests"]))
    rc, out = run_mr(ws, changed, python)
    assert rc == 0 and "m1: killed" in out, out
    assert "m1: killed (cached" not in out, out


# --- the checkpoint mode --------------------------------------------------------------------------------------------

def test_task085_checkpoint_reads_the_path_entry_roots(tmp_path):
    """TASK-085 Done when: "`--checkpoint` reads the roots the same way where the folder exists at the commit": the
    path-entry project's new test, already passing on the commit's code, is judged there (exit 4, the test listed as
    passing on old code) instead of being refused for a module loaded from the Workspace (exit 2 on the checkpoint)."""
    ws = nested_project(tmp_path)
    python = path_entry_venv(tmp_path, ws, tag="cp")
    sha = git(ws, "rev-parse", "HEAD")
    mf = mutants(ws, "cp", {"mutants": [], "new_tests": ["tests/test_pkg.py::test_add"]})
    rc, out = run_mr(ws, mf, python, extra=["--checkpoint", sha])
    assert rc == 4, out
    assert "passing on old code" in out, out


def test_task085_checkpoint_skips_an_import_root_absent_at_the_commit(tmp_path):
    """TASK-085 Done when: `--checkpoint` "skips one that does not" exist at the commit: a root named in
    `import_roots` that the working tree holds and the commit lacks neither refuses the run nor stops the judgement."""
    ws = nested_project(tmp_path)
    python = finder_venv(tmp_path, ws, tag="cs")
    sha = git(ws, "rev-parse", "HEAD")
    write(ws, "lib/later/__init__.py", "")
    git(ws, "add", "lib/later/__init__.py")
    git(ws, "commit", "-q", "-m", "a later folder")
    mf = mutants(ws, "cs", {"mutants": [], "new_tests": ["tests/test_pkg.py::test_add"],
                            "import_roots": ["sdk/src", "lib/later"]})
    rc, out = run_mr(ws, mf, python, extra=["--checkpoint", sha])
    assert rc == 4, out
    assert "passing on old code" in out, out
