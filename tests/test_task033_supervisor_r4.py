"""Supervisor's acceptance tests for TASK-033 round 4 (R-044), the round past the owner's three-round ceiling, lifted by
the class line in handoff/TASK-033-r4.md; written by the supervisor from round 3's Review A and security audit; the
builder reads and runs them, never edits them.

R-044: the report cycle has a pace section for every project, computed by `pace-report.py`, read-only, from git and
the launcher's and the guard's own records; the pace report and the plan check read a squash subject by one rule, one
copy in `bridge_env.py`, under which a closing parenthesis merges an increment only when each of its comma-separated
items is a bare ID (ISS-013). Each test names the round-3 finding it closes and the paragraph it enforces.
"""
import builtins
import os
import subprocess
import time

import pytest

from test_task033_supervisor import (Project, Report, assistant, at, git, pace, readings, run_main, section, usage)
from test_task033_supervisor_r2 import GitWatch, lowered_limits, transcript_project


class SpyFile(object):
    """A file object whose readline records its size argument and, when `delay` is set, sleeps before each call."""

    def __init__(self, f, sizes, delay=0.0):
        self._f = f
        self._sizes = sizes
        self._delay = delay

    def readline(self, *args, **kwargs):
        size = args[0] if args else kwargs.get("size", kwargs.get("limit"))
        self._sizes.append(size)
        if self._delay:
            time.sleep(self._delay)
        return self._f.readline(*args, **kwargs)

    def __iter__(self):
        while True:
            line = self.readline()
            if not line:
                return
            yield line

    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._f.close()
        return False

    def __getattr__(self, name):
        return getattr(self._f, name)


def spy_open(monkeypatch, mod, folder, sizes, delay=0.0):
    """pace-report.py's `open` (the builtin, looked up in its module) wrapped for files under `folder`."""
    real_open = builtins.open
    root = os.path.normcase(os.path.abspath(str(folder)))

    def wrapped(file, *args, **kwargs):
        f = real_open(file, *args, **kwargs)
        try:
            inside = os.path.normcase(os.path.abspath(os.fspath(file))).startswith(root)
        except TypeError:
            inside = False
        return SpyFile(f, sizes, delay) if inside else f

    monkeypatch.setattr(mod, "open", wrapped, raising=False)


def test_task033r4_the_drain_of_an_over_cap_line_stops_at_the_deadline(tmp_path, program, monkeypatch, capsys):
    """R-044. The session read's limit holds while an over-cap line is drained: with LINE_CAP at 1,000, the limit at
    1 s and every read of a transcript slowed to 0.2 s, a 3 MB line without a newline ends the read at the limit (an
    empty tokens cell, the project named, exit 0) within a few seconds, where draining it to its end would take over
    nine (Review A r3 B1, the security audit's r3 B: converged; `if past_deadline(): pass`).
    enforces: handoff/TASK-033-r3.md Requirement 3 ("checking the deadline at every chunk"); docs/BUILD_PLAN.md
    TASK-033 (b) ("the read of the session folders is bounded like a git command"); handoff/TASK-033-r4.md
    Requirement 1."""
    home = tmp_path / "fixture-home"
    long_line = "x" * 3000000
    good = assistant("m_good", at(2, 1), usage(100000, 200000, 300000, 400000))
    p, _ = transcript_project(tmp_path, home, program, "proj-drain-q7", [long_line + good])
    mod = program("pace-report")
    monkeypatch.setattr(mod, "LINE_CAP", 1000)
    if not lowered_limits(mod, monkeypatch, 1):
        pytest.skip("pace-report.py holds no module-level 120-second limit to lower")
    GitWatch(monkeypatch, unlimited_git=True)
    spy_open(monkeypatch, mod, home / ".claude" / "projects", [], delay=0.2)
    t0 = time.monotonic()
    r = run_main(mod, monkeypatch, capsys, [p.root, "--tokens", "--home", home])
    elapsed = time.monotonic() - t0
    assert r.rc == 0, r
    assert elapsed < 6.0, "%.1f s\n%r" % (elapsed, r)
    rep = Report(section(r.out, p.name))
    for row in rep.weeks.values():
        assert rep.cell(row, "tokens") == "", row
    assert any(p.name in line and ("time" in line.lower() or "limit" in line.lower()) for line in r.both.splitlines()), r


def test_task033r4_every_transcript_read_is_given_a_size(tmp_path, program, monkeypatch, capsys):
    """R-044. Every readline on a transcript is given a size of at most LINE_CAP + 1, so no line is read whole before
    it is measured (Review A r3 S3: round 3's cap test did not catch `readline()` with no size coming back).
    enforces: handoff/TASK-033-r3.md Requirement 3 ("Read each line with f.readline(LINE_CAP + 1)"); handoff/
    TASK-033-r4.md Requirement 1."""
    home = tmp_path / "fixture-home"
    good = assistant("m_good", at(2, 1), usage(100000, 200000, 300000, 400000))
    p, _ = transcript_project(tmp_path, home, program, "proj-sizes-q7", [good, good])
    mod = program("pace-report")
    sizes = []
    spy_open(monkeypatch, mod, home / ".claude" / "projects", sizes)
    r = run_main(mod, monkeypatch, capsys, [p.root, "--tokens", "--home", home])
    assert r.rc == 0, r
    assert sizes, "no readline on a transcript was seen (the read must go through readline)"
    assert all(isinstance(s, int) and 0 < s <= mod.LINE_CAP + 1 for s in sizes), sizes
    assert Report(section(r.out, p.name)).at_week(2, "tokens") == 1.0


def letter_project(base, name, untracked_brief):
    p = Project(base / name)
    p.brief("TASK-040")
    p.report("TASK-040-r1")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-040: letters (#3)", at(1, 2))
    p.err("TASK-040", "TASK-040a", "TASK-040b")
    if untracked_brief:
        p.brief("TASK-040b")                             # on disk, never committed: no tracked brief
    return p


def test_task033r4_the_letter_rule_asks_the_tracked_list(tmp_path):
    """R-044. Whether a lettered token has a brief, for the letter rule, is read from the tracked list: an untracked
    `handoff/TASK-040b.md` on disk does not take `REVIEW-TASK-040b.err` away from TASK-040, so TASK-040's rounds read
    the same with the file as without it (Review A r3 B2, the security audit's r3 D: converged).
    enforces: handoff/TASK-033-r3.md Requirement 9 ("the letter rule asks the same tracked list"); handoff/TASK-033.md
    Context ("An ID that has a brief means a tracked handoff/<ID>.md"); handoff/TASK-033-r4.md Requirement 2."""
    plain = letter_project(tmp_path, "proj-letter-plain-q7", untracked_brief=False)
    draft = letter_project(tmp_path, "proj-letter-draft-q7", untracked_brief=True)
    assert "TASK-040b" not in git(draft.ws, "ls-files", "handoff/")
    readings_by = {}
    for p in (plain, draft):
        r = pace([p.root], cwd=tmp_path)
        assert r.rc == 0, r
        rep = Report(section(r.out, p.name))
        readings_by[p.name] = (rep.at_week(1, "rounds_mean"), rep.at_week(1, "rounds_max"))
    assert readings_by[plain.name][1] is not None, readings_by
    assert readings_by[draft.name] == readings_by[plain.name], readings_by


@pytest.mark.parametrize("subject,plan_expected,grammar_expected", [
    ("docs: x (TASK-100, R-027) (#5)", {"TASK-100"}, {"TASK-100", "R-027"}),
    ("docs: x (R-027)", set(), {"R-027"}),
    ("docs: x ( R-027 , BUG-018 )", set(), {"R-027", "BUG-018"}),
])
def test_task033r4_r_nnn_is_a_bare_item_merging_only_under_the_grammar(tmp_path, program, monkeypatch, subject,
                                                                       plan_expected, grammar_expected):
    """R-044. `R-nnn` is a bare parenthesis item under either pattern; it merges nothing under the plan pattern and, as
    an ID token holding a hyphen and a digit, merges itself under the grammar's (Review A r3 B3, the security audit's
    r3 C: converged; round 3 tested `R-nnn` before the pattern, so under the grammar it never merged).
    enforces: handoff/TASK-033.md Requirement 1 ("`R-nnn` counts as a bare item but merges nothing under the plan
    pattern"); handoff/TASK-033-r2.md Requirement 1 (under the grammar `(TASK-100, R-027)` merges its IDs);
    handoff/TASK-033-r4.md Requirement 3."""
    pc, plan, grammar = readings(tmp_path, program, monkeypatch, subject)
    assert pc == plan_expected and plan == plan_expected, (pc, plan)
    assert grammar == grammar_expected, grammar


def test_task033r4_a_tracked_path_named_like_the_ref_is_no_failure(tmp_path):
    """R-044. A tracked file at `refs/heads/main` in the Workspace does not make the commit read's ref ambiguous: the
    `--` after the ref is pinned (Review A r3 S3: a folder named `main` could not tell `refs/heads/main --` from
    `refs/heads/main`). enforces: handoff/TASK-033-r3.md Requirement 6 ("the options before the ref, `--` after it");
    handoff/TASK-033-r4.md Requirement 4."""
    p = Project(tmp_path / "proj-refpath-q7")
    p.brief("TASK-910")
    p.write("refs/heads/main", "a file at the ref's path\n")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-910: x (#1)", at(2, 2))
    probe = subprocess.run(["git", "-C", str(p.ws), "log", "--format=%s", "refs/heads/main"], capture_output=True,
                           timeout=300, env=dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull,
                                                 GIT_CONFIG_SYSTEM=os.devnull))
    if probe.returncode == 0:
        pytest.skip("this git does not find `refs/heads/main` ambiguous beside a file of that path")
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    assert Report(section(r.out, p.name)).at_week(2, "merged") == 1, r
