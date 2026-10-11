"""diagram-check.py (release A4, 13.1): a project's own shortcut paths are read from tsconfig/jsconfig,
a tracked `build/` folder is source, and a column named like a keyword is a column. In-process and
scratch repositories."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "diagram-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
KINDS = ["use-case", "operational-activity", "system-architecture", "deployment", "context-dfd", "inter-system-sequence", "infrastructure-state",
         "component", "inter-component-sequence", "component-dfd", "component-state", "class", "erd", "domain-dfd", "object", "micro-sequence",
         "algorithmic-activity", "object-state"]
LEVEL = {"use-case": 1, "operational-activity": 1, "system-architecture": 2, "deployment": 2, "context-dfd": 2, "inter-system-sequence": 2, "infrastructure-state": 2,
         "component": 3, "inter-component-sequence": 3, "component-dfd": 3, "component-state": 3, "class": 4, "erd": 4, "domain-dfd": 4, "object": 5,
         "micro-sequence": 5, "algorithmic-activity": 5, "object-state": 5}


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stdout + p.stderr


def make(tmp_path, ui_paths, store_paths, files):
    r = tmp_path / "ws"
    (r / "docs" / "diagrams").mkdir(parents=True)
    (r / "docs" / "REQUIREMENTS.md").write_text("| ID | Requirement |\n|---|---|\n| R-001 | things |\n", encoding="utf-8")
    rows = ["| ID | Level | Kind | Status | File | Refines | Realizes | Enforced by | Why |", "|---|---|---|---|---|---|---|---|---|",
            "| D-004 | 3 | component | selected | docs/diagrams/D-004-components.md | - | R-001 | check:components; review: diff-reviewer — crossings | - |"]
    for k in KINDS:
        if k != "component":
            rows.append("| - | %d | %s | omitted | - | - | - | - | not needed |" % (LEVEL[k], k))
    (r / "docs" / "diagrams" / "INDEX.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (r / "docs" / "diagrams" / "D-004-components.md").write_text(
        "# D-004 component\n\n```mermaid\nflowchart LR\n  ui[UI] --> service[Service]\n  service --> store[(Store)]\n```\n\n"
        "| Element | Paths |\n|---|---|\n| ui | %s |\n| service | app/service.* |\n| store | %s |\n" % (ui_paths, store_paths), encoding="utf-8")
    for f, t in files.items():
        (r / f).parent.mkdir(parents=True, exist_ok=True)
        (r / f).write_text(t, encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    return r


def run(repo):
    p = subprocess.run([sys.executable, PROG, "--mode", "code"], capture_output=True, text=True, cwd=str(repo), env=ENV)
    return p.returncode, p.stdout + p.stderr


def test_the_projects_own_shortcut_paths_are_read(tmp_path):
    r = make(tmp_path, "app/ui/**", "app/store/**", {
        "tsconfig.json": json.dumps({"compilerOptions": {"baseUrl": ".", "paths": {"@app/*": ["app/*"], "#store/*": ["app/store/*"]}}}),
        "app/service.ts": "import { keys } from '@app/store/keys';\n",
        "app/store/keys.ts": "export const keys = {};\n",
        "app/ui/view.ts": "import { keys } from '#store/keys';  // the view reads the store directly\n"})
    rc, out = run(r)
    assert rc == 1 and "IMPORT: app/ui/view.ts" in out and "ui --> store" in out, "the alias #store/* was not resolved (13.1): " + out
    assert "app/service.ts" not in "\n".join(l for l in out.splitlines() if l.startswith("IMPORT")), out


def test_a_tracked_build_folder_is_source(tmp_path):
    r = make(tmp_path, "build/ui/**", "build/store/**", {
        "build/__init__.py": "", "build/ui/__init__.py": "", "build/store/__init__.py": "",
        "app/service.py": "from build.store import keys\n",
        "build/store/keys.py": "KEYS = {}\n",
        "build/ui/view.py": "from build.store import keys\n"})
    rc, out = run(r)
    assert rc == 1 and "IMPORT: build/ui/view.py" in out, "a tracked folder named build/ was skipped (13.1): " + out


def test_a_column_named_like_a_keyword_is_a_column(program):
    dc = program("diagram-check")
    tables = dc.sql_schema('CREATE TABLE t (id INT PRIMARY KEY, key VARCHAR(10), "index" INT, `check` INT, KEY idx_name (id), INDEX (key), CONSTRAINT c CHECK (id > 0));')
    assert tables["t"] == {"id", "key", "index", "check"}, tables
