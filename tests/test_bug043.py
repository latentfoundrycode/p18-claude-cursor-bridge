"""BUG-043 (stage T2's review, round 2): the increment's own test files run stripped, and the claim says what the launches do; written by the supervisor.

enforces: docs/debug/BUG-043.md; docs/REQUIREMENTS.md R-052 (the loop's launches run stripped); docs/diagrams/D-004-context-dfd.md, the note "Stripped environment". The loop's step 4 said code the builder wrote never runs with the owner's login, six lines above a sentence letting the first run of that code, the increment's own test files, run in the foreground with the owner's whole environment. The round's records findings are held here too: R-042's `P2:` entry, which TASK-045's stamp test reads, and the design past the retrofit.
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
             "<the increment's test files>")
OLD_CLAIM = "never runs in the loop"
LIMITS = ("a reviewer's or auditor's own run beside its reading, after it has read the diff; a build `test-runner` runs; "
          "a stage demonstration's start of the product")


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
    assert "A run of the increment's own test files alone goes through the launcher stripped too, since it is the first run of code nobody has read (`" + OWN_FILES + "`)" in text
    assert "A run of the increment's own test files alone may run in the foreground" not in text
    assert "any wait for the slot included (KP-061); a longer one runs in the background like a suite." in text


def test_bug043_the_test_runner_runs_them_through_the_launcher():
    text = flat(read(BRIDGE, "agents", "test-runner.md"))
    assert "you may run the increment's own test files alone in the foreground." not in text
    assert "The increment's own test files alone you run in the foreground through the launcher, stripped, since it is the first run of code nobody has read: `" + OWN_FILES + "` (D-004, R-052)." in text
    assert "Its wait for the computer's one slot counts against your ten minutes" in text


def test_bug043_the_claim_says_what_the_launches_do():
    assert OLD_CLAIM not in loop()
    assert "no launch of the loop hands code the builder wrote the owner's login or secret-like variables (D-004, R-052)" in loop()
    design = flat(read(ROOT, "docs", "DESIGN.md"))
    assert "builder-written code never runs in the loop" not in design
    assert "no launch of the loop hands builder-written code the owner's secret-like variables and login" in design


def test_bug043_every_home_states_the_limits():
    """What stays in a session's own environment is stated where the claim stands, so an auditor reading every crossing of D-004 is told it exists."""
    assert "Three runs stay in a session's own environment, stated limits (`docs/INVENTORY.md`, Decisions; D-004): " + LIMITS + "." in loop()
    assert LIMITS in flat(read(ROOT, "docs", "DESIGN.md"))
    d004 = flat(read(ROOT, "docs", "diagrams", "D-004-context-dfd.md"))
    assert LIMITS in d004
    assert 'ds_checkout -->|"UNTRUSTED: code and tests the builder wrote, run in the session\'s own environment: stated limits (BUG-043)"| p_supervisor' in d004
    assert "the increment's own test files with them (BUG-043)" in d004
    inventory = flat(read(ROOT, "docs", "INVENTORY.md"))
    assert "| The strip covers the loop's launches through the launcher, not every run of builder-written code:" in inventory
    assert LIMITS in inventory
    assert "the increment's own test files run stripped too (BUG-043;" in flat(row("R-052"))


def test_bug043_negative_the_own_file_launch_runs_on_the_heavy_launch_rules():
    """An invariant, the rule's `*` already covering `auto --strip`: the form the text now gives runs with no prompt."""
    assert decide(OWN_FILES, ALLOW, DENY)[0] == "allow", OWN_FILES
    assert any(rule_matches(rule, OWN_FILES) for rule in HEAVY_RULES)


def test_bug043_negative_a_stripped_launch_of_one_test_file_gets_no_account_key(tmp_path):
    """An invariant of the launcher: one test file, through `--strip --kind test`, runs with the agent home and without an account key of the environment. Its value is made up."""
    ws = tmp_path / "Workspace"
    ws.mkdir()
    (ws / "test_one.py").write_text("import os\n\n\ndef test_one():\n    assert 'OTHER_API_KEY' not in os.environ\n    assert os.path.basename(os.environ['HOME']) == 'agent-home'\n", encoding="utf-8")
    profile = tmp_path / "profile"
    (profile / ".cursor").mkdir(parents=True)
    env = B.env_for(tmp_path, HOME=str(profile), USERPROFILE=str(profile), OTHER_API_KEY="withheld")
    p = subprocess.run([sys.executable, B.PROG, "--limit", "60", "--strip", "--kind", "test", "--", sys.executable, "-m", "pytest", "-q",
                        "-p", "no:cacheprovider", "test_one.py"], capture_output=True, text=True, env=env, cwd=str(ws))
    assert p.returncode == 0, p.stdout + p.stderr


def test_bug043_r042_names_its_p2_entry():
    """Round 2's records part, S1: the plan's grammar reads `(P2, the by-class line of 2026-10-27)` as label P2, and TASK-045's stamp test asks a `<label>: <test>` entry for it."""
    evidence = row("R-042").rstrip(" |").split(" | ")[-1]
    assert "P2: tests/test_loop_text_pace.py::test_bug033_a_late_finding_two_reviewers_name_blocks_only_of_the_five_in_every_home" in evidence


def test_bug043_the_design_is_past_the_retrofit():
    """Round 2's records part, S2 and C5: `--mode code` prints no `TESTS` line since TASK-044, and R-052's homes name what its row names."""
    design = flat(read(ROOT, "docs", "DESIGN.md"))
    assert "over the tracked Python today, its thirteen" not in design
    assert "over the tracked Python at the retrofit, its thirteen" in design
    assert "being what the addendum's test increment closed (TASK-044: no `TESTS` line since; R-055)" in design
    assert "`delegation-loop/merge.md` (P7's launch)" in design
    assert "`agents/test-runner.md`" in design
    assert "`intake.md` and `configuration.md` (BUG-042)" in design


def test_bug043_the_inventory_keeps_the_trace_series():
    """Round 2's records part, C4: the series names the last move of the count tests/test_core_carve.py pins."""
    inventory = read(ROOT, "docs", "INVENTORY.md")
    assert inventory.count("79 since BUG-042") == 2
