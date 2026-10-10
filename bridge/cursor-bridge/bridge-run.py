#!/usr/bin/env python3
"""bridge-run: run one of the loop's commands under a hard time limit that kills its whole
process tree.

  python ~/.claude/cursor-bridge/bridge-run.py --limit <seconds|auto> [--kind <kind>] [--key-file <path>] -- <command> [args...]
  python ~/.claude/cursor-bridge/bridge-run.py --healthy <run id> [--kind <kind>]

Why it exists (KP-033): a background builder, reviewer or watch that hangs holds the loop
until the owner notices, and on Windows a plain timeout kills only the first process while
its children (node under cmd.exe, a dev server under npx) live on and keep the output pipe
open, so the supervisor is never woken. This program puts ITSELF into a Windows Job Object
with "kill on close" before it starts the command, so every process the command creates is
born inside the job: at the limit the job is terminated and every member dies with it, the
pipe closes, and the supervisor wakes with exit code 124; at a normal end, closing the job
kills any orphan the command left behind. On other platforms the command runs in its own
process group, killed as a whole.

What it accepts (release 0a review, F6; release A2): only the commands the loop runs through
it, each by name: `cursor-agent …` (a builder, or Review B with `--kind review`), `gh pr
checks …` (the CI watch) and the test suites the supervisor awaits (`pytest`, `python -m
pytest`, `python -m unittest`, `uv run pytest`, `npm test`, `npm run test*`, `pnpm test`,
`yarn test`, `npx vitest`, `npx jest`, `npx playwright test`, `node --test`, `go test`,
`cargo test`, `dotnet test`); an option that would run another program or delete a folder
(`-exec`, `-p`, `-c`, `--config`, `--basetemp`) is refused, an `npx` tool is accepted only
when it is installed in the project (`node_modules/.bin/`), and `--key-file` is refused with
`cursor-agent` (a key must never reach the builder); anything else is refused with exit 125,
so the launcher's allow rule cannot become a way to run arbitrary commands unseen. A
benchmark or a runner the launcher does not know runs directly in the background, marked
`# wake`. The tests set BRIDGE_RUN_ALLOW_ANY=1 to run their own helpers through it.

Ceilings (release A2, plan 10.3): every run is logged to `run/launcher/runs.jsonl` under the
folder the launcher is started in (kind, limit, seconds, exit; never the prompt). `--limit
auto` takes the kind's default (builder 7200, review 3600, watch 3600, test 1800) or, once a
HEALTHY run of that kind is on record, one and a half times the longest healthy run, never
below the default and never above twice it unless `docs/RUN_PARAMETERS.md` carries the
owner's words on a line `Ceiling above twice: <kind> <seconds> (<their words>, <date>)`. The
supervisor marks a run healthy with `--healthy <run id>` once its work passed the gate (the
id is the launch time on the first stderr line, given whole or as a prefix that fits exactly
one run; a run ended at its limit whose kept work merged counts too, so the ceiling can grow);
a test run that exits 0 is marked by the launcher itself. The run that raised a ceiling is
named when the ceiling is chosen. A slow but healthy task is never ended before its ceiling.
An owner's cap below twice the default is ignored with a note: the line says "above twice".

`--key-file <path>` (release A2): a file of `NAME=value` lines, outside the Workspace, whose
values reach the child's environment only; names are printed, values never (the owner's
rule of 2026-10-05: no secret through the environment the owner sets).

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
import json
import os
import re
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env  # noqa: E402

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
AGENT_NAMES = ("cursor-agent", "cursor-agent.cmd", "cursor-agent.exe")
KINDS = {"builder": 7200, "review": 3600, "watch": 3600, "test": 1800}
LOG = os.path.join("run", "launcher", "runs.jsonl")
LEARN_FACTOR = 1.5
CAP_FACTOR = 2


def usage():
    sys.stderr.write("usage: bridge-run.py --limit <seconds|auto> [--kind builder|review|watch|test] [--strip] [--key-file <path>] -- <command> [args...]\n"
                     "       bridge-run.py --healthy <run id>\n")
    return 2


def head_of(argv):
    return os.path.basename(argv[0]).lower().replace(".exe", "").replace(".cmd", "") if argv else ""


ESCAPE_OPTIONS = {                                     # options that run another program or delete a folder, per runner
    "pytest": ("-p", "-c", "--basetemp", "--rootdir", "--plugin"), "python": ("-p", "-c", "--basetemp", "--rootdir"), "uv": ("-p", "-c", "--basetemp"),
    "go": ("-exec", "-toolexec"), "cargo": ("--config", "-Z"), "node": ("--require", "-r", "--import", "--loader", "--experimental-loader"),
    "npx": ("--package", "-p", "-c", "--call"), "npm": (), "pnpm": (), "yarn": (), "dotnet": ()}


UV_VALUE_OPTIONS = ("--project", "--directory", "--package")   # -p is --python, refused
UV_FLAGS = ("--frozen", "--locked", "--no-sync", "--offline", "-q", "--quiet")


def uv_run_pytest(argv):
    """`uv run [--project x] [--directory x] [--frozen|--locked|--no-sync] pytest ...`: only these options
    before pytest, never --with, --python or a script (the first review of A3, finding 9)."""
    i = 2
    while i < len(argv):
        if argv[i] in UV_VALUE_OPTIONS:
            i += 2
            continue
        if "=" in argv[i] and argv[i].split("=", 1)[0] in UV_VALUE_OPTIONS:         # --project=x
            i += 1
            continue
        if argv[i] in UV_FLAGS:
            i += 1
            continue
        return argv[i] == "pytest"
    return False


def own_venv_python(path, folder=None):
    """A path-qualified python is accepted only as the project's own virtual environment's interpreter."""
    full = os.path.abspath(path)
    base = os.path.abspath(folder or os.getcwd())
    norm = full.replace("\\", "/").lower()
    return norm.startswith(base.replace("\\", "/").lower() + "/") and bool(re.search(r"/\.venv/(scripts/python(3)?\.exe|bin/python3?)$", norm))


def named_suite(argv):
    """A test suite the launcher knows by name (release A2)."""
    head, rest = head_of(argv), argv[1:3]
    return (head == "pytest"
             or head in ("python", "python3", "py") and rest[:2] in (["-m", "pytest"], ["-m", "unittest"])
             or head == "uv" and uv_run_pytest(argv)
             or head in ("npm", "pnpm", "yarn") and (rest[:1] == ["test"] or (rest[:1] == ["run"] and rest[1:2] and rest[1].startswith("test")))
             or head == "npx" and rest[:1] in (["vitest"], ["jest"], ["playwright"])
             or head == "node" and rest[:1] == ["--test"]
             or head in ("go", "cargo", "dotnet") and rest[:1] == ["test"])


def test_suite(argv, folder=None):
    """A named test suite the launcher accepts: never with an option that runs another program
    or deletes a folder; an npx tool only when the project has it installed."""
    head, rest = head_of(argv), argv[1:3]
    if not named_suite(argv):
        return False
    if ("/" in argv[0] or "\\" in argv[0]) and not (head in ("python", "python3") and own_venv_python(argv[0], folder)):
        return False                                       # the runner by its bare name; a path only for the project's own .venv python
    escapes = ESCAPE_OPTIONS.get(head, ())
    for i, a in enumerate(argv[1:], 1):
        name = a.split("=", 1)[0]
        attached = next((e for e in escapes if e in ("-p", "-c", "-r") and a.startswith(e) and len(a) > len(e)), None)
        if name in escapes or attached:
            value = a[len(attached):] if attached else (argv[i + 1] if i + 1 < len(argv) else "")
            if head in ("pytest", "uv") and (name == "-p" or attached == "-p") and value.startswith("no:") and "pytest" in argv and i > argv.index("pytest"):
                continue                                   # `-p no:cacheprovider` disables a plugin (after the word pytest, never uv's own -p)
            return False
    if head == "npx" and not os.path.isfile(os.path.join(folder or os.getcwd(), "node_modules", ".bin", rest[0])) \
            and not os.path.isfile(os.path.join(folder or os.getcwd(), "node_modules", ".bin", rest[0] + ".cmd")):
        return False                                       # npx would fetch it from the registry, outside the gate
    return True


def kind_of(argv):
    """The kind a command is, when its name says so."""
    head = head_of(argv)
    if head == "cursor-agent":
        return "builder"
    if head == "gh" and argv[1:3] == ["pr", "checks"]:
        return "watch"
    if named_suite(argv):
        return "test"
    return None


def accepted(argv, folder=None):
    """The inner commands the loop runs through the launcher."""
    if not argv:
        return False
    if kind_of(argv) is not None and (kind_of(argv) != "test" or test_suite(argv, folder)):
        return True
    return os.environ.get("BRIDGE_RUN_ALLOW_ANY") == "1"


def read_log(folder):
    runs = []
    try:
        with open(os.path.join(folder, LOG), encoding="utf-8") as f:
            for line in f:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if isinstance(o, dict):
                    runs.append(o)
    except OSError:
        pass
    return runs


def write_log(folder, entry):
    """Append one run to the project's run log; written only where a project's `run/` folder
    exists (the Workspace the loop runs from), and a log that cannot be written never stops a run."""
    if not os.path.isdir(os.path.join(folder, "run")):
        return
    try:
        os.makedirs(os.path.dirname(os.path.join(folder, LOG)), exist_ok=True)
        with open(os.path.join(folder, LOG), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        sys.stderr.write("bridge-run: run log not written (%s)\n" % e)


def cap_for(kind, folder):
    """(cap, note): twice the default, or the owner's recorded value when it is above that."""
    default = KINDS[kind]
    owner = owner_cap(kind, folder)
    if owner and owner > CAP_FACTOR * default:
        return owner, ""
    if owner:
        return CAP_FACTOR * default, "the run parameters' `Ceiling above twice: %s %d` is not above twice the default (%d) and is ignored" % (kind, owner, CAP_FACTOR * default)
    return CAP_FACTOR * default, ""


def owner_cap(kind, folder):
    """The owner's recorded words lifting a kind's cap above twice its default, or None."""
    try:
        with open(os.path.join(folder, "docs", "RUN_PARAMETERS.md"), encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^\s*[-*]?\s*\**Ceiling above twice\**\s*:\s*(\w+)\s+(\d+)\s*\((.+)\)", line.strip(), re.I)
                if m and m.group(1).lower() == kind and m.group(3).strip():
                    return int(m.group(2))
    except OSError:
        pass
    return None


def learned_limit(kind, folder):
    """(limit, reason): the kind's default, or one and a half times the longest healthy run,
    never below the default and never above twice it without the owner's words."""
    default = KINDS[kind]
    cap, _ = cap_for(kind, folder)
    healthy = [r for r in read_log(folder) if r.get("kind") == kind and r.get("healthy") is True
               and isinstance(r.get("seconds"), (int, float)) and r.get("exit") in (0, 124)]   # 124: ended at its limit, its kept work merged
    if not healthy:
        return default, "the default for %s" % kind
    longest = max(healthy, key=lambda r: r["seconds"])
    if LEARN_FACTOR * longest["seconds"] <= default:
        return default, "the default for %s (the longest healthy run, %s at %ds, needs no more)" % (kind, longest.get("id"), int(longest["seconds"]))
    limit = int(min(cap, LEARN_FACTOR * longest["seconds"]))
    return limit, "learned from run %s (%ds, healthy); cap %ds" % (longest.get("id"), int(longest["seconds"]), int(cap))


def mark_healthy(run_id, folder, kind=None):
    runs = read_log(folder)
    hit = [r for r in runs if str(r.get("id", "")).startswith(run_id) and (kind is None or r.get("kind") == kind)]
    if not hit:
        sys.stderr.write("bridge-run: no run %s in %s\n" % (run_id, LOG))
        return 1
    if len(hit) > 1:
        sys.stderr.write("bridge-run: refused - %s fits %d runs (%s); give the whole id, and --kind when two kinds share it\n" % (
            run_id, len(hit), ", ".join("%s %s" % (r.get("id"), r.get("kind")) for r in hit[:6])))
        return 1
    for r in hit:
        r["healthy"] = True
    try:
        with open(os.path.join(folder, LOG), "w", encoding="utf-8") as f:
            for r in runs:
                f.write(json.dumps(r) + "\n")
    except OSError as e:
        sys.stderr.write("bridge-run: run log not written (%s)\n" % e)
        return 1
    sys.stderr.write("bridge-run: run %s marked healthy (%s, %ds)\n" % (hit[-1].get("id"), hit[-1].get("kind"), int(hit[-1].get("seconds") or 0)))
    return 0


def key_file_env(path, folder):
    """{NAME: value} from a key file outside the Workspace; values are never printed."""
    full = os.path.abspath(path)
    inside = os.path.commonpath([full, os.path.abspath(folder)]) == os.path.abspath(folder) if os.path.splitdrive(full)[0].lower() == os.path.splitdrive(os.path.abspath(folder))[0].lower() else False
    if inside:
        raise ValueError("the key file must lie outside the folder the launcher runs in (%s is inside %s)" % (path, folder))
    found = {}
    with open(full, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                found[name] = value.strip().strip('"').strip("'")
    return found


def head_text(argv):
    """The program's name and its subcommand, from the command as given: never an argument,
    never a prompt (`cursor-agent`, `gh pr checks`, `pytest`, `npm test`)."""
    head = head_of(argv)
    subs = [a for a in argv[1:3] if a in ("pr", "checks", "test", "run", "pytest", "unittest", "vitest", "jest", "playwright", "--test", "-m") or a.startswith("test")]
    if head == "cursor-agent":
        return head
    return " ".join([head] + subs)[:40]


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
    folder = os.getcwd()
    if argv[:1] == ["--healthy"]:
        kind = argv[argv.index("--kind") + 1] if "--kind" in argv and argv.index("--kind") + 1 < len(argv) else None
        return mark_healthy(argv[1], folder, kind) if len(argv) >= 2 and argv[1] and argv[1] != "--kind" else usage()
    if "--limit" not in argv or "--" not in argv:
        return usage()
    flags = argv[:argv.index("--")]
    cmd = argv[argv.index("--") + 1:]
    if not cmd:
        return usage()
    if not accepted(cmd, folder):
        sys.stderr.write("bridge-run: refused - the launcher runs only cursor-agent, gh pr checks and the test suites it knows by name, without an option that runs another program, and an npx tool only when the project has it (got %r); a benchmark or an unknown runner runs directly in the background, marked # wake\n" % cmd[0])
        return 125
    if "--key-file" in flags and head_of(cmd) == "cursor-agent":
        sys.stderr.write("bridge-run: refused - a key file never goes to a cursor-agent run (the builder and the reviewer must not see a key)\n")
        return 125
    kind = flags[flags.index("--kind") + 1] if "--kind" in flags and flags.index("--kind") + 1 < len(flags) else kind_of(cmd)
    if kind is None and os.environ.get("BRIDGE_RUN_ALLOW_ANY") == "1":
        kind = "test"                                        # the tests' own helpers
    if kind not in KINDS:
        sys.stderr.write("bridge-run: refused - unknown kind %r (builder, review, watch, test)\n" % kind)
        return 125
    raw = flags[flags.index("--limit") + 1] if flags.index("--limit") + 1 < len(flags) else ""
    if raw != "auto":
        try:
            float(raw)
        except ValueError:
            return usage()
    head = head_text(cmd)
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    taken = [r.get("id") for r in read_log(folder)]
    n = 2
    while run_id in taken:                                 # two runs in one second: the second gets a suffix
        run_id = run_id.split("Z")[0] + "Z-%d" % n
        n += 1
    sys.stderr.write("bridge-run: started %s\n" % run_id)         # the FIRST line: review-guard and pr-activity-check read it
    sys.stderr.flush()
    cap, cap_note = cap_for(kind, folder)
    if cap_note:
        sys.stderr.write("bridge-run: %s\n" % cap_note)
    if raw == "auto":
        limit, why = learned_limit(kind, folder)
        sys.stderr.write("bridge-run: limit %ds for %s (%s)\n" % (limit, kind, why))
    else:
        limit = float(raw)
        if limit > cap:
            sys.stderr.write("bridge-run: refused - a limit of %ds is above twice the default for %s (%ds); the owner's words in docs/RUN_PARAMETERS.md (`Ceiling above twice: %s <seconds> (<their words>, <date>)`) lift the cap\n" % (int(limit), kind, cap, kind))
            return 125
    strip = "--strip" in flags
    cmd, is_agent = resolve(cmd)
    try:
        env = bridge_env.stripped_env() if (is_agent or strip) else dict(os.environ)
    except bridge_env.AgentHomeError as e:
        sys.stderr.write("bridge-run: refused - %s\n" % e)
        return 125
    if "--key-file" in flags:
        try:
            keys = key_file_env(flags[flags.index("--key-file") + 1], folder)
        except (IndexError, OSError, ValueError) as e:
            sys.stderr.write("bridge-run: refused - key file: %s\n" % e)
            return 125
        env.update(keys)
        sys.stderr.write("bridge-run: key file read (%d name(s): %s)\n" % (len(keys), ", ".join(sorted(keys)) or "none"))
    entry = {"id": run_id, "kind": kind, "head": head, "limit": int(limit), "seconds": None, "exit": None, "healthy": None}

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
        entry.update(seconds=int(time.time() - started), exit=124)
        write_log(folder, entry)            # before the job ends this process too
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
    if entry["exit"] is None:
        entry.update(seconds=int(time.time() - started), exit=rc, healthy=(True if kind == "test" and rc == 0 else None))   # a passing test run is its own gate
        write_log(folder, entry)
    # The job handle is deliberately not closed here: it closes when this process exits,
    # after the exit code is set, and "kill on close" then ends any orphan the command left.
    return rc


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
