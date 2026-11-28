"""TASK-091, the supervisor's acceptance tests: the heavy slot's line names the holder's limit, project and branch
(R-113).

enforces: docs/REQUIREMENTS.md R-113; docs/DESIGN.md, Change: the improvements release, C51; docs/BUILD_PLAN.md,
TASK-091's Done when.

- The holder record a heavy run publishes carries, beside the limit it holds already, `project` (the name of the
  holder's project folder: the launch folder's parent where the launch folder is named `Workspace`, the launch
  folder's own name otherwise; a name, never a path) and `branch` (the run's branch, as its run row records it).
  A value outside its character list or length bound is not written: the record goes without that field.
- The record's reader accepts each field only as a string of 1 to 64 characters of `A-Z a-z 0-9 . _ -` (project)
  or 1 to 100 characters of `A-Z a-z 0-9 . _ / -` (branch); a record whose field breaks that is no live record (as a
  malformed record is today: `held by unknown`). A record without the fields, as 2026.11.23a writes it, is read.
- The waiter's line, at once and at each repeat, and the line printed at the bound, read as on the checkpoint and go
  on with `, limit <seconds>s`, then `, project <name>` and `, branch <branch>` where the record holds them; the
  line naming several holders does the same in each holder's clause.
- No queue, no priority, no new option.

The builder reads and runs these tests and edits nothing in this file.
"""
import importlib.util
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
BRIDGE_DIR = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")
SESSION = {"start_new_session": True} if sys.platform != "win32" else {}
STAMP_RE = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ"


def load_br():
    spec = importlib.util.spec_from_file_location("bridge_run_slot_line", PROG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def env_for(scale="0.02"):
    env = dict(os.environ)
    env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    env["BRIDGE_RUN_SLOT_SCALE"] = scale
    return env


def holder_record_path(env):
    return os.path.join(str(env["HOME"]), ".cursor-bridge", "heavy.lock.holder")


def git(folder, *args):
    subprocess.run(["git", "-C", str(folder)] + list(args), check=True, capture_output=True)


def checkout(path, branch=None):
    """A launch folder with run/; a git checkout on `branch` where one is given."""
    path.mkdir(parents=True)
    (path / "run").mkdir()
    if branch:
        git(path, "init", "-q")
        git(path, "checkout", "-q", "-b", branch)
        git(path, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", "x")
    return path


class Launch:
    """A launcher started in the background; a thread reads its stderr lines."""

    def __init__(self, cwd, env, *args):
        self.proc = subprocess.Popen([sys.executable, PROG] + list(args), cwd=str(cwd), env=env,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, **SESSION)
        self.lines = []
        self.q = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for ln in iter(self.proc.stderr.readline, ""):
            self.q.put(ln.rstrip("\n"))
        self.q.put(None)

    def until(self, pred, timeout=20):
        end = time.monotonic() + timeout
        while True:
            left = end - time.monotonic()
            assert left > 0, "no such line in %r" % self.lines
            try:
                ln = self.q.get(timeout=left)
            except queue.Empty:
                continue
            assert ln is not None, "stderr ended: %r" % self.lines
            self.lines.append(ln)
            if pred(ln):
                return ln

    def run_id(self):
        return self.lines[0].split("started ", 1)[1]

    def kill(self):
        if self.proc.poll() is None:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(self.proc.pid), "/T", "/F"], capture_output=True)
            else:
                try:
                    os.killpg(os.getpgid(self.proc.pid), 9)
                except (OSError, ProcessLookupError):
                    self.proc.kill()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def holding_cmd(root):
    rel = str(root / "release")
    return [sys.executable, "-c", "import os,time\n[time.sleep(0.05) for _ in range(1200) if not os.path.exists(%r)]" % rel]


def kill_all(*launches):
    for la in launches:
        if la is not None:
            la.kill()


# ---------------------------------------------------------------- the record a holder publishes


def hold_and_read(tmp_path, env, folder):
    """Launch a holder in `folder`; return (its record as read from the file, its raw text, its Launch)."""
    la = Launch(folder, env, "--limit", "30", "--", *holding_cmd(folder))
    la.until(lambda ln: ln.startswith("bridge-run: slot taken "))
    path = holder_record_path(env)
    deadline = time.time() + 10
    raw = None
    while time.time() < deadline:
        try:
            raw = open(path, encoding="utf-8").read()
            if json.loads(raw).get("run_id") == la.run_id():
                break
        except (OSError, ValueError):
            pass
        time.sleep(0.05)
    return json.loads(raw), raw, la


def test_r113_the_record_carries_the_project_folders_name_and_the_branch(tmp_path):
    """R-113. Red on the checkpoint: the record holds neither field."""
    env = env_for()
    ws = checkout(tmp_path / "proj-x" / "Workspace", branch="feat/x")
    la = None
    try:
        rec, raw, la = hold_and_read(tmp_path, env, ws)
    finally:
        (ws / "release").write_text("")
        kill_all(la)
    assert rec.get("project") == "proj-x", rec
    assert rec.get("branch") == "feat/x", rec
    assert rec.get("limit") == 30, rec
    assert str(tmp_path) not in raw and os.path.normcase(str(tmp_path)) not in os.path.normcase(raw), raw


def test_r113_a_launch_folder_not_named_workspace_is_its_own_project(tmp_path):
    env = env_for()
    folder = checkout(tmp_path / "plain-folder", branch="main")
    la = None
    try:
        rec, raw, la = hold_and_read(tmp_path, env, folder)
    finally:
        (folder / "release").write_text("")
        kill_all(la)
    assert rec.get("project") == "plain-folder" and rec.get("branch") == "main", rec


def test_r113_a_name_outside_the_list_is_not_written(tmp_path):
    """A project folder whose name holds a character outside the list (a space here) gives a record without
    `project`; a launch folder that is no git checkout gives one without `branch`; the record is still published."""
    env = env_for()
    ws = checkout(tmp_path / "my proj" / "Workspace")
    la = None
    try:
        rec, raw, la = hold_and_read(tmp_path, env, ws)
    finally:
        (ws / "release").write_text("")
        kill_all(la)
    assert "project" not in rec and "branch" not in rec, rec
    assert rec.get("kind") == "test" and rec.get("limit") == 30, rec


# ---------------------------------------------------------------- the waiter's line


def test_r113_the_waiters_line_names_the_limit_the_project_and_the_branch(tmp_path):
    """R-113. The waiter's first line and its repeats read as on the checkpoint and go on to name the holder's limit,
    project and branch. Red on the checkpoint."""
    env = env_for(scale="0.01")
    ws = checkout(tmp_path / "proj-x" / "Workspace", branch="feat/x")
    other = checkout(tmp_path / "other")
    holder = waiter = None
    try:
        holder = Launch(ws, env, "--limit", "30", "--", *holding_cmd(ws))
        holder.until(lambda ln: ln.startswith("bridge-run: slot taken "))
        taken = holder.lines[-1].split("slot taken ", 1)[1]
        time.sleep(0.3)
        waiter = Launch(other, env, "--limit", "30", "--", *holding_cmd(other))
        first = waiter.until(lambda ln: ln.startswith("bridge-run: waiting"))
        second = waiter.until(lambda ln: ln.startswith("bridge-run: waiting"))
    finally:
        (ws / "release").write_text("")
        (other / "release").write_text("")
        kill_all(holder, waiter)
    want = (r"bridge-run: waiting for the slot held by test %s since %s, ends by %s, limit 30s, project proj-x, "
            r"branch feat/x" % (re.escape(holder.run_id()), re.escape(taken), STAMP_RE))
    named = [ln for ln in (first, second) if "held by unknown" not in ln]
    assert named, (first, second)
    for ln in named:
        assert re.fullmatch(want, ln), ln


HOLD_SRC = r'''
import json, os, sys, time
import importlib.util
spec = importlib.util.spec_from_file_location("bridge_run", os.path.join(sys.argv[1], "bridge-run.py"))
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)
extra = json.loads(sys.argv[2])
lock_path, holder_path = br.heavy_state_paths()
os.makedirs(os.path.dirname(lock_path), exist_ok=True)
fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
if not br._try_lock_byte(fd):
    sys.exit(2)
rec = {"kind": "test", "run_id": "2026-04-01T00:00:00Z", "pid": os.getpid(),
       "created": br.process_creation_epoch(os.getpid()) or time.time(),
       "start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "limit": 3}
rec.update(extra)
with open(holder_path, "w", encoding="utf-8") as f:
    json.dump(rec, f)
time.sleep(30)
'''


def plant_holder(tmp_path, env, extra):
    script = tmp_path / "hold.py"
    script.write_text(HOLD_SRC, encoding="utf-8")
    p = subprocess.Popen([sys.executable, str(script), BRIDGE_DIR, json.dumps(extra)], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **SESSION)
    path = holder_record_path(env)
    deadline = time.time() + 10
    while time.time() < deadline and not os.path.exists(path):
        time.sleep(0.05)
    time.sleep(0.2)
    return p


def wait_out(tmp_path, env, extra):
    """A planted holder (limit 3) with `extra` fields, and a waiter that reaches its bound: the waiter's stderr lines."""
    root = checkout(tmp_path / "w")
    holder = None
    try:
        holder = plant_holder(tmp_path, env, extra)
        out = subprocess.run([sys.executable, PROG, "--limit", "5", "--", sys.executable, "-c", "pass"], cwd=str(root),
                             env=env, capture_output=True, text=True, timeout=40)
    finally:
        if holder is not None and holder.poll() is None:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(holder.pid), "/T", "/F"], capture_output=True)
            else:
                holder.kill()
            holder.wait(timeout=10)
    assert out.returncode == 123, out.stderr
    return out.stderr.splitlines()


def test_r113_the_line_at_the_bound_names_them_too(tmp_path):
    """R-113. Red on the checkpoint."""
    lines = wait_out(tmp_path, env_for(scale="0.001"), {"project": "proj-y", "branch": "task-091"})
    assert lines[-1] == "bridge-run: exit 123"
    assert re.fullmatch(r"bridge-run: slot not free - held by test 2026-04-01T00:00:00Z since %s, ends by %s, limit 3s, "
                        r"project proj-y, branch task-091" % (STAMP_RE, STAMP_RE), lines[-2]), lines[-2]
    waits = [ln for ln in lines if ln.startswith("bridge-run: waiting") and "unknown" not in ln]
    assert waits and all(ln.endswith(", limit 3s, project proj-y, branch task-091") for ln in waits), waits


def test_r113_an_older_record_is_read_and_named_without_them(tmp_path):
    """R-113. A record as 2026.11.23a writes it (no project, no branch) is a live record: its lines name the holder
    as on the checkpoint and its limit. Red on the checkpoint (no limit named)."""
    lines = wait_out(tmp_path, env_for(scale="0.001"), {})
    assert re.fullmatch(r"bridge-run: slot not free - held by test 2026-04-01T00:00:00Z since %s, ends by %s, limit 3s"
                        % (STAMP_RE, STAMP_RE), lines[-2]), lines[-2]


@pytest.mark.parametrize("extra", [
    {"project": "a/b"}, {"project": "..\\x"}, {"project": "x" * 65}, {"project": ""}, {"project": 5},
    {"project": "caf\u00e9"}, {"project": "a b"}, {"branch": "a b"}, {"branch": "b" * 101}, {"branch": "x\ny"},
    {"branch": None}, {"branch": ""},
], ids=["slash", "backslash", "long-project", "empty-project", "number", "non-ascii", "space", "branch-space",
        "long-branch", "newline", "null-branch", "empty-branch"])
def test_r113_a_record_whose_new_field_breaks_the_rules_is_no_live_record(tmp_path, extra):
    """R-113. As the checkpoint treats a malformed record: the reader returns None, the waiter says `held by
    unknown`."""
    lines = wait_out(tmp_path, env_for(scale="0.001"), extra)
    assert lines[-2] == "bridge-run: slot not free - held by unknown", lines[-2]


# ---------------------------------------------------------------- the reader and the lines, in the program


def live_record(**extra):
    br = load_br()
    rec = {"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": os.getpid(),
           "created": br.process_creation_epoch(os.getpid()), "limit": 10}
    rec.update(extra)
    return br, rec


def test_r113_the_reader_returns_the_fields(tmp_path):
    br, rec = live_record(project="p18-claude-cursor-bridge", branch="task-091")
    path = tmp_path / "holder.json"
    path.write_text(json.dumps(rec), encoding="utf-8")
    got = br.read_holder_record(str(path))
    assert got is not None and got.get("project") == "p18-claude-cursor-bridge" and got.get("branch") == "task-091", got
    bounds = dict(rec, project="p" * 64, branch="b/" * 50)
    path.write_text(json.dumps(bounds), encoding="utf-8")
    assert br.read_holder_record(str(path)) is not None, "64 and 100 characters are within the bounds"


def test_r113_each_line_form_names_them():
    br, rec = live_record(project="proj", branch="main")
    grace = br.SLOT_GRACE
    tail = ", ends by 2026-01-01T00:02:10Z, limit 10s, project proj, branch main"
    head = "held by test 2026-01-01T00:00:00Z since 2026-01-01T00:00:00Z"
    assert br._waiting_line(rec, grace) == "bridge-run: waiting for the slot " + head + tail + "\n"
    assert br._slot_not_free_line(rec, grace) == "bridge-run: slot not free - " + head + tail + "\n"
    other = dict(rec, run_id="2026-01-01T00:00:05Z", project="q")
    del other["branch"]
    assert br._waiting_line_multi(2, [rec, other], grace) == (
        "bridge-run: waiting for a slot (2 of 2 held): test 2026-01-01T00:00:00Z since 2026-01-01T00:00:00Z" + tail
        + "; test 2026-01-01T00:00:05Z since 2026-01-01T00:00:00Z, ends by 2026-01-01T00:02:10Z, limit 10s, project q\n")


def test_r113_no_new_option():
    """R-113: no queue, no priority, no new option: the usage text names the checkpoint's options only."""
    p = subprocess.run([sys.executable, PROG], capture_output=True, text=True, timeout=60)
    assert p.returncode == 2
    assert set(re.findall(r"--[a-z][a-z-]*", p.stderr)) == {"--limit", "--kind", "--strip", "--key-file", "--healthy"}, \
        p.stderr
