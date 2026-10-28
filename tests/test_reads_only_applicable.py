"""TASK-025: a new project walked from intake to configuration reads only its core, its current phase's module and its
own conditional workflows (R-030).

enforces: docs/REQUIREMENTS.md R-030 and docs/BUILD_PLAN.md TASK-025's Done when ("`test_reads_only_applicable.py`
walks a sample project intake->configuration and asserts only the core + current phase module + its own conditionals
are named for reading"). What a session is told to read after a compaction, a resume or a fork is what the
session-start hook prints (rule 28): the core's digest in one part, the files to re-read in the other. The expected
files are computed here from the texts, not from the hook: the phase's modules as transcribed from the core's table
"The phase modules" (WALK; each module checked to stand in that table), each module's `Sub-files:` and `Variants:` lines, and of the project's
own type, sub-type and traits (the open list's workflow names) each written file that changes a point the registry
(extension-points.md) declares in one of those modules, or replaces one, in the order additions apply in (type,
sub-type, the traits in the open list's order; the core's "The order additions apply in"). R-030's layers are the
workflow files; beside them the hook names the phase's reference texts (`and <file>, whole`), and every other file it
names is checked to be such a text at the bridge's top folder, the same for every project at that phase whatever its
type, sub-type and traits (no layer of its own). The hook reads an installed
bridge: each test copies the repository's bridge/ into a temporary home, as bridge-install.py lays it out.
Supervisor-written; no builder run."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

from phase_modules import BRIDGE, read, section
from workflow_files import PHASES, REGISTRY, TRAITS, TYPES, WORKFLOW, rows

PROG = os.path.join(BRIDGE, "cursor-bridge", "session-start.py")
W = "~/.claude/cursor-bridge/workflow/"
ARROW = "→"
# the walk from intake to configuration: each `Phase:` value the template allows there and the modules the core's
# table "The phase modules" gives it (planning's value covers the run parameters, asked after the plan)
WALK = [("intake", ["intake"]), ("design", ["design"]), ("mockups", ["interface"]),
        ("planning", ["planning", "run-parameters"]), ("configuration", ["configuration"])]
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def unfenced(text):
    """The lines of the text outside fenced blocks."""
    out, fence = [], None
    for line in text.split("\n"):
        m = FENCE.match(line)
        if fence is None and m:
            fence = m.group(1)
        elif fence is not None and m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
                and not line.strip()[len(m.group(1)):].strip():
            fence = None
        elif fence is None:
            out.append(line)
    return out


def module_files(module):
    """The module's file and the files its `Sub-files:` and `Variants:` lines name, in their order, as the hook names
    them (relative to workflow/phases/)."""
    files = ["phases/%s.md" % module]
    for line in unfenced(read(os.path.join(PHASES, module + ".md"))):
        m = re.match(r"^(Sub-files|Variants): (.+)$", line)
        if m:
            files += ["phases/" + p.strip() for p in m.group(2).split("; ")]
    return files


def declared_by():
    """{point key: the module that declares it}, from the registry's table."""
    got = {}
    for line in section(read(REGISTRY), "Extension points", 2).split("\n"):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if line.startswith("| ") and len(cells) == 6 and "." in cells[0] and cells[0] != "Key":
            got[cells[0]] = cells[3]
    return got


def touched_modules(path):
    """The modules a conditional workflow file changes: each `## Add at` or `## Set at` point's declaring module and
    each `## Replace` module, outside fenced blocks."""
    points = declared_by()
    got = set()
    for line in unfenced(read(path)):
        m = re.match(r"^## (?:Add at|Set at) (\S+?)(?: for \S+)?$", line)
        if m:
            got.add(points[m.group(1)])
        m = re.match(r"^## Replace (\S+)$", line)
        if m:
            got.add(m.group(1))
    return got


def own_files(line):
    """The project's own conditional workflow files that exist, in the order additions apply in: (relative path,
    absolute path)."""
    m = re.fullmatch(r"Workflows: (.+?)(?: %s (.+))?; traits: (.+)" % ARROW, line)
    assert m, line
    types = {r["Workflow name"]: r for r in rows("Product types").values()}
    subs = {r["Sub-workflow name"]: r for r in rows("Sub-types").values()}
    traits = rows("Traits")
    t = types[m.group(1)]
    files = [("types/%s.md" % t["Key"], os.path.join(TYPES, t["Key"] + ".md"))]
    if m.group(2):
        s = subs[m.group(2)]
        files.append(("types/%s/%s.md" % (t["Key"], s["Key"]), os.path.join(TYPES, t["Key"], s["Key"] + ".md")))
    names = [n.strip() for n in m.group(3).split(",")]
    for key, r in traits.items():
        if r["Name"] in names:
            files.append(("traits/%s.md" % key, os.path.join(TRAITS, key + ".md")))
    return [(rel, path) for rel, path in files if os.path.isfile(path)]


def expected(line, modules):
    want = [f for m in modules for f in module_files(m)]
    want += [rel for rel, path in own_files(line) if touched_modules(path) & set(modules)]
    return [W + f for f in want]


def sample_lines():
    """One new project per written type and per written sub-type, each with the open list's default traits for it
    (a type's own where it has no sub-type), named in the open list's order; and a local web app with every written
    trait (reAngle's line and performance budgets)."""
    traits = rows("Traits")
    order = list(traits)

    def line(type_wf, sub_wf, defaults):
        keys = sorted((k.strip() for k in defaults.split(",") if k.strip() in traits), key=order.index)
        head = type_wf + (" %s %s" % (ARROW, sub_wf) if sub_wf else "")
        return "Workflows: %s; traits: %s" % (head, ", ".join(traits[k]["Name"] for k in keys))

    types = rows("Product types")
    got = [line(r["Workflow name"], None, r["Default traits"]) for r in types.values() if r["Written"] == "yes"]
    got += [line(types[r["Of type"]]["Workflow name"], r["Sub-workflow name"], r["Default traits"])
            for r in rows("Sub-types").values() if r["Written"] == "yes"]
    got.append(line("Web App Development", "Local Web App",
                    ", ".join(k for k, r in traits.items() if r["Written"] == "yes")))
    return got


SAMPLES = sample_lines()


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    shutil.copytree(os.path.join(BRIDGE, "commands"), str(h / ".claude" / "commands"))
    shutil.copytree(os.path.join(BRIDGE, "cursor-bridge"), str(h / ".claude" / "cursor-bridge"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    return h


def hook(tmp_path, home, part, *status_lines):
    ws = tmp_path / "proj" / "Workspace"
    (ws / "docs").mkdir(parents=True, exist_ok=True)
    (ws / "docs" / "PROJECT_STATUS.md").write_text(
        "# Project Status\n" + "\n".join(status_lines) + "\nAwaiting user on: nothing\n", encoding="utf-8")
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    data = {"cwd": str(ws), "hook_event_name": "SessionStart", "source": "compact"}
    p = subprocess.run([sys.executable, PROG, "--part", part], input=json.dumps(data), capture_output=True, text=True,
                       encoding="utf-8", env=env)
    assert p.returncode == 0 and p.stderr == "", p.stderr
    return p.stdout


def named(out):
    return [re.match(r"  - (\S+)", l).group(1) for l in out.split("\n") if l.startswith("  - " + W)]


REFERENCE = re.compile(r"  - and ~/\.claude/cursor-bridge/[A-Za-z-]+\.md, whole")


def references(out):
    """The hook's other listed lines, each a reference text at the bridge's top folder (an assertion), in order."""
    other = [l for l in out.replace("\r\n", "\n").split("\n") if l.startswith("  - ") and not l.startswith("  - " + W)]
    assert all(REFERENCE.fullmatch(l) for l in other), other
    return other


def test_r030_walk_modules_stand_in_the_cores_table():
    """WALK's modules are the core's table's (a transcription, checked here so a change to the table is seen)."""
    table = section(read(os.path.join(BRIDGE, "commands", "supervisor.md")), "The phase modules", 2)
    for _phase, modules in WALK:
        for m in modules:
            assert "`%sphases/%s.md`" % (W, m) in table, m


def test_r030_the_samples_cover_every_written_type_and_sub_type():
    """The walk's projects are one per written type and sub-type, and every written trait file belongs to one of
    them, so each conditional workflow the bridge ships is walked."""
    assert len(SAMPLES) == 1 + len([r for r in rows("Product types").values() if r["Written"] == "yes"]) + \
        len([r for r in rows("Sub-types").values() if r["Written"] == "yes"])
    walked = {rel for line in SAMPLES for rel, _path in own_files(line)}
    shipped = {os.path.relpath(os.path.join(d, f), WORKFLOW).replace(os.sep, "/")
               for base in (TYPES, TRAITS) for d, _dirs, fs in os.walk(base) for f in fs if f.endswith(".md")}
    assert walked == shipped, (sorted(shipped - walked), sorted(walked - shipped))


def test_r030_before_classification_intake_names_its_module_alone(tmp_path, home):
    """A new project at intake, its parts not yet classified, is told to read the intake module and no conditional
    workflow."""
    out = hook(tmp_path, home, "pointers", "Phase: intake", "Workflows: not yet classified")
    assert named(out) == [W + "phases/intake.md"], out


@pytest.mark.parametrize("line", SAMPLES)
def test_r030_each_phase_from_intake_to_configuration_names_only_its_modules_and_own_conditionals(tmp_path, home, line):
    """For each phase of the walk the hook names exactly the phase's module files and, after them, the project's own
    conditional workflows that change that phase, in the order additions apply in: no other phase's module and no
    other type's, sub-type's or trait's file; every other file it names is a reference text, the same as for an
    unclassified project at that phase. Over the walk each of the project's own files that changes one of these
    phases is named at its phase."""
    own = {W + rel for rel, _path in own_files(line)}
    seen = set()
    for phase, modules in WALK:
        out = hook(tmp_path, home, "pointers", "Phase: %s" % phase, line)
        got = named(out)
        assert got == expected(line, modules), (phase, line, out)
        modfiles = {W + f for m in modules for f in module_files(m)}
        assert set(got) <= modfiles | own, (phase, sorted(set(got) - modfiles - own))
        seen |= set(got) & own
        plain = hook(tmp_path, home, "pointers", "Phase: %s" % phase, "Workflows: not yet classified")
        assert references(out) == references(plain), (phase, line, out)
    reach = {W + rel for rel, path in own_files(line)
             if touched_modules(path) & {m for _p, ms in WALK for m in ms}}
    assert seen == reach, (line, sorted(reach - seen))


def test_r030_the_other_part_is_the_core_and_names_no_workflow_file(tmp_path, home):
    """The hook's other part re-injects the core's digest, the core a session reads in every phase, and names no
    module or conditional workflow file."""
    out = hook(tmp_path, home, "digest", "Phase: design", SAMPLES[0])
    core = read(os.path.join(BRIDGE, "commands", "supervisor.md"))
    digest = core[core.index("<!-- digest:start -->") + len("<!-- digest:start -->"):core.index("<!-- digest:end -->")]
    assert "**Standing rules.**" in digest and digest.strip() in out.replace("\r\n", "\n"), out[:400]
    assert W not in out, out
