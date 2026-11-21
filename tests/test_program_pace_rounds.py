"""TASK-069's acceptance tests, the supervisor's (R-089; D-003): review passes and round causes in the pace report.
enforces: docs/REQUIREMENTS.md R-089; docs/DESIGN.md, "C20 as reshaped, F1, F6, C14"; docs/BUILD_PLAN.md, TASK-069,
Done when; D-003 (the rounds record's `cause` field and its readers). The builder reads and runs these tests and never
edits them.

What they fix, through each program's command line and records:
  - bridge_env.ROUND_CAUSES is the one list of round causes, the seven of release S and `base update`; `unstated` is
    no member of it, it is what a reader writes where nothing on the list is stated.
  - the in-flight program and the launcher accept the new cause with no edit of theirs.
  - `review-guard.py snapshot` writes the round's cause, read from the first `Round cause:` line of
    run/review/SCOPE-<ID>.md, into the round's entry of .git/bridge/rounds-<ID>.json, `unstated` where the line is
    missing or names a word outside the list, never a refusal; a re-snapshot of the round reads the line again.
  - `pace-report.py` counts a name (an increment's ID, or PR-<n>) by a brief, a guard rounds record or a tagged pass
    line, and PR-<n> also by its squash on refs/heads/main; merged by main alone; PR-<n> folds into the first counted
    name its squash subject names; one cause per name and round after the first (builder row, guard round, pass line,
    in that order); one line per week of recorded passes per reviewer kind, ending `recorded passes only`; a round
    stands in the week of its earliest record; the builder-rounds-per-model line unchanged; the HARDENING column reads
    refs/heads/main.

Every case builds a scratch project under pytest's tmp_path; git runs with the global and system configuration
isolated; review-guard runs with the home folder and its hash-copy folder redirected into tmp_path; nothing reads
GitHub or the network. Every subprocess call has a time limit. KP-052: no character outside printable ASCII is typed
in this file."""
import datetime
import json
import os
import re
import subprocess
import sys

from test_task032_supervisor_launcher import Lab, assert_ran, build, launch, write_brief

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, os.pardir))
BRIDGE = os.path.join(WORKSPACE, "bridge", "cursor-bridge")
PACE = os.path.join(BRIDGE, "pace-report.py")
GUARD = os.path.join(BRIDGE, "review-guard.py")
IN_FLIGHT = os.path.join(BRIDGE, "in-flight.py")
LIMIT = 120

SEVEN = ("defect", "security", "fix-induced", "no external path", "records", "builder incomplete", "brief error")
EIGHT = SEVEN + ("base update",)
COUNTED = EIGHT + ("unstated",)
KINDS = ("review-a", "review-b", "security-auditor", "design-auditor", "plan-critic", "design-critic-b", "supervisor")
PASSES_END = "recorded passes only"
STAMP = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z"

UTC = datetime.timezone.utc
NOW = datetime.datetime.now(UTC)
MONDAY0 = datetime.datetime.combine(NOW.date() - datetime.timedelta(days=NOW.weekday()), datetime.time(0, 0), tzinfo=UTC)


# ---------------------------------------------------------------- helpers (the pattern of tests/test_pace_report.py)


def at(k, day=2, hour=12):
    """A time k ISO weeks before this one: day 0 is its Monday, day 6 its Sunday."""
    return MONDAY0 - datetime.timedelta(weeks=k) + datetime.timedelta(days=day, hours=hour)


def week(k):
    y, w, _ = (MONDAY0 - datetime.timedelta(weeks=k)).date().isocalendar()
    return (y, w)


def label(k):
    return "%d-W%02d" % week(k)


def gitdate(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+0000")


def run_id(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def minute(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%MZ")


def git_env():
    return dict(
        os.environ,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_SYSTEM=os.devnull,
        GIT_TERMINAL_PROMPT="0",
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
    )


def git(folder, *args, env=None):
    p = subprocess.run(["git", "-C", str(folder)] + list(args), env=env or git_env(), capture_output=True, text=True,
                       timeout=LIMIT)
    assert p.returncode == 0, "fixture git %s failed: %s" % (" ".join(args), p.stderr)
    return p.stdout


def pace(args, cwd):
    p = subprocess.run([sys.executable, PACE] + [str(a) for a in args], cwd=str(cwd), env=git_env(),
                       capture_output=True, timeout=LIMIT)
    return p.returncode, p.stdout.decode("ascii", "replace"), p.stderr.decode("ascii", "replace")


class MiniProject(object):
    """<tmp>/<name>/Workspace, a git repository on main with run/ ignored."""

    def __init__(self, tmp_path, name="proj"):
        self.root = tmp_path / name
        self.ws = self.root / "Workspace"
        self.ws.mkdir(parents=True)
        git(self.ws, "init", "-q", "-b", "main")
        (self.ws / ".gitignore").write_text("run/\n", encoding="utf-8")
        self.rows = []
        self.passes = []

    def brief(self, ident):
        p = self.ws / "handoff" / ("%s.md" % ident)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# %s\n" % ident, encoding="utf-8")

    def commit(self, subject, when):
        git(self.ws, "add", "-A")
        env = dict(git_env(), GIT_AUTHOR_DATE=gitdate(when), GIT_COMMITTER_DATE=gitdate(when))
        git(self.ws, "commit", "-q", "--allow-empty", "--no-verify", "-m", subject, env=env)

    def builder(self, ident, rnd, when, model="composer-2.5", cause=None):
        """One launcher builder row, as bridge-run.py writes it; `cause` only where given."""
        row = {"id": run_id(when), "kind": "builder", "model": model, "branch": ident.lower(), "exit": 0, "brief": ident,
               "round": rnd, "brief_name": ident if rnd == 1 else "%s-r%d" % (ident, rnd), "merge_ids": [ident]}
        if cause is not None:
            row["cause"] = cause
        self.rows.append(row)
        log = self.ws / "run" / "launcher"
        log.mkdir(parents=True, exist_ok=True)
        (log / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in self.rows), encoding="utf-8")

    def guard(self, ident, rounds):
        """A guard rounds record, .git/bridge/rounds-<ident>.json, in the shape review-guard.py writes: rounds is a
        list of (round, time, cause or None); an entry with no cause carries no cause field."""
        entries = []
        for rnd, when, cause in rounds:
            entry = {"round": rnd, "name": ident if rnd == 1 else "%s-r%d" % (ident, rnd), "branch": ident.lower(),
                     "tree": "0" * 40, "time": run_id(when), "lift": None, "lift_line": None, "reply": None}
            if cause is not None:
                entry["cause"] = cause
            entries.append(entry)
        folder = self.ws / ".git" / "bridge"
        folder.mkdir(parents=True, exist_ok=True)
        data = {"id": ident, "merge_ids": [ident], "rounds": entries}
        (folder / ("rounds-%s.json" % ident)).write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")

    def pass_line(self, when, text):
        """One line of run/supervisor/in-flight.md, `<UTC time to the minute>Z <text>`, as in-flight.py writes it."""
        self.passes.append("%s %s" % (minute(when), text))
        log = self.ws / "run" / "supervisor"
        log.mkdir(parents=True, exist_ok=True)
        (log / "in-flight.md").write_text("".join(l + "\n" for l in self.passes), encoding="utf-8")

    def report(self, tmp_path, *extra):
        rc, out, err = pace([self.root] + list(extra), tmp_path)
        assert rc == 0, out + err
        assert "Traceback" not in err, err
        return out


def table(out):
    """{week label: cells} of the pace table's week rows."""
    rows = {}
    for line in out.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and re.match(r"^\d{4}-W\d{2}$", cells[0]):
            rows[cells[0]] = cells
    return rows


def total_row(out):
    for line in out.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == "Total":
            return cells
    raise AssertionError("no Total row:\n" + out)


def cause_lines(out):
    return [l for l in out.splitlines() if l.startswith("Round causes")]


def cause_counts(line):
    """{cause: count} of one cause line, read as `<cause> <count>` for every cause the report may name."""
    got = {}
    for cause in COUNTED:
        m = re.search(r"(?<![\w-])%s (\d+)" % re.escape(cause), line)
        if m:
            got[cause] = int(m.group(1))
    return got


def passes_lines(out):
    return [l for l in out.splitlines() if l.rstrip().endswith(PASSES_END)]


def passes_line(out, k):
    """The passes line of week k, or None; never two."""
    got = [l for l in passes_lines(out) if label(k) in l]
    assert len(got) <= 1, "two passes lines for %s:\n%s" % (label(k), out)
    return got[0] if got else None


def kind_count(line, kind):
    """The count a passes line gives a reviewer kind, written as the kind followed by its count; 0 where absent."""
    if line is None:
        return 0
    m = re.search(r"(?<![\w-])%s[\s:=]*(\d+)" % re.escape(kind), line)
    return int(m.group(1)) if m else 0


def tracked_old_brief(p):
    """An old increment with a tracked brief, merged before the window: handoff/ is tracked, as in the field."""
    p.brief("TASK-001")
    p.commit("records: the first brief", at(20))
    p.commit("TASK-001: the first increment (#1)", at(20, day=3))


# ---------------------------------------------------------------- 1. the one list of round causes


def test_r089_round_causes_are_the_seven_and_base_update(program):
    """R-089: bridge_env.ROUND_CAUSES is release S's seven causes and `base update`, in that order; `unstated` is no
    cause of the list (it is what a reader writes where none is stated)."""
    be = program("bridge_env")
    assert tuple(be.ROUND_CAUSES) == EIGHT, be.ROUND_CAUSES
    assert "unstated" not in be.ROUND_CAUSES


# ---------------------------------------------------------------- 2. the in-flight program and the launcher take it


def test_r089_in_flight_and_the_launcher_accept_base_update(tmp_path):
    """R-089: `in-flight.py --pass <name> review-b --round 2 --cause "base update"` writes the PASS line ending with
    the cause, and the launcher reads a brief's `Round cause: base update - ...` into the run log as that cause, with
    no edit of either program."""
    ws = tmp_path / "flight" / "Workspace"
    (ws / "docs").mkdir(parents=True)
    (ws / "docs" / "PROJECT_STATUS.md").write_text("# Project Status\nPhase: changing\n", encoding="utf-8")
    p = subprocess.run([sys.executable, IN_FLIGHT, "--pass", "TASK-069", "review-b", "--round", "2", "--cause",
                        "base update"], cwd=str(ws), capture_output=True, timeout=60)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    log = ws / "run" / "supervisor" / "in-flight.md"
    written = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    flight_ok = (p.returncode == 0 and len(written) == 1
                 and re.fullmatch(STAMP + " PASS TASK-069 r2 review-b base update", written[0]) is not None)

    lab = Lab(tmp_path / "launcher")
    write_brief(lab.root, "TASK-001-r2", extra="\nRound cause: base update - main took the status file first\n")
    res = launch(lab, build("TASK-001-r2"))
    row = assert_ran(res)
    launcher_ok = row.get("cause") == "base update" and row.get("round") == 2

    assert flight_ok and launcher_ok, (
        "in-flight: rc %r, lines %r, output %r; launcher row %r, stderr %r" % (p.returncode, written, out, row, res.err))


# ---------------------------------------------------------------- 3. the guard writes the round's cause


def guard_env(tmp_path):
    env = git_env()
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["BRIDGE_REVIEW_HASHES"] = str(tmp_path / "review-hashes")
    return env


def guard_repo(tmp_path, name):
    """A scratch repository on branch task-001 with one review input committed, as the ceiling's tests build it."""
    r = tmp_path / name / "ws"
    r.mkdir(parents=True)
    git(r, "init", "-q", "-b", "main")
    (r / ".gitignore").write_text("run/\n", encoding="utf-8")
    (r / "a.py").write_text("1\n", encoding="utf-8")
    (r / "run" / "review").mkdir(parents=True)
    (r / "run" / "review" / "REVIEW-TASK-001.diff").write_text("d\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    git(r, "checkout", "-q", "-b", "task-001")
    git(r, "add", "-f", "run/review/REVIEW-TASK-001.diff")
    git(r, "commit", "-q", "-m", "TASK-001")
    return r


def snapshot(repo, env, name):
    p = subprocess.run([sys.executable, GUARD, "snapshot", name], cwd=str(repo), env=env, capture_output=True,
                       text=True, timeout=LIMIT)
    return p.returncode, p.stdout + p.stderr


def write_scope(repo, text, message):
    (repo / "run" / "review" / "SCOPE-TASK-001.md").write_text(text, encoding="utf-8")
    git(repo, "add", "-f", "run/review/SCOPE-TASK-001.md")
    git(repo, "commit", "-q", "-m", message)


def round_entry(repo, rnd):
    data = json.loads((repo / ".git" / "bridge" / "rounds-TASK-001.json").read_text(encoding="utf-8"))
    got = [r for r in data.get("rounds", []) if r.get("round") == rnd]
    assert len(got) == 1, data
    return got[0]


def test_r089_the_guard_writes_the_round_s_cause_beside_its_time(tmp_path):
    """R-089, D-003: `review-guard.py snapshot TASK-001-r2` reads the first line of run/review/SCOPE-TASK-001.md that
    begins `Round cause:` into round 2's entry of .git/bridge/rounds-TASK-001.json as `cause`, beside its time; a SCOPE
    file with no such line, and one whose word is outside the list, each give `unstated` and the snapshot succeeds; a
    re-snapshot of the round after the line changed reads it again."""
    env = guard_env(tmp_path)
    cases = [
        ("stated", "# Scope of TASK-001-r2\n\nRound cause: records - the status file was stale\n"
                   "Round cause: defect - a second line, never the one read\n", "records"),
        ("missing", "# Scope of TASK-001-r2\n\nThe round re-reads the fix of round 1.\n", "unstated"),
        ("outside", "# Scope of TASK-001-r2\n\nRound cause: polish - nicer names\n", "unstated"),
    ]
    repos = {}
    for name, text, want in cases:
        repo = guard_repo(tmp_path, name)
        repos[name] = repo
        rc, out = snapshot(repo, env, "TASK-001")
        assert rc == 0, out
        write_scope(repo, text, "scope of round 2")
        rc, out = snapshot(repo, env, "TASK-001-r2")
        assert rc == 0, "%s: the snapshot is never refused for its cause: %s" % (name, out)
        entry = round_entry(repo, 2)
        assert isinstance(entry.get("time"), str) and entry["time"], entry
        assert entry.get("cause") == want, "%s: %r" % (name, entry)

    repo = repos["stated"]
    write_scope(repo, "# Scope of TASK-001-r2\n\nRound cause: base update - main took the status file first\n",
                "scope of round 2, read again")
    rc, out = snapshot(repo, env, "TASK-001-r2")
    assert rc == 0, out
    entry = round_entry(repo, 2)
    assert entry.get("cause") == "base update", entry
    assert isinstance(entry.get("time"), str) and entry["time"], entry
    assert not (tmp_path / "home" / ".cursor-bridge").exists(), "a hash copy reached the home folder"


# ---------------------------------------------------------------- 4. the pace report


def test_r089_the_field_week_is_counted(tmp_path):
    """R-089 (F6), the field's week: a calibration of three guard rounds whose second says `records`, a dependency
    increment and a configuration increment with guard records and no brief, a records pull request with a pass line
    PR-<n> and its squash on main (its subject begins with a capitalised word and a colon), and a name with a guard
    record whose branch never merged: 5 started, 4 merged, and the cause line counts the calibration's two later
    rounds. The name that never merged is started and not merged."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    p.guard("CALIB-1", [(1, at(2, day=0, hour=9), None), (2, at(2, day=1, hour=9), "records"),
                        (3, at(2, day=2, hour=9), None)])
    p.guard("DEP-2", [(1, at(2, day=0, hour=10), None)])
    p.guard("CONFIG-3", [(1, at(2, day=0, hour=11), None)])
    p.guard("SPIKE-5", [(1, at(2, day=1, hour=10), None)])
    p.pass_line(at(2, day=0, hour=8), "TASK-069 builder r1 launched")
    p.pass_line(at(2, day=3, hour=9), "PASS PR-24 r1 supervisor")
    p.commit("CALIB-1: the calibration, in three rounds (#21)", at(2, day=3, hour=12))
    p.commit("DEP-2: the pinned library raised (#22)", at(2, day=3, hour=13))
    p.commit("CONFIG-3: the linter's configuration (#23)", at(2, day=3, hour=14))
    p.commit("Records: the week's status and the in-flight log (#24)", at(2, day=4, hour=9))
    git(p.ws, "checkout", "-q", "-b", "spike-5")
    p.commit("SPIKE-5: the spike, never merged", at(2, day=4, hour=10))
    git(p.ws, "checkout", "-q", "main")

    out = p.report(tmp_path)
    row = table(out)[label(2)]
    assert row[1:3] == ["5", "4"], "started and merged of %s: %r\n%s" % (label(2), row, out)
    total = total_row(out)
    assert total[1:3] == ["5", "4"], total
    lines = cause_lines(out)
    assert len(lines) == 1, out
    assert lines[0].startswith("Round causes (2 rounds after the first): "), lines[0]
    counts = cause_counts(lines[0])
    assert counts.get("records") == 1 and counts.get("unstated") == 1 and sum(counts.values()) == 2, lines[0]

    q = MiniProject(tmp_path, name="never-merged")
    tracked_old_brief(q)
    q.guard("SPIKE-5", [(1, at(2, day=1, hour=10), None)])
    git(q.ws, "checkout", "-q", "-b", "spike-5")
    q.commit("SPIKE-5: the spike, never merged", at(2, day=4, hour=10))
    out = q.report(tmp_path)
    assert table(out)[label(2)][1:3] == ["1", "0"], out
    assert total_row(out)[1:3] == ["1", "0"], out


def test_r089_a_pull_request_folds_into_the_name_its_squash_names(tmp_path):
    """R-089: a pass line PR-31 whose squash names TASK-301 (a brief) counts as TASK-301, one merge and no name of its
    own; a squash naming TASK-302 and TASK-303 folds PR-32's pass into the first, TASK-302; a pass line PR-33 for a
    pull request main does not hold is started and not merged. Week: 4 started (TASK-301, 302, 303 and PR-33), 3 merged;
    passes: review-b 2 (the guard rounds of TASK-301 and TASK-302, the folded pass lines adding none), review-a 1."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    for ident in ("TASK-301", "TASK-302", "TASK-303"):
        p.brief(ident)
    p.commit("records: three briefs", at(6))
    p.builder("TASK-301", 1, at(3, day=0, hour=10))
    p.builder("TASK-302", 1, at(3, day=0, hour=11))
    p.builder("TASK-303", 1, at(3, day=0, hour=12))
    p.guard("TASK-301", [(1, at(3, day=1, hour=10), None)])
    p.guard("TASK-302", [(1, at(3, day=1, hour=11), None)])
    p.pass_line(at(3, day=1, hour=15), "PASS PR-31 r1 review-b")
    p.pass_line(at(3, day=1, hour=16), "PASS PR-32 r1 review-b")
    p.pass_line(at(3, day=2, hour=9), "PASS PR-33 r1 review-a")
    p.commit("TASK-301: the first feature (#31)", at(3, day=2, hour=12))
    p.commit("TASK-302, TASK-303: two features in one pull request (#32)", at(3, day=2, hour=13))

    out = p.report(tmp_path)
    row = table(out)[label(3)]
    assert row[1:3] == ["4", "3"], "started and merged of %s: %r\n%s" % (label(3), row, out)
    assert total_row(out)[1:3] == ["4", "3"], out
    line = passes_line(out, 3)
    assert line is not None, out
    assert kind_count(line, "review-b") == 2, line
    assert kind_count(line, "review-a") == 1, line


def test_r089_a_round_s_cause_is_the_first_stated_of_builder_guard_and_pass(tmp_path):
    """R-089: one cause per name and round after the first, the first stated among the builder's launcher row, the
    guard's round and a pass line: a builder row saying `unstated` beside a guard round saying `records` counts records;
    a builder `defect` beside a guard `records` counts defect; neither stated and a pass line's `fix-induced` counts
    fix-induced; a builder row's `base update` counts base update. No round counts unstated."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    for ident in ("TASK-401", "TASK-402", "TASK-403", "TASK-404"):
        p.brief(ident)
    p.commit("records: four briefs", at(6))
    p.builder("TASK-401", 1, at(2, day=0, hour=9))
    p.builder("TASK-401", 2, at(2, day=1, hour=9), cause="unstated")
    p.guard("TASK-401", [(1, at(2, day=0, hour=12), None), (2, at(2, day=1, hour=12), "records")])
    p.builder("TASK-402", 1, at(2, day=0, hour=10))
    p.builder("TASK-402", 2, at(2, day=1, hour=10), cause="defect")
    p.guard("TASK-402", [(1, at(2, day=0, hour=13), None), (2, at(2, day=1, hour=13), "records")])
    p.builder("TASK-403", 1, at(2, day=0, hour=11))
    p.builder("TASK-403", 2, at(2, day=1, hour=11))
    p.guard("TASK-403", [(1, at(2, day=0, hour=14), None), (2, at(2, day=1, hour=14), "unstated")])
    p.pass_line(at(2, day=1, hour=15), "PASS TASK-403 r2 review-a fix-induced")
    p.builder("TASK-404", 1, at(2, day=0, hour=12))
    p.builder("TASK-404", 2, at(2, day=1, hour=12), cause="base update")

    out = p.report(tmp_path)
    lines = cause_lines(out)
    assert len(lines) == 1, out
    assert lines[0].startswith("Round causes (4 rounds after the first): "), lines[0]
    counts = cause_counts(lines[0])
    assert counts == {"records": 1, "defect": 1, "fix-induced": 1, "base update": 1}, lines[0]


def test_r089_one_line_per_week_of_recorded_passes(tmp_path):
    """R-089: one line per week of recorded passes by reviewer kind, ending `recorded passes only`, holding the week's
    label: a guard round is a review-b pass; a review-b pass line for the same name and round adds nothing; one with no
    round number is round 1 and adds nothing beside guard round 1; a review-b pass line for a round the guard holds
    none of counts; a review-a pass line counts once under review-a, however often it is written."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    p.brief("TASK-501")
    p.brief("TASK-502")
    p.commit("records: two briefs", at(6))
    p.guard("TASK-501", [(1, at(4, day=1, hour=9), None), (2, at(4, day=2, hour=9), None)])
    p.pass_line(at(4, day=1, hour=14), "PASS TASK-501 r1 review-b")
    p.pass_line(at(4, day=1, hour=15), "PASS TASK-501 review-b")
    p.pass_line(at(4, day=1, hour=16), "PASS TASK-501 r1 review-a")
    p.pass_line(at(4, day=1, hour=17), "PASS TASK-501 r1 review-a")
    p.pass_line(at(4, day=3, hour=9), "PASS TASK-501 r3 review-b")
    p.guard("TASK-502", [(1, at(5, day=2, hour=9), None)])

    out = p.report(tmp_path)
    for line in passes_lines(out):
        assert re.search(r"\d{4}-W\d{2}", line), line
    four = passes_line(out, 4)
    assert four is not None, out
    assert kind_count(four, "review-b") == 3, four
    assert kind_count(four, "review-a") == 1, four
    for kind in ("security-auditor", "design-auditor", "plan-critic", "design-critic-b", "supervisor"):
        assert kind_count(four, kind) == 0, four
    five = passes_line(out, 5)
    assert five is not None, out
    assert kind_count(five, "review-b") == 1 and kind_count(five, "review-a") == 0, five


def test_r089_a_round_that_crosses_a_week_s_end_is_counted_once(tmp_path):
    """R-089: round 2 of TASK-601 has its builder row on a Sunday (cause defect) and its guard round on the next Monday
    (cause records): the cause line counts it once, as defect, and the passes lines hold its review-b pass once, in the
    Monday's week; with a window that begins on that Monday the round stands outside it (it stands in the Sunday's
    week), while the Monday's pass is still there."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    p.brief("TASK-601")
    p.commit("records: the brief", at(6))
    sunday = at(2, day=6, hour=20)
    monday = at(1, day=0, hour=9)
    assert sunday.isoweekday() == 7 and monday.isoweekday() == 1 and (monday - sunday) < datetime.timedelta(days=1)
    p.builder("TASK-601", 1, at(3, day=2, hour=9))
    p.builder("TASK-601", 2, sunday, cause="defect")
    p.guard("TASK-601", [(1, at(3, day=2, hour=12), None), (2, monday, "records")])

    out = p.report(tmp_path)
    lines = cause_lines(out)
    assert len(lines) == 1, out
    assert lines[0].startswith("Round causes (1 rounds after the first): "), lines[0]
    assert cause_counts(lines[0]) == {"defect": 1}, lines[0]
    assert sum(kind_count(l, "review-b") for l in passes_lines(out)) == 2, out
    assert kind_count(passes_line(out, 1), "review-b") == 1, out
    assert kind_count(passes_line(out, 2), "review-b") == 0, out

    out = p.report(tmp_path, "--weeks", "2")
    for line in cause_lines(out):
        assert not cause_counts(line), "the round stands in the Sunday's week, outside the window: %s" % line
    assert kind_count(passes_line(out, 1), "review-b") == 1, out


def test_r089_the_builder_rounds_per_model_line_is_unchanged(tmp_path):
    """R-089: the builder-rounds-per-model line keeps its form and counts builder rows only, a guard round with no
    builder row adding nothing to it."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    p.brief("TASK-701")
    p.commit("records: the brief", at(6))
    p.builder("TASK-701", 1, at(2, day=0, hour=9))
    p.builder("TASK-701", 2, at(2, day=1, hour=9), cause="defect")
    p.guard("TASK-701", [(1, at(2, day=0, hour=12), None), (2, at(2, day=1, hour=12), None),
                         (3, at(2, day=2, hour=12), "records")])

    out = p.report(tmp_path)
    models = [l for l in out.splitlines() if l.startswith("Builder rounds per model")]
    assert models == ["Builder rounds per model: composer-2.5 2 round(s) over 1 increment(s), mean 2"], out


def test_r089_the_hardening_column_reads_refs_heads_main(tmp_path):
    """R-089 (C14): the HARDENING column counts docs/HARDENING.md lines added on refs/heads/main per week: three weeks
    of 5, 7 and 11 lines; 13 and 17 lines committed on another branch, checked out while the report runs, are not
    counted."""
    p = MiniProject(tmp_path)
    hard = p.ws / "docs" / "HARDENING.md"
    hard.parent.mkdir(parents=True)
    written = []

    def add(n, tag, when):
        written.extend("- %s line %d" % (tag, i) for i in range(n))
        hard.write_text("".join(l + "\n" for l in written), encoding="utf-8")
        p.commit("docs: %d HARDENING lines (%s)" % (n, tag), when)

    add(5, "main a", at(3))
    add(7, "main b", at(2))
    add(11, "main c", at(1))
    git(p.ws, "checkout", "-q", "-b", "side")
    add(13, "side a", at(2, day=4))
    add(17, "side b", at(1, day=4))

    out = p.report(tmp_path)
    rows = table(out)
    assert rows[label(3)][5] == "5", rows[label(3)]
    assert rows[label(2)][5] == "7", rows[label(2)]
    assert rows[label(1)][5] == "11", rows[label(1)]
    assert total_row(out)[5] == "23", out


# ---------------------------------------------------------------- Round 2 (TASK-069-r2): Review A's two behaviour
# findings, its should-fix on the ISS-013 subject, and the security review's two hardenings.


def test_r089_r2_a_pull_request_s_own_start_is_no_known_start_for_the_days(tmp_path):
    """R-089 (round 2, Review A B1, behaviour): a PR-<n> with no launcher row, guard round or pass line starts at its
    commit's time for the Started column only; the Mean days column reads only a start drawn from a record, so a records
    pull request merged beside an increment leaves that increment's days as they were."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    p.brief("TASK-701")
    p.commit("records: the brief", at(6))
    p.builder("TASK-701", 1, at(3, day=2, hour=9))
    p.commit("TASK-701: the thing (#71)", at(1, day=2, hour=12))
    p.commit("docs: records of the week (#72)", at(1, day=2, hour=13))
    out = p.report(tmp_path)
    row = table(out)[label(1)]
    assert row[1:3] == ["1", "2"], "started (PR-72) and merged (TASK-701, PR-72): %r" % (row,)
    assert row[4] == "14", "mean days to merge is TASK-701's alone: %r\n%s" % (row, out)


def test_r089_r2_a_stage_review_or_a_design_critique_is_no_counted_name(tmp_path):
    """R-089 (round 2, Review A B2, behaviour): a name beginning STAGE- or DESIGN-, a stage review or a design critique
    that merges nothing of its own, is no counted name from any source (guard record or pass line): it starts nothing
    and its rounds enter no cause line; its passes still count in the passes lines."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    p.guard("STAGE-P2", [(1, at(2, day=1, hour=8), None), (2, at(2, day=1, hour=13), "defect")])
    p.pass_line(at(2, day=1, hour=9), "PASS STAGE-P2 r1 security-auditor")
    p.pass_line(at(2, day=1, hour=10), "PASS STAGE-P2 r2 security-auditor records")
    p.pass_line(at(2, day=1, hour=11), "PASS DESIGN-program r1 plan-critic")
    p.pass_line(at(2, day=1, hour=12), "PASS DESIGN-program r2 plan-critic scope")
    out = p.report(tmp_path)
    assert table(out)[label(2)][1] == "0", out
    assert total_row(out)[1] == "0", out
    for line in cause_lines(out):
        assert not cause_counts(line), "a stage review's rounds are no increment's: %s" % line
    line = passes_line(out, 2)
    assert kind_count(line, "security-auditor") == 2, out
    assert kind_count(line, "review-b") == 2, out


def test_r089_r2_with_handoff_untracked_a_pull_request_is_counted_too(tmp_path):
    """R-089 (round 2, Review A should-fix 1, the supervisor's ruling): the rule for PR-<n> holds whether handoff/ is
    tracked or not, so with handoff/ untracked a squash naming no ID is merged as its pull request."""
    p = MiniProject(tmp_path)
    p.commit("docs: fix the pointers (#5)", at(2, day=2))
    out = p.report(tmp_path)
    assert table(out)[label(2)][2] == "1", out


def test_r089_r2_the_iss013_subject_is_its_pull_request_not_the_increment_it_mentions(tmp_path):
    """R-089 (round 2, Review A should-fix 3): the ISS-013 subject mentions TASK-031, which has a brief, inside its
    parenthesis; the reader names no ID there, so the commit is PR-61: started at its commit (its own start, no known
    start for the days) and merged; TASK-031 starts nothing."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    p.brief("TASK-031")
    p.commit("records: the brief", at(6))
    p.commit("docs: fixes (pointers, TASK-031's Scope, survival lists, records) (#61)", at(2, day=2))
    out = p.report(tmp_path)
    row = table(out)[label(2)]
    assert row[1:3] == ["1", "1"], out
    assert row[4] == "", "PR-61's own start is no known start for the days: %r" % (row,)


def test_r089_r2_a_stamp_of_other_digits_is_no_pass_line(tmp_path):
    """R-089 (round 2, the security review's advisory): a pass line's stamp is the ASCII form in-flight.py writes; a
    stamp written in other digits (here the full-width ones) is no pass line."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    good = minute(at(2, day=1, hour=9))
    wide = "".join(chr(0xFF10 + int(c)) if c in "0123456789" else c for c in good)
    log = p.ws / "run" / "supervisor"
    log.mkdir(parents=True, exist_ok=True)
    (log / "in-flight.md").write_text(wide + " PASS TASK-001 r2 review-a\n" + good + " PASS TASK-001 r1 review-b\n",
                                      encoding="utf-8")
    out = p.report(tmp_path)
    line = passes_line(out, 2)
    assert kind_count(line, "review-b") == 1, out
    assert kind_count(line, "review-a") == 0, out


def test_r089_r2_a_long_scope_line_never_stalls_the_snapshot(tmp_path):
    """R-089 (round 2, the security review's advisory): the guard reads the round's SCOPE file within a bound and
    matches the cause line in linear time, so a line of 200,000 spaces between two words neither stalls the snapshot
    nor stops it; the cause, a word outside the list, is unstated."""
    import time
    env = guard_env(tmp_path)
    repo = guard_repo(tmp_path, "long")
    rc, out = snapshot(repo, env, "TASK-001")
    assert rc == 0, out
    write_scope(repo, "Round cause: a" + " " * 200000 + "b" + chr(10), "a long cause line")
    began = time.monotonic()
    rc, out = snapshot(repo, env, "TASK-001-r2")
    took = time.monotonic() - began
    assert rc == 0, out
    assert took < 20, "the snapshot took %.1f s" % took
    assert round_entry(repo, 2).get("cause") == "unstated"


# ---------------------------------------------------------------- Round 3 (TASK-069-r3): Review B round 1's two
# behaviour findings.


def test_r089_r3_a_pull_request_is_merged_by_its_closing_number_alone(tmp_path):
    """R-089 (round 3, Review B finding 1, behaviour): PR-<n> is merged by a squash closing `(#<n>)` alone. A PR-<n>
    the subject reader finds in a subject is no name that subject names: `PR-2: follow-up (#1)` merges PR-1, which
    starts at its commit, and leaves PR-2, counted from its pass line, started and not merged."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    p.pass_line(at(2, day=1, hour=9), "PASS PR-2 r1 review-b")
    p.commit("PR-2: follow-up (#1)", at(2, day=2, hour=12))
    out = p.report(tmp_path)
    row = table(out)[label(2)]
    assert row[1:3] == ["2", "1"], "started (PR-2, PR-1) and merged (PR-1 alone): %r\n%s" % (row, out)


def test_r089_r3_a_pass_line_naming_a_word_outside_the_causes_is_unstated(tmp_path):
    """R-089 (round 3, Review B finding 2, behaviour): a pass line whose cause is a word outside the round causes'
    list is still a pass and still a record of its round, its cause read as `unstated`, never dropped."""
    p = MiniProject(tmp_path)
    tracked_old_brief(p)
    p.brief("TASK-801")
    p.commit("records: the brief", at(6))
    p.builder("TASK-801", 1, at(2, day=0, hour=9))
    p.pass_line(at(2, day=1, hour=9), "PASS TASK-801 r2 review-a weather")
    out = p.report(tmp_path)
    lines = cause_lines(out)
    assert len(lines) == 1, out
    assert lines[0].startswith("Round causes (1 rounds after the first): "), lines[0]
    assert cause_counts(lines[0]) == {"unstated": 1}, lines[0]
    assert kind_count(passes_line(out, 2), "review-a") == 1, out
