"""TASK-065's acceptance tests, the supervisor's (R-085; D-004): the launcher's wait before a CI watch, and the watch started
again where no list of required contexts could be named. enforces: docs/DESIGN.md, Change: the program release, the launcher
(F2, both cases, and J6); docs/BUILD_PLAN.md, TASK-065, Done when. The builder reads and runs these tests and never edits them.

The interface these tests fix (the brief states it):
  bridge-run.py's WATCH_POLL, the wait's interval in seconds, and watch_loop(argv, folder, limit, start): argv the watch's words
  (gh pr checks <n> ...), folder the launch folder, limit the run's seconds, start(words, seconds) the function that runs one
  watch for at most that many seconds and returns its exit. watch_loop returns the launcher's exit. It reads GitHub only through
  bridge_env's readers, its clock and its pause through the module's name `time` (time.monotonic, time.sleep), and prints its
  lines on standard error, each beginning `bridge-run: `. Each poll begins with one read of the pull request (pull_refs).

Every case runs on GitHub's replies recorded from this repository (tests/fixtures/github/: TASK-064's captured replies and the
head states built from them, `ready-*.json` for TASK-083 and `wait-*.json` for this increment, each header naming the captured
reply and the fields changed), answered by TASK-064's stand-in `gh` with two additions: the captured head (forty 1s) is replaced
in every reply by the case's local head, and the replies are a list of states, the n-th read of the pull request (the n-th poll)
answering from the n-th state and every later read from the last. A path the stand-in has no route for is GitHub's 404. The
clock is the test's: time.sleep advances it, nothing else does, and a watch advances it by its own duration.

On the checkpoint every case is red: the launcher has no watch_loop and keeps the old wait, whose own two cases this file
replaces (tests/test_hotfix25a_roster_launcher.py, a pointer). The child launcher's case runs where a stand-in gh can stand on
PATH as a shell script (CI's ubuntu job)."""
import json
import os
import shutil
import subprocess
import sys

import pytest

import test_program_branch_rule as B
import test_program_ready as R
import test_task032_supervisor_guard as G

FIXTURES = B.FIXTURES
FORTY = R.FORTY
LAUNCHER = os.path.normpath(os.path.join(os.path.dirname(G.PROG), "bridge-run.py"))
OTHER = "2222222222222222222222222222222222222222"
OLD_ROUTE = 'name = config["routes"].get(key)'
NEW_ROUTE = ('polls = sum(1 for line in open(config["log"], encoding="utf-8") if "/pulls/" in line)\n'
             'states = config["states"]\n'
             'name = states[min(max(polls - 1, 0), len(states) - 1)].get(key)')
assert OLD_ROUTE in R.STANDIN, "TASK-064's stand-in reads one route map"
STANDIN = R.STANDIN.replace(OLD_ROUTE, NEW_ROUTE)

BASE = "the base branch's required contexts (main)"
DEFAULT = "the default branch's required contexts (main)"
RUNS = "the workflow runs"
REQUIRED = ["bridge programs (windows-latest)", "bridge programs (ubuntu-latest)", "security floor"]
WATCH = ["gh", "pr", "checks", "12", "--watch", "--required", "--fail-fast"]
PLAIN_WATCH = ["gh", "pr", "checks", "12", "--watch"]
GREEN = dict(checks="check-runs.json", runs="runs.json")
NO_RULE = R.NO_RULE
NONE_ANYWHERE = dict(NO_RULE, default=("ready-protection-main-none.json", "rules-main.json"))
DEFAULT_LIST = dict(NO_RULE, default=("protection-main.json", "rules-main.json"))


class Clock:
    """The test's clock: monotonic() reads it, sleep(s) advances it and records s."""

    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

    def time(self):
        return self.now


class Watch:
    """A watch stand-in: start(words, seconds) records the call, advances the clock by `duration` and returns the next exit."""

    def __init__(self, clock, exits, duration=60):
        self.clock, self.exits, self.duration = clock, list(exits), duration
        self.calls = []

    def __call__(self, words, seconds):
        self.calls.append((list(words), seconds))
        self.clock.now += self.duration
        return self.exits.pop(0) if self.exits else 0


class Case:
    def __init__(self, tmp_path, monkeypatch, capsys, program):
        self.tmp, self.mp, self.capsys = tmp_path, monkeypatch, capsys
        self.br = program("bridge-run")
        self.repo = G.make_repo(tmp_path)
        self.head = G.git(self.repo, "rev-parse", "HEAD")
        self.clock = Clock()
        monkeypatch.setattr(self.br, "time", self.clock)
        self.log = tmp_path / "gh-wait-calls.jsonl"

    def states(self, *states):
        """Each state a dict of routes() keywords; returns the route maps the stand-in answers from."""
        return [R.routes(self.head, **s) for s in states]

    def run(self, states, argv=WATCH, limit=3600, exits=(0,), duration=60, raw_states=None):
        maps = raw_states if raw_states is not None else self.states(*states)
        standin = self.tmp / "standin_wait_gh.py"
        standin.write_text(STANDIN, encoding="utf-8")
        if self.log.exists():
            self.log.unlink()
        self.log.write_text("", encoding="utf-8")
        cfg = self.tmp / "wait-routes.json"
        cfg.write_text(json.dumps({"states": maps, "fixtures": FIXTURES, "log": str(self.log), "sha": self.head}), encoding="utf-8")
        self.mp.setattr(self.br.bridge_env, "GH_COMMAND", [sys.executable, str(standin), str(cfg)])
        self.watch = Watch(self.clock, exits, duration)
        self.capsys.readouterr()
        rc = self.br.watch_loop(list(argv), str(self.repo), limit, self.watch)
        self.err = self.capsys.readouterr().err
        return rc

    def calls(self):
        return [json.loads(l) for l in self.log.read_text(encoding="utf-8").splitlines() if l.strip()]

    def polls(self):
        return sum(1 for c in self.calls() if any("/pulls/" in a for a in c))

    def lines(self):
        return [l for l in self.err.splitlines() if l.startswith("bridge-run: ")]

    def started(self):
        return [w for w, _s in self.watch.calls]


@pytest.fixture
def case(tmp_path, monkeypatch, capsys, program):
    return Case(tmp_path, monkeypatch, capsys, program)


def with_other_head(case, state):
    """A route map for `state` that also answers the old head's lists, so a wait that reads them is seen to count them."""
    m = R.routes(case.head, **state)
    for k, v in R.routes(OTHER, **GREEN).items():
        if OTHER in k:
            m[k] = v
    return m


# ---------------------------------------------------------------- the field's two cases (F2), red on the checkpoint


def test_r085_field_a_required_job_with_needs_is_waited_for_under_required(case):
    """F2, first case: under --required the two bridge programs jobs (needs: security floor) have no check yet; the watch
    starts only once every required context of main has one, as given, with what was left of the limit."""
    rc = case.run([dict(checks="wait-checks-floor-only.json", runs="wait-runs-in-progress.json"), GREEN], limit=3600)
    assert rc == 0, case.err
    assert case.started() == [WATCH], case.watch.calls
    assert case.clock.sleeps == [case.br.WATCH_POLL], case.clock.sleeps
    assert case.watch.calls[0][1] == 3600 - case.br.WATCH_POLL, case.watch.calls
    line = [l for l in case.lines() if "waited" in l]
    assert line and "waited %ds" % case.br.WATCH_POLL in line[0] and BASE in line[0] and "the watch starts" in line[0], case.err


def test_r085_field_b_app_checks_green_while_the_workflow_is_queued_never_start_the_watch(case):
    """F2, second case: on a base with no rule, without --required, two app checks green while the run is queued, then
    running with no check of its own: the watch starts only once the run has a check, and without --required."""
    states = [dict(NONE_ANYWHERE, checks="ready-checks-S07-apps-only.json", runs="ready-runs-S07-queued.json"),
              dict(NONE_ANYWHERE, checks="ready-checks-S07-apps-only.json", runs="wait-runs-in-progress.json"),
              dict(NONE_ANYWHERE, checks="wait-checks-run-pending.json", runs="wait-runs-in-progress.json"),
              dict(NONE_ANYWHERE, **GREEN)]
    rc = case.run(states, argv=PLAIN_WATCH)
    assert rc == 0, case.err
    assert case.started() == [PLAIN_WATCH], case.watch.calls
    assert case.clock.sleeps == [case.br.WATCH_POLL] * 2, case.clock.sleeps
    assert any(RUNS in l and "the watch starts" in l for l in case.lines()), case.err


# ---------------------------------------------------------------- the base's list


def test_r085_a_head_every_required_context_holds_starts_the_watch_at_once_and_is_not_watched_again(case):
    rc = case.run([GREEN])
    assert rc == 0 and case.started() == [WATCH] and case.clock.sleeps == [], case.err
    assert case.polls() == 1, "a named list is never read again after the watch: %r" % case.calls()
    assert any("waited 0s" in l and BASE in l for l in case.lines()), case.err


def test_r085_a_pending_check_holds_its_context(case):
    rc = case.run([dict(checks="wait-checks-pending.json", runs="wait-runs-in-progress.json")])
    assert rc == 0 and case.started() == [WATCH] and case.clock.sleeps == [], case.err


@pytest.mark.parametrize("checks,word", [("wait-checks-floor-failed.json", "failure"), ("wait-checks-floor-timed-out.json", "timed_out")],
                         ids=["failed", "timed-out"])
def test_r085_a_failed_check_starts_the_watch_at_once_with_contexts_still_missing(case, checks, word):
    """So that --fail-fast reports it: a timed-out check is failed by TASK-064's closed list."""
    rc = case.run([dict(checks=checks, runs="wait-runs-in-progress.json")])
    assert rc == 0 and case.started() == [WATCH] and case.clock.sleeps == [], case.err
    assert any("security floor" in l and "failed" in l and word in l for l in case.lines()), case.err


def test_r085_contexts_still_missing_at_the_limit_end_the_run_with_124_naming_them(case):
    rc = case.run([dict(checks="wait-checks-floor-only.json", runs="wait-runs-in-progress.json")], limit=35)
    assert rc == 124 and case.started() == [], case.err
    limit_lines = [l for l in case.lines() if l.startswith("bridge-run: LIMIT")]
    assert len(limit_lines) == 1, case.err
    assert "bridge programs (windows-latest)" in limit_lines[0] and "bridge programs (ubuntu-latest)" in limit_lines[0], limit_lines
    assert "security floor" not in limit_lines[0].split(":", 2)[-1], "security floor has its check: " + limit_lines[0]
    assert 35 <= case.clock.now - 1000.0 <= 35 + case.br.WATCH_POLL, case.clock.sleeps


def test_r085_the_checks_of_a_head_github_has_not_yet_taken_prove_nothing(case):
    """KP-051 kept: while the pull request's head on GitHub is not the local head, its lists (all green here) are not counted."""
    old = with_other_head(case, dict(pull="wait-pull-old-head.json", checks="wait-checks-none.json", runs="wait-runs-none.json"))
    rc = case.run(None, raw_states=[old, R.routes(case.head, **GREEN)])
    assert rc == 0 and case.started() == [WATCH], case.err
    assert case.clock.sleeps == [case.br.WATCH_POLL], case.clock.sleeps


def test_r085_a_head_github_never_takes_ends_at_the_limit_naming_both_heads(case):
    old = with_other_head(case, dict(pull="wait-pull-old-head.json", checks="wait-checks-none.json", runs="wait-runs-none.json"))
    rc = case.run(None, raw_states=[old], limit=25)
    assert rc == 124 and case.started() == [], case.err
    limit_lines = [l for l in case.lines() if l.startswith("bridge-run: LIMIT")]
    assert limit_lines and OTHER[:12] in limit_lines[0] and case.head[:12] in limit_lines[0], case.err


# ---------------------------------------------------------------- the three cases with no list of the base's: no --required


def test_r085_a_base_with_no_rule_waits_for_the_default_branchs_contexts_without_required(case):
    states = [dict(DEFAULT_LIST, checks="wait-checks-floor-only.json", runs="wait-runs-in-progress.json"), dict(DEFAULT_LIST, **GREEN)]
    rc = case.run(states)
    assert rc == 0, case.err
    assert case.started() == [[w for w in WATCH if w != "--required"]], case.watch.calls
    assert case.clock.sleeps == [case.br.WATCH_POLL], case.clock.sleeps
    assert any(DEFAULT in l and "the watch starts" in l for l in case.lines()), case.err
    assert any("without --required" in l for l in case.lines()), case.err
    assert case.polls() == 2, "a named list is never read again after the watch: %r" % case.calls()


def test_r085_no_rule_anywhere_waits_for_the_runs_and_starts_without_required(case):
    rc = case.run([dict(NONE_ANYWHERE, **GREEN)])
    assert rc == 0, case.err
    assert case.started() == [[w for w in WATCH if w != "--required"]], case.watch.calls
    assert any(RUNS in l and "the watch starts" in l for l in case.lines()), case.err
    assert any("without --required" in l and "names no required context" in l for l in case.lines()), case.err


def test_r085_a_rule_that_cannot_be_read_waits_for_the_runs_says_why_and_starts_without_required(case):
    rc = case.run([dict(prot="protection-unreadable.json", **GREEN)])
    assert rc == 0, case.err
    assert case.started() == [[w for w in WATCH if w != "--required"]], case.watch.calls
    why = [l for l in case.lines() if "cannot be read" in l]
    assert why and "Resource not accessible by integration" in why[0] and "without --required" in why[0], case.err


def test_r085_without_required_given_the_watch_is_started_as_given_and_the_line_names_no_option(case):
    rc = case.run([dict(NONE_ANYWHERE, **GREEN)], argv=PLAIN_WATCH)
    assert rc == 0 and case.started() == [PLAIN_WATCH], case.err
    assert not any("--required" in l for l in case.lines()), case.err


# ---------------------------------------------------------------- the runs


def test_r085_no_run_started_at_the_limit_ends_with_124_saying_so(case):
    rc = case.run([dict(NONE_ANYWHERE, checks="ready-checks-S07-apps-only.json", runs="wait-runs-none.json")], limit=25)
    assert rc == 124 and case.started() == [], case.err
    assert any(l.startswith("bridge-run: LIMIT") and "no workflow run" in l for l in case.lines()), case.err


def test_r085_a_run_with_no_check_at_the_limit_ends_with_124_naming_it(case):
    rc = case.run([dict(NONE_ANYWHERE, checks="ready-checks-S07-apps-only.json", runs="wait-runs-in-progress.json")], limit=25)
    assert rc == 124 and case.started() == [], case.err
    assert any(l.startswith("bridge-run: LIMIT") and "run tests (pull_request)" in l for l in case.lines()), case.err


def test_r085_a_run_that_completed_without_a_check_does_not_hold_the_wait(case):
    rc = case.run([dict(NONE_ANYWHERE, checks="ready-checks-S07-apps-only.json", runs="wait-runs-failed-at-start.json")])
    assert rc == 0 and case.started() and case.clock.sleeps == [], case.err


def test_r085_a_failed_check_starts_the_watch_at_once_under_the_runs(case):
    rc = case.run([dict(NONE_ANYWHERE, checks="wait-checks-floor-failed.json", runs="wait-runs-in-progress.json")], exits=(1,))
    assert rc == 1 and len(case.started()) == 1 and case.clock.sleeps == [], case.err


# ---------------------------------------------------------------- the watch started again where no list was named


TWO = [dict(NONE_ANYWHERE, checks="wait-checks-two-running.json", runs="wait-runs-two-running.json"),
       dict(NONE_ANYWHERE, checks="wait-checks-two-gap.json", runs="wait-runs-two-one-done.json"),
       dict(NONE_ANYWHERE, checks="wait-checks-two-next.json", runs="wait-runs-two-one-done.json"),
       dict(NONE_ANYWHERE, checks="wait-checks-two-done.json", runs="wait-runs-two-done.json")]


def test_r085_a_watch_that_returned_between_two_jobs_is_started_again_once_the_next_check_is_listed(case):
    """The plan's case: one run completed and a second still running with no pending check yet: no watch started until the
    check is listed (one interval), then the watch started a second time; the runs then all completed, the launcher's exit is
    the last watch's."""
    rc = case.run(TWO, exits=(0, 0))
    assert rc == 0, case.err
    assert case.started() == [[w for w in WATCH if w != "--required"]] * 2, case.watch.calls
    assert case.clock.sleeps == [case.br.WATCH_POLL], case.clock.sleeps
    assert case.polls() == 4, case.calls()
    assert any("starts again" in l for l in case.lines()), case.err


def test_r085_the_second_watch_s_exit_is_the_launcher_s(case):
    rc = case.run(TWO[:3], exits=(0, 1))
    assert rc == 1 and len(case.started()) == 2, case.err
    assert case.polls() == 3, "a watch that returns 1 ends the launcher, nothing read after it: %r" % case.calls()


@pytest.mark.parametrize("code", [1, 8], ids=["failed", "pending"])
def test_r085_a_watch_that_returns_another_exit_ends_the_launcher_with_it(case, code):
    rc = case.run([dict(NONE_ANYWHERE, **GREEN)], exits=(code,))
    assert rc == code and len(case.started()) == 1, case.err
    assert case.polls() == 1, case.calls()


def test_r085_the_watch_is_not_started_again_where_every_run_completed(case):
    rc = case.run([dict(NONE_ANYWHERE, **GREEN)], exits=(0,))
    assert rc == 0 and len(case.started()) == 1 and case.polls() == 2, case.calls()


def test_r085_the_next_check_never_listed_ends_at_the_limit(case):
    rc = case.run(TWO[:2], exits=(0,), limit=200, duration=60)
    assert rc == 124 and len(case.started()) == 1, case.err
    assert any(l.startswith("bridge-run: LIMIT") for l in case.lines()), case.err
    assert case.clock.now - 1000.0 <= 200 + case.br.WATCH_POLL, case.clock.sleeps


def test_r085_the_second_watch_gets_what_is_left_of_the_limit(case):
    case.run(TWO, exits=(0, 0), limit=3600, duration=60)
    (_w1, s1), (_w2, s2) = case.watch.calls
    assert s1 == 3600 and s2 == 3600 - 60 - case.br.WATCH_POLL, case.watch.calls


# ---------------------------------------------------------------- a poll that fails


def test_r085_a_failed_poll_is_retried_and_its_reason_printed_once(case):
    states = [dict(checks=None, runs="wait-runs-in-progress.json"), dict(checks=None, runs="wait-runs-in-progress.json"), GREEN]
    rc = case.run(states)
    assert rc == 0 and case.started() == [WATCH], case.err
    assert case.clock.sleeps == [case.br.WATCH_POLL] * 2, case.clock.sleeps
    failed = [l for l in case.lines() if "a poll failed" in l]
    assert len(failed) == 1 and "Not Found" in failed[0], case.err


def test_r085_a_pull_request_that_cannot_be_read_is_retried(case):
    rc = case.run([dict(pull=None, **GREEN), GREEN])
    assert rc == 0 and case.started() == [WATCH] and case.clock.sleeps == [case.br.WATCH_POLL], case.err


def test_r085_a_poll_that_keeps_failing_ends_at_the_limit(case):
    rc = case.run([dict(checks=None, runs="wait-runs-in-progress.json")], limit=25)
    assert rc == 124 and case.started() == [], case.err
    assert len([l for l in case.lines() if "a poll failed" in l]) == 1, case.err


# ---------------------------------------------------------------- what stays


def test_r085_a_check_without_watch_reads_nothing_and_runs_as_given(case):
    rc = case.run([GREEN], argv=["gh", "pr", "checks", "12", "--required"], limit=600)
    assert rc == 0 and case.watch.calls == [(["gh", "pr", "checks", "12", "--required"], 600)], case.watch.calls
    assert case.calls() == [] and case.lines() == [], (case.calls(), case.err)


def test_r085_the_old_wait_is_gone(program):
    br = program("bridge-run")
    assert not hasattr(br, "wait_for_first_check") and not hasattr(br, "WATCH_WAIT"), "the 120-second wait goes with its message"


def test_r085_every_poll_is_a_get_of_the_reader(case):
    case.run(TWO, exits=(0, 0))
    for args in case.calls():
        assert args[0] == "api" and not any(a in ("-X", "--method", "-f", "-F", "--input") for a in args), args


# ---------------------------------------------------------------- main runs the loop (a child launcher; a POSIX stand-in gh)


@pytest.mark.skipif(sys.platform == "win32", reason="a stand-in gh on PATH is a shell script; CI's ubuntu job runs it")
@pytest.mark.parametrize("state,expect_required", [(GREEN, True), (dict(NONE_ANYWHERE, **GREEN), False)], ids=["base-list", "no-rule"])
def test_r085_the_launcher_waits_then_runs_the_watch_it_was_given(tmp_path, state, expect_required):
    repo = G.make_repo(tmp_path)
    head = G.git(repo, "rev-parse", "HEAD")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "gh-calls.jsonl"
    log.write_text("", encoding="utf-8")
    cfg = tmp_path / "routes.json"
    cfg.write_text(json.dumps({"states": [R.routes(head, **state)], "fixtures": FIXTURES, "log": str(log), "sha": head}), encoding="utf-8")
    standin = tmp_path / "standin_wait_gh.py"
    standin.write_text(STANDIN.replace('if not args or args[0] != "api":',
                                       'if args[:2] == ["pr", "checks"]:\n    sys.stdout.write("WATCH " + " ".join(args) + "\\n")\n    sys.exit(0)\n'
                                       'if not args or args[0] != "api":'), encoding="utf-8")
    gh = bin_dir / "gh"
    gh.write_text('#!/bin/sh\nexec "%s" "%s" "%s" "$@"\n' % (sys.executable, standin, cfg), encoding="ascii")
    gh.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("BRIDGE_RUN_ALLOW_ANY", "BRIDGE_RUN_SLOT_SCALE")}
    env["PATH"] = os.pathsep.join([str(bin_dir), env.get("PATH", "")])
    assert shutil.which("gh", path=env["PATH"]) == str(gh)
    p = subprocess.run([sys.executable, LAUNCHER, "--limit", "120", "--"] + WATCH,
                       capture_output=True, text=True, cwd=str(repo), env=env, timeout=300)
    assert p.returncode == 0, p.stdout + p.stderr
    watch_line = [l for l in p.stdout.splitlines() if l.startswith("WATCH ")]
    assert len(watch_line) == 1, p.stdout
    assert ("--required" in watch_line[0].split()) is expect_required, watch_line
    assert "waited 0s" in p.stderr, p.stderr
