"""TASK-064's acceptance tests, the supervisor's (R-083, R-084; D-002): the one reading of a repository's branch rule, of its
auto-merge setting and default branch, of a pull request's base and head and of a head's checks, commit statuses and workflow
runs, in `bridge_env.py`; the line `premerge` and `premerge-records` print after the verdict; the closing word of `verify` and
`premerge` for a snapshot deleted or rewritten. The builder reads and runs these tests and never edits them.

Every case runs on GitHub's replies recorded once from this repository before the brief (tests/fixtures/github/, each file's
`fixture` field saying captured or built, and a built one naming the captured reply it was made from), answered by a stand-in
`gh`: `bridge_env.GH_COMMAND`, the one command list every call starts, is set to this interpreter and the stand-in program the
test writes, whose first argument is the case's routing file. The stand-in answers a GET (`gh api <path>`, no method other than
GET, no field, no input, no `--paginate`) by the path, its query (`per_page` aside, `page` 1 by default) and the owner and the
repository read as placeholders; it logs every call; a path it has no answer for is GitHub's 404."""
import json
import os
import sys
import time

import pytest

import test_task032_supervisor_guard as G
from test_bug039 import load_guard

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures", "github")
SHA = "1111111111111111111111111111111111111111"
PROT_MAIN = "repos/OWNER/REPO/branches/main/protection/required_status_checks"
RULES_MAIN = "repos/OWNER/REPO/rules/branches/main"
PROT_REL = "repos/OWNER/REPO/branches/release%2F2026.11.03/protection/required_status_checks"
RULES_REL = "repos/OWNER/REPO/rules/branches/release%2F2026.11.03"
CHECKS = "repos/OWNER/REPO/commits/%s/check-runs?filter=all" % SHA
STATUS = "repos/OWNER/REPO/commits/%s/status" % SHA
RUNS = "repos/OWNER/REPO/actions/runs?head_sha=%s" % SHA

STANDIN = r'''
import json, os, sys, time
from urllib.parse import parse_qsl
config = json.load(open(sys.argv[1], encoding="utf-8"))
args = sys.argv[2:]
with open(config["log"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(args) + "\n")
def refuse(why):
    sys.stderr.write("standin: " + why + "\n")
    sys.exit(99)
if not args or args[0] != "api":
    refuse("not gh api")
path = None
i = 1
while i < len(args):
    a = args[i]
    if a in ("-X", "--method"):
        if i + 1 >= len(args) or args[i + 1].upper() != "GET":
            refuse("not a GET")
        i += 2
        continue
    if a.startswith("--method=") and a.split("=", 1)[1].upper() != "GET":
        refuse("not a GET")
    if a in ("-f", "-F", "--field", "--raw-field", "--input", "--paginate") or a.startswith(("-f", "-F", "--field=", "--raw-field=", "--input=")):
        refuse("not a plain GET: " + a)
    if a in ("-H", "--header", "-q", "--jq", "-t", "--template", "--hostname", "--cache"):
        i += 2
        continue
    if not a.startswith("-") and path is None:
        path = a
    i += 1
if path is None:
    refuse("no path")
path = path.lstrip("/")
base, _, query = path.partition("?")
parts = base.split("/")
if len(parts) >= 3 and parts[0] == "repos":
    parts[1], parts[2] = "OWNER", "REPO"
base = "/".join(parts)
params = [(k, v) for k, v in parse_qsl(query, keep_blank_values=True) if k not in ("per_page", "page")]
page = dict(parse_qsl(query)).get("page", "1")
key = base + ("?" + "&".join("%s=%s" % kv for kv in sorted(params)) if params else "") + "#" + page
time.sleep(config.get("sleep", 0))
name = config["routes"].get(key)
if name is None:
    sys.stdout.write(json.dumps({"message": "Not Found", "status": "404"}))
    sys.stderr.write("gh: Not Found (HTTP 404)\n")
    sys.exit(1)
doc = json.load(open(os.path.join(config["fixtures"], name), encoding="utf-8"))
sys.stdout.write(json.dumps(doc["body"]))
if doc["gh_stderr"]:
    sys.stderr.write(doc["gh_stderr"] + "\n")
sys.exit(doc["gh_exit"])
'''


@pytest.fixture
def be(monkeypatch):
    """bridge_env as the installed programs import it."""
    monkeypatch.syspath_prepend(os.path.dirname(G.PROG))
    import bridge_env
    return bridge_env


@pytest.fixture
def github(tmp_path, monkeypatch, be):
    """github({route: fixture file}, sleep=0): every gh call of bridge_env answered by the stand-in from those routes; returns the
    call log reader. A route is a path with OWNER/REPO, its query sorted (per_page aside) and '#<page>' (bare: page 1)."""
    standin = tmp_path / "standin_gh.py"
    standin.write_text(STANDIN, encoding="utf-8")
    log = tmp_path / "gh-calls.jsonl"

    def setup(routes, sleep=0, command=None):
        full = {}
        for k, v in routes.items():
            full[k if "#" in k else k + "#1"] = v
        cfg = tmp_path / "routes.json"
        cfg.write_text(json.dumps({"routes": full, "fixtures": FIXTURES, "log": str(log), "sleep": sleep}), encoding="utf-8")
        if log.exists():
            log.unlink()
        monkeypatch.setattr(be, "GH_COMMAND", command or [sys.executable, str(standin), str(cfg)])

    def calls():
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]

    setup.calls = calls
    return setup


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return json.load(fh)


def contexts(result):
    return sorted((c["context"], c.get("app_id")) for c in result["contexts"])


# ---------------------------------------------------------------- the recorded replies themselves


def test_every_fixture_says_how_it_was_made_and_holds_no_account(be):
    """tests/fixtures/github/: each file captured or built, a built one naming its captured source, the owner and the repository
    as placeholders, no token-shaped string."""
    names = sorted(n for n in os.listdir(FIXTURES) if n.endswith(".json"))
    assert len(names) >= 20, names
    for n in names:
        doc = fixture(n)
        text = json.dumps(doc)
        assert doc["fixture"] in ("captured", "built"), n
        if doc["fixture"] == "built":
            assert "from the captured" in doc["note"], n
        assert "latentfoundrycode" not in text and "p18-claude-cursor-bridge" not in text, n
        assert "ghp_" not in text and "github_pat_" not in text and "gho_" not in text, n
        assert doc["request"].startswith("repos/OWNER/REPO"), n


# ---------------------------------------------------------------- the branch rule: value, none, cannot read


def test_r083_main_reads_its_classic_contexts_each_with_its_app(be, github):
    github({PROT_MAIN: "protection-main.json", RULES_MAIN: "rules-main.json"})
    r = be.branch_rule("OWNER/REPO", "main")
    assert r["answer"] == be.ANSWER_VALUE == "value", r
    assert contexts(r) == [("bridge programs (ubuntu-latest)", 15368), ("bridge programs (windows-latest)", 15368), ("security floor", 15368)], r


def test_r083_a_branch_with_no_protection_and_no_rule_is_none_and_its_name_is_encoded(be, github):
    """The captured reply for this repository's release branch, a 404 matched exactly by its status and its message; the slash
    in the branch's name percent-encoded in both paths (a raw slash reaches no route here: GitHub's own 404)."""
    github({PROT_REL: "protection-release-none.json", RULES_REL: "rules-release.json"})
    r = be.branch_rule("OWNER/REPO", "release/2026.11.03")
    assert r["answer"] == be.ANSWER_NONE == "none" and r["contexts"] == [], r
    paths = [c[c.index("api") + 1] for c in github.calls()]
    assert any("release%2F2026.11.03/protection" in p for p in paths) and any("rules/branches/release%2F2026.11.03" in p for p in paths), paths
    assert not any("release/2026.11.03" in p for p in paths), paths


def test_r083_a_rule_that_applies_to_the_branch_names_its_contexts_with_its_app(be, github):
    github({PROT_MAIN: "protection-release-none.json", RULES_MAIN: "rules-app.json"})
    r = be.branch_rule("OWNER/REPO", "main")
    assert r["answer"] == "value" and contexts(r) == [("build", 15368)], r


def test_r083_the_two_sources_are_united(be, github):
    github({PROT_MAIN: "protection-main.json", RULES_MAIN: "rules-app-lint.json"})
    r = be.branch_rule("OWNER/REPO", "main")
    names = sorted(c["context"] for c in r["contexts"])
    assert r["answer"] == "value" and names == ["bridge programs (ubuntu-latest)", "bridge programs (windows-latest)", "lint", "security floor"], r
    lint = [c for c in r["contexts"] if c["context"] == "lint"]
    assert lint[0].get("app_id") is None, "a rule that names no app: the context carries none"


@pytest.mark.parametrize("prot,rules", [
    ("protection-empty.json", "rules-main.json"),
    ("protection-release-none.json", "rules-other-type.json"),
    ("protection-empty.json", "rules-other-type.json"),
])
def test_r083_a_success_that_names_no_required_check_is_none(be, github, prot, rules):
    github({PROT_MAIN: prot, RULES_MAIN: rules})
    r = be.branch_rule("OWNER/REPO", "main")
    assert r["answer"] == "none" and r["contexts"] == [], r


@pytest.mark.parametrize("prot,rules,source", [
    ("protection-main.json", "rules-unreadable.json", "rules"),
    ("protection-unreadable.json", "rules-main.json", "protection"),
    ("protection-unreadable.json", "rules-app.json", "protection"),
    ("protection-not-enabled.json", "rules-main.json", "protection"),
    ("not-found.json", "rules-main.json", "protection"),
])
def test_r083_a_reply_that_is_not_a_success_is_cannot_read_whatever_the_other_source_names(be, github, prot, rules, source):
    """A refusal, the reply of its own for a protected branch without required checks, no access: cannot read with the reason
    and the source, never none, and never hidden by the contexts the other source names."""
    github({PROT_MAIN: prot, RULES_MAIN: rules})
    r = be.branch_rule("OWNER/REPO", "main")
    assert r["answer"] == be.ANSWER_CANNOT == "cannot read", r
    assert source in r["source"], r
    assert r["reason"], r


def test_r083_gh_absent_and_a_reply_past_the_time_limit_are_cannot_read(be, github, monkeypatch):
    github({}, command=["no-such-gh-%d" % os.getpid()])
    r = be.branch_rule("OWNER/REPO", "main")
    assert r["answer"] == "cannot read" and r["reason"], r
    github({PROT_MAIN: "protection-main.json", RULES_MAIN: "rules-main.json"}, sleep=6)
    monkeypatch.setattr(be, "GH_API_TIMEOUT", 1)
    start = time.monotonic()
    r = be.branch_rule("OWNER/REPO", "main")
    assert r["answer"] == "cannot read", r
    assert time.monotonic() - start < 5, "each call ends at the stated time limit"


def test_r083_every_call_is_one_plain_get_with_no_retry(be, github):
    """The stand-in refuses anything but a GET (exit 99); a refusal is read once, never asked again."""
    github({PROT_MAIN: "protection-unreadable.json", RULES_MAIN: "rules-main.json"})
    be.branch_rule("OWNER/REPO", "main")
    calls = github.calls()
    paths = [c[c.index("api") + 1].lstrip("/") for c in calls]
    assert all(c[0] == "api" for c in calls), calls
    assert sum(1 for p in paths if "protection/required_status_checks" in p) == 1, calls
    assert sum(1 for p in paths if "/rules/branches/" in p) <= 1, calls


# ---------------------------------------------------------------- the repository, the pull request


def test_r084_the_repository_s_auto_merge_setting_and_default_branch(be, github):
    github({"repos/OWNER/REPO": "repo.json"})
    r = be.repo_settings("OWNER/REPO")
    assert r["answer"] == "value" and r["allow_auto_merge"] is False and r["default_branch"] == "main", r
    github({"repos/OWNER/REPO": "repo-on.json"})
    assert be.repo_settings("OWNER/REPO")["allow_auto_merge"] is True
    github({"repos/OWNER/REPO": "not-found.json"})
    r = be.repo_settings("OWNER/REPO")
    assert r["answer"] == "cannot read" and r["reason"], r


def test_r083_a_pull_request_s_base_and_head(be, github):
    github({"repos/OWNER/REPO/pulls/173": "pull.json"})
    r = be.pull_refs("OWNER/REPO", 173)
    assert r["answer"] == "value" and r["base"] == "main" and r["head"] == SHA, r
    github({})
    assert be.pull_refs("OWNER/REPO", 173)["answer"] == "cannot read"


# ---------------------------------------------------------------- a head's state, page by page


def test_r083_a_head_s_checks_statuses_and_runs_on_the_recorded_replies(be, github):
    github({CHECKS: "check-runs.json", STATUS: "status.json", RUNS: "runs.json"})
    r = be.head_state("OWNER/REPO", SHA)
    assert r["answer"] == "value", r
    assert len(r["checks"]) == 5 and r["statuses"] == [] and len(r["runs"]) == 1, r
    assert any("filter=all" in c[c.index("api") + 1] for c in github.calls()), "the check runs are asked with filter=all"


def test_r083_a_list_is_read_page_by_page_to_the_count_its_reply_states(be, github):
    github({CHECKS + "#1": "check-runs-two-page1.json", CHECKS + "#2": "check-runs-two-page2.json", STATUS: "status-one.json", RUNS: "runs.json"})
    r = be.head_state("OWNER/REPO", SHA)
    assert r["answer"] == "value" and len(r["checks"]) == 2 and len(r["statuses"]) == 1, r
    assert len({c["id"] for c in r["checks"]}) == 2, r


@pytest.mark.parametrize("second", [None, "check-runs-page2.json"])
def test_r083_a_list_not_read_whole_is_cannot_read_never_a_shorter_list(be, github, second):
    """Page 2 missing; or every page read and the entries fewer than the count the reply states (5 stated, 2 given)."""
    routes = {CHECKS + "#1": "check-runs-page1.json", STATUS: "status.json", RUNS: "runs.json"}
    if second:
        routes[CHECKS + "#2"] = second
    github(routes)
    r = be.head_state("OWNER/REPO", SHA)
    assert r["answer"] == "cannot read" and r["reason"], r


def test_r083_a_head_whose_source_cannot_be_read_is_cannot_read(be, github):
    github({CHECKS: "check-runs.json", STATUS: "not-found.json", RUNS: "runs.json"})
    assert be.head_state("OWNER/REPO", SHA)["answer"] == "cannot read"


# ---------------------------------------------------------------- the latest of each source


def run(rid, number, attempt, suite, event="pull_request", workflow=374570417, status="completed", conclusion="success"):
    return {"id": rid, "name": "tests", "workflow_id": workflow, "event": event, "run_number": number, "run_attempt": attempt,
            "status": status, "conclusion": conclusion, "check_suite_id": suite, "head_sha": SHA}


def check(cid, name, suite, started="2026-11-16T10:51:42Z", status="completed", conclusion="success", app=15368, slug="github-actions"):
    return {"id": cid, "name": name, "status": status, "conclusion": conclusion, "started_at": started, "completed_at": None,
            "head_sha": SHA, "check_suite": {"id": suite}, "app": {"id": app, "slug": slug}}


def test_r083_a_run_attempted_again_keeps_its_latest_attempt_and_only_its_checks(be):
    runs = [run(1, 801, 1, 100, conclusion="failure"), run(2, 801, 2, 200)]
    checks = [check(11, "security floor", 100, conclusion="failure"), check(12, "security floor", 200)]
    kept = be.latest_of_each({"checks": checks, "statuses": [], "runs": runs})
    assert [r["id"] for r in kept["runs"]] == [2], kept
    assert [c["id"] for c in kept["checks"]] == [12], "a check of a replaced run is not counted"


def test_r083_a_later_run_number_wins_and_two_events_are_two_sources(be):
    runs = [run(1, 800, 1, 100), run(2, 801, 1, 200), run(3, 5, 1, 300, event="push")]
    kept = be.latest_of_each({"checks": [], "statuses": [], "runs": runs})
    assert sorted(r["id"] for r in kept["runs"]) == [2, 3], kept


def test_r083_checks_no_run_made_are_kept_by_name_and_app_the_pending_after_the_completed(be):
    socket = dict(app=156372, slug="socket-security")
    checks = [check(21, "Socket Security: Project Report", 900, started="2026-11-16T10:00:00Z", **socket),
              check(22, "Socket Security: Project Report", 901, started="2026-11-16T10:30:00Z", conclusion="failure", **socket),
              check(23, "Socket Security: Project Report", 902, started="2026-11-16T09:00:00Z", status="in_progress", conclusion=None, **socket),
              check(24, "Socket Security: Project Report", 903, started="2026-11-16T11:00:00Z", app=1, slug="other")]
    kept = be.latest_of_each({"checks": checks, "statuses": [], "runs": []})
    ids = sorted(c["id"] for c in kept["checks"])
    assert ids == [23, 24], "of one name and app the pending one ranks after every completed one; another app is its own source"


def test_r083_of_several_checks_of_one_name_in_a_latest_run_the_last_is_kept(be):
    runs = [run(1, 801, 1, 100)]
    checks = [check(31, "security floor", 100, started="2026-11-16T10:00:00Z", conclusion="failure"),
              check(32, "security floor", 100, started="2026-11-16T10:05:00Z"),
              check(33, "security floor", 100, started=None)]
    kept = be.latest_of_each({"checks": checks, "statuses": [], "runs": runs})
    assert [c["id"] for c in kept["checks"]] == [33], "one carries no start time: ordered by id alone"
    checks = [check(41, "security floor", 100, started="2026-11-16T10:05:00Z"),
              check(40, "security floor", 100, started="2026-11-16T10:00:00Z", conclusion="failure")]
    kept = be.latest_of_each({"checks": checks, "statuses": [], "runs": runs})
    assert [c["id"] for c in kept["checks"]] == [41], "the completed ordered by started_at then id"
    checks = [check(51, "security floor", 100, started="2026-11-16T10:05:00Z"),
              check(50, "security floor", 100, started="2026-11-16T10:10:00Z", conclusion="failure")]
    kept = be.latest_of_each({"checks": checks, "statuses": [], "runs": runs})
    assert [c["id"] for c in kept["checks"]] == [50], "the later start wins over the higher id"


def test_r083_a_status_is_kept_by_its_context_the_latest_by_its_update(be):
    statuses = [{"id": 1, "context": "ci/legacy", "state": "failure", "updated_at": "2026-11-16T10:00:00Z"},
                {"id": 2, "context": "ci/legacy", "state": "success", "updated_at": "2026-11-16T10:10:00Z"},
                {"id": 3, "context": "ci/other", "state": "pending", "updated_at": "2026-11-16T09:00:00Z"}]
    kept = be.latest_of_each({"checks": [], "statuses": statuses, "runs": []})
    assert sorted(s["id"] for s in kept["statuses"]) == [2, 3], kept


def test_r083_the_captured_head_keeps_every_entry(be, github):
    github({CHECKS: "check-runs.json", STATUS: "status.json", RUNS: "runs.json"})
    kept = be.latest_of_each(be.head_state("OWNER/REPO", SHA))
    assert len(kept["checks"]) == 5 and len(kept["runs"]) == 1 and kept["statuses"] == [], kept


# ---------------------------------------------------------------- passed, pending, skipped, failed


@pytest.mark.parametrize("kind,item,want", [
    ("check", {"status": "completed", "conclusion": "success"}, "passed"),
    ("run", {"status": "completed", "conclusion": "success"}, "passed"),
    ("status", {"state": "success"}, "passed"),
    ("check", {"status": "in_progress", "conclusion": None}, "pending"),
    ("check", {"status": "queued", "conclusion": None}, "pending"),
    ("run", {"status": "queued", "conclusion": None}, "pending"),
    ("status", {"state": "pending"}, "pending"),
    ("check", {"status": "completed", "conclusion": "skipped"}, "skipped"),
    ("run", {"status": "completed", "conclusion": "skipped"}, "skipped"),
    ("check", {"status": "completed", "conclusion": "timed_out"}, "failed"),
    ("check", {"status": "completed", "conclusion": "neutral"}, "failed"),
    ("check", {"status": "completed", "conclusion": "cancelled"}, "failed"),
    ("check", {"status": "completed", "conclusion": "action_required"}, "failed"),
    ("check", {"status": "completed", "conclusion": "a-conclusion-not-known"}, "failed"),
    ("run", {"status": "completed", "conclusion": "failure"}, "failed"),
    ("status", {"state": "failure"}, "failed"),
    ("status", {"state": "error"}, "failed"),
    ("status", {"state": "a-state-not-known"}, "failed"),
])
def test_r083_each_entry_is_passed_pending_skipped_or_failed_by_the_closed_lists(be, kind, item, want):
    assert be.ci_class(item, kind) == want


# ---------------------------------------------------------------- the line after premerge's verdict


@pytest.mark.parametrize("fixture_name,line", [
    ("repo.json", "auto-merge is off for this repository"),
    ("repo-on.json", "auto-merge is on for this repository"),
    (None, "auto-merge setting not read"),
])
def test_r084_premerge_prints_the_repository_s_auto_merge_setting_after_its_verdict(tmp_path, monkeypatch, capsys, fixture_name, line):
    """After the record is written; the verdict and the exit code unchanged; no armed form."""
    repo = G.make_repo(tmp_path)
    G.reviewed(repo, "TASK-001", change=False)
    guard = load_guard(monkeypatch)
    standin = tmp_path / "standin_gh.py"
    standin.write_text(STANDIN, encoding="utf-8")
    cfg = tmp_path / "routes.json"
    routes = {"repos/OWNER/REPO#1": fixture_name} if fixture_name else {}
    cfg.write_text(json.dumps({"routes": routes, "fixtures": FIXTURES, "log": str(tmp_path / "log.jsonl")}), encoding="utf-8")
    monkeypatch.setattr(guard.bridge_env, "GH_COMMAND", [sys.executable, str(standin), str(cfg)])
    monkeypatch.chdir(str(repo))
    monkeypatch.setattr(sys, "argv", ["review-guard.py", "premerge", "TASK-001"])
    assert guard.main() == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert line in lines, out
    ok = [i for i, l in enumerate(lines) if l.startswith("review-guard: OK")]
    assert ok and lines.index(line) > ok[-1], "the line follows the verdict"
    assert os.listdir(str(G.bridge_dir(repo) / "premerge")), "the record is written"
    assert "--auto" not in out, out


def test_r084_premerge_records_prints_the_line_after_its_verdict_too(tmp_path, monkeypatch, capsys):
    """A records-only pull request (GitHub's list replaced in-process, as release S's tests replace it): the record written,
    exit 0, the setting's line last."""
    repo = G.make_repo(tmp_path)
    G.git(repo, "update-ref", "refs/remotes/origin/main", "main")
    G.put(repo / "docs" / "PROJECT_STATUS.md", "Phase: building\n")
    G.git(repo, "add", "-A")
    G.git(repo, "commit", "-q", "-m", "records")
    head = G.git(repo, "rev-parse", "HEAD")
    base = G.git(repo, "rev-parse", "refs/remotes/origin/main")
    guard = load_guard(monkeypatch)
    monkeypatch.setattr(guard, "pr_state", lambda pr, root: ({"head": head, "base": base, "into": "main", "files": ["docs/PROJECT_STATUS.md"]}, None))
    standin = tmp_path / "standin_gh.py"
    standin.write_text(STANDIN, encoding="utf-8")
    cfg = tmp_path / "routes.json"
    cfg.write_text(json.dumps({"routes": {"repos/OWNER/REPO#1": "repo.json"}, "fixtures": FIXTURES, "log": str(tmp_path / "log.jsonl")}), encoding="utf-8")
    monkeypatch.setattr(guard.bridge_env, "GH_COMMAND", [sys.executable, str(standin), str(cfg)])
    monkeypatch.chdir(str(repo))
    rc = guard.cmd_premerge_records(str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 0 and "OK - records only" in out, out
    assert os.listdir(str(G.bridge_dir(repo) / "premerge")) == [head], out
    assert out.rstrip().splitlines()[-1] == "auto-merge is off for this repository", out
    assert "--auto" not in out, out


# ---------------------------------------------------------------- the closing word: deleted or rewritten


def _snapshot(repo, name):
    return G.bridge_dir(repo) / ("review-%s.json" % name)


def _gate_line(out):
    hits = [l for l in out.splitlines() if l.startswith("review-guard: GATE-INTEGRITY -")]
    assert hits, out
    return hits[-1]


def test_r084_verify_s_closing_line_says_deleted_where_the_snapshot_was_deleted(tmp_path):
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, "TASK-001")
    G.launched(repo, "TASK-001")
    os.remove(str(_snapshot(repo, "TASK-001")))
    rc, out = G.guard(repo, "verify", "TASK-001")
    line = _gate_line(out)
    assert rc == 1 and "deleted after it was taken" in line and "rewritten" not in line, out


def test_r084_verify_s_closing_line_says_rewritten_where_the_snapshot_was_rewritten(tmp_path):
    repo = G.make_repo(tmp_path)
    G.snap_ok(repo, "TASK-001")
    G.launched(repo, "TASK-001")
    p = _snapshot(repo, "TASK-001")
    data = json.loads(p.read_text(encoding="utf-8"))
    data["head"] = "0" * 40
    p.write_text(json.dumps(data), encoding="utf-8")
    rc, out = G.guard(repo, "verify", "TASK-001")
    line = _gate_line(out)
    assert rc == 1 and "rewritten after it was taken" in line and "deleted" not in line, out


def test_r084_premerge_s_closing_line_says_deleted_or_rewritten(tmp_path):
    repo = G.make_repo(tmp_path, name="ws1")
    G.reviewed(repo, "TASK-001", change=False)
    os.remove(str(_snapshot(repo, "TASK-001")))
    rc, out = G.guard(repo, "premerge", "TASK-001")
    line = _gate_line(out)
    assert rc == 1 and "deleted after it was taken" in line and "rewritten" not in line, out
    repo2 = G.make_repo(tmp_path, name="ws2")
    G.reviewed(repo2, "TASK-001", change=False)
    p = _snapshot(repo2, "TASK-001")
    data = json.loads(p.read_text(encoding="utf-8"))
    data["head"] = "0" * 40
    p.write_text(json.dumps(data), encoding="utf-8")
    rc, out = G.guard(repo2, "premerge", "TASK-001")
    line = _gate_line(out)
    assert rc == 1 and "rewritten after it was taken" in line and "deleted" not in line, out
