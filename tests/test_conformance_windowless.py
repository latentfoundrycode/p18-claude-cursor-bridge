"""R-039: conformance-check Windowless test suite floor and windowless-default snapshot."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from test_bridge_run_driver import _link_folder

HERE = os.path.dirname(os.path.abspath(__file__))
OUTSIDE_NAME = "outside_r5n8"
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "conformance-check.py")
SNAPSHOT = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "windowless-default.snapshot.md")
CONFTEST = os.path.join(HERE, "conftest.py")
WORKSPACE = os.path.join(HERE, os.pardir)
FIXTURE_NAME = "wlfx_q7k2"
MISSING_ROW = ("  MISSING  Windowless test suite  - copy windowless-default.snapshot.md into "
               "conftest.py (see Cursor-Project-Configuration.md, windowless-default); need "
               "windowless_kwargs, Popen.__init__ and CREATE_NO_WINDOW")
NEITHER_NOTE = ("  NOTE     Windowless test suite  - no pytest configuration, no tests/test_*.py "
                "and no package.json test script were found")
ECHO_NOTE = ("  NOTE     Windowless test suite  - no test runner is configured "
             "(the package.json test script starts with echo)")


def extract_snapshot_block(text):
    blocks = re.findall(r"```python\n(.*?)```", text, re.S)
    assert len(blocks) == 1
    return blocks[0]


def row_for(out, floor="Windowless test suite"):
    return [line for line in out.splitlines() if re.match(r"\s+(OK|MISSING|NOTE)\s+%s" % floor, line)]


def fixture_root(tmp_path):
    root = tmp_path / FIXTURE_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def run_check(tmp_path, root=None):
    root = Path(root or fixture_root(tmp_path))
    (root / "docs").mkdir(parents=True, exist_ok=True)
    p = subprocess.run([sys.executable, PROG, str(root), "--offline"], capture_output=True, text=True, timeout=120)
    combined = p.stdout + p.stderr
    for line in combined.splitlines():
        if line.startswith("conformance-check: "):
            continue
        assert FIXTURE_NAME not in line, line
    return p.returncode, p.stdout, p.stderr


def minimal_conftest():
    return extract_snapshot_block(open(SNAPSHOT, encoding="utf-8").read())


def test_r039_snapshot_matches_conftest():
    """R-039: conftest.py holds the snapshot block verbatim."""
    snap = open(SNAPSHOT, encoding="utf-8").read()
    block = extract_snapshot_block(snap)
    conf = open(CONFTEST, encoding="utf-8").read().replace("\r\n", "\n")
    assert block.replace("\r\n", "\n") in conf


def test_r039_snapshot_block_runs_under_pytest(tmp_path):
    """R-039: the block alone in conftest.py installs the Popen wrapper."""
    proj = tmp_path / "proj"
    (proj / "tests").mkdir(parents=True)
    (proj / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (proj / "tests" / "test_one.py").write_text(
        "import subprocess, sys\n"
        "def test_flag():\n"
        "    assert getattr(subprocess.Popen.__init__, 'windowless_default', False) is (sys.platform == 'win32')\n",
        encoding="utf-8",
    )
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=str(proj),
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr + p.stdout


def test_r039_tools_ignore_snapshot_md():
    """R-039: dump-cli and windowless-check do not read .md files."""
    dump = open(os.path.join(HERE, os.pardir, "tools", "dump-cli.py"), encoding="utf-8").read()
    wl = open(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "windowless-check.py"), encoding="utf-8").read()
    assert "windowless-default.snapshot.md" not in dump
    assert "windowless-default.snapshot.md" not in wl
    assert 'PY_EXT = (".py",)' in wl


def test_r039_ok_tests_conftest(tmp_path):
    """R-039: OK row for tests/conftest.py."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    _, out, err = run_check(tmp_path)
    assert row_for(out + err) == ["  OK       Windowless test suite (tests/conftest.py)"]


def test_r039_ok_root_conftest(tmp_path):
    """R-039: OK when rootdir conftest.py carries the default."""
    root = fixture_root(tmp_path)
    (root / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    _, out, err = run_check(tmp_path)
    assert row_for(out + err) == ["  OK       Windowless test suite (conftest.py)"]


def test_r039_ok_testpaths_checks(tmp_path):
    """R-039: OK through pytest.ini testpaths = checks."""
    root = fixture_root(tmp_path)
    (root / "checks").mkdir(parents=True)
    (root / "checks" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = checks\n", encoding="utf-8")
    _, out, err = run_check(tmp_path)
    assert row_for(out + err) == ["  OK       Windowless test suite (checks/conftest.py)"]


@pytest.mark.parametrize("token", ["windowless_kwargs", "Popen.__init__", "CREATE_NO_WINDOW"])
def test_r039_missing_one_token_removed(tmp_path, token):
    """R-039: removing one snapshot token yields MISSING."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    block = minimal_conftest().replace(token, "")
    assert token not in block
    for other in ("windowless_kwargs", "Popen.__init__", "CREATE_NO_WINDOW"):
        if other != token:
            assert other in block
    (root / "tests" / "conftest.py").write_text(block, encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1
    assert row_for(out + err) == [MISSING_ROW]


@pytest.mark.parametrize("layout", ["pytest.ini", "pyproject", "setup.cfg", "tests_only"])
def test_r039_missing_no_conftest(tmp_path, layout):
    """R-039: MISSING for pytest suite without conftest."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    if layout == "pytest.ini":
        (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    elif layout == "pyproject":
        (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    elif layout == "setup.cfg":
        (root / "setup.cfg").write_text("[tool:pytest]\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1
    assert row_for(out + err) == [MISSING_ROW]


def test_r039_precedence_pytest_ini_wins(tmp_path):
    """R-039: pytest.ini beats pyproject.toml and setup.cfg."""
    root = fixture_root(tmp_path)
    (root / "a").mkdir()
    (root / "a" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = a\n", encoding="utf-8")
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths = ["b"]\n', encoding="utf-8")
    (root / "setup.cfg").write_text("[tool:pytest]\ntestpaths = c\n", encoding="utf-8")
    _, out, err = run_check(tmp_path)
    assert row_for(out + err) == ["  OK       Windowless test suite (a/conftest.py)"]


def test_r039_precedence_pyproject_over_setup(tmp_path):
    """R-039: pyproject.toml beats setup.cfg when no pytest.ini."""
    root = fixture_root(tmp_path)
    (root / "b").mkdir()
    (root / "b" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths = ["b"]\n', encoding="utf-8")
    (root / "setup.cfg").write_text("[tool:pytest]\ntestpaths = c\n", encoding="utf-8")
    _, out, err = run_check(tmp_path)
    assert row_for(out + err) == ["  OK       Windowless test suite (b/conftest.py)"]


def test_r039_precedence_setup_cfg_only_missing(tmp_path):
    """R-039: pyproject testpaths b wins; block only under c is MISSING."""
    root = fixture_root(tmp_path)
    (root / "b").mkdir()
    (root / "c").mkdir()
    (root / "c" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths = ["b"]\n', encoding="utf-8")
    (root / "setup.cfg").write_text("[tool:pytest]\ntestpaths = c\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1
    assert row_for(out + err) == [MISSING_ROW]


def test_r039_tox_ini_ignored(tmp_path):
    """R-039: tox.ini is never read for pytest settings."""
    root = fixture_root(tmp_path)
    (root / "d").mkdir()
    (root / "d" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "tox.ini").write_text("[pytest]\ntestpaths = d\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1
    assert row_for(out + err) == [MISSING_ROW]


def test_r039_no_crash_bom_pytest_ini(tmp_path):
    """R-039: BOM-prefixed pytest.ini still yields OK for checks/."""
    root = fixture_root(tmp_path)
    (root / "checks").mkdir()
    (root / "checks" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pytest.ini").write_bytes(b"\xef\xbb\xbf[pytest]\ntestpaths = checks\n")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == ["  OK       Windowless test suite (checks/conftest.py)"]


def test_r039_no_crash_bad_pytest_ini(tmp_path):
    """R-039: unparsable pytest.ini NOTE then OK on tests/conftest.py."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pytest.ini").write_text("testpaths = checks\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == [
        "  NOTE     Windowless test suite  - pytest.ini could not be parsed; judged as if it held no pytest settings",
        "  OK       Windowless test suite (tests/conftest.py)",
    ]


def test_r039_no_crash_duplicate_setup_cfg(tmp_path):
    """R-039: duplicate testpaths in setup.cfg NOTE then OK."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "setup.cfg").write_text("[tool:pytest]\ntestpaths = a\ntestpaths = b\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == [
        "  NOTE     Windowless test suite  - setup.cfg could not be parsed; judged as if it held no pytest settings",
        "  OK       Windowless test suite (tests/conftest.py)",
    ]


def test_r039_no_crash_setup_cfg_non_utf8_comment(tmp_path):
    """R-039: setup.cfg with bad comment line still reads testpaths."""
    root = fixture_root(tmp_path)
    (root / "checks").mkdir()
    (root / "checks" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "setup.cfg").write_bytes(b"[tool:pytest]\n# \xff\xfe\n testpaths = checks\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == ["  OK       Windowless test suite (checks/conftest.py)"]


def test_r039_no_crash_pyproject_tool_scalar(tmp_path):
    """R-039: tool = 1 in pyproject.toml is ignored without NOTE."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pyproject.toml").write_text("tool = 1\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == ["  OK       Windowless test suite (tests/conftest.py)"]


def test_r039_no_crash_invalid_pyproject_toml(tmp_path):
    """R-039: invalid pyproject.toml NOTE then MISSING."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("not = [toml\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1 and "Traceback" not in err
    assert row_for(out + err) == [
        "  NOTE     Windowless test suite  - pyproject.toml could not be parsed; judged as if it held no pytest settings",
        MISSING_ROW,
    ]


def test_r039_no_crash_package_json_array(tmp_path):
    """R-039: package.json array gives neither-seen NOTE."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text("[]\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == [NEITHER_NOTE]


def test_r039_outside_root_relative_testpaths(tmp_path):
    """R-039: testpaths = ../x drops outside root."""
    root = fixture_root(tmp_path)
    outside = tmp_path / "outside_x"
    outside.mkdir()
    (outside / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = ../outside_x\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1
    assert row_for(out + err) == [MISSING_ROW]


def test_r039_outside_root_absolute_testpaths(tmp_path):
    """R-039: absolute testpaths outside the workspace is dropped."""
    root = fixture_root(tmp_path)
    outside = tmp_path / "outside_abs"
    outside.mkdir()
    (outside / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = %s\n" % str(outside).replace("\\", "/"), encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1
    assert row_for(out + err) == [MISSING_ROW]


@pytest.mark.skipif(sys.platform != "win32", reason="other-drive testpaths only on Windows")
def test_r039_outside_root_other_drive(tmp_path):
    """R-039: testpaths on another drive falls back to tests/."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    drive = "Z:" if "z" not in str(tmp_path).lower()[:1] else "Y:"
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = %s/elsewhere\n" % drive, encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == ["  OK       Windowless test suite (tests/conftest.py)"]


@pytest.mark.parametrize("script,runner", [
    ("vitest run", "vitest"),
    ("jest", "jest"),
    ("playwright test", "playwright"),
    ("node --test tests/", "node --test"),
])
def test_r039_node_runner_note(tmp_path, script, runner):
    """R-039: Node suite NOTE names runner, detached: false and KP-059."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text('{"scripts":{"test":"%s"}}' % script, encoding="utf-8")
    _, out, err = run_check(tmp_path)
    rows = row_for(out + err)
    assert rows == [
        "  NOTE     Windowless test suite  - %s: release B ships no default for this runner "
        "(INVENTORY, Deferred); use detached: false (KP-059)" % runner
    ]


def test_r039_other_runner_mocha_note(tmp_path):
    """R-039: mocha tests names mocha."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text('{"scripts":{"test":"mocha tests"}}', encoding="utf-8")
    _, out, err = run_check(tmp_path)
    assert row_for(out + err) == [
        "  NOTE     Windowless test suite  - mocha: release B ships no default for this runner "
        "(INVENTORY, Deferred); use detached: false (KP-059)"
    ]


def test_r039_other_runner_skips_env_assignments(tmp_path):
    """R-039: TOKEN=abc123 mocha tests names mocha only."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text('{"scripts":{"test":"TOKEN=abc123 mocha tests"}}', encoding="utf-8")
    _, out, err = run_check(tmp_path)
    combined = out + err
    assert "abc123" not in combined
    assert row_for(combined) == [
        "  NOTE     Windowless test suite  - mocha: release B ships no default for this runner "
        "(INVENTORY, Deferred); use detached: false (KP-059)"
    ]


def test_r039_echo_default_script_note(tmp_path):
    """R-039: npm default echo script NOTE."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text(
        '{"scripts":{"test":"echo \\"Error: no test specified\\" && exit 1"}}', encoding="utf-8")
    _, out, err = run_check(tmp_path)
    assert row_for(out + err) == [ECHO_NOTE]


def test_r039_none_seen_note(tmp_path):
    """R-039: empty workspace NOTE."""
    root = fixture_root(tmp_path)
    (root / "docs").mkdir()
    _, out, err = run_check(tmp_path)
    assert row_for(out + err) == [NEITHER_NOTE]


def test_r039_pytest_and_node_both_rows(tmp_path):
    """R-039: pytest OK and Node NOTE together."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "package.json").write_text('{"scripts":{"test":"vitest"}}', encoding="utf-8")
    _, out, err = run_check(tmp_path)
    assert row_for(out + err) == [
        "  OK       Windowless test suite (tests/conftest.py)",
        "  NOTE     Windowless test suite  - vitest: release B ships no default for this runner "
        "(INVENTORY, Deferred); use detached: false (KP-059)",
    ]


def test_r039_bridge_workspace_ok():
    """R-039: this repository's Workspace grades OK."""
    p = subprocess.run([sys.executable, PROG, WORKSPACE, "--offline"], capture_output=True, text=True, timeout=120)
    rows = row_for(p.stdout)
    assert rows == ["  OK       Windowless test suite (tests/conftest.py)"]


def _outside(tmp_path):
    d = tmp_path / OUTSIDE_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_r039_no_crash_nested_pyproject(tmp_path):
    """R-039: deeply nested pyproject.toml RecursionError yields NOTE then MISSING."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("a = " + "[" * 5000 + "]" * 5000, encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == [
        "  NOTE     Windowless test suite  - pyproject.toml could not be parsed; judged as if it held no pytest settings",
        MISSING_ROW,
    ]


def test_r039_no_crash_nested_package_json(tmp_path):
    """R-039: deeply nested package.json RecursionError yields neither-seen NOTE."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == [NEITHER_NOTE]


def test_r039_testpaths_through_link(tmp_path):
    """R-039: testpaths pointing through a link does not read outside conftest."""
    root = fixture_root(tmp_path)
    outside = _outside(tmp_path)
    (outside / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    _link_folder(root / "checks", outside)
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = checks\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1 and "Traceback" not in err
    assert row_for(out + err) == [MISSING_ROW]
    assert OUTSIDE_NAME not in out + err


def test_r039_tests_link_with_config(tmp_path):
    """R-039: linked tests/ with pytest.ini yields MISSING, not outside OK."""
    root = fixture_root(tmp_path)
    outside = _outside(tmp_path)
    (outside / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (outside / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    _link_folder(root / "tests", outside)
    (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1 and "Traceback" not in err
    assert row_for(out + err) == [MISSING_ROW]
    assert OUTSIDE_NAME not in out + err


def test_r039_tests_link_no_config(tmp_path):
    """R-039: linked tests/ without config yields neither-seen NOTE."""
    root = fixture_root(tmp_path)
    outside = _outside(tmp_path)
    (outside / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (outside / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    _link_folder(root / "tests", outside)
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == [NEITHER_NOTE]
    assert OUTSIDE_NAME not in out + err


def test_r039_root_conftest_symlink(tmp_path):
    """R-039: root conftest.py symlink to outside is ignored for OK."""
    root = fixture_root(tmp_path)
    outside = _outside(tmp_path)
    (outside / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    try:
        os.symlink(outside / "conftest.py", root / "conftest.py")
    except OSError:
        pytest.skip("creating a file symbolic link needs a privilege here")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1 and "Traceback" not in err
    assert row_for(out + err) == [MISSING_ROW]
    assert OUTSIDE_NAME not in out + err


def test_r039_testpaths_dotdot_component_dropped(tmp_path):
    """R-039 (the supervisor's, TASK-028 round 3's reviews): a testpaths entry holding a `..`
    component is dropped, as the driver's rule 1(c) refuses one, so the default tests/ decides:
    `a/../b` with b/conftest.py holding the default is not OK when tests/ has no conftest.py."""
    root = fixture_root(tmp_path)
    (root / "a").mkdir()
    (root / "b").mkdir()
    (root / "b" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = a/../b\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1 and "Traceback" not in err
    assert row_for(out + err) == [MISSING_ROW]


@pytest.mark.skipif(sys.platform == "win32", reason="Windows collapses `..` before it follows a link")
def test_r039_testpaths_link_then_dotdot_posix(tmp_path):
    """R-039 (the supervisor's, TASK-028 round 3's reviews): on POSIX the kernel follows a link before
    it applies `..`, so `lnk/../tests` with lnk a link to outside/a would read outside/tests/conftest.py;
    the entry is dropped and the outside file is never the reason for OK."""
    root = fixture_root(tmp_path)
    outside = _outside(tmp_path)
    (outside / "a").mkdir()
    (outside / "tests").mkdir()
    (outside / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    _link_folder(root / "lnk", outside / "a")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = lnk/../tests\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1 and "Traceback" not in err
    assert row_for(out + err) == [MISSING_ROW]
    assert OUTSIDE_NAME not in out + err


def test_r039_linked_testpaths_entry_falls_back_to_tests(tmp_path):
    """R-039 (the supervisor's, Review A round 3, H4): a testpaths entry reached through a link is
    dropped like an outside entry, and with no entry left the default tests/ decides (9(b))."""
    root = fixture_root(tmp_path)
    outside = _outside(tmp_path)
    _link_folder(root / "checks", outside)
    (root / "tests").mkdir()
    (root / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = checks\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == ["  OK       Windowless test suite (tests/conftest.py)"]
    assert OUTSIDE_NAME not in out + err


def test_r039_testpaths_glob_literal(tmp_path):
    """R-039: testpaths = tests/* is literal, not expanded."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "a").mkdir(parents=True)
    (root / "tests" / "a" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = tests/*\n", encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1 and "Traceback" not in err
    assert row_for(out + err) == [MISSING_ROW]


@pytest.mark.parametrize("script,word,forbidden", [
    (r"C:\Users\usr_q8w3\AppData\Roaming\npm\mocha.cmd tests", "mocha.cmd", "usr_q8w3"),
    ("/home/usr_q8w3/bin/mocha tests", "mocha", "usr_q8w3"),
])
def test_r039_other_runner_path_basename(tmp_path, script, word, forbidden):
    """R-039: path-like script words reduce to basename for the NOTE."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text('{"scripts":{"test":%s}}' % json.dumps(script), encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    combined = out + err
    assert forbidden not in combined
    assert row_for(combined) == [
        "  NOTE     Windowless test suite  - %s: release B ships no default for this runner "
        "(INVENTORY, Deferred); use detached: false (KP-059)" % word
    ]


def test_r039_other_runner_escape_control_chars(tmp_path):
    """R-039: control characters in runner word are escape_field literals."""
    root = fixture_root(tmp_path)
    script = "\u001b]0;pwned\u0007mocha tests"
    (root / "package.json").write_text('{"scripts":{"test":%s}}' % json.dumps(script), encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    combined = out + err
    assert "\x1b" not in combined and "\x07" not in combined
    assert row_for(combined) == [
        "  NOTE     Windowless test suite  - \\x1b]0;pwned\\x07mocha: release B ships no default for this runner "
        "(INVENTORY, Deferred); use detached: false (KP-059)"
    ]


def test_r039_other_runner_dash_option(tmp_path):
    """R-039: --token=abc123 mocha tests names mocha."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text('{"scripts":{"test":"--token=abc123 mocha tests"}}', encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    combined = out + err
    assert "abc123" not in combined
    assert row_for(combined) == [
        "  NOTE     Windowless test suite  - mocha: release B ships no default for this runner "
        "(INVENTORY, Deferred); use detached: false (KP-059)"
    ]


def test_r039_other_runner_quoted_assignment(tmp_path):
    """R-039: TOKEN=quoted mocha uses shlex grouping."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text('{"scripts":{"test":"TOKEN=\\"abc4x def7z\\" mocha tests"}}', encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    combined = out + err
    assert "abc4x" not in combined and "def7z" not in combined
    assert row_for(combined) == [
        "  NOTE     Windowless test suite  - mocha: release B ships no default for this runner "
        "(INVENTORY, Deferred); use detached: false (KP-059)"
    ]


def test_r039_other_runner_unclosed_quote(tmp_path):
    """R-039: unclosed quote falls back to str.split."""
    root = fixture_root(tmp_path)
    (root / "package.json").write_text('{"scripts":{"test":"TOKEN=\\"q1w2 mocha tests"}}', encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    combined = out + err
    assert "q1w2" not in combined
    assert row_for(combined) == [
        "  NOTE     Windowless test suite  - mocha: release B ships no default for this runner "
        "(INVENTORY, Deferred); use detached: false (KP-059)"
    ]


# --- the supervisor's tests for round 5 (TASK-028 round 4's reviews; handoff/TASK-028-r5.md)

def _floor_rows_in_process(program, monkeypatch, capsys, root):
    """Run the Workspace's conformance-check.main() in this process on a fixture; return (rc, rows, out)."""
    mod = program("conformance-check")
    (Path(root) / "docs").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sys, "argv", ["conformance-check.py", str(root), "--offline"])
    rc = mod.main()
    out = capsys.readouterr().out
    for line in out.splitlines():
        if not line.startswith("conformance-check: "):
            assert FIXTURE_NAME not in line, line
    return mod, rc, row_for(out), out


def test_r039_nul_in_testpaths_dropped(tmp_path):
    """R-039 (the supervisor's, TASK-028 round 4's reviews, both): 9(c), no input makes the check print a
    traceback: a testpaths entry holding a NUL counts as a link and is dropped, so tests/ decides."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "pytest.ini").write_bytes(b"[pytest]\ntestpaths = a\x00b\n")
    rc, out, err = run_check(tmp_path)
    assert rc < 2 and "Traceback" not in err
    assert row_for(out + err) == [MISSING_ROW]


def test_r039_unlistable_tests_folder_is_no_suite(program, monkeypatch, capsys, tmp_path):
    """R-039 (the supervisor's, Review A round 4): 9(c) and 9(b2): a tests/ that cannot be listed shows
    no test_*.py, never a traceback; with no configuration the neither-seen row stands."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    real_listdir = os.listdir
    tests_dir = os.path.normcase(os.path.abspath(str(root / "tests")))

    def listdir(path="."):
        if os.path.normcase(os.path.abspath(str(path))) == tests_dir:
            raise PermissionError(13, "Access is denied", str(path))
        return real_listdir(path)

    monkeypatch.setattr(os, "listdir", listdir)
    mod, rc, rows, out = _floor_rows_in_process(program, monkeypatch, capsys, root)
    assert rc < 2
    assert rows == [NEITHER_NOTE]


def test_r039_ok_row_path_is_escaped(tmp_path):
    """R-039 (the supervisor's, Review A round 4): requirement 9, the floor prints no control
    character: the OK row's path is rendered by escape_field, so U+202E reaches no output line."""
    root = fixture_root(tmp_path)
    folder = "t" + chr(0x202E) + "x"
    try:
        (root / folder).mkdir()
    except OSError:
        pytest.skip("this file system refuses U+202E in a folder name")
    (root / folder / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths = ["t\\u202ex"]\n', encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")      # a UTF-8 console, where no encoding error escapes it by chance
    p = subprocess.run([sys.executable, PROG, str(root), "--offline"], capture_output=True, timeout=120, env=env)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    assert p.returncode < 2 and "Traceback" not in out
    assert chr(0x202E) not in out
    assert row_for(out) == ["  OK       Windowless test suite (t\\u202ex/conftest.py)"]


def test_r039_floor_backstop_turns_an_error_into_one_note(program, monkeypatch, capsys, tmp_path):
    """R-039 (the supervisor, closing the input-robustness tail of rounds 2 to 4): 9(c), no input makes the
    check print a traceback: an unexpected exception anywhere in the floor gives exactly one NOTE naming the
    exception's class and nothing of its message, and the check's other floors still run."""
    root = fixture_root(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    mod = program("conformance-check")

    def boom(ws):
        raise RuntimeError("secret_zz91 " + str(ws))

    monkeypatch.setattr(mod, "_pytest_test_roots", boom)
    monkeypatch.setattr(sys, "argv", ["conformance-check.py", str(root), "--offline"])
    (root / "docs").mkdir(exist_ok=True)
    rc = mod.main()
    out = capsys.readouterr().out
    assert rc < 2
    assert "secret_zz91" not in out
    assert row_for(out) == ["  NOTE     Windowless test suite  - the floor could not be judged (RuntimeError)"]
    assert re.search(r"^\s+(OK|MISSING|NOTE)\s+Lockfile|^\s+(OK|MISSING|NOTE)\s+Records|^conformance-check: \d+ OK", out, re.M)


@pytest.mark.parametrize("entry", ["a\\..\\b", "a/..\\b", "ABS"])
def test_r039_dotdot_entry_spellings_dropped(tmp_path, entry):
    """R-039 (the supervisor's, Review A round 4, H1): round 4's 9(b) rule splits on `/` and `\\` and
    applies to an absolute entry too: each spelling of `a/../b` is dropped, so tests/ decides."""
    root = fixture_root(tmp_path)
    (root / "a").mkdir()
    (root / "b").mkdir()
    (root / "b" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    value = (str(root) + "/a/../b") if entry == "ABS" else entry
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = %s\n" % value, encoding="utf-8")
    rc, out, err = run_check(tmp_path)
    assert rc == 1 and "Traceback" not in err
    assert row_for(out + err) == [MISSING_ROW]
