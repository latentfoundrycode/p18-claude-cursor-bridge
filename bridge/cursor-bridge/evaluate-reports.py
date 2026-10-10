#!/usr/bin/env python3
"""evaluate-reports: the report cycle's program (restructuring plan, section 12; release A3).

  python ~/.claude/cursor-bridge/evaluate-reports.py collect [--ledger <file>] [--out <folder>]
  python ~/.claude/cursor-bridge/evaluate-reports.py extract [--since <date>] [--out <folder>]
  python ~/.claude/cursor-bridge/evaluate-reports.py record <project> <id> <outcome> [--reason <text>] [--ledger <file>]
  python ~/.claude/cursor-bridge/evaluate-reports.py seed [--ledger <file>] [--evaluations <folder>]

Run in the bridge project by the maintainer session (the `/evaluate-reports` command), never by a
project supervisor. Read-only towards the projects: their documents, their supervisors' notes and
their session records are read in place and never written; the bridge's own files under Reports/
are the only output. Never prints a secret: the owner's messages are extracted as typed, and every
token shaped like a key, and every `NAME=value` of a key-like name, is replaced by a marker.

What it reads (12.1): each project's `<Name> Issues During Development and Their Solutions.md`
and `<Name> Claude-Cursor Bridge Feedback.md` (Documents/ beside Workspace/), the private notes
Claude Code keeps per project (`~/.claude/projects/<key>/memory/*.md`), and, with `extract`, the
owner's typed messages and question-form answers from the session records since the last run
(`~/.claude/projects/<key>/*.jsonl`, every folder the project was opened in; only records the app
marks as the owner's own typing, `origin.kind == human`; a compaction summary, app-inserted text,
a notification and a message from another session are left out; a record is counted once by its
uuid; a message with a screenshot keeps its text).

Entries (12.2), in the documents' own shapes: an Issues entry is each `## ` section (`## ISS-nnn`,
`## Issue n`, or a plain heading); a Feedback entry is any section whose heading carries `FB-nnn`
(at any level), each numbered `## n.` section (the video factory's form), each `### ` section under
a stage heading (reAngle's form), and the body a `## ` section holds before its first `### ` (the
TDP's form). An entry's ID is the project's own (`ISS-nnn`, `FB-nnn`, `ISSUE-n`, `FEEDBACK-n`);
an entry without one is identified by a fingerprint of its first body lines (so a renamed heading
does not make it new), with the heading kept as its label. `collect` prints, per document, how
many entries it found and how many lines lie outside any entry, so a silent loss is visible. The
ledger (`Reports/ledger.json`) keeps, per project and ID, the date evaluated, the fingerprint of
the entry's text and the outcome: fixed in release X, pitfall KP-nnn, planned in section Y,
declined with the reason, or project-specific.

`collect` writes `Reports/Evaluations/<date>/unprocessed.md`: every entry absent from the ledger
(unprocessed) or whose text no longer matches its fingerprint (updated, with the earlier outcome
shown beside it); a run with nothing new prints one line and writes no evaluation file (the
ledger keeps the run's date). `record` writes a
verdict. `seed` enters the first evaluation's tables (`Reports/Evaluations/2026-10-04/<Project>.md`,
one file per project, matched to that project only) as outcomes, so that the first scheduled run
raises nothing already handled.

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
ISSUE_HEAD_RX = re.compile(r"^##\s+(?:(ISS-\d{3,}[a-z]?)|Issue\s+(\d+))\b", re.I)
FB_RX = re.compile(r"\b(FB-\d{3,})\b")
NUMBERED_RX = re.compile(r"^##\s+(\d+)\.\s")
SECRET_RX = re.compile(r"(?i)\b([A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSPHRASE))\b\s*[:=]\s*\S+")
KEY_TOKEN_RX = re.compile(r"\b(sk-[A-Za-z0-9_-]{8,}|hf_[A-Za-z0-9]{8,}|gh[pousr]_[A-Za-z0-9]{8,}|xox[a-z]-[A-Za-z0-9-]{8,}|AKIA[A-Z0-9]{12,}|AIza[A-Za-z0-9_-]{20,}|[A-Za-z0-9_-]{40,})\b")
MAINTAINER_RX = re.compile(r"cross-session-message|Another Claude session sent a message|Maintainer session \(bridge mechanics", re.I)
OUTCOMES = ("fixed", "pitfall", "planned", "declined", "project-specific")
DATE_RX = re.compile(r"^\d{4}-\d\d-\d\d$")


def bridge_root(start=None):
    """The bridge project's root (holds Reports/ and Workspace/), found from the current folder."""
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


def body_id(prefix, body, heading):
    """An ID for an entry the project did not number: the first three non-empty body lines,
    normalised (a renamed heading keeps the ID); the heading when the body is empty."""
    lines = [l.strip() for l in body.split("\n") if l.strip()][:3]
    return "%s:%s" % (prefix, fingerprint(" ".join(lines) if lines else heading)[:10])


def project_key(root):
    """Claude Code's folder name for a project path: the path with every separator and colon as a dash."""
    return re.sub(r"[:\\/]", "-", root)


def project_of_file(name, projects):
    """The project an evaluation file belongs to, by its stem (TDP.md, reAngle.md, Video Factory.md)."""
    stem = re.sub(r"[^a-z0-9]", "", os.path.splitext(os.path.basename(name))[0].lower())
    for project in projects:
        if re.sub(r"[^a-z0-9]", "", project.lower()) == stem:
            return project
    return None


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


def sections(text, level):
    """[(heading line, body, start line)] of a document's headings of exactly `level` hashes."""
    out, current = [], None
    mark = "#" * level + " "
    for n, line in enumerate(text.split("\n")):
        if line.startswith(mark):
            if current:
                out.append(current)
            current = [line, "", n]
        elif current is not None:
            if re.match(r"^#{1,%d} " % (level - 1), line) if level > 1 else False:
                out.append(current)
                current = None
            else:
                current[1] += line + "\n"
    if current:
        out.append(current)
    return out


def issues_entries(text):
    """[(id, label, body, lines)] of an Issues document: one entry per `## ` section."""
    out = []
    for heading, body, start in sections(text, 2):
        m = ISSUE_HEAD_RX.match(heading)
        label = heading[3:].strip()
        eid = (m.group(1).upper() if m and m.group(1) else ("ISSUE-%s" % m.group(2) if m else body_id("issues", body, label)))
        out.append((eid, label, body, 1 + body.count("\n")))
    return out


def feedback_entries(text):
    """[(id, label, body, lines)] of a Feedback document, in all three shapes the projects use."""
    out, taken = [], set()
    lines = text.split("\n")
    # 1. any heading carrying FB-nnn, at any level: the section to the next heading of its level or higher
    for n, line in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if not m:
            continue
        fb = FB_RX.search(m.group(2))
        if not fb:
            continue
        level = len(m.group(1))
        body = []
        for k in range(n + 1, len(lines)):
            if re.match(r"^#{1,%d} " % level, lines[k]):
                break
            body.append(lines[k])
            taken.add(k)
        taken.add(n)
        out.append((fb.group(1).upper(), m.group(2).strip(), "\n".join(body) + "\n", len(body) + 1))
    # 2. `## ` sections: a numbered entry (## n.) whole, else the body before the first ### and each ### section
    stage = ""
    for heading, body, start in sections(text, 2):
        if start in taken:
            continue
        label = heading[3:].strip()
        num = NUMBERED_RX.match(heading)
        if num:
            out.append(("FEEDBACK-%s" % num.group(1), label, body, 1 + body.count("\n")))
            for k in range(start, start + 1 + body.count("\n")):
                taken.add(k)
            continue
        stage = label
        own = re.split(r"^### ", body, maxsplit=1, flags=re.M)[0]      # empty when the first subsection follows the heading directly
        if own.strip() and not re.match(r"^\s*$", own):
            out.append((body_id("feedback", own, label), label, own, 1 + own.count("\n")))
            for k in range(start, start + 1 + own.count("\n")):
                taken.add(k)
    for heading, body, start in sections(text, 3):
        if start in taken:
            continue
        label = "%s / %s" % (stage_of(lines, start), heading[4:].strip())
        out.append((body_id("feedback", body, label), label, body, 1 + body.count("\n")))
        for k in range(start, start + 1 + body.count("\n")):
            taken.add(k)
    return out


def stage_of(lines, index):
    for k in range(index, -1, -1):
        if lines[k].startswith("## "):
            return lines[k][3:].strip()
    return ""


def outside(text, entries):
    """Lines of a document that belong to no entry: the title and the preamble, and anything lost."""
    total = len([l for l in text.split("\n") if l.strip()])
    inside = sum(len([l for l in body.split("\n") if l.strip()]) + 1 for _, _, body, _ in entries)
    return max(0, total - inside)


def notes_entries(project_root, home=None):
    """[(id, label, body, lines)] of the supervisor's private notes, keyed by file name."""
    out = []
    for key in (project_key(project_root), project_key(os.path.join(project_root, "Workspace"))):
        folder = os.path.join(home or HOME, ".claude", "projects", key, "memory")
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if name.endswith(".md") and name != "MEMORY.md":
                body = read(os.path.join(folder, name))
                out.append(("note:%s" % name, name, body, 1 + body.count("\n")))
    return out


def collect_entries(projects=None, home=None, report=None):
    """{project: [(source, id, label, body)]} over the three sources, read in place."""
    found = {}
    for project, root in (projects or PROJECTS).items():
        rows = []
        docs = documents(root)
        for source, parse in (("issues", issues_entries), ("feedback", feedback_entries)):
            if source not in docs:
                continue
            text = read(docs[source])
            entries = parse(text)
            for eid, label, body, _ in entries:
                rows.append((source, eid, label, body))
            if report is not None:
                report.append("%s %s: %d entries, %d line(s) outside any entry" % (project, source, len(entries), outside(text, entries)))
        for eid, label, body, _ in notes_entries(root, home):
            rows.append(("note", eid, label, body))
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
    """[(project, source, id, label, body, earlier outcome or None)] absent from the ledger or changed since."""
    out = []
    for project, rows in entries.items():
        for source, eid, label, body in rows:
            rec = ledger.get(ledger_key(project, eid))
            fp = fingerprint(body)
            if rec is None:
                out.append((project, source, eid, label, body, None))
            elif rec.get("fingerprint") and rec.get("fingerprint") != fp:
                out.append((project, source, eid, label, body, rec))
    return out


def redact(text):
    text = SECRET_RX.sub(lambda m: "%s=<value withheld>" % m.group(1), text)
    return KEY_TOKEN_RX.sub("<value withheld>", text)


def projects_from(a):
    return {a.project_name or os.path.basename(a.project_root): a.project_root} if getattr(a, "project_root", None) else None


def cmd_collect(a):
    root = bridge_root()
    ledger_path = a.ledger or os.path.join(root, "Reports", "ledger.json")
    ledger = load_ledger(ledger_path)
    report = []
    entries = collect_entries(projects_from(a), a.home, report)
    for line in report:
        print("evaluate-reports: " + line)
    rows = unprocessed(entries, ledger)
    ledger["_meta"] = {"last_collect": today()}
    save_ledger(ledger_path, ledger)
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
        for project, source, eid, label, body, earlier in rows:
            tag = "UPDATED (earlier: %s %s)" % (earlier.get("outcome"), earlier.get("reason") or "") if earlier else "NEW"
            f.write("## %s / %s / %s - %s\n\n%s\n\n%s\n\n" % (project, source, eid, tag, label, redact(body.strip())[:6000]))
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
    entries = collect_entries(projects_from(a), a.home)
    fp = None
    for source, eid, label, body in entries.get(a.project, []):
        if eid == a.id:
            fp = fingerprint(body)
    if fp is None and not a.force:
        print("evaluate-reports: no entry %s in %s's documents or notes (use --force to record it anyway)" % (a.id, a.project))
        return 2
    ledger[ledger_key(a.project, a.id)] = {"evaluated": today(), "fingerprint": fp or "", "outcome": a.outcome, "reason": a.reason or "", "forced": fp is None}
    save_ledger(ledger_path, ledger)
    print("evaluate-reports: %s/%s -> %s%s" % (a.project, a.id, a.outcome, (" (%s)" % a.reason) if a.reason else ""))
    return 0


def separator(line):
    inner = line.replace("|", "").strip()
    return bool(inner) and set(inner) <= set("-: ")


def column(header, words):
    """The index of the header cell carrying one of the words whole ("Class", "ID or source"), never a substring."""
    for i, h in enumerate(header):
        if re.search(r"\b(?:%s)\b" % "|".join(words), h.strip().lower()):
            return i
    return None


def cmd_seed(a):
    """The first scheduled run must raise nothing already handled: every entry the first evaluation
    classified (one table file per project, matched to that project only) is recorded with its class."""
    root = bridge_root()
    ledger_path = a.ledger or os.path.join(root, "Reports", "ledger.json")
    ledger = load_ledger(ledger_path)
    projects = projects_from(a) or PROJECTS
    entries = collect_entries(projects, a.home)
    seeded, skipped = 0, []
    for path in sorted(glob.glob(os.path.join(a.evaluations or os.path.join(root, "Reports", "Evaluations", "2026-10-04"), "*.md"))):
        project = project_of_file(path, projects)
        if project is None:
            skipped.append(os.path.basename(path))
            continue
        rows = entries.get(project, [])
        src_col = cls_col = None
        lines = read(path).split("\n")
        for n, line in enumerate(lines):
            if not line.startswith("|") or separator(line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if n + 1 < len(lines) and separator(lines[n + 1]):          # the header: the row before the |---| line, once per table
                cls_col, src_col = column(cells, ("classification", "class", "verdict")), column(cells, ("source", "id"))
                continue
            if cls_col is None or len(cells) <= cls_col:
                continue
            m = re.search(r"\b(CLOSED|PLANNED|PARTLY|OPEN)\b", cells[cls_col])
            if not m:
                continue
            outcome = {"CLOSED": "fixed", "PLANNED": "planned", "PARTLY": "planned", "OPEN": "planned"}[m.group(1)]
            src = cells[src_col] if src_col is not None and len(cells) > src_col else cells[0]
            wanted = set(x.upper() for x in re.findall(r"\b(ISS-\d{3,}[a-z]?|FB-\d{3,})\b", src))
            numbers = set(re.findall(r"\bIssues?\s+(\d+)", src))
            for lo, hi in re.findall(r"\bIssues?\s+(\d+)-(\d+)", src):
                numbers |= set(str(n) for n in range(int(lo), int(hi) + 1))
            wanted |= set(x for n in numbers for x in ("ISSUE-%s" % n, "ISS-%03d" % int(n)))   # a numbered issue in either spelling
            wanted |= set("FEEDBACK-%s" % n for n in re.findall(r"\bFeedback\s+(\d+)\b", src))
            notes = set("note:" + n for n in re.findall(r"`([\w.-]+\.md)`", src))
            notes |= set("note:%s.md" % n for n in re.findall(r"[Mm]emory\s+`([\w-]+)`", src))      # the TDP: memory `ci-config-gotchas` item 6
            quoted = [q.lower() for q in re.findall(r'Feedback\s+"([^"]+)"', src)]              # the TDP: Feedback "Milestone 5 close"
            fb = re.findall(r"Feedback Stage (\w+),\s*([^;()|]+)", src)                           # reAngle: Feedback Stage 3a, Stalls item 1
            for source, e, label, body in rows:
                hit = e.upper() in wanted or e in notes
                if not hit and source == "feedback":
                    low = label.lower()
                    hit = any(q in low for q in quoted)
                    for stage, words in fb:
                        w = [x.lower() for x in re.findall(r"[A-Za-z]+", re.split(r"\bitem\b|\d|\(", words)[0])][:2]
                        if low.startswith("stage %s" % stage.lower()) and all(x in low for x in w):
                            hit = True
                if hit and ledger_key(project, e) not in ledger:
                    ledger[ledger_key(project, e)] = {"evaluated": a.date or "2026-10-04", "fingerprint": fingerprint(body),
                                                      "outcome": outcome, "reason": "first evaluation of 2026-10-04: %s" % m.group(1)}
                    seeded += 1
    save_ledger(ledger_path, ledger)
    print("evaluate-reports: %d entries seeded; the ledger holds %d%s" % (
        seeded, len([k for k in ledger if not k.startswith("_")]), ("; files of no project skipped: %s" % ", ".join(skipped)) if skipped else ""))
    return 0


# ---------------------------------------------------------------- the owner's messages
def session_files(project_root, home=None):
    out = []
    for key in (project_key(project_root), project_key(os.path.join(project_root, "Workspace"))):
        out += glob.glob(os.path.join(home or HOME, ".claude", "projects", key, "*.jsonl"))
    return sorted(set(out))


def message_text(content):
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [x.get("text", "") for x in content if isinstance(x, dict) and x.get("type") == "text"]
        images = sum(1 for x in content if isinstance(x, dict) and x.get("type") == "image")
        text = "\n".join(p for p in parts if p).strip()
        return (text + (" [with %d image(s)]" % images if images else "")).strip() if (text or images) else ""
    return ""


def command_text(text):
    """A slash command the owner typed is recorded as app text (<command-message>, <command-name>/x</command-name>,
    <command-args>); keep the name and the arguments, drop the rest of the app's wrapping."""
    if not text.lstrip().startswith("<command-"):
        return text
    m = re.search(r"<command-name>\s*(/?[\w-]+)", text)
    if not m:
        return ""
    args = re.search(r"<command-args>\s*([^<]*)", text)
    return ("command: %s %s" % (m.group(1), args.group(1).strip() if args else "")).strip()


def owner_messages(path, since, seen):
    """[(time, kind, text)]: the owner's own typed messages (origin.kind == human, no compaction
    summary, no app text, no other session's message) and question-form answers; each record once."""
    out = []
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
            uid = o.get("uuid") or (ts + str(o.get("parentUuid")))
            if uid in seen:
                continue
            msg = o.get("message") or {}
            origin = o.get("origin") if isinstance(o.get("origin"), dict) else {}
            if o.get("type") == "user" and msg.get("role") == "user" and origin.get("kind") == "human" \
                    and not o.get("isMeta") and not o.get("isCompactSummary"):
                text = command_text(message_text(msg.get("content")))
                if text and not text.lstrip().startswith("<") and not MAINTAINER_RX.search(text):
                    seen.add(uid)
                    out.append((ts, "message", text))
            tur = o.get("toolUseResult")
            if isinstance(tur, dict) and isinstance(tur.get("answers"), dict):
                seen.add(uid)
                for q, ans in tur["answers"].items():
                    out.append((ts, "answer", "Q: %s\nA: %s" % (q.strip()[:300], str(ans).strip()[:300])))
    return out


def last_run(root, ledger_path):
    meta = load_ledger(ledger_path).get("_meta") or {}
    if DATE_RX.match(str(meta.get("last_extract") or "")):
        return meta["last_extract"]
    folder = os.path.join(root, "Reports", "Evaluations")
    dated = sorted(d for d in os.listdir(folder) if DATE_RX.match(d) and d < today()) if os.path.isdir(folder) else []   # never today's, which collect has just made
    return dated[-1] if dated else "2026-10-04"


def cmd_extract(a):
    root = bridge_root()
    ledger_path = a.ledger or os.path.join(root, "Reports", "ledger.json")
    since = a.since or last_run(root, ledger_path)
    out_dir = a.out or os.path.join(root, "Reports", "Evaluations", today())
    os.makedirs(out_dir, exist_ok=True)
    total = 0
    for project, proot in (projects_from(a) or PROJECTS).items():
        rows, seen = [], set()
        for path in session_files(proot, a.home):
            rows += owner_messages(path, since, seen)
        rows.sort()
        if not rows:
            continue
        total += len(rows)
        with open(os.path.join(out_dir, "owner-messages-%s.md" % project.replace(" ", "-")), "w", encoding="utf-8") as f:
            f.write("# The owner's messages and answers, %s, since %s\n\nFilters: only records the app marks as the owner's own typing and the question-form answers; compaction summaries, app-inserted text, notifications and other sessions' messages left out; each record once; every session folder the project was opened in; key values and key-shaped tokens withheld.\n\n" % (project, since))
            for ts, kind, text in rows:
                f.write("- %s [%s] %s\n" % (ts[:16].replace("T", " "), kind, redact(text).replace("\n", " / ")[:1200]))
    ledger = load_ledger(ledger_path)
    ledger.setdefault("_meta", {})["last_extract"] = today()
    save_ledger(ledger_path, ledger)
    print("evaluate-reports: %d message(s) and answer(s) extracted since %s -> %s" % (total, since, out_dir))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    for name in ("collect", "record", "seed", "extract"):
        p = sub.add_parser(name)
        p.add_argument("--ledger")
        p.add_argument("--project-root", help="one project root instead of the three (tests)")
        p.add_argument("--project-name")
        p.add_argument("--home", help="the folder holding .claude/projects (tests)")
        if name in ("collect", "extract"):
            p.add_argument("--out")
        if name == "record":
            p.add_argument("project")
            p.add_argument("id")
            p.add_argument("outcome")
            p.add_argument("--reason")
            p.add_argument("--force", action="store_true")
        if name == "seed":
            p.add_argument("--date")
            p.add_argument("--evaluations", help="the folder of the first evaluation's tables (default Reports/Evaluations/2026-10-04)")
        if name == "extract":
            p.add_argument("--since", help="a date; default the ledger's last extract, else the newest evaluation folder")
    a = ap.parse_args()
    if not a.cmd:
        ap.print_usage()
        return 2
    try:
        return {"collect": cmd_collect, "record": cmd_record, "seed": cmd_seed, "extract": cmd_extract}[a.cmd](a)
    except OSError as e:
        print("evaluate-reports: a file could not be read or written (%s)" % e)
        return 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
