"""R-047, R-048, R-053 (release T, TASK-037): the design critique's record and mechanics, the reports and run sheets,
project state and the design's lenses.

enforces: docs/REQUIREMENTS.md R-047, R-048, R-053; docs/BUILD_PLAN.md TASK-037, Done when; docs/DESIGN.md, Change:
release T (the table of what changes, rows R-047, R-048, R-053).

One test per item label of the three rows (R-047: T1, T3, T7, T26; R-048: D11, D10, D7, D6; R-053: P10, P9, P20),
each pinning its sentence in the home the design's table names. KP-052: the one non-ASCII character these pins need,
the template's ellipsis, is built with chr(), never typed."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
CALIBRATE = os.path.join(BRIDGE, "commands", "calibrate-bridge.md")
SKILL = os.path.join(BRIDGE, "skills", "explain-for-decision", "SKILL.md")
PLAN_CRITIC = os.path.join(BRIDGE, "agents", "plan-critic.md")
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")
DESIGN = os.path.join(PHASES, "design.md")
CHANGE_CYCLE = os.path.join(PHASES, "change-cycle.md")
CONVENTIONS = os.path.join(BRIDGE, "cursor-bridge", "Diagram-Planning-Conventions.md")
ELLIPSIS = chr(0x2026)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def flat(text):
    return re.sub(r"\s+", " ", text)


def section(text, title):
    """The section under the heading `title`, up to the next heading of its level or higher; a line inside a fenced
    block (the status template's `# Project Status`, say) is no heading."""
    lines = text.split("\n")
    fenced, start, level = False, None, 0
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fenced = not fenced
            continue
        m = None if fenced else re.match(r"(#+) (.*)$", line)
        if m and start is None and m.group(2) == title:
            start, level = i + 1, len(m.group(1))
        elif m and start is not None and len(m.group(1)) <= level:
            return "\n".join(lines[start:i])
    assert start is not None, "heading %r" % title
    return "\n".join(lines[start:])


def rule(n):
    """Standing rule n of the core, from its number to the next rule's."""
    rules = section(read(CORE), "Standing rules")
    start = re.search(r"^%d\. " % n, rules, re.M).start()
    end = re.search(r"^%d\. " % (n + 1), rules, re.M).start()
    return flat(rules[start:end])


def digest():
    text = read(CORE)
    return text[text.index("<!-- digest:start -->"):text.index("<!-- digest:end -->")]


def item(text, number, label):
    """A numbered item of a procedure list, from `<number>. **<label>**` to the next item."""
    start = text.index("\n%d. **%s**" % (number, label))
    end = text.index("\n%d. **" % (number + 1), start)
    return flat(text[start:end])


def test_r047_t1_a_plan_addendum_from_round_1_is_one_subject_with_the_design():
    """T1: a plan addendum whose increments stood in the design's review file from round 1 is criticised and gated
    with the design as one subject, the record naming both (design.md, the critique's subjects)."""
    assert ("A plan addendum whose increments stood in the design's review file from round 1 is no subject of its "
            "own: it is criticised and gated with the design as one subject, under the design's token, and the "
            "subject's block heading in `docs/DESIGN_CRITIQUE.md` names both.") in flat(section(read(DESIGN), "The procedure"))


def test_r047_t3_the_records_definitions():
    """T3: "the commit its file was built from" is the subject's head when the file was assembled; a round in which
    one critic delivered is a critique round, the other recorded "not run (reason)" (design.md, the record)."""
    procedure = flat(section(read(DESIGN), "The procedure"))
    assert ("The commit its file was built from is the subject's head when the round's file was assembled; a round "
            "in which one critic delivered is a critique round, the other critic's row reading "
            "`not run (<the reason>)`.") in procedure
    # Review A, round 1, B1: the failed-launch paragraph agrees: Review B's row, not the round, is not run
    assert ("makes the design wait (below), Review B's row recorded as `not run (<the reason>)`. A round counts "
            "against the four once either critic delivered in it (the record's definitions, below); a round in which "
            "neither delivered is never run and spends none of the four.") in procedure
    assert "If that launch fails too, Review B's row stays `not run (<the reason>)` and the subject goes on" in procedure
    assert "the round recorded as not run" not in procedure and "the round stays not run" not in procedure


def test_r047_t7_the_snapshot_id_and_the_err_name_together():
    """T7: the design round's snapshot id is `DESIGN-<subject>-<round>` and the `.err` name follows from it."""
    procedure = flat(section(read(DESIGN), "The procedure"))
    assert ("The snapshot's id is the round file's name, `DESIGN-<subject>-<round>` (`review-guard.py snapshot "
            "DESIGN-<subject>-<round>`, then `verify` under the same id), and the `.err` file's name follows from "
            "it, `run/review/REVIEW-DESIGN-<subject>-<round>.err`, as the command above writes it.") in procedure
    assert "2> run/review/REVIEW-DESIGN-<subject>-<round>.err" in procedure


def test_r047_t26_the_pause_before_planning_work_with_a_push_notification():
    """T26 (rule 48): a plan revision mid-build and a change's design are planning work; the supervisor pauses before
    them and names the model to set, with a push notification when the owner has Remote Control on; the change
    cycle's item 2 says the same for a change's design."""
    assert ("A plan revision mid-build and a change's design are planning work: you pause before each, name the "
            "model to set (Fable 5.1, as for a design revision), and, where the owner has Remote Control on, send a "
            "push notification (`PushNotification`) carrying that line, since the owner may be away from the screen; "
            "the work starts on the owner's word that the model is set.") in rule(48)
    # Review A, round 1, S1: the rule's "nothing else waits" names planning work's exception
    assert ("report leads with the switch and nothing else waits on it, save planning work (below), which waits "
            "for the switch.") in rule(48)
    assert ("Pause before it: a change's design is planning work (rule 48), so you stop, the report naming the "
            "model to set, Fable 5.1, with a push notification (`PushNotification`) carrying that line where the "
            "owner has Remote Control on; the design starts on the owner's word that the model is set.") in \
        item(read(CHANGE_CYCLE), 2, "Design revision")


def test_r048_d11_a_turn_ending_on_a_run_names_its_limit():
    """D11 (rule 43): a turn that ends on a builder or reviewer run names the run's limit in the report."""
    assert ("A turn that ends on a builder or reviewer run names the run's limit in the report (\"the builder runs "
            "until 19:16 at the latest\"), its end worked out from the launcher's lines in the run's `.err` or output "
            "file (the `slot taken` time for a heavy run, else the `started` time, plus the `limit` line's seconds, "
            "all in UTC) and given on the computer's clock, read from `date` (KP-039), so the owner knows when a "
            "running delegation is late.") in rule(43)


def test_r048_d10_a_vendor_console_from_documentation_fetched_at_the_time():
    """D10 (the run-sheet template): an instruction that sends the owner into a vendor's console is written from the
    vendor's documentation fetched at the time, with the exact path."""
    sheet = flat(section(read(SKILL), "Handing the user something to run " + chr(0x2014) + " the run sheet"))
    assert ("- A step that sends the owner into a vendor's console (a dashboard, a settings or billing page) is "
            "written from the vendor's documentation, fetched at the time, with the exact path to the field or "
            "figure; never from memory, and the owner is never sent to look for a figure the sheet has not "
            "located.") in sheet


def test_r048_d7_rule_12_in_the_question_form_in_the_core_and_the_digest():
    """D7: the digest's rule 12 reads "Reports lead with the owner's decision, asked in the question form", and the
    core's rule 12 says what the question form is; the digest's cap and its rule numbers are
    tests/test_session_start.py's."""
    assert "12 Reports lead with the owner's decision, asked in the question form. 13 " in digest()
    assert ("A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended "
            "option first), so that answering it is one choice.") in rule(12)


def test_r048_d6_the_calibrated_line_is_rewritten():
    """D6: the `Calibrated:` line is rewritten at each calibration, holding the latest calibration and its pending
    items, the earlier text living in git (calibrate-bridge.md step 5 and the status template)."""
    assert ("The line is rewritten at each calibration, never appended to: it holds the latest calibration and its "
            "pending items, and the earlier text lives in git.") in flat(section(read(CALIBRATE), "5. Record and report"))
    template = section(read(CORE), "Project state")
    fence = template[template.index("```markdown\n"):template.index("\n```\n", template.index("```markdown\n"))]
    line = [l for l in fence.split("\n") if l.startswith("Calibrated: ")]
    assert line == ["Calibrated: <date> from <old> to <new> " + chr(0x2014) + " applied: %s; pending: %s @ <phase>; "
                    "not applied (gate passed): %s (rewritten at each calibration; the earlier text lives in git)"
                    % (ELLIPSIS, ELLIPSIS, ELLIPSIS)]


def test_r053_p10_a_decided_rule_not_yet_built():
    """P10 ("Project state"): a Decisions row whose rule a later increment or release builds says whether it applies
    from the decision and how it is held until built; the next report names every decided-but-unbuilt rule; a release
    that adds a safety mechanism says in its Running projects items how the loop holds it by hand."""
    assert ("**A decided rule not yet built.** A Decisions row whose rule a later increment or release builds says "
            "whether it applies from the decision and how it is held until built; the next report names every "
            "decided-but-unbuilt rule with how it is applied meanwhile. A release that adds a safety mechanism "
            "names, in its `Running projects must` items, how the loop holds it by hand until the release "
            "installs.") in flat(section(read(CORE), "Project state"))


def test_r053_p9_the_worked_scenario_lens_in_both_critics():
    """P9: a rule about money or stored data is read against one worked scenario before it reaches code review, a
    lens of the design critique (design.md) and of plan-critic."""
    assert ("**A worked scenario for money and stored data** is a lens of both critics: a rule about money or stored "
            "data is read against one worked scenario before it reaches code review (a retry after a lost reply, a "
            "dry run, a benchmark, an approved live smoke, two users on one account), each step naming the store it "
            "reads and writes; `plan-critic` carries the lens, and Review B's file copies it with the rest of its "
            "sections.") in flat(section(read(DESIGN), "The procedure"))
    assert ("- **A worked scenario for money and stored data.** Is every rule about money or stored data read "
            "against one worked scenario before it reaches code review: a retry after a lost reply, a dry run, a "
            "benchmark, an approved live smoke, two users on one account, each step naming the store it reads and "
            "writes? A rule no scenario was walked through is **Should fix**; a step that can charge twice or lose "
            "a result is **Blocking**.") in flat(section(read(PLAN_CRITIC), "When reviewing a design document"))


def test_r053_p20_the_all_omitted_index_and_the_minimum_sets_binding():
    """P20 (the conventions' section 8): a project whose design draws no architecture records it as an index with
    every kind omitted; the minimum set binds every project whose code has components; the calibration's retrofit
    reads the same rows."""
    assert ("**A project that draws no architecture** records it as a diagram index with every kind omitted, each "
            "with its reason in the Why column. The minimum set binds every project whose code has components (more "
            "than one module a builder edits); such a project omits a kind of it only with its reason recorded in the "
            "index's Why column and in its inventory's Decisions. The calibration's retrofit reads the same rows: a "
            "kind omitted with its recorded reason is covered, and one omitted without it is a retrofit item.") in \
        flat(section(read(CONVENTIONS), "8. As-built diagrams and the retrofit (release A3, plan 8.7)"))
