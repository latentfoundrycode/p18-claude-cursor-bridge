"""Release S: the text form of evidence in completion-check.py.

A requirement an instruction text satisfies names where the text stands and the pull request that merged it, `text: <file>.md ::
<heading> (#<n>)`. The form exists only in a project whose project.json declares where its instruction texts are
(`instruction_texts`); the program then verifies each part: the file stands under a declared folder, it holds the heading outside
a code block, the pull request's squash is on origin/main and changed that file (a failure on merged work, a note on a branch of
unmerged work). For a row whose sentence names a program a text entry never counts. Scratch repositories with a bare repository
as `origin`.

Review A, round 1 (both reviewers): the first form asked only for a file, a heading and any merged number, so a product row with
no test passed done mode on `text: README.md :: Install (#1)`; `test_a_product_row_cannot_be_proved_by_a_text` is that case."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "completion-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")

HEAD = "| ID | Requirement | Source | Status | Evidence |\n|---|---|---|---|---|\n"
TEXT = ("# The guide\n\n## The pause before planning\n\nThe supervisor pauses.\n\n### A closed heading ###\n\nMore.\n\n"
        "```markdown\n## A heading in a code block\n```\n\n~~~\n## Another in a tilde block\n~~~\n")
PAUSE = "| R-001 | the supervisor pauses before planning | owner | built | text: guide/loop.md :: The pause before planning (#%d) |\n"


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout


def make(tmp_path, rows, subjects=("the guide's pause (R-001) (#7)",), texts=("guide/",)):
    """A Workspace whose main is pushed to a bare origin: the first subject's commit holds every file, the others are empty,
    as squash commits stand on main. `texts` is project.json's `instruction_texts`; None writes a project file without it."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "guide").mkdir()
    (r / "guide" / "loop.md").write_text(TEXT, encoding="utf-8")
    (r / "README.md").write_text("# The product\n\n## Install\n\nRun the installer.\n", encoding="utf-8")
    (r / "docs" / "REQUIREMENTS.md").write_text(HEAD + rows, encoding="utf-8")
    project = {"name": "t", "kind": "private"}
    if texts is not None:
        project["instruction_texts"] = list(texts)
    (r / "project.json").write_text(json.dumps(project), encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "remote", "add", "origin", str(origin))
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", subjects[0])
    for subject in subjects[1:]:
        git(r, "commit", "-q", "--allow-empty", "-m", subject)
    git(r, "push", "-q", "origin", "main")
    git(r, "fetch", "-q", "origin")
    return r


def run(repo, mode="done"):
    p = subprocess.run([sys.executable, PROG, "--mode", mode], cwd=str(repo), capture_output=True, text=True, env=ENV)
    return p.returncode, p.stdout + p.stderr


def no_evidence(out):
    return [line for line in out.splitlines() if line.startswith("NO EVIDENCE")]


def test_a_text_entry_whose_file_heading_and_merge_hold_is_evidence_in_both_modes(tmp_path):
    """No test names R-001 anywhere, and the row passes plan and done mode on its text entry alone; a heading closed with
    hashes is read as its words."""
    r = make(tmp_path, PAUSE % 7 + "| R-002 | a closed heading is found | owner | built | text: `guide/loop.md` :: A closed heading (#7) |\n")
    for mode in ("plan", "done"):
        rc, out = run(r, mode)
        assert rc == 0 and not no_evidence(out) and "RESULT: OK" in out, out


def test_a_product_row_cannot_be_proved_by_a_text(tmp_path):
    """The reviewers' case: a project that declares no instruction texts takes no text entry at all, in either mode."""
    r = make(tmp_path, "| R-001 | the user exports their rows as a CSV file | owner | built | text: README.md :: Install (#7) |\n", texts=None)
    for mode in ("plan", "done"):
        rc, out = run(r, mode)
        lines = no_evidence(out)
        assert rc == 1 and lines and "R-001 carries a text entry, and this project declares no instruction texts" in lines[0], out


def test_only_a_file_under_a_declared_folder_counts_and_a_record_folder_is_never_one(tmp_path):
    """The guide is declared, the README is not; a declaration that names a record folder, the Workspace itself or a
    folder outside it declares nothing."""
    r = make(tmp_path, "| R-001 | the product is installed by its installer | owner | built | text: README.md :: Install (#7) |\n")
    rc, out = run(r, "plan")
    assert rc == 1 and "R-001 names the text README.md, which is under none of this project's instruction texts (guide/)" in out, out
    for n, declared in enumerate((["docs/"], ["docs/guides"], ["handoff/"], ["run/"], ["."], ["./"], [""], ["../ws/guide"], ["C:/x"], [7], "guide/")):
        (tmp_path / ("d%d" % n)).mkdir()
        r = make(tmp_path / ("d%d" % n), "| R-001 | the register is kept | owner | built | text: docs/REQUIREMENTS.md :: x (#7) |\n", texts=None)
        (r / "project.json").write_text(json.dumps({"instruction_texts": declared}), encoding="utf-8")
        rc, out = run(r, "plan")
        assert rc == 1 and "this project declares no instruction texts" in out, (declared, out)


def test_a_missing_file_a_missing_heading_and_a_path_outside_each_fail(tmp_path):
    r = make(tmp_path, "| R-001 | a | owner | built | text: guide/gone.md :: The pause before planning (#7) |\n"
                       "| R-002 | b | owner | built | text: guide/loop.md :: The pause before plannin (#7) |\n"
                       "| R-003 | c | owner | built | text: ../ws/guide/loop.md :: The pause before planning (#7) |\n"
                       "| R-004 | d | owner | built | text: guide/loop.md :: The pause before planning (#7); text: guide/loop.md :: No such heading (#7) |\n"
                       "| R-005 | e | owner | built | text: C:guide/loop.md :: The pause before planning (#7) |\n")
    rc, out = run(r, "plan")
    lines = no_evidence(out)
    assert rc == 1 and len(lines) == 5, out
    assert "R-001 names the text guide/gone.md, which is no file of this Workspace" in lines[0]
    assert "R-002 names the heading 'The pause before plannin', which guide/loop.md does not hold" in lines[1]
    assert "R-003 names the text ../ws/guide/loop.md" in lines[2]
    assert "R-004 names the heading 'No such heading'" in lines[3], "one failing entry fails the row, whatever its other entries"
    assert "R-005 names the text C:guide/loop.md, which is no file of this Workspace" in lines[4], "a drive-relative path is no path of the Workspace"


def test_a_heading_inside_a_code_block_is_no_heading(tmp_path):
    r = make(tmp_path, "| R-001 | a | owner | built | text: guide/loop.md :: A heading in a code block (#7) |\n"
                       "| R-002 | b | owner | built | text: guide/loop.md :: Another in a tilde block (#7) |\n")
    rc, out = run(r, "plan")
    lines = no_evidence(out)
    assert rc == 1 and len(lines) == 2 and "does not hold" in lines[0] and "does not hold" in lines[1], out


def test_a_pull_request_not_on_origin_main_fails_on_merged_work_and_is_a_note_on_a_branch(tmp_path):
    """On main as merged, a number no squash carries is a failure. On a branch with a commit origin/main lacks, the cell may
    name the branch's own pull request: a note, and the row passes; the same number fails once the checkout is merged work."""
    r = make(tmp_path, PAUSE % 8)
    rc, out = run(r)
    assert rc == 1 and "NO EVIDENCE: R-001 names pull request #8, whose squash is not on origin/main" in out, out
    git(r, "switch", "-q", "-c", "work")
    git(r, "commit", "-q", "--allow-empty", "-m", "the records")
    rc, out = run(r)
    assert rc == 0 and "note: R-001: pull request #8 is not on origin/main yet" in out and not no_evidence(out), out


def test_the_pull_request_named_must_have_changed_the_file(tmp_path):
    """Any merged number is not enough: #8's squash stands on origin/main and changed nothing of the guide. A later squash
    that did change it counts, and so does the one that first wrote it."""
    r = make(tmp_path, PAUSE % 8, subjects=("the guide's pause (R-001) (#7)", "another thing altogether (#8)"))
    rc, out = run(r)
    assert rc == 1 and "NO EVIDENCE: R-001 names pull request #8, whose squash did not change guide/loop.md" in out, out
    (r / "guide" / "loop.md").write_text(TEXT + "\nOne more line.\n", encoding="utf-8")
    git(r, "commit", "-q", "-am", "the pause reworded (R-001) (#9)")
    git(r, "push", "-q", "origin", "main")
    git(r, "fetch", "-q", "origin")
    (r / "docs" / "REQUIREMENTS.md").write_text(HEAD + PAUSE % 9 + (PAUSE % 7).replace("R-001", "R-002"), encoding="utf-8")
    rc, out = run(r, "plan")                                 # the register's own edit is unmerged work: `ahead`, and both numbers are on main
    assert rc == 0 and not no_evidence(out), out


def test_the_number_is_read_at_the_end_of_a_squash_subject_only(tmp_path):
    r = make(tmp_path, PAUSE % 8, subjects=("a subject that names (#8) in its middle (#7)",))
    rc, out = run(r)
    assert rc == 1 and "names pull request #8" in out, out


def test_for_a_row_whose_sentence_names_a_program_a_text_entry_never_counts(tmp_path):
    """What a program does is proved by a test. A text entry alone fails by the program's name; beside a test file it is
    allowed in plan mode, and done mode still asks for a tracked test that names the row, which the text cannot stand in for."""
    entry = "text: guide/loop.md :: The pause before planning (#7)"
    rows = ("| R-001 | scope-check.py refuses a path outside the brief | owner | built | %s |\n"
            "| R-002 | the text says when the pause ends | owner | built | - |\n"
            "| R-003 | scope-check.py prints its count, and the guide says how to read it | owner | built | tests/test_scope.py; %s |\n" % (entry, entry))
    r = make(tmp_path, rows)
    rc, out = run(r, "plan")
    lines = no_evidence(out)
    assert rc == 1 and len(lines) == 2, out
    assert "R-001 names a program (scope-check.py): a text entry alone is no evidence of what a program does, name its test beside it" in lines[0]
    assert "R-002" in lines[1] and "names no test file" in lines[1], "a row with neither form still fails as before"
    rc, out = run(r, "done")
    assert "NO EVIDENCE: R-003 (scope-check.py prints its count" in out and "no tracked test names it" in out, out


def test_a_text_s_own_path_under_a_tests_folder_is_no_test_file(tmp_path):
    """The entry's path is taken out before the cell is searched for a test path: a text kept under a folder named tests
    does not pass a row whose heading is missing."""
    r = make(tmp_path, "| R-001 | a | owner | built | text: tests/notes.md :: No such heading (#7) |\n", texts=("tests/",))
    (r / "tests").mkdir()
    (r / "tests" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    rc, out = run(r, "plan")
    assert rc == 1 and len(no_evidence(out)) == 1 and "names the heading 'No such heading'" in out, out


def test_a_shallow_clone_checks_file_and_heading_and_notes_the_rest(tmp_path):
    """CI's checkout holds one commit: the squash cannot be looked up there, which is a note and never a failure, while a
    missing heading still fails."""
    r = make(tmp_path, PAUSE % 99, subjects=("first (#1)", "second (#2)"))
    shallow = tmp_path / "shallow"
    git(tmp_path, "clone", "-q", "--depth", "1", (tmp_path / "origin.git").as_uri(), str(shallow))
    rc, out = run(shallow)
    assert rc == 0 and "note: R-001: pull request #99 not looked up (a shallow clone holds no history)" in out, out
