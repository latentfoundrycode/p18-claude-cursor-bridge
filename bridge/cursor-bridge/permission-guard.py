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
`gh pr merge` only when it is not the value of a flag such as `--subject`. A here-document is unreadable. `powershell` without `-Command` runs the rest of its line,
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
import time

WRITE_METHODS = ("PUT", "POST", "PATCH", "DELETE")
AROUND_THE_SHIM = ("agent", "agent.cmd", "agent.ps1", "cursor-agent.cmd", "cursor-agent.ps1", "cursor-agent.exe")
SHELLS = ("cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe")
PROGRAM_AFTER = ("/c", "/k", "-c", "-command", "-file")
WRAPPER_SHELLS = SHELLS + ("bash", "bash.exe", "sh", "sh.exe", "zsh", "dash")
MERGE_MUTATIONS = ("mergePullRequest", "enablePullRequestAutoMerge", "enqueuePullRequest")
GH_VALUE_FLAGS = ("-t", "--subject", "-b", "--body", "-F", "--body-file", "-A", "--author-email", "-R", "--repo", "--match-head-commit", "--hostname")
_ALIAS_PREFIXES = ("worktree", "pr", "push", "api")
VALUE_OPTIONS = {"xargs": ("-I", "-n", "-L", "-s", "-d", "-P", "-E", "-a", "--max-args", "--max-lines", "--delimiter", "--max-procs", "--arg-file", "--replace"),
                 "nice": ("-n", "--adjustment"), "timeout": ("-s", "--signal", "-k", "--kill-after"), "sudo": ("-u", "-g", "--user", "--group"),
                 "env": ("-u", "--unset", "-C", "--chdir", "-S", "--split-string")}
PS_VALUE_SWITCHES = ("-executionpolicy", "-ep", "-ex", "-windowstyle", "-w", "-inputformat", "-if", "-outputformat", "-of")
ENCODED = object()
INNER_UNREADABLE = object()
PREMERGE_DIR = os.path.join("bridge", "premerge")
_clock = time.monotonic
_read_started = None
_READ_LIMIT = 8.0
_FIND_ACTIONS = ("-exec", "-execdir", "-ok", "-okdir")
_FIND_TAKES_ARG = frozenset((
    "-name", "-iname", "-path", "-ipath", "-regex", "-iregex", "-wholename", "-iwholename",
    "-lname", "-ilname", "-type", "-xtype", "-perm", "-user", "-group", "-uid", "-gid",
    "-size", "-amin", "-atime", "-cmin", "-ctime", "-mmin", "-mtime", "-used", "-links",
    "-inum", "-samefile", "-fstype", "-context", "-newer", "-anewer", "-cnewer",
    "-maxdepth", "-mindepth", "-regextype", "-printf", "-fprint", "-fprint0", "-fls", "-D",
))
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

BASH_RESERVED = frozenset("if then else elif fi case esac for select while until do done in function time coproc".split() + ["{", "}", "!", "[[", "]]"])
BASH_OK_BUILTINS = frozenset(("cd", "echo", "pwd", "true", "false", ":", "exit", "type", "printf"))
BASH_WRAPPER_CMDS = frozenset(("eval", "exec", "command", "builtin"))
REFUSED_CMD_WORDS = frozenset(("xargs", "start", "wsl", "mintty", "winpty", "strace", "dash", "zsh", "ksh", "fish", "csh", "tcsh", "ash", "busybox", "forfiles", "conhost", "schtasks", "chroot", "wt", "git-bash", "git-cmd", "gpg-agent", "gpg-connect-agent", "rundll32", "pcalua", "runas", "wmic"))
_MSYS_PREFIX = frozenset(("env", "nice", "nohup", "stdbuf", "timeout", "setsid", "sudo"))
_MSYS_COMMAND = frozenset(("bash", "sh", "find"))
_SHELL_CODE_NAMES = frozenset(("BASH_ENV", "ENV", "PS4", "SHELLOPTS", "BASHOPTS", "PROMPT_COMMAND"))
_LOCALE_NAMES = frozenset(("LANG", "LC_ALL", "LC_CTYPE"))
_REPARSE_MARK = "'\"{}*?[]"
_SSH_AGENT_VALUED = ("-a", "-E", "-P", "-t", "-O")
_SSH_AGENT_FLAGS = frozenset(("-c", "-s", "-D", "-d", "-k"))
_SSH_O_KEYS = frozenset(("proxycommand", "localcommand", "permitlocalcommand", "knownhostscommand"))
REFUSED_BUILTINS = frozenset(
    ". : [ alias bg bind break builtin caller cd command compgen complete compopt continue declare dirs disown echo enable eval exec exit export false fc fg getopts hash help history jobs kill let local logout mapfile popd printf pushd pwd read readarray readonly return set shift shopt source suspend test times trap true type typeset ulimit umask unalias unset wait".split()
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
CMD_BAD_BUILTIN = frozenset(b.lower() for b in "assoc break call cd chdir cls color copy date del dir echo endlocal erase exit for ftype goto if md mkdir mklink move path pause popd prompt pushd rd rem ren rename rmdir set setlocal shift start time title type ver verify vol".split()) - frozenset(("dir", "echo", "type", "cd", "ver"))
PS_VERBS = frozenset(v.lower() for v in "Add Approve Assert Backup Block Checkpoint Clear Close Compare Complete Compress Confirm Connect Convert ConvertFrom ConvertTo Copy Debug Deny Disable Disconnect Dismount Edit Enable Enter Exit Expand Export Find Format Get Grant Group Hide Import Initialize Install Invoke Join Limit Lock Measure Merge Mount Move New Open Optimize Out Ping Pop Protect Publish Push Read Receive Redo Register Remove Rename Repair Request Reset Resize Resolve Restart Restore Resume Revoke Save Search Select Send Set Show Skip Split Start Step Stop Submit Suspend Switch Sync Test Trace Unblock Undo Uninstall Unlock Unprotect Unpublish Unregister Update Use Wait Watch Write".split())
PS_CMDLETS = frozenset(x.lower() for x in "Get-ChildItem Get-Content Get-Item Get-ItemProperty Get-Location Get-Command Get-Help Get-Process Get-Service Get-Date Get-FileHash Test-Path Select-String Select-Object Sort-Object Measure-Object Format-List Format-Table Out-String Out-Host Write-Output Write-Host Compare-Object Resolve-Path Join-Path Split-Path ConvertTo-Json ConvertFrom-Json Set-Location Push-Location Pop-Location".split())
PS_ALIASES_OK = frozenset(x.lower() for x in "cat cd chdir compare diff dir echo fl ft gc gci gcm gi gl gp gps gsv help ls man measure oh popd ps pushd pwd rvpa select sl sls sort type write".split())
PS_ALIASES_BAD = frozenset(x.lower() for x in "% ? ac asnp CFS clc clear clhy cli clp cls clv cnsn copy cp cpi cpp curl cvpa dbp del dnsn ebp epal epcsv epsn erase etsn exsn fc fhx foreach fw gal gbp gcb gcs gdr ghy gin gjb gm gmo gpv group gsn gsnp gtz gu gv gwmi h history icm iex ihy ii ipal ipcsv ipmo ipsn irm ise iwmi iwr kill lp md mi mount move mp mv nal ndr ni nmo npssc nsn nv ogv r rbp rcjb rcsn rd rdr ren ri rjb rm rmdir rmo rni rnp rp rsn rsnp rujb rv rwmi sajb sal saps sasv sbp sc scb set shcm si sleep sp spjb spps spsv start stz sujb sv swmi tee trcm wget where wjb".split())
GH_API_OPTS = frozenset(("-X", "--method", "-H", "--header", "-f", "-F", "--field", "--raw-field", "-q", "--jq", "-t", "--template", "--cache", "--input", "-p", "--preview"))


def _cannot(msg):
    return "the guard cannot read the command: %s" % msg


def _too_long():
    if _read_started is None:
        return False
    return (_clock() - _read_started) >= _READ_LIMIT


def _deadline_at(i, next_check):
    """Test the clock when the position reaches the mark, then move the mark 4096 on."""
    if i < next_check:
        return False, next_check
    if _too_long():
        return True, next_check
    next_check += 4096
    if next_check <= i:
        next_check = i + 4096
    return False, next_check


def _time_left():
    if _read_started is None:
        return _READ_LIMIT
    return _READ_LIMIT - (_clock() - _read_started)


def _mode_name(tool):
    return "powershell" if tool == "PowerShell" else "bash"


def read_commands(text, mode="bash", slash_ok=False, fed=False):
    """One flat read of a command line (R-082 round 5); never raises."""
    try:
        if mode == "cmd":
            return _read_cmd(text, fed)
        if mode == "powershell":
            return _read_powershell(text, slash_ok, fed)
        return _read_bash(text, slash_ok, fed)
    except Exception as ex:
        return {"unreadable": _cannot("internal error (%s)" % type(ex).__name__), "commands": [], "chain": [], "chain_wds": [], "parts": [], "gh_amp": None}


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


def _locale_value_ok(value):
    low = value.lower()
    if low == "c" or low == "posix":
        return True
    return low.endswith(".utf-8") or low.endswith(".utf8")


def _apply_assignment(tok, husky, strict):
    """One NAME=value word, or NAME+=value outside env's and sudo's strict reading."""
    if not tok or tok[:1] == "-" or "=" not in tok:
        return None, husky, False
    name, value = tok.split("=", 1)
    an = _assignment_name(tok)
    append = False
    if an is None and not strict and len(name) >= 2 and name[-1] == "+":
        stem = name[:-1]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", stem):
            an = stem
            name = stem
            append = True
    up = name.upper()
    if up.startswith("BASH_FUNC_") and (strict or an is not None):
        return _cannot("an assignment that makes a shell run code"), husky, True
    if an is None:
        if strict:
            return _cannot("an assignment whose name is not an identifier"), husky, True
        return None, husky, False
    if up.startswith("GIT_CONFIG"):
        return _cannot("an assignment whose name begins GIT_CONFIG"), husky, True
    if up in _SHELL_CODE_NAMES:
        return _cannot("an assignment that makes a shell run code"), husky, True
    if append and up in _LOCALE_NAMES:
        return _cannot("an assignment that appends to the inherited locale"), husky, True
    if up in _LOCALE_NAMES and not _locale_value_ok(value):
        return _cannot("a locale assignment whose charset is not C, POSIX or UTF-8"), husky, True
    if tok == "HUSKY=0" or tok == "HUSKY+=0":
        husky = True
    return None, husky, True


def _reparse_applies(word, mode):
    """An MSYS program a native parent starts, or Git's bin\\bash.exe handing its command line on."""
    stem = _exe_stem(word)
    if stem not in _MSYS_PREFIX and stem not in _MSYS_COMMAND and stem not in REFUSED_CMD_WORDS:
        return False
    if mode == "powershell" or mode == "cmd":
        return True
    if mode == "bash" and stem in ("bash", "sh"):
        if ("/" in word or "\\" in word) and not word.startswith("/usr/bin/") and not word.startswith("/bin/"):
            return True
    return False


def _reparse_word_bad(word):
    if not word:
        return False
    if word[0] == "~" or word[0] == "@":
        return True
    slash, blank = False, False
    for ch in word:
        if ch in _REPARSE_MARK:
            return True
        if ch == "\\":
            slash = True
        elif ch in " \t\r\n":
            blank = True
    return slash and blank


def _words_reparse_refusal(words):
    for word in words:
        if _reparse_word_bad(word):
            return _cannot("a word an MSYS program parses again")
    return None


def _reparse_after(words, i, mode, scanned):
    """The words after i, scanned once: the first position of this walk that re-parses."""
    if scanned or i >= len(words) or not _reparse_applies(words[i], mode):
        return None, scanned
    return _words_reparse_refusal(words[i + 1:]), True


def _ssh_o_key(val):
    cut = len(val)
    for i, ch in enumerate(val):
        if ch == "=" or ch == " " or ch == "\t":
            cut = i
            break
    return val[:cut]


def _ssh_agent_refusal(words, i):
    """ssh-agent's own options and no command after them."""
    j, n = i + 1, len(words)
    while j < n:
        t = words[j]
        if t in _SSH_AGENT_FLAGS:
            j += 1
            continue
        if t in _SSH_AGENT_VALUED:
            if j + 1 >= n:
                return _cannot("an ssh-agent option without a value")
            j += 2
            continue
        glued = False
        for opt in _SSH_AGENT_VALUED:
            if t.startswith(opt) and len(t) > len(opt):
                glued = True
                break
        if glued:
            j += 1
            continue
        if t[:1] == "-":
            return _cannot("an unknown ssh-agent option")
        return _cannot("ssh-agent running a command")
    return None


def _ssh_option_refusal(words, i):
    """ssh -o whose key runs a command."""
    j, n = i + 1, len(words)
    while j < n:
        t = words[j]
        val = None
        if t == "-o":
            if j + 1 >= n:
                return _cannot("ssh -o without a value")
            val = words[j + 1]
            j += 2
        elif t.startswith("-o") and not t.startswith("--"):
            val = t[2:]
            if val[:1] == "=":
                val = val[1:]
            j += 1
        else:
            j += 1
            continue
        key = _ssh_o_key(val)
        if key.lower() in _SSH_O_KEYS:
            return _cannot("ssh -o %s" % key)
    return None


def _exe_stem(tok):
    """Command, shell, wrapper, prefix, launcher and builtin names, without a trailing .exe."""
    name = base(tok)
    if name.endswith(".exe"):
        return name[:-4]
    return name


def _cmd_word_refusal(words, mode="bash", slash_ok=False, fed=False):
    if mode == "cmd" and words:
        bad_name = _cmd_name_refusal(words[0])
        if bad_name:
            return _cannot(bad_name)
    _idx, err, _husky, _saw = _walk_to_command(words, mode, slash_ok, fed)
    return err


def _parse_bash_sh_words(words):
    """Options of bash or sh, before and after -c. The fourth value is an error, or the script word."""
    opts, i, has_c = [], 0, False
    while i < len(words):
        t = words[i]
        if t == "--":
            i += 1
            break
        if t == "-":
            break
        if t.startswith("+"):
            body = t[1:]
            if body and all(c in BASH_SH_FLAGS for c in body):
                if "c" in body:
                    return [], [], False, _cannot("a plus flag holding c")
                opts.append(t)
                i += 1
                continue
            return [], [], False, _cannot("an unknown bash option")
        if t.startswith("--"):
            if t in BASH_SH_OPTS:
                opts.append(t)
                i += 1
                continue
            return [], [], False, _cannot("an unknown bash option")
        if t.startswith("-"):
            body = t[1:]
            if "i" in body:
                return [], [], False, _cannot("interactive bash")
            if body and all(c in BASH_SH_FLAGS for c in body):
                if "c" in body:
                    has_c = True
                opts.append(t)
                i += 1
                continue
            return [], [], False, _cannot("an unknown bash option")
        break
    rest = words[i:] if i < len(words) else []
    if has_c:
        return opts, rest, True, None
    return opts, rest, False, rest[0] if rest else None


def _bash_reads_stdin(words, i, fed=False):
    _opts, _rest, has_c, script = _parse_bash_sh_words(words[i + 1:])
    if isinstance(script, str) and script.startswith("the guard cannot read"):
        return False
    if has_c:
        return False
    if script is None:
        return True
    if fed:
        return True
    return _stdin_script(script)


def _stdin_script(script):
    """A bash or sh script word that reads standard input or a descriptor."""
    if script == "-":
        return True
    absolute = script[:1] in "/\\" or (len(script) >= 2 and (("A" <= script[0] <= "Z") or ("a" <= script[0] <= "z")) and script[1] == ":")
    holds_dotdot = False
    parts, part = [], []
    for ch in script:
        if ch in "/\\":
            parts.append("".join(part))
            part = []
        else:
            part.append(ch)
    parts.append("".join(part))
    for p in parts:
        if p == "..":
            holds_dotdot = True
            break
    if not absolute and not holds_dotdot:
        return False
    for p in parts:
        if p == "" or p == ".":
            continue
        if p.lower() in ("dev", "proc"):
            return True
    return False


def _bash_inner_string(words):
    _opts, rest, has_c, script = _parse_bash_sh_words(words[1:])
    if isinstance(script, str) and script.startswith("the guard cannot read"):
        return None
    if not has_c or not rest:
        return None
    return " ".join(rest)


def _opt_err(msg):
    return _cannot(msg)


def _take_separate(words, i, n):
    if i + 1 >= n:
        return _opt_err("an unknown wrapper option"), i
    return None, i + 2


def _walk_env(words, i, husky):
    i += 1
    n = len(words)
    while i < n:
        t = words[i]
        if t in ENV_BAD or t.startswith("--split-string") or (t.startswith("-S") and not t.startswith("--")):
            return _opt_err("env -S or --split-string"), i, husky
        err, husky, consumed = _apply_assignment(t, husky, True)
        if consumed:
            if err:
                return err, i, husky
            i += 1
            continue
        if not t.startswith("-"):
            break
        bare = t.split("=", 1)[0]
        glued_short = (t.startswith("-u") and t != "-u" and not t.startswith("--")) or (t.startswith("-C") and t != "-C" and not t.startswith("--"))
        if t in ("-i", "-0", "--ignore-environment", "--null"):
            i += 1
            continue
        if bare in ("-u", "--unset", "-C", "--chdir") or glued_short:
            if "=" in t or glued_short:
                i += 1
                continue
            err, i = _take_separate(words, i, n)
            if err:
                return err, i, husky
            continue
        return _opt_err("an unknown env option"), i, husky
    return None, i, husky


def _walk_nice(words, i):
    i += 1
    n = len(words)
    while i < n and words[i].startswith("-"):
        t = words[i]
        if t == "-n" or (t.startswith("-n") and not t.startswith("--")):
            if t == "-n":
                err, i = _take_separate(words, i, n)
                if err:
                    return err, i
            else:
                i += 1
            continue
        if t == "--adjustment" or t.startswith("--adjustment="):
            if t == "--adjustment":
                err, i = _take_separate(words, i, n)
                if err:
                    return err, i
            else:
                i += 1
            continue
        return _opt_err("an unknown wrapper option"), i
    return None, i


def _walk_stdbuf(words, i):
    i += 1
    n = len(words)
    while i < n and words[i].startswith("-"):
        t = words[i]
        if t in ("-i", "-o", "-e"):
            err, i = _take_separate(words, i, n)
            if err:
                return err, i
            continue
        if len(t) > 2 and t[1] in "ioe" and not t.startswith("--"):
            i += 1
            continue
        if t.startswith("--input=") or t.startswith("--output=") or t.startswith("--error="):
            i += 1
            continue
        return _opt_err("an unknown wrapper option"), i
    return None, i


def _walk_timeout(words, i):
    i += 1
    n = len(words)
    while i < n and words[i].startswith("-"):
        t = words[i]
        bare = t.split("=", 1)[0]
        short_glue = len(t) > 2 and not t.startswith("--") and t[1] in "sk" and "=" not in t
        if bare in ("-s", "--signal", "-k", "--kill-after") or short_glue:
            glued = ("=" in t) or short_glue or (not t.startswith("--") and t not in ("-s", "-k") and len(t) > 2)
            if glued:
                i += 1
                continue
            err, i = _take_separate(words, i, n)
            if err:
                return err, i
            continue
        if t in ("--preserve-status", "--foreground", "-v", "--verbose"):
            i += 1
            continue
        return _opt_err("an unknown wrapper option"), i
    if i < n:
        i += 1
    return None, i


def _walk_flags(words, i, flags):
    i += 1
    n = len(words)
    while i < n and words[i].startswith("-"):
        if words[i] not in flags:
            return _opt_err("an unknown wrapper option"), i
        i += 1
    return None, i


def _walk_valued(words, i, flags, valued):
    i += 1
    n = len(words)
    while i < n and words[i].startswith("-"):
        t = words[i]
        bare = t.split("=", 1)[0]
        if bare not in flags and not any(t.startswith(v) and t != v and not t.startswith("--") for v in valued if len(v) == 2):
            return _opt_err("an unknown wrapper option"), i
        short = bare if bare in valued else None
        if short is None:
            for v in valued:
                if len(v) == 2 and t.startswith(v) and t != v and not t.startswith("--"):
                    short = v
                    break
        glued = ("=" in t) or (short is not None and t != short)
        if bare in valued or short is not None:
            if glued:
                i += 1
                continue
            err, i = _take_separate(words, i, n)
            if err:
                return err, i
            continue
        i += 1
    return None, i


def _take_assignments(words, i, n, husky, strict=False):
    """Leading NAME=value words, or env and sudo assignments when strict. Returns (error or None, index, husky)."""
    while i < n:
        err, husky, consumed = _apply_assignment(words[i], husky, strict)
        if not consumed:
            break
        if err:
            return err, i, husky
        i += 1
    return None, i, husky


def _walk_to_command(words, mode="bash", slash_ok=False, fed=False):
    """One prefix walk. Returns (index of the command word or None, error or None, saw HUSKY=0, saw a prefix)."""
    husky, saw_prefix, scanned = False, False, False
    i, n = 0, len(words)
    for t in words:
        if t == "--config-env" or t.startswith("--config-env="):
            return None, _cannot("an option --config-env"), husky, saw_prefix
    if mode != "cmd":
        err, i, husky = _take_assignments(words, i, n, husky)
        if err:
            return None, err, husky, saw_prefix
    while mode != "cmd" and i < n:
        head = _exe_stem(words[i])
        if head in _MSYS_PREFIX:
            err, scanned = _reparse_after(words, i, mode, scanned)
            if err:
                return None, err, husky, saw_prefix
        if head == "env":
            err, i, husky = _walk_env(words, i, husky)
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            continue
        if head == "nice":
            err, i = _walk_nice(words, i)
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            continue
        if head == "nohup":
            err, i = _walk_flags(words, i, ())
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            continue
        if head == "stdbuf":
            err, i = _walk_stdbuf(words, i)
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            continue
        if head == "timeout":
            err, i = _walk_timeout(words, i)
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            continue
        if head == "setsid":
            err, i = _walk_flags(words, i, SETSID_OPTS)
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            continue
        if head == "sudo":
            err, i = _walk_valued(words, i, SUDO_OPTS, ("-u", "-g", "--user", "--group"))
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            if mode != "cmd":
                err, i, husky = _take_assignments(words, i, n, husky, True)
                if err:
                    return None, err, husky, saw_prefix
            continue
        if head == "exec":
            err, i = _walk_valued(words, i, EXEC_OPTS, ("-a",))
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            continue
        if head == "command":
            err, i = _walk_flags(words, i, COMMAND_OPTS)
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            continue
        if head == "builtin":
            err, i = _walk_flags(words, i, ())
            saw_prefix = True
            if err:
                return None, err, husky, saw_prefix
            continue
        break
    if i >= n:
        return None, None, husky, saw_prefix
    err, scanned = _reparse_after(words, i, mode, scanned)
    if err:
        return i, err, husky, saw_prefix
    head = _exe_stem(words[i])
    use_slash = slash_ok and not saw_prefix
    if head == "ssh-agent":
        err = _ssh_agent_refusal(words, i)
        if err:
            return i, err, husky, saw_prefix
    if head == "ssh":
        err = _ssh_option_refusal(words, i)
        if err:
            return i, err, husky, saw_prefix
    if head in REFUSED_CMD_WORDS:
        return i, _cannot("a launcher or shell (%s)" % base(words[i])), husky, saw_prefix
    if mode == "bash":
        if head in BASH_RESERVED:
            return i, _cannot("a reserved word (%s)" % head), husky, saw_prefix
        if head == "printf" and any(a == "-v" or (a.startswith("-v") and not a.startswith("--")) for a in words[i + 1:]):
            return i, _cannot("a builtin (printf -v)"), husky, saw_prefix
        if head in REFUSED_BUILTINS:
            return i, _cannot("a builtin (%s)" % head), husky, saw_prefix
    if head in ("bash", "sh"):
        err = _parse_bash_sh_words(words[i + 1:])[3]
        if isinstance(err, str) and err.startswith("the guard cannot read"):
            return i, err, husky, saw_prefix
        if _bash_reads_stdin(words, i, fed):
            return i, _cannot("a shell that reads commands from standard input"), husky, saw_prefix
    if head == "cmd":
        err = _parse_cmd_wrapper(words[i:], use_slash)
        if err:
            return i, err, husky, saw_prefix
    if head in ("powershell", "pwsh"):
        err = _parse_ps_wrapper(words[i:], use_slash)
        if err:
            return i, err, husky, saw_prefix
    return i, None, husky, saw_prefix


def _cmd_switch_key(tl):
    """The letter of a /x or //x switch, and the text glued after it."""
    if tl.startswith("//"):
        return tl[2:3], tl[3:]
    if tl.startswith("/"):
        return tl[1:2], tl[2:]
    return "", tl


def _parse_cmd_wrapper(words, slash_ok=False):
    """Every switch before the inner command. /d /cgit is the glued switch /cgit."""
    err, _idx = _cmd_switch_walk(words, slash_ok)
    return err


def _cmd_switch_walk(words, slash_ok=False):
    """One walk of a cmd switch table. Returns (error or None, index of the inner command or None)."""
    i, n = 1, len(words)
    while i < n:
        tl = words[i].lower()
        if tl.startswith("/") and not tl.startswith("//") and not slash_ok:
            return _cannot("a single-slash cmd switch"), None
        if tl in ("/k", "//k"):
            return _cannot("a shell that reads commands from standard input"), None
        if tl in ("/c", "/r", "//c", "//r"):
            return None, i + 1
        if tl in ("/d", "/s", "/q", "//d", "//s", "//q"):
            i += 1
            continue
        if tl.startswith("/"):
            key, rest = _cmd_switch_key(tl)
            if key in "ckr" and rest:
                return _cannot("a switch glued to its command"), None
            return _cannot("an unknown cmd switch"), None
        return _cannot("an unknown cmd switch"), None
    return _cannot("cmd without /c, /k or /r"), None


def _ps_arg_edge(raw):
    """powershell.exe trims each argument and skips an empty one."""
    if not raw:
        return True
    return raw[0].isspace() or raw[-1].isspace()


def _ps_is_switch(raw):
    if _ps_arg_edge(raw):
        return False
    if raw[0] in "-/":
        return True
    for dash in ("\u2013", "\u2014", "\u2015"):
        if raw.startswith(dash):
            return True
    return False


def _ps_switch_walk(words, slash_ok=False):
    """One walk of a powershell or pwsh switch table. Returns (error or None, index of the inner command or None)."""
    i, n = 1, len(words)
    for raw in words[1:]:
        if _ps_arg_edge(raw):
            return _cannot("a powershell argument that is empty or begins or ends with whitespace"), None
    while i < n:
        raw = words[i]
        if not _ps_is_switch(raw):
            return None, i
        if raw.startswith("/") and not raw.startswith("//") and not slash_ok:
            return _cannot("a single-slash PowerShell switch"), None
        if "=" in raw:
            return _cannot("a PowerShell switch with a glued value"), None
        t = _ps_norm_switch(raw)
        if t in ("-e", "-ec") or t.startswith("-en") or t.startswith("-encodedcommand"):
            return "an encoded PowerShell command, which the guard cannot read", None
        if len(t) >= 2 and "-command".startswith(t):
            if i + 1 >= n or words[i + 1] == "-":
                return _cannot("a shell that reads commands from standard input"), None
            return None, i + 1
        if t in ("-f", "-file"):
            if i + 1 >= n or words[i + 1] == "-":
                return _cannot("a shell that reads commands from standard input"), None
            return None, None
        if t in ("-noprofile", "-nop", "-noninteractive", "-noni", "-nologo", "-sta", "-mta"):
            i += 1
            continue
        if t in PS_VALUE_SWITCHES:
            i += 2 if i + 1 < n else 1
            continue
        if t.startswith("-"):
            return _cannot("an unknown PowerShell switch"), None
        return None, i
    return _cannot("a shell that reads commands from standard input"), None


def _parse_ps_wrapper(words, slash_ok=False):
    err, _idx = _ps_switch_walk(words, slash_ok)
    return err


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


_BRACE_NAME = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"


def _note(refuse, err):
    if not err:
        return
    prefix = "the guard cannot read the command: "
    refuse(err[len(prefix):] if err.startswith(prefix) else err)


def _read_bash(text, slash_ok=False, fed=False):
    unreadable, gh_amp = None, None
    n = len(text)

    def refuse(msg):
        nonlocal unreadable
        if unreadable is None:
            unreadable = _cannot(msg)

    quote = None
    wbuf = []
    word_started = False
    word_quoted = False
    word_backslash = False
    brace_only = False
    pending = False
    words = []
    commands, chain, chain_wds, parts = [], [], [], []
    seg_words, piped, saw_input = [], False, False
    last_amp_glued = False
    i = 0
    in_comment = False
    next_check = 0

    def reset_word():
        nonlocal wbuf, word_started, word_quoted, word_backslash, brace_only
        wbuf = []
        word_started = False
        word_quoted = False
        word_backslash = False
        brace_only = False

    def emit_word():
        nonlocal pending
        if pending:
            if word_started:
                pending = False
                reset_word()
            return
        if not word_started:
            return
        words.append("".join(wbuf))
        reset_word()

    def finish_cmd(sep):
        nonlocal piped, saw_input, seg_words, last_amp_glued, gh_amp, words, commands
        emit_word()
        if pending:
            refuse("a redirection with no target")
            return
        if not words:
            saw_input = False
            return
        cw = list(words)
        this_input = saw_input
        commands.append({"words": cw, "sep": sep, "pipe": piped, "input": this_input, "last_amp": last_amp_glued})
        seg_words.append(cw)
        if _gh_api_head(cw) and last_amp_glued:
            gh_amp = "an unquoted & in a gh api argument (quote the URL or put each query field in its own quoted argument)"
        _note(refuse, _cmd_word_refusal(cw, "bash", slash_ok, fed or piped or this_input))
        words[:] = []
        piped = False
        saw_input = False
        last_amp_glued = False

    def finish_chain(sep):
        nonlocal seg_words, chain, chain_wds, parts
        finish_cmd(sep)
        if seg_words:
            chain.append(" ".join(" ".join(s) for s in seg_words))
            chain_wds.append(list(seg_words[0]))
            parts.append([list(s) for s in seg_words])
            seg_words = []

    def digits_held():
        if not word_started or word_quoted or word_backslash or not wbuf:
            return False
        for ch in wbuf:
            if not ch.isdigit():
                return False
        return True

    def boundary(kind, glued_amp=False):
        nonlocal last_amp_glued, piped
        if glued_amp:
            last_amp_glued = word_started and not pending
        if pending and not word_started:
            refuse("a redirection with no target")
            return
        emit_word()
        if kind == "pipe":
            finish_cmd("|")
            piped = True
        else:
            finish_chain(kind)

    def start_redirect(at):
        nonlocal pending, i, saw_input
        if at == "<":
            saw_input = True
        if at in "<>" and brace_only:
            refuse("a named file descriptor redirection")
            return False
        if pending and not word_started:
            refuse("a redirection with no target")
            return False
        if pending and word_started:
            pending = False
            reset_word()
        elif word_started:
            if at in "<>" and digits_held():
                reset_word()
            else:
                emit_word()
        c1 = text[i + 1] if i + 1 < n else ""
        c2 = text[i + 2] if i + 2 < n else ""
        if at == "&":
            i += 3 if c1 == ">" and c2 == ">" else 2
        elif at == "<":
            i += 2 if c1 in ">&" else 1
        elif c1 in ">&|":
            i += 2
        else:
            i += 1
        pending = True
        return True

    def mark():
        nonlocal word_started, brace_only
        word_started = True
        brace_only = False

    while i < n:
        if unreadable:
            break
        late, next_check = _deadline_at(i, next_check)
        if late:
            refuse("too long to read in time")
            break
        if in_comment:
            if text[i] == "\n":
                in_comment = False
                finish_chain("\n")
            i += 1
            continue
        c = text[i]
        if quote == "s":
            if c == "'":
                quote = None
            else:
                wbuf.append(c)
                mark()
            i += 1
            continue
        if quote == "d":
            if c == "\\" and i + 1 < n:
                nxt = text[i + 1]
                if nxt in '"\\':
                    wbuf.append(nxt)
                    mark()
                    i += 2
                    continue
                if nxt == "\n":
                    i += 2
                    continue
                wbuf.append(c)
                mark()
                i += 1
                continue
            if c in "$`":
                refuse("a substitution inside double quotes")
                break
            if c == '"':
                quote = None
                i += 1
                continue
            wbuf.append(c)
            mark()
            i += 1
            continue
        if c == "\\" and i + 1 < n:
            nxt = text[i + 1]
            if nxt == "$":
                refuse("a command substitution")
                break
            if nxt == "`":
                refuse("a backtick command")
                break
            if nxt == "\n":
                i += 2
                continue
            if nxt == "\r":
                wbuf.append("\r")
                word_started = True
                word_backslash = True
                brace_only = False
                i += 2
                continue
            wbuf.append(nxt)
            word_started = True
            word_backslash = True
            brace_only = False
            i += 2
            continue
        if c == "\\":
            wbuf.append(c)
            word_started = True
            word_backslash = True
            brace_only = False
            i += 1
            continue
        if c == "`":
            refuse("a backtick command")
            break
        if c == "$":
            refuse("a command substitution")
            break
        if c == "<" and i + 1 < n and text[i + 1] == "(":
            refuse("process substitution")
            break
        if c == ">" and i + 1 < n and text[i + 1] == "(":
            refuse("process substitution")
            break
        if c == "<" and i + 1 < n and text[i + 1] == "<":
            refuse("a here-document")
            break
        if c == "&" and i + 1 < n and text[i + 1] == ">":
            if not start_redirect("&"):
                break
            continue
        if c == "<" or c == ">":
            if not start_redirect(c):
                break
            continue
        if c == "|":
            if i + 1 < n and text[i + 1] == "|":
                boundary("||")
                i += 2
            elif i + 1 < n and text[i + 1] == "&":
                boundary("pipe")
                i += 2
            else:
                boundary("pipe")
                i += 1
            continue
        if c == "&":
            if i + 1 < n and text[i + 1] == "&":
                boundary("&&")
                i += 2
            else:
                boundary("&", glued_amp=True)
                i += 1
            continue
        if c in (";", "\n"):
            boundary(c)
            i += 1
            continue
        if c == "\r":
            refuse("a carriage return")
            break
        if c in " \t":
            if pending and not word_started:
                i += 1
                continue
            emit_word()
            i += 1
            continue
        if c == "#" and not word_started:
            if pending:
                refuse("a redirection with no target")
                break
            in_comment = True
            i += 1
            continue
        if c == "'":
            quote = "s"
            word_started = True
            word_quoted = True
            brace_only = False
            i += 1
            continue
        if c == '"':
            quote = "d"
            word_started = True
            word_quoted = True
            brace_only = False
            i += 1
            continue
        if c == "{":
            if i + 1 >= n:
                refuse("brace expansion (quote it)")
                break
            nxt = text[i + 1]
            if nxt == "}":
                wbuf.append("{")
                wbuf.append("}")
                word_started = True
                brace_only = False
                i += 2
                continue
            if nxt in _BRACE_NAME:
                j = i + 1
                while j < n and text[j] in _BRACE_NAME:
                    j += 1
                if j < n and text[j] == "}":
                    wholly = not word_started
                    k = i
                    while k <= j:
                        wbuf.append(text[k])
                        k += 1
                    word_started = True
                    brace_only = wholly
                    i = j + 1
                    continue
            refuse("brace expansion (quote it)")
            break
        if c == "}":
            refuse("brace expansion (quote it)")
            break
        if c in "()":
            refuse("parentheses")
            break
        if c in "*?[":
            refuse("a glob character (quote it)")
            break
        wbuf.append(c)
        mark()
        i += 1
    if unreadable is None and quote:
        refuse("an unclosed quote")
    if unreadable is None and pending and not word_started:
        refuse("a redirection with no target")
    if unreadable is None:
        emit_word()
        if words:
            finish_cmd(None)
        if seg_words:
            chain.append(" ".join(" ".join(s) for s in seg_words))
            chain_wds.append(list(seg_words[-1]))
            parts.append([list(s) for s in seg_words])
    if not chain and commands:
        chain = [" ".join(" ".join(c["words"]) for c in commands)]
        chain_wds = [commands[0]["words"]]
        if not parts:
            parts = [[c["words"]] for c in commands]
    return {"unreadable": unreadable, "commands": commands, "chain": chain, "chain_wds": chain_wds, "parts": parts, "gh_amp": gh_amp, "text": text}


def _ps_char_ok(c, nxt):
    if c in "\t\n":
        return True
    if c == "\r":
        return nxt == "\n"
    return 32 <= ord(c) <= 126


def _ps_splat_word(word):
    if len(word) < 2 or word[0] != "@":
        return False
    if word[1] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_":
        return False
    k = 2
    while k < len(word):
        if word[k] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_":
            return False
        k += 1
    return True


def _ps_shape_refusal(cw):
    """A PowerShell command word outside the read-only cmdlet and alias lists."""
    wp = strip_prefix(cw)
    if not wp:
        return None
    tok = wp[0]
    tl = tok.lower()
    if tl in PS_ALIASES_BAD or tl in ("iex", "invoke-expression", "start", "set-alias"):
        return _cannot("a cmdlet or alias (%s)" % tok)
    if "\\" in tok:
        tail = tok[tok.rfind("\\") + 1:]
        low = tail.lower()
        if _verb_noun(tail) or low in PS_ALIASES_OK or low in PS_ALIASES_BAD:
            return _cannot("a module-qualified cmdlet (%s)" % tok)
    elif _verb_noun(tok) and tl not in PS_CMDLETS and tl not in PS_ALIASES_OK:
        return _cannot("a cmdlet (%s)" % tok)
    return None


def _ps_holds_blank(word):
    for ch in word:
        if ch in " \t\r\n":
            return True
    return False


def _read_powershell(text, slash_ok=False, fed=False):
    unreadable, gh_amp = None, None
    n = len(text)

    def refuse(msg):
        nonlocal unreadable
        if unreadable is None:
            unreadable = _cannot(msg)

    quote = None
    wbuf = []
    word_started = False
    word_quoted = False
    began_quoted = False
    lead_closed = False
    pending = False
    words = []
    commands, chain, chain_wds, seg_words, parts = [], [], [], [], []
    piped, saw_input = False, False
    i = 0
    next_check = 0

    def reset_word():
        nonlocal wbuf, word_started, word_quoted, began_quoted, lead_closed
        wbuf = []
        word_started = False
        word_quoted = False
        began_quoted = False
        lead_closed = False

    def emit_word():
        nonlocal pending
        if word_started:
            word = "".join(wbuf)
            if '"' in word:
                refuse("a literal double quote")
                reset_word()
                pending = False
                return
            if word[-1:] == "\\" and _ps_holds_blank(word):
                refuse("a trailing backslash in a word that holds a blank")
                reset_word()
                pending = False
                return
            if word.startswith("-") and not word.startswith("--") and "." in word:
                refuse("a switch split at a dot")
                reset_word()
                pending = False
                return
            if not word:
                refuse("an empty quoted word")
                reset_word()
                pending = False
                return
            if _ps_splat_word(word):
                refuse("splatting")
                reset_word()
                pending = False
                return
        if pending:
            if word_started:
                pending = False
                reset_word()
            return
        if not word_started:
            return
        words.append("".join(wbuf))
        reset_word()

    def ps_command_shape(cw, this_fed):
        if unreadable is not None:
            return
        _note(refuse, _cmd_word_refusal(cw, "powershell", slash_ok, this_fed))
        if unreadable is not None:
            return
        _note(refuse, _ps_shape_refusal(cw))

    def finish_cmd(sep):
        nonlocal words, commands, seg_words, piped, saw_input
        emit_word()
        if pending:
            refuse("a redirection with no target")
            return
        if not words:
            saw_input = False
            return
        cw = list(words)
        this_input = saw_input
        commands.append({"words": cw, "sep": sep, "pipe": piped, "input": this_input, "last_amp": False})
        seg_words.append(cw)
        ps_command_shape(cw, fed or piped or this_input)
        words[:] = []
        piped = False
        saw_input = False

    def finish_chain(sep):
        nonlocal chain, chain_wds, seg_words, parts
        finish_cmd(sep)
        if seg_words:
            chain.append(" ".join(" ".join(x) for x in seg_words))
            chain_wds.append(list(seg_words[0]))
            parts.append([list(s) for s in seg_words])
            seg_words = []

    def ps_desc():
        return word_started and not word_quoted and len(wbuf) == 1 and wbuf[0] in "123456*"

    def start_ps_redirect():
        nonlocal pending, i
        if pending and not word_started:
            refuse("a redirection with no target")
            return False
        desc = ps_desc()
        if pending and word_started:
            pending = False
            reset_word()
        elif desc:
            reset_word()
        elif word_started:
            emit_word()
        c1 = text[i + 1] if i + 1 < n else ""
        c2 = text[i + 2] if i + 2 < n else ""
        if c1 == ">":
            pending = True
            i += 2
            return True
        if c1 == "&":
            if desc and c2 in "12":
                i += 3
                return True
            refuse("a redirection")
            return False
        pending = True
        i += 1
        return True

    def boundary(kind):
        nonlocal piped
        if pending and not word_started:
            refuse("a redirection with no target")
            return
        if kind == "pipe":
            finish_cmd("|")
            piped = True
        else:
            finish_chain(kind)

    while i < n and unreadable is None:
        late, next_check = _deadline_at(i, next_check)
        if late:
            refuse("too long to read in time")
            break
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "\r" and nxt != "\n":
            refuse("a lone carriage return")
            break
        if not _ps_char_ok(c, nxt):
            refuse("a character outside printable ASCII")
            break
        if quote == "s":
            if c == "'" and nxt == "'":
                wbuf.append("'")
                word_started = True
                i += 2
                continue
            if c == "'":
                quote = None
                if began_quoted:
                    lead_closed = True
                i += 1
                continue
            wbuf.append(c)
            word_started = True
            i += 1
            continue
        if quote == "d":
            if c == '"' and nxt == '"':
                wbuf.append('"')
                word_started = True
                i += 2
                continue
            if c == '"':
                quote = None
                if began_quoted:
                    lead_closed = True
                i += 1
                continue
            if c in "$`":
                refuse("a substitution")
                break
            wbuf.append(c)
            word_started = True
            i += 1
            continue
        if c == "<" and nxt == "#":
            refuse("a block comment")
            break
        if c == "<" and nxt == "<":
            refuse("a here-document")
            break
        if c == "<":
            if pending and not word_started:
                refuse("a redirection with no target")
                break
            desc = word_started and not word_quoted and bool(wbuf) and all(ch.isdigit() for ch in wbuf)
            if pending and word_started:
                pending = False
                reset_word()
            elif desc:
                reset_word()
            elif word_started:
                emit_word()
            saw_input = True
            i += 2 if nxt in ">&" else 1
            pending = True
            continue
        if c == "'" or c == '"':
            if lead_closed:
                refuse("a word continuing after its quote")
                break
            if word_started:
                refuse("a quote not at the start of a word")
                break
            began_quoted = True
            quote = "s" if c == "'" else "d"
            word_started = True
            word_quoted = True
            i += 1
            continue
        if c == "#" and not word_started:
            if pending:
                refuse("a redirection with no target")
                break
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "`":
            if nxt == "\n":
                i += 2
                continue
            if nxt == "\r" and i + 2 < n and text[i + 2] == "\n":
                i += 3
                continue
            refuse("a backtick")
            break
        if c == "$":
            refuse("a variable")
            break
        if c in "(){}[]":
            refuse("parentheses or braces")
            break
        if c == "@" and nxt in "({'\"":
            refuse("splatting")
            break
        if c == ">" :
            if not start_ps_redirect():
                break
            continue
        if c == "&" and nxt == "&":
            boundary("&&")
            i += 2
            continue
        if c == "|" and nxt == "|":
            boundary("||")
            i += 2
            continue
        if c in (";", "\n"):
            boundary(c)
            i += 1
            continue
        if c == "|":
            boundary("pipe")
            i += 1
            continue
        if c == "&" and not word_started:
            boundary("&")
            i += 1
            continue
        if c == "&":
            refuse("an unquoted &")
            break
        if c == ",":
            refuse("a comma")
            break
        if c == "\r":
            if pending and not word_started:
                i += 1
                continue
            emit_word()
            i += 1
            continue
        if c in " \t":
            if pending and not word_started:
                i += 1
                continue
            emit_word()
            i += 1
            continue
        if c == "." and not word_started and not words and (not nxt or nxt in " \t\r\n;|&"):
            i += 1
            continue
        if c == "-" and not word_started and nxt == "-" and i + 2 < n and text[i + 2] == "%":
            refuse("stop-parsing")
            break
        if lead_closed:
            refuse("a word continuing after its quote")
            break
        wbuf.append(c)
        word_started = True
        i += 1
    if unreadable is None and quote:
        refuse("an unclosed quote")
    if unreadable is None and pending and not word_started:
        refuse("a redirection with no target")
    if unreadable is None:
        finish_chain(None)
    if not chain and commands:
        chain = [" ".join(" ".join(c["words"]) for c in commands)]
        chain_wds = [commands[0]["words"]]
        if not parts:
            parts = [[c["words"]] for c in commands]
    return {"unreadable": unreadable, "commands": commands, "chain": chain, "chain_wds": chain_wds, "parts": parts, "gh_amp": gh_amp, "text": text}


def _cmd_name_refusal(word):
    """cmd ends a command name at characters other than a letter, a digit, - _ and ."""
    for ch in word:
        if not (("A" <= ch <= "Z") or ("a" <= ch <= "z") or ("0" <= ch <= "9") or ch in "-_."):
            return "a cmd command name ended by a special character"
    stem = word.split(".", 1)[0].lower()
    if stem in CMD_BAD_BUILTIN:
        return "a cmd builtin (%s)" % stem
    return None


def _read_cmd(text, fed=False):
    bad = "\"'\\^%!()\r\n@;,=" + "`"
    next_check = 0
    for nch, ch in enumerate(text):
        late, next_check = _deadline_at(nch, next_check)
        if late:
            return {"unreadable": _cannot("too long to read in time"), "commands": [], "chain": [], "chain_wds": [], "parts": [], "gh_amp": None}
        if ch in bad:
            return {"unreadable": _cannot("cmd inner command character %s" % ch), "commands": [], "chain": [], "chain_wds": [], "parts": [], "gh_amp": None}
    unreadable = None
    n = len(text)
    wbuf, words = [], []
    word_started = False
    pending = False
    commands, chain, chain_wds, seg, parts = [], [], [], [], []
    piped, saw_input = False, False
    i = 0
    next_check = 0

    def refuse(msg):
        nonlocal unreadable
        if unreadable is None:
            unreadable = _cannot(msg)

    def reset_word():
        nonlocal wbuf, word_started
        wbuf = []
        word_started = False

    def emit_word():
        nonlocal pending
        if pending:
            if word_started:
                pending = False
                reset_word()
            return
        if word_started:
            words.append("".join(wbuf))
            reset_word()

    def one_digit():
        return word_started and len(wbuf) == 1 and wbuf[0].isdigit()

    def close_cmd():
        nonlocal piped, saw_input
        emit_word()
        if pending:
            refuse("a redirection with no target")
            return
        if not words:
            saw_input = False
            return
        cw = list(words)
        this_input = saw_input
        _note(refuse, _cmd_word_refusal(cw, "cmd", False, fed or piped or this_input))
        commands.append({"words": cw, "sep": None, "pipe": piped, "input": this_input, "last_amp": False})
        seg.append(cw)
        words[:] = []
        piped = False
        saw_input = False

    def close_part():
        close_cmd()
        if seg:
            chain.append(" ".join(" ".join(s) for s in seg))
            chain_wds.append(list(seg[0]))
            parts.append([list(s) for s in seg])
            seg[:] = []

    while i < n and unreadable is None:
        late, next_check = _deadline_at(i, next_check)
        if late:
            refuse("too long to read in time")
            break
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c in "<>":
            if pending and not word_started:
                refuse("a redirection with no target")
                break
            digit = one_digit()
            if c == "<":
                saw_input = True
            if pending and word_started:
                pending = False
                reset_word()
            elif digit:
                reset_word()
            elif word_started:
                emit_word()
            c2 = text[i + 2] if i + 2 < n else ""
            if c == ">" and nxt == ">":
                pending = True
                i += 2
                continue
            if nxt == "&" and c2.isdigit():
                i += 3
                continue
            if nxt == "&":
                refuse("a redirection")
                break
            pending = True
            i += 1
            continue
        if c == "|":
            if pending and not word_started:
                refuse("a redirection with no target")
                break
            if nxt == "|":
                close_part()
                i += 2
            else:
                close_cmd()
                piped = True
                i += 1
            continue
        if c == "&":
            if pending and not word_started:
                refuse("a redirection with no target")
                break
            close_part()
            i += 2 if nxt == "&" else 1
            continue
        if c in " \t":
            if not (pending and not word_started):
                emit_word()
            i += 1
            continue
        wbuf.append(c)
        word_started = True
        i += 1
    if unreadable is None and pending and not word_started:
        refuse("a redirection with no target")
    if unreadable is None:
        close_part()
    return {"unreadable": unreadable, "commands": commands, "chain": chain, "chain_wds": chain_wds, "parts": parts, "gh_amp": None, "text": text}


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


def _find_arg_count(tok):
    """How many following words a find option takes. A bare -O takes none."""
    if tok == "-fprintf":
        return 2
    if tok == "-files0-from":
        return 1
    if len(tok) == 8 and tok.startswith("-newer"):
        a, b = tok[6], tok[7]
        if (("A" <= a <= "Z") or ("a" <= a <= "z")) and (("A" <= b <= "Z") or ("a" <= b <= "z")):
            return 1
    if tok in _FIND_TAKES_ARG:
        return 1
    return 0


def _find_clauses(words):
    """Each find -exec, -execdir, -ok or -okdir clause as its own word list. Never joined back into text."""
    clauses = []
    i, n = 0, len(words)
    while i < n:
        t = words[i]
        if t in _FIND_ACTIONS:
            start = i + 1
            k = start
            while k < n:
                tok = words[k]
                if tok == ";":
                    clauses.append(words[start:k])
                    i = k + 1
                    break
                if tok == "+" and k > start and words[k - 1] == "{}":
                    clauses.append(words[start:k])
                    i = k + 1
                    break
                if tok in _FIND_ACTIONS and _exe_stem(words[start] if start < k else "") != "find":
                    return _cannot("a find clause holding another -exec"), None
                k += 1
            else:
                clauses.append(words[start:])
                i = n
            continue
        ntake = _find_arg_count(t)
        if ntake:
            if i + ntake >= n:
                i = n
                continue
            for v in words[i + 1:i + 1 + ntake]:
                if v in _FIND_ACTIONS:
                    return _cannot("an -exec word taken as an option value"), None
            i += 1 + ntake
            continue
        i += 1
    return None, clauses


def _command_changes(words, mode, depth, tool, slash_ok=False, fed=False):
    """Words that change state, including a wrapper or find clause this command re-reads."""
    if not words or depth > READ_DEPTH_BOUND or _too_long():
        return None
    _idx, _err, _husky, saw_prefix = _walk_to_command(words, mode, slash_ok, fed)
    sp = strip_prefix(words)
    if sp and state_changing(sp):
        return sp
    if not sp:
        return None
    head = _exe_stem(sp[0])
    base_slash = False if saw_prefix else slash_ok
    inner, inner_mode, child_slash = None, mode, base_slash
    if head == "eval" and len(sp) > 1:
        inner, child_slash = " ".join(sp[1:]), False
    elif head in ("bash", "sh"):
        inner, inner_mode, child_slash = _bash_inner_string(sp), "bash", False
    elif head in ("powershell", "pwsh"):
        got = shell_inner(sp, base_slash)
        if isinstance(got, str):
            inner, inner_mode, child_slash = got, "powershell", base_slash
    elif head == "cmd":
        got = shell_inner(sp, base_slash)
        if isinstance(got, str):
            inner, inner_mode, child_slash = got, "cmd", False
    elif head == "find":
        err, clauses = _find_clauses(sp)
        if err or not clauses:
            return None
        for clause in clauses:
            hit = _command_changes(clause, mode, depth + 1, tool, False, fed)
            if hit:
                return hit
        return None
    if not isinstance(inner, str):
        return None
    parsed = read_commands(inner, mode=inner_mode, slash_ok=child_slash, fed=fed)
    if parsed.get("unreadable"):
        return None
    for cmd in parsed.get("commands") or []:
        cfed = fed or cmd.get("pipe") or cmd.get("input")
        hit = _command_changes(cmd.get("words") or [], inner_mode, depth + 1, tool, child_slash, cfed)
        if hit:
            return hit
    return None


def _stage_changes(parts, mode="bash", tool="Bash", slash_ok=False, fed=False):
    for part in parts:
        later = False
        for stage in part:
            hit = _command_changes(stage, mode, 0, tool, slash_ok, fed or later)
            if hit:
                return hit
            later = True
    return None


def _chain_from_words(words, mode, depth, lists, tool, slash_ok=False, fed=False):
    if not words or depth > READ_DEPTH_BOUND:
        return
    _idx, _err, _husky, saw_prefix = _walk_to_command(words, mode, slash_ok, fed)
    w = strip_prefix(words)
    if not w:
        return
    head = _exe_stem(w[0])
    base_slash = False if saw_prefix else slash_ok
    inner, inner_mode, child_slash = None, mode, base_slash
    if head == "eval" and len(w) > 1:
        inner, child_slash = " ".join(w[1:]), False
    elif head in WRAPPER_SHELLS or base(w[0]) in WRAPPER_SHELLS:
        if head in ("bash", "sh"):
            child_slash = False
        elif head == "cmd":
            child_slash = False
        got = shell_inner(w, base_slash)
        if isinstance(got, str):
            inner = got
            if head in ("powershell", "pwsh"):
                inner_mode = "powershell"
            elif head == "cmd":
                inner_mode = "cmd"
            elif head in ("bash", "sh"):
                inner_mode = "bash"
    if isinstance(inner, str):
        sp = read_commands(inner, mode=inner_mode, slash_ok=child_slash, fed=fed)
        ip = sp.get("parts") or []
        if not sp.get("unreadable") and len(ip) >= 2:
            lists.append((ip, inner_mode, child_slash, fed))
        if not sp.get("unreadable"):
            for cmd in sp.get("commands") or []:
                cfed = fed or cmd.get("pipe") or cmd.get("input")
                _chain_from_words(cmd.get("words") or [], inner_mode, depth + 1, lists, tool, child_slash, cfed)
    if head == "find":
        err, clauses = _find_clauses(w)
        if not err:
            for clause in clauses:
                _chain_from_words(clause, mode, depth + 1, lists, tool, False, fed)


def _chain_lists(parsed, command, mode, depth, tool="Bash", slash_ok=False, fed=False):
    lists = []
    parts = parsed.get("parts") or []
    if len(parts) >= 2:
        lists.append((parts, mode, slash_ok, fed))
    for cmd in parsed.get("commands", []):
        cfed = fed or cmd.get("pipe") or cmd.get("input")
        _chain_from_words(cmd.get("words") or [], mode, depth, lists, tool, slash_ok, cfed)
    return lists


def chain_reason(command, cwd, tool="Bash", outermost=True, *, slash_ok):
    if not in_workspace(cwd):
        return None
    mode = _mode_name(tool)
    parsed = read_commands(command, mode=mode, slash_ok=slash_ok)
    if parsed.get("unreadable"):
        return None
    top = parsed.get("parts") or []
    if outermost and len(top) >= 2 and top[0]:
        sp = strip_prefix(top[0][0])
        if sp and base(sp[0]) == "cd":
            return "a command wrapped in cd (rule 8: never wrap a command in cd; run it with the path it needs, or git -C)"
    for parts, part_mode, part_slash, part_fed in _chain_lists(parsed, command, mode, 0, tool, slash_ok, False):
        if len(parts) < 2:
            continue
        hit = _stage_changes(parts, part_mode, tool, part_slash, part_fed)
        if hit:
            return "a chain of %d commands carrying %s (rule 8: one command per call, never chained with &&, ; or ||; the allowlist and the guard read one command, and a chain once built an increment on a merged branch)" % (len(parts), " ".join(hit[:2]))
    return None


def _husky_git_mutation(simple):
    """git, then commit, push or merge, each as its own word. Two linear searches, no .*."""
    found = re.search(r"\bgit\b", simple, re.I)
    if not found:
        return False
    return re.search(r"\b(commit|push|merge)\b", simple[found.end():], re.I) is not None


def _alias_key_char(ch):
    return ch.isalnum() or ch == "_" or ch == "-"


def _alias_value_prefix(a):
    """The value after =, blanks and one optional quote stripped, then a refused prefix."""
    if len(a) < 7 or a[:6].lower() != "alias.":
        return False
    i, n = 6, len(a)
    while i < n and _alias_key_char(a[i]):
        i += 1
    if i >= n or a[i] != "=":
        return False
    i += 1
    while i < n and a[i].isspace():
        i += 1
    if i < n and a[i] in "'\"":
        i += 1
        while i < n and a[i].isspace():
            i += 1
    if i < n and a[i] == "!":
        return True
    for pref in _ALIAS_PREFIXES:
        if a[i:i + len(pref)].lower() == pref:
            end = i + len(pref)
            if end >= n or not (a[end].isalnum() or a[end] == "_"):
                return True
    return False


def _alias_names_refused(a):
    if _alias_value_prefix(a):
        return True
    if not a.lower().startswith("alias."):
        return False
    if re.search(r"worktree\s+remove|pr\s+merge", a, re.I):
        return True
    found = re.search(r"push\b", a, re.I)
    if found and re.search(r"--forc|-f\b|\+", a[found.end():], re.I):
        return True
    return False


def _short_letters_hold(a, letter):
    """A single-dash word whose other characters are ASCII letters, one of them letter."""
    if len(a) < 2 or a[0] != "-" or a[1] == "-":
        return False
    has = False
    for ch in a[1:]:
        if not (("A" <= ch <= "Z") or ("a" <= ch <= "z")):
            return False
        if ch == letter:
            has = True
    return has


def leading_husky_zero(words_or_text, tool="Bash"):
    w = list(words_or_text) if isinstance(words_or_text, (list, tuple)) else words(words_or_text, mode=_mode_name(tool))
    _idx, _err, husky, _saw = _walk_to_command(w, _mode_name(tool))
    return husky


def shell_inner(w, slash_ok=False):
    """The inner command of a wrapper, taken from the same switch walk the refusal uses."""
    if not w:
        return None
    bh = _exe_stem(w[0])
    if bh in ("bash", "sh"):
        return _bash_inner_string(w) or None
    if bh in ("powershell", "pwsh"):
        err, idx = _ps_switch_walk(w, slash_ok)
        if err:
            if isinstance(err, str) and err.startswith("an encoded"):
                return ENCODED
            return INNER_UNREADABLE
        if idx is None:
            return None
        return " ".join(w[idx:]) or None
    if bh == "cmd":
        err, idx = _cmd_switch_walk(w, slash_ok)
        if err or idx is None:
            return INNER_UNREADABLE
        rest = w[idx:]
        for word in rest:
            if word == "" or (" " in word) or ("\t" in word):
                return INNER_UNREADABLE
        return " ".join(rest) or None
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
    if not w:
        return []
    idx, _err, _husky, _saw = _walk_to_command(list(w), "bash")
    if idx is None:
        return []
    return list(w[idx:])


def commit_message(args, command):
    msg = None
    for i, a in enumerate(args):
        if a in ("-m", "--message") and i + 1 < len(args):
            msg = args[i + 1]
            break
        if a.startswith("--message="):
            msg = a.split("=", 1)[1]
            break
        if a.startswith("-m") and not a.startswith("--") and len(a) > 2:
            msg = a[2:]
            break
    return (msg or "").strip()


def check(command, cwd=None, tool="Bash", _depth=0):
    global _read_started
    own = _depth == 0
    if own:
        _read_started = _clock()
    mode = _mode_name(tool)
    try:
        return _check_one(command, cwd, tool, mode, _depth, tool == "PowerShell", False)
    finally:
        if own:
            _read_started = None


def _check_one(command, cwd, tool, mode, depth, slash_ok, fed):
    if _too_long():
        return _cannot("too long to read in time")
    if depth > READ_DEPTH_BOUND:
        return _cannot("nesting past the bound")
    parsed = read_commands(command, mode=mode, slash_ok=slash_ok, fed=fed)
    if parsed.get("unreadable"):
        return parsed["unreadable"]
    if parsed.get("gh_amp"):
        return parsed["gh_amp"]
    r = chain_reason(command, cwd, tool=tool, outermost=(depth == 0), slash_ok=slash_ok)
    if r:
        return r
    for cmd in parsed.get("commands", []):
        if _too_long():
            return _cannot("too long to read in time")
        cfed = fed or cmd.get("pipe") or cmd.get("input")
        r = _check_word_list(cmd["words"], command, cwd, tool, mode, depth, slash_ok, cfed)
        if r:
            return r
    return None


def _find_brace_refusal(words, mode, depth):
    """A find -exec clause whose command is the found file, at any depth under the clause."""
    if not words or depth > READ_DEPTH_BOUND:
        return None
    if _too_long():
        return _cannot("too long to read in time")
    for word in words:
        if "{}" in word and word != "{}":
            return _cannot("a find argument holding {}")
    use = "bash" if mode == "cmd" else mode
    idx, _err, _h, _s = _walk_to_command(words, use, False, False)
    if idx is None:
        return None
    cmd = words[idx]
    if "{}" in cmd:
        return _cannot("a find clause whose command is the found file")
    head = _exe_stem(cmd)
    rest = words[idx:]
    inner, inner_mode = None, mode
    if head == "eval" and len(rest) > 1:
        inner, inner_mode = " ".join(rest[1:]), mode
    elif head in ("bash", "sh"):
        inner, inner_mode = _bash_inner_string(rest), "bash"
    elif head in ("powershell", "pwsh"):
        got = shell_inner(rest, False)
        if isinstance(got, str):
            inner, inner_mode = got, "powershell"
    elif head == "cmd":
        got = shell_inner(rest, False)
        if isinstance(got, str):
            inner, inner_mode = got, "cmd"
    elif head == "find":
        ferr, clauses = _find_clauses(rest)
        if ferr or not clauses:
            return None
        for clause in clauses:
            r = _find_brace_refusal(clause, mode, depth + 1)
            if r:
                return r
        return None
    if not inner:
        return None
    parsed = read_commands(inner, mode=inner_mode, slash_ok=False, fed=False)
    if parsed.get("unreadable"):
        return None
    for one in parsed.get("commands") or []:
        r = _find_brace_refusal(one.get("words") or [], inner_mode, depth + 1)
        if r:
            return r
    return None


def _check_word_list(cmd_wds, command, cwd, tool, mode, depth, slash_ok, fed=False):
    """Every check of one command, on the word list the reader produced or a find clause."""
    if _too_long():
        return _cannot("too long to read in time")
    if depth > READ_DEPTH_BOUND:
        return _cannot("nesting past the bound")
    err = _cmd_word_refusal(cmd_wds, mode, slash_ok, fed)
    if err:
        return err
    if mode == "powershell":
        err = _ps_shape_refusal(cmd_wds)
        if err:
            return err
    simple = " ".join(cmd_wds)
    if leading_husky_zero(cmd_wds, tool) and _husky_git_mutation(simple):
        return "HUSKY=0 switches the hook runner off (a commit that skips its checks; rule 4)"
    if _too_long():
        return _cannot("too long to read in time")
    if mode == "cmd":
        bidx, berr, _bh, _bs = _walk_to_command(cmd_wds, "bash", False, fed)
        if berr and "a builtin (" not in berr and "a reserved word (" not in berr:
            return berr
        w = list(cmd_wds[bidx:]) if bidx is not None else []
    else:
        w = strip_prefix(cmd_wds)
    if tool == "PowerShell" and w:
        j = 0
        while j < len(w) and w[j] in BASH_RESERVED:
            j += 1
        w = w[j:]
    if not w:
        return None
    head = base(w[0])
    if head == "eval" and len(w) > 1:
        r = _check_one(" ".join(w[1:]), cwd, tool, mode, depth + 1, False, fed)
        if r:
            return r
    if head in WRAPPER_SHELLS:
        _idx, _err, _husky, saw_prefix = _walk_to_command(cmd_wds, mode, slash_ok, fed)
        base_slash = slash_ok and not saw_prefix
        if base(w[0]).replace(".exe", "") in ("powershell", "pwsh") and not base_slash:
            _pse, ps_idx = _ps_switch_walk(w, base_slash)
            if ps_idx is not None:
                for word in w[ps_idx:]:
                    if "/" in word and ":" in word:
                        return _cannot("a path list a powershell inner command would split")
        inner = shell_inner(w, base_slash)
        if inner is ENCODED:
            return "an encoded PowerShell command, which the guard cannot read"
        if inner is INNER_UNREADABLE:
            return _cannot("a wrapper whose inner command cannot be read")
        if inner:
            bh = base(w[0]).replace(".exe", "")
            if bh in ("powershell", "pwsh"):
                im, child_slash = "powershell", base_slash
            elif bh in ("cmd", "cmd.exe"):
                im, child_slash = "cmd", False
            elif bh in ("bash", "sh"):
                im, child_slash = "bash", False
            else:
                im, child_slash = mode, False
            r = _check_one(inner, cwd, tool, im, depth + 1, child_slash, fed)
            if r:
                return r
    if head in ("find", "find.exe"):
        err, clauses = _find_clauses(w)
        if err:
            return err
        for clause in clauses:
            if _too_long():
                return _cannot("too long to read in time")
            if clause:
                r = _find_brace_refusal(clause, mode, depth + 1)
                if r:
                    return r
                r = _check_word_list(clause, command, cwd, tool, mode, depth + 1, False, fed)
                if r:
                    return r
    if base(w[0]) == "cursor-agent" and _names_bridge_review_paths(w):
        return "cursor-agent with handoff/ or run/review/ in its arguments must run through python ~/.claude/cursor-bridge/bridge-run.py"
    started = w[0] if around_the_shim(w[0]) else (program_behind(w) if head in SHELLS else None)
    if started and around_the_shim(started):
        return "starting the Cursor agent as %s, around the bridge's shim (KP-038); start it as cursor-agent, or through bridge-run.py" % started
    if is_git(w):
        helpful = "--help" in w[1:] or "-h" in w[1:]
        for a in w:
            if _alias_names_refused(a):
                return "a git alias that defines a refused command (%s)" % a[:60]
            if _too_long():
                return _cannot("too long to read in time")
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
            if _too_long():
                return _cannot("too long to read in time")
            if skipper:
                return "git %s %s (a commit that skips its checks; the merge policy allows it only for the checkpoint commit, whose subject says `checkpoint` and names the increment before any parenthesis without an accept, merge or release word, and for a builder's hand-off snapshot inside a worktree)" % (sub, skipper)
        if sub == "push" and not helpful:
            r = force_push_reason(args)
            if _too_long():
                return _cannot("too long to read in time")
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
        if sub == "commit" and _short_letters_hold(a, "n") and not snapshot:
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
        if _short_letters_hold(a, "f"):
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
        left = _time_left()
        if left <= 0:
            return False
        p = subprocess.run(["git", "-C", cwd or ".", "-c", "core.fsmonitor=false", "rev-parse", "--git-common-dir"],
                           capture_output=True, text=True, timeout=left, creationflags=NO_WINDOW)
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