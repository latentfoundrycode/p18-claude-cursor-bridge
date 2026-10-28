"""bridge_env: shared helpers for the bridge's programs that start cursor-agent.

- stripped_env(): the process environment with the owner's identity withheld (KP-032). It is
  the same recipe as cursor-agent.shim, kept here so every Python launcher of cursor-agent
  (bridge-run.py, roster-check.py's probe) applies it without going through the shell.
- agent_home(): the home folder every run gets instead of the owner's (KP-038): one link
  `.cursor` to the owner's real ~/.cursor and nothing else, so cursor-agent finds no
  ~/.claude/settings.json whose hooks it would import; the owner's other stores are no
  longer found by default (not out of reach: the run is the owner's account).
- rename_probe(): a write-and-rename through a scratch link beside the agent home, the
  operation cursor-agent's state writes need and that fails under some folders here.
- cursor_agent_launcher(): the argv prefix that starts cursor-agent the way Windows needs it
  (the .cmd launcher through cmd.exe), or the binary elsewhere.

ASCII-only on purpose (cp1252 consoles). Writes nothing but the empty gh folder and the
agent's home folder, %USERPROFILE%/.cursor-bridge/agent-home.
"""
import json
import os
import re
import shutil
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

TOKEN_VARS = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN",
              "GIT_ASKPASS", "SSH_ASKPASS")

# Every variable whose NAME looks like an account key is withheld as well (2026.10.04e): a
# builder, and a reviewer that may execute code, must not inherit the owner's paid keys from
# the Windows user environment. The same test, word for word, is in cursor-agent.shim.
# TOKEN and SECRET count only as whole words, singular or plural (HF_TOKEN, MODAL_TOKEN_ID,
# SFVF_SECRETS_PASSPHRASE; not TOKENIZERS_PARALLELISM); a store's unlock PASSPHRASE is a
# key; KEY only as API/ACCESS/PRIVATE key or a name ending in _KEY or _KEYS (not
# GIT_CONFIG_KEY_0, which the recipe itself sets). Cursor's own variables are kept.
SECRET_LIKE = re.compile(r"((^|_)TOKENS?(_|$)|(^|_)SECRETS?(_|$)|PASSWORD|PASSWD|PASSPHRASE|CREDENTIAL|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|_KEYS?$)")
KEEP_PREFIXES = ("CURSOR_", "GIT_CONFIG_KEY_")


def secret_like(name):
    u = name.upper()
    return bool(SECRET_LIKE.search(u)) and not u.startswith(KEEP_PREFIXES)


def gh_empty_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    return os.path.join(base, "cursor-bridge", "gh-empty")


class AgentHomeError(RuntimeError):
    """The home folder a run must get could not be prepared; the run must not start."""


def real_home(env):
    """The owner's profile folder as Windows names it."""
    return env.get("USERPROFILE") or os.path.expanduser("~")


def is_link(path):
    try:
        st = os.lstat(path)
    except OSError:
        return False
    return os.path.islink(path) or bool(getattr(st, "st_reparse_tag", 0))


def leads_to(link, target):
    """True when `link` is a link that resolves to `target` (not dangling, not elsewhere)."""
    try:
        return is_link(link) and os.path.samefile(link, target)
    except OSError:
        return False


def remove_link(link):
    """Remove `link` itself, never what it points at: a symbolic link (POSIX, or a Windows
    symbolic link) by unlink, a Windows junction by rmdir, which cannot remove a folder
    that has content."""
    if os.path.islink(link):
        os.unlink(link)
    else:
        os.rmdir(link)


def make_link(link, target):
    """A directory junction (Windows) or a symbolic link to `target`; the error text, or None."""
    if os.name == "nt":
        p = subprocess.run(["cmd", "/d", "/c", "mklink", "/J", link, target], capture_output=True, text=True, creationflags=NO_WINDOW)
        if not os.path.lexists(link):
            return (p.stdout + p.stderr).strip()[:200] or "mklink made nothing"
        return None
    try:
        os.symlink(target, link)
    except OSError as e:
        return str(e)
    return None


# Windows resolves its known folders (Local AppData, Documents, Desktop, ...) from USERPROFILE,
# and a program handed one that does not exist falls back to the current directory, the
# builder's checkout (reAngle's Workspace got a PowerShell cache folder that way, 2026-10-06).
SKELETON = (os.path.join("AppData", "Local"), os.path.join("AppData", "LocalLow"), os.path.join("AppData", "Roaming"),
            "Documents", "Desktop", "Downloads")


def agent_home(env=None, create=True, repair=False):
    """(path, problem) of the home folder a builder or reviewer run gets instead of the
    owner's (KP-038). It holds one thing: a link `.cursor` to the owner's real `~/.cursor`,
    the CLI's own account and state. So cursor-agent finds no `~/.claude/settings.json`
    whose hooks it would import (Cursor imports them by default, and under Git Bash it
    composes them as PowerShell and runs them with bash; the error denies every tool call),
    and the owner's `.ssh`, `.aws`, `.docker` and other stores are no longer found by
    default. `problem` is None when the folder is usable: the link exists, is a link, and
    leads to the owner's real `~/.cursor`. With create=False a missing link is a problem,
    not a task; with repair=True (the installer) a link that leads elsewhere or nowhere is
    removed, by itself and never through it, and made again. A plain folder in the link's
    place is never removed.

    The folder sits in the profile root, %USERPROFILE%/.cursor-bridge/agent-home, and not
    under %LOCALAPPDATA%: on the owner's computer a rename into a link placed under
    AppData/Local/<folder> fails with "path not found" (cursor-agent writes its state that
    way), while the same link in the profile root works (KP-038); rename_probe() checks it."""
    env = os.environ if env is None else env
    home = os.path.join(real_home(env), ".cursor-bridge", "agent-home")
    link = os.path.join(home, ".cursor")
    target = os.path.join(real_home(env), ".cursor")
    if os.path.lexists(link):
        if not is_link(link):
            return home, "%s is a plain folder, not a link to %s" % (link, target)
        if leads_to(link, target):
            if create:
                for rel in SKELETON:
                    try:
                        os.makedirs(os.path.join(home, rel), exist_ok=True)
                    except OSError:
                        pass
            return home, None
        if not repair:
            return home, "%s is a link that does not lead to %s" % (link, target)
        try:
            remove_link(link)
        except OSError as e:
            return home, "cannot remove the link %s (%s)" % (link, e)
    if not create:
        return home, "%s does not exist" % link
    try:
        os.makedirs(home, exist_ok=True)
        os.makedirs(target, exist_ok=True)
        for rel in SKELETON:
            os.makedirs(os.path.join(home, rel), exist_ok=True)
    except OSError as e:
        return home, "cannot prepare %s (%s)" % (home, e)
    err = make_link(link, target)
    if err:
        return home, "cannot link %s to %s (%s)" % (link, target, err)
    if not leads_to(link, target):
        return home, "%s was made but does not lead to %s" % (link, target)
    return home, None


def rename_probe(env=None):
    """A write-and-rename through a scratch link beside the agent home, cleaned up after:
    the operation cursor-agent's state writes need, which fails under some folders on the
    owner's computer (KP-038). Returns None when it works, else the error text. Never
    touches the owner's real ~/.cursor."""
    env = os.environ if env is None else env
    base = os.path.join(real_home(env), ".cursor-bridge")
    target = os.path.join(base, "probe-target")
    link = os.path.join(base, "probe-link")
    problem = None
    try:
        os.makedirs(target, exist_ok=True)
        if os.path.lexists(link):
            remove_link(link)
        err = make_link(link, target)
        if err:
            return "cannot make the probe link (%s)" % err
        tmp = os.path.join(link, "probe.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("{}\n")
        os.replace(tmp, os.path.join(link, "probe.json"))
    except OSError as e:
        problem = "a rename through a link beside the agent home fails here (KP-038): %s" % e
    for name in ("probe.tmp", "probe.json"):
        try:
            os.remove(os.path.join(target, name))
        except OSError:
            pass
    try:
        remove_link(link)
    except OSError:
        pass
    try:
        os.rmdir(target)
    except OSError:
        pass
    return problem


# the caches the builders' tools read by default under the home, passed through by their own
# variables; never HF_HOME or XDG_CACHE_HOME, which would show the owner's token file again
CACHES = (("HF_HUB_CACHE", os.path.join(".cache", "huggingface", "hub")),
          ("TORCH_HOME", os.path.join(".cache", "torch")),
          ("PUPPETEER_CACHE_DIR", os.path.join(".cache", "puppeteer")))


def write_gitconfig(real):
    """`<profile>/.cursor-bridge/gitconfig`: includes the owner's global git config when it
    exists and resets the credential helper list (an empty `helper =` resets it, as git
    documents), so a builder or reviewer run keeps the owner's identity and safe.directory
    entries and has no helper that could hand out the owner's GitHub login (2026.10.11c)."""
    base = os.path.join(real, ".cursor-bridge")
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, "gitconfig")
    owner = os.path.join(real, ".gitconfig")
    lines = ["# written by the Claude-Cursor Bridge before every builder or reviewer run; do not edit"]
    if os.path.isfile(owner):
        lines += ["[include]", "\tpath = " + owner.replace("\\", "/")]
    lines += ["[credential]", "\thelper ="]
    text = "\n".join(lines) + "\n"
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == text:
                return path
    except OSError:
        pass
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)                                  # published whole (KP-047)
    return path


def stripped_env(env=None):
    """Return a copy of `env` (default: os.environ) in which gh is logged out, no token
    variable and no variable named like an account key survives, git has no credential
    helper and never prompts, and the home folder is the agent's own (KP-038). Raises
    AgentHomeError when that folder cannot be prepared: the run must not start."""
    e = dict(os.environ if env is None else env)
    empty = gh_empty_dir()
    try:
        os.makedirs(empty, exist_ok=True)
    except OSError:
        pass
    e["GH_CONFIG_DIR"] = empty
    for k in TOKEN_VARS:
        e.pop(k, None)
    for k in [k for k in e if secret_like(k)]:
        e.pop(k, None)
    e["GIT_TERMINAL_PROMPT"] = "0"
    for k in ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"):
        e.pop(k, None)                                 # until 2026.10.11b an empty GIT_CONFIG_VALUE_0 reset the helper list; a wholesale environment restore on Windows drops an empty variable (reAngle ISS-016)
    # The run's own home folder (2026.10.06a, KP-038); git reads the bridge's own global
    # config file, which includes the owner's and resets the credential helper list.
    home, problem = agent_home(e)
    if problem:
        raise AgentHomeError("the agent's home folder is not usable: %s (KP-038)" % problem)
    real = real_home(e)
    e["HOME"] = e["USERPROFILE"] = home
    drive, rest = os.path.splitdrive(home)
    if drive:
        e["HOMEDRIVE"], e["HOMEPATH"] = drive, rest
    try:
        e["GIT_CONFIG_GLOBAL"] = write_gitconfig(real)
    except OSError as exc:
        raise AgentHomeError("the bridge's git config file cannot be written (%s); it resets the credential helper for the run" % exc)
    e["GIT_CONFIG_PARAMETERS"] = "'credential.helper='"   # read after the checkout's .git/config: a helper a builder writes there cannot re-enable the owner's login
    for var, rel in CACHES:
        if not e.get(var) and os.path.isdir(os.path.join(real, rel)):
            e[var] = os.path.join(real, rel)
    return e


def cursor_agent_launcher():
    """argv prefix for cursor-agent, or None when it cannot be found."""
    for cand in ("cursor-agent.cmd", "cursor-agent.exe", "cursor-agent"):
        found = shutil.which(cand)
        if found:
            break
    else:
        found = os.path.join(os.environ.get("LOCALAPPDATA", ""), "cursor-agent", "cursor-agent.cmd")
        if not os.path.isfile(found):
            return None
    if found.lower().endswith((".cmd", ".bat")):
        return ["cmd.exe", "/d", "/c", found]
    if not found.lower().endswith(".exe") and os.name == "nt":
        # the Git-Bash shim is a shell script; CreateProcess cannot run it, use the .cmd beside it
        cmd = os.path.join(os.path.dirname(found), "cursor-agent.cmd")
        if os.path.isfile(cmd):
            return ["cmd.exe", "/d", "/c", cmd]
    return [found]


# --- code-review round ceiling (R-042, TASK-032); imported by bridge-run.py and review-guard.py ---

REVIEW_ROUNDS = 3

BLOCKING_CLASSES = frozenset((
    "behaviour",
    "security",
    "data integrity",
    "safety mechanism",
    "failing test",
))

_REVIEW_ROUND_SUFFIX = re.compile(r"-r([1-9][0-9]*)$")
_REVIEW_R_IN_ID = re.compile(r"-r[0-9]")
_REVIEW_ID_BODY = re.compile(r"^[A-Z][A-Za-z0-9-]*$")

REVIEW_LIFT_RE = re.compile(
    r"^\s*[-*]?\s*(?:\*\*(?i:Review rounds above the ceiling):\*\*|\*\*(?i:Review rounds above the ceiling)\*\*:|(?i:Review rounds above the ceiling):)\s*"
    r"([A-Z][A-Za-z0-9-]*)\s+([0-9]+)\s*\((.+)\)"
)

BLOCKING_CLASS_RE = re.compile(
    r"^\s*(?:[-*]\s+)?Blocking class:\s*([^-\n]+?)\s*-\s*(.+?)\s*$",
    re.I,
)

MERGE_UNIT_RE = re.compile(
    r"^\s*(?:[-*]\s+)?Merge unit:\s*((?:[A-Z][A-Za-z0-9-]*\s+)+[A-Z][A-Za-z0-9-]*)\s*$",
    re.I,
)

HANDOFF_PATH_NORM = re.compile(r"[/\\]+(?:\.[/\\]+)*")
HANDOFF_MARK = re.compile(r"(?i)handoff/")
HANDOFF_TOKEN_RE = re.compile(r"[^\s\"'`]+")
HANDOFF_TRIM_BEFORE_SEP = re.compile(r"[. ]+(?=[/\\])")
HANDOFF_REPORT_NAME = re.compile(r"-r[1-9][0-9]*-report\.md$", re.I)
HANDOFF_RESOLUTION = re.compile(r"(?i)^RESOLUTION-")


def parse_review_name(name):
    """Read a review increment name: (id, round) or None when the grammar refuses."""
    if not name or not isinstance(name, str):
        return None
    if " " in name or "/" in name or "\\" in name:
        return None
    if re.search(r"-R[0-9]", name) or re.search(r"-r0(?:\D|$)", name):
        return None
    m = _REVIEW_ROUND_SUFFIX.search(name)
    if m:
        id_part = name[: m.start()]
        try:
            round_n = int(m.group(1))
        except ValueError:
            return None
    else:
        id_part = name
        round_n = 1
    if not id_part or not _REVIEW_ID_BODY.match(id_part):
        return None
    if _REVIEW_R_IN_ID.search(id_part):
        return None
    return id_part, round_n


def read_blocking_class_line(text):
    """The first `Blocking class:` line in text: (class, finding, full line) or None."""
    if not text:
        return None
    for line in text.splitlines():
        m = BLOCKING_CLASS_RE.match(line.strip())
        if not m:
            continue
        cls = m.group(1).strip().lower()
        finding = m.group(2).strip()
        if cls not in BLOCKING_CLASSES or not finding:
            return None
        return cls, finding, line.strip()
    return None


def review_owner_lifts(folder):
    """{id: max round} from the first well-formed owner's line per id in docs/RUN_PARAMETERS.md."""
    lifts = {}
    path = os.path.join(folder, "docs", "RUN_PARAMETERS.md")
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return lifts
    for line in lines:
        m = REVIEW_LIFT_RE.match(line.strip())
        if not m:
            continue
        id_part = m.group(1)
        if id_part in lifts:
            continue
        words = m.group(3).strip()
        if not words:
            continue
        try:
            rounds = int(m.group(2))
        except ValueError:
            continue
        if rounds <= REVIEW_ROUNDS:
            continue
        lifts[id_part] = rounds
    return lifts


def plan_increment_ids(folder):
    """Increment headings from docs/BUILD_PLAN.md (same shape as plan-check.py's parse)."""
    ids = set()
    paths = []
    for name in ("docs/BUILD_PLAN.md",):
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            paths.append(p)
    id_pat = re.compile(r"^[A-Z][A-Za-z0-9-]*$")
    head_rx = re.compile(r"^###\s+([A-Z][A-Za-z0-9-]*)\s*(?:[-:—–]+)?\s*(.*)$")
    for path in paths:
        try:
            text = open(path, encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        for line in text.splitlines():
            m = head_rx.match(line)
            if m and id_pat.match(m.group(1)):
                ids.add(m.group(1))
    return ids


def merge_unit_ids(text):
    """IDs from a `Merge unit:` line in a brief, or None."""
    if not text:
        return None
    for line in text.splitlines():
        m = MERGE_UNIT_RE.match(line.strip())
        if m:
            return tuple(m.group(1).split())
    return None


def squash_merged_ids(base, id_rx):
    """Squash subjects on main that merged increments, parameterized by id_rx (plan-check's four forms)."""
    p = subprocess.run(
        ["git", "log", base, "--format=%s%n%(trailers:key=Merges,valueonly)"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=NO_WINDOW,
    )
    if p.returncode != 0:
        return set()
    subject_rx = re.compile(r"^\s*((?:%s[\s,:]*)+)" % id_rx.pattern)
    trail_rx = re.compile(
        r"\(([^()]*%s[^()]*)\)\s*(?:[-\u2014\u2013]\s*v?[\w.]+\s*)?(?:\(#\d+\))?\s*$" % id_rx.pattern
    )
    merge_rx = re.compile(r"^\s*Merge (?:pull request #\d+ from \S+?/|branch ')([a-z0-9-]+)\b", re.I)
    out = set()
    for line in p.stdout.splitlines():
        m = subject_rx.match(line)
        if m:
            out.update(id_rx.findall(m.group(1)))
            continue
        m = merge_rx.match(line)
        if m:
            branch = m.group(1)
            if "-" in branch:
                out.add(branch.split("-", 1)[0].upper() + "-" + branch.split("-", 1)[1])
            else:
                out.add(branch.upper())
            continue
        m = trail_rx.search(line)
        if m:
            out.update(id_rx.findall(m.group(1)))
            continue
        if re.match(r"^\s*(%s)(\s*,\s*%s)*\s*$" % (id_rx.pattern, id_rx.pattern), line):
            out.update(id_rx.findall(line))
    return out


def _norm_branch(branch):
    if not branch:
        return ""
    if branch.startswith("refs/heads/"):
        return branch[len("refs/heads/") :]
    return branch


def _read_runs_jsonl(folder):
    path = os.path.join(folder, "run", "launcher", "runs.jsonl")
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if isinstance(o, dict):
                    rows.append(o)
    except OSError:
        pass
    return rows


def _read_rounds_files(common):
    out = {}
    bridge = os.path.join(common, "bridge")
    if not os.path.isdir(bridge):
        return out
    for name in os.listdir(bridge):
        if not name.startswith("rounds-") or not name.endswith(".json"):
            continue
        id_part = name[len("rounds-") : -len(".json")]
        try:
            with open(os.path.join(bridge, name), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            out[id_part] = data
    return out


def _branch_events(folder, common):
    """Chronological branch claims from launcher log and guard rounds records."""
    events = []
    for row in _read_runs_jsonl(folder):
        br = row.get("branch")
        if not br or not row.get("brief"):
            continue
        events.append(
            {
                "branch": _norm_branch(br),
                "ids": row.get("merge_ids") or (row.get("brief"),),
                "source": "launcher",
                "id": row.get("id"),
            }
        )
    for id_part, data in _read_rounds_files(common).items():
        for rnd in data.get("rounds") or []:
            br = _norm_branch(rnd.get("branch") or "")
            if br:
                events.append(
                    {
                        "branch": br,
                        "ids": data.get("merge_ids") or (id_part,),
                        "source": "guard",
                        "name": rnd.get("name"),
                    }
                )
    return events


def branch_declared_ids(folder, common, branch):
    """The ID set the branch's first brief or snapshot declared."""
    branch = _norm_branch(branch)
    for ev in _branch_events(folder, common):
        if ev["branch"] == branch:
            return frozenset(ev["ids"])
    return frozenset()


def ids_lapsed_on_main(folder, id_rx):
    merged = squash_merged_ids("main", id_rx)
    return frozenset(merged)


def branch_allows_id(folder, common, branch, id_part, owner_lifts, id_rx):
    """Whether id_part may run on branch (owner lift for outside ids; lapse on main merge)."""
    branch = _norm_branch(branch)
    if branch == "main":
        return False, "main"
    declared = branch_declared_ids(folder, common, branch)
    if not declared:
        return True, None
    if id_part in declared:
        return True, None
    if id_part in owner_lifts:
        return True, "owner"
    lapsed = ids_lapsed_on_main(folder, id_rx)
    if declared <= lapsed:
        return True, "lapsed"
    return False, declared


def handoff_brief_tokens(argv):
    """Brief file tokens found in argv (normalised paths), excluding resolution and report names."""
    text = HANDOFF_TRIM_BEFORE_SEP.sub("", " ".join(argv))
    norm = HANDOFF_PATH_NORM.sub("/", text)
    out = []
    for m in HANDOFF_MARK.finditer(norm):
        tm = HANDOFF_TOKEN_RE.match(norm, m.end())
        if not tm:
            continue
        token = tm.group(0).rstrip(".,;:)])}'\"")
        if not token.lower().endswith(".md"):
            continue
        base = token.rsplit("/", 1)[-1]
        if base.lower().endswith(".md"):
            base = base[:-3]
        if HANDOFF_RESOLUTION.match(base):
            continue
        if HANDOFF_REPORT_NAME.search(token):
            continue
        out.append(base)
    return out


def launcher_round_for_id(folder, common, branch, id_part):
    """Distinct completed brief names (id+round) on branch for id_part, plus next round logic."""
    branch = _norm_branch(branch)
    completed = set()
    for row in _read_runs_jsonl(folder):
        if _norm_branch(row.get("branch") or "") != branch:
            continue
        if row.get("brief") != id_part:
            continue
        if row.get("exit") != 0:
            continue
        rnd = row.get("round")
        if rnd is None:
            rnd = 1
        completed.add((id_part, rnd))
    for data in _read_rounds_files(common).values():
        for rnd in data.get("rounds") or []:
            if _norm_branch(rnd.get("branch") or "") != branch:
                continue
            parsed = parse_review_name(rnd.get("name") or "")
            if not parsed:
                continue
            rid, rn = parsed
            if rid != id_part:
                continue
            if rnd.get("reply") is not None:
                completed.add((rid, rn))
    return completed


def effective_launcher_round(folder, common, branch, id_part, name_round):
    completed = launcher_round_for_id(folder, common, branch, id_part)
    return max(name_round, len(completed) + 1)


def grammar_id_rx():
    return re.compile(r"[A-Z][A-Za-z0-9-]*")
