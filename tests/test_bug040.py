"""BUG-040 (stage T1's review, round 1): the findings of Review A's parts and Review B's consider, each its own cause.

enforces: docs/REQUIREMENTS.md R-042 (the ceiling's lifts), R-045 (T11, T17: the overtaken status file), R-047 (T1:
one subject for a design and its addendum), R-049 (D2: the stage review's SCOPE file and its parts), R-050 (T20: the
threat model given to the reviewers with the diff), R-051 (T13: escapes as text, KP-052 as corrected by R-054).

Review A's bridge part, Blocking 1: an overtaken pull request's re-review is a new snapshot, a guard round, and at a
round above the ceiling the text named no lift that fits, so the loop met a refusal it could not lawfully pass. The
rewrite is behaviour against the register (R-045's T17), one of the five, so the text names the class line. Its
Should fixes: the stage review's SCOPE file and Review A's briefing carried no threat model (S1); spec-packager told a
brief to write an escape through the file-writing tool where KP-052 says no tool writes one safely (S2); the change
cycle's item 4 ran a separate plan-addendum critique where design.md makes an addendum in the design's review file
from round 1 part of the design's subject (S3). Review B's consider: rule 6's "One of the five always blocks" read
alone ignored the threat model's bound. Review A's records part: R-045's Evidence named no test for P4, (a) or (c),
and the design's R-051 row still named `--staged`. The constants below are the sentences as written; the text was
applied from them. KP-052: no character outside ASCII is typed here."""
import os

from phase_modules import CORE, PHASES, flat, read, rule, section

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGE = os.path.join(PHASES, "delegation-loop", "merge.md")
REFLECTION = os.path.join(PHASES, "reflection.md")
CHANGE = os.path.join(PHASES, "change-cycle.md")
PACKAGER = os.path.join(ROOT, "bridge", "agents", "spec-packager.md")
REQUIREMENTS = os.path.join(ROOT, "docs", "REQUIREMENTS.md")
DESIGN = os.path.join(ROOT, "docs", "DESIGN.md")

B1_MERGE = ("Where that re-read would open a round above the ceiling, the rewrite is behaviour against the register, "
            "R-045's T17, one of the five, so its lift is a class line, `Blocking class: behaviour - R-045, the status "
            "file overtaken by PR #<m>'s merge`, written into `run/review/SCOPE-<ID>.md` before the snapshot (step 7, "
            "\"The review ceiling\"), which the reviewers confirm or deny against the round it lifts.")
B1_RULE43 = ("A pull request whose status file another pull request's merge overtook has the file rewritten as at its "
             "own merge and `main` merged into it, a new head the reviews read again (the delegation loop's step 8), "
             "above the ceiling under the class line step 8 gives it.")
S1_STEP2 = ("Write `run/review/SCOPE-STAGE-<name>.md`, the stage's increments and briefs, the threat models "
            "`docs/INVENTORY.md` records for the parts the stage touched (R-050), given to both reviewers with the "
            "diff, the earlier rounds' dispositions and,")
S1_STEP4 = ("4. Review A: `diff-reviewer` on `run/review/STAGE-<name>-r<N>.diff`, told the stage's briefs, the threat "
            "models the SCOPE file carries, and that it reads a stage, not an increment.")
S2_PACKAGER = ("**Escapes as text; non-ASCII listed.** Name a character a brief must mention but must not hold by its "
               "code point (U+202E), never by a typed backslash escape, which no tool writes safely, the file-writing "
               "tool included (KP-052); write a backtick or a backslash through the file-writing tool, never through a "
               "shell that reads escapes (a here-document, an inline command), which reads a backslash sequence as the "
               "real character, a right-to-left override among them.")
S3_ITEM4 = ("the two-critic loop, with its ceiling, on the addendum (the subject `<the change's name>-plan`), unless its "
            "increments stood in the design revision's review file from round 1, when it is criticised and gated with "
            "the design revision as one subject (Phase 2, \"The procedure\"). Gate: present it and get approval, at the "
            "design's gate where the two are one subject.")
S3_SURVIVAL = ("its record in `docs/DESIGN_CRITIQUE.md` under the change's subject and, where the plan addendum is a "
               "subject of its own (item 4), under `<the change's name>-plan`,")
RULE6 = "One of the five always blocks, within the threat model recorded for its part (below)."
DESIGN_R051 = ("`invisible-check.py` with a base and `--staged` (as built: its default form, `--staged` left to a "
               "program release, R-051's note);")
R045_EVIDENCE = (
    "P4: tests/test_release_t_merge.py::test_r045_p4_the_merged_branch_deleted_and_the_armed_form_skipped",
    "(a): tests/test_release_t_merge.py::test_r045_a_step_8_stands_in_its_own_sub_file",
    "(c): tests/test_release_t_merge.py::test_r045_c_the_three_allow_rules_and_the_commands_they_admit",
    "BUG-040: tests/test_bug040.py::test_bug040_b1_the_overtaken_re_review_names_its_lift",
)


def step8():
    return flat(section(read(MERGE), "8. Merge (the verified gate)", 3))


def stage_procedure():
    return flat(section(read(REFLECTION), "The procedure", 3))


def test_bug040_b1_the_overtaken_re_review_names_its_lift():
    """B1: the overtaken pull request's re-review, a new guard round, names its lift above the ceiling, in step 8 after
    the sentence that sends the reviews back, and in rule 43, which states the rewrite."""
    s = step8()
    assert ("and merges `main`, and the reviews read the new head again (T11, T17). " + B1_MERGE) in s
    r = rule(43)
    assert B1_RULE43 in r
    assert "a new head the reviews read again (the delegation loop's step 8). The `loop-guard`" not in r


def test_bug040_s1_the_stage_review_carries_the_threat_models():
    """S1 (R-050's T20 at the stage review): the stage's SCOPE file holds the recorded threat models, which both
    reviewers read with the diff, and Review A's briefing names them."""
    p = stage_procedure()
    assert S1_STEP2 in p
    assert S1_STEP4 in p
    assert "told the stage's briefs and that it reads a stage, not an increment." not in p


def test_bug040_s2_spec_packager_names_an_escape_by_its_code_point():
    """S2 (T13 against KP-052 as corrected): a brief names a character it must not hold by its code point, and writes
    backticks and backslashes through the file-writing tool."""
    rules = flat(read(PACKAGER).split("## Rules", 1)[1].split("## Output", 1)[0])
    assert S2_PACKAGER in rules
    assert "Write an escape sequence or a backtick as the characters you mean" not in rules
    assert "no tool is safe for a typed backslash-u escape" in flat(read(os.path.join(
        ROOT, "bridge", "cursor-bridge", "Known-Pitfalls.md")))


def test_bug040_s3_a_change_cycle_takes_the_one_subject_exception():
    """S3 (R-047's T1 in the text a change cycle reads): item 4 and the survival list give the exception design.md
    states, so an addendum in the design revision's review file from round 1 has no budget of its own."""
    text = read(CHANGE)
    assert S3_ITEM4 in flat(section(text, "The procedure", 3))
    assert S3_SURVIVAL in flat(section(text, "What must survive a compaction", 3))
    assert "A plan addendum whose increments stood in the design's review file from round 1 is no subject of its own" \
        in flat(read(os.path.join(PHASES, "design.md")))


def test_bug040_rule_6_bounds_always_by_the_threat_model():
    """Review B's consider: rule 6's "always blocks" carries the threat model's bound the rest of the rule states."""
    r = rule(6)
    assert RULE6 in r
    assert "within the threat model `docs/INVENTORY.md` records for the part it is in" in r
    assert "One of the five always blocks. " not in r


def test_bug040_records_r045_evidence_and_the_design_s_r051_row():
    """Review A's records part: R-045's Evidence names a test for P4, (a) and (c), and the design's R-051 row says what
    was built in place of `--staged`."""
    row = [l for l in read(REQUIREMENTS).split("\n") if l.startswith("| R-045 |")]
    assert len(row) == 1
    for item in R045_EVIDENCE:
        assert item in row[0], item
    assert DESIGN_R051 in read(DESIGN)
    assert os.path.exists(CORE)
