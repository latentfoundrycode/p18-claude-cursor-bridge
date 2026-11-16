"""permission-guard.py (release A4, 13.1 and the 2026.10.06a review's S2): inside a bridge Workspace a
chain of commands carrying a state-changing git or gh command, or a command wrapped in cd, is
refused (rule 8); a commit that skips its checks is refused; a wrapper's quoted string is read."""
import json
import os
import subprocess
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py")


def run(command, cwd=None, tool="Bash"):
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto"}
    if cwd:
        payload["cwd"] = str(cwd)
    p = subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stderr


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("command", [
    "git add -A && git commit -m 'TASK-001' && git push",
    "git add -A; git commit -m x",
    "cd ../Worktrees/TASK-001 && git commit -am x",
    "cd src && python build.py",
    "git switch main || git checkout main",
    "bash -c 'git add -A && git commit -m x'",
    "gh pr create -t x -b y && gh pr merge 5 --match-head-commit abc",
])
def test_a_chain_carrying_a_state_change_is_refused_inside_a_workspace(workspace, command):
    rc, err = run(command, workspace)
    assert rc == 2 and "rule 8" in err, (command, err)


@pytest.mark.parametrize("command", [
    "git log --oneline | head -5",
    "git status --porcelain && git diff --stat",
    "python -m pytest tests -q",
    "python a.py && python b.py",
    "gh pr view 5 --json state && gh pr checks 5",
])
def test_reading_chains_and_plain_commands_pass(workspace, command):
    rc, err = run(command, workspace)
    assert rc == 0, (command, err)


def test_outside_a_workspace_chains_are_not_the_guards_business(tmp_path):
    rc, err = run("git add -A && git commit -m x", tmp_path)
    assert rc == 0, err


@pytest.mark.parametrize("command", [
    "git commit --no-verify -m x",
    "git commit -n -m x",
    "git -c core.hooksPath=/dev/null commit -m x",
    "git push --no-verify origin task-001",
    "powershell -Command \"git commit --no-verify -m x\"",
    "git commit --no-verify -m \"$(cat <<'EOF'\ncheckpoint before TASK-003\n\nthe tree as delegated\nEOF\n)\"",
])
def test_a_commit_that_skips_its_checks_is_refused(tmp_path, command):
    rc, err = run(command, tmp_path)
    assert rc == 2 and ("skips its checks" in err or "hooksPath" in err or "cannot read" in err.lower()), (command, err)


@pytest.mark.parametrize("command", [
    "git push -n origin task-001",
    'git commit --no-verify -m "checkpoint before TASK-001"',
    'git commit --no-verify --message="checkpoint before TASK-001"',
    'git -C ../Worktrees/TASK-001 commit --no-verify -m "TASK-001 builder hand-off"',
    'git commit --no-verify -m "checkpoint before TASK-105 (brief handoff/TASK-105.md)"',
    'git commit --no-verify -m "checkpoint before TASK-159 r2 (round 1 builder output, scope clean)"',
    'git commit --no-verify -m "checkpoint: roster re-resolved before TASK-159 r3"',
    'git commit --no-verify -m "checkpoint: TASK-059e round-5 builder work"',
    'git commit --no-verify -m "checkpoint before CONFIG-001a"',
    'git commit --no-verify -m "checkpoint before TASK-159 r3 (round 2 builder output; frozen acceptance tests kept)"',
    'git commit --no-verify -m "TASK-010c round 3 checkpoint (status after TASK-059b merge)"',
    'git commit --no-verify -m "BUG-022: round-2 brief, one spend-record snapshot per raise (checkpoint)"',
    'git commit --no-verify -m "checkpoint before FIX-next-sharp: roster resolved"',
    'git commit --no-verify -m "checkpoint (paused by owner): TASK-141-r2 builder work - junction guard"',
    'git commit --no-verify -m "checkpoint before TASK-057 round 3: reproductions of the overlay-merge finding (red)"',
    'git commit --no-verify -m "checkpoint: TASK-056a merged (PR #17 @ 0f99ae1); correct PROJECT_STATUS drift; resume at TASK-056b"',
    "git config core.hooksPath .githooks && git branch -r --contains abc1234",
    'git branch --list "task-*" && git status',
])
def test_the_snapshots_the_policy_allows_and_a_dry_run_pass(tmp_path, command):
    """The pre-delegation checkpoint (its exact subject, in any of the app's commit forms) and a builder's hand-off
    snapshot inside a worktree may skip the hook (merge policy); the accept commit on top runs it."""
    rc, err = run(command, tmp_path)
    assert rc == 0, (command, err)


@pytest.mark.parametrize("command", [
    'git commit -n -m "checkpoint: accept TASK-003 with the increment"',
    'git commit -n -m "TASK-003 accept, hand-off to review"',
    'git commit --no-verify -m "TASK-001 builder hand-off"',
    "HUSKY=0 git commit -m x",
    "git config core.hooksPath /dev/null",
    "git config --unset core.hooksPath",
    "git config core.hooksPath ../elsewhere",
    "git commit -n -m \"accept TASK-003\" -m \"$(cat <<'EOF'\ncheckpoint before TASK-003\nEOF\n)\"",
    'git commit --no-verify -m "checkpoint: merge TASK-003 to main"',
    "git commit -n -m \"$(cat <<'EOF'\naccept TASK-003\nEOF\n)\" -m \"checkpoint before TASK-003\"",
    "git config core.hooksPath ~/elsewhere",
    'git commit --no-verify -m "G-7e: since-the-last-learning-run checkpoint (frozen test, RED)"',
    'git commit --no-verify -m "checkpoint: restore HARDENING text lost to shell backtick substitution"',
    "git config core.hooksPath .githooks/../../elsewhere",
])
def test_the_words_alone_do_not_open_the_exemption(tmp_path, command):
    """First pass, F6 and F14: the exemption is the policy's exact subject, the hand-off only inside a worktree;
    the hook runner's own switches are refused too."""
    rc, err = run(command, tmp_path)
    assert rc == 2, (command, err)


@pytest.mark.parametrize("command", [
    'gh pr create --title "TASK-003 parser" \\\n  --body "text"',
    'git commit -m "x" \\\n  -m "y"',
    "git branch --show-current && git status --short",
    "git worktree list && git status",
    "git stash list && git status",
    "git tag -l && git fetch origin",
    "git config core.hooksPath .githooks",
])
def test_continued_lines_and_read_forms_pass(workspace, command):
    """First pass, F5 and F13: a line continued with a backslash is one command; the read forms of branch, stash,
    worktree, tag and fetch are reads."""
    rc, err = run(command, workspace)
    assert rc == 0, (command, err)


@pytest.mark.parametrize("command", [
    "git add -A & git commit -m x",
    "(git add -A) && (git commit -m x)",
    'eval "git add -A && git commit -m x"',
    "git status && git stash",
    "git remote add x https://example.invalid/r.git && git status",
])
def test_the_remaining_chain_spellings_are_refused(workspace, command):
    """First pass, F14: a single &, parentheses and eval do not hide a chain."""
    rc, err = run(command, workspace)
    assert rc == 2 and ("rule 8" in err or "cannot read" in err.lower()), (command, err)


@pytest.mark.parametrize("command", [
    'cmd /c "git push --force origin main"',
    'powershell -Command "git push --force origin main"',
    'bash -c "git push -f origin main"',
    "bash -lc 'git worktree remove ../Worktrees/x'",
])
def test_a_wrappers_quoted_string_is_read(tmp_path, command):
    rc, err = run(command, tmp_path)
    assert rc == 2, (command, err)


def _run_r082(command, cwd=None, tool="Bash"):
    """R-082 builder cases: hook JSON, windowless subprocess, bounded wait."""
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto"}
    if cwd:
        payload["cwd"] = str(cwd)
    return subprocess.run(
        [sys.executable, PROG],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=120,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def test_r082_checkpoint_commit_form_with_no_verify_passes_in_a_workspace(workspace):
    """R-082 (req 11a): flat grammar refuses the app heredoc commit form as unreadable."""
    command = 'git commit --no-verify -m "$(cat <<\'EOF\'\ncheckpoint before TASK-003\n\nthe tree as delegated\nEOF\n)"'
    p = _run_r082(command, workspace)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), (command, p.stderr)


def test_r082_unquoted_ampersand_in_gh_api_is_refused_in_a_workspace(workspace):
    """R-082 (req 11b): an unquoted & in a gh api argument is refused with a quoting remedy in a Workspace."""
    command = "gh api repos/o/r/pulls?state=all&per_page=1"
    p = _run_r082(command, workspace)
    assert p.returncode == 2 and "quote" in p.stderr.lower(), (command, p.stderr)


@pytest.mark.parametrize("command,expect", [
    ('git commit -m x --message="--no-verify"', 0),
    ("git commit -m x --no-verify", 2),
])
def test_r082_no_verify_after_message_is_not_the_message_value(tmp_path, command, expect):
    """R-082 (req 11c): --no-verify in a message value passes; as an option after -m it is refused."""
    p = _run_r082(command, tmp_path)
    assert p.returncode == expect, (command, p.stderr)


def test_r082_env_husky_zero_before_git_push_is_refused(tmp_path):
    """R-082 (req 11d): env HUSKY=0 git push is refused like a leading HUSKY=0 assignment."""
    p = _run_r082("env HUSKY=0 git push origin task-012", tmp_path)
    assert p.returncode == 2 and "HUSKY" in p.stderr, p.stderr


WR = "git worktree remove ../Worktrees/TASK-012"
BT = "`"
NL = "\n"


@pytest.mark.parametrize("command", [
    "git cherry-pick -m 1 --no-verify 0123abc",
    "git commit -F msg.txt --no-verify",
    "git push $'\\x2d\\x2dforce' origin main",
    "git push $'\\055\\055force' origin main",
    "echo " + BT + WR + BT,
    "echo " + BT + "# c` ; " + WR + BT,
    'echo "$( (true) ; ' + WR + ')"',
    "echo ${x:- #} ; " + WR,
    "cat <<EOF" + NL + "$(" + WR + ")" + NL + "EOF",
    "HUSKY=0 setsid git commit -m x",
])
def test_r082_req14_refused_forms(tmp_path, command):
    """R-082 requirement 14: builder refusal cases the acceptance file does not name."""
    p = _run_r082(command, tmp_path)
    assert p.returncode == 2, (command, p.returncode, p.stderr)


def test_r082_req14_powershell_wrapper_refuses_worktree(tmp_path):
    """R-082 requirement 14: a powershell -Command string is read under the PowerShell tool."""
    command = 'powershell -Command \'Get-ChildItem "C:\\dir\\" ; ' + WR + ' ; echo "x"\''
    p = _run_r082(command, tmp_path, tool="PowerShell")
    assert p.returncode == 2, (command, p.returncode, p.stderr)


def test_r082_req14_nesting_past_the_read_bound_is_refused(tmp_path):
    """R-082 requirement 5: nesting past the reader bound refuses with a depth reason."""
    command = "$(" * 70 + "true" + ")" * 70 + " ; " + WR
    p = _run_r082(command, tmp_path)
    assert p.returncode == 2 and ("nest" in p.stderr.lower() or "cannot read" in p.stderr.lower()), (command, p.stderr)


@pytest.mark.parametrize("command", [
    "gh api graphql -f query='$(x)'",
])
def test_r082_req14_passing_forms(tmp_path, command):
    """R-082 requirement 14: deliberate passes called out in the brief."""
    p = _run_r082(command, tmp_path)
    assert p.returncode == 0, (command, p.stderr)


def test_r082_req14_heredoc_form_is_refused(tmp_path):
    """R-082 requirement 14: a here-document is unreadable under the flat grammar."""
    command = "cat <<'EOF'" + NL + "$(" + WR + ")" + NL + "EOF"
    p = _run_r082(command, tmp_path)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), (command, p.stderr)


def test_r082_req14_cd_in_substitution_is_not_rule8_refusal(workspace):
    """R-082 requirement 14: a substitution is unreadable under the flat grammar."""
    command = 'echo "$(cd "$(dirname "$0")" && pwd)"'
    p = _run_r082(command, workspace)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), (command, p.stderr)


def test_r082_cmd_words_from_reader_not_a_second_scan(tmp_path):
    """R-082 (req 1): a cut simple command is checked with the reader's word list, not an empty re-read."""
    p = _run_r082('gh pr merge 12 --squash --body $(cat x)', tmp_path)
    assert p.returncode == 2 and ("match-head-commit" in p.stderr or "cannot read" in p.stderr.lower()), p.stderr


def test_r082_backslash_newline_in_comment_does_not_hide_next_command(tmp_path):
    """R-082 (req 2): backslash-newline in a comment leaves the next physical line as its own command."""
    p = _run_r082("echo a # c \\\n" + WR, tmp_path)
    assert p.returncode == 2, (p.returncode, p.stderr)


def _run_r6(command, cwd=None, tool="Bash"):
    """R-082 round 6 cases: one subprocess line, windowless, bounded wait."""
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto"}
    if cwd:
        payload["cwd"] = str(cwd)
    return subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


_R6_WRAPPERS = [
    ("env", "env FOO=bar git status", "env --foo git status"),
    ("nice", "nice -n 5 git status", "nice --foo git status"),
    ("nohup", "nohup git status", "nohup --foo git status"),
    ("stdbuf", "stdbuf -o0 git status", "stdbuf --foo git status"),
    ("timeout", "timeout 5 git status", "timeout --foo 5 git status"),
    ("setsid", "setsid git status", "setsid --foo git status"),
    ("sudo", "sudo -u root git status", "sudo --foo git status"),
    ("exec", "exec git status", "exec --foo git status"),
    ("command", "command git status", "command --foo git status"),
    ("builtin", "builtin echo hi", "builtin let x=1"),
    ("eval", "eval git status", "eval \"git worktree remove y\""),
    ("bash", "bash -c 'git status'", "bash --foo -c 'git status'"),
    ("sh", "sh -c 'git status'", "sh -i -c 'git status'"),
    ("cmd", "cmd //c git status", "cmd /v git status"),
    ("powershell", "powershell -NoProfile -Command git status", "powershell -Foo -Command git status"),
    ("find", "find . -exec echo hi {} ;", "find . -exec git worktree remove z \\;"),
]


@pytest.mark.parametrize("label,ok,bad", _R6_WRAPPERS, ids=[row[0] for row in _R6_WRAPPERS])
def test_r082_wrapper_one_pass_and_one_refusal(label, ok, bad):
    """R-082 (req 16): each prefix wrapper has one command that passes and one that is refused."""
    passed = _run_r6(ok)
    assert passed.returncode == 0, (label, ok, passed.stderr)
    refused = _run_r6(bad)
    assert refused.returncode == 2, (label, bad, refused.stderr)


def test_r082_req1_empty_quotes_are_a_word():
    """R-082 (req 1): '' is a word, so a hash after it is not a comment and an empty -C value is kept."""
    hidden = _run_r6("printf ''#x ; git worktree remove z")
    assert hidden.returncode == 2 and "worktree" in hidden.stderr, hidden.stderr
    empty = _run_r6("git -C '' status")
    assert empty.returncode == 0, empty.stderr


def test_r082_req2_backslash_newline_removes_one_newline():
    """R-082 (req 2): a backslash and one newline join; the next newline is a separator."""
    p = _run_r6("printf ab\\\n\ngit worktree remove z")
    assert p.returncode == 2 and "worktree" in p.stderr, p.stderr


def test_r082_req3_redirection_target_is_the_next_word():
    """R-082 (req 3): a quoted redirection target is one word and is taken out."""
    p = _run_r6("git >'a b' worktree remove z")
    assert p.returncode == 2 and "worktree" in p.stderr, p.stderr


def test_r082_req4_named_descriptor_is_unreadable():
    """R-082 (req 4): a word that is only {name} directly before < or > is unreadable."""
    p = _run_r6("{out}>file git worktree remove z")
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_req5_prefix_chain_reaches_the_command_word():
    """R-082 (req 5): nice then env are prefixes; the command word is still git."""
    p = _run_r6("nice -n 1 env git worktree remove z")
    assert p.returncode == 2 and "worktree" in p.stderr, p.stderr


def test_r082_req6_exe_stem_keeps_the_shim_name():
    """R-082 (req 6): strace.exe is the launcher strace; cursor-agent.exe is still the shim name."""
    launcher = _run_r6("strace.exe git status")
    assert launcher.returncode == 2 and "cannot read" in launcher.stderr.lower(), launcher.stderr
    shim = _run_r6("cursor-agent.exe")
    assert shim.returncode == 2 and "shim" in shim.stderr, shim.stderr


def test_r082_req7_complete_and_proc_stdin_are_unreadable():
    """R-082 (req 7): complete is a refused builtin and sh /proc/... reads a descriptor."""
    complete = _run_r6("complete -p")
    assert complete.returncode == 2 and "cannot read" in complete.stderr.lower(), complete.stderr
    proc = _run_r6("sh /proc/self/fd/0")
    assert proc.returncode == 2 and "cannot read" in proc.stderr.lower(), proc.stderr


def test_r082_req8_a_short_brace_run_passes():
    """R-082 (req 8): a modest run of {} is read in the main loop and passes."""
    p = _run_r6("echo " + ("{}" * 100))
    assert p.returncode == 0, p.stderr


def test_r082_req9_escaped_dollar_is_unreadable():
    """R-082 (req 9): a backslash before $ does not make the dollar literal."""
    p = _run_r6("printf \\$x")
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_req10_cmd_reads_every_switch_and_redirection():
    """R-082 (req 10): /q then /c is the command switch, and >out is not a git argument."""
    p = _run_r6("cmd //q //c git '>out' worktree remove z")
    assert p.returncode == 2 and "worktree" in p.stderr, p.stderr


def test_r082_req11_powershell_descriptor_module_and_vertical_tab():
    """R-082 (req 11): PowerShell descriptors 4 and *, a module-qualified cmdlet, and a vertical tab."""
    numbered = _run_r6("git 4>out worktree remove z", tool="PowerShell")
    assert numbered.returncode == 2 and "worktree" in numbered.stderr, numbered.stderr
    star = _run_r6("git *>&2 worktree remove z", tool="PowerShell")
    assert star.returncode == 2 and "worktree" in star.stderr, star.stderr
    module = _run_r6("Mod\\Format-Table", tool="PowerShell")
    assert module.returncode == 2 and "cannot read" in module.stderr.lower(), module.stderr
    vertical = _run_r6("echo hi\v", tool="PowerShell")
    assert vertical.returncode == 2 and "cannot read" in vertical.stderr.lower(), vertical.stderr


def test_r082_req12_pipeline_stage_changes_state_in_a_workspace(workspace):
    """R-082 (req 12): a pipeline is one part, and that part changes state when any stage does."""
    alone = _run_r6("git status", workspace)
    assert alone.returncode == 0, alone.stderr
    chained = _run_r6("git status; echo a | git add -A", workspace)
    assert chained.returncode == 2 and "rule 8" in chained.stderr, chained.stderr


def test_r082_req12a_husky_after_a_prefix_walk(workspace):
    """R-082 (req 12a): HUSKY=0 is seen after nice and env options."""
    p = _run_r6("nice -n 1 env HUSKY=0 git push origin t", workspace)
    assert p.returncode == 2 and "HUSKY" in p.stderr, p.stderr


def test_r082_req13_glued_message_checkpoint_passes(workspace):
    """R-082 (req 13): --message=<text> is the checkpoint subject, and a hyphen is a word boundary."""
    p = _run_r6("git commit --message=checkpoint-before-TASK-002 --no-verify", workspace)
    assert p.returncode == 0, p.stderr


def test_r082_r7_req1_find_clause_keeps_an_empty_word(tmp_path):
    """R-082 round 7 req 1: a find clause is the word list, so git -C keeps the empty word."""
    p = _run_r6("find . -maxdepth 0 -exec git -C '' worktree remove y ';'", tmp_path)
    assert p.returncode == 2 and "worktree" in p.stderr, p.stderr


def test_r082_r7_req1_long_find_is_refused_for_worktree_quickly(tmp_path):
    """R-082 round 7 req 1: the acceptance file's long find form is refused for the removal, inside two seconds."""
    command = "find . " + "-exec true ';' " * 3000 + "; git worktree remove y"
    started = time.monotonic()
    p = _run_r6(command, tmp_path)
    assert p.returncode == 2 and "worktree" in p.stderr and "too long" not in p.stderr.lower(), p.stderr
    assert time.monotonic() - started < 2


def test_r082_r7_req1_nested_find_is_refused_for_worktree_quickly(workspace):
    """R-082 round 7 req 1: the acceptance file's nested find form is refused for the removal, inside two seconds."""
    command = "find . " + ("-exec find . " * 18) + "-exec true " + "'\\;'" + " | git worktree remove y"
    started = time.monotonic()
    p = _run_r6(command, workspace)
    assert p.returncode == 2 and "worktree" in p.stderr and "too long" not in p.stderr.lower(), p.stderr
    assert time.monotonic() - started < 2


def test_r082_r7_req2_cmd_ends_a_command_name_at_a_semicolon(tmp_path):
    """R-082 round 7 req 2: cmd ends a command name at a semicolon."""
    p = _run_r6("cmd //c 'call;git worktree remove y'", tmp_path)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_r7_req3_cmd_refuses_a_word_that_holds_a_blank(tmp_path):
    """R-082 round 7 req 3: a cmd word that holds a blank does not survive the join."""
    p = _run_r6("cmd //c git -C 'a b' worktree remove y", tmp_path)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_r7_req4_powershell_word_continuing_after_its_quote(tmp_path):
    """R-082 round 7 req 4: a PowerShell word that continues after its closing quote is unreadable."""
    p = _run_r6("git 'worktree'remove y", tmp_path, tool="PowerShell")
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_r7_req5_powershell_switch_with_a_glued_value(tmp_path):
    """R-082 round 7 req 5: a PowerShell switch holding = is outside the table."""
    p = _run_r6("powershell -NoProfile -ep=Bypass '; git worktree remove y'", tmp_path)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_r7_req6_single_slash_cmd_under_bash_is_unreadable(tmp_path):
    """R-082 round 7 req 6: a single-slash cmd switch under Bash is unreadable."""
    p = _run_r6("cmd /c echo agent", tmp_path)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_r7_req7_bash_plus_c_is_unreadable(tmp_path):
    """R-082 round 7 req 7: a plus flag holding c is unreadable."""
    p = _run_r6("bash +c 'git worktree remove y'", tmp_path)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_r7_req8_stdin_path_with_a_dot_segment(tmp_path):
    """R-082 round 7 req 8: a script path with a dot segment into dev reads standard input."""
    p = _run_r6("echo x | bash /./dev/stdin", tmp_path)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_r7_req9_carriage_return_before_a_hash(tmp_path):
    """R-082 round 7 req 9: a carriage return outside quotes is unreadable."""
    p = _run_r6("echo x\r#; git worktree remove y", tmp_path)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_r7_req10_eval_changes_state_in_a_chain(workspace):
    """R-082 round 7 req 10: rule 8 sees a state change inside eval."""
    p = _run_r6("echo hi; eval git commit -m x", workspace)
    assert p.returncode == 2 and ("rule 8" in p.stderr or "chain" in p.stderr.lower()), p.stderr


def test_r082_r7_req11_sudo_keeps_a_husky_assignment(tmp_path):
    """R-082 round 7 req 11: an assignment after sudo is still an assignment."""
    p = _run_r6("sudo HUSKY=0 git commit -m x", tmp_path)
    assert p.returncode == 2 and "HUSKY" in p.stderr, p.stderr


def test_r082_r7_req12_conhost_is_a_launcher(tmp_path):
    """R-082 round 7 req 12: conhost is refused as a launcher."""
    p = _run_r6("conhost git worktree remove y", tmp_path)
    assert p.returncode == 2 and "cannot read" in p.stderr.lower(), p.stderr


def test_r082_r7_req13_a_clock_past_the_deadline_refuses():
    """R-082 round 7 req 13: check refuses when the module clock passes eight seconds."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("permission_guard_r7_deadline", PROG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    real = mod._clock
    base = {"t": None}

    def clock():
        if base["t"] is None:
            base["t"] = real()
            return base["t"]
        return base["t"] + 9

    mod._clock = clock
    reason = mod.check("echo hi")
    assert reason and "cannot read" in reason.lower() and "too long" in reason.lower(), reason


def test_r082_r7_req13_premerge_with_no_time_left_refuses(tmp_path):
    """R-082 round 7 req 13: a git call with no time left refuses instead of passing."""
    import importlib.util
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True, timeout=30, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    sha = "0123456789abcdef"
    folder = repo / ".git" / "bridge" / "premerge"
    folder.mkdir(parents=True)
    (folder / sha).write_text("ok", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("permission_guard_r7_premerge", PROG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._read_started = mod._clock() - 9
    assert mod.premerge_recorded(sha, str(repo)) is False


def test_r082_r8_req1_a_script_fed_by_a_pipe_is_unreadable(tmp_path):
    """R-082 round 8 req 1: a bash script in a later pipeline stage reads standard input."""
    rc, err = run("echo x | env -C / bash dev/stdin", tmp_path)
    assert rc == 2 and "cannot read" in err.lower(), err


def test_r082_r8_req2_single_slash_behind_a_prefix_is_unreadable(tmp_path):
    """R-082 round 8 req 2: slash_ok becomes false once a prefix wrapper is crossed."""
    rc, err = run("echo x | env powershell -c cmd /c echo hi", tmp_path, tool="PowerShell")
    assert rc == 2 and "cannot read" in err.lower(), err


def test_r082_r8_req3_a_quote_not_at_the_start_of_a_word_is_unreadable(tmp_path):
    """R-082 round 8 req 3: PowerShell reads a quoted part only as the whole word."""
    rc, err = run("echo a'b c'", tmp_path, tool="PowerShell")
    assert rc == 2 and "cannot read" in err.lower(), err


def test_r082_r8_req4_settingsfile_is_not_a_value_switch(tmp_path):
    """R-082 round 8 req 4: powershell.exe 5.1 does not take -settingsfile."""
    rc, err = run("powershell -settingsfile 'x; git worktree remove y;' echo", tmp_path)
    assert rc == 2 and "cannot read" in err.lower(), err


def test_r082_r8_req5_cmd_takes_no_prefix(tmp_path):
    """R-082 round 8 req 5: in the cmd mode the first word is the command word."""
    rc, err = run("cmd //c powershell/command git status", tmp_path)
    assert rc == 2 and "cannot read" in err.lower(), err


def test_r082_r8_req6_fprintf_takes_two_words(tmp_path):
    """R-082 round 8 req 6: -fprintf takes two words, so the -exec clause is the removal."""
    rc, err = run("find . -maxdepth 0 -fprintf out.txt -name -exec git worktree remove y ';'", tmp_path)
    assert rc == 2 and "worktree" in err, err


def test_r082_r8_req7_a_long_husky_command_is_the_removal(tmp_path):
    """R-082 round 8 req 7: the HUSKY search is two linear searches, then the removal is refused."""
    started = time.monotonic()
    rc, err = run("HUSKY=0 echo " + "git " * 32000 + "; git worktree remove y", tmp_path)
    assert time.monotonic() - started < 2
    assert rc == 2 and "worktree" in err, err[:200]


def test_r082_r8_req8_a_two_character_step_still_meets_the_deadline():
    """R-082 round 8 req 8: a step of two characters still tests the deadline at the mark."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("permission_guard_r8_deadline", PROG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    real = mod._clock
    state = {"n": 0, "t0": None}

    def clock():
        state["n"] += 1
        if state["t0"] is None:
            state["t0"] = real()
        if state["n"] >= 3:
            return state["t0"] + 9
        return state["t0"]

    mod._clock = clock
    mod._read_started = clock()
    parsed = mod._read_bash("echo " + ("\\x" * 2100), False, False)
    err = parsed.get("unreadable") or ""
    assert "cannot read" in err.lower() and "too long" in err.lower(), err
