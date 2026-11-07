"""TASK-047, the supervisor's acceptance tests (R-058; D-002): the status file's header read first by its
six readers through bridge_env, and the one fallback reading of each field where the file has no header.

enforces: docs/DESIGN.md, "Change: release B2", "The records and their headers" (the status row), "The
fallback readers, one copy each" with its enumerated retired readings (1) to (4), and "Header first;
fallback; malformed"; docs/BUILD_PLAN.md, TASK-047's Done when; R-058.

The fixed forms these tests pin, which the brief repeats:
- bridge_env.status_fallback(text) returns a dict of exactly the six keys (phase, workflows,
  awaiting_user_on, bridge_version, stage, open_issues), each read from the prose by its one copy:
  phase the first word of the `Phase:` value (the hooks' field() regex) in lower case; awaiting_user_on
  "" for no wait (the loop guard's rule), else the value; bridge_version the first YYYY.MM.DD stamp with
  an optional letter in the value, else ""; workflows the parts status_workflows reads; stage the
  `Stage:` value (conformance-check's status_field regex); open_issues the segments of the `Open
  issues:` value (evaluate-reports' status_segments). An absent line gives "" or [].
- bridge_env.status_workflows(text) returns (parts, problems): parts a list of
  {"type", "subtype", "traits"} in line order, a `not yet classified` line giving none; problems a
  list of strings, one per line the strict grammar refuses, worded as workflow-check's check_status
  words it, never a silent none.
- bridge_env.status_values(text) returns (values, malformed, disagrees): values the header's six keys
  where the text has a well-formed header (read_header raises nothing and check_header finds nothing),
  else status_fallback(text); malformed None, or (line, what): a HeaderError's line, or 1 for a
  schema fault; disagrees the keys header_agrees names against status_fallback(text), else [].
- The hooks print `header malformed: <path>:<line>`, `header disagrees: <key>` and `workflows line
  refused: <reason>`; the checkers print `HEADER MALFORMED: <path>:<line> <what>` and exit 2;
  inventory-check prints `HEADER DISAGREES: <key>`.

The supervisor's cases stand above the marker at the end of this file. The builder adds its own cases
below the marker and edits nothing above it.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures", "workflows")
OPEN_LIST = os.path.join(BRIDGE, "workflow", "open-list.md")
VERSION = open(os.path.join(BRIDGE, "VERSION"), encoding="utf-8").read().strip()
ARROW = chr(0x2192)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
W = "~/.claude/cursor-bridge/workflow/"
P = W + "phases/"

WEB = ["Has screens", "Installable", "External services", "Spends money", "Long-running process", "AI models"]
PARTS = {
    "bridge": [("Host Extension Development", "Claude Code Extension", ["Installable"])],
    "reangle": [("Web App Development", "Local Web App", WEB)],
    "tdp": [("Own-Computer Software Development", "Local Service Software", WEB[1:])],
    "video-factory": [("Web App Development", "Local Web App", WEB)],
}
NAMES = sorted(PARTS)


def need(name):
    obj = getattr(bridge_env, name, None)
    assert obj is not None, "bridge_env.%s is missing (TASK-047)" % name
    return obj


def fixture(name):
    with open(os.path.join(FIXTURES, name + ".status.md"), encoding="utf-8", newline="") as f:
        return f.read()


def header(phase="building", parts=(), awaiting="", version="", stage="", issues=(), nl="\n", replace=None):
    """A status header written from the design's table, in the subset's form."""
    lines = ["---", "record: project-status", "header: 1", "phase: " + phase]
    if parts:
        lines.append("workflows:")
        for kind, sub, traits in parts:
            lines.append('  - type: "%s"' % kind)
            lines.append("    subtype: %s" % (('"%s"' % sub) if sub else "null"))
            lines.append("    traits: [%s]" % ", ".join('"%s"' % t for t in traits))
    else:
        lines.append("workflows: []")
    lines.append('awaiting_user_on: "%s"' % awaiting)
    lines.append('bridge_version: "%s"' % version)
    lines.append('stage: "%s"' % stage)
    lines.append("open_issues: [%s]" % ", ".join('"%s"' % i for i in issues))
    lines.append("---")
    text = nl.join(lines) + nl
    if replace:
        text = text.replace(replace[0], replace[1])
    return text


def with_header(name, **values):
    text = fixture(name)
    nl = "\r\n" if "\r\n" in text else "\n"
    return header(parts=PARTS[name], nl=nl, **values) + text


def as_parts(parts):
    return [{"type": t, "subtype": s, "traits": list(tr)} for t, s, tr in parts]


def write(path, text):
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(str(path), "w", encoding="utf-8", newline="") as f:
        f.write(text)


def env_with_home(home=None):
    env = dict(os.environ)
    if home is not None:
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
    return env


def run(args, cwd=None, stdin=None, env=None):
    p = subprocess.run([sys.executable] + [str(a) for a in args], cwd=str(cwd) if cwd else None, input=stdin,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env or env_with_home(),
                       creationflags=NO_WINDOW)
    return p.returncode, p.stdout, p.stderr


# A tab inside the block: read_header refuses it on the line it stands on.
TAB_HEADER = header(phase="done", replace=("phase: done", "phase:\tdone"))
# A value the schema refuses: read_header reads it, check_header fails it (line 1).
SCHEMA_HEADER = header(phase="paused")


def tab_line(text):
    error = need("HeaderError")
    with pytest.raises(error) as caught:
        need("read_header")(text)
    return caught.value.line


# --- the fallback readers, one copy each, in bridge_env ---------------------------------------------------------

FIELD_CASES = [
    ("phase-plain", "Phase: building\n", "phase", "building"),
    ("phase-with-stage", "Phase: building (Stage 3 of 5)\n", "phase", "building"),
    ("phase-bold-capital", "**Phase:** Changing\n", "phase", "changing"),
    ("phase-bullet", "- Phase: done\n", "phase", "done"),
    ("phase-absent", "Stage: H1\n", "phase", ""),
    ("awaiting-nothing", "Awaiting user on: nothing\n", "awaiting_user_on", ""),
    ("awaiting-capital", "Awaiting user on: Nothing\n", "awaiting_user_on", ""),
    ("awaiting-na", "Awaiting user on: n/a\n", "awaiting_user_on", ""),
    ("awaiting-angled", "Awaiting user on: <nothing>\n", "awaiting_user_on", ""),
    ("awaiting-none-note", "Awaiting user on: none (the owner has answered)\n", "awaiting_user_on", ""),
    ("awaiting-dash", "Awaiting user on: -\n", "awaiting_user_on", ""),
    ("awaiting-absent", "Phase: building\n", "awaiting_user_on", ""),
    ("awaiting-real", "Awaiting user on: the owner's yes on the plan\n", "awaiting_user_on", "the owner's yes on the plan"),
    ("version-plain", "Bridge version: 2026.11.03a\n", "bridge_version", "2026.11.03a"),
    ("version-bold-ticked", "**Bridge version:** `2026.11.03a` (calibrated today)\n", "bridge_version", "2026.11.03a"),
    ("version-in-words", "Bridge version: calibrated to 2026.10.30d\n", "bridge_version", "2026.10.30d"),
    ("version-no-stamp", "Bridge version: 1.2\n", "bridge_version", ""),
    ("version-absent", "Phase: building\n", "bridge_version", ""),
    ("stage-plain", "Stage: H1 in progress\n", "stage", "H1 in progress"),
    ("stage-absent", "Phase: building\n", "stage", ""),
    ("issues-segments", "Open issues: ISS-001 fixed; ISS-015 to write (PR #3; round 1)\n", "open_issues",
     ["ISS-001 fixed", "ISS-015 to write (PR #3; round 1)"]),
    ("issues-absent", "Phase: building\n", "open_issues", []),
    ("workflows-bridge", "Phase: building\nWorkflows: Host Extension Development %s Claude Code Extension; traits: Installable\n" % ARROW,
     "workflows", as_parts(PARTS["bridge"])),
    ("workflows-unclassified", "Phase: intake\nWorkflows: not yet classified\n", "workflows", []),
    ("workflows-no-traits", "Phase: building\nWorkflows: Web App Development; traits: none\n", "workflows",
     [{"type": "Web App Development", "subtype": None, "traits": []}]),
    ("workflows-two-parts", "Phase: building\nWorkflows: app: Web App Development; traits: Installable\n"
                            "Workflows: site: Web App Development %s Local Web App; traits: none\n" % ARROW, "workflows",
     [{"type": "Web App Development", "subtype": None, "traits": ["Installable"]},
      {"type": "Web App Development", "subtype": "Local Web App", "traits": []}]),
    ("workflows-absent", "Phase: building\n", "workflows", []),
]


@pytest.mark.parametrize("text,key,expected", [c[1:] for c in FIELD_CASES], ids=[c[0] for c in FIELD_CASES])
def test_r058_each_field_has_one_fallback_reading(text, key, expected):
    values = need("status_fallback")("# Project Status\n" + text)
    assert sorted(values) == sorted(["phase", "workflows", "awaiting_user_on", "bridge_version", "stage", "open_issues"])
    assert values[key] == expected


REFUSED = [
    ("prefix-on-a-single-line", "Workflows: main: Host Extension Development %s Claude Code Extension; traits: Installable\n" % ARROW,
     "Workflows line breaks the part-prefix rule"),
    ("no-traits-mark", "Workflows: Host Extension Development\n", "Workflows line must contain '; traits: ' exactly once"),
    ("two-traits-marks", "Workflows: Web App Development; traits: Installable; traits: AI models\n",
     "Workflows line must contain '; traits: ' exactly once"),
]


@pytest.mark.parametrize("line,reason", [c[1:] for c in REFUSED], ids=[c[0] for c in REFUSED])
def test_r058_a_workflows_line_the_grammar_refuses_is_a_problem_never_a_silent_none(line, reason):
    parts, problems = need("status_workflows")("# Project Status\nPhase: building\n" + line)
    assert parts == [] and len(problems) == 1 and reason in problems[0], problems


def test_r058_without_a_header_the_values_are_the_fallbacks():
    text = "# Project Status\nPhase: building\nAwaiting user on: nothing\nBridge version: 2026.11.03a\n"
    assert need("status_values")(text) == (need("status_fallback")(text), None, [])


def test_r058_a_well_formed_header_governs_and_its_disagreements_are_named():
    prose = "# Project Status\nPhase: building\nAwaiting user on: nothing\n"
    values, malformed, disagrees = need("status_values")(header(phase="done") + prose)
    assert malformed is None and disagrees == ["phase"]
    assert values == {"phase": "done", "workflows": [], "awaiting_user_on": "", "bridge_version": "", "stage": "",
                      "open_issues": []}


@pytest.mark.parametrize("bad", ["tab", "schema"], ids=["tab-in-block", "schema-fault"])
def test_r058_a_malformed_header_falls_back_and_names_its_line(bad):
    prose = "# Project Status\nPhase: building\nAwaiting user on: nothing\n"
    text = (TAB_HEADER if bad == "tab" else SCHEMA_HEADER) + prose
    values, malformed, disagrees = need("status_values")(text)
    assert values == need("status_fallback")(text) and values["phase"] == "building" and disagrees == []
    line, what = malformed
    assert line == (tab_line(text) if bad == "tab" else 1) and isinstance(what, str) and what


@pytest.mark.parametrize("name", NAMES, ids=NAMES)
def test_r058_the_four_projects_fixtures_read_alike_by_header_and_by_fallback(name):
    plain = fixture(name)
    fallback = need("status_fallback")(plain)
    assert fallback["phase"] == "building" and fallback["workflows"] == as_parts(PARTS[name])
    assert need("status_values")(plain) == (fallback, None, [])
    assert need("status_values")(with_header(name)) == (fallback, None, [])


# --- the retired readings, matched as uses (KP-073) -------------------------------------------------------------

def code_tree(program):
    with open(os.path.join(BRIDGE, program), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return tree


def names_used(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            out.add(node.id)
        elif isinstance(node, ast.Attribute):
            out.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(node.name)
    return out


def constant_sets(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)) and node.elts and \
                all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts):
            yield frozenset(e.value for e in node.elts)


def calls(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            called = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if called == name:
                yield [a.value for a in node.args if isinstance(a, ast.Constant)]


def test_r058_retired_1_session_starts_forgiving_workflows_parse():
    used = names_used(code_tree("session-start.py"))
    assert not used & {"parse_workflows_tail", "workflows_lines_parsed"}, used & {"parse_workflows_tail", "workflows_lines_parsed"}


def test_r058_retired_2_session_starts_equality_with_four_exact_values():
    assert frozenset(["nothing", "none", "", "-"]) not in set(constant_sets(code_tree("session-start.py")))


def test_r058_retired_3_conformance_checks_bridge_version_regex():
    tree = code_tree("conformance-check.py")
    found = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and "[0-9.]+[a-z]?" in n.value]
    assert found == [], found


def test_r058_retired_4_conformance_checks_own_readings_of_phase():
    tree = code_tree("conformance-check.py")
    assert not [a for a in calls(tree, "status_field") if "Phase" in a], "status_field applied to Phase"
    assert not [a for a in calls(tree, "startswith") if "Phase: " in a], 'line.startswith("Phase: ")'


# --- loop-guard.py ----------------------------------------------------------------------------------------------

GUARD = os.path.join(BRIDGE, "loop-guard.py")


def guard(ws, listed=True):
    data = {"cwd": str(ws), "hook_event_name": "Stop"}
    if listed:
        data["background_tasks"] = []
        data["session_crons"] = []
    return run([GUARD], stdin=json.dumps(data))


@pytest.mark.parametrize("name", NAMES, ids=NAMES)
def test_r058_loop_guard_reads_the_fixture_alike_by_header_and_by_fallback(tmp_path, name):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    ws = tmp_path / "Workspace"
    write(ws / "docs" / "PROJECT_STATUS.md", fixture(name))
    plain = guard(ws)
    write(ws / "docs" / "PROJECT_STATUS.md", with_header(name))
    assert guard(ws) == plain and plain[0] == 2, plain


@pytest.mark.parametrize("prose,code", [("Awaiting user on: the owner's word\n", 0), ("Awaiting user on: nothing\n", 2)],
                         ids=["prose-waits", "prose-does-not-wait"])
def test_r058_loop_guard_on_a_malformed_header_does_what_the_prose_says(tmp_path, prose, code):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    ws = tmp_path / "Workspace"
    write(ws / "docs" / "PROJECT_STATUS.md", TAB_HEADER + "# Project Status\nPhase: building\n" + prose)
    rc, out, err = guard(ws)
    assert rc == code and "Traceback" not in err, err


@pytest.mark.parametrize("key,head,prose", [
    ("phase", {"phase": "done"}, "Phase: building\nAwaiting user on: nothing\n"),
    ("awaiting_user_on", {"awaiting": "the owner's gate"}, "Phase: building\nAwaiting user on: nothing\n"),
], ids=["phase", "awaiting_user_on"])
def test_r058_loop_guard_refuses_the_stop_where_its_two_keys_disagree(tmp_path, key, head, prose):
    ws = tmp_path / "Workspace"
    write(ws / "docs" / "PROJECT_STATUS.md", header(**head) + "# Project Status\n" + prose)
    rc, out, err = guard(ws, listed=False)
    assert rc == 2 and "header disagrees: %s" % key in err, (rc, err)


def test_r058_loop_guard_reads_no_other_key_for_its_disagreement(tmp_path):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    ws = tmp_path / "Workspace"
    prose = "# Project Status\nPhase: building\nAwaiting user on: the owner's gate\nBridge version: 2026.11.03a\n"
    write(ws / "docs" / "PROJECT_STATUS.md", header(awaiting="the owner's gate", version="2026.01.01a") + prose)
    rc, out, err = guard(ws)
    assert rc == 0 and "header disagrees" not in err, (rc, err)


# --- session-start.py -------------------------------------------------------------------------------------------

HOOK = os.path.join(BRIDGE, "session-start.py")


@pytest.fixture(scope="module")
def home(tmp_path_factory):
    """An installed bridge in a temporary home, laid out as bridge-install.py lays it out."""
    h = tmp_path_factory.mktemp("installed") / "home"
    shutil.copytree(os.path.join(ROOT, "bridge", "commands"), str(h / ".claude" / "commands"))
    shutil.copytree(BRIDGE, str(h / ".claude" / "cursor-bridge"), ignore=shutil.ignore_patterns("__pycache__"))
    return h


def pointers(ws, home):
    data = {"cwd": str(ws), "hook_event_name": "SessionStart", "source": "compact"}
    rc, out, err = run([HOOK, "--part", "pointers"], stdin=json.dumps(data), env=env_with_home(home))
    assert rc == 0 and err == "", err
    return out


def named(out):
    return [re.match(r"  - (\S+)", line).group(1) for line in out.split("\n") if line.startswith("  - " + W)]


def hook_status(tmp_path, text):
    ws = tmp_path / "proj" / "Workspace"
    write(ws / "docs" / "PROJECT_STATUS.md", text)
    return ws


@pytest.mark.parametrize("name", NAMES, ids=NAMES)
def test_r058_session_start_reads_the_fixture_alike_by_header_and_by_fallback(tmp_path, home, name):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    ws = hook_status(tmp_path, fixture(name))
    plain = pointers(ws, home)
    write(ws / "docs" / "PROJECT_STATUS.md", with_header(name))
    headed = pointers(ws, home)
    assert headed == plain and P + "delegation-loop.md" in named(plain), headed


@pytest.mark.parametrize("bad", ["tab", "schema"], ids=["tab-in-block", "schema-fault"])
def test_r058_session_start_falls_back_on_a_malformed_header_and_names_its_line(tmp_path, home, bad):
    text = (TAB_HEADER if bad == "tab" else SCHEMA_HEADER) + "# Project Status\nPhase: building\nAwaiting user on: nothing\n"
    out = pointers(hook_status(tmp_path, text), home)
    m = re.search(r"^header malformed: .*PROJECT_STATUS\.md:(\d+)$", out, re.M)
    assert m and int(m.group(1)) == (tab_line(text) if bad == "tab" else 1), out
    assert P + "delegation-loop.md" in named(out), "the prose's phase governs: " + out


BRIDGE_LINE = "Workflows: Host Extension Development %s Claude Code Extension; traits: Installable" % ARROW


@pytest.mark.parametrize("key,head,prose,governs", [
    ("phase", {"phase": "done"}, "Phase: building\nAwaiting user on: nothing\n", "change-cycle"),
    ("awaiting_user_on", {"awaiting": "the owner's gate"}, "Phase: building\nAwaiting user on: nothing\n",
     "WAITING FOR THE OWNER on: the owner's gate"),
    ("bridge_version", {"version": "2026.01.01a"}, "Phase: building\nAwaiting user on: nothing\nBridge version: %s\n" % VERSION,
     "the status file records 2026.01.01a"),
    ("workflows", {}, "Phase: building\n" + BRIDGE_LINE + "\nAwaiting user on: nothing\n", "no conditional file"),
], ids=["phase", "awaiting_user_on", "bridge_version", "workflows"])
def test_r058_session_start_names_each_disagreeing_key_and_the_header_governs(tmp_path, home, key, head, prose, governs):
    out = pointers(hook_status(tmp_path, header(**head) + "# Project Status\n" + prose), home)
    assert re.search(r"^header disagrees: %s$" % key, out, re.M), out
    if governs == "change-cycle":
        assert named(out)[0] == P + "change-cycle.md", out
    elif governs == "no conditional file":
        assert not [n for n in named(out) if n.startswith(W + "types/") or n.startswith(W + "traits/")], out
    else:
        assert governs in out, out


def test_r058_session_start_names_no_disagreement_where_the_header_agrees(tmp_path, home):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    prose = "# Project Status\nPhase: building\n" + BRIDGE_LINE + "\nAwaiting user on: nothing\nBridge version: %s\n" % VERSION
    out = pointers(hook_status(tmp_path, header(parts=PARTS["bridge"], version=VERSION) + prose), home)
    assert "header disagrees" not in out and "header malformed" not in out and W + "types/host-extension.md" in named(out), out


@pytest.mark.parametrize("value", ["n/a", "<nothing>", "nothing (cleared 2026-11-07)", "None yet"],
                         ids=["na", "angled", "nothing-with-note", "none-yet"])
def test_r058_retired_2_session_start_reads_no_wait_by_the_one_normalisation(tmp_path, home, value):
    out = pointers(hook_status(tmp_path, "# Project Status\nPhase: building\nAwaiting user on: %s\n" % value), home)
    assert "WAITING FOR THE OWNER" not in out and "Continue from where the status file says the work is." in out, out


def test_r058_retired_1_session_start_refuses_a_line_the_grammar_refuses(tmp_path, home):
    line = "Workflows: main: Host Extension Development %s Claude Code Extension; traits: Installable" % ARROW
    out = pointers(hook_status(tmp_path, "# Project Status\nPhase: building\n" + line + "\nAwaiting user on: nothing\n"), home)
    assert "workflows line refused: Workflows line breaks the part-prefix rule" in out, out
    assert W + "types/host-extension.md" not in named(out), out


# --- conformance-check.py ---------------------------------------------------------------------------------------

CONFORMANCE = os.path.join(BRIDGE, "conformance-check.py")
STATUS_WORDS = ("Workflows", "Unwritten trait", "Calibrated", "project.json", "HEADER")


def conformance_ws(tmp_path, text):
    from test_conformance_check import make_workspace
    root = tmp_path / "proj"
    root.mkdir(exist_ok=True)
    if not (root / "docs").exists():
        make_workspace(root)
    write(root / "docs" / "PROJECT_STATUS.md", text)
    return root


def conformance(root):
    return run([CONFORMANCE, root, "--offline"])


def status_lines(out):
    return [line for line in out.splitlines() if any(w in line for w in STATUS_WORDS)]


@pytest.mark.parametrize("name", NAMES, ids=NAMES)
def test_r058_conformance_check_reads_the_fixture_alike_by_header_and_by_fallback(tmp_path, name):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    root = conformance_ws(tmp_path, fixture(name))
    rc, plain, err = conformance(root)
    write(root / "docs" / "PROJECT_STATUS.md", with_header(name))
    rc2, headed, err2 = conformance(root)
    assert rc2 == rc and status_lines(headed) == status_lines(plain) and status_lines(plain), headed


@pytest.mark.parametrize("bad", ["tab", "schema"], ids=["tab-in-block", "schema-fault"])
def test_r058_conformance_check_refuses_a_malformed_header(tmp_path, bad):
    text = (TAB_HEADER if bad == "tab" else SCHEMA_HEADER) + "# Project Status\nPhase: building\nWorkflows: not yet classified\n"
    rc, out, err = conformance(conformance_ws(tmp_path, text))
    m = re.search(r"HEADER MALFORMED: .*PROJECT_STATUS\.md:(\d+) \S", out)
    assert rc == 2 and m and int(m.group(1)) == (tab_line(text) if bad == "tab" else 1), (rc, out, err)


def test_r058_retired_3_conformance_check_reads_the_stamp_anywhere_in_the_value(tmp_path):
    from test_conformance_check import verdict
    text = "# Project Status\nBridge version: calibrated to %s\nPhase: building\nWorkflows: not yet classified\n" % VERSION
    rc, out, err = conformance(conformance_ws(tmp_path, text))
    assert verdict(out, "Calibrated to the installed bridge")[0] == "OK", out


def test_r058_retired_4_conformance_checks_grades_read_the_one_phase_value(tmp_path):
    from test_conformance_check import verdict
    text = header(phase="changing", version=VERSION) + \
        "# Project Status\nBridge version: %s\nPhase: intake\nWorkflows: not yet classified\n" % VERSION
    rc, out, err = conformance(conformance_ws(tmp_path, text))
    grade, detail = verdict(out, "Workflows classification")
    assert grade == "NOTE" and "(Phase: changing)" in detail, out


# --- workflow-check.py --status ---------------------------------------------------------------------------------

WORKFLOW_CHECK = os.path.join(BRIDGE, "workflow-check.py")


def workflow_check(path):
    return run([WORKFLOW_CHECK, "--open-list", OPEN_LIST, "--status", path])


@pytest.mark.parametrize("name", NAMES, ids=NAMES)
def test_r058_workflow_check_reads_the_fixture_alike_by_header_and_by_fallback(tmp_path, name):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    path = tmp_path / "PROJECT_STATUS.md"
    write(path, fixture(name))
    plain = workflow_check(path)
    write(path, with_header(name))
    assert workflow_check(path) == plain and plain[0] == 0, plain


@pytest.mark.parametrize("bad", ["tab", "schema"], ids=["tab-in-block", "schema-fault"])
def test_r058_workflow_check_refuses_a_malformed_header(tmp_path, bad):
    path = tmp_path / "PROJECT_STATUS.md"
    text = (TAB_HEADER if bad == "tab" else SCHEMA_HEADER) + fixture("bridge")
    write(path, text)
    rc, out, err = workflow_check(path)
    m = re.search(r"HEADER MALFORMED: .*PROJECT_STATUS\.md:(\d+) \S", out)
    assert rc == 2 and m and int(m.group(1)) == (tab_line(text) if bad == "tab" else 1), (rc, out, err)


# --- inventory-check.py -----------------------------------------------------------------------------------------

INVENTORY_CHECK = os.path.join(BRIDGE, "inventory-check.py")


def inventory(cwd, status, *more):
    return run([INVENTORY_CHECK, "--inventory", "absent-inventory.md", "--changes", "absent-changes.md", "--status", status]
               + list(more), cwd=cwd)


@pytest.mark.parametrize("name", NAMES, ids=NAMES)
def test_r058_inventory_check_reads_the_fixture_alike_by_header_and_by_fallback(tmp_path, name):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    path = tmp_path / "PROJECT_STATUS.md"
    write(path, fixture(name))
    plain = inventory(tmp_path, path)
    write(path, with_header(name))
    assert inventory(tmp_path, path) == plain and "HEADER" not in plain[1], plain


@pytest.mark.parametrize("bad", ["tab", "schema"], ids=["tab-in-block", "schema-fault"])
def test_r058_inventory_check_refuses_a_malformed_header(tmp_path, bad):
    path = tmp_path / "PROJECT_STATUS.md"
    text = (TAB_HEADER if bad == "tab" else SCHEMA_HEADER) + fixture("bridge")
    write(path, text)
    rc, out, err = inventory(tmp_path, path)
    m = re.search(r"HEADER MALFORMED: .*PROJECT_STATUS\.md:(\d+) \S", out)
    assert rc == 2 and m and int(m.group(1)) == (tab_line(text) if bad == "tab" else 1), (rc, out, err)


DISAGREE = [
    ("phase", {"phase": "done"}),
    ("workflows", {"parts": ()}),
    ("awaiting_user_on", {"awaiting": "the owner's gate"}),
    ("bridge_version", {"version": "2026.01.01a"}),
    ("stage", {"stage": "H9"}),
    ("open_issues", {"issues": ("ISS-099 to write",)}),
]


@pytest.mark.parametrize("key,change", DISAGREE, ids=[d[0] for d in DISAGREE])
def test_r058_inventory_check_compares_every_key_with_its_line(tmp_path, key, change):
    text = fixture("bridge")
    values = {"parts": PARTS["bridge"], "nl": "\r\n"}
    values.update(change)
    path = tmp_path / "PROJECT_STATUS.md"
    write(path, header(**values) + text)
    rc, out, err = inventory(tmp_path, path)
    assert re.findall(r"^HEADER DISAGREES: (\S+)", out, re.M) == [key] and rc == 1, out


def test_r058_inventory_checks_caps_count_the_body_after_the_header(tmp_path):
    body = fixture("bridge")
    path = tmp_path / "PROJECT_STATUS.md"
    write(path, header(parts=PARTS["bridge"], nl="\r\n") + body)
    rc, out, err = inventory(tmp_path, path, "--max-lines", "3", "--max-chars", str(len(body) + 5))
    assert "STATUS TOO LONG" not in out and "status: 3 lines / " in out, out
    rc, out, err = inventory(tmp_path, path, "--max-lines", "2")
    assert "STATUS TOO LONG" in out and " is 3 lines / " in out, out
    rc, out, err = inventory(tmp_path, path, "--max-chars", str(len(body) - 10))
    assert "STATUS TOO LONG" in out, out


def test_r058_inventory_checks_help_says_the_caps_count_the_body():
    rc, out, err = run([INVENTORY_CHECK, "--help"])
    assert rc == 0 and out.count("after the header") >= 2, out


# --- evaluate-reports.py ----------------------------------------------------------------------------------------

EVALUATE = os.path.join(BRIDGE, "evaluate-reports.py")
ISSUES = "# Thing - Issues During Development and Their Solutions\n\n## ISS-001 - The first issue\nContext: the first.\n"
FEEDBACK = "# Thing - Claude-Cursor Bridge Feedback\n\n## Stage 1 - Foundation (2026-10-01)\n\n### FB-001 - A check\nIt fired.\n"


def evaluate(tmp_path, status, out_name):
    root = tmp_path / "proj"
    write(root / "Documents" / "Thing Issues During Development and Their Solutions.md", ISSUES)
    write(root / "Documents" / "Thing Claude-Cursor Bridge Feedback.md", FEEDBACK)
    write(root / "Workspace" / "docs" / "PROJECT_STATUS.md", status)
    out_dir = tmp_path / out_name
    rc, out, err = run([EVALUATE, "collect", "--out", out_dir, "--project-root", root, "--project-name", "Thing",
                        "--ledger", tmp_path / "ledger.json", "--home", tmp_path / "home"], cwd=tmp_path)
    written = ""
    if out_dir.is_dir():
        for name in sorted(os.listdir(str(out_dir))):
            with open(str(out_dir / name), encoding="utf-8", errors="replace") as f:
                written += f.read()
    return rc, out + err, written


def status_report(text):
    return [line for line in text.splitlines() if " status: " in line or "header malformed" in line]


@pytest.mark.parametrize("name", NAMES, ids=NAMES)
def test_r058_evaluate_reports_reads_the_fixture_alike_by_header_and_by_fallback(tmp_path, name):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    rc, plain, _ = evaluate(tmp_path, fixture(name), "out1")
    rc2, headed, _ = evaluate(tmp_path, with_header(name), "out2")
    assert rc2 == rc == 0 and status_report(headed) == status_report(plain), headed


def test_r058_evaluate_reports_reads_open_issues_from_the_header(tmp_path):
    status = header(issues=("ISS-015 to write at the next reflection",)) + "# Project Status\nPhase: building\n"
    rc, out, written = evaluate(tmp_path, status, "out")
    assert rc == 0 and "Thing status: 1 incident(s)" in out, out


@pytest.mark.parametrize("bad", ["tab", "schema"], ids=["tab-in-block", "schema-fault"])
def test_r058_evaluate_reports_falls_back_on_a_malformed_header_and_writes_its_line(tmp_path, bad):
    prose = "# Project Status\nPhase: building\nOpen issues: ISS-015 to write at the next reflection\n"
    text = (TAB_HEADER if bad == "tab" else SCHEMA_HEADER) + prose
    rc, out, written = evaluate(tmp_path, text, "out")
    m = re.search(r"header malformed: .*PROJECT_STATUS\.md:(\d+)", out + written)
    assert rc == 0 and m and int(m.group(1)) == (tab_line(text) if bad == "tab" else 1), out + written
    assert "Thing status: 1 incident(s)" in out, "the prose's Open issues line governs: " + out


# --- THE BUILDER'S CASES GO BELOW THIS LINE; NOTHING ABOVE IT IS EDITED ---
