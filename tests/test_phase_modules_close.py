"""TASK-014: the change-cycle, reflection and project-end modules enriched (R-004, R-006, R-032, R-036).

enforces: docs/REQUIREMENTS.md R-004 (each phase module opens with the short list of what must survive a compaction),
R-006 (each phase module declares the points the registry names it as declaring; the tree-wide cross-check of the
registry against every module, BUILD_PLAN TASK-014's Done when, and the registry's "How a phase module declares its
points"), R-032 (each module read whole), R-036 (a new or unwritten trait is put to the promotion pass at project end);
docs/BUILD_PLAN.md TASK-014's Done when (the issues rule's line on whether a compaction preceded an incident, the
compaction baseline's follow-up); docs/HARDENING.md, Stage B3's leads for TASK-014 (the change cycle runs the variant of
every interface kind a change touches; the variant files' declaring paragraphs under headings of their own; the promotion
pass reads the inventory's `Flagged trait:` rows; the pointer sweep, the glossary's phase-module entry)."""
import hashlib
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CB = os.path.join(BRIDGE, "cursor-bridge")
PHASES = os.path.join(CB, "workflow", "phases")
REGISTRY = os.path.join(CB, "workflow", "extension-points.md")
EXCEPTIONS = os.path.join(CB, "workflow", "trace-exceptions.md")
GLOSSARY = os.path.join(CB, "Glossary.md")


def read(path):
    return open(path, encoding="utf-8").read().replace("\r\n", "\n")


def module(rel):
    return read(os.path.join(PHASES, rel if rel.endswith(".md") else rel + ".md"))


def flat(text):
    return re.sub(r"\s+", " ", text)


def headings(text):
    """(level, title) of every heading outside fenced blocks, in order."""
    out, fence = [], None
    for line in text.split("\n"):
        m = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if m:
            if fence is None:
                fence = m.group(1)[0]
            elif m.group(1)[0] == fence:
                fence = None
            continue
        if fence is None:
            h = re.match(r"^(#{1,6}) (.*)$", line)
            if h:
                out.append((len(h.group(1)), h.group(2).strip()))
    return out


def section(text, title, level):
    """The body of the heading `title` at `level`, to the next heading of that level or higher."""
    lines = text.split("\n")
    start = lines.index("#" * level + " " + title) + 1
    end = len(lines)
    for i in range(start, len(lines)):
        h = re.match(r"^(#{1,6}) ", lines[i])
        if h and len(h.group(1)) <= level:
            end = i
            break
    return "\n".join(lines[start:end])


STRUCTURE = {
    "change-cycle": [(2, "The change cycle — a request on a finished project"), (3, "What must survive a compaction"),
                     (3, "The procedure")],
    "reflection": [(2, "Reflection points — stage close, phase gates, project end"), (3, "What must survive a compaction"),
                   (3, "The procedure"), (3, "Keeping the position"), (3, "Project end"),
                   (3, "Issues — what counts, and where it is written"), (4, "Whether a compaction preceded it"),
                   (2, "Extension points")],
    "project-end": [(2, "Project end"), (3, "What must survive a compaction"), (3, "Where this module begins"),
                    (3, "The trigger and what project end adds"), (3, "Flagged traits in the promotion pass"),
                    (3, "Keeping the position"), (2, "Extension points")],
}

INTRO = {
    "change-cycle": "After a compaction or a resume in a change cycle, read these before your next action:",
    "reflection": "After a compaction or a resume at a reflection point, read these before your next action:",
    "project-end": "After a compaction or a resume at project end, read these before your next action:",
}

SURVIVAL = {
    "change-cycle": [
        "this module, whole, and the module of the step the change has reached, whole: its intake runs `intake.md`'s "
        "procedure, its design revision `design.md`'s, its interface variants `interface.md`'s with the variant files its "
        "`Variants:` line names, and its plan addendum `planning.md`'s, each scaled to the change; its new stages run "
        "`delegation-loop.md` with its sub-file, and their closes `reflection.md` and `project-end.md`, which the "
        "session-start hook names with this module while the phase is `changing`;",
        "`docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, whole (rule 41): the `Change cycle:` line names the change, its "
        "date and the step it has reached, and `Awaiting user on:` a gate that waits for the owner; the inventory's "
        "Features answer a request already satisfied, and its Decisions name one the change reverses (item 1);",
        "`docs/REQUIREMENTS.md`, with the failures `completion-check.py --mode done` printed at item 1: each is a gap in "
        "the previous delivery, reported to the owner first and planned ahead of the request unless the owner defers it;",
        "the change's records as far as they are written, whole: its `Change: <name>` section of `docs/DESIGN.md`, its "
        "record in `docs/DESIGN_CRITIQUE.md` under the change's subject and under `<the change's name>-plan`, the "
        "interface artifacts it amends, and its stages in `docs/BUILD_PLAN.md`;",
        "while its intake runs, this project's own Issues file, `Documents/<Name> Issues During Development and Their "
        "Solutions.md`, whole: it takes the place of the prior-project lessons step.",
    ],
    "reflection": [
        "this module, whole, and at the close of the plan's last stage `project-end.md` too, whole (the session-start hook "
        "names both while the phase is `building` or `changing`);",
        "the last entries of `run/supervisor/in-flight.md`: the reflection point in hand and the items it has finished "
        "(\"Keeping the position\"), and, while the stage review's Review B runs, the position the delegation loop's step 8 "
        "keeps there;",
        "`docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, whole (rule 41): the `Stage:` line's `Last reflection:` names "
        "the reflection point before this one, from which items 1, 2 and 4 count, and `Open issues:` the issues item 1 "
        "completes; the inventory holds the decisions and resources the Project Summary's patch reports;",
        "`docs/RUN_PARAMETERS.md`: whether the refactoring pass runs before a stage closes, and `Stage pause`, which item 6 "
        "obeys;",
        "at a stage close, the stage's section of `docs/BUILD_PLAN.md`, whole, with its `Demonstration:` line, and, while "
        "the stage review runs, its files under `run/review/` (`STAGE-<name>.diff` with its parts, and "
        "`REVIEW-STAGE-<name>.err`);",
        "the records the items read and write, whole: `docs/BUILDER_NOTES.md`, the entries of `docs/CHANGES.md` since the "
        "last reflection point, the stage's section of `docs/HARDENING.md`, and under `Documents/` the Issues document, "
        "the Feedback document, the Project Summary and, once it exists, the User Manual.",
    ],
    "project-end": [
        "this module and `reflection.md`, each whole: project end runs after the reflection points' items 1 to 5 at the "
        "last stage's close, in the same turn;",
        "the last entries of `run/supervisor/in-flight.md`: the project-end items finished so far (\"Keeping the "
        "position\");",
        "`docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, whole (rule 41): the `Workflows:` lines name each part's "
        "conditional workflows, whose additions at `project-end.completion-conditions` and `project-end.delivery` this "
        "module runs; the inventory's `Delivery kind:` rows give each part's delivery kind, its `Flagged trait:` rows the "
        "traits the promotion pass puts forward, and its Deferred rows the items the \"Project complete\" line lists;",
        "`docs/REQUIREMENTS.md`, `docs/CHANGES.md` and `docs/RUN_PARAMETERS.md`: the completion check reads the register, "
        "the User Manual is written from the change log, and the installer's last verification follows the `Installer "
        "verification` parameter;",
        "the Issues and Feedback documents under `Documents/`, whole: the promotion pass reads both and writes its "
        "proposals as the Feedback document's last section.",
    ],
}

KEYS = ["change-cycle", "reflection", "project-end"]


@pytest.mark.parametrize("key", KEYS)
def test_r004_the_module_opens_with_its_compaction_survival_list(key):
    """R-004: the module's first section, straight after its heading, is the compaction-survival list, and the list is
    exactly what a resumed session at that point reads before its next action."""
    text = module(key)
    assert headings(text) == STRUCTURE[key], headings(text)
    lines = text.split("\n")
    assert lines[1] == "" and lines[2] == "### What must survive a compaction", lines[:3]
    body = section(text, "What must survive a compaction", 3).strip().split("\n")
    assert body[0] == INTRO[key]
    assert all(l.startswith("- ") for l in body[1:] if l), body
    assert [l[2:] for l in body[1:] if l] == SURVIVAL[key]


def registry_rows(heading):
    text = read(REGISTRY)
    table = text.split("\n" + heading + "\n", 1)[1].split("\n## ", 1)[0]
    rows = [l for l in table.split("\n") if l.startswith("|")]
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    return [dict(zip(header, [c.strip() for c in row.strip("|").split("|")])) for row in rows[2:]]


def registry_points(module_key):
    return [r["Key"] for r in registry_rows("## Extension points") if r["Declared by"] == module_key]


EXT_PROSE = ("This module offers the points below, each by its key in the extension-point registry "
             "(`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and "
             "whether it applies per part or per project. A conditional workflow's additions at a point are made where the "
             "point's line places them, in the order the core states in \"Main and conditional workflows\".")


def declared(text):
    """The keys a module declares: the point lines of its `## Extension points` section, or [] where it has none."""
    if (2, "Extension points") not in headings(text):
        return []
    body = section(text, "Extension points", 2).strip().split("\n")
    return [re.match(r"^- `([a-z0-9.-]+)` — \S", l).group(1) for l in body if l.startswith("- ")]


@pytest.mark.parametrize("key", ["reflection", "project-end"])
def test_r006_the_module_declares_exactly_its_registry_points_in_the_registrys_order(key):
    """R-006 and the registry's "How a phase module declares its points": a `## Extension points` section, one line
    per point giving its key, exactly the points the registry names this module as declaring, in the table's order;
    the reflection points declare `reflection.items` and project end Definition of done and Delivery (§6.4's rows)."""
    text = module(key)
    want = registry_points(key)
    assert want and declared(text) == want, (declared(text), want)
    body = section(text, "Extension points", 2).strip().split("\n")
    assert flat(" ".join(l for l in body if l and not l.startswith("- "))) == EXT_PROSE
    assert "may set" not in "\n".join(body)
    if key == "project-end":
        assert want == ["project-end.completion-conditions", "project-end.delivery"], want


def test_r006_the_change_cycle_declares_no_point_and_says_so():
    """R-006: the registry names no point the change cycle declares, so the module has no `## Extension points`
    section (the registry: "Each phase module that declares points does so in a section headed ..."), and it says how a
    conditional workflow reaches a change cycle instead."""
    text = module("change-cycle")
    assert registry_points("change-cycle") == [] and declared(text) == []
    assert ("This module declares no extension points: a conditional workflow changes a change cycle through the modules "
            "whose procedures it runs, each at its own points.") in text.split("\n")


POINTS = {
    "reflection.items": "reflection items a conditional workflow adds to the numbered items above, each run at every "
                        "reflection point after item 4 and before item 5, so that the reflection point is recorded only "
                        "once they are done, and each finished step kept as \"Keeping the position\" says; made once for "
                        "the whole project.",
    "project-end.completion-conditions": "completion conditions a conditional workflow adds for the part, each checked "
                                         "with \"Prove the product is complete\" above, before anything else at project "
                                         "end: a condition not met means, as a failure of `completion-check.py` does, "
                                         "that the project has not ended; a condition the plan must build toward is also "
                                         "added at intake (`intake.requirement-sources`), as the registry says.",
    "project-end.delivery": "the delivery procedure for the part's delivery kind, which an addition names (`## Add at "
                            "project-end.delivery for <kind>`) and which runs for each part whose `Delivery kind:` row in "
                            "`docs/INVENTORY.md` names that kind, beside \"Deliver the installer\" above and before the "
                            "promotion pass; the report and the User Manual name what was delivered and where it is.",
}


@pytest.mark.parametrize("key", ["reflection", "project-end"])
def test_r006_each_point_says_where_its_additions_are_made(key):
    """R-006: each point's line places the additions a conditional workflow makes there and says what the registry's
    Applies cell states: a point that applies per project is made once for the whole project; one that applies per part
    names the part (TASK-013's rule)."""
    applies = {r["Key"]: r["Applies"] for r in registry_rows("## Extension points")}
    body = section(module(key), "Extension points", 2).strip().split("\n")
    for line in [l for l in body if l.startswith("- ")]:
        k = re.match(r"^- `([a-z0-9.-]+)` — ", line).group(1)
        assert line == "- `%s` — %s" % (k, POINTS[k]), line
        if applies[k] == "project":
            assert line.endswith("; made once for the whole project."), (k, line)
        else:
            assert applies[k] == "part" and re.search(r"\b(of|for) the part\b", line), (k, applies[k], line)
            assert "whole project" not in line, line


def test_r006_the_reflection_items_point_is_placed_before_the_record():
    """R-006: the numbered items the reflection point adds to exist as the point's line names them: item 4 the User
    Manual, item 5 the record of the reflection point."""
    proc = section(module("reflection"), "The procedure", 3)
    assert "\n4. **User Manual** (once it exists)." in proc
    assert "\n5. **Record** the reflection point in `docs/PROJECT_STATUS.md` (`Last reflection:`)" in proc


def test_r006_the_tree_wide_registry_module_cross_check():
    """R-006 and TASK-014's Done when: every point of the registry is declared by the module it names, every module's
    declaration is in the registry, in the registry's order, for every module the registry lists; every module the
    registry lists is a file under workflow/phases/ and every file there is a module the registry lists; no sub-file or
    variant file declares a point (a module declares its points itself)."""
    modules = [r["Module"] for r in registry_rows("## Phase modules")]
    points = registry_rows("## Extension points")
    assert len(modules) == len(set(modules)) == 10, modules
    assert all(p["Declared by"] in modules for p in points), [p for p in points if p["Declared by"] not in modules]
    top = sorted(f[:-3] for f in os.listdir(PHASES) if f.endswith(".md"))
    assert top == sorted(modules), (top, modules)
    every = []
    for m in modules:
        got = declared(module(m))
        assert got == registry_points(m), (m, got, registry_points(m))
        every += got
    assert sorted(every) == sorted(p["Key"] for p in points), every
    for root, _dirs, files in os.walk(PHASES):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), PHASES).replace(os.sep, "/")
            if "/" in rel:
                assert (2, "Extension points") not in headings(read(os.path.join(root, f))), rel


def test_r036_the_promotion_pass_puts_the_flagged_traits_forward():
    """R-036, the project-end half (the design-gate half is TASK-011's): the promotion pass reads the inventory's
    `Flagged trait:` rows beside the Issues and Feedback documents and proposes each trait as the maintainer could
    write it; the supervisor writes no trait file. The row is the one design.md writes at the gate."""
    s = flat(section(module("project-end"), "Flagged traits in the promotion pass", 3)).strip()
    assert s == ("The promotion pass reads a third source beside the Issues and Feedback documents: every row of "
                 "`docs/INVENTORY.md` → Decisions that begins `Flagged trait:`, written at the design gate for a new trait "
                 "or one defined but not yet written, whose handling the project's design carries (`design.md`, \"Traits "
                 "at the design gate\"). For each, \"Proposed bridge changes\" proposes the trait as the maintainer could "
                 "write it: for a new trait, its entry in the open list (`~/.claude/cursor-bridge/workflow/open-list.md`), "
                 "with its definition; for a new trait and an unwritten one alike, its additions, each under the `## Add "
                 "at <point key>` heading of the extension point at which the project's design handled it, drafted from "
                 "that handling and naming the design section and the row they come from. The maintainer writes the "
                 "trait or not; you write no trait file and change nothing in the open list (the open list, \"A new trait "
                 "is flagged, and the work continues\").")
    end = flat(module("project-end"))
    assert "- **Run the promotion pass.** Read the Issues document and the Feedback document whole" in end
    design = flat(module("design"))
    assert ("Record each flagged trait in `docs/INVENTORY.md` → Decisions as a row that begins `Flagged trait:`, naming "
            "the trait, the parts that have it and the design section that handles it, so that the promotion pass at "
            "project end puts it forward") in design
    assert "**A new trait is flagged, and the work continues.**" in read(os.path.join(CB, "workflow", "open-list.md"))


def test_r004_an_issue_records_whether_a_compaction_preceded_it():
    """TASK-014's Done when (the compaction baseline's follow-up, Restructuring Plan §14.3): the issues rule, read
    whenever an issue is detected, has each entry give the incident's time and whether a compaction preceded it, under
    a heading of its own inside the issues section."""
    issues = section(module("reflection"), "Issues — what counts, and where it is written", 3)
    assert "\n#### Whether a compaction preceded it\n" in issues
    s = flat(section(module("reflection"), "Whether a compaction preceded it", 4)).strip()
    assert s == ("Every entry's part written on detection also gives the time the incident happened, in UTC, and one "
                 "line, `Compaction before: yes, <the compaction's time in UTC, where known>` or `Compaction before: "
                 "no`: whether the session's context was compacted, or the session resumed, between your last whole "
                 "reading of the governing text and the incident. The bridge's maintainer measures from these lines how "
                 "often a rule is broken within an hour of a compaction, which entries carrying a date alone could not "
                 "show.")


def test_the_change_cycle_runs_the_variant_of_every_interface_kind_it_touches():
    """HARDENING Stage B3 (Review A, for TASK-014): item 3 runs the interface variant of every kind the change touches,
    not only the mockups (a local service's next change would otherwise skip its contract design, §6.8), amends what
    was approved and re-presents no untouched kind; the closing gate sentence names each variant's artifact."""
    proc = section(module("change-cycle"), "The procedure", 3)
    item3 = [l for l in proc.split("\n") if l.startswith("3. ")]
    assert item3 == ["3. **The interface variants** (Phase 3) **only for the kinds of interface the change touches** — "
                     "screens, commands, a protocol other software calls, play — each kind by the variant `interface.md` "
                     "gives it (\"The variants\", \"Which variants a part runs\"), and each run only for the screens and "
                     "states, the commands or the operations the change adds or alters. An artifact already approved is "
                     "amended, not replaced (for screens, the mockups and the visual system); an artifact the part does "
                     "not have yet is written for what the change touches; a kind the change does not touch is not "
                     "re-presented. Gate as in Phase 3, for the variants run."], item3
    assert "**only if the change touches the UI**" not in proc
    assert ("The gates of a change cycle are the same approvals the original build had — the change design, the artifact "
            "of each interface variant the change runs, the plan addendum.") in flat(proc)
    assert "the mockup if any" not in proc


# sha256 of the change cycle's procedure as TASK-014 leaves it (from its heading to the file's end, LF, the whitespace at
# its end stripped; 6,094 characters): the trace entry on "The procedure" excuses new text anywhere under it, so CI holds
# the section's text here (trace-check has no CI step, INVENTORY Decisions); a later reword updates this with its record
PROCEDURE_SHA256 = "13d899566e54047361783cd57d3c6f61ae3886c51f59de2fc87e2baaca0c6cab"


def test_the_change_cycles_procedure_is_pinned():
    """The trace exceptions' lead (HARDENING Stage B3): the change cycle's procedure holds reworded and new text under
    one excused heading, so its whole text is fixed here and a passage added to it or copied into it later fails."""
    text = module("change-cycle")
    proc = text[text.index("### The procedure"):].rstrip()
    assert len(proc) == 6094 and hashlib.sha256(proc.encode("utf-8")).hexdigest() == PROCEDURE_SHA256, len(proc)


def test_r004_the_positions_the_survival_lists_name_are_kept():
    """R-004: what each survival list names as the position is written as the procedure runs: the change cycle's step on
    its `Change cycle:` line; the reflection point's and project end's finished steps in run/supervisor/in-flight.md,
    since what the items write under Documents/ is not under git."""
    cc = flat(section(module("change-cycle"), "The procedure", 3))
    assert ("Keep the step the change has reached on the `Change cycle:` line, rewritten as each step's gate passes, so "
            "that a resume after a compaction starts where the change stands and asks no approval twice.") in cc
    r = flat(section(module("reflection"), "Keeping the position", 3)).strip()
    assert r == ("As each step above finishes (the stage review, the demonstration, each numbered item), write one line to "
                 "`run/supervisor/in-flight.md` naming the reflection point and the step finished, and name the file on "
                 "the status file's `Working files:` line (rule 54). A resume after a compaction reads its last entries "
                 "and starts at the next step, so that no Issues or Feedback entry is written twice and none is skipped: "
                 "what the items write under `Documents/` is not under git, and nothing else shows how far they got.")
    p = flat(section(module("project-end"), "Keeping the position", 3)).strip()
    assert p == ("Keep the position as the reflection points keep theirs (`reflection.md`, \"Keeping the position\"): as "
                 "each item above finishes, one line in `run/supervisor/in-flight.md` naming it, so that a resume after a "
                 "compaction starts at the next item and writes nothing under `Documents/` twice.")


def test_no_trace_entry_excuses_a_whole_phase_file():
    """HARDENING Stage B3 (the trace exceptions, from S1): a `new` entry on a file's top heading excuses every passage in
    the file, so a passage added under it, or a copy of one, passes unseen; each variant file's declaring paragraph is
    under a heading of its own, and no entry names the top heading of a file under workflow/phases/."""
    entries = [l for l in read(EXCEPTIONS).split("\n") if l.startswith("- new ")]
    prefix = "bridge/cursor-bridge/workflow/phases/"
    seen = 0
    for e in entries:
        m = re.match(r"^- new \S+ (\S+\.md) (.+)$", e)
        if m and m.group(1).startswith(prefix):
            seen += 1
            text = module(m.group(1)[len(prefix):])
            assert headings(text)[0][1] != m.group(2), e
    assert seen > 30, seen
    for f in ("mockups", "command-design", "contract-design", "playable-prototype"):
        assert "- new TASK-014 %sinterface/%s.md What this variant is" % (prefix, f) in entries, f


@pytest.mark.parametrize("rel", KEYS)
def test_r032_the_module_is_read_whole(rel):
    """R-032: each enriched module stays within the bound a module is read whole by."""
    text = module(rel)
    assert text.count("\n") <= 1500 and len(text) <= 60000, (rel, text.count("\n"), len(text))


def test_the_glossary_names_the_modules_as_files():
    """The pointer sweep (HARDENING Stage B3, the carve's lead): the glossary's phase-module entry no longer says a
    module may still be a section of the core, or that project end is part of the reflection points."""
    g = flat(read(GLOSSARY))
    assert "project end is today part of the Reflection points section" not in g
    assert "Until a module is moved into a file of its own" not in g
    assert ("Each is a file of its own under `workflow/phases/`; a module too long to be read whole keeps a step in a "
            "sub-file under `workflow/phases/<module>/` (the delegation loop's step 9), and the interface phase keeps one "
            "file per variant under `workflow/phases/interface/`.") in g
