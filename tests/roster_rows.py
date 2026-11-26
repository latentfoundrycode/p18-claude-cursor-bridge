"""Shared by tests/test_improve_roster_alt.py (TASK-086a) and tests/test_improve_roster_launch.py (TASK-086b): the
roster's model ids and profiles, a launcher run-record row as the launcher writes it, and two readers of the
programs' output. One copy, the two files' former identical helpers (stage I1's refactoring pass, tests lane)."""
import itertools
import json
import os

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
       "-c", "commit.gpgsign=false"]
BRANCH = "task-1"

REVIEW_A = "claude-opus-5-5"        # anthropic, Review A's family
GROK_B = "grok-4.7-high"            # xai, native pool
GROK_R = "grok-4.7-medium"          # xai, native pool
COMPOSER = "composer-2.5"           # cursor, native pool
GPT = "gpt-5.6-sol-high"            # openai, other pool

FULL = {"name": "full", "builder": GROK_B, "review_b": GPT}
NATIVE = {"name": "native", "builder": COMPOSER, "review_b": GROK_R}

_ids = itertools.count(1)


def row(model, branch=BRANCH, start=None, clean=None, brief="TASK-001", rnd=1, slot=None):
    """A builder row as the launcher writes it; `start_commit` and `clean` only where given."""
    e = {"id": "r%d" % next(_ids), "kind": "builder", "head": "cursor-agent", "model": model, "branch": branch,
         "limit": 7200, "seconds": 100, "exit": 0, "healthy": True}
    if brief:
        e.update(brief=brief, round=rnd, brief_name=brief if rnd == 1 else "%s-r%d" % (brief, rnd))
    if start is not None:
        e["start_commit"] = start
    if clean is not None:
        e["clean"] = clean
    if slot:
        e.update(slot=slot, exit=123, seconds=0, healthy=None, waited=7320)
    return json.dumps(e)


def review_row(model=GPT, branch=BRANCH):
    return json.dumps({"id": "v%d" % next(_ids), "kind": "review", "head": "cursor-agent", "model": model,
                       "branch": branch, "limit": 3600, "seconds": 10, "exit": 0, "healthy": True})


def rebuild_text(out):
    return "\n".join(line for line in out.splitlines() if "REBUILD" in line)


def lies_in_no_repository(path):
    p = os.path.abspath(str(path))
    while True:
        if os.path.exists(os.path.join(p, ".git")):
            return False
        parent = os.path.dirname(p)
        if parent == p:
            return True
        p = parent
