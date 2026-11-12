"""R-050, R-051 and R-042 as revised (release T, TASK-039): rule 6, convergence and the ceiling's text; briefs, reports
and the accept step.

enforces: docs/REQUIREMENTS.md R-050, R-051, R-042 (its revision sentence); docs/BUILD_PLAN.md TASK-039, Done when;
docs/DESIGN.md, Change: release T (the table of what changes, rows R-050 and R-051).

One test per item label that keeps one (R-050: T18; R-051: T21, P11, T15, P13, T24, P6, T13), each pinning its
sentence in every home the design's table names. Release S retired the tests of R-050's P1, P2, P3 and T20 and of
R-051's P12 and T10, and the convergence tests of tests/test_loop_text_pace.py that held R-042's revision (prose
literals; the register names the text). KP-052: the one non-ASCII character these pins need, the em dash, is built
with chr(), never typed."""
import os

from phase_modules import flat, read

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge")
CB = os.path.join(BRIDGE, "cursor-bridge")
PHASES = os.path.join(CB, "workflow", "phases")
LOOP = os.path.join(PHASES, "delegation-loop.md")
DECIDE = os.path.join(PHASES, "delegation-loop", "decide.md")
AGENTS = os.path.join(BRIDGE, "agents")
REVIEWERS = ("diff-reviewer.md", "security-auditor.md", "design-auditor.md")
PACKAGER = os.path.join(AGENTS, "spec-packager.md")
SENTINEL = os.path.join(AGENTS, "secret-sentinel.md")
EM = chr(0x2014)


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i + len(start))]


def paragraph(text, start):
    i = text.index(start)
    return flat(text[i:text.index("\n\n", i)])


def accept():
    return flat(between(read(DECIDE), "- **Accept**", "- **Iterate**"))


def loop_step(start, end):
    return flat(between(read(LOOP), start, end))


def survival():
    return loop_step("### What must survive a compaction", "### The procedure")


def packager_done():
    return flat(between(read(PACKAGER), "## Done\n", "## The refactoring variant"))


def agent_paragraph(name):
    return paragraph(read(os.path.join(AGENTS, name)), "**The threat model, the class and the count.**")


# --------------------------------------------------------------------------- R-050


def test_r050_t18_a_supervisor_authored_increment_takes_the_test_strength_rule():
    """T18: tests first, a supervisor-side driver and each kill judged by the test it names, for an increment the
    supervisor writes, before its gate (step 4, where the new tests are run)."""
    s4 = loop_step("### 4. Inspect", "### 5. Scan")
    assert ("An increment you write yourself (`Author: supervisor.` in its plan entry) takes the same test-strength rule "
            "before its gate: its tests written first and run against its checkpoint (below), its mutants in its mutants "
            "file run by the bridge's engine, and each kill judged by the test it names.") in s4
    assert s4.index("An increment you write yourself") < s4.index("**Then every new test runs once against the checkpoint")


# --------------------------------------------------------------------------- R-051


def test_r051_t21_printed_lines_verbatim_mutations_by_label_not_run():
    """T21: the brief's Done asks for every printed line verbatim in a fenced block, each mutation by the brief's own
    label and text, and `not run` where a command was not run."""
    d = packager_done()
    assert "Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block;" in d
    assert "Each mutation is listed by this brief's own label and text, with what caught it." in d
    assert "A command you did not run is written `not run`, never described as run." in d


def test_r051_p11_every_count_quotes_its_line_and_the_reviewer_compares():
    """P11: every count and every claim of a check in a builder's report and in the accept commit's message quotes the
    output line that shows it; the three reviewers compare each count with its line."""
    assert "a count, or a claim that a check passed, quotes the output line that shows it." in packager_done()
    assert ("Commit to the increment branch with a message referencing the task ID, every count and every claim of a "
            "check in it quoting the output line that shows it (a reviewer compares each count with its line).") in accept()
    for name in REVIEWERS:
        assert ("Compare every count a builder's report or the accept commit's message gives with the output line it "
                "quotes: a count with no line, or one its line does not show, is a finding.") in agent_paragraph(name)


def test_r051_t15_the_rebuild_at_a_profile_switch():
    """T15: the change in flight at a profile switch is rebuilt by the new profile's builder, roster-check.py printing
    its REBUILD line and the launcher refusing that Review B until then (the two programs' own words)."""
    s3b = loop_step("### 3b.", "#### Waiting for the slot")
    assert ("A change in flight that the old profile's builder built is rebuilt by the new profile's builder before any "
            "Review B reads it: `roster-check.py` prints a `REBUILD` line when the new Review B is of the family that "
            "built it, and the launcher refuses that Review B until the rebuild.") in s3b
    assert s3b.index("**Restart the interrupted step**") < s3b.index("A change in flight that the old profile's") < s3b.index("**Record and report.**")
    roster = read(os.path.join(CB, "roster-check.py"))
    assert "REBUILD" in roster and "the launcher refuses Review B until then" in roster


def test_r051_p13_the_resume_reads_the_output_and_err_first():
    """P13: after an interruption the background task's output and its `.err` first; with a snapshot open `verify` only
    once the run has ended; an `.err` with no `bridge-run: exit` line a run still going, waited for or ended with
    bridge-stop.py first."""
    s = survival()
    assert ("- after an interruption (a compaction, a resume, a session ended mid-run), the background task's output and "
            "its `.err` file, read first: with a snapshot open, `review-guard.py verify` runs before anything else once "
            "the run has ended, an `.err` holding `bridge-run: exit`; one with no such line is a run still going, waited "
            "for or ended with `bridge-stop.py` first, since a `verify` during the run resets the tree under the "
            "reviewer;") in s
    assert s.index("- after an interruption") < s.index("- while step 9 runs")


def test_r051_t24_invisible_check_against_origin_main_in_the_sentinel():
    """T24: the sentinel runs invisible-check.py against `origin/main`, so every commit of the branch is read, in the
    loop's step 5 and the sentinel's definition; the program takes the base as its one positional argument."""
    s5 = loop_step("### 5. Scan", "### 5b.")
    assert ("It runs `python ~/.claude/cursor-bridge/invisible-check.py origin/main` first (release A4), against "
            "`origin/main` so that every commit of the branch is read:") in s5
    assert ("Run `python ~/.claude/cursor-bridge/invisible-check.py origin/main` from the Workspace root (release A4; "
            "against `origin/main`, so every commit of the branch is read, not only what is uncommitted):") in flat(read(SENTINEL))
    assert "invisible-check.py [<base-ref>]" in read(os.path.join(CB, "invisible-check.py"))


def test_r051_p6_invisible_check_before_every_commit_and_escapes_as_text():
    """P6: invisible-check.py before every commit of the supervisor's, a brief's and a records commit included, in the
    form the program has (its default base HEAD; it has no `--staged` option); spec-packager writes an escape as text,
    never through a tool or shell that reads escapes."""
    s5 = loop_step("### 5. Scan", "### 5b.")
    assert ("Before every commit of yours as well %s a brief's, the accept commit, a records commit %s run `python "
            "~/.claude/cursor-bridge/invisible-check.py` with its default base, `HEAD`, which reads everything the "
            "commit takes: the staged, the unstaged and the untracked changes." % (EM, EM)) in s5
    assert "--staged" not in s5 and "--staged" not in read(SENTINEL)
    rules = flat(between(read(PACKAGER), "## Rules", "## Output"))
    # BUG-040 (stage T1's review, Review A's S2): a character a brief must not hold is named by its code point
    assert ("**Escapes as text; non-ASCII listed.** Name a character a brief must mention but must not hold by its "
            "code point (U+202E), never by a typed backslash escape, which no tool writes safely, the file-writing "
            "tool included (KP-052); write a backtick or a backslash through the file-writing tool, never through a "
            "shell that reads escapes (a here-document, an inline command), which reads a backslash sequence as the "
            "real character, a right-to-left override among them.") in rules


def test_r051_t13_the_briefs_non_ascii_characters_listed_before_the_checkpoint():
    """T13: spec-packager lists a brief's non-ASCII characters, by line and code point, before the checkpoint commit."""
    rules = flat(between(read(PACKAGER), "## Rules", "## Output"))
    assert ("Before the supervisor's checkpoint commit, list in your report back every non-ASCII character the brief "
            "holds, by line and code point, so that each is checked.") in rules
