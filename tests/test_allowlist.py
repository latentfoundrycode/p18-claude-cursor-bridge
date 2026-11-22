"""Every command the supervisor's instructions issue must be allowed by the bridge's
settings and denied by none of its deny rules; the deny rules must catch what they are for.
Commands are collected from the fenced bash blocks and the inline code of supervisor.md, its phase
modules (TASK-010), and the merge policy. A placeholder such as <nnn> or <sha> is kept as text: a rule that
needs the placeholder's position to be a space is a rule that cannot match in practice.

The mark `<!-- not run -->` (R-096): an inline command on a line that carries it is not collected. It is for a
command an instruction quotes as an example and does not instruct, so the text need not reword it to escape the
check. The mark is a line's, not a command's: a line that instructs any command never carries it, and a marked line
holding more than one inline command is refused, so a mark never hides an instructed command beside its example.
The two skip lists below keep what they hold."""
import json
import os
import re

import pytest

from instructions import instruction_paths
from permission_rules import decide, rule_matches

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUDE = os.path.join(HERE, os.pardir, "bridge")
SETTINGS = json.load(open(os.path.join(CLAUDE, "cursor-bridge", "settings.bridge.json"), encoding="utf-8"))
ALLOW = SETTINGS["permissions"]["allow"]
DENY = SETTINGS["permissions"]["deny"]
DOCS = instruction_paths() + [os.path.join(CLAUDE, "cursor-bridge", "Merge-Verification-Policy.md")]   # the core and its phase modules (TASK-010)

EXECUTABLES = ("git ", "gh ", "python ~/.claude/", "cursor-agent ", "npx ", "semgrep ", "osv-scanner ", "socket ",
               "pytest ", "cat ~/.claude/", "powershell -NoProfile")


NOT_RUN = "<!-- not run -->"


def commands_in(text, src):
    """The commands one text issues: each runnable line of its fenced bash blocks, and each inline command on a line
    that does not carry NOT_RUN (R-096). An inline command never spans a line, so reading it line by line finds what
    reading the whole text finds."""
    found = []
    for m in re.finditer(r"```(?:bash|sh)\n(.*?)```", text, re.S):
        for line in m.group(1).splitlines():
            line = line.strip()
            if line and not line.startswith("#") and line.startswith(EXECUTABLES):
                found.append((src, line))
    for text_line in text.split("\n"):
        cmds = [m.group(1).strip() for m in re.finditer(r"`([^`\n]+)`", text_line)]
        cmds = [cmd for cmd in cmds if cmd.startswith(EXECUTABLES) and " " in cmd and len(cmd) < 220]
        if NOT_RUN in text_line:
            if len(cmds) > 1:
                raise ValueError("%s: a line carrying %s holds %d commands; the mark is for a line that quotes one "
                                 "example: %r" % (src, NOT_RUN, len(cmds), cmds))
            continue
        found.extend((src, cmd) for cmd in cmds)
    return found


def collect_commands():
    found = []
    for path in DOCS:
        found.extend(commands_in(open(path, encoding="utf-8").read(), os.path.basename(path)))
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
               "yarn test", "node --test", "go test", "cargo test", "dotnet test", "uv run pytest", "python -m pytest", "python -m unittest",
               "git commit --no-verify")   # a command family named bare (the test suites run through the launcher; the policy's forbidden form), never a runnable form


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
    "gh pr merge 12 --squash --match-head-commit 0123456789abcdef0123456789abcdef01234567",   # TASK-082 (R-083): the armed form retired
    "git worktree add ../Worktrees/TASK-012 task-012",
    "npx --yes jscpd@4.0.5 src --min-lines 5",
])
def test_ordinary_commands_are_not_denied(cmd):
    verdict, _ = decide(cmd, ALLOW, DENY)
    assert verdict == "allow", cmd


@pytest.mark.parametrize("src,cmd", collect_commands())
def test_no_instructed_command_is_refused_by_the_guard(src, cmd, program, monkeypatch):
    """Review of 2026.10.06b, finding 8: the bridge's own texts never instruct a command its
    hook refuses. A placeholder sha stands for a recorded one, and every other placeholder (a
    `<...>` word beginning with a letter, prose that an agent replaces before it runs the command)
    for a sample word: a placeholder may hold an apostrophe, which the guard reads as an open quote
    (R-082, TASK-063's resolution round, docs/CHANGES.md)."""
    if any(cmd.startswith(k) for k in KNOWN_PROSE) or cmd in PROSE_EXACT:
        pytest.skip("prose, not a runnable command")
    guard = program("permission-guard")
    monkeypatch.setattr(guard, "premerge_recorded", lambda sha, cwd: True)
    monkeypatch.setattr(guard, "ready_recorded", lambda pr, sha, cwd: True)   # TASK-083 (R-083): the ready record stands too
    # A merge's <n> is the pull request's number, which the guard reads (TASK-083): a sample number stands for it.
    numbered = re.sub(r"\bgh pr merge <n>", "gh pr merge 12", cmd)
    runnable = re.sub(r"<[A-Za-z][^<>\n]*>", "placeholder", numbered.replace("<sha>", "0123456789abcdef0123456789abcdef01234567"))
    reason = guard.check(runnable, None)
    assert reason is None, "%s instructs %r, which the guard refuses: %s" % (src, cmd, reason)


def test_r096_an_inline_command_on_a_line_marked_not_run_is_not_collected():
    """R-096 (TASK-076): the collector keeps an inline command on an unmarked line and skips one on a line that
    carries the mark, so an instruction can quote a command as an example without the check reading it as issued."""
    text = ("Before you start, run `git status --short` and read what it prints.\n"
            "A command never to run, quoted as an example: `git push --force origin main` " + NOT_RUN + "\n")
    assert [cmd for _src, cmd in commands_in(text, "sample.md")] == ["git status --short"]


def test_r096_a_marked_line_holding_two_commands_is_refused():
    """R-096 (TASK-076, Review A): the mark is a line's, so a marked line holding an instructed command beside its
    example would hide that command from the check; such a line is refused, never read silently."""
    text = ("Run `git fetch -q origin main:main`, never `git push --force origin main` " + NOT_RUN + "\n")
    with pytest.raises(ValueError, match="holds 2 commands"):
        commands_in(text, "sample.md")

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


def test_r039_driver_launcher_rule_in_allow():
    """R-039: settings.bridge.json allows bridge-run --kind driver."""
    rule = "Bash(python ~/.claude/cursor-bridge/bridge-run.py --limit * --kind driver -- *)"
    assert rule in ALLOW
    for interpreter in ("python", "python3", "py", ".venv/Scripts/python.exe"):
        cmd = ("python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind driver -- %s "
               "run/supervisor/task028_mutants.py" % interpreter)
        assert decide(cmd, ALLOW, DENY)[0] == "allow", cmd
    cmd = ("python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind driver -- python "
           "~/.claude/cursor-bridge/mutation-run.py run/supervisor/TASK-028-mutants.json")
    assert decide(cmd, ALLOW, DENY)[0] == "allow", cmd


HEAVY_RULES = ("Bash(python ~/.claude/cursor-bridge/bridge-run.py --limit * --kind test -- *)",
               "Bash(python ~/.claude/cursor-bridge/bridge-run.py --limit * --kind driver -- *)")


def test_r052_the_documented_strip_launches_run_on_the_heavy_launch_rules():
    """TASK-041 (R-052): the loop's suite and driver launches carry `--strip` between `--limit` and `--kind`. One such
    launch was observed from the supervisor's session on 2026-11-02 running with no prompt and no refusal (docs/DESIGN.md,
    the host table), so the two heavy-launch rules are kept as they are, and the documented commands are pinned here as
    matching them: the suite, the new tests against the checkpoint, the mutation run and, since BUG-043, the
    increment's own test files (P7's whole-suite run before the first push left the text with release S: CI's run on the
    pull request is that run)."""
    for rule in HEAVY_RULES:
        assert rule in ALLOW
    strip = [cmd for _src, cmd in collect_commands() if " --strip " in cmd]
    assert len(strip) == 4, strip
    for cmd in strip:
        assert cmd.startswith("python ~/.claude/cursor-bridge/bridge-run.py --limit auto --strip "), cmd
        assert decide(cmd, ALLOW, DENY)[0] == "allow", cmd
        launch = cmd.split(" > ", 1)[0]
        assert any(rule_matches(rule, launch) for rule in HEAVY_RULES), cmd


def test_the_digest_and_the_merge_step_show_the_same_review_b_form():
    """0b review, finding 4: the digest's Review B command carries the .err redirect the
    activity check reads the launch time from, so the consistency check covers it too; since TASK-034 the file
    carries the round's name, `<ID>-r<N>` or `STAGE-<name>-r<N>` (R-042)."""
    forms = [cmd for src, cmd in collect_agent_invocations() if "REVIEW-" in cmd and "REVIEW-DESIGN" not in cmd]
    assert len(forms) >= 2, forms
    assert all(re.search(r"2> run/review/REVIEW-(<ID>-r<N>|STAGE-<name>-r<N>)\.err", f) and "--force" in f and "--limit auto --kind review" in f for f in forms), forms


def test_r049_d4_p4_the_stage_review_tag_its_read_and_the_remote_branch_list_are_allowed():
    """R-049, TASK-040's Done when: `settings.bridge.json` gains `Bash(git tag stage-review/*)`, `Bash(git cat-file -p
    stage-review/*)` and the exact `Bash(git branch -r)`; the commands reflection.md documents for them (D4's tag and its
    read, P4's remote-branch list beside `gh pr list --state open --limit 100`) are collected and allowed."""
    for r in ("Bash(git tag stage-review/*)", "Bash(git cat-file -p stage-review/*)", "Bash(git branch -r)",
              "Bash(gh pr list:*)", "Bash(git push:*)"):
        assert r in ALLOW, r
    documented = [cmd for _src, cmd in collect_commands()]
    for cmd in ("git tag stage-review/<name>-<n>", "git cat-file -p stage-review/<name>-<n>:<path>", "git branch -r",
                "gh pr list --state open --limit 100", "gh pr list --state merged --head <branch>",
                "git push origin --delete <branch>"):
        assert cmd in documented, cmd
    for cmd in ("git tag stage-review/T1-1", "git cat-file -p stage-review/T1-1:run/review/SCOPE-STAGE-T1.md",
                "git branch -r", "gh pr list --state open --limit 100"):
        assert decide(cmd, ALLOW, DENY)[0] == "allow", cmd


def test_r049_d4_the_new_rules_admit_nothing_beyond_the_tag_s_namespace():
    """R-049, TASK-040's Done when: `git show stage-review/<name>-<n>:<path> --output=<file>` (KP-067: the file created
    empty) matches no rule, which is why the read is `git cat-file -p`, which has no such option; a tag outside the
    namespace, a tag deleted, an object read outside it and a remote branch deleted are not admitted either."""
    new = ("Bash(git tag stage-review/*)", "Bash(git cat-file -p stage-review/*)", "Bash(git branch -r)")
    assert all(r in ALLOW for r in new), [r for r in new if r not in ALLOW]
    for cmd in ("git show stage-review/<name>-<n>:<path> --output=<file>", "git show stage-review/T1-1:run/review/x.md --output=x",
                "git tag v1.0", "git tag -d stage-review/T1-1", "git cat-file -p HEAD:docs/INVENTORY.md",
                "git branch -r -d origin/task-040"):
        assert not any(rule_matches(r, cmd) for r in ALLOW), cmd
        assert decide(cmd, ALLOW, DENY)[0] != "allow", cmd
    # A `*` matches any text, so the tag rule alone admits an option after the name (Review A, TASK-040 round 1, S1:
    # `git tag stage-review/x -d v1.0` deletes another tag, `-a` makes the annotated tag --follow-tags carries, `-f`
    # moves a tag a record cites); the deny rule `Bash(git tag stage-review/* -*)` refuses any bare option after the name
    # (a quoted or tab-separated option is not matched: a HARDENING lead), mirrored for the PowerShell tool as the
    # file's comment says. Not ` *`: a trailing ` *` also matches the bare command, which would refuse the tag itself. A
    # commit named after the tag's name (`git tag stage-review/T1-1 HEAD~3`) stays admitted: without `-f` it makes a new
    # local lightweight tag only, moving and deleting none.
    assert "Bash(git tag stage-review/* -*)" in DENY
    assert "PowerShell(*git tag stage-review/* -*)" in DENY
    for cmd in ("git tag stage-review/T1-2 -d v1.0", "git tag stage-review/T1-2 -d stage-review/T1-1",
                "git tag stage-review/T1-2 --delete v1.0", "git tag stage-review/T1-1 -a -m annotated",
                "git tag stage-review/T1-1 -f", "git tag stage-review/T1-1 HEAD~3 --force"):
        assert decide(cmd, ALLOW, DENY)[0] == "deny", cmd
    assert decide("git tag stage-review/T1-1", ALLOW, DENY)[0] == "allow"


def test_r049_d4_the_guard_treats_the_stage_tag_as_it_treats_the_loop_s_state_commands(program):
    """R-049, TASK-040's Done when: the permission guard reads the documented `git tag stage-review/<name>-<n>` as a
    state change, as it reads `git commit` and `git push` (its `tag` branch, beside `worktree`'s, reads a tag with a
    name as a state change and `-l` as a read), so a chain carrying it is refused as theirs is (rule 8); the tag's read and
    the remote-branch list are reads."""
    guard = program("permission-guard")
    documented = [cmd for _src, cmd in collect_commands()]
    tag = "git tag stage-review/<name>-<n>"
    assert tag in documented, tag
    assert "commit" in guard.STATE_GIT and "push" in guard.STATE_GIT
    sample = lambda c: re.sub(r"<[A-Za-z][^<>\n]*>", "placeholder", c)   # placeholders are prose (R-082, TASK-063)
    for cmd in (tag, "git tag stage-review/T1-1", "git commit -m x", "git push origin task-040"):
        assert guard.state_changing(guard.words(sample(cmd))), cmd
    for cmd in ("git cat-file -p stage-review/<name>-<n>:<path>", "git branch -r", "git tag -l"):
        assert cmd in documented or cmd == "git tag -l", cmd
        assert not guard.state_changing(guard.words(sample(cmd))), cmd


def test_r087_push_scan_rule_in_allow():
    """R-087 (TASK-067): push-scan.py, a read-only command, is allowed with and without its base."""
    rule = "Bash(python ~/.claude/cursor-bridge/push-scan.py:*)"
    assert rule in ALLOW
    for cmd in ("python ~/.claude/cursor-bridge/push-scan.py",
                "python ~/.claude/cursor-bridge/push-scan.py origin/main"):
        assert decide(cmd, ALLOW, DENY)[0] == "allow", cmd


def test_r088_in_flight_rule_in_allow():
    """R-088 (TASK-068): in-flight.py is allowed for a text, a file, and a review pass."""
    rule = "Bash(python ~/.claude/cursor-bridge/in-flight.py:*)"
    assert rule in ALLOW
    for cmd in ('python ~/.claude/cursor-bridge/in-flight.py "TASK-068 builder r1 launched"',
                "python ~/.claude/cursor-bridge/in-flight.py --file run/supervisor/line.txt",
                "python ~/.claude/cursor-bridge/in-flight.py --pass PR-7 review-a --round 2 --cause records",
                'python ~/.claude/cursor-bridge/in-flight.py --pass TASK-068 review-b --round 1 --cause "no external path"'):
        assert decide(cmd, ALLOW, DENY)[0] == "allow", cmd


def test_r062_records_migrate_rule_in_allow():
    """R13: records-migrate.py is allowed for a normal run and for --check."""
    rule = "Bash(python ~/.claude/cursor-bridge/records-migrate.py:*)"
    assert rule in ALLOW
    for cmd in ("python ~/.claude/cursor-bridge/records-migrate.py",
                "python ~/.claude/cursor-bridge/records-migrate.py --check"):
        assert decide(cmd, ALLOW, DENY)[0] == "allow", cmd
