"""Release S: the short gate of a records-only pull request (`review-guard.py premerge-records [<pr>]`).

A pull request whose every changed file is a record, none of them one a program reads to decide a gate, merges on CI and one Review A
read: the guard writes the record the permission guard reads without a snapshot, a Review B run or a verified mark. Everything else keeps
the whole round. The changed files are GitHub's list of the pull request joined with the local diff from its base, so a moved local ref
cannot shrink what is classified. Scratch repositories; `gh` is replaced in-process by `pr_state`, as the head-wait tests replace
`pr_head`."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")
GUARD = os.path.join(BRIDGE, "review-guard.py")
PERMISSION = os.path.join(BRIDGE, "permission-guard.py")

REGISTER = ("| ID | Requirement | Source | Status | Evidence |\n|---|---|---|---|---|\n"
            "| R-001 | parse the file | owner | built | tests/test_parse.py |\n"
            "| R-002 | write the file | owner | planned | - |\n")
INVENTORY = ("# Inventory\n\n## Decisions\n\n| Decision | Why |\n|---|---|\n"
             "| The threat model: the builder and the reviewer are outside input | KP-032 |\n| Dates are UTC | simpler |\n")


def env():
    return dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x",
                GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=env())
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def run(repo, *args):
    p = subprocess.run([sys.executable, GUARD] + list(args), cwd=str(repo), capture_output=True, text=True, env=env(), encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


@pytest.fixture
def repo(tmp_path):
    """main as merged (origin/main beside it) and a branch `records` cut from it, nothing changed yet."""
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "handoff").mkdir()
    (r / "src").mkdir()
    (r / "docs" / "REQUIREMENTS.md").write_text(REGISTER, encoding="utf-8")
    (r / "docs" / "INVENTORY.md").write_text(INVENTORY, encoding="utf-8")
    (r / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\n", encoding="utf-8")
    (r / "docs" / "RUN_PARAMETERS.md").write_text("Merge authority: owner\n", encoding="utf-8")
    (r / "docs" / "BUILD_PLAN.md").write_text("# Plan\n", encoding="utf-8")
    (r / "docs" / "ROSTER.json").write_text("{}\n", encoding="utf-8")
    (r / "project.json").write_text("{}\n", encoding="utf-8")
    (r / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    git(r, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(r, "checkout", "-q", "-b", "records")
    return r


def change(repo, path, text, message="records"):
    full = repo / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def premerge_record(repo):
    folder = repo / ".git" / "bridge" / "premerge"
    return sorted(os.listdir(str(folder))) if folder.is_dir() else []


# ---------------------------------------------------------------- which gate, by path and by cell


def test_records_alone_take_the_short_gate_and_nothing_is_written_without_a_pull_request(repo):
    """The status file, a new brief, a planned row's sentence and Evidence and a new `planned` row, the inventory's other rows,
    project.json's state, a picture."""
    change(repo, "docs/PROJECT_STATUS.md", "Phase: done\n")
    change(repo, "handoff/TASK-002.md", "# TASK-002\n")
    change(repo, "docs/REQUIREMENTS.md", REGISTER.replace("write the file | owner | planned | - |", "write the file whole | owner | planned | TASK-002 |")
           + "| R-003 | show a graph | owner | planned | - |\n")
    change(repo, "docs/INVENTORY.md", INVENTORY.replace("simpler", "simpler to compare"))
    change(repo, "project.json", '{"phase": "done"}\n')
    change(repo, "docs/screens/first.PNG", "not really a picture\n")
    rc, out = run(repo, "premerge-records")
    assert rc == 0 and "SHORT GATE - 6 changed file(s)" in out and "nothing was written" in out, out
    assert premerge_record(repo) == []


@pytest.mark.parametrize("path,text,why", [
    ("src/a.py", "x = 2\n", "not a record"),
    ("tests/test_a.py", "def test_a():\n    assert True\n", "not a record"),
    (".github/workflows/tests.yml", "on: push\n", "not a record"),
    ("docs/RUN_PARAMETERS.md", "Merge authority: supervisor\n", "the run parameters decide"),
    ("docs/BUILD_PLAN.md", "# Plan\n\n### TASK-009\n", "the plan decides"),
    ("docs/BUILD_PLAN-2.md", "# Plan two\n", "the plan decides"),
    ("docs/ROSTER.json", '{"builder": "x"}\n', "the roster decides"),
    ("docs/ROSTER.resolved.json", '{"builder": "x"}\n', "the roster decides"),
    ("docs/build_plan-3.md", "# Plan three\n", "the plan decides"),                    # the names are compared in lower case
    ("docs/diagrams/DEVIATIONS.md", "| crossing | why |\n", "decide what the diagram check allows"),
    ("docs/diagrams/INDEX.md", "| D-001 | context |\n", "decide what the diagram check allows"),
    ("docs/diagrams/D-001-context.md", "flowchart LR\n", "decide what the diagram check allows"),
    ("docs/conf.py", "import os\n", "not a record by its type"),                       # a program under a record folder (Review A, round 1)
    ("docs/conftest.py", "import os\n", "not a record by its type"),
    ("handoff/run.sh", "echo x\n", "not a record by its type"),
    ("docs/mockups/first.html", "<script>x()</script>\n", "not a record by its type"),
    ("docs/notes", "no type at all\n", "not a record by its type"),
    ("docs/mkdocs.yml", "plugins: [x]\n", "not a record by its type"),
    ("docs/package.json", '{"scripts": {"postinstall": "node x.js"}}\n', "a tool's configuration or a hidden file"),   # Review A, round 2
    ("docs/site/tsconfig.json", "{}\n", "a tool's configuration or a hidden file"),
    ("docs/requirements.txt", "requests==2.0\n", "a tool's configuration or a hidden file"),
    ("docs/Requirements-dev.txt", "pytest\n", "a tool's configuration or a hidden file"),
    ("docs/.vitepress/config.md", "# x\n", "a tool's configuration or a hidden file"),
    ("handoff/.notes.md", "# x\n", "a tool's configuration or a hidden file"),
])
def test_a_path_that_is_no_record_or_decides_a_gate_keeps_the_full_gate(repo, path, text, why):
    """One such file beside a plain record is enough: the whole pull request takes the round."""
    change(repo, "docs/PROJECT_STATUS.md", "Phase: done\n")
    change(repo, path, text)
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "FULL GATE  %s: " % path in out and why in out and "FULL GATE - 1 of 2 changed file(s)" in out, out


@pytest.mark.parametrize("register,named", [
    (REGISTER.replace("| planned | - |", "| built | tests/test_write.py |"), "R-002"),                      # a Status cell changed
    (REGISTER.replace("| R-002 | write the file | owner | planned | - |\n", ""), "R-002"),                   # a row left
    (REGISTER + "| R-003 | show a graph | owner | deferred - owner 2026-11-11 | - |\n", "R-003"),           # a new row that is not planned
    (REGISTER + "| R-003 | show a graph | owner | built | tests/test_graph.py |\n", "R-003"),
])
def test_the_register_keeps_the_full_gate_where_a_status_changed(repo, register, named):
    change(repo, "docs/REQUIREMENTS.md", register)
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "FULL GATE  docs/REQUIREMENTS.md: a Status cell changed, a row left, or a new row is not `planned`: %s" % named in out, out


@pytest.mark.parametrize("old,new", [
    ("| built | tests/test_parse.py |", "| built | tests/test_parse.py; tests/test_more.py |"),
    ("| built | tests/test_parse.py |", "| built | text: guide/loop.md :: The pause (#7) |"),
    ("| built | tests/test_parse.py |", "| built | - |"),
    ("| R-001 | parse the file |", "| R-001 | open the file |"),                         # the sentence the build is held to (Review A, round 2)
    ("| R-001 | parse the file | owner |", "| R-001 | parse the file | the supervisor |"),
])
def test_the_register_keeps_the_full_gate_where_a_built_row_changed(repo, old, new):
    """A built row's sentence and its Evidence are what completion-check.py holds the build to: a test named, a text entry
    written in its place, the cell emptied, the sentence reworded, each is read by both reviewers (Review A, round 1: a text
    entry alone once passed here; round 2: a reworded sentence did)."""
    change(repo, "docs/REQUIREMENTS.md", REGISTER.replace(old, new))
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "FULL GATE  docs/REQUIREMENTS.md: a built row changed, its sentence or its Evidence" in out and "R-001" in out, out


@pytest.mark.parametrize("path", ["docs/PROJECT_STATUS.md", "docs/INVENTORY.md", "docs/REQUIREMENTS.md", "project.json"])
def test_a_removed_record_the_guards_and_checks_read_keeps_the_full_gate(repo, path):
    change(repo, "handoff/TASK-002.md", "# TASK-002\n")
    git(repo, "rm", "-q", path)
    git(repo, "commit", "-q", "-m", "removed")
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "FULL GATE  %s: removed" % path in out, out


@pytest.mark.parametrize("mode,why", [("120000", "a link"), ("160000", "a link"), ("100755", "a link")])
def test_a_link_a_submodule_entry_and_an_executable_are_no_records(repo, program, mode, why):
    """Written into the index by its mode, as a checkout on any system can commit it; read in-process, since the working
    tree of this scratch repository does not hold what the index says."""
    mod = program("review-guard")
    base = git(repo, "rev-parse", "HEAD")
    value = "0" * 39 + "1" if mode == "160000" else git(repo, "hash-object", "-w", "docs/PROJECT_STATUS.md")
    git(repo, "update-index", "--add", "--cacheinfo", "%s,%s,docs/extra.md" % (mode, value))
    git(repo, "commit", "-q", "-m", "an entry that is no plain file")
    root, _, common = mod.find_git_dirs(str(repo))
    reasons = mod.full_gate_reasons(["docs/extra.md"], base, git(repo, "rev-parse", "HEAD"), root, common)
    assert len(reasons) == 1 and why in reasons[0][1] and mode in reasons[0][1], reasons


@pytest.mark.parametrize("after,why", [
    ('{"instruction_texts": ["guide/"]}\n', "`instruction_texts` changed"),
    ("{not json\n", "cannot be read on both sides"),
])
def test_the_project_file_keeps_the_full_gate_where_its_instruction_texts_changed(repo, after, why):
    change(repo, "project.json", after)
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "FULL GATE  project.json: " in out and why in out, out


def test_a_register_that_cannot_be_read_row_for_row_keeps_the_full_gate(repo):
    """The same ID twice: which row's Status counts is not for the guard to choose."""
    change(repo, "docs/REQUIREMENTS.md", REGISTER + "| R-002 | write the file | owner | built | tests/x.py |\n")
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "the register cannot be read row for row" in out, out


@pytest.mark.parametrize("inventory", [
    INVENTORY.replace("are outside input", "are trusted"),                                                   # the line reworded
    INVENTORY.replace("| The threat model: the builder and the reviewer are outside input | KP-032 |\n", ""),  # the line removed
    INVENTORY + "| The threat model does not cover the owner's own terminal | owner |\n",                     # a line added
])
def test_the_inventory_keeps_the_full_gate_where_a_threat_model_line_changed(repo, inventory):
    change(repo, "docs/INVENTORY.md", inventory)
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "FULL GATE  docs/INVENTORY.md: a line that names the threat model, or one under a heading that names it, changed" in out, out


def test_the_inventory_keeps_the_full_gate_where_a_line_under_a_threat_model_heading_changed(repo):
    """A model written as a section: its bullets do not name it, its heading does; the next heading ends it."""
    section = INVENTORY + "\n## The review guard's threat model\n\n- a reviewer in passing is inside it\n\n## Dates\n\n- UTC\n"
    change(repo, "docs/INVENTORY.md", section)                 # the section added: a heading that names the model
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    change(repo, "docs/INVENTORY.md", section.replace("- UTC", "- UTC, always"))
    rc, out = run(repo, "premerge-records")
    assert rc == 0 and "SHORT GATE" in out, out
    change(repo, "docs/INVENTORY.md", section.replace("is inside it", "is outside it"))
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "or one under a heading that names it, changed" in out, out


def test_a_sub_heading_stays_inside_the_threat_model_s_section(repo):
    """`## Threat model` with `### The review guard` under it and bullets under that (Review A, round 2: the sub-heading ended
    the section and its bullets changed on the short gate); a heading of the same level ends it."""
    section = INVENTORY + "\n## Threat model\n\n### The review guard\n\n- a finding outside it is recorded\n\n## Dates\n\n### Zones\n\n- UTC\n"
    change(repo, "docs/INVENTORY.md", section)
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    change(repo, "docs/INVENTORY.md", section.replace("- UTC", "- UTC, always"))
    rc, out = run(repo, "premerge-records")
    assert rc == 0 and "SHORT GATE" in out, out
    change(repo, "docs/INVENTORY.md", section.replace("a finding outside it is recorded", "every finding blocks"))
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "or one under a heading that names it, changed" in out, out


@pytest.mark.parametrize("sample", [
    "```\n# a comment in a sample\n```\n",                           # a fenced block (Review B, round 1: its `#` line ended the section)
    "````text\n```\n# still inside the longer fence\n```\n````\n",   # a shorter fence inside a longer one closes nothing
    "~~~\n## not a heading\n~~~\n",
    "<!--\n# a note to the editor\n-->\n",                           # an HTML comment
    "    # indented as code\n",
    "#no space, no heading\n",
])
def test_only_a_heading_markdown_would_draw_ends_the_threat_model_s_section(repo, sample):
    """A line that starts with `#` inside a code sample, a comment or an indented block is a line of the section: the line
    below it is still the model's, and its change keeps the full gate."""
    section = INVENTORY + "\n## Threat model\n\n- the builder is outside input\n\n" + sample + "\n- a finding outside it is recorded\n\n## Dates\n\n- UTC\n"
    change(repo, "docs/INVENTORY.md", section)
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    change(repo, "docs/INVENTORY.md", section.replace("- UTC", "- UTC, always"))
    rc, out = run(repo, "premerge-records")
    assert rc == 0 and "SHORT GATE" in out, out
    change(repo, "docs/INVENTORY.md", section.replace("a finding outside it is recorded", "every finding blocks"))
    rc, out = run(repo, "premerge-records")
    assert rc == 1 and "or one under a heading that names it, changed" in out, out


def test_a_dirty_tree_no_change_and_an_unknown_upstream_cannot_be_checked(repo):
    rc, out = run(repo, "premerge-records")
    assert rc == 2 and "HEAD changes nothing against origin/main" in out, out
    (repo / "docs" / "PROJECT_STATUS.md").write_text("Phase: done\n", encoding="utf-8")
    rc, out = run(repo, "premerge-records")
    assert rc == 2 and "the tree is not clean" in out, out
    git(repo, "commit", "-q", "-am", "records")
    git(repo, "update-ref", "-d", "refs/remotes/origin/main")
    rc, out = run(repo, "premerge-records")
    assert rc == 2 and "origin/main is not known here" in out, out


# ---------------------------------------------------------------- with the pull request: GitHub's list, the head, the record


@pytest.fixture
def guard(repo, program, monkeypatch):
    for k in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"):
        monkeypatch.setenv(k, os.devnull)
    mod = program("review-guard")
    sleeps = []
    real_time = mod.time

    class GuardTime:
        sleep = staticmethod(sleeps.append)

        def __getattr__(self, name):
            return getattr(real_time, name)

    monkeypatch.setattr(mod, "time", GuardTime())

    def github(*states, error=None):
        seq = list(states)
        monkeypatch.setattr(mod, "pr_state", lambda pr, root: (None, error) if error else ((seq.pop(0) if len(seq) > 1 else seq[0]), None))
    return mod, sleeps, github


def state(repo, files, head=None, base=None, into="main"):
    return {"head": head or git(repo, "rev-parse", "HEAD"), "base": base or git(repo, "rev-parse", "refs/remotes/origin/main"), "into": into,
            "files": list(files)}


def test_with_the_pull_request_the_record_is_written_and_the_permission_guard_lets_the_merge_through(repo, guard, capsys):
    """The record is the one `premerge` writes, by the head's sha: the permission guard, which refuses a merge without it, reads it."""
    mod, sleeps, github = guard
    change(repo, "docs/PROJECT_STATUS.md", "Phase: done\n")
    head = git(repo, "rev-parse", "HEAD")
    github(state(repo, ["docs/PROJECT_STATUS.md"]))
    pg = _permission_guard(repo, head)
    assert pg("gh pr merge 12 --squash --match-head-commit %s" % head) is not None, "no record yet: the merge is refused"
    rc = mod.cmd_premerge_records(str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 0 and "OK - records only, 1 file(s)" in out and "gh pr merge 12 --squash --match-head-commit %s" % head in out, out
    assert premerge_record(repo) == [head] and sleeps == []
    record = json.loads((repo / ".git" / "bridge" / "premerge" / head).read_text(encoding="utf-8"))
    assert record["review"] == "records" and record["pr"] == "12" and record["files"] == ["docs/PROJECT_STATUS.md"], record
    assert pg("gh pr merge 12 --squash --match-head-commit %s" % head) is None, "with the record the merge passes the permission guard"


def _permission_guard(repo, head):
    """permission-guard.py's own reading of a merge command's words (`merge_reason`): None lets it through."""
    from conftest import load_program
    pg = load_program("permission-guard")
    return lambda command: pg.merge_reason(command.split()[3:], str(repo))


def test_a_file_github_lists_and_the_local_diff_lacks_is_classified_too(repo, guard, capsys):
    """origin/main moved, by anyone, to hide a code commit: the local diff from it shows records only, GitHub's list still names the
    program, and the pull request keeps the full gate."""
    mod, _, github = guard
    base = git(repo, "rev-parse", "HEAD")
    change(repo, "src/a.py", "x = 2\n", "the program")
    hidden = git(repo, "rev-parse", "HEAD")
    change(repo, "docs/PROJECT_STATUS.md", "Phase: done\n")
    github(state(repo, ["docs/PROJECT_STATUS.md", "src/a.py"], base=hidden))          # even the base GitHub reports is taken as moved
    rc = mod.cmd_premerge_records(str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 1 and "FULL GATE  src/a.py: not a record" in out and premerge_record(repo) == [], out
    github(state(repo, ["docs/PROJECT_STATUS.md"], base=base))                        # and a list that lacks it: the local diff from the true base names it
    rc = mod.cmd_premerge_records(str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 1 and "FULL GATE  src/a.py: not a record" in out and premerge_record(repo) == [], out


def test_a_lagging_head_is_read_again_and_one_that_still_differs_is_not_ready(repo, guard, capsys):
    mod, sleeps, github = guard
    change(repo, "docs/PROJECT_STATUS.md", "Phase: done\n")
    lagging = state(repo, ["docs/PROJECT_STATUS.md"], head="0" * 40)
    github(lagging, lagging, state(repo, ["docs/PROJECT_STATUS.md"]))
    rc = mod.cmd_premerge_records(str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 0 and "waited 30 seconds" in out and sleeps == [15, 15], out
    del sleeps[:]
    os.remove(str(repo / ".git" / "bridge" / "premerge" / git(repo, "rev-parse", "HEAD")))
    github(lagging)
    rc = mod.cmd_premerge_records(str(repo), "12")
    out = capsys.readouterr().out
    assert rc == 1 and "NOT READY" in out and "after waiting 90 seconds" in out and sum(sleeps) == 90 and premerge_record(repo) == [], out


def test_a_failed_gh_a_list_at_its_limit_and_a_base_not_fetched_write_nothing(repo, guard, capsys):
    mod, _, github = guard
    change(repo, "docs/PROJECT_STATUS.md", "Phase: done\n")
    github(error=": no pull requests found")
    assert mod.cmd_premerge_records(str(repo), "12") == 2 and "gh pr view failed: no pull requests found" in capsys.readouterr().out
    github(state(repo, ["docs/f%d.md" % i for i in range(100)]))
    assert mod.cmd_premerge_records(str(repo), "12") == 1 and "FULL GATE - the pull request changes 100 files or more" in capsys.readouterr().out
    github(state(repo, ["docs/PROJECT_STATUS.md"], base="1" * 40))
    assert mod.cmd_premerge_records(str(repo), "12") == 2 and "fetch first" in capsys.readouterr().out
    github(state(repo, ["docs/PROJECT_STATUS.md"], into="release-1"))
    assert mod.cmd_premerge_records(str(repo), "12") == 1 and "FULL GATE - the pull request merges into release-1, not main" in capsys.readouterr().out
    assert premerge_record(repo) == []


def test_the_whole_round_s_premerge_is_untouched_and_still_needs_its_verified_mark(repo):
    """The short gate is a second door only for records: `premerge <nnn>` on the same branch still refuses without a snapshot."""
    change(repo, "docs/PROJECT_STATUS.md", "Phase: done\n")
    rc, out = run(repo, "premerge", "TASK-001")
    assert rc == 2 and premerge_record(repo) == [], out
    rc, out = run(repo, "premerge-records", "12", "extra")
    assert rc == 2 and "premerge-records [<pr>]" in out, "more words than the command takes: the usage, nothing run"
