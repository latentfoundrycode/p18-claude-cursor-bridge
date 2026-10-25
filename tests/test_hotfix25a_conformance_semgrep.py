"""Hotfix 2026.10.25a, conformance-check.py and semgrep-bridge-rules.yml.

2026-10-18 C6 (the TDP's FB-006 (3)): an inventory row whose environment-variable mention is
negated ("never an environment variable the owner sets") is not a supply-by-environment row.
2026-10-25 C9 (ISS-005, ISS-010, FB-007, FB-025, FB-026, FB-031): the boundary-check hook is a
NOTE (configured, not engaging) until this computer's probe record says it fired; the hook
without its log's ignore line, `socket ci` without `--no-banner`, the Socket CLI installed in the
step that holds the key, and an absolute path in a tracked status file are MISSING.
2026-10-18 C5 (entry 26): the SQL-concatenation rules match both operand orders, spare only a
literal pair at the top of the argument, spare a literal-only `executemany` as `execute`, and the
header claims no more than the rules and the packs do; planted probes run where Semgrep is on PATH."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_conformance_check import GATE, make_workspace, run, verdict  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "semgrep-bridge-rules.yml")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
IGNORE_LOG = "docs/BOUNDARY_VIOLATIONS.md\n"


def workspace(root):
    """The conformant fixture, with the two lines this hotfix requires written here, so the
    test does not rest on the shared fixture's version."""
    make_workspace(root)
    (root / ".gitignore").write_text(IGNORE_LOG, encoding="utf-8")
    (root / ".github" / "workflows" / "ci.yml").write_text(re.sub(r"npx socket@1\.2\.3 ci\b(?! --no-banner)", "npx socket@1.2.3 ci --no-banner", GATE), encoding="utf-8")


# --- 2026-10-18 C6: a negated environment-variable mention

def test_a_negated_environment_variable_mention_is_not_supply_by_environment(tmp_path):
    workspace(tmp_path)
    (tmp_path / "docs" / "INVENTORY.md").write_text(
        "## Resources\n"
        "| Name | Kind | Where | Used by | Since |\n|---|---|---|---|---|\n"
        "| OPENROUTER_API_KEY | secret | key file outside the Workspace (TASK-164), never an environment variable the owner sets | app/llm.py | 2026-10-11 |\n"
        "| HF_TOKEN | secret | the app's encrypted store, not through an environment variable | app/hf.py | 2026-10-11 |\n"
        "| BFL_API_KEY | secret | key file; no longer an env var since TASK-164 | app/bfl.py | 2026-10-11 |\n", encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "No secret through an environment variable")
    assert v == "OK", "a negated mention says the key does NOT arrive through a variable (TDP FB-006 (3)): %s" % line


def test_a_plain_mention_beside_a_negation_still_counts(tmp_path):
    workspace(tmp_path)
    (tmp_path / "docs" / "INVENTORY.md").write_text(
        "## Resources\n"
        "| Name | Kind | Where | Used by | Since |\n|---|---|---|---|---|\n"
        "| OPENROUTER_API_KEY | secret | key file outside the Workspace, never an environment variable the owner sets | app/llm.py | 2026-10-11 |\n"
        "| MODAL_TOKEN_SECRET | secret | user env var, not the key file | app/modal.py | 2026-10-11 |\n"
        "| STRIPE_SECRET_KEY | secret | not the key file but an environment variable | app/pay.py | 2026-10-11 |\n", encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "No secret through an environment variable")
    assert v == "MISSING" and "MODAL_TOKEN_SECRET" in line and "STRIPE_SECRET_KEY" in line, line
    assert "OPENROUTER_API_KEY" not in line, line


# --- 2026-10-25 C9: the boundary-check floor

def test_the_boundary_hook_is_a_note_until_a_probe_record_says_it_fired(tmp_path, home_of_the_tests):
    workspace(tmp_path)
    rc, out = run(tmp_path, home=home_of_the_tests)
    v, line = verdict(out, "Boundary-check hook")
    assert v == "NOTE", "configured is not engaging (ISS-010): %s" % line
    assert "configured, not engaging" in line and "headless builder run on this computer" in line, line
    assert "BOUNDARY on stderr" in line and "before-and-after listing" in line, "the NOTE names the detector that works: " + line
    probe = home_of_the_tests / ".cursor-bridge" / "boundary-probe.json"
    probe.parent.mkdir()
    probe.write_text(json.dumps({"fired": False, "when": "2026-10-19T10:00:00Z", "launch": "bridge-run.py from Git Bash"}), encoding="utf-8")
    rc, out = run(tmp_path, home=home_of_the_tests)
    assert verdict(out, "Boundary-check hook")[0] == "NOTE", "a record that says it did not fire is not a firing"
    probe.write_text("{not json", encoding="utf-8")
    rc, out = run(tmp_path, home=home_of_the_tests)
    assert verdict(out, "Boundary-check hook")[0] == "NOTE"
    probe.write_text(json.dumps({"fired": True, "when": "2026-10-26T09:00:00Z", "launch": "bridge-run.py from Git Bash"}), encoding="utf-8")
    rc, out = run(tmp_path, home=home_of_the_tests)
    v, line = verdict(out, "Boundary-check hook")
    assert v == "OK" and "2026-10-26T09:00:00Z" in line and "bridge-run.py from Git Bash" in line, line
    assert rc == 0, out


def test_the_boundary_hook_without_its_log_ignored_is_missing(tmp_path):
    workspace(tmp_path)
    (tmp_path / ".gitignore").write_text("node_modules/\nrun/\n", encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "Boundary log ignored")
    assert rc == 1 and v == "MISSING" and "docs/BOUNDARY_VIOLATIONS.md" in line and "absolute paths" in line, out
    (tmp_path / ".gitignore").write_text("node_modules/\nrun/\n/docs/BOUNDARY_VIOLATIONS.md\n", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Boundary log ignored")[0] is None, out
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, creationflags=NO_WINDOW)      # in a repository, git decides
    (tmp_path / ".gitignore").write_text("docs/*.log\n", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Boundary log ignored")[0] == "MISSING", out
    (tmp_path / ".gitignore").write_text("**/BOUNDARY_*.md\n", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Boundary log ignored")[0] is None, out
    (tmp_path / ".cursor" / "hooks.json").write_text('{"hooks": ["windowless-check.py"]}', encoding="utf-8")
    (tmp_path / ".gitignore").write_text("", encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Boundary-check hook")[0] == "MISSING" and verdict(out, "Boundary log ignored")[0] is None, "no hook, no log to ignore"


# --- 2026-10-25 C9: the Socket step

def test_socket_ci_without_no_banner_is_missing(tmp_path):
    workspace(tmp_path)
    assert verdict(run(tmp_path)[1], "Socket runs without its banner")[0] is None
    gate = GATE.replace(" --no-banner", "")                     # the gate's Socket step as 2026.10.18a's fixture wrote it
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(gate, encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "Socket runs without its banner")
    assert rc == 1 and v == "MISSING" and "--no-banner" in line and "ISS-005" in line, out
    for form in ("npx @socketsecurity/cli@1.7.0 ci", "socket ci --repo x", "socket --config .socket.yml ci"):
        (tmp_path / ".github" / "workflows" / "ci.yml").write_text(gate.replace("npx socket@1.2.3 ci", form), encoding="utf-8")
        assert verdict(run(tmp_path)[1], "Socket runs without its banner")[0] == "MISSING", form
    block = gate.replace("      - name: socket\n        run: npx socket@1.2.3 ci\n",
                         "      - name: socket\n        run: |\n          socket ci \\\n            --no-banner\n")
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(block, encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Socket in the gate")[0] == "OK" and verdict(out, "Socket runs without its banner")[0] is None, "a continued line carries the flag: " + out


INSTALL_WITH_KEY = """name: gate
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
        env:
          SOCKET_SECURITY_API_KEY: ${{ secrets.SOCKET_SECURITY_API_KEY }}
        run: npm install -g @socketsecurity/cli@1.7.0 --ignore-scripts && socket ci --no-banner
      - run: npx impeccable@3.3.0 detect --json docs/mockups
"""

INSTALL_APART = INSTALL_WITH_KEY.replace(
    """      - name: socket
        env:
          SOCKET_SECURITY_API_KEY: ${{ secrets.SOCKET_SECURITY_API_KEY }}
        run: npm install -g @socketsecurity/cli@1.7.0 --ignore-scripts && socket ci --no-banner
""", """      - name: install socket
        run: npm install -g @socketsecurity/cli@1.7.0 --ignore-scripts
      - name: socket
        env:
          SOCKET_SECURITY_API_KEY: ${{ secrets.SOCKET_SECURITY_API_KEY }}
        run: socket ci --no-banner
""")


def test_the_socket_cli_installed_in_the_step_that_holds_the_key_is_missing(tmp_path):
    workspace(tmp_path)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(INSTALL_WITH_KEY, encoding="utf-8")
    rc, out = run(tmp_path)
    v, line = verdict(out, "Socket CLI installed without the key")
    assert rc == 1 and v == "MISSING" and "FB-007" in line and "--ignore-scripts" in line, out
    for name in ("SOCKET_CLI_API_TOKEN", "SOCKET_API_KEY"):
        (tmp_path / ".github" / "workflows" / "ci.yml").write_text(INSTALL_WITH_KEY.replace("SOCKET_SECURITY_API_KEY:", name + ":"), encoding="utf-8")
        assert verdict(run(tmp_path)[1], "Socket CLI installed without the key")[0] == "MISSING", name
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(INSTALL_APART, encoding="utf-8")
    rc, out = run(tmp_path)
    assert verdict(out, "Socket CLI installed without the key")[0] is None and verdict(out, "Socket in the gate")[0] == "OK", out
    assert rc == 0, out


# --- 2026-10-25 C9: no computer path in the status file

def test_an_absolute_path_in_a_tracked_status_file_is_missing(tmp_path):
    workspace(tmp_path)
    status = tmp_path / "docs" / "PROJECT_STATUS.md"
    base = status.read_text(encoding="utf-8")
    assert verdict(run(tmp_path)[1], "No computer path in the status file")[0] is None
    for layout in ("Layout: Workspace=E:\\p18\\Workspace  Documents=E:\\p18\\Documents", "Layout: Workspace=C:/Users/owner/p18/Workspace",
                   "Layout: Workspace=/Users/owner/p18/Workspace", "Layout: Workspace=/home/owner/p18/Workspace"):
        status.write_text(base + layout + "\n", encoding="utf-8")
        rc, out = run(tmp_path)
        v, line = verdict(out, "No computer path in the status file")
        assert rc == 1 and v == "MISSING" and "line(s) 4" in line and "FB-026" in line, (layout, out)
        assert "owner" not in line and "p18" not in line, "the line number is named, not the path"
    status.write_text(base + "Layout: Workspace=Workspace/  Documents=Documents/  (see https://github.com/x/y)\n", encoding="utf-8")
    assert verdict(run(tmp_path)[1], "No computer path in the status file")[0] is None, "relative folders and a URL are not computer paths"
    status.write_text(base + "Layout: Workspace=E:\\p18\\Workspace\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, creationflags=NO_WINDOW)
    assert verdict(run(tmp_path)[1], "No computer path in the status file")[0] is None, "an untracked status file reaches no commit"
    subprocess.run(["git", "add", "docs/PROJECT_STATUS.md"], cwd=tmp_path, check=True, creationflags=NO_WINDOW)
    assert verdict(run(tmp_path)[1], "No computer path in the status file")[0] == "MISSING", "tracked once added"


# --- 2026-10-18 C5: the bridge's Semgrep rules

def rules():
    with open(RULES, encoding="utf-8") as f:
        text = f.read()
    return text, {r["id"]: r for r in yaml.safe_load(text)["rules"]}


def test_the_rules_parse_and_their_exclusions_are_top_level_at_every_sink():
    text, by_id = rules()
    for rid in ("bridge-sql-string-concat-js", "bridge-sql-string-concat-py"):
        pats = by_id[rid]["patterns"]
        either = [alt["pattern"] for p in pats if "pattern-either" in p for alt in p["pattern-either"]]
        nots = [p["pattern-not"] for p in pats if "pattern-not" in p]
        assert any('"..." + $X' in p for p in either) and any('$X + "..."' in p for p in either), (rid, "both operand orders")
        assert nots and all("<..." not in n for n in nots), (rid, "the exclusion is not a deep match: %s" % nots)
    py = by_id["bridge-sql-string-concat-py"]["patterns"]
    py_nots = [p["pattern-not"] for p in py if "pattern-not" in p]
    assert any(n.startswith("$CUR.executemany(") for n in py_nots) and any(n.startswith("$CUR.execute(") for n in py_nots), py_nots
    header = text.split("rules:", 1)[0]
    assert "do NOT catch string-concatenation" not in header, "the packs flag the Python case since 1.176.1"
    assert "JavaScript" in header and "executemany" in header and "do NOT catch" in header, "the header says what the rules catch and what they do not"


JS_PROBE = """function probes(db, x, rows) {
  db.query("SELECT * FROM t WHERE id=" + x);              // FLAG literal + value
  db.query(x + " OR 1=1");                                 // FLAG value + literal
  db.query("SELECT " + "* FROM t WHERE id=" + x);          // FLAG a literal pair, then a value
  db.execute("DELETE FROM t WHERE id=" + x, []);           // FLAG another sink
  db.all(rows.where + " ORDER BY id");                     // SPARE value + literal at a generic name (axios.get, Promise.all)
  axios.get(baseUrl + "/items");                           // SPARE the same shape outside SQL
  db.query("SELECT * " + "FROM t");                        // SPARE literals only
  db.query("SELECT * FROM t WHERE id = ?", [x]);           // SPARE parameterised
  db.run("INSERT INTO t VALUES (?)", [x]);                 // SPARE parameterised
}
"""

PY_PROBE = """def probes(cur, x, rows):
    cur.execute("SELECT * FROM t WHERE id=" + x)              # FLAG literal + value
    cur.execute(x + " OR 1=1")                                # FLAG value + literal
    cur.execute("SELECT " + "* FROM t WHERE id=" + x)         # FLAG a literal pair, then a value
    cur.executemany("INSERT INTO t VALUES (" + x + ")", rows) # FLAG executemany
    cur.executemany(x + " VALUES (?)", rows)                  # FLAG executemany, value + literal
    cur.execute("SELECT * FROM t WHERE id=%s" % x)            # FLAG %-formatting
    cur.execute(f"SELECT * FROM t WHERE id={x}")              # FLAG f-string
    cur.execute("SELECT * " + "FROM t")                       # SPARE literals only
    cur.executemany("INSERT INTO t " + "VALUES (?)", rows)    # SPARE literals only at executemany
    cur.execute("SELECT * FROM t WHERE id = ?", (x,))         # SPARE parameterised
"""


def semgrep_lines(tmp_path, name, source):
    """The lines the bridge rules flag in one planted probe file, by a local Semgrep run (no
    metrics, no version check: nothing leaves the computer)."""
    exe = shutil.which("semgrep")
    if not exe:
        pytest.skip("semgrep is not on PATH: the planted probes need the Semgrep CLI (the rules' text is checked above)")
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    (probe_dir / name).write_text(source, encoding="utf-8")
    env = dict(os.environ, SEMGREP_ENABLE_VERSION_CHECK="0", SEMGREP_SEND_METRICS="off")
    p = subprocess.run([exe, "scan", "--config", os.path.abspath(RULES), "--metrics=off", "--disable-version-check", "--json", "--quiet", str(probe_dir)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(tmp_path), timeout=300, creationflags=NO_WINDOW)
    data = json.loads(p.stdout)
    assert not data.get("errors"), data.get("errors")
    return sorted(r["start"]["line"] for r in data["results"] if r["check_id"].endswith(".bridge-sql-string-concat-" + ("js" if name.endswith(".js") else "py")))


def expected(source):
    return sorted(i for i, l in enumerate(source.splitlines(), 1) if "FLAG" in l)


def test_the_planted_javascript_probes(tmp_path):
    assert semgrep_lines(tmp_path, "probe.js", JS_PROBE) == expected(JS_PROBE)


def test_the_planted_python_probes(tmp_path):
    assert semgrep_lines(tmp_path, "probe.py", PY_PROBE) == expected(PY_PROBE)
