"""TASK-017: the trait files has screens, installable, performance budgets and external services (R-010, R-016,
R-017, R-018, R-019), written by moving their passages out of the phase modules and the plan critic.

enforces: docs/BUILD_PLAN.md TASK-017 (its Done when: the files' form, the points each adds at, the moved passages
gone from their sources, the three splits and the lens bullets word for word, the placement of new text, R-019's
two checks, N7 and N9 in the core); docs/INVENTORY.md, Decisions, the rows of the subject `traits` (the moving rule
and what stays; the plan critic's conditional lenses, R-018's performance lens being satisfied by the plan-side
benchmark lens while the design-side lens stays in plan-critic.md).

The pre-move text is held as constants below, taken from the modules and the plan critic as they stood at the
increment's checkpoint, never read from git history. Supervisor-written; no builder run."""
import os
import re
import subprocess
import sys

import pytest

from phase_modules import read, module, headings, section
from workflow_files import (CORE, EXCEPTIONS, OPEN_LIST, PLAN_CRITIC, TRAIT_PREFIX, TRAITS, WORKFLOW, WORKFLOW_CHECK,
                            flat, trace_check)


def trait(key):
    return read(os.path.join(TRAITS, key + ".md"))


def units(text):
    """The units trace-check.py reads (a paragraph, a list item, a table, a fence), each (normal form, chain)."""
    return [(u["normal"], [t for _l, t in u["chain"]]) for u in trace_check().parse_units(text)[0]]


def entries(kind=None):
    out = []
    for line in read(EXCEPTIONS).split("\n"):
        m = re.match(r"^- (new|reword) (\S+) (\S+\.md) (.+)$", line)
        if m and (kind is None or m.group(1) == kind):
            out.append((m.group(1), m.group(2), m.group(3), m.group(4).strip()))
    return out


# The pre-move text, as trace-check.py's normal form reads it.
DESIGN_PERF_UNIT = "For every **performance or cost budget** the design names the **mechanism** that meets it and the **hot path** it runs on — the index or data structure, caching, batching, streaming, concurrency, where the work happens, what is precomputed (`Performance-Conventions.md` §2). These are the choices that are cheap now and expensive after the build, so they are decided here, and `plan-critic`'s performance lens checks them against the stated data sizes. **Code signing is the one escalation here**: a certificate costs money and identity verification, so present it once as a user-level consequence — unsigned (SmartScreen warns on first run, the manual explains the two clicks) or signed (the owner buys a certificate) — and record the answer."
DESIGN_PERF = "For every **performance or cost budget** the design names the **mechanism** that meets it and the **hot path** it runs on — the index or data structure, caching, batching, streaming, concurrency, where the work happens, what is precomputed (`Performance-Conventions.md` §2). These are the choices that are cheap now and expensive after the build, so they are decided here, and `plan-critic`'s performance lens checks them against the stated data sizes."
DESIGN_SIGNING = '**Code signing is the one escalation here**: a certificate costs money and identity verification, so present it once as a user-level consequence — unsigned (SmartScreen warns on first run, the manual explains the two clicks) or signed (the owner buys a certificate) — and record the answer.'
DESIGN_OBS_UNIT = 'Also for a UI-bearing project, add an **"Observability & Verifiability" section** to `docs/DESIGN.md`, instantiating `~/.claude/cursor-bridge/Observability-Conventions.md` (read it by that absolute path). It records, per Phase-1 inventory state, its **reachability mechanism** (deep-link URL on web; a shared scriptable action path on mobile/desktop; a test-mode-only, prod-compiled-out hook only as a last resort — so your observability driver can reach every state *through the real render path*); the **runtime invariant list** (baseline: no undefined/NaN/`[object Object]`/untranslated-key rendered, `console.error` fails the run, plus project-specific); and the log/test-mode/redaction conventions. **Choose the tier** and record it: Tier A (deterministic assertions + reachability — the default) always; Tier B (screenshots as `design-auditor` evidence) at your discretion for higher-stakes UI. A non-UI project (CLI/ library, no screen-and-state inventory) opts out — note that it did. The driver dependency is the one escalation (see Phase 5).'
DESIGN_OBS_UI = 'Also for a UI-bearing project, add an **"Observability & Verifiability" section** to `docs/DESIGN.md`, instantiating `~/.claude/cursor-bridge/Observability-Conventions.md` (read it by that absolute path). It records, per Phase-1 inventory state, its **reachability mechanism** (deep-link URL on web; a shared scriptable action path on mobile/desktop; a test-mode-only, prod-compiled-out hook only as a last resort — so your observability driver can reach every state *through the real render path*); the **runtime invariant list** (baseline: no undefined/NaN/`[object Object]`/untranslated-key rendered, `console.error` fails the run, plus project-specific); and the log/test-mode/redaction conventions. **Choose the tier** and record it: Tier A (deterministic assertions + reachability — the default) always; Tier B (screenshots as `design-auditor` evidence) at your discretion for higher-stakes UI.'
DESIGN_OBS_REST = 'A non-UI project (CLI/ library, no screen-and-state inventory) opts out — note that it did. The driver dependency is the one escalation (see Phase 5).'
STEP2_UNIT = 'Delegate to **spec-packager** to write `handoff/TASK-<nnn>.md`. The brief must be self-contained — Cursor gets no conversation history, only this file. For a UI-bearing increment, the brief must name the exact approved mockup file(s) and the relevant `docs/design/DESIGN.md` sections, and list the frozen `vercel-interface.mdc` as an applicable rule. Every brief carries the Workspace boundary and the standing invitation to note tooling friction in `docs/BUILDER_NOTES.md` (spec-packager\'s constraints template). spec-packager\'s **reality check** runs first: the schema, configuration, data, and interfaces the increment assumes must exist in the codebase *as built*; "approved in the plan" is not "fits the data" (KP-019). A mismatch comes back to you as a scope question, not as a brief. Once the brief is written, `python ~/.claude/cursor-bridge/plan-check.py` compares it with its increment: a Scope path outside the increment\'s Scope or a requirement the increment satisfies that the brief does not name is a `BRIEF` failure, fixed in the brief before the checkpoint commit (release A4: a brief once silently dropped planned work).'
STEP2_HEAD = 'Delegate to **spec-packager** to write `handoff/TASK-<nnn>.md`. The brief must be self-contained — Cursor gets no conversation history, only this file.'
STEP2_UI = 'For a UI-bearing increment, the brief must name the exact approved mockup file(s) and the relevant `docs/design/DESIGN.md` sections, and list the frozen `vercel-interface.mdc` as an applicable rule.'
STEP2_TAIL = 'Every brief carries the Workspace boundary and the standing invitation to note tooling friction in `docs/BUILDER_NOTES.md` (spec-packager\'s constraints template). spec-packager\'s **reality check** runs first: the schema, configuration, data, and interfaces the increment assumes must exist in the codebase *as built*; "approved in the plan" is not "fits the data" (KP-019). A mismatch comes back to you as a scope question, not as a brief. Once the brief is written, `python ~/.claude/cursor-bridge/plan-check.py` compares it with its increment: a Scope path outside the increment\'s Scope or a requirement the increment satisfies that the brief does not name is a `BRIEF` failure, fixed in the brief before the checkpoint commit (release A4: a brief once silently dropped planned work).'
LENS_PACK = '- **Packaging stage (installable software: desktop application, command-line tool, local server).** Is the last stage "Packaging & installer", and does it carry `Delivery-Conventions.md` §2 / §3 / §4 as checkable acceptance criteria — one-command build or install, committed installer or install script, per-user install registered in Apps & features (a CLI on PATH from an isolated environment built from the lock file), upgrade in place keeping data, Upgrade / Uninstall / Cancel when already installed, uninstall keeping data, the lifecycle verification passing, the manual\'s install chapter? A plan for installable software without it is **Blocking**: the owner cannot install the result.'
LENS_CLI = '- **Command reference (any command-line surface).** Does the increment that first adds a command also add the reference generator (`scripts/dump-cli.py` → `docs/cli-reference.json`) and the CI currency check, and does every later command-changing increment carry "reference regenerated" as a criterion? Without it the supervisor has nothing to look commands up in and will instruct the owner from memory — **Blocking**.'
LENS_EXT = '- **External-service integrations.** For every third-party API, SDK, or provider the software talks to: is the first increment on it a **contract capture** (an attended live call recorded to fixtures, secrets scrubbed) that later increments replay, with "passes against recorded real responses" as the acceptance criterion? An adapter increment whose only evidence is a mock the builder writes is **Blocking**: it tests the builder\'s assumption about the service, not the service (KP-020).'
LENS_BENCH = '- **Benchmark increments (where budgets exist).** Is there a benchmark increment per budget, in the stage where the budgeted operation first exists, so a baseline is committed before any optimization? A budget with no benchmark in the plan is **Blocking**: it can never be checked.'
LENS_DESIGN = '- **Design criteria (UI increments).** Does each UI-bearing increment cite an approved mockup screen and the relevant `docs/design/DESIGN.md` sections, and are its design acceptance criteria actually checkable (a specific observable outcome — "matches mockup screen X", "passes `impeccable detect` with no primary findings") rather than "looks good"?'
LENS_OBS = '- **Observability criteria (UI increments).** Does each increment that adds/changes a screen-state carry checkable observability criteria — the state is driver-reachable through the real render path, its observability test passes (no fired invariant, no `console.error`), the required empty/sparse/dense/error states exist — rather than "renders fine"? Is each state\'s reachability mechanism named in `docs/DESIGN.md`\'s Observability section?'


# Each trait file's `## Add at` headings in file order, and its `###` sub-headings, each with the `## Add at` section it
# stands in. The open list's order of traits is the order their additions apply in; a file's own order is the
# registry's order of points.
POINTS = {
    "has-screens": ["intake.questions", "design.sections", "interface.variants", "planning.acceptance-criteria",
                    "planning.critic-lenses", "configuration.items", "delegation-loop.inspect-checks",
                    "delegation-loop.test-checks", "delegation-loop.brief-constraints"],
    "installable": ["intake.questions", "design.sections", "planning.stages", "planning.critic-lenses",
                    "project-end.delivery for installer", "project-end.delivery for install-script"],
    "performance-budgets": ["intake.questions", "design.sections", "planning.stages", "planning.critic-lenses",
                            "delegation-loop.test-checks"],
    "external-services": ["planning.stages", "planning.critic-lenses", "delegation-loop.inspect-checks",
                          "delegation-loop.test-checks", "delegation-loop.brief-constraints"],
}
SUBSECTIONS = {
    "has-screens": {"The Observability & Verifiability section": "design.sections",
                    "The approved mockup and the frozen rule": "delegation-loop.brief-constraints"},
    "installable": {"Which delivery kinds the intake passage is for": "intake.questions",
                    "Code signing": "design.sections",
                    "Which delivery kinds the Delivery section is for": "design.sections",
                    "Which delivery kinds the packaging stage is for": "planning.stages"},
    "performance-budgets": {"The mechanism and the hot path": "design.sections"},
    "external-services": {},
}
# The `## Add at` sections that hold new text throughout, each under its own `new` entry.
NEW_SECTIONS = {
    "has-screens": {"interface.variants", "planning.critic-lenses"},
    "installable": {"planning.critic-lenses", "project-end.delivery for install-script"},
    "performance-budgets": {"planning.critic-lenses"},
    "external-services": {"planning.critic-lenses", "delegation-loop.inspect-checks", "delegation-loop.test-checks",
                          "delegation-loop.brief-constraints"},
}
# The passages each trait moves, by the start of each moved unit, with the `## Add at` section it now stands in
# directly (under no `###`) and the module it left. The plan critic's lens bullets are listed apart (LENSES).
MOVED = {
    "has-screens": [
        ("intake.questions", "intake", "For every **UI-bearing** feature, capture a **screen-and-state inventory**"),
        ("design.sections", "design", "For a UI-bearing project, record in `docs/INVENTORY.md` (Decisions) whether the stack is"),
        ("planning.acceptance-criteria", "planning", "Each **UI-bearing** increment additionally **cites the approved mockup screen(s)"),
        ("configuration.items", "configuration", "For a UI-bearing project, also work the **design-tooling** steps"),
        ("configuration.items", "configuration", "For a UI-bearing project, also work the **observability** steps"),
        ("delegation-loop.inspect-checks", "delegation-loop", "For a **UI-bearing** diff, also delegate to **design-auditor**"),
        ("delegation-loop.test-checks", "delegation-loop", "For a UI-bearing increment, the tests you write include the **observability tests**"),
    ],
    "installable": [
        ("intake.questions", "intake", "For **installable software** — a desktop application, a command-line tool, a local server"),
        ("design.sections", "design", "For **installable software** it also has a **Delivery** section"),
        ("planning.stages", "planning", "For **installable software** the plan's **last stage is \"Packaging & installer\"**"),
        ("project-end.delivery for installer", "project-end", "- **Deliver the installer** (installable software): run the lifecycle verification one final time"),
    ],
    "performance-budgets": [
        ("intake.questions", "intake", "**Performance and cost budgets** (`~/.claude/cursor-bridge/Performance-Conventions.md` §1)."),
        ("planning.stages", "planning", "For every **budget** the plan carries a **benchmark increment**"),
        ("delegation-loop.test-checks", "delegation-loop", "Where budgets exist and their benchmarks are built, the **benchmark floor**"),
    ],
    "external-services": [
        ("planning.stages", "planning", "For every **external service** the software talks to (a third-party API, SDK, or provider)"),
    ],
}
LENSES = {"has-screens": [LENS_DESIGN, LENS_OBS], "installable": [LENS_PACK, LENS_CLI],
          "performance-budgets": [LENS_BENCH], "external-services": [LENS_EXT]}


def add_heading(point):
    return "Add at " + point


@pytest.mark.parametrize("key", sorted(POINTS))
def test_r016_r019_each_file_is_a_title_and_add_at_sections_with_unique_sub_headings(key):
    """BUILD_PLAN TASK-017: one `#` title, then `## Add at <point key>` sections, nothing between them but the `###`
    sub-headings inside a named section, each `###` heading unique within its file and in the section named for it."""
    text = trait(key)
    hs = headings(text)
    assert hs[0][0] == 1, hs[0]
    assert [t for lv, t in hs if lv == 1] == [hs[0][1]]
    assert [t for lv, t in hs if lv == 2] == [add_heading(p) for p in POINTS[key]], key
    assert all(lv in (1, 2, 3) for lv, _t in hs), hs
    subs = [t for lv, t in hs if lv == 3]
    assert len(subs) == len(set(subs)) and set(subs) == set(SUBSECTIONS[key]), subs
    current = None
    for lv, t in hs:
        if lv == 2:
            current = t
        elif lv == 3:
            assert current == add_heading(SUBSECTIONS[key][t]), (t, current)
    title_line, rest = text.split("\n", 1)
    assert rest.lstrip("\n").startswith("## Add at "), "nothing between the title and the first section"


def test_r016_r019_workflow_check_passes_over_the_workflow_folder():
    """BUILD_PLAN TASK-017: `workflow-check.py` passes over `workflow/` with the four files written (each adds only, at
    points of the registry; the delivery additions name their kinds)."""
    r = subprocess.run([sys.executable, WORKFLOW_CHECK, WORKFLOW], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "RESULT: OK" in r.stdout, r.stdout


def test_r016_r019_the_four_rows_are_written_in_the_open_list():
    """BUILD_PLAN TASK-017: the four rows flip to written in the same change as their files (the open list's step 3)."""
    text = read(OPEN_LIST)
    for key in POINTS:
        rows = [l for l in text.split("\n") if l.startswith("| %s |" % key)]
        assert len(rows) == 1 and rows[0].rstrip().endswith("| yes | release B |"), rows


@pytest.mark.parametrize("key", sorted(POINTS))
def test_r016_r019_each_section_is_moved_units_with_new_text_only_under_a_following_sub_heading(key):
    """BUILD_PLAN TASK-017, "Placement" and "Units and the trace check": a section holds moved units, with new text
    only under a `###` standing after them, or new text throughout under its own `new` entry; every `###` holds new
    text only and has its own `new` entry; no other section of the file is excused (a moved unit under an excused
    heading would leave the copy check). trace-check.py reads the units."""
    rel = TRAIT_PREFIX + key + ".md"
    excused = {h for kind, _id, f, h in entries("new") if f == rel}
    assert {h for kind, _id, f, h in entries() if f == rel} == excused, "trait files take `new` entries only"
    expected = {add_heading(p) for p in NEW_SECTIONS[key]} | set(SUBSECTIONS[key])
    assert excused == expected, sorted(excused ^ expected)
    moved_starts = {(add_heading(p), start) for p, _m, start in MOVED[key]}
    seen = set()
    for normal, chain in units(trait(key)):
        assert len(chain) >= 2 and chain[1].startswith("Add at "), (normal[:60], chain)
        under_sub = len(chain) == 3
        if chain[1] in excused or under_sub:
            assert under_sub or chain[1] in excused
            assert not any(normal.startswith(s) for _h, s in moved_starts), ("a moved unit under an excused heading", normal[:60])
        else:
            hits = [(h, s) for h, s in moved_starts if h == chain[1] and normal.startswith(s)]
            assert len(hits) == 1, ("a unit in a section of moved units that is not one of them", chain[1], normal[:60])
            seen.add(hits[0])
    assert seen == moved_starts, sorted(moved_starts - seen)


@pytest.mark.parametrize("key", sorted(POINTS))
def test_r016_r019_the_sources_no_longer_hold_the_moved_passages(key):
    """BUILD_PLAN TASK-017: a passage is moved, never copied: each moved unit's module no longer holds it, the plan
    critic no longer holds the lens bullets, and no other phase module holds either."""
    for _p, mod, start in MOVED[key]:
        assert start not in flat(module(mod)), (mod, start)
    phases = []
    for root, _dirs, names in os.walk(os.path.join(WORKFLOW, "phases")):
        phases += [os.path.join(root, f) for f in names if f.endswith(".md")]
    assert len(phases) >= 10, phases
    for path in phases:
        t = flat(read(path))
        for _p, _mod, start in MOVED[key]:
            assert start not in t, (path, start)
        for lens in LENSES.get(key, []):
            assert lens[:80] not in t, (path, lens[:80])
    pc = flat(read(PLAN_CRITIC))
    for lens in LENSES[key]:
        assert lens[:80] not in pc, lens[:80]


@pytest.mark.parametrize("key", sorted(LENSES))
def test_r016_r019_the_lens_sections_equal_the_bullets_the_plan_critic_lost(key):
    """BUILD_PLAN TASK-017: the `## Add at planning.critic-lenses` section holds the bullets moved from
    bridge/agents/plan-critic.md word for word, in their order there (the trace check does not read the plan critic)."""
    body = section(trait(key), add_heading("planning.critic-lenses"), 2)
    assert [n for n, _c in units(body)] == LENSES[key]


def test_r017_r018_design_s_performance_and_code_signing_paragraph_is_split_at_the_sentence():
    """BUILD_PLAN TASK-017: design.md's paragraph leaves whole: its first two sentences to performance budgets and its
    code-signing sentence to installable, each under its `###`; put back in the paragraph's sentence order they are
    the paragraph as trace-check.py reads it; design.md keeps no part of it."""
    assert DESIGN_PERF + " " + DESIGN_SIGNING == DESIGN_PERF_UNIT
    assert [n for n, _c in units(section(trait("performance-budgets"), "The mechanism and the hot path", 3))] == [DESIGN_PERF]
    assert [n for n, _c in units(section(trait("installable"), "Code signing", 3))] == [DESIGN_SIGNING]
    d = flat(module("design"))
    assert DESIGN_PERF[:60] not in d and DESIGN_SIGNING[:60] not in d


def test_r016_design_s_observability_paragraph_is_split_its_remainder_reworded():
    """BUILD_PLAN TASK-017: the paragraph's UI sentences go to has screens under their `###`, and equal the unit's
    sentences up to the cut; the closing sentences stay in design.md, reworded to name what they opt out of, under a
    `####` of their own placed directly before `### The delivery kind`; the pre-move remainder is held as a constant."""
    assert DESIGN_OBS_UI + " " + DESIGN_OBS_REST == DESIGN_OBS_UNIT
    assert DESIGN_OBS_UNIT.startswith(DESIGN_OBS_UI)
    body = section(trait("has-screens"), "The Observability & Verifiability section", 3)
    assert [n for n, _c in units(body)] == [DESIGN_OBS_UI]
    text = module("design")
    hs = headings(text)
    at = hs.index((4, "A part without screens"))
    assert hs[at + 1] == (3, "The delivery kind")
    remainder = [n for n, c in units(text) if c[-1:] == ["A part without screens"]]
    assert len(remainder) == 1 and remainder[0] != DESIGN_OBS_REST
    assert "*has screens*" in remainder[0] and "Observability & Verifiability" in remainder[0]
    assert DESIGN_OBS_REST[:40] not in flat(text)


def test_r016_step_2_s_brief_paragraph_is_split_at_its_ui_bearing_sentence():
    """BUILD_PLAN TASK-017: step 2's UI-bearing sentence (the mockup files, the DESIGN.md sections and the frozen rule)
    goes to has screens under its `###`; put back between the remainder's first two sentences and its rest, it gives
    the paragraph as trace-check.py reads it; the step's section holds the remainder alone, under its `new` entry."""
    assert STEP2_HEAD + " " + STEP2_UI + " " + STEP2_TAIL == STEP2_UNIT
    body = section(trait("has-screens"), "The approved mockup and the frozen rule", 3)
    assert [n for n, _c in units(body)] == [STEP2_UI]
    step2 = section(module("delegation-loop"), "2. Package the brief", 3)
    assert [n for n, _c in units(step2)] == [STEP2_HEAD + " " + STEP2_TAIL]
    assert ("new", "TASK-017", "bridge/cursor-bridge/workflow/phases/delegation-loop.md", "2. Package the brief") in entries()
    assert ("reword", "TASK-017", "bridge/commands/supervisor.md", "2. Package the brief") in entries()


def test_r010_r016_has_screens_activates_the_mockups_and_gathers_the_interface_s_build_conditions():
    """R-010, R-016: has screens adds (activates) the mockup variant at `interface.variants`, an addition and never a
    replacement, and gathers the frozen interface rules (the brief), the design auditor (the inspect step) and the
    running-interface tests (the test step); it points at N7 and N9, which stay in the core."""
    text = trait("has-screens")
    variants = flat(section(text, add_heading("interface.variants"), 2))
    assert "`~/.claude/cursor-bridge/workflow/phases/interface/mockups.md`" in variants
    assert "never a replacement" in variants and "N7" in variants and "N9" in variants
    assert "vercel-interface.mdc" in flat(section(text, add_heading("delegation-loop.brief-constraints"), 2))
    assert "**design-auditor**" in flat(section(text, add_heading("delegation-loop.inspect-checks"), 2))
    assert "**observability tests**" in flat(section(text, add_heading("delegation-loop.test-checks"), 2))


def test_r019_the_two_checks_exist_only_in_external_services():
    """R-019, the plan's P11: the bounded remote wait (a brief constraint and an inspect check) and the deployed layout
    tested before any deployment (a test check) are external services' new text, held nowhere else; the inspect check
    names its reviewer and retries only a call that may run twice, the brief names a zero limit for one that may not,
    and the layout test is for an increment that deploys or prepares a deployment (Review A, TASK-017 round 1)."""
    text = trait("external-services")
    inspect = flat(section(text, add_heading("delegation-loop.inspect-checks"), 2))
    assert "is bounded" in inspect and "`diff-reviewer` checks" in inspect and "where it retries, a bounded retry" in inspect
    assert "must not run twice" in inspect and "is not retried" in inspect
    brief = flat(section(text, add_heading("delegation-loop.brief-constraints"), 2))
    assert "is bounded" in brief and "the limit zero for a call that must not run twice" in brief
    layout = flat(section(text, add_heading("delegation-loop.test-checks"), 2))
    assert "the deployed layout is tested before any deployment" in layout and "deploys the part or prepares" in layout
    others = [CORE, PLAN_CRITIC]
    for root, _dirs, files in os.walk(WORKFLOW):
        others += [os.path.join(root, f) for f in files if f.endswith(".md") and f != "external-services.md"]
    for path in others:
        t = flat(read(path))
        assert "the deployed layout is tested" not in t and "Every remote wait the increment adds is bounded" not in t, path
        assert "Every wait on a remote service in the diff is bounded" not in t, path


def test_r017_installable_s_new_sentences_name_their_kinds():
    """BUILD_PLAN TASK-017: each scoping sentence names the kinds `installer` and `install-script` and what a part of
    another kind does; the packaging stage's names the `n/a` pass-over; the install-script delivery names the project's
    `install-check.ps1` and no dialog (the registry: an addition at project-end.delivery reaches only its kind)."""
    text = trait("installable")
    for title, other in (("Which delivery kinds the intake passage is for", "takes its delivery questions from its type workflow"),
                         ("Which delivery kinds the Delivery section is for", "records its kind's delivery as its type workflow says"),
                         ("Which delivery kinds the packaging stage is for", "takes the packaging stage its type workflow adds")):
        body = flat(section(text, title, 3))
        assert "`installer`" in body and "`install-script`" in body and other in body, title
    assert "`Installer verification` answer of `n/a` passes the lifecycle check over" in flat(section(text, "Which delivery kinds the packaging stage is for", 3))
    script = flat(section(text, add_heading("project-end.delivery for install-script"), 2))
    assert "`install-check.ps1` as the lifecycle verification" in script and 'no "already installed" dialog' in script


def test_r016_r019_n7_and_n9_remain_in_the_core():
    """BUILD_PLAN TASK-017: the founding rules the traits point at stay in the core."""
    core = flat(read(CORE))
    assert "N7 Design quality is measured, never asked." in core
    assert "N9 For software with screens the running render is measured." in core


def test_r016_r019_the_plan_critic_keeps_its_design_lenses_and_catches_a_missing_trait():
    """BUILD_PLAN TASK-017; INVENTORY, Decisions (the plan critic's conditional lenses): the design-document performance
    lens stays, since the design critique runs before the traits are settled; one bullet catches each trigger with no
    lens of its own in the plan's critique file. R-018's performance lens is the plan-side benchmark lens, which the
    trait carries (that Decisions row)."""
    pc = flat(read(PLAN_CRITIC))
    assert "**Performance lens (where budgets exist).**" in pc
    assert "is a finding that a trait is missing" in pc
    for trigger, lens in (("`installer` or `install-script`", "no packaging lens"),
                          ("a service run by others (a third-party API, SDK or provider)", "no external-service lens"),
                          ("a design that shows screens", "no design-criteria lens"),
                          ("a design naming a budget", "no benchmark-increments lens")):
        start = pc.index(trigger)
        assert pc[start:pc.index(" lens", start) + 5].endswith(lens), (trigger, lens)


def test_r035_a_plan_critique_carries_the_traits_lenses_and_a_trait_added_at_the_gate_is_asked_and_written():
    """BUILD_PLAN TASK-017: design.md's "Traits at the design gate" says the plan critique's file carries the lenses
    the parts' conditional workflows add, once for the project, and what a trait added at that gate brings in before
    the design is presented again."""
    body = flat(section(module("design"), "Traits at the design gate", 3))
    assert "`planning.critic-lenses`, each once for the project" in body
    for phrase in ("its additions at `intake.questions` asked", "the answers written to the intake notes",
                   "its additions at `design.sections` and `design.mandatory-diagrams` written",
                   "the design and the register revised from the new answers, before the design is presented again"):
        assert phrase in body, phrase
