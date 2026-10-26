"""R-040: one heavy job at a time — the launcher's machine-wide slot on ~/.cursor-bridge/heavy.lock."""
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
BRIDGE_DIR = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")
SESSION = {"start_new_session": True} if sys.platform != "win32" else {}


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


def launch_dir(tmp_path, name="a"):
    root = tmp_path / name
    (root / "run").mkdir(parents=True)
    return root


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
    with open(holder_path, "w", encoding="utf-8") as f:
        f.write(plant)
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


def test_r040_no_tasklist_in_launcher():
    """R-040: slot liveness never shells out to tasklist."""
    text = open(PROG, encoding="utf-8").read()
    assert "tasklist" not in text


def test_r040_wait_uses_monotonic_clock(tmp_path, monkeypatch):
    """R-040: the slot wait deadline follows time.monotonic(), not a jumping wall clock."""
    br = load_br()
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    holder = start_lock_only(tmp_path, env, hold=25)
    time.sleep(0.2)
    real_mono = time.monotonic
    bump = [0]

    def fake_mono():
        return real_mono() + bump[0]

    base_wall = time.time()
    monkeypatch.setattr(time, "monotonic", fake_mono)
    monkeypatch.setattr(time, "time", lambda: base_wall + 100000)
    import threading
    done = []

    def run():
        done.append(br.acquire_heavy_slot("test", "2026-01-01T00:00:00Z", 5, 0.001))

    t = threading.Thread(target=run)
    t.start()
    time.sleep(0.3)
    bump[0] = 100000
    t.join(timeout=5)
    kill_tree(holder)
    assert done and done[0] is None


def test_r040_provisional_bound_without_record(tmp_path):
    """R-040: no live record ends at the scaled provisional bound with only unknown waiting lines."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    root = launch_dir(tmp_path)
    marker = root / "never.txt"
    holder = start_lock_only(tmp_path, env, hold=25)
    time.sleep(0.15)
    t0 = time.monotonic()
    try:
        out = run_bridge(
            root, env, "--limit", "5", "--",
            sys.executable, "-c", "open(r'%s','w').write('x')" % str(marker).replace("\\", "\\\\"),
            timeout=25,
        )
    finally:
        kill_tree(holder)
    elapsed = time.monotonic() - t0
    assert out.returncode == 123
    assert 12 <= elapsed <= 20
    lines = [ln for ln in out.stderr.splitlines() if ln.startswith("bridge-run: waiting")]
    assert lines and all(ln == "bridge-run: waiting for the slot held by unknown" for ln in lines)
    assert out.stderr.splitlines()[-2:] == [
        "bridge-run: slot not free - held by unknown",
        "bridge-run: exit 123",
    ]
    assert not marker.exists()


def test_r040_untrusted_records_in_process(tmp_path):
    """R-040: crafted holder records read as no record; the well-formed twin reads live."""
    br = load_br()
    env = env_for()
    holder = start_holder(tmp_path, env, delay=0, hold=8)
    time.sleep(0.2)
    pid = holder.pid
    created = br.process_creation_epoch(pid)
    assert created is not None
    _, holder_path = br.heavy_state_paths(env)
    cases = [
        "not json",
        "[]",
        json.dumps(good_record(pid, created, kind=["x"])),
        json.dumps(good_record(pid, created, kind="nope")),
        json.dumps(good_record(pid, created, kind="test\u0007")),
        json.dumps(good_record(pid, created, run_id="2026\x0701T00:00:00Z")),
        json.dumps(good_record(pid, created, run_id="2026\u066001T00:00:00Z")),
        json.dumps({**good_record(pid, created), "pid": str(pid)}),
        json.dumps({**good_record(pid, created), "pid": True}),
        json.dumps({**good_record(pid, created), "pid": 0}),
        json.dumps({**good_record(pid, created), "pid": -1}),
        json.dumps({**good_record(pid, created), "pid": 2**64 + 5}),
        json.dumps({**good_record(pid, created), "created": "1"}),
        json.dumps({**good_record(pid, created), "created": True}),
        json.dumps({**good_record(pid, created), "created": float("nan")}),
        json.dumps({**good_record(pid, created), "created": float("inf")}),
        json.dumps({**good_record(pid, created), "limit": "9"}),
        json.dumps({**good_record(pid, created), "limit": 9.9}),
        json.dumps({**good_record(pid, created), "limit": True}),
        json.dumps({**good_record(pid, created), "limit": 0}),
        json.dumps({**good_record(pid, created), "limit": 604801}),
        json.dumps({**good_record(pid, created), "limit": float("inf")}),
        json.dumps({**good_record(pid, created), "limit": 1e400}),
        json.dumps({**good_record(pid, created), "limit": int("9" * 400)}),
        json.dumps(good_record(pid, created, start="0001-01-01T00:00:00Z")),
        json.dumps(good_record(pid, created, start="1999-12-31T23:59:59Z")),
        json.dumps(good_record(pid, created, start="9999-12-31T23:59:59Z")),
        json.dumps(good_record(pid, created, start=(datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S") + "Z")),
        json.dumps(good_record(pid, created, start="2026-02-30T00:00:00Z")),
        json.dumps(good_record(pid, created, start="2026-05-01T12:00:00Z-2")),
        json.dumps(good_record(pid, created, start="2026\u066005-01T12:00:00Z")),
    ]
    try:
        for raw in cases:
            with open(holder_path, "w", encoding="utf-8") as f:
                f.write(raw)
            assert br.read_holder_record(holder_path) is None
        live = good_record(pid, created)
        with open(holder_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(live))
        assert br.read_holder_record(holder_path) is not None
        kill_tree(holder)
        time.sleep(0.3)
        assert br.read_holder_record(holder_path) is None
        wrong_ct = good_record(pid, created + 1.0)
        with open(holder_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(wrong_ct))
        assert br.read_holder_record(holder_path) is None
    finally:
        kill_tree(holder)


@pytest.mark.parametrize("plant", [
    "not json",
    json.dumps(["x"]),
    '{"kind": "test\\u0007", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": 1, "created": 1, "limit": 9}',
    '{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "0001-01-01T00:00:00Z", "pid": 1, "created": 1, "limit": 9}',
    '{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": 1, "created": 1, "limit": 1e400}',
    '{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": 18446744073709551621, "created": 1, "limit": 9}',
])
def test_r040_untrusted_records_by_launch(tmp_path, plant):
    """R-040: planted bad records while a helper holds the lock never crash the waiter."""
    br = load_br()
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    root = launch_dir(tmp_path)
    holder = start_holder(tmp_path, env, delay=0, hold=25, plant=plant)
    time.sleep(0.2)
    waiter = popen_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "pass")
    try:
        err = waiter.communicate(timeout=35)[1]
        assert waiter.returncode == 123
        for ln in err.splitlines():
            if ln.startswith("bridge-run: waiting"):
                assert ln == "bridge-run: waiting for the slot held by unknown"
                assert all(ord(c) >= 32 for c in ln)
        assert "Traceback" not in err
        assert err.splitlines()[-2:] == [
            "bridge-run: slot not free - held by unknown",
            "bridge-run: exit 123",
        ]
    finally:
        kill_tree(holder)
        kill_tree(waiter)


def test_r040_wellformed_record_named_in_wait_line(tmp_path):
    """R-040: precondition — a live holder record is named in the waiting line."""
    br = load_br()
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    holder = start_holder(tmp_path, env, delay=0, hold=8, kind="test", run_id="2026-08-01T09:00:00Z", limit=600)
    waiter = popen_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "pass")
    try:
        time.sleep(0.5)
        err = waiter.stderr.read() or ""
        assert "waiting for the slot held by test 2026-08-01T09:00:00Z" in err
    finally:
        kill_tree(holder)
        kill_tree(waiter)


def test_r040_review_and_watch_skip_slot(tmp_path):
    """R-040: review and gh pr checks watch runs take no slot; heavy run creates the lock."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    gh = tmp_path / "gh.cmd" if sys.platform == "win32" else tmp_path / "gh"
    gh.write_text("@echo off\necho ok\n", encoding="utf-8")
    if sys.platform != "win32":
        gh.chmod(0o755)
    env["PATH"] = str(tmp_path) + os.pathsep + env.get("PATH", "")
    review = run_bridge(root, env, "--limit", "30", "--kind", "review", "--", sys.executable, "-c", "print(1)")
    watch = run_bridge(root, env, "--limit", "30", "--kind", "watch", "--", "gh", "pr", "checks", "1")
    assert review.returncode == 0 and "slot" not in review.stderr
    assert watch.returncode == 0 and "slot" not in watch.stderr
    lock = os.path.join(str(env["HOME"]), ".cursor-bridge", "heavy.lock")
    assert not os.path.exists(lock)
    heavy = run_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "pass")
    assert heavy.returncode == 0
    assert os.path.exists(lock)
    holder = start_holder(tmp_path, env, delay=0, hold=3)
    time.sleep(0.2)
    review2 = run_bridge(root, env, "--limit", "30", "--kind", "review", "--", sys.executable, "-c", "pass")
    try:
        assert review2.returncode == 0
    finally:
        kill_tree(holder)


def test_r040_watch_refuses_non_gh_command(tmp_path):
    """R-040: --kind watch with a non-gh command is refused before the slot."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    lock = os.path.join(str(env["HOME"]), ".cursor-bridge", "heavy.lock")
    out = run_bridge(root, env, "--limit", "30", "--kind", "watch", "--", sys.executable, "-c", "pass")
    assert out.returncode == 125
    assert "bridge-run: refused - a watch run is only a gh pr checks command" in out.stderr
    assert not os.path.exists(lock)


def test_r040_wait_before_record_published(tmp_path):
    """R-040: waiter says unknown until the holder publishes, then exits at the record bound."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    root = launch_dir(tmp_path)
    holder = start_holder(tmp_path, env, delay=0.5, hold=30, kind="test", run_id="2026-07-01T10:00:00Z", limit=4)
    waiter = popen_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "pass")
    try:
        err = waiter.communicate(timeout=25)[1]
        assert waiter.returncode == 123
        assert "held by unknown" in err
        assert "test 2026-07-01T10:00:00Z" in err
    finally:
        kill_tree(holder)
        kill_tree(waiter)


def test_r040_bound_stays_first_fixed(tmp_path):
    """R-040: the wait bound is fixed from the first live record; last_live names the latest holder."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    root = launch_dir(tmp_path)
    first = start_holder(tmp_path, env, delay=0, hold=30, kind="test", run_id="2026-03-01T08:00:00Z", limit=2)
    time.sleep(0.25)
    waiter = popen_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(0.1)")
    time.sleep(0.35)
    br = load_br()
    _, holder_path = br.heavy_state_paths(env)
    second = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(15)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **SESSION,
    )
    time.sleep(0.1)
    created2 = br.process_creation_epoch(second.pid)
    start2 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    with open(holder_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(good_record(second.pid, created2, kind="builder", run_id="2026-03-01T09:00:00Z", start=start2, limit=600)))
    try:
        err = waiter.communicate(timeout=25)[1]
        assert waiter.returncode == 123
        wait_lines = [ln for ln in err.splitlines() if ln.startswith("bridge-run: waiting")]
        assert wait_lines and "builder 2026-03-01T09:00:00Z" in wait_lines[-1]
    finally:
        kill_tree(first)
        kill_tree(second)
        kill_tree(waiter)
    br = load_br()
    last = {"kind": "builder", "run_id": "2026-03-01T09:00:00Z", "start": "2026-03-01T09:00:00Z", "limit": 600, "pid": 1, "created": 1.0}
    assert "builder 2026-03-01T09:00:00Z" in br._waiting_line(last, br.SLOT_GRACE)


def test_r040_killed_holder_frees_slot(tmp_path):
    """R-040: killing the holder lets a waiting launcher take the slot."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    holder = start_holder(tmp_path, env, delay=0, hold=5)
    waiter = popen_bridge(root, env, "--limit", "10", "--", sys.executable, "-c", "pass")
    try:
        time.sleep(0.4)
        kill_tree(holder)
        err = waiter.communicate(timeout=10)[1]
        assert waiter.returncode == 0
        assert "waiting for the slot" in err
        assert "slot taken" in err
        assert time.monotonic()  # waiter finished quickly
    finally:
        kill_tree(holder)
        kill_tree(waiter)


def test_r040_two_heavy_runs_serialize_commands(tmp_path):
    """R-040: concurrent heavy runs do not overlap; the waiter names the first holder."""
    a, b = launch_dir(tmp_path, "a"), launch_dir(tmp_path, "b")
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.05")
    p1 = popen_bridge(a, env, "--limit", "30", "--", sys.executable, "-c", "import time; open('s','w'); time.sleep(3); open('e','w')")
    time.sleep(0.35)
    p2 = popen_bridge(b, env, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(1)")
    try:
        err1 = p1.communicate(timeout=25)[1]
        err2 = p2.communicate(timeout=25)[1]
        rid = err1.splitlines()[0].split("started ", 1)[1]
        taken = next(ln.split("slot taken ", 1)[1] for ln in err1.splitlines() if ln.startswith("bridge-run: slot taken "))
        wait_ln = next(ln for ln in err2.splitlines() if ln.startswith("bridge-run: waiting for the slot held by"))
        assert "test %s" % rid in wait_ln
        assert "since %s" % taken in wait_ln
        assert err2.splitlines()[-1] == "bridge-run: exit 0"
        taken_ix = next(i for i, ln in enumerate(err2.splitlines()) if ln.startswith("bridge-run: slot taken "))
        wait_ix = next(i for i, ln in enumerate(err2.splitlines()) if ln.startswith("bridge-run: waiting"))
        assert wait_ix < taken_ix
    finally:
        kill_tree(p1)
        kill_tree(p2)


def test_r040_holder_that_waited_publishes_slot_taken_start(tmp_path):
    """R-040: a launcher that waited publishes slot taken time as since (see also two_heavy serialize)."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.02")
    root = launch_dir(tmp_path)
    holder = start_holder(tmp_path, env, delay=0, hold=30, kind="test", run_id="2020-01-01T00:00:00Z", limit=600)
    l1 = popen_bridge(root, env, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(1)")
    try:
        time.sleep(0.4)
        kill_tree(holder)
        err1 = l1.communicate(timeout=15)[1]
        taken = next(ln.split("slot taken ", 1)[1] for ln in err1.splitlines() if ln.startswith("bridge-run: slot taken "))
        started = err1.splitlines()[0].split("started ", 1)[1]
        assert taken != started
        br = load_br()
        rec = json.loads(open(br.heavy_state_paths(env)[1], encoding="utf-8").read())
        assert rec["start"] == taken
    finally:
        kill_tree(holder)
        kill_tree(l1)


def test_r040_wait_timeout_exit_123_and_log(tmp_path):
    """R-040: bound exceeded logs slot not free and refuses --healthy."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.001")
    root = launch_dir(tmp_path)
    marker = root / "would_run.txt"
    holder = start_holder(tmp_path, env, delay=0, hold=30, kind="test", run_id="2026-04-01T00:00:00Z", limit=3)
    time.sleep(0.2)
    try:
        out = run_bridge(
            root, env, "--limit", "5", "--",
            sys.executable, "-c", "open(r'%s','w').write('x')" % str(marker).replace("\\", "\\\\"),
            timeout=12,
        )
    finally:
        kill_tree(holder)
    assert out.returncode == 123
    assert out.stderr.splitlines()[-1] == "bridge-run: exit 123"
    assert "slot not free - held by test" in out.stderr and "2026-04-01T00:00:00Z" in out.stderr
    assert not marker.exists()
    log = json.loads((root / "run" / "launcher" / "runs.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1])
    assert log["exit"] == 123 and log.get("slot") == "not free" and log.get("healthy") is None
    rid = log["id"]
    before = (root / "run" / "launcher" / "runs.jsonl").read_bytes()
    bad = run_bridge(root, env, "--healthy", rid)
    assert bad.returncode == 1 and "refused -" in bad.stderr
    assert (root / "run" / "launcher" / "runs.jsonl").read_bytes() == before
    free = run_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "import sys; sys.exit(123)")
    assert "slot taken" in free.stderr
    log2 = json.loads((root / "run" / "launcher" / "runs.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1])
    assert "slot" not in log2
    ok = run_bridge(root, env, "--healthy", log2["id"])
    assert ok.returncode == 0


def test_r040_seconds_excludes_wait(tmp_path):
    """R-040: runs.jsonl seconds is command time only; waited holds the slot wait."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.02")
    a, b = launch_dir(tmp_path, "a"), launch_dir(tmp_path, "b")
    p1 = popen_bridge(a, env, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(4)")
    time.sleep(0.35)
    p2 = popen_bridge(b, env, "--limit", "30", "--", sys.executable, "-c", "pass")
    try:
        p1.communicate(timeout=30)
        p2.communicate(timeout=30)
        kill_tree(p1)
    finally:
        kill_tree(p1)
        kill_tree(p2)
    log = json.loads((b / "run" / "launcher" / "runs.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1])
    assert log.get("waited", 0) >= 3
    assert log.get("seconds", 99) <= 1


def test_r040_lock_path_from_home(tmp_path, home_of_the_tests):
    """R-040: heavy.lock lives under the test home, not LOCALAPPDATA or APPDATA."""
    br = load_br()
    env = env_for(LOCALAPPDATA=str(tmp_path / "la"), APPDATA=str(tmp_path / "ap"))
    root = launch_dir(tmp_path)
    out = run_bridge(root, env, "--limit", "10", "--", sys.executable, "-c", "pass")
    assert out.returncode == 0
    lock, _ = br.heavy_state_paths(env)
    assert str(home_of_the_tests).replace("\\", "/") in lock.replace("\\", "/")
    assert br.heavy_state_paths(env)[0] == lock


def test_r040_grace_end_lines_at_scale_one():
    """R-040: ends by is start plus limit plus grace at scale 1."""
    br = load_br()
    rec = {"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "limit": 10, "pid": 1, "created": 1.0}
    grace = br.SLOT_GRACE
    line = br._waiting_line(rec, grace)
    end = line.split("ends by ")[1].strip()
    start = datetime.strptime("2026-01-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    expect = (start.timestamp() + 10 + grace)
    got = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    assert int(got) == int(expect)


def test_r040_lock_folder_refused(tmp_path):
    """R-040: heavy.lock as a folder refuses before the command with no traceback."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    lock = os.path.join(str(env["HOME"]), ".cursor-bridge", "heavy.lock")
    os.makedirs(lock)
    marker = root / "m.txt"
    out = run_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "open('m.txt','w')")
    assert out.returncode == 125
    assert re.search(r"bridge-run: refused - ~/.cursor-bridge/heavy\.lock \([^)]+\)", out.stderr)
    assert str(env["HOME"]) not in out.stderr
    assert "Traceback" not in out.stderr
    assert not marker.exists()


def test_r040_ebadf_not_held():
    """R-040: a lock attempt on a closed descriptor is not read as contention."""
    br = load_br()
    fd = os.open(os.devnull, os.O_RDONLY)
    os.close(fd)
    with pytest.raises(OSError):
        br._try_lock_byte(fd)


def test_r040_creation_time_unreadable_skips_record(tmp_path):
    """R-040: when creation time cannot be read, no holder record is published."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    env["BRIDGE_RUN_ALLOW_ANY"] = "1"
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
        "sys.argv = [prog, '--limit', '5', '--', sys.executable, '-c', 'pass']\n"
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
    assert "could not read this process creation time" in out.stderr
    assert not os.path.exists(load_br().heavy_state_paths(env)[1])


def test_r040_limit_under_one_publishes_one(tmp_path):
    """R-040: a sub-second limit is published as limit 1 in the holder record."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    br = load_br()
    _, holder_path = br.heavy_state_paths(env)
    proc = popen_bridge(root, env, "--limit", "0.5", "--", sys.executable, "-c", "import time; time.sleep(0.2)")
    try:
        time.sleep(0.4)
        rec = json.loads(open(holder_path, encoding="utf-8").read())
        assert rec["limit"] == 1
        proc.communicate(timeout=10)
        assert proc.returncode == 0
    finally:
        kill_tree(proc)


@pytest.mark.parametrize("scale", ["0", "-1", "2", "nan", "abc"])
def test_r040_invalid_slot_scale_refused_first(tmp_path, scale):
    """R-040: invalid BRIDGE_RUN_SLOT_SCALE is the first stderr line with no started."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE=scale)
    out = run_bridge(launch_dir(tmp_path), env, "--limit", "5", "--", sys.executable, "-c", "pass")
    assert out.returncode == 125
    assert out.stderr.splitlines()[0].startswith("bridge-run: refused - BRIDGE_RUN_SLOT_SCALE")
    assert "started" not in out.stderr


def test_r040_slot_scale_ignored_without_allow_any(tmp_path):
    """R-040: BRIDGE_RUN_SLOT_SCALE without ALLOW_ANY is ignored with one note line."""
    env = dict(os.environ)
    env.pop("BRIDGE_RUN_ALLOW_ANY", None)
    env["BRIDGE_RUN_SLOT_SCALE"] = "0.25"
    gh = tmp_path / "gh.cmd" if sys.platform == "win32" else tmp_path / "gh"
    gh.write_text("@echo off\necho ok\n", encoding="utf-8")
    if sys.platform != "win32":
        gh.chmod(0o755)
    env["PATH"] = str(tmp_path) + os.pathsep + env.get("PATH", "")
    root = launch_dir(tmp_path)
    out = run_bridge(root, env, "--limit", "30", "--kind", "watch", "--", "gh", "pr", "checks", "1")
    assert out.returncode == 0
    assert out.stderr.count("bridge-run: note - BRIDGE_RUN_SLOT_SCALE is ignored without BRIDGE_RUN_ALLOW_ANY=1") == 1


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_r040_posix_lock_modes(tmp_path):
    """R-040: state folder 0o700 and heavy.lock 0o600 on POSIX."""
    env = dict(os.environ)
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
