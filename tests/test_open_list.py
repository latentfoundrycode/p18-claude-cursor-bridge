"""Release B — TASK-004: the open list of product types, sub-types and traits.

enforces: docs/BUILD_PLAN.md TASK-004 Done when; the Restructuring Plan §6.3 (every product type,
sub-type and trait with its definition, default traits and fixed workflow name), §6.5 (a sub-type
must earn its place; siblings exclusive; two levels), §6.7 (what does not fit), §6.8 (what release B
writes), §6.10 (the add/change procedure) and §6.11 (the file's path). Satisfies R-011.
The three tables are the shape `workflow-check.py` (TASK-006) reads: each found by its heading, the
first Markdown table under it, one row per entry, cells split on `|`.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OL = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "workflow", "open-list.md")
TEXT = open(OL, encoding="utf-8").read()
SV = os.path.join(HERE, os.pardir, "bridge", "commands", "supervisor.md")

KEY = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

TYPE_COLS = ["Key", "Name", "Definition", "Workflow name", "Default traits", "Written", "Planned"]
SUB_COLS = ["Key", "Name", "Of type", "Definition", "Sub-workflow name", "Default traits", "Written", "Planned"]
TRAIT_COLS = ["Key", "Name", "Definition", "Written", "Planned"]

# §6.3, as the plan states it (types with their workflow names where the owner fixed them).
TYPES = ["mobile-app", "web-app", "website", "software-on-your-own-computer", "backend-service",
         "library", "video-game", "host-extension"]
SUBTYPES = {"android": "mobile-app", "ios": "mobile-app", "local-web-app": "web-app",
            "gui": "software-on-your-own-computer", "cli": "software-on-your-own-computer",
            "pipeline": "software-on-your-own-computer", "local-service": "software-on-your-own-computer",
            "roblox": "video-game", "claude-code-extension": "host-extension",
            "browser-extension": "host-extension"}
# §6.3's trait order, which supervisor.md's "The order additions apply in" also states (R-034).
TRAITS = ["has-screens", "installable", "performance-budgets", "external-services", "spends-money",
          "long-running-process", "ai-models", "personal-data", "multiplayer"]
DEFAULTS = {
    "mobile-app": {"has-screens", "installable"},
    "web-app": {"has-screens", "personal-data"},
    "website": {"has-screens"},
    "software-on-your-own-computer": {"installable"},
    "backend-service": {"long-running-process"},
    "library": set(),
    "video-game": {"has-screens", "performance-budgets"},
    "host-extension": {"installable"},
    "local-web-app": {"has-screens", "installable", "long-running-process"},
    "gui": {"installable", "has-screens"},
    "local-service": {"installable", "long-running-process"},
    "roblox": {"has-screens", "performance-budgets", "multiplayer"},
}


def table(heading):
    """The first Markdown table under `heading`: (header cells, rows as dicts)."""
    a = TEXT.index("\n" + heading + "\n")
    b = TEXT.find("\n## ", a + 1)
    section = TEXT[a:b if b != -1 else len(TEXT)]
    lines = [l for l in section.split("\n") if l.startswith("|")]
    cells = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    head, sep, body = cells[0], cells[1], cells[2:]
    assert all(set(c) <= set("-:") and c for c in sep), "the second table line is the separator"
    rows = []
    for r in body:
        assert len(r) == len(head), "every row has one cell per column: %r" % (r,)
        rows.append(dict(zip(head, r)))
    return head, rows


def traits_of(cell):
    return set() if cell == "—" else {t.strip() for t in cell.split(",")}


def test_r011_the_file_sits_at_the_s6_11_path_and_is_bounded():
    """R-011, §6.11: `workflow/open-list.md` beside the bridge's programs; a bounded reference text."""
    assert os.path.isfile(OL)
    assert TEXT.count("\n") < 300 and len(TEXT) < 30000
    assert "\r" not in TEXT


def test_r011_the_three_tables_parse_in_the_shape_workflow_check_reads():
    """R-011: each table found by its heading, with exactly these columns, in this order."""
    assert table("## Product types")[0] == TYPE_COLS
    assert table("## Sub-types")[0] == SUB_COLS
    assert table("## Traits")[0] == TRAIT_COLS
    for h in ("## Product types", "## Sub-types", "## Traits"):
        assert TEXT.count("\n" + h + "\n") == 1, "one heading per table: " + h


def test_r011_every_entry_has_a_key_name_definition_and_written_flag():
    """R-011: definition, name and flag on every entry; keys well formed and unique per table."""
    for heading in ("## Product types", "## Sub-types", "## Traits"):
        _, rows = table(heading)
        keys = [r["Key"] for r in rows]
        assert len(keys) == len(set(keys)), heading + ": keys are unique"
        for r in rows:
            assert KEY.match(r["Key"]), r["Key"]
            assert r["Name"] and r["Definition"] and r["Planned"], r["Key"]
            assert r["Written"] in ("yes", "no"), r["Key"]


def test_r011_every_s6_3_product_type_is_listed_with_its_workflow_name_and_defaults():
    """R-011, §6.3: the eight product types, each with its fixed workflow name and default traits."""
    _, rows = table("## Product types")
    by = {r["Key"]: r for r in rows}
    assert [r["Key"] for r in rows] == TYPES
    for k in TYPES:
        assert by[k]["Workflow name"], k
        assert traits_of(by[k]["Default traits"]) == DEFAULTS[k], k
    assert by["video-game"]["Workflow name"] == "Game Development", "the owner's name (2026-10-01)"
    names = [r["Workflow name"] for r in rows]
    assert len(names) == len(set(names))


def test_r011_every_s6_3_sub_type_is_listed_under_its_type_with_its_name_and_defaults():
    """R-011, §6.3: the ten sub-types, each of an existing type, with a sub-workflow name and defaults."""
    _, rows = table("## Sub-types")
    by = {r["Key"]: r for r in rows}
    assert set(by) == set(SUBTYPES)
    for k, of in SUBTYPES.items():
        assert by[k]["Of type"] == of, k
        assert by[k]["Sub-workflow name"], k
        assert by[k]["Default traits"], k
        if k in DEFAULTS:
            assert traits_of(by[k]["Default traits"]) == DEFAULTS[k], k
        else:
            # a sub-type §6.3 adds nothing to keeps its type's defaults (or more), never fewer
            assert traits_of(by[k]["Default traits"]) >= DEFAULTS[of], k
    assert by["roblox"]["Sub-workflow name"] == "Roblox Game", "the owner's name (2026-10-01)"
    names = [r["Sub-workflow name"] for r in rows]
    assert len(names) == len(set(names))


def test_r011_every_default_trait_names_a_listed_trait():
    """R-011: default traits are trait keys of the Traits table, never free text."""
    known = {r["Key"] for r in table("## Traits")[1]}
    for heading in ("## Product types", "## Sub-types"):
        for r in table(heading)[1]:
            assert traits_of(r["Default traits"]) <= known, r["Key"]


def test_r011_r034_the_traits_are_listed_in_the_s6_3_order_the_core_states():
    """R-011, R-034: the open list's trait order is §6.3's and the one supervisor.md states."""
    rows = table("## Traits")[1]
    assert [r["Key"] for r in rows] == TRAITS
    core = re.sub(r"\s+", " ", open(SV, encoding="utf-8").read())
    stated = "has screens, installable, performance budgets, external services, spends money, " \
             "long-running process, AI models, personal data, multiplayer"
    assert stated in core
    assert [r["Name"].lower() for r in rows] == [n.lower() for n in stated.split(", ")]
    assert "a trait added later goes at the end of the table" in TEXT


def test_r011_all_entries_start_unwritten():
    """R-011: no conditional workflow is written yet; later increments flip each flag with its file."""
    for heading in ("## Product types", "## Sub-types", "## Traits"):
        for r in table(heading)[1]:
            assert r["Written"] == "no", r["Key"]


def test_r011_release_b_entries_are_planned_for_release_b():
    """§6.8: release B writes these; the rest wait for their release or their first project."""
    planned = {r["Key"]: r["Planned"] for h in ("## Product types", "## Sub-types", "## Traits")
               for r in table(h)[1]}
    for k in ("web-app", "local-web-app", "software-on-your-own-computer", "local-service",
              "host-extension", "claude-code-extension", "has-screens", "installable",
              "performance-budgets", "external-services", "spends-money", "long-running-process",
              "ai-models"):
        assert planned[k] == "release B", k
    for k in ("video-game", "roblox", "multiplayer"):
        assert "release E" in planned[k], k
    assert "Mac" in planned["ios"]


def test_r011_the_open_list_is_the_canonical_source_of_default_traits():
    """R-011: a type file's default traits are checked against this file by workflow-check."""
    flat = re.sub(r"\s+", " ", TEXT)
    assert "the one source of a product type's default traits" in flat
    assert "checked against this file by `workflow-check.py`" in flat


def test_r011_the_classification_rules_are_recorded():
    """§6.3, §6.5, §6.7: the intake tests, earning a place, siblings, two levels, what does not fit."""
    flat = re.sub(r"\s+", " ", TEXT.replace("**", ""))
    assert "does it keep data for its users" in flat
    assert "does its user meet it in a browser?" in flat
    assert "A sub-type must earn its place. It must change a phase, a gate, a check or the tooling." in flat
    assert "Siblings are exclusive: a part has at most one sub-type of its product type." in flat
    assert "Two levels are enough" in flat
    assert "A new product type or sub-type pauses the project." in flat
    assert "A new trait is flagged, and the work continues." in flat


def test_r011_the_s6_10_procedure_is_recorded():
    """R-011, §6.10: the four steps of adding one, changing one, and who may write one."""
    a = TEXT.index("## Adding or changing a conditional workflow")
    section = TEXT[a:TEXT.index("\n## ", a + 1)]
    steps = re.findall(r"^\d\. ", section, re.M)
    assert len(steps) == 4
    flat = re.sub(r"\s+", " ", section)
    assert "in the maintainer's session" in flat
    assert "The workflow check passes." in flat
    assert "calibration applies it to running projects" in flat and "reopening no gate" in flat
    assert "Changing an existing one is the same" in flat
    assert "A project's supervisor never writes a conditional workflow" in flat
    assert "promotion pass" in flat
