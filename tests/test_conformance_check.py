"""conformance-check.py (review R4; 0b review finding 6): a conformant workspace passes; each
missing floor is reported; a guarded scanner step, public-ruleset Semgrep, a design under
other names, a CLI reference checked by a test, local service passwords and private memory
notes are judged as the review asked; secret values are never printed; nothing is written."""
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "conformance-check.py")
VERSION = open(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "VERSION"), encoding="utf-8").read().strip()

GATE = """name: gate
on: [pull_request]
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09
      - name: semgrep
        run: pipx run semgrep==1.176.1 ci
      - name: osv
        run: osv-scanner@v2.3.1 --lockfile package-lock.json
      - name: socket
        run: npx socket@1.2.3 ci
      - run: npx impeccable@3.3.0 detect --json docs/mockups
      - run: pytest -q
"""


INVENTORY = """# Inventory — Thing
Reflected through: none
Updated: 2026-10-06

## Features
| Feature | What it does | Where | Tests | Since |
|---|---|---|---|---|
| Search | finds things | app/search.py | tests/test_search.py | TASK-001 |

## Resources
| Name | Kind | Where it lives | Used by | Provided |
|---|---|---|---|---|
| OPENROUTER_API_KEY | secret | key file outside the Workspace; limit $20/month, set 2026-10-06 | app/llm.py | 2026-10-01 |
| BFL_API_KEY | secret | key file outside the Workspace; limit $5/month, set 2026-10-06 | app/bfl.py | 2026-10-01 |
| Socket account | account | the owner's Socket login; no spend possible | CI | 2026-09-01 |

## Decisions
| Decision | Reason | Settled | Revisit only if |
|---|---|---|---|
| Development data: a development build reads `data/dev.sqlite`, chosen by the `APP_ENV=dev` marker, and refuses the installed product's store | two live databases were upgraded by development builds | 2026-10-06, owner | the product gains a second store |

## Deferred
| Item | Why deferred | Since | Owner decision needed |
|---|---|---|---|
"""


def make_workspace(root, conformant=True):
    (root / "docs" / "diagrams").mkdir(parents=True)
    (root / "docs" / "mockups").mkdir()
    (root / ".cursor" / "rules").mkdir(parents=True)
    (root / ".github" / "workflows").mkdir(parents=True)
    for name in ("PROJECT_STATUS.md", "INVENTORY.md", "REQUIREMENTS.md", "RUN_PARAMETERS.md", "ROSTER.json", "DESIGN.md"):
        (root / "docs" / name).write_text("x\n", encoding="utf-8")
    (root / "docs" / "INVENTORY.md").write_text(INVENTORY, encoding="utf-8")
    (root / "docs" / "PROJECT_STATUS.md").write_text("# Project Status\nBridge version: %s\nPhase: building\n" % VERSION, encoding="utf-8")
    (root / "docs" / "diagrams" / "INDEX.md").write_text("# Diagrams\n", encoding="utf-8")
    (root / ".cursor" / "rules" / "workspace-boundary.mdc").write_text("rule\n", encoding="utf-8")
    (root / ".cursor" / "rules" / "secure-coding.mdc").write_text("rule\n", encoding="utf-8")
    (root / ".cursor" / "hooks.json").write_text('{"hooks": ["boundary-check.py", "windowless-check.py"]}', encoding="utf-8")
    (root / "package.json").write_text("{}", encoding="utf-8")
    (root / "package-lock.json").write_text("{}", encoding="utf-8")
    (root / ".github" / "workflows" / "ci.yml").write_text(GATE, encoding="utf-8")
    (root / ".env").write_text("DATABASE_URL=postgres://localhost/x\nLOG_LEVEL=debug\n", encoding="utf-8")
    if not conformant:
        (root / ".github" / "workflows" / "ci.yml").write_text(GATE.replace("pipx run semgrep==1.176.1 ci", "echo no").replace("@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09", "@v5").replace("ubuntu-latest", "windows-latest"), encoding="utf-8")
        (root / "docs" / "diagrams" / "INDEX.md").unlink()
        (root / ".cursor" / "rules" / "secure-coding.mdc").unlink()
        (root / ".cursor" / "hooks.json").write_text('{"hooks": ["boundary-check.py"]}', encoding="utf-8")
        (root / ".env").write_text("DATABASE_URL=x\nMODAL_TOKEN_SECRET=abc123\nexport OPENROUTER_API_KEY=sk-live-999\n", encoding="utf-8")
        (root / "docs" / "PROJECT_STATUS.md").write_text("Bridge version: 2026.09.27c\nPhase: building\n", encoding="utf-8")


def run(root, *extra, home=None):
    env = dict(os.environ)
    if home:
        env.update(HOME=str(home), USERPROFILE=str(home))
    p = subprocess.run([sys.executable, PROG, str(root), "--offline"] + list(extra), capture_output=True, text=True, env=env)
    return p.returncode, p.stdout


def verdict(out, floor):
    for line in out.splitlines():
        m = re.match(r"\s+(OK|MISSING|NOTE)\s+(.*)$", line)
        if m and m.group(2).startswith(floor):
            return m.group(1), m.group(2)
    return None, None


def test_a_conformant_workspace_passes_from_workspace_and_from_root(tmp_path):
    root = tmp_path / "proj"
    make_workspace(root / "Workspace")
    for start in (root / "Workspace", root):
        rc, out = run(start)
        assert rc == 0 and "RESULT: CONFORMANT" in out, out
        assert "0 MISSING" in out and "  MISSING" not in out
    assert verdict(out, "Semgrep bridge rules or Pro engine")[0] == "OK"
    assert verdict(out, "Windowless check")[0] == "OK"
    assert verdict(out, "Required check on the default branch")[0] == "NOTE"      # --offline


def test_each_missing_floor_is_named_and_secret_values_never_printed(tmp_path):
    make_workspace(tmp_path, conformant=False)
    rc, out = run(tmp_path)
    assert rc == 1, out
    for floor in ("Semgrep in the gate", "CI actions pinned by commit", "Secure-coding rule", "Windowless check", "docs/diagrams/INDEX.md",
                  "Keys out of the builder's reach", "Calibrated to the installed bridge"):
        assert verdict(out, floor)[0] == "MISSING", floor
    assert verdict(out, "Runner OS")[0] == "NOTE"
    assert "MODAL_TOKEN_SECRET" in out and "OPENROUTER_API_KEY" in out
    assert "abc123" not in out and "sk-live-999" not in out, "values must never be printed"
    assert "DATABASE_URL" not in verdict(out, "Keys out of the builder's reach")[1]
    assert verdict(out, "OSV-Scanner in the gate")[0] == "OK", "OSV is present in the fixture"


def test_guarded_scanner_step_and_public_rulesets_are_not_a_floor(tmp_path):
    make_workspace(tmp_path)
    gate = GATE.replace("      - name: socket\n        run: npx socket@1.2.3 ci\n",
                        "      - name: socket\n        if: ${{ env.SOCKET_TOKEN != '' }}\n        run: npx socket@1.2.3 ci\n")
    gate = gate.replace("pipx run semgrep==1.176.1 ci", "pipx run semgrep==1.176.1 --config p/default --config p/owasp-top-ten")
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(gate, encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "Socket in the gate")
    assert v == "MISSING" and "guarded" in line, line
    assert verdict(out, "Semgrep in the gate")[0] == "OK"
    v, line = verdict(out, "Semgrep bridge rules or Pro engine")
    assert v == "MISSING" and "public rulesets" in line
    assert verdict(out, "OSV-Scanner in the gate")[0] == "OK"


def test_unpinned_scanner_version_is_a_note(tmp_path):
    make_workspace(tmp_path)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(GATE.replace("osv-scanner@v2.3.1", "osv-scanner"), encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "OSV-Scanner version pinned")[0] == "NOTE"
    assert verdict(out, "Semgrep version pinned")[0] is None


def test_cli_reference_checked_by_a_test_counts(tmp_path):
    make_workspace(tmp_path)
    (tmp_path / "docs" / "cli-reference.json").write_text("{}", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "CLI reference checked")[0] == "MISSING"
    (tmp_path / "backend" / "tests").mkdir(parents=True)
    (tmp_path / "backend" / "tests" / "test_cli.py").write_text('def test_reads():\n    data = open("docs/cli-reference.json").read()\n    assert data\n', encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "CLI reference checked")
    assert v == "MISSING" and "backend/tests/test_cli.py reads" in line, "S9: a test that only reads the file is not a check"
    (tmp_path / "backend" / "tests" / "test_cli_ref.py").write_text('def test_ref():\n    assert open("docs/cli-reference.json").read() == generate()\n', encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "CLI reference checked")
    assert v == "OK" and "backend/tests/test_cli_ref.py" in line


def test_local_service_passwords_are_a_note_and_env_variants_are_read(tmp_path):
    make_workspace(tmp_path)
    (tmp_path / ".env").write_text("POSTGRES_PASSWORD=pw1\nMINIO_ROOT_PASSWORD=pw2\nREDIS_PASSWORD=pw3\n", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Keys out of the builder's reach")[0] == "OK"
    v, line = verdict(out, "Local service passwords in .env")
    assert v == "NOTE" and "POSTGRES_PASSWORD" in line and "pw1" not in out
    (tmp_path / ".env.local").write_text("HF_TOKEN=hf_secret\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("ANTHROPIC_API_KEY=\n", encoding="utf-8")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / ".env").write_text("STRIPE_SECRET_KEY=sk\n", encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "Keys out of the builder's reach")
    assert v == "MISSING" and "HF_TOKEN (.env.local)" in line and "STRIPE_SECRET_KEY (backend/.env)" in line
    assert "ANTHROPIC_API_KEY" not in line and "hf_secret" not in out


def test_design_under_other_names_is_a_note(tmp_path):
    make_workspace(tmp_path)
    (tmp_path / "docs" / "DESIGN.md").unlink()
    (tmp_path / "docs" / "SFVF_Architecture.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "docs" / "DESIGN-grants.md").write_text("x\n", encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "docs/DESIGN.md")
    assert v == "NOTE" and "SFVF_Architecture.md" in line and "DESIGN-grants.md" in line
    (tmp_path / "docs" / "SFVF_Architecture.md").unlink()
    (tmp_path / "docs" / "DESIGN-grants.md").unlink()
    rc, out = run(tmp_path)
    assert verdict(out, "docs/DESIGN.md")[0] == "MISSING"


def test_requirements_txt_needs_a_transitive_lock_and_editable_subprojects_fold_into_it(tmp_path):
    make_workspace(tmp_path)
    (tmp_path / "requirements.txt").write_text("requests==2.32.0\nclick==8.1.7\n-e ./sdk\n", encoding="utf-8")
    (tmp_path / "sdk").mkdir()
    (tmp_path / "sdk" / "pyproject.toml").write_text("[project]\nname='sdk'\n", encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "Transitive lock for requirements.txt")
    assert v == "MISSING" and "2 direct dependencies" in line
    assert verdict(out, "Lockfile for sdk/pyproject.toml")[0] is None, "the editable sub-project is covered by the root's lock"
    (tmp_path / "uv.lock").write_text("", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Transitive lock for requirements.txt")[0] == "OK"


def test_private_memory_notes_are_listed_by_name(tmp_path):
    root = tmp_path / "proj"
    make_workspace(root / "Workspace")
    home = tmp_path / "home"
    encoded = re.sub(r"[:\\/]", "-", str(root))
    mem = home / ".claude" / "projects" / encoded / "memory"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text("- index\n", encoding="utf-8")
    (mem / "tdp-supervisor-workflow.md").write_text("The /supervisor operating contract...\n", encoding="utf-8")
    rc, out = run(root, home=home)
    v, line = verdict(out, "Private memory notes")
    assert v == "NOTE" and "tdp-supervisor-workflow.md" in line and "1 note(s)" in line and "operating contract" not in out


def test_not_a_workspace(tmp_path):
    rc, out = run(tmp_path / "nothing")
    assert rc == 2


def test_writes_nothing(tmp_path):
    make_workspace(tmp_path, conformant=False)
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    run(tmp_path)
    after = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    assert before == after


def test_second_pass_residue(tmp_path):
    """S9: a version in the install step's download URL counts as pinned; a scanner step
    that guards itself in its script is a note; the product's own token is not an account
    key. S3: a gitignored record is MISSING."""
    make_workspace(tmp_path)
    gate = GATE.replace("      - name: osv\n        run: osv-scanner@v2.3.1 --lockfile package-lock.json\n",
                        "      - name: get osv\n        run: curl -L https://github.com/google/osv-scanner/releases/download/v2.6.0/osv-scanner_linux_amd64 -o osv-scanner\n"
                        "      - name: osv\n        run: ./osv-scanner --lockfile package-lock.json\n")
    gate = gate.replace("npx socket@1.2.3 ci", 'if [ -n "${SOCKET_CLI_API_TOKEN}" ]; then npx socket@1.2.3 ci; else echo skipping; fi')
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(gate, encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "OSV-Scanner in the gate")[0] == "OK" and verdict(out, "OSV-Scanner version pinned")[0] is None
    assert verdict(out, "Socket in the gate")[0] == "OK" and verdict(out, "Socket step guards itself")[0] == "NOTE"
    proj = tmp_path / "ck04-reangle-prototype"
    make_workspace(proj / "Workspace")
    (proj / "Workspace" / ".env").write_text("REANGLE_API_TOKEN=abc\nHF_TOKEN=hf\n", encoding="utf-8")
    rc, out = run(proj / "Workspace")
    v, line = verdict(out, "Keys out of the builder's reach")
    assert v == "MISSING" and "HF_TOKEN" in line and "REANGLE_API_TOKEN" not in line
    assert verdict(out, "The product's own tokens in .env")[0] == "NOTE"
    subprocess.run(["git", "init", "-q"], cwd=proj / "Workspace", check=True)
    (proj / "Workspace" / ".gitignore").write_text("docs/RUN_PARAMETERS.md\n", encoding="utf-8")
    rc, out = run(proj / "Workspace")
    v, line = verdict(out, "docs/RUN_PARAMETERS.md")
    assert v == "MISSING" and "gitignored" in line


def test_key_advice_and_the_environment_note(tmp_path):
    """2026.10.04e: the advice names a key file outside the Workspace, never the user
    environment; key-like variables in the session's environment are a NOTE, names only."""
    make_workspace(tmp_path, conformant=False)
    env = dict(os.environ, HF_TOKEN="hf_value_never_printed", TOKENIZERS_PARALLELISM="false")
    p = subprocess.run([sys.executable, PROG, str(tmp_path), "--offline"], capture_output=True, text=True, env=env)
    out = p.stdout
    v, line = verdict(out, "Keys out of the builder's reach")
    assert v == "MISSING" and "OUTSIDE the Workspace" in line and "NOT into the Windows user environment" in line
    v, line = verdict(out, "Account keys in the session's environment")
    assert v == "NOTE" and "HF_TOKEN" in line and "TOKENIZERS_PARALLELISM" not in line
    assert "hf_value_never_printed" not in out


def test_a_secret_supplied_through_an_environment_variable_is_a_missing_floor(tmp_path):
    """The owner, 2026-10-05: no secret through an environment variable the owner sets. The
    inventory says how each resource arrives; a passphrase is a secret, a path is not."""
    make_workspace(tmp_path)
    (tmp_path / "docs" / "INVENTORY.md").write_text(
        "## Resources\n"
        "| Name | Kind | Where | Used by | Since |\n|---|---|---|---|---|\n"
        "| SFVF_DATA_DIR | env var | user env var / installer | app/paths.py | owner |\n"
        "| SFVF_SECRETS_PATH SFVF_SECRETS_PASSPHRASE | env var | user env var | app.core.secrets | owner |\n"
        "| SFVF_MARKER_KEEP | test-only env var | tests | test | n/a |\n"
        "| OPENROUTER_API_KEY | secret | the app's encrypted store | workflows | 2026-10-04 |\n", encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "No secret through an environment variable")
    assert v == "MISSING" and "SFVF_SECRETS_PASSPHRASE" in line
    assert "SFVF_SECRETS_PATH" not in line and "SFVF_DATA_DIR" not in line and "OPENROUTER_API_KEY" not in line
    (tmp_path / "docs" / "INVENTORY.md").write_text(
        "| OPENROUTER_API_KEY | secret | key file outside the Workspace | workflows | 2026-10-04 |\n", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "No secret through an environment variable")[0] == "OK"


def test_claude_code_hooks_in_the_projects_settings_are_a_missing_floor(tmp_path):
    """Review of 2026.10.06a, finding 6: cursor-agent imports a project's .claude hooks and
    plugins as it imports the user's (KP-038)."""
    make_workspace(tmp_path)
    rc, out = run(tmp_path)
    assert "No Claude Code hooks in the project's .claude" not in out
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.local.json").write_text('{"permissions": {"allow": ["Bash(ls:*)"]}}', encoding="utf-8")
    rc, out = run(tmp_path)
    assert "No Claude Code hooks in the project's .claude" not in out, "permissions alone are not imported as hooks"
    (tmp_path / ".claude" / "settings.json").write_text('{"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python guard.py"}]}]}}', encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "No Claude Code hooks in the project's .claude")[0] == "MISSING" and ".claude/settings.json (hooks)" in out, out
    (tmp_path / ".claude" / "settings.json").write_text('{"enabledPlugins": {"x@y": true}}', encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "No Claude Code hooks in the project's .claude")[0] == "MISSING" and "(enabledPlugins)" in out, out
    (tmp_path / ".claude" / "settings.json").write_text('{"enabledPlugins": {"x@y": false}}', encoding="utf-8")
    rc, out = run(tmp_path)
    assert "No Claude Code hooks in the project's .claude" not in out, "a plugin listed as disabled is not imported"
    (tmp_path / ".claude" / "settings.json").unlink()
    root = tmp_path.parent / (tmp_path.name + "-project")
    (root / "Workspace").mkdir(parents=True)
    import shutil
    for item in tmp_path.iterdir():
        shutil.move(str(item), str(root / "Workspace" / item.name))
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text('{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "x"}]}]}}', encoding="utf-8")
    rc, out = run(root / "Workspace")
    assert verdict(out, "No Claude Code hooks in the project's .claude")[0] == "NOTE" and "../.claude/settings.json (hooks)" in out, "the root's .claude is read only when a builder's workspace is the root: " + out


def test_the_three_floors_of_release_a1b(tmp_path):
    """A paid provider without a recorded limit, no development-data decision, and an
    adapter of an external service without recorded replies are each reported."""
    make_workspace(tmp_path)
    rc, out = run(tmp_path)
    assert verdict(out, "Spending limit recorded")[0] == "OK" and verdict(out, "Development data kept apart")[0] == "OK", out
    assert verdict(out, "Adapters tested against recorded replies")[0] is None, "no adapter, nothing to say"
    inv = (tmp_path / "docs" / "INVENTORY.md").read_text(encoding="utf-8")
    (tmp_path / "docs" / "INVENTORY.md").write_text(inv.replace("; limit $20/month, set 2026-10-06", "; a rate limit of 60/min").replace("Development data: a development build", "Data: a development build")
                                                     .replace("| CI | 2026-09-01 |\n", "| CI | 2026-09-01 |\n"
                                                              + "| POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD | secret | generated per instance for the local Postgres | tests | n/a |\n"
                                                              + "| AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY | secret | the MinIO login, generated per instance | app | n/a |\n"
                                                              + "| THING_API_TOKEN | secret | the product's own per-instance token | app | n/a |\n"
                                                              + "| OpenRouter (rule judge) | external API | key file; limit $10/month, set 2026-10-06 | app | 2026-10-01 |\n"
                                                              + "| HF_TOKEN | repo secret | GitHub secret | CI | 2026-10-01 |\n"
                                                              + "| ANTHROPIC_API_KEY | secret | key file; spending limit not set yet | app | 2026-10-01 |\n"
                                                              + "| SMPL-X model files (MPI account) | account | downloaded once with the MPI login | assets | 2026-09-01 |\n"
                                                              + "| Claude Code MCP registration | registration | the owner's Claude Code settings | tooling | 2026-09-01 |\n"), encoding="utf-8")
    rc, out = run(tmp_path)
    kind, detail = verdict(out, "Spending limit recorded")
    assert kind == "MISSING" and "OPENROUTER_API_KEY" in detail and "HF_TOKEN" in detail and "ANTHROPIC_API_KEY" in detail and "3 key" in detail, out
    for name in ("POSTGRES", "AWS_", "THING_API_TOKEN", "Socket", "OpenRouter (rule judge)", "SMPL", "MCP", "BFL"):
        assert name not in detail, "local logins (every name in the cell), per-instance values, the product's own tokens, no-spend accounts, limited rows, model files and registrations are not reported: " + detail
    assert verdict(out, "Development data kept apart")[0] == "MISSING", out
    (tmp_path / "docs" / "INVENTORY.md").write_text(inv.replace("| Development data: a development build", "| **`Development data:`** a development build"), encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Development data kept apart")[0] == "OK", "a bold or backticked row counts: " + out
    (tmp_path / "docs" / "INVENTORY.md").write_text(inv, encoding="utf-8")
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "run/ ignored")[0] == "NOTE", out
    (tmp_path / ".gitignore").write_text("node_modules/\nrun/\n", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "run/ ignored")[0] is None, out
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "llm.py").write_text('import httpx2\nURL = "https://openrouter.ai/api/v1"\n\ndef ask(q):\n    return httpx2.get(URL)\n', encoding="utf-8")
    (tmp_path / "app" / "store.py").write_text('import boto3\n\nclient = boto3.client("s3", endpoint_url="http://localhost:9000")  # the local MinIO store\n', encoding="utf-8")
    (tmp_path / "venvs" / "x" / "Lib" / "site-packages" / "aiohttp").mkdir(parents=True)
    (tmp_path / "venvs" / "x" / "Lib" / "site-packages" / "aiohttp" / "client.py").write_text('import aiohttp\nURL = "https://openrouter.ai"\n', encoding="utf-8")
    (tmp_path / "venvs" / "x" / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
    rc, out = run(tmp_path)
    kind, detail = verdict(out, "Adapters tested against recorded replies")
    assert kind == "MISSING" and "llm" in detail and "client" not in detail and "store" not in detail, "library code in an environment and a local store's client are not adapters of a listed provider: " + out
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_other.py").write_text("def test_x():\n    assert True  # replays recorded replies\n", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Adapters tested against recorded replies")[0] == "MISSING", "a recorded word in an unrelated test proves nothing for llm: " + out
    (tmp_path / "tests" / "test_llm.py").write_text('import httpx2\nfrom app import llm\n\n\ndef test_frozen_contract():\n    transport = httpx2.MockTransport(lambda r: httpx2.Response(200, json={"id": 1}))  # recorded replies, cassette, contract\n', encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Adapters tested against recorded replies")[0] == "MISSING", "the video factory's shape: a mock transport fed by hand, with the words, is not evidence: " + out
    (tmp_path / "tests" / "test_llm.py").write_text('import json\nfrom app import llm\n\nREPLY = json.load(open("tests/cassettes/openrouter.json"))\n', encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Adapters tested against recorded replies")[0] == "OK", "a cassette file the adapter's test loads is evidence: " + out
    (tmp_path / "app" / "bfl.py").write_text('import httpx2\nBASE = "https://api.bfl.ml/v1"\n', encoding="utf-8")
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "api.ts").write_text('export const models = () => fetch("https://openrouter.ai/api/v1/models");\n', encoding="utf-8")
    (tmp_path / "web" / "health.ts").write_text('export const health = () => fetch("/api/health");\n', encoding="utf-8")
    rc, out = run(tmp_path)
    kind, detail = verdict(out, "Adapters tested against recorded replies")
    assert kind == "MISSING" and "api" in detail and "bfl" in detail and "health" not in detail, "a JavaScript call to a provider counts, a call to the product's own API does not: " + out
