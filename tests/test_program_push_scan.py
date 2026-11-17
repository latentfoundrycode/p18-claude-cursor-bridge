"""TASK-067's acceptance tests, the supervisor's (R-087; D-002, D-004): the pre-push scan as a program.
enforces: docs/REQUIREMENTS.md R-087; docs/DESIGN.md, Change: the program release, "The scans" (C2); docs/BUILD_PLAN.md,
TASK-067, Done when; D-002 (push_scan --> bridge_env); D-004 (p_push_scan: hits to the terminal only, never the matched
text); the owner's decision of 2026-11-18 (in this chat, the question form): the names taken from the repository's
configured git identity are public, dropped like the remote's owner segment (rule 52: pinned here). The builder reads
and runs these tests and never edits them.

The interface these tests fix (the brief states it):
  python push-scan.py [<base>]     run from the repository; <base> defaults to origin/<the default branch>, read from
                                   origin/HEAD; a base beginning with `-` is refused with exit 2.
  Each hit is one line `push-scan: HIT <short hash> <place> <kind>`: <short hash> as git's %h prints it; <place> is
  `message`, `author`, `committer`, `file #<k>` (a file's own name, k its 1-based position in the commit's list of
  files), `line <path>:<n>` (an added line, n its number in the new file) or `line #<k>:<n>` where that file's own path
  holds a hit; <kind> is `path` or `name`, one line per place and kind. A clean range prints
  `push-scan: OK - <n> commit(s)` and exits 0; any hit exits 1; git or the base unreadable exits 2, never a pass.
  The matched text, a file's path that holds a hit, and every name are never printed.

Every case builds a scratch repository with a made-up identity, made-up names and made-up paths: the profile folder
`zarqanel`, the login `veltrask`, the names file's `Quilloran` and `zq`, the remote's owner `zarqowner`, the configured
identity `Plumbob Corp <robot@example.invalid>`, the path segment `kevrolt`. Each path is assembled at run time from
parts, so that this file holds no text the scan reads as a path. On the checkpoint every case is red: there is no
push-scan.py. The static cases read the program's source.

KP-052: no character outside printable ASCII is typed in this file."""
import ast
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.normpath(os.path.join(HERE, os.pardir))
PROG = os.path.join(WORKSPACE, "bridge", "cursor-bridge", "push-scan.py")

PROFILE_NAME = "zarqanel"
LOGIN = "veltrask"
EXTRA = "Quilloran"
SHORT = "zq"
OWNER = "zarqowner"
IDENT_NAME = "Plumbob Corp"
IDENT_MAIL = "robot" + "@example.invalid"
SEG = "kevrolt"
FWD, BACK, COLON = "/", chr(92), ":"
DRIVE_FWD = "D" + COLON + FWD + SEG + FWD + "notes"          # a drive letter, a forward slash and a segment
DRIVE_BACK = "E" + COLON + BACK + SEG + BACK + "notes"       # a drive letter, a backslash and a segment
USERS = FWD + "Us" + "ers" + FWD + SEG + FWD + "x"
HOMEP = FWD + "ho" + "me" + FWD + SEG + FWD + "x"
APPDATA = "Local" + FWD + "App" + "Data" + FWD + "Roaming"
PLACEHOLDERS = ["D" + COLON + FWD + "<root>" + FWD + "x", FWD + "Us" + "ers" + FWD + "<you>" + FWD + "x",
                FWD + "ho" + "me" + FWD + "<user>" + FWD + "x", "C" + COLON + BACK + "<folder>" + BACK + "y"]
NEVER_PRINTED = [PROFILE_NAME, LOGIN, EXTRA, OWNER, SEG, "Plumbob", "robot"]


class Scratch:
    """A repository with an origin remote named for OWNER, a base commit at origin/main, origin/HEAD pointing there,
    a profile folder named PROFILE_NAME holding .cursor-bridge/names.txt, and a global git config holding the
    configured identity."""

    def __init__(self, tmp_path, login=LOGIN, names=(EXTRA, SHORT), remote=True, base_files=None, base_message="base"):
        self.home = tmp_path / "profiles" / PROFILE_NAME
        (self.home / ".cursor-bridge").mkdir(parents=True)
        (self.home / ".cursor-bridge" / "names.txt").write_text("".join(n + "\n" for n in names), encoding="utf-8")
        self.gitconfig = tmp_path / "gitconfig"
        self.gitconfig.write_text("[user]\n\tname = %s\n\temail = %s\n[core]\n\tautocrlf = false\n" % (IDENT_NAME, IDENT_MAIL),
                                  encoding="utf-8")
        self.login = login
        self.repo = tmp_path / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        files = base_files if base_files is not None else {"README.md": "plain\n"}
        self.write(files)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", base_message)
        self.base = self.git("rev-parse", "HEAD")
        if remote:
            self.git("remote", "add", "origin", "https://github.com/%s/proj.git" % OWNER)
            self.git("update-ref", "refs/remotes/origin/main", self.base)
            self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")

    def env(self, **extra):
        e = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        e.update(HOME=str(self.home), USERPROFILE=str(self.home), USERNAME=self.login, USER=self.login,
                 GIT_CONFIG_GLOBAL=str(self.gitconfig), GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        e.update(extra)
        return e

    def git(self, *args, **env_extra):
        p = subprocess.run(["git"] + list(args), cwd=str(self.repo), capture_output=True, text=True,
                           env=self.env(**env_extra), timeout=120)
        assert p.returncode == 0, p.stderr
        return p.stdout.strip()

    def write(self, files):
        for name, text in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))

    def commit(self, files=None, message="change", author=None, committer=None, renames=()):
        for old, new in renames:
            self.git("mv", old, new)
        if files:
            self.write(files)
        self.git("add", "-A")
        args = ["commit", "-q", "-m", message]
        if author:
            args += ["--author", author]
        extra = {}
        if committer:
            extra = dict(GIT_COMMITTER_NAME=committer[0], GIT_COMMITTER_EMAIL=committer[1])
        self.git(*args, **extra)
        return self.git("rev-parse", "--short", "HEAD")

    def run(self, *args, cwd=None, **env_extra):
        p = subprocess.run([sys.executable, PROG] + list(args), cwd=str(cwd or self.repo), capture_output=True,
                           env=self.env(**env_extra), timeout=300)
        out = p.stdout.decode("utf-8", errors="replace") + p.stderr.decode("utf-8", errors="replace")
        return p.returncode, out


def hits(out):
    return sorted(line.strip() for line in out.splitlines() if line.startswith("push-scan: HIT "))


def silent(out, also=()):
    low = out.lower()
    for s in list(NEVER_PRINTED) + list(also):
        assert s.lower() not in low, "printed %r: %s" % (s, out)


def hit(short, place, kind):
    return "push-scan: HIT %s %s %s" % (short, place, kind)


# ---------------------------------------------------------------- the three exits

def test_r087_a_clean_range_passes_naming_its_commit_count(tmp_path):
    """R-087: exit 0 with `push-scan: OK - <n> commit(s)` where no commit of base..HEAD holds a path or a name."""
    s = Scratch(tmp_path)
    s.commit({"a.md": "first\n"}, message="one")
    s.commit({"b.md": "second\n"}, message="two")
    rc, out = s.run()
    assert rc == 0 and "push-scan: OK - 2 commit(s)" in out, out
    assert hits(out) == [], out


@pytest.mark.parametrize("case", ["dash-base", "unknown-base", "not-a-repository", "no-origin-head"])
def test_r087_git_or_the_base_unreadable_exits_2_never_a_pass(tmp_path, case):
    """R-087: exit 2 where git or the base cannot be read, and for a base beginning with `-`; never `OK`."""
    s = Scratch(tmp_path, remote=(case != "no-origin-head"))
    s.commit({"a.md": "x\n"})
    if case == "dash-base":
        rc, out = s.run("--", "-x")
    elif case == "unknown-base":
        rc, out = s.run("no-such-ref")
    elif case == "not-a-repository":
        plain = tmp_path / "plain"
        plain.mkdir()
        rc, out = s.run(cwd=plain)
    else:
        rc, out = s.run()
    assert rc == 2, out
    assert "push-scan: OK" not in out and hits(out) == [], out


def test_r087_names_are_never_taken_from_the_command_line(tmp_path):
    """R-087: the names are never on the command line: the program takes [<base>] alone, so a names option is a usage
    error (exit 2)."""
    s = Scratch(tmp_path)
    s.commit({"a.md": "x\n"})
    rc, out = s.run("--names", "someone")
    assert rc == 2 and "push-scan: OK" not in out, out


# ---------------------------------------------------------------- the base

def test_r087_the_default_base_is_origin_head_and_the_base_s_own_commit_is_not_read(tmp_path):
    """R-087: with no base the range is origin/<the default branch>..HEAD, read from origin/HEAD; the base commit itself
    (its message holding a name) is outside the range. A base given by its hash reads the same range."""
    s = Scratch(tmp_path, base_message="base by " + EXTRA)
    s.commit({"a.md": "x\n"})
    rc, out = s.run()
    assert rc == 0 and "push-scan: OK - 1 commit(s)" in out, out
    rc, out = s.run(s.base)
    assert rc == 0 and "push-scan: OK - 1 commit(s)" in out, out
    silent(out)


# ---------------------------------------------------------------- each place a hit can stand

def test_r087_a_path_and_a_name_in_the_message_are_two_hits_at_message(tmp_path):
    s = Scratch(tmp_path)
    h = s.commit({"a.md": "x\n"}, message="see %s for %s" % (DRIVE_FWD, EXTRA))
    rc, out = s.run()
    assert rc == 1, out
    assert hits(out) == sorted([hit(h, "message", "path"), hit(h, "message", "name")]), out
    silent(out)


def test_r087_a_name_in_another_identity_s_author_name_is_a_hit_at_author(tmp_path):
    s = Scratch(tmp_path)
    h = s.commit({"a.md": "x\n"}, author="Veltrask Q <someone@example.invalid>")
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "author", "name")], out
    silent(out)


def test_r087_a_name_in_another_identity_s_author_address_is_a_hit_at_author(tmp_path):
    s = Scratch(tmp_path)
    h = s.commit({"a.md": "x\n"}, author="Some One <%s@example.invalid>" % PROFILE_NAME)
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "author", "name")], out
    silent(out)


def test_r087_a_name_in_another_committer_is_a_hit_at_committer(tmp_path):
    s = Scratch(tmp_path)
    h = s.commit({"a.md": "x\n"}, committer=(EXTRA, "c@example.invalid"))
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "committer", "name")], out
    silent(out)


def test_r087_each_path_form_in_an_added_line_is_a_hit_at_its_line(tmp_path):
    """R-087: a drive letter with either slash and a segment, `/Users/<segment>`, `/home/<segment>`, a segment
    `AppData`; each added line is placed by its file's path and its number in the new file."""
    s = Scratch(tmp_path)
    text = "clean\n" + DRIVE_FWD + "\n" + DRIVE_BACK + "\n" + USERS + "\n" + HOMEP + "\n" + APPDATA + "\n"
    h = s.commit({"notes.md": text})
    rc, out = s.run()
    assert rc == 1, out
    assert hits(out) == sorted(hit(h, "line notes.md:%d" % n, "path") for n in (2, 3, 4, 5, 6)), out
    silent(out)


def test_r087_a_changed_file_s_added_line_is_numbered_in_the_new_file(tmp_path):
    s = Scratch(tmp_path, base_files={"doc.md": "a\nb\nc\n"})
    h = s.commit({"doc.md": "a\nsee " + USERS + "\nb\nc\n"})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line doc.md:2", "path")], out
    silent(out)


def test_r087_a_placeholder_segment_in_angle_brackets_passes(tmp_path):
    s = Scratch(tmp_path)
    s.commit({"notes.md": "".join(p + "\n" for p in PLACEHOLDERS)}, message="paths " + PLACEHOLDERS[1])
    rc, out = s.run()
    assert rc == 0 and "push-scan: OK - 1 commit(s)" in out, out


def test_r087_a_name_is_a_whole_word_in_any_letter_case(tmp_path):
    """R-087: each of the owner's names (the profile folder's name, the login, the names file's) as a whole word in
    any letter case; a name inside a longer word is no hit."""
    s = Scratch(tmp_path)
    text = PROFILE_NAME.upper() + " here\n" + PROFILE_NAME + "x and x" + LOGIN + "\nend " + LOGIN + ".\n" + EXTRA.lower() + "\n"
    h = s.commit({"notes.md": text})
    rc, out = s.run()
    assert rc == 1, out
    assert hits(out) == sorted(hit(h, "line notes.md:%d" % n, "name") for n in (1, 3, 4)), out
    silent(out)


def test_r087_a_name_shorter_than_four_characters_is_skipped_with_a_note_that_does_not_name_it(tmp_path):
    s = Scratch(tmp_path)
    s.commit({"notes.md": SHORT + " is a word here\n"})
    rc, out = s.run()
    assert rc == 0 and "push-scan: OK - 1 commit(s)" in out, out
    assert "shorter than four" in out, "the note on the short name: " + out
    silent(out, also=[SHORT])


def test_r087_a_name_in_an_added_file_s_name_is_placed_by_its_position_not_its_path(tmp_path):
    s = Scratch(tmp_path)
    h = s.commit({"a.md": "x\n", "b-%s.md" % PROFILE_NAME: "y\n"})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "file #2", "name")], out
    silent(out)


def test_r087_a_name_in_a_renamed_file_s_new_name_is_a_hit_by_position(tmp_path):
    s = Scratch(tmp_path, base_files={"plain.md": "some text that stays the same\n" * 5})
    h = s.commit(renames=[("plain.md", "%s-notes.md" % LOGIN)])
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "file #1", "name")], out
    silent(out)


def test_r087_a_line_of_a_file_whose_own_name_holds_a_hit_is_placed_by_the_file_s_position(tmp_path):
    s = Scratch(tmp_path)
    h = s.commit({"%s.md" % PROFILE_NAME: "clean\n" + DRIVE_FWD + "\n"})
    rc, out = s.run()
    assert rc == 1, out
    assert hits(out) == sorted([hit(h, "file #1", "name"), hit(h, "line #1:2", "path")]), out
    silent(out)


# ---------------------------------------------------------------- what is public

def test_r087_owner_2026_11_18_the_configured_identity_is_no_finding_anywhere(tmp_path):
    """The owner's decision of 2026-11-18 (rule 52): the configured identity's author and committer lines are no
    finding, and the names taken from it (its name and its address's local part) are public, so they pass in a
    message and in an added line too."""
    s = Scratch(tmp_path)
    s.commit({"notes.md": "written by %s\nmail %s\nthe robot ran\n" % (IDENT_NAME, IDENT_MAIL)}, message="by " + IDENT_NAME)
    rc, out = s.run()
    assert rc == 0 and "push-scan: OK - 1 commit(s)" in out, out
    silent(out)


def test_r087_a_derived_name_equal_to_the_remote_s_owner_is_dropped_and_not_printed(tmp_path):
    """R-087: a derived name equal to the owner segment of the remote's address is public with the repository: dropped,
    the note counting such names and printing none."""
    s = Scratch(tmp_path, login=OWNER)
    s.commit({"notes.md": "see https://github.com/%s/proj\n" % OWNER}, message="for " + OWNER)
    rc, out = s.run()
    assert rc == 0 and "push-scan: OK - 1 commit(s)" in out, out
    silent(out)


# ---------------------------------------------------------------- the program's shape (static)

def _tree():
    with open(PROG, encoding="utf-8") as f:
        return ast.parse(f.read())


def test_r087_d002_the_program_imports_bridge_env_and_builds_its_parser_at_top_level():
    """D-002 (`push_scan --> bridge_env`; `dump_cli -.-> push_scan`): a plain `import bridge_env` and a top-level
    `build_parser` whose only argument is the optional base."""
    tree = _tree()
    imports = [a.name for node in ast.walk(tree) if isinstance(node, ast.Import) for a in node.names]
    assert "bridge_env" in imports, imports
    assert any(isinstance(n, ast.FunctionDef) and n.name == "build_parser" for n in tree.body)


def test_r087_d004_every_child_process_is_bounded_by_a_timeout():
    """D-004 (p_push_scan reads git under a time limit): every subprocess call is a bounded one (no Popen) and passes
    `timeout=`."""
    calls = [n for n in ast.walk(_tree()) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess"
             and n.func.attr in ("run", "Popen", "check_output", "call", "check_call")]
    assert calls, "no subprocess call found (vacuous pass)"
    for c in calls:
        kw = {k.arg for k in c.keywords}
        assert c.func.attr != "Popen" and "timeout" in kw, "line %d: an unbounded child process" % c.lineno
