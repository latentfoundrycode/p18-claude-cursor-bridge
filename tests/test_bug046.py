"""BUG-046 (R-082, R-083): the permission guard's refusal of a merge through `gh api` reads the method from words gh reads as other options' values, and its refusal of a body it cannot read holds only for the bare endpoint word `graphql`.

The supervisor's reproduction tests, written before the builder's run (docs/debug/BUG-046.md). Each runs
permission-guard.py as the hook runs it (the hook's JSON on standard input), under the Bash tool and the PowerShell
tool, from a scratch folder that is no bridge Workspace, and reads the exit code (2 refuses, 0 lets through).

The causes: permission-guard.py's `gh api` branch of `_check_word_list` takes the method from every word, so a
value-taking option's value that looks like a method (`-p -XGET`, `-H --method=GET`) is read as the last method, where gh
(pflag) reads it as that option's value and sends the method written before it; and its refusal of a query read from a file
or standard input runs only where gh_words reads the endpoint as exactly `graphql`, where gh also takes a URL or a path to
the GraphQL endpoint (`https://api.github.com/graphql`, `/graphql`) and a body from `--input`. Found by the security audit
of TASK-083's round 4 (docs/HARDENING.md, TASK-083, ruling 2).

enforces: docs/DESIGN.md, "Change: the program release", "The permission guard, permission-guard.py (C5)"; R-082; R-083;
docs/INVENTORY.md, Decisions, the permission guard's threat-model row (a refused action named in the command's own words).
"""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py")
TOOLS = ["Bash", "PowerShell"]


def guard(tool, command, cwd):
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto", "cwd": str(cwd)}
    p = subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stderr


@pytest.fixture
def plain(tmp_path):
    """A folder that is no bridge Workspace."""
    d = tmp_path / "plain"
    d.mkdir()
    return d


# A merge through the REST endpoint whose method gh reads as PUT, a word that looks like a method standing as another
# option's value. Each is refused (red on f3fa7b4).
METHOD_AS_A_VALUE = [
    ("preview-value-short-method", "gh api -X PUT repos/o/r/pulls/5/merge -p -XGET"),
    ("header-value-long-method", "gh api --method PUT repos/o/r/pulls/5/merge -H --method=GET"),
    ("jq-value-short-method", "gh api -X PUT repos/o/r/pulls/5/merge -q -XGET"),
    ("template-value-long-method", "gh api -XPUT repos/o/r/pulls/5/merge -t --method=GET"),
]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("command", [c for _, c in METHOD_AS_A_VALUE], ids=[n for n, _ in METHOD_AS_A_VALUE])
def test_bug046_a_method_word_that_is_another_options_value_never_lets_a_merge_through(plain, tool, command):
    rc, err = guard(tool, command, plain)
    assert rc == 2 and "refused" in err, (tool, command, rc, err)


# A query or body read from a file or standard input, sent to the GraphQL endpoint named another way than the bare word.
# Each is refused (red on f3fa7b4).
BODY_IT_CANNOT_READ = [
    ("url-field-from-a-file", "gh api https://api.github.com/graphql -F query=@q.graphql"),
    ("url-input-file", "gh api https://api.github.com/graphql --input body.json"),
    ("path-field-from-a-file", "gh api /graphql -F query=@q.graphql"),
    ("path-input-standard-input", "gh api /graphql --input -"),
    ("url-long-field-from-standard-input", "gh api https://api.github.com/graphql --field=query=@-"),
]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("command", [c for _, c in BODY_IT_CANNOT_READ], ids=[n for n, _ in BODY_IT_CANNOT_READ])
def test_bug046_a_body_the_guard_cannot_read_is_refused_whatever_the_endpoint(plain, tool, command):
    rc, err = guard(tool, command, plain)
    assert rc == 2 and "refused" in err, (tool, command, rc, err)


# The ruling F2: a pull request's merge endpoint named in any form is refused whatever the method, a read of it as well
# (the bridge never reads it; `gh pr view <n> --json mergedAt,mergeable` is the read). Each is refused.
MERGE_ENDPOINT_FORMS = [
    ("read-no-method", "gh api repos/o/r/pulls/12/merge"),
    ("put-doubled-slashes", "gh api -X PUT repos/o/r/pulls//5//merge"),
    ("put-upper-case", "gh api -X PUT repos/o/r/PULLS/5/MERGE"),
    ("put-dot-segment", "gh api -X PUT repos/o/r/pulls/5/./merge"),
    ("put-dot-dot-segment", "gh api -X PUT repos/o/r/pulls/5/x/../merge"),
    ("put-encoded-slashes", "gh api -X PUT repos/o/r/pulls%2F5%2Fmerge"),
    ("put-url", "gh api -X PUT https://api.github.com/repos/o/r/pulls/5/merge"),
    ("get-method-given", "gh api -X GET repos/o/r/pulls/5/merge"),
]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("command", [c for _, c in MERGE_ENDPOINT_FORMS], ids=[n for n, _ in MERGE_ENDPOINT_FORMS])
def test_bug046_the_merge_endpoint_is_refused_whatever_the_method_or_spelling(plain, tool, command):
    rc, err = guard(tool, command, plain)
    assert rc == 2 and "refused" in err, (tool, command, rc, err)


# The reads and writes the bridge and an ordinary session make through gh api, none a merge and none with a body read from
# a file. Each passes, before the fix and after it.
ORDINARY_API_CALLS = [
    ("pull-request-read", "gh api repos/o/r/pulls/12 --jq .mergeable"),
    ("pull-request-read-with-header", "gh api -H Accept:application/json repos/OWNER/REPO/pulls/12"),
    ("vulnerability-alerts", "gh api repos/OWNER/REPO/vulnerability-alerts"),
    ("dependabot-alerts-paged", "gh api --paginate 'repos/OWNER/REPO/dependabot/alerts?state=open'"),
    ("graphql-read-on-the-command-line", "gh api graphql -f 'query=query { viewer { login } }'"),
    ("search-with-get-and-a-field", "gh api -X GET search/issues -f q=repo:cli/cli"),
    ("issue-comment-post", "gh api repos/o/r/issues/5/comments -f body=hi"),
    ("check-runs-read", "gh api 'repos/OWNER/REPO/commits/abc/check-runs?per_page=100'"),
]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("command", [c for _, c in ORDINARY_API_CALLS], ids=[n for n, _ in ORDINARY_API_CALLS])
def test_bug046_ordinary_api_calls_still_pass(plain, tool, command):
    rc, err = guard(tool, command, plain)
    assert rc == 0, (tool, command, rc, err)


# ---------------------------------------------------------------- the builder adds its cases below this line and edits nothing above it
