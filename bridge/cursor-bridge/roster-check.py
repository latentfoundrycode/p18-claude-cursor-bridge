#!/usr/bin/env python3
"""roster-check: resolve which models fill the builder / Review A / Review B roles today,
prove three distinct families, and (optionally) prove each model answers.

  python roster-check.py docs/ROSTER.json [--command "<delegate command>"] [--no-probe] [--out docs/ROSTER.resolved.json] [--run-log run/launcher/runs.jsonl]

docs/ROSTER.json (v2):
{
  "other_pool": "available" | "exhausted",      <- Cursor's "Other Models" usage pool (every
                                                    third-party model). Set automatically by
                                                    --record-failure, restored on reset_day, or
                                                    by the owner (--mark-exhausted/--mark-reset).
                                                    A probe cannot see 1% remaining.
  "review_a": "claude-opus-5-5",                  <- Review A runs in Claude Code, not Cursor.
  "profiles": [                                   <- tried in order; the first usable one wins
    {"name": "full",   "builder": "grok-4.7-high", "review_b": "gpt-5.6-sol-high",
                        "review_b_alt": "composer-2.5"},
    {"name": "native", "builder": "composer-2.5",  "review_b": "grok-4.7-high"}
  ]
}
A model entry is an id string or {"model": id, "family": name, "pool": "native"|"other"}.
Pool is inferred from the id per Cursor's docs: Grok (any effort/host prefix) and Composer are
the "Cursor Models" pool (native); every third-party model is "Other Models".
A profile is skipped when other_pool is "exhausted" and any of its models is in the other
pool. Unless --no-probe, the builder and Review B of a candidate profile are each sent a
one-word request through `cursor-agent -p -f --model <id>`; a refusal, empty reply,
usage-limit message or timeout marks the profile unusable (this catches hard failures only,
never a nearly-empty quota); any other reply counts as answered, off-script. The chosen
profile's three families must be distinct. The result is written to
docs/ROSTER.resolved.json for the delegate and Review B commands to read, and only when it
changes (the time of every check goes to the state file as last_resolved), so a check
before a snapshot leaves the tree clean.
When the Cursor tool itself is signed out, its own sign-in line (the whole of standard output,
or any whole line of standard error) ends the run with SIGN-IN, exit 5, and counts no failure.
A profile may name a second reviewer in review_b_alt. The families that built the branch are
read from run/launcher/runs.jsonl: every builder row of the branch counts (rows marked slot
not free never count). The set is known (a list of families after the clean-rebuild drop rule),
unknown (a line of the record does not parse, or a report file the branch adds has no matching
builder row), empty (no row applies, or the checkout lies in no repository), or cannot be read
(detached head, the record cannot be opened, git does not answer, or a report is present and
the branch's base against main cannot be found): cannot read exits 1 with no REBUILD. Review B is
never of a family in the known built set. When review_b's family built and review_b_alt is
independent and usable, the alternate resolves with a DEVIATION line and a deviation entry (reason
family, unavailable, or the reason given with --review-alt) instead of a rebuild entry. Otherwise
the profile still resolves with a REBUILD line and a rebuild entry when the table says so.
--repair-record  rewrites the run record keeping every line that parses, appends the others to
run/launcher/runs.damaged.jsonl, prints both counts, resolves nothing.
--review-alt <reason>  resolve the alternate on request; reason is one word of ASCII letters and
hyphens; exit 1 when the alternate cannot be resolved (the built set unknown or not readable
among the causes).
--record-failure <model> --stderr-file <path> [--stdout-file <path>]
  Classify a failed cursor-agent call. <model> must be a model id of this roster (a wrong
  argument exits 2 and changes nothing). USAGE-LIMIT (a usage/quota/limit message) or a
  second failure of the same model within 2 hours marks the model's pool exhausted in
  docs/ROSTER.json automatically (auto_exhausted_at / auto_exhausted_reason) and exits 3 =
  "re-resolve and restart the step". A connection error (lost, reset, reconnect, 5xx, 429)
  or a hit run limit (bridge-run's LIMIT line) is not the model's fault: exit 4 = "retry
  the same step once", twice per window, then exit 5 = "stop and tell the owner" (no
  switch helps a dead line). A first other failure is exit 4 too. The counts expire after
  8 hours, longer than any run limit, and --record-success <model> clears them. An
  automatic "unavailable" mark expires after 6 hours; --clear-unavailable <model> removes
  one at once (a wrong mark, e.g. a service outage). The service's `[unavailable]` line is a
  connection error, never the model's failure.
The changing state (pool, marks, counts) is kept in <git common dir>/bridge/roster-state.json,
never in the tracked roster, so a reset of the working tree cannot erase a switch; a roster
from an older release seeds the state file once.
--mark-exhausted   the owner said "usage exhausted": stamp other_pool exhausted now (UTC).
--mark-reset       the owner said "usage reset": restore other_pool and clear marks now.
Automatic reset: "reset_day" (day of month, UTC; e.g. 16) in the roster. When other_pool is
exhausted and the current UTC time is at or past 00:00 UTC of the first reset_day strictly
after exhausted_at, the check restores other_pool to "available" by itself, clears the
unavailable marks and failure counts, and says so. Timestamps are UTC. ROSTER_NOW=<ISO UTC>
overrides "now" for tests.
Exit 0 = resolved; 1 = no usable profile, a family collision, a command mismatch, a built set
that cannot be read, or a refused --review-alt;
2 = cannot read or a wrong model argument; 3 = pool/model marked exhausted, re-resolve;
4 = transient, retry once; 5 = repeated connection failures or time-outs, or the Cursor tool signed out (SIGN-IN), tell the owner.
ASCII-only on purpose.
"""
import datetime
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env  # noqa: E402  (the stripped environment and the cursor-agent launcher, KP-032)

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
FAILURE_WINDOW_HOURS = 8      # failures count as consecutive only within this window (longer than any run limit)
UNAVAILABLE_TTL_HOURS = 6     # an automatic "unavailable" mark expires after this
CONNECTION_RETRIES = 2        # connection failures / time-outs retried this often per window, then exit 5
# The roster's changing state never lives in the tracked docs/ROSTER.json: a reset of the
# working tree would erase it (release 0a review, F1). It lives in the repository's own
# .git/bridge/roster-state.json, which no reset, clean or checkout touches.
STATE_KEYS = ("other_pool", "exhausted_at", "exhausted_reason", "auto_exhausted_at", "auto_exhausted_reason",
              "unavailable", "failures", "connection_failures", "last_reset", "last_resolved")
NL = chr(10)
PROBE_PROMPT = "Reply with exactly the single word OK and nothing else."
PROBE_TIMEOUT = 150
SIGN_IN_PREFIX = "Error: Authentication required. Please run 'agent login' first"
SIGN_IN_LINE = "SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login"


class _ProbeSignInSentinel(object):
    """Distinct falsy value probe returns when the Cursor tool is signed out (not ok, not False)."""

    __slots__ = ()

    def __bool__(self):
        return False


PROBE_SIGN_IN = _ProbeSignInSentinel()  # falsy sentinel; main() tests ``ok is PROBE_SIGN_IN``

FAMILY_PREFIXES = [
    ("claude", "anthropic"), ("anthropic", "anthropic"),
    ("gpt", "openai"), ("o1", "openai"), ("o3", "openai"), ("o4", "openai"), ("openai", "openai"), ("codex", "openai"),
    ("grok", "xai"), ("xai", "xai"),
    ("gemini", "google"), ("google", "google"),
    ("mistral", "mistral"), ("codestral", "mistral"), ("devstral", "mistral"),
    ("llama", "meta"), ("meta", "meta"),
    ("deepseek", "deepseek"),
    ("qwen", "alibaba"), ("kimi", "moonshot"), ("moonshot", "moonshot"),
    ("mimo", "xiaomi"), ("xiaomi", "xiaomi"),
    ("glm", "zhipu"), ("minimax", "minimax"),
    ("composer", "cursor"),
]


def norm_entry(entry):
    if isinstance(entry, dict):
        return entry.get("model", ""), entry.get("family"), entry.get("pool")
    return entry or "", None, None


def current_branch():
    try:
        p = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, creationflags=NO_WINDOW)
        return p.stdout.strip() if p.returncode == 0 else ""
    except OSError:
        return ""


def built_by(run_log, branch=None):
    """The model of the last builder run of the branch under review in the launcher's run log
    (release A4; the log records the branch). None for a branch with no builder run: a design
    review is of a text nothing built, and another branch's builder did not build this change
    (2026.10.25a: the fallback to any branch's last run refused the only usable profile)."""
    try:
        with open(run_log, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    branch = branch or current_branch()
    entries = []
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("kind") == "builder" and e.get("model"):
            if e.get("slot") == "not free":
                continue
            entries.append(e)
    for e in reversed(entries):
        if branch and e.get("branch") == branch:
            return str(e["model"])
    return None


GIT_TIMEOUT = 20
REVIEW_ALT_REASON_RX = re.compile(r"^[a-zA-Z-]+$")
_COMMIT_NAME_RX = re.compile(r"^[0-9a-fA-F]{4,64}$")


def _git_run(args, cwd):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=GIT_TIMEOUT,
                              creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _in_git_repo(cwd):
    p = os.path.abspath(cwd or ".")
    while True:
        if os.path.exists(os.path.join(p, ".git")):
            return True
        parent = os.path.dirname(p)
        if parent == p:
            return False
        p = parent


def _valid_commit_name(name):
    return isinstance(name, str) and _COMMIT_NAME_RX.match(name)


def _commit_exists(sha, cwd):
    p = _git_run(["git", "rev-parse", "--verify", "-q", sha + "^{commit}"], cwd)
    return p is not None and p.returncode == 0


def _git_is_ancestor(ancestor, descendant, cwd):
    p = _git_run(["git", "merge-base", "--is-ancestor", ancestor, descendant], cwd)
    if p is None:
        return None
    return p.returncode == 0


def _brief_from_report(rel_path):
    base = os.path.basename(rel_path.replace("\\", "/"))
    m = re.match(r"^(.+)-r\d+-report\.md$", base)
    return m.group(1) if m else None


def _handoff_reports_on_tree(cwd):
    handoff = os.path.join(cwd, "handoff")
    found = []
    if not os.path.isdir(handoff):
        return found
    for name in os.listdir(handoff):
        if name.endswith("-report.md"):
            found.append(("handoff/" + name).replace("\\", "/"))
    return found


def _reports_at_commit(commit, cwd):
    p = _git_run(["git", "ls-tree", "-r", "--name-only", commit, "handoff"], cwd)
    if p is None or p.returncode != 0:
        return set()
    out = set()
    for line in (p.stdout or "").splitlines():
        line = line.strip().replace("\\", "/")
        if line.endswith("-report.md"):
            out.add(line)
    return out


def _merge_base_with_main(branch, cwd):
    for ref in ("origin/main", "main"):
        p = _git_run(["git", "rev-parse", "--verify", "-q", ref + "^{commit}"], cwd)
        if p is None or p.returncode != 0:
            continue
        main_sha = (p.stdout or "").strip()
        mb = _git_run(["git", "merge-base", branch, main_sha], cwd)
        if mb is None:
            return None, None
        if mb.returncode != 0:
            continue
        base = (mb.stdout or "").strip()
        if base:
            return base, None
    return None, "main"


def _row_valid_start(row, cwd):
    sc = row.get("start_commit")
    if not _valid_commit_name(sc):
        return None
    if not _commit_exists(sc, cwd):
        return None
    return sc


def _apply_drop_rule(rows, cwd):
    """Return rows that survive the clean-rebuild drop rule, in file order, or None if git does not answer."""
    if not rows:
        return []
    kept = []
    for i, row in enumerate(rows):
        dropped = False
        for later in rows[i + 1:]:
            if later.get("clean") is not True:
                continue
            ls = _row_valid_start(later, cwd)
            es = _row_valid_start(row, cwd)
            if ls is None or es is None:
                continue
            if ls == es:
                dropped = True
                break
            ans = _git_is_ancestor(ls, es, cwd)
            if ans is None:
                return None
            if ans:
                dropped = True
                break
        if not dropped:
            kept.append(row)
    return kept


def _roster_builder_families(roster, profiles):
    fams = set()
    for prof in profiles:
        b_id, b_fam_o, _ = norm_entry(prof.get("builder"))
        fam = family_of(b_id, b_fam_o)
        if fam:
            fams.add(fam)
    for role in ("builder",):
        mid, fam_o, _ = norm_entry(roster.get(role))
        if mid:
            fam = family_of(mid, fam_o)
            if fam:
                fams.add(fam)
    return fams


def _parse_run_log_raw(run_log):
    try:
        if os.path.isdir(run_log):
            return None, "runs.jsonl", [], [0]
        with open(run_log, encoding="utf-8") as f:
            raw_lines = f.read().splitlines()
    except OSError:
        if os.path.exists(run_log):
            return None, "runs.jsonl", [], [0]
        return [], None, [], []
    bad = []
    objs = []
    for line in raw_lines:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            bad.append(line)
            continue
        if not isinstance(e, dict):
            bad.append(line)
            continue
        objs.append(e)
    return objs, None, bad, raw_lines


def _branch_builder_rows(entries, branch):
    rows = []
    for e in entries:
        if e.get("kind") != "builder" or not e.get("model"):
            continue
        if e.get("slot") == "not free":
            continue
        if e.get("branch") == branch:
            rows.append(e)
    return rows


def built_families(run_log, branch=None, cwd=None):
    """Families that built the branch, or empty / unknown / unreadable.

    Signature for TASK-086b: built_families(run_log, branch=None, cwd=None) -> dict with
    status, families, unknown_causes, unreadable_cause, parsing_rows, counted_rows, rebuild_end.
    cwd is the folder the branch is read in (default: process cwd).
    """
    cwd = cwd or os.getcwd()
    branch_arg = branch
    result = {"branch": branch or "", "status": "known", "families": set(), "unknown_causes": [],
              "unreadable_cause": None, "parsing_rows": [], "counted_rows": [],
              "rebuild_end": None, "run_log_base": os.path.basename(run_log)}
    if not _in_git_repo(cwd):
        result["status"] = "empty"
        return result
    head_ref = _git_run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if head_ref is None or head_ref.returncode != 0:
        result["status"] = "unreadable"
        result["unreadable_cause"] = "git"
        return result
    ref = (head_ref.stdout or "").strip()
    if ref == "HEAD":
        result["status"] = "unreadable"
        result["unreadable_cause"] = "detached"
        return result
    branch = branch_arg or ref
    result["branch"] = branch
    tree_reports = _handoff_reports_on_tree(cwd)
    if tree_reports:
        base, fail = _merge_base_with_main(branch, cwd)
        if fail:
            result["status"] = "unreadable"
            result["unreadable_cause"] = fail
            return result
        if base is None:
            result["status"] = "unreadable"
            result["unreadable_cause"] = "main"
            return result
        base_reports = _reports_at_commit(base, cwd)
        added_reports = [r for r in tree_reports if r not in base_reports]
    else:
        added_reports = []
    entries, open_fail, bad_lines, _raw = _parse_run_log_raw(run_log)
    if open_fail:
        result["status"] = "unreadable"
        result["unreadable_cause"] = open_fail
        return result
    if entries is None:
        result["status"] = "unreadable"
        result["unreadable_cause"] = "runs.jsonl"
        return result
    parsing_rows = _branch_builder_rows(entries, branch)
    result["parsing_rows"] = list(parsing_rows)
    counted = _apply_drop_rule(parsing_rows, cwd)
    if counted is None:
        result["status"] = "unreadable"
        result["unreadable_cause"] = "git"
        return result
    result["counted_rows"] = counted
    for row in counted:
        fam = family_of(str(row.get("model")))
        if fam:
            result["families"].add(fam)
    unknown = []
    if bad_lines:
        unknown.append(("runs.jsonl", "runs.jsonl"))
        result["rebuild_end"] = "--repair-record"
    for rep in added_reports:
        brief = _brief_from_report(rep)
        if not brief:
            continue
        if not any(r.get("brief") == brief for r in parsing_rows):
            unknown.append((rep, rep))
            if result["rebuild_end"] is None:
                result["rebuild_end"] = "checkpoint"
    if unknown:
        result["status"] = "unknown"
        result["unknown_causes"] = unknown
    elif not counted and not entries and not bad_lines and not added_reports:
        result["status"] = "empty"
        result["families"] = set()
    else:
        result["status"] = "known"
    return result


def _rebuild_needs_new_branch(counted, branch, cwd):
    if not counted:
        return False
    start = None
    for row in counted:
        sc = _row_valid_start(row, cwd)
        if sc:
            start = sc
            break
    if start is None:
        return True
    hypo = {"kind": "builder", "branch": branch, "model": "x", "start_commit": start, "clean": True}
    survived = _apply_drop_rule(counted + [hypo], cwd)
    return len(survived) > 1


def _alt_independent(alt_fam, built_fams, ra_fam):
    return alt_fam and alt_fam != ra_fam and alt_fam not in built_fams


def _parsing_row_families(rows):
    fams = set()
    for row in rows:
        fam = family_of(str(row.get("model")))
        if fam:
            fams.add(fam)
    return fams


def repair_record(run_log):
    entries, open_fail, bad_lines, raw_lines = _parse_run_log_raw(run_log)
    if open_fail or entries is None:
        print("CANNOT REPAIR: cannot read %s" % run_log)
        return 2
    good_objs = []
    bad_lines_ordered = []
    for line in raw_lines:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            if not isinstance(e, dict):
                bad_lines_ordered.append(line)
                continue
        except ValueError:
            bad_lines_ordered.append(line)
            continue
        good_objs.append(line)
    if not bad_lines_ordered:
        print("repair-record  kept %d  moved 0" % len(good_objs))
        return 0
    log_dir = os.path.dirname(os.path.abspath(run_log)) or "."
    base = os.path.basename(run_log)
    tmp = os.path.join(log_dir, base + ".tmp")
    os.makedirs(log_dir, exist_ok=True)
    with open(tmp, "w", encoding="utf-8", newline=NL) as f:
        for line in good_objs:
            f.write(line + NL)
    os.replace(tmp, run_log)
    damaged = os.path.join(log_dir, "runs.damaged.jsonl")
    with open(damaged, "a", encoding="utf-8", newline=NL) as f:
        for line in bad_lines_ordered:
            f.write(line + NL)
    print("repair-record  kept %d  moved %d" % (len(good_objs), len(bad_lines_ordered)))
    return 0


def family_of(model_id, override=None):
    if override:
        return override.lower()
    m = model_id.lower().replace("_", "-").strip()
    core = m[len("cursor-"):] if m.startswith("cursor-") else m   # cursor-grok-* is xAI, hosted by Cursor
    for prefix, fam in FAMILY_PREFIXES:
        if core.startswith(prefix) or ("-" + prefix) in core or ("/" + prefix) in core:
            return fam
    return None


# Pool membership per Cursor's Models & Pricing page (cursor.com/docs/models, read 2026-09-25):
# "The Cursor Models pool includes Grok 4.7, Grok 4.6, Grok 4.5, and Composer 2.5." Every
# third-party model (GPT, Gemini, Claude, GLM, Kimi, ...) draws from "Other Models". Re-check
# the page when a new model appears; an id not matching either list is treated as "other".
NATIVE_MARKERS = ("composer", "grok")


def pool_of(model_id, override=None):
    if override:
        return override.lower()
    m = model_id.lower()
    core = m[len("cursor-"):] if m.startswith("cursor-") else m
    return "native" if any(core.startswith(k) or ("-" + k) in core for k in NATIVE_MARKERS) else "other"


def cursor_agent_cmd():
    """The CLI the way Windows needs it (see bridge_env.cursor_agent_launcher)."""
    return bridge_env.cursor_agent_launcher()


_TRIM_EDGES = " \t\r\n"


def _lf_lines(text):
    if not text:
        return []
    return text.split(NL)


def _trim_line_edges(line):
    return line.strip(_TRIM_EDGES)


def _line_starts_with_sign_in(line):
    return _trim_line_edges(line).startswith(SIGN_IN_PREFIX)


def tool_sign_in_on_stderr(text):
    """True when any whole line of standard error is the tool's sign-in line."""
    for line in _lf_lines(text):
        if _line_starts_with_sign_in(line):
            return True
    return False


def tool_sign_in_on_stdout(text):
    """True when standard output is only the tool's sign-in line (one non-empty trimmed line)."""
    non_empty = []
    for line in _lf_lines(text):
        trimmed = _trim_line_edges(line)
        if trimmed:
            non_empty.append(trimmed)
    return len(non_empty) == 1 and non_empty[0].startswith(SIGN_IN_PREFIX)


def _ascii_line(text):
    return (text or "").encode("ascii", errors="backslashreplace").decode("ascii")


def probe(model_id):
    """Return (ok, detail). ok when the model replied 'OK' (case-insensitive) within the timeout, or
    replied something else that is not a usage-limit message: answered off-script, so the model is
    there (2026.10.25a: a sentence instead of the word printed FAIL, which sends the owner to buy
    usage). A refusal (non-zero exit), an empty reply, a time-out or a usage-limit message is not ok.
    When the Cursor tool is signed out, ok is PROBE_SIGN_IN (falsy, tested by identity in main())."""
    launcher = cursor_agent_cmd()
    if launcher is None:
        return False, "cursor-agent not found (PATH or %LOCALAPPDATA%/cursor-agent)"
    try:
        env = bridge_env.stripped_env()
    except bridge_env.AgentHomeError as e:
        return False, str(e)
    try:
        p = subprocess.run(launcher + ["-p", "-f", "--model", model_id, PROBE_PROMPT],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=PROBE_TIMEOUT, creationflags=NO_WINDOW, env=env)
    except subprocess.TimeoutExpired:
        return False, "timeout after %ds" % PROBE_TIMEOUT
    except FileNotFoundError:
        return False, "cursor-agent launcher not executable: %s" % launcher[0]
    if tool_sign_in_on_stdout(p.stdout or "") or tool_sign_in_on_stderr(p.stderr or ""):
        return PROBE_SIGN_IN, ""
    out = (p.stdout or "").strip()
    if p.returncode == 0 and out.strip().strip(".").upper() == "OK":
        return True, "answered"
    if (p.returncode == 0 and out and classify_failure(out + " " + (p.stderr or ""))[0] == "OTHER"
            and not re.search(r"(?i)\b(error|exception|failed|failure|traceback|unavailable|not available|denied|unauthori[sz]ed|forbidden"
                              r"|invalid|not found|unknown model|cannot use|not supported)\b", out)):
        return True, "answered off-script: %a" % out.replace(NL, " ")[:80]
    err =(p.stderr or "").strip().replace("\n", " ")[:200]
    return False, "exit %d; stdout=%a; stderr=%a" % (p.returncode, out[:80], err)


def now_utc():
    forced = os.environ.get("ROSTER_NOW")
    if forced:
        return datetime.datetime.strptime(forced, "%Y-%m-%dT%H:%M").replace(tzinfo=datetime.timezone.utc)
    return datetime.datetime.now(datetime.timezone.utc)


def stamp(dt):
    return dt.strftime("%Y-%m-%dT%H:%M UTC")


def parse_stamp(text):
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M UTC").replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def next_reset_after(exhausted_at, reset_day):
    """00:00 UTC of the first `reset_day` strictly after exhausted_at."""
    y, m = exhausted_at.year, exhausted_at.month
    candidate = datetime.datetime(y, m, reset_day, tzinfo=datetime.timezone.utc)
    if candidate <= exhausted_at:
        m += 1
        if m == 13:
            y, m = y + 1, 1
        candidate = datetime.datetime(y, m, reset_day, tzinfo=datetime.timezone.utc)
    return candidate


def state_path(roster_path):
    """Where the mutable state lives: <git common dir>/bridge/roster-state.json for a roster
    inside a git checkout; otherwise run/roster-state.json beside the roster's folder."""
    roster_dir = os.path.dirname(os.path.abspath(roster_path)) or "."
    try:
        g = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=roster_dir, capture_output=True,
                           text=True, timeout=20, creationflags=NO_WINDOW)
        if g.returncode == 0 and g.stdout.strip():
            common = g.stdout.strip()
            if not os.path.isabs(common):
                common = os.path.join(roster_dir, common)
            return os.path.join(os.path.abspath(common), "bridge", "roster-state.json")
    except (OSError, subprocess.TimeoutExpired):
        pass
    base = os.path.dirname(roster_dir) if os.path.basename(roster_dir) == "docs" else roster_dir
    return os.path.join(base, "run", "roster-state.json")


def load_roster(path):
    """The tracked configuration merged with the untracked state. A roster written by an
    older release carries state keys in the tracked file: they seed the state file once."""
    with open(path, encoding="utf-8-sig") as f:
        config = json.load(f)
    sp = state_path(path)
    state = None
    if os.path.isfile(sp):
        try:
            with open(sp, encoding="utf-8-sig") as f:
                state = json.load(f)
        except Exception:
            state = None
    if state is None:
        state = {k: config[k] for k in STATE_KEYS if k in config}
        if state:
            print("note  migrated the roster's state out of %s into %s" % (path, sp))
        save_state(path, state)
    roster = {k: v for k, v in config.items() if k not in STATE_KEYS}
    roster.update(state)
    return roster


def save_state(path, roster):
    sp = state_path(path)
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    state = {k: roster[k] for k in STATE_KEYS if k in roster}
    with open(sp, "w", encoding="utf-8", newline=NL) as f:
        json.dump(state, f, indent=2); f.write(NL)


def clear_marks(roster, how):
    roster["other_pool"] = "available"
    for k in ("auto_exhausted_at", "auto_exhausted_reason", "exhausted_at", "exhausted_reason", "unavailable", "failures"):
        roster.pop(k, None)
    roster["last_reset"] = "%s (%s)" % (stamp(now_utc()), how)


def maybe_auto_reset(path, roster):
    """If the pool is exhausted and the reset day has passed since exhaustion, restore it."""
    if (roster.get("other_pool") or "available").lower() != "exhausted":
        return False
    reset_day = roster.get("reset_day")
    ex = parse_stamp(roster.get("exhausted_at") or roster.get("auto_exhausted_at") or "")
    if not reset_day or ex is None:
        return False
    due = next_reset_after(ex, int(reset_day))
    now = now_utc()
    if now >= due:
        clear_marks(roster, "automatic reset: reset_day %d, exhausted %s, due %s" % (int(reset_day), stamp(ex), stamp(due)))
        save_state(path, roster)
        print("AUTO-RESET  other_pool restored to 'available' (reset day %d passed at %s; exhausted since %s)" % (int(reset_day), stamp(due), stamp(ex)))
        return True
    print("note  other_pool exhausted since %s; automatic reset due %s (reset_day %d)" % (stamp(ex), stamp(due), int(reset_day)))
    return False


USAGE_LIMIT_PATTERNS = [
    r"usage[\s-]*limit", r"\busage\b.*\b(exhaust|exceed|reached|used up)", r"\bquota\b.*\b(exhaust|exceed|reached)",
    r"\b(monthly|plan|usage|request|spend(ing)?)\s+limit\b.*\b(reached|exceeded)", r"insufficient (credits|balance|usage)",
    r"no (remaining|more) (credits|usage|requests)", r"upgrade (your )?plan", r"out of (credits|usage)",
    r"spend(ing)? limit", r"\b402\b", r"payment required", r"billing (issue|problem|limit)",
]
# A dropped line is neither the model's fault nor a usage limit: it never counts toward
# "consecutive failures" (KP-034: two reconnects once marked Grok unavailable in both profiles).
CONNECTION_PATTERNS = [
    r"connection (lost|reset|refused|closed|timed out)", r"\becon(nreset|nrefused)\b", r"\betimedout\b",
    r"\benotfound\b", r"network (error|unreachable|is unreachable)", r"reconnect", r"socket hang up",
    r"\b(502|503|504)\b", r"gateway time-?out", r"service unavailable", r"\brate limit",
    r"\b429\b", r"too many requests",
    r"\[unavailable\]",                  # the service's own outage line, `[unavailable] Error ...` (2026.10.25a)
    r"bridge-run: limit \d+s reached",   # the launcher's limit was hit: the run hung, the model did not fail
]


def classify_failure(text):
    """USAGE-LIMIT (the pool is used up), CONNECTION (transient, never counted), or OTHER."""
    t = (text or "").lower()
    for pat in USAGE_LIMIT_PATTERNS:
        if re.search(pat, t):
            return "USAGE-LIMIT", pat
    for pat in CONNECTION_PATTERNS:
        if re.search(pat, t):
            return "CONNECTION", pat
    return "OTHER", ""


def roster_models(roster):
    ids = set()
    rid, _, _ = norm_entry(roster.get("review_a"))
    if rid:
        ids.add(rid)
    for prof in roster.get("profiles") or []:
        for role in ("builder", "review_b"):
            mid, _, _ = norm_entry(prof.get(role))
            if mid:
                ids.add(mid)
    for role in ("builder", "review_b"):
        mid, _, _ = norm_entry(roster.get(role))
        if mid:
            ids.add(mid)
    return ids


def expire_unavailable(roster):
    """Drop automatic 'unavailable' marks older than UNAVAILABLE_TTL_HOURS. Returns the dropped ids."""
    dropped = []
    marks = roster.get("unavailable") or {}
    now = now_utc()
    for mid, note in list(marks.items()):
        when = parse_stamp(str(note)[:len("2026-01-01T00:00 UTC")])     # automatic marks start with their stamp
        if when is not None and (now - when).total_seconds() > UNAVAILABLE_TTL_HOURS * 3600:
            del marks[mid]
            dropped.append(mid)
    if not marks:
        roster.pop("unavailable", None)
    return dropped


def record_failure(path, roster, model, stderr_text="", stdout_text=""):
    """Mark the model's pool exhausted on a usage-limit message or a second consecutive
    failure within FAILURE_WINDOW_HOURS; a connection error is transient and never counted;
    otherwise count it. Writes the roster. Returns the exit code (2, 3, 4 or 5)."""
    if tool_sign_in_on_stderr(stderr_text) or tool_sign_in_on_stdout(stdout_text):
        print(SIGN_IN_LINE)
        return 5
    text = stderr_text + stdout_text
    if model not in roster_models(roster):
        print("CANNOT RECORD: %r is not a model in this roster (%s)" % (model, ", ".join(sorted(roster_models(roster)))))
        print("               the argument after --record-failure must be the model id of the failed call; nothing was changed")
        return 2
    kind, pat = classify_failure(text)
    now = now_utc()
    when = stamp(now)
    excerpt = (text or "").strip().replace(NL, " ")[:300]
    excerpt_out = _ascii_line(excerpt)
    if kind == "CONNECTION":
        conn = roster.setdefault("connection_failures", {})
        prev = conn.get(model)
        count = 1
        if isinstance(prev, dict):
            last = parse_stamp(prev.get("last") or "")
            if last is not None and (now - last).total_seconds() <= FAILURE_WINDOW_HOURS * 3600:
                count = int(prev.get("count", 0)) + 1
        conn[model] = {"count": count, "last": when}
        save_state(path, roster)
        if count > CONNECTION_RETRIES:
            print("ESCALATE   %s: connection failure or time-out %d times in %d hours (%s)." % (model, count, FAILURE_WINDOW_HOURS, pat))
            print("           Not a model problem, so no switch: stop the step, write it on the Awaiting user on: line, and tell the owner.")
            print("           excerpt: %s" % excerpt_out)
            return 5
        print("TRANSIENT  %s: connection error or time-out (%s), %d of %d - retry the same step once." % (model, pat, count, CONNECTION_RETRIES))
        print("           excerpt: %s" % excerpt_out)
        return 4
    failures = roster.setdefault("failures", {})
    prev = failures.get(model)
    count = 1
    if isinstance(prev, dict):
        last = parse_stamp(prev.get("last") or "")
        if last is not None and (now - last).total_seconds() <= FAILURE_WINDOW_HOURS * 3600:
            count = int(prev.get("count", 0)) + 1
    # an integer count was written by an older release with no time stamp: treat it as expired
    failures[model] = {"count": count, "last": when}
    pool = pool_of(model)
    if kind == "USAGE-LIMIT" or count >= 2:
        reason = "usage-limit message (%s)" % pat if kind == "USAGE-LIMIT" else "%d consecutive failures" % count
        if pool == "other":
            roster["other_pool"] = "exhausted"
            roster["exhausted_at"] = when
            roster["auto_exhausted_at"] = when
            roster["auto_exhausted_reason"] = "%s: %s -- %s" % (model, reason, excerpt)
            print("EXHAUSTED  %s (%s pool): %s" % (model, pool, reason))
            print("           other_pool set to 'exhausted' automatically; re-resolve and restart the step.")
        else:
            roster.setdefault("unavailable", {})[model] = "%s: %s -- %s" % (when, reason, excerpt)
            print("UNAVAILABLE  %s (%s pool): %s" % (model, pool, reason))
            print("             marked unavailable in the roster; re-resolve and restart the step.")
        failures.pop(model, None)
        roster.get("connection_failures", {}).pop(model, None)
        code = 3
    else:
        print("TRANSIENT  %s: first failure in %d hours, not a usage-limit message - retry the same step once." % (model, FAILURE_WINDOW_HOURS))
        print("           excerpt: %s" % excerpt_out)
        code = 4
    save_state(path, roster)
    return code


def main():
    argv = sys.argv[1:]
    if not argv or argv[0].startswith("--"):
        print("usage: roster-check.py docs/ROSTER.json [--command ...] [--no-probe] [--out <path>] | --record-failure <model> --stderr-file <path>")
        return 2
    path = argv[0]
    command = argv[argv.index("--command") + 1] if "--command" in argv and argv.index("--command") + 1 < len(argv) else None
    do_probe = "--no-probe" not in argv
    run_log = argv[argv.index("--run-log") + 1] if "--run-log" in argv and argv.index("--run-log") + 1 < len(argv) else os.path.join("run", "launcher", "runs.jsonl")
    out_path = argv[argv.index("--out") + 1] if "--out" in argv and argv.index("--out") + 1 < len(argv) else os.path.join(os.path.dirname(path) or ".", "ROSTER.resolved.json")
    try:
        roster = load_roster(path)
    except Exception as e:
        print("CANNOT VERIFY: cannot read %s (%s)" % (path, e))
        return 2

    if "--mark-exhausted" in argv:
        roster["other_pool"] = "exhausted"
        roster["exhausted_at"] = stamp(now_utc())
        roster["exhausted_reason"] = "owner said usage exhausted"
        save_state(path, roster)
        print("MARKED  other_pool exhausted at %s (owner)" % roster["exhausted_at"])
        return 0
    if "--mark-reset" in argv:
        clear_marks(roster, "owner said usage reset")
        save_state(path, roster)
        print("RESET   other_pool available (owner)")
        return 0
    if "--record-failure" in argv:
        model = argv[argv.index("--record-failure") + 1]
        stderr_text = ""
        stdout_text = ""
        for flag, slot in (("--stderr-file", "stderr"), ("--stdout-file", "stdout")):
            if flag in argv and argv.index(flag) + 1 < len(argv):
                try:
                    chunk = open(argv[argv.index(flag) + 1], encoding="utf-8", errors="replace").read() + "\n"
                    if slot == "stderr":
                        stderr_text = chunk
                    else:
                        stdout_text = chunk
                except OSError:
                    pass
        return record_failure(path, roster, model, stderr_text, stdout_text)

    if "--record-success" in argv:
        model = argv[argv.index("--record-success") + 1]
        changed = (roster.get("failures") or {}).pop(model, None) is not None
        changed = ((roster.get("connection_failures") or {}).pop(model, None) is not None) or changed
        if changed:
            save_state(path, roster)
        print(("ok    failure count cleared for %s" if changed else "ok    no failure count for %s") % model)
        return 0

    if "--clear-unavailable" in argv:
        i = argv.index("--clear-unavailable") + 1
        model = argv[i] if i < len(argv) else ""
        marks = roster.get("unavailable") or {}
        if model not in marks:
            print("ok    no unavailable mark for %r (marked: %s)" % (model, ", ".join(sorted(marks)) or "none"))
            return 0 if model in roster_models(roster) else 2
        del marks[model]
        if not marks:
            roster.pop("unavailable", None)
        (roster.get("failures") or {}).pop(model, None)
        save_state(path, roster)
        print("CLEARED  the unavailable mark of %s (a wrong mark, e.g. a service outage) - re-resolve" % model)
        return 0

    if "--repair-record" in argv:
        return repair_record(run_log)

    review_alt_reason = None
    if "--review-alt" in argv:
        i = argv.index("--review-alt") + 1
        if i >= len(argv) or not REVIEW_ALT_REASON_RX.match(argv[i] or ""):
            return 2
        review_alt_reason = argv[i]

    maybe_auto_reset(path, roster)
    dropped = expire_unavailable(roster)
    if dropped:
        save_state(path, roster)
        print("note  unavailable mark expired after %d hours: %s" % (UNAVAILABLE_TTL_HOURS, ", ".join(dropped)))
    other_pool = (roster.get("other_pool") or "available").lower()
    unavailable = roster.get("unavailable") or {}
    ra_id, ra_fam_o, _ = norm_entry(roster.get("review_a"))
    ra_fam = family_of(ra_id, ra_fam_o) if ra_id else None
    if not ra_id or ra_fam is None:
        print("FAIL  review_a missing or family unknown (%r)" % ra_id)
        return 1
    profiles = roster.get("profiles") or []
    if not profiles and "builder" in roster and "review_b" in roster:   # v1 shape: one implicit profile
        profiles = [{"name": "default", "builder": roster["builder"], "review_b": roster["review_b"]}]
    if not profiles:
        print("FAIL  roster has no profiles")
        return 1

    cwd = os.getcwd()
    bset = built_families(run_log, cwd=cwd)
    built_model = built_by(run_log, bset["branch"])
    built_fam_one = family_of(built_model) if built_model else None
    roster_b_fams = _roster_builder_families(roster, profiles)
    parse_b_fams = _parsing_row_families(bset["parsing_rows"])
    rebuild_end = bset.get("rebuild_end")
    set_status = bset["status"]
    built_fam_set = set(bset["families"]) if set_status in ("known", "empty") else set()

    if set_status == "unreadable":
        cause = bset["unreadable_cause"]
        print("FAIL  cannot read the families that built this branch (%s)" % cause)
        return 1

    if review_alt_reason is not None and set_status == "unknown":
        for _needle, label in bset["unknown_causes"]:
            print("unknown  the built set is not known (%s)" % label)
        print("FAIL  --review-alt refused: the built set is not known")
        return 1

    print("roster-check: other_pool=%s  review_a=%s (%s)" % (other_pool, ra_id, ra_fam))
    if built_model:
        print("roster-check: the last builder run was %s (%s family), from %s" % (built_model, built_fam_one, run_log))
    if set_status == "unknown":
        for _needle, label in bset["unknown_causes"]:
            print("unknown  the built set is not known (%s)" % label)

    def _probe_roles(roles):
        usable = True
        for role, mid in roles:
            ok, detail = probe(mid)
            if ok is PROBE_SIGN_IN:
                print("    probe %-8s %s: tool sign-in required" % (role, mid))
                print(SIGN_IN_LINE)
                return False, True
            print("    probe %-8s %s: %s" % (role, mid, detail))
            if not ok:
                usable = False
        return usable, False

    def _alt_pool_ok(alt_id, alt_pool):
        if alt_id in unavailable:
            return False
        return not (other_pool == "exhausted" and alt_pool == "other")

    def _r_excluded(r_id, r_pool):
        return r_id in unavailable or (other_pool == "exhausted" and r_pool == "other")

    def _r_usable_plain(r_id, r_pool):
        return r_id not in unavailable and not (other_pool == "exhausted" and r_pool == "other")

    chosen = None
    global_rebuild_end = rebuild_end
    for prof in profiles:
        name = prof.get("name", "?")
        b_id, b_fam_o, b_pool_o = norm_entry(prof.get("builder"))
        r_id, r_fam_o, r_pool_o = norm_entry(prof.get("review_b"))
        a_id, a_fam_o, a_pool_o = norm_entry(prof.get("review_b_alt"))
        b_fam, r_fam = family_of(b_id, b_fam_o), family_of(r_id, r_fam_o)
        a_fam = family_of(a_id, a_fam_o) if a_id else None
        b_pool, r_pool = pool_of(b_id, b_pool_o), pool_of(r_id, r_pool_o)
        a_pool = pool_of(a_id, a_pool_o) if a_id else None
        print("  profile %-8s builder=%s (%s, %s)  review_b=%s (%s, %s)" % (name, b_id, b_fam, b_pool, r_id, r_fam, r_pool))
        if b_fam is None or r_fam is None:
            print("    skip: family unknown - add {\"model\": ..., \"family\": ...}"); continue
        if other_pool == "exhausted" and b_pool == "other":
            how = (" automatically at " + roster["auto_exhausted_at"]) if roster.get("auto_exhausted_at") else " by the owner"
            print("    skip: uses the other-models pool, marked exhausted%s" % how); continue
        if b_id in unavailable:
            print("    skip: a model was marked unavailable after repeated failures (%s)" % b_id); continue
        fams = {"builder": b_fam, "review_a": ra_fam, "review_b": r_fam}
        if len(set(fams.values())) < 3:
            print("    skip: family collision %s" % fams); continue

        if review_alt_reason is not None:
            if not a_id:
                continue
            if not _alt_independent(a_fam, built_fam_set if set_status == "known" else set(), ra_fam):
                continue
            if not _alt_pool_ok(a_id, a_pool):
                continue
            probe_list = [("builder", b_id), ("review_b_alt", a_id)]
            if do_probe:
                ok, sign_in = _probe_roles(probe_list)
                if sign_in:
                    return 5
                if not ok:
                    continue
            branch_name = bset["branch"]
            known_built = sorted(built_fam_set) if set_status == "known" else []
            chosen = {"profile": name, "builder": b_id, "review_a": ra_id, "review_b": a_id, "families": dict(fams, review_b=a_fam),
                      "other_pool": other_pool, "probed": do_probe,
                      "resolved_at": stamp(now_utc()), "reset_day": roster.get("reset_day"),
                      "deviation": {"review_b_alt": a_id, "reason": review_alt_reason, "branch": branch_name, "built": known_built}}
            print("DEVIATION  review_b is %s on request (%s)" % (a_id, review_alt_reason))
            break

        r_excl = _r_excluded(r_id, r_pool)
        use_r_id, use_r_fam = r_id, r_fam
        rebuild = None
        deviation = None
        profile_rebuild_end = global_rebuild_end

        if set_status == "unknown":
            if r_excl:
                print("    skip: review_b is excluded and no alternate may be resolved on an unknown built set"); continue
            if not _r_usable_plain(r_id, r_pool):
                print("    skip: a model was marked unavailable after repeated failures (%s)" % r_id); continue
            if r_fam in roster_b_fams or r_fam in parse_b_fams:
                rebuild = {"built_by": built_model, "rebuild_with": b_id}
                print("    REBUILD  review_b %s is of the %s family, which built the change in flight (%s): this profile's builder %s rebuilds it before Review B (step 3b); the reviewer of a change is never of the family that built it (release A4)" % (r_id, r_fam, built_model or "?", b_id))
            else:
                pass
        elif set_status in ("known", "empty"):
            if not r_excl and not _r_usable_plain(r_id, r_pool):
                print("    skip: a model was marked unavailable after repeated failures (%s)" % r_id); continue
            if not r_excl and r_fam not in built_fam_set:
                pass
            elif not r_excl and r_fam in built_fam_set:
                if a_id and _alt_independent(a_fam, built_fam_set, ra_fam) and _alt_pool_ok(a_id, a_pool):
                    use_r_id, use_r_fam = a_id, a_fam
                    known_built = sorted(built_fam_set)
                    deviation = {"review_b_alt": a_id, "reason": "family", "branch": bset["branch"], "built": known_built}
                else:
                    rebuild = {"built_by": built_model, "rebuild_with": b_id}
                    if _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd):
                        profile_rebuild_end = "new branch"
                    print("    REBUILD  review_b %s is of the %s family, which built the change in flight (%s): this profile's builder %s rebuilds it before Review B (step 3b); the reviewer of a change is never of the family that built it (release A4)" % (r_id, r_fam, built_model or "?", b_id))
            elif r_excl:
                if a_id and _alt_independent(a_fam, built_fam_set, ra_fam) and _alt_pool_ok(a_id, a_pool):
                    use_r_id, use_r_fam = a_id, a_fam
                    known_built = sorted(built_fam_set)
                    deviation = {"review_b_alt": a_id, "reason": "unavailable", "branch": bset["branch"], "built": known_built}
                else:
                    print("    skip: review_b is excluded and no independent usable alternate"); continue

        probe_list = [("builder", b_id)]
        if deviation and a_id:
            probe_list.append(("review_b_alt", a_id))
        elif not deviation:
            probe_list.append(("review_b", r_id))
        if do_probe:
            ok, sign_in = _probe_roles(probe_list)
            if sign_in:
                return 5
            if not ok:
                if deviation and rebuild is None and set_status != "unknown":
                    rebuild = {"built_by": built_model, "rebuild_with": b_id}
                    if _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd):
                        profile_rebuild_end = "new branch"
                    deviation = None
                    use_r_id, use_r_fam = r_id, r_fam
                    print("    REBUILD  review_b %s is of the %s family, which built the change in flight (%s): this profile's builder %s rebuilds it before Review B (step 3b); the reviewer of a change is never of the family that built it (release A4)" % (r_id, r_fam, built_model or "?", b_id))
                else:
                    print("    skip: a model did not answer"); continue

        fams_out = {"builder": b_fam, "review_a": ra_fam, "review_b": use_r_fam}
        chosen = {"profile": name, "builder": b_id, "review_a": ra_id, "review_b": use_r_id, "families": fams_out,
                  "other_pool": other_pool, "probed": do_probe,
                  "resolved_at": stamp(now_utc()), "reset_day": roster.get("reset_day")}
        if deviation:
            chosen["deviation"] = deviation
            print("DEVIATION  review_b is %s instead of %s (%s)" % (a_id, r_id, deviation["reason"]))
        if rebuild:
            chosen["rebuild"] = rebuild
            chosen["_rebuild_end"] = profile_rebuild_end
        break

    if review_alt_reason is not None and chosen is None:
        print("FAIL  --review-alt refused: no profile has an independent usable alternate")
        return 1
    if chosen is None:
        print("FAIL  no usable profile - the owner must buy usage, flip other_pool, or add a native profile")
        return 1
    ok = True
    if command is not None:
        m = re.search(r"--model[=\s]+(\S+)", command)
        if not m:
            print("FAIL  delegate command carries no --model; the builder family would be a default that can change"); ok = False
        elif m.group(1).strip("\"'") != chosen["builder"]:
            print("FAIL  delegate command uses --model %s but the resolved builder is %s" % (m.group(1), chosen["builder"])); ok = False
        else:
            print("ok    delegate command sets --model %s" % chosen["builder"])
    # The tracked file is rewritten only when what it resolves changes, so a check before every
    # snapshot leaves the tree clean (2026.10.25a, FB-008); the time of each check goes to the
    # roster's untracked state.
    try:
        with open(out_path, encoding="utf-8-sig") as f:
            before = json.load(f)
    except (OSError, ValueError):
        before = None
    same = isinstance(before, dict) and {k: v for k, v in before.items() if k != "resolved_at"} == {k: v for k, v in chosen.items() if k != "resolved_at"}
    roster["last_resolved"] = chosen["resolved_at"]
    save_state(path, roster)
    if not same:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(chosen, f, indent=2); f.write("\n")
    print("RESOLVED profile '%s': builder=%s  review_a=%s  review_b=%s  -> %s%s" % (
        chosen["profile"], chosen["builder"], chosen["review_a"], chosen["review_b"], out_path,
        "" if not same else " (unchanged since %s, not rewritten)" % before.get("resolved_at")))
    if chosen.get("rebuild"):
        end = chosen.pop("_rebuild_end", None)
        base = "REBUILD  the change in flight was built by %s; rebuild it with %s (the brief re-delegated) before Review B %s; the launcher refuses Review B until then" % (
            chosen["rebuild"]["built_by"], chosen["builder"], chosen["review_b"])
        if end == "checkpoint":
            print(base + "; the branch is taken back to the checkpoint of its first builder run and its first-round brief run again (checkpoint)")
        elif end == "--repair-record":
            print(base + "; run roster-check.py --repair-record first (--repair-record)")
        elif end == "new branch":
            print(base + "; run the same rebuild under a new branch name (new branch)")
        else:
            print(base)
    if chosen["profile"] != profiles[0].get("name", "?"):
        print("NOTE  the preferred profile '%s' is not in use - report this to the owner in the first line" % profiles[0].get("name", "?"))
    return 0 if ok else 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
