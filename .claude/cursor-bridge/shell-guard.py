#!/usr/bin/env python3
"""
Bridge shell guard — a fail-closed `beforeShellExecution` hook for the headless
Cursor builder (cursor-agent). It runs BEFORE the builder executes any shell command
and DENIES a tight, high-confidence set of genuinely dangerous / irreversible /
data-exfil commands. Everything else passes untouched.

This is the ONE deliberately fail-closed hook in the bridge (the linter/design/security
detect hooks are advisory/fail-open). Wire it in `.cursor/hooks.json` with
`"failClosed": true` so a crash/timeout/bad-JSON BLOCKS — Cursor has a documented bug
where a malformed hook response silently ALLOWS, so this script also defaults to DENY on
any internal error (belt-and-suspenders).

Contract (Cursor hooks):
  - stdin  : JSON payload for the beforeShellExecution event (carries the command string).
             On Windows, Cursor prefixes it with a UTF-8 BOM — decode utf-8-sig.
  - stdout : {"permission": "allow"|"deny", "user_message": ..., "agent_message": ...}
  - exit   : 0 = proceed, 2 = block (equivalent to permission:"deny").

Scope note: this governs the BUILDER's shell (cursor-agent). The supervisor's own
`git reset --hard HEAD` recovery runs through Claude's Bash tool, NOT cursor-agent, so it
is unaffected — which is why blocking destructive git here is safe.

The deny-list below is the auditable policy. Keep it tight: an over-broad guard that
stalls normal builds is the fastest way to get a safety control switched off.
"""

import json
import re
import sys

# --- Dangerous-target helper (used for recursive deletes) ---------------------
# A recursive/forced delete is blocked ONLY when it targets one of these — so that
# ordinary build cleanup (`rm -rf node_modules`, `rm -rf dist`) is NOT blocked.
_DANGEROUS_DELETE_TARGETS = [
    r"/\s*$", r"/\*", r"~", r"\$home", r"%userprofile%",
    r"(^|\s)\.(\s|$)", r"(^|\s)\./(\s|$)", r"\.\.", r"(^|\s)\*(\s|$)",
    r"[a-z]:\\?\s*$",            # Windows drive root, e.g. C:\
    r"\.git\b", r"\.env\b", r"(^|[\s/\\])secrets?([\s/\\]|$)",
]

# --- Deny rules: (name, compiled regex, message) ------------------------------
# Matched case-insensitively against the whitespace-normalised command string.
def _rx(p):
    return re.compile(p, re.IGNORECASE)

_ALWAYS_DENY = [
    # Disk / filesystem destruction
    ("disk-destruction", _rx(r"\bmkfs\b|\bformat\s+[a-z]:|\bdd\b[^|]*\bof=/dev/|>\s*/dev/sd"),
     "Disk/filesystem-destroying command."),
    # Irreversible git (builder must never rewrite history or discard the tree)
    ("git-irreversible", _rx(
        r"\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-[a-z]*f|\bgit\s+push\b[^|]*(--force\b|--force-with-lease\b|(^|\s)-f(\s|$))"
        r"|\bgit\s+rebase\b|\bgit\s+branch\s+-D\b|\bgit\s+filter-branch\b|git\s+filter-repo\b|\bgit\s+update-ref\s+-d\b"
        r"|\bgit\s+worktree\s+remove\b[^|]*(--force\b|(^|\s)-f(\s|$))"),
     "Irreversible git operation (history rewrite / hard reset / force push / clean / forced worktree removal, "
     "which follows a live junction and deletes the real target). The builder never does these."),
    # Download piped straight into an interpreter (remote code execution)
    ("download-pipe-to-shell", _rx(
        r"\b(curl|wget|iwr|invoke-webrequest)\b[^|]*\|\s*(sh|bash|zsh|python|python3|node|perl|ruby)\b"
        r"|\b(iex|invoke-expression)\b[^|]*(downloadstring|invoke-webrequest|iwr\b|curl\b|wget\b)"),
     "Downloading and executing remote code in one step (RCE vector)."),
    # Outbound data exfiltration
    ("data-exfil", _rx(
        r"\b(curl|wget)\b[^|]*(-x\s*post|--data(-binary|-raw)?\b|(^|\s)-d\s|(^|\s)-t\s)"
        r"|\bscp\b[^|]*@[^\s]+:|\brsync\b[^|]*(::|@[^\s]+:)|\bn(c|cat)\b[^|]*-e\b"),
     "Outbound data transfer / reverse shell."),
    # Privilege escalation and system / security-control tampering
    ("privilege-or-control-tamper", _rx(
        r"\bsudo\b|\brunas\b|\breg\s+(add|delete)\b|\bschtasks\b|\bsc\s+create\b"
        r"|\.git[\\/]+hooks|\bchmod\s+-r?\s*777\b"),
     "Privilege escalation or tampering with a system/security control."),
    # Writes to protected paths (best-effort: obvious redirect / copy / move forms)
    ("protected-path-write", _rx(
        r"(>|>>)\s*\.?(env\b|/?secrets?[\\/]|[\w./\\-]*\.cursor[\\/][\w./\\-]*\.json|[\w./\\-]*\.git[\\/])"
        r"|\b(cp|mv|copy|move)\b[^|]*\s(\.env\b|secrets?[\\/])"),
     "Write to a protected path (.env, secrets/, .cursor/*.json, .git/)."),
]

# Recursive/forced deletes get target-aware handling so normal cleanup is allowed.
_RECURSIVE_DELETE = _rx(
    r"\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r|\brm\s+.*(-r\b|--recursive).*(-f\b|--force)"
    r"|\brmdir\s+/s|\bdel\b[^|]*/s|\brd\s+/s|remove-item\b[^|]*-recurse[^|]*-force|remove-item\b[^|]*-force[^|]*-recurse")


def _deny(reason):
    msg = ("Blocked by the bridge shell guard: %s "
           "If this is genuinely required, raise it with the supervisor — do not work around the guard."
           % reason)
    print(json.dumps({"permission": "deny", "user_message": msg, "agent_message": msg}))
    sys.exit(2)


def _allow():
    print(json.dumps({"permission": "allow"}))
    sys.exit(0)


def _extract_command(payload):
    # beforeShellExecution carries the command string; be defensive about the shape.
    if isinstance(payload, dict):
        for key in ("command", "cmd", "commandLine", "shellCommand"):
            v = payload.get(key)
            if isinstance(v, str) and v.strip():
                return v
        # Fall back to any string value that looks like a command.
        for v in payload.values():
            if isinstance(v, str) and v.strip():
                return v
    if isinstance(payload, str):
        return payload
    return None


def main():
    # Fail CLOSED on any error: if we cannot read or understand the request, DENY.
    try:
        raw = sys.stdin.buffer.read()
        text = raw.decode("utf-8-sig")  # strips the Windows BOM Cursor prepends
        payload = json.loads(text) if text.strip() else {}
    except Exception:
        _deny("could not read/parse the hook request (failing closed).")
        return

    command = _extract_command(payload)
    if not command:
        # No command found — nothing to guard; allow so we do not stall benign events.
        _allow()
        return

    norm = re.sub(r"\s+", " ", command.strip())

    try:
        for name, rx, message in _ALWAYS_DENY:
            if rx.search(norm):
                _deny("%s [%s]" % (message, name))
                return

        if _RECURSIVE_DELETE.search(norm):
            low = norm.lower()
            for pat in _DANGEROUS_DELETE_TARGETS:
                if re.search(pat, low, re.IGNORECASE):
                    _deny("recursive/forced delete of a dangerous target (root, home, cwd, "
                          "wildcard, drive root, or a protected path). [recursive-delete]")
                    return
            # Recursive delete of an ordinary subdirectory (node_modules, dist, …) — allowed.
    except Exception:
        _deny("guard evaluation error (failing closed).")
        return

    _allow()


if __name__ == "__main__":
    main()
