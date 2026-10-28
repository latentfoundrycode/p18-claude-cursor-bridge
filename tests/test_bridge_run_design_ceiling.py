"""bridge-run.py holds the design critique's ceiling (2026.10.18a, KP-062; enforces: design.md, "The launcher holds the ceiling", "The loop
stops by what was found, and after four rounds at the most", and "The launcher holds the ceiling"): a cursor-agent
launch whose arguments name run/review/DESIGN-<subject>-<n>.md with n above five is refused, and so are a second
resolution round, DESIGN-<subject>-R2 or later, and a round that cannot be read (only 1 to 5 and R1 can), unless docs/RUN_PARAMETERS.md carries the owner's words on a line
`Design rounds above five: <subject> <rounds> (<their words>, <date>)`, which allows rounds up to <rounds> and a second
resolution round for that subject. The TDP ran 45 rounds on one change on 2026-10-18."""
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
PROMPT = ("The text to criticise is already written to run/review/DESIGN-%s.md, with the lenses, the grades to answer in, "
          "and the record of what was accepted so far. Read that file whole; do not ask for it.")


def design_cmd(name, mode="--mode=ask"):
    return ["cursor-agent", "-p", mode, "--trust", "--model", "grok-4.7-medium", PROMPT % name]


def run_parameters(folder, *lines):
    (folder / "docs").mkdir(exist_ok=True)
    (folder / "docs" / "RUN_PARAMETERS.md").write_text("# Run parameters\n" + "".join(l + "\n" for l in lines),
                                                        encoding="utf-8", newline="\n")


@pytest.mark.parametrize("name", ["design-1", "design-4", "design-5", "plan-5", "azure-allowance-5", "change-2-5",
                                  "design-R1", "5"])
def test_rounds_up_to_five_and_one_resolution_round_are_allowed(program, tmp_path, name):
    """Four rounds and the confirming read (round five), and the subject's one resolution round, launch as before; a
    subject holding a hyphen or a digit is read whole (`change-2-5` is subject `change-2`, round five), and the plan's
    older file name without a subject (`DESIGN-5.md`) counts as a subject of its own."""
    br = program("bridge-run")
    assert br.design_ceiling(design_cmd(name), str(tmp_path)) is None


@pytest.mark.parametrize("name, subject", [("design-6", "design"), ("plan-7", "plan"), ("azure-allowance-45", "azure-allowance"),
                                           ("change-2-6", "change-2"), ("design-R2", "design"), ("design-R3", "design"),
                                           ("6", "")])
def test_a_sixth_round_and_a_second_resolution_round_are_refused(program, tmp_path, name, subject):
    """Past the ceiling the launcher refuses, naming the subject, the ceiling and the line that lifts it."""
    br = program("bridge-run")
    reason = br.design_ceiling(design_cmd(name), str(tmp_path))
    assert reason is not None, name
    assert 'design.md, "The launcher holds the ceiling"' in reason, reason
    if subject:
        assert subject in reason, reason


@pytest.mark.parametrize("name", ["design-0", "design-05", "design-R0", "design-R01", "design-confirm", "ceiling-5b",
                                  "design-", "design-R", "Azure monthly allowance-1", "Design-1", "azure-Allowance-2",
                                  "design-r1", "design-06", "design-R02"])
def test_a_round_that_cannot_be_read_is_refused(program, tmp_path, name):
    """Only 1 to 5 without a leading zero, and R1, are rounds: `0` would be a sixth critique file, `R0` a second
    resolution file and `05` a second fifth round; a round that is no number is no round at all."""
    br = program("bridge-run")
    run_parameters(tmp_path, "Design rounds above five: %s 8 (\"run it to eight\", 2026-10-18)" % name.rsplit("-", 1)[0])
    assert br.design_ceiling(design_cmd(name), str(tmp_path)) is not None, name


def test_a_design_file_whose_name_does_not_end_in_md_is_refused(program, tmp_path):
    """A subject written with spaces ends the name before `.md`: the launch is refused as a name it cannot read, never
    let through unchecked."""
    br = program("bridge-run")
    for prompt in ("read run/review/DESIGN-azure allowance-6.md", "read run/review/DESIGN-azure"):
        assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", prompt], str(tmp_path)) is not None, prompt


@pytest.mark.parametrize("name, allowed", [("1", True), ("5", True), ("45", False), ("R1", True), ("R2", False)])
def test_a_one_part_name_is_a_round_with_an_empty_subject(program, tmp_path, name, allowed):
    """The plan's file before 2026.10.18a, `DESIGN-<round>.md`, is held by the same ceiling; its empty subject is not
    `plan`, so a line lifting `plan` does not lift it."""
    br = program("bridge-run")
    run_parameters(tmp_path, "Design rounds above five: plan 50 (\"let the plan run\", 2026-10-18)")
    assert (br.design_ceiling(design_cmd(name), str(tmp_path)) is None) == allowed, name


def test_trailing_punctuation_is_not_part_of_the_name(program, tmp_path):
    """A file named at the end of a sentence (`...DESIGN-design-1.md.`) or before a comma is read without it."""
    br = program("bridge-run")
    for prompt in ("read run/review/DESIGN-design-1.md.", "read run/review/DESIGN-design-1.md, then answer",
                   "read (run/review/DESIGN-design-1.md)"):
        assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", prompt], str(tmp_path)) is None, prompt
    assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", "read run/review/DESIGN-design-6.md."],
                             str(tmp_path)) is not None


def test_an_absolute_path_is_read_too(program, tmp_path):
    br = program("bridge-run")
    for prompt in ("read D:\\work\\proj\\run\\review\\DESIGN-design-6.md", "read /srv/proj/run/review/DESIGN-design-6.md"):
        assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", prompt], str(tmp_path)) is not None, prompt


def test_the_folders_are_matched_in_any_case(program, tmp_path):
    """On Windows `Run\\Review\\DESIGN-design-6.md` names the same file as `run/review/DESIGN-design-6.md`, so the
    folders' case is no way around the ceiling."""
    br = program("bridge-run")
    for prompt in ("read Run\\Review\\DESIGN-design-6.md", "read RUN/REVIEW/design-design-6.md"):
        assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", prompt], str(tmp_path)) is not None, prompt


def test_one_refused_name_among_several_refuses_the_launch(program, tmp_path):
    br = program("bridge-run")
    prompt = "compare run/review/DESIGN-design-1.md with run/review/DESIGN-design-6.md"
    assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", prompt], str(tmp_path)) is not None
    prompt = "compare run/review/DESIGN-design-1.md with run/review/DESIGN-plan-2.md"
    assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", prompt], str(tmp_path)) is None


def test_the_refusal_names_the_file_and_where_it_looked_for_the_owners_line(program, tmp_path):
    """After an app restart the session can sit at the project root, where there is no docs/: the message says which
    run parameters file was read, so a lift that was not seen is not mistaken for the ceiling."""
    br = program("bridge-run")
    reason = br.design_ceiling(design_cmd("design-6"), str(tmp_path))
    assert "DESIGN-design-6.md" in reason and "RUN_PARAMETERS.md" in reason, reason
    assert str(tmp_path) in reason, reason


def test_the_mode_does_not_matter(program, tmp_path):
    """The refusal reads the file the arguments name, not the mode: a launch without `--mode=ask` (the code review's
    `--force` form) on a sixth round is refused too, so dropping the read-only mode is no way around the ceiling."""
    br = program("bridge-run")
    assert br.design_ceiling(design_cmd("design-6", mode="--force"), str(tmp_path)) is not None
    assert br.design_ceiling(design_cmd("design-6", mode="--mode=plan"), str(tmp_path)) is not None


def test_other_files_and_commands_are_not_touched(program, tmp_path):
    """A code review's file, a stage review's, the launcher's own .err name and a command that is not cursor-agent
    are no design rounds."""
    br = program("bridge-run")
    for prompt in ("the diff is already at run/review/REVIEW-012.diff; read it",
                   "the diff is already at run/review/STAGE-B2.diff; read it",
                   "see run/review/REVIEW-DESIGN-design-9.err"):
        assert br.design_ceiling(["cursor-agent", "-p", "--force", "--model", "m", prompt], str(tmp_path)) is None, prompt
    assert br.design_ceiling(["gh", "pr", "checks", "12", "--watch", "--required"], str(tmp_path)) is None


def test_a_windows_path_is_read_too(program, tmp_path):
    br = program("bridge-run")
    assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", "read run\\review\\DESIGN-design-6.md"], str(tmp_path)) is not None


def test_the_owners_line_lifts_the_ceiling_for_its_subject_only(program, tmp_path):
    """`Design rounds above five: design 8 (...)` allows rounds up to eight and a second resolution round for the
    design; the plan keeps its ceiling; round nine and a third resolution round stay refused."""
    br = program("bridge-run")
    run_parameters(tmp_path, "Design rounds above five: design 8 (\"let the design run to eight\", 2026-10-18)")
    for name in ("design-5", "design-6", "design-8", "design-R1", "design-R2"):
        assert br.design_ceiling(design_cmd(name), str(tmp_path)) is None, name
    for name in ("design-9", "design-R3", "plan-6", "plan-R2"):
        assert br.design_ceiling(design_cmd(name), str(tmp_path)) is not None, name


def test_a_second_line_for_one_subject_is_ignored(program, tmp_path):
    """A subject is lifted once: the first line governs, so a later, larger line lifts nothing more."""
    br = program("bridge-run")
    run_parameters(tmp_path, "Design rounds above five: design 8 (\"to eight\", 2026-10-18)",
                   "Design rounds above five: design 12 (\"to twelve\", 2026-10-19)")
    assert br.design_ceiling(design_cmd("design-8"), str(tmp_path)) is None
    assert br.design_ceiling(design_cmd("design-9"), str(tmp_path)) is not None


def test_the_first_well_formed_line_stands(program, tmp_path):
    """A line without the owner's words lifts nothing and does not use up the subject's one lift: the first
    well-formed line after it stands, as the sibling `Ceiling above twice` line is read."""
    br = program("bridge-run")
    run_parameters(tmp_path, "Design rounds above five: design 12",
                   "Design rounds above five: design 8 (\"to eight\", 2026-10-18)")
    assert br.design_ceiling(design_cmd("design-8"), str(tmp_path)) is None
    assert br.design_ceiling(design_cmd("design-9"), str(tmp_path)) is not None


@pytest.mark.parametrize("line", [
    "Design rounds above five: design 8",
    "Design rounds above five: design 8 ()",
    "Design rounds above five: design 5 (\"five\", 2026-10-18)",
    "Design rounds above five: design 4 (\"four\", 2026-10-18)",
], ids=["no-words", "empty-words", "not-above-five", "below-five"])
def test_a_line_without_the_owners_words_or_not_above_five_lifts_nothing(program, tmp_path, line):
    br = program("bridge-run")
    run_parameters(tmp_path, line)
    assert br.design_ceiling(design_cmd("design-6"), str(tmp_path)) is not None
    assert br.design_ceiling(design_cmd("design-R2"), str(tmp_path)) is not None


@pytest.mark.parametrize("prompt", [
    "read run//review/DESIGN-plan-6.md",
    "read run\\\\review\\\\DESIGN-plan-6.md",
    "read run/review//DESIGN-plan-6.md",
    "read run/./review/DESIGN-plan-6.md",
    "read run/review/./DESIGN-plan-6.md",
    "read .\\run\\.\\review\\DESIGN-plan-6.md",
], ids=["doubled-before-review", "escaped-backslashes", "doubled-before-design", "dot-before-review",
        "dot-before-design", "windows-dots"])
def test_doubled_separators_and_dot_segments_name_the_same_file(program, tmp_path, prompt):
    """Review A, round 1: Windows opens `run//review/...`, `run\\\\review\\\\...` (a JSON-escaped path) and
    `run/./review/...` as `run/review/...`, so they are read as it is."""
    br = program("bridge-run")
    assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", prompt], str(tmp_path)) is not None, prompt
    allowed = prompt.replace("plan-6", "plan-2")
    assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", allowed], str(tmp_path)) is None, allowed


@pytest.mark.parametrize("prompt", [
    "read run./review/DESIGN-design-6.md",
    "read run/review./DESIGN-design-6.md",
    "read run./review./DESIGN-azure-allowance-45.md",
    "read run..\\review.\\DESIGN-design-6.md",
    "read run /review/DESIGN-design-6.md",
], ids=["dot-after-run", "dot-after-review", "dots-after-both", "windows-dots-after-both", "space-after-run"])
def test_a_folder_name_ending_in_dots_or_spaces_names_the_same_file(program, tmp_path, prompt):
    """Review B, HOTFIX-001: Windows drops a folder name's trailing dots and spaces, so `run./review./` opens
    `run/review/`; reading the round-6 file through it proved it."""
    br = program("bridge-run")
    assert br.design_ceiling(["cursor-agent", "-p", "--mode=ask", prompt], str(tmp_path)) is not None, prompt


def test_a_round_too_long_for_int_is_refused_without_a_traceback(program, tmp_path):
    """Review A, HOTFIX-001 round 2: Python refuses int() on more than 4,300 digits; the launcher refuses the name
    instead of ending in a traceback, and a run parameters line holding such a number is skipped as not well-formed."""
    br = program("bridge-run")
    assert br.design_ceiling(design_cmd("design-" + "9" * 5000), str(tmp_path)) is not None
    assert br.design_ceiling(design_cmd("design-R" + "9" * 5000), str(tmp_path)) is not None
    run_parameters(tmp_path, "Design rounds above five: design %s (\"many\", 2026-10-18)" % ("9" * 5000))
    assert br.design_ceiling(design_cmd("design-6"), str(tmp_path)) is not None
    assert br.design_ceiling(design_cmd("design-2"), str(tmp_path)) is None


@pytest.mark.parametrize("name, words", [
    ("design-6", "above round 5"), ("design-R2", "beyond R1"), ("design-05", "cannot be read"),
    ("Design-3", "cannot be read"), ("design-confirm", "cannot be read"),
])
def test_the_refusal_says_which_refusal_it_is_and_names_the_round(program, tmp_path, name, words):
    """A name that cannot be read is a typo to fix; a round past the ceiling sends the subject on to its resolution
    round or gate: the message says which, and names the round as written."""
    br = program("bridge-run")
    reason = br.design_ceiling(design_cmd(name), str(tmp_path))
    assert words in reason, reason
    assert "round %s" % name.rsplit("-", 1)[1] in reason, reason


def test_under_the_owners_line_the_refusal_names_the_lifted_ceiling(program, tmp_path):
    br = program("bridge-run")
    run_parameters(tmp_path, "Design rounds above five: design 8 (\"to eight\", 2026-10-18)")
    assert "above round 8" in br.design_ceiling(design_cmd("design-9"), str(tmp_path))
    assert "beyond R2" in br.design_ceiling(design_cmd("design-R3"), str(tmp_path))


def test_the_refusal_is_ascii_whatever_the_name_holds(program, tmp_path):
    br = program("bridge-run")
    reason = br.design_ceiling(design_cmd("plän-6"), str(tmp_path))
    assert reason is not None and reason.isascii(), reason


@pytest.mark.parametrize("line", [
    "- **Design rounds above five:** design 8 (\"to eight\", 2026-10-18)",
    "**Design rounds above five**: design 8 (\"to eight\", 2026-10-18)",
    "* Design rounds above five: design 8 (\"to eight\", 2026-10-18)",
], ids=["colon-inside-bold", "colon-after-bold", "star-bullet"])
def test_the_owners_line_is_read_in_its_markdown_forms(program, tmp_path, line):
    br = program("bridge-run")
    run_parameters(tmp_path, line)
    assert br.design_ceiling(design_cmd("design-8"), str(tmp_path)) is None


@pytest.mark.parametrize("line", [
    "Design rounds above five: DESIGN 8 (\"to eight\", 2026-10-18)",
    "Design rounds above five: design ٨ (\"to eight\", 2026-10-18)",
], ids=["subject-in-capitals", "arabic-indic-digit"])
def test_the_owners_line_takes_a_lower_case_subject_and_ascii_digits_only(program, tmp_path, line):
    """A subject is a lower-case token; a round is written in ASCII digits."""
    br = program("bridge-run")
    run_parameters(tmp_path, line)
    assert br.design_ceiling(design_cmd("design-6"), str(tmp_path)) is not None


def test_the_launcher_refuses_with_125_before_it_starts_anything(tmp_path):
    """End to end: the refusal is a `bridge-run: refused - ` line and exit 125, before the `started` line, and nothing is
    logged (no cursor-agent is run)."""
    env = dict(os.environ)
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    p = subprocess.run([sys.executable, PROG, "--limit", "auto", "--kind", "review", "--", *design_cmd("design-6")],
                       capture_output=True, text=True, env=env, cwd=str(tmp_path),
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert p.returncode == 125, (p.returncode, p.stderr)
    assert p.stderr.startswith("bridge-run: refused - design ceiling: "), p.stderr
    assert "bridge-run: started" not in p.stderr, p.stderr
    assert not (tmp_path / "run" / "launcher" / "runs.jsonl").exists()
