"""TASK-086a (R-107; docs/DESIGN.md, "Change: the improvements release", C39 and its ten-row table): the roster
resolves an alternate reviewer from the families that built a branch. The supervisor's acceptance tests, written
before the brief and committed before the checkpoint.

Every test builds what it needs under pytest's temporary folder: a scratch git repository (a `main` with one commit
and a `.gitignore` that ignores `run/`, as the project's own does, and a branch `task-1`), a `docs/ROSTER.json`
written by the test, the roster's state file under the repository's git common dir (`.git/bridge/roster-state.json`,
where the pool and the marks live), and the run record `run/launcher/runs.jsonl` written by the test as JSON lines.
A builder row has the launcher's shape (`kind` builder, `model`, `branch`, `brief` the brief's id, `round`,
`brief_name`) and, where the test gives them, TASK-086b's two keys `start_commit` and `clean`; a row written before
this release carries neither. A report file is a file under `handoff/` whose name ends `-report.md`
(`handoff/TASK-001-r1-report.md` belongs to brief TASK-001, round 1). `roster-check.py` is always run with
`--no-probe` (the one probe test replaces `probe` in the imported module), with `ROSTER_NOW` fixed, from the scratch
repository, every git variable of the suite's own environment removed.

The tests read the program's lines by these words: a resolve on an unknown set prints its cause on a line of its own
that holds the word `unknown` and the name of what caused it (`runs.jsonl` for a line of the record that does not
parse, the report file's name for a report without its row); a set that cannot be read names `detached`, the
record's file name, `git`, or `main`; the REBUILD line names `--repair-record` for a line that does not parse,
`checkpoint` for a report without its row, and `new branch` where the same-branch rebuild cannot drop a counted row
(and only there); an alternate resolved prints a line that begins `DEVIATION`. The repair is run as
`roster-check.py docs/ROSTER.json --repair-record`, the alternate on request as
`roster-check.py docs/ROSTER.json --review-alt <reason>`, the roster's path first as every other mode takes it.

enforces: docs/BUILD_PLAN.md, TASK-086a, Done when; docs/REQUIREMENTS.md R-107; docs/DESIGN.md C39 and its table
"""
import itertools
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

import conftest as test_conftest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "roster-check.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
       "-c", "commit.gpgsign=false"]

NOW = "2026-11-24T09:00"
MARK = "2026-11-24T08:30 UTC: 2 consecutive failures -- x"
BRANCH = "task-1"
REPORT1 = "handoff/TASK-001-r1-report.md"
REPORT2 = "handoff/TASK-001-r2-report.md"

REVIEW_A = "claude-opus-5-5"        # anthropic, Review A's family
GROK_B = "grok-4.7-high"            # xai, native pool
GROK_R = "grok-4.7-medium"          # xai, native pool
COMPOSER = "composer-2.5"           # cursor, native pool
GPT = "gpt-5.6-sol-high"            # openai, other pool
CLAUDE_ALT = "claude-sonnet-5"      # anthropic: Review A's family, never independent

FULL = {"name": "full", "builder": GROK_B, "review_b": GPT}
NATIVE = {"name": "native", "builder": COMPOSER, "review_b": GROK_R}

_ids = itertools.count(1)


# --- helpers -------------------------------------------------------------------------------------

def _env(**extra):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env["ROSTER_NOW"] = NOW
    env.update(extra)
    return env


def _kw(**extra):
    base = {"capture_output": True, "text": True, "timeout": 60, "env": _env()}
    base.update(extra)
    return test_conftest.windowless_kwargs(base)


def git(ws, *args):
    p = subprocess.run(GIT + list(args), cwd=str(ws), **_kw())
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def write(ws, rel, text):
    path = ws / rel.replace("/", os.sep)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def scratch_repo(tmp_path, main=True, base_files=None):
    """A git repository with `main` (one commit: the `.gitignore` and any `base_files`) and the branch `task-1`
    checked out; with main=False the repository is made on `task-1` alone and has no `main`."""
    ws = tmp_path / "ws"
    ws.mkdir()
    git(ws, "init", "-q", "-b", "main" if main else BRANCH)
    write(ws, ".gitignore", "run/\n")
    git(ws, "add", ".gitignore")
    for rel, text in (base_files or {}).items():
        write(ws, rel, text)
        git(ws, "add", "--", rel)
    git(ws, "commit", "-q", "-m", "base")
    if main:
        git(ws, "checkout", "-q", "-b", BRANCH)
    return ws


def commit(ws, msg, files=None, remove=None):
    for rel, text in (files or {}).items():
        write(ws, rel, text)
        git(ws, "add", "--", rel)
    for rel in remove or ():
        git(ws, "rm", "-q", "--", rel)
    git(ws, "commit", "-q", "--allow-empty", "-m", msg)
    return git(ws, "rev-parse", "HEAD")


def write_roster(ws, profiles, other_pool="available", unavailable=(), in_repo=True):
    write(ws, "docs/ROSTER.json", json.dumps({"other_pool": other_pool, "review_a": REVIEW_A, "profiles": profiles},
                                             indent=2) + "\n")
    if in_repo:
        state = {"other_pool": other_pool}
        if other_pool == "exhausted":
            state.update(exhausted_at="2026-11-24T08:00 UTC", exhausted_reason="owner said usage exhausted")
        if unavailable:
            state["unavailable"] = {m: MARK for m in unavailable}
        write(ws, ".git/bridge/roster-state.json", json.dumps(state, indent=2) + "\n")


def row(model, branch=BRANCH, start=None, clean=None, brief="TASK-001", rnd=1, slot=None):
    """A builder row as the launcher writes it; `start_commit` and `clean` only where given."""
    e = {"id": "r%d" % next(_ids), "kind": "builder", "head": "cursor-agent", "model": model, "branch": branch,
         "limit": 7200, "seconds": 100, "exit": 0, "healthy": True}
    if brief:
        e.update(brief=brief, round=rnd, brief_name=brief if rnd == 1 else "%s-r%d" % (brief, rnd))
    if start is not None:
        e["start_commit"] = start
    if clean is not None:
        e["clean"] = clean
    if slot:
        e.update(slot=slot, exit=123, seconds=0, healthy=None, waited=7320)
    return json.dumps(e)


def review_row(model=GPT, branch=BRANCH):
    return json.dumps({"id": "v%d" % next(_ids), "kind": "review", "head": "cursor-agent", "model": model,
                       "branch": branch, "limit": 3600, "seconds": 10, "exit": 0, "healthy": True})


def record_path(ws):
    return ws / "run" / "launcher" / "runs.jsonl"


def write_record(ws, *lines):
    path = record_path(ws)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")


def append_record(ws, *lines):
    with open(str(record_path(ws)), "a", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(line + "\n")


def resolve(ws, *args, **env_extra):
    p = subprocess.run([sys.executable, PROG, "docs/ROSTER.json", "--no-probe"] + list(args), cwd=str(ws),
                       **_kw(env=_env(**env_extra)))
    return p.returncode, p.stdout + p.stderr


def resolved_path(ws):
    return ws / "docs" / "ROSTER.resolved.json"


def resolved(ws):
    return json.loads(resolved_path(ws).read_text(encoding="utf-8"))


SENTINEL = '{"sentinel": "the resolved file as it stood before the run"}\n'


def plant_resolved(ws):
    write(ws, "docs/ROSTER.resolved.json", SENTINEL)
    return resolved_path(ws).read_bytes()


def rebuild_text(out):
    return "\n".join(line for line in out.splitlines() if "REBUILD" in line)


def deviation_printed(out):
    return any(line.strip().startswith("DEVIATION") for line in out.splitlines())


def unknown_cause(out, needle):
    """The lines of their own that name an unknown set's cause: the word `unknown` and `needle`."""
    return [line for line in out.splitlines()
            if "unknown" in line.lower() and needle in line
            and not line.strip().startswith(("REBUILD", "RESOLVED", "DEVIATION"))]


def any_unknown_line(out):
    return [line for line in out.splitlines() if "unknown" in line.lower()]


def assert_rebuild(ws, rc, out, builder=COMPOSER):
    assert rc == 0 and "REBUILD" in out, out
    data = resolved(ws)
    assert sorted(data.get("rebuild") or {}) == ["built_by", "rebuild_with"], data
    assert data["rebuild"]["rebuild_with"] == builder, data
    assert "deviation" not in data and not deviation_printed(out), out


def assert_deviation(ws, rc, out, alt, reason, built):
    assert rc == 0, out
    assert "REBUILD" not in out, out
    assert deviation_printed(out), out
    data = resolved(ws)
    dev = data.get("deviation")
    assert isinstance(dev, dict), data
    assert {"review_b_alt", "reason", "branch", "built"} <= set(dev), dev
    assert dev["review_b_alt"] == alt and dev["reason"] == reason and dev["branch"] == BRANCH, dev
    assert set(dev["built"]) == set(built), dev
    assert data["review_b"] == alt, data
    assert "rebuild" not in data, data


def assert_review_b(ws, rc, out, review_b):
    assert rc == 0 and "REBUILD" not in out and not deviation_printed(out), out
    data = resolved(ws)
    assert data["review_b"] == review_b and "rebuild" not in data and "deviation" not in data, data


def assert_cannot_read(ws, rc, out, before, needle):
    assert rc == 1, out
    assert re.search(r"\b%s\b" % re.escape(needle), out.lower()), "the cause named (%s): %s" % (needle, out)
    assert "REBUILD" not in out and "RESOLVED" not in out, out
    assert resolved_path(ws).read_bytes() == before, "the resolved file is left unchanged"


def lies_in_no_repository(path):
    p = os.path.abspath(str(path))
    while True:
        if os.path.exists(os.path.join(p, ".git")):
            return False
        parent = os.path.dirname(p)
        if parent == p:
            return True
        p = parent


# --- the built set's histories ---------------------------------------------------------------------

def test_task086a_one_family_is_the_built_set(tmp_path):
    """TASK-086a Done when: "the histories are held by tests: one family"; "every builder row of the branch counts";
    and the same-branch REBUILD names no new branch where the rebuild from the first counted row's `start_commit`
    drops every counted row."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    write_record(ws, review_row(), row(GROK_B, start=c1, clean=True))
    commit(ws, "the builder's work")
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)
    assert "new branch" not in rebuild_text(out).lower(), out


def test_task086a_a_rebuild_from_the_checkpoint_leaves_the_rebuilding_family_alone(tmp_path):
    """TASK-086a Done when: "a row is dropped only where a later builder row of the branch reads `clean` true and a
    `start_commit` that is the row's own `start_commit` or an ancestor of it, by git's own answer"; "a rebuild from
    the checkpoint by another model, which leaves that model's family alone"; "`clean` is read as TASK-086b writes
    it, the resolved roster file apart" (the tree is dirty when the program runs, the rows say clean)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    commit(ws, "the first run's work")
    git(ws, "reset", "-q", "--hard", c1)
    append_record(ws, row(COMPOSER, start=c1, clean=True))
    commit(ws, "the rebuild's work")
    write(ws, "notes.txt", "an untracked file the program never reads for clean\n")
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GROK_R)
    assert not any_unknown_line(out), out


@pytest.mark.parametrize("case", ["tree-not-clean", "descendant-commit", "fix-round", "report-deleted"])
def test_task086a_a_later_run_that_is_no_rebuild_counts_both_families(tmp_path, case):
    """TASK-086a Done when: "the same second run on a tree that was not clean, and on a commit that descends from
    the first run's, where both count; a fix round by another family, where both count; a clean second run on a
    later commit after the first run's report was deleted, where both count"; "no report file enters the test"
    (red on the checkpoint, which reads the last builder run alone)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    first = row(GROK_B, start=c1, clean=True)
    if case == "tree-not-clean":
        commit(ws, "the first run's work")
        second = row(COMPOSER, start=c1, clean=False)
    elif case == "descendant-commit":
        c2 = commit(ws, "the first run's work")
        second = row(COMPOSER, start=c2, clean=True)
    elif case == "fix-round":
        c2 = commit(ws, "the first run's work", files={REPORT1: "round 1\n"})
        second = row(COMPOSER, start=c2, clean=True, rnd=2)
        commit(ws, "the fix round's work", files={REPORT2: "round 2\n"})
    else:
        commit(ws, "the first run's work", files={REPORT1: "round 1\n"})
        c3 = commit(ws, "the first run's report deleted", remove=[REPORT1])
        second = row(COMPOSER, start=c3, clean=True)
    write_record(ws, first, second)
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)
    assert "new branch" not in rebuild_text(out).lower(), "every counted row starts at or after the checkpoint: " + out
    assert not any_unknown_line(out), out


def test_task086a_two_briefs_on_one_branch_the_second_rebuilt_keep_the_first_briefs_family(tmp_path):
    """TASK-086a Done when: "every builder row of the branch counts, whatever brief it names"; "two briefs on one
    branch, the second rebuilt, where the first brief's family stays" (the alternate's `built` shows the set: the
    first brief's family and the rebuilding one, the rebuilt run's dropped)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [{"name": "native", "builder": COMPOSER, "review_b": GPT, "review_b_alt": GROK_R}])
    rows = [row(GPT, start=c1, clean=True, brief="TASK-001")]
    c2 = commit(ws, "the first brief's work")
    rows.append(row(GROK_B, start=c2, clean=True, brief="TASK-002"))
    commit(ws, "the second brief's work")
    git(ws, "reset", "-q", "--hard", c2)
    rows.append(row(COMPOSER, start=c2, clean=True, brief="TASK-002"))
    commit(ws, "the second brief rebuilt")
    write_record(ws, *rows)
    rc, out = resolve(ws)
    assert_deviation(ws, rc, out, GROK_R, "family", {"openai", "cursor"})


@pytest.mark.parametrize("start", [None, "deadbeef" * 5], ids=["no-start-commit", "start-names-no-commit"])
def test_task086a_a_row_git_cannot_place_before_a_rebuild_stays_counted_and_the_rebuild_takes_a_new_branch(tmp_path, start):
    """TASK-086a Done when: "a row without `start_commit`, or whose `start_commit` names no commit of the repository,
    is never dropped"; "a row without `start_commit` before a rebuild, which stays counted, the REBUILD line naming
    the rebuild under a new branch name, and that new branch reading the rebuilding family alone"; "the form standing
    in the printed line alone and the resolved file's `rebuild` entry keeping its two keys"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    commit(ws, "the first run's work")
    write_record(ws, row(GROK_B, start=start), row(COMPOSER, start=c1, clean=True))
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)
    assert "new branch" in rebuild_text(out).lower(), out
    git(ws, "checkout", "-q", "-b", "task-1-rebuilt", c1)
    append_record(ws, row(COMPOSER, branch="task-1-rebuilt", start=c1, clean=True))
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GROK_R)


@pytest.mark.parametrize("start", [None, "deadbeef" * 5], ids=["no-start-commit", "start-names-no-commit"])
def test_task086a_a_row_git_cannot_place_drops_nothing(tmp_path, start):
    """TASK-086a Done when: "a row without `start_commit`, or whose `start_commit` names no commit of the repository,
    is never dropped and drops nothing"; the REBUILD line names "the same rebuild under a new branch name" for a
    counted row with no `start_commit` or one that names no commit."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    commit(ws, "the first run's work")
    write_record(ws, row(GROK_B, start=c1, clean=True), row(COMPOSER, start=start, clean=True))
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)
    assert "new branch" in rebuild_text(out).lower(), out


def test_task086a_a_branch_rebased_between_two_runs_is_rebuilt_under_a_new_branch(tmp_path):
    """TASK-086a Done when: "a branch rebased between two runs, whose REBUILD line names the new-branch form too";
    a counted row whose `start_commit` "is neither the first counted row's nor a descendant of it"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint, first form")
    write_roster(ws, [NATIVE])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    commit(ws, "the first run's work")
    git(ws, "reset", "-q", "--hard", "main")
    c1b = commit(ws, "checkpoint, rebased form")
    append_record(ws, row(COMPOSER, start=c1b, clean=True))
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)
    assert "new branch" in rebuild_text(out).lower(), out


def test_task086a_a_row_whose_launch_never_got_the_slot_never_counts(tmp_path):
    """TASK-086a Done when: "a row marked `slot not free` never" counts."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    write_record(ws, row(GROK_B, start=c1, clean=True, slot="not free"))
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GROK_R)


def test_task086a_a_row_without_a_brief_always_counts(tmp_path):
    """TASK-086a Done when: "every builder row of the branch counts, whatever brief it names ... a row without a
    brief always"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    write_record(ws, row(GROK_B, start=c1, clean=True, brief=None))
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)


def test_task086a_a_folder_in_no_repository_has_the_empty_set(tmp_path):
    """TASK-086a Done when: "in a folder that lies in no repository, neither it nor a folder above it holding a
    `.git` entry, the set is the empty one, as on the checkpoint"; the history "a folder in no repository"."""
    if not lies_in_no_repository(tmp_path):
        pytest.skip("the temporary folder lies inside a git repository on this computer")
    ws = tmp_path / "plain"
    ws.mkdir()
    write_roster(ws, [NATIVE], in_repo=False)
    write_record(ws, row(GROK_B, start="deadbeef" * 5, clean=True), row(GROK_B, branch=None))
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GROK_R)
    assert not any_unknown_line(out), out


def test_task086a_a_repository_without_main_and_without_a_report_resolves_as_on_the_checkpoint(tmp_path):
    """TASK-086a Done when: "a tree that holds no report file needs no base, so a repository without `main` that
    holds none resolves as on the checkpoint"; the history "a repository without `main` and without a report file";
    "every existing roster test stands unedited, those whose repository has no `main` and holds no report file"."""
    ws = scratch_repo(tmp_path, main=False)
    c1 = git(ws, "rev-parse", "HEAD")
    write_roster(ws, [FULL, NATIVE], other_pool="exhausted")
    write(ws, "handoff/TASK-001.md", "a brief is no report\n")
    rc, out = resolve(ws)
    assert rc == 0 and "RESOLVED profile 'native'" in out, out
    assert_review_b(ws, rc, out, GROK_R)
    write_record(ws, row(GROK_R))
    rc, out = resolve(ws)
    assert "RESOLVED profile 'native'" in out, out
    assert_rebuild(ws, rc, out)
    write_record(ws, row(GROK_R, start=c1, clean=True), row(COMPOSER, start=c1, clean=True))
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GROK_R)


# --- the two causes of an unknown set ----------------------------------------------------------------

def test_task086a_a_record_line_that_does_not_parse_makes_the_set_unknown(tmp_path):
    """TASK-086a Done when: "where it can be read it is unknown where a line of the record does not parse"; "each of
    the two causes of an unknown set"; "every resolve on an unknown set printing the cause on a line of its own"
    (here it resolves `review_b`, whose family no builder of the roster file and no parsing row of the branch has)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [FULL])
    write_record(ws, row(GROK_B, start=c1, clean=True), '{"id": "torn", "kind": "builder", "model": "gr')
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GPT)
    assert unknown_cause(out, "runs.jsonl"), "the cause on a line of its own: " + out


@pytest.mark.parametrize("case", ["committed", "untracked", "no-record", "row-of-another-branch"])
def test_task086a_a_report_the_branch_adds_without_its_row_makes_the_set_unknown(tmp_path, case):
    """TASK-086a Done when: "it is unknown where ... a report file that the branch adds over that base has no builder
    row of the branch for its brief"; "a record that does not exist is an empty record, so ... one that adds a report
    an unknown one"; a report file is "committed or still in the working tree"; "every resolve on an unknown set
    printing the cause on a line of its own"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [FULL])
    commit(ws, "the first brief's work", files={REPORT1: "round 1\n"})
    other = "handoff/TASK-002-r1-report.md"
    if case == "untracked":
        write(ws, other, "a report never committed\n")
    else:
        commit(ws, "the second brief's report", files={other: "round 1\n"})
    if case == "no-record":
        git(ws, "rm", "-q", "--", REPORT1)
        commit(ws, "only the second brief's report stays")
    else:
        rows = [row(GROK_B, start=c1, clean=True, brief="TASK-001")]
        if case == "row-of-another-branch":
            rows.append(row(GROK_B, branch="task-9", start=c1, clean=True, brief="TASK-002"))
        write_record(ws, *rows)
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GPT)
    assert unknown_cause(out, "TASK-002-r1-report.md"), "the cause on a line of its own: " + out


def test_task086a_a_report_in_the_base_and_a_report_with_its_row_leave_the_set_known(tmp_path):
    """TASK-086a Done when: "a report file that the branch adds over that base has no builder row of the branch for
    its brief" is the cause, so a report already on `main` and a report with its row add none; "a resolve on a branch
    that needs no alternate writes no `deviation`"."""
    ws = scratch_repo(tmp_path, base_files={"handoff/TASK-000-r1-report.md": "an earlier increment's report\n"})
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(FULL, review_b_alt=COMPOSER)])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    commit(ws, "the brief's work", files={REPORT1: "round 1\n"})
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GPT)
    assert not any_unknown_line(out), out


# --- the four causes of a set that cannot be read ------------------------------------------------------

def test_task086a_a_detached_head_cannot_be_read(tmp_path):
    """TASK-086a Done when: "inside a repository the set cannot be read where the head is detached ...: the resolve
    then ends with exit 1 and the cause, the resolved file unchanged and no REBUILD printed"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    git(ws, "checkout", "-q", "--detach")
    before = plant_resolved(ws)
    rc, out = resolve(ws)
    assert_cannot_read(ws, rc, out, before, "detached")


def test_task086a_a_record_that_cannot_be_opened_cannot_be_read(tmp_path):
    """TASK-086a Done when: "the set cannot be read where ... the record exists and cannot be opened ...: the
    resolve then ends with exit 1 and the cause, the resolved file unchanged and no REBUILD printed" (the record is a
    folder of that name)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    record_path(ws).mkdir(parents=True)
    before = plant_resolved(ws)
    rc, out = resolve(ws)
    assert_cannot_read(ws, rc, out, before, "runs.jsonl")


def _git_that_does_not_answer(tmp_path, how):
    """A PATH on which `git` fails (a script that prints a fatal line and exits 128: an executable sh on POSIX, a
    .bat and a .cmd on Windows) or does not start (no git at all). The program finds git through PATH: it calls
    "git" by name. On Windows a program started by name without a shell is found as an .exe only, so the fake .bat
    stands for "does not start" there unless the program looks git up through PATHEXT, where it fails; either is a
    git that does not answer. The interpreter's own folder stays on PATH on Windows only, for its libraries."""
    fake = tmp_path / ("fake-git-" + how)
    fake.mkdir()
    if how == "fails":
        if sys.platform == "win32":
            for name in ("git.bat", "git.cmd"):
                (fake / name).write_text("@echo off\r\necho fatal: git is not answering 1>&2\r\nexit /b 128\r\n",
                                         encoding="ascii")
        else:
            script = fake / "git"
            script.write_text("#!/bin/sh\necho 'fatal: git is not answering' >&2\nexit 128\n", encoding="ascii")
            os.chmod(str(script), 0o755)
    path = str(fake)
    if sys.platform == "win32":
        path += os.pathsep + os.path.dirname(sys.executable)
    found = shutil.which("git", path=path)
    if found and not os.path.abspath(found).startswith(str(fake)):
        pytest.skip("a real git lies beside the interpreter: %s" % found)
    return path


@pytest.mark.parametrize("how", ["fails", "does-not-start"])
def test_task086a_git_that_does_not_answer_cannot_be_read(tmp_path, how):
    """TASK-086a Done when: "any other failure of git a set that cannot be read"; "inside a repository the set cannot
    be read where ... git does not answer (it does not start, times out or fails) ...: the resolve then ends with
    exit 1 and the cause, the resolved file unchanged and no REBUILD printed". The repository is found by its `.git`
    entry; git is replaced on PATH (see the helper)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    before = plant_resolved(ws)
    rc, out = resolve(ws, PATH=_git_that_does_not_answer(tmp_path, how))
    assert_cannot_read(ws, rc, out, before, "git")


@pytest.mark.parametrize("where", ["committed", "untracked"])
def test_task086a_a_report_without_a_base_cannot_be_read(tmp_path, where):
    """TASK-086a Done when: "the set cannot be read where ... the tree holds a report file (a file under `handoff/`
    whose name ends `-report.md`, committed or still in the working tree) and the branch's base cannot be found (its
    merge base with `origin/main`, or with `main` where the repository has no remote): the resolve then ends with
    exit 1 and the cause, the resolved file unchanged and no REBUILD printed"."""
    ws = scratch_repo(tmp_path, main=False)
    c1 = git(ws, "rev-parse", "HEAD")
    write_roster(ws, [NATIVE])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    if where == "committed":
        commit(ws, "the brief's work", files={REPORT1: "round 1\n"})
    else:
        write(ws, REPORT1, "round 1, not committed\n")
    before = plant_resolved(ws)
    rc, out = resolve(ws)
    assert_cannot_read(ws, rc, out, before, "main")


# --- the design's table, one test a row ------------------------------------------------------------

@pytest.mark.parametrize("record", ["none", "empty", "another-family", "another-branch"])
def test_task086a_table_row_1_review_b_where_its_family_did_not_build(tmp_path, record):
    """TASK-086a Done when: "the check resolves by the design's table, one test a row: `review_b` where the branch has
    no builder run or its family did not build"; "a record that does not exist is an empty record, so a branch that
    adds no report file has the empty set"; "a resolve on a branch that needs no alternate writes no `deviation`"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    if record == "empty":
        write_record(ws)
    elif record == "another-family":
        write_record(ws, row(COMPOSER, start=c1, clean=True))
    elif record == "another-branch":
        write_record(ws, row(GROK_B, branch="task-9", start=c1, clean=True))
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GROK_R)
    assert not any_unknown_line(out), out


def test_task086a_table_row_2_the_alternate_where_review_b_s_family_built(tmp_path):
    """TASK-086a Done when: "the alternate with a `deviation` entry (`review_b_alt`, `reason`, `branch`, `built`) and
    a DEVIATION line where `review_b`'s family built and the alternate's family is in neither the known built set nor
    Review A's, its pool not exhausted and unmarked (red on the checkpoint, which prints REBUILD)"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    commit(ws, "the builder's work")
    rc, out = resolve(ws)
    assert_deviation(ws, rc, out, GPT, "family", {"xai"})


@pytest.mark.parametrize("case", ["no-alternate", "alternate-family-built", "alternate-of-review-a",
                                  "alternate-pool-exhausted", "alternate-marked"])
def test_task086a_table_row_3_rebuild_where_no_alternate_is_independent_and_usable(tmp_path, case):
    """TASK-086a Done when: "REBUILD as on the checkpoint where `review_b`'s family built and no alternate is named,
    its family built, or its pool or a mark excludes it"; the design's row "none named, or not independent, or not
    usable"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    alt = {"no-alternate": None, "alternate-family-built": GPT, "alternate-of-review-a": CLAUDE_ALT,
           "alternate-pool-exhausted": GPT, "alternate-marked": GPT}[case]
    profile = dict(NATIVE, review_b_alt=alt) if alt else dict(NATIVE)
    write_roster(ws, [profile], other_pool="exhausted" if case == "alternate-pool-exhausted" else "available",
                 unavailable=[GPT] if case == "alternate-marked" else ())
    rows = [row(GROK_B, start=c1, clean=True)]
    c2 = commit(ws, "the first run's work")
    if case == "alternate-family-built":
        rows.append(row(GPT, start=c2, clean=True, rnd=2))
        commit(ws, "the fix round's work")
    write_record(ws, *rows)
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)


@pytest.mark.parametrize("case", ["pool", "mark"])
def test_task086a_table_row_4_the_alternate_where_review_b_is_unavailable(tmp_path, case):
    """TASK-086a Done when: "the alternate with the reason `unavailable` where the set is known, a mark or its pool
    excludes `review_b` and the alternate is independent and usable (red on the checkpoint, which skips the
    profile)"."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    if case == "pool":
        write_roster(ws, [dict(FULL, review_b_alt=COMPOSER)], other_pool="exhausted")
        alt = COMPOSER
    else:
        write_roster(ws, [dict(NATIVE, review_b_alt=GPT)], unavailable=[GROK_R])
        alt = GPT
    rc, out = resolve(ws)
    assert_deviation(ws, rc, out, alt, "unavailable", set())


@pytest.mark.parametrize("case", ["no-alternate", "alternate-of-review-a", "alternate-family-built",
                                  "alternate-not-usable", "set-unknown"])
def test_task086a_table_row_5_the_profile_skipped_where_no_rebuild_removes_the_cause(tmp_path, case):
    """TASK-086a Done when: "the profile skipped as on the checkpoint, never a REBUILD, where a mark or its pool
    excludes `review_b` and no alternate is independent and usable"; "with the set unknown, the alternate never
    resolved: ... the profile skipped where a mark or its pool excludes it"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    alt = {"no-alternate": None, "alternate-of-review-a": CLAUDE_ALT, "alternate-family-built": GPT,
           "alternate-not-usable": GPT, "set-unknown": GPT}[case]
    profile = dict(NATIVE, review_b_alt=alt) if alt else dict(NATIVE)
    write_roster(ws, [profile], other_pool="exhausted" if case == "alternate-not-usable" else "available",
                 unavailable=[GROK_R])
    if case == "no-alternate":
        write_record(ws, row(GROK_B, start=c1, clean=True))
    elif case == "alternate-family-built":
        write_record(ws, row(GPT, start=c1, clean=True))
    elif case == "set-unknown":
        write_record(ws, review_row(), '{"id": "torn", "kind": "build')
    before = plant_resolved(ws)
    rc, out = resolve(ws)
    assert rc == 1 and "skip" in out and "RESOLVED" not in out, out
    assert "REBUILD" not in out and not deviation_printed(out), out
    assert resolved_path(ws).read_bytes() == before
    if case == "set-unknown":
        assert unknown_cause(out, "runs.jsonl"), "the cause on a line of its own: " + out


@pytest.mark.parametrize("cause", ["unparsed-line", "report-without-row"])
def test_task086a_table_row_6_unknown_set_review_b_of_no_builders_family(tmp_path, cause):
    """TASK-086a Done when: "with the set unknown, the alternate never resolved: `review_b` where it is usable and its
    family is the family of no builder the roster file names and of no builder row of the branch that parses";
    "every resolve on an unknown set printing the cause on a line of its own"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(FULL, review_b_alt=COMPOSER), NATIVE])
    if cause == "unparsed-line":
        write_record(ws, row(GROK_B, start=c1, clean=True), "not a json line")
        needle = "runs.jsonl"
    else:
        write_record(ws, row(GROK_B, start=c1, clean=True, brief="TASK-001"))
        commit(ws, "a report with no row", files={"handoff/TASK-002-r1-report.md": "round 1\n"})
        needle = "TASK-002-r1-report.md"
    rc, out = resolve(ws)
    assert "RESOLVED profile 'full'" in out, out
    assert_review_b(ws, rc, out, GPT)
    assert unknown_cause(out, needle), "the cause on a line of its own: " + out


def test_task086a_table_row_7_unknown_set_a_roster_whose_builder_changed_family_after_the_build(tmp_path):
    """TASK-086a Done when: "`review_b` where it is usable and its family is the family of no builder the roster file
    names and of no builder row of the branch that parses (one test for a roster whose builder changed family after
    the build)" and "REBUILD otherwise": the branch was built by xai under a roster that named a grok builder; the
    roster now names composer alone, and the parsing row still shows the family, so `review_b` grok does not review
    and the alternate is never resolved on an unknown set."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    write_record(ws, row(GROK_B, start=c1, clean=True), '{"id": "torn"')
    commit(ws, "the builder's work")
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)
    assert unknown_cause(out, "runs.jsonl"), "the cause on a line of its own: " + out
    assert "--repair-record" in rebuild_text(out), out


@pytest.mark.parametrize("cause", ["unparsed-line", "report-without-row"])
def test_task086a_table_row_7_unknown_set_rebuild_where_review_b_is_of_a_roster_builders_family(tmp_path, cause):
    """TASK-086a Done when: "with the set unknown ... REBUILD otherwise (red on the checkpoint, which resolves
    `review_b`), every resolve on an unknown set printing the cause on a line of its own; the REBUILD line names what
    ends it: for a report without its row the rebuild itself, the branch taken back to the checkpoint of its first
    builder run and its first-round brief run again; for a line that does not parse, `roster-check.py
    --repair-record` first"; the alternate never resolved on an unknown set."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [FULL, dict(NATIVE, review_b_alt=COMPOSER)], other_pool="exhausted")
    if cause == "unparsed-line":
        write_record(ws, review_row(), '{"id": "torn", "kind": "builder"')
        needle, ends = "runs.jsonl", "--repair-record"
    else:
        commit(ws, "a report with no row", files={REPORT1: "round 1\n"})
        needle, ends = "TASK-001-r1-report.md", "checkpoint"
    rc, out = resolve(ws)
    assert "RESOLVED profile 'native'" in out, out
    assert_rebuild(ws, rc, out)
    assert unknown_cause(out, needle), "the cause on a line of its own: " + out
    assert ends in rebuild_text(out).lower(), "the REBUILD line names what ends it: " + out


def test_task086a_review_alt_resolves_the_alternate_with_the_given_reason(tmp_path):
    """TASK-086a Done when: "`--review-alt <reason>`, the reason one word of letters and hyphens, resolving the
    alternate under the same checks with the reason in the entry"; the design's row "known, on `--review-alt
    <reason>` | refused by its provider (T103) | independent and usable | the alternate, with `deviation` (the reason
    given)"."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [dict(FULL, review_b_alt=COMPOSER)])
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert_deviation(ws, rc, out, COMPOSER, "safety-refusal", set())


@pytest.mark.parametrize("case", ["no-alternate", "alternate-of-review-a", "alternate-family-built",
                                  "alternate-pool-exhausted", "alternate-marked", "set-unknown"])
def test_task086a_review_alt_ends_with_exit_1_where_it_cannot(tmp_path, case):
    """TASK-086a Done when: "`--review-alt <reason>` ... ending with exit 1, the cause named and the resolved file
    unchanged, where it cannot, the unknown set among its causes"; the design's row "known or unknown, on
    `--review-alt <reason>` | none, or not independent, or not usable, or the set unknown | exit 1, the cause
    named"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    if case == "alternate-pool-exhausted":
        write_roster(ws, [dict(NATIVE, review_b_alt=GPT)], other_pool="exhausted")
    else:
        alt = {"no-alternate": None, "alternate-of-review-a": CLAUDE_ALT, "alternate-family-built": COMPOSER,
               "alternate-marked": COMPOSER, "set-unknown": COMPOSER}[case]
        profile = dict(FULL, review_b_alt=alt) if alt else dict(FULL)
        write_roster(ws, [profile], unavailable=[COMPOSER] if case == "alternate-marked" else ())
    if case == "alternate-family-built":
        write_record(ws, row(COMPOSER, start=c1, clean=True))
    elif case == "set-unknown":
        write_record(ws, review_row(), "{torn")
    before = plant_resolved(ws)
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert rc == 1 and "RESOLVED" not in out and not deviation_printed(out), out
    assert resolved_path(ws).read_bytes() == before, "the resolved file is left unchanged"
    if case == "set-unknown":
        assert unknown_cause(out, "runs.jsonl"), "the cause named: " + out


@pytest.mark.parametrize("reason", ["safety_refusal", "two words", "refusal1", "", None],
                         ids=["underscore", "space", "digit", "empty", "missing"])
def test_task086a_review_alt_refuses_a_malformed_reason(tmp_path, reason):
    """TASK-086a Done when: "`--review-alt <reason>`, the reason one word of letters and hyphens"."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [dict(FULL, review_b_alt=COMPOSER)])
    before = plant_resolved(ws)
    args = ["--review-alt"] + ([] if reason is None else [reason])
    rc, out = resolve(ws, *args)
    assert rc != 0 and "RESOLVED" not in out and not deviation_printed(out), out
    assert resolved_path(ws).read_bytes() == before, "the resolved file is left unchanged"


# --- --repair-record ---------------------------------------------------------------------------------

def test_task086a_repair_record_keeps_every_parsing_line_in_place_and_moves_the_others(tmp_path):
    """TASK-086a Done when: "`--repair-record` rewrites the record by a temporary file and a replace, keeping every
    line that parses in its place and order, appends the others to `run/launcher/runs.damaged.jsonl`, prints both
    counts"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    good = [review_row(), row(GROK_B, start=c1, clean=True), review_row(), row(COMPOSER, start=c1, clean=True),
            review_row()]
    bad = ['{"id": "torn", "kind": "builder", "model": "gr', "not a json line", '{"id": "torn-again"']
    write_record(ws, good[0], bad[0], good[1], good[2], bad[1], good[3], bad[2], good[4])
    damaged = ws / "run" / "launcher" / "runs.damaged.jsonl"
    damaged.write_text('{"earlier": "a line moved by an earlier repair"}\n', encoding="utf-8", newline="\n")
    rc, out = resolve(ws, "--repair-record")
    assert rc == 0, out
    assert record_path(ws).read_text(encoding="utf-8").splitlines() == good
    assert damaged.read_text(encoding="utf-8").splitlines() == ['{"earlier": "a line moved by an earlier repair"}'] + bad
    assert re.search(r"\b5\b", out) and re.search(r"\b3\b", out), "both counts printed: " + out


def test_task086a_repair_record_changes_nothing_where_every_line_parses(tmp_path):
    """TASK-086a Done when: "`--repair-record` ... changes nothing where every line parses"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    write_record(ws, review_row(), row(GROK_B, start=c1, clean=True), row(GROK_B))
    before = record_path(ws).read_bytes()
    rc, out = resolve(ws, "--repair-record")
    assert rc == 0, out
    assert record_path(ws).read_bytes() == before
    assert not (ws / "run" / "launcher" / "runs.damaged.jsonl").exists()


def test_task086a_after_a_repair_that_moved_a_builders_row_the_rebuild_makes_the_set_known(tmp_path):
    """TASK-086a Done when: "a test holds that after a repair that moved a builder's row the set is unknown by the
    report's cause, that the rebuild makes it known"; the REBUILD line names `--repair-record` first for a line that
    does not parse; "a report whose row was among the lines moved is then a report without its row"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE], other_pool="exhausted")
    write_record(ws, review_row(), row(GROK_B, start=c1, clean=True)[:-1], review_row())
    commit(ws, "the first round's work", files={REPORT1: "round 1\n"})
    rc, out = resolve(ws)
    assert rc == 0 and unknown_cause(out, "runs.jsonl"), out
    assert "--repair-record" in rebuild_text(out), out
    rc, out = resolve(ws, "--repair-record")
    assert rc == 0, out
    rc, out = resolve(ws)
    assert rc == 0 and "REBUILD" in out, out
    assert unknown_cause(out, "TASK-001-r1-report.md"), "unknown by the report's cause: " + out
    git(ws, "reset", "-q", "--hard", c1)
    append_record(ws, row(COMPOSER, start=c1, clean=True))
    commit(ws, "the rebuild's work", files={REPORT1: "round 1, rebuilt\n"})
    rc, out = resolve(ws)
    assert "RESOLVED profile 'native'" in out, out
    assert_review_b(ws, rc, out, GROK_R)
    assert not any_unknown_line(out), out


def test_task086a_a_first_round_line_moved_aside_then_the_whole_branch_rebuilt_reads_the_rebuilder_alone(tmp_path):
    """TASK-086a Done when: the history "a first-round row and a fix-round row by one family whose first-round line a
    repair moved aside, the whole branch then rebuilt by another family, after which the set is that family's alone
    and the resolve prints no REBUILD"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE], other_pool="exhausted")
    first = row(GROK_B, start=c1, clean=True)[:-1]
    c2 = commit(ws, "the first round's work", files={REPORT1: "round 1\n"})
    write_record(ws, first, row(GROK_B, start=c2, clean=True, rnd=2))
    commit(ws, "the fix round's work", files={REPORT2: "round 2\n"})
    rc, out = resolve(ws, "--repair-record")
    assert rc == 0, out
    rc, out = resolve(ws)
    assert rc == 0 and "REBUILD" in out, out
    git(ws, "reset", "-q", "--hard", c1)
    append_record(ws, row(COMPOSER, start=c1, clean=True))
    commit(ws, "the whole branch rebuilt", files={REPORT1: "round 1, rebuilt\n"})
    rc, out = resolve(ws)
    assert "RESOLVED profile 'native'" in out, out
    assert_review_b(ws, rc, out, GROK_R)


# --- families, the alternate's probe, a deviation no longer needed, built_by -----------------------------

def test_task086a_the_native_profile_names_its_own_builder_as_the_alternate(tmp_path):
    """TASK-086a Done when: "a profile's builder, Review A and `review_b` stay of three families, and `review_b_alt`
    may be of the builder's" (the native profile: builder composer-2.5, `review_b` grok-4.7-medium, `review_b_alt`
    composer-2.5)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=COMPOSER)])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    commit(ws, "the builder's work")
    rc, out = resolve(ws)
    assert_deviation(ws, rc, out, COMPOSER, "family", {"xai"})
    assert resolved(ws)["builder"] == COMPOSER


@pytest.mark.parametrize("profile", [
    {"name": "p", "builder": GROK_B, "review_b": GROK_R, "review_b_alt": GPT},
    {"name": "p", "builder": COMPOSER, "review_b": CLAUDE_ALT, "review_b_alt": GPT},
    {"name": "p", "builder": REVIEW_A, "review_b": GROK_R, "review_b_alt": COMPOSER},
], ids=["review-b-of-the-builders-family", "review-b-of-review-a-s-family", "builder-of-review-a-s-family"])
def test_task086a_builder_review_a_and_review_b_stay_three_families(tmp_path, profile):
    """TASK-086a Done when: "a profile's builder, Review A and `review_b` stay of three families" (an alternate does
    not rescue a collision)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [profile])
    rc, out = resolve(ws)
    assert rc == 1 and "collision" in out and "RESOLVED" not in out and not deviation_printed(out), out


def test_task086a_a_resolve_that_needs_no_alternate_writes_no_deviation(tmp_path):
    """TASK-086a Done when: "a resolve on a branch that needs no alternate writes no `deviation`" (a deviation written
    before the rebuild is gone after it)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    commit(ws, "the first run's work")
    rc, out = resolve(ws)
    assert_deviation(ws, rc, out, GPT, "family", {"xai"})
    git(ws, "reset", "-q", "--hard", c1)
    append_record(ws, row(COMPOSER, start=c1, clean=True))
    commit(ws, "the rebuild's work")
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GROK_R)


def test_task086a_the_alternate_is_probed_where_the_profiles_models_are(program, tmp_path, monkeypatch, capsys):
    """TASK-086a Done when: "the alternate is probed where the profile's models are". The program's `main` is run in
    this process with its `probe` replaced, so no model is asked: an alternate that answers is resolved, one that
    does not leaves the REBUILD."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    commit(ws, "the builder's work")
    mod = program("roster-check")
    probed = []
    failing = set()

    def fake_probe(model_id, *args, **kwargs):
        probed.append(model_id)
        return (False, "exit 1; stdout=''; stderr='refused'") if model_id in failing else (True, "answered")

    monkeypatch.setattr(mod, "probe", fake_probe)
    for name in list(os.environ):
        if name.upper().startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("ROSTER_NOW", NOW)
    monkeypatch.chdir(ws)
    monkeypatch.setattr(sys, "argv", ["roster-check.py", "docs/ROSTER.json"])
    assert mod.main() == 0, capsys.readouterr().out
    out = capsys.readouterr().out
    assert GPT in probed and COMPOSER in probed, (probed, out)
    assert resolved(ws).get("deviation", {}).get("review_b_alt") == GPT, out
    del probed[:]
    failing.add(GPT)
    assert mod.main() == 0, capsys.readouterr().out
    out = capsys.readouterr().out
    assert GPT in probed, (probed, out)
    data = resolved(ws)
    assert "deviation" not in data and "rebuild" in data and "REBUILD" in out, out


def test_task086a_built_by_keeps_its_answer(program, tmp_path):
    """TASK-086a Done when: "`built_by` keeps its answer, the last builder run's model, for the tests and the line that
    read it" (rows with and without the two new keys; a slot-not-free row skipped as on the checkpoint)."""
    mod = program("roster-check")
    log = tmp_path / "runs.jsonl"
    log.write_text("\n".join([
        row(GROK_B, start="a" * 40, clean=True),
        row(GROK_R),
        row(COMPOSER, start="a" * 40, clean=True),
        row(GPT, start="a" * 40, clean=True, slot="not free"),
        review_row(),
        row(GROK_B, branch="task-9"),
    ]) + "\n", encoding="utf-8")
    assert mod.built_by(str(log), BRANCH) == COMPOSER
    assert mod.built_by(str(log), "task-9") == GROK_B
    assert mod.built_by(str(log), "design-x") is None


def test_task086a_after_the_repair_and_the_rebuild_the_review_guards_first_snapshot_seeds_no_round(tmp_path):
    """TASK-086a Done when: "a test holds that after a repair that moved a builder's row the set is unknown by the
    report's cause, that the rebuild makes it known, and that the review guard's first snapshot after it seeds no
    round". The checkout is the review guard's own test checkout (tests/test_task032_supervisor_guard.py), the roster
    files kept out of the tree by `.git/info/exclude` so the snapshot finds it clean; the rebuild's builder row names
    brief TASK-001 round 1, so the rebuilt report's round is a logged one and the first snapshot `TASK-001` is round 1,
    unseeded."""
    import test_task032_supervisor_guard as G
    ws = G.make_repo(tmp_path, branch=BRANCH, files={"handoff/TASK-001.md": "# TASK-001\n"})
    write(ws, ".git/info/exclude", "docs/ROSTER.json\ndocs/ROSTER.resolved.json\n")
    c1 = git(ws, "rev-parse", "HEAD")
    write_roster(ws, [FULL, NATIVE], other_pool="exhausted")
    write_record(ws, review_row(), row(GROK_B, start=c1, clean=True)[:-1], review_row())
    commit(ws, "the first round's work", files={REPORT1: "round 1\n"})
    rc, out = resolve(ws, "--repair-record")
    assert rc == 0, out
    rc, out = resolve(ws)
    assert rc == 0 and "REBUILD" in out and unknown_cause(out, "TASK-001-r1-report.md"), out
    git(ws, "reset", "-q", "--hard", c1)
    append_record(ws, row(COMPOSER, start=c1, clean=True))
    commit(ws, "the rebuild's work", files={REPORT1: "round 1, rebuilt\n"})
    rc, out = resolve(ws)
    assert_review_b(ws, rc, out, GROK_R)
    G.snap_ok(ws, "TASK-001")
    data = G.rounds(ws, "TASK-001")["rounds"]
    assert [r["round"] for r in data] == [1] and not data[0].get("seeded"), data


# --- round 2: the supervisor's tests of round 1's defects ------------------------------------------------
# Written after round 1's review, before the round-2 brief; each is red on round 1's code. The in-process tests run
# the program's `main` with `subprocess.run`, `probe` or `open` wrapped, so no fake git has to be found on PATH (a
# program started by name without a shell finds an .exe alone on Windows).

RESOLVED_KEYS = {"profile", "builder", "review_a", "review_b", "families", "other_pool", "probed", "resolved_at",
                 "reset_day", "rebuild", "deviation"}


def fail_text(out):
    """The lines that begin `FAIL`, lower-cased: where a refusal names its cause."""
    return "\n".join(line for line in out.splitlines() if line.strip().startswith("FAIL")).lower()


def _main_in_process(mod, ws, monkeypatch, capsys, *args):
    for name in list(os.environ):
        if name.upper().startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("ROSTER_NOW", NOW)
    monkeypatch.chdir(ws)
    monkeypatch.setattr(sys, "argv", ["roster-check.py", "docs/ROSTER.json"] + list(args))
    capsys.readouterr()
    rc = mod.main()
    return rc, capsys.readouterr().out


@pytest.mark.parametrize("form", ["new-branch", "repair-record", "checkpoint"])
def test_task086a_the_rebuild_form_stands_in_the_printed_line_alone(tmp_path, form):
    """TASK-086a Done when: "the form standing in the printed line alone and the resolved file's `rebuild` entry
    keeping its two keys": the resolved file holds no key beyond the checkpoint's and `deviation` (round 1 wrote the
    form into the file as a key of its own)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    if form == "new-branch":
        write_roster(ws, [NATIVE])
        commit(ws, "the first run's work")
        write_record(ws, row(GROK_B), row(COMPOSER, start=c1, clean=True))
        needle = "new branch"
    elif form == "repair-record":
        write_roster(ws, [FULL, dict(NATIVE, review_b_alt=COMPOSER)], other_pool="exhausted")
        write_record(ws, review_row(), '{"id": "torn", "kind": "builder"')
        needle = "--repair-record"
    else:
        write_roster(ws, [FULL, dict(NATIVE, review_b_alt=COMPOSER)], other_pool="exhausted")
        commit(ws, "a report with no row", files={REPORT1: "round 1\n"})
        needle = "checkpoint"
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)
    assert needle in rebuild_text(out).lower(), out
    assert set(resolved(ws)) <= RESOLVED_KEYS, "the form stands in the printed line alone: %s" % sorted(resolved(ws))


def test_task086a_the_rebuild_names_the_model_of_review_b_s_family_that_built(tmp_path):
    """TASK-086a Done when: "REBUILD as on the checkpoint where `review_b`'s family built"; the checkpoint's REBUILD
    names the model of `review_b`'s family that built the change. A first round by grok and a fix round by composer
    both count; `review_b` grok is refused for the xai family, so the lines and the `rebuild` entry name the grok
    model, never the composer model of the last row as if it were of the xai family (round 1)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    c2 = commit(ws, "the first round's work", files={REPORT1: "round 1\n"})
    write_record(ws, row(GROK_B, start=c1, clean=True), row(COMPOSER, start=c2, clean=True, rnd=2))
    commit(ws, "the fix round's work", files={REPORT2: "round 2\n"})
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)
    assert resolved(ws)["rebuild"]["built_by"] == GROK_B, resolved(ws)
    lines = [line for line in out.splitlines() if "REBUILD" in line]
    assert lines and all(GROK_B in line for line in lines), out


def test_task086a_an_unavailable_reviewers_alternate_that_does_not_answer_skips_the_profile(program, tmp_path,
                                                                                          monkeypatch, capsys):
    """TASK-086a Done when: "the profile skipped as on the checkpoint, never a REBUILD, where a mark or its pool
    excludes `review_b` and no alternate is independent and usable"; "the alternate is probed where the profile's
    models are": `review_b` is marked unavailable and the alternate does not answer its probe, so no alternate is
    usable and the profile is skipped (round 1 resolved a REBUILD with the marked `review_b`)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)], unavailable=[GROK_R])
    before = plant_resolved(ws)
    mod = program("roster-check")
    monkeypatch.setattr(mod, "probe", lambda model_id, *a, **k: (False, "exit 1") if model_id == GPT else (True, "ok"))
    rc, out = _main_in_process(mod, ws, monkeypatch, capsys)
    assert rc == 1 and "skip" in out and "RESOLVED" not in out, out
    assert "REBUILD" not in out and not deviation_printed(out), out
    assert resolved_path(ws).read_bytes() == before


def _git_answering_otherwise(monkeypatch, match, how):
    real = subprocess.run

    def fake(args, *a, **k):
        if isinstance(args, (list, tuple)) and match([str(x) for x in args]):
            if how == "times-out":
                raise subprocess.TimeoutExpired(args, 20)
            return subprocess.CompletedProcess(args, 128, "", "fatal: git is not answering\n")
        return real(args, *a, **k)

    monkeypatch.setattr(subprocess, "run", fake)


@pytest.mark.parametrize("call,how", [("is-ancestor", "fails"), ("is-ancestor", "times-out"),
                                      ("verify", "fails"), ("verify", "times-out"), ("merge-base", "times-out"),
                                      ("ls-tree", "fails")])
def test_task086a_git_answering_neither_yes_nor_no_cannot_be_read(program, tmp_path, monkeypatch, capsys, call, how):
    """TASK-086a Done when: "git's answer of yes or no being the test and any other failure of git a set that cannot
    be read"; "git does not answer (it does not start, times out or fails)": an exit other than git's yes or no (128)
    or a timeout of the ancestor test, of the check that a start commit names a commit, or of the base's merge base
    ends the resolve with exit 1 and the cause `git`, the resolved file unchanged (round 1 read them as no, as a
    commit that does not exist, or as no `main`)."""
    ws = scratch_repo(tmp_path)
    c0 = git(ws, "rev-parse", "HEAD")
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    if call in ("merge-base", "ls-tree"):
        commit(ws, "the brief's work", files={REPORT1: "round 1\n"})
        write_record(ws, row(COMPOSER, start=c1, clean=True))
        if call == "merge-base":
            match = lambda a: a[:2] == ["git", "merge-base"] and "--is-ancestor" not in a
        else:
            match = lambda a: a[:2] == ["git", "ls-tree"]
    else:
        commit(ws, "the first run's work")
        write_record(ws, row(GROK_B, start=c1, clean=True), row(COMPOSER, start=c0, clean=True))
        if call == "is-ancestor":
            match = lambda a: a[:3] == ["git", "merge-base", "--is-ancestor"]
        else:
            match = lambda a: a[:3] == ["git", "rev-parse", "--verify"] and any(x.startswith(c1) for x in a[3:])
    before = plant_resolved(ws)
    mod = program("roster-check")
    _git_answering_otherwise(monkeypatch, match, how)
    rc, out = _main_in_process(mod, ws, monkeypatch, capsys, "--no-probe")
    assert_cannot_read(ws, rc, out, before, "git")


def test_task086a_a_repair_that_fails_part_way_leaves_the_record_whole(program, tmp_path, monkeypatch, capsys):
    """TASK-086a Done when: "`--repair-record` rewrites the record by a temporary file and a replace, keeping every
    line that parses in its place and order, appends the others to `run/launcher/runs.damaged.jsonl`"; the brief's
    security context: "a crash leaves the old record whole". The damaged file cannot be written, so the repair ends
    with a non-zero exit and no traceback, and the record keeps every line, the moved ones among them (round 1
    replaced the record first and lost the lines it had not yet appended)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    write_record(ws, review_row(), '{"id": "torn", "kind": "builder"', row(GROK_B, start=c1, clean=True))
    before = record_path(ws).read_bytes()
    mod = program("roster-check")
    real_open = open

    def refusing_open(file, *a, **k):
        if os.path.basename(str(file)) == "runs.damaged.jsonl":
            raise OSError("the damaged file cannot be written")
        return real_open(file, *a, **k)

    monkeypatch.setattr("builtins.open", refusing_open)
    rc, out = _main_in_process(mod, ws, monkeypatch, capsys, "--repair-record")
    monkeypatch.setattr("builtins.open", real_open)
    assert rc != 0, out
    assert record_path(ws).read_bytes() == before, "the record is left whole"


def test_task086a_a_repair_refuses_a_damaged_file_linked_to_another_file(tmp_path):
    """The brief's security context ("`--repair-record` rewrites the record by a temporary file and a replace in the
    record's own folder"): the repair writes nothing outside the record's folder, so a `runs.damaged.jsonl` that is a
    hard link to another file (made without privilege on one volume) is refused, the other file and the record
    unchanged (round 1 appended to whatever the name reached)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    write_record(ws, review_row(), "not a json line", row(GROK_B, start=c1, clean=True))
    before = record_path(ws).read_bytes()
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"a file outside the record's folder\n")
    try:
        os.link(str(outside), str(ws / "run" / "launcher" / "runs.damaged.jsonl"))
    except OSError as exc:
        pytest.skip("no hard link on this file system: %s" % exc)
    rc, out = resolve(ws, "--repair-record")
    assert rc != 0 and "Traceback" not in out, out
    assert outside.read_bytes() == b"a file outside the record's folder\n"
    assert record_path(ws).read_bytes() == before


def test_task086a_a_record_line_split_only_at_its_line_feed(tmp_path):
    """TASK-086a Done when: "`--repair-record` ... changes nothing where every line parses": a line is what lies
    between two line feeds, so a builder row whose text holds a line separator (U+2028, valid inside a JSON string)
    parses whole and the repair changes nothing (round 1 split it there and moved two halves)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    odd = '{"id": "a\u2028b", "kind": "builder", "model": "composer-2.5", "branch": "task-9"}'
    write_record(ws, review_row(), odd, row(GROK_B, start=c1, clean=True))
    before = record_path(ws).read_bytes()
    rc, out = resolve(ws, "--repair-record")
    assert rc == 0, out
    assert record_path(ws).read_bytes() == before
    assert not (ws / "run" / "launcher" / "runs.damaged.jsonl").exists()


@pytest.mark.parametrize("line", [b"\xff\xfe not utf-8", b"[" * 100000],
                         ids=["not-utf-8", "nested-too-deep"])
def test_task086a_a_hostile_record_line_makes_the_set_unknown_and_the_repair_moves_it(tmp_path, line):
    """The brief's acceptance criterion "No exception escapes as a traceback on any record" and its security context
    ("a line that does not parse makes the set unknown"): a line that is not UTF-8, or nested past the parser's depth,
    is a line that does not parse; the resolve prints the cause on a line of its own and `--repair-record` moves the
    line, byte for byte, to the damaged file (round 1 raised a traceback on both)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    good = row(GROK_B, start=c1, clean=True).encode("utf-8")
    record_path(ws).parent.mkdir(parents=True, exist_ok=True)
    record_path(ws).write_bytes(good + b"\n" + line + b"\n")
    rc, out = resolve(ws)
    assert "Traceback" not in out and unknown_cause(out, "runs.jsonl"), out
    rc, out = resolve(ws, "--repair-record")
    assert rc == 0 and "Traceback" not in out, out
    assert record_path(ws).read_bytes() == good + b"\n"
    assert (ws / "run" / "launcher" / "runs.damaged.jsonl").read_bytes() == line + b"\n"


def test_task086a_the_unknown_cause_names_the_record_given_by_run_log(tmp_path):
    """TASK-086a Done when: "every resolve on an unknown set printing the cause on a line of its own"; the module
    docstring of these tests: the cause names "the record's file name": under `--run-log` the record is another file,
    and its name is the one printed (round 1 printed `runs.jsonl` whatever the record was)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    other = ws / "run" / "launcher" / "other.jsonl"
    other.parent.mkdir(parents=True, exist_ok=True)
    other.write_text(review_row() + "\nnot a json line\n", encoding="utf-8", newline="\n")
    rc, out = resolve(ws, "--run-log", "run/launcher/other.jsonl")
    assert unknown_cause(out, "other.jsonl"), out


@pytest.mark.parametrize("name", ["handoff/BUG-047-report.md", "handoff/TASK-002-r1-Report.md"],
                         ids=["no-round-in-the-name", "letter-case"])
def test_task086a_every_report_file_the_branch_adds_needs_its_row(tmp_path, name):
    """TASK-086a Done when: "a report file (a file under `handoff/` whose name ends `-report.md` ...)"; "unknown where
    ... a report file that the branch adds over that base has no builder row of the branch for its brief": a report
    named without a round (`BUG-047-report.md`, the form four committed reports of this repository use) belongs to
    brief BUG-047, and the name's ending is compared without regard to letter case (round 1 skipped both, and read the
    set as known)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    write_record(ws, row(COMPOSER, start=c1, clean=True, brief="TASK-001"))
    commit(ws, "a report with no row", files={name: "the report\n"})
    rc, out = resolve(ws)
    assert unknown_cause(out, os.path.basename(name)), "the cause on a line of its own: " + out


def test_task086a_a_family_named_in_the_roster_counts_for_a_builder_row(tmp_path):
    """The brief's security context ("unknown is never read as nobody having built"); the program's own skip line
    tells the owner to give a model its family in the roster (`{"model": ..., "family": ...}`): a builder row of that
    model counts for that family (round 1 counted it for none, so a Review B of the family resolved)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [{"name": "full", "builder": {"model": "mystery-builder-1", "family": "xai"}, "review_b": GPT},
                      NATIVE], other_pool="exhausted")
    write_record(ws, row("mystery-builder-1", start=c1, clean=True))
    commit(ws, "the builder's work")
    rc, out = resolve(ws)
    assert "RESOLVED profile 'native'" in out, out
    assert_rebuild(ws, rc, out)


@pytest.mark.parametrize("model", ["mystery-builder-2", 123], ids=["family-unknown", "not-a-string"])
def test_task086a_a_builder_row_of_no_known_family_makes_the_set_unknown(tmp_path, model):
    """The brief's security context ("a field of the wrong type is never trusted", "unknown is never read as nobody
    having built"): a builder row of the branch whose model is not a string, or whose family neither the roster nor
    the program can name, leaves the set unknown with the cause on a line of its own, so the alternate is never
    resolved on it; and since that row may be of `review_b`'s family, `review_b` is not "of no builder row of the
    branch that parses", so the resolve is a REBUILD (round 1 counted the row for no family, read the set as known and
    resolved `review_b`)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    e = json.loads(row(GROK_B, start=c1, clean=True))
    e["model"] = model
    write_record(ws, json.dumps(e))
    commit(ws, "the builder's work")
    rc, out = resolve(ws)
    assert unknown_cause(out, "runs.jsonl"), "the cause on a line of its own: " + out
    assert_rebuild(ws, rc, out)


@pytest.mark.parametrize("ref", ["tag-main", "tag-branch"])
def test_task086a_main_and_the_branch_are_read_by_their_full_ref_names(tmp_path, ref):
    """TASK-086a Done when: "the branch's base ... (its merge base with `origin/main`, or with `main` where the
    repository has no remote)"; "every builder row of the branch counts": the base is the branch `main`, never a tag
    named `main` (git reads a tag first), and the branch is the checked-out branch, never `heads/<name>` (what git's
    short name gives where a tag has the same name) (round 1 took the tag for the base, so a report the branch adds
    read as the base's, and read the branch as `heads/task-1`, so its builder rows counted for nothing)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    if ref == "tag-main":
        write_record(ws, row(COMPOSER, start=c1, clean=True, brief="TASK-001"))
        commit(ws, "a report with no row", files={REPORT2.replace("TASK-001", "TASK-002"): "round 1\n"})
        git(ws, "tag", "main", "HEAD")
        rc, out = resolve(ws)
        assert unknown_cause(out, "TASK-002-r2-report.md"), "the cause on a line of its own: " + out
    else:
        write_record(ws, row(GROK_B, start=c1, clean=True))
        commit(ws, "the builder's work")
        git(ws, "tag", BRANCH, c1)
        rc, out = resolve(ws)
        assert_deviation(ws, rc, out, GPT, "family", {"xai"})


def test_task086a_a_start_commit_is_a_full_object_name(tmp_path):
    """The brief's security context ("a `start_commit` from the record is passed to git only after it is checked to
    be a hexadecimal object name (never ... a revision expression)"): a short object name is one git may read as a
    branch or tag named like it, so only a full one (40 or 64 hexadecimal digits) places a row; a later row whose
    start commit is short drops nothing, and the earlier family stays (round 1 dropped it)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [NATIVE])
    commit(ws, "the first run's work")
    write_record(ws, row(GROK_B, start=c1, clean=True), row(COMPOSER, start=c1[:12], clean=True))
    rc, out = resolve(ws)
    assert_rebuild(ws, rc, out)


def test_task086a_a_builder_that_does_not_answer_skips_the_profile_where_an_alternate_would_resolve(
        program, tmp_path, monkeypatch, capsys):
    """TASK-086a Done when: "the alternate is probed where the profile's models are"; the checkpoint's rule that a
    model that does not answer skips the profile: `review_b`'s family built and the alternate answers, but the
    profile's builder does not, so the profile is skipped, never a REBUILD with a builder that does not answer
    (round 1 resolved the REBUILD)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    write_record(ws, row(GROK_B, start=c1, clean=True))
    commit(ws, "the builder's work")
    before = plant_resolved(ws)
    mod = program("roster-check")
    monkeypatch.setattr(mod, "probe",
                        lambda model_id, *a, **k: (False, "exit 1") if model_id == COMPOSER else (True, "ok"))
    rc, out = _main_in_process(mod, ws, monkeypatch, capsys)
    assert rc == 1 and "skip" in out and "RESOLVED" not in out, out
    assert "REBUILD" not in out and not deviation_printed(out), out
    assert resolved_path(ws).read_bytes() == before


@pytest.mark.parametrize("case,cause", [("no-alternate", "no review_b_alt"), ("alternate-of-review-a", "review a"),
                                        ("alternate-family-built", "built"), ("alternate-pool-exhausted", "pool"),
                                        ("alternate-marked", "marked")])
def test_task086a_review_alt_names_its_cause(tmp_path, case, cause):
    """TASK-086a Done when: "`--review-alt <reason>` ... ending with exit 1, the cause named"; the design's row "none,
    or not independent, or not usable ... exit 1, the cause named": the refusal names which (round 1 printed one line
    for every cause). The words: `no review_b_alt` where none is named, `Review A` for an alternate of its family,
    `built` for a family that built the branch, `pool` for an exhausted pool, `marked` for a mark."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    if case == "alternate-pool-exhausted":
        write_roster(ws, [dict(NATIVE, review_b_alt=GPT)], other_pool="exhausted")
    else:
        alt = {"no-alternate": None, "alternate-of-review-a": CLAUDE_ALT, "alternate-family-built": COMPOSER,
               "alternate-marked": COMPOSER}[case]
        profile = dict(FULL, review_b_alt=alt) if alt else dict(FULL)
        write_roster(ws, [profile], unavailable=[COMPOSER] if case == "alternate-marked" else ())
    if case == "alternate-family-built":
        write_record(ws, row(COMPOSER, start=c1, clean=True))
    before = plant_resolved(ws)
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert rc == 1 and "RESOLVED" not in out, out
    assert cause in fail_text(out), "the cause named on a FAIL line (%s): %s" % (cause, out)
    assert resolved_path(ws).read_bytes() == before


def test_task086a_review_alt_acts_on_the_profile_in_use_alone(tmp_path):
    """The design's row "known, on `--review-alt <reason>` | refused by its provider (T103)": the request is about
    the profile in use, whose `review_b` was refused; where that profile names no alternate the request ends with exit
    1 and the cause, and never passes to a later profile, which would also change the builder (round 1 resolved the
    second profile's alternate without a word)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [FULL, dict(NATIVE, review_b_alt=COMPOSER)])
    before = plant_resolved(ws)
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert rc == 1 and "RESOLVED" not in out and not deviation_printed(out), out
    assert "no review_b_alt" in fail_text(out), out
    assert resolved_path(ws).read_bytes() == before


def test_task086a_review_alt_on_a_set_that_cannot_be_read(tmp_path):
    """TASK-086a Done when: "`--review-alt <reason>` ... ending with exit 1, the cause named and the resolved file
    unchanged, where it cannot"; the design: the row of a set that cannot be read "is read before the others"."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(FULL, review_b_alt=COMPOSER)])
    git(ws, "checkout", "-q", "--detach", c1)
    before = plant_resolved(ws)
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert_cannot_read(ws, rc, out, before, "detached")


def test_task086a_review_alt_on_a_known_set_records_the_built_families(tmp_path):
    """The design's row "known, on `--review-alt <reason>` ... the alternate, with `deviation` (the reason given)";
    the entry's `built` holds the known set (the acceptance test of the request on an empty set never shows it)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [dict(NATIVE, review_b_alt=GPT)])
    write_record(ws, row(COMPOSER, start=c1, clean=True))
    commit(ws, "the builder's work")
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert_deviation(ws, rc, out, GPT, "safety-refusal", {"cursor"})


@pytest.mark.parametrize("reason", ["safety\n", "--no-probe", "-"], ids=["trailing-newline", "an-option", "hyphen"])
def test_task086a_review_alt_refuses_a_reason_that_is_not_a_word_and_says_so(tmp_path, reason):
    """TASK-086a Done when: "`--review-alt <reason>`, the reason one word of letters and hyphens": a word begins with
    a letter and ends at the value's end, so a trailing line feed, an option and a hyphen alone are refused, with a
    line naming the reason (round 1 took `safety` followed by a line feed and `--no-probe`, the latter also turning
    the probe off, and refused the rest without a word)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [dict(FULL, review_b_alt=COMPOSER)])
    before = plant_resolved(ws)
    rc, out = resolve(ws, "--review-alt", reason)
    assert rc != 0 and "RESOLVED" not in out and not deviation_printed(out), out
    assert "reason" in out.lower(), "a line naming the reason: " + out
    assert resolved_path(ws).read_bytes() == before
