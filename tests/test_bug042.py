"""BUG-042 (stage T2's review, round 1): the conformance check's scanner rows read the gate's workflows, and what the review found behind the text; written by the supervisor; the builder reads and runs them, never edits them.

enforces: docs/debug/BUG-042.md; docs/REQUIREMENTS.md R-052 (the weekly scan is a second workflow, the floor's steps stand in the gate). The weekly file R-052 puts in every project holds an unguarded OSV-Scanner step, and `conformance-check.py` read every workflow as the gate, so that step alone made the row `OSV-Scanner in the gate` read OK. The fixtures are tests/test_conformance_check.py's; the weekly file is this repository's own, the one every project receives.
"""
import ast
import os
import subprocess
import sys

import pytest

import test_bridge_run as B
from test_conformance_check import GATE, make_workspace, run, verdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
BRIDGE = os.path.join(ROOT, "bridge")
ROW = "OSV-Scanner in the gate"
PIN = "OSV-Scanner version pinned"
OSV = "      - name: osv\n        run: osv-scanner@v2.3.1 --lockfile package-lock.json\n"
WEEKLY_HEAD = "on:\n  workflow_dispatch:\njobs:\n  scan:\n    runs-on: ubuntu-latest\n    steps:\n"


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def flat(text):
    return " ".join(text.split())


def weekly():
    return read(ROOT, ".github", "workflows", "dependency-scan.yml")


def workspace(tmp_path, gate):
    make_workspace(tmp_path)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(gate, encoding="utf-8")


def add_weekly(tmp_path):
    (tmp_path / ".github" / "workflows" / "dependency-scan.yml").write_text(weekly(), encoding="utf-8")


def test_bug042_a_gate_with_no_osv_step_stays_missing_beside_the_weekly_file(tmp_path):
    """The reproduction: the row is MISSING with no weekly file (its precondition), and the weekly file changes nothing."""
    assert OSV in GATE
    workspace(tmp_path, GATE.replace(OSV, ""))
    assert verdict(run(tmp_path)[1], ROW)[0] == "MISSING", "the precondition: no weekly file, no OSV step"
    add_weekly(tmp_path)
    assert verdict(run(tmp_path)[1], ROW)[0] == "MISSING"


@pytest.mark.parametrize("name", ["Dependency-Scan.yml", "dependency-scan.yaml"])
def test_bug042_the_weekly_file_is_known_by_its_name_in_either_form(tmp_path, name):
    """The name is compared case-insensitively and either workflow suffix is left out, as `.github/workflows/` reads both."""
    workspace(tmp_path, GATE.replace(OSV, ""))
    (tmp_path / ".github" / "workflows" / name).write_text(weekly(), encoding="utf-8")
    assert verdict(run(tmp_path)[1], ROW)[0] == "MISSING"


def test_bug042_a_guarded_gate_step_stays_missing_beside_the_weekly_file(tmp_path):
    """The reproduction's second case: a floor step skipped by `if:` is still named guarded once the weekly file arrives."""
    workspace(tmp_path, GATE.replace(OSV, OSV.replace("        run:", "        if: ${{ env.SCAN == '1' }}\n        run:")))
    v, line = verdict(run(tmp_path)[1], ROW)
    assert v == "MISSING" and "guarded" in line, "the precondition: " + str(line)
    add_weekly(tmp_path)
    v, line = verdict(run(tmp_path)[1], ROW)
    assert v == "MISSING" and "guarded" in line, line


def test_bug042_an_unpinned_gate_step_keeps_its_note_beside_the_weekly_file(tmp_path):
    """The version NOTE reads the gate's lines too, so the weekly file's pinned download does not answer for the gate's step."""
    workspace(tmp_path, GATE.replace("osv-scanner@v2.3.1", "osv-scanner"))
    assert verdict(run(tmp_path)[1], PIN)[0] == "NOTE", "the precondition"
    add_weekly(tmp_path)
    out = run(tmp_path)[1]
    assert verdict(out, ROW)[0] == "OK" and verdict(out, PIN)[0] == "NOTE", out


def test_bug042_the_weekly_file_alone_is_no_gate(tmp_path):
    """A project holding only the weekly file has no gate: its OSV step answers for nothing."""
    make_workspace(tmp_path)
    (tmp_path / ".github" / "workflows" / "ci.yml").unlink()
    add_weekly(tmp_path)
    out = run(tmp_path)[1]
    assert [verdict(out, "%s in the gate" % name)[0] for name in ("Semgrep", "OSV-Scanner", "Socket")] == ["MISSING"] * 3, out
    assert verdict(out, "CI gate")[0] is None, out


def test_bug042_the_same_steps_under_another_name_are_a_gate(tmp_path):
    """The name is the one thing left out, whole: the weekly text in a file of another name answers the row, and a name that only
    begins with or holds the weekly file's is no weekly file."""
    workspace(tmp_path, GATE.replace(OSV, ""))
    (tmp_path / ".github" / "workflows" / "ci.yml").unlink()
    for name in ("security-scan.yml", "dependency-scan-pr.yml"):
        path = tmp_path / ".github" / "workflows" / name
        path.write_text(weekly(), encoding="utf-8")
        assert verdict(run(tmp_path)[1], ROW)[0] == "OK", name
        path.unlink()


@pytest.mark.parametrize("floor,step", [
    ("Socket runs without its banner", "      - name: scan\n        run: npx socket@1.2.3 ci\n"),
    ("Socket CLI installed without the key",
     "      - name: scan\n        run: npm install -g socket@1.2.3\n        env:\n          SOCKET_CLI_API_TOKEN: ${{ secrets.SOCKET_SECURITY_API_KEY }}\n"),
], ids=["banner", "keyed-install"])
def test_bug042_a_socket_hazard_in_the_weekly_file_still_reads_missing(tmp_path, floor, step):
    """The security audit of round 1: these two rows are no gate floors, they flag a key's exposure in any workflow (ISS-005, FB-007),
    so a step of either form in a file named as the weekly one reads as it does in any other file."""
    workspace(tmp_path, GATE)
    assert verdict(run(tmp_path)[1], floor)[0] is None, "the precondition: the gate holds neither hazard"
    (tmp_path / ".github" / "workflows" / "other.yml").write_text(WEEKLY_HEAD + step, encoding="utf-8")
    assert verdict(run(tmp_path)[1], floor)[0] == "MISSING", "the same step in another file"
    (tmp_path / ".github" / "workflows" / "other.yml").rename(tmp_path / ".github" / "workflows" / "dependency-scan.yml")
    assert verdict(run(tmp_path)[1], floor)[0] == "MISSING"


def test_bug042_negative_a_gate_step_beside_the_weekly_file_is_ok(tmp_path):
    """An invariant: the fix takes nothing from a project whose gate holds the step."""
    workspace(tmp_path, GATE)
    add_weekly(tmp_path)
    out = run(tmp_path)[1]
    assert verdict(out, ROW)[0] == "OK" and verdict(out, PIN)[0] is None, out


def test_bug042_negative_an_action_in_the_weekly_file_still_counts_for_the_pin_row(tmp_path):
    """An invariant: `CI actions pinned by commit` reads every workflow, the weekly file's checkout included, as it did."""
    workspace(tmp_path, GATE)
    (tmp_path / ".github" / "workflows" / "dependency-scan.yml").write_text(
        weekly().replace("actions/checkout@", "actions/checkout@v5 #"), encoding="utf-8")
    v, line = verdict(run(tmp_path)[1], "CI actions pinned by commit")
    assert v == "MISSING" and "actions/checkout@v5" in line, line


def guard_docstrings():
    tree = ast.parse(read(BRIDGE, "cursor-bridge", "review-guard.py"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "snapshot_rewritten")
    return flat(ast.get_docstring(tree)), flat(ast.get_docstring(fn))


def test_bug042_the_guard_s_docstrings_name_the_deleted_snapshot():
    """docs/HARDENING.md, BUG-041's section and stage T2's review (Review A's records and briefs parts): the module's exit lines
    and `snapshot_rewritten` still gave a hash difference alone, though a snapshot deleted with its copy standing exits 1 and
    returns 'rewritten'; the generated command reference carries the module's text."""
    module, fn = guard_docstrings()
    assert "1 = GATE-INTEGRITY (open the flag, condition 4, and an issue; do not merge)" in module
    assert "a snapshot deleted after it was taken, its hash copy standing, is GATE-INTEGRITY" in module
    assert "2 = cannot verify (no snapshot," not in module
    assert "2 = cannot verify (no copy of the snapshot's hash," in module
    assert "from `verify` voids a qualifying Review B launch" in module
    assert "`premerge` voids nothing" in module
    assert "or the file is gone while the copy stands" in fn


def test_bug042_intake_records_the_layout_as_the_core_does():
    """Review A's bridge part, S1: TASK-041 moved the core and the template to relative paths and left intake's sentence, which
    asked every new project to write what rule 54 forbids in a public file."""
    text = flat(read(BRIDGE, "cursor-bridge", "workflow", "phases", "intake.md"))
    assert "record both resolved paths" not in text
    assert ("and record them and the software name in `docs/PROJECT_STATUS.md`, the two on its `Layout:` line, relative to the project "
            "root and never as a computer path (rule 54).") in text


def test_bug042_the_configuration_lists_name_the_weekly_scan():
    """Review A's bridge part, S2: the two lists of what the configuration writes read as closed and named neither item, so a
    project configured after release T had no calibration to bring them."""
    assert "and the weekly dependency scan's workflow beside it (§5c, step 8)." in flat(
        read(BRIDGE, "cursor-bridge", "workflow", "phases", "configuration.md"))
    guide = flat(read(BRIDGE, "cursor-bridge", "Cursor-Project-Configuration.md"))
    assert "write `.github/workflows/dependency-scan.yml` from `cursor-configurator`'s frozen block (§5c, step 8);" in guide


def test_bug042_the_configurator_gitignores_the_boundary_log():
    """Review A's bridge part, S2: T22's line stood in the guide alone, beside the configurator's "Write only the files named"."""
    agent = flat(read(BRIDGE, "agents", "cursor-configurator.md"))
    assert ("Add `docs/BOUNDARY_VIOLATIONS.md` to `.gitignore`: the log holds this computer's absolute paths, so it is read locally "
            "and never committed (rule 54).") in agent


def test_bug042_the_configurator_s_stop_has_a_way_forward():
    """Review A's bridge and ci parts: a floor with other pins, no `--lockfile=` word or no OSV step stopped the configurator with
    no sentence saying what came next, and the first OSV-Scanner release after this one makes that stop the expected one."""
    agent = flat(read(BRIDGE, "agents", "cursor-configurator.md"))
    assert "Stop and report the same where that step names no `--lockfile=` word," in agent
    assert "where any value it gives, its shell quotes aside, holds anything but letters, digits and `.`, `_`, `-`, `/`, `:`," in agent
    assert " where the project has no such step or no GitHub remote," in agent
    assert ("or where a workflow named `dependency-scan`, `.yml` or `.yaml` in any case, already stands and is not this block filled with the floor's list, compared whole.") in agent
    assert ("an increment brings an older floor pin to the block's, gives the floor the step or the word, or moves a lockfile whose value the list refuses, and you write the file after it merges;") in agent
    assert ("a standing file that differs from the block only by an older block's pins or list is replaced whole from the block by an increment;") in agent
    assert ("any other standing file is read by the supervisor and never overwritten unread, an increment of its own renaming or removing it;") in agent
    assert ("a floor pin newer than the block's is never taken back, and the file waits for the bridge release that carries it, the reason "
            "recorded in `docs/INVENTORY.md`;") in agent
    assert "a project with no GitHub remote has nowhere to run the workflow, the reason recorded there too;" in agent
    assert ("a project on GitHub whose gates run locally receives the file, the list, the value check and the OSV-Scanner pin read against its local OSV-Scanner command, there being no checkout pin to compare.") in agent


def test_bug042_the_evaluation_reads_the_list_by_what_it_prints():
    """Review A's bridge part, C1, read here on this repository: `gh workflow list --all` prints the workflow's name,
    `dependency-scan`, never its file, so a reading of the file's name made every configured project `not configured`."""
    text = flat(read(BRIDGE, "commands", "evaluate-reports.md"))
    assert "A list that holds no `dependency-scan.yml`" not in text
    assert "A list that holds no `dependency-scan` names a project that has not received the workflow yet" in text
    assert "name: dependency-scan\n" in weekly(), "the name the list prints"


def test_bug042_the_guide_and_the_evaluation_know_the_stop_s_two_cases():
    """Review A's read of round 2, S3 and S5: R-052's every project has two exceptions since the configurator's stop, and a reader of
    the guide met neither, while the evaluation read a project with no remote as a list it cannot read, a finding every Sunday, and one
    waiting for a newer pin as its calibration's item, which that calibration cannot act on."""
    guide = flat(read(BRIDGE, "cursor-bridge", "Cursor-Project-Configuration.md"))
    assert "Two cases go without it, each with its reason in `docs/INVENTORY.md` (`cursor-configurator`, the stop): a project with no GitHub remote has nowhere to run it, and a floor pin newer than the block's waits for the bridge release that carries the newer pin." in guide
    text = flat(read(BRIDGE, "commands", "evaluate-reports.md"))
    assert "A project with no GitHub remote has no list to read and no alerts: it is written `no remote`, with the reason its inventory records, a finding where it records none, and no run and no alert is read for it." in text
    assert "Where its inventory records that the file waits for the bridge release that carries a newer floor pin, that reason takes the place of the calibration's item." in text


def test_bug042_negative_a_stripped_suite_launch_gets_its_key_file(tmp_path):
    """Review A's tests part, C4: P7's form, `--strip` with `--key-file`, was run by no test. An invariant, the keys being applied
    after the strip: the pull request's variables and a key named like a secret reach the suite, an account key of the
    environment does not, and the home is the agent home. Its values are made up."""
    ws = tmp_path / "Workspace"
    ws.mkdir()
    profile = tmp_path / "profile"
    (profile / ".cursor").mkdir(parents=True)
    keys = tmp_path / "keys.txt"
    keys.write_text("GITHUB_REF=refs/pull/1/merge\nMY_SERVICE_API_KEY=value-never-printed\n", encoding="utf-8")
    code = ("import os; print(os.environ.get('GITHUB_REF'), os.environ.get('MY_SERVICE_API_KEY'), os.environ.get('OTHER_API_KEY'), "
            "os.path.basename(os.environ['HOME']))")
    env = B.env_for(tmp_path, HOME=str(profile), USERPROFILE=str(profile), OTHER_API_KEY="withheld")
    p = subprocess.run([sys.executable, B.PROG, "--limit", "30", "--strip", "--kind", "test", "--key-file", str(keys), "--",
                        sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=str(ws))
    assert p.returncode == 0, p.stderr
    assert p.stdout.split() == ["refs/pull/1/merge", "value-never-printed", "None", "agent-home"], p.stdout
    assert "value-never-printed" not in p.stderr, "names are printed, values never"
    assert "MY_SERVICE_API_KEY" in p.stderr, p.stderr
