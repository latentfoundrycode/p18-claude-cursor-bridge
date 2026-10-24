"""TASK-012: the interface and planning modules enriched (R-004, R-006, R-010, R-012, R-032).

enforces: docs/REQUIREMENTS.md R-004 (each phase module opens with the short list of what must survive a compaction),
R-006 (each phase module declares the points the registry names it as declaring), R-010 (the interface phase runs one
variant per kind of interface a part has, and the trait *has screens* adds the mockup variant, an addition, not a
replacement; the build-phase conditions of screens stay with the build modules), R-012 (the four variants declared
once in the interface module, each variant's text in one place), R-032 (each module and each variant file read whole);
docs/BUILD_PLAN.md TASK-012's Done when (the playable-prototype file a declared pointer worded clear of
completion-check's stand-in patterns), and its pointer sweep (docs/HARDENING.md, Stage B3)."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

from phase_modules import read, module, flat, headings, section, registry_points

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CB = os.path.join(BRIDGE, "cursor-bridge")
PHASES = os.path.join(CB, "workflow", "phases")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
HOOK = os.path.join(CB, "session-start.py")

VARIANTS = [
    ("Mockups", "screens a person sees", "interface/mockups.md"),
    ("Command design", "commands a person types", "interface/command-design.md"),
    ("Contract design", "a protocol other software calls", "interface/contract-design.md"),
    ("Playable prototype", "play", "interface/playable-prototype.md"),
]


STRUCTURE = {
    "interface": [(2, "Phase 3 — Interface"), (3, "What must survive a compaction"), (3, "The variants"),
                  (3, "Which variants a part runs"), (3, "The interface notes"), (3, "The gate"),
                  (2, "Extension points")],
    "planning": [(2, "Phase 4 — Build plan"), (3, "What must survive a compaction"),
                 (3, "Step 0 — Prior-project lessons (ask before drafting)"),
                 (3, "What the interface phase hands to the plan"), (3, "The plan"), (2, "Extension points")],
}

SURVIVAL = {
    "interface": [
        "this module and every variant file, each whole (the session-start hook names the four variant files with it; "
        "a variant no part runs is read only to know it does not apply);",
        "the approved design: `docs/DESIGN.md`, `docs/REQUIREMENTS.md`, `docs/INVENTORY.md`, and `docs/diagrams/INDEX.md` "
        "with every diagram it lists, whole: each variant maps onto the agreed functionality, adds its screens, commands "
        "or operations to the register, and agrees with the diagrams (the mockups with the operational activity "
        "diagram's screens);",
        "what each running variant has produced so far: `docs/design/DESIGN.md` and `docs/mockups/` for the mockups, "
        "`docs/design/COMMANDS.md` for the command design, `docs/design/CONTRACT.md` and the contract file it names for "
        "the contract design;",
        "`run/supervisor/interface-notes.md` (\"The interface notes\"), whole;",
        "`docs/PROJECT_STATUS.md`, whole: its `Workflows:` line names each part's conditional workflows, which activate "
        "variants at `interface.variants` beside the kinds of interface the design shows, and its `Awaiting user on:` "
        "line says which variant waits for the owner;",
        "once this phase's gate is approved, its reflection point: `~/.claude/cursor-bridge/workflow/phases/reflection.md`, "
        "whole, and the last entries of `run/supervisor/in-flight.md`, the items it has finished (\"Keeping the "
        "position\"), until the reflection point is done.",
    ],
    "planning": [
        "this module, whole;",
        "the approved design and what the interface phase approved: `docs/DESIGN.md`, `docs/REQUIREMENTS.md`, "
        "`docs/INVENTORY.md`, `docs/diagrams/INDEX.md` and every diagram it lists, and the approved artifacts under "
        "`docs/design/` and `docs/mockups/`, whole: every increment satisfies requirements of the register and cites "
        "what it implements;",
        "`docs/BUILD_PLAN.md` as drafted so far, whole, and each Issues file the owner named at Step 0, whole (its path "
        "stands in the plan's Prior-project lessons section, Step 0);",
        "`docs/DESIGN_CRITIQUE.md`, whole, while the plan critique runs, with `docs/RUN_PARAMETERS.md` and the round's "
        "files under `run/review/` (`DESIGN-plan-<round>.md` and its `REVIEW-DESIGN-` files) while a round is in "
        "flight, and `~/.claude/cursor-bridge/workflow/phases/design.md`'s \"The procedure\", whose two-critic loop, "
        "stop rule, ceiling, confirming read and resolution round the plan critique runs: it counts its rounds as the "
        "design critique does;",
        "`docs/PROJECT_STATUS.md`, whole: its `Awaiting user on:` line says whether Step 0's question or the plan's "
        "gate waits for the owner;",
        "`~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`'s steps 3b and 8, while a critique round is in "
        "flight or a launch has failed: a round is snapshotted and verified as step 8 says, the snapshot's hash "
        "written to `run/supervisor/in-flight.md` at the launch, and a failed launch is handled as step 3b "
        "says;",
        "once this phase's gate is approved, its reflection point: `~/.claude/cursor-bridge/workflow/phases/reflection.md`, "
        "whole, and the last entries of `run/supervisor/in-flight.md`, the items it has finished (\"Keeping the "
        "position\"), until the reflection point is done.",
    ],
}


@pytest.mark.parametrize("key", ["interface", "planning"])
def test_r004_the_module_opens_with_its_compaction_survival_list(key):
    """R-004: the module's first section, straight after its heading, is the compaction-survival list, and the list is
    exactly what a resumed session in that phase reads before its next action."""
    text = module(key)
    assert headings(text) == STRUCTURE[key], headings(text)
    lines = text.split("\n")
    assert lines[1] == "" and lines[2] == "### What must survive a compaction", lines[:3]
    body = section(text, "What must survive a compaction", 3).strip().split("\n")
    assert body[0] == "After a compaction or a resume in this phase, read these before your next action:"
    assert all(l.startswith("- ") for l in body[1:] if l), body
    assert [l[2:] for l in body[1:] if l] == SURVIVAL[key]


@pytest.mark.parametrize("key", ["interface", "planning"])
def test_r006_the_module_declares_exactly_its_registry_points_in_the_registrys_order(key):
    """R-006 and the registry's "How a phase module declares its points": a `## Extension points` section, one line
    per point giving its key, exactly the points the registry names this module as declaring, in the table's order."""
    body = section(module(key), "Extension points", 2).strip().split("\n")
    lines = [l for l in body if l.startswith("- ")]
    keys = [re.match(r"^- `([a-z0-9.-]+)` — \S", l).group(1) for l in lines]
    want = registry_points(key)
    assert want and keys == want, (keys, want)
    prose = flat(" ".join(l for l in body if l and not l.startswith("- ")))
    assert prose == ("This module offers the points below, each by its key in the extension-point registry "
                     "(`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each "
                     "accepts and whether it applies per part or per project. A conditional workflow's additions at a "
                     "point are made where the point's line places them, in the order the core states in \"Main and "
                     "conditional workflows\".")
    assert "may set" not in "\n".join(body)


def test_r012_the_four_variants_are_declared_once_in_the_interface_module():
    """R-012: the interface module's table names the four variants, each with its interface kind and its file, and the
    module's one `Variants:` pointer line names exactly those files in that order, in the grammar session-start.py
    reads (a line at column 0 outside fences, paths separated by `; `)."""
    s = section(module("interface"), "The variants", 3)
    rows = [l for l in s.split("\n") if l.startswith("| ") and not l.startswith("| Variant ")]
    assert rows == ["| %s | %s | `%s` |" % v for v in VARIANTS], rows
    text = module("interface")
    pointer = [l for l in text.split("\n") if l.startswith("Variants: ") or l.startswith("Sub-files: ")]
    assert pointer == ["Variants: " + "; ".join(v[2] for v in VARIANTS)], pointer
    assert "Every variant is an addition, never a replacement of another" in flat(s)


def test_r012_each_variants_text_is_in_one_place():
    """R-012: each variant file exists, opens with its variant's heading, says which interface kind it is for and points
    back to the interface module, in a declaring paragraph under a heading of its own (TASK-014: so that the trace entry
    excusing it excuses nothing else in the file); no other file under workflow/phases/ carries a variant's heading."""
    titles = set()
    for name, _kind, rel in VARIANTS:
        text = module(rel)
        assert text.split("\n")[0] == "## " + name, (rel, text.split("\n")[0])
        assert text.split("\n\n")[1] == "### What this variant is", rel
        assert "(`interface.md`, \"The variants\")" in section(text, "What this variant is", 3).split("\n\n")[0], rel
        titles.add(name)
    for root, _dirs, files in os.walk(PHASES):
        for f in files:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, PHASES).replace(os.sep, "/")
            if rel in [v[2] for v in VARIANTS]:
                continue
            for _level, title in headings(read(path)):
                assert title not in titles, (rel, title)


def test_r010_the_mockups_are_an_addition_the_trait_has_screens_activates():
    """R-010 (§6.5, "Today's interface conditions stay together"): the mockups are an addition, not a replacement,
    activated by the trait *has screens* at `interface.variants`; a part with screens has the trait by its definition,
    and a missing trait is settled at the design gate."""
    m = flat(section(module("interface/mockups.md"), "What this variant is", 3))
    assert ("They are an addition, never a replacement: the trait *has screens* activates them at `interface.variants` "
            "for each part that has screens, beside any other variant the part runs") in m
    runs = flat(section(module("interface"), "Which variants a part runs", 3))
    assert ("The mockups are activated by the trait *has screens*, which a part with screens has by its definition; a "
            "part whose design shows screens without the trait on its `Workflows:` line has a trait missing, which the "
            "design gate settles (`design.md`, \"Traits at the design gate\") before this phase begins, and a missing trait "
            "found during this phase goes back to the owner as that same decision, asked on its own, before any mockup is "
            "approved.") in runs


def test_r010_the_mockups_file_holds_the_phase_3_procedure_and_not_the_build_conditions():
    """R-010 and TASK-012's Done when: interface/mockups.md holds today's Phase 3 mockup procedure, verbatim (its
    passages, its design-tooling flow, its gate and the mockup's authority); the build-phase conditions of screens (the
    frozen-rule brief constraint, the design-auditor review step, the observability tests) are the trait *has screens*'
    additions at the delegation loop's points, moved there out of the delegation-loop module (TASK-017)."""
    m = module("interface/mockups.md")
    assert headings(m) == [(2, "Mockups"), (3, "What this variant is"), (3, "The procedure"),
                           (3, "The design-tooling flow")], headings(m)
    fm = flat(m)
    for passage in (
        "Build an HTML/CSS mockup of the interface — a static, disposable design artifact for the user to judge and "
        "change, not the product's real frontend.",
        "The mockup must map onto the agreed functionality **with no gaps, in both directions**",
        "**Approve the pair.** The user approves the **mockup and the visual `DESIGN.md` together**",
        "**Gate:** present the mockup **and the visual `docs/design/DESIGN.md`** to the user and get explicit approval "
        "of the pair before writing the build plan.",
        "**The approved mockup's authority:** once approved, the mockup is **guidance**, not a pixel contract.",
    ):
        assert passage in fm, passage
    loop = flat(module("delegation-loop"))
    screens = flat(module("../traits/has-screens.md"))
    for build in ("list the frozen `vercel-interface.mdc` as an applicable rule",
                  "For a **UI-bearing** diff, also delegate to **design-auditor** after `diff-reviewer`",
                  "the tests you write include the **observability tests** (Tier A)"):
        assert build in screens, build
        assert build not in loop, build
        assert build not in fm, build
    assert "Build an HTML/CSS mockup" not in module("interface")


def test_r012_each_variant_names_the_artifact_the_module_and_the_plan_cite():
    """R-012 (Review A round 2, convergent with the security re-check): the artifacts interface.md's survival list and
    planning.md cite are named by the variant that writes them, with its approval at the phase's gate, so no module
    cites a file nothing defines; their bodies follow in TASK-022."""
    c = flat(module("interface/command-design.md"))
    assert ("Its artifact is `docs/design/COMMANDS.md`, one section per command, and the owner approves it at the phase's "
            "gate (`interface.md`, \"The gate\").") in c
    k = flat(module("interface/contract-design.md"))
    assert ("Its artifacts are `docs/design/CONTRACT.md`, which states in plain words every operation the part offers, "
            "and the machine-readable contract file `CONTRACT.md` names, which tests enforce; the owner approves what the "
            "part offers, from `CONTRACT.md`, at the phase's gate (`interface.md`, \"The gate\").") in k
    survival = flat(section(module("interface"), "What must survive a compaction", 3))
    plan = flat(section(module("planning"), "What the interface phase hands to the plan", 3))
    for name in ("`docs/design/COMMANDS.md`", "`docs/design/CONTRACT.md`"):
        assert name in survival, name
    assert "`docs/design/CONTRACT.md`" in plan and "`docs/design/COMMANDS.md`" in c and "`docs/design/CONTRACT.md`" in k


def test_r010_no_text_calls_the_mockups_a_replacement():
    """R-010, the negative side (Review A's consider): neither the interface module nor the mockups file calls the
    mockups a replacement of anything; only a type workflow or sub-workflow replaces, and it replaces the phase."""
    called = re.compile(r"[Mm]ockups?\b[^.;:,]*\b(is|are) a replacement")
    replacing = re.compile(r"[Mm]ockups? (replace|replaces)\b")
    assert called.search("the mockups are a replacement for it") and replacing.search("the mockups replace it")
    for rel in ("interface.md", "interface/mockups.md"):
        text = flat(module(rel))
        assert called.search(text) is None and replacing.search(text) is None, rel


def test_r004_the_interface_notes_are_written_by_the_procedure_and_no_key_among_them():
    """R-004 (the survival list names the interface notes) and Review A's should-fix: writing them is an instruction
    of the procedure, the file is named on Working files: (rule 54), and the security audit's advisory: a pasted key is
    never written there (rule 53)."""
    s = flat(section(module("interface"), "The interface notes", 3))
    assert ("Write every change the owner asks for on a variant's artifact, and whether it is made, to "
            "`run/supervisor/interface-notes.md` as each request arrives, and name the file on the status file's "
            "`Working files:` line (rule 54).") in s
    assert ("A key, token or password the owner pastes is never written there: rule 53 applies to it, and the note says "
            "only that one was given.") in s


def test_r004_the_issues_paths_are_written_by_step_0():
    """R-004 (the planning survival list names the Issues files by the paths in the plan) and Review A's should-fix:
    Step 0 writes each path into the plan as soon as the owner names it."""
    s = flat(section(module("planning"), "Step 0 — Prior-project lessons (ask before drafting)", 3))
    assert ("Write each path the owner names into the plan's Prior-project lessons section as soon as they name it, "
            "before you read the file: the conversation that held it does not survive a compaction (rule 54).") in s


def test_r012_the_gate_asks_for_every_variant_and_for_none():
    """R-012 and rule 5: the phase passes when every variant every part runs is approved, each as its own question;
    when no part runs any variant the owner's word is still asked (Review A's consider)."""
    s = flat(section(module("interface"), "The gate", 3))
    assert "each variant's approval asked as a question of its own in the app's question form" in s
    assert ("When no part runs any variant, the gate still asks the owner's word, that no part has an interface to judge "
            "before the build (rule 5).") in s
    assert "The phase passes when every variant every part runs is approved." in s


def test_r012_the_plan_builds_against_what_the_interface_phase_approved():
    """R-012 with the planning module (Review A's should-fix: the contract-enforcement increment is a Phase 4 duty,
    stated where Phase 4 reads it): every approved contract gets an increment whose tests check the built part against
    the contract file."""
    s = flat(section(module("planning"), "What the interface phase hands to the plan", 3))
    assert ("for every contract the contract design approved (`docs/design/CONTRACT.md`), the plan carries an increment "
            "whose tests check the built part against the contract file, so that the contract is enforced, never only "
            "described.") in s
    assert "every increment that builds a command cites the approved command design's section for it" in s


def standin_rx():
    spec = importlib.util.spec_from_file_location("completion_check", os.path.join(CB, "completion-check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.STANDIN_RX


def test_the_playable_prototype_is_a_declared_pointer_with_no_stand_in_wording():
    """TASK-012's Done when: the playable-prototype file is a declared pointer to the Game Development workflow
    (release E), worded clear of completion-check's stand-in patterns, as are the interface module and every variant
    file. (completion-check.py reads code files only, so its run cannot see a Markdown stand-in; the patterns are applied
    here directly. The rest of workflow/ is not scanned: project-end.md quotes the patterns as the rule's own text.)"""
    p = flat(module("interface/playable-prototype.md"))
    assert "Its procedure belongs to the Game Development type workflow, which replaces this phase" in p
    assert "The main workflow holds no procedure for play beyond this pointer." in p
    rx = standin_rx()
    # the precondition (Review A's blocking item): the patterns catch a stand-in, so their silence below means something
    assert rx.search("this screen arrives in a later release")
    assert rx.search("coming soon")
    for rel in ["interface.md", "planning.md"] + [v[2] for v in VARIANTS]:
        hit = rx.search(module(rel))
        assert hit is None, (rel, hit and hit.group(0))


@pytest.mark.parametrize("rel", ["interface.md", "planning.md"] + [v[2] for v in VARIANTS])
def test_r032_the_module_and_each_variant_file_are_read_whole(rel):
    """R-032: each enriched module and each variant file stays within the bound a module is read whole by."""
    text = module(rel)
    assert text.count("\n") <= 1500 and len(text) <= 60000, (rel, text.count("\n"), len(text))


def test_r005_the_hook_names_the_interface_module_and_its_four_variants(tmp_path):
    """R-005 with R-012, the first real pointer line: for `Phase: mockups` the installed hook names interface.md and,
    after it, the four variant files in the `Variants:` line's order (FIX-003 hardened the hook for this line)."""
    home = tmp_path / "home"
    shutil.copytree(os.path.join(BRIDGE, "commands"), str(home / ".claude" / "commands"))
    shutil.copytree(CB, str(home / ".claude" / "cursor-bridge"), ignore=shutil.ignore_patterns("__pycache__"))
    ws = tmp_path / "proj" / "Workspace"
    (ws / "docs").mkdir(parents=True)
    (ws / "docs" / "PROJECT_STATUS.md").write_text(
        "# Project Status\nPhase: mockups\nWorkflows: not yet classified\nAwaiting user on: nothing\n", encoding="utf-8")
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    data = {"cwd": str(ws), "hook_event_name": "SessionStart", "source": "compact"}
    p = subprocess.run([sys.executable, HOOK, "--part", "pointers"], input=json.dumps(data), capture_output=True,
                       text=True, encoding="utf-8", env=env)
    assert p.returncode == 0 and p.stderr == "", p.stderr
    w = "~/.claude/cursor-bridge/workflow/phases/"
    named = [re.match(r"  - (\S+)", l).group(1) for l in p.stdout.split("\n") if l.startswith("  - " + w)]
    assert named == [w + "interface.md"] + [w + v[2] for v in VARIANTS], p.stdout


def test_the_interface_phase_is_named_by_its_variants_outside_the_module():
    """The pointer sweep (docs/HARDENING.md, Stage B3): the core's module table and the design gate named Phase 3 as
    "the UI mockups", which is now one variant of the interface phase."""
    core = flat(read(CORE))
    assert "| The interface phase (Phase 3, today the UI mockups) |" not in core
    assert ("| The interface phase (Phase 3: one variant per kind of interface, the mockups among them) | "
            "`~/.claude/cursor-bridge/workflow/phases/interface.md` and its variant files under "
            "`~/.claude/cursor-bridge/workflow/phases/interface/` |") in core
    gate = flat(section(module("design"), "The gate", 3))
    assert "Do not proceed to the UI mockups" not in gate
    assert "Do not proceed to the interface phase until they approve it." in gate
