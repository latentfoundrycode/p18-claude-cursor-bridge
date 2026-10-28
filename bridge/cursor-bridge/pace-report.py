#!/usr/bin/env python3
"""pace-report: read-only weekly pace table per project (R-044).

  python pace-report.py [<project root>...] [--weeks <n>] [--ceiling <n>] [--tokens] [--home <folder>]

Run from any folder. ASCII output only; writes nothing. A project root holds Workspace/ with its
own .git. With no roots, the roots are evaluate-reports.py's PROJECTS plus the bridge root found
like that program. Defaults for --weeks (8), --ceiling (bridge_env.REVIEW_ROUNDS), and --home (~)
are resolved in main(), not in the parser.

Columns per ISO week (UTC): increments started (earliest launcher brief row or guard round with
a time, else unknown), merged (squash subjects on main via bridge_env's reader and
GRAMMAR_ID_PATTERN, for IDs that have a brief), rounds mean and max among merges that week, mean
days from known start to merge, docs/HARDENING.md lines added on main that week (added lines only).
A total row follows. Below the table, IDs over --ceiling with round counts and lifts (class, owner,
none, unknown), then stage reviews (STAGE-<name>). With --tokens, token millions (sum of
input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens per message id,
greatest total kept) from ~/.claude/projects/<key>/*.jsonl and <key>/**/subagents/*.jsonl for keys
from evaluate-reports.py's project_keys, plus tokens per merged increment.

Sources: git log on Workspace/main (committer week), run/launcher/runs.jsonl, .git/bridge/rounds-*.json,
handoff/*.md and *-report.md, run/review/REVIEW-*.err, docs/HARDENING.md numstat, session jsonl.
Untracked handoff/ (git ls-files): started and rounds show n/a (handoff/ untracked); merged still counts.
Every git command is read-only with a 120-second limit; session folder reads use the same limit per project.

Exit 0 when done; 1 when a project's git command hits the limit (others still printed); 2 for usage
or a given root that is not a project.
"""
import argparse
import datetime
import glob
import importlib.util
import json
import os
import re
import subprocess
import sys

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
_REVIEW_ERR_RX = re.compile(r"^REVIEW-(.+)\.err$", re.I)
_ERR_R_RX = re.compile(r"-r([1-9][0-9]*)$", re.I)


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


def _iso_week(dt):
    y, w, _ = dt.date().isocalendar()
    return (y, w)


def _week_range(n):
    now = datetime.datetime.now(datetime.timezone.utc)
    monday = datetime.datetime.combine(
        now.date() - datetime.timedelta(days=now.weekday()),
        datetime.time(0, 0),
        tzinfo=datetime.timezone.utc,
    )
    return [ _iso_week(monday - datetime.timedelta(weeks=k)) for k in range(n) ]


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


def _git(ws, args, timeout=GIT_LIMIT):
    try:
        p = subprocess.run(
            ["git", "-C", ws] + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=NO_WINDOW,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "timeout", None
    except OSError:
        return "error", None
    if p.returncode != 0:
        return "fail", None
    return "ok", p.stdout


def _handoff_untracked(ws, ls_out):
    handoff = os.path.join(ws, "handoff")
    if not os.path.isdir(handoff):
        return False
    listed = set(line.replace("\\", "/").strip() for line in (ls_out or "").splitlines() if line.strip())
    for name in os.listdir(handoff):
        if name.endswith(".md") and ("handoff/" + name) not in listed:
            return True
    return False


def _ids_with_brief(ws):
    ids = set()
    handoff = os.path.join(ws, "handoff")
    if not os.path.isdir(handoff):
        return ids
    for name in os.listdir(handoff):
        if not name.endswith(".md") or bridge_env.HANDOFF_REPORT_NAME.search(name):
            continue
        parsed = bridge_env.parse_review_name(name[:-3])
        if parsed:
            ids.add(parsed[0])
    return ids


def _has_brief_file(ws, token):
    return os.path.isfile(os.path.join(ws, "handoff", "%s.md" % token))


def _letter_err_belongs(ws, id_part, token):
    if token == id_part:
        return True
    if token.startswith(id_part) and len(token) > len(id_part):
        extra = token[len(id_part) :]
        if re.fullmatch(r"[a-z]+", extra):
            if _has_brief_file(ws, token):
                return False
            return _has_brief_file(ws, id_part)
    if "-r" in token:
        return False
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


def _err_rounds(ws, id_part):
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
        if _letter_err_belongs(ws, id_part, token):
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


def _rounds_for_id(ws, common, id_part):
    return max(_report_rounds(ws, id_part), _err_rounds(ws, id_part), _guard_rounds(common, id_part))


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
    status, out = _git(ws, ["log", "main", "--format=%ct%x1f%s%x1f%(trailers:key=Merges,valueonly)"])
    if status != "ok":
        return status, None
    commits = []
    for line in out.splitlines():
        parts = line.split("\x1f", 2)
        if len(parts) < 2:
            continue
        try:
            ts = int(parts[0])
        except ValueError:
            continue
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        subject = parts[1]
        trailer = parts[2] if len(parts) > 2 else ""
        lines = [subject]
        if trailer:
            lines.append(trailer)
        merged = bridge_env.squash_merged_ids_from_lines(lines, bridge_env.GRAMMAR_ID_PATTERN, plan_style=False)
        commits.append((dt, merged))
    return "ok", commits


def _hardening_by_week(ws):
    status, out = _git(
        ws,
        ["log", "main", "--format=%ct", "--numstat", "--", "docs/HARDENING.md"],
    )
    if status != "ok":
        return status, None
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
        wk = _iso_week(datetime.datetime.fromtimestamp(cur_ts, tz=datetime.timezone.utc))
        by_week[wk] = by_week.get(wk, 0) + added
    return "ok", by_week


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


def _session_paths(home, keys):
    paths = []
    for key in keys:
        base = os.path.join(home, ".claude", "projects", key)
        paths.extend(glob.glob(os.path.join(base, "*.jsonl")))
        paths.extend(glob.glob(os.path.join(base, "**", "subagents", "*.jsonl"), recursive=True))
    return sorted(set(paths))


def _read_tokens(home, keys, weeks_set, timeout=None):
    if timeout is None:
        timeout = SESSION_READ_LIMIT
    best = {}
    found_keys = []
    for key in keys:
        if os.path.isdir(os.path.join(home, ".claude", "projects", key)):
            found_keys.append(key)
    if timeout <= 0:
        return {}, found_keys, "timeout"
    paths = _session_paths(home, keys)
    if not paths:
        return {}, found_keys, None
    deadline = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=timeout)
    for path in paths:
        if datetime.datetime.now(datetime.timezone.utc) > deadline:
            return {}, found_keys, "timeout"
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    if datetime.datetime.now(datetime.timezone.utc) > deadline:
                        return {}, found_keys, "timeout"
                    try:
                        o = json.loads(line)
                    except ValueError:
                        continue
                    if o.get("type") != "assistant":
                        continue
                    msg = o.get("message") or {}
                    usage = msg.get("usage") or {}
                    try:
                        total = sum(int(usage.get(f) or 0) for f in USAGE_FIELDS)
                    except (TypeError, ValueError):
                        continue
                    mid = msg.get("id")
                    if not mid:
                        continue
                    ts = str(o.get("timestamp") or "")
                    try:
                        if ts.endswith("Z"):
                            dt = datetime.datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(
                                tzinfo=datetime.timezone.utc
                            )
                        else:
                            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    wk = _iso_week(dt)
                    if wk not in weeks_set:
                        continue
                    prev = best.get((wk, mid))
                    if prev is None or total > prev:
                        best[(wk, mid)] = total
        except OSError:
            continue
    by_week = {}
    for (wk, _), total in best.items():
        by_week[wk] = by_week.get(wk, 0) + total
    return by_week, found_keys, None


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
    lines = ["# %s" % name, ""]
    git_fail = None
    status, ls_out = _git(ws, ["ls-files", "handoff/"])
    if status == "timeout":
        return None, "git ls-files handoff/"
    if status != "ok":
        ls_out = ""
    untracked = _handoff_untracked(ws, ls_out)
    brief_ids = _ids_with_brief(ws)

    status, commits = _commits(ws)
    if status == "timeout":
        return None, "git log main"
    if status != "ok":
        return None, "git log main"

    status, hardening = _hardening_by_week(ws)
    if status == "timeout":
        return None, "git log main --numstat docs/HARDENING.md"
    if status != "ok":
        hardening = {}

    merge_week = {}
    for dt, merged in commits:
        wk = _iso_week(dt)
        for ident in merged:
            if ident in brief_ids:
                merge_week.setdefault(ident, wk)

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
        round_ids.update(bridge_env._read_rounds_files(common).keys())
        for ident in round_ids:
            rounds_cache[ident] = _rounds_for_id(ws, common, ident)

    week_rows = {wk: {"started": 0, "merged": 0, "rounds": [], "days": [], "hardening": hardening.get(wk, 0)}
                 for wk in weeks}

    for ident, wk in starts.items():
        if wk is None:
            continue
        if wk in week_rows:
            week_rows[wk]["started"] += 1

    for ident, wk in merge_week.items():
        if wk in week_rows:
            week_rows[wk]["merged"] += 1
            if not untracked:
                week_rows[wk]["rounds"].append(rounds_cache.get(ident, 0))
            st = starts.get(ident)
            if st is not None and starts.get(ident) is not None:
                start_dt = _start_times(ws, common, ident)
                if start_dt:
                    for dt, merged in commits:
                        if ident in merged and _iso_week(dt) == wk:
                            days = (dt.date() - start_dt.date()).days
                            week_rows[wk]["days"].append(days)
                            break

    tokens_by_week = {}
    token_keys = []
    token_note = ""
    if with_tokens:
        tokens_by_week, token_keys, tok_err = _read_tokens(home, er.project_keys(name, root), set(weeks))
        if tok_err == "timeout":
            token_note = "pace-report: %s: session read reached the 120 second limit" % name
            tokens_by_week = {}

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
        cells = ["%d-W%02d" % (wk[0], wk[1]), started_s, _fmt_num(row["merged"]) if row["merged"] else "0",
                 rounds_s, days_s, hard_s]
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

    t_rounds_mean = ""
    t_rounds_max = ""
    all_rounds = []
    for wk in weeks:
        all_rounds.extend(week_rows[wk]["rounds"])
    if all_rounds:
        t_rounds_mean = _fmt_num(sum(all_rounds) / len(all_rounds))
        t_rounds_max = _fmt_num(max(all_rounds))
    t_days = []
    for wk in weeks:
        t_days.extend(week_rows[wk]["days"])
    t_days_s = _fmt_num(sum(t_days) / len(t_days)) if t_days else ""
    t_cells = ["Total", _fmt_num(totals["started"]), _fmt_num(totals["merged"]),
               ("%s / %s" % (t_rounds_mean, t_rounds_max)) if t_rounds_mean else "",
               t_days_s, _fmt_num(totals["hardening"])]
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
    all_ids.update(bridge_env._read_rounds_files(common).keys())
    for ident in sorted(all_ids):
        is_stage = ident.startswith("STAGE-")
        rnd = rounds_cache.get(ident, 0) if not untracked else _rounds_for_id(ws, common, ident)
        if ident not in brief_ids and not is_stage:
            continue
        if is_stage and ident not in bridge_env._read_rounds_files(common):
            continue
        mw = merge_week.get(ident)
        in_window = mw in weeks if mw else True
        if rnd <= ceiling or not (in_window or mw is None):
            continue
        if is_stage:
            stage.append((ident, rnd))
        else:
            over.append((ident, rnd))

    for ident, rnd in over:
        lifts = _lift_map(ws, common, ident)
        parts = ["%s: %d rounds" % (ident, rnd)]
        for r in range(ceiling + 1, rnd + 1):
            lv = lifts.get(r, "unknown")
            parts.append("r%d %s" % (r, lv))
        lines.append("- " + "; ".join(parts))
    for ident, rnd in stage:
        lifts = _lift_map(ws, common, ident)
        parts = ["%s: %d rounds" % (ident, rnd)]
        for r in range(ceiling + 1, rnd + 1):
            lv = lifts.get(r, "unknown")
            parts.append("r%d %s" % (r, lv))
        lines.append("- " + "; ".join(parts))

    unknown_starts = [i for i in brief_ids if starts.get(i) is None and not untracked
                      and (merge_week.get(i) in weeks or merge_week.get(i) is None)]
    if unknown_starts and not untracked:
        lines.append("")
        lines.append("Starts unknown: " + ", ".join(sorted(unknown_starts)))

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
    else:
        roots = _default_roots(er)

    for _, root in roots:
        if not _is_project(root):
            print("pace-report: not a project root (needs Workspace/.git): %s" % root, file=sys.stderr)
            return 2

    weeks = _week_range(weeks_n)
    out_parts = []
    exit_code = 0
    for name, root in roots:
        if not os.path.isdir(root):
            out_parts.append("# %s\n\n(not present on this computer)\n" % name)
            continue
        text, cmd = _project_section(name, root, weeks, ceiling, a.tokens, home, er)
        if text is None:
            print("pace-report: %s: git command timed out after %d seconds: %s" % (name, GIT_LIMIT, cmd), file=sys.stderr)
            out_parts.append("# %s\n\n(git command timed out: %s)\n" % (name, cmd))
            exit_code = 1
            continue
        out_parts.append(text)

    sys.stdout.write("".join(out_parts))
    return exit_code


if __name__ == "__main__":
    sys.exit(main() or 0)
