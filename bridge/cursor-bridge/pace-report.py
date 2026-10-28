#!/usr/bin/env python3
"""pace-report: read-only weekly pace table per project (R-044).

  python pace-report.py [<project root>...] [--weeks <n>] [--ceiling <n>] [--tokens] [--home <folder>]

Run from any folder. ASCII output only; writes nothing. A project root holds Workspace/ with its
own .git. With no roots, the roots are evaluate-reports.py's PROJECTS plus the bridge root found
like that program. Defaults for --weeks (8), --ceiling (bridge_env.REVIEW_ROUNDS), and --home (~)
are resolved in main(), not in the parser.

Columns per ISO week (UTC): increments started (earliest launcher brief row or guard round with
a time, else unknown), merged (squash subjects on main via bridge_env's reader and
GRAMMAR_ID_PATTERN; with a tracked handoff/ only IDs that have a brief, with handoff/ untracked
every ID the reader finds), rounds mean and max among merges that week, mean
days from known start to merge, docs/HARDENING.md lines added on main that week (added lines only).
A total row follows. Below the table, IDs over --ceiling with round counts and lifts (class, owner,
none, unknown), then stage reviews (STAGE-<name>). With --tokens, token millions (sum of
input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens per message id,
greatest total kept) from ~/.claude/projects/<key>/*.jsonl and <key>/**/subagents/*.jsonl for keys
from evaluate-reports.py's project_keys, plus tokens per merged increment.

Sources: git log on Workspace/main (committer week), run/launcher/runs.jsonl, .git/bridge/rounds-*.json,
handoff/*.md and *-report.md, run/review/REVIEW-*.err, docs/HARDENING.md numstat, session jsonl.
Untracked handoff/ (git ls-files): started and rounds show n/a (handoff/ untracked); merged counts
every ID the reader finds in squash subjects.
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
        merged = bridge_env.squash_merged_ids_from_lines(
            body, bridge_env.GRAMMAR_ID_PATTERN, plan_style=False
        )
        commits.append((dt, merged))
    commits.reverse()
    return "ok", commits, None


def _hardening_by_week(ws):
    status, out, code = _git(
        ws,
        ["log", "main", "--format=%ct", "--numstat", "--", "docs/HARDENING.md"],
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
        return None, ("timeout", "git log main --numstat docs/HARDENING.md")
    if status == "start":
        return None, ("start", "git log main --numstat docs/HARDENING.md")
    if status == "fail":
        return None, ("fail", "git log main --numstat docs/HARDENING.md", code)

    merge_week = {}
    merge_dt = {}
    for dt, merged in commits:
        wk = _iso_week(dt)
        for ident in merged:
            if untracked or ident in brief_ids:
                prev = merge_dt.get(ident)
                if prev is None or dt < prev:
                    merge_dt[ident] = dt
                    merge_week[ident] = wk

    starts = {}
    for ident in brief_ids:
        if untracked:
            continue
        t = _start_times(ws, common, ident)
        if t is None:
            starts[ident] = None
        else:
            starts[ident] = _iso_week(t)

    rounds_cache = {}
    if not untracked:
        round_ids = set(brief_ids)
        round_ids.update(_rounds_file_ids(common))
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
            st = starts.get(ident)
            if st is not None:
                start_dt = _start_times(ws, common, ident)
                if start_dt:
                    for dt, merged in commits:
                        if ident in merged and _iso_week(dt) == mw:
                            if start_dt.date() <= dt.date():
                                days = (dt.date() - start_dt.date()).days
                                week_rows[mw]["days"].append(days)
                            break

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

    unknown_starts = [
        i
        for i in brief_ids
        if starts.get(i) is None and not untracked and (merge_week.get(i) in weeks or merge_week.get(i) is None)
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
