"""BUG-043 (stage T2's review, round 2): the increment's own test files run stripped, and the claim says what the launches do; written by the supervisor.

enforces: docs/debug/BUG-043.md; docs/REQUIREMENTS.md R-052 (the loop's launches run stripped); docs/diagrams/D-004-context-dfd.md, the note "Stripped environment". The loop's step 4 said code the builder wrote never runs with the owner's login, six lines above a sentence letting that code, the increment's own test files, run in the foreground with the owner's whole environment. The round's records findings are held here too: R-042's `P2:` entry, which TASK-045's stamp test reads, and the design past the retrofit.
"""
import os
import subprocess
import sys

import test_bridge_run as B
from permission_rules import decide
from test_allowlist import ALLOW, DENY, HEAVY_RULES
from permission_rules import rule_matches

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
BRIDGE = os.path.join(ROOT, "bridge")
OWN_FILES = ("python ~/.claude/cursor-bridge/bridge-run.py --limit auto --strip --kind test -- <the project's test command> "
             "<the increment's test files> > run/agent/TASK-<nnn>-own.out 2>&1")
OLD_CLAIM = "never runs in the loop"
LIMITS = ("a runner the launcher refuses, and a benchmark or profile; a build, a type check or a linter; a hook a commit runs; "
          "a reviewer's or auditor's own run beside its reading; a root-cause reproduction; an installer rehearsal; "
          "a live smoke and a stage demonstration's start of the product")


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def flat(text):
    return " ".join(text.split())


def loop():
    return flat(read(BRIDGE, "cursor-bridge", "workflow", "phases", "delegation-loop.md"))


def row(rid):
    for line in read(ROOT, "docs", "REQUIREMENTS.md").split("\n"):
        if line.startswith("| %s |" % rid):
            return line
    raise AssertionError(rid)


def test_bug043_the_loop_runs_the_increment_s_own_files_through_the_launcher():
    text = loop()
    assert "A run of the increment's own test files alone goes through the launcher the same way, yours and never `test-runner`'s, since it runs code no reviewer has read: `" + OWN_FILES + "`, in the background under the same `timeout`, and `test-runner` reads that file." in text
    assert "A run of the increment's own test files alone may run in the foreground" not in text
    assert "A stripped suite or own-file run that fails for want of a variable takes `--key-file` as above, a variable nothing names being the run's failure, back to the builder or the owner, and for want of a file a variable naming a copy outside the Workspace, never a home variable, which would undo the home redirect; it is never run again without `--strip`, and a 125 on a runner you know, or naming the agent home, is a defect to fix, not a runner the launcher does not know." in text


def test_bug043_the_test_runner_reads_their_file():
    text = flat(read(BRIDGE, "agents", "test-runner.md"))
    assert "you may run the increment's own test files alone in the foreground." not in text
    assert "The increment's own test files alone are the supervisor's launch too, stripped, in the background, since they run code no reviewer has read: `" + OWN_FILES + "` (D-004, R-052), and you read that file." in text
    assert "If you are asked to run either yourself, say so and hand the command back." in text
    assert "A stripped run that fails for want of a variable or a file is said so in your report, for the supervisor's `--key-file` where the brief or the inventory names it, and never run again without `--strip`." in text
    assert "so read the run's file first" in text
    assert "so run the suite first" not in text
    assert "You run tests and report failures." not in text
    assert "the run is lost with its result" not in text


def test_bug043_the_claim_says_what_the_flag_withholds():
    """Review A's B1 and the audit's B3 of the second text: a sentence about every launch of the loop was false against `# wake`'s direct run and against the key file in its own next clause. It now says what the flag withholds, and what a key file hands over."""
    assert OLD_CLAIM not in loop()
    assert "no launch of the loop" not in loop()
    assert "the flag withholds the owner's `gh` and git login and the environment's secret-like variables from code the builder wrote (D-004, R-052). A variable the suite needs reaches it by `--key-file <a file outside the Workspace>`, which the test kind accepts and which hands that code what the file names, so a key file holds only what the brief or the inventory names for this increment, or the loop's own step names, never what a test's failure asks for:" in loop()
    design = flat(read(ROOT, "docs", "DESIGN.md"))
    assert "builder-written code never runs in the loop" not in design
    assert "no launch of the loop" not in design
    assert "so the flag withholds the owner's `gh` and git login and the environment's secret-like variables from builder-written code" in design
    inventory = flat(read(ROOT, "docs", "INVENTORY.md"))
    assert "no launch of the loop" not in inventory
    assert "the flag withholds the owner's `gh` and git login and the environment's secret-like variables from code the builder wrote" in inventory
    d004 = flat(read(ROOT, "docs", "diagrams", "D-004-context-dfd.md"))
    assert "a suite's or own-file run's named key values by --key-file, handed to that code" in d004


def test_bug043_every_home_states_a_class_not_a_count():
    """Review A's B1 and the audit's B1: "three runs" was a new absolute with the old claim's fault, and the next sentence of the same paragraph disproved it. What stays in a session's own environment is a class, stated where the claim stands, so an auditor reading every crossing of D-004 is told it exists."""
    assert "The strip is instructed, no program holding the flag, and reaches only what goes through the launcher. Whatever else runs what a builder wrote on this computer runs in a session's own environment, stated limits (`docs/INVENTORY.md`, Decisions; D-004), among them: " + LIMITS + "." in loop()
    design = flat(read(ROOT, "docs", "DESIGN.md"))
    d004 = flat(read(ROOT, "docs", "diagrams", "D-004-context-dfd.md"))
    inventory = flat(read(ROOT, "docs", "INVENTORY.md"))
    assert "whatever does not go through the launcher runs in a session's own environment, stated limits (INVENTORY, Decisions; D-004), among them: " + LIMITS in design
    assert "Whatever does not go through the launcher runs in a session's own environment, stated limits (`docs/INVENTORY.md`, Decisions; BUG-043), among them: " + LIMITS in d004
    assert 'ds_checkout -->|"UNTRUSTED: code and tests the builder wrote, run in the session\'s own environment: stated limits (BUG-043)"| p_supervisor' in d004
    assert "the increment's own test files with them (BUG-043)" in d004
    assert "| The strip reaches only what goes through the launcher, and no program holds the flag:" in inventory
    assert "whatever else runs what a builder wrote on this computer runs in a session's own environment, stated limits, among them: " + LIMITS in inventory
    assert "the increment's own test files run stripped too (BUG-043;" in flat(row("R-052"))
    for text in (loop(), design, d004, flat(read(ROOT, "docs", "debug", "BUG-043.md"))):
        assert "hree runs stay" not in text


def test_bug043_step_4_reads_the_git_config_as_a_file_first():
    """The audit's B2 of the first text; Review A's B2 and S1 and the audit's B1 and B2 of the second: a `.git` setting a builder or its tests wrote runs on the session's next git command, in its own environment, and no diff shows `.git`. The read stands after every run of what a builder wrote, reads a class of lines, and says what it is: text cannot hold the order, so it is a check, not a boundary, and the launcher's comparison is a program item."""
    assert "After a run of what a builder wrote (a builder, the own-file run and a suite among them) and before your next git command, step 3b's `git status` and reset and a parallel branch's switch included, read `.git/config` with the Read tool, never through git, and list the active hooks folder and `.git/hooks`, and for a builder in a worktree that worktree's own hooks folder as `core.hooksPath` resolves there: a line you did not write that names a program, another file or a host (`core.fsmonitor`, a foreign `core.hooksPath`, `diff.*`, `filter.*`, `include*`, `extensions.*`, `http.proxy`, `remote.*.pushurl`, `url.*`, among them), a new hook, or a `.git/config` that cannot be read is a gate-integrity flag, the line removed by hand (KP-032). The read holds after each such run, wherever a module or a sub-file states the next git command, the first of a reviewer you send next among them, whether or not that site repeats it. This is a check, not a boundary: the strip does not keep a run from writing `.git`, a listing shows a new hook and not a changed one, nor one the branch holds and the disk does not, and a git command the session or the app runs first still runs what it wrote; the launcher's comparison before and after a run is a program item." in loop()
    plan = flat(read(ROOT, "docs", "BUILD_PLAN.md"))
    assert "a launcher comparison of `.git/config`, `.git/config.worktree`, `.git/info/attributes` and the hooks folders before and after a run of what a builder wrote" in plan
    assert "a refusal of a home variable in a `--key-file`" in plan


def test_bug043_the_read_holds_wherever_a_git_command_follows_a_run():
    """Review B's second finding: step 4's sentence names step 3b's `git status` and reset and a parallel branch's switch, while those sites still put the git command first, so a reader at the site runs what a builder wrote before the read. Each site that says what comes first now says the read does; Review A's B1 and B2 on that fix: naming sites left the checkpoint run's `git add` and P7's push, so step 4 states the class and those two repeat it."""
    text = loop()
    read_first = "step 4's read of `.git/config` and the hooks folders, then "
    assert "look before you discard** (KP-033): " + read_first + "`git status` and `git diff --stat` in the checkout." in text
    assert "**Restart point first.** A delegation: " + read_first + "the working tree goes back to the pre-delegation checkpoint (`git reset --hard <checkpoint sha>`" in text
    assert "**When a builder finishes**, make " + read_first + "remove its worktree from your checkout" in text
    decide_text = flat(read(BRIDGE, "cursor-bridge", "workflow", "phases", "delegation-loop", "decide.md"))
    assert "a state you cannot make sense of: " + read_first + "`git reset --hard HEAD` returns you to the checkpoint." in decide_text
    assert "The read holds after each such run, wherever a module or a sub-file states the next git command, the first of a reviewer you send next among them, whether or not that site repeats it." in text
    assert "make " + read_first + "stage them (`git add`), and launch" in text
    merge = flat(read(BRIDGE, "cursor-bridge", "workflow", "phases", "delegation-loop", "merge.md"))
    assert "The push comes after step 4's read of `.git/config` and the hooks folders: a `pre-push` hook, a `core.sshCommand` or a credential helper line that run wrote fires, each on its transport, on the command that carries the login." in merge


def test_bug043_the_read_lists_a_worktree_s_own_hooks_folder():
    """The audit's B1 on that fix: a relative `core.hooksPath` makes a hook a parallel builder committed in its worktree fire at the teardown's status and at the switch, after a clean read of the supervisor's checkout. Reproduced with the real worktree-teardown.py."""
    assert "and list the active hooks folder and `.git/hooks`, and for a builder in a worktree that worktree's own hooks folder as `core.hooksPath` resolves there:" in loop()
    assert "a listing shows a new hook and not a changed one, nor one the branch holds and the disk does not," in loop()
    assert "`worktree-teardown.py` turning hooks off as it turns off the file monitor; a read of the hooks a finished parallel branch holds before its switch;" in flat(read(ROOT, "docs", "BUILD_PLAN.md"))


def test_bug043_d004_s_note_names_no_only():
    """Review B's first finding: "instructs only for a driver" was the absolute the fix removed from the loop, false against the note's own next sentences."""
    d004 = flat(read(ROOT, "docs", "diagrams", "D-004-context-dfd.md"))
    assert "instructs only for a driver" not in d004
    assert "and driver the loop launches" not in d004
    assert "on every suite and increment's own test files the loop launches and on every driver but one under a recorded Decision" in d004
    assert "A test, driver or watch run without the flag still gets the owner's environment; of the launcher's runs of builder-written code, the loop's text leaves the flag off by name for a driver whose suite needs a variable beyond `.env`, under a recorded Decision in `docs/INVENTORY.md` naming the variable." in d004


def test_bug043_every_home_states_what_the_strip_does_not_stop():
    """Review A's B2 and the audit's B1 of the second text, the threat model R-050 asks to be recorded: what a run is handed is withheld; what it can reach on purpose is KP-032's, stated, with the crossing drawn."""
    inventory = flat(read(ROOT, "docs", "INVENTORY.md"))
    assert "The strip withholds what a run is handed, never what it can reach on purpose. That neither the strip nor the loop's text can stop a run writing the checkout's `.git`, so that a later git command runs its program, or asking the credential store, is a stated limit, KP-032's, no blocking finding by itself (R-050)" in inventory
    assert "the act is not the limit: code in a diff that writes the checkout's `.git` (as the guard's row says for a reviewer) or asks the credential store for the owner's login, or a line step 4's check finds, is a gate-integrity flag and a security finding." in inventory
    assert "a check, not a boundary, since a git command of the session or the app may run first." in inventory
    assert "so it holds only what the brief or the inventory names for this increment, or the loop's own step names." in inventory
    assert "a step 4 flag or a diff's test is found in real work" in inventory
    assert "KP-032's deliberate reach, stated here, never blocking" not in inventory
    design = flat(read(ROOT, "docs", "DESIGN.md"))
    assert "a stripped run can still write `.git`, which a later git command of the session runs: step 4 reads it as a check, not a boundary (KP-032)" in design
    d004 = flat(read(ROOT, "docs", "diagrams", "D-004-context-dfd.md"))
    assert "A stripped run can still write `.git`, which a later git command of the session runs: step 4's check, not a boundary (KP-032)." in d004
    assert 'p_test_suite -.->|"UNTRUSTED: a deliberate write, .git config, hooks, which a later git command of the session runs (BUG-043)"| ds_checkout' in d004
    assert 'p_test_suite -.->|"deliberate only"| ext_credential_store' in d004
    assert "| ds_run_outputs | run/agent/\\*.err, run/agent/\\*.out, run/review/REVIEW-nnn.err |" in read(ROOT, "docs", "diagrams", "D-004-context-dfd.md")


def test_bug043_negative_the_own_file_launch_runs_on_the_heavy_launch_rules():
    """An invariant, the rule's `*` already covering `auto --strip`: the form the text now gives runs with no prompt."""
    assert decide(OWN_FILES, ALLOW, DENY)[0] == "allow", OWN_FILES
    assert any(rule_matches(rule, OWN_FILES.split(" > ", 1)[0]) for rule in HEAVY_RULES)


def test_bug043_negative_a_stripped_launch_of_one_test_file_gets_no_account_key(tmp_path):
    """An invariant of the launcher, with no bypass (Review A's C2, the audit's A6: the helper's BRIDGE_RUN_ALLOW_ANY would prove nothing of the form's acceptance): `python -m pytest <file>`, through `--strip --kind test`, runs with the agent home and without an account key of the environment, and the same launch without the flag hands the key over, the test's own precondition (Review A's S4 of the second text). Its value is made up."""
    ws = tmp_path / "Workspace"
    ws.mkdir()
    (ws / "test_key.py").write_text("import os\n\n\ndef test_key():\n    assert 'OTHER_API_KEY' not in os.environ\n", encoding="utf-8")
    (ws / "test_home.py").write_text("import os\n\n\ndef test_home():\n    assert os.path.basename(os.environ['HOME']) == 'agent-home'\n", encoding="utf-8")
    profile = tmp_path / "profile"
    (profile / ".cursor").mkdir(parents=True)
    env = B.env_for(tmp_path, HOME=str(profile), USERPROFILE=str(profile), OTHER_API_KEY="withheld")
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    run = [sys.executable, B.PROG, "--limit", "60", "--strip", "--kind", "test", "--", "python", "-m", "pytest", "-q"]
    p = subprocess.run(run + ["test_key.py", "test_home.py"], capture_output=True, text=True, env=env, cwd=str(ws))
    assert p.returncode == 0, p.stdout + p.stderr
    assert "2 passed" in p.stdout, p.stdout
    run.remove("--strip")
    control = subprocess.run(run + ["test_key.py"], capture_output=True, text=True, env=env, cwd=str(ws))
    assert control.returncode == 1, control.stdout + control.stderr
    assert "1 failed" in control.stdout, control.stdout


def test_bug043_the_design_is_past_the_retrofit():
    """Round 2's records part, S2 and C5: `--mode code` prints no `TESTS` line since TASK-044, and R-052's homes name what its row names."""
    design = flat(read(ROOT, "docs", "DESIGN.md"))
    assert "over the tracked Python today, its thirteen" not in design
    assert "over the tracked Python at the retrofit, its thirteen" in design
    assert "being what the addendum's test increment closed (TASK-044: no `TESTS` line since; R-055)" in design
    assert "`delegation-loop/merge.md` (P7's launch)" in design
    assert "`agents/test-runner.md`" in design
    assert "`intake.md` and `configuration.md` (BUG-042)" in design
