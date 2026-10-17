"""Release B — TASK-004: the open list of product types, sub-types and traits.

enforces: docs/BUILD_PLAN.md TASK-004 Done when; the Restructuring Plan §6.3 (every product type,
sub-type and trait with its definition, default traits and fixed workflow name), §6.5 (a sub-type
must earn its place; siblings exclusive; two levels), §6.7 (what does not fit), §6.8 (what release B
writes), §6.10 (the add/change procedure) and §6.11 (the file's path). Satisfies R-011.
The three tables are the shape `workflow-check.py` (TASK-006) reads: each found by its heading, the
first Markdown table after it (its rows running to the first line that is not a table line), one row
per entry, cells split on `|`, columns found by their header names.
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

# §6.3, as the plan states it (the product types; every workflow and sub-workflow name is pinned below).
TYPES = ["mobile-app", "web-app", "website", "own-computer", "backend-service",
         "library", "video-game", "host-extension"]
SUBTYPES = {"android": "mobile-app", "ios": "mobile-app", "local-web-app": "web-app",
            "gui": "own-computer", "cli": "own-computer",
            "pipeline": "own-computer", "local-service": "own-computer",
            "roblox": "video-game", "claude-code-extension": "host-extension",
            "browser-extension": "host-extension"}
# §6.3's trait order, which supervisor.md's "The order additions apply in" also states (R-034).
TRAITS = ["has-screens", "installable", "performance-budgets", "external-services", "spends-money",
          "long-running-process", "ai-models", "personal-data", "multiplayer"]
DEFAULTS = {
    "mobile-app": {"has-screens", "installable"},
    "web-app": {"has-screens", "personal-data"},
    "website": {"has-screens"},
    "own-computer": {"installable"},
    "backend-service": {"long-running-process"},
    "library": set(),
    "video-game": {"has-screens", "performance-budgets"},
    "host-extension": {"installable"},
    # a sub-type's cell is its complete default set (§6.3); where §6.3 adds nothing it is its type's
    "android": {"has-screens", "installable"},
    "ios": {"has-screens", "installable"},
    "local-web-app": {"has-screens", "installable", "long-running-process"},
    "gui": {"has-screens", "installable"},
    "cli": {"installable"},
    "pipeline": {"installable"},
    "local-service": {"installable", "long-running-process"},
    "roblox": {"has-screens", "performance-budgets", "multiplayer"},
    "claude-code-extension": {"installable"},
    "browser-extension": {"installable"},
}
# §6.3, §6.8, §6.9: when each entry's workflow is to be written.
FIRST = "when the first project of this type arrives"
PLANNED = {
    "mobile-app": FIRST, "web-app": "release B", "website": FIRST, "own-computer": "release B",
    "backend-service": FIRST, "library": FIRST, "video-game": "release E", "host-extension": "release B",
    "android": FIRST, "ios": "when the owner builds on a Mac", "local-web-app": "release B", "gui": FIRST,
    "cli": FIRST, "pipeline": FIRST, "local-service": "release B", "roblox": "release E",
    "claude-code-extension": "release B", "browser-extension": FIRST,
    "has-screens": "release B", "installable": "release B", "performance-budgets": "release B",
    "external-services": "release B", "spends-money": "release B", "long-running-process": "release B",
    "ai-models": "release B", "personal-data": "when a project first needs it",
    "multiplayer": "release E, with the Roblox sub-workflow",
}
# §6.3: the workflow and sub-workflow names are "fixed here"; the owner chose the game's (2026-10-01)
# and the others take the same shape. Renaming one is a change to this file and to these pins together.
WORKFLOW_NAMES = {
    "mobile-app": "Mobile App Development", "web-app": "Web App Development",
    "website": "Website Development", "own-computer": "Own-Computer Software Development",
    "backend-service": "Backend Service Development", "library": "Library Development",
    "video-game": "Game Development", "host-extension": "Host Extension Development",
}
SUB_WORKFLOW_NAMES = {
    "android": "Android App", "ios": "iOS App", "local-web-app": "Local Web App",
    "gui": "GUI Software", "cli": "CLI Software", "pipeline": "Pipeline Software",
    "local-service": "Local Service Software", "roblox": "Roblox Game",
    "claude-code-extension": "Claude Code Extension", "browser-extension": "Browser Extension",
}
WF = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "workflow")


def table(heading, text=TEXT):
    """The first Markdown table after `heading` in `text` (the open list unless another file's text is
    given), to the first non-table line: (header cells, rows)."""
    a = text.index("\n" + heading + "\n")
    b = text.find("\n## ", a + 1)
    section = text[a:b if b != -1 else len(text)].split("\n")
    start = next(i for i, l in enumerate(section) if l.startswith("|"))
    lines = []
    for l in section[start:]:
        if not l.startswith("|"):
            break
        lines.append(l)
    cells = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    head, sep, body = cells[0], cells[1], cells[2:]
    assert all(set(c) <= set("-:") and c for c in sep), "the second table line is the separator"
    assert len(sep) == len(head), "the separator has one cell per column"
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
    raw = open(OL, encoding="utf-8", newline="").read()
    assert "\r" not in raw.replace("\r\n", "\n"), "no lone carriage return (a CRLF checkout is fine; stage B2 review, round 3)"


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


def test_r011_the_names_a_workflows_line_reads_are_unique_across_the_tables():
    """R-011, R-015: a `Workflows:` line names its entries by Workflow name, Sub-workflow name and trait Name, and
    workflow-check.py looks each up across the three tables, so no name stands in two places (stage B2 review, round 2)."""
    names = ([r["Workflow name"] for r in table("## Product types")[1]]
             + [r["Sub-workflow name"] for r in table("## Sub-types")[1]]
             + [r["Name"] for r in table("## Traits")[1]])
    assert len(names) == len(set(names)), sorted(n for n in names if names.count(n) > 1)
    assert "the Workflow names, the Sub-workflow names and the traits' Names are unique across the three tables" in TEXT
    # workflow-check.py splits a line at these characters (prefix_of, check_head, check_traits): stage B2 review, round 3.
    assert [n for n in names if any(c in n for c in (",", ";", ":", chr(0x2192)))] == [], "a name holds a separator"
    assert "none of them contains `,`, `;`, `:` or `" + chr(0x2192) + "`" in TEXT


def test_r011_every_s6_3_product_type_is_listed_with_its_workflow_name_and_defaults():
    """R-011, §6.3: the eight product types, each with its fixed workflow name and default traits."""
    _, rows = table("## Product types")
    by = {r["Key"]: r for r in rows}
    assert [r["Key"] for r in rows] == TYPES
    for k in TYPES:
        assert by[k]["Workflow name"] == WORKFLOW_NAMES[k], k
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
        assert by[k]["Sub-workflow name"] == SUB_WORKFLOW_NAMES[k], k
        assert traits_of(by[k]["Default traits"]) == DEFAULTS[k], k
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


def test_r011_an_entry_is_written_exactly_when_its_file_exists_at_its_key_path():
    """R-011, §6.11: Written is `yes` iff the entry's workflow file exists at its key's path; the
    increment that writes the file sets the flag in the same change."""
    for heading in ("## Product types", "## Sub-types", "## Traits"):
        for r in table(heading)[1]:
            if heading == "## Product types":
                path = os.path.join(WF, "types", r["Key"] + ".md")
            elif heading == "## Sub-types":
                path = os.path.join(WF, "types", r["Of type"], r["Key"] + ".md")
            else:
                path = os.path.join(WF, "traits", r["Key"] + ".md")
            assert (r["Written"] == "yes") == os.path.isfile(path), r["Key"]


def test_r011_every_entry_is_planned_as_s6_3_s6_8_and_s6_9_say():
    """§6.8: release B writes these; the rest wait for their release or their first project."""
    planned = {r["Key"]: r["Planned"] for h in ("## Product types", "## Sub-types", "## Traits")
               for r in table(h)[1]}
    assert planned == PLANNED


def test_r011_the_tables_shape_is_stated_for_the_reader():
    """R-011: the shape `workflow-check.py` relies on is stated, not only implied by the tables."""
    flat = re.sub(r"\s+", " ", TEXT)
    assert "Each table is the first table after its heading" in flat
    assert "its rows running to the first line that is not a table line" in flat
    assert "its columns are found by their header names; no cell contains a `|`" in flat
    assert "The order inside a cell carries no meaning; the order traits apply in is the Traits table's." in flat


def test_r011_the_open_list_is_the_canonical_source_of_default_traits():
    """R-011: the open list is the source of the default traits; the workflow check does not yet check a
    statement of them, since no form for one exists (stage B2 review: the text had claimed a check never built)."""
    flat = re.sub(r"\s+", " ", TEXT)
    assert "the one source of the default traits of a product type and of a sub-type" in flat
    assert "No form for that statement exists yet, so `workflow-check.py` does not check it" in flat
    assert "the form and its check come together, in the change that writes the first such statement" in flat
    assert "is checked against this file by `workflow-check.py`" not in flat


def test_r011_the_classification_rules_are_recorded():
    """§6.3, §6.5, §6.7: the intake tests, earning a place, siblings, two levels, what does not fit."""
    flat = re.sub(r"\s+", " ", TEXT.replace("**", ""))
    assert "does it keep data for its users" in flat
    assert "does its user meet it in a browser?" in flat
    assert "A sub-type must earn its place. It must change a phase, a gate, a check or the tooling." in flat
    assert "Siblings are exclusive: a part has at most one sub-type of its product type." in flat
    assert "Two levels are enough" in flat
    assert "A new product type or sub-type pauses the project." in flat
    assert ("fits no product type, fits two equally, fits one whose workflow is not yet written, or fits a sub-type whose "
            "sub-workflow is not yet written, the supervisor stops before design") in flat
    assert "the supervisor stops before design" in flat
    assert "A new trait is flagged, and the work continues." in flat
    assert "from which the maintainer may write it as trait additions" in flat
    assert "The same holds for a trait that is defined but not yet written." in flat


def test_r011_the_s6_10_procedure_is_recorded():
    """R-011, §6.10: the four steps of adding one, changing one, and who may write one."""
    a = TEXT.index("## Adding or changing a conditional workflow")
    section = TEXT[a:TEXT.index("\n## ", a + 1)]
    steps = re.findall(r"^\d\. ", section, re.M)
    assert len(steps) == 4
    flat = re.sub(r"\s+", " ", section)
    assert "in the maintainer's session" in flat
    assert "The workflow check passes, and the entry's Written flag is set to `yes` in the same change." in flat
    assert "Its entry joins this list with every column of its table filled, including," in flat
    assert "calibration applies it to running projects" in flat and "reopening no gate" in flat
    assert "Changing an existing one is the same" in flat
    assert "A project's supervisor never writes a conditional workflow and never changes this file" in flat
    assert "promotion pass" in flat
