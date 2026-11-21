"""TASK-068's acceptance tests, the supervisor's (R-088; D-002): the in-flight program.
enforces: docs/REQUIREMENTS.md R-088; docs/DESIGN.md, Change: the program release, "Measurement" (C15, J3); docs/BUILD_PLAN.md,
TASK-068, Done when; D-002 (in_flight --> bridge_env). The builder reads and runs these tests and never edits them.

The interface these tests fix (the brief states it):
  python in-flight.py <text>                       appends `<UTC time to the minute>Z <text>` to the Workspace's
  python in-flight.py --file <path>                run/supervisor/in-flight.md and prints the line it wrote
  python in-flight.py --pass <name> <reviewer> [--round <n>] [--cause <cause>]
                                                   appends `<time> PASS <name> r<n> <reviewer> <cause>`
  The Workspace is the folder holding docs/PROJECT_STATUS.md that the current folder belongs to. A refusal exits 2 and
  writes nothing. The round causes stand once, as bridge_env.ROUND_CAUSES, read by the launcher, the pace report and
  this program.

Every case builds a scratch Workspace under pytest's tmp_path. KP-052: no character outside printable ASCII is typed in
this file."""
import datetime
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.normpath(os.path.join(HERE, os.pardir))
BRIDGE = os.path.join(WORKSPACE, "bridge", "cursor-bridge")
PROG = os.path.join(BRIDGE, "in-flight.py")

SEVEN = ("defect", "security", "fix-induced", "no external path", "records", "builder incomplete", "brief error")
REVIEWERS = ("review-a", "review-b", "security-auditor", "design-auditor", "plan-critic", "design-critic-b", "supervisor")
STAMP = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z"


def scratch(tmp_path):
    ws = tmp_path / "proj" / "Workspace"
    (ws / "docs").mkdir(parents=True)
    (ws / "docs" / "PROJECT_STATUS.md").write_text("# Project Status\nPhase: changing\n", encoding="utf-8")
    return ws


def log_of(ws):
    return ws / "run" / "supervisor" / "in-flight.md"


def run(cwd, *args):
    assert os.path.isfile(PROG), "in-flight.py is not built"
    p = subprocess.run([sys.executable, PROG] + list(args), cwd=str(cwd), capture_output=True, timeout=60)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def lines(ws):
    return log_of(ws).read_text(encoding="utf-8").splitlines() if log_of(ws).exists() else []


def now_minute():
    return datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)


def parse_stamp(line):
    return datetime.datetime.strptime(line[:17], "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc)


def test_r088_a_text_is_appended_with_the_clock_s_time_and_printed(tmp_path):
    """R-088: one line `<UTC time to the minute>Z <text>`, the folder and file created where absent, the line printed."""
    ws = scratch(tmp_path)
    before = now_minute()
    rc, out, err = run(ws, "TASK-068 builder r1 launched")
    after = now_minute()
    assert rc == 0, out + err
    got = lines(ws)
    assert len(got) == 1, got
    assert re.fullmatch(STAMP + " TASK-068 builder r1 launched", got[0]), got
    assert before <= parse_stamp(got[0]) <= after, got
    assert got[0] in out, out


def test_r088_a_second_run_appends_and_never_rewrites(tmp_path):
    """R-088: what stands in the log stays; each run adds exactly one line at the end."""
    ws = scratch(tmp_path)
    log_of(ws).parent.mkdir(parents=True)
    log_of(ws).write_text("an earlier line\n", encoding="utf-8")
    assert run(ws, "one")[0] == 0
    assert run(ws, "two")[0] == 0
    got = lines(ws)
    assert got[0] == "an earlier line" and len(got) == 3, got
    assert got[1].endswith(" one") and got[2].endswith(" two"), got


def test_r088_the_workspace_is_found_from_a_folder_inside_it(tmp_path):
    """R-088: run from a subfolder, the line goes to the Workspace's log, not the subfolder's."""
    ws = scratch(tmp_path)
    sub = ws / "bridge" / "deep"
    sub.mkdir(parents=True)
    rc, out, err = run(sub, "from below")
    assert rc == 0, out + err
    assert lines(ws)[-1].endswith(" from below"), lines(ws)
    assert not (sub / "run").exists()


def test_r088_file_text_has_its_line_breaks_made_spaces(tmp_path):
    """R-088: --file takes a file under run/supervisor/, its line breaks made spaces, in one line."""
    ws = scratch(tmp_path)
    (ws / "run" / "supervisor").mkdir(parents=True)
    src = ws / "run" / "supervisor" / "line.txt"
    src.write_bytes(b"first part\r\nsecond part\nthird part\n")
    rc, out, err = run(ws, "--file", str(src))
    assert rc == 0, out + err
    got = lines(ws)
    assert len(got) == 1 and re.fullmatch(STAMP + " first part second part third part", got[0].rstrip()), got


def test_r088_a_paused_line_in_the_file_stays_a_line_the_loop_guard_reads(tmp_path):
    """R-088 with the loop guard (FB-027): a line beginning `Paused:` keeps a line of its own, so the guard's reading
    of a pause in the log still finds it."""
    ws = scratch(tmp_path)
    (ws / "run" / "supervisor").mkdir(parents=True)
    src = ws / "run" / "supervisor" / "pause.txt"
    src.write_text("position written down\nPaused: the owner's word to resume\nnext step named\n", encoding="utf-8")
    rc, out, err = run(ws, "--file", str(src))
    assert rc == 0, out + err
    got = lines(ws)
    assert any(line.startswith("Paused: the owner's word to resume") for line in got), got
    assert re.match(STAMP + " position written down", got[0]), got
    import importlib.util
    spec = importlib.util.spec_from_file_location("loop_guard_r088", os.path.join(BRIDGE, "loop-guard.py"))
    lg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lg)
    assert lg.paused_in_flight(str(ws)), "the loop guard does not find the pause"


def test_r088_a_pass_line_is_tagged(tmp_path):
    """R-088: --pass <name> <reviewer> --round <n> --cause <cause> appends `<time> PASS <name> r<n> <reviewer> <cause>`."""
    ws = scratch(tmp_path)
    rc, out, err = run(ws, "--pass", "PR-7", "review-a", "--round", "2", "--cause", "records")
    assert rc == 0, out + err
    got = lines(ws)
    assert re.fullmatch(STAMP + " PASS PR-7 r2 review-a records", got[-1]), got
    rc, out, err = run(ws, "--pass", "TASK-068", "review-b", "--round", "1", "--cause", "no external path")
    assert rc == 0, out + err
    assert re.fullmatch(STAMP + " PASS TASK-068 r1 review-b no external path", lines(ws)[-1]), lines(ws)


@pytest.mark.parametrize("reviewer", REVIEWERS)
def test_r088_every_stated_reviewer_kind_is_accepted(tmp_path, reviewer):
    """R-088: the reviewer is one of the stated kinds."""
    ws = scratch(tmp_path)
    rc, out, err = run(ws, "--pass", "TASK-068", reviewer, "--round", "1", "--cause", "defect")
    assert rc == 0, out + err
    assert (" %s defect" % reviewer) in lines(ws)[-1], lines(ws)


@pytest.mark.parametrize("cause", SEVEN)
def test_r088_every_round_cause_is_accepted(tmp_path, cause):
    """R-088: the cause is one of the round causes."""
    ws = scratch(tmp_path)
    rc, out, err = run(ws, "--pass", "TASK-068", "review-a", "--round", "3", "--cause", cause)
    assert rc == 0, out + err
    assert lines(ws)[-1].endswith(" review-a " + cause), lines(ws)


@pytest.mark.parametrize("args", [
    ["--pass", "TASK-068", "reviewer-c", "--round", "1", "--cause", "defect"],
    ["--pass", "TASK-068", "review-a", "--round", "1", "--cause", "weather"],
    ["--pass", "TASK-068", "review-a", "--round", "zero", "--cause", "defect"],
], ids=["unknown-reviewer", "unknown-cause", "round-not-a-number"])
def test_r088_a_word_outside_the_lists_is_refused_and_nothing_written(tmp_path, args):
    """R-088: a reviewer or cause outside its list, or a round that is no number, exits 2 and writes nothing."""
    ws = scratch(tmp_path)
    rc, out, err = run(ws, *args)
    assert rc == 2, out + err
    assert lines(ws) == []


def test_r088_outside_a_workspace_it_refuses_and_writes_nothing(tmp_path):
    """R-088: no docs/PROJECT_STATUS.md above the current folder: exit 2, no run/ folder made."""
    plain = tmp_path / "plain"
    plain.mkdir()
    rc, out, err = run(plain, "a text")
    assert rc == 2, out + err
    assert not (plain / "run").exists()


@pytest.mark.parametrize("case", ["no-text", "empty-text", "file-and-text", "control-character"])
def test_r088_no_text_both_sources_or_a_control_character_is_refused(tmp_path, case):
    """R-088: no text, an empty text, a file and a text together, and a text holding a control character each exit 2
    and write nothing."""
    ws = scratch(tmp_path)
    (ws / "run" / "supervisor").mkdir(parents=True)
    src = ws / "run" / "supervisor" / "line.txt"
    src.write_text("text\n", encoding="utf-8")
    if case == "no-text":
        rc, out, err = run(ws)
    elif case == "empty-text":
        rc, out, err = run(ws, "")
    elif case == "file-and-text":
        rc, out, err = run(ws, "--file", str(src), "a text")
    else:
        rc, out, err = run(ws, "before" + chr(27) + "[2Jafter")
    assert rc == 2, out + err
    assert lines(ws) == []


def test_r088_a_file_outside_run_supervisor_is_refused(tmp_path):
    """R-088: --file names a file under that Workspace's run/supervisor/ by its resolved path; one elsewhere in the
    Workspace, or outside it, is refused."""
    ws = scratch(tmp_path)
    (ws / "run" / "supervisor").mkdir(parents=True)
    inside_ws = ws / "docs" / "note.txt"
    inside_ws.write_text("x\n", encoding="utf-8")
    outside = tmp_path / "elsewhere.txt"
    outside.write_text("y\n", encoding="utf-8")
    dotted = os.path.join(str(ws), "run", "supervisor", os.pardir, os.pardir, "docs", "note.txt")
    for path in (str(inside_ws), str(outside), dotted):
        rc, out, err = run(ws, "--file", path)
        assert rc == 2, (path, out + err)
    assert lines(ws) == []


def test_r088_a_file_reached_through_a_link_is_refused(tmp_path):
    """R-088: a --file path through a link is refused, even when the link stands under run/supervisor/."""
    ws = scratch(tmp_path)
    sup = ws / "run" / "supervisor"
    sup.mkdir(parents=True)
    target = tmp_path / "target.txt"
    target.write_text("through a link\n", encoding="utf-8")
    link = sup / "link.txt"
    try:
        os.symlink(str(target), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("this account cannot create a symbolic link")
    rc, out, err = run(ws, "--file", str(link))
    assert rc == 2, out + err
    assert lines(ws) == []


def test_r088_concurrent_runs_never_interleave_within_a_line(tmp_path):
    """R-088: the write is one append, so eight runs started together leave eight whole lines."""
    ws = scratch(tmp_path)
    (ws / "run" / "supervisor").mkdir(parents=True)
    texts = ["run%d-" % i + ("abcdefgh%d" % i) * 400 for i in range(8)]
    procs = [subprocess.Popen([sys.executable, PROG, t], cwd=str(ws), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             for t in texts]
    for p in procs:
        assert p.wait(timeout=120) == 0
    got = lines(ws)
    assert len(got) == 8, len(got)
    assert sorted(line[18:] for line in got) == sorted(texts)


def _load(name, filename):
    import importlib.util
    sys.path.insert(0, BRIDGE)
    try:
        spec = importlib.util.spec_from_file_location(name, os.path.join(BRIDGE, filename))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(BRIDGE)


def test_r088_the_round_causes_stand_once_in_bridge_env():
    """R-088: the seven round causes of release S stand once, as bridge_env.ROUND_CAUSES, unchanged."""
    env = _load("bridge_env_r088", "bridge_env.py")
    assert tuple(env.ROUND_CAUSES) == SEVEN


@pytest.mark.parametrize("filename", ["bridge-run.py", "pace-report.py", "in-flight.py"])
def test_r088_the_launcher_the_report_and_this_program_hold_no_copy_of_the_list(filename):
    """R-088: the launcher, the pace report and the in-flight program read bridge_env's list and hold no list of their
    own: no tuple or list literal of the causes in their source, and each names bridge_env.ROUND_CAUSES."""
    with open(os.path.join(BRIDGE, filename), encoding="utf-8") as f:
        src = f.read()
    assert "bridge_env.ROUND_CAUSES" in src, filename
    assert not re.search(r"""["']builder incomplete["']\s*,\s*["']brief error["']""", src), filename


def test_r088_the_launcher_and_the_report_see_the_same_list_as_bridge_env():
    """R-088: loaded, the launcher's and the report's readings of the causes are bridge_env's seven (the report adds
    `unstated`, the word for none)."""
    env = _load("bridge_env_r088b", "bridge_env.py")
    launcher = _load("bridge_run_r088", "bridge-run.py")
    report = _load("pace_report_r088", "pace-report.py")
    assert tuple(getattr(launcher, "ROUND_CAUSES", env.ROUND_CAUSES)) == SEVEN
    report_list = tuple(getattr(report, "ROUND_CAUSES", tuple(env.ROUND_CAUSES) + ("unstated",)))
    assert report_list[:7] == SEVEN and set(report_list) - set(SEVEN) <= {"unstated"}


def test_r088_the_loop_guard_s_refusal_names_the_in_flight_log_and_the_program():
    """R-088 (J3): the loop guard's refusal names run/supervisor/in-flight.md and in-flight.py where it named the status
    file's `In flight:` line; its decision is the loop guard's own tests' (tests/test_loop_guard.py)."""
    with open(os.path.join(BRIDGE, "loop-guard.py"), encoding="utf-8") as f:
        src = f.read()
    assert "in-flight.py" in src and "run/supervisor/in-flight.md" in src
    assert "status file's `In flight:` line" not in src


# Round 2 (TASK-068-r2): the reviewers' findings on round 1, each held by a test.

def _guard():
    import importlib.util
    spec = importlib.util.spec_from_file_location("loop_guard_r088_r2", os.path.join(BRIDGE, "loop-guard.py"))
    lg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lg)
    return lg


def test_r088_r2_every_line_the_program_writes_ends_with_lf_alone(tmp_path):
    """R-088 (round 2, Review A's B1): the log's raw bytes hold no carriage return, whatever the platform's text mode."""
    ws = scratch(tmp_path)
    (ws / "run" / "supervisor").mkdir(parents=True)
    src = ws / "run" / "supervisor" / "pause.txt"
    src.write_text("a line\nPaused: until the owner\n", encoding="utf-8")
    assert run(ws, "plain text")[0] == 0
    assert run(ws, "--file", str(src))[0] == 0
    assert run(ws, "--pass", "TASK-068", "review-a", "--round", "1", "--cause", "defect")[0] == 0
    raw = log_of(ws).read_bytes()
    assert b"\r" not in raw and raw.endswith(b"\n"), raw


def test_r088_r2_a_later_paused_line_lifts_or_replaces_an_earlier_one(tmp_path):
    """R-088 (round 2, convergent: Review A's B2 and the security review's blocking finding): the loop guard reads the
    last `Paused:` line of the log, so a pause written through the program can be lifted through it, and set again."""
    ws = scratch(tmp_path)
    lg = _guard()
    assert run(ws, "Paused: the owner's word to resume")[0] == 0
    assert lg.paused_in_flight(str(ws)) == "the owner's word to resume"
    assert run(ws, "Paused: resumed 11-21")[0] == 0
    assert lg.paused_in_flight(str(ws)) is None
    assert run(ws, "an ordinary line after the resume")[0] == 0
    assert lg.paused_in_flight(str(ws)) is None
    assert run(ws, "Paused: the install run sheet")[0] == 0
    assert lg.paused_in_flight(str(ws)) == "the install run sheet"
    assert run(ws, "Paused: no")[0] == 0
    assert lg.paused_in_flight(str(ws)) is None


def test_r088_r2_an_empty_file_option_beside_a_text_is_two_sources(tmp_path):
    """R-088 (round 2, Review A's SF1): `--file ""` beside a text is two sources, refused, nothing written."""
    ws = scratch(tmp_path)
    rc, out, err = run(ws, "--file", "", "free text")
    assert rc == 2, out + err
    assert lines(ws) == []


@pytest.mark.parametrize("text", ["PASS TASK-1 r9 review-a defect", "pass PR-3 r1 review-b records", "Pass X"])
def test_r088_r2_a_free_text_cannot_forge_a_pass_line(tmp_path, text):
    """R-088 (round 2, convergent: Review A and the security review): a text, or a --file text, whose first word is
    PASS in any letter case is refused, so a tagged line comes from --pass alone."""
    ws = scratch(tmp_path)
    (ws / "run" / "supervisor").mkdir(parents=True)
    rc, out, err = run(ws, text)
    assert rc == 2, out + err
    src = ws / "run" / "supervisor" / "line.txt"
    src.write_text(text + "\nmore\n", encoding="utf-8")
    rc, out, err = run(ws, "--file", str(src))
    assert rc == 2, out + err
    assert lines(ws) == []


def _junction(target, link):
    try:
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
        return True
    except Exception:
        try:
            os.symlink(str(target), str(link), target_is_directory=True)
            return True
        except (OSError, NotImplementedError):
            return False


@pytest.mark.parametrize("where", ["run", "supervisor"])
def test_r088_r2_a_log_folder_that_is_a_link_is_refused(tmp_path, where):
    """R-088 (round 2, convergent: Review A's note and the security review): where `run/` or `run/supervisor/` is a
    junction or link leading out of the Workspace, the program refuses and appends nothing there."""
    ws = scratch(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    if where == "run":
        made = _junction(outside, ws / "run")
    else:
        (ws / "run").mkdir()
        made = _junction(outside, ws / "run" / "supervisor")
    if not made:
        pytest.skip("this account can create neither a junction nor a link")
    try:
        rc, out, err = run(ws, "a text")
        assert rc == 2, out + err
        assert list(outside.rglob("*.md")) == []
    finally:
        os.rmdir(str(ws / "run")) if where == "run" else os.rmdir(str(ws / "run" / "supervisor"))

