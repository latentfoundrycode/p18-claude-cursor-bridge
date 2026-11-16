"""TASK-083's acceptance tests, the supervisor's (R-083; D-003): `review-guard.py ready <pr>`, the proof that CI passed on the
pull request's head as a program, the ready record it writes on READY and nothing else, the permission guard's merge rule that
requires that record for the pull request's number and the head the command names, and `premerge-records <pr>` making the same
check and writing both records or neither. enforces: docs/DESIGN.md, Change: the program release, the review guard (T-CONTEXT);
docs/BUILD_PLAN.md, TASK-083, Done when. The builder reads and runs these tests and never edits them.

Every case runs on GitHub's replies recorded from this repository (tests/fixtures/github/; the head states `ready-*.json` built
from TASK-064's captured replies, each header naming the captured reply and the fields changed), answered by TASK-064's stand-in
`gh` with one addition: the head's sha of the captured replies (forty 1s) is replaced in every reply by the local head of the
case's repository, so the routes are built at run time from that head. A path the stand-in has no route for is GitHub's 404.

The lines pinned (the brief states them):
  review-guard: READY - pull request <pr>, head <head 12>, <reading>
  review-guard: NOT READY - pull request <pr>, head <head 12>, <reading>: <item>: <class>[; <item>: <class>]...
  review-guard: NOT READY - pull request <pr>, head <head 12>: the head moved (GitHub's head is <head 12>)
  review-guard: CANNOT CHECK - pull request <pr>: <reason>
<reading> one of: the base branch's required contexts (<base>) / the default branch's required contexts (<default>) /
the workflow runs; <item> a context's name, or under the runs `run <name> (<event>)`, `check <name>`, `status <context>`, or
`no workflow run succeeded`; <class> missing, pending or failed, a note in parentheses after it where the brief names one."""
import json
import os
import subprocess
import sys
import urllib.parse

import pytest

import test_program_branch_rule as B
import test_task032_supervisor_guard as G
from test_bug039 import load_guard

FIXTURES = B.FIXTURES
FORTY = "1111111111111111111111111111111111111111"
OLD = 'sys.stdout.write(json.dumps(doc["body"]))'
NEW = 'sys.stdout.write(json.dumps(doc["body"]).replace("%s", config.get("sha") or "%s"))' % (FORTY, FORTY)
assert OLD in B.STANDIN, "TASK-064's stand-in writes the body on one line"
STANDIN = B.STANDIN.replace(OLD, NEW)
PGUARD = G.PGUARD

BASE_READING = "the base branch's required contexts (main)"
DEFAULT_READING = "the default branch's required contexts (main)"
RUNS_READING = "the workflow runs"
RELEASE = "release/2026.11.03"
NO_RULE = dict(pull="ready-pull-release.json", base=RELEASE, prot="protection-release-none.json", rules="rules-release.json",
               default=("ready-protection-main-none.json", "rules-main.json"))
APP_RULE = dict(prot="ready-protection-main-none.json", rules="rules-app.json")


def routes(head, pr="12", pull="pull.json", base="main", prot="protection-main.json", rules="rules-main.json",
           checks="check-runs.json", status="status.json", runs="runs.json", default=None, repo="repo.json", pages=None):
    """The stand-in's routes for one case: a value of None leaves that path unanswered (GitHub's 404)."""
    enc = urllib.parse.quote(base, safe="")
    r = {
        "repos/OWNER/REPO/pulls/%s" % pr: pull,
        "repos/OWNER/REPO/branches/%s/protection/required_status_checks" % enc: prot,
        "repos/OWNER/REPO/rules/branches/%s" % enc: rules,
        "repos/OWNER/REPO/commits/%s/check-runs?filter=all" % head: checks,
        "repos/OWNER/REPO/commits/%s/status" % head: status,
        "repos/OWNER/REPO/actions/runs?head_sha=%s" % head: runs,
        "repos/OWNER/REPO": repo,
    }
    if default:
        r["repos/OWNER/REPO/branches/main/protection/required_status_checks"] = default[0]
        r["repos/OWNER/REPO/rules/branches/main"] = default[1]
    out = {k + "#1": v for k, v in r.items() if v}
    for k, v in (pages or {}).items():
        out[k] = v
    return out


def use_standin(module_env, monkeypatch, tmp_path, route_map, sha):
    """Every gh api call of `module_env` (bridge_env) answered by the stand-in from route_map; returns the call log's path."""
    standin = tmp_path / "standin_ready_gh.py"
    standin.write_text(STANDIN, encoding="utf-8")
    log = tmp_path / "gh-ready-calls.jsonl"
    if log.exists():
        log.unlink()
    cfg = tmp_path / "ready-routes.json"
    cfg.write_text(json.dumps({"routes": route_map, "fixtures": FIXTURES, "log": str(log), "sha": sha}), encoding="utf-8")
    monkeypatch.setattr(module_env, "GH_COMMAND", [sys.executable, str(standin), str(cfg)])
    return log


def ready_routes(head, pr="12"):
    """The routes of a head every required context of main holds green (for other tests that need a READY head)."""
    return routes(head, pr=pr)


class Case:
    def __init__(self, tmp_path, monkeypatch, capsys):
        self.tmp, self.mp, self.capsys = tmp_path, monkeypatch, capsys
        self.repo = G.make_repo(tmp_path)
        self.head = G.git(self.repo, "rev-parse", "HEAD")
        self.premerge(self.head)
        self.guard = load_guard(monkeypatch)
        monkeypatch.setattr(self.guard, "PR_HEAD_WAIT", 0)
        monkeypatch.chdir(str(self.repo))
        self.log = None

    def premerge(self, head):
        G.put(G.bridge_dir(self.repo) / "premerge" / head, json.dumps({"pr": "12", "review": "TASK-001", "snapshot": "x", "written": "2026-11-16T10:00:00"}))

    def run(self, pr="12", **kw):
        self.log = use_standin(self.guard.bridge_env, self.mp, self.tmp, routes(self.head, pr=pr, **kw), self.head)
        self.capsys.readouterr()
        self.mp.setattr(sys, "argv", ["review-guard.py", "ready", pr])
        rc = self.guard.main()
        return rc, self.capsys.readouterr().out

    def ready_records(self):
        folder = G.bridge_dir(self.repo) / "ready"
        return sorted(os.listdir(str(folder))) if folder.exists() else []

    def calls(self):
        if not self.log or not self.log.exists():
            return []
        return [json.loads(l) for l in self.log.read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture
def case(tmp_path, monkeypatch, capsys):
    return Case(tmp_path, monkeypatch, capsys)


def verdict(out, word):
    hits = [l for l in out.splitlines() if l.startswith("review-guard: %s - " % word)]
    assert len(hits) == 1, out
    return hits[0]


# ---------------------------------------------------------------- the fixtures


def test_every_ready_fixture_says_how_it_was_made_and_holds_no_account():
    """Each head state built from a captured reply, the header naming it; the owner and the repository as placeholders."""
    names = sorted(n for n in os.listdir(FIXTURES) if n.startswith("ready-") and n.endswith(".json"))
    assert len(names) >= 30, names
    for n in names:
        doc = B.fixture(n)
        text = json.dumps(doc)
        assert doc["fixture"] == "built" and "from the captured" in doc["note"] and "TASK-083" in doc["note"], n
        assert doc["request"].startswith("repos/OWNER/REPO"), n
        assert "latentfoundrycode" not in text and "p18-claude-cursor-bridge" not in text and "ghp_" not in text, n


# ---------------------------------------------------------------- READY under each reading, and the record


READY_CASES = {
    "S01 every required context of the base successful": (dict(), BASE_READING),
    "S06 no rule on the base or the default branch, every run succeeded": (dict(NO_RULE), RUNS_READING),
    "S09 a cancelled run beside its successor": (dict(NO_RULE, checks="ready-checks-S09-cancelled.json", runs="ready-runs-S09-cancelled.json"), RUNS_READING),
    "S10 a required context skipped, no failure beside it": (dict(checks="ready-checks-S10-skipped.json"), BASE_READING),
    "S17 a required context held by a commit status": (dict(prot="ready-protection-main-none.json", rules="ready-rules-legacy.json", status="status-one.json"), BASE_READING),
    "S27 a required context skipped beside a cancelled run its successor replaced": (dict(checks="ready-checks-S27-skipped-cancelled.json", runs="ready-runs-S09-cancelled.json"), BASE_READING),
    "S13r the default branch's contexts held on a base with no rule": (dict(NO_RULE, default=("protection-main.json", "rules-main.json")), DEFAULT_READING),
}


@pytest.mark.parametrize("name", sorted(READY_CASES))
def test_r083_ready_proves_ci_writes_the_ready_record_and_names_its_reading(case, name):
    """enforces: T-CONTEXT, READY (exit 0): the heads equal, the premerge record standing, CI proven; the ready record
    `<git common dir>/bridge/ready/<pr>-<head>` written beside the premerge record; the line names the pull request, the head and
    the reading."""
    kw, reading = READY_CASES[name]
    rc, out = case.run(**kw)
    line = verdict(out, "READY")
    assert rc == 0, out
    assert line == "review-guard: READY - pull request 12, head %s, %s" % (case.head[:12], reading), out
    assert case.ready_records() == ["12-" + case.head], out
    assert os.listdir(str(G.bridge_dir(case.repo) / "premerge")) == [case.head], "the premerge record stays"


# ---------------------------------------------------------------- NOT READY: each context or run named, nothing written


NOT_READY_CASES = {
    "S02 one required context missing": (dict(checks="ready-checks-S02-missing.json"), BASE_READING, ["security floor: missing"], []),
    "S03 one pending": (dict(checks="ready-checks-S03-pending.json", runs="ready-runs-S03-pending.json"), BASE_READING, ["security floor: pending"], []),
    "S04 one failed": (dict(checks="ready-checks-S04-failed.json", runs="ready-runs-S04-failed.json"), BASE_READING, ["security floor: failed"], []),
    "S07 a queued workflow beside two green app checks": (dict(NO_RULE, checks="ready-checks-S07-apps-only.json", runs="ready-runs-S07-queued.json"), RUNS_READING, ["run tests (pull_request): pending"], []),
    "S08 a run failed": (dict(NO_RULE, checks="ready-checks-S08-failed.json", runs="ready-runs-S08-failed.json"), RUNS_READING, ["run tests (pull_request): failed"], []),
    "S11 a required context skipped beside a failure": (dict(checks="ready-checks-S11-skipped-failure.json"), BASE_READING, ["security floor: "], []),
    "S13 the gate's check missing on a base with no rule while another workflow succeeded": (dict(NO_RULE, default=("protection-main.json", "rules-main.json"), checks="ready-checks-S13-other-workflow.json", runs="ready-runs-S13-other.json"), DEFAULT_READING, ["security floor: missing", "bridge programs (ubuntu-latest): missing"], []),
    "S15 no run at all": (dict(NO_RULE, checks="ready-checks-S15-none.json", runs="ready-runs-S15-none.json"), RUNS_READING, ["no workflow run succeeded"], []),
    "S16 an earlier success, a later check of the same source pending": (dict(checks="ready-checks-S16-pending.json", runs="ready-runs-S16-pending.json"), BASE_READING, ["security floor: pending"], []),
    "S16 an earlier success, a later check of the same source failed": (dict(checks="ready-checks-S16-failed.json", runs="ready-runs-S16-failed.json"), BASE_READING, ["security floor: failed"], []),
    "S18 a check and a status of one name, the status failed": (dict(status="ready-status-S18-failed.json"), BASE_READING, ["security floor: failed"], []),
    "S19 a push run's failed check beside the pull request run's green one": (dict(checks="ready-checks-S19-push.json", runs="ready-runs-S19-push.json"), BASE_READING, ["security floor: failed"], []),
    "S20 a required context concluded neutral": (dict(checks="ready-checks-S20-neutral.json"), BASE_READING, ["security floor: failed", "stricter than GitHub"], []),
    "S21 a rule naming an app, the check of that name from another app": (dict(APP_RULE, checks="ready-checks-S21-other-app.json"), BASE_READING, ["build: missing"], []),
    "S22 a rule naming an app, a commit status of that name": (dict(APP_RULE, status="ready-status-S22-build.json"), BASE_READING, ["build: missing", "carries no app"], []),
    "S23 a check timed out beside a skipped required context": (dict(checks="ready-checks-S23-timed-out.json"), BASE_READING, ["security floor: "], []),
    "S24 a run failed at its start beside one that succeeded": (dict(NO_RULE, runs="ready-runs-S24-startup.json"), RUNS_READING, ["run lint (pull_request): failed"], []),
    "S25 a replaced run's check still running, its successor's failed": (dict(checks="ready-checks-S25-replaced.json", runs="ready-runs-S25-replaced.json"), BASE_READING, ["security floor: failed"], ["security floor: pending"]),
}


@pytest.mark.parametrize("name", sorted(NOT_READY_CASES))
def test_r083_not_ready_names_each_context_or_run_and_writes_nothing(case, name):
    """enforces: T-CONTEXT, NOT READY (exit 1) names each context or run that is missing, pending or failed; only the latest of
    each source counts (a replaced run's check counts for nothing); failed is the closed list (neutral, timed_out,
    startup_failure among it); a skipped context passes only where no latest check or run failed; a status never holds a context
    the rule names an app for; nothing written and nothing removed."""
    kw, reading, wanted, unwanted = NOT_READY_CASES[name]
    G.put(G.bridge_dir(case.repo) / "ready" / ("99-" + case.head), "{}")
    rc, out = case.run(**kw)
    line = verdict(out, "NOT READY")
    assert rc == 1, out
    assert line.startswith("review-guard: NOT READY - pull request 12, head %s, %s: " % (case.head[:12], reading)), out
    for w in wanted:
        assert w in line, (w, line)
    for w in unwanted:
        assert w not in line, (w, line)
    assert case.ready_records() == ["99-" + case.head], "nothing written, nothing removed: %s" % out


def test_r083_a_list_of_two_pages_whose_second_holds_a_failed_run_is_not_ready(case):
    """enforces: T-CONTEXT, the three lists read to their last page (S12)."""
    runs_path = "repos/OWNER/REPO/actions/runs?head_sha=%s" % case.head
    rc, out = case.run(**dict(NO_RULE, runs="ready-runs-S12-page1.json", pages={runs_path + "#2": "ready-runs-S12-page2.json"}))
    line = verdict(out, "NOT READY")
    assert rc == 1 and "run lint (pull_request): failed" in line, out
    assert case.ready_records() == []


def test_r083_the_head_moved_is_not_ready_and_writes_nothing(case):
    """enforces: T-CONTEXT, NOT READY says that the head moved where GitHub's head and the local one differ (S05)."""
    rc, out = case.run(pull="ready-pull-moved.json")
    line = verdict(out, "NOT READY")
    assert rc == 1, out
    assert line == "review-guard: NOT READY - pull request 12, head %s: the head moved (GitHub's head is 222222222222)" % case.head[:12], out
    assert case.ready_records() == []


def test_r083_ready_reads_the_pull_request_through_the_reader_s_fixed_point(case):
    """enforces: DESIGN, the rule's reader: the pull request's base and head through `repos/<o>/<r>/pulls/<n>`, every call a
    plain GET through `gh api`."""
    rc, out = case.run()
    assert rc == 0, out
    paths = [c[1] for c in case.calls()]
    assert any(p.startswith("repos/{owner}/{repo}/pulls/12") or p.startswith("repos/OWNER/REPO/pulls/12") or "/pulls/12" in p for p in paths), paths
    assert all(c[0] == "api" for c in case.calls())


# ---------------------------------------------------------------- CANNOT CHECK: a stop, never a pass, nothing written


CANNOT_CASES = {
    "S26 the base's rule cannot be read beside a head all green": (dict(prot="protection-unreadable.json"), ["protection", "Resource not accessible"]),
    "the base's rules cannot be read": (dict(rules="rules-unreadable.json"), ["rules", "Resource not accessible"]),
    "the default branch's rule cannot be read where the base names none": (dict(NO_RULE, default=("ready-protection-main-unreadable.json", "rules-main.json")), ["protection", "Resource not accessible"]),
    "the default branch cannot be named where the base names none": (dict(NO_RULE, repo=None), ["repo"]),
    "the pull request cannot be read": (dict(pull=None), ["pull"]),
    "the head's runs cannot be read": (dict(runs=None), ["runs"]),
    "the head's statuses cannot be read": (dict(status=None), ["statuses"]),
}


@pytest.mark.parametrize("name", sorted(CANNOT_CASES))
def test_r083_cannot_check_where_github_a_rule_or_the_pull_request_cannot_be_read(case, name):
    """enforces: T-CONTEXT, CANNOT CHECK (exit 2): a rule consulted that cannot be read is never answered from the runs; the
    source and its reply named; nothing written and nothing removed."""
    kw, words = CANNOT_CASES[name]
    G.put(G.bridge_dir(case.repo) / "ready" / ("12-" + "3" * 40), "{}")
    rc, out = case.run(**kw)
    line = verdict(out, "CANNOT CHECK")
    assert rc == 2, out
    assert line.startswith("review-guard: CANNOT CHECK - pull request 12: "), out
    for w in words:
        assert w in line, (w, line)
    assert "READY - " not in out.replace("NOT READY - ", "").replace("CANNOT CHECK - ", ""), out
    assert case.ready_records() == ["12-" + "3" * 40], "nothing written, nothing removed: %s" % out


def test_r083_no_premerge_record_for_the_local_head_is_cannot_check(case):
    """enforces: T-CONTEXT, the guard's own records are inputs (KP-077): a premerge record of another head is no record for this
    one; an absent one is CANNOT CHECK."""
    os.remove(str(G.bridge_dir(case.repo) / "premerge" / case.head))
    case.premerge("4" * 40)
    rc, out = case.run()
    line = verdict(out, "CANNOT CHECK")
    assert rc == 2 and "premerge" in line, out
    assert case.ready_records() == []


def test_r083_an_unreadable_premerge_folder_is_cannot_check(case):
    """enforces: T-CONTEXT: the premerge record unreadable is CANNOT CHECK, never a pass."""
    folder = G.bridge_dir(case.repo) / "premerge"
    os.remove(str(folder / case.head))
    os.rmdir(str(folder))
    G.put(folder, "not a folder")
    rc, out = case.run()
    assert rc == 2 and "premerge" in verdict(out, "CANNOT CHECK"), out
    assert case.ready_records() == []


# ---------------------------------------------------------------- one head, two pull requests


def test_r083_two_pull_requests_sharing_one_head_are_proven_once_each(case):
    """enforces: T-CONTEXT, the record of another pull request that shares the head proves nothing (S14): one branch opened into
    two bases, one head, is proven once per pull request, each writing its own record and leaving the other's."""
    rc, out = case.run(pr="12")
    assert rc == 0, out
    assert case.ready_records() == ["12-" + case.head]
    rc, out = case.run(pr="13", **dict(NO_RULE, default=("protection-main.json", "rules-main.json")))
    assert rc == 0 and verdict(out, "READY").endswith(DEFAULT_READING), out
    assert case.ready_records() == ["12-" + case.head, "13-" + case.head]


def test_r083_ready_s_answers_are_reached_through_main_and_its_usage_names_ready():
    """enforces: J14: the guard's docstring lists `ready`'s three exits and the record."""
    text = open(G.PROG, encoding="utf-8").read()
    doc = text.split('"""', 2)[1]
    usage = doc.split("\n\n")[1]
    assert "review-guard.py ready <pr>" in usage, usage
    for words in ("READY (exit 0)", "NOT READY (exit 1)", "CANNOT CHECK (exit 2)", "bridge/ready/<pr>-<head>"):
        assert words in doc, words


def test_r083_ready_with_a_number_that_is_not_digits_asks_nothing(case):
    """enforces: T-CONTEXT: a pull request named by no number is CANNOT CHECK and asks GitHub nothing."""
    rc, out = case.run(pr="task-001")
    assert rc == 2 and verdict(out, "CANNOT CHECK"), out
    assert case.calls() == [] and case.ready_records() == []


# ---------------------------------------------------------------- the permission guard: the merge held on the ready record


SHA = "0123456789abcdef0123456789abcdef01234567"
OTHER = "fedcba9876543210fedcba9876543210fedcba98"
FORM = "gh pr merge <n> --squash --match-head-commit <sha>"


def pg(tool, command, cwd):
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto", "cwd": str(cwd)}
    p = subprocess.run([sys.executable, PGUARD], input=json.dumps(payload), capture_output=True, text=True, timeout=120,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stderr


def records_repo(tmp_path, premerge=(SHA,), ready=("12-" + SHA,)):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True, capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for name in premerge:
        G.put(repo / ".git" / "bridge" / "premerge" / name, '{"pr": 12}')
    for name in ready:
        G.put(repo / ".git" / "bridge" / "ready" / name, "{}")
    return repo


TOOLS = ["Bash", "PowerShell"]


@pytest.mark.parametrize("tool", TOOLS)
def test_r083_a_merge_with_both_records_passes(tool, tmp_path):
    """enforces: T-CONTEXT: the guard reads the premerge record by the head and the ready record by the head and the number."""
    repo = records_repo(tmp_path)
    for cmd in ("gh pr merge 12 --squash --match-head-commit " + SHA,
                "gh pr merge 12 --squash --match-head-commit " + SHA[:12],
                "gh pr merge --squash 12 --match-head-commit " + SHA,
                "gh pr merge 12 --subject done --squash --match-head-commit " + SHA):
        rc, err = pg(tool, cmd, repo)
        assert rc == 0, (cmd, err)


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("ready", [(), ("13-" + SHA,), ("12-" + OTHER,)], ids=["no ready record", "another pull request's", "another head's"])
def test_r083_a_merge_without_its_ready_record_is_refused_naming_ready(tool, tmp_path, ready):
    """enforces: T-CONTEXT: refused without the ready record of the pull request and the head the command names, after the
    premerge record's check and in the same way, the message naming `review-guard.py ready <n>`."""
    repo = records_repo(tmp_path, ready=ready)
    rc, err = pg(tool, "gh pr merge 12 --squash --match-head-commit " + SHA, repo)
    assert rc == 2 and "review-guard.py ready 12" in err, err


@pytest.mark.parametrize("tool", TOOLS)
def test_r083_the_ready_record_alone_does_not_pass_the_premerge_check(tool, tmp_path):
    """enforces: T-CONTEXT: the ready record is required beside the premerge record, never in its place."""
    repo = records_repo(tmp_path, premerge=())
    rc, err = pg(tool, "gh pr merge 12 --squash --match-head-commit " + SHA, repo)
    assert rc == 2 and "premerge" in err, err


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("cmd", [
    "gh pr merge --squash --match-head-commit " + SHA,
    "gh pr merge task-083 --squash --match-head-commit " + SHA,
    "gh pr merge --subject 12 --squash --match-head-commit " + SHA,
    "gh pr merge https://github.com/OWNER/REPO/pull/12 --squash --match-head-commit " + SHA,
])
def test_r083_a_merge_that_names_no_number_is_refused_with_the_form(tool, tmp_path, cmd):
    """enforces: T-CONTEXT: a merge that names its pull request by no number (a branch, or nothing) is refused with the form every
    instruction gives; a value of a flag is not the number."""
    repo = records_repo(tmp_path)
    rc, err = pg(tool, cmd, repo)
    assert rc == 2 and FORM in err, (cmd, err)


@pytest.mark.parametrize("tool", TOOLS)
def test_r083_the_guard_s_other_forms_are_unchanged(tool, tmp_path):
    """enforces: TASK-083 Done when: every other refusal and every allowed form unchanged."""
    repo = records_repo(tmp_path, premerge=(), ready=())
    assert pg(tool, "gh pr merge 12 --disable-auto", repo)[0] == 0
    assert pg(tool, "gh pr merge --help", repo)[0] == 0
    rc, err = pg(tool, "gh pr merge 12 --squash --admin --match-head-commit " + SHA, repo)
    assert rc == 2 and "--admin" in err, err
    rc, err = pg(tool, "gh pr merge 12 --squash", repo)
    assert rc == 2 and "--match-head-commit" in err, err


def test_r083_the_guard_s_ready_check_is_its_own_function(monkeypatch):
    """The function `tests/test_allowlist.py` replaces beside `premerge_recorded`: `ready_recorded(pr, sha, cwd)`."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("permission_guard_083", PGUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "premerge_recorded", lambda sha, cwd: True)
    monkeypatch.setattr(mod, "ready_recorded", lambda pr, sha, cwd: (pr, sha) == ("12", SHA))
    assert mod.check("gh pr merge 12 --squash --match-head-commit " + SHA, None) is None
    assert "review-guard.py ready 13" in (mod.check("gh pr merge 13 --squash --match-head-commit " + SHA, None) or "")


# ---------------------------------------------------------------- premerge-records <pr>: the same check, both records or neither


def records_case(tmp_path, monkeypatch, capsys, kw):
    repo = G.make_repo(tmp_path)
    G.git(repo, "update-ref", "refs/remotes/origin/main", "main")
    G.put(repo / "docs" / "PROJECT_STATUS.md", "Phase: building\n")
    G.git(repo, "add", "-A")
    G.git(repo, "commit", "-q", "-m", "records")
    head = G.git(repo, "rev-parse", "HEAD")
    base = G.git(repo, "rev-parse", "refs/remotes/origin/main")
    guard = load_guard(monkeypatch)
    monkeypatch.setattr(guard, "PR_HEAD_WAIT", 0)
    monkeypatch.setattr(guard, "pr_state", lambda pr, root: ({"head": head, "base": base, "into": "main", "files": ["docs/PROJECT_STATUS.md"]}, None))
    use_standin(guard.bridge_env, monkeypatch, tmp_path, routes(head, **kw), head)
    monkeypatch.chdir(str(repo))
    capsys.readouterr()
    rc = guard.cmd_premerge_records(str(repo), "12")
    out = capsys.readouterr().out
    folder = G.bridge_dir(repo)
    written = sorted(os.path.relpath(os.path.join(d, f), str(folder)).replace("\\", "/") for d, _, files in os.walk(str(folder)) for f in files)
    return rc, out, head, written


def test_r083_premerge_records_proves_ci_and_writes_both_records(tmp_path, monkeypatch, capsys):
    """enforces: T-CONTEXT: `premerge-records <pr>` makes the same check and writes both records; its OK line and the auto-merge
    line stay."""
    rc, out, head, written = records_case(tmp_path, monkeypatch, capsys, {})
    assert rc == 0 and "OK - records only" in out, out
    assert verdict(out, "READY") == "review-guard: READY - pull request 12, head %s, %s" % (head[:12], BASE_READING), out
    assert [w for w in written if w.startswith(("premerge/", "ready/"))] == ["premerge/" + head, "ready/12-" + head], written
    assert out.rstrip().splitlines()[-1] == "auto-merge is off for this repository", out


@pytest.mark.parametrize("kw,word,code", [
    (dict(checks="ready-checks-S04-failed.json", runs="ready-runs-S04-failed.json"), "NOT READY", 1),
    (dict(prot="protection-unreadable.json"), "CANNOT CHECK", 2),
], ids=["not ready", "cannot check"])
def test_r083_premerge_records_writes_neither_record_where_ci_is_not_proven(tmp_path, monkeypatch, capsys, kw, word, code):
    """enforces: T-CONTEXT: both records or neither."""
    rc, out, head, written = records_case(tmp_path, monkeypatch, capsys, kw)
    assert rc == code and verdict(out, word), out
    assert [w for w in written if w.startswith(("premerge/", "ready/"))] == [], written
