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
CLAUDE = os.path.join(HERE, os.pardir, "bridge")
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
    "python ~/.claude/" + chr(0x2026),  # the permissions paragraph's "every python ~/.claude/... command"
)
PROSE_EXACT = ("git worktree remove", "gh pr merge", "npx vitest", "npx jest", "npx playwright test", "npm test", "npm run test*", "pnpm test",
               "yarn test", "node --test", "go test", "cargo test", "dotnet test", "uv run pytest", "python -m pytest", "python -m unittest")   # a command family named bare (the test suites run through the launcher), never a runnable form


@pytest.mark.parametrize("src,cmd", collect_commands())
def test_instructed_command_is_allowed(src, cmd):
    if any(cmd.startswith(k) for k in KNOWN_PROSE) or cmd in PROSE_EXACT:
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
    "gh pr merge 12 --squash --auto --match-head-commit 0123456789abcdef0123456789abcdef01234567",
    "git worktree add ../Worktrees/TASK-012 task-012",
    "npx --yes jscpd@4.0.5 src --min-lines 5",
])
def test_ordinary_commands_are_not_denied(cmd):
    verdict, _ = decide(cmd, ALLOW, DENY)
    assert verdict == "allow", cmd


@pytest.mark.parametrize("src,cmd", collect_commands())
def test_no_instructed_command_is_refused_by_the_guard(src, cmd, program, monkeypatch):
    """Review of 2026.10.06b, finding 8: the bridge's own texts never instruct a command its
    hook refuses. A placeholder sha stands for a recorded one."""
    if any(cmd.startswith(k) for k in KNOWN_PROSE) or cmd in PROSE_EXACT:
        pytest.skip("prose, not a runnable command")
    guard = program("permission-guard")
    monkeypatch.setattr(guard, "premerge_recorded", lambda sha, cwd: True)
    reason = guard.check(cmd.replace("<sha>", "0123456789abcdef0123456789abcdef01234567"), None)
    assert reason is None, "%s instructs %r, which the guard refuses: %s" % (src, cmd, reason)


def test_documented_matching_examples():
    assert rule_matches("Bash(git log * main)", "git log --oneline main")
    assert rule_matches("Bash(ls:*)", "ls -la")
    assert rule_matches("Bash(npm run build)", "npm run build")
    assert not rule_matches("Bash(npm run build)", "npm run build --watch")
    assert not rule_matches("Bash(git push *)", "git -C . push")


def collect_agent_invocations():
    found = []
    for path in DOCS:
        text = open(path, encoding="utf-8").read()
        for m in re.finditer(r"```(?:bash|sh)\n(.*?)```", text, re.S):
            for line in m.group(1).splitlines():
                if "cursor-agent -p" in line:
                    found.append((os.path.basename(path), line.strip()))
        for m in re.finditer(r"`([^`\n]*cursor-agent -p[^`\n]*)`", text):
            found.append((os.path.basename(path), m.group(1).strip()))
    return found


@pytest.mark.parametrize("src,cmd", collect_agent_invocations())
def test_every_agent_run_goes_through_the_launcher_and_review_b_keeps_execution(src, cmd):
    """Release 0a review, F2: the launcher gives the limit and withholds the identity; Review B
    keeps execution (it runs tests and reproductions) on a checkpoint restored afterwards."""
    assert cmd.startswith("python ~/.claude/cursor-bridge/bridge-run.py --limit "), "%s: not through the launcher: %r" % (src, cmd)
    if "REVIEW-DESIGN" in cmd:
        assert "--mode=ask --trust" in cmd, "%s: a design review reads only, with the workspace trusted (release A3): %r" % (src, cmd)
        return
    assert "--mode ask" not in cmd and "--mode=ask" not in cmd, "%s: the read-only mode was dropped for code reviews (owner, 2026-10-04): %r" % (src, cmd)
    if "REVIEW-" in cmd:
        assert "--force" in cmd and ("--limit auto --kind review" in cmd or "--limit 3600" in cmd), "%s: Review B runs with execution under its learned ceiling: %r" % (src, cmd)


def test_the_digest_and_the_merge_step_show_the_same_review_b_form():
    """0b review, finding 4: the digest's Review B command carries the .err redirect the
    activity check reads the launch time from, so the consistency check covers it too."""
    forms = [cmd for src, cmd in collect_agent_invocations() if "REVIEW-" in cmd and "REVIEW-DESIGN" not in cmd]
    assert len(forms) >= 2, forms
    assert all(re.search(r"2> run/review/REVIEW-(<nnn>|STAGE-<name>)\.err", f) and "--force" in f and "--limit auto --kind review" in f for f in forms), forms
