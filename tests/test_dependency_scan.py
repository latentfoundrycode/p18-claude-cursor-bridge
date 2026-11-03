"""Release T - TASK-042 (the weekly dependency scan in this repository) structural test.

enforces: docs/BUILD_PLAN.md TASK-042 Done when; satisfies R-052, D-004 (`p_dependency_scan`).
Supervisor-authored, written before the workflow file. Asserts the committed workflow: the frozen block of
bridge/agents/cursor-configurator.md with its one fill-in, the security floor's pins and lockfile list, the two triggers
and no other, `contents: read` and nothing else, no secret and no token, and exit-code handling that names every non-zero
exit. Reads committed files only. A `workflow_dispatch` run is the workflow's proof, which GitHub runs only for a file on
the default branch: TASK-044's criterion, not this test's.
"""
import pathlib
import re

import yaml

from test_release_b_ci_floor import DISABLERS, OSV, SECRET_REF, SHA40, _commands, _lines, _on, _steps
from test_release_t_floor import frozen_block

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN = ROOT / ".github" / "workflows" / "dependency-scan.yml"
FLOOR = ROOT / ".github" / "workflows" / "tests.yml"
TOKEN = re.compile(r"\b(?:GITHUB_TOKEN|GH_TOKEN|token)\b", re.I)
LOCKFILE = re.compile(r"--lockfile=(?:'([^']+)'|(\S+))")
VERSION = re.compile(r"osv-scanner/releases/download/(v[0-9.]+)/osv-scanner_linux_amd64")
SHA256 = re.compile(r'echo "([0-9a-f]{64})  osv-scanner" \| sha256sum -c -')
CHECKOUT = re.compile(r"^\s*-\s*uses:\s*actions/checkout@([0-9a-f]{40})", re.M)


def _text(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _data():
    return yaml.safe_load(_text(SCAN))


def _job():
    jobs = _data()["jobs"]
    assert list(jobs) == ["dependency-scan"], "R-052: the workflow holds one job: %s" % list(jobs)
    return jobs["dependency-scan"]


def _scanner_step():
    found = [s for s in _steps(_job()) if any(OSV.search(line) for line in _lines(s))]
    assert len(found) == 1, "R-052: one step runs OSV-Scanner: %s" % found
    return found[0]


def _lockfiles(path):
    return [a or b for a, b in LOCKFILE.findall(_text(path))]


def test_r052_the_file_is_the_frozen_block_with_its_fill_in():
    """R-052, docs/BUILD_PLAN.md TASK-042: the file equals the frozen block but for its one fill-in, the floor's lockfile value."""
    block = frozen_block()
    assert block.count("<fill-in>") == 1, "R-052: the block holds one fill-in"
    assert _text(SCAN) == block.replace("<fill-in>", "requirements.txt:requirements.lock")


def test_r052_the_lockfile_list_is_the_floors():
    """R-052: the `--lockfile=` list equals the floor step's, so the two scans read the same files."""
    listed = _lockfiles(SCAN)
    assert listed == _lockfiles(FLOOR) and listed == ["requirements.txt:requirements.lock"], listed


def test_r052_the_pins_are_the_floors():
    """R-052: the OSV-Scanner version and SHA-256 and the checkout commit equal the floor's, each statement of each pin equal."""
    for pattern in (VERSION, SHA256, CHECKOUT):
        scan, floor = pattern.findall(_text(SCAN)), pattern.findall(_text(FLOOR))
        assert len(scan) == 1, "R-052: %s: %s" % (pattern.pattern, scan)
        assert floor and set(floor) == set(scan), "R-052: %s: %s and %s" % (pattern.pattern, scan, floor)


def test_r052_every_action_is_pinned_by_commit():
    """R-052, rule 14: every `uses:` names a 40-hex commit, and at least one exists."""
    uses = [s["uses"] for s in _steps(_job()) if "uses" in s]
    assert uses, "R-052: no uses: found (vacuous pass)"
    for use in uses:
        assert SHA40.search(use + " "), "R-052: unpinned uses: %r" % use


def test_r052_contents_read_and_nothing_else():
    """R-052: `permissions:` holds `contents: read` and nothing else, and no job widens it."""
    data = _data()
    assert data["permissions"] == {"contents": "read"}, data["permissions"]
    assert "permissions" not in _job(), "R-052: a job carries its own permissions"


def test_r052_the_two_triggers_and_no_other():
    """R-052, D-004: the schedule `17 6 * * 0` and `workflow_dispatch`, so it runs on no pull-request or push event."""
    on = _on(_data())
    assert sorted(on) == ["schedule", "workflow_dispatch"], sorted(on)
    assert on["schedule"] == [{"cron": "17 6 * * 0"}], on["schedule"]
    assert on["workflow_dispatch"] is None, on["workflow_dispatch"]


def test_r052_the_checkout_keeps_no_credentials():
    """R-052, D-004: the checkout sets `persist-credentials: false`."""
    checkouts = [s for s in _steps(_job()) if "actions/checkout" in str(s.get("uses", ""))]
    assert len(checkouts) == 1, checkouts
    assert checkouts[0]["with"] == {"persist-credentials": False}, checkouts[0]["with"]


def test_r052_no_secret_and_no_token():
    """R-052, D-004: no `secrets.` reference, no `GITHUB_TOKEN` and no token handed to a step, at any level."""
    assert not SECRET_REF.search(_text(SCAN)), "R-052: the workflow reads a secret or the job's token"
    assert not TOKEN.search(_text(SCAN)), "R-052: the workflow names a token"
    assert "${{" not in _text(SCAN), "R-052: an expression can carry the job's token or an event field into the run"
    data = _data()
    assert "env" not in data and "env" not in _job(), "R-052: an env above the step"
    for step in _steps(_job()):
        assert "env" not in step, "R-052: a step carries an env: %s" % step


def test_r052_no_patterns_catch_their_forms():
    """R-052 (a negative test must show its precondition): the token pattern and the exit-swallowers it relies on match."""
    for bad in ("GITHUB_TOKEN: x", "token: ${{ x }}", "GH_TOKEN=x"):
        assert TOKEN.search(bad), bad
    assert not TOKEN.search("requirements.txt:requirements.lock")
    for bad in ("x || true", "x; exit 0"):
        assert DISABLERS.search(bad), bad


def test_r052_a_finding_fails_the_run_and_every_exit_is_named():
    """R-052, KP-005: the status is taken at once, `exit 0` stands only under the clean-status branch, the
    `dependency-scan: OSV-Scanner exit` line prints on every non-zero exit before the branch for 128, and the step ends
    with `exit "$code"`, so the evaluation reads the exit from the log and silence is not green."""
    lines = _lines(_scanner_step())
    call = next(i for i, s in enumerate(lines) if s.startswith("./osv-scanner scan source"))
    assert lines[call - 1] == "set +e" and lines[call + 1] == "code=$?" and lines[call + 2] == "set -e", lines
    clean = lines.index('if [ "$code" -eq 0 ]; then')
    assert clean == call + 3, "R-052: the clean branch reads the scanner's own status, nothing changing it between"
    assert lines[clean + 1:clean + 3] == ["exit 0", "fi"], lines
    assert [i for i, s in enumerate(lines) if s == "exit 0"] == [clean + 1], "R-052: exit 0 outside the clean-status branch"
    named = lines.index('echo "dependency-scan: OSV-Scanner exit $code"')
    assert named == clean + 3, "R-052: the exit line prints on every non-zero exit, straight after the clean branch"
    assert lines[-1] == 'exit "$code"', lines
    assert lines[named + 1:-1] == ['if [ "$code" -eq 128 ]; then', 'echo "OSV-Scanner exit 128: no lockfile was read"', "fi"], lines


def test_r052_the_scanner_is_checked_before_it_runs_and_cannot_be_skipped():
    """R-052: the two steps alone, the binary checked by its SHA-256 before it runs under bash, whose `-e` stops the step on a
    mismatch, with no guard, `continue-on-error`, trap or exit-swallower, and the scanner's call chained to nothing."""
    job, step = _job(), _scanner_step()
    assert len(_steps(job)) == 2, "R-052: the checkout and the scanner, and no other step"
    assert step["shell"] == "bash", step["shell"]
    lines = _lines(step)
    scan = next(s for s in lines if s.startswith("./osv-scanner"))
    assert lines.index(next(s for s in lines if "sha256sum -c -" in s)) < lines.index(scan), lines
    assert len(_commands(scan)) == 1, "R-052: the scanner's call is chained: %r" % scan
    for holder in (job, step):
        assert "if" not in holder and not holder.get("continue-on-error"), holder
    assert job["runs-on"] == "ubuntu-latest", job["runs-on"]
    for line in lines:
        assert not DISABLERS.search(line), line
        assert not line.startswith("trap"), line
        assert len(_commands(line)) <= 2, "R-052: a chained command: %r" % line
