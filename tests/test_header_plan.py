"""TASK-048, the supervisor's acceptance tests (R-059; D-002): the plan's and the briefs' headers read first,
the agreement of each header with its prose, the historic mark, and the one plan-id reader over every plan file.

enforces: docs/DESIGN.md, "Change: release B2", "The records and their headers" (the build-plan and brief rows),
"Three kinds of record, one rule each" (2) and (1) for the briefs, "The fallback readers, one copy each" with the
retired readings (5), (6) and (11), and "Header first; fallback; malformed"; docs/BUILD_PLAN.md, TASK-048's Done
when; R-059.

The fixed forms these tests pin, which the brief repeats:
- plan-check.py prints `HEADER MALFORMED: <path>:<line> <what>` and exits 2 on a malformed plan header, and
  `HEADER DISAGREES: <id> <field>` or `HEADER DISAGREES: <stage> <field>` (a shape failure, exit 1) where a
  header field differs from its prose under the design's normalisations; an increment in the header with no
  heading, or a heading with no header entry, is a failure naming the ID.
- a `historic: true` increment is exempt from the shape rules only where the merged set read from `--base`
  holds its ID; the mark on an unmerged increment is a failure naming it; under `--no-git` the mark is accepted
  with a `note:` line naming the increments not re-checked; a `--base` beginning with `-` exits 2.
- a `Scope:` entry with an unbalanced parenthesis is a shape failure (`SHAPE: <id> ...`) for an unmerged
  increment and read as today for a merged one.
- scope-check.py prints `HEADER MALFORMED: <path>:<line> <what>` and `HEADER DISAGREES: <key>`, each exit 2.
- completion-check.py prints `HEADER MALFORMED: <path>:<line> <what>` (exit 2) and `HEADER DISAGREES:
  satisfies` (exit 1) where an R-id that a `Satisfies:` line anywhere in a plan file's body names stands in no
  increment's header `satisfies`; for a file with no header only an increment's own `Satisfies:` line counts.
- bridge-run.py refuses with exit 125 and `bridge-run: refused - header: ` naming the brief and the line for a
  malformed brief header, and `bridge-run: refused - header: disagrees <key>` for a disagreeing one;
  review-guard.py refuses a snapshot the same way (`review-guard: refused - header: `) on the branch's first
  brief, comparing `merge_unit`, `id` and `round`.
- bridge_env.plan_increment_ids(folder) reads every docs/BUILD_PLAN*.md; bridge_env.brief_satisfies(text)
  returns the R-ids of the brief's `Satisfies:` line in order; bridge_env.merge_unit_ids(text) reads a brief's
  header first.

The supervisor's cases stand above the marker at the end of this file. The builder adds its own cases below the
marker and edits nothing above it.
"""
import ast
import copy
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

import test_task032_supervisor_launcher as t32  # noqa: E402  (the launcher's lab, reused as it stands)

DASH = chr(0x2014)
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
PLAN_CHECK = os.path.join(BRIDGE, "plan-check.py")
SCOPE_CHECK = os.path.join(BRIDGE, "scope-check.py")
COMPLETION_CHECK = os.path.join(BRIDGE, "completion-check.py")
GUARD = os.path.join(BRIDGE, "review-guard.py")


def need(name):
    obj = getattr(bridge_env, name, None)
    assert obj is not None, "bridge_env.%s is missing (TASK-048)" % name
    return obj


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV, timeout=120,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def run(prog, repo, *args):
    p = subprocess.run([sys.executable, prog] + [str(a) for a in args], cwd=str(repo), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ENV, timeout=120,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout + p.stderr


def lines_starting(out, prefix):
    return [l for l in out.splitlines() if l.startswith(prefix)]


# ---------------------------------------------------------------- the plan fixture, prose and header from one table

def q(s):
    return '"%s"' % s


def flow(items):
    return "[" + ", ".join(q(x) for x in items) + "]"


STAGES = [
    {"name": "Stage 1 %s the parser" % DASH, "demo": "the parser runs.", "incs": [
        {"id": "TASK-001", "title": "parser",
         "lines": ["Parent: none", "Depends on: none", "Parallel: no", "Diagrams: none", "Satisfies: R-001",
                   "Scope: src/parse.py; tests/test_parse.py"],
         "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [],
               "scope": ["src/parse.py", "tests/test_parse.py"], "satisfies": ["R-001"], "historic": False}},
        {"id": "TASK-002", "title": "writer",
         "lines": ["Depends on: TASK-001", "Parallel: yes", "Satisfies: R-002, R-003", "Scope: src/write.py; src/out/"],
         "h": {"kind": "increment", "parent": None, "depends_on": ["TASK-001"], "parallel": True, "diagrams": [],
               "scope": ["src/write.py", "src/out/"], "satisfies": ["R-002", "R-003"], "historic": False}},
    ]},
    {"name": "Stage 2 %s the export" % DASH, "demo": None, "incs": [
        {"id": "TASK-003", "title": "export",
         "lines": ["Kind: increment", "Depends on: TASK-002", "Satisfies: R-004", "Scope: src/export.py"],
         "h": {"kind": "increment", "parent": None, "depends_on": ["TASK-002"], "parallel": False, "diagrams": [],
               "scope": ["src/export.py"], "satisfies": ["R-004"], "historic": False}},
    ]},
]


def plan_prose(stages):
    out = ["# Plan", ""]
    for st in stages:
        out.append("## " + st["name"])
        if st["demo"]:
            out.append("Demonstration: " + st["demo"])
        out.append("")
        for inc in st["incs"]:
            out.append("### %s %s %s" % (inc["id"], DASH, inc["title"]))
            out.extend(inc["lines"])
            out.append("")
    return "\n".join(out) + "\n"


def plan_header(stages, demo=None):
    """The header in the subset's form; `demo` overrides a stage's demonstration by index."""
    out = ["---", "record: build-plan", "header: 1", "stages:"]
    for si, st in enumerate(stages):
        shown = bool(st["demo"]) if not demo or si not in demo else demo[si]
        out += ["  - name: " + q(st.get("hname", st["name"])), "    demonstration: " + ("true" if shown else "false"),
                "    increments:"]
        for inc in st["incs"]:
            h = inc["h"]
            out += ["      - id: " + inc.get("hid", inc["id"]),
                    "        title: " + q(inc.get("htitle", inc["title"])),
                    "        kind: " + h["kind"],
                    "        parent: " + (q(h["parent"]) if h["parent"] else "null"),
                    "        depends_on: " + flow(h["depends_on"]),
                    "        parallel: " + ("true" if h["parallel"] else "false"),
                    "        diagrams: " + flow(h["diagrams"]),
                    "        scope: " + flow(h["scope"]),
                    "        satisfies: " + flow(h["satisfies"]),
                    "        deferred: null",
                    "        historic: " + ("true" if h["historic"] else "false")]
    out.append("---")
    return "\n".join(out) + "\n"


def plan_text(stages=None, header=True, demo=None):
    stages = STAGES if stages is None else stages
    return (plan_header(stages, demo) if header else "") + plan_prose(stages)


def plan_repo(tmp_path, text, merged=("TASK-001",), name="ws"):
    r = tmp_path / name
    (r / "docs").mkdir(parents=True)
    (r / "handoff").mkdir()
    (r / "docs" / "BUILD_PLAN.md").write_text(text, encoding="utf-8", newline="")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    for tid in merged:
        git(r, "commit", "-q", "--allow-empty", "-m", "%s: merged (#1)" % tid)
    return r


def plan_check(repo, *args):
    return run(PLAN_CHECK, repo, "--base", "main", *args)


def answer(out):
    """The lines that are the check's answer: READY, TOGETHER and every failure, notes aside."""
    return [l for l in out.splitlines() if not l.startswith("note:")]


# ---------------------------------------------------------------- plan-check: header first, the same answer

def test_r059_plan_check_reads_the_header_and_gives_the_fallbacks_answer(tmp_path):
    # The header that agrees with its prose gives exactly the answer the header-less plan gives.
    rc_h, out_h = plan_check(plan_repo(tmp_path, plan_text(), name="with"))
    rc_p, out_p = plan_check(plan_repo(tmp_path, plan_text(header=False), name="without"))
    assert rc_p == 0, out_p                       # precondition: the fixture is a clean plan
    assert rc_h == 0 and answer(out_h) == answer(out_p), (out_h, out_p)
    assert not lines_starting(out_h, "HEADER"), out_h


def _variant(mutate):
    stages = copy.deepcopy(STAGES)
    mutate(stages)
    return stages


DISAGREE = [
    ("parallel", lambda s: s[0]["incs"][1]["h"].update(parallel=False), "TASK-002 parallel"),
    ("title", lambda s: s[0]["incs"][0].update(htitle="the parser"), "TASK-001 title"),
    ("scope-folder-slash", lambda s: s[0]["incs"][1]["h"].update(scope=["src/write.py", "src/out"]), "TASK-002 scope"),
    ("satisfies", lambda s: s[0]["incs"][1]["h"].update(satisfies=["R-002"]), "TASK-002 satisfies"),
    ("depends-on", lambda s: s[1]["incs"][0]["h"].update(depends_on=[]), "TASK-003 depends_on"),
    ("parent", lambda s: s[0]["incs"][0]["h"].update(parent="TASK-003"), "TASK-001 parent"),
    ("kind", lambda s: s[1]["incs"][0]["h"].update(kind="group"), "TASK-003 kind"),
    ("diagrams", lambda s: s[0]["incs"][0]["h"].update(diagrams=["D-002"]), "TASK-001 diagrams"),
    ("historic", lambda s: s[1]["incs"][0]["h"].update(historic=True), "TASK-003 historic"),
]


@pytest.mark.parametrize("mutate,token", [(m, t) for _, m, t in DISAGREE], ids=[n for n, _, _ in DISAGREE])
def test_r059_plan_check_fails_a_header_field_that_differs_from_its_line(tmp_path, mutate, token):
    stages = _variant(mutate)
    text = plan_header(stages) + plan_prose(STAGES)
    rc, out = plan_check(plan_repo(tmp_path, text))
    assert rc == 1 and "HEADER DISAGREES: %s" % token in out.splitlines(), out


def test_r059_plan_check_fails_a_line_changed_and_not_its_key(tmp_path):
    prose = _variant(lambda s: s[0]["incs"][1]["lines"].__setitem__(1, "Parallel: no"))
    rc, out = plan_check(plan_repo(tmp_path, plan_header(STAGES) + plan_prose(prose)))
    assert rc == 1 and "HEADER DISAGREES: TASK-002 parallel" in out.splitlines(), out


@pytest.mark.parametrize("which", ["name", "demonstration"], ids=["name", "demonstration"])
def test_r059_plan_check_fails_a_stage_field_that_differs(tmp_path, which):
    if which == "name":
        text = plan_header(_variant(lambda s: s[1].update(hname="Stage 2 %s the exporter" % DASH))) + plan_prose(STAGES)
    else:
        text = plan_header(STAGES, demo={1: True}) + plan_prose(STAGES)
    rc, out = plan_check(plan_repo(tmp_path, text))
    hits = [l for l in lines_starting(out, "HEADER DISAGREES: ") if l.endswith(" " + which) and "Stage 2" in l]
    assert rc == 1 and hits, out


def test_r059_plan_check_holds_the_normalisations(tmp_path):
    # Agreement under the stated normalisations: the filler `none` on Parent, Depends on and Diagrams as an absent
    # line (TASK-001), an absent Kind and Parallel line as `increment` and `false` (TASK-002 has no Kind line,
    # TASK-003 no Parallel line), a folder's trailing slash kept on both sides (TASK-002), Parallel yes as true.
    rc, out = plan_check(plan_repo(tmp_path, plan_text()))
    assert rc == 0 and not lines_starting(out, "HEADER"), out


@pytest.mark.parametrize("side", ["header-only", "heading-only"], ids=["header-only", "heading-only"])
def test_r059_plan_check_pairs_every_increment_with_its_heading(tmp_path, side):
    extra = {"id": "TASK-009", "title": "extra", "lines": ["Satisfies: R-009", "Scope: src/extra.py"],
             "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [],
                   "scope": ["src/extra.py"], "satisfies": ["R-009"], "historic": False}}
    more = _variant(lambda s: s[1]["incs"].append(extra))
    text = plan_header(more) + plan_prose(STAGES) if side == "header-only" else plan_header(STAGES) + plan_prose(more)
    rc, out = plan_check(plan_repo(tmp_path, text))
    named = [l for l in out.splitlines() if "TASK-009" in l and l.startswith(("SHAPE: ", "HEADER DISAGREES: "))]
    assert rc == 1 and named, out


@pytest.mark.parametrize("fault,line", [("tab", 8), ("kind", 1)], ids=["tab", "schema"])
def test_r059_plan_check_refuses_a_malformed_header(tmp_path, fault, line):
    header = plan_header(STAGES)
    if fault == "tab":
        lines = header.split("\n")
        lines[line - 1] = lines[line - 1].replace("      - id:", "      -\tid:")
        assert "\t" in lines[line - 1], lines[line - 1]
        header = "\n".join(lines)
    else:
        header = header.replace("kind: increment", "kind: feature", 1)
    rc, out = plan_check(plan_repo(tmp_path, header + plan_prose(STAGES)))
    hits = lines_starting(out, "HEADER MALFORMED: docs/BUILD_PLAN.md:")
    assert rc == 2 and hits, out
    if fault == "tab":
        assert hits[0].startswith("HEADER MALFORMED: docs/BUILD_PLAN.md:%d " % line), hits


# ---------------------------------------------------------------- plan-check: the historic mark and the merged set

HISTORIC = [
    {"name": "Stage 1 %s the early work" % DASH, "demo": "the early work runs.", "incs": [
        {"id": "TASK-001", "title": "the first thing", "lines": ["Done when: it works."],
         "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [], "scope": [],
               "satisfies": [], "historic": True}},
        {"id": "TASK-002", "title": "the second thing", "lines": ["Done when: it works."],
         "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [], "scope": [],
               "satisfies": [], "historic": True}},
        {"id": "TASK-003", "title": "the new thing",
         "lines": ["Kind: increment", "Parallel: no", "Satisfies: R-001", "Scope: src/new.py"],
         "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [],
               "scope": ["src/new.py"], "satisfies": ["R-001"], "historic": False}},
    ]},
]


def test_r059_historic_increments_merged_on_the_base_are_exempt_from_the_shape_rules(tmp_path):
    bare = plan_repo(tmp_path, plan_prose(HISTORIC), merged=("TASK-001", "TASK-002"), name="bare")
    rc, out = plan_check(bare)
    assert "SHAPE: TASK-001 has no Scope" in out, out          # precondition: the TDP's shape noise, header-less
    marked = plan_repo(tmp_path, plan_header(HISTORIC) + plan_prose(HISTORIC), merged=("TASK-001", "TASK-002"),
                       name="marked")
    rc, out = plan_check(marked)
    assert rc == 0, out
    assert not [l for l in out.splitlines() if l.startswith(("SHAPE: TASK-001", "SHAPE: TASK-002"))], out
    assert not lines_starting(out, "HEADER"), out


def test_r059_a_historic_mark_on_an_unmerged_increment_is_a_failure(tmp_path):
    repo = plan_repo(tmp_path, plan_header(HISTORIC) + plan_prose(HISTORIC), merged=("TASK-001",))
    rc, out = plan_check(repo)
    named = [l for l in out.splitlines() if "TASK-002" in l and not l.startswith(("note:", "READY:"))]
    assert rc == 1 and named, out
    assert not [l for l in out.splitlines() if "TASK-001" in l and l.startswith(("SHAPE:", "HEADER"))], out


def test_r059_the_merged_set_is_read_from_the_base_named(tmp_path):
    # The subjects that merge the historic IDs stand on a branch other than main: `--base` names it.
    repo = plan_repo(tmp_path, plan_header(HISTORIC) + plan_prose(HISTORIC), merged=())
    git(repo, "switch", "-q", "-c", "elsewhere")
    git(repo, "commit", "-q", "--allow-empty", "-m", "TASK-001: first (#1)")
    git(repo, "commit", "-q", "--allow-empty", "-m", "TASK-002: second (#2)")
    git(repo, "switch", "-q", "main")
    rc, out = run(PLAN_CHECK, repo, "--base", "elsewhere")
    assert rc == 0 and not lines_starting(out, "SHAPE: TASK-00"), out
    rc, out = run(PLAN_CHECK, repo, "--base", "main")
    assert rc == 1, out


def test_r059_under_no_git_the_mark_is_accepted_with_a_note(tmp_path):
    repo = plan_repo(tmp_path, plan_header(HISTORIC) + plan_prose(HISTORIC), merged=())
    rc, out = run(PLAN_CHECK, repo, "--no-git")
    notes = [l for l in lines_starting(out, "note:") if "TASK-001" in l and "TASK-002" in l]
    assert rc == 0 and notes, out


def test_r059_a_base_beginning_with_a_dash_is_refused(tmp_path):
    repo = plan_repo(tmp_path, plan_text())
    rc, out = run(PLAN_CHECK, repo, "--base=-c")
    assert rc == 2 and "Traceback" not in out, out


UNBALANCED = "Scope: src/export.py (the writer; its tests)"


def test_r059_an_unbalanced_parenthesis_in_an_unmerged_scope_is_a_shape_failure(tmp_path):
    prose = _variant(lambda s: s[1]["incs"][0]["lines"].__setitem__(3, UNBALANCED))
    rc, out = plan_check(plan_repo(tmp_path, plan_prose(prose)))
    hits = [l for l in lines_starting(out, "SHAPE: TASK-003") if "parenthes" in l]
    assert rc == 1 and hits, out


def test_r059_an_unbalanced_parenthesis_in_a_merged_scope_is_read_as_today(tmp_path):
    prose = _variant(lambda s: s[0]["incs"][0]["lines"].__setitem__(5, "Scope: src/parse.py (the reader; its tests)"))
    rc, out = plan_check(plan_repo(tmp_path, plan_prose(prose), merged=("TASK-001",)))
    assert not [l for l in out.splitlines() if l.startswith("SHAPE: TASK-001")], out


# ---------------------------------------------------------------- the briefs: scope-check, the brief's checker

def brief_header(id_="TASK-001", rnd=1, satisfies=("R-001",), scope=("src/core/a.py", "docs/BUILDER_NOTES.md"),
                 merge_unit=None, blocking_class=None):
    out = ["---", "record: brief", "header: 1", "id: " + id_, "round: %d" % rnd, "satisfies: " + flow(satisfies),
           "scope: " + flow(scope), "merge_unit: " + (flow(merge_unit) if merge_unit is not None else "null"),
           "blocking_class: " + (q(blocking_class) if blocking_class else "null"), "---"]
    return "\n".join(out) + "\n"


def brief_prose(id_="TASK-001", extra=""):
    return ("# %s: the fixture\n\nSatisfies: R-001 - parse the file\n%s\n## Objective\nFixture.\n\n## Scope\n"
            "- src/core/a.py\n- docs/BUILDER_NOTES.md\n\n## Constraints\n- none\n" % (id_, extra))


@pytest.fixture
def scope_repo(tmp_path):
    r = tmp_path / "ws"
    (r / "src" / "core").mkdir(parents=True)
    (r / "docs").mkdir()
    (r / "handoff").mkdir()
    (r / "src" / "core" / "a.py").write_text("A = 1\n", encoding="utf-8")
    (r / "docs" / "BUILDER_NOTES.md").write_text("# notes\n", encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    return r


def checkpoint(repo, name, text):
    (repo / "handoff" / name).write_text(text, encoding="utf-8", newline="")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "checkpoint: " + name)
    (repo / "src" / "core" / "a.py").write_text("A = 2\n", encoding="utf-8")
    return "handoff/" + name


def test_r059_scope_check_reads_an_agreeing_brief_header_as_the_prose(scope_repo):
    b = checkpoint(scope_repo, "TASK-001.md", brief_header() + brief_prose())
    rc, out = run(SCOPE_CHECK, scope_repo, b)
    assert rc == 0 and "VERDICT: SCOPE CLEAN" in out and "HEADER" not in out, out


BRIEF_DISAGREE = [
    ("scope", dict(scope=("src/core/b.py", "docs/BUILDER_NOTES.md")), "", "TASK-001.md"),
    ("satisfies", dict(satisfies=("R-002",)), "", "TASK-001.md"),
    ("id", dict(id_="TASK-002"), "", "TASK-001.md"),
    ("round", dict(rnd=1), "", "TASK-001-r2.md"),
    ("merge_unit", dict(merge_unit=("TASK-001",)), "Merge unit: TASK-001 TASK-002\n", "TASK-001.md"),
    ("blocking_class", dict(blocking_class="security"), "Blocking class: behaviour - the fixture's finding\n",
     "TASK-001.md"),
]


@pytest.mark.parametrize("key,over,extra,name", [b for b in BRIEF_DISAGREE], ids=[b[0] for b in BRIEF_DISAGREE])
def test_r059_scope_check_fails_a_brief_key_that_differs_from_its_prose(scope_repo, key, over, extra, name):
    b = checkpoint(scope_repo, name, brief_header(**over) + brief_prose(extra=extra))
    rc, out = run(SCOPE_CHECK, scope_repo, b)
    assert rc == 2 and "HEADER DISAGREES: %s" % key in out.splitlines(), out


def test_r059_scope_check_agrees_on_a_merge_unit_and_a_class_line(scope_repo):
    text = brief_header(merge_unit=("TASK-001", "TASK-002"), blocking_class="behaviour") + brief_prose(
        extra="Merge unit: TASK-001 TASK-002\nBlocking class: behaviour - the fixture's finding\n")
    b = checkpoint(scope_repo, "TASK-001.md", text)
    rc, out = run(SCOPE_CHECK, scope_repo, b)
    assert rc == 0 and "HEADER" not in out, out


def test_r059_scope_check_refuses_a_malformed_brief_header(scope_repo):
    text = brief_header().replace("round: 1", "round:\t1") + brief_prose()
    b = checkpoint(scope_repo, "TASK-001.md", text)
    rc, out = run(SCOPE_CHECK, scope_repo, b)
    assert rc == 2 and lines_starting(out, "HEADER MALFORMED: handoff/TASK-001.md:5 "), out


# ---------------------------------------------------------------- completion-check: satisfies from the headers

REGISTER = """| ID | Requirement | Source | Status | Evidence |
|---|---|---|---|---|
| R-001 | parse the file | owner | built | tests/test_parse.py |
| R-002 | write the file | owner | built | tests/test_write.py |
| R-003 | show a graph | owner | planned | - |
| R-004 | old thing | owner | built | tests/test_old.py |
"""
C_STAGES = [
    {"name": "Stage 1", "demo": "the parser runs.", "incs": [
        {"id": "TASK-001", "title": "parser", "lines": ["Satisfies: R-001, R-004", "Scope: src/parse.py"],
         "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [],
               "scope": ["src/parse.py"], "satisfies": ["R-001", "R-004"], "historic": False}},
        {"id": "TASK-002", "title": "writer, which also mentions R-003 in prose but does not satisfy it",
         "lines": ["Satisfies: R-002", "Scope: src/write.py"],
         "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [],
               "scope": ["src/write.py"], "satisfies": ["R-002"], "historic": False}},
    ]},
]
BOLD = "**Satisfies**: R-003\n\n"


def completion_repo(tmp_path, plan):
    r = tmp_path / "ws"
    for d in ("docs", "tests", "src"):
        (r / d).mkdir(parents=True)
    (r / "docs" / "REQUIREMENTS.md").write_text(REGISTER, encoding="utf-8")
    (r / "docs" / "BUILD_PLAN.md").write_text(plan, encoding="utf-8", newline="")
    for name, rid in (("test_parse.py", "R-001"), ("test_write.py", "R-002"), ("test_old.py", "R-004")):
        (r / "tests" / name).write_text("def test_it():  # %s\n    assert True\n" % rid, encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    return r


def with_bold(prose):
    return prose.replace("# Plan\n\n", "# Plan\n\n" + BOLD, 1)


def test_r059_completion_check_reads_satisfies_from_the_headers(tmp_path):
    rc, out = run(COMPLETION_CHECK, completion_repo(tmp_path, plan_text(C_STAGES)), "--mode", "plan")
    assert "UNPLANNED: R-003" in out and "HEADER" not in out, out
    assert "UNPLANNED: R-001" not in out and "UNPLANNED: R-004" not in out, out


def test_r059_a_bold_satisfies_line_outside_an_increment_counts_for_nothing(tmp_path):
    # The retired reading (5): yesterday the whole-text search counted R-003 as planned.
    rc, out = run(COMPLETION_CHECK, completion_repo(tmp_path, with_bold(plan_prose(C_STAGES))), "--mode", "plan")
    assert rc == 1 and "UNPLANNED: R-003" in out, out


def test_r059_a_bold_satisfies_line_beside_a_header_is_a_disagreement(tmp_path):
    plan = plan_header(C_STAGES) + with_bold(plan_prose(C_STAGES))
    rc, out = run(COMPLETION_CHECK, completion_repo(tmp_path, plan), "--mode", "plan")
    assert rc == 1 and "HEADER DISAGREES: satisfies" in out.splitlines(), out


def test_r059_completion_check_refuses_a_malformed_plan_header(tmp_path):
    plan = plan_header(C_STAGES).replace("historic: false", "historic: maybe", 1) + plan_prose(C_STAGES)
    rc, out = run(COMPLETION_CHECK, completion_repo(tmp_path, plan), "--mode", "plan")
    assert rc == 2 and lines_starting(out, "HEADER MALFORMED: docs/BUILD_PLAN.md:"), out


# ---------------------------------------------------------------- the one plan-id reader and the brief readers

def test_r059_plan_increment_ids_reads_every_plan_file(tmp_path):
    read = need("plan_increment_ids")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "BUILD_PLAN.md").write_text("# Plan\n\n### TASK-010 %s one\n" % DASH, encoding="utf-8")
    (tmp_path / "docs" / "BUILD_PLAN-2026-11-04.md").write_text(
        plan_header(_variant(lambda s: None)) + plan_prose(STAGES), encoding="utf-8")
    got = set(read(str(tmp_path)))
    assert got == {"TASK-010", "TASK-001", "TASK-002", "TASK-003"}, sorted(got)


def test_r059_the_launcher_sees_an_addendums_increments(tmp_path):
    lab = t32.Lab(tmp_path, branch="task-010")
    t32.write_plan(lab, "TASK-010")
    (lab.root / "docs" / "BUILD_PLAN-2026-11-04.md").write_bytes(
        ("# Addendum\n\n### TASK-015 %s two\n\nKind: increment\n" % DASH).encode("utf-8"))
    t32.write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-015\n")
    t32.assert_ran(t32.launch(lab, t32.build("TASK-010")))


def test_r059_brief_satisfies_reads_the_line_in_order():
    read = need("brief_satisfies")
    assert list(read("# T\n\nSatisfies: R-061, R-057 - the two rows\n\n## Scope\n- a.py\n")) == ["R-061", "R-057"]
    assert list(read("# T\n\n## Scope\n- a.py\n")) == []


def test_r059_merge_unit_ids_reads_the_header_first():
    text = brief_header(merge_unit=("TASK-010", "TASK-015")) + brief_prose(extra="Merge unit: TASK-010 TASK-015\n")
    assert tuple(bridge_env.merge_unit_ids(text)) == ("TASK-010", "TASK-015")
    header_only = brief_header(merge_unit=("TASK-010", "TASK-015")) + brief_prose()
    assert bridge_env.merge_unit_ids(header_only) is not None and tuple(bridge_env.merge_unit_ids(header_only)) == (
        "TASK-010", "TASK-015")


MOVED = ["parse_scope", "split_entry", "brief_satisfies", "plan_r_ids_outside_headers", "HEAD_RX", "FIELD_RX", "DEMO_RX"]


@pytest.mark.parametrize("name", MOVED, ids=MOVED)
def test_r059_the_moved_readers_live_in_bridge_env(name):
    need(name)


# ---------------------------------------------------------------- the launcher's and the guard's header refusals

def lab_brief(lab, name, header, extra=""):
    text = header + "# %s\n\n## Objective\nFixture brief.\n%s\n## Scope\n- a.py\n" % (name, extra)
    (lab.root / "handoff" / (name + ".md")).write_bytes(text.encode("ascii"))


def test_r059_the_launcher_runs_an_agreeing_brief_header(tmp_path):
    lab = t32.Lab(tmp_path)
    lab_brief(lab, "TASK-001", brief_header(satisfies=(), scope=("a.py",)))
    t32.assert_ran(t32.launch(lab, t32.build("TASK-001")))


def test_r059_the_launcher_refuses_a_disagreeing_brief_header(tmp_path):
    lab = t32.Lab(tmp_path)
    lab_brief(lab, "TASK-001", brief_header(satisfies=(), scope=("b.py",)))
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-001")), "bridge-run: refused - header: ")
    assert line.startswith("bridge-run: refused - header: disagrees scope"), line


def test_r059_the_launcher_refuses_a_malformed_brief_header(tmp_path):
    lab = t32.Lab(tmp_path)
    lab_brief(lab, "TASK-001", brief_header(satisfies=(), scope=("a.py",)).replace("round: 1", "round:\t1"))
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-001")), "bridge-run: refused - header: ")
    assert "TASK-001.md" in line and ":5" in line, line


def guard_repo(tmp_path, brief_text):
    r = tmp_path / "gws"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / ".gitignore").write_text("run/\n", encoding="utf-8")
    (r / "a.py").write_text("1\n", encoding="utf-8")
    (r / "run" / "review").mkdir(parents=True)
    (r / "run" / "review" / "REVIEW-TASK-001.diff").write_text("d\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    git(r, "checkout", "-q", "-b", "task-001")
    (r / "handoff").mkdir()
    (r / "handoff" / "TASK-001.md").write_text(brief_text, encoding="utf-8", newline="")
    git(r, "add", "-A")
    git(r, "add", "-f", "run/review/REVIEW-TASK-001.diff")
    git(r, "commit", "-q", "-m", "TASK-001")
    return r


UNIT = "Merge unit: TASK-001 TASK-002\n"


def test_r059_the_guard_snapshots_on_an_agreeing_first_brief(tmp_path):
    repo = guard_repo(tmp_path, brief_header(merge_unit=("TASK-001", "TASK-002")) + brief_prose(extra=UNIT))
    rc, out = run(GUARD, repo, "snapshot", "TASK-001")
    assert rc == 0, out


GUARD_DISAGREE = [
    ("merge_unit", dict(merge_unit=("TASK-001",))),
    ("id", dict(id_="TASK-002", merge_unit=("TASK-001", "TASK-002"))),
    ("round", dict(rnd=2, merge_unit=("TASK-001", "TASK-002"))),
]


@pytest.mark.parametrize("key,over", GUARD_DISAGREE, ids=[k for k, _ in GUARD_DISAGREE])
def test_r059_the_guard_refuses_a_disagreeing_first_brief(tmp_path, key, over):
    repo = guard_repo(tmp_path, brief_header(**over) + brief_prose(extra=UNIT))
    rc, out = run(GUARD, repo, "snapshot", "TASK-001")
    assert rc == 125 and out.startswith("review-guard: refused - header: disagrees %s" % key), out


def test_r059_the_guard_refuses_a_malformed_first_brief(tmp_path):
    text = brief_header(merge_unit=("TASK-001", "TASK-002")).replace("round: 1", "round:\t1") + brief_prose(extra=UNIT)
    repo = guard_repo(tmp_path, text)
    rc, out = run(GUARD, repo, "snapshot", "TASK-001")
    assert rc == 125 and out.startswith("review-guard: refused - header: ") and "TASK-001.md" in out, out


# ---------------------------------------------------------------- the retired readings (5), (6) and (11), as uses

def _tree(name):
    with open(os.path.join(BRIDGE, name), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):                     # docstrings out: a description never matches (KP-073)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) and isinstance(
                    first.value.value, str):
                node.body = node.body[1:] or [ast.Pass()]
    return tree


def _re_patterns(tree):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(
                node.func.value, ast.Name) and node.func.value.id == "re" and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                out.append(arg.value)
    return out


def test_r059_completion_check_keeps_no_satisfies_search_of_its_own():
    tree = _tree("completion-check.py")
    assert not [p for p in _re_patterns(tree) if "Satisfies" in p], "reading (5) stands"
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "plan_r_ids_outside_headers"]
    assert calls, "completion-check does not call bridge_env.plan_r_ids_outside_headers"


@pytest.mark.parametrize("name", ["brief_scope", "merged_ids"], ids=["reading-6", "reading-11"])
def test_r059_plan_check_keeps_no_retired_reader(name):
    defs = [n.name for n in ast.walk(_tree("plan-check.py")) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    assert name not in defs, "plan-check.py still defines %s" % name


def test_r059_plan_check_reads_the_one_merged_set():
    calls = [n for n in ast.walk(_tree("plan-check.py")) if isinstance(n, ast.Attribute) and n.attr == "squash_merged_ids"]
    assert calls, "plan-check does not call bridge_env.squash_merged_ids"


def test_r059_plan_check_compiles_no_heading_or_field_regex_of_its_own():
    tree = _tree("plan-check.py")
    own = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            f = node.value.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "re" and f.attr == "compile":
                own += [t.id for t in node.targets if isinstance(t, ast.Name) and t.id in ("HEAD_RX", "FIELD_RX", "DEMO_RX")]
    assert not own, "plan-check.py compiles its own %s" % ", ".join(own)


# ---------------------------------------------------------------- builder's cases below this line
