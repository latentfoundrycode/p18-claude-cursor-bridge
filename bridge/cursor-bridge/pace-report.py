#!/usr/bin/env python3
"""pace-report: read-only weekly pace table per project (R-044, R-089).

  python pace-report.py [<project root>...] [--weeks <n>] [--ceiling <n>] [--tokens] [--home <folder>]

Run from any folder. ASCII output only; writes nothing. A project root holds Workspace/ with its
own .git. With no roots, the roots are evaluate-reports.py's PROJECTS plus the bridge root found
like that program. Defaults for --weeks (8), --ceiling (bridge_env.REVIEW_ROUNDS), and --home (~)
are resolved in main(), not in the parser. No option is added beyond those.

A counted name is an increment's ID (a string GRAMMAR_ID_PATTERN fullmatches) or PR-<n> (PR-
and a whole number from 1, parsed with int), the reserved form for a pull request. It is counted
where it has a brief under a tracked handoff/, a guard rounds record (a record named STAGE-
excepted), or a tagged pass line in run/supervisor/in-flight.md. PR-<n> is also counted by a
commit of refs/heads/main whose subject closes with (#<n>) and names no name counted by those
three: the IDs the subject reader returns that are counted names. Where that subject names one
or more, PR-<n> is not a name of its own; its pass lines and their causes fold into the first
counted name by position in the subject (a name the reader returns only from a trailer sorts
after every name that stands in the subject, and those tie by the ID text). A PR-<n> that main
does not close is a name of its own, started and not merged. One merge is never two names and
one pass never two passes.

Columns per ISO week (UTC): started (the earliest of a counted name's launcher rows, its
non-seeded guard rounds and its pass lines, folded pass lines included; a PR-<n> with none of
those starts at its commit on refs/heads/main; else unknown), merged (by the commits of
refs/heads/main alone: an ID by a subject the reader says names it, at its earliest such commit,
and PR-<n> by the closing (#<n>) where it is a name of its own; a rounds record or a pass line
never merges a name; with handoff/ untracked, every ID the reader finds, as before), rounds mean
and max among merges that week that have a rounds reading, mean days from a known start to that
merge, and docs/HARDENING.md lines added on refs/heads/main that week (added lines only). The
HARDENING column reads refs/heads/main, as the commit list does. A total row follows. Below the
table, IDs over --ceiling with round counts and lifts (class, owner, none, unknown), then stage
reviews (STAGE-<name>). Those lists keep their present rules: a name with no brief is not listed
as over the ceiling, and a stage review stays in the stage list.

One round per name and round number. Its records are the builder's launcher rows (kind builder,
not slot not free) of that brief and round (a row with no round is round 1), including a brief
that has no brief file, the guard's non-seeded entry of that round, and the pass lines of that
name and round (a pass line with no round number is round 1; folded pass lines count under the
name they fold into). A seeded guard round is not a record, not a start and not a pass. The
round's cause is the first stated one among the builder's rows (log order), the guard's round
and the pass lines (log order); a value is stated when it is on bridge_env.ROUND_CAUSES, and
unstated only where none of them states one. The round, with its cause, stands in the week of
its earliest record. The line, printed only where the window holds at least one round after the
first, is `Round causes (<n> rounds after the first): ` then `<cause> <count> (<pct>%)` joined
by `; `, in the report's ROUND_CAUSES order (bridge_env.ROUND_CAUSES, then unstated), zeroes
left out, `<pct>` rounded as round(100.0 * count / n).

Below that line, or where it would stand, one line per week of the window that holds a recorded
pass, in the table's week order. A pass is one per name, reviewer kind and round: a non-seeded
guard round is a review-b pass in the week of its time; a pass line is a pass of its name, kind
and round in the week of its stamp, the earliest if written twice; a review-b pass line is not
a further pass where the guard holds that name and round. Kinds are review-a, review-b,
security-auditor, design-auditor, plan-critic, design-critic-b and supervisor, printed in that
order. The line is `<YYYY-Www> <kind> <count>, <kind> <count> recorded passes only`: one space
between a kind and its count, a comma and a space between kinds, and nothing after
`recorded passes only`. It counts recorded passes only. Then `Builder rounds per model:`, from
builder launcher rows only, unchanged. With --tokens, token millions (sum of input_tokens,
output_tokens, cache_creation_input_tokens, cache_read_input_tokens per message id, greatest
total kept) from ~/.claude/projects/<key>/*.jsonl and <key>/**/subagents/*.jsonl for keys from
evaluate-reports.py's project_keys, plus tokens per merged increment.

The in-flight log is read as UTF-8 with errors replaced, at most 8388608 bytes; past that cap
only the bytes up to the last newline are kept, and a file with no newline inside the cap is no
pass lines. A missing or unreadable file is no pass lines. A line that is not a whole pass line
is skipped. With handoff/ untracked, started and rounds show n/a (handoff/ untracked); the cause
line and the passes lines are still printed from the launcher rows, the guard rounds and the
pass lines. Sources: git log on refs/heads/main (committer week), run/launcher/runs.jsonl,
.git/bridge/rounds-*.json, handoff/*.md and *-report.md, run/review/REVIEW-*.err,
run/supervisor/in-flight.md, docs/HARDENING.md numstat, session jsonl.
Every git command is read-only with a 120-second limit; session folder reads use the same limit per project.

Exit 0 when done; 1 when a project's git command failed (timed out, exited non-zero, or could not
start; others still printed); 2 for usage or a given root that is not a project.
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True

_BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BRIDGE_DIR not in sys.path:
    sys.path.insert(0, _BRIDGE_DIR)
import bridge_env

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
GIT_LIMIT = 120
_IN_FLIGHT_CAP = 8 * 1024 * 1024
_REVIEWERS = (
    "review-a",
    "review-b",
    "security-auditor",
    "design-auditor",
    "plan-critic",
    "design-critic-b",
    "supervisor",
)
_PASS_RX = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z) PASS ([A-Z][A-Za-z0-9-]*)(?: r([0-9]+))? ([a-z0-9-]+)(?: (.+))?$"
)
_PR_CLOSE_RX = re.compile(r"\(#([0-9]+)\)$")
_ID_EDGE = r"[A-Za-z0-9-]"
SESSION_READ_LIMIT = 120
UNTRACKED_HANDOFF = "n/a (handoff/ untracked)"
USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)
_MAX_JSONL_LINE = 64 * 1024 * 1024
LINE_CAP = 64 * 1024 * 1024
_READ_LINE_TIMED_OUT = object()
_REVIEW_ERR_RX = re.compile(r"^REVIEW-(.+)\.err$", re.I)
_COMMIT_HEAD_RX = re.compile(r"^[0-9a-f]{40} ([0-9]+)$")
_COMMIT_LOG_CMD = (
    "git log --format=%x00%H %ct%n%s%n%(trailers:key=Merges,valueonly) refs/heads/main --"
)


def _load_evaluate_reports():
    path = os.path.join(_BRIDGE_DIR, "evaluate-reports.py")
    spec = importlib.util.spec_from_file_location("evaluate_reports", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_parser():
    ap = argparse.ArgumentParser(description="Weekly pace table per project (read-only).")
    ap.add_argument("roots", nargs="*", help="project roots (default: evaluate-reports project list)")
    ap.add_argument("--weeks", type=int, help="ISO weeks to show (1-520, default 8)")
    ap.add_argument("--ceiling", type=int, help="round ceiling (1-100, default REVIEW_ROUNDS)")
    ap.add_argument("--tokens", action="store_true", help="include token columns from session jsonl")
    ap.add_argument("--home", help="folder holding .claude/projects (default: user home at run time)")
    return ap


def _ascii_name(name):
    return name.encode("ascii", "backslashreplace").decode("ascii")


def _iso_week(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    else:
        dt = dt.astimezone(datetime.timezone.utc)
    y, w, _ = dt.date().isocalendar()
    return (y, w)


def _week_range(n):
    now = datetime.datetime.now(datetime.timezone.utc)
    monday = datetime.datetime.combine(
        now.date() - datetime.timedelta(days=now.weekday()),
        datetime.time(0, 0),
        tzinfo=datetime.timezone.utc,
    )
    return [_iso_week(monday - datetime.timedelta(weeks=k)) for k in range(n)]


def _parse_run_time(text):
    if not text or not isinstance(text, str):
        return None
    m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z", text)
    if not m:
        return None
    try:
        return datetime.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
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


def _git(ws, args, diff_output=False, as_bytes=False):
    cmd = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "log.showSignature=false",
        "-C",
        ws,
    ]
    arglist = list(args)
    if diff_output:
        if "--" in arglist:
            i = arglist.index("--")
            arglist = arglist[:i] + ["--no-textconv", "--no-ext-diff"] + arglist[i:]
        else:
            arglist = arglist + ["--no-textconv", "--no-ext-diff"]
    cmd.extend(arglist)
    try:
        if as_bytes:
            p = subprocess.run(
                cmd,
                capture_output=True,
                creationflags=NO_WINDOW,
                timeout=GIT_LIMIT,
                env=_git_env(),
            )
        else:
            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=NO_WINDOW,
                timeout=GIT_LIMIT,
                env=_git_env(),
            )
    except subprocess.TimeoutExpired:
        return "timeout", None, None
    except OSError:
        return "start", None, None
    if p.returncode != 0:
        return "fail", None, p.returncode
    return "ok", p.stdout, None


def _rounds_file_ids(common):
    out = []
    for id_part in bridge_env._read_rounds_files(common).keys():
        if id_part.startswith("STAGE-") and bridge_env.parse_review_name(id_part) is None:
            continue
        out.append(id_part)
    return out


def _handoff_untracked(ls_out):
    return not any(line.strip() for line in (ls_out or "").splitlines())


def _ids_with_brief(ls_out):
    ids = set()
    for line in (ls_out or "").splitlines():
        line = line.replace("\\", "/").strip()
        if not line.startswith("handoff/") or not line.endswith(".md"):
            continue
        rest = line[len("handoff/") :]
        if "/" in rest:
            continue
        base = os.path.basename(line)
        if bridge_env.HANDOFF_REPORT_NAME.search(base):
            continue
        parsed = bridge_env.parse_review_name(base[:-3])
        if parsed:
            ids.add(parsed[0])
    return ids


def _letter_err_belongs(brief_ids, id_part, token):
    if token == id_part:
        return True
    if token.startswith(id_part) and len(token) > len(id_part):
        extra = token[len(id_part) :]
        if re.fullmatch(r"[a-z]+", extra):
            if token in brief_ids:
                return False
            return id_part in brief_ids
    return False


def _report_rounds(ws, id_part):
    best = 0
    handoff = os.path.join(ws, "handoff")
    if not os.path.isdir(handoff):
        return 0
    pat = re.compile(r"^%s-r([1-9][0-9]*)[a-z]?-report\.md$" % re.escape(id_part), re.I)
    for name in os.listdir(handoff):
        m = pat.match(name)
        if m:
            best = max(best, int(m.group(1)))
    return best


def _err_rounds(ws, id_part, brief_ids):
    review = os.path.join(ws, "run", "review")
    if not os.path.isdir(review):
        return 0
    count = 0
    max_r = 0
    for name in os.listdir(review):
        m = _REVIEW_ERR_RX.match(name)
        if not m:
            continue
        token = m.group(1)
        parsed = bridge_env.parse_review_name(token)
        if parsed and parsed[0] == id_part:
            count += 1
            max_r = max(max_r, parsed[1])
            continue
        if _letter_err_belongs(brief_ids, id_part, token):
            count += 1
    if count > _report_rounds(ws, id_part):
        return count
    return max(max_r, count)


def _guard_rounds(common, id_part):
    data = bridge_env._read_rounds_files(common).get(id_part)
    if not data:
        return 0
    rounds = data.get("rounds") or []
    return len([r for r in rounds if isinstance(r, dict)])


def _has_rounds_reading(ws, common, id_part, brief_ids):
    if _report_rounds(ws, id_part) > 0:
        return True
    if _err_rounds(ws, id_part, brief_ids) > 0:
        return True
    if _guard_rounds(common, id_part) > 0:
        return True
    return False


def _rounds_for_id(ws, common, id_part, brief_ids):
    return max(
        _report_rounds(ws, id_part),
        _err_rounds(ws, id_part, brief_ids),
        _guard_rounds(common, id_part),
    )


def _start_times(ws, common, id_part):
    times = []
    for row in bridge_env.read_runs_jsonl(ws):
        if row.get("brief") != id_part:
            continue
        if row.get("slot") == "not free":
            continue
        t = _parse_run_time(bridge_env._event_time_launcher(row))
        if t:
            times.append(t)
    data = bridge_env._read_rounds_files(common).get(id_part)
    if data:
        for rnd in data.get("rounds") or []:
            if not isinstance(rnd, dict) or rnd.get("seeded"):
                continue
            t = _parse_run_time(rnd.get("time") or "")
            if t:
                times.append(t)
    if not times:
        return None
    return min(times)


def _commits(ws):
    status, out, code = _git(
        ws,
        [
            "log",
            "--format=%x00%H %ct%n%s%n%(trailers:key=Merges,valueonly)",
            "refs/heads/main",
            "--",
        ],
        as_bytes=True,
    )
    if status != "ok":
        return status, None, code
    text = out.decode("utf-8", errors="replace")
    commits = []
    for rec in text.lstrip("\x00").split("\x00"):
        if not rec.strip():
            continue
        lines = rec.split("\n")
        head = lines[0].strip()
        m = _COMMIT_HEAD_RX.match(head)
        if not m:
            continue
        try:
            ts = int(m.group(1))
        except ValueError:
            continue
        try:
            dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        except (OverflowError, OSError, ValueError):
            continue
        body = lines[1:]
        subject = body[0] if body else ""
        merged = bridge_env.squash_merged_ids_from_lines(
            body, bridge_env.GRAMMAR_ID_PATTERN, plan_style=False
        )
        commits.append((dt, merged, subject))
    commits.reverse()
    return "ok", commits, None


def _hardening_by_week(ws):
    status, out, code = _git(
        ws,
        ["log", "refs/heads/main", "--format=%ct", "--numstat", "--", "docs/HARDENING.md"],
        diff_output=True,
    )
    if status != "ok":
        return status, None, code
    by_week = {}
    cur_ts = None
    for line in out.splitlines():
        if line and line.isdigit():
            try:
                cur_ts = int(line)
            except ValueError:
                cur_ts = None
            continue
        if cur_ts is None or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            added = int(parts[0])
        except ValueError:
            continue
        if added <= 0:
            continue
        try:
            wk = _iso_week(datetime.datetime.fromtimestamp(cur_ts, tz=datetime.timezone.utc))
        except (OverflowError, OSError, ValueError):
            cur_ts = None
            continue
        by_week[wk] = by_week.get(wk, 0) + added
    return "ok", by_week, None


def _lift_map(ws, common, id_part):
    lifts = {}
    for row in bridge_env.read_runs_jsonl(ws):
        if row.get("brief") != id_part:
            continue
        if row.get("slot") == "not free":
            continue
        rnd = row.get("round")
        if rnd is None:
            rnd = 1
        try:
            rnd = int(rnd)
        except (TypeError, ValueError):
            continue
        lift = row.get("lift")
        if lift in ("class", "owner"):
            lifts[rnd] = lift
        elif lift is None and row.get("brief"):
            lifts.setdefault(rnd, "none")
    data = bridge_env._read_rounds_files(common).get(id_part)
    if data:
        for rnd in data.get("rounds") or []:
            if not isinstance(rnd, dict):
                continue
            rn = rnd.get("round")
            try:
                rn = int(rn)
            except (TypeError, ValueError):
                continue
            lift = rnd.get("lift")
            if lift in ("class", "owner"):
                lifts[rn] = lift
            elif lift is None:
                lifts.setdefault(rn, "none")
    return lifts


ROUND_CAUSES = bridge_env.ROUND_CAUSES + ("unstated",)


def _builder_rounds(ws, weeks):
    """{(brief id, round): (model, cause)} of the launcher's builder rows launched in the window, a
    round launched twice counted once and its last row kept (release S: M1, M2)."""
    seen = {}
    for row in bridge_env.read_runs_jsonl(ws):
        if row.get("kind") != "builder" or not row.get("brief") or row.get("slot") == "not free":
            continue
        try:
            rnd = int(row.get("round") or 1)
        except (TypeError, ValueError):
            continue
        when = _parse_run_time(str(row.get("id", ""))[:20])
        if when is None or _iso_week(when) not in weeks:
            continue
        cause = row.get("cause")
        seen[(str(row["brief"]), rnd)] = (str(row.get("model") or "unknown"), cause if cause in ROUND_CAUSES else "unstated")
    return seen


def _model_lines(ws, weeks):
    """The builder-rounds-per-model line, from builder launcher rows only (M2)."""
    rounds = _builder_rounds(ws, weeks)
    by_model = {}
    for (ident, _), (model, _) in rounds.items():
        by_model.setdefault(model, []).append(ident)
    if not by_model:
        return []
    parts = []
    for model in sorted(by_model):
        ids = by_model[model]
        parts.append("%s %d round(s) over %d increment(s), mean %s" % (_ascii_name(model), len(ids), len(set(ids)), _fmt_num(len(ids) / float(len(set(ids))))))
    return ["Builder rounds per model: " + "; ".join(parts)]


def _grammar_name(name):
    return isinstance(name, str) and re.fullmatch(bridge_env.GRAMMAR_ID_PATTERN, name) is not None


def _stated_cause(value):
    if isinstance(value, str) and value in bridge_env.ROUND_CAUSES:
        return value
    return None


def _first_stated(values):
    for value in values:
        stated = _stated_cause(value)
        if stated:
            return stated
    return None


def _closing_pr(subject):
    if not isinstance(subject, str):
        return None
    m = _PR_CLOSE_RX.search(subject.rstrip())
    if not m:
        return None
    try:
        n = int(m.group(1))
    except ValueError:
        return None
    if n < 1:
        return None
    return n


def _parse_pass_stamp(text):
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None


def _parse_pass_line(line):
    m = _PASS_RX.match(line)
    if not m:
        return None
    when = _parse_pass_stamp(m.group(1))
    if when is None or not _grammar_name(m.group(2)):
        return None
    if m.group(3) is None:
        rnd = 1
    else:
        try:
            rnd = int(m.group(3))
        except ValueError:
            return None
        if rnd < 1 or rnd > 999:
            return None
    if m.group(4) not in _REVIEWERS:
        return None
    cause = m.group(5)
    if cause is not None and cause not in bridge_env.ROUND_CAUSES:
        return None
    return {"time": when, "name": m.group(2), "round": rnd, "kind": m.group(4), "cause": cause}


def _read_pass_lines(ws):
    path = os.path.join(ws, "run", "supervisor", "in-flight.md")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            data = f.read(_IN_FLIGHT_CAP + 1)
    except OSError:
        return []
    if len(data) > _IN_FLIGHT_CAP:
        data = data[:_IN_FLIGHT_CAP]
        cut = data.rfind("\n")
        if cut < 0:
            return []
        data = data[:cut]
    out = []
    for line in data.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        parsed = _parse_pass_line(line)
        if parsed:
            out.append(parsed)
    return out


def _id_at(subject, ident):
    m = re.search("(?<!" + _ID_EDGE + ")" + re.escape(ident) + "(?!" + _ID_EDGE + ")", subject or "")
    return m.start() if m else None


def _first_counted_name(subject, merged, occupy):
    found = []
    for ident in merged:
        if ident not in occupy:
            continue
        at = _id_at(subject, ident)
        found.append((10 ** 9 if at is None else at, ident))
    if not found:
        return None
    found.sort()
    return found[0][1]


def _home_name(name, fold):
    seen = set()
    while name in fold and name not in seen:
        seen.add(name)
        nxt = fold[name]
        if nxt == name:
            break
        name = nxt
    return name


def _builder_events(ws):
    events = []
    for row in bridge_env.read_runs_jsonl(ws):
        if row.get("kind") != "builder" or not row.get("brief") or row.get("slot") == "not free":
            continue
        brief = row.get("brief")
        if not _grammar_name(brief):
            continue
        raw = row.get("round")
        if isinstance(raw, bool):
            continue
        try:
            rnd = int(raw or 1)
        except (TypeError, ValueError):
            continue
        if rnd < 1:
            continue
        events.append((brief, rnd, _parse_run_time(str(row.get("id", ""))[:20]), row.get("cause")))
    return events


def _guard_name_ids(common):
    out = set()
    for id_part in bridge_env._read_rounds_files(common):
        if id_part.startswith("STAGE-") or not _grammar_name(id_part):
            continue
        out.add(id_part)
    return out


def _guard_events(common):
    events = []
    for id_part, data in bridge_env._read_rounds_files(common).items():
        if id_part.startswith("STAGE-") or not _grammar_name(id_part):
            continue
        for rnd in data.get("rounds") or []:
            if not isinstance(rnd, dict) or rnd.get("seeded"):
                continue
            rn = rnd.get("round")
            if isinstance(rn, bool) or not isinstance(rn, int) or rn < 1:
                continue
            events.append((id_part, rn, _parse_run_time(rnd.get("time") or ""), rnd.get("cause")))
    return events


def _format_cause_line(causes):
    n = len(causes)
    parts = []
    for cause in ROUND_CAUSES:
        count = causes.count(cause)
        if count:
            parts.append("%s %d (%d%%)" % (cause, count, round(100.0 * count / n)))
    return "Round causes (%d rounds after the first): %s" % (n, "; ".join(parts))


def _format_pass_lines(by_week, weeks):
    lines = []
    for wk in weeks:
        counts = by_week.get(wk)
        if not counts:
            continue
        parts = ["%s %d" % (kind, counts[kind]) for kind in _REVIEWERS if counts.get(kind)]
        if parts:
            lines.append("%d-W%02d %s recorded passes only" % (wk[0], wk[1], ", ".join(parts)))
    return lines


def _pace_names(ws, common, brief_ids, untracked, commits, weeks):
    """Counted names, their starts and merges, the cause-line causes and the passes lines.

    `commits` is oldest first, as `_commits` returns it. A seeded guard round is ignored.
    """
    weeks_set = set(weeks)
    pass_rows = _read_pass_lines(ws)
    guard = _guard_events(common)
    builders = _builder_events(ws)
    base = set()
    if not untracked:
        for ident in brief_ids:
            if _grammar_name(ident):
                base.add(ident)
    base.update(_guard_name_ids(common))
    for row in pass_rows:
        base.add(row["name"])
    fold = {}
    own = {}
    seen_pr = set()
    for dt, merged, subject in commits:
        n = _closing_pr(subject)
        if n is None or n in seen_pr:
            continue
        seen_pr.add(n)
        pr = "PR-%d" % n
        occupy = set(base)
        if untracked:
            for ident in merged:
                if _grammar_name(ident):
                    occupy.add(ident)
        target = _first_counted_name(subject, merged, occupy)
        if target and target != pr:
            fold[pr] = target
        else:
            own[pr] = dt
    counted = set(base)
    for pr in fold:
        counted.discard(pr)
    counted.update(own)
    for target in fold.values():
        if target not in fold:
            counted.add(target)

    def home(name):
        return _home_name(name, fold)

    pass_times = {}
    for row in pass_rows:
        pass_times.setdefault(home(row["name"]), []).append(row["time"])
    starts = {}
    start_dt = {}
    if not untracked:
        for ident in counted:
            times = list(pass_times.get(ident, ()))
            base_t = _start_times(ws, common, ident)
            if base_t:
                times.append(base_t)
            if ident in own and not times:
                times.append(own[ident])
            dt = min(times) if times else None
            start_dt[ident] = dt
            starts[ident] = _iso_week(dt) if dt else None
    merge_dt = {}
    merge_week = {}
    for dt, merged, subject in commits:
        wk = _iso_week(dt)
        for ident in merged:
            if _grammar_name(ident) and (untracked or ident in counted):
                prev = merge_dt.get(ident)
                if prev is None or dt < prev:
                    merge_dt[ident] = dt
                    merge_week[ident] = wk
        n = _closing_pr(subject)
        if n is None:
            continue
        pr = "PR-%d" % n
        if pr in counted:
            prev = merge_dt.get(pr)
            if prev is None or dt < prev:
                merge_dt[pr] = dt
                merge_week[pr] = wk
    buckets = {}

    def bucket(name, rnd):
        return buckets.setdefault((name, rnd), {"times": [], "builder": [], "guard": [], "pass": []})

    held = set()
    for brief, rnd, when, cause in builders:
        got = bucket(home(brief), rnd)
        got["builder"].append(cause)
        if when:
            got["times"].append(when)
    for ident, rnd, when, cause in guard:
        name = home(ident)
        held.add((name, rnd))
        got = bucket(name, rnd)
        got["guard"].append(cause)
        if when:
            got["times"].append(when)
    pass_best = {}
    for row in pass_rows:
        name = home(row["name"])
        if name not in counted:
            continue
        rnd = row["round"]
        got = bucket(name, rnd)
        got["pass"].append(row["cause"])
        got["times"].append(row["time"])
        if row["kind"] == "review-b" and (name, rnd) in held:
            continue
        key = (name, row["kind"], rnd)
        prev = pass_best.get(key)
        if prev is None or row["time"] < prev:
            pass_best[key] = row["time"]
    for ident, rnd, when, _cause in guard:
        if when is None:
            continue
        name = home(ident)
        key = (name, "review-b", rnd)
        prev = pass_best.get(key)
        if prev is None or when < prev:
            pass_best[key] = when
    later = []
    for (_name, rnd), got in buckets.items():
        if rnd < 2 or not got["times"]:
            continue
        when = min(got["times"])
        if _iso_week(when) not in weeks_set:
            continue
        cause = _first_stated(got["builder"])
        if cause is None:
            cause = _first_stated(got["guard"])
        if cause is None:
            cause = _first_stated(got["pass"])
        later.append(cause or "unstated")
    by_week = {}
    for (_name, kind, _rnd), when in pass_best.items():
        wk = _iso_week(when)
        if wk not in weeks_set:
            continue
        cell = by_week.setdefault(wk, {})
        cell[kind] = cell.get(kind, 0) + 1
    return starts, start_dt, merge_week, merge_dt, later, _format_pass_lines(by_week, weeks)


def _entry_is_link(entry):
    if entry.is_symlink():
        return True
    is_junction = getattr(entry, "is_junction", None)
    if is_junction and is_junction():
        return True
    return False


def _parse_transcript_record(line):
    try:
        o = json.loads(line)
    except (ValueError, TypeError, RecursionError):
        return None
    if not isinstance(o, dict) or o.get("type") != "assistant":
        return None
    msg = o.get("message")
    if not isinstance(msg, dict):
        return None
    mid = msg.get("id")
    if not isinstance(mid, str):
        return None
    usage = msg.get("usage")
    if not isinstance(usage, dict):
        return None
    total = 0
    for f in USAGE_FIELDS:
        v = usage.get(f)
        if v is None:
            continue
        if type(v) is not int or v < 0 or v > 10 ** 12:
            return None
        total += v
    ts = o.get("timestamp")
    if not isinstance(ts, str):
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        else:
            dt = dt.astimezone(datetime.timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None
    return mid, dt, total


def _read_line_capped(f, cap, past_deadline):
    if past_deadline():
        return _READ_LINE_TIMED_OUT
    line = f.readline(cap + 1)
    if line == "":
        return ""
    if len(line) > cap and not line.endswith("\n"):
        while line and not line.endswith("\n"):
            if past_deadline():
                return _READ_LINE_TIMED_OUT
            chunk = f.readline(65536)
            if chunk == "":
                break
            line = chunk
        return None
    if len(line) > cap:
        return None
    return line


def _walk_key_dir(key_dir, deadline, file_handler, counts):
    """Walk key_dir without following links; counts [session, subagent] files seen."""
    stack = [key_dir]
    key_norm = os.path.normcase(os.path.abspath(key_dir))
    while stack:
        if datetime.datetime.now(datetime.timezone.utc) > deadline:
            return "timeout"
        dirpath = stack.pop()
        if datetime.datetime.now(datetime.timezone.utc) > deadline:
            return "timeout"
        try:
            with os.scandir(dirpath) as it:
                for entry in it:
                    if datetime.datetime.now(datetime.timezone.utc) > deadline:
                        return "timeout"
                    if entry.name.startswith("."):
                        continue
                    if _entry_is_link(entry):
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if datetime.datetime.now(datetime.timezone.utc) > deadline:
                            return "timeout"
                        stack.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        if datetime.datetime.now(datetime.timezone.utc) > deadline:
                            return "timeout"
                        path = entry.path
                        rel = os.path.normcase(os.path.abspath(path))
                        if not rel.startswith(key_norm):
                            continue
                        parent = os.path.basename(os.path.dirname(path))
                        base = os.path.basename(path)
                        if not base.endswith(".jsonl"):
                            continue
                        if os.path.dirname(path) == key_dir:
                            counts[0] += 1
                        elif parent == "subagents":
                            counts[1] += 1
                        else:
                            continue
                        err = file_handler(path)
                        if err:
                            return err
        except OSError:
            continue
    return None


def _read_tokens(home, keys, weeks_set, timeout=None):
    if timeout is None:
        timeout = SESSION_READ_LIMIT
    deadline = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=timeout)
    if timeout <= 0:
        return {}, 0, 0, "timeout"
    best = {}
    session_count = 0
    subagent_count = 0

    def handle_file(path):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                while True:
                    if datetime.datetime.now(datetime.timezone.utc) > deadline:
                        return "timeout"
                    line = _read_line_capped(
                        f, LINE_CAP, lambda: datetime.datetime.now(datetime.timezone.utc) > deadline
                    )
                    if line is _READ_LINE_TIMED_OUT:
                        return "timeout"
                    if line == "":
                        break
                    if line is None:
                        continue
                    rec = _parse_transcript_record(line)
                    if rec is None:
                        continue
                    mid, dt, total = rec
                    wk = _iso_week(dt)
                    if wk not in weeks_set:
                        continue
                    prev = best.get((wk, mid))
                    if prev is None or total > prev:
                        best[(wk, mid)] = total
        except OSError:
            pass
        return None

    for key in keys:
        key_dir = os.path.join(home, ".claude", "projects", key)
        if not os.path.isdir(key_dir):
            continue
        counts = [0, 0]
        err = _walk_key_dir(key_dir, deadline, handle_file, counts)
        session_count += counts[0]
        subagent_count += counts[1]
        if err == "timeout":
            return {}, session_count, subagent_count, "timeout"

    by_week = {}
    for (wk, _), total in best.items():
        by_week[wk] = by_week.get(wk, 0) + total
    return by_week, session_count, subagent_count, None


def _fmt_num(n):
    if n is None:
        return ""
    if isinstance(n, float):
        if abs(n - round(n)) < 0.001:
            return str(int(round(n)))
        return "%.1f" % n
    return str(n)


def _fmt_tokens(millions):
    if millions is None:
        return ""
    return "%.2f" % millions


def _project_section(name, root, weeks, ceiling, with_tokens, home, er):
    ws = os.path.join(root, "Workspace")
    common = os.path.join(ws, ".git")
    aname = _ascii_name(name)
    lines = ["# %s" % aname, ""]
    status, ls_out, code = _git(ws, ["ls-files", "handoff/"])
    if status == "timeout":
        return None, ("timeout", "git ls-files handoff/")
    if status == "start":
        return None, ("start", "git ls-files handoff/")
    if status == "fail":
        return None, ("fail", "git ls-files handoff/", code)
    untracked = _handoff_untracked(ls_out)
    brief_ids = _ids_with_brief(ls_out)

    status, commits, code = _commits(ws)
    if status != "ok":
        return None, (status, _COMMIT_LOG_CMD, code)

    status, hardening, code = _hardening_by_week(ws)
    if status == "timeout":
        return None, ("timeout", "git log refs/heads/main --numstat docs/HARDENING.md")
    if status == "start":
        return None, ("start", "git log refs/heads/main --numstat docs/HARDENING.md")
    if status == "fail":
        return None, ("fail", "git log refs/heads/main --numstat docs/HARDENING.md", code)

    starts, start_dt, merge_week, merge_dt, later_causes, pass_lines = _pace_names(
        ws, common, brief_ids, untracked, commits, weeks
    )

    rounds_cache = {}
    if not untracked:
        round_ids = set(brief_ids)
        round_ids.update(_rounds_file_ids(common))
        round_ids.update(merge_week)
        for ident in round_ids:
            rounds_cache[ident] = _rounds_for_id(ws, common, ident, brief_ids)

    week_rows = {
        wk: {"started": 0, "merged": 0, "rounds": [], "days": [], "hardening": hardening.get(wk, 0)}
        for wk in weeks
    }

    for ident, wk in starts.items():
        if wk is None:
            continue
        if wk in week_rows:
            week_rows[wk]["started"] += 1

    for ident, mw in merge_week.items():
        if mw in week_rows:
            week_rows[mw]["merged"] += 1
            if not untracked and _has_rounds_reading(ws, common, ident, brief_ids):
                week_rows[mw]["rounds"].append(rounds_cache.get(ident, 0))
            st = start_dt.get(ident)
            mt = merge_dt.get(ident)
            if st and mt and st.date() <= mt.date():
                week_rows[mw]["days"].append((mt.date() - st.date()).days)

    tokens_by_week = {}
    session_files = 0
    subagent_files = 0
    token_note = ""
    if with_tokens:
        tokens_by_week, session_files, subagent_files, tok_err = _read_tokens(
            home, er.project_keys(name, root), set(weeks)
        )
        if tok_err == "timeout":
            token_note = "pace-report: %s: session read reached the %d second limit" % (aname, SESSION_READ_LIMIT)
            tokens_by_week = {}

    if with_tokens:
        lines.append(
            "Token sources: %d session file(s), %d subagent file(s)"
            % (session_files, subagent_files)
        )
        lines.append("")

    hdr = [
        "Week",
        "Started",
        "Merged",
        "Rounds (mean / max)",
        "Mean days to merge",
        "HARDENING lines landing on main",
    ]
    if with_tokens:
        hdr.append("Tokens (M): " + ", ".join(USAGE_FIELDS))
        hdr.append("Tokens per merged (M)")
    lines.append("| " + " | ".join(hdr) + " |")
    sep = "| --- | --- | --- | --- | --- | --- |"
    if with_tokens:
        sep += " --- | --- |"
    lines.append(sep)

    totals = {"started": 0, "merged": 0, "hardening": 0, "tokens": 0.0}

    for wk in weeks:
        row = week_rows[wk]
        totals["started"] += row["started"]
        totals["merged"] += row["merged"]
        totals["hardening"] += row["hardening"]
        if untracked:
            started_s = UNTRACKED_HANDOFF
            rounds_s = UNTRACKED_HANDOFF
        else:
            started_s = _fmt_num(row["started"]) if row["started"] else "0"
            if row["rounds"]:
                mean_r = sum(row["rounds"]) / len(row["rounds"])
                max_r = max(row["rounds"])
                rounds_s = "%s / %s" % (_fmt_num(mean_r), _fmt_num(max_r))
            elif row["merged"]:
                rounds_s = ""
            else:
                rounds_s = ""
        if row["days"]:
            days_s = _fmt_num(sum(row["days"]) / len(row["days"]))
        else:
            days_s = ""
        hard_s = _fmt_num(row["hardening"]) if row["hardening"] else "0"
        cells = [
            "%d-W%02d" % (wk[0], wk[1]),
            started_s,
            _fmt_num(row["merged"]) if row["merged"] else "0",
            rounds_s,
            days_s,
            hard_s,
        ]
        if with_tokens:
            tok_m = tokens_by_week.get(wk)
            if tok_m is not None and tok_m > 0:
                tm = tok_m / 1_000_000.0
                totals["tokens"] += tm
                cells.append(_fmt_tokens(tm))
                if row["merged"]:
                    cells.append(_fmt_tokens(tm / row["merged"]))
                else:
                    cells.append("")
            else:
                cells.append("")
                cells.append("")
        lines.append("| " + " | ".join(cells) + " |")

    if untracked:
        t_started = UNTRACKED_HANDOFF
        t_rounds = UNTRACKED_HANDOFF
    else:
        t_started = _fmt_num(totals["started"])
        t_rounds_mean = ""
        t_rounds_max = ""
        all_rounds = []
        for wk in weeks:
            all_rounds.extend(week_rows[wk]["rounds"])
        if all_rounds:
            t_rounds_mean = _fmt_num(sum(all_rounds) / len(all_rounds))
            t_rounds_max = _fmt_num(max(all_rounds))
        t_rounds = ("%s / %s" % (t_rounds_mean, t_rounds_max)) if t_rounds_mean else ""
    t_days = []
    for wk in weeks:
        t_days.extend(week_rows[wk]["days"])
    t_days_s = _fmt_num(sum(t_days) / len(t_days)) if t_days else ""
    t_cells = [
        "Total",
        t_started,
        _fmt_num(totals["merged"]),
        t_rounds,
        t_days_s,
        _fmt_num(totals["hardening"]),
    ]
    if with_tokens:
        t_cells.append(_fmt_tokens(totals["tokens"]) if totals["tokens"] else "")
        t_cells.append("")
    lines.append("| " + " | ".join(t_cells) + " |")
    lines.append("")

    if token_note:
        lines.append(token_note)
        lines.append("")

    over = []
    stage = []
    all_ids = set(brief_ids)
    all_ids.update(_rounds_file_ids(common))
    rounds_keys = set(_rounds_file_ids(common))
    for ident in sorted(all_ids):
        is_stage = ident.startswith("STAGE-")
        rnd = (
            rounds_cache.get(ident, 0)
            if not untracked
            else _rounds_for_id(ws, common, ident, brief_ids)
        )
        if ident not in brief_ids and not is_stage:
            continue
        if is_stage and ident not in rounds_keys:
            continue
        mw = merge_week.get(ident)
        in_window = mw in weeks if mw else True
        if rnd <= ceiling or not (in_window or mw is None):
            continue
        if is_stage:
            stage.append((ident, rnd))
        else:
            over.append((ident, rnd))

    for ident, rnd in over + stage:
        lifts = _lift_map(ws, common, ident)
        parts = ["%s: %d rounds" % (_ascii_name(ident), rnd)]
        for r in range(ceiling + 1, rnd + 1):
            lv = lifts.get(r, "unknown")
            parts.append("r%d %s" % (r, lv))
        lines.append("- " + "; ".join(parts))

    extra = []
    if later_causes:
        extra.append(_format_cause_line(later_causes))
    extra.extend(pass_lines)
    extra.extend(_model_lines(ws, set(weeks)))
    if extra:
        if over or stage:
            lines.append("")
        lines.extend(extra)

    unknown_starts = [
        i
        for i in brief_ids
        if i in starts and starts.get(i) is None and not untracked and (merge_week.get(i) in weeks or merge_week.get(i) is None)
    ]
    if unknown_starts and not untracked:
        lines.append("")
        lines.append("Starts unknown: " + ", ".join(sorted(_ascii_name(i) for i in unknown_starts)))

    return "\n".join(lines) + "\n", None


def _default_roots(er):
    roots = []
    seen = set()
    for path in er.PROJECTS.values():
        ab = os.path.normcase(os.path.abspath(path))
        if ab in seen:
            continue
        seen.add(ab)
        roots.append((os.path.basename(path), path))
    br = er.bridge_root()
    ab = os.path.normcase(os.path.abspath(br))
    if ab not in seen:
        roots.append((os.path.basename(br), br))
    return roots


def _is_project(root):
    ws = os.path.join(root, "Workspace")
    return os.path.isdir(ws) and os.path.isdir(os.path.join(ws, ".git"))


def _git_failure_line(kind, cmd, code=None):
    if kind == "timeout":
        return "git command timed out after %d seconds: %s" % (GIT_LIMIT, cmd)
    if kind == "start":
        return "git command could not start: %s" % cmd
    return "git command failed (exit %s): %s" % (code, cmd)


def main():
    ap = build_parser()
    a = ap.parse_args()
    weeks_n = a.weeks if a.weeks is not None else 8
    ceiling = a.ceiling if a.ceiling is not None else bridge_env.REVIEW_ROUNDS
    if weeks_n < 1 or weeks_n > 520:
        print("pace-report: --weeks must be an integer from 1 to 520", file=sys.stderr)
        return 2
    if ceiling < 1 or ceiling > 100:
        print("pace-report: --ceiling must be an integer from 1 to 100", file=sys.stderr)
        return 2
    home = os.path.expanduser(a.home) if a.home else os.path.expanduser("~")
    er = _load_evaluate_reports()
    if a.roots:
        roots = [(os.path.basename(os.path.abspath(r)), os.path.abspath(r)) for r in a.roots]
        for _, root in roots:
            if not _is_project(root):
                print(
                    "pace-report: not a project root (needs Workspace/.git): %s" % root,
                    file=sys.stderr,
                )
                return 2
    else:
        roots = _default_roots(er)

    weeks = _week_range(weeks_n)
    out_parts = []
    exit_code = 0
    for name, root in roots:
        aname = _ascii_name(name)
        if not os.path.isdir(root):
            out_parts.append("# %s\n\n(not present on this computer)\n" % aname)
            continue
        if not _is_project(root):
            out_parts.append("# %s\n\n(not a project: no Workspace/.git)\n" % aname)
            continue
        text, err = _project_section(name, root, weeks, ceiling, a.tokens, home, er)
        if text is None:
            if len(err) == 3:
                kind, cmd, code = err
            else:
                kind, cmd = err
                code = None
            msg = _git_failure_line(kind, cmd, code)
            print("pace-report: %s: %s" % (aname, msg), file=sys.stderr)
            out_parts.append("# %s\n\n(%s)\n" % (aname, msg))
            exit_code = 1
            continue
        out_parts.append(text)

    sys.stdout.write("".join(out_parts))
    return exit_code


if __name__ == "__main__":
    sys.exit(main() or 0)
