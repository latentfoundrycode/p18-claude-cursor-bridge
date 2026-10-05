#!/usr/bin/env python3
"""pr-activity-check: prove that nobody wrote to a pull request as the owner during a run.

  python ~/.claude/cursor-bridge/pr-activity-check.py <pr-number> --since <ISO-8601 UTC> [--repo owner/name]

Why (KP-032): the cross-family reviewer and the builder run as `cursor-agent` processes on
the owner's machine. Before release 2026.10.04a they inherited the owner's GitHub login, and
a reviewer twice posted its verdict on a pull request under the owner's name. The shim and
bridge-run.py now withhold that login; this check is the proof, run after every Review B
and before every merge: it lists every comment, review and review comment on the pull
request created at or after --since and flags any written by the account `gh` is logged
in as (the owner); it then reads the owner's own GitHub events since --since and flags, in
the same repository, what an agent would do and a supervisor would not during a review: a
comment or review on any other pull request or issue, a merge, a push straight to main.
The supervisor's own pushes to task branches and its opening of pull requests, which go on
while a review runs, are not flagged. A read-only check: `gh api` GET calls only.

--since must carry a time zone (`2026-10-04T13:14:33Z`): the launcher prints exactly that
as its first stderr line, `bridge-run: started <time>Z`. A timestamp without a zone is
refused, because a local time read as UTC would open the window hours late (fail open).

Exit 0 = nothing written as the owner since --since; 1 = GATE-INTEGRITY, something was;
2 = cannot verify (gh not logged in, API error, bad timestamp) - never treat as clean.
What it cannot see: edits to an older comment, a change of title or body, a label; the
identity withheld from the agents (KP-032) is what stops those, this check is the proof
for the likely cases, not a boundary.
ASCII-only on purpose (cp1252 consoles).
"""
import datetime
import json
import os
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def gh(args):
    try:
        p = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=60, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)
    if p.returncode != 0:
        return None, (p.stderr or p.stdout).strip()[:300]
    return p.stdout, ""


def parse_ts(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def events_since(owner, since, repo):
    """What an agent, not a supervisor, would do as the owner in `repo` since `since`."""
    found, errors = [], []
    for page in (1, 2, 3):
        out, err = gh(["api", "users/%s/events?per_page=100&page=%d" % (owner, page)])
        if out is None:
            errors.append(err)
            break
        try:
            items = json.loads(out)
        except ValueError:
            errors.append("unreadable events page %d" % page)
            break
        if not items:
            break
        older = False
        for it in items:
            ts = parse_ts(str(it.get("created_at") or ""))
            if ts is None:
                continue
            if ts < since:
                older = True
                continue
            kind = it.get("type") or ""
            where = (it.get("repo") or {}).get("name") or "?"
            if where.lower() != repo.lower():
                continue
            payload = it.get("payload") or {}
            detail = None
            if kind in ("IssueCommentEvent", "PullRequestReviewEvent", "PullRequestReviewCommentEvent", "CommitCommentEvent", "IssuesEvent"):
                detail = "%s on #%s" % (payload.get("action") or "", ((payload.get("issue") or payload.get("pull_request") or {}).get("number") or "?"))
            elif kind == "PullRequestEvent" and payload.get("action") == "closed" and (payload.get("pull_request") or {}).get("merged"):
                detail = "merged #%s" % ((payload.get("pull_request") or {}).get("number") or "?")
            elif kind == "PushEvent" and (payload.get("ref") or "").endswith("/main"):
                detail = "a merge or a push to main (%d commit(s))" % len(payload.get("commits") or [])
            if detail:
                found.append((kind, it.get("created_at"), where, detail))
        if older:
            break
    return found, errors


def main():
    argv = sys.argv[1:]
    if not argv or "--since" not in argv:
        print("usage: pr-activity-check.py <pr-number> --since <ISO-8601 UTC> [--repo owner/name]")
        return 2
    pr = argv[0]
    raw_since = argv[argv.index("--since") + 1]
    since = parse_ts(raw_since)
    if since is None:
        print("CANNOT VERIFY: --since is not an ISO-8601 timestamp")
        return 2
    if since.tzinfo is None:
        print("CANNOT VERIFY: --since %r has no time zone; use the launcher's `bridge-run: started <time>Z` line" % raw_since)
        return 2
    repo_args = ["--repo", argv[argv.index("--repo") + 1]] if "--repo" in argv else []

    out, err = gh(["api", "user", "--jq", ".login"])
    if out is None:
        print("CANNOT VERIFY: gh api user failed (%s)" % err)
        return 2
    owner = out.strip()
    if not owner:
        print("CANNOT VERIFY: gh is not logged in")
        return 2

    repo = None
    if repo_args:
        repo = repo_args[1]
    else:
        out, err = gh(["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
        if out is None:
            print("CANNOT VERIFY: not inside a GitHub repository and no --repo given (%s)" % err)
            return 2
        repo = out.strip()

    sources = [
        ("comment", "repos/%s/issues/%s/comments" % (repo, pr), "created_at"),
        ("review", "repos/%s/pulls/%s/reviews" % (repo, pr), "submitted_at"),
        ("review comment", "repos/%s/pulls/%s/comments" % (repo, pr), "created_at"),
    ]
    found = []
    for kind, path, ts_key in sources:
        out, err = gh(["api", "--paginate", path])
        if out is None:
            print("CANNOT VERIFY: %s (%s)" % (path, err))
            return 2
        try:
            items = json.loads(out) if out.strip().startswith("[") else [json.loads(line) for line in out.splitlines() if line.strip()]
            if items and isinstance(items[0], list):
                items = [x for page in items for x in page]
        except ValueError:
            print("CANNOT VERIFY: unreadable response for %s" % path)
            return 2
        for it in items:
            ts = parse_ts(str(it.get(ts_key) or ""))
            if ts is None or ts < since:
                continue
            login = ((it.get("user") or {}).get("login") or "")
            if login.lower() == owner.lower():
                found.append((kind, it.get(ts_key), (it.get("body") or "").strip().replace("\n", " ")[:80]))

    elsewhere, errors = events_since(owner, since, repo)
    if found or elsewhere:
        if found:
            print("GATE-INTEGRITY: %d item(s) written to %s#%s as the owner (%s) since %s:" % (len(found), repo, pr, owner, since.isoformat()))
            for kind, ts, body in found:
                print("  %-15s %s  %s" % (kind, ts, body))
        if elsewhere:
            print("GATE-INTEGRITY: %d event(s) by the owner (%s) in %s since %s that a reviewer or builder would cause:" % (len(elsewhere), owner, repo, since.isoformat()))
            for kind, ts, repo_name, detail in elsewhere:
                print("  %-28s %s  %s  %s" % (kind, ts, repo_name, detail))
            print("A merge of ANOTHER pull request by the supervisor itself while this review ran is legitimate: record it and go on. A merge of this pull request before its verdict, or a comment or review by anyone but the supervisor, means an agent acted with the owner's login.")
        print("Do not merge until this is explained; record a gate-integrity flag and an issue for anything an agent did.")
        return 1
    if errors:
        print("CANNOT VERIFY: the pull request is clean but the owner's events could not be read (%s)" % "; ".join(errors)[:200])
        return 2
    print("OK: nothing written to %s#%s as %s since %s, and no agent-like event by %s in %s" % (repo, pr, owner, since.isoformat(), owner, repo))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
