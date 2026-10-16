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
    assert mod.check_placement("s.md", HEAD + UNCLASSIFIED) == []
    two = "Phase: building\nWorkflows: app: not yet classified\nWorkflows: site: not yet classified\nOther: x\n"
    assert mod.check_placement("s.md", two) == []
    apart = "Phase: building\nWorkflows: app: not yet classified\nOther: x\nWorkflows: site: not yet classified\n"
    assert mod.check_placement("d\\s.md", apart) == [("place", "d/s.md", "-", "Workflows lines do not stand together right after the Phase line")]
    assert mod.check_placement("s.md", "Workflows: not yet classified\n") == [("place", "s.md", "-", "status file has no Phase line")]
    assert mod.check_placement("s.md", "Phase: building" + FF + "x\n" + UNCLASSIFIED) == [], "a form feed does not end the Phase line"
    assert mod.check_placement("s.md", "Phase: a\nPhase: b\n" + UNCLASSIFIED) == [("place", "s.md", "-", "Workflows lines do not stand together right after the Phase line")], "the first Phase line counts"


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
    rc, lines, out, err = inventory(tmp_path, tmp_path / "absent-status.md")
    assert workflows_lines(lines) == [], lines


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
    "open-list-without-tables": ("open-list-without-tables", VALID["not-yet-classified"], "missing heading"),
    "no-escape-field": ("no-escape-field", MALFORMED["no-traits"][0], "workflow-check.py: AttributeError"),
    "check-exits-after-load": ("check-exits-after-load", VALID["not-yet-classified"], "workflow-check.py: SystemExit"),
}


def _broken_copy(tmp_path, how):
    folder = _bridge_copy(tmp_path, with_checker=(how != "checker-absent"), with_rules=(how != "rules-absent"))
    checker = folder / "workflow-check.py"
    if how == "checker-syntax-error":
        checker.write_text(checker.read_text(encoding="utf-8") + "\ndef broken(:\n", encoding="utf-8", newline="")
    elif how == "checker-exits":
        checker.write_text("import sys\nsys.exit(3)\n" + checker.read_text(encoding="utf-8"), encoding="utf-8", newline="")
    elif how == "open-list-without-tables":
        (folder / "workflow" / "open-list.md").write_text("# Open list\n\nNo tables here.\n", encoding="utf-8", newline="\n")
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
    if how == "rules-absent":
        assert any("open-list.md" in line for line in found), "the cause names the rule file that cannot be read"


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
