"""R-049 (release T, TASK-040): the stage close and the stage review.

enforces: docs/REQUIREMENTS.md R-049; docs/BUILD_PLAN.md TASK-040, Done when; docs/DESIGN.md, Change: release T (the
table of what changes, row R-049).

One test per item label of the row (D1, D2, D3, D4, T11, P4's text half, P17), each pinning its sentence in the home
the design's table names: the stage review's steps 2, 4 and 8, the demonstration and item 5 in `reflection.md`, step
9's scout in `delegation-loop/refactoring-pass.md`, and the `planning.stages` additions of `types/host-extension.md`
(the kind host-installation) and `traits/installable.md` (the kinds `installer` and `install-script`). The allow rules
D4 and P4 need, and the guard's reading of the tag, are pinned in tests/test_allowlist.py. The constants below are the
sentences as written; the text was applied from them. KP-052: no character outside ASCII is typed here."""
import os
import re

from phase_modules import read, section

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(ROOT, "bridge", "cursor-bridge", "workflow")
REFLECTION = os.path.join(WORKFLOW, "phases", "reflection.md")
REFACTOR = os.path.join(WORKFLOW, "phases", "delegation-loop", "refactoring-pass.md")

D1 = ("Re-check every mutation driver of the stage at HEAD first: every live mutant of the stage's mutants files "
      "applies exactly once, its `old` text found once in its file as the stage branch holds it (`mutation-run.py` "
      "applies a pair only then, and a pair found other than once is a mutant not applied, its earlier kill claiming "
      "nothing, KP-065), and one that does not is re-anchored in its mutants file and run again before the review, its "
      "kill counting only from that run; between stage "
      "reviews, a fix that moves product code re-anchors or re-runs every driver anchored on the moved file in the same "
      "pull request, and a ruling that names surfaces gets one test per surface in the fix that introduces it (D1).")
STEP2_DIFF = ("Then write the stage's whole change from committed state: `git diff <the stage's first checkpoint commit> "
              "origin/main > run/review/STAGE-<name>-r<N>.diff`, `<N>` the round step 3 opens, while no other stage's "
              "increment merged between the stage's first checkpoint and its last merge.")
D2 = ("each part a `diff-reviewer` call of its own and every part bounded alike: a test part at most 25 files (counted "
      "by `git diff --name-only <the first checkpoint> origin/main -- <the test folders>`), a product part per package, "
      "a drivers-and-records part per driver family (D2): a 79-file part once ended at the reviewer's turn limit without "
      "a verdict (reAngle, stage 3b), and a part that ends without a verdict, of any kind, is run again on what it had "
      "not reached (rule 43).")
D2_UNION = ("For an interleaved stage (step 2) the parts are `stage-diff.py`'s per-commit parts, a part over these "
            "bounds split by path alike, or its union split by path, never the plain range, which holds the other "
            "stage's commits, and the test part's files are counted on the union's own file list, the `diff --git` "
            "headers of the committed `run/review/STAGE-<name>-r<N>.diff` (D2, T11).")
D3 =("Three things keep the demonstration true to the product (D3): a stage that adds tables starts its live stack, "
      "with the schema check, at its first increment, never first at its close; the development database's rebuild run "
      "sheet is prepared before the demonstration, so that a database earlier runs left behind is rebuilt, never read "
      "as it stands; and the demonstration's harness drives the product's own entry points (its commands, its server, "
      "its screens), never a function below them, whose call can create a state the product cannot (KP-064).")
D4 = ("8. Still on the stage branch, tag its head: `git tag stage-review/<name>-<n>`, `<n>` the round's number (step "
      "2's `<N>`), a local tag never pushed (no push names it, and `--follow-tags` carries annotated tags only, which "
      "this one is not); then `git switch main` and `git branch -D stage/<name>`; nothing of the stage branch reaches "
      "`main`. A record citing a stage review's inputs (the round's diff, its parts, its SCOPE file) cites each as "
      "`<tag>:<path>`, `stage-review/<name>-<n>:run/review/SCOPE-STAGE-<name>.md` say, and reads it back with "
      "`git cat-file -p stage-review/<name>-<n>:<path>`, never with git show, whose `--output` form creates the file "
      "empty (KP-067) (D4).")
P4 = ("Then list the remote branches, the default branch and its `HEAD` pointer apart, that have no open pull "
      "request: read them with `git branch -r`, after the fetch "
      "`sync-check.py` made, beside the open pull requests, `gh pr list --state open --limit 100`; delete each whose "
      "pull request merged (`gh pr list --state merged --head <branch>` names it) with `git push origin --delete "
      "<branch>`, as the delegation loop's step 8 deletes a merged branch, and name the others in the report, deleting "
      "none unasked (P4).")


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def procedure():
    return section(read(REFLECTION), "The procedure", 3)


def stage_step(n):
    """The stage review's step `n`, from its number to the next step's (step 8 to the demonstration)."""
    text = procedure()
    start = text.index("\n%d. " % n) + 1
    end = text.index("\n%d. " % (n + 1), start) if n < 8 else text.index("**Then the stage's demonstration runs live:**")
    return flat(text[start:end])


def test_r049_d1_every_driver_is_re_checked_at_head_before_a_stage_review():
    """D1: before the stage's diff is written, every live mutant applies exactly once at HEAD, one that does not
    re-anchored and run again, its kill counting only from that run; a fix that moves product code re-anchors or re-runs
    the drivers on the moved file in its own pull request; one test per named surface."""
    step = stage_step(2)
    assert step.startswith("2. " + D1 + " " + STEP2_DIFF), step[:300]
    assert flat(D1) not in flat(read(REFACTOR))


def test_r049_d2_every_stage_review_part_is_bounded_alike():
    """D2: a test part at most 25 files, a product part per package, a drivers-and-records part per driver family; a
    part without a verdict, of any kind, run again on what it had not reached."""
    step = stage_step(4)
    assert (D2 + " " + D2_UNION) in step, step
    assert "the test files' part at most 25 files" not in step


def test_r049_d3_the_live_stack_the_rebuild_run_sheet_and_the_harness():
    """D3: the demonstration's paragraph: the live stack with the schema check from a stage's first increment that adds
    tables, the development database's rebuild run sheet before the demonstration, the harness at the entry points."""
    text = procedure()
    para = text[text.index("**Then the stage's demonstration runs live:**"):text.index("\n1. **Issues.**")]
    assert flat(para).endswith(" " + D3), flat(para)[-400:]


def test_r049_d4_the_stage_review_tag_before_the_branch_is_deleted():
    """D4: step 8 tags the stage branch's head `stage-review/<name>-<n>` before `git branch -D stage/<name>`, a local tag
    never pushed; a record cites `<tag>:<path>` and reads it with `git cat-file -p`, never `git show` (KP-067)."""
    step = stage_step(8)
    assert step == D4, step
    assert step.index("`git tag stage-review/<name>-<n>`") < step.index("`git branch -D stage/<name>`")
    assert "`git show" not in step


def test_r049_p4_item_5_lists_the_remote_branches_and_deletes_the_merged_ones():
    """P4's text half: item 5 reads the remote branches after the fetch, beside the open pull requests, and deletes the
    merged ones with the remote delete step 8 uses, after the sync check."""
    text = procedure()
    item5 = flat(text[text.index("\n5. **Record**"):text.index("\n6. **Then, at a stage close")])
    assert item5.endswith(" " + P4), item5[-500:]
    assert item5.index("`python ~/.claude/cursor-bridge/sync-check.py --apply`") < item5.index("`git branch -r`")
