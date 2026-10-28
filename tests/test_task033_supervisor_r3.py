"""Supervisor's acceptance tests for TASK-033 round 3 (R-044); written by the supervisor from round 2's Review A and
security audit; the builder reads and runs them, never edits them.

R-044: the report cycle has a pace section for every project, computed by `pace-report.py`, read-only, from git and
the launcher's and the guard's own records; the pace report and the plan check read a squash subject by one rule, one
copy in `bridge_env.py`, under which a closing parenthesis merges an increment only when each of its comma-separated
items is a bare ID (ISS-013). The briefs are handoff/TASK-033.md, handoff/TASK-033-r2.md and handoff/TASK-033-r3.md.
Each test names the round-2 finding it closes and the paragraph it enforces.

The fixtures and helpers are tests/test_task033_supervisor.py's and tests/test_task033_supervisor_r2.py's, imported
unchanged.
"""
import json
import os
import re
import subprocess
import sys

import pytest

from test_task033_supervisor import (GRAMMAR_PATTERN, PACE, PLAN_PATTERN, TIMEOUT, Project, Report, Run, assistant, at,
                                     git, gitdate, pace, run_main, section, usage, write_lines)
from test_task033_supervisor_r2 import transcript_project

# round 1's trailing-parenthesis form (bridge_env.py at 80c2a8b, :520), copied here only to state "the accepted forms
# stay exactly the same" (handoff/TASK-033-r2.md Requirement 1): its last match on a subject, its inner text.
R1_TRAIL = re.compile(r"\(([^()]*)\)\s*(?:[-\u2014\u2013]\s*v?[\w.]+\s*)?(?:\(#\d+\))?\s*$")
R_ITEM = re.compile(r"R-\d{3,}[a-z]?")


def expected_from_parenthesis(subject, pattern):
    """What a subject that starts with no ID, holds no Merge line and no trailer merges: the IDs of the parenthesis
    round 1's form finds, when every item is a bare ID (the pattern fully matched, a hyphen and a digit; R-nnn a bare
    item merging nothing under the plan pattern)."""
    m = R1_TRAIL.search(subject)
    if not m:
        return set()
    items = [i.strip() for i in m.group(1).split(",")]
    rx = re.compile(pattern)
    if not items or not all(items):
        return set()
    out = set()
    for item in items:
        bare = rx.fullmatch(item) and "-" in item and any(c.isdigit() for c in item)
        if R_ITEM.fullmatch(item):
            if pattern != PLAN_PATTERN and bare:
                out.add(item)
            continue
        if not bare:
            return set()
        out.add(item)
    return out


def verbatim_repo(tmp_path, subject):
    """A repository whose main holds one commit with exactly `subject` (from a file, cleanup verbatim); returns the
    repository and the subject as git prints it."""
    repo = tmp_path / "verbatim-repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    msg = tmp_path / "message.txt"
    msg.write_bytes(subject.encode("utf-8") + b"\n")
    git(repo, "commit", "-q", "--allow-empty", "--no-verify", "--cleanup=verbatim", "-F", str(msg))
    return repo


TRAIL_SHAPES = [
    "docs: x (TASK-050) - not done",
    "docs: x (TASK-050) - fix things",
    "docs: x (TASK-050) -v2 extra",
    "docs: x (TASK-050) \u2014 v2 wip (#7)",
    "docs: x (TASK-050) - v2 - v3",
    "docs: x (TASK-050) (#7) trailing",
    "docs: x (TASK-050) - . (#1)",
    "docs: x (TASK-050) - v1.2",
    "docs: x (TASK-050) \u2013 v1.2 (#7)",
    "docs: x (TASK-050)-v2",
    "docs: x (TASK-050) (#7)",
    "docs: x (TASK-050)   ",
    "docs: x (TASK-050)\u00a0",
    "docs: x (TASK-050) -\u00a0v2",
    "docs: x (TASK-050)\u00a0(#7)",
    "docs: x (TASK-050) (TASK-051)",
    "docs: x (TASK-050, TASK-051) (#9)",
    "docs: x (TASK-050",
    "docs: x TASK-050)",
]


@pytest.mark.parametrize("subject", TRAIL_SHAPES)
@pytest.mark.parametrize("pattern", [PLAN_PATTERN, GRAMMAR_PATTERN], ids=["plan", "grammar"])
def test_task033r3_the_trailing_parenthesis_accepts_exactly_round_1s_shapes(tmp_path, program, subject, pattern):
    """R-044. The linear trailing-parenthesis reader finds the parenthesis round 1's form found, on every shape: words
    after the parenthesis or after a version (`- not done`, `-v2 extra`, `- v2 wip (#7)`) leave the subject unmerged,
    and Unicode spaces (a no-break space) count as spaces, as `\\s` did (the security audit's r2 B2: a free word after
    the parenthesis merged the ID, lapsing a branch's claim). enforces: handoff/TASK-033-r2.md Requirement 1 ("the forms
    it accepts stay exactly the same"); docs/BUILD_PLAN.md TASK-033 (a); handoff/TASK-033-r3.md Requirement 1."""
    repo = verbatim_repo(tmp_path, subject)
    shown = git(repo, "log", "-1", "--format=%s").rstrip("\n")
    got = program("bridge_env").squash_merged_ids(str(repo), pattern)
    assert got is not None
    assert set(got) == expected_from_parenthesis(shown, pattern), (shown, got)


@pytest.mark.parametrize("stamp", ["0001-01-01T00:00:00+05:00", "9999-12-31T23:59:59-05:00", "0001-01-01T00:00:00Z",
                                   "9999-12-31T23:59:59.999999+00:00"])
def test_task033r3_a_timestamp_at_the_edge_of_the_calendar_is_skipped(tmp_path, program, stamp):
    """R-044. A transcript timestamp that `fromisoformat` reads but whose conversion to UTC (or to its week) leaves the
    calendar is a malformed record: skipped, never a traceback, the good record still counted (the security audit's r2
    B1: OverflowError from astimezone lost every project). enforces: handoff/TASK-033.md Security context ("A malformed
    line or record is skipped, never a traceback"); handoff/TASK-033-r2.md Requirement 6 ("nothing raises");
    handoff/TASK-033-r3.md Requirement 2."""
    home = tmp_path / "fixture-home"
    good = assistant("m_good", at(2, 1), usage(100000, 200000, 300000, 400000))
    edge = json.dumps({"type": "assistant", "timestamp": stamp,
                       "message": {"id": "m_edge", "role": "assistant", "usage": usage(1, 1, 1, 1)}})
    p, _ = transcript_project(tmp_path, home, program, "proj-edge-q7", [edge, good])
    r = pace([p.root, "--tokens", "--home", home], cwd=tmp_path)
    assert r.rc == 0, r
    assert "Traceback" not in r.both
    assert Report(section(r.out, p.name)).at_week(2, "tokens") == 1.0


def test_task033r3_a_line_over_the_cap_is_skipped(tmp_path, program, monkeypatch, capsys):
    """R-044. A transcript line longer than the line cap is skipped, its record not counted, and the next line read:
    with `LINE_CAP` lowered to 2,000 bytes, a valid 1.00-million record padded to 6,000 bytes is skipped and a 0.50-million
    record after it counted (the security audit's r2 A1: the cap was applied after reading the whole line).
    enforces: handoff/TASK-033-r2.md Requirement 8 ("Read lines with a cap of 64 MiB: a longer line is skipped to its
    end, unread"); handoff/TASK-033-r3.md Requirement 3."""
    home = tmp_path / "fixture-home"
    long_rec = json.loads(assistant("m_long", at(2, 1), usage(100000, 200000, 300000, 400000)))
    long_rec["message"]["content"] = [{"type": "text", "text": "x" * 6000}]
    short = assistant("m_short", at(2, 2), usage(100000, 100000, 100000, 200000))
    p, _ = transcript_project(tmp_path, home, program, "proj-cap-q7", [json.dumps(long_rec), short])
    mod = program("pace-report")
    assert isinstance(getattr(mod, "LINE_CAP", None), int), "pace-report.py has no module-level LINE_CAP"
    assert mod.LINE_CAP == 64 * 1024 * 1024
    monkeypatch.setattr(mod, "LINE_CAP", 2000)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    r = run_main(mod, monkeypatch, capsys, [p.root, "--tokens", "--home", home])
    assert r.rc == 0, r
    assert Report(section(r.out, p.name)).at_week(2, "tokens") == 0.5, r


def test_task033r3_a_carriage_return_inside_a_subject_merges_nothing(tmp_path):
    """R-044. A subject holding a lone carriage return before an ID is one subject: pace-report.py merges nothing from
    it (the security audit's r2 A2: universal newlines split it into a second line beginning with the ID).
    enforces: handoff/TASK-033-r2.md Requirement 2 ("never split on a character a subject can hold"); handoff/
    TASK-033-r3.md Requirement 4."""
    p = Project(tmp_path / "proj-cr-q7")
    p.brief("TASK-850")
    p.commit("records: brief", at(10, 0))
    msg = tmp_path / "message.txt"
    msg.write_bytes(b"docs: x\rTASK-850 later (#4)\n")
    git(p.ws, "add", "-A")
    git(p.ws, "commit", "-q", "--allow-empty", "--no-verify", "--cleanup=verbatim", "-F", str(msg),
        extra={"GIT_AUTHOR_DATE": gitdate(at(2, 2)), "GIT_COMMITTER_DATE": gitdate(at(2, 2))})
    raw = subprocess.run(["git", "-C", str(p.ws), "log", "-1", "--format=%s"], capture_output=True, timeout=TIMEOUT,
                         env=dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)).stdout
    assert b"\r" in raw, raw                                   # read as bytes: text mode would turn it into \n
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    assert Report(section(r.out, p.name)).at_week(2, "merged") in (None, 0), r


def test_task033r3_inherited_git_variables_do_not_redirect_the_read(tmp_path):
    """R-044. GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE and GIT_OBJECT_DIRECTORY in the caller's environment do not make
    pace-report.py read another repository than the Workspace's (the security audit's r2 A3).
    enforces: handoff/TASK-033.md Security context (git given the Workspace by `-C`); handoff/TASK-033-r3.md
    Requirement 5."""
    p = Project(tmp_path / "proj-gitdir-q7")
    p.brief("TASK-860")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-860: x (#1)", at(2, 2))
    other = tmp_path / "other-repo"
    other.mkdir()
    git(other, "init", "-q", "-b", "main")
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, PYTHONDONTWRITEBYTECODE="1",
               GIT_DIR=str(other / ".git"), GIT_WORK_TREE=str(other), GIT_INDEX_FILE=str(other / ".git" / "index"),
               GIT_OBJECT_DIRECTORY=str(other / ".git" / "objects"))
    proc = subprocess.run([sys.executable, PACE, str(p.root)], cwd=str(tmp_path), env=env, capture_output=True,
                          timeout=TIMEOUT)
    r = Run(proc.returncode, proc.stdout, proc.stderr)
    assert r.rc == 0, r
    assert Report(section(r.out, p.name)).at_week(2, "merged") == 1, r


def test_task033r3_every_git_command_runs_without_lazy_fetch(tmp_path, program, monkeypatch, capsys):
    """R-044. Every git command pace-report.py runs is given an environment with GIT_NO_LAZY_FETCH=1 and without
    GIT_DIR (a partial clone's lazy fetch would run the project's core.sshCommand: the security audit's r2 A3).
    enforces: handoff/TASK-033.md Security context ("It writes nothing anywhere"); handoff/TASK-033-r3.md
    Requirement 5."""
    p = Project(tmp_path / "proj-lazy-q7")
    p.brief("TASK-870")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-870: x (#1)", at(2, 2))
    mod = program("pace-report")
    seen = []
    real_init = subprocess.Popen.__init__

    def init(self, *args, **kwargs):
        argv = args[0] if args else kwargs.get("args")
        first = str(argv[0]) if isinstance(argv, (list, tuple)) and argv else str(argv or "")
        if os.path.splitext(os.path.basename(first))[0].lower() == "git":
            seen.append(kwargs.get("env"))
        real_init(self, *args, **kwargs)

    init.windowless_default = getattr(real_init, "windowless_default", False)
    monkeypatch.setattr(subprocess.Popen, "__init__", init)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "no-such-repo"))
    r = run_main(mod, monkeypatch, capsys, [p.root])
    assert r.rc == 0, r
    assert seen, "no git command was seen"
    for env in seen:
        assert env is not None and env.get("GIT_NO_LAZY_FETCH") == "1", env and sorted(env)
        assert "GIT_DIR" not in env


def test_task033r3_a_tracked_folder_named_main_is_no_failure(tmp_path):
    """R-044. A tracked top-level folder named `main` beside the branch does not make `git log main` ambiguous: the
    project is printed, its merge counted (the security audit's r2 A4: the ref was written without `--`).
    enforces: handoff/TASK-033-r2.md Requirement 4 ("Write the ref unambiguously"); handoff/TASK-033-r3.md
    Requirement 6."""
    p = Project(tmp_path / "proj-mainfolder-q7")
    p.brief("TASK-880")
    p.write("main/readme.txt", "a folder named main\n")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-880: x (#1)", at(2, 2))
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    assert Report(section(r.out, p.name)).at_week(2, "merged") == 1, r


@pytest.mark.parametrize("sep", ["\r", "\u2028", "\u2029", "\x85", "\x0c", "\x1c", "\x1e", "\x0b"])
@pytest.mark.parametrize("pattern", [PLAN_PATTERN, GRAMMAR_PATTERN], ids=["plan", "grammar"])
def test_task033r3_the_reader_splits_git_output_on_newlines_only(tmp_path, program, sep, pattern):
    """R-044. The one reader (and through it the round ceiling's claim lapse) splits git's output on `\\n` only: a
    subject holding a carriage return, a Unicode line or paragraph separator, a form feed or a file separator
    before an ID is one subject and merges nothing (the security audit's r2: `str.splitlines` made `docs: x<U+2028>TASK-050` lapse a claim).
    enforces: handoff/TASK-033-r2.md Requirement 2 ("never split on a character a subject can hold"); handoff/
    TASK-033.md Requirement 1 ("`_claim_lapsed` keeps its behaviour"); handoff/TASK-033-r3.md Requirement 4."""
    repo = verbatim_repo(tmp_path, "docs: x%sTASK-050 later" % sep)
    got = program("bridge_env").squash_merged_ids(str(repo), pattern)
    assert got is not None
    assert set(got) == set(), got


def test_task033r3_a_stage_name_the_name_grammar_refuses_is_not_listed(tmp_path):
    """R-044. A rounds record whose file name `bridge_env.parse_review_name` does not read (`rounds-STAGE-x y.json`)
    is not listed among the stage reviews over the ceiling (Review A r2 B5, the security audit's r2 A6: converged).
    enforces: handoff/TASK-033-r2.md Requirement 9 ("a stage ID is listed only when bridge_env.parse_review_name
    accepts it"); handoff/TASK-033-r3.md Requirement 8."""
    p = Project(tmp_path / "proj-stagename-q7")
    p.brief("TASK-900")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-900: x (#1)", at(2, 2))
    four = [(at(3, 1), None, None), (at(3, 2), None, None), (at(3, 3), None, None), (at(3, 4), None, None)]
    p.rounds("STAGE-x y", four)
    p.rounds("STAGE-B9", four)
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    assert "STAGE-B9" in r.out, r
    assert "STAGE-x" not in r.out, r


def test_task033r3_a_brief_in_a_sub_folder_is_no_brief(tmp_path):
    """R-044. Only `handoff/<ID>.md` and `handoff/<ID>-r<N>.md` at the folder's top are briefs: a tracked
    `handoff/old/TASK-905.md` does not make TASK-905 an ID that has a brief (Review A r2 S3).
    enforces: handoff/TASK-033.md Context ("An ID that has a brief means a tracked handoff/<ID>.md or
    handoff/<ID>-r<N>.md"); handoff/TASK-033-r3.md Requirement 9."""
    p = Project(tmp_path / "proj-subbrief-q7")
    p.brief("TASK-904")
    p.write("handoff/old/TASK-905.md", "# TASK-905\n")
    p.commit("records: briefs", at(10, 0))
    p.commit("TASK-904 TASK-905: two (#1)", at(2, 2))
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    assert Report(section(r.out, p.name)).at_week(2, "merged") == 1, r


def test_task033r3_the_first_merge_is_the_earliest_commit_time(tmp_path):
    """R-044. An increment's merge week is the week of the merging commit with the earliest committer time, whatever
    git's log order: a later commit dated earlier wins (Review A r2, Consider). enforces: handoff/TASK-033-r2.md
    Requirement 2 ("the week of the earliest commit that merges it"); handoff/TASK-033.md Context ("A merge's week is
    the squash commit's committer date"); handoff/TASK-033-r3.md Requirement 9."""
    p = Project(tmp_path / "proj-skew-q7")
    p.brief("TASK-906")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-906: first in history, dated later (#1)", at(1, 2))
    p.commit("docs: again (#2)", at(4, 2), body="Merges: TASK-906")
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(4, "merged") == 1, rep.text
    assert rep.at_week(1, "merged") in (None, 0), rep.text


def test_task033r3_a_hidden_session_file_is_not_read(tmp_path, program):
    """R-044. The session walk reads what `<key>/*.jsonl` and `<key>/**/subagents/*.jsonl` name as glob reads them:
    a file or folder whose name starts with a dot is not read (Review A r2, Consider: os.scandir sees what glob
    skipped). enforces: docs/BUILD_PLAN.md TASK-033 (b) (`~/.claude/projects/<key>/*.jsonl` and
    `<key>/**/subagents/*.jsonl`); handoff/TASK-033-r3.md Requirement 3."""
    home = tmp_path / "fixture-home"
    rec = assistant("m_one", at(2, 1), usage(100000, 200000, 300000, 400000))
    p, keys = transcript_project(tmp_path, home, program, "proj-hidden-q7", [rec])
    key_dir = home / ".claude" / "projects" / keys[0]
    write_lines(key_dir / ".hidden.jsonl", [assistant("m_h1", at(2, 2), usage(1000000, 0, 0, 0))])
    write_lines(key_dir / ".dot" / "subagents" / "a.jsonl", [assistant("m_h2", at(2, 2), usage(1000000, 0, 0, 0))])
    r = pace([p.root, "--tokens", "--home", home], cwd=tmp_path)
    assert r.rc == 0, r
    assert Report(section(r.out, p.name)).at_week(2, "tokens") == 1.0, r


def test_task033r3_a_commit_dated_past_the_calendar_is_skipped(tmp_path):
    """R-044. A commit whose date the platform cannot convert (far in the future) is skipped, never a traceback; the
    other commits are counted (the security audit's r2: fromtimestamp outside any try lost every project).
    enforces: handoff/TASK-033.md Security context (commit records are untrusted; never a traceback); handoff/
    TASK-033-r3.md Requirement 7."""
    p = Project(tmp_path / "proj-future-q7")
    p.brief("TASK-890", "TASK-891")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-890: x (#1)", at(2, 2))
    git(p.ws, "commit", "-q", "--allow-empty", "--no-verify", "-m", "TASK-891: far (#2)",
        extra={"GIT_AUTHOR_DATE": "@33000000000 +0000", "GIT_COMMITTER_DATE": "@33000000000 +0000"})
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    assert "Traceback" not in r.both
    assert Report(section(r.out, p.name)).at_week(2, "merged") == 1, r
