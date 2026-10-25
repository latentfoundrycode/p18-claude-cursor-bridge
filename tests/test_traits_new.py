"""TASK-018: the trait files spends money, long-running process and AI models (R-020, R-021, R-022), new text
throughout.

enforces: docs/BUILD_PLAN.md TASK-018 (its Done when: each file one `#` title and `## Add at <point key>` sections and
nothing else, each section under a `new` entry naming the file and the heading, the points each adds at and no other,
what each names, N1/§8.1 left in the core, the pointer at external services' bounded wait, the three rows written,
the workflow check passing); docs/INVENTORY.md, Decisions, the row on the deployed-layout and bounded-remote-wait
checks (spends money's pointer and its classification sentence). Supervisor-written; no builder run."""
import os
import re
import subprocess
import sys

import pytest

from phase_modules import BRIDGE, read, section
from workflow_files import (CORE, OPEN_LIST, PHASES, TRAIT_PREFIX, TRAITS, WORKFLOW, WORKFLOW_CHECK, file_entries, flat,
                            trace_units)

# The points each file adds at, in its order (BUILD_PLAN TASK-018).
POINTS = {
    "spends-money": ["intake.questions", "configuration.items", "delegation-loop.brief-constraints",
                     "delegation-loop.inspect-checks", "delegation-loop.test-checks"],
    "long-running-process": ["configuration.items", "delegation-loop.brief-constraints", "delegation-loop.test-checks"],
    "ai-models": ["intake.questions", "design.sections", "configuration.items", "delegation-loop.test-checks"],
}
TITLES = {"spends-money": "Spends money", "long-running-process": "Long-running process", "ai-models": "AI models"}


def trait(key):
    return read(os.path.join(TRAITS, key + ".md"))


def add(key, point):
    return flat(section(trait(key), "Add at " + point, 2))


@pytest.mark.parametrize("key", sorted(POINTS))
def test_r020_r022_each_file_is_a_title_and_add_at_sections_only(key):
    """BUILD_PLAN TASK-018: one `#` title, then the `## Add at <point key>` sections named above, in that order, and
    nothing else: no other heading of any level, so each file adds only and at no other point."""
    lines = trait(key).split("\n")
    heads = [l for l in lines if re.match(r"^ {0,3}#", l)]
    assert heads == ["# " + TITLES[key]] + ["## Add at " + p for p in POINTS[key]], heads
    assert lines[0] == "# " + TITLES[key], lines[0]
    for p in POINTS[key]:
        assert add(key, p), (key, p)


@pytest.mark.parametrize("key", sorted(POINTS))
def test_r020_r022_every_section_has_its_own_new_entry_and_no_other_entry_names_the_file(key):
    """BUILD_PLAN TASK-018: each `## Add at` section is new text under a `new` entry naming the file and that heading
    (the trace check counts a trait file as a module); no `reword` entry, and no entry on the file's title, which would
    excuse the file whole."""
    rel = TRAIT_PREFIX + key + ".md"
    got = file_entries(rel)
    by = {("spends-money", "delegation-loop.test-checks"): "BUG-027"}  # stage B4's review, round 7
    assert got == [("new", by.get((key, p), "TASK-018"), "Add at " + p) for p in POINTS[key]], got


@pytest.mark.parametrize("key", sorted(POINTS))
def test_r020_r022_the_text_is_new_and_copies_no_passage_of_the_main_workflow(key):
    """BUILD_PLAN TASK-018: the files are new text throughout; no unit of one, as trace-check.py reads units, is a unit
    of the core, of a phase module, of the plan critic or of another trait file (a copy would be a passage in two homes,
    and an excused section switches the trace check's copy check off; Review A, round 1)."""
    main = set(trace_units(read(CORE))) | set(trace_units(read(os.path.join(BRIDGE, "agents", "plan-critic.md"))))
    for root, _dirs, names in os.walk(PHASES):
        for f in names:
            if f.endswith(".md"):
                main |= set(trace_units(read(os.path.join(root, f))))
    others = [f for f in os.listdir(TRAITS) if f.endswith(".md") and f != key + ".md"]
    assert len(others) >= 6, others
    for f in others:
        main |= set(trace_units(read(os.path.join(TRAITS, f))))
    assert len(main) > 300, len(main)
    for unit in trace_units(trait(key)):
        assert unit not in main, unit[:80]


def test_r020_r022_the_three_rows_are_written_in_the_open_list():
    """BUILD_PLAN TASK-018: the three rows flip to written in the same change as their files."""
    text = read(OPEN_LIST)
    for key in POINTS:
        rows = [l for l in text.split("\n") if l.startswith("| %s |" % key)]
        assert len(rows) == 1 and rows[0].rstrip().endswith("| yes | release B |"), rows


def test_r020_r022_workflow_check_passes_over_the_workflow_folder():
    """BUILD_PLAN TASK-018: `workflow-check.py` passes over `workflow/` with the three files written."""
    r = subprocess.run([sys.executable, WORKFLOW_CHECK, WORKFLOW], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "RESULT: OK" in r.stdout, r.stdout


def test_r020_spends_money_asks_for_approval_the_worst_case_the_cap_and_the_account():
    """R-020 (DESIGN §6.8): at intake, the approval before any paid action, the estimate against the worst case, the
    cap, and the platform and account named."""
    t = add("spends-money", "intake.questions")
    assert "**platform and account**" in t and "**worst case**" in t and "the **cap** the owner sets" in t
    assert "No paid action of the loop runs without the owner's approval first" in t
    assert "with its estimate against the worst case and the platform and account named in the same sentence" in t
    assert "an approval covers the action it names, never the next one" in t
    assert ("and the escalation the trait *external services* asks once per service (its addition at "
            "`planning.stages`) settles the service's key and account only: where a part has both traits, the contract "
            "capture's live call that escalation names is, when it costs money, a paid action of the loop "
            "like any other, approved for itself as this trait asks, and so is every later capture or "
            "re-recording of that service.") in t, "BUG-021: one escalation never approves a paid call"
    assert "never a silent overrun" in t
    # Review A, round 1: which paid actions the approval covers, and who enforces the cap.
    assert "The loop's own paid actions (a contract capture, a paid run of an increment, a re-recording" in t
    assert "tracked against the cap by the supervisor" in t
    assert "the design states how the product enforces the cap" in t and "fixed in a test (rule 52)" in t
    # Review A, round 2, and BUG-022: the trait adds no design section, so the intake notes carry its three duties.
    assert "the intake notes carry its three duties to the design as requirements of it" in t
    assert ("and how a speed budget that includes a paid service's time is measured (its addition at "
            "`delegation-loop.brief-constraints`).") in t
    assert "the folder that holds the store of paid results" in t
    # the section held whole (stage B4's review, round 7).
    assert t == (
        "For a part whose actions cost real money (a paid API, a purchase, a metered model or service), ask "
        "before design, and write each answer to the intake notes: which actions cost money, on which "
        "**platform and account** each is charged; the **worst case** of each, the most one run of it can "
        "cost when it goes wrong as well as when it goes right (every retry, every item of the largest input, "
        "a run that does not stop), estimated in that platform's own units and in money; and the **cap** the "
        "owner sets, the most the project may spend in all, per month or per run as the owner names it, with "
        "what happens at the cap (the action stops and the owner is asked; never a silent overrun). The "
        "loop's own paid actions (a contract capture, a paid run of an increment, a re-recording, a benchmark "
        "against a paid service) are tracked against the cap by the supervisor; where the product itself "
        "spends in the owner's use, the design states how the product enforces the cap, and the cap is a "
        "value the owner chose, fixed in a test (rule 52). This trait adds no design section, so the intake "
        "notes carry its three duties to the design as requirements of it: how the product enforces the cap, "
        "where it spends in the owner's use; the folder that holds the store of paid results (its addition at "
        "`configuration.items`); and how a speed budget that includes a paid service's time is measured (its "
        "addition at `delegation-loop.brief-constraints`). No paid action of the loop runs without the "
        "owner's approval first, given in words for that action, with its estimate against the worst case and "
        "the platform and account named in the same sentence; an approval covers the action it names, never "
        "the next one, and the escalation the trait *external services* asks once per service (its addition "
        "at `planning.stages`) settles the service's key and account only: where a part has both traits, the "
        "contract capture's live call that escalation names is, when it costs money, a paid action of the "
        "loop like any other, approved for itself as this trait asks, and so is every later capture or "
        "re-recording of that service. A paid call is a remote call, whose wait the trait *external services* "
        "bounds (its addition at `delegation-loop.inspect-checks`), so a part that pays a remote service is "
        "classified with *external services* too, which the design gate's trait decision checks."), t


def test_r020_r019_a_paid_call_is_bounded_by_external_services_and_classified_with_it():
    """BUILD_PLAN TASK-018; INVENTORY, Decisions (the bounded remote wait is external services' addition): one sentence
    that a paid call is a remote call whose wait external services' addition bounds, naming that addition, and that a
    part paying a remote service is classified with external services too, which the design gate checks; the addition
    it names exists and holds the bounded wait, and spends money holds no bound of its own."""
    t = add("spends-money", "intake.questions")
    assert ("A paid call is a remote call, whose wait the trait *external services* bounds (its addition at "
            "`delegation-loop.inspect-checks`), so a part that pays a remote service is classified with *external "
            "services* too, which the design gate's trait decision checks.") in t
    target = flat(section(trait("external-services"), "Add at delegation-loop.inspect-checks", 2))
    assert target.startswith("Every wait on a remote service in the diff is bounded")
    assert "timeout" not in flat(trait("spends-money"))


def test_r020_spends_money_keeps_paid_results_records_the_cap_and_runs_dry_first():
    """R-020 (DESIGN §6.8, §13.1): the store of paid results that is never discarded and where the cap is recorded
    (configuration); the approval before any paid action in a builder run and the dry run on the development data
    with a stand-in provider before any paid run (brief); the check that no paid action ran unapproved (inspect)."""
    conf = add("spends-money", "configuration.items")
    assert "**The store of paid results.**" in conf
    assert "reads the result already paid for on the same account instead of buying it again" in conf
    assert "**The cap** is recorded" in conf and "`Spending cap: " in conf
    # Stage B4's review, round 5: a capture, the dry run and a benchmark buy or count afresh (the passage cut back
    # to a plain rule at BUG-025's confirming read).
    # The section held whole, one `==` (stage B4's review, round 6, and Review A on BUG-026: the cap's sentence and
    # the store's opening were held by the pin alone). Round 6: the store outside the repository and the
    # Workspace, its requests without secrets; a live smoke buys afresh; a test run on a stand-in keeps a store of
    # its own; each repetition starts empty. Round 7: each request written before it is sent, one found with no
    # result put to the owner; each result kept with the account it was charged to.
    assert conf == (
        "**The store of paid results.** Before the first paid action, configure where its results are kept: a "
        "folder the design names, outside the repository and the Workspace, which no clean, reset, cache "
        "purge or test teardown reaches, each request written there before it is sent, and each result kept "
        "with the request that bought it and the account it was charged to, named by its role, all with every "
        "key, token and other secret left out as a contract capture's are scrubbed, so that a retry, a rerun "
        "or a crash reads the result already paid for on the same account instead of buying it again, and a "
        "request found there with no result (a crash, or a wait that ended, after the provider may have "
        "charged) is put to the owner with the provider's record of it, never bought again unasked. A "
        "contract capture, a re-recording or a live smoke the owner approved buys its replies afresh: it "
        "reads only the replies it has bought itself, each written there with the run that bought it in place "
        "of the one recorded before, so that a resumed run never takes an older reply for a new one. The dry "
        "run, a benchmark and a test run on a stand-in provider keep their results in a store of their own "
        "instead, outside the repository, the Workspace and this folder, empty when each run, and each "
        "repetition of a benchmark, starts, deleted whichever way it ends, and never reading this store, so "
        "that no stand-in's reply reaches it and a benchmark counts every paid call a run from cold makes. "
        "Every other run reads this store before it buys. The store is a Resources row of "
        "`docs/INVENTORY.md`, named by its role and never by a path of this computer (rule 54). **The cap** "
        "is recorded where the owner can read it: a Decisions row `Spending cap: <amount> <per month or per "
        "run> on <platform and account> (<the owner's words>, <date>)`, beside the provider's own spending "
        "limit in the account's Resources row, which configuration's spending-limits item sets."), conf
    brief = add("spends-money", "delegation-loop.brief-constraints")
    # the section held whole (stage B4's review, round 7).
    assert brief == (
        "The builder runs no paid action: a brief that needs one says so, and the paid run is the "
        "supervisor's, after the owner's approval for it. Every paid call the part's code makes goes through "
        "the store of paid results as its configuration says: its request written there before it is sent and "
        "its result with it, and the store read on the same account before a call is bought, so a retry never "
        "buys twice, a capture, a re-recording, a live smoke, the dry run, a benchmark and a test run keeping "
        "the rule that configuration gives them, and no result or request kept with a secret in it. Before "
        "any paid run, the brief's increment has run once **dry**: on the development data the inventory's "
        "`Development data:` decision names (rule 55; a copy of live data only with the owner's yes for that "
        "run, kept away from the repository and the Workspace, since it holds the users' data, and deleted "
        "whichever way the run ends), with a stand-in provider that answers as the real one does (its "
        "recorded replies, the trait *external services*' contract capture) and charges nothing, the run's "
        "every paid call counted and compared with the estimate. The first paid run of a contract capture, "
        "which has no recorded replies to stand in yet, and a paid action with no remote service behind it (a "
        "purchase) run instead at the smallest size that answers them, under their own approval, their paid "
        "calls counted beforehand against the estimate. A benchmark of an operation that calls a paid service "
        "runs against the dry run's stand-in provider, which measures the operation's paid calls for a cost "
        "budget and the part's own time, never the service's: a speed budget that includes the service's time "
        "is one the floor cannot check on the stand-in, so the design that names one says how it is measured, "
        "any paid run the measuring needs approved as a paid action of its own and run by the supervisor, and "
        "until the design says so the floor reports the budget `NOT MEASURED`, a block, never a pass, since "
        "no benchmark of it runs on the stand-in. A speed budget of an operation that calls a paid service "
        "includes the service's time unless the design records, in the owner's words, that it leaves that "
        "time out. The part's own time on the stand-in is always reported under a benchmark name of its own, "
        "never under the benchmark and metric a budget that includes the service's time names. A benchmark "
        "run against the paid service itself is a paid action of its own, approved as one, never part of the "
        "benchmark floor or of CI."), brief
    assert "The builder runs no paid action" in brief and "after the owner's approval for it" in brief
    assert "charges nothing" in brief
    # Stage B4's review, round 2: the dry run's data is the development data, a copy of live data only with the
    # owner's yes; a benchmark on the stand-in measures calls and the part's own time, never the service's.
    assert ("**dry**: on the development data the inventory's `Development data:` decision names (rule 55; a copy "
            "of live data only with the owner's yes for that run, kept away from the repository and the Workspace, "
            "since it holds the users' data, and deleted whichever way the run ends), with a stand-in provider") in brief
    assert ("A benchmark of an operation that calls a paid service runs against the dry run's stand-in provider, "
            "which measures the operation's paid calls for a cost budget and the part's own time, never the "
            "service's") in brief
    # Stage B4's review, round 3: the part's own time never stands under a service-time budget's name.
    assert ("The part's own time on the stand-in is always reported under a benchmark name of its own, never under "
            "the benchmark and metric a budget that includes the service's time names.") in brief
    assert ("a speed budget that includes the service's time is one the floor cannot check on the stand-in, so the "
            "design that names one says how it is measured, any paid run the measuring needs approved as a paid action of its "
            "own and run by the supervisor, and until the design says so the floor reports the budget `NOT MEASURED`, "
            "a block, never a pass, since no benchmark of it runs on the stand-in") in brief
    # Stage B4's review, round 4: a design that says nothing leaves the budget including the service's time.
    assert ("A speed budget of an operation that calls a paid service includes the service's time unless the "
            "design records, in the owner's words, that it leaves that time out.") in brief
    assert "budgets file" not in brief and "baseline" not in brief, "stage B4's review, round 2: no baseline exception"
    assert ("A benchmark run against the paid service itself is a paid action of its own, approved as one, never "
            "part of the benchmark floor or of CI.") in brief
    # Review A, round 1, blocking: the product's paid calls go through the store; a first capture and a purchase,
    # which have no replies to stand in, run at the smallest size instead of dry.
    assert "Every paid call the part's code makes goes through the store of paid results" in brief
    # Its pointer to the store's rule, the request written before it is sent (round 7), is held by the `==` above.
    assert "The first paid run of a contract capture, which has no recorded replies to stand in yet" in brief
    assert "a paid action with no remote service behind it (a purchase)" in brief
    assert "at the smallest size that answers them, under their own approval" in brief
    inspect = add("spends-money", "delegation-loop.inspect-checks")
    # The section held whole, one `==` (stage B4's review, round 6: the list had been held from its second item,
    # its first, a paid call with no approval naming it, and its closing duty held by the pin alone).
    assert inspect == (
        "No paid action ran unapproved, and none bypassed the store: the supervisor reads the run's log and "
        "the store of paid results, and the provider's usage for the run's time where a Resources row records "
        "a way to read it (otherwise the owner reads it at the stage close, by a run sheet); a paid call with "
        "no approval naming it, a paid call in the diff that does not read the store first, write its request "
        "there before sending it and write its result there after (a capture, re-recording or live smoke "
        "reading only the replies its own run bought, in an approved run of it only, as the store's "
        "configuration says), a capture, re-recording or live smoke that reads a reply its own run did not "
        "buy, a run other than those the configuration names that skips the store, a stand-in's reply written "
        "to the store of paid results, a dry run, benchmark or test run on a stand-in provider that reads it, "
        "a store of paid results or a run's own store inside the repository or the Workspace, a result or "
        "request kept with a secret in it, a reply read for an account other than the one it was charged to, "
        "a dry run's, benchmark's or test run's own store left after it, or a stand-in result reported under "
        "the benchmark and metric a budget that includes a paid service's time names (the benchmark results "
        "read against the budgets file and the design's record, in the owner's words, of the speed budgets "
        "that leave that time out, any other speed budget of an operation that calls a paid service read as "
        "including it), is a blocking finding, a paid call that ran unapproved also recorded as an issue and "
        "told to the owner in the next report's first line with its amount, platform and account."), inspect


def test_r020_the_test_step_runs_on_the_stand_in_provider():
    """Stage B4's review, round 7 (BUG-027): every run of the test step runs on the stand-in provider, a test that
    must reach the paid service is a live smoke under its own approval, and the new tests are read for such a call
    before their first run, so no test the loop runs spends unapproved."""
    t = add("spends-money", "delegation-loop.test-checks")
    # the section held whole (stage B4's review, round 7).
    assert t == (
        "Every run of the test step runs on the stand-in provider: the builder's own test runs, the suite, "
        "the new tests against the checkpoint, a mutation run and CI, their configuration naming no key the "
        "part's code could reach, so that no test buys anything. A test that must reach the paid service is a "
        "live smoke, the supervisor's to run under its own approval as a paid action, never part of the test "
        "step or of CI, and it is marked as one, so that the step's rule failing a skipped test of the "
        "increment does not make it run. Before their first run the new tests are read for a call that could "
        "reach the paid service; such a call, or a run of the test step that bought anything, is a blocking "
        "finding, a paid call it made also recorded as an issue and told to the owner in the next report's "
        "first line with its amount, platform and account."), t


def test_r021_long_running_process_points_at_n1_which_stays_in_the_core():
    """R-021 (DESIGN §8.1): the trait points at founding rule N1 and §8.1, which stay in the core, and adds the start,
    stop and health procedure."""
    conf = add("long-running-process", "configuration.items")
    assert "the conditions stay in the core (" in conf and "§8.1" in conf
    assert "never an exception to them" in conf
    assert "**start, stop and health**" in conf
    for verb in ("starts it", "stops it and everything it started", "reports whether it is healthy"):
        assert verb in conf, verb
    # Review A, round 3: the commands take an instance's port and data, so a test's instance runs beside the owner's.
    assert "the start and stop commands taking the port and the data of the instance they start and stop" in conf
    # Review A, round 1: a command is recorded in the increment that builds it, and N1 binds the runs the loop starts.
    assert "in its command reference, in the increment that builds it" in conf
    assert "Every run of the process the loop starts (a test, a demonstration, a check) meets founding rule N1" in conf
    assert "a run a test starts and stops being part of that test, so that no gate depends on a process it did not start" in conf
    rules = section(read(CORE), "Founding rules", 2).replace("\r\n", "\n").split("\n")
    core = [l for l in rules if l.startswith("- **N1 — Files are the truth; programs are one-shot.**")]
    assert len(core) == 1, core
    core = flat(core[0])  # N1's own bullet (stage B4's review, round 5's fix)
    n1 = ("A background process is allowed only when all eight hold", "never writes tracked files",
          "can be rebuilt from the files", "states the commit or version it reflects", "stops when idle",
          "no gate depends on it", "runs no migration of the owner's live data", "unreleased code against live data",
          "spends nothing unless asked")
    for phrase in n1:
        assert phrase in core, phrase
    for key in POINTS:
        t = flat(trait(key))
        for phrase in n1:
            assert phrase not in t, (key, phrase)


def test_r021_a_run_leaves_nothing_running():
    """R-021: the brief constraint (a run leaves nothing running; the brief says how a test starts and stops the
    process) and the nothing-left-running test check."""
    brief = add("long-running-process", "delegation-loop.brief-constraints")
    assert brief.startswith("A run leaves nothing running")
    # Review B, round 1: a test never touches the instance the owner runs, and the check stops only what the run started.
    assert "a test starts an instance of its own, on a port and data of its own, never the instance the owner runs" in brief
    assert "the brief says how a test starts that instance and how it stops it" in brief
    assert "its children included" in brief
    test = add("long-running-process", "delegation-loop.test-checks")
    assert test.startswith("Nothing the run started is left running") and "correctness-class block" in test
    # Review A, round 3: what the tests started is told by descent or by a test instance's port or data, never by
    # start time alone, and the stop never reaches the instance the owner runs.
    assert "no process the tests started (one descended from the test run, or one on a test instance's port or data)" in test
    assert "stopped by its process ID together with its children" in test
    assert "never by a command that reaches the instance the owner runs" in test
    assert "A process the owner started, or another session's, is left as it is." in test


def test_r022_ai_models_judge_by_evaluation_on_pinned_models_and_recorded_outputs():
    """R-022 (DESIGN §6.8): the evaluation sets and thresholds in place of exact tests (intake), the evaluation's design
    (design), the pinned models and the recorded outputs' home (configuration), the evaluation against the thresholds
    on recorded outputs (test check)."""
    intake = add("ai-models", "intake.questions")
    assert "the **evaluation set** that stands in for exact tests" in intake and "the **threshold**" in intake
    assert "fixed in a test (rule 52)" in intake
    design = add("ai-models", "design.sections")
    assert "**Evaluation** section" in design and "rule 51" in design
    assert "a result below it blocking the change at the test step" in design
    conf = add("ai-models", "configuration.items")
    assert "Each model is **pinned**, a model judge included" in conf and "never a name that moves to a newer model" in conf
    assert "**Recorded outputs** have a home" in conf and "without calling any model" in conf
    assert "a model judge's verdicts on them, judged again whenever the outputs are recorded again or anything" in conf
    assert "(the code after the model's reply included)" in conf
    test = add("ai-models", "delegation-loop.test-checks")
    # the section held whole (stage B4's review, round 7).
    assert test == (
        "The evaluation runs against its thresholds on the recorded outputs and their recorded verdicts with "
        "the change's tests: a result below a threshold is a correctness-class block (step 7), and an "
        "exact-match assertion on a model's output, where the evaluation set should judge it, is a finding of "
        "its own. The evaluation at this step runs the whole set, the cases kept outside the repository and "
        "the Workspace read from their place: a case not run here is a correctness-class block too, as `NOT "
        "MEASURED` is at the benchmark floor, and the not-run report of a run without those cases (CI) is "
        "that run's alone. A change that alters the prompt, the model or its settings records new outputs "
        "first, and new verdicts on them; a change to the code that shapes the judged result from a recorded "
        "reply has that result judged again; each in a run the owner has approved where a model costs money, "
        "and the evaluation reads those. Until they are recorded, the evaluation does not pass on the "
        "verdicts recorded before the change: a change whose judged result changed and whose new verdicts are "
        "not yet recorded is blocked at the test step, however the old verdicts read. A judged result has "
        "changed where it differs from the one kept beside its verdict; where a model costs money, the block "
        "waits on the run the owner approved, which the supervisor starts (a builder runs no paid action), "
        "never on a re-delegation."), test
    assert "The evaluation runs against its thresholds on the recorded outputs and their recorded verdicts" in test
    assert "correctness-class block" in test and "an exact-match assertion on a model's output" in test
    assert "records new outputs first, and new verdicts on them" in test
    assert "a change to the code that shapes the judged result from a recorded reply has that result judged again" in test
    # Review B, round 1: no pass on verdicts recorded before a change to the judged result.
    assert "the evaluation does not pass on the verdicts recorded before the change" in test
    assert "is blocked at the test step, however the old verdicts read" in test
    assert "while nothing that shapes the judged result changes, the evaluation runs again without calling any model" in conf
    # Review A, round 3: the judged result is kept beside its verdict, and a paid re-judging is the supervisor's run.
    assert "each verdict is kept with the judged result it read" in conf
    assert "where a model costs money, the block waits on the run the owner approved" in test
    assert "never on a re-delegation" in test
    # BUG-021 and stage B4's review, round 2: a case kept out of the repository lives in a development-only place,
    # apart from the live data, and the test step runs the whole set, a case not run there blocking.
    # Stage B4's review, round 3: the scrubbing clause, the security half of the sentence, is held too.
    assert ("The evaluation set's inputs and the recorded outputs are scrubbed as a contract capture's fixtures are "
            "(no key, no secret, nothing about a person the owner has not agreed to commit), and the owner, who "
            "chooses the cases, ") in conf
    assert ("is asked before the first is recorded whether they may be committed; a case that cannot be scrubbed, "
            "or that the owner keeps out, is kept with its outputs, and the verdicts and judged results recorded "
            "beside them, outside the repository and the Workspace, since it may hold something about a person, "
            "in a development-only place the Evaluation section names by its "
            "role, never by a path of a computer (rule 54), apart from the live data and never read by the product "
            "(rule 55), and a run without it (CI) reports that case as not run, never as passed.") in conf
    assert ("The evaluation at this step runs the whole set, the cases kept outside the repository and the "
            "Workspace read from their place: a case not run here is a correctness-class block too") in test
    assert "the not-run report of a run without those cases (CI) is that run's alone." in test
