"""The Workflows status line enforced (TASK-008), the supervisor's tests, written from handoff/TASK-008.md before the
delegation.

enforces: docs/REQUIREMENTS.md R-015 (the status file records a `Workflows:` line per part, beside the `Phase:` line):
inventory-check.py and conformance-check.py report a missing line, a malformed line and lines that do not stand together
right after `Phase:`, judging the grammar by workflow-check.py's check_status and the placement by its new
check_placement; a rule file that cannot be loaded is a failure; output stays ASCII; lines are split only at a line feed
(TASK-006's lesson). Special characters are built with chr() so no editing tool can turn an escape into the character.

Round 2 (handoff/TASK-008-r2.md): the valid and unwritten cases run on a bridge copy whose open list marks every entry
unwritten, with the f/FLAG precondition asserted; every way the rules can fail to load is a case (R2-3, R2-4); loading
writes no bytecode (R2-1); a program run through a link loads the checker beside its real file (R2-2).
"""
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

from test_conformance_check import VERSION, make_workspace, verdict

REPO = pathlib.Path(__file__).resolve().parent.parent
BRIDGE = REPO / "bridge" / "cursor-bridge"
INVENTORY_CHECK = BRIDGE / "inventory-check.py"
CONFORMANCE_CHECK = BRIDGE / "conformance-check.py"
FF = chr(12)
LSEP = chr(0x2028)
ARROW = chr(0x2192)

HEAD = "# Project Status\nBridge version: %s\nPhase: building\n" % VERSION
BRIDGE_LINE = "Workflows: Host Extension Development " + ARROW + " Claude Code Extension; traits: Installable\n"
UNCLASSIFIED = "Workflows: not yet classified\n"

VALID = {
    "bridge-line": HEAD + BRIDGE_LINE,
    "not-yet-classified": HEAD + UNCLASSIFIED,
}
MISSING = {
    "no-line": HEAD,
    "joined-by-form-feed": HEAD.rstrip("\n") + FF + UNCLASSIFIED,
    "joined-by-line-separator": HEAD.rstrip("\n") + LSEP + UNCLASSIFIED,
}
MALFORMED = {
    # (status text, the reason that must be named)
    "no-traits": (HEAD + "Workflows: Host Extension Development\n", "Workflows line must contain '; traits: ' exactly once"),
    "unknown-name": (HEAD + "Workflows: Nonexistent Development; traits: none\n", "name is not in the open list"),
    # An (e) finding: two product types on one line (stage B2 review, round 6: tests).
    "two-types": (HEAD + "Workflows: Web App Development, Host Extension Development; traits: none\n",
                  "part must name exactly one product type"),
    "line-between": ("# Project Status\nPhase: building\nBridge version: %s\n" % VERSION + UNCLASSIFIED,
                     "Workflows lines do not stand together right after the Phase line"),
    "above-phase": ("# Project Status\nBridge version: %s\n" % VERSION + UNCLASSIFIED + "Phase: building\n",
                    "Workflows lines do not stand together right after the Phase line"),
    "no-phase-line": ("# Project Status\nBridge version: %s\n" % VERSION + UNCLASSIFIED, "status file has no Phase line"),
}


def write_status(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")


def writing_env():
    """The environment with bytecode writing left on, so a test of R2-1 cannot pass because the runner turned it off."""
    env = dict(os.environ)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    env.pop("PYTHONPYCACHEPREFIX", None)
    return env


def inventory(cwd, status, program=INVENTORY_CHECK):
    """inventory-check.py on one status file, with no inventory or change log, from a folder of its own."""
    p = subprocess.run([sys.executable, str(program), "--inventory", "absent-inventory.md", "--changes", "absent-changes.md",
                        "--status", str(status)], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=writing_env(), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout.splitlines(), p.stdout, p.stderr


def workflows_lines(lines):
    return [line for line in lines if line.startswith("WORKFLOWS LINE:")]


def conformance(root, program=CONFORMANCE_CHECK):
    p = subprocess.run([sys.executable, str(program), str(root), "--offline"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=writing_env(), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout, p.stderr


def workspace(tmp_path, status_text):
    root = tmp_path / "proj"
    root.mkdir()
    make_workspace(root)
    write_status(root / "docs" / "PROJECT_STATUS.md", status_text)
    return root


# --- check_placement, the one new function in workflow-check.py --------------------------------------------------

def test_r015_placement_function(program):
    mod = program("workflow-check")
    assert mod.check_placement("s.md", HEAD) == [], "no Workflows line: missing is check_status's finding"
    # Neither line: still nothing to place (stage B2 review, round 6: the sweep's line 718).
    assert mod.check_placement("s.md", "# Project Status\n") == []
    assert mod.check_placement("s.md", HEAD + UNCLASSIFIED) == []
    two = "Phase: building\nWorkflows: app: not yet classified\nWorkflows: site: not yet classified\nOther: x\n"
    assert mod.check_placement("s.md", two) == []
    apart = "Phase: building\nWorkflows: app: not yet classified\nOther: x\nWorkflows: site: not yet classified\n"
    assert mod.check_placement("d\\s.md", apart) == [("place", "d/s.md", "-", "Workflows lines do not stand together right after the Phase line")]
    assert mod.check_placement("s.md", "Workflows: not yet classified\n") == [("place", "s.md", "-", "status file has no Phase line")]
    assert mod.check_placement("s.md", "Phase: building" + FF + "x\n" + UNCLASSIFIED) == [], "a form feed does not end the Phase line"
    assert mod.check_placement("s.md", "Phase: a\nPhase: b\n" + UNCLASSIFIED) == [("place", "s.md", "-", "Workflows lines do not stand together right after the Phase line")], "the first Phase line counts"


def test_r015_placement_reads_the_prefixes_with_their_space(program):
    """bridge/commands/supervisor.md, "Project state": the status lines are `Phase: ` and `Workflows: `, each prefix with
    its space, and check_placement places only such lines. A `Workflows:` line without its space is no Workflows line
    to place (check_status's (form) finding, not a placement one), and stands in no run of them; a `Phase:` line
    without its space is no Phase line (stage B2's review, round 8: the widened sweep's literals of lines 717, 722 and
    729 made without their space)."""
    mod = program("workflow-check")
    apart = "Phase: building\nWorkflows: app: not yet classified\nOther: x\nWorkflows:site: not yet classified\n"
    assert mod.check_placement("s.md", apart) == [], "a Workflows: line without its space is not placed"
    run_broken = "Phase: building\nWorkflows:site: not yet classified\nWorkflows: app: not yet classified\n"
    assert mod.check_placement("s.md", run_broken) == [("place", "s.md", "-", "Workflows lines do not stand together right after the Phase line")]
    assert mod.check_placement("s.md", "Phase:building\nWorkflows: not yet classified\n") == [("place", "s.md", "-", "status file has no Phase line")]


# --- inventory-check.py --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", sorted(VALID))
def test_r015_inventory_valid_line_reports_nothing(tmp_path, case):
    """Run on a copy whose open list marks every entry unwritten, so the bridge line's f and FLAG findings exist."""
    folder = _unwritten_copy(tmp_path)
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, VALID[case])
    rc, lines, out, err = inventory(tmp_path, status, program=folder / "inventory-check.py")
    assert "Traceback" not in err, err
    assert workflows_lines(lines) == [], lines


@pytest.mark.parametrize("case", sorted(MISSING))
def test_r015_inventory_missing_line(tmp_path, case):
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, MISSING[case])
    rc, lines, out, err = inventory(tmp_path, status)
    assert rc == 1, lines
    shown = str(status).replace("\\", "/")
    assert workflows_lines(lines) == [f"WORKFLOWS LINE: missing: {shown} has no Workflows line"], lines


@pytest.mark.parametrize("case", sorted(MALFORMED))
def test_r015_inventory_malformed_line(tmp_path, case):
    text, reason = MALFORMED[case]
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, text)
    rc, lines, out, err = inventory(tmp_path, status)
    assert rc == 1, lines
    found = workflows_lines(lines)
    assert found and all(line.startswith("WORKFLOWS LINE: malformed: ") for line in found), lines
    assert any(line.endswith(" - " + reason) for line in found), lines


def test_r015_inventory_prints_each_finding_in_order(tmp_path):
    """handoff/TASK-008.md: one WORKFLOWS LINE per finding of the judge, in the judge's order, the placement's last
    (stage B2 review, round 6: tests)."""
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, "# Project Status\nPhase: building\nBridge version: %s\n" % VERSION
                 + "Workflows: Nonexistent Development; traits: none\n")
    rc, lines, out, err = inventory(tmp_path, status)
    assert rc == 1, lines
    assert workflows_lines(lines) == [
        "WORKFLOWS LINE: malformed: Nonexistent Development - name is not in the open list",
        "WORKFLOWS LINE: malformed: - - part must name exactly one product type",
        "WORKFLOWS LINE: malformed: - - Workflows lines do not stand together right after the Phase line",
    ], lines


def test_r015_inventory_unwritten_types_are_not_malformed(tmp_path):
    """Codes f and FLAG (unwritten type, sub-type, trait) are workflow-check.py's concern, not a failure here.

    The copy's open list marks every entry unwritten and _unwritten_copy asserts that check_status then gives f and
    FLAG for the bridge line, so this negative test keeps its precondition when release B writes the bridge's entries.
    """
    folder = _unwritten_copy(tmp_path)
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, VALID["bridge-line"])
    rc, lines, out, err = inventory(tmp_path, status, program=folder / "inventory-check.py")
    assert "Traceback" not in err, err
    assert workflows_lines(lines) == [], lines
    assert not [line for line in lines if "not written" in line], lines


def test_r015_inventory_counts_each_finding_as_a_problem(tmp_path):
    """A malformed line is a failure line, counted in RESULT."""
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, VALID["not-yet-classified"])
    rc_ok, lines_ok, *_ = inventory(tmp_path, status)
    write_status(status, MALFORMED["no-traits"][0])
    rc_bad, lines_bad, *_ = inventory(tmp_path, status)

    def count(lines):
        last = lines[-1]
        return 0 if last == "RESULT: OK" else int(last.split()[1])

    assert workflows_lines(lines_bad), lines_bad
    assert count(lines_bad) == count(lines_ok) + len(workflows_lines(lines_bad)), (lines_ok, lines_bad)


def test_r015_inventory_output_is_ascii(tmp_path):
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, HEAD + "Workflows: " + chr(0xDC) + "nknown" + chr(0x1B) + "[31m; traits: none\n")
    rc, lines, out, err = inventory(tmp_path, status)
    assert rc == 1
    assert out.isascii(), repr(out)
    assert "\\xdc" in out and "\\x1b" in out, out


def test_r015_inventory_no_status_file_no_check(tmp_path):
    """TASK-008 Requirement 4: with no status file the line is not judged, nothing is said about it, and inventory-check
    keeps its existing note; the run ends normally. test_r015_inventory_missing_line is the positive control."""
    absent = tmp_path / "absent-status.md"
    rc, lines, out, err = inventory(tmp_path, absent)
    # The whole output on both streams, so nothing about the line can be said in any words (BUG-004 rounds 2 and 3,
    # Review A and Review B); the absent inventory is the run's one problem.
    assert err == "", err
    assert rc == 1, lines
    assert lines == [
        "note: status: %s not found (skipped)" % absent,
        "note: resources: not a git repository (reads not scanned)",
        "MISSING: absent-inventory.md does not exist",
        "RESULT: 1 problem(s)",
    ], lines


def _bridge_copy(tmp_path, with_checker=True, with_rules=True):
    """The two programs, in a folder of their own, with or without workflow-check.py and its rule files."""
    folder = tmp_path / "bin"
    folder.mkdir()
    for name in ("inventory-check.py", "conformance-check.py"):
        shutil.copyfile(BRIDGE / name, folder / name)
    if with_checker:
        shutil.copyfile(BRIDGE / "workflow-check.py", folder / "workflow-check.py")
    if with_rules:
        shutil.copytree(BRIDGE / "workflow", folder / "workflow")
    return folder


def _load_copy(folder):
    """The copy's workflow-check.py as a module, written to no __pycache__."""
    spec = importlib.util.spec_from_file_location("workflow_check_copy", folder / "workflow-check.py")
    mod = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = before
    return mod


def _unwritten_copy(tmp_path):
    """A bridge copy whose open list marks every entry unwritten, with that precondition asserted."""
    folder = _bridge_copy(tmp_path)
    open_list = folder / "workflow" / "open-list.md"
    text = open_list.read_text(encoding="utf-8")
    open_list.write_text(text.replace("| yes |", "| no |"), encoding="utf-8", newline="")
    mod = _load_copy(folder)
    open_text, _, open_err = mod.read_utf8(mod.DEFAULT_OPEN)
    reg_text, _, reg_err = mod.read_utf8(mod.DEFAULT_REGISTRY)
    assert open_err is None and reg_err is None, (open_err, reg_err)
    tables, errors = mod.load_tables(open_text, mod.DEFAULT_OPEN, reg_text, mod.DEFAULT_REGISTRY)
    assert not errors, errors
    codes = [item[0] for item in mod.check_status("s.md", VALID["bridge-line"], tables)]
    assert "f" in codes and "FLAG" in codes, "precondition: the bridge line must give f and FLAG findings, got %r" % codes
    return folder


# Each way the rules can fail to load: (how the copy is broken, status text, the text a not-checked line must hold).
NOT_LOADABLE = {
    "checker-absent": ("checker-absent", VALID["not-yet-classified"], "cannot be loaded (FileNotFoundError)"),
    "checker-syntax-error": ("checker-syntax-error", VALID["not-yet-classified"], "cannot be loaded (SyntaxError)"),
    "checker-exits": ("checker-exits", VALID["not-yet-classified"], "cannot be loaded (SystemExit)"),
    "rules-absent": ("rules-absent", VALID["not-yet-classified"], "open-list.md"),
    # The registry alone unreadable: its cause is named, the open list's is not (round 7: tests).
    "registry-absent": ("registry-absent", VALID["not-yet-classified"], "extension-points.md: does not exist"),
    "open-list-without-tables": ("open-list-without-tables", VALID["not-yet-classified"], "missing heading"),
    "no-escape-field": ("no-escape-field", MALFORMED["no-traits"][0], "workflow-check.py: AttributeError"),
    "check-exits-after-load": ("check-exits-after-load", VALID["not-yet-classified"], "workflow-check.py: SystemExit"),
    # Two tables without Key give two identical causes, each a line (TASK-008 Requirement 5: one line per cause; BUG-011's
    # gate round 1: Review A, the idiom sweep's inventory-check.py line 264, the causes printed with repeats dropped).
    "two-tables-without-key": ("two-tables-without-key", VALID["not-yet-classified"], "missing column Key"),
}


def _broken_copy(tmp_path, how):
    folder = _bridge_copy(tmp_path, with_checker=(how != "checker-absent"), with_rules=(how != "rules-absent"))
    checker = folder / "workflow-check.py"
    if how == "checker-syntax-error":
        checker.write_text(checker.read_text(encoding="utf-8") + "\ndef broken(:\n", encoding="utf-8", newline="")
    elif how == "checker-exits":
        checker.write_text("import sys\nsys.exit(3)\n" + checker.read_text(encoding="utf-8"), encoding="utf-8", newline="")
    elif how == "registry-absent":
        (folder / "workflow" / "extension-points.md").unlink()
    elif how == "open-list-without-tables":
        (folder / "workflow" / "open-list.md").write_text("# Open list\n\nNo tables here.\n", encoding="utf-8", newline="\n")
    elif how == "two-tables-without-key":
        open_list = folder / "workflow" / "open-list.md"
        text = open_list.read_text(encoding="utf-8")
        assert text.count("\n| Key | Name |") == 3, "precondition: three tables whose first column is Key"
        open_list.write_text(text.replace("\n| Key | Name |", "\n| Id | Name |", 2), encoding="utf-8", newline="")
    elif how == "check-exits-after-load":
        text = checker.read_text(encoding="utf-8")
        head = "def check_status(path, text, tables):\n"
        assert text.count(head) == 1
        checker.write_text(text.replace(head, head + "    raise SystemExit(4)\n"), encoding="utf-8", newline="")
    elif how == "no-escape-field":
        text = checker.read_text(encoding="utf-8")
        assert text.count("def escape_field(") == 1
        checker.write_text(text.replace("def escape_field(", "def escape_field_removed("), encoding="utf-8", newline="")
    return folder


# The cases whose rule files are broken; each of the others is one load failure with one cause.
RULE_CASES = ("rules-absent", "registry-absent", "open-list-without-tables", "two-tables-without-key")


def _causes(folder):
    """The causes a copy with broken rule files must give, from the copy itself: each rule file that cannot be read,
    else each table that cannot be loaded, as workflow-check.py's own reader states them, escaped as the judges
    escape them."""
    mod = _load_copy(folder)
    reads = [mod.read_utf8(mod.DEFAULT_OPEN), mod.read_utf8(mod.DEFAULT_REGISTRY)]
    causes = ["%s: %s" % (shown, err) for _, shown, err in reads if err]
    if not causes:
        _, errors = mod.load_tables(reads[0][0], mod.DEFAULT_OPEN, reads[1][0], mod.DEFAULT_REGISTRY)
        causes = ["%s: %s" % (item_path, reason) for item_path, reason in errors]
    return [mod.escape_field(cause) for cause in causes]


@pytest.mark.parametrize("case", sorted(NOT_LOADABLE))
def test_r015_inventory_rule_files_not_loadable_is_a_failure(tmp_path, case):
    how, text, cause = NOT_LOADABLE[case]
    folder = _broken_copy(tmp_path, how)
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, text)
    rc, lines, out, err = inventory(tmp_path, status, program=folder / "inventory-check.py")
    assert "Traceback" not in err and "Traceback" not in out, (out, err)
    assert rc == 1, (lines, err)
    found = workflows_lines(lines)
    assert found and all(line.startswith("WORKFLOWS LINE: not checked: ") for line in found), lines
    assert any(cause in line for line in found), "the cause must name %r: %r" % (cause, found)
    # One line per cause, each whole (TASK-008 Requirement 5; round 7: tests).
    if how in RULE_CASES:
        expected = _causes(folder)
        assert len(expected) == 1 if how == "registry-absent" else len(expected) >= 2, "precondition: %r" % expected
        assert found == ["WORKFLOWS LINE: not checked: " + c for c in expected], (found, expected)
        if how == "open-list-without-tables":
            # The three causes by name, so the copy's reader is not the only oracle (BUG-008's gate round 1: consider).
            assert [line.rsplit(": ", 1)[1] for line in found] == [
                "missing heading ## Product types", "missing heading ## Sub-types", "missing heading ## Traits"], found
        if how == "two-tables-without-key":
            assert [line.rsplit(": ", 1)[1] for line in found] == ["missing column Key"] * 2, found
    else:
        assert len(found) == 1, found


def _non_ascii_folder(tmp_path):
    folder = tmp_path / ("d" + chr(0xE9))
    folder.mkdir()
    return folder


def test_r015_inventory_not_checked_path_is_ascii(tmp_path):
    """The not-checked message names the checker's path; a non-ASCII path reaches the output as its escape. Since BUG-003
    escape_field makes every finding field ASCII, this message is the one the program's own ascii_text alone guards
    (stage B2 review, round 3: the driver's mutant had become equivalent for the field tests)."""
    base = _non_ascii_folder(tmp_path)
    folder = _broken_copy(base, "checker-absent")
    status = base / "PROJECT_STATUS.md"
    write_status(status, VALID["not-yet-classified"])
    rc, lines, out, err = inventory(base, status, program=folder / "inventory-check.py")
    found = workflows_lines(lines)
    assert found and "cannot be loaded (FileNotFoundError)" in found[0], lines
    assert all(line.isascii() for line in found) and "\\xe9" in found[0], found


def test_r015_conformance_not_checked_path_is_ascii(tmp_path):
    base = _non_ascii_folder(tmp_path)
    folder = _broken_copy(base, "checker-absent")
    rc, out, err = conformance(workspace(base, VALID["not-yet-classified"]), program=folder / "conformance-check.py")
    v, text = verdict(out, "Workflows line")
    assert v == "MISSING" and "cannot be loaded (FileNotFoundError)" in text, out
    assert text.isascii() and "\\xe9" in text, text


def test_r015_loading_the_checker_writes_no_bytecode(tmp_path):
    """R2-1: neither program leaves a __pycache__ beside itself (inventory-check reads only; conformance-check never writes)."""
    folder = _bridge_copy(tmp_path)
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, MALFORMED["no-traits"][0])
    rc, lines, out, err = inventory(tmp_path, status, program=folder / "inventory-check.py")
    assert "Traceback" not in err, err
    assert any(line.startswith("WORKFLOWS LINE: malformed: ") for line in lines), "the run must have judged the line: %r" % lines
    rc, out, err = conformance(workspace(tmp_path, VALID["not-yet-classified"]), program=folder / "conformance-check.py")
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert not (folder / "__pycache__").exists(), sorted(p.name for p in (folder / "__pycache__").iterdir())
    # Positive control: in this environment, the same load without the switch does leave bytecode beside the checker.
    probe = ("import importlib.util, sys; s = importlib.util.spec_from_file_location('w', sys.argv[1]); "
             "m = importlib.util.module_from_spec(s); s.loader.exec_module(m)")
    subprocess.run([sys.executable, "-c", probe, str(folder / "workflow-check.py")], env=writing_env(), check=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert (folder / "__pycache__").exists(), "the control: bytecode writing must be on, or this test proves nothing"


def test_r015_the_bytecode_switch_is_restored(program):
    """R2-1: sys.dont_write_bytecode is put back after the check, whatever it was."""
    before = sys.dont_write_bytecode
    try:
        for name in ("inventory-check", "conformance-check"):
            mod = program(name)
            for value in (False, True):
                sys.dont_write_bytecode = value
                mod.judge_workflows_line("s.md", VALID["not-yet-classified"])
                assert sys.dont_write_bytecode is value, (name, value)
    finally:
        sys.dont_write_bytecode = before


@pytest.mark.parametrize("case", sorted(VALID))
@pytest.mark.parametrize("name", ["inventory-check", "conformance-check"])
def test_r015_a_valid_line_is_judged_valid_with_no_rows(tmp_path, name, case):
    """handoff/TASK-008.md, the judge's interface (and its docstring): the outcome is valid, missing, malformed or not
    checked, and the rows are empty for valid. A valid line is judged ("valid", []) by each judge, never malformed
    with no rows, which inventory-check.py prints the same (BUG-009's gate round 1: Review A, a consider; the
    widened sweep's inventory-check.py line 228, `if findings:` forced true, survived at the output). Judged on a copy
    whose open list marks every entry unwritten, so the line's f and FLAG findings exist and are dropped, as the
    output twins are (BUG-009's gate round 2: Review A, a consider)."""
    folder = _unwritten_copy(tmp_path)
    spec = importlib.util.spec_from_file_location(name.replace("-", "_") + "_valid_copy", folder / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.judge_workflows_line("s.md", VALID[case]) == ("valid", [])


@pytest.mark.parametrize("program_name", ["inventory-check.py", "conformance-check.py"])
def test_r015_checker_is_found_beside_the_real_file_not_the_link(tmp_path, program_name):
    """R2-2: run through a symbolic link, a program loads the workflow-check.py beside its real file."""
    folder = _bridge_copy(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "workflow-check.py").write_text("raise RuntimeError('the wrong checker')\n", encoding="utf-8")
    link = elsewhere / program_name
    try:
        os.symlink(folder / program_name, link)
    except (OSError, NotImplementedError) as err:
        pytest.skip("cannot create a symbolic link here: %s" % err)
    if program_name == "inventory-check.py":
        status = tmp_path / "PROJECT_STATUS.md"
        write_status(status, VALID["not-yet-classified"])
        rc, lines, out, err = inventory(tmp_path, status, program=link)
        assert "Traceback" not in err and lines and lines[-1].startswith("RESULT: "), (lines, err)
        assert workflows_lines(lines) == [], lines
    else:
        rc, out, err = conformance(workspace(tmp_path, VALID["not-yet-classified"]), program=link)
        assert "Traceback" not in err, err
        assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out


# --- conformance-check.py ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", sorted(VALID))
def test_r015_conformance_valid_line_is_ok(tmp_path, case):
    """Run on a copy whose open list marks every entry unwritten, as the inventory twin is."""
    folder = _unwritten_copy(tmp_path)
    rc, out, err = conformance(workspace(tmp_path, VALID[case]), program=folder / "conformance-check.py")
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rc == 0 and out.splitlines()[-1] == "RESULT: CONFORMANT", out


@pytest.mark.parametrize("case", sorted(MISSING))
def test_r015_conformance_missing_line(tmp_path, case):
    rc, out, err = conformance(workspace(tmp_path, MISSING[case]))
    v, text = verdict(out, "Workflows line")
    assert v == "MISSING" and text == "Workflows line  - missing: docs/PROJECT_STATUS.md has no Workflows line", out
    assert rc == 1


@pytest.mark.parametrize("case", sorted(MALFORMED))
def test_r015_conformance_malformed_line(tmp_path, case):
    text_in, reason = MALFORMED[case]
    rc, out, err = conformance(workspace(tmp_path, text_in))
    v, text = verdict(out, "Workflows line")
    assert v == "MISSING" and text.startswith("Workflows line  - malformed: "), out
    assert reason in text, out
    assert rc == 1


def test_r015_conformance_prints_each_finding_in_order(tmp_path):
    """handoff/TASK-008.md Requirement 7: the row is `malformed: ` and every finding of the judge, `name - reason`, joined
    by `; `, in the judge's order, the placement's last (stage B2 review, round 7: tests; the inventory twin is
    test_r015_inventory_prints_each_finding_in_order)."""
    text = "# Project Status\nPhase: building\nBridge version: %s\n" % VERSION + "Workflows: Nonexistent Development; traits: none\n"
    rc, out, err = conformance(workspace(tmp_path, text))
    assert verdict(out, "Workflows line") == ("MISSING", "Workflows line  - malformed: "
        "Nonexistent Development - name is not in the open list; - - part must name exactly one product type; "
        "- - Workflows lines do not stand together right after the Phase line"), out
    assert rc == 1


# Stage B2's review, round 10: a finding given twice is printed twice, and two identical lines stand together (the idiom
# sweep's inventory-check.py line 224, conformance-check.py line 333 and workflow-check.py line 729: the findings, or
# the placed run, with repeats dropped).
REPEATED = "# Project Status\nPhase: building\nWorkflows: Web App Development; traits: none\nWorkflows: Web App Development; traits: none\n"


def test_r015_a_repeated_finding_is_reported_each_time(tmp_path):
    """handoff/TASK-008.md: one WORKFLOWS LINE per finding of the judge, and the conformance row every finding joined
    by `; `: two identical unprefixed lines each break the part-prefix rule, so each judge names it twice."""
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, REPEATED)
    rc, lines, out, err = inventory(tmp_path, status)
    assert workflows_lines(lines) == ["WORKFLOWS LINE: malformed: - - Workflows line breaks the part-prefix rule"] * 2, lines
    assert rc == 1, lines
    rc, out, err = conformance(workspace(tmp_path, REPEATED))
    assert verdict(out, "Workflows line") == ("MISSING", "Workflows line  - malformed: "
        "- - Workflows line breaks the part-prefix rule; - - Workflows line breaks the part-prefix rule"), out
    assert rc == 1


def test_r015_two_identical_lines_stand_together(program):
    """check_placement: the Workflows lines stand together right after the Phase line, two identical ones too."""
    assert program("workflow-check").check_placement("s.md", REPEATED) == []


def test_r015_conformance_no_status_file_no_check(tmp_path):
    """TASK-008 Requirement 4, conformance-check's half: with no status file the Workflows line is not judged and no row
    names it; the records row already reports the file missing. The positive control runs first, on the same workspace
    with its status file."""
    root = workspace(tmp_path, VALID["not-yet-classified"])
    rc, out, err = conformance(root)
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), "control: with the file the line is judged: " + out
    (root / "docs" / "PROJECT_STATUS.md").unlink()
    rc, out, err = conformance(root)
    assert "Traceback" not in err and "Traceback" not in out, (out, err)
    assert out.splitlines()[-1].startswith("RESULT: "), out
    assert verdict(out, "Workflows line") == (None, None), out
    assert "workflows" not in out.lower(), "nothing about the line under any name (stage B2 review, round 4: tests)"
    v, text = verdict(out, "docs/PROJECT_STATUS.md")
    assert v == "MISSING" and "the bounded status file" in text, out
    assert rc == 1


def test_r015_conformance_output_is_ascii(tmp_path):
    rc, out, err = conformance(workspace(tmp_path, HEAD + "Workflows: " + chr(0xDC) + "nknown; traits: none\n"))
    assert rc == 1 and out.isascii(), repr(out)
    assert "\\xdc" in out, out


@pytest.mark.parametrize("case", sorted(NOT_LOADABLE))
def test_r015_conformance_rule_files_not_loadable_is_missing(tmp_path, case):
    how, text_in, cause = NOT_LOADABLE[case]
    folder = _broken_copy(tmp_path, how)
    rc, out, err = conformance(workspace(tmp_path, text_in), program=folder / "conformance-check.py")
    assert "Traceback" not in err and "Traceback" not in out, (out, err)
    assert rc == 1, (out, err)
    v, text = verdict(out, "Workflows line")
    assert v == "MISSING" and text.startswith("Workflows line  - not checked: "), out
    assert cause in text, "the cause must name %r: %r" % (cause, text)
    # Every cause, joined by "; " (TASK-008 Requirement 7; round 7: tests).
    if how in RULE_CASES:
        assert text == "Workflows line  - not checked: " + "; ".join(_causes(folder)), text
    else:
        assert "; " not in text, text


@pytest.mark.parametrize("how", ["checker-absent", "checker-syntax-error", "checker-exits"])
@pytest.mark.parametrize("name", ["inventory-check", "conformance-check"])
def test_r015_the_bytecode_switch_is_restored_when_the_checker_cannot_be_loaded(tmp_path, name, how):
    """handoff/TASK-008-r2.md R2-1: the judge puts sys.dont_write_bytecode back in a `finally`, so a checker that is
    absent, does not compile or exits while it loads leaves the switch as it found it, either way (stage B2's review,
    round 8: tests; a restore after the load alone survived)."""
    folder = _broken_copy(tmp_path, how)
    spec = importlib.util.spec_from_file_location(name.replace("-", "_") + "_copy", folder / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(mod)
        for value in (False, True):
            sys.dont_write_bytecode = value
            outcome, rows = mod.judge_workflows_line("s.md", VALID["not-yet-classified"])
            assert outcome == "not-checked" and "cannot be loaded" in rows[0], (outcome, rows)
            assert sys.dont_write_bytecode is value, (name, how, value)
    finally:
        sys.dont_write_bytecode = before


@pytest.mark.parametrize("judge", ["inventory-check", "conformance-check"])
def test_r015_tables_that_cannot_be_loaded_are_reported_before_a_line_is_judged(tmp_path, judge):
    """TASK-008 Requirement 5: rule files that cannot be loaded give `not checked` and their causes, for a status file
    that holds a Workflows line to judge, not only for `not yet classified`, which needs no table (stage B2's review,
    round 9: the control-flow sweep's inventory-check.py line 224 and conformance-check.py line 333, the line judged
    before the load errors were tested, which then judged it with no tables)."""
    folder = _broken_copy(tmp_path, "open-list-without-tables")
    expected = _causes(folder)
    assert len(expected) >= 2, "precondition: %r" % expected
    text = HEAD + BRIDGE_LINE
    if judge == "inventory-check":
        status = tmp_path / "PROJECT_STATUS.md"
        write_status(status, text)
        rc, lines, out, err = inventory(tmp_path, status, program=folder / "inventory-check.py")
        assert workflows_lines(lines) == ["WORKFLOWS LINE: not checked: " + c for c in expected], lines
    else:
        rc, out, err = conformance(workspace(tmp_path, text), program=folder / "conformance-check.py")
        assert verdict(out, "Workflows line") == ("MISSING", "Workflows line  - not checked: " + "; ".join(expected)), out
    assert "Traceback" not in err and "Traceback" not in out, (out, err)
    assert rc == 1
