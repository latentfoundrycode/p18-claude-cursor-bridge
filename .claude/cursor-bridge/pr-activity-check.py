#!/usr/bin/env python3
"""pr-activity-check: prove that nobody wrote to a pull request as the owner during a run.

  python ~/.claude/cursor-bridge/pr-activity-check.py <pr-number> --since <ISO-8601 UTC> [--repo owner/name]

Why (KP-032): the cross-family reviewer and the builder run as `cursor-agent` processes on
the owner's machine. Before release 2026.10.04a they inherited the owner's GitHub login, and
a reviewer twice posted its verdict on a pull request under the owner's name. The shim and
bridge-run.py now withhold that login; this check is the proof, run after every Review B
and before every merge: it lists every comment, review and review comment on the pull
request created at or after --since and flags any written by the account `gh` is logged
in as (the owner). A read-only check: it uses `gh api` GET calls only.

Exit 0 = nothing written as the owner since --since; 1 = GATE-INTEGRITY, something was;
2 = cannot verify (gh not logged in, API error) - treat as not verified, never as clean.
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


def main():
    argv = sys.argv[1:]
    if not argv or "--since" not in argv:
        print("usage: pr-activity-check.py <pr-number> --since <ISO-8601 UTC> [--repo owner/name]")
        return 2
    pr = argv[0]
    since = parse_ts(argv[argv.index("--since") + 1])
    if since is None:
        print("CANNOT VERIFY: --since is not an ISO-8601 timestamp")
        return 2
    if since.tzinfo is None:
        since = since.replace(tzinfo=datetime.timezone.utc)
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

    if found:
        print("GATE-INTEGRITY: %d item(s) written to %s#%s as the owner (%s) since %s:" % (len(found), repo, pr, owner, since.isoformat()))
        for kind, ts, body in found:
            print("  %-15s %s  %s" % (kind, ts, body))
        print("A reviewer or builder acted with the owner's login. Do not merge; record a gate-integrity flag and an issue.")
        return 1
    print("OK: nothing written to %s#%s as %s since %s" % (repo, pr, owner, since.isoformat()))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
