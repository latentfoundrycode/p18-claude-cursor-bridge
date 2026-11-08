"""TASK-048's successor, TASK-049 (R-060, D-002): the tabular records' headers read first.

The supervisor's acceptance tests, written before the checkpoint. Each record kind declares its table's shape in a
header (docs/BUILD_PLAN.md, TASK-049's Done when; docs/DESIGN.md, Change: release B2, the third kind):

- docs/INVENTORY.md (`record: inventory`): `reflected_through`, `development_data`, `tables` (the four sections, each
  `columns` and `key`), read first by inventory-check.py, its owning checker (`HEADER DISAGREES: columns`,
  `tables.<section>`, `development_data`, `reflected_through`, each a finding, exit 1), and by conformance-check.py,
  which trusts that check and reads the decision from the header; conformance-check's heading-word guess retired
  (reading (7));
- docs/REQUIREMENTS.md (`record: requirements`): `columns`, `roles` (id, status, evidence), `statuses` (exactly the four
  words or malformed), read first by completion-check.py, its owning checker (`HEADER DISAGREES: columns`,
  `roles.<role>`), the rows split by the declared columns and read by role, and by diagram-check.py, which traces the
  R-ids of the id column, its whole-text R_RX over the register retired (reading (9)); parse_register moved into
  bridge_env;
- docs/diagrams/INDEX.md (`record: diagram-index`): `columns`, `roles`, read first by diagram-check.py, its owning
  checker, and by plan-check.py (id and status by role), plan-check's column-position read retired (reading (8));
- docs/diagrams/DEVIATIONS.md (`record: deviations`): `columns`, `roles`, read first by diagram-check.py;
- every program: `HEADER MALFORMED: <path>:<line> <what>` and exit 2 on a malformed header (a `roles` value naming a
  column absent from the header's own `columns` among the malformed cases); a file with no header reads as today.

The fallback's `Reflected through:` value is the line's marker as inventory-check reads it today
(`Reflected through: none` reads `"none"`); a file with no such line reads null.
"""
import ast
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge_env  # noqa: E402
from test_conformance_check import INVENTORY, make_workspace  # noqa: E402

PROGS = {name: os.path.join(BRIDGE, name) for name in (
    "inventory-check.py", "conformance-check.py", "completion-check.py", "diagram-check.py", "plan-check.py")}
DASH = "—"


def need(name):
    obj = getattr(bridge_env, name, None)
    assert obj is not None, "bridge_env.%s is missing (TASK-049)" % name
    return obj


def run(prog, cwd, *args):
    p = subprocess.run([sys.executable, PROGS[prog]] + [str(a) for a in args], cwd=str(cwd), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=300,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout + p.stderr


def answer(out):
    """The output without its note lines, so a header run and a header-less run can be compared."""
    return [l for l in out.splitlines() if l.strip() and not l.startswith("note:")]


def disagrees(out):
    return re.findall(r"^HEADER DISAGREES: (\S+)", out, re.M)


def q(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def flow(items):
    return "[" + ", ".join(q(x) for x in items) + "]"


def write(path, text):
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(str(path), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def malformed_line(text):
    """The line read_header names for a block it refuses, or 1 for a schema fault."""
    try:
        bridge_env.read_header(text)
    except bridge_env.HeaderError as err:
        return err.line
    return 1


def assert_malformed(rc, out, rel, text):
    m = re.search(r"HEADER MALFORMED: (?:\S*/)?%s:(\d+) \S" % re.escape(rel), out)
    assert rc == 2 and m and int(m.group(1)) == malformed_line(text), (rc, out)


# ---------------------------------------------------------------- the inventory

INV_TABLES = [
    ("features", ["Feature", "What it does", "Where", "Tests", "Since"], "Feature"),
    ("resources", ["Name", "Kind", "Where it lives", "Used by", "Provided"], "Name"),
    ("decisions", ["Decision", "Reason", "Settled", "Revisit only if"], "Decision"),
    ("deferred", ["Item", "Why deferred", "Since", "Owner decision needed"], "Item"),
]
DEV_DATA = ("Development data: a development build reads `data/dev.sqlite`, chosen by the `APP_ENV=dev` marker, "
            "and refuses the installed product's store")


def inventory_header(reflected="none", dev=DEV_DATA, tables=None, drop=None, replace=None):
    lines = ["---", "record: inventory", "header: 1",
             "reflected_through: %s" % ("null" if reflected is None else q(reflected)),
             "development_data: %s" % q(dev), "tables:"]
    for name, cols, key in (tables or INV_TABLES):
        if name == drop:
            continue
        lines += ["  %s:" % name, "    columns: %s" % flow(cols), "    key: %s" % q(key)]
    lines.append("---")
    text = "\n".join(lines) + "\n"
    if replace:
        assert replace[0] in text
        text = text.replace(replace[0], replace[1], 1)
    return text


def inventory_ws(tmp_path, header_text=None, body=INVENTORY):
    ws = tmp_path / "ws"
    write(ws / "docs" / "INVENTORY.md", (header_text or "") + body)
    return ws


def conformance_ws(tmp_path, header_text=None, body=INVENTORY):
    ws = tmp_path / "proj" / "Workspace"
    make_workspace(ws)
    write(ws / "docs" / "INVENTORY.md", (header_text or "") + body)
    return ws


def conformance(ws):
    return run("conformance-check.py", ws, str(ws), "--offline")


def floor(out, name):
    for line in out.splitlines():
        m = re.match(r"\s+(OK|MISSING|NOTE)\s+(.*)$", line)
        if m and m.group(2).startswith(name):
            return m.group(1)
    return None


def test_r060_inventory_check_reads_an_agreeing_header_as_its_prose(tmp_path):
    rc_p, out_p = run("inventory-check.py", inventory_ws(tmp_path / "p"))
    rc_h, out_h = run("inventory-check.py", inventory_ws(tmp_path / "h", inventory_header()))
    assert rc_p == 0 and rc_h == 0 and answer(out_h) == answer(out_p) and not disagrees(out_h), (out_p, out_h)


def test_r060_inventory_check_fails_a_declared_column_the_table_lacks(tmp_path):
    cols = [(n, c + ["Owner"] if n == "features" else c, k) for n, c, k in INV_TABLES]
    ws = inventory_ws(tmp_path, inventory_header(tables=cols))
    rc, out = run("inventory-check.py", ws)
    assert rc == 1 and disagrees(out) == ["columns"], out


def test_r060_inventory_check_fails_a_declared_section_the_file_lacks(tmp_path):
    body = INVENTORY.split("## Deferred")[0]
    ws = inventory_ws(tmp_path, inventory_header(), body=body)
    rc, out = run("inventory-check.py", ws)
    assert rc == 1 and "tables.deferred" in disagrees(out), out


def test_r060_an_inventory_header_lacking_a_section_is_malformed(tmp_path):
    text = inventory_header(drop="deferred")
    ws = inventory_ws(tmp_path, text)
    rc, out = run("inventory-check.py", ws)
    assert_malformed(rc, out, "docs/INVENTORY.md", text + INVENTORY)


def test_r060_inventory_check_fails_a_development_data_that_differs_from_its_row(tmp_path):
    ws = inventory_ws(tmp_path, inventory_header(dev="Development data: none, the product keeps no data"))
    rc, out = run("inventory-check.py", ws)
    assert rc == 1 and disagrees(out) == ["development_data"], out


def test_r060_inventory_check_fails_a_reflected_through_that_differs_from_its_line(tmp_path):
    ws = inventory_ws(tmp_path, inventory_header(reflected="## 2026-10-01"))
    rc, out = run("inventory-check.py", ws)
    assert rc == 1 and disagrees(out) == ["reflected_through"], out


def test_r060_no_reflected_through_line_reads_null(tmp_path):
    body = INVENTORY.replace("Reflected through: none\n", "")
    ws = inventory_ws(tmp_path, inventory_header(reflected=None), body=body)
    rc, out = run("inventory-check.py", ws)
    assert "reflected_through" not in disagrees(out), out


def test_r060_conformance_check_trusts_the_inventory_check_on_a_column(tmp_path):
    cols = [(n, c + ["Owner"] if n == "features" else c, k) for n, c, k in INV_TABLES]
    rc_p, out_p = conformance(conformance_ws(tmp_path / "p"))
    rc_h, out_h = conformance(conformance_ws(tmp_path / "h", inventory_header(tables=cols)))
    assert rc_h == rc_p == 0 and "HEADER" not in out_h, out_h


def test_r060_conformance_check_reads_the_development_data_decision_from_the_header(tmp_path):
    rc_p, out_p = conformance(conformance_ws(tmp_path / "p"))
    rc_h, out_h = conformance(conformance_ws(tmp_path / "h", inventory_header(dev="")))
    assert floor(out_p, "Development data kept apart") == "OK", out_p      # precondition: the row is there
    assert floor(out_h, "Development data kept apart") == "MISSING" and rc_h == 1, out_h


def test_r060_conformance_check_reads_an_agreeing_header_as_its_prose(tmp_path):
    rc_p, out_p = conformance(conformance_ws(tmp_path / "p"))
    rc_h, out_h = conformance(conformance_ws(tmp_path / "h", inventory_header()))
    assert rc_p == rc_h == 0 and answer(out_h)[1:] == answer(out_p)[1:], (out_p, out_h)   # the first line names the folder


@pytest.mark.parametrize("prog", ["inventory-check.py", "conformance-check.py"], ids=["inventory-check", "conformance-check"])
def test_r060_a_malformed_inventory_header_is_refused(tmp_path, prog):
    text = inventory_header(replace=("header: 1", "header:\t1"))
    if prog == "inventory-check.py":
        ws = inventory_ws(tmp_path, text)
        rc, out = run(prog, ws)
    else:
        ws = conformance_ws(tmp_path, text)
        rc, out = conformance(ws)
    assert_malformed(rc, out, "docs/INVENTORY.md", text + INVENTORY)


# ---------------------------------------------------------------- the register

REG_COLS = ["ID", "Requirement", "Source", "Status", "Evidence"]
REG_ROLES = {"id": "ID", "status": "Status", "evidence": "Evidence"}
STATUSES = ["planned", "built", "deferred", "dropped"]


def register_header(columns=REG_COLS, roles=None, statuses=STATUSES):
    lines = ["---", "record: requirements", "header: 1", "columns: %s" % flow(columns), "roles:"]
    lines += ["  %s: %s" % (k, q(v)) for k, v in (roles or REG_ROLES).items()]
    lines += ["statuses: %s" % flow(statuses), "---"]
    return "\n".join(lines) + "\n"


def register_body(columns=REG_COLS, extra_prose=""):
    rows = {"ID": ["R-001", "R-002"], "Requirement": ["the thing", "the other thing"], "Source": ["owner", "owner"],
            "Status": ["planned", "planned"], "Evidence": [DASH, DASH]}
    out = ["# Requirements", "", "Rows R-001 and R-002." + extra_prose, "",
           "| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for i in range(2):
        out.append("| " + " | ".join(rows[c][i] for c in columns) + " |")
    return "\n".join(out) + "\n"


PLAN = ("# Build plan\n\n## Stage 1\nDemonstration: it runs.\n\n### TASK-001 %s the thing\nKind: increment\n"
        "Parallel: no\nScope: src/a.py\nSatisfies: R-001, R-002\n" % DASH)


def register_ws(tmp_path, header_text=None, body=None):
    ws = tmp_path / "ws"
    write(ws / "docs" / "REQUIREMENTS.md", (header_text or "") + (body or register_body()))
    write(ws / "docs" / "BUILD_PLAN.md", PLAN)
    return ws


def completion(ws):
    return run("completion-check.py", ws, "--mode", "plan")


def test_r060_completion_check_reads_an_agreeing_header_as_its_prose(tmp_path):
    rc_p, out_p = completion(register_ws(tmp_path / "p"))
    rc_h, out_h = completion(register_ws(tmp_path / "h", register_header()))
    assert rc_p == rc_h == 0 and answer(out_h) == answer(out_p) and not disagrees(out_h), (out_p, out_h)


def test_r060_completion_check_splits_the_rows_by_the_declared_columns(tmp_path):
    cols = ["ID", "Status", "Requirement", "Source", "Evidence"]
    rc_p, out_p = completion(register_ws(tmp_path / "p", body=register_body(cols)))
    rc_h, out_h = completion(register_ws(tmp_path / "h", register_header(cols), register_body(cols)))
    assert rc_p == 1, out_p                                    # precondition: by position the order is refused
    assert rc_h == 0 and "RESULT: OK" in out_h, out_h


def test_r060_completion_check_fails_a_declared_column_the_table_lacks(tmp_path):
    ws = register_ws(tmp_path, register_header(REG_COLS + ["Owner"]))
    rc, out = completion(ws)
    assert rc == 1 and disagrees(out) == ["columns"], out


def test_r060_completion_check_fails_a_role_column_absent_from_the_table(tmp_path):
    cols = ["ID", "Requirement", "Source", "Status"]
    ws = register_ws(tmp_path, register_header(REG_COLS), register_body(cols))
    rc, out = completion(ws)
    assert rc == 1 and sorted(disagrees(out)) == ["columns", "roles.evidence"], out


def test_r060_a_role_naming_a_column_outside_the_headers_columns_is_malformed(tmp_path):
    text = register_header(roles={"id": "ID", "status": "State", "evidence": "Evidence"})
    ws = register_ws(tmp_path, text)
    rc, out = completion(ws)
    assert_malformed(rc, out, "docs/REQUIREMENTS.md", text + register_body())


@pytest.mark.parametrize("statuses", [STATUSES + ["waiting"], STATUSES[:3]], ids=["a-fifth-word", "three-words"])
def test_r060_a_statuses_list_other_than_the_four_words_is_malformed(tmp_path, statuses):
    text = register_header(statuses=statuses)
    ws = register_ws(tmp_path, text)
    rc, out = completion(ws)
    assert_malformed(rc, out, "docs/REQUIREMENTS.md", text + register_body())


def test_r060_a_status_cell_with_another_word_is_the_register_checks_finding(tmp_path):
    body = register_body().replace("| R-002 | the other thing | owner | planned |", "| R-002 | the other thing | owner | waiting |")
    ws = register_ws(tmp_path, register_header(), body)
    rc, out = completion(ws)
    assert rc == 1 and re.search(r"^REGISTER: R-002 has status 'waiting'", out, re.M) and not disagrees(out), out


def test_r060_parse_register_lives_in_bridge_env():
    parse = need("parse_register")
    header, rows = parse(register_body())
    assert [r[0] for r in rows] == ["R-001", "R-002"] and len(header) == 5, (header, rows)


# ---------------------------------------------------------------- the index, the register's R-ids, the deviations

IDX_COLS = ["ID", "Level", "Kind", "Status", "File", "Refines", "Realizes", "Enforced by", "Why"]
IDX_ROLES = {"id": "ID", "level": "Level", "kind": "Kind", "status": "Status", "file": "File", "refines": "Refines",
             "realizes": "Realizes", "enforced_by": "Enforced by", "why": "Why"}
DEV_COLS = ["Diagram", "From", "To", "As built", "Since", "Resolved by"]
DEV_ROLES = {"diagram": "Diagram", "from": "From", "to": "To", "as_built": "As built", "since": "Since",
             "resolved_by": "Resolved by"}


def roles_header(kind, columns, roles):
    lines = ["---", "record: %s" % kind, "header: 1", "columns: %s" % flow(columns), "roles:"]
    lines += ["  %s: %s" % (k, q(v)) for k, v in roles.items()]
    lines.append("---")
    return "\n".join(lines) + "\n"


def read_repo(rel):
    with open(os.path.join(ROOT, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


def swap_columns(text, i, j):
    """Every table line of text with its cells i and j exchanged."""
    out = []
    for line in text.split("\n"):
        if line.startswith("|"):
            cells = line.strip().strip("|").split("|")
            cells[i], cells[j] = cells[j], cells[i]
            line = "|" + "|".join(cells) + "|"
        out.append(line)
    return "\n".join(out)


def diagrams_ws(tmp_path, index=None, register=None, deviations=None, plan=None):
    """A copy of this repository's diagrams, index and register (header-less today), each replaceable."""
    ws = tmp_path / "ws"
    shutil.copytree(os.path.join(ROOT, "docs", "diagrams"), str(ws / "docs" / "diagrams"))
    write(ws / "docs" / "REQUIREMENTS.md", register if register is not None else read_repo("docs/REQUIREMENTS.md"))
    if index is not None:
        write(ws / "docs" / "diagrams" / "INDEX.md", index)
    if deviations is not None:
        write(ws / "docs" / "diagrams" / "DEVIATIONS.md", deviations)
    if plan is not None:
        write(ws / "docs" / "BUILD_PLAN.md", plan)
    return ws


def diagram(ws, *args):
    return run("diagram-check.py", ws, *args)


def test_r060_diagram_check_reads_agreeing_headers_as_their_prose(tmp_path):
    reg_cols = REG_COLS
    rc_p, out_p = diagram(diagrams_ws(tmp_path / "p"))
    ws = diagrams_ws(tmp_path / "h", index=roles_header("diagram-index", IDX_COLS, IDX_ROLES) + read_repo("docs/diagrams/INDEX.md"),
                     register=register_header(reg_cols) + read_repo("docs/REQUIREMENTS.md"))
    rc_h, out_h = diagram(ws)
    assert rc_p == rc_h == 0 and answer(out_h) == answer(out_p) and not disagrees(out_h), (out_p, out_h)


def test_r060_diagram_check_fails_a_declared_index_column_the_table_lacks(tmp_path):
    index = roles_header("diagram-index", IDX_COLS + ["Owner"], IDX_ROLES) + read_repo("docs/diagrams/INDEX.md")
    rc, out = diagram(diagrams_ws(tmp_path, index=index))
    assert rc == 1 and disagrees(out) == ["columns"], out


def test_r060_diagram_check_trusts_the_completion_check_on_a_register_column(tmp_path):
    register = register_header(REG_COLS + ["Owner"]) + read_repo("docs/REQUIREMENTS.md")
    rc, out = diagram(diagrams_ws(tmp_path, register=register))
    assert rc == 0 and "HEADER" not in out, out


@pytest.mark.parametrize("headed", [False, True], ids=["header-less", "headed"])
def test_r060_an_r_id_in_the_registers_prose_is_counted_by_nothing(tmp_path, headed):
    register = "\n".join(l for l in read_repo("docs/REQUIREMENTS.md").split("\n") if not l.startswith("| R-064 |"))
    assert "R-064" in register                                # the prose still names it (rows R-057 to R-064)
    if headed:
        register = register_header() + register
    rc, out = diagram(diagrams_ws(tmp_path, register=register))
    assert rc == 1 and re.search(r"^TRACE: .*R-064", out, re.M), out


def test_r060_diagram_check_reads_the_deviations_by_their_declared_columns(tmp_path):
    cols = ["From", "Diagram", "To", "As built", "Since", "Resolved by"]
    body = ("# Known deviations\n\n| " + " | ".join(cols) + " |\n|---|---|---|---|---|---|\n"
            "| hooks | D-002 | bridge_env | imports by file | 2026-11-01 | TASK-099 |\n")
    ws = diagrams_ws(tmp_path, deviations=roles_header("deviations", cols, DEV_ROLES) + body)
    rc, out = diagram(ws, "--mode", "code")
    assert re.search(r"^note: 1 known deviation\(s\) listed", out, re.M), out


def test_r060_diagram_check_fails_a_declared_deviations_column_the_table_lacks(tmp_path):
    deviations = roles_header("deviations", DEV_COLS + ["Owner"], DEV_ROLES) + read_repo("docs/diagrams/DEVIATIONS.md")
    rc, out = diagram(diagrams_ws(tmp_path, deviations=deviations), "--mode", "code")
    assert rc == 1 and disagrees(out) == ["columns"], out


PLAN_D = ("# Build plan\n\n## Stage 1\nDemonstration: it runs.\n\n### TASK-001 %s the thing\nKind: increment\n"
          "Parallel: no\nDiagrams: %%s\nScope: src/a.py\nSatisfies: R-001\n" % DASH)


def plan_check(ws):
    return run("plan-check.py", ws, "--no-git")


def test_r060_plan_check_reads_the_index_status_by_role(tmp_path):
    index = swap_columns(read_repo("docs/diagrams/INDEX.md"), 2, 3)          # Status before Kind
    cols = ["ID", "Level", "Status", "Kind", "File", "Refines", "Realizes", "Enforced by", "Why"]
    rc_p, out_p = plan_check(diagrams_ws(tmp_path / "p", index=index, plan=PLAN_D % "D-002"))
    assert re.search(r"^DIAGRAMS: TASK-001 names D-002", out_p, re.M), out_p   # precondition: by position it is lost
    ws = diagrams_ws(tmp_path / "h", index=roles_header("diagram-index", cols, IDX_ROLES) + index, plan=PLAN_D % "D-002")
    rc_h, out_h = plan_check(ws)
    assert rc_h == 0 and not re.search(r"^DIAGRAMS:", out_h, re.M), out_h


def test_r060_plan_check_reads_the_index_table_not_every_line(tmp_path):
    index = read_repo("docs/diagrams/INDEX.md").rstrip("\n") + "\n\nA later note quotes a row:\n\n| D-009 | 3 | component | selected | x |\n"
    rc, out = plan_check(diagrams_ws(tmp_path, index=index, plan=PLAN_D % "D-009"))
    assert rc == 1 and re.search(r"^DIAGRAMS: TASK-001 names D-009", out, re.M), out


def test_r060_plan_check_trusts_the_diagram_check_on_an_index_column(tmp_path):
    index = roles_header("diagram-index", IDX_COLS + ["Owner"], IDX_ROLES) + read_repo("docs/diagrams/INDEX.md")
    rc, out = plan_check(diagrams_ws(tmp_path, index=index, plan=PLAN_D % "D-002"))
    assert rc == 0 and "HEADER" not in out, out


BAD_ROLES = {"index": ("diagram-index", IDX_COLS, dict(IDX_ROLES, why="Reason"), "docs/diagrams/INDEX.md"),
             "deviations": ("deviations", DEV_COLS, dict(DEV_ROLES, since="When"), "docs/diagrams/DEVIATIONS.md"),
             "register": ("requirements", REG_COLS, dict(REG_ROLES, evidence="Proof"), "docs/REQUIREMENTS.md")}


@pytest.mark.parametrize("prog,record,args", [
    ("diagram-check.py", "index", []),
    ("diagram-check.py", "register", []),
    ("diagram-check.py", "deviations", ["--mode", "code"]),
    ("plan-check.py", "index", ["--no-git"]),
], ids=["diagram-check-index", "diagram-check-register", "diagram-check-deviations", "plan-check-index"])
def test_r060_a_malformed_table_header_is_refused(tmp_path, prog, record, args):
    kind, cols, roles, rel = BAD_ROLES[record]
    if kind == "requirements":
        text = register_header(cols, roles)
    else:
        text = roles_header(kind, cols, roles)
    full = text + read_repo(rel)
    ws = diagrams_ws(tmp_path, plan=PLAN_D % "D-002")
    write(ws / rel, full)
    rc, out = run(prog, ws, *args)
    assert_malformed(rc, out, rel, full)


# ---------------------------------------------------------------- the retired readings, matched as uses

def code_tree(prog):
    """The program's syntax tree with its docstrings removed, so a comment or a docstring naming a reading never matches."""
    with open(PROGS[prog], encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) and isinstance(
                getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
            body.pop(0)
    return tree


def re_patterns(tree):
    """The constant first arguments of re.<function>(...) calls."""
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) \
                and n.func.value.id == "re" and n.args and isinstance(n.args[0], ast.Constant):
            out.add(n.args[0].value)
    return out


def test_r060_conformance_check_keeps_no_heading_word_guess():
    assert r"^##\s+(\w+)" not in re_patterns(code_tree("conformance-check.py"))


def test_r060_diagram_check_reads_no_r_id_from_the_whole_register():
    found = []
    for n in ast.walk(code_tree("diagram-check.py")):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("findall", "finditer", "search") \
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "R_RX" and n.args \
                and isinstance(n.args[0], ast.Call) and isinstance(n.args[0].func, ast.Name) and n.args[0].func.id == "read":
            found.append(n.lineno)
    assert not found, "diagram-check.py reads R-ids from a whole file at line(s) %s" % found


# ---------------------------------------------------------------- builder's cases below this line
