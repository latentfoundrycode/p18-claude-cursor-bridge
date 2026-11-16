"""BUG-045 (R-082): a -h or --help word anywhere among git's words exempts every git refusal of the permission guard.

The supervisor's reproduction tests, written before the builder's run (docs/debug/BUG-045.md). Each runs
permission-guard.py as the hook runs it (the hook's JSON on standard input, the Bash tool), from a scratch folder that
is no bridge Workspace, and reads the exit code (2 refuses, 0 lets through) and the reason on standard error.

The cause: permission-guard.py sets `helpful = "--help" in w[1:] or "-h" in w[1:]` and skips the hooksPath, hook-skipper,
force-push and worktree-removal refusals when it holds, though git reads a help word as its help option only where it
stands as an option of its own; as an option's value (`-m -h`, `-o -h`) or after `--` it is an argument, and git does
what the rest of the command says. The premise test below shows git committing with its hooks skipped under such a form.

enforces: docs/DESIGN.md, "Change: the program release", "The permission guard, permission-guard.py (C5)"; R-082;
docs/INVENTORY.md, Decisions, the permission guard's threat-model row (a refused action named in the command's own words).
"""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py")


def guard(command, cwd):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "permission_mode": "auto", "cwd": str(cwd)}
    p = subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stderr


@pytest.fixture
def plain(tmp_path):
    """A folder that is no bridge Workspace."""
    d = tmp_path / "plain"
    d.mkdir()
    return d


# A help word that git reads as an argument: an option's value, or a word after `--`. Each is refused (red on b05fbc8).
HELP_AS_AN_ARGUMENT = [
    ("commit-no-verify-message-h", "git commit --no-verify -a -m -h", "--no-verify"),
    ("commit-no-verify-message-help", "git commit --no-verify -a -m --help", "--no-verify"),
    ("commit-n-message-h", "git commit -n -a -m -h", "-n"),
    ("commit-no-verify-pathspec-h-after-dashdash", "git commit --no-verify -m x -- -h", "--no-verify"),
    ("commit-hookspath-message-h", "git -c core.hooksPath=/dev/null commit -m -h", "core.hooksPath"),
    ("push-force-push-option-h", "git push --force -o -h origin main", "--force"),
    ("push-force-help-after-dashdash", "git push --force -- --help", "--force"),
    ("worktree-remove-help-after-dashdash", "git worktree remove -- --help", "worktree remove"),
    ("worktree-remove-h-after-dashdash", "git worktree remove -- -h", "worktree remove"),
]


@pytest.mark.parametrize("command,reason", [(c, r) for _, c, r in HELP_AS_AN_ARGUMENT], ids=[n for n, _, _ in HELP_AS_AN_ARGUMENT])
def test_bug045_a_help_word_git_reads_as_an_argument_exempts_no_refusal(plain, command, reason):
    rc, err = guard(command, plain)
    assert rc == 2 and "refused" in err and reason in err, (command, rc, err)


# A lone help word after the subcommand is git's help option: git prints its help and does nothing else. Each passes.
HELP_CALLS = [
    ("worktree-remove-help", "git worktree remove --help"),
    ("worktree-remove-h", "git worktree remove -h"),
    ("commit-h", "git commit -h"),
    ("commit-help", "git commit --help"),
    ("push-help", "git push --help"),
    ("push-h", "git push -h"),
]


@pytest.mark.parametrize("command", [c for _, c in HELP_CALLS], ids=[n for n, _ in HELP_CALLS])
def test_bug045_a_lone_help_word_after_the_subcommand_still_passes(plain, command):
    rc, err = guard(command, plain)
    assert rc == 0, (command, rc, err)


def test_bug045_premise_git_takes_a_help_word_as_the_message_and_skips_the_hooks(tmp_path):
    """The premise of the defect, on git itself: a failing pre-commit hook stops `-m x`, and `--no-verify -m -h` commits."""
    repo = str(tmp_path / "repo")

    def git(*args):
        return subprocess.run(["git", "-C", repo, "-c", "core.hooksPath=.git/hooks", "-c", "user.email=probe@example.invalid", "-c", "user.name=probe"] + list(args), capture_output=True, text=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    os.makedirs(repo)
    assert git("init", "-q").returncode == 0
    with open(os.path.join(repo, "a.txt"), "w") as fh:
        fh.write("1\n")
    git("add", "a.txt")
    assert git("commit", "-q", "--no-verify", "-m", "base").returncode == 0
    hook = os.path.join(repo, ".git", "hooks", "pre-commit")
    with open(hook, "w", newline="\n") as fh:
        fh.write("#!/bin/sh\nexit 1\n")
    os.chmod(hook, 0o755)
    with open(os.path.join(repo, "a.txt"), "a") as fh:
        fh.write("2\n")
    assert git("commit", "-a", "-m", "x").returncode != 0, "the hook did not stop the commit"
    assert git("commit", "-a", "--no-verify", "-m", "-h").returncode == 0
    assert git("log", "-1", "--format=%s").stdout.strip() == "-h"


# ---------------------------------------------------------------- round 1's findings (the security audit and Review A), red on round 1's tree
# The same subsystem a second time, so the design changes (docs/debug/BUG-045.md, round 2): git's global options before the
# subcommand are read from a known list, and any other one is refused as unreadable; an alias defined in the command for
# a hook-skipping subcommand is refused as the aliases for the other refused actions are.

GLOBAL_OPTIONS_REFUSED = [
    ("attr-source-before-a-no-verify-commit", "git --attr-source HEAD commit --no-verify -m x", "--no-verify"),
    ("attr-source-before-a-force-push", "git --attr-source HEAD push --force origin main", "--force"),
    ("attr-source-before-worktree-remove", "git --attr-source HEAD worktree remove wt", "worktree remove"),
    ("super-prefix-before-a-no-verify-commit", "git --super-prefix x/ commit --no-verify -m x", "--no-verify"),
    ("unknown-global-option-before-a-no-verify-commit", "git --bogus-new-option x commit --no-verify -m x", "cannot read"),
    ("unknown-global-option-before-a-force-push", "git --some-future-flag push --force origin main", "cannot read"),
    ("no-lazy-fetch-before-a-force-push", "git --no-lazy-fetch push --force origin main", "--force"),
]


@pytest.mark.parametrize("command,reason", [(c, r) for _, c, r in GLOBAL_OPTIONS_REFUSED], ids=[n for n, _, _ in GLOBAL_OPTIONS_REFUSED])
def test_bug045_a_refused_action_behind_a_git_global_option_is_refused(plain, command, reason):
    rc, err = guard(command, plain)
    assert rc == 2 and "refused" in err and reason in err, (command, rc, err)


ALIASES_REFUSED = [
    ("alias-for-a-no-verify-commit", 'git -c "alias.cm=commit --no-verify -am" cm x'),
    ("alias-for-an-n-commit", 'git -c "alias.cm=commit -n -am" cm x'),
    ("alias-for-a-commit-before-a-lone-h-with-hooks-off", 'git -c core.hooksPath=nohooks -c "alias.cm=commit -am" cm -h'),
    ("alias-for-a-no-verify-rebase", 'git -c "alias.r=rebase --no-verify" r main'),
    ("alias-for-a-merge", 'git -c "alias.m=merge --no-verify" m topic'),
]


@pytest.mark.parametrize("command", [c for _, c in ALIASES_REFUSED], ids=[n for n, _ in ALIASES_REFUSED])
def test_bug045_an_alias_defined_in_the_command_for_a_hook_skipper_is_refused(plain, command):
    rc, err = guard(command, plain)
    assert rc == 2 and "refused" in err and "alias" in err, (command, rc, err)


GLOBAL_OPTIONS_PASSING = [
    ("no-pager-log", "git --no-pager log -1"),
    ("dash-capital-c-status", "git -C sub status"),
    ("dash-c-config-status", "git -c color.ui=never status"),
    ("git-dir-equals-status", "git --git-dir=.git status"),
    ("paginate-log", "git -p log -1"),
    ("no-optional-locks-status", "git --no-optional-locks status"),
    ("attr-source-status", "git --attr-source HEAD status"),
]


@pytest.mark.parametrize("command", [c for _, c in GLOBAL_OPTIONS_PASSING], ids=[n for n, _ in GLOBAL_OPTIONS_PASSING])
def test_bug045_a_known_global_option_or_a_harmless_alias_still_passes(plain, command):
    rc, err = guard(command, plain)
    assert rc == 0, (command, rc, err)


# ---------------------------------------------------------------- round 2's findings (the supervisor's probe and the security audit), red on round 2's tree
# Each family a second time, so each reading is made whole (docs/debug/BUG-045.md, round 2's findings): every alias defined
# in the command is refused, whatever its value (git reads options at the start of an alias value, and the guard does not
# expand aliases; round 2's alias-for-status case, which passed, now stands here refused); a refused long option is read as
# git reads it, by any prefix git accepts as its abbreviation; and a git config command that names core.hooksPath passes
# only in its read forms.

INLINE_ALIASES_REFUSED = [
    ("alias-with-a-hookspath-option-before-commit", 'git -c "alias.cm=-c core.hooksPath=/dev/null commit" cm -a -m x'),
    ("alias-with-a-no-pager-option-before-commit", 'git -c "alias.cm=--no-pager commit -n" cm -a -m x'),
    ("alias-for-status", 'git -c "alias.st=status" st'),
    ("alias-for-log", "git -c alias.lg=log lg"),
    ("alias-key-in-upper-case", 'git -c "ALIAS.cm=status" cm'),
    ("alias-value-in-single-quotes", "git -c \"alias.cm='commit' -n -am\" cm x"),
    ("alias-value-in-double-quotes", "git -c 'alias.cm=\"commit\" -n -am' cm x"),
    ("alias-value-partly-quoted", "git -c 'alias.cm=c\"ommit\" -n -am' cm x"),
    ("alias-with-a-dotted-key", "git -c alias.v.x=commit v.x -am x"),
    ("shell-alias-with-a-dotted-key", "git -c 'alias.v.x=!echo hi' v.x"),
]


@pytest.mark.parametrize("command", [c for _, c in INLINE_ALIASES_REFUSED], ids=[n for n, _ in INLINE_ALIASES_REFUSED])
def test_bug045_every_alias_defined_in_the_command_is_refused(plain, command):
    rc, err = guard(command, plain)
    assert rc == 2 and "refused" in err and "alias" in err, (command, rc, err)


ABBREVIATIONS_REFUSED = [
    ("commit-no-verif", "git commit -a --no-verif -m x", "skips its checks"),
    ("commit-no-veri", "git commit -a --no-veri -m x", "skips its checks"),
    ("push-no-verif", "git push --no-verif origin HEAD", "skips its checks"),
    ("merge-no-verif", "git merge --no-verif topic", "skips its checks"),
    ("rebase-no-verif", "git rebase --no-verif main", "skips its checks"),
    ("push-mirr", "git push --mirr origin", "push"),
    ("push-force-w", "git push --force-w origin main", "push"),
    ("push-force-with-equals", "git push --force-with=main origin main", "push"),
    ("push-force-if", "git push --force-if origin main", "push"),
]


@pytest.mark.parametrize("command,reason", [(c, r) for _, c, r in ABBREVIATIONS_REFUSED], ids=[n for n, _, _ in ABBREVIATIONS_REFUSED])
def test_bug045_an_abbreviation_git_accepts_for_a_refused_option_is_refused(plain, command, reason):
    rc, err = guard(command, plain)
    assert rc == 2 and "refused" in err and reason in err, (command, rc, err)


CONFIG_HOOKSPATH_REFUSED = [
    ("comment-value-decoy-get", "git config --comment --get core.hooksPath /dev/null"),
    ("relative-folder-that-holds-no-hooks", "git config core.hooksPath nohooks"),
    ("set-subcommand", "git config set core.hooksPath /dev/null"),
    ("add", "git config --add core.hooksPath /dev/null"),
    ("local-scope-write", "git config --local core.hooksPath nohooks"),
]


@pytest.mark.parametrize("command", [c for _, c in CONFIG_HOOKSPATH_REFUSED], ids=[n for n, _ in CONFIG_HOOKSPATH_REFUSED])
def test_bug045_a_git_config_write_of_core_hookspath_is_refused(plain, command):
    rc, err = guard(command, plain)
    assert rc == 2 and "refused" in err and "core.hooksPath" in err, (command, rc, err)


PASSING_AFTER_ROUND_2 = [
    ("config-read-bare", "git config core.hooksPath"),
    ("config-read-get", "git config --get core.hooksPath"),
    ("config-read-get-subcommand", "git config get core.hooksPath"),
    ("config-instructed-write-of-the-bridge-hooks-folder", "git config core.hooksPath .githooks"),
    ("merge-no-verify-signatures", "git merge --no-verify-signatures topic"),
    ("push-follow-tags", "git push --follow-tags origin task-012"),
    ("push-no-force-with-lease-word", "git push origin task-012"),
    ("commit-no-edit", "git commit --amend --no-edit"),
]


@pytest.mark.parametrize("command", [c for _, c in PASSING_AFTER_ROUND_2], ids=[n for n, _ in PASSING_AFTER_ROUND_2])
def test_bug045_a_read_or_an_ordinary_option_still_passes(plain, command):
    rc, err = guard(command, plain)
    assert rc == 0, (command, rc, err)


# ---------------------------------------------------------------- the builder adds its cases below this line and edits nothing above it


def test_bug045_a_help_word_as_the_file_of_F_is_refused(plain):
    """BUG-045 (R-082): -h as the file of -F is an option value, so --no-verify is still refused."""
    rc, err = guard("git commit --no-verify -F -h", plain)
    assert rc == 2 and "refused" in err and "--no-verify" in err, (rc, err)


def test_bug045_a_help_word_beside_other_arguments_is_the_ruled_over_refusal(plain):
    """BUG-045 (R-082): `git commit --no-verify -a -h -m x` is refused. git would print its help and run nothing, because -h stands as its own option beside other arguments; the refusal is the ruled, safe over-refusal."""
    rc, err = guard("git commit --no-verify -a -h -m x", plain)
    assert rc == 2 and "refused" in err and "--no-verify" in err, (rc, err)


def test_bug045_a_config_hookspath_with_a_trailing_help_word_is_refused(plain):
    """BUG-045 (R-082): `git config core.hooksPath /dev/null -h` is refused. args are the key, the value and -h, not a lone help word, so the config refusal stands."""
    rc, err = guard("git config core.hooksPath /dev/null -h", plain)
    assert rc == 2 and "refused" in err and "core.hooksPath" in err, (rc, err)


# BUG-045 (R-082), F3. Each known global option before `status` passes, and the same option before
# `commit --no-verify -m x` is refused. -c's value is neither core.hooksPath nor an alias key.
# -h, --help, -v, --version, --exec-path, --html-path, --man-path, --info-path and --list-cmds=
# make git print help, a version, a path or a command list and run nothing, so refusing
# `commit --no-verify` behind them is a safe over-refusal. --config-env= is left out: it is refused earlier.
KNOWN_GIT_GLOBAL = [
    ("dash-C", "-C sub"),
    ("dash-c", "-c color.ui=never"),
    ("git-dir", "--git-dir .git"),
    ("work-tree", "--work-tree ."),
    ("namespace", "--namespace ns"),
    ("super-prefix", "--super-prefix x/"),
    ("attr-source", "--attr-source HEAD"),
    ("git-dir-equals", "--git-dir=.git"),
    ("work-tree-equals", "--work-tree=."),
    ("namespace-equals", "--namespace=ns"),
    ("super-prefix-equals", "--super-prefix=x/"),
    ("attr-source-equals", "--attr-source=HEAD"),
    ("exec-path-equals", "--exec-path=/usr/bin"),
    ("list-cmds-equals", "--list-cmds=main"),
    ("dash-p", "-p"),
    ("paginate", "--paginate"),
    ("dash-P", "-P"),
    ("no-pager", "--no-pager"),
    ("bare", "--bare"),
    ("no-replace-objects", "--no-replace-objects"),
    ("no-lazy-fetch", "--no-lazy-fetch"),
    ("literal-pathspecs", "--literal-pathspecs"),
    ("glob-pathspecs", "--glob-pathspecs"),
    ("noglob-pathspecs", "--noglob-pathspecs"),
    ("icase-pathspecs", "--icase-pathspecs"),
    ("no-optional-locks", "--no-optional-locks"),
    ("no-advice", "--no-advice"),
    ("exec-path", "--exec-path"),
    ("html-path", "--html-path"),
    ("man-path", "--man-path"),
    ("info-path", "--info-path"),
    ("dash-v", "-v"),
    ("version", "--version"),
    ("dash-h", "-h"),
    ("help", "--help"),
]


@pytest.mark.parametrize("option", [opt for _, opt in KNOWN_GIT_GLOBAL], ids=[name for name, _ in KNOWN_GIT_GLOBAL])
def test_bug045_a_known_git_global_option_is_read(plain, option):
    """BUG-045 (R-082): a known git global option before status passes, and the same option before commit --no-verify is refused."""
    rc, err = guard("git %s status" % option, plain)
    assert rc == 0, (option, rc, err)
    rc, err = guard("git %s commit --no-verify -m x" % option, plain)
    assert rc == 2 and "refused" in err and "--no-verify" in err, (option, rc, err)


# -C and -c take the next word. A value glued onto the same word is not that option, not an equals-form, and not a flag.
GLUED_SHORT = [
    ("glued-C", "git -Csub status", "-Csub"),
    ("glued-c", "git -ccolor.ui=never status", "-ccolor.ui=never"),
]


@pytest.mark.parametrize("command,option", [(c, o) for _, c, o in GLUED_SHORT], ids=[name for name, _, _ in GLUED_SHORT])
def test_bug045_a_glued_short_option_value_is_unreadable(plain, command, option):
    """BUG-045 (R-082): F3 names -C and -c as whole words, so a glued value is an unknown option and unreadable."""
    rc, err = guard(command, plain)
    assert rc == 2 and "refused" in err and "cannot read" in err and option in err, (command, rc, err)


HOOK_ALIAS = [
    ("commit", 'git -c "alias.co=commit -m x" co'),
    ("merge", 'git -c "alias.mg=merge topic" mg'),
    ("rebase", 'git -c "alias.rb=rebase main" rb'),
    ("am", 'git -c "alias.box=am mbox" box'),
    ("cherry-pick", 'git -c "alias.pick=cherry-pick abc" pick'),
    ("revert", 'git -c "alias.undo=revert HEAD" undo'),
]


@pytest.mark.parametrize("command", [c for _, c in HOOK_ALIAS], ids=[name for name, _ in HOOK_ALIAS])
def test_bug045_an_alias_for_each_hook_skipper_is_refused(plain, command):
    """BUG-045 (R-082): an alias whose value starts with commit, merge, rebase, am, cherry-pick or revert is refused."""
    rc, err = guard(command, plain)
    assert rc == 2 and "refused" in err and "alias" in err, (command, rc, err)


READ_ALIAS = [
    ("status", 'git -c "alias.ss=status" ss'),
    ("log", 'git -c "alias.lg=log -1" lg'),
]


@pytest.mark.parametrize("command", [c for _, c in READ_ALIAS], ids=[name for name, _ in READ_ALIAS])
def test_bug045_an_alias_for_status_or_log_still_passes(plain, command):
    """BUG-045 (R-082): an alias whose value starts with status or log still passes."""
    rc, err = guard(command, plain)
    assert rc == 0, (command, rc, err)


@pytest.fixture
def bridge_workspace(tmp_path):
    """A bridge Workspace: a folder under tmp_path holding docs/PROJECT_STATUS.md."""
    d = tmp_path / "ws"
    os.makedirs(os.path.join(str(d), "docs"))
    with open(os.path.join(str(d), "docs", "PROJECT_STATUS.md"), "w", newline="\n") as fh:
        fh.write("# Project Status\n")
    return d


def test_bug045_an_unreadable_option_is_state_changing_in_a_workspace_chain(bridge_workspace):
    """BUG-045 (R-082): chain_reason runs before the word checks, so this chain is refused with `a chain of` only because state_changing read the unreadable git command as state-changing; read as a read, the refusal would be the `cannot read` one instead."""
    rc, err = guard("git status && git --bogus-new-option x commit --no-verify -m x", bridge_workspace)
    assert rc == 2 and "refused" in err and "a chain of" in err, (rc, err)
