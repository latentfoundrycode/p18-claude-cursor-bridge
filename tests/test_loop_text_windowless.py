"""TASK-030: the loop's text for windowless runs, the one heavy job at a time and the mutation run.

enforces: docs/BUILD_PLAN.md TASK-030's Done when (step 4's suite and mutants file, the driver kind and the checkpoint
run; step 7's mutation run with its cut, its estimate and its exit 1; the survival list's verdicts; step 3's heavy
launch's duration stated once; step 3b's exit 123, waiter and cut-short mutation run; test-runner.md, diff-reviewer.md,
spec-packager.md and KP-056; the windowless default as a configuration item in configuration.md,
Cursor-Project-Configuration.md and cursor-configurator.md; calibration writing the floor between two suite runs; the
core's rules 8 and 24); docs/REQUIREMENTS.md R-039, R-040, R-041 and R-043. Supervisor-written; no builder run.

The figures and names the text states are read from the programs that hold them (bridge-run.py, loop-guard.py,
conformance-check.py), so the text and the programs cannot drift apart unseen."""
import ast
import os
import re

from phase_modules import flat, module, read, section

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CB = os.path.join(BRIDGE, "cursor-bridge")
def loop():
    return module("delegation-loop")


def decide():
    return module("delegation-loop/decide.md")


STEP3B = "3b. A model fails mid-step — switch automatically, restart the step, never wait"


def text(*parts):
    return read(os.path.join(BRIDGE, *parts))


def constants(path):
    """The module-level constants a program assigns as literals (or, for SLOT_BUILDER_CAP, from two of them)."""
    tree = ast.parse(read(path))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                found[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                pass
    return found


def heavy_durations():
    """Each heavy kind's duration as step 3 defines it: the kind's cap (twice the launcher's default) plus the slot
    wait's bound (the builder's cap plus the grace) plus the waiter's reporting minute."""
    run = constants(os.path.join(CB, "bridge-run.py"))
    cap = lambda kind: run["CAP_FACTOR"] * run["KINDS"][kind]
    wait = cap("builder") + run["SLOT_GRACE"] + run["SLOT_REPORT"]
    return {kind: cap(kind) + wait for kind in ("builder", "driver", "test")}


def markdown_files():
    for root, _dirs, files in os.walk(BRIDGE):
        for f in files:
            if f.endswith(".md") and f != "CHANGELOG.md":
                yield os.path.join(root, f)


# --- step 3: the heavy launch's duration (R-040) ------------------------------------------------------------------

def test_r040_step_3_names_the_heavy_launchs_duration_from_the_launchers_figures():
    """R-040: step 3 names the heavy launch's duration once, in seconds and as the Bash tool's `timeout`, and the
    figures are the launcher's (the kind's cap plus the slot wait's bound plus the reporting minute); the loop guard
    counts the same wait (HEAVY_SLOT_WAIT, SLOT_GRACE, SLOT_REPORT equal the launcher's)."""
    d = heavy_durations()
    assert d == {"builder": 28980, "driver": 28980, "test": 18180}, d
    guard = constants(os.path.join(CB, "loop-guard.py"))
    run = constants(os.path.join(CB, "bridge-run.py"))
    assert guard["HEAVY_SLOT_WAIT"] == run["CAP_FACTOR"] * run["KINDS"]["builder"]
    assert (guard["SLOT_GRACE"], guard["SLOT_REPORT"]) == (run["SLOT_GRACE"], run["SLOT_REPORT"])
    s = flat(section(loop(), "The model, the timeout and the limit", 4))
    assert ("A **heavy launch** — a builder, a test suite or a mutation run (`--kind builder`, `test` or `driver`) — may "
            "wait for the computer's one slot before its command starts (step 3b), so it takes the **heavy launch's "
            "duration**: the kind's cap, plus the slot wait's bound (the builder's cap, 14,400 s, plus a grace of 120 s), "
            "plus the waiter's reporting minute.") in s
    assert ("That is 28,980 s for a builder or a mutation run, a `timeout` of `28980000`, and 18,180 s for a test suite, "
            "a `timeout` of `18180000`.") in s
    assert ("The same `timeout` goes on every heavy launch and on a wake-timer that waits for one, and the loop guard "
            "counts the same duration with its own notification grace on top.") in s
    assert ("A review or a CI watch takes the review cap, twice the launcher's default for a review: `7200000` (a "
            "learned `--limit auto` never exceeds the cap); a wake-timer bounding an agent takes its own seconds plus a "
            "minute (rule 43).") in s
    assert run["CAP_FACTOR"] * run["KINDS"]["review"] * 1000 == 7200000


def test_r040_the_heavy_figures_stand_in_one_place():
    """R-040: the heavy launch's figures stand in step 3 and nowhere else in the bridge's texts (the changelog, a
    record of releases, apart), and the caps they replaced are gone from every text (KP-053's correction names step 3
    instead of repeating them)."""
    d = heavy_durations()
    figures = ["%d" % (d["builder"] * 1000), "%d" % (d["test"] * 1000), "{:,}".format(d["builder"]),
               "{:,}".format(d["test"])]
    homes = {}
    for path in markdown_files():
        body = read(path)
        for fig in figures + ["14400000", "3600000"]:
            n = len(re.findall(r"(?<![\d,])%s(?![\d,])" % re.escape(fig), body))
            if n:
                homes.setdefault(fig, []).append((os.path.relpath(path, BRIDGE).replace(os.sep, "/"), n))
    want = [("cursor-bridge/workflow/phases/delegation-loop.md", 1)]
    assert {f: homes.get(f) for f in figures} == {f: want for f in figures}, homes
    assert "14400000" not in homes and "3600000" not in homes, homes
    # the figures in bare seconds stand nowhere either (step 3 writes them with a thousands comma)
    for path in markdown_files():
        for fig in ("%d" % d["builder"], "%d" % d["test"]):
            assert not re.search(r"(?<![\d,])%s(?![\d,])" % fig, read(path)), (path, fig)
    kp53 = flat(text("cursor-bridge", "Known-Pitfalls.md")).split("### KP-053")[1].split("### KP-054")[0]
    assert ("every background launch sets the Bash tool's `timeout` in milliseconds as "
            "`~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`, step 3, gives it for its kind (a heavy launch's "
            "duration covers its wait for the computer's one slot), the same on a wake-timer;") in kp53


# --- step 3b: the slot's exits (R-040) ----------------------------------------------------------------------------

def test_r040_step_3b_handles_the_slots_exits_without_a_model_failure():
    """R-040: exit 123 never started the command; the wait for the holder's end is a wake-timer until the `ends by`
    time, then one relaunch, a second 123 retried twice more and then the owner told; `held by unknown` relaunches at
    once and a second such 123 tells the owner, naming the lock; no 123 reaches roster-check.py; a waiter killed from
    outside is relaunched; a cut-short mutation run is relaunched once from its cache; the wait is never a reason to
    start the command another way. The waiter's lines are the launcher's own."""
    s = flat(section(loop(), "Waiting for the slot, and a mutation run cut short", 4))
    assert section(loop(), STEP3B, 3).count("#### Waiting for the slot, and a mutation run cut short") == 1
    for sentence in (
        "A run waiting for the slot is the launcher's business: it is never a reason to start the command another way.",
        "Nothing below is a model's failure, and no exit below is passed to `roster-check.py`:",
        "The wait ended unmet (`bridge-run: slot not free - held by ...`), so the command never started and nothing was "
        "spent.",
        "Wait for the holder's end with `python ~/.claude/cursor-bridge/wake-timer.py <seconds> \"<the run that waits>\"` "
        "in the background, the seconds being the time left until the `ends by` time the exit line printed, or zero when "
        "it has passed; then relaunch once, unchanged.",
        "The timer's closing line, which tells you to run a task in the foreground, does not apply here: its "
        "completion means the relaunch, through the launcher.",
        "A second 123 naming a holder is retried twice more the same way; after that, tell the owner, naming the holder's "
        "kind and run id.",
        "A 123 reading `held by unknown` (the launcher waited its provisional bound and never read a live holder's "
        "record) relaunches at once, and a second such 123 in a row is told to the owner at once, naming "
        "`~/.cursor-bridge/heavy.lock`: it is a sign of a defect, not of a busy computer.",
        "**A waiter killed from outside** — its output file holds waiting lines and neither `slot taken` nor "
        "`bridge-run: exit` (KP-053) — is relaunched; nothing was spent.",
        "**A driver run cut short** — ended at its limit (exit 124), or killed from outside after `slot taken` (no "
        "`bridge-run: exit` line) — is relaunched once: a mutation run continues from its cache, the kills it "
        "recorded standing (step 7), and a program under `run/supervisor/` starts again.",
        "One that edits the Workspace's files in place keeps a copy of each file it edits under `run/supervisor/` "
        "before its first edit, taken from the tree as it stands and never replaced by a relaunch, and at every start "
        "first puts back each file that differs from its copy (KP-056's residue check), so a relaunch undoes what the "
        "killed run left and the builder's uncommitted work is never touched.",
    ):
        assert sentence in s, sentence
    launcher = read(os.path.join(CB, "bridge-run.py"))
    for line in ("waiting for the slot held by", "slot taken", "slot not free - held by", "unknown"):
        assert line in launcher, line
    assert "`bridge-run: waiting for the slot held by <kind> <run id> since <start>, ends by <end>`" in s
    # the three kinds step 3 calls heavy are the launcher's
    assert 'HEAVY_KINDS = frozenset(("builder", "driver", "test"))' in launcher


# --- step 4: the suite, the mutants file, the driver and the checkpoint run (R-039, R-041) ---------------------------

def test_r039_every_suite_runs_through_the_launcher_and_test_runner_reads_its_file():
    """R-039: a suite is the recorded suite command or any run of more than the increment's own test files; every
    suite runs through the launcher in the background, whatever its length, and test-runner reads the output file; the
    increment's own test files alone may run in the foreground; test-runner.md says the suite is always the
    launcher's background run whose file it reads."""
    s = flat(section(loop(), "The tests before the first reviewer", 4))
    for sentence in (
        "A suite is the project's recorded suite command, or any run of more than the increment's own test files.",
        "The suite runs through the launcher in the background, whatever its length: `python "
        "~/.claude/cursor-bridge/bridge-run.py --limit auto --kind test -- <the recorded suite command> > "
        "run/agent/TASK-<nnn>-suite.out 2>&1`, under the heavy launch's `timeout` (step 3); its completion wakes you, "
        "and `test-runner` then reads that file.",
        "so a suite never runs in the foreground and its expected length no longer chooses the path.",
        "A run of the increment's own test files alone may run in the foreground, yours or `test-runner`'s, since this "
        "session's console is hidden (a probe of 2026-10-20), where it ends within the ten minutes a foreground "
        "command has (KP-061); a longer one runs through the launcher like a suite.",
    ):
        assert sentence in s, sentence
    tr = flat(text("agents", "test-runner.md"))
    assert ("The suite is always the supervisor's launch through the launcher in the background, and you read the "
            "output file it names you (`run/agent/TASK-<nnn>-suite.out`).") in tr
    assert "you may run the increment's own test files alone in the foreground." in tr


def test_r041_every_mutation_run_is_mutation_run_py_through_the_driver_kind():
    """R-041: the mutants file is run/supervisor/<id>-mutants.json, the supervisor's with the criterion tests, never
    the builder's; the engine is mutation-run.py on a scratch copy; a driver is a Python program under run/supervisor/
    or a mutation-run.py run and nothing else; every mutation run goes through `--kind driver` in the background under
    the heavy launch's timeout; `# wake` is not available for a driver. The reword of the settled sentence that the
    supervisor writes the driver is named in trace-exceptions.md."""
    s = flat(section(loop(), "The tests before the first reviewer", 4))
    for sentence in (
        "The increment's mutants are written here too, on your side, after the builder's run and never by the builder, "
        "in its mutants file `run/supervisor/<id>-mutants.json` (`<id>` the increment's ID)",
        "with the criterion tests those name, which are yours too",
        "The engine that applies each mutant, runs its tests and records the outcome is the bridge's `mutation-run.py`, "
        "reviewed at the bridge's own gate; it works on a scratch copy of the Workspace and so restores nothing in it.",
        "A **driver** is a Python program under `run/supervisor/` or a `mutation-run.py` run, and nothing else, and every "
        "mutation run is a `mutation-run.py` run through the launcher's driver kind (`--kind driver`), in the background "
        "under the heavy launch's `timeout`",
        "the step resumes when its completion arrives.",
        "`# wake` is not available for a driver: it stays for a benchmark or a runner the launcher does not know, each "
        "named with its reason in the status file.",
    ):
        assert sentence in s, sentence
    entries = read(os.path.join(CB, "workflow", "trace-exceptions.md"))
    assert "- reword TASK-030 bridge/commands/supervisor.md 4. Inspect" in entries
    settings = read(os.path.join(CB, "settings.bridge.json"))
    assert "Bash(python ~/.claude/cursor-bridge/bridge-run.py --limit * --kind driver -- *)" in settings


def test_r041_the_checkpoint_run_is_mutation_run_py_and_each_result_has_its_handling():
    """R-041 (TASK-030): the new tests' run against the checkpoint is `mutation-run.py --checkpoint`, the new tests
    listed in `new_tests` (a new file by path, a changed file by its new tests' ids) and staged; no old-<nnn> worktree;
    exit 4 sends each test passing on the old code back before any reviewer; `not run` is said; exit 3 stops the step,
    never a model failure. The labels are the program's own."""
    s = flat(section(loop(), "The tests before the first reviewer", 4))
    for sentence in (
        "list the increment's new tests in the mutants file's `new_tests` (a new test file by its path, a changed file "
        "by its new tests' ids), stage them (`git add`), and launch `python ~/.claude/cursor-bridge/bridge-run.py "
        "--limit auto --kind driver -- python ~/.claude/cursor-bridge/mutation-run.py run/supervisor/<id>-mutants.json "
        "--checkpoint <the increment's checkpoint commit> > run/agent/<id>-checkpoint.out 2>&1` in the background like "
        "any mutation run.",
        "The program runs the listed tests on a copy of the tree at that commit, so no worktree of your own is needed "
        "(rule 39's `old-<nnn>` worktree stays unused).",
        "so each test the output marks `passing on old code` goes back to be rewritten before any reviewer reads the "
        "diff.",
        "A test the output marks `not run` (it cannot collect, or ran nothing, on the old code) is neither pass nor "
        "fail, and is said.",
        "Exit 3 stops the step: it is the run's own result, recorded as such, never a model failure;",
        "exit 2 is a refused file or path, or the program's resolution check refusing the run (a module that "
        "resolves outside the copy or nowhere, a module loaded from the Workspace, or the check's own failure), "
        "each fixed before the run is launched again; where the cause is an editable install of the package "
        "(KP-054: its `__file__`, read from a folder outside the Workspace, names the Workspace), no correction "
        "helps, so \"not run against the checkpoint: editable install\" goes on `run/supervisor/in-flight.md` and "
        "into the SCOPE file, the reviewer's check of each test against its paragraph standing in, and the first "
        "time, an Issues entry names the install and its remedy (the tests run from an environment without it) "
        "and the inventory names it as a hazard, so the lost coverage is a recorded condition of the project.",
    ):
        assert sentence in s, sentence
    assert "git worktree add" not in s and "Worktrees/old-" not in flat(loop())
    program = read(os.path.join(CB, "mutation-run.py"))
    for label in ('"passing on old code"', '"%s: not run"', '"new_tests"', "return 4 if any_pass else 0",
                  "resolves outside the copy", "module from Workspace path %s was loaded"):
        assert label in program, label


def test_r041_the_agents_and_kp_056_say_the_same_of_the_mutation_run():
    """R-041: diff-reviewer.md and spec-packager.md say the engine is mutation-run.py on a scratch copy and the
    mutants file the supervisor's, read against each mutant's name; KP-056's correction says the same."""
    dr = flat(text("agents", "diff-reviewer.md"))
    assert ("The mutants are the supervisor's mutants file, `run/supervisor/<id>-mutants.json`, and the engine that "
            "applies them is the bridge's `mutation-run.py`, which works on a scratch copy of the Workspace and so "
            "restores nothing in it. Read each mutant in the file against its name as you read a test against its "
            "paragraph") in dr
    assert ("A driver of the supervisor's under `run/supervisor/` that edits the Workspace's files in place is read "
            "for its restore too: it restores each file in a `finally` and aborts on a byte mismatch at restore; one "
            "that works on a scratch copy restores nothing.") in dr
    sp = flat(text("agents", "spec-packager.md"))
    assert ("the mutation run itself (the supervisor's mutants file, applied by the bridge's `mutation-run.py` on a "
            "scratch copy of the Workspace) is the supervisor's side's, written after your run with the criterion "
            "tests") in sp
    kp = flat(text("cursor-bridge", "Known-Pitfalls.md")).split("### KP-056")[1].split("### KP-057")[0]
    assert ("the mutants are written on the supervisor's side, in its mutants file with the criterion tests, never by "
            "the builder (2026.10.11d), and since release B the bridge's `mutation-run.py` applies them on a scratch copy "
            "of the Workspace, launched through the launcher's driver kind, so a run killed at any point leaves no "
            "mutant in the product") in kp
    assert ("so the loop never advances into its next driver (before that release, only between drivers, its "
            "`bash.exe` first);") in kp
    assert "a driver that edits product files in place aborts on a byte mismatch at restore;" in kp
    assert "until then" not in kp


# --- step 7: the mutation run, its cut and its estimate (R-043) -----------------------------------------------------

def test_r043_the_mutation_run_is_launched_at_step_7_on_every_pass():
    """R-043: the run is launched at step 7 on every pass, after Review A and the auditors accepted the behaviour and
    before step 8's snapshot, never at every round's step 4; the checkpoint run stays at step 4; the cache skips
    what is unchanged and `--all` is the full run."""
    assert "#### The mutation run" in section(decide(), "7. Decide (accept the increment)", 3)
    s = flat(section(decide(), "The mutation run", 4))
    for sentence in (
        "The mutation run is launched here, on every pass through this step: once Review A and the auditors have "
        "accepted the increment's behaviour, and before step 8's snapshot; never at every round's step 4",
        "The new tests' run against the checkpoint (`--checkpoint`) stays at step 4, before any reviewer.",
        "python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind driver -- python "
        "~/.claude/cursor-bridge/mutation-run.py run/supervisor/<id>-mutants.json > run/agent/<id>-mutation.out 2>&1",
        "a mutant whose keyed inputs (the mutated file's folder, the test folders it runs, the suite's configuration "
        "and the mutant itself) are byte-identical since its last kill keeps that kill, and every survived, unapplied "
        "or erred mutant runs again.",
        "Add `--all` for the full run where a round changed files outside every key.",
        "The Accept bullet's commit may come before the run; the move to the next increment waits for its result.",
    ):
        assert sentence in s, sentence


def test_r043_the_cut_and_the_estimate_come_first_and_go_on_the_in_flight_line():
    """R-043 (FB-040): before the first run, any `--all` run and any run after the file changed since its last
    estimate, the duplicates the file shows are removed (never a criterion test, nothing on a kept kill), then the
    process count is estimated to its order of magnitude per distinct tests list, and both go on in-flight.md."""
    s = flat(section(decide(), "The mutation run", 4))
    for sentence in (
        "Before the increment's first mutation run, before any `--all` run, and whenever the mutants file has changed "
        "since its last estimate:",
        "A mutant whose `file`, `pairs` and expectations (`tests`, `expect_fail`, `expect`) equal another's is the same "
        "mutant under a second `id`: remove its entry from the mutants file before the launch, so the program never "
        "applies it.",
        "This needs no run and no kill, and nothing else is cut: never a criterion test, and nothing on the strength of a "
        "kept kill (the cache's skipping is the program's own, and an `--all` run is chosen exactly where a kept kill is "
        "distrusted).",
        "**Estimate the run's process count** to its order of magnitude, from the file as it stands after the cut.",
        "For each distinct `tests` list among the mutants the run will apply (every mutant for `--all`, otherwise those "
        "with no kept kill; two lists naming the same test files in any order are one list), count the processes one "
        "completed run of that list starts: the pytest process, plus every launch its tests make, counted once per pass "
        "the run makes through it (each parametrization, each loop iteration), plus the programs those launched programs "
        "start in turn.",
        "Read the launches from the launcher's run log (`run/launcher/runs.jsonl`) where they go through the launcher, "
        "since it holds the launcher's runs and nothing else, and otherwise from the launch sites in the tests and in the "
        "programs they launch, with their pass counts; a counting run is launched the way step 4 launches a run of its "
        "kind.",
        "Reuse each list's count for every mutant that lists it: the sum over the mutants to apply, plus the one "
        "collection check, is the estimate.",
        "the cuts made and the estimate go on `run/supervisor/in-flight.md`, with the mutants file's name.",
    ):
        assert sentence in s, sentence
    # the fields the cut compares are the mutants file's own (mutation-run.py's loader)
    program = read(os.path.join(CB, "mutation-run.py"))
    for field in ('"file"', '"pairs"', '"tests"', '"expect_fail"', '"expect"'):
        assert field in program, field


def test_r043_exit_1_follows_the_ceiling_and_exit_3_is_the_runs_own():
    """R-043: at or below the ceiling a criterion test's fix is the supervisor's and no round, a code fix a
    re-delegation and a round; above it the mutant goes to HARDENING unless a safety mechanism or a blocking-class
    defect; exit 3 is never a model failure; nothing reaches roster-check.py."""
    s = flat(section(decide(), "The mutation run", 4))
    for sentence in (
        "Take the larger of the two next counts: the review guard's rounds opened for the increment plus one, and the "
        "launcher's round of the brief that would carry a code fix.",
        "Where it is at or below the code gate's ceiling of three rounds, the mutant is fixed: a criterion test's fix is "
        "yours and no round; a code fix is a re-delegation (above) and a round.",
        "A mutant not applied (its text no longer in its file) is re-anchored in the mutants file, yours and no round; "
        "a fix of yours after Review A's read stands in the diff Review B reads at step 8.",
        "**Exit 2** — the mutants file or a path in it was refused: correct the file and launch again. Or the "
        "program's resolution check refused the run; where the cause is an editable install of the package "
        "(KP-054; step 4 tells it apart and records it as an issue the first time), no correction helps, so the "
        "run is not made, `mutation run not made: editable install` goes on `run/supervisor/in-flight.md` and "
        "into the SCOPE file, and the reviewers' reading of each mutant against its name stands in; it is the "
        "run's own result, never a model failure.",
        "Above the ceiling, the mutant goes to `docs/HARDENING.md` under the increment and never to a re-delegation, "
        "unless the code it shows untested is a safety mechanism the increment relies on, or the result shows a defect "
        "of a blocking class (behaviour against the brief or the register, security, data integrity, a defeated safety "
        "mechanism, a failing test).",
        "**Exit 3** — a mutant erred or the program failed: the step stops, and the result is the run's own, recorded "
        "as such, never a model failure; no exit of the program is passed to `roster-check.py`.",
    ):
        assert sentence in s, sentence


# --- the windowless default as a configuration item and at calibration (R-039) ---------------------------------------

def test_r039_the_snapshot_the_texts_name_is_the_one_task_028_ships():
    """R-039: every text that names the default names `~/.claude/cursor-bridge/windowless-default.snapshot.md`, the
    file TASK-028 ships (whose block test_conformance_windowless.py holds equal to tests/conftest.py's), and the
    tokens and the floor they name are the conformance check's."""
    assert os.path.isfile(os.path.join(CB, "windowless-default.snapshot.md"))
    check = constants(os.path.join(CB, "conformance-check.py"))
    tokens = check["WINDOWLESS_TOKENS"]
    assert tokens == ("windowless_kwargs", "Popen.__init__", "CREATE_NO_WINDOW")
    named = "(`%s`, `%s`, `%s`)" % tokens
    assert "Windowless test suite" in read(os.path.join(CB, "conformance-check.py"))
    homes = {
        "configuration.md": flat(section(module("configuration"), "The windowless test suite", 3)),
        "Cursor-Project-Configuration.md": flat(text("cursor-bridge", "Cursor-Project-Configuration.md")),
        "cursor-configurator.md": flat(text("agents", "cursor-configurator.md")),
    }
    for name, body in homes.items():
        assert "~/.claude/cursor-bridge/windowless-default.snapshot.md" in body, name
        assert named in body, name
        assert "where one exists" in body and "every other line as it stands" in body, name
        assert "(`tests/conftest.py`, with its folder, where the project has no test root yet)" in body, name
    for name in ("configuration.md", "Cursor-Project-Configuration.md"):
        assert "`Windowless test suite`" in homes[name], name
    assert "see `Cursor-Project-Configuration.md`, windowless-default item" in flat(
        read(os.path.join(CB, "windowless-default.snapshot.md")))
    assert "- **The windowless-default item — the test suite's frozen default.**" in text(
        "cursor-bridge", "Cursor-Project-Configuration.md")


def test_r039_the_configuration_texts_carry_the_item():
    """R-039: configuration.md's section, the configuration guide's §2 item and its order of operations, and the
    configurator's list carry the item, with the floor that checks it and the NOTE a Node suite gets."""
    s = flat(section(module("configuration"), "The windowless test suite", 3))
    assert ("the configurator creates the test root's `conftest.py` from the block only where the test root has none "
            "(`tests/conftest.py`, with its folder, where the project has no test root yet), and where one exists "
            "inserts the block once, at the file's end, unless the file already holds its three tokens") in s
    guide_item = flat(text("cursor-bridge", "Cursor-Project-Configuration.md"))
    assert "exists it inserts the block once, at the file's end, unless the file already holds its three tokens" in (
        guide_item)
    assert "insert the block once, at the file's end, unless the file already holds its three tokens" in flat(
        text("agents", "cursor-configurator.md"))
    assert "A Node suite has no default yet: the check gives it a NOTE naming its runner and KP-059's mechanism" in s
    guide = text("cursor-bridge", "Cursor-Project-Configuration.md")
    order = flat(guide.split("## Configuration run — order of operations", 1)[1])
    assert ("then write the test suite's windowless default into the test root's `conftest.py` (§2, the "
            "windowless-default item) and record a Node suite's NOTE.") in order
    two = flat(guide.split("## 2. The feedback loop", 1)[1].split("\n## ", 1)[0])
    assert "The windowless-default item — the test suite's frozen default." in two
    assert "A running project receives the item at calibration, which writes it before the project resumes" in two
    cfg = flat(text("agents", "cursor-configurator.md").split("## What you write", 1)[1].split("## Hard limits", 1)[0])
    assert ("The test root's `conftest.py` — the frozen windowless default, for **every** project whose suite is pytest. "
            "The **block is the fenced block of `~/.claude/cursor-bridge/windowless-default.snapshot.md`**, written "
            "verbatim") in cfg
    assert cfg.index("`.cursor/rules/secure-coding.mdc`") < cfg.index("The test root's `conftest.py`")


def test_r039_calibration_writes_the_floor_between_two_suite_runs():
    """R-039: calibration writes the floor during the calibration, before the project resumes, the recorded suite run
    before and after the write in the background through the launcher, the two reports' failed ids compared, an
    insert-caused failure reverting the insert, the results on the Calibrated: line, no gate reopened."""
    cal = flat(text("commands", "calibrate-bridge.md"))
    for sentence in (
        "**The `Windowless test suite` floor is the one written during this calibration**, before the project resumes",
        "Run the project's recorded suite once, with `-rA` added where the command lacks it, in the background through "
        "the launcher: `python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind test -- <the recorded suite "
        "command> -rA > run/agent/calibrate-suite-before.out 2>&1`, under the heavy launch's `timeout`",
        "Run the same suite once more the same way, into `run/agent/calibrate-suite-after.out`, and read it when its "
        "completion arrives.",
        "the run waits for the computer's one slot). Read the output file when its completion arrives.",
        "Have `cursor-configurator` write the default from `~/.claude/cursor-bridge/windowless-default.snapshot.md` "
        "exactly as configuration writes it (`Cursor-Project-Configuration.md` §2, the windowless-default item): the "
        "test root's `conftest.py` created from the snapshot's fenced block where the test root has none, or the block "
        "inserted once at the end of the one that exists, every other line left as it stands.",
        "Compare the two reports: their failed and erred test ids, the number of tests each collected, and each run's "
        "exit status. A before-run that itself ends in pytest's exit 2 to 5 ran no comparable tests and proves "
        "nothing: the write is committed as the calibration's checkpoint and recorded as unverified, whatever the "
        "after-run shows. Otherwise, a failure or error present before the write is the project's own: it is "
        "recorded, and the write stands.",
        "A failure or error present only after the write, fewer tests collected after it than before, or an after-run "
        "ending in pytest's exit 2 to 5 (interrupted, an internal error, a usage error such as a `conftest.py` that "
        "fails to import, no tests collected) where the before-run did not, is the insert's: it leads the report's "
        "first line, the insert is "
        "reverted, the reverted tree is committed as the calibration's checkpoint, and the floor stays `MISSING`, named "
        "in the report.",
        "named in the report. Otherwise the write is committed as the calibration's checkpoint.",
        "Write the two runs' results on the `Calibrated:` line (step 5).",
        "the line also names the two suite runs' results (item 4's comparison: the failed and erred ids, the collected "
        "counts and the exit statuses, before and after the write) and whether the write stands, stands unverified or "
        "was reverted.",
        "It is a configuration item: no gate is reopened, and the loop resumes after it.",
        "A Node suite's NOTE (its default is not shipped yet) is recorded in `PROJECT_STATUS.md` like any NOTE.",
        "Where step 1b wrote the windowless default, the line also names the two suite runs' results",
    ):
        assert sentence in cal, sentence


# --- the core (R-039, R-041) -----------------------------------------------------------------------------------------

def test_r039_r041_rules_8_and_24_name_the_runs_and_the_default():
    """Rule 8 names the suites and the mutation runs and excepts the driver kind's `python <program>`, the launcher's
    path check being the guard; rule 24 names the suite's default."""
    core = flat(text("commands", "supervisor.md"))
    rule8 = core.split(" 8. Never chain shell commands", 1)[1].split(" 9. Never merge", 1)[0]
    assert ("and the mutation runs (`--kind driver`: `python` with a program under `run/supervisor/` or the installed "
            "`mutation-run.py`); never with an option that runs another program, but for the driver kind's `python "
            "<program>`, whose program the launcher's path check confines.") in rule8
    assert "Every suite and every mutation run goes through it, in the background (the delegation loop's step 4)." in rule8
    # rule 43 counts a mutation run as a wake source, as the loop guard does (Review A, TASK-030 round 1)
    rule43 = core.split(" 43. Never end a turn", 1)[1].split(" 44. ", 1)[0]
    assert ("a test suite you await, run through the launcher (`--limit auto --kind test`), or a mutation run or "
            "another driver, run through it too (`--kind driver`), or a benchmark,") in rule43
    assert '"driver"' in read(os.path.join(CB, "loop-guard.py"))
    rule24 = core.split(" 24. Windowless by default.", 1)[1].split(" 25. Refactoring", 1)[0]
    assert ("A project's test suite carries the bridge's frozen windowless default "
            "(`~/.claude/cursor-bridge/windowless-default.snapshot.md`, the pytest `conftest.py` block), written at "
            "configuration and at calibration and checked by the conformance floor `Windowless test suite`; and every "
            "suite and mutation run starts through the launcher, which starts it windowless.") in rule24
