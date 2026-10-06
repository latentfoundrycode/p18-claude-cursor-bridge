#!/usr/bin/env python3
"""permission-guard: a Claude Code PreToolUse hook for the Bash and PowerShell tools that
refuses the two actions the loop must never take, in every permission mode (KP-032):

  - merging a pull request past the repository's rules: `gh pr merge … --admin`, and the
    REST route `gh api … /pulls/<n>/merge` with a method that writes;
  - a force-push in any form: `--force`, `--force-with-lease`, `--force-if-includes`,
    `-f`, a combined short flag such as `-fu`, `--mirror`, a `+` refspec;
  - any `git worktree remove` (rule 19, release A1b): Git for Windows follows a gitignored
    junction or symbolic link inside the worktree into its target in an ordinary removal
    as in a forced one; `worktree-teardown.py` removes a worktree and refuses while a link
    is inside (it runs git as its own child, which this hook never sees);
  - a merge without the pre-merge check's record (release A1b): `gh pr merge` must carry
    `--match-head-commit <sha>`, and `review-guard.py premerge` must have written the record
    `<git common dir>/bridge/premerge/<sha>` for that sha when it printed OK; `--disable-auto`
    and `--help` pass; a `gh api graphql` call carrying a merge mutation is refused.

A command behind a wrapper shell (`bash -c`, `bash -lc`, `sh -c`, `cmd /c`, `cmd /k`,
`powershell -Command`), quoted or not, is checked as the command it is; a single `&` and the
PowerShell call operator `&`, joined or not, separate commands; `{`, `if`, `then`, `xargs` and
its options are dropped like `env` and `timeout`; a here-document's body is data (a commit
message that quotes a forbidden command is not a command); a `git -c alias.<x>=...` whose
value starts with `worktree`, `pr`, `push`, `api` or `!` is refused; an abbreviated `--forc`
counts as `--force`, as it does for git; `--help` exempts a `gh pr merge` only when it is not
the value of a flag such as `--subject`.
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
import os
import re
import shlex
import subprocess
import sys

WRITE_METHODS = ("PUT", "POST", "PATCH", "DELETE")
AROUND_THE_SHIM = ("agent", "agent.cmd", "agent.ps1", "cursor-agent.cmd", "cursor-agent.ps1", "cursor-agent.exe")
SHELLS = ("cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe")
PROGRAM_AFTER = ("/c", "/k", "-c", "-command", "-file")
WRAPPER_SHELLS = SHELLS + ("bash", "bash.exe", "sh", "sh.exe", "zsh", "dash")
MERGE_MUTATIONS = ("mergePullRequest", "enablePullRequestAutoMerge", "enqueuePullRequest")
GH_VALUE_FLAGS = ("-t", "--subject", "-b", "--body", "-F", "--body-file", "-A", "--author-email", "-R", "--repo", "--match-head-commit", "--hostname")
ALIAS_RX = re.compile(r"^alias\.[\w-]+=\s*['\"]?\s*(!|worktree\b|pr\b|push\b|api\b)", re.I)
HEREDOC_RX = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1[^\n]*\n.*?^\2[ \t]*$", re.S | re.M)
PREMERGE_DIR = os.path.join("bridge", "premerge")
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


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
        elif c in (";", "|", "&", "\n", "(", ")", "`"):   # a single & separates too (cmd; PowerShell's call operator)
            parts.append(buf); buf = ""
        elif c == "$" and text.startswith("$(", i):
            parts.append(buf); buf = ""; i += 1
        else:
            buf += c
        i += 1
    parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def strip_heredocs(text):
    """A here-document's body is data (a commit message), not commands."""
    return HEREDOC_RX.sub(lambda m: m.group(0).split("\n", 1)[0], text)


def words(command):
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def shell_inner(w):
    """The command a wrapper shell runs, as one string: everything after /c, /k, -c, -Command,
    -File or a combined short flag ending in c (bash -lc), quoted or not; None without one."""
    for i, tok in enumerate(w[1:], 1):
        t = tok.lower()
        if t in PROGRAM_AFTER or re.match(r"^-[a-z]*c$", t):
            rest = w[i + 1:]
            return " ".join(rest) if rest else None
    return None


def gh_words(w):
    """(group, subcommand, the rest) of a gh command; flags before the subcommand are skipped
    (`gh pr -R owner/repo merge ...`)."""
    found, rest, i = [], [], 1
    while i < len(w):
        tok = w[i]
        if len(found) < 2:
            if tok in ("-R", "--repo", "--hostname"):
                i += 2
                continue
            if tok.startswith("-"):
                i += 1
                continue
            found.append(tok)
        else:
            rest.append(tok)
        i += 1
    found += [None, None]
    return found[0], found[1], rest


def strip_prefix(w):
    """Drop leading assignments and wrappers (timeout 5, env X=1, nice, nohup, sudo …) and
    PowerShell's call operator `&`."""
    i = 0
    while i < len(w):
        tok = w[i]
        if tok in ("&", "{", "}", "then", "do", "else", "elif", "if", "while", "until", "!"):
            i += 1
            continue
        if tok in ("xargs", "xargs.exe"):
            i += 1
            while i < len(w) and (w[i].startswith("-") or w[i].isdigit() or w[i] == "{}"):
                i += 1
            continue
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
        if len(a) >= 4 and "--force".startswith(a):      # git accepts an unambiguous abbreviation
            return "git push with %s (an abbreviation of --force)" % a
        if re.match(r"^-[A-Za-z]*f[A-Za-z]*$", a):
            return "git push with the short flag %s" % a
        if a.startswith("+") and len(a) > 1:
            return "git push with a forcing refspec %s" % a
    return None


def premerge_recorded(sha, cwd):
    """True when review-guard.py premerge wrote its record for this head in the repository the
    hook's cwd belongs to (release A1b): the sha alone proves nothing, the record does."""
    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", sha or ""):
        return False
    try:
        p = subprocess.run(["git", "-C", cwd or ".", "-c", "core.fsmonitor=false", "rev-parse", "--git-common-dir"],
                           capture_output=True, text=True, timeout=20, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if p.returncode != 0:
        return False
    common = p.stdout.strip()
    if not os.path.isabs(common):
        common = os.path.join(cwd or ".", common)
    try:
        names = os.listdir(os.path.join(common, PREMERGE_DIR))
    except OSError:
        return False
    return any(n.lower().startswith(sha.lower()) for n in names)


def merge_reason(args, cwd):
    """The reason to refuse a gh pr merge (args = the words after `merge`), or None."""
    if any(a == "--admin" or a.startswith("--admin=") for a in args):
        return "gh pr merge --admin (merging past the repository's rules)"
    if "--disable-auto" in args:
        return None
    for i, a in enumerate(args):
        if a in ("--help", "-h") and (i == 0 or args[i - 1] not in GH_VALUE_FLAGS):
            return None                                    # `--subject --help` is a subject, and gh merges
    sha = None
    for i, a in enumerate(args):
        if a == "--match-head-commit":
            sha = args[i + 1] if i + 1 < len(args) else ""
        elif a.startswith("--match-head-commit="):
            sha = a.split("=", 1)[1]
    if sha is None:
        return "gh pr merge without --match-head-commit <sha>: the sha, and the record review-guard.py premerge writes when it prints OK, are the gate's confirmation"
    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", sha):
        return "gh pr merge with an empty or malformed --match-head-commit value"
    if not premerge_recorded(sha, cwd):
        return "gh pr merge for %s without the pre-merge check's record: run python ~/.claude/cursor-bridge/review-guard.py premerge <nnn> <n> in the checkout first (it writes the record when it prints OK)" % sha[:12]
    return None


def check(command, cwd=None):
    """Return the reason to refuse, or None."""
    for simple in split_commands(strip_heredocs(command)):
        w = strip_prefix(words(simple))
        if not w:
            continue
        head = base(w[0])
        if head in WRAPPER_SHELLS:
            inner = shell_inner(w)
            if inner:
                r = check(inner, cwd)
                if r:
                    return r
        started = w[0] if around_the_shim(w[0]) else (program_behind(w) if head in SHELLS else None)
        if started and around_the_shim(started):
            return "starting the Cursor agent as %s, around the bridge's shim (KP-038); start it as cursor-agent, or through bridge-run.py" % started
        if is_git(w):
            helpful = "--help" in w[1:] or "-h" in w[1:]      # git runs nothing with these, in any position
            for a in w:
                if ALIAS_RX.match(a) or (a.lower().startswith("alias.") and re.search(r"worktree\s+remove|pr\s+merge|push\b.*(--force|--forc|-f\b|\+)", a, re.I)):
                    return "a git alias that defines a refused command (%s)" % a[:60]
            sub, args = git_subcommand(w)
            if sub == "push" and not helpful:
                r = force_push_reason(args)
                if r:
                    return r
            if sub == "worktree" and args and args[0] == "remove" and not helpful:
                return "git worktree remove (git follows a gitignored junction or link inside the worktree into its target, forced or not): tear a worktree down with python ~/.claude/cursor-bridge/worktree-teardown.py <path>, which refuses while a link is inside"
        elif head in ("gh", "gh.exe"):
            group, sub, args = gh_words(w)
            if group == "pr" and sub == "merge":
                r = merge_reason(args, cwd)
                if r:
                    return r
            if group == "api" and any(m in tok for tok in w for m in MERGE_MUTATIONS):
                return "gh api with a merge mutation (merging outside the gate)"
            if group == "api" and sub == "graphql" and any(t == "--input" or t.startswith("--input=") or t.startswith("@") or "=@" in t for t in args):
                return "gh api graphql with a query read from a file, which the guard cannot read (write the query on the command line)"
            if group == "api":
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
    reason = check(command, data.get("cwd") or os.getcwd())
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
