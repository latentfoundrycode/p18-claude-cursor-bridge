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
- Heavy runs (`builder`, `test`, `driver`) take one machine-wide slot on
  `~/.cursor-bridge/heavy.lock` before the command starts and hold it until the launcher
  process ends; a second heavy run waits, prints who holds the slot once a minute, and exits
  123 if the wait bound passes without the slot. `review` and `watch` take no slot. After
  `bridge-run: started <run id>`, the launch's own notes, the limit line and the other launch
  lines, and before the command starts: waiting lines, then `bridge-run: slot taken <UTC time>Z`,
  or `bridge-run: slot not free - ...` and `bridge-run: exit 123`. A run that waited logs
  `waited` (whole seconds in the slot queue); a run that ended waiting logs `"slot": "not free"`.
- The exit code is the command's own; 123 = the slot was not free in time; 124 = the limit was
  hit; 125 = refused or could not start.
- `BRIDGE_RUN_SLOT_SCALE` (test-only, honoured only beside `BRIDGE_RUN_ALLOW_ANY=1`): when set
  to a number with 0 < value <= 1, scales the slot wait reporting interval, grace and wait
  bounds for tests; without `BRIDGE_RUN_ALLOW_ANY=1` a set value is ignored and one note line
  says so.
- `cursor-agent` is started the way Windows needs it (the .cmd launcher) and with the
  owner's identity withheld, the same recipe as cursor-agent.shim (KP-032). `--strip`
  withholds it for any other accepted command too.

ASCII-only on purpose (cp1252 consoles).
"""
import datetime
import hashlib
import json
import math
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
HEAVY_KINDS = frozenset(("builder", "driver", "test"))
SLOT_GRACE = 120
SLOT_REPORT = 60
SLOT_BUILDER_CAP = CAP_FACTOR * KINDS["builder"]
SLOT_CLOCK_SKEW = 300
SLOT_LIMIT_MAX = 604800
PID_MAX = 4294967295 if sys.platform == "win32" else 4194304
RUN_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z(?:-\d+)?$", re.ASCII)
SLOT_START_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", re.ASCII)
SLOT_START_MIN = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
WATCH_ONLY_REFUSE = ("bridge-run: refused - a watch run is only a gh pr checks command\n")
REVIEW_ONLY_REFUSE = ("bridge-run: refused - a review run is only a cursor-agent command\n")
DESIGN_DEFAULT_ROUNDS = 5
DESIGN_RESOLUTION_DEFAULT = 1
DESIGN_RESOLUTION_LIFTED = 2
DESIGN_PATH_NORM = bridge_env.DESIGN_PATH_NORM
DESIGN_MARK = bridge_env.DESIGN_MARK
DESIGN_NAME_RE = re.compile(r"^(?:([a-z0-9-]*)-)?(R?)([1-9][0-9]*)$")
DESIGN_TOKEN_RE = bridge_env.DESIGN_TOKEN_RE
DESIGN_LIFT_RE = re.compile(
    r"^\s*[-*]?\s*(?:\*\*(?i:Design rounds above five):\*\*|\*\*(?i:Design rounds above five)\*\*:|(?i:Design rounds above five):)\s*"
    r"([a-z0-9-]+)\s+([0-9]+)\s*\((.+)\)")
DESIGN_TRIM_BEFORE_SEP = bridge_env.DESIGN_TRIM_BEFORE_SEP


def usage():
    sys.stderr.write("usage: bridge-run.py --limit <seconds|auto> [--kind builder|driver|review|watch|test] [--strip] [--key-file <path>] -- <command> [args...]\n"
                     "       bridge-run.py --healthy <run id>\n")
    return 2


def head_of(argv):
    if not argv:
        return ""
    base = os.path.basename(argv[0]).lower()
    if base.endswith(".exe"):
        return base[:-4]
    if base.endswith(".cmd"):
        return base[:-4]
    return base


def is_agent_argv(argv):
    """True when argv[0] is a bare cursor-agent name (AGENT_NAMES), not a path or doubled suffix."""
    if not argv:
        return False
    if os.path.dirname(argv[0]):
        return False
    return argv[0].lower() in AGENT_NAMES


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
    if is_agent_argv(argv):
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
    if head_of(argv) == "cursor-agent":
        return kind_of(argv) is not None and (kind_of(argv) != "test" or test_suite(argv, folder))
    if kind_of(argv) is not None and (kind_of(argv) != "test" or test_suite(argv, folder)):
        return True
    return os.environ.get("BRIDGE_RUN_ALLOW_ANY") == "1"


def read_log(folder):
    return bridge_env.read_runs_jsonl(folder)


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
        with open(os.path.join(folder, "docs", "RUN_PARAMETERS.md"), encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"^\s*[-*]?\s*\**Ceiling above twice\**\s*:\s*(\w+)\s+(\d+)\s*\((.+)\)", line.strip(), re.I)
                if m and m.group(1).lower() == kind and m.group(3).strip():
                    try:
                        return int(m.group(2))
                    except ValueError:
                        continue
    except (OSError, UnicodeDecodeError, ValueError):
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
           'Design rounds above five: design.md, "The launcher holds the ceiling"' % (
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
    if not is_agent_argv(argv):
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


BRIEF_RULE_POINTER = 'workflow/phases/delegation-loop.md, "3. Delegate to Cursor"'


def git_common_dir(folder):
    try:
        p = subprocess.run(
            ["git", "-C", folder or ".", "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=NO_WINDOW,
            timeout=bridge_env.GIT_TIMEOUT,
        )
        if p.returncode != 0:
            return None
        gd = p.stdout.strip()
        if not os.path.isabs(gd):
            gd = os.path.normpath(os.path.join(os.path.abspath(folder or "."), gd))
        return gd
    except (OSError, subprocess.TimeoutExpired):
        return None


def roster_builder_model(folder):
    try:
        with open(os.path.join(folder, "docs", "ROSTER.resolved.json"), encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("builder"), str):
            return data["builder"]
    except (OSError, ValueError, RecursionError):
        pass
    return None


def prior_brief_run(folder, brief_name):
    for row in read_log(folder):
        if row.get("brief_name") == brief_name:
            return row
        bn = row.get("brief")
        rnd = row.get("round") or 1
        if bn:
            full = "%s-r%d" % (bn, rnd) if rnd > 1 else bn
            if full == brief_name or (rnd == 1 and bn == brief_name):
                return row
    return None


def prior_brief_run_same_sha(folder, brief_name, brief_sha):
    for row in read_log(folder):
        if row.get("brief_sha256") != brief_sha:
            continue
        if row.get("brief_name") == brief_name:
            return row
        bn = row.get("brief")
        rnd = row.get("round") or 1
        if bn:
            full = "%s-r%d" % (bn, rnd) if rnd > 1 else bn
            if full == brief_name or (rnd == 1 and bn == brief_name):
                return row
    return None


def completed_brief_run(folder, brief_name):
    row = prior_brief_run(folder, brief_name)
    if row and row.get("exit") == 0:
        return row
    for row in read_log(folder):
        if row.get("brief_name") == brief_name and row.get("exit") == 0:
            return row
        bn = row.get("brief")
        rnd = row.get("round") or 1
        if bn and row.get("exit") == 0:
            full = "%s-r%d" % (bn, rnd) if rnd > 1 else bn
            if full == brief_name or (rnd == 1 and bn == brief_name):
                return row
    return None


def review_launch_refusal(argv, folder):
    """Refuse a --kind review launch that names a brief or uses the builder model."""
    if not is_agent_argv(argv):
        return None
    builder = roster_builder_model(folder)
    model = model_of(argv)
    if builder and model == builder:
        return "review launch on the roster builder model (%s) is refused; Review B uses a reviewer model" % builder
    for token in bridge_env.handoff_brief_tokens(argv):
        if bridge_env.parse_review_name(token):
            return "a review launch must not name a brief (%s); only the launcher counts builder briefs" % token
    return None


def _ascii_refusal(msg):
    return msg.encode("ascii", "backslashreplace").decode("ascii")


def _brief_rule_refusal(msg):
    return _ascii_refusal("%s %s" % (msg, BRIEF_RULE_POINTER))


def builder_review_refusal(argv, folder, kind):
    """All review-ceiling and brief rules for a cursor-agent launch; None when allowed.
    Returns (reason, meta) where meta holds log fields when the launch may proceed."""
    if not is_agent_argv(argv):
        return None, None
    ws = workspace_of(argv, folder)
    common = git_common_dir(ws) or ""
    log_folder = folder
    id_rx = bridge_env.grammar_id_rx()
    owner_lifts = bridge_env.review_owner_lifts(folder)
    if kind == "review":
        reason = review_launch_refusal(argv, folder)
        return (_ascii_refusal(reason) if reason else None), None
    tokens = bridge_env.handoff_brief_tokens(argv)
    parsed = []
    for t in tokens:
        p = bridge_env.parse_review_name(t)
        if not p:
            return (_brief_rule_refusal("brief rule: %s is not a brief name; name exactly one" % t), None)
        parsed.append((t, p[0], p[1]))
    if not parsed:
        return (_brief_rule_refusal("brief rule: name exactly one"), None)
    if len(parsed) > 1:
        return (_brief_rule_refusal("brief rule: name only one brief, not %d (%s)" % (len(parsed), ", ".join(x[0] for x in parsed))), None)
    brief_name, id_part, name_round = parsed[0]
    brief_path = os.path.join(ws, "handoff", brief_name + ".md")
    if not os.path.isfile(brief_path):
        return (_brief_rule_refusal("brief rule: %s does not exist under %s" % (brief_name, ws)), None)
    try:
        brief_bytes = open(brief_path, "rb").read()
    except OSError:
        return (_brief_rule_refusal("brief rule: %s cannot be read" % brief_name), None)
    brief_sha = hashlib.sha256(brief_bytes).hexdigest()
    br = branch_of(ws)
    if br is None:
        return (_brief_rule_refusal("brief rule: builds run on a branch, not a folder outside git"), None)
    if br == "HEAD":
        return (_brief_rule_refusal("brief rule: builds run on a branch, not a detached HEAD"), None)
    if br == "main":
        return (_brief_rule_refusal("brief rule: builds run on a branch, not main"), None)
    prior = prior_brief_run_same_sha(folder, brief_name, brief_sha)
    prev = completed_brief_run(folder, brief_name)
    if prev and prev.get("brief_sha256") and prev["brief_sha256"] != brief_sha and prev.get("exit") == 0:
        return (
            "revised in place: write handoff/%s-r%d.md" % (id_part, name_round + 1),
            None,
        )
    brief_text = brief_bytes.decode("utf-8", errors="replace")
    merge_ids = bridge_env.merge_unit_ids(brief_text)
    if merge_ids is None and bridge_env.merge_unit_line_present(brief_text):
        return (_brief_rule_refusal("brief rule: Merge unit: line is not valid"), None)
    declared = frozenset(merge_ids) if merge_ids else frozenset((id_part,))
    plan_path = os.path.join(ws, "docs", "BUILD_PLAN.md")
    has_plan = os.path.isfile(plan_path)
    if merge_ids is not None:
        if not has_plan:
            return (_brief_rule_refusal("brief rule: Merge unit: cannot be checked without docs/BUILD_PLAN.md"), None)
        plan_ids = bridge_env.plan_increment_ids(ws)
        plan_id_rx = re.compile(bridge_env.PLAN_ID_PATTERN)
        scope_mu = None
        scope_path = os.path.join(ws, "run", "review", "SCOPE-%s.md" % id_part)
        if os.path.isfile(scope_path):
            try:
                scope_mu = bridge_env.merge_unit_ids(open(scope_path, encoding="utf-8", errors="replace").read())
            except OSError:
                scope_mu = None
        for mid in merge_ids:
            if scope_mu and mid == id_part and mid in scope_mu:
                continue
            if not plan_id_rx.fullmatch(mid) or mid not in plan_ids:
                return (_brief_rule_refusal("brief rule: %s is not an increment heading in docs/BUILD_PLAN.md" % mid), None)
    existing = bridge_env.branch_declared_ids(log_folder, common, ws, br, id_rx)
    if existing and existing < declared:
        return (
            _brief_rule_refusal(
                "brief rule: names more IDs than the branch's first brief: %s" % ", ".join(sorted(declared))
            ),
            None,
        )
    for mid in declared:
        ok, why = bridge_env.branch_allows_id(log_folder, common, ws, br, mid, owner_lifts, id_rx)
        if not ok:
            if isinstance(why, frozenset):
                return (_ascii_refusal("branch rule: %s is not on this branch (counted: %s)" % (mid, ", ".join(sorted(why)))), None)
            return (_ascii_refusal("branch rule: refused for %s" % mid), None)
    eff_round = bridge_env.launcher_effective_round(log_folder, br, id_part, name_round)
    if prior:
        eff_round = name_round
    lift = None
    lift_line = None
    class_used = set()
    for row in bridge_env.read_runs_jsonl(folder):
        if row.get("brief") == id_part and row.get("lift") == "class" and row.get("lift_line"):
            if row.get("slot") == "not free":
                continue
            class_used.add(row["lift_line"])
    blk = bridge_env.read_blocking_class_line(brief_text)
    owner_entry = owner_lifts.get(id_part)
    owner_cap = owner_entry[0] if owner_entry else bridge_env.REVIEW_ROUNDS
    if eff_round > bridge_env.REVIEW_ROUNDS:
        if eff_round <= owner_cap:
            lift, lift_line = "owner", owner_entry[1] if owner_entry else ""
        elif blk:
            line = blk[2]
            if line in class_used and not prior:
                return (_ascii_refusal("review ceiling: class line already used for %s" % id_part), None)
            lift, lift_line = "class", line
        else:
            return (
                _ascii_refusal(
                    "review ceiling: %s (id %s, branch %s, round %d, ceiling %d); lift with "
                    "Blocking class: <class> - <finding> in the brief or "
                    "Review rounds above the ceiling: <ID> <rounds> (<their words>, <date>) in docs/RUN_PARAMETERS.md"
                    % (brief_name, id_part, br, eff_round, bridge_env.REVIEW_ROUNDS)
                ),
                None,
            )
    meta = {
        "brief": id_part,
        "round": name_round,
        "brief_sha256": brief_sha,
        "brief_name": brief_name,
        "lift": lift,
        "lift_line": lift_line,
        "merge_ids": tuple(declared),
        "branch": br,
    }
    return None, meta


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
    if hit[0].get("slot") == "not free":
        sys.stderr.write("bridge-run: refused - a run that ended waiting for the slot cannot be marked healthy\n")
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
    if is_agent_argv(argv):
        return "cursor-agent"
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


def heavy_state_paths(env=None):
    """`(~/.cursor-bridge/heavy.lock, ~/.cursor-bridge/heavy.lock.holder)` from the launcher's environment."""
    home = bridge_env.real_home(env or os.environ)
    folder = os.path.join(home, ".cursor-bridge")
    return os.path.join(folder, "heavy.lock"), os.path.join(folder, "heavy.lock.holder")


def parse_slot_scale():
    """Test-only scale for slot waits; raises ValueError when set but invalid."""
    raw = os.environ.get("BRIDGE_RUN_SLOT_SCALE", "")
    if not raw:
        return 1.0
    value = float(raw)
    if not math.isfinite(value) or value <= 0 or value > 1:
        raise ValueError("must be a number with 0 < value <= 1 (got %r)" % raw)
    return value


def _plain_record_text(value):
    if not isinstance(value, str) or not value:
        return False
    for ch in value:
        if ord(ch) < 32 or ord(ch) == 127:
            return False
    return True


def process_alive(pid):
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.WaitForSingleObject.restype = wintypes.DWORD
        k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.CloseHandle.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        access = 0x1000 | 0x00100000
        handle = k.OpenProcess(access, False, int(pid))
        if not handle:
            return False
        try:
            if k.WaitForSingleObject(handle, 0) == 258:
                return True
            return False
        finally:
            k.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except (OSError, OverflowError, ValueError):
        return False
    try:
        with open("/proc/%d/stat" % pid, encoding="utf-8", errors="replace") as f:
            state = f.read().rsplit(")", 1)[-1].split()[0]
        return state != "Z"
    except (OSError, IndexError):
        return True


def process_creation_epoch(pid):
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.GetProcessTimes.restype = wintypes.BOOL
        k.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        k.CloseHandle.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = k.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return None

        class FILETIME(ctypes.Structure):
            _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

        created = FILETIME()
        if not k.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(FILETIME()),
                                 ctypes.byref(FILETIME()), ctypes.byref(FILETIME())):
            k.CloseHandle(handle)
            return None
        k.CloseHandle(handle)
        filetime = (int(created.dwHighDateTime) << 32) + int(created.dwLowDateTime)
        return filetime / 10000000.0 - 11644473600.0
    try:
        with open("/proc/%d/stat" % pid, encoding="utf-8", errors="replace") as f:
            stat = f.read()
        rest = stat.rsplit(")", 1)[-1].split()
        starttime = int(rest[19])
        boot = None
        with open("/proc/stat", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("btime "):
                    boot = int(line.split()[1])
                    break
        if boot is None:
            return None
        hz = os.sysconf("SC_CLK_TCK")
        return boot + starttime / hz
    except (OSError, ValueError, IndexError):
        return None


def _slot_start_epoch(start):
    if not isinstance(start, str) or not SLOT_START_RE.match(start) or not _plain_record_text(start):
        return None
    try:
        dt = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None
    if dt < SLOT_START_MIN:
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    if dt > now + datetime.timedelta(seconds=SLOT_CLOCK_SKEW):
        return None
    try:
        return dt.timestamp()
    except (OverflowError, OSError, ValueError):
        return None


def read_holder_record(holder_path):
    """A live holder record, or None when missing, stale or untrusted."""
    import stat
    flags = (os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
             | getattr(os, "O_BINARY", 0))
    try:
        fd = os.open(holder_path, flags)
    except OSError:
        return None
    try:
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                return None
            raw_b = os.read(fd, 4097)
            if len(raw_b) > 4096:
                return None
            raw = raw_b.decode("utf-8")
            data = json.loads(raw)
        except (OSError, ValueError, RecursionError, MemoryError, OverflowError):
            return None
        if not isinstance(data, dict):
            return None
        kind = data.get("kind")
        if not isinstance(kind, str) or kind not in KINDS or not _plain_record_text(kind):
            return None
        run_id = data.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id) or not _plain_record_text(run_id):
            return None
        start = data.get("start")
        if _slot_start_epoch(start) is None:
            return None
        pid = data.get("pid")
        if type(pid) is not int or pid < 1 or pid > PID_MAX:
            return None
        limit = data.get("limit")
        if type(limit) is not int or limit < 1 or limit > SLOT_LIMIT_MAX:
            return None
        created = data.get("created")
        if type(created) not in (int, float) or isinstance(created, bool):
            return None
        try:
            created_f = float(created)
        except (TypeError, ValueError, OverflowError):
            return None
        if not math.isfinite(created_f):
            return None
        try:
            actual = process_creation_epoch(pid)
        except (OverflowError, OSError, ValueError):
            return None
        if not process_alive(pid) or actual is None or abs(actual - created_f) > 0.01:
            return None
        return {"kind": kind, "run_id": run_id, "pid": pid, "created": created_f, "start": start, "limit": limit}
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def holder_end_time(record, grace):
    """UTC end time string for a live holder record plus grace."""
    try:
        start_epoch = _slot_start_epoch(record["start"])
        if start_epoch is None:
            return None
        end = datetime.datetime.fromtimestamp(start_epoch + int(record["limit"]) + int(grace), tz=datetime.timezone.utc)
        return end.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    except (OverflowError, OSError, ValueError):
        return None


def publish_holder_record(holder_path, record):
    folder = os.path.dirname(holder_path)
    import tempfile
    tmp = None
    try:
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, prefix=".heavy.holder.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(record, f)
        except OSError:
            try:
                os.close(fd)
            except OSError:
                pass
            raise
        for _ in range(5):
            try:
                os.replace(tmp, holder_path)
                return True
            except (OSError, PermissionError):
                time.sleep(0.02)
    except OSError:
        if tmp is not None:
            try:
                os.remove(tmp)
            except OSError:
                pass
        sys.stderr.write("bridge-run: note - could not publish the slot holder record\n")
        return False
    if tmp is not None:
        try:
            os.remove(tmp)
        except OSError:
            pass
    sys.stderr.write("bridge-run: note - could not publish the slot holder record\n")
    return False


def _try_lock_byte(fd):
    if sys.platform == "win32":
        import errno
        import msvcrt
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return True
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EDEADLOCK):
                return False
            raise
    import fcntl
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def _unlock_byte(fd):
    if sys.platform == "win32":
        import msvcrt
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        import fcntl
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass


def _waiting_line(record, grace):
    if record is None:
        return "bridge-run: waiting for the slot held by unknown\n"
    end = holder_end_time(record, grace)
    if end is None:
        return "bridge-run: waiting for the slot held by unknown\n"
    return ("bridge-run: waiting for the slot held by %s %s since %s, ends by %s\n"
            % (record["kind"], record["run_id"], record["start"], end))


def _slot_not_free_line(record, grace):
    if record is None:
        return "bridge-run: slot not free - held by unknown\n"
    end = holder_end_time(record, grace)
    if end is None:
        return "bridge-run: slot not free - held by unknown\n"
    return ("bridge-run: slot not free - held by %s %s since %s, ends by %s\n"
            % (record["kind"], record["run_id"], record["start"], end))


def _open_heavy_lock(lock_path, state_dir):
    if sys.platform == "win32":
        os.makedirs(state_dir, exist_ok=True)
        return os.open(lock_path, os.O_RDWR | os.O_CREAT)
    os.makedirs(state_dir, mode=0o700, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lock_path, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
    except OSError:
        pass
    return fd


def acquire_heavy_slot(kind, run_id, limit, scale):
    """Take the machine-wide heavy slot; return (lock_fd, waited_seconds) or None after printing exit 123."""
    lock_path, holder_path = heavy_state_paths()
    state_dir = os.path.dirname(lock_path)
    grace = SLOT_GRACE * scale
    report = max(0.001, SLOT_REPORT * scale)
    wait_mono = time.monotonic()
    wait_wall = time.time()
    provisional_wall = wait_wall + (SLOT_BUILDER_CAP + SLOT_GRACE) * scale
    own_floor_wall = wait_wall + KINDS[kind] * scale
    deadline_mono = wait_mono + (SLOT_BUILDER_CAP + SLOT_GRACE) * scale
    bound_wall = None
    last_report = 0.0
    last_live = None
    try:
        lock_fd = _open_heavy_lock(lock_path, state_dir)
    except OSError as exc:
        sys.stderr.write("bridge-run: refused - ~/.cursor-bridge/heavy.lock (%s)\n" % exc.__class__.__name__)
        return "refused"
    pub_limit = max(1, int(limit))
    while True:
        try:
            got_lock = _try_lock_byte(lock_fd)
        except OSError as exc:
            sys.stderr.write("bridge-run: refused - ~/.cursor-bridge/heavy.lock (%s)\n" % exc.__class__.__name__)
            try:
                os.close(lock_fd)
            except OSError:
                pass
            return "refused"
        if got_lock:
            waited = int(time.monotonic() - wait_mono)
            taken = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            created = process_creation_epoch(os.getpid())
            if created is None:
                sys.stderr.write("bridge-run: note - could not read this process creation time for the slot holder record\n")
            else:
                publish_holder_record(holder_path, {
                    "kind": kind, "run_id": run_id, "pid": os.getpid(),
                    "created": created, "start": taken, "limit": pub_limit,
                })
            sys.stderr.write("bridge-run: slot taken %s\n" % taken)
            sys.stderr.flush()
            return lock_fd, waited
        now_mono = time.monotonic()
        live = read_holder_record(holder_path)
        if live is not None:
            last_live = live
            if bound_wall is None:
                start_epoch = _slot_start_epoch(live["start"])
                if start_epoch is not None:
                    try:
                        end_epoch = start_epoch + live["limit"] + grace
                        bound_wall = min(provisional_wall, max(own_floor_wall, end_epoch))
                        deadline_mono = wait_mono + (bound_wall - wait_wall)
                    except (OverflowError, OSError, ValueError):
                        pass
        if now_mono > deadline_mono:
            sys.stderr.write(_slot_not_free_line(last_live, grace))
            sys.stderr.write("bridge-run: exit 123\n")
            sys.stderr.flush()
            try:
                os.close(lock_fd)
            except OSError:
                pass
            return None
        if last_report == 0.0 or now_mono - last_report >= report - 0.001:
            sys.stderr.write(_waiting_line(last_live, grace))
            sys.stderr.flush()
            last_report = now_mono
        time.sleep(1)


def branch_of(folder):
    """The checkout's branch at launch (the roster check matches a builder run to the branch under review)."""
    try:
        p = subprocess.run(
            ["git", "-C", folder or ".", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            creationflags=NO_WINDOW,
            timeout=bridge_env.GIT_TIMEOUT,
        )
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def workspace_of(argv, folder):
    """The folder a cursor-agent run works in: its `--workspace <path>` (a worktree builder, relative to
    the launch folder), else the launch folder; the run is logged under that folder's branch (2026.10.25a)."""
    if is_agent_argv(argv):
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
    if not is_agent_argv(argv) or not model:
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
    if is_agent_argv(argv):
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
    if "--key-file" in flags and is_agent_argv(cmd):
        sys.stderr.write("bridge-run: refused - a key file never goes to a cursor-agent run (the builder and the reviewer must not see a key)\n")
        return 125
    reason = design_ceiling(cmd, folder)
    if reason:
        sys.stderr.write("bridge-run: refused - %s\n" % reason)
        return 125
    brief_meta = None
    brief_recheck_path = None
    if head_of(cmd) == "cursor-agent":
        pre_kind = kind if kind is not None else (kind_of(cmd) or "builder")
        reason, brief_meta = builder_review_refusal(cmd, folder, pre_kind)
        if reason:
            sys.stderr.write("bridge-run: refused - %s\n" % reason)
            return 125
        if brief_meta is not None:
            ws = workspace_of(cmd, folder)
            brief_recheck_path = os.path.join(ws, "handoff", brief_meta["brief_name"] + ".md")
    if kind is None:
        kind = kind_of(cmd)
    if kind is None and os.environ.get("BRIDGE_RUN_ALLOW_ANY") == "1":
        kind = "test"                                        # the tests' own helpers
    if kind not in KINDS:
        sys.stderr.write("bridge-run: refused - unknown kind %r (builder, driver, review, watch, test)\n" % kind)
        return 125
    slot_scale = 1.0
    scale_raw = os.environ.get("BRIDGE_RUN_SLOT_SCALE", "")
    if os.environ.get("BRIDGE_RUN_ALLOW_ANY") == "1":
        try:
            slot_scale = parse_slot_scale()
        except ValueError as e:
            sys.stderr.write("bridge-run: refused - BRIDGE_RUN_SLOT_SCALE %s\n" % e)
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
    if scale_raw and os.environ.get("BRIDGE_RUN_ALLOW_ANY") != "1":
        sys.stderr.write("bridge-run: note - BRIDGE_RUN_SLOT_SCALE is ignored without BRIDGE_RUN_ALLOW_ANY=1\n")
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
    if kind == "review" and kind_of(cmd) is not None and not is_agent_argv(cmd):
        sys.stderr.write(REVIEW_ONLY_REFUSE)
        return 125
    if kind == "watch" and kind_of(cmd) != "watch":
        sys.stderr.write(WATCH_ONLY_REFUSE)
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
    log_branch = brief_meta.get("branch") if brief_meta else branch_of(workspace_of(cmd, folder))
    entry = {"id": run_id, "kind": kind, "head": head, "model": model_of(cmd), "branch": log_branch, "limit": int(limit), "seconds": None, "exit": None, "healthy": None}
    if brief_meta:
        entry.update(
            brief=brief_meta["brief"],
            round=brief_meta["round"],
            brief_sha256=brief_meta["brief_sha256"],
            brief_name=brief_meta["brief_name"],
            lift=brief_meta.get("lift"),
            merge_ids=list(brief_meta.get("merge_ids") or ()),
        )
        if brief_meta.get("lift_line"):
            entry["lift_line"] = brief_meta["lift_line"]
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

    if kind == "driver" and len(cmd) >= 2 and not verify_driver_program_abs(cmd[1], folder):
        sys.stderr.write(DRIVER_REFUSE)
        return 125

    slot_fd = None
    if kind in HEAVY_KINDS:
        slot_attempt = time.monotonic()
        slot_result = acquire_heavy_slot(kind, run_id, limit, slot_scale)
        if slot_result == "refused":
            return 125
        if slot_result is None:
            entry.update(waited=int(time.monotonic() - slot_attempt), seconds=0, exit=123, slot="not free", healthy=None)
            write_log(folder, entry)
            return 123
        slot_fd, entry["waited"] = slot_result[0], slot_result[1]

    if brief_meta is not None and slot_fd is not None:
        try:
            after_sha = hashlib.sha256(open(brief_recheck_path, "rb").read()).hexdigest()
        except OSError:
            after_sha = None
        if after_sha != brief_meta["brief_sha256"]:
            _unlock_byte(slot_fd)
            try:
                os.close(slot_fd)
            except OSError:
                pass
            sys.stderr.write(
                "bridge-run: refused - %s\n"
                % _brief_rule_refusal("brief rule: the brief changed while the launch waited for the slot")
            )
            return 125

    if kind == "driver" and len(cmd) >= 2 and not verify_driver_program_abs(cmd[1], folder):
        if slot_fd is not None:
            _unlock_byte(slot_fd)
            try:
                os.close(slot_fd)
            except OSError:
                pass
        sys.stderr.write(DRIVER_REFUSE)
        return 125

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
            if slot_fd is not None:
                _unlock_byte(slot_fd)
                try:
                    os.close(slot_fd)
                except OSError:
                    pass
            return 125
        if killer is None:
            killer = proc.kill
    else:
        try:
            proc = subprocess.Popen(cmd, env=env, preexec_fn=os.setsid, creationflags=NO_WINDOW)
        except OSError as e:
            sys.stderr.write("bridge-run: cannot start %s (%s)\n" % (cmd[0], e))
            if slot_fd is not None:
                _unlock_byte(slot_fd)
                try:
                    os.close(slot_fd)
                except OSError:
                    pass
            return 125
        killer = lambda: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)  # noqa: E731

    started = time.time()                                    # after the slot: the limit counts from here
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
