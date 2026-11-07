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

R-057 (TASK-046): read_header, HeaderError, HEADER_SCHEMAS, check_header and header_agrees
(the YAML front-matter reader and schema data programs will import in later increments).

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


# --- R-057 header reader, schemas, check and agreement (TASK-046) ---

_HEADER_BYTE_BOUND = 262144
_HEADER_DEPTH_BOUND = 8

_PLAIN_TYPED_WORDS = frozenset(
    ("yes", "no", "on", "off", "y", "n", "true", "false", "null", "~")
)

_PLAIN_WORD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")

_KINDS = (
    "project-status", "build-plan", "brief", "inventory", "requirements",
    "diagram-index", "deviations", "run-parameters",
)

_REQ_STATUSES = ("planned", "built", "deferred", "dropped")

_NOTHING = ("nothing", "none", "-", "")


class HeaderError(Exception):
    """A header block the subset refuses; .line is the 1-based line in the whole text."""

    def __init__(self, line, message):
        self.line = line
        super().__init__(message)


HEADER_SCHEMAS = {
    "project-status": {
        "record": "enum of project-status, build-plan, brief, inventory, requirements, diagram-index, deviations, run-parameters",
        "header": "integer",
        "phase": "enum of intake, design, mockups, interface, planning, configuration, configuring, configure, building, done, changing",
        "workflows": "list of WorkflowPart",
        "awaiting_user_on": "string",
        "bridge_version": "string",
        "stage": "string",
        "open_issues": "list of string",
    },
    "WorkflowPart": {
        "type": "string",
        "subtype": "string or null",
        "traits": "list of string",
    },
    "build-plan": {
        "record": "enum of project-status, build-plan, brief, inventory, requirements, diagram-index, deviations, run-parameters",
        "header": "integer",
        "stages": "list of Stage",
    },
    "Stage": {
        "name": "string",
        "demonstration": "boolean",
        "increments": "list of Increment",
    },
    "Increment": {
        "id": "string",
        "title": "string",
        "kind": "enum of increment, group",
        "parent": "string or null",
        "depends_on": "list of string",
        "parallel": "boolean",
        "diagrams": "list of string",
        "scope": "list of string",
        "satisfies": "list of string",
        "deferred": "string or null",
        "historic": "boolean",
    },
    "brief": {
        "record": "enum of project-status, build-plan, brief, inventory, requirements, diagram-index, deviations, run-parameters",
        "header": "integer",
        "id": "string",
        "round": "integer",
        "satisfies": "list of string",
        "scope": "list of string",
        "merge_unit": "list of string or null",
        "blocking_class": "enum of behaviour, security, data integrity, safety mechanism, failing test or null",
    },
    "inventory": {
        "record": "enum of project-status, build-plan, brief, inventory, requirements, diagram-index, deviations, run-parameters",
        "header": "integer",
        "reflected_through": "string or null",
        "development_data": "string",
        "tables": "InventoryTables",
    },
    "InventoryTables": {
        "features": "TableShape",
        "resources": "TableShape",
        "decisions": "TableShape",
        "deferred": "TableShape",
    },
    "TableShape": {
        "columns": "list of string",
        "key": "string",
    },
    "requirements": {
        "record": "enum of project-status, build-plan, brief, inventory, requirements, diagram-index, deviations, run-parameters",
        "header": "integer",
        "columns": "list of string",
        "roles": "RequirementsRoles",
        "statuses": "list of enum of planned, built, deferred, dropped",
    },
    "RequirementsRoles": {
        "id": "string",
        "status": "string",
        "evidence": "string",
    },
    "diagram-index": {
        "record": "enum of project-status, build-plan, brief, inventory, requirements, diagram-index, deviations, run-parameters",
        "header": "integer",
        "columns": "list of string",
        "roles": "DiagramIndexRoles",
    },
    "DiagramIndexRoles": {
        "id": "string",
        "level": "string",
        "kind": "string",
        "status": "string",
        "file": "string",
        "refines": "string",
        "realizes": "string",
        "enforced_by": "string",
        "why": "string",
    },
    "deviations": {
        "record": "enum of project-status, build-plan, brief, inventory, requirements, diagram-index, deviations, run-parameters",
        "header": "integer",
        "columns": "list of string",
        "roles": "DeviationsRoles",
    },
    "DeviationsRoles": {
        "diagram": "string",
        "from": "string",
        "to": "string",
        "as_built": "string",
        "since": "string",
        "resolved_by": "string",
    },
    "run-parameters": {
        "record": "enum of project-status, build-plan, brief, inventory, requirements, diagram-index, deviations, run-parameters",
        "header": "integer",
        "stage_pause": "string",
        "merge_authority": "string",
        "refactoring_pass": "string",
        "installer_verification": "string",
        "parallel_increments": "string",
        "agent_ceiling": "integer or null",
        "ceiling_above_twice": "list of CeilingLift",
        "design_rounds_above_five": "list of DesignLift",
        "review_rounds_above_ceiling": "list of ReviewLift",
    },
    "CeilingLift": {
        "kind": "string",
        "seconds": "integer",
        "words": "string",
    },
    "DesignLift": {
        "subject": "string",
        "rounds": "integer",
        "words": "string",
        "date": "string",
    },
    "ReviewLift": {
        "id": "string",
        "rounds": "integer",
        "words": "string",
        "date": "string",
    },
}


def _header_refuse(line, msg):
    raise HeaderError(line, "line %d: %s" % (line, msg))


def _line_end_len(text, pos):
    if pos < len(text) and text[pos] == "\r":
        if pos + 1 < len(text) and text[pos + 1] == "\n":
            return 2
        return 0
    if pos < len(text) and text[pos] == "\n":
        return 1
    return 0


def _split_physical_lines(text):
    """(line_no, content, end) where line_no is 1-based; content excludes line ending."""
    out = []
    i, start, line_no = 0, 0, 1
    n = len(text)
    while i < n:
        el = _line_end_len(text, i)
        if el:
            out.append((line_no, text[start:i], text[start:i + el]))
            line_no += 1
            i += el
            start = i
        else:
            i += 1
    if start < n:
        out.append((line_no, text[start:n], text[start:n]))
    return out


_CLOSE_BLOCK = re.compile(r"(?:\r\n|\n)---(?:\r\n|\n|$)")


def _find_block(text):
    """Return (block_text, body, block_start_line) or (None, whole, None)."""
    whole = text
    if text.startswith("\ufeff"):
        text = text[1:]
    if len(text) < 3 or text[:3] != "---":
        return None, whole, None
    el0 = _line_end_len(text, 3)
    if len(text) > 3 and not el0:
        return None, whole, None
    base_line = 1
    start = 3 + el0
    if text.startswith("---", start):
        el1 = _line_end_len(text, start + 3)
        if el1:
            block = ""
            body = text[start + 3 + el1:]
            return block, body, base_line
    close_m = _CLOSE_BLOCK.search(text, start)
    if not close_m:
        _header_refuse(base_line, "unterminated header block")
    prefix = close_m.group(0)
    cut = close_m.start() + prefix.index("---")
    block = text[start:cut]
    body = text[close_m.end():]
    return block, body, base_line


def _is_refused_char(c, in_string_or_comment=False):
    o = ord(c)
    if o == 0x09 or o == 0x0C:
        return True
    if o == 0x0D:
        return True
    if o < 0x20:
        return True
    if o == 0x7F:
        return True
    if 0x80 <= o <= 0x9F or o == 0x85:
        return True
    if o in (0x2028, 0x2029, 0xFFFE, 0xFFFF):
        return True
    if 0xD800 <= o <= 0xDFFF:
        return True
    if o > 0x7F and not in_string_or_comment:
        return True
    return False


def _scan_line_characters(raw, line_no):
    in_str = in_comment = False
    j, n = 0, len(raw)
    while j < n:
        c = raw[j]
        if in_comment:
            if _is_refused_char(c, True):
                _header_refuse(line_no, "refused character")
            j += 1
            continue
        if in_str:
            if c == "\\":
                if j + 1 < n and _is_refused_char(raw[j + 1], True):
                    _header_refuse(line_no, "refused character")
                j += 2
                continue
            if c == '"':
                if j + 1 < n and raw[j + 1] == '"':
                    _header_refuse(line_no, "plain scalar; double-quote it")
                in_str = False
                j += 1
                continue
            if _is_refused_char(c, True):
                _header_refuse(line_no, "refused character")
            j += 1
            continue
        if c == '"':
            in_str = True
            j += 1
            continue
        if c == "#" and (j == 0 or raw[j - 1] == " "):
            in_comment = True
            j += 1
            continue
        if c == "\r":
            if j + 1 < n and raw[j + 1] == "\n":
                j += 2
                continue
            _header_refuse(line_no, "lone carriage return")
        if _is_refused_char(c, False):
            _header_refuse(line_no, "refused character")
        j += 1


def _scan_block_characters(block, first_line):
    for line_no, content, _end in _split_physical_lines(block):
        _scan_line_characters(content, first_line + line_no - 1)


def _dq_end_in_line(raw, start, line_no):
    i = start + 1
    n = len(raw)
    while i < n:
        c = raw[i]
        if c == "\\":
            if i + 1 >= n:
                _header_refuse(line_no, "unterminated quoted string")
            i += 2
            continue
        if c == '"':
            if i + 1 < n and raw[i + 1] == '"':
                _header_refuse(line_no, "plain scalar; double-quote it")
            return i + 1
        i += 1
    _header_refuse(line_no, "unterminated quoted string")


def _split_line_parts(raw, line_no):
    i, n = 0, len(raw)
    while i < n and raw[i] == " ":
        i += 1
    if i < n and raw[i] == "\t":
        _header_refuse(line_no, "tab")
    indent = i
    code_start = i
    in_str = False
    code_end = n
    j = i
    while j < n:
        c = raw[j]
        if in_str:
            if c == "\\":
                if j + 1 >= n:
                    _header_refuse(line_no, "unterminated quoted string")
                j += 2
                continue
            if c == '"':
                if j + 1 < n and raw[j + 1] == '"':
                    _header_refuse(line_no, "plain scalar; double-quote it")
                in_str = False
                j += 1
                continue
            j += 1
            continue
        if c == '"':
            in_str = True
            j += 1
            continue
        if c == "#" and (j == code_start or raw[j - 1] == " "):
            code_end = j
            while code_end > code_start and raw[code_end - 1] == " ":
                code_end -= 1
            break
        j += 1
    if in_str:
        _header_refuse(line_no, "unterminated quoted string")
    return indent, raw[code_start:code_end]


def _code_outside_quotes(code, line_no):
    out, i, n = [], 0, len(code)
    while i < n:
        if code[i] == '"':
            i = _dq_end_in_line(code, i, line_no)
            continue
        out.append(code[i])
        i += 1
    return "".join(out)


def _structural_guards(code, line_no):
    bare = _code_outside_quotes(code, line_no)
    if re.search(r"(^|\s)&\w", bare):
        _header_refuse(line_no, "anchor not allowed")
    if re.search(r"(^|\s)\*\w+", bare):
        _header_refuse(line_no, "alias not allowed")
    if re.search(r"(^|\s)!!", bare):
        _header_refuse(line_no, "tag not allowed")
    if "{" in bare:
        ib = bare.index("{")
        if ":" in bare[ib:]:
            _header_refuse(line_no, "flow mapping not allowed")
    if "[[" in bare and '"' not in code:
        _header_refuse(line_no, "flow list in flow list not allowed")
    stripped = bare.lstrip(" ")
    if re.fullmatch(r"[|>]\s*", stripped) or re.search(r":\s*[|>]\s*$", bare):
        _header_refuse(line_no, "block scalar not allowed")


def _valid_key(name):
    if len(name) > 1024:
        return False
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name or ""):
        return False
    if name.lower() in _PLAIN_TYPED_WORDS:
        return False
    return True


def _parse_double_quoted(s, line):
    if not s.startswith('"'):
        _header_refuse(line, "expected double-quoted string")
    i = 1
    out = []
    while i < len(s):
        c = s[i]
        if c == '"':
            if i + 1 != len(s):
                _header_refuse(line, "text after closing quote")
            return "".join(out)
        if c == "\\":
            if i + 1 >= len(s):
                _header_refuse(line, "bad escape in quoted string")
            nxt = s[i + 1]
            if nxt == '"':
                out.append('"')
                i += 2
                continue
            if nxt == "\\":
                out.append("\\")
                i += 2
                continue
            _header_refuse(line, "bad escape in quoted string")
        out.append(c)
        i += 1
    _header_refuse(line, "unterminated quoted string")


def _parse_flow_list(rest, line):
    rest = rest.strip(" ")
    if not rest.startswith("[") or not rest.endswith("]"):
        _header_refuse(line, "bad flow list")
    inner = rest[1:-1].strip(" ")
    if not inner:
        return []
    items = []
    i = 0
    n = len(inner)
    while i < n:
        while i < n and inner[i] == " ":
            i += 1
        if i >= n:
            break
        if inner[i] == ",":
            _header_refuse(line, "bad flow list")
        if inner[i] == '"':
            end = _dq_end_in_line(inner, i, line)
            token = inner[i:end]
            items.append(_parse_double_quoted(token, line))
            i = end
        else:
            j = i
            while j < n and inner[j] != ",":
                j += 1
            token = inner[i:j].strip(" ")
            items.append(_parse_scalar_token(token, line, flow_item=True))
            i = j
        while i < n and inner[i] == " ":
            i += 1
        if i < n:
            if inner[i] != ",":
                _header_refuse(line, "bad flow list")
            i += 1
    if inner.rstrip(" ").endswith(","):
        _header_refuse(line, "bad flow list")
    return items


def _parse_scalar_token(token, line, flow_item=False):
    if token == "":
        return None
    if token == '""':
        return ""
    if token == "true":
        return True
    if token == "false":
        return False
    if token == "null":
        return None
    if token.startswith('"'):
        return _parse_double_quoted(token, line)
    if token.startswith("'"):
        _header_refuse(line, "single-quoted scalar; double-quote it")
    if re.fullmatch(r"[0-9]+", token):
        if len(token) > 1 and token[0] == "0":
            _header_refuse(line, "plain scalar; double-quote it")
        try:
            return int(token)
        except ValueError:
            _header_refuse(line, "integer value too large")
    if _PLAIN_WORD_RE.fullmatch(token):
        if token.lower() in _PLAIN_TYPED_WORDS:
            _header_refuse(line, "plain scalar; double-quote it")
        return token
    _header_refuse(line, "plain scalar; double-quote it")


def _parse_scalar_value(rest, line):
    rest = rest.strip(" ")
    if rest == "":
        return None
    if rest.startswith('"'):
        return _parse_double_quoted(rest, line)
    if rest.startswith("'"):
        _header_refuse(line, "single-quoted scalar; double-quote it")
    if rest.startswith("[") and rest.endswith("]"):
        return _parse_flow_list(rest, line)
    if rest.startswith("["):
        _header_refuse(line, "bad flow list")
    if " " in rest:
        _header_refuse(line, "plain scalar; double-quote it")
    return _parse_scalar_token(rest, line)


class _ParseFrame:
    __slots__ = ("kind", "obj", "content_col", "keys")

    def __init__(self, kind, obj, content_col):
        self.kind = kind
        self.obj = obj
        self.content_col = content_col
        self.keys = set() if kind == "map" else None


def _find_colon(code, line_no):
    i, n = 0, len(code)
    while i < n:
        if code[i] == '"':
            i = _dq_end_in_line(code, i, line_no)
            continue
        if code[i] == ":":
            return i
        i += 1
    return -1


class _HeaderParser:
    def __init__(self, block, base_line):
        self.base_line = base_line
        first_content_line = base_line + 1
        if len(block.encode("utf-8", "surrogatepass")) > _HEADER_BYTE_BOUND:
            _header_refuse(first_content_line, "header block over byte bound")
        _scan_block_characters(block, first_content_line)
        self.lines = []
        for line_no, content, _end in _split_physical_lines(block):
            self.lines.append((base_line + line_no, content))
        self.i = 0
        self.depth = 1

    def _refuse(self, msg):
        line = self.lines[self.i][0] if self.i < len(self.lines) else self.base_line + 1
        _header_refuse(line, msg)

    def _enter_depth(self):
        self.depth += 1
        if self.depth > _HEADER_DEPTH_BOUND:
            self._refuse("nesting too deep")

    def _leave_depth(self):
        self.depth -= 1

    def parse(self):
        if not self.lines:
            return {}
        root = {}
        stack = [_ParseFrame("map", root, 0)]
        self._parse_children(stack)
        return root

    def _parse_key_value(self, code, line_no, allow_list_item=False):
        if allow_list_item:
            if not code.startswith("- "):
                if code == "-" or (code.startswith("-") and not code.startswith("- ")):
                    self._refuse("plain scalar; double-quote it")
                self._refuse("not a key line")
            rest = code[2:]
            if rest == "" or rest[0] == " ":
                self._refuse("plain scalar; double-quote it")
            if rest.startswith("[") or rest.startswith("'"):
                self._refuse("plain scalar; double-quote it")
            code = rest
        ci = _find_colon(code, line_no)
        if ci < 0:
            if allow_list_item:
                try:
                    return None, _parse_scalar_value(code, line_no)
                except HeaderError:
                    raise
            self._refuse("not a key line")
        key = code[:ci]
        after = code[ci + 1:]
        if " " in key or (key and key[-1] == " "):
            if allow_list_item:
                self._refuse("plain scalar; double-quote it")
            self._refuse("bad key")
        if key.startswith('"') or key.startswith("'"):
            self._refuse("quoted key not allowed")
        if after and not after.startswith(" "):
            if allow_list_item:
                self._refuse("plain scalar; double-quote it")
            self._refuse("bad key")
        val = after[1:] if after.startswith(" ") else ""
        if not _valid_key(key):
            if allow_list_item:
                self._refuse("plain scalar; double-quote it")
            self._refuse("bad key")
        return key, val

    def _parse_children(self, stack):
        while self.i < len(self.lines):
            line_no, raw = self.lines[self.i]
            indent, code = _split_line_parts(raw, line_no)
            if not code.strip(" "):
                self.i += 1
                continue
            need_col = stack[-1].content_col
            if indent < need_col:
                return
            if indent != need_col:
                self._refuse("bad indentation")
            _structural_guards(code, line_no)
            frame = stack[-1]
            if frame.kind == "list":
                parsed = self._parse_key_value(code, line_no, allow_list_item=True)
                if parsed[0] is None:
                    frame.obj.append(parsed[1])
                    self.i += 1
                    continue
                key, val = parsed
                mapping = {}
                frame.obj.append(mapping)
                self._enter_depth()
                stack.append(_ParseFrame("map", mapping, indent + 2))
                if key in stack[-1].keys:
                    self._refuse("duplicate key")
                stack[-1].keys.add(key)
                self._store_map_key(stack, indent + 2, key, val, line_no)
                self._parse_children(stack)
                stack.pop()
                self._leave_depth()
                continue
            key, val = self._parse_key_value(code, line_no)
            if key in frame.keys:
                self._refuse("duplicate key")
            frame.keys.add(key)
            self._store_map_key(stack, indent, key, val, line_no)
        return

    def _store_map_key(self, stack, indent, key, val, line_no):
        frame = stack[-1]
        if val.strip(" ") == "":
            self.i += 1
            frame.obj[key] = None
            child_opened = False
            while self.i < len(self.lines):
                nxt_ind, nxt_code = _split_line_parts(self.lines[self.i][1], self.lines[self.i][0])
                if not nxt_code.strip(" "):
                    self.i += 1
                    continue
                if nxt_ind < indent + 2:
                    break
                if not child_opened:
                    if nxt_code.startswith("- "):
                        lst = []
                        frame.obj[key] = lst
                        self._enter_depth()
                        stack.append(_ParseFrame("list", lst, indent + 2))
                        child_opened = True
                    else:
                        child = {}
                        frame.obj[key] = child
                        self._enter_depth()
                        stack.append(_ParseFrame("map", child, indent + 2))
                        child_opened = True
                break
            if child_opened:
                self._parse_children(stack)
                stack.pop()
                self._leave_depth()
        else:
            if val.strip(" ").startswith("[") and not val.strip(" ").endswith("]"):
                self._refuse("bad flow list")
            frame.obj[key] = _parse_scalar_value(val, line_no)
            self.i += 1


def read_header(text):
    """Read YAML front matter: (mapping or None, body). Malformed input raises HeaderError."""
    if not isinstance(text, str):
        raise TypeError("read_header expects a str")
    block, body, base = _find_block(text)
    if block is None:
        return None, body
    if block == "":
        return {}, body
    header = _HeaderParser(block, base).parse()
    return header, body

def _type_spec(type_str):
    text = type_str.strip()
    nullable = False
    if text.endswith(" or null"):
        nullable = True
        text = text[: -len(" or null")].strip()
    if text.startswith("list of "):
        return ("list", _type_spec(text[len("list of "):]), nullable)
    if text.startswith("enum of "):
        items = frozenset(x.strip() for x in text[len("enum of "):].split(", "))
        return ("enum", items, nullable)
    if text in ("string", "integer", "boolean"):
        return (text, None, nullable)
    return ("class", text, nullable)


def _check_value(spec, value, key, findings):
    kind, inner, nullable = spec
    if value is None:
        if nullable:
            return
        findings.append("wrong type for %s" % key)
        return
    if kind == "string":
        if not isinstance(value, str):
            findings.append("wrong type for %s" % key)
        return
    if kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            findings.append("wrong type for %s" % key)
        return
    if kind == "boolean":
        if not isinstance(value, bool):
            findings.append("wrong type for %s" % key)
        return
    if kind == "enum":
        if not isinstance(value, str):
            findings.append("wrong type for %s" % key)
        elif value not in inner:
            findings.append("value for %s outside its set" % key)
        return
    if kind == "list":
        if not isinstance(value, list):
            findings.append("wrong type for %s" % key)
            return
        item_kind, item_inner, _item_null = inner
        for idx, item in enumerate(value):
            if item_kind == "enum":
                if not isinstance(item, str) or item not in item_inner:
                    findings.append("wrong type for %s" % key)
            elif item_kind == "class":
                if not isinstance(item, dict):
                    findings.append("wrong type for %s" % key)
                else:
                    _check_mapping(HEADER_SCHEMAS.get(item_inner, {}), item, findings, item_inner)
            else:
                _check_value(inner, item, "%s[%d]" % (key, idx), findings)
        return
    if kind == "class":
        if not isinstance(value, dict):
            findings.append("wrong type for %s" % key)
            return
        table = HEADER_SCHEMAS.get(inner)
        if not table:
            findings.append("wrong type for %s" % key)
            return
        _check_mapping(table, value, findings, inner)


def _check_mapping(table, header, findings, label=None):
    for k in header:
        if not isinstance(k, str):
            findings.append("unknown key %r" % (k,))
            continue
        if k not in table:
            findings.append("unknown key %s" % k)
    for k in table:
        if k not in header:
            findings.append("missing key %s" % k)
            continue
        _check_value(_type_spec(table[k]), header[k], k, findings)


def _statuses_ok(st):
    return (
        isinstance(st, list)
        and len(st) == 4
        and all(isinstance(x, str) for x in st)
        and len(set(st)) == 4
        and set(st) == set(_REQ_STATUSES)
    )


def check_header(kind, header):
    """Schema findings for a parsed header mapping; empty list when valid."""
    if kind not in _KINDS:
        return ["unknown kind %r" % (kind,)]
    table = HEADER_SCHEMAS.get(kind)
    if not table:
        return ["unknown kind %s" % kind]
    if not isinstance(header, dict):
        return ["header is not a mapping"]
    for k in header:
        if not isinstance(k, str):
            return ["unknown key %r" % (k,)]
    if header.get("record") != kind:
        return ["record"]
    if header.get("header") != 1:
        return ["header"]
    if kind == "requirements" and not _statuses_ok(header.get("statuses")):
        st = header.get("statuses")
        if isinstance(st, list) and any(isinstance(x, str) and x not in _REQ_STATUSES for x in st):
            return ["statuses outside set"]
        return ["statuses"]
    if kind in ("requirements", "diagram-index", "deviations"):
        cols = header.get("columns")
        roles = header.get("roles")
        if not isinstance(cols, list):
            return ["columns"]
        if not isinstance(roles, dict):
            return ["roles"]
        role_table = {
            "requirements": "RequirementsRoles",
            "diagram-index": "DiagramIndexRoles",
            "deviations": "DeviationsRoles",
        }[kind]
        schema_roles = HEADER_SCHEMAS[role_table]
        col_set = frozenset(c for c in cols if isinstance(c, str))
        for rk, col in roles.items():
            if not isinstance(rk, str):
                return ["role %r" % (rk,)]
            if rk not in schema_roles:
                return ["role %s" % rk]
            if not isinstance(col, str):
                return ["role %s" % rk]
            if col not in col_set:
                return ["role %s" % rk]
    findings = []
    _check_mapping(table, header, findings)
    return findings


def _no_wait(prose):
    a = (prose or "").strip().strip("<>").strip().lower()
    return a in _NOTHING or a.startswith(("nothing", "none", "n/a"))


def _normalize_wait(prose):
    if _no_wait(prose):
        return ""
    if prose is None:
        return ""
    return prose


def _none_filler(prose):
    if prose is None:
        return True
    if isinstance(prose, str) and prose.strip().lower() == "none":
        return True
    return False


def _parallel_norm(prose):
    if prose is None:
        return False
    if isinstance(prose, bool):
        return prose
    if isinstance(prose, str):
        low = prose.strip().lower()
        if low == "yes":
            return True
        if low == "no":
            return False
    return prose


def _kind_norm(prose):
    if prose is None:
        return "increment"
    if isinstance(prose, str):
        k = prose.strip().lower()
        if not k:
            return "increment"
        return k
    return "increment"


def _plan_field_value(fk, fields):
    if fk not in fields:
        if fk in ("parent", "deferred"):
            return None
        if fk == "parallel":
            return False
        return []
    val = fields[fk]
    if val == "":
        if fk in ("parent", "deferred"):
            return None
        if fk == "parallel":
            return False
        if fk in ("depends_on", "diagrams", "scope", "satisfies"):
            return []
    if fk == "parent" and _none_filler(val):
        return None
    if fk in ("depends_on", "diagrams") and (val is None or _none_filler(val)):
        return []
    if fk == "parallel":
        return _parallel_norm(val)
    if fk in ("scope", "satisfies") and val is None:
        return []
    return val


def _demonstration_present(line):
    if line is None:
        return False
    if not isinstance(line, str):
        return bool(line)
    return bool(line.strip())


def _derived_historic(fields, inc_id, merged):
    if fields.get("scope") is not None or fields.get("kind") is not None:
        return False
    return inc_id in merged


def _fallback_list(fallback, key):
    if key not in fallback:
        return []
    val = fallback.get(key)
    if val is None:
        return []
    return val


def _fallback_string(fallback, key):
    if key not in fallback:
        return ""
    val = fallback.get(key)
    if val is None:
        return ""
    return val


def header_agrees(kind, header, fallback):
    """Disagreement tokens after check_header found nothing; empty when header matches fallback."""
    if kind == "project-status":
        out = []
        for key in ("phase", "bridge_version", "stage"):
            hv = header.get(key, "")
            fv = _fallback_string(fallback, key)
            if hv != fv:
                out.append(key)
        for key in ("open_issues", "workflows"):
            if header.get(key, []) != _fallback_list(fallback, key):
                out.append(key)
        hwait = header.get("awaiting_user_on", "")
        fwait = _normalize_wait(fallback.get("awaiting_user_on"))
        if hwait != fwait:
            out.append("awaiting_user_on")
        return out
    if kind == "brief":
        out = []
        parsed = parse_review_name(fallback.get("name") or "")
        if parsed:
            fid, fr = parsed
        else:
            fid, fr = None, None
        if header.get("id") != fid:
            out.append("id")
        if header.get("round") != fr:
            out.append("round")
        for key in ("satisfies", "scope", "merge_unit", "blocking_class"):
            hv = header.get(key)
            if key not in fallback:
                if key in ("satisfies", "scope"):
                    fv = []
                elif key == "merge_unit":
                    fv = None
                else:
                    fv = None
            else:
                fv = fallback.get(key)
            if key in ("satisfies", "scope") and fv is None:
                fv = []
            if key == "merge_unit" and hv is None and fv is None:
                continue
            if key == "merge_unit" and hv == [] and fv is None:
                continue
            if key == "merge_unit" and isinstance(fv, tuple):
                fv = list(fv)
            if hv != fv:
                out.append(key)
        return out
    if kind in ("requirements", "diagram-index", "deviations"):
        row = list(fallback.get("header_row") or [])
        cols = list(header.get("columns") or [])
        out = []
        if row != cols:
            out.append("columns")
        roles = header.get("roles") or {}
        for rk, col in roles.items():
            if col not in row:
                out.append("roles.%s" % rk)
        return out
    if kind == "inventory":
        out = []
        if header.get("reflected_through") != fallback.get("reflected_through"):
            out.append("reflected_through")
        hdev = header.get("development_data", "")
        fdev = _fallback_string(fallback, "development_data")
        if hdev != fdev:
            out.append("development_data")
        sections = fallback.get("sections") or {}
        tables = header.get("tables") or {}
        all_secs = set(tables) | set(sections)
        columns_reported = False
        for sec in sorted(all_secs):
            if sec not in sections or sections.get(sec) is None:
                out.append("tables.%s" % sec)
                continue
            if sec not in tables:
                out.append("tables.%s" % sec)
                continue
            if list(tables[sec].get("columns") or []) != list(sections[sec] or []):
                if not columns_reported:
                    out.append("columns")
                    columns_reported = True
        return out
    if kind == "run-parameters":
        out = []
        schema = HEADER_SCHEMAS["run-parameters"]
        list_keys = ("ceiling_above_twice", "design_rounds_above_five", "review_rounds_above_ceiling")

        def _rp_default(key):
            if key in list_keys:
                return []
            if key == "agent_ceiling":
                return None
            return ""

        for key in schema:
            if key in ("record", "header"):
                continue
            hv = header.get(key, _rp_default(key))
            if key not in fallback:
                fv = _rp_default(key)
            else:
                fv = fallback.get(key)
            if fv is None and key not in list_keys and key != "agent_ceiling":
                fv = ""
            if key in list_keys and fv is None:
                fv = []
            if key in list_keys and hv is None:
                hv = []
            if hv != fv:
                out.append(key)
        return out
    if kind == "build-plan":
        return _plan_agrees(header, fallback)
    return ["kind"]


def _plan_agrees(header, fallback):
    out = []
    hstages = header.get("stages") or []
    fstages = fallback.get("stages") or []
    merged = fallback.get("merged")
    nstages = max(len(hstages), len(fstages))
    for si in range(nstages):
        if si >= len(hstages):
            out.append("%s name" % (fstages[si].get("name") or "stage"))
            continue
        if si >= len(fstages):
            out.append("%s name" % (hstages[si].get("name") or "stage"))
            continue
        hs, fs = hstages[si], fstages[si]
        sname = hs.get("name")
        if sname != fs.get("name"):
            out.append("%s name" % (sname or "Stage"))
        if bool(hs.get("demonstration")) != _demonstration_present(fs.get("demonstration")):
            out.append("%s demonstration" % (sname or "Stage"))
        hin = hs.get("increments") or []
        fin = fs.get("increments") or []
        ninc = max(len(hin), len(fin))
        for ii in range(ninc):
            if ii >= len(hin):
                out.append("%s id" % fin[ii].get("id", "TASK"))
                continue
            if ii >= len(fin):
                out.append("%s id" % hin[ii].get("id", "TASK"))
                continue
            inc_h, inc_f = hin[ii], fin[ii]
            iid = inc_h.get("id")
            fields = inc_f.get("fields") or {}
            if inc_h.get("id") != inc_f.get("id"):
                out.append("%s id" % iid)
            if inc_h.get("title") != inc_f.get("title"):
                out.append("%s title" % iid)
            for fk in ("kind", "parallel", "parent", "depends_on", "diagrams", "scope", "satisfies", "deferred"):
                fv = _plan_field_value(fk, fields)
                hv = inc_h.get(fk)
                if fk == "kind":
                    if _kind_norm(fields.get("kind") if "kind" in fields else None) != hv:
                        out.append("%s kind" % iid)
                    continue
                if fk == "parallel":
                    if _plan_field_value("parallel", fields) != hv:
                        out.append("%s parallel" % iid)
                    continue
                if fv != hv:
                    out.append("%s %s" % (iid, fk))
            hist_h = bool(inc_h.get("historic"))
            if merged is None:
                if fields.get("scope") is not None or fields.get("kind") is not None:
                    derived = _derived_historic(fields, inc_f.get("id"), set())
                    if hist_h != derived:
                        out.append("%s historic" % iid)
            else:
                derived = _derived_historic(fields, inc_f.get("id"), merged)
                if hist_h != derived:
                    out.append("%s historic" % iid)
    return out


_STATUS_TRAITS_MARK = "; traits: "
_STATUS_ARROW = "\u2192"
_OPEN_ISSUES_RX = re.compile(r"^[ \t]*(?:[-*]\s+)?[*_`]*Open issues[*_`]*\s*:[*_`]*\s*(.*)$", re.M | re.I)

STATUS_WORKFLOWS_PROBLEMS = (
    "Workflows line breaks the part-prefix rule",
    "Workflows line must contain '; traits: ' exactly once",
    "two Workflows lines name the same part",
    "empty name in the Workflows head",
)


def _status_rule_line_end(text, pos):
    """After a --- at pos, return index after the line ending when the rule line is well formed."""
    if pos + 3 > len(text) or text[pos:pos + 3] != "---":
        return None
    i = pos + 3
    while i < len(text) and text[i] in " \t\r":
        i += 1
    if i >= len(text):
        return i
    if text[i] == "\n":
        return i + 1
    if text[i] == "\r" and i + 1 < len(text) and text[i + 1] == "\n":
        return i + 2
    return None


def _status_prose_body(text):
    if not isinstance(text, str):
        return ""
    if text.startswith("\ufeff"):
        text = text[1:]
    if len(text) < 3 or text[:3] != "---":
        return text
    first_end = _status_rule_line_end(text, 0)
    if first_end is None:
        return text
    pos = first_end
    while pos <= len(text):
        if text.startswith("---", pos):
            close_end = _status_rule_line_end(text, pos)
            if close_end is not None:
                return text[close_end:]
        nl = text.find("\n", pos)
        if nl == -1:
            break
        pos = nl + 1
    return text[first_end:]


def _status_body_lines(text):
    lines = text.split("\n")
    if lines and lines[-1] == "":
        del lines[-1]
    return lines


def _status_hook_field(text, name):
    pat = r"^[ \t]*(?:[-*]\s+)?[*_`]*%s[*_`]*\s*:[*_`]*\s*(.*?)\s*$" % re.escape(name)
    m = re.search(pat, text, re.M | re.I)
    if not m:
        return None
    return m.group(1).strip().strip("*_`").strip()


def _status_stage_field(text):
    m = re.search(r"^[ \t*_-]*Stage[*_]*\s*:[*_\s`]*([^`\n]+)", text, re.M | re.I)
    return m.group(1).strip() if m else None


def _status_bridge_stamp(value):
    if not value:
        return ""
    m = re.search(r"[0-9]{4}\.[0-9]{2}\.[0-9]{2}[a-z]?", value)
    return m.group(0) if m else ""


def _status_segments(value):
    if not value:
        return []
    parts, depth, quote, cur = [], 0, False, ""
    for i, ch in enumerate(value):
        if ch == '"':
            quote = not quote
        elif not quote and ch in "([":
            depth += 1
        elif not quote and ch in ")]":
            depth = max(0, depth - 1)
        if depth == 0 and not quote and (ch == ";" or (ch == "." and value[i + 1:i + 2] in (" ", ""))):
            parts.append(cur.strip())
            cur = ""
            continue
        cur += ch
    parts.append(cur.strip())
    return [p for p in parts if p]


def _status_prefix_of(rest, multi):
    mark_at = rest.find(_STATUS_TRAITS_MARK)
    if mark_at == -1:
        head = rest
        tail = ""
    else:
        head = rest[:mark_at]
        tail = rest[mark_at:]
    if ": " not in head:
        if multi:
            return None, None, "-"
        return None, rest, None
    cut = head.find(": ")
    part = head[:cut]
    invalid = part == "" or part != part.strip() or ";" in part or _STATUS_ARROW in part or ":" in part
    if (not multi) or invalid:
        return None, None, part or "-"
    return part, head[cut + 2:] + tail, None


def _status_workflow_part(body):
    if body == "not yet classified":
        return None
    if body.count(_STATUS_TRAITS_MARK) != 1:
        return None
    head, traits_text = body.split(_STATUS_TRAITS_MARK, 1)
    segments = [segment.strip() for segment in head.split(_STATUS_ARROW)]
    for segment in segments:
        for name in [n.strip() for n in segment.split(",")]:
            if name == "":
                return None
    sub_name = None
    if _STATUS_ARROW in head:
        type_name, sub_name = head.split(_STATUS_ARROW, 1)
        type_name, sub_name = type_name.strip(), sub_name.strip()
    else:
        type_name = head.strip()
    traits_text = traits_text.strip()
    if traits_text == "none":
        traits = []
    else:
        traits = [t.strip() for t in traits_text.split(", ")]
    return {"type": type_name, "subtype": sub_name or None, "traits": traits}


def status_workflow_line(rest, multi, seen_parts):
    """One Workflows: line's grammar (part prefix, traits marker, duplicate part, empty name)."""
    part, body_line, bad = _status_prefix_of(rest, multi)
    if bad is not None:
        return None, None, bad, [STATUS_WORKFLOWS_PROBLEMS[0]], None
    line_problems = []
    if part is not None:
        seen_parts[part] = seen_parts.get(part, 0) + 1
        if seen_parts[part] == 2:
            line_problems.append(STATUS_WORKFLOWS_PROBLEMS[2])
    if body_line == "not yet classified":
        return part, body_line, None, line_problems, None
    if body_line.count(_STATUS_TRAITS_MARK) != 1:
        line_problems.append(STATUS_WORKFLOWS_PROBLEMS[1])
        return part, body_line, None, line_problems, None
    head, _traits = body_line.split(_STATUS_TRAITS_MARK, 1)
    for segment in [s.strip() for s in head.split(_STATUS_ARROW)]:
        for name in [n.strip() for n in segment.split(",")]:
            if name == "":
                line_problems.append(STATUS_WORKFLOWS_PROBLEMS[3])
                return part, body_line, None, line_problems, None
    if line_problems:
        return part, body_line, None, line_problems, None
    parsed = _status_workflow_part(body_line)
    return part, body_line, None, [], parsed


def status_workflows(text):
    """(parts, problems) from the status file's Workflows lines (strict grammar)."""
    body = _status_prose_body(text)
    lines = [line for line in _status_body_lines(body) if line.startswith("Workflows: ")]
    if not lines:
        return [], []
    multi = len(lines) > 1
    parts, problems = [], []
    seen_parts = {}
    for line in lines:
        rest = line[len("Workflows: "):]
        _part, _body, bad, line_problems, parsed = status_workflow_line(rest, multi, seen_parts)
        problems.extend(line_problems)
        if line_problems:
            continue
        if parsed is not None:
            parts.append(parsed)
    return parts, problems


def status_fallback(text):
    """The six project-status fields read from prose (one copy each)."""
    body = _status_prose_body(text)
    phase_raw = _status_hook_field(body, "Phase") or ""
    phase_word = phase_raw.split()[0].lower() if phase_raw.split() else ""
    awaiting_raw = _status_hook_field(body, "Awaiting user on")
    if awaiting_raw is None:
        awaiting = ""
    else:
        awaiting = _normalize_wait(awaiting_raw)
    bridge = _status_bridge_stamp(_status_hook_field(body, "Bridge version") or "")
    stage = _status_stage_field(body) or ""
    issues_line = _OPEN_ISSUES_RX.search(body)
    open_issues = _status_segments(issues_line.group(1)) if issues_line else []
    workflows, _problems = status_workflows(text)
    return {
        "phase": phase_word,
        "workflows": workflows,
        "awaiting_user_on": awaiting,
        "bridge_version": bridge,
        "stage": stage,
        "open_issues": open_issues,
    }


def status_values(text):
    """(values, malformed, disagrees) for a status file's six header fields."""
    fallback = status_fallback(text)
    header = None
    malformed = None
    try:
        header, _body = read_header(text)
    except HeaderError as err:
        malformed = (err.line, str(err))
        return fallback, malformed, []
    if header is None:
        return fallback, None, []
    findings = check_header("project-status", header)
    if findings:
        malformed = (1, "; ".join(findings))
        return fallback, malformed, []
    values = {
        "phase": header.get("phase", ""),
        "workflows": list(header.get("workflows") or []),
        "awaiting_user_on": header.get("awaiting_user_on", ""),
        "bridge_version": header.get("bridge_version", ""),
        "stage": header.get("stage", ""),
        "open_issues": list(header.get("open_issues") or []),
    }
    disagrees = header_agrees("project-status", header, fallback)
    return values, None, disagrees

