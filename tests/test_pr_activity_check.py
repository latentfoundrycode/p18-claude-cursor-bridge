"""pr-activity-check.py with gh replaced by canned answers: the owner's own post is flagged,
the supervisor's task-branch pushes are not, a naive timestamp is refused, an API error is
'cannot verify'."""
import json

import pytest


@pytest.fixture
def pac(program):
    return program("pr-activity-check")


def fake_gh(answers):
    """answers: {substring of the args -> stdout string}; anything else is an error."""
    def gh(args):
        joined = " ".join(args)
        for key, out in answers.items():
            if key in joined:
                return out, ""
        return None, "no canned answer for " + joined
    return gh


BASE = {
    "api user --jq": "latentfoundrycode\n",
    "repo view": "o/r\n",
    "issues/12/comments": "[]",
    "pulls/12/reviews": "[]",
    "pulls/12/comments": "[]",
    "users/latentfoundrycode/events": "[]",
}


def run(pac, monkeypatch, answers, *argv):
    monkeypatch.setattr(pac, "gh", fake_gh(answers))
    monkeypatch.setattr(pac.sys, "argv", ["pr-activity-check.py"] + list(argv))
    return pac.main()


def test_clean_window_is_ok(pac, monkeypatch, capsys):
    assert run(pac, monkeypatch, BASE, "12", "--since", "2026-10-04T12:00:00Z") == 0
    assert capsys.readouterr().out.startswith("OK:")


def test_naive_timestamp_is_refused(pac, monkeypatch, capsys):
    assert run(pac, monkeypatch, BASE, "12", "--since", "2026-10-04T12:00:00") == 2
    assert "no time zone" in capsys.readouterr().out


def test_the_owners_comment_on_the_pull_request_is_flagged(pac, monkeypatch, capsys):
    answers = dict(BASE)
    answers["issues/12/comments"] = json.dumps([
        {"user": {"login": "latentfoundrycode"}, "created_at": "2026-10-04T12:05:00Z", "body": "## Review B - APPROVE"},
        {"user": {"login": "someone-else"}, "created_at": "2026-10-04T12:06:00Z", "body": "lgtm"},
        {"user": {"login": "latentfoundrycode"}, "created_at": "2026-10-04T11:00:00Z", "body": "before the window"},
    ])
    assert run(pac, monkeypatch, answers, "12", "--since", "2026-10-04T12:00:00Z") == 1
    out = capsys.readouterr().out
    assert "GATE-INTEGRITY: 1 item" in out and "Review B - APPROVE" in out and "before the window" not in out


def test_agent_like_events_elsewhere_in_the_repo_are_flagged_but_task_pushes_are_not(pac, monkeypatch, capsys):
    answers = dict(BASE)
    answers["users/latentfoundrycode/events"] = json.dumps([
        {"type": "PushEvent", "created_at": "2026-10-04T12:10:00Z", "repo": {"name": "o/r"}, "payload": {"ref": "refs/heads/task-013", "commits": [{}]}},
        {"type": "IssueCommentEvent", "created_at": "2026-10-04T12:11:00Z", "repo": {"name": "o/r"}, "payload": {"action": "created", "issue": {"number": 9}}},
        {"type": "IssueCommentEvent", "created_at": "2026-10-04T12:12:00Z", "repo": {"name": "o/other"}, "payload": {"action": "created", "issue": {"number": 3}}},
        {"type": "PushEvent", "created_at": "2026-10-04T12:13:00Z", "repo": {"name": "o/r"}, "payload": {"ref": "refs/heads/main", "commits": []}},
        {"type": "PushEvent", "created_at": "2026-10-04T11:00:00Z", "repo": {"name": "o/r"}, "payload": {"ref": "refs/heads/main", "commits": []}},
    ])
    assert run(pac, monkeypatch, answers, "12", "--since", "2026-10-04T12:00:00Z") == 1
    out = capsys.readouterr().out
    assert "2 event(s)" in out and "created on #9" in out and "push to main" in out
    assert "task-013" not in out and "o/other" not in out


def test_api_error_is_cannot_verify(pac, monkeypatch, capsys):
    answers = {k: v for k, v in BASE.items() if "events" not in k}
    assert run(pac, monkeypatch, answers, "12", "--since", "2026-10-04T12:00:00Z") == 2
    assert "CANNOT VERIFY" in capsys.readouterr().out
    assert run(pac, monkeypatch, {"api user --jq": ""}, "12", "--since", "2026-10-04T12:00:00Z") == 2
