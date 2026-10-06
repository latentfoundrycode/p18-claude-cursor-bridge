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
            return home, None
        if not repair:
            return home, "%s is a link that does not lead to %s" % (link, target)
        try:
            os.rmdir(link)                        # the link itself, never what it points at
        except OSError as e:
            return home, "cannot remove the link %s (%s)" % (link, e)
    if not create:
        return home, "%s does not exist" % link
    try:
        os.makedirs(home, exist_ok=True)
        os.makedirs(target, exist_ok=True)
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
            os.rmdir(link)
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
    for p in (link, target):
        try:
            os.rmdir(p)
        except OSError:
            pass
    return problem


# the caches the builders' tools read by default under the home, passed through by their own
# variables; never HF_HOME or XDG_CACHE_HOME, which would show the owner's token file again
CACHES = (("HF_HUB_CACHE", os.path.join(".cache", "huggingface", "hub")),
          ("TORCH_HOME", os.path.join(".cache", "torch")),
          ("PUPPETEER_CACHE_DIR", os.path.join(".cache", "puppeteer")))


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
    # GIT_CONFIG_* is read last, so an empty credential.helper resets the helper list that
    # the system and global gitconfig built up (git >= 2.31).
    e["GIT_CONFIG_COUNT"] = "1"
    e["GIT_CONFIG_KEY_0"] = "credential.helper"
    e["GIT_CONFIG_VALUE_0"] = ""
    # The run's own home folder (2026.10.06a, KP-038); git keeps the owner's global
    # configuration (identity, safe.directory) through GIT_CONFIG_GLOBAL.
    home, problem = agent_home(e)
    if problem:
        raise AgentHomeError("the agent's home folder is not usable: %s (KP-038)" % problem)
    real = real_home(e)
    gitconfig = os.path.join(real, ".gitconfig")
    e["HOME"] = e["USERPROFILE"] = home
    drive, rest = os.path.splitdrive(home)
    if drive:
        e["HOMEDRIVE"], e["HOMEPATH"] = drive, rest
    if os.path.isfile(gitconfig):
        e["GIT_CONFIG_GLOBAL"] = gitconfig
    else:
        e.pop("GIT_CONFIG_GLOBAL", None)
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
