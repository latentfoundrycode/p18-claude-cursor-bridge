"""R-040: one heavy job at a time — the launcher's machine-wide slot on ~/.cursor-bridge/heavy.lock."""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
BRIDGE_DIR = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge")


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
lock_path, holder_path = br.heavy_state_paths()
os.makedirs(os.path.dirname(lock_path), exist_ok=True)
fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
if not br._try_lock_byte(fd):
    sys.exit(2)
time.sleep(delay)
taken = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
br.publish_holder_record(holder_path, {
    "kind": kind, "run_id": run_id, "pid": os.getpid(),
    "created": br.process_creation_epoch(os.getpid()) or time.time(),
    "start": taken, "limit": limit,
})
time.sleep(hold)
'''


def start_holder(tmp_path, env, delay=0, hold=5, kind="test", run_id="2020-01-01T00:00:00Z", limit=30):
    script = tmp_path / "holder.py"
    script.write_text(HOLDER_SRC, encoding="utf-8")
    return subprocess.Popen(
        [sys.executable, str(script), BRIDGE_DIR, str(delay), str(hold), kind, run_id, str(limit)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def kill_tree(proc):
    if proc.poll() is not None:
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


def test_r040_two_heavy_runs_serialize_commands(tmp_path):
    """R-040: concurrent heavy runs do not overlap; the waiter names the holder then takes the slot."""
    a, b = launch_dir(tmp_path, "a"), launch_dir(tmp_path, "b")
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.05")
    p1 = subprocess.Popen(
        [sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(3)"],
        cwd=str(a), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    time.sleep(0.3)
    p2 = subprocess.Popen(
        [sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(1)"],
        cwd=str(b), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    try:
        err2 = p2.communicate(timeout=25)[1]
        p1.wait(timeout=25)
    finally:
        kill_tree(p1)
        kill_tree(p2)
    lines = err2.splitlines()
    assert lines[0].startswith("bridge-run: started ")
    wait_ix = next(i for i, ln in enumerate(lines) if ln.startswith("bridge-run: waiting for the slot held by"))
    assert "test " in lines[wait_ix] and "since " in lines[wait_ix] and "ends by " in lines[wait_ix]
    taken_ix = next(i for i, ln in enumerate(lines) if ln.startswith("bridge-run: slot taken "))
    assert wait_ix < taken_ix
    assert lines[-1] == "bridge-run: exit 0"


def test_r040_unknown_record_then_named_waiter(tmp_path, home_of_the_tests):
    """R-040: before the holder publishes, the waiter says unknown, then names the holder."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.02")
    root = launch_dir(tmp_path)
    proc = start_holder(tmp_path, env, delay=1.5, hold=8, kind="test", run_id="2026-01-02T12:00:00Z", limit=600)
    time.sleep(0.2)
    waiter = subprocess.Popen(
        [sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", "pass"],
        cwd=str(root), env=env, stderr=subprocess.PIPE, text=True,
    )
    try:
        err = waiter.communicate(timeout=20)[1]
        proc.wait(timeout=10)
    finally:
        kill_tree(proc)
    assert "held by unknown" in err
    assert "2026-01-02T12:00:00Z" in err or "waiting for the slot held by test" in err


def test_r040_holder_start_is_slot_taken_time(tmp_path):
    """R-040: a holder publishes slot taken as start so ends-by uses that time, not its run id."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    proc = start_holder(tmp_path, env, delay=0, hold=30, kind="test", run_id="2026-06-01T10:00:00Z", limit=3)
    time.sleep(0.2)
    short_bound = run_bridge(root, env, "--limit", "5", "--", sys.executable, "-c", "open('x','w')")
    try:
        proc.wait(timeout=15)
    finally:
        kill_tree(proc)
    assert short_bound.returncode == 123
    m = re.search(r"since (2026-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z), ends by (2026-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", short_bound.stderr)
    assert m and m.group(1) != "2026-06-01T10:00:00Z"
    def z_epoch(text):
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()

    start_epoch = z_epoch(m.group(1))
    end_epoch = z_epoch(m.group(2))
    assert 2 <= end_epoch - start_epoch <= 5


def test_r040_review_skips_slot(tmp_path, program):
    """R-040: review runs at once with no slot line and do not create the lock file."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    proc = start_holder(tmp_path, env, delay=0, hold=5)
    time.sleep(0.2)
    review = run_bridge(
        root, env, "--limit", "30", "--kind", "review", "--",
        sys.executable, "-c", "print('ok')",
    )
    try:
        proc.wait(timeout=10)
    finally:
        kill_tree(proc)
    assert review.returncode == 0
    assert "slot taken" not in review.stderr and "waiting for the slot" not in review.stderr
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    fe = dict(os.environ)
    fe["HOME"] = str(fresh)
    fe["USERPROFILE"] = str(fresh)
    fe["BRIDGE_RUN_ALLOW_ANY"] = "1"
    run_bridge(launch_dir(fresh), fe, "--limit", "5", "--kind", "review", "--", sys.executable, "-c", "pass")
    assert not os.path.exists(os.path.join(str(fresh), ".cursor-bridge", "heavy.lock"))


def test_r040_killed_holder_frees_slot(tmp_path):
    """R-040: killing the holder lets a waiter take the slot within about two seconds."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    proc = start_holder(tmp_path, env, delay=0, hold=60)
    time.sleep(0.3)
    kill_tree(proc)
    time.sleep(0.5)
    t0 = time.time()
    got = run_bridge(root, env, "--limit", "10", "--", sys.executable, "-c", "pass")
    assert got.returncode == 0 and "slot taken" in got.stderr
    assert time.time() - t0 < 5


def test_r040_bound_fixed_when_second_holder_arrives(tmp_path):
    """R-040: a second holder during the wait does not extend the waiter's bound."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    first = start_holder(tmp_path, env, delay=0, hold=25, kind="test", run_id="2026-03-01T08:00:00Z", limit=2)
    time.sleep(0.2)
    waiter = subprocess.Popen(
        [sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", "open('nope')"],
        cwd=str(root), env=env, stderr=subprocess.PIPE, text=True,
    )
    time.sleep(0.5)
    second = start_holder(tmp_path, env, delay=0, hold=20, kind="builder", run_id="2026-03-01T09:00:00Z", limit=600)
    try:
        err = waiter.communicate(timeout=25)[1]
        assert waiter.returncode == 123
    finally:
        kill_tree(first)
        kill_tree(second)
    assert "bridge-run: exit 123" in err.splitlines()[-1]
    assert "builder 2026-03-01T09:00:00Z" in err or "test 2026-03-01T08:00:00Z" in err


def test_r040_wait_timeout_exit_123_and_log(tmp_path):
    """R-040: bound exceeded → exit 123, command file absent, log not healthy."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    marker = root / "would_run.txt"
    proc = start_holder(tmp_path, env, delay=0, hold=40, kind="test", run_id="2026-04-01T00:00:00Z", limit=3)
    time.sleep(0.2)
    out = run_bridge(
        root, env, "--limit", "5", "--",
        sys.executable, "-c", "open(r'%s','w').write('x')" % str(marker).replace("\\", "\\\\"),
    )
    try:
        proc.wait(timeout=45)
    finally:
        kill_tree(proc)
    assert out.returncode == 123
    assert out.stderr.rstrip().endswith("bridge-run: exit 123")
    assert "slot not free" in out.stderr
    assert not marker.exists()
    log = json.loads((root / "run" / "launcher" / "runs.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1])
    assert log["exit"] == 123 and log.get("healthy") is None and log.get("waited", 0) >= 0


def test_r040_seconds_excludes_wait(tmp_path):
    """R-040: runs.jsonl seconds is command time; waited holds the slot wait."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.02")
    a, b = launch_dir(tmp_path, "a"), launch_dir(tmp_path, "b")
    p1 = subprocess.Popen(
        [sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(2)"],
        cwd=str(a), env=env, stderr=subprocess.DEVNULL,
    )
    time.sleep(0.3)
    p2 = subprocess.Popen(
        [sys.executable, PROG, "--limit", "30", "--", sys.executable, "-c", "import time; time.sleep(2)"],
        cwd=str(b), env=env, stderr=subprocess.DEVNULL,
    )
    try:
        p1.wait(timeout=30)
        p2.wait(timeout=30)
    finally:
        kill_tree(p1)
        kill_tree(p2)
    log = json.loads((b / "run" / "launcher" / "runs.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1])
    assert log.get("waited", 0) >= 1
    assert log.get("seconds", 99) <= 5


def test_r040_lock_path_from_home(tmp_path, home_of_the_tests, program):
    """R-040: heavy.lock lives under the test home, not LOCALAPPDATA or APPDATA."""
    br = program("bridge-run")
    env = env_for(
        LOCALAPPDATA=str(tmp_path / "la"),
        APPDATA=str(tmp_path / "ap"),
    )
    root = launch_dir(tmp_path)
    out = run_bridge(root, env, "--limit", "10", "--", sys.executable, "-c", "pass")
    assert out.returncode == 0
    lock, _ = br.heavy_state_paths(env)
    assert str(home_of_the_tests) in lock
    assert "localappdata" not in lock.lower() and "ap" not in lock.replace("/", "\\").split("\\")[-3:]
    assert br.heavy_state_paths(env)[0] == lock


def test_r040_bad_record_does_not_crash_waiter(tmp_path, program):
    """R-040: corrupt holder records are ignored safely on stderr."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE="0.01")
    root = launch_dir(tmp_path)
    mod = program("bridge-run")
    _, holder = mod.heavy_state_paths(env)
    os.makedirs(os.path.dirname(holder), exist_ok=True)
    with open(holder, "w", encoding="utf-8") as f:
        f.write('{"kind": "test\\x07", "run_id": "2026-01-01T00:00:00Z", "pid": 1, "created": 1, "start": "2026-01-01T00:00:00Z", "limit": 9}')
    proc = start_holder(tmp_path, env, delay=0, hold=8)
    time.sleep(0.2)
    waiter = subprocess.Popen(
        [sys.executable, PROG, "--limit", "8", "--", sys.executable, "-c", "pass"],
        cwd=str(root), env=env, stderr=subprocess.PIPE, text=True,
    )
    try:
        err = waiter.communicate(timeout=15)[1]
        proc.wait(timeout=10)
    finally:
        kill_tree(proc)
    assert "\x07" not in err
    assert "held by unknown" in err or waiter.returncode in (0, 123)


@pytest.mark.parametrize("scale", ["0", "-1", "2", "nan", "abc"])
def test_r040_invalid_slot_scale(tmp_path, scale):
    """R-040: invalid BRIDGE_RUN_SLOT_SCALE → exit 125."""
    env = env_for(BRIDGE_RUN_SLOT_SCALE=scale)
    out = run_bridge(launch_dir(tmp_path), env, "--limit", "5", "--", sys.executable, "-c", "pass")
    assert out.returncode == 125
    assert out.stderr.startswith("bridge-run: refused - BRIDGE_RUN_SLOT_SCALE")
