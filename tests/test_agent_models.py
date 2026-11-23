"""Model allocation (rule 48, KP-036): every agent definition names a current model, the
reviewers carry high effort, the roster template matches Review A, no legacy id remains."""
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUDE = os.path.join(HERE, os.pardir, "bridge")
AGENTS = os.path.join(CLAUDE, "agents")

CURRENT = {"claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-2", "claude-haiku-4-5"}
# 4.x and plain 5 ids, and Fable 5.1, which Fable 5.2 replaced for planning (R-099); Haiku 4.5 is current
LEGACY = re.compile(r"claude-(?!haiku-4-5)(?:(opus|sonnet|fable|haiku)-(4-[0-9]|5)|fable-5-1)(?![-.0-9])")
EXPECTED = {
    "diff-reviewer": ("claude-opus-5-5", "high"), "security-auditor": ("claude-opus-5-5", "high"),
    "design-auditor": ("claude-opus-5-5", "high"), "refactor-scout": ("claude-opus-5-5", "high"),
    "spec-packager": ("claude-opus-5-5", None), "diagram-specialist": ("claude-opus-5-5", None),
    "plan-critic": ("claude-fable-5-2", None),
    "test-runner": ("claude-sonnet-5-5", None), "secret-sentinel": ("claude-sonnet-5-5", None),
    "cursor-configurator": ("claude-sonnet-5-5", None),
}


def frontmatter(name):
    text = open(os.path.join(AGENTS, name + ".md"), encoding="utf-8").read()
    head = text.split("\n---\n", 1)[0]
    fields = {}
    for line in head.splitlines()[1:]:
        k, _, v = line.partition(":")
        fields[k.strip()] = v.strip()
    return fields


def test_every_agent_definition_is_covered():
    names = sorted(f[:-3] for f in os.listdir(AGENTS) if f.endswith(".md"))
    assert names == sorted(EXPECTED), "a new agent definition needs a model in the allocation (rule 48)"


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_agent_model_and_effort(name):
    fm = frontmatter(name)
    model, effort = EXPECTED[name]
    assert fm.get("model") == model, "%s: model %r" % (name, fm.get("model"))
    assert fm.get("model") in CURRENT
    assert fm.get("effort") == effort, "%s: effort %r" % (name, fm.get("effort"))


SEARCHERS = tuple(sorted(EXPECTED))                 # every agent searches, so every agent has the folder rule (first review of A2, finding 8)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_every_agent_has_a_turn_limit_and_every_searcher_its_folders(name):
    """Release A2 (plan 10.3): a reviewer that searched the whole disk ran seven hours."""
    fm = frontmatter(name)
    assert fm.get("maxTurns", "").isdigit() and 10 <= int(fm["maxTurns"]) <= 60, "%s: maxTurns %r" % (name, fm.get("maxTurns"))
    if name in SEARCHERS:
        text = open(os.path.join(AGENTS, name + ".md"), encoding="utf-8").read()
        assert "never the home folder, another project or the whole disk" in text, "%s names no folder limit" % name
        body = text.split("\n---\n", 1)[1].strip()
        first = body.split("\n\n", 1)[0]
        assert body.count(first) == 1, "%s repeats its opening paragraph" % name


def test_roster_template_matches_review_a():
    policy = open(os.path.join(CLAUDE, "cursor-bridge", "Merge-Verification-Policy.md"), encoding="utf-8").read()
    m = re.search(r'"review_a":\s*"([^"]+)"', policy)
    assert m and m.group(1) == frontmatter("diff-reviewer")["model"]
    prog = open(os.path.join(CLAUDE, "cursor-bridge", "roster-check.py"), encoding="utf-8").read()
    m2 = re.search(r'"review_a":\s*"([^"]+)"', prog)
    assert m2 and m2.group(1) == m.group(1)


def test_r099_the_plan_critic_runs_on_fable_5_2_and_a_leftover_5_1_id_reads_legacy():
    """R-099 (the owner's allocation of 2026-11-13, rule 52): design and planning run on Fable 5.2, so the plan
    critic's definition carries `model: claude-fable-5-2`, and a leftover `claude-fable-5-1` in any agent
    definition is a legacy id."""
    assert frontmatter("plan-critic").get("model") == "claude-fable-5-2"
    assert LEGACY.search("model: claude-fable-5-1\n")
    assert not LEGACY.search("model: claude-fable-5-2\n")
    for name in sorted(EXPECTED):
        text = open(os.path.join(AGENTS, name + ".md"), encoding="utf-8").read()
        assert not LEGACY.search(text), "%s names a legacy model id" % name


def test_no_legacy_model_id_in_the_tree():
    offenders = []
    for root, _, files in os.walk(CLAUDE):
        for f in files:
            if f == "CHANGELOG.md" or f == "Known-Pitfalls.md" or not f.endswith((".md", ".py", ".json")):
                continue  # history may name old models
            text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
            for m in LEGACY.finditer(text):
                offenders.append("%s: %s" % (f, m.group(0)))
    assert not offenders, offenders
