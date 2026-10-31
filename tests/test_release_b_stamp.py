"""TASK-027: release B's stamp and the install run sheet (R-037, R-038).

enforces: docs/BUILD_PLAN.md TASK-027 (its Done when: VERSION bumped and MANIFEST regenerated, VERSION, the CHANGELOG
and the manifest agreeing; the CHANGELOG entry naming release B with its "if rolled back" notes and its "Running
projects must" items, the windowless default among them; the install run sheet reflecting R-038, pause and switch);
docs/REQUIREMENTS.md R-037 (the stamp: VERSION, a regenerated MANIFEST, a CHANGELOG entry with its "if rolled back"
notes) and R-038 (the install mechanics settled by the owner, recorded in INVENTORY's Decisions row, and reflected
in the install run sheet); docs/HARDENING.md, TASK-026's "For TASK-027" list (the new heading first, sorting after
2026.10.25a, `**If rolled back**` on its own line; C-1's run-sheet half). Supervisor-written; no builder run. Release B's
entry is read by its heading, 2026.10.30a, since BUG-036's fix release (2026.10.30b) stands above it; VERSION and the
manifest are checked against the newest heading.

- test_r037_version_changelog_and_manifest_agree enforces: VERSION is the newest CHANGELOG heading, the version
  make-manifest.py stamps, and MANIFEST.json's version, with the manifest's fingerprints of VERSION and CHANGELOG.md
  those of the files as they stand (the manifest regenerated after the entry was written).
- test_r037_the_new_version_sorts_after_2026_10_25a enforces: release B's heading stands directly above 2026.10.25a,
  and the newest heading, VERSION's, sorts after every other heading as the installer compares versions (as text).
- test_r037_the_entry_has_its_three_parts_and_its_rolled_back_items_reach_the_installer enforces: the entry holds
  What changed, Running projects must, If rolled back and Field acceptance, each on a line of its own, in that order,
  and bridge-install.py's rolled_back_note reads this entry's own If rolled back items for a rollback to 2026.10.25a.
- test_r037_every_running_projects_item_is_phase_marked_and_the_windowless_default_is_named enforces: each item of
  Running projects must and If rolled back names its phase, `all phases` or the Glossary's phases, `building` never
  without `changing`; and the items name the windowless default (TASK-030), its floor and its snapshot.
- test_r038_the_run_sheet_says_pause_and_switch enforces: step 1's run sheet pauses the bridge's own build and
  switches its checkout to main before the install.
- test_r038_the_run_sheet_tells_the_maintainer_and_never_passes_anyway enforces: C-1's run-sheet half, the
  installer's same-version refusal named, `--anyway` never passed by the owner, the maintainer told; the owner's
  three commands as written, `--anyway` in none of them (BUG-037).
- test_r037_step_4_sends_an_increment_in_flight_to_the_entry enforces: step 4's rule for an increment whose snapshot
  or rounds were taken under the older release (TASK-026, M3).
"""
import importlib.util
import json
import os
import re
import sys

from phase_modules import read, section
from workflow_files import BRIDGE, flat

ROOT = os.path.dirname(BRIDGE)
CB = os.path.join(BRIDGE, "cursor-bridge")
CHANGELOG = os.path.join(CB, "CHANGELOG.md")
VERSION_FILE = os.path.join(CB, "VERSION")
MANIFEST = os.path.join(CB, "MANIFEST.json")
MAKE_MANIFEST = os.path.join(ROOT, "tools", "make-manifest.py")
INSTALL = os.path.join(CB, "bridge-install.py")
CALIBRATE = os.path.join(BRIDGE, "commands", "calibrate-bridge.md")
STEP1 = "1. Verify the install — deterministically"
STEP4 = "4. Apply the delta by phase — reopen nothing"
PREVIOUS = "2026.10.25a"
RELEASE_B = "2026.10.30a"
GLOSSARY_PHASES = ("intake", "design", "mockups", "planning", "configuration", "building", "done", "changing")
PARTS = ("**What changed**", "**Running projects must**", "**If rolled back**", "**Field acceptance**")


def load(path, name):
    """A bridge program loaded afresh, leaving no __pycache__ beside it (HARDENING, stage B5, round 1's note)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = before
    return mod


def version():
    return open(VERSION_FILE, encoding="utf-8").read().strip()


def headings():
    return re.findall(r"^## (\d{4}\.\d{2}\.\d{2}[a-z]?)[ \t]*$", read(CHANGELOG), re.M)


def entry(v=RELEASE_B):
    """Release B's entry (or version v's): from its heading to the `---` that closes it."""
    text = read(CHANGELOG)
    start = text.index("\n## " + v + "\n")
    end = text.index("\n---\n", start)
    return text[start + 1:end]


def part(body, title):
    """The lines of one part of an entry, from its title line to the next part's title line."""
    lines = body.split("\n")
    i = lines.index(title)
    j = next((k for k in range(i + 1, len(lines)) if lines[k] in PARTS), len(lines))
    return lines[i + 1:j]


def test_r037_version_changelog_and_manifest_agree():
    mm = load(MAKE_MANIFEST, "make_manifest_for_stamp")
    v = version()
    assert re.fullmatch(r"\d{4}\.\d{2}\.\d{2}[a-z]", v), v
    assert mm.pick_version(None) == headings()[0] == v, "R-037: VERSION is the newest CHANGELOG heading"
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    assert manifest["version"] == v, "R-037: MANIFEST.json carries VERSION's version"
    for rel, path in (("cursor-bridge/VERSION", VERSION_FILE), ("cursor-bridge/CHANGELOG.md", CHANGELOG)):
        assert manifest["files"].get(rel) == mm.norm_hash(path), "R-037: the manifest is regenerated after %s" % rel


def test_r037_the_new_version_sorts_after_2026_10_25a():
    found = headings()
    assert len(found) == len(set(found)), "one entry per release"
    assert found.index(RELEASE_B) + 1 == found.index(PREVIOUS), "R-037: release B's entry stands directly above %s" % PREVIOUS
    assert RELEASE_B > PREVIOUS, "R-037: release B sorts after %s" % PREVIOUS
    assert found[0] == version() and all(found[0] > other for other in found[1:]), "R-037: the newest version sorts last"


def test_r037_the_entry_has_its_three_parts_and_its_rolled_back_items_reach_the_installer():
    body = entry()
    lines = body.split("\n")
    at = [lines.index(p) for p in PARTS]                    # ValueError: a part not on a line of its own
    assert at == sorted(at), "R-037: the parts in the header's order"
    for p in PARTS:
        assert body.count(p) == 1, p
        assert [l for l in part(body, p) if l.startswith("- ")], "R-037: %s holds items" % p
    assert "release B" in lines[2], "R-037: the lead names release B"
    inst = load(INSTALL, "bridge_install_for_stamp")
    note, found = inst.rolled_back_note(CHANGELOG, version(), PREVIOUS)
    assert found and "## " + RELEASE_B in note, "R-037: a rollback to %s writes this entry's items" % PREVIOUS
    assert "This release's entry names nothing to restore." not in note
    for item in [l for l in part(body, "**If rolled back**") if l.startswith("- ")]:
        assert item in note, "R-037: the installer's ROLLED-BACK.md holds every If rolled back item"


def marks_are_phases(items):
    """Each item opens with `*(all phases)*` or a list of the Glossary's phases, and one marked `building` also names
    `changing`, which runs the same loop (the entries' own convention)."""
    for l in items:
        m = re.match(r"- \*\(([^)]*)\)\* ", l)
        assert m, "every item names its phase: " + l[:60]
        if m.group(1) == "all phases":
            continue
        named = m.group(1).split(", ")
        assert set(named) <= set(GLOSSARY_PHASES), "a phase the Glossary names: " + m.group(1)
        assert "building" not in named or "changing" in named, "building with changing: " + l[:60]


def test_r037_every_running_projects_item_is_phase_marked_and_the_windowless_default_is_named():
    items = [l for l in part(entry(), "**Running projects must**") if l.strip()]
    assert items
    marks_are_phases(items)
    marks_are_phases([l for l in part(entry(), "**If rolled back**") if l.startswith("- ")])
    joined = flat(" ".join(items))
    for words in ("windowless default", "`Windowless test suite` floor", "`windowless-default.snapshot.md`",
                  "`Workflows line`", "`/calibrate-bridge` before the next increment",
                  "`round <N> is off the count (current <C>)`", "`handoff/<ID>-r<N>.md`"):
        assert words in joined, words


def test_r038_the_run_sheet_says_pause_and_switch():
    s1 = flat(section(read(CALIBRATE), STEP1, 2))
    assert ("**Where the bridge's repository is being built on a branch by its own supervisor**, the run sheet "
            "pauses that work before the install (R-038): no builder, review, CI watch or suite running in it and "
            "everything committed; then its checkout is switched to `main`, the first of the three commands, and "
            "the release is installed from it.") in s1, "R-038: pause, then switch to main"
    assert "`git -C <the bridge's repository> switch main`" in s1


def test_r038_the_run_sheet_tells_the_maintainer_and_never_passes_anyway():
    s1 = flat(section(read(CALIBRATE), STEP1, 2))
    assert ("If the installer refuses with `the release folder carries version <version>, the release installed "
            "now, but not its files`, `main` has moved past the release's stamp: the owner never passes "
            "`--anyway`, which is for the maintainer's rehearsals, and tells the maintainer.") in s1, "C-1"
    assert "never a dry run" in s1, "the install is checked on the real run"
    commands = ("three commands — `git -C <the bridge's repository> switch main`, `git -C <the bridge's repository> "
                "pull --ff-only`, then `python <the bridge's repository>/bridge/cursor-bridge/bridge-install.py`, which")
    assert commands in s1, "the owner's three commands, as written, the installer's with no flag (BUG-037)"
    assert s1.count("anyway") == 1, "`--anyway` named in step 1 only in the refusal's sentence, never in a command (BUG-037)"


def test_r037_step_4_sends_an_increment_in_flight_to_the_entry():
    s4 = flat(section(read(CALIBRATE), STEP4, 2))
    assert ("- An increment in flight whose Review B snapshot or review rounds were taken under the older release "
            "follows the items the release's entry names for it: the names the installed review guard reads, how it "
            "counts the rounds already run, and how the next brief is named.") in s4, "M3: step 4's rule"
