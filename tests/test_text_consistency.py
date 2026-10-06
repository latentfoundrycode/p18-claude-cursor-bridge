"""Release A1a (plan review R8 and R17): the sources are out of .claude, and the bridge's own
text no longer contradicts itself on what a builder may write, on Review A's verdict words,
on the number of run parameters, or on where pinned versions are recorded."""
import importlib.util
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
    assert "docs/CLI_REFERENCE.md" in sp[:sp.index("## Write to")], "and its rendered copy, which the builder's generator writes"


def test_the_fix_and_the_refactoring_briefs_name_the_notes_file_too():
    """Review of 2026.10.05a, finding 2: both variants said "Scope: these files, nothing
    else" while inheriting the Constraints that ask for the note."""
    sp = text("agents", "spec-packager.md")
    variants = [line for line in sp.split("\n") if line.startswith("- **Scope** names")]
    assert len(variants) == 2, variants
    assert all("`docs/BUILDER_NOTES.md`" in line for line in variants), variants


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
    names = [n for n in sorted(os.listdir(folder)) if n.endswith(".md") and n != "CHANGELOG.md" and not n.endswith(".snapshot.md")]
    for name in names + [os.path.join(os.pardir, "commands", "supervisor.md")]:
        lines = open(os.path.join(folder, name), encoding="utf-8").read().split("\n")
        for i, line in enumerate(lines):
            # the bridge's own version and the conformance check's notes are the status file's by its template
            if "PROJECT_STATUS.md" not in line or any(own in " ".join(lines[max(0, i - 1): i + 1]) for own in ("its version is recorded in", "record `NOTE`s in")):
                continue
            window = " ".join(lines[max(0, i - 2): i + 1]).lower()
            if re.search(r"\bpin|version|ruleset|\bsha\b|tier", window) and re.search(r"\brecord", window) and "worktree" not in window:
                offenders.append("%s:%d %s" % (os.path.basename(name), i + 1, line.strip()[:100]))
    assert not offenders, offenders
    assert "Pinned versions and configured modes are Resources" in SV


def test_a_commit_pin_is_recorded_by_its_file_and_the_inventory_check_accepts_what_is_asked():
    """Review of 2026.10.05a, finding 4: the conventions sent every pinned commit to the
    inventory, whose check reads a 40-character token as a leaked key."""
    spec = importlib.util.spec_from_file_location("inventory_check", os.path.join(BRIDGE, "cursor-bridge", "inventory-check.py"))
    ic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ic)
    sha = "b4ffde65f46336ab88eb53be808477a3936bae11"
    for cell in ("Semgrep 1.90.0 in .pre-commit-config.yaml", "pinned by commit in .github/workflows/gate.yml", "Tier A", "ASVS level 2",
                 "snapshot of 2026-09-10", "jscpd 4.0.5 in package.json"):
        assert not ic.looks_secret(cell), cell
    assert ic.looks_secret(sha) and ic.looks_secret("actions/checkout@" + sha) and ic.fingerprint_like("actions/checkout@" + sha)
    assert not ic.fingerprint_like("sk-" + "a1" * 12)
    assert "never by its 40-character value" in SV
    for name in ("Cursor-Project-Configuration.md", "Cursor-File-Formats.md"):
        for line in text("cursor-bridge", name).split("\n"):
            if "INVENTORY.md" in line and "SHA" in line:
                assert "file" in line, "%s still asks for the value: %s" % (name, line.strip()[:120])


def test_no_text_puts_a_dependency_or_a_licence_question_to_the_owner():
    """Review of 2026.10.06b, finding 4: one dependency rule (56); a licence is never the owner's
    question (the owner's instruction of 2026-10-01)."""
    offenders = []
    for root, dirs, files in os.walk(BRIDGE):
        dirs[:] = [d for d in dirs if d != "design-seeds"]           # a seed's text about a brand's typefaces is not the bridge's rule
        for name in sorted(files):
            if not name.endswith(".md") or name.endswith(".snapshot.md") or name == "CHANGELOG.md":
                continue
            body = open(os.path.join(root, name), encoding="utf-8").read()
            for i, line in enumerate(body.split("\n")):
                low = line.lower()
                if re.search(r"licen[cs]", low) and re.search(r"\bask|escalat|question|the owner's call|clear(ed)? with the user|reaches the owner|to the owner", low) \
                        and not re.search(r"\bnever\b|no licence|out of scope", low):
                    offenders.append("%s:%d %s" % (name, i + 1, line.strip()[:110]))
                if re.search(r"dependenc", low) and re.search(r"\[escalate\]|escalate[sd]? (any|the|to the user)[^.]*dep|clear(ed)? with the user|new dependency/cost", low) and "rule 56" not in low:
                    offenders.append("%s:%d %s" % (name, i + 1, line.strip()[:110]))
    assert not offenders, offenders


def test_no_text_calls_a_review_outcome_a_fail():
    """Review A and Review B answer APPROVE, REJECT or ESCALATE-INTENT; only the auditors and
    the test runner keep PASS and FAIL."""
    for parts in (("commands", "supervisor.md"), ("cursor-bridge", "Diagram-Planning-Conventions.md"), ("cursor-bridge", "Glossary.md"),
                  ("skills", "root-cause-first", "SKILL.md")):
        for i, line in enumerate(text(*parts).split("\n")):
            assert not re.search(r"(is|and) a `FAIL`|A (review )?`FAIL`", line), "%s:%d %s" % (parts[-1], i + 1, line.strip()[:120])
