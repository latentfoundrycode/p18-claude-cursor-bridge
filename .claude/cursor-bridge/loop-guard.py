#!/usr/bin/env python3
"""loop-guard: a Claude Code Stop hook that keeps a bridge supervisor from ending its turn
while the build loop has work and nothing is going to wake it.

Registered in the bridge's settings.json (hooks -> Stop). Reads the hook's JSON on stdin.
It BLOCKS the stop - exit code 2 with the reason on stderr, which Claude Code feeds back to
the model (documented; code.claude.com hooks reference) - only when ALL hold:

  1. the session runs in a bridge Workspace: <cwd>/docs/PROJECT_STATUS.md exists;
  2. its `Phase:` is building or changing;
  3. its `Awaiting user on:` is `nothing` (the supervisor is not waiting for the owner);
  4. nothing is pending that will wake the session: no background command, background
     agent, or scheduled wake-up started in the last GRACE_HOURS without a completion
     notification in the transcript;
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
TAIL_BYTES = 12 * 1024 * 1024
RECHECK_SECONDS = 2.0      # grace for the asynchronously written transcript
ACTIVE_PHASES = ("building", "changing")
NOTHING = ("nothing", "none", "-", "")

REASON = (
    "Loop guard (Claude-Cursor Bridge): docs/PROJECT_STATUS.md says Phase: {phase} and "
    "Awaiting user on: nothing, and no background command or agent is running that would wake "
    "you. Ending the turn now stalls the build until the owner notices. Do the next step of the "
    "loop instead. If you are waiting for CI, start ONE background watch of the PR's required "
    "checks (gh pr checks <n> --watch --required --fail-fast, run in the background) - its completion wakes "
    "you; the desktop app's CI monitor never reports a green gate. If you are genuinely waiting "
    "for the owner (an escalation, a gate, a pause they asked for, a stage pause), write that on "
    "the `Awaiting user on:` line first, then stop."
)


def allow():
    sys.exit(0)


def read_status(cwd):
    for base in (cwd, os.environ.get("CLAUDE_PROJECT_DIR") or ""):
        if not base:
            continue
        p = os.path.join(base, "docs", "PROJECT_STATUS.md")
        if os.path.isfile(p):
            with open(p, encoding="utf-8-sig", errors="replace") as f:
                return f.read()
    return None


def field(text, name):
    m = re.search(r"^\s*%s\s*:\s*(.*?)\s*$" % re.escape(name), text, re.M | re.I)
    return m.group(1) if m else None


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


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
    started, done, wakeups = {}, set(), []
    cutoff = now - GRACE_HOURS * 3600
    for line in raw.splitlines():
        try:
            o = json.loads(line)
        except ValueError:
            continue
        ts = parse_ts(o.get("timestamp") or "") or now
        tur = o.get("toolUseResult")
        if isinstance(tur, dict):
            tid = tur.get("backgroundTaskId") or (tur.get("agentId") if tur.get("isAsync") else None) \
                or tur.get("taskId")
            if tid and ts >= cutoff:
                started[str(tid)] = ts
        origin = o.get("origin")
        if isinstance(origin, dict) and origin.get("senderTaskId"):
            done.add(str(origin["senderTaskId"]))
        msg = o.get("message") or {}
        content = msg.get("content")
        texts = []
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
    if not phase.lower().startswith(ACTIVE_PHASES):
        allow()
    awaiting = (field(status, "Awaiting user on") or "").strip().strip("<>").strip()
    if awaiting.lower() not in NOTHING and not awaiting.lower().startswith("nothing"):
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
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)                                # fail open, always
