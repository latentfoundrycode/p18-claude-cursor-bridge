"""workflow-check.py (TASK-006), the supervisor's tests, written from handoff/TASK-006.md before the delegation.

enforces: docs/REQUIREMENTS.md R-014 (every change targets an existing extension point; replace/set only in a type or
sub-workflow, replace only on a replaceable phase; trait additions only add; a sub-workflow names an existing type
workflow; a `Workflows:` line names one product type, at most one of its sub-types, and traits, all in the open list;
an unwritten type or sub-type fails, an unwritten trait is flagged and non-fatal) and R-033 (the check runs at every
bridge release, in CI). The fixtures are tests/fixtures/workflows/: `pass/` is the CI root, `fail/<case>/` one root per
failing case, `status/` the status-line cases with an open list of their own.
"""
import codecs
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
    type_text = (pass_root / "types/host-extension.md").read_text(encoding="utf-8")
    assert "## Replace interface" in type_text
    assert "\n```\n## Replace design\n## Add at nowhere.at-all\n```\n" in type_text, "precondition: the column-0 fence pair"
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
    ("form-unclosed-fence", "form", "types/host-extension.md", "-"),
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


@pytest.mark.parametrize("name", ["ok-single.md", "ok-multi.md", "ok-unclassified.md", "bom-workflows-line.md"])
def test_r014_status_ok(name):
    """bom-workflows-line.md is not a whole status file (it has no `Phase:` line, which check_placement would refuse);
    it holds one `Workflows:` line after a byte-order mark, the case only check_status reads."""
    rc, lines, err = status(name)
    assert_clean_end(lines, err)
    assert rc == 0 and lines[-1] == "RESULT: OK", lines
    assert not [line for line in lines if line.startswith(("FAIL", "FLAG"))], lines


@pytest.mark.parametrize("inner", ["fail/b-trait-sets-bom/traits/has-screens.md", "status/bom-workflows-line.md"])
def test_r014_bom_fixtures_carry_their_bom(inner):
    """The two byte-order-mark cases test nothing if an editor drops the mark (stage B2 review)."""
    assert (REPO / FIX / inner).read_bytes().startswith(codecs.BOM_UTF8), inner


def _status_line_case(tmp_path, line):
    path = tmp_path / "status.md"
    path.write_text("Phase: building\n" + line + "\n", encoding="utf-8", newline="\n")
    return run("--open-list", STATUS_LIST, "--status", str(path))


@pytest.mark.parametrize("line", [
    "Workflows: Host Extension Development → Claude Code Extension; traits: Installable",
    "Workflows: app: Web App Development; traits: Has screens, Installable",
], ids=["single", "with-part"])
def test_r015_exact_separators_pass(tmp_path, line):
    """The control for the case below: the grammar's own separators pass."""
    if line.startswith("Workflows: app: "):
        line = line + "\nWorkflows: plugin: Host Extension Development → Browser Extension; traits: none"
    rc, lines, err = _status_line_case(tmp_path, line)
    assert rc == 0 and lines[-1] == "RESULT: OK", lines


@pytest.mark.parametrize("line", [
    "Workflows: Host Extension Development→Claude Code Extension; traits: Installable",
    "Workflows: Host Extension Development  → Claude Code Extension; traits: Installable",
    "Workflows: Host Extension Development →  Claude Code Extension; traits: Installable",
    "Workflows:  Host Extension Development; traits: Installable",
    "Workflows: Host Extension Development ; traits: Installable",
    "Workflows: app:  Web App Development; traits: none\nWorkflows: plugin: Host Extension Development; traits: none",
], ids=["arrow-unspaced", "two-spaces-before-arrow", "two-spaces-after-arrow", "two-spaces-after-colon",
        "space-before-traits-mark", "two-spaces-after-part"])
def test_r015_separators_are_exact(tmp_path, line):
    """supervisor.md "Project state": the head is `<Workflow name>[ → <Sub-workflow name>]` exactly, after `Workflows: `
    or `<part>: `; any other spacing is (form), as it already is for a part name or the traits (stage B2 review)."""
    rc, lines, err = _status_line_case(tmp_path, line)
    assert_clean_end(lines, err)
    assert rc == 1, lines
    assert any(line.startswith("FAIL (form) ")
               and line.endswith(" - Workflows head is not the product type, then at most its sub-type")
               for line in fails(lines)), lines


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
    ("form-part-whitespace.md", "form", None),
    ("form-part-blank.md", "form", None),
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


def test_r014_unwritten_type_fails_against_the_real_open_list(tmp_path):
    """The pause (§6.7) against the bridge's own open list: a copy with every entry marked unwritten, so the test still
    holds once release B writes its first workflows (TASK-017 to TASK-021; stage B2 review)."""
    real = (REPO / "bridge" / "cursor-bridge" / "workflow" / "open-list.md").read_text(encoding="utf-8")
    copy = tmp_path / "open-list.md"
    copy.write_text(real.replace("| yes |", "| no |"), encoding="utf-8", newline="\n")
    assert "| yes |" not in copy.read_text(encoding="utf-8")
    rc, lines, err = run("--open-list", str(copy), "--status", f"{FIX}/status/ok-single.md")
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


# --- round 3: the second review's corrections (handoff/TASK-006-r3.md) --------------------------------------------

def test_r014_misspelt_heading_section_is_not_read_as_a_change():
    """R2-1 with its precondition: `## Sets at intake.questions` in a trait file would give (b) and (set) if read as a
    change; it gives one (form) and nothing else."""
    root = f"{FIX}/fail/form-misspelt-in-trait"
    rc, lines, err = run(root)
    assert rc == 1
    assert len(fails(lines)) == 1 and fails(lines)[0].startswith(f"FAIL (form) {root}/traits/installable.md: - "), lines


def test_r014_change_word_with_punctuation_is_form():
    """R3-4: `## Set:`, `## Add:`, `## Replace:`, `## Adding`, `## Setting` are malformed change headings; a trait's
    `## Set:` no longer escapes."""
    root = f"{FIX}/fail/form-change-word-punctuation"
    rc, lines, err = run(root)
    assert rc == 1
    forms = [line for line in fails(lines) if line.startswith(f"FAIL (form) {root}/traits/installable.md: - ")]
    assert len(forms) == 5 and len(fails(lines)) == 5, lines
    text = (REPO / FIX / "pass/types/host-extension.md").read_text(encoding="utf-8")
    assert "\n## Add-ons\n" in text, "the pass root keeps `## Add-ons` as prose"


def test_r014_indented_or_tabbed_change_heading_is_form():
    """R3-6: ` ## Set at x` and `##<tab>Add at x` are heading candidates that fail the exact forms."""
    root = f"{FIX}/fail/form-indented-heading"
    text = (REPO / root / "types/host-extension.md").read_text(encoding="utf-8")
    assert "\n##" + chr(9) + "Add at intake.questions\n" in text, "precondition: the tab survives"
    rc, lines, err = run(root)
    assert rc == 1
    assert len([line for line in fails(lines) if line.startswith(f"FAIL (form) {root}/types/host-extension.md: ")]) == 2, lines


def test_r014_usage_error_message_is_escaped():
    """R3-1: an argument holding a newline cannot start a GitHub workflow command on standard error."""
    rc, lines, err = run("--bogus\n::warning::injected")
    assert rc == 2 and lines[-1] == "RESULT: not checked", (lines, err)
    assert "\n::warning::" not in err and not err.startswith("::warning::"), err
    assert "\\x0a::warning::injected" in err, err


@pytest.mark.parametrize("sep", ["|---|", "|---|---|---|---|---|---|---|---|"], ids=["one-cell", "eight-cells"])
def test_r014_separator_cell_count_differs(tmp_path, sep):
    """R3-2."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    good = "| Key | Name | Definition | Workflow name | Default traits | Written | Planned |\n|---|---|---|---|---|---|---|\n"
    assert good in text
    broken = tmp_path / "open-list.md"
    broken.write_text(text.replace(good, good.split("\n")[0] + "\n" + sep + "\n", 1), encoding="utf-8")
    assert_not_checked(*run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md"))


def _outside_with_canary(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "host-extension.md").write_text("## Add at nowhere.at-all\n\nq\n", encoding="utf-8")
    (outside / "claude-code-extension.md").write_text("## Add at nowhere.at-all\n\nq\n", encoding="utf-8")
    return outside


def test_r014_link_under_an_unknown_type_folder_is_form(tmp_path):
    """R3-3: the unknown folder keeps its (d); the link inside it is (form) at its own path. (Whether it is read is not
    tested here: the check reads no file under an unknown type folder, link or not; test_r014_top_level_link_is_form_and_not_walked
    tests a link that would be read.)"""
    outside = _outside_with_canary(tmp_path)
    root = tmp_path / "root"
    (root / "types" / "not-a-type").mkdir(parents=True)
    _link_folder(root / "types" / "not-a-type" / "out", outside)
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/")
    assert rc == 1, lines
    assert any(line.startswith(f"FAIL (d) {shown}/types/not-a-type") for line in lines), lines
    assert any(line.startswith(f"FAIL (form) {shown}/types/not-a-type/out") for line in lines), lines


def test_r014_top_level_link_is_form_and_not_walked(tmp_path):
    """R3-3: ROOT/types as a link, and ROOT/traits as a dangling link, are each (form) at their own path."""
    outside = _outside_with_canary(tmp_path)
    gone = tmp_path / "gone"
    gone.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    _link_folder(root / "types", outside)
    _link_folder(root / "traits", gone)
    gone.rmdir()
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/")
    assert rc == 1, lines
    assert any(line.startswith(f"FAIL (form) {shown}/types") for line in lines), lines
    assert any(line.startswith(f"FAIL (form) {shown}/traits") for line in lines), lines
    assert not [line for line in lines if line.startswith("FAIL (a)")], "a file behind a link was read"


@pytest.mark.skipif(os.name != "nt", reason="a junction exists only on Windows")
def test_r014_junction_detected_without_isjunction(tmp_path, monkeypatch, program):
    """R3-7: with os.path.isjunction absent (a Python before 3.12), a junction still counts as a link."""
    mod = program("workflow-check")
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    _link_folder(link, target)
    assert mod.is_link(str(link))
    monkeypatch.delattr(os.path, "isjunction", raising=False)
    assert mod.is_link(str(link)), "the fallback must see the reparse point"
    assert not mod.is_link(str(target))


# --- round 4: the third review's corrections (handoff/TASK-006-r4.md) ---------------------------------------------

def _main_in_process(mod, *args, capsys):
    code = mod.main(list(args))
    return code, capsys.readouterr().out.splitlines()


@pytest.mark.parametrize("isjunction", ["present", "absent"])
def test_r014_missing_layer_folder_is_not_a_link(tmp_path, monkeypatch, capsys, program, isjunction):
    """R4-1: a root with no traits/, and a root with neither layer, pass whether or not os.path.isjunction exists; on
    Windows its absence takes the lstat fallback, which once counted a missing path as a link. Both roots are built
    here, not the bridge's own folder, which gains its layers in stage B4 (stage B2 review)."""
    mod = program("workflow-check")
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "types" / "host-extension.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    bare = tmp_path / "bare"
    bare.mkdir()
    if isjunction == "absent":
        monkeypatch.delattr(os.path, "isjunction", raising=False)
    for target in (root, bare):
        code, lines = _main_in_process(mod, str(target), capsys=capsys)
        assert code == 0 and lines[-1] == "RESULT: OK", (target, lines)


def test_r014_missing_layer_is_skipped_before_the_link_test(tmp_path, monkeypatch, capsys, program):
    """R4-1: a layer path that does not exist is skipped before it is classified, so even a classifier that calls
    everything a link reports nothing for a root with neither types/ nor traits/ (built here: the bridge's own folder
    gains its layers in stage B4; stage B2 review)."""
    mod = program("workflow-check")
    bare = tmp_path / "bare"
    bare.mkdir()
    monkeypatch.setattr(mod, "is_link", lambda path: True)
    code, lines = _main_in_process(mod, str(bare), capsys=capsys)
    assert code == 0 and lines[-1] == "RESULT: OK", lines


@pytest.mark.parametrize("isjunction", ["present", "absent"])
def test_r014_is_link_false_for_a_path_that_does_not_exist(tmp_path, monkeypatch, program, isjunction):
    """R4-1, R4-2: nothing there, and a path below a file, are not links on either branch."""
    mod = program("workflow-check")
    afile = tmp_path / "a-file"
    afile.write_text("x", encoding="utf-8")
    if isjunction == "absent":
        monkeypatch.delattr(os.path, "isjunction", raising=False)
    assert not mod.is_link(str(tmp_path / "nothing-here"))
    assert not mod.is_link(str(afile / "below-a-file"))


@pytest.mark.parametrize("isjunction", ["present", "absent"])
@pytest.mark.parametrize("error,expected", [(PermissionError, True), (OSError, True), (FileNotFoundError, False), (NotADirectoryError, False)])
def test_r014_lstat_error_follows_one_rule(tmp_path, monkeypatch, program, error, expected, isjunction):
    """R5-2 (replacing R4-2's two branches): is_link reads os.lstat once on every Python and platform; an error other
    than a missing path is a link (fail closed), a missing path is not."""
    mod = program("workflow-check")

    def raises(path, *a, **k):
        raise error("probe")

    if isjunction == "absent":
        monkeypatch.delattr(os.path, "isjunction", raising=False)
    monkeypatch.setattr(os, "lstat", raises)
    assert mod.is_link(str(tmp_path / "probe")) is expected


def test_r014_is_link_does_not_use_isjunction(tmp_path, monkeypatch, program):
    """R5-2: os.path.isjunction no longer decides; an isjunction that calls every path a junction changes nothing."""
    mod = program("workflow-check")
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.setattr(os.path, "isjunction", lambda path: True, raising=False)
    assert not mod.is_link(str(plain))
    assert not mod.is_link(str(tmp_path / "nothing-here"))


# --- round 5: the fourth review's corrections (handoff/TASK-006-r5.md) --------------------------------------------

@pytest.mark.parametrize("layer", ["types", "traits"])
def test_r014_layer_that_cannot_be_examined_stops_the_check(tmp_path, monkeypatch, capsys, program, layer):
    """R5-1: an lstat error on ROOT/types or ROOT/traits other than a missing path is an input the check cannot read:
    an ERROR line for that path and `RESULT: not checked`, exit 2; never an empty root that passes."""
    mod = program("workflow-check")
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "traits").mkdir()
    real = os.lstat

    def lstat(path, *a, **k):
        if os.path.basename(os.fspath(path)) == layer:
            raise PermissionError(13, "Permission denied", os.fspath(path))
        return real(path, *a, **k)

    monkeypatch.setattr(os, "lstat", lstat)
    code, lines = _main_in_process(mod, str(root), capsys=capsys)
    assert code == 2, lines
    assert lines[-1] == "RESULT: not checked", lines
    shown = str(root).replace("\\", "/")
    assert any(line.startswith("ERROR: ") and f"{shown}/{layer}" in line.replace("\\", "/") for line in lines), lines


def test_r014_tilde_fences_and_longer_runs_hide_headings():
    """R5-3: in the pass root's trait file a tilde fence hides a trait's `## Set` (b), and a four-tilde fence holding a
    four-backtick line (the other character, long enough) and a shorter tilde line hides `## Replace design` (b) until
    its own four-tilde close."""
    text = (REPO / FIX / "pass/traits/installable.md").read_text(encoding="utf-8")
    assert "\n~~~\n## Set at intake.delivery-kind\n~~~\n" in text, "precondition: a tilde fence hides a Set"
    assert "\n~~~~\n````\n## Replace design\n~~~\n~~~~" in text, "precondition: a longer tilde fence hides a Replace"
    assert "\n~~~a`b\n## Set at intake.delivery-kind\n~~~" in text, "precondition: a backtick in a tilde info string still opens"
    rc, lines, err = run(f"{FIX}/pass")
    assert rc == 0 and lines[-1] == "RESULT: OK", lines


@pytest.mark.parametrize("case", ["fence-longer-opening", "fence-info-string-not-closing", "fence-backtick-in-info", "fence-close-trailing-space"])
def test_r014_commonmark_fence_cases_read_the_set(case):
    """R5-3: a shorter run does not close a longer fence; a backtick line with text after it does not close; a backtick
    line whose info string holds a backtick does not open; a closing run followed only by spaces closes. In each the
    trait's `## Set` is read and is the one (b), with no open fence left."""
    root = f"{FIX}/fail/{case}"
    if case == "fence-close-trailing-space":
        text = (REPO / root / "traits/installable.md").read_text(encoding="utf-8")
        assert "\n```   \n" in text, "precondition: the closing run keeps its trailing spaces"
    rc, lines, err = run(root)
    assert_clean_end(lines, err)
    assert rc == 1
    assert fails(lines) == [f"FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add"], lines


def test_r014_indented_fence_pair_hides_a_heading():
    """R4-3: the pass root holds a fence pair indented by two and three spaces around a heading that, read, is (c)."""
    text = (REPO / FIX / "pass/types/host-extension.md").read_text(encoding="utf-8")
    assert "\n  ```\n## Replace design\n   ```" in text, "the precondition: an indented fence pair hides `## Replace design`"
    rc, lines, err = run(f"{FIX}/pass")
    assert rc == 0 and lines[-1] == "RESULT: OK", lines


def test_r014_indented_closing_fence_closes_the_block():
    """R4-3: a column-0 fence closed by one indented three spaces; the trait's `## Set` after it is read and is (b)."""
    root = f"{FIX}/fail/fence-indented-close"
    rc, lines, err = run(root)
    assert_clean_end(lines, err)
    assert rc == 1
    assert fails(lines) == [f"FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add"], lines


def test_r014_four_spaces_is_not_a_fence():
    """R4-3: backticks indented four spaces are an indented code block, not a fence; the `## Set` after them is (b) and
    no fence is left open."""
    root = f"{FIX}/fail/fence-four-spaces"
    rc, lines, err = run(root)
    assert rc == 1
    assert fails(lines) == [f"FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add"], lines


def test_r014_unclosed_indented_fence_is_form():
    """R4-3 with R3-6: an indented opening fence never closed hides the heading after it and is one (form)."""
    root = f"{FIX}/fail/form-indented-fence-open"
    rc, lines, err = run(root)
    assert rc == 1
    assert fails(lines) == [f"FAIL (form) {root}/types/host-extension.md: - - fenced code block is still open at the end of the file"], lines


# --- round 6: the fifth review's corrections (handoff/TASK-006-r6.md) ---------------------------------------------

LIBRARY_ROW = "| library | Library | Included by other programs | Library Development | — | no | — |"


@pytest.mark.parametrize("row", [LIBRARY_ROW + "|", "|" + LIBRARY_ROW], ids=["trailing-double-pipe", "leading-double-pipe"])
def test_r014_double_pipe_row_is_a_cell_count_error(tmp_path, row):
    """R6-1: a row ending or starting `||` keeps its empty cell, so its count differs from the header's: exit 2."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    assert "\n" + LIBRARY_ROW + "\n" in text, "precondition: the row the test breaks"
    broken = tmp_path / "open-list.md"
    broken.write_text(text.replace("\n" + LIBRARY_ROW + "\n", "\n" + row + "\n", 1), encoding="utf-8")
    rc, lines, err = run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md")
    assert_not_checked(rc, lines, err)
    assert any("table row cell count differs from its header" in line for line in lines), lines


def test_r014_separator_with_double_pipe_is_not_a_separator(tmp_path):
    """R6-1 with R3-2: a separator ending `||` has one cell too many."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    good = "| Key | Name | Definition | Workflow name | Default traits | Written | Planned |\n|---|---|---|---|---|---|---|\n"
    assert good in text
    broken = tmp_path / "open-list.md"
    broken.write_text(text.replace(good, good.rstrip("\n") + "|\n", 1), encoding="utf-8")
    assert_not_checked(*run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md"))


@pytest.mark.parametrize("sep", ["\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"],
                         ids=["vt", "ff", "fs", "gs", "rs", "nel", "ls", "ps"])
def test_r014_lines_end_only_at_line_feeds(tmp_path, sep):
    """R6-2: two lines joined to text by a character Markdown does not end a line at are not fences, so the trait's
    `## Set` between them is read and is the one (b)."""
    root = tmp_path / "root"
    (root / "traits").mkdir(parents=True)
    body = f"## Add at intake.questions\n\nq\n\na{sep}```\n\n## Set at intake.delivery-kind\n\ninstaller\n\nb{sep}```\n"
    (root / "traits" / "installable.md").write_text(body, encoding="utf-8", newline="\n")
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/")
    assert rc == 1, lines
    assert fails(lines) == [f"FAIL (b) {shown}/traits/installable.md: intake.delivery-kind - a trait file may only add"], lines


def test_r014_table_row_holding_a_line_separator_is_one_row(tmp_path):
    """R6-2 in parse_table: a U+2028 inside a cell keeps the row whole; split there, its first part would be a short row
    and the check would stop (exit 2)."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    assert "\n" + LIBRARY_ROW + "\n" in text
    lsep = LIBRARY_ROW.replace("Included by other programs", "Included by\u2028other programs")
    changed = tmp_path / "open-list.md"
    changed.write_text(text.replace("\n" + LIBRARY_ROW + "\n", "\n" + lsep + "\n", 1), encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", str(changed), "--status", f"{FIX}/status/ok-single.md")
    assert rc == 0 and lines[-1] == "RESULT: OK", lines


def test_r014_workflows_line_after_a_form_feed_is_not_a_line(tmp_path):
    """R6-2 in the status check: `Workflows:` joined to the line before it by a form feed does not begin a line, so the
    file has no Workflows line (form)."""
    text = (REPO / FIX / "status/ok-single.md").read_text(encoding="utf-8")
    assert "\nWorkflows: " in text
    status = tmp_path / "status.md"
    status.write_text(text.replace("\nWorkflows: ", "\x0cWorkflows: ", 1), encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", STATUS_LIST, "--status", str(status))
    assert rc == 1, lines
    assert len(fails(lines)) == 1 and "status file has no Workflows line" in fails(lines)[0], lines


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
