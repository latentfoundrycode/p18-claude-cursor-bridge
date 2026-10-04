"""bridge_env: shared helpers for the bridge's programs that start cursor-agent.

- stripped_env(): the process environment with the owner's identity withheld (KP-032). It is
  the same recipe as cursor-agent.shim, kept here so every Python launcher of cursor-agent
  (bridge-run.py, roster-check.py's probe) applies it without going through the shell.
- cursor_agent_launcher(): the argv prefix that starts cursor-agent the way Windows needs it
  (the .cmd launcher through cmd.exe), or the binary elsewhere.

ASCII-only on purpose (cp1252 consoles). Never writes anything but the empty gh folder.
"""
import os
import shutil

TOKEN_VARS = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN",
              "GIT_ASKPASS", "SSH_ASKPASS")


def gh_empty_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    return os.path.join(base, "cursor-bridge", "gh-empty")


def stripped_env(env=None):
    """Return a copy of `env` (default: os.environ) in which gh is logged out, no token
    variable survives, and git has no credential helper and never prompts."""
    e = dict(os.environ if env is None else env)
    empty = gh_empty_dir()
    try:
        os.makedirs(empty, exist_ok=True)
    except OSError:
        pass
    e["GH_CONFIG_DIR"] = empty
    for k in TOKEN_VARS:
        e.pop(k, None)
    e["GIT_TERMINAL_PROMPT"] = "0"
    # GIT_CONFIG_* is read last, so an empty credential.helper resets the helper list that
    # the system and global gitconfig built up (git >= 2.31).
    e["GIT_CONFIG_COUNT"] = "1"
    e["GIT_CONFIG_KEY_0"] = "credential.helper"
    e["GIT_CONFIG_VALUE_0"] = ""
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
