"""Release A1a (plan review R8 and R17): the sources are out of .claude, and the bridge's own
text no longer contradicts itself on what a builder may write, on Review A's verdict words,
on the number of run parameters, or on where pinned versions are recorded."""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
BRIDGE = os.path.join(ROOT, "bridge")


def text(*parts):
    return open(os.path.join(BRIDGE, *parts), encoding="utf-8").read()


SV = text("commands", "supervisor.md")
CLAUSE = "Do not modify .env, secrets/, CI configuration, or anything under docs/ or handoff/ unless the Scope section names the file."


def test_no_governance_file_is_tracked_under_dot_claude():
    """KP-037: Claude Code loads a project's .claude folder; the sources must not live there."""
    p = subprocess.run(["git", "ls-files", "--", ".claude"], cwd=ROOT, capture_output=True, text=True)
    assert p.returncode == 0 and p.stdout.strip() == "", p.stdout
    for sub in ("agents", "commands", "skills", "cursor-bridge"):
        assert os.path.isdir(os.path.join(BRIDGE, sub))
        assert not os.path.isdir(os.path.join(ROOT, ".claude", sub))


def test_the_delegate_command_is_one_text_in_all_its_places():
    commands = re.findall(r'cursor-agent -p --force[^"\n]*"(Read handoff/[^"]+)"', SV)
    assert len(commands) == 3, "the digest, step 3 and the parallel variant"
    assert all(CLAUSE in c for c in commands), commands
    bodies = {re.sub(r"TASK-<[a-z]+>", "TASK-<n>", c) for c in commands}
    assert len(bodies) == 1, "the constant command differs between its places: %r" % bodies


def test_the_brief_and_the_command_agree_on_what_a_builder_may_write():
    sp = text("agents", "spec-packager.md")
    scope = sp[sp.index("## Scope"):sp.index("## Out of scope")]
    assert "- docs/BUILDER_NOTES.md\n" in scope, "the brief asks the builder to append to this file, so Scope names it"
    out = sp[sp.index("## Out of scope"):sp.index("## Context")]
    assert "docs/ and handoff/, except the files the Scope section names" in out
    assert "`docs/BUILDER_NOTES.md`" in sp[sp.index("## Constraints"):]
    assert "docs/cli-reference.json" in sp[:sp.index("## Write to")], "the packager is told when the command reference goes in Scope"


def test_review_a_answers_in_the_merge_policy_words():
    dr = text("agents", "diff-reviewer.md")
    assert "VERDICT: APPROVE | REJECT | ESCALATE-INTENT" in dr
    assert "`FAIL`" not in dr and "PASS WITH FINDINGS" not in dr
    policy = text("cursor-bridge", "Merge-Verification-Policy.md")
    assert "Review A = APPROVE AND Review B = APPROVE" in policy
    for word in ("`APPROVE`", "`REJECT`", "`ESCALATE-INTENT`"):
        assert word in dr and word in policy


def test_five_run_parameters_everywhere():
    names = ["Stage pause", "Merge authority", "Refactoring pass", "Installer verification", "Parallel increments"]
    template = SV[SV.index("# Run parameters\n"):]
    template = template[:template.index("```")]
    for n in names:
        assert (n + ":") in template, n
    rule = re.search(r"^29\. .*?(?=^30\. )", SV, re.M | re.S).group(0)
    for n in names:
        assert ("`%s`" % n) in rule, "rule 29 does not name %s" % n
    status_line = re.search(r"^Run parameters: see docs/RUN_PARAMETERS\.md \(([^)]*)\)", SV, re.M).group(1)
    assert [x.strip() for x in status_line.split("/")] == [n.lower() for n in names]


def test_no_convention_sends_a_pin_to_the_status_file():
    offenders = []
    folder = os.path.join(BRIDGE, "cursor-bridge")
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md") or name in ("CHANGELOG.md",) or name.endswith(".snapshot.md"):
            continue
        lines = open(os.path.join(folder, name), encoding="utf-8").read().split("\n")
        for i, line in enumerate(lines):
            if "PROJECT_STATUS.md" not in line:
                continue
            window = " ".join(lines[max(0, i - 2): i + 1]).lower()
            if re.search(r"\bpin|version|ruleset|\bsha\b|tier", window) and re.search(r"\brecord", window) and "worktree" not in window:
                offenders.append("%s:%d %s" % (name, i + 1, line.strip()[:100]))
    assert not offenders, offenders
    assert "Pinned versions and configured modes are Resources" in SV
