"""TASK-049 round 2 (R-060, D-002): the reviewers' findings on round 1, each reproduced before its fix.

The supervisor's reproduction tests, written before the round-2 brief:
- an agreeing inventory header with `reflected_through: null` keeps the header-less rule: `SHAPE: no 'Reflected
  through:' line`, the absorption check not silenced (Review A B1, the audit's B1);
- with a register header, every declared column's cell must be non-empty except the evidence role's, as the
  header-less rule `all(r[:4])` reads the standard order (Review A B2, the audit's B2);
- with a register header, the requirement's text is the first declared column that is no role's column
  (`Requirement` in the standard order), so UNPLANNED names it (Review A B3, the audit's B2);
- with an index header, diagram-check reads the rows of the body's first table by the declared columns, with no
  header-less first-word check, so a reordered declared index is read as plan-check reads it (Review A B4);
- one copy of each moved reading (Review A's should-fix 1): no section table, no `Reflected through:` pattern and
  no index first-word list kept in a program;
- known_deviations raises on a malformed header, never a silent empty set (should-fix 2, the audit's A4);
- inventory-check without a usable bridge_env and with no status file refuses without a traceback (should-fix 3,
  the audit's A2);
- conformance-check on its stand-in (no bridge_env.py beside it) gives no false verdict on the inventory's floors:
  both read not checked (should-fix 4, the audit's A1).
"""
import ast
import os
import re
import shutil

import pytest

import test_header_tables as th

be = th.bridge_env
run = th.run


# ---------------------------------------------------------------- B1: a null reflected_through keeps the rule

def test_r060_r2_a_null_reflected_through_keeps_the_missing_line_finding(tmp_path):
    body = th.INVENTORY.replace("Reflected through: none\n", "")
    rc_p, out_p = run("inventory-check.py", th.inventory_ws(tmp_path / "p", body=body))
    rc_h, out_h = run("inventory-check.py", th.inventory_ws(tmp_path / "h", th.inventory_header(reflected=None), body=body))
    assert rc_p == 1 and "SHAPE: no 'Reflected through:' line" in out_p, out_p      # precondition, as on main
    assert rc_h == 1 and th.answer(out_h) == th.answer(out_p), out_h


# ---------------------------------------------------------------- B2, B3: the register's rows under a header

@pytest.mark.parametrize("cell", ["Source", "Requirement"], ids=["source", "requirement"])
def test_r060_r2_a_headed_register_row_with_an_empty_cell_is_malformed(tmp_path, cell):
    old = "| R-002 | the other thing | owner | planned |"
    new = old.replace("| owner |", "|  |") if cell == "Source" else old.replace("| the other thing |", "|  |")
    body = th.register_body().replace(old, new)
    rc_p, out_p = th.completion(th.register_ws(tmp_path / "p", body=body))
    rc_h, out_h = th.completion(th.register_ws(tmp_path / "h", th.register_header(), body))
    assert rc_p == 1 and re.search(r"^REGISTER: malformed row: R-002", out_p, re.M), out_p
    assert rc_h == 1 and th.answer(out_h) == th.answer(out_p), out_h


def test_r060_r2_a_headed_register_names_the_requirement_in_its_findings(tmp_path):
    plan = th.PLAN.replace("Satisfies: R-001, R-002", "Satisfies: R-001")
    ws_p = th.register_ws(tmp_path / "p")
    ws_h = th.register_ws(tmp_path / "h", th.register_header())
    for ws in (ws_p, ws_h):
        th.write(ws / "docs" / "BUILD_PLAN.md", plan)
    rc_p, out_p = th.completion(ws_p)
    rc_h, out_h = th.completion(ws_h)
    assert re.search(r"^UNPLANNED: R-002 \(the other thing\)", out_p, re.M), out_p
    assert rc_h == rc_p and th.answer(out_h) == th.answer(out_p), out_h


def test_r060_r2_a_reordered_headed_register_names_its_requirement(tmp_path):
    cols = ["ID", "Status", "Requirement", "Source", "Evidence"]
    ws = th.register_ws(tmp_path, th.register_header(cols), th.register_body(cols))
    th.write(ws / "docs" / "BUILD_PLAN.md", th.PLAN.replace("Satisfies: R-001, R-002", "Satisfies: R-001"))
    rc, out = th.completion(ws)
    assert rc == 1 and re.search(r"^UNPLANNED: R-002 \(the other thing\)", out, re.M), out


# ---------------------------------------------------------------- B4: diagram-check reads a declared index by role

def test_r060_r2_diagram_check_reads_a_reordered_declared_index(tmp_path):
    index = th.swap_columns(th.read_repo("docs/diagrams/INDEX.md"), 2, 3)
    cols = ["ID", "Level", "Status", "Kind", "File", "Refines", "Realizes", "Enforced by", "Why"]
    rc_p, out_p = th.diagram(th.diagrams_ws(tmp_path / "p"))
    rc_h, out_h = th.diagram(th.diagrams_ws(tmp_path / "h", index=th.roles_header("diagram-index", cols, th.IDX_ROLES) + index))
    assert rc_p == 0, out_p
    assert rc_h == 0 and th.answer(out_h) == th.answer(out_p), out_h


# ---------------------------------------------------------------- one copy of each moved reading

def _tree(prog):
    return th.code_tree(prog)


def test_r060_r2_inventory_check_keeps_no_section_table_or_reflected_pattern():
    tree = _tree("inventory-check.py")
    pats = [p for p in th.re_patterns(tree) if isinstance(p, str) and "Reflected through" in p]
    names = sorted({t.id for n in ast.walk(tree) if isinstance(n, ast.Assign) for t in n.targets
                    if isinstance(t, ast.Name) and t.id == "SECTIONS" and isinstance(n.value, ast.Dict)})
    assert not pats and not names, (pats, names)


def test_r060_r2_diagram_check_keeps_no_index_first_word_list():
    want = ["id", "level", "kind", "status", "file", "refines", "realizes", "enforced", "why"]
    found = [n.lineno for n in ast.walk(_tree("diagram-check.py")) if isinstance(n, ast.List)
             and [getattr(e, "value", None) for e in n.elts] == want]
    assert not found, "diagram-check.py keeps the index's first-word list at line(s) %s" % found


# ---------------------------------------------------------------- no exception swallowed, no traceback, no false verdict

def _load(prog):
    import importlib.util
    spec = importlib.util.spec_from_file_location(prog.replace("-", "_")[:-3], th.PROGS[prog])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_r060_r2_known_deviations_raises_on_a_malformed_header(tmp_path):
    dc = _load("diagram-check.py")
    path = tmp_path / "DEVIATIONS.md"
    th.write(path, th.roles_header("deviations", th.DEV_COLS, dict(th.DEV_ROLES, since="When")) + th.read_repo("docs/diagrams/DEVIATIONS.md"))
    with pytest.raises(be.HeaderError):
        dc.known_deviations(str(path))


def test_r060_r2_inventory_check_without_bridge_env_refuses_without_a_traceback(tmp_path):
    lone = tmp_path / "lone"
    lone.mkdir()
    shutil.copyfile(th.PROGS["inventory-check.py"], str(lone / "inventory-check.py"))
    ws = th.inventory_ws(tmp_path)
    import subprocess
    import sys
    p = subprocess.run([sys.executable, str(lone / "inventory-check.py")], cwd=str(ws), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    out = p.stdout + p.stderr
    assert p.returncode == 2 and "Traceback" not in out and "bridge_env" in out, out


def test_r060_r2_conformance_check_on_its_stand_in_gives_no_false_inventory_verdict(tmp_path):
    lone = tmp_path / "lone"
    lone.mkdir()
    for name in os.listdir(th.BRIDGE):
        if name.endswith(".py") and name != "bridge_env.py":
            shutil.copyfile(os.path.join(th.BRIDGE, name), str(lone / name))
    ws = th.conformance_ws(tmp_path)
    import subprocess
    import sys
    p = subprocess.run([sys.executable, str(lone / "conformance-check.py"), str(ws), "--offline"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=300,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    out = p.stdout + p.stderr
    for name in ("Spending limit recorded", "Development data kept apart"):
        line = next((l for l in out.splitlines() if name in l), "")
        assert re.match(r"\s+MISSING\s", line) and "not checked" in line, (name, out)


# ---------------------------------------------------------------- A5 and SF-1b, added after round 2's review

def test_r060_r2_a_headed_inventory_reads_its_sections_from_the_body_alone(tmp_path):
    hdr = th.inventory_header(replace=("tables:", "## Features\ntables:"))
    rc, out = run("inventory-check.py", th.inventory_ws(tmp_path, hdr, body=""))
    assert rc == 1 and "SHAPE: section '## Features' missing" in out, out
    assert "has no table header" not in out, out


def test_r060_r2_the_headerless_index_reading_keeps_the_first_table_check():
    selected_ids = th.need("diagram_index_selected_ids")
    index = th.read_repo("docs/diagrams/INDEX.md")
    assert selected_ids(index, None), "precondition: the repository's index selects diagrams"
    renamed = re.sub(r"^\|\s*ID\s*\|", "| Diagram |", index, count=1, flags=re.M)
    assert renamed != index
    assert selected_ids(renamed, None) == set()


# ---------------------------------------------------------------- the mutation sweep's survivors on round 2, closed

def _block_fault(text):
    assert "header: 1" in text
    return text.replace("header: 1", "header:\t1", 1)


@pytest.mark.parametrize("prog,rel,args", [
    ("completion-check.py", "docs/REQUIREMENTS.md", ["--mode", "plan"]),
    ("diagram-check.py", "docs/REQUIREMENTS.md", []),
    ("diagram-check.py", "docs/diagrams/INDEX.md", []),
    ("diagram-check.py", "docs/diagrams/DEVIATIONS.md", ["--mode", "code"]),
    ("plan-check.py", "docs/diagrams/INDEX.md", ["--no-git"]),
], ids=["completion-check-register", "diagram-check-register", "diagram-check-index", "diagram-check-deviations",
        "plan-check-index"])
def test_r060_r2_a_header_block_the_reader_refuses_stops_the_program(tmp_path, prog, rel, args):
    if rel == "docs/REQUIREMENTS.md":
        head, body = th.register_header(), th.read_repo(rel)
    elif rel.endswith("INDEX.md"):
        head, body = th.roles_header("diagram-index", th.IDX_COLS, th.IDX_ROLES), th.read_repo(rel)
    else:
        head, body = th.roles_header("deviations", th.DEV_COLS, th.DEV_ROLES), th.read_repo(rel)
    full = _block_fault(head) + body
    if prog == "completion-check.py":
        ws = th.register_ws(tmp_path)
    else:
        ws = th.diagrams_ws(tmp_path, plan=th.PLAN_D % "D-002")
    th.write(ws / rel, full)
    rc, out = run(prog, ws, *args)
    th.assert_malformed(rc, out, rel, full)


def test_r060_r2_conformance_check_refuses_an_inventory_header_lacking_a_section(tmp_path):
    text = th.inventory_header(drop="deferred")
    rc, out = th.conformance(th.conformance_ws(tmp_path, text))
    th.assert_malformed(rc, out, "docs/INVENTORY.md", text + th.INVENTORY)


COLS_MOVED = ["Requirement", "ID", "Evidence", "Status", "Source"]


@pytest.mark.parametrize("mode", ["plan", "done"], ids=["plan", "done"])
def test_r060_r2_a_headed_register_reads_its_id_and_evidence_by_role(tmp_path, mode):
    test = "tests/test_thing.py"
    body = th.register_body().replace("| R-001 | the thing | owner | planned | " + th.DASH + " |",
                                      "| R-001 | the thing | owner | built | " + test + " |")
    moved = th.register_body(COLS_MOVED).replace("| the thing | R-001 | " + th.DASH + " | planned |",
                                                 "| the thing | R-001 | " + test + " | built |")
    assert body != th.register_body() and moved != th.register_body(COLS_MOVED)
    rc_p, out_p = run("completion-check.py", th.register_ws(tmp_path / "p", body=body), "--mode", mode)
    rc_h, out_h = run("completion-check.py", th.register_ws(tmp_path / "h", th.register_header(COLS_MOVED), moved),
                      "--mode", mode)
    assert rc_h == rc_p and th.answer(out_h) == th.answer(out_p), (out_p, out_h)


def test_r060_r2_the_registers_ids_are_read_by_role():
    ids = th.need("requirement_ids_from_register")
    header = {"columns": COLS_MOVED, "roles": th.REG_ROLES}
    assert ids(th.register_body(COLS_MOVED), header) == {"R-001", "R-002"}


def test_r060_r2_the_deviations_keys_are_read_by_role():
    keys = th.need("parse_deviation_keys")
    cols = ["From", "To", "Diagram", "As built", "Since", "Resolved by"]
    body = ("# Known deviations\n\n| " + " | ".join(cols) + " |\n|---|---|---|---|---|---|\n"
            "| hooks | bridge_env | D-002 | imports by file | 2026-11-01 | TASK-099 |\n")
    assert keys(body, {"columns": cols, "roles": th.DEV_ROLES}) == {("D-002", "hooks", "bridge_env")}


def test_r060_r2_an_inventory_section_is_found_by_its_whole_heading(tmp_path):
    body = th.INVENTORY.replace("## Decisions\n", "## Decisions (settled)\n")
    assert "Decisions" not in th.need("inventory_parse_tables")(body)
    rc, out = run("inventory-check.py", th.inventory_ws(tmp_path, body=body))
    assert rc == 1 and "SHAPE: section '## Decisions' missing" in out, out


def test_r060_r2_diagram_check_selects_every_diagram_of_a_reordered_declared_index(tmp_path):
    index = th.swap_columns(th.read_repo("docs/diagrams/INDEX.md"), 2, 3)
    cols = ["ID", "Level", "Status", "Kind", "File", "Refines", "Realizes", "Enforced by", "Why"]
    rc_p, out_p = th.diagram(th.diagrams_ws(tmp_path / "p"))
    rc_h, out_h = th.diagram(th.diagrams_ws(tmp_path / "h", index=th.roles_header("diagram-index", cols, th.IDX_ROLES) + index))
    sel_p = re.findall(r"(\d+) diagrams selected", out_p)
    assert sel_p and sel_p[0] != "0", out_p
    assert re.findall(r"(\d+) diagrams selected", out_h) == sel_p, out_h


# ---------------------------------------------------------------- builder's cases below this line


def test_r060_r2_headed_inventory_tables_read_from_body_only(tmp_path):
    """R-060: a headed inventory reads tables from the body alone, not the YAML header block."""
    hdr = th.inventory_header()
    rc, out = run("inventory-check.py", th.inventory_ws(tmp_path, hdr, body=""))
    assert rc != 0 or "SHAPE: section" in out, out


def test_r060_r2_headed_inventory_column_count_uses_template(tmp_path):
    """R-060: column-count SHAPE under an agreeing header matches the header-less template rule."""
    bad_tables = [
        ("features", ["Feature", "What it does"], "Feature"),
        ("resources", ["Name", "Kind", "Where it lives", "Used by", "Provided"], "Name"),
        ("decisions", ["Decision", "Reason", "Settled", "Revisit only if"], "Decision"),
        ("deferred", ["Item", "Why deferred", "Since", "Owner decision needed"], "Item"),
    ]
    body = th.INVENTORY.replace(
        "| Feature | What it does | Where | Tests | Since |\n|---|---|---|---|---|",
        "| Feature | What it does |\n|---|---|",
    ).replace(
        "| Search | finds things | app/search.py | tests/test_search.py | TASK-001 |",
        "| Search | finds things |",
    )
    rc_p, out_p = run("inventory-check.py", th.inventory_ws(tmp_path / "p", body=body))
    rc_h, out_h = run("inventory-check.py", th.inventory_ws(tmp_path / "h", th.inventory_header(tables=bad_tables), body=body))
    assert "SHAPE:" in out_p and "Features" in out_p, out_p
    assert rc_h == rc_p and th.answer(out_h) == th.answer(out_p), out_h


def test_r060_r2_conformance_development_data_uses_bridge_env_reading(tmp_path):
    """R-060: conformance-check reads header-less development data through bridge_env, not a local regex."""
    tree = _tree("conformance-check.py")
    pats = [p for p in th.re_patterns(tree) if isinstance(p, str) and "development data" in p.lower()]
    assert not pats, "conformance-check.py keeps a local development-data pattern at %s" % pats


def test_r060_r2_plan_check_headerless_index_applies_first_table_check(tmp_path):
    """R-060: plan-check's header-less index reading refuses a table that fails the normative header check."""
    index = th.swap_columns(th.read_repo("docs/diagrams/INDEX.md"), 2, 3)
    rc, out = th.plan_check(th.diagrams_ws(tmp_path, index=index, plan=th.PLAN_D % "D-002"))
    assert rc == 1 and re.search(r"DIAGRAMS:", out), out
