"""TASK-054, this repository's records migrated by the installed records-migrate.py at its calibration to 2026.11.11a
(R-063). Supervisor-authored, written before the migration.

enforces: docs/REQUIREMENTS.md R-063 (this repository's records gain their headers at its calibration to the release,
the prose unchanged); docs/BUILD_PLAN.md, TASK-054's Done when: every file of the eight kinds opens with `---` and a
`record:` key of its kind but for the merged briefs the fallback refuses, which stay header-less by rule; every
migrated header parsed by `yaml.safe_load` equals `read_header`'s value (R-057's cross-check over this repository's
records); and the token measure: a brief's bytes minus its header's equal its bytes before the migration (the migration
adds only the header), and the status file's bytes at the last commit before the migration and at the migration's,
read by `git show`, skipped where either commit is absent (the branch's commits squashed away on main; CI's depth-1
checkout; a copy with no repository).

The records are read from the working tree, line endings normalised to LF as git stores them, and enumerated as the
migration enumerates them (records_migrate.enumerate_records), so the test reads the same files in a checkout, in CI
and in the mutation engine's copy.
"""
import importlib.util
import os
import subprocess
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

_spec = importlib.util.spec_from_file_location("records_migrate", os.path.join(BRIDGE, "records-migrate.py"))
records_migrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(records_migrate)

# The merged briefs the fallback refuses (a plain Scope line with no bullet; records-migrate.py --check prints
# `cannot read <path>: empty`); by rule a merged brief's prose is never repaired, so they stay header-less.
REFUSED = ("handoff/TASK-002-r2.md", "handoff/TASK-002-r3.md", "handoff/TASK-002-r4.md")

# The token measure, taken once in the supervisor's checkout by `git show <sha>:<path>` (quoted in the accept commit
# and in docs/INVENTORY.md's growth row).
TRIM_SHA = "5473fc6200ef404b0903f29967833866525e9f97"        # the repairs, the last commit before the migration
MIGRATION_SHA = "9199d048a1d35689286849fbc7577cf80eae1864"   # the installed program's write
STATUS = "docs/PROJECT_STATUS.md"
STATUS_BYTES_AT_TRIM = 9124
STATUS_BYTES_AT_MIGRATION = 10523
STATUS_HEADER_BYTES = 1399
BRIEF = "handoff/TASK-046.md"
BRIEF_PROSE_BYTES = 31392
BRIEF_HEADER_BYTES = 357


def records():
    return [(rel, records_migrate.record_kind(rel)) for rel, _ in records_migrate.enumerate_records(ROOT)]


def lf_bytes(rel):
    with open(os.path.join(ROOT, *rel.split("/")), "rb") as fh:
        return fh.read().replace(b"\r\n", b"\n")


def header_bytes(data):
    """The header block's bytes: the opening `---` line through the closing one."""
    lines = data.splitlines(keepends=True)
    assert lines and lines[0].rstrip(b"\r\n") == b"---"
    for i in range(1, len(lines)):
        if lines[i].rstrip(b"\r\n") == b"---":
            return len(b"".join(lines[:i + 1]))
    raise AssertionError("no closing --- line")


def opens_with_header(text, kind):
    lines = text.split("\n")
    if lines[0] != "---" or "---" not in lines[1:]:
        return False
    return "record: %s" % kind in lines[1:lines.index("---", 1)]


def test_r063_every_record_of_the_eight_kinds_is_found():
    kinds = {kind for _, kind in records()}
    assert kinds == {"project-status", "build-plan", "brief", "inventory", "requirements", "diagram-index",
                     "deviations", "run-parameters"}, kinds


def test_r063_every_record_opens_with_its_header_but_the_refused_merged_briefs():
    missing = []
    for rel, kind in records():
        has = opens_with_header(lf_bytes(rel).decode("utf-8"), kind)
        if rel in REFUSED:
            assert not has, "%s was refused by rule and must stay header-less" % rel
        elif not has:
            missing.append(rel)
    assert missing == [], missing


def test_r063_every_migrated_header_reads_the_same_through_yaml_and_read_header():
    differ = []
    count = 0
    for rel, kind in records():
        text = lf_bytes(rel).decode("utf-8")
        header, _ = bridge_env.read_header(text)
        if header is None:
            continue
        count += 1
        block = text.split("\n---\n", 1)[0][len("---\n"):]
        if yaml.safe_load(block) != header:
            differ.append(rel)
        assert bridge_env.check_header(kind, header) == [], rel
    assert count > 0
    assert differ == [], differ


def test_r063_the_brief_s_prose_is_unchanged_by_the_migration():
    data = lf_bytes(BRIEF)
    assert header_bytes(data) == BRIEF_HEADER_BYTES
    assert len(data) - BRIEF_HEADER_BYTES == BRIEF_PROSE_BYTES


def git(*args):
    try:
        p = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, timeout=120)
    except OSError:
        return 1, b""
    return p.returncode, p.stdout


def test_r063_the_status_file_s_growth_over_the_two_commits():
    for sha in (TRIM_SHA, MIGRATION_SHA):
        if git("cat-file", "-e", "%s^{commit}" % sha)[0] != 0:
            pytest.skip("commit %s is absent (the branch's commits squashed away on main, CI's depth-1 checkout, or a "
                        "copy with no repository); the numbers are quoted in TASK-054's accept commit" % sha)
    before = git("show", "%s:%s" % (TRIM_SHA, STATUS))[1]
    after = git("show", "%s:%s" % (MIGRATION_SHA, STATUS))[1]
    assert len(before) == STATUS_BYTES_AT_TRIM
    assert len(after) == STATUS_BYTES_AT_MIGRATION
    assert header_bytes(after) == STATUS_HEADER_BYTES
    assert after[STATUS_HEADER_BYTES:] == before
