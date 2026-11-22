"""TASK-072, the supervisor's acceptance tests (R-092): the conformance check knows the weekly scan.

enforces: docs/REQUIREMENTS.md R-092; docs/BUILD_PLAN.md, TASK-072's Done when (J14 for the docstring's exits).

The forms these tests pin:
- conformance-check.py prints exactly one row named `Weekly dependency scan`, in its usual row form
  (`  <STATUS>  Weekly dependency scan  - <detail>`), its status OK, NOTE or MISSING.
- Workflows are told apart by their triggers and steps, never by a file name. An OSV-Scanner step is a step
  whose run text matches the program's OSV-Scanner pattern. The gate's lock files are the union, as a set, of
  the `--lockfile=` values of the OSV-Scanner steps in workflows triggered by pull_request or push; a weekly
  workflow is a workflow file under .github/workflows/ with an OSV-Scanner step and a `schedule:` trigger.
  A value is compared after one pair of matching surrounding quotes is removed; values compare as sets.
- OK where some weekly workflow's set equals the gate's; else NOTE for an inventory Decisions row whose first
  cell begins `Weekly scan:` (the detail quotes that cell); else NOTE where the local git configuration names
  no github.com remote; else MISSING, saying which: no workflow file runs OSV-Scanner on a `schedule:` trigger,
  a workflow with an OSV-Scanner step that "has no schedule: trigger", or a list that differs, naming the lock
  files apart. The OK detail says pins, permissions and exit handling are "not compared" and that a workflow
  "disabled" on GitHub is the evaluation's read.
- An index with every diagram kind omitted, each with its reason, passes diagram-check.py's three modes and
  the conformance check's diagram floor (green on the checkpoint: the design found main right).
- The check's docstring names every exit code main() returns, with its meaning (J14).
- This repository's own run prints the row OK.

Every conformance run here passes --offline, so nothing reaches the network. Each test builds its own scratch
project under tmp_path; nothing here is shared with another test module.
"""
import ast
import os
import re
import subprocess
import sys

import pytest

import conftest as suite_conftest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
CONFORMANCE = os.path.join(BRIDGE, "conformance-check.py")
DIAGRAM = os.path.join(BRIDGE, "diagram-check.py")
with open(os.path.join(BRIDGE, "VERSION"), encoding="utf-8") as _f:
    BRIDGE_VERSION = _f.read().strip()

ROW_NAME = "Weekly dependency scan"
PIN = "3d3c42e5aac5ba805825da76410c181273ba90b1"
GITHUB_REMOTE = "https://github.com/example-owner/thing.git"
OTHER_REMOTE = "https://gitlab.example.invalid/team/thing.git"
OSV_FETCH = ('curl -fsSL -o osv-scanner "https://github.com/google/osv-scanner/releases/download/v2.7.0/'
             'osv-scanner_linux_amd64"')

GATE = """name: tests
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  security-floor:
    name: security floor
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@%(pin)s
        with:
          persist-credentials: false
      - name: Semgrep
        run: pipx run semgrep==1.176.1 scan --config .semgrep.yml --error .
%(osv)s      - name: Socket
        run: npx socket@1.2.3 ci --no-banner
"""

OSV_STEP = """      - name: OSV-Scanner
        shell: bash
        run: |
          %(fetch)s
          chmod +x osv-scanner
          ./osv-scanner scan source --config=osv-scanner.toml %(locks)s
"""

SCAN = """name: %(name)s
on:
%(on)spermissions:
  contents: read
jobs:
  dependency-scan:
    name: dependency scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@%(pin)s
        with:
          persist-credentials: false
%(osv)s"""

SCHEDULED = "  schedule:\n    - cron: '17 6 * * 0'\n  workflow_dispatch:\n"
DISPATCH_ONLY = "  workflow_dispatch:\n"

INVENTORY = """# Inventory - Thing
Reflected through: none
Updated: 2026-11-21

## Features
| Feature | What it does | Where | Tests | Since |
|---|---|---|---|---|
| Search | finds things | app/search.py | tests/test_search.py | TASK-001 |

## Resources
| Name | Kind | Where it lives | Used by | Provided |
|---|---|---|---|---|

## Decisions
| Decision | Reason | Settled | Revisit only if |
|---|---|---|---|
| Development data: a development build reads `data/dev.sqlite` and refuses the installed product's store | two live stores were upgraded by development builds | 2026-11-01, owner | the product gains a second store |
%(extra)s
## Deferred
| Item | Why deferred | Since | Owner decision needed |
|---|---|---|---|
"""

KINDS = (("use-case", 1), ("operational-activity", 1), ("system-architecture", 2), ("deployment", 2),
         ("context-dfd", 2), ("inter-system-sequence", 2), ("infrastructure-state", 2), ("component", 3),
         ("inter-component-sequence", 3), ("component-dfd", 3), ("component-state", 3), ("class", 4),
         ("erd", 4), ("domain-dfd", 4), ("object", 5), ("micro-sequence", 5), ("algorithmic-activity", 5),
         ("object-state", 5))


# ---------------------------------------------------------------- the scratch project

def put(ws, rel, text):
    path = os.path.join(str(ws), *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(text.encode("ascii"))


def git(ws, *args):
    kw = suite_conftest.windowless_kwargs({"capture_output": True, "text": True, "timeout": 60})
    p = subprocess.run(["git", "-C", str(ws).replace("\\", "/"), "-c", "core.autocrlf=false",
                        "-c", "user.name=t", "-c", "user.email=t@example.invalid"] + list(args), **kw)
    assert p.returncode == 0, p.stdout + p.stderr


def osv_step(locks):
    return OSV_STEP % {"fetch": OSV_FETCH, "locks": locks}


def gate(locks):
    """The gate workflow (push and pull_request), its OSV-Scanner step running with `locks`, or no
    OSV-Scanner step when `locks` is None."""
    return GATE % {"pin": PIN, "osv": "" if locks is None else osv_step(locks)}


def scan(locks, on=SCHEDULED, name="dependency-scan"):
    return SCAN % {"name": name, "on": on, "pin": PIN, "osv": osv_step(locks)}


def make_project(tmp_path, gate_text, workflows=(), remote=GITHUB_REMOTE, decision="", index="# Diagrams\n"):
    """A scratch Workspace the conformance check finds conformant but for the weekly row: the records,
    project.json, the builder's rules and hooks, .gitignore, the gate workflow `gate_text` (as tests.yml),
    the extra workflows `workflows` ((file name, text) pairs), an inventory with `decision` as an extra
    Decisions row, and a git repository whose origin is `remote` (None: no remote)."""
    ws = tmp_path / "proj" / "Workspace"
    os.makedirs(str(ws))
    for rel in ("docs/REQUIREMENTS.md", "docs/RUN_PARAMETERS.md", "docs/ROSTER.json", "docs/DESIGN.md"):
        put(ws, rel, "x\n")
    put(ws, "docs/PROJECT_STATUS.md", "# Project Status\nBridge version: %s\nPhase: building\n"
                                      "Workflows: not yet classified\n" % BRIDGE_VERSION)
    put(ws, "docs/INVENTORY.md", INVENTORY % {"extra": decision})
    put(ws, "docs/diagrams/INDEX.md", index)
    put(ws, "project.json", '{"name": "Thing", "purpose": "finds things", "kind": "private", "version": "0.0.0", '
                            '"state": {"phase": "building", "stage": "Stage 1", "bridge": "%s", '
                            '"updated": "2026-11-21"}}' % BRIDGE_VERSION)
    put(ws, ".cursor/rules/workspace-boundary.mdc", "rule\n")
    put(ws, ".cursor/rules/secure-coding.mdc", "rule\n")
    put(ws, ".cursor/hooks.json", '{"hooks": ["boundary-check.py", "windowless-check.py"]}')
    put(ws, ".gitignore", "docs/BOUNDARY_VIOLATIONS.md\nrun/\n")
    put(ws, ".github/workflows/tests.yml", gate_text)
    for name, text in workflows:
        put(ws, ".github/workflows/" + name, text)
    git(ws, "init", "-q")
    if remote is not None:
        git(ws, "remote", "add", "origin", remote)
    return ws


def conformance(ws, cwd=None):
    kw = suite_conftest.windowless_kwargs({"capture_output": True, "text": True, "encoding": "utf-8",
                                           "errors": "replace", "timeout": 300})
    p = subprocess.run([sys.executable, CONFORMANCE, str(ws), "--offline"], cwd=str(cwd or ws), **kw)
    return p.returncode, p.stdout + p.stderr


def rows(out, name):
    """[(status, detail)] for every row of the check's output named exactly `name`."""
    found = []
    for line in out.splitlines():
        m = re.match(r"^  (OK|MISSING|NOTE) +(.*)$", line)
        if not m:
            continue
        rest = m.group(2)
        if rest == name:
            found.append((m.group(1), ""))
        elif rest.startswith(name + "  - "):
            found.append((m.group(1), rest[len(name) + 4:]))
    return found


def weekly_row(out):
    found = rows(out, ROW_NAME)
    assert len(found) == 1, "exactly one row named %r: %s" % (ROW_NAME, out)
    return found[0]


def plain(detail):
    return detail.replace("`", "")


def assert_ok(rc, out):
    status, detail = weekly_row(out)
    assert status == "OK", out
    assert "not compared" in detail and "disabled" in detail, out
    assert rc == 0 and "RESULT: CONFORMANT" in out, out


# ---------------------------------------------------------------- the weekly row

def test_ok_on_the_repository_like_pair(tmp_path):
    """R-092, TASK-072 Done when (`OK` where a workflow file under `.github/workflows/` carries a `schedule:`
    trigger and an OSV-Scanner step whose `--lockfile=` list equals, as a set, the gate workflow's): the gate
    quotes its value (--lockfile='requirements.txt:requirements.lock'), the weekly does not, as in this
    repository. Today's code prints no weekly row, so this fails."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"),
                      [("dependency-scan.yml", scan("--lockfile=requirements.txt:requirements.lock"))])
    rc, out = conformance(ws)
    assert_ok(rc, out)


def test_ok_with_a_weekly_workflow_named_otherwise(tmp_path):
    """R-092, TASK-072 Done when (the row is found by the steps' own commands, never by a file name, so a
    project that names its workflow otherwise passes): the weekly is .github/workflows/nightly-deps.yaml.
    Today's code prints no weekly row (and reads that file as a gate workflow), so this fails."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"),
                      [("nightly-deps.yaml", scan("--lockfile=requirements.txt:requirements.lock", name="nightly deps"))])
    rc, out = conformance(ws)
    assert_ok(rc, out)


def test_ok_where_the_weekly_lists_two_lock_files_in_another_order(tmp_path):
    """R-092, TASK-072 Done when (the `--lockfile=` list equals, as a set, the gate workflow's): the gate lists
    package-lock.json then requirements.txt:requirements.lock, quoted two ways; the weekly lists them unquoted in
    the other order. Today's code prints no weekly row, so this fails."""
    ws = make_project(tmp_path, gate("--lockfile=\"package-lock.json\" --lockfile='requirements.txt:requirements.lock'"),
                      [("dependency-scan.yml", scan("--lockfile=requirements.txt:requirements.lock --lockfile=package-lock.json"))])
    rc, out = conformance(ws)
    assert_ok(rc, out)


def test_note_by_a_weekly_scan_decision_row_quoting_its_cell(tmp_path):
    """R-092, TASK-072 Done when (`NOTE` where the inventory's Decisions holds a row whose first cell begins
    `Weekly scan:`, the note quoting that cell): no weekly workflow, a GitHub remote, and a Decisions row
    `Weekly scan: not kept, the gate scans every pull request`. Today's code prints no weekly row, so this
    fails."""
    cell = "Weekly scan: not kept, the gate scans every pull request"
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"),
                      decision="| %s | a short-lived project | 2026-11-21, owner | the project ships |\n" % cell)
    rc, out = conformance(ws)
    status, detail = weekly_row(out)
    assert status == "NOTE", out
    assert cell in detail, "the note quotes the Decisions cell: " + out
    assert rc == 0, out


@pytest.mark.parametrize("remote", [None, OTHER_REMOTE], ids=["no-remote", "non-github-remote"])
def test_note_without_a_github_remote(tmp_path, remote):
    """R-092, TASK-072 Done when (`NOTE` where the repository has no GitHub remote, read from the local
    configuration alone): no weekly workflow, no Decisions row, and a scratch repository with no remote or
    with a remote that is not on github.com. Today's code prints no weekly row, so this fails."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"), remote=remote)
    rc, out = conformance(ws)
    status, _detail = weekly_row(out)
    assert status == "NOTE", out
    assert rc == 0, out


def test_missing_with_no_weekly_file_and_a_github_remote(tmp_path):
    """R-092, TASK-072 Done when (`MISSING` where the file is absent, the row saying which): the gate alone, a
    GitHub remote, no Decisions row; the detail says no workflow file runs OSV-Scanner on a `schedule:`
    trigger. Today's code prints no weekly row, so this fails."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"))
    rc, out = conformance(ws)
    status, detail = weekly_row(out)
    assert status == "MISSING", out
    assert "no workflow file" in plain(detail).lower() and "schedule:" in plain(detail), out
    assert rc == 1, out


def test_missing_with_a_workflow_dispatch_only_scan(tmp_path):
    """R-092, TASK-072 Done when (`MISSING` where the file has no `schedule:` trigger, the row saying which):
    an OSV-Scanner workflow triggered by workflow_dispatch alone, its list equal to the gate's; the detail says
    it "has no schedule: trigger" (backticks around schedule: allowed). Today's code prints no weekly row, so
    this fails."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"),
                      [("dependency-scan.yml", scan("--lockfile=requirements.txt:requirements.lock", on=DISPATCH_ONLY))])
    rc, out = conformance(ws)
    status, detail = weekly_row(out)
    assert status == "MISSING", out
    assert "has no schedule: trigger" in plain(detail), out
    assert rc == 1, out


def test_missing_with_a_scheduled_scan_whose_list_differs(tmp_path):
    """R-092, TASK-072 Done when (`MISSING` where its list differs, the row naming the lock files apart): the
    gate scans requirements.txt:requirements.lock and package-lock.json, the weekly
    requirements.txt:requirements.lock and poetry.lock; the detail names package-lock.json (the gate's alone)
    and poetry.lock (the weekly's alone). Today's code prints no weekly row, so this fails."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock' --lockfile=package-lock.json"),
                      [("dependency-scan.yml", scan("--lockfile=requirements.txt:requirements.lock --lockfile=poetry.lock"))])
    rc, out = conformance(ws)
    status, detail = weekly_row(out)
    assert status == "MISSING", out
    assert "package-lock.json" in detail and "poetry.lock" in detail, out
    assert rc == 1, out


def test_a_scheduled_scan_is_never_read_as_the_gate(tmp_path):
    """R-092, TASK-072 Done when (workflows told apart by their triggers and steps): the gate has no
    OSV-Scanner step and the scheduled dependency-scan.yml has one; `OSV-Scanner in the gate` stays MISSING.
    Today's code already holds this, by the file name dependency-scan.yml, so this passes today."""
    ws = make_project(tmp_path, gate(None),
                      [("dependency-scan.yml", scan("--lockfile=requirements.txt:requirements.lock"))])
    rc, out = conformance(ws)
    found = rows(out, "OSV-Scanner in the gate")
    assert found and found[0][0] == "MISSING", out
    assert rc == 1, out


# ---------------------------------------------------------------- an index with every kind omitted

def omitted_index():
    lines = ["# Diagrams", "",
             "| ID | Level | Kind | Status | File | Refines | Realizes | Enforced by | Why |",
             "|---|---|---|---|---|---|---|---|---|"]
    for kind, level in KINDS:
        lines.append("| - | %d | %s | omitted | - | - | - | - | a single script; no %s carries a decision here |"
                     % (level, kind, kind))
    return "\n".join(lines) + "\n"


def diagram_project(tmp_path):
    ws = tmp_path / "proj" / "Workspace"
    put(ws, "docs/diagrams/INDEX.md", omitted_index())
    put(ws, "docs/REQUIREMENTS.md", "| ID | Requirement |\n|---|---|\n| R-001 | things |\n")
    put(ws, "app/main.py", "print('thing')\n")
    git(ws, "init", "-q")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "scratch")
    return ws


def diagram_check(ws, mode):
    kw = suite_conftest.windowless_kwargs({"capture_output": True, "text": True, "encoding": "utf-8",
                                           "errors": "replace", "timeout": 120})
    p = subprocess.run([sys.executable, DIAGRAM, "--mode", mode], cwd=str(ws), **kw)
    return p.returncode, p.stdout + p.stderr


@pytest.mark.parametrize("mode", ["design", "code", "done"])
def test_an_all_omitted_index_passes_diagram_check(tmp_path, mode):
    """R-092, TASK-072 Done when (a diagram index with every kind omitted, each with its reason, passes
    `diagram-check.py --mode design`, `--mode code` and `--mode done`): every catalogue kind omitted with a
    reason in Why. Today's code passes it (the design found main right; the test holds it)."""
    ws = diagram_project(tmp_path)
    rc, out = diagram_check(ws, mode)
    assert rc == 0 and "RESULT: OK" in out, out


def test_an_all_omitted_index_passes_the_conformance_diagram_floor(tmp_path):
    """R-092, TASK-072 Done when (a diagram index with every kind omitted, each with its reason, passes the
    conformance check's diagram floor): the `docs/diagrams/INDEX.md` row is OK. Today's code passes it (the
    design found main right; the test holds it)."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"),
                      [("dependency-scan.yml", scan("--lockfile=requirements.txt:requirements.lock"))],
                      index=omitted_index())
    _rc, out = conformance(ws)
    found = rows(out, "docs/diagrams/INDEX.md")
    assert found == [("OK", "")], out


# ---------------------------------------------------------------- the docstring's exits (J14)

EXIT_MEANINGS = {
    0: (("every floor", "conformant"),),
    1: (("missing",),),
    2: (("workspace",), ("header", "malformed")),
}


def _main_exit_codes(tree):
    codes = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Constant) and isinstance(sub.value.value, int) \
                        and not isinstance(sub.value.value, bool):
                    codes.add(sub.value.value)
    for sub in ast.walk(tree):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "exit" \
                and sub.args and isinstance(sub.args[0], ast.Constant) and isinstance(sub.args[0].value, int):
            codes.add(sub.args[0].value)
    return codes


def test_the_docstring_lists_the_exits_the_code_has(tmp_path):
    """R-092, TASK-072 Done when (the check's docstring lists its exits as the code has them, J14): main()
    returns 0 (conformant), 1 (a MISSING floor), and 2 both for a folder that is not a workspace and for a
    malformed record header (HEADER MALFORMED, the status file's or the inventory's); the entry passes main's
    value to sys.exit. Today's docstring says `2 = not a workspace` only, so this fails."""
    with open(CONFORMANCE, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    assert _main_exit_codes(tree) == set(EXIT_MEANINGS), "the exits main() returns changed: update this test"
    doc = ast.get_docstring(tree) or ""
    marks = list(re.finditer(r"(?<![\w.\-])([0-9])(?![\w.])\s*(?:=|:|-)\s*", doc))
    meaning = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(doc)
        meaning.setdefault(int(m.group(1)), []).append(doc[m.end():min(end, m.end() + 250)].lower())
    for code, keys in sorted(EXIT_MEANINGS.items()):
        text = " ".join(meaning.get(code, []))
        assert text, "the docstring names no exit %d" % code
        for alternatives in keys:
            assert any(word in text for word in alternatives), \
                "the docstring's exit %d does not say %s: %r" % (code, " or ".join(alternatives), text)


# ---------------------------------------------------------------- this repository

def test_this_repository_prints_the_weekly_row_ok():
    """R-092, TASK-072 Done when (this repository's own conformance run prints the new row `OK`): a read-only
    --offline run over this Workspace; tests.yml's OSV-Scanner step quotes
    --lockfile='requirements.txt:requirements.lock', dependency-scan.yml's does not. Today's code prints no
    weekly row, so this fails."""
    rc, out = conformance(ROOT, cwd=ROOT)
    status, detail = weekly_row(out)
    assert status == "OK", out
    assert "not compared" in detail and "disabled" in detail, out


# ---------------------------------------------------------------- round 2: the remote is this repository's own

def conformance_env(ws, env):
    """The check over `ws`, --offline, with `env` as its whole environment."""
    kw = suite_conftest.windowless_kwargs({"capture_output": True, "text": True, "encoding": "utf-8",
                                           "errors": "replace", "timeout": 300, "env": env})
    p = subprocess.run([sys.executable, CONFORMANCE, str(ws), "--offline"], cwd=str(ws), **kw)
    return p.returncode, p.stdout + p.stderr


def test_r2_a_git_dir_whose_path_holds_a_space_is_read(tmp_path):
    """R-092, TASK-072 Done when (`NOTE` where the repository has no GitHub remote, read from the local
    configuration alone; otherwise `MISSING` where the file is absent): Review A round 1, B1. The Workspace's
    .git is a file (`git init --separate-git-dir`, as a worktree's is) naming a folder whose path holds a space;
    the repository's origin is on github.com and no weekly workflow exists, so the row is MISSING. Round 1 cut
    the gitdir path at its first space and read NOTE."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"))
    git(ws, "init", "-q", "--separate-git-dir", str(tmp_path / "git dir with space").replace("\\", "/"))
    assert os.path.isfile(os.path.join(str(ws), ".git"))
    rc, out = conformance(ws)
    status, detail = weekly_row(out)
    assert status == "MISSING", out
    assert "no workflow file" in plain(detail).lower(), out
    assert rc == 1, out


@pytest.mark.parametrize("how", ["global-file", "environment-pairs"])
def test_r2_a_remote_outside_this_repository_config_is_not_read(tmp_path, how):
    """R-092, TASK-072 Done when (`NOTE` where the repository has no GitHub remote, read from the local
    configuration alone): Review A round 1, B2. The repository has no remote; a github.com remote stands in
    the user's global configuration (GIT_CONFIG_GLOBAL) or in configuration passed by the environment
    (GIT_CONFIG_COUNT); neither is this repository's, so the row is NOTE. Round 1 read both and said MISSING."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"), remote=None)
    env = dict(os.environ)
    if how == "global-file":
        cfg = tmp_path / "global.gitconfig"
        cfg.write_text('[remote "x"]\n\turl = %s\n' % GITHUB_REMOTE, encoding="ascii")
        env["GIT_CONFIG_GLOBAL"] = str(cfg)
    else:
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "remote.y.url"
        env["GIT_CONFIG_VALUE_0"] = GITHUB_REMOTE
    rc, out = conformance_env(ws, env)
    status, _detail = weekly_row(out)
    assert status == "NOTE", out
    assert rc == 0, out


def test_r2_an_included_config_file_is_not_read(tmp_path):
    """R-092, TASK-072 Done when (`NOTE` where the repository has no GitHub remote, read from the local
    configuration alone): the security audit of round 1. The repository's own config names no remote but
    includes (include.path) a file outside it that names a github.com remote; an include is not this
    repository's configuration, and following one lets a project's config make the check read any file, so the
    row is NOTE. Round 1 followed the include and said MISSING."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"), remote=None)
    inc = tmp_path / "included.gitconfig"
    inc.write_text('[remote "origin"]\n\turl = %s\n' % GITHUB_REMOTE, encoding="ascii")
    git(ws, "config", "include.path", str(inc).replace("\\", "/"))
    rc, out = conformance(ws)
    status, _detail = weekly_row(out)
    assert status == "NOTE", out
    assert rc == 0, out


@pytest.mark.parametrize("key", ['"on":', "'on':"], ids=["double-quoted", "single-quoted"])
def test_r2_a_quoted_on_key_is_read(tmp_path, key):
    """R-092, TASK-072 Done when (`OK` where a workflow file carries a `schedule:` trigger and an OSV-Scanner
    step whose list equals the gate's): Review A round 1, S1. Both workflows write their trigger key quoted, as
    yamllint's truthy rule asks; the lists are equal and the remote is on github.com, so the row is OK. Round 1
    read no trigger under a quoted key and said MISSING."""
    gate_text = gate("--lockfile='requirements.txt:requirements.lock'").replace("\non:\n", "\n%s\n" % key)
    scan_text = scan("--lockfile=requirements.txt:requirements.lock").replace("\non:\n", "\n%s\n" % key)
    assert key in gate_text and key in scan_text
    ws = make_project(tmp_path, gate_text, [("dependency-scan.yml", scan_text)])
    rc, out = conformance(ws)
    assert_ok(rc, out)


def test_r2_a_parent_folder_repository_is_not_read(tmp_path):
    """R-092, TASK-072 Done when (`NOTE` where the repository has no GitHub remote, read from the local
    configuration alone): Review A round 1, a gap no test held. The Workspace has no .git of its own; the
    folder above it is a repository whose origin is on github.com. That repository is not the Workspace's, so
    the row is NOTE."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"))
    os.rename(os.path.join(str(ws), ".git"), os.path.join(os.path.dirname(str(ws)), ".git"))
    assert not os.path.exists(os.path.join(str(ws), ".git"))
    rc, out = conformance(ws)
    status, _detail = weekly_row(out)
    assert status == "NOTE", out
    assert rc == 0, out


def test_r2_the_remote_url_is_never_printed(tmp_path):
    """R-092, TASK-072 (the brief's trust boundary: a remote URL can hold a credential and is never printed):
    Review A round 1, a gap no test held. The origin carries a user name; the row is MISSING and no part of the
    URL appears in the output."""
    remote = "https://example-user@github.com/example-owner/thing.git"
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"), remote=remote)
    rc, out = conformance(ws)
    status, _detail = weekly_row(out)
    assert status == "MISSING", out
    assert "example-user" not in out and "example-owner" not in out, out


def test_r2_the_row_stands_where_there_is_no_workflow(tmp_path):
    """R-092, TASK-072 Done when (`MISSING` where the file is absent, the row saying which): Review A round 1,
    a gap no test held. The project has no workflow at all and a github.com remote; the one row still stands,
    MISSING, saying no workflow file runs OSV-Scanner on a schedule: trigger."""
    ws = make_project(tmp_path, gate(None))
    os.remove(os.path.join(str(ws), ".github", "workflows", "tests.yml"))
    rc, out = conformance(ws)
    status, detail = weekly_row(out)
    assert status == "MISSING", out
    assert "no workflow file" in plain(detail).lower() and "schedule:" in plain(detail), out
    assert rc == 1, out


# ---------------------------------------------------------------- round 3: no link is followed to the git folder

def link_dir(link, target):
    """A folder link the platform makes without a privilege: a junction on Windows, a symbolic link elsewhere."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(str(target), str(link), target_is_directory=True)


def unlink_dir(link):
    """Remove the link itself, never what it points at."""
    if os.name == "nt":
        os.rmdir(str(link))
    else:
        os.unlink(str(link))


def test_r3_a_git_entry_that_is_a_link_is_not_followed(tmp_path):
    """R-092, TASK-072 (the brief's trust boundary: the remote is read from the Workspace's own configuration and
    reading the row never opens a network connection): Review B round 1, finding 1. The Workspace's .git is a
    link (a junction on Windows) to a git folder elsewhere whose origin is on github.com; a link at .git could as
    well name a folder on another host, so it is not followed and the row is NOTE (no GitHub remote of its own).
    Round 2 followed it and said MISSING."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"))
    real = tmp_path / "real-git"
    os.rename(os.path.join(str(ws), ".git"), str(real))
    link = os.path.join(str(ws), ".git")
    link_dir(link, real)
    try:
        rc, out = conformance(ws)
        status, _detail = weekly_row(out)
        assert status == "NOTE", out
    finally:
        unlink_dir(link)


def test_r3_a_gitdir_target_that_is_a_link_is_not_followed(tmp_path):
    """R-092, TASK-072 (as above): Review B round 1, finding 1, its second door. The Workspace's .git is a file
    whose gitdir: line names a link (a junction on Windows) to the real git folder, whose origin is on github.com;
    the link is not followed and the row is NOTE. Round 2 followed it and said MISSING."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"))
    named = tmp_path / "gitdir-link"
    git(ws, "init", "-q", "--separate-git-dir", str(named).replace("\\", "/"))
    assert os.path.isfile(os.path.join(str(ws), ".git"))
    real = tmp_path / "gitdir-real"
    os.rename(str(named), str(real))
    link_dir(named, real)
    try:
        rc, out = conformance(ws)
        status, _detail = weekly_row(out)
        assert status == "NOTE", out
    finally:
        unlink_dir(named)


# ---------------------------------------------------------------- rebuild round 2: a network gitdir, either slash order

NET_HOST = "nohost.invalid"

GUARD_RUNNER = r'''
import os, runpy, subprocess, sys
MARK = "nohost.invalid"


def touched(what):
    sys.stderr.write("TOUCHED-NETWORK-PATH %s\n" % what)
    raise OSError("the test refuses a filesystem or git call on the network path")


def hit(value):
    try:
        return MARK in os.fsdecode(value).lower()
    except TypeError:
        return MARK in str(value).lower()


def guard(name, fn):
    def wrapped(path, *a, **k):
        if hit(path):
            touched(name)
        return fn(path, *a, **k)
    return wrapped


for name in ("lstat", "stat", "scandir", "listdir"):
    setattr(os, name, guard(name, getattr(os, name)))
for name in ("isdir", "isfile", "exists", "lexists", "islink", "realpath"):
    setattr(os.path, name, guard(name, getattr(os.path, name)))
import builtins
builtins.open = guard("open", builtins.open)
_Popen = subprocess.Popen


class GuardedPopen(_Popen):
    def __init__(self, args, *a, **k):
        env = k.get("env") or {}
        if any(hit(v) for v in env.values()) or any(hit(x) for x in (args if isinstance(args, (list, tuple)) else [args])):
            touched("subprocess")
        super().__init__(args, *a, **k)


subprocess.Popen = GuardedPopen
target = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(target, run_name="__main__")
'''


@pytest.mark.parametrize("gitdir", [
    "//" + NET_HOST + "/share/x",
    "\\\\" + NET_HOST + "\\share\\x",
    "/\\" + NET_HOST + "\\share\\x",
    "\\/" + NET_HOST + "/share/x",
    "\\??\\UNC\\" + NET_HOST + "\\share",
    "\\??\\GLOBALROOT\\Device\\Mup\\" + NET_HOST + "\\share",
    "/??/UNC/" + NET_HOST + "/share",
], ids=["two-slashes", "two-backslashes", "slash-then-backslash", "backslash-then-slash",
        "nt-object-unc", "nt-object-globalroot", "nt-object-forward-slashes"])
def test_rebuild_r2_a_network_gitdir_in_either_slash_order_is_never_touched(tmp_path, gitdir):
    """R-092, TASK-072 (handoff/TASK-072-r2.md, correction 3: a `gitdir:` value beginning with two slashes or two
    backslashes, in either order of slash, is read as no git folder before any os.path call touches it, so that
    reading the row never opens a network connection): the security audit of the native rebuild, round 1. The
    check runs under a runner that refuses, and reports, any filesystem call, file open or git launch naming the
    value's host (nohost.invalid, which no resolver answers); the row is NOTE, the repository having no git folder
    of its own. The rebuild's round 1 refused only `//` and two backslashes, so the two mixed orders reached
    os.lstat (on Windows a network share). The rebuild's round 2 refused those, but a value in the NT object
    manager's form (`\\??\\UNC\\<host>\\...`, `\\??\\GLOBALROOT\\Device\\Mup\\...`) is absolute to Python 3.12's
    ntpath.isabs and reached os.lstat raw, which hands it to the object manager, a network share again (the
    security audit, rebuild round 2); it is refused too, in either slash, on every platform."""
    ws = make_project(tmp_path, gate("--lockfile='requirements.txt:requirements.lock'"))
    os.rename(os.path.join(str(ws), ".git"), str(tmp_path / "old-git"))
    put(ws, ".git", "gitdir: " + gitdir + "\n")
    runner = tmp_path / "guard_runner.py"
    runner.write_text(GUARD_RUNNER, encoding="utf-8")
    kw = suite_conftest.windowless_kwargs({"capture_output": True, "text": True, "encoding": "utf-8",
                                           "errors": "replace", "timeout": 300})
    p = subprocess.run([sys.executable, str(runner), CONFORMANCE, str(ws), "--offline"], cwd=str(ws), **kw)
    out = p.stdout + p.stderr
    assert "TOUCHED-NETWORK-PATH" not in out, out
    status, _detail = weekly_row(out)
    assert status == "NOTE", out
