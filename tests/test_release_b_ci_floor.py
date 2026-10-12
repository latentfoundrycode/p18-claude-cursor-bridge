"""Release B — TASK-002 (security floor in CI) structural test.

enforces: docs/BUILD_PLAN.md TASK-002 Done when; satisfies R-002.
Supervisor-authored (reviewer-independent). Asserts the committed CI floor:
Semgrep (OSS engine, explicit pinned rulesets, --error, diff-aware), OSV-Scanner,
and Socket run unguarded on ubuntu from a committed requirements.lock, every
action pinned by commit SHA, no secret value, and the floor cannot silently skip
itself (no step- or job-level guard, no `|| true`). Reads committed files only.
"""
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
LOCKFILE = ROOT / "requirements.lock"

SHA40 = re.compile(r"@[0-9a-f]{40}(?:\s|$|#)")
SCANNERS = (
    ("semgrep", re.compile(r"\bsemgrep\b", re.I)),
    ("osv-scanner", re.compile(r"osv-scanner", re.I)),
    ("socket", re.compile(r"\bsocket(?:security)?\b", re.I)),
)
DISABLERS = re.compile(r"\|\|\s*(true|exit\s+0|:)\b")


def _text():
    return WORKFLOW.read_text(encoding="utf-8")


def _data():
    return yaml.safe_load(_text())


def _step_body(step):
    if not isinstance(step, dict):
        return ""
    return "\n".join(str(step.get(k)) for k in ("uses", "run") if step.get(k))


def _ubuntu_jobs(data):
    for name, job in (data.get("jobs") or {}).items():
        if isinstance(job, dict) and str(job.get("runs-on", "")).strip() == "ubuntu-latest":
            yield name, job


def test_r002_workflow_parses():
    """R-002: the workflow is valid YAML with jobs."""
    data = _data()
    assert isinstance(data, dict) and "jobs" in data


def test_r002_three_scanners_unguarded_on_ubuntu():
    """R-002: Semgrep, OSV-Scanner, and Socket each run on ubuntu with no guard that could skip them."""
    data = _data()
    for label, pattern in SCANNERS:
        found = False
        for _name, job in _ubuntu_jobs(data):
            # the job itself must not be conditional or allowed to fail
            assert "if" not in job, f"R-002: scanner job has a job-level if:"
            assert not job.get("continue-on-error"), "R-002: scanner job uses continue-on-error"
            for step in job.get("steps") or []:
                body = _step_body(step)
                if not pattern.search(body):
                    continue
                assert "if" not in step, f"R-002: {label} step is guarded by if:"
                assert not step.get("continue-on-error"), f"R-002: {label} uses continue-on-error"
                assert not DISABLERS.search(body), f"R-002: {label} command disables its own exit status"
                found = True
        assert found, f"R-002: no unguarded {label} step on ubuntu-latest"


def test_r002_semgrep_blocks_with_explicit_rules():
    """R-002: the Semgrep step runs `semgrep scan` with --error and explicit --config rulesets (not a bare/registry-policy run)."""
    data = _data()
    for _name, job in _ubuntu_jobs(data):
        for step in job.get("steps") or []:
            body = _step_body(step)
            if not re.search(r"\bsemgrep\b", body, re.I):
                continue
            assert "scan" in body, "R-002: Semgrep must use `semgrep scan` (deterministic), not `semgrep ci`"
            assert "--error" in body, "R-002: the Semgrep step must pass --error so a finding fails the step"
            assert body.count("--config") >= 2, "R-002: Semgrep must name explicit rulesets via --config"
            assert "bridge/cursor-bridge/semgrep-bridge-rules.yml" in body, "R-002: the bridge rules must be in the Semgrep config"
            return
    raise AssertionError("R-002: no Semgrep step found on ubuntu-latest")


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


def test_r002_pip_installs_only_from_lockfile():
    """R-002: every pip install is exactly `-r requirements.lock` with no extra packages and no direct pytest/pyyaml pins."""
    for line in _text().splitlines():
        if "pip install" not in line:
            continue
        after = line.split("pip install", 1)[1].strip()
        assert after == "-r requirements.lock", f"R-002: pip install must be exactly `-r requirements.lock`: {line!r}"


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


def test_r002_secrets_only_in_step_env_no_values():
    """R-002: repo secrets are referenced only inside step-level env: mappings, never at workflow or job env, and no secret value is embedded."""
    text = _text()
    # no literal-looking secret assignment (a secret reference is always ${{ secrets.NAME }})
    for line in text.splitlines():
        if re.search(r"(SEMGREP_APP_TOKEN|SOCKET_\w*API\w*TOKEN|SOCKET_SECURITY_API_KEY)\s*[:=]", line):
            assert "${{" in line and "secrets." in line, f"R-002: secret not referenced via ${{{{ secrets.* }}}}: {line!r}"
    data = _data()
    workflow_env = str(data.get("env", {}))
    assert "secrets." not in workflow_env, "R-002: a secret is referenced at workflow-level env"
    for name, job in (data.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        assert "secrets." not in str(job.get("env", {})), f"R-002: a secret is referenced at job-level env in {name}"


def test_r002_least_privilege_permissions():
    """R-002: the workflow sets a least-privilege permissions block (contents: read at workflow or security job level)."""
    data = _data()
    top = data.get("permissions")
    if isinstance(top, dict) and top.get("contents") == "read":
        return
    for _name, job in _ubuntu_jobs(data):
        perms = job.get("permissions")
        if isinstance(perms, dict) and perms.get("contents") == "read":
            return
    raise AssertionError("R-002: no least-privilege `permissions: {contents: read}` block on the floor")
