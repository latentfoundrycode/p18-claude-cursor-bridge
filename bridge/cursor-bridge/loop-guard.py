#!/usr/bin/env python3
"""loop-guard: a Claude Code Stop hook that keeps a bridge supervisor from ending its turn
while the build loop has work and nothing is going to wake it.

Registered in the bridge's settings.json (hooks -> Stop). Reads the hook's JSON on stdin.
It BLOCKS the stop - exit code 2 with the reason on stderr, which Claude Code feeds back to
the model (documented; code.claude.com hooks reference) - only when ALL hold:

  1. the session runs in a bridge Workspace: <cwd>/docs/PROJECT_STATUS.md exists;
  2. its `Phase:` is building or changing;
  3. its `Awaiting user on:` is `nothing` (the supervisor is not waiting for the owner);
  (and, in every phase: a turn whose last message holds a shell block and names no terminal
  is sent back once, because a run sheet without its terminal cannot be followed, rule 27);
  4. nothing is pending that will wake the session: no background agent or scheduled
     wake-up, and no background command *of a kind that finishes* - a builder run
     (cursor-agent), a CI watch (gh pr checks --watch), or any command the supervisor marked
     with `# wake` - started in the last GRACE_HOURS without a completion notification in
     the transcript. A background command of any other kind (a dev server, a worker, a
     probe) is NOT a wake source: a server never finishes, so nothing would ever wake the
     session (KP-031: a dev stack left running masqueraded as a wake source for 7 hours);
  5. this is not already a continuation forced by this hook (`stop_hook_active`), so it
     nudges at most once per stop sequence and can never trap the session.

Everything else - any other folder, any other phase, an owner question outstanding, a
background task pending, a missing or unreadable file - ALLOWS the stop. The guard fails
open: a parse problem never blocks. ASCII output only. Never writes anything.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

GRACE_HOURS = 6            # a background task older than this no longer counts as a wake source
# A background command counts as a wake source only if it is of a kind that finishes: the
# builder, the CI watch, or a command the supervisor marked with "# wake". Everything else
# (servers, workers, probes) runs until killed and can never wake the session.
WAKE_PATTERNS = (
    re.compile(r"\bcursor-agent\b"),
    re.compile(r"\bgh\s+pr\s+checks\b.*--watch"),
    re.compile(r"#\s*wake\b", re.I),
)
TAIL_BYTES = 12 * 1024 * 1024
RECHECK_SECONDS = 2.0      # grace for the asynchronously written transcript
ACTIVE_PHASES = ("building", "changing")
NOTHING = ("nothing", "none", "-", "")

REASON = (
    "Loop guard (Claude-Cursor Bridge): docs/PROJECT_STATUS.md says Phase: {phase} and "
    "Awaiting user on: nothing, and no background command or agent is running that would wake "
    "you (a running server, worker or probe is not one: it never finishes). Ending the turn now "
    "stalls the build until the owner notices. Do the next step of the loop instead. If you are "
    "waiting for CI, start ONE background watch of the PR's required "
    "checks (gh pr checks <n> --watch --required --fail-fast, run in the background) - its completion wakes "
    "you; the desktop app's CI monitor never reports a green gate. If you are genuinely waiting "
    "for the owner (an escalation, a gate, a pause they asked for, a stage pause), write that on "
    "the `Awaiting user on:` line first, then stop. A background command of your own that will "
    "finish and should wake you is recognised only if it is the builder, the CI watch, or "
    "carries the comment `# wake`."
)


SHELL_FENCE = re.compile(r"^```[ \t]*(bash|sh|shell|powershell|pwsh|cmd|bat|console)\b", re.M | re.I)
TERMINAL_NAMED = re.compile(r"Terminal:|Git Bash|PowerShell|Command Prompt|this chat", re.I)
RUN_SHEET_REASON = (
    "Run-sheet rule (Claude-Cursor Bridge, rule 27): your last message holds a shell block but "
    "names no terminal. A run sheet opens with `Terminal: <PowerShell | Git Bash | Command Prompt | "
    "this chat | the <name> page>` and how to open it, then the folder, the commands one per block, "
    "what to expect under each, and one report-back line. If the block was not for the owner to "
    "run, say so in the text (it was run by you, in <terminal>) or put it in a plain block."
)


def allow():
    sys.exit(0)


def last_assistant_text(transcript_path):
    """The text of the last assistant message in the transcript, or None."""
    try:
        size = os.path.getsize(transcript_path)
        with open(transcript_path, "rb") as f:
            if size > TAIL_BYTES:
                f.seek(size - TAIL_BYTES)
                f.readline()
            raw = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    last = None
    for line in raw.splitlines():
        try:
            o = json.loads(line)
        except ValueError:
            continue
        msg = o.get("message") or {}
        if msg.get("role") != "assistant" or not isinstance(msg.get("content"), list):
            continue
        texts = [x.get("text") or "" for x in msg["content"] if isinstance(x, dict) and x.get("type") == "text"]
        if texts:
            last = "\n".join(texts)
    return last


def run_sheet_without_terminal(text):
    """True when the message holds a shell block and names no terminal (release A1b)."""
    return bool(text) and bool(SHELL_FENCE.search(text)) and not TERMINAL_NAMED.search(text)


def status_candidates(cwd):
    """Where the project's status file may be, for a session started in Workspace, in the
    project root above it, or inside a worktree under <root>/Worktrees (KP-031 follow-up:
    the guard used to look only under cwd and so was blind in sessions started at the root)."""
    bases = []
    for start in (cwd, os.environ.get("CLAUDE_PROJECT_DIR") or ""):
        if not start:
            continue
        d = os.path.abspath(start)
        parts = d.replace("\\", "/").split("/")
        if "Worktrees" in parts:                       # a worktree root: use the project's own checkout
            root = "/".join(parts[:parts.index("Worktrees")])
            bases.append(os.path.join(root, "Workspace"))
        for _ in range(4):
            bases.append(d)
            bases.append(os.path.join(d, "Workspace"))
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    seen, out = set(), []
    for b in bases:
        if b not in seen:
            seen.add(b)
            out.append(os.path.join(b, "docs", "PROJECT_STATUS.md"))
    return out


def read_status(cwd):
    for p in status_candidates(cwd):
        if os.path.isfile(p):
            with open(p, encoding="utf-8-sig", errors="replace") as f:
                return f.read()
    return None


def field(text, name):
    """The value of a `Name: value` line, tolerating list bullets, bold markers and backticks
    around the name or the value (`**Phase:** building`, `- Phase: building`)."""
    pat = r"^\s*(?:[-*]\s+)?[*_`]*%s[*_`]*\s*:[*_`]*\s*(.*?)\s*$" % re.escape(name)
    m = re.search(pat, text, re.M | re.I)
    if not m:
        return None
    return m.group(1).strip().strip("*_`").strip()


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def wakes(tur, content, uses):
    """Does this background task's completion count as a wake source?

    Agents and non-Bash tasks finish by nature. A background Bash command counts only if
    its text matches WAKE_PATTERNS; a command the transcript cannot be mapped back to is
    counted (fail open)."""
    if not tur.get("backgroundTaskId"):
        return True                                # an async agent or a tracked task: finishes
    if not isinstance(content, list):
        return True
    for x in content:
        if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("tool_use_id") in uses:
            name, inp = uses[x["tool_use_id"]]
            if not isinstance(inp, dict) or "command" not in inp:
                return True                        # not a shell tool: finishes by nature
            cmd = str(inp.get("command") or "")    # Bash, PowerShell, any shell tool alike
            return any(pat.search(cmd) for pat in WAKE_PATTERNS)
    return True


def pending_wakeups(transcript_path, now):
    """Return a list of descriptions of background work that will still wake the session."""
    try:
        size = os.path.getsize(transcript_path)
        with open(transcript_path, "rb") as f:
            if size > TAIL_BYTES:
                f.seek(size - TAIL_BYTES)
                f.readline()                       # drop the partial first line
            raw = f.read().decode("utf-8", "replace")
    except OSError:
        return None                                # unknown -> caller fails open
    started, done, wakeups, uses = {}, set(), [], {}
    cutoff = now - GRACE_HOURS * 3600
    for line in raw.splitlines():
        try:
            o = json.loads(line)
        except ValueError:
            continue
        ts = parse_ts(o.get("timestamp") or "") or now
        msg = o.get("message") or {}
        content = msg.get("content")
        if isinstance(content, list):
            for x in content:
                if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("id"):
                    uses[x["id"]] = (x.get("name") or "", x.get("input") or {})
        tur = o.get("toolUseResult")
        if isinstance(tur, dict):
            tid = tur.get("backgroundTaskId") or (tur.get("agentId") if tur.get("isAsync") else None) \
                or tur.get("taskId")
            if tid and ts >= cutoff and wakes(tur, content, uses):
                started[str(tid)] = ts
        origin = o.get("origin")
        if isinstance(origin, dict) and origin.get("senderTaskId"):
            done.add(str(origin["senderTaskId"]))
        msg = o.get("message") or {}
        content = msg.get("content")
        texts = []
        # Completion notifications also arrive as queue records (`content` at the top level)
        # and as queued-command attachments (`attachment.prompt`), not only as message text.
        if isinstance(o.get("content"), str):
            texts.append(o["content"])
        att = o.get("attachment")
        if isinstance(att, dict) and isinstance(att.get("prompt"), str):
            texts.append(att["prompt"])
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for x in content:
                if not isinstance(x, dict):
                    continue
                if x.get("type") == "text":
                    texts.append(x.get("text", ""))
                if x.get("type") == "tool_use" and x.get("name") == "ScheduleWakeup":
                    inp = x.get("input") or {}
                    try:
                        due = ts + float(inp.get("delaySeconds") or 0)
                    except (TypeError, ValueError):
                        due = ts
                    if due >= now and not inp.get("stop"):
                        wakeups.append("scheduled wake-up due in %ds" % int(due - now))
        for t in texts:
            if "<task-notification" in t:
                for m in re.finditer(r"<task-id>\s*([^<\s]+)\s*</task-id>", t):
                    st = re.search(r"<status>\s*(\w+)", t)
                    if not st or st.group(1).lower() in ("completed", "failed", "killed", "stopped",
                                                        "error", "cancelled", "canceled", "timeout"):
                        done.add(m.group(1))
    pending = ["background task %s" % k for k in started if k not in done]
    return pending + wakeups


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        allow()
    if not isinstance(data, dict) or data.get("stop_hook_active"):
        allow()
    cwd = data.get("cwd") or os.getcwd()
    status = read_status(cwd)
    if status is None:
        allow()
    phase = (field(status, "Phase") or "").strip()
    tp = data.get("transcript_path")
    if tp and os.path.isfile(tp) and run_sheet_without_terminal(last_assistant_text(tp)):
        sys.stderr.write(RUN_SHEET_REASON + chr(10))
        sys.exit(2)
    if not phase.lower().startswith(ACTIVE_PHASES):
        allow()
    awaiting = (field(status, "Awaiting user on") or "").strip().strip("<>").strip()
    a = awaiting.lower()
    if a not in NOTHING and not a.startswith(("nothing", "none", "n/a")):
        allow()
    tp = data.get("transcript_path")
    if not tp or not os.path.isfile(tp):
        allow()
    pending = pending_wakeups(tp, time.time())
    if pending is None or pending:
        allow()
    # The transcript is written asynchronously and may lag (documented): a watch launched just
    # before the stop may not be on disk yet. Look once more before blocking.
    time.sleep(RECHECK_SECONDS)
    pending = pending_wakeups(tp, time.time())
    if pending is None or pending:
        allow()
    sys.stderr.write(REASON.format(phase=phase.split()[0]) + chr(10))
    sys.exit(2)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)                                # fail open, always
