"""R-039: conformance-check Windowless test suite floor and windowless-default snapshot."""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "conformance-check.py")
SNAPSHOT = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "windowless-default.snapshot.md")
CONFTEST = os.path.join(HERE, "conftest.py")
WINDOWLESS_BLOCK = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "windowless-default.snapshot.md")
WORKSPACE = os.path.join(HERE, os.pardir)


def extract_snapshot_block(text):
    blocks = re.findall(r"```python\n(.*?)```", text, re.S)
    assert len(blocks) == 1
    return blocks[0]


def row_for(out, floor="Windowless test suite"):
    return [line for line in out.splitlines() if re.match(r"\s+(OK|MISSING|NOTE)\s+%s" % floor, line)]


def run_check(root):
    root = Path(root)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    p = subprocess.run([sys.executable, PROG, str(root), "--offline"], capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout


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
    root = tmp_path / "ws"
    root.mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    _, out = run_check(root)
    assert row_for(out) == ["  OK       Windowless test suite (tests/conftest.py)"]


def test_r039_ok_root_conftest(tmp_path):
    """R-039: OK when rootdir conftest.py carries the default."""
    root = tmp_path / "ws"
    root.mkdir()
    (root / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    _, out = run_check(root)
    assert row_for(out) == ["  OK       Windowless test suite (conftest.py)"]


def test_r039_ok_testpaths_checks(tmp_path):
    """R-039: OK through pytest.ini testpaths = checks."""
    root = tmp_path / "ws"
    root.mkdir()
    (root / "checks").mkdir()
    (root / "checks" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = checks\n", encoding="utf-8")
    _, out = run_check(root)
    assert row_for(out) == ["  OK       Windowless test suite (checks/conftest.py)"]


def test_r039_missing_bad_conftest(tmp_path):
    """R-039: MISSING when conftest lacks a token."""
    root = tmp_path / "ws"
    root.mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text("# empty\n", encoding="utf-8")
    rc, out = run_check(root)
    assert rc == 1
    rows = row_for(out)
    assert len(rows) == 1 and rows[0].startswith("  MISSING  Windowless test suite")
    assert "windowless-default.snapshot.md" in rows[0] and "Cursor-Project-Configuration.md" in rows[0]
    assert "windowless_kwargs" in rows[0]


@pytest.mark.parametrize("layout", ["pytest.ini", "pyproject", "setup.cfg", "tests_only"])
def test_r039_missing_no_conftest(tmp_path, layout):
    """R-039: MISSING for pytest suite without conftest."""
    root = tmp_path / "ws"
    root.mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    if layout == "pytest.ini":
        (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    elif layout == "pyproject":
        (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\n', encoding="utf-8")
    elif layout == "setup.cfg":
        (root / "setup.cfg").write_text("[tool:pytest]\n", encoding="utf-8")
    rc, out = run_check(root)
    assert rc == 1
    rows = row_for(out)
    assert len(rows) == 1 and rows[0].startswith("  MISSING  Windowless test suite")
    assert "windowless-default.snapshot.md" in rows[0]


@pytest.mark.parametrize("script,runner", [
    ("vitest run", "vitest"),
    ("jest", "jest"),
    ("playwright test", "playwright"),
    ("node --test tests/", "node --test"),
])
def test_r039_node_runner_note(tmp_path, script, runner):
    """R-039: Node suite NOTE names runner, detached: false and KP-059."""
    root = tmp_path / "ws"
    root.mkdir()
    (root / "package.json").write_text('{"scripts":{"test":"%s"}}' % script, encoding="utf-8")
    _, out = run_check(root)
    rows = row_for(out)
    assert len(rows) == 1
    assert runner in rows[0] and "detached: false" in rows[0] and "KP-059" in rows[0]


def test_r039_other_runner_mocha_note(tmp_path):
    """R-039: other package.json test script names the first word."""
    root = tmp_path / "ws"
    root.mkdir()
    (root / "package.json").write_text('{"scripts":{"test":"mocha tests"}}', encoding="utf-8")
    rc, out = run_check(root)
    rows = row_for(out)
    assert len(rows) == 1 and "mocha" in rows[0]


def test_r039_none_seen_note(tmp_path):
    """R-039: empty workspace NOTE."""
    root = tmp_path / "ws"
    root.mkdir()
    (root / "docs").mkdir()
    rc, out = run_check(root)
    rows = row_for(out)
    assert len(rows) == 1
    assert "no pytest configuration" in rows[0]


def test_r039_pytest_and_node_both_rows(tmp_path):
    """R-039: pytest OK and Node NOTE together."""
    root = tmp_path / "ws"
    root.mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text(minimal_conftest(), encoding="utf-8")
    (root / "package.json").write_text('{"scripts":{"test":"vitest"}}', encoding="utf-8")
    rc, out = run_check(root)
    rows = row_for(out)
    assert len(rows) == 2
    assert any(line.startswith("  OK") for line in rows)
    assert any(line.startswith("  NOTE") for line in rows)


def test_r039_bridge_workspace_ok():
    """R-039: this repository's Workspace grades OK."""
    rc, out = run_check(WORKSPACE)
    rows = row_for(out)
    assert any(line == "  OK       Windowless test suite (tests/conftest.py)" for line in rows)
