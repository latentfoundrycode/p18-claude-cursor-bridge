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
def test_r023_the_type_sets_web_deployment_and_the_sub_type_overrides_it_with_install_script(key):
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
    """BUILD_PLAN TASK-019: the delivery procedure for `web-deployment`, numbered steps each run only after the one
    before it has succeeded (Review B, rounds 1 and 2; Review A, round 5): the owner's yes first (an action outside the
    repository a revert does not undo, the merge policy's irreversibility), the procedure recorded with its platform
    and account; the pause before the backup, in a mode in which the product still answers, seen to hold by a marker
    write that changes no user's data; the backup taken under the pause, outside the repository and the Workspace,
    proved by a restore to a copy read back against the live store, the migration rehearsed on that copy, the copy
    deleted, a failure resuming writes on the unchanged product; the migration on the live data only inside the
    deployment (N1's principle); the pause seen to hold again after the deployment, then the check; the way back with
    writes held, a restore only where a migration began and only once the pause is seen to have held since the backup,
    a write that may have landed since (or a product with no write records) making the restore the owner's question, put with what each answer costs, the answer not ending the pause, an accepted marker write contained first, the cost of declining naming the failed release left deployed, the previous release deployed only
    after the restore succeeded, a failure keeping writes held; the address and version named. Dropping data is the
    owner's yes (supervisor.md's escalation)."""
    t = flat(body("web-app", "Add at project-end.delivery for web-deployment"))
    assert t.startswith("- **Deploy the release** (a hosted web application): steps 1 to 5 in this order, each only after the one before it has succeeded, and step 6 when step 4 or step 5 fails, its own actions too each only after the one before it has succeeded:")
    steps = ["1. **The owner's yes**, first", "2. **The pause.**", "3. **The backup, proved.**",
             "4. **The deployment.**", "5. **The check.**", "6. **The way back**"]
    at = [t.index(s) for s in steps]
    assert at == sorted(at), at
    # Review B, rounds 2 to 4: the order the paragraph enforces, read sentence by sentence, not heading by heading.
    order = ["the yes names the release", "The product stops taking writes", "a marker write that changes no user's data",
             "With writes held, the owner's live data is backed up", "The backup is then restored to a copy",
             "its contents compared with the live store's under the pause", "its migration is rehearsed on that copy",
             "A backup that does not restore, or a rehearsal that fails, stops the deployment",
             "the copy is then deleted", "The release's commit on `main` is deployed",
             "step 2's marker write is tried again and refused", "the check below is not run, writes stay held, and step 6 runs",
             "Only after a refused marker is it checked at its address",
             "When it passes, writes resume", "Where step 4 began a migration on the live data",
             "step 2's marker write, tried again at the start of this step, is refused",
             "Then the backup is restored over the live data", "the restore is the owner's question",
             "Only once the restore has succeeded, or where none was needed, is the previous release deployed",
             "only once it passes the check of step 5 do writes resume"]
    at = [t.index(s) for s in order]
    assert at == sorted(at), list(zip(order, at))
    assert t.count("The release's commit on `main` is deployed") == 1
    assert "since a deployment acts outside the repository and a revert does not undo it" in t
    assert "the yes names the release, the pause step 2 makes and how long it may last (and the writes from outside it refuses, which a sender that does not retry loses), and the way back in step 6" in t
    assert "recorded in `docs/INVENTORY.md` (Resources: the host, its platform and account, the command that deploys) before the first deployment" in t
    assert "the owner through a run sheet where it needs a key the session does not hold" in t
    assert "neither its users' nor any from outside (a provider's notices, its scheduled jobs), in a maintenance or read-only mode in which it still answers at its address" in t
    assert "a marker write that changes no user's data (one the product discards, or one removed afterwards) is tried and refused" in t
    assert "A product with neither mode cannot be checked while it takes no writes, so its design gives it one, a change like any other, before its first deployment" in t
    # Review A, round 8: an accepted marker write is contained before anything else is done.
    assert "Wherever the marker write is tried again (steps 5 and 6) and accepted, the product has left its mode: it is first put back into it, or stopped where it will not hold the mode, and seen to take no writes before anything else is done." in t
    assert "offline" not in t and "where it can hold them" not in t and "leave it taking writes" not in t
    assert "the live store's last write" not in t
    assert "so the backup holds every write" in t
    assert "never into the repository or the Workspace, since it holds the users' data" in t
    assert "kept away from the repository and the Workspace as the backup is, and read back, its contents compared with the live store's under the pause (the count of records in each table or collection, or a checksum of each), which proves this backup restores" in t
    assert "Whichever way this step ends, the copy is then deleted, since it holds the users' data; the backup stays where Resources records it." in t
    assert "A backup that does not restore, or a rehearsal that fails, stops the deployment: writes resume on the unchanged live product" in t
    assert "deployed by the recorded procedure, which brings the release up in the mode of step 2" in t
    assert "its migration runs on the live data only here, as part of the deployment, never apart from a release" in t
    assert "The deployed product is first seen to be still paused, since a deployment may restart it out of its mode" in t
    assert "step 2's marker write is tried again and refused; one accepted fails this step at once, once the product is back in its mode or stopped as step 2 says: the check below is not run, writes stay held, and step 6 runs." in t
    assert "with requests that change no user's data: it answers, and it reports the release's version where the design gives the version a place, the deployed commit read from the platform otherwise" in t
    assert "When it passes, writes resume, and the report and the User Manual name the address and the version deployed." in t
    assert "when step 4 or step 5 fails, a defect like any other, with writes held throughout" in t
    assert "but only once the pause is seen to hold and no write from a user or from outside can have landed since the backup" in t
    assert "is refused (where it is accepted, once the product is back in its mode or stopped, as step 2 says), and the product's records of when each write from a user or from outside was made show none later than the backup's time (the migration's own writes and the marker writes not counted)" in t
    assert "Otherwise (a write later than the backup, or a product that keeps no such records, where nothing shows that no write landed while the deployment ran or while the product was out of its mode) a user's write may have landed since the backup" in t
    assert "every earlier try" not in t
    assert "Then the backup is restored over the live data, and the restore discards no user's write." in t
    assert "may have landed since the backup, and the restore is the owner's question, put with what each answer costs: a restore discards the writes made since the backup (named where the product's records allow), and declining leaves the failed release deployed on the migrated data, which the previous release may not run on, with writes held until the owner says to resume them, which would resume them on that failed release and that data." in t
    assert "The answer does not end the pause: after a yes, the restore and the rest of this step run as for any restore, writes held until the previous release passes its check." in t
    assert "Where step 4 began no migration, the live data is left as it is." in t
    assert "is the previous release deployed by the same procedure, in the mode of step 2" in t
    assert "The pause lasts until step 5 passes, step 3 stops the deployment, or step 6 has brought the previous release back and its check has passed; where step 6 ends without that (the owner declines its restore, or the restore or the previous release's check fails), until the owner says, as a decision of its own, to resume writes on the release then deployed and the data it holds, both of which the supervisor names when it tells them. An answer to step 6's question does not end it." in t
    assert "until their word" not in t
    assert "If the restore fails, or the previous release fails its check, writes stay held and the owner is told." in t
    assert "Once step 5 has passed and writes have resumed, the backup is no longer a way back that loses nothing: restoring it later discards the writes made since, which is the owner's question." in t


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
