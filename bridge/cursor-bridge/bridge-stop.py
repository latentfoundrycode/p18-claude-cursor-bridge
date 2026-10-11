#!/usr/bin/env python3
"""bridge-stop: end a background task's whole process tree (release A4 follow-up, 2026.10.11c).

  python bridge-stop.py <run id>          a run of the launcher: its child's tree, then the launcher
  python bridge-stop.py --pid <pid>       any process and everything under it

Run from the Workspace root. The launcher's run log (`run/launcher/runs.jsonl`) carries each
run's `pid` (the launcher) and `child_pid` (the command it started) since 2026.10.11c; a run
id is exact or a unique prefix. On Windows the tree is ended with `taskkill /T /F`; elsewhere
the process group is signalled with SIGKILL, then the process itself. Stopping a verification
loop this way never advances it into its next driver, since the loop and its children end
together (KP-056); the app's own TaskStop ends the loop only. Prints what it ended and whether
anything of the tree survived. Exit 0 = ended or already gone, 1 = something survived,
2 = no such run or bad arguments. Windowless. Never writes the run log.
"""
import json
import os
import signal
import subprocess
import sys
import time

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
LOG = os.path.join("run", "launcher", "runs.jsonl")


def runs(folder="."):
    try:
        with open(os.path.join(folder, LOG), encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("id"):
            out.append(e)
    return out


def alive(pid):
    if sys.platform == "win32":
        p = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"], capture_output=True, text=True, creationflags=NO_WINDOW)
        return str(pid) in p.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def command_line(pid):
    """The command line of a process, or '' when it cannot be read."""
    try:
        if sys.platform == "win32":
            p = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Process -Filter 'ProcessId=%d').CommandLine" % pid],
                               capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW)
            return (p.stdout or "").strip()
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        try:
            p = subprocess.run(["ps", "-o", "args=", "-p", str(pid)], capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW)
            return (p.stdout or "").strip()
        except (OSError, subprocess.SubprocessError):
            return ""


def end_tree(pid):
    """End `pid` and everything under it; True when nothing of it is left."""
    if not alive(pid):
        print("bridge-stop: %d is not running" % pid)
        return True
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, text=True, creationflags=NO_WINDOW)
    else:
        try:
            if os.getpgid(pid) != os.getpgid(0):           # never the caller's own group
                os.killpg(os.getpgid(pid), signal.SIGKILL)
        except OSError:
            pass
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    for _ in range(20):
        if not alive(pid):
            print("bridge-stop: ended %d and its tree" % pid)
            return True
        time.sleep(0.25)
    print("bridge-stop: %d SURVIVED the stop; end it by hand (Task Manager, or `taskkill /T /F /PID %d` as the owner)" % (pid, pid))
    return False


def main(argv):
    if not argv:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    if argv[0] == "--pid":
        if len(argv) < 2 or not argv[1].isdigit():
            print("bridge-stop: --pid needs a number")
            return 2
        pid = int(argv[1])
        if not alive(pid):
            print("bridge-stop: %d is not running (nothing to end)" % pid)
            return 2
        print("bridge-stop: ending %d: %s" % (pid, command_line(pid)[:160] or "(command line unreadable)"))
        return 0 if end_tree(pid) else 1
    wanted = argv[0]
    pid_dir = os.path.join("run", "launcher", "pids")
    names = sorted(n for n in (os.listdir(pid_dir) if os.path.isdir(pid_dir) else []) if n == wanted.replace(":", "-") or n.startswith(wanted.replace(":", "-")))
    if len(names) == 1:                                    # a run still living: its pid file
        pid_path = os.path.join(pid_dir, names[0])
        try:
            with open(pid_path, encoding="utf-8") as f:
                pid, child_pid = (int(x) for x in f.read().split()[:2])
        except (OSError, ValueError) as e:
            print("bridge-stop: the pid file of %s is unreadable (%s)" % (names[0], e))
            return 2
        if not alive(pid) or "bridge-run" not in command_line(pid):   # a launcher killed from outside left its file; the pid may belong to another program by now
            print("bridge-stop: the pid file of %s is stale (pid %d is not a running launcher); removed, nothing ended" % (names[0], pid))
            try:
                os.remove(pid_path)
            except OSError:
                pass
            return 2
        ok = end_tree(child_pid)
        ok = end_tree(pid) and ok
        return 0 if ok else 1
    matches = [e for e in runs() if e["id"] == wanted or e["id"].startswith(wanted)]
    if len(matches) != 1:
        print("bridge-stop: %s run(s) match %s in %s and %d pid file(s); give the exact id" % (len(matches), wanted, LOG, len(names)))
        return 2
    e = matches[0]
    if e.get("exit") is not None:
        print("bridge-stop: run %s has ended (exit %s); nothing to stop" % (e["id"], e["exit"]))
        return 2
    ok = True
    for key in ("child_pid", "pid"):
        if isinstance(e.get(key), int):
            ok = end_tree(e[key]) and ok
    if not any(isinstance(e.get(k), int) for k in ("child_pid", "pid")):
        print("bridge-stop: run %s carries no pid (logged before 2026.10.11c); use --pid" % e["id"])
        return 2
    return 0 if ok else 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main(sys.argv[1:]))
