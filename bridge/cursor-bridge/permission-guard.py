#!/usr/bin/env python3
"""permission-guard: a Claude Code PreToolUse hook for the Bash and PowerShell tools that
refuses the two actions the loop must never take, in every permission mode (KP-032):

  - merging a pull request past the repository's rules: `gh pr merge … --admin`, and the
    REST route `gh api … /pulls/<n>/merge` with a method that writes;
  - a force-push in any form: `--force`, `--force-with-lease`, `--force-if-includes`,
    `-f`, a combined short flag such as `-fu`, `--mirror`, a `+` refspec;
  - a forced worktree removal (`git worktree remove --force`, `-f`), which follows a live
    junction or symbolic link inside the worktree into its target (rule 19, release A1b);
    `worktree-teardown.py` removes a worktree without forcing;
  - a merge that does not carry the confirmation only the pre-merge check prints:
    `gh pr merge` without `--match-head-commit <sha>` (release A1b), except `--disable-auto`;
  - the Cursor agent started around the bridge's shim (`agent`, `agent.cmd`, `agent.ps1`,
    `cursor-agent.cmd`, `cursor-agent.ps1`, `cursor-agent.exe`, also behind `cmd /c` or
    `powershell`), which would run it with the owner's real home and identity (KP-038): the
    agent is started as `cursor-agent`, or through bridge-run.py.

It parses the command rather than matching a pattern, so chains, wrappers and quoting do
not hide the action, and `git commit -m "never use --force"` is not refused. Deny rules in
settings.bridge.json cover the common spellings as a second layer; this hook is the one
that reads the whole command.

Registered by bridge-install.py from settings.bridge.json (hooks.PreToolUse, matcher
"Bash|PowerShell"). Reads the hook's JSON on stdin; exit 2 with the reason on stderr blocks
the call (documented), exit 0 lets it through. Fails open on anything unexpected: a guard
that cannot read its input never blocks the loop. ASCII-only on purpose. Never writes.
"""
import json
import re
import shlex
import sys

WRITE_METHODS = ("PUT", "POST", "PATCH", "DELETE")
AROUND_THE_SHIM = ("agent", "agent.cmd", "agent.ps1", "cursor-agent.cmd", "cursor-agent.ps1", "cursor-agent.exe")
SHELLS = ("cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe")
PROGRAM_AFTER = ("/c", "/k", "-c", "-command", "-file")


def base(tok):
    return tok.lower().split("/")[-1].split("\\")[-1]


def around_the_shim(tok):
    """The Cursor agent started by a name other than `cursor-agent` (KP-038): one of the CLI's
    own launcher names, or a bare `agent` without a path or from the CLI's own folder; a
    project's own `./agent` or `dist/agent.exe` is not it."""
    name = base(tok)
    if name not in AROUND_THE_SHIM:
        return False
    if name == "agent" and ("/" in tok or "\\" in tok) and "cursor-agent" not in tok.lower():
        return False
    return True


def program_behind(w):
    """The program a shell wrapper runs: the token after /c, /k, -c, -Command or -File."""
    for i, tok in enumerate(w[1:-1], 1):
        if tok.lower() in PROGRAM_AFTER:
            return w[i + 1]
    return None


def split_commands(text):
    """Break a shell command line into its simple commands: on &&, ||, ;, |, newlines and
    subshell parentheses. Quotes are respected. Good enough for commands a model writes."""
    parts, buf, quote, i = [], "", None, 0
    while i < len(text):
        c = text[i]
        if quote:
            buf += c
            if c == quote and (i == 0 or text[i - 1] != "\\"):
                quote = None
        elif c in ("'", '"'):
            quote = c
            buf += c
        elif text.startswith("&&", i) or text.startswith("||", i):
            parts.append(buf); buf = ""; i += 1
        elif c in (";", "|", "\n", "(", ")", "`"):
            parts.append(buf); buf = ""
        elif c == "$" and text.startswith("$(", i):
            parts.append(buf); buf = ""; i += 1
        else:
            buf += c
        i += 1
    parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def words(command):
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def strip_prefix(w):
    """Drop leading assignments and wrappers (timeout 5, env X=1, nice, nohup, sudo …)."""
    i = 0
    while i < len(w):
        tok = w[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok):
            i += 1
            continue
        if tok in ("env", "nice", "nohup", "stdbuf", "time", "sudo", "command", "builtin", "exec"):
            i += 1
            while i < len(w) and w[i].startswith("-"):
                i += 1
            continue
        if tok == "timeout":
            i += 1
            while i < len(w) and w[i].startswith("-"):
                i += 1
            i += 1                                   # the duration
            continue
        break
    return w[i:]


def is_git(w):
    return bool(w) and w[0].lower().split("/")[-1].split("\\")[-1] in ("git", "git.exe")


def git_subcommand(w):
    """The git subcommand and its arguments, skipping global options such as -C <dir>."""
    i = 1
    while i < len(w):
        tok = w[i]
        if tok in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"):
            i += 2
            continue
        if tok.startswith("-"):
            i += 1
            continue
        return tok, w[i + 1:]
    return None, []


def force_push_reason(args):
    for a in args:
        if a in ("--force", "--force-with-lease", "--force-if-includes", "--mirror") or a.startswith("--force-with-lease=") or a.startswith("--force-if-includes="):
            return "git push with %s" % a
        if re.match(r"^-[A-Za-z]*f[A-Za-z]*$", a):
            return "git push with the short flag %s" % a
        if a.startswith("+") and len(a) > 1:
            return "git push with a forcing refspec %s" % a
    return None


def check(command):
    """Return the reason to refuse, or None."""
    for simple in split_commands(command):
        w = strip_prefix(words(simple))
        if not w:
            continue
        head = base(w[0])
        started = w[0] if around_the_shim(w[0]) else (program_behind(w) if head in SHELLS else None)
        if started and around_the_shim(started):
            return "starting the Cursor agent as %s, around the bridge's shim (KP-038); start it as cursor-agent, or through bridge-run.py" % started
        if is_git(w):
            sub, args = git_subcommand(w)
            if sub == "push":
                r = force_push_reason(args)
                if r:
                    return r
            if sub == "worktree" and args and args[0] == "remove":
                for a in args[1:]:
                    if a == "--force" or re.match(r"^-[A-Za-z]*f[A-Za-z]*$", a):
                        return "git worktree remove with %s (a forced removal follows a live link inside the worktree into its target; use worktree-teardown.py)" % a
        elif head in ("gh", "gh.exe"):
            if len(w) >= 3 and w[1] == "pr" and w[2] == "merge" and any(a == "--admin" or a.startswith("--admin=") for a in w):
                return "gh pr merge --admin (merging past the repository's rules)"
            if len(w) >= 3 and w[1] == "pr" and w[2] == "merge" and "--disable-auto" not in w \
                    and not any(a == "--match-head-commit" or a.startswith("--match-head-commit=") for a in w):
                return "gh pr merge without --match-head-commit <sha>, the confirmation only review-guard.py premerge prints (a merge that skipped the gate is not refused by anything else)"
            if len(w) >= 2 and w[1] == "api":
                method = "GET"
                for i, a in enumerate(w):
                    if a in ("-X", "--method") and i + 1 < len(w):
                        method = w[i + 1].upper()
                    elif a.startswith("--method="):
                        method = a.split("=", 1)[1].upper()
                    elif a in ("-f", "--raw-field", "-F", "--field", "--input"):
                        method = method if method != "GET" else "POST"   # gh switches to POST with fields
                if method in WRITE_METHODS and any(re.search(r"/pulls/\d+/merge\b", a) for a in w):
                    return "gh api %s on a pull request's merge endpoint (merging outside the gate)" % method
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0
    tool = data.get("tool_name") or ""
    if tool not in ("Bash", "PowerShell"):
        return 0
    command = ((data.get("tool_input") or {}).get("command") or "")
    if not isinstance(command, str) or not command.strip():
        return 0
    reason = check(command)
    if reason:
        sys.stderr.write("permission-guard (Claude-Cursor Bridge): refused - %s. The loop merges only through the "
                         "verified gate and never force-pushes; if the branch rules refuse a merge, fix the cause, "
                         "never bypass the rules.\n" % reason)
        return 2
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
