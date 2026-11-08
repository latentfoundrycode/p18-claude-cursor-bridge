"""TASK-050, the supervisor's acceptance tests (R-061; D-002): the run parameters' header read first by the loop
guard, the launcher and the review guard through bridge_env, checked by inventory-check, and the one fallback
reading of each line where the file has no header.

enforces: docs/DESIGN.md, "Change: release B2", "The records and their headers" (the run-parameters row), "The
fallback readers, one copy each" with its enumerated retired reading (10), and "Header first; fallback;
malformed"; docs/BUILD_PLAN.md, TASK-050's Done when; R-061.

The fixed forms these tests pin, which the brief repeats:
- bridge_env.run_parameters_fallback(text) returns a dict of exactly the nine keys, in HEADER_SCHEMAS' order:
  - the five values (stage_pause, merge_authority, refactoring_pass, installer_verification, parallel_increments):
    the first line beginning `<Name>: ` (`Stage pause: `, `Merge authority: `, `Refactoring pass: `,
    `Installer verification: `, `Parallel increments: `), its text after that prefix up to the first space or the
    end, the token test_r001_run_parameters_owner_values reads (`supervisor`, never the parenthesis after it);
    "" where no line stands;
  - agent_ceiling: the loop guard's `Agent ceiling:` reading, the first such line's integer; None where none stands;
  - ceiling_above_twice: the launcher's `owner_cap` reading, one copy: each line `Ceiling above twice: <kind>
    <seconds> (<words>)` whose words are not empty after stripping, the first such line per kind (a line with an
    empty parenthesis is skipped and a later line of its kind stands), in file order, each
    {"kind": <kind in lower case>, "seconds": <int>, "words": <the parenthesis's text, stripped, whole>};
  - design_rounds_above_five: bridge-run's `Design rounds above five:` reading (DESIGN_LIFT_RE, moved), the first
    well-formed line per subject (words not empty, rounds an integer above five), in file order, each
    {"subject", "rounds", "words", "date"};
  - review_rounds_above_ceiling: review_owner_lifts' reading (REVIEW_LIFT_RE), the first well-formed line per ID
    (words not empty, rounds an integer above three), in file order, each {"id", "rounds", "words", "date"};
  - a lift's parenthesis text that ends `, YYYY-MM-DD` gives words = the text before that comma, stripped, and
    date = the date; otherwise words = the whole text and date = "".
- bridge_env.run_parameters_values(text) returns (values, malformed, disagrees): values the header's nine keys
  where the text has a well-formed header (read_header raises nothing and check_header finds nothing), else
  run_parameters_fallback(text); malformed None, or (line, what): a HeaderError's line, or 1 for a schema fault;
  disagrees the keys header_agrees names against run_parameters_fallback of the body, else [].
- bridge_env.run_parameters_refusal(folder, keys) reads <folder>/docs/RUN_PARAMETERS.md and returns None (no file,
  no header, or a header agreeing on every key of `keys`), `header: docs/RUN_PARAMETERS.md:<line> <what>` for a
  malformed header, or `header: disagrees <key>` for the first key of `keys` (in the order given) that disagrees.
- bridge-run.py refuses every launch, exit 125, `bridge-run: refused - header: ` and that text, where the run
  parameters' header is malformed or disagrees on ceiling_above_twice, design_rounds_above_five or
  review_rounds_above_ceiling; a disagreement on any other key never refuses a launch.
- review-guard.py refuses a snapshot, exit 125, `review-guard: refused - header: ` and that text, where the header
  is malformed or disagrees on review_rounds_above_ceiling; a disagreement on any other key never refuses it.
- loop-guard.py refuses the stop (exit 2, `header disagrees: <key>` on stderr) where the header's agent_ceiling or
  ceiling_above_twice disagrees with its line; on a malformed header it reads the lines (the stop decided as the
  lines decide, no traceback); a disagreement on any other key is not its finding.
- inventory-check.py checks docs/RUN_PARAMETERS.md beside the inventory: `HEADER DISAGREES: <key>` for each of the
  nine keys that disagrees (exit 1), `HEADER MALFORMED: docs/RUN_PARAMETERS.md:<line> <what>` and exit 2 for a
  malformed header; a file with no header is not its finding.
- With an agreeing header every reader gives the answer the lines give.

The supervisor's cases stand above the marker at the end of this file. The builder adds its own cases below the
marker and edits nothing above it.
"""
import copy
import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

import test_task032_supervisor_launcher as t32  # noqa: E402  (the launcher's lab, reused as it stands)
import test_header_plan as tp  # noqa: E402  (the guard's repository and the brief prose, reused)
import test_header_tables as th  # noqa: E402  (the inventory fixture, reused)

LOOP_GUARD = os.path.join(BRIDGE, "loop-guard.py")
REVIEW_GUARD = os.path.join(BRIDGE, "review-guard.py")
INVENTORY_CHECK = os.path.join(BRIDGE, "inventory-check.py")


def need(name):
    obj = getattr(bridge_env, name, None)
    assert obj is not None, "bridge_env.%s is missing (TASK-050)" % name
    return obj


def write(path, text):
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(str(path), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


# ---------------------------------------------------------------- the fixture, prose and header from one table

PROSE = (
    "# Run parameters\n"
    "Set: 2026-10-11   (owner may change any of these at any time by saying so; update this file)\n"
    "Stage pause: run\n"
    "Merge authority: supervisor   (owner's instruction 2026-10-12: the supervisor completes the merge)\n"
    "Refactoring pass: on\n"
    "Installer verification: n/a (host extension)\n"
    "Parallel increments: on   (the owner's word, 2026-10-25)\n"
    "Agent ceiling: 7200\n"
    "Ceiling above twice: Builder 21600 (the owner: six hours, 2026-10-10)\n"
    "Ceiling above twice: driver 14400 (owner, 2026-10-10)\n"
    "Design rounds above five: pace 7 (the owner's words, 2026-11-04)\n"
    "Review rounds above the ceiling: TASK-046 4 (the owner allows one more, 2026-11-04)\n"
)

VALUES = {
    "stage_pause": "run",
    "merge_authority": "supervisor",
    "refactoring_pass": "on",
    "installer_verification": "n/a",
    "parallel_increments": "on",
    "agent_ceiling": 7200,
    "ceiling_above_twice": [
        {"kind": "builder", "seconds": 21600, "words": "the owner: six hours, 2026-10-10"},
        {"kind": "driver", "seconds": 14400, "words": "owner, 2026-10-10"},
    ],
    "design_rounds_above_five": [
        {"subject": "pace", "rounds": 7, "words": "the owner's words", "date": "2026-11-04"},
    ],
    "review_rounds_above_ceiling": [
        {"id": "TASK-046", "rounds": 4, "words": "the owner allows one more", "date": "2026-11-04"},
    ],
}

KEYS = list(VALUES)
LIFT_ORDER = {"ceiling_above_twice": ("kind", "seconds", "words"),
              "design_rounds_above_five": ("subject", "rounds", "words", "date"),
              "review_rounds_above_ceiling": ("id", "rounds", "words", "date")}


def q(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def scalar(v):
    if v is None:
        return "null"
    if isinstance(v, int):
        return str(v)
    return q(v)


def rp_header(values=None):
    values = VALUES if values is None else values
    lines = ["---", "record: run-parameters", "header: 1"]
    for key in KEYS:
        v = values[key]
        if key in LIFT_ORDER:
            if not v:
                lines.append("%s: []" % key)
                continue
            lines.append("%s:" % key)
            for item in v:
                for i, field in enumerate(LIFT_ORDER[key]):
                    lines.append("%s%s: %s" % ("  - " if i == 0 else "    ", field, scalar(item[field])))
        else:
            lines.append("%s: %s" % (key, scalar(v)))
    lines.append("---")
    return "\n".join(lines) + "\n"


def changed(key):
    """VALUES with one key changed, so the header disagrees with PROSE on that key alone."""
    v = copy.deepcopy(VALUES)
    if key in LIFT_ORDER:
        v[key][0]["words"] = v[key][0]["words"] + " and more"
    elif key == "agent_ceiling":
        v[key] = 10800
    else:
        v[key] = {"stage_pause": "pause", "merge_authority": "owner", "refactoring_pass": "off",
                  "installer_verification": "local", "parallel_increments": "off"}[key]
    return v


MALFORMED = rp_header().replace("header: 1", "header:\t1", 1)


def test_r061_the_fixtures_header_is_well_formed_and_reads_as_the_values():
    header, body = bridge_env.read_header(rp_header() + PROSE)
    assert bridge_env.check_header("run-parameters", header) == []
    assert {k: header[k] for k in KEYS} == VALUES and body == PROSE


# ---------------------------------------------------------------- the one fallback reading

def test_r061_the_fallback_reads_the_nine_keys_from_the_lines():
    got = need("run_parameters_fallback")(PROSE)
    assert list(got) == KEYS and got == VALUES, got


def test_r061_the_fallback_reads_this_repositorys_run_parameters():
    got = need("run_parameters_fallback")(th.read_repo("docs/RUN_PARAMETERS.md"))
    assert got == {"stage_pause": "run", "merge_authority": "supervisor", "refactoring_pass": "on",
                   "installer_verification": "n/a", "parallel_increments": "on", "agent_ceiling": None,
                   "ceiling_above_twice": [], "design_rounds_above_five": [], "review_rounds_above_ceiling": []}, got


def test_r061_the_fallback_of_an_empty_file_is_empty_values():
    got = need("run_parameters_fallback")("# Run parameters\n")
    assert got == {k: ([] if k in LIFT_ORDER else (None if k == "agent_ceiling" else "")) for k in KEYS}, got


def test_r061_the_ceiling_reading_is_the_launchers_one_copy():
    text = ("Ceiling above twice: builder 30000 ()\n"
            "Ceiling above twice: builder 25000 ( )\n"
            "Ceiling above twice: builder 21600 (the owner's words)\n"
            "Ceiling above twice: builder 99999 (a later line)\n"
            "Ceiling above twice: REVIEW 9000 (owner)\n")
    got = need("run_parameters_fallback")(text)["ceiling_above_twice"]
    assert got == [{"kind": "builder", "seconds": 21600, "words": "the owner's words"},
                   {"kind": "review", "seconds": 9000, "words": "owner"}], got


def test_r061_a_lift_line_at_or_below_its_default_or_without_words_lifts_nothing():
    text = ("Design rounds above five: pace 5 (not above, 2026-11-04)\n"
            "Design rounds above five: pace 8 ( )\n"
            "Design rounds above five: pace 9 (the owner, 2026-11-05)\n"
            "Design rounds above five: pace 12 (a later line, 2026-11-06)\n"
            "Review rounds above the ceiling: TASK-001 3 (not above, 2026-11-04)\n"
            "Review rounds above the ceiling: TASK-001 5 (two more)\n")
    got = need("run_parameters_fallback")(text)
    assert got["design_rounds_above_five"] == [{"subject": "pace", "rounds": 9, "words": "the owner", "date": "2026-11-05"}]
    assert got["review_rounds_above_ceiling"] == [{"id": "TASK-001", "rounds": 5, "words": "two more", "date": ""}]


def test_r061_the_values_read_by_header_and_by_fallback_alike():
    values = need("run_parameters_values")
    assert values(rp_header() + PROSE) == (VALUES, None, [])
    assert values(PROSE) == (VALUES, None, [])


@pytest.mark.parametrize("key", KEYS, ids=KEYS)
def test_r061_the_values_name_a_disagreeing_key(key):
    got, malformed, disagrees = need("run_parameters_values")(rp_header(changed(key)) + PROSE)
    assert malformed is None and disagrees == [key] and got == changed(key), (malformed, disagrees)


def test_r061_a_malformed_header_reads_the_lines():
    got, malformed, disagrees = need("run_parameters_values")(MALFORMED + PROSE)
    assert got == VALUES and malformed is not None and malformed[0] == 3, malformed


def test_r061_the_refusal_reads_only_the_keys_it_is_given(tmp_path):
    refusal = need("run_parameters_refusal")
    write(tmp_path / "docs" / "RUN_PARAMETERS.md", rp_header(changed("agent_ceiling")) + PROSE)
    assert refusal(str(tmp_path), ("ceiling_above_twice", "review_rounds_above_ceiling")) is None
    assert refusal(str(tmp_path), ("review_rounds_above_ceiling", "agent_ceiling")) == "header: disagrees agent_ceiling"
    write(tmp_path / "docs" / "RUN_PARAMETERS.md", MALFORMED + PROSE)
    assert refusal(str(tmp_path), ("ceiling_above_twice",)).startswith("header: docs/RUN_PARAMETERS.md:3 ")
    write(tmp_path / "docs" / "RUN_PARAMETERS.md", PROSE)
    assert refusal(str(tmp_path), KEYS) is None


# ---------------------------------------------------------------- the launcher

def lab_with(tmp_path, params):
    lab = t32.Lab(tmp_path)
    t32.write_brief(lab.root, "TASK-001")
    t32.write_params(lab, params)
    return lab


def test_r061_the_launcher_runs_with_an_agreeing_header(tmp_path):
    need("run_parameters_refusal")  # the header path is new: red on the checkpoint, never passing there by the old reading
    t32.assert_ran(t32.launch(lab_with(tmp_path, rp_header() + PROSE), t32.build("TASK-001")))


LAUNCHER_KEYS = ["ceiling_above_twice", "design_rounds_above_five", "review_rounds_above_ceiling"]


@pytest.mark.parametrize("key", LAUNCHER_KEYS, ids=LAUNCHER_KEYS)
def test_r061_the_launcher_refuses_a_disagreeing_lift(tmp_path, key):
    lab = lab_with(tmp_path, rp_header(changed(key)) + PROSE)
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-001")), "bridge-run: refused - header: ")
    assert line.startswith("bridge-run: refused - header: disagrees %s" % key), line


def test_r061_the_launcher_refuses_a_malformed_header(tmp_path):
    lab = lab_with(tmp_path, MALFORMED + PROSE)
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-001")), "bridge-run: refused - header: ")
    assert "docs/RUN_PARAMETERS.md:3" in line, line


@pytest.mark.parametrize("key", ["agent_ceiling", "merge_authority"], ids=["agent_ceiling", "merge_authority"])
def test_r061_the_launcher_compares_only_the_lifts_it_reads(tmp_path, key):
    need("run_parameters_refusal")  # the header path is new: red on the checkpoint, never passing there by the old reading
    t32.assert_ran(t32.launch(lab_with(tmp_path, rp_header(changed(key)) + PROSE), t32.build("TASK-001")))


def test_r061_the_launchers_ceiling_reads_alike_by_header_and_by_lines(tmp_path, program):
    need("run_parameters_refusal")  # the header path is new: red on the checkpoint, never passing there by the old reading
    br = program("bridge-run")
    plain, headed = tmp_path / "p", tmp_path / "h"
    write(plain / "docs" / "RUN_PARAMETERS.md", PROSE)
    write(headed / "docs" / "RUN_PARAMETERS.md", rp_header() + PROSE)
    for kind in ("builder", "driver", "review"):
        assert br.cap_for(kind, str(headed)) == br.cap_for(kind, str(plain)), kind
    assert br.cap_for("builder", str(plain))[0] == 21600


# ---------------------------------------------------------------- the review guard

def guard_repo(tmp_path, params):
    repo = tp.guard_repo(tmp_path, tp.brief_prose())
    write(repo / "docs" / "RUN_PARAMETERS.md", params)
    tp.git(repo, "add", "docs/RUN_PARAMETERS.md")
    tp.git(repo, "commit", "-q", "-m", "run parameters")
    return repo


def test_r061_the_guard_snapshots_with_an_agreeing_header(tmp_path):
    need("run_parameters_refusal")  # the header path is new: red on the checkpoint, never passing there by the old reading
    rc, out = tp.run(REVIEW_GUARD, guard_repo(tmp_path, rp_header() + PROSE), "snapshot", "TASK-001")
    assert rc == 0, out


def test_r061_the_guard_refuses_a_disagreeing_review_lift(tmp_path):
    repo = guard_repo(tmp_path, rp_header(changed("review_rounds_above_ceiling")) + PROSE)
    rc, out = tp.run(REVIEW_GUARD, repo, "snapshot", "TASK-001")
    assert rc == 125 and out.startswith("review-guard: refused - header: disagrees review_rounds_above_ceiling"), out


def test_r061_the_guard_refuses_a_malformed_header(tmp_path):
    rc, out = tp.run(REVIEW_GUARD, guard_repo(tmp_path, MALFORMED + PROSE), "snapshot", "TASK-001")
    assert rc == 125 and out.startswith("review-guard: refused - header: docs/RUN_PARAMETERS.md:3 "), out


def test_r061_the_guard_compares_only_its_one_lift(tmp_path):
    need("run_parameters_refusal")  # the header path is new: red on the checkpoint, never passing there by the old reading
    rc, out = tp.run(REVIEW_GUARD, guard_repo(tmp_path, rp_header(changed("ceiling_above_twice")) + PROSE),
                     "snapshot", "TASK-001")
    assert rc == 0, out


# ---------------------------------------------------------------- the loop guard

STATUS = "# Project Status\nPhase: building\nAwaiting user on: the owner's gate\n"


def loop_guard(ws):
    data = {"cwd": str(ws), "hook_event_name": "Stop", "background_tasks": [], "session_crons": []}
    p = subprocess.run([sys.executable, LOOP_GUARD], input=json.dumps(data), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout, p.stderr


def loop_ws(tmp_path, params):
    ws = tmp_path / "Workspace"
    write(ws / "docs" / "PROJECT_STATUS.md", STATUS)
    write(ws / "docs" / "RUN_PARAMETERS.md", params)
    return ws


def test_r061_the_loop_guard_allows_the_stop_with_an_agreeing_header(tmp_path):
    need("run_parameters_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    rc, out, err = loop_guard(loop_ws(tmp_path, rp_header() + PROSE))
    assert rc == 0 and "header" not in err, (rc, err)


@pytest.mark.parametrize("key", ["agent_ceiling", "ceiling_above_twice"], ids=["agent_ceiling", "ceiling_above_twice"])
def test_r061_the_loop_guard_refuses_the_stop_where_its_two_keys_disagree(tmp_path, key):
    rc, out, err = loop_guard(loop_ws(tmp_path, rp_header(changed(key)) + PROSE))
    assert rc == 2 and "header disagrees: %s" % key in err, (rc, err)


@pytest.mark.parametrize("key", ["design_rounds_above_five", "review_rounds_above_ceiling", "stage_pause"],
                         ids=["design_rounds_above_five", "review_rounds_above_ceiling", "stage_pause"])
def test_r061_the_loop_guard_reads_no_other_key_for_its_disagreement(tmp_path, key):
    need("run_parameters_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    rc, out, err = loop_guard(loop_ws(tmp_path, rp_header(changed(key)) + PROSE))
    assert rc == 0 and "header disagrees" not in err, (rc, err)


def test_r061_the_loop_guard_on_a_malformed_header_reads_the_lines(tmp_path):
    need("run_parameters_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    rc, out, err = loop_guard(loop_ws(tmp_path, MALFORMED + PROSE))
    assert rc == 0 and "Traceback" not in err, (rc, err)


def test_r061_the_loop_guards_ceilings_read_alike_by_header_and_by_lines(tmp_path, program):
    need("run_parameters_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    lg = program("loop-guard")
    plain = loop_ws(tmp_path / "p", PROSE)
    headed = loop_ws(tmp_path / "h", rp_header() + PROSE)
    assert lg.agent_ceiling(str(headed)) == lg.agent_ceiling(str(plain)) == 7200
    cmd = 'python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind builder -- cursor-agent -p "x"'
    assert lg.command_ceiling(cmd, str(headed)) == lg.command_ceiling(cmd, str(plain)) == 21600


def test_r061_the_loop_guards_ceiling_takes_the_launchers_rule(tmp_path, program):
    need("run_parameters_fallback")
    lg = program("loop-guard")
    ws = loop_ws(tmp_path, "Ceiling above twice: builder 30000 ()\nCeiling above twice: builder 21600 (the owner)\n")
    cmd = 'python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind builder -- cursor-agent -p "x"'
    assert lg.command_ceiling(cmd, str(ws)) == 21600


# ---------------------------------------------------------------- inventory-check, the record's checker

def inventory_ws(tmp_path, params):
    ws = th.inventory_ws(tmp_path)
    write(ws / "docs" / "RUN_PARAMETERS.md", params)
    return ws


def inventory_check(ws):
    p = subprocess.run([sys.executable, INVENTORY_CHECK], cwd=str(ws), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout + p.stderr


def test_r061_inventory_check_passes_an_agreeing_header(tmp_path):
    need("run_parameters_values")  # the header path is new: red on the checkpoint, never passing there by the old reading
    rc_p, out_p = inventory_check(inventory_ws(tmp_path / "p", PROSE))
    rc_h, out_h = inventory_check(inventory_ws(tmp_path / "h", rp_header() + PROSE))
    assert rc_p == rc_h == 0 and "HEADER" not in out_h, (out_p, out_h)


def test_r061_inventory_check_passes_this_repositorys_run_parameters_with_their_header(tmp_path):
    text = th.read_repo("docs/RUN_PARAMETERS.md")
    values = need("run_parameters_fallback")(text)
    rc, out = inventory_check(inventory_ws(tmp_path, rp_header(values) + text))
    assert rc == 0 and "HEADER" not in out, out


@pytest.mark.parametrize("key", KEYS, ids=KEYS)
def test_r061_inventory_check_fails_a_disagreeing_key(tmp_path, key):
    rc, out = inventory_check(inventory_ws(tmp_path, rp_header(changed(key)) + PROSE))
    assert rc == 1 and re.findall(r"^HEADER DISAGREES: (\S+)", out, re.M) == [key], out


def test_r061_inventory_check_refuses_a_malformed_header(tmp_path):
    rc, out = inventory_check(inventory_ws(tmp_path, MALFORMED + PROSE))
    assert rc == 2 and re.search(r"HEADER MALFORMED: (?:\S*/)?docs/RUN_PARAMETERS.md:3 \S", out), out


# ---------------------------------------------------------------- one copy of each reader

LABELS = ("Ceiling above twice", "Agent ceiling", "Design rounds above five", "Review rounds above the ceiling")


@pytest.mark.parametrize("prog", ["bridge-run.py", "loop-guard.py", "review-guard.py", "inventory-check.py"],
                         ids=["bridge-run", "loop-guard", "review-guard", "inventory-check"])
def test_r061_no_program_keeps_a_line_reading_of_its_own(prog):
    tree = tp._tree(prog)
    found = [p for p in tp._re_patterns(tree) if any(label in p for label in LABELS)]
    assert not found, "%s keeps its own reading: %s" % (prog, found)


# ---------------------------------------------------------------- builder's cases below this line


def test_r061_launcher_refuses_header_design_lift_without_owner_line(tmp_path):
    """R-061: a header-only design lift (no matching prose line) must not govern the launch."""
    header = rp_header({**VALUES, "design_rounds_above_five": [
        {"subject": "pace", "rounds": 9, "words": "header only", "date": "2026-11-05"},
    ]})
    prose_no_lift = "\n".join(
        line for line in PROSE.splitlines()
        if not line.strip().lower().startswith("design rounds above five:")
    ) + "\n"
    lab = lab_with(tmp_path, header + prose_no_lift)
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-001")), "bridge-run: refused - header: ")
    assert "disagrees design_rounds_above_five" in line, line


def test_r061_loop_guard_reads_agent_ceiling_with_a_non_utf8_byte(tmp_path, program):
    """R-061: a non-UTF-8 byte in RUN_PARAMETERS.md does not crash the loop guard; it reads the line fallback."""
    lg = program("loop-guard")
    ws = loop_ws(tmp_path, b"Agent ceiling: 5400\n\xff\n".decode("utf-8", "replace"))
    assert lg.agent_ceiling(str(ws)) == 5400
