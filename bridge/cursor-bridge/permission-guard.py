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
value starts with `worktree`, `pr`, `push`, `api` or `!` is refused, and so is a `gh alias set`
for a merge; an abbreviated `--forc` counts as `--force`, as it does for git; `--help` exempts a
`gh pr merge` only when it is not the value of a flag such as `--subject`. A here-document
read by a shell (`bash <<EOF`) is that shell's script and is checked; one read by any other
program (a commit message) is data. `powershell` without `-Command` runs the rest of its line,
`-com` abbreviates `-Command`, `.` runs a program as `&` does, `find -exec` runs its command,
and `-XPUT` is a method: all read as what they run. An encoded PowerShell command and a
GraphQL query built by a command substitution are refused unread.
  - inside a bridge Workspace (one holding docs/PROJECT_STATUS.md), a chain of commands
    (`&&`, `;`, `||`, a new line) carrying a state-changing git or gh command, or a command
    wrapped in `cd …` (rule 8: one command per call; a chain once built an increment on a
    merged branch; release A4). A pipe into a reader and a chain of reads pass.
  - a commit or push that skips its checks: `--no-verify`, commit's `-n`, or a
    `-c core.hooksPath=…` override (rule 4; release A4), except the two snapshots the merge
    policy allows: the pre-delegation checkpoint, whose subject starts with "checkpoint" and
    names the increment (`checkpoint before TASK-nnn`, with a round or a note after it,
    `checkpoint: … before TASK-nnn …`) and carries no accept, merge or release word; and a
    builder's hand-off ("… hand-off") made inside a worktree (`-C …/Worktrees/…`).
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
VALUE_OPTIONS = {"xargs": ("-I", "-n", "-L", "-s", "-d", "-P", "-E", "-a", "--max-args", "--max-lines", "--delimiter", "--max-procs", "--arg-file", "--replace"),
                 "nice": ("-n", "--adjustment"), "timeout": ("-s", "--signal", "-k", "--kill-after"), "sudo": ("-u", "-g", "--user", "--group"),
                 "env": ("-u", "--unset", "-C", "--chdir", "-S", "--split-string")}
PS_VALUE_SWITCHES = ("-executionpolicy", "-ep", "-ex", "-version", "-v", "-windowstyle", "-w", "-workingdirectory", "-wd", "-inputformat", "-if",
                     "-outputformat", "-of", "-psconsolefile", "-psc", "-configurationname", "-config", "-settingsfile", "-settings")
ENCODED = object()
PREMERGE_DIR = os.path.join("bridge", "premerge")
STATE_GIT = ("add", "commit", "push", "pull", "merge", "rebase", "switch", "checkout", "reset", "rm", "mv", "cherry-pick", "revert",
             "am", "apply", "clean", "restore", "stash", "worktree", "branch", "tag", "submodule", "config")
BRANCH_WRITES = ("-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy", "--set-upstream-to", "-u", "--unset-upstream", "-f", "--force")
INCREMENT_RX = re.compile(r"\b(?:TASK|BUG|REFAC|FIX|CONFIG)-(?:\d{3,}[a-z]?|<nnn>|[\w-]+)(?!\w)", re.I)   # the plan's IDs, and a project's own spelling (FIX-next-sharp)
NOT_A_SNAPSHOT_RX = re.compile(r"(?<![-\w])(?:accept\w*|merge|merges|merging|release\w*|ship\w*)\b", re.I)   # an action word; "merged" (a status note) and "overlay-merge" (a name) are not


def snapshot_subject(message):
    """The checkpoint commit the merge policy exempts: the subject says `checkpoint` and names the
    increment, and its leading clause (before any parenthesis) carries no accept, merge, release or
    ship word (`checkpoint before TASK-159 r2 (round 1 builder output)`, `TASK-010c round 3
    checkpoint (status after TASK-059b merge)`, `BUG-022: round-2 brief (checkpoint)`, `checkpoint
    (paused by owner): TASK-141-r2 builder work`; never `checkpoint: accept TASK-003`, and never a
    product commit that only speaks of a checkpoint marker without an increment's ID)."""
    clause = message.split("(", 1)[0]
    return bool(re.search(r"\bcheckpoint\b", message, re.I)) and bool(INCREMENT_RX.search(message)) and not NOT_A_SNAPSHOT_RX.search(clause)   # starts with checkpoint, names the increment, no accept/merge/release word (second pass, N2)
GH_READ = ("view", "list", "checks", "status", "diff", "search", "download", "auth", "--version", "version")
HOOK_SKIPPERS = ("commit", "push", "merge", "rebase", "am", "cherry-pick", "revert")
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def base(tok):
    return tok.lower().split("/")[-1].split("\\")[-1]


def _names_bridge_review_paths(w):
    text = " ".join(w)
    return bool(
        re.search(r"(?i)(?:^|[^A-Za-z0-9_])handoff[/\\]", text)
        or re.search(r"(?i)(?:^|[^A-Za-z0-9_])run[/\\]+review[/\\]", text)
    )


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


def in_workspace(cwd):
    """A bridge Workspace: the folder the hook runs in holds the project's status file."""
    return bool(cwd) and os.path.isfile(os.path.join(cwd, "docs", "PROJECT_STATUS.md"))


def chain_parts(text):
    """The commands a line chains with &&, ||, ; or a new line (quotes respected); a pipe is one command."""
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
        elif c in (";", "\n"):
            parts.append(buf); buf = ""
        elif c == "&" and (i == 0 or text[i - 1] not in "<>") and (i + 1 >= len(text) or text[i + 1] != ">"):
            parts.append(buf); buf = ""                        # a single & sequences in cmd and backgrounds in bash; 2>&1 is not one
        else:
            buf += c
        i += 1
    parts.append(buf)
    return [re.sub(r"^\(+|\)+$", "", p.strip()).strip() for p in parts if p.strip()]


def state_changing(w):
    """A git or gh command that changes something, as opposed to a read (`git branch --show-current`,
    `git stash list`, `git worktree list`, `git tag -l`, `git fetch` and `git remote` are reads)."""
    if is_git(w):
        sub, args = git_subcommand(w)
        if sub == "branch":
            reads = ("--list", "-l", "--contains", "--no-contains", "--merged", "--no-merged", "--points-at", "--show-current", "-r", "-a", "-v", "-vv", "--sort", "--format")
            if any(a in BRANCH_WRITES for a in args):
                return True
            return any(not a.startswith("-") for a in args) and not any(a.split("=", 1)[0] in reads for a in args)
        if sub == "stash":
            return not args or args[0] not in ("list", "show")            # a bare `git stash` pushes (N5)
        if sub in ("worktree", "tag"):
            return bool(args) and args[0] not in ("list", "show", "-l", "--list", "-v", "--verbose", "-n")
        if sub == "remote":
            return bool(args) and args[0] in ("add", "remove", "rm", "rename", "set-url", "set-head", "prune", "update")
        if sub == "config":
            return any(a == "core.hookspath" for a in (x.lower() for x in args)) and not any(a.startswith("--get") for a in args)
        return sub in STATE_GIT
    if base(w[0]) in ("gh", "gh.exe"):
        group, sub, _ = gh_words(w)
        return bool(group) and group not in GH_READ and sub not in GH_READ
    return False


def chain_reason(command, cwd):
    """Inside a Workspace, a chain carrying a state change or wrapped in cd is refused (rule 8)."""
    if not in_workspace(cwd):
        return None
    parts = chain_parts(strip_heredocs(command))
    if len(parts) < 2:
        return None
    heads = [strip_prefix(words(p)) for p in parts]
    heads = [h for h in heads if h]
    for h in list(heads):
        if base(h[0]) == "eval" and len(h) > 1:            # eval "git add -A && git commit": the string is the chain
            heads += [strip_prefix(words(p)) for p in chain_parts(" ".join(h[1:]))]
    if heads and base(heads[0][0]) == "cd":
        return "a command wrapped in cd (rule 8: never wrap a command in cd; run it with the path it needs, or git -C)"
    for w in heads:
        if state_changing(w):
            return "a chain of %d commands carrying %s (rule 8: one command per call, never chained with &&, ; or ||; the allowlist and the guard read one command, and a chain once built an increment on a merged branch)" % (len(parts), " ".join(w[:2]))
    return None


def strip_heredocs(text):
    """A here-document's body is data (a commit message) unless a shell reads it: then it is
    that shell's script, and its lines are checked as commands."""
    def repl(m):
        first, body = m.group(0).split("\n", 1)
        line = text[:m.start()].rsplit("\n", 1)[-1] + first
        head = strip_prefix(words(line.split("<<", 1)[0]))
        if head and base(head[0]) in WRAPPER_SHELLS:
            return "\n" + body
        return first
    return HEREDOC_RX.sub(repl, text)


def words(command):
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def shell_inner(w):
    """The command a wrapper shell runs, as one string, quoted or not: for cmd and the Bourne
    shells everything after /c, /k, -c or a combined short flag holding c (bash -lc, -ce); for
    PowerShell everything after -Command (any abbreviation) or -File, or, without either, the
    rest of the line after its switches; ENCODED for an encoded command; None for nothing."""
    ps = base(w[0]).replace(".exe", "") in ("powershell", "pwsh")
    i = 1
    while i < len(w):
        t = w[i].lower()
        if ps:
            if t in ("-encodedcommand", "-ec", "-enc", "-e"):
                return ENCODED
            if (len(t) >= 2 and "-command".startswith(t)) or t.startswith("-file") or t == "-f":
                return " ".join(w[i + 1:]) or None
            if t.startswith("-"):
                i += 2 if t in PS_VALUE_SWITCHES else 1
                continue
            return " ".join(w[i:]) or None
        if t in PROGRAM_AFTER or re.match(r"^-[a-z]*c[a-z]*$", t):
            return " ".join(w[i + 1:]) or None
        i += 1
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
        if tok in ("&", ".", "{", "}", "then", "do", "else", "elif", "if", "while", "until", "!"):
            i += 1
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok):
            i += 1
            continue
        name = tok.replace(".exe", "")
        if name in ("xargs", "env", "nice", "nohup", "stdbuf", "time", "sudo", "command", "builtin", "exec", "timeout"):
            vals = VALUE_OPTIONS.get(name, ())
            i += 1
            while i < len(w) and (w[i].startswith("-") or (name == "xargs" and (w[i].isdigit() or w[i] == "{}"))):
                opt = w[i]
                i += 1
                if opt in vals and i < len(w):
                    i += 1                           # the option's value (xargs -I %, nice -n 10, timeout -s KILL)
            if name == "timeout" and i < len(w):
                i += 1                               # the duration
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


def commit_message(args, command):
    """The message of a git commit: `-m <value>`, `--message=<value>`, or the first line of a
    here-document the command feeds it (the app's own commit form)."""
    msg = None
    for i, a in enumerate(args):                           # git's subject is the FIRST -m's first line (third pass, T5)
        if a in ("-m", "--message") and i + 1 < len(args):
            msg = args[i + 1]
            break
        if a.startswith("--message="):
            msg = a.split("=", 1)[1]
            break
    if msg is None:
        msg = ""
    if not msg.strip() or "<<" in msg or "$(" in msg:
        for m in HEREDOC_RX.finditer(command):
            body = m.group(0).split("\n", 1)[1]
            lines = [l for l in body.splitlines() if l.strip() and not re.match(r"^\w+\s*$", l)]
            if lines:
                return lines[0].strip()
    return msg.strip()


def in_worktree(w, cwd):
    """A commit made inside a builder's worktree (`-C ../Worktrees/x`, or a cwd under Worktrees/)."""
    paths = [cwd or ""] + [w[i + 1] for i, a in enumerate(w) if a == "-C" and i + 1 < len(w)]
    return any(re.search(r"[\\/]Worktrees[\\/]", p) for p in paths)


def check(command, cwd=None):
    """Return the reason to refuse, or None."""
    command = re.sub(r"\\\r?\n|`\r?\n", " ", command)                     # a line continued with \ or a PowerShell backtick is one line
    if re.search(r"\bgh\s+api\s+graphql\b[^\n]*(\$\(|`)", command):
        return "gh api graphql with a query built by a command substitution, which the guard cannot read (write the query on the command line)"
    r = chain_reason(command, cwd)
    if r:
        return r
    for simple in split_commands(strip_heredocs(command)):
        w = strip_prefix(words(simple))
        if not w:
            continue
        head = base(w[0])
        if re.search(r"(^|\s)HUSKY=0(\s|$)", simple) and re.search(r"\bgit\s+(commit|push|merge)\b", simple):
            return "HUSKY=0 switches the hook runner off (a commit that skips its checks; rule 4)"
        if head == "eval" and len(w) > 1:
            r = check(" ".join(w[1:]), cwd)
            if r:
                return r
        if head in WRAPPER_SHELLS:
            inner = shell_inner(w)
            if inner is ENCODED:
                return "an encoded PowerShell command, which the guard cannot read"
            if inner:
                r = check(inner, cwd)
                if r:
                    return r
        if head in ("find", "find.exe") and any(t in ("-exec", "-execdir", "-ok") for t in w):
            j = next(k for k, t in enumerate(w) if t in ("-exec", "-execdir", "-ok"))
            inner = " ".join(t for t in w[j + 1:] if t not in (";", "+", "{}"))
            r = check(inner, cwd) if inner else None
            if r:
                return r
        if base(w[0]) == "cursor-agent" and _names_bridge_review_paths(w):
            return "cursor-agent with handoff/ or run/review/ in its arguments must run through python ~/.claude/cursor-bridge/bridge-run.py"
        started = w[0] if around_the_shim(w[0]) else (program_behind(w) if head in SHELLS else None)
        if started and around_the_shim(started):
            return "starting the Cursor agent as %s, around the bridge's shim (KP-038); start it as cursor-agent, or through bridge-run.py" % started
        if is_git(w):
            helpful = "--help" in w[1:] or "-h" in w[1:]      # git runs nothing with these, in any position
            for a in w:
                if ALIAS_RX.match(a) or (a.lower().startswith("alias.") and re.search(r"worktree\s+remove|pr\s+merge|push\b.*(--force|--forc|-f\b|\+)", a, re.I)):
                    return "a git alias that defines a refused command (%s)" % a[:60]
            sub, args = git_subcommand(w)
            if any(re.match(r"^core\.hookspath=", a, re.I) for a in w) and not helpful:
                return "git -c core.hooksPath=... (the checks a commit runs are switched off; rule 4)"
            if sub == "config" and not helpful and any(a.lower() == "core.hookspath" for a in args) and not any(a.startswith("--get") for a in args):
                value = next((a for a in args[args.index(next(x for x in args if x.lower() == "core.hookspath")) + 1:] if not a.startswith("-")), "")
                norm = os.path.normpath(os.path.expanduser(value)).replace("\\", "/") if value else ""
                if "--unset" in args or value.lower() in ("/dev/null", "nul", "") or os.path.isabs(norm) or norm.startswith("..") or norm.lower() in ("/dev/null", "nul"):
                    return "git config core.hooksPath %s (the checks a commit runs are switched off; rule 4)" % (value or "--unset")
            if sub in HOOK_SKIPPERS and not helpful:
                message = commit_message(args, command)
                snapshot = snapshot_subject(message) or (bool(re.search(r"\bhand-off\b", message, re.I)) and in_worktree(w, cwd))
                for a in args:
                    if (a == "--no-verify" or (sub == "commit" and re.match(r"^-[A-Za-z]*n[A-Za-z]*$", a))) and not snapshot:
                        return "git %s %s (a commit that skips its checks; the merge policy allows it only for the checkpoint commit, whose subject says `checkpoint` and names the increment before any parenthesis without an accept, merge or release word, and for a builder's hand-off snapshot inside a worktree)" % (sub, a)
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
            if group == "alias" and sub in ("set", "import"):
                expansion = (args[-1] if args else "").strip("'\"").lstrip("!").strip()   # the last word is the expansion
                if sub == "import" or re.match(r"^(pr\s+merge|api)\b", expansion) or "worktree" in expansion:
                    return "a gh alias for a merge or an api call (%s)" % " ".join(args)[:60]
            if group == "api":
                method = "GET"
                for i, a in enumerate(w):
                    if a in ("-X", "--method") and i + 1 < len(w):
                        method = w[i + 1].upper()
                    elif a.startswith("--method=") or (a.startswith("-X") and len(a) > 2):
                        method = a.split("=", 1)[1].upper() if "=" in a else a[2:].upper()   # -XPUT, -X=PUT
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
