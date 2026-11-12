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

from phase_modules import digest, flat, module, read, rule, section

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


def policy():
    return text("cursor-bridge", "Merge-Verification-Policy.md")


def loop():
    return module("delegation-loop")


def decide():
    return module("delegation-loop/decide.md")


def ceiling():
    return f(section(decide(), "The review ceiling", 4))


def reflection():
    return module("reflection")


def step8():
    return section(module("delegation-loop/merge.md"), STEP8, 3)


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
            "snapshot recorded), which you name beside the line at step 4 and in the SCOPE file, the brief carrying the line alone " + chr(0x2014)
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


def test_r042_the_digest_stays_within_its_cap_with_every_rule_number():
    """The digest within its cap, and every standing rule's number in its Standing rules paragraph (the loop's step
    numbers, 1 to 9, read apart: Review A, round 1, consider 2)."""
    d = digest()
    assert len(d) <= 9500, len(d)
    rules = d[d.index("**Standing rules.**"):d.index("**Permissions.**")]
    for n in range(1, 59):
        assert re.search(r"(?:\*\* | )%d [A-Z`]" % n, rules), n


def test_r042_the_convergence_by_class_pointers_name_the_two_rules_apart():
    p = f(policy())
    assert "convergence-by-class" not in p
    assert "governed by the same two rules below, the re-delegation-by-class rule and the convergence rule, not a separate mechanism." in p
    assert "The same two rules below, the re-delegation-by-class rule and the convergence rule." in p
    da = f(text("agents", "design-auditor.md"))
    assert "convergence-by-class split" not in da
    assert ("Mirror the loop's re-delegation-by-class rule (the convergence rule, which grades a finding's certainty "
            "and never its class, is the supervisor's to apply):") in da


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
    # the three sentences re-taken at TASK-041, which adds the Dependency scan section beside the Pace section (R-052)
    assert ("\"Nothing new\" leaves steps 2 and 3 only the entries the owner's messages raise (the extract below), "
            "and the evaluation file only those and its Pace and Dependency scan sections (the ledger keeps the run's "
            "date); the pace report below runs all the same.") in fr
    assert "ends the run in one line" not in fr and "ends in one line" not in fr
    assert ("then a **Pace** section that reads `pace.md`: per project the week's rows against the weeks before, a "
            "creeping slowdown named the week it starts; then the **Dependency scan** section step 1b gives. An "
            "increment over the ceiling whose round used no lift "
            "(`none`), or whose class line a reviewer denied (its Issues entry), is an entry of the evaluation like "
            "any other; an `unknown` lift is a round no record covers, an entry only when the round was run after "
            "release B installed. In a week with nothing new the file is written all the same, holding the Pace and "
            "Dependency scan sections and any entry the owner's messages raised.") in fr
    assert ("A Sunday with nothing new writes the Pace and Dependency scan sections and any entry the owner's messages "
            "raised.") in fr


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
