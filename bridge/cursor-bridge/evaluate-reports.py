#!/usr/bin/env python3
"""evaluate-reports: the report cycle's program (restructuring plan, section 12; release A3).

  python ~/.claude/cursor-bridge/evaluate-reports.py collect [--since <date>] [--ledger <file>] [--out <folder>]
  python ~/.claude/cursor-bridge/evaluate-reports.py extract --since <date> [--out <folder>]
  python ~/.claude/cursor-bridge/evaluate-reports.py record <project> <id> <outcome> [--reason <text>] [--ledger <file>]
  python ~/.claude/cursor-bridge/evaluate-reports.py seed [--ledger <file>]

Run in the bridge project by the maintainer session (the `/evaluate-reports` command), never by a
project supervisor. Read-only towards the projects: their documents, their supervisors' notes and
their session records are read in place and never written; the bridge's own files under Reports/
are the only output. Never prints a secret: the owner's messages are extracted as typed, and a
line holding a key-like value is replaced by its name.

What it reads (12.1): each project's `<Name> Issues During Development and Their Solutions.md`
and `<Name> Claude-Cursor Bridge Feedback.md` (Documents/ beside Workspace/), the private
notes Claude Code keeps per project (`~/.claude/projects/<key>/memory/*.md`), and, with
`extract`, the owner's typed messages and question-form answers from the session records since
the last run (`~/.claude/projects/<key>/*.jsonl`, every folder the project was opened in; a
session continued after a compaction is followed; subagents' records and app-inserted text are
left out).

Entries (12.2): an Issues entry is a `## ISS-nnn — title` heading (or `## Issue n — title`, or any
`## ` heading of the Issues document when it carries no ID); a Feedback entry is a `### ` section
under a `## Stage ...` heading (`FB-nnn` where the document numbers them). An entry's ID is the
project's own; an entry without one gets `<document>:<heading fingerprint>` inside the ledger,
never in the document. The ledger (`Reports/ledger.json`) keeps, per project and ID, the date
evaluated, the fingerprint of the entry's text and the outcome: fixed in release X, pitfall
KP-nnn, planned in section Y, declined with the reason, or project-specific.

`collect` writes `Reports/Evaluations/<date>/unprocessed.md`: every entry absent from the ledger
(unprocessed) or whose text no longer matches its fingerprint (updated, with the earlier
outcome shown beside it), with its text, for the session to classify; a run with nothing new
prints one line and writes nothing. `record` writes a verdict into the ledger. `seed` enters the
Known Pitfalls, the changelog's releases and the first evaluation's tables as outcomes so that
the first scheduled run raises nothing already handled.

Exit 0 = done; 1 = a document could not be read; 2 = usage. ASCII-only on purpose.
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
PROJECTS = {
    "reAngle": r"E:\ck04k02s01-reangle-prototype",
    "TDP": r"E:\p19-technical-documentation-provider",
    "Video Factory": r"E:\pk02k02s02-short-form-video-factory",
}
ISSUES_SUFFIX = "Issues During Development and Their Solutions.md"
FEEDBACK_SUFFIX = "Claude-Cursor Bridge Feedback.md"
ID_RX = re.compile(r"^##\s+(?:(ISS-\d{3,}[a-z]?)|Issue\s+(\d+))\b", re.I)
FB_RX = re.compile(r"\b(FB-\d{3,})\b")
SECRET_RX = re.compile(r"(?i)\b([A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSPHRASE))\b\s*[:=]\s*\S+")
OUTCOMES = ("fixed", "pitfall", "planned", "declined", "project-specific")
MAINTAINER_RX = re.compile(r"cross-session-message|Another Claude session sent a message|Maintainer session \(bridge mechanics|^From .*(Agent|session)", re.I | re.M)


def bridge_root(start=None):
    """The bridge project's root (holds Reports/), found from the current folder."""
    d = os.path.abspath(start or os.getcwd())
    for _ in range(5):
        if os.path.isdir(os.path.join(d, "Reports")) and os.path.isdir(os.path.join(d, "Workspace")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.path.abspath(start or os.getcwd())


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def fingerprint(text):
    return hashlib.sha256(re.sub(r"\s+", " ", text.strip()).encode("utf-8")).hexdigest()[:16]


def project_key(root):
    """Claude Code's folder name for a project path: the path with every separator and colon as a dash."""
    return re.sub(r"[:\\/]", "-", root)


# ---------------------------------------------------------------- the documents
def documents(project_root):
    folder = os.path.join(project_root, "Documents")
    found = {}
    if not os.path.isdir(folder):
        return found
    for name in os.listdir(folder):
        if name.endswith(ISSUES_SUFFIX):
            found["issues"] = os.path.join(folder, name)
        elif name.endswith(FEEDBACK_SUFFIX):
            found["feedback"] = os.path.join(folder, name)
    return found


def issues_entries(text, document):
    """[(id, heading, body)] of an Issues document: one entry per `## ` heading."""
    entries, current = [], None
    for line in text.split("\n"):
        if line.startswith("## "):
            if current:
                entries.append(current)
            m = ID_RX.match(line)
            eid = (m.group(1).upper() if m and m.group(1) else ("ISSUE-%s" % m.group(2) if m else None))
            current = [eid, line[3:].strip(), ""]
        elif current is not None:
            current[2] += line + "\n"
    if current:
        entries.append(current)
    out = []
    for eid, heading, body in entries:
        if eid is None:
            eid = "%s:%s" % (document, fingerprint(heading)[:8])
        out.append((eid, heading, body))
    return out


def feedback_entries(text, document):
    """[(id, heading, body)] of a Feedback document: one entry per `### ` section, under its stage."""
    entries, stage, current = [], "", None
    for line in text.split("\n"):
        if line.startswith("## "):
            stage = line[3:].strip()
            if current:
                entries.append(current)
                current = None
        elif line.startswith("### "):
            if current:
                entries.append(current)
            current = [None, "%s / %s" % (stage, line[4:].strip()), ""]
        elif current is not None:
            current[2] += line + "\n"
    if current:
        entries.append(current)
    out = []
    for _, heading, body in entries:
        m = FB_RX.search(heading) or FB_RX.search(body[:200])
        eid = m.group(1).upper() if m else "%s:%s" % (document, fingerprint(heading)[:8])
        out.append((eid, heading, body))
    return out


def notes_entries(project_root, home=None):
    """[(id, heading, body)] of the supervisor's private notes, keyed by file name."""
    out = []
    for key in (project_key(project_root), project_key(os.path.join(project_root, "Workspace"))):
        folder = os.path.join(home or HOME, ".claude", "projects", key, "memory")
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if name.endswith(".md") and name != "MEMORY.md":
                body = read(os.path.join(folder, name))
                out.append(("note:%s" % name, name, body))
    return out


def collect_entries(projects=None, home=None):
    """{project: [(source, id, heading, body)]} over the three sources, read in place."""
    found = {}
    for project, root in (projects or PROJECTS).items():
        rows = []
        docs = documents(root)
        if "issues" in docs:
            for eid, heading, body in issues_entries(read(docs["issues"]), "issues"):
                rows.append(("issues", eid, heading, body))
        if "feedback" in docs:
            for eid, heading, body in feedback_entries(read(docs["feedback"]), "feedback"):
                rows.append(("feedback", eid, heading, body))
        for eid, heading, body in notes_entries(root, home):
            rows.append(("note", eid, heading, body))
        found[project] = rows
    return found


# ---------------------------------------------------------------- the ledger
def load_ledger(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_ledger(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def ledger_key(project, eid):
    return "%s/%s" % (project, eid)


def today():
    return datetime.date.today().isoformat()


def unprocessed(entries, ledger):
    """[(project, source, id, heading, body, earlier outcome or None)] absent from the ledger or changed since."""
    out = []
    for project, rows in entries.items():
        for source, eid, heading, body in rows:
            rec = ledger.get(ledger_key(project, eid))
            fp = fingerprint(heading + "\n" + body)
            if rec is None:
                out.append((project, source, eid, heading, body, None))
            elif rec.get("fingerprint") != fp:
                out.append((project, source, eid, heading, body, rec))
    return out


def redact(text):
    return SECRET_RX.sub(lambda m: "%s=<value withheld>" % m.group(1), text)


def cmd_collect(a):
    root = bridge_root()
    ledger_path = a.ledger or os.path.join(root, "Reports", "ledger.json")
    ledger = load_ledger(ledger_path)
    projects = PROJECTS if not a.projects else {k: v for k, v in PROJECTS.items() if k in a.projects}
    if a.project_root:
        projects = {a.project_name or os.path.basename(a.project_root): a.project_root}
    entries = collect_entries(projects, a.home)
    rows = unprocessed(entries, ledger)
    if not rows:
        total = sum(len(v) for v in entries.values())
        print("evaluate-reports: nothing new - %d entries of %d project(s), all evaluated and unchanged since" % (total, len(entries)))
        return 0
    out_dir = a.out or os.path.join(root, "Reports", "Evaluations", today())
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "unprocessed.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Unprocessed and updated entries, %s\n\n" % today())
        f.write("%d entries. Each needs one verdict: fixed <release> | pitfall KP-nnn | planned <section> | declined <reason> | project-specific. Record with `evaluate-reports.py record <project> <id> <outcome> --reason <text>`.\n\n" % len(rows))
        for project, source, eid, heading, body, earlier in rows:
            tag = "UPDATED (earlier: %s %s)" % (earlier.get("outcome"), earlier.get("reason") or "") if earlier else "NEW"
            f.write("## %s / %s / %s - %s\n\n%s\n\n%s\n\n" % (project, source, eid, tag, heading, redact(body.strip())[:6000]))
    print("evaluate-reports: %d entries to evaluate (%d new, %d updated) -> %s" % (
        len(rows), sum(1 for r in rows if r[5] is None), sum(1 for r in rows if r[5] is not None), path))
    return 0


def cmd_record(a):
    root = bridge_root()
    ledger_path = a.ledger or os.path.join(root, "Reports", "ledger.json")
    if a.outcome not in OUTCOMES:
        print("evaluate-reports: outcome must be one of %s" % ", ".join(OUTCOMES))
        return 2
    if a.outcome in ("fixed", "pitfall", "planned", "declined") and not a.reason:
        print("evaluate-reports: %s needs --reason (the release, the KP id, the plan section, or why)" % a.outcome)
        return 2
    ledger = load_ledger(ledger_path)
    projects = {a.project_name or os.path.basename(a.project_root): a.project_root} if a.project_root else None
    entries = collect_entries(projects, a.home)
    fp = None
    for source, eid, heading, body in entries.get(a.project, []):
        if eid == a.id:
            fp = fingerprint(heading + "\n" + body)
    if fp is None and not a.force:
        print("evaluate-reports: no entry %s in %s's documents or notes (use --force to record it anyway)" % (a.id, a.project))
        return 2
    ledger[ledger_key(a.project, a.id)] = {"evaluated": today(), "fingerprint": fp or "", "outcome": a.outcome, "reason": a.reason or ""}
    save_ledger(ledger_path, ledger)
    print("evaluate-reports: %s/%s -> %s%s" % (a.project, a.id, a.outcome, (" (%s)" % a.reason) if a.reason else ""))
    return 0


def classification_column(header):
    for i, h in enumerate(header):
        if "classification" in h.lower() or h.strip().lower() in ("class", "verdict"):
            return i
    return None


def cmd_seed(a):
    """The first scheduled run must raise nothing already handled: every entry the first
    evaluation (Reports/Evaluations/2026-10-04/*.md) classified is recorded with its class."""
    root = bridge_root()
    ledger_path = a.ledger or os.path.join(root, "Reports", "ledger.json")
    ledger = load_ledger(ledger_path)
    entries = collect_entries()
    projects = {a.project_name or os.path.basename(a.project_root): a.project_root} if a.project_root else None
    entries = collect_entries(projects, a.home)
    seeded = 0
    for path in sorted(glob.glob(os.path.join(a.evaluations or os.path.join(root, "Reports", "Evaluations", "2026-10-04"), "*.md"))):
        col = None
        for line in read(path).split("\n"):
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if col is None or set("".join(cells)) <= set("-: "):
                c = classification_column(cells)
                if c is not None:
                    col = c
                continue
            if len(cells) <= col:
                continue
            m = re.search(r"\b(CLOSED|PLANNED|PARTLY|OPEN)\b", cells[col])
            if not m:
                continue
            outcome = {"CLOSED": "fixed", "PLANNED": "planned", "PARTLY": "planned", "OPEN": "planned"}[m.group(1)]
            wanted = set(x.upper() for x in re.findall(r"\b(ISS-\d{3,}[a-z]?|FB-\d{3,})\b", cells[0]))
            wanted |= set("ISSUE-%s" % n for n in re.findall(r"\bIssue\s+(\d+)", cells[0]))
            fb = re.findall(r"Feedback Stage (\w+),\s*([^;()|]+)", cells[0])
            for project, rows in entries.items():
                for source, e, heading, body in rows:
                    hit = e.upper() in wanted
                    if not hit and source == "feedback":
                        for stage, words in fb:
                            w = [x.lower() for x in re.findall(r"[A-Za-z]+", words)][:2]
                            if heading.lower().startswith("stage %s" % stage.lower()) and all(x in heading.lower() for x in w):
                                hit = True
                    if hit and ledger_key(project, e) not in ledger:
                        ledger[ledger_key(project, e)] = {"evaluated": a.date or "2026-10-04", "fingerprint": fingerprint(heading + "\n" + body),
                                                          "outcome": outcome, "reason": "first evaluation of 2026-10-04: %s" % m.group(1)}
                        seeded += 1
    save_ledger(ledger_path, ledger)
    print("evaluate-reports: %d entries seeded; the ledger holds %d" % (seeded, len(ledger)))
    return 0


# ---------------------------------------------------------------- the owner's messages
def session_files(project_root, home=None):
    out = []
    for key in (project_key(project_root), project_key(os.path.join(project_root, "Workspace"))):
        out += glob.glob(os.path.join(home or HOME, ".claude", "projects", key, "*.jsonl"))
    return sorted(set(out))


def owner_messages(path, since):
    """[(time, kind, text)]: the owner's typed messages and question-form answers, nothing else."""
    out = []
    questions = {}
    try:
        f = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return out
    with f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            ts = str(o.get("timestamp") or "")
            if ts[:10] < since:
                continue
            msg = o.get("message") or {}
            if o.get("type") == "user" and msg.get("role") == "user" and not o.get("isMeta"):
                c = msg.get("content")
                if isinstance(c, str) and c.strip() and not c.lstrip().startswith("<") and not MAINTAINER_RX.search(c):
                    out.append((ts, "message", c.strip()))   # the maintainer session's messages are not the owner's words (rule 57)
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                for x in msg["content"]:
                    if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("name") == "AskUserQuestion":
                        questions[x.get("id")] = x.get("input") or {}
            tur = o.get("toolUseResult")
            if isinstance(tur, dict) and isinstance(tur.get("answers"), dict):
                for q, ans in tur["answers"].items():
                    out.append((ts, "answer", "Q: %s\nA: %s" % (q.strip()[:300], str(ans).strip()[:300])))
    return out


def cmd_extract(a):
    root = bridge_root()
    out_dir = a.out or os.path.join(root, "Reports", "Evaluations", today())
    os.makedirs(out_dir, exist_ok=True)
    total = 0
    projects = {a.project_name or os.path.basename(a.project_root): a.project_root} if a.project_root else PROJECTS
    for project, proot in projects.items():
        rows = []
        for path in session_files(proot, a.home):
            rows += owner_messages(path, a.since)
        rows.sort()
        if not rows:
            continue
        total += len(rows)
        with open(os.path.join(out_dir, "owner-messages-%s.md" % project.replace(" ", "-")), "w", encoding="utf-8") as f:
            f.write("# The owner's messages and answers, %s, since %s\n\nFilters: typed messages and question-form answers only; app-inserted text, pasted blocks, notifications and subagents' records left out; every session folder the project was opened in; values of keys withheld.\n\n" % (project, a.since))
            for ts, kind, text in rows:
                f.write("- %s [%s] %s\n" % (ts[:16].replace("T", " "), kind, redact(text).replace("\n", " / ")[:1200]))
    print("evaluate-reports: %d message(s) and answer(s) extracted since %s -> %s" % (total, a.since, out_dir))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("collect")
    c.add_argument("--ledger")
    c.add_argument("--out")
    c.add_argument("--projects", nargs="*")
    c.add_argument("--project-root", help="one project root instead of the three (tests)")
    c.add_argument("--project-name")
    c.add_argument("--home", help="the folder holding .claude/projects (tests)")
    r = sub.add_parser("record")
    r.add_argument("project")
    r.add_argument("id")
    r.add_argument("outcome")
    r.add_argument("--reason")
    r.add_argument("--ledger")
    r.add_argument("--force", action="store_true")
    r.add_argument("--project-root")
    r.add_argument("--project-name")
    r.add_argument("--home")
    s = sub.add_parser("seed")
    s.add_argument("--ledger")
    s.add_argument("--date")
    s.add_argument("--evaluations", help="the folder of the first evaluation's tables (default Reports/Evaluations/2026-10-04)")
    s.add_argument("--project-root")
    s.add_argument("--project-name")
    s.add_argument("--home")
    e = sub.add_parser("extract")
    e.add_argument("--since", required=True)
    e.add_argument("--out")
    e.add_argument("--project-root")
    e.add_argument("--project-name")
    e.add_argument("--home")
    a = ap.parse_args()
    if not a.cmd:
        ap.print_usage()
        return 2
    try:
        return {"collect": cmd_collect, "record": cmd_record, "seed": cmd_seed, "extract": cmd_extract}[a.cmd](a)
    except OSError as e2:
        print("evaluate-reports: a file could not be read or written (%s)" % e2)
        return 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
