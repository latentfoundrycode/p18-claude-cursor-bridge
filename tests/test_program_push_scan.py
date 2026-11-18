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
import re
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

    def __init__(self, tmp_path, login=LOGIN, names=(EXTRA, SHORT), remote=True, base_files=None, base_message="base",
                 object_format=None):
        self.home = tmp_path / "profiles" / PROFILE_NAME
        (self.home / ".cursor-bridge").mkdir(parents=True)
        (self.home / ".cursor-bridge" / "names.txt").write_text("".join(n + "\n" for n in names), encoding="utf-8")
        self.gitconfig = tmp_path / "gitconfig"
        self.gitconfig.write_text("[user]\n\tname = %s\n\temail = %s\n[core]\n\tautocrlf = false\n" % (IDENT_NAME, IDENT_MAIL),
                                  encoding="utf-8")
        self.login = login
        self.repo = tmp_path / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main", *([("--object-format=" + object_format)] if object_format else []))
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
            path.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))

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
        # Python exits 2 for a missing script too, so an exit-2 case would pass before the program exists.
        assert os.path.isfile(PROG), "push-scan.py is not built: %s" % os.path.basename(PROG)
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
    if case == "dash-base":
        # refused by its first character, before git reads it: not merely git's later "not a commit"
        assert 'the base must not begin with "-"' in out and "not a commit" not in out, out


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


def test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped(tmp_path):
    """The owner's decision of 2026-11-18 (rule 52), where it bites: the profile folder's name equals the configured
    identity's user.name and the login equals its address's local part, so both are dropped as public and pass in the
    message, the author and committer lines and an added line; the identity's address holds a further searched name in
    its domain, which is no finding in the identity's own author and committer lines; that name is still searched in an
    added line, so the scan is not switched off."""
    s = Scratch(tmp_path)
    s.gitconfig.write_text("[user]\n\tname = %s\n\temail = %s\n[core]\n\tautocrlf = false\n"
                           % (PROFILE_NAME, LOGIN + "@" + EXTRA.lower() + ".invalid"), encoding="utf-8")
    short = s.commit({"notes.md": "by %s\nmail %s\nand %s\n" % (PROFILE_NAME, LOGIN, EXTRA)},
                     message="from %s and %s" % (PROFILE_NAME, LOGIN))
    rc, out = s.run()
    assert rc == 1, out
    assert hits(out) == [hit(short, "line notes.md:3", "name")], out
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


# ---------------------------------------------------------------- round 2: the patch read as git writes it (the reviews of round 1)

def _config(s, extra=""):
    s.gitconfig.write_text("[user]\n\tname = %s\n\temail = %s\n[core]\n\tautocrlf = false\n%s" % (IDENT_NAME, IDENT_MAIL, extra),
                           encoding="utf-8")


def test_r087_an_added_line_that_reads_like_a_file_header_is_scanned_in_its_hunk(tmp_path):
    """R-087 (round 2): an added line whose text begins with `++ ` is an added line of its hunk, never a file header:
    its path is a hit at its own line, and the lines after it stay placed in their file."""
    s = Scratch(tmp_path)
    h = s.commit({"notes.md": "ok\n++ " + DRIVE_FWD + "\nand " + EXTRA + "\n"})
    rc, out = s.run()
    assert rc == 1, out
    assert hits(out) == sorted([hit(h, "line notes.md:2", "path"), hit(h, "line notes.md:3", "name")]), out
    silent(out)


def test_r087_a_changed_file_with_a_space_in_its_name_is_read_by_its_whole_name(tmp_path):
    """R-087 (round 2): git writes an unquoted path that holds a space whole, so a file is named by its whole path;
    where its own name holds a name, its lines are placed by its position, never dropped."""
    hidden_name = PROFILE_NAME + " notes.md"
    s = Scratch(tmp_path, base_files={hidden_name: "plain\n", "other file.md": "plain\n"})
    h = s.commit({hidden_name: "plain\n" + DRIVE_FWD + "\n", "other file.md": "plain\nby " + EXTRA + "\n"})
    rc, out = s.run()
    assert rc == 1, out
    assert hits(out) == sorted([hit(h, "line other file.md:2", "name"), hit(h, "line #2:2", "path")]), out
    silent(out)


def test_r087_a_merge_where_one_side_renamed_a_file_reads_each_file_by_its_own_position(tmp_path):
    """R-087 (round 2): a merge's file list holds one path per combined status, a rename on one side included, so a
    line the merge itself adds to a file whose own name holds a name is a hit placed by that file's position."""
    hidden_name = LOGIN + "-notes.md"
    body = "".join("%d\n" % n for n in range(1, 9))
    s = Scratch(tmp_path, base_files={"old.md": body, hidden_name: "x\n"})
    s.git("checkout", "-q", "-b", "side")
    s.commit({"new.md": body + "9\n"}, renames=[("old.md", "new.md")], message="side")
    s.git("checkout", "-q", "main")
    # both sides change the renamed file, so the merge lists it with a combined status (RM) before the hidden file
    s.commit({"old.md": "0\n" + body[2:], hidden_name: "x\ny\n"}, message="main")
    s.git("merge", "-q", "--no-ff", "--no-commit", "side")
    s.write({hidden_name: "x\ny\n" + DRIVE_FWD + "\n"})
    s.git("add", "-A")
    s.git("commit", "-q", "-m", "merge")
    rc, out = s.run()
    assert rc == 1, out
    found = hits(out)
    assert len(found) == 1 and re.match(r"^push-scan: HIT [0-9a-f]+ line #[0-9]+:3 path$", found[0]), out
    silent(out)


def test_r087_a_control_character_in_a_printed_path_is_escaped(tmp_path):
    """R-087 (round 2): a file name is untrusted: a newline in a printed path is escaped, never written raw, so every
    line of the output is one of the program's own."""
    s = Scratch(tmp_path)
    (s.repo / "payload.txt").write_bytes(("plain\n" + DRIVE_FWD + "\n").encode("utf-8"))
    blob = s.git("hash-object", "-w", "payload.txt")
    (s.repo / "payload.txt").unlink()
    # git for Windows refuses a control character in a path while core.protectNTFS is on; the index takes it otherwise
    s.git("-c", "core.protectNTFS=false", "update-index", "--add", "--cacheinfo",
          "100644,%s,evil\npush-scan: OK - 9 commit(s)\nx.md" % blob)
    s.git("-c", "core.protectNTFS=false", "commit", "-q", "-m", "change")
    rc, out = s.run()
    assert rc == 1, out
    lines = [line for line in out.splitlines() if line.strip()]
    assert lines and all(line.startswith("push-scan: ") for line in lines), out
    assert "push-scan: OK - 9 commit(s)" not in lines, out
    assert len(hits(out)) == 1 and hits(out)[0].endswith(":2 path"), out


def test_r087_the_user_s_diff_settings_neither_hide_nor_misplace_a_hit(tmp_path):
    """R-087 (round 2): diff.relative, run from a subfolder, and diff.noprefix are the user's settings, not the scan's:
    every file of the commit is read and placed by its path."""
    s = Scratch(tmp_path, base_files={"sub/keep.md": "x\n"})
    _config(s, "[diff]\n\trelative = true\n\tnoprefix = true\n")
    h = s.commit({"notes.md": "plain\n" + DRIVE_FWD + "\n"})
    rc, out = s.run(cwd=s.repo / "sub")
    assert rc == 1 and hits(out) == [hit(h, "line notes.md:2", "path")], out


@pytest.mark.parametrize("cfg", ["[diff]\n\tnoprefix = true\n", "[diff]\n\tsrcPrefix = b/\n\tdstPrefix = a/\n"],
                         ids=["noprefix", "swapped"])
def test_r087_a_file_under_a_folder_named_like_a_prefix_is_read_whatever_the_user_s_prefixes(tmp_path, cfg):
    """R-087 (round 6, the supervisor's case after mutant n08 survived): the scan sets git's own a/ and b/ prefixes, so
    the user's diff.noprefix or swapped prefixes never make a file under a folder named b/ unreadable."""
    s = Scratch(tmp_path)
    _config(s, cfg)
    h = s.commit({"b/notes.md": "plain\n" + DRIVE_FWD + "\n"})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line b/notes.md:2", "path")], out


def test_r087_a_name_after_a_letter_that_lowercases_to_two_characters_is_found(tmp_path):
    """R-087 (round 2): a name matches in any letter case wherever it stands: a capital I with a dot above earlier in
    the line (two characters once lower-cased) moves nothing."""
    s = Scratch(tmp_path)
    h = s.commit({"notes.md": "\u0130stanbul by " + PROFILE_NAME + "\n"})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line notes.md:1", "name")], out
    silent(out)


def test_r087_a_form_feed_inside_an_added_line_moves_no_line_number(tmp_path):
    """R-087 (round 2): a patch's lines end at a newline only: a form feed or another separator inside an added line
    neither splits it nor moves the numbers of the lines after it."""
    s = Scratch(tmp_path)
    h = s.commit({"notes.md": "a\x0cb\x1cc\u2028d\n" + DRIVE_FWD + "\n"})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line notes.md:2", "path")], out


def test_r087_a_commit_s_signature_is_never_read_into_a_hit():
    """R-087 (round 2): with log.showSignature set, git prints a signature check before a commit's hash and its file
    list, text that can hold a path or a signer's name; the program turns it off for every git call."""
    with open(PROG, encoding="utf-8") as f:
        src = f.read()
    assert "log.showSignature=false" in src or "--no-show-signature" in src


# ---------------------------------------------------------------- round 3: what git shows is never narrowed (the reviews of round 2)

def _index_add(s, path, text=None, mode="100644", sha=None):
    """Adds one entry to the index by --cacheinfo (a path the file system may refuse, or a gitlink)."""
    if sha is None:
        (s.repo / "payload.txt").write_bytes(text.encode("utf-8"))
        sha = s.git("hash-object", "-w", "payload.txt")
        (s.repo / "payload.txt").unlink()
    s.git("-c", "core.protectNTFS=false", "update-index", "--add", "--cacheinfo", "%s,%s,%s" % (mode, sha, path))


def test_r087_a_submodule_hidden_by_the_user_s_setting_is_still_read(tmp_path):
    """R-087 (round 3): diff.ignoreSubmodules is the user's setting, not the scan's: a submodule entry whose own name
    holds a name is a hit at its file position."""
    s = Scratch(tmp_path)
    _config(s, "[diff]\n\tignoreSubmodules = all\n")
    _index_add(s, PROFILE_NAME + "-vendor", mode="160000", sha=s.base)
    s.git("commit", "-q", "-m", "vendor")
    h = s.git("rev-parse", "--short", "HEAD")
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "file #1", "name")], out
    silent(out)


def test_r087_a_submodule_hidden_by_the_commit_s_own_gitmodules_is_still_read(tmp_path):
    """R-087 (round 3): a commit's own .gitmodules is commit content: its `ignore = all` hides nothing from the scan,
    so a submodule entry whose own name holds a name is a hit at its file position."""
    s = Scratch(tmp_path)
    split = PROFILE_NAME[:4] + '""' + PROFILE_NAME[4:]
    gitmodules = '[submodule "v"]\n\tpath = "%s-vendor"\n\turl = ./v\n\tignore = all\n' % split
    _index_add(s, ".gitmodules", text=gitmodules)
    _index_add(s, PROFILE_NAME + "-vendor", mode="160000", sha=s.base)
    s.git("commit", "-q", "-m", "vendor")
    h = s.git("rev-parse", "--short", "HEAD")
    rc, out = s.run()
    assert rc == 1, out
    assert hit(h, "file #2", "name") in hits(out), out
    silent(out)


def test_r087_a_root_commit_in_the_range_is_read_whatever_log_show_root_says(tmp_path):
    """R-087 (round 3): log.showRoot is the user's setting, not the scan's: a root commit brought into the range by a
    merge of an unrelated history is read, its added lines and its file names."""
    s = Scratch(tmp_path)
    _config(s, "[log]\n\tshowRoot = false\n")
    s.git("checkout", "-q", "--orphan", "other")
    s.git("rm", "-rq", "--cached", ".")
    (s.repo / "README.md").unlink()
    root = s.commit({"imported.md": "plain\n" + DRIVE_FWD + "\n"}, message="imported")
    s.git("checkout", "-q", "-f", "main")
    s.git("merge", "-q", "--allow-unrelated-histories", "-m", "merge", "other")
    rc, out = s.run()
    assert rc == 1, out
    assert hits(out) == [hit(root, "line imported.md:2", "path")], out


def test_r087_a_blank_context_line_is_read_whatever_diff_suppress_blank_empty_says(tmp_path):
    """R-087 (round 3): diff.suppressBlankEmpty is the user's setting, not the scan's: a hunk whose context holds a blank
    line is read, never refused."""
    s = Scratch(tmp_path, base_files={"notes.md": "a\n\nb\n"})
    _config(s, "[diff]\n\tsuppressBlankEmpty = true\n")
    h = s.commit({"notes.md": "a\n\nb\n" + DRIVE_FWD + "\n"})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line notes.md:4", "path")], out


def test_r087_a_path_whose_escaped_form_holds_a_name_is_placed_by_its_position(tmp_path):
    """R-087 (round 3): the hit test on a path reads the text that would be printed too: a vertical tab before the rest
    of a login prints as a backslash and a v, which completes the name, so the line is placed by the file's position."""
    s = Scratch(tmp_path)
    _index_add(s, chr(11) + LOGIN[1:] + ".md", text="plain\n" + DRIVE_FWD + "\n")
    s.git("commit", "-q", "-m", "change")
    h = s.git("rev-parse", "--short", "HEAD")
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line #1:2", "path")], out
    silent(out)


def test_r087_a_format_character_in_a_printed_path_is_escaped(tmp_path):
    """R-087 (round 3): a format character (category Cf, such as the right-to-left override) in a printed path is
    escaped by its UTF-8 bytes, so a terminal cannot show a hit line reordered."""
    s = Scratch(tmp_path)
    _index_add(s, "a" + chr(0x202E) + "b.md", text="plain\n" + DRIVE_FWD + "\n")
    s.git("commit", "-q", "-m", "change")
    h = s.git("rev-parse", "--short", "HEAD")
    rc, out = s.run()
    escaped = '"a' + chr(92) + "342" + chr(92) + "200" + chr(92) + '256b.md"'
    assert rc == 1 and hits(out) == [hit(h, "line %s:2" % escaped, "path")], out
    assert chr(0x202E) not in out, out


def test_r087_a_submodule_s_own_diff_is_never_inlined():
    """R-087 (round 3): with diff.submodule set to diff, git inlines a submodule's own changes under paths that are not
    this repository's files; the program asks for the short form on both reads, so a submodule bump is read as one entry."""
    with open(PROG, encoding="utf-8") as f:
        src = f.read()
    assert src.count("--submodule=short") >= 2 and src.count("--ignore-submodules=none") >= 2


# ---------------------------------------------------------------- round 4: the objects a push sends (the reviews of round 3)

def test_r087_a_replaced_commit_is_read_as_the_push_sends_it(tmp_path):
    """R-087 (round 4): a replace ref changes what git shows for a commit, never what a push sends: the scan reads the
    original object, so a hit in a commit hidden behind a clean replacement is still a hit."""
    s = Scratch(tmp_path)
    x_short = s.commit({"notes.md": "plain\n" + DRIVE_FWD + "\n"}, message="with a path")
    x_full = s.git("rev-parse", "HEAD")
    s.git("checkout", "-q", "-b", "clean", s.base)
    s.commit({"notes.md": "plain\nclean\n"}, message="with a path")
    y_full = s.git("rev-parse", "HEAD")
    s.git("checkout", "-q", "main")
    s.git("replace", x_full, y_full)
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(x_short, "line notes.md:2", "path")], out


@pytest.mark.parametrize("attribute", ["-diff", "binary"])
def test_r087_a_text_file_the_commit_marks_binary_is_still_read(tmp_path, attribute):
    """R-087 (round 4): a commit's own .gitattributes is commit content: marking a text file `-diff` or `binary` hides
    none of its added lines from the scan."""
    s = Scratch(tmp_path)
    h = s.commit({".gitattributes": "*.md %s\n" % attribute, "notes.md": "plain\n" + DRIVE_FWD + "\n"})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line notes.md:2", "path")], out


# ---------------------------------------------------------------- round 5: content decides how a file is read (the resolution round)

NOTE_ONE = "push-scan: note - 1 binary file(s) not read"
# a real binary by git's rule (a NUL in its first 8000 bytes) whose bytes hold a path-shaped run on a line of their own
BINARY = b"\x89PNG\x00\x01\x02\n" + DRIVE_FWD.encode("ascii") + b"\n" + bytes(range(256)) * 4


def _info_attributes(s, text):
    (s.repo / ".git" / "info").mkdir(parents=True, exist_ok=True)
    (s.repo / ".git" / "info" / "attributes").write_text(text, encoding="utf-8")


def _shown(s, rev="HEAD"):
    """How git itself shows a commit with the user's settings (the precondition each case states before the scan)."""
    p = subprocess.run(["git", "show", "--format=", "--no-ext-diff", "--no-textconv", "--no-color", rev],
                       cwd=str(s.repo), capture_output=True, env=s.env(), timeout=120)
    assert p.returncode == 0, p.stderr
    return p.stdout.decode("utf-8", errors="replace")


def _force(s, how):
    """A setting that makes git show a file another way than its content: None, or one of the routes."""
    if how == "committed-diff":
        s.write({".gitattributes": "*.bin diff\n*.md -diff\n"})
    elif how == "info-diff":
        _info_attributes(s, "*.bin diff\n")
    elif how == "driver-text":
        _info_attributes(s, "*.bin diff=raw\n")
        _config(s, '[diff "raw"]\n\tbinary = false\n')
    elif how == "info-nodiff":
        _info_attributes(s, "*.md -diff\n")
    elif how == "info-binary":
        _info_attributes(s, "*.md binary\n")
    elif how == "big-file":
        _config(s, "[core]\n\tbigFileThreshold = 1\n")


def _merge_ours_then(s, files, message="merge"):
    """A merge of the branch side into main whose result is written by hand, so it differs from both parents."""
    s.git("merge", "-q", "--no-ff", "--no-commit", "-s", "ours", "side")
    s.write(files)
    s.git("add", "-A")
    s.git("commit", "-q", "-m", message)
    return s.git("rev-parse", "--short", "HEAD")


@pytest.mark.parametrize("how", [None, "committed-diff", "info-diff", "driver-text"])
def test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it(tmp_path, how):
    """R-087 (round 5): a file whose content is binary (a NUL in its first 8000 bytes) is never read, even where a
    commit's .gitattributes, .git/info/attributes or a diff driver makes git show its bytes as hunks: no false hit, and
    the note counts it without naming it."""
    s = Scratch(tmp_path)
    _force(s, how)
    s.commit({"img/blob.bin": BINARY, "img/other.bin": b"\x00" + BINARY[::-1]})   # never begins with a byte-order mark
    if how is not None:
        assert "@@" in _shown(s), "precondition: git shows the binary as hunks"
    rc, out = s.run()
    assert rc == 0 and hits(out) == [], out
    assert "push-scan: OK - 1 commit(s)" in out and "push-scan: note - 2 binary file(s) not read" in out, out
    assert "blob.bin" not in out and "other.bin" not in out, out


@pytest.mark.parametrize("how", [None, "info-diff", "driver-text"])
def test_r087_a_real_binary_a_merge_writes_is_counted_and_never_read(tmp_path, how):
    """R-087 (round 5): a merge's combined diff is read as an ordinary diff is: a binary the merge writes is counted,
    never read, however a local setting shows it; the note totals every binary result of the range (side's, main's and
    the merge's)."""
    s = Scratch(tmp_path, base_files={"blob.bin": bytes(range(256)) * 8})
    s.git("checkout", "-q", "-b", "side")
    s.commit({"blob.bin": bytes(range(254, -1, -1)) * 8}, message="side")   # FE FD: not a byte-order mark
    s.git("checkout", "-q", "main")
    s.commit({"blob.bin": bytes(range(128)) * 16}, message="main")
    _force(s, how)
    _merge_ours_then(s, {"blob.bin": BINARY})
    if how is not None:
        assert "@@@" in _shown(s), "precondition: git shows the merge's binary as combined hunks"
    rc, out = s.run()
    assert rc == 0 and hits(out) == [], out
    assert "push-scan: OK - 3 commit(s)" in out and "push-scan: note - 3 binary file(s) not read" in out, out
    assert "blob.bin" not in out, out


@pytest.mark.parametrize("how", ["info-nodiff", "info-binary", "big-file"])
def test_r087_a_text_file_a_local_setting_shows_as_binary_is_read(tmp_path, how):
    """R-087 (round 5): .git/info/attributes and core.bigFileThreshold are local settings that make git show a text
    file as binary; the scan reads it by its content, its added line a hit at its own line, never a pass and never a
    refusal."""
    s = Scratch(tmp_path, base_files={"notes.md": "plain\n"})
    _force(s, how)
    h = s.commit({"notes.md": "plain\n" + DRIVE_FWD + "\n"})
    assert "Binary files" in _shown(s), "precondition: git shows the text file as binary"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line notes.md:2", "path")], out


@pytest.mark.parametrize("how", ["info-nodiff", "info-binary"])
def test_r087_a_merge_s_resolved_line_in_a_text_file_shown_as_binary_is_read(tmp_path, how):
    """R-087 (round 5, B1 of round 4): a merge's combined diff ignores --text, so a resolved line in a text file a
    local setting shows as binary was hidden; the scan reads the file by its content, the resolved line a hit."""
    s = Scratch(tmp_path, base_files={"m.md": "1\n2\n3\n"})
    s.git("checkout", "-q", "-b", "side")
    s.commit({"m.md": "1\nSIDE\n3\n"}, message="side")
    s.git("checkout", "-q", "main")
    s.commit({"m.md": "1\nMAIN\n3\n"}, message="main")
    _force(s, how)
    h = _merge_ours_then(s, {"m.md": "1\n" + DRIVE_FWD + "\n3\n"})
    assert "Binary files" in _shown(s), "precondition: git shows the merge's text file as binary"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line m.md:2", "path")], out


def test_r087_a_merge_s_resolved_line_in_a_file_the_commit_marks_binary_is_read(tmp_path):
    """R-087 (round 5, B1 of round 4): a merge whose own .gitattributes marks a text file `-diff` hides none of its
    resolved lines."""
    s = Scratch(tmp_path, base_files={"m.md": "1\n2\n3\n"})
    s.git("checkout", "-q", "-b", "side")
    s.commit({"m.md": "1\nSIDE\n3\n"}, message="side")
    s.git("checkout", "-q", "main")
    s.commit({"m.md": "1\nMAIN\n3\n", ".gitattributes": "*.md -diff\n"}, message="main")
    h = _merge_ours_then(s, {"m.md": "1\n" + DRIVE_FWD + "\n3\n"})
    assert "Binary files" in _shown(s), "precondition: git shows the merge's text file as binary"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line m.md:2", "path")], out


@pytest.mark.parametrize("how", [None, "info-nodiff"])
def test_r087_a_duplicate_added_line_counts_however_git_shows_the_file(tmp_path, how):
    """R-087 (round 5): a line added again where the parent already holds it is an added line (git's meaning): read
    from hunks or by the scan's own line diff, it is a hit at its new line, and the old one is not."""
    line = "see " + DRIVE_FWD
    s = Scratch(tmp_path, base_files={"notes.md": line + "\nbase\n"})
    _force(s, how)
    h = s.commit({"notes.md": line + "\nbase\n" + line + "\n"})
    if how is not None:
        assert "Binary files" in _shown(s), "precondition: git shows the text file as binary"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line notes.md:3", "path")], out


def test_r087_a_duplicate_line_a_merge_adds_against_both_parents_counts(tmp_path):
    """R-087 (round 5): in a merge a line counts where it is added against every parent, position by position, so a
    copy of a line each parent holds once, added once more by the merge, is one hit."""
    line = "see " + DRIVE_FWD
    s = Scratch(tmp_path, base_files={"m.md": "a\nb\n"})
    s.git("checkout", "-q", "-b", "side")
    s.commit({"m.md": line + "\na\nb\n"}, message="side")
    s.git("checkout", "-q", "main")
    s.commit({"m.md": "a\nb\n" + line + "\n"}, message="main")
    _force(s, "info-nodiff")
    _merge_ours_then(s, {"m.md": line + "\na\nb\n" + line + "\n" + line + "\n"})
    rc, out = s.run()
    assert rc == 1, out
    merge_hits = [x for x in hits(out) if re.match(r"^push-scan: HIT [0-9a-f]+ line m\.md:[45] path$", x)]
    side_main = [x for x in hits(out) if x not in merge_hits]
    assert len(merge_hits) == 1 and len(side_main) == 2, out


@pytest.mark.parametrize("bom,codec", [(b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be")])
def test_r087_a_utf16_file_with_a_byte_order_mark_is_read_as_text(tmp_path, bom, codec):
    """R-087 (round 5): Windows PowerShell 5.1 writes UTF-16 with a byte-order mark, which git shows as binary; the scan
    decodes it, so a path on its second line is a hit at that line."""
    s = Scratch(tmp_path)
    h = s.commit({"list.txt": bom + ("Directory: x\r\n" + DRIVE_BACK + "\r\n").encode(codec)})
    assert "Binary files" in _shown(s), "precondition: git shows the UTF-16 file as binary"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line list.txt:2", "path")], out


def test_r087_a_changed_utf16_file_reports_only_its_new_lines(tmp_path):
    """R-087 (round 5): a changed UTF-16 file is read by its lines added against the parent, so a path the parent
    already held is not reported again and a new one is a hit at its line."""
    bom, codec = b"\xff\xfe", "utf-16-le"
    s = Scratch(tmp_path, base_files={"list.txt": bom + ("one\r\n" + DRIVE_BACK + "\r\n").encode(codec)})
    h = s.commit({"list.txt": bom + ("one\r\n" + DRIVE_BACK + "\r\ntwo\r\n" + USERS + "\r\n").encode(codec)})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line list.txt:4", "path")], out


def test_r087_a_utf16_file_rewritten_as_utf8_is_read_never_refused(tmp_path):
    """R-087 (round 5): a text file whose parent was binary to git (here UTF-16) shows as binary; the scan reads the new
    text and never ends the scan for it."""
    bom, codec = b"\xff\xfe", "utf-16-le"
    s = Scratch(tmp_path, base_files={"list.txt": bom + "plain\r\n".encode(codec)})
    h = s.commit({"list.txt": "plain\n" + DRIVE_FWD + "\n"})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line list.txt:2", "path")], out


@pytest.mark.parametrize("nul_at,binary", [(7999, True), (8000, False)])
def test_r087_git_s_content_rule_decides_at_its_8000th_byte(tmp_path, nul_at, binary):
    """R-087 (round 5): a NUL inside the first 8000 bytes makes a file binary (counted, not read: the accepted limit for
    a text file holding one); a NUL after them leaves it text, its lines read."""
    s = Scratch(tmp_path)
    data = b"x" * nul_at + b"\x00\n" + DRIVE_FWD.encode("ascii") + b"\n"
    h = s.commit({"data.txt": data})
    rc, out = s.run()
    if binary:
        assert rc == 0 and hits(out) == [] and NOTE_ONE in out, out
    else:
        assert rc == 1 and hits(out) == [hit(h, "line data.txt:2", "path")], out


def test_r087_entries_without_content_to_read_never_end_the_scan(tmp_path):
    """R-087 (round 5): a deleted file, a mode change, a pure rename, a symbolic link, a type change, a submodule and an
    octopus merge carry no added text a hit could stand in: the file list and the patch agree and the scan passes."""
    s = Scratch(tmp_path, base_files={"gone.md": "x\n", "run.sh": "echo\n", "old.md": "same\n", "t.md": "plain\n"})
    s.git("rm", "-q", "gone.md")
    s.git("commit", "-q", "-m", "delete")
    s.git("update-index", "--chmod=+x", "run.sh")
    s.git("commit", "-q", "-m", "mode")
    s.git("mv", "old.md", "new.md")
    s.git("commit", "-q", "-m", "rename")
    _index_add(s, "link", text="new.md", mode="120000")
    _index_add(s, "vendor", mode="160000", sha=s.base)
    s.git("commit", "-q", "-m", "link and submodule")
    _index_add(s, "t.md", text="new.md", mode="120000")
    s.git("commit", "-q", "-m", "type change")
    s.git("checkout", "-q", "-b", "o1")
    s.commit({"a.md": "a\n"}, message="o1")
    s.git("checkout", "-q", "-b", "o2", "main")
    s.commit({"b.md": "b\n"}, message="o2")
    s.git("checkout", "-q", "main")
    s.git("merge", "-q", "--no-ff", "-m", "octopus", "o1", "o2")
    rc, out = s.run()
    assert rc == 0 and hits(out) == [], out
    assert "push-scan: OK - 8 commit(s)" in out, out


def test_r087_a_type_change_reads_the_new_entry(tmp_path):
    """R-087 (round 5): a type change (a file made a symbolic link) is one record and two patch sections, a deletion and
    an addition: the scan reads the new entry by its class, its target a hit at line 1, and never ends the scan."""
    s = Scratch(tmp_path, base_files={"t.md": "plain\n"})
    _index_add(s, "t.md", text=DRIVE_FWD, mode="120000")
    s.git("commit", "-q", "-m", "type change")
    h = s.git("rev-parse", "--short", "HEAD")
    assert " T" in s.git("show", "--format=", "--raw", "HEAD"), "precondition: git lists a type change"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line t.md:1", "path")], out


def test_r087_a_sha256_repository_is_read_with_its_own_ids(tmp_path):
    """R-087 (round 5): ids are the repository's hash length: in a SHA-256 repository the empty tree, the full ids and
    the content rule work as in a SHA-1 one."""
    s = Scratch(tmp_path, object_format="sha256", base_files={"notes.md": "plain\n"})
    _force(s, "info-nodiff")
    h = s.commit({"notes.md": "plain\n" + DRIVE_FWD + "\n", "blob.bin": BINARY})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line notes.md:2", "path")], out
    assert NOTE_ONE in out, out


LARGE = "".join("plain line %06d\n" % n for n in range(80000))   # about 1.4 MiB of text, above the 1 MiB bound


def test_r087_a_commit_s_attribute_never_decides_how_a_large_text_file_is_read(tmp_path):
    """R-087 (round 5): a commit's own .gitattributes marking a large text file `-diff` decides nothing: git shows it
    as hunks to the scan (no tree's attributes reach the read), so its added line is a hit and the scan never ends on
    the size bound because of commit content."""
    s = Scratch(tmp_path, base_files={"big.md": LARGE})
    h = s.commit({".gitattributes": "*.md -diff\n", "big.md": LARGE + DRIVE_FWD + "\n"})
    assert "Binary files" in _shown(s), "precondition: git shows the file as binary under the commit's attribute"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line big.md:80001", "path")], out


def test_r087_a_large_text_file_a_local_setting_shows_as_binary_is_read(tmp_path):
    """R-087 (round 6, the second resolution withdrew round 5's 1 MiB refusal): a text file above 1 MiB that a local
    setting shows as binary is read by the trimmed line diff, its added line a hit, never a refusal."""
    s = Scratch(tmp_path, base_files={"big.md": LARGE})
    _force(s, "info-nodiff")
    h = s.commit({"big.md": LARGE + DRIVE_FWD + "\n"})
    assert "Binary files" in _shown(s), "precondition: git shows the file as binary"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line big.md:80001", "path")], out


def test_r087_no_attribute_decides_and_ids_are_full():
    """R-087 (round 5): the reads take no tree's attributes (--attr-source of the empty tree, an empty
    core.attributesFile), read full ids (--full-index on the patch, --no-abbrev on the raw list) and never read every
    file as text."""
    with open(PROG, encoding="utf-8") as f:
        src = f.read()
    assert "--attr-source" in src and "core.attributesFile=" in src, src[:0]
    assert "--full-index" in src and "--no-abbrev" in src and "--raw" in src
    assert '"--text"' not in src and "'--text'" not in src


# ---------------------------------------------------------------- round 6: the second resolution (round 5's regressions)

@pytest.mark.parametrize("tail", ["", "x"])
def test_r087_a_byte_order_mark_before_plain_text_never_hides_its_lines(tmp_path, tail):
    """R-087 (round 6, F1): a file whose first two bytes are a UTF-16 byte-order mark but whose rest is plain text (git
    shows it as text) is read without its NULs, so its path line is a hit, whatever the length parity."""
    s = Scratch(tmp_path)
    h = s.commit({"notes.txt": b"\xff\xfe" + ("hello\nsee " + DRIVE_FWD + "\n" + tail).encode("ascii")})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line notes.txt:2", "path")], out


@pytest.mark.parametrize("tail", ["", "x"])
def test_r087_a_utf16_file_appended_in_another_encoding_is_read(tmp_path, tail):
    """R-087 (round 6, F1): Windows PowerShell 5.1 writes UTF-16 with a byte-order mark and another shell's `>>`
    appends UTF-8: the appended path line is read, never counted as binary, whatever the length parity."""
    s = Scratch(tmp_path)
    data = b"\xff\xfe" + "Directory: x\r\n".encode("utf-16-le") + ("see " + DRIVE_FWD + "\r\n" + tail).encode("ascii")
    h = s.commit({"out.txt": data})
    assert "Binary files" in _shown(s), "precondition: git shows the mixed file as binary"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line out.txt:2", "path")], out
    assert "binary file(s) not read" not in out, out


@pytest.mark.parametrize("with_path", [True, False])
def test_r087_utf16_appended_at_an_odd_offset_is_read(tmp_path, with_path):
    """R-087 (round 6, F1, Review A's sequence): PowerShell `>` (UTF-16LE with a mark), an odd-length `>>` of plain
    bytes, then a PowerShell `>>` appending UTF-16LE at an odd offset: the path is read (a hit at line 3); without it
    the scan passes with no note."""
    s = Scratch(tmp_path)
    last = (DRIVE_FWD if with_path else "plain") + "\r\n"
    data = b"\xff\xfe" + "hello\r\n".encode("utf-16-le") + b"ab\n" + last.encode("utf-16-le")
    h = s.commit({"f.txt": data})
    rc, out = s.run()
    if with_path:
        assert rc == 1 and hits(out) == [hit(h, "line f.txt:3", "path")], out
    else:
        assert rc == 0 and hits(out) == [] and "binary file(s) not read" not in out, out


@pytest.mark.parametrize("with_path", [False, True])
def test_r087_a_clean_merge_of_a_large_text_file_passes(tmp_path, with_path):
    """R-087 (round 6, F2): a clean merge where both branches changed a text file over 1 MiB in different places adds
    no line against both parents, so git prints no section for it and the scan reads nothing there: OK, never refused;
    its twin, a merge adding a path line against both parents, is a hit."""
    lines = ["plain line %06d\n" % n for n in range(80000)]
    s = Scratch(tmp_path, base_files={"lock.json": "".join(lines)})
    s.git("checkout", "-q", "-b", "side")
    side = list(lines)
    side[1] = "side line\n"
    s.commit({"lock.json": "".join(side)}, message="side")
    s.git("checkout", "-q", "main")
    main = list(lines)
    main[-2] = "main line\n"
    s.commit({"lock.json": "".join(main)}, message="main")
    if with_path:
        both = list(lines)
        both[1] = "side line\n"
        both[-2] = "main line\n"
        both[40000] = DRIVE_FWD + "\n"
        h = _merge_ours_then(s, {"lock.json": "".join(both)})
    else:
        s.git("merge", "-q", "--no-ff", "-m", "merge", "side")
    rc, out = s.run()
    if with_path:
        assert rc == 1 and hits(out) == [hit(h, "line lock.json:40001", "path")], out
    else:
        assert rc == 0 and hits(out) == [] and "push-scan: OK - 3 commit(s)" in out, out


def test_r087_an_octopus_re_adding_a_parent_s_line_elsewhere_is_read(tmp_path):
    """R-087 (round 6, F2): an octopus merge that adds again, at a new position, a line one parent holds is a line added
    against every parent: git prints it and the scan reads it, a hit."""
    line = "see " + DRIVE_FWD
    s = Scratch(tmp_path, base_files={"m.md": "a\nb\nc\n"})
    s.git("checkout", "-q", "-b", "o1")
    o1 = s.commit({"m.md": line + "\na\nb\nc\n"}, message="o1")
    s.git("checkout", "-q", "-b", "o2", "main")
    s.commit({"o2.md": "x\n"}, message="o2")
    s.git("checkout", "-q", "main")
    s.git("merge", "-q", "--no-ff", "--no-commit", "-s", "ours", "o1", "o2")
    s.write({"m.md": line + "\na\nb\nc\n" + line + "\n", "o2.md": "x\n"})
    s.git("add", "-A")
    s.git("commit", "-q", "-m", "octopus")
    h = s.git("rev-parse", "--short", "HEAD")
    rc, out = s.run()
    assert rc == 1 and hits(out) == sorted([hit(o1, "line m.md:1", "path"), hit(h, "line m.md:5", "path")]), out


def test_r087_type_changes_to_and_from_a_submodule_are_read(tmp_path):
    """R-087 (round 6, F3): a result of mode 160000 is a submodule whatever the status: a file made a submodule, a
    symbolic link made a submodule, and a submodule made a file are read without asking for a blob of a commit id, the
    file's path line a hit."""
    s = Scratch(tmp_path, base_files={"lib": "plain\n", "ln": "plain\n"})
    _index_add(s, "ln", text="lib", mode="120000")
    s.git("commit", "-q", "-m", "symlink")
    _index_add(s, "lib", mode="160000", sha=s.base)
    _index_add(s, "ln", mode="160000", sha=s.base)
    s.git("commit", "-q", "-m", "to submodules")
    assert s.git("show", "--format=", "--raw", "HEAD").count(" T\t") == 2, "precondition: two type changes"
    _index_add(s, "lib", text="plain\n" + DRIVE_FWD + "\n")
    s.git("commit", "-q", "-m", "back to a file")
    h = s.git("rev-parse", "--short", "HEAD")
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line lib:2", "path")], out


@pytest.mark.parametrize("result", ["submodule", "file"])
def test_r087_a_merge_between_a_file_and_a_submodule_is_read(tmp_path, result):
    """R-087 (round 6, F3): a merge where one parent has a file and the other a submodule is a combined status: a
    submodule result is read as a submodule, never as a blob; a file result holding a path is a hit."""
    s = Scratch(tmp_path, base_files={"lib": "plain\n"})
    s.git("checkout", "-q", "-b", "side")
    _index_add(s, "lib", mode="160000", sha=s.base)
    s.git("commit", "-q", "-m", "side")
    s.git("checkout", "-q", "-f", "main")
    s.commit({"lib": "plain\nmain\n"}, message="main")
    other = s.git("rev-parse", "HEAD")   # a gitlink differing from side's, so the merge lists the path
    s.git("merge", "-q", "--no-ff", "--no-commit", "-s", "ours", "side")
    if result == "submodule":
        _index_add(s, "lib", mode="160000", sha=other)
    else:
        _index_add(s, "lib", text="plain\nmerged\n" + DRIVE_FWD + "\n")
    s.git("commit", "-q", "-m", "merge")
    h = s.git("rev-parse", "--short", "HEAD")
    assert s.git("show", "--format=", "--raw", "HEAD").startswith("::"), "precondition: a combined record"
    rc, out = s.run()
    if result == "submodule":
        assert rc == 0 and hits(out) == [] and "push-scan: OK - 3 commit(s)" in out, out
    else:
        assert rc == 1 and hits(out) == [hit(h, "line lib:3", "path")], out


def test_r087_a_one_line_edit_of_a_large_utf16_file_is_read(tmp_path):
    """R-087 (round 6, F4): the line diff trims the common leading and trailing lines, so a one-line edit of an ordinary
    UTF-16 file of 7,100 unique lines (about 0.7 MB) is read quickly and never refused."""
    lines = ["entry %05d of the exported list, padded to fifty chars\r\n" % n for n in range(7100)]
    s = Scratch(tmp_path, base_files={"list.txt": b"\xff\xfe" + "".join(lines).encode("utf-16-le")})
    new = list(lines)
    new[3500] = DRIVE_BACK + "\r\n"
    h = s.commit({"list.txt": b"\xff\xfe" + "".join(new).encode("utf-16-le")})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line list.txt:3501", "path")], out


def test_r087_a_middle_too_costly_to_diff_is_read_whole(tmp_path):
    """R-087 (round 6, F4): content shaped to make the line diff slow (thousands of short repeated lines) is never
    diffed past the work bound: the whole changed middle counts as added, so a path inside it is a hit, never a
    refusal and never a hang."""
    pre = ["abcd"[n % 4] + "\r\n" for n in range(9000)]
    res = ["abcd"[(n * 7) % 4] + "\r\n" for n in range(9000)]
    res[4500] = DRIVE_BACK + "\r\n"
    s = Scratch(tmp_path, base_files={"many.txt": b"\xff\xfe" + "".join(pre).encode("utf-16-le")})
    h = s.commit({"many.txt": b"\xff\xfe" + "".join(res).encode("utf-16-le")})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line many.txt:4501", "path")], out


def test_r087_a_non_ascii_name_in_a_utf16_file_is_read(tmp_path):
    """R-087 (round 6, L1): a name holding a letter outside ASCII is read in a UTF-16 file through its UTF-16 view (the
    NUL-removed view cannot spell it), a hit at its line, and the name is never printed."""
    accented = "Z" + chr(0xF6) + "lvarin"
    s = Scratch(tmp_path, names=(EXTRA, SHORT, accented))
    h = s.commit({"list.txt": b"\xff\xfe" + ("plain\r\nby " + accented + "\r\n").encode("utf-16-le")})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line list.txt:2", "name")], out
    silent(out, also=[accented])


def test_r087_a_far_edit_of_a_large_repetitive_file_does_not_read_an_old_line(tmp_path):
    """R-087 (round 6, L4): the common leading and trailing lines are trimmed before the work bound, so a one-line edit
    far from a path line the parent already holds, in a large file of repeated lines, reads only the edit: no hit."""
    pre = ["abcd"[n % 4] + "\r\n" for n in range(9000)]
    pre[9] = DRIVE_BACK + "\r\n"
    res = list(pre)
    res[8000] = "zz\r\n"
    s = Scratch(tmp_path, base_files={"many.txt": b"\xff\xfe" + "".join(pre).encode("utf-16-le")})
    s.commit({"many.txt": b"\xff\xfe" + "".join(res).encode("utf-16-le")})
    rc, out = s.run()
    assert rc == 0 and hits(out) == [] and "push-scan: OK - 1 commit(s)" in out, out


def test_r087_a_binary_beginning_with_a_byte_order_mark_is_read_not_counted(tmp_path):
    """R-087 (round 6, L1 and its accepted limit): a blob whose first two bytes are a UTF-16 byte-order mark is read in
    both views and never counted as binary, even where its bytes are a real binary's; with no path-shaped run in it,
    the scan passes with no note."""
    s = Scratch(tmp_path)
    s.commit({"marked.bin": b"\xff\xfe" + bytes(range(256)) * 4})
    rc, out = s.run()
    assert rc == 0 and hits(out) == [] and "push-scan: OK - 1 commit(s)" in out, out
    assert "binary file(s) not read" not in out, out

# ---------------------------------------------------------------- round 7: text that is not UTF-8 (Review B, round 4)

E_ACUTE = "\u00e9"
NONASCII_NAME = "Z" + E_ACUTE + "lvarn"
E_FORMS = {
    "drive-forward": "D" + COLON + FWD + E_ACUTE + SEG + FWD + "x",
    "drive-back": "E" + COLON + BACK + E_ACUTE + SEG + BACK + "x",
    "users": FWD + "Us" + "ers" + FWD + E_ACUTE + SEG + FWD + "x",
    "home": FWD + "ho" + "me" + FWD + E_ACUTE + SEG + FWD + "x",
}


def _commit_with_encoding(s, tmp_path, message_bytes, encoding, files=None):
    s.write(files or {"a.md": "plain\n"})
    s.git("add", "-A")
    (tmp_path / "message.txt").write_bytes(message_bytes)
    s.git("-c", "i18n.commitEncoding=" + encoding, "commit", "-q", "-F", str(tmp_path / "message.txt"))
    return s.git("rev-parse", "--short", "HEAD")


@pytest.mark.parametrize("form", sorted(E_FORMS))
def test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found(tmp_path, form):
    """R-087 (round 7, Review B round 4): a commit whose message git records as ISO-8859-1 (its `encoding` header,
    from i18n.commitEncoding) and whose path's first segment begins with a non-ASCII letter is a hit at message."""
    s = Scratch(tmp_path)
    h = _commit_with_encoding(s, tmp_path, ("note " + E_FORMS[form] + "\n").encode("latin-1"), "ISO-8859-1")
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "message", "path")], out


def test_r087_a_message_whose_encoding_python_does_not_know_is_read_as_utf8(tmp_path):
    """R-087 (round 7): a commit whose `encoding` header names an encoding Python does not know is read as UTF-8, as
    every other commit is, so its path is still found."""
    s = Scratch(tmp_path)
    h = _commit_with_encoding(s, tmp_path, ("note " + E_FORMS["drive-forward"] + "\n").encode("utf-8"), "x-unknown-zq")
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "message", "path")], out


@pytest.mark.parametrize("form", sorted(E_FORMS))
def test_r087_a_path_in_a_file_written_in_another_encoding_is_found(tmp_path, form):
    """R-087 (round 7, Review B round 4): a text file written in ISO-8859-1 whose added line holds a path beginning with
    a non-ASCII letter is a hit: a byte no decoding reads still begins a path's segment."""
    s = Scratch(tmp_path)
    h = s.commit({"latin.txt": ("plain\n" + E_FORMS[form] + "\n").encode("latin-1")})
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "line latin.txt:2", "path")], out


@pytest.mark.parametrize("text", ["drive = \"C" + COLON + BACK + BACK + "\"", "root = \"D" + COLON + FWD + "\"",
                                  "see D" + COLON + FWD + " x"],
                         ids=["backslash-quote", "slash-quote", "space"])
def test_r087_ascii_punctuation_after_a_drive_still_begins_no_segment(tmp_path, text):
    """R-087 (round 7): only a letter, a digit, `_`, `.`, `-` or a non-ASCII character that is not a space begins a
    path's segment; ASCII punctuation and a space after a drive's separator still pass, as code that names a bare
    drive does."""
    s = Scratch(tmp_path)
    s.commit({"code.py": text + "\n"})
    rc, out = s.run()
    assert rc == 0 and hits(out) == [] and "push-scan: OK - 1 commit(s)" in out, out


def test_r087_a_message_header_naming_an_encoding_that_changes_ascii_is_read_as_utf8(tmp_path):
    """R-087 (round 7, the supervisor's case after its mutants): a commit whose `encoding` header names UTF-16, which
    does not read ASCII as ASCII, is read as UTF-8, so an ASCII path in its message is still found."""
    s = Scratch(tmp_path)
    h = _commit_with_encoding(s, tmp_path, ("note " + DRIVE_FWD + "\n").encode("utf-8"), "UTF-16")
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "message", "path")], out


def test_r087_a_non_ascii_name_in_an_ordinary_utf8_message_is_found(tmp_path):
    """R-087 (round 7, the supervisor's case after its mutants): a commit with no `encoding` header is read as UTF-8, so
    a searched name holding a non-ASCII letter matches as written."""
    s = Scratch(tmp_path, names=(NONASCII_NAME,))
    h = s.commit({"a.md": "plain\n"}, message="thanks " + NONASCII_NAME)
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "message", "name")], out
    silent(out, also=(NONASCII_NAME,))


# ---------------------------------------------------------------- the third resolution: a header never hides a hit

@pytest.mark.parametrize("encoding,prefix,form", [
    ("ISO-2022-JP", b"note \x1b$B", "users"),
    ("ISO-2022-JP", b"note \x1b$B", "home"),
    ("Shift_JIS", b"note \x81", "drive-back"),
    ("Big5", b"note \xa1", "drive-back"),
    ("unicode_escape", b"note ", "escaped-drive"),
], ids=["iso2022jp-users", "iso2022jp-home", "shiftjis-drive", "big5-drive", "unicode-escape-drive"])
def test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds(tmp_path, encoding, prefix, form):
    """R-087 (the third resolution, round 7's regression found by both reviewers): whatever encoding a commit's header
    names, a path the UTF-8 reading of its message finds is a hit (round 6 found each; round 7's decoding hid it)."""
    paths = {"users": USERS, "home": HOMEP, "drive-back": DRIVE_BACK,
             "escaped-drive": "E" + COLON + BACK + "new" + BACK + SEG}
    s = Scratch(tmp_path)
    h = _commit_with_encoding(s, tmp_path, prefix + paths[form].encode("ascii") + b"\n", encoding)
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "message", "path")], out


def test_r087_an_encoding_header_never_hides_a_name_the_utf8_reading_finds(tmp_path):
    """R-087 (the third resolution): a Shift_JIS lead byte before a searched name never hides the name."""
    s = Scratch(tmp_path)
    h = _commit_with_encoding(s, tmp_path, b"thanks \x81" + EXTRA.encode("ascii") + b"\n", "Shift_JIS")
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, "message", "name")], out


def test_r087_a_non_ascii_identity_stays_exempt_under_another_encoding_header(tmp_path):
    """R-087 (the third resolution; the owner's decision of 2026-11-18): git writes the author and committer lines as
    UTF-8 whatever i18n.commitEncoding says, so a configured identity holding a non-ASCII letter stays no finding, and
    a searched name equal to part of it is not found in those lines."""
    s = Scratch(tmp_path, names=("Vandrelq",))
    s.git("config", "user.name", "Zo" + E_ACUTE + " Vandrelq")
    s.git("config", "user.email", "zo" + "@example.invalid")
    _commit_with_encoding(s, tmp_path, b"plain\n", "ISO-8859-1")
    rc, out = s.run()
    assert rc == 0 and hits(out) == [] and "push-scan: OK - 1 commit(s)" in out, out


# ---------------------------------------------------------------- the third resolution: ESC and SO begin a segment

JAPAN = "\u65e5\u672c"
HAN = "\ud55c"


@pytest.mark.parametrize("where,codec,text", [
    ("message-header", "iso2022_jp", "D" + COLON + FWD + JAPAN + SEG + FWD + "x"),
    ("message-plain", "iso2022_jp", FWD + "Us" + "ers" + FWD + JAPAN + SEG + FWD + "x"),
    ("file", "iso2022_jp", "D" + COLON + BACK + JAPAN + SEG + BACK + "x"),
    ("file", "iso2022_kr", FWD + "Us" + "ers" + FWD + HAN + SEG + FWD + "x"),
], ids=["jp-message-with-header", "jp-message-without-header", "jp-file-line", "kr-file-line"])
def test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found(tmp_path, where, codec, text):
    """R-087 (the third resolution, Review A's vote): the ISO-2022 encodings write a segment's non-ASCII first
    character after an ASCII shift (ESC, or SO), so ESC and SO begin a segment: the path is a hit in a message, with or
    without an encoding header, and in a file's added line."""
    s = Scratch(tmp_path)
    data = text.encode(codec)
    if codec == "iso2022_kr":
        # real ISO-2022-KR text designates once, at its start, so SO itself follows the separator
        data = b"\x1b$)C" + data.replace(b"\x1b$)C", b"")
    if where == "file":
        h = s.commit({"jp.txt": b"plain\n" + data + b"\n"})
        place = "line jp.txt:2"
    elif where == "message-header":
        h = _commit_with_encoding(s, tmp_path, b"note " + data + b"\n", "ISO-2022-JP")
        place = "message"
    else:
        s.write({"a.md": "plain\n"})
        s.git("add", "-A")
        (tmp_path / "message.txt").write_bytes(b"note " + data + b"\n")
        s.git("commit", "-q", "-F", str(tmp_path / "message.txt"))
        h = s.git("rev-parse", "--short", "HEAD")
        place = "message"
    rc, out = s.run()
    assert rc == 1 and hits(out) == [hit(h, place, "path")], out
