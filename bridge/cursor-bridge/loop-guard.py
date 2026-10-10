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
  4. nothing is pending that will wake the session. Since release A2 the hook's own lists
     decide: a background command *of a kind that finishes* (a builder run, a CI watch, a
     command run through bridge-run.py, or one marked `# wake`) counts until its limit plus a
     grace; a background agent counts only under its ceiling (an hour, or `Agent ceiling:` in
     the run parameters) AND only while a scheduled wake-up is due no later than that
     ceiling, because a hung agent never completes and nothing else would wake the session
     (plan 10.1, case 5); a scheduled wake-up counts (one past due fires as soon as the
     session is idle). A background command of any other kind (a dev server, a worker, a
     probe) is NOT a wake source: a server never finishes (KP-031). When the hook hands no
     lists, the transcript is read as before, within GRACE_HOURS;
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
from datetime import datetime, timedelta, timezone

GRACE_HOURS = 6            # a background task older than this no longer counts as a wake source (transcript fallback)
AGENT_CEILING = 3600       # a background agent older than this no longer counts (release A2; `Agent ceiling:` in RUN_PARAMETERS overrides)
KIND_CEILING = {"cursor-agent": 7200, "review": 3600, "gh pr checks": 3600, "# wake": 1800}
GRACE_SECONDS = 600        # the launcher ends a run at its limit; the notification follows within this
# A background command counts as a wake source only if it is of a kind that finishes: the
# builder, the CI watch, or a command the supervisor marked with "# wake". Everything else
# (servers, workers, probes) runs until killed and can never wake the session.
WAKE_PATTERNS = (
    re.compile(r"\bcursor-agent\b"),
    re.compile(r"bridge-run\.py"),                       # anything the launcher runs is bounded by its limit
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


SHELL_FENCE = re.compile(r"^[ \t]*(?:```|~~~)[ \t]*(bash|sh|shell|zsh|powershell|pwsh|ps1|cmd|bat|batch|console)\b", re.M | re.I)
TERMINAL_LINE = re.compile(r"^[ \t]*[*_`#>]*[ \t]*(?:[-*+]|\d+[.)])?[ \t]*[*_`#>]*[ \t]*Terminal\b(\s*\([^)\n]{0,40}\))?[*_`]*[ \t]*:", re.M | re.I)
RUN_SHEET_REASON = (
    "Run-sheet rule (Claude-Cursor Bridge, rule 27): your last message holds a shell block and "
    "names no terminal (no line begins `Terminal:`). A run sheet follows the one template: a line "
    "`Purpose:`, a line `End state:`, a line `Terminal: <PowerShell | Git Bash | Command Prompt | "
    "this chat | the <name> page>` with how to open it, the folder as a step, the commands numbered "
    "one per block, what to expect under each, and one report-back line. A command you ran "
    "yourself is not a run sheet: quote it in a plain block (no language tag) or inline."
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
    """True when the message holds a shell block and no line begins `Terminal:` (release A1b)."""
    return bool(text) and bool(SHELL_FENCE.search(text)) and not TERMINAL_LINE.search(text)


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
    """ISO 8601 (with or without Z), or epoch seconds or milliseconds, as a unix time; None otherwise.
    (reAngle, 2026-10-10: every task's start read as 'now' because the hook's form was not the one expected.)"""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s) / 1000 if float(s) > 1e11 else float(s)
    t = str(s).strip()
    if re.fullmatch(r"\d{10,13}(\.\d+)?", t):
        v = float(t)
        return v / 1000 if v > 1e11 else v
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def cron_field(field, value):
    """Does a 5-field cron field (`*`, n, a-b, a,b, */n) match a value?"""
    for part in field.split(","):
        part = part.strip()
        step = 1
        if "/" in part:
            part, step = part.split("/", 1)
            step = int(step) if step.isdigit() else 1
        if part == "*":
            if (value % step) == 0:
                return True
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            if lo.isdigit() and hi.isdigit() and int(lo) <= value <= int(hi) and (value - int(lo)) % step == 0:
                return True
            continue
        if part.isdigit() and int(part) == value:
            return True
    return False


def cron_next(expr, now):
    """The next fire time (local wall clock, as a unix time) of a 5-field cron expression, within
    eight days; None when the expression does not parse. Claude Code's session crons are local time."""
    fields = (expr or "").split()
    if len(fields) != 5:
        return None
    t = datetime.fromtimestamp(now).replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(8 * 24 * 60):
        if cron_field(fields[0], t.minute) and cron_field(fields[1], t.hour) and cron_field(fields[2], t.day) \
                and cron_field(fields[3], t.month) and cron_field(fields[4], t.weekday() + 1 if t.weekday() < 6 else 0):
            return t.timestamp()
        t += timedelta(minutes=1)
    return None


def workspace_of(cwd):
    """The folder holding docs/PROJECT_STATUS.md, or None."""
    for status in status_candidates(cwd):
        if os.path.isfile(status):
            return os.path.dirname(os.path.dirname(status))
    return None


def record_input(data, cwd):
    """The hook's last input, for the record (run/supervisor/loop-guard-input.json beside the project's
    status file; never the transcript): what the guard decided from can then be read (release A3)."""
    ws = workspace_of(cwd)
    if not ws or not os.path.isdir(os.path.join(ws, "run")):
        return
    try:
        os.makedirs(os.path.join(ws, "run", "supervisor"), exist_ok=True)
        keep = {k: v for k, v in data.items() if k in ("hook_event_name", "background_tasks", "session_crons", "stop_hook_active", "cwd")}
        keep["recorded_at"] = datetime.now().isoformat(timespec="seconds")
        with open(os.path.join(ws, "run", "supervisor", "loop-guard-input.json"), "w", encoding="utf-8") as f:
            json.dump(keep, f, indent=1, default=str)
    except OSError:
        pass


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


def agent_ceiling(cwd):
    """`Agent ceiling: <seconds>` from docs/RUN_PARAMETERS.md beside the status file, else the default."""
    for status in status_candidates(cwd):
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(status)), "docs", "RUN_PARAMETERS.md"), encoding="utf-8") as f:
                m = re.search(r"^\s*[-*]?\s*\**Agent ceiling\**\s*:\s*(\d+)", f.read(), re.M | re.I)
            if m:
                return int(m.group(1))
        except OSError:
            continue
    return AGENT_CEILING


def owner_ceiling(cwd, kind):
    """`Ceiling above twice: <kind> <seconds> (...)` from the run parameters beside the status file."""
    for status in status_candidates(cwd):
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(status)), "docs", "RUN_PARAMETERS.md"), encoding="utf-8") as f:
                for m in re.finditer(r"^\s*[-*]?\s*\**Ceiling above twice\**\s*:\s*(\w+)\s+(\d+)\s*\(", f.read(), re.M | re.I):
                    if m.group(1).lower() == kind:
                        return int(m.group(2))
        except OSError:
            continue
    return None


def command_ceiling(cmd, cwd=None):
    """The limit a launched command runs under: `--limit N` in the command; with `--limit auto`
    twice its kind's default, or the owner's raised ceiling (the most the launcher learns)."""
    m = re.search(r"--limit\s+(\d+)", cmd)
    if m:
        return int(m.group(1))
    k = re.search(r"--kind\s+(builder|review|watch|test)", cmd)
    kind = k.group(1) if k else ("builder" if "cursor-agent" in cmd else "watch" if "gh pr checks" in cmd else "test")
    key = {"builder": "cursor-agent", "review": "review", "watch": "gh pr checks", "test": "# wake"}[kind]
    ceiling = KIND_CEILING[key]
    if "--limit auto" in cmd:
        return max(2 * ceiling, owner_ceiling(cwd, kind) or 0)
    return ceiling


def pending_from_hook(data, now, cwd):
    """What Claude Code itself says is in flight (release A2): the background tasks and the
    scheduled wake-ups of the hook input. None when the input has neither list, so the
    transcript is read instead."""
    tasks, crons = data.get("background_tasks"), data.get("session_crons")
    if not isinstance(tasks, list) and not isinstance(crons, list):
        return None, []
    pending, unscheduled = [], []
    dues, unknown_crons = [], 0
    for c in crons if isinstance(crons, list) else []:
        if isinstance(c, dict):
            due = parse_ts(c.get("next_run_at")) or (cron_next(str(c.get("schedule") or ""), now) if c.get("schedule") else None)
            if due is not None:
                dues.append(due)
            else:
                unknown_crons += 1                         # listed, its time unreadable: it still fires
            pending.append("scheduled wake-up %s" % c.get("id"))   # one past due fires as soon as the session is idle
    for t in tasks if isinstance(tasks, list) else []:
        if not isinstance(t, dict) or str(t.get("status") or "").lower() != "running":
            continue
        start = parse_ts(t.get("started_at") if t.get("started_at") is not None else t.get("startedAt")) or now
        age = now - start
        kind, cmd = str(t.get("type") or "").lower(), str(t.get("command") or "")
        is_agent = kind in ("background_subagent", "subagent", "agent", "agent sdk tool") or (not cmd and kind != "command")
        if not is_agent:                                   # a command: whatever the hook calls its type
            if not any(pat.search(cmd) for pat in WAKE_PATTERNS):
                continue                                   # a server never finishes, so it never wakes you
            if age <= command_ceiling(cmd, cwd) + GRACE_SECONDS:
                pending.append("background command %s" % t.get("id"))
        else:                                              # background_subagent, Agent SDK tool
            ceiling = agent_ceiling(cwd)
            if age > ceiling:
                continue                                   # past its ceiling: stop it and re-run its task in the foreground
            if any(due <= start + ceiling + 60 for due in dues) or unknown_crons:
                pending.append("background agent %s" % t.get("id"))
            else:
                unscheduled.append("%s (started %ds ago, ceiling %ds)" % (t.get("id"), int(age), ceiling))
    return pending, unscheduled


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
    record_input(data, cwd)
    phase = (field(status, "Phase") or "").strip()
    tp = data.get("transcript_path")
    final = data.get("last_assistant_message")           # the hook's own copy; the transcript lags
    if not isinstance(final, str) or not final.strip():
        final = last_assistant_text(tp) if tp and os.path.isfile(tp) else None
    if run_sheet_without_terminal(final):
        sys.stderr.write(RUN_SHEET_REASON + chr(10))
        sys.exit(2)
    if not phase.lower().startswith(ACTIVE_PHASES):
        allow()
    awaiting = (field(status, "Awaiting user on") or "").strip().strip("<>").strip()
    a = awaiting.lower()
    if a not in NOTHING and not a.startswith(("nothing", "none", "n/a")):
        allow()
    listed, unscheduled = pending_from_hook(data, time.time(), cwd)
    tp = data.get("transcript_path")
    if unscheduled:                                        # before anything else: a later wake-up does not bound the agent
        sys.stderr.write("Loop guard (Claude-Cursor Bridge, rule 43): you are waiting on a background agent with no wake-up scheduled at its ceiling: %s. A hung agent never completes and nothing else would wake you (plan 10.1, case 5). Before ending the turn, write it on the status file's `In flight:` line and schedule a one-shot wake-up at its ceiling with CronCreate (`recurring: false`, the prompt naming the agent); at that wake-up, stop an agent still running with TaskStop and run its task again in the foreground.%s" % (", ".join(unscheduled), chr(10)))
        sys.exit(2)
    if listed:
        allow()
    if listed is not None:                                 # Claude Code's own list is exact: nothing pending
        sys.stderr.write(REASON.format(phase=phase.split()[0]) + chr(10))
        sys.exit(2)
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
