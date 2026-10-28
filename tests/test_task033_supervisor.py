"""Supervisor's acceptance tests for TASK-033 (R-044); written by the supervisor; the builder reads and runs them,
never edits them.

R-044: the report cycle has a pace section for every project, computed by `pace-report.py`, read-only, from git and
the launcher's and the guard's own records; the pace report and the plan check read a squash subject by one rule, one
copy in `bridge_env.py`, under which a closing parenthesis merges an increment only when each of its comma-separated
items is a bare ID (ISS-013). The brief is handoff/TASK-033.md; the plan clauses are docs/BUILD_PLAN.md TASK-033 (a) to
(c).

How the tests reach the programs:
- the subject reader through `plan-check.py`'s module-level `merged_ids(base)` (loaded by path, the current folder a
  fixture repository) and through `bridge_env.squash_merged_ids(folder, pattern)`'s two-argument call, under the plan's
  pattern and the grammar's;
- `pace-report.py` as a user runs it, `python bridge/cursor-bridge/pace-report.py <root>... [options]`, on project
  roots built in the test (a folder holding Workspace/ with its own git repository; commits dated with
  GIT_AUTHOR_DATE / GIT_COMMITTER_DATE; GIT_CONFIG_GLOBAL and GIT_CONFIG_SYSTEM set to os.devnull);
- three cases the brief says cannot be produced from outside without waiting 120 seconds (a git command at its limit,
  the limit itself, a timed-out session read) run the program's main() in this process, with only the standard
  library's subprocess.Popen (or a module-level 120-second number, which is what "a monkeypatched limit" names)
  changed; no internal name of pace-report.py is used.

Weeks are computed from the clock when the module is imported: events are placed k weeks before the current UTC ISO
week, never in the current week (no future dates). A run that straddles Monday 00:00 UTC may misplace a week.
"""
import ast
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, os.pardir))
CB = os.path.join(WORKSPACE, "bridge", "cursor-bridge")
PACE = os.path.join(CB, "pace-report.py")
PLAN_CHECK = os.path.join(CB, "plan-check.py")
BRIDGE_ENV = os.path.join(CB, "bridge_env.py")
TIMEOUT = 300

PLAN_PATTERN = r"TASK-\d{3,}[a-z]?"
GRAMMAR_PATTERN = r"[A-Z][A-Za-z0-9-]*"
ISS013 = "BUG-018: stage B3's review round 2's fixes (pointers, TASK-031's Scope, survival lists, records) (#61)"
ISS013_FORM = "docs: fixes (pointers, TASK-031's Scope, survival lists, records) (#61)"
UNTRACKED = "n/a (handoff/ untracked)"
FOUR_FIELDS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
LIFT_WORDS = ("class", "owner", "none", "unknown")
UTC = datetime.timezone.utc

NOW = datetime.datetime.now(UTC)
MONDAY0 = datetime.datetime.combine(NOW.date() - datetime.timedelta(days=NOW.weekday()), datetime.time(0, 0),
                                    tzinfo=UTC)


# ---------------------------------------------------------------- dates and weeks


def at(k, day=2, hour=12, minute=0, second=0):
    """A UTC time k weeks before the current ISO week: day 0 is Monday; noon unless given."""
    return MONDAY0 - datetime.timedelta(weeks=k) + datetime.timedelta(days=day, hours=hour, minutes=minute,
                                                                       seconds=second)


def week(k):
    """(ISO year, ISO week) of the week k weeks before the current UTC ISO week."""
    y, w, _ = (MONDAY0 - datetime.timedelta(weeks=k)).date().isocalendar()
    return (y, w)


def gitdate(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+0000")


def run_id(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def transcript_ts(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ---------------------------------------------------------------- git and fixture projects


def git_env(home=None):
    env = dict(os.environ)
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0",
               GIT_AUTHOR_NAME="Supervisor Fixture", GIT_AUTHOR_EMAIL="supervisor@example.invalid",
               GIT_COMMITTER_NAME="Supervisor Fixture", GIT_COMMITTER_EMAIL="supervisor@example.invalid")
    if home is not None:                      # a module-scoped fixture runs before conftest's temporary HOME is set
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
    return env


def git(folder, *args, **kw):
    env = git_env(kw.get("home"))
    env.update(kw.get("extra") or {})
    p = subprocess.run(["git", "-C", str(folder)] + list(args), env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=TIMEOUT)
    assert p.returncode == 0, "fixture git %s failed: %s" % (" ".join(args), p.stderr)
    return p.stdout


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Project(object):
    """A project root built in the test: <root>/Workspace is a git repository on main, run/ ignored."""

    def __init__(self, root, home=None):
        self.root = root
        self.name = root.name
        self.ws = root / "Workspace"
        self.home = home
        self.ws.mkdir(parents=True)
        git(self.ws, "init", "-q", "-b", "main", home=home)
        self.write(".gitignore", "run/\n")

    def write(self, rel, text):
        p = self.ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
        return p

    def brief(self, *names):
        for n in names:
            self.write("handoff/%s.md" % n, "# %s\n\nSatisfies: R-044\n" % n)

    def report(self, *names):
        for n in names:
            self.write("handoff/%s-report.md" % n, "# report %s\n" % n)

    def commit(self, subject, when, body=None, committer=None):
        """A commit on main of everything in the tree (empty allowed), author date `when`, committer date
        `committer` (a datetime, or a raw git date string with its own offset) or `when`."""
        git(self.ws, "add", "-A", home=self.home)
        args = ["commit", "-q", "--allow-empty", "--no-verify", "-m", subject]
        if body:
            args += ["-m", body]
        cdate = committer if isinstance(committer, str) else gitdate(committer or when)
        git(self.ws, *args, home=self.home, extra={"GIT_AUTHOR_DATE": gitdate(when), "GIT_COMMITTER_DATE": cdate})

    def log_line(self, text):
        p = self.ws / "run" / "launcher" / "runs.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(str(p), "a", encoding="utf-8") as f:
            f.write(text + "\n")

    def launch(self, brief, when, rnd=1, lift=None, lift_line=None):
        """A runs.jsonl row in the shape bridge-run.py writes for a builder launch of a brief."""
        name = brief if rnd == 1 else "%s-r%d" % (brief, rnd)
        row = {"id": run_id(when), "kind": "builder", "head": "cursor-agent", "model": "composer-2.5",
               "branch": brief.lower(), "limit": 7200, "seconds": 60, "exit": 0, "healthy": None, "brief": brief,
               "round": rnd, "brief_sha256": sha(name), "brief_name": name, "lift": lift, "merge_ids": [brief],
               "waited": 0, "pid": 4242, "child_pid": 4343}
        if lift_line:
            row["lift_line"] = lift_line
        self.log_line(json.dumps(row))

    def rounds(self, ident, entries):
        """.git/bridge/rounds-<ident>.json in the guard's shape; entries are (time, lift, lift_line)."""
        rounds = []
        for i, (when, lift, line) in enumerate(entries, 1):
            rounds.append({"round": i, "name": ident if i == 1 else "%s-r%d" % (ident, i), "branch": ident.lower(),
                           "tree": "0" * 40, "time": run_id(when) if when else "", "lift": lift, "lift_line": line,
                           "reply": 0})
        p = self.ws / ".git" / "bridge" / ("rounds-%s.json" % ident)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"id": ident, "merge_ids": [ident], "rounds": rounds}, indent=1), encoding="utf-8")

    def err(self, *names):
        for n in names:
            p = self.ws / "run" / "review" / ("REVIEW-%s.err" % n)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("bridge-run: started 2020-01-01T00:00:00Z\nbridge-run: exit 0\n", encoding="utf-8")


class Run(object):
    def __init__(self, rc, raw_out, raw_err):
        self.rc = rc
        self.raw_out = raw_out
        self.raw_err = raw_err
        self.out = raw_out.decode("ascii", "replace")
        self.err = raw_err.decode("ascii", "replace")
        self.both = self.out + "\n" + self.err

    def __repr__(self):
        return "exit %s\n--- stdout\n%s\n--- stderr\n%s" % (self.rc, self.out, self.err)


def pace(args, cwd, timeout=TIMEOUT):
    """`python bridge/cursor-bridge/pace-report.py <args>` from `cwd`, under conftest's temporary HOME."""
    assert os.path.isfile(PACE), "bridge/cursor-bridge/pace-report.py does not exist"
    env = dict(os.environ)
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0",
               PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, PACE] + [str(a) for a in args], cwd=str(cwd), env=env, capture_output=True,
                       timeout=timeout)
    return Run(p.returncode, p.stdout, p.stderr)


# ---------------------------------------------------------------- reading the Markdown output loosely

WEEK_RX = re.compile(r"(?<!\d)(\d{4})\s*-?\s*W\s*(\d{1,2})(?!\d)", re.I)
SEP_RX = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")
NUM_RX = re.compile(r"\d+(?:\.\d+)?")


def cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def section(out, name, others=()):
    """The lines of one project's Markdown section: from the first heading line (`#...`) naming `name` to the
    heading naming the next of `others` (or the end). The heading may hold the base name or the whole path."""
    lines = out.splitlines()

    def head(n):
        for i, line in enumerate(lines):
            if line.lstrip().startswith("#") and n in line:
                return i
        return None

    start = head(name)
    assert start is not None, "no heading names %s in:\n%s" % (name, out)
    ends = [e for e in (head(o) for o in others) if e is not None and e > start]
    return lines[start:min(ends) if ends else len(lines)]


ROLE_PREDICATES = {
    "started": lambda c: "start" in c and not any(x in c for x in ("day", "token", "merg")),
    "merged": lambda c: "merg" in c and not any(x in c for x in ("day", "round", "token", "start")),
    "rounds_mean": lambda c: "round" in c and any(x in c for x in ("mean", "avg", "average")),
    "rounds_max": lambda c: "max" in c and not any(x in c for x in ("day", "token")),
    "days": lambda c: "day" in c,
    "hardening": lambda c: "harden" in c,
    "tokens": lambda c: "token" in c and "merg" not in c,
    "tokens_per_merged": lambda c: "token" in c and "merg" in c,
}


class Report(object):
    """One project's section, read loosely.

    The table is the first Markdown table in the section (a header row followed by a `---` separator row; outer
    pipes optional). A week row is a row whose first cell holds an ISO week label: the brief fixes the rows as ISO
    weeks but not the label's spelling, so `YYYY-Www`, `YYYYWww`, `YYYY Www` and the same followed by more text
    (`2026-W43 (Oct 19)`, `2026-W43-1`) are all accepted, read as (year, week). The total row is the row whose first
    cell says "total" (any case). Columns are found by words in their header cell, the brief fixing what each column
    holds but not its header text: started ("start", not "day"/"token"/"merg"), merged ("merg", not "day"/"round"/
    "token"/"start"), rounds mean ("round" with "mean"/"avg"/"average"), rounds max ("max"; one with "round"
    preferred), days ("day"), HARDENING lines ("harden"), tokens ("token" without "merg") and tokens per merged
    increment ("token" with "merg"). Mean and maximum may share one cell (`4.5 / 5`); their order is then the order
    of "mean" and "max" in the header. Everything after the table is `after`, where the over-ceiling lists stand."""

    def __init__(self, lines):
        self.lines = list(lines)
        self.text = "\n".join(self.lines)
        self.header, rows, end = None, [], len(self.lines)
        for i in range(len(self.lines) - 1):
            if "|" in self.lines[i] and SEP_RX.match(self.lines[i + 1]):
                self.header = [c.lower() for c in cells(self.lines[i])]
                j = i + 2
                while j < len(self.lines) and "|" in self.lines[j] and self.lines[j].strip():
                    rows.append(cells(self.lines[j]))
                    j += 1
                end = j
                break
        assert self.header is not None, "no Markdown table in the section:\n%s" % self.text
        self.weeks, self.total = {}, None
        for r in rows:
            m = WEEK_RX.search(r[0])
            if m:
                self.weeks[(int(m.group(1)), int(m.group(2)))] = r
            elif self.total is None and re.search(r"total", r[0], re.I):
                self.total = r
        self.after = "\n".join(self.lines[end:])

    def index(self, role):
        found = [i for i, c in enumerate(self.header) if i > 0 and ROLE_PREDICATES[role](c)]
        if role == "rounds_max" and len(found) > 1:
            found = [i for i in found if "round" in self.header[i]] or found
        if role == "rounds_mean" and not found:
            found = [i for i, c in enumerate(self.header) if i > 0 and "round" in c and "max" not in c]
        assert len(found) == 1, "cannot tell the %s column among the headers %s" % (role, self.header)
        return found[0]

    def row(self, k):
        key = week(k)
        assert key in self.weeks, "no row for ISO week %d-W%02d; week rows: %s\n%s" % (
            key[0], key[1], sorted(self.weeks), self.text)
        return self.weeks[key]

    def cell(self, row, role):
        i = self.index(role)
        return row[i] if i < len(row) else ""

    def number(self, row, role):
        """The cell's value (None when it holds no number); for the rounds mean and max, the right half of a
        shared cell."""
        if role in ("rounds_mean", "rounds_max"):
            mi, xi = self.index("rounds_mean"), self.index("rounds_max")
            if mi == xi:
                nums = [float(n) for n in NUM_RX.findall(row[mi] if mi < len(row) else "")]
                if not nums:
                    return None
                h = self.header[mi]
                mean_first = h.find("max") < 0 or (0 <= h.find("mean") < h.find("max")) or (
                    0 <= h.find("avg") < h.find("max"))
                if len(nums) == 1:
                    return nums[0]
                return nums[0 if (role == "rounds_mean") == mean_first else 1]
        nums = NUM_RX.findall(self.cell(row, role))
        return float(nums[0]) if nums else None

    def at_week(self, k, role):
        return self.number(self.row(k), role)


def id_rx(ident):
    return re.compile(r"(?<![A-Za-z0-9-])%s(?![A-Za-z0-9])" % re.escape(ident))


def blocks(text, ident, known):
    """Each item of `text` that mentions `ident`: from the mention to the end of its line, with the following lines
    indented deeper than that line (sub-bullets, continuations), cut before the next mention of another of `known`.
    So an item on one line, an item with its rounds on indented lines below it, and several items on one line are
    each read as one block. Returns [(offset in text, block)]."""
    others = [id_rx(k) for k in known if k != ident]
    lines = text.split("\n")
    out, offset = [], 0
    for li, line in enumerate(lines):
        for m in id_rx(ident).finditer(line):
            indent = len(line) - len(line.lstrip())
            parts = [line[m.start():]]
            j = li + 1
            while j < len(lines) and lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) > indent:
                parts.append(lines[j])
                j += 1
            chunk = "\n".join(parts)
            end = len(chunk)
            for rx in others:
                o = rx.search(chunk, len(ident))
                if o:
                    end = min(end, o.start())
            out.append((offset + m.start(), chunk[:end]))
        offset += len(line) + 1
    return out


def has_number(block, ident, n):
    rest = id_rx(ident).sub(" ", block)
    return re.search(r"(?<![\w.])%d(?![\d.])" % n, rest) is not None


def listed(rep, ident, rounds, known):
    """The block below the table that lists `ident` with its rounds `rounds` (asserted to exist): (position, text)."""
    found = [b for b in blocks(rep.after, ident, known) if has_number(b[1], ident, rounds)]
    assert found, "%s is not listed below the table with %d rounds:\n%s" % (ident, rounds, rep.after)
    return found[0]


def not_listed(rep, ident, rounds, known):
    """No block below the table gives `ident` with its rounds `rounds`: a mention without them (an unknown-start
    line, say) is not a listing."""
    found = [b for b in blocks(rep.after, ident, known) if has_number(b[1], ident, rounds)]
    assert not found, "%s is listed below the table with %d rounds:\n%s" % (ident, rounds, rep.after)


def words_in(block):
    return {w for w in LIFT_WORDS if re.search(r"\b%s\b" % w, block, re.I)}


# ---------------------------------------------------------------- the subject reader


def subject_repo(tmp_path, subject, body=None):
    repo = tmp_path / "subject-repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    args = ["commit", "-q", "--allow-empty", "--no-verify", "-m", subject]
    if body:
        args += ["-m", body]
    git(repo, *args)
    return repo


def readings(tmp_path, program, monkeypatch, subject, body=None):
    """(plan-check's merged_ids("main"), bridge_env's reader under the plan pattern, under the grammar's) on a
    repository whose main holds the one commit."""
    repo = subject_repo(tmp_path, subject, body)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.chdir(str(repo))
    pc = program("plan-check").merged_ids("main")
    be = program("bridge_env")
    plan = be.squash_merged_ids(str(repo), PLAN_PATTERN)
    grammar = be.squash_merged_ids(str(repo), GRAMMAR_PATTERN)
    assert pc is not None and plan is not None and grammar is not None, (pc, plan, grammar)
    return set(pc), set(plan), set(grammar)


# plan-check.py's reading before TASK-033 (its four forms and loop, copied here only to state "unchanged").
F_ID = r"TASK-\d{3,}[a-z]?"
F_SUBJECT = re.compile(r"^\s*((?:%s[\s,:]*)+)" % F_ID)
F_TRAIL = re.compile(r"\(([^()]*%s[^()]*)\)\s*(?:[-\u2014\u2013]\s*v?[\w.]+\s*)?(?:\(#\d+\))?\s*$" % F_ID)
F_MERGE = re.compile(r"^\s*Merge (?:pull request #\d+ from \S+?/|branch ')(task-\d{3,}[a-z]?)\b", re.I)
F_ID_RX = re.compile(F_ID)


def former_reading(repo):
    out = set()
    log = git(repo, "log", "main", "--format=%s%n%(trailers:key=Merges,valueonly)")
    for line in log.splitlines():
        m = F_SUBJECT.match(line)
        if m:
            out.update(F_ID_RX.findall(m.group(1)))
            continue
        m = F_MERGE.match(line)
        if m:
            out.add("TASK-" + m.group(1)[5:])
            continue
        m = F_TRAIL.search(line)
        if m:
            out.update(F_ID_RX.findall(m.group(1)))
            continue
        if re.match(r"^\s*(%s)(\s*,\s*%s)*\s*$" % (F_ID, F_ID), line):
            out.update(F_ID_RX.findall(line))
    return out


def test_task033_bare_id_parenthesis_merges_its_increment(tmp_path, program, monkeypatch):
    """R-044. Clause (a): `(TASK-100, R-027)` merges TASK-100; R-nnn is a bare item that merges nothing under the plan
    pattern. enforces: docs/BUILD_PLAN.md TASK-033 (a); handoff/TASK-033.md Requirement 1."""
    pc, plan, grammar = readings(tmp_path, program, monkeypatch, "feat(x): thing (TASK-100, R-027) (#7)")
    assert pc == {"TASK-100"}
    assert plan == {"TASK-100"}
    assert "TASK-100" in grammar


@pytest.mark.parametrize("subject", [
    "docs: x (pointers, TASK-031's Scope, survival lists, records) (#61)",
    "docs: x (TASK-031's Scope)",
    "docs: x (TASK-031's Scope) (#9)",
    "docs: x (TASK-100, the fixes) (#9)",
])
def test_task033_parenthesis_with_a_non_id_item_merges_nothing(tmp_path, program, monkeypatch, subject):
    """R-044. Clause (a): a closing parenthesis holding any item that is not a bare ID merges nothing, in
    plan-check.py and in bridge_env's reader under either pattern (ISS-013).
    enforces: docs/BUILD_PLAN.md TASK-033 (a); handoff/TASK-033.md Requirement 1."""
    pc, plan, grammar = readings(tmp_path, program, monkeypatch, subject)
    assert pc == set()
    assert plan == set()
    assert grammar == set()


@pytest.mark.parametrize("subject", [
    "docs: spaced ( TASK-100 ,  TASK-101 ) (#3)",
    "docs: tight (TASK-100,TASK-101) (#3)",
    "docs: release (TASK-100, TASK-101) - v0.2.0 (#3)",
])
def test_task033_parenthesis_items_may_have_spaces_around_them(tmp_path, program, monkeypatch, subject):
    """R-044. Clause (a): spaces around each comma-separated item are allowed; every bare ID merges.
    enforces: docs/BUILD_PLAN.md TASK-033 (a) ("spaces around each allowed")."""
    pc, plan, grammar = readings(tmp_path, program, monkeypatch, subject)
    assert pc == {"TASK-100", "TASK-101"}
    assert plan == {"TASK-100", "TASK-101"}
    assert {"TASK-100", "TASK-101"} <= grammar


def test_task033_iss013_subject_merges_nothing_under_the_plan_pattern(tmp_path, program, monkeypatch):
    """R-044. 9f6ace6's exact subject merges nothing under the plan pattern, in plan-check.py and bridge_env.
    enforces: handoff/TASK-033.md Context, "The ISS-013 subject"; docs/BUILD_PLAN.md TASK-033 (a)."""
    pc, plan, _ = readings(tmp_path, program, monkeypatch, ISS013)
    assert pc == set()
    assert plan == set()


def test_task033_iss013_subject_merges_bug018_not_task031_under_the_grammar(tmp_path, program, monkeypatch):
    """R-044. Under the grammar's pattern 9f6ace6's subject merges BUG-018 by its leading ID and not TASK-031.
    enforces: handoff/TASK-033.md Context, "The ISS-013 subject"."""
    _, _, grammar = readings(tmp_path, program, monkeypatch, ISS013)
    assert "BUG-018" in grammar
    assert "TASK-031" not in grammar


@pytest.mark.parametrize("subject,expected", [
    ("Merge pull request #1 from x/feat/task-005", {"TASK-005"}),
    ("Merge pull request #9 from x/feature-z (TASK-100)", {"TASK-100"}),
    ("Merge pull request #1 from x/task-001ab", set()),
])
def test_task033_the_three_divergences_read_as_plan_check_did(tmp_path, program, monkeypatch, subject, expected):
    """R-044. The three divergences the reality check found: under the plan pattern the one reader gives plan-check's
    former answer. enforces: handoff/TASK-033.md Context, "Divergences the reality check found"; Requirement 2."""
    pc, plan, _ = readings(tmp_path, program, monkeypatch, subject)
    assert former_reading(tmp_path / "subject-repo") == expected      # the copy of the former rule agrees
    assert pc == expected
    assert plan == expected


@pytest.mark.parametrize("subject", ["Fix TASK-001 typo", "Revert TASK-001: x", "Plan: TASK-033 x"])
def test_task033_n4_an_id_after_a_leading_word_merges_nothing(tmp_path, program, monkeypatch, subject):
    """R-044. N4: the subject form reads IDs only at the subject's start, under either pattern.
    enforces: handoff/TASK-033.md Context, "HARDENING's TASK-032 leads that this increment takes" (N4)."""
    pc, plan, grammar = readings(tmp_path, program, monkeypatch, subject)
    assert pc == set()
    assert plan == set()
    assert grammar == set()


def test_task033_n4_two_leading_ids_merge_both(tmp_path, program, monkeypatch):
    """R-044. N4: `TASK-002 TASK-003: two (#2)` merges both, under either pattern.
    enforces: handoff/TASK-033.md Context (N4)."""
    pc, plan, grammar = readings(tmp_path, program, monkeypatch, "TASK-002 TASK-003: two (#2)")
    assert pc == {"TASK-002", "TASK-003"}
    assert plan == {"TASK-002", "TASK-003"}
    assert grammar == {"TASK-002", "TASK-003"}


def test_task033_n4_a_leading_bug_id_merges_under_the_grammar(tmp_path, program, monkeypatch):
    """R-044. N4: `BUG-018: x (#61)` merges BUG-018 under the grammar's pattern.
    enforces: handoff/TASK-033.md Context (N4)."""
    _, plan, grammar = readings(tmp_path, program, monkeypatch, "BUG-018: x (#61)")
    assert grammar == {"BUG-018"}
    assert plan == set()


def test_task033_trailer_form_unchanged(tmp_path, program, monkeypatch):
    """R-044. Clause (a): the `Merges:` trailer form is unchanged, under either pattern.
    enforces: docs/BUILD_PLAN.md TASK-033 (a) ("the other three forms unchanged")."""
    pc, plan, grammar = readings(tmp_path, program, monkeypatch, "chore: a unit (#8)", "Merges: TASK-007, TASK-008")
    assert pc == {"TASK-007", "TASK-008"}
    assert plan == {"TASK-007", "TASK-008"}
    assert grammar == {"TASK-007", "TASK-008"}


def test_task033_grammar_merge_line_keeps_case_ignored_and_letter(tmp_path, program, monkeypatch):
    """R-044. Under the grammar's pattern the Merge form still reads `config-b3b` as CONFIG-B3b's ID (case ignored,
    the letter kept), and `Plan the next stage` merges nothing.
    enforces: handoff/TASK-033.md Context ("Every behaviour the TASK-032 tests pin under the grammar's pattern stays")."""
    _, _, grammar = readings(tmp_path, program, monkeypatch, "Merge pull request #7 from x/config-b3b")
    upper = {g.upper() for g in grammar}
    assert "CONFIG-B3B" in upper and "CONFIG-B3" not in upper


def test_task033_grammar_plan_word_merges_nothing(tmp_path, program, monkeypatch):
    """R-044. `Plan the next stage` merges nothing under either pattern (pinned by TASK-032).
    enforces: handoff/TASK-033.md Context, Requirement 2."""
    pc, plan, grammar = readings(tmp_path, program, monkeypatch, "Plan the next stage")
    assert pc == set() and plan == set() and grammar == set()


PARITY = [
    ("TASK-001: one (#1)", None),
    ("TASK-002 TASK-003: two (#2)", None),
    ("TASK-011a: lettered (#11)", None),
    ("Merge pull request #4 from x/task-004b", None),
    ("Merge branch 'task-005'", None),
    ("Merge pull request #12 from x/TASK-012", None),
    ("Merge pull request #14 from x/task-014-retry", None),
    ("Merge pull request #9 from x/feature-z", None),
    ("feat(x): thing (TASK-006, R-027) - v0.2.0 (#7)", None),
    ("feat: pair (TASK-020,TASK-021) (#4)", None),
    ("chore: a unit (#8)", "Merges: TASK-007, TASK-008"),
    ("docs: plan split TASK-003 out of TASK-004", None),
    ("docs: nothing (#10)", None),
    ("Plan the next stage", None),
]


@pytest.mark.parametrize("subject,body", PARITY)
def test_task033_plan_pattern_reading_equals_the_former_rule(tmp_path, program, monkeypatch, subject, body):
    """R-044. Under the plan pattern the one reader returns what plan-check.py's former merged_ids returned, for every
    subject without a non-ID item in its closing parenthesis.
    enforces: handoff/TASK-033.md Requirement 2; docs/BUILD_PLAN.md TASK-033 (a) ("the other three forms unchanged")."""
    pc, plan, _ = readings(tmp_path, program, monkeypatch, subject, body)
    expected = former_reading(tmp_path / "subject-repo")
    assert pc == expected
    assert plan == expected


def test_task033_reader_takes_a_compiled_pattern_too(tmp_path, program, monkeypatch):
    """R-044. bridge_env.squash_merged_ids(folder, pattern)'s two-argument call keeps working with a compiled pattern.
    enforces: handoff/TASK-033.md Context ("The two-argument call of squash_merged_ids must keep working")."""
    repo = subject_repo(tmp_path, "feat: x (TASK-100, R-027) (#1)")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    got = program("bridge_env").squash_merged_ids(str(repo), re.compile(PLAN_PATTERN))
    assert set(got) == {"TASK-100"}


def read_source(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize("path", [PLAN_CHECK, PACE])
def test_task033_no_program_keeps_a_copy_of_the_four_forms(path):
    """R-044. plan-check.py and pace-report.py hold no SUBJECT_RX, TRAIL_RX, MERGE_RX or trailer regex of their own;
    both import bridge_env. enforces: handoff/TASK-033.md Requirement 1; Acceptance criteria ("plan-check.py holds no
    copy of the four forms")."""
    assert os.path.isfile(path), "%s does not exist" % path
    src = read_source(path)
    for name in ("SUBJECT_RX", "TRAIL_RX", "MERGE_RX"):
        assert not re.search(r"^\s*%s\s*=" % name, src, re.M), "%s defines %s" % (os.path.basename(path), name)
    assert "Merge (?:pull request" not in src
    assert r"(\s*,\s*%s)*" not in src
    assert re.search(r"^\s*(?:import bridge_env|from bridge_env import)", src, re.M), "does not import bridge_env"


def test_task033_pace_report_uses_review_rounds_and_stays_ascii():
    """R-044. pace-report.py imports bridge_env's REVIEW_ROUNDS (the ceiling's default) and, like bridge_env.py, is
    ASCII. enforces: handoff/TASK-033.md Acceptance criteria ("pace-report.py imports it and bridge_env.REVIEW_ROUNDS");
    Requirement 8."""
    assert os.path.isfile(PACE), "bridge/cursor-bridge/pace-report.py does not exist"
    src = read_source(PACE)
    assert "REVIEW_ROUNDS" in src
    for path in (PACE, BRIDGE_ENV):
        with open(path, "rb") as f:
            data = f.read()
        assert all(b < 128 for b in data), "%s holds a non-ASCII byte" % os.path.basename(path)


def test_task033_plan_check_docstring_states_the_narrowed_rule(program):
    """R-044. plan-check.py's docstring states the narrowed parenthesis rule, `(TASK-100, R-027)` merging and
    `(TASK-031's Scope)` merging nothing. enforces: handoff/TASK-033.md Requirement 3; docs/BUILD_PLAN.md TASK-033 (a)
    ("the docstring saying so")."""
    doc = program("plan-check").__doc__ or ""
    assert "(TASK-100, R-027)" in doc
    assert "(TASK-031's Scope)" in doc


PLAN = """# Build plan

## Stage A

Demonstration: the fixture shows nothing.

### TASK-100: the first

Kind: increment
Parent: none
Depends on: none
Parallel: no
Satisfies: R-027
Diagrams: none
Scope: src/a.py

### TASK-031: the second

Kind: increment
Parent: none
Depends on: TASK-100
Parallel: no
Satisfies: R-028
Diagrams: none
Scope: src/b.py
"""


def test_task033_plan_check_command_reads_the_iss013_form_as_unmerged(tmp_path):
    """R-044. `python plan-check.py --base main` on a Workspace whose main holds `(TASK-100, R-027)` and the ISS-013
    form counts one merged increment and reports TASK-031 ready; its exit code is unchanged (0).
    enforces: docs/BUILD_PLAN.md TASK-033 (a); handoff/TASK-033.md Requirement 3 ("--base, the report lines and the exit
    codes are unchanged")."""
    repo = tmp_path / "ws"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "docs").mkdir()
    (repo / "docs" / "BUILD_PLAN.md").write_text(PLAN, encoding="ascii")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--no-verify", "-m", "plan: the fixture's plan")
    git(repo, "commit", "-q", "--allow-empty", "--no-verify", "-m", "feat(x): first (TASK-100, R-027) (#1)")
    git(repo, "commit", "-q", "--allow-empty", "--no-verify", "-m", ISS013_FORM)
    p = subprocess.run([sys.executable, PLAN_CHECK, "--base", "main", "--briefs", "no-briefs"], cwd=str(repo),
                       env=git_env(), capture_output=True, text=True, encoding="ascii", errors="replace",
                       timeout=TIMEOUT)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "Traceback" not in p.stderr
    assert "2 increments in 1 file(s); 1 merged" in p.stdout, p.stdout
    assert re.search(r"^READY: TASK-031\b", p.stdout, re.M), p.stdout


# ---------------------------------------------------------------- the known history (clause (c))

KNOWN = ("TASK-101", "TASK-102", "TASK-103", "TASK-104", "TASK-105", "STAGE-B3", "TASK-900", "TASK-901", "B3-RECORDS")
CLASS_LINE = "Blocking class: behaviour - the fixture's finding"
OWNER_LINE = "Review rounds above the ceiling: TASK-102 5 (the owner's words, 2026-10-01)"


class Fixture(object):
    def __init__(self, project):
        self.project = project
        self.cache = {}

    def run(self, *args):
        """pace-report.py on this root with `args`, run once per argument list (each run inside a test)."""
        key = tuple(str(a) for a in args)
        if key not in self.cache:
            self.cache[key] = pace([self.project.root] + list(args), cwd=self.project.root.parent)
        return self.cache[key]

    def report(self, *args):
        r = self.run(*args)
        assert r.rc == 0, r
        return Report(section(r.out, self.project.name))


@pytest.fixture(scope="module")
def known(tmp_path_factory):
    """The known history: started, merged, rounds, days and HARDENING lines in set weeks (k weeks back).

    starts: TASK-104 launcher k6 (guard k5), TASK-101 launcher k5, TASK-102 guard k4, TASK-103 guard k4 (launcher k3),
            TASK-105 unknown, STAGE-B3 and B3-RECORDS records at k7 (no brief: no start).
    merges: k4 TASK-101 `(TASK-101, R-044)`; k2 TASK-102 by trailer and TASK-105 by subject; k1 `TASK-103 TASK-104:`;
            TASK-900 (no brief) k6 and TASK-901 (a report, no brief) k7 count nothing.
    rounds: TASK-101 3 (three builder reports), TASK-102 5 (guard record over reports r1, r2a), TASK-103 2,
            TASK-104 3 (r1 and the letter sub-round r3a), TASK-105 4 (four .err files over one report),
            STAGE-B3 4 (guard record).
    lifts:  TASK-102 r4 class, r5 owner; TASK-105 r4 unknown (no record); STAGE-B3 r4 none.
    HARDENING.md: +5 at k3, +2 (1 removed) at k1."""
    base = tmp_path_factory.mktemp("known")
    home = tmp_path_factory.mktemp("git-home")
    p = Project(base / "proj-known-q7", home=home)
    p.brief("TASK-101", "TASK-101-r2", "TASK-102", "TASK-103", "TASK-104", "TASK-105")
    p.report("TASK-101-r1", "TASK-101-r2", "TASK-101-r3", "TASK-102-r1", "TASK-102-r2a", "TASK-103-r1", "TASK-103-r2",
             "TASK-104-r1", "TASK-104-r3a", "TASK-105-r1", "TASK-901-r1")
    p.write("docs/README.md", "fixture \u00e9\n")
    p.commit("records: briefs and reports", at(10, 0))
    p.commit("TASK-901: report only, no brief (#11)", at(7, 3))
    p.commit("docs: caf\u00e9 notes \u2014 nothing merges (#12)", at(7, 4))
    p.commit("TASK-900: no brief (#10)", at(6, 3))
    p.commit("feat(core): first increment (TASK-101, R-044) (#1)", at(4, 2))
    p.write("docs/HARDENING.md", "".join("- lead %d\n" % i for i in range(1, 6)))
    p.commit("docs: hardening leads (#4)", at(3, 3))
    p.commit("chore: land the unit (#2)", at(2, 2), body="Merges: TASK-102")
    p.commit("TASK-105: unknown start (#5)", at(2, 2, hour=13))
    p.write("docs/HARDENING.md", "".join("- lead %d\n" % i for i in (1, 2, 3, 4, 6, 7)))
    p.commit("TASK-103 TASK-104: the pair (#6)", at(1, 2))
    # the launcher's records
    p.log_line(json.dumps({"id": run_id(at(6, 1)), "kind": "builder", "head": "cursor-agent", "branch": "task-777",
                           "exit": 0}))                                 # before TASK-032: no brief, no lift
    p.log_line("{not json")
    p.launch("TASK-104", at(6, 0))
    p.launch("TASK-101", at(5, 0))
    p.launch("TASK-101", at(5, 3), rnd=2)
    p.launch("TASK-103", at(3, 0))
    p.launch("STAGE-B3", at(7, 2))
    p.launch("B3-RECORDS", at(7, 2, hour=14))
    # the guard's records
    p.rounds("TASK-102", [(at(4, 0), None, None), (at(3, 1), None, None), (at(3, 4), None, None),
                          (at(2, 0), "class", CLASS_LINE), (at(2, 1), "owner", OWNER_LINE)])
    p.rounds("TASK-103", [(at(4, 4), None, None), (at(3, 2), None, None)])
    p.rounds("TASK-104", [(at(5, 2), None, None)])
    p.rounds("STAGE-B3", [(at(7, 2), None, None), (at(7, 3), None, None), (at(7, 4), None, None),
                          (at(7, 5), None, None)])
    p.rounds("B3-RECORDS", [(at(7, 2, hour=15), None, None)])
    p.err("TASK-101", "TASK-102", "TASK-105", "TASK-105-r2", "TASK-105-r3", "TASK-105-r4", "STAGE-B3", "STAGE-B3-r2")
    return Fixture(p)


def test_task033_started_from_the_launchers_record(known):
    """R-044. Clause (b): an increment's start is the week of its first builder launch in runs.jsonl (TASK-101, k5).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) "increments started"; (c) "a start from the launcher's record"."""
    rep = known.report()
    assert rep.at_week(5, "started") == 1


def test_task033_started_from_the_guards_record(known):
    """R-044. Clause (b): an increment with no launcher row starts in the week of its first round in
    rounds-<ID>.json (TASK-102 at k4, with TASK-103). enforces: docs/BUILD_PLAN.md TASK-033 (c) "a start from the
    guard's record"."""
    rep = known.report()
    assert rep.at_week(4, "started") == 2


def test_task033_started_whichever_is_earlier(known):
    """R-044. Clause (b): the start is the earlier of the launcher's first launch and the guard's first round:
    TASK-104 at k6 (not k5), TASK-103 at k4 (not k3).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("whichever is earlier")."""
    rep = known.report()
    assert rep.at_week(6, "started") == 1
    assert rep.at_week(3, "started") == 0


def test_task033_stage_and_records_subject_records_are_no_start(known):
    """R-044. Clause (b): a stage review's record (STAGE-B3) and a records subject's (B3-RECORDS, no brief) are no
    start: k7 starts nothing. enforces: docs/BUILD_PLAN.md TASK-033 (b) ("counted only for an ID that has a brief");
    (c) "a stage review's record counted as no start"."""
    rep = known.report()
    assert rep.at_week(7, "started") == 0


def test_task033_unknown_start_is_printed_and_not_counted(tmp_path):
    """R-044. Clause (b): an increment with a brief, merged, with neither record has an `unknown` start; no week
    counts it as started. enforces: docs/BUILD_PLAN.md TASK-033 (b) (`unknown` where neither record exists);
    (c) "an unknown start"."""
    p = Project(tmp_path / "proj-unknown-q7")
    p.brief("TASK-601")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-601: merged with no record (#1)", at(2, 2))
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "merged") == 1
    assert all(rep.number(row, "started") in (0, None) for row in rep.weeks.values()), rep.text
    assert re.search(r"\bunknown\b", rep.text, re.I), rep.text


def test_task033_merged_by_a_bare_id_parenthesis(known):
    """R-044. Clause (b): `feat(core): first increment (TASK-101, R-044) (#1)` merges TASK-101 in its week (k4).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) "increments merged"; (c) "one merged by ... a bare-ID parenthesis"."""
    rep = known.report()
    assert rep.at_week(4, "merged") == 1


def test_task033_merged_by_a_trailer_and_a_subject(known):
    """R-044. Clause (b): the `Merges: TASK-102` trailer and `TASK-105: ...` merge in their week (k2), and
    `TASK-103 TASK-104: ...` merges both at k1. enforces: docs/BUILD_PLAN.md TASK-033 (b); (c) "one merged by a
    trailer"."""
    rep = known.report()
    assert rep.at_week(2, "merged") == 2
    assert rep.at_week(1, "merged") == 2


def test_task033_an_id_without_a_brief_is_never_merged(known):
    """R-044. Clause (b): merged is applied to every ID that has a brief: TASK-900 (no brief) and TASK-901 (a report
    file only, which is no brief) count nothing, nor does a subject that merges nothing.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("applied to every ID that has a brief"); handoff/TASK-033.md Context
    ("A -rN-report.md file is no brief")."""
    rep = known.report()
    assert rep.at_week(6, "merged") == 0
    assert rep.at_week(7, "merged") == 0
    assert rep.at_week(3, "merged") == 0


def test_task033_total_row(known):
    """R-044. Clause (b): the table has a total row; with every event inside the window it sums the weeks (merged 5,
    started 4, HARDENING lines 7). enforces: docs/BUILD_PLAN.md TASK-033 (b) ("and a total row")."""
    rep = known.report()
    assert rep.total is not None, rep.text
    assert rep.number(rep.total, "merged") == 5
    assert rep.number(rep.total, "started") == 4
    assert rep.number(rep.total, "hardening") == 7


def test_task033_rounds_three_builder_reports(known):
    """R-044. Clause (b): rounds read from three builder reports: TASK-101, the week's only merge, has mean and max 3.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) rounds; (c) "one with three builder reports"."""
    rep = known.report()
    assert rep.at_week(4, "rounds_max") == 3
    assert rep.at_week(4, "rounds_mean") == 3


def test_task033_rounds_letter_subround_report_reads_as_its_n(known):
    """R-044. Clause (b): `TASK-104-r3a-report.md` reads as round 3, so k1's merges (TASK-103 2, TASK-104 3) give max 3
    and mean 2.5. enforces: docs/BUILD_PLAN.md TASK-033 (b) ("a letter sub-round reading as its <N>"); (c) "a letter
    sub-round report"; "mean and maximum"."""
    rep = known.report()
    assert rep.at_week(1, "rounds_max") == 3
    assert rep.at_week(1, "rounds_mean") == pytest.approx(2.5, abs=0.051)


def test_task033_rounds_guard_record_outranks_reports_and_err_files_outnumber(known):
    """R-044. Clause (b): TASK-102's guard record (5 rounds) outranks its reports (r1, r2a); TASK-105's four .err files
    outnumber its one report and read at 4: k2's mean 4.5, max 5.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) (the largest of three readings); (c) "the guard's record outranking the
    reports", "an increment whose .err files outnumber its reports read at the .err count"."""
    rep = known.report()
    assert rep.at_week(2, "rounds_max") == 5
    assert rep.at_week(2, "rounds_mean") == pytest.approx(4.5, abs=0.051)


@pytest.mark.parametrize("k", [0, 3, 5, 6, 7])
def test_task033_a_week_without_a_merge_prints_a_blank_mean(known, k):
    """R-044. Clause (b): a week that merged nothing prints a blank mean, not a zero (rounds mean and days mean).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("a week that merged nothing prints a blank mean, not a zero"); (c)."""
    rep = known.report()
    assert rep.at_week(k, "merged") in (0, None)
    assert rep.at_week(k, "rounds_mean") is None, rep.row(k)
    assert not re.search(r"\d", rep.cell(rep.row(k), "days")), rep.row(k)


def test_task033_mean_days_from_start_to_merge_over_known_starts(known):
    """R-044. Clause (b): mean days from start to merge over the increments whose start is known: k4 9 (TASK-101),
    k2 16 (TASK-102; TASK-105's unknown start left out), k1 28 (TASK-103 19, TASK-104 37).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("mean days from start to merge over the increments whose start is
    known")."""
    rep = known.report()
    assert rep.at_week(4, "days") == pytest.approx(9, abs=0.051)
    assert rep.at_week(2, "days") == pytest.approx(16, abs=0.051)
    assert rep.at_week(1, "days") == pytest.approx(28, abs=0.051)


def test_task033_hardening_lines_added_by_commit_week(known):
    """R-044. Clause (b) and Requirement 5: lines added to docs/HARDENING.md by the commits on main touching it, by
    commit week: 5 at k3, 2 at k1 (a removed line not subtracted).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) (HARDENING lines); handoff/TASK-033.md Requirement 5 "HARDENING lines"."""
    rep = known.report()
    assert rep.at_week(3, "hardening") == 5
    assert rep.at_week(1, "hardening") == 2
    for k in (0, 2, 4, 5, 6, 7):
        assert rep.at_week(k, "hardening") in (0, None)


def test_task033_hardening_header_says_lines_landing_on_main(known):
    """R-044. Clause (b): the HARDENING column's header says the lines are lines landing on main that week.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("the header saying they are lines landing on main that week")."""
    rep = known.report()
    assert "main" in rep.header[rep.index("hardening")], rep.header


def test_task033_over_the_default_ceiling_listed_by_id(known):
    """R-044. Clause (b): under the table the increments over the default ceiling (3) are listed by ID with their
    rounds (TASK-102 5, TASK-105 4); TASK-101 (3), TASK-103 and TASK-104 are not; the stage review STAGE-B3 (4) is
    listed beneath them. enforces: docs/BUILD_PLAN.md TASK-033 (b) (the over-ceiling list, `--ceiling` default
    bridge_env.REVIEW_ROUNDS); (c) "one over the ceiling"."""
    rep = known.report()
    b102 = listed(rep, "TASK-102", 5, KNOWN)
    b105 = listed(rep, "TASK-105", 4, KNOWN)
    stage = listed(rep, "STAGE-B3", 4, KNOWN)
    assert stage[0] > b102[0] and stage[0] > b105[0], rep.after
    for ident, rounds in (("TASK-101", 3), ("TASK-103", 2), ("TASK-104", 3)):
        not_listed(rep, ident, rounds, KNOWN)


def test_task033_lift_column_four_values(known):
    """R-044. Clause (b): each round above the ceiling names the lift it used: TASK-102 `class` (r4) and `owner`
    (r5) from the guard's record, TASK-105 `unknown` (no record of its round 4), STAGE-B3 `none` (its record says
    no lift). enforces: docs/BUILD_PLAN.md TASK-033 (b) (`class`, `owner`, `none`, or `unknown`); (c) "the lift
    column's four values"."""
    rep = known.report()
    assert words_in(listed(rep, "TASK-102", 5, KNOWN)[1]) == {"class", "owner"}
    assert words_in(listed(rep, "TASK-105", 4, KNOWN)[1]) == {"unknown"}
    assert "none" in words_in(listed(rep, "STAGE-B3", 4, KNOWN)[1])


def test_task033_explicit_ceiling_four(known):
    """R-044. `--ceiling 4`: only TASK-102 (5) is over; TASK-105 (4) and STAGE-B3 (4) are not.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) `--ceiling`; handoff/TASK-033.md Context ("An increment is 'over' when its
    rounds exceed it")."""
    rep = known.report("--ceiling", "4")
    listed(rep, "TASK-102", 5, KNOWN)
    not_listed(rep, "TASK-105", 4, KNOWN)
    not_listed(rep, "STAGE-B3", 4, KNOWN)


def test_task033_explicit_ceiling_two(known):
    """R-044. `--ceiling 2`: TASK-101 (3) and TASK-104 (3) join the list; TASK-103 (2) does not.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) `--ceiling`."""
    rep = known.report("--ceiling", "2")
    listed(rep, "TASK-101", 3, KNOWN)
    listed(rep, "TASK-104", 3, KNOWN)
    listed(rep, "TASK-102", 5, KNOWN)
    not_listed(rep, "TASK-103", 2, KNOWN)


def test_task033_default_weeks_are_the_current_week_and_seven_before(known):
    """R-044. `--weeks` defaults to 8: one row per ISO week, the current UTC week and the seven before it.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("one row per ISO week of the last --weeks (default 8)");
    handoff/TASK-033.md Context ("Weeks are UTC ISO weeks")."""
    rep = known.report()
    assert set(rep.weeks) == {week(k) for k in range(8)}, sorted(rep.weeks)


@pytest.mark.parametrize("n", [1, 3, 520])
def test_task033_weeks_within_bounds(known, n):
    """R-044. `--weeks n` for n in 1..520 prints exactly n week rows, the current week and the n-1 before it.
    enforces: handoff/TASK-033.md Context ("--weeks: an integer count of ISO weeks, 1 to 520 inclusive")."""
    rep = known.report("--weeks", str(n))
    assert set(rep.weeks) == {week(k) for k in range(n)}


@pytest.mark.parametrize("value", ["0", "521", "x", "2.5", "-1"])
def test_task033_weeks_out_of_bounds_is_usage(known, value):
    """R-044. `--weeks` outside 1..520 or not an integer is a usage error, exit 2, no table.
    enforces: handoff/TASK-033.md Context ("A value outside its range, or one int cannot parse, is a usage error with
    exit 2")."""
    r = known.run("--weeks", value)
    assert r.rc == 2, r
    assert not any(SEP_RX.match(line) for line in r.out.splitlines()), r


@pytest.mark.parametrize("value", ["0", "101", "x"])
def test_task033_ceiling_out_of_bounds_is_usage(known, value):
    """R-044. `--ceiling` outside 1..100 or not an integer is a usage error, exit 2.
    enforces: handoff/TASK-033.md Context ("--ceiling: an integer count of rounds, 1 to 100 inclusive")."""
    r = known.run("--ceiling", value)
    assert r.rc == 2, r


@pytest.mark.parametrize("value", ["1", "100"])
def test_task033_ceiling_bounds_accepted(known, value):
    """R-044. `--ceiling 1` and `--ceiling 100` are accepted. enforces: handoff/TASK-033.md Context ("--ceiling ... 1 to
    100 inclusive")."""
    r = known.run("--ceiling", value)
    assert r.rc == 0, r


def test_task033_output_is_ascii(known):
    """R-044. The output is ASCII only, though a subject and a file on main hold non-ASCII text.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("prints, read-only and ASCII"); (c) "ASCII output"."""
    r = known.run()
    assert r.rc == 0, r
    assert all(b < 128 for b in r.raw_out), r.raw_out
    assert all(b < 128 for b in r.raw_err), r.raw_err


def tree_state(project):
    """(git status --porcelain --ignored, {relative path: sha256}) of the project root; .git/index is left out of
    the hashes because `git status` itself may refresh it."""
    status = git(project.ws, "status", "--porcelain", "--ignored", "--untracked-files=all")
    hashes = {}
    for dirpath, _, files in os.walk(str(project.root)):
        for name in files:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, str(project.root)).replace(os.sep, "/")
            if rel == "Workspace/.git/index":
                continue
            with open(path, "rb") as f:
                hashes[rel] = hashlib.sha256(f.read()).hexdigest()
    return status, hashes


def test_task033_the_tree_is_unchanged_after_a_run(tmp_path):
    """R-044. The program writes nothing: git status --porcelain and every file's hash are the same before and after a
    run (with --tokens on an empty --home too).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("the program writes nothing"); (c) "the tree unchanged after a run";
    handoff/TASK-033.md Requirement 6."""
    p = Project(tmp_path / "proj-tree-q7")
    p.brief("TASK-701")
    p.report("TASK-701-r1")
    p.commit("records: brief", at(10, 0))
    p.write("docs/HARDENING.md", "- a lead\n")
    p.commit("TASK-701: x (#1)", at(2, 2))
    p.launch("TASK-701", at(3, 0))
    p.rounds("TASK-701", [(at(3, 1), None, None)])
    p.err("TASK-701")
    home = tmp_path / "empty-home"
    home.mkdir()
    before = tree_state(p)
    r = pace([p.root, "--tokens", "--home", home], cwd=tmp_path)
    assert r.rc == 0, r
    assert tree_state(p) == before
    assert os.listdir(str(home)) == []


@pytest.mark.parametrize("make", ["missing", "no-git"])
def test_task033_a_root_that_is_no_project_exits_2_naming_it(tmp_path, make):
    """R-044. A given root that is no project (no folder, or Workspace/ without .git) exits 2 naming it, before any
    output: no section of the good root given before it is printed.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("a root that is no project exits 2 naming it"); handoff/TASK-033.md
    Requirement 5 ("before any output"); (c) "exit 2 on a non-project root"."""
    good = Project(tmp_path / "proj-good-q7")
    good.brief("TASK-801")
    good.commit("records: brief", at(10, 0))
    bad = tmp_path / "not-a-project-q7"
    if make == "no-git":
        (bad / "Workspace").mkdir(parents=True)
    r = pace([good.root, bad], cwd=tmp_path)
    assert r.rc == 2, r
    assert "not-a-project-q7" in r.both, r
    assert not any(line.lstrip().startswith("#") or "|" in line for line in r.out.splitlines()), r


def test_task033_untracked_handoff_prints_na(tmp_path):
    """R-044. A project whose handoff/ is untracked prints `n/a (handoff/ untracked)` in the rounds and started
    columns of every week row. enforces: docs/BUILD_PLAN.md TASK-033 (b); (c) "an untracked handoff/";
    handoff/TASK-033.md Requirement 5 ("read with git ls-files")."""
    p = Project(tmp_path / "proj-untracked-q7")
    p.write("docs/README.md", "fixture\n")
    p.commit("records: docs", at(10, 0))
    p.commit("TASK-501: x (#2)", at(2, 2))
    p.brief("TASK-501")                                  # written after the last commit: present, untracked
    p.report("TASK-501-r1")
    p.launch("TASK-501", at(3, 0))
    assert git(p.ws, "ls-files", "handoff/") == ""
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert len(rep.weeks) == 8
    for row in rep.weeks.values():
        assert UNTRACKED in rep.cell(row, "started"), row
        mi = rep.index("rounds_mean")
        assert UNTRACKED in row[mi], row


def test_task033_a_merge_week_is_the_committer_date(tmp_path):
    """R-044. A merge's week is the squash commit's committer date: authored at k3, committed at k2, it counts at k2.
    enforces: handoff/TASK-033.md Context ("A merge's week is the squash commit's committer date")."""
    p = Project(tmp_path / "proj-committer-q7")
    p.brief("TASK-201")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-201: x (#1)", at(3, 2), committer=at(2, 2))
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "merged") == 1
    assert rep.at_week(3, "merged") in (0, None)


def test_task033_week_boundaries_are_utc_iso_weeks(tmp_path):
    """R-044. Weeks are UTC ISO weeks: Monday 00:30 UTC counts in its week, Sunday 23:30 UTC in the week before, and
    Monday 03:00 +0500 (Sunday 22:00 UTC) in the week before too.
    enforces: handoff/TASK-033.md Context ("Weeks are UTC ISO weeks (date.isocalendar()), for every source alike");
    (c) "the week boundaries"."""
    p = Project(tmp_path / "proj-utc-q7")
    p.brief("TASK-301", "TASK-302", "TASK-303")
    p.commit("records: briefs", at(10, 0))
    monday = at(2, 0, hour=0)
    p.commit("TASK-301: a (#1)", monday + datetime.timedelta(minutes=30))
    p.commit("TASK-302: b (#2)", monday - datetime.timedelta(minutes=30))
    p.commit("TASK-303: c (#3)", monday, committer=monday.strftime("%Y-%m-%dT03:00:00+0500"))
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "merged") == 1
    assert rep.at_week(3, "merged") == 2


def test_task033_letter_files_beside_a_real_lettered_increment(tmp_path):
    """R-044. TASK-032's letter rule: `REVIEW-TASK-010c*.err` belong to TASK-010c, which has its own brief, not to
    TASK-010 (2 rounds, not over); TASK-010c reads 4 and is over; TASK-040's letter files (no TASK-040a..d briefs) are
    TASK-040's sub-rounds, over the ceiling. enforces: docs/BUILD_PLAN.md TASK-033 (b) ("a letter as its ordinal where
    the longer token has no brief and the shorter has one"); (c) "TASK-010's letter files beside a real TASK-010c"."""
    p = Project(tmp_path / "proj-letters-q7")
    p.brief("TASK-010", "TASK-010c", "TASK-040")
    p.report("TASK-010-r1", "TASK-010c-r1", "TASK-040-r1")
    p.commit("records: briefs", at(10, 0))
    p.commit("TASK-010: base (#1)", at(3, 2))
    p.commit("TASK-010c: lettered (#2)", at(2, 2))
    p.commit("TASK-040: letters (#3)", at(1, 2))
    p.err("TASK-010", "TASK-010-r2", "TASK-010c", "TASK-010c-r2", "TASK-010c-r3", "TASK-010c-r4",
          "TASK-040", "TASK-040a", "TASK-040b", "TASK-040c", "TASK-040d")
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(3, "rounds_max") == 2
    assert rep.at_week(2, "rounds_max") == 4
    assert 4 <= rep.at_week(1, "rounds_max") <= 5
    ids = ("TASK-010", "TASK-010c", "TASK-040")
    listed(rep, "TASK-010c", 4, ids)
    assert any(has_number(b, "TASK-040", 4) or has_number(b, "TASK-040", 5) for _, b in blocks(rep.after, "TASK-040", ids))
    not_listed(rep, "TASK-010", 2, ids)


def test_task033_iss013_form_merges_nothing_in_both_programs(tmp_path, program, monkeypatch):
    """R-044. One subject in the ISS-013 form with no leading ID, on one repository: plan-check.py's merged_ids does not
    read TASK-031 as merged, and pace-report.py counts no merge that week.
    enforces: docs/BUILD_PLAN.md TASK-033 (c) ("a subject in the ISS-013 form merging nothing in both programs (one
    test runs both on the same subject)"); handoff/TASK-033.md Context, "The ISS-013 subject"."""
    p = Project(tmp_path / "proj-iss013-q7")
    p.brief("TASK-031")
    p.commit("records: brief", at(10, 0))
    p.commit(ISS013_FORM, at(2, 2))
    r = pace([p.root], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert rep.at_week(2, "merged") in (0, None)
    assert rep.number(rep.total, "merged") in (0, None)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.chdir(str(p.ws))
    merged = program("plan-check").merged_ids("main")
    assert merged is not None and "TASK-031" not in merged


# ---------------------------------------------------------------- --tokens


def usage(i, o, cc, cr):
    return {"input_tokens": i, "output_tokens": o, "cache_creation_input_tokens": cc, "cache_read_input_tokens": cr}


def assistant(msg_id, when, u):
    return json.dumps({"type": "assistant", "timestamp": transcript_ts(when), "sessionId": "s",
                       "message": {"id": msg_id, "role": "assistant", "model": "m", "usage": u,
                                   "content": [{"type": "text", "text": "secret transcript text \u00e9"}]}})


def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def token_project(base, home, program, git_home=None):
    """A project merging TASK-401 at k2, with transcripts under <home>/.claude/projects/<key> for the keys
    evaluate-reports.py's project_keys gives its root:
      k2: msg_a twice (1.5M kept, the 1.0M copy dropped) + msg_f on Sunday 23:59:30 UTC (20,000) = 1.52
      k1: msg_e on Monday 00:00:30 UTC (10,000) = 0.01
      k3: msg_c under the Workspace's key = 2.00
      k4: msg_b in <key>/sub-x/subagents/ = 0.25
      k5: 9.00 under another project's key; k6: 3.00 in <key>/notes/deeper/ (neither counted)."""
    p = Project(base / "proj-tok-q7", home=git_home)
    p.brief("TASK-401")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-401: x (#1)", at(2, 2))
    er = program("evaluate-reports")
    keys = er.project_keys(p.name, str(p.root))
    assert len(keys) == 2, keys
    root_key, ws_key = keys
    projects = home / ".claude" / "projects"
    write_lines(projects / root_key / "s1.jsonl", [
        json.dumps({"type": "user", "timestamp": transcript_ts(at(2, 1)), "message": {"role": "user",
                                                                                        "content": "hi \u00e9"}}),
        assistant("msg_a", at(2, 1, hour=10), usage(100000, 400000, 300000, 700000)),
        "not json at all",
        assistant("msg_a", at(2, 1, hour=10, second=5), usage(100000, 200000, 300000, 400000)),
        assistant("msg_e", at(1, 0, hour=0, second=30), usage(1000, 2000, 3000, 4000)),
        assistant("msg_f", at(2, 6, hour=23, minute=59, second=30), usage(2000, 4000, 6000, 8000)),
    ])
    write_lines(projects / root_key / "sub-x" / "subagents" / "agent-1.jsonl", [
        assistant("msg_b", at(4, 3), usage(25000, 50000, 75000, 100000))])
    write_lines(projects / ws_key / "s2.jsonl", [assistant("msg_c", at(3, 1), usage(200000, 400000, 600000, 800000))])
    write_lines(projects / "C--elsewhere-other-project" / "s3.jsonl", [
        assistant("msg_z", at(5, 1), usage(900000, 1800000, 2700000, 3600000))])
    write_lines(projects / root_key / "notes" / "deeper" / "x.jsonl", [
        assistant("msg_y", at(6, 1), usage(300000, 600000, 900000, 1200000))])
    return p


@pytest.fixture(scope="module")
def tokens(tmp_path_factory):
    import conftest
    base = tmp_path_factory.mktemp("tokens")
    home = base / "fixture-home"
    p = token_project(base, home, conftest.load_program, git_home=tmp_path_factory.mktemp("git-home"))
    fx = Fixture(p)
    fx.home = home
    return fx


def token_report(tokens):
    return tokens.report("--tokens", "--home", tokens.home)


def test_task033_tokens_dedupe_a_message_id_at_its_greatest_total(tokens):
    """R-044. `--tokens`: the four usage fields summed per record, one usage per message id (the copy with the
    greatest total), a record's week from its timestamp: k2 1.50 + 0.02 = 1.52, k1 0.01.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) `--tokens`; (c) "a duplicated message id counted once at its greatest
    total"; handoff/TASK-033.md Context ("Tokens are printed in millions, to two decimal places")."""
    rep = token_report(tokens)
    assert NUM_RX.findall(rep.cell(rep.row(2), "tokens")) == ["1.52"], rep.row(2)
    assert NUM_RX.findall(rep.cell(rep.row(1), "tokens")) == ["0.01"], rep.row(1)


def test_task033_tokens_subagents_record_counted(tokens):
    """R-044. `--tokens`: a record in <key>/<sub>/subagents/*.jsonl is counted (k4 0.25); a .jsonl elsewhere under the
    key (k6) and another project's key (k5) are not.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("<key>/**/subagents/*.jsonl"); (c) "a subagents/ record counted"."""
    rep = token_report(tokens)
    assert NUM_RX.findall(rep.cell(rep.row(4), "tokens")) == ["0.25"], rep.row(4)
    for k in (5, 6):
        assert rep.number(rep.row(k), "tokens") in (0, None), rep.row(k)


def test_task033_tokens_workspace_key_counted(tokens):
    """R-044. `--tokens` reads the root's and the Workspace's keys as evaluate-reports.py's project_keys derives them:
    the Workspace key's record counts at k3 (2.00).
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("for the root's and the Workspace's keys as evaluate-reports.py derives
    them")."""
    rep = token_report(tokens)
    assert NUM_RX.findall(rep.cell(rep.row(3), "tokens")) == ["2.00"], rep.row(3)


def test_task033_tokens_cells_have_two_decimals_and_header_names_the_fields(tokens):
    """R-044. Tokens are millions to two decimals; the column's header names the four usage fields summed.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("named in the column's header"); handoff/TASK-033.md Context
    ("Tokens are printed in millions, to two decimal places")."""
    rep = token_report(tokens)
    header_text = " ".join(rep.header)
    for field in FOUR_FIELDS:
        assert field in header_text, rep.header
    for row in rep.weeks.values():
        cell = rep.cell(row, "tokens")
        assert cell == "" or re.fullmatch(r"\d+\.\d\d", cell), row


def test_task033_tokens_per_merged_increment_beside(tokens):
    """R-044. The week's tokens per merged increment stand beside the tokens: k2 merged TASK-401, 1.52 per merge.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("the week's tokens per merged increment beside it")."""
    rep = token_report(tokens)
    assert rep.at_week(2, "merged") == 1
    assert rep.at_week(2, "tokens_per_merged") == pytest.approx(1.52, abs=0.006)


def test_task033_tokens_no_session_folder_empty_cell_exit_0(tmp_path):
    """R-044. `--tokens` on a project with no session folder: an empty tokens cell in every week, exit 0.
    enforces: docs/BUILD_PLAN.md TASK-033 (b) ("a project with no session folder gets an empty tokens cell and exits
    0"); (c) "an empty cell without a session folder"."""
    p = Project(tmp_path / "proj-nosession-q7")
    p.brief("TASK-402")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-402: x (#1)", at(2, 2))
    home = tmp_path / "home-without-sessions"
    (home / ".claude" / "projects").mkdir(parents=True)
    r = pace([p.root, "--tokens", "--home", home], cwd=tmp_path)
    assert r.rc == 0, r
    rep = Report(section(r.out, p.name))
    assert len(rep.weeks) == 8
    for row in rep.weeks.values():
        assert rep.cell(row, "tokens") == "", row


def test_task033_tokens_print_no_transcript_content(tokens):
    """R-044. The program prints no transcript content, only counts and IDs.
    enforces: handoff/TASK-033.md Security context ("The program prints no transcript content")."""
    r = tokens.run("--tokens", "--home", tokens.home)
    assert r.rc == 0, r
    assert "secret transcript text" not in r.both
    assert "msg_a" not in r.both


# ---------------------------------------------------------------- limits, in this process


def is_git(argv):
    if isinstance(argv, (list, tuple)) and argv:
        first = str(argv[0])
    elif isinstance(argv, str) and argv.strip():
        first = argv.split()[0]
    else:
        return False
    return os.path.splitext(os.path.basename(first))[0].lower() == "git"


def git_subcommand(argv):
    args = [str(a) for a in (argv if isinstance(argv, (list, tuple)) else argv.split())][1:]
    i = 0
    while i < len(args):
        if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            i += 2
            continue
        if args[i].startswith("-"):
            i += 1
            continue
        return args[i]
    return None


class GitWatch(object):
    """Wraps the standard library's subprocess.Popen (init and communicate) for one in-process run: records every git
    command and the limit it was given; makes the git commands of one project (its folder named in the arguments or
    the working folder) end as at their limit (TimeoutExpired, the process killed); or, for the session-read case,
    lets git run without its limit so only the session read can reach one."""

    def __init__(self, monkeypatch, slow=None, unlimited_git=False):
        self.calls = []
        real_init = subprocess.Popen.__init__
        real_communicate = subprocess.Popen.communicate
        watch = self

        def init(self, *args, **kwargs):
            real_init(self, *args, **kwargs)
            argv = args[0] if args else kwargs.get("args")
            parts = list(argv) if isinstance(argv, (list, tuple)) else [argv]
            self._t033_where = " ".join(str(a) for a in parts) + " " + str(kwargs.get("cwd") or "")

        init.windowless_default = getattr(real_init, "windowless_default", False)

        def communicate(self, input=None, timeout=None):
            if is_git(self.args):
                watch.calls.append((self.args, timeout))
                where = getattr(self, "_t033_where", "").lower()
                if timeout is not None and slow and slow.lower() in where:
                    self.kill()
                    raise subprocess.TimeoutExpired(self.args, timeout)
                if unlimited_git:
                    return real_communicate(self, input)
            return real_communicate(self, input, timeout)

        monkeypatch.setattr(subprocess.Popen, "__init__", init)
        monkeypatch.setattr(subprocess.Popen, "communicate", communicate)


def run_main(mod, monkeypatch, capsys, argv):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.setattr(sys, "argv", ["pace-report.py"] + [str(a) for a in argv])
    try:
        rc = mod.main()
    except SystemExit as e:
        rc = e.code
    captured = capsys.readouterr()
    return Run(0 if rc is None else rc, captured.out.encode("ascii", "replace"), captured.err.encode("ascii", "replace"))


def small_project(base, name):
    p = Project(base / name)
    p.brief("TASK-451")
    p.report("TASK-451-r1")
    p.write("docs/HARDENING.md", "- a lead\n")
    p.commit("records: brief", at(10, 0))
    p.commit("TASK-451: x (#1)", at(2, 2))
    return p


def test_task033_every_git_command_has_a_120_second_limit_and_is_read_only(tmp_path, program, monkeypatch, capsys):
    """R-044. Every git command the program runs is given a 120-second limit and is a read (no commit, add, reset,
    checkout, switch, stash, update-ref, gc ...). enforces: docs/BUILD_PLAN.md TASK-033 (b) ("every git command is
    read-only with a 120-second limit"); handoff/TASK-033.md Context ("Limits: every git command 120 seconds")."""
    p = small_project(tmp_path, "proj-limit-q7")
    mod = program("pace-report")
    watch = GitWatch(monkeypatch)
    r = run_main(mod, monkeypatch, capsys, [p.root])
    assert r.rc == 0, r
    assert watch.calls, "no git command was seen"
    assert all(t is not None and float(t) == 120 for _, t in watch.calls), watch.calls
    writes = {"commit", "add", "rm", "mv", "reset", "checkout", "switch", "restore", "stash", "merge", "rebase", "push",
              "fetch", "pull", "gc", "update-ref", "update-index", "tag", "worktree", "clean", "cherry-pick", "revert",
              "am", "apply", "init", "clone", "notes", "replace", "prune", "repack", "pack-refs", "maintenance"}
    assert not [a for a, _ in watch.calls if git_subcommand(a) in writes], watch.calls


def test_task033_a_git_command_at_its_limit_fails_that_project_only(tmp_path, program, monkeypatch, capsys):
    """R-044. A git command that reaches its limit fails that project naming the command; the other project is still
    printed; the exit is 1. enforces: docs/BUILD_PLAN.md TASK-033 (b) ("one that reaches it fails that project naming
    the command (the others printed, exit 1 at the end)"); handoff/TASK-033.md Requirement 5 "Exit codes"."""
    slow = small_project(tmp_path, "proj-slow-q7")
    fast = small_project(tmp_path, "proj-fast-q7")
    mod = program("pace-report")
    GitWatch(monkeypatch, slow="proj-slow-q7")
    r = run_main(mod, monkeypatch, capsys, [slow.root, fast.root])
    assert r.rc == 1, r
    rep = Report(section(r.out, "proj-fast-q7", others=("proj-slow-q7",)))
    assert len(rep.weeks) == 8
    assert rep.at_week(2, "merged") == 1
    assert "proj-slow-q7" in r.both, r
    assert any("git" in line and re.search(r"time|limit|120", line, re.I) for line in r.both.splitlines()), r
    assert "Traceback" not in r.both


def test_task033_a_timed_out_session_read_gives_an_empty_cell(tmp_path, program, monkeypatch, capsys):
    """R-044. The session-folder read is bounded per project; at its limit the tokens cell is empty and the project is
    named. Produced without waiting 120 seconds: every module-level 120-second number in pace-report.py and the bridge
    modules it loaded is lowered (the brief's "monkeypatched limit"), while git runs without a limit, so only the
    session read can reach one. enforces: docs/BUILD_PLAN.md TASK-033 (b) ("the read of the session folders is
    bounded like a git command (120 seconds per project; on the limit an empty cell and the project named)"); (c) "an
    empty cell ... on a timed-out read"; handoff/TASK-033.md Requirement 6."""
    home = tmp_path / "fixture-home"
    p = token_project(tmp_path, home, program)
    mod = program("pace-report")
    modules = [mod] + [v for v in vars(mod).values() if isinstance(v, types.ModuleType)
                       and os.path.dirname(os.path.abspath(getattr(v, "__file__", "") or "")) == os.path.abspath(CB)]
    lowered = []
    for m in modules:
        for name, value in list(vars(m).items()):
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)) and value == 120:
                monkeypatch.setattr(m, name, -1)
                lowered.append(name)
            elif isinstance(value, datetime.timedelta) and value == datetime.timedelta(seconds=120):
                monkeypatch.setattr(m, name, datetime.timedelta(seconds=-1))
                lowered.append(name)
    if not lowered:
        pytest.skip("pace-report.py holds no module-level 120-second limit to lower, and the brief fixes no other name")
    GitWatch(monkeypatch, unlimited_git=True)
    r = run_main(mod, monkeypatch, capsys, [p.root, "--tokens", "--home", home])
    assert r.rc in (0, 1), r
    assert "Traceback" not in r.both
    rep = Report(section(r.out, p.name))
    assert len(rep.weeks) == 8
    for row in rep.weeks.values():
        assert rep.cell(row, "tokens") == "", row
    assert any(p.name in line and re.search(r"time|limit|120", line, re.I) for line in r.both.splitlines()), r


# ---------------------------------------------------------------- the command reference and the parser


def test_task033_dump_cli_lists_pace_report():
    """R-044. tests/test_dump_cli.py's ARGPARSE lists pace-report.py, so its entry is compared with its build_parser().
    enforces: docs/BUILD_PLAN.md TASK-033 (c) ("tests/test_dump_cli.py lists the program"); handoff/TASK-033.md
    Requirement 7."""
    tree = ast.parse(read_source(os.path.join(HERE, "test_dump_cli.py")))
    names = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ARGPARSE" for t in node.targets):
            names |= {n.value for n in ast.walk(node.value) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "pace-report.py" in names, sorted(names)


def test_task033_command_reference_names_pace_report():
    """R-044. docs/cli-reference.json carries pace-report.py as an argparse command (the reference regenerated).
    enforces: docs/BUILD_PLAN.md TASK-033 (c) ("the command reference regenerated"); handoff/TASK-033.md Context
    "tests/test_dump_cli.py and the command reference"."""
    with open(os.path.join(WORKSPACE, "docs", "cli-reference.json"), encoding="utf-8") as f:
        data = json.load(f)
    entries = [c for c in data["commands"] if "pace-report" in str(c.get("name", ""))]
    assert entries, [c.get("name") for c in data["commands"]]
    assert entries[0].get("source") == "argparse"


def test_task033_parser_and_docstring(program):
    """R-044. pace-report.py has a module-level build_parser() taking the roots, --weeks, --ceiling, --tokens and
    --home; its module docstring gives the usage, the sources and the exit codes.
    enforces: handoff/TASK-033.md Requirement 5 ("an argparse program with a module-level build_parser()"),
    Requirement 8; docs/BUILD_PLAN.md TASK-033 (b) (the command line)."""
    assert os.path.isfile(PACE), "bridge/cursor-bridge/pace-report.py does not exist"
    mod = program("pace-report")
    parser = mod.build_parser()
    options = {s for a in parser._actions for s in a.option_strings}
    assert {"--weeks", "--ceiling", "--tokens", "--home"} <= options, options
    doc = mod.__doc__ or ""
    for word in ("--weeks", "--ceiling", "--tokens", "--home", "runs.jsonl", "rounds-", "HARDENING.md"):
        assert word in doc, word
    assert re.search(r"\b2\b", doc) and re.search(r"\b1\b", doc) and re.search(r"\b0\b", doc)


def test_task033_help_exits_0(tmp_path):
    """R-044. `pace-report.py --help` prints the usage and exits 0, ASCII.
    enforces: handoff/TASK-033.md Requirement 5 (argparse program), Requirement 8."""
    r = pace(["--help"], cwd=tmp_path)
    assert r.rc == 0, r
    assert "--weeks" in r.out
    assert all(b < 128 for b in r.raw_out)


# ---------------------------------------------------------------- the bridge's own Workspace


def own_checkout_skip_reason():
    if os.path.basename(WORKSPACE) != "Workspace":
        return "the checkout does not sit in a folder named Workspace (CI's checkout)"
    p = subprocess.run(["git", "-C", WORKSPACE, "rev-parse", "--is-shallow-repository"], capture_output=True, text=True,
                       timeout=TIMEOUT)
    if p.returncode != 0 or p.stdout.strip() == "true":
        return "the checkout is shallow"
    p = subprocess.run(["git", "-C", WORKSPACE, "rev-parse", "--verify", "--quiet", "refs/heads/main"],
                       capture_output=True, text=True, timeout=TIMEOUT)
    if p.returncode != 0:
        return "the checkout has no local main"
    return None


def test_task033_the_bridges_own_workspace_prints_without_error(tmp_path):
    """R-044. pace-report.py on the bridge's own root (this checkout's parent), without --tokens, under the temporary
    HOME, prints its section without error. Skipped where the checkout is shallow, has no local main, or does not sit
    in a folder named Workspace. enforces: docs/BUILD_PLAN.md TASK-033 (c) ("the bridge's own Workspace printing
    without error"); handoff/TASK-033.md Context, "Development data"."""
    reason = own_checkout_skip_reason()
    if reason:
        pytest.skip(reason)
    root = os.path.dirname(WORKSPACE)
    r = pace([root], cwd=tmp_path, timeout=600)
    assert r.rc == 0, r
    assert "Traceback" not in r.both
    assert all(b < 128 for b in r.raw_out)
    rep = Report(section(r.out, os.path.basename(root)))
    assert set(rep.weeks) == {week(k) for k in range(8)}
