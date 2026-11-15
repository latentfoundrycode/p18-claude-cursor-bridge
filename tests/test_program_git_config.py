"""R-081, D-004: the launcher detects a change of git's configuration made by a test or driver run.

enforces: docs/BUILD_PLAN.md TASK-062 Done when; docs/REQUIREMENTS.md R-081; docs/diagrams/D-004-context-dfd.md
(the edge `p_bridge_run` to `p_supervisor`, "GIT-CONFIG line per difference on standard error, exit unchanged: a
detection, never a restore").

Around a run of kind test or driver the launcher reads, before and after, the bytes of `config` and
`info/attributes` in the common git folder, of `config.worktree` in the worktree's own git folder, and of every
entry of the hooks folders (the folder `core.hooksPath` named before the run, and the common folder's `hooks`),
and prints one line `bridge-run: GIT-CONFIG <path> <new|removed|changed>` per difference on standard error, after
the run's own output and before the exit line; the path is relative to the folder that holds the common git
folder, with forward slashes. The exit code, the log row and the limit are unchanged and nothing is restored.

Every launch here runs in a repository under the test's temporary folder, with its own home folder (so the
computer's heavy slot and the agent home are the test's own) and `BRIDGE_RUN_ALLOW_ANY=1`, which lets the
launcher start a plain `python -c` as a test run; nothing reaches the checkout's `run/launcher/`.
"""
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
LINE = re.compile(r"^bridge-run: GIT-CONFIG (.+) (new|removed|changed|unreadable)$")
CHILD_DONE = "child done"


def git(cwd, *args):
    p = subprocess.run(["git", "-C", str(cwd)] + list(args), capture_output=True, text=True,
                       creationflags=NO_WINDOW, timeout=120)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def make_repo(tmp_path):
    """A repository at <tmp>/proj/Workspace with one commit (a worktree needs one) and a project's `run/` folder,
    where the launcher writes its log row (`write_log` writes only where `run/` exists; round 2's correction)."""
    ws = tmp_path / "proj" / "Workspace"
    ws.mkdir(parents=True)
    (ws / "run").mkdir()
    git(ws, "init", "-q")
    git(ws, "config", "user.email", "test@example.invalid")
    git(ws, "config", "user.name", "test")
    git(ws, "config", "commit.gpgsign", "false")
    (ws / "a.txt").write_text("a\n", encoding="utf-8")
    git(ws, "add", "a.txt")
    git(ws, "commit", "-q", "-m", "init")
    return ws


def env_for(tmp_path):
    env = dict(os.environ)
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env.update(HOME=str(home), USERPROFILE=str(home), LOCALAPPDATA=str(tmp_path / "localappdata"),
               BRIDGE_RUN_ALLOW_ANY="1", GIT_CEILING_DIRECTORIES=str(tmp_path))
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "BRIDGE_RUN_SLOT_SCALE"):
        env.pop(name, None)
    return env


def child_code(body, exit_code=0):
    """A python -c program: run `body` (statements, `os`, `subprocess` and `pathlib` imported), write the
    marker line on stderr, exit with `exit_code`."""
    return ("import os, subprocess, pathlib, sys\n" + body + "\n"
            "sys.stderr.write(%r + chr(10)); sys.stderr.flush(); sys.exit(%d)\n" % (CHILD_DONE, exit_code))


def launch(tmp_path, cwd, code, kind="test", strip=False):
    flags = ["--limit", "60"] + (["--strip"] if strip else []) + ["--kind", kind]
    return subprocess.run([sys.executable, PROG] + flags + ["--", sys.executable, "-c", code],
                          capture_output=True, text=True, env=env_for(tmp_path), cwd=str(cwd),
                          creationflags=NO_WINDOW, timeout=120)


def git_config_lines(stderr):
    return sorted(m.group(1).replace(chr(92), "/") + " " + m.group(2)
                  for m in (LINE.match(line) for line in stderr.splitlines()) if m)


def rows(ws):
    path = ws / "run" / "launcher" / "runs.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


GIT_IN_CHILD = "subprocess.run(['git'] + %r, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))"


def test_r081_the_reproduction_a_stripped_test_that_writes_core_fsmonitor_is_named(tmp_path):
    """Release T's stage T2 (docs/HARDENING.md): a stripped test run writes `core.fsmonitor` into the checkout's
    `.git/config` with git itself; the launcher names `.git/config changed`, after the run's own output and before
    the exit line, which stays the last; the run's exit code passes through and the line is not restored."""
    ws = make_repo(tmp_path)
    p = launch(tmp_path, ws, child_code(GIT_IN_CHILD % ["config", "core.fsmonitor", "echo planted"], exit_code=3),
               strip=True)
    assert p.returncode == 3, p.stderr
    assert git_config_lines(p.stderr) == [".git/config changed"], p.stderr
    lines = p.stderr.splitlines()
    at = [i for i, line in enumerate(lines) if LINE.match(line)]
    assert at and min(at) > lines.index(CHILD_DONE), "the line comes after the run's own output: " + p.stderr
    assert lines[-1] == "bridge-run: exit 3", "the exit line stays the last (review-guard reads it): " + p.stderr
    assert "fsmonitor" in (ws / ".git" / "config").read_text(encoding="utf-8"), "a detection, never a restore"


def test_r081_a_run_that_changes_nothing_prints_no_line_and_the_log_row_is_unchanged(tmp_path):
    """A run that changes nothing prints no GIT-CONFIG line; a run that changes the config writes a log row with the
    same fields as one that does not (no field added), its exit and its limit as given."""
    ws = make_repo(tmp_path)
    quiet = launch(tmp_path, ws, child_code("pass"))
    assert quiet.returncode == 0, quiet.stderr
    assert git_config_lines(quiet.stderr) == [] and "GIT-CONFIG" not in quiet.stderr, quiet.stderr
    loud = launch(tmp_path, ws, child_code(GIT_IN_CHILD % ["config", "core.fsmonitor", "echo planted"], exit_code=2))
    assert loud.returncode == 2 and git_config_lines(loud.stderr) == [".git/config changed"], loud.stderr
    first, second = rows(ws)[-2:]
    assert set(first) == set(second), (sorted(first), sorted(second))
    assert second["exit"] == 2 and second["limit"] == 60 and second["kind"] == "test"


def test_r081_a_hook_file_added_is_new(tmp_path):
    ws = make_repo(tmp_path)
    body = "pathlib.Path('.git/hooks/pre-commit').write_text('#!/bin/sh' + chr(10) + 'exit 0' + chr(10))"
    p = launch(tmp_path, ws, child_code(body))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/hooks/pre-commit new"], p.stderr


def test_r081_a_hook_replaced_by_a_file_of_the_same_size_is_changed(tmp_path):
    """Compared by content, never by size or time alone."""
    ws = make_repo(tmp_path)
    hook = ws / ".git" / "hooks" / "pre-commit"
    hook.write_bytes(b"#!/bin/sh\nexit 0\n")
    st = os.stat(hook)
    body = ("p = pathlib.Path('.git/hooks/pre-commit'); p.write_bytes(b'#!/bin/sh' + bytes([10]) + b'exit 1' + bytes([10]))\n"
            "os.utime(p, ns=(%d, %d))" % (st.st_atime_ns, st.st_mtime_ns))
    p = launch(tmp_path, ws, child_code(body))
    assert p.returncode == 0, p.stderr
    assert hook.stat().st_size == st.st_size
    assert git_config_lines(p.stderr) == [".git/hooks/pre-commit changed"], p.stderr


def test_r081_a_hook_removed_is_removed(tmp_path):
    ws = make_repo(tmp_path)
    (ws / ".git" / "hooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    p = launch(tmp_path, ws, child_code("os.remove('.git/hooks/pre-commit')"))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/hooks/pre-commit removed"], p.stderr


def test_r081_a_hooks_path_set_during_the_run_is_a_config_change(tmp_path):
    """Setting `core.hooksPath` is a change of `.git/config`; the folder it now names was not the hooks folder
    before the run, so a hook written there in the same run adds no line of its own."""
    ws = make_repo(tmp_path)
    body = (GIT_IN_CHILD % ["config", "core.hooksPath", "planted-hooks"]) + "\n" + \
        "os.makedirs('planted-hooks'); pathlib.Path('planted-hooks/pre-commit').write_text('exit 0')"
    p = launch(tmp_path, ws, child_code(body))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/config changed"], p.stderr


def test_r081_the_folder_core_hooks_path_named_before_the_run_is_read(tmp_path):
    """With `core.hooksPath` set before the run, that folder's entries are compared by name and content, and the
    common folder's `hooks` too."""
    ws = make_repo(tmp_path)
    git(ws, "config", "core.hooksPath", ".githooks")
    (ws / ".githooks").mkdir()
    (ws / ".githooks" / "pre-commit").write_text("exit 0\n", encoding="utf-8")
    body = ("pathlib.Path('.githooks/pre-commit').write_text('exit 1' + chr(10))\n"
            "pathlib.Path('.githooks/post-checkout').write_text('exit 0' + chr(10))\n"
            "pathlib.Path('.git/hooks/pre-push').write_text('exit 0' + chr(10))")
    p = launch(tmp_path, ws, child_code(body))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/hooks/pre-push new", ".githooks/post-checkout new",
                                          ".githooks/pre-commit changed"], p.stderr


def test_r081_an_attributes_file_added_is_new(tmp_path):
    ws = make_repo(tmp_path)
    body = "os.makedirs('.git/info', exist_ok=True); pathlib.Path('.git/info/attributes').write_text('* diff=planted' + chr(10))"
    p = launch(tmp_path, ws, child_code(body))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/info/attributes new"], p.stderr


def test_r081_an_attributes_file_removed_is_removed(tmp_path):
    ws = make_repo(tmp_path)
    (ws / ".git" / "info").mkdir(exist_ok=True)
    (ws / ".git" / "info" / "attributes").write_text("* text=auto\n", encoding="utf-8")
    p = launch(tmp_path, ws, child_code("os.remove('.git/info/attributes')"))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/info/attributes removed"], p.stderr


def test_r081_a_config_worktree_written_in_a_worktree_is_new(tmp_path):
    """Launched in a linked worktree: `config.worktree` in the worktree's own git folder
    (`.git/worktrees/<name>/` of the main repository), the path relative to the folder that holds the common git
    folder."""
    ws = make_repo(tmp_path)
    wt = tmp_path / "proj" / "wt"
    git(ws, "worktree", "add", "-q", str(wt))
    body = ("d = subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True, text=True, check=True, "
            "creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout.strip()\n"
            "pathlib.Path(d, 'config.worktree').write_text('[core]' + chr(10) + '  fsmonitor = echo planted' + chr(10))")
    p = launch(tmp_path, wt, child_code(body))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/worktrees/wt/config.worktree new"], p.stderr


def test_r081_a_driver_run_is_read_too(tmp_path):
    """A driver run (a program under run/supervisor/) is read like a test run."""
    ws = make_repo(tmp_path)
    prog = ws / "run" / "supervisor" / "plant.py"
    prog.parent.mkdir(parents=True)
    prog.write_text("import pathlib\npathlib.Path('.git/hooks/post-merge').write_text('exit 0')\n", encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, "--limit", "60", "--kind", "driver", "--", "python", str(prog)],
                       capture_output=True, text=True, env=env_for(tmp_path), cwd=str(ws),
                       creationflags=NO_WINDOW, timeout=120)
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/hooks/post-merge new"], p.stderr


@pytest.mark.parametrize("kind", ["builder", "review"])
def test_r081_builder_and_review_runs_are_untouched(tmp_path, kind):
    """The guard and BOUNDARY hold builder and review runs; the launcher prints no GIT-CONFIG line for them."""
    ws = make_repo(tmp_path)
    p = launch(tmp_path, ws, child_code(GIT_IN_CHILD % ["config", "core.fsmonitor", "echo planted"]), kind=kind)
    assert p.returncode == 0, p.stderr
    assert "GIT-CONFIG" not in p.stderr, p.stderr


def test_r081_a_launch_folder_in_no_repository_prints_nothing(tmp_path):
    folder = tmp_path / "plain"
    folder.mkdir()
    p = launch(tmp_path, folder, child_code("pathlib.Path('config').write_text('x')"))
    assert p.returncode == 0, p.stderr
    assert "GIT-CONFIG" not in p.stderr, p.stderr


def test_r081_a_launch_from_a_sub_folder_reads_the_hooks_path_folder(tmp_path):
    """Launched from a sub-folder of the worktree with a relative `core.hooksPath` set before the run: the folder git
    uses is the one at the worktree's top, read once, its change named relative to the common folder's parent."""
    ws = make_repo(tmp_path)
    git(ws, "config", "core.hooksPath", ".githooks")
    (ws / ".githooks").mkdir()
    (ws / ".githooks" / "pre-commit").write_text("exit 0\n", encoding="utf-8")
    sub = ws / "sub"
    sub.mkdir()
    p = launch(tmp_path, sub, child_code("pathlib.Path('../.githooks/pre-commit').write_text('exit 1' + chr(10))"))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".githooks/pre-commit changed"], p.stderr


def test_r081_a_launch_from_a_sub_folder_without_a_hooks_path_reads_git_hooks_once(tmp_path):
    ws = make_repo(tmp_path)
    sub = ws / "sub"
    sub.mkdir()
    p = launch(tmp_path, sub, child_code("pathlib.Path('../.git/hooks/pre-push').write_text('exit 0')"))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/hooks/pre-push new"], p.stderr


def test_r081_a_hook_replaced_by_a_folder_is_unreadable(tmp_path):
    """A hooks entry that is not a regular file is never opened: it reads as unreadable."""
    ws = make_repo(tmp_path)
    (ws / ".git" / "hooks" / "pre-commit").write_text("exit 0\n", encoding="utf-8")
    p = launch(tmp_path, ws, child_code("os.remove('.git/hooks/pre-commit'); os.makedirs('.git/hooks/pre-commit')"))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/hooks/pre-commit unreadable"], p.stderr


def test_r081_a_sub_folder_of_a_hooks_folder_present_before_and_after_prints_nothing(tmp_path):
    ws = make_repo(tmp_path)
    (ws / ".git" / "hooks" / "lib").mkdir()
    (ws / ".git" / "hooks" / "lib" / "x.sh").write_text("exit 0\n", encoding="utf-8")
    p = launch(tmp_path, ws, child_code("pathlib.Path('.git/hooks/lib/x.sh').write_text('exit 1')"))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [], p.stderr


@pytest.mark.skipif(sys.platform == "win32", reason="a named pipe in a folder is POSIX's mkfifo")
def test_r081_a_fifo_planted_in_a_hooks_folder_is_unreadable_and_the_run_ends(tmp_path):
    """Opening a FIFO blocks until a writer comes: the after-read never opens what is not a regular file, so the run
    ends with its exit line and the entry reads unreadable."""
    ws = make_repo(tmp_path)
    p = launch(tmp_path, ws, child_code("os.mkfifo('.git/hooks/post-merge')"))
    assert p.returncode == 0, p.stderr
    assert git_config_lines(p.stderr) == [".git/hooks/post-merge unreadable"], p.stderr
    assert p.stderr.splitlines()[-1] == "bridge-run: exit 0", p.stderr


# The child swaps the hooks folder for a link to a folder that needs no privilege: a junction on Windows, a symbolic
# link elsewhere.
LINK_CHILD = ("os.rename('.git/hooks', '.git/hooks-moved')\n"
              + ("import _winapi\n_winapi.CreateJunction(%r, '.git/hooks')" if sys.platform == "win32"
                 else "os.symlink(%r, '.git/hooks')"))


def test_r081_a_hooks_folder_swapped_for_a_link_is_not_listed_through_it(tmp_path):
    """A run that replaces the hooks folder with a junction (no privilege needed) to a folder full of files: the
    after-read never lists through the link; the folder's own line is `unreadable` and its entries read as absent,
    so no entry of the link's target is named."""
    ws = make_repo(tmp_path)
    target = tmp_path / "elsewhere"
    target.mkdir()
    for name in ("one.exe", "two.dll", "three.sys"):
        (target / name).write_text(name, encoding="utf-8")
    (ws / ".git" / "hooks" / "pre-commit").write_text("exit 0\n", encoding="utf-8")
    p = launch(tmp_path, ws, child_code(LINK_CHILD % str(target)))
    assert p.returncode == 0, p.stderr
    lines = git_config_lines(p.stderr)
    assert ".git/hooks unreadable" in lines, p.stderr
    assert ".git/hooks/pre-commit removed" in lines, p.stderr
    assert not any(n in line for line in lines for n in ("one.exe", "two.dll", "three.sys")), p.stderr
    assert all(line == ".git/hooks unreadable" or line.endswith(" removed") for line in lines), p.stderr


def test_r081_a_worktree_s_git_file_and_commondir_are_read(tmp_path):
    """In a linked worktree, the `.git` file at its top (`gitdir: ...`) and `commondir` in its own git folder steer
    every later git command there: a run that rewrites either is named (security audit, round 1)."""
    ws = make_repo(tmp_path)
    wt = tmp_path / "proj" / "wt"
    git(ws, "worktree", "add", "-q", str(wt))
    body = ("d = subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True, text=True, check=True, "
            "creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout.strip()\n"
            "open(os.path.join(d, 'commondir'), 'a').write(chr(10))\n"
            "open('.git', 'a').write(chr(10))")        # appended: Windows refuses to truncate the hidden `.git` file
    p = launch(tmp_path, wt, child_code(body))
    assert p.returncode == 0, p.stderr
    lines = git_config_lines(p.stderr)
    assert ".git/worktrees/wt/commondir changed" in lines, p.stderr
    assert any(line.endswith("wt/.git changed") for line in lines), p.stderr
    assert len(lines) == 2, p.stderr


def test_r081_a_read_that_fails_is_unreadable_and_changes_nothing_else(tmp_path):
    """A file the launcher cannot read after the run (here `info/attributes` made a folder) is named unreadable, its
    one line, and the run's exit and the other lines stand."""
    ws = make_repo(tmp_path)
    body = ("os.makedirs('.git/info/attributes')\n"
            "pathlib.Path('.git/hooks/pre-commit').write_text('exit 0')")
    p = launch(tmp_path, ws, child_code(body, exit_code=5))
    assert p.returncode == 5, p.stderr
    assert git_config_lines(p.stderr) == [".git/hooks/pre-commit new", ".git/info/attributes unreadable"], p.stderr
    assert p.stderr.splitlines()[-1] == "bridge-run: exit 5", p.stderr
