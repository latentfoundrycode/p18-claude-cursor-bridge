"""TASK-058, the bridge's own records checked by its tests (R-101). Supervisor-authored.

enforces: docs/REQUIREMENTS.md R-101 (a test runs `inventory-check.py` over this repository's records, and one asserts
`header_agrees` for every headed record of it); docs/BUILD_PLAN.md, TASK-058's Done when: `inventory-check.py` over this
repository's records exits 0, and every headed record agrees with its prose through `bridge_env`'s readers, the merged
briefs the fallback refuses named as release B2 named them (tests/test_release_b2_records.py, REFUSED).

The records are enumerated as the migration enumerates them (records_migrate.enumerate_records) and read as their own
checks read them: a brief through `read_brief_record`, the plan through `plan_header_findings` (its merged set from
`origin/main`, or none where the clone is shallow or absent, as in CI's depth-1 push run and the mutation engine's
copy), the status file and the run parameters through `status_values` and `run_parameters_values`, and the inventory,
the register, the diagram index and the deviations register by `header_agrees` over the body, as inventory-check.py,
completion-check.py and diagram-check.py read them.
"""
import importlib.util
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

_spec = importlib.util.spec_from_file_location("records_migrate", os.path.join(BRIDGE, "records-migrate.py"))
records_migrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(records_migrate)

# The merged briefs the fallback refuses, header-less by rule (release B2's list, tests/test_release_b2_records.py).
REFUSED = ("handoff/TASK-002-r2.md", "handoff/TASK-002-r3.md", "handoff/TASK-002-r4.md")
BODY_KINDS = {
    "inventory": bridge_env.inventory_fallback,
    "requirements": bridge_env.register_fallback,
    "diagram-index": bridge_env.diagram_index_fallback,
    "deviations": bridge_env.deviations_fallback,
}


def git(*args):
    try:
        p = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return p.returncode, p.stdout.strip()


def merged_ids():
    """The plan's merged set as plan-check.py derives it, or None where no full history is at hand."""
    if not os.path.exists(os.path.join(ROOT, ".git")):
        return None
    rc, out = git("rev-parse", "--is-shallow-repository")
    if rc != 0 or out != "false":
        return None
    for ref in ("origin/main", "HEAD"):
        if git("rev-parse", "--verify", "--quiet", ref)[0] == 0:
            return bridge_env.squash_merged_ids(ROOT, bridge_env.PLAN_ID_PATTERN, ref=ref)
    return None


def records():
    return [(rel, records_migrate.record_kind(rel)) for rel, _ in records_migrate.enumerate_records(ROOT)]


def text_of(rel):
    with open(os.path.join(ROOT, *rel.split("/")), "rb") as fh:
        return bridge_env.decode_record_bytes(fh.read())


def findings(rel, kind, text, merged):
    """What the record's own reader says against its header: a list, empty when the header agrees with its prose."""
    if kind == "brief":
        rec = bridge_env.read_brief_record(text, os.path.splitext(os.path.basename(rel))[0])
        if rec.refusal is not None:
            return ["refused: %s" % (rec.refusal,)]
        return list(rec.disagrees)
    if kind == "build-plan":
        fatal, disagree, _header = bridge_env.plan_header_findings(rel, text, merged)
        return fatal + disagree
    if kind == "project-status":
        _values, malformed, disagrees = bridge_env.status_values(text)
        return ["malformed: %s" % (malformed,)] if malformed else list(disagrees)
    if kind == "run-parameters":
        _values, malformed, disagrees = bridge_env.run_parameters_values(text)
        return ["malformed: %s" % (malformed,)] if malformed else list(disagrees)
    header, body = bridge_env.read_header(text)
    out = ["malformed: %s" % f for f in bridge_env.check_header(kind, header)]
    return out or list(bridge_env.header_agrees(kind, header, BODY_KINDS[kind](body or "")))


def test_r101_inventory_check_passes_over_this_repository_s_records():
    p = subprocess.run([sys.executable, os.path.join(BRIDGE, "inventory-check.py")], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=300)
    assert p.returncode == 0 and "RESULT: OK" in p.stdout, p.stdout + p.stderr


def test_r101_every_headed_record_agrees_with_its_prose_through_its_own_reader():
    merged = merged_ids()
    headed, headerless, disagree = 0, [], {}
    for rel, kind in records():
        text = text_of(rel)
        header, _body = bridge_env.read_header(text)
        if header is None:
            headerless.append(rel)
            continue
        headed += 1
        found = findings(rel, kind, text, merged if kind == "build-plan" else None)
        if found:
            disagree[rel] = found
    assert sorted(headerless) == sorted(REFUSED), "header-less records other than release B2's refused briefs: %s" % (
        sorted(set(headerless) - set(REFUSED)) or sorted(set(REFUSED) - set(headerless)))
    assert headed > len(BODY_KINDS), headed
    assert disagree == {}, disagree
