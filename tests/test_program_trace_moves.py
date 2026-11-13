"""The trace check's move mode, `trace-check.py --moves [--base <rev>]` (R-077, T-MOVE).

The supervisor's acceptance tests for TASK-057, written before the build. Most tests build a scratch repository:
- its `main` is the base, with `origin/main` beside it;
- a branch carries the change;
- the mode runs on the branch with `--repo`.

The last test runs the mode on this repository's own history.

What the tests pin, as docs/TRACE_MOVES.md states it:
- **Entry.** An entry is the line `- <sha256 of the passage's normal form> <its first eight words>`. The words are escaped as the pinned mode escapes a field.
- **First output line.** It names the full commit id of the base the mode used: the merge-base of HEAD with `origin/main` or with `--base`.
- **A drop.** It prints a line beginning `FAIL` that names the file and the passage's first words. It also prints the entry line that would excuse it.
- **An added entry that excuses nothing.** It prints a line beginning `FAIL` that names the entry's hash.
- **Exit codes.**
  - Exit 1: a `RESULT:` line that is not `RESULT: OK`.
  - Exit 0: `RESULT: OK` and the counts `<n> file(s) compared`, `<n> passage(s) compared` and `<n> excused`.
  - Exit 2: a base that cannot be read, or a `--base` beginning with `-`.

enforces: docs/BUILD_PLAN.md, TASK-057, Done when; docs/REQUIREMENTS.md, R-077; docs/DESIGN.md, Change: the program release, T-MOVE.
"""
import hashlib
import os
import pathlib
import re
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
TRACE = REPO / "bridge" / "cursor-bridge" / "trace-check.py"

ALPHA = "bridge/cursor-bridge/workflow/phases/alpha.md"
BETA = "bridge/commands/beta.md"
CHANGELOG = "bridge/cursor-bridge/CHANGELOG.md"
MOVES = "docs/TRACE_MOVES.md"

P1 = "The first passage says what the loop does before every brief is written for the builder."
P2 = "The second passage says the review guard counts every round it opens for an increment."
P3 = "The third passage says that nothing reaches main except through the verified gate."
P4 = "The fourth passage is new on main after the branch was cut from it."
PB = "The beta passage says how the owner is told about a decision that is theirs."
P2_REWORDED = "The second passage says the review guard counts every round the launcher logs for it."
DASH = chr(0x2014)
PD = "The gate " + DASH + " never bypassed " + DASH + " holds every merge for the owner today."

MOVES_HEAD = "# Trace moves\n\nThe form is stated in the bridge's own record.\n\n## Entries\n"


def env():
    return dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x",
                GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=env())
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def put(repo, rel, text):
    full = repo / rel
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(text, encoding="utf-8", newline="\n")


def commit(repo, message="change"):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def escape_field(text):
    """The pinned mode's escaping, written out here so the test does not take it from the program it tests."""
    out = []
    for ch in text:
        code = ord(ch)
        if code < 0x20 or code == 0x7f:
            out.append("\\x%02x" % code)
        elif code < 128:
            out.append(ch)
        elif code < 256:
            out.append("\\x%02x" % code)
        elif code <= 0xFFFF:
            out.append("\\u%04x" % code)
        else:
            out.append("\\U%08x" % code)
    return "".join(out)


def words(passage):
    return escape_field(" ".join(passage.split()[:8]))


def digest(passage):
    """A one-line paragraph's normal form is the line with its whitespace collapsed."""
    return hashlib.sha256(" ".join(passage.split()).encode("utf-8")).hexdigest()


def entry(passage):
    return "- %s %s" % (digest(passage), words(passage))


def doc(title, *passages):
    return "# %s\n\n" % title + "".join(p + "\n\n" for p in passages)


def add_entries(repo, *passages):
    text = (repo / MOVES).read_text(encoding="utf-8")
    put(repo, MOVES, text + "".join(entry(p) + "\n" for p in passages))


@pytest.fixture
def repo(tmp_path):
    """`main` holds alpha (P1, P2, P3), beta (PB), the CHANGELOG and the moves record; `origin/main` beside it; branch `work`."""
    r = tmp_path / "ws"
    r.mkdir()
    put(r, ALPHA, doc("Alpha", P1, P2, P3))
    put(r, BETA, doc("Beta", PB))
    put(r, CHANGELOG, "# Changelog\n\n## 2026.01.01a\n\nThe first release.\n")
    put(r, MOVES, MOVES_HEAD)
    put(r, "docs/notes.md", "# Notes\n\nNothing here.\n")
    git(r, "init", "-q", "-b", "main")
    commit(r, "base")
    git(r, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(r, "checkout", "-q", "-b", "work")
    return r


def run(repo, *args):
    p = subprocess.run([sys.executable, str(TRACE), "--moves", "--repo", str(repo)] + list(args), cwd=str(repo),
                       capture_output=True, text=True, env=env(), encoding="utf-8", errors="replace")
    return p.returncode, p.stdout


def fail_lines(out):
    return [l for l in out.splitlines() if l.startswith("FAIL")]


def count(out, label):
    m = re.search(r"\b(\d+) %s\b" % re.escape(label), out)
    assert m, "no '<n> %s' in the output:\n%s" % (label, out)
    return int(m.group(1))


def assert_ok(rc, out):
    assert rc == 0 and "RESULT: OK" in out and not fail_lines(out), out


def assert_fails(rc, out):
    assert rc == 1 and "RESULT: OK" not in out and re.search(r"^RESULT: ", out, re.M) and fail_lines(out), out


# ---------------------------------------------------------------- the five cases of the supervisor's acceptance tests


def test_r077_a_dropped_passage_fails_naming_its_file_its_first_words_and_its_entry(repo):
    put(repo, ALPHA, doc("Alpha", P1, P3))
    commit(repo)
    rc, out = run(repo)
    assert_fails(rc, out)
    assert any(ALPHA in l and words(P2) in l for l in fail_lines(out)), out
    assert entry(P2) in out, out                                    # the entry line, to paste
    assert len(fail_lines(out)) == 1, out                           # P1 and P3 stand; the heading is no passage


def test_r077_the_entry_the_range_adds_excuses_its_passage(repo):
    put(repo, ALPHA, doc("Alpha", P1, P3))
    add_entries(repo, P2)
    commit(repo)
    rc, out = run(repo)
    assert_ok(rc, out)
    assert count(out, "excused") == 1, out
    assert count(out, "file(s) compared") == 1, out                 # alpha alone changed under bridge/
    assert count(out, "passage(s) compared") == 3, out              # alpha's three passages at the base


def test_r077_an_added_entry_that_excuses_no_dropped_passage_is_a_finding(repo):
    put(repo, BETA, doc("Beta", PB, "A new beta passage added on the branch."))
    add_entries(repo, P1)                                           # P1 still stands at HEAD: nothing to excuse
    commit(repo)
    rc, out = run(repo)
    assert_fails(rc, out)
    assert any(digest(P1) in l for l in fail_lines(out)), out


def test_r077_an_entry_an_earlier_pull_request_added_is_never_read_again(repo):
    """main merged an entry for P2 earlier (its own pull request); the branch then drops P2: the old entry excuses nothing."""
    git(repo, "checkout", "-q", "main")
    add_entries(repo, P2)
    commit(repo, "an earlier pull request's entry")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(repo, "checkout", "-q", "-B", "work", "main")
    put(repo, ALPHA, doc("Alpha", P1, P3))
    commit(repo)
    rc, out = run(repo)
    assert_fails(rc, out)
    assert any(ALPHA in l and words(P2) in l for l in fail_lines(out)), out


def test_r077_an_earlier_entry_fails_no_later_pull_request(repo):
    """main merged P3's drop with its entry; a later branch that drops nothing passes, the earlier entry unread."""
    git(repo, "checkout", "-q", "main")
    put(repo, ALPHA, doc("Alpha", P1, P2))
    add_entries(repo, P3)
    commit(repo, "an earlier pull request: P3 retired with its entry")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(repo, "checkout", "-q", "-B", "work", "main")
    put(repo, BETA, doc("Beta", PB, "A new beta passage added on the branch."))
    commit(repo)
    rc, out = run(repo)
    assert_ok(rc, out)
    assert count(out, "excused") == 0, out


def test_r077_the_default_base_is_the_merge_base_with_origin_main_named_on_the_first_line(repo):
    """origin/main moved on after the branch was cut (P4 added): the default base is the merge-base, so P4 is no drop."""
    cut = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "main")
    put(repo, ALPHA, doc("Alpha", P1, P2, P3, P4))
    commit(repo, "main moves on")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(repo, "checkout", "-q", "work")
    put(repo, ALPHA, doc("Alpha", P1, P3))
    add_entries(repo, P2)
    commit(repo)
    rc, out = run(repo)
    assert_ok(rc, out)
    assert cut in out.splitlines()[0], out
    assert count(out, "excused") == 1, out


# ---------------------------------------------------------------- the further cases of the Done when


def test_r077_a_passage_moved_to_another_file_under_bridge_passes(repo):
    put(repo, ALPHA, doc("Alpha", P1, P3))
    put(repo, BETA, doc("Beta", PB, P2))
    commit(repo)
    rc, out = run(repo)
    assert_ok(rc, out)
    assert count(out, "excused") == 0, out


def test_r077_a_passage_moved_into_the_changelog_fails(repo):
    """The CHANGELOG is no place a passage may go."""
    put(repo, ALPHA, doc("Alpha", P1, P3))
    put(repo, CHANGELOG, "# Changelog\n\n## 2026.01.01a\n\nThe first release.\n\n" + P2 + "\n")
    commit(repo)
    rc, out = run(repo)
    assert_fails(rc, out)
    assert any(ALPHA in l and words(P2) in l for l in fail_lines(out)), out


def test_r077_a_reworded_passage_fails_and_only_its_own_entry_excuses_it(repo):
    """P2 reworded after its eighth word: no entry fails; an entry made from the new wording (same first words, another hash)
    excuses nothing and is itself a finding; the entry of the old wording excuses it."""
    assert words(P2) == words(P2_REWORDED) and digest(P2) != digest(P2_REWORDED)
    put(repo, ALPHA, doc("Alpha", P1, P2_REWORDED, P3))
    commit(repo)
    rc, out = run(repo)
    assert_fails(rc, out)
    assert entry(P2) in out, out

    add_entries(repo, P2_REWORDED)
    commit(repo, "a wrong entry")
    rc, out = run(repo)
    assert_fails(rc, out)
    assert any(ALPHA in l and words(P2) in l for l in fail_lines(out)), out
    assert any(digest(P2_REWORDED) in l for l in fail_lines(out)), out

    put(repo, MOVES, MOVES_HEAD + entry(P2) + "\n")
    commit(repo, "the right entry")
    rc, out = run(repo)
    assert_ok(rc, out)
    assert count(out, "excused") == 1, out


def test_r077_a_passage_outside_ascii_has_an_escaped_entry_that_excuses_it(repo):
    git(repo, "checkout", "-q", "main")
    put(repo, BETA, doc("Beta", PB, PD))
    commit(repo, "a passage with dashes")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(repo, "checkout", "-q", "-B", "work", "main")
    put(repo, BETA, doc("Beta", PB))
    commit(repo)
    rc, out = run(repo)
    assert_fails(rc, out)
    assert entry(PD) in out and entry(PD).isascii(), out
    add_entries(repo, PD)
    commit(repo, "its entry")
    rc, out = run(repo)
    assert_ok(rc, out)


def test_r077_a_deleted_file_fails_for_each_of_its_passages(repo):
    (repo / BETA).unlink()
    commit(repo)
    rc, out = run(repo)
    assert_fails(rc, out)
    assert any(BETA in l and words(PB) in l for l in fail_lines(out)), out
    add_entries(repo, PB)
    commit(repo, "its entry")
    rc, out = run(repo)
    assert_ok(rc, out)


def test_r077_a_renamed_file_passes(repo):
    git(repo, "mv", ALPHA, "bridge/cursor-bridge/workflow/phases/alpha-renamed.md")
    commit(repo)
    rc, out = run(repo)
    assert_ok(rc, out)
    assert count(out, "excused") == 0, out


def test_r077_a_base_two_merges_back_reads_an_earlier_drop_with_the_entry_that_merge_added(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "main")
    put(repo, ALPHA, doc("Alpha", P1, P3))
    add_entries(repo, P2)
    commit(repo, "merge one: P2 retired with its entry")
    put(repo, BETA, doc("Beta", PB, "A passage merge two added."))
    commit(repo, "merge two")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(repo, "checkout", "-q", "-B", "work", "main")
    put(repo, "docs/notes.md", "# Notes\n\nA record changed on the branch.\n")
    commit(repo)
    rc, out = run(repo, "--base", base)
    assert_ok(rc, out)
    assert base in out.splitlines()[0], out
    assert count(out, "excused") == 1, out


def test_r077_a_base_ahead_of_the_branch_takes_the_merge_base(repo):
    """main, ahead of the branch, added P4 and retired P3 with its entry: with `--base main` the mode compares from the
    merge-base, so neither main's new passage nor its entry is read."""
    cut = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "main")
    put(repo, ALPHA, doc("Alpha", P1, P2, P4))
    add_entries(repo, P3)
    commit(repo, "main moves on")
    git(repo, "checkout", "-q", "work")
    put(repo, BETA, doc("Beta", PB, "A new beta passage added on the branch."))
    commit(repo)
    rc, out = run(repo, "--base", "main")
    assert_ok(rc, out)
    assert cut in out.splitlines()[0], out


def test_r077_a_base_that_cannot_be_read_is_exit_2_never_a_pass(repo):
    """The mode answers on the default base first (an unknown option would also exit 2), then not on a base it cannot read."""
    put(repo, ALPHA, doc("Alpha", P1, P3))
    add_entries(repo, P2)
    commit(repo)
    assert_ok(*run(repo))
    rc, out = run(repo, "--base", "no-such-revision")
    assert rc == 2 and "RESULT: OK" not in out and "no-such-revision" in out, out


def test_r077_a_base_beginning_with_a_dash_is_refused(repo):
    put(repo, "docs/notes.md", "# Notes\n\nA record changed on the branch.\n")
    commit(repo)
    assert_ok(*run(repo))
    rc, out = run(repo, "--base=--output=x")
    assert rc == 2 and "RESULT: OK" not in out, out
    assert not (repo / "x").exists()


# ---------------------------------------------------------------- this repository's own history


def test_r077_the_mode_passes_on_this_repository_s_own_history():
    """On a pull request CI fetches the full history and the base is `origin/<the pull request's base branch>`; elsewhere the
    default base. Run alone with the pull request's variables set to see CI's case (KP-074)."""
    if not (REPO / ".git").exists():
        pytest.skip("no repository here (mutation-run.py's copy holds none)")
    shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=str(REPO), capture_output=True, text=True, env=env())
    on_pull_request = os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
    if shallow.stdout.strip() == "true":
        assert not on_pull_request, "CI's tests job fetches the full history on pull requests, so this test never skips there"
        pytest.skip("the history is shallow (a push to main checks out one commit)")
    base_branch = os.environ.get("GITHUB_BASE_REF", "")
    args = ["--base", "origin/" + base_branch] if base_branch else []
    if not base_branch:
        has_origin_main = subprocess.run(["git", "rev-parse", "--verify", "-q", "refs/remotes/origin/main"], cwd=str(REPO),
                                         capture_output=True, text=True, env=env())
        if has_origin_main.returncode != 0:
            pytest.skip("no origin/main in this checkout")
    rc, out = run(REPO, *args)
    assert_ok(rc, out)
