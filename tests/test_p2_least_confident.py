"""Stage P2's least-confident item 3, settled by a test before stage P3's first delegation (FIX-006).

enforces: docs/HARDENING.md, The program release, "Least confident (stage P2's close, 2026-11-19)", item 3;
docs/REQUIREMENTS.md R-087 (git unreadable exits 2, never a pass).

Item 3: push-scan.py reads each commit with `git --attr-source=<the empty tree> ... show`, git's own option, gained in
2.40. An older git refuses the option (exit 129, `unknown option`, nothing on standard output). The scan must then stop with
`push-scan: CANNOT SCAN - git show failed (exit 129)` and exit 2, never pass and never report a partial result.
The older git is a stand-in: a wrapper starts the program with Python's subprocess.run answering exactly as git
before 2.40 answers any command carrying `--attr-source`, every other git command running the real git. Each case
runs once without the stand-in as its control.

Supervisor-written; no builder run. KP-052: no character outside printable ASCII is typed in this file."""
import os
import subprocess
import sys

from test_program_push_scan import DRIVE_FWD, PROG, Scratch, hits

OLD_GIT = '''import os, runpy, subprocess, sys
_real = subprocess.run
def _old_git(argv, *args, **kwargs):
    if any(isinstance(a, str) and a.startswith("--attr-source") for a in argv):
        bad = [a for a in argv if isinstance(a, str) and a.startswith("--attr-source")][0]
        return subprocess.CompletedProcess(argv, 129, b"", ("unknown option: " + bad + "\\n").encode())
    return _real(argv, *args, **kwargs)
subprocess.run = _old_git
prog = sys.argv[1]
sys.path.insert(0, os.path.dirname(prog))
sys.argv = [prog] + sys.argv[2:]
runpy.run_path(prog, run_name="__main__")
'''


def run_old_git(s, tmp_path, *args):
    wrapper = tmp_path / "old_git_wrapper.py"
    wrapper.write_text(OLD_GIT, encoding="ascii")
    p = subprocess.run([sys.executable, str(wrapper), PROG] + list(args), cwd=str(s.repo), capture_output=True,
                       env=s.env(), timeout=300)
    return p.returncode, p.stdout.decode("utf-8", errors="replace") + p.stderr.decode("utf-8", errors="replace")


def test_item3_a_git_refusing_attr_source_on_a_clean_range_cannot_scan_and_exits_2(tmp_path):
    """Item 3: a clean range, which passes under a git that has the option, exits 2 with CANNOT SCAN under one
    that refuses it, and never prints OK."""
    s = Scratch(tmp_path)
    s.commit({"a.md": "first\n"}, message="one")
    rc, out = s.run()
    assert rc == 0 and "push-scan: OK - 1 commit(s)" in out, out
    rc, out = run_old_git(s, tmp_path)
    assert rc == 2, out
    assert "push-scan: CANNOT SCAN - git show failed (exit 129)" in out, out
    assert "push-scan: OK" not in out and hits(out) == [], out


def test_item3_a_git_refusing_attr_source_on_a_range_with_a_hit_exits_2_and_reports_no_partial_hits(tmp_path):
    """Item 3: a range whose first commit is clean and whose second holds a path in an added line exits 1 with the
    hit under a git that has the option; under one that refuses it the scan stops at the first commit with exit 2,
    printing no HIT line and no OK."""
    s = Scratch(tmp_path)
    s.commit({"a.md": "plain\n"}, message="one")
    s.commit({"b.md": "see " + DRIVE_FWD + "\n"}, message="two")
    rc, out = s.run()
    assert rc == 1 and len(hits(out)) == 1, out
    rc, out = run_old_git(s, tmp_path)
    assert rc == 2, out
    assert "push-scan: CANNOT SCAN - git show failed (exit 129)" in out, out
    assert "push-scan: OK" not in out and hits(out) == [], out


def test_item3_the_stand_in_refuses_only_the_attr_source_command(tmp_path):
    """The stand-in's own control: under it, the range's other git commands still run, so the exit 2 above comes
    from the refused option and not from a git that cannot start (push-scan names that `git cannot be started`)."""
    s = Scratch(tmp_path)
    s.commit({"a.md": "first\n"}, message="one")
    rc, out = run_old_git(s, tmp_path)
    assert "git cannot be started" not in out and "internal error" not in out, out
    assert "git show failed (exit 129)" in out, out
