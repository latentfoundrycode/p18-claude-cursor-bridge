"""TASK-073, the supervisor's acceptance tests (R-094): the installer refuses unknown words and keeps a named copy.

enforces: docs/REQUIREMENTS.md R-094; docs/BUILD_PLAN.md, TASK-073's Done when; docs/DESIGN.md, C9 and C11.

The forms these tests pin (bridge/cursor-bridge/bridge-install.py):
- The known words, exactly: `--target <path>`, `--dry-run`, `--anyway`, `--rollback` with an optional `<version>`
  (the next word, when it does not begin with `-`), `--keep <version>` (or `--keep none`). Every word is read
  before any file is read or written.
- Refused with exit 2, the usage printed (its text names the five known options) and nothing changed (every file
  under the scratch computer hashed, names and bytes, before and after): an unknown option (`--version`, `--yes`,
  an abbreviation such as `--dry`, `--target=<path>`), `--help`, `-h`, a positional word, any option given twice,
  `--target` or `--keep` with no value (the last word, or followed by a word that begins with `-`).
- `--keep <value>`: the value equals the name of a folder under `<target>/cursor-bridge-previous/` exactly (case
  included), or is `none`. A value holding `/`, `\\`, `..` or a drive letter, or naming no kept folder, exits 2 and
  changes nothing. The named copy stays over every later install beside the one previous release, until another
  `--keep` names another copy or `--keep none` clears it; the next install then removes it as the one-previous rule
  does. The marker beside the copy is not pinned by name; only what it does is.
- `--rollback` alone restores the previous release (the newest kept folder) as today; `--rollback <version>` restores
  that kept copy, removes the kept copies newer than it, and writes cursor-bridge/ROLLED-BACK.md with the "If rolled
  back" items of every CHANGELOG entry newer than it. A version that names no kept folder exits 2, nothing changed.
- A dry run of each new form exits 0, names what it would act on, and changes nothing.
- Not pinned: `--keep` given with `--rollback`; whether `--keep` alone installs; what a rollback does to kept copies
  other than the newer ones; the usage's wording beyond the option names.

Isolation: every run is a subprocess whose HOME, USERPROFILE, LOCALAPPDATA, APPDATA and working folder are folders
of a scratch computer under pytest's temporary folder, and whose target is that scratch computer's ~/.claude
(named with --target, or the default the scratch HOME gives). The release folders are copies of bridge/ under the
temporary folder, four versions with one file and one CHANGELOG item each of their own; their installer is the
program under test.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import types

import pytest

import conftest as suite_conftest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_RELEASE = os.path.join(ROOT, "bridge")
PREVIOUS = "cursor-bridge-previous"
A, B, C, D = "2026.01.01a", "2026.01.02a", "2026.01.03a", "2026.01.04a"
VERSIONS = (A, B, C, D)
VERSION_NAME = re.compile(r"^\d{4}\.\d{2}\.\d{2}[a-z]$")
USAGE_WORDS = ("--target", "--dry-run", "--anyway", "--rollback", "--keep")


# ---------------------------------------------------------------- the release folders and the scratch computer

def item(version):
    """The one "If rolled back" item of `version`'s CHANGELOG entry."""
    return "ROLLBACK-ITEM-%s restores what %s changed" % (version, version)


def changelog_up_to(version):
    """A CHANGELOG with one entry per version up to `version`, newest first, each with its own item."""
    out = ["# Claude-Cursor Bridge - CHANGELOG (a test release)", "", "---", ""]
    for v in sorted((x for x in VERSIONS if x <= version), reverse=True):
        out += ["## " + v, "", "**What changed**", "- the test release " + v, "", "**If rolled back**", "- " + item(v), ""]
    return "\n".join(out)


def make_release(folder, version, norm_hash):
    """A release folder of `version`: bridge/ copied, its VERSION, its CHANGELOG, a file of its own, its manifest."""
    shutil.copytree(SOURCE_RELEASE, folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    cb = os.path.join(folder, "cursor-bridge")
    with open(os.path.join(cb, "VERSION"), "w", encoding="utf-8", newline="\n") as f:
        f.write(version + "\n")
    with open(os.path.join(cb, "CHANGELOG.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(changelog_up_to(version))
    with open(os.path.join(cb, "only-%s.md" % version), "w", encoding="utf-8", newline="\n") as f:
        f.write("shipped by %s only\n" % version)
    files = {}
    for dirpath, dirs, names in os.walk(folder):
        for n in names:
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, folder).replace("\\", "/")
            if rel != "cursor-bridge/MANIFEST.json":
                files[rel] = norm_hash(p)
    with open(os.path.join(cb, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"version": version, "generated": "test", "files": files}, f, indent=2)


def make_computer(root):
    """A scratch computer: a home with an empty .cursor, LOCALAPPDATA and APPDATA of its own, a working folder."""
    sb = types.SimpleNamespace(root=str(root), home=os.path.join(str(root), "home"),
                               localappdata=os.path.join(str(root), "localappdata"),
                               appdata=os.path.join(str(root), "appdata"), cwd=os.path.join(str(root), "cwd"))
    sb.target = os.path.join(sb.home, ".claude")
    for d in (os.path.join(sb.home, ".cursor"), sb.localappdata, sb.appdata, sb.cwd):
        os.makedirs(d, exist_ok=True)
    return sb


def run(sb, installer, *args):
    """Run `installer` with `args` on the scratch computer `sb` only."""
    env = dict(os.environ, HOME=sb.home, USERPROFILE=sb.home, LOCALAPPDATA=sb.localappdata, APPDATA=sb.appdata)
    kw = suite_conftest.windowless_kwargs({"capture_output": True, "text": True, "encoding": "utf-8",
                                           "errors": "replace", "timeout": 600})
    p = subprocess.run([sys.executable, installer] + list(args), env=env, cwd=sb.cwd, **kw)
    return p.returncode, p.stdout + p.stderr


def snapshot(root):
    """Every folder and file under `root`, names and bytes (a link is recorded, never followed)."""
    isjunction = getattr(os.path, "isjunction", lambda p: False)
    out = {}
    for dirpath, dirs, names in os.walk(root):
        rel = os.path.relpath(dirpath, root).replace("\\", "/")
        for d in list(dirs):
            p = os.path.join(dirpath, d)
            if os.path.islink(p) or isjunction(p):
                out[rel + "/" + d] = "link"
                dirs.remove(d)
            else:
                out[rel + "/" + d] = "dir"
        for n in names:
            with open(os.path.join(dirpath, n), "rb") as f:
                out[rel + "/" + n] = hashlib.sha256(f.read()).hexdigest()
    return out


def kept_versions(target):
    """The names of the kept release folders under <target>/cursor-bridge-previous/, sorted."""
    base = os.path.join(target, PREVIOUS)
    if not os.path.isdir(base):
        return []
    return sorted(n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n)) and VERSION_NAME.match(n))


def installed_version(target):
    with open(os.path.join(target, "cursor-bridge", "VERSION"), encoding="utf-8") as f:
        return f.read().strip()


def whole_copy(target, version):
    """True when the kept copy of `version` is there with its own file and manifest."""
    copy = os.path.join(target, PREVIOUS, version)
    try:
        with open(os.path.join(copy, "cursor-bridge", "MANIFEST.json"), encoding="utf-8") as f:
            listed = json.load(f).get("version")
    except (OSError, ValueError):
        return False
    return listed == version and os.path.isfile(os.path.join(copy, "cursor-bridge", "only-%s.md" % version))


def plain(out, *roots):
    """`out` with the scratch folders' paths taken out, so a word test never matches a folder name."""
    for r in roots:
        for form in (r, r.replace("\\", "/")):
            out = out.replace(form, "<scratch>")
    return out


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    """The four release folders, and a scratch computer's ~/.claude with A installed and then B (A kept as the one
    previous release), copied whole into each test's own scratch computer."""
    norm_hash = suite_conftest.load_program("bridge-check").norm_hash
    base = tmp_path_factory.mktemp("install-keep-releases")
    releases = {}
    for v, name in zip(VERSIONS, ("release-a", "release-b", "release-c", "release-d")):
        releases[v] = os.path.join(str(base), name)
        make_release(releases[v], v, norm_hash)
    tpl = make_computer(tmp_path_factory.mktemp("install-keep-template"))
    w = types.SimpleNamespace(root=str(base), template=tpl,
                              installer=lambda v: os.path.join(releases[v], "cursor-bridge", "bridge-install.py"))
    for v in (A, B):
        rc, out = run(tpl, w.installer(v), "--target", tpl.target)
        assert rc == 0 and "MATCHES bridge " + v in out, out
    assert kept_versions(tpl.target) == [A], "the template's one previous release"
    return w


@pytest.fixture
def sb(tmp_path, world):
    """This test's scratch computer, its ~/.claude holding B installed and A kept as the one previous release."""
    s = make_computer(tmp_path)
    shutil.copytree(world.template.target, s.target)
    return s


def install(world, sb, version, *args):
    rc, out = run(sb, world.installer(version), "--target", sb.target, *args)
    assert rc == 0 and "MATCHES bridge " + version in out, out
    return out


def keep_a_then_install_c_and_d(world, sb):
    """B installed with A kept; `--keep A` from B's own release folder (an install of B, if --keep installs, changes
    nothing); C and D installed after it. A stays beside the one previous release each time."""
    rc, out = run(sb, world.installer(B), "--target", sb.target, "--keep", A)
    assert rc == 0, "--keep naming the kept copy of A was not accepted: " + out
    install(world, sb, C)
    assert kept_versions(sb.target) == [A, B], "after the first later install the named copy is not beside the previous release"
    install(world, sb, D)
    assert kept_versions(sb.target) == [A, C], "after the second later install the named copy is not beside the previous release"
    assert whole_copy(sb.target, A) and installed_version(sb.target) == D


# ---------------------------------------------------------------- every word read first

REFUSED_FORMS = [
    ("unknown-version", ["--target", "{T}", "--version"]),
    ("unknown-yes", ["--target", "{T}", "--yes"]),
    ("unknown-yes-in-a-dry-run", ["--target", "{T}", "--dry-run", "--yes"]),
    ("unknown-abbreviation", ["--target", "{T}", "--dry"]),
    ("unknown-target-equals", ["--target={T}"]),
    ("help", ["--target", "{T}", "--help"]),
    ("help-alone", ["--help"]),
    ("h", ["--target", "{T}", "-h"]),
    ("positional-last", ["--target", "{T}", "install"]),
    ("positional-first", ["now", "--target", "{T}"]),
    ("positional-after-dry-run", ["--target", "{T}", "--dry-run", A]),
    ("positional-after-rollback-version", ["--rollback", A, "again", "--target", "{T}"]),
    ("twice-target", ["--target", "{T}", "--target", "{T}"]),
    ("twice-dry-run", ["--target", "{T}", "--dry-run", "--dry-run"]),
    ("twice-anyway", ["--target", "{T}", "--anyway", "--anyway"]),
    ("twice-rollback", ["--rollback", "--rollback", "--target", "{T}"]),
    ("twice-keep", ["--target", "{T}", "--keep", A, "--keep", A]),
    ("target-last-word", ["--target"]),
    ("target-last-after-dry-run", ["--dry-run", "--target"]),
    ("target-before-an-option", ["--target", "--dry-run"]),
    ("keep-last-word", ["--target", "{T}", "--keep"]),
    ("keep-before-an-option", ["--target", "{T}", "--keep", "--dry-run"]),
    ("keep-before-target", ["--keep", "--target", "{T}"]),
    ("keep-with-rollback", ["--target", "{T}", "--rollback", "--keep", A]),
]


@pytest.mark.parametrize("argv", [f[1] for f in REFUSED_FORMS], ids=[f[0] for f in REFUSED_FORMS])
def test_r094_a_word_the_installer_does_not_know_is_refused_with_the_usage(world, sb, argv):
    """R-094, TASK-073 Done when (`bridge-install.py` reads every word of its command line before it reads or writes
    anything else, and an unknown option, `--help`, `-h`, a positional word, an option given twice or an option
    missing its value prints the usage and exits 2 with the target byte-identical, a test that hashes the target
    before and after, for each): the release folder of a newer version would install over the target, so any run
    that went past the words changes it. Today the installer ignores the words it does not know and installs."""
    args = [a.replace("{T}", sb.target) for a in argv]
    before = snapshot(sb.root)
    rc, out = run(sb, world.installer(C), *args)
    assert rc == 2, "not refused with exit 2: %r -> %d: %s" % (argv, rc, out)
    assert "Traceback" not in out, out
    missing = [w for w in USAGE_WORDS if w not in out]
    assert not missing, "the usage was not printed (it names no %s): %s" % (", ".join(missing), out)
    assert snapshot(sb.root) == before, "a refused command changed the target or the computer: %r" % argv


KNOWN_FORMS = [
    ("dry-run-first", ["--dry-run", "--target", "{T}"]),
    ("dry-run-anyway", ["--target", "{T}", "--dry-run", "--anyway"]),
    ("rollback-dry-run", ["--rollback", "--target", "{T}", "--dry-run"]),
    ("rollback-last", ["--target", "{T}", "--dry-run", "--rollback"]),
]


@pytest.mark.parametrize("argv", [f[1] for f in KNOWN_FORMS], ids=[f[0] for f in KNOWN_FORMS])
def test_r094_the_known_words_are_still_accepted_in_any_order(world, sb, argv):
    """R-094, TASK-073 Done when (the existing install and rollback tests green unedited; `--rollback [<version>]`
    restores the previous release where no version is given, as today): the known words, in any order, are not
    refused; a dry run changes nothing. Holds today."""
    args = [a.replace("{T}", sb.target) for a in argv]
    before = snapshot(sb.root)
    rc, out = run(sb, world.installer(C), *args)
    assert rc == 0 and "(dry run)" in out, "a known form was refused: %r: %s" % (argv, out)
    assert snapshot(sb.root) == before, "a dry run changed something: %r" % argv


# ---------------------------------------------------------------- --keep: the value

KEEP_VALUES = [
    ("forward-slash", "sub/" + A),
    ("backslash", "sub\\" + A),
    ("dotdot", ".."),
    ("dotdot-back-to-the-copy", A + "/../" + A),
    ("dotdot-backslash", "..\\" + PREVIOUS + "\\" + A),
    ("rooted", "/" + A),
    ("drive", "C:"),
    ("drive-relative", "C:" + A),
    ("drive-absolute", "C:\\" + A),
    ("no-such-copy", "2026.01.09z"),
    ("other-case", A.upper()),
    ("prefix", A[:-1]),
    ("the-installed-version", B),
    ("empty", ""),
]


@pytest.mark.parametrize("value", [v[1] for v in KEEP_VALUES], ids=[v[0] for v in KEEP_VALUES])
def test_r094_a_keep_value_that_is_not_a_kept_folders_name_is_refused(world, sb, value):
    """R-094, TASK-073 Done when (`--keep <version>` keeps the named earlier copy under `cursor-bridge-previous/`, the
    value matched against the kept folders' names exactly and never joined to a path: a value holding a separator,
    `..` or a drive letter is a usage error, exit 2, as is a name that matches no kept folder, nothing removed): the
    target keeps A as its previous release, so a value that reaches A only as a path, or by another case, is still
    refused. Today `--keep` is ignored and the newer release installs."""
    before = snapshot(sb.root)
    rc, out = run(sb, world.installer(C), "--target", sb.target, "--keep", value)
    assert rc == 2, "--keep %r was not refused with exit 2 (%d): %s" % (value, rc, out)
    assert "Traceback" not in out, out
    assert snapshot(sb.root) == before, "--keep %r changed or removed something" % value
    assert kept_versions(sb.target) == [A] and whole_copy(sb.target, A)


# ---------------------------------------------------------------- --keep: what it keeps

def test_r094_one_previous_release_is_kept_without_keep(world, sb):
    """R-094, TASK-073 Done when (the named copy kept beside the one previous release; the existing install tests
    green unedited): without `--keep`, an install keeps one previous release, as today. Holds today."""
    install(world, sb, C)
    assert kept_versions(sb.target) == [B], "an install without --keep kept more or less than the one previous release"


def test_r094_the_named_copy_stays_over_two_later_installs(world, sb):
    """R-094, TASK-073 Done when (`--keep <version>` keeps the named earlier copy under `cursor-bridge-previous/`
    beside the one previous release, a marker file beside the copy keeping it over every later install): A named,
    then C and D installed; A is still there, whole, beside C, the one previous release. Today `--keep` is ignored
    and the install of C removes A."""
    keep_a_then_install_c_and_d(world, sb)


def test_r094_another_keep_names_another_copy(world, sb):
    """R-094, TASK-073 Done when (a marker file beside the copy keeping it over every later install until another
    `--keep` names another copy): A named, C installed, then B named; at the install of D, B stays beside C and A
    goes. Today `--keep` is ignored and A is gone at the install of C."""
    rc, out = run(sb, world.installer(B), "--target", sb.target, "--keep", A)
    assert rc == 0, out
    install(world, sb, C)
    assert kept_versions(sb.target) == [A, B], "the named copy did not stay over the install of C"
    rc, out = run(sb, world.installer(C), "--target", sb.target, "--keep", B)
    assert rc == 0, "--keep naming the previous release B was not accepted: " + out
    install(world, sb, D)
    assert kept_versions(sb.target) == [B, C], "after another --keep, the install of D did not keep B and drop A"
    assert whole_copy(sb.target, B) and whole_copy(sb.target, C)


def test_r094_keep_none_clears_the_kept_copy(world, sb):
    """R-094, TASK-073 Done when (a marker file beside the copy keeping it over every later install until `--keep
    none` clears it): A named, C installed, `--keep none`; the install of D keeps only C, as the one-previous rule
    does. Today `--keep` is ignored and A is gone at the install of C."""
    rc, out = run(sb, world.installer(B), "--target", sb.target, "--keep", A)
    assert rc == 0, out
    install(world, sb, C)
    assert kept_versions(sb.target) == [A, B], "the named copy did not stay over the install of C"
    rc, out = run(sb, world.installer(C), "--target", sb.target, "--keep", "none")
    assert rc == 0, "--keep none was not accepted: " + out
    install(world, sb, D)
    assert kept_versions(sb.target) == [C], "after --keep none the next install did not keep only the one previous release"


# ---------------------------------------------------------------- --rollback [<version>]

def test_r094_rollback_alone_restores_the_previous_release_beside_a_kept_copy(world, sb):
    """R-094, TASK-073 Done when (`--rollback [<version>]` restores the previous release where no version is given,
    as today): with A kept and C the previous release under D, `--rollback` restores C. What it does to A is not
    pinned. Today the setup fails: `--keep` is ignored."""
    keep_a_then_install_c_and_d(world, sb)
    rc, out = run(sb, world.installer(D), "--rollback", "--target", sb.target)
    assert rc == 0 and "MATCHES bridge " + C in out, out
    assert installed_version(sb.target) == C


def test_r094_rollback_to_the_older_kept_copy(world, sb):
    """R-094, TASK-073 Done when (`--rollback <version>` restores the named kept copy, a rollback to the older copy
    removing the kept copies newer than it and writing `ROLLED-BACK.md` from every CHANGELOG entry newer than its
    target): with A kept and C the previous release under D, `--rollback A` installs A, removes C, and the note holds
    the items of B, C and D and not A's. Today the setup fails (`--keep` is ignored), and `--rollback A` would restore
    the previous release."""
    keep_a_then_install_c_and_d(world, sb)
    rc, out = run(sb, world.installer(D), "--rollback", A, "--target", sb.target)
    assert rc == 0 and "MATCHES bridge " + A in out, out
    assert installed_version(sb.target) == A
    assert os.path.isfile(os.path.join(sb.target, "cursor-bridge", "only-%s.md" % A))
    assert not os.path.exists(os.path.join(sb.target, "cursor-bridge", "only-%s.md" % D)), "a file only D shipped stayed"
    assert not [v for v in kept_versions(sb.target) if v > A], "a kept copy newer than A stayed: %s" % kept_versions(sb.target)
    with open(os.path.join(sb.target, "cursor-bridge", "ROLLED-BACK.md"), encoding="utf-8") as f:
        note = f.read()
    for v in (B, C, D):
        assert item(v) in note, "ROLLED-BACK.md lacks the item of %s, an entry newer than A: %s" % (v, note)
    assert item(A) not in note, "ROLLED-BACK.md holds the item of A, the release rolled back to"


def test_r094_rollback_names_the_previous_release(world, sb):
    """R-094, TASK-073 Done when (`--rollback [<version>]` ... the named kept copy where one is): the one previous
    release is a kept folder too, and `--rollback C` restores it. Today the setup fails: `--keep` is ignored."""
    keep_a_then_install_c_and_d(world, sb)
    rc, out = run(sb, world.installer(D), "--rollback", C, "--target", sb.target)
    assert rc == 0 and "MATCHES bridge " + C in out, out
    assert installed_version(sb.target) == C


ROLLBACK_VALUES = [
    ("no-such-copy", "2026.01.09z"),
    ("other-case", A.upper()),
    ("the-installed-version", B),
    ("dotdot", ".."),
    ("path-to-the-copy", "../" + PREVIOUS + "/" + A),
    ("drive-absolute", "C:\\" + A),
]


@pytest.mark.parametrize("value", [v[1] for v in ROLLBACK_VALUES], ids=[v[0] for v in ROLLBACK_VALUES])
def test_r094_a_rollback_to_no_kept_copy_changes_nothing(world, sb, value):
    """R-094, TASK-073 Done when (`--rollback [<version>]` restores the named kept copy where one is; the value
    matched against the kept folders' names, never used as a path): a version that names no kept folder exactly
    exits 2 and changes nothing (the exit is the installer's "nothing to roll back to"). Today the version is
    ignored and the previous release, A, is restored."""
    before = snapshot(sb.root)
    rc, out = run(sb, world.installer(C), "--rollback", value, "--target", sb.target)
    assert rc == 2, "--rollback %r was not refused with exit 2 (%d): %s" % (value, rc, out)
    assert "Traceback" not in out, out
    assert snapshot(sb.root) == before, "--rollback %r changed something" % value


# ---------------------------------------------------------------- a dry run of each new form

DRY_FORMS = [
    ("keep-the-previous", False, B, ["--keep", A], A),
    ("keep-another", True, D, ["--keep", C], C),
    ("keep-none", True, D, ["--keep", "none"], None),
    ("rollback-to-the-kept-copy", True, D, ["--rollback", A], A),
]


@pytest.mark.parametrize("after_keep, installer, words, named", [f[1:] for f in DRY_FORMS], ids=[f[0] for f in DRY_FORMS])
def test_r094_a_dry_run_of_each_new_form_says_what_it_would_do_and_changes_nothing(world, sb, after_keep, installer, words, named):
    """R-094, TASK-073 Done when (a dry run prints what each would do and changes nothing): `--keep <version>`,
    `--keep none` and `--rollback <version>` with `--dry-run` exit 0, name the copy they would act on (for `--keep
    none`, the word none or the copy it would release) and leave every file as it was. Today the words are ignored:
    the dry run names no copy, and the setup with a kept copy fails."""
    if after_keep:
        keep_a_then_install_c_and_d(world, sb)
    before = snapshot(sb.root)
    rc, out = run(sb, world.installer(installer), "--target", sb.target, "--dry-run", *words)
    assert rc == 0, "a dry run of %r failed: %s" % (words, out)
    said = plain(out, sb.root, world.root)
    if named:
        assert named in said, "the dry run of %r does not name %s: %s" % (words, named, out)
    else:
        assert "none" in said.lower() or A in said, "the dry run of --keep none says nothing of what it would clear: " + out
    assert snapshot(sb.root) == before, "a dry run of %r changed something" % words


# ---------------------------------------------------------------- round 2

def marker_files(target):
    """The files directly under <target>/cursor-bridge-previous/ (the marker among them; its name is not pinned)."""
    base = os.path.join(target, PREVIOUS)
    return [os.path.join(base, n) for n in os.listdir(base) if os.path.isfile(os.path.join(base, n))]


def spoil_markers(target, make):
    """Rewrite every marker file's bytes with `make(old_bytes)`; at least one marker must be there."""
    markers = marker_files(target)
    assert markers, "no marker file beside the kept copies after --keep"
    for m in markers:
        with open(m, "rb") as f:
            data = f.read()
        with open(m, "wb") as f:
            f.write(make(data))


NOT_TEXT = b"\xff\xfe\x00not text\x80\x81"


def test_r2_keep_given_with_the_install_of_a_new_version_keeps_the_named_copy(world, sb):
    """R-094, TASK-073 Done when (`--keep <version>` keeps the named earlier copy under `cursor-bridge-previous/`
    beside the one previous release): round 1 removed the named copy when `--keep` came with the install of a new
    version (the copies rotated before the mark was written). B installed with A kept; C installed with `--keep A`:
    A is still whole beside B; D installed after it: A beside C."""
    out = install(world, sb, C, "--keep", A)
    assert kept_versions(sb.target) == [A, B], "the install of C with --keep A did not keep A beside B: %s" % out
    assert whole_copy(sb.target, A) and whole_copy(sb.target, B)
    install(world, sb, D)
    assert kept_versions(sb.target) == [A, C], "the copy named at the install of C did not stay over the install of D"
    assert whole_copy(sb.target, A)


def test_r2_a_marker_that_is_not_text_never_stops_an_install(world, sb):
    """R-094, TASK-073 Done when (a marker file beside the copy keeping it over every later install): a marker
    edited by hand into bytes that are not text never makes an install fail. A named, the marker's bytes replaced,
    C installs: exit 0, no traceback, B kept as the one previous release."""
    rc, out = run(sb, world.installer(B), "--target", sb.target, "--keep", A)
    assert rc == 0, out
    spoil_markers(sb.target, lambda data: NOT_TEXT)
    rc, out = run(sb, world.installer(C), "--target", sb.target)
    assert "Traceback" not in out, out
    assert rc == 0 and "MATCHES bridge " + C in out, "an install stopped on a marker that is not text: %s" % out
    assert B in kept_versions(sb.target) and whole_copy(sb.target, B)


def test_r2_a_marker_that_is_not_text_never_stops_a_rollback(world, sb):
    """R-094, TASK-073 Done when (`--rollback [<version>]` restores the previous release where no version is given,
    as today): a marker that is not text never makes a rollback fail, before or after the copies are removed. A
    named, C and D installed, the marker's bytes replaced; `--rollback` restores C, exit 0, no traceback."""
    keep_a_then_install_c_and_d(world, sb)
    spoil_markers(sb.target, lambda data: NOT_TEXT)
    rc, out = run(sb, world.installer(D), "--rollback", "--target", sb.target)
    assert "Traceback" not in out, out
    assert rc == 0 and "MATCHES bridge " + C in out, "a rollback stopped on a marker that is not text: %s" % out
    assert installed_version(sb.target) == C


def test_r2_a_marker_saved_with_a_byte_order_mark_still_keeps_its_copy(world, sb):
    """R-094, TASK-073 Done when (a marker file beside the copy keeping it over every later install): a marker
    saved again by a Windows editor gains a byte order mark and still names the same copy. A named, a byte order
    mark put before the marker's text, C installed: A is still beside B."""
    rc, out = run(sb, world.installer(B), "--target", sb.target, "--keep", A)
    assert rc == 0, out
    spoil_markers(sb.target, lambda data: b"\xef\xbb\xbf" + data)
    install(world, sb, C)
    assert kept_versions(sb.target) == [A, B], "a marker with a byte order mark did not keep A over the install of C"


def test_r2_an_interrupted_copy_is_cleared_when_the_copies_rotate(world, sb):
    """R-094, TASK-073 Done when (an unmarked copy is removed at the next install by the one-previous rule, as
    today): a half-written copy left by an interrupted run (a folder ending .partial) is removed when the copies
    rotate, as the one-previous rule removed it before this increment."""
    stale = os.path.join(sb.target, PREVIOUS, "2026.01.00a.partial")
    os.makedirs(os.path.join(stale, "cursor-bridge"))
    with open(os.path.join(stale, "cursor-bridge", "half.md"), "w", encoding="utf-8") as f:
        f.write("half written\n")
    install(world, sb, C)
    assert not os.path.exists(stale), "a stale .partial copy stayed after the copies rotated"
    assert kept_versions(sb.target) == [B]


def test_r2_a_kept_copy_of_a_version_with_no_letter_is_still_rolled_back_to(world, tmp_path):
    """R-094, TASK-073 Done when (`--rollback [<version>]` restores the previous release where no version is given,
    as today): the bridge's own changelog has versions with no letter (2026.09.20 to 2026.09.27); today a kept copy
    of one is restored by `--rollback`, and round 1's version filter hid it ("nothing to roll back to")."""
    norm_hash = suite_conftest.load_program("bridge-check").norm_hash
    plain_version = "2026.01.00"
    release = os.path.join(str(tmp_path), "release-plain")
    make_release(release, plain_version, norm_hash)
    s = make_computer(tmp_path / "computer")
    rc, out = run(s, os.path.join(release, "cursor-bridge", "bridge-install.py"), "--target", s.target)
    assert rc == 0 and "MATCHES bridge " + plain_version in out, out
    install(world, s, B)
    assert os.path.isdir(os.path.join(s.target, PREVIOUS, plain_version)), "the plain version was not kept"
    rc, out = run(s, world.installer(B), "--rollback", "--target", s.target)
    assert rc == 0 and "MATCHES bridge " + plain_version in out, "the kept copy of a version with no letter was not restored: %s" % out
    assert installed_version(s.target) == plain_version


# ---------------------------------------------------------------- round 3

def link_dir(link, target):
    """A folder link the platform makes without a privilege: a junction on Windows, a symbolic link elsewhere."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(str(target), str(link), target_is_directory=True)


def unlink_dir(link):
    """Remove the link itself, never what it points at."""
    if os.name == "nt":
        os.rmdir(link)
    else:
        os.unlink(link)


def test_r3_a_linked_previous_folder_never_has_its_other_contents_removed(world, sb):
    """R-094, TASK-073 Done when (`--keep <version>` keeps the named earlier copy under `cursor-bridge-previous/`;
    the one-previous rule as today): round 2's rotation followed a `cursor-bridge-previous` that is itself a link (a
    junction on Windows) and removed every file and folder in the folder it points at; before this increment the
    whole-folder removal refused a link. The kept copies moved to a folder elsewhere that also holds the owner's
    own files, `cursor-bridge-previous` made a link to it, C installed: the owner's files are all still there."""
    base = os.path.join(sb.target, PREVIOUS)
    elsewhere = os.path.join(sb.root, "elsewhere")
    shutil.move(base, elsewhere)
    with open(os.path.join(elsewhere, "doc.txt"), "w", encoding="utf-8") as f:
        f.write("the owner's own file\n")
    os.makedirs(os.path.join(elsewhere, "sub"))
    with open(os.path.join(elsewhere, "sub", "f.txt"), "w", encoding="utf-8") as f:
        f.write("the owner's own folder\n")
    owned = {k: v for k, v in snapshot(elsewhere).items() if k.startswith("./doc") or k.startswith("./sub")}
    link_dir(base, elsewhere)
    try:
        rc, out = run(sb, world.installer(C), "--target", sb.target)
        assert "Traceback" not in out, out
        after = {k: v for k, v in snapshot(elsewhere).items() if k.startswith("./doc") or k.startswith("./sub")}
        assert after == owned, "the install removed or changed what the linked folder points at: %s" % out
    finally:
        unlink_dir(base)


def test_r3_a_stray_file_that_cannot_be_removed_never_stops_an_install(world, sb):
    """R-094, TASK-073 Done when (a marker or an entry under `cursor-bridge-previous/` never makes an install
    fail): round 2's rotation removed a stray file with no error handling, so a read-only file there stopped every
    install; before this increment the whole-folder removal ignored errors. A read-only file beside the kept copy,
    C installed: exit 0, no traceback, B kept as the one previous release."""
    import stat
    stray = os.path.join(sb.target, PREVIOUS, "notes.txt")
    with open(stray, "w", encoding="utf-8") as f:
        f.write("a stray file\n")
    os.chmod(stray, stat.S_IREAD)
    try:
        rc, out = run(sb, world.installer(C), "--target", sb.target)
        assert "Traceback" not in out, out
        assert rc == 0 and "MATCHES bridge " + C in out, "a stray read-only file stopped the install: %s" % out
        assert B in kept_versions(sb.target) and whole_copy(sb.target, B)
    finally:
        if os.path.exists(stray):
            os.chmod(stray, stat.S_IREAD | stat.S_IWRITE)


def test_r3_a_stray_file_named_like_the_version_being_saved_never_stops_an_install(world, sb):
    """R-094, TASK-073 Done when (an entry under `cursor-bridge-previous/` never makes an install fail; the
    one-previous rule as today): round 2's rotation spared any entry named like the version being saved, so a stray
    file of that name stayed and the new copy could not take its place. A file named like B beside the kept copy,
    C installed: exit 0, no traceback, B kept whole as the one previous release."""
    stray = os.path.join(sb.target, PREVIOUS, B)
    with open(stray, "w", encoding="utf-8") as f:
        f.write("a stray file named like a version\n")
    rc, out = run(sb, world.installer(C), "--target", sb.target)
    assert "Traceback" not in out, out
    assert rc == 0 and "MATCHES bridge " + C in out, "a stray file named like the saved version stopped the install: %s" % out
    assert whole_copy(sb.target, B)


# ---------------------------------------------------------------- the mutation sweep's cases

def test_sweep_the_marker_names_the_spared_copy_after_a_failed_install_check(world, sb, monkeypatch):
    """R-094, TASK-073 Done when (a marker file beside the copy keeping it over every later install until another
    `--keep` names another copy): an install of C with `--keep A` whose install check fails (exit 1) still leaves
    the marker naming A, the copy its rotation spared, so the install of D after it keeps A beside C. Run in process
    with the check made to fail; tests/test_rollback.py, which installs the repository's own stamped release,
    cannot run under a mutant."""
    import importlib.util
    for name, value in (("HOME", sb.home), ("USERPROFILE", sb.home), ("LOCALAPPDATA", sb.localappdata),
                        ("APPDATA", sb.appdata)):
        monkeypatch.setenv(name, value)
    spec = importlib.util.spec_from_file_location("bridge_install_of_release_c", world.installer(C))
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    monkeypatch.setattr(installer, "run_check", lambda target: 1)
    assert installer.install(sb.target, False, False, A) == 1, "the install with the check made to fail did not exit 1"
    assert installed_version(sb.target) == C
    assert kept_versions(sb.target) == [A, B], "the rotation of the failed install did not spare A beside B"
    markers = marker_files(sb.target)
    assert markers, "no marker after the failed install"
    named = []
    for m in markers:
        with open(m, encoding="utf-8-sig", errors="replace") as f:
            named.append(f.read().strip())
    assert A in named, "after the failed check the marker does not name A, the spared copy: %r" % named
    install(world, sb, D)
    assert kept_versions(sb.target) == [A, C], "the install after the failed one did not keep A, the marked copy"
    assert whole_copy(sb.target, A)
