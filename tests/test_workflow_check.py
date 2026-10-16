"""workflow-check.py (TASK-006), the supervisor's tests, written from handoff/TASK-006.md before the delegation.

enforces: docs/REQUIREMENTS.md R-014 (every change targets an existing extension point; replace/set only in a type or
sub-workflow, replace only on a replaceable phase; trait additions only add; a sub-workflow names an existing type
workflow; a `Workflows:` line names one product type, at most one of its sub-types, and traits, all in the open list;
an unwritten type or sub-type fails, an unwritten trait is flagged and non-fatal) and R-033 (the check runs at every
bridge release, in CI). The fixtures are tests/fixtures/workflows/: `pass/` is the CI root, `fail/<case>/` one root per
failing case, `status/` the status-line cases with an open list of their own.
"""
import os
import pathlib
import subprocess
import sys

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
PROG = "bridge/cursor-bridge/workflow-check.py"
FIX = "tests/fixtures/workflows"
STATUS_LIST = f"{FIX}/status/open-list.md"
WORKFLOW = REPO / ".github" / "workflows" / "tests.yml"


def run(*args):
    """Run the check from the repository root with relative paths, so finding lines carry predictable paths."""
    p = subprocess.run([sys.executable, PROG, *args], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")
    lines = p.stdout.splitlines()
    return p.returncode, lines, p.stderr


def fails(lines):
    return [line for line in lines if line.startswith("FAIL (")]


def assert_clean_end(lines, stderr):
    assert lines, "the check printed nothing"
    assert "Traceback" not in stderr, stderr
    assert sum(1 for line in lines if line.startswith("RESULT:")) == 1, "exactly one RESULT line"
    assert lines[-1].startswith("RESULT:"), "the RESULT line is the last line"


# --- the passing roots (R-033: the CI invocation) ---------------------------------------------------------------

def test_r033_ci_invocation_passes():
    code, lines, err = run("bridge/cursor-bridge/workflow", f"{FIX}/pass")
    assert_clean_end(lines, err)
    assert code == 0, lines
    assert lines[-1] == "RESULT: OK"
    assert not fails(lines)


def test_r014_default_root_is_the_programs_workflow_folder():
    code, lines, err = run()
    assert_clean_end(lines, err)
    assert code == 0 and lines[-1] == "RESULT: OK", lines


def test_r014_replaced_module_keeps_its_points():
    """Carry item 1 (Requirement 10): the trait has-screens and the sub-workflow add at interface.variants while the
    type workflow replaces interface; the fixture's fenced `## Replace design` and prose headings are not changes."""
    pass_root = REPO / FIX / "pass"
    assert "## Replace interface" in (pass_root / "types/host-extension.md").read_text(encoding="utf-8")
    assert "## Add at interface.variants" in (pass_root / "traits/has-screens.md").read_text(encoding="utf-8")
    code, lines, err = run(f"{FIX}/pass")
    assert code == 0 and lines[-1] == "RESULT: OK", lines


# --- the conditional-workflow files: one failing root per case --------------------------------------------------

FILE_CASES = [
    # (case folder, code, file inside the root, offending name or None where the brief leaves the name open)
    ("a-unknown-point", "a", "types/host-extension.md", "intake.question"),
    ("a-set-unknown-point", "a", "types/host-extension.md", "intake.delivery-kinds"),
    ("b-trait-sets", "b", "traits/installable.md", None),
    ("b-trait-replaces", "b", "traits/has-screens.md", None),
    ("c-not-replaceable", "c", "types/host-extension.md", "design"),
    ("c-unknown-module", "c", "types/host-extension.md", "testing"),
    ("d-type-file-missing", "d", "types/host-extension/claude-code-extension.md", None),
    ("d-sub-type-of-another", "d", "types/web-app/claude-code-extension.md", None),
    ("d-unknown-type-folder", "d", "types/not-a-type", None),
    ("set-point-without-set", "set", "types/host-extension.md", "intake.questions"),
    ("kind-missing", "kind", "types/host-extension.md", ("project-end.delivery", "-")),
    ("kind-unlisted", "kind", "traits/installable.md", "docker-image"),
    ("kind-on-another-point", "kind", "types/host-extension.md", None),
    ("kind-set-value", "kind", "types/host-extension.md", "deployment"),
    ("unknown-type-file", "unknown", "types/not-a-type.md", "not-a-type"),
    ("unknown-trait-file", "unknown", "traits/not-a-trait.md", "not-a-trait"),
    ("form-third-level", "form", "types/host-extension/claude-code-extension", None),
    ("form-not-markdown", "form", "traits/installable.txt", None),
    ("form-bad-heading", "form", "types/host-extension.md", None),
    ("form-two-sets", "form", "types/host-extension.md", None),
    ("form-empty-set", "form", "types/host-extension.md", None),
    ("form-two-replaces", "form", "types/host-extension.md", None),
    ("form-misspelt-change-word", "form", "types/host-extension.md", "-"),
    ("b-trait-sets-bom", "b", "traits/has-screens.md", None),
]


@pytest.mark.parametrize("case,code,inner,name", FILE_CASES, ids=[c[0] for c in FILE_CASES])
def test_r014_file_case_fails(case, code, inner, name):
    root = f"{FIX}/fail/{case}"
    rc, lines, err = run(root)
    assert_clean_end(lines, err)
    assert rc == 1, lines
    prefix = f"FAIL ({code}) {root}/{inner}"
    hits = [line for line in fails(lines) if line.startswith(prefix)]
    assert hits, f"no line starting {prefix!r} in {lines}"
    if name is not None:
        names = name if isinstance(name, tuple) else (name,)
        assert any(line.startswith(f"{prefix}: {n} - ") for n in names for line in hits), f"name {name!r} not the offending name: {hits}"
    assert lines[-1] == f"RESULT: {len(fails(lines))} problem(s)"


def test_r014_trait_set_at_unknown_point_gives_b_and_a():
    root = f"{FIX}/fail/b-and-a"
    rc, lines, err = run(root)
    assert rc == 1
    codes = {line.split(")")[0] for line in fails(lines)}
    assert {"FAIL (b", "FAIL (a"} <= codes, lines


def test_r014_fail_root_beside_the_pass_root_is_reported_in_argument_order():
    rc, lines, err = run(f"{FIX}/pass", f"{FIX}/fail/c-not-replaceable")
    assert rc == 1
    assert fails(lines) == [line for line in lines if line.startswith(f"FAIL (c) {FIX}/fail/c-not-replaceable/")], lines


# --- the status files ---------------------------------------------------------------------------------------------

def status(name):
    return run("--open-list", STATUS_LIST, "--status", f"{FIX}/status/{name}")


@pytest.mark.parametrize("name", ["ok-single.md", "ok-multi.md", "ok-unclassified.md", "ok-bom.md"])
def test_r014_status_ok(name):
    rc, lines, err = status(name)
    assert_clean_end(lines, err)
    assert rc == 0 and lines[-1] == "RESULT: OK", lines
    assert not [line for line in lines if line.startswith(("FAIL", "FLAG"))], lines


def test_r014_unwritten_trait_is_flagged_not_failed():
    rc, lines, err = status("flag-unwritten-trait.md")
    assert_clean_end(lines, err)
    assert rc == 0 and lines[-1] == "RESULT: OK", lines
    path = f"{FIX}/status/flag-unwritten-trait.md"
    assert f"FLAG (trait) {path}: Spends money - trait not yet written; flagged, work continues (non-fatal)" in lines
    assert not any(line.startswith("FLAG (trait)") and ": Installable - " in line for line in lines), "a written trait is not flagged"


STATUS_CASES = [
    ("e-two-types.md", "e", None),
    ("e-two-sub-types.md", "e", None),
    ("e-sub-type-of-another.md", "e", None),
    ("e-no-type.md", "e", None),
    ("e-same-part.md", "e", "app"),
    ("f-unwritten-type.md", "f", "Library Development"),
    ("f-unwritten-sub-type.md", "f", "Local Web App"),
    ("unknown-name.md", "unknown", "Toaster Development"),
    ("unknown-trait.md", "unknown", "Glitter"),
    ("form-no-traits-marker.md", "form", None),
    ("form-prefix-on-single.md", "form", None),
    ("form-prefix-missing.md", "form", None),
    ("form-trait-order.md", "form", None),
    ("form-trait-repeated.md", "form", None),
    ("form-sub-type-first.md", "form", None),
    ("form-trait-in-head.md", "form", None),
    ("form-no-line.md", "form", "-"),
    ("form-trait-separator.md", "form", None),
    ("form-trait-double-space.md", "form", None),
    ("form-bad-prefix-single.md", "form", None),
    ("form-empty-segment.md", "form", None),
]


@pytest.mark.parametrize("name,code,offending", STATUS_CASES, ids=[c[0] for c in STATUS_CASES])
def test_r014_status_case_fails(name, code, offending):
    rc, lines, err = status(name)
    assert_clean_end(lines, err)
    assert rc == 1, lines
    prefix = f"FAIL ({code}) {FIX}/status/{name}"
    hits = [line for line in fails(lines) if line.startswith(prefix)]
    assert hits, f"no line starting {prefix!r} in {lines}"
    if offending is not None:
        assert any(line.startswith(f"{prefix}: {offending} - ") for line in hits), hits
    assert lines[-1] == f"RESULT: {len(fails(lines))} problem(s)"


def test_r014_unwritten_type_fails_against_the_real_open_list():
    """Every entry of the bridge's own open list is unwritten today, so a classified line fails (f): the pause (§6.7)."""
    rc, lines, err = run("--status", f"{FIX}/status/ok-single.md")
    assert rc == 1
    assert any(line.startswith(f"FAIL (f) {FIX}/status/ok-single.md: Host Extension Development - ") for line in lines), lines


# --- the inputs the check cannot read: exit 2 ---------------------------------------------------------------------

def assert_not_checked(rc, lines, err):
    assert rc == 2, (rc, lines)
    assert "Traceback" not in err, err
    assert any(line.startswith("ERROR: ") for line in lines + err.splitlines()), (lines, err)
    assert lines and lines[-1] == "RESULT: not checked", lines


def test_r014_root_not_a_folder(tmp_path):
    assert_not_checked(*run(str(tmp_path / "absent")))


def test_r014_open_list_missing(tmp_path):
    assert_not_checked(*run("--open-list", str(tmp_path / "absent.md"), f"{FIX}/pass"))


def test_r014_status_file_missing(tmp_path):
    assert_not_checked(*run("--status", str(tmp_path / "absent.md")))


def test_r014_status_file_not_utf8(tmp_path):
    bad = tmp_path / "status.md"
    bad.write_bytes(b"Workflows: Web App Development; traits: none \xff\xfe\n")
    assert_not_checked(*run("--open-list", STATUS_LIST, "--status", str(bad)))


def test_r014_required_column_missing(tmp_path):
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    broken = tmp_path / "open-list.md"
    broken.write_text(text.replace("| Default traits | Written | Planned |\n|---|---|---|---|---|---|---|",
                                   "| Default traits | Done | Planned |\n|---|---|---|---|---|---|---|", 1), encoding="utf-8")
    assert "| Done |" in broken.read_text(encoding="utf-8")
    assert_not_checked(*run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md"))


def test_r014_row_cell_count_differs(tmp_path):
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    broken = tmp_path / "open-list.md"
    broken.write_text(text.replace("| library | Library |", "| library | Library | extra |", 1), encoding="utf-8")
    assert_not_checked(*run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md"))


def test_r014_registry_heading_missing(tmp_path):
    reg = (REPO / "bridge/cursor-bridge/workflow/extension-points.md").read_text(encoding="utf-8")
    broken = tmp_path / "extension-points.md"
    assert reg.count("\n## Extension points\n") == 1, "the heading line, not its citation in the prose"
    broken.write_text(reg.replace("\n## Extension points\n", "\n## Points\n", 1), encoding="utf-8")
    assert_not_checked(*run("--registry", str(broken), f"{FIX}/pass"))


# --- the usage text -----------------------------------------------------------------------------------------------

def test_r033_usage_names_the_three_times_and_the_codes():
    rc, lines, err = run("--help")
    text = "\n".join(lines).lower()
    assert rc == 0
    for word in ("intake", "release", "calibration", "r-014", "r-033"):
        assert word in text, word
    for code in ("(a)", "(b)", "(c)", "(d)", "(e)", "(f)", "(set)", "(kind)", "(unknown)", "(form)", "flag (trait)"):
        assert code in text, code


# --- round 2: the review's corrections (handoff/TASK-006-r2.md) ---------------------------------------------------

def test_r014_every_misspelt_change_word_is_form():
    """R2-1: `## Adds at`, `## add at`, `## Replacing`, `## Append at` are each a malformed change heading."""
    root = f"{FIX}/fail/form-misspelt-change-word"
    rc, lines, err = run(root)
    assert rc == 1
    forms = [line for line in fails(lines) if line.startswith(f"FAIL (form) {root}/types/host-extension.md: - ")]
    assert len(forms) == 4, lines
    assert len(fails(lines)) == 4, "a misspelt heading's section is not read as a change"


def test_r014_prose_headings_stay_prose():
    """R2-1: `## Settings`, `## Setup`, `## Additional notes`, `## Replacement history` in the pass root are prose."""
    text = (REPO / FIX / "pass/types/host-extension.md").read_text(encoding="utf-8")
    for heading in ("## Settings", "## Setup", "## Additional notes", "## Replacement history"):
        assert f"\n{heading}\n" in text, heading
    rc, lines, err = run(f"{FIX}/pass")
    assert rc == 0 and lines[-1] == "RESULT: OK", lines


def test_r014_bad_prefix_on_a_single_line_is_form_only():
    """R2-6: a line that fails the prefix rule is not checked further."""
    rc, lines, err = status("form-bad-prefix-single.md")
    assert rc == 1
    assert len(fails(lines)) == 1 and fails(lines)[0].startswith("FAIL (form) "), lines


def test_r014_empty_head_segment_is_form_not_unknown():
    """R2-7."""
    rc, lines, err = status("form-empty-segment.md")
    assert rc == 1
    assert not [line for line in fails(lines) if line.startswith("FAIL (unknown)")], lines


def test_r014_repeated_unwritten_trait_is_flagged_once():
    """R2-8."""
    rc, lines, err = status("flag-repeated-unwritten.md")
    assert rc == 1
    assert len([line for line in lines if line.startswith("FLAG (trait)") and ": Spends money - " in line]) == 1, lines
    assert any(line.startswith("FAIL (form) ") for line in lines), lines


def test_r014_separator_row_missing(tmp_path):
    """R2-9."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    broken = tmp_path / "open-list.md"
    sep = "| Key | Name | Definition | Workflow name | Default traits | Written | Planned |\n|---|---|---|---|---|---|---|\n"
    assert sep in text
    broken.write_text(text.replace(sep, sep.split("\n")[0] + "\n", 1), encoding="utf-8")
    assert_not_checked(*run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md"))


def test_r014_usage_error_ends_with_result_line():
    """R2-10."""
    rc, lines, err = run("--no-such-option")
    assert rc == 2
    assert lines and lines[-1] == "RESULT: not checked", (lines, err)
    assert "Traceback" not in err


def test_r014_control_characters_are_escaped(tmp_path):
    """R2-11: an escape and a bell in a heading target reach the output as \\x1b and \\x07, never raw."""
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "types" / "host-extension.md").write_text("## Add at intake.x\x1b[31mred\x07\n\nq\n", encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, str(root)], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 1, p.stdout
    assert "\x1b" not in p.stdout and "\x07" not in p.stdout, repr(p.stdout)
    assert "intake.x\\x1b[31mred\\x07" in p.stdout, p.stdout


def _link_folder(link, target):
    """A junction on Windows (no privilege needed), a symbolic link elsewhere."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(str(target), str(link), target_is_directory=True)


def test_r014_links_are_not_followed(tmp_path):
    """R2-4: a linked folder under types/ is form and is never read; a link to a parent cannot loop."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "claude-code-extension.md").write_text("## Add at nowhere.at-all\n\nq\n", encoding="utf-8")
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "types" / "host-extension.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    _link_folder(root / "types" / "host-extension", outside)
    _link_folder(root / "types" / "loop", root)
    p = subprocess.run([sys.executable, PROG, str(root)], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", timeout=60)
    lines = p.stdout.splitlines()
    assert p.returncode == 1, lines
    assert not [line for line in lines if line.startswith("FAIL (a)")], "a file behind a link was read"
    shown = str(root).replace("\\", "/")
    assert any(line.startswith(f"FAIL (form) {shown}/types/host-extension") for line in lines), lines
    assert lines[-1] == f"RESULT: {len(fails(lines))} problem(s)"


@pytest.mark.skipif(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0), reason="a folder made unreadable by mode bits needs a non-root POSIX user (CI's ubuntu leg)")
def test_r014_unreadable_folder_stops_the_check(tmp_path):
    """R2-3."""
    root = tmp_path / "root"
    sub = root / "types" / "host-extension"
    sub.mkdir(parents=True)
    (root / "types" / "host-extension.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    (sub / "claude-code-extension.md").write_text("## Add at nowhere.at-all\n\nq\n", encoding="utf-8")
    sub.chmod(0)
    try:
        assert_not_checked(*run(str(root)))
    finally:
        sub.chmod(0o755)


# --- the CI step (R-033) ------------------------------------------------------------------------------------------

def _jobs():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def test_r033_ci_runs_the_check_last_in_the_tests_job():
    step = _jobs()["tests"]["steps"][-1]
    assert step.get("run") == "python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass", step
    assert set(step) == {"name", "run"}, f"the step carries only a name and its command: {step}"
    assert "PROJECT_STATUS" not in step["run"] and "--status" not in step["run"]


def test_r033_ci_check_is_not_in_the_security_floor():
    steps = _jobs()["security-floor"]["steps"]
    assert not any("workflow-check" in str(s) for s in steps)
