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
`# wake`. `--kind driver` accepts only `python <program> [args]` where the program is a `.py`
file under `run/supervisor/` of the launch folder (no link on the path) or
`~/.claude/cursor-bridge/mutation-run.py`; interpreter options before the program (`-c`,
`-m`, `py -3`) are refused. The tests set BRIDGE_RUN_ALLOW_ANY=1 to run their own helpers
through it (driver commands are never exempt).

Ceilings (release A2, plan 10.3): every run is logged to `run/launcher/runs.jsonl` under the
folder the launcher is started in (kind, limit, seconds, exit; never the prompt). `--limit
auto` takes the kind's default (builder 7200, driver 7200, review 3600, watch 3600, test 1800) or, once a
HEALTHY run of that kind is on record, one and a half times the longest healthy run, never
below the default and never above twice it unless `docs/RUN_PARAMETERS.md` carries the
owner's words on a line `Ceiling above twice: <kind> <seconds> (<their words>, <date>)`. The
supervisor marks a run healthy with `--healthy <run id>` once its work passed the gate (the
id is the launch time on the first stderr line, given whole or as a prefix that fits exactly
one run; a run ended at its limit whose kept work merged counts too, so the ceiling can grow);
a test run that exits 0 is marked by the launcher itself. The run that raised a ceiling is
named when the ceiling is chosen. A slow but healthy task is never ended before its ceiling.
An owner's cap below twice the default is ignored with a note: the line says "above twice".
Refuses a design critique round above the ceiling (exit 125, `design ceiling:`).

Since 2026.10.25a: a `--kind review` run whose `--model` is of the family of the branch's last
builder run is refused (exit 125; roster-check.py's REBUILD: the new profile's builder
rebuilds the change first). A builder or review run lists the files beside the Workspace
(its parent folder, the Workspace and `Worktrees/` excluded) before and after, and reports
each new, changed or removed one as `bridge-run: BOUNDARY ...` on stderr and in the run log:
the boundary hook does not run in a headless builder run (ISS-010), so this is the one
detection of a write outside the Workspace. A `gh pr checks <n> --watch` waits up to two
minutes for the pushed head (the local HEAD) to be the pull request's head on GitHub with a
check registered, and says how long it waited, so a watch neither ends at once with "no
checks reported" nor takes the previous commit's run (KP-051). `-p no:cacheprovider` is
accepted after `python -m pytest` as after `pytest`.

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
KINDS = {"builder": 7200, "driver": 7200, "review": 3600, "watch": 3600, "test": 1800}
DRIVER_REFUSE = ("bridge-run: refused - driver kind: only python <program> under run/supervisor/ "
                 "or ~/.claude/cursor-bridge/mutation-run.py\n")
DRIVER_KEYFILE_REFUSE = ("bridge-run: refused - driver kind: --key-file is not allowed; a key file never "
                         "goes to a driver run (its NAME=value pairs reach the interpreter environment "
                         "before the program runs)\n")
LOG = os.path.join("run", "launcher", "runs.jsonl")
LEARN_FACTOR = 1.5
CAP_FACTOR = 2
DESIGN_DEFAULT_ROUNDS = 5
DESIGN_RESOLUTION_DEFAULT = 1
DESIGN_RESOLUTION_LIFTED = 2
DESIGN_PATH_NORM = re.compile(r"[/\\]+(?:\.[/\\]+)*")
DESIGN_MARK = re.compile(r"(?i)run/review/DESIGN-")
DESIGN_NAME_RE = re.compile(r"^(?:([a-z0-9-]*)-)?(R?)([1-9][0-9]*)$")
DESIGN_TOKEN_RE = re.compile(r"[^\s\"'`]+")
DESIGN_LIFT_RE = re.compile(
    r"^\s*[-*]?\s*(?:\*\*(?i:Design rounds above five):\*\*|\*\*(?i:Design rounds above five)\*\*:|(?i:Design rounds above five):)\s*"
    r"([a-z0-9-]+)\s+([0-9]+)\s*\((.+)\)")
DESIGN_TRIM_BEFORE_SEP = re.compile(r"[. ]+(?=[/\\])")


def usage():
    sys.stderr.write("usage: bridge-run.py --limit <seconds|auto> [--kind builder|driver|review|watch|test] [--strip] [--key-file <path>] -- <command> [args...]\n"
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
    return any(":" in p for p in parts)


def own_venv_python(path, folder=None):
    """A path-qualified python is accepted only as the project's own virtual environment's interpreter."""
    full = os.path.abspath(path)
    base = os.path.abspath(folder or os.getcwd())
    norm = full.replace("\\", "/").lower()
    return norm.startswith(base.replace("\\", "/").lower() + "/") and bool(re.search(r"/\.venv/(scripts/python(3)?\.exe|bin/python3?)$", norm))


def python_interpreter_ok(argv, folder=None):
    """Bare python, python3 or py, or the project's own .venv interpreter (shared by test and driver kinds)."""
    if not argv:
        return False
    head = head_of(argv)
    if "/" in argv[0] or "\\" in argv[0]:
        return head in ("python", "python3") and own_venv_python(argv[0], folder)
    return head in ("python", "python3", "py")


def _normcase_path(path):
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def _mutation_run_path():
    return os.path.normpath(os.path.join(os.path.expanduser("~"), ".claude", "cursor-bridge", "mutation-run.py"))


def _program_abs(token, folder):
    if token.startswith("~/") or token.startswith("~\\"):
        return os.path.abspath(os.path.join(os.path.expanduser("~"), token[2:].replace("\\", "/")))
    if os.path.isabs(token):
        return os.path.abspath(token)
    return os.path.abspath(os.path.join(os.path.abspath(folder), token))


def _token_has_dotdot(token):
    return ".." in [p for p in re.split(r"[/\\]", token) if p]


def _colon_in_path_after_drive(abs_path):
    norm = os.path.normpath(abs_path)
    if sys.platform == "win32":
        _, tail = os.path.splitdrive(norm)
        parts = [p for p in tail.split(os.sep) if p]
    else:
        parts = [p for p in norm.split(os.sep) if p]
    return any(":" in p for p in parts)


def _link_component_refused(path):
    try:
        os.lstat(path)
    except OSError:
        return True
    return bridge_env.is_link(path)


def _link_walk_ok(prog, base):
    rel = os.path.relpath(prog, base)
    if rel.startswith(".."):
        return False
    current = base
    for part in rel.split(os.sep):
        current = os.path.join(current, part)
        if _link_component_refused(current):
            return False
    return True


def _supervisor_file_ok(prog, folder):
    base = os.path.abspath(folder)
    supervisor = os.path.normpath(os.path.join(base, "run", "supervisor"))
    sup = _normcase_path(supervisor)
    p = _normcase_path(prog)
    if not (p == sup or p.startswith(sup + os.sep)):
        return False
    if not os.path.isfile(prog):
        return False
    try:
        if os.stat(prog).st_nlink != 1:
            return False
    except OSError:
        return False
    return _link_walk_ok(prog, base)


def _mutation_program_ok(program_token, folder):
    prog = _program_abs(program_token, folder)
    return _normcase_path(prog) == _normcase_path(_mutation_run_path())


def resolve_driver_program(argv, folder=None):
    """Accepted driver program as an absolute, normalised path, or None."""
    if len(argv) < 2 or not python_interpreter_ok(argv, folder) or argv[1].startswith("-"):
        return None
    program = argv[1]
    if not program.endswith(".py"):
        return None
    if _token_has_dotdot(program):
        return None
    prog = _program_abs(program, folder)
    if _colon_in_path_after_drive(prog):
        return None
    if _supervisor_file_ok(prog, folder):
        return os.path.abspath(prog)
    if _mutation_program_ok(program, folder):
        return os.path.abspath(prog)
    return None


def driver_accepted(argv, folder=None):
    """python <program> [args]: program under run/supervisor/ or the installed mutation-run.py."""
    return resolve_driver_program(argv, folder) is not None


def verify_driver_program_abs(abs_prog, folder):
    """Re-check (c)-(e) on the absolute program path already placed in the command to start."""
    if not abs_prog.endswith(".py"):
        return False
    prog = os.path.abspath(abs_prog)
    if _colon_in_path_after_drive(prog):
        return False
    if _supervisor_file_ok(prog, folder):
        return True
    return _normcase_path(prog) == _normcase_path(_mutation_run_path())


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
    if ("/" in argv[0] or "\\" in argv[0]) and not python_interpreter_ok(argv, folder):
        return False                                       # the runner by its bare name; a path only for the project's own .venv python
    escapes = ESCAPE_OPTIONS.get(head, ())
    for i, a in enumerate(argv[1:], 1):
        name = a.split("=", 1)[0]
        attached = next((e for e in escapes if e in ("-p", "-c", "-r") and a.startswith(e) and len(a) > len(e)), None)
        if name in escapes or attached:
            value = a[len(attached):] if attached else (argv[i + 1] if i + 1 < len(argv) else "")
            if head in ("pytest", "uv", "python", "python3", "py") and (name == "-p" or attached == "-p") and value.startswith("no:") and "pytest" in argv and i > argv.index("pytest"):
                continue                                   # `-p no:cacheprovider` disables a plugin (after the word pytest, never uv's or python's own -p; 2026.10.25a: python -m pytest and the project's .venv python too)
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


def design_lifts(folder):
    """{subject: max numbered round} from the first well-formed owner's line per subject."""
    lifts = {}
    try:
        with open(os.path.join(folder, "docs", "RUN_PARAMETERS.md"), encoding="utf-8") as f:
            for line in f:
                m = DESIGN_LIFT_RE.match(line.strip())
                if not m or m.group(1) in lifts:
                    continue
                words = m.group(3).strip()
                if not words:
                    continue
                try:
                    rounds = int(m.group(2))
                except ValueError:
                    continue
                if rounds <= DESIGN_DEFAULT_ROUNDS:
                    continue
                lifts[m.group(1)] = rounds
    except (OSError, UnicodeDecodeError):
        pass
    return lifts


def design_round_written(name):
    return name.rsplit("-", 1)[1] if "-" in name else name


def design_refusal(file_label, subject, round_written, detail, params_path):
    msg = ("design ceiling: %s (subject %s, round %s) %s; looked in %s for "
           "Design rounds above five: supervisor.md, Phase 2" % (
               file_label, subject, round_written, detail, params_path))
    return msg.encode("ascii", "backslashreplace").decode("ascii")


def design_refuse_name(name, token, lifts, params_path):
    """Refusal for one design token; None when allowed."""
    label_name = name if name is not None else token
    round_written = design_round_written(label_name)
    subject = label_name.rsplit("-", 1)[0] if "-" in label_name else ""
    if name is None:
        return design_refusal("DESIGN-%s" % token, subject, round_written, "the name cannot be read", params_path)
    parsed = DESIGN_NAME_RE.match(name)
    if not parsed:
        return design_refusal("DESIGN-%s.md" % name, subject, round_written, "the name cannot be read", params_path)
    subject = parsed.group(1) or ""
    round_written = design_round_written(name)
    try:
        round_n = int(parsed.group(3))
    except ValueError:
        round_n = None
    if parsed.group(2) == "R":
        limit = DESIGN_RESOLUTION_LIFTED if subject in lifts else DESIGN_RESOLUTION_DEFAULT
        if round_n is None or round_n > limit:
            return design_refusal("DESIGN-%s.md" % name, subject, round_written,
                                  "a resolution round beyond R%d" % limit, params_path)
        return None
    limit = lifts.get(subject, DESIGN_DEFAULT_ROUNDS)
    if round_n is None or round_n > limit:
        return design_refusal("DESIGN-%s.md" % name, subject, round_written,
                              "above round %d" % limit, params_path)
    return None


def design_ceiling(argv, folder):
    """Refuse cursor-agent launches naming a design round above the ceiling; None when allowed."""
    if head_of(argv) != "cursor-agent":
        return None
    text = DESIGN_TRIM_BEFORE_SEP.sub("", " ".join(argv))
    norm = DESIGN_PATH_NORM.sub("/", text)
    hits = list(DESIGN_MARK.finditer(norm))
    if not hits:
        return None
    params_path = os.path.join(folder, "docs", "RUN_PARAMETERS.md")
    lifts = design_lifts(folder)
    for m in hits:
        tm = DESIGN_TOKEN_RE.match(norm, m.end())
        token = tm.group(0).rstrip(".,;:)])}'\"") if tm else ""
        if not token.endswith(".md"):
            reason = design_refuse_name(None, token, lifts, params_path)
            if reason:
                return reason
            continue
        reason = design_refuse_name(token[:-3], token, lifts, params_path)
        if reason:
            return reason
    return None


def learned_limit(kind, folder):
    """(limit, reason): the kind's default, or one and a half times the longest healthy run,
    never below the default and never above twice it without the owner's words."""
    default = KINDS[kind]
    cap, _ = cap_for(kind, folder)
    exits = (0, 1) if kind == "driver" else (0, 124)   # 124: ended at its limit, its kept work merged (test kind)
    healthy = [r for r in read_log(folder) if r.get("kind") == kind and r.get("healthy") is True
               and isinstance(r.get("seconds"), (int, float)) and r.get("exit") in exits]
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
    if hit[0].get("kind") == "driver" and hit[0].get("exit") not in (0, 1):
        sys.stderr.write("bridge-run: refused - a driver run is healthy at exit 0 or 1 only\n")
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


def write_pid_file(folder, run_id, pid, child_pid):
    """`run/launcher/pids/<run id>`: the launcher's and the child's pids, for bridge-stop.py; only where run/ exists."""
    if not os.path.isdir(os.path.join(folder, "run")):
        return None
    try:
        d = os.path.join(folder, "run", "launcher", "pids")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, run_id.replace(":", "-"))
        with open(path, "w", encoding="utf-8") as f:
            f.write("%d %d\n" % (pid, child_pid))
        return path
    except OSError:
        return None


def remove_pid_file(path):
    if path:
        try:
            os.remove(path)
        except OSError:
            pass


def branch_of(folder):
    """The checkout's branch at launch (the roster check matches a builder run to the branch under review)."""
    try:
        p = subprocess.run(["git", "-C", folder or ".", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, creationflags=NO_WINDOW)
        return p.stdout.strip() if p.returncode == 0 else None
    except OSError:
        return None


def workspace_of(argv, folder):
    """The folder a cursor-agent run works in: its `--workspace <path>` (a worktree builder, relative to
    the launch folder), else the launch folder; the run is logged under that folder's branch (2026.10.25a)."""
    if head_of(argv) == "cursor-agent":
        for i, a in enumerate(argv):
            if a == "--workspace" and i + 1 < len(argv):
                return os.path.join(folder, argv[i + 1])
            if a.startswith("--workspace="):
                return os.path.join(folder, a.split("=", 1)[1])
    return folder


def model_of(argv):
    """The --model value of a launched command (the roster check compares the reviewer's family with it; release A4)."""
    for i, a in enumerate(argv):
        if a == "--model" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--model="):
            return a.split("=", 1)[1]
    return None


def roster_program():
    """roster-check.py beside this file, loaded as a module (its family and built-by rules are the one copy)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("roster_check", os.path.join(HERE, "roster-check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NOTES = []                                               # printed after the launch line, which stays the first


def review_family_refusal(argv, folder):
    """A Review B of the family that built the change in flight is refused (release A4's rule, held by the
    launcher since 2026.10.25a): after a profile switch the new profile's builder rebuilds the change first."""
    model = model_of(argv)
    if head_of(argv) != "cursor-agent" or not model:
        return None
    try:
        roster = roster_program()
        built = roster.built_by(os.path.join(folder, LOG), branch_of(workspace_of(argv, folder)))
        if not built:
            return None
        built_fam, review_fam = roster.family_of(built), roster.family_of(model)
    except Exception as e:                               # the check never stops a run on its own failure, but says so
        NOTES.append("the review-family check could not run (%s); check the family by hand" % e)
        return None
    if built_fam and built_fam == review_fam:
        return ("Review B %s is of the %s family, which built this change (%s, the branch's last builder run): rebuild it "
                "with the builder in docs/ROSTER.resolved.json first (step 3b; roster-check prints REBUILD)" % (model, review_fam, built))
    return None


WATCH_WAIT = 120                                         # seconds the watch waits for the pushed head's first check
WATCH_STEP = 10


def gh_pr_state(pr_args, folder):
    """(head sha on GitHub, number of checks on it) of the pull request, or (None, None)."""
    try:
        p = subprocess.run(["gh", "pr", "view"] + pr_args + ["--json", "headRefOid,statusCheckRollup"], cwd=folder, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60, creationflags=NO_WINDOW)
        if p.returncode != 0:
            return None, None
        o = json.loads(p.stdout or "{}")
        return o.get("headRefOid"), len(o.get("statusCheckRollup") or [])
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None, None


def local_head(folder):
    try:
        p = subprocess.run(["git", "-C", folder, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW)
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def wait_for_first_check(argv, folder):
    """Before `gh pr checks <n> --watch`: wait up to WATCH_WAIT seconds until the pull request's head on
    GitHub is the local head and has a check (2026.10.25a, FB-002: a watch started seconds after the push
    exited at once with "no checks reported"; KP-051: a watch begun before the new run took the old one).
    Returns the line to print."""
    if "--watch" not in argv:
        return None
    rest = argv[3:]
    pr_args = [a for a in rest[:1] if not a.startswith("-")]
    want = local_head(folder)
    waited = 0
    while True:
        head, checks = gh_pr_state(pr_args, folder)
        if head and want and head == want and checks:
            return "waited %ds for the pushed head %s's first check (%d check(s) registered)" % (waited, want[:12], checks)
        if waited >= WATCH_WAIT:
            return ("waited %ds and the pushed head %s has no check registered on GitHub (its head there: %s); the watch starts anyway "
                    "- if it ends at once with \"no checks reported\", run `gh pr checks <n>` once and start the watch again" % (
                        waited, (want or "?")[:12], (head or "unknown")[:12]))
        time.sleep(WATCH_STEP)
        waited += WATCH_STEP


BOUNDARY_SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
BOUNDARY_MAX = 20000


def boundary_listing(folder):
    """{path relative to the Workspace's parent: (size, mtime_ns)} for every file beside the Workspace
    (the project root's other folders and files), the Workspace itself and the worktrees excluded;
    None when the parent is a drive root or the listing is too large to be a project root."""
    work = os.path.abspath(folder)
    parent = os.path.dirname(work)
    if not parent or os.path.dirname(parent) == parent:
        return None
    found = {}
    same = lambda a, b: os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))   # noqa: E731  (Windows: any case)
    junction = getattr(os.path, "isjunction", lambda p: False)
    for top, dirs, files in os.walk(parent):
        if same(top, parent):
            dirs[:] = [d for d in dirs if not same(os.path.join(parent, d), work) and d.lower() != "worktrees"]
        dirs[:] = [d for d in dirs if d not in BOUNDARY_SKIP and not junction(os.path.join(top, d))]
        for name in files:
            full = os.path.join(top, name)
            try:
                st = os.stat(full)
            except OSError:
                continue
            found[os.path.relpath(full, parent).replace("\\", "/")] = (st.st_size, st.st_mtime_ns)
            if len(found) > BOUNDARY_MAX:
                return None
    return found


def boundary_changes(before, after):
    """[(new|changed|removed, path)] between two listings."""
    out = []
    for path in sorted(set(before) | set(after)):
        b, a = before.get(path), after.get(path)
        if b != a:
            out.append(("new" if b is None else "removed" if a is None else "changed", path))
    return out


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
    kind = flags[flags.index("--kind") + 1] if "--kind" in flags and flags.index("--kind") + 1 < len(flags) else None
    driver_prog = None
    if kind == "driver":
        driver_prog = resolve_driver_program(cmd, folder)
        if driver_prog is None:
            sys.stderr.write(DRIVER_REFUSE)
            return 125
        if "--key-file" in flags:
            sys.stderr.write(DRIVER_KEYFILE_REFUSE)
            return 125
    elif not accepted(cmd, folder):
        sys.stderr.write("bridge-run: refused - the launcher runs only cursor-agent, gh pr checks and the test suites it knows by name, without an option that runs another program, and an npx tool only when the project has it (got %r); a benchmark or an unknown runner runs directly in the background, marked # wake\n" % cmd[0])
        return 125
    if "--key-file" in flags and head_of(cmd) == "cursor-agent":
        sys.stderr.write("bridge-run: refused - a key file never goes to a cursor-agent run (the builder and the reviewer must not see a key)\n")
        return 125
    reason = design_ceiling(cmd, folder)
    if reason:
        sys.stderr.write("bridge-run: refused - %s\n" % reason)
        return 125
    if kind is None:
        kind = kind_of(cmd)
    if kind is None and os.environ.get("BRIDGE_RUN_ALLOW_ANY") == "1":
        kind = "test"                                        # the tests' own helpers
    if kind not in KINDS:
        sys.stderr.write("bridge-run: refused - unknown kind %r (builder, driver, review, watch, test)\n" % kind)
        return 125
    if kind == "review":
        reason = review_family_refusal(cmd, folder)
        if reason:
            sys.stderr.write("bridge-run: refused - %s\n" % reason)
            return 125
    raw = flags[flags.index("--limit") + 1] if flags.index("--limit") + 1 < len(flags) else ""
    if raw != "auto":
        try:
            float(raw)
        except ValueError:
            return usage()
    head = head_of(cmd) if kind == "driver" else head_text(cmd)
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    taken = [r.get("id") for r in read_log(folder)]
    n = 2
    while run_id in taken:                                 # two runs in one second: the second gets a suffix
        run_id = run_id.split("Z")[0] + "Z-%d" % n
        n += 1
    sys.stderr.write("bridge-run: started %s\n" % run_id)         # the FIRST line: review-guard and pr-activity-check read it
    for note in NOTES:
        sys.stderr.write("bridge-run: note - %s\n" % note)
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
    if kind == "driver" and driver_prog is not None:
        cmd = list(cmd)
        cmd[1] = driver_prog
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
    entry = {"id": run_id, "kind": kind, "head": head, "model": model_of(cmd), "branch": branch_of(workspace_of(argv[argv.index("--") + 1:], folder)), "limit": int(limit), "seconds": None, "exit": None, "healthy": None}
    if kind == "watch" and head.startswith("gh pr checks"):
        line = wait_for_first_check(argv[argv.index("--") + 1:], folder)
        if line:
            sys.stderr.write("bridge-run: %s\n" % line)
            sys.stderr.flush()
    # A builder's or reviewer's write outside the Workspace (2026.10.25a, ISS-010: the boundary hook does not run in a
    # headless builder run): the files beside the Workspace are listed before and after, and every new,
    # changed or removed one is reported as BOUNDARY on stderr and in the run log.
    boundary_before = boundary_listing(folder) if kind in ("builder", "review") else None
    if kind in ("builder", "review") and boundary_before is None:
        sys.stderr.write("bridge-run: note - no boundary listing (the Workspace's parent is a drive root or holds over %d files)\n" % BOUNDARY_MAX)

    def report_boundary():
        if boundary_before is None:
            return
        after = boundary_listing(folder)
        if after is None:
            return
        changes = boundary_changes(boundary_before, after)
        for what, path in changes[:20]:
            sys.stderr.write("bridge-run: BOUNDARY %s outside the Workspace: %s\n" % (what, path))
        if len(changes) > 20:
            sys.stderr.write("bridge-run: BOUNDARY ... and %d more\n" % (len(changes) - 20))
        if changes:
            entry["boundary"] = ["%s %s" % c for c in changes[:200]]
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
        if kind == "driver" and len(cmd) >= 2 and not verify_driver_program_abs(cmd[1], folder):
            sys.stderr.write(DRIVER_REFUSE)
            return 125
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
        if kind == "driver" and len(cmd) >= 2 and not verify_driver_program_abs(cmd[1], folder):
            sys.stderr.write(DRIVER_REFUSE)
            return 125
        try:
            proc = subprocess.Popen(cmd, env=env, preexec_fn=os.setsid, creationflags=NO_WINDOW)
        except OSError as e:
            sys.stderr.write("bridge-run: cannot start %s (%s)\n" % (cmd[0], e))
            return 125
        killer = lambda: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)  # noqa: E731

    started = time.time()
    entry.update(pid=os.getpid(), child_pid=proc.pid)
    pid_file = write_pid_file(folder, run_id, os.getpid(), proc.pid)   # read by bridge-stop.py while the run lives (2026.10.11c)
    try:
        rc = proc.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        sys.stderr.write("bridge-run: LIMIT %ds reached after %ds; terminating the whole process tree\n"
                         % (int(limit), int(time.time() - started)))
        report_boundary()                   # before the exit line, which stays the last (the job ends this process)
        sys.stderr.write("bridge-run: exit 124\n")
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
    remove_pid_file(pid_file)
    if rc != 124:
        report_boundary()
        sys.stderr.write("bridge-run: exit %d\n" % rc)
        sys.stderr.flush()
    if entry["exit"] is None:
        healthy = True if (kind == "test" and rc == 0) or (kind == "driver" and rc in (0, 1)) else None
        entry.update(seconds=int(time.time() - started), exit=rc, healthy=healthy)
        write_log(folder, entry)
    # The job handle is deliberately not closed here: it closes when this process exits,
    # after the exit code is set, and "kill on close" then ends any orphan the command left.
    return rc


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
