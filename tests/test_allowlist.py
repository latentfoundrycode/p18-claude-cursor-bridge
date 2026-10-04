"""Every command the supervisor's instructions issue must be allowed by the bridge's
settings and denied by none of its deny rules; the deny rules must catch what they are for.
Commands are collected from the fenced bash blocks and the inline code of supervisor.md
and the merge policy. A placeholder such as <nnn> or <sha> is kept as text: a rule that
needs the placeholder's position to be a space is a rule that cannot match in practice."""
import json
import os
import re

import pytest

from permission_rules import decide, rule_matches

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUDE = os.path.join(HERE, os.pardir, ".claude")
SETTINGS = json.load(open(os.path.join(CLAUDE, "cursor-bridge", "settings.bridge.json"), encoding="utf-8"))
ALLOW = SETTINGS["permissions"]["allow"]
DENY = SETTINGS["permissions"]["deny"]
DOCS = [os.path.join(CLAUDE, "commands", "supervisor.md"), os.path.join(CLAUDE, "cursor-bridge", "Merge-Verification-Policy.md")]

EXECUTABLES = ("git ", "gh ", "python ~/.claude/", "cursor-agent ", "npx ", "semgrep ", "osv-scanner ", "socket ",
               "pytest ", "cat ~/.claude/", "powershell -NoProfile")


def collect_commands():
    found = []
    for path in DOCS:
        text = open(path, encoding="utf-8").read()
        for m in re.finditer(r"```(?:bash|sh)\n(.*?)```", text, re.S):
            for line in m.group(1).splitlines():
                line = line.strip()
                if line and not line.startswith("#") and line.startswith(EXECUTABLES):
                    found.append((os.path.basename(path), line))
        for m in re.finditer(r"`([^`\n]+)`", text):
            cmd = m.group(1).strip()
            if cmd.startswith(EXECUTABLES) and " " in cmd and len(cmd) < 220:
                found.append((os.path.basename(path), cmd))
    # the same command text appears many times; test each once
    seen, out = set(), []
    for src, cmd in found:
        if cmd not in seen:
            seen.add(cmd)
            out.append((src, cmd))
    return out


KNOWN_PROSE = (
    # inline code that names a command family rather than a runnable command
    "git worktree remove --force",      # named as the thing never to run
    "git worktree remove <worktree>",   # described generically; the real form carries ../Worktrees/
    "git reset --hard HEAD",            # covered: 'git reset --hard:*'
    "git add -A && git commit",         # rule 8's example of what never to do
    "gh pr merge --admin",              # named as the thing the deny rules forbid
)


@pytest.mark.parametrize("src,cmd", collect_commands())
def test_instructed_command_is_allowed(src, cmd):
    if any(cmd.startswith(k) for k in KNOWN_PROSE):
        pytest.skip("prose, not a runnable command")
    verdict, part = decide(cmd, ALLOW, DENY)
    if verdict == "ask":
        pytest.fail("%s: no allow rule matches %r (part %r)" % (src, cmd, part))
    assert verdict != "deny", "%s: a deny rule hits an instructed command %r (part %r)" % (src, cmd, part)


@pytest.mark.parametrize("cmd", [
    "gh pr merge 187 --squash --admin --delete-branch",
    "gh pr merge --admin 12",
    "cd Workspace && gh pr merge 5 --squash --admin",
    "git push --force origin main",
    "git push -f origin task-12",
    "git push origin main -f",
    "git -C . push --force-with-lease",
])
def test_deny_rules_catch_the_override_and_force_push(cmd):
    verdict, part = decide(cmd, ALLOW, DENY)
    assert verdict == "deny", "%r should be denied, got %s on %r" % (cmd, verdict, part)


@pytest.mark.parametrize("cmd", [
    "cursor-agent -p --force --model grok-4.7-high \"Read handoff/TASK-012.md and implement exactly what it specifies.\"",
    "git push -u origin task-012",
    "gh pr merge 12 --squash --auto",
    "git worktree add ../Worktrees/TASK-012 task-012",
    "npx --yes jscpd@4.0.5 src --min-lines 5",
])
def test_ordinary_commands_are_not_denied(cmd):
    verdict, _ = decide(cmd, ALLOW, DENY)
    assert verdict == "allow", cmd


def test_documented_matching_examples():
    assert rule_matches("Bash(git log * main)", "git log --oneline main")
    assert rule_matches("Bash(ls:*)", "ls -la")
    assert rule_matches("Bash(npm run build)", "npm run build")
    assert not rule_matches("Bash(npm run build)", "npm run build --watch")
    assert not rule_matches("Bash(git push *)", "git -C . push")
