"""R-100 and D-004 (TASK-080): the Claude side's library documentation through Context7, as the probe of 2026-11-23
decided it (docs/HARDENING.md, TASK-080).

- The first form is built: a subagent whose `tools:` line names an absent server's tools starts and works, and receives
  the server's tools once Claude Code has the server at user scope; so `spec-packager` and `diff-reviewer` name the
  server's tools on their `tools:` lines, beside the tools they had.
- No allow entry: in auto mode a call to the server's tool ran without a question and without an entry, so
  `settings.bridge.json` names none.
- D-004 draws the first form: the two subagents query the documentation service.

Not pinned: the wording of the lookup's rules (instruction text, release S: the reviewers' read is its check)."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.join(HERE, os.pardir, "bridge")
D004 = os.path.join(HERE, os.pardir, "docs", "diagrams", "D-004-context-dfd.md")

TOOLS = {
    "spec-packager": "Read, Grep, Glob, Write, mcp__context7__*",
    "diff-reviewer": "Read, Grep, Glob, Bash, mcp__context7__*",
}


def tools_line(name):
    with open(os.path.join(BRIDGE, "agents", name + ".md"), encoding="utf-8") as f:
        head = f.read().split("\n---\n", 1)[0]
    found = [line.partition(":")[2].strip() for line in head.splitlines() if line.startswith("tools:")]
    assert len(found) <= 1, "%s: one tools line at most, found %d" % (name, len(found))
    return found[0] if found else None


def test_r100_the_two_agents_name_the_documentation_server_s_tools():
    for name, line in TOOLS.items():
        assert tools_line(name) == line, name


def test_r100_no_other_agent_names_the_documentation_server():
    """An agent with no `tools:` line inherits every tool of the session, the server's among them: only
    `cursor-configurator` has none (it writes configuration and is given no lookup rule), recorded in HARDENING."""
    without = []
    for f in sorted(os.listdir(os.path.join(BRIDGE, "agents"))):
        name = f[:-3]
        if not f.endswith(".md") or name in TOOLS:
            continue
        line = tools_line(name)
        if line is None:
            without.append(name)
        else:
            assert "mcp__context7" not in line, name
    assert without == ["cursor-configurator"], without


def test_r100_no_allow_entry_for_the_documentation_server():
    with open(os.path.join(BRIDGE, "cursor-bridge", "settings.bridge.json"), encoding="utf-8") as f:
        settings = json.load(f)
    assert not [rule for rule in settings.get("permissions", {}).get("allow", []) if "context7" in rule.lower()]


def test_d004_draws_the_two_subagents_querying_the_documentation_service():
    with open(D004, encoding="utf-8") as f:
        text = f.read()
    assert re.search(r"^ext_docs_service\[", text, re.M)
    assert re.search(r"p_claude_subagents\s*-->.*ext_docs_service", text)
