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

A command behind a wrapper shell (`bash -c`, `cmd /c`, `powershell -Command`), quoted or not, is
checked as the command it is when the guard can read that wrapper's options; a single `&` and the
PowerShell call operator `&` separate commands; nested shell forms (`$(`, backticks,
here-documents, subshells, globs) are refused as unreadable; a `git -c alias.<x>=...` whose
value starts with `worktree`, `pr`, `push`, `api` or `!` is refused, and so is a `gh alias set`
for a merge; an abbreviated `--forc` counts as `--force`, as it does for git; `--help` exempts a
`gh pr merge` only when it is not the value of a flag such as `--subject`. A here-document
read by a shell (`bash <<EOF`) is that shell's script and is checked; one read by any other
program (a commit message) is data. `powershell` without `-Command` runs the rest of its line,
`-com` abbreviates `-Command`, `.` runs a program as `&` does, `find -exec` runs its command,
and `-XPUT` is a method: all read as what they run. An encoded PowerShell command and a
GraphQL query read from a file are refused unread.
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

It reads one flat grammar (plain words, quotes, redirections, wrappers with option tables)
and refuses every other form as unreadable; within that grammar, chains, wrappers and quoting
do not hide the action, and `git commit -m "never use --force"` is not refused. Deny rules in
settings.bridge.json cover the common spellings as a second layer; this hook is the one
that reads the whole command.

Registered by bridge-install.py from settings.bridge.json (hooks.PreToolUse, matcher
"Bash|PowerShell"). Reads the hook's JSON on stdin; exit 2 with the reason on stderr blocks
the call (documented), exit 0 lets it through. An exception raised while checking a command
refuses it (exit 2) with an internal-error reason; input that is not the hook's JSON still
passes. ASCII-only on purpose. Never writes.
"""
import json
import os
import re
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


READ_DEPTH_BOUND = 64



READ_CACHE = {}

BASH_RESERVED = frozenset("if then else elif fi case esac for select while until do done in function time coproc".split() + ["{", "}", "!", "[[", "]]"])
BASH_OK_BUILTINS = frozenset(("cd", "echo", "pwd", "true", "false", ":", "exit", "type", "printf"))
BASH_WRAPPER_CMDS = frozenset(("eval", "exec", "command", "builtin"))
REFUSED_CMD_WORDS = frozenset(("xargs", "start", "wsl", "mintty", "winpty", "strace", "dash", "zsh", "ksh", "fish", "csh", "tcsh", "ash", "busybox"))
REFUSED_BUILTINS = frozenset(
    ". : [ alias bg bind break builtin caller declare dirs disown enable eval exec export fc fg getopts hash help history jobs kill let local logout mapfile popd pushd read readarray readonly return set shift shopt source suspend test times trap typeset ulimit umask unalias unset wait".split()
) - BASH_OK_BUILTINS - BASH_WRAPPER_CMDS
ENV_OPTS = frozenset(("-i", "-0", "--ignore-environment", "--null", "-u", "--unset", "-C", "--chdir"))
ENV_BAD = frozenset(("-S", "--split-string"))
NICE_OPTS = frozenset(("-n", "--adjustment"))
STDBUF_OPTS = frozenset(("-i", "-o", "-e", "--input=", "--output=", "--error="))
TIMEOUT_OPTS = frozenset(("-s", "--signal", "-k", "--kill-after", "--preserve-status", "--foreground", "-v", "--verbose"))
SETSID_OPTS = frozenset(("-c", "-f", "-w"))
SUDO_OPTS = frozenset(("-u", "-g", "--user", "--group"))
EXEC_OPTS = frozenset(("-a", "-c", "-l"))
COMMAND_OPTS = frozenset(("-p", "-v", "-V"))
BASH_SH_OPTS = frozenset(("-c", "--login", "--noprofile", "--norc", "--"))
BASH_SH_FLAGS = frozenset("lexuvc")
CMD_OK_SWITCH = frozenset(("/c", "/k", "/r", "/d", "/s", "/q", "//c", "//k", "//r", "//d", "//s", "//q"))
CMD_BAD_BUILTIN = frozenset(b.lower() for b in "assoc break call chdir cls color copy date del endlocal erase exit for ftype goto if md mklink pause popd prompt pushd rd rem ren rename rmdir set setlocal shift start time title verify vol".split()) - frozenset(("dir", "echo", "type", "cd", "ver", "chdir", "mkdir"))
PS_VERBS = frozenset(v.lower() for v in "Add Approve Assert Backup Block Checkpoint Clear Close Compare Complete Compress Confirm Connect Convert Copy Debug Deny Disable Disconnect Dismount Edit Enable Enter Exit Expand Export Find Format Get Grant Group Hide Import Initialize Install Invoke Join Limit Lock Measure Merge Mount Move New Open Optimize Out Ping Pop Protect Publish Push Read Receive Redo Register Remove Rename Repair Request Reset Resize Resolve Restart Restore Resume Revoke Save Search Select Send Set Show Skip Split Start Step Stop Submit Suspend Switch Sync Test Trace Unblock Undo Uninstall Unlock Unprotect Unpublish Unregister Update Use Wait Watch Write".split())
PS_CMDLETS = frozenset(x.lower() for x in "Get-ChildItem Get-Content Get-Item Get-ItemProperty Get-Location Get-Command Get-Help Get-Process Get-Service Get-Date Get-FileHash Test-Path Select-String Select-Object Sort-Object Measure-Object Format-List Format-Table Out-String Out-Host Write-Output Write-Host Compare-Object Resolve-Path Join-Path Split-Path ConvertTo-Json ConvertFrom-Json Set-Location Push-Location Pop-Location".split())
PS_ALIASES_OK = frozenset(x.lower() for x in "cat cd chdir compare diff dir echo fl ft gc gci gcm gi gl gp gps gsv help ls man measure oh popd ps pushd pwd rvpa select sl sls sort type write".split())
PS_ALIASES_BAD = frozenset(x.lower() for x in "% ? ac asnp CFS clc clear clhy cli clp cls clv cnsn copy cp cpi cpp curl cvpa dbp del dnsn ebp epal epcsv epsn erase etsn exsn fc fhx foreach fw gal gbp gcb gcs gdr ghy gin gjb gm gmo gpv group gsn gsnp gtz gu gv gwmi h history icm iex ihy ii ipal ipcsv ipmo ipsn irm ise iwmi iwr kill lp md mi mount move mp mv nal ndr ni nmo npssc nsn nv ogv r rbp rcjb rcsn rd rdr ren ri rjb rm rmdir rmo rni rnp rp rsn rsnp rujb rv rwmi sajb sal saps sasv sbp sc scb set shcm si sleep sp spjb spps spsv start stz sujb sv swmi tee trcm wget where wjb".split())
GH_API_OPTS = frozenset(("-X", "--method", "-H", "--header", "-f", "-F", "--field", "--raw-field", "-q", "--jq", "-t", "--template", "--cache", "--input", "-p", "--preview"))


def _cannot(msg):
    return "the guard cannot read the command: %s" % msg


def _mode_name(tool):
    return "powershell" if tool == "PowerShell" else "bash"


def _snapshot(text, mode="bash"):
    key = (text, mode)
    if key not in READ_CACHE:
        READ_CACHE[key] = read_commands(text, mode=mode)
    return READ_CACHE[key]


def read_commands(text, mode="bash"):
    """One flat read of a command line (R-082 round 5); never raises."""
    try:
        if mode == "cmd":
            return _read_cmd(text)
        if mode == "powershell":
            return _read_powershell(text)
        return _read_bash(text)
    except Exception as ex:
        return {"unreadable": _cannot("internal error (%s)" % type(ex).__name__), "commands": [], "chain": [], "chain_wds": [], "gh_amp": None}


def _ps_norm_switch(tok):
    t = tok
    for dash in ("\u2013", "\u2014", "\u2015"):
        if t.startswith(dash):
            t = "-" + t[len(dash):]
            break
    if t.startswith("//"):
        t = "-" + t[2:]
    elif t.startswith("/") and not t.startswith("//"):
        t = "-" + t[1:]
    return t.lower()


def _verb_noun(tok):
    if "." in tok or "/" in tok or "\\" in tok:
        return False
    parts = tok.split("-", 1)
    if len(parts) != 2:
        return False
    return parts[0].lower() in PS_VERBS


def _assignment_name(tok):
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=", tok)
    return m.group(1) if m else None


def _skip_assignments(words):
    i = 0
    while i < len(words):
        name = _assignment_name(words[i])
        if name:
            if name.upper().startswith("GIT_CONFIG"):
                return _cannot("an assignment whose name begins GIT_CONFIG"), i
            i += 1
            continue
        break
    return None, i


def _cmd_word_refusal(words, mode="bash"):
    bad, i = _skip_assignments(words)
    if bad:
        return bad
    if i >= len(words):
        return None
    w = words[i]
    lw = base(w)
    if any(w == x or w.startswith(x + "=") for x in ("--config-env",)):
        return _cannot("an option --config-env")
    if lw.replace(".exe", "") in REFUSED_CMD_WORDS:
        return _cannot("a launcher or shell (%s)" % lw)
    if mode == "bash":
        if lw in BASH_RESERVED:
            return _cannot("a reserved word (%s)" % lw)
        if lw == "printf" and any(words[j] == "-v" or words[j].startswith("-v") for j in range(i + 1, len(words))):
            return _cannot("a builtin (printf -v)")
        if lw in REFUSED_BUILTINS:
            return _cannot("a builtin (%s)" % lw)
        if lw in ("bash", "sh") and _bash_reads_stdin(words, i):
            return _cannot("a shell that reads commands from standard input")
        if lw in ("bash", "sh") and _bash_interactive(words, i):
            return _cannot("interactive bash")
    return None


def _bash_reads_stdin(words, i):
    opts, rest, has_c, script = _parse_bash_sh_words(words[i + 1:])
    if has_c:
        return False
    return script is None


def _bash_interactive(words, i):
    opts, rest, has_c, script = _parse_bash_sh_words(words[i + 1:])
    for o in opts:
        if o == "-i" or (o.startswith("-") and not o.startswith("--") and "i" in o[1:]):
            return True
    return False


def _parse_bash_sh_words(words):
    opts, i, has_c, script = [], 0, False, False
    while i < len(words):
        t = words[i]
        if t == "--":
            i += 1
            break
        if t.startswith("+"):
            if t in ("+x", "+e") or all(c in BASH_SH_FLAGS for c in t[1:]):
                opts.append(t); i += 1; continue
            return [], None, False, _cannot("an unknown bash option")
        if t.startswith("-"):
            if t == "-c":
                has_c = True; opts.append(t); i += 1; break
            if len(t) > 1 and not t.startswith("--") and all(c in BASH_SH_FLAGS for c in t[1:]):
                if "c" in t[1:]:
                    has_c = True; opts.append(t); i += 1; break
                opts.append(t); i += 1; continue
            if t in BASH_SH_OPTS:
                opts.append(t); i += 1; continue
            return [], None, False, _cannot("an unknown bash option")
        break
    rest = words[i:] if i < len(words) else []
    if has_c:
        return opts, rest, has_c, None
    return opts, rest, has_c, rest[0] if rest else None


def _bash_inner_string(words):
    i, has_c = 1, False
    while i < len(words):
        t = words[i]
        if t == "--":
            i += 1
            break
        if t.startswith("+"):
            if t in ("+x", "+e") or all(c in BASH_SH_FLAGS for c in t[1:]):
                i += 1
                continue
            return None
        if t.startswith("-"):
            if t == "-c":
                has_c = True
                i += 1
                continue
            if len(t) > 1 and not t.startswith("--") and all(c in BASH_SH_FLAGS for c in t[1:]):
                if "c" in t[1:]:
                    has_c = True
                i += 1
                continue
            if t in BASH_SH_OPTS:
                i += 1
                continue
            return None
        break
    if not has_c or i >= len(words):
        return None
    return " ".join(words[i:])


def _parse_env_words(words):
    i, opts = 1, []
    vals = ENV_OPTS
    while i < len(words):
        t = words[i]
        if t in ENV_BAD:
            return _cannot("env -S or --split-string")
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t):
            i += 1; continue
        if not t.startswith("-"):
            break
        eq = t.split("=", 1)
        opt = eq[0]
        if opt in ENV_OPTS:
            opts.append(opt)
            if "=" in t:
                i += 1
            elif opt in ("-u", "--unset", "-C", "--chdir") and i + 1 < len(words):
                i += 2
            else:
                i += 1
            continue
        return _cannot("an unknown env option")
    return None


def _wrapper_opt_refusal(words, depth):
    if not words:
        return None
    head = base(words[0]).replace(".exe", "")
    if head == "env":
        return _parse_env_words(words)
    if head == "xargs":
        return _cannot("xargs")
    if head == "nice":
        return _scan_simple_opts(words, NICE_OPTS, ("-n", "--adjustment"))
    if head == "stdbuf":
        return _scan_glue_opts(words, STDBUF_OPTS)
    if head == "timeout":
        return _scan_simple_opts(words, TIMEOUT_OPTS, ("-s", "--signal", "-k", "--kill-after"))
    if head == "setsid":
        return _scan_simple_opts(words, SETSID_OPTS, ())
    if head == "sudo":
        return _scan_simple_opts(words, SUDO_OPTS, ("-u", "-g", "--user", "--group"))
    if head == "exec":
        return _scan_simple_opts(words, EXEC_OPTS, ("-a",))
    if head == "command":
        return _scan_simple_opts(words, COMMAND_OPTS, ())
    if head in ("bash", "sh"):
        opts, rest, has_c, err = _parse_bash_sh_words(words[1:])
        if isinstance(err, str) and err.startswith("the guard cannot read"):
            return err
    if head in ("cmd", "cmd.exe"):
        return _parse_cmd_wrapper(words)
    if head in ("powershell", "pwsh", "powershell.exe", "pwsh.exe"):
        return _parse_ps_wrapper(words)
    return None


def _scan_simple_opts(words, allowed, with_val):
    i = 1
    while i < len(words):
        t = words[i]
        if not t.startswith("-"):
            break
        opt = t.split("=", 1)[0]
        if opt not in allowed:
            return _cannot("an unknown wrapper option")
        if opt in with_val and "=" not in t and i + 1 < len(words):
            i += 2
        else:
            i += 1
    return None


def _scan_glue_opts(words, prefixes):
    i = 1
    while i < len(words):
        t = words[i]
        if not t.startswith("-"):
            break
        if not any(t == p or t.startswith(p) for p in prefixes):
            return _cannot("an unknown wrapper option")
        if not any(t.startswith(p) for p in prefixes if p.endswith("=")) and "=" not in t and i + 1 < len(words):
            i += 2
        else:
            i += 1
    return None


def _parse_cmd_wrapper(words):
    i = 1
    inner_start = None
    while i < len(words):
        t = words[i]
        tl = t.lower()
        if tl in CMD_OK_SWITCH:
            inner_start = i + 1
            i += 1
            break
        if tl.startswith("/") or tl.startswith("//"):
            if tl in ("/v", "//v", "/e", "/f", "/a", "/u", "/t") or tl.startswith("/v:") or tl.startswith("//v:"):
                return _cannot("an unknown cmd switch")
            if len(t) >= 3 and tl[:3] in ("/c", "//c", "/k", "//k", "/r", "//r") and len(t) > 3:
                return _cannot("a switch glued to its command")
            return _cannot("an unknown cmd switch")
        return _cannot("an unknown cmd switch")
    if inner_start is None:
        return _cannot("cmd without /c, /k or /r")
    return None


def _parse_ps_wrapper(words):
    i, seen_cmd, seen_file = 1, False, False
    while i < len(words):
        raw = words[i]
        t = _ps_norm_switch(raw)
        if t in ("-e", "-ec") or t.startswith("-en") or t.startswith("-encodedcommand") or (t.startswith("//") and _ps_norm_switch(raw).startswith("-en")):
            return "an encoded PowerShell command, which the guard cannot read"
        if len(t) >= 2 and "-command".startswith(t) or t.startswith("-command"):
            seen_cmd = True
            i += 1
            break
        if t.startswith("-file") or t == "-f":
            seen_file = True
            i += 1
            break
        if t in ("-noprofile", "-nop", "-noninteractive", "-noni", "-nologo", "-sta", "-mta", "-noexit"):
            i += 1; continue
        if t in PS_VALUE_SWITCHES or any(t == x or t.startswith(x + "=") for x in PS_VALUE_SWITCHES):
            i += 2 if "=" not in raw and i + 1 < len(words) else 1
            continue
        if t.startswith("-"):
            return _cannot("an unknown PowerShell switch")
        break
    return None


def _gh_api_head(words):
    w = strip_prefix(words)
    if not w or base(w[0]) not in ("gh", "gh.exe"):
        return False
    j = 1
    while j < len(w):
        if w[j] == "api":
            return True
        if w[j] in ("-R", "--repo", "--hostname"):
            j += 2; continue
        if w[j].startswith("-"):
            j += 1; continue
        return False
    return False


def _brace_in_word_ok(prefix, c, nxt):
    if c == "{":
        j = 2
        while j < len(nxt) and nxt[j] in "[]A-Za-z0-9_-":
            j += 1
        return j < len(nxt) and nxt[j] == "}"
    return True


def _read_bash(text):
    unreadable, gh_amp = None, None
    n = len(text)

    def refuse(msg):
        nonlocal unreadable
        if unreadable is None:
            unreadable = _cannot(msg)

    quote, wbuf = None, []
    words, raw_parts = [], []
    commands, chain, chain_wds = [], [], []
    seg_words, piped = [], False
    last_amp_glued = False
    i, bs_run = 0, 0
    in_comment = False
    chain_buf = []

    def in_sq():
        return quote == "s"

    def in_dq():
        return quote == "d"

    def flush_word():
        nonlocal wbuf, last_amp_glued, words
        if not wbuf:
            return
        words.append("".join(wbuf))
        wbuf = []

    def finish_cmd(sep):
        nonlocal piped, seg_words, last_amp_glued, gh_amp, words, commands
        flush_word()
        if not words:
            return
        for w in words:
            if w in ("--config-env",) or w.startswith("--config-env="):
                refuse("an option --config-env")
                return
        cw = list(words)
        commands.append({"words": cw, "sep": sep, "pipe": piped, "last_amp": last_amp_glued})
        seg_words.append(cw)
        if _gh_api_head(cw) and last_amp_glued:
            gh_amp = "an unquoted & in a gh api argument (quote the URL or put each query field in its own quoted argument)"
        wr = _wrapper_opt_refusal(cw, 0)
        if wr:
            refuse(wr.split(": ", 1)[-1] if ": " in wr else wr)
        cr = _cmd_word_refusal(cw, "bash")
        if cr:
            refuse(cr.split(": ", 1)[-1] if ": " in cr else cr)
        words[:] = []
        piped = False
        last_amp_glued = False

    def finish_chain(sep):
        nonlocal seg_words, chain_buf, chain, chain_wds
        finish_cmd(sep)
        if seg_words:
            chain.append("".join(chain_buf).strip() or " ".join(" ".join(x) for x in seg_words))
            chain_wds.append(list(seg_words[0]))
            seg_words = []
            chain_buf = []

    while i < n:
        if unreadable:
            break
        if in_comment:
            if text[i] == "\n":
                in_comment = False
                finish_chain("\n")
            i += 1
            continue
        c = text[i]
        chain_buf.append(c)
        raw_parts.append(c)
        if quote == "s":
            if c == "'":
                quote = None
            else:
                wbuf.append(c)
            i += 1
            continue
        if quote == "d":
            if c == "\\" and i + 1 < n:
                nxt = text[i + 1]
                if nxt in '"\\':
                    wbuf.append(nxt); i += 2; continue
                if nxt == "\n":
                    i += 2; continue
                wbuf.append(c); i += 1; continue
            if c in "$`":
                refuse("a substitution inside double quotes")
                break
            if c == '"':
                quote = None; i += 1; continue
            wbuf.append(c); i += 1; continue
        if c == "\\" and i + 1 < n:
            nxt = text[i + 1]
            if nxt == "`":
                refuse("a backtick command")
                break
            if nxt in "\r\n":
                j = i
                while j < n and text[j] == "\\":
                    j += 1
                if (j - i) % 2 == 1:
                    while j < n and text[j] in "\r\n":
                        j += 1
                    i = j
                    continue
            wbuf.append(nxt); i += 2; continue
        if c == "`":
            refuse("a backtick command")
            break
        if c == "#" and not wbuf:
            in_comment = True; i += 1; continue
        if c == "'":
            quote = "s"; i += 1; continue
        if c == '"':
            quote = "d"; i += 1; continue
        if text.startswith("$(", i) or c == "$":
            refuse("a command substitution")
            break
        if text.startswith("<<", i):
            refuse("a here-document")
            break
        if not in_dq() and text.startswith("<(", i):
            refuse("process substitution")
            break
        if not in_dq() and text.startswith(">(", i):
            refuse("process substitution")
            break
        if c in "()":
            refuse("parentheses")
            break
        if c in "*?[":
            refuse("a glob character (quote it)")
            break
        if c in "{}":
            rest = text[i:]
            if c == "{" and re.match(r"^\{[A-Za-z_][A-Za-z0-9_]*\}>", rest):
                refuse("a named file descriptor redirection")
                break
            if c == "{" and not (rest.startswith("{}") or re.match(r"^\{[A-Za-z0-9_-]+\}", rest)):
                refuse("brace expansion")
                break
            if c == "}" and "}" not in "".join(wbuf) and wbuf:
                pass
        rr = _try_redirect_bash(text, i, refuse)
        if rr is not None:
            flush_word()
            i = rr
            continue
        if i + 1 < n and text[i:i + 2] in ("&&", "||"):
            finish_chain(text[i:i + 2]); i += 2; continue
        if c in (";", "\n"):
            finish_chain(c); i += 1; continue
        if c == "|" or text.startswith("|&", i):
            finish_cmd("|")
            piped = True
            i += 2 if text.startswith("|&", i) else 1
            continue
        if c == "&" and (i + 1 >= n or text[i + 1] not in ">&"):
            glued = bool(wbuf)
            last_amp_glued = glued
            finish_chain("&")
            i += 1
            continue
        if c in " \t\r":
            flush_word(); i += 1; continue
        wbuf.append(c); i += 1
    if unreadable is None and quote:
        refuse("an unclosed quote")
    if unreadable is None:
        flush_word()
        if words:
            finish_cmd(None)
        if seg_words:
            chain.append("".join(chain_buf).strip() or " ".join(" ".join(x) for x in seg_words))
            chain_wds.append(list(seg_words[-1]))
    if not chain and commands:
        chain = [" ".join(" ".join(c["words"]) for c in commands)]
        chain_wds = [commands[0]["words"]]
    return {"unreadable": unreadable, "commands": commands, "chain": chain, "chain_wds": chain_wds, "gh_amp": gh_amp, "text": text}


def _skip_redirect_target_bash(text, j, n, refuse):
    if j >= n:
        refuse("a redirection with no target")
        return n
    while j < n and text[j] in " \t":
        j += 1
    if j >= n:
        refuse("a redirection with no target")
        return n
    if text[j] in "'\"":
        q = text[j]
        j += 1
        while j < n and text[j] != q:
            if q == '"' and text[j] in "$`":
                refuse("a substitution in a redirection target")
                return n
            if q == '"' and text.startswith("$(", j):
                refuse("a substitution in a redirection target")
                return n
            j += 1
        return j + 1 if j < n else n
    if text[j] in "$`(":
        refuse("a redirection target")
        return n
    if text.startswith("<&", j) or text.startswith(">&", j):
        k = j + 2
        if k < n and (text[k].isdigit() or text[k] == "-"):
            while k < n and text[k].isdigit():
                k += 1
            return k
    while j < n and text[j] not in " \t\n\r;|&":
        j += 1
    return j


def _try_redirect_bash(text, i, refuse):
    n = len(text)
    m, k = 0, i
    while k < n and text[k].isdigit():
        k += 1
    start = k
    if text.startswith(">&-", start):
        m = 4
    elif text.startswith("&>>", start):
        m = 3
    elif text.startswith(">>", start):
        m = 2
    elif text.startswith("<<", start):
        return None
    elif text.startswith("<&", start) or text.startswith(">&", start):
        m = 2
    elif text.startswith("<>", start) or text.startswith(">|", start):
        m = 2
    elif text.startswith("&>", start):
        m = 2
    elif text.startswith("2>&1", start):
        m = 4
    elif text.startswith("2>", start):
        m = 2
    elif start < n and text[start] in "<>":
        m = 1
    else:
        return None
    j = _skip_redirect_target_bash(text, start + m, n, refuse)
    return j


def _read_powershell(text):
    unreadable, gh_amp = None, None
    n = len(text)

    def refuse(msg):
        nonlocal unreadable
        if unreadable is None:
            unreadable = _cannot(msg)

    quote, wbuf, words = None, [], []
    commands, chain, chain_wds, seg_words = [], [], [], []
    i = 0

    def flush_word():
        nonlocal wbuf, words
        if wbuf:
            words.append("".join(wbuf))
            wbuf.clear()

    def finish_cmd(sep):
        nonlocal words, commands, seg_words, unreadable
        flush_word()
        if not words:
            return
        cw = list(words)
        commands.append({"words": cw, "sep": sep, "pipe": False, "last_amp": False})
        seg_words.append(cw)
        wr = _wrapper_opt_refusal(cw, 0)
        if wr and unreadable is None:
            unreadable = wr
        cr = _cmd_word_refusal(cw, "powershell")
        if cr and unreadable is None:
            unreadable = cr
        elif unreadable is None:
            wp = strip_prefix(cw)
            if wp:
                tl = wp[0].lower()
                if tl in PS_ALIASES_BAD or tl in ("iex", "invoke-expression", "start", "set-alias"):
                    unreadable = _cannot("a cmdlet or alias (%s)" % wp[0])
                elif "\\" in wp[0]:
                    tail = wp[0].split("\\")[-1].lower()
                    if tail in PS_ALIASES_BAD or tail == "invoke-expression":
                        unreadable = _cannot("a module-qualified cmdlet (%s)" % wp[0])
                elif _verb_noun(wp[0]) and tl not in PS_CMDLETS and tl not in PS_ALIASES_OK:
                    unreadable = _cannot("a cmdlet (%s)" % wp[0])
        words.clear()

    def finish_chain(sep):
        nonlocal chain, chain_wds, seg_words
        finish_cmd(sep)
        if seg_words:
            chain.append(" ".join(" ".join(x) for x in seg_words))
            chain_wds.append(list(seg_words[0]))
            seg_words.clear()

    while i < n and unreadable is None:
        c = text[i]
        if ord(c) > 127 and c not in "\t\n":
            refuse("a non-ASCII character")
            break
        if quote == "s":
            if c == "'" and i + 1 < n and text[i + 1] == "'":
                wbuf.append("'"); i += 2; continue
            if c == "'":
                quote = None; i += 1; continue
            wbuf.append(c); i += 1; continue
        if quote == "d":
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    wbuf.append('"'); i += 2; continue
                quote = None; i += 1; continue
            if c in "$`":
                refuse("a substitution")
                break
            wbuf.append(c); i += 1; continue
        if text.startswith("<#", i):
            refuse("a block comment")
            break
        if c == "'" or c == '"':
            quote = "s" if c == "'" else "d"; i += 1; continue
        if c == "#" and not wbuf:
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "`":
            if i + 1 < n and text[i + 1] in "\r\n":
                while i < n and text[i] in "`\r\n":
                    i += 1
                continue
            refuse("a backtick")
            break
        if c == "$":
            refuse("a variable")
            break
        if c in "(){}[]":
            refuse("parentheses or braces")
            break
        if c == "@" and i + 1 < n:
            nxt = text[i + 1]
            if nxt in "({'\"":
                refuse("splatting")
                break
            if re.match(r"@[A-Za-z_][A-Za-z0-9_]*$", text[i:].split()[0] if text[i:].split() else ""):
                refuse("splatting")
                break
        if i + 1 < n and text[i:i + 2] in ("&&", "||"):
            finish_chain(text[i:i + 2]); i += 2; continue
        if c in (";", "\n"):
            finish_chain(c); i += 1; continue
        if c == "|":
            finish_cmd("|"); i += 1; continue
        if c == "&" and not wbuf:
            finish_chain("&")
            i += 1
            continue
        if c == "\r":
            if i + 1 >= n or text[i + 1] != "\n":
                refuse("a lone carriage return")
                break
            flush_word(); i += 1; continue
        if c in " \t":
            flush_word(); i += 1; continue
        if c in "&." and not wbuf and not words:
            i += 1; continue
        if text.startswith("--%", i):
            refuse("stop-parsing")
            break
        if i + 1 < n and text[i:i + 2] in (">>", "2>", "2>&1", "*>"):
            i = _try_redirect_ps(text, i) or i + 2
            continue
        if c in ">" :
            i = _try_redirect_ps(text, i) or i + 1
            continue
        wbuf.append(c); i += 1
    if unreadable is None and quote:
        refuse("an unclosed quote")
    if unreadable is None:
        finish_chain(None)
    if not chain and commands:
        chain = [" ".join(" ".join(c["words"]) for c in commands)]
        chain_wds = [commands[0]["words"]]
    return {"unreadable": unreadable, "commands": commands, "chain": chain, "chain_wds": chain_wds, "gh_amp": gh_amp, "text": text}


def _try_redirect_ps(text, i):
    for op in (">>", "2>&1", "2>", "*>", ">"):
        if text.startswith(op, i):
            j = i + len(op)
            while j < len(text) and text[j] in " \t":
                j += 1
            while j < len(text) and text[j] not in " \t\n\r;|":
                j += 1
            return j
    return None


def _read_cmd(text):
    for ch in "\"'\\^%!`()\r\n":
        if ch in text:
            return {"unreadable": _cannot("cmd inner command character %s" % ch), "commands": [], "chain": [], "chain_wds": [], "gh_amp": None}
    parts, buf, commands = [], [], []
    i, n = 0, len(text)
    while i <= n:
        if i == n or text[i] in "&":
            if buf:
                parts.append("".join(buf).strip())
                buf = []
            if i < n and text[i] == "&":
                i += 2 if i + 1 < n and text[i + 1] == "&" else 1
                continue
        if i < n:
            buf.append(text[i])
        i += 1
    for part in parts:
        if not part:
            continue
        words = part.split()
        if not words:
            continue
        bw = base(words[0]).lower()
        if bw in CMD_BAD_BUILTIN:
            return {"unreadable": _cannot("a cmd builtin (%s)" % bw), "commands": [], "chain": [], "chain_wds": [], "gh_amp": None}
        commands.append({"words": words, "sep": None, "pipe": False, "last_amp": False})
    chain_wds = [c["words"] for c in commands]
    return {"unreadable": None, "commands": commands, "chain": parts if len(parts) > 1 else ([text.strip()] if parts else []), "chain_wds": chain_wds if chain_wds else [], "gh_amp": None, "text": text}


def chain_parts(text, mode="bash"):
    p = read_commands(text, mode=mode)
    return [x for x in p.get("chain", []) if x.strip()]


def words(command, mode="bash"):
    p = read_commands(command, mode=mode)
    if p.get("unreadable"):
        return []
    cs = command.strip()
    for cmd in p.get("commands", []):
        if cmd.get("words"):
            return list(cmd["words"])
    return []


def split_commands(text, mode="bash"):
    p = read_commands(text, mode=mode)
    if p.get("unreadable"):
        return []
    out = []
    for c in p.get("commands", []):
        if c.get("words"):
            out.append(" ".join(c["words"]))
    return out


def in_workspace(cwd):
    return bool(cwd) and os.path.isfile(os.path.join(cwd, "docs", "PROJECT_STATUS.md"))


def _chain_lists(parsed, command, mode, depth):
    lists = []
    ch, cw = parsed.get("chain", []), parsed.get("chain_wds", [])
    if len(ch) >= 2:
        lists.append((ch, cw))
    for cmd in parsed.get("commands", []):
        w = strip_prefix(cmd["words"])
        if not w:
            continue
        head = base(w[0]).replace(".exe", "")
        inner = None
        inner_mode = mode
        if head == "eval" and len(w) > 1:
            inner = " ".join(w[1:])
        elif head in WRAPPER_SHELLS:
            inner = shell_inner(w)
            if inner is ENCODED:
                continue
            if head in ("powershell", "pwsh", "powershell.exe", "pwsh.exe"):
                inner_mode = "powershell"
            elif head in ("cmd", "cmd.exe"):
                inner_mode = "cmd"
        if inner and depth < READ_DEPTH_BOUND:
            sp = read_commands(inner, mode=inner_mode)
            if not sp.get("unreadable") and len(sp.get("chain", [])) >= 2:
                lists.append((sp["chain"], sp.get("chain_wds", [])))
        if head == "find" and any(x in w for x in ("-exec", "-execdir", "-ok", "-okdir")):
            for j, t in enumerate(w):
                if t in ("-exec", "-execdir", "-ok", "-okdir"):
                    clip = [x for x in w[j + 1:] if x not in (";", "+", "{}")]
                    if clip:
                        ip = read_commands(" ".join(clip), mode=mode)
                        if not ip.get("unreadable") and len(ip.get("chain", [])) >= 2:
                            lists.append((ip["chain"], ip.get("chain_wds", [])))
    return lists


def chain_reason(command, cwd, tool="Bash"):
    if not in_workspace(cwd):
        return None
    mode = _mode_name(tool)
    parsed = read_commands(command, mode=mode)
    if parsed.get("unreadable"):
        return None
    heads = [strip_prefix(w) for w in (parsed.get("chain_wds") or []) if w]
    if heads and base(heads[0][0]) == "cd":
        return "a command wrapped in cd (rule 8: never wrap a command in cd; run it with the path it needs, or git -C)"
    for ch, cw in _chain_lists(parsed, command, mode, 0):
        if len(ch) < 2:
            continue
        for pi, wds in enumerate(cw):
            w = strip_prefix(wds) if wds else []
            if w and state_changing(w):
                return "a chain of %d commands carrying %s (rule 8: one command per call, never chained with &&, ; or ||; the allowlist and the guard read one command, and a chain once built an increment on a merged branch)" % (len(ch), " ".join(w[:2]))
    return None


def leading_husky_zero(words_or_text, tool="Bash"):
    w = list(words_or_text) if isinstance(words_or_text, (list, tuple)) else words(words_or_text, mode=_mode_name(tool))
    i = 0
    while i < len(w):
        if w[i] == "HUSKY=0":
            return True
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w[i]):
            i += 1; continue
        name = base(w[i]).replace(".exe", "")
        if name in ("env", "nice", "nohup", "stdbuf", "sudo", "command", "builtin", "exec", "timeout", "setsid"):
            i += 1
            vals = VALUE_OPTIONS.get(name, ())
            while i < len(w) and w[i].startswith("-"):
                opt = w[i]; i += 1
                if opt in vals and i < len(w):
                    i += 1
            if name == "timeout" and i < len(w):
                i += 1
            if name == "env":
                while i < len(w):
                    if w[i] == "HUSKY=0":
                        return True
                    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w[i]):
                        i += 1; continue
                    if w[i].startswith("-"):
                        i += 1; continue
                    break
            continue
        break
    return False


def shell_inner(w):
    bh = base(w[0]).replace(".exe", "")
    if bh in ("bash", "sh"):
        return _bash_inner_string(w) or None
    ps = bh in ("powershell", "pwsh")
    i = 1
    while i < len(w):
        t = w[i].lower()
        if ps:
            tn = _ps_norm_switch(w[i])
            if tn in ("-e", "-ec") or tn.startswith("-en") or tn.startswith("-encodedcommand"):
                return ENCODED
            if tn == "-command" or (len(tn) >= 2 and "-command".startswith(tn)):
                return " ".join(w[i + 1:]) or None
            if tn.startswith("-file") or tn == "-f":
                return None
            if tn in ("-noprofile", "-nop", "-noninteractive", "-noni", "-nologo", "-sta", "-mta", "-noexit"):
                i += 1
                continue
            if tn.startswith("-"):
                if tn in PS_VALUE_SWITCHES or any(tn.startswith(x) for x in PS_VALUE_SWITCHES):
                    i += 2 if i + 1 < len(w) else 1
                    continue
                if len(tn) >= 2 and "-command".startswith(tn):
                    return " ".join(w[i + 1:]) or None
                i += 1
                continue
            return " ".join(w[i:]) or None
        if t in ("/c", "/k", "/r", "//c", "//k", "//r") or t == "-c" or re.match(r"^-[a-z]*c[a-z]*$", t):
            if t.startswith("/"):
                rest = " ".join(w[i + 1:])
                return rest or None
            return " ".join(w[i + 1:]) or None
        if t.startswith("-"):
            i += 1; continue
        i += 1
    return None


def gh_words(w):
    found, rest, i = [], [], 1
    while i < len(w):
        tok = w[i]
        if len(found) < 2:
            opt = tok.split("=", 1)[0]
            if opt in ("-R", "--repo", "--hostname"):
                i += 2 if "=" not in tok else 1; continue
            if tok in GH_API_OPTS:
                if "=" in tok:
                    i += 1; continue
                i += 2 if i + 1 < len(w) else 1; continue
            if opt in ("-X", "--method") and tok.startswith("-") and len(tok) > 2 and "=" not in tok:
                i += 1; continue
            if tok.startswith("-"):
                i += 1; continue
            found.append(tok)
        else:
            rest.append(tok)
        i += 1
    found += [None, None]
    return found[0], found[1], rest


def strip_prefix(w):
    i = 0
    while i < len(w):
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w[i]):
            i += 1; continue
        if w[i] in ("&", "."):
            i += 1; continue
        name = base(w[i]).replace(".exe", "")
        if name == "exec":
            i += 1
            while i < len(w) and w[i].startswith("-"):
                opt = w[i].split("=", 1)[0]
                if opt in EXEC_OPTS:
                    i += 2 if "=" not in w[i] and opt in ("-a",) and i + 1 < len(w) else 1
                else:
                    break
            continue
        if name == "stdbuf":
            i += 1
            while i < len(w) and w[i].startswith("-"):
                tok = w[i]
                ok = tok in STDBUF_OPTS or any(tok.startswith(p) for p in ("-i", "-o", "-e", "--input=", "--output=", "--error="))
                if ok:
                    if "=" not in tok and tok in ("-i", "-o", "-e") and i + 1 < len(w):
                        i += 2
                    else:
                        i += 1
                else:
                    break
            continue
        if name in ("env", "nice", "nohup", "sudo", "command", "builtin", "timeout", "setsid"):
            i += 1
            vals = VALUE_OPTIONS.get(name, ())
            while i < len(w) and w[i].startswith("-"):
                opt = w[i]; i += 1
                if opt in vals and i < len(w):
                    i += 1
            if name == "timeout" and i < len(w):
                i += 1
            continue
        break
    return w[i:]


def commit_message(args, command):
    msg = None
    for i, a in enumerate(args):
        if a in ("-m", "--message") and i + 1 < len(args):
            msg = args[i + 1]; break
        if a.startswith("--message="):
            msg = a.split("=", 1)[1]; break
    return (msg or "").strip()


def check(command, cwd=None, tool="Bash", _depth=0):
    mode = _mode_name(tool)
    return _check_one(command, cwd, tool, mode, _depth)


def _check_one(command, cwd, tool, mode, depth):
    if depth > READ_DEPTH_BOUND:
        return _cannot("nesting past the bound")
    if depth == 0:
        READ_CACHE.clear()
    parsed = read_commands(command, mode=mode)
    if parsed.get("unreadable"):
        return parsed["unreadable"]
    if parsed.get("gh_amp"):
        return parsed["gh_amp"]
    r = chain_reason(command, cwd, tool=tool)
    if r:
        return r
    for cmd in parsed.get("commands", []):
        cmd_wds = cmd["words"]
        simple = " ".join(cmd_wds)
        if leading_husky_zero(cmd_wds, tool) and re.search(r"\bgit\b.*\b(commit|push|merge)\b", simple, re.I):
            return "HUSKY=0 switches the hook runner off (a commit that skips its checks; rule 4)"
        w = strip_prefix(cmd_wds)
        if tool == "PowerShell" and w:
            j = 0
            while j < len(w) and w[j] in BASH_RESERVED:
                j += 1
            w = w[j:]
        if not w:
            continue
        head = base(w[0])
        if head == "eval" and len(w) > 1:
            r = _check_one(" ".join(w[1:]), cwd, tool, mode, depth + 1)
            if r:
                return r
        if head in WRAPPER_SHELLS:
            inner = shell_inner(w)
            if inner is ENCODED:
                return "an encoded PowerShell command, which the guard cannot read"
            if inner:
                bh = base(w[0]).replace(".exe", "")
                if bh in ("powershell", "pwsh"):
                    im = "powershell"
                elif bh in ("cmd", "cmd.exe"):
                    im = "cmd"
                elif bh in ("bash", "sh"):
                    im = "bash"
                else:
                    im = mode
                r = _check_one(inner, cwd, tool, im, depth + 1)
                if r:
                    return r
        if head in ("find", "find.exe"):
            j = 0
            while j < len(w):
                if w[j] in ("-exec", "-execdir", "-ok", "-okdir"):
                    clip = [x for x in w[j + 1:] if x not in (";", "+", "{}")]
                    first = []
                    for x in clip:
                        if x == ";":
                            break
                        first.append(x)
                    inner = " ".join(first)
                    if inner:
                        r = _check_one(inner, cwd, tool, mode, depth + 1)
                        if r:
                            return r
                j += 1
        if base(w[0]) == "cursor-agent" and _names_bridge_review_paths(w):
            return "cursor-agent with handoff/ or run/review/ in its arguments must run through python ~/.claude/cursor-bridge/bridge-run.py"
        started = w[0] if around_the_shim(w[0]) else (program_behind(w) if head in SHELLS else None)
        if started and around_the_shim(started):
            return "starting the Cursor agent as %s, around the bridge's shim (KP-038); start it as cursor-agent, or through bridge-run.py" % started
        if is_git(w):
            helpful = "--help" in w[1:] or "-h" in w[1:]
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
                skipper = hook_skipper_option(sub, args, snapshot)
                if skipper:
                    return "git %s %s (a commit that skips its checks; the merge policy allows it only for the checkpoint commit, whose subject says `checkpoint` and names the increment before any parenthesis without an accept, merge or release word, and for a builder's hand-off snapshot inside a worktree)" % (sub, skipper)
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
            if group == "api" and sub == "graphql":
                if any(t == "--input" or t.startswith("--input=") or t.startswith("@") or "=@" in t or (t in ("-F", "--field", "--raw-field", "-f") and any("@" in a for a in args)) for t in args + w):
                    return "gh api graphql with a query read from a file, which the guard cannot read (write the query on the command line)"
            if group == "alias" and sub in ("set", "import"):
                expansion = (args[-1] if args else "").strip("'\"").lstrip("!").strip()
                if sub == "import" or re.match(r"^(pr\s+merge|api)\b", expansion) or "worktree" in expansion:
                    return "a gh alias for a merge or an api call (%s)" % " ".join(args)[:60]
            if group == "api":
                method = "GET"
                for i, a in enumerate(w):
                    if a in ("-X", "--method") and i + 1 < len(w):
                        method = w[i + 1].upper()
                    elif a.startswith("--method=") or (a.startswith("-X") and len(a) > 2):
                        method = a.split("=", 1)[1].upper() if "=" in a else a[2:].upper()
                    elif a in ("-f", "--raw-field", "-F", "--field", "--input"):
                        method = method if method != "GET" else "POST"
                if method in WRITE_METHODS and any(re.search(r"/pulls/\d+/merge\b", a) for a in w):
                    return "gh api %s on a pull request's merge endpoint (merging outside the gate)" % method
    return None

def hook_skipper_option(sub, args, snapshot):
    """--no-verify or commit's -n as a git option, never another option's value."""
    skip_m = sub in ("commit", "merge", "cherry-pick", "revert")
    i = 0
    while i < len(args):
        a = args[i]
        if skip_m and a in ("-m", "--message", "-F", "--file") and i + 1 < len(args):
            i += 2
            continue
        if skip_m and (a.startswith("--message=") or a.startswith("--file=")):
            i += 1
            continue
        if a.startswith("-") and "=" in a:
            i += 1
            continue
        if a == "--no-verify" and not snapshot:
            return a
        if sub == "commit" and re.match(r"^-[A-Za-z]*n[A-Za-z]*$", a) and not snapshot:
            return a
        i += 1
    return None


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


def in_worktree(w, cwd):
    """A commit made inside a builder's worktree (`-C ../Worktrees/x`, or a cwd under Worktrees/)."""
    paths = [cwd or ""] + [w[i + 1] for i, a in enumerate(w) if a == "-C" and i + 1 < len(w)]
    return any(re.search(r"[\\/]Worktrees[\\/]", p) for p in paths)

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
    try:
        reason = check(command, data.get("cwd") or os.getcwd(), tool=tool)
    except Exception as ex:
        reason = "the guard cannot read the command: internal error (%s)" % type(ex).__name__
    if reason:
        sys.stderr.write("permission-guard (Claude-Cursor Bridge): refused - %s. The loop merges only through the "
                         "verified gate and never force-pushes; if the branch rules refuse a merge, fix the cause, "
                         "never bypass the rules.\n" % reason)
        return 2
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())