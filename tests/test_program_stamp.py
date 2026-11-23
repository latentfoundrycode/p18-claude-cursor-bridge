"""TASK-081: the program release's stamp (R-102).

enforces: docs/BUILD_PLAN.md TASK-081 (its Done when: VERSION reads 2026.<mm>.<dd>a, sorting after 2026.11.12a, whose
entry this one stands above; the entry names the program release with What changed by row, R-076 to R-101 and R-105,
release S's rows as records only, Running projects must with its phase-marked items, If rolled back with each effect
observed on a scratch copy and its line quoted, and the items left for a later release by name; the manifest regenerated;
every row R-066 to R-101 and R-103 to R-105 built with an Evidence cell in the register's grammar; R-102's own flip in the
accept commit); docs/REQUIREMENTS.md R-102 and R-096 (the mark stated in the release's entry). Supervisor-written; no
builder run. The entry is read by its heading, so a later release above it leaves these tests standing; VERSION, the
manifest, project.json and the status file are checked against the newest heading.

- test_r102_version_entry_manifest_and_project_agree enforces: VERSION is the newest heading, the version
  make-manifest.py stamps, MANIFEST.json's, project.json's `version` and `state.bridge` and the status file's
  `Bridge version:`, the manifest's fingerprints of VERSION and CHANGELOG.md those of the files as they stand.
- test_r102_the_version_is_the_stamp_s_form_and_sorts_after_2026_11_12a enforces: `2026.<mm>.<dd>a`, directly above
  2026.11.12a, the newest sorting after every other as the installer compares versions.
- test_r102_the_entry_has_its_parts_and_its_rolled_back_items_reach_the_installer enforces: the three parts on lines of
  their own in order, the lead naming the program release, its two new files and two allow entries, and
  bridge-install.py's rolled_back_note holding every If rolled back item.
- test_r102_what_changed_names_every_row enforces: R-076 to R-101 and R-105 by row, release S's rows as records only,
  and R-096's mark with what it is for.
- test_r102_every_running_projects_item_is_phase_marked_and_the_items_are_named enforces: the phase marks and the
  items the plan names, each by words a reader acts on.
- test_r102_if_rolled_back_quotes_the_observed_lines enforces: the lines run/supervisor/task081_rollback_observe.py
  printed on 2026-11-23 over a scratch copy at eccc484, quoted, and that the two allow entries it names are this
  release's.
- test_r102_the_items_left_for_a_later_release_are_named enforces: the improvements release and the leads by name.
- test_r102_every_row_is_built_with_evidence_in_the_grammar enforces: R-066 to R-105 built, each built row's labels
  read as the grammar says (tests/test_release_t_stamp.py's reading), every test it names existing.
"""
import json
import os
import re

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
PREVIOUS = "2026.11.12a"
RELEASE = "2026.11.23a"
PARTS = ("**What changed**", "**Running projects must**", "**If rolled back**")
GLOSSARY_PHASES = ("intake", "design", "mockups", "planning", "configuration", "building", "done", "changing")
ROWS = ["R-%03d" % n for n in range(66, 106)]
NEW_RULES = ("Bash(python ~/.claude/cursor-bridge/in-flight.py:*)", "Bash(python ~/.claude/cursor-bridge/push-scan.py:*)")


def version():
    return open(VERSION_FILE, encoding="utf-8").read().strip()


def headings():
    return re.findall(r"^## (\d{4}\.\d{2}\.\d{2}[a-z]?)[ \t]*$", read(CHANGELOG), re.M)


def entry():
    text = read(CHANGELOG)
    start = text.index("\n## " + RELEASE + "\n")
    end = text.index("\n## ", start + 1)
    return text[start + 1:end]


def part(title):
    lines = entry().split("\n")
    i = lines.index(title)
    j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith("**")), len(lines))
    return lines[i + 1:j]


def items(title):
    return [l for l in part(title) if l.startswith("- ")]


def test_r102_version_entry_manifest_and_project_agree():
    mm = load(MAKE_MANIFEST, "make_manifest_for_program_stamp")
    v = version()
    assert v >= RELEASE, "the stamp in force is the program release's or a later release's"
    assert mm.pick_version(None) == headings()[0] == v, "VERSION is the newest CHANGELOG heading"
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    assert manifest["version"] == v, "MANIFEST.json carries VERSION's version"
    for rel, path in (("cursor-bridge/VERSION", VERSION_FILE), ("cursor-bridge/CHANGELOG.md", CHANGELOG)):
        assert manifest["files"].get(rel) == mm.norm_hash(path), "the manifest is regenerated after %s" % rel
    project = json.load(open(PROJECT, encoding="utf-8"))
    assert project["version"] == v, "project.json's version"
    assert project["state"]["bridge"] == v, "project.json's state.bridge"
    assert re.search(r"^Bridge version: %s$" % re.escape(v), read(STATUS), re.M), "the status file's Bridge version line"


def test_r102_the_version_is_the_stamp_s_form_and_sorts_after_2026_11_12a():
    found = headings()
    assert re.fullmatch(r"2026\.\d{2}\.\d{2}a", RELEASE) and re.fullmatch(r"\d{4}\.\d{2}\.\d{2}[a-z]", version())
    assert len(found) == len(set(found)), "one entry per release"
    assert found.index(RELEASE) + 1 == found.index(PREVIOUS), "the entry stands directly above %s" % PREVIOUS
    assert RELEASE > PREVIOUS and version() >= RELEASE
    assert found[0] == version() and all(found[0] > other for other in found[1:]), "the newest version sorts last"


def test_r102_the_entry_has_its_parts_and_its_rolled_back_items_reach_the_installer():
    body = entry()
    lines = body.split("\n")
    at = [lines.index(p) for p in PARTS]                    # ValueError: a part not on a line of its own
    assert at == sorted(at), "the parts in order"
    for p in PARTS:
        assert body.count(p) == 1, p
        assert items(p), "%s holds items" % p
    assert lines[2].startswith("**The program release**"), "the lead names the program release"
    assert "two files new (`in-flight.py`, `push-scan.py`), none removed, two allow entries new" in lines[2]
    inst = load(INSTALL, "bridge_install_for_program_stamp")
    note, found = inst.rolled_back_note(CHANGELOG, RELEASE, PREVIOUS)
    assert found and "## " + RELEASE in note, "a rollback to %s writes this entry's items" % PREVIOUS
    assert "This release's entry names nothing to restore." not in note
    for item in items("**If rolled back**"):
        assert item in note, "the installer's ROLLED-BACK.md holds every If rolled back item"


def test_r102_what_changed_names_every_row():
    joined = flat(" ".join(items("**What changed**")))
    for n in list(range(76, 102)) + [102, 105]:
        assert "**R-%03d" % n in joined, "R-%03d by row" % n
    assert "release S's rows** R-066 to R-075, R-103 and R-104" in joined and "as records only" in joined
    assert "`<!-- not run -->`" in joined, "R-096: the mark stated in the release's entry"
    assert "quotes a command as an example and does not instruct it" in joined
    for program in ("`push-scan.py", "`in-flight.py", "`review-guard.py ready <pr>`", "`trace-check.py --moves"):
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


def test_r102_every_running_projects_item_is_phase_marked_and_the_items_are_named():
    lines = [l for l in part("**Running projects must**") if l.strip()]
    assert lines and all(l.startswith("- ") for l in lines), "every line an item"
    marks_are_phases(lines)
    marks_are_phases(items("**If rolled back**"))
    joined = flat(" ".join(lines))
    for words in (
        "with every project paused at a merge boundary",
        "`RESULT: INSTALLED TREE MATCHES bridge " + RELEASE + "`",
        "`/calibrate-bridge`",
        "`cursor-agent status`",
        "`claude mcp add --transport http --scope user context7 https://mcp.context7.com/mcp`",
        "called by the path its installer names",
        "configuration work in the next stage and reopens nothing",
        "an inventory Decisions row beginning `Weekly scan:`",
        "its header written again by `records-migrate.py`",
        "`invisible-check.py` may flag a file that passed",
        "fixed in the next commit that touches it",
        "A key file that names `USERPROFILE`, `HOME`, `HOMEDRIVE`, `HOMEPATH`, `APPDATA` or `LOCALAPPDATA` is refused",
        "The round cause `base update`",
        "`--pass <name> <reviewer> --round <n>`",
        "`python ~/.claude/cursor-bridge/review-guard.py ready <pr>` runs after the CI watch",
        "a pull request already past `premerge` at the install included",
        "No merge is armed before the watch any more",
        "the right to read the branch's protection",
        "the owner's own merge on GitHub is the way through",
        "`python ~/.claude/cursor-bridge/push-scan.py` runs before every push",
        "exit 5",
        "loses the line, where it has one, and reads `merge_unit: null` before its launch",
        "written as the next numbered brief, without the line",
        "the two names are taken off the two `tools:` lines by a hotfix",
    ):
        assert words in joined, words


def test_r102_if_rolled_back_quotes_the_observed_lines():
    joined = flat(" ".join(items("**If rolled back**")))
    for words in (
        "`bridge-install.py --rollback` restores 2026.11.12a",
        "a scratch copy of this repository's records at eccc484, never the live records",
        "`note: status: 28 lines / 10676 chars (cap 120 / 12000)`",
        "`note: mode plan; requirements: 102 built, 2 deferred, 1 planned`",
        "`note: 84 increments in 1 file(s); 83 merged, 0 deferred`",
        "`TRACED: 424 passages of baseline 0a186da; 123 in supervisor.md, 191 under workflow/, 0 dropped, 110 excused`",
        "`unrecognized arguments: --moves`",
        "answered `None`",
        "`gh pr merge for <head> without the ready record of pull request 201: run python ~/.claude/cursor-bridge/review-guard.py ready 201 after the CI watch`",
        "A `Round cause: base update` line is logged `unstated`",
        "`_validate_rounds_data` accepted",
        "`model: claude-fable-5-1`",
        "`tools: Read, Grep, Glob, Write`",
        "`tools: Read, Grep, Glob, Bash`",
    ):
        assert words in joined, words
    allow = json.load(open(SETTINGS, encoding="utf-8"))["permissions"]["allow"]
    for rule in NEW_RULES:
        assert "`" + rule + "`" in joined, rule
        assert rule in allow, "the allow entry the rollback removes is the release's"


def test_r102_the_items_left_for_a_later_release_are_named():
    joined = flat(read(CHANGELOG)[read(CHANGELOG).index("\n## " + RELEASE + "\n"):read(CHANGELOG).index("\n## " + PREVIOUS + "\n")])
    for words in ("Left for a later release, by name", "the improvements release", "C25 to C61", "T44 to T108",
                  "KP-084 to KP-100", "`cursor-configurator`'s missing `tools:` line"):
        assert words in joined, words


def test_r102_every_row_is_built_with_evidence_in_the_grammar():
    cc = load(COMPLETION, "completion_check_for_program_stamp")
    header, rows = cc.parse_register(read(REGISTER))
    assert len(header) == 5, "the register's five columns"
    by_id = {r[0]: r for r in rows}
    for rid in ROWS:
        cells = by_id[rid]
        assert len(cells) == 5, rid
        requirement, status, evidence = cells[1], cells[3], cells[4]
        assert status == "built", rid
        entries = [e.strip() for e in evidence.split(";")]
        for label in labels_of(requirement):
            hits = [e for e in entries if e.startswith(label + ":") and (named_tests(e) or cc.TEXT_EVIDENCE.search(e))]
            assert hits, "%s: no `%s: <test>` or text entry" % (rid, label)
        tests = named_tests(evidence)
        assert tests or cc.TEXT_EVIDENCE.search(evidence), "%s: a test or a text entry" % rid
        for t in tests:
            path, _, node = t.partition("::")
            full = os.path.join(ROOT, *path.split("/"))
            assert os.path.isfile(full), "%s: %s" % (rid, path)
            if node:
                assert re.search(r"^def %s\b" % re.escape(node), read(full), re.M), "%s: %s" % (rid, t)
