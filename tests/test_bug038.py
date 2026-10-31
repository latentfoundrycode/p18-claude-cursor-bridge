"""Supervisor-side reproduction tests of BUG-038; written by the supervisor; the builder reads and runs them, never edits them.

Project end on the bridge itself (2026-10-31): `completion-check.py --mode done` failed with two STAND-IN lines, both in
the program's own docstring, which quotes the phrases its stand-in scan looks for ("coming soon", "not yet
implemented", "under construction", a Placeholder component, todo!()). The bridge ships the program as tracked code,
so the scan finds its own description of what it scans for, and the bridge's project end cannot pass. The check must
still find every stand-in in the other shipped files.

enforces: ~/.claude/cursor-bridge/workflow/phases/project-end.md ("Prove the product is complete": `completion-check.py
--mode done` prints `RESULT: OK` ... no stand-in in shipped code) and completion-check.py's own docstring (STAND-IN:
"shipped (non-test) code shows a user-visible stand-in"). The helpers are tests/test_completion_check.py's.
"""
import os
import shutil
import subprocess
import sys

import test_completion_check as C

REGISTER = """| ID | Requirement | Source | Status | Evidence |
|---|---|---|---|---|
| R-001 | parse the file | owner | built | tests/test_parse.py |
"""
PLAN = """# Plan

## Stage 1
Demonstration: the parser runs.

### TASK-001 — parser
Satisfies: R-001
Scope: src/parse.py
"""
SHIPPED = os.path.join("bridge", "cursor-bridge", "completion-check.py")


def _repo(tmp_path, extra=None):
    """A scratch project complete but for what `extra` adds, shipping a tracked copy of the completion check as the
    bridge does, and running that copy."""
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "tests").mkdir()
    (r / "src").mkdir()
    (r / "bridge" / "cursor-bridge").mkdir(parents=True)
    (r / "docs" / "REQUIREMENTS.md").write_text(REGISTER, encoding="utf-8")
    (r / "docs" / "BUILD_PLAN.md").write_text(PLAN, encoding="utf-8")
    (r / "tests" / "test_parse.py").write_text("def test_r001():  # R-001\n    assert True\n", encoding="utf-8")
    (r / "src" / "parse.py").write_text("X = 1\n", encoding="utf-8")
    shutil.copyfile(C.PROG, str(r / SHIPPED))
    for rel, text in (extra or {}).items():
        (r / rel).write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(r), check=True, env=C.ENV)
    subprocess.run(["git", "add", "-A"], cwd=str(r), check=True, env=C.ENV)
    subprocess.run(["git", "commit", "-q", "-m", "scratch"], cwd=str(r), check=True, env=C.ENV)
    return r


def _run(repo, program):
    p = subprocess.run([sys.executable, "-B", str(program), "--mode", "done"], cwd=str(repo), capture_output=True, text=True,
                       env=C.ENV, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout + p.stderr


def test_bug038_the_completion_check_finds_no_stand_in_in_its_own_source(tmp_path):
    """The reproduction: a complete project that ships the completion check passes at done, run by the shipped copy
    and by the release folder's program alike (the bridge runs the installed one on its own tree)."""
    r = _repo(tmp_path)
    for program in (r / SHIPPED, C.PROG):
        rc, out = _run(r, program)
        assert "STAND-IN" not in out, "the check reports its own source as a stand-in: " + out
        assert rc == 0 and "RESULT: OK" in out, out


def test_bug038_a_stand_in_elsewhere_is_still_found(tmp_path):
    """Preservation: each kind of stand-in the docstring names, in another shipped file beside the program, still
    fails at done, and so does one added to the program's own source: the fix is the docstring's wording, not a
    scan that skips the bridge's folder or the program's file."""
    planted = ('"""Settings: arrives in a later stage."""\n', "MSG = 'coming soon'\n", "# not yet implemented\n",
               "TITLE = 'under construction'\n", "class SettingsPlaceholderView: pass\n",
               "class AboutPlaceholderSection: pass\n", "# todo!()\n")
    beside = os.path.join("bridge", "cursor-bridge", "screen.py")
    source = open(C.PROG, encoding="utf-8").read()
    if not source.endswith("\n"):
        source += "\n"
    own = source + "# coming soon\n"
    r = _repo(tmp_path, {beside: "".join(planted), SHIPPED: own})
    rc, out = _run(r, C.PROG)
    lines = out.splitlines()
    found = [l for l in lines if l.startswith("STAND-IN: bridge/cursor-bridge/screen.py:")]
    assert rc == 1 and len(found) == len(planted), out
    in_own = [l for l in lines if l.startswith("STAND-IN: bridge/cursor-bridge/completion-check.py:")]
    last = own.count("\n")
    assert in_own == ["STAND-IN: bridge/cursor-bridge/completion-check.py:%d: # coming soon" % last], out


def test_bug038_the_docstring_still_names_each_kind_it_scans_for():
    """The fix keeps the program's own account of what a stand-in is: the STAND-IN paragraph of its docstring
    still names each kind (a feature said to come later or soon, one not yet implemented or available, one under
    construction, a placeholder component with each of its six suffixes, Rust's todo and unimplemented macros), in
    words its scan does not match, and ends on the owner-deferred sentence unchanged."""
    text = open(C.PROG, encoding="utf-8").read()
    start = text.index('"""')                       # after the shebang line
    doc = text[start:text.index('"""', start + 3)]
    para = doc[doc.index("STAND-IN"):doc.index("Notes never fail")].lower()
    for words in ("later", "soon", "implemented", "available", "construction", "placeholder", "todo", "unimplemented",
                  "view", "page", "screen", "tab", "panel", "section"):
        assert words in para, words
    sentence = "Allowed only on a line that names the ID of an owner-deferred requirement."
    assert doc[doc.index("STAND-IN"):doc.index("Notes never fail")].rstrip().endswith(sentence)
