"""TASK-066's acceptance tests, the supervisor's (R-086, ISS-031): invisible-check.py refuses by Unicode category.
enforces: docs/REQUIREMENTS.md R-086; docs/DESIGN.md, Change: the program release, "The scans" (J1); docs/BUILD_PLAN.md,
TASK-066, Done when. The builder reads and runs these tests and never edits them.

The rule these tests fix: every character whose Unicode category is Cc, Cf, Zl or Zp, and every Zs character other than
U+0020, is a finding, but for U+0009, U+000A and U+000D anywhere and U+FEFF as a file's first character. Each finding is
one line `INVISIBLE: <path>:<line>:<column> U+XXXX <the Unicode name>`, or `INVISIBLE: <path>:<line>:<column> U+XXXX`
alone where the character has no Unicode name (the names are compared without regard to case). The program's options
([<base-ref>] [--all] [--non-ascii]), its exit codes (0 none, 1 at least one, 2 cannot verify) and what it reads (the
files changed against the base plus the untracked ones, or every tracked file with --all) are unchanged.

On the checkpoint every case is red but the last: the old program names its characters by a list and passes each
character below, so a run prints `RESULT: OK` where these cases expect a finding. The last case runs the Workspace's own
program over the Workspace's tracked files and skips where the Workspace is not a git work tree (a mutation run's copy).

KP-052: every character outside printable ASCII in this file is built with chr(), never typed."""
import os
import subprocess
import sys
import unicodedata

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.normpath(os.path.join(HERE, os.pardir))
PROG = os.path.join(WORKSPACE, "bridge", "cursor-bridge", "invisible-check.py")
TAB, LF, CR, SPACE, BOM = chr(9), chr(10), chr(13), chr(32), chr(0xFEFF)

# One or more characters per category; none of them is on the old program's list (each is red on the checkpoint).
FINDINGS = [
    ("Cc", 0x0001), ("Cc", 0x0007), ("Cc", 0x0008), ("Cc", 0x000B), ("Cc", 0x000C), ("Cc", 0x001B), ("Cc", 0x001F),
    ("Cc", 0x007F), ("Cc", 0x0085), ("Cc", 0x009F),
    ("Cf", 0x200E), ("Cf", 0x2061), ("Cf", 0xFFF9), ("Cf", 0xE0041),
    ("Zl", 0x2028), ("Zp", 0x2029),
    ("Zs", 0x1680), ("Zs", 0x205F),
]


def env():
    return dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
                GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=env())
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def run(repo, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), cwd=str(repo), capture_output=True, env=env())
    out = p.stdout.decode("utf-8", errors="replace") + p.stderr.decode("utf-8", errors="replace")
    return p.returncode, out


def base_repo(tmp_path):
    r = tmp_path / "inv"
    r.mkdir()
    (r / "doc.md").write_bytes(b"plain\n")
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "core.autocrlf", "false")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    return r


def finding_lines(out):
    return [line for line in out.splitlines() if line.startswith("INVISIBLE: ")]


def expected_line(path, n, col, cp):
    head = "INVISIBLE: %s:%d:%d U+%04X" % (path, n, col, cp)
    name = unicodedata.name(chr(cp), "")
    return head, name


@pytest.mark.parametrize("category,cp", FINDINGS, ids=["%s-U+%04X" % (c, cp) for c, cp in FINDINGS])
def test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point(tmp_path, category, cp):
    """R-086: a character of the categories Cc, Cf, Zl, Zp, or Zs other than the plain space, is a finding naming the file,
    the line, the code point and the Unicode name, or the code point alone where the character has none."""
    assert unicodedata.category(chr(cp)) == category
    r = base_repo(tmp_path)
    (r / "doc.md").write_bytes(("plain" + LF + "a" + chr(cp) + "b" + LF).encode("utf-8"))
    rc, out = run(r, "HEAD")
    assert rc == 1, out
    lines = finding_lines(out)
    assert len(lines) == 1, out
    head, name = expected_line("doc.md", 2, 2, cp)
    if name:
        assert lines[0].startswith(head + " "), out
        assert lines[0][len(head) + 1:].lower() == name.lower(), out
    else:
        assert lines[0] == head, "a character with no Unicode name is named by its code point alone: " + out
    assert all(ord(c) < 128 for c in out), "the output is ASCII"


def test_r086_the_allow_list_passes_and_only_the_other_characters_are_findings(tmp_path):
    """R-086: tab, line feed and carriage return anywhere, the byte-order mark as the file's first character, the plain
    space and visible non-ASCII characters are no finding; a byte-order mark anywhere else and a line separator are."""
    r = base_repo(tmp_path)
    text = (BOM + "head" + TAB + "col" + CR + LF
            + "a" + SPACE + "b" + chr(0x2028) + "c" + CR + LF
            + BOM + "mid" + TAB + CR + LF
            + "caf" + chr(0x00E9) + SPACE + chr(0x2014) + SPACE + chr(0x4E2D) + CR + "x" + LF)
    (r / "doc.md").write_bytes(text.encode("utf-8"))
    rc, out = run(r, "HEAD")
    assert rc == 1, out
    lines = finding_lines(out)
    assert len(lines) == 2, out
    assert lines[0].startswith("INVISIBLE: doc.md:2:4 U+2028 "), out
    assert lines[1].startswith("INVISIBLE: doc.md:3:1 U+FEFF "), out
    assert "RESULT: 2 invisible character(s)" in out, out


def test_r086_every_tracked_file_is_read_with_all(tmp_path):
    """R-086 with the options unchanged: --all reads every tracked file, committed or not changed."""
    r = base_repo(tmp_path)
    (r / "a.md").write_bytes(("x" + chr(0x2029) + "y" + LF).encode("utf-8"))
    (r / "b.md").write_bytes(b"clean\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "two")
    rc, out = run(r, "HEAD")
    assert rc == 0 and "RESULT: OK" in out, "nothing changed against HEAD: " + out
    rc, out = run(r, "--all")
    assert rc == 1, out
    assert [line.lower() for line in finding_lines(out)] == ["invisible: a.md:1:2 u+2029 paragraph separator"], out
    assert "RESULT: 1 invisible character(s) in the tree" in out, out


def test_r086_the_files_changed_against_a_base_and_the_untracked_files_are_read(tmp_path):
    """R-086 with what it reads unchanged: the files changed against the given base, and the untracked ones."""
    r = base_repo(tmp_path)
    base = git(r, "rev-parse", "HEAD")
    (r / "c.md").write_bytes(("c" + chr(0x0085) + LF).encode("utf-8"))
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "c")
    (r / "u.md").write_bytes(("u" + chr(0x000B) + LF).encode("utf-8"))
    rc, out = run(r, base)
    assert rc == 1, out
    assert finding_lines(out) == ["INVISIBLE: c.md:1:2 U+0085", "INVISIBLE: u.md:1:2 U+000B"], out
    rc, out = run(r, "HEAD")
    assert finding_lines(out) == ["INVISIBLE: u.md:1:2 U+000B"], "against HEAD only the untracked file: " + out


def test_r086_the_non_ascii_listing_keeps_the_exit_code(tmp_path):
    """R-086 with the options unchanged: --non-ascii lists every character above U+007F and does not change the exit."""
    r = base_repo(tmp_path)
    (r / "doc.md").write_bytes(("a" + chr(0x2028) + "b" + chr(0x00E9) + LF).encode("utf-8"))
    rc, out = run(r, "HEAD", "--non-ascii")
    assert rc == 1, out
    assert len(finding_lines(out)) == 1 and finding_lines(out)[0].startswith("INVISIBLE: doc.md:1:2 U+2028 "), out
    assert "NON-ASCII: doc.md:1:2 U+2028 LINE SEPARATOR" in out, "the listing's format is unchanged: " + out
    assert "NON-ASCII: doc.md:1:4 U+00E9 LATIN SMALL LETTER E WITH ACUTE" in out, out
    assert all(ord(c) < 128 for c in out), "the output is ASCII"


def _work_tree(folder):
    try:
        p = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=folder, capture_output=True, text=True, env=env())
    except OSError:
        return False
    return p.returncode == 0 and os.path.normcase(os.path.normpath(p.stdout.strip())) == os.path.normcase(folder)


def test_r086_the_repository_s_tracked_files_pass():
    """R-086: the repository's own tracked files pass the program (TASK-066's sweep, Done when)."""
    if not _work_tree(WORKSPACE):
        pytest.skip("the Workspace is not a git work tree here (a mutation run's copy)")
    rc, out = run(WORKSPACE, "--all")
    assert rc == 0 and "RESULT: OK" in out, out
