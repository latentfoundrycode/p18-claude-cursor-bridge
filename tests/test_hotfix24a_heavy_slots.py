"""HOTFIX-004 (hotfix 2026.11.24a): the heavy slots, a setting of 1 to 4 machine-wide heavy slots, one heavy run per
folder, unique run ids, and the mutation engine's per-run-id lock. The supervisor's acceptance tests
(run/supervisor/hotfix-004-design.md, "The behaviour" and "Tests", cases 1 to 10; case 11 is the existing suite);
each names the design line it enforces.

The harness follows tests/test_bridge_run_slot.py, copying the minimum so the file runs from tests/ or from
run/supervisor/: every launch is windowless, the slot's state folder (~/.cursor-bridge) lives under a temporary home
given through HOME and USERPROFILE, BRIDGE_RUN_ALLOW_ANY=1 lets a plain Python command run as a heavy (test) launch,
and BRIDGE_RUN_SLOT_SCALE shortens the waits. A launch holds its slot with a command that waits for a release file
the test writes, so the order of events is the test's, not a sleep's. No test runs cursor-agent."""
import importlib.util
import json
import os
import queue
import re
import stat
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

import pytest


def _repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    for _ in range(6):
        if os.path.isfile(os.path.join(d, "bridge", "cursor-bridge", "bridge-run.py")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("bridge/cursor-bridge/bridge-run.py not found above %s" % here)


ROOT = _repo_root()
BRIDGE_DIR = os.path.join(ROOT, "bridge", "cursor-bridge")
PROG = os.path.join(BRIDGE_DIR, "bridge-run.py")
MUTATION_PROG = os.path.join(BRIDGE_DIR, "mutation-run.py")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
SESSION = {"start_new_session": True} if sys.platform != "win32" else {"creationflags": NO_WINDOW}
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
       "-c", "commit.gpgsign=false"]
STAMP_RE = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ"
TAKEN_RE = r"bridge-run: slot taken " + STAMP_RE
NOTE_PREFIX = "bridge-run: note - heavy-slots.json ignored ("
NOTE_SUFFIX = "); one heavy slot"


def load_br():
    spec = importlib.util.spec_from_file_location("bridge_run", PROG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- the harness


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    (h / ".cursor").mkdir(parents=True)
    return h


@pytest.fixture
def env(home, tmp_path):
    """The launch environment: a temporary home (never the owner's ~/.cursor-bridge or ~/.claude), any-command
    launches, and slot waits scaled by 0.01 (the report every 0.6 s, a holder's grace 1.2 s, a test's floor 18 s)."""
    e = dict(os.environ)
    e.pop("BRIDGE_RUN_SLOT_SCALE", None)
    e["HOME"] = str(home)
    e["USERPROFILE"] = str(home)
    appdata = home.parent / "appdata"
    appdata.mkdir(exist_ok=True)
    e["APPDATA"] = str(appdata)
    e["BRIDGE_RUN_ALLOW_ANY"] = "1"
    e["BRIDGE_RUN_SLOT_SCALE"] = "0.01"
    return e


def state_dir(env):
    return os.path.join(env["USERPROFILE"], ".cursor-bridge")


def settings_path(env):
    return os.path.join(state_dir(env), "heavy-slots.json")


def write_settings(env, raw):
    os.makedirs(state_dir(env), exist_ok=True)
    data = raw if isinstance(raw, bytes) else raw.encode("utf-8")
    with open(settings_path(env), "wb") as f:
        f.write(data)


def launch_dir(tmp_path, name):
    root = tmp_path / name
    (root / "run").mkdir(parents=True)
    return root


def run_bridge(cwd, env, *args, timeout=30):
    return subprocess.run([sys.executable, PROG, *args], cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=timeout, **SESSION)


HOLD_SRC = (
    "import os, sys, time\n"
    "s, e, rel = sys.argv[1:4]\n"
    "open(s, 'w').write(repr(time.time()))\n"
    "end = time.monotonic() + 60\n"
    "while not os.path.exists(rel) and time.monotonic() < end:\n"
    "    time.sleep(0.05)\n"
    "open(e, 'w').write(repr(time.time()))\n"
)


def holding_cmd(root, tag=""):
    """A command that notes its start time in `<root>/s<tag>`, holds until `<root>/release<tag>` exists (at most
    60 s), and notes its end in `<root>/e<tag>`."""
    s, e, rel = (str(root / (n + tag)) for n in ("s", "e", "release"))
    code = ("import os,time;open(%r,'w').write(repr(time.time()));"
            "[time.sleep(0.05) for _ in range(1200) if not os.path.exists(%r)];"
            "open(%r,'w').write(repr(time.time()))" % (s, rel, e))
    return [sys.executable, "-c", code]


def release(root, tag=""):
    (root / ("release" + tag)).write_text("go", encoding="utf-8")


class Launch:
    """A bridge-run.py launch whose stderr a thread reads line by line into a queue, so a silent launch fails the
    test at a timeout instead of hanging it."""

    def __init__(self, cwd, env, *args):
        self.proc = subprocess.Popen([sys.executable, PROG, *args], cwd=str(cwd), env=env,
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                     text=True, **SESSION)
        self.lines = []
        self.ended = False
        self._q = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for ln in iter(self.proc.stderr.readline, ""):
            self._q.put(ln.rstrip("\n"))
        self._q.put(None)

    def until(self, pred, what, timeout=10):
        """The first new stderr line for which pred holds; fails at the timeout or at the end of stderr."""
        end = time.monotonic() + timeout
        while True:
            left = end - time.monotonic()
            assert left > 0, "no line %s within %ss; stderr so far: %r" % (what, timeout, self.lines)
            try:
                ln = self._q.get(timeout=min(left, 0.2))
            except queue.Empty:
                continue
            if ln is None:
                self.ended = True
                assert False, "stderr ended without a line %s: %r" % (what, self.lines)
            self.lines.append(ln)
            if pred(ln):
                return ln

    def until_prefix(self, prefix, timeout=10):
        return self.until(lambda ln: ln.startswith(prefix), "starting %r" % prefix, timeout)

    def finish(self, timeout=30):
        """Wait for the launch's end; return its whole stderr as a list of lines."""
        self.proc.wait(timeout=timeout)
        end = time.monotonic() + 10
        while not self.ended and time.monotonic() < end:
            try:
                ln = self._q.get(timeout=0.2)
            except queue.Empty:
                continue
            if ln is None:
                self.ended = True
            else:
                self.lines.append(ln)
        return self.lines

    def run_id(self):
        return self.lines[0].split("started ", 1)[1]

    def kill(self):
        kill_tree(self.proc)


def kill_tree(proc):
    if proc is None or proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), 9)
        except (OSError, ProcessLookupError):
            proc.kill()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def kill_all(*launches):
    for p in launches:
        if p is not None:
            kill_tree(p.proc if isinstance(p, Launch) else p)


def rows_of(root):
    log = root / "run" / "launcher" / "runs.jsonl"
    if not log.exists():
        return []
    return [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]


def row_of(root, run_id):
    hits = [r for r in rows_of(root) if r.get("id") == run_id]
    assert len(hits) == 1, "no single row for run %s in %r" % (run_id, rows_of(root))
    return hits[0]


def waits(lines):
    return [ln for ln in lines if ln.startswith("bridge-run: waiting")]


def taken_lines(lines):
    return [ln for ln in lines if ln.startswith("bridge-run: slot taken ")]


SLOT_HOLDER_SRC = r'''
import datetime, importlib.util, os, sys, time
bridge_dir, lock_name, run_id, limit, ready, rel = sys.argv[1:7]
spec = importlib.util.spec_from_file_location("bridge_run", os.path.join(bridge_dir, "bridge-run.py"))
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)
folder = os.path.dirname(br.heavy_state_paths()[0])
os.makedirs(folder, exist_ok=True)
lock_path = os.path.join(folder, lock_name)
fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
if not br._try_lock_byte(fd):
    sys.exit(2)
start = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
br.publish_holder_record(lock_path + ".holder", {
    "kind": "test", "run_id": run_id, "pid": os.getpid(),
    "created": br.process_creation_epoch(os.getpid()) or time.time(), "start": start, "limit": int(limit)})
open(ready, "w").close()
end = time.monotonic() + 120
while time.monotonic() < end and not os.path.exists(rel):
    time.sleep(0.05)
'''


def start_slot_holder(tmp_path, env, lock_name, run_id, limit):
    """A process that locks ~/.cursor-bridge/<lock_name> with bridge-run.py's own byte lock and publishes a live
    record beside it (`<lock_name>.holder`); returns (process, its release file)."""
    script = tmp_path / "slot_holder.py"
    script.write_text(SLOT_HOLDER_SRC, encoding="utf-8")
    ready, rel = tmp_path / ("ready-" + lock_name), tmp_path / ("release-" + lock_name)
    p = subprocess.Popen([sys.executable, str(script), BRIDGE_DIR, lock_name, run_id, str(limit), str(ready), str(rel)],
                         env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         **SESSION)
    end = time.monotonic() + 15
    while not ready.exists() and p.poll() is None and time.monotonic() < end:
        time.sleep(0.05)
    assert ready.exists(), "the slot holder of %s never held it (exit %r)" % (lock_name, p.poll())
    return p, rel


# ---------------------------------------------------------------- 1 to 3: the slots


def test_hotfix24a_no_setting_file_keeps_one_slot(tmp_path, env):
    """Test 1; the setting, "Absent: 1 slot, as 2026.11.23a, no line printed"; Taking a slot and Waiting, "with
    n = 1 ... the line is byte-identical to today's": with no heavy-slots.json, a second heavy launch from another
    folder waits while the first holds the slot and starts only after the first command ended; the slot-taken lines
    carry no suffix and the waiting line is today's."""
    a, b = launch_dir(tmp_path, "a"), launch_dir(tmp_path, "b")
    assert not os.path.exists(settings_path(env))
    first = second = None
    try:
        first = Launch(a, env, "--limit", "30", "--", *holding_cmd(a))
        first.until_prefix("bridge-run: slot taken ")
        second = Launch(b, env, "--limit", "30", "--", *holding_cmd(b))
        wait_line = second.until_prefix("bridge-run: waiting")
        time.sleep(1.0)
        assert second.proc.poll() is None and not (b / "s").exists()  # still waiting, its command not started
        release(a)
        err1 = first.finish()
        second.until_prefix("bridge-run: slot taken ")
        release(b)
        err2 = second.finish()
    finally:
        kill_all(first, second)
    assert first.proc.returncode == 0 and second.proc.returncode == 0, (err1, err2)
    assert float((b / "s").read_text()) >= float((a / "e").read_text())
    assert re.fullmatch(r"bridge-run: waiting for the slot held by test %s since %s, ends by %s"
                        % (re.escape(first.run_id()), STAMP_RE, STAMP_RE), wait_line), wait_line
    for err in (err1, err2):
        assert taken_lines(err) and all(re.fullmatch(TAKEN_RE, ln) for ln in taken_lines(err)), err
        assert not any("heavy-slots" in ln for ln in err), err
        assert err[-1] == "bridge-run: exit 0", err


def test_hotfix24a_two_slots_second_at_once_third_waits_on_both(tmp_path, env):
    """Test 2; Taking a slot, "With n > 1, `bridge-run: slot taken <time>Z` gains ` (slot <k> of <n>)`"; Waiting,
    "`bridge-run: waiting for a slot (<held> of <n> held): <kind> <run id> since <start>, ends by <end>; ...` (one
    clause per live holder, slot order)": with {"slots": 2} a second launch from another folder takes slot 2 at once,
    a third waits naming both holders, and when the first ends the third takes slot 1."""
    write_settings(env, json.dumps({"slots": 2}))
    a, b, c = (launch_dir(tmp_path, n) for n in ("a", "b", "c"))
    l1 = l2 = l3 = None
    try:
        l1 = Launch(a, env, "--limit", "30", "--", *holding_cmd(a))
        t1 = l1.until_prefix("bridge-run: slot taken ")
        assert re.fullmatch(TAKEN_RE + re.escape(" (slot 1 of 2)"), t1), t1
        l2 = Launch(b, env, "--limit", "30", "--", *holding_cmd(b))
        t2 = l2.until_prefix("bridge-run: slot taken ", timeout=8)
        assert not waits(l2.lines), l2.lines  # at once, never waiting
        assert re.fullmatch(TAKEN_RE + re.escape(" (slot 2 of 2)"), t2), t2
        rid1, rid2 = l1.run_id(), l2.run_id()
        l3 = Launch(c, env, "--limit", "30", "--", *holding_cmd(c))
        line = l3.until_prefix("bridge-run: waiting")
        clause = r"test %s since " + STAMP_RE + r", ends by " + STAMP_RE
        assert re.fullmatch(r"bridge-run: waiting for a slot \(2 of 2 held\): " + clause % re.escape(rid1)
                            + "; " + clause % re.escape(rid2), line), line
        assert not (c / "s").exists()
        release(a)
        l1.finish()
        t3 = l3.until_prefix("bridge-run: slot taken ")
        assert re.fullmatch(TAKEN_RE + re.escape(" (slot 1 of 2)"), t3), t3
        assert l2.proc.poll() is None  # slot 2 still held by the second
        release(b)
        release(c)
        l2.finish()
        l3.finish()
    finally:
        kill_all(l1, l2, l3)
    assert [p.proc.returncode for p in (l1, l2, l3)] == [0, 0, 0], (l1.lines, l2.lines, l3.lines)


def today_waiting_re(run_id):
    """Today's waiting line naming one live holder (the one-slot form the folder lock's waiter keeps)."""
    return r"bridge-run: waiting for the slot held by test %s since %s, ends by %s" % (re.escape(run_id), STAMP_RE, STAMP_RE)


@pytest.mark.parametrize("where", ["same-folder", "subfolder"])
def test_hotfix24a_same_checkout_waits_on_the_folder_lock(tmp_path, env, where):
    """Test 3 (first part); "One heavy run per checkout": "Before it tries any slot, a heavy launch takes an exclusive
    byte lock on `~/.cursor-bridge/heavy-folder-<h>.lock` ... raised to `git rev-parse --show-toplevel` ... A launch
    waiting for the folder lock waits exactly as for a busy slot: its waiting line names the folder lock's holder
    ... one checkout, top folder or subfolder, never two": with {"slots": 2} a second launch from the first's
    checkout (its folder, or a subfolder of the repository) waits naming the first run in today's waiting-line form,
    while a launch from another folder takes the free slot 2 at once; the waiter starts only after the first ends."""
    write_settings(env, json.dumps({"slots": 2}))
    repo = launch_dir(tmp_path, "repo")
    _git(repo, "init", "-q", "-b", "main")
    second_dir = repo if where == "same-folder" else repo / "sub" / "deeper"
    second_dir.mkdir(parents=True, exist_ok=True)
    other = launch_dir(tmp_path, "other")
    first = second = third = None
    try:
        first = Launch(repo, env, "--limit", "30", "--", *holding_cmd(repo, "1"))
        first.until_prefix("bridge-run: slot taken ")
        second = Launch(second_dir, env, "--limit", "30", "--", *holding_cmd(repo, "2"))
        line = second.until_prefix("bridge-run: waiting", timeout=8)
        assert re.fullmatch(today_waiting_re(first.run_id()), line), line
        third = Launch(other, env, "--limit", "30", "--", *holding_cmd(other))
        t3 = third.until_prefix("bridge-run: slot taken ", timeout=8)
        assert t3.endswith(" (slot 2 of 2)"), t3  # slot 2 was free all along: the same-checkout waiter left it
        assert not (repo / "s2").exists() and not taken_lines(second.lines)
        release(repo, "1")
        first.finish()
        release(other)
        third.finish()
        second.until_prefix("bridge-run: slot taken ")
        release(repo, "2")
        second.finish()
    finally:
        kill_all(first, second, third)
    assert [p.proc.returncode for p in (first, second, third)] == [0, 0, 0], (first.lines, second.lines, third.lines)
    assert float((repo / "s2").read_text()) >= float((repo / "e1").read_text())


def test_hotfix24a_same_checkout_started_together_one_at_a_time(tmp_path, env):
    """Test 3 (second part); "The lock is an OS byte lock, taken atomically, so two launches from one checkout
    started together cannot both pass it": with {"slots": 2}, two launches from one folder started together (both
    before either holds anything): exactly one command runs at a time."""
    write_settings(env, json.dumps({"slots": 2}))
    root = launch_dir(tmp_path, "a")
    p1 = p2 = None
    try:
        p1 = Launch(root, env, "--limit", "30", "--", *holding_cmd(root, "1"))
        p2 = Launch(root, env, "--limit", "30", "--", *holding_cmd(root, "2"))
        assert wait_until(lambda: (root / "s1").exists() or (root / "s2").exists(), timeout=15)
        time.sleep(1.5)
        started = [t for t in ("1", "2") if (root / ("s" + t)).exists()]
        assert len(started) == 1, "both commands run at once: %r" % started
        first, second = started[0], "2" if started[0] == "1" else "1"
        release(root, first)
        assert wait_until(lambda: (root / ("s" + second)).exists(), timeout=15)
        release(root, second)
        p1.finish()
        p2.finish()
    finally:
        kill_all(p1, p2)
    assert p1.proc.returncode == 0 and p2.proc.returncode == 0, (p1.lines, p2.lines)
    assert float((root / ("s" + second)).read_text()) >= float((root / ("e" + first)).read_text())


def test_hotfix24a_same_checkout_holder_record_from_its_slot_taken_time(tmp_path, env):
    """Test 3 (final design); "One heavy run per checkout": the folder lock's holder record is published only when
    its holder takes its slot, with start = the slot-taken time; until then a same-checkout waiter reads no record
    and waits as today's waiter does before a record is published: with both slots held from other folders, a
    launch H from the checkout takes the folder lock and waits for a slot; a waiter W from the same checkout says
    `unknown`; once H takes slot 1, W names H `since` H's slot-taken time, `ends by` that time plus H's limit (30 s)
    and the scaled grace's whole seconds (1.2 -> 1)."""
    write_settings(env, json.dumps({"slots": 2}))
    root = launch_dir(tmp_path, "a")
    h1 = h2 = hl = wl = None
    try:
        h1, rel1 = start_slot_holder(tmp_path, env, "heavy.lock", "2026-09-01T04:00:00Z", 600)
        h2, _ = start_slot_holder(tmp_path, env, "heavy-2.lock", "2026-09-01T05:00:00Z", 600)
        hl = Launch(root, env, "--limit", "30", "--", *holding_cmd(root, "h"))
        hl.until_prefix("bridge-run: waiting", timeout=8)  # H holds the folder lock and waits for a slot
        wl = Launch(root, env, "--limit", "30", "--", *holding_cmd(root, "w"))
        first_wait = wl.until_prefix("bridge-run: waiting", timeout=8)
        assert first_wait == "bridge-run: waiting for the slot held by unknown", first_wait
        rel1.write_text("go", encoding="utf-8")
        h1.wait(timeout=15)
        taken = hl.until_prefix("bridge-run: slot taken ", timeout=10)
        assert taken.endswith(" (slot 1 of 2)"), taken
        t_h = taken.split("slot taken ", 1)[1].split(" ", 1)[0]
        rid_h = hl.run_id()
        line = wl.until(lambda ln: ln.startswith("bridge-run: waiting") and rid_h in ln, "naming H %s" % rid_h)
        m = re.fullmatch(r"bridge-run: waiting for the slot held by test %s since (\S+Z), ends by (\S+Z)"
                         % re.escape(rid_h), line)
        assert m, line
        assert m.group(1) == t_h, (m.group(1), t_h)
        since, ends = (datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ") for x in m.groups())
        assert (ends - since).total_seconds() == 31
        assert not taken_lines(wl.lines)
        release(root, "h")
        hl.finish()
        wl.until_prefix("bridge-run: slot taken ")
        release(root, "w")
        wl.finish()
    finally:
        kill_all(h1, h2, hl, wl)
    assert hl.proc.returncode == 0 and wl.proc.returncode == 0, (hl.lines, wl.lines)


def test_hotfix24a_same_checkout_not_free_names_the_folder_holder(tmp_path, env):
    """Test 3 (third part); "One heavy run per checkout": "its bound is that holder's end (same floor and cap); its
    exit-123 line names that holder" [S9]: slot 1 held from another folder with an end long before the
    same-checkout holder's (slot 2, limit 600), a waiter from that checkout ends with 123 naming the same-checkout
    holder, never the sooner-ending slot 1 holder."""
    write_settings(env, json.dumps({"slots": 2}))
    env["BRIDGE_RUN_SLOT_SCALE"] = "0.001"
    root = launch_dir(tmp_path, "a")
    br = load_br()
    holder = mine = None
    try:
        holder, _ = start_slot_holder(tmp_path, env, "heavy.lock", "2026-09-01T03:00:00Z", 2)
        assert wait_until(lambda: br.read_holder_record(os.path.join(state_dir(env), "heavy.lock.holder")) is not None)
        mine = Launch(root, env, "--limit", "600", "--", *holding_cmd(root))
        t = mine.until_prefix("bridge-run: slot taken ", timeout=8)
        assert t.endswith(" (slot 2 of 2)"), t
        t0 = time.monotonic()
        out = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "open('ran.txt','w')", timeout=40)
        elapsed = time.monotonic() - t0
        release(root)
        mine.finish()
    finally:
        kill_all(holder, mine)
    lines = out.stderr.splitlines()
    assert out.returncode == 123, out.stderr
    assert lines[-1] == "bridge-run: exit 123"
    assert re.fullmatch(r"bridge-run: slot not free - held by test %s since %s, ends by %s"
                        % (re.escape(mine.run_id()), STAMP_RE, STAMP_RE), lines[-2]), lines[-2]
    assert elapsed < 25, elapsed  # the folder holder's end capped at (14,400 + 120) x 0.001 = 14.5 s
    assert not (root / "ran.txt").exists()


# ---------------------------------------------------------------- 4: a malformed setting


MALFORMED = [
    ("not-json", b"not json"),
    ("zero", b'{"slots": 0}'),
    ("five", b'{"slots": 5}'),
    ("true", b'{"slots": true}'),
    ("string", b'{"slots": "2"}'),
    ("float", b'{"slots": 2.0}'),
    ("extra-key", b'{"slots": 2, "x": 1}'),
    ("bom", b'\xef\xbb\xbf{"slots": 2}'),
    ("list", b"[2]"),
    ("empty", b""),
    ("over-4096", b'{"slots": 2}' + b" " * 5000),
    ("folder", None),
]


@pytest.mark.parametrize("raw", [m[1] for m in MALFORMED], ids=[m[0] for m in MALFORMED])
def test_hotfix24a_malformed_setting_is_one_note_and_one_slot(tmp_path, env, raw):
    """Test 4; the setting, "Anything else than the exact form: 1 slot and one note line `bridge-run: note -
    heavy-slots.json ignored (<cause>); one heavy slot`, printed after `bridge-run: started <run id>` ..., never a
    refusal" (a bool, a float, a string, extra keys or a byte-order mark are not the form; at most 4096 bytes; a
    regular file only): each launch prints the note once after its started line, and a second launch waits while
    the first holds the one slot, its lines byte-identical to today's."""
    if raw is None:
        os.makedirs(settings_path(env))
    else:
        write_settings(env, raw)
    a, b = launch_dir(tmp_path, "a"), launch_dir(tmp_path, "b")
    first = second = None
    try:
        first = Launch(a, env, "--limit", "30", "--", *holding_cmd(a))
        first.until_prefix("bridge-run: slot taken ")
        second = Launch(b, env, "--limit", "30", "--", *holding_cmd(b))
        line = second.until_prefix("bridge-run: waiting")
        assert line.startswith("bridge-run: waiting for the slot held by "), line
        release(a)
        err1 = first.finish()
        second.until_prefix("bridge-run: slot taken ")
        release(b)
        err2 = second.finish()
    finally:
        kill_all(first, second)
    for err, proc in ((err1, first.proc), (err2, second.proc)):
        notes = [i for i, ln in enumerate(err) if ln.startswith(NOTE_PREFIX)]
        assert len(notes) == 1, "want one %r line, got: %r" % (NOTE_PREFIX, err)
        assert err[notes[0]].endswith(NOTE_SUFFIX), err[notes[0]]
        assert err[0].startswith("bridge-run: started ") and notes[0] > 0, err
        assert all(re.fullmatch(TAKEN_RE, ln) for ln in taken_lines(err)), err
        assert proc.returncode == 0, err
        assert not any(ln.startswith("bridge-run: refused") for ln in err), err
    assert float((b / "s").read_text()) >= float((a / "e").read_text())


# ---------------------------------------------------------------- 5: --heavy-slots


def test_hotfix24a_heavy_slots_option_writes_the_setting(tmp_path, env):
    """Test 5; the setting, "`bridge-run.py --heavy-slots <n>` (n 1..4) writes the file atomically (a temporary
    file in the same folder, then replace), prints `bridge-run: heavy slots set to <n>`, exit 0, starts no command
    and writes no run row"."""
    root = launch_dir(tmp_path, "a")
    out = run_bridge(root, env, "--heavy-slots", "2")
    text = out.stdout + out.stderr
    assert out.returncode == 0, text
    assert "bridge-run: heavy slots set to 2" in text.splitlines(), text
    with open(settings_path(env), encoding="utf-8") as f:
        assert json.load(f) == {"slots": 2}
    assert sorted(os.listdir(state_dir(env))) == ["heavy-slots.json"]  # no temporary file left, no slot taken
    assert "started" not in out.stderr and "slot taken" not in out.stderr
    assert rows_of(root) == []


@pytest.mark.parametrize("value", ["0", "5", "x"])
def test_hotfix24a_heavy_slots_option_refuses_out_of_range(tmp_path, env, value):
    """Test 5; the setting, "Out of range or not an integer: exit 125 naming the range, the file unchanged"."""
    root = launch_dir(tmp_path, "a")
    write_settings(env, json.dumps({"slots": 3}) + "\n")
    before = open(settings_path(env), "rb").read()
    out = run_bridge(root, env, "--heavy-slots", value)
    assert out.returncode == 125, out.stdout + out.stderr
    assert re.search(r"1\D{1,8}4", out.stderr), out.stderr  # names the range 1 to 4
    assert open(settings_path(env), "rb").read() == before
    assert sorted(os.listdir(state_dir(env))) == ["heavy-slots.json"]
    assert "started" not in out.stderr
    assert rows_of(root) == []


@pytest.mark.parametrize("extra", ["command", "kind"])
def test_hotfix24a_heavy_slots_option_alone_only(tmp_path, env, extra):
    """Test 5; the setting, "Given with a command (`--`) or any other option: exit 125, nothing written [S6]":
    `--heavy-slots 2 -- python -c ...` and `--heavy-slots 2 --kind test` write no setting, start nothing and write
    no row."""
    root = launch_dir(tmp_path, "a")
    marker = root / "ran.txt"
    if extra == "command":
        args = ["--heavy-slots", "2", "--", sys.executable, "-c", "open(%r,'w').write('x')" % str(marker)]
    else:
        args = ["--heavy-slots", "2", "--kind", "test"]
    out = run_bridge(root, env, *args)
    assert out.returncode == 125, out.stdout + out.stderr
    assert not os.path.exists(settings_path(env))
    assert not os.path.isdir(state_dir(env)) or os.listdir(state_dir(env)) == []
    assert not marker.exists()
    assert "started" not in out.stderr
    assert rows_of(root) == []


# ---------------------------------------------------------------- 6 to 9: the row, a lock error, run ids, the bound


def test_hotfix24a_run_row_carries_its_slot(tmp_path, env):
    """Test 6; the run row, "A heavy run's row gains `"slot": <k>`": a lone run with no setting logs slot 1; with
    {"slots": 2}, a run beside a holder of slot 1 logs slot 2 and the holder logs slot 1, each matching the slot
    its slot-taken line names."""
    lone = launch_dir(tmp_path, "lone")
    out = run_bridge(lone, env, "--limit", "30", "--", sys.executable, "-c", "pass")
    assert out.returncode == 0, out.stderr
    rid = out.stderr.splitlines()[0].split("started ", 1)[1]
    assert row_of(lone, rid).get("slot") == 1, row_of(lone, rid)

    write_settings(env, json.dumps({"slots": 2}))
    a, b = launch_dir(tmp_path, "a"), launch_dir(tmp_path, "b")
    first = second = None
    try:
        first = Launch(a, env, "--limit", "30", "--", *holding_cmd(a))
        t1 = first.until_prefix("bridge-run: slot taken ")
        second = Launch(b, env, "--limit", "30", "--", sys.executable, "-c", "pass")
        second.until_prefix("bridge-run: slot taken ", timeout=8)
        err2 = second.finish()
        release(a)
        err1 = first.finish()
    finally:
        kill_all(first, second)
    assert first.proc.returncode == 0 and second.proc.returncode == 0, (err1, err2)
    t2 = taken_lines(err2)
    assert t1.endswith(" (slot 1 of 2)") and t2 and t2[0].endswith(" (slot 2 of 2)"), (t1, t2)
    assert row_of(a, first.run_id()).get("slot") == 1
    assert row_of(b, second.run_id()).get("slot") == 2


def test_hotfix24a_slot_lock_error_refuses(tmp_path, env):
    """Test 7; the slots, "An open or lock error on any slot's lock file refuses the launch with exit 125 and the
    line `bridge-run: refused - ~/.cursor-bridge/<that file> (<error class>)`, as today for slot 1 [S4]":
    "All n lock files are opened before the first pass, so a broken `heavy-2.lock` refuses the launch even while
    slot 1 is free [C8]": heavy-2.lock a folder, slots 2, slot 1 free: exit 125 naming heavy-2.lock, the command
    never started, no pid file left."""
    write_settings(env, json.dumps({"slots": 2}))
    os.makedirs(os.path.join(state_dir(env), "heavy-2.lock"))
    root = launch_dir(tmp_path, "a")
    marker = root / "ran.txt"
    out = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "open('ran.txt','w')")
    assert out.returncode == 125, out.stderr
    assert re.search(r"^bridge-run: refused - ~/\.cursor-bridge/heavy-2\.lock \([^)]+\)$", out.stderr, re.M), out.stderr
    assert "Traceback" not in out.stderr
    assert not marker.exists()
    pids = root / "run" / "launcher" / "pids"
    assert not pids.is_dir() or os.listdir(str(pids)) == []


def test_hotfix24a_folder_lock_error_refuses(tmp_path, env):
    """The slots, "One heavy run per checkout" with "An open or lock error on any slot's lock file refuses the
    launch with exit 125" (final design: a folder lock file error refuses with 125 naming heavy-folder-<h>.lock):
    the folder lock file a first launch made, replaced by a folder, refuses the next launch from that folder."""
    root = launch_dir(tmp_path, "a")
    first = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "pass")
    assert first.returncode == 0, first.stderr
    made = [n for n in os.listdir(state_dir(env)) if re.fullmatch(r"heavy-folder-[0-9a-f]{64}\.lock", n)]
    assert len(made) == 1, "want one heavy-folder-<sha256>.lock, got %r" % sorted(os.listdir(state_dir(env)))
    path = os.path.join(state_dir(env), made[0])
    os.remove(path)
    os.makedirs(path)
    marker = root / "ran.txt"
    out = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "open('ran.txt','w')")
    assert out.returncode == 125, out.stderr
    assert re.search(r"^bridge-run: refused - ~/\.cursor-bridge/%s \([^)]+\)$" % re.escape(made[0]), out.stderr,
                     re.M), out.stderr
    assert "Traceback" not in out.stderr
    assert not marker.exists()


def pid_names(root):
    pids = root / "run" / "launcher" / "pids"
    return set(os.listdir(str(pids))) if pids.is_dir() else set()


def test_hotfix24a_same_second_launches_get_distinct_ids(tmp_path, env):
    """Test 8; Run ids [S8, S10], "The run id keeps today's form: the launch second, with today's `-<n>` suffix
    where taken ... made unique by creating its pid file `run/launcher/pids/<run id>` exclusively at launch ...,
    holding the launcher's own pid twice while it waits ... Every exit before the child starts (each refusal with
    125, an exit 123, a refused slot) removes it": two launches from one folder started in one second (the second
    waiting on the folder lock) get distinct ids in today's form, distinct pid files while both live, and distinct
    rows; a launch refused with 125 at its slots and one ending with 123 leave no pid file."""
    write_settings(env, json.dumps({"slots": 2}))
    root = launch_dir(tmp_path, "a")
    while time.time() % 1 > 0.1:  # start both at the head of a second, so their launch seconds agree
        time.sleep(0.01)
    p1 = p2 = None
    try:
        p1 = Launch(root, env, "--limit", "30", "--", *holding_cmd(root, "1"))
        p2 = Launch(root, env, "--limit", "30", "--", *holding_cmd(root, "2"))
        p1.until_prefix("bridge-run: started ")
        p2.until_prefix("bridge-run: started ")
        ids = (p1.run_id(), p2.run_id())
        assert ids[0] != ids[1], ids
        for rid in ids:
            assert re.fullmatch(STAMP_RE + r"(-[2-9]|-[1-9]\d+)?", rid), rid
        if ids[0][:20] == ids[1][:20]:  # one launch second: the later id carries today's suffix
            assert sorted(ids)[1] == sorted(ids)[0] + "-2", ids
        names = {i.replace(":", "-") for i in ids}
        assert wait_until(lambda: (root / "s1").exists() or (root / "s2").exists(), timeout=10)
        assert wait_until(lambda: names <= pid_names(root)), (names, pid_names(root))  # one runs, one waits
        release(root, "1")
        release(root, "2")
        p1.finish()
        p2.finish()
    finally:
        kill_all(p1, p2)
    assert p1.proc.returncode == 0 and p2.proc.returncode == 0, (p1.lines, p2.lines)
    assert sorted(r.get("id") for r in rows_of(root)) == sorted(ids)

    write_settings(env, json.dumps({"slots": 3}))  # a refused slot: heavy-3.lock a folder
    os.makedirs(os.path.join(state_dir(env), "heavy-3.lock"))
    refused = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "pass")
    assert refused.returncode == 125, refused.stderr
    rid = refused.stderr.splitlines()[0].split("started ", 1)[1]
    assert rid.replace(":", "-") not in pid_names(root), pid_names(root)

    write_settings(env, json.dumps({"slots": 2}))  # an exit 123: both slots held from elsewhere
    env["BRIDGE_RUN_SLOT_SCALE"] = "0.001"
    h1 = h2 = None
    try:
        h1, _ = start_slot_holder(tmp_path, env, "heavy.lock", "2026-09-01T06:00:00Z", 2)
        h2, _ = start_slot_holder(tmp_path, env, "heavy-2.lock", "2026-09-01T07:00:00Z", 2)
        ended = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "pass", timeout=40)
    finally:
        kill_all(h1, h2)
    assert ended.returncode == 123, ended.stderr
    rid = ended.stderr.splitlines()[0].split("started ", 1)[1]
    assert rid.replace(":", "-") not in pid_names(root), pid_names(root)


def wait_until(pred, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.05)
    return pred()


def test_hotfix24a_not_free_names_the_earliest_end(tmp_path, env):
    """Test 9; Waiting, "The wait's bound is fixed once ... as the earliest of their ends ... At the bound:
    `bridge-run: slot not free - held by <the live holder with the earliest end> ...` in today's format, then exit
    123 [S3]": slot 1 held with a limit of 600 s, slot 2 with a limit of 2 s; a waiter ends near the second's end
    (its own floor is 1,800 x 0.001 = 1.8 s), naming it."""
    write_settings(env, json.dumps({"slots": 2}))
    env["BRIDGE_RUN_SLOT_SCALE"] = "0.001"
    root = launch_dir(tmp_path, "a")
    marker = root / "ran.txt"
    br = load_br()
    folder = state_dir(env)
    h1 = h2 = None
    try:
        h1, _ = start_slot_holder(tmp_path, env, "heavy.lock", "2026-09-01T01:00:00Z", 600)
        h2, _ = start_slot_holder(tmp_path, env, "heavy-2.lock", "2026-09-01T02:00:00Z", 2)
        for name in ("heavy.lock.holder", "heavy-2.lock.holder"):  # precondition: both records read live
            assert wait_until(lambda: br.read_holder_record(os.path.join(folder, name)) is not None), name
        t0 = time.monotonic()
        out = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "open('ran.txt','w')", timeout=40)
        elapsed = time.monotonic() - t0
    finally:
        kill_all(h1, h2)
    lines = out.stderr.splitlines()
    assert out.returncode == 123, out.stderr
    assert lines[-1] == "bridge-run: exit 123"
    assert re.fullmatch(r"bridge-run: slot not free - held by test 2026-09-01T02:00:00Z since %s, ends by %s"
                        % (STAMP_RE, STAMP_RE), lines[-2]), lines[-2]
    assert elapsed < 9, elapsed  # the earliest end, not the provisional bound (14,520 x 0.001 = 14.5 s)
    assert not marker.exists()


# ---------------------------------------------------------------- 10: the mutation engine


LOCK_HELPER_SRC = r'''
import os, sys, time
path, ready, release = sys.argv[1:4]
fd = os.open(path, os.O_RDWR | os.O_CREAT)
if sys.platform == "win32":
    import msvcrt
    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
else:
    import fcntl
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:  # hold the record lock as well, so either POSIX primitive meets it
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        pass
open(ready, "w").close()
end = time.monotonic() + 180
while time.monotonic() < end and not os.path.exists(release):
    time.sleep(0.05)
'''

CALC = {
    "demo/__init__.py": "",
    "demo/calc.py": "def add(a, b):\n    return a + b\n",
    "tests/test_calc.py": "from demo.calc import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
}


def _git(ws, *args):
    p = subprocess.run(GIT + list(args), cwd=str(ws), stdin=subprocess.DEVNULL, capture_output=True, text=True,
                       timeout=60, **SESSION)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def _mutants_file(ws, run_id):
    mf = ws / "run" / "supervisor" / ("%s-mutants.json" % run_id)
    mf.write_text(json.dumps({"mutants": [{
        "id": "m", "file": "demo/calc.py", "pairs": [{"old": "return a + b", "new": "return a - b"}],
        "tests": ["tests/test_calc.py"], "expect_fail": ["tests/test_calc.py::test_add"]}]}), encoding="utf-8")
    return mf


def _mutation_fixture(tmp_path):
    ws = tmp_path / "proj" / "Workspace"
    (ws / "run" / "supervisor").mkdir(parents=True)
    for rel, text in CALC.items():
        path = ws / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    _git(ws, "init", "-q", "-b", "main")
    _git(ws, "add", "-A")
    _git(ws, "commit", "-q", "-m", "init")
    return ws


def _run_mutation(ws, mf, scratch, env):
    return subprocess.run([sys.executable, MUTATION_PROG, str(mf), "--scratch", str(scratch)], cwd=str(ws), env=env,
                          stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180, **SESSION)


def _snapshot(folder):
    seen = {}
    for dirpath, dirnames, filenames in os.walk(str(folder)):
        for name in dirnames + filenames:
            p = os.path.join(dirpath, name)
            st = os.lstat(p)
            seen[os.path.relpath(p, str(folder))] = (st.st_size, st.st_mtime_ns)
    return seen


def test_hotfix24a_mutation_run_refuses_its_run_id_in_use(tmp_path, env):
    """Test 10; the mutation engine [S7], "`mutation-run.py` takes an exclusive byte lock on `<scratch
    base>/.mutation-run-<run_id>.lock` ... before it removes or writes anything; a second run of the same run id
    ends at once with exit 2 and `mutation-run: refused - this mutants file is already running (<run id>); wait for
    it to end`, writing nothing. Runs of different ids share the base folder freely. The lock is released at exit":
    while another process holds the run id's lock the run is refused and neither the base folder nor the cache is
    touched; a run of another run id with the same base gets past the check; after the holder ends, the first run
    gets past it too."""
    ws = _mutation_fixture(tmp_path)
    mf = _mutants_file(ws, "lockt")
    other = _mutants_file(ws, "othert")
    cache = ws / "run" / "supervisor" / "mutation-cache" / "lockt.jsonl"
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    lock = scratch / ".mutation-run-lockt.lock"
    helper_src = tmp_path / "lock_helper.py"
    helper_src.write_text(LOCK_HELPER_SRC, encoding="utf-8")
    ready, rel = tmp_path / "helper-ready", tmp_path / "helper-release"
    helper = subprocess.Popen([sys.executable, str(helper_src), str(lock), str(ready), str(rel)],
                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              **SESSION)
    try:
        end = time.monotonic() + 15
        while not ready.exists() and helper.poll() is None and time.monotonic() < end:
            time.sleep(0.05)
        assert ready.exists(), "the lock helper never held the lock (exit %r)" % helper.poll()
        before = _snapshot(scratch)
        assert not cache.exists()
        t0 = time.monotonic()
        refused = _run_mutation(ws, mf, scratch, env)
        elapsed = time.monotonic() - t0
        after = _snapshot(scratch)
        text = refused.stdout + refused.stderr
        assert refused.returncode == 2, "want exit 2, got %s: %s" % (refused.returncode, text[-2000:])
        assert ("mutation-run: refused - this mutants file is already running (lockt); wait for it to end"
                in text.splitlines()), text[-2000:]
        assert after == before, "the refused run wrote in the scratch base: %r -> %r" % (before, after)
        assert not cache.exists()
        assert elapsed < 30  # at once, never waiting for the holder
        side = _run_mutation(ws, other, scratch, env)
        assert "already running" not in side.stdout + side.stderr, (side.stdout + side.stderr)[-2000:]
    finally:
        rel.write_text("go", encoding="utf-8")
        try:
            helper.wait(timeout=15)
        except subprocess.TimeoutExpired:
            kill_tree(helper)
    again = _run_mutation(ws, mf, scratch, env)
    assert "already running" not in again.stdout + again.stderr, (again.stdout + again.stderr)[-2000:]


# ---------------------------------------------------------------- round 2: round 1's review


def _repo(folder):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "f.txt").write_text("x\n", encoding="utf-8")
    _git(folder, "init", "-q", "-b", "main")
    _git(folder, "add", "-A")
    _git(folder, "commit", "-q", "-m", "init")
    return folder


def test_hotfix24a_r2_identity_follows_the_builders_workspace(tmp_path, monkeypatch):
    """Round 2, Review A B1 and the security audit's Blocking finding; the slots, "One heavy run per checkout":
    "`<h>` the SHA-256 (hex) of its checkout's identity: the folder the run works in (`workspace_of(argv, launch
    folder)`: a builder's `--workspace`, else the launch folder), raised to `git rev-parse --show-toplevel` of that
    folder": a builder launched from checkout A with `--workspace` into checkout B (its subfolder, or `--workspace=`)
    hashes as B, never as A."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    a = _repo(tmp_path / "a")
    b = _repo(tmp_path / "b")
    (b / "sub").mkdir()
    br = load_br()
    h_a = br.checkout_identity_hash(str(a), ["python", "-c", "pass"])
    h_b = br.checkout_identity_hash(str(b), ["python", "-c", "pass"])
    assert h_a != h_b
    assert br.checkout_identity_hash(str(a), ["cursor-agent", "-p", "--workspace", str(b / "sub"), "x"]) == h_b
    assert br.checkout_identity_hash(str(a), ["cursor-agent", "--workspace=" + str(b), "-p", "x"]) == h_b
    assert br.checkout_identity_hash(str(b / "sub"), ["python"]) == h_b


class _Stop(Exception):
    pass


def test_hotfix24a_r2_the_identity_reads_the_command_never_the_launchers_options(tmp_path, monkeypatch, env):
    """Round 2, Review A B1: `checkout_identity_hash(folder, argv)` is given the command as written after `--`,
    before the launcher resolves it, never the launcher's own options (`--limit` first made `workspace_of` blind to
    a builder's `--workspace`)."""
    for name in ("HOME", "USERPROFILE", "APPDATA", "BRIDGE_RUN_ALLOW_ANY"):
        monkeypatch.setenv(name, env[name])
    monkeypatch.delenv("BRIDGE_RUN_SLOT_SCALE", raising=False)
    root = launch_dir(tmp_path, "a")
    monkeypatch.chdir(str(root))
    br = load_br()
    seen = []

    def fake(folder, argv):
        seen.append(list(argv))
        raise _Stop()

    monkeypatch.setattr(br, "checkout_identity_hash", fake)
    monkeypatch.setattr(sys, "argv", [PROG, "--limit", "30", "--kind", "test", "--", "python", "-c", "pass"])
    with pytest.raises(_Stop):
        br.main()
    assert seen == [["python", "-c", "pass"]], seen


@pytest.mark.parametrize("case", ["cap", "watch-only", "key-file"])
def test_hotfix24a_r2_an_early_refusal_leaves_no_pid_file(tmp_path, env, case):
    """Round 2, Review A B2 and the security audit's Should fix 1; Run ids, "Every exit before the child starts
    (each refusal with 125, an exit 123, a refused slot) removes it, so a refused launch leaves no pid file": the
    refusals of a limit above the cap, a watch launch of another command, and an unreadable key file."""
    root = launch_dir(tmp_path, "a")
    marker = root / "ran.txt"
    cmd = [sys.executable, "-c", "open('ran.txt','w')"]
    if case == "cap":
        args = ["--limit", "99999", "--kind", "test", "--"] + cmd
    elif case == "watch-only":
        args = ["--limit", "30", "--kind", "watch", "--"] + cmd
    else:
        args = ["--limit", "30", "--key-file", str(tmp_path / "missing.env"), "--kind", "test", "--"] + cmd
    out = run_bridge(root, env, *args)
    assert out.returncode == 125, out.stderr
    assert "Traceback" not in out.stderr
    assert not marker.exists()
    assert pid_names(root) == set(), pid_names(root)


def test_hotfix24a_r2_heavy_slots_after_the_separator_belongs_to_the_command(tmp_path, env):
    """Round 2, Review A B3 and the security audit's Should fix 3; the setting, "`--heavy-slots <n>` ... Given with a
    command (`--`) or any other option: exit 125" reads the launcher's own words only: a `--heavy-slots` after `--`
    is the command's argument, so the launch runs and the setting is not written."""
    root = launch_dir(tmp_path, "a")
    out = run_bridge(root, env, "--limit", "30", "--kind", "test", "--", sys.executable, "-c",
                     "open('ran.txt','w')", "--heavy-slots", "2")
    assert out.returncode == 0, out.stderr
    assert (root / "ran.txt").exists()
    assert not os.path.exists(settings_path(env))


@pytest.mark.parametrize("which", ["heavy.lock", "heavy-2.lock", "folder"])
def test_hotfix24a_r2_a_linked_lock_file_is_refused(tmp_path, env, which):
    """Round 2, the security audit's Should fix 2 (the brief: every file under ~/.cursor-bridge is opened with no
    link followed): a lock file that is a hard link to another file (no privilege needed, on Windows too) refuses
    the launch with 125 naming it; the command never starts and the linked file is unchanged."""
    write_settings(env, json.dumps({"slots": 2}))
    root = launch_dir(tmp_path, "a")
    if which == "folder":
        first = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "pass")
        assert first.returncode == 0, first.stderr
        made = [n for n in os.listdir(state_dir(env)) if re.fullmatch(r"heavy-folder-[0-9a-f]{64}\.lock", n)]
        assert len(made) == 1, sorted(os.listdir(state_dir(env)))
        name = made[0]
    else:
        name = which
    path = os.path.join(state_dir(env), name)
    if os.path.exists(path):
        os.remove(path)
    victim = tmp_path / "victim.txt"
    victim.write_bytes(b"keep me")
    os.link(str(victim), path)
    marker = root / "ran.txt"
    out = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "open('ran.txt','w')")
    assert out.returncode == 125, out.stderr
    assert re.search(r"^bridge-run: refused - ~/\.cursor-bridge/%s \([^)]+\)$" % re.escape(name), out.stderr,
                     re.M), out.stderr
    assert "Traceback" not in out.stderr
    assert not marker.exists()
    assert victim.read_bytes() == b"keep me"


def test_hotfix24a_r2_a_linked_mutation_lock_is_refused(tmp_path, env):
    """Round 2, the security audit (mutation-run.py's lock, the link check before the open): a run lock that is a hard
    link to another file ends the run with exit 2 and a `mutation-run: refused - ` line, the linked file unchanged
    and nothing written in the scratch base or the cache."""
    ws = _mutation_fixture(tmp_path)
    mf = _mutants_file(ws, "linkt")
    cache = ws / "run" / "supervisor" / "mutation-cache" / "linkt.jsonl"
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    victim = tmp_path / "victim.txt"
    victim.write_bytes(b"keep me")
    os.link(str(victim), str(scratch / ".mutation-run-linkt.lock"))
    before = _snapshot(scratch)
    out = _run_mutation(ws, mf, scratch, env)
    text = out.stdout + out.stderr
    assert out.returncode == 2, text[-2000:]
    assert any(ln.startswith("mutation-run: refused - ") for ln in text.splitlines()), text[-2000:]
    assert _snapshot(scratch) == before
    assert not cache.exists()
    assert victim.read_bytes() == b"keep me"


def test_hotfix24a_r2_a_failed_setting_write_leaves_no_temporary_file(tmp_path, env):
    """Round 2, Review A C1 and the security audit; the setting, "`--heavy-slots <n>` writes the file atomically (a
    temporary file in the same folder, then replace)", with no temporary file left: a folder at heavy-slots.json
    makes the replace fail; the launch exits 125 and the state folder holds nothing new."""
    os.makedirs(settings_path(env))
    root = launch_dir(tmp_path, "a")
    out = run_bridge(root, env, "--heavy-slots", "2")
    assert out.returncode == 125, out.stderr
    assert "Traceback" not in out.stderr
    assert sorted(os.listdir(state_dir(env))) == ["heavy-slots.json"]
    assert os.path.isdir(settings_path(env))


# ---------------------------------------------------------------- round 3: round 2's review


def test_hotfix24a_r3_a_refused_mutation_run_leaves_the_live_runs_scratch(tmp_path, env):
    """Round 3, the supervisor's inspection of round 2 (requirement 31 moved the refusals inside the try whose finally
    removes the run's scratch folder); test 10, the mutation engine [S7], "a second run of the same run id ends at once
    with exit 2 ... writing nothing": while another process holds the run id's lock and its scratch folder
    `mutation-run-<run id>` holds that run's work, the refused run leaves the folder and its files as they are."""
    ws = _mutation_fixture(tmp_path)
    mf = _mutants_file(ws, "livet")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    live = scratch / "mutation-run-livet" / "tree"
    live.mkdir(parents=True)
    (live / "work.txt").write_text("the live run's work", encoding="utf-8")
    lock = scratch / ".mutation-run-livet.lock"
    helper_src = tmp_path / "lock_helper.py"
    helper_src.write_text(LOCK_HELPER_SRC, encoding="utf-8")
    ready, rel = tmp_path / "helper-ready", tmp_path / "helper-release"
    helper = subprocess.Popen([sys.executable, str(helper_src), str(lock), str(ready), str(rel)],
                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              **SESSION)
    try:
        end = time.monotonic() + 15
        while not ready.exists() and helper.poll() is None and time.monotonic() < end:
            time.sleep(0.05)
        assert ready.exists(), "the lock helper never held the lock (exit %r)" % helper.poll()
        before = _snapshot(scratch)
        refused = _run_mutation(ws, mf, scratch, env)
        text = refused.stdout + refused.stderr
        assert refused.returncode == 2, "want exit 2, got %s: %s" % (refused.returncode, text[-2000:])
        assert ("mutation-run: refused - this mutants file is already running (livet); wait for it to end"
                in text.splitlines()), text[-2000:]
        assert (live / "work.txt").read_text(encoding="utf-8") == "the live run's work"
        assert _snapshot(scratch) == before, "the refused run changed the scratch base"
    finally:
        rel.write_text("go", encoding="utf-8")
        try:
            helper.wait(timeout=15)
        except subprocess.TimeoutExpired:
            kill_tree(helper)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_hotfix24a_r3_a_linked_lock_files_mode_is_left_as_it_was(tmp_path, env):
    """Round 3, the security audit of round 2 (requirement 29: the regular-file and one-link check comes before any
    change to the opened file): a heavy.lock hard-linked to an executable file is refused and the file keeps its
    mode, never chmodded to 0600 first."""
    write_settings(env, json.dumps({"slots": 2}))
    root = launch_dir(tmp_path, "a")
    path = os.path.join(state_dir(env), "heavy.lock")
    os.makedirs(state_dir(env), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    victim = tmp_path / "victim.sh"
    victim.write_bytes(b"#!/bin/sh\n")
    os.chmod(str(victim), 0o755)
    os.link(str(victim), path)
    out = run_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "open('ran.txt','w')")
    assert out.returncode == 125, out.stderr
    assert not (root / "ran.txt").exists()
    assert stat.S_IMODE(os.stat(str(victim)).st_mode) == 0o755


# ---------------------------------------------------------------- round 4: Review B round 1


def test_hotfix24a_r4_an_unusable_pids_folder_refuses_the_launch(tmp_path, env):
    """Round 4, Review B round 1 (behaviour): with a file where `run/launcher/pids` should be, the pid file cannot be
    reserved under any run id; the launch is refused at once with 125 and `bridge-run: refused - cannot reserve
    run/launcher/pids/<run id> (<error class>)`, before its started line, the command never run (round 3's code
    tried the next suffix forever)."""
    root = launch_dir(tmp_path, "a")
    (root / "run" / "launcher").mkdir()
    (root / "run" / "launcher" / "pids").write_text("not a folder", encoding="utf-8")
    out = run_bridge(root, env, "--limit", "30", "--kind", "test", "--", sys.executable, "-c", "open('ran.txt','w')",
                     timeout=60)
    assert out.returncode == 125, out.stderr[-2000:]
    assert re.search(r"^bridge-run: refused - cannot reserve run/launcher/pids/\S+ \([A-Za-z]+\)$", out.stderr,
                     re.M), out.stderr[-2000:]
    assert "bridge-run: started" not in out.stderr
    assert "Traceback" not in out.stderr
    assert not (root / "ran.txt").exists()
    assert (root / "run" / "launcher" / "pids").read_text(encoding="utf-8") == "not a folder"


def test_hotfix24a_r4_a_pid_file_that_cannot_be_made_is_never_a_reservation(tmp_path):
    """Round 4, Review B round 1 (safety mechanism): `create_pid_file_exclusive(folder, run_id)` answers None only
    where the folder has no `run/`, False only when the exclusive open finds the name taken, and raises OSError for
    every other failure, so the launch never keeps a run id it did not reserve: a file at `run/launcher/pids` raises;
    a folder at the pid file's own name is taken (False) or raises, never None."""
    br = load_br()
    rid = "2026-01-01T00:00:00Z"
    bare = tmp_path / "bare"
    bare.mkdir()
    assert br.create_pid_file_exclusive(str(bare), rid) is None
    a = launch_dir(tmp_path, "a")
    (a / "run" / "launcher").mkdir()
    (a / "run" / "launcher" / "pids").write_text("not a folder", encoding="utf-8")
    with pytest.raises(OSError):
        br.create_pid_file_exclusive(str(a), rid)
    b = launch_dir(tmp_path, "b")
    pids = b / "run" / "launcher" / "pids"
    pids.mkdir(parents=True)
    (pids / rid.replace(":", "-")).mkdir()
    try:
        got = br.create_pid_file_exclusive(str(b), rid)
    except OSError:
        got = "raised"
    assert got is False or got == "raised", got
    c = launch_dir(tmp_path, "c")
    made = br.create_pid_file_exclusive(str(c), rid)
    assert made and os.path.isfile(made)
    assert br.create_pid_file_exclusive(str(c), rid) is False
