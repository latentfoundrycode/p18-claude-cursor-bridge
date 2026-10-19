"""TASK-016: the traceability comparison, bridge/cursor-bridge/trace-check.py.

enforces: docs/REQUIREMENTS.md R-029 (every standing rule and conditional passage traceable from a pinned pre-split
baseline commit to its new file by a mechanical comparison: moves verbatim, a reword a listed exception, text new to the
modules declared new, every ~/.claude/... reference and cited section resolving) and docs/BUILD_PLAN.md, TASK-016's
Done when (a clean move, a two-hop move, a copy into two homes fails, a silent reword fails, an undeclared new passage
fails, a dropped boundary section fails, a dangling reference fails, both exception kinds), as handoff/TASK-016.md
specifies the program's output. Each case builds a small git repository in a temporary folder. Supervisor-authored.
"""
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
TRACE_CHECK = REPO / "bridge" / "cursor-bridge" / "trace-check.py"
DASH = chr(0x2014)
INTAKE = "Phase 1 " + DASH + " Intake"
CORE = "bridge/commands/supervisor.md"
PHASES = "bridge/cursor-bridge/workflow/phases/"

INTAKE_WRAPPED = "Intake asks the owner what the software does\nand records it in the requirements register.\n"
INTAKE_ONE_LINE = "Intake asks the owner what the software does and records it in the requirements register.\n"
BOUNDARY = "**The Workspace boundary.** Every artifact the loop writes lives in the Workspace;\nnothing is written outside it.\n"

BASE_CORE = (
    "---\nname: supervisor\n---\n\n"
    "# Supervisor\n\n"
    "## The project layout\n\n"
    + BOUNDARY + "\n"
    "## " + INTAKE + "\n\n"
    + INTAKE_WRAPPED + "\n"
    "- A list item that\n  continues on a second line.\n\n"
    "| a | b |\n|---|---|\n| 1 | 2 |\n\n"
    "```text\n# Not a heading\n```\n\n"
    "Terms are in ~/.claude/cursor-bridge/Glossary.md (see \"The project layout\"), and seeds in\n"
    "~/.claude/cursor-bridge/design-seeds/<brand>/DESIGN.md, per \"Phase 1\".\n\n"
    "## Standing rules\n\n"
    "1. Never write implementation code.\n"
    "2. Reports lead with the owner's decision,\n   and the technical part follows.\n"
)
OPEN_LIST = "# The open list\n\nThe open list names every product type.\n"
EXCEPTIONS = "# Trace exceptions\n\nEntries are appended by the increment that rewords or adds.\n\n## Entries\n"


def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                        "-c", "core.autocrlf=false", *args],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def make_repo(tmp_path):
    """A repository in the bridge's layout, its baseline commit, and the pinned baseline and empty exceptions."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    write(root, CORE, BASE_CORE)
    write(root, "bridge/cursor-bridge/workflow/open-list.md", OPEN_LIST)
    write(root, "bridge/cursor-bridge/Glossary.md", "# Glossary\n")
    write(root, "bridge/cursor-bridge/design-seeds/acme/DESIGN.md", "# Acme\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "baseline")
    sha = git(root, "rev-parse", "HEAD")
    write(root, "bridge/cursor-bridge/workflow/trace-baseline.txt", sha + "\n")
    write(root, "bridge/cursor-bridge/workflow/trace-exceptions.md", EXCEPTIONS)
    return root


def core_without(*parts):
    text = BASE_CORE
    for part in parts:
        assert text.count(part) == 1, part
        text = text.replace(part, "")
    return text


def entries(root, *lines):
    write(root, "bridge/cursor-bridge/workflow/trace-exceptions.md", EXCEPTIONS + "".join(l + "\n" for l in lines))


def run(root, *args):
    p = subprocess.run([sys.executable, str(TRACE_CHECK), "--repo", str(root), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                       timeout=120)
    assert "Traceback" not in p.stderr, p.stderr
    return p.returncode, p.stdout.splitlines()


def fails(lines):
    return [l for l in lines if l.startswith("FAIL ")]


def test_r029_an_unchanged_tree_passes_and_traces_every_passage(tmp_path):
    root = make_repo(tmp_path)
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [] and lines[-1] == "RESULT: OK", lines
    traced = [l for l in lines if l.startswith("TRACED: ")]
    # the units: the front matter's line, the boundary paragraph, the intake paragraph, the list item, the table, the fenced block, the
    # references paragraph, and the two standing rules
    assert traced and re.match(r"TRACED: 9 passages of baseline [0-9a-f]{7}; 9 in supervisor\.md, 0 under workflow/, "
                               r"0 dropped, 0 excused$", traced[0]), lines


def test_r029_map_lists_each_passage_with_its_home(tmp_path):
    root = make_repo(tmp_path)
    rc, lines = run(root, "--map")
    maps = [l for l in lines if l.startswith("MAP ")]
    assert rc == 0 and len(maps) == 9, lines
    assert all(l.startswith("MAP " + CORE + ": ") for l in maps), maps
    assert any("**The Workspace boundary.**" in l and ": The project layout - " in l for l in maps), maps
    assert any(": Standing rules - 1. Never write implementation code." in l for l in maps), maps


def test_r029_a_clean_move_into_a_phase_module_passes(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, core_without(INTAKE_WRAPPED + "\n"))
    write(root, PHASES + "intake.md", "# Intake\n\n" + INTAKE_WRAPPED)
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [] and lines[-1] == "RESULT: OK", lines
    assert any(l.startswith("TRACED: 9 passages") and "; 8 in supervisor.md, 1 under workflow/, 0 dropped" in l
               for l in lines), lines


def test_r029_a_hard_wrapped_passage_moved_onto_one_line_passes(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, core_without(INTAKE_WRAPPED + "\n"))
    write(root, PHASES + "intake.md", "# Intake\n\n" + INTAKE_ONE_LINE)
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [], lines


def test_r029_a_two_hop_move_with_the_module_emptied_passes(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, core_without(INTAKE_WRAPPED + "\n"))
    write(root, PHASES + "intake.md", "# Intake\n")
    write(root, "bridge/cursor-bridge/workflow/traits/installable.md", "# Installable\n\n" + INTAKE_ONE_LINE)
    rc, lines = run(root, "--map")
    assert rc == 0 and fails(lines) == [], lines
    assert any(l.startswith("MAP bridge/cursor-bridge/workflow/traits/installable.md: " + INTAKE.replace(DASH, "\\u2014"))
               for l in lines), lines


def test_r029_a_copy_into_two_homes_fails(tmp_path):
    root = make_repo(tmp_path)
    write(root, PHASES + "intake.md", "# Intake\n\n" + INTAKE_WRAPPED)
    rc, lines = run(root)
    assert rc == 1 and lines[-1] == "RESULT: 1 problem(s)", lines
    assert fails(lines) == ["FAIL (copy) %s, %sintake.md: Phase 1 \\u2014 Intake - Intake asks the owner what the "
                            "software does and records it " % (CORE, PHASES)], lines


def test_r029_a_copy_within_one_file_fails(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, BASE_CORE.replace(INTAKE_WRAPPED, INTAKE_WRAPPED + "\n" + INTAKE_ONE_LINE))
    rc, lines = run(root)
    assert rc == 1 and len(fails(lines)) == 1 and fails(lines)[0].startswith("FAIL (copy) " + CORE), lines


def test_r029_a_silent_reword_fails_as_dropped(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, BASE_CORE.replace("what the software does", "what the product does"))
    rc, lines = run(root)
    assert rc == 1 and fails(lines) == ["FAIL (dropped) %s: Phase 1 \\u2014 Intake - Intake asks the owner what the "
                                        "software does and records it " % CORE], lines


def test_r029_an_undeclared_new_passage_in_a_module_fails(tmp_path):
    root = make_repo(tmp_path)
    write(root, PHASES + "intake.md", "# Intake\n\nA passage no baseline holds.\n")
    rc, lines = run(root)
    assert rc == 1 and fails(lines) == ["FAIL (new) %sintake.md: Intake - A passage no baseline holds." % PHASES], lines


def test_r029_new_text_in_the_core_or_beside_the_modules_is_not_flagged(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, BASE_CORE + "\nA sentence the core gained.\n")
    write(root, "bridge/cursor-bridge/workflow/open-list.md", OPEN_LIST + "\nA row the open list gained.\n")
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [], lines


def test_r029_a_dropped_workspace_boundary_paragraph_fails(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, core_without(BOUNDARY + "\n"))
    rc, lines = run(root)
    assert rc == 1 and fails(lines) == ["FAIL (dropped) %s: The project layout - **The Workspace boundary.** Every "
                                        "artifact the loop writes l" % CORE], lines


def test_r029_a_dangling_claude_reference_fails(tmp_path):
    root = make_repo(tmp_path)
    (root / "bridge" / "cursor-bridge" / "Glossary.md").unlink()
    rc, lines = run(root)
    assert rc == 1 and fails(lines) == ["FAIL (ref) %s:28: ~/.claude/cursor-bridge/Glossary.md" % CORE], lines


def test_r029_a_placeholder_reference_resolves_by_its_folder(tmp_path):
    root = make_repo(tmp_path)
    for path in (root / "bridge" / "cursor-bridge" / "design-seeds").rglob("*"):
        if path.is_file():
            path.unlink()
    (root / "bridge" / "cursor-bridge" / "design-seeds" / "acme").rmdir()
    rc, lines = run(root)
    assert rc == 0, lines
    (root / "bridge" / "cursor-bridge" / "design-seeds").rmdir()
    rc, lines = run(root)
    assert rc == 1 and fails(lines) == ["FAIL (ref) %s:29: ~/.claude/cursor-bridge/design-seeds/<brand>/DESIGN.md"
                                        % CORE], lines


def test_r029_a_dangling_cited_section_fails(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, BASE_CORE.replace("## The project layout\n", "## The layout of a project\n"))
    rc, lines = run(root)
    assert rc == 1 and fails(lines) == ['FAIL (cite) %s: Phase 1 \\u2014 Intake - "The project layout"' % CORE], lines


def test_r029_a_cited_section_resolves_in_a_module(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, BASE_CORE.replace("## The project layout\n\n" + BOUNDARY + "\n", ""))
    write(root, PHASES + "intake.md", "# The project layout\n\n" + BOUNDARY)
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [], lines


def test_r029_reword_entries_excuse_the_vanished_and_the_new_text(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, core_without(INTAKE_WRAPPED + "\n"))
    write(root, PHASES + "intake.md", "# Intake\n\nIntake asks the owner what the product does.\n")
    rc, lines = run(root)
    assert rc == 1 and [l.split(" ")[1] for l in fails(lines)] == ["(dropped)", "(new)"], lines
    entries(root, "- reword TASK-010 %s %s" % (CORE, INTAKE), "- reword TASK-010 %sintake.md Intake" % PHASES)
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [] and lines[-1] == "RESULT: OK", lines
    assert ("NOTE (reword TASK-010) %s: Phase 1 \\u2014 Intake - Intake asks the owner what the software does and "
            "records it " % CORE) in lines, lines
    assert any(l.startswith("TRACED: ") and l.endswith(" dropped, 1 excused") for l in lines), lines


def test_r029_a_reword_entry_names_the_baseline_section_even_when_the_core_renamed_it(tmp_path):
    """Requirement 6: a reword entry's vanished text is looked up in the baseline file's section; here the core has
    no section of that name any more (the builder's mutation (e) survived without this case)."""
    root = make_repo(tmp_path)
    renamed = BASE_CORE.replace("## " + INTAKE + "\n", "## Phase 1 " + DASH + " Start\n")
    write(root, CORE, renamed.replace("what the software does", "what the product does"))
    rc, lines = run(root)
    assert rc == 1 and [l.split(" ")[1] for l in fails(lines)] == ["(dropped)"], lines
    entries(root, "- reword TASK-010 %s %s" % (CORE, INTAKE))
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [], lines
    assert any(l.startswith("NOTE (reword TASK-010) %s: Phase 1 \\u2014 Intake - " % CORE) for l in lines), lines


def test_r029_a_reword_entry_for_another_file_does_not_excuse_a_core_drop(tmp_path):
    """Requirement 6: a reword entry excuses vanished text only in the section of the baseline file it names; an entry
    naming a module, under the core's heading text, excuses nothing in the core."""
    root = make_repo(tmp_path)
    write(root, CORE, BASE_CORE.replace("what the software does", "what the product does"))
    entries(root, "- reword TASK-010 %sintake.md %s" % (PHASES, INTAKE))
    rc, lines = run(root)
    assert rc == 1 and [l.split(" ")[1] for l in fails(lines)] == ["(dropped)"], lines


def test_r029_module_text_from_any_baseline_home_is_not_new(tmp_path):
    """Requirement 5: new text is judged against the units of all baseline homes, the workflow files included, not
    the core alone (the builder's mutation (f) survived without this case)."""
    root = make_repo(tmp_path)
    write(root, PHASES + "intake.md", "# Intake\n\nThe open list names every product type.\n")
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [], lines


def test_r029_a_word_ending_in_see_per_or_under_is_not_a_citation(tmp_path):
    root = make_repo(tmp_path)
    write(root, CORE, BASE_CORE + "\nWe understand \"No such section\" and hyper \"Nor this\" and foresee \"Nor that\".\n")
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [], lines


def test_r029_a_new_entry_excuses_new_text_but_not_a_dropped_passage(tmp_path):
    root = make_repo(tmp_path)
    write(root, PHASES + "intake.md", "# Intake\n\nA passage no baseline holds.\n")
    entries(root, "- new TASK-010 %sintake.md Intake" % PHASES)
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [], lines
    write(root, CORE, core_without(INTAKE_WRAPPED + "\n"))
    entries(root, "- new TASK-010 %sintake.md Intake" % PHASES, "- new TASK-010 %s %s" % (CORE, INTAKE))
    rc, lines = run(root)
    assert rc == 1 and [l.split(" ")[1] for l in fails(lines)] == ["(dropped)"], lines


def test_r029_a_copy_explained_by_an_entry_passes(tmp_path):
    root = make_repo(tmp_path)
    write(root, PHASES + "intake.md", "# Intake\n\n" + INTAKE_WRAPPED)
    entries(root, "- new TASK-010 %sintake.md Intake" % PHASES)
    rc, lines = run(root)
    assert rc == 0 and fails(lines) == [], lines


def test_r029_a_missing_baseline_commit_is_not_checked(tmp_path):
    root = make_repo(tmp_path)
    write(root, "bridge/cursor-bridge/workflow/trace-baseline.txt", "0" * 40 + "\n")
    rc, lines = run(root)
    assert rc == 2 and lines[-1] == "RESULT: not checked", lines
    assert any(l.startswith("ERROR: ") and "shallow clone" in l for l in lines), lines   # Requirement 9 names the cause
    assert not fails(lines), lines


def test_r029_a_malformed_baseline_file_is_not_checked(tmp_path):
    root = make_repo(tmp_path)
    for text in ("HEAD\n", "0" * 39 + "\n", ("A" * 40) + "\n", "0" * 40 + "\n" + "0" * 40 + "\n"):
        write(root, "bridge/cursor-bridge/workflow/trace-baseline.txt", text)
        rc, lines = run(root)
        assert rc == 2 and lines[-1] == "RESULT: not checked", (text, lines)


def test_r029_a_malformed_exceptions_file_is_not_checked(tmp_path):
    root = make_repo(tmp_path)
    for line in ("- rewrite TASK-010 %s %s" % (CORE, INTAKE), "- reword task-010 %s %s" % (CORE, INTAKE),
                 "- reword TASK-010 %s" % CORE, "reword TASK-010 %s %s" % (CORE, INTAKE),
                 "- reword TASK-010 docs/other.md Intake"):
        entries(root, line)
        rc, lines = run(root)
        assert rc == 2 and lines[-1] == "RESULT: not checked", (line, lines)
        assert any(l.startswith("ERROR: ") and re.search(r"\b6\b", l) for l in lines), (line, lines)
    write(root, "bridge/cursor-bridge/workflow/trace-exceptions.md", "# Trace exceptions\n\nNo entries heading.\n")
    rc, lines = run(root)
    assert rc == 2 and lines[-1] == "RESULT: not checked", lines


def test_r029_a_folder_that_is_not_a_repository_is_not_checked(tmp_path):
    rc, lines = run(tmp_path)
    assert rc == 2 and lines[-1] == "RESULT: not checked", lines
