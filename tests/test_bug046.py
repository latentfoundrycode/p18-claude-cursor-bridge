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


# ---------------------------------------------------------------- round 1's findings (the supervisor, Review A and the security audit, 2026-11-17)
# Round 1 resolved dot segments over the whole word, so a `..` in a query or fragment, or a trailing `merge/..`, erased the
# merge path gh requests (a regression: f3fa7b4 refused each); and it decoded only `%2f` and `%2e`, so an escaped letter of
# the path (`%70` is `p`, `%65` is `e`) passed. Each is refused under both tools, with the merge endpoint in the reason.
ROUND1_MERGE_SPELLINGS = [
    ("query-dot-segments", "gh api -X PUT 'repos/o/r/pulls/5/merge?a=/../../x'"),
    ("fragment-dot-segments", "gh api -X PUT 'repos/o/r/pulls/5/merge#/../../x'"),
    ("trailing-dot-dot", "gh api -X PUT repos/o/r/pulls/5/merge/.."),
    ("trailing-encoded-dot-dot", "gh api -X PUT repos/o/r/pulls/5/merge/%2e%2e"),
    ("trailing-mixed-dot-dot", "gh api -X PUT 'repos/o/r/pulls/5/merge/.%2e'"),
    ("query-encoded-slashes-dot-segments", "gh api -X PUT 'repos/o/r/pulls/5/merge?a=%2f..%2f..%2fx'"),
    ("path-dot-dot-before-a-query-dot-dot", "gh api -X PUT 'repos/o/r/pulls/5/x/../merge?q=/..'"),
    ("escaped-first-letter", "gh api -X PUT repos/o/r/%70ulls/5/merge"),
    ("escaped-last-letter", "gh api -X PUT repos/o/r/pulls/5/merg%65"),
    ("escaped-middle-letter", "gh api -X PUT repos/o/r/pulls/5/me%72ge"),
    ("every-letter-escaped", "gh api -X PUT repos/o/r/%70%75%6c%6c%73/5/%6d%65%72%67%65"),
    ("escaped-upper-hex", "gh api -X PUT repos/o/r/pull%73/5/%6Derge"),
    ("encoded-parent-segment", "gh api -X PUT repos/o/r/%2E%2E/r/pulls/5/merge"),
]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("command", [c for _, c in ROUND1_MERGE_SPELLINGS], ids=[n for n, _ in ROUND1_MERGE_SPELLINGS])
def test_bug046_r1_a_merge_endpoint_hidden_by_a_query_a_dot_segment_or_an_escape_is_refused(plain, tool, command):
    rc, err = guard(tool, command, plain)
    assert rc == 2 and "merge endpoint" in err, (tool, command, rc, err)


# A merge mutation's name written with escapes in a word gh sends (the security audit's advisory, the same family): refused
# under both tools as a merge mutation.
ROUND1_ESCAPED_MUTATIONS = [
    ("query-string-escaped-name", "gh api -X POST 'graphql?query=mutation%7Bmerge%50ullRequest(input:%7BpullRequestId:%22x%22%7D)%7BclientMutationId%7D%7D'"),
    ("url-query-string-escaped-name", "gh api -X POST 'https://api.github.com/graphql?query=mutation%7B%65nablePullRequestAutoMerge(input:%7B%7D)%7BclientMutationId%7D%7D'"),
]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("command", [c for _, c in ROUND1_ESCAPED_MUTATIONS], ids=[n for n, _ in ROUND1_ESCAPED_MUTATIONS])
def test_bug046_r1_an_escaped_merge_mutation_name_is_refused(plain, tool, command):
    rc, err = guard(tool, command, plain)
    assert rc == 2 and "merge mutation" in err, (tool, command, rc, err)


# Ordinary calls with escapes or queries that name no merge endpoint: each passes, before round 2 and after it.
ROUND1_ORDINARY = [
    ("escaped-space-in-a-search", "gh api 'search/issues?q=repo%3Ao%2Fr%20is%3Aopen'"),
    ("pull-request-files-paged", "gh api 'repos/o/r/pulls/5/files?per_page=100'"),
    ("issue-merge-escaped", "gh api repos/o/r/issues/5/%6derge"),
]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("command", [c for _, c in ROUND1_ORDINARY], ids=[n for n, _ in ROUND1_ORDINARY])
def test_bug046_r1_ordinary_calls_with_escapes_or_queries_pass(plain, tool, command):
    rc, err = guard(tool, command, plain)
    assert rc == 0, (tool, command, rc, err)


# ---------------------------------------------------------------- round 2's findings (Review A and the security audit, 2026-11-17)
# Round 2 decoded the word and then cut it at its first `?` or `#`, where gh cuts only at a literal one: an escaped `%3F` or
# `%23` (at any nesting) stays inside the path gh sends, and the `..` after it then resolves to the merge endpoint; and a
# decoded `%2F` split one segment into two, so `..` removed only half of it. Each is refused under both tools, with the
# merge endpoint in the reason (round 3: a word whose decoded, lower-cased text holds both `pulls` and `merge`).
ROUND2_MERGE_SPELLINGS = [
    ("escaped-hash-segment", "gh api -X PUT 'repos/o/r/pulls/5/%23/../merge'"),
    ("escaped-question-segment", "gh api -X PUT 'repos/o/r/pulls/5/%3F/../merge'"),
    ("escaped-question-inside-a-segment", "gh api -X PUT 'repos/o/r/pulls/5/a%3Fb/../merge'"),
    ("doubly-escaped-question", "gh api -X PUT 'repos/o/r/pulls/5/%253F/../merge'"),
    ("escaped-hash-full-url", "gh api -X PUT 'https://api.github.com/repos/o/r/pulls/5/%23/../merge'"),
    ("escaped-question-before-the-number", "gh api -X PUT 'repos/o/r/pulls/x%3F/../5/merge'"),
    ("escaped-hash-before-the-number", "gh api -X PUT 'repos/o/r/pulls/x%23/../5/merge'"),
    ("escaped-question-and-encoded-dots", "gh api -X PUT 'repos/o/r/pulls/5/a%3f/%2e%2e/merge'"),
    ("escaped-slash-inside-a-segment", "gh api -X PUT 'repos/o/r/pulls/5/a%2Fb/../merge'"),
]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("command", [c for _, c in ROUND2_MERGE_SPELLINGS], ids=[n for n, _ in ROUND2_MERGE_SPELLINGS])
def test_bug046_r2_an_escaped_delimiter_never_hides_the_merge_endpoint(plain, tool, command):
    rc, err = guard(tool, command, plain)
    assert rc == 2 and "merge endpoint" in err, (tool, command, rc, err)


# Ordinary calls that name pull requests or merges in separate words: each passes, before round 3 and after it.
ROUND2_ORDINARY = [
    ("pull-requests-listed-with-a-merged-filter", "gh api repos/o/r/pulls --jq '.[] | select(.merged_at)'"),
    ("pull-request-commits", "gh api repos/o/r/pulls/5/commits"),
    ("merged-search", "gh api 'search/issues?q=repo:o/r+is:pr+is:merged'"),
]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("command", [c for _, c in ROUND2_ORDINARY], ids=[n for n, _ in ROUND2_ORDINARY])
def test_bug046_r2_pulls_and_merge_in_separate_words_pass(plain, tool, command):
    rc, err = guard(tool, command, plain)
    assert rc == 0, (tool, command, rc, err)


# ---------------------------------------------------------------- the builder adds its cases below this line and edits nothing above it


# BUG-046 (R-082): --input= and a field glued to @, on a REST path and on graphql.
# PowerShell refuses a single-dash switch that holds a dot before the body rule, so those two rows use -Fquery=@- there. Bash keeps the dotted name.
GLUED_UNREADABLE_BODIES = [
    ("rest-input-equals", "gh api repos/o/r/issues/5/comments --input=body.json", "gh api repos/o/r/issues/5/comments --input=body.json"),
    ("graphql-input-equals", "gh api graphql --input=body.json", "gh api graphql --input=body.json"),
    ("rest-glued-field", "gh api repos/o/r/issues/5/comments -Fquery=@q.graphql", "gh api repos/o/r/issues/5/comments -Fquery=@-"),
    ("graphql-glued-field", "gh api graphql -Fquery=@q.graphql", "gh api graphql -Fquery=@-"),
    ("rest-long-field", "gh api repos/o/r/issues/5/comments --field=query=@q.graphql", "gh api repos/o/r/issues/5/comments --field=query=@q.graphql"),
    ("graphql-long-field", "gh api graphql --field=query=@q.graphql", "gh api graphql --field=query=@q.graphql"),
    # Accepted over-refusal (BUG-046 F1): -f sends the value as written, and key=@x is refused with the file reads.
    ("raw-field-at", "gh api repos/o/r/issues/5/comments -f key=@x", "gh api repos/o/r/issues/5/comments -f key=@x"),
]


@pytest.mark.parametrize("tool", TOOLS, ids=["Bash", "PowerShell"])
@pytest.mark.parametrize("name,bash,powershell", GLUED_UNREADABLE_BODIES, ids=[n for n, _, _ in GLUED_UNREADABLE_BODIES])
def test_bug046_glued_and_clustered_unreadable_bodies_are_refused_on_rest_and_graphql(plain, tool, name, bash, powershell):
    """BUG-046 (R-082): a body the guard cannot read is refused on a REST path and on graphql."""
    command = powershell if tool == "PowerShell" else bash
    rc, err = guard(tool, command, plain)
    assert rc == 2 and "refused" in err and "body read from a file or standard input" in err, (tool, name, command, rc, err)


# BUG-046 (R-082): the merge endpoint with a query, a fragment, or %2E segments. The query is quoted because an unquoted ? is a glob.
MERGE_ENDPOINT_SPELLINGS = [
    ("trailing-query", "gh api 'repos/o/r/pulls/5/merge?x=1'"),
    ("trailing-fragment", "gh api repos/o/r/pulls/5/merge#frag"),
    ("percent-2e-dot", "gh api repos/o/r/pulls/5/%2E/merge"),
    ("percent-2e-dot-before-pulls", "gh api repos/o/r/%2E/pulls/5/merge"),
    ("doubly-escaped-letter", "gh api -X PUT repos/o/r/%2570ulls/5/merge"),
]


@pytest.mark.parametrize("tool", TOOLS, ids=["Bash", "PowerShell"])
@pytest.mark.parametrize("command", [c for _, c in MERGE_ENDPOINT_SPELLINGS], ids=[n for n, _ in MERGE_ENDPOINT_SPELLINGS])
def test_bug046_a_merge_endpoint_with_a_query_fragment_or_percent_2e_is_refused(plain, tool, command):
    """BUG-046 (R-082): those spellings still name a pull request's merge endpoint."""
    rc, err = guard(tool, command, plain)
    assert rc == 2 and "refused" in err and "merge endpoint" in err, (tool, command, rc, err)


@pytest.mark.parametrize("tool", TOOLS, ids=["Bash", "PowerShell"])
def test_bug046_an_issues_merge_endpoint_passes(plain, tool):
    """BUG-046 (R-082): repos/o/r/issues/5/merge is not a pull request's merge endpoint."""
    rc, err = guard(tool, "gh api repos/o/r/issues/5/merge", plain)
    assert rc == 0, (tool, rc, err)


@pytest.mark.parametrize("tool", TOOLS, ids=["Bash", "PowerShell"])
def test_bug046_mergeable_report_is_refused(plain, tool):
    """BUG-046 (R-082): accepted over-refusal. The rule refuses a word that holds /pulls/<segment>/merge, so repos/o/r/pulls/5/mergeable-report is refused because it holds /pulls/5/merge."""
    rc, err = guard(tool, "gh api repos/o/r/pulls/5/mergeable-report", plain)
    assert rc == 2 and "refused" in err and "merge endpoint" in err, (tool, rc, err)

