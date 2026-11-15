"""R-082: the permission guard reads a command as the shell does (TASK-063).

The supervisor's acceptance tests, written before the builder's run. Each runs permission-guard.py as the hook runs it
(the hook's JSON on standard input, the Bash tool), from a scratch folder that is no bridge Workspace unless a case says
so, and reads the exit code (2 refuses, 0 lets through) and the reason on standard error.

Since the second resolution round (docs/CHANGES.md, 2026-11-15 TASK-063: second resolution round) the guard reads one
flat grammar, in which every command is one list of complete words, and refuses every nested construct as unreadable:
the cases written for the earlier subsets that expected a nested form to pass now expect it refused.

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
    ("single-quoted-substitution-is-text", "echo \"it's\" '$(" + WR + ")'"),
    ("double-quoted-escaped-quote", 'echo "a ' + BS + '" ; ' + WR + '"'),
]


@pytest.mark.parametrize("command", [c for _, c in HARMLESS], ids=[n for n, _ in HARMLESS])
def test_r082_a_harmless_form_passes(plain, command):
    passes(command, plain)


# Forms round 1's harmless list let through: under the flat grammar each holds a `$`, a backtick or `<(` outside
# single quotes, and is refused as unreadable.
HARMLESS_BEFORE_THE_FLAT_GRAMMAR = [
    ("double-quoted-substitution", 'echo "$(git status)"'),
    ("double-quoted-backtick", 'echo "' + BT + 'date' + BT + '"'),
    ("nested-substitutions", 'echo "$(echo "$(date)")"'),
    ("process-substitution", "diff <(git log -1) <(git status)"),
    ("escaped-dollar-inside-double-quotes", 'echo "' + BS + '$(' + WR + ')"'),
    ("ansi-c-escaped-quote-closes-nothing", "echo $'it" + BS + "'s; " + MERGE + "'"),
    ("escaped-backticks-outside-quotes", "echo " + BS + BT + WR + BS + BT),
    ("escaped-backticks-inside-double-quotes", 'echo "x ' + BS + BT + WR + BS + BT + ' y"'),
    ("indirect-expansion-in-the-command-place", "${!name} worktree remove ../Worktrees/TASK-012"),
    ("variable-in-the-command-place", "$CMD worktree remove ../Worktrees/TASK-012"),
]


@pytest.mark.parametrize("command", [c for _, c in HARMLESS_BEFORE_THE_FLAT_GRAMMAR], ids=[n for n, _ in HARMLESS_BEFORE_THE_FLAT_GRAMMAR])
def test_r082_a_once_harmless_nested_form_is_refused_as_unreadable(plain, command):
    err = refused(command, plain)
    assert "cannot read" in err.lower(), err


# ---------------------------------------------------------------- rule 8's chain, read by the second splitter

def test_r082_a_chain_hidden_after_a_string_ending_in_a_backslash_is_refused_in_a_workspace(workspace):
    err = refused('echo "a' + BS + BS + '" && git add -A', workspace)
    assert "chain" in err, err


def test_r082_a_chain_inside_a_double_quoted_substitution_is_refused_in_a_workspace(workspace):
    """Refused: a chain once, unreadable under the flat grammar."""
    refused('echo "$(git add -A && git commit -m x)"', workspace)


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
    assert "graphql" in err or "cannot read" in err.lower(), err


# ---------------------------------------------------------------- an unquoted & in a gh api argument

def test_r082_an_unquoted_ampersand_in_a_gh_api_argument_is_refused_with_its_remedy(plain):
    err = refused("gh api repos/o/r/pulls?state=all&per_page=1", plain)
    assert "quote" in err.lower(), err


def test_r082_a_quoted_ampersand_in_a_gh_api_argument_passes(plain):
    passes("gh api 'repos/o/r/pulls?state=all&per_page=1'", plain)


# ---------------------------------------------------------------- the supervisor's tests after round 1 (forms bash reads that round 1 did not)

GLUED = [
    ("glued-ampersand-before-a-worktree-removal", "git status&" + WR),
    ("glued-ampersand-before-a-merge", "git fetch&" + MERGE),
    ("quoted-paren-inside-a-double-quoted-substitution", 'echo "$(echo ")" ; ' + WR + ')"'),
]


@pytest.mark.parametrize("command", [c for _, c in GLUED], ids=[n for n, _ in GLUED])
def test_r082_a_refused_command_after_a_glued_ampersand_or_a_quoted_paren_is_refused(plain, command):
    """bash ends a command at an unquoted & with or without a space, and a quote inside $( ) opens a new context."""
    refused(command, plain)


def test_r082_a_chain_glued_with_an_ampersand_is_refused_in_a_workspace(workspace):
    err = refused("git add -A&git commit -m x", workspace)
    assert "chain" in err, err


def test_r082_an_unquoted_substitution_building_a_graphql_query_is_refused(plain):
    err = refused("gh api graphql -f query=$(cat merge.graphql)", plain)
    assert "graphql" in err or "cannot read" in err.lower(), err


@pytest.mark.parametrize("sub,command", [
    ("rebase", "git rebase -m --no-verify main"),
    ("am", "git am -m --no-verify fix.patch"),
], ids=["rebase-m-is-a-flag", "am-m-is-a-flag"])
def test_r082_no_verify_after_a_flag_that_takes_no_value_is_refused(plain, sub, command):
    """-m is rebase's --merge and am's --message-id, flags that take no value: the --no-verify after them is an option."""
    err = refused(command, plain)
    assert "--no-verify" in err, err


def test_r082_an_unquoted_ampersand_after_a_quoted_gh_api_argument_is_refused_with_its_remedy(plain):
    err = refused("gh api -H 'Accept: application/json' repos/o/r/pulls?state=all&per_page=1", plain)
    assert "quote" in err.lower(), err


def _nested_quoted(depth, core):
    """echo "$(echo "$(... core)")": every level but the innermost echoes the next; the innermost runs core."""
    return 'echo "$(' * depth + core + ')"' * depth


def _nested_unquoted(depth, core):
    """echo "$(echo $(echo ... $(core)))": one double quote around a nest of unquoted substitutions."""
    return 'echo "' + '$(echo ' * (depth - 1) + '$(' + core + ')' * depth + '"'


NESTS = [
    ("quoted-depth-25", _nested_quoted(25, WR)),
    ("quoted-depth-400", _nested_quoted(400, WR)),
    ("unquoted-depth-1000", _nested_unquoted(1000, WR)),
    ("parameter-expansion-depth-1000", "echo " + "${x:-" * 1000 + "}" * 1000 + " ; " + WR),
    ("twenty-nests-of-400-then-a-removal", " ; ".join([_nested_unquoted(400, "true")] * 20) + " ; " + WR),
    ("eval-depth-1000", "eval " * 1000 + WR),
    ("thirty-thousand-backslashes-quoted", 'echo "' + BS * 30000 + '" ; ' + WR),
    ("forty-thousand-backslashes-unquoted", "echo " + BS * 40000 + " ; " + WR),
]


@pytest.mark.parametrize("command", [c for _, c in NESTS], ids=[n for n, _ in NESTS])
def test_r082_a_refused_command_after_deep_nesting_or_a_long_escape_run_is_refused_within_the_hooks_time(plain, command):
    """A depth the reading cannot finish, or a recursion it cannot hold, must not end in an exit other than 2
    (an exit 1 or the hook's timeout lets the command run)."""
    started = time.monotonic()
    refused(command, plain)
    assert time.monotonic() - started < HOOK_SECONDS


# ---------------------------------------------------------------- the reviewers' reproductions after round 1

NL = "\n"
TAB = "\t"

READ_AS_BASH_READS = [
    ("husky-before-eval", "HUSKY=0 eval git commit -m x"),
    ("husky-before-bash-c", 'HUSKY=0 bash -c "git commit -m x"'),
    ("husky-before-sh-c", "HUSKY=0 sh -c 'git push origin main'"),
    ("env-u-value-then-husky", "env -u FOO HUSKY=0 git commit -m x"),
    ("env-C-value-then-husky", "env -C sub HUSKY=0 git commit -m x"),
    ("apostrophe-in-a-comment", "git status # don't worry" + NL + WR),
    ("double-quote-in-a-comment", 'git status # say "hi' + NL + WR),
    ("comment-inside-a-double-quoted-substitution", 'echo "$(# )' + NL + WR + ')"'),
    ("case-pattern-inside-a-double-quoted-substitution", 'echo "$(case x in x) ' + WR + ';; esac)"'),
    ("pipe-quoted-inside-a-double-quoted-substitution", 'echo "$(echo ";" | ' + WR + ')"'),
    ("quoted-paren-inside-a-backtick-in-double-quotes", 'echo "' + BT + 'echo ")" ; ' + WR + BT + '"'),
    ("escaped-backslash-before-a-newline", "echo a" + BS + BS + NL + WR),
    ("backtick-before-a-newline-under-bash", "echo " + BT + NL + WR + NL + BT),
    ("escaped-double-quote-outside-quotes", "echo " + BS + '" ; ' + WR + " ; echo " + BS + '"'),
    ("escaped-single-quote-outside-quotes", "echo " + BS + "' ; " + WR + " ; echo " + BS + "'"),
    ("ansi-c-quoted-subcommand", "git $'worktree' remove ../Worktrees/TASK-012"),
    ("locale-quoted-subcommand", 'git $"worktree" remove ../Worktrees/TASK-012'),
    ("ansi-c-hex-escape-in-a-subcommand", "git worktree $'" + BS + "x72emove' ../Worktrees/TASK-012"),
    ("ansi-c-quoted-force-flag", "git push $'--force' origin main"),
    ("heredoc-operator-inside-quotes", 'echo "<<EOF"' + NL + WR + NL + "EOF"),
    ("here-string-is-no-heredoc", "cat <<<EOF" + NL + WR + NL + "EOF"),
    ("tab-indented-heredoc-terminator", "cat <<-EOF" + NL + "x" + NL + TAB + "EOF" + NL + WR + NL + "EOF"),
    ("heredoc-piped-to-a-shell", "cat <<EOF | bash" + NL + WR + NL + "EOF"),
]


@pytest.mark.parametrize("command", [c for _, c in READ_AS_BASH_READS], ids=[n for n, _ in READ_AS_BASH_READS])
def test_r082_a_refused_command_the_shell_runs_is_refused(plain, command):
    refused(command, plain)


STILL_PASS = [
    ("gh-api-with-stderr-redirect", "gh api repos/o/r/pulls 2>&1"),
    ("gh-api-with-both-redirect", "gh api repos/o/r &>/dev/null"),
    ("gh-api-and-and", "gh api repos/o/r&&echo ok"),
    ("gh-api-words-in-an-echo", "echo gh api a&b"),
    ("process-substitution-words-inside-double-quotes", 'git commit -m "see <(gh pr merge 12 --squash) in docs"'),
    ("substitution-inside-a-comment", "echo hi # $(" + WR + ")"),
]


@pytest.mark.parametrize("command", [c for _, c in STILL_PASS], ids=[n for n, _ in STILL_PASS])
def test_r082_a_form_the_shell_does_not_run_as_a_refused_command_passes(plain, command):
    passes(command, plain)


def test_r082_the_apps_commit_form_is_refused_as_unreadable_in_a_workspace(workspace):
    """The app's commit form holds a substitution and a here-document: unreadable under the flat grammar (the
    agent writes the message to a file and commits with -F)."""
    err = refused("git commit -m \"$(cat <<'EOF'" + NL + "fix: don't read the body" + NL + NL + "a body line" + NL + "EOF" + NL + ')"', workspace)
    assert "cannot read" in err.lower(), err


def test_r082_a_state_change_inside_a_substitution_of_a_chain_is_refused_in_a_workspace(workspace):
    """Refused: a chain once, unreadable under the flat grammar."""
    refused('ls && echo "$(git commit -m x)"', workspace)


BACKTICK_ENDS = [
    ("double-quote-inside-a-backtick-pair", "echo " + BT + 'echo "' + BT + " ; " + WR + " ; " + BT + 'echo "' + BT),
    ("single-quote-inside-a-backtick-pair", "echo " + BT + "echo '" + BT + " ; " + WR + " ; " + BT + "echo '" + BT),
    ("comment-inside-a-backtick-pair", "echo " + BT + "# c" + BT + " ; " + WR),
]


@pytest.mark.parametrize("command", [c for _, c in BACKTICK_ENDS], ids=[n for n, _ in BACKTICK_ENDS])
def test_r082_a_backtick_pair_ends_at_its_first_unescaped_backtick(plain, command):
    """bash ends a backtick substitution at the first unescaped backtick, whatever quote or # stands before it
    (the supervisor's test after round 2, the brief's own forms)."""
    refused(command, plain)


def guard_tool(command, cwd, tool):
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto", "cwd": str(cwd)}
    p = subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stderr


# ---------------------------------------------------------------- after the resolution round: read a subset exactly, refuse the rest
# (docs/CHANGES.md, 2026-11-15 TASK-063: resolution round; handoff/RESOLUTION-TASK-063.md)

CR = "\r"
PUSHF = "git push --force origin main"

ROUND2_HOLES = [
    ("double-quote-in-a-backtick-body", "echo " + BT + 'echo "x"' + BT + " ; " + WR),
    ("single-quote-in-a-backtick-body", "echo " + BT + "echo 'x'" + BT + " ; " + WR),
    ("substitution-in-a-backtick-body", "echo " + BT + "echo $(date +%Y)" + BT + " ; " + WR),
    ("nested-backtick", "echo " + BT + "echo " + BS + BT + WR + BS + BT + BT),
    ("escaped-substitution-in-a-backtick-body", 'echo "' + BT + "echo " + BS + "$(" + WR + ")" + BT + '"'),
    ("separator-after-a-heredoc-delimiter", "cat <<'EOF' ; " + WR + NL + "x" + NL + "EOF"),
    ("push-after-a-heredoc-delimiter", "cat <<'EOF' > m.txt && " + PUSHF + NL + "x" + NL + "EOF"),
    ("and-after-an-unquoted-heredoc-delimiter", "cat <<EOF && " + WR + NL + "x" + NL + "EOF"),
    ("apps-commit-form-with-an-apostrophe-then-a-push", "git commit -m \"$(cat <<'EOF'" + NL + "fix: don't crash" + NL + "EOF" + NL + ')"' + NL + PUSHF),
    ("apps-commit-form-with-a-paren-then-a-push", "git commit -m \"$(cat <<'EOF'" + NL + "fix: thing (see notes" + NL + "EOF" + NL + ')"' + NL + PUSHF),
    ("heredoc-operator-without-a-delimiter", WR + NL + "cat <<"),
    ("assignment-of-an-ansi-c-word", "X=$'1' " + WR),
    ("quoted-part-inside-a-flag", 'git push --fo"rce" origin $' + "'main'"),
    ("escaped-letter-in-a-subcommand", "git " + BS + "push --force origin $'main'"),
    ("quoted-part-inside-a-subcommand", 'git wo"rk"tree remove $' + "'../Worktrees/TASK-012'"),
    ("ansi-c-word-cut-at-a-nul", "git push $'--force" + BS + "x00x' origin main"),
    ("ansi-c-word-cut-at-an-octal-nul", "git push $'--force" + BS + "0x' origin main"),
    ("husky-before-bash-c-with-a-first-command", 'HUSKY=0 bash -c "true; git commit -m x"'),
    ("husky-before-eval-with-a-first-command", "HUSKY=0 eval 'true; git commit -m x'"),
    ("husky-before-cmd-c", "HUSKY=0 cmd /c git commit -m x"),
    ("husky-before-powershell-command", "HUSKY=0 powershell -Command git commit -m x"),
    ("husky-before-find-exec", "HUSKY=0 find . -maxdepth 0 -exec git commit -m x " + BS + ";"),
    ("husky-before-python-c", "HUSKY=0 python -c \"import os; os.system('git commit -m x')\""),
    ("husky-before-npx", "HUSKY=0 npx git commit -m x"),
    ("husky-before-coproc", "HUSKY=0 coproc git commit -m x"),
    ("husky-before-watch", "HUSKY=0 watch git push origin main"),
    ("lone-brace-in-a-parameter-expansion", "echo ${x:-{} ; " + WR),
    ("nested-parameter-expansions", "echo ${x:-${y:-$(true)}} ; " + WR),
    ("backtick-in-a-parameter-expansion", "echo ${x:-" + BT + WR + BT + "}"),
    ("the-word-case-in-an-argument", 'git log -1 "$(echo upper case in titles)" ; ' + WR),
    ("checkpoint-subject-from-another-command", "echo $(echo checkpoint before TASK-001) ; git commit --no-verify -F msg.txt"),
    ("shift-in-arithmetic-expansion", "echo $((1<<2)) ; " + WR),
    ("shift-in-an-arithmetic-command", "(( x = 1 << 2 )) ; " + WR),
    ("partly-quoted-heredoc-delimiter", "cat <<'E'OF" + NL + "hi" + NL + "EOF" + NL + WR),
    ("backslash-newline-in-a-quoted-heredoc-body", "cat <<'EOF'" + NL + "x " + BS + NL + "EOF" + NL + WR + NL + "EOF"),
    ("backslash-newline-in-a-comment", "echo a # c " + BS + NL + WR),
    ("backslash-newline-in-a-comment-inside-a-substitution", "echo $(echo a # c " + BS + NL + WR + ")"),
    ("backslash-newline-in-an-unquoted-heredoc-body", "cat <<EOF" + NL + "x " + BS + NL + "EOF" + NL + "'$(" + WR + ")'" + NL + "EOF"),
    ("comment-in-a-backtick-body-ends-at-its-line", "echo " + BT + "true # c" + NL + WR + BT),
    ("body-line-beginning-with-the-delimiter", "cat <<'EOF'" + NL + "EOF " + NL + "it's" + NL + "EOF" + NL + WR),
    ("shell-reading-a-heredoc-after-a-separator", "true ; bash <<'EOF'" + NL + WR + NL + "EOF"),
    ("shell-reading-a-heredoc-inside-a-substitution", "echo $(bash <<'EOF'" + NL + WR + NL + "EOF" + NL + ")"),
    ("heredoc-ending-at-a-delimiter-and-paren", "x=$(cat <<'EOF'" + NL + "hi" + NL + "EOF)" + NL + WR + NL + "EOF"),
    ("comment-after-a-subshell-paren-in-a-substitution", 'echo "$( (# it' + "'s" + NL + "true) ; " + WR + ' )"'),
    ("subshell-inside-a-double-quoted-substitution", 'echo "$( (true) ; ' + WR + ' )"'),
    ("leading-input-redirection", "</dev/null " + WR),
    ("leading-input-redirection-to-a-file", "<x " + WR),
    ("leading-read-write-redirection", "<>x " + WR),
    ("leading-output-redirection", ">out " + WR),
    ("substitution-in-a-redirection-target", 'echo x > "$(' + WR + ')"'),
    ("brace-expansion-of-a-flag", "git push origin main --{force,quiet}"),
    ("comment-with-an-apostrophe-before-gh-api", "echo # it's" + NL + "gh api repos/o/r/pulls?state=all&per_page=1"),
    ("many-unquoted-heredocs", WR + " ; " + NL.join("cat <<E%d" % k for k in range(1000)) + NL),
    ("many-nested-shell-heredocs", WR + NL + NL.join("bash <<'E%d'" % k for k in range(1000)) + NL + NL.join("E%d" % k for k in reversed(range(1000)))),
]


@pytest.mark.parametrize("command", [c for _, c in ROUND2_HOLES], ids=[n for n, _ in ROUND2_HOLES])
def test_r082_a_form_round_2_let_through_is_refused_within_the_hooks_time(plain, command):
    started = time.monotonic()
    refused(command, plain)
    assert time.monotonic() - started < HOOK_SECONDS


TIMED = [
    ("quoted-substitutions-in-parameter-expansions", "echo " + '${x:-"$(' * 3000 + "true" + ')"}' * 3000 + " ; " + WR),
    ("forty-thousand-newlines-in-a-substitution", 'echo "$(echo "<<x"' + NL * 40000 + ')" ; ' + WR),
    ("thirty-thousand-words-in-a-substitution", "echo $(echo" + " x" * 30000 + ") ; " + WR),
    ("fifteen-thousand-subshells-in-a-substitution", "echo $(" + "( " * 15000 + "true" + " )" * 15000 + ") ; " + WR),
]


@pytest.mark.parametrize("command", [c for _, c in TIMED], ids=[n for n, _ in TIMED])
def test_r082_a_long_command_is_refused_within_the_hooks_time(plain, command):
    started = time.monotonic()
    refused(command, plain)
    assert time.monotonic() - started < HOOK_SECONDS


UNREADABLE = [
    ("here-string", 'cat <<< "$(date)"'),
    ("substitution-in-a-parameter-expansion", 'echo "${x:-$(date)}"'),
    ("quote-in-a-parameter-expansion", 'echo ${x:-"a b"}'),
    ("tab-stripping-heredoc", "cat <<-EOF" + NL + TAB + "x" + NL + TAB + "EOF"),
    ("two-heredocs-on-one-line", "cat <<A <<B" + NL + "a" + NL + "A" + NL + "b" + NL + "B"),
    ("heredoc-inside-backticks", "echo " + BT + "cat <<'EOF'" + NL + "x" + NL + "EOF" + NL + BT),
    ("case-statement", "case x in x) echo y ;; esac"),
    ("arithmetic-expansion", "echo $((1+1))"),
    ("arithmetic-command", "(( x = 1 ))"),
    ("ansi-c-part-of-a-word", "git $'work'tree list"),
    ("locale-part-of-a-word", 'git $"work"tree list'),
    ("brace-expansion-with-a-range", "echo file{1..3}.txt"),
    ("named-descriptor-redirection", "exec {fd}>out.txt"),
    ("unclosed-double-quote", 'echo "abc'),
    ("unclosed-substitution", "echo $(git status"),
    ("nesting-past-the-bound", "echo " + "$(echo " * 200 + "x" + ")" * 200),
]


@pytest.mark.parametrize("command", [c for _, c in UNREADABLE], ids=[n for n, _ in UNREADABLE])
def test_r082_a_form_outside_the_read_subset_is_refused_as_unreadable_with_its_remedy(plain, command):
    """The guard reads a defined subset of the shell's grammar exactly; anything else it refuses, its reason
    saying it cannot read the command and naming the form."""
    err = refused(command, plain)
    assert "cannot read" in err.lower(), err


POWERSHELL_UNREADABLE = [
    ("backslash-before-a-quote", 'Get-ChildItem "C:' + BS + 'dir' + BS + '" ; git add -A ; echo "x"'),
    ("backtick-escaped-quote", 'echo "' + BT + '"" ; ' + WR),
    ("here-string", "$m = @'" + NL + "it's" + NL + "'@" + NL + WR),
    ("block-comment", "<# it's #> " + WR),
    ("lone-carriage-return", "git status" + CR + WR),
]


@pytest.mark.parametrize("command", [c for _, c in POWERSHELL_UNREADABLE], ids=[n for n, _ in POWERSHELL_UNREADABLE])
def test_r082_a_powershell_form_neither_reading_models_is_refused_under_powershell(workspace, command):
    rc, err = guard_tool(command, workspace, "PowerShell")
    assert rc == 2 and "refused" in err, (command, rc, err)


def test_r082_a_backtick_inside_a_word_is_refused_under_powershell(plain):
    """PowerShell reads a backtick inside a word as an escape (git pu`s`h is push): outside single quotes and
    not before a new line, the guard cannot read it."""
    rc, err = guard_tool("git pu" + BT + "s" + BT + "h --force origin main", plain, "PowerShell")
    assert rc == 2 and "refused" in err, (rc, err)


def test_r082_a_backslash_before_a_newline_is_no_continuation_under_powershell(plain):
    rc, err = guard_tool("Get-ChildItem C:" + BS + "temp" + BS + NL + WR, plain, "PowerShell")
    assert rc == 2 and "refused" in err, (rc, err)


def test_r082_a_powershell_wrapper_is_read_the_powershell_way_under_bash(plain):
    rc, err = guard_tool("powershell -Command 'Get-ChildItem \"C:" + BS + "dir" + BS + "\" ; " + WR + " ; echo \"x\"'", plain, "Bash")
    assert rc == 2 and "refused" in err, (rc, err)


def test_r082_gh_api_with_an_option_before_api_and_an_unquoted_ampersand_is_refused_with_its_remedy(plain):
    err = refused("gh -R o/r api repos/o/r/pulls?state=all&per_page=1", plain)
    assert "quote" in err.lower(), err


SUBSET_PASSES = [
    ("stderr-to-stdout", "git status 2>&1"),
    ("stdout-to-stderr", "echo error >&2"),
    ("append-redirection", "echo x >> notes.txt"),
    ("reflog-brace-word", "git log -1 HEAD@{1}"),
    ("find-exec-braces", "find . -name x -exec echo {} +"),
    ("escaped-ampersand-in-a-quoted-gh-api-endpoint", "gh api 'repos/o/r/pulls?state=all'" + BS + "&per_page=1"),
    ("redirection-before-the-command", "2>/dev/null git status"),
]


@pytest.mark.parametrize("command", [c for _, c in SUBSET_PASSES], ids=[n for n, _ in SUBSET_PASSES])
def test_r082_a_form_inside_the_read_subset_passes(plain, command):
    passes(command, plain)


# Forms the first resolution round's subset read: unreadable under the flat grammar.
SUBSET_BEFORE_THE_FLAT_GRAMMAR = [
    ("brace-group", "{ git status; }"),
    ("unquoted-question-mark-in-a-gh-api-endpoint", "gh api repos/o/r/pulls?state=all" + BS + "&per_page=1"),
    ("graphql-then-another-substitution", "gh api graphql -f query='{viewer{login}}' ; echo $(date)"),
    ("whole-word-ansi-c-string", "echo $'a" + BS + "tb'"),
    ("substitution-whose-body-chains-nothing", 'git commit -m "$(echo a; echo b)"'),
    ("continued-pr-create-with-a-heredoc-body", 'gh pr create --title "TASK-063 guard" ' + BS + NL + "  --body \"$(cat <<'EOF'" + NL + "## Summary" + NL + "it's done" + NL + "EOF" + NL + ')"'),
    ("heredoc-body-holding-gh-api-words", "cat > notes.md <<'EOF'" + NL + "run gh api repos/o/r/pulls?a=1&b=2" + NL + "EOF"),
]


@pytest.mark.parametrize("command", [c for _, c in SUBSET_BEFORE_THE_FLAT_GRAMMAR], ids=[n for n, _ in SUBSET_BEFORE_THE_FLAT_GRAMMAR])
def test_r082_a_form_the_first_subset_read_is_refused_as_unreadable_in_a_workspace(workspace, command):
    err = refused(command, workspace)
    assert "cannot read" in err.lower(), err


def test_r082_the_continued_pr_create_with_a_body_file_passes_in_a_workspace(workspace):
    """A backslash-newline outside quotes joins the lines: the continued form the bridge's agents write."""
    passes('gh pr create --title "TASK-063 guard" ' + BS + NL + "  --body-file run/supervisor/pr-body.md", workspace)


def test_r082_a_backslash_before_a_quote_is_no_escape_under_powershell(plain):
    """PowerShell has no backslash escape: "C:\\dir\\" closes at its last quote and the removal after it runs."""
    rc, err = guard_tool('Get-ChildItem "C:' + BS + 'dir' + BS + '" ; ' + WR + ' ; echo "done"', plain, "PowerShell")
    assert rc == 2 and "refused" in err, (rc, err)


def test_r082_a_backtick_before_a_newline_continues_the_line_under_powershell(plain):
    rc, err = guard_tool("git status " + BT + NL + "  --short", plain, "PowerShell")
    assert rc == 0, (rc, err)


# ---------------------------------------------------------------- a long command, read within the hook's time

@pytest.mark.parametrize("command", [
    "echo " + "word " * 2000,
    'echo "' + BS * 9994 + '"',
    "echo " + ("'a' \"b\" c" + BS + "d ") * 850,
], ids=["words", "backslashes", "mixed-quotes"])
def test_r082_a_command_of_ten_thousand_characters_is_read_within_the_hooks_time(plain, command):
    assert len(command) >= 10000
    started = time.monotonic()
    passes(command, plain)
    assert time.monotonic() - started < HOOK_SECONDS


# ---------------------------------------------------------------- round 4's pre-launch read: holes on round 3's tree
# (handoff/TASK-063-r4.md, requirements 2 and 11)

@pytest.mark.parametrize("command", [
    "git push --force origin $(echo main)",
    "gh pr merge 12 --squash --body $(cat x)",
], ids=["force-push-with-a-substitution-argument", "merge-with-a-substitution-argument"])
def test_r082_a_refused_command_with_an_unquoted_substitution_argument_is_still_refused(plain, command):
    """A command's words come from the reading itself: a command whose text holds an unquoted `$(` is checked
    like any other (the checkpoint fae0860 refuses both)."""
    refused(command, plain)


def test_r082_a_powershell_wrapper_leaves_the_rest_of_the_line_read_the_bash_way(plain):
    """The PowerShell reading of a wrapper's inner command ends with it: under the Bash tool, a backslash after the
    wrapper is still an escape, and `--fo\\rce` is `--force`."""
    rc, err = guard_tool("pwsh -Command echo ; git push --fo" + BS + "rce origin main", plain, "Bash")
    assert rc == 2 and "refused" in err, (rc, err)


# ---------------------------------------------------------------- after the second resolution round: the flat grammar
# (docs/CHANGES.md, 2026-11-15 TASK-063: second resolution round; handoff/RESOLUTION-TASK-063-2.md). The forms are
# round 4's findings (Review A B1 to B15, the security audit S1 to S10) and the holes both reviewers' votes found.

B64 = "ZQBjAGgAbwA="   # an encoded PowerShell command (echo)
ENDASH = "–"
LSQ = "‘"
RSQ = "’"

FLAT_UNREADABLE = [
    # a $ anywhere outside single quotes
    ("variable-in-the-command-place-after-an-assignment", "cmd=git; $cmd push --force origin main"),
    ("variable-holding-a-flag", 'flag=--force; git push "$flag" origin main'),
    ("substitution-in-an-assignment-before-a-merge", "GH_TOKEN=$(cat t) gh pr merge 12 --squash"),
    ("substitution-as-a-git-option-value", "git -C $(git rev-parse --show-toplevel) push --force origin main"),
    ("arithmetic-inside-a-substitution", "echo $(echo $((1)); " + WR + ")"),
    ("locale-string-holding-a-substitution", 'echo $"$(' + WR + ')"'),
    ("ansi-c-control-escape", "git push $'--force" + BS + "c@x' origin main"),
    ("variable-in-a-redirection-target", "git worktree 2>$(mktemp) remove ../Worktrees/TASK-012"),
    # here-documents
    ("unreadable-body-a-shell-reads", "bash <<'EOF'" + NL + "case x in x) " + WR + ";; esac" + NL + "EOF"),
    ("body-a-shell-reads-seventy-deep", NL.join("bash <<'E%d'" % k for k in range(70)) + NL + WR + NL + NL.join("E%d" % k for k in reversed(range(70)))),
    ("quoted-substitution-in-an-unquoted-body", "cat <<EOF" + NL + "'$(" + WR + ")'" + NL + "EOF"),
    ("heredoc-piped-to-a-shell-by-its-holder", "bash <<'EOF' | cat" + NL + WR + NL + "EOF"),
    ("redirection-before-a-shell-reading-a-heredoc", "<<'EOF' bash" + NL + WR + NL + "EOF"),
    ("delimiter-with-trailing-blank", "cat <<'EOF'" + NL + "EOF " + NL + "it's" + NL + "EOF" + NL + WR + NL + "#'"),
    # parentheses, braces, globs
    ("brace-group-around-a-removal", "{ git worktree remove /tmp/wt; }"),
    ("brace-group-around-a-force-push", "{ git push --force origin main; }"),
    ("subshell-holding-a-newline-chain", "(git add -A" + NL + "git commit -m x)"),
    ("glob-question-mark-in-a-flag", "git push --forc? origin main"),
    ("glob-bracket-in-a-flag", "git push -[-]force origin main"),
    ("glob-bracket-in-the-command-name", "/usr/bin/gi[t] push --force origin main"),
    ("glob-star", "git add *.py"),
    ("brace-expansion-with-a-prefix", "git push --{force,x} origin main"),
    ("brace-expansion-with-an-empty-member", "git push {,-}-force origin main"),
    ("brace-expansion-with-a-range", "echo x{a..c}y"),
    # builtins and reserved words as a command word
    ("coproc", "coproc git worktree remove /tmp/wt"),
    ("let-evaluating-a-subscript", "let 'x=a[$(" + WR + ")0]'"),
    ("declare-evaluating-a-subscript", "declare 'b[$(" + WR + ")0]=1'"),
    ("trap", "trap 'git push --force origin main' EXIT"),
    ("alias-then-its-name", "alias g=git" + NL + "g push --force origin main"),
    ("hash-rebinding-a-name", "hash -p /usr/bin/git g"),
    ("export-husky-then-a-commit", "export HUSKY=0" + NL + "git commit -m x"),
    ("source-from-stdin", "source /dev/stdin"),
    ("printf-assigning-a-variable", "printf -v x '%s' y"),
    ("a-for-loop", "for b in main dev; do git push --force origin main; done"),
    ("an-if-statement", "if true; then git push --force origin main; fi"),
    ("negation", "! git push --force origin main"),
    # wrappers and launchers that read their command from elsewhere
    ("xargs-appending-a-flag", "echo --force | xargs git push origin main"),
    ("shell-reading-stdin-in-a-pipeline", "echo 'git push --force origin main' | bash"),
    ("shell-reading-stdin-from-a-file", "bash < script.sh"),
    ("env-split-string", "env -S 'git push --force origin main'"),
    ("interactive-bash", "bash -i -c 'git status'"),
    ("zsh", "zsh -c 'git status'"),
    ("git-bash-start", "start git push --force origin main"),
    ("wsl", "wsl git push --force origin main"),
    ("mintty", "mintty -e git push --force origin main"),
    ("git-config-environment-variables", "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null git commit -m x"),
    ("git-config-env-option", "git --config-env=core.hooksPath=HOOKS commit -m x"),
    ("cmd-inner-command-with-a-percent-variable", 'F=--force cmd //c "git push %F% origin main"'),
    ("cmd-switch-glued-to-its-command", "cmd /cgit worktree remove ../Worktrees/TASK-012"),
    ("cmd-delayed-expansion-switch", "cmd //v:on //c git status"),
    # the rest
    ("redirection-without-a-target", "git status >"),
    ("unclosed-single-quote", "echo 'abc"),
]


@pytest.mark.parametrize("command", [c for _, c in FLAT_UNREADABLE], ids=[n for n, _ in FLAT_UNREADABLE])
def test_r082_a_form_outside_the_flat_grammar_is_refused_as_unreadable(plain, command):
    started = time.monotonic()
    err = refused(command, plain)
    assert "cannot read" in err.lower(), err
    assert time.monotonic() - started < HOOK_SECONDS


FLAT_REFUSED = [
    ("backslash-newline-inside-double-quotes-joins", 'git push "--for' + BS + NL + 'ce" origin main'),
    ("backslash-newline-outside-quotes-joins", "git push --for" + BS + NL + "ce origin main"),
    ("quoted-redirection-target-before-the-command", '>"out" ' + WR),
    ("quoted-redirection-target-inside-the-command", 'git worktree >"x" remove ../Worktrees/TASK-012'),
    ("help-as-a-redirection-target-is-no-help-call", "git push --force origin main >'--help'"),
    ("h-as-a-redirection-target-is-no-help-call", 'git worktree remove ../Worktrees/TASK-012 2>"-h"'),
    ("help-target-after-a-merge", "gh pr merge 12 --squash >'--help'"),
    ("exec-with-a-name-option", "exec -a x git push --force origin main"),
    ("stdbuf-with-a-buffer-option", "stdbuf -o L git push --force origin main"),
    ("pipe-and-stderr-separator", "git status |& " + WR),
    ("cmd-inner-command", "cmd //c git worktree remove ../Worktrees/TASK-012"),
    ("cmd-inner-command-by-its-r-switch", "cmd //r git worktree remove ../Worktrees/TASK-012"),
    ("encoded-powershell-by-a-short-switch", "powershell -en " + B64),
    ("encoded-powershell-by-a-double-slash", "powershell //enc " + B64),
    ("encoded-powershell-by-an-en-dash", "powershell " + ENDASH + "enc " + B64),
    ("graphql-query-from-a-file-after-a-method", "gh api -X POST graphql -F query=@q.graphql"),
    ("graphql-query-from-a-file-after-a-long-method", "gh api --method POST graphql -F query=@q.graphql"),
]


@pytest.mark.parametrize("command", [c for _, c in FLAT_REFUSED], ids=[n for n, _ in FLAT_REFUSED])
def test_r082_a_refused_command_in_a_flat_form_is_refused(plain, command):
    refused(command, plain)


@pytest.mark.parametrize("command", [
    "FOO=bar && git push --force origin main",
    "X=1 ; " + WR,
    "REPO=o/r; gh pr merge 12 --repo o/r --squash",
], ids=["assignment-then-and", "assignment-then-semicolon", "assignment-then-merge"])
def test_r082_an_assignment_before_a_chain_is_refused_without_a_crash_in_a_workspace(workspace, command):
    """Round 4 raised IndexError on these (exit 1, the hook's fail-open path)."""
    refused(command, workspace)


def test_r082_a_bash_wrapper_is_read_the_bash_way_under_powershell(plain):
    rc, err = guard_tool("bash -c 'git push --fo" + BS + "rce origin main'", plain, "PowerShell")
    assert rc == 2 and "refused" in err, (rc, err)


POWERSHELL_FLAT_UNREADABLE = [
    ("parenthesised-command", "Write-Output (" + WR + ")"),
    ("array-subexpression", "@(" + WR + ")"),
    ("cast-of-a-parenthesised-command", "[void](" + WR + ")"),
    ("call-of-a-parenthesised-name", "& ('git') worktree remove ../Worktrees/TASK-012"),
    ("script-block-after-a-call", "& { git worktree remove /tmp/wt }"),
    ("assignment", "$x = " + WR),
    ("iex", "iex '" + WR + "'"),
    ("invoke-expression", "Invoke-Expression '" + WR + "'"),
    ("module-qualified-invoke-expression", "Microsoft.PowerShell.Utility" + BS + "Invoke-Expression '" + WR + "'"),
    ("foreach-alias-with-a-block", "1 | % { git worktree remove /tmp/wt }"),
    ("backtick-inside-double-quotes", 'git push "--f' + BT + 'or' + BT + 'ce" origin main'),
    ("splatting", "Set-Variable a push,--force; git @a"),
    ("stop-parsing-token", "git --% push --force origin main"),
    ("start-alias", "start git 'push'"),
    ("set-alias-then-its-name", "Set-Alias g git" + NL + "g push --force origin main"),
    ("typographic-quotes", "git push " + LSQ + "--force" + RSQ + " origin main"),
    ("a-cmdlet-outside-the-read-set", "Remove-Item -Recurse docs"),
]


@pytest.mark.parametrize("command", [c for _, c in POWERSHELL_FLAT_UNREADABLE], ids=[n for n, _ in POWERSHELL_FLAT_UNREADABLE])
def test_r082_a_powershell_form_outside_the_flat_grammar_is_refused_as_unreadable(plain, command):
    rc, err = guard_tool(command, plain, "PowerShell")
    assert rc == 2 and "cannot read" in err.lower(), (command, rc, err)


FLAT_PASSES = [
    ("the-word-case-as-an-argument", "grep -n case src/app.py"),
    ("git-with-a-folder", "git -C ../Worktrees/TASK-063 status"),
    ("gh-pr-checks", "gh pr checks 12 --watch"),
    ("python-script", "python run/supervisor/x.py a b"),
    ("commit-from-a-file", "git commit -q -F run/msg.txt"),
    ("log-format-percent", "git log --format=%H"),
    ("revision-suffixes", "git diff HEAD~1 HEAD^ -- docs/"),
    ("stash-reflog-brace", "git stash show stash@{0}"),
    ("gh-api-placeholders", "gh api repos/{owner}/{repo}/pulls/12"),
    ("upstream-brace", "git rev-parse @{u}"),
    ("tilde", "ls ~/.claude/cursor-bridge"),
    ("escaped-quotes-in-double-quotes", 'echo "a ' + BS + '"quoted' + BS + '" word"'),
    ("pipe-and-stderr", "git status |& cat"),
    ("an-assignment-alone", "X=1"),
    ("an-assignment-before-a-command", "X=1 git status"),
    ("printf-with-a-format", "printf '%s" + BS + "n' a"),
    ("type-and-pwd", "type git"),
    ("redirections-after-the-command", "git push origin main 2>/dev/null >out.txt"),
    ("a-comment-holding-a-substitution", "echo hi # $(" + WR + ")"),
    ("single-quoted-graphql-text", "gh api graphql -f query='$(x)'"),
    ("bash-c-wrapper", "bash -c 'git status'"),
    ("env-with-an-unset-option", "env -u FOO git status"),
    ("timeout-wrapper", "timeout 60 git fetch"),
    ("cmd-inner-command", "cmd //c dir"),
    ("powershell-inner-cmdlet", "powershell -Command Get-ChildItem"),
]


@pytest.mark.parametrize("command", [c for _, c in FLAT_PASSES], ids=[n for n, _ in FLAT_PASSES])
def test_r082_a_form_inside_the_flat_grammar_passes(plain, command):
    passes(command, plain)


POWERSHELL_FLAT_PASSES = [
    ("cmdlet", "Get-ChildItem docs"),
    ("native-program", "git status"),
    ("cmdlet-pipeline", "Get-Content README.md | Select-String TODO"),
    ("test-path", "Test-Path docs"),
    ("alias-into-the-read-set", "ls docs"),
    ("cd-alias", "cd docs"),
    ("gh-pr-checks", "gh pr checks 12 --watch"),
    ("call-operator-before-a-native-program", "& git status"),
]


@pytest.mark.parametrize("command", [c for _, c in POWERSHELL_FLAT_PASSES], ids=[n for n, _ in POWERSHELL_FLAT_PASSES])
def test_r082_a_powershell_form_inside_the_flat_grammar_passes(plain, command):
    rc, err = guard_tool(command, plain, "PowerShell")
    assert rc == 0, (command, rc, err)


@pytest.mark.parametrize("command", [
    "echo " + "{" * 100000 + " ; " + WR,
    " ; ".join("git commit -q -F m%d.txt" % k for k in range(1000)) + " ; " + WR,
    "echo " + "x " * 30000 + "; " + WR,
], ids=["a-hundred-thousand-braces", "a-thousand-commits", "thirty-thousand-words"])
def test_r082_a_long_flat_command_is_refused_within_the_hooks_time(plain, command):
    started = time.monotonic()
    refused(command, plain)
    assert time.monotonic() - started < HOOK_SECONDS


# ---------------------------------------------------------------- round 5's pre-launch read (Review A): forms the brief now names

@pytest.mark.parametrize("command", [
    "bash -c -x 'git push --force origin main'",
    "bash +x -c 'git push --force origin main'",
    "find . -maxdepth 0 -exec true " + BS + "; -exec git push --force origin main " + BS + ";",
    "winpty git push --force origin main",
], ids=["bash-option-after-c", "bash-plus-option-before-c", "find-second-exec-clause", "winpty"])
def test_r082_a_refused_command_behind_a_wrapper_read_in_full_is_refused(plain, command):
    refused(command, plain)


@pytest.mark.parametrize("command", [
    "dash -c 'echo hi'",
    "cmd //c call git push --force origin main",
    "cmd //c set X=1",
], ids=["dash", "cmd-call", "cmd-set"])
def test_r082_a_wrapper_the_flat_grammar_does_not_read_is_refused_as_unreadable(plain, command):
    err = refused(command, plain)
    assert "cannot read" in err.lower(), err


@pytest.mark.parametrize("command", [
    "wsl git push --force origin main",
    "git push origin#x --force",
], ids=["wsl-under-powershell", "hash-inside-a-word-is-no-comment"])
def test_r082_a_refused_command_is_refused_under_powershell(plain, command):
    rc, err = guard_tool(command, plain, "PowerShell")
    assert rc == 2 and "refused" in err, (command, rc, err)
