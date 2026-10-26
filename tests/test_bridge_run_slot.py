"""R-040: one heavy job at a time — the launcher's machine-wide slot on ~/.cursor-bridge/heavy.lock.

The tests of round 3 are the supervisor's (handoff/TASK-029-r3.md, Context): each names the paragraph it
enforces; a requirement is handoff/TASK-029-r2.md's unless the r3 brief is named."""
import importlib.util
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
BRIDGE_DIR = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")
SESSION = {"start_new_session": True} if sys.platform != "win32" else {}
STAMP = "%Y-%m-%dT%H:%M:%SZ"


def load_br():
    spec = importlib.util.spec_from_file_location("bridge_run", PROG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def env_for(**extra):
    env = dict(os.environ)
    env["BRIDGE_RUN_ALLOW_ANY"] = "1"
    env.update(extra)
    return env


def env_without_allow_any(**extra):
    env = dict(os.environ)
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    env.update(extra)
    return env


def launch_dir(tmp_path, name="a"):
    root = tmp_path / name
    (root / "run").mkdir(parents=True)
    return root


def lock_path_of(env):
    return os.path.join(str(env["HOME"]), ".cursor-bridge", "heavy.lock")


def run_bridge(cwd, env, *args, timeout=30):
    return subprocess.run(
        [sys.executable, PROG, *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def popen_bridge(cwd, env, *args):
    return subprocess.Popen(
        [sys.executable, PROG, *args],
        cwd=str(cwd),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        **SESSION,
    )


def read_until(proc, prefix, timeout=15):
    """proc's stderr lines up to and including the first starting with prefix; a thread reads them,
    so a process that stays silent fails the test at the timeout instead of hanging it."""
    q = queue.Queue()

    def pump():
        for ln in iter(proc.stderr.readline, ""):
            q.put(ln.rstrip("\n"))
            if ln.startswith(prefix):
                return
        q.put(None)

    threading.Thread(target=pump, daemon=True).start()
    lines, end = [], time.monotonic() + timeout
    while True:
        left = end - time.monotonic()
        assert left > 0, "no line starting %r in %r" % (prefix, lines)
        try:
            ln = q.get(timeout=left)
        except queue.Empty:
            continue
        assert ln is not None, "stderr ended without a line starting %r: %r" % (prefix, lines)
        lines.append(ln)
        if ln.startswith(prefix):
            return lines


HOLDER_SRC = r'''
import json, os, sys, time
sys.path.insert(0, sys.argv[1])
import importlib.util
spec = importlib.util.spec_from_file_location("bridge_run", os.path.join(sys.argv[1], "bridge-run.py"))
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)
delay = float(sys.argv[2])
hold = float(sys.argv[3])
kind = sys.argv[4]
run_id = sys.argv[5]
limit = int(sys.argv[6])
plant = sys.argv[7]
lock_path, holder_path = br.heavy_state_paths()
os.makedirs(os.path.dirname(lock_path), exist_ok=True)
fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
if not br._try_lock_byte(fd):
    sys.exit(2)
if plant:
    me = os.getpid()
    if plant.startswith("hex:"):
        data = bytes.fromhex(plant[4:])
    elif plant.startswith("deep:"):
        data = ("[" * int(plant[5:])).encode("ascii")
    else:
        data = (plant.replace("__PID32__", str(2 ** 32 + me)).replace("__PID__", str(me))
                .replace("__CREATED__", repr(br.process_creation_epoch(me))).encode("utf-8"))
    with open(holder_path, "wb") as f:
        f.write(data)
time.sleep(delay)
taken = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
if not plant:
    br.publish_holder_record(holder_path, {
        "kind": kind, "run_id": run_id, "pid": os.getpid(),
        "created": br.process_creation_epoch(os.getpid()) or time.time(),
        "start": taken, "limit": limit,
    })
time.sleep(hold)
'''

LOCK_ONLY_SRC = r'''
import os, sys, time
sys.path.insert(0, sys.argv[1])
import importlib.util
spec = importlib.util.spec_from_file_location("bridge_run", os.path.join(sys.argv[1], "bridge-run.py"))
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)
hold = float(sys.argv[2])
lock_path, _ = br.heavy_state_paths()
os.makedirs(os.path.dirname(lock_path), exist_ok=True)
fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
if not br._try_lock_byte(fd):
    sys.exit(2)
time.sleep(hold)
'''


def start_holder(tmp_path, env, delay=0, hold=5, kind="test", run_id="2020-01-01T00:00:00Z", limit=30, plant=""):
    script = tmp_path / "holder.py"
    script.write_text(HOLDER_SRC, encoding="utf-8")
    return subprocess.Popen(
        [sys.executable, str(script), BRIDGE_DIR, str(delay), str(hold), kind, run_id, str(limit), plant],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **SESSION,
    )


def start_lock_only(tmp_path, env, hold=30):
    script = tmp_path / "lockonly.py"
    script.write_text(LOCK_ONLY_SRC, encoding="utf-8")
    return subprocess.Popen(
        [sys.executable, str(script), BRIDGE_DIR, str(hold)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **SESSION,
    )


def kill_tree(proc):
    if proc is None or proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
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


def good_record(pid, created, **overrides):
    base = {
        "kind": "test",
        "run_id": "2026-05-01T12:00:00Z",
        "start": "2026-05-01T12:00:00Z",
        "pid": pid,
        "created": created,
        "limit": 60,
    }
    base.update(overrides)
    return base


def wait_until(pred, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.05)
    return pred()


def test_r040_no_tasklist_in_launcher():
    """R-040 (Requirement 4): slot liveness never shells out to tasklist."""
    text = open(PROG, encoding="utf-8").read()
    assert "tasklist" not in text


def test_r040_wait_uses_monotonic_clock(tmp_path, monkeypatch):
    """R-040 (Requirement 3): the slot wait deadline follows time.monotonic(), not a jumping wall clock."""
    br = load_br()
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    holder = start_lock_only(tmp_path, env, hold=25)
    try:
        time.sleep(0.2)
        real_mono = time.monotonic
        bump = [0]

        def fake_mono():
            return real_mono() + bump[0]

        base_wall = time.time()
        monkeypatch.setattr(time, "monotonic", fake_mono)
        monkeypatch.setattr(time, "time", lambda: base_wall + 100000)
        done = []

        def run():
            done.append(br.acquire_heavy_slot("test", "2026-01-01T00:00:00Z", 5, 0.001))

        t = threading.Thread(target=run)
        t.start()
        time.sleep(0.3)
        bump[0] = 100000
        t.join(timeout=5)
    finally:
        kill_tree(holder)
    assert done and done[0] is None


def test_r040_provisional_bound_without_record(tmp_path):
    """R-040 (Requirement 2; 17's ten seconds): no live record ends at the scaled provisional bound,
    (14,400 + 120) x 0.0003 = 4.4 s, with only unknown waiting lines, the command never started."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.0003")
    root = launch_dir(tmp_path)
    marker = root / "never.txt"
    holder = None
    try:
        holder = start_lock_only(tmp_path, env, hold=25)
        time.sleep(0.15)
        t0 = time.monotonic()
        out = run_bridge(
            root, env, "--limit", "5", "--",
            sys.executable, "-c", "open(r'%s','w').write('x')" % str(marker).replace("\\", "\\\\"),
            timeout=15,
        )
        elapsed = time.monotonic() - t0
    finally:
        kill_tree(holder)
    assert out.returncode == 123
    assert 3.5 <= elapsed <= 8
    lines = [ln for ln in out.stderr.splitlines() if ln.startswith("bridge-run: waiting")]
    assert lines and all(ln == "bridge-run: waiting for the slot held by unknown" for ln in lines)
    assert out.stderr.splitlines()[-2:] == [
        "bridge-run: slot not free - held by unknown",
        "bridge-run: exit 123",
    ]
    assert not marker.exists()


def test_r040_untrusted_records_in_process(tmp_path):
    """R-040 (Requirements 4 and 5; handoff/TASK-029-r3.md, the record's read): crafted holder records,
    each naming the live helper so that only its own field can refuse it, read as no record without an
    exception; the well-formed twin reads live; after the kill it reads as no record."""
    br = load_br()
    env = env_for()
    holder = None
    try:
        holder = start_holder(tmp_path, env, delay=0, hold=12)
        time.sleep(0.3)
        pid = holder.pid
        created = br.process_creation_epoch(pid)
        assert created is not None
        _, holder_path = br.heavy_state_paths(env)
        live = good_record(pid, created)
        with open(holder_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(live))
        assert br.read_holder_record(holder_path) is not None  # precondition: the twin reads live
        arabic = "2026-05-01T12:00:00Z".translate({ord(d): 0x0660 + int(d) for d in "0123456789"})
        too_big_pid = 2 ** 32 + pid if sys.platform == "win32" else br.PID_MAX + 1
        cases = [
            "not json",
            "[]",
            "[" * 100000,
            json.dumps(good_record(pid, created, kind=["x"])),
            json.dumps(good_record(pid, created, kind="nope")),
            json.dumps(good_record(pid, created, kind="test\u0007")),
            json.dumps(good_record(pid, created, run_id="2026\x0701T00:00:00Z")),
            json.dumps(good_record(pid, created, run_id="2026٠01T00:00:00Z")),
            json.dumps(good_record(pid, created, run_id=arabic)),
            json.dumps(good_record(pid, created, run_id="2026-05-01T12:00:00Z\n")),
            json.dumps({**live, "pid": str(pid)}),
            json.dumps({**live, "pid": True}),
            json.dumps({**live, "pid": 0}),
            json.dumps({**live, "pid": -1}),
            json.dumps({**live, "pid": 2 ** 64 + 5}),
            json.dumps({**live, "pid": too_big_pid}),
            json.dumps({**live, "created": "1"}),
            json.dumps({**live, "created": True}),
            json.dumps({**live, "created": float("nan")}),
            json.dumps({**live, "created": float("inf")}),
            json.dumps({**live, "created": int("9" * 400)}),
            json.dumps({**live, "created": created + 1.0}),  # alive, its creation time one second off
            json.dumps({**live, "limit": "9"}),
            json.dumps({**live, "limit": 9.9}),
            json.dumps({**live, "limit": True}),
            json.dumps({**live, "limit": 0}),
            json.dumps({**live, "limit": 604801}),
            json.dumps({**live, "limit": float("inf")}),
            json.dumps({**live, "limit": int("9" * 400)}),
            json.dumps(live).replace('"limit": 60', '"limit": 1e400'),
            json.dumps(live) + " " * 8192,  # a record past the read's size cap (handoff/TASK-029-r3.md)
            json.dumps(good_record(pid, created, start="0001-01-01T00:00:00Z")),
            json.dumps(good_record(pid, created, start="1999-12-31T23:59:59Z")),
            json.dumps(good_record(pid, created, start="9999-12-31T23:59:59Z")),
            json.dumps(good_record(pid, created, start=(datetime.now(timezone.utc) + timedelta(days=2)).strftime(STAMP))),
            json.dumps(good_record(pid, created, start="2026-02-30T00:00:00Z")),
            json.dumps(good_record(pid, created, start="2026-05-01T12:00:00Z-2")),
            json.dumps(good_record(pid, created, start="2026٠05-01T12:00:00Z")),
        ]
        for raw in cases:
            with open(holder_path, "w", encoding="utf-8") as f:
                f.write(raw)
            assert br.read_holder_record(holder_path) is None, raw[:120]
        for raw in (b"\xff\xfe{\x00}\x00", json.dumps(live).encode("utf-16"), b"\x80" * 10):
            with open(holder_path, "wb") as f:
                f.write(raw)
            assert br.read_holder_record(holder_path) is None, raw[:40]
        with open(holder_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(live))
        assert br.read_holder_record(holder_path) is not None
        kill_tree(holder)
        time.sleep(0.3)
        assert br.read_holder_record(holder_path) is None
    finally:
        kill_tree(holder)


def test_r040_exit_code_259_reads_as_dead(tmp_path):
    """R-040 (Requirement 4; handoff/TASK-029-r3.md, liveness): a process that exited with code 259
    (STILL_ACTIVE's value) is not alive: its record, live while it ran, reads as no record."""
    br = load_br()
    p = subprocess.Popen([sys.executable, "-c", "import sys, time; time.sleep(1.5); sys.exit(259)"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **SESSION)
    try:
        time.sleep(0.3)
        created = br.process_creation_epoch(p.pid)
        assert created is not None
        rec = tmp_path / "heavy.lock.holder"
        rec.write_text(json.dumps(good_record(p.pid, created)), encoding="utf-8")
        assert br.read_holder_record(str(rec)) is not None  # precondition: alive, it reads live
        p.wait(timeout=10)
        assert p.returncode == (259 if sys.platform == "win32" else 3)
        assert br.read_holder_record(str(rec)) is None
    finally:
        kill_tree(p)


READ_CHILD_SRC = (
    "import importlib.util, os, sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "spec = importlib.util.spec_from_file_location('bridge_run', os.path.join(sys.argv[1], 'bridge-run.py'))\n"
    "br = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(br)\n"
    "print(br.read_holder_record(sys.argv[2]))\n"
)


def read_in_child(path, timeout=5):
    """read_holder_record(path) in a child the timeout kills, so a read that blocks or never ends
    fails the test without holding the suite (None when the child had to be killed)."""
    try:
        return subprocess.run([sys.executable, "-c", READ_CHILD_SRC, BRIDGE_DIR, path],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX special files")
def test_r040_special_file_records_posix(tmp_path):
    """R-040 (Requirement 5; handoff/TASK-029-r3.md, the record's read): a FIFO at the record's path is
    not waited on, and a link to /dev/zero is not read without end: both read as no record at once."""
    fifo = str(tmp_path / "fifo.holder")
    os.mkfifo(fifo)
    zero = str(tmp_path / "zero.holder")
    os.symlink("/dev/zero", zero)
    for path in (fifo, zero):
        t0 = time.monotonic()
        out = read_in_child(path)
        assert out is not None, "the read of %s did not end" % os.path.basename(path)
        assert out.returncode == 0 and out.stdout.strip() == "None", out.stdout + out.stderr
        assert time.monotonic() - t0 < 4


@pytest.mark.parametrize("plant", [
    "not json",
    json.dumps(["x"]),
    "deep:100000",
    "hex:fffe7b007d00",
    '{"kind": "test\\u0007", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": __PID__, "created": __CREATED__, "limit": 9}',
    '{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "0001-01-01T00:00:00Z", "pid": __PID__, "created": __CREATED__, "limit": 9}',
    '{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": __PID__, "created": __CREATED__, "limit": 1e400}',
    '{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": __PID32__, "created": __CREATED__, "limit": 9}',
    '{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": __PID__, "created": ' + "9" * 400 + ', "limit": 9}',
])
def test_r040_untrusted_records_by_launch(tmp_path, plant):
    """R-040 (Requirement 17(a); handoff/TASK-029-r3.md, the record's read): a planted bad record, each
    naming the live helper, never crashes the waiter: it waits with unknown, ends with 123 at the
    provisional bound, and prints no control character; the helper's well-formed twin reads live."""
    br = load_br()
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.0003")
    root = launch_dir(tmp_path)
    holder = waiter = None
    try:
        holder = start_holder(tmp_path, env, delay=0, hold=25, plant=plant)
        _, holder_path = br.heavy_state_paths(env)
        assert wait_until(lambda: os.path.exists(holder_path))
        waiter = popen_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "pass")
        err = waiter.communicate(timeout=15)[1]
        assert waiter.returncode == 123
        assert "Traceback" not in err
        assert all(ord(c) >= 32 for c in err.replace("\n", ""))
        waits = [ln for ln in err.splitlines() if ln.startswith("bridge-run: waiting")]
        assert waits and all(ln == "bridge-run: waiting for the slot held by unknown" for ln in waits)
        assert err.splitlines()[-2:] == [
            "bridge-run: slot not free - held by unknown",
            "bridge-run: exit 123",
        ]
        created = br.process_creation_epoch(holder.pid)
        with open(holder_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(good_record(holder.pid, created)))
        assert br.read_holder_record(holder_path) is not None  # precondition: the helper is live
    finally:
        kill_tree(holder)
        kill_tree(waiter)


def test_r040_wellformed_record_named_in_wait_line(tmp_path):
    """R-040 (Requirement 17(a)'s precondition): a live holder record is named in the waiting line."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    holder = waiter = None
    try:
        holder = start_holder(tmp_path, env, delay=0, hold=20, kind="test", run_id="2026-08-01T09:00:00Z", limit=600)
        time.sleep(0.3)
        waiter = popen_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "pass")
        lines = read_until(waiter, "bridge-run: waiting")
        assert "waiting for the slot held by test 2026-08-01T09:00:00Z since " in lines[-1]
    finally:
        kill_tree(holder)
        kill_tree(waiter)


def test_r040_review_and_watch_skip_slot(tmp_path):
    """R-040 (Requirement 17(b)): a review helper and a gh pr checks watch take no slot; a heavy run
    creates the lock; a review helper runs while a holder has the slot."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    gh = tmp_path / "gh.cmd" if sys.platform == "win32" else tmp_path / "gh"
    gh.write_text("@echo off\necho ok\n" if sys.platform == "win32" else "#!/bin/sh\necho ok\n", encoding="utf-8")
    if sys.platform != "win32":
        gh.chmod(0o755)
    env["PATH"] = str(tmp_path) + os.pathsep + env.get("PATH", "")
    review = run_bridge(root, env, "--limit", "30", "--kind", "review", "--", sys.executable, "-c", "print(1)")
    watch = run_bridge(root, env, "--limit", "30", "--kind", "watch", "--", "gh", "pr", "checks", "1")
    assert review.returncode == 0 and "slot" not in review.stderr
    assert watch.returncode == 0 and "slot" not in watch.stderr
    lock = lock_path_of(env)
    assert not os.path.exists(lock)
    heavy = run_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "pass")
    assert heavy.returncode == 0
    assert os.path.exists(lock)
    holder = None
    try:
        holder = start_holder(tmp_path, env, delay=0, hold=10)
        time.sleep(0.3)
        t0 = time.monotonic()
        review2 = run_bridge(root, env, "--limit", "30", "--kind", "review", "--", sys.executable, "-c", "pass")
        assert review2.returncode == 0 and "slot" not in review2.stderr
        assert time.monotonic() - t0 < 5  # it ran at once, not after the holder
    finally:
        kill_tree(holder)


def test_r040_watch_refuses_non_gh_command(tmp_path):
    """R-040 (Requirement 11): --kind watch with a non-gh command is refused before the slot."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    marker = root / "m.txt"
    out = run_bridge(root, env, "--limit", "30", "--kind", "watch", "--", sys.executable, "-c", "open('m.txt','w')")
    assert out.returncode == 125
    assert "bridge-run: refused - a watch run is only a gh pr checks command" in out.stderr
    assert not os.path.exists(lock_path_of(env))
    assert not marker.exists()


@pytest.mark.parametrize("allow_any", [False, True])
def test_r040_review_refuses_a_heavy_command(tmp_path, allow_any):
    """R-040 (handoff/TASK-029-r3.md, the review kind): --kind review never carries a command the launcher
    knows as another kind (a named test suite, a gh pr checks watch): exit 125 with the review refusal,
    the command never started, no heavy.lock; the limit's cap refusal still comes first."""
    env = env_for() if allow_any else env_without_allow_any()
    root = launch_dir(tmp_path)
    for cmd in (["python", "-m", "pytest", "--version"], ["pytest", "-q"], ["gh", "pr", "checks", "1"]):
        out = run_bridge(root, env, "--limit", "30", "--kind", "review", "--", *cmd)
        assert out.returncode == 125, out.stderr
        assert "bridge-run: refused - a review run is only a cursor-agent command" in out.stderr
        assert "pytest" not in out.stdout and "ok" not in out.stdout
    assert not os.path.exists(lock_path_of(env))
    capped = run_bridge(root, env, "--limit", "99999", "--kind", "review", "--", "python", "-m", "pytest", "--version")
    assert capped.returncode == 125 and "above twice the default for review" in capped.stderr
    assert "a review run is only" not in capped.stderr


def test_r040_wait_before_record_published(tmp_path):
    """R-040 (Requirement 17(c)): the waiter says unknown until the holder publishes, then names it and
    exits at the record's end (start + 6 s + grace), seconds apart from the own-kind floor (1.8 s) and
    the provisional bound (14.5 s)."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    root = launch_dir(tmp_path)
    holder = waiter = None
    try:
        holder = start_holder(tmp_path, env, delay=1.2, hold=30, kind="test", run_id="2026-07-01T10:00:00Z", limit=6)
        time.sleep(0.2)
        t0 = time.monotonic()
        waiter = popen_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "pass")
        err = waiter.communicate(timeout=25)[1]
        elapsed = time.monotonic() - t0
    finally:
        kill_tree(holder)
        kill_tree(waiter)
    assert waiter.returncode == 123
    waits = [ln for ln in err.splitlines() if ln.startswith("bridge-run: waiting")]
    assert waits[0] == "bridge-run: waiting for the slot held by unknown"
    assert "held by test 2026-07-01T10:00:00Z since " in waits[-1]
    assert 4.5 <= elapsed <= 10


def test_r040_bound_stays_first_fixed(tmp_path):
    """R-040 (Requirement 5's fixing rule; 17(d)): the first live record fixes the bound; a replacement
    record (limit 600) is named but does not move it, so the wait ends near the first bound, not at the
    provisional bound, (14,400 + 120) x 0.001 = 14.5 s."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    root = launch_dir(tmp_path)
    br = load_br()
    _, holder_path = br.heavy_state_paths(env)
    first = second = waiter = None
    try:
        first = start_holder(tmp_path, env, delay=0, hold=30, kind="test", run_id="2026-03-01T08:00:00Z", limit=2)
        time.sleep(0.3)
        t0 = time.monotonic()
        waiter = popen_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(0.1)")
        seen = read_until(waiter, "bridge-run: waiting")
        assert "held by test 2026-03-01T08:00:00Z since " in seen[-1]  # the first record fixed the bound
        second = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **SESSION)
        time.sleep(0.1)
        created2 = br.process_creation_epoch(second.pid)
        start2 = datetime.now(timezone.utc).strftime(STAMP)
        with open(holder_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(good_record(second.pid, created2, kind="builder", run_id="2026-03-01T09:00:00Z", start=start2, limit=600)))
        err = waiter.communicate(timeout=25)[1]
        elapsed = time.monotonic() - t0
    finally:
        kill_tree(first)
        kill_tree(second)
        kill_tree(waiter)
    assert waiter.returncode == 123
    waits = [ln for ln in err.splitlines() if ln.startswith("bridge-run: waiting")]
    assert waits and "held by builder 2026-03-01T09:00:00Z since " in waits[-1]
    assert "slot not free - held by builder 2026-03-01T09:00:00Z since " in err
    assert elapsed < 8


def test_r040_waiting_line_keeps_last_live_record(tmp_path):
    """R-040 (Requirement 8; 17(d)): once a live record has been read, a poll that reads no live record
    (the file replaced by text that does not parse) still names the last live record."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    root = launch_dir(tmp_path)
    br = load_br()
    _, holder_path = br.heavy_state_paths(env)
    holder = waiter = None
    try:
        holder = start_holder(tmp_path, env, delay=0, hold=30, kind="test", run_id="2026-06-01T07:00:00Z", limit=5)
        assert wait_until(lambda: br.read_holder_record(holder_path) is not None)  # precondition
        waiter = popen_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "pass")
        read_until(waiter, "bridge-run: waiting")
        with open(holder_path, "w", encoding="utf-8") as f:
            f.write("not json")
        err = waiter.communicate(timeout=25)[1]
    finally:
        kill_tree(holder)
        kill_tree(waiter)
    assert waiter.returncode == 123
    waits = [ln for ln in err.splitlines() if ln.startswith("bridge-run: waiting")]
    assert len(waits) >= 2  # lines after the replacement (one a second)
    assert all("held by test 2026-06-01T07:00:00Z since " in ln for ln in waits)
    assert "slot not free - held by test 2026-06-01T07:00:00Z since " in err


def test_r040_killed_holder_frees_slot(tmp_path):
    """R-040 (Requirements 7 and 17(e)): killing the holder frees the slot: the waiter, seen waiting on
    it, takes the slot within about two seconds of the kill; the dead holder's record reads as none."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    br = load_br()
    _, holder_path = br.heavy_state_paths(env)
    holder = waiter = None
    try:
        holder = start_holder(tmp_path, env, delay=0, hold=60, kind="test", run_id="2026-02-01T00:00:00Z", limit=600)
        assert wait_until(lambda: br.read_holder_record(holder_path) is not None)
        waiter = popen_bridge(root, env, "--limit", "10", "--", sys.executable, "-c", "pass")
        lines = read_until(waiter, "bridge-run: waiting")
        assert "held by test 2026-02-01T00:00:00Z" in lines[-1]
        kill_tree(holder)
        t_kill = time.monotonic()
        assert br.read_holder_record(holder_path) is None
        rest = waiter.communicate(timeout=10)[1]
        t_done = time.monotonic()
    finally:
        kill_tree(holder)
        kill_tree(waiter)
    assert waiter.returncode == 0
    assert "bridge-run: slot taken " in rest
    assert t_done - t_kill < 3


def test_r040_two_heavy_runs_serialize_commands(tmp_path):
    """R-040 (Requirement 17(f)): concurrent heavy runs do not overlap (the second command starts after
    the first ends); the waiter names the first holder with its since and ends by."""
    a, b = launch_dir(tmp_path, "a"), launch_dir(tmp_path, "b")
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.05")
    p1 = p2 = None
    try:
        p1 = popen_bridge(a, env, "--limit", "30", "--", sys.executable, "-c",
                          "import time; open('s','w').write(repr(time.time())); time.sleep(3); open('e','w').write(repr(time.time()))")
        time.sleep(0.5)
        p2 = popen_bridge(b, env, "--limit", "30", "--", sys.executable, "-c",
                          "import time; open('s2','w').write(repr(time.time()))")
        err1 = p1.communicate(timeout=25)[1]
        err2 = p2.communicate(timeout=25)[1]
    finally:
        kill_tree(p1)
        kill_tree(p2)
    rid = err1.splitlines()[0].split("started ", 1)[1]
    taken = next(ln.split("slot taken ", 1)[1] for ln in err1.splitlines() if ln.startswith("bridge-run: slot taken "))
    wait_ln = next(ln for ln in err2.splitlines() if ln.startswith("bridge-run: waiting for the slot held by"))
    assert re.fullmatch(r"bridge-run: waiting for the slot held by test %s since %s, ends by \S+Z" % (re.escape(rid), re.escape(taken)), wait_ln)
    assert err2.splitlines()[-1] == "bridge-run: exit 0"
    assert float((b / "s2").read_text()) >= float((a / "e").read_text())
    taken_ix = next(i for i, ln in enumerate(err2.splitlines()) if ln.startswith("bridge-run: slot taken "))
    wait_ix = next(i for i, ln in enumerate(err2.splitlines()) if ln.startswith("bridge-run: waiting"))
    assert wait_ix < taken_ix


def test_r040_holder_that_waited_publishes_slot_taken_start(tmp_path):
    """R-040 (Requirement 17(f)): a launcher that waited publishes its slot-taken time as since, which a
    third launcher's waiting line shows."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.02")
    r1, r3 = launch_dir(tmp_path, "one"), launch_dir(tmp_path, "three")
    holder = l1 = l3 = None
    try:
        holder = start_holder(tmp_path, env, delay=0, hold=30, kind="test", run_id="2020-01-01T00:00:00Z", limit=600)
        time.sleep(0.3)
        l1 = popen_bridge(r1, env, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(4)")
        first = read_until(l1, "bridge-run: waiting")
        started = first[0].split("started ", 1)[1]
        kill_tree(holder)
        taken = read_until(l1, "bridge-run: slot taken ")[-1].split("slot taken ", 1)[1]
        assert taken != started
        l3 = popen_bridge(r3, env, "--limit", "30", "--", sys.executable, "-c", "pass")
        line = read_until(l3, "bridge-run: waiting")[-1]
        assert "held by test %s since %s, ends by " % (started, taken) in line
    finally:
        kill_tree(holder)
        kill_tree(l1)
        kill_tree(l3)


def test_r040_wait_timeout_exit_123_and_log(tmp_path):
    """R-040 (Requirements 12 and 17(g)): a wait past its bound ends with the exact not-free line and
    exit 123, the command never started (the same command writes its marker once the slot is free);
    the log entry carries slot "not free", its waited, nothing learnable, and --healthy refuses it."""
    br = load_br()
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    root = launch_dir(tmp_path)
    marker = root / "would_run.txt"
    cmd = [sys.executable, "-c", "open(r'%s','w').write('x')" % str(marker).replace("\\", "\\\\")]
    holder = None
    try:
        holder = start_holder(tmp_path, env, delay=0, hold=30, kind="test", run_id="2026-04-01T00:00:00Z", limit=3)
        time.sleep(0.3)
        t0 = time.monotonic()
        out = run_bridge(root, env, "--limit", "5", "--", *cmd, timeout=20)
        elapsed = time.monotonic() - t0
    finally:
        kill_tree(holder)
    assert out.returncode == 123
    lines = out.stderr.splitlines()
    assert lines[-1] == "bridge-run: exit 123"
    m = re.fullmatch(r"bridge-run: slot not free - held by test 2026-04-01T00:00:00Z since (\S+Z), ends by (\S+Z)", lines[-2])
    assert m, lines[-2]
    since, ends = (datetime.strptime(x, STAMP) for x in m.groups())
    assert (ends - since).total_seconds() == 3  # limit 3 plus the scaled grace's whole seconds (0)
    assert not marker.exists()
    log_path = root / "run" / "launcher" / "runs.jsonl"
    log = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert log["exit"] == 123 and log.get("slot") == "not free" and log.get("healthy") is None
    assert log["waited"] >= int(elapsed) - 1
    assert br.learned_limit("test", str(root)) == (1800, "the default for test")
    before = log_path.read_bytes()
    bad = run_bridge(root, env, "--healthy", log["id"])
    assert bad.returncode == 1 and "refused -" in bad.stderr
    assert log_path.read_bytes() == before
    control = run_bridge(root, env, "--limit", "5", "--", *cmd)
    assert control.returncode == 0 and marker.exists()  # precondition: the command does write it
    free = run_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "import sys; sys.exit(123)")
    assert "slot taken" in free.stderr
    log2 = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert "slot" not in log2
    ok = run_bridge(root, env, "--healthy", log2["id"])
    assert ok.returncode == 0


def test_r040_seconds_excludes_wait(tmp_path):
    """R-040 (Requirement 17(h)): runs.jsonl seconds is command time only; waited holds the slot wait."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.02")
    a, b = launch_dir(tmp_path, "a"), launch_dir(tmp_path, "b")
    p1 = p2 = None
    try:
        p1 = popen_bridge(a, env, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(4)")
        time.sleep(0.35)
        p2 = popen_bridge(b, env, "--limit", "30", "--", sys.executable, "-c", "pass")
        p1.communicate(timeout=30)
        p2.communicate(timeout=30)
    finally:
        kill_tree(p1)
        kill_tree(p2)
    log = json.loads((b / "run" / "launcher" / "runs.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1])
    assert log.get("waited", 0) >= 3
    assert log.get("seconds", 99) <= 1


def test_r040_lock_path_from_home(tmp_path, home_of_the_tests):
    """R-040 (Requirement 17(i)): heavy.lock lives under the home, not LOCALAPPDATA or APPDATA."""
    br = load_br()
    env = env_for(LOCALAPPDATA=str(tmp_path / "la"), APPDATA=str(tmp_path / "ap"))
    root = launch_dir(tmp_path)
    out = run_bridge(root, env, "--limit", "10", "--", sys.executable, "-c", "pass")
    assert out.returncode == 0
    lock, _ = br.heavy_state_paths(env)
    assert os.path.normcase(lock) == os.path.normcase(os.path.join(str(home_of_the_tests), ".cursor-bridge", "heavy.lock"))
    assert os.path.exists(lock)
    assert not os.path.exists(tmp_path / "la") and not os.path.exists(tmp_path / "ap")


def test_r040_grace_end_lines_at_scale_one():
    """R-040 (Requirement 17(j)): at scale 1 a line's ends by is its start plus its limit plus 120 s."""
    br = load_br()
    rec = {"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "limit": 10, "pid": 1, "created": 1.0}
    grace = br.SLOT_GRACE
    assert grace == 120
    expect = "2026-01-01T00:02:10Z"  # 00:00:00 + 10 s + 120 s
    assert br._waiting_line(rec, grace).rstrip("\n").endswith("since 2026-01-01T00:00:00Z, ends by " + expect)
    assert br._slot_not_free_line(rec, grace).rstrip("\n") == (
        "bridge-run: slot not free - held by test 2026-01-01T00:00:00Z since 2026-01-01T00:00:00Z, ends by " + expect)


def test_r040_lock_folder_refused(tmp_path):
    """R-040 (Requirement 6): heavy.lock as a folder refuses before the command with no traceback."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    lock = lock_path_of(env)
    os.makedirs(lock)
    marker = root / "m.txt"
    out = run_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "open('m.txt','w')")
    assert out.returncode == 125
    assert re.search(r"bridge-run: refused - ~/.cursor-bridge/heavy\.lock \([^)]+\)", out.stderr)
    assert str(env["HOME"]) not in out.stderr
    assert "Traceback" not in out.stderr
    assert not marker.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX links and permission bits")
def test_r040_lock_link_not_followed_posix(tmp_path):
    """R-040 (Requirement 13; handoff/TASK-029-r3.md, the lock's open): a link planted at heavy.lock is
    not followed: the run is refused before its command, and the link's target keeps its mode."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    lock = lock_path_of(env)
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    target = tmp_path / "target"
    target.write_text("", encoding="utf-8")
    target.chmod(0o644)
    os.symlink(str(target), lock)
    marker = root / "m.txt"
    out = run_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "open('m.txt','w')")
    assert out.returncode == 125
    assert re.search(r"bridge-run: refused - ~/.cursor-bridge/heavy\.lock \([^)]+\)", out.stderr)
    assert "Traceback" not in out.stderr
    assert not marker.exists()
    assert oct(os.stat(target).st_mode & 0o777) == "0o644"


def test_r040_ebadf_not_held():
    """R-040 (Requirement 6): a lock attempt on a closed descriptor is not read as contention."""
    br = load_br()
    fd = os.open(os.devnull, os.O_RDONLY)
    os.close(fd)
    with pytest.raises(OSError):
        br._try_lock_byte(fd)


def test_r040_creation_time_unreadable_skips_record(tmp_path):
    """R-040 (Requirement 16): when creation time cannot be read, no holder record is published."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    script = tmp_path / "noct.py"
    script.write_text(
        "import importlib.util, os, sys\n"
        "prog, cwd = sys.argv[1], sys.argv[2]\n"
        "spec = importlib.util.spec_from_file_location('br', prog)\n"
        "br = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(br)\n"
        "br.process_creation_epoch = lambda _p: None\n"
        "os.chdir(cwd)\n"
        "sys.argv = [prog, '--limit', '5', '--', sys.executable, '-c', \"open('ran.txt','w')\"]\n"
        "raise SystemExit(br.main())\n",
        encoding="utf-8",
    )
    out = subprocess.run(
        [sys.executable, str(script), PROG, str(root)],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert out.returncode == 0
    assert "could not read this process creation time" in out.stderr
    assert "slot taken" in out.stderr and (root / "ran.txt").exists()
    assert not os.path.exists(load_br().heavy_state_paths(env)[1])


def test_r040_limit_under_one_publishes_one(tmp_path):
    """R-040 (Requirement 16): a sub-second limit is published as limit 1, read live while the run holds."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    br = load_br()
    _, holder_path = br.heavy_state_paths(env)
    proc = None
    try:
        proc = popen_bridge(root, env, "--limit", "0.9", "--", sys.executable, "-c", "import time; time.sleep(3)")
        assert wait_until(lambda: br.read_holder_record(holder_path) is not None, timeout=5)
        rec = br.read_holder_record(holder_path)
        assert rec["limit"] == 1 and rec["pid"] == proc.pid
        proc.communicate(timeout=10)
    finally:
        kill_tree(proc)


def test_r040_record_published_while_read(tmp_path, capsys):
    """R-040 (Requirement 14): the record, written by mkstemp and os.replace, is published every time
    while a reader reads it more than ten times a second; a read is a whole record or none, never a
    part of one; no temporary file is left."""
    br = load_br()
    folder = tmp_path / "state"
    folder.mkdir()
    holder_path = str(folder / "heavy.lock.holder")
    records = [good_record(1000 + i, 1.0, limit=i + 1) for i in range(40)]
    stop = threading.Event()
    reads, partial = [0], []

    def reader():
        while not stop.is_set():
            try:
                with open(holder_path, encoding="utf-8") as f:
                    raw = f.read()
            except OSError:
                raw = None  # absent, or the open refused while the file is replaced: no record
            if raw is not None:
                try:
                    if json.loads(raw) not in records:
                        partial.append(raw)
                except ValueError:
                    partial.append(raw)
            reads[0] += 1
            time.sleep(0.005)

    t = threading.Thread(target=reader)
    t.start()
    try:
        results = []
        for rec in records:
            results.append(br.publish_holder_record(holder_path, rec))
            time.sleep(0.01)
    finally:
        stop.set()
        t.join(timeout=10)
    assert reads[0] >= 20
    assert results == [True] * len(records)
    assert partial == []
    assert "could not publish" not in capsys.readouterr().err
    assert sorted(p.name for p in folder.iterdir()) == ["heavy.lock.holder"]


def test_r040_publication_failure_is_a_note(tmp_path, capsys):
    """R-040 (Requirement 14; handoff/TASK-029-r3.md, publication): a record that cannot be published
    (its folder cannot be made, or its temporary file cannot be created) is one note line and False,
    never an exception."""
    br = load_br()
    blocker = tmp_path / "afile"
    blocker.write_text("", encoding="utf-8")
    assert br.publish_holder_record(str(blocker / "heavy.lock.holder"), good_record(1, 1.0)) is False
    assert capsys.readouterr().err.count("bridge-run: note - could not publish the slot holder record") == 1


def test_r040_unpublishable_record_keeps_the_slot(tmp_path):
    """R-040 (Requirement 14): when the record cannot be put in place (its path is a folder), the run
    prints the note, keeps the slot and runs its command."""
    br = load_br()
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    _, holder_path = br.heavy_state_paths(env)
    os.makedirs(holder_path)
    out = run_bridge(root, env, "--limit", "10", "--", sys.executable, "-c", "open('ran.txt','w')")
    assert out.returncode == 0, out.stderr
    assert "bridge-run: note - could not publish the slot holder record" in out.stderr
    assert "slot taken" in out.stderr and (root / "ran.txt").exists()
    assert [p for p in os.listdir(os.path.dirname(holder_path)) if p.endswith(".tmp")] == []


@pytest.mark.parametrize("scale", ["0", "-1", "2", "nan", "abc"])
def test_r040_invalid_slot_scale_refused_first(tmp_path, scale):
    """R-040 (Requirement 15): invalid BRIDGE_RUN_SLOT_SCALE is the first stderr line with no started."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE=scale)
    out = run_bridge(launch_dir(tmp_path), env, "--limit", "5", "--", sys.executable, "-c", "pass")
    assert out.returncode == 125
    assert out.stderr.splitlines()[0].startswith("bridge-run: refused - BRIDGE_RUN_SLOT_SCALE")
    assert "started" not in out.stderr


def test_r040_slot_scale_ignored_without_allow_any(tmp_path):
    """R-040 (Requirement 15): without ALLOW_ANY a set value, valid or not, is ignored with one note line
    and refuses nothing."""
    gh = tmp_path / "gh.cmd" if sys.platform == "win32" else tmp_path / "gh"
    gh.write_text("@echo off\necho ok\n" if sys.platform == "win32" else "#!/bin/sh\necho ok\n", encoding="utf-8")
    if sys.platform != "win32":
        gh.chmod(0o755)
    for value in ("0.25", "abc"):
        env = env_without_allow_any(BRIDGE_RUN_SLOT_SCALE=value)
        env["PATH"] = str(tmp_path) + os.pathsep + env.get("PATH", "")
        out = run_bridge(launch_dir(tmp_path, "s" + str(len(value))), env, "--limit", "30", "--kind", "watch", "--", "gh", "pr", "checks", "1")
        assert out.returncode == 0, out.stderr
        assert out.stderr.count("bridge-run: note - BRIDGE_RUN_SLOT_SCALE is ignored without BRIDGE_RUN_ALLOW_ANY=1") == 1


def test_r040_scale_not_honoured_on_a_heavy_run_without_allow_any(tmp_path):
    """R-040 (Requirement 15): without BRIDGE_RUN_ALLOW_ANY=1 a heavy run waits on the real durations, so
    a slot held without a record is not given up at the scaled provisional bound."""
    env = env_without_allow_any(BRIDGE_RUN_SLOT_SCALE="0.0001")
    root = launch_dir(tmp_path)
    holder = waiter = None
    try:
        holder = start_lock_only(tmp_path, env, hold=30)
        time.sleep(0.3)
        waiter = popen_bridge(root, env, "--limit", "60", "--", "python", "-m", "pytest", "--version")
        time.sleep(5)
        # scaled, the provisional bound is (14,400 + 120) x 0.0001 = 1.5 s and the run would have ended with 123
        assert waiter.poll() is None
    finally:
        kill_tree(waiter)
        kill_tree(holder)
    err = waiter.stderr.read()
    assert err.count("bridge-run: note - BRIDGE_RUN_SLOT_SCALE is ignored without BRIDGE_RUN_ALLOW_ANY=1") == 1
    assert "bridge-run: waiting for the slot held by unknown" in err
    assert "exit 123" not in err


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_r040_posix_lock_modes(tmp_path):
    """R-040 (Requirement 13): state folder 0o700 and heavy.lock 0o600 on POSIX."""
    env = env_for()
    env["HOME"] = str(tmp_path / "h")
    env["USERPROFILE"] = env["HOME"]
    os.makedirs(env["HOME"])
    root = launch_dir(tmp_path)
    out = run_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "pass")
    assert out.returncode == 0
    folder = os.path.join(env["HOME"], ".cursor-bridge")
    lock = os.path.join(folder, "heavy.lock")
    assert oct(os.stat(folder).st_mode & 0o777) == "0o700"
    assert oct(os.stat(lock).st_mode & 0o777) == "0o600"
