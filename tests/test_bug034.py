"""BUG-034 (TASK-026's release-level review, pass 1, M2; Review B's TASK-027 note): bridge-install.py
keeps the installed release as the way back only when the two versions differ, so a release folder
carrying the installed release's version but other files (main before its stamp) replaced it with
no previous kept, and --rollback then had nothing to restore. A release whose version equals the
installed one is installed only when its manifest lists the same files with the same fingerprints
(a repeated install, the repair the installer's own messages name); any other is refused before
anything changes, --anyway excepted (the maintainer's rehearsals).

enforces: docs/REQUIREMENTS.md R-037 (the release delivered with its way back: "bridge-install.py
run", KP-037's take-back); bridge/cursor-bridge/bridge-install.py's docstring (the previous release
kept under cursor-bridge-previous/<version>/ and put back with --rollback). Scratch targets only."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_rollback import make_old_release, install_old, run, OLD_VERSION  # noqa: E402


def restamp(tree, program):
    """Write `tree`'s manifest again from its files, keeping its version (the stamp program's
    shape: every file but the manifest, by the installer's own fingerprint)."""
    norm_hash = program("bridge-check").norm_hash
    files = {}
    for dirpath, dirs, names in os.walk(tree):
        for n in names:
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, tree).replace("\\", "/")
            if rel != "cursor-bridge/MANIFEST.json":
                files[rel] = norm_hash(p)
    man = tree / "cursor-bridge" / "MANIFEST.json"
    version = json.loads(man.read_text(encoding="utf-8"))["version"]
    man.write_text(json.dumps({"version": version, "generated": "test", "files": files}, indent=2), encoding="utf-8")


def two_releases_of_one_version(tmp_path, program):
    """Release A, installed; release B, the same version string with one file changed and its
    manifest written again (main before the stamp)."""
    a = make_old_release(tmp_path / "release-a", program)
    b = make_old_release(tmp_path / "release-b", program)
    (b / "cursor-bridge" / "old-only.md").write_text("changed after the version was stamped\n", encoding="utf-8")
    restamp(b, program)
    target = tmp_path / ".claude"
    target.mkdir()
    rc, out = install_old(tmp_path, a, target)
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    return a, b, target


def test_bug034_a_release_of_the_installed_version_with_other_files_is_refused(tmp_path, program):
    a, b, target = two_releases_of_one_version(tmp_path, program)
    kept = target / "cursor-bridge-previous" / "2025.01.01a"
    kept.mkdir(parents=True)
    (kept / "marker.txt").write_text("an older way back\n", encoding="utf-8")
    before = (target / "cursor-bridge" / "old-only.md").read_text(encoding="utf-8")
    manifest_before = (target / "cursor-bridge" / "MANIFEST.json").read_text(encoding="utf-8")
    rc, out = run(b / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target))
    assert rc == 2, "a release carrying the installed version but other files was installed, with no way back kept: " + out
    assert "but not its files" in out and "nothing was changed" in out and OLD_VERSION in out, "not this refusal: " + out
    assert (target / "cursor-bridge" / "old-only.md").read_text(encoding="utf-8") == before, "the installed file changed although the install was refused"
    assert (target / "cursor-bridge" / "MANIFEST.json").read_text(encoding="utf-8") == manifest_before, "the installed manifest changed although the install was refused"
    assert sorted(p.name for p in (target / "cursor-bridge-previous").iterdir()) == ["2025.01.01a"], "a refused install rotated the kept copy"
    assert (kept / "marker.txt").read_text(encoding="utf-8") == "an older way back\n", "a refused install changed the kept copy"


def test_bug034_a_file_listed_in_one_manifest_only_is_named(tmp_path, program):
    a, b, target = two_releases_of_one_version(tmp_path, program)
    (b / "cursor-bridge" / "new-only.md").write_text("in the release folder only\n", encoding="utf-8")
    restamp(b, program)
    rc, out = run(b / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target))
    assert rc == 2 and "but not its files" in out and "2 file(s)" in out and "cursor-bridge/new-only.md" in out, out
    assert not (target / "cursor-bridge" / "new-only.md").exists()


def test_bug034_the_refusal_holds_under_a_dry_run(tmp_path, program):
    a, b, target = two_releases_of_one_version(tmp_path, program)
    rc, out = run(b / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target), "--dry-run")
    assert rc == 2 and "nothing was changed" in out and "(dry run)" not in out, "a dry run promised an install the real run refuses: " + out


def test_bug034_a_dry_run_with_anyway_warns_and_changes_nothing(tmp_path, program):
    a, b, target = two_releases_of_one_version(tmp_path, program)
    before = (target / "cursor-bridge" / "old-only.md").read_text(encoding="utf-8")
    rc, out = run(b / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target), "--dry-run", "--anyway")
    assert rc == 0 and "(dry run)" in out and "WARNING" in out and "no way back to it was kept" in out, out
    assert (target / "cursor-bridge" / "old-only.md").read_text(encoding="utf-8") == before, "a dry run changed the installed tree"


def test_bug034_the_same_release_installed_again_is_still_allowed(tmp_path, program):
    a, b, target = two_releases_of_one_version(tmp_path, program)
    rc, out = install_old(tmp_path, a, target)
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, "the repeated install of the release already installed (the repair) was refused: " + out


def test_bug034_anyway_installs_it_for_the_maintainers_rehearsals(tmp_path, program):
    a, b, target = two_releases_of_one_version(tmp_path, program)
    rc, out = run(b / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target), "--anyway")
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    assert (target / "cursor-bridge" / "old-only.md").read_text(encoding="utf-8") == "changed after the version was stamped\n"
    assert "WARNING" in out and "no way back to it was kept" in out, "--anyway replaced a same-version tree with no way back kept, without a word (the security audit and Review A, convergent): " + out
    lines = out.splitlines()
    banner = next(i for i, line in enumerate(lines) if line.startswith("bridge-install: ") and " -> " in line)
    warning = [i for i, line in enumerate(lines) if line.startswith("  WARNING        the installed " + OLD_VERSION + " was replaced")]
    assert len(warning) == 1 and warning[0] > banner, "the warning is not one line after the banner: " + out
    assert "(1 file(s): cursor-bridge/old-only.md)" in lines[warning[0]], "the warning does not name the refusal's differing list: " + lines[warning[0]]


def test_bug034_the_same_release_with_anyway_warns_of_nothing(tmp_path, program):
    a, b, target = two_releases_of_one_version(tmp_path, program)
    rc, out = run(a / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target), "--anyway")
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    assert "no way back to it was kept" not in out, "the identical release, installed again with --anyway, was said to lose its way back: " + out
