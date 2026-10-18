"""workflow-check.py (TASK-006), the supervisor's tests, written from handoff/TASK-006.md before the delegation.

enforces: docs/REQUIREMENTS.md R-014 (every change targets an existing extension point; replace/set only in a type or
sub-workflow, replace only on a replaceable phase; trait additions only add; a sub-workflow names an existing type
workflow; a `Workflows:` line names one product type, at most one of its sub-types, and traits, all in the open list;
an unwritten type or sub-type fails, an unwritten trait is flagged and non-fatal) and R-033 (the check runs at every
bridge release, in CI). The fixtures are tests/fixtures/workflows/: `pass/` is the CI root, `fail/<case>/` one root per
failing case, `status/` the status-line cases with an open list of their own.
"""
import codecs
import importlib.util
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
    'd-unknown-sub-type-key': [
        'FAIL (d) {root}/types/host-extension/claude-code-extention.md: claude-code-extention - not a sub-type of host-extension',
        'FAIL (a) {root}/types/host-extension/claude-code-extention.md: nowhere.at-all - point is not in the extension-point registry',
    ],
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
    # Each form matched exactly: text after the key or the kind, and a space after the key (round 6: tests); then
    # each of the four forms loosened one way at a time, two spaces after `##`, two spaces between words, a space
    # after the key or the kind, lower case, nineteen headings, and `##+Add at ...`, which is no heading and gives
    # nothing (round 7: fixtures 2 and the widened sweep).
    'form-heading-trailing-text': [
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
    ] * 24,
    'form-indented-fence-open': ['FAIL (form) {root}/types/host-extension.md: - - fenced code block is still open at the end of the file'],
    # Indented one and three spaces (three is the most a heading may be indented), and a tab after `##` (round 6:
    # fixtures 1 and 2; the comment corrected in round 9: fixtures 2).
    'form-indented-heading': [
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
        'FAIL (form) {root}/types/host-extension.md: - - change heading is not one of the four forms',
    ],
    # Each inflected change word without `at`, a two-word heading ending `at`, and `AT` in capitals (stage B2 review,
    # round 5: fixtures 1, and the supervisor's mutation sweep); add, set and replace without `at` are in
    # form-change-word-punctuation and form-heading-trailing-text, adding and setting in the first (round 10: fixtures 2).
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
    # A file that is not `.md` under traits/, under types/ and under a type's folder (round 6: tests, fixtures 2), and
    # one of each whose name ends in `md` without the dot (round 7: fixtures 2, the widened sweep's lines 360 to 364).
    'form-not-markdown': [
        'FAIL (form) {root}/traits/installable.txt: installable.txt - path is not a conditional-workflow file',
        'FAIL (form) {root}/traits/installablemd: installablemd - path is not a conditional-workflow file',
        'FAIL (form) {root}/types/host-extension/notes.txt: notes.txt - path is not a conditional-workflow file',
        'FAIL (form) {root}/types/host-extension/notesmd: notesmd - path is not a conditional-workflow file',
        'FAIL (form) {root}/types/host-extensionabc: host-extensionabc - path is not a conditional-workflow file',
        'FAIL (form) {root}/types/host-extensionmd: host-extensionmd - path is not a conditional-workflow file',
    ],
    'form-third-level': [
        'FAIL (form) {root}/types/host-extension/claude-code-extension: claude-code-extension - path is not a conditional-workflow file',
        'FAIL (form) {root}/types/host-extension/claude-code-extension/extra.md: extra.md - path is not a conditional-workflow file',
    ],
    # A folder under traits/ (stage B2 review, round 5: fixtures 2), one named like a trait file too (round 6: the
    # sweep's line 364), which hides no type file of its name (BUG-007's gate round 1: Review A, the sweep's 342).
    'form-traits-folder': [
        'FAIL (form) {root}/traits/installable: installable - path is not a conditional-workflow file',
        'FAIL (form) {root}/traits/installable/extra.md: extra.md - path is not a conditional-workflow file',
        'FAIL (form) {root}/traits/odd.md: odd.md - path is not a conditional-workflow file',
        'FAIL (form) {root}/traits/odd.md/extra.md: extra.md - path is not a conditional-workflow file',
        'FAIL (unknown) {root}/types/odd.md: odd - not a product type key',
        'FAIL (a) {root}/types/odd.md: nowhere.at-all - point is not in the extension-point registry',
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
    # A lone backtick is no pair, so it stays, printed as itself (round 8: tests, the first sweep's line 485 once its
    # numbers were moved).
    'kind-two-backticks': [
        'FAIL (kind) {root}/types/host-extension.md: - - Set at intake.delivery-kind is not one delivery kind',
        'FAIL (kind) {root}/types/host-extension/claude-code-extension.md: ` - Set at intake.delivery-kind is not one delivery kind',
    ],
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

# The single-line status files have no Phase line: only check_status reads them, and workflow-check.py never runs
# check_placement (inventory-check.py and conformance-check.py do), so a placement check added to it would need a
# Phase line in each (round 7: fixtures 5, consider). The prefix of a name is the case's subject, not always its
# finding code: form-traits-none-case and form-unclassified-with-traits are cases of the traits text's and the
# unclassified line's form, read as unknown names.
STATUS_EXACT = {
    # An unprefixed `not yet classified` among several lines breaks the part-prefix rule like any other line (round
    # 7: fixtures 5).
    'form-prefix-missing-unclassified.md': ['FAIL (form) {path}: - - Workflows line breaks the part-prefix rule'],
    'bom-workflows-line.md': [],
    'e-lone-trait.md': ['FAIL (e) {path}: - - part must name exactly one product type'],
    'e-no-type.md': ['FAIL (e) {path}: - - part must name exactly one product type'],
    'e-same-part.md': ['FAIL (e) {path}: app - two Workflows lines name the same part'],
    # A part named three times is one (e), and the repeated lines are still checked, the third too: its unknown trait
    # is reported (round 6: fixtures 3, programs; round 8: fixtures 3, a mutant that stopped at the third line).
    'e-same-part-three.md': ['FAIL (e) {path}: app - two Workflows lines name the same part',
                             'FAIL (unknown) {path}: Glitter - not a trait name'],
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
    # A prefix on a single line fails before its name is read, so this is the single-line rule, not the `;` rule;
    # form-part-semicolon holds that (round 8: fixtures 4, consider).
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
    # A colon with no space after it is no `<part>: ` prefix, so the line has none (round 8: fixtures 4).
    'form-part-colon-no-space.md': ['FAIL (form) {path}: - - Workflows line breaks the part-prefix rule'],
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
    # The third `Has screens` is repeated and below the highest trait so far; the program reports a name once, its
    # repeat, a reading the grammar leaves open (round 8: fixtures 4, consider; recorded in HARDENING).
    'form-trait-repeat-separated.md': ['FAIL (form) {path}: Has screens - trait repeated'],
    # The highest trait so far rises as traits come in order, so a later one below it fails (round 6: tests).
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
    # `none` is the whole traits text or no trait at all: beside a name it is an unknown name, first or last (round
    # 7: fixtures 4, the widened sweep's line 646).
    'form-traits-none-first.md': ['FAIL (unknown) {path}: none - not a trait name'],
    'form-traits-none-last.md': ['FAIL (unknown) {path}: none - not a trait name'],
    # An empty traits text, and one ending `, ` (round 6: tests).
    'form-traits-empty.md': ['FAIL (form) {path}: - - traits are not joined by a comma and one space'],
    'form-traits-trailing-comma.md': ['FAIL (form) {path}: - - traits are not joined by a comma and one space'],
    'form-traits-marker-twice.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
    # A rest that only starts as `not yet classified`, or differs in case or by a space, is read as names (stage B2
    # review, round 5: tests and fixtures 4, converged).
    'form-unclassified-case.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
    'form-unclassified-trailing-space.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
    # A space before it, or words before it, too (round 7: fixtures 5, the widened sweep's line 692).
    'form-unclassified-leading-space.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
    'form-unclassified-ending.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
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
    # A key where a Name belongs: the line is read by name only (stage B2 review, round 3: fixtures 4). `installable`
    # is also the Name in another case; its twin unknown-trait-key-not-case is the key alone (round 10: fixtures 6).
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
    # Stage B2's review, round 9: each line after one that stops early is checked (tests, blocking); a `not yet
    # classified` line names its part (tests, blocking); a line that breaks the prefix rule, or has no traits marker, is
    # not checked further though what follows would fail (fixtures 4, blocking); a name after a finding is checked
    # (tests, should-fix); a trait key is no trait name (fixtures 6). form-bad-prefix-bodies-unchecked's fourth line,
    # its body valid, repeats the first line's refused part `a;b`: a refused part is never counted for "the same part",
    # so the line gives its prefix finding alone (round 10: fixtures 4, consider).
    'e-after-unclassified.md': ['FAIL (unknown) {path}: Toaster Development - name is not in the open list', 'FAIL (e) {path}: - - part must name exactly one product type'],
    'form-bad-prefix-then-checked.md': ['FAIL (form) {path}: a;b - Workflows line breaks the part-prefix rule', 'FAIL (unknown) {path}: Toaster Development - name is not in the open list', 'FAIL (e) {path}: - - part must name exactly one product type'],
    'form-no-traits-marker-then-checked.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once", 'FAIL (unknown) {path}: Toaster Development - name is not in the open list', 'FAIL (e) {path}: - - part must name exactly one product type'],
    'e-same-part-unclassified.md': ['FAIL (e) {path}: app - two Workflows lines name the same part'],
    'form-bad-prefix-bodies-unchecked.md': [
        'FAIL (form) {path}: a;b - Workflows line breaks the part-prefix rule',
        'FAIL (form) {path}: c;d - Workflows line breaks the part-prefix rule',
        'FAIL (form) {path}: a;b - Workflows line breaks the part-prefix rule',
    ],
    'form-bad-prefix-single-unknown.md': ['FAIL (form) {path}: app - Workflows line breaks the part-prefix rule'],
    'form-bad-prefix-single-two-types.md': ['FAIL (form) {path}: app - Workflows line breaks the part-prefix rule'],
    'form-bad-prefix-single-unwritten.md': ['FAIL (form) {path}: app - Workflows line breaks the part-prefix rule'],
    'form-no-traits-marker-unknown-head.md': ["FAIL (form) {path}: - - Workflows line must contain '; traits: ' exactly once"],
    'form-empty-name-then-unknown.md': ['FAIL (form) {path}: - - empty name in the Workflows head', 'FAIL (unknown) {path}: Toaster Development - name is not in the open list', 'FAIL (e) {path}: - - part must name exactly one product type'],
    'unknown-trait-then-flag.md': ['FAIL (unknown) {path}: Glitter - not a trait name', 'FLAG (trait) {path}: Spends money - trait not yet written; flagged, work continues (non-fatal)'],
    'form-trait-separator-then-flag.md': ['FAIL (form) {path}: Has screens,Installable - traits are not joined by a comma and one space', 'FLAG (trait) {path}: Spends money - trait not yet written; flagged, work continues (non-fatal)'],
    'form-trait-repeated-then-flag.md': ['FAIL (form) {path}: Installable - trait repeated', 'FLAG (trait) {path}: Spends money - trait not yet written; flagged, work continues (non-fatal)'],
    'unknown-trait-key-not-case.md': ['FAIL (unknown) {path}: has-screens - not a trait name'],
    # Stage B2's review, round 10 (tests, blocking): a line given twice is two lines, each judged; read with its
    # repeats dropped, the unprefixed pair would be one valid line and the prefixed pair a single line with a prefix
    # (BUG-011, the idiom sweep's lines 676 and 679). A name given twice in a head is two names, so the counts fail
    # (supervisor.md "Project state": exactly one product type, at most one sub-type; round 10: tests, consider, line 609).
    'e-same-part-identical.md': ['FAIL (e) {path}: app - two Workflows lines name the same part'],
    'form-prefix-missing-identical.md': ['FAIL (form) {path}: - - Workflows line breaks the part-prefix rule',
                                         'FAIL (form) {path}: - - Workflows line breaks the part-prefix rule'],
    'e-type-named-twice.md': ['FAIL (e) {path}: - - part must name exactly one product type'],
    'e-sub-type-named-twice.md': ['FAIL (e) {path}: - - part must name at most one sub-type'],
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
    assert fails(lines) == ["FAIL (form) %s/status/flag-repeated-unwritten.md: Spends money - trait repeated" % FIX], lines


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
    # The usage line stays as argparse prints it, on standard error (the program's usage text; round 7: tests).
    assert err.startswith("usage: workflow-check.py"), err


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
    text = (REPO / root / "traits/installable.md").read_text(encoding="utf-8")
    assert [line for line in text.split("\n") if line.startswith("## ")] == [
        "## Set: intake.delivery-kind", "## Add: intake.questions", "## Replace: design", "## Adding intake.questions",
        "## Setting intake.budget-kind", "## Adds. intake.questions", "## Set; intake.target-environment",
        "## Replace, design", "## Add- intake.questions", "## Set:; intake.budget-kind",
    ], "precondition: each heading the docstring names, two marks on the last (round 7: fixtures 1)"
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
    # The three headings print the same (form) line, so their whole list is pinned (round 10: fixtures 2, consider).
    assert _headings("fail/form-indented-heading/types/host-extension.md") == [
        " ## Set at intake.target-environment", "##" + chr(9) + "Add at intake.questions", "   ## Add at intake.questions"]
    rc, lines, err = run(root)
    assert rc == 1
    assert len([line for line in fails(lines) if line.startswith(f"FAIL (form) {root}/types/host-extension.md: ")]) == 3, lines


def test_r014_usage_error_message_is_escaped():
    """R3-1: an argument holding a newline cannot start a GitHub workflow command on standard error."""
    rc, lines, err = run("--bogus\n::warning::injected")
    assert rc == 2 and lines[-1] == "RESULT: not checked", (lines, err)
    assert "\n::warning::" not in err and not err.startswith("::warning::"), err
    assert "\\x0a::warning::injected" in err, err


@pytest.mark.parametrize("sep", ["|---|", "|---|---|---|---|---|---|---|---|", "|---|x|---|---|---|---|---|",
                                 "|---|---|---|---|---|---| |", "|---|---|---|---|---|---|:|"],
                         ids=["one-cell", "eight-cells", "second-cell-not-dashes", "last-cell-blank", "last-cell-colon-only"])
def test_r014_separator_cell_count_differs(tmp_path, sep):
    """R3-2; every cell of the separator is dashes, not the first only (round 7: the widened sweep's line 181); a cell
    is at least one dash, so a blank cell, or one holding only an alignment colon, is none (stage B2's review, round
    10: tests, should-fix; the separator test without its `bool(text)`)."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    good = "| Key | Name | Definition | Workflow name | Default traits | Written | Planned |\n|---|---|---|---|---|---|---|\n"
    assert good in text
    broken = tmp_path / "open-list.md"
    broken.write_text(text.replace(good, good.split("\n")[0] + "\n" + sep + "\n", 1), encoding="utf-8")
    rc, lines, err = run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md")
    assert_not_checked(rc, lines, err)
    # The cause is the separator (BUG-008's gate round 1: Review A, consider).
    shown = str(broken).replace("\\", "/")
    assert lines == [f"ERROR: {shown}: table after ## Product types has no separator row", "RESULT: not checked"], lines


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
    # The whole output, so a deeper line under either link would show (round 7: tests).
    assert lines == whole_output([
        f"FAIL (form) {shown}/traits: traits - path is not a conditional-workflow file",
        f"FAIL (form) {shown}/types: types - path is not a conditional-workflow file",
    ]), lines
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
    if case == "fence-info-string-not-closing":
        assert "\n```\n```python\n```\n" in text, "precondition: a run with text after it inside (round 7: fixtures 1)"
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
    ("status/form-no-line.md", "\nWorkflows:Web", "a Workflows line without its space is not one (round 8: fixtures 4)"),
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
    ("fail/form-traits-folder/traits/odd.md/extra.md", "## Add at nowhere.at-all\n",
     "a folder named like a trait file is a folder (the sweep's line 364), and its file is never read"),
    ("fail/form-traits-folder/traits/installable/extra.md", "## Add at nowhere.at-all\n",
     "a file in a folder under traits/ is never read (BUG-007's gate round 2: Review A)"),
    ("fail/form-not-markdown/traits/installable.txt", "## Add at nowhere.at-all\n",
     "a file under traits/ that is not .md is never read (BUG-007's gate round 2: Review A)"),
    ("fail/form-traits-folder/types/odd.md", "## Add at nowhere.at-all\n",
     "a type file named as the folder under traits/ is still checked (the sweep's line 342)"),
    ("fail/form-not-markdown/types/host-extensionabc", "## Add at nowhere.at-all\n",
     "a path that is no conditional workflow is never read: its failing change is not reported"),
    ("fail/form-not-markdown/types/host-extension/notes.txt", "## Add at nowhere.at-all\n",
     "a path that is no conditional workflow is never read: its failing change is not reported"),
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
    traceback, and nothing else is checked: a readable failing file beside it, reported when the file is UTF-8, is not
    reported then (stage B2 review, round 6: programs and tests; the sweep's line 806; the sibling per BUG-007's gate
    round 1, Review B)."""
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "traits").mkdir()
    (root / "traits" / "not-a-trait.md").write_bytes(b"## Add at intake.questions\n\nq\n")
    path = root / "types" / "host-extension.md"
    path.write_bytes(b"## Add at intake.questions\n\nq\n")
    shown = str(root).replace("\\", "/")
    assert run(str(root)) == (1, [f"FAIL (unknown) {shown}/traits/not-a-trait.md: not-a-trait - not a trait key",
                                  "RESULT: 1 problem(s)"], "")
    path.write_bytes(b"## Add at intake.questions\n\n\xff\n")
    rc, lines, err = run(str(root))
    assert_not_checked(rc, lines, err)
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
    """A link the walk lists among a folder's files (one whose target is gone, named like a trait file so that reading it
    as a file would be an ERROR), a link to a folder named like a trait file, and a `types` path that is a link to a
    folder are each reported at their exact line and never read or walked (stage B2 review, round 6: the sweep's lines
    335, 336 and 353; the name per BUG-007's gate round 1, Review A)."""
    outside = _outside_with_canary(tmp_path)
    gone = tmp_path / "gone"
    gone.mkdir()
    root = tmp_path / "root"
    (root / "traits").mkdir(parents=True)
    (root / "traits" / "installable.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    _link_folder(root / "traits" / "gone.md", gone)
    gone.rmdir()
    _link_folder(root / "traits" / "has-screens.md", outside)
    _link_folder(root / "types", outside)
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/")
    assert lines == whole_output([
        f"FAIL (form) {shown}/traits/gone.md: gone.md - path is not a conditional-workflow file",
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


CLOSED_STDOUT = "import os, subprocess, sys\nos.close(1)\nsys.exit(subprocess.call([sys.executable] + sys.argv[1:]))\n"


def test_r014_closed_standard_output_gives_no_traceback():
    """With standard output closed (a launch with no standard handles: Python then sets sys.stdout to None) the check
    still decides its exit code, 0, 1 or 2, and prints no traceback, which the usage text promises for exit 2 (BUG-007's
    gate round 3: Review A, the sweep's line 833 with its condition forced true). The launch is shown first to give
    the child no standard output (its gate round 4: Review A)."""
    p = subprocess.run([sys.executable, "-c", CLOSED_STDOUT, "-c", "import sys; sys.stderr.write(repr(sys.stdout))"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    assert (p.returncode, p.stderr) == (0, "None"), "precondition: the child starts with standard output closed"
    for root, code in ((f"{FIX}/pass", 0), (f"{FIX}/fail/form-bad-heading", 1), (f"{FIX}/absent-root", 2)):
        p = subprocess.run([sys.executable, "-c", CLOSED_STDOUT, PROG, root], cwd=str(REPO), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True, encoding="utf-8")
        assert p.returncode == code and "Traceback" not in p.stderr, (root, p.returncode, p.stderr)


def test_r014_root_the_system_refuses_is_not_walked(tmp_path):
    """A root the system refuses outright (a name Windows rejects; a link to itself on POSIX) is `not a folder` and
    nothing under it is examined, so no further ERROR line follows (BUG-007's gate round 4: Review A, the sweep's line
    795, its `continue` deleted). The root's `types/` is shown first to raise an error the walk reports, not one it
    skips quietly (its gate round 5: Review A)."""
    if os.name == "nt":
        root = tmp_path / "a<b"
    else:
        root = tmp_path / "loop"
        os.symlink("loop", str(root))
    with pytest.raises(OSError) as refused:
        os.lstat(str(root / "types"))
    assert not isinstance(refused.value, (FileNotFoundError, NotADirectoryError)), \
        ("precondition: examining the root's types/ would be an ERROR, not a quiet skip", refused.value)
    rc, lines, err = run(str(root))
    assert_not_checked(rc, lines, err)
    assert lines == [f"ERROR: {str(root).replace(chr(92), '/')}: not a folder", "RESULT: not checked"], lines


# --- stage B2 review, round 7 (BUG-008): the seventh review's controls and the widened sweep's survivors -------------

ROUND7_PRECONDITIONS = [
    # (fixture, text it holds, the rule the text gives a control to)
    ("fail/form-heading-trailing-text/types/host-extension.md", "\n##  Add at intake.questions\n",
     "two spaces after `##` are not one of the four forms (the widened sweep's line 66)"),
    ("fail/form-heading-trailing-text/types/host-extension.md", "\n## Set at  intake.target-environment\n",
     "two spaces between words are not one of the four forms (fixtures 2)"),
    ("fail/form-heading-trailing-text/types/host-extension.md", "\n## Replace interface \n",
     "a space after the module is not one of the four forms (fixtures 2)"),
    ("fail/form-heading-trailing-text/types/host-extension.md", "\n## Add at project-end.delivery for installer \n",
     "a space after the delivery kind is not one of the four forms (fixtures 2)"),
    ("fail/form-heading-trailing-text/types/host-extension.md", "\n## set at intake.target-environment\n",
     "the forms are matched in their case (fixtures 2)"),
    ("fail/form-heading-trailing-text/types/host-extension.md", "\n##+Add at intake.questions\n",
     "a `##` with no space or tab after it is no heading (the widened sweep's line 78)"),
    ("pass/types/host-extension.md", "\n```\n```+\n## Replace design\n```\n",
     "a backtick run with text after it does not close a fence (the widened sweep's line 83)"),
    ("pass/types/host-extension.md", "\n## Look atop the target\n",
     "a second word that starts with `at` is not `at` (the widened sweep's line 390)"),
    ("pass/types/host-extension.md", "\n## Go combat it\n",
     "a second word that ends with `at` is not `at` (the widened sweep's line 390)"),
    ("pass/types/host-extension.md", "\n## Stay a while\n",
     "a second word that begins `at` is not `at` (BUG-008's gate round 1: the widened sweep's line 390)"),
    ("pass/types/host-extension.md", "\n## Hold t tight\n",
     "a second word that ends `at` is not `at` (BUG-008's gate round 1: the widened sweep's line 390)"),
    ("pass/README.md", "Nothing outside types/ and traits/ is read.",
     "a file outside types/ and traits/ in the pass root is never read (round 7: fixtures 3)"),
    ("pass/README.md", "\n## Add at nowhere.at-all\n",
     "the README holds a change heading that would fail if its content were read (round 10: fixtures 3, consider)"),
]


@pytest.mark.parametrize("rel,held,rule", ROUND7_PRECONDITIONS, ids=[f"{r}:{i}" for i, (r, _, _) in enumerate(ROUND7_PRECONDITIONS)])
def test_r014_round7_fixtures_hold_their_controls(rel, held, rule):
    """Each fixture holds the text that makes its case a control (stage B2 review, round 7); the cases' outputs are in
    FILE_EXACT and STATUS_EXACT, and the pass root must stay RESULT: OK."""
    text = (REPO / FIX / rel).read_text(encoding="utf-8")
    assert held in text, rule


def test_r014_round7_trailing_spaces_are_bytes_of_the_fixture():
    """The three headings that end in a space keep it: an editor that trims it would turn the control into a copy of
    another (round 7: fixtures 2)."""
    data = (REPO / FIX / "fail/form-heading-trailing-text/types/host-extension.md").read_bytes().replace(b"\r\n", b"\n")
    for heading in (b"## Add at intake.questions ", b"## Replace interface ", b"## Add at project-end.delivery for installer "):
        assert b"\n" + heading + b"\n" in data, heading


def test_r014_every_unreadable_file_is_reported(tmp_path):
    """Each file that cannot be read is its own ERROR line, in path order, before RESULT: not checked, not the first
    only (round 7: the widened sweep's line 818)."""
    root = tmp_path / "root"
    (root / "traits").mkdir(parents=True)
    (root / "traits" / "has-screens.md").write_bytes(b"## Add at intake.questions\n\n\xff\n")
    (root / "traits" / "installable.md").write_bytes(b"## Add at intake.questions\n\n\xfe\n")
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/")
    assert rc == 2 and "Traceback" not in err, (lines, err)
    assert lines == [
        f"ERROR: {shown}/traits/has-screens.md: cannot be read as UTF-8",
        f"ERROR: {shown}/traits/installable.md: cannot be read as UTF-8",
        "RESULT: not checked",
    ], lines


# --- BUG-008's gate round 1 (Review A): comparisons against the rule files' own values ---------------------------------

ARROW = chr(0x2192)


def _open_list_copy(tmp_path, name, change):
    """The status cases' open list with one change, each of whose anchors is asserted once."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    for old, new in change:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _status_file(tmp_path, line):
    path = tmp_path / "status.md"
    path.write_text("Phase: building\n" + line + "\n", encoding="utf-8")
    return path


ROW_HOST = "| host-extension | Host extension | Runs inside another application | Host Extension Development | installable | yes | — |"
ROW_CCE = "| claude-code-extension | Claude Code extension | host-extension | Runs inside Claude Code | Claude Code Extension | installable | yes | — |"
ROW_INSTALLABLE = "| installable | Installable | Delivered as something installed | yes | — |"


# Values other than `yes`: another case, `yes` with more after it, a part of `yes`.
NOT_YES = ["Yes", "yes, later", "y"]


@pytest.mark.parametrize("value", NOT_YES)
def test_r014_written_other_than_yes_is_unwritten(tmp_path, value):
    """handoff/TASK-006.md: Written is `yes` or `no`, and any value other than `yes` is unwritten, its case included: a
    product type, a sub-type and a trait written `Yes`, `yes, later` or `y` give (f), (f) and the trait's FLAG
    (BUG-008's gate round 1: Review A, the widened sweep's lines 638, 640 and 667)."""
    open_list = _open_list_copy(tmp_path, "open-list.md", [(row, row.replace("| yes |", "| %s |" % value))
                                                           for row in (ROW_HOST, ROW_CCE, ROW_INSTALLABLE)])
    status = _status_file(tmp_path, "Workflows: Host Extension Development " + ARROW + " Claude Code Extension; traits: Installable")
    # The control: the same line against the list as written, `yes` in all three rows, gives nothing.
    assert run("--open-list", STATUS_LIST, "--status", str(status))[:2] == (0, ["RESULT: OK"])
    rc, lines, err = run("--open-list", str(open_list), "--status", str(status))
    shown = str(status).replace("\\", "/")
    assert lines == whole_output([
        f"FAIL (f) {shown}: Host Extension Development - product type is not written",
        f"FAIL (f) {shown}: Claude Code Extension - sub-type is not written",
        f"FLAG (trait) {shown}: Installable - trait not yet written; flagged, work continues (non-fatal)",
    ]), lines
    assert rc == 1 and err == "", err


@pytest.mark.parametrize("value", NOT_YES)
def test_r014_replaceable_other_than_yes_is_not_replaceable(tmp_path, value):
    """The registry's Replaceable is `yes` or `no`, and only `yes` lets a type file replace the module (the program's
    usage text: whose Replaceable is not yes): the interface module marked `Yes`, `yes, later` or `y` refuses a Replace
    with (c) (BUG-008's gate round 1: Review A, the widened sweep's line 540)."""
    reg = (REPO / "bridge/cursor-bridge/workflow/extension-points.md").read_text(encoding="utf-8")
    row = "| interface | Interface phase | yes |"
    assert reg.count(row) == 1, "the interface module's row"
    registry = tmp_path / "extension-points.md"
    registry.write_text(reg.replace(row, row.replace("| yes |", "| %s |" % value)), encoding="utf-8")
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "types" / "host-extension.md").write_text("## Replace interface\n\nAn interface.\n", encoding="utf-8")
    # The control: the same root against the registry as written, interface replaceable `yes`, gives nothing.
    assert run("--open-list", STATUS_LIST, str(root))[:2] == (0, ["RESULT: OK"])
    rc, lines, err = run("--open-list", STATUS_LIST, "--registry", str(registry), str(root))
    shown = str(root).replace("\\", "/")
    assert lines == whole_output([f"FAIL (c) {shown}/types/host-extension.md: interface - module is missing or not replaceable"]), lines
    assert rc == 1


RETIRED = ("## Product types (retired)\n\n| Key | Name | Definition | Workflow name | Default traits | Written | Planned |\n"
           "|---|---|---|---|---|---|---|\n| library | Library | Included by other programs | Library Development | — | no | — |\n\n")


@pytest.mark.parametrize("how", ["longer-heading-first", "deeper-heading-first", "trailing-space", "lower-case"])
def test_r014_a_table_is_read_under_its_exact_heading(tmp_path, how):
    """workflow/open-list.md, "How this file is read": each table is the first table after its heading, the heading
    named exactly: a longer heading, or a deeper one (`### Product types`), with its own table before the real one
    is not it, and a heading in lower case is no heading at all, so the table is missing (BUG-008's gate round 1:
    Review A, the widened sweep's line 203). A heading with a trailing space is no heading either: the program's
    reading, which handoff/TASK-006.md left open (its `Assumed, not verified` example), pinned here and recorded in
    docs/HARDENING.md as a lead (gate round 2: Review A)."""
    head = "## Product types\n"
    new = {"longer-heading-first": RETIRED + head, "deeper-heading-first": "#" + RETIRED.replace(" (retired)", "") + head,
           "trailing-space": "## Product types \n", "lower-case": "## product types\n"}[how]
    open_list = _open_list_copy(tmp_path, "open-list.md", [(head, new)])
    status = _status_file(tmp_path, "Workflows: Host Extension Development; traits: none")
    rc, lines, err = run("--open-list", str(open_list), "--status", str(status))
    if how.endswith("-first"):
        assert (rc, lines) == (0, ["RESULT: OK"]), lines
    else:
        shown = str(open_list).replace("\\", "/")
        assert (rc, lines) == (2, [f"ERROR: {shown}: missing heading ## Product types", "RESULT: not checked"]), lines


# Product keys where one begins the other, `web` and `web-app`, each with a sub-type of its own.
WEB_ROWS = [
    ("| library |", "| web | Web | Served from a host | Web Development | — | yes | — |\n| library |"),
    ("| local-web-app |", "| local-web | Local web | web | Opened at a local address | Local Web | — | yes | — |\n| local-web-app |"),
]


@pytest.mark.parametrize("line,sub", [
    ("Workflows: Web App Development " + ARROW + " Local Web; traits: none", "Local Web"),
    ("Workflows: Web Development " + ARROW + " Local Web App; traits: none", "Local Web App"),
], ids=["sub-of-web-on-a-web-app-line", "sub-of-web-app-on-a-web-line"])
def test_r014_a_sub_type_is_of_the_lines_type_by_its_whole_key(tmp_path, line, sub):
    """supervisor.md, the Workflows grammar: a sub-type is of the line's product type, its Of type the type's key
    exactly; a key that only begins the other's is another type (BUG-008's gate round 1: Review A, the widened sweep's
    line 625)."""
    open_list = _open_list_copy(tmp_path, "open-list.md", WEB_ROWS)
    status = _status_file(tmp_path, line)
    rc, lines, err = run("--open-list", str(open_list), "--status", str(status))
    shown = str(status).replace("\\", "/")
    assert lines == whole_output([f"FAIL (e) {shown}: {sub} - sub-type is not of the line's product type"]), lines


@pytest.mark.parametrize("type_key,sub_key", [("web-app", "local-web"), ("web", "local-web-app")],
                         ids=["sub-of-web-under-web-app", "sub-of-web-app-under-web"])
def test_r014_a_sub_workflow_is_under_its_type_by_its_whole_key(tmp_path, type_key, sub_key):
    """handoff/TASK-006.md, the (d) finding: a sub-workflow file sits under its sub-type's own type, the Of type equal to
    the folder's key; a key that only begins the other's is another type (BUG-008's gate round 1: Review A, the widened
    sweep's line 553)."""
    open_list = _open_list_copy(tmp_path, "open-list.md", WEB_ROWS)
    root = tmp_path / "root"
    (root / "types" / type_key).mkdir(parents=True)
    (root / "types" / (type_key + ".md")).write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    (root / "types" / type_key / (sub_key + ".md")).write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    rc, lines, err = run("--open-list", str(open_list), str(root))
    shown = str(root).replace("\\", "/")
    assert lines == whole_output([f"FAIL (d) {shown}/types/{type_key}/{sub_key}.md: {sub_key} - not a sub-type of {type_key}"]), lines


LOCAL_WEB_APP = "| local-web-app | Local web app | web-app | Opened at a local address | Local Web App | installable | no | — |"


def test_r014_an_of_type_in_another_case_is_another_type(tmp_path):
    """A sub-type's Of type is its type's key exactly, its case included (handoff/TASK-006.md: Of type is the sub-type's
    product-type key; workflow/open-list.md: a key is lowercase letters, digits and hyphens): local-web-app written of
    `Web-App` is of no type, so the line gives (e) and its file under types/web-app/ gives (d) (BUG-008's gate round 1:
    the widened sweep's lines 553 and 625)."""
    open_list = _open_list_copy(tmp_path, "open-list.md", [(LOCAL_WEB_APP, LOCAL_WEB_APP.replace("| web-app |", "| Web-App |"))])
    status = _status_file(tmp_path, "Workflows: Web App Development " + ARROW + " Local Web App; traits: none")
    rc, lines, err = run("--open-list", str(open_list), "--status", str(status))
    shown = str(status).replace("\\", "/")
    assert lines == whole_output([f"FAIL (e) {shown}: Local Web App - sub-type is not of the line's product type"]), lines
    root = tmp_path / "root"
    (root / "types" / "web-app").mkdir(parents=True)
    (root / "types" / "web-app.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    (root / "types" / "web-app" / "local-web-app.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    rc, lines, err = run("--open-list", str(open_list), str(root))
    shown = str(root).replace("\\", "/")
    assert lines == whole_output([f"FAIL (d) {shown}/types/web-app/local-web-app.md: local-web-app - not a sub-type of web-app"]), lines


# --- BUG-008's gate round 2 (Review A): the delivery rules at their two points exactly ------------------------------

NOT_THE_DELIVERY_POINTS = [
    # A longer key, another case, a part of it, its last part, a key ending with it: none is the point.
    "project-end.delivery-notes", "Project-End.Delivery", "project-end", "delivery", "x-project-end.delivery",
    "intake.delivery-kind-notes", "Intake.Delivery-Kind", "intake", "delivery-kind", "x-intake.delivery-kind",
]


def test_r014_the_delivery_rules_apply_at_their_two_points_exactly(tmp_path):
    """handoff/TASK-006.md Requirement 9: `FAIL (kind)` for an `## Add at project-end.delivery` heading with no
    ` for <kind>`, and for a `## Set at intake.delivery-kind` section whose first non-blank line is not one kind. A point
    key that is not exactly one of the two is another point, here one the registry lacks, so each heading gives (a)
    alone, with no (kind) line, though no kind is named and the body is no kind (BUG-008's gate round 2: Review A, the
    widened sweep's lines 524 and 533)."""
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    adds, sets = NOT_THE_DELIVERY_POINTS[:5], NOT_THE_DELIVERY_POINTS[5:]
    text = "".join("## Add at %s\n\nnonsense\n\n" % key for key in adds) + "".join("## Set at %s\n\nnonsense\n\n" % key for key in sets)
    (root / "types" / "host-extension.md").write_text(text, encoding="utf-8")
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/") + "/types/host-extension.md"
    assert lines == whole_output([f"FAIL (a) {shown}: {key} - point is not in the extension-point registry"
                                  for key in adds + sets]), lines
    assert rc == 1 and err == "", err
    # The control: the same bodies under the two points exactly give their (kind) lines (BUG-008's gate round 3).
    exact = tmp_path / "exact"
    (exact / "types").mkdir(parents=True)
    (exact / "types" / "host-extension.md").write_text(
        "## Add at project-end.delivery\n\nnonsense\n\n## Set at intake.delivery-kind\n\nnonsense\n", encoding="utf-8")
    rc, lines, err = run(str(exact))
    shown = str(exact).replace("\\", "/") + "/types/host-extension.md"
    assert lines == whole_output([
        f"FAIL (kind) {shown}: project-end.delivery - addition at project-end.delivery does not name a delivery kind",
        f"FAIL (kind) {shown}: nonsense - Set at intake.delivery-kind is not one delivery kind"]), lines
    assert rc == 1 and err == "", err


# A module name that is not `__main__` exactly: another case, longer, shorter, a part, spaced.
NOT_MAIN = ["__MAIN__", "__main__x", "x__main__", "x__main__x", "__main", "main__", "main", " __main__ "]


@pytest.mark.parametrize("name", NOT_MAIN)
def test_r015_loaded_as_a_module_the_check_runs_nothing(name, monkeypatch, capsys):
    """The judges load workflow-check.py as a module (inventory-check.py and conformance-check.py, by
    spec_from_file_location) and call its checks; the program runs its check only when run as a script, under the
    name `__main__` exactly. Loaded under any other name, with arguments that would end a run at once, it prints
    nothing and does not exit (BUG-008's gate round 2: Review B, the widened sweep's line 831)."""
    monkeypatch.setattr(sys, "argv", ["workflow-check.py", "--bogus"])
    spec = importlib.util.spec_from_file_location(name, str(REPO / PROG))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
    assert capsys.readouterr() == ("", "")
    # The control: under `__main__` exactly the same arguments end a run, exit 2 (BUG-008's gate round 3).
    spec = importlib.util.spec_from_file_location("__main__", str(REPO / PROG))
    with pytest.raises(SystemExit) as stop:
        spec.loader.exec_module(importlib.util.module_from_spec(spec))
    assert stop.value.code == 2
    assert capsys.readouterr().out.splitlines()[-1] == "RESULT: not checked"


# --- stage B2 review, round 8 (BUG-009): the four forms take one space and no other white space ----------------------

# The four forms, each valid against the bridge's registry, with a body each accepts (the pass root's own).
FOUR_FORMS = [
    ("## Add at intake.questions", "q"),
    ("## Add at project-end.delivery for installer", "q"),
    ("## Set at intake.target-environment", "Inside the host application."),
    ("## Replace interface", "An interface."),
]
# White space other than one space, each put in place of one space of a form. A form's words are split as the
# program splits them (is_change_heading: str.split()), so Unicode white space also ends a word: a gap after the first
# word filled with a no-break space, a form feed, a vertical tab or an ideographic space leaves a change heading, which
# is (form), rather than prose. extension-points.md does not define a word; this is the program's reading, the safer
# one (a near-form fails), pinned here (BUG-009's gate round 1: Review A, a consider).
OTHER_SPACE = [("a tab", "\t"), ("two spaces", "  "), ("a space and a tab", " \t"), ("a no-break space", " "),
               ("a form feed", "\x0c"), ("a vertical tab", "\x0b"), ("an ideographic space", "　")]
# Before `##`: one to three spaces make a heading candidate that is no form; four spaces, a tab or other white space
# make no heading at all.
INDENTS = [("one space", " ", True), ("two spaces", "  ", True), ("three spaces", "   ", True),
           ("four spaces", "    ", False), ("a tab", "\t", False), ("a no-break space", " ", False)]
# After the key or the kind: nothing, not even white space.
TRAILING = [("a space", " "), ("a tab", "\t"), ("a no-break space", " "), ("a form feed", "\x0c")]


def _white_space_variants():
    """(label, heading line, body, whether it is a form finding), for each form and each way of loosening it."""
    out = []
    for heading, body in FOUR_FORMS:
        out.append(("%s as written" % heading, heading, body, False))
        gaps = [k for k, ch in enumerate(heading) if ch == " "]
        for n, k in enumerate(gaps):
            for name, ws in OTHER_SPACE:
                # The first gap is the one after `##`: a candidate needs a space or tab there (anything else is prose).
                form = n > 0 or ws[0] in " \t"
                out.append(("%s, gap %d as %s" % (heading, n, name), heading[:k] + ws + heading[k + 1:], body, form))
        for name, ws, form in INDENTS:
            out.append(("%s, indented %s" % (heading, name), ws + heading, body, form))
        for name, ws in TRAILING:
            out.append(("%s, then %s" % (heading, name), heading + ws, body, True))
    return out


def test_r014_the_four_forms_take_one_space_and_no_other_white_space(tmp_path):
    """bridge/cursor-bridge/workflow/extension-points.md, "How a conditional workflow names a point": the four forms are
    matched exactly, `##` at the start of the line, one space between words, nothing after the key or the delivery
    kind; a `##` line is a heading candidate only with at most three spaces before it and a space or tab after it
    (the program's R3-6, its usage of HEADING_CANDIDATE). So each form with a tab, two spaces, a no-break space, a form
    feed, a vertical tab or an ideographic space in place of any one of its spaces, indented one to three spaces, or
    with white space after it is (form); with such white space straight after `##`, indented four spaces, a tab or a
    no-break space it is prose, no finding; and each form as written gives nothing. Each variant is a root of its own,
    so each finding names its variant (stage B2's review, round 8: fixtures-2, eleven loosened patterns surviving)."""
    variants = _white_space_variants()
    roots = []
    for n, (label, line, body, form) in enumerate(variants):
        root = tmp_path / ("v%03d" % n)
        (root / "types").mkdir(parents=True)
        (root / "types" / "host-extension.md").write_text(line + "\n\n" + body + "\n", encoding="utf-8")
        roots.append(root)
    assert sum(1 for v in variants if v[3]) > 100 and sum(1 for v in variants if not v[3]) > 20, "precondition: both kinds"
    rc, lines, err = run(*map(str, roots))
    expected = [f"FAIL (form) {str(root).replace(chr(92), '/')}/types/host-extension.md: - - change heading is not one of the four forms"
                for root, (_, _, _, form) in zip(roots, variants) if form]
    assert lines == whole_output(expected), [v[0] for v, root in zip(variants, roots)
                                             if (str(root).replace(chr(92), "/") in "\n".join(lines)) != v[3]]
    assert rc == 1 and err == "", err


def _headings(rel):
    text = (REPO / FIX / rel).read_text(encoding="utf-8")
    return [line for line in text.split("\n") if line.lstrip(" ").startswith("##")]


def test_r014_round8_the_loosened_heading_files_hold_their_headings():
    """Two fixtures print one identical (form) line per heading, so a heading edited into a copy of another would
    change no output: their whole lists of `##` lines are pinned here (stage B2's review, round 8: fixtures-2,
    considers)."""
    assert _headings("fail/form-heading-trailing-text/types/host-extension.md") == [
        "## Set at intake.target-environment extra", "## Replace interface now", "## Add at intake.questions please",
        "## Set at intake.budget-kind ", "## Add at project-end.delivery for installer extra",
        "##  Add at intake.questions", "##  Set at intake.target-environment", "##  Replace interface",
        "##  Add at project-end.delivery for installer", "## Add  at intake.questions", "## Add at  intake.questions",
        "## Set  at intake.target-environment", "## Set at  intake.target-environment", "## Replace  interface",
        "## Add  at project-end.delivery for installer", "## Add at  project-end.delivery for installer",
        "## Add at project-end.delivery  for installer", "## Add at project-end.delivery for  installer",
        "## Add at intake.questions ", "## Replace interface ", "## Add at project-end.delivery for installer ",
        "## add at project-end.delivery for installer", "## set at intake.target-environment", "## replace interface",
        "##+Add at intake.questions",
    ]
    assert _headings("fail/form-misspelt-change-word/types/host-extension.md") == [
        "## Adds at intake.questions", "## add at intake.questions", "## Replacing interface",
        "## Append at intake.questions", "## Adds intake.questions", "## Added intake.questions",
        "## Sets intake.target-environment", "## Replaces interface", "## Replaced interface", "## Look at",
        "## Look AT intake.questions",
    ]


def test_r014_a_folder_named_like_the_type_file_is_no_type_file(tmp_path):
    """handoff/TASK-006.md, the (d) finding (its line 159: "`types/<t>.md` exists in the same root"): read as a file,
    the program's `isfile`, the stricter reading, taken here; a folder of that name is no such file, so the folder gives its own (d) and the sub-workflow's (d) names the missing
    type workflow (stage B2's review, round 8: tests, consider; `isfile` read as `exists` survived)."""
    root = tmp_path / "root"
    (root / "types" / "host-extension.md").mkdir(parents=True)
    (root / "types" / "host-extension").mkdir()
    (root / "types" / "host-extension" / "claude-code-extension.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8")
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/") + "/types"
    assert lines == whole_output([
        f"FAIL (d) {shown}/host-extension.md: host-extension.md - type folder is not a product type",
        f"FAIL (d) {shown}/host-extension/claude-code-extension.md: claude-code-extension - type workflow types/host-extension.md does not exist",
    ]), lines


# The widened sweep after BUG-009's first cases (run/supervisor/sweep_wide_r6.out): a space of a form made optional, a
# key made possibly empty, and a fence's indent let take a tab survived.
DROPPED = [
    # (heading line, whether it is a form finding)
    ("## Add atintake.questions", True),
    ("## Add atproject-end.delivery for installer", True),
    ("## Add at project-end.deliveryfor installer", True),
    ("## Add at project-end.delivery forinstaller", True),
    ("## Set atintake.target-environment", True),
    # A second word `at` makes a change heading of any first word.
    ("## Addat at", True),
    ("## Addat at for installer", True),
    ("## Setat at", True),
    # `Replace:` is the change word once its trailing colon is stripped.
    ("## Replace:", True),
    # No key, no kind.
    ("## Add at ", True),
    ("## Add at  for installer", True),
    ("## Add at project-end.delivery for ", True),
    ("## Set at ", True),
    ("## Replace ", True),
    # Controls: no space after `##` is no heading candidate; neither word a change word nor `at` is prose.
    ("##Add at intake.questions", False),
    ("##Replace interface", False),
    ("## Addat intake.questions", False),
]


def test_r014_the_four_forms_take_each_of_their_spaces_and_a_key(tmp_path):
    """bridge/cursor-bridge/workflow/extension-points.md, "How a conditional workflow names a point": each form's words
    are separated by one space and its point, module or delivery kind is a word (`\\S+`). So a form with one of its
    spaces dropped, or with its key or kind left out, is no form: (form) when the line is a change heading (its first
    word a change word after trailing punctuation is stripped, or its second word `at`, the program's R3-4), prose
    otherwise. Each variant is a root of its own (stage B2's review, round 8: the widened sweep's `space -> ' ?'` and
    `\\S+ -> \\S*` survivors)."""
    roots = []
    for n, (line, _) in enumerate(DROPPED):
        root = tmp_path / ("d%02d" % n)
        (root / "types").mkdir(parents=True)
        (root / "types" / "host-extension.md").write_text(line + "\n\nq\n", encoding="utf-8")
        roots.append(root)
    rc, lines, err = run(*map(str, roots))
    expected = [f"FAIL (form) {str(root).replace(chr(92), '/')}/types/host-extension.md: - - change heading is not one of the four forms"
                for root, (_, form) in zip(roots, DROPPED) if form]
    assert lines == whole_output(expected), lines
    assert rc == 1 and err == "", err


TAB_FENCES = [
    ("opening-backticks", "## Add at intake.questions\n\nq\n\n\t```\n\n## Set at intake.delivery-kind\n\ninstaller\n"),
    ("opening-tildes", "## Add at intake.questions\n\nq\n\n\t~~~\n\n## Set at intake.delivery-kind\n\ninstaller\n"),
    ("closing", "## Add at intake.questions\n\nq\n\n```\ncode\n\t```\n```\n\n## Set at intake.delivery-kind\n\ninstaller\n"),
]


@pytest.mark.parametrize("text", [t for _, t in TAB_FENCES], ids=[i for i, _ in TAB_FENCES])
def test_r014_a_tab_is_no_fence_indent(tmp_path, text):
    """R4-3 and R5-3: a fence is indented by zero to three spaces; a tab before the run is no such indent (CommonMark
    reads it as four columns, an indented code block). So a run after a tab opens no fence, and closes none: in each
    trait file the `## Set` after it is read and is the one (b), with no fence left open (stage B2's review, round 8:
    the widened sweep's `{0,3} -> [ \\t]{0,3}` on the opening and closing patterns)."""
    root = tmp_path / "root"
    (root / "traits").mkdir(parents=True)
    (root / "traits" / "installable.md").write_text(text, encoding="utf-8")
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/")
    assert lines == whole_output([f"FAIL (b) {shown}/traits/installable.md: intake.delivery-kind - a trait file may only add"]), lines
    assert rc == 1 and err == "", err


# --- stage B2 review, round 9 (BUG-010) ----------------------------------------------------------------------------

# Each status fixture's whole text (line feeds as committed; the checkout may carry CRLF), so the line a case is about
# is stated beside its findings: a fixture given other lines with the same findings fails here (stage B2's review,
# round 9: Review B, four fixtures swapped with every test passing).
STATUS_TEXT = {
    'bom-workflows-line.md': '\ufeffWorkflows: Web App Development; traits: none\n',
    'e-after-unclassified.md': 'Workflows: app: not yet classified\nWorkflows: site: Toaster Development; traits: none\n',
    'e-lone-trait.md': 'Workflows: Installable; traits: none\n',
    'e-no-type.md': 'Workflows: Claude Code Extension; traits: none\n',
    'e-same-part-checked.md': 'Workflows: app: Web App Development; traits: none\nWorkflows: app: Glitter Development; traits: none\n',
    'e-same-part-three.md': 'Workflows: app: Web App Development; traits: none\nWorkflows: app: Web App Development; traits: none\nWorkflows: app: Web App Development; traits: Glitter\n',
    'e-same-part-unclassified.md': 'Workflows: app: not yet classified\nWorkflows: app: Web App Development; traits: none\n',
    'e-same-part.md': 'Workflows: app: Web App Development; traits: none\nWorkflows: app: Host Extension Development; traits: none\n',
    'e-same-part-identical.md': 'Workflows: app: Web App Development; traits: none\nWorkflows: app: Web App Development; traits: none\n',
    'e-sub-type-named-twice.md': 'Workflows: Host Extension Development → Claude Code Extension, Claude Code Extension; traits: none\n',
    'e-type-named-twice.md': 'Workflows: Web App Development, Web App Development; traits: none\n',
    'form-prefix-missing-identical.md': 'Workflows: Web App Development; traits: none\nWorkflows: Web App Development; traits: none\n',
    'e-sub-type-of-another.md': 'Workflows: Web App Development → Claude Code Extension; traits: none\n',
    'e-two-sub-types.md': 'Workflows: Host Extension Development → Claude Code Extension, Browser Extension; traits: none\n',
    'e-two-types.md': 'Workflows: Host Extension Development, Web App Development; traits: none\n',
    'f-unwritten-sub-type.md': 'Workflows: Web App Development → Local Web App; traits: none\n',
    'f-unwritten-type.md': 'Workflows: Library Development; traits: none\n',
    'flag-repeated-unwritten.md': 'Workflows: Web App Development; traits: Installable, Spends money, Spends money\n',
    'flag-unwritten-trait.md': 'Workflows: Host Extension Development; traits: Installable, Spends money\n',
    'form-bad-prefix-bodies-unchecked.md': 'Workflows: a;b: Toaster Development; traits: Glitter\nWorkflows: c;d: Library Development; traits: none\nWorkflows: site: Web App Development; traits: none\nWorkflows: a;b: Web App Development; traits: none\n',
    'form-bad-prefix-single-two-types.md': 'Workflows: app: Library Development, Web App Development; traits: none\n',
    'form-bad-prefix-single-unknown.md': 'Workflows: app: Toaster Development; traits: Glitter\n',
    'form-bad-prefix-single-unwritten.md': 'Workflows: app: Library Development; traits: none\n',
    'form-bad-prefix-single.md': 'Workflows: bad;part: Web App Development; traits: none\n',
    'form-bad-prefix-then-checked.md': 'Workflows: a;b: Web App Development; traits: none\nWorkflows: site: Toaster Development; traits: none\n',
    'form-empty-name-then-unknown.md': 'Workflows: , Toaster Development; traits: none\n',
    'form-empty-segment.md': 'Workflows: Host Extension Development →; traits: none\n',
    'form-no-line.md': '# Project Status\nPhase: building\n  Workflows: Web App Development; traits: none\nworkflows: Web App Development; traits: none\nWorkflows:Web App Development; traits: none\n',
    'form-no-traits-marker-then-checked.md': 'Workflows: app: Web App Development\nWorkflows: site: Toaster Development; traits: none\n',
    'form-no-traits-marker-unknown-head.md': 'Workflows: Toaster Development\n',
    'form-no-traits-marker.md': 'Workflows: Host Extension Development\n',
    'form-part-arrow.md': 'Workflows: a→b: Web App Development; traits: none\nWorkflows: plugin: Host Extension Development; traits: none\n',
    'form-part-blank.md': 'Workflows: app: Web App Development; traits: none\nWorkflows:  : Host Extension Development; traits: none\n',
    'form-part-colon-no-space.md': 'Workflows: app:Web App Development; traits: none\nWorkflows: plugin: Host Extension Development; traits: none\n',
    'form-part-colon.md': 'Workflows: a:b: Web App Development; traits: none\nWorkflows: plugin: Host Extension Development; traits: none\n',
    'form-part-empty.md': 'Workflows: : Web App Development; traits: none\nWorkflows: plugin: Host Extension Development; traits: none\n',
    'form-part-leading-space.md': 'Workflows: app: Web App Development; traits: none\nWorkflows:  plugin: Host Extension Development; traits: none\n',
    'form-part-semicolon.md': 'Workflows: a;b: Web App Development; traits: none\nWorkflows: plugin: Host Extension Development; traits: none\n',
    'form-part-tab.md': 'Workflows: app: Web App Development; traits: none\nWorkflows: plugin\t: Host Extension Development; traits: none\n',
    'form-part-whitespace.md': 'Workflows: app: Web App Development; traits: none\nWorkflows: app : Host Extension Development; traits: none\n',
    'form-prefix-missing-unclassified.md': 'Workflows: not yet classified\nWorkflows: plugin: Host Extension Development; traits: none\n',
    'form-prefix-missing.md': 'Workflows: app: Web App Development; traits: none\nWorkflows: Host Extension Development; traits: none\n',
    'form-prefix-on-single.md': 'Workflows: app: Host Extension Development; traits: none\n',
    'form-sub-type-first.md': 'Workflows: Claude Code Extension → Host Extension Development; traits: none\n',
    'form-trait-double-space.md': 'Workflows: Web App Development; traits: Has screens,  Installable\n',
    'form-trait-in-head.md': 'Workflows: Host Extension Development, Installable; traits: none\n',
    'form-trait-order-highest.md': 'Workflows: Web App Development; traits: Has screens, Spends money, Installable\n',
    'form-trait-order-three.md': 'Workflows: Web App Development; traits: Spends money, Has screens, Installable\n',
    'form-trait-order.md': 'Workflows: Web App Development; traits: Installable, Has screens\n',
    'form-trait-repeat-separated.md': 'Workflows: Web App Development; traits: Has screens, Installable, Has screens\n',
    'form-trait-repeated-then-flag.md': 'Workflows: Web App Development; traits: Installable, Installable, Spends money\n',
    'form-trait-repeated.md': 'Workflows: Web App Development; traits: Installable, Installable\n',
    'form-trait-separator-then-flag.md': 'Workflows: Web App Development; traits: Has screens,Installable, Spends money\n',
    'form-trait-separator.md': 'Workflows: Web App Development; traits: Has screens,Installable\n',
    'form-trait-trailing-space.md': 'Workflows: Web App Development; traits: Has screens , Installable\n',
    'form-traits-double-space.md': 'Workflows: Web App Development; traits:  none\n',
    'form-traits-empty.md': 'Workflows: Web App Development; traits: \n',
    'form-traits-marker-twice.md': 'Workflows: Web App Development; traits: none; traits: none\n',
    'form-traits-none-case.md': 'Workflows: Web App Development; traits: None\n',
    'form-traits-none-first.md': 'Workflows: Web App Development; traits: none, Installable\n',
    'form-traits-none-last.md': 'Workflows: Web App Development; traits: Installable, none\n',
    'form-traits-trailing-comma.md': 'Workflows: Web App Development; traits: Has screens, \n',
    'form-unclassified-case.md': 'Workflows: Not yet classified\n',
    'form-unclassified-ending.md': 'Workflows: Web App not yet classified\n',
    'form-unclassified-leading-space.md': 'Workflows:  not yet classified\n',
    'form-unclassified-trailing-space.md': 'Workflows: not yet classified \n',
    'form-unclassified-with-traits.md': 'Workflows: not yet classified; traits: none\n',
    'ok-multi-unclassified.md': 'Phase: intake\nWorkflows: app: not yet classified\nWorkflows: plugin: Host Extension Development; traits: none\n',
    'ok-multi.md': 'Phase: building\nWorkflows: app: Web App Development; traits: Has screens, Installable\nWorkflows: plugin: Host Extension Development → Browser Extension; traits: none\n',
    'ok-no-final-newline.md': '\nPhase: building\nWorkflows: Host Extension Development → Claude Code Extension; traits: Installable',
    'ok-single.md': '# Project Status\nPhase: building\nWorkflows: Host Extension Development → Claude Code Extension; traits: Installable\n',
    'ok-unclassified.md': 'Phase: intake\nWorkflows: not yet classified\n',
    'unknown-name.md': 'Workflows: Toaster Development; traits: none\n',
    'unknown-sub-type-key.md': 'Workflows: Host Extension Development → claude-code-extension; traits: none\n',
    'unknown-sub-type-name.md': 'Workflows: Host Extension Development → Claude Code extension; traits: none\n',
    'unknown-trait-key-not-case.md': 'Workflows: Web App Development; traits: has-screens\n',
    'unknown-trait-key.md': 'Workflows: Web App Development; traits: installable\n',
    'unknown-trait-then-flag.md': 'Workflows: Web App Development; traits: Glitter, Spends money\n',
    'unknown-trait.md': 'Workflows: Web App Development; traits: Glitter\n',
    'unknown-type-key.md': 'Workflows: web-app; traits: none\n',
    'unknown-type-name.md': 'Workflows: Web app; traits: none\n',
    'unknown-workflow-name-case.md': 'Workflows: web app development; traits: none\n',
}


def test_r014_every_status_case_holds_exactly_its_lines():
    assert sorted(STATUS_TEXT) == sorted(STATUS_EXACT), "a status fixture without its text, or a text without its case"
    for name, text in STATUS_TEXT.items():
        held = (REPO / FIX / "status" / name).read_bytes().decode("utf-8").replace("\r\n", "\n")
        assert held == text, name


# The bodies a stopped line would have shown failing: each, as a line of its own, gives findings, so a check that went
# on past the stop would print more than the one (form) line (stage B2's review, round 9: fixtures 4, blocking).
STOPPED = [
    ("form-bad-prefix-bodies-unchecked.md", ["Toaster Development; traits: Glitter", "Library Development; traits: none"]),
    ("form-bad-prefix-single-unknown.md", ["Toaster Development; traits: Glitter"]),
    ("form-bad-prefix-single-two-types.md", ["Library Development, Web App Development; traits: none"]),
    ("form-bad-prefix-single-unwritten.md", ["Library Development; traits: none"]),
]


@pytest.mark.parametrize("case, bodies", STOPPED, ids=[c for c, _ in STOPPED])
def test_r014_a_line_that_breaks_the_prefix_rule_is_not_checked_further(tmp_path, case, bodies):
    """handoff/TASK-006-r2.md R2-6 (and TASK-006.md Requirement 11): a line that fails the prefix rule "is not checked
    further (no `unknown`, `e` or `f` from it)". The precondition runs each body as a status line of its own, where it
    fails; the case then gives the prefix's (form) finding and nothing else (STATUS_EXACT)."""
    for body in bodies:
        alone = tmp_path / "alone.md"
        alone.write_text("Workflows: " + body + "\n", encoding="utf-8")
        rc, lines, err = run("--open-list", STATUS_LIST, "--status", str(alone))
        assert rc == 1 and [line for line in fails(lines) if not line.startswith("FAIL (form)")], (body, lines)
    rc, lines, err = status(case)
    assert {line.split(")")[0] for line in fails(lines)} == {"FAIL (form"}, lines
    assert all("breaks the part-prefix rule" in line for line in fails(lines)), lines


def test_r014_a_line_without_the_traits_marker_is_not_checked_further(tmp_path):
    """handoff/TASK-006.md Requirement 11: a line without `; traits: ` exactly once is not checked further. Its head,
    given the marker as a line of its own, fails; the case gives the marker's (form) finding alone (stage B2's review,
    round 10: fixtures 4, consider; the STOPPED treatment for the marker)."""
    alone = tmp_path / "alone.md"
    alone.write_text("Workflows: Toaster Development; traits: none\n", encoding="utf-8")
    rc, lines, err = run("--open-list", STATUS_LIST, "--status", str(alone))
    assert rc == 1 and [line for line in fails(lines) if not line.startswith("FAIL (form)")], lines
    rc, lines, err = status("form-no-traits-marker-unknown-head.md")
    assert [line.split(": ", 1)[1] for line in fails(lines)] == ["- - Workflows line must contain '; traits: ' exactly once"], lines


CLOSE_FD = "import os, subprocess, sys\nos.close(%d)\nsys.exit(subprocess.call([sys.executable] + sys.argv[1:]))\n"


@pytest.mark.parametrize("fd", [1, 2], ids=["stdout-closed", "stderr-closed"])
def test_r014_usage_error_with_a_closed_stream_exits_2_without_traceback(fd):
    """The usage text: a usage error is exit 2 and ends with `RESULT: not checked`, with no traceback, as a run with
    a standard stream closed already does for its findings (test_r014_closed_standard_output_gives_no_traceback).
    Started with standard output or standard error closed (Python then sets that stream to None), a bad argument
    must still exit 2: with standard error closed the RESULT line is the last line on standard output, and with
    standard output closed nothing but the usage error reaches standard error (stage B2's review, round 9: Review B;
    docs/debug/BUG-010.md). The precondition shows the child starts with the stream closed."""
    probe = "import sys; sys.%s.write(repr(sys.%s))" % (("stderr", "stdout") if fd == 1 else ("stdout", "stderr"))
    p = subprocess.run([sys.executable, "-c", CLOSE_FD % fd, "-c", probe], capture_output=True, text=True, encoding="utf-8")
    assert (p.returncode, (p.stderr if fd == 1 else p.stdout)) == (0, "None"), "precondition: the child starts with the stream closed"
    p = subprocess.run([sys.executable, "-c", CLOSE_FD % fd, PROG, "--no-such-option"], cwd=str(REPO),
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 2, (p.returncode, p.stdout, p.stderr)
    assert "Traceback" not in p.stdout + p.stderr, (p.stdout, p.stderr)
    # Each open stream whole, white space aside (argparse wraps the usage line at the terminal's width); with standard
    # error closed argparse prints the usage line on standard output, and the program writes nothing to the other
    # stream (BUG-010's gate: Review A, a consider).
    usage = "usage: workflow-check.py [-h] [--open-list FILE] [--registry FILE] [--status FILE] [ROOT ...]"
    if fd == 2:
        assert p.stdout.splitlines()[-1] == "RESULT: not checked", p.stdout
        assert " ".join(p.stdout.split()) == usage + " RESULT: not checked", p.stdout
    else:
        assert p.stderr.splitlines()[-1] == "workflow-check.py: error: unrecognized arguments: --no-such-option", p.stderr
        assert " ".join(p.stderr.split()) == usage + " workflow-check.py: error: unrecognized arguments: --no-such-option", p.stderr


def test_r014_every_root_that_is_no_folder_is_reported(tmp_path):
    """The program's usage text and R4: each argument that cannot be checked is an ERROR line, then `RESULT: not
    checked`; a second root that is no folder is reported after the first (stage B2's review, round 9: tests, a
    consider; `continue` made `break` survived)."""
    first, second = tmp_path / "absent-1", tmp_path / "absent-2"
    rc, lines, err = run(str(first), str(second))
    shown = str(tmp_path).replace("\\", "/")
    assert lines == [f"ERROR: {shown}/absent-1: not a folder", f"ERROR: {shown}/absent-2: not a folder", "RESULT: not checked"], lines
    assert rc == 2 and err == "", err


def test_r014_every_status_file_that_cannot_be_read_is_reported(tmp_path):
    """As above, for two status files that do not exist (stage B2's review, round 9: tests, a consider)."""
    rc, lines, err = run("--open-list", STATUS_LIST, "--status", str(tmp_path / "no-1.md"), "--status", str(tmp_path / "no-2.md"))
    shown = str(tmp_path).replace("\\", "/")
    assert lines == [f"ERROR: {shown}/no-1.md: does not exist", f"ERROR: {shown}/no-2.md: does not exist", "RESULT: not checked"], lines
    assert rc == 2 and err == "", err


# --- stage B2's review, round 9: the control-flow sweep's separable survivors (BUG-010) ---------------------------
# run/supervisor/sweep_flow.py made every `continue` a `break` or a `pass`, every bare `return` a `pass`, every two
# neighbouring statements swapped, every `for` loop reversed and every member of a module constant dropped. Each
# survivor an input separates in a fixed order has a case here; the output is pinned as the program gives it, its
# order included, so a change of the order is a change of these tests. Where a document fixes the order the test cites
# it; where none does, the test says so. The rest are recorded by class in docs/HARDENING.md, "the stage review (round
# 9)". The line numbers are those of the sweep's first run, on main's program (run/supervisor/sweep_flow_r1.out); BUG-010's
# fix moved each line after 756 down by two (run/supervisor/sweep_flow_r4.out).

def test_r014_a_final_line_feed_adds_no_empty_line(program):
    """file_lines' docstring: "A final line feed does not add an empty line." (the sweep's line 105, the return moved
    above the deletion of the last empty line)."""
    mod = program("workflow-check")
    assert mod.file_lines("a\nb\n") == ["a", "b"]
    assert mod.file_lines("a\nb") == ["a", "b"]
    assert mod.file_lines("\n") == [""]
    assert mod.file_lines("") == []


def _open_list_with(tmp_path, old, new):
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    assert text.count(old) == 1, "precondition: the text to replace is in the fixture once"
    broken = tmp_path / "open-list.md"
    broken.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    return broken, str(broken).replace("\\", "/")


PRODUCT_HEADER = "| Key | Name | Definition | Workflow name | Default traits | Written | Planned |\n|---|---|---|---|---|---|---|\n"


def test_r014_a_table_without_its_separator_is_reported_before_its_columns(tmp_path):
    """A table with no separator row and a missing column is reported for the separator (the sweep's line 227, the
    column test moved above the separator test). Each is a table that cannot be read (handoff/TASK-006.md R3-2 and
    Requirement 3); which of the two is named is the program's choice, which no document fixes."""
    broken, shown = _open_list_with(tmp_path, PRODUCT_HEADER,
                                    "| Key | Name | Definition | Workflow name | Default traits | Done | Planned |\n")
    rc, lines, err = run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md")
    assert lines == [f"ERROR: {shown}: table after ## Product types has no separator row", "RESULT: not checked"], lines
    assert rc == 2 and err == "", err


def test_r014_the_first_missing_column_is_reported(tmp_path):
    """Two required columns missing: the first, in the order the program requires them (the sweep's line 227, the
    columns walked in reverse). That a missing column stops the check is handoff/TASK-006.md Requirement 3's; which of
    two is named, no document fixes."""
    broken, shown = _open_list_with(tmp_path, PRODUCT_HEADER, PRODUCT_HEADER.replace("| Key |", "| Id |").replace("| Written |", "| Done |"))
    rc, lines, err = run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md")
    assert lines == [f"ERROR: {shown}: missing column Key", "RESULT: not checked"], lines
    assert rc == 2 and err == "", err


def test_r014_the_first_row_of_a_name_is_the_one_read(tmp_path):
    """A workflow name given twice in the open list is read from its first row (the sweep's line 241, the rows walked
    in reverse): the second, unwritten, row is not the one judged. Such an open list breaks its own rule (open-list.md:
    the Workflow names are unique), and no document says which row wins; the test pins the program's choice, index_first's,
    so a change of it is seen."""
    row = "| library | Library | Included by other programs | Library Development | — | no | — |\n"
    broken, shown = _open_list_with(tmp_path, row, row + "| web-app-2 | Web app again | A second row | Web App Development | — | no | — |\n")
    status = tmp_path / "status.md"
    status.write_text("Workflows: Web App Development; traits: none\n", encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", str(broken), "--status", str(status))
    assert lines == ["RESULT: OK"], lines
    assert rc == 0 and err == "", err


def test_r014_a_traits_place_is_its_first_rows(tmp_path):
    """A trait name given twice keeps the place of its first row in the open list's order (the sweep's line 279, the
    rows walked in reverse): Has screens, then Installable, is in order. Such an open list breaks its own rule (open-
    list.md: the traits' Names are unique), and no document says which row's place counts; the test pins the program's choice."""
    last = "| spends-money | Spends money | Its actions cost money | no | — |\n"
    broken, shown = _open_list_with(tmp_path, last, last + "| has-screens-2 | Has screens | A second row | yes | — |\n")
    status = tmp_path / "status.md"
    status.write_text("Workflows: Web App Development; traits: Has screens, Installable\n", encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", str(broken), "--status", str(status))
    assert lines == ["RESULT: OK"], lines
    assert rc == 0 and err == "", err


def test_r014_both_layers_that_cannot_be_examined_are_reported_in_order(tmp_path, monkeypatch, capsys, program):
    """R5-1 (handoff/TASK-006-r5.md): each layer that cannot be examined is an ERROR line, so with both layers in that
    state both are reported (the sweep's line 313, the `continue` after the error made `break`). Their order, types then
    traits, is the program's (line 303, the layers walked in reverse); no document fixes it."""
    mod = program("workflow-check")
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "traits").mkdir()
    real = os.lstat

    def lstat(path, *a, **k):
        if os.path.basename(os.fspath(path)) in ("types", "traits"):
            raise PermissionError(13, "Permission denied", os.fspath(path))
        return real(path, *a, **k)

    monkeypatch.setattr(os, "lstat", lstat)
    code, lines = _main_in_process(mod, str(root), capsys=capsys)
    shown = str(root).replace("\\", "/")
    assert [line.replace("\\", "/") for line in lines] == [
        f"ERROR: {shown}/types: Permission denied", f"ERROR: {shown}/traits: Permission denied", "RESULT: not checked"], lines
    assert code == 2


def test_r014_a_folder_that_cannot_be_listed_is_reported_before_a_file_that_cannot_be_read(tmp_path, monkeypatch, capsys, program):
    """A root's listing errors come before its files' read errors (the sweep's line 800, the files read before the
    listing errors were kept). Both stop the check with an ERROR line (handoff/TASK-006.md Requirement 3, and
    TASK-006-r2.md R2-3 for the folder); their order is the program's, which no document fixes."""
    mod = program("workflow-check")
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "traits").mkdir()
    (root / "types" / "host-extension.md").write_bytes(b"## Add at intake.questions\n\n\xff\n")
    real = os.walk

    def walk(top, *a, onerror=None, **k):
        if os.path.basename(os.fspath(top)) == "types" and onerror is not None:
            onerror(PermissionError(13, "Permission denied", os.path.join(os.fspath(top), "locked")))
        return real(top, *a, onerror=onerror, **k)

    monkeypatch.setattr(os, "walk", walk)
    code, lines = _main_in_process(mod, str(root), capsys=capsys)
    shown = str(root).replace("\\", "/")
    assert [line.replace("\\", "/") for line in lines] == [
        f"ERROR: {shown}/types/locked: Permission denied",
        f"ERROR: {shown}/types/host-extension.md: cannot be read as UTF-8",
        "RESULT: not checked"], lines
    assert code == 2


def _one_file_root(tmp_path, rel, text):
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "traits").mkdir()
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return root, str(root).replace("\\", "/") + "/" + rel


# (the file, its text, the sweep's survivor it separates, the findings in order).
FLOW_FILE_CASES = {
    "fence-open-first": ("types/host-extension.md", "## Add at nowhere.at-all\n\nq\n\n```\n",
                         "line 500: the file's open fence reported after its headings",
                         ["FAIL (form) {f}: - - fenced code block is still open at the end of the file",
                          "FAIL (a) {f}: nowhere.at-all - point is not in the extension-point registry"]),
    "trait-set-empty": ("traits/has-screens.md", "## Set at intake.delivery-kind\n",
                        "line 516: the trait rule tested before the section's own rules",
                        ["FAIL (form) {f}: intake.delivery-kind - Set at section has no non-blank line",
                         "FAIL (b) {f}: intake.delivery-kind - a trait file may only add",
                         "FAIL (kind) {f}: - - Set at intake.delivery-kind is not one delivery kind"]),
    "kind-at-unknown-point": ("types/host-extension.md", "## Add at nowhere.at-all for installer\n\nq\n",
                              "line 524: the delivery kind tested before the point",
                              ["FAIL (a) {f}: nowhere.at-all - point is not in the extension-point registry",
                               "FAIL (kind) {f}: installer - delivery kind is named on a point other than project-end.delivery"]),
    "sub-two-identity-findings": ("types/host-extension/not-a-sub.md", "## Add at intake.questions\n\nq\n",
                                  "line 571: a sub-workflow's identity findings reversed",
                                  ["FAIL (d) {f}: not-a-sub - type workflow types/host-extension.md does not exist",
                                   "FAIL (d) {f}: not-a-sub - not a sub-type of host-extension"]),
}


@pytest.mark.parametrize("case", sorted(FLOW_FILE_CASES))
def test_r014_a_files_findings_come_in_their_order(tmp_path, case):
    """A file's findings, in the order the program gives them (stage B2's review, round 9: the control-flow sweep). Each
    finding is its rule's (bridge/cursor-bridge/workflow/extension-points.md, "How a conditional workflow names a
    point"); the order of two findings of one file, no document fixes."""
    rel, text, survivor, expected = FLOW_FILE_CASES[case]
    root, shown = _one_file_root(tmp_path, rel, text)
    rc, lines, err = run(str(root))
    assert lines == whole_output([line.format(f=shown) for line in expected]), (survivor, lines)
    assert rc == 1 and err == "", err


# (the status line, the sweep's survivor it separates, the findings in order).
FLOW_STATUS_CASES = {
    "two-unknown-segments": ("Workflows: Glitter → Toaster; traits: none",
                             "line 608: the head's segments walked in reverse",
                             ["FAIL (unknown) {f}: Glitter - name is not in the open list",
                              "FAIL (unknown) {f}: Toaster - name is not in the open list",
                              "FAIL (e) {f}: - - part must name exactly one product type"]),
    "no-type-two-subs": ("Workflows: Claude Code Extension, Browser Extension; traits: none",
                         "line 621: the sub-type count tested before the type count",
                         ["FAIL (e) {f}: - - part must name exactly one product type",
                          "FAIL (e) {f}: - - part must name at most one sub-type"]),
    "shape-then-unwritten": ("Workflows: Library Development, Installable; traits: none",
                             "line 638: the written test moved above the shape test",
                             ["FAIL (form) {f}: - - Workflows head is not the product type, then at most its sub-type",
                              "FAIL (f) {f}: Library Development - product type is not written"]),
}


@pytest.mark.parametrize("case", sorted(FLOW_STATUS_CASES))
def test_r014_a_status_lines_findings_come_in_their_order(tmp_path, case):
    """A status line's findings, in the order handoff/TASK-006.md Requirement 11 checks a line: the head's names in
    turn (unknown), then the counts (e), then the shape (form), then the written test (f); the two count findings'
    order, the product type's first, is the program's (stage B2's review, round 9: the control-flow sweep's lines 608,
    621 and 638)."""
    line, survivor, expected = FLOW_STATUS_CASES[case]
    status = tmp_path / "status.md"
    status.write_text(line + "\n", encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", STATUS_LIST, "--status", str(status))
    shown = str(status).replace("\\", "/")
    assert lines == whole_output([item.format(f=shown) for item in expected]), (survivor, lines)
    assert rc == 1 and err == "", err


def test_r014_the_usage_line_names_the_options_in_their_order():
    """The usage line argparse prints, white space aside (the sweep's lines 768 and 769, two options declared in the
    other order). That a usage error prints the usage and RESULT: not checked is the program's usage text's; the order
    of the options in the line, no document fixes."""
    rc, lines, err = run("--no-such-option")
    assert " ".join(err.split()) == ("usage: workflow-check.py [-h] [--open-list FILE] [--registry FILE] [--status FILE] "
                                     "[ROOT ...] workflow-check.py: error: unrecognized arguments: --no-such-option"), err
    assert rc == 2 and lines == ["RESULT: not checked"], lines


def test_r014_a_root_that_is_no_folder_is_reported_when_the_rules_cannot_be_read(tmp_path):
    """Every argument that cannot be checked is an ERROR line, the rules' first (the program's usage text and R4): with
    the open list unreadable, a root that is no folder after one that is still reported (the sweep's line 796, the
    rules test moved above the folder test, and line 797, the `continue` after it made `break`)."""
    absent = tmp_path / "absent.md"
    rc, lines, err = run("--open-list", str(absent), f"{FIX}/pass", str(tmp_path / "absent-root"))
    shown = str(tmp_path).replace("\\", "/")
    assert lines == [f"ERROR: {shown}/absent.md: does not exist", f"ERROR: {shown}/absent-root: not a folder", "RESULT: not checked"], lines
    assert rc == 2 and err == "", err


def test_r014_a_reason_that_holds_a_key_is_escaped(tmp_path):
    """A finding's reason is escaped like its path and its name (the usage text; round 2: Review B): a sub-workflow's
    reasons name its type key, which the open list gives. A key is lowercase letters, digits and hyphens by the open
    list's own rule (open-list.md), so this key breaks it; the escaping is the defence for an open list that does (stage
    B2's review, round 9: the control-flow sweep's line 740, the line printed before its reason was escaped)."""
    key = "libräry"
    broken, _ = _open_list_with(tmp_path, "| library | Library |", "| %s | Library |" % key)
    root = tmp_path / "root"
    (root / "types" / key).mkdir(parents=True)
    (root / "traits").mkdir()
    (root / "types" / key / "x.md").write_text("## Add at intake.questions\n\nq\n", encoding="utf-8", newline="\n")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, PROG, "--open-list", str(broken), str(root)], cwd=str(REPO), capture_output=True,
                       text=True, encoding="utf-8", env=env)
    f = str(root).replace("\\", "/") + "/types/libr\\xe4ry/x.md"
    assert p.stdout.splitlines() == whole_output([
        f"FAIL (d) {f}: x - type workflow types/libr\\xe4ry.md does not exist",
        f"FAIL (d) {f}: x - not a sub-type of libr\\xe4ry"]), p.stdout
    assert p.returncode == 1 and p.stderr == "", p.stderr


# --- stage B2's review, round 10: the idiom sweep's separable survivors (BUG-011) ----------------------------------
# run/supervisor/sweep_idiom.py made every `for` loop walk its items with repeats dropped, every `len(x)` count x's
# distinct items, every list assigned in a function lose its repeats, every operand of an `and` or an `or` dropped, and
# every `all` an `any` and back: rules rewritten in another idiom, which no earlier sweep tried (round 10: tests, a
# status file's lines deduplicated). Each survivor an input separates has a case here or in STATUS_EXACT; the rest are
# recorded by class in docs/HARDENING.md, "the stage review (round 10)".

def test_r014_each_line_of_a_repeated_pair_is_valid_alone(tmp_path):
    """The precondition of e-same-part-identical and form-prefix-missing-identical: each pair's line, alone, gives the
    output a check that dropped repeats would print (RESULT: OK unprefixed; the single-line prefix finding prefixed), so
    the pair's findings are the repeat's (handoff/TASK-006.md Requirements 11 and 12: each line is checked)."""
    for name, alone in (("form-prefix-missing-identical.md", ["RESULT: OK"]),
                        ("e-same-part-identical.md", None)):
        text = (REPO / FIX / "status" / name).read_text(encoding="utf-8")
        first, second = text.splitlines()
        assert first == second, name
        one = tmp_path / name
        one.write_text(first + "\n", encoding="utf-8", newline="\n")
        rc, lines, err = run("--open-list", STATUS_LIST, "--status", str(one))
        if alone is None:
            shown = str(one).replace("\\", "/")
            alone = [f"FAIL (form) {shown}: app - Workflows line breaks the part-prefix rule", "RESULT: 1 problem(s)"]
        assert lines == alone, (name, lines)
    text = (REPO / FIX / "status" / "e-type-named-twice.md").read_text(encoding="utf-8")
    assert text == "Workflows: Web App Development, Web App Development; traits: none\n"
    one = tmp_path / "once.md"
    one.write_text("Workflows: Web App Development; traits: none\n", encoding="utf-8", newline="\n")
    assert run("--open-list", STATUS_LIST, "--status", str(one))[1] == ["RESULT: OK"]
    text = (REPO / FIX / "status" / "e-sub-type-named-twice.md").read_text(encoding="utf-8")
    assert text == "Workflows: Host Extension Development \u2192 Claude Code Extension, Claude Code Extension; traits: none\n"
    one.write_text("Workflows: Host Extension Development \u2192 Claude Code Extension; traits: none\n", encoding="utf-8", newline="\n")
    assert run("--open-list", STATUS_LIST, "--status", str(one))[1] == ["RESULT: OK"]


# (the status line, the sweep's survivor it separates, the findings).
IDIOM_STATUS_CASES = {
    "type-in-two-segments": ("Workflows: Web App Development → Web App Development; traits: none",
                             "line 604: the head's segments with repeats dropped",
                             ["FAIL (e) {f}: - - part must name exactly one product type"]),
    # The program judges the Of type relation only where the line names exactly one product type and one sub-type, so a
    # name given twice leaves it unjudged. Read literally, handoff/TASK-006.md Requirement 4 asks it of any sub-type the
    # line names whose Of type is not the line's product type, and "Print each" asks for that finding beside the count's:
    # these two cases pin the program's output, and the gap is a lead for the next change of workflow-check.py
    # (docs/HARDENING.md, "BUG-011's gate round 1"; the sweep's line 624, either count taken with repeats dropped).
    "type-twice-sub-of-another": ("Workflows: Web App Development, Web App Development → Claude Code Extension; traits: none",
                                  "line 624: the product types counted with repeats dropped",
                                  ["FAIL (e) {f}: - - part must name exactly one product type"]),
    "sub-twice-of-another": ("Workflows: Web App Development → Claude Code Extension, Claude Code Extension; traits: none",
                             "line 624: the sub-types counted with repeats dropped",
                             ["FAIL (e) {f}: - - part must name at most one sub-type"]),
}


@pytest.mark.parametrize("case", sorted(IDIOM_STATUS_CASES))
def test_r014_a_repeated_name_is_counted_each_time(tmp_path, case):
    """handoff/TASK-006.md Requirement 11, step 4: the names that are Workflow names count as product types, each
    one it is given; a product type named in two segments is two (stage B2's review, round 10: the idiom sweep)."""
    line, survivor, expected = IDIOM_STATUS_CASES[case]
    status = tmp_path / "status.md"
    status.write_text(line + "\n", encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", STATUS_LIST, "--status", str(status))
    shown = str(status).replace("\\", "/")
    assert lines == whole_output([item.format(f=shown) for item in expected]), (survivor, lines)
    assert rc == 1 and err == "", err




# (the files of a root, the sweep's survivors they separate, the findings in order; {r} is the root).
IDIOM_ROOT_CASES = {
    # A folder named `types` inside types/ is a type folder that is no product type: reported once, its file unread
    # (extension-points.md:72); with its path's repeats dropped it was no type folder, or its file a type workflow.
    "type-folder-named-types": ({"types/types/x.md": "## Add at nowhere.at-all\n\nq\n"},
                                "lines 341, 342, 346, 347 and 350: the path's parts with repeats dropped, or counted so",
                                ["FAIL (d) {r}/types/types: types - type folder is not a product type"]),
    # A folder named `traits` inside traits/ is a folder under traits/, and its file no trait file (extension-points.md:72).
    "trait-folder-named-traits": ({"traits/traits/x.md": "## Add at nowhere.at-all\n\nq\n"},
                                  "line 357: the folder's parts counted with repeats dropped",
                                  ["FAIL (form) {r}/traits/traits: traits - path is not a conditional-workflow file",
                                   "FAIL (form) {r}/traits/traits/x.md: x.md - path is not a conditional-workflow file"]),
    # A folder under traits/ named like an unknown type folder is still a folder under traits/, and its file is read as
    # one (extension-points.md:72; the sweep's line 347 without `parts[0] == "types"`, which took it for the type folder).
    "trait-folder-named-like-a-type-folder": ({"types/foo/x.md": "## Add at nowhere.at-all\n\nq\n",
                                               "traits/foo/y.md": "## Add at nowhere.at-all\n\nq\n"},
                                              "line 347: the unknown-type-folder test without its layer",
                                              ["FAIL (form) {r}/traits/foo: foo - path is not a conditional-workflow file",
                                               "FAIL (form) {r}/traits/foo/y.md: y.md - path is not a conditional-workflow file",
                                               "FAIL (d) {r}/types/foo: foo - type folder is not a product type"]),
    # A folder inside a type's folder is (form) whatever its name, `types` too (extension-points.md:72; BUG-011's gate
    # round 1: Review A, the sweep's second `len` of line 357, which counted the path's parts without repeats and so
    # dropped the folder); its file is no conditional workflow either.
    "folder-named-types-in-a-type-folder": ({"types/host-extension.md": "## Add at intake.questions\n\nq\n",
                                             "types/host-extension/types/f.md": "## Add at intake.questions\n\nq\n"},
                                            "line 357: a folder under a type's folder counted with repeats dropped",
                                            ["FAIL (form) {r}/types/host-extension/types: types - path is not a conditional-workflow file",
                                             "FAIL (form) {r}/types/host-extension/types/f.md: f.md - path is not a conditional-workflow file"]),
    # A folder named like a file inside a type's folder, and one under traits/, is a folder, and the file inside it,
    # named like its folder, is at no key's path (extension-points.md:72; BUG-011's gate round 1: Review A, lines 362
    # and 364 counting the path's parts without repeats, which read it as a sub-workflow and as a trait).
    "folder-named-like-a-sub-workflow": ({"types/host-extension.md": "## Add at intake.questions\n\nq\n",
                                          "types/host-extension/x.md/x.md": "## Add at intake.questions\n\nq\n"},
                                         "line 362: a three-part path counted with repeats dropped",
                                         ["FAIL (form) {r}/types/host-extension/x.md: x.md - path is not a conditional-workflow file",
                                          "FAIL (form) {r}/types/host-extension/x.md/x.md: x.md - path is not a conditional-workflow file"]),
    "folder-named-like-a-trait": ({"traits/installable.md/installable.md": "## Add at intake.questions\n\nq\n"},
                                  "line 364: a traits path counted with repeats dropped",
                                  ["FAIL (form) {r}/traits/installable.md: installable.md - path is not a conditional-workflow file",
                                   "FAIL (form) {r}/traits/installable.md/installable.md: installable.md - path is not a conditional-workflow file"]),
    # A Set at project-end.delivery is no addition there, so it owes no delivery kind: its one finding is the point's
    # (extension-points.md:68, the `for <kind>` form is an addition's; the sweep's line 524 without `kind == "add"`).
    "set-at-delivery": ({"types/host-extension.md": "## Set at project-end.delivery\n\nx\n"},
                        "line 524: the delivery-kind rule applied to a Set",
                        ["FAIL (set) {r}/types/host-extension.md: project-end.delivery - point does not accept set"]),
}


@pytest.mark.parametrize("case", sorted(IDIOM_ROOT_CASES))
def test_r014_a_paths_repeated_parts_are_read_as_given(tmp_path, case):
    """A root's findings where a path repeats a name, or a Set stands at the delivery point (stage B2's review, round
    10: the idiom sweep)."""
    files, survivor, expected = IDIOM_ROOT_CASES[case]
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "traits").mkdir()
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    rc, lines, err = run(str(root))
    shown = str(root).replace("\\", "/")
    assert lines == whole_output([item.format(r=shown) for item in expected]), (survivor, lines)
    assert rc == 1 and err == "", err


@pytest.mark.parametrize("heading", ["## at at", "## at at the gate"])
def test_r014_a_heading_of_at_at_is_a_change_heading(tmp_path, heading):
    """extension-points.md:72: a heading whose second word is `at` fails as a malformed change heading; `## at at`, two
    words alike, is one (the idiom sweep's line 390, the words counted with repeats dropped), and so is `## at at the
    gate` (line 382, the words with repeats dropped, which makes the second word `the`)."""
    root, shown = _one_file_root(tmp_path, "types/host-extension.md", heading + "\n\nq\n")
    rc, lines, err = run(str(root))
    assert lines == whole_output([f"FAIL (form) {shown}: - - change heading is not one of the four forms"]), lines
    assert rc == 1 and err == "", err


def test_r014_a_table_whose_header_repeats_a_column_is_read(tmp_path):
    """A table whose header names a column twice, each row with as many cells: the separator and the rows are counted
    against every header cell (the idiom sweep's lines 225 and 233, the header counted with repeats dropped). Such an
    open list breaks its own column list (open-list.md), and no document says it must stop the check; the test pins the
    program's choice, which reads it."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    head = "| Key | Name | Definition | Written | Planned |\n|---|---|---|---|---|\n"
    assert text.count(head) == 1
    start = text.index(head)
    rows = text[start + len(head):].split("\n")
    body = []
    for row in rows:
        if not row.startswith("|"):
            break
        body.append(row + " — |")
    assert len(body) == 3, "precondition: the three traits rows"
    new = "| Key | Name | Definition | Written | Planned | Planned |\n|---|---|---|---|---|---|\n" + "\n".join(body) + "\n"
    broken = tmp_path / "open-list.md"
    old = head + "\n".join(rows[:3]) + "\n"
    assert text.count(old) == 1
    broken.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md")
    assert lines == ["RESULT: OK"], lines
    assert rc == 0 and err == "", err


def test_r014_an_error_without_its_reason_still_names_one(tmp_path, monkeypatch, capsys, program):
    """Every argument that cannot be checked is an ERROR line with a reason (handoff/TASK-006.md Requirement 3): where
    the system's error carries no reason text or no file name, the program's own words stand in (the idiom sweep's
    lines 299, 300 and 312, each `or` without its fallback; line 126 below)."""
    mod = program("workflow-check")
    root = tmp_path / "root"
    (root / "types").mkdir(parents=True)
    (root / "traits").mkdir()
    shown = str(root).replace("\\", "/")
    real_lstat, real_walk = os.lstat, os.walk

    def lstat(path, *a, **k):
        if os.path.basename(os.fspath(path)) == "traits":
            raise OSError()
        return real_lstat(path, *a, **k)

    def walk(top, *a, onerror=None, **k):
        if os.path.basename(os.fspath(top)) == "types" and onerror is not None:
            onerror(OSError())
        return real_walk(top, *a, onerror=onerror, **k)

    monkeypatch.setattr(os, "lstat", lstat)
    monkeypatch.setattr(os, "walk", walk)
    code, lines = _main_in_process(mod, str(root), capsys=capsys)
    assert [line.replace("\\", "/") for line in lines] == [
        f"ERROR: {shown}: cannot be listed", f"ERROR: {shown}/traits: cannot be examined", "RESULT: not checked"], lines
    assert code == 2


def test_r014_a_read_error_without_its_reason_names_the_error(tmp_path, monkeypatch, program):
    """read_utf8: a file that cannot be read names the system's reason, or the error itself where it has none (the
    idiom sweep's line 126, the `or` without its fallback)."""
    mod = program("workflow-check")
    path = tmp_path / "open-list.md"
    path.write_text("x\n", encoding="utf-8")

    def fake_open(*a, **k):
        raise OSError("odd failure")

    monkeypatch.setattr(mod, "open", fake_open, raising=False)
    text, shown, reason = mod.read_utf8(str(path))
    assert text is None and reason == "cannot be read (odd failure)", reason


def _product_table(text):
    """The Product types table of an open list's text: its lines, from the header to the last row."""
    lines = text.split("\n")
    start = lines.index("## Product types")
    first = next(k for k in range(start + 1, len(lines)) if lines[k].startswith("|"))
    end = next(k for k in range(first, len(lines)) if not lines[k].startswith("|"))
    return "\n".join(lines[first:end]) + "\n"


def test_r014_a_table_of_two_separator_lines_is_read_for_its_columns(tmp_path):
    """A table of two identical separator lines: the first is read as the header, whose cells are dashes, so the
    table has its separator and lacks its columns (BUG-011's gate round 1: Review A, the sweep's line 222, the table's
    lines counted with repeats dropped, which names the separator instead). Each is a table that cannot be read
    (handoff/TASK-006.md Requirement 3); which reason is named, no document fixes: the test pins the program's."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    table = _product_table(text)
    sep = "|---|---|---|---|---|---|---|"
    broken, shown = _open_list_with(tmp_path, table, sep + "\n" + sep + "\n")
    rc, lines, err = run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md")
    assert lines == [f"ERROR: {shown}: missing column Key", "RESULT: not checked"], lines
    assert rc == 2 and err == "", err


def test_r014_a_row_like_the_separator_is_a_row(tmp_path):
    """A product type row that repeats the separator line is read as a row (BUG-011's gate round 1: Review A, the
    sweep's line 218, the table's lines with repeats dropped, which drops it): its Workflow name is `---` and its
    Written `---`, so a line naming it gives (f). Such an open list breaks its own rules (open-list.md), and no
    document says what such a row is; the test pins the program's reading."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    table = _product_table(text)
    sep = "|---|---|---|---|---|---|---|"
    assert table.split("\n")[1] == sep, "precondition: the separator line"
    broken, shown = _open_list_with(tmp_path, table, table + sep + "\n")
    status = tmp_path / "status.md"
    status.write_text("Workflows: ---; traits: none\n", encoding="utf-8", newline="\n")
    rc, lines, err = run("--open-list", str(broken), "--status", str(status))
    s = str(status).replace("\\", "/")
    assert lines == [f"FAIL (f) {s}: --- - product type is not written", "RESULT: 1 problem(s)"], lines
    assert rc == 1 and err == "", err


def test_r014_two_tables_without_a_column_are_two_error_lines(tmp_path):
    """Each table that cannot be read is an ERROR line (handoff/TASK-006.md Requirement 3: "one or more lines"), two
    identical ones too: the Product types and Sub-types tables both without Key (BUG-011's gate round 1: Review A, the
    sweep's line 820, the errors printed with repeats dropped). The count of identical lines, no document fixes beyond
    one per table; the test pins the program's."""
    text = (REPO / STATUS_LIST).read_text(encoding="utf-8")
    assert text.count("\n| Key | Name |") == 3, "precondition: three tables whose first column is Key"
    broken = tmp_path / "open-list.md"
    broken.write_text(text.replace("\n| Key | Name |", "\n| Id | Name |", 2), encoding="utf-8", newline="\n")
    shown = str(broken).replace("\\", "/")
    rc, lines, err = run("--open-list", str(broken), "--status", f"{FIX}/status/ok-single.md")
    assert lines == [f"ERROR: {shown}: missing column Key"] * 2 + ["RESULT: not checked"], lines
    assert rc == 2 and err == "", err
