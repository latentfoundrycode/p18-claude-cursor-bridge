"""R-082: the permission guard reads a command as the shell does (TASK-063).

The supervisor's acceptance tests, written before the builder's run. Each runs permission-guard.py as the hook runs it
(the hook's JSON on standard input, the Bash tool), from a scratch folder that is no bridge Workspace unless a case says
so, and reads the exit code (2 refuses, 0 lets through) and the reason on standard error.

enforces: docs/DESIGN.md, "Change: the program release", "The permission guard, permission-guard.py (C5)";
docs/BUILD_PLAN.md, TASK-063's Done when; R-082.
"""
import json
import os
import subprocess
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py")
HOOK_SECONDS = 15   # settings.bridge.json gives the permission guard's hook a timeout of 15 seconds

WR = "git worktree remove ../Worktrees/TASK-012"    # refused in every form (rule 19)
MERGE = "gh pr merge 12 --squash"                   # refused without --match-head-commit and its record
BS = "\\"                                            # one backslash
BT = "`"                                             # one backtick


def guard(command, cwd):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "permission_mode": "auto", "cwd": str(cwd)}
    p = subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stderr


@pytest.fixture
def plain(tmp_path):
    """A folder that is no bridge Workspace: rule 8's chain refusal does not apply there."""
    d = tmp_path / "plain"
    d.mkdir()
    return d


@pytest.fixture
def workspace(tmp_path):
    """A bridge Workspace (it holds docs/PROJECT_STATUS.md): rule 8's chain refusal applies."""
    d = tmp_path / "ws"
    (d / "docs").mkdir(parents=True)
    (d / "docs" / "PROJECT_STATUS.md").write_text("# Project Status\n", encoding="utf-8")
    return d


def refused(command, cwd):
    rc, err = guard(command, cwd)
    assert rc == 2 and "refused" in err, (command, rc, err)
    return err


def passes(command, cwd):
    rc, err = guard(command, cwd)
    assert rc == 0, (command, rc, err)


# ---------------------------------------------------------------- the two reproductions of the design, red on the checkpoint

def test_r082_a_refused_command_inside_a_double_quoted_substitution_is_refused(plain):
    """`"$( )"`: a command substitution inside double quotes is a command of its own."""
    refused('echo "$(' + WR + ')"', plain)


def test_r082_a_refused_command_after_a_double_quoted_string_ending_in_a_backslash_is_refused(plain):
    """`"a\\\\"` closes after the escaped backslash, as bash closes it, and hides nothing after it."""
    refused('echo "a' + BS + BS + '" ; ' + WR, plain)


# ---------------------------------------------------------------- the same holes in their other spellings

HOLES = [
    ("backtick-inside-double-quotes", 'echo "' + BT + WR + BT + '"'),
    ("single-quoted-string-ending-in-a-backslash", "echo 'a" + BS + "' ; " + WR),
    ("merge-inside-double-quoted-substitution", 'echo "$(' + MERGE + ')"'),
    ("even-run-of-backslashes-before-the-substitution", 'echo "' + BS + BS + '$(' + WR + ')"'),
    ("ansi-c-string-ending-in-an-escaped-backslash", "echo $'a" + BS + BS + "' ; " + WR),
    ("substitution-inside-parameter-expansion", 'echo "${x:-$(' + WR + ')}"'),
    ("backtick-inside-parameter-expansion", 'echo "${x:-' + BT + WR + BT + '}"'),
    ("nested-substitutions", 'echo "$(echo "$(' + WR + ')")"'),
    ("substitution-inside-a-here-string", 'cat <<< "$(' + WR + ')"'),
    ("mixed-quotes", "echo 'a \"b' \"$(" + WR + ')"'),
    ("process-substitution-in", "diff <(" + WR + ") x.txt"),
    ("process-substitution-out", "tee >(" + MERGE + ") < x.txt"),
]


@pytest.mark.parametrize("command", [c for _, c in HOLES], ids=[n for n, _ in HOLES])
def test_r082_a_refused_command_hidden_by_quoting_or_substitution_is_refused(plain, command):
    refused(command, plain)


HARMLESS = [
    ("double-quoted-substitution", 'echo "$(git status)"'),
    ("double-quoted-backtick", 'echo "' + BT + 'date' + BT + '"'),
    ("nested-substitutions", 'echo "$(echo "$(date)")"'),
    ("here-string", 'cat <<< "$(date)"'),
    ("parameter-expansion", 'echo "${x:-$(date)}"'),
    ("process-substitution", "diff <(git log -1) <(git status)"),
    ("single-quoted-substitution-is-text", "echo \"it's\" '$(" + WR + ")'"),
    ("escaped-dollar-inside-double-quotes", 'echo "' + BS + '$(' + WR + ')"'),
    ("ansi-c-escaped-quote-closes-nothing", "echo $'it" + BS + "'s; " + MERGE + "'"),
    ("escaped-backticks-outside-quotes", "echo " + BS + BT + WR + BS + BT),
    ("escaped-backticks-inside-double-quotes", 'echo "x ' + BS + BT + WR + BS + BT + ' y"'),
    ("double-quoted-escaped-quote", 'echo "a ' + BS + '" ; ' + WR + '"'),
    ("indirect-expansion-in-the-command-place", "${!name} worktree remove ../Worktrees/TASK-012"),
    ("variable-in-the-command-place", "$CMD worktree remove ../Worktrees/TASK-012"),
]


@pytest.mark.parametrize("command", [c for _, c in HARMLESS], ids=[n for n, _ in HARMLESS])
def test_r082_a_harmless_form_passes(plain, command):
    passes(command, plain)


# ---------------------------------------------------------------- rule 8's chain, read by the second splitter

def test_r082_a_chain_hidden_after_a_string_ending_in_a_backslash_is_refused_in_a_workspace(workspace):
    err = refused('echo "a' + BS + BS + '" && git add -A', workspace)
    assert "chain" in err, err


def test_r082_a_chain_inside_a_double_quoted_substitution_is_refused_in_a_workspace(workspace):
    err = refused('echo "$(git add -A && git commit -m x)"', workspace)
    assert "chain" in err, err


def test_r082_a_gh_api_read_still_counts_as_a_state_change_in_a_chain(workspace):
    err = refused("git status && gh api repos/o/r", workspace)
    assert "chain" in err, err


# ---------------------------------------------------------------- the three moved tests

def test_r082_a_commit_message_that_quotes_no_verify_passes(plain):
    """A false refusal of the checkpoint: --no-verify as -m's value is the message, not an option."""
    passes('git commit -m "--no-verify"', plain)


def test_r082_husky_inside_a_quoted_argument_passes(plain):
    """A false refusal of the checkpoint: HUSKY=0 inside a commit message is no assignment."""
    passes('git commit -m "set HUSKY=0 in CI"', plain)


def test_r082_a_substitution_in_a_quoted_field_of_another_command_passes(plain):
    """A false refusal of the checkpoint: the graphql test reads that command's own arguments."""
    passes("gh api graphql -f query='query { viewer { login } }'; gh api repos/o/r/issues -f body='see $(this)'", plain)


@pytest.mark.parametrize("sub,command", [
    ("commit", "git commit --no-verify -m x"),
    ("push", "git push --no-verify origin task-012"),
    ("merge", "git merge --no-verify task-012"),
    ("rebase", "git rebase --no-verify main"),
    ("am", "git am --no-verify fix.patch"),
    ("cherry-pick", "git cherry-pick --no-verify 0123abc"),
    ("revert", "git revert --no-verify 0123abc"),
], ids=["commit", "push", "merge", "rebase", "am", "cherry-pick", "revert"])
def test_r082_no_verify_is_refused_as_an_option_of_each_hook_skipper(plain, sub, command):
    err = refused(command, plain)
    assert "--no-verify" in err, err


@pytest.mark.parametrize("command", [
    "HUSKY=0 git commit -m x",
    "HUSKY=0 git push origin task-012",
    "X=1 HUSKY=0 git merge task-012",
], ids=["commit", "push", "merge-after-another-assignment"])
def test_r082_a_leading_husky_assignment_is_refused(plain, command):
    err = refused(command, plain)
    assert "HUSKY" in err, err


@pytest.mark.parametrize("command", [
    'gh api graphql -f query="$(cat merge.graphql)"',
    "gh api graphql -f query=" + BT + "cat merge.graphql" + BT,
    "gh api graphql -f query=\"" + BT + "cat merge.graphql" + BT + "\"",
], ids=["dollar-paren", "backtick", "quoted-backtick"])
def test_r082_a_graphql_query_built_by_a_substitution_is_refused(plain, command):
    err = refused(command, plain)
    assert "graphql" in err, err


# ---------------------------------------------------------------- an unquoted & in a gh api argument

def test_r082_an_unquoted_ampersand_in_a_gh_api_argument_is_refused_with_its_remedy(plain):
    err = refused("gh api repos/o/r/pulls?state=all&per_page=1", plain)
    assert "quote" in err.lower(), err


def test_r082_a_quoted_ampersand_in_a_gh_api_argument_passes(plain):
    passes("gh api 'repos/o/r/pulls?state=all&per_page=1'", plain)


# ---------------------------------------------------------------- a long command, read within the hook's time

@pytest.mark.parametrize("command", [
    'echo "' + "$(echo x) " * 1000 + '"',
    'echo "' + BS * 9994 + '"',
    "echo " + "'a' \"b\" $'c' " * 770,
], ids=["substitutions", "backslashes", "mixed-quotes"])
def test_r082_a_command_of_ten_thousand_characters_is_read_within_the_hooks_time(plain, command):
    assert len(command) >= 10000
    started = time.monotonic()
    passes(command, plain)
    assert time.monotonic() - started < HOOK_SECONDS
