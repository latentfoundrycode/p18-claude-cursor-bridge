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

R-042 (TASK-032): REVIEW_ROUNDS, BLOCKING_CLASSES, the review name grammar, Blocking class and
Review rounds above the ceiling readers, plan headings, squash_merged_ids (Merge form first),
branch_declared_ids / branch_allows_id (launcher log plus guard rounds, lapse on main), and
handoff_brief_tokens live here for bridge-run.py and review-guard.py.

ASCII-only on purpose (cp1252 consoles). Writes nothing (read-only helpers except gh_empty_dir
and agent_home side effects used by stripped_env).
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

GIT_TIMEOUT = 30

REVIEW_ROUNDS = 3

BLOCKING_CLASSES = frozenset((
    "behaviour",
    "security",
    "data integrity",
    "safety mechanism",
    "failing test",
))

GRAMMAR_ID_PATTERN = r"[A-Z][A-Za-z0-9-]*"
PLAN_ID_PATTERN = r"TASK-\d{3,}[a-z]?"

_REVIEW_ROUND_SUFFIX = re.compile(r"-r([1-9][0-9]*)$")
_REVIEW_R_IN_ID = re.compile(r"-r[0-9]")
_REVIEW_ID_BODY = re.compile(r"^%s$" % GRAMMAR_ID_PATTERN)
_REVIEW_NAME_RX = re.compile(r"^([A-Z][A-Za-z0-9-]*?)(?:-r([1-9][0-9]*))?$")

REVIEW_LIFT_RE = re.compile(
    r"^\s*[-*]?\s*(?:\*\*(?i:Review rounds above the ceiling):\*\*|\*\*(?i:Review rounds above the ceiling)\*\*:|(?i:Review rounds above the ceiling):)\s*"
    r"([A-Z][A-Za-z0-9-]*)\s+([0-9]+)\s*\((.+)\)"
)

BLOCKING_CLASS_RE = re.compile(
    r"^\s*(?:[-*]\s+)?Blocking class:\s*([^-\n]+?)\s*-\s*(.+?)\s*$",
)

MERGE_UNIT_RE = re.compile(
    r"^\s*(?:[-*]\s+)?Merge unit:\s*((?:[A-Z][A-Za-z0-9-]*\s+)+[A-Z][A-Za-z0-9-]*)?\s*$",
)

DESIGN_PATH_NORM = re.compile(r"[/\\]+(?:\.[/\\]+)*")
DESIGN_MARK = re.compile(r"(?i)run/review/DESIGN-")
DESIGN_TOKEN_RE = re.compile(r"[^\s\"'`]+")
DESIGN_TRIM_BEFORE_SEP = re.compile(r"[. ]+(?=[/\\])")

HANDOFF_PATH_NORM = DESIGN_PATH_NORM
HANDOFF_MARK = re.compile(r"(?i)handoff/")
HANDOFF_TOKEN_RE = DESIGN_TOKEN_RE
HANDOFF_TRIM_BEFORE_SEP = DESIGN_TRIM_BEFORE_SEP
HANDOFF_REPORT_NAME = re.compile(
    r"(?:-r[1-9][0-9]*[a-z]-report|-r[1-9][0-9]*-report|[A-Z][A-Za-z0-9-]*-report)\.md$",
    re.I,
)
HANDOFF_RESOLUTION = re.compile(r"(?i)^RESOLUTION-")


def parse_review_name(name):
    """Read a review increment name: (id, round) or None when the grammar refuses."""
    if not name or not isinstance(name, str):
        return None
    if "\n" in name or "\r" in name:
        return None
    if re.search(r"-R[0-9]", name):
        return None
    m = _REVIEW_NAME_RX.fullmatch(name)
    if not m:
        return None
    id_part = m.group(1)
    if _REVIEW_R_IN_ID.search(id_part):
        return None
    try:
        round_n = int(m.group(2)) if m.group(2) else 1
    except ValueError:
        return None
    return id_part, round_n


def read_blocking_class_line(text):
    """The first well-formed `Blocking class:` line in text: (class, finding, full line) or None."""
    if not text:
        return None
    for line in text.splitlines():
        m = BLOCKING_CLASS_RE.match(line.strip())
        if not m:
            continue
        cls = m.group(1).strip()
        finding = m.group(2).strip()
        if cls not in BLOCKING_CLASSES or not finding:
            continue
        return cls, finding, line.strip()
    return None


def review_owner_lifts(folder):
    """{id: (max_round, line_text)} from the first well-formed owner's line per id."""
    lifts = {}
    path = os.path.join(folder, "docs", "RUN_PARAMETERS.md")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
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
        lifts[id_part] = (rounds, line.strip())
    return lifts


def plan_increment_ids(folder):
    """Increment headings from docs/BUILD_PLAN.md (plan-check HEAD_RX and TASK ID pattern)."""
    ids = set()
    path = os.path.join(folder, "docs", "BUILD_PLAN.md")
    if not os.path.isfile(path):
        return ids
    head_rx = re.compile(r"^###\s+(%s)\s*(?:[-:\u2014\u2013]+)?\s*(.*)$" % PLAN_ID_PATTERN)
    id_rx = re.compile(PLAN_ID_PATTERN)
    try:
        text = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return ids
    for line in text.splitlines():
        m = head_rx.match(line)
        if m and id_rx.fullmatch(m.group(1)):
            ids.add(m.group(1))
    return ids


def merge_unit_line_present(text):
    if not text:
        return False
    for line in text.splitlines():
        m = MERGE_UNIT_RE.match(line.strip())
        if m and m.group(1):
            return True
    return False


def merge_unit_ids(text):
    """IDs from a `Merge unit:` line in a brief, or None when no line or the line is invalid."""
    if not text:
        return None
    for line in text.splitlines():
        m = MERGE_UNIT_RE.match(line.strip())
        if not m or not m.group(1):
            continue
        ids = []
        for tok in m.group(1).split():
            bare = parse_review_name(tok)
            if bare is None or bare[1] != 1 or bare[0] != tok:
                return None
            ids.append(tok)
        return tuple(ids)
    return None


def _id_eq(a, b):
    """Compare increment IDs ignoring case but keeping a trailing letter."""
    if not a or not b:
        return False
    return a.lower() == b.lower()


def _ids_subset_merged(declared, merged):
    for did in declared:
        if not any(_id_eq(did, m) for m in merged):
            return False
    return True


def _branch_name_to_id(branch, id_rx):
    """Map a merge branch name to an ID when it matches id_rx (case-insensitive, letter kept)."""
    if re.match(r"^task-\d", branch, re.I):
        cand = "TASK-" + branch[5:]
        if id_rx.fullmatch(cand):
            return cand
    for cand in (branch, branch.upper()):
        if id_rx.fullmatch(cand):
            return cand
    if "-" in branch:
        parts = branch.split("-", 1)
        cand = parts[0].upper() + "-" + parts[1]
        if id_rx.fullmatch(cand):
            return cand
    return None


def _id_token_hyphen_and_digit(id_rx, tok):
    """True when tok fully matches id_rx and holds a hyphen and a digit (bare ID test for subject and parenthesis)."""
    return bool(id_rx.fullmatch(tok) and "-" in tok and any(ch.isdigit() for ch in tok))


def _subject_leading_ids(line, id_rx):
    subject_rx = re.compile(r"^\s*((?:%s[\s,:]*)+)" % id_rx.pattern)
    m = subject_rx.match(line)
    if not m:
        return ()
    chunk = m.group(1)
    pos = 0
    out = []
    while pos < len(chunk):
        while pos < len(chunk) and chunk[pos] in " \t,:;":
            pos += 1
        if pos >= len(chunk):
            break
        m_tok = re.match(id_rx.pattern, chunk[pos:])
        if not m_tok:
            break
        tok = m_tok.group(0)
        if not _id_token_hyphen_and_digit(id_rx, tok):
            break
        out.append(tok)
        pos += m_tok.end()
    return out


_PLAN_MERGE_RX = re.compile(
    r"^\s*Merge (?:pull request #\d+ from \S+?/|branch ')(task-\d{3,}[a-z]?)\b", re.I
)
_GRAMMAR_MERGE_RX = re.compile(r"^\s*Merge (?:pull request #\d+ from \S+?/|branch ')([a-z0-9-]+)\b", re.I)
def _trail_paren_inner(line):
    """Closing parenthesis at end of subject; linear in line length (round 1's trailing form, last match)."""
    rest = line.rstrip()
    m = re.search(r"\(#\d+\)$", rest)
    if m:
        rest = rest[: m.start()].rstrip()
    ver = re.search(r"[-\u2014\u2013]\s*v?[\w.]+\s*$", rest)
    if ver:
        rest = rest[: ver.start()].rstrip()
    if not rest.endswith(")"):
        return None
    open_i = rest.rfind("(")
    if open_i < 0:
        return None
    inner = rest[open_i + 1 : -1]
    if "(" in inner or ")" in inner:
        return None
    return inner


def _trail_subject_search(line):
    return _trail_paren_inner(line)
_TRAILER_LINE_TEMPLATE = r"^\s*(%s)(\s*,\s*%s)*\s*$"
_R_BARE_RX = re.compile(r"R-\d{3,}[a-z]?")


def _is_plan_id_rx(id_rx):
    return id_rx.pattern == PLAN_ID_PATTERN


def _parenthesis_bare_item(item, id_rx):
    """Bare parenthesis item: id_rx match with hyphen-and-digit rule, or R-nnn token."""
    if _id_token_hyphen_and_digit(id_rx, item):
        return "id"
    if _R_BARE_RX.fullmatch(item):
        return "r"
    return None


def _parenthesis_merged_ids(inner, id_rx, plan_style):
    """Closing parenthesis form: every comma-separated item must be a bare ID; else merge nothing."""
    items = [part.strip() for part in inner.split(",")]
    if not items or not all(items):
        return None
    for item in items:
        if _parenthesis_bare_item(item, id_rx) is None:
            return None
    out = set()
    for item in items:
        if plan_style and _R_BARE_RX.fullmatch(item):
            continue
        if id_rx.fullmatch(item) and _parenthesis_bare_item(item, id_rx) == "id":
            out.add(item)
    return out


def _grammar_merge_id(branch, id_rx):
    mapped = None
    if re.match(r"^task-\d", branch, re.I):
        bm = re.match(r"(task-\d{3,}[a-z]?)", branch, re.I)
        if bm:
            cand = "TASK-" + bm.group(1)[5:]
            if id_rx.fullmatch(cand):
                mapped = cand
    if mapped is None:
        mapped = _branch_name_to_id(branch, id_rx)
    return mapped


def _plan_merge_id(line, id_rx):
    m = _PLAN_MERGE_RX.match(line)
    if not m:
        return None
    cand = "TASK-" + m.group(1)[5:]
    return cand if id_rx.fullmatch(cand) else None


def squash_merged_ids_from_lines(lines, id_rx, plan_style=None):
    """Apply the four squash-subject forms to log lines (subject, trailer pairs). Returns a set of IDs."""
    if isinstance(id_rx, str):
        id_rx = re.compile(id_rx)
    if plan_style is None:
        plan_style = _is_plan_id_rx(id_rx)
    trailer_rx = re.compile(_TRAILER_LINE_TEMPLATE % (id_rx.pattern, id_rx.pattern))
    out = set()
    for line in lines:
        if plan_style:
            subs = _subject_leading_ids(line, id_rx)
            if subs:
                out.update(subs)
                continue
            mapped = _plan_merge_id(line, id_rx)
            if mapped:
                out.add(mapped)
                continue
            inner = _trail_subject_search(line)
            if inner is not None:
                ids = _parenthesis_merged_ids(inner, id_rx, True)
                if ids is not None:
                    out.update(ids)
                continue
        else:
            m = _GRAMMAR_MERGE_RX.match(line)
            if m:
                mapped = _grammar_merge_id(m.group(1), id_rx)
                if mapped:
                    out.add(mapped)
                continue
            subs = _subject_leading_ids(line, id_rx)
            if subs:
                out.update(subs)
                continue
            inner = _trail_subject_search(line)
            if inner is not None:
                ids = _parenthesis_merged_ids(inner, id_rx, False)
                if ids is not None:
                    out.update(ids)
                continue
        if trailer_rx.match(line):
            for tok in id_rx.findall(line):
                if id_rx.fullmatch(tok):
                    out.add(tok)
    return out


def squash_merged_ids(folder, id_rx, git_runner=None, ref="main"):
    """Squash subjects on ref that merged increments (plan pattern: subject before Merge; grammar: Merge first)."""
    if isinstance(id_rx, str):
        id_rx = re.compile(id_rx)
    plan_style = _is_plan_id_rx(id_rx)
    if git_runner is None:
        def git_runner(args):
            return subprocess.run(
                ["git", "-C", folder] + args,
                capture_output=True,
                creationflags=NO_WINDOW,
                timeout=GIT_TIMEOUT,
            )
    try:
        p = git_runner(["log", ref, "--format=%s%n%(trailers:key=Merges,valueonly)"])
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    raw = p.stdout
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace")
    else:
        text = raw
    return squash_merged_ids_from_lines(text.split("\n"), id_rx, plan_style=plan_style)


def branch_exists(folder, branch, git_runner=None):
    if not branch or branch == "main":
        return branch == "main"
    if git_runner is None:
        def git_runner(args):
            return subprocess.run(
                ["git", "-C", folder] + args,
                capture_output=True,
                creationflags=NO_WINDOW,
                timeout=GIT_TIMEOUT,
            )
    try:
        p = git_runner(["rev-parse", "--verify", "--quiet", "refs/heads/%s" % branch])
        return p.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return None


def norm_branch(branch):
    if not branch:
        return ""
    if branch.startswith("refs/heads/"):
        return branch[len("refs/heads/") :]
    return branch


def _valid_log_row(o):
    if not isinstance(o, dict):
        return False
    if o.get("branch") is not None and not isinstance(o.get("branch"), str):
        return False
    if o.get("brief") is not None and not isinstance(o.get("brief"), str):
        return False
    if o.get("round") is not None and (isinstance(o.get("round"), bool) or not isinstance(o.get("round"), int)):
        return False
    if o.get("exit") is not None and (isinstance(o.get("exit"), bool) or not isinstance(o.get("exit"), int)):
        return False
    mi = o.get("merge_ids")
    if mi is not None and (not isinstance(mi, list) or not all(isinstance(x, str) for x in mi)):
        return False
    return True


def read_runs_jsonl(log_folder):
    path = os.path.join(log_folder, "run", "launcher", "runs.jsonl")
    rows = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if _valid_log_row(o):
                    rows.append(o)
    except OSError:
        pass
    return rows


def launcher_log_folder(common, worktree_root):
    """Folder whose runs.jsonl the branch rule reads (launch folder or main checkout)."""
    return os.path.dirname(common) if common else worktree_root


def _valid_rounds_file(data):
    if not isinstance(data, dict):
        return False
    rounds = data.get("rounds")
    if rounds is None:
        return True
    if not isinstance(rounds, list):
        return False
    for r in rounds:
        if not isinstance(r, dict):
            return False
        rn = r.get("round")
        if rn is not None and (isinstance(rn, bool) or not isinstance(rn, int)):
            return False
        t = r.get("time")
        if t is not None and not isinstance(t, str):
            return False
    mi = data.get("merge_ids")
    if mi is not None and (not isinstance(mi, list) or not all(isinstance(x, str) for x in mi)):
        return False
    return True


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
            with open(os.path.join(bridge, name), encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if _valid_rounds_file(data):
            out[id_part] = data
    return out


def _event_time_launcher(row):
    rid = row.get("id")
    if not isinstance(rid, str):
        rid = ""
    m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", rid)
    return m.group(1) if m else rid


def declared_set_for_id(folder, id_part):
    """Declared ID set from the branch's first brief or a records subject's SCOPE file."""
    if id_part.startswith("STAGE-"):
        scope_names = ("SCOPE-%s.md" % id_part,)
    else:
        scope_names = ("SCOPE-%s.md" % id_part, "SCOPE-STAGE-%s.md" % id_part)
    for pat in ("%s.md" % id_part,):
        p = os.path.join(folder, "handoff", pat)
        if os.path.isfile(p):
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                break
            mu = merge_unit_ids(text)
            return frozenset(mu) if mu else frozenset((id_part,))
    for name in scope_names:
        scope = os.path.join(folder, "run", "review", name)
        if os.path.isfile(scope):
            try:
                text = open(scope, encoding="utf-8", errors="replace").read()
            except OSError:
                return frozenset((id_part,))
            mu = merge_unit_ids(text)
            if mu:
                return frozenset(mu)
    return frozenset((id_part,))


def _branch_events(log_folder, common, worktree_root):
    events = []
    for row in read_runs_jsonl(log_folder):
        br = norm_branch(row.get("branch") or "")
        if not br or not row.get("brief"):
            continue
        ids = row.get("merge_ids")
        if ids:
            decl = frozenset(ids)
        else:
            decl = frozenset((row.get("brief"),))
        events.append(
            {
                "branch": br,
                "ids": decl,
                "time": _event_time_launcher(row),
                "first_id": row.get("brief"),
            }
        )
    git_folder = worktree_root or log_folder
    for id_part, data in _read_rounds_files(common).items():
        merge_ids = data.get("merge_ids")
        if merge_ids:
            file_decl = frozenset(merge_ids)
        else:
            file_decl = declared_set_for_id(git_folder, id_part)
        for rnd in data.get("rounds") or []:
            if not isinstance(rnd, dict):
                continue
            br = norm_branch(rnd.get("branch") or "")
            if not br:
                continue
            events.append(
                {
                    "branch": br,
                    "ids": file_decl,
                    "time": rnd.get("time") or "",
                    "first_id": id_part,
                }
            )
    events.sort(key=lambda e: e.get("time") or "")
    return events


def _claim_lapsed(git_folder, branch, declared, id_rx, git_runner=None):
    merged = squash_merged_ids(git_folder, id_rx, git_runner=git_runner)
    if merged is None:
        return False
    if _ids_subset_merged(declared, merged):
        return True
    exists = branch_exists(git_folder, branch, git_runner=git_runner)
    if exists is None:
        return False
    return not exists


def _refactor_stage(branch):
    if not branch.startswith("refactor/"):
        return None
    stage = branch[len("refactor/"):]
    if not stage:
        return None
    return stage


def _refac_numbered_brief_id(id_part):
    if not isinstance(id_part, str):
        return False
    return re.fullmatch(r"REFAC-[0-9]+", id_part) is not None


def _refac_branch_snapshot_id(id_part, stage):
    if not isinstance(id_part, str) or not stage:
        return False
    if id_part != "REFAC-" + stage:
        return False
    return re.fullmatch(GRAMMAR_ID_PATTERN, id_part) is not None


def _declared_ids_all_refac(declared, branch):
    stage = _refactor_stage(branch)
    if stage is None:
        return False
    if not declared:
        return False
    for d in declared:
        if not (_refac_numbered_brief_id(d) or _refac_branch_snapshot_id(d, stage)):
            return False
    return True


def branch_declared_ids(log_folder, common, worktree_root, branch, id_rx, git_runner=None):
    """Active declared ID set on branch after lapse (R3)."""
    branch = norm_branch(branch)
    if branch == "main":
        return frozenset()
    git_folder = worktree_root or log_folder
    for ev in _branch_events(log_folder, common, worktree_root):
        if ev["branch"] != branch:
            continue
        declared = ev["ids"]
        if _claim_lapsed(git_folder, branch, declared, id_rx, git_runner=git_runner):
            continue
        return declared
    return frozenset()


def branch_allows_id(log_folder, common, worktree_root, branch, id_part, owner_lifts, id_rx, git_runner=None,
                     snapshot=False):
    branch = norm_branch(branch)
    if branch == "main":
        return False, "main"
    declared = branch_declared_ids(log_folder, common, worktree_root, branch, id_rx, git_runner=git_runner)
    git_folder = worktree_root or log_folder
    if not declared:
        return True, None
    if id_part in declared:
        return True, None
    stage = _refactor_stage(branch)
    if stage is not None and _declared_ids_all_refac(declared, branch):
        if snapshot:
            if _refac_branch_snapshot_id(id_part, stage):
                return True, None
        elif _refac_numbered_brief_id(id_part) or _refac_branch_snapshot_id(id_part, stage):
            return True, None
    if id_part in owner_lifts:
        return True, "owner"
    if _claim_lapsed(git_folder, branch, declared, id_rx, git_runner=git_runner):
        return True, "lapsed"
    return False, declared


def launcher_round_for_id(log_folder, branch, id_part):
    """Distinct completed brief names (exit 0) on branch for id_part from the launcher log only."""
    branch = norm_branch(branch)
    completed = set()
    for row in read_runs_jsonl(log_folder):
        if norm_branch(row.get("branch") or "") != branch:
            continue
        if row.get("brief") != id_part:
            continue
        if row.get("exit") != 0:
            continue
        rnd = row.get("round")
        if rnd is None:
            rnd = 1
        bn = row.get("brief_name")
        if not isinstance(bn, str):
            bn = id_part if rnd == 1 else "%s-r%d" % (id_part, rnd)
        name = bn
        completed.add(name)
    return completed


def launcher_effective_round(log_folder, branch, id_part, name_round):
    completed = launcher_round_for_id(log_folder, branch, id_part)
    return max(name_round, len(completed) + 1)


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


def grammar_id_rx():
    return re.compile(GRAMMAR_ID_PATTERN)
