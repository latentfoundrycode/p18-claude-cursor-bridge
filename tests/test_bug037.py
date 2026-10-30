"""BUG-037 (stage B6's review, round 1): the run sheet's install check against what the installer prints (R-038).

Written by the supervisor; no builder run. calibrate-bridge.md's step 1 checked every install by two signs, `VERSION`
changed and a `previous <version> kept at` line printed. The installer prints that line with the spaces that align its
columns (`previous       <version> kept at <folder>`), and only when the installed MANIFEST.json's version differs
from the release's: the same release installed again prints none, and a repeat after an interrupted install prints it
or not, as far as the first run got (Review A of BUG-037: a run killed before it replaced cursor-bridge/MANIFEST.json
leaves the older version there). The run sheet now gives every install one check, the installer's exit 0 with the
line it prints last, `RESULT: INSTALLED TREE MATCHES bridge <the release's version>`, and names the two signs as what
an install over an older release installed whole also shows. The installs are test_rollback.py's, imported, so the
fixtures are the same; LOCALAPPDATA points at a temporary folder in every run.

- test_bug037_every_install_ends_on_the_check_the_run_sheet_names enforces: step 1's one check, the installer's last
  line on an install over an older release.
- test_bug037_a_whole_install_over_an_older_release_prints_the_previous_line_as_named enforces: step 1's signs of
  that install, and the installer's line reading as step 1 names it, its columns aligned by spaces.
- test_bug037_the_same_release_again_changes_nothing_the_signs_name enforces: step 1's clause for the same release
  installed again, `VERSION` unchanged and no `previous` line, the check passing.
- test_bug037_a_repeat_after_an_interrupted_install_prints_the_line_or_none enforces: step 1's clause for a repeat,
  a run killed before and after cursor-bridge/MANIFEST.json is replaced, each repeat ending on the one check.
- test_bug037_the_fix_release_entry_stands_above_2026_10_30b enforces: bridge/cursor-bridge/CHANGELOG.md's header
  (each entry's parts, every item phase-marked, the If rolled back items reaching the installer's note) for
  2026.10.30c, and 2026.10.30b's corrected sentence on an increment in flight at its install.
"""
import os
import re

import pytest

import test_release_b_stamp as S
from test_rollback import (NEW_VERSION, OLD_VERSION, RELEASE, install_new, install_old, installed_old_then_new,  # noqa: F401 (fixtures)
                           load_installer, old_release, version_of)

FIX_RELEASE = "2026.10.30c"
CHECK = ("Every install's check is the installer's exit 0 with the line it prints last, `RESULT: INSTALLED TREE "
         "MATCHES bridge <the release's version>` (the installer runs `bridge-check.py` itself).")
SIGNS = ("An install over an older release installed whole also changes the installed `VERSION` and prints the "
         "installer's `previous` line, `previous <version> kept at <folder>` with the spaces that align its columns;")
AGAIN = "the same release installed again changes neither and prints none;"
REPEAT = "and a repeat after an interrupted install prints that line or none, as far as the first run got."
MANIFEST_DST = os.path.join("cursor-bridge", "MANIFEST.json")


def step1():
    return S.flat(S.section(S.read(S.CALIBRATE), S.STEP1, 2))


def raw_previous(out):
    return [line for line in out.splitlines() if line.split()[:1] == ["previous"]]


def ends_on_the_check(rc, out):
    return rc == 0 and out.strip().splitlines()[-1] == "RESULT: INSTALLED TREE MATCHES bridge " + NEW_VERSION


def test_bug037_every_install_ends_on_the_check_the_run_sheet_names(installed_old_then_new):
    assert CHECK in step1(), "R-038: step 1's one check"
    _, out = installed_old_then_new
    assert ends_on_the_check(0, out), out


def test_bug037_a_whole_install_over_an_older_release_prints_the_previous_line_as_named(installed_old_then_new):
    assert SIGNS in step1(), "R-038: step 1's signs of an install over an older release"
    target, out = installed_old_then_new
    lines = raw_previous(out)
    assert len(lines) == 1, out
    assert re.match(r"\s*previous {2,}\S+ kept at ", lines[0]), "the installer's columns: " + lines[0]
    m = re.fullmatch(r"previous (\S+) kept at (.+)", " ".join(lines[0].split()))
    assert m and m.group(1) == OLD_VERSION, "the line does not read `previous <version> kept at <folder>`: " + lines[0]
    assert version_of(target) == NEW_VERSION != OLD_VERSION


def test_bug037_the_same_release_again_changes_nothing_the_signs_name(tmp_path, installed_old_then_new):
    assert AGAIN in step1(), "R-038: step 1's clause for the same release installed again"
    target, first = installed_old_then_new
    assert raw_previous(first), "the first install printed the line this test expects gone: " + first
    rc, out = install_new(tmp_path, target)
    assert ends_on_the_check(rc, out), out
    assert version_of(target) == NEW_VERSION and raw_previous(out) == [], out


@pytest.mark.parametrize("killed", ["before the manifest", "after the manifest"])
def test_bug037_a_repeat_after_an_interrupted_install_prints_the_line_or_none(tmp_path, old_release, monkeypatch, killed):
    assert REPEAT in step1(), "R-038: step 1's clause for a repeat after an interrupted install"
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    target = tmp_path / ".claude"
    assert install_old(tmp_path, old_release, target)[0] == 0
    bi = load_installer(RELEASE)
    real, state = bi.shutil.copyfile, {"manifest": False, "killed": False}

    def copyfile(src, dst, **kwargs):
        d = str(dst)
        if "cursor-bridge-previous" not in d:                  # the release's own copy, not the keeping of the older one
            at_manifest = d.endswith(MANIFEST_DST)
            if (killed == "before the manifest" and at_manifest) or (killed == "after the manifest" and state["manifest"]):
                state["killed"] = True
                raise OSError("killed %s" % killed)
            state["manifest"] = state["manifest"] or at_manifest
        return real(src, dst, **kwargs)
    with monkeypatch.context() as m:
        m.setattr(bi.shutil, "copyfile", copyfile)
        with pytest.raises(OSError):
            bi.install(str(target), False, anyway=True)
    assert state["killed"], killed
    rc, out = install_new(tmp_path, target)
    assert ends_on_the_check(rc, out), out
    expected = [OLD_VERSION] if killed == "before the manifest" else []
    assert [line.split()[1] for line in raw_previous(out)] == expected, out


def test_bug037_the_fix_release_entry_stands_above_2026_10_30b():
    found = S.headings()
    assert found.index(FIX_RELEASE) + 1 == found.index("2026.10.30b"), found[:3]
    assert found[0] == S.version() and FIX_RELEASE <= found[0], found[:3]
    body = S.entry(FIX_RELEASE)
    lines = body.split("\n")
    at = [lines.index(p) for p in S.PARTS[:3]]
    assert at == sorted(at), at
    for p in S.PARTS[:3]:
        assert body.count(p) == 1 and [l for l in S.part(body, p) if l.startswith("- ")], p
    S.marks_are_phases([l for l in S.part(body, "**Running projects must**") if l.strip()])
    rolled = [l for l in S.part(body, "**If rolled back**") if l.startswith("- ")]
    S.marks_are_phases(rolled)
    note, ok = S.load(S.INSTALL, "bridge_install_for_bug037").rolled_back_note(S.CHANGELOG, FIX_RELEASE, "2026.10.30b")
    assert ok and all(item in note for item in rolled), note[:200]
    joined = S.flat(body)
    for words in ("BUG-037", "No program changed", "`previous <version> kept at <folder>`",
                  "`RESULT: INSTALLED TREE MATCHES bridge <the release's version>`",
                  "`/calibrate-bridge` before the next increment", "the way back is 2026.10.30b"):
        assert words in joined, words
    fixed = S.flat(S.entry("2026.10.30b"))
    assert "seeds as before;" not in fixed, "2026.10.30b's sentence on an increment in flight at its install"
    assert "seeds rounds 1 to the highest round the launcher did not log" in fixed
