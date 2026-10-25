"""TASK-021: the type workflow host extension and its sub-workflow Claude Code extension (R-025), new text throughout.

enforces: docs/BUILD_PLAN.md TASK-021 (its Done when: the type adds the host's behaviour as verified facts with the
version checked, tests inside the real host, and sets `intake.delivery-kind` to `host-installation`, with the kind's
procedure at `project-end.delivery for host-installation`; every section new text under a `new` entry; both rows written;
`workflow-check.py` passing and classifying the bridge itself from a committed fixture without pausing);
bridge/cursor-bridge/workflow/extension-points.md (the points' kinds of change, the delivery kinds, a procedure applying
only to its own kind); bridge/cursor-bridge/workflow/open-list.md, "Default traits" (the open list is the one source of a
type's and a sub-type's default traits). Supervisor-written; no builder run."""
import importlib.util
import os
import re

import pytest

from phase_modules import read, section
from workflow_files import (CORE, PHASES, REGISTRY, TRAITS, TYPES, WORKFLOW, FIXTURES, BRIDGE, REPO, WORKFLOW_CHECK,
                            file_entries, flat, row, run_check, trace_units)

DELIVERY = "Add at project-end.delivery for host-installation"
# Each file's path under workflow/types/, its title and its change headings, in its order (BUILD_PLAN TASK-021).
FILES = {
    "host-extension": ("host-extension.md", "Host extension",
                       ["Set at intake.delivery-kind", "Add at design.sections", "Add at delegation-loop.test-checks",
                        DELIVERY]),
    "claude-code-extension": ("host-extension/claude-code-extension.md", "Claude Code extension",
                              ["Add at design.sections"]),
}


def text(key):
    return read(os.path.join(TYPES, FILES[key][0]))


def body(key, heading):
    return section(text(key), heading, 2)


def registry_row(point):
    got = [l for l in read(REGISTRY).split("\n") if l.startswith("| %s |" % point)]
    assert len(got) == 1, (point, got)
    return [c.strip() for c in got[0].strip().strip("|").split("|")]


@pytest.mark.parametrize("key", sorted(FILES))
def test_r025_each_file_is_a_title_and_its_change_sections_only(key):
    """BUILD_PLAN TASK-021: one `#` title, then the change headings named above, in that order, and nothing else, so
    each file changes the main workflow at those points and no other, and no module is replaced; each point accepts
    the kind of change its heading makes (extension-points.md: `intake.delivery-kind` add and set, the others add)."""
    lines = text(key).split("\n")
    heads = [l for l in lines if re.match(r"^ {0,3}#", l)]
    assert heads == ["# " + FILES[key][1]] + ["## " + h for h in FILES[key][2]], heads
    assert lines[0] == "# " + FILES[key][1], lines[0]
    for h in FILES[key][2]:
        kind, point = re.match(r"^(Set|Add) at (\S+)", h).groups()
        assert kind.lower() in registry_row(point)[4].split(", "), (h, registry_row(point))


def test_r025_the_type_sets_host_installation():
    """BUILD_PLAN TASK-021: the type sets `intake.delivery-kind` to `host-installation`, one key, its section's first
    non-blank line with nothing after it (extension-points.md: the value is the section's first non-blank line); the
    key is one of the registry's delivery kinds and of workflow-check.py's copy of them; a type may set, a trait may
    not (the core's "Main and conditional workflows"), and no trait file sets the kind."""
    lines = [l.strip() for l in body("host-extension", "Set at intake.delivery-kind").split("\n") if l.strip()]
    assert lines == ["host-installation"], lines
    assert "`host-installation` (an extension installed into its host)" in flat(read(REGISTRY))
    spec = importlib.util.spec_from_file_location("workflow_check_type_host_extension", WORKFLOW_CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "host-installation" in mod.DELIVERY_KINDS
    trait_files = [os.path.join(here, f) for here, _dirs, names in os.walk(TRAITS) for f in names]
    assert len(trait_files) >= 7, trait_files
    for here, _dirs, names in os.walk(TRAITS):
        for f in names:
            assert "## Set at" not in read(os.path.join(here, f)), f
    assert "Set at" not in text("claude-code-extension")


def test_r025_the_hosts_behaviour_is_recorded_as_verified_facts_with_the_version_checked():
    """BUILD_PLAN TASK-021: the type adds the host's behaviour as verified facts with the version checked: a design
    section on the host, each behaviour the part relies on recorded with what was checked, how and on which version of
    the host; an unchecked behaviour is an assumption checked before anything is built on it; a fact holds for its
    version and is checked again when the host reports another, a changed fact being a defect or the owner's question."""
    t = flat(body("host-extension", "Add at design.sections"))
    for phrase in [
            "The host's rules are not the project's: the host decides how its extension points behave and changes them "
            "with its updates.",
            "the design gains a section on the host, recording each behaviour of the host's extension points the part "
            "relies on",
            "as a verified fact: what was checked, how it was checked (a probe run in the host, or the host's own "
            "documentation for that version), and the host's version it was checked on.",
            "A behaviour not yet checked is written as an assumption, and the first increment that relies on it checks "
            "it before anything is built on it.",
            "A fact holds for the version it names: when the host the project is built against reports another version, "
            "the facts the part relies on are checked again before the next increment that relies on them",
            "a fact found changed is a defect like any other, or a question for the owner where it changes what the part "
            "can do."]:
        assert phrase in t, phrase


def test_r025_host_behaviour_is_tested_inside_the_real_host_kept_apart_from_the_owners():
    """BUILD_PLAN TASK-021: tests inside the real host, at the version the design records, with the part installed
    into a host kept apart from the owner's own and never into the host the owner works in; the result read from what
    the host did; a behaviour no test can reach there named as untested, never counted as tested; the owner's account or paid usage, where driving the host needs it, put to the owner first."""
    t = flat(body("host-extension", "Add at delegation-loop.test-checks"))
    for phrase in [
            "each behaviour of the part that depends on the host is tested inside the real host, at the version the "
            "design's host section records",
            "with the part installed into a host kept apart from the owner's own (a separate profile, folder or "
            "instance, as the host allows), never into the host the owner works in.",
            "The behaviour is driven there and its result read from what the host did.",
            "A host behaviour no test can reach inside the host is named in the increment's report as untested there, "
            "never counted as tested.",
            "Where driving the host uses the owner's account, that use is put to the owner once, before any test relies "
            "on it, and what it reaches is recorded in `docs/INVENTORY.md` (Decisions)",
            "where it draws paid usage, the part is classified with *spends money* too, and each run that draws it is "
            "a paid action of that trait's, approved for itself and run by the supervisor, never by the builder or in "
            "CI."]:
        assert phrase in t, phrase


def test_r025_the_host_installation_procedure():
    """BUILD_PLAN TASK-021: the kind's procedure at `project-end.delivery for host-installation`: an install program
    the owner runs from a run sheet (it acts outside the repository, rule 27), copying the release, merging into the
    host's settings without changing the owner's entries, keeping what it replaces, ending by checking that the host
    loads the installed version, a clash with the owner's entries put to the owner; a take-back proved once on a host kept apart before the first install; the User
    Manual's first chapter (project-end.md's install chapter for installable software)."""
    t = flat(body("host-extension", DELIVERY))
    for phrase in [
            "the owner's host receives the release through an install program the project ships, which the owner runs "
            "from a run sheet, since it acts outside the repository.",
            "The program copies the release's files into the host's extension folder, merges the part's entries into the "
            "host's settings without changing the owner's own entries (where an entry of the part's and one of the "
            "owner's name the same thing, it stops and puts the clash to the owner), keeps what it replaces so that "
            "the previous release can be put back, and ends by checking that the host loads the installed version",
            "The take-back puts the previous release's files and entries back the same way, and is proved once, on a "
            "host kept apart from the owner's own, before the first release is installed.",
            "The User Manual's first chapter says how to install, update and take back the release, and that the "
            "owner's own settings stay as they were."]:
        assert phrase in t, phrase


def test_r025_the_procedure_reaches_host_installation_parts_only():
    """extension-points.md: each addition at `project-end.delivery` names its kind and applies only to a part of that
    kind; host-installation's procedure is the type's alone, and installable's procedures, for `installer` and
    `install-script`, never reach a host extension, though installable is its default trait."""
    for here, _dirs, names in os.walk(WORKFLOW):
        for f in names:
            if f.endswith(".md") and os.path.normcase(os.path.join(here, f)) != os.path.normcase(
                    os.path.join(TYPES, "host-extension.md")):
                assert "## " + DELIVERY not in read(os.path.join(here, f)), f
    installable = [l for l in read(os.path.join(TRAITS, "installable.md")).split("\n")
                   if l.startswith("## Add at project-end.delivery")]
    assert installable == ["## Add at project-end.delivery for installer",
                           "## Add at project-end.delivery for install-script"], installable
    assert "project-end.delivery" not in text("claude-code-extension")
    assert ("Each addition at `project-end.delivery` names the delivery kind it is for and applies only to a part of that "
            "kind") in flat(read(REGISTRY))


def test_r025_the_sub_workflow_names_claude_codes_extension_points_and_its_version():
    """BUILD_PLAN TASK-021: Claude Code extension adds to the design's host section what is Claude Code's: its
    extension points, the version `claude --version` prints, and the facts that cost most when wrong, checked in Claude
    Code itself; the sub-workflow inherits the type's kind and procedure and sets nothing of its own."""
    t = flat(body("claude-code-extension", "Add at design.sections"))
    for phrase in [
            "The host is Claude Code, and its extension points include its commands, agents, skills, hooks, settings and "
            "permission rules.",
            "The version each fact in the design's host section was checked on is the one `claude --version` prints.",
            "when a hook runs and what its output does (the Stop hook's), and which commands a permission rule matches "
            "(a rule for git that does not match git given a folder with -C)",
            "each such fact is checked in Claude Code itself before the design relies on it.",
            "Such a check runs, as the type's probes do, in a Claude Code kept apart from the owner's own."]:
        assert phrase in t, phrase
    # BUG-021 and stage B4's review, round 2: a probe that checks a fact runs as the tests do, kept apart.
    probe = flat(body("host-extension", "Add at design.sections"))
    assert ("A probe that checks such a fact runs as the tests do, in a host kept apart from the owner's own, and its "
            "use of the owner's account or paid usage is put to the owner as the test step's addition says.") in probe


@pytest.mark.parametrize("key", sorted(FILES))
def test_r025_every_section_has_its_own_new_entry_and_no_other_entry_names_the_file(key):
    """BUILD_PLAN TASK-021: every section of the two files is new text under a `new` entry naming the file and that
    heading (the trace check counts the type files as modules); no `reword` entry, and none on the title."""
    rel = "bridge/cursor-bridge/workflow/types/" + FILES[key][0]
    got = file_entries(rel)
    assert got == [("new", "TASK-021", h) for h in FILES[key][2]], got


@pytest.mark.parametrize("key", sorted(FILES))
def test_r025_the_text_is_new_and_copies_no_passage_of_the_main_workflow(key):
    """BUILD_PLAN TASK-021: the files are new text throughout; no unit of one, as trace-check.py reads units, is a unit
    of the core, of a phase module, of the plan critic, of a trait file, of another type file or of the other file."""
    main = set(trace_units(read(CORE))) | set(trace_units(read(os.path.join(BRIDGE, "agents", "plan-critic.md"))))
    for root in (PHASES, TRAITS, TYPES):
        for here, _dirs, names in os.walk(root):
            for f in names:
                path = os.path.join(here, f)
                if f.endswith(".md") and os.path.normcase(path) != os.path.normcase(os.path.join(TYPES, FILES[key][0])):
                    main |= set(trace_units(read(path)))
    assert len(main) > 300, len(main)
    for unit in trace_units(text(key)):
        assert unit not in main, unit[:80]


def test_r025_both_rows_are_written_and_browser_extension_is_not():
    """BUILD_PLAN TASK-021: the type's and Claude Code extension's rows flip to written in the same change as their
    files; browser extension stays unwritten, so a part of it still pauses at intake (open-list.md, "When each is
    written")."""
    host = row("Product types", "host-extension")
    cc = row("Sub-types", "claude-code-extension")
    assert host["Written"] == "yes" and cc["Written"] == "yes", (host, cc)
    assert cc["Of type"] == "host-extension"
    assert row("Sub-types", "browser-extension")["Written"] == "no"
    assert host["Workflow name"] == "Host Extension Development"
    assert cc["Sub-workflow name"] == "Claude Code Extension"


def test_r025_the_default_traits_stay_in_the_open_list():
    """§6.3: the type's default trait is installable, and so is Claude Code extension's complete set. The open list is
    the one source of both, so neither type file states them (open-list.md, "Default traits"; INVENTORY, Decisions,
    TASK-019)."""
    assert row("Product types", "host-extension")["Default traits"] == "installable"
    assert row("Sub-types", "claude-code-extension")["Default traits"] == "installable"
    for key in FILES:
        assert "Default traits" not in text(key) and "installable" not in text(key).lower(), key


def test_r025_workflow_check_passes_over_the_workflow_folder():
    """BUILD_PLAN TASK-021: `workflow-check.py` passes over `workflow/` with the two files written."""
    r = run_check(WORKFLOW)
    assert r.returncode == 0 and r.stdout.strip().split("\n") == ["RESULT: OK"], r.stdout + r.stderr


def test_r025_the_bridge_is_classified_without_pausing():
    """BUILD_PLAN TASK-021: the committed fixture, the bridge's own `Workflows:` line as docs/PROJECT_STATUS.md writes
    it (§6.3's classification: host extension → Claude Code extension, with installable), passes `workflow-check.py
    --status` with no FAIL (a part whose type or sub-type is not written pauses) and no FLAG; the bridge's own status
    file carries the same line."""
    path = os.path.join(FIXTURES, "bridge.status.md")
    want = "Workflows: Host Extension Development → Claude Code Extension; traits: Installable"
    wf = [l for l in read(path).replace("\r\n", "\n").split("\n") if l.startswith("Workflows: ")]
    assert wf == [want], wf
    status = read(os.path.join(REPO, "docs", "PROJECT_STATUS.md")).replace("\r\n", "\n").split("\n")
    assert [l for l in status if l.startswith("Workflows: ")] == [want]
    r = run_check("--status", path)
    assert r.returncode == 0 and r.stdout.strip().split("\n") == ["RESULT: OK"], r.stdout + r.stderr
