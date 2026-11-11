"""TASK-053: release B2's stamp (R-064).

enforces: docs/BUILD_PLAN.md TASK-053 (its Done when: VERSION reads 2026.11.<dd>a, sorting after 2026.11.09a; the
CHANGELOG entry naming release B2 with What changed by row, R-057 to R-064, R-063 as the increment after the stamp,
Running projects must with its phase-marked items, If rolled back as `bridge-install.py --rollback` does it with the
effects observed over a migrated scratch copy of this repository's records, their lines quoted, and the items for the
maintainer; every row R-057 to R-062 and R-064 built with an Evidence cell in the constraints' grammar, R-063 planned or
built); docs/REQUIREMENTS.md R-064; bridge/cursor-bridge/workflow/types/host-extension.md, `planning.stages` (the field
acceptance names its stand-in while the trial project has no increment at the gate). Supervisor-written; no builder run.
The entry is read by its heading, so a later release above it leaves these tests standing; VERSION, the manifest and
project.json are checked against the newest heading.

- test_r064_version_entry_manifest_and_project_agree enforces: VERSION is the newest heading, the version make-manifest.py
  stamps, MANIFEST.json's, project.json's `version` and `state.bridge` and the status file's `Bridge version:`, with the
  manifest's fingerprints of VERSION and CHANGELOG.md those of the files as they stand.
- test_r064_the_version_is_the_stamp_s_form_and_sorts_after_2026_11_09a enforces: `2026.11.<dd>a`, directly above
  2026.11.09a, the newest sorting after every other as the installer compares versions.
- test_r064_the_entry_has_its_parts_and_its_rolled_back_items_reach_the_installer enforces: the parts on lines of their own
  in order, the lead naming release B2 and the one new file, and bridge-install.py's rolled_back_note holding every If
  rolled back item.
- test_r064_what_changed_names_every_row enforces: What changed by row, R-057 to R-064, R-063 as TASK-054 after the
  stamp, BUG-044 with R-062.
- test_r064_every_running_projects_item_is_phase_marked_and_the_items_are_named enforces: the phase marks and the items
  the plan names (the migration at the next checkpoint, `--check` first, a repairable `cannot read` record repaired, a
  merged brief left header-less, a `cannot write` status file trimmed first, the records-only commit, the caps on the
  body, the two findings and the refusal and what each asks, `historic: true`, the retired second readings, the text in
  force from the calibration reopening no gate), each by words a reader acts on.
- test_r064_if_rolled_back_quotes_the_observed_lines enforces: the program and its allow entry removed with the release,
  the older programs reading the prose and never the header, and the lines the installed checkers printed over the
  migrated scratch copy (run/supervisor/task053_rollback_observe.py, run 2026-11-11), quoted: completion-check's search
  finding the same IDs, inventory-check's whole-file count before and after under both caps, and conformance-check's one
  more NOTE; and that the allow entry it names is in settings.bridge.json.
- test_r064_the_field_acceptance_names_its_stand_in enforces: the TDP's trial and its stand-in while it has no
  increment at the gate, and the two projects that calibrate when the owner resumes them.
- test_r064_the_items_for_the_maintainer_are_listed enforces: the plan's three items.
- test_r064_every_row_is_built_with_evidence_in_the_grammar enforces: R-057 to R-062 and R-064 built, R-063 planned or
  built, each built row's labels read as the grammar says (tests/test_release_t_stamp.py's reading), a `<label>: <test>`
  entry for each, at least one test, every test named existing.
- test_r064_the_completion_check_passes_in_plan_mode enforces: `completion-check.py --mode plan`, RESULT OK; it skips
  only where no repository exists, a mutation run's copy, and never on CI.
"""
import json
import os
import re
import subprocess
import sys

import pytest

from phase_modules import read
from workflow_files import BRIDGE, flat
from test_release_t_stamp import labels_of, load, named_tests

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
PREVIOUS = "2026.11.09a"
RELEASE_B2 = "2026.11.11a"
PARTS = ("**What changed**", "**Running projects must**", "**If rolled back**", "**Field acceptance**", "**For the maintainer**")
GLOSSARY_PHASES = ("intake", "design", "mockups", "planning", "configuration", "building", "done", "changing")
BUILT_ROWS = ["R-%03d" % n for n in range(57, 63)] + ["R-064"]
MIGRATE_RULE = "Bash(python ~/.claude/cursor-bridge/records-migrate.py:*)"


def version():
    return open(VERSION_FILE, encoding="utf-8").read().strip()


def headings():
    return re.findall(r"^## (\d{4}\.\d{2}\.\d{2}[a-z]?)[ \t]*$", read(CHANGELOG), re.M)


def entry():
    text = read(CHANGELOG)
    start = text.index("\n## " + RELEASE_B2 + "\n")
    end = text.index("\n---\n", start)
    return text[start + 1:end]


def part(title):
    lines = entry().split("\n")
    i = lines.index(title)
    j = next((k for k in range(i + 1, len(lines)) if lines[k] in PARTS), len(lines))
    return lines[i + 1:j]


def items(title):
    return [l for l in part(title) if l.startswith("- ")]


def test_r064_version_entry_manifest_and_project_agree():
    mm = load(MAKE_MANIFEST, "make_manifest_for_b2_stamp")
    v = version()
    assert v >= RELEASE_B2, "the stamp in force is release B2's or a later release's"
    assert mm.pick_version(None) == headings()[0] == v, "VERSION is the newest CHANGELOG heading"
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    assert manifest["version"] == v, "MANIFEST.json carries VERSION's version"
    for rel, path in (("cursor-bridge/VERSION", VERSION_FILE), ("cursor-bridge/CHANGELOG.md", CHANGELOG)):
        assert manifest["files"].get(rel) == mm.norm_hash(path), "the manifest is regenerated after %s" % rel
    project = json.load(open(PROJECT, encoding="utf-8"))
    assert project["version"] == v, "project.json's version"
    assert project["state"]["bridge"] == v, "project.json's state.bridge"
    assert re.search(r"^Bridge version: %s$" % re.escape(v), read(STATUS), re.M), "the status file's Bridge version line"


def test_r064_the_version_is_the_stamp_s_form_and_sorts_after_2026_11_09a():
    found = headings()
    assert re.fullmatch(r"2026\.11\.\d{2}a", RELEASE_B2) and re.fullmatch(r"\d{4}\.\d{2}\.\d{2}[a-z]", version())
    assert len(found) == len(set(found)), "one entry per release"
    assert found.index(RELEASE_B2) + 1 == found.index(PREVIOUS), "release B2's entry stands directly above %s" % PREVIOUS
    assert RELEASE_B2 > PREVIOUS and version() >= RELEASE_B2
    assert found[0] == version() and all(found[0] > other for other in found[1:]), "the newest version sorts last"


def test_r064_the_entry_has_its_parts_and_its_rolled_back_items_reach_the_installer():
    body = entry()
    lines = body.split("\n")
    at = [lines.index(p) for p in PARTS]                    # ValueError: a part not on a line of its own
    assert at == sorted(at), "the parts in order"
    for p in PARTS:
        assert body.count(p) == 1, p
        assert items(p), "%s holds items" % p
    assert "Release B2" in lines[2], "the lead names release B2"
    assert "one file new (`records-migrate.py`), none removed, one allow entry new" in lines[2]
    inst = load(INSTALL, "bridge_install_for_b2_stamp")
    note, found = inst.rolled_back_note(CHANGELOG, RELEASE_B2, PREVIOUS)
    assert found and "## " + RELEASE_B2 in note, "a rollback to %s writes this entry's items" % PREVIOUS
    assert "This release's entry names nothing to restore." not in note
    for item in items("**If rolled back**"):
        assert item in note, "the installer's ROLLED-BACK.md holds every If rolled back item"


def test_r064_what_changed_names_every_row():
    joined = flat(" ".join(items("**What changed**")))
    for row in ["R-%03d" % n for n in range(57, 65)]:
        assert row in joined, row
    assert "R-063, TASK-054, the increment after this stamp" in joined
    assert "BUG-044" in joined and "R-062" in joined
    for program in ("`bridge_env.py`", "`records-migrate.py"):
        assert program in joined, program


def marks_are_phases(lines):
    for l in lines:
        m = re.match(r"- \*\(([^)]*)\)\* ", l)
        assert m, "every item names its phase: " + l[:60]
        if m.group(1) == "all phases":
            continue
        named = m.group(1).split(", ")
        assert set(named) <= set(GLOSSARY_PHASES), "a phase the Glossary names: " + m.group(1)
        assert "building" not in named or "changing" in named, "building with changing: " + l[:60]


def test_r064_every_running_projects_item_is_phase_marked_and_the_items_are_named():
    lines = [l for l in part("**Running projects must**") if l.strip()]
    assert lines and all(l.startswith("- ") for l in lines), "every line an item"
    marks_are_phases(lines)
    marks_are_phases(items("**If rolled back**"))
    joined = flat(" ".join(lines))
    for words in (
        "`RESULT: INSTALLED TREE MATCHES bridge " + RELEASE_B2 + "`",
        "`python ~/.claude/cursor-bridge/records-migrate.py --check` from the Workspace root first",
        "at the next checkpoint",
        "a status file listed `cannot write` is trimmed first",
        "each repairable `cannot read` record is repaired in its prose",
        "a merged brief the program cannot read is never repaired: it stays header-less and is named in the report",
        "committed as the calibration's checkpoint in a records-only commit of its own",
        "the status file's caps count the body after the header",
        "`HEADER DISAGREES: <key>`",
        "`HEADER MALFORMED: <path>:<line> <what>`",
        "`refused - header: `",
        "a stop, never a model's failure",
        "`historic: true`",
        "a lift in the header that no owner's line holds lifts nothing",
        "The retired second readings",
        "reopening no gate",
        "takes the no-delta path",
    ):
        assert words in joined, words


def test_r064_if_rolled_back_quotes_the_observed_lines():
    joined = flat(" ".join(items("**If rolled back**")))
    for words in (
        "`bridge-install.py --rollback`",
        "`" + MIGRATE_RULE + "`",
        "falls to the classifier until the reinstall",
        "read the prose and never the header",
        "a scratch copy of this repository's records",
        "never the live records",
        "the same IDs",
        "`note: status: 39 lines / 9943 chars (cap 120 / 12000)`",
        "`note: status: 52 lines / 11986 chars (cap 120 / 12000)`",
        "under both caps",
        "is not the status file's (\"release b2's stage h1 closed 2026-11-11): bring it up to date at this reflection point`",
        "`conformance-check: 24 OK, 0 MISSING, 2 NOTE`",
        "`conformance-check: 24 OK, 0 MISSING, 3 NOTE`",
        "`HEADER DISAGREES: <key>`",
    ):
        assert words in joined, words
    for checker in ("`completion-check.py --mode plan`", "`plan-check.py`", "`diagram-check.py --mode code`",
                    "`workflow-check.py --status`", "`session-start.py`", "`loop-guard.py`", "`inventory-check.py`",
                    "`conformance-check.py`"):
        assert checker in joined, checker
    allow = json.load(open(SETTINGS, encoding="utf-8"))["permissions"]["allow"]
    assert MIGRATE_RULE in allow, "the allow entry the rollback removes is the release's"


def test_r064_the_field_acceptance_names_its_stand_in():
    joined = flat(" ".join(items("**Field acceptance**")))
    for words in ("The TDP, the trial,", "While it has no increment at the gate", "stand in",
                  "recorded when its next increment comes", "reAngle and the video factory calibrate when the owner resumes them"):
        assert words in joined, words


def test_r064_the_items_for_the_maintainer_are_listed():
    joined = flat(" ".join(items("**For the maintainer**")))
    for words in ("`pyyaml` at run time once the installed programs have a declared environment",
                  "a header for `run/supervisor/in-flight.md` and the SCOPE files where a second reader appears",
                  "the CHANGELOG template's and the release procedure's migration sentence"):
        assert words in joined, words


def test_r064_every_row_is_built_with_evidence_in_the_grammar():
    cc = load(COMPLETION, "completion_check_for_b2_stamp")
    header, rows = cc.parse_register(read(REGISTER))
    assert len(header) == 5, "the register's five columns"
    by_id = {r[0]: r for r in rows}
    statuses = {rid: by_id[rid][3] for rid in BUILT_ROWS + ["R-063"]}
    assert statuses["R-063"] in ("planned", "built"), "R-063 is TASK-054's, after the stamp"
    for rid in BUILT_ROWS + (["R-063"] if statuses["R-063"] == "built" else []):
        cells = by_id[rid]
        assert len(cells) == 5, rid
        requirement, status, evidence = cells[1], cells[3], cells[4]
        assert status == "built", rid
        entries = [e.strip() for e in evidence.split(";")]
        for label in labels_of(requirement):
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


def test_r064_the_completion_check_passes_in_plan_mode():
    if not os.path.exists(os.path.join(ROOT, ".git")):
        assert "GITHUB_ACTIONS" not in os.environ, "CI holds a checkout, so this test never skips there"
        pytest.skip("completion-check.py reads `git ls-files`, and mutation-run.py's copy holds no repository")
    p = subprocess.run([sys.executable, COMPLETION, "--mode", "plan"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert p.returncode == 0 and "RESULT: OK" in p.stdout, p.stdout[-800:]
