#!/usr/bin/env python3
"""session-start: a Claude Code SessionStart hook (matchers: compact, resume, fork) that puts
the supervisor's core rules back after a compaction, a resume or a fork (KP-035).

Why: when a session's context is compacted, Claude Code re-attaches only the first part of
an invoked command (measured: 20,000 of the supervisor's 150,000 characters, 13%), so the
supervisor carried on for hours without its loop, its gate and its standing rules, and the
record shows the rule-breaking that followed.

Claude Code caps every hook's plain stdout at 10,000 characters and, above that, replaces it
with a file path and a 2,000-character preview. The two things this hook prints do not fit
together under that cap on a real project (the 0b review measured 9,841 characters, and the
part that was cut was the pointers), so the bridge registers the hook TWICE for the same
event, each run printing one part under its own cap:

  --part pointers   the project's phase from docs/PROJECT_STATUS.md (the "awaiting" text
                    capped), the exact sections of supervisor.md to re-read before the next
                    action with their line ranges, the conventions that phase relies on, and
                    whether to continue or to wait for the owner;
  --part digest     the digest at the top of ~/.claude/commands/supervisor.md (between the
                    markers <!-- digest:start --> and <!-- digest:end -->), the one text the
                    maintainer keeps as the condensed core.

Without --part both are printed (tests, manual runs). It prints nothing outside a bridge
project (no docs/PROJECT_STATUS.md found from the session's folder, its Workspace, a parent,
or a worktree). It FAILS OPEN on purpose: a session that is not the project's supervisor
(a review or a planning session opened in a project folder) is told to ignore the message,
because a gate on the transcript silenced the hook on two of three live supervisor sessions
(one invoked through the Skill tool, one continuing an earlier transcript; the 0b review's
second pass, S1), and a silent supervisor is the failure this hook exists to prevent. A
forked session is told not to continue the loop (S8). It never blocks (exit 0 always), never
writes anything, and keeps each part under the cap. ASCII-only apart from what it quotes.
"""
import json
import os
import re
import sys

MAX_OUTPUT = 9800           # per part; Claude Code's cap is 10,000
AWAITING_MAX = 300          # the quoted "Awaiting user on" text; the file is read whole anyway

PHASE_SECTIONS = {
    "intake": ["## Phase 1 — Intake"],
    "design": ["## Phase 2 — Design"],
    "mockups": ["## Phase 3 — UI mockups"],
    "interface": ["## Phase 3 — UI mockups"],
    "planning": ["## Phase 4 — Build plan", "## Run parameters — asked once, after the plan is approved, before configuration"],
    "configuration": ["## Phase 5 — Configure the Cursor build environment"],
    "configuring": ["## Phase 5 — Configure the Cursor build environment"],
    "configure": ["## Phase 5 — Configure the Cursor build environment"],
    "building": ["## Phase 6 — The delegation loop", "## Reflection points — stage close, phase gates, project end"],
    "changing": ["## The change cycle — a request on a finished project", "## Phase 6 — The delegation loop"],
    "done": ["## The change cycle — a request on a finished project"],
}
PHASE_CONVENTIONS = {
    "building": ["~/.claude/cursor-bridge/Merge-Verification-Policy.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
    "changing": ["~/.claude/cursor-bridge/Merge-Verification-Policy.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
    "design": ["~/.claude/cursor-bridge/Diagram-Planning-Conventions.md", "~/.claude/cursor-bridge/Glossary.md"],
    "configuration": ["~/.claude/cursor-bridge/Cursor-Project-Configuration.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
    "configuring": ["~/.claude/cursor-bridge/Cursor-Project-Configuration.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
    "configure": ["~/.claude/cursor-bridge/Cursor-Project-Configuration.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
}


def status_candidates(cwd):
    bases = []
    for start in (cwd, os.environ.get("CLAUDE_PROJECT_DIR") or ""):
        if not start:
            continue
        d = os.path.abspath(start)
        parts = d.replace("\\", "/").split("/")
        if "Worktrees" in parts:
            bases.append(os.path.join("/".join(parts[:parts.index("Worktrees")]), "Workspace"))
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
    pat = r"^\s*(?:[-*]\s+)?[*_`]*%s[*_`]*\s*:[*_`]*\s*(.*?)\s*$" % re.escape(name)
    m = re.search(pat, text, re.M | re.I)
    return m.group(1).strip().strip("*_`").strip() if m else None


def supervisor_path():
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "commands", "supervisor.md")


def digest_and_sections(path):
    """The digest text and {heading: (first line, last line)} for every '## ' section.
    Lines inside fenced code blocks are never headings (a template's '# Requirements' line
    once cut the design section short; the 0b review, finding 3)."""
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        lines = f.read().split("\n")
    text = "\n".join(lines)
    a, b = text.find("<!-- digest:start -->"), text.find("<!-- digest:end -->")
    digest = text[a + len("<!-- digest:start -->"):b].strip() if a >= 0 and b > a else ""
    sections, current, fenced = {}, None, False
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("## ") or line.startswith("# "):
            if current:
                sections[current][1] = i - 1
            current = line.strip()
            sections[current] = [i, len(lines)]
    return digest, {k: tuple(v) for k, v in sections.items()}


def cap(text, limit, what):
    if len(text) <= limit:
        return text
    return text[:limit - 90] + "\n[%s cut at %d characters by the hook's cap; re-read it in the file]" % (what, limit)


def pointers_part(status, sections, source):
    phase_raw = (field(status, "Phase") or "").strip()
    phase = phase_raw.split()[0].lower() if phase_raw else ""
    awaiting = (field(status, "Awaiting user on") or "nothing").strip()
    if len(awaiting) > AWAITING_MAX:
        awaiting = awaiting[:AWAITING_MAX] + "... (read it whole in docs/PROJECT_STATUS.md)"
    version = field(status, "Bridge version") or "?"
    waiting = awaiting.lower() not in ("nothing", "none", "", "-")
    out = ["CLAUDE-CURSOR BRIDGE: this folder belongs to a bridge project (bridge %s) and this message is for its supervisor session. "
           "If you are not the project's supervisor (you were not asked to act as supervisor here), ignore this message and the digest. "
           "The context was just %s, and a compaction keeps only the first part of your instructions; the core digest is re-injected beside this message." % (version, source),
           "",
           "PROJECT STATE: Phase: %s. Awaiting user on: %s." % (phase_raw or "unknown", awaiting)]
    wanted = PHASE_SECTIONS.get(phase, [])
    if wanted:
        out.append("BEFORE YOUR NEXT ACTION, re-read these sections of ~/.claude/commands/supervisor.md with the Read tool (offset = first line, limit = the line count):")
        for h in wanted:
            rng = sections.get(h)
            if rng:
                out.append("  - '%s': lines %d-%d" % (h.lstrip("# ").strip(), rng[0], rng[1]))
            else:
                out.append("  - '%s'" % h.lstrip("# ").strip())
    elif phase:
        out.append("BEFORE YOUR NEXT ACTION, re-read the section of ~/.claude/commands/supervisor.md for phase '%s' (not in the hook's map: find it by its heading)." % phase_raw)
    for conv in PHASE_CONVENTIONS.get(phase, []):
        out.append("  - and %s, whole" % conv)
    out.append("Then read docs/PROJECT_STATUS.md and docs/INVENTORY.md whole (rule 41).")
    if source == "forked from another session":
        out.append("This session is a COPY; the original may still be the supervisor. Do not continue the loop unless the owner says this session is the supervisor now.")
    elif waiting:
        out.append("The status file says you are WAITING FOR THE OWNER on: %s. Do not continue the loop; wait for their word, and clear the line when they give it." % awaiting)
    else:
        out.append("Continue from where the status file says the work is.")
    return "\n".join(out)


def digest_part(digest, version):
    head = "CLAUDE-CURSOR BRIDGE core digest (bridge %s) - the condensed core of ~/.claude/commands/supervisor.md; the full text governs:" % version
    return head + "\n\n" + (digest if digest else "(no digest found in supervisor.md; re-read the whole file)")


def main():
    argv = sys.argv[1:]
    part = "all"
    if "--part" in argv:
        i = argv.index("--part")
        part = argv[i + 1] if i + 1 < len(argv) else "all"
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    cwd = data.get("cwd") or os.getcwd()
    status = read_status(cwd)
    if status is None:
        return 0
    sv = supervisor_path()
    if not os.path.isfile(sv):
        return 0
    source = {"compact": "compacted", "resume": "resumed", "fork": "forked from another session"}.get(data.get("source"), "compacted or resumed")
    digest, sections = digest_and_sections(sv)
    version = field(status, "Bridge version") or "?"
    parts = []
    if part in ("pointers", "all"):
        parts.append(cap(pointers_part(status, sections, source), MAX_OUTPUT, "the section pointers"))
    if part in ("digest", "all"):
        parts.append(cap(digest_part(digest, version), MAX_OUTPUT, "the digest"))
    sys.stdout.write("\n\n".join(parts) + "\n")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # Claude Code reads the hook's output as UTF-8
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="backslashreplace")
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
