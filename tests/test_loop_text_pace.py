"""TASK-034: the loop's text for the code gate's review ceiling, the mutation run's place and the pace report.

enforces: docs/BUILD_PLAN.md TASK-034's Done when (the rounds: new numbered briefs, the fix brief inside a gate, step
7's "The review ceiling", step 8's SCOPE file before the snapshot and the round's names, the convergence rule's
certainty sentence and its bearing; the mutation run on every pass of step 7; the stage review's names and step 7's
arms; the gloss; rule 6 in the core and the digest, the policy, the three reviewers, the run parameters' owner's line,
KP-009 and KP-062; the pace report in /evaluate-reports); docs/REQUIREMENTS.md R-042, R-043 and R-044.
Supervisor-written; no builder run.

The ceiling's figure, the five blocking classes and the two lines' grammar are read from bridge_env.py, the one copy
the launcher and the review guard hold (TASK-032), and the refusal prefixes from the two programs, so the text and the
programs cannot drift apart unseen."""
import os
import re
import sys

import pytest

from phase_modules import flat, module, read, section

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CB = os.path.join(BRIDGE, "cursor-bridge")
sys.path.insert(0, CB)
import bridge_env  # noqa: E402

STEP3 = "3. Delegate to Cursor"
STEP3B = "3b. A model fails mid-step — switch automatically, restart the step, never wait"
STEP7 = "7. Decide (accept the increment)"
STEP8 = "8. Merge (the verified gate)"

# each blocking class as the texts spell it out, keyed by bridge_env's name for it
FIVE = {
    "behaviour": "behaviour against the brief or the register",
    "security": "security",
    "data integrity": "data integrity",
    "safety mechanism": "a defeated safety mechanism",
    "failing test": "a failing test",
}
NUMBER_WORDS = {3: "three"}


def text(*parts):
    return read(os.path.join(BRIDGE, *parts))


def f(s):
    return flat(s)


def core():
    return text("commands", "supervisor.md")


def digest():
    t = core()
    return t[t.index("<!-- digest:start -->"):t.index("<!-- digest:end -->")]


def rule(n):
    """Standing rule n of the core, flat."""
    t = core()
    body = t.split("\n## Standing rules\n", 1)[1]
    m = re.search(r"^%d\. (.*?)(?=^%d\. )" % (n, n + 1), body, re.S | re.M)
    return f(m.group(1))


def policy():
    return text("cursor-bridge", "Merge-Verification-Policy.md")


def policy_paragraph(start):
    t = policy()
    i = t.index(start)
    return f(t[i:t.index("\n\n", i)])


def loop():
    return module("delegation-loop")


def decide():
    return module("delegation-loop/decide.md")


def ceiling():
    return f(section(decide(), "The review ceiling", 4))


def brake():
    d = decide()
    i = d.index("**When to stop re-delegating")
    return f(d[i:d.index("**Split verdicts you resolve yourself")])


def reflection():
    return module("reflection")


def step8():
    return section(module("delegation-loop/merge.md"), STEP8, 3)


def convergence_in(t):
    i = t.index("**Convergence is a signal.**")
    return f(t[i:t.index("\n\n", i)])


def has_five(t):
    return [name for name, words in FIVE.items() if words not in t]


# --------------------------------------------------------------------------- the programs' copy


def test_r042_the_text_names_the_programs_constants():
    """The five the texts spell out are bridge_env's five, and the ceiling the texts state is its REVIEW_ROUNDS."""
    assert set(FIVE) == set(bridge_env.BLOCKING_CLASSES)
    assert bridge_env.REVIEW_ROUNDS in NUMBER_WORDS, bridge_env.REVIEW_ROUNDS
    word = NUMBER_WORDS[bridge_env.REVIEW_ROUNDS]
    assert ("The code gate's ceiling is %s rounds per increment and per stage review" % word) in rule(6)
    assert ("The code gate stops at %s rounds per increment" % word) in ceiling()
    assert ("**The ceiling** (R-042): %s rounds per increment and per stage review" % word) in f(policy())
    assert ("from round %s (program-held) only the five blocking classes send work back" % word) in digest()
    assert ("%s-round ceiling" % word) in f(text("agents", "diff-reviewer.md"))


def test_r042_the_class_line_the_text_gives_is_the_one_the_programs_read():
    """The `Blocking class:` line's grammar and its class names, as the review ceiling section writes them, are read
    by bridge_env's reader (the launcher's and the guard's), each class name among them."""
    c = ceiling()
    assert "**A class line**, `Blocking class: <class> - <the finding>`, its `<class>` one of `behaviour`, `security`, `data integrity`, `safety mechanism` and `failing test`" in c
    for cls in sorted(bridge_env.BLOCKING_CLASSES):
        assert ("`%s`" % cls) in c, cls
        line = "Blocking class: %s - Review A, round 3, B1" % cls
        assert bridge_env.read_blocking_class_line(line) == (cls, "Review A, round 3, B1", line), cls
    assert ("You write it into the brief before the builder launch, where the launcher reads it, and into "
            "`run/review/SCOPE-<ID>.md` before the snapshot, where the guard reads it; a line lifts the one round it "
            "was written for.") in c
    assert ("The reviewers are told of the line and confirm or deny it against the code of the round it lifted as "
            "that round's builder found it " + chr(0x2014) + " the commit that round's builder was launched on, its "
            "brief's commit (for a round of your own fix, with no builder run, the head the previous round's "
            "snapshot recorded), which you name beside the line in the brief and in the SCOPE file " + chr(0x2014)
            + " never against the "
            "fixed code under review: a reviewer's denial voids the round's result "
            "and withholds the merge as GATE-INTEGRITY does, and the breach is recorded in `docs/HARDENING.md` under "
            "the increment and as an issue.") in c


def test_r042_the_owners_line_the_text_gives_is_the_one_the_programs_read(tmp_path):
    """The owner's line, as decide.md and run-parameters.md write it, is read by bridge_env's reader; a line at or
    below the ceiling lifts nothing."""
    form = "`Review rounds above the ceiling: <ID> <rounds> (<their words>, <date>)`"
    assert form in ceiling()
    assert "written only on the owner's own words and never asked for" in ceiling()
    assert ("its `<rounds>` is at least the larger of the guard's and the launcher's next counts for the increment, "
            "the count your report names when the ceiling is reached") in ceiling()
    rp = f(module("run-parameters"))
    assert ("`Review rounds above the ceiling: <ID> <rounds> (<the owner's words>, <date>)` lets one increment's code "
            "review, or a stage's (`<ID>` then `STAGE-<name>`), run past the code gate's three-round ceiling up to "
            "`<rounds>`, at least the larger of the review guard's and the launcher's next counts for it") in rp
    assert "Four optional lines are never asked" in rp and "the fourth release B" in rp
    docs = tmp_path / "docs"
    docs.mkdir()
    rounds = bridge_env.REVIEW_ROUNDS + 1
    line = "Review rounds above the ceiling: TASK-099 %d (yes, one more, 2026-10-28)" % rounds
    (docs / "RUN_PARAMETERS.md").write_text(
        line + "\nReview rounds above the ceiling: TASK-098 %d (no, 2026-10-28)\n" % bridge_env.REVIEW_ROUNDS,
        encoding="utf-8")
    assert bridge_env.review_owner_lifts(str(tmp_path)) == {"TASK-099": (rounds, line)}


def test_r042_the_refusals_are_stops_named_as_the_programs_print_them():
    """The two refusal prefixes the text names are the ones the programs print, and step 3b and step 7 say that they
    are neither a failed launch nor a model's failure."""
    run = read(os.path.join(CB, "bridge-run.py"))
    guard = read(os.path.join(CB, "review-guard.py"))
    assert 'sys.stderr.write("bridge-run: refused - %s\\n" % reason)' in run and '"review ceiling: ' in run
    assert '"review-guard: refused - review ceiling: ' in guard
    assert '"brief rule: ' in run and '"review-guard: refused - branch rule: ' in guard
    assert '"revised in place: write handoff/' in run and '"branch rule: ' in run
    assert "brief rule: " not in guard and "revised in place: " not in guard
    assert "is off the count" in guard and "is reviewed: write" in guard
    c = ceiling()
    assert ("**The refusals are stops, not failures.** The launcher's `bridge-run: refused - review ceiling: ` and "
            "the guard's `review-guard: refused - review ceiling: `") in c
    assert ("and their other refusals of the ceiling's rules (the launcher's `brief rule: ` and `revised in place: `, "
            "the `branch rule: ` either prints, a brief revised after a completed run, a new round under a "
            "name whose round already has its reply or off the count, a brief or a snapshot under another ID on a "
            "counted branch), are the ceiling's programs holding: neither a failed launch nor a model's failure (step "
            "3b), never retried as one and never passed to `roster-check.py`.") in c
    s3b = f(section(loop(), STEP3B, 3))
    assert "(The exceptions: every exit 125 whose message begins `bridge-run: refused - design ceiling: `" in s3b
    assert ("Nor is a refusal of the code gate's programs a model's failure: the launcher's `review ceiling: `, "
            "`brief rule: `, `revised in place: ` and `branch rule: ` refusals (a fourth round with no lift, no brief "
            "or two, a builder launch on `main`, a brief revised after a completed run, a brief under another ID on a "
            "counted branch) and the guard's `review ceiling: ` and `branch rule: ` refusals and its refusals of a "
            "round off its count or already reviewed are the ceiling's programs holding, "
            "neither a failed launch nor a model's failure, handled as step 7's \"The review ceiling\" says; every "
            "other `bridge-run: refused - ` of a builder or review launch (the slot's `heavy.lock`, a limit, a key "
            "file) and every other `review-guard: refused - ` is no model's failure either, and is read and fixed as "
            "its message says.)") in s3b
    assert "branch rule: " in run


# --------------------------------------------------------------------------- the rounds


def test_r042_every_re_delegation_writes_a_new_numbered_brief():
    """Step 3 and step 7 (Iterate, Re-delegate) write a new numbered brief and never revise one in place; a merge
    unit's briefs carry its line; KP-009 says the same; no text still tells the supervisor to revise a brief in place."""
    s3 = f(section(loop(), STEP3, 3))
    assert ("**This applies to re-delegations too:** corrections go into a new numbered brief, `handoff/<ID>-r<N>.md` "
            "(`<N>` the round it opens, `-r2` after the first brief), committed, and never into a revision of a brief "
            "in place: the launcher refuses a brief whose bytes changed after a completed run under its name. A merge "
            "unit's briefs each carry the `Merge unit: <ID> <ID> ...` line the branch's first brief declares.") in s3
    s7 = f(section(decide(), STEP7, 3))
    assert ("- **Iterate** — something is wrong and you understand why. Write the next numbered brief, "
            "`handoff/<ID>-r<N>.md`, with specific corrections (never a revision in place, step 3), commit it, and "
            "re-issue the same constant delegate command, naming it.") in s7
    assert "Feed the reasons into the next numbered brief and re-delegate" in s7
    kp = f(text("cursor-bridge", "Known-Pitfalls.md"))
    assert ("Corrections and re-delegations go into the brief file (a new numbered brief, `handoff/<ID>-r<N>.md`, "
            "never a revision in place, which the launcher refuses after a completed run); never into the prompt.") in kp
    for root, _dirs, files in os.walk(BRIDGE):
        for name in files:
            if name.endswith(".md") and name != "CHANGELOG.md":
                t = f(read(os.path.join(root, name)))
                for old in ("revise `handoff/TASK-<nnn>.md` in place", "(in place, or as `TASK-<nnn>-r2.md`)",
                            "revised in place or `TASK-<nnn>-r2.md`"):
                    assert old not in t, (name, old)


def test_r042_the_fix_brief_inside_a_gate_is_the_next_numbered_brief():
    """The fix brief inside a gate is `<ID>-r<N>`, BUG-<nnn> after a merge, in every text that names it; the fix mode
    and the fix-diff check are keyed on the fix variant's content, the Objective's opening that spec-packager writes."""
    s7 = f(section(decide(), STEP7, 3))
    assert ("Inside an increment's gate the fix brief is the increment's next numbered brief, `handoff/<ID>-r<N>.md`, "
            "so that no fix within a gate opens a budget of its own; `handoff/BUG-<nnn>.md` is the brief of a defect "
            "found after a merge.") in s7
    sp = text("agents", "spec-packager.md")
    assert "## The fix variant — `handoff/<ID>-r<N>.md` inside a gate, `handoff/BUG-<nnn>.md` after a merge" in sp
    assert "Its content, not its name, makes it a fix brief" in f(sp)
    assert "(`handoff/<ID>-r<N>-report.md` inside a gate, `handoff/BUG-<nnn>-r<N>-report.md` after a merge)" in sp
    opening = "Fix the following confirmed defect"
    assert ('- **Objective** opens with: "%s' % opening) in sp
    dr = f(text("agents", "diff-reviewer.md"))
    assert ("**Fix mode.** If the brief is a fix brief — spec-packager's fix variant, whose Objective opens \"%s\" and "
            "whose confirmed cause is stated with its evidence, whatever its name (`handoff/<ID>-r<N>.md` inside an "
            "increment's gate, `handoff/BUG-<nnn>.md` after a merge) —" % opening) in dr
    assert ("**Fix-diff tampering** is a gate-integrity flag on the same footing. A fix brief — spec-packager's fix "
            "variant, known by its Objective, which opens \"%s\" and states the confirmed cause with its evidence, "
            "whatever its name: `handoff/<ID>-r<N>.md` inside an increment's gate, `handoff/BUG-<nnn>.md` for a "
            "defect found after a merge — names a confirmed root cause" % opening) in f(policy())
    skill = f(text("skills", "root-cause-first", "SKILL.md"))
    assert ("The builder receives the fix brief (spec-packager's fix variant) — inside an increment's gate the "
            "increment's next numbered brief, `handoff/<ID>-r<N>.md`, and `handoff/BUG-<nnn>.md` for a defect found "
            "after a merge:") in skill
    surv = f(section(loop(), "What must survive a compaction", 3))
    assert ("the fix brief, `handoff/<ID>-r<N>.md` inside an increment's gate or `handoff/BUG-<nnn>.md` for a defect "
            "found after a merge (step 7)") in surv


def test_r042_step_7_states_what_a_round_is_and_the_count_the_gate_reads():
    c = ceiling()
    assert ("**A round** is one version of the increment the gate's reviewers read: each builder run of a numbered "
            "brief (`handoff/<ID>.md`, then `handoff/<ID>-r<N>.md`, step 3), and each Review B read that "
            "`review-guard.py snapshot <ID>-r<N>` opens (step 8), spent when its reply arrived. A fix you make and "
            "Review A re-reads before step 8's snapshot is no round, and a failed launch's re-run re-snapshots the "
            "same tree under the same name.") in c
    assert ("**The count the gate reads** is the guard's count of rounds opened for the increment, which your report "
            "names; the launcher's count of builder rounds holds the briefs to it.") in c
    assert ("a Review A rejection spends a builder round with no snapshot, a fix of yours after a Review B REJECT a "
            "guard round with no builder run — so where a next count matters, take the larger of the guard's and the "
            "launcher's.") in c
    assert "the owner's number at the plan's gate (2026-10-24), held by two programs (R-042)" in c


def test_r042_above_the_ceiling_only_the_five_send_work_back():
    c = ceiling()
    assert "**Below the ceiling** the brake above is your judgment, and the by-class line yours to draw." in c
    assert ("**At and above it** — the guard's count of rounds opened for the increment at three or more — only a "
            "finding of one of the five blocking classes") in c
    assert ("sends the work back; every other finding goes to `docs/HARDENING.md` under the increment and merges with "
            "it. Every reviewer and auditor grades each finding by the five first, a convergent finding included "
            "(step 8).") in c
    assert has_five(c) == []
    assert "A stage review is bounded the same way (`STAGE-<name>-r<N>`, the reflection module's step 7)." in c


def test_r042_the_five_and_the_class_is_the_defect_in_all_three_homes():
    """Rule 6, the policy's re-delegation paragraph and step 7's brake each name the five and say that the class is
    the defect, not the operator that exposed it; the old four-item lists are gone from the two that had them."""
    homes = {
        "rule 6": rule(6),
        "policy": policy_paragraph("**Re-delegation runs while the code converges"),
        "brake": brake(),
    }
    for name, t in homes.items():
        assert has_five(t) == [], (name, has_five(t))
        assert "The class is the defect, not the operator that exposed it" in t, name
        assert "a further mutant, input or operator family that shows a class already recorded in `docs/HARDENING.md` under the by-class line for the increment or the stage is that class" in t, name
        assert "is that class and never a new one, while a defect of one of the five" in t, name
        assert "blocks whatever was recorded before" in t, name
    assert "output correctness, data integrity, security, or what the software does" not in homes["policy"]
    assert "**new class**" not in homes["policy"] and "**new class**" not in homes["brake"]
    assert "render/output correctness, data integrity, security, or what the software actually does" not in homes["brake"]
    assert ("Below the ceiling, drawing this line is a decision you make and record, not one you bring to the user; at "
            "and above it the line is the rule (\"The review ceiling\", below).") in homes["brake"]


def test_r042_rule_6_states_the_outcomes_and_the_programs():
    r = rule(6)
    assert r.startswith("Judge re-delegation by defect class, never by a round count alone.")
    assert "One of the five always blocks." in r
    assert ("held by two programs: the launcher (`bridge-run.py`) counts the builder rounds and the review guard "
            "(`review-guard.py`) the Review B rounds (Phase 6, step 7, \"The review ceiling\")") in r
    assert "the owner's number at the plan's gate" in r
    assert ("once the increment's core behaviour is verified, record the long tail of a hard subsystem under the "
            "by-class line and merge it; a late finding then blocks only if it is of the five, within the threat "
            "model `docs/INVENTORY.md` records for the part it is in (outside it a finding is recorded, not blocking; "
            "where none is recorded, the five stand unbounded), its class shown by reproduction on an ordinary, "
            "realistic layout, a label alone never deciding (a security finding by whether untrusted input can reach "
            "it), two reviewers naming the same defect making it certain, never blocking of itself (the convergence "
            "rule).") in r
    assert "or if two or more reviewers or auditors name it" not in r
    assert ("At and above it, every finding of an increment's review outside the five goes to `docs/HARDENING.md` "
            "with the increment, and a stage round's findings are disposed of as the reflection module's step 7 "
            "says.") in r
    assert "A round count is never itself a reason to involve the user." in r
    d = digest()
    assert ("6 Re-delegation ends by defect class, whatever operator showed it; from round three (program-held) only "
            "the five blocking classes send work back, the rest to HARDENING; stop only on non-convergence. A design "
            "critique stops after four rounds, a due confirming read and resolution round, whatever is open.") in d


def test_r042_the_digest_stays_within_its_cap_with_every_rule_number():
    """The digest within its cap, and every standing rule's number in its Standing rules paragraph (the loop's step
    numbers, 1 to 9, read apart: Review A, round 1, consider 2)."""
    d = digest()
    assert len(d) <= 9500, len(d)
    rules = d[d.index("**Standing rules.**"):d.index("**Permissions.**")]
    for n in range(1, 59):
        assert re.search(r"(?:\*\* | )%d [A-Z`]" % n, rules), n


def test_r042_the_convergence_rule_grades_certainty_never_class_in_both_homes():
    """R-042 as revised by release T (P1, T20): two reviewers naming the same defect make it certain, and blocking only
    where its content is of the five, at any round; a convergent finding of another class is fixed by the next
    increment that edits its file or recorded, with no gate pass of its own; a recorded class stays that class; a
    finding outside the recorded threat model is recorded, however many name it. The old sentence (two reviewers'
    agreement blocking whatever the grade below the ceiling) is gone from both homes."""
    homes = {"policy": convergence_in(policy()), "loop": convergence_in(step8())}
    for name, t in homes.items():
        assert "The rule grades a finding's certainty, never its class." in t, name
        assert "independently name the same defect," in t and "same line or the same defect" not in t, name
        assert "two findings on one line are one defect only where they name the same fault in it." in t, name
        assert ("Two reviewers independently naming the same defect make it blocking where its content is of one of "
                "the five blocking classes, at any round; a convergent finding of another class is fixed by the next "
                "increment that edits its file, or recorded in `docs/HARDENING.md`, marked convergent, with no gate "
                "pass of its own.") in t, name
        assert ("A class already recorded under the by-class line for that increment or that stage stays that class: "
                "two reviewers naming a further mutant, input or operator family of it name that class, which stays "
                "recorded and starts no round, and no class of the five is ever on that line.") in t, name
        assert ("A finding outside the threat model `docs/INVENTORY.md` (Decisions) records for the part it is in is "
                "recorded, not blocking, however many reviewers name it; where none is recorded for that part, the "
                "five stand unbounded.") in t, name
        assert "two reviewers' agreement makes a finding blocking whatever its grade" not in t, name


def test_r042_the_convergence_by_class_pointers_name_the_two_rules_apart():
    p = f(policy())
    assert "convergence-by-class" not in p
    assert "governed by the same two rules below, the re-delegation-by-class rule and the convergence rule, not a separate mechanism." in p
    assert "The same two rules below, the re-delegation-by-class rule and the convergence rule." in p
    da = f(text("agents", "design-auditor.md"))
    assert "convergence-by-class split" not in da
    assert ("Mirror the loop's re-delegation-by-class rule (the convergence rule, which grades a finding's certainty "
            "and never its class, is the supervisor's to apply):") in da


@pytest.mark.parametrize("agent,verdict,other", [("diff-reviewer.md", "a `REJECT`", "`NOTED`"),
                                                 ("security-auditor.md", "a FAIL", "advisory"),
                                                 ("design-auditor.md", "a FAIL", "advisory")])
def test_r042_each_reviewer_grades_by_the_five_first_above_the_ceiling(agent, verdict, other):
    t = f(text("agents", agent))
    i = t.index("**Above the ceiling.**")
    para = t[i:t.index("withholds the merge.", i) + len("withholds the merge.")]
    assert ("When the supervisor tells you the round is at or above the code gate's three-round ceiling (the review "
            "guard's "
            "count of rounds opened for the increment or the stage at three or more), grade each finding by the five "
            "blocking classes first") in para
    assert has_five(para) == []
    assert ("only those make %s, every other finding being %s" % (verdict, other)) in para
    assert ("When you are given a `Blocking class:` line, confirm or deny it: say whether the finding it names is a "
            "defect of the class it names. A denial is a breach of the ceiling, which voids the round's result and "
            "withholds the merge.") in para


def test_r042_step_8_commits_the_scope_file_before_the_round_named_snapshot():
    s = f(step8())
    first = s.index("**First** write `run/review/SCOPE-<ID>.md` (below) and commit it beside the diff: the guard reads it at the snapshot, its `Blocking class:` line included")
    then = s.index("**Then** `python ~/.claude/cursor-bridge/review-guard.py snapshot <ID>-r<N>`, `<ID>` the increment's ID")
    assert first < then
    assert ("`<N>` the round it opens: one more than the rounds the guard has counted for the increment, or the same "
            "`<N>` again to re-run a failed launch on the same tree; the round's diff") in s
    assert ("so confirm yourself that it is not empty. It refuses a tree that is not clean (commit everything of yours "
            "first), a round off its count and a round above the ceiling with no lift") in s
    assert "\"<directive prompt>\" 2> run/review/REVIEW-<ID>-r<N>.err`" in s
    assert "**Afterwards** `python ~/.claude/cursor-bridge/review-guard.py verify <ID>-r<N>` must print `OK`" in s
    assert ("and, at a round above the ceiling, that round's `Blocking class:` line with, beside it, the commit "
            "that round's builder was launched on, its brief's commit (for a round of your own fix, with no builder "
            "run, the head the previous round's snapshot recorded).") in s
    assert ("(at a round at or above the ceiling, the guard's count at three or more, a sixth clause: grade every "
            "finding by the five blocking classes first, and confirm or deny the SCOPE file's `Blocking class:` line "
            "where it has one, against the code of the round it lifted, never against the fixed code under review)") in s
    assert ("`git diff <merge-base>...HEAD > run/review/REVIEW-<ID>-r<N>.diff`, named as the round's snapshot below "
            "is, the earlier round's diff and assumptions file removed with `git rm` and committed first, so that no "
            "round's diff carries another's;") in s
    assert "write `run/review/ASSUMPTIONS-<ID>-r<N>.md` from the `Assumptions:` sections" in s
    assert ("the round's diff and assumptions file carry the snapshot's name, since the guard lists as the review's "
            "inputs, and refuses empty, the files under `run/review/` whose names hold it (KP-067); the SCOPE file, "
            "which it reads by `<ID>`, is not among them, so confirm yourself that it is not empty.") in s
    assert ("stopping only on non-convergence per step 7's brake, and at and above the ceiling only for a finding of "
            "one of the five blocking classes.") in f(step8())
    assert "`python ~/.claude/cursor-bridge/review-guard.py premerge <ID>-r<N> <n>`, the name the round's snapshot took" in f(step8())
    surv = f(section(loop(), "What must survive a compaction", 3))
    assert ("(the round's `REVIEW-<ID>-r<N>.diff`, `ASSUMPTIONS-<ID>-r<N>.md` and `REVIEW-<ID>-r<N>.err`, whose first "
            "line is the launch time `pr-activity-check.py` needs, and the increment's `SCOPE-<ID>.md`), whole, with "
            "the review guard's count of rounds opened for the increment, which names the next snapshot `<ID>-r<N>` "
            "(step 8)") in surv


def test_r042_no_governing_text_names_a_review_round_the_old_way():
    """The snapshot, verify, premerge, .err, diff and assumptions names carry the round everywhere the loop is
    governed (the change log and KP-032's narrative apart; Review A, round 1, consider 3)."""
    old = ("review-guard.py snapshot <nnn>", "review-guard.py verify <nnn>", "review-guard.py premerge <nnn>",
           "REVIEW-<nnn>.err", "snapshot STAGE-<name>`", "verify STAGE-<name>`", "REVIEW-STAGE-<name>.err",
           "`snapshot <nnn>`", "`verify <nnn>`", "`premerge <nnn>`", "snapshot <nnn>", "verify <nnn>",
           "premerge <nnn>", "REVIEW-<nnn>.diff", "ASSUMPTIONS-<nnn>", "SCOPE-<nnn>", "STAGE-<name>.diff",
           "STAGE-<name>-<part>")
    for root, _dirs, files in os.walk(BRIDGE):
        for name in files:
            if name.endswith(".md") and name != "CHANGELOG.md":
                t = read(os.path.join(root, name))
                if name == "Known-Pitfalls.md":  # KP-032's narrative keeps the names of its release
                    i = t.index("### KP-032")
                    t = t[:i] + t[t.index("\n### ", i + 1):]
                for o in old:
                    assert o not in t, (name, o)


def test_r042_the_policy_carries_the_ceiling_the_names_and_the_breach():
    p = f(policy())
    para = policy_paragraph("**Re-delegation runs while the code converges")
    assert ("held by `bridge-run.py`, which counts the builder rounds, and `review-guard.py`, which counts the Review "
            "B rounds; the count is the guard's") in para
    assert ("Below it the by-class line is the supervisor's judgment; at and above it the line is the rule: only a "
            "finding of the five sends the work back, every other finding goes to `docs/HARDENING.md` with the "
            "increment, and a round above the ceiling runs only under a `Blocking class:` line or the owner's `Review "
            "rounds above the ceiling:` line.") in para
    assert ("Every reviewer and auditor grades each finding of a round at or above the ceiling by the five first and "
            "confirms or denies the round's `Blocking class:` line where it has one, against the code of the round it "
            "lifted, never against the fixed code under review; a denial is a breach, which voids the round's result and withholds "
            "the merge as GATE-INTEGRITY does, recorded in `docs/HARDENING.md` and as an issue.") in para
    assert "\"<prompt>\" 2> run/review/REVIEW-<ID>-r<N>.err`" in p
    assert "names `run/review/SCOPE-<ID>.md`, committed beside the diff before the snapshot," in p
    assert ("that at a round at or above the ceiling every finding is graded by the five blocking classes first and "
            "the SCOPE file's `Blocking class:` line, where it has one, confirmed or denied against the code of the "
            "round it lifted, never against the fixed code under review,") in p
    assert "(`run/review/REVIEW-<ID>-r<N>.diff`, named as the round's snapshot," in p
    assert "It also reads `run/review/ASSUMPTIONS-<ID>-r<N>.md`" in p
    assert "the count is the guard's (`~/.claude/cursor-bridge/workflow/phases/delegation-loop/decide.md`, step 7, \"The review ceiling\")" in p
    assert ("`snapshot <ID>-r<N>` before the launch, `<N>` the round it opens by the guard's count, the SCOPE file "
            "committed first since the guard reads its `Blocking class:` line (it refuses a dirty tree, a round off "
            "its count and a round above the ceiling with no lift,") in p
    assert "`verify <ID>-r<N>` after the run, and `premerge <ID>-r<N>` before `gh pr merge`" in p


def test_r042_kp_062_names_its_twin():
    kp = f(text("cursor-bridge", "Known-Pitfalls.md"))
    i = kp.index("### KP-062")
    assert ("Its twin is the code gate's ceiling (release B, R-042): three rounds per increment and per stage review, "
            "held by `bridge-run.py` and `review-guard.py`, past which only the five blocking classes send work back "
            "(the delegation loop's step 7, \"The review ceiling\").") in kp[i:]


def test_r042_the_run_parameters_gloss_reads_nothing_installs():
    rp = module("run-parameters")
    assert "Installer verification: local | ci-only | n/a (nothing installs)" in rp
    assert "not a desktop application" not in rp


def test_r042_the_rounds_input_names_are_the_ones_the_guard_checks(tmp_path):
    """The review inputs the text names for a round, an increment's and a stage's, are listed by the guard's own
    review_inputs for that round's snapshot name, so its refusal of an empty input (KP-067) covers them; the SCOPE file,
    read by the ID, is not, which the text says (Review A, round 1, Blocking 2)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("review_guard_t034", os.path.join(CB, "review-guard.py"))
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    folder = tmp_path / "run" / "review"
    folder.mkdir(parents=True)
    names = {"TASK-099-r2": ["ASSUMPTIONS-TASK-099-r2.md", "REVIEW-TASK-099-r2.diff"],
             "STAGE-B9-r1": ["STAGE-B9-r1-tests.diff", "STAGE-B9-r1.diff"]}
    for files in names.values():
        for name in files:
            (folder / name).write_text("x", encoding="utf-8")
    for unseen in ("SCOPE-TASK-099.md", "SCOPE-STAGE-B9.md", "REVIEW-TASK-099-r2.err", "REVIEW-STAGE-B9-r1.err"):
        (folder / unseen).write_text("x", encoding="utf-8")
    for snap, files in names.items():
        listed = [n for n, _size in guard.review_inputs(str(tmp_path), snap)]
        assert listed == sorted(files), (snap, listed)
    s8 = f(step8())
    for form in ("REVIEW-<ID>-r<N>.diff", "ASSUMPTIONS-<ID>-r<N>.md"):
        assert form.replace("<ID>-r<N>", "TASK-099-r2") in names["TASK-099-r2"] and form in s8, form
    r = f(section(reflection(), "The procedure", 3))
    for form in ("STAGE-<name>-r<N>.diff", "STAGE-<name>-r<N>-<part>.diff"):
        assert form.replace("<name>-r<N>", "B9-r1").replace("<part>", "tests") in names["STAGE-B9-r1"] and form in r, form


# --------------------------------------------------------------------------- the stage review


def test_r042_the_stage_review_takes_the_rounds_names_and_its_scope_file():
    r = f(section(reflection(), "The procedure", 3))
    assert ("write `run/review/SCOPE-STAGE-<name>.md`, the stage's increments and briefs, the earlier rounds' "
            "dispositions and, at a round above the ceiling, its `Blocking class:` line (step 7); then `git add -f` "
            "both and commit them on the stage branch.") in r
    assert ("3. `python ~/.claude/cursor-bridge/review-guard.py snapshot STAGE-<name>-r<N>`, `<N>` the round it opens: "
            "one more than the rounds the guard has counted for the stage; the round's diff and its parts carry the "
            "snapshot's name, since the guard lists as the review's inputs, and refuses empty, the files under "
            "`run/review/` whose names hold it (KP-067); the SCOPE file, which it reads by the stage's name, is not "
            "among them, so confirm yourself that it is not empty.") in r
    assert "origin/main > run/review/STAGE-<name>-r<N>.diff`, `<N>` the round step 3 opens;" in r
    assert "4. Review A: `diff-reviewer` on `run/review/STAGE-<name>-r<N>.diff`," in r
    assert "origin/main -- <paths> > run/review/STAGE-<name>-r<N>-<part>.diff`" in r
    assert "naming run/review/STAGE-<name>-r<N>.diff and the stage>" in r
    assert "2> run/review/REVIEW-STAGE-<name>-r<N>.err`; you write nothing to the checkout meanwhile but `run/supervisor/in-flight.md` (rule 43), where the position and each verdict go." in r
    assert "6. `python ~/.claude/cursor-bridge/review-guard.py verify STAGE-<name>-r<N>` must print `OK`" in r
    surv = f(section(reflection(), "What must survive a compaction", 3))
    assert ("(the round's `STAGE-<name>-r<N>.diff` with its parts and `REVIEW-STAGE-<name>-r<N>.err`, and "
            "`SCOPE-STAGE-<name>.md`), the review guard's count of rounds opened for the stage (step 7)") in surv


def test_r042_the_stage_reviews_step_7_and_its_arms():
    r = f(section(reflection(), "The procedure", 3))
    assert ("7. Decide the round, the ceiling read against the guard's count of rounds opened for the stage (with "
            "three opened, the next round is above it). Every arm that starts a fix does step 8 first (back on "
            "`main`, the stage branch deleted), and an arm that opens a new stage round runs it from step 1, on the "
            "new whole change, only after that fix has merged.") in r
    assert ("- **Below the ceiling.** (a) A REJECT from either reviewer starts a fix brief and a new stage round; the "
            "round's findings the convergence rule makes blocking") in r
    assert "ride in its fix brief, and a class already recorded under the by-class line for the stage stays recorded." in r
    assert ("(b) A round ending with no REJECT but with findings the convergence rule makes blocking, the same "
            "exception included, puts those findings, with the round's other findings you take, into one fix "
            "increment through its own gate; the stage closes at its merge with no further stage round, and the rest "
            "are recorded at the close.") in r
    i = r.index("- **At and above the ceiling.**")
    above = r[i:r.index("- **The fix brief**", i)]
    assert has_five(above) == []
    assert ("Only a blocking-class finding starts a fix brief and a new stage round, its `Blocking class:` line "
            "written into `run/review/SCOPE-STAGE-<name>.md` at that round's step 2, before its snapshot") in above
    assert ("A convergent finding outside the five goes to `docs/HARDENING.md` under the stage, marked convergent, and "
            "opens no fix increment") in above
    assert "every other finding is recorded at the close and never becomes a fix increment." in above
    assert ("- **The fix brief** of either arm is a `BUG-<nnn>`, the stage's increments having merged; arm (b)'s is an "
            "increment with a budget of its own under the programs' branch rule.") in r
    assert "the plain brief KP-015's proportionality allows only where every finding is its own cause." in r
    assert "- **No finding sends work back:** the stage review is done, its findings recorded at the close." in r


# --------------------------------------------------------------------------- the mutation run (R-043)


def test_r043_the_mutation_run_comes_on_every_pass_once_accepted_before_the_snapshot():
    m = f(section(decide(), "The mutation run", 4))
    assert ("The mutation run is launched here, on every pass through this step: once Review A and the auditors have "
            "accepted the increment's behaviour, and before step 8's snapshot; never at every round's step 4") in m
    assert "The new tests' run against the checkpoint (`--checkpoint`) stays at step 4, before any reviewer." in m
    assert ("Take the larger of the two next counts: the review guard's rounds opened for the increment plus one, and "
            "the launcher's round of the brief that would carry a code fix. Where it is at or below the code gate's "
            "ceiling of three rounds, the mutant is fixed: a criterion test's fix is yours and no round; a code fix "
            "is a re-delegation (above) and a round.") in m
    assert ("Above the ceiling, the mutant goes to `docs/HARDENING.md` under the increment and never to a "
            "re-delegation, unless the code it shows untested is a safety mechanism the increment relies on, or the "
            "result shows a defect of a blocking class") in m


# --------------------------------------------------------------------------- the pace report (R-044)


def test_r044_evaluate_reports_runs_the_pace_report_every_week():
    er = text("commands", "evaluate-reports.md")
    fr = f(er)
    assert "Then, on every run, a week with nothing new included:" in fr
    assert "   ```bash\n   python ~/.claude/cursor-bridge/pace-report.py --tokens > Reports/Evaluations/<date>/pace.md\n   ```" in er
    assert '"--tokens"' in read(os.path.join(CB, "pace-report.py"))
    assert ("\"Nothing new\" leaves steps 2 and 3 only the entries the owner's messages raise (the extract below), "
            "and the evaluation file only those and its Pace section (the ledger keeps the run's date); the pace "
            "report below runs all the same.") in fr
    assert "ends the run in one line" not in fr and "ends in one line" not in fr
    assert ("then a **Pace** section that reads `pace.md`: per project the week's rows against the weeks before, a "
            "creeping slowdown named the week it starts. An increment over the ceiling whose round used no lift "
            "(`none`), or whose class line a reviewer denied (its Issues entry), is an entry of the evaluation like "
            "any other; an `unknown` lift is a round no record covers, an entry only when the round was run after "
            "release B installed. In a week with nothing new the file is written all the same, holding the Pace section and any "
            "entry the owner's messages raised.") in fr
    assert "A Sunday with nothing new writes the Pace section and any entry the owner's messages raised." in fr


def test_bug031_a_late_finding_has_one_outcome_in_all_three_homes():
    """BUG-031 (stage B5's review, round 1; core S4 and tests-text S1, convergent): below the ceiling, once the
    by-class line is drawn, rule 6 sent "a late finding outside the five back when it is not that tail" while step
    7's brake said a late finding "blocks the merge only if it is of one of the five"; the three-homes test above
    checked only the class sentence and passed on the two outcomes. Each home now gives the one outcome: a late
    finding blocks only if it is of the five (or, below the ceiling, if two reviewers name it: the test after this).
    enforces: R-042 (the by-class line; only the five send work back); rule 6; step 7's brake; the policy's
    re-delegation paragraph"""
    r = rule(6)
    assert "a late finding then blocks only if it is of the five," in r
    assert "send a late finding outside the five back" not in r
    assert "A late finding blocks the merge only if it is of one of the five **blocking classes**" in brake()
    p = policy_paragraph("**Re-delegation runs while the code converges")
    assert "A late finding blocks the merge only if it is of one of the five **blocking classes**" in p
    for home in (r, brake(), p):
        assert "outside the five back" not in home and "when it is not that tail" not in home


def test_bug033_a_late_finding_two_reviewers_name_blocks_only_of_the_five_in_every_home():
    """BUG-033 (stage B5's review, round 2; core S1 and modules C2, convergent) found the late-finding sentence and the
    convergence rule giving a convergent late finding outside the five two outcomes, and made each home name the
    convergence rule's exception. R-042 as revised by release T (P1, TASK-039) gives it one outcome the other way: two
    reviewers naming a late finding make it certain, never blocking of itself, and it blocks only where its content is
    of the five, at any round, in all three homes of the late-finding sentence and both convergence paragraphs.
    enforces: R-042 (the by-class line; the convergence rule, as revised); rule 6; step 7's brake; the policy's
    re-delegation and convergence paragraphs; step 8's convergence paragraph"""
    r = rule(6)
    assert "a late finding then blocks only if it is of the five, within the threat model" in r
    assert "two reviewers naming the same defect making it certain, never blocking of itself (the convergence rule)." in r
    assert "or if two or more reviewers or auditors name it" not in r
    for name, home in (("brake", brake()), ("policy", policy_paragraph("**Re-delegation runs while the code converges"))):
        assert ("Two reviewers naming the same late finding make it certain, never blocking of itself: it blocks only "
                "where its content is of the five") in home, name
        assert "a late finding two or more reviewers or auditors name blocks too" not in home, name
    for name, home in (("policy", convergence_in(policy())), ("loop", convergence_in(step8()))):
        assert ("Two reviewers independently naming the same defect make it blocking where its content is of one of "
                "the five blocking classes, at any round;") in home, name
        assert "two reviewers' agreement makes a finding blocking whatever its grade" not in home, name


def test_bug031_evaluate_reports_says_what_the_pace_report_counts():
    """BUG-031 (stage B5's review, round 1; core C4 and Review B C, convergent; programs S3, Review B S2 and
    tests-mutation-pace S3 on what the report lists): pace-report.py prints a round's lift as `class`, `owner`,
    `none` or `unknown` (no record of it), counts as increments only the IDs with a tracked brief where anything is
    tracked under handoff/ (every ID a squash subject names where nothing is), and lists a stage
    review only from the guard's rounds files; /evaluate-reports named three lifts and neither limit.
    enforces: R-044 (the pace section computed from git and the launcher's and the guard's records, "for every
    brief's ID"); bridge/cursor-bridge/pace-report.py (`_lift_map`, the over-the-ceiling list)"""
    t = flat(read(os.path.join(HERE, os.pardir, "bridge", "commands", "evaluate-reports.md")))
    assert "(a class line, the owner's line, `none`, or `unknown` where no launcher row or guard round records it" in t
    assert "In a project that tracks any file under `handoff/`, an increment is an ID with a tracked brief" in t
    # BUG-033 (stage B5's review, round 2; BUG-031's Review B, round 3, note): any tracked file under handoff/
    # switches the count to tracked briefs (`_handoff_untracked`), and a report is no brief (`_ids_with_brief`)
    assert ("a project that tracks only builder reports there (`<ID>-report.md`, `<ID>-r<N>-report.md`, "
            "`<ID>-r<N><letter>-report.md`, which are no briefs) counts no increment at all") in t
    assert ("(in a project that tracks nothing under `handoff/`, every ID a squash subject names is counted merged, and the "
            "started and rounds cells read `n/a`)") in t
    assert "a stage review is listed only from the review guard's rounds files" in t
    prog = read(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "pace-report.py"))
    assert 'lifts.get(r, "unknown")' in prog and 'lifts.setdefault(rnd, "none")' in prog


def test_bug033_a_project_tracking_only_reports_under_handoff_counts_no_increment(program):
    """BUG-033 (stage B5's review, round 2; BUG-031's Review B, round 3, note): what evaluate-reports.md now says of a
    project that tracks only builder reports under handoff/ is what pace-report.py does: any tracked file there
    switches the count to tracked briefs, and a report is no brief, so no ID is counted; a tracked brief is (the
    precondition).
    enforces: bridge/commands/evaluate-reports.md, step 1 (the pace section's increments); R-044"""
    pr = program("pace-report")
    reports = "handoff/BUG-029-report.md\nhandoff/TASK-031-r2-report.md\nhandoff/TASK-031-r2a-report.md\n"
    assert pr._handoff_untracked(reports) is False
    assert pr._ids_with_brief(reports) == set()
    assert pr._ids_with_brief(reports + "handoff/TASK-031.md\n") == {"TASK-031"}
    assert pr._handoff_untracked("") is True


def test_bug031_the_refactoring_pass_title_names_its_briefs():
    """BUG-031 (stage B5's review, round 1; tests-mutation-pace S3): PR #99's title `REFAC-B5: ...` named the stage, so
    the squash subject merged no brief and REFAC-003 reads as never merged; step 6 of the pass now asks the title to
    start with every `REFAC-<nnn>` brief ID, as step 8 asks of every title.
    enforces: R-044 (merged increments read from the squash subjects); step 8 ("PR titles start with every increment
    ID the branch carries")"""
    t = flat(module("delegation-loop/refactoring-pass.md"))
    assert ("Merge as one squash, the pull request's title starting with every `REFAC-<nnn>` brief ID the branch "
            "carries (`REFAC-003 REFAC-004: ...`)") in t
    assert "merges none of the branch's briefs" in t
    assert "the squash subject is how the pace report knows a brief merged (the plan check reads only the plan's increments)" in t
