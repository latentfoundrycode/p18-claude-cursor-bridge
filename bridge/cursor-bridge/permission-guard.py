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


def _join_bs_newlines(text, backslash_escapes):
    if not backslash_escapes:
        return text
    out, i, n = [], 0, len(text)
    while i < n:
        if text[i] == "\\":
            j, bs = i, 0
            while j < n and text[j] == "\\":
                bs += 1
                j += 1
            if j < n and text[j] in "\r\n" and bs % 2 == 1:
                out.append("\\" * (bs - 1))
                while j < n and text[j] in "\r\n":
                    j += 1
                i = j
                continue
            out.append("\\" * bs)
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def read_shell(text, backslash_escapes=True):
    """One iterative read: quoting, separators, substitutions, here-documents (R-082)."""
    text = _join_bs_newlines(text, backslash_escapes)
    n = len(text)
    full_cmds, subst_inners, heredocs, cmd_words_list, sub_chains_list = [], [], [], [], []
    depth_exceeded, saw_subst = False, False
    unreadable, gh_amp_reason = None, None
    stack = [{"k": "spl", "buf": [], "cbuf": [], "chain_segs": [], "top": True, "nest": 0, "pd": 0, "cmt": False, "inh": 0,
              "wmerge": [], "words": [], "chain_wds": [], "gh": False, "hd_line": False}]
    i, bs_run = 0, 0

    def refuse(msg):
        nonlocal unreadable
        if unreadable is None:
            unreadable = msg

    def active_split():
        for fr in reversed(stack):
            if fr["k"] == "spl":
                return fr
        return None

    def in_quote():
        return any(fr["k"] in ("sq", "dq", "ansi", "loc") for fr in stack)

    def subst_counts():
        return not any(fr["k"] in ("sq", "ansi") for fr in stack)

    def mark_gh(fr):
        ws = fr["words"]
        if fr.get("wmerge"):
            ws = ws + ["".join(fr["wmerge"])]
        i = 0
        while i < len(ws):
            if base(ws[i]) not in ("gh", "gh.exe"):
                i += 1
                continue
            j = i + 1
            while j < len(ws):
                t = ws[j]
                if t == "api":
                    fr["gh"] = True
                    return
                if t.startswith("-"):
                    j += 1
                    if j < len(ws) and not ws[j].startswith("-"):
                        j += 1
                    continue
                j += 1
            i += 1

    def flush_word(fr):
        if not fr.get("wmerge"):
            return
        w = "".join(fr["wmerge"])
        fr["wmerge"] = []
        fr["words"].append(w)
        if w == "case":
            refuse("the guard cannot read the command: a case statement")
        mark_gh(fr)

    def wadd(ch):
        sp = active_split()
        if sp and sp.get("wmerge") is not None:
            sp["wmerge"].append(ch)

    def append_ch(fr, ch, word=True):
        fr["buf"].append(ch)
        fr["cbuf"].append(ch)
        if word and fr.get("wmerge") is not None and not in_quote():
            if ch in " \t\n\r":
                flush_word(fr)
            elif ch not in "'\"":
                fr["wmerge"].append(ch)

    def spl_emit(ch, word=True):
        sp = active_split()
        if sp:
            append_ch(sp, ch, word=word)

    def heredoc_op_at(i):
        if text.startswith("<<<", i):
            refuse("the guard cannot read the command: a here-string (<<<)")
            return False
        if text.startswith("<<-", i):
            refuse("the guard cannot read the command: a tab-stripping here-document (<<-)")
            return False
        if not text.startswith("<<", i):
            return False
        return i == 0 or text[i - 1] != "<"

    def flush_spl(fr, chain_too=True, collect_chain=True):
        nonlocal gh_amp_reason
        flush_word(fr)
        seg = "".join(fr["buf"]).strip()
        fr["buf"] = []
        wd = list(fr["words"])
        fr["words"] = []
        if seg and fr.get("top"):
            full_cmds.append(seg)
            cmd_words_list.append(wd)
        elif seg and not fr.get("top"):
            subst_inners.append(seg)
            sub_chains_list.append(list(fr["chain_segs"]))
        if chain_too:
            cseg = "".join(fr["cbuf"]).strip()
            fr["cbuf"] = []
            if cseg:
                fr["chain_segs"].append(cseg)
            if collect_chain and cseg:
                fr["chain_wds"].append(wd if wd else list(fr.get("_last_wds", [])))
        if wd:
            fr["_last_wds"] = wd

    def try_redirect(i, fr):
        if in_quote() or fr.get("wmerge"):
            return None
        m = None
        if text.startswith(">&-", i):
            m = 4
        elif i + 2 < n and text[i:i + 3] in (">>>", "<<<"):
            return None
        elif text.startswith(">>", i) and not text.startswith(">>>", i):
            m = 2
        elif text.startswith("<<", i):
            return None
        elif text.startswith("<&", i) or text.startswith(">&", i):
            m = 2
        elif text.startswith("<>", i):
            m = 2
        elif text.startswith(">|", i):
            m = 2
        elif text.startswith("&>>", i):
            m = 3
        elif text.startswith("&>", i):
            m = 2
        elif text[i] in "<>" and not (text[i] == "<" and i + 1 < n and text[i + 1] == "(") and not (text[i] == ">" and i + 1 < n and text[i + 1] == "("):
            m = 1
        else:
            k = i
            while k < n and text[k].isdigit():
                k += 1
            if k > i and k < n and text[k] in "<>":
                if text.startswith(">&-", k):
                    m = (k - i) + 4
                elif text.startswith(">>", k):
                    m = (k - i) + 2
                elif text.startswith("<<", k):
                    return None
                elif text[k:k + 2] in ("<&", ">&", "<>"):
                    m = (k - i) + 2
                elif text[k] in "<>":
                    m = (k - i) + 1
        if m:
            for ch in text[i:i + m]:
                append_ch(fr, ch, word=False)
            j = i + m
            while j < n and text[j] in " \t":
                append_ch(fr, text[j], word=False); j += 1
            if j < n and text[j] in "'\"":
                return j
            while j < n and text[j] not in " \t\n\r;|&":
                if text.startswith("$(", j) or text[j] in "'\"":
                    return j
                append_ch(fr, text[j], word=False)
                j += 1
            return j
        return None

    def bare_amp(i, fr):
        if i >= n or text[i] != "&":
            return False
        if i > 0 and text[i - 1] in "<>":
            return False
        if i > 0 and text[i - 1] not in " \t\n\r;|&(":
            return False
        if i + 1 < n and text[i + 1] in ">&":
            return False
        if i + 1 < n and text[i + 1] == "&":
            return False
        if i + 1 < n and text[i + 1] not in " \t\n\r;|&)":
            return False
        return True

    def push_split(top, nest):
        nonlocal depth_exceeded
        if nest > READ_DEPTH_BOUND:
            depth_exceeded = True
            refuse("the guard cannot read the command: nesting past the bound")
            return
        stack.append({"k": "spl", "buf": [], "cbuf": [], "chain_segs": [], "top": top, "nest": nest, "pd": 0, "cmt": False, "inh": nest,
                        "wmerge": [], "words": [], "chain_wds": [], "gh": False, "hd_line": False})

    def try_sep(i, fr, subst=False):
        nonlocal gh_amp_reason
        chain_hit = full_hit = None
        if i + 1 < n and text[i:i + 2] in ("&&", "||"):
            chain_hit = full_hit = i + 2
        elif text[i] in (";", "\n"):
            if not (subst and text[i] == "\n" and fr.get("hd_line")):
                chain_hit = full_hit = i + 1
        elif bare_amp(i, fr):
            if fr.get("gh") and fr.get("wmerge") and not gh_amp_reason:
                gh_amp_reason = "gh api with an unquoted & in an argument (quote the endpoint or URL so the shell does not split on &)"
            if fr.get("wmerge"):
                flush_word(fr)
            chain_hit = full_hit = i + 1
        elif text[i] == "|":
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
            return None, None, None, None
        if text[j] in ("'", '"'):
            quoted, q = text[j], j + 1
            while q < n and text[q] != quoted:
                q += 1
            if q >= n:
                refuse("the guard cannot read the command: an unclosed quote or substitution")
                return None, None, None, None
            dname = text[j + 1:q]
            if q + 1 < n and text[q + 1] not in " \t\n;|&":
                refuse("the guard cannot read the command: a here-document delimiter is not one plain word or one quoted plain word")
                return None, None, None, None
            return dname, quoted, q + 1, j
        start = j
        while j < n and text[j] not in " \t\n;|&":
            j += 1
        dname = text[start:j]
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", dname):
            refuse("the guard cannot read the command: a here-document delimiter is not one plain word or one quoted plain word")
            return None, None, None, None
        return dname, None, j, start

    def in_dq():
        return any(fr["k"] == "dq" for fr in stack)

    def unescape_bt(s):
        out, j, bn = [], 0, len(s)
        while j < bn:
            if s[j] == "\\" and j + 1 < bn:
                nxt = s[j + 1]
                if nxt in "$\\\"":
                    out.append({"$": "$", "\\": "\\", '"': '"'}[nxt])
                else:
                    out.append(s[j:j + 2])
                j += 2
            else:
                out.append(s[j]); j += 1
        return "".join(out)

    def scan_btick_body(body, nest):
        push_split(False, nest)
        bi, bn, bt_bs = 0, len(body), 0
        while bi < bn:
            if unreadable or depth_exceeded:
                break
            bc = body[bi]
            sp = active_split()
            if not sp:
                break
            if sp.get("cmt"):
                if bc == "\n":
                    sp["cmt"] = False
                bi += 1
                continue
            if bc == "#" and (not sp["buf"] or sp["buf"][-1].isspace()):
                sp["cmt"] = True
                bi += 1
                continue
            if bc == "\\" and backslash_escapes:
                append_ch(sp, bc, word=False)
                bt_bs += 1
                bi += 1
                continue
            escd = backslash_escapes and bt_bs % 2 == 1
            bt_bs = 0
            if not escd and body.startswith("$(", bi):
                saw_subst = True
                append_ch(sp, "$(", word=False)
                push_split(False, nest + 1)
                stack.append({"k": "sub", "start": bi + 2, "pd": 1})
                bi += 2
                continue
            if not escd and bc == "`":
                refuse("the guard cannot read the command: a nested backtick")
                break
            if not escd and bc == "'":
                append_ch(sp, "'", word=False)
                stack.append({"k": "sq"})
                bi += 1
                continue
            if not escd and bc == '"':
                append_ch(sp, '"', word=False)
                stack.append({"k": "dq", "nest": nest})
                bi += 1
                continue
            tsep = try_sep(bi, sp, subst=True)
            if tsep is not None:
                bi = tsep
                continue
            append_ch(sp, bc)
            bi += 1
        flush_spl(active_split())
        while len(stack) > 1 and stack[-1]["k"] == "spl" and stack[-1]["nest"] >= nest:
            stack.pop()

    def scan_unquoted_hd_body(start, end, delim):
        nonlocal saw_subst
        j = start
        in_sq = in_dq = False
        bs = 0
        while j < end:
            line_nl = text.find("\n", j)
            if line_nl < 0 or line_nl > end:
                line_nl = end
            if text[j:line_nl].lstrip("\t").rstrip(" \t") == delim:
                return
            k = j
            while k < line_nl:
                c = text[k]
                if in_sq:
                    if c == "'":
                        in_sq = False
                    k += 1
                    continue
                if in_dq:
                    esc = backslash_escapes and bs % 2 == 1
                    if c == "\\" and backslash_escapes and not esc:
                        bs += 1; k += 1; continue
                    if c == '"' and not esc:
                        in_dq = False
                    bs = 0; k += 1; continue
                if c == "'":
                    in_sq = True; k += 1; continue
                if c == '"':
                    in_dq = True; k += 1; continue
                if text.startswith("$(", k):
                    saw_subst = True
                    dep = 1
                    k2 = k + 2
                    while k2 < end and dep:
                        if text.startswith("$(", k2):
                            dep += 1; k2 += 2; continue
                        if text[k2] == ")":
                            dep -= 1
                        k2 += 1
                    if dep:
                        refuse("the guard cannot read the command: an unclosed quote or substitution")
                        return
                    inner = text[k + 2:k2 - 1].strip()
                    if inner:
                        subst_inners.append(inner)
                    k = k2
                    continue
                if c == "`":
                    refuse("the guard cannot read the command: a backtick inside an unquoted here-document body")
                    return
                k += 1
            j = line_nl + 1 if line_nl < end else end

    def finish_heredoc(i, fr):
        nonlocal gh_amp_reason
        line_end = text.find("\n", i)
        if line_end < 0:
            line_end = n
        if fr.get("hdcnt", 0):
            refuse("the guard cannot read the command: two here-documents on one line")
            return line_end + 1 if line_end < n else n
        fr["hdcnt"] = fr.get("hdcnt", 0) + 1
        fr["hd_line"] = True
        delim, quoted, dj, _ = parse_heredoc_delim(i + 2)
        if delim is None and unreadable:
            return line_end + 1 if line_end < n else n
        if delim is None:
            refuse("the guard cannot read the command: a here-document without a delimiter")
            return i + 2
        in_sq = in_dq = False
        j, bs = i, 0
        while j < line_end:
            if text.startswith("<<", j) and j > i:
                refuse("the guard cannot read the command: two here-documents on one line")
                break
            c = text[j]
            if in_sq:
                append_ch(fr, c, word=False)
                if c == "'":
                    in_sq = False
                j += 1
                continue
            if in_dq:
                esc = backslash_escapes and bs % 2 == 1
                if c == "\\" and backslash_escapes and not esc:
                    append_ch(fr, c, word=False); bs += 1; j += 1; continue
                append_ch(fr, c, word=False)
                if c == '"' and not esc:
                    in_dq = False
                bs = 0
                j += 1
                continue
            if c == "'":
                in_sq = True; append_ch(fr, c, word=False); j += 1; continue
            if c == '"':
                in_dq = True; append_ch(fr, c, word=False); j += 1; continue
            if j + 1 < line_end and text[j:j + 2] in ("&&", "||"):
                flush_spl(fr); j += 2; continue
            if c in ";|&" and (c != "&" or not (j > 0 and text[j - 1] in "<>")):
                if c == "&" and j + 1 < line_end and text[j + 1] in ">&":
                    append_ch(fr, c, word=False); j += 1; continue
                if c == "&" and j + 1 < line_end and text[j + 1] == "&":
                    flush_spl(fr); j += 2; continue
                if c == "&":
                    if fr.get("gh") and fr.get("wmerge") and not gh_amp_reason:
                        gh_amp_reason = "gh api with an unquoted & in an argument (quote the endpoint or URL so the shell does not split on &)"
                    if fr.get("wmerge"):
                        flush_word(fr)
                    flush_spl(fr); j += 1; continue
                if c in ";|":
                    flush_spl(fr); j += 1; continue
            append_ch(fr, c); j += 1
        if line_end < n:
            append_ch(fr, "\n", word=False)
        body_start = line_end + 1 if line_end < n else n
        body_end = skip_heredoc_body(body_start, delim, False)
        if not quoted:
            scan_unquoted_hd_body(body_start, body_end, delim)
        line_start_ix = text[:i].rfind("\n") + 1
        heredocs.append({"start": i, "end": body_end, "delim": delim, "quoted": quoted, "strip": False,
                         "line": text[line_start_ix:line_end]})
        if len(heredocs) > READ_DEPTH_BOUND:
            refuse("the guard cannot read the command: nesting past the bound")
        fr["hd_line"] = False
        fr["hdcnt"] = 0
        return body_end

    if not backslash_escapes:
        j = 0
        while j < n:
            if text.startswith("@'", j) or text.startswith('@"', j):
                refuse("the guard cannot read the command: a PowerShell here-string")
                break
            if text.startswith("<#", j):
                refuse("the guard cannot read the command: a PowerShell block comment")
                break
            if text[j] == "\r" and (j + 1 >= n or text[j + 1] != "\n"):
                refuse("the guard cannot read the command: a lone carriage return")
                break
            j += 1

    while i < n:
        if unreadable or depth_exceeded:
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
            c = text[i]
            if c == "'":
                spl_emit(c, word=False)
                stack.pop()
            else:
                spl_emit(c, word=False)
                wadd(c)
            i += 1
            bs_run = 0
            continue
        if topk == "dq":
            fr = stack[-1]
            c = text[i]
            if not backslash_escapes and c == "\\" and i + 1 < n and text[i + 1] == '"':
                refuse("the guard cannot read the command: a backslash before a quote under PowerShell")
                break
            esc = backslash_escapes and bs_run % 2 == 1
            if c == "\\" and backslash_escapes and not esc:
                spl_emit(c, word=False); bs_run += 1; i += 1; continue
            if c == '"' and not esc:
                spl_emit('"', word=False); stack.pop(); bs_run = 0; i += 1; continue
            if not esc and text.startswith("$(", i):
                spl_emit("$(", word=False); i += 2; bs_run = 0
                if subst_counts():
                    saw_subst = True
                push_split(False, fr.get("nest", 0) + 1)
                stack.append({"k": "sub", "start": i, "pd": 1})
                continue
            if not esc and text.startswith("${", i):
                spl_emit("${", word=False); wadd("$"); wadd("{"); i += 2; bs_run = 0
                stack.append({"k": "br", "body": [], "nest": fr.get("nest", 0)})
                continue
            if not esc and c == "`":
                spl_emit(c, word=False); i += 1; bs_run = 0
                if subst_counts():
                    saw_subst = True
                stack.append({"k": "btf", "buf": [], "nest": fr.get("nest", 0)})
                continue
            if esc:
                if c not in "$\"\\`":
                    wadd("\\")
                wadd(c)
            else:
                wadd(c)
            spl_emit(c, word=False); bs_run = 0; i += 1
            continue
        if topk == "ansi":
            fr = stack[-1]
            c = text[i]
            if c == "\\" and i + 1 < n:
                fr.setdefault("raw", []).append(text[i:i + 2])
                spl_emit(text[i:i + 2], word=False)
                i += 2; continue
            if c == "'":
                raw = "".join(fr.get("raw", []))
                try:
                    decoded = _ansi_c_decode(raw)
                except Exception:
                    decoded = raw
                if "\x00" in decoded:
                    decoded = decoded.split("\x00", 1)[0]
                    if not decoded and "\x00" in _ansi_c_decode(raw):
                        refuse("the guard cannot read the command: an ANSI-C string with a NUL byte")
                spl_emit("'", word=False)
                sp = active_split()
                if sp:
                    sp.setdefault("wmerge", []).extend(list(decoded))
                    mark_gh(sp)
                stack.pop()
                if i + 1 < n and text[i + 1] not in " \t\n\r;|&":
                    refuse("the guard cannot read the command: an ANSI-C string that is not a whole word")
                i += 1; bs_run = 0; continue
            fr.setdefault("raw", []).append(c)
            spl_emit(c, word=False)
            i += 1
            bs_run = 0
            continue
        if topk == "loc":
            fr = stack[-1]
            c = text[i]
            esc = backslash_escapes and bs_run % 2 == 1
            if c == "\\" and backslash_escapes and not esc:
                fr.setdefault("raw", []).append(c); spl_emit(c, word=False); bs_run += 1; i += 1; continue
            if c == '"' and not esc:
                spl_emit('"', word=False)
                sp = active_split()
                if sp:
                    sp.setdefault("wmerge", []).extend(list("".join(fr.get("raw", []))))
                    mark_gh(sp)
                stack.pop()
                if i + 1 < n and text[i + 1] not in " \t\n\r;|&":
                    refuse("the guard cannot read the command: a locale string that is not a whole word")
                bs_run = 0; i += 1; continue
            fr.setdefault("raw", []).append(c); spl_emit(c, word=False); i += 1; bs_run = 0
            continue
        if topk == "br":
            fr = stack[-1]
            c = text[i]
            if c == "}":
                body = "".join(fr.get("body", []))
                stack.pop()
                sp = active_split()
                if sp:
                    spl_emit("}", word=False)
                bad = any(x in body for x in "\"'`$({")
                if bad or (not re.match(r"^!?[A-Za-z_][A-Za-z0-9_]*$", body) and not re.match(r"^#[A-Za-z_][A-Za-z0-9_]*$", body) and not re.match(r"^[A-Za-z_][A-Za-z0-9_]*:-[^\"'`${}()]*$", body)):
                    refuse("the guard cannot read the command: a parameter expansion holding a quote, substitution or brace")
                else:
                    for ch in body + "}":
                        wadd(ch)
                i += 1; bs_run = 0; continue
            if c in "\"'`$({" or text.startswith("$(", i):
                refuse("the guard cannot read the command: a parameter expansion holding a quote, substitution or brace")
                break
            fr.setdefault("body", []).append(c)
            i += 1; bs_run = 0
            continue
        if topk == "btf":
            fr = stack[-1]
            c = text[i]
            if c == "\\" and i + 1 < n and backslash_escapes:
                fr["buf"].append(text[i:i + 2]); i += 2; continue
            if c == "`" and (not backslash_escapes or bs_run % 2 == 0):
                raw = "".join(fr["buf"])
                body = unescape_bt(raw)
                nest = fr["nest"]
                stack.pop()
                spl = active_split()
                if spl:
                    spl_emit("`", word=False)
                saw_subst = True
                subst_inners.append(body)
                scan_btick_body(body, nest + 1)
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
                append_ch(sp, c, word=False); bs_run += 1; i += 1; continue
            escd = backslash_escapes and bs_run % 2 == 0 and False
            escd = backslash_escapes and (bs_run % 2 == 1)
            bs_run = 0
            if escd:
                wadd(c); append_ch(sp, c, word=False); i += 1; continue
            if c == "#" and (not sp["buf"] or sp["buf"][-1].isspace() or sp["buf"][-1] in ";|&"):
                sp["cmt"] = True; i += 1; continue
            if c == "'":
                append_ch(sp, c, word=False); stack.append({"k": "sq"}); i += 1; continue
            if c == '"':
                append_ch(sp, c, word=False); stack.append({"k": "dq", "nest": sp["nest"]}); i += 1; continue
            if text.startswith("$'", i):
                if sp.get("wmerge"):
                    refuse("the guard cannot read the command: an ANSI-C string that is not a whole word")
                append_ch(sp, "$'", word=False); stack.append({"k": "ansi"}); i += 2; continue
            if text.startswith('$"', i):
                if sp.get("wmerge"):
                    refuse("the guard cannot read the command: a locale string that is not a whole word")
                append_ch(sp, '$"', word=False); stack.append({"k": "loc"}); i += 2; continue
            if text.startswith("${", i):
                append_ch(sp, "${"); wadd("$"); wadd("{"); stack.append({"k": "br", "body": [], "nest": sp["nest"]}); i += 2; continue
            if text.startswith("$(", i):
                saw_subst = True
                append_ch(sp, "$(")
                push_split(False, sp["nest"] + 1)
                stack.append({"k": "sub", "start": i + 2, "pd": 1})
                i += 2; continue
            if not in_dq() and text.startswith("<(", i):
                saw_subst = True
                append_ch(sp, text[i:i + 2], word=False)
                push_split(False, sp["nest"] + 1)
                stack.append({"k": "sub", "start": i + 2, "pd": 1, "proc": 1})
                i += 2; continue
            if not in_dq() and text.startswith(">(", i):
                saw_subst = True
                append_ch(sp, text[i:i + 2], word=False)
                push_split(False, sp["nest"] + 1)
                stack.append({"k": "sub", "start": i + 2, "pd": 1, "proc": 1})
                i += 2; continue
            if c == "`":
                saw_subst = True
                append_ch(sp, c, word=False)
                stack.append({"k": "btf", "buf": [], "nest": sp["nest"]})
                i += 1; continue
            if not in_dq() and heredoc_op_at(i):
                i = finish_heredoc(i, sp)
                continue
            if c == "(":
                fr["pd"] += 1; append_ch(sp, c); i += 1; continue
            if c == ")":
                append_ch(sp, c)
                fr["pd"] -= 1
                if fr["pd"] == 0:
                    body = text[fr["start"]:i].strip()
                    if body:
                        subst_inners.append(body)
                    si = len(stack) - 1
                    while si > 0 and stack[si]["k"] != "sub":
                        if stack[si]["k"] == "spl" and not stack[si].get("top"):
                            flush_spl(stack[si], chain_too=True)
                            if stack[si]["chain_segs"]:
                                sub_chains_list.append(list(stack[si]["chain_segs"]))
                        si -= 1
                    stack.pop()
                    while stack and stack[-1]["k"] == "spl" and not stack[-1].get("top"):
                        stack.pop()
                    if stack and stack[-1]["k"] == "dq":
                        spl_emit(")", word=False)
                    i += 1; continue
                i += 1; continue
            ns = try_sep(i, sp, subst=True)
            if ns is not None:
                i = ns; continue
            rr = try_redirect(i, sp) if not in_quote() else None
            if rr is not None:
                i = rr; continue
            append_ch(sp, c); i += 1; continue
        if not fr:
            i += 1; continue
        c = text[i]
        if not backslash_escapes and c == "`" and not any(s["k"] == "sq" for s in stack):
            if i + 1 < n and text[i + 1] in "\r\n":
                while i + 1 < n and text[i + 1] in "\r\n":
                    i += 1
                i += 1
                bs_run = 0
                if active_split():
                    append_ch(active_split(), " ")
                continue
            if i + 1 >= n or text[i + 1] not in "\r\n":
                refuse("the guard cannot read the command: a backtick that is not a line continuation under PowerShell")
                break
        if text.startswith("$((", i) and bs_run % 2 == 0 and not in_dq():
            refuse("the guard cannot read the command: arithmetic expansion")
            break
        if text.startswith("((", i) and bs_run % 2 == 0 and not in_dq():
            refuse("the guard cannot read the command: an arithmetic command")
            break
        if c == "\\" and backslash_escapes:
            append_ch(fr, c, word=False); bs_run += 1; i += 1; continue
        escd = backslash_escapes and (bs_run % 2 == 1)
        bs_run = 0
        if escd:
            wadd(c); append_ch(fr, c, word=False); i += 1; continue
        if c == "#" and (not fr["buf"] or fr["buf"][-1].isspace() or fr["buf"][-1] in ";|&("):
            fr["cmt"] = True; i += 1; continue
        if not backslash_escapes and c == "\\" and i + 1 < n and text[i + 1] == '"':
            refuse("the guard cannot read the command: a backslash before a quote under PowerShell")
            break
        if not in_quote() and fr.get("wmerge") and "".join(fr["wmerge"]).strip() and text[i] in "<>":
            flush_word(fr)
        rr = try_redirect(i, fr) if not in_quote() else None
        if rr is not None:
            i = rr; continue
        if c == "{" and not in_quote():
            m = re.match(r"^\{[A-Za-z_][A-Za-z0-9_]*\}>", text[i:])
            if m:
                refuse("the guard cannot read the command: a named file descriptor redirection")
                break
            end = text.find("}", i + 1)
            if end > i and ("," in text[i + 1:end] or ".." in text[i + 1:end]):
                refuse("the guard cannot read the command: an unquoted brace expansion")
                break
        if c == "'":
            append_ch(fr, c, word=False); stack.append({"k": "sq"}); i += 1; continue
        if c == '"':
            append_ch(fr, c, word=False); stack.append({"k": "dq", "nest": fr["nest"]}); i += 1; continue
        if text.startswith("$'", i):
            if fr.get("wmerge") and "".join(fr["wmerge"]).strip():
                refuse("the guard cannot read the command: an ANSI-C string that is not a whole word")
            append_ch(fr, "$'", word=False); stack.append({"k": "ansi"}); i += 2; continue
        if text.startswith('$"', i):
            if fr.get("wmerge") and "".join(fr["wmerge"]).strip():
                refuse("the guard cannot read the command: a locale string that is not a whole word")
            append_ch(fr, '$"', word=False); stack.append({"k": "loc"}); i += 2; continue
        if text.startswith("${", i):
            append_ch(fr, "${"); wadd("$"); wadd("{"); stack.append({"k": "br", "body": [], "nest": fr["nest"]}); i += 2; continue
        if text.startswith("$(", i):
            saw_subst = True
            append_ch(fr, "$(")
            push_split(False, fr["nest"] + 1)
            stack.append({"k": "sub", "start": i + 2, "pd": 1})
            i += 2; continue
        if not in_dq() and c == "<" and i + 1 < n and text[i + 1] == "(":
            saw_subst = True
            append_ch(fr, "<(", word=False)
            push_split(False, fr["nest"] + 1)
            stack.append({"k": "sub", "start": i + 2, "pd": 1, "proc": 1})
            i += 2; continue
        if not in_dq() and c == ">" and i + 1 < n and text[i + 1] == "(":
            saw_subst = True
            append_ch(fr, ">(", word=False)
            push_split(False, fr["nest"] + 1)
            stack.append({"k": "sub", "start": i + 2, "pd": 1, "proc": 1})
            i += 2; continue
        if c == "`":
            saw_subst = True
            append_ch(fr, c, word=False)
            stack.append({"k": "btf", "buf": [], "nest": fr["nest"]})
            i += 1; continue
        if not in_dq() and heredoc_op_at(i):
            i = finish_heredoc(i, fr)
            if fr.get("top"):
                flush_spl(fr, chain_too=False)
            continue
        ns = try_sep(i, fr)
        if ns is not None:
            i = ns; continue
        append_ch(fr, c); i += 1
    flush_spl(stack[0]) if stack else None
    chain_cmds = stack[0]["chain_segs"] if stack else []
    if depth_exceeded and unreadable is None:
        unreadable = "the guard cannot read the command: nesting past the bound"
    if unreadable is None and stack:
        for fr in stack:
            if fr["k"] in ("sq", "dq", "sub", "btf", "br", "ansi", "loc"):
                unreadable = "the guard cannot read the command: an unclosed quote or substitution"
                break
    return {"unreadable": unreadable, "full": full_cmds, "cmd_words": cmd_words_list, "chain": chain_cmds,
            "subs": subst_inners, "sub_chains": sub_chains_list, "heredocs": heredocs,
            "deep": depth_exceeded, "hassub": saw_subst, "gh_amp": gh_amp_reason, "text": text}


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
    if p.get("unreadable") or p["deep"]:
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


def words(command):
    p = _parsed_snapshot(command, backslash_escapes=_READ_ESCAPES)
    if p.get("unreadable") or p.get("deep"):
        return []
    cmd = command.strip()
    for i, f in enumerate(p.get("full", [])):
        if f.strip() == cmd and i < len(p.get("cmd_words", [])):
            return list(p["cmd_words"][i])
    cw = p.get("cmd_words") or []
    if len(p.get("full", [])) == 1 and len(cw) == 1:
        return list(cw[0])
    if cw and len(p.get("full", [])) == len(cw):
        for i, f in enumerate(p["full"]):
            if f.strip() == cmd or cmd in f or f.strip() in cmd:
                return list(cw[i])
    return []


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
    parsed = _parsed_snapshot(command)
    if parsed.get("unreadable"):
        return None
    top = [_strip_outer_parens(x) for x in parsed["chain"] if x.strip()]
    heads = [strip_prefix(words(p)) for p in top]
    heads = [h for h in heads if h]
    for h in list(heads):
        if base(h[0]) == "eval" and len(h) > 1:
            heads += [strip_prefix(words(p)) for p in chain_parts(" ".join(h[1:]))]
    if heads and base(heads[0][0]) == "cd":
        return "a command wrapped in cd (rule 8: never wrap a command in cd; run it with the path it needs, or git -C)"
    lists = []
    if len(top) >= 2:
        lists.append(top)
    for sc in parsed.get("sub_chains", []):
        parts = [_strip_outer_parens(x) for x in sc if x.strip()]
        if len(parts) >= 2:
            lists.append(parts)
    for sub in parsed.get("subs", []):
        if re.search(r"&&|\|\||;", sub):
            sp = _parsed_snapshot(sub, backslash_escapes=_READ_ESCAPES)
            parts = [_strip_outer_parens(x) for x in sp.get("chain", []) if x.strip()]
            if len(parts) >= 2:
                lists.append(parts)
    for parts in lists:
        n = len(parts)
        for p in parts:
            w = strip_prefix(words(p))
            if w and state_changing(w):
                return "a chain of %d commands carrying %s (rule 8: one command per call, never chained with &&, ; or ||; the allowlist and the guard read one command, and a chain once built an increment on a merged branch)" % (n, " ".join(w[:2]))
            pp = _parsed_snapshot(p)
            for sub in pp.get("subs", []):
                sw = strip_prefix(words(sub))
                if sw and state_changing(sw):
                    return "a chain of %d commands carrying %s (rule 8: one command per call, never chained with &&, ; or ||; the allowlist and the guard read one command, and a chain once built an increment on a merged branch)" % (n, " ".join(sw[:2]))
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

        for sub in p.get("subs", []):
            if sub not in command and command not in sub:
                continue
            subj = first_heredoc_subject(_parsed_snapshot(sub), sub)
            if subj:
                return subj
    return msg.strip()


def in_worktree(w, cwd):
    """A commit made inside a builder's worktree (`-C ../Worktrees/x`, or a cwd under Worktrees/)."""
    paths = [cwd or ""] + [w[i + 1] for i, a in enumerate(w) if a == "-C" and i + 1 < len(w)]
    return any(re.search(r"[\\/]Worktrees[\\/]", p) for p in paths)


def check(command, cwd=None, tool="Bash", _depth=0):
    """Return the reason to refuse, or None."""
    bs = tool != "PowerShell"
    return _check_one(command, cwd, tool, _depth, backslash_escapes=bs)


def _check_one(command, cwd, tool, depth, backslash_escapes=True):
    if depth > READ_DEPTH_BOUND:
        return "the guard cannot read the command: nesting past the bound"
    global _READ_ESCAPES
    _parsed_snapshot._cache = {}
    _READ_ESCAPES = backslash_escapes
    parsed = _parsed_snapshot(command, backslash_escapes=backslash_escapes)
    if parsed.get("unreadable"):
        return parsed["unreadable"]
    if parsed["deep"]:
        return "the guard cannot read the command: nesting past the bound"
    r = parsed.get("gh_amp")
    if r:
        return r
    r = chain_reason(command, cwd)
    if r:
        return r
    for simple in split_commands(command):
        if leading_husky_zero(simple) and re.search(r"\bgit\b.*\b(commit|push|merge)\b", simple, re.I | re.S):
            return "HUSKY=0 switches the hook runner off (a commit that skips its checks; rule 4)"
        w = strip_prefix(words(simple))
        if not w:
            continue
        head = base(w[0])
        if head == "eval" and len(w) > 1:
            r = _check_one(" ".join(w[1:]), cwd, tool, depth + 1, backslash_escapes=backslash_escapes)
            if r:
                return r
        if head in WRAPPER_SHELLS:
            inner = shell_inner(w)
            if inner is ENCODED:
                return "an encoded PowerShell command, which the guard cannot read"
            if inner:
                ps_tool = "PowerShell" if base(w[0]).replace(".exe", "") in ("powershell", "pwsh") else tool
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
                gp = _parsed_snapshot(simple, backslash_escapes=backslash_escapes)
                if gp.get("unreadable"):
                    return gp["unreadable"]
                if parsed.get("hassub") or gp.get("hassub"):
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
