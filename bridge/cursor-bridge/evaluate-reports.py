#!/usr/bin/env python3
"""evaluate-reports: the report cycle's program (restructuring plan, section 12; release A3).

  python ~/.claude/cursor-bridge/evaluate-reports.py collect [--ledger <file>] [--out <folder>]
  python ~/.claude/cursor-bridge/evaluate-reports.py extract [--since <date>] [--out <folder>]
  python ~/.claude/cursor-bridge/evaluate-reports.py record <project> <id> <outcome> [--reason <text>] [--ledger <file>]
  python ~/.claude/cursor-bridge/evaluate-reports.py seed [--ledger <file>] [--evaluations <folder>]
  python ~/.claude/cursor-bridge/evaluate-reports.py security [--date <YYYY-MM-DD>] [--seed-from <evaluation file>]

Run in the bridge project by the maintainer session (the `/evaluate-reports` command), never by a
project supervisor. Read-only towards the projects: their documents, their supervisors' notes and
their session records are read in place and never written; the bridge's own files under Reports/
are the only output. Never prints a secret: the owner's messages are extracted as typed, and every
token shaped like a key, and every `NAME=value` of a key-like name, is replaced by a marker.

The projects and their roots are read from `~/.cursor-bridge/projects.json`, a JSON object of
project name to project root (an absolute folder holding `Workspace/`), when no `--project-root` is
given. An absent or malformed file is named and refused with exit 2.

What it reads (12.1): each project's `<Name> Issues During Development and Their Solutions.md`
and `<Name> Claude-Cursor Bridge Feedback.md` (Documents/ beside Workspace/), the private notes
Claude Code keeps per project (`~/.claude/projects/<key>/memory/*.md`), and, with `extract`, the
owner's typed messages and question-form answers from the session records since the last run
(`~/.claude/projects/<key>/*.jsonl`, every folder the project was opened in; only records the app
marks as the owner's own typing, `origin.kind == human`; a compaction summary, app-inserted text,
a notification and a message from another session are left out; a record is counted once by its
uuid; a message with a screenshot keeps its text; times are UTC, as the records hold them). The
bridge's own project `Bridge` reads its notes and session records from its Workspace's folder key
only: the root's key is the maintainer's own and never a report source. Also read: the one
`Open issues:` line of each project's status file (Workspace/docs/PROJECT_STATUS.md), for the
incidents it names as still to write (2026.10.25a, C8 of 2026-10-18): a part of the line that says
"to write" and names no ISS entry the Issues document holds is shown as TO WRITE, so an incident
not yet written is not missed for a week; nothing else of the status file is read.

`security` (R-097) makes GET requests only, through `gh api`, for each project's weekly dependency-
scan workflow, its runs since the last read and its open Dependabot alerts. It writes
`Reports/Evaluations/<date>/security.md` and moves the window in the ledger's `_meta.security`.
`--seed-from` seeds the window from a hand-written evaluation's Dependency scan table. GitHub reads
use the owner's `gh` login; nothing is written to GitHub.

Entries (12.2), in the documents' own shapes: an Issues entry is each `## ` section (`## ISS-nnn`,
`## Issue n`, or a plain heading); a Feedback entry is any section whose heading carries `FB-nnn`
(at any level), each numbered `## n.` section (the video factory's form), each `### ` section under
a stage heading (reAngle's form), and the body a `## ` section holds before its first `### ` (the
TDP's form). An entry's ID is the project's own (`ISS-nnn`, `FB-nnn`, `ISSUE-n`, `FEEDBACK-n`);
an entry without one is identified by a fingerprint of its first body lines (so a renamed heading
does not make it new), with the heading kept as its label. A recurrence heading under an ID the
document already holds (`### FB-001 (recurred 2026-10-18)`) is part of that entry, read as its
update, never a second entry under the same key (2026.10.25a). `collect` prints, per document, how
many entries it found and how many lines lie outside any entry, so a silent loss is visible. The
ledger (`Reports/ledger.json`) keeps, per project and ID, the date evaluated, the fingerprint of
the entry's text and the outcome: fixed in release X, pitfall KP-nnn, planned in section Y,
declined with the reason, or project-specific.

`collect` writes `Reports/Evaluations/<date>/unprocessed.md`: every entry absent from the ledger
(unprocessed) or whose text no longer matches its fingerprint (updated, with the earlier outcome
shown beside it); an entry whose verdict was recorded with `--force` before the project wrote it
(no fingerprint) is shown on its first appearance as WRITTEN with the forced verdict beside it,
and its fingerprint is taken then, so a later change surfaces as UPDATED (2026.10.25a: four
entries written after a forced verdict were never shown); a run with nothing new prints one line
and writes no evaluation file (the ledger keeps the run's date). `record` writes a
verdict. `seed` enters the first evaluation's tables (`Reports/Evaluations/2026-10-04/<Project>.md`,
one file per project, matched to that project only) as outcomes, so that the first scheduled run
raises nothing already handled.

Exit 0 = done; 1 = a document could not be read or written; 2 = usage or the projects file.
ASCII-only on purpose.
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env  # noqa: E402

HOME = os.path.expanduser("~")
PROJECTS_FILE_LABEL = "~/.cursor-bridge/projects.json"
HTTPS_ORIGIN_RX = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")
SSH_ORIGIN_RX = re.compile(r"^git@github\.com:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?$")
DEP_SCAN_SUFFIX = "/dependency-scan.yml"
EXIT_LINE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z dependency-scan: OSV-Scanner exit (\d+)$")
GIT_REMOTE_LIMIT = 30
SCANNER_OTHER = frozenset(("cancelled", "timed_out", "startup_failure", "skipped", "action_required", "neutral", "stale"))
# A project whose root's own folder key is the maintainer's session (the bridge's root): only its
# Workspace's key is a report source, for the notes and the session records alike.
WORKSPACE_KEY_ONLY = ("Bridge",)
STATUS_TO_WRITE_RX = re.compile(r"\bto (?:be )?write\b|\bto be written\b|\bnot yet written\b", re.I)
ISS_ID_RX = re.compile(r"\bISS-\d{3,}[a-z]?\b", re.I)
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


def project_keys(project, root):
    """The folder keys under ~/.claude/projects that are this project's: the root's and the
    Workspace's; the Workspace's only for the bridge's own project, whose root key is the
    maintainer's (2026.10.25a; by name, or by the bridge's root under any name)."""
    keys = [project_key(root), project_key(os.path.join(root, "Workspace"))]
    bridge = os.path.normcase(os.path.abspath(bridge_root()))
    if project in WORKSPACE_KEY_ONLY or os.path.normcase(os.path.abspath(root)) == bridge:
        keys = keys[1:]
    return keys


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
    return merge_recurrences(out)


def merge_recurrences(entries):
    """One entry per ID: a later section under an ID already found (`### FB-001 (recurred
    2026-10-18)`) is appended to the first, heading and body, so it reads as that entry's update
    and never as a second entry under the same key (2026.10.25a, C1)."""
    out, at = [], {}
    for eid, label, body, lines in entries:
        if eid in at:
            first = out[at[eid]]
            out[at[eid]] = (eid, first[1], first[2] + "\n" + label + "\n" + body, first[3] + lines)
            continue
        at[eid] = len(out)
        out.append((eid, label, body, lines))
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
        if own.strip() and (re.search(r"^\s*(?:[-*]|\d+[.)])\s", own, re.M) or len(own.strip()) >= 400):   # a stage heading's short preamble (reAngle: "Bridge versions in force: ...") is not an entry; its items are the ### sections (2026.10.11c)
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
    return merge_recurrences(out)


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


def status_entries(project_root, written, report=None):
    """[(id, label, body, lines)] of the incidents the status file's `Open issues:` line names as
    still to write (2026.10.25a, C8 of 2026-10-18), less those the Issues document already holds
    (`written`, a set of IDs). Only that one line of the status file is read."""
    path = os.path.join(project_root, "Workspace", "docs", "PROJECT_STATUS.md")
    try:
        text = read(path)
    except OSError:
        return []
    values, malformed, _disagrees = bridge_env.status_values(text)
    if malformed is not None:
        line, _what = malformed
        if report is not None:
            report.append("header malformed: %s:%d" % (path.replace("\\", "/"), line))
    segments = values.get("open_issues") or []
    out = []
    for seg in segments:
        if not STATUS_TO_WRITE_RX.search(seg):
            continue
        ids = [x.upper() for x in ISS_ID_RX.findall(seg)]
        if ids and all(x in written for x in ids):
            continue                                   # written since: the Issues entry is the source now
        eid = "status:%s" % ids[0] if ids else body_id("status", seg, seg)
        out.append((eid, "Open issues: " + seg[:120], seg + "\n", 1))
    return out


def notes_entries(project_root, home=None, project=None):
    """[(id, label, body, lines)] of the supervisor's private notes, keyed by file name."""
    out = []
    for key in project_keys(project, project_root):
        folder = os.path.join(home or HOME, ".claude", "projects", key, "memory")
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if name.endswith(".md") and name != "MEMORY.md":
                body = read(os.path.join(folder, name))
                out.append(("note:%s" % name, name, body, 1 + body.count("\n")))
    return out


def collect_entries(projects, home=None, report=None):
    """{project: [(source, id, label, body)]} over the three sources, read in place."""
    found = {}
    for project, root in projects.items():
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
        written = set(eid for source, eid, _, _ in rows if source == "issues")
        to_write = status_entries(root, written, report)
        for eid, label, body, _ in to_write:
            rows.append(("status", eid, label, body))
        if report is not None and to_write:
            report.append("%s status: %d incident(s) named on the Open issues: line as still to write" % (project, len(to_write)))
        for eid, label, body, _ in notes_entries(root, home, project):
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
            elif not rec.get("fingerprint") and source != "status":
                out.append((project, source, eid, label, body, rec))   # forced before it was written: shown once, as WRITTEN
            elif rec.get("fingerprint") and rec.get("fingerprint") != fp:
                out.append((project, source, eid, label, body, rec))
    return out


def row_tag(source, earlier):
    """NEW, TO WRITE (a status-line incident), WRITTEN (its verdict forced before the entry existed) or UPDATED."""
    if earlier is None:
        return "TO WRITE (named on the status file's Open issues: line; not yet written as an ISS entry)" if source == "status" else "NEW"
    if not earlier.get("fingerprint"):
        return "WRITTEN (forced verdict: %s %s)" % (earlier.get("outcome"), earlier.get("reason") or "")
    return "UPDATED (earlier: %s %s)" % (earlier.get("outcome"), earlier.get("reason") or "")


def redact(text):
    text = SECRET_RX.sub(lambda m: "%s=<value withheld>" % m.group(1), text)
    return KEY_TOKEN_RX.sub("<value withheld>", text)


def projects_from(a):
    return {a.project_name or os.path.basename(a.project_root): a.project_root} if getattr(a, "project_root", None) else None


def projects_file_path(home=None):
    return os.path.join(os.path.expanduser("~"), ".cursor-bridge", "projects.json")


def load_projects(home=None):
    """(projects dict, None) or (None, refusal text naming PROJECTS_FILE_LABEL)."""
    path = projects_file_path()
    prefix = "%s holds a JSON object of project name to project root" % PROJECTS_FILE_LABEL
    if not os.path.isfile(path):
        return None, "%s; the file is absent" % prefix
    try:
        with open(path, encoding="utf-8-sig") as f:
            raw = f.read()
    except UnicodeDecodeError:
        return None, "%s; the file is not UTF-8 text" % prefix
    except OSError:
        return None, "%s; the file could not be read" % prefix
    try:
        data = json.loads(raw)
    except ValueError:
        return None, "%s; the file is not JSON" % prefix
    if not isinstance(data, dict):
        return None, "%s; the file is not a JSON object" % prefix
    out = {}
    for key, value in data.items():
        if not isinstance(key, str) or not key:
            return None, "%s; the file holds an empty key" % prefix
        if not isinstance(value, str):
            return None, "%s; a value is not a string" % prefix
        out[key] = value
    return out, None


def resolve_projects(a):
    one = projects_from(a)
    if one is not None:
        return one, None
    return load_projects()


def printable_ascii(text):
    if not isinstance(text, str):
        text = str(text)
    out = []
    for ch in text:
        o = ord(ch)
        if ch in "\n\r":
            out.append(" ")
        elif 0x20 <= o <= 0x7E:
            out.append(ch)
        elif o <= 0xFF:
            out.append("\\x%02x" % o)
        else:
            out.append("\\u%04x" % o)
    return "".join(out)


def ascii_line(text):
    return printable_ascii(text)


def parse_utc(text):
    if not text:
        return None
    text = str(text).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.datetime.fromisoformat(text)
    except ValueError:
        return None


def _repo_segment_ok(segment):
    return bool(segment) and not all(c == "." for c in segment)


def github_repo_from_url(url):
    url = (url or "").strip()
    for rx in (HTTPS_ORIGIN_RX, SSH_ORIGIN_RX):
        m = rx.match(url)
        if m and _repo_segment_ok(m.group(1)) and _repo_segment_ok(m.group(2)):
            return m.group(1), m.group(2)
    return None


def _git_env():
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_NO_LAZY_FETCH"] = "1"
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
    ):
        env.pop(key, None)
    return env


def git_origin_repo(project_root):
    ws = os.path.join(project_root, "Workspace")
    if not os.path.isdir(ws):
        return None
    cmd = ["git", "-c", "core.fsmonitor=false", "-C", ws, "remote", "get-url", "origin"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            creationflags=bridge_env.NO_WINDOW,
            timeout=GIT_REMOTE_LIMIT,
            text=True,
            env=_git_env(),
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    return github_repo_from_url(proc.stdout.strip())


def _gh_api_raw(args):
    """GH_COMMAND + ['api'] + args. (exit_code, stdout text) or (-1, None) on timeout/start failure."""
    command = list(bridge_env.GH_COMMAND) + ["api"] + list(args)
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            creationflags=bridge_env.NO_WINDOW,
            timeout=bridge_env.GH_API_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return -1, None
    except OSError:
        return -2, None
    out = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
    return proc.returncode, out


def _raw_failure_phrase(rc):
    if rc == -1:
        return "timed out"
    if rc == -2:
        return "gh could not start"
    if rc != 0:
        return "gh exited non-zero"
    return "reply could not be parsed"


def _api_failure_phrase(reason, body):
    if reason == "timed out":
        return "timed out"
    if reason == "gh cannot start":
        return "gh could not start"
    if isinstance(body, dict):
        st = body.get("status")
        if st is not None and re.fullmatch(r"\d+", str(st)):
            code = int(st)
            if code == 403:
                return "refused (HTTP 403)"
            if 100 <= code <= 599:
                return "refused (HTTP %d)" % code
    if reason == "reply is not JSON":
        return "reply could not be parsed"
    return "gh exited non-zero"


def _http_status_from_include(text):
    if not text:
        return None
    head = text.split("\r\n\r\n", 1)[0] if "\r\n\r\n" in text else text.split("\n\n", 1)[0]
    if not head.startswith("HTTP/"):
        return None
    m = re.search(r"HTTP/\S+\s+(\d+)", head.split("\r\n", 1)[0].split("\n", 1)[0])
    if m and re.fullmatch(r"\d+", m.group(1)):
        return int(m.group(1))
    return None


def _gh_api_include(path):
    rc, text = _gh_api_raw(["-i", path])
    if text is None:
        return False, _raw_failure_phrase(rc), None
    status = _http_status_from_include(text)
    if status == 404:
        return True, "", "alerts_off"
    if status == 204:
        return True, "", "alerts_on"
    if status is not None and status >= 400:
        if status == 403:
            return False, "refused (HTTP 403)", None
        return False, "refused (HTTP %d)" % status, None
    if rc != 0:
        return False, "gh exited non-zero", None
    return False, "reply could not be parsed", None


def _gh_paginate_json(path):
    rc, text = _gh_api_raw(["--paginate", path])
    if text is None:
        return False, _raw_failure_phrase(rc), None
    if rc != 0:
        stripped = text.strip()
        if stripped:
            try:
                body = json.loads(stripped)
                if isinstance(body, dict):
                    return False, _api_failure_phrase("", body), None
            except ValueError:
                pass
        return False, "gh exited non-zero", None
    if not text.strip():
        return False, "reply could not be parsed", None
    items, idx, raw = [], 0, text.strip()
    dec = json.JSONDecoder()
    while idx < len(raw):
        while idx < len(raw) and raw[idx].isspace():
            idx += 1
        if idx >= len(raw):
            break
        try:
            chunk, end = dec.raw_decode(raw, idx)
        except ValueError:
            return False, "reply could not be parsed", None
        if not isinstance(chunk, list):
            return False, "reply could not be parsed", None
        for item in chunk:
            if not isinstance(item, dict):
                return False, "reply could not be parsed", None
        items.extend(chunk)
        idx = end
    return True, "", items


def log_exit_code(log_text):
    code = None
    for line in (log_text or "").splitlines():
        m = EXIT_LINE_RX.match(line.strip("\r"))
        if m:
            code = int(m.group(1))
    return code


def security_runs_day(entry, meta):
    lrr = (entry or {}).get("last_run_read")
    if lrr:
        t = parse_utc(lrr)
        if t:
            return t.date().isoformat()
    le = (meta or {}).get("last_extract")
    if le and DATE_RX.match(str(le)):
        return str(le)
    return None


def run_in_window(run, last_run_read, had_entry, last_extract):
    created = parse_utc(run.get("created_at"))
    if not created:
        return False
    if last_run_read:
        start = parse_utc(last_run_read)
        if start and created <= start:
            return False
        if start:
            return True
    if had_entry:
        return True
    if last_extract and DATE_RX.match(str(last_extract)):
        return created.date() > datetime.date.fromisoformat(str(last_extract))
    return True


def dependency_workflow(workflows_body):
    if not isinstance(workflows_body, dict):
        return None
    wfs = workflows_body.get("workflows")
    if not isinstance(wfs, list):
        return None
    for wf in wfs:
        if not isinstance(wf, dict):
            continue
        path = wf.get("path") or ""
        if path.endswith(DEP_SCAN_SUFFIX):
            return wf
    return None


def _digit_id(value):
    if value is None:
        return None
    s = str(value)
    if not re.fullmatch(r"\d+", s):
        return None
    return int(s)


def _normalize_standing(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    s = str(value)
    if re.fullmatch(r"\d+", s):
        return int(s)
    return None


def _validate_workflows_body(body):
    if not isinstance(body, dict):
        return "reply could not be parsed"
    wfs = body.get("workflows")
    if not isinstance(wfs, list):
        return "reply could not be parsed"
    for wf in wfs:
        if not isinstance(wf, dict):
            return "reply could not be parsed"
    return None


def _validate_runs_list(runs):
    if not isinstance(runs, list):
        return "reply could not be parsed"
    for run in runs:
        if not isinstance(run, dict):
            return "reply could not be parsed"
        if not parse_utc(run.get("created_at")):
            return "reply could not be parsed"
        if run.get("status") == "completed" and not run.get("conclusion"):
            return "reply could not be parsed"
        rid = run.get("id")
        if rid is not None and not re.fullmatch(r"\d+", str(rid)):
            return "reply could not be parsed"
    return None


def _validate_jobs_body(body):
    if not isinstance(body, dict):
        return "reply could not be parsed"
    jobs = body.get("jobs")
    if not isinstance(jobs, list):
        return "reply could not be parsed"
    for job in jobs:
        if not isinstance(job, dict):
            return "reply could not be parsed"
        jid = job.get("id")
        if jid is not None and not re.fullmatch(r"\d+", str(jid)):
            return "reply could not be parsed"
    return None


def _completed_runs(runs):
    out = [r for r in runs if r.get("status") == "completed" and r.get("conclusion")]
    out.sort(key=lambda r: parse_utc(r.get("created_at")) or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    return out


def _standing_cleared(standing_id, prev_last, window_runs, all_runs):
    if standing_id is None:
        return True
    threshold = None
    for run in all_runs:
        if _digit_id(run.get("id")) == standing_id:
            threshold = parse_utc(run.get("created_at"))
            break
    if threshold is None and prev_last:
        threshold = parse_utc(prev_last)
    if threshold is None:
        return False
    for run in window_runs:
        if run.get("status") == "completed" and run.get("conclusion") == "success":
            created = parse_utc(run.get("created_at"))
            if created and created > threshold:
                return True
    return False


def _run_exit_code(owner, repo, run):
    run_id = _digit_id(run.get("id"))
    if run_id is None:
        return None, ("jobs list", "reply could not be parsed")
    jobs_path = "repos/%s/%s/actions/runs/%d/jobs" % (owner, repo, run_id)
    ok, reason, body = bridge_env._gh_get(jobs_path)
    if not ok:
        return None, ("jobs list", _api_failure_phrase(reason, body))
    err = _validate_jobs_body(body)
    if err:
        return None, ("jobs list", err)
    for job in body.get("jobs") or []:
        if job.get("conclusion") != "failure":
            continue
        job_id = _digit_id(job.get("id"))
        if job_id is None:
            return None, ("jobs list", "reply could not be parsed")
        log_path = "repos/%s/%s/actions/jobs/%d/logs" % (owner, repo, job_id)
        rc_log, log_text = _gh_api_raw([log_path])
        if log_text is None:
            return None, ("job log", _raw_failure_phrase(rc_log))
        if rc_log != 0:
            return None, ("job log", "gh exited non-zero")
        code = log_exit_code(log_text)
        if code is not None:
            return code, None
    return None, None


def classify_window_runs(window_runs, owner, repo):
    completed = _completed_runs(window_runs)
    rerun = "gh workflow run dependency-scan.yml --repo %s/%s" % (owner, repo)
    if not completed:
        if any(r.get("status") in ("queued", "in_progress", "waiting") for r in window_runs):
            return "no completed run", None, None, False
        return "no completed run", rerun, None, False
    last = completed[-1]
    conclusion = last.get("conclusion")
    last_at = last.get("created_at")
    if conclusion == "success":
        return "green", None, last_at, True
    if conclusion == "failure":
        return "pending_failure", None, last_at, True
    return "scanner failure", rerun, last_at, True


def read_failure_remedy(alerts=False):
    remedy = "gh auth refresh -s repo for the login's scope"
    if alerts:
        remedy += "; the repository's Security tab"
    return remedy


def _format_alerts(alerts):
    if not alerts:
        return "No open Dependabot alert."
    parts = []
    for al in alerts:
        num = al.get("number")
        pkg = ((al.get("dependency") or {}).get("package") or {}).get("name") or ""
        ghsa = ((al.get("security_advisory") or {}).get("ghsa_id") or "")
        parts.append("alert %s %s %s" % (num, pkg, ghsa))
    return "; ".join(parts)


def _read_alerts(owner, repo, read_failures):
    vuln_path = "repos/%s/%s/vulnerability-alerts" % (owner, repo)
    v_ok, v_phrase, v_kind = _gh_api_include(vuln_path)
    if not v_ok:
        read_failures.append(("alerts check", v_phrase))
        return None, False, True
    if v_kind == "alerts_off":
        return "alerts off", True, False
    alerts_path = "repos/%s/%s/dependabot/alerts?state=open" % (owner, repo)
    a_ok, a_phrase, alerts = _gh_paginate_json(alerts_path)
    if not a_ok:
        read_failures.append(("open alerts list", a_phrase))
        return None, False, True
    return _format_alerts(alerts), False, False


def scan_project(owner, repo, entry, meta, had_entry_before_seed):
    repo_slash = "%s/%s" % (owner, repo)
    prev_last = (entry or {}).get("last_run_read")
    prev_standing = _normalize_standing((entry or {}).get("finding_standing"))
    read_failures = []
    scan_unreadable = False
    ledger_skip = False
    kind = None
    remedy = None
    new_last = prev_last
    new_standing = prev_standing
    last_extract = (meta or {}).get("last_extract")
    wf_path = "repos/%s/%s/actions/workflows" % (owner, repo)
    ok, reason, body = bridge_env._gh_get(wf_path)
    if not ok:
        scan_unreadable = True
        ledger_skip = True
        kind = "finding"
        remedy = read_failure_remedy(False)
        read_failures.append(("workflows list", _api_failure_phrase(reason, body)))
    else:
        wf_err = _validate_workflows_body(body)
        if wf_err:
            scan_unreadable = True
            ledger_skip = True
            kind = "finding"
            remedy = read_failure_remedy(False)
            read_failures.append(("workflows list", wf_err))
        else:
            wf = dependency_workflow(body)
            if wf is None:
                kind = "not configured"
                remedy = "add dependency-scan.yml in the project's calibration"
                new_standing = prev_standing
            elif (wf.get("state") or "") != "active":
                enable = "gh workflow enable dependency-scan.yml --repo %s/%s" % (owner, repo)
                rerun = "gh workflow run dependency-scan.yml --repo %s/%s" % (owner, repo)
                kind = "no completed run"
                remedy = "%s; then %s" % (enable, rerun)
                new_standing = prev_standing
            else:
                day = security_runs_day(entry, meta) or "1970-01-01"
                runs_path = "repos/%s/%s/actions/workflows/dependency-scan.yml/runs?created=>=%s&per_page=100" % (owner, repo, day)
                ok, reason, runs_body = bridge_env._gh_get(runs_path)
                if not ok:
                    scan_unreadable = True
                    ledger_skip = True
                    kind = "finding"
                    remedy = read_failure_remedy(False)
                    read_failures.append(("runs list", _api_failure_phrase(reason, runs_body)))
                elif not isinstance(runs_body, dict):
                    scan_unreadable = True
                    ledger_skip = True
                    kind = "finding"
                    remedy = read_failure_remedy(False)
                    read_failures.append(("runs list", "reply could not be parsed"))
                else:
                    all_runs = runs_body.get("workflow_runs")
                    if all_runs is None:
                        all_runs = []
                    runs_err = _validate_runs_list(all_runs)
                    if runs_err:
                        scan_unreadable = True
                        ledger_skip = True
                        kind = "finding"
                        remedy = read_failure_remedy(False)
                        read_failures.append(("runs list", runs_err))
                    else:
                        window_runs = [r for r in all_runs if run_in_window(r, prev_last, had_entry_before_seed, last_extract)]
                        week_kind, week_remedy, marker_at, advance_last = classify_window_runs(window_runs, owner, repo)
                        completed = _completed_runs(window_runs)
                        if advance_last and completed:
                            new_last = completed[-1].get("created_at")
                        failures = [r for r in window_runs if r.get("status") == "completed" and r.get("conclusion") == "failure"]
                        exit1_id = None
                        for run in failures:
                            code, fail = _run_exit_code(owner, repo, run)
                            if fail:
                                scan_unreadable = True
                                ledger_skip = True
                                kind = "finding"
                                remedy = read_failure_remedy(False)
                                read_failures.append(fail)
                                break
                            if code == 1:
                                exit1_id = _digit_id(run.get("id"))
                        else:
                            if not scan_unreadable:
                                cleared = _standing_cleared(prev_standing, prev_last, window_runs, all_runs)
                                if exit1_id is not None:
                                    new_standing = exit1_id
                                elif cleared:
                                    new_standing = None
                                else:
                                    new_standing = prev_standing
                                if week_kind == "green":
                                    kind = "green"
                                    remedy = week_remedy
                                elif week_kind == "pending_failure":
                                    last = completed[-1]
                                    last_code, fail = _run_exit_code(owner, repo, last)
                                    if fail:
                                        scan_unreadable = True
                                        ledger_skip = True
                                        kind = "finding"
                                        remedy = read_failure_remedy(False)
                                        read_failures.append(fail)
                                    elif last_code == 1:
                                        kind = "finding"
                                        remedy = "Open a DEP-<nnn> increment per the merge policy."
                                    else:
                                        kind = "scanner failure"
                                        remedy = "gh workflow run dependency-scan.yml --repo %s/%s" % (owner, repo)
                                else:
                                    kind = week_kind
                                    remedy = week_remedy
                                if week_kind == "no completed run" and new_standing is not None and not any(
                                    r.get("status") in ("queued", "in_progress", "waiting") for r in window_runs
                                ):
                                    kind = "finding"
                                    remedy = "Open a DEP-<nnn> increment per the merge policy."
    alerts_line, alerts_off, alerts_failed = _read_alerts(owner, repo, read_failures)
    if alerts_failed:
        remedy = read_failure_remedy(True)
    scan_success = kind == "green" and alerts_failed
    if scan_success:
        kind = "finding"
    info = {
        "kind": kind or "finding",
        "remedy": remedy,
        "repo": repo_slash,
        "last_run_read": new_last,
        "standing": new_standing,
        "alerts_line": alerts_line,
        "alerts_off": alerts_off,
        "read_failures": read_failures,
        "scan_unreadable": scan_unreadable,
        "scan_success": scan_success,
        "alerts_failed": alerts_failed,
    }
    if ledger_skip:
        update = None
    else:
        update = {"last_run_read": new_last, "finding_standing": new_standing}
    return info, update


def project_security_section(name, root, entry, meta, had_entry):
    pair = git_origin_repo(root)
    if not pair:
        prev = (entry or {}).get("last_run_read")
        stand = _normalize_standing((entry or {}).get("finding_standing"))
        return format_security_section(name, {
            "kind": "no remote",
            "remedy": "record a GitHub origin on the Workspace checkout",
            "last_run_read": prev,
            "standing": stand,
        }), {"last_run_read": prev, "finding_standing": stand}
    info, update = scan_project(pair[0], pair[1], entry, meta, had_entry)
    return format_security_section(name, info), update


def format_security_section(project, info):
    lines = ["## %s" % ascii_line(project), ""]
    kind = info.get("kind") or "finding"
    lines.append(ascii_line(kind))
    if info.get("scan_success"):
        lines.append(ascii_line("scan: the last completed run ended success"))
    if info.get("scan_unreadable"):
        lines.append("the scan could not be read")
    for read_name, phrase in info.get("read_failures") or []:
        lines.append("read failed: the %s, %s" % (read_name, phrase))
    if info.get("remedy"):
        lines.append("Remedy: %s" % ascii_line(info["remedy"]))
    if info.get("repo"):
        lines.append("Repository: %s" % ascii_line(info["repo"]))
    lrr = info.get("last_run_read")
    lines.append("last run read: %s" % (ascii_line(lrr) if lrr else "none"))
    stand = info.get("standing")
    if stand is not None:
        lines.append("finding standing: run %s" % ascii_line(str(stand)))
    if info.get("alerts_off"):
        lines.append("alerts off")
    elif info.get("alerts_line"):
        lines.append(ascii_line(info["alerts_line"]))
    lines.append("")
    return "\n".join(lines)


def parse_seed_security(path):
    try:
        text = read(path)
    except OSError:
        raise
    out = {}
    for line in text.splitlines():
        if "`" not in line or "last run read:" not in line:
            continue
        repos = re.findall(r"`([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)`", line)
        if not repos:
            continue
        m = re.search(r"`last run read:\s*([^`]+)`", line)
        if not m:
            continue
        token = m.group(1).strip()
        if token.lower() == "none":
            out[repos[0]] = None
        else:
            if not parse_utc(token):
                continue
            out[repos[0]] = token
    return out


def cmd_collect(a):
    root = bridge_root()
    projects, err = resolve_projects(a)
    if err:
        print("evaluate-reports: %s" % err)
        return 2
    ledger_path = a.ledger or os.path.join(root, "Reports", "ledger.json")
    ledger = load_ledger(ledger_path)
    report = []
    entries = collect_entries(projects, a.home, report)
    for line in report:
        print("evaluate-reports: " + line)
    rows = [r + (row_tag(r[1], r[5]),) for r in unprocessed(entries, ledger)]
    for project, source, eid, label, body, earlier, tag in rows:
        if tag.startswith("WRITTEN"):                                       # its fingerprint is taken now: a later change is an update
            earlier.update({"fingerprint": fingerprint(body), "written": today()})
    ledger.setdefault("_meta", {})["last_collect"] = today()                  # never drops last_extract (third pass, finding 1)
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
        for project, source, eid, label, body, earlier, tag in rows:
            shown = redact(body.strip())
            if len(shown) > 6000:
                shown = shown[:6000] + "\n\n[cut at 6,000 characters; the document holds the rest]"
            f.write("## %s / %s / %s - %s\n\n%s\n\n%s\n\n" % (project, source, eid, tag, label, shown))
    counts = dict((k, sum(1 for r in rows if r[6].startswith(k))) for k in ("NEW", "UPDATED", "WRITTEN", "TO WRITE"))
    more = "".join(", %d %s" % (counts[k], w) for k, w in (("WRITTEN", "written after a forced verdict"), ("TO WRITE", "to write")) if counts[k])
    print("evaluate-reports: %d entries to evaluate (%d new, %d updated%s) -> %s" % (
        len(rows), counts["NEW"], counts["UPDATED"], more, path))
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
    projects, err = resolve_projects(a)
    if err:
        print("evaluate-reports: %s" % err)
        return 2
    ledger = load_ledger(ledger_path)
    entries = collect_entries(projects, a.home)
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
    projects, err = resolve_projects(a)
    if err:
        print("evaluate-reports: %s" % err)
        return 2
    ledger_path = a.ledger or os.path.join(root, "Reports", "ledger.json")
    ledger = load_ledger(ledger_path)
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
            for span in re.findall(r"[Mm]emory\s+([^;|]*)", src):                                  # the TDP: memory `ci-config-gotchas` item 17, `tdp-mcp-claude-code-wiring`
                notes |= set("note:%s.md" % n for n in re.findall(r"`([\w-]+)`", span))
            headline = bool(re.search(r"\bIssues?\s+headline\b", src, re.I))                    # the video factory: Issues headline + Issues 1-4
            quoted = [q.lower() for q in re.findall(r'Feedback\s+"([^"]+)"', src)]              # the TDP: Feedback "Milestone 5 close"
            fb = re.findall(r"Feedback Stage (\w+),\s*([^;()|]+)", src)                           # reAngle: Feedback Stage 3a, Stalls item 1
            for source, e, label, body in rows:
                hit = e.upper() in wanted or e in notes or (headline and source == "issues" and "headline" in label.lower())
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
def session_files(project_root, home=None, project=None):
    out = []
    for key in project_keys(project, project_root):
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
    dated = sorted(d for d in os.listdir(folder) if DATE_RX.match(d) and d < today() and run_files(os.path.join(folder, d))) if os.path.isdir(folder) else []
    return dated[-1] if dated else "2026-10-04"           # never today's folder (collect has just made it) nor one without a run's files


def run_files(folder):
    """A folder of a run of this command holds unprocessed.md or owner-messages-*.md; the first evaluation's tables and other notes do not count."""
    return any(n == "unprocessed.md" or n.startswith("owner-messages-") for n in os.listdir(folder))


def cmd_extract(a):
    root = bridge_root()
    ledger_path = a.ledger or os.path.join(root, "Reports", "ledger.json")
    since = a.since or last_run(root, ledger_path)
    out_dir = a.out or os.path.join(root, "Reports", "Evaluations", today())
    projects, err = resolve_projects(a)
    if err:
        print("evaluate-reports: %s" % err)
        return 2
    os.makedirs(out_dir, exist_ok=True)
    total = 0
    for project, proot in projects.items():
        rows, seen = [], set()
        for path in session_files(proot, a.home, project):
            rows += owner_messages(path, since, seen)
        rows.sort()
        if not rows:
            continue
        total += len(rows)
        with open(os.path.join(out_dir, "owner-messages-%s.md" % project.replace(" ", "-")), "w", encoding="utf-8") as f:
            f.write("# The owner's messages and answers, %s, since %s\n\nTimes are UTC (the session records' own timestamps).\n\nFilters: only records the app marks as the owner's own typing and the question-form answers; compaction summaries, app-inserted text, notifications and other sessions' messages left out; each record once; every session folder the project was opened in; key values and key-shaped tokens withheld.\n\n" % (project, since))
            for ts, kind, text in rows:
                f.write("- %s [%s] %s\n" % (ts[:16].replace("T", " "), kind, redact(text).replace("\n", " / ")[:1200]))
    ledger = load_ledger(ledger_path)
    ledger.setdefault("_meta", {})["last_extract"] = today()
    save_ledger(ledger_path, ledger)
    print("evaluate-reports: %d message(s) and answer(s) extracted since %s -> %s" % (total, since, out_dir))
    return 0


def cmd_security(a):
    root = bridge_root()
    eval_date = today()
    if a.date:
        if not DATE_RX.match(a.date):
            print("evaluate-reports: --date must be YYYY-MM-DD")
            return 2
        try:
            eval_date = datetime.date.fromisoformat(a.date).isoformat()
        except ValueError:
            print("evaluate-reports: --date must be YYYY-MM-DD")
            return 2
    projects, err = resolve_projects(a)
    if err:
        print("evaluate-reports: %s" % err)
        return 2
    if a.seed_from:
        try:
            open(a.seed_from, encoding="utf-8").close()
        except OSError:
            print("evaluate-reports: cannot read --seed-from file %s" % a.seed_from)
            return 2
    ledger_path = os.path.join(root, "Reports", "ledger.json")
    ledger = load_ledger(ledger_path)
    meta = ledger.setdefault("_meta", {})
    security_meta = dict(meta.get("security") or {})
    seed_by_repo = {}
    if a.seed_from:
        try:
            seed_by_repo = parse_seed_security(a.seed_from)
        except OSError:
            print("evaluate-reports: cannot read --seed-from file %s" % a.seed_from)
            return 2
    repo_map = {}
    for project, proot in projects.items():
        pair = git_origin_repo(proot)
        if pair:
            repo_map["%s/%s" % pair] = project
    orig_security = dict(security_meta)
    seeded_now = set()
    for repo_slash, last in seed_by_repo.items():
        project = repo_map.get(repo_slash)
        if project and project not in security_meta:
            security_meta[project] = {"last_run_read": last, "finding_standing": None}
            seeded_now.add(project)
    sections = []
    updates = {}
    for project in sorted(projects):
        proot = projects[project]
        had_entry = project in orig_security or project in seeded_now
        entry = security_meta.get(project) or {}
        text, update = project_security_section(project, proot, entry, meta, had_entry)
        sections.append(text)
        if update is not None:
            updates[project] = update
    body = "# Dependency scan, %s\n\n" % eval_date + "".join(sections)
    out_dir = os.path.join(root, "Reports", "Evaluations", eval_date)
    path = os.path.join(out_dir, "security.md")
    if os.path.isfile(out_dir):
        print("evaluate-reports: a file could not be read or written (not a directory)")
        return 1
    try:
        os.makedirs(out_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
    except OSError as e:
        print("evaluate-reports: a file could not be read or written (%s)" % e)
        return 1
    for project, upd in updates.items():
        security_meta[project] = upd
    meta["security"] = security_meta
    save_ledger(ledger_path, ledger)
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    for name in ("collect", "record", "seed", "extract"):
        p = sub.add_parser(name)
        p.add_argument("--ledger")
        p.add_argument("--project-root", help="one project root instead of the project list (tests, a hand collect)")
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
    ps = sub.add_parser("security")
    ps.add_argument("--date", help="evaluation date YYYY-MM-DD (default today)")
    ps.add_argument("--seed-from", help="hand-written evaluation file to seed the window")
    return ap


def main():
    ap = build_parser()
    a = ap.parse_args()
    if not a.cmd:
        ap.print_usage()
        return 2
    try:
        return {"collect": cmd_collect, "record": cmd_record, "seed": cmd_seed, "extract": cmd_extract,
                "security": cmd_security}[a.cmd](a)
    except OSError as e:
        print("evaluate-reports: a file could not be read or written (%s)" % e)
        return 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
