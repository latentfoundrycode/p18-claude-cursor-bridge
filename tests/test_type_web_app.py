"""TASK-019: the type workflow web app and its sub-workflow local web app (R-023), new text throughout.

enforces: docs/BUILD_PLAN.md TASK-019 (its Done when: the type sets `intake.delivery-kind` to `web-deployment` and adds
the delivery procedure for that kind; local web app overrides the kind with one key, `install-script` (a local server
ships the install-script way, Delivery-Conventions.md §1; INVENTORY, Decisions, TASK-019), installable's procedure
for that kind applying; the default traits has-screens and personal-data, replaced for the sub-type by installable and
long-running process; every section new text under a `new` entry; both rows written; `workflow-check.py` passing and
classifying reAngle and the video factory without pausing); bridge/cursor-bridge/workflow/open-list.md, "Default
traits" (the open list is the one source of a type's and a sub-type's default traits); extension-points.md, "How a
conditional workflow names a point" and the delivery kinds. Supervisor-written; no builder run."""
import importlib.util
import os
import re
import subprocess
import sys

import pytest

from phase_modules import BRIDGE, read, section

REPO = os.path.dirname(BRIDGE)

WORKFLOW = os.path.join(BRIDGE, "cursor-bridge", "workflow")
TYPES = os.path.join(WORKFLOW, "types")
TRAITS = os.path.join(WORKFLOW, "traits")
PHASES = os.path.join(WORKFLOW, "phases")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
EXCEPTIONS = os.path.join(WORKFLOW, "trace-exceptions.md")
OPEN_LIST = os.path.join(WORKFLOW, "open-list.md")
REGISTRY = os.path.join(WORKFLOW, "extension-points.md")
TRACE_CHECK = os.path.join(BRIDGE, "cursor-bridge", "trace-check.py")
WORKFLOW_CHECK = os.path.join(BRIDGE, "cursor-bridge", "workflow-check.py")
FIXTURES = os.path.join(REPO, "tests", "fixtures", "workflows")

# Each file's path under workflow/types/, its title and its change headings, in its order (BUILD_PLAN TASK-019).
FILES = {
    "web-app": ("web-app.md", "Web app",
                ["Set at intake.delivery-kind", "Add at project-end.delivery for web-deployment"]),
    "local-web-app": ("web-app/local-web-app.md", "Local web app", ["Set at intake.delivery-kind"]),
}
KINDS = {"web-app": "web-deployment", "local-web-app": "install-script"}


def text(key):
    return read(os.path.join(TYPES, FILES[key][0]))


def flat(t):
    return re.sub(r"\s+", " ", t).strip()


def body(key, heading):
    return section(text(key), heading, 2)


def trace_units(t):
    spec = importlib.util.spec_from_file_location("trace_check_type_web_app", TRACE_CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [u["normal"] for u in mod.parse_units(t)[0]]


def row(table_heading, key):
    """The open list's row for `key` in the table under `table_heading`, as a dict of its columns."""
    lines = section(read(OPEN_LIST), table_heading, 2).split("\n")
    table = [l for l in lines if l.startswith("|")]
    header = [c.strip() for c in table[0].strip("|").split("|")]
    for l in table[2:]:
        cells = [c.strip() for c in l.strip("|").split("|")]
        if cells[0] == key:
            return dict(zip(header, cells))
    raise AssertionError(key)


def traits_of(cell):
    return set(t.strip() for t in cell.split(","))


def run_check(*args):
    return subprocess.run([sys.executable, WORKFLOW_CHECK] + list(args), capture_output=True, text=True,
                          encoding="utf-8")


@pytest.mark.parametrize("key", sorted(FILES))
def test_r023_each_file_is_a_title_and_its_change_sections_only(key):
    """BUILD_PLAN TASK-019: one `#` title, then the change headings named above, in that order, and nothing else, so
    each file changes the main workflow at those points and no other."""
    lines = text(key).split("\n")
    heads = [l for l in lines if re.match(r"^ {0,3}#", l)]
    assert heads == ["# " + FILES[key][1]] + ["## " + h for h in FILES[key][2]], heads
    assert lines[0] == "# " + FILES[key][1], lines[0]


@pytest.mark.parametrize("key", sorted(FILES))
def test_r023_the_type_sets_web_deployment_and_the_sub_type_overrides_it_with_installer(key):
    """BUILD_PLAN TASK-019: web app sets `intake.delivery-kind` to `web-deployment`; local web app overrides it with
    `install-script`, one key, its section's first non-blank line (extension-points.md: the value is the section's first
    non-blank line), with nothing after it."""
    lines = [l.strip() for l in body(key, "Set at intake.delivery-kind").split("\n") if l.strip()]
    assert lines == [KINDS[key]], lines


@pytest.mark.parametrize("key", sorted(FILES))
def test_r023_every_section_has_its_own_new_entry_and_no_other_entry_names_the_file(key):
    """BUILD_PLAN TASK-019: every section of the two files is new text under a `new` entry naming the file and that
    heading (the trace check counts the type files as modules); no `reword` entry, and none on the title."""
    rel = "bridge/cursor-bridge/workflow/types/" + FILES[key][0]
    got = []
    for line in read(EXCEPTIONS).split("\n"):
        m = re.match(r"^- (new|reword) (\S+) (\S+\.md) (.+)$", line)
        if m and m.group(3) == rel:
            got.append((m.group(1), m.group(2), m.group(4).strip()))
    assert got == [("new", "TASK-019", h) for h in FILES[key][2]], got


@pytest.mark.parametrize("key", sorted(FILES))
def test_r023_the_text_is_new_and_copies_no_passage_of_the_main_workflow(key):
    """BUILD_PLAN TASK-019: the files are new text throughout; no unit of one, as trace-check.py reads units, is a unit
    of the core, of a phase module, of the plan critic, of a trait file or of the other type file."""
    main = set(trace_units(read(CORE))) | set(trace_units(read(os.path.join(BRIDGE, "agents", "plan-critic.md"))))
    for root in (PHASES, TRAITS):
        for here, _dirs, names in os.walk(root):
            for f in names:
                if f.endswith(".md"):
                    main |= set(trace_units(read(os.path.join(here, f))))
    for other in FILES:
        if other != key:
            main |= set(trace_units(text(other)))
    assert len(main) > 300, len(main)
    for unit in trace_units(text(key)):
        assert unit not in main, unit[:80]


def test_r023_both_rows_are_written_and_the_sub_type_is_of_web_app():
    """BUILD_PLAN TASK-019: both rows flip to written in the same change as their files; local web app is a sub-type of
    web app, delivered by an installer instead of a deployment, with a local server to start and stop (the open
    list's definition, §6.3, whose plain-word installer the install script is: Delivery-Conventions.md §1)."""
    web = row("Product types", "web-app")
    local = row("Sub-types", "local-web-app")
    assert web["Written"] == "yes" and local["Written"] == "yes", (web, local)
    assert local["Of type"] == "web-app"
    assert "delivered by an installer instead of a deployment and has a local server to start and stop" in local["Definition"]
    assert web["Workflow name"] == "Web App Development" and local["Sub-workflow name"] == "Local Web App"


def test_r023_the_default_traits_and_the_sub_types_replacement():
    """BUILD_PLAN TASK-019 and §6.3: web app's default traits are has-screens and personal-data; local web app's
    complete set (open-list.md: a sub-type's cell is the complete default set, in place of its type's) replaces
    personal-data with installable and long-running process. The open list is the one source of both sets, so neither
    type file states them (open-list.md, the opening paragraph and "Default traits")."""
    web = traits_of(row("Product types", "web-app")["Default traits"])
    local = traits_of(row("Sub-types", "local-web-app")["Default traits"])
    assert web == {"has-screens", "personal-data"}, web
    assert local == (web - {"personal-data"}) | {"installable", "long-running-process"}, local
    for key in FILES:
        assert "Default traits" not in text(key) and "personal-data" not in text(key), key


def test_r023_the_sub_workflow_inherits_and_leaves_the_types_delivery_behind():
    """BUILD_PLAN TASK-019: the sub-workflow changes only what differs, at the same point its type set (an override is
    inheritance, the core's "Main and conditional workflows"); its kind `install-script` takes installable's procedure
    for that kind (TASK-017), and the type's procedure names `web-deployment`, so it never reaches a local web app
    (extension-points.md: a sub-workflow that sets another kind leaves its type workflow's procedure behind)."""
    assert "project-end.delivery" not in text("local-web-app")
    delivery = [l for l in text("web-app").split("\n") if l.startswith("## Add at project-end.delivery")]
    assert delivery == ["## Add at project-end.delivery for web-deployment"], delivery
    installable = read(os.path.join(TRAITS, "installable.md"))
    assert "\n## Add at project-end.delivery for install-script\n" in installable.replace("\r\n", "\n")
    assert "Deliver the install script** (a command-line tool or a local server)" in flat(installable)
    core = flat(read(CORE))
    assert "**A sub-workflow inherits its type workflow** and changes only what differs, at the same extension points." in core
    assert "It may override its type workflow's replacement or setting: that is inheritance, not a collision." in core
    assert "so a sub-workflow that sets another kind leaves its type workflow's procedure behind" in flat(read(REGISTRY))


def test_r023_the_web_deployment_procedure():
    """BUILD_PLAN TASK-019: the delivery procedure for `web-deployment`: the owner's yes before a deployment (an action
    outside the repository a revert does not undo, the merge policy's irreversibility), the procedure recorded with its
    platform and account, a migration rehearsed on a restored copy, the live data backed up outside the repository and
    the Workspace with writes held, migrated only as part of a release, a check at the deployed address that changes no
    user's data, the way back in its order, and the address and version named."""
    t = flat(body("web-app", "Add at project-end.delivery for web-deployment"))
    assert t.startswith("- **Deploy the release** (a hosted web application): the owner says yes first")
    assert "since a deployment acts outside the repository and a revert does not undo it" in t
    # Review A, round 1 (blocking): a restore over the owner's live data that discards users' writes is the owner's own yes.
    assert "the yes covers the deployment and the way back below, except a restore that would discard users' writes, which is asked of its own" in t
    assert "a restore that would discard writes made since the backup (the product could not hold them) waits for the owner's yes, given with what it discards stated" in t
    assert "deployed to the server the owner operates by the deployment procedure" in t
    assert "recorded in `docs/INVENTORY.md` (Resources: the host, its platform and account, the command that deploys) before the first deployment" in t
    assert "the owner through a run sheet where it needs a key the session does not hold" in t
    # Review A, round 1: the migration rehearsed first; the backup's home; writes held so going back loses nothing.
    assert "its migration is first rehearsed on a copy restored from a backup of the live data" in t and "which also proves the backup restores" in t
    assert "kept away from the repository and the Workspace as the backup below is" in t
    assert "Immediately before the deployment the owner's live data is backed up" in t
    assert "never into the repository or the Workspace, since it holds the users' data" in t
    assert "the product takes no writes where it can hold them (a maintenance or read-only mode), so that going back loses nothing" in t
    assert "the migration runs on the live data only as part of the deployment, never apart from a release" in t
    assert "checked at its address with requests that change no user's data: it answers" in t
    assert "it reports the release's version where the design gives the version a place, the deployed commit read from the platform otherwise" in t
    # Review A, round 1: the order of the way back.
    assert "where a migration ran, the backup is restored first, since the previous release may not run on migrated data, then the previous release is deployed by the same procedure" in t
    assert "A check that fails is a defect like any other" in t
    assert "The report and the User Manual name the address and the version deployed." in t
    assert t.index("rehearsed on a copy") < t.index("Immediately before the deployment") < t.index("checked at its address")


def test_r023_workflow_check_passes_over_the_workflow_folder():
    """BUILD_PLAN TASK-019: `workflow-check.py` passes over `workflow/` with the two files written."""
    r = run_check(WORKFLOW)
    assert r.returncode == 0 and r.stdout.strip().split("\n") == ["RESULT: OK"], r.stdout + r.stderr


@pytest.mark.parametrize("name", ["reangle.status.md", "video-factory.status.md"])
def test_r023_reangle_and_the_video_factory_are_classified_without_pausing(name):
    """BUILD_PLAN TASK-019: the committed fixtures, shaped as each project's `Workflows:` line (§6.3's classification:
    web app → local web app, with its traits in the open list's order), pass `workflow-check.py --status` with no FAIL
    (a part whose type or sub-type is not written pauses) and no FLAG (every trait named is written)."""
    path = os.path.join(FIXTURES, name)
    lines = read(path).replace("\r\n", "\n").split("\n")
    wf = [l for l in lines if l.startswith("Workflows: ")]
    assert wf == ["Workflows: Web App Development → Local Web App; traits: Has screens, Installable, External "
                  "services, Spends money, Long-running process, AI models"], wf
    r = run_check("--status", path)
    assert r.returncode == 0 and r.stdout.strip().split("\n") == ["RESULT: OK"], r.stdout + r.stderr
