"""Release B — TASK-002 (security floor in CI) structural test.

enforces: docs/BUILD_PLAN.md TASK-002 Done when; satisfies R-002.
Supervisor-authored (reviewer-independent). Asserts the committed CI floor:
Semgrep (OSS engine, no token, explicit rulesets, --error, diff-aware), OSV-Scanner,
and Socket (authenticated by its repo secret) run unguarded on ubuntu from a
committed requirements.lock; every action is pinned by commit SHA; checkouts do not
persist credentials; secrets appear only in step-level env; and the floor cannot
silently skip itself (no step- or job-level guard, no `|| true` / `|| :` / `|| echo`).
Reads committed files only.
"""
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
LOCKFILE = ROOT / "requirements.lock"

SHA40 = re.compile(r"@[0-9a-f]{40}(?:\s|$|#)")
SEMGREP = re.compile(r"\bsemgrep\b", re.I)
OSV = re.compile(r"osv-scanner", re.I)
SOCKET = re.compile(r"\bsocket(?:security)?\b", re.I)
SCANNERS = (("semgrep", SEMGREP), ("osv-scanner", OSV), ("socket", SOCKET))
DISABLERS = re.compile(r"\|\|\s*(?:true\b|exit\s+0\b|:(?=\s|$|;)|echo\b)")


def _text():
    return WORKFLOW.read_text(encoding="utf-8")


def _data():
    return yaml.safe_load(_text())


def _jobs(data):
    return {n: j for n, j in (data.get("jobs") or {}).items() if isinstance(j, dict)}


def _steps(job):
    return [s for s in (job.get("steps") or []) if isinstance(s, dict)]


def _body(step):
    return "\n".join(str(step.get(k)) for k in ("uses", "run") if step.get(k))


def _ubuntu_jobs(data):
    return {n: j for n, j in _jobs(data).items() if str(j.get("runs-on", "")).strip() == "ubuntu-latest"}


def _semgrep_step(data):
    for job in _ubuntu_jobs(data).values():
        for step in _steps(job):
            if SEMGREP.search(_body(step)):
                return step
    raise AssertionError("R-002: no Semgrep step on ubuntu-latest")


def test_r002_disabler_pattern_catches_the_idioms():
    """R-002: the guard this test relies on catches the usual exit-status swallowers (a negative test must show its precondition)."""
    for bad in ("socket ci || true", "socket ci || :", "x || exit 0", "x || echo skipped", "x ||:;"):
        assert DISABLERS.search(bad), bad
    for ok in ("a && b", "set -euo pipefail", "exit \"$code\""):
        assert not DISABLERS.search(ok), ok


def test_r002_workflow_parses():
    """R-002: the workflow is valid YAML with jobs."""
    data = _data()
    assert isinstance(data, dict) and _jobs(data)


def test_r002_three_scanners_unguarded_on_ubuntu():
    """R-002: Semgrep, OSV-Scanner, and Socket each run on ubuntu with no guard that could skip them."""
    data = _data()
    for label, pattern in SCANNERS:
        found = False
        for job in _ubuntu_jobs(data).values():
            for step in _steps(job):
                body = _body(step)
                if not pattern.search(body):
                    continue
                assert "if" not in job, f"R-002: the job running {label} has a job-level if:"
                assert not job.get("continue-on-error"), f"R-002: the job running {label} uses continue-on-error"
                assert "if" not in step, f"R-002: {label} step is guarded by if:"
                assert not step.get("continue-on-error"), f"R-002: {label} step uses continue-on-error"
                assert not DISABLERS.search(body), f"R-002: {label} command swallows its own exit status"
                found = True
        assert found, f"R-002: no unguarded {label} step on ubuntu-latest"


def test_r002_semgrep_not_on_other_runners():
    """R-002: Semgrep runs only on ubuntu (it is unreliable on Windows), never on another runner."""
    data = _data()
    ubuntu = _ubuntu_jobs(data)
    for name, job in _jobs(data).items():
        if name in ubuntu:
            continue
        for step in _steps(job):
            assert not SEMGREP.search(_body(step)), f"R-002: Semgrep runs in non-ubuntu job {name}"


def test_r002_semgrep_oss_blocking_explicit_diff_aware():
    """R-002: Semgrep is a `scan` (OSS, no token, no --pro) with --error, explicit --config rulesets incl. the bridge rules, and diff-aware baselines."""
    step = _semgrep_step(_data())
    body = _body(step)
    assert re.search(r"\(scan\b|\bsemgrep\S*\s+scan\b", body), "R-002: Semgrep must run `scan`, not `ci`"
    assert "--error" in body, "R-002: --error must make a finding fail the step"
    assert body.count("--config") >= 2, "R-002: explicit rulesets via --config"
    assert "bridge/cursor-bridge/semgrep-bridge-rules.yml" in body, "R-002: the bridge rules must be loaded"
    assert "pull_request" in body and "push" in body, "R-002: Semgrep must branch on pull_request and push"
    assert body.count("--baseline-commit") >= 2, "R-002: Semgrep must be diff-aware on both pull_request and push (--baseline-commit on each path)"
    assert "--pro" not in body and "install-semgrep-pro" not in body, "R-002: OSS engine (owner's decision 2026-10-12)"
    assert "SEMGREP_APP_TOKEN" not in _text(), "R-002: no Semgrep token in the workflow (OSS engine)"


def test_r002_every_uses_is_commit_pinned():
    """R-002: every `uses:` names a 40-hex commit SHA, and at least one uses: exists."""
    seen = 0
    for line in _text().splitlines():
        m = re.search(r"^\s*(?:-\s*)?uses:\s*(\S+)", line)
        if not m:
            continue
        seen += 1
        assert SHA40.search(m.group(1) + " "), f"R-002: unpinned uses: {m.group(1)!r}"
    assert seen >= 1, "R-002: no uses: lines found (vacuous pass)"


def test_r002_checkouts_do_not_persist_credentials():
    """R-002: every actions/checkout step sets persist-credentials: false, and at least one exists."""
    seen = 0
    for job in _jobs(_data()).values():
        for step in _steps(job):
            if "actions/checkout" not in str(step.get("uses", "")):
                continue
            seen += 1
            assert (step.get("with") or {}).get("persist-credentials") is False, "R-002: checkout persists credentials"
    assert seen >= 1, "R-002: no checkout step found (vacuous pass)"


def test_r002_pip_installs_only_from_lockfile():
    """R-002: every pip install is exactly `-r requirements.lock`, and at least one exists."""
    seen = 0
    for line in _text().splitlines():
        if "pip install" not in line:
            continue
        seen += 1
        assert line.split("pip install", 1)[1].strip() == "-r requirements.lock", f"R-002: pip install must be exactly `-r requirements.lock`: {line!r}"
    assert seen >= 1, "R-002: no pip install found (vacuous pass)"


def test_r002_lockfile_pins_closure():
    """R-002: requirements.lock pins pytest, pyyaml, and every requirement line with ==."""
    text = LOCKFILE.read_text(encoding="utf-8")
    low = text.lower()
    assert "pytest==9.1.1" in low and "pyyaml==6.0.3" in low
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        assert "==" in s, f"R-002: unpinned requirement line: {s!r}"


def test_r002_secrets_only_in_step_env():
    """R-002: `secrets.` appears only inside a step's env: mapping (never in run/with/uses, job- or workflow-level keys), and Socket is authenticated by its repo secret."""
    data = _data()
    assert "secrets." not in str({k: v for k, v in data.items() if k != "jobs"}), "R-002: secret at workflow level"
    socket_authenticated = False
    for name, job in _jobs(data).items():
        assert "secrets." not in str({k: v for k, v in job.items() if k != "steps"}), f"R-002: secret at job level in {name}"
        for step in _steps(job):
            for key, value in step.items():
                if key == "env":
                    continue
                assert "secrets." not in str(value), f"R-002: secret outside step env ({key}) in {name}"
            if SOCKET.search(_body(step)) and "run" in step:
                socket_authenticated = "secrets.SOCKET_SECURITY_API_KEY" in str(step.get("env") or {})
    assert socket_authenticated, "R-002: the Socket step is not authenticated by secrets.SOCKET_SECURITY_API_KEY in its env"


def test_r002_socket_names_its_organization():
    """R-002: the Socket step names its organization through SOCKET_CLI_ORG_SLUG from the repository variable SOCKET_ORG_SLUG (without it the Socket API answers 404 Organization not found, observed on PR #16)."""
    for job in _ubuntu_jobs(_data()).values():
        for step in _steps(job):
            if SOCKET.search(_body(step)) and "run" in step:
                env = step.get("env") or {}
                value = re.sub(r"\s+", "", str(env.get("SOCKET_CLI_ORG_SLUG", "")))
                assert value == "${{vars.SOCKET_ORG_SLUG}}", "R-002: Socket step must set exactly SOCKET_CLI_ORG_SLUG: ${{ vars.SOCKET_ORG_SLUG }}"
                return
    raise AssertionError("R-002: no Socket step found on ubuntu-latest")


def test_r002_least_privilege_permissions():
    """R-002: a least-privilege `permissions: {contents: read}` block covers the floor."""
    data = _data()
    top = data.get("permissions")
    if isinstance(top, dict) and top.get("contents") == "read":
        return
    for job in _ubuntu_jobs(data).values():
        perms = job.get("permissions")
        if isinstance(perms, dict) and perms.get("contents") == "read":
            return
    raise AssertionError("R-002: no least-privilege `permissions: {contents: read}` block on the floor")
