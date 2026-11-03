"""TASK-045: release T's stamp (R-056).

enforces: docs/BUILD_PLAN.md TASK-045 (its Done when: VERSION reads 2026.11.<dd>a, sorting after 2026.10.30d; the
CHANGELOG entry with What changed by row, Running projects must phase-marked with its items, If rolled back as
`bridge-install.py --rollback` does it, the program items and the three maintainer halves; every row R-045 to R-056 and
R-042 built with an Evidence cell in the constraints' grammar); docs/REQUIREMENTS.md R-056; docs/BUILD_PLAN.md, Release
T's constraints (the labels of a Requirement cell, an Evidence cell's `<label>: <test>` entries). Supervisor-written; no
builder run. The entry is read by its heading, so a later release above it leaves these tests standing; VERSION, the
manifest and project.json are checked against the newest heading.

- test_r056_version_entry_manifest_and_project_agree enforces: VERSION is the newest heading, the version make-manifest.py
  stamps, MANIFEST.json's, project.json's `version` and `state.bridge` and the status file's `Bridge version:`, with the
  manifest's fingerprints of VERSION and CHANGELOG.md those of the files as they stand.
- test_r056_the_version_is_the_stamp_s_form_and_sorts_after_2026_10_30d enforces: `2026.11.<dd>a`, directly above
  2026.10.30d, the newest sorting after every other as the installer compares versions.
- test_r056_the_entry_has_its_parts_and_its_rolled_back_items_reach_the_installer enforces: the parts on lines of their
  own in order, the lead naming release T, and bridge-install.py's rolled_back_note holding every If rolled back item.
- test_r056_what_changed_names_every_row enforces: What changed by row, R-045 to R-056, R-042's revision, BUG-039 as
  TASK-043, BUG-041, BUG-042 and BUG-043.
- test_r056_every_running_projects_item_is_phase_marked_and_the_items_are_named enforces: the phase marks and the items
  the plan names, each by words a reader acts on.
- test_r056_if_rolled_back_says_what_the_rollback_does enforces: the allow rules removed, the kept weekly file, BUG-042's
  false OK, the voids an older guard reads, the text falling back; and that a by-hand `--strip` is not said to fall to the
  classifier, since TASK-041 wrote no form of it (the heavy-launch rules admit it, on 2026.10.30d's rules too).
- test_r056_the_six_allow_rules_are_the_release_s enforces: the six allow and two deny rules If rolled back names are in
  settings.bridge.json, and no `--strip` form is.
- test_r056_the_program_items_and_the_three_halves_are_listed enforces: the program items for the maintainer and the
  three halves outside bridge/.
- test_r056_every_row_is_built_with_evidence_in_the_grammar enforces: the labels read as the grammar says from the
  register parsed as completion-check.py parses it, a `<label>: <test>` entry for each, at least one test where a cell
  carries none, every test named existing.
- test_r056_the_grammar_reads_the_plan_s_examples enforces: the plan's own four examples of the grammar.
- test_r056_the_completion_check_passes_in_done_mode enforces: `completion-check.py --mode done`, RESULT OK.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys

from phase_modules import read
from workflow_files import BRIDGE, flat

ROOT = os.path.dirname(BRIDGE)
CB = os.path.join(BRIDGE, "cursor-bridge")
CHANGELOG = os.path.join(CB, "CHANGELOG.md")
VERSION_FILE = os.path.join(CB, "VERSION")
MANIFEST = os.path.join(CB, "MANIFEST.json")
SETTINGS = os.path.join(CB, "settings.bridge.json")
MAKE_MANIFEST = os.path.join(ROOT, "tools", "make-manifest.py")
INSTALL = os.path.join(CB, "bridge-install.py")
COMPLETION = os.path.join(CB, "completion-check.py")
REGISTER = os.path.join(ROOT, "docs", "REQUIREMENTS.md")
STATUS = os.path.join(ROOT, "docs", "PROJECT_STATUS.md")
PROJECT = os.path.join(ROOT, "project.json")
PREVIOUS = "2026.10.30d"
RELEASE_T = "2026.11.03a"
PARTS = ("**What changed**", "**Running projects must**", "**If rolled back**", "**Field acceptance**", "**For the maintainer**")
GLOSSARY_PHASES = ("intake", "design", "mockups", "planning", "configuration", "building", "done", "changing")
ROWS = ["R-042"] + ["R-%03d" % n for n in range(45, 57)]
ALLOW_RULES = ("Bash(git branch -D:*)", "Bash(gh pr list:*)", "Bash(gh issue list:*)", "Bash(git tag stage-review/*)",
               "Bash(git cat-file -p stage-review/*)", "Bash(git branch -r)")
DENY_RULES = ("Bash(git tag stage-review/* -*)", "PowerShell(*git tag stage-review/* -*)")


def load(path, name):
    """A bridge program loaded afresh, leaving no __pycache__ beside it."""
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


def entry():
    text = read(CHANGELOG)
    start = text.index("\n## " + RELEASE_T + "\n")
    end = text.index("\n---\n", start)
    return text[start + 1:end]


def part(title):
    lines = entry().split("\n")
    i = lines.index(title)
    j = next((k for k in range(i + 1, len(lines)) if lines[k] in PARTS), len(lines))
    return lines[i + 1:j]


def items(title):
    return [l for l in part(title) if l.startswith("- ")]


def test_r056_version_entry_manifest_and_project_agree():
    mm = load(MAKE_MANIFEST, "make_manifest_for_t_stamp")
    v = version()
    assert mm.pick_version(None) == headings()[0] == v, "VERSION is the newest CHANGELOG heading"
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    assert manifest["version"] == v, "MANIFEST.json carries VERSION's version"
    for rel, path in (("cursor-bridge/VERSION", VERSION_FILE), ("cursor-bridge/CHANGELOG.md", CHANGELOG)):
        assert manifest["files"].get(rel) == mm.norm_hash(path), "the manifest is regenerated after %s" % rel
    project = json.load(open(PROJECT, encoding="utf-8"))
    assert project["version"] == v, "project.json's version"
    assert project["state"]["bridge"] == v, "project.json's state.bridge"
    assert re.search(r"^Bridge version: %s$" % re.escape(v), read(STATUS), re.M), "the status file's Bridge version line"


def test_r056_the_version_is_the_stamp_s_form_and_sorts_after_2026_10_30d():
    found = headings()
    assert re.fullmatch(r"\d{4}\.\d{2}\.\d{2}[a-z]", version())
    assert len(found) == len(set(found)), "one entry per release"
    assert found.index(RELEASE_T) + 1 == found.index(PREVIOUS), "release T's entry stands directly above %s" % PREVIOUS
    assert version() > PREVIOUS
    assert found[0] == version() and all(found[0] > other for other in found[1:]), "the newest version sorts last"


def test_r056_the_entry_has_its_parts_and_its_rolled_back_items_reach_the_installer():
    body = entry()
    lines = body.split("\n")
    at = [lines.index(p) for p in PARTS]                    # ValueError: a part not on a line of its own
    assert at == sorted(at), "the parts in order"
    for p in PARTS:
        assert body.count(p) == 1, p
        assert items(p), "%s holds items" % p
    assert "Release T" in lines[2], "the lead names release T"
    inst = load(INSTALL, "bridge_install_for_t_stamp")
    note, found = inst.rolled_back_note(CHANGELOG, version(), PREVIOUS)
    assert found and "## " + RELEASE_T in note, "a rollback to %s writes this entry's items" % PREVIOUS
    assert "This release's entry names nothing to restore." not in note
    for item in items("**If rolled back**"):
        assert item in note, "the installer's ROLLED-BACK.md holds every If rolled back item"


def test_r056_what_changed_names_every_row():
    joined = flat(" ".join(items("**What changed**")))
    for row in ROWS[1:]:
        assert row in joined, row
    assert "R-042's revision" in joined
    for fix in ("BUG-039", "TASK-043", "BUG-041", "BUG-042", "BUG-043"):
        assert fix in joined, fix


def marks_are_phases(lines):
    for l in lines:
        m = re.match(r"- \*\(([^)]*)\)\* ", l)
        assert m, "every item names its phase: " + l[:60]
        if m.group(1) == "all phases":
            continue
        named = m.group(1).split(", ")
        assert set(named) <= set(GLOSSARY_PHASES), "a phase the Glossary names: " + m.group(1)
        assert "building" not in named or "changing" in named, "building with changing: " + l[:60]


def test_r056_every_running_projects_item_is_phase_marked_and_the_items_are_named():
    lines = [l for l in part("**Running projects must**") if l.strip()]
    assert lines and all(l.startswith("- ") for l in lines), "every line an item"
    marks_are_phases(lines)
    marks_are_phases(items("**If rolled back**"))
    joined = flat(" ".join(lines))
    for words in (
        "`RESULT: INSTALLED TREE MATCHES bridge " + RELEASE_T + "`",
        "written into the project by `cursor-configurator` from the frozen block",
        "a configuration item",
        "`workflow_dispatch`",
        "run `review-guard.py verify <ID>-r<N>` once more under the new release",
        "read as files with no git command run",
        "returns before any git command and restores nothing",
        "puts HEAD, every local branch and tag and the tree back to the snapshot",
        "only where nothing of yours or a builder's has been committed, made, moved or changed in any of them since the snapshot",
        "A branch still held in another worktree stops it too",
        "`git for-each-ref` against the snapshot file's `refs`",
        "do not run it",
        "for the round's count only",
        "the flag already opened stands",
        "where `verify` would undo such work, cannot be recovered",
        "the copy is removed on the owner's word",
        "a repository re-created at the same path",
        "Remove it only for a re-creation or a clearing you made yourself",
        "Any other stop of the configurator's",
        "never what a test's failure asks for and never a home variable",
        "Read the session's variable names",
        "known limitation",
        "the owner's line is the lift",
        "`<key>-rounds-<id>.sha256`",
        "exit 125",
        "a cleared `.git/bridge`",
        "before its first stripped launch",
        "`--key-file` for a suite",
        "a recorded Decision for a driver",
        "reopening no gate",
        "a check, not a boundary",
    ):
        assert words in joined, words


def test_r056_if_rolled_back_says_what_the_rollback_does():
    joined = flat(" ".join(items("**If rolled back**")))
    for rule in ALLOW_RULES + DENY_RULES:
        assert "`" + rule + "`" in joined, rule
    for words in (
        "So a `git branch -D` outside `stage/` and those commands fall to the classifier",
        "BUG-039's fixes go back with it",
        "voids that launch whatever a later `verify` says",
        "a `--strip` by hand stays admitted",
        "`bridge-install.py --rollback`",
        "`delegation-loop/merge.md`",
        "`.github/workflows/dependency-scan.yml` keeps running",
        "read by no older evaluation",
        "BUG-042's false OK",
        "until the reinstall",
        "`flagged_launch` records an older guard already reads",
        "fall back to the older release's text",
        "TASK-041 wrote no `--strip` form",
    ):
        assert words in joined, words
    assert "`--strip` falls to the classifier" not in joined, "the heavy-launch rules admit `--strip` on the older release too"
    assert "the hooks and the file monitor on" not in joined, "the older premerge has its hooks off; the file monitor alone is lost"


def test_r056_the_six_allow_rules_are_the_release_s():
    allow = json.load(open(SETTINGS, encoding="utf-8"))["permissions"]["allow"]
    for rule in ALLOW_RULES:
        assert rule in allow, rule
    assert not [r for r in allow if "--strip" in r], "TASK-041's observed launch ran on the heavy-launch rules"
    deny = json.load(open(SETTINGS, encoding="utf-8"))["permissions"]["deny"]
    for rule in DENY_RULES:
        assert rule in deny, rule


def test_r056_the_program_items_and_the_three_halves_are_listed():
    joined = flat(" ".join(items("**For the maintainer**")))
    for words in (
        "a conformance floor for the weekly workflow",
        "a driver key file in the launcher",
        "`APPDATA` and `LOCALAPPDATA`",
        "`diagram-check.py`'s file-load form",
        "the guard's records and the launcher's log under `verify`",
        "a program reading the weekly runs and the Dependabot alerts",
        "reading the all-omitted index",
        "`.git/config.worktree`",
        "`worktree-teardown.py` turning hooks off",
        "the hooks a finished parallel branch holds before its switch",
        "a home variable in a `--key-file`",
        "a 125 message telling a refused option from an unknown runner",
        "the secret-like name test's gaps",
        "P10's sentence for the CHANGELOG template",
        "P17's for the release procedure",
        "P7's stamp-procedure half",
    ):
        assert words in joined, words


def labels_of(requirement):
    """The constraints' grammar: the leading token of a parenthesis, a letter D, T or P with digits followed by `)`,
    `,`, `:` or `;`, with every further such token the parenthesis lists after commas before any prose."""
    found = []
    for m in re.finditer(r"\(", requirement):
        at = m.end()
        while True:
            t = re.compile(r"([DTP]\d+)([),:;])").match(requirement, at)
            if not t:
                break
            found.append(t.group(1))
            if t.group(2) != ",":
                break
            at = t.end()
            while requirement[at:at + 1] == " ":
                at += 1
    return set(found)


def test_r056_the_grammar_reads_the_plan_s_examples():
    assert labels_of("x (P5: step 8 and more) y") == {"P5"}
    assert labels_of("x (T24, P6) y") == {"T24", "P6"}
    assert labels_of("x (P2, the by-class line of 2026-10-27) y") == {"P2"}
    assert labels_of("x (T18's rule) y") == set()


def named_tests(text):
    return re.findall(r"tests/[\w./-]+\.py(?:::\w+)?", text)


def test_r056_every_row_is_built_with_evidence_in_the_grammar():
    cc = load(COMPLETION, "completion_check_for_t_stamp")
    header, rows = cc.parse_register(read(REGISTER))
    assert len(header) == 5, "the register's five columns"
    by_id = {r[0]: r for r in rows}
    for rid in ROWS:
        cells = by_id[rid]
        assert len(cells) == 5, rid
        requirement, status, evidence = cells[1], cells[3], cells[4]
        assert status == "built", rid
        entries = [e.strip() for e in evidence.split(";")]
        labels = labels_of(requirement)
        for label in labels:
            hits = [e for e in entries if e.startswith(label + ":") and named_tests(e)]
            assert hits, "%s: no `%s: <test>` entry" % (rid, label)
        tests = named_tests(evidence)
        assert tests, "%s: at least one test" % rid
        for t in tests:
            path, _, node = t.partition("::")
            full = os.path.join(ROOT, *path.split("/"))
            assert os.path.isfile(full), "%s: %s" % (rid, path)
            if node:
                assert re.search(r"^def %s\b" % re.escape(node), read(full), re.M), "%s: %s" % (rid, t)


def test_r056_the_completion_check_passes_in_done_mode():
    p = subprocess.run([sys.executable, COMPLETION, "--mode", "done"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert p.returncode == 0 and "RESULT: OK" in p.stdout, p.stdout[-800:]
