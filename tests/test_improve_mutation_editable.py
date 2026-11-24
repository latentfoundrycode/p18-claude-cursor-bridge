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


@pytest.mark.parametrize("value", ["sdk/src", [5], [["sdk/src"]], {"sdk": "src"}, None])
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


# --- written after the builder's round 1, where its own mutation check found two survivors (M2, M8) and the brief's
# --- R8 kept a check no case held ---------------------------------------------------------------------------------

@pytest.mark.parametrize("entry", ["sdk/missing", "sdk/src/pkg/calc.py"])
def test_task085_import_roots_entry_naming_no_folder_refused_in_the_ordinary_mode(tmp_path, entry):
    """The brief's R4 (handoff/TASK-085.md): in the ordinary mode an `import_roots` entry naming a folder the working
    tree does not hold, or naming a file, is refused with exit 2 by a line naming the key and the entry, so that a
    mistyped root is told and never silently ignored."""
    ws = nested_project(tmp_path)
    rc, out = run_mr(ws, mutants(ws, "nf", body(import_roots=[entry])), sys.executable)
    assert rc == 2, out
    assert "import_roots" in out and entry in out, out


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the interpreter's -m puts its folder first, and only Python "
                    "3.11 and later can be told not to (-P)")
def test_task085_mapped_roots_stand_ahead_of_the_copy_root(tmp_path):
    """TASK-085 Done when: every mapped entry "stands on the run's `PYTHONPATH` ahead of the copy's root" (the
    design: "those folders stand first on the run's PYTHONPATH, ahead of the copy's root"): where the copy's root
    also holds a stale `pkg/` of its own, the path entry's folder answers first, so the mutant of sdk/src/pkg/calc.py
    is killed; with the root first the stale package would answer and the mutant survive (exit 1)."""
    ws = nested_project(tmp_path)
    write(ws, "pkg/__init__.py", "")
    write(ws, "pkg/calc.py", CALC)
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "a stale copy at the root")
    python = path_entry_venv(tmp_path, ws, tag="po")
    rc, out = run_mr(ws, mutants(ws, "po", body()), python)
    assert rc == 0, out
    assert "m1: killed" in out, out


def test_task085_dotted_name_under_import_roots_refuses_a_module_resolving_outside(tmp_path):
    """TASK-085 Done when: "the same roots, with `import_roots` where the file names them, serve
    `dotted_module_paths` and the generated plugin, so that a module under `sdk/src/pkg/` is checked as
    `pkg.<module>`": where `pkg.calc` resolves outside the copy (a conftest.py puts an outside folder holding `pkg`
    first), the resolution check refuses it by that name with exit 2, as it refuses any mutated module resolving
    outside; read as `sdk.src.pkg.calc` alone it would pass and the mutant survive (exit 1)."""
    ws = nested_project(tmp_path)
    outside = tmp_path / "outside_pkg"
    (outside / "pkg").mkdir(parents=True)
    (outside / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (outside / "pkg" / "calc.py").write_text(CALC, encoding="utf-8")
    write(ws, "tests/conftest.py", "import sys\nsys.path.insert(0, %r)\n" % str(outside))
    git(ws, "add", "tests/conftest.py")
    git(ws, "commit", "-q", "-m", "an outside package first")
    rc, out = run_mr(ws, mutants(ws, "dn", body(import_roots=["sdk/src"])), sys.executable)
    assert rc == 2, out
    assert "pkg.calc" in out and "resolves outside the copy" in out, out


def test_task085_workspace_entry_ahead_of_the_copy_refused_by_its_own_line(tmp_path):
    """TASK-085, the brief's R8 (the check that raised `module from Workspace path sys.path was loaded` kept under a
    line of its own): a test module that puts the Workspace's own folder first on the import path when it is
    collected, ahead of every entry of the copy, is refused with exit 2 by a line that says the entry stands ahead of
    the copy, and never by the old line. The insert stands in the test module, which pytest collects after its
    configure hook, so no mutated module is resolved through it (Review A, round 1: from an initial conftest.py the
    insert came first and the check of a module resolving outside the copy answered instead)."""
    ws = nested_project(tmp_path)
    write(ws, "tests/test_pkg.py", "import sys\nsys.path.insert(0, %r)\n\n%s" % (str(ws), TEST))
    git(ws, "add", "tests/test_pkg.py")
    git(ws, "commit", "-q", "-m", "the Workspace first")
    rc, out = run_mr(ws, mutants(ws, "wa", body(import_roots=["sdk/src"])), sys.executable)
    assert rc == 2, out
    assert "ahead of the copy" in out, out
    assert "Workspace path sys.path" not in out, out


# --- written after Review A's round 1 -------------------------------------------------------------------------------

def test_task085_mapped_folder_keeps_its_letter_case_for_the_dotted_name(tmp_path):
    """TASK-085 Done when: every entry inside the Workspace "is mapped to the same folder of the copy" and the same
    roots serve the dotted name, so that a module under the mapped folder is checked as `pkg.<module>`; on Windows the
    entry is compared without regard to letter case but the folder keeps the case it has, so a path entry into
    `SDK/Src` still forms `pkg.calc` for SDK/Src/pkg/calc.py, and where `pkg.calc` resolves outside the copy (an
    outside folder holding `pkg` put first by a conftest.py) the run is refused by that name (Review A, round 1: a
    lower-cased folder lost the name, and the mutant survived)."""
    ws = tmp_path / "proj" / "Workspace"
    (ws / "run" / "supervisor" / "mutation-cache").mkdir(parents=True)
    write(ws, "SDK/Src/pkg/__init__.py", "")
    write(ws, "SDK/Src/pkg/calc.py", CALC)
    write(ws, "tests/test_pkg.py", TEST)
    outside = tmp_path / "outside_pkg"
    (outside / "pkg").mkdir(parents=True)
    (outside / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (outside / "pkg" / "calc.py").write_text(CALC, encoding="utf-8")
    write(ws, "tests/conftest.py", "import sys\nsys.path.insert(0, %r)\n" % str(outside))
    git(ws, "init", "-q", "-b", "main")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "init")
    python = path_entry_venv(tmp_path, ws, tag="lc", entry=str(ws / "SDK" / "Src"))
    mutant = dict(MUTANT, file="SDK/Src/pkg/calc.py")
    rc, out = run_mr(ws, mutants(ws, "lc", {"mutants": [mutant]}), python)
    assert rc == 2, out
    assert "pkg.calc" in out and "resolves outside the copy" in out, out


def _link_folder(link, target):
    """A symbolic link to a folder or, on Windows where none can be made, a junction; skips where neither can."""
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
        return
    except (OSError, NotImplementedError) as e:
        if sys.platform != "win32":
            pytest.skip("this account cannot create a symbolic link here (%s)" % e)
    j = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], **_kw(timeout=30))
    if j.returncode != 0:
        pytest.skip("neither a symbolic link nor a junction could be made here (%s)" % j.stderr)


def test_task085_workspace_reached_through_a_link_still_maps_its_entries(tmp_path):
    """TASK-085 Done when: "every entry that resolves inside the Workspace ... is mapped to the same folder of the
    copy": where the program is started in the Workspace through a link (a junction, a symbolic link), an entry that
    names the Workspace's real folder still resolves inside it and is mapped, so the mutant is killed (Review A,
    round 1: the folder was taken relative to the unresolved Workspace path and the entry was dropped). The mutants
    file is named relative to the folder the program starts in: on POSIX the working folder is the link's real folder
    (getcwd resolves a symbolic link), so a path through the link would be refused as outside run/supervisor/ by the
    file's own check, which this increment does not change (CI, PR #205); there the case runs from the real folder,
    and on Windows, where the working folder keeps the junction, it runs through the link."""
    ws = nested_project(tmp_path)
    python = path_entry_venv(tmp_path, ws, tag="lk")
    via = tmp_path / "via"
    _link_folder(via, ws)
    mf = mutants(ws, "lk", body())
    rc, out = run_mr(via, os.path.join("run", "supervisor", mf.name), python)
    assert rc == 0, out
    assert "m1: killed" in out, out


# --- written after the builder's round 2 ----------------------------------------------------------------------------

def test_task085_workspace_entry_with_no_copy_entry_on_the_path_refused(tmp_path):
    """TASK-085, the brief's R8 and round 2's correction 6: an entry of the import path inside the Workspace is
    refused where it stands ahead of every entry of the copy, and also where no entry of the copy stands on the path at
    all: a test module that, after its imports, takes every entry of the copy off the import path and appends the
    Workspace's folder is refused with exit 2 by the line that says the entry stands ahead of the copy (round 2's
    self-check: with that case removed, nothing failed)."""
    ws = nested_project(tmp_path)
    tail = ("\n\nimport os as _os\nimport sys as _sys\n\n"
            "_COPY = _os.path.normcase(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))\n\n\n"
            "def _in_copy(p):\n"
            "    n = _os.path.normcase(_os.path.abspath(p))\n"
            "    return n == _COPY or n.startswith(_COPY + _os.sep)\n\n\n"
            "_sys.path[:] = [p for p in _sys.path if not (p and _in_copy(p))]\n"
            "_sys.path.append(%r)\n" % str(ws))
    write(ws, "tests/test_pkg.py", TEST + tail)
    git(ws, "add", "tests/test_pkg.py")
    git(ws, "commit", "-q", "-m", "the copy off the path, the Workspace on it")
    rc, out = run_mr(ws, mutants(ws, "nc", body(import_roots=["sdk/src"])), sys.executable)
    assert rc == 2, out
    assert "ahead of the copy" in out, out


TOOL_TEST = '''import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def test_tool():
    p = subprocess.run([sys.executable, os.path.join(HERE, os.pardir, "tools", "show.py")], capture_output=True,
                       text=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert p.stdout.strip() == "7", p.stderr
'''


def test_task085_a_script_started_by_a_test_still_imports_its_neighbour(tmp_path):
    """TASK-085, round 1's R12 (no environment variable, no other behaviour change): the run's path order is set for
    the run's own pytest processes, never through the environment that every process a project's test starts
    inherits; so a test that starts a script of the project, which imports a module from its own folder, passes in the
    baseline as it passes outside the run, and the mutant is killed (round 2 set PYTHONSAFEPATH=1 in that
    environment, where a script started by a test no longer finds its neighbour)."""
    ws = nested_project(tmp_path)
    write(ws, "tools/helper.py", "VALUE = 7\n")
    write(ws, "tools/show.py", "import helper\n\nprint(helper.VALUE)\n")
    write(ws, "tests/test_tool.py", TOOL_TEST)
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "a tool and its test")
    mutant = dict(MUTANT, tests=["tests/test_pkg.py", "tests/test_tool.py"])
    rc, out = run_mr(ws, mutants(ws, "sp", {"mutants": [mutant], "import_roots": ["sdk/src"]}), sys.executable)
    assert rc == 0, out
    assert "m1: killed" in out, out


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
