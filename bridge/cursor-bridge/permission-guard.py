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


READ_DEPTH_BOUND = 64
_READ_ESCAPES = True


def _ansi_c_decode(s):
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c != "\\" or i + 1 >= n:
            out.append(c); i += 1; continue
        e = s[i + 1]; i += 2
        if e == "a": out.append("\a")
        elif e == "b": out.append("\b")
        elif e == "e": out.append("\x1b")
        elif e == "E": out.append("\x1b")
        elif e == "f": out.append("\f")
        elif e == "n": out.append("\n")
        elif e == "r": out.append("\r")
        elif e == "t": out.append("\t")
        elif e == "v": out.append("\v")
        elif e in ("'", '"', "\\", "?"): out.append(e)
        elif e == "c" and i < n: out.append(""); i += 1
        elif e in "01234567":
            j, o = i, 0
            while j < n and j < i + 3 and s[j] in "01234567":
                o = o * 8 + int(s[j]); j += 1
            if o: out.append(chr(o % 256))
            i = j
        elif e == "x":
            j, hx = i, ""
            while j < n and j < i + 2 and s[j] in "0123456789abcdefABCDEF":
                hx += s[j]; j += 1
            out.append(chr(int(hx or "0", 16) % 256)); i = j
        elif e == "u":
            j, hx = i, ""
            while j < n and j < i + 4 and s[j] in "0123456789abcdefABCDEF":
                hx += s[j]; j += 1
            out.append(chr(int(hx or "0", 16) % 0x110000)); i = j
        elif e == "U":
            j, hx = i, ""
            while j < n and j < i + 8 and s[j] in "0123456789abcdefABCDEF":
                hx += s[j]; j += 1
            out.append(chr(int(hx or "0", 16) % 0x110000)); i = j
        else: out.append(e)
    return "".join(out)


def _strip_outer_parens(s):
    while s.startswith("("):
        d, k = 1, 1
        while k < len(s) and d:
            if s[k] == "(":
                d += 1
            elif s[k] == ")":
                d -= 1
            k += 1
        if d == 0 and k == len(s) and s.endswith(")"):
            s = s[1:-1].strip()
        else:
            break
    while s.endswith(")") and s.count("(") < s.count(")"):
        s = s[:-1].strip()
    while s.startswith("(") and not s.endswith(")"):
        s = s[1:].strip()
    return s


def read_shell(text, backslash_escapes=True):
    """One iterative read: quoting, separators, substitutions, here-documents (R-082)."""
    n = len(text)
    full_cmds, subst_inners, heredocs = [], [], []
    depth_exceeded, saw_subst = False, False
    stack = [{"k": "spl", "buf": [], "cbuf": [], "chain_segs": [], "top": True, "nest": 0, "pd": 0, "cs": 0, "cmt": False, "inh": 0}]
    i, bs_run = 0, 0

    def active_split():
        for fr in reversed(stack):
            if fr["k"] == "spl":
                return fr
        return None

    def heredoc_op_at(i):
        if not text.startswith("<<", i) or text.startswith("<<<", i):
            return False
        return i == 0 or text[i - 1] != "<"

    def flush_spl(fr, chain_too=True):
        seg = "".join(fr["buf"]).strip()
        fr["buf"] = []
        if seg and fr.get("top"):
            full_cmds.append(seg)
        if chain_too:
            cseg = "".join(fr["cbuf"]).strip()
            fr["cbuf"] = []
            if cseg:
                fr["chain_segs"].append(cseg)

    def append_ch(fr, ch):
        fr["buf"].append(ch)
        fr["cbuf"].append(ch)

    def spl_emit(ch):
        sp = active_split()
        if sp:
            append_ch(sp, ch)

    def push_split(top, nest):
        if nest > READ_DEPTH_BOUND:
            nonlocal depth_exceeded
            depth_exceeded = True
        stack.append({"k": "spl", "buf": [], "cbuf": [], "chain_segs": [], "top": top, "nest": nest, "pd": 0, "cs": 0, "cmt": False, "inh": nest})

    def bare_amp(i):
        if i >= n or text[i] != "&":
            return False
        if i > 0 and text[i - 1] in "<>":
            return False
        if i + 1 < n and text[i + 1] in ">&":
            return False
        if i + 1 < n and text[i + 1] == "&":
            return False
        return True

    def try_sep(i, fr, subst=False):
        chain_hit = full_hit = None
        if i + 1 < n and text[i:i + 2] in ("&&", "||"):
            chain_hit = full_hit = i + 2
        elif text[i] in (";", "\n"):
            bb = "".join(fr["buf"])
            heredoc_op = re.search(r"(?<!<)<<-?(?![<-])", bb)
            if not (subst and text[i] == "\n" and heredoc_op):
                chain_hit = full_hit = i + 1
        elif bare_amp(i):
            chain_hit = full_hit = i + 1
        elif text[i] == "|":
            full_hit = i + 1
        elif not subst and text[i] in "()":
            full_hit = i + 1
        if full_hit is not None:
            flush_spl(fr, chain_too=chain_hit is not None)
            return full_hit
        return None

    def skip_heredoc_body(i, delim, strip_tabs):
        j = i
        while j < n:
            line_end = text.find("\n", j)
            if line_end < 0:
                return n
            line = text[j:line_end]
            if strip_tabs:
                line = line.lstrip("\t")
            if line.lstrip("\t").rstrip(" \t") == delim:
                return line_end + 1
            j = line_end + 1
        return n

    def parse_heredoc_delim(i):
        j = i
        quoted = None
        while j < n and text[j] in " \t":
            j += 1
        if j >= n:
            return None
        if text[j] in ("'", '"'):
            quoted, q = text[j], j + 1
            while q < n and text[q] != quoted:
                q += 1
            return text[j + 1:q], quoted, q + 1
        start = j
        while j < n and text[j] not in " \t\n;|&":
            j += 1
        return text[start:j], None, j

    def in_dq():
        return any(fr["k"] == "dq" for fr in stack)

    def absorb_expanded_heredoc(hd_start, body_end, dj, delim, quoted, strip_tabs):
        nonlocal saw_subst
        if quoted is not None:
            return
        blob = text[hd_start:body_end]
        if "\n" not in blob:
            return
        body = blob.split("\n", 1)[1]
        lines = body.splitlines()
        if lines:
            last = lines[-1]
            if strip_tabs:
                last = last.lstrip("\t")
            if last.rstrip(" \t") == delim:
                body = "\n".join(lines[:-1])
        if not body.strip():
            return
        inn = read_shell(body, backslash_escapes=backslash_escapes)
        saw_subst = saw_subst or inn["hassub"]
        for s in inn["subs"]:
            if s.strip():
                subst_inners.append(s.strip())
        for c in inn["full"]:
            if c.strip():
                subst_inners.append(c.strip())

    while i < n:
        if depth_exceeded:
            break
        fr = active_split()
        if fr and fr["cmt"]:
            if text[i] == "\n":
                fr["cmt"] = False
                fr["inh"] = max(0, fr["inh"] - 1)
                flush_spl(fr)
            i += 1
            continue
        topk = stack[-1]["k"] if stack else ""
        if topk == "sq":
            fr = stack[-1]
            fr["buf"].append(text[i])
            spl_emit(text[i])
            if text[i] == "'":
                stack.pop()
            i += 1
            bs_run = 0
            continue
        if topk == "dq":
            fr = stack[-1]
            c = text[i]
            esc = backslash_escapes and bs_run % 2 == 1
            if c == "\\" and backslash_escapes and not esc:
                fr["buf"].append(c); spl_emit(c); bs_run += 1; i += 1; continue
            if c == '"' and not esc:
                spl_emit(c); stack.pop(); bs_run = 0; i += 1; continue
            if not esc and text.startswith("$(", i):
                fr["buf"].append("$("); spl_emit("$("); i += 2; bs_run = 0
                saw_subst = True
                push_split(False, fr.get("nest", 0) + 1)
                stack.append({"k": "sub", "start": i, "pd": 1, "cs": 0})
                continue
            if not esc and c == "`":
                fr["buf"].append(c); spl_emit(c); i += 1; bs_run = 0
                saw_subst = True
                stack.append({"k": "btf", "buf": [], "nest": fr.get("nest", 0)})
                continue
            fr["buf"].append(c); spl_emit(c); bs_run = 0; i += 1
            continue
        if topk == "ansi":
            fr = stack[-1]
            c = text[i]
            if c == "\\" and i + 1 < n:
                fr["buf"].append(text[i:i + 2])
                spl_emit(text[i:i + 2])
                i += 2; continue
            fr["buf"].append(c)
            spl_emit(c)
            if c == "'":
                stack.pop()
            i += 1
            bs_run = 0
            continue
        if topk == "loc":
            fr = stack[-1]
            c = text[i]
            esc = backslash_escapes and bs_run % 2 == 1
            if c == "\\" and backslash_escapes and not esc:
                fr["buf"].append(c); spl_emit(c); bs_run += 1; i += 1; continue
            if c == '"' and not esc:
                spl_emit(c); stack.pop(); bs_run = 0; i += 1; continue
            fr["buf"].append(c); spl_emit(c); bs_run = 0; i += 1
            continue
        if topk == "br":
            fr = stack[-1]
            if fr["bd"] <= 0:
                stack.pop()
                continue
            c = text[i]
            if c == "'":
                stack.append({"k": "sq", "buf": ["'"]}); i += 1; bs_run = 0; continue
            if c == '"':
                stack.append({"k": "dq", "buf": ['"'], "nest": 0}); i += 1; bs_run = 0; continue
            if text.startswith("$'", i):
                stack.append({"k": "ansi", "buf": list("$'")}); i += 2; bs_run = 0; continue
            if text.startswith('$"', i):
                stack.append({"k": "loc", "buf": list('$"')}); i += 2; bs_run = 0; continue
            if text.startswith("${", i):
                stack.append({"k": "br", "bd": 1, "buf": []}); i += 2; bs_run = 0; continue
            if not in_dq() and text.startswith("$(", i) and bs_run % 2 == 0:
                saw_subst = True
                push_split(False, fr["nest"] + 1)
                stack.append({"k": "sub", "start": i + 2, "pd": 1, "cs": 0})
                i += 2; bs_run = 0; continue
            if text[i] == "{":
                fr["bd"] += 1
            elif text[i] == "}":
                fr["bd"] -= 1
                if fr["bd"] == 0:
                    stack.pop(); i += 1; bs_run = 0; continue
            i += 1; bs_run = 0
            continue
        if topk == "btf":
            fr = stack[-1]
            c = text[i]
            if c == "\\" and i + 1 < n and backslash_escapes:
                fr["buf"].append(text[i:i + 2]); i += 2; continue
            if c == "`" and (not backslash_escapes or bs_run % 2 == 0):
                body = "".join(fr["buf"])
                stack.pop()
                spl = active_split()
                if spl:
                    spl["buf"].append("`")
                subst_inners.append(body)
                saw_subst = True
                push_split(False, fr["nest"] + 1)
                bi, bn = 0, len(body)
                bt_bs = 0
                while bi < bn:
                    bc = body[bi]
                    sp = active_split()
                    if not sp:
                        break
                    if sp["cmt"]:
                        if bc == "\n":
                            sp["cmt"] = False
                        bi += 1; continue
                    if bc == "#" and sp["inh"] == 0 and (not sp["buf"] or sp["buf"][-1].isspace()):
                        sp["cmt"] = True; bi += 1; continue
                    if bc == "\\" and backslash_escapes:
                        sp["buf"].append(bc); bt_bs += 1; bi += 1; continue
                    escd = backslash_escapes and bt_bs % 2 == 1
                    bt_bs = 0
                    if not escd and body.startswith("$(", bi):
                        saw_subst = True
                        flush_spl(sp)
                        push_split(False, fr["nest"] + 2)
                        stack.append({"k": "sub", "start": bi + 2, "pd": 1, "cs": 0})
                        bi += 2; continue
                    ns = try_sep(bi, sp, subst=True)
                    if ns is not None:
                        bi = ns; continue
                    if not escd and bc == "`":
                        stack.append({"k": "btf", "buf": [], "nest": fr["nest"] + 1})
                        bi += 1; continue
                    if not escd and bc == "'":
                        stack.append({"k": "sq", "buf": ["'"]}); bi += 1; continue
                    if not escd and bc == '"':
                        stack.append({"k": "dq", "buf": ['"'], "nest": 0}); bi += 1; continue
                    sp["buf"].append(bc); bi += 1
                flush_spl(active_split())
                while stack and stack[-1]["k"] == "spl" and stack[-1]["nest"] > fr["nest"]:
                    stack.pop()
                if spl:
                    spl["buf"].append("`")
                i += 1; bs_run = 0
                continue
            fr["buf"].append(c); i += 1
            if c == "\\" and backslash_escapes:
                bs_run += 1
            else:
                bs_run = 0
            continue
        if topk == "sub":
            fr = stack[-1]
            sp = active_split()
            if not sp:
                i += 1; continue
            c = text[i]
            if sp["cmt"]:
                if c == "\n":
                    sp["cmt"] = False
                i += 1; continue
            if c == "\\" and backslash_escapes:
                append_ch(sp, c); bs_run += 1; i += 1; continue
            escd = backslash_escapes and bs_run % 2 == 0 and False
            escd = backslash_escapes and (bs_run % 2 == 1)
            bs_run = 0
            if escd:
                append_ch(sp, c); i += 1; continue
            if c == "#" and (not sp["buf"] or sp["buf"][-1].isspace() or sp["buf"][-1] in ";|&"):
                sp["cmt"] = True; i += 1; continue
            if c == "'":
                append_ch(sp, c); stack.append({"k": "sq", "buf": ["'"]}); i += 1; continue
            if c == '"':
                append_ch(sp, c); stack.append({"k": "dq", "buf": ['"'], "nest": sp["nest"]}); i += 1; continue
            if text.startswith("$'", i):
                append_ch(sp, "$'"); stack.append({"k": "ansi", "buf": list("$'")}); i += 2; continue
            if text.startswith('$"', i):
                append_ch(sp, '$"'); stack.append({"k": "loc", "buf": list('$"')}); i += 2; continue
            if text.startswith("${", i):
                append_ch(sp, "${"); stack.append({"k": "br", "bd": 1, "buf": [], "nest": sp["nest"]}); i += 2; continue
            if text.startswith("$(", i):
                saw_subst = True
                append_ch(sp, "$(")
                push_split(False, sp["nest"] + 1)
                stack.append({"k": "sub", "start": i + 2, "pd": 1, "cs": 0})
                i += 2; continue
            if not in_dq() and text.startswith("<(", i):
                saw_subst = True
                append_ch(sp, text[i:i + 2])
                push_split(False, sp["nest"] + 1)
                stack.append({"k": "sub", "start": i + 2, "pd": 1, "cs": 0, "proc": 1})
                i += 2; continue
            if not in_dq() and text.startswith(">(", i):
                saw_subst = True
                append_ch(sp, text[i:i + 2])
                push_split(False, sp["nest"] + 1)
                stack.append({"k": "sub", "start": i + 2, "pd": 1, "cs": 0, "proc": 1})
                i += 2; continue
            if c == "`":
                saw_subst = True
                append_ch(sp, c)
                stack.append({"k": "btf", "buf": [], "nest": sp["nest"]})
                i += 1; continue
            if not in_dq() and heredoc_op_at(i):
                strip_tabs = text.startswith("<<-", i)
                adj = 3 if strip_tabs else 2
                delim, quoted, dj = parse_heredoc_delim(i + adj)
                if delim:
                    body_end = skip_heredoc_body(dj, delim, strip_tabs)
                    line_start = text[:i].rfind("\n") + 1
                    heredocs.append({"start": i, "end": body_end, "delim": delim, "quoted": quoted, "strip": strip_tabs, "line": text[line_start:dj]})
                    for ch in text[i:dj]:
                        append_ch(sp, ch)
                    absorb_expanded_heredoc(i, body_end, dj, delim, quoted, strip_tabs)
                    i = body_end
                    continue
            if c == "(":
                fr["pd"] += 1; append_ch(sp, c); i += 1; continue
            if c == ")":
                buf_s = "".join(sp["buf"])
                in_case_pat = fr.get("cs") >= 2 if fr.get("cs") else False
                if not in_case_pat and fr.get("cs") == 1 and re.search(r"\sin\s", buf_s) and re.search(r"(?:^|[\s(])case", buf_s):
                    in_case_pat = True
                    fr["cs"] = 3
                elif in_case_pat and fr.get("cs") == 2:
                    fr["cs"] = 3
                if in_case_pat:
                    append_ch(sp, c); i += 1; continue
                fr["pd"] -= 1
                if fr["pd"] == 0:
                    body = text[fr["start"]:i].strip()
                    if body:
                        subst_inners.append(body)
                    flush_spl(sp)
                    stack.pop()
                    while stack and stack[-1]["k"] == "spl" and not stack[-1].get("top"):
                        stack.pop()
                    if stack and stack[-1]["k"] == "dq":
                        stack[-1]["buf"].append(")")
                        spl_emit(")")
                    i += 1; continue
                append_ch(sp, c); i += 1; continue
            ns = try_sep(i, sp, subst=True)
            if ns is not None:
                i = ns; continue
            if text.startswith(";;", i):
                append_ch(sp, ";;"); i += 2
                if fr.get("cs") == 3:
                    fr["cs"] = 2
                continue
            if c.isspace():
                tail = "".join(sp["buf"])
                if re.search(r"(?:^|[\s(])case(?:\s|$)", tail):
                    fr["cs"] = 1
                elif fr.get("cs") == 1 and re.search(r"\sin\s", tail + c):
                    fr["cs"] = 2
                if re.search(r"\sesac(?:\s|$)", tail + c):
                    fr["cs"] = 0
            append_ch(sp, c); i += 1; continue
        if not fr:
            i += 1; continue
        c = text[i]
        if c == "\\" and backslash_escapes:
            append_ch(fr, c); bs_run += 1; i += 1; continue
        escd = backslash_escapes and (bs_run % 2 == 1)
        bs_run = 0
        if escd:
            append_ch(fr, c); i += 1; continue
        if c == "#" and (not fr["buf"] or fr["buf"][-1].isspace() or fr["buf"][-1] in ";|&("):
            fr["cmt"] = True; i += 1; continue
        if c == "'":
            append_ch(fr, c); stack.append({"k": "sq", "buf": ["'"]}); i += 1; continue
        if c == '"':
            append_ch(fr, c); stack.append({"k": "dq", "buf": ['"'], "nest": fr["nest"]}); i += 1; continue
        if text.startswith("$'", i):
            append_ch(fr, "$'"); stack.append({"k": "ansi", "buf": list("$'")}); i += 2; continue
        if text.startswith('$"', i):
            append_ch(fr, '$"'); stack.append({"k": "loc", "buf": list('$"')}); i += 2; continue
        if text.startswith("${", i):
            append_ch(fr, "${"); stack.append({"k": "br", "bd": 1, "buf": [], "nest": fr["nest"]}); i += 2; continue
        if text.startswith("$(", i):
            saw_subst = True
            append_ch(fr, "$(")
            push_split(False, fr["nest"] + 1)
            stack.append({"k": "sub", "start": i + 2, "pd": 1, "cs": 0})
            i += 2; continue
        if not in_dq() and text.startswith("<(", i):
            saw_subst = True
            append_ch(fr, text[i:i + 2])
            push_split(False, fr["nest"] + 1)
            stack.append({"k": "sub", "start": i + 2, "pd": 1, "cs": 0, "proc": 1})
            i += 2; continue
        if not in_dq() and text.startswith(">(", i):
            saw_subst = True
            append_ch(fr, text[i:i + 2])
            push_split(False, fr["nest"] + 1)
            stack.append({"k": "sub", "start": i + 2, "pd": 1, "cs": 0, "proc": 1})
            i += 2; continue
        if c == "`":
            saw_subst = True
            append_ch(fr, c)
            stack.append({"k": "btf", "buf": [], "nest": fr["nest"]})
            i += 1; continue
        if not in_dq() and heredoc_op_at(i):
            strip_tabs = text.startswith("<<-", i)
            adj = 3 if strip_tabs else 2
            delim, quoted, dj = parse_heredoc_delim(i + adj)
            if delim:
                body_end = skip_heredoc_body(dj, delim, strip_tabs)
                prefix = text[:i]
                line_start = prefix.rfind("\n") + 1
                heredocs.append({"start": i, "end": body_end, "delim": delim, "quoted": quoted, "strip": strip_tabs, "line": text[line_start:dj]})
                for ch in text[i:dj]:
                    append_ch(fr, ch)
                absorb_expanded_heredoc(i, body_end, dj, delim, quoted, strip_tabs)
                i = body_end
                if fr.get("top"):
                    flush_spl(fr, chain_too=False)
                continue
        ns = try_sep(i, fr)
        if ns is not None:
            i = ns; continue
        append_ch(fr, c); i += 1
    flush_spl(stack[0]) if stack else None
    chain_cmds = stack[0]["chain_segs"] if stack else []
    return {"full": full_cmds, "chain": chain_cmds, "subs": subst_inners, "heredocs": heredocs,
            "deep": depth_exceeded, "hassub": saw_subst, "text": text}


def _parsed_snapshot(text, backslash_escapes=True):
    if not hasattr(_parsed_snapshot, "_cache"):
        _parsed_snapshot._cache = {}
    key = (text, backslash_escapes)
    if key not in _parsed_snapshot._cache:
        _parsed_snapshot._cache[key] = read_shell(text, backslash_escapes=backslash_escapes)
        if len(_parsed_snapshot._cache) > 8:
            _parsed_snapshot._cache.pop(next(iter(_parsed_snapshot._cache)))
    return _parsed_snapshot._cache[key]


def _apply_heredocs(text, parsed):
    if not parsed["heredocs"]:
        return text
    out, pos = [], 0
    for hd in sorted(parsed["heredocs"], key=lambda h: h["start"]):
        out.append(text[pos:hd["start"]])
        line = hd["line"]
        head = strip_prefix(words(line.split("<<", 1)[0]))
        blob = text[hd["start"]:hd["end"]]
        first = blob.split("\n", 1)[0]
        if len(blob.split("\n", 1)) > 1:
            body = blob.split("\n", 1)[1]
        else:
            body = ""
        shell_reads = head and base(head[0]) in WRAPPER_SHELLS
        if "|" in first:
            parts = first.split("|")
            for p in parts[1:]:
                if strip_prefix(words(p.strip())) and base(words(p.strip())[0]) in WRAPPER_SHELLS:
                    shell_reads = True
                    break
        if shell_reads and body:
            out.append("\n" + body)
        else:
            out.append(line.split("<<", 1)[0].rstrip() + "\n")
        pos = hd["end"]
    out.append(text[pos:])
    return "".join(out)


def strip_heredocs(text):
    """A here-document's body is data unless a shell reads it: then its lines are checked."""
    parsed = _parsed_snapshot(text, backslash_escapes=_READ_ESCAPES)
    return _apply_heredocs(text, parsed)


def _heredoc_shell_reads(hd, text):
    line = hd["line"]
    first = text[hd["start"]:hd["end"]].split("\n", 1)[0]
    head = strip_prefix(words(line.split("<<", 1)[0]))
    shell_reads = head and base(head[0]) in WRAPPER_SHELLS
    if "|" in first:
        for part in first.split("|")[1:]:
            if strip_prefix(words(part.strip())) and base(words(part.strip())[0]) in WRAPPER_SHELLS:
                return True
    return shell_reads


def _heredoc_body(text, hd):
    blob = text[hd["start"]:hd["end"]]
    if "\n" not in blob:
        return ""
    body = blob.split("\n", 1)[1]
    lines = body.splitlines()
    if lines:
        last = lines[-1]
        if hd["strip"]:
            last = last.lstrip("\t")
        if last.rstrip(" \t") == hd["delim"]:
            body = "\n".join(lines[:-1])
    return body


def split_commands(text):
    """Break a shell command line into simple commands (one read_shell pass)."""
    p = _parsed_snapshot(text, backslash_escapes=_READ_ESCAPES)
    if p["deep"]:
        return []
    seen, out = set(), []
    for c in p["full"]:
        cs = c.strip()
        if cs and cs not in seen:
            seen.add(cs)
            out.append(cs)
    for s in p["subs"]:
        ss = s.strip()
        if not ss:
            continue
        inner = _parsed_snapshot(ss, backslash_escapes=_READ_ESCAPES)
        for c in inner["full"]:
            cs = c.strip()
            if cs and cs not in seen:
                seen.add(cs)
                out.append(cs)
        for b in inner["subs"]:
            bs = b.strip()
            if bs and bs not in seen:
                seen.add(bs)
                out.append(bs)
    for hd in p["heredocs"]:
        if not _heredoc_shell_reads(hd, text):
            continue
        body = _heredoc_body(text, hd)
        for sc in split_commands(body):
            if sc not in seen:
                seen.add(sc)
                out.append(sc)
    return out


def in_workspace(cwd):
    """A bridge Workspace: the folder the hook runs in holds the project's status file."""
    return bool(cwd) and os.path.isfile(os.path.join(cwd, "docs", "PROJECT_STATUS.md"))


def chain_parts(text):
    """Commands chained with &&, ||, ; or newline (quotes respected); a pipe stays one command."""
    p = _parsed_snapshot(text, backslash_escapes=_READ_ESCAPES)
    return [_strip_outer_parens(x) for x in p["chain"] if x.strip()]


def chain_parts_with_substitutions(text):
    p = _parsed_snapshot(text)
    parts = [_strip_outer_parens(x) for x in p["chain"] if x.strip()]
    expanded = list(parts)
    for sub in p["subs"]:
        sp = _parsed_snapshot(sub)
        sub_parts = [_strip_outer_parens(x) for x in sp["chain"] if x.strip()]
        if len(sub_parts) >= 2:
            expanded.extend(sub_parts)
    return expanded


def contains_command_substitution(text):
    return _parsed_snapshot(text, backslash_escapes=_READ_ESCAPES)["hassub"]


def gh_api_unquoted_ampersand_reason(command):
    """Unquoted & glued into a gh api argument (checked on parsed commands)."""
    text = strip_heredocs(command)
    i, n = 0, len(text)
    in_sq = in_dq = False
    at_cmd = True
    in_gh = False

    def cmd_head(j):
        t = text[j:].lstrip()
        return t.startswith("gh api") or t.startswith("gh.exe api")

    while i < n:
        c = text[i]
        if in_sq:
            in_sq = c != "'"
            i += 1; continue
        if in_dq:
            if c == "\\" and i + 1 < n:
                i += 2; continue
            if c == '"':
                in_dq = False
            i += 1; continue
        if c == "'":
            in_sq = True; i += 1; continue
        if c == '"':
            in_dq = True; i += 1; continue
        if text.startswith("$'", i):
            j = i + 2
            while j < n and text[j] != "'":
                j += 2 if text[j] == "\\" and j + 1 < n else 1
            i = j + 1; continue
        if not in_sq and not in_dq and not c.isspace():
            if at_cmd:
                in_gh = cmd_head(i)
                at_cmd = False
        if in_gh and c == "&" and (i == 0 or text[i - 1] not in "<>") and (i + 1 >= n or text[i + 1] not in ">&"):
            if i + 1 < n and text[i + 1] == "&":
                in_gh = False; at_cmd = True; i += 2; continue
            prev = text[i - 1] if i > 0 else " "
            nxt = text[i + 1] if i + 1 < n else " "
            if (not prev.isspace() and prev not in ";|&") or (not nxt.isspace() and nxt not in ";|&\n"):
                return "gh api with an unquoted & in an argument (quote the endpoint or URL so the shell does not split on &)"
        if c in (";", "\n") or text.startswith("&&", i) or text.startswith("||", i):
            in_gh = False; at_cmd = True
            i += 2 if text.startswith("&&", i) or text.startswith("||", i) else 1
            continue
        if c == "&":
            if i > 0 and text[i - 1] in "<>":
                i += 1; continue
            if i + 1 < n and text[i + 1] in ">&":
                i += 1; continue
            if i + 1 < n and text[i + 1] == "&":
                in_gh = False; at_cmd = True; i += 2; continue
            in_gh = False; at_cmd = True
            i += 1; continue
        i += 1
    return None


def _shell_words(command):
    parsed = _parsed_snapshot(command)
    return _tokenize_parsed(command, parsed)


def _tokenize_parsed(text, parsed):
    words, buf, i, n = [], [], 0, len(text)
    bs_run = 0

    def flush():
        if buf:
            s = "".join(buf)
            if s.startswith("$'") and s.endswith("'"):
                words.append(_ansi_c_decode(s[2:-1]))
            elif s.startswith('$"') and s.endswith('"'):
                words.append(s[2:-1])
            else:
                words.append(s)
            buf[:] = []

    while i < n:
        c = text[i]
        if c.isspace() and not buf:
            i += 1; continue
        if c == "\\" and not buf and i + 1 < n:
            buf.append(text[i:i + 2]); i += 2; continue
        if c in ("'", '"') and not buf:
            q, j = c, i + 1
            while j < n and text[j] != q:
                if q == '"' and text[j] == "\\" and j + 1 < n:
                    j += 2; continue
                j += 1
            words.append(text[i + 1:j] if j < n else text[i + 1:])
            i = j + 1 if j < n else n
            continue
        if text.startswith("$'", i):
            j = i + 2
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    j += 2; continue
                if text[j] == "'":
                    break
                j += 1
            words.append(_ansi_c_decode(text[i + 2:j])); i = j + 1; continue
        if text.startswith('$"', i):
            j = i + 2
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    j += 2; continue
                if text[j] == '"':
                    break
                j += 1
            words.append(text[i + 2:j]); i = j + 1; continue
        if c in " \t\n" and buf:
            flush(); i += 1; continue
        buf.append(c); i += 1
    flush()
    return words


def words(command):
    if "$'" in command or '$"' in command:
        toks = _shell_words(command)
    else:
        try:
            toks = shlex.split(command, posix=True)
        except ValueError:
            toks = command.split()
    out = []
    for t in toks:
        if t.startswith("$'") and t.endswith("'") and len(t) > 2:
            out.append(_ansi_c_decode(t[2:-1]))
        elif t.startswith('$"') and t.endswith('"') and len(t) > 2:
            out.append(t[2:-1])
        else:
            out.append(t)
    return out


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


def _part_state_change(part, parsed):
    w = strip_prefix(words(part))
    if w and state_changing(w):
        return w
    pp = _parsed_snapshot(part)
    for sub in pp["subs"]:
        for cmd in pp["full"] + (_parsed_snapshot(sub)["full"] if sub else []):
            sw = strip_prefix(words(cmd))
            if sw and state_changing(sw):
                return sw
    for sub in pp["subs"]:
        sw = strip_prefix(words(sub))
        if sw and state_changing(sw):
            return sw
    return None


def chain_reason(command, cwd):
    """Inside a Workspace, a chain carrying a state change or wrapped in cd is refused (rule 8)."""
    if not in_workspace(cwd):
        return None
    parsed_full = _parsed_snapshot(command)
    parts = chain_parts_with_substitutions(command)
    if len(parts) < 2:
        top = [_strip_outer_parens(x) for x in parsed_full["chain"] if x.strip()]
        if len(top) < 2:
            return None
        parts = top
    heads = [strip_prefix(words(p)) for p in parts]
    heads = [h for h in heads if h]
    for h in list(heads):
        if base(h[0]) == "eval" and len(h) > 1:
            heads += [strip_prefix(words(p)) for p in chain_parts(" ".join(h[1:]))]
    if heads and base(heads[0][0]) == "cd":
        return "a command wrapped in cd (rule 8: never wrap a command in cd; run it with the path it needs, or git -C)"
    for i, p in enumerate(parts):
        w = _part_state_change(p, None)
        if w:
            return "a chain of %d commands carrying %s (rule 8: one command per call, never chained with &&, ; or ||; the allowlist and the guard read one command, and a chain once built an increment on a merged branch)" % (len(parts), " ".join(w[:2]))
    if len(parts) >= 2:
        for sub in parsed_full["subs"]:
            sw = strip_prefix(words(sub))
            if sw and state_changing(sw):
                return "a chain of %d commands carrying %s (rule 8: one command per call, never chained with &&, ; or ||; the allowlist and the guard read one command, and a chain once built an increment on a merged branch)" % (len(parts), " ".join(sw[:2]))
    for w in heads:
        if state_changing(w):
            return "a chain of %d commands carrying %s (rule 8: one command per call, never chained with &&, ; or ||; the allowlist and the guard read one command, and a chain once built an increment on a merged branch)" % (len(parts), " ".join(w[:2]))
    return None


def leading_husky_zero(simple):
    """True when HUSKY=0 is a leading shell assignment, not text inside a quoted argument."""
    w = words(simple)
    i = 0
    while i < len(w):
        tok = w[i]
        if tok == "HUSKY=0":
            return True
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok):
            i += 1
            continue
        if tok in ("&", ".", "{", "}", "then", "do", "else", "elif", "if", "while", "until", "!"):
            i += 1
            continue
        name = tok.replace(".exe", "")
        if name in ("xargs", "env", "nice", "nohup", "stdbuf", "time", "sudo", "command", "builtin", "exec", "timeout", "setsid", "winpty"):
            i += 1
            if name == "env":
                vals = VALUE_OPTIONS.get("env", ())
                while i < len(w):
                    if w[i] == "HUSKY=0":
                        return True
                    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w[i]):
                        i += 1
                        continue
                    if w[i].startswith("-"):
                        opt = w[i]; i += 1
                        if opt in vals and i < len(w):
                            i += 1
                        continue
                    break
                continue
            vals = VALUE_OPTIONS.get(name, ())
            while i < len(w) and (w[i].startswith("-") or (name == "xargs" and (w[i].isdigit() or w[i] == "{}"))):
                opt = w[i]
                i += 1
                if opt in vals and i < len(w):
                    i += 1
            if name == "timeout" and i < len(w):
                i += 1
            continue
        break
    return False


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
        if name in ("xargs", "env", "nice", "nohup", "stdbuf", "time", "sudo", "command", "builtin", "exec", "timeout", "setsid", "winpty"):
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
        p = _parsed_snapshot(command)

        def first_heredoc_subject(parsed, src):
            for hd in parsed["heredocs"]:
                blob = src[hd["start"]:hd["end"]]
                if "\n" not in blob:
                    continue
                body = blob.split("\n", 1)[1]
                lines = [l for l in body.splitlines() if l.strip() and not re.match(r"^\w+\s*$", l) and l.rstrip(" \t") != hd["delim"]]
                if lines:
                    return lines[0].strip()
            return None

        subj = first_heredoc_subject(p, command)
        if subj:
            return subj
        for sub in p["subs"]:
            subj = first_heredoc_subject(_parsed_snapshot(sub), sub)
            if subj:
                return subj
            for line in sub.splitlines():
                t = line.strip()
                if t and not re.match(r"^\w+\s*<<", t):
                    return t
    return msg.strip()


def _join_continuations(command, tool):
    out, i, n, bs = [], 0, len(command), 0
    while i < n:
        if command[i] == "\\":
            bs += 1
            out.append(command[i])
            i += 1
            if i < n and command[i] in "\r\n":
                if tool == "PowerShell" or bs % 2 == 1:
                    while i < n and command[i] in "\r\n":
                        i += 1
                    if tool == "PowerShell":
                        out.append(" ")
                else:
                    out.append(command[i]); i += 1
                bs = 0
                continue
            continue
        if tool == "PowerShell" and command[i] == "`" and i + 1 < n and command[i + 1] in "\r\n":
            while i + 1 < n and command[i + 1] in "\r\n":
                i += 1
            out.append(" ")
            i += 1
            bs = 0
            continue
        if tool == "Bash" and command[i] == "`" and i + 1 < n and command[i + 1] in "\r\n":
            out.append(command[i]); i += 1
            while i < n and command[i] in "\r\n":
                out.append(command[i]); i += 1
            bs = 0
            continue
        out.append(command[i])
        bs = 0
        i += 1
    return "".join(out)


def in_worktree(w, cwd):
    """A commit made inside a builder's worktree (`-C ../Worktrees/x`, or a cwd under Worktrees/)."""
    paths = [cwd or ""] + [w[i + 1] for i, a in enumerate(w) if a == "-C" and i + 1 < len(w)]
    return any(re.search(r"[\\/]Worktrees[\\/]", p) for p in paths)


def check(command, cwd=None, tool="Bash", _depth=0):
    """Return the reason to refuse, or None."""
    if tool == "PowerShell":
        r1 = _check_one(command, cwd, "Bash", _depth, backslash_escapes=True)
        r2 = _check_one(command, cwd, "PowerShell", _depth, backslash_escapes=False)
        return r1 or r2
    return _check_one(command, cwd, tool, _depth, backslash_escapes=True)


def _check_one(command, cwd, tool, depth, backslash_escapes=True):
    if depth > READ_DEPTH_BOUND:
        return "command nests too deeply to read"
    command = _join_continuations(command, tool)
    global _READ_ESCAPES
    _parsed_snapshot._cache = {}
    _READ_ESCAPES = backslash_escapes
    parsed = _parsed_snapshot(command, backslash_escapes=backslash_escapes)
    if parsed["deep"]:
        return "command nests too deeply to read"
    r = gh_api_unquoted_ampersand_reason(command)
    if r:
        return r
    r = chain_reason(command, cwd)
    if r:
        return r
    for simple in split_commands(command):
        w = strip_prefix(words(simple))
        if not w:
            continue
        head = base(w[0])
        husky = leading_husky_zero(simple)
        if husky:
            wgit = strip_prefix(words(simple))
            if wgit and is_git(wgit):
                sub, _ = git_subcommand(wgit)
                if sub in ("commit", "push", "merge"):
                    return "HUSKY=0 switches the hook runner off (a commit that skips its checks; rule 4)"
            if head in ("eval", "bash", "bash.exe", "sh", "sh.exe", "setsid", "winpty"):
                inner = shell_inner(w) if head not in ("eval", "setsid", "winpty") else " ".join(w[1:])
                if inner:
                    iw = strip_prefix(words(inner))
                    if iw and is_git(iw):
                        sub, _ = git_subcommand(iw)
                        if sub in ("commit", "push", "merge"):
                            return "HUSKY=0 switches the hook runner off (a commit that skips its checks; rule 4)"
        if head == "eval" and len(w) > 1:
            r = _check_one(" ".join(w[1:]), cwd, tool, depth + 1, backslash_escapes=backslash_escapes)
            if r:
                return r
        if head in WRAPPER_SHELLS:
            inner = shell_inner(w)
            if inner is ENCODED:
                return "an encoded PowerShell command, which the guard cannot read"
            if inner:
                ps_tool = tool if base(w[0]).replace(".exe", "") in ("powershell", "pwsh") else tool
                r = check(inner, cwd, tool=ps_tool, _depth=depth + 1)
                if r:
                    return r
        if head in ("find", "find.exe") and any(t in ("-exec", "-execdir", "-ok") for t in w):
            j = next(k for k, t in enumerate(w) if t in ("-exec", "-execdir", "-ok"))
            inner = " ".join(t for t in w[j + 1:] if t not in (";", "+", "{}"))
            r = _check_one(inner, cwd, tool, depth + 1, backslash_escapes=backslash_escapes) if inner else None
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
                if parsed["hassub"]:
                    return "gh api graphql with a query built by a command substitution, which the guard cannot read (write the query on the command line)"
                if any(t == "--input" or t.startswith("--input=") or t.startswith("@") or "=@" in t for t in args):
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
    reason = check(command, data.get("cwd") or os.getcwd(), tool=tool)
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
