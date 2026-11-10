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

Round 2 (the reviewers' findings on round 1) pins these besides:
- The fallback never raises. Where the text starts with a `---` line, the prose body starts after the
  first later line that is `---` with nothing after it but spaces, tabs or a carriage return; where no
  such line follows, after the first line. status_values reads the header first and names a HeaderError
  of any kind (an unterminated block too) as malformed, the fallback governing.
- bridge_env.STATUS_WORKFLOWS_PROBLEMS is the tuple of the four wordings, in this order: the part-prefix
  rule, the '; traits: ' rule, the same part twice, the empty name. They are worded nowhere else:
  workflow-check, session-start and conformance-check take them from bridge_env, and workflow-check's
  --status refuses exactly the lines status_workflows refuses. A line naming a part a second time is a
  problem and adds no part.
- The fallback of a file padded with blank or space-only lines takes linear time.
- session-start loads bridge_env as it loads workflow-check: nothing the module prints reaches either
  part, no bytecode is written, and a module without the status readers gives one plain line,
  `~/.claude/cursor-bridge/bridge_env.py: cannot be loaded (<type>)` or `... cannot be used (<type>)`.
  The phase it shows is the governing value, never a header line read as prose.
- workflow-check and inventory-check without a usable bridge_env (missing, or without status_values)
  exit 2 with a line naming bridge_env, never skipping the header check; loop-guard without one allows
  the stop with exactly one stderr line naming it and no traceback.

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
import time

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
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
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


# A block opened and never closed (round 2, Blocking 1): read_header refuses it; the prose is still read.
UNTERMINATED_HEADER = "---\nrecord: project-status\n"
# A block whose closing line carries a trailing space: read_header refuses it; the prose after that line governs,
# never the block's own lines (its phase is "done", the prose's "building").
TRAILING_SPACE_HEADER = header(phase="done")[:-len("---\n")] + "--- \n"
# A Markdown rule on the first line and no block at all.
LONE_RULE = "---\n"
BAD = {"tab": TAB_HEADER, "schema": SCHEMA_HEADER, "unterminated": UNTERMINATED_HEADER,
       "trailing-space": TRAILING_SPACE_HEADER, "lone-rule": LONE_RULE}
BAD_IDS = sorted(BAD)


def bad_line(bad, text):
    """The line a malformed header is named on: 1 for a schema fault, else the HeaderError's line."""
    return 1 if bad == "schema" else tab_line(text)


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


@pytest.mark.parametrize("bad", BAD_IDS, ids=BAD_IDS)
def test_r058_a_malformed_header_falls_back_and_names_its_line(bad):
    prose = "# Project Status\nPhase: building\nAwaiting user on: nothing\n"
    text = BAD[bad] + prose
    values, malformed, disagrees = need("status_values")(text)
    assert values == need("status_fallback")(text) and values["phase"] == "building" and disagrees == []
    line, what = malformed
    assert line == bad_line(bad, text) and isinstance(what, str) and what


@pytest.mark.parametrize("name", NAMES, ids=NAMES)
def test_r058_the_four_projects_fixtures_read_alike_by_header_and_by_fallback(name):
    plain = fixture(name)
    fallback = need("status_fallback")(plain)
    assert fallback["phase"] == "building" and fallback["workflows"] == as_parts(PARTS[name])
    assert need("status_values")(plain) == (fallback, None, [])
    assert need("status_values")(with_header(name)) == (fallback, None, [])


# --- the retired readings, matched as uses (KP-073) -------------------------------------------------------------

# The one copy of the syntax-tree helpers (stage H1's refactoring pass): tests/test_header_currency.py.
from test_header_currency import code_tree, constant_sets  # noqa: E402
from test_header_currency import call_args as calls  # noqa: E402
from test_header_currency import names as names_used  # noqa: E402


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
@pytest.mark.parametrize("bad", BAD_IDS, ids=BAD_IDS)
def test_r058_loop_guard_on_a_malformed_header_does_what_the_prose_says(tmp_path, bad, prose, code):
    need("status_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    ws = tmp_path / "Workspace"
    write(ws / "docs" / "PROJECT_STATUS.md", BAD[bad] + "# Project Status\nPhase: building\n" + prose)
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


@pytest.mark.parametrize("bad", BAD_IDS, ids=BAD_IDS)
def test_r058_session_start_falls_back_on_a_malformed_header_and_names_its_line(tmp_path, home, bad):
    text = BAD[bad] + "# Project Status\nPhase: building\nAwaiting user on: nothing\n"
    out = pointers(hook_status(tmp_path, text), home)
    m = re.search(r"^header malformed: .*PROJECT_STATUS\.md:(\d+)$", out, re.M)
    assert m and int(m.group(1)) == bad_line(bad, text), out
    assert P + "delegation-loop.md" in named(out), "the prose's phase governs: " + out
    assert "PROJECT STATE: Phase: building." in out, "the phase shown is the prose's: " + out


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


@pytest.mark.parametrize("line,reason", [c[1:] for c in REFUSED], ids=[c[0] for c in REFUSED])
def test_r058_retired_1_session_start_refuses_a_line_the_grammar_refuses(tmp_path, home, line, reason):
    out = pointers(hook_status(tmp_path, "# Project Status\nPhase: building\n" + line + "Awaiting user on: nothing\n"), home)
    assert "workflows line refused: " + reason in out, out
    assert not [n for n in named(out) if n.startswith(W + "types/")], out


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


@pytest.mark.parametrize("bad", BAD_IDS, ids=BAD_IDS)
def test_r058_conformance_check_refuses_a_malformed_header(tmp_path, bad):
    text = BAD[bad] + "# Project Status\nPhase: building\nWorkflows: not yet classified\n"
    rc, out, err = conformance(conformance_ws(tmp_path, text))
    m = re.search(r"HEADER MALFORMED: .*PROJECT_STATUS\.md:(\d+) \S", out)
    assert rc == 2 and m and int(m.group(1)) == bad_line(bad, text), (rc, out, err)


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


@pytest.mark.parametrize("bad", BAD_IDS, ids=BAD_IDS)
def test_r058_workflow_check_refuses_a_malformed_header(tmp_path, bad):
    path = tmp_path / "PROJECT_STATUS.md"
    text = BAD[bad] + fixture("bridge")
    write(path, text)
    rc, out, err = workflow_check(path)
    m = re.search(r"HEADER MALFORMED: .*PROJECT_STATUS\.md:(\d+) \S", out)
    assert rc == 2 and m and int(m.group(1)) == bad_line(bad, text), (rc, out, err)


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


@pytest.mark.parametrize("bad", BAD_IDS, ids=BAD_IDS)
def test_r058_inventory_check_refuses_a_malformed_header(tmp_path, bad):
    path = tmp_path / "PROJECT_STATUS.md"
    text = BAD[bad] + fixture("bridge")
    write(path, text)
    rc, out, err = inventory(tmp_path, path)
    m = re.search(r"HEADER MALFORMED: .*PROJECT_STATUS\.md:(\d+) \S", out)
    assert rc == 2 and m and int(m.group(1)) == bad_line(bad, text), (rc, out, err)


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


@pytest.mark.parametrize("bad", BAD_IDS, ids=BAD_IDS)
def test_r058_evaluate_reports_falls_back_on_a_malformed_header_and_writes_its_line(tmp_path, bad):
    prose = "# Project Status\nPhase: building\nOpen issues: ISS-015 to write at the next reflection\n"
    text = BAD[bad] + prose
    rc, out, written = evaluate(tmp_path, text, "out")
    m = re.search(r"header malformed: .*PROJECT_STATUS\.md:(\d+)", out + written)
    assert rc == 0 and m and int(m.group(1)) == bad_line(bad, text), out + written
    assert "Thing status: 1 incident(s)" in out, "the prose's Open issues line governs: " + out


# --- round 2: the reviewers' findings on round 1 ----------------------------------------------------------------

GRAMMAR_WORDINGS = ("Workflows line breaks the part-prefix rule", "Workflows line must contain '; traits: ' exactly once",
                    "two Workflows lines name the same part", "empty name in the Workflows head")


def test_r058_a_line_naming_a_part_twice_is_a_problem_and_adds_no_part():
    text = ("# Project Status\nPhase: building\nWorkflows: app: Web App Development; traits: Installable\n"
            "Workflows: app: Web App Development %s Local Web App; traits: none\n" % ARROW)
    parts, problems = need("status_workflows")(text)
    assert parts == [{"type": "Web App Development", "subtype": None, "traits": ["Installable"]}], parts
    assert problems == ["two Workflows lines name the same part"], problems


@pytest.mark.parametrize("pad", ["\n", " \n"], ids=["blank-lines", "space-lines"])
def test_r058_the_status_values_of_a_padded_file_take_linear_time(pad):
    text = "# Project Status\n" + pad * 20000
    start = time.perf_counter()
    values, malformed, disagrees = need("status_values")(text)
    took = time.perf_counter() - start
    assert took < 2.0 and values["phase"] == "" and malformed is None, took


def test_r058_bridge_env_holds_the_four_workflows_wordings():
    assert tuple(need("STATUS_WORKFLOWS_PROBLEMS")) == GRAMMAR_WORDINGS


@pytest.mark.parametrize("program", ["workflow-check.py", "session-start.py", "conformance-check.py"],
                         ids=["workflow-check", "session-start", "conformance-check"])
def test_r058_the_workflows_grammar_is_worded_only_in_bridge_env(program):
    need("STATUS_WORKFLOWS_PROBLEMS")  # the one copy is new: red on the checkpoint
    tree = code_tree(program)
    words = [w[len("Workflows line "):] if w.startswith("Workflows line ") else w for w in GRAMMAR_WORDINGS]
    found = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and any(w in n.value for w in words)]
    assert found == [], found


def test_r058_workflow_check_refuses_a_workflows_line_as_bridge_env_does(tmp_path):
    # A form feed splits a line for str.splitlines and not for a split at the line feed: one grammar reads it one way.
    text = ("# Project Status\nPhase: building\n"
            "Workflows: Web App Development; traits: none\x0cWorkflows: Web App Development; traits: none\n")
    parts, problems = need("status_workflows")(text)
    path = tmp_path / "PROJECT_STATUS.md"
    write(path, text)
    rc, out, err = workflow_check(path)
    refused = [w for line in out.splitlines() for w in GRAMMAR_WORDINGS if line.startswith("FAIL") and line.endswith(w)]
    assert refused == problems and problems, (problems, out)


def installed_copy(tmp_path, module_text=None):
    """A home holding the installed bridge, its bridge_env.py replaced by module_text where given."""
    h = tmp_path / "home"
    shutil.copytree(os.path.join(ROOT, "bridge", "commands"), str(h / ".claude" / "commands"))
    shutil.copytree(BRIDGE, str(h / ".claude" / "cursor-bridge"), ignore=shutil.ignore_patterns("__pycache__"))
    if module_text is not None:
        write(h / ".claude" / "cursor-bridge" / "bridge_env.py", module_text)
    return h


def hook_run(ws, home):
    data = {"cwd": str(ws), "hook_event_name": "SessionStart", "source": "compact"}
    env = env_with_home(home)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    hook = home / ".claude" / "cursor-bridge" / "session-start.py"  # the copy: it loads bridge_env from its own folder
    return run([hook, "--part", "pointers"], stdin=json.dumps(data), env=env)


LEAK = 'import sys\nprint("LEAK-OUT")\nsys.stderr.write("LEAK-ERR\\n")\n'


def test_r058_session_start_sinks_what_bridge_env_prints_and_writes_no_bytecode(tmp_path):
    need("status_values")  # the header path is new: red on the checkpoint
    with open(os.path.join(BRIDGE, "bridge_env.py"), encoding="utf-8") as f:
        h = installed_copy(tmp_path, LEAK + f.read())
    rc, out, err = hook_run(hook_status(tmp_path, fixture("bridge")), h)
    assert rc == 0 and "LEAK" not in out + err and err == "", (out, err)
    assert P + "delegation-loop.md" in named(out), out
    assert not (h / ".claude" / "cursor-bridge" / "__pycache__").exists(), "bytecode written beside bridge_env.py"


def test_r058_session_start_prints_one_line_where_bridge_env_lacks_the_status_readers(tmp_path):
    need("status_values")  # the header path is new: red on the checkpoint
    h = installed_copy(tmp_path, LEAK + "def read_header(text):\n    return None, text\n")
    rc, out, err = hook_run(hook_status(tmp_path, fixture("bridge")), h)
    assert rc == 0 and err == "" and re.fullmatch(
        r"~/\.claude/cursor-bridge/bridge_env\.py: cannot be (loaded|used) \([A-Za-z ]+\)\n", out), (rc, out, err)


@pytest.mark.parametrize("module", ["missing", "old"], ids=["missing", "old"])
@pytest.mark.parametrize("program", ["workflow-check.py", "inventory-check.py"], ids=["workflow-check", "inventory-check"])
def test_r058_a_checker_without_the_status_readers_refuses_and_never_skips_the_header(tmp_path, program, module):
    need("status_values")  # the header path is new: red on the checkpoint
    alone = tmp_path / "alone"
    alone.mkdir()
    shutil.copy(os.path.join(BRIDGE, program), str(alone / program))
    if program == "workflow-check.py":  # its registry beside it, as the R-014 harness copies it
        shutil.copytree(os.path.join(BRIDGE, "workflow"), str(alone / "workflow"))
    if module == "old":
        write(alone / "bridge_env.py", "def read_header(text):\n    return None, text\n")
    status = tmp_path / "PROJECT_STATUS.md"
    write(status, with_header("bridge"))
    if program == "workflow-check.py":
        rc, out, err = run([alone / program, "--open-list", OPEN_LIST, "--status", status])
    else:
        rc, out, err = run([alone / program, "--inventory", "absent-inventory.md", "--changes", "absent-changes.md",
                            "--status", status], cwd=tmp_path)
    assert rc == 2 and "bridge_env" in out + err and "Traceback" not in err, (rc, out, err)


def test_r058_loop_guard_without_bridge_env_fails_open_with_one_plain_line(tmp_path):
    need("status_values")  # the header path is new: red on the checkpoint
    alone = tmp_path / "alone"
    alone.mkdir()
    shutil.copy(GUARD, str(alone / "loop-guard.py"))
    ws = tmp_path / "Workspace"
    write(ws / "docs" / "PROJECT_STATUS.md", "# Project Status\nPhase: building\nAwaiting user on: nothing\n")
    data = {"cwd": str(ws), "hook_event_name": "Stop", "background_tasks": [], "session_crons": []}
    rc, out, err = run([alone / "loop-guard.py"], stdin=json.dumps(data))
    assert rc == 0 and "Traceback" not in err and len(err.splitlines()) == 1 and "bridge_env" in err, (rc, out, err)


# --- round 3: a part named twice on a line that breaks the grammar again (Review A, round 2, B1) ---------------

FIRST_APP = "# Project Status\nPhase: building\nWorkflows: app: Web App Development; traits: none\n"
TWICE = "two Workflows lines name the same part"
TWICE_AND = [
    ("no-traits-mark", "Workflows: app: Web App Development\n", [TWICE, GRAMMAR_WORDINGS[1]]),
    ("empty-name", "Workflows: app: Web App Development, ; traits: none\n", [TWICE, GRAMMAR_WORDINGS[3]]),
    ("two-traits-marks", "Workflows: app: Web App Development; traits: a; traits: b\n", [TWICE, GRAMMAR_WORDINGS[1]]),
]
TWICE_AND_IDS = [c[0] for c in TWICE_AND]


@pytest.mark.parametrize("second,expected", [c[1:] for c in TWICE_AND], ids=TWICE_AND_IDS)
def test_r058_r3_a_part_named_twice_keeps_the_second_lines_other_problem(second, expected):
    parts, problems = need("status_workflows")(FIRST_APP + second)
    assert parts == [{"type": "Web App Development", "subtype": None, "traits": []}], parts
    assert problems == expected, problems


@pytest.mark.parametrize("second,expected", [c[1:] for c in TWICE_AND], ids=TWICE_AND_IDS)
def test_r058_r3_workflow_check_refuses_a_part_named_twice_as_bridge_env_does(tmp_path, second, expected):
    need("STATUS_WORKFLOWS_PROBLEMS")  # the one copy of the grammar is new: red on the checkpoint
    _parts, problems = need("status_workflows")(FIRST_APP + second)
    path = tmp_path / "PROJECT_STATUS.md"
    write(path, FIRST_APP + second)
    rc, out, err = workflow_check(path)
    assert rc == 1 and "Traceback" not in err, (rc, out, err)
    fails = [line for line in out.splitlines() if line.startswith("FAIL")]
    refused = [w for line in fails for w in GRAMMAR_WORDINGS if line.endswith(w)]
    assert refused == problems == expected, (problems, expected, out)


LINE_FAULTS = [
    ("no-traits-mark", "Workflows: Web App Development\n"),
    ("two-traits-marks", "Workflows: Web App Development; traits: a; traits: b\n"),
    ("prefix-fault", "Workflows: app: Web App Development; traits: none\nWorkflows: : Web App Development; traits: none\n"),
]
LINE_FAULT_IDS = [c[0] for c in LINE_FAULTS]


@pytest.mark.parametrize("lines", [c[1] for c in LINE_FAULTS], ids=LINE_FAULT_IDS)
def test_r058_r3_workflow_check_refuses_a_line_fault_as_bridge_env_does(tmp_path, lines):
    # The sweep's c04: without the skip on a prefix or traits fault, workflow-check splits a body that breaks the rule.
    need("STATUS_WORKFLOWS_PROBLEMS")  # the one copy of the grammar is new: red on the checkpoint
    text = "# Project Status\nPhase: building\n" + lines
    _parts, problems = need("status_workflows")(text)
    path = tmp_path / "PROJECT_STATUS.md"
    write(path, text)
    rc, out, err = workflow_check(path)
    assert rc == 1 and "Traceback" not in err, (rc, out, err)
    refused = [w for line in out.splitlines() if line.startswith("FAIL") for w in GRAMMAR_WORDINGS if line.endswith(w)]
    assert refused == problems and len(problems) == 1, (problems, out)


FOREIGN_REASON = "a reason bridge_env never gives"


def test_r058_r3_session_start_prints_no_refusal_outside_the_four_wordings(tmp_path):
    # The sweep's r17: the hook prints a refusal only when it is one of bridge_env's four wordings.
    need("STATUS_WORKFLOWS_PROBLEMS")  # the one copy of the grammar is new: red on the checkpoint
    with open(os.path.join(BRIDGE, "bridge_env.py"), encoding="utf-8") as f:
        real = f.read()
    foreign = real + "\n\ndef status_workflows(text):\n    return [], [%r, 7]\n" % FOREIGN_REASON
    h = installed_copy(tmp_path, foreign)
    rc, out, err = hook_run(hook_status(tmp_path, fixture("bridge")), h)
    assert rc == 0 and err == "", (rc, out, err)
    assert "workflows line refused" not in out and FOREIGN_REASON not in out, out
    assert P + "delegation-loop.md" in named(out), out


# --- round 4: conformance-check through a link (CI on PR #138, bridge programs (ubuntu-latest)) ----------------

LINKED_LOAD = r'''
import importlib.util, os, sys
link_dir, real_dir = sys.argv[1], sys.argv[2]
real = os.path.realpath
link_file = os.path.normcase(real(os.path.join(link_dir, "conformance-check.py")))
def resolved(path, *args, **kwargs):
    # A symbolic link resolved as Linux resolves it: the program's real file lives in real_dir.
    if os.path.normcase(real(path, *args, **kwargs)) == link_file:
        return os.path.join(real_dir, "conformance-check.py")
    return real(path, *args, **kwargs)
os.path.realpath = resolved
spec = importlib.util.spec_from_file_location("conformance_check", os.path.join(link_dir, "conformance-check.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(hasattr(mod.bridge_env, "status_workflow_line"), hasattr(mod.bridge_env, "status_values"))
'''


def test_r058_r4_conformance_check_loads_bridge_env_beside_its_real_file(tmp_path):
    # R-015's R2-2 for bridge_env: run through a link, conformance-check loads the bridge_env.py beside its real
    # file, as it loads workflow-check.py, never one beside the link (the link's folder holds none here).
    need("status_workflow_line")  # the per-line reader is new: red on the checkpoint
    real_dir = tmp_path / "bin"
    real_dir.mkdir()
    for name in ("conformance-check.py", "workflow-check.py", "bridge_env.py"):
        shutil.copy(os.path.join(BRIDGE, name), str(real_dir / name))
    link_dir = tmp_path / "elsewhere"
    link_dir.mkdir()
    shutil.copy(os.path.join(BRIDGE, "conformance-check.py"), str(link_dir / "conformance-check.py"))
    driver = tmp_path / "linked_load.py"
    write(driver, LINKED_LOAD)
    rc, out, err = run([driver, link_dir, real_dir], cwd=tmp_path)
    assert rc == 0 and out.strip() == "True True", (rc, out, err)


# --- THE BUILDER'S CASES GO BELOW THIS LINE; NOTHING ABOVE IT IS EDITED ---


def test_r058_status_values_agreeing_header_matches_fixture_fallback(name="bridge"):
    """R-058: when the header matches the prose fallback, status_values reports no disagreement."""
    text = with_header(name)
    values, malformed, disagrees = need("status_values")(text)
    assert malformed is None and disagrees == []
    assert values["workflows"] == need("status_fallback")(fixture(name))["workflows"]
