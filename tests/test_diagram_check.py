"""diagram-check.py (release A3, plan 8.7): a known deviation listed in docs/diagrams/DEVIATIONS.md
passes as a note and anything new fails; a review item that names no reviewer is a note before
project end and a failure at it; a deviation still listed at project end fails. Scratch repository."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "diagram-check.py")
KINDS = ["use-case", "operational-activity", "system-architecture", "deployment", "context-dfd", "inter-system-sequence", "infrastructure-state",
         "component", "inter-component-sequence", "component-dfd", "component-state", "class", "erd", "domain-dfd", "object", "micro-sequence",
         "algorithmic-activity", "object-state"]
LEVEL = {"use-case": 1, "operational-activity": 1, "system-architecture": 2, "deployment": 2, "context-dfd": 2, "inter-system-sequence": 2, "infrastructure-state": 2,
         "component": 3, "inter-component-sequence": 3, "component-dfd": 3, "component-state": 3, "class": 4, "erd": 4, "domain-dfd": 4, "object": 5,
         "micro-sequence": 5, "algorithmic-activity": 5, "object-state": 5}


def git(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid"] + list(args), capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def make_repo(tmp_path, review_item="review: security-auditor checks every crossing"):
    r = tmp_path / "ws"
    (r / "docs" / "diagrams").mkdir(parents=True)
    (r / "app" / "ui").mkdir(parents=True)
    (r / "app" / "store").mkdir()
    (r / "docs" / "REQUIREMENTS.md").write_text("| ID | Requirement |\n|---|---|\n| R-001 | things |\n", encoding="utf-8")
    rows = ["| ID | Level | Kind | Status | File | Refines | Realizes | Enforced by | Why |", "|---|---|---|---|---|---|---|---|---|",
            "| D-004 | 3 | component | selected | docs/diagrams/D-004-components.md | - | R-001 | check:components; %s | - |" % review_item]
    for k in KINDS:
        if k != "component":
            rows.append("| - | %d | %s | omitted | - | - | - | - | not needed in this scratch project |" % (LEVEL[k], k))
    (r / "docs" / "diagrams" / "INDEX.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (r / "docs" / "diagrams" / "D-004-components.md").write_text(
        "# D-004 component\n\n```mermaid\nflowchart LR\n  settings_ui[Settings] --> settings_service[Service]\n  settings_service --> key_store[(Keys)]\n```\n\n"
        "| Element | Paths |\n|---|---|\n| settings_ui | app/ui/** |\n| settings_service | app/service.py |\n| key_store | app/store/** |\n", encoding="utf-8")
    (r / "app" / "__init__.py").write_text("", encoding="utf-8")
    (r / "app" / "ui" / "__init__.py").write_text("", encoding="utf-8")
    (r / "app" / "store" / "__init__.py").write_text("", encoding="utf-8")
    (r / "app" / "service.py").write_text("from app.store import keys\n", encoding="utf-8")
    (r / "app" / "store" / "keys.py").write_text("KEYS = {}\n", encoding="utf-8")
    (r / "app" / "ui" / "view.py").write_text("from app.store import keys  # the view reads the store directly\n", encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    return r


def run(repo, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), capture_output=True, text=True, cwd=str(repo))
    return p.returncode, p.stdout + p.stderr


def test_a_listed_deviation_passes_as_a_note_and_a_new_one_fails(tmp_path):
    r = make_repo(tmp_path)
    rc, out = run(r, "--mode", "code")
    assert rc == 1 and "IMPORT: app/ui/view.py" in out and "settings_ui --> key_store" in out, out
    (r / "docs" / "diagrams" / "DEVIATIONS.md").write_text(
        "| Diagram | From | To | As built | Since | Resolved by |\n|---|---|---|---|---|---|\n| D-004 | settings_ui | key_store | the view reads the store directly | 2026-10-12 | TASK-041 |\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "deviations")
    rc, out = run(r, "--mode", "code")
    assert rc == 0 and "DEVIATION listed" in out and "1 known deviation(s)" in out, out
    (r / "app" / "ui" / "view.py").write_text("from app.store import keys\nfrom app import service\n", encoding="utf-8")
    git(r, "commit", "-q", "-am", "a second crossing")
    rc, out = run(r, "--mode", "code")
    assert rc == 0, "settings_ui --> settings_service is drawn: " + out
    (r / "app" / "store" / "keys.py").write_text("from app.ui import view  # a new crossing the diagram does not allow\n", encoding="utf-8")
    git(r, "commit", "-q", "-am", "a new crossing")
    rc, out = run(r, "--mode", "code")
    assert rc == 1 and "IMPORT: app/store/keys.py" in out and "DEVIATION listed" in out, out
    rc, out = run(r, "--mode", "done")
    assert rc == 1 and "still listed" in out, "a deviation still listed at project end fails: " + out


def test_a_review_item_must_name_its_reviewer_by_project_end(tmp_path):
    r = make_repo(tmp_path, review_item="review: every workflow step traces to a use case")
    rc, out = run(r, "--mode", "design")
    assert "names no reviewer" in out and "note:" in out.split("names no reviewer")[0].rsplit("\n", 1)[-1], "a note before project end: " + out
    assert "RESULT: OK" in out, out
    rc, out = run(r, "--mode", "done")
    assert rc == 1 and "names no reviewer" in out and "note: " + out.split("names no reviewer")[0].rsplit("\n", 1)[-1] not in out, "a failure at project end: " + out
