"""R-045, R-046 (release T, TASK-038): the merge step in its own sub-file, the merge mechanics, and where reviewers
write.

enforces: docs/REQUIREMENTS.md R-045, R-046; docs/BUILD_PLAN.md TASK-038, Done when (a) to (d); docs/DESIGN.md, Change:
release T (the table of what changes, rows R-045 and R-046).

One test per item label of the two rows (R-045: T4, T8, P7, P5, P4, T11 with T17; R-046: T5, T16, T25, T2), each pinning
its sentence in the home the design's table names, and one for each of Done when (a) and (c): step 8 in its sub-file,
and the three allow rules with the commands they admit. KP-052: the one non-ASCII character these pins need, the em
dash, is built with chr(), never typed."""
import json
import os
import re

from permission_rules import rule_matches

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge")
CB = os.path.join(BRIDGE, "cursor-bridge")
PHASES = os.path.join(CB, "workflow", "phases")
LOOP = os.path.join(PHASES, "delegation-loop.md")
MERGE = os.path.join(PHASES, "delegation-loop", "merge.md")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
HOOK = os.path.join(CB, "session-start.py")
POLICY = os.path.join(CB, "Merge-Verification-Policy.md")
DESIGN = os.path.join(PHASES, "design.md")
REFLECTION = os.path.join(PHASES, "reflection.md")
REVIEWER = os.path.join(BRIDGE, "agents", "diff-reviewer.md")
SENTINEL = os.path.join(BRIDGE, "agents", "secret-sentinel.md")
SETTINGS = os.path.join(CB, "settings.bridge.json")
EM = chr(0x2014)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def flat(text):
    return re.sub(r"\s+", " ", text)


def section(text, title):
    """The section under the heading `title`, up to the next heading of its level or higher; a line inside a fenced
    block is no heading."""
    lines = text.split("\n")
    fenced, start, level = False, None, 0
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fenced = not fenced
            continue
        m = None if fenced else re.match(r"(#+) (.*)$", line)
        if m and start is None and m.group(2) == title:
            start, level = i + 1, len(m.group(1))
        elif m and start is not None and len(m.group(1)) <= level:
            return "\n".join(lines[start:i])
    assert start is not None, "heading %r" % title
    return "\n".join(lines[start:])


def step8():
    return flat(section(read(MERGE), "8. Merge (the verified gate)"))


def rule(n):
    rules = section(read(CORE), "Standing rules")
    start = re.search(r"^%d\. " % n, rules, re.M).start()
    end = re.search(r"^%d\. " % (n + 1), rules, re.M).start()
    return flat(rules[start:end])


def design_prompt(text):
    """The design critique's constant prompt: the quoted argument of its one design-mode launch."""
    lines = [line for line in text.split("\n") if "cursor-agent -p --mode=ask --trust" in line]
    assert len(lines) == 1, lines
    return lines[0]


def test_r045_a_step_8_stands_in_its_own_sub_file():
    """Done when (a): step 8 moved into delegation-loop/merge.md, the module keeping a pointer where it stood and
    naming the sub-file third on its `Sub-files:` line."""
    loop = read(LOOP)
    assert "\nSub-files: delegation-loop/decide.md; delegation-loop/refactoring-pass.md; delegation-loop/merge.md\n" in loop
    assert "### 8. Merge (the verified gate)" not in loop
    assert ("### 8. Merge " + EM + " in a sub-file\n\nStep 8, the verified gate, from the review files and Review B's "
            "snapshot to the merge and the healthy marks after it, stands in the sub-file `delegation-loop/merge.md` "
            "(\"The procedure\" names it), read whole with this module.") in loop
    merge = read(MERGE)
    assert merge.startswith("## The merge (Phase 6, step 8)\n\n### Where this sub-file belongs\n\n")
    assert merge.count("### 8. Merge (the verified gate)") == 1


def test_r045_t4_the_title_form():
    """T4: a pull request that merges no increment ends its title with bare IDs in parentheses; the `Merges:` trailer
    form holds only where the squash message is the description (step 8 and the policy's invocation)."""
    assert flat(" A pull request that merges no increment (records, a design, a fix of the records) starts its title with its kind (`Records:`, `Design:`) and ends it with the bare requirement or issue IDs it carries in parentheses, the one form every squash setting keeps, never a plan increment's ID there, which the squash reader would take as merged (ISS-013). The `Merges:` trailer form holds only where the repository's squash message is the pull request's description: where it is the commit messages, GitHub's default and the bridge's own repository's (read 2026-11-01), the trailer never reaches `main`, so the title form is the rule (T4).") in step8()
    assert flat("\n**The merge's own commands.** Pushes and the merge run bare (`git push`, `gh pr merge <n> --squash --match-head-commit <sha>`), never piped, chained or wrapped: the allow rules and the permission guard read a command as written (rule 8, T8). A pull request's title starts with every increment ID it merges; one that merges none starts with its kind and ends with its bare requirement or issue IDs in parentheses, never a plan increment's ID there (ISS-013), and the `Merges:` trailer form holds only where the repository's squash message is the pull request's description (T4; the delegation loop's step 8, `~/.claude/cursor-bridge/workflow/phases/delegation-loop/merge.md`).\n").strip() in flat(section(read(POLICY), "Invocation"))


def test_r045_t8_push_and_merge_bare():
    """T8: every push and the merge run bare (step 8)."""
    assert flat(' The same holds for every push and for the merge: `git push` and `gh pr merge` run bare, never piped, chained or wrapped (rule 8, T8).') in step8()


def test_r045_p7_the_suite_with_the_pull_request_variables():
    """P7: before the first push of a status-file change, the suite with the pull request's variables, in the documented
    form, `<n>` predicted by the two reads."""
    assert flat("**Before every push, and before the first push of a status-file change.** Every commit the push publishes (`origin/<the base>..HEAD`) is read for computer paths and account names first, `secret-sentinel` scanning those commits on request: a leak in a commit not yet pushed is removed from that commit, by rewriting it before the push, never covered by a later commit (P5). And before the first push of a pull request that changes the status file, `project.json` or a `VERSION`, the full suite runs once with the pull request's variables set, as CI runs it on the pull request's merge: `python ~/.claude/cursor-bridge/bridge-run.py --limit auto --key-file <a file outside the Workspace> --kind test -- python -m pytest -q tests`, its output to `run/agent/<ID>-suite.out`, in the background under the heavy launch's `timeout` (`delegation-loop.md`, step 3), the key file holding the three lines `GITHUB_REF=refs/pull/<n>/merge`, `GITHUB_BASE_REF=main` and `GITHUB_EVENT_NAME=pull_request` (the launcher applies a file of `NAME=value` lines; an environment prefix before `python` would match no allow rule). `<n>` is the number the pull request will take, predicted as the next the repository issues, one above its latest pull request or issue (`gh pr list --state all --limit 1`, `gh issue list --state all --limit 1`), the number the branch's status file writes on its Last accepted line for that pull request (ISS-009); where GitHub issues another, the status file takes the real number and the run is repeated with it (P7).\n\n").strip() in step8()
    assert ("`python ~/.claude/cursor-bridge/bridge-run.py --limit auto --key-file <a file outside the Workspace> --kind "
            "test -- python -m pytest -q tests`") in read(MERGE)


def test_r045_p5_every_pushed_commit_scanned():
    """P5: every commit a push publishes is read for computer paths and account names, a leak removed from the commit
    (step 8 and secret-sentinel)."""
    assert "a leak in a commit not yet pushed is removed from that commit, by rewriting it before the push, never covered by a later commit (P5)" in step8()
    assert flat('\n**Before a push, every commit it publishes.** When the supervisor asks before a push, scan every commit the push publishes (`git log -p <the base>..HEAD`), not only the staged diff, for those paths and for the account names the supervisor gives you: a commit not yet pushed is rewritten to remove the leak, never covered by a later commit, so report each by its commit and line (P5).\n').strip() in flat(read(SENTINEL))


def test_r045_p4_the_merged_branch_deleted_and_the_armed_form_skipped():
    """P4's text: the armed form skipped where the repository refuses auto-merge; the merged branch deleted locally and
    on the remote with the two bare commands."""
    assert flat(', or, where the repository refuses auto-merge (its `allow_auto_merge` setting off), skip the armed form, the direct merge after the green watch being the merge,') in step8()
    assert flat(' Then delete the merged branch, locally and on the remote, each command bare: `git branch -D <branch>`, then `git push origin --delete <branch>` (P4).') in step8()


def test_r045_t11_t17_the_status_file_as_at_the_merge():
    """T11 and T17: the status file as at the merge, the live position in in-flight.md, an overtaken pull request
    rewritten and re-reviewed (rule 43, the template, the hook's text, step 8)."""
    assert flat("write it in `run/supervisor/in-flight.md`, where the live position between merges lives: the status file a pull request carries reads as at that pull request's merge, its `In flight:` line `none` (ISS-009, KP-069), and a resume reads `in-flight.md`'s last entries first") in rule(43)
    assert flat(" A pull request whose status file another pull request's merge overtook has the file rewritten as at its own merge and `main` merged into it, a new head the reviews read again (the delegation loop's step 8).") in rule(43)
    assert "copied to the status file after `verify`" not in rule(43)
    assert 'In flight: <none (the file a pull request carries reads as at its merge; between merges the live position is in run/supervisor/in-flight.md) | TASK-nnn in <checkout> since <time>;' in read(CORE)
    hook = read(HOOK)
    first = hook.index('out.append("Then read docs/PROJECT_STATUS.md and docs/INVENTORY.md whole (rule 41).")')
    assert hook.index('out.append(' + '"The status file reads as at its last merge (ISS-009): where run/supervisor/in-flight.md exists, read its last entries first, the live position between merges."' + ')') > first
    assert flat(" So is a pull request whose status file another pull request's merge overtook: the file a pull request carries reads as at that pull request's merge (ISS-009, KP-069), so where another merged first the branch rewrites it as at its own merge and merges `main`, and the reviews read the new head again (T11, T17).") in step8()


def test_r045_c_the_three_allow_rules_and_the_commands_they_admit():
    """Done when (c): `Bash(git branch -D:*)` beside the narrower stage rule, which stays, and the two reads for P7's
    prediction; each documented command is admitted, the remote delete on the existing `Bash(git push:*)`."""
    allow = json.loads(read(SETTINGS))["permissions"]["allow"]
    for r in ("Bash(git branch -D stage/*)", "Bash(git branch -D:*)", "Bash(gh pr list:*)", "Bash(gh issue list:*)",
              "Bash(git push:*)"):
        assert r in allow, r
    for cmd in ("git branch -D task-038", "git push origin --delete task-038", "gh pr list --state all --limit 1",
                "gh issue list --state all --limit 1"):
        assert any(rule_matches(r, cmd) for r in allow), cmd
    merge = read(MERGE)
    for cmd in ("`git branch -D <branch>`", "`git push origin --delete <branch>`", "`gh pr list --state all --limit 1`",
                "`gh issue list --state all --limit 1`"):
        assert cmd in merge, cmd


def test_r046_t5_where_a_reviewer_may_write():
    """T5: the directive's clause, the policy's invocation, the design critique's constant prompt (its two copies one
    text) and the reviewer's definition say where a reviewer may write and that it edits nothing."""
    assert "with five short clauses (release A5; where a reviewer writes, release T)" in step8()
    assert "a sixth clause: grade every" in step8() and "a fifth clause" not in step8()
    assert flat('write no file under the checkout and point no cache there, scratch files and test caches going to the system temporary folder, and edit nothing (what `verify` restores was still written, and a write under `docs/`, `handoff/` or `run/review/` is a flag);') in step8()
    assert flat('that the reviewer writes no file under the checkout and points no cache there, its scratch files and test caches going to the system temporary folder, and edits nothing,') in flat(section(read(POLICY), "Invocation"))
    prompt = design_prompt(read(DESIGN))
    assert "Write no file under the checkout, point no cache there, and edit nothing." in prompt
    assert design_prompt(read(POLICY)) == prompt
    assert flat('You write no file under the checkout and point no cache there: a scratch file or a test cache goes to the system temporary folder (pytest run with `-p no:cacheprovider`), so the tree is as you found it.') in flat(read(REVIEWER))


def test_r046_t16_single_test_files_beside_review_b():
    """T16: a part reviewed while Review B runs runs single test files at most, its mutation runs on a copy outside the
    checkout (the stage review's step 4, and step 8's read-only subagents)."""
    stage = flat(read(REFLECTION))
    assert "a part read while Review B runs (step 5) runs single test files at most, never the suite, and any mutation run on a copy outside the checkout" in stage
    assert flat(", each running single test files at most, never the suite, and any mutation run on a copy outside the checkout, as `mutation-run.py` makes one, since the reviewer's own run shares the checkout's databases, ports and caches (T16)") in step8()


def test_r046_t25_each_parts_turn_budget():
    """T25: each stage-review part's prompt names its turn budget and keeps the last turns for the verdict (step 4)."""
    assert flat(" Each part's prompt names its turn budget (the reviewer's `maxTurns`) and keeps the last turns for the verdict, so a part that runs short still answers (T25); a part read while Review B runs (step 5) runs single test files at most, never the suite, and any mutation run on a copy outside the checkout, so it shares nothing of the checkout with the reviewer's own run (T16).").strip() in flat(read(REFLECTION))


def test_r046_t2_a_clean_reply_names_three_verified_statements():
    """T2: a design critic's reply with no finding names three statements it verified, each with a short quotation, and
    the receipt check reads them; the reviewer's clean APPROVE does the same."""
    design = read(DESIGN)
    assert flat(' A reply with no finding names three statements of the file it verified, each with a short quotation, and the check reads them against the file: fewer than three, or a quotation the file does not hold, is a failed launch too (T2).').strip() in flat(design)
    assert flat('; where you find nothing, name instead three statements of the file you verified, each with a short quotation from it. Write no file under the checkout, point no cache there, and edit nothing.').strip("; ") in design_prompt(design)
    assert flat('An `APPROVE` with no finding in any section names, under NOTED, three statements of the diff you verified, each with a short quotation and the file and line it stands at, so the supervisor can see the diff was read; a clean reply with none is read as no review.') in flat(read(REVIEWER))


def test_policy_design_mode_the_failed_launch_as_design_md_words_it():
    """The policy's design-mode paragraph, widened from its "Invocation" region (TASK-037's HARDENING lead): a failed
    last launch leaves Review B's row `not run (<the reason>)`, as design.md says, never "the round stays not run"."""
    policy = flat(read(POLICY))
    assert "if that fails too, Review B's row stays `not run (<the reason>)` and the subject goes on" in policy
    assert "the round stays not run" not in policy
