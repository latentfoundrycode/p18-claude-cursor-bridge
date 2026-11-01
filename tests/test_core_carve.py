"""TASK-010: the core and its phase modules (R-003, R-032).

enforces: docs/REQUIREMENTS.md R-003 (the core holds the roles and division of labour, the founding rules, the loop's
shape, escalation and reporting, project state and the standing rules; each phase's procedure is a module) and R-032
(each module is read whole: within 1,500 lines and 60,000 characters); docs/BUILD_PLAN.md TASK-010's Done when (the
core's section set, no phase procedure left in it, the modules exist, workflow/** installs from the regenerated
manifest)."""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")
REGISTRY = os.path.join(BRIDGE, "cursor-bridge", "workflow", "extension-points.md")
INSTALL = os.path.join(BRIDGE, "cursor-bridge", "bridge-install.py")

# each module and the heading it opens with: the phase's own heading from the core, kept (project end has its own,
# and the interface module names the phase since TASK-012 made its mockups one of four variants)
MODULES = {
    "intake": "## Phase 1 — Intake",
    "design": "## Phase 2 — Design",
    "interface": "## Phase 3 — Interface",
    "planning": "## Phase 4 — Build plan",
    "run-parameters": "## Run parameters — asked once, after the plan is approved, before configuration",
    "configuration": "## Phase 5 — Configure the Cursor build environment",
    "delegation-loop": "## Phase 6 — The delegation loop",
    "change-cycle": "## The change cycle — a request on a finished project",
    "reflection": "## Reflection points — stage close, phase gates, project end",
    "project-end": "## Project end",
}
CORE_SECTIONS = [
    "The core, in brief", "Founding rules", "The division of labour", "Main and conditional workflows",
    "The project layout", "The phase modules", "Objections — bottom-up escalation", "Escalate to the user when",
    "Reporting to the user", "Project state", "Standing rules",
]


def read(path):
    return open(path, encoding="utf-8").read().replace("\r\n", "\n")


def headings(text, level):
    """The headings of one level outside fenced blocks, in order."""
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
            h = re.match(r"^ {0,3}(#{1,6}) (.*)$", line)
            if h and len(h.group(1)) == level:
                out.append(h.group(2).strip())
    return out


def test_r003_the_core_holds_exactly_its_sections():
    assert headings(read(CORE), 2) == CORE_SECTIONS


def test_r003_no_phase_procedure_remains_in_the_core():
    core = read(CORE)
    for heading in MODULES.values():
        assert heading not in core.split("\n"), heading
    for step in ("### 1. Checkpoint", "### 8. Merge (the verified gate)", "### Step 0 — Prior-project lessons (ask before drafting)",
                 "### The design-tooling flow", "### Issues — what counts, and where it is written"):
        assert step not in core.split("\n"), step
    assert "**Project end is a defined trigger, not a judgement.**" not in core
    assert "**At project end**, additionally:" not in core


def test_r003_the_modules_are_the_registrys_and_each_opens_with_its_heading():
    registry = read(REGISTRY)
    table = registry.split("\n## Phase modules\n", 1)[1].split("\n## ", 1)[0]
    keys = [row.split("|")[1].strip() for row in table.split("\n") if row.startswith("| ") and not row.startswith("| Module")]
    assert keys == list(MODULES), keys
    assert sorted(f for f in os.listdir(PHASES) if f.endswith(".md")) == sorted(k + ".md" for k in MODULES)
    for key, heading in MODULES.items():
        assert read(os.path.join(PHASES, key + ".md")).split("\n", 1)[0] == heading, key


def test_r003_the_core_names_every_module():
    core = read(CORE)
    section = core.split("\n## The phase modules\n", 1)[1].split("\n## ", 1)[0]
    for key in MODULES:
        assert "`~/.claude/cursor-bridge/workflow/phases/%s.md`" % key in section, key


def test_r003_project_end_is_carved_out_of_the_reflection_points():
    reflection = read(os.path.join(PHASES, "reflection.md"))
    project_end = read(os.path.join(PHASES, "project-end.md"))
    assert "**Project end is a defined trigger, not a judgement.**" in project_end
    assert "**At project end**, additionally:" in project_end and "- **Run the promotion pass.**" in project_end
    assert "**Project end is a defined trigger" not in reflection and "**At project end**" not in reflection
    assert "`~/.claude/cursor-bridge/workflow/phases/project-end.md`" in reflection
    assert "### Issues — what counts, and where it is written" in reflection.split("\n")


def test_r003_a_module_read_outside_its_own_phase_is_named_with_when():
    """PR #52's gate (Review A, the carve's part, blocking): before the carve every procedure was in the one file read
    whole; after it a reader reads the current phase's modules and "never a phase you are not in". The procedures that
    run outside their own Phase: value (reflection points at every phase gate, an issue in any phase, project end, the
    change cycle's scaled Phases 1 to 4) are named in the core with when they are read."""
    core = read(CORE)
    section = core.split("\n## The phase modules\n", 1)[1].split("\n## ", 1)[0]
    rule = section.split("**Modules read outside their own phase.**", 1)[1]
    assert "`reflection.md` is read whole at every reflection point: a stage close, each approved phase gate, and project end;" in rule
    assert "its section \"Issues — what counts, and where it is written\" is read whenever an issue is detected, in any phase;" in rule
    assert "`project-end.md` is read whole at the close of the plan's last stage;" in rule
    assert ("reads that phase's module whole for that step: the change cycle runs Phases 1 to 4, scaled; the design "
            "critique's failed launch follows the delegation loop's step 3b, and its review launch follows step 8.") in rule
    assert ("You never read a phase you are not in or a conditional workflow that does not apply, except a module "
            "\"The phase modules\" says is read outside its own phase.") in core
    layering = core.split("\n## Main and conditional workflows\n", 1)[1].split("\n## ", 1)[0]
    assert ("on entering the phase and at every calibration; a module read outside its own phase when \"The phase "
            "modules\" says |") in layering


# the traceability check's result on this tree, every excuse it uses named (PR #52's gate, Review A, the carve's part:
# a reword entry excuses a whole section, so a later drop there would show only as a NOTE with RESULT: OK)
# (TASK-012: three passages move from traced to excused: the design gate's sentence, "the UI mockups" -> "the
# interface phase"; the mockup paragraph's "Saving these concludes the planning stage", now the mockups and the phase;
# rule 13's pointer to the approved-mockup rule, excused by the earlier Standing rules entry and so labelled TASK-015;
# the other mockup passages traced in their new home, workflow/phases/interface/mockups.md)
# (TASK-014: two more move from traced to excused: the change cycle's item 3, the UI mockups -> the interface
# variants of every kind the change touches, and its closing sentence on the gates, "the mockup if any" -> "the
# artifact of each interface variant the change runs"; and, for Review B's should-fix, its step 7, project end now run
# by project-end.md, scaled; and, for Review B's round 3, rule 34, which stated the same procedure, excused by the
# earlier Standing rules entry and so labelled TASK-015)
# (TASK-017: three passages move from traced to excused, each split at the sentence between two homes: design's
# performance-mechanism and code-signing paragraph and its Observability & Verifiability paragraph, under the
# standing TASK-012 entry on "Phase 2 \u2014 Design", and step 2's brief paragraph, under TASK-017's own entry on
# "2. Package the brief"; every other passage the trait files take moves whole and is traced in its new home)
# (TASK-030: four more move from traced to excused: step 3's timeout paragraph and step 4's tests paragraph,
# reworded under TASK-030's own entries on "3. Delegate to Cursor" and "4. Inspect" (the heavy launch's duration;
# every suite through the launcher; the mutants file and the checkpoint run through mutation-run.py), and rules 8
# and 24, excused by the earlier Standing rules entry and so labelled TASK-015 (the driver kind; the suite's
# default), and in round 2 rule 43 the same way (a mutation run a wake source); step 7 moves whole into
# delegation-loop/decide.md and is traced there)
# (TASK-035: seven more move from traced to excused, six under TASK-035's own `reword` entries: the founding rules'
# "Every procedure in this file" and the layout's "every path below", which now name the modules; planning's
# project-end pointer, run-parameters' escalation-list pointer and the refactoring pass's project-end sentence,
# each with its `new` entry in its module; the status template's `Deferred increments:` field; and the change
# cycle's item 1, whose closing confirmation is not a gate, under the standing TASK-014 entry. Rule 34 stays
# labelled TASK-015: the check names the first entry that matches a passage, and the TASK-014 entry TASK-035 adds
# beside it records that increment's reword of rule 34 without relabelling rules 8, 13, 24, 28 and 43)
# (TASK-034: twenty-four more move from traced to excused, under TASK-034's own `reword` entries but where an
# earlier entry matches first: the digest's four paragraphs (the role's "package briefs" -> "brief"; N1's
# "touches no data it does not own" -> "touches only its own data" and "never runs" -> "runs no"; step 3's
# "with the constant command" -> "by"; step 4's "list copied, then dispositioned" -> "list dispositioned" (the
# copy stays in rule 42 and step 4); step 7's "re-delegates with a corrected brief" -> "by a new numbered
# brief"; step 8's names `<ID>-r<N>` and "the diff committed to `run/review/`" -> "the diff and its SCOPE file
# committed"; step 9's "on a `stage/<name>` branch" -> "(`stage/<name>`)"; rule 6 in short; rule 43's
# "a builder run, Review B, the CI watch, a `# wake` command or an agent" -> "a builder, Review B, CI watch or
# `# wake` run, or an agent"; rule 48's "The session's model" -> "The model", "through Phase 4" -> "to
# Phase 4" and "told at the stage close before" -> "told a stage close ahead"; rule 55's "(design, brief,
# conformance check)" dropped), trimmed to keep the digest within its cap; step 3b's exception
# for the review ceiling's refusals; step 7's Iterate and Re-delegate bullets, its root-cause-first paragraph and
# its by-class bullet; step 8's Review B item, both convergence paragraphs and the merge paragraph's names; the
# stage review's steps 2 to 7; and, labelled by the earlier entries, step 3's brief paragraph (TASK-030), the run
# parameters' fence and its optional-lines paragraph (TASK-035) and rules 6 and 42 (TASK-015))
# (BUG-031: two more move from traced to excused, under BUG-031's own `reword` entries but labelled by the earlier
# entries that match first: the refactoring pass's step 6, whose title now names its REFAC-<nnn> brief IDs
# (TASK-035), and rule 39, which retires step 4's old-<nnn> worktree (TASK-015))
TRACED = "TRACED: 424 passages of baseline 0a186da; 139 in supervisor.md, 222 under workflow/, 0 dropped, 63 excused"
NOTES = [
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: The core, in brief - **Role.** The supervising architect: design, plan, package b",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: The core, in brief - **Founding rules.** N1 The loop's truth lives in files; one-",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: The core, in brief - **The loop (Phase 6, one increment).** 1 Checkpoint: clean t",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: The core, in brief - **Standing rules.** 1 Never write implementation code. 2 Nev",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: Founding rules - These nine rules are the bridge's constitution. Every proced",
    "NOTE (reword TASK-010) bridge/commands/supervisor.md: Main and conditional workflows - | Layer | Holds | Read when | |---|---|---| | **The main wor",
    "NOTE (reword TASK-010) bridge/commands/supervisor.md: Main and conditional workflows - Until the phases are moved into files of their own, each pha",
    "NOTE (reword TASK-010) bridge/commands/supervisor.md: Main and conditional workflows - **The order additions apply in.** Additions from several con",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: The project layout - You work in `Workspace/`; `Documents/` is its sibling (`../D",
    "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - For every **performance or cost budget** the design names th",
    "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - It answers in the critic's grades (Blocking, Should fix, Con",
    "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - **The loop stops by what was found, and after four rounds at",
    "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - `docs/DESIGN_CRITIQUE.md` has three parts, one block per sub",
    "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - Also for a UI-bearing project, add an **\"Observability & Ver",
    "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - **Gate:** present the design to the user. Do not proceed to ",
    "NOTE (reword TASK-012) bridge/commands/supervisor.md: The design-tooling flow - Save the mockup files under `docs/mockups/` (one file per sc",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: The plan - Give each one an ID (`TASK-001`, `TASK-002`, \\u2026). Group the i",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: Run parameters \\u2014 asked once, after the plan is approved, before configuration - - `run` *(default)* \\u2014 report the stage close as a notificati",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: Run parameters \\u2014 asked once, after the plan is approved, before configuration - 5. **Parallel increments** \\u2014 whether independent increments ",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: Run parameters \\u2014 asked once, after the plan is approved, before configuration - - `on` \\u2014 ready independent increments are built at once, eac",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: Run parameters \\u2014 asked once, after the plan is approved, before configuration - ```markdown\\x0a# Run parameters\\x0aSet: <date>   (owner may change",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: Run parameters \\u2014 asked once, after the plan is approved, before configuration - Three optional lines are never asked and are written only on",
    "NOTE (reword TASK-017) bridge/commands/supervisor.md: 2. Package the brief - Delegate to **spec-packager** to write `handoff/TASK-<nnn>.m",
    "NOTE (reword TASK-030) bridge/commands/supervisor.md: 3. Delegate to Cursor - The `--model` value is copied from `docs/ROSTER.resolved.jso",
    "NOTE (reword TASK-030) bridge/commands/supervisor.md: 3. Delegate to Cursor - - **The brief carries the constraints \\u2014 the command line car",
    "NOTE (reword TASK-030) bridge/commands/supervisor.md: 3. Delegate to Cursor - **Parallel increments** (only when `docs/RUN_PARAMETERS.md` ",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: 3b. A model fails mid-step \\u2014 switch automatically, restart the step, never wait - (The one exception: every exit 125 whose message begins `bri",
    "NOTE (reword TASK-030) bridge/commands/supervisor.md: 4. Inspect - **The tests run before the first reviewer** (release A5, pla",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: 7. Decide (accept the increment) - - **Iterate** \\u2014 something is wrong and you understand why. R",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: 7. Decide (accept the increment) - - **Re-delegate on a review REJECT** \\u2014 if a reviewer rejects",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: 7. Decide (accept the increment) - **Diagnose before you re-delegate a defect \\u2014 the `root-cause",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: 7. Decide (accept the increment) - - **Draw a by-class line once the core is correct.** When th",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: 8. Merge (the verified gate) - 3. **Review B** \\u2014 a **cross-family**, non-Anthropic verifier",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: 8. Merge (the verified gate) - **Convergence is a signal.** When two or more reviewers or a",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: 8. Merge (the verified gate) - A `REJECT` from either reviewer goes back through re-delegat",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: 8. Merge (the verified gate) - When all four hold the merge is authorised. A pull request t",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: 9. Refactoring and optimization pass (at stage close) - 4. **One branch, many small commits.** Cut `refactor/<stage>",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: 9. Refactoring and optimization pass (at stage close) - 6. **One gate pass.** The whole branch goes through step 8 o",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: 9. Refactoring and optimization pass (at stage close) - The pass never escalates. It never introduces an abstraction",
    "NOTE (reword TASK-014) bridge/commands/supervisor.md: The change cycle \\u2014 a request on a finished project - 1. **Intake of the change** (Phase 1, scaled). The session i",
    "NOTE (reword TASK-014) bridge/commands/supervisor.md: The change cycle \\u2014 a request on a finished project - 2. **Design revision** (Phase 2, scaled). Append a dated **C",
    "NOTE (reword TASK-014) bridge/commands/supervisor.md: The change cycle \\u2014 a request on a finished project - 3. **UI mockups** (Phase 3) **only if the change touches the",
    "NOTE (reword TASK-014) bridge/commands/supervisor.md: The change cycle \\u2014 a request on a finished project - 7. **Project end again.** The close of the addendum's last s",
    "NOTE (reword TASK-014) bridge/commands/supervisor.md: The change cycle \\u2014 a request on a finished project - The gates of a change cycle are the same approvals the origi",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: Reflection points \\u2014 stage close, phase gates, project end - 2. Write the stage's whole change from committed state: `git",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: Reflection points \\u2014 stage close, phase gates, project end - 3. `python ~/.claude/cursor-bridge/review-guard.py snapshot ",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: Reflection points \\u2014 stage close, phase gates, project end - 4. Review A: `diff-reviewer` on `run/review/STAGE-<name>.dif",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: Reflection points \\u2014 stage close, phase gates, project end - 5. Review B in the background, with execution, exactly as st",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: Reflection points \\u2014 stage close, phase gates, project end - 6. `python ~/.claude/cursor-bridge/review-guard.py verify ST",
    "NOTE (reword TASK-034) bridge/commands/supervisor.md: Reflection points \\u2014 stage close, phase gates, project end - 7. A REJECT from either reviewer: do step 8 first (back on `",
    "NOTE (reword TASK-035) bridge/commands/supervisor.md: Project state - ```markdown\\x0a# Project Status\\x0aLast updated: <timestamp>\\x0aPhase",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 6. Judge re-delegation by defect class, not a round count. N",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 8. Never chain shell commands with `&&`, `|`, or `;`, and ne",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 12. Every report to the user leads with the one decision the",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 13. Design correctness \\u2014 accessibility and interface MUSTs, ",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 24. Windowless by default. The user works on the same Window",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 28. The installed bridge is the governing text, and its vers",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 34. A request on a finished project is a change cycle: the s",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 39. Sequential work is branches in one checkout, never a wor",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 42. Every builder run ends with an `Assumed, not verified` l",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 43. Never end a turn while the loop has work unless somethin",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 46. The build plan is explicit. Every increment states its p",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 48. **The session's model follows the phase, and the switch ",
]


def test_r003_the_carve_traces_with_exactly_its_excuses():
    """The traceability check (R-029) on the repository: every passage of the baseline traced, none dropped, and the
    excused ones exactly the sixty-three passages of the `reword` entries the carve (TASK-010), TASK-012, TASK-014,
    TASK-015, TASK-017, TASK-030, TASK-034, TASK-035 and BUG-031 declare (three in the core's "Main and conditional workflows", six
    standing rules, three under "Phase 2 \u2014 Design" (the design gate and the two paragraphs TASK-017 splits),
    one in the design-tooling flow, four in the change cycle, one each in steps 2, 3, 4 and 9, and one each in the
    founding rules, the layout, the plan, the run parameters and the status template, and TASK-034's twenty-four: the
    digest's four paragraphs, step 3b's exception, four in step 7, four in step 8, six in the stage review, two
    more in the run parameters, rules 6 and 42, and step 3's brief paragraph; BUG-031's two: the refactoring
    pass's step 6 and rule 39; and five passages BUG-033 reworded, which those entries excuse: the refactoring
    pass's step 4 and the run parameters' Parallel increments item and its `on` option, under TASK-035's, step 3's
    Parallel increments paragraph, under TASK-030's, and rule 46, under TASK-015's; and six passages TASK-037 reworded, which those entries excuse: three under "Phase 2 \u2014 Design" (the critique's round paragraph, its stop rule and its record), the change cycle's item 2, and rules 12 and 48, under TASK-012's, TASK-014's and TASK-015's), so an increment that excuses anything more changes this test. It
    needs the baseline commit, which CI's depth-1 checkout lacks (INVENTORY Decisions): skipped there, run in
    the supervisor's checkout."""
    repo = os.path.abspath(os.path.join(HERE, os.pardir))
    have = subprocess.run(["git", "cat-file", "-e", "0a186da^{commit}"], cwd=repo, capture_output=True)
    if have.returncode != 0:
        import pytest
        pytest.skip("the baseline commit is not in this clone (a shallow checkout)")
    p = subprocess.run([sys.executable, os.path.join(BRIDGE, "cursor-bridge", "trace-check.py")], cwd=repo,
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stdout + p.stderr
    lines = p.stdout.strip().split("\n")
    assert lines == NOTES + [TRACED, "RESULT: OK"], p.stdout


def test_r032_each_module_is_read_whole():
    for key in MODULES:
        text = read(os.path.join(PHASES, key + ".md"))
        assert text.count("\n") <= 1500 and len(text) <= 60000, (key, text.count("\n"), len(text))


def test_r003_the_modules_install_from_the_manifest(tmp_path):
    """The proof that workflow/** installs with no change to bridge-install.py: the regenerated manifest lists every
    module, and an install into an empty target writes each one as it is in the source."""
    manifest = json.load(open(os.path.join(BRIDGE, "cursor-bridge", "MANIFEST.json"), encoding="utf-8"))
    listed = json.dumps(manifest)
    for key in MODULES:
        assert "cursor-bridge/workflow/phases/%s.md" % key in listed, key
    target = tmp_path / ".claude"
    env = dict(os.environ)
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    p = subprocess.run([sys.executable, INSTALL, "--target", str(target), "--anyway"], capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stdout + p.stderr
    for key in MODULES:
        installed = target / "cursor-bridge" / "workflow" / "phases" / (key + ".md")
        assert installed.is_file(), key
        assert read(str(installed)) == read(os.path.join(PHASES, key + ".md")), key
