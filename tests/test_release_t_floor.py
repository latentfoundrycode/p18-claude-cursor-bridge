"""TASK-041 (R-052's text): the configuration guide's security floor, the weekly scan's frozen block, the Sunday
evaluation's reading of it, the change cycle's conformance check, the template's relative `Layout:` line and the
stripped suite and driver launches.

enforces: docs/REQUIREMENTS.md R-052 (T9, T22, the weekly scan, T12, T19, the `--strip` launch commands);
docs/diagrams/D-004-context-dfd.md (the edge p_bridge_run -> p_test_suite drawn as the commands now run it, its
deviation closed); docs/DESIGN.md, "Change: release T", "The weekly dependency scan" and "The host" (R-052's assumption
observed). The constants below are the sentences as written; the text was written from them. KP-052: no character
outside ASCII is typed here."""
import os
import re

import yaml

from phase_modules import BRIDGE, CORE, flat, module, read

ROOT = os.path.dirname(BRIDGE)
CB = os.path.join(BRIDGE, "cursor-bridge")
GUIDE = os.path.join(CB, "Cursor-Project-Configuration.md")
CONFIGURATOR = os.path.join(BRIDGE, "agents", "cursor-configurator.md")
EVALUATE = os.path.join(BRIDGE, "commands", "evaluate-reports.md")
CALIBRATE = os.path.join(BRIDGE, "commands", "calibrate-bridge.md")
PITFALLS = os.path.join(CB, "Known-Pitfalls.md")
FLOOR_CI = os.path.join(ROOT, ".github", "workflows", "tests.yml")
DEVIATIONS = os.path.join(ROOT, "docs", "diagrams", "DEVIATIONS.md")
D004 = os.path.join(ROOT, "docs", "diagrams", "D-004-context-dfd.md")
DESIGN = os.path.join(ROOT, "docs", "DESIGN.md")

# --- T22 and T9 (the guide)
T22 = ("outside the workspace to `docs/BOUNDARY_VIOLATIONS.md`, which the same item adds to `.gitignore`: the log holds "
       "this computer's absolute paths, so it is read locally and never committed (rule 54, T22).")
T9 = (
    "7. **The floor's conventions (T9).** The floor is trusted only once it has shown that it can fail, and it is kept "
    "the way it was proved:",
    "**Teeth first.** The floor's first increment plants one finding for each scanner (a pattern the Semgrep rules "
    "match, a lock entry with a published advisory for OSV-Scanner, a package Socket flags) on a real CI run, reads each "
    "step red in that run's log, and removes the plants in the same increment, before any review of the floor is "
    "trusted; a scanner whose step stays green with its plant in place has no teeth, whatever it prints.",
    "**Every pin checked for deprecation.** Each action's and tool's pin is read against its vendor's release page when "
    "it is written and at every change of the floor, the OSV-Scanner pin in both places it is stated (the floor's step "
    "and the weekly scan's, step 8): a deprecated, archived or unsupported release is replaced through an increment, "
    "never kept because it still runs.",
    "**A vendor token enables no paid engine.** What a token turns on is read from the vendor's documentation when it is "
    "set; a token that would enable a paid engine or plan is set only on the owner's word, a consequence they bear "
    "(rule 56).",
    "**The floor's test is the supervisor's.** The structural test of the floor (its pins, its permissions, its steps, "
    "its exit-code handling) is written by the supervisor, never by the builder whose work the floor gates.",
    "**Vendor CLIs quiet.** Every vendor CLI runs with its banner, its spinner and its telemetry off, by the option or "
    "variable its documentation names (`socket ci --no-banner`): a banner once printed part of a key into a public log.",
    "**The install apart from the key.** A vendor CLI is installed in a step of its own, without the key and with "
    "`--ignore-scripts` (an install runs the package's code and its dependencies'); the key stands in the scan step's "
    "`env` alone.",
    "**The first log read.** The first CI log of every step that holds a secret is read for any part of it before the "
    "next push; a part found there is told to the owner as a run sheet, since deleting the logs and replacing the key "
    "are the owner's actions.",
)
WEEKLY = (
    "8. **The weekly dependency scan, every project's.** The floor's OSV-Scanner runs only on a pull request's or a "
    "push's event, so a flaw disclosed later in an unchanged dependency, or in a paused or finished project, is never "
    "flagged by it. Every project therefore has a second workflow, `.github/workflows/dependency-scan.yml`, written by "
    "`cursor-configurator` from its frozen block, the block's one fill-in the `--lockfile=` list copied from the floor's "
    "OSV-Scanner step: a weekly `schedule` (Sunday 06:17 UTC) and `workflow_dispatch`, `permissions: contents: read` and "
    "nothing else, the checkout at the floor's pin without persisted credentials, OSV-Scanner at the floor's version and "
    "SHA-256 with the floor's exit-code handling and the line `dependency-scan: OSV-Scanner exit <code>` on every "
    "non-zero exit, no secret and no token handed to a step; a finding fails the run. The increment that adds it is "
    "proved by one `workflow_dispatch` run read green after its merge, since GitHub runs a dispatch or a schedule only "
    "for a file on the default branch, beside its structural test before the merge; a running project receives it at "
    "its calibration, as configuration. The Sunday evaluation reads its runs and the project's Dependabot alerts "
    "(`~/.claude/commands/evaluate-reports.md`)."
)

# --- the configurator and the frozen block
CONFIGURATOR_ITEM = (
    "- The **weekly dependency scan**, `.github/workflows/dependency-scan.yml`, a workflow file of its own beside the "
    "gate's, for **every** project: written verbatim from the frozen block (\"The weekly scan's frozen block\", below), "
    "its one fill-in `<fill-in>` replaced by the value the floor's OSV-Scanner step in the project's gate workflow gives "
    "`--lockfile=` (`requirements.txt:requirements.lock`, say), with one more `--lockfile=<value>` word for each further "
    "lockfile that step names. Never add a step, a permission, a secret or a token, never change a pin or the exit-code "
    "handling, and never regenerate, trim or reorder the block. Its checkout and OSV-Scanner pins are the floor's: where "
    "the project's floor pins another checkout commit or another OSV-Scanner release, stop and report it rather than "
    "write the file."
)
CHECKOUT = "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09"
OSV_URL = "https://github.com/google/osv-scanner/releases/download/v2.7.0/osv-scanner_linux_amd64"
OSV_SHA = "160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b"
FROZEN = (
    "name: dependency-scan\n"
    "on:\n"
    "  schedule:\n"
    "    - cron: '17 6 * * 0'\n"
    "  workflow_dispatch:\n"
    "permissions:\n"
    "  contents: read\n"
    "jobs:\n"
    "  dependency-scan:\n"
    "    name: dependency scan\n"
    "    runs-on: ubuntu-latest\n"
    "    steps:\n"
    "      - uses: " + CHECKOUT + " # v5\n"
    "        with:\n"
    "          persist-credentials: false\n"
    "      - name: OSV-Scanner\n"
    "        shell: bash\n"
    "        run: |\n"
    "          curl -fsSL -o osv-scanner \"" + OSV_URL + "\"\n"
    "          echo \"" + OSV_SHA + "  osv-scanner\" | sha256sum -c -\n"
    "          chmod +x osv-scanner\n"
    "          set +e\n"
    "          ./osv-scanner scan source --config=osv-scanner.toml --lockfile=<fill-in>\n"
    "          code=$?\n"
    "          set -e\n"
    "          if [ \"$code\" -eq 0 ]; then\n"
    "            exit 0\n"
    "          fi\n"
    "          echo \"dependency-scan: OSV-Scanner exit $code\"\n"
    "          if [ \"$code\" -eq 128 ]; then\n"
    "            echo \"OSV-Scanner exit 128: no lockfile was read\"\n"
    "          fi\n"
    "          exit \"$code\"\n"
)

# --- the Sunday evaluation
EV_NOTE = ("Before the extract, note the ledger's `_meta.last_extract`, the previous run's date, which the extract "
           "rewrites: it opens the window step 1b reads.")
EV_HEAD = ("1b. **Read the weekly dependency scan and the Dependabot alerts**, for every project, a week with nothing new "
           "included (R-052; the three kinds below are the bridge design's, `docs/DESIGN.md`, \"The weekly dependency "
           "scan\"). `<owner>/<repo>` is the project's GitHub repository, read from its `origin` remote. First the "
           "workflow's state:")
EV_COMMANDS = (
    "gh workflow list --all --repo <owner>/<repo>",
    "gh run list --repo <owner>/<repo> --workflow dependency-scan.yml --created \">=<the ledger's _meta.last_extract>\" "
    "--json databaseId,createdAt,status,conclusion",
    "gh run view <run id> --repo <owner>/<repo> --log-failed",
    "gh api repos/<owner>/<repo>/vulnerability-alerts",
    "gh api --paginate \"repos/<owner>/<repo>/dependabot/alerts?state=open\"",
)
EV_WINDOW = (
    "The date is a day and the schedule runs on the morning of the evaluation's own Sunday, so that list also holds "
    "the runs the previous evaluation read. The window is the listed runs whose `createdAt` is later than the `last "
    "run read:` time the previous evaluation's Dependency scan section gives for the project, every listed run where "
    "that section reads `last run read: none`, and, where no previous section names the project, the listed runs "
    "whose `createdAt` falls on a later day than that date, so a run of that day cannot cover this Sunday; each "
    "evaluation's section gives, per project, `last run read: <createdAt>`, the creation time of the newest "
    "completed run of its window, or the previous section's value where the window completed none, `none` where "
    "there was no previous one, so a run still in progress at the reading is read the next Sunday (an older one "
    "beside a newer completed run goes unread, the newer run's time passing it), and a late or missing schedule "
    "leaves the window without a completed run. A run re-run from the Actions tab keeps its creation time and is not "
    "read again; the rerun this step names, `gh workflow run`, starts a new run. While a finding stands, the section "
    "also gives `finding standing: run <id>`, carried from each section to the next until a later run ends "
    "`success`, so the finding is reported every week it stands, beside whatever kind the week's own runs show.")
EV_NOT_CONFIGURED = (
    "A list that holds no `dependency-scan` names a project that has not received the workflow yet (one not "
    "calibrated to release T): it is written `not configured`, its calibration's item, with `last run read: none`, "
    "and no run is read for it.")
EV_EVERY_WEEK = (
    "and the evaluation file only those and its Pace and Dependency scan sections (the ledger keeps the run's date)",
    "a creeping slowdown named the week it starts; then the **Dependency scan** section step 1b gives.",
    "In a week with nothing new the file is written all the same, holding the Pace and Dependency scan sections and "
    "any entry the owner's messages raised.",
    "A Sunday with nothing new writes the Pace and Dependency scan sections and any entry the owner's messages raised.",
)
EV_SENTENCES = (
    "Any disabled state of the workflow (`disabled_inactivity`, `disabled_manually`) is the third kind below whatever "
    "its runs show: GitHub disables a public repository's scheduled workflows after 60 days with no activity, and "
    "`gh run list` lists no run of a disabled workflow without `--all`.",
    "**A finding**: a completed run of the window ended `failure` and its exit line reads `exit 1`, a flaw in a "
    "dependency, fixed by a `DEP-<nnn>` increment (the merge policy's procedure), never by an unreviewed change; it "
    "stands until a later run ends `success`, in this window or a later one.",
    "**A scanner failure**: the window's last completed run proved nothing, a `failure` with "
    "another exit code or no exit line at all, or any conclusion other than `success` and `failure`; it is reported "
    "with the rerun's one command, `gh workflow run dependency-scan.yml --repo <owner>/<repo>`, and the rerun is read at "
    "the next evaluation, a finding that stands reported beside it, superseded by nothing but a `success`.",
    "**No completed run since the previous evaluation**: the workflow disabled, no run of the window listed, a list the "
    "login cannot read, or only runs still queued or in progress, a finding of its own and never green (KP-005: silence "
    "is not green), reported with its remedy: where the workflow is disabled, a run sheet for the project's owner "
    "(`gh workflow enable dependency-scan.yml`, then `gh workflow run dependency-scan.yml`); where no run is listed, the "
    "rerun command; where a run is in progress, none, the next Sunday reading it.",
    "A window whose last completed run ended `success`, with no finding standing, is green.",
    "answers 204 where the alerts are enabled and 404 where they are not, a 404 the finding \"alerts off\" and the "
    "second call not made; after a 204,",
    "lists the open alerts, every page of them, an empty list being alerts on with nothing open. A 403 on either call is "
    "the login's scope, named in a run sheet for the owner, never a token in text, the project's Security tab the "
    "fallback.",
    "Step 4's file gives each project's kind, its `last run read:` time and any `finding standing:` run, its alerts and "
    "the remedy in a **Dependency scan** "
    "section, written every week beside the Pace section; a finding of either is an entry of the evaluation like any "
    "other.",
)

# --- T12 and T19
T12 = ("A project that became supervised after it was built (its code written before the bridge supervised it) also "
       "runs `python ~/.claude/cursor-bridge/conformance-check.py` here, before the first delegation: every `MISSING` "
       "floor becomes a configuration increment of the plan addendum, planned ahead of the request's increments, and "
       "every `NOTE` is recorded in `PROJECT_STATUS.md` (T12).")
T19_TEMPLATE = "Layout: Workspace=Workspace/  Documents=Documents/ (relative to the project root)"
T19_CORE = ("Resolve both folders once, at intake, and record them on the status file's `Layout:` line, relative to the "
            "project root and never as a computer path (rule 54).")

# --- the stripped launches, one text in five homes
LAUNCHER = "python ~/.claude/cursor-bridge/bridge-run.py --limit auto --strip "
SCRATCH = "--scratch ~/.cursor-bridge/scratch/<the project root's folder name>"
MUTATION_RUN = "--kind driver -- python ~/.claude/cursor-bridge/mutation-run.py run/supervisor/<id>-mutants.json "
SUITE_CMD = LAUNCHER + "--kind test -- <the recorded suite command> > run/agent/TASK-<nnn>-suite.out 2>&1"
CHECKPOINT_CMD = (LAUNCHER + MUTATION_RUN + "--checkpoint <the increment's checkpoint commit> " + SCRATCH
                  + " > run/agent/<id>-checkpoint.out 2>&1")
MUTATION_CMD = LAUNCHER + MUTATION_RUN + SCRATCH + " > run/agent/<id>-mutation.out 2>&1"
P7_CMD = LAUNCHER + "--key-file <a file outside the Workspace> --kind test -- python -m pytest -q tests"
CALIBRATE_CMD = LAUNCHER + "--kind test -- <the recorded suite command> -rA > run/agent/calibrate-suite-before.out 2>&1"
KP061 = "(`bridge-run.py --limit auto --strip --kind test`)"
LOOP_SUITE = ("The suite runs through the launcher in the background, whatever its length, with the owner's environment "
              "stripped (`--strip`, between `--limit` and `--kind`): no launch of the loop but a driver under a recorded Decision (step 7) hands code the builder wrote "
              "the owner's login or secret-like variables (D-004, R-052), and a variable the suite needs reaches it by "
              "`--key-file <a file outside the Workspace>`, which the test kind accepts:")
LOOP_CHECKPOINT = ("stage them (`git add`), and launch the engine in the background like any mutation run, stripped and "
                   "with its scratch folder named as step 7 says (`delegation-loop/decide.md`, \"The mutation run\"), the "
                   "`python` after the `--` being the project's own interpreter:")
DECIDE_LEAD = ("Launch the run in the background through the launcher's driver kind, under the heavy launch's `timeout` "
               "(`delegation-loop.md`, step 3), stripped and with its scratch folder named:")
DECIDE_WHY = ("The strip keeps the owner's login and secret-like variables from the code the mutants run (`--strip`, "
              "D-004, R-052). `--scratch` names the folder the copy is built in, `~/.cursor-bridge/scratch/<the project "
              "root's folder name>`, the shell's `~` being the owner's profile: the program's default follows the home "
              "the environment names, which the strip makes the agent home, so a stripped driver would otherwise copy "
              "the Workspace, `.env` included, into the agent home. The copy carries the project's `.env` (KP-032's home "
              "for local service passwords), and the driver kind refuses `--key-file`, so a mutation run whose suite "
              "needs a variable beyond `.env` runs without `--strip` only under a Decision in `docs/INVENTORY.md` naming "
              "the variable, until the launcher gains a driver key file.")
MERGE_P7 = ("the full suite runs once with the pull request's variables set, as CI runs it on the pull request's merge, "
            "stripped as every suite of the loop runs (`delegation-loop.md`, step 4):")
CALIBRATE_LEAD = ("in the background through the launcher, stripped as the loop's suites run "
                  "(`~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`, step 4): `" + CALIBRATE_CMD + "`")
UNSTRIPPED = ("--limit auto --kind test", "--limit auto --kind driver", "--limit auto --key-file")

# --- the design's host table and D-004
HOST_ROW = ("| A permission allow rule's `*` between fixed words admits a launch with two words there: `--limit * --kind "
            "test -- *` and `--limit auto --strip --kind test -- ...` (R-052's assumption) | observed 2026-11-02 at "
            "TASK-041's (a): `bridge-run.py --limit auto --strip --kind test -- python -m pytest -q -rs "
            "tests/test_release_t_strip.py` ran from this session twice with no prompt and no refusal (10:45:12Z, exit 1, "
            "the test reading HOME after the suite's own fixture had replaced it, a defect of the test; 10:45:50Z, exit 0, "
            "the strip test passing: HOME the agent home, no withheld name); the absence of a prompt is the observable the "
            "plan names, and it does not tell a launch the rule allowed from one auto mode's classifier allowed, so the "
            "observation does not contradict the assumption rather than proving it: the two heavy-launch rules are kept, "
            "the documented `--strip` commands are pinned as matching (`tests/test_allowlist.py`), and a prompt or a "
            "refusal at any later stripped launch is still the trigger for the widening below | 2.1.309, 2026-11-02 |")


def bash_blocks(text):
    return [line.strip() for m in re.finditer(r"```(?:bash|sh)\n(.*?)```", text, re.S) for line in m.group(1).splitlines()]


def guide_section(title):
    text = read(GUIDE)
    return text.split("\n## " + title, 1)[1].split("\n## ", 1)[0]


def frozen_block():
    text = read(CONFIGURATOR)
    section = text.split("\n## The weekly scan's frozen block\n", 1)[1].split("\n## ", 1)[0]
    blocks = re.findall(r"```yaml\n(.*?)```", section, re.S)
    assert len(blocks) == 1, "the section holds one yaml block"
    return blocks[0]


def floor_osv_step():
    floor = yaml.safe_load(read(FLOOR_CI))
    steps = floor["jobs"]["security-floor"]["steps"]
    return [s for s in steps if s.get("name") == "OSV-Scanner"][0], steps[0]


def test_r052_t22_the_boundary_item_ignores_its_log():
    assert T22 in flat(guide_section("1. Repo hygiene"))


def test_r052_t9_the_guide_carries_the_floor_s_conventions():
    s = flat(guide_section("5c. Security tooling"))
    for sentence in T9:
        assert sentence in s, sentence[:60]
    assert s.index(T9[0]) < s.index("**Escalation:**")


def test_r052_the_weekly_scan_is_every_project_s():
    s = flat(guide_section("5c. Security tooling"))
    assert WEEKLY in s
    assert s.index(T9[0]) < s.index(WEEKLY) < s.index("**Escalation:**")


def test_r052_the_configurator_writes_the_scan_from_the_frozen_block():
    t = flat(read(CONFIGURATOR))
    what = t.split("## What you write", 1)[1].split("## Hard limits", 1)[0]
    assert flat(CONFIGURATOR_ITEM) in what
    assert frozen_block() == FROZEN


def test_r052_the_frozen_block_is_the_workflow_whole():
    block = frozen_block()
    assert block.count("<fill-in>") == 1
    wf = yaml.safe_load(block.replace("<fill-in>", "requirements.txt:requirements.lock"))
    triggers = wf[True]                                   # yaml reads `on:` as the boolean True
    assert triggers["schedule"] == [{"cron": "17 6 * * 0"}] and "workflow_dispatch" in triggers
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert wf["permissions"] == {"contents": "read"}
    (job,) = wf["jobs"].values()
    checkout, osv = job["steps"]
    assert checkout["with"] == {"persist-credentials": False}
    assert "secrets." not in block and "token" not in block.lower()
    assert "env" not in job and all("env" not in step for step in job["steps"])
    run = osv["run"]
    assert "./osv-scanner scan source --config=osv-scanner.toml --lockfile=requirements.txt:requirements.lock" in run
    assert 'echo "dependency-scan: OSV-Scanner exit $code"' in run
    assert run.index("exit 0") < run.index("dependency-scan: OSV-Scanner exit") < run.index('exit "$code"')


def test_r052_the_block_s_pins_are_the_floor_s():
    """The one pin stated twice: the floor's checkout and OSV-Scanner version and SHA-256 equal the block's."""
    osv, checkout = floor_osv_step()
    block = frozen_block()
    assert checkout["uses"] == CHECKOUT and ("uses: " + CHECKOUT) in block
    assert OSV_URL in osv["run"] and OSV_URL in block
    assert ('echo "' + OSV_SHA + '  osv-scanner" | sha256sum -c -') in osv["run"]
    assert ('echo "' + OSV_SHA + '  osv-scanner" | sha256sum -c -') in block


def test_r052_evaluate_reports_reads_the_scan_in_three_kinds():
    text = read(EVALUATE)
    t = flat(text)
    assert EV_NOTE in t
    assert t.index(EV_NOTE) < t.index("python ~/.claude/cursor-bridge/evaluate-reports.py extract")
    assert EV_HEAD in t
    assert t.index("pace-report.py --tokens") < t.index(EV_HEAD) < t.index("2. **Classify**")
    lines = bash_blocks(text)
    for cmd in EV_COMMANDS:
        assert cmd in lines, cmd
    for sentence in EV_SENTENCES + (EV_WINDOW, EV_NOT_CONFIGURED) + EV_EVERY_WEEK:
        assert sentence in t, sentence[:60]
    assert t.index(EV_WINDOW) < t.index("--log-failed")
    assert "Pace section and any entry" not in t, "a nothing-new week names the Dependency scan section too"


def test_r052_t12_the_change_cycle_runs_the_conformance_check_first():
    item1 = flat(module("change-cycle.md")).split("1. **Intake of the change**", 1)[1].split("2. **Design revision**", 1)[0]
    assert ("A project with no register gets one built from its requirements document, design, and mockup before the "
            "check runs. " + T12) in item1


def test_r052_t19_the_layout_line_is_relative():
    core = read(CORE)
    assert ("\n" + T19_TEMPLATE + "\n") in core
    assert "Layout: Workspace=<resolved path>" not in core
    assert T19_CORE in flat(core)
    assert "record the resolved paths in" not in flat(core)


def test_r052_the_stripped_launches_in_the_loop_and_its_sub_files():
    loop, decide, merge = module("delegation-loop.md"), module("delegation-loop/decide.md"), module("delegation-loop/merge.md")
    assert SUITE_CMD in bash_blocks(loop) and CHECKPOINT_CMD in bash_blocks(loop)
    assert MUTATION_CMD in bash_blocks(decide)
    assert P7_CMD in bash_blocks(merge)
    assert LOOP_SUITE in flat(loop) and LOOP_CHECKPOINT in flat(loop)
    assert DECIDE_LEAD in flat(decide) and DECIDE_WHY in flat(decide)
    assert MERGE_P7 in flat(merge)
    for name, text in (("loop", loop), ("decide", decide), ("merge", merge)):
        for old in UNSTRIPPED:
            assert old not in text, (name, old)


def test_r052_the_five_homes_give_one_command():
    """The calibration's and KP-061's forms are the loop's: the same launcher words, `--strip` between `--limit` and
    `--kind`; neither file is read by tests/test_allowlist.py's collector, so this test holds them to the loop's."""
    cal = flat(read(CALIBRATE))
    assert CALIBRATE_LEAD in cal
    assert "Run the same suite once more the same way, into `run/agent/calibrate-suite-after.out`" in cal
    kp = flat(read(PITFALLS)).split("### KP-061", 1)[1].split("### KP-062", 1)[0]
    assert KP061 in kp
    for name, text in (("calibrate", cal), ("KP-061", kp)):
        for old in UNSTRIPPED:
            assert old not in text, (name, old)
        assert "bridge-run.py --limit auto --strip --kind test" in text, name


def test_r052_d004_s_deviation_closed_and_its_edge_redrawn():
    rows = [line for line in read(DEVIATIONS).splitlines() if line.startswith("| D-004 | p_bridge_run | p_test_suite |")]
    assert rows == []
    d004 = read(D004)
    edge = [line for line in d004.splitlines() if line.startswith("p_bridge_run -->") and line.endswith("p_test_suite")]
    assert len(edge) == 1
    assert "--strip" in edge[0] and "DEVIATIONS" not in edge[0]
    assert "the as-built default a deviation" not in d004


def test_r052_the_observed_launch_in_the_host_table():
    assert HOST_ROW in read(DESIGN)
