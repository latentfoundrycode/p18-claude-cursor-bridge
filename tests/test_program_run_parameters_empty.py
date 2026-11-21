"""TASK-071, the supervisor's acceptance tests (R-091): an empty run parameter is named, never written.

enforces: docs/REQUIREMENTS.md R-091; docs/BUILD_PLAN.md, TASK-071's Done when; docs/DESIGN.md, the field finding F4
and J13; docs/HARDENING.md, "The migration's two uncovered failure exits".

The fixed forms these tests pin:
- records-migrate.py refuses a header-less run-parameters record whose fallback reading
  (bridge_env.run_parameters_fallback) leaves any of the five values (stage_pause, merge_authority, refactoring_pass,
  installer_verification, parallel_increments) empty: exactly one line for that record,
  `cannot read <shown path>: <label> has no value on a plain line`, <label> the plain line's label as
  bridge_env._RUN_PARAM_VALUE_PREFIXES spells it without its colon and space (Stage pause, Merge authority,
  Refactoring pass, Installer verification, Parallel increments), the first empty one in that order. Nothing is
  written (the file byte for byte as before), no `would write` / `wrote` line for it, in a run and under --check; a
  `cannot read` alone does not change the exit (a run or a --check whose only record is refused exits 0).
- inventory-check.py, docs/RUN_PARAMETERS.md beside the inventory: with a header, `RUN PARAMETERS: <key> is empty`
  for each of the five empty in the header, in the schema's order, exit 1; with no header,
  `RUN PARAMETERS: <label> is empty` for each of the five the fallback leaves empty, exit 1. A file with all five
  values passes.
- The fallback reads no new form: a value under a heading, in a bullet or in bold stays empty.
- The migration's two failure exits no test reached before (HARDENING: a failed close of the temporary file and a
  failed read of it back) each exit 3 with their exact line, the record byte-identical, no temporary file left.

Each test builds its own scratch project under tmp_path; nothing here is shared with another test module.
"""
import builtins
import errno
import importlib.util
import os
import subprocess
import sys

import pytest

import conftest as suite_conftest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
MIGRATE = os.path.join(BRIDGE, "records-migrate.py")
INVENTORY_CHECK = os.path.join(BRIDGE, "inventory-check.py")
REL = "docs/RUN_PARAMETERS.md"

LABELS = ("Stage pause", "Merge authority", "Refactoring pass", "Installer verification", "Parallel increments")
KEYS = ("stage_pause", "merge_authority", "refactoring_pass", "installer_verification", "parallel_increments")
VALUES = ("run", "supervisor", "on", "n/a", "off")


# ---------------------------------------------------------------- the scratch project

def make_project(tmp_path, text):
    """A scratch Workspace whose docs/RUN_PARAMETERS.md holds `text` (LF, UTF-8, no BOM); returns the Workspace."""
    ws = tmp_path / "proj" / "Workspace"
    os.makedirs(str(ws / "docs"))
    put(ws, REL, text)
    return ws


def put(ws, rel, text):
    path = os.path.join(str(ws), *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(text.encode("utf-8") if isinstance(text, str) else text)


def get(ws, rel):
    with open(os.path.join(str(ws), *rel.split("/")), "rb") as f:
        return f.read()


def run(argv, ws):
    kw = suite_conftest.windowless_kwargs({"capture_output": True, "text": True, "encoding": "utf-8",
                                           "errors": "replace", "timeout": 300})
    p = subprocess.run([sys.executable] + argv, cwd=str(ws), **kw)
    return p.returncode, p.stdout, p.stderr


def migrate(ws, *args):
    return run([MIGRATE] + list(args), ws)


def lines_of(out):
    return [ln for ln in out.splitlines() if ln.strip()]


def plain_record(skip=()):
    """A header-less run-parameters record in the plain-line form, every value on its line but the labels in `skip`."""
    out = ["# Run parameters", "Set: 2026-11-01"]
    for label, value in zip(LABELS, VALUES):
        if label not in skip:
            out.append("%s: %s" % (label, value))
    return "\n".join(out) + "\n"


def heading_record():
    """The field's form (F4, the supervisor's reproduction): each value on its own line under a `## <label>`."""
    out = ["# Run parameters", "Set: 2026-11-01", ""]
    for label, value in zip(LABELS, VALUES):
        out += ["## " + label, value, ""]
    return "\n".join(out)


def bullet_record():
    out = ["# Run parameters", "Set: 2026-11-01", ""]
    out += ["- %s: %s" % (label, value) for label, value in zip(LABELS, VALUES)]
    return "\n".join(out) + "\n"


def bold_record():
    out = ["# Run parameters", "Set: 2026-11-01", ""]
    out += ["**%s:** %s" % (label, value) for label, value in zip(LABELS, VALUES)]
    return "\n".join(out) + "\n"


def refusal(label):
    return "cannot read %s: %s has no value on a plain line" % (REL, label)


def assert_refused(ws, before, mode, label):
    """records-migrate.py, given the record's path, in a run (mode "run") or under --check: the one cannot read line
    naming `label`, nothing else for the record, exit 0, the file byte for byte as before."""
    args = ["--check", REL] if mode == "check" else [REL]
    code, out, err = migrate(ws, *args)
    assert "Traceback" not in out + err, (out, err)
    assert lines_of(out) == [refusal(label)], (code, out, err)
    assert not [ln for ln in out.splitlines() if ln.startswith(("would write ", "wrote "))], out
    assert code == 0, (code, out, err)
    assert get(ws, REL) == before, "the refused record changed"


# ---------------------------------------------------------------- records-migrate.py refuses an empty value

@pytest.mark.parametrize("mode", ["check", "run"])
def test_r091_the_fields_heading_form_is_refused_naming_stage_pause(tmp_path, mode):
    """R-091, TASK-071 Done when (records-migrate.py lists a run-parameters record whose fallback reading leaves any
    of the five values empty as `cannot read <file>: <name> has no value on a plain line`, the first such name, and
    leaves it header-less, in a run and under --check, the exit rule for a cannot read unchanged; the field's file, a
    record with `## Stage pause` headings, is the reproduction, red on the checkpoint): today --check prints `would
    write docs/RUN_PARAMETERS.md` and exits 1, and a run prints `wrote` and writes a header whose five values are all
    "" (exit 0)."""
    text = heading_record()
    ws = make_project(tmp_path, text)
    assert_refused(ws, text.encode("utf-8"), mode, "Stage pause")


@pytest.mark.parametrize("label", LABELS, ids=KEYS)
@pytest.mark.parametrize("mode", ["check", "run"])
def test_r091_each_value_empty_alone_is_named(tmp_path, mode, label):
    """R-091, TASK-071 Done when (records-migrate.py lists a run-parameters record whose fallback reading leaves any
    of the five values empty as `cannot read <file>: <name> has no value on a plain line`, and leaves it
    header-less): a plain-line record lacking only this value's line; today it is migrated with that value "" (--check
    `would write`, exit 1; a run `wrote`, exit 0)."""
    text = plain_record(skip=(label,))
    ws = make_project(tmp_path, text)
    assert_refused(ws, text.encode("utf-8"), mode, label)


@pytest.mark.parametrize("mode", ["check", "run"])
def test_r091_two_empty_values_name_only_the_first(tmp_path, mode):
    """R-091, TASK-071 Done when (`cannot read <file>: <name> has no value on a plain line`, the first such name in
    the record's order): Merge authority and Parallel increments both empty, the one line names Merge authority only;
    today the record is migrated with both values "" (--check `would write`, exit 1; a run `wrote`, exit 0)."""
    text = plain_record(skip=("Merge authority", "Parallel increments"))
    ws = make_project(tmp_path, text)
    assert_refused(ws, text.encode("utf-8"), mode, "Merge authority")


@pytest.mark.parametrize("form", ["bullet", "bold"])
@pytest.mark.parametrize("mode", ["check", "run"])
def test_r091_the_fallback_reads_no_bullet_or_bold_form(tmp_path, mode, form):
    """R-091, TASK-071 Done when (the fallback reads no heading, bullet or bold form): every value written as a bullet
    (`- Stage pause: run`) or in bold (`**Stage pause:** run`) stays empty, so the record is refused naming Stage
    pause; today it is migrated with all five values "" (--check `would write`, exit 1; a run `wrote`, exit 0)."""
    text = bullet_record() if form == "bullet" else bold_record()
    ws = make_project(tmp_path, text)
    assert_refused(ws, text.encode("utf-8"), mode, "Stage pause")


def test_r091_a_complete_plain_line_record_still_migrates(tmp_path):
    """R-091, TASK-071 Done when (the exit rule for a cannot read unchanged; only an empty value is refused): the
    control, a header-less record with all five values on plain lines, is listed `would write` under --check, exit 1,
    and no cannot read line; today it is the same (this passes on the checkpoint)."""
    text = plain_record()
    ws = make_project(tmp_path, text)
    code, out, err = migrate(ws, "--check", REL)
    assert lines_of(out) == ["would write %s" % REL], (code, out, err)
    assert code == 1, (code, out, err)
    assert get(ws, REL) == text.encode("utf-8")


# ---------------------------------------------------------------- inventory-check.py fails an empty value

INVENTORY = (
    "# Inventory\n"
    "Reflected through: none\n"
    "Updated: 2026-11-01\n"
    "\n"
    "## Features\n"
    "| Feature | What it does | Where | Tests | Since |\n"
    "|---|---|---|---|---|\n"
    "| Search | finds things | app/search.py | tests/test_search.py | TASK-001 |\n"
    "\n"
    "## Resources\n"
    "| Name | Kind | Where it lives | Used by | Provided |\n"
    "|---|---|---|---|---|\n"
    "| Socket account | account | the owner's login; no spend possible | CI | 2026-09-01 |\n"
    "\n"
    "## Decisions\n"
    "| Decision | Reason | Settled | Revisit only if |\n"
    "|---|---|---|---|\n"
    "| Development data: none | no data store | 2026-11-01, owner | the product gains a store |\n"
    "\n"
    "## Deferred\n"
    "| Item | Why deferred | Since | Owner decision needed |\n"
    "|---|---|---|---|\n"
)


def inventory_project(tmp_path, params):
    """A scratch Workspace with a passing docs/INVENTORY.md and `params` (text or bytes) as docs/RUN_PARAMETERS.md."""
    ws = tmp_path / "inv" / "Workspace"
    os.makedirs(str(ws / "docs"))
    put(ws, "docs/INVENTORY.md", INVENTORY)
    put(ws, REL, params)
    return ws


def inventory_check(ws):
    code, out, err = run([INVENTORY_CHECK], ws)
    return code, out + err


def rp_lines(out):
    return [ln for ln in out.splitlines() if ln.startswith("RUN PARAMETERS")]


def test_r091_the_inventory_fixture_passes_on_its_own(tmp_path):
    """R-091, TASK-071 Done when (this repository's own run-parameters file passes): the scratch inventory every
    inventory-check case here stands on passes alone (no run-parameters file), exit 0, so the only failure in a case
    below is the run-parameters one; today it is the same."""
    ws = tmp_path / "bare" / "Workspace"
    os.makedirs(str(ws / "docs"))
    put(ws, "docs/INVENTORY.md", INVENTORY)
    code, out = inventory_check(ws)
    assert code == 0 and "RESULT: OK" in out, out


def headed_record(values):
    lines = ["---", "record: run-parameters", "header: 1"]
    for key in KEYS:
        lines.append('%s: "%s"' % (key, values.get(key, "")))
    lines += ["agent_ceiling: null", "ceiling_above_twice: []", "design_rounds_above_five: []",
              "review_rounds_above_ceiling: []", "---"]
    return "\n".join(lines) + "\n"


def test_r091_inventory_check_fails_each_value_empty_in_the_header(tmp_path):
    """R-091, TASK-071 Done when (inventory-check.py fails a run-parameters file with any of the five empty, in its
    header where it has one, `RUN PARAMETERS: <name> is empty`, a shape failure, exit 1, where both readings being
    empty passed): a header with stage_pause "" and parallel_increments "" over a body that agrees (neither line
    stands), the two lines in the schema's order; today it prints no RUN PARAMETERS line, `RESULT: OK`, exit 0."""
    values = dict(zip(KEYS, VALUES))
    values["stage_pause"] = ""
    values["parallel_increments"] = ""
    body = plain_record(skip=("Stage pause", "Parallel increments"))
    ws = inventory_project(tmp_path, headed_record(values) + body)
    code, out = inventory_check(ws)
    assert "HEADER" not in out, out
    assert rp_lines(out) == ["RUN PARAMETERS: stage_pause is empty", "RUN PARAMETERS: parallel_increments is empty"], out
    assert "RESULT: 2 problem(s)" in out.splitlines(), out
    assert code == 1, (code, out)


def test_r091_inventory_check_fails_a_value_empty_in_a_headerless_file(tmp_path):
    """R-091, TASK-071 Done when (inventory-check.py fails a run-parameters file with any of the five empty ... in its
    lines where it has none): a header-less file lacking only the Refactoring pass line, one line naming its label,
    exit 1; today a header-less file is not its finding: no RUN PARAMETERS line, `RESULT: OK`, exit 0."""
    ws = inventory_project(tmp_path, plain_record(skip=("Refactoring pass",)))
    code, out = inventory_check(ws)
    assert rp_lines(out) == ["RUN PARAMETERS: Refactoring pass is empty"], out
    assert "RESULT: 1 problem(s)" in out.splitlines(), out
    assert code == 1, (code, out)


def test_r091_inventory_check_passes_this_repositorys_own_run_parameters(tmp_path):
    """R-091, TASK-071 Done when (this repository's own run-parameters file passes): docs/RUN_PARAMETERS.md, headed,
    copied byte for byte beside a passing inventory, no RUN PARAMETERS line and exit 0; today it is the same."""
    with open(os.path.join(ROOT, "docs", "RUN_PARAMETERS.md"), "rb") as f:
        own = f.read()
    ws = inventory_project(tmp_path, own)
    code, out = inventory_check(ws)
    assert rp_lines(out) == [] and "HEADER" not in out, out
    assert code == 0, (code, out)


def test_r091_inventory_check_passes_a_complete_headerless_file(tmp_path):
    """R-091, TASK-071 Done when (inventory-check.py fails a file with any of the five empty, and only such a file):
    a header-less file with all five values on plain lines, no RUN PARAMETERS line, exit 0; today it is the same."""
    ws = inventory_project(tmp_path, plain_record())
    code, out = inventory_check(ws)
    assert rp_lines(out) == [], out
    assert code == 0, (code, out)


# ---------------------------------------------------------------- the migration's two uncovered failure exits

def load_migrate():
    spec = importlib.util.spec_from_file_location("records_migrate_task071", MIGRATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def is_temporary(file):
    return isinstance(file, (str, bytes, os.PathLike)) and \
        os.path.basename(os.fsdecode(os.fspath(file))).startswith(".records-migrate-")


class _CloseFails:
    """The temporary file, opened for real; its close closes it and then fails as a full disk's flush would."""

    def __init__(self, f):
        self._f = f

    def write(self, data):
        return self._f.write(data)

    def close(self):
        self._f.close()
        raise OSError(errno.EIO, "Input/output error")

    def __getattr__(self, name):
        return getattr(self._f, name)


def temporaries(ws):
    return [n for n in os.listdir(os.path.join(str(ws), "docs")) if n.startswith(".records-migrate-")]


def test_r091_a_failed_close_of_the_temporary_file_exits_3(tmp_path, monkeypatch, capsys):
    """R-091, TASK-071 Done when (the migration's two failure exits that no test reaches today, named by the reality
    check, each get a test): the temporary file's close failing (records-migrate.py's third `temporary write failed`)
    prints `records-migrate: <path>: temporary write failed: <error>`, exits 3, the record byte-identical, no temporary
    file left; today it does the same (this passes on the checkpoint). The program is unedited; only open() is
    replaced in this process."""
    text = plain_record()
    ws = make_project(tmp_path, text)
    mod = load_migrate()
    real_open = builtins.open
    hits = []

    def open_close_fails(file, mode="r", *args, **kwargs):
        f = real_open(file, mode, *args, **kwargs)
        if is_temporary(file) and "x" in mode:
            hits.append(file)
            return _CloseFails(f)
        return f

    with monkeypatch.context() as m:
        m.chdir(str(ws))
        m.setattr(builtins, "open", open_close_fails)
        code = mod.main([REL])
    out = capsys.readouterr().out
    assert hits, "no temporary file was opened"
    assert lines_of(out) == ["records-migrate: %s: temporary write failed: [Errno %d] Input/output error"
                             % (REL, errno.EIO)], out
    assert code == 3, (code, out)
    assert get(ws, REL) == text.encode("utf-8")
    assert temporaries(ws) == []


def test_r091_a_failed_read_of_the_temporary_file_exits_3(tmp_path, monkeypatch, capsys):
    """R-091, TASK-071 Done when (the migration's two failure exits that no test reaches today, named by the reality
    check, each get a test): the temporary file's read back failing prints `records-migrate: <path>: temporary read
    failed: <error>`, exits 3, the record byte-identical, no temporary file left; today it does the same (this passes
    on the checkpoint). The program is unedited; only open() is replaced in this process."""
    text = plain_record()
    ws = make_project(tmp_path, text)
    mod = load_migrate()
    real_open = builtins.open
    hits = []

    def open_read_fails(file, mode="r", *args, **kwargs):
        if is_temporary(file) and "r" in mode:
            hits.append(file)
            raise OSError(errno.EACCES, "Permission denied")
        return real_open(file, mode, *args, **kwargs)

    with monkeypatch.context() as m:
        m.chdir(str(ws))
        m.setattr(builtins, "open", open_read_fails)
        code = mod.main([REL])
    out = capsys.readouterr().out
    assert hits, "the temporary file was never read back"
    assert lines_of(out) == ["records-migrate: %s: temporary read failed: [Errno %d] Permission denied"
                             % (REL, errno.EACCES)], out
    assert code == 3, (code, out)
    assert get(ws, REL) == text.encode("utf-8")
    assert temporaries(ws) == []
