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
import shutil
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


def test_r014_a_file_sets_each_point_at_most_once():
    """extension-points.md, "How a conditional workflow names a point": a file sets each point at most once, so two Sets
    of different points in one file pass, where two of the same point are (form) (form-two-sets) (Review A, BUG-005
    gate round 2)."""
    type_text = (REPO / FIX / "pass/types/host-extension.md").read_text(encoding="utf-8")
    assert "\n## Set at intake.delivery-kind\n" in type_text and "\n## Set at intake.target-environment\n" in type_text, \
        "precondition: the pass root's type workflow sets two different points outside a fence"
    code, lines, err = run(f"{FIX}/pass")
    assert lines == whole_output([]) and err == "" and code == 0, (lines, err)


def test_r014_replaced_module_keeps_its_points():
    """Carry item 1 (Requirement 10): the trait has-screens and the sub-workflow add at interface.variants while the
    type workflow replaces interface; the fixture's fenced `## Replace design` and prose headings are not changes."""
    pass_root = REPO / FIX / "pass"
    type_text = (pass_root / "types/host-extension.md").read_text(encoding="utf-8")
    assert "## Replace interface" in type_text
    assert "\n```\n## Replace design\n## Add at nowhere.at-all\n```\n" in type_text, "precondition: the column-0 fence pair"
    assert "## Add at interface.variants" in (pass_root / "traits/has-screens.md").read_text(encoding="utf-8")
    sub_text = (pass_root / "types/host-extension/claude-code-extension.md").read_text(encoding="utf-8")
    assert "## Add at interface.variants" in sub_text
    code, lines, err = run(f"{FIX}/pass")
    assert code == 0 and lines[-1] == "RESULT: OK", lines


def test_r014_pass_root_holds_its_only_cases():
    """Two lines of the pass root are the only fixtures of their rule, so the pass root's OK proves the rule only while
    they stand (stage B2 review, round 3: fixtures 2): a third-level heading is prose (TASK-006 Requirement 7), and a Set
    value may be written in backticks."""
    type_text = (REPO / FIX / "pass/types/host-extension.md").read_text(encoding="utf-8")
    assert "\n### Add at not.a-change\n" in type_text, "precondition: a deeper heading that would be (a) if read"
    assert "\n## Set at intake.delivery-kind\n\n`host-installation`\n" in type_text, "precondition: a backticked Set value"
    # TASK-006 Requirements 7 to 9, each held by one line of the pass root (stage B2 review, round 4: fixtures 2).
    sub_text = (REPO / FIX / "pass/types/host-extension/claude-code-extension.md").read_text(encoding="utf-8")
    assert "\n## Set at intake.delivery-kind\n" in sub_text, "precondition: a sub-workflow sets what its type sets"
    assert "\n## Replace interface\n" in sub_text and "\n## Replace interface\n" in type_text, \
        "precondition: a sub-workflow replaces what its type replaces"
    trait_text = (REPO / FIX / "pass/traits/installable.md").read_text(encoding="utf-8")
    assert trait_text.count("\n## Add at intake.questions\n") == 2, "precondition: two additions at one point in one file"
    assert ("\n## Add at project-end.delivery for installer\n" in trait_text
            and "\n## Add at project-end.delivery for package\n" in trait_text), "precondition: several delivery kinds in one file"


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
    assert_clean_end(lines, err)
    assert rc == 1
    codes = {line.split(")")[0] for line in fails(lines)}
    assert {"FAIL (b", "FAIL (a"} <= codes, lines


def test_r014_fail_root_beside_the_pass_root_is_reported_in_argument_order():
    rc, lines, err = run(f"{FIX}/pass", f"{FIX}/fail/c-not-replaceable")
    assert rc == 1
    assert fails(lines) == [line for line in lines if line.startswith(f"FAIL (c) {FIX}/fail/c-not-replaceable/")], lines


def findings_of(*args):
    rc, lines, err = run(*args)
    assert_clean_end(lines, err)
    return [line for line in lines if line.startswith(("FAIL (", "FLAG ("))]


@pytest.mark.parametrize("first,second", [("c-not-replaceable", "a-unknown-point"), ("a-unknown-point", "c-not-replaceable")])
def test_r014_roots_are_reported_in_argument_order(first, second):
    """TASK-006: finding lines come roots in argument order, files in sorted path order, then status files in argument
    order. Two failing roots, in both orders: c- before a- is not the sorted order of their paths, so a check that
    sorted across roots fails one of the two (stage B2 review, round 3: Review A, tests part)."""
    one, two = f"{FIX}/fail/{first}", f"{FIX}/fail/{second}"
    expected = findings_of(one) + findings_of(two)
    assert findings_of(one) and findings_of(two), "precondition: each root fails on its own"
    assert findings_of(one, two) == expected


@pytest.mark.parametrize("first,second", [("unknown-trait.md", "f-unwritten-type.md"), ("f-unwritten-type.md", "unknown-trait.md")])
def test_r014_status_files_are_reported_in_argument_order(first, second):
    """TASK-006: status files in argument order, in both orders (stage B2 review, round 3: Review A, tests part)."""
    one, two = f"{FIX}/status/{first}", f"{FIX}/status/{second}"
    single = [findings_of("--open-list", STATUS_LIST, "--status", path) for path in (one, two)]
    assert single[0] and single[1], "precondition: each status file fails on its own"
    assert findings_of("--open-list", STATUS_LIST, "--status", one, "--status", two) == single[0] + single[1]


def test_r014_roots_come_before_status_files():
    """The status file is given first on the command line; its findings still follow the root's."""
    root, path = f"{FIX}/fail/c-not-replaceable", f"{FIX}/status/unknown-trait.md"
    from_root = findings_of("--open-list", STATUS_LIST, root)
    from_status = findings_of("--open-list", STATUS_LIST, "--status", path)
    assert from_root and from_status, "precondition: each fails on its own"
    assert findings_of("--open-list", STATUS_LIST, "--status", path, root) == from_root + from_status


# --- the status files ---------------------------------------------------------------------------------------------

def status(name):
    return run("--open-list", STATUS_LIST, "--status", f"{FIX}/status/{name}")


@pytest.mark.parametrize("name", ["ok-single.md", "ok-multi.md", "ok-multi-unclassified.md", "ok-no-final-newline.md", "ok-unclassified.md", "bom-workflows-line.md"])
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
    "Workflows: Host Extension Development , Installable; traits: none",
], ids=["arrow-unspaced", "two-spaces-before-arrow", "two-spaces-after-arrow", "two-spaces-after-colon",
        "space-before-traits-mark", "two-spaces-after-part", "space-before-comma"])
def test_r015_separators_are_exact(tmp_path, line):
    """supervisor.md "Project state": the head is `<Workflow name>[ → <Sub-workflow name>]` exactly, after `Workflows: `
    or `<part>: `; any other spacing is (form), as it already is for a part name or the traits (stage B2 review)."""
    rc, lines, err = _status_line_case(tmp_path, line)
    assert_clean_end(lines, err)
    assert rc == 1, lines
    # The whole output: the shape finding alone. Each name is read stripped (handoff/TASK-006.md R11.4), so a space
    # before a comma still finds `Host Extension Development` and only the shape fails; a name stripped on one side only
    # would add an (unknown) and an (e) (BUG-006 r2: Review A, the sweep's line 605).
    shown = str(tmp_path / "status.md").replace("\\", "/")
    assert lines == whole_output([f"FAIL (form) {shown}: - - Workflows head is not the product type, then at most its sub-type"]), lines
    assert err == "", err


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


def test_r014_trait_in_head_is_only_the_shape_finding():
    """R-014: a trait's Name is in the open list, so a trait beside the product type in the Workflows head is the shape
    (form) finding alone, never (unknown); a lone trait gives only the (e) finding, before the shape test (BUG-002 round 2
    review: no test held check_head's trait branch exactly; the lone trait's case added at stage B2's review, round 3)."""
    rc, lines, err = status("form-trait-in-head.md")
    assert_clean_end(lines, err)
    assert rc == 1, lines
    assert fails(lines) == [f"FAIL (form) {FIX}/status/form-trait-in-head.md: - - "
                            "Workflows head is not the product type, then at most its sub-type"], lines
    rc, lines, err = status("e-lone-trait.md")
    assert rc == 1, lines
    assert fails(lines) == [f"FAIL (e) {FIX}/status/e-lone-trait.md: - - part must name exactly one product type"], lines


# --- every case's exact findings (stage B2 review, round 2: a second finding must not hide the named one) -----------

# Each list is the case's whole output of FAIL and FLAG lines, in order. {root} is the case's root, {path} the status file.
FILE_EXACT = {
    'a-set-unknown-point': ['FAIL (a) {root}/types/host-extension.md: intake.delivery-kinds - point is not in the extension-point registry'],
    'a-unknown-point': ['FAIL (a) {root}/types/host-extension.md: intake.question - point is not in the extension-point registry'],
    'b-and-a': [
        'FAIL (b) {root}/traits/installable.md: nowhere.point - a trait file may only add',
        'FAIL (a) {root}/traits/installable.md: nowhere.point - point is not in the extension-point registry',
    ],
    'b-trait-replaces': ['FAIL (b) {root}/traits/has-screens.md: interface - a trait file may only add'],
    'b-trait-sets': ['FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add'],
    'b-trait-sets-bom': ['FAIL (b) {root}/traits/has-screens.md: intake.delivery-kind - a trait file may only add'],
    'c-not-replaceable': ['FAIL (c) {root}/types/host-extension.md: design - module is missing or not replaceable'],
    'c-unknown-module': ['FAIL (c) {root}/types/host-extension.md: testing - module is missing or not replaceable'],
    # A file failing its identity still has its changes checked (stage B2 review, round 6: tests, fixtures 2).
    'd-sub-type-of-another': [
        'FAIL (d) {root}/types/web-app/claude-code-extension.md: claude-code-extension - not a sub-type of web-app',
        'FAIL (a) {root}/types/web-app/claude-code-extension.md: nowhere.at-all - point is not in the extension-point registry',
    ],
    # A sub-workflow file whose key is no sub-type at all (stage B2 review, round 5: tests).
    'd-unknown-sub-type-key': ['FAIL (d) {root}/types/host-extension/claude-code-extention.md: claude-code-extention - not a sub-type of host-extension'],
    'd-type-file-missing': [
        'FAIL (d) {root}/types/host-extension/claude-code-extension.md: claude-code-extension - type workflow types/host-extension.md does not exist',
        'FAIL (a) {root}/types/host-extension/claude-code-extension.md: nowhere.at-all - point is not in the extension-point registry',
    ],
    'd-unknown-type-folder': ['FAIL (d) {root}/types/not-a-type: not-a-type - type folder is not a product type'],
    'fence-backtick-in-info': ['FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add'],
    'fence-close-trailing-space': ['FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add'],
    'fence-four-spaces': ['FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add'],
    'fence-indented-close': ['FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add'],
    'fence-info-string-not-closing': ['FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add'],
    'fence-longer-opening': ['FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add'],
    'form-bad-heading': ['FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms'],
    # Each stripped punctuation mark, and two marks on one word (stage B2 review, round 5: fixtures 1).
    'form-change-word-punctuation': [
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms',
    ],
    'form-empty-set': ['FAIL (form) {root}/types/host-extension.md: intake.target-environment - Set at section has no non-blank line'],
    # A section ends at the next `##` heading, a prose one too, so a Set right above one is empty (stage B2 review,
    # round 6: tests and fixtures 2, converged).
    'form-empty-set-before-prose': [
        'FAIL (form) {root}/types/host-extension.md: intake.target-environment - Set at section has no non-blank line',
        'FAIL (form) {root}/types/host-extension.md: intake.delivery-kind - Set at section has no non-blank line',
        'FAIL (kind) {root}/types/host-extension.md: - - Set at intake.delivery-kind is not one delivery kind',
    ],
    # Each form matched exactly: text after the key or the kind, and a space after the key (round 6: tests).
    'form-heading-trailing-text': [
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
    ],
    'form-indented-fence-open': ['FAIL (form) {root}/types/host-extension.md: - - fenced code block is still open at the end of the file'],
    # One space, a tab, and three spaces, the most a heading may be indented (round 6: fixtures 1 and 2).
    'form-indented-heading': [
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
    ],
    # Every change word without `at`, a two-word heading ending `at`, and `AT` in capitals (stage B2 review, round 5:
    # fixtures 1, and the supervisor's mutation sweep).
    'form-misspelt-change-word': [
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
    ],
    'form-misspelt-in-trait': ['FAIL (form) {root}/traits/installable.md: - - change heading is not one of the four forms'],
    # A file that is not `.md` under traits/, under types/ and under a type's folder (round 6: tests, fixtures 2).
    'form-not-markdown': [
        'FAIL (form) {root}/traits/installable.txt: installable.txt - path is not a conditional-workflow file',
        'FAIL (form) {root}/types/host-extension/notes.txt: notes.txt - path is not a conditional-workflow file',
        'FAIL (form) {root}/types/host-extensionabc: host-extensionabc - path is not a conditional-workflow file',
    ],
    'form-third-level': [
        'FAIL (form) {root}/types/host-extension/claude-code-extension: claude-code-extension - path is not a conditional-workflow file',
        'FAIL (form) {root}/types/host-extension/claude-code-extension/extra.md: extra.md - path is not a conditional-workflow file',
    ],
    # A folder under traits/ (stage B2 review, round 5: fixtures 2), one named like a trait file too (round 6: the
    # sweep's line 364).
    'form-traits-folder': [
        'FAIL (form) {root}/traits/installable: installable - path is not a conditional-workflow file',
        'FAIL (form) {root}/traits/installable/extra.md: extra.md - path is not a conditional-workflow file',
        'FAIL (form) {root}/traits/odd.md: odd.md - path is not a conditional-workflow file',
        'FAIL (form) {root}/traits/odd.md/extra.md: extra.md - path is not a conditional-workflow file',
    ],
    'form-two-replaces': ['FAIL (form) {root}/types/host-extension.md: interface - two Replace headings for the same module'],
    'form-two-sets': ['FAIL (form) {root}/types/host-extension.md: intake.target-environment - two Set at headings for the same point'],
    'form-unclosed-fence': ['FAIL (form) {root}/types/host-extension.md: - - fenced code block is still open at the end of the file'],
    'kind-missing': ['FAIL (kind) {root}/types/host-extension.md: project-end.delivery - addition at project-end.delivery does not name a delivery kind'],
    # An unlisted kind on another point is both findings (stage B2 review, round 5: fixtures 2).
    'kind-on-another-point': [
        'FAIL (kind) {root}/types/host-extension.md: installer - delivery kind is named on a point other than project-end.delivery',
        'FAIL (kind) {root}/types/host-extension.md: docker-image - delivery kind is not in the delivery-kind list',
        'FAIL (kind) {root}/types/host-extension.md: docker-image - delivery kind is named on a point other than project-end.delivery',
    ],
    # A value with a backtick on one side only is not unwrapped, the trailing side (stage B2 review, round 5: the
    # supervisor's sweep) and the leading side (round 6: fixtures 2).
    'kind-set-value': [
        'FAIL (kind) {root}/types/host-extension.md: deployment - Set at intake.delivery-kind is not one delivery kind',
        'FAIL (kind) {root}/types/host-extension/browser-extension.md: `installer - Set at intake.delivery-kind is not one delivery kind',
        'FAIL (kind) {root}/types/host-extension/claude-code-extension.md: installer` - Set at intake.delivery-kind is not one delivery kind',
    ],
    # A line of `##` alone is no heading, so it is the Set's first non-blank line (BUG-006 r4: Review A, the heading shape).
    'kind-bare-hashes': ['FAIL (kind) {root}/types/host-extension.md: ## - Set at intake.delivery-kind is not one delivery kind'],
    # Two backticks are unwrapped to nothing, printed as `-` (round 6: the sweep's line 485; round 5's lead pinned).
    'kind-two-backticks': ['FAIL (kind) {root}/types/host-extension.md: - - Set at intake.delivery-kind is not one delivery kind'],
    'kind-unlisted': ['FAIL (kind) {root}/traits/installable.md: docker-image - delivery kind is not in the delivery-kind list'],
    'set-point-without-set': ['FAIL (set) {root}/types/host-extension.md: intake.questions - point does not accept set'],
    'sub-workflow-changes': [
        'FAIL (a) {root}/types/host-extension/claude-code-extension.md: intake.question - point is not in the extension-point registry',
        'FAIL (set) {root}/types/host-extension/claude-code-extension.md: intake.questions - point does not accept set',
        'FAIL (c) {root}/types/host-extension/claude-code-extension.md: design - module is missing or not replaceable',
    ],
    # A file of an unknown key still has its changes checked (round 6: tests, fixtures 2).
    'unknown-trait-file': [
        'FAIL (unknown) {root}/traits/not-a-trait.md: not-a-trait - not a trait key',
        'FAIL (a) {root}/traits/not-a-trait.md: nowhere.at-all - point is not in the extension-point registry',
    ],
    'unknown-type-file': [
        'FAIL (unknown) {root}/types/not-a-type.md: not-a-type - not a product type key',
        'FAIL (a) {root}/types/not-a-type.md: nowhere.at-all - point is not in the extension-point registry',
    ],
}

STATUS_EXACT = {
    'bom-workflows-line.md': [],
    'e-lone-trait.md': ['FAIL (e) {path}: - - part must name exactly one product type'],
    'e-no-type.md': ['FAIL (e) {path}: - - part must name exactly one product type'],
    'e-same-part.md': ['FAIL (e) {path}: app - two Workflows lines name the same part'],
    # A part named three times is one (e), and the repeated line is still checked (round 6: fixtures 3, programs).
    'e-same-part-three.md': ['FAIL (e) {path}: app - two Workflows lines name the same part'],
    'e-same-part-checked.md': [
        'FAIL (e) {path}: app - two Workflows lines name the same part',
        'FAIL (unknown) {path}: Glitter Development - name is not in the open list',
        'FAIL (e) {path}: - - part must name exactly one product type',
    ],
    'e-sub-type-of-another.md': ["FAIL (e) {path}: Claude Code Extension - sub-type is not of the line's product type"],
    'e-two-sub-types.md': ['FAIL (e) {path}: - - part must name at most one sub-type'],
    'e-two-types.md': ['FAIL (e) {path}: - - part must name exactly one product type'],
    'f-unwritten-sub-type.md': ['FAIL (f) {path}: Local Web App - sub-type is not written'],
    'f-unwritten-type.md': ['FAIL (f) {path}: Library Development - product type is not written'],
    'flag-repeated-unwritten.md': [
        'FLAG (trait) {path}: Spends money - trait not yet written; flagged, work continues (non-fatal)',
        'FAIL (form) {path}: Spends money - trait repeated',
    ],
    'flag-unwritten-trait.md': ['FLAG (trait) {path}: Spends money - trait not yet written; flagged, work continues (non-fatal)'],
    'form-bad-prefix-single.md': ['FAIL (form) {path}: bad;part - Workflows line breaks the part-prefix rule'],
    'form-empty-segment.md': [
        'FAIL (form) {path}: - - empty name in the Workflows head',
        'FAIL (form) {path}: - - Workflows head is not the product type, then at most its sub-type',
    ],
    'form-no-line.md': ['FAIL (form) {path}: - - status file has no Workflows line'],
    'form-no-traits-marker.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
    'form-part-arrow.md': ['FAIL (form) {path}: a\\u2192b - Workflows line breaks the part-prefix rule'],
    'form-part-blank.md': ['FAIL (form) {path}:   - Workflows line breaks the part-prefix rule'],
    'form-part-colon.md': ['FAIL (form) {path}: a:b - Workflows line breaks the part-prefix rule'],
    # Whitespace at the start of a part name, and a tab (stage B2 review, round 4: fixtures 3).
    'form-part-leading-space.md': ['FAIL (form) {path}:  plugin - Workflows line breaks the part-prefix rule'],
    'form-part-tab.md': ['FAIL (form) {path}: plugin\\x09 - Workflows line breaks the part-prefix rule'],
    'form-part-empty.md': ['FAIL (form) {path}: - - Workflows line breaks the part-prefix rule'],
    'form-part-semicolon.md': ['FAIL (form) {path}: a;b - Workflows line breaks the part-prefix rule'],
    'form-part-whitespace.md': ['FAIL (form) {path}: app  - Workflows line breaks the part-prefix rule'],
    'form-prefix-missing.md': ['FAIL (form) {path}: - - Workflows line breaks the part-prefix rule'],
    'form-prefix-on-single.md': ['FAIL (form) {path}: app - Workflows line breaks the part-prefix rule'],
    'form-sub-type-first.md': ['FAIL (form) {path}: - - Workflows head is not the product type, then at most its sub-type'],
    'form-trait-double-space.md': ['FAIL (form) {path}:  Installable - traits are not joined by a comma and one space'],
    'form-trait-in-head.md': ['FAIL (form) {path}: - - Workflows head is not the product type, then at most its sub-type'],
    # Order and repeats beyond neighbouring traits (stage B2 review, round 5: fixtures 3).
    'form-trait-order-three.md': [
        'FLAG (trait) {path}: Spends money - trait not yet written; flagged, work continues (non-fatal)',
        "FAIL (form) {path}: Has screens - traits are not in the open list's order",
        "FAIL (form) {path}: Installable - traits are not in the open list's order",
    ],
    'form-trait-repeat-separated.md': ['FAIL (form) {path}: Has screens - trait repeated'],
    # Order is judged against the highest trait so far, not only the one before (round 6: tests).
    'form-trait-order-highest.md': [
        'FLAG (trait) {path}: Spends money - trait not yet written; flagged, work continues (non-fatal)',
        "FAIL (form) {path}: Installable - traits are not in the open list's order",
    ],
    'form-trait-order.md': ["FAIL (form) {path}: Has screens - traits are not in the open list's order"],
    'form-trait-repeated.md': ['FAIL (form) {path}: Installable - trait repeated'],
    'form-trait-separator.md': ['FAIL (form) {path}: Has screens,Installable - traits are not joined by a comma and one space'],
    'form-trait-trailing-space.md': ['FAIL (form) {path}: Has screens  - traits are not joined by a comma and one space'],
    # The traits text's own edges: no space before the first name, `none` in its case (round 5: fixtures 4).
    'form-traits-double-space.md': ['FAIL (form) {path}:  none - traits are not joined by a comma and one space'],
    'form-traits-none-case.md': ['FAIL (unknown) {path}: None - not a trait name'],
    # An empty traits text, and one ending `, ` (round 6: tests).
    'form-traits-empty.md': ['FAIL (form) {path}: - - traits are not joined by a comma and one space'],
    'form-traits-trailing-comma.md': ['FAIL (form) {path}: - - traits are not joined by a comma and one space'],
    'form-traits-marker-twice.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
    # A rest that only starts as `not yet classified`, or differs in case or by a space, is read as names (stage B2
    # review, round 5: tests and fixtures 4, converged).
    'form-unclassified-case.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
    'form-unclassified-trailing-space.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
    'form-unclassified-with-traits.md': [
        'FAIL (unknown) {path}: not yet classified - name is not in the open list',
        'FAIL (e) {path}: - - part must name exactly one product type',
    ],
    'ok-multi.md': [],
    'ok-no-final-newline.md': [],
    'ok-multi-unclassified.md': [],
    'ok-single.md': [],
    'ok-unclassified.md': [],
    'unknown-name.md': [
        'FAIL (unknown) {path}: Toaster Development - name is not in the open list',
        'FAIL (e) {path}: - - part must name exactly one product type',
    ],
    'unknown-trait.md': ['FAIL (unknown) {path}: Glitter - not a trait name'],
    # A key where a Name belongs: the line is read by name only (stage B2 review, round 3: fixtures 4).
    'unknown-trait-key.md': ['FAIL (unknown) {path}: installable - not a trait name'],
    'unknown-sub-type-key.md': [
        'FAIL (unknown) {path}: claude-code-extension - name is not in the open list',
        'FAIL (form) {path}: - - Workflows head is not the product type, then at most its sub-type',
    ],
    # A product type's Name where its Workflow name belongs, and a sub-type's Name where its Sub-workflow name
    # belongs, the two differing only in case (round 5: fixtures 4; worded so in round 6: fixtures 5).
    'unknown-sub-type-name.md': [
        'FAIL (unknown) {path}: Claude Code extension - name is not in the open list',
        'FAIL (form) {path}: - - Workflows head is not the product type, then at most its sub-type',
    ],
    'unknown-type-name.md': [
        'FAIL (unknown) {path}: Web app - name is not in the open list',
        'FAIL (e) {path}: - - part must name exactly one product type',
    ],
    'unknown-type-key.md': [
        'FAIL (unknown) {path}: web-app - name is not in the open list',
        'FAIL (e) {path}: - - part must name exactly one product type',
    ],
    # A Workflow name in another case (round 6: fixtures 5).
    'unknown-workflow-name-case.md': [
        'FAIL (unknown) {path}: web app development - name is not in the open list',
        'FAIL (e) {path}: - - part must name exactly one product type',
    ],
}


def whole_output(expected):
    """A case's whole standard output: its finding lines, then the RESULT line, which counts the FAIL lines only."""
    count = sum(1 for line in expected if line.startswith("FAIL ("))
    return expected + ["RESULT: OK" if count == 0 else f"RESULT: {count} problem(s)"]


def test_r014_every_case_has_its_exact_findings():
    """Every fixture under fail/ and status/ has an entry, so a new case states its whole output."""
    assert sorted(FILE_EXACT) == sorted(p.name for p in (REPO / FIX / "fail").iterdir())
    assert sorted(STATUS_EXACT) == sorted(p.name for p in (REPO / FIX / "status").iterdir() if p.name != "open-list.md")


@pytest.mark.parametrize("case", sorted(FILE_EXACT))
def test_r014_file_case_gives_exactly_its_findings(case):
    """R-014: each failing root reports its case and nothing else (stage B2 review, round 2: fixtures parts 1-3); the
    whole standard output is compared, RESULT line included, and standard error is empty (round 3: Review B)."""
    root = f"{FIX}/fail/{case}"
    rc, lines, err = run(root)
    assert_clean_end(lines, err)
    expected = [line.replace("{root}", root) for line in FILE_EXACT[case]]
    assert lines == whole_output(expected), lines
    assert err == "", err
    assert rc == (1 if expected else 0), lines


@pytest.mark.parametrize("name", sorted(STATUS_EXACT))
def test_r014_status_case_gives_exactly_its_findings(name):
    """R-014, R-015: each status file reports its case and nothing else; the part-name rules (non-empty, no `;`, `→` or
    `:`) are tested in a file of several lines, where they are reached (stage B2 review, round 2: Review B, fixtures 3);
    the whole standard output is compared, RESULT line included, and standard error is empty (round 3: Review B)."""
    path = f"{FIX}/status/{name}"
    rc, lines, err = status(name)
    assert_clean_end(lines, err)
    expected = [line.replace("{path}", path) for line in STATUS_EXACT[name]]
    assert lines == whole_output(expected), lines
    assert err == "", err
    assert rc == (1 if any(line.startswith("FAIL (") for line in expected) else 0), lines


def test_r014_sub_workflow_changes_are_checked():
    """R-014 across the three layers: a valid sub-workflow's changes are checked like a type workflow's: an unknown
    point (a), a set where the point accepts add only (set), a replace of a module that is not replaceable (c). Runs the
    program; the type workflow beside it is valid, so every finding is the sub-workflow's (BUG-003 review: Review A and
    Review B both found the first version read only the table)."""
    root = f"{FIX}/fail/sub-workflow-changes"
    sub = f"{root}/types/host-extension/claude-code-extension.md"
    rc, lines, err = run(root)
    assert_clean_end(lines, err)
    assert rc == 1, lines
    assert fails(lines) == [
        f"FAIL (a) {sub}: intake.question - point is not in the extension-point registry",
        f"FAIL (set) {sub}: intake.questions - point does not accept set",
        f"FAIL (c) {sub}: design - module is missing or not replaceable",
    ], lines


@pytest.mark.parametrize("encoding", ["utf-8", "cp1252"])
def test_r014_output_is_ascii_on_every_console(tmp_path, encoding):
    """The finding lines are ASCII whatever the console's encoding: a non-ASCII character in a printed field reaches the
    output as its escape (\\xe9), as a control character already does (stage B2 review, round 2: Review B; inventory-check
    and conformance-check already print ASCII)."""
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "types" / "host-extension.md").write_text("## Add at intake.t\u00e9st\n\nq\n", encoding="utf-8")
    st = tmp_path / "status.md"
    st.write_text("Phase: building\nWorkflows: T\u00e9st Development; traits: Gl\u2192it\U0001f600ter\n", encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING=encoding)
    p = subprocess.run([sys.executable, PROG, "--status", str(st), str(root)], cwd=str(REPO), capture_output=True, env=env)
    assert p.returncode == 1, p.stdout
    assert all(byte < 128 for byte in p.stdout), p.stdout
    assert b"intake.t\\xe9st - point is not in the extension-point registry" in p.stdout, p.stdout
    assert b": T\\xe9st Development - name is not in the open list" in p.stdout, p.stdout
    # A character up to U+FFFF and one above it, in a trait name (the security auditor's advisory, BUG-003).
    assert b": Gl\\u2192it\\U0001f600ter - not a trait name" in p.stdout, p.stdout


def test_r014_layer_path_that_is_a_file_is_form(tmp_path):
    """A `types` or `traits` path that exists and is not a folder is reported, as a link there is, never skipped as a
    missing layer (stage B2 review, round 2: Review B)."""
    root = tmp_path / "root"
    root.mkdir()
    (root / "types").write_text("not a folder\n", encoding="utf-8")
    (root / "traits").write_text("not a folder\n", encoding="utf-8")
    rc, lines, err = run(str(root))
    assert_clean_end(lines, err)
    shown = str(root).replace("\\", "/")
    assert fails(lines) == [
        f"FAIL (form) {shown}/traits: traits - path is not a conditional-workflow file",
        f"FAIL (form) {shown}/types: types - path is not a conditional-workflow file",
    ], lines
    assert rc == 1


def test_r014_unwritten_type_fails_against_the_real_open_list(tmp_path):
    """The pause (§6.7) against the bridge's own open list: a copy with every entry marked unwritten, so the test still
    holds once release B writes its first workflows (TASK-017 to TASK-021; stage B2 review)."""
    real = (REPO / "bridge" / "cursor-bridge" / "workflow" / "open-list.md").read_text(encoding="utf-8")
    copy = tmp_path / "open-list.md"
    copy.write_text(real.replace("| yes |", "| no |"), encoding="utf-8", newline="\n")
    assert "| yes |" not in copy.read_text(encoding="utf-8")
    rc, lines, err = run("--open-list", str(copy), "--status", f"{FIX}/status/ok-single.md")
    assert_clean_end(lines, err)
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


def test_r014_set_changes_cell_is_split_on_commas_and_stripped(tmp_path):
    """handoff/TASK-006.md, the `set` finding: a point's Changes cell is split on commas and each part stripped, so a
    cell reading `set , add` accepts a Set as `add, set` does, and `add` alone refuses it (BUG-006 r2: Review A, the
    sweep's line 285)."""
    reg = (REPO / "bridge/cursor-bridge/workflow/extension-points.md").read_text(encoding="utf-8")
    row = "| intake.target-environment | Intake | The product type's target environment | intake | add, set | part |"
    assert reg.count(row) == 1, "the row of the point the pass root sets"
    text = (REPO / FIX / "pass/types/host-extension.md").read_text(encoding="utf-8")
    assert "\n## Set at intake.target-environment\n" in "\n" + text, "precondition: the pass root sets the point"
    spaced = tmp_path / "spaced.md"
    spaced.write_text(reg.replace(row, row.replace("| add, set |", "| set , add |")), encoding="utf-8", newline="\n")
    rc, lines, err = run("--registry", str(spaced), f"{FIX}/pass")
    assert (rc, lines, err) == (0, ["RESULT: OK"], ""), (rc, lines, err)
    add_only = tmp_path / "add-only.md"
    add_only.write_text(reg.replace(row, row.replace("| add, set |", "| add |")), encoding="utf-8", newline="\n")
    rc, lines, err = run("--registry", str(add_only), f"{FIX}/pass")
    assert rc == 1, lines
    assert lines == whole_output(
        [f"FAIL (set) {FIX}/pass/types/host-extension.md: intake.target-environment - point does not accept set"]), lines
    assert err == "", err


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
    """R2-1: `## Adds at`, `## add at`, `## Replacing`, `## Append at`, each change word without `at` (`## Adds`, `## Added`,
    `## Sets`, `## Replaces`, `## Replaced`), a two-word `## Look at` and `## Look AT ...` are each a malformed change
    heading (stage B2 review, round 5)."""
    root = f"{FIX}/fail/form-misspelt-change-word"
    rc, lines, err = run(root)
    assert rc == 1
    forms = [line for line in fails(lines) if line.startswith(f"FAIL (form) {root}/types/host-extension.md: - ")]
    assert len(forms) == 11, lines


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
    """R2-4: a linked folder under types/ is form and is never read; a link to a parent cannot loop. Each link is
    reported under its own path and name, a link inside a folder that is no product type too, beside the folder's (d)
    (BUG-006 r2: Review A, the sweep's lines 349 and 354)."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "claude-code-extension.md").write_text("## Add at nowhere.at-all\n\nq\n", encoding="utf-8")
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "types" / "host-extension.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    _link_folder(root / "types" / "host-extension", outside)
    _link_folder(root / "types" / "loop", root)
    (root / "types" / "not-a-type").mkdir()
    _link_folder(root / "types" / "not-a-type" / "inner-link", outside)
    p = subprocess.run([sys.executable, PROG, str(root)], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", timeout=60)
    lines = p.stdout.splitlines()
    assert p.returncode == 1, lines
    assert not [line for line in lines if line.startswith("FAIL (a)")], "a file behind a link was read"
    shown = str(root).replace("\\", "/")
    assert lines == whole_output([
        f"FAIL (form) {shown}/types/host-extension: host-extension - path is not a conditional-workflow file",
        f"FAIL (form) {shown}/types/loop: loop - path is not a conditional-workflow file",
        f"FAIL (d) {shown}/types/not-a-type: not-a-type - type folder is not a product type",
        f"FAIL (form) {shown}/types/not-a-type/inner-link: inner-link - path is not a conditional-workflow file",
    ]), lines


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
    """R3-4: `## Set:`, `## Add:`, `## Replace:`, `## Adding`, `## Setting`, and each other stripped mark (`## Adds.`,
    `## Set;`, `## Replace,`, `## Add-`) and two marks (`## Set:;`) are malformed change headings; a trait's `## Set:` no
    longer escapes (stage B2 review, round 5)."""
    root = f"{FIX}/fail/form-change-word-punctuation"
    rc, lines, err = run(root)
    assert rc == 1
    forms = [line for line in fails(lines) if line.startswith(f"FAIL (form) {root}/traits/installable.md: - ")]
    assert len(forms) == 10 and len(fails(lines)) == 10, lines
    text = (REPO / FIX / "pass/types/host-extension.md").read_text(encoding="utf-8")
    assert "\n## Add-ons\n" in text, "the pass root keeps `## Add-ons` as prose"


def test_r014_indented_or_tabbed_change_heading_is_form():
    """R3-6: ` ## Set at x`, `##<tab>Add at x` and `   ## Add at x` (three spaces, the most a heading may be indented:
    stage B2 review, round 6, fixtures 1 and 2) are heading candidates that fail the exact forms."""
    root = f"{FIX}/fail/form-indented-heading"
    text = (REPO / root / "types/host-extension.md").read_text(encoding="utf-8")
    assert "\n##" + chr(9) + "Add at intake.questions\n" in text, "precondition: the tab survives"
    assert "\n   ## Add at intake.questions\n" in text, "precondition: the three spaces survive"
    rc, lines, err = run(root)
    assert rc == 1
    assert len([line for line in fails(lines) if line.startswith(f"FAIL (form) {root}/types/host-extension.md: ")]) == 3, lines


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
    # The path and the system's reason, not the fallback text (BUG-006 r2: Review A, the sweep's line 312).
    assert f"ERROR: {shown}/{layer}: Permission denied" in [line.replace("\\", "/") for line in lines], lines


def test_r014_unknown_type_folder_is_reported_without_its_files():
    """R-014: a folder under types/ that is no product type is the (d) finding alone; its file holds a change the check
    would refuse with (a), so the exact output shows the folder's files are not read (stage B2 review, round 4: fixtures
    1; the precondition by Review A, BUG-005)."""
    text = (REPO / FIX / "fail/d-unknown-type-folder/types/not-a-type/thing.md").read_text(encoding="utf-8")
    assert "\n## Add at nowhere.at-all\n" in "\n" + text, "precondition: the folder's file holds a change to an unknown point"
    rc, lines, err = run(f"{FIX}/fail/d-unknown-type-folder")
    assert lines == whole_output([f"FAIL (d) {FIX}/fail/d-unknown-type-folder/types/not-a-type: not-a-type - type folder is not a product type"]), lines
    assert err == "" and rc == 1, (lines, err)


def test_r014_tilde_fences_and_longer_runs_hide_headings():
    """R5-3: in the pass root's trait file a tilde fence hides a trait's `## Set` (b), and a four-tilde fence holds a
    four-backtick line (the other character, long enough), after which `## Replace interface` (b) stands, and a shorter
    tilde line, after which `## Replace design` (b) stands, both still hidden until the fence's own four-tilde close
    (one heading after each line since stage B2's review, round 4: fixtures 2)."""
    text = (REPO / FIX / "pass/traits/installable.md").read_text(encoding="utf-8")
    assert "\n~~~\n## Set at intake.delivery-kind\n~~~\n" in text, "precondition: a tilde fence hides a Set"
    assert "\n~~~~\n````\n## Replace interface\n~~~\n## Replace design\n~~~~" in text, (
        "precondition: a longer tilde fence hides a Replace after a backtick line and another after a shorter tilde line")
    assert "\n~~~a`b\n## Set at intake.delivery-kind\n~~~" in text, "precondition: a backtick in a tilde info string still opens"
    rc, lines, err = run(f"{FIX}/pass")
    assert rc == 0 and lines[-1] == "RESULT: OK", lines


@pytest.mark.parametrize("case", ["fence-longer-opening", "fence-info-string-not-closing", "fence-backtick-in-info", "fence-close-trailing-space"])
def test_r014_commonmark_fence_cases_read_the_set(case):
    """R5-3: a shorter run does not close a longer fence and a longer run does; a backtick line with text after it does
    not close; a backtick line whose info string holds a backtick does not open, while one with an ordinary info string
    does (its pair hides `## Replace design`); a closing run followed only by spaces or tabs closes. In each the trait's
    `## Set` is read and is the one (b), with no open fence left (the controls since stage B2's review, round 4:
    fixtures 1)."""
    root = f"{FIX}/fail/{case}"
    text = (REPO / root / "traits/installable.md").read_text(encoding="utf-8")
    if case == "fence-close-trailing-space":
        assert "\n```  \t\n" in text, "precondition: the closing run keeps its trailing spaces and tab"
    if case == "fence-backtick-in-info":
        assert "\n```md\n## Replace design\n```\n" in text, "precondition: an ordinary info string opens a fence"
    if case == "fence-longer-opening":
        assert "\n````\n```\n`````\n" in text, "precondition: a shorter run inside, a longer run closes"
    rc, lines, err = run(root)
    assert_clean_end(lines, err)
    assert rc == 1
    assert fails(lines) == [f"FAIL (b) {root}/traits/installable.md: intake.delivery-kind - a trait file may only add"], lines


def test_r014_whitespace_only_set_section_is_empty():
    """TASK-006: a `## Set at` section with no non-blank line is (form); a line of spaces and a tab is blank, so the
    case's Set section holds one, kept by this precondition (stage B2 review, round 3: fixtures 1)."""
    root = f"{FIX}/fail/form-empty-set"
    text = (REPO / root / "types/host-extension.md").read_text(encoding="utf-8")
    assert "## Set at intake.target-environment\n\n  \t\n\n## Add at" in text, "precondition: the Set section holds only a whitespace line"
    assert findings_of(root) == [f"FAIL (form) {root}/types/host-extension.md: intake.target-environment - Set at section has no non-blank line"]


def test_r014_indented_fence_pair_hides_a_heading():
    """R4-3: the pass root holds a fence pair indented by two and three spaces around a heading that, read, is (c)."""
    text = (REPO / FIX / "pass/types/host-extension.md").read_text(encoding="utf-8")
    assert "\n  ```\n## Replace design\n   ```" in text, "the precondition: an indented fence pair hides `## Replace design`"
    rc, lines, err = run(f"{FIX}/pass")
    assert rc == 0 and lines[-1] == "RESULT: OK", lines


def test_r014_indented_closing_fence_closes_the_block():
    """R4-3: a column-0 fence closed by one indented three spaces; the trait's `## Set` after it is read and is (b)."""
    root = f"{FIX}/fail/fence-indented-close"
    text = (REPO / root / "traits/installable.md").read_text(encoding="utf-8")
    assert "\n   ```\n" in text, "precondition: the closing fence is indented three spaces"
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
    """R4-3 with R3-6: an opening fence indented three spaces, the most a fence may be (stage B2 review, round 6:
    fixtures 1 and 2), never closed, hides the heading after it and is one (form)."""
    root = f"{FIX}/fail/form-indented-fence-open"
    text = (REPO / root / "types/host-extension.md").read_text(encoding="utf-8")
    assert "\n   ```\n" in text, "precondition: the opening fence is indented three spaces"
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


# --- stage B2 review, round 5: the controls the reviewers and the supervisor's mutation sweep found missing -----------

ROUND5_PRECONDITIONS = [
    # (fixture, text it holds, the rule the text gives a control to)
    ("fail/kind-bare-hashes/types/host-extension.md", "## Set at intake.delivery-kind\n##\ninstaller\n",
     "a line of `##` alone right under a Set heading is no heading (BUG-006 r4)"),
    ("fail/fence-indented-close/traits/installable.md", "\n```\ncode\n    ```\n   ```\n",
     "a closing run indented four spaces is content; the three-space one closes"),
    ("fail/fence-four-spaces/traits/installable.md", "\n    ```\n", "backticks indented four spaces open no fence"),
    ("fail/fence-four-spaces/traits/installable.md", "\n``\n", "two backticks open no fence"),
    ("fail/fence-four-spaces/traits/installable.md", "\n~~\n", "two tildes open no fence"),
    ("pass/types/host-extension.md", "\n\n    ## Replace design\n", "a heading indented four spaces is prose"),
    ("pass/types/host-extension.md", "\n## \n", "an empty heading is prose"),
    ("pass/types/host-extension/claude-code-extension.md",
     "\n## Set at intake.delivery-kind\n  installer  \nThe part's installer delivers it.\n",
     "the Set value is the first non-blank line, stripped, with no blank line before it and prose after it"),
    ("fail/c-not-replaceable/types/host-extension.md", "## Replace interface\n", "two different modules replaced in one file"),
    ("fail/d-unknown-type-folder/types/not-a-type/deeper/more.md", "## Add at nowhere.at-all\n",
     "a folder inside an unknown type folder is not reported again"),
    ("status/form-no-line.md", "\n  Workflows: ", "an indented Workflows line is not one"),
    ("status/form-no-line.md", "\nworkflows: ", "a lower-case workflows line is not one"),
]


@pytest.mark.parametrize("rel, held, rule", ROUND5_PRECONDITIONS,
                         ids=[f"{r}: {h.strip()[:24]}" for r, h, _ in ROUND5_PRECONDITIONS])
def test_r014_round5_fixtures_hold_their_controls(rel, held, rule):
    """Each fixture holds the text that makes its case a control (stage B2 review, round 5); the cases' outputs are in
    FILE_EXACT and STATUS_EXACT, and the pass root must stay RESULT: OK."""
    text = (REPO / FIX / rel).read_text(encoding="utf-8")
    assert held in text, rule


def test_r015_byte_cases_keep_their_bytes():
    """A trailing space after `not yet classified`, and a status file that starts with a blank line and has no final line
    feed, are bytes an editor could change; the cases depend on them (stage B2 review, round 5)."""
    trailing = (REPO / FIX / "status/form-unclassified-trailing-space.md").read_bytes().rstrip(b"\r\n")
    assert trailing.endswith(b"not yet classified "), trailing
    no_final = (REPO / FIX / "status/ok-no-final-newline.md").read_bytes()
    assert no_final.startswith((b"\n", b"\r\n")) and not no_final.endswith(b"\n"), no_final


@pytest.mark.parametrize("char, shown", [
    ("\t", "\\x09"), ("\x7f", "\\x7f"), ("\x80", "\\x80"), ("\xff", "\\xff"), ("Ā", "\\u0100"),
    ("→", "\\u2192"), ("￿", "\\uffff"), ("\U00010000", "\\U00010000"),
], ids=["tab", "del", "x80", "xff", "u0100", "arrow", "uffff", "U00010000"])
def test_r014_escape_field_at_each_width_boundary(program, char, shown):
    """R-014 output is ASCII: an unprintable or non-ASCII character prints as backslashreplace's forms, `\\xNN` up to
    U+00FF, `\\uNNNN` up to U+FFFF, `\\UNNNNNNNN` above, each width at its boundary (stage B2 review, round 5: the
    supervisor's mutation sweep)."""
    assert program("workflow-check").escape_field("a" + char + "b") == "a" + shown + "b"


TABLE_REQ = ["Key", "Name"]


@pytest.mark.parametrize("text, rows", [
    # the first table after the heading, rows to the first non-table line
    ("## T\n\n| Key | Name |\n|---|---|\n| a | A |\n\nprose\n", [("a", "A")]),
    # a table right under its heading, no blank line between
    ("## T\n| Key | Name |\n|---|---|\n| a | A |\n", [("a", "A")]),
    # alignment colons on either side of the separator's dashes
    ("## T\n\n| Key | Name |\n|:---|---:|\n| a | A |\n", [("a", "A")]),
    # rows without their trailing pipe, and spaces after the last pipe
    ("## T\n\n| Key | Name\n|---|---\n| a | A |   \n| b | B\n", [("a", "A"), ("b", "B")]),
    # a table with a header and a separator and no row is an empty table
    ("## T\n\n| Key | Name |\n|---|---|\n", []),
    # the heading given twice: the first one's table
    ("## T\n\n| Key | Name |\n|---|---|\n| a | A |\n\n## T\n\n| Key | Name |\n|---|---|\n| z | Z |\n", [("a", "A")]),
    # a prose line ending in a pipe is not the table's start
    ("## T\n\nsee below |\n\n| Key | Name |\n|---|---|\n| a | A |\n", [("a", "A")]),
    # a line starting `##` with no space after it (a tab, or nothing) does not end the section the table is looked
    # for in; only a line starting `## ` does (BUG-006 r3: Review B)
    ("## T\n\nprose\n\n##\tU\n##\n\n| Key | Name |\n|---|---|\n| a | A |\n", [("a", "A")]),
], ids=["blank-line", "no-blank-line", "alignment", "no-trailing-pipe", "no-rows", "heading-twice", "prose-pipe",
        "hashes-without-space"])
def test_r014_table_reader_reads_the_first_table_after_its_heading(program, text, rows):
    """The two rule files' tables are read as `How this file is read` says (open-list.md, extension-points.md): the first
    table after the exact heading, its rows to the first line that is not a table line, columns found by header name
    (stage B2 review, round 5: the supervisor's mutation sweep)."""
    found, error = program("workflow-check").parse_table(text, "t.md", "## T", TABLE_REQ)
    assert error is None, error
    assert [(row["Key"], row["Name"]) for row in found] == rows


def test_r014_table_reader_stops_at_the_next_section(program):
    """A heading with no table before the next line starting `## ` is an error, not that section's table, as both rule
    files' "How this file is read" says (stage B2 review, round 5: the supervisor's mutation sweep; BUG-006 r3)."""
    found, error = program("workflow-check").parse_table(
        "## T\n\nprose\n\n## U\n\n| Key | Name |\n|---|---|\n| a | A |\n", "t.md", "## T", TABLE_REQ)
    assert found is None and error == "no table after ## T", error


# --- BUG-006 r2: Review A of BUG-006, the sweep's survivors an input separates --------------------------------------

def test_r014_unreadable_file_names_the_systems_reason(tmp_path, monkeypatch, program):
    """handoff/TASK-006.md: `<reason>` is free plain-language text; a file the system refuses to read gives `cannot be
    read (<the system's reason>)`, never the exception's own text (BUG-006 r2: Review A, the sweep's line 126)."""
    mod = program("workflow-check")
    path = tmp_path / "refused.md"
    path.write_text("q\n", encoding="utf-8")

    def refuse(*a, **k):
        raise PermissionError(13, "Permission denied", str(path))

    monkeypatch.setattr(mod, "open", refuse, raising=False)
    text, _shown, reason = mod.read_utf8(str(path))
    assert (text, reason) == (None, "cannot be read (Permission denied)"), reason


def test_r014_folder_that_cannot_be_listed_is_named_with_its_reason(tmp_path, monkeypatch, capsys, program):
    """R2-3 and handoff/TASK-006.md's `<reason>`: a folder under a layer that cannot be listed stops the check with an
    ERROR line naming that folder, not the root, and the system's reason; on every host, where
    test_r014_unreadable_folder_stops_the_check needs POSIX mode bits (BUG-006 r2: Review A, the sweep's lines 299
    and 300)."""
    mod = program("workflow-check")
    root = tmp_path / "root"
    sub = root / "types" / "host-extension"
    sub.mkdir(parents=True)
    (root / "types" / "host-extension.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    real = os.scandir

    def scandir(path=".", *a, **k):
        if os.path.basename(os.fspath(path)) == "host-extension":
            raise PermissionError(13, "Permission denied", os.fspath(path))
        return real(path, *a, **k)

    monkeypatch.setattr(os, "scandir", scandir)
    code, lines = _main_in_process(mod, str(root), capsys=capsys)
    assert code == 2, lines
    assert lines[-1] == "RESULT: not checked", lines
    shown = str(sub).replace("\\", "/")
    assert f"ERROR: {shown}: Permission denied" in [line.replace("\\", "/") for line in lines], lines


# --- stage B2 review, round 6 (BUG-007): the sixth review's controls and the widened sweep's survivors ---------------

ROUND6_PRECONDITIONS = [
    # (fixture, text it holds, the rule the text gives a control to)
    ("fail/form-indented-heading/types/host-extension.md", "\n   ## Add at intake.questions\n",
     "a change heading indented three spaces is a heading candidate (fixtures 1 and 2)"),
    ("fail/form-indented-fence-open/types/host-extension.md", "\n   ```\n",
     "an opening fence indented three spaces opens a fence (fixtures 1 and 2)"),
    ("fail/form-heading-trailing-text/types/host-extension.md", "\n## Set at intake.budget-kind \n",
     "a space after the key is not one of the four forms (tests)"),
    ("fail/form-heading-trailing-text/types/host-extension.md", "\n## Add at project-end.delivery for installer extra\n",
     "text after the delivery kind is not one of the four forms (tests: ADD_FOR's kind read as `.+`)"),
    ("fail/form-empty-set-before-prose/types/host-extension.md", "## Set at intake.target-environment\n\n## Notes\n",
     "a section ends at a prose heading (tests and fixtures 2)"),
    ("fail/form-empty-set-before-prose/types/host-extension.md", "\n## Set at intake.delivery-kind\n\n## About\n",
     "a section ends at a prose heading at the delivery-kind point too"),
    ("fail/kind-set-value/types/host-extension/browser-extension.md", "\n\n`installer\n",
     "a backtick on the leading side only is not unwrapped (fixtures 2)"),
    ("fail/form-traits-folder/traits/odd.md/extra.md", "## Add at intake.questions\n",
     "a folder named like a trait file is a folder (the sweep's line 364)"),
    ("pass/traits/installable.md", "\n## Add at intake.delivery-kind\n", "an addition at a value point is an addition (tests)"),
    ("pass/types/host-extension.md", "\n## - notes\n", "a heading whose first word is punctuation only is prose (tests)"),
    ("pass/types/host-extension.md", "\n## ...\n", "a heading of punctuation alone is prose (tests)"),
    # The rows of the status fixtures' open list the status cases read (fixtures 5).
    ("status/open-list.md", "\n| web-app | Web app |", "a product type's Name differs from its Workflow name"),
    ("status/open-list.md", "\n| claude-code-extension | Claude Code extension |",
     "a sub-type's Name differs from its Sub-workflow name in case only"),
    ("status/open-list.md", "\n| installable | Installable |", "a trait is named by its Name"),
]


@pytest.mark.parametrize("rel, held, rule", ROUND6_PRECONDITIONS,
                         ids=[f"{r}: {h.strip()[:24]}" for r, h, _ in ROUND6_PRECONDITIONS])
def test_r014_round6_fixtures_hold_their_controls(rel, held, rule):
    """Each fixture holds the text that makes its case a control (stage B2 review, round 6); the cases' outputs are in
    FILE_EXACT and STATUS_EXACT, and the pass root must stay RESULT: OK."""
    text = (REPO / FIX / rel).read_text(encoding="utf-8")
    assert held in text, rule


def test_r015_round6_byte_cases_keep_their_bytes():
    """A traits text that ends in a space is a byte an editor could trim; the two cases depend on it (round 6: tests)."""
    for name, end in (("form-traits-empty.md", b"; traits: "), ("form-traits-trailing-comma.md", b"; traits: Has screens, ")):
        data = (REPO / FIX / "status" / name).read_bytes().rstrip(b"\r\n")
        assert data.endswith(end), (name, data)


def test_r014_four_backtick_fence_and_shorter_tilde_run(program):
    """A fence opened by four backticks hides the heading inside it, and a shorter tilde run inside a fence of four
    tildes is content (stage B2 review, round 6: the sweep's line 82, `{3,}` read as `{3}`)."""
    spans = program("workflow-check").heading_spans
    assert spans("````\n## Set at intake.delivery-kind\n````\n") == ([], False)
    assert spans("~~~~\n~~~\n## Set at intake.delivery-kind\n~~~~\n") == ([], False)


def test_r014_form_feed_after_a_closing_run_does_not_close(program):
    """A closing run is followed only by spaces or tabs: a form feed after it leaves the fence open, as Markdown does
    (stage B2 review, round 6: the sweep's line 83, `[ \\t]*` read as `\\s*`; round 5's lead, now a test)."""
    text = "```\n## Set at intake.delivery-kind\n```" + chr(12) + "\n"
    assert program("workflow-check").heading_spans(text) == ([], True)


def test_r014_single_dash_separator_cells(program):
    """A separator cell is at least one dash, with an optional colon at either end: `-` and `:-:` are separator cells
    (stage B2 review, round 6: the sweep's lines 171 and 173)."""
    found, error = program("workflow-check").parse_table("## T\n\n| Key | Name |\n|-|:-:|\n| a | A |\n", "t.md", "## T", TABLE_REQ)
    assert error is None, error
    assert [(row["Key"], row["Name"]) for row in found] == [("a", "A")]


def test_r014_table_with_only_its_header_has_no_separator(program):
    """A header line with no table line after it is a table without its separator row: an error, no traceback (stage
    B2 review, round 6: tests; the sweep's line 222)."""
    found, error = program("workflow-check").parse_table("## T\n\n| Key | Name |\n\nprose\n", "t.md", "## T", TABLE_REQ)
    assert found is None and error == "table after ## T has no separator row", error


def test_r014_registry_missing(tmp_path):
    """The registry, like the open list, is an input the check cannot run without (stage B2 review, round 6: tests;
    the sweep's lines 116, 117 and 782)."""
    absent = tmp_path / "absent.md"
    rc, lines, err = run("--registry", str(absent), f"{FIX}/pass")
    assert_not_checked(rc, lines, err)
    assert lines == [f"ERROR: {str(absent).replace(chr(92), '/')}: does not exist", "RESULT: not checked"], lines


def test_r014_rule_file_that_is_a_folder_cannot_be_read(tmp_path):
    """A path that exists and is not a file cannot be read; it is never reported as missing (stage B2 review, round 6:
    the sweep's lines 116 and 117)."""
    rc, lines, err = run("--registry", str(tmp_path), f"{FIX}/pass")
    assert_not_checked(rc, lines, err)
    assert lines == [f"ERROR: {str(tmp_path).replace(chr(92), '/')}: cannot be read", "RESULT: not checked"], lines


def test_r014_conditional_file_not_utf8_stops_the_check(tmp_path):
    """A conditional-workflow file that cannot be read as UTF-8 stops the check with an ERROR line naming it and no
    traceback; the same file in UTF-8 passes (stage B2 review, round 6: programs and tests; the sweep's line 806)."""
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    path = root / "types" / "host-extension.md"
    path.write_bytes(b"## Add at intake.questions\n\nq\n")
    assert run(str(root)) == (0, ["RESULT: OK"], "")
    path.write_bytes(b"## Add at intake.questions\n\n\xff\n")
    rc, lines, err = run(str(root))
    assert_not_checked(rc, lines, err)
    shown = str(root).replace("\\", "/")
    assert lines == [f"ERROR: {shown}/types/host-extension.md: cannot be read as UTF-8", "RESULT: not checked"], lines


def test_r014_path_fields_are_escaped(tmp_path):
    """A root, a status file and a missing root holding a non-ASCII character print it as its escape, in FAIL and ERROR
    lines alike, on a console that could print it (stage B2 review, round 6: tests)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    root = tmp_path / "rooté"
    (root / "traits").mkdir(parents=True)
    (root / "traits" / "not-a-trait.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    st = tmp_path / "statusé.md"
    st.write_text("Phase: building\n", encoding="utf-8")

    def shown(path):
        return str(path).replace("\\", "/").replace("é", "\\xe9").encode("ascii")

    p = subprocess.run([sys.executable, PROG, "--status", str(st), str(root)], cwd=str(REPO), capture_output=True, env=env)
    assert p.returncode == 1, p.stdout
    assert p.stdout.splitlines() == [
        b"FAIL (unknown) " + shown(root) + b"/traits/not-a-trait.md: not-a-trait - not a trait key",
        b"FAIL (form) " + shown(st) + b": - - status file has no Workflows line",
        b"RESULT: 2 problem(s)",
    ], p.stdout
    absent = tmp_path / "absenté"
    p = subprocess.run([sys.executable, PROG, str(absent)], cwd=str(REPO), capture_output=True, env=env)
    assert p.returncode == 2, p.stdout
    assert p.stdout.splitlines() == [b"ERROR: " + shown(absent) + b": not a folder", b"RESULT: not checked"], p.stdout


def test_r014_default_root_is_read_when_no_root_is_given(tmp_path):
    """With no ROOT and no --status the root is the workflow folder beside the program: a copy of the program whose
    workflow folder holds a failing file reports that file. test_r014_default_root_is_the_programs_workflow_folder
    passes whether that root is read or not (stage B2 review, round 6: tests; the sweep's line 786)."""
    folder = tmp_path / "bin"
    folder.mkdir()
    shutil.copyfile(REPO / PROG, folder / "workflow-check.py")
    shutil.copytree(REPO / "bridge" / "cursor-bridge" / "workflow", folder / "workflow")
    (folder / "workflow" / "types").mkdir(exist_ok=True)
    (folder / "workflow" / "types" / "not-a-type.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    p = subprocess.run([sys.executable, str(folder / "workflow-check.py")], cwd=str(tmp_path), capture_output=True,
                       text=True, encoding="utf-8", env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    shown = str(folder / "workflow").replace("\\", "/")
    assert p.stdout.splitlines() == [
        f"FAIL (unknown) {shown}/types/not-a-type.md: not-a-type - not a product type key",
        "RESULT: 1 problem(s)",
    ], p.stdout
    assert p.returncode == 1
    # With --status and no ROOT only the status file is checked (the sweep's line 785, `and not statuses` dropped).
    st = tmp_path / "status.md"
    st.write_text("Phase: building\nWorkflows: not yet classified\n", encoding="utf-8")
    p = subprocess.run([sys.executable, str(folder / "workflow-check.py"), "--status", str(st)], cwd=str(tmp_path),
                       capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert (p.returncode, p.stdout.splitlines()) == (0, ["RESULT: OK"]), p.stdout


def test_r014_root_with_a_trailing_slash_prints_one_slash():
    """A root given with a trailing slash prints one slash between the root and each path under it (stage B2 review,
    round 6: tests)."""
    root = f"{FIX}/fail/form-traits-folder"
    rc, lines, err = run(root + "/")
    assert lines == whole_output([line.replace("{root}", root) for line in FILE_EXACT["form-traits-folder"]]), lines
    assert rc == 1


def test_r014_link_among_a_folders_files_is_form(tmp_path):
    """A link the walk lists among a folder's files (one whose target is gone), a link named like a trait file, and a
    `types` path that is a link to a folder are each reported at their exact line and never read or walked (stage B2
    review, round 6: the sweep's lines 335, 336 and 353)."""
    outside = _outside_with_canary(tmp_path)
    gone = tmp_path / "gone"
    gone.mkdir()
    root = tmp_path / "root"
    (root / "traits").mkdir(parents=True)
    (root / "traits" / "installable.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    _link_folder(root / "traits" / "gone", gone)
    gone.rmdir()
    _link_folder(root / "traits" / "has-screens.md", outside)
    _link_folder(root / "types", outside)
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/")
    assert lines == whole_output([
        f"FAIL (form) {shown}/traits/gone: gone - path is not a conditional-workflow file",
        f"FAIL (form) {shown}/traits/has-screens.md: has-screens.md - path is not a conditional-workflow file",
        f"FAIL (form) {shown}/types: types - path is not a conditional-workflow file",
    ]), lines
    assert rc == 1


def test_r014_part_name_ends_at_the_first_colon_space(tmp_path):
    """A part's name ends at the first `: ` of the line's head, so a second one belongs to the head (stage B2 review,
    round 6: tests, consider; the sweep's line 595, find read as rfind)."""
    st = tmp_path / "status.md"
    st.write_text("Workflows: app: x: Web App Development; traits: none\nWorkflows: site: Web App Development; traits: none\n",
                  encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", STATUS_LIST, "--status", str(st))
    shown = str(st).replace("\\", "/")
    assert lines == whole_output([
        f"FAIL (unknown) {shown}: x: Web App Development - name is not in the open list",
        f"FAIL (e) {shown}: - - part must name exactly one product type",
    ]), lines
    assert rc == 1


def test_r014_part_with_nothing_after_its_prefix_lacks_the_traits_marker(tmp_path):
    """A line holding only its part's prefix (`app: `) names the part and nothing else, so it is the line without the
    traits marker, not a broken prefix (stage B2 review, round 6: the sweep's line 585)."""
    st = tmp_path / "status.md"
    st.write_text("Workflows: app: \nWorkflows: site: Web App Development; traits: none\n", encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", STATUS_LIST, "--status", str(st))
    shown = str(st).replace("\\", "/")
    assert lines == whole_output([f"FAIL (form) {shown}: - - Workflows line must contain '; traits: ' exactly once"]), lines
    assert rc == 1
