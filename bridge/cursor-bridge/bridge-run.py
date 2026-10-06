#!/usr/bin/env python3
"""bridge-run: run one of the loop's commands under a hard time limit that kills its whole
process tree.

  python ~/.claude/cursor-bridge/bridge-run.py --limit <seconds> -- <command> [args...]

Why it exists (KP-033): a background builder, reviewer or watch that hangs holds the loop
until the owner notices, and on Windows a plain timeout kills only the first process while
its children (node under cmd.exe, a dev server under npx) live on and keep the output pipe
open, so the supervisor is never woken. This program puts ITSELF into a Windows Job Object
with "kill on close" before it starts the command, so every process the command creates is
born inside the job: at the limit the job is terminated and every member dies with it, the
pipe closes, and the supervisor wakes with exit code 124; at a normal end, closing the job
kills any orphan the command left behind. On other platforms the command runs in its own
process group, killed as a whole.

What it accepts (release 0a review, F6): only the commands the loop runs through it,
`cursor-agent …` and `gh pr checks …`; anything else is refused with exit 125, so the
launcher's allow rule cannot become a way to run arbitrary commands unseen. The tests set
BRIDGE_RUN_ALLOW_ANY=1 to run their own helpers through it.

- stdout and stderr are inherited, so `2> run/agent/TASK-nnn.err` works unchanged.
- The first line on stderr is `bridge-run: started <UTC time>Z`, which is what
  pr-activity-check.py's --since needs; the last is `bridge-run: exit <code>`, which
  review-guard.py reads to tell a review that reached a verdict from one that failed.
- The exit code is the command's own; 124 = the limit was hit; 125 = refused or could not
  start.
- `cursor-agent` is started the way Windows needs it (the .cmd launcher) and with the
  owner's identity withheld, the same recipe as cursor-agent.shim (KP-032). `--strip`
  withholds it for any other accepted command too.

ASCII-only on purpose (cp1252 consoles).
"""
import datetime
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env  # noqa: E402

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
AGENT_NAMES = ("cursor-agent", "cursor-agent.cmd", "cursor-agent.exe")


def usage():
    sys.stderr.write("usage: bridge-run.py --limit <seconds> [--strip] -- <command> [args...]\n")
    return 2


def accepted(argv):
    """The inner commands the loop runs through the launcher."""
    if not argv:
        return False
    head = os.path.basename(argv[0]).lower()
    if head in AGENT_NAMES:
        return True
    if head in ("gh", "gh.exe") and argv[1:3] == ["pr", "checks"]:
        return True
    return os.environ.get("BRIDGE_RUN_ALLOW_ANY") == "1"


def resolve(argv):
    """Return (argv to start, is_agent)."""
    if os.path.basename(argv[0]).lower() in AGENT_NAMES:
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
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        # Declare the signatures: without them ctypes passes HANDLEs as 32-bit ints, and the
        # current process's pseudo-handle (-1) arrives truncated as an invalid handle.
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.SetInformationJobObject.restype = wintypes.BOOL
        k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k.AssignProcessToJobObject.restype = wintypes.BOOL
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.GetCurrentProcess.restype = wintypes.HANDLE
        k.TerminateJobObject.restype = wintypes.BOOL
        k.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.k32 = k
        self.handle = k.CreateJobObjectW(None, None)
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

    def assign_self(self):
        """Put this process into the job; every process it creates from now on is born in it."""
        import ctypes
        if not self.k32.AssignProcessToJobObject(self.handle, self.k32.GetCurrentProcess()):
            raise OSError("AssignProcessToJobObject failed (error %d)" % ctypes.get_last_error())

    def terminate(self):
        """Ends every member, this process included, with exit code 124."""
        self.k32.TerminateJobObject(self.handle, 124)


def main():
    argv = sys.argv[1:]
    if "--limit" not in argv or "--" not in argv:
        return usage()
    try:
        limit = float(argv[argv.index("--limit") + 1])
    except (IndexError, ValueError):
        return usage()
    strip = "--strip" in argv[:argv.index("--")]
    cmd = argv[argv.index("--") + 1:]
    if not cmd:
        return usage()
    if not accepted(cmd):
        sys.stderr.write("bridge-run: refused - the launcher runs only cursor-agent and gh pr checks (got %r)\n" % cmd[0])
        return 125
    cmd, is_agent = resolve(cmd)
    try:
        env = bridge_env.stripped_env() if (is_agent or strip) else dict(os.environ)
    except bridge_env.AgentHomeError as e:
        sys.stderr.write("bridge-run: refused - %s\n" % e)
        return 125
    sys.stderr.write("bridge-run: started %sZ\n" % datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
    sys.stderr.flush()

    killer = None
    if sys.platform == "win32":
        try:
            job = Job()
            job.assign_self()
            killer = job.terminate
        except OSError as e:
            sys.stderr.write("bridge-run: no job object (%s); the limit will end the first process only\n" % e)
            job = None
        try:
            # A process created without a console (NO_WINDOW) does not inherit the standard
            # handles by itself; they are passed explicitly so the caller's redirects hold.
            proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=sys.stdout, stderr=sys.stderr,
                                    creationflags=NO_WINDOW | 0x00000200)  # CREATE_NEW_PROCESS_GROUP
        except OSError as e:
            sys.stderr.write("bridge-run: cannot start %s (%s)\n" % (cmd[0], e))
            return 125
        if killer is None:
            killer = proc.kill
    else:
        try:
            proc = subprocess.Popen(cmd, env=env, preexec_fn=os.setsid, creationflags=NO_WINDOW)
        except OSError as e:
            sys.stderr.write("bridge-run: cannot start %s (%s)\n" % (cmd[0], e))
            return 125
        killer = lambda: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)  # noqa: E731

    started = time.time()
    try:
        rc = proc.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        sys.stderr.write("bridge-run: LIMIT %ds reached after %ds; terminating the whole process tree\nbridge-run: exit 124\n"
                         % (int(limit), int(time.time() - started)))
        sys.stderr.flush()
        try:
            killer()                        # on Windows this ends this process too, with exit code 124
        except OSError as e:
            sys.stderr.write("bridge-run: terminate failed (%s)\n" % e)
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
        rc = 124
    if rc != 124:
        sys.stderr.write("bridge-run: exit %d\n" % rc)
        sys.stderr.flush()
    # The job handle is deliberately not closed here: it closes when this process exits,
    # after the exit code is set, and "kill on close" then ends any orphan the command left.
    return rc


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
