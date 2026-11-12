"""TASK-014: the change-cycle, reflection and project-end modules enriched (R-004, R-006, R-032, R-036).

enforces: docs/REQUIREMENTS.md R-004 (each phase module opens with the short list of what must survive a compaction),
R-006 (each phase module declares the points the registry names it as declaring; the tree-wide cross-check of the
registry against every module, BUILD_PLAN TASK-014's Done when, and the registry's "How a phase module declares its
points"), R-032 (each module read whole), R-036 (a new or unwritten trait is put to the promotion pass at project end);
docs/BUILD_PLAN.md TASK-014's Done when (the issues rule's line on whether a compaction preceded an incident, the
compaction baseline's follow-up); docs/HARDENING.md, Stage B3's leads for TASK-014 (the change cycle runs the variant of
every interface kind a change touches; the variant files' declaring paragraphs under headings of their own; the promotion
pass reads the inventory's `Flagged trait:` rows; the pointer sweep, the glossary's phase-module entry)."""
import os
import re

import pytest

from phase_modules import (read, module, flat, headings, section, registry_rows, registry_points,
                           assert_declares_registry_points, assert_points_placed)

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CB = os.path.join(BRIDGE, "cursor-bridge")
PHASES = os.path.join(CB, "workflow", "phases")
EXCEPTIONS = os.path.join(CB, "workflow", "trace-exceptions.md")
GLOSSARY = os.path.join(CB, "Glossary.md")


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
    want = assert_declares_registry_points(key)
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
                            "`docs/INVENTORY.md` names that kind, after the User Manual item above and before the "
                            "promotion pass; the report and the User Manual name what was delivered and where it is.",
}


@pytest.mark.parametrize("key", ["reflection", "project-end"])
def test_r006_each_point_says_where_its_additions_are_made(key):
    """R-006: each point's line places the additions a conditional workflow makes there and says what the registry's
    Applies cell states: a point that applies per project is made once for the whole project; one that applies per part
    names the part (TASK-013's rule)."""
    assert_points_placed(key, POINTS)


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
                 "that handling and naming the design section and the row they come from. Each is written in general "
                 "terms, for every project the trait may reach: no path of this computer, no key and none of the "
                 "project's data (rules 53 and 54); and each proposed file stands in a fenced block whose first line "
                 "reads `Proposal — not in force`, so that no later reading of the Feedback document takes its `## Add "
                 "at` headings for additions in force. The maintainer writes the "
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
                 "line, `Compaction before:` followed by `yes` and the compaction's time in UTC where it is known, or by "
                 "`no`: whether the session's context was compacted between your last whole reading of the governing "
                 "text and the incident. A resume or a fork of the session in that time is not a compaction and is "
                 "written on a line of its own, `Resumed before:` or `Forked before:` with its time where known (the "
                 "session-start hook's message after each says which of the three it follows, when its input names it; where it names none, and says *compacted or resumed*, the line reads "
                 "`Compaction before: unknown`). The bridge's maintainer "
                 "measures from these lines how often a rule is broken within an hour of a compaction, which entries "
                 "carrying a date alone could not show.")
    # Review B, round 1: a resume is not a compaction, so `yes` names a compaction only and a resume has a line of its
    # own (the hook tells the three apart: session-start.py's compact, resume and fork messages)
    assert "`Compaction before:` followed by `yes`" in s and "`Resumed before:`" in s and "or the session resumed" not in s


def test_the_change_cycle_runs_the_variant_of_every_interface_kind_it_touches():
    """HARDENING Stage B3 (Review A, for TASK-014): item 3 runs the interface variant of every kind the change touches,
    not only the mockups (a local service's next change would otherwise skip its contract design, §6.8), amends what
    was approved and re-presents no untouched kind; the closing gate sentence names each variant's artifact."""
    proc = section(module("change-cycle"), "The procedure", 3)
    item3 = [l for l in proc.split("\n") if l.startswith("3. ")]
    assert item3 == ["3. **The interface variants** (Phase 3) **only for the kinds of interface the change touches** — "
                     "screens, commands, a protocol other software calls, play — each kind by the variant `interface.md` "
                     "gives it (\"The variants\", \"Which variants a part runs\"), or by the replacement of a part whose type "
                     "workflow replaces the interface phase, and each run only for the screens and states, the "
                     "commands or the operations the change adds or alters. An artifact already approved is "
                     "amended, not replaced (for screens, the mockups and the visual system); an artifact the part does "
                     "not have yet is written for what the change touches; a kind the change does not touch is not "
                     "re-presented. Gate as in Phase 3, for the variants run; a change that touches no kind of interface runs "
                     "no variant and holds no interface gate."], item3
    assert "**only if the change touches the UI**" not in proc
    assert ("The gates of a change cycle are the same approvals the original build had — the change design, the artifact "
            "of each interface variant the change runs, the plan addendum.") in flat(proc)
    assert "the mockup if any" not in proc


def test_r004_the_positions_the_survival_lists_name_are_kept():
    """R-004: what each survival list names as the position is written as the procedure runs: the change cycle's step on
    its `Change cycle:` line; the reflection point's and project end's finished steps in run/supervisor/in-flight.md,
    since what the items write under Documents/ is not under git."""
    cc = flat(section(module("change-cycle"), "The procedure", 3))
    assert ("Keep the step the change has reached on the `Change cycle:` line, rewritten as each step is reached or its "
            "gate passes, so that a resume after a compaction starts where the change stands and asks no approval twice.") in cc
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
    under a heading of its own, and no entry names the top heading of a file under workflow/phases/, nor of a
    conditional workflow under workflow/traits/ or workflow/types/, which trace-check.py reads as modules too
    (TASK-017). A `reword` entry
    excuses the current text under its heading as a `new` one does (trace-check.py, build_excuse_index), so both kinds
    are read, and an entry's heading is stripped as trace-check.py's parse_exceptions strips it (stage B3's review,
    round 1; BUG-017's Review A)."""
    entries = [l for l in read(EXCEPTIONS).split("\n") if l.startswith(("- new ", "- reword "))]
    prefix = "bridge/cursor-bridge/workflow/phases/"
    conditional = ("bridge/cursor-bridge/workflow/traits/", "bridge/cursor-bridge/workflow/types/")
    seen = conditional_seen = 0
    for e in entries:
        m = re.match(r"^- (?:new|reword) \S+ (\S+\.md) (.+)$", e)
        if m and m.group(1).startswith(prefix):
            seen += 1
            text = module(m.group(1)[len(prefix):])
            assert headings(text)[0][1] != m.group(2).strip(), e
        elif m and m.group(1).startswith(conditional):
            conditional_seen += 1
            text = read(os.path.join(BRIDGE, os.pardir, m.group(1)))
            assert headings(text)[0][1] != m.group(2).strip(), e
    assert seen > 30, seen
    assert conditional_seen > 10, conditional_seen
    for f in ("mockups", "command-design", "contract-design", "playable-prototype"):
        assert "- new TASK-014 %sinterface/%s.md What this variant is" % (prefix, f) in entries, f


def test_the_glossary_names_the_modules_as_files():
    """The pointer sweep (HARDENING Stage B3, the carve's lead): the glossary's phase-module entry no longer says a
    module may still be a section of the core, or that project end is part of the reflection points."""
    g = flat(read(GLOSSARY))
    assert "project end is today part of the Reflection points section" not in g
    assert "Until a module is moved into a file of its own" not in g
    assert ("Each is a file of its own under `workflow/phases/`; a module too long to be read whole keeps a step in a "
            "sub-file under `workflow/phases/<module>/` (the delegation loop's step 9), and the interface phase keeps one "
            "file per variant under `workflow/phases/interface/`.") in g


def test_bug035_a_change_cycle_reads_the_conditional_workflows_of_the_step_it_has_reached():
    """BUG-035 (TASK-026's release-level review, pass 1, M1): while the phase is `changing` the session-start hook names
    the change cycle's own modules only, so after a compaction in a change's intake, design or interface step the
    conditional workflows touching that step's module (claude-code-extension.md at design, local-service.md at the
    interface, local-web-app.md and own-computer.md at intake) were never named. The survival list says to read them,
    and its parenthesis names the modules the hook does name, which are the hook's own table.

    enforces: change-cycle.md "What must survive a compaction"; docs/REQUIREMENTS.md R-004 (what must survive a
    compaction), R-005 (the hook names the phase's modules and the conditional workflows that touch them)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("session_start_for_bug035", os.path.join(CB, "session-start.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    text = flat(section(module("change-cycle"), "What must survive a compaction", 3))
    clause = "the module of the step the change has reached, with the conditional workflows the `Workflows:` line names that touch it"
    assert clause in text, "the change cycle's survival list does not name the step's conditional workflows"
    hook = mod.PHASE_MODULES["changing"]
    named = text[text.index(clause):].split("):", 1)[0]
    assert hook[0] == "change-cycle" and set(re.findall(r"`([\w-]+)\.md`", named)) == set(hook[1:]), (hook, named)
    for step in ("intake", "design", "interface"):
        assert step not in hook, "the hook now names %s.md while changing; the parenthesis is no longer true" % step
