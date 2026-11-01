"""R-050, R-051 and R-042 as revised (release T, TASK-039): rule 6, convergence and the ceiling's text; briefs, reports
and the accept step.

enforces: docs/REQUIREMENTS.md R-050, R-051, R-042 (its revision sentence); docs/BUILD_PLAN.md TASK-039, Done when;
docs/DESIGN.md, Change: release T (the table of what changes, rows R-050 and R-051).

One test per item label of the two rows (R-050: P1, P2, P3, T20, T18; R-051: T21, P11, P12, T10, T15, P13, T24, P6,
T13), each pinning its sentence in every home the design's table names. R-042's revision is pinned where its old
sentence was, by the rewritten convergence tests of tests/test_loop_text_pace.py. KP-052: the one non-ASCII character
these pins need, the em dash, is built with chr(), never typed."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge")
CB = os.path.join(BRIDGE, "cursor-bridge")
PHASES = os.path.join(CB, "workflow", "phases")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
POLICY = os.path.join(CB, "Merge-Verification-Policy.md")
LOOP = os.path.join(PHASES, "delegation-loop.md")
DECIDE = os.path.join(PHASES, "delegation-loop", "decide.md")
MERGE = os.path.join(PHASES, "delegation-loop", "merge.md")
REFLECTION = os.path.join(PHASES, "reflection.md")
AGENTS = os.path.join(BRIDGE, "agents")
REVIEWERS = ("diff-reviewer.md", "security-auditor.md", "design-auditor.md")
PACKAGER = os.path.join(AGENTS, "spec-packager.md")
SENTINEL = os.path.join(AGENTS, "secret-sentinel.md")
EM = chr(0x2014)

# the sentences two or more homes share, as the homes give them
THREAT = ("What a defect of the five is for the project is bounded by its threat model, recorded in "
          "`docs/INVENTORY.md` (Decisions) with its reason and what would reopen it and given to the reviewers "
          "with the diff, for the parts the model names: a finding in those parts outside it is recorded, not "
          "blocking, whatever its label and however many reviewers name it, and where the inventory records no "
          "threat model for what the diff changes, the five stand unbounded.")
MEMBER = ("Within it, a finding is a member of a blocking class when it reproduces as a regression or a false result on "
          "an ordinary, realistic project layout, a reviewer's label alone never deciding: one that needs a contrived "
          "setup goes to `docs/HARDENING.md` with the increment, and a security finding is judged instead by whether "
          "untrusted input can reach it (files a builder or reviewer writes, a cloned or third-party repository), never "
          "by the layout's ordinariness.")
CERTAIN_LATE = ("Two reviewers naming the same late finding make it certain, never blocking of itself: it blocks only "
                "where its content is of the five")
CLASS_GATE = ("Two reviewers independently naming the same defect make it blocking where its content is of one of the "
              "five blocking classes, at any round; a convergent finding of another class is fixed by the next increment "
              "that edits its file, or recorded in `docs/HARDENING.md`, marked convergent, with no gate pass of its own.")
ONE_FAULT = "two findings on one line are one defect only where they name the same fault in it."
RECORDED = ("A class already recorded under the by-class line for that increment or that stage stays that class: two "
            "reviewers naming a further mutant, input or operator family of it name that class, which stays recorded and "
            "starts no round, and no class of the five is ever on that line.")
OUTSIDE = ("A finding outside the threat model `docs/INVENTORY.md` (Decisions) records for the part it is in is "
           "recorded, not blocking, however many reviewers name it; where none is recorded for that part, the "
           "five stand unbounded.")
RULE6 = 'a late finding then blocks only if it is of the five, within the threat model `docs/INVENTORY.md` records for the part it is in (outside it a finding is recorded, not blocking; where none is recorded, the five stand unbounded), its class shown by reproduction on an ordinary, realistic layout, a label alone never deciding (a security finding by whether untrusted input can reach it), two reviewers naming the same defect making it certain, never blocking of itself (the convergence rule).'
RULE36 = 'two reviewers naming the same defect make it certain, and blocking only where it is of the five (rule 6).'
DESIGN = os.path.join(PHASES, "design.md")
P3_LONG = ("against the code of the round it lifted as that round's builder found it %s the tree the guard's snapshot of "
           "the round before it recorded, whose commit you name beside the line in the SCOPE file %s never against the "
           "fixed code under review" % (EM, EM))
P3_SHORT = "against the code of the round it lifted, never against the fixed code under review"
AGENT_PARA = ("**The threat model, the class and the count.** The supervisor gives you the project's threat model with "
              "the diff (`docs/INVENTORY.md`, Decisions; at merge in the SCOPE file too) for the parts it names: a finding in "
              "those parts outside it is recorded, not blocking, whatever its label, and where none is recorded for what "
              "the diff changes, the five stand unbounded. Within it, a finding is of a blocking class only when it reproduces as a "
              "regression or a false result on an ordinary, realistic project layout, a label alone never deciding; one "
              "that needs a contrived setup goes to `docs/HARDENING.md`, and a security finding is judged instead by "
              "whether untrusted input can reach it. Another reviewer naming the same defect makes your finding certain, "
              "never blocking of itself: it blocks only where its content is of the five. Confirm or deny a `Blocking "
              "class:` line against the code of the round it lifted as that round's builder found it (the commit the SCOPE "
              "file names beside the line), never against the fixed code under review. Compare every count a builder's report or the accept commit's message gives with "
              "the output line it quotes: a count with no line, or one its line does not show, is a finding.")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def flat(text):
    return re.sub(r"\s+", " ", text)


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i + len(start))]


def paragraph(text, start):
    i = text.index(start)
    return flat(text[i:text.index("\n\n", i)])


def rule(n):
    body = read(CORE).split("\n## Standing rules\n", 1)[1]
    m = re.search(r"^%d\. (.*?)(?=^%d\. )" % (n, n + 1), body, re.S | re.M)
    return flat(m.group(1))


def redelegation():
    return paragraph(read(POLICY), "**Re-delegation runs while the code converges")


def brake():
    return flat(between(read(DECIDE), "**When to stop re-delegating", "**Split verdicts you resolve yourself"))


def convergence(path):
    return paragraph(read(path), "**Convergence is a signal.**")


def ceiling():
    return flat(between(read(DECIDE), "#### The review ceiling", "#### The mutation run"))


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


def test_r050_p1_one_defect_class_gated_in_every_home():
    """P1: two reviewers naming the same defect make it certain, and blocking only where its content is of the five; a
    convergent finding of another class is fixed by the next increment that edits its file or recorded, with no gate
    pass of its own; two findings on one line are one defect only where they name the same fault."""
    for path in (POLICY, MERGE):
        c = convergence(path)
        assert "independently name the same defect," in c, path
        assert "same line or the same defect" not in c, path
        assert ONE_FAULT in c and CLASS_GATE in c and RECORDED in c, path
        assert "two reviewers' agreement makes a finding blocking whatever its grade" not in c, path
    assert RULE6 in rule(6)
    assert "two reviewers naming the same defect making it certain, never blocking of itself (the convergence rule)." in rule(6)
    assert "or if two or more reviewers or auditors name it" not in rule(6)
    assert RULE36 in rule(36) and "converging on one line is blocking" not in rule(36)
    d = flat(read(DESIGN))
    assert ("The convergence rule of step 8 (two reviewers naming the same defect make it certain, and blocking only "
            "where it is of the five blocking classes) belongs to the code gate") in d
    assert "makes it blocking)" not in d
    for home in (redelegation(), brake()):
        assert CERTAIN_LATE in home
        assert "a late finding two or more reviewers or auditors name blocks too" not in home
    r = flat(read(REFLECTION))
    assert ("(the delegation loop's step 8: two or more reviewers independently naming the same defect, each alone "
            "calling it advisory, where its content is of one of the five blocking classes)") in r
    assert "the same line or the same defect" not in r
    for name in REVIEWERS:
        assert ("Another reviewer naming the same defect makes your finding certain, never blocking of itself: it blocks "
                "only where its content is of the five.") in agent_paragraph(name), name


def test_r050_p2_membership_by_reproduction_on_an_ordinary_layout():
    """P2: a finding is of a blocking class when it reproduces on an ordinary, realistic layout, a label alone never
    deciding, a contrived setup going to HARDENING; a security finding judged by whether untrusted input can reach it."""
    for home in (redelegation(), brake()):
        assert MEMBER in home
    assert ("its class shown by reproduction on an ordinary, realistic layout, a label alone never deciding (a "
            "security finding by whether untrusted input can reach it)") in rule(6)
    for name in REVIEWERS:
        p = agent_paragraph(name)
        assert ("Within it, a finding is of a blocking class only when it reproduces as a regression or a false result "
                "on an ordinary, realistic project layout, a label alone never deciding;") in p, name
        assert "a security finding is judged instead by whether untrusted input can reach it." in p, name


def test_r050_p3_the_class_line_against_the_round_it_lifted():
    """P3: a `Blocking class:` line is confirmed or denied against the code of the round it lifted, as that round's
    builder found it, never against the fixed code under review: step 7's class line, the directive's sixth clause, the
    policy's two statements of it and the three reviewers."""
    assert ("The reviewers are told of the line and confirm or deny it %s: a reviewer's denial voids" % P3_LONG) in ceiling()
    m = flat(read(MERGE))
    assert ("and confirm or deny the SCOPE file's `Blocking class:` line where it has one, %s)" % P3_SHORT) in m
    p = flat(read(POLICY))
    assert ("`Blocking class:` line, where it has one, confirmed or denied %s, and that the reply is one of" % P3_SHORT) in p
    assert ("or denies the round's `Blocking class:` line where it has one, %s; a denial is a breach" % P3_SHORT) in redelegation()
    for name in REVIEWERS:
        assert ("Confirm or deny a `Blocking class:` line against the code of the round it lifted as that round's "
                "builder found it (the commit the SCOPE file names beside the line), never against the fixed code under "
                "review.") in agent_paragraph(name), name
    assert ("and, at a round above the ceiling, that round's `Blocking class:` line with, beside it, the commit that "
            "round's builder started from (the head the previous round's snapshot recorded).") in m


def test_r050_t20_the_recorded_threat_model_bounds_the_five():
    """T20: a threat model recorded in the inventory's Decisions bounds what a defect of the five is, a finding outside
    it recorded, not blocking, however many name it; the reviewers get it with the diff, in the SCOPE file; it is read
    before P1's class gate and P2's membership rule."""
    for home in (redelegation(), brake()):
        assert THREAT in home
        assert home.index(THREAT) < home.index(MEMBER) < home.index(CERTAIN_LATE)
    for path in (POLICY, MERGE):
        assert OUTSIDE in convergence(path), path
    assert ("within the threat model `docs/INVENTORY.md` records for the part it is in (outside it a finding is "
            "recorded, not blocking; where none is recorded, the five stand unbounded)") in rule(6)
    r6 = rule(6)
    assert r6.index("within the threat model") < r6.index("its class shown by reproduction") < r6.index("(the convergence rule)")
    s4 = loop_step("### 4. Inspect", "### 5. Scan")
    assert ("Give it, and each auditor below, the project's threat model as `docs/INVENTORY.md`'s Decisions record it "
            "for what the diff changes, or say that none is recorded.") in s4
    m = flat(read(MERGE))
    assert ("where the increment ends, which tests the supervisor wrote and the project's threat model are in "
            "`run/review/SCOPE-<ID>.md`, read it") in m
    assert ("holds the brief's Scope and Out of scope sections quoted, the project's threat model as "
            "`docs/INVENTORY.md`'s Decisions record it, the tests,") in m
    assert ("where the supervisor wrote the brief's Scope and Out of scope, the project's threat model from "
            "`docs/INVENTORY.md`'s Decisions, the tests it wrote") in flat(read(POLICY))
    for name in REVIEWERS:
        p = agent_paragraph(name)
        assert AGENT_PARA in p, name
        assert ("The supervisor gives you the project's threat model with the diff (`docs/INVENTORY.md`, Decisions; "
                "at merge in the SCOPE file too) for the parts it names: a finding in those parts outside it is "
                "recorded, not blocking, whatever its label, and where none is recorded for what the diff changes, the "
                "five stand unbounded.") in p


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


def test_r051_p12_the_suite_once_after_the_last_edit_and_known_failures_named():
    """P12: the suite once, after the last edit, the report written after that run and naming the commit its counts
    belong to; a Done that runs the whole suite names the failures already known outside the Scope."""
    assert ("Where this brief has you run the suite, run it once, after your last edit, and write the report's results "
            "after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree "
            "then held uncommitted changes (`git status --short`).") in packager_done()
    sp = flat(read(PACKAGER))
    c = sp[sp.index("- Every verification command the Done section asks you to run"):sp.index("- Prefer reuse over new code")]
    assert ("Where the Done section runs the whole suite, this bullet names the failures already known outside the "
            "Scope, each by its test id, so that you report them as known and fix none of them.") in c


def test_r051_t10_the_records_in_a_records_only_commit_after_the_accept():
    """T10: the records go in a records-only commit after the accept commit, the CHANGES.md entry and the register's
    flip with them."""
    a = accept()
    assert "Then the records go in a records-only commit after the accept commit:" in a
    assert "with the increment's `CHANGES.md` entry in the same records commit, moving `Reflected through:` to that entry (rule 41);" in a
    assert "in its Evidence cell, in that records commit." in a
    assert "in the same commit as the increment's `CHANGES.md` entry" not in a
    assert a.index("every count and every claim of a check") < a.index("Then the records go in a records-only commit")


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
    assert ("**Escapes as text; non-ASCII listed.** Write an escape sequence or a backtick as the characters you mean, "
            "through the file-writing tool, never through a tool or a shell that reads escapes (a here-document, an "
            "inline command): a shell reads a backslash sequence as the real character, a right-to-left override among "
            "them (KP-052).") in rules


def test_r051_t13_the_briefs_non_ascii_characters_listed_before_the_checkpoint():
    """T13: spec-packager lists a brief's non-ASCII characters, by line and code point, before the checkpoint commit."""
    rules = flat(between(read(PACKAGER), "## Rules", "## Output"))
    assert ("Before the supervisor's checkpoint commit, list in your report back every non-ASCII character the brief "
            "holds, by line and code point, so that each is checked.") in rules
