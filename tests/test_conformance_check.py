"""conformance-check.py (review R4): a conformant workspace passes; each missing floor is
reported; secret names in .env are reported, never values; nothing is written."""
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, ".claude", "cursor-bridge", "conformance-check.py")
VERSION = open(os.path.join(HERE, os.pardir, ".claude", "cursor-bridge", "VERSION"), encoding="utf-8").read().strip()

GATE = """name: gate
on: [pull_request]
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09
      - run: semgrep ci
      - run: osv-scanner --lockfile package-lock.json
      - run: socket ci
      - run: npx impeccable@3.3.0 detect --json docs/mockups
"""


def make_workspace(root, conformant=True):
    (root / "docs" / "diagrams").mkdir(parents=True)
    (root / "docs" / "mockups").mkdir()
    (root / ".cursor" / "rules").mkdir(parents=True)
    (root / ".github" / "workflows").mkdir(parents=True)
    for name in ("PROJECT_STATUS.md", "INVENTORY.md", "REQUIREMENTS.md", "RUN_PARAMETERS.md", "ROSTER.json", "DESIGN.md"):
        (root / "docs" / name).write_text("x\n", encoding="utf-8")
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
        (root / ".github" / "workflows" / "ci.yml").write_text(GATE.replace("semgrep ci", "echo no").replace("@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09", "@v5").replace("ubuntu-latest", "windows-latest"), encoding="utf-8")
        (root / "docs" / "diagrams" / "INDEX.md").unlink()
        (root / ".cursor" / "rules" / "secure-coding.mdc").unlink()
        (root / ".env").write_text("DATABASE_URL=x\nMODAL_TOKEN_SECRET=abc123\nexport OPENROUTER_API_KEY=sk-live-999\n", encoding="utf-8")
        (root / "docs" / "PROJECT_STATUS.md").write_text("Bridge version: 2026.09.27c\nPhase: building\n", encoding="utf-8")


def run(root):
    p = subprocess.run([sys.executable, PROG, str(root)], capture_output=True, text=True)
    return p.returncode, p.stdout


def test_a_conformant_workspace_passes(tmp_path):
    make_workspace(tmp_path)
    rc, out = run(tmp_path)
    assert rc == 0 and "RESULT: CONFORMANT" in out, out
    assert "0 MISSING" in out and "  MISSING" not in out


def test_each_missing_floor_is_named_and_secret_values_never_printed(tmp_path):
    make_workspace(tmp_path, conformant=False)
    rc, out = run(tmp_path)
    assert rc == 1, out
    for floor in ("Semgrep in the gate", "CI actions pinned by commit", "Secure-coding rule", "docs/diagrams/INDEX.md",
                  "Keys out of the builder's reach", "Calibrated to the installed bridge"):
        assert ("MISSING  " + floor) in out, floor
    assert "NOTE     Runner OS" in out
    assert "MODAL_TOKEN_SECRET" in out and "OPENROUTER_API_KEY" in out
    assert "abc123" not in out and "sk-live-999" not in out, "values must never be printed"
    assert "DATABASE_URL" not in out.split("Keys out of the builder's reach")[1].split("\n")[0]
    assert "OSV-Scanner in the gate" not in [l.strip() for l in out.splitlines() if l.strip().startswith("MISSING")], "OSV is present in the fixture"


def test_not_a_workspace(tmp_path):
    rc, out = run(tmp_path / "nothing")
    assert rc == 2


def test_writes_nothing(tmp_path):
    make_workspace(tmp_path, conformant=False)
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    run(tmp_path)
    after = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    assert before == after
