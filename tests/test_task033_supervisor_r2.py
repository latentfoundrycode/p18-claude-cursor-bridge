"""Supervisor's acceptance tests for TASK-033 round 2 (R-044); written by the supervisor from round 1's Review A and
security audit; the builder reads and runs them, never edits them.

R-044: the report cycle has a pace section for every project, computed by `pace-report.py`, read-only, from git and
the launcher's and the guard's own records; the pace report and the plan check read a squash subject by one rule, one
copy in `bridge_env.py`, under which a closing parenthesis merges an increment only when each of its comma-separated
items is a bare ID (ISS-013). The briefs are handoff/TASK-033.md and handoff/TASK-033-r2.md; the plan clauses are
docs/BUILD_PLAN.md TASK-033 (a) to (c). Each test names the round-1 finding it closes and the paragraph it enforces.

The fixtures, the reading of the Markdown output and the in-process helpers are tests/test_task033_supervisor.py's,
imported from it unchanged.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
import types

import pytest

from test_task033_supervisor import (CB, GRAMMAR_PATTERN, PLAN_PATTERN, TIMEOUT, UNTRACKED, GitWatch, Project, Report,
                                     Run, assistant, at, git, pace, readings, run_main, section, subject_repo,
                                     transcript_ts, usage, write_lines)


# ---------------------------------------------------------------- the reader (Review A B1, audit A9)


@pytest.mark.parametrize("subject", [
    "docs: x (TASK-031, Scope) (#5)",
    "docs: x (B3, TASK-031)",
    "docs: x (Scope)",
    "docs: x (TASK-031, Plan, records) (#7)",
])
def test_task033r2_grammar_parenthesis_with_a_capitalised_word_merges_nothing(tmp_path, program, monkeypatch,
                                                                              subject):
    """R-044. Under the grammar's pattern too, a closing parenthesis merges only when every item is a bare ID: an ID
    token holding a hyphen and a digit, as the subject form's own test reads one; a capitalised word (`Scope`, `B3`,
    `Plan`) is no bare ID, so the parenthesis merges nothing under either pattern (Review A r1 B1).
    enforces: docs/BUILD_PLAN.md TASK-033 (a) ("only when every comma-separated item inside the parenthesis is a bare
    increment or requirement ID"); handoff/TASK-033.md Requirement 1 ("Under either pattern")."""
    pc, plan, grammar = readings(tmp_path, program, monkeypatch, subject)
    assert pc == set() and plan == set(), (pc, plan)
    assert grammar == set(), grammar


@pytest.mark.parametrize("subject,expected", [
    ("docs: x (TASK-100, R-027) (#5)", "TASK-100"),
    ("docs: x (BUG-018)", "BUG-018"),
    ("docs: x ( TASK-100 ,  BUG-018 ) (#9)", "TASK-100"),
])
def test_task033r2_grammar_parenthesis_of_bare_ids_still_merges(tmp_path, program, monkeypatch, subject, expected):
    """R-044. The narrowing keeps a parenthesis of bare IDs merging under the grammar's pattern (spaces around each
    item allowed). enforces: docs/BUILD_PLAN.md TASK-033 (a) ("`(TASK-100, R-027)` merges TASK-100"); handoff/
    TASK-033-r2.md Requirement 1."""
    _, _, grammar = readings(tmp_path, program, monkeypatch, subject)
    assert expected in grammar, grammar


def test_task033r2_a_long_whitespace_run_is_read_in_linear_time(tmp_path, program):
    """R-044. A subject holding a parenthesis followed by a long run of spaces is read in time linear in its length,
    under both patterns (the security audit's r1 A9: two adjacent `\\s*` after the parenthesis made it quadratic).
    enforces: handoff/TASK-033.md Security context (commit subjects are untrusted text); handoff/TASK-033-r2.md
    Requirement 1."""
    subject = "x (a)" + " " * 80000 + "z"
    repo = tmp_path / "subject-repo"                           # the message from a file: a command line this long
    repo.mkdir()                                               # is refused on Windows
    git(repo, "init", "-q", "-b", "main")
    msg = tmp_path / "message.txt"
    msg.write_bytes(subject.encode("ascii") + b"\n")
    git(repo, "commit", "-q", "--allow-empty", "--no-verify", "--cleanup=verbatim", "-F", str(msg))
    assert len(git(repo, "log", "-1", "--format=%s")) > 80000
    be = program("bridge_env")
    for pattern in (PLAN_PATTERN, GRAMMAR_PATTERN):
        t0 = time.monotonic()
        got = be.squash_merged_ids(str(repo), pattern)
        elapsed = time.monotonic() - t0
        assert got == set(), got
        assert elapsed < 3.0, "%s: %.2f s" % (pattern, elapsed)


def test_task033r2_plan_check_gives_its_git_command_a_limit(tmp_path, program, monkeypatch):
    """R-044. plan-check.py's git command is given a limit (the security audit's r1 A7).
    enforces: handoff/TASK-033.md Constraints ("Give every subprocess a timeout"); handoff/TASK-033-r2.md
    Requirement 1."""
    repo = subject_repo(tmp_path, "TASK-100: x (#1)")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.chdir(str(repo))
    watch = GitWatch(monkeypatch)
    assert program("plan-check").merged_ids("main") == {"TASK-100"}
    assert watch.calls, "no git command was seen"
    assert all(t is not None for _, t in watch.calls), watch.calls


# ---------------------------------------------------------------- the merged column (Review A S2, audit A2; S4)


def test_task033r2_two_merges_trailer_lines_both_count(tmp_path):
    """R-044. A squash carrying two `Merges:` trailer lines merges both IDs in pace-report.py, as the one reader does
    (Review A r1 S2, the security audit's r1 A2: the program's own split dropped the second line).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("whose subject merges the ID under the plan check's four forms");
    handoff/TASK-033-r2.md Requirement 2."""
    p = Project(tmp_path / "proj-trailers-q7")
    p.brief("TASK-601", "TASK-602")
    p.commit("records: briefs", at(10, 0))
    p.commit("docs: two units (#3)", at(2, 2), body="Merges: TASK-601\nMerges: TASK-602")
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "merged") == 2, rep.text


def test_task033r2_a_separator_character_in_a_subject_merges_nothing(tmp_path):
    """R-044. A subject holding the unit separator before an ID is one subject, read whole by the one reader, which
    merges nothing from it (the security audit's r1 A2: `docs: x<US>TASK-050` merged TASK-050).
    enforces: handoff/TASK-033.md Security context (commit subjects are untrusted text); handoff/TASK-033-r2.md
    Requirement 2."""
    p = Project(tmp_path / "proj-sep-q7")
    p.brief("TASK-650")
    p.commit("records: brief", at(10, 0))
    p.commit("docs: x\x1fTASK-650 (#4)", at(2, 2))
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "merged") in (None, 0), rep.text


def test_task033r2_an_increment_merged_twice_counts_in_its_first_merge_week(tmp_path):
    """R-044. An ID that two commits merge counts once, in the week of the earlier commit (Review A r1 C4).
    enforces: handoff/TASK-033-r2.md Requirement 9 ("an increment's merge week is its first merging commit's")."""
    p = Project(tmp_path / "proj-twice-q7")
    p.brief("TASK-660")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-660: first (#1)", at(4, 2))
    p.commit("docs: again (#2)", at(1, 2), body="Merges: TASK-660")
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(4, "merged") == 1, rep.text
    assert rep.at_week(1, "merged") in (None, 0), rep.text


# ---------------------------------------------------------------- handoff/ tracked or not (Review A B6, S4)


def test_task033r2_one_new_brief_beside_a_tracked_handoff_is_no_untracked_handoff(tmp_path):
    """R-044. handoff/ is untracked only when `git ls-files handoff/` lists nothing: a tracked handoff/ beside one new
    brief not yet committed (the supervisor writes a brief before its checkpoint commit) prints its columns, never
    `n/a (handoff/ untracked)`; and the untracked brief is not "a tracked brief", so its ID is not counted merged
    (Review A r1 B6 and S4). enforces: handoff/TASK-033.md Requirement 5 ("Tracked handoff/ ... read with git
    ls-files"), Context ("An ID that has a brief means a tracked handoff/<ID>.md"); handoff/TASK-033-r2.md
    Requirement 3."""
    p = Project(tmp_path / "proj-onenew-q7")
    p.brief("TASK-701")
    p.commit("records: brief", at(10, 0))
    p.launch("TASK-701", at(3, 0))
    p.commit("TASK-701: x (#1)", at(2, 2))
    p.commit("TASK-703: not briefed in git (#3)", at(2, 3))
    p.brief("TASK-702", "TASK-703")                      # written after the last commit: untracked
    assert "TASK-701" in git(p.ws, "ls-files", "handoff/")
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    assert UNTRACKED not in r.out, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(3, "started") == 1, rep.text
    assert rep.at_week(2, "merged") == 1, rep.text


def test_task033r2_untracked_handoff_counts_every_id_the_reader_finds(tmp_path):
    """R-044. With handoff/ untracked, the merged column counts every ID the reader finds in the week's subjects, with
    or without a brief file, and the total row's started and rounds cells print `n/a (handoff/ untracked)` like the
    week rows (Review A r1 S4 and C4). enforces: handoff/TASK-033.md Requirement 9 ("An untracked handoff/");
    docs/BUILD_PLAN.md TASK-033 (b) ("prints n/a (handoff/ untracked) in the rounds and started columns")."""
    p = Project(tmp_path / "proj-untracked2-q7")
    p.write("docs/README.md", "fixture\n")
    p.commit("records: docs", at(10, 0))
    p.commit("TASK-801 BUG-802: two (#2)", at(2, 2))
    assert git(p.ws, "ls-files", "handoff/") == ""
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "merged") == 2, rep.text
    assert rep.total is not None, rep.text
    assert UNTRACKED in rep.cell(rep.total, "started"), rep.total
    assert UNTRACKED in rep.total[rep.index("rounds_mean")], rep.total


# ---------------------------------------------------------------- rounds and days (Review A C4)


def test_task033r2_a_merged_increment_with_no_reading_of_rounds_is_left_out_of_the_rounds(tmp_path):
    """R-044. An increment merged with no report, `.err` file or rounds record has no reading of its rounds: it is left
    out of the mean and maximum, so a week whose merged increments have none prints blank rounds cells, never `0`
    (Review A r1 C4). enforces: handoff/TASK-033-r2.md Requirement 9 ("no reading of rounds")."""
    p = Project(tmp_path / "proj-norounds-q7")
    p.brief("TASK-710")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-710: x (#1)", at(2, 2))
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "merged") == 1, rep.text
    assert rep.at_week(2, "rounds_mean") is None, rep.text
    assert rep.at_week(2, "rounds_max") is None, rep.text


def test_task033r2_a_start_after_the_merge_gives_no_negative_days(tmp_path):
    """R-044. An increment whose earliest record is later than its merge has no usable start for the days column: it is
    left out of the mean days, so no negative number is printed (Review A r1 C4).
    enforces: handoff/TASK-033-r2.md Requirement 9 ("a start later than the merge")."""
    p = Project(tmp_path / "proj-late-q7")
    p.brief("TASK-720")
    p.report("TASK-720-r1")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-720: x (#1)", at(3, 2))
    p.launch("TASK-720", at(2, 1))
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(3, "merged") == 1, rep.text
    assert rep.at_week(3, "days") is None, rep.text
    assert not re.search(r"(?<![\w-])-\d", "\n".join("|".join(row) for row in rep.weeks.values())), rep.text


# ---------------------------------------------------------------- git: missing ref, configuration (B3, A3, A4)


def test_task033r2_a_missing_main_is_no_timeout(tmp_path):
    """R-044. A Workspace with no `main` (and a file named `main` beside it) fails that project naming the git command
    as failed, never as timed out; the other project is still printed; exit 1 (Review A r1 B3, the security audit's
    r1 A4). enforces: handoff/TASK-033.md Requirement 1 ("can tell a timeout (naming the command) from a missing
    ref"); handoff/TASK-033-r2.md Requirement 4."""
    good = Project(tmp_path / "proj-good-q7")
    good.brief("TASK-730")
    good.commit("records: brief", at(10, 0))
    good.commit("TASK-730: x (#1)", at(2, 2))
    bad = Project(tmp_path / "proj-trunk-q7")
    bad.brief("TASK-731")
    bad.commit("records: brief", at(10, 0))
    git(bad.ws, "branch", "-m", "main", "trunk")
    bad.write("main", "a file named main\n")
    r = pace([good.root, bad.root], cwd=tmp_path)
    assert r.rc == 1, r
    assert "Traceback" not in r.both
    rep = Report(section(r.out, good.name, others=(bad.name,)))
    assert rep.at_week(2, "merged") == 1, rep.text
    lines = [line for line in r.both.splitlines() if bad.name in line or "main" in line]
    assert any("main" in line for line in lines), r
    assert not re.search(r"timed?[ -]?out|\b120[ -]?s(?:ec(?:ond)?s?)?\b|\blimit\b", r.both, re.I), r


def test_task033r2_a_projects_git_configuration_runs_no_program(tmp_path):
    """R-044. A project's own `.git/config` cannot make pace-report.py run a program: `core.fsmonitor` set to a script
    that writes a marker runs under a plain `git status` there (the fixture proves the mechanism), and never under a
    pace-report.py run (the security audit's r1 A3). enforces: handoff/TASK-033.md Security context (the records under
    .git/ are untrusted; the program writes nothing); handoff/TASK-033-r2.md Requirement 4."""
    p = Project(tmp_path / "proj-fsmon-q7")
    p.brief("TASK-740")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-740: x (#1)", at(2, 2))
    marker = tmp_path / "fsmonitor-ran.txt"
    script = tmp_path / "fsmon.py"
    script.write_text("import sys\nopen(%r, 'a').write('ran\\n')\nsys.stdout.write('')\n" % str(marker),
                      encoding="utf-8")
    command = '"%s" "%s"' % (sys.executable.replace("\\", "/"), str(script).replace("\\", "/"))
    git(p.ws, "config", "core.fsmonitor", command)
    subprocess.run(["git", "-C", str(p.ws), "status", "--porcelain"], capture_output=True, timeout=TIMEOUT,
                   env=dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull))
    if not marker.exists():
        pytest.skip("this git does not run core.fsmonitor from a repository's configuration")
    marker.unlink()
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    assert not marker.exists(), "pace-report.py ran the project's core.fsmonitor program"


# ---------------------------------------------------------------- default roots (Review A B2, audit A5)


PROJECTS_RX = re.compile(r"^PROJECTS = \{.*?^\}", re.S | re.M)


def sandbox_bridge(base, projects):
    """A copy of pace-report.py, bridge_env.py and evaluate-reports.py in <base>/cb, the copy's PROJECTS replaced."""
    cb = base / "cb"
    cb.mkdir(parents=True)
    for name in ("pace-report.py", "bridge_env.py", "evaluate-reports.py"):
        shutil.copyfile(os.path.join(CB, name), str(cb / name))
    src = (cb / "evaluate-reports.py").read_text(encoding="utf-8")
    body = "PROJECTS = {\n%s}" % "".join("    %r: %r,\n" % (k, str(v)) for k, v in projects.items())
    new, n = PROJECTS_RX.subn(lambda m: body, src, count=1)
    assert n == 1, "evaluate-reports.py's PROJECTS literal was not found"
    (cb / "evaluate-reports.py").write_text(new, encoding="utf-8")
    return cb


def run_copy(cb, args, cwd, bytecode=False):
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0")
    if bytecode:
        env.pop("PYTHONDONTWRITEBYTECODE", None)
    else:
        env["PYTHONDONTWRITEBYTECODE"] = "1"
    p = subprocess.run([sys.executable, str(cb / "pace-report.py")] + [str(a) for a in args], cwd=str(cwd), env=env,
                       capture_output=True, timeout=TIMEOUT)
    return Run(p.returncode, p.stdout, p.stderr)


def test_task033r2_a_default_root_missing_or_no_project_is_a_named_line(tmp_path):
    """R-044. With no root given, a root of the project list that does not exist on this computer, or exists and is no
    project, is a named line in its section and never exit 2; the projects that exist are printed; run from a folder
    outside the bridge's tree, the bridge root found there (the current folder, no project) is a named line too, and
    the run exits 0 (Review A r1 B2, the security audit's r1 A5). enforces: handoff/TASK-033.md Requirement 5
    ("A root from PROJECTS that does not exist on this computer is a named line in its section, not exit 2");
    docs/BUILD_PLAN.md TASK-033 (b) ("with none given, the roots evaluate-reports.py's project list names");
    handoff/TASK-033-r2.md Requirement 5."""
    here = Project(tmp_path / "proj-here-q7")
    here.brief("TASK-750")
    here.commit("records: brief", at(10, 0))
    here.commit("TASK-750: x (#1)", at(2, 2))
    bridge = Project(tmp_path / "proj-bridge-q7")
    bridge.commit("records: start", at(10, 0))
    bare = tmp_path / "proj-bare-q7"
    bare.mkdir()
    cb = sandbox_bridge(tmp_path / "sandbox", {"proj-here-q7": here.root, "proj-gone-q7": tmp_path / "proj-gone-q7",
                                              "proj-bare-q7": bare, "Bridge": bridge.root})
    elsewhere = tmp_path / "elsewhere-q7"
    elsewhere.mkdir()
    r = run_copy(cb, [], cwd=elsewhere)
    assert r.rc == 0, r
    assert "Traceback" not in r.both
    rep = Report(section(r.out, "proj-here-q7", others=("proj-gone-q7", "proj-bare-q7", "Bridge", "elsewhere-q7")))
    assert rep.at_week(2, "merged") == 1, rep.text
    assert any("proj-gone-q7" in line and re.search(r"not present", line, re.I) for line in r.out.splitlines()) or (
        "proj-gone-q7" in r.out and re.search(r"not present", "\n".join(section(r.out, "proj-gone-q7")), re.I)), r
    assert "proj-bare-q7" in r.out, r
    assert "elsewhere-q7" in r.out, r


# ---------------------------------------------------------------- transcripts (audit B1, Review A B4, S3, B5, S5, C5)


def bad_lines(ts):
    """Transcript lines that are no usable assistant record, each to be skipped."""
    big = {"input_tokens": 400000, "output_tokens": 300000, "cache_creation_input_tokens": 200000,
           "cache_read_input_tokens": 100000}
    rec = lambda mid, u, t=ts: json.dumps({"type": "assistant", "timestamp": t,
                                            "message": {"id": mid, "role": "assistant", "usage": u}})
    return [
        "[1, 2]",
        '"just a string"',
        "42",
        "null",
        json.dumps({"type": "assistant", "timestamp": ts, "message": "hi"}),
        json.dumps({"type": "assistant", "timestamp": ts, "message": {"id": "m_list", "usage": [1]}}),
        json.dumps({"type": "assistant", "timestamp": ts, "message": {"id": {"a": 1}, "usage": big}}),
        json.dumps({"type": "assistant", "timestamp": ts, "message": {"id": ["x"], "usage": big}}),
        '{"type": "assistant", "timestamp": "%s", "message": {"id": "m_inf", "usage": {"input_tokens": Infinity, '
        '"output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}}' % ts,
        '{"type": "assistant", "timestamp": "%s", "message": {"id": "m_nan", "usage": {"input_tokens": NaN, '
        '"output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}}' % ts,
        rec("m_neg", dict(big, input_tokens=-400000)),
        rec("m_uni", dict(big, input_tokens="١٢")),
        rec("m_str", dict(big, input_tokens="400000")),
        rec("m_float", dict(big, input_tokens=400000.0)),
        rec("m_bool", dict(big, input_tokens=True)),
        rec("m_huge", dict(big, input_tokens=10 ** 400)),
        rec("m_ts", big, t=12345),
        rec("m_badts", big, t="not a time"),
        json.dumps({"type": "assistant", "timestamp": ts, "message": {"id": "m_nousage"}}),
        json.dumps({"type": "assistant", "timestamp": ts, "message": {"id": "m_usage_str", "usage": "lots"}}),
    ]


def transcript_project(base, home, program, name, lines):
    """A project merging TASK-760 at k2, its root key's one session file holding `lines`; returns the project."""
    p = Project(base / name)
    p.brief("TASK-760")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-760: x (#1)", at(2, 2))
    er = program("evaluate-reports")
    keys = er.project_keys(p.name, str(p.root))
    write_lines(home / ".claude" / "projects" / keys[0] / "s1.jsonl", lines)
    return p, keys


def test_task033r2_malformed_transcript_lines_are_skipped(tmp_path, program):
    """R-044. A transcript line that is no object, whose message or usage is no object, whose message id is no string,
    or whose usage field is not a non-negative integer (a float, a string of digits, a bool, a negative, Infinity,
    NaN, a number past any count) is skipped whole, never a traceback and never a partial sum; a record whose
    timestamp is no ISO time is skipped; only the good record (1.00 million) is counted (the security audit's r1 B1,
    Review A r1 B4 and S3: converged). enforces: handoff/TASK-033.md Security context ("A malformed line or record is
    skipped, never a traceback"; "A number in them is read with int after a regex has matched its ASCII digits");
    handoff/TASK-033-r2.md Requirement 6."""
    home = tmp_path / "fixture-home"
    ts = transcript_ts(at(2, 1))
    good = assistant("m_good", at(2, 1, hour=9), usage(100000, 200000, 300000, 400000))
    p, _ = transcript_project(tmp_path, home, program, "proj-badlines-q7", [good] + bad_lines(ts))
    r = pace([p.root, "--tokens", "--home", home], cwd=tmp_path)
    assert r.rc == 0, r
    assert "Traceback" not in r.both
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "tokens") == 1.0, rep.text


def test_task033r2_a_timestamp_with_an_offset_is_read_in_utc(tmp_path, program):
    """R-044. A transcript record's week is its timestamp's UTC week: Monday 03:00 at +05:00 is Sunday 22:00 UTC, the
    week before (Review A r1 C5). enforces: handoff/TASK-033.md Context ("Weeks are UTC ISO weeks ... for every source
    alike"; Numbers: times parsed with datetime, never by slicing); handoff/TASK-033-r2.md Requirement 6."""
    home = tmp_path / "fixture-home"
    monday = at(1, 0, hour=3)                                  # Monday 03:00 of week k1
    stamp = monday.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=5))).isoformat()
    assert stamp.endswith("+05:00"), stamp                     # Monday 03:00+05:00 = Sunday 22:00 UTC, week k2
    line = json.dumps({"type": "assistant", "timestamp": stamp,
                       "message": {"id": "m_off", "role": "assistant", "usage": usage(250000, 250000, 250000, 250000)}})
    p, _ = transcript_project(tmp_path, home, program, "proj-offset-q7", [line])
    r = pace([p.root, "--tokens", "--home", home], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "tokens") == 1.0, rep.text
    assert rep.at_week(1, "tokens") is None, rep.text


TOKEN_SOURCES_RX = re.compile(r"(\d+)\s+session files?\b.*?(\d+)\s+subagent files?\b", re.I)


def test_task033r2_the_header_says_which_session_sources_were_found(tmp_path, program):
    """R-044. With `--tokens`, the section says which session sources were found, as counts of session files and of
    subagent files, and never prints a session folder's key (a key is a path of this computer) (Review A r1 B5).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("where present (the header says which were found)"); handoff/
    TASK-033-r2.md Requirement 7."""
    home = tmp_path / "fixture-home"
    rec = assistant("m_one", at(2, 1), usage(100000, 200000, 300000, 400000))
    p, keys = transcript_project(tmp_path, home, program, "proj-sources-q7", [rec])
    write_lines(home / ".claude" / "projects" / keys[0] / "s2.jsonl",
                [assistant("m_two", at(3, 1), usage(1, 1, 1, 1))])
    write_lines(home / ".claude" / "projects" / keys[0] / "sub-x" / "subagents" / "agent-1.jsonl",
                [assistant("m_sub", at(3, 2), usage(1, 1, 1, 1))])
    r = pace([p.root, "--tokens", "--home", home], cwd=tmp_path)
    assert r.rc == 0, r
    text = "\n".join(section(r.out, p.name))
    m = TOKEN_SOURCES_RX.search(text)
    assert m, text
    assert (int(m.group(1)), int(m.group(2))) == (2, 1), m.group(0)
    for key in keys:
        assert key not in r.both, key


def junction_or_link(link, target):
    """A directory link at `link` to `target`: a junction on Windows, a symlink elsewhere; None if neither can be
    made."""
    try:
        if sys.platform == "win32":
            import _winapi
            _winapi.CreateJunction(str(target), str(link))
        else:
            os.symlink(str(target), str(link), target_is_directory=True)
    except (OSError, AttributeError, NotImplementedError):
        return None
    return link


def test_task033r2_the_session_walk_follows_no_link(tmp_path, program):
    """R-044. The walk of a session folder never follows a directory link (a junction or a symlink): a link inside
    the key folder to a folder holding `subagents/*.jsonl` adds nothing (the security audit's r1 A1).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) (`<key>/**/subagents/*.jsonl` of the root's and the Workspace's keys);
    handoff/TASK-033-r2.md Requirement 8."""
    home = tmp_path / "fixture-home"
    rec = assistant("m_one", at(2, 1), usage(100000, 200000, 300000, 400000))
    p, keys = transcript_project(tmp_path, home, program, "proj-link-q7", [rec])
    outside = tmp_path / "outside-q7"
    write_lines(outside / "deep" / "subagents" / "agent-9.jsonl",
                [assistant("m_out", at(2, 2), usage(1000000, 1000000, 1000000, 1000000))])
    if junction_or_link(home / ".claude" / "projects" / keys[0] / "linked", outside) is None:
        pytest.skip("no directory link can be made here")
    r = pace([p.root, "--tokens", "--home", home], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "tokens") == 1.0, rep.text


def lowered_limits(mod, monkeypatch, value):
    """Every module-level 120-second number of pace-report.py and the bridge modules it loaded set to `value` (the
    brief's "monkeypatched limit"); returns the names."""
    modules = [mod] + [v for v in vars(mod).values() if isinstance(v, types.ModuleType)
                       and os.path.dirname(os.path.abspath(getattr(v, "__file__", "") or "")) == os.path.abspath(CB)]
    lowered = []
    for m in modules:
        for name, v in list(vars(m).items()):
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)) and v == 120:
                monkeypatch.setattr(m, name, value)
                lowered.append(name)
            elif isinstance(v, datetime.timedelta) and v == datetime.timedelta(seconds=120):
                monkeypatch.setattr(m, name, datetime.timedelta(seconds=value))
                lowered.append(name)
    return lowered


def test_task033r2_a_timed_out_session_read_keeps_exit_0(tmp_path, program, monkeypatch, capsys):
    """R-044. A timed-out session read gives an empty tokens cell and a line naming the project and the limit, and does
    not by itself make the exit 1 (Review A r1 C1: round 1's test allowed either exit).
    enforces: handoff/TASK-033.md Requirement 9 ("A timed-out session-folder read ... is not a failed project and does
    not by itself make the exit 1")."""
    home = tmp_path / "fixture-home"
    rec = assistant("m_one", at(2, 1), usage(100000, 200000, 300000, 400000))
    p, _ = transcript_project(tmp_path, home, program, "proj-tokto-q7", [rec])
    mod = program("pace-report")
    if not lowered_limits(mod, monkeypatch, -1):
        pytest.skip("pace-report.py holds no module-level 120-second limit to lower")
    GitWatch(monkeypatch, unlimited_git=True)
    r = run_main(mod, monkeypatch, capsys, [p.root, "--tokens", "--home", home])
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    for row in rep.weeks.values():
        assert rep.cell(row, "tokens") == "", row
    assert any(p.name in line and re.search(r"time|limit|120", line, re.I) for line in r.both.splitlines()), r


def test_task033r2_the_session_walk_is_inside_the_limit(tmp_path, program, monkeypatch, capsys):
    """R-044. The session read's limit covers the walk of the folders, not only the reading of the files found: with
    every directory listing slowed to 0.3 s and the limit at 1 s, a key folder of 30 sub-folders ends at the limit
    (an empty tokens cell, the project named, exit 0) within a few seconds, where a walk outside the limit would take
    over nine (Review A r1 S5, the security audit's r1 A1: converged). enforces: docs/BUILD_PLAN.md TASK-033 (b) ("the
    read of the session folders is bounded like a git command (120 seconds per project)"); handoff/TASK-033-r2.md
    Requirement 8."""
    home = tmp_path / "fixture-home"
    rec = assistant("m_one", at(2, 1), usage(100000, 200000, 300000, 400000))
    p, keys = transcript_project(tmp_path, home, program, "proj-slowwalk-q7", [rec])
    key_dir = home / ".claude" / "projects" / keys[0]
    for i in range(30):
        (key_dir / ("d%02d" % i) / "e").mkdir(parents=True)
    mod = program("pace-report")
    if not lowered_limits(mod, monkeypatch, 1):
        pytest.skip("pace-report.py holds no module-level 120-second limit to lower")
    GitWatch(monkeypatch, unlimited_git=True)
    real_scandir = os.scandir
    real_listdir = os.listdir
    projects_dir = os.path.normcase(os.path.abspath(str(home / ".claude" / "projects")))

    def slow(fn):
        def wrapped(path=".", *a, **kw):
            if os.path.normcase(os.path.abspath(os.fspath(path))).startswith(projects_dir):
                time.sleep(0.3)
            return fn(path, *a, **kw)
        return wrapped

    monkeypatch.setattr(os, "scandir", slow(real_scandir))
    monkeypatch.setattr(os, "listdir", slow(real_listdir))
    t0 = time.monotonic()
    r = run_main(mod, monkeypatch, capsys, [p.root, "--tokens", "--home", home])
    elapsed = time.monotonic() - t0
    assert r.rc == 0, r
    assert elapsed < 6.0, "%.1f s\n%r" % (elapsed, r)
    rep = Report(section(r.out, p.name))
    for row in rep.weeks.values():
        assert rep.cell(row, "tokens") == "", row
    assert any(p.name in line and re.search(r"time|limit", line, re.I) for line in r.both.splitlines()), r


# ---------------------------------------------------------------- output and writes (audit A6, A8 / Review A C6)


def test_task033r2_non_ascii_names_are_printed_ascii(tmp_path):
    """R-044. A project folder's name and a rounds record's file name outside ASCII never put a non-ASCII byte on the
    output, and the run exits 0 (the security audit's r1 A6). enforces: handoff/TASK-033.md Requirement 5 ("It is
    ASCII only"); handoff/TASK-033-r2.md Requirement 9."""
    p = Project(tmp_path / "proj-café-q7")
    p.brief("TASK-770")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-770: x (#1)", at(2, 2))
    p.rounds("STAGE-Bé", [(at(3, 1), None, None), (at(3, 2), None, None), (at(3, 3), None, None),
                               (at(3, 4), None, None)])
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    assert all(b < 128 for b in r.raw_out), r.raw_out
    assert all(b < 128 for b in r.raw_err), r.raw_err


def test_task033r2_a_run_writes_no_bytecode(tmp_path):
    """R-044. A run of pace-report.py writes no `__pycache__` beside it, its imports of bridge_env.py and
    evaluate-reports.py included, even where the environment allows bytecode (the security audit's r1 A8, Review A
    r1 C6: converged). enforces: docs/BUILD_PLAN.md TASK-033 (b) ("the program writes nothing"); handoff/
    TASK-033-r2.md Requirement 9."""
    p = Project(tmp_path / "proj-pyc-q7")
    p.brief("TASK-780")
    p.commit("records: brief", at(10, 0))
    cb = sandbox_bridge(tmp_path / "sandbox", {"Bridge": p.root})
    r = run_copy(cb, [p.root], cwd=tmp_path, bytecode=True)
    assert r.rc == 0, r
    assert not (cb / "__pycache__").exists(), os.listdir(str(cb / "__pycache__"))
