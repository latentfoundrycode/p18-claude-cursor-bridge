"""Release B — TASK-007: the status template carries a `Workflows:` line per part, beside `Phase:`.

enforces: docs/BUILD_PLAN.md TASK-007 Done when; the Restructuring Plan §6.2 (a project's status
file records, for each part, its product type, sub-type and traits on a `Workflows:` line, and the
phase on the `Phase:` line; a project with one part has one `Workflows:` line) and §6.6 (the line
names one product type, at most one of its sub-types, and traits, all in the open list).
Satisfies R-015. The names come from the open list (TASK-004), whose Workflow name and
Sub-workflow name columns say they are the names this line uses, and whose trait Name names a
trait on it.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
SV = os.path.join(ROOT, "bridge", "commands", "supervisor.md")
OPEN_LIST = os.path.join(ROOT, "bridge", "cursor-bridge", "workflow", "open-list.md")
STATUS = os.path.join(ROOT, "docs", "PROJECT_STATUS.md")
TEXT = open(SV, encoding="utf-8").read()
OL = open(OPEN_LIST, encoding="utf-8").read()

GRAMMAR = "`Workflows: [<part>: ]<Workflow name>[ → <Sub-workflow name>]; traits: <Trait name>[, <Trait name>…]`"
LINE = re.compile(r"^Workflows: (?:(?P<part>[^:;→]+): )?(?:(?P<unclassified>not yet classified)|"
                  r"(?P<type>[^:;→]+?)(?: → (?P<sub>[^:;→]+?))?; traits: (?P<traits>[^:;→]+))$")


def flat(s):
    return re.sub(r"\s+", " ", s.replace("**", ""))


def model_section():
    a = TEXT.index("## Main and conditional workflows")
    return TEXT[a:TEXT.index("\n## ", a + 3)]


def template():
    a = TEXT.index("## Project state")
    a = TEXT.index("```markdown\n# Project Status\n", a)
    return TEXT[a:TEXT.index("\n```", a + 3)]


def paragraph():
    a = TEXT.index("**Workflows** records")
    return TEXT[a:TEXT.index("**Terms fixed**", a)]


def table(heading):
    """The first table after the heading, as dicts keyed by its header names (open-list.md, "How this file is read")."""
    lines = OL[OL.index("\n" + heading + "\n"):].split("\n")[2:]
    rows = []
    started = False
    for line in lines:
        if line.startswith("|"):
            started = True
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif started:
            break
    header, body = rows[0], rows[2:]
    return [dict(zip(header, r)) for r in body]


TYPES = table("## Product types")
SUBS = table("## Sub-types")
TRAITS = table("## Traits")


def check(line, several_parts=False):
    """The grammar's rules, applied to one line; returns the list of what it breaks."""
    m = LINE.match(line)
    if not m:
        return ["not in the grammar"]
    faults = []
    if bool(m.group("part")) != several_parts:
        faults.append("part prefix only when the project has several parts")
    if m.group("unclassified"):
        return faults
    types = [t for t in TYPES if t["Workflow name"] == m.group("type")]
    if len(types) != 1:
        return faults + ["product type is not a Workflow name of the open list"]
    if m.group("sub"):
        subs = [s for s in SUBS if s["Sub-workflow name"] == m.group("sub")]
        if len(subs) != 1:
            faults.append("sub-type is not a Sub-workflow name of the open list")
        elif subs[0]["Of type"] != types[0]["Key"]:
            faults.append("sub-type is not of the line's product type")
    traits = m.group("traits")
    if traits != "none":
        names = traits.split(", ")
        order = [t["Name"] for t in TRAITS]
        if any(n not in order for n in names):
            faults.append("a trait is not a trait Name of the open list")
        elif len(set(names)) != len(names):
            faults.append("a trait is repeated")
        elif [order.index(n) for n in names] != sorted(order.index(n) for n in names):
            faults.append("traits not in the open list's order")
    return faults


def test_r015_the_template_carries_the_workflows_line_right_after_phase():
    """R-015 (plan §6.2): the line sits beside `Phase:` in the status template."""
    lines = template().split("\n")
    i = next(n for n, l in enumerate(lines) if l.startswith("Phase: "))
    assert lines[i + 1].startswith("Workflows: "), lines[i + 1]
    assert sum(1 for l in lines if l.startswith("Workflows:")) == 1, "the template shows the line once"
    assert "one line per part" in lines[i + 1]
    assert "not yet classified" in lines[i + 1]


def test_r015_the_grammar_is_defined_once_after_the_template():
    """R-015: the grammar is stated in the Project state section, after the template, before Terms fixed."""
    p = paragraph()
    assert TEXT.count("**Workflows** records") == 1
    assert TEXT.index("## Project state") < TEXT.index("**Workflows** records") < TEXT.index("**Terms fixed** is")
    assert TEXT.index("<!-- digest:end -->") < TEXT.index("**Workflows** records"), "core text, not the digest"
    assert GRAMMAR in p
    assert "one `Workflows:` line per part, directly after `Phase:`" in p  # where check_placement requires it
    assert "with the `Phase:` line they name exactly what a resumed session must read" in flat(p)


def test_r015_names_are_the_open_lists_workflow_names_and_trait_names():
    """R-015 / plan §6.6: every name on the line is in the open list, spelled as it spells them."""
    p = flat(paragraph())
    assert ("the product type is named by its Workflow name, the sub-type by its Sub-workflow name and each "
            "trait by its Name, spelled exactly as `~/.claude/cursor-bridge/workflow/open-list.md` spells them; "
            "every name on the line is in the open list") in p
    # the open list says the same from its side (TASK-004)
    assert "used in the status file's `Workflows:` line" in OL
    assert "is named by it on a `Workflows:` line" in OL


def test_r015_one_type_at_most_one_of_its_sub_types_traits_in_order_or_none():
    """R-015 / plan §6.6: exactly one product type, at most one of its sub-types; the traits' form."""
    p = flat(paragraph())
    assert "exactly one product type and at most one of its sub-types" in p
    assert "is left out when the part has no sub-type" in p
    assert "separated by a comma and a space, in the order the open list gives them" in p
    assert "a part with no trait reads `; traits: none`" in p


def test_r015_a_part_prefix_only_with_several_parts_and_the_unclassified_form():
    """Plan §6.2: a project with one part has one line; §7's parts each get their own."""
    p = flat(paragraph())
    assert ("follows `Workflows: ` only when the project has more than one part; a project with one part has one "
            "line without it; a part's name is not empty, has no space at either end and contains no `:`, `;` or `→`") in p
    assert ("with several parts, the lines stand together right after `Phase:`, one per part, in the order of the "
            "project's parts; that is the order \"for each part in the order the status file lists them\" reads") in p
    assert "for each part in the order the status file lists them" in flat(model_section()), "the core reads that order"
    assert "`Workflows: not yet classified` in a project with one part" in p
    assert ("written at intake, when the part is classified, with the traits proposed there; the design gate settles "
            "them, and the line is rewritten then if they changed") in p


def test_r015_unwritten_type_pauses_unwritten_trait_is_flagged():
    """Plan §6.7, as the open list states it: the line is where an unwritten workflow shows."""
    p = flat(paragraph())
    assert ("At intake, a part whose product type or sub-type is not yet written pauses the project; a trait not yet "
            "written is flagged and the work continues") in p
    assert "## When something does not fit" in OL


def test_r015_the_example_line_is_valid_against_the_open_list():
    """The paragraph's example — the bridge itself — obeys the grammar it illustrates."""
    ex = "Workflows: Host Extension Development → Claude Code Extension; traits: Installable"
    assert "`%s`" % ex in paragraph()
    assert check(ex) == []


def test_r015_this_projects_own_status_line_obeys_the_grammar():
    """The bridge's own status file (a supervised project since release B) carries a valid line."""
    all_lines = open(STATUS, encoding="utf-8").read().split("\n")
    lines = [l for l in all_lines if l.startswith("Workflows:")]
    assert len(lines) == 1, "one part, one line"
    assert check(lines[0]) == [], (lines[0], check(lines[0]))
    i = next(n for n, l in enumerate(all_lines) if l.startswith("Phase: "))
    assert all_lines[i + 1] == lines[0], "the line sits right after Phase:"


def test_the_checker_here_refuses_what_the_grammar_forbids():
    """The rules above, read as a checker, refuse each kind of malformed line (so the two tests before are not vacuous)."""
    good = "Workflows: Host Extension Development → Claude Code Extension; traits: Installable"
    assert check(good) == []
    hx = "Workflows: Host Extension Development"
    assert check("Workflows: host extension → Claude Code Extension; traits: Installable") == [
        "product type is not a Workflow name of the open list"]  # the type's plain Name
    assert check(hx + " → Claude Code extension; traits: Installable") == [
        "sub-type is not a Sub-workflow name of the open list"]  # the sub-type's plain Name
    assert check(hx + " → Roblox Game; traits: Installable") == ["sub-type is not of the line's product type"]
    assert check(hx + "; traits: installable") == ["a trait is not a trait Name of the open list"]  # a key
    # alphabetical, but not the Traits table's order (Performance budgets comes before External services there)
    assert check(hx + "; traits: External services, Performance budgets") == ["traits not in the open list's order"]
    assert check(hx + "; traits: Performance budgets, External services") == []
    assert check(hx + "; traits: Installable, Installable") == ["a trait is repeated"]
    assert check(hx + " → Claude Code Extension") == ["not in the grammar"]  # no traits part
    assert check("Bridge: " + good[len("Workflows: "):]) == ["not in the grammar"]  # no `Workflows: ` at all
    assert check("Bridge: " + good, several_parts=True) == ["not in the grammar"]  # the prefix before `Workflows: `
    one_part = ["part prefix only when the project has several parts"]
    assert check("Workflows: Bridge: Host Extension Development; traits: none") == one_part
    assert check("Workflows: Bridge: Host Extension Development; traits: none", several_parts=True) == []
    assert check("Workflows: Host Extension Development; traits: none", several_parts=True) == one_part
    assert check(hx + "; traits: none") == []
    assert check("Workflows: not yet classified") == []
    assert check("Workflows: Bridge: not yet classified", several_parts=True) == []
    assert check("Workflows: Bridge: not yet classified") == one_part
