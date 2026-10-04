#!/usr/bin/env python3
"""bridge-run: run a command under a hard time limit that kills its whole process tree.

  python ~/.claude/cursor-bridge/bridge-run.py --limit <seconds> -- <command> [args...]

Why it exists (KP-033): a background builder, reviewer or watch that hangs holds the loop
until the owner notices, and on Windows a plain timeout kills only the first process while
its children (node under cmd.exe, a dev server under npx) live on and keep the output pipe
open, so the supervisor is never woken. This program starts the command inside a Windows
Job Object with "kill on close": at the limit the job is terminated, every descendant dies
with it, the pipe closes, and the supervisor wakes with exit code 124. On other platforms
the command runs in its own process group, which is killed as a whole.

- stdout and stderr are inherited, so `2> run/agent/TASK-nnn.err` works unchanged.
- The exit code is the command's own; 124 = the limit was hit; 125 = could not start.
- `cursor-agent` is started the way Windows needs it (the .cmd launcher) and with the
  owner's identity withheld, the same recipe as cursor-agent.shim (KP-032).
- Progress note: when the limit is hit, the last 20 lines of stderr are not available here
  (they are in the .err file the caller redirected); the exit code is the signal.

ASCII-only on purpose (cp1252 consoles).
"""
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env  # noqa: E402

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def usage():
    sys.stderr.write("usage: bridge-run.py --limit <seconds> -- <command> [args...]\n")
    return 2


def resolve(argv):
    if not argv:
        return argv, False
    if os.path.basename(argv[0]).lower() in ("cursor-agent", "cursor-agent.cmd", "cursor-agent.exe"):
        launcher = bridge_env.cursor_agent_launcher()
        if launcher is None:
            sys.stderr.write("bridge-run: cursor-agent not found (PATH or %LOCALAPPDATA%/cursor-agent)\n")
            sys.exit(125)
        return launcher + argv[1:], True
    if sys.platform == "win32":
        import shutil
        found = shutil.which(argv[0]) or argv[0]
        if found.lower().endswith((".cmd", ".bat")):
            return ["cmd.exe", "/d", "/c", found] + argv[1:], False
        return [found] + argv[1:], False
    return argv, False


class Job(object):
    """A Windows Job Object that kills every member when terminated or closed."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.k32 = ctypes.windll.kernel32
        self.handle = self.k32.CreateJobObjectW(None, None)
        if not self.handle:
            raise OSError("CreateJobObject failed")

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class BASIC(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class EXTENDED(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS),
                        ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

        info = EXTENDED()
        info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.k32.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            raise OSError("SetInformationJobObject failed")

    def assign(self, proc):
        import ctypes
        PROCESS_SET_QUOTA, PROCESS_TERMINATE = 0x0100, 0x0001
        h = self.k32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, proc.pid)
        if not h:
            raise OSError("OpenProcess failed")
        try:
            if not self.k32.AssignProcessToJobObject(self.handle, h):
                raise OSError("AssignProcessToJobObject failed (error %d)" % ctypes.get_last_error())
        finally:
            self.k32.CloseHandle(h)

    def terminate(self):
        self.k32.TerminateJobObject(self.handle, 124)

    def close(self):
        self.k32.CloseHandle(self.handle)


def main():
    argv = sys.argv[1:]
    if "--limit" not in argv or "--" not in argv:
        return usage()
    try:
        limit = float(argv[argv.index("--limit") + 1])
    except (IndexError, ValueError):
        return usage()
    cmd = argv[argv.index("--") + 1:]
    if not cmd:
        return usage()
    cmd, is_agent = resolve(cmd)
    env = bridge_env.stripped_env() if is_agent else dict(os.environ)

    if sys.platform == "win32":
        job = Job()
        # CREATE_SUSPENDED is not exposed by Popen; assign right after creation instead. The
        # launcher (cmd.exe) needs milliseconds to spawn its child, and a child created after
        # the assignment inherits the job, so the window is far smaller than any real start.
        try:
            # A process created without a console (NO_WINDOW) does not inherit the standard
            # handles by itself; they are passed explicitly so the caller's redirects hold.
            proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=sys.stdout, stderr=sys.stderr,
                                    creationflags=NO_WINDOW | 0x00000200)  # CREATE_NEW_PROCESS_GROUP
        except OSError as e:
            sys.stderr.write("bridge-run: cannot start %s (%s)\n" % (cmd[0], e))
            return 125
        try:
            job.assign(proc)
        except OSError as e:
            sys.stderr.write("bridge-run: job assignment failed (%s); running without a tree kill\n" % e)
        killer = job.terminate
        closer = job.close
    else:
        try:
            proc = subprocess.Popen(cmd, env=env, preexec_fn=os.setsid, creationflags=NO_WINDOW)
        except OSError as e:
            sys.stderr.write("bridge-run: cannot start %s (%s)\n" % (cmd[0], e))
            return 125
        killer = lambda: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)  # noqa: E731
        closer = lambda: None  # noqa: E731

    started = time.time()
    try:
        rc = proc.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        sys.stderr.write("bridge-run: LIMIT %ds reached after %ds; terminating the whole process tree\n"
                         % (int(limit), int(time.time() - started)))
        try:
            killer()
        except OSError as e:
            sys.stderr.write("bridge-run: terminate failed (%s)\n" % e)
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
        rc = 124
    finally:
        try:
            closer()
        except Exception:
            pass
    return rc


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
