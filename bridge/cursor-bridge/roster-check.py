#!/usr/bin/env python3
"""roster-check: resolve which models fill the builder / Review A / Review B roles today,
prove three distinct families, and (optionally) prove each model answers.

  python roster-check.py docs/ROSTER.json [--command "<delegate command>"] [--no-probe] [--out docs/ROSTER.resolved.json] [--run-log run/launcher/runs.jsonl] [--repair-record] [--review-alt <reason>]

docs/ROSTER.json (v2):
{
  "other_pool": "available" | "exhausted",      <- Cursor's "Other Models" usage pool (every
                                                    third-party model). Set automatically by
                                                    --record-failure, restored on reset_day, or
                                                    by the owner (--mark-exhausted/--mark-reset).
                                                    A probe cannot see 1% remaining.
  "review_a": "claude-opus-5-5",                  <- Review A runs in Claude Code, not Cursor.
  "profiles": [                                   <- tried in order; the first usable one wins
    {"name": "full",   "builder": "grok-4.7-high", "review_b": "gpt-5.6-sol-high"},
    {"name": "native", "builder": "composer-2.5",  "review_b": "grok-4.7-high",
                        "review_b_alt": "composer-2.5"}
  ]
}
A model entry is an id string or {"model": id, "family": name, "pool": "native"|"other"}.
Pool is inferred from the id per Cursor's docs: Grok (any effort/host prefix) and Composer are
the "Cursor Models" pool (native); every third-party model is "Other Models".
A profile is skipped when other_pool is "exhausted" and the builder is in the other pool, or
when review_b is excluded by its pool or a mark only where no alternate is independent and
usable. Unless --no-probe, the profile's builder, Review B and (where the table resolves an
alternate) review_b_alt are each sent a one-word request through `cursor-agent -p -f --model <id>`;
a refusal, empty reply, usage-limit message or timeout marks that model as not answering (this
catches hard failures only, never a nearly-empty quota); any other reply counts as answered,
off-script. After every probe planned for the profile, a builder that did not answer skips it;
under the reason unavailable an alternate that did not answer skips it (review_b is excluded and
not probed). Under the reason family an alternate that answered resolves with the deviation,
whatever review_b answered; an alternate that did not answer leaves a REBUILD with review_b, judged
on the answer review_b gave in its one probe (never probed twice), and skips the profile if review_b
did not answer. With no deviation, review_b that did not answer skips the profile. The chosen
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
--review-alt <reason>  resolve the alternate on request for the profile the resolve without it
picks, never passing to a later profile; reason is one word of ASCII letters and hyphens; exit 1
when the alternate cannot be resolved (the built set unknown or not readable among the causes).
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
2 = cannot read, a malformed --review-alt reason, CANNOT REPAIR, or a wrong model argument;
3 = pool/model marked exhausted, re-resolve;
4 = transient, retry once; 5 = repeated connection failures or time-outs, or the Cursor tool signed out (SIGN-IN), tell the owner.
ASCII-only on purpose.
"""
import datetime
import json
import os
import re
import stat
import subprocess
import sys
import tempfile

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
    p = _git_run(["git", "rev-parse", "--abbrev-ref", "HEAD"], os.getcwd())
    if p is None or p.returncode != 0:
        return ""
    return (p.stdout or "").strip()


def built_by(run_log, branch=None):
    """The model of the last builder run of the branch under review in the launcher's run log
    (release A4; the log records the branch). None for a branch with no builder run: a design
    review is of a text nothing built, and another branch's builder did not build this change
    (2026.10.25a: the fallback to any branch's last run refused the only usable profile)."""
    try:
        with open(run_log, "rb") as f:
            raw = f.read().split(b"\n")
    except OSError:
        return None
    branch = branch or current_branch()
    entries = []
    for line_b in raw:
        e = _parse_run_line(line_b)
        if not e:
            continue
        if e.get("kind") == "builder" and e.get("model"):
            if e.get("slot") == "not free":
                continue
            entries.append(e)
    for e in reversed(entries):
        if branch and e.get("branch") == branch:
            return str(e["model"])
    return None


GIT_TIMEOUT = 20
REVIEW_ALT_WORD_RX = re.compile(r"[A-Za-z][A-Za-z-]*")
_COMMIT_NAME_RX = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
_REPORT_BRIEF_RX = re.compile(r"(.+?)(?:-r\d+[a-z]?)?-report\.md", re.IGNORECASE)


def _git_decode_stdout(raw):
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    try:
        return raw.decode("utf-8", errors="surrogateescape")
    except ValueError:
        return None


def _git_run(args, cwd):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=False, timeout=GIT_TIMEOUT,
                           creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None
    stdout = _git_decode_stdout(p.stdout)
    if stdout is None:
        return None
    return subprocess.CompletedProcess(args, p.returncode, stdout, p.stderr)


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
    return isinstance(name, str) and bool(_COMMIT_NAME_RX.fullmatch(name))


def _commit_exists(sha, cwd, cache=None):
    if cache is None:
        cache = {}
    if sha in cache:
        return cache[sha]
    p = _git_run(["git", "rev-parse", "--verify", "-q", sha + "^{commit}"], cwd)
    if p is None or p.returncode not in (0, 1):
        cache[sha] = None
        return None
    ok = p.returncode == 0
    cache[sha] = ok
    return ok


def _git_is_ancestor(ancestor, descendant, cwd):
    p = _git_run(["git", "merge-base", "--is-ancestor", ancestor, descendant], cwd)
    if p is None or p.returncode not in (0, 1):
        return None
    return p.returncode == 0


def _repo_toplevel(cwd):
    p = _git_run(["git", "rev-parse", "--show-toplevel"], cwd)
    if p is None or p.returncode != 0:
        return None
    return (p.stdout or "").strip()


def _brief_from_report(rel_path):
    base = os.path.basename(rel_path.replace("\\", "/"))
    m = _REPORT_BRIEF_RX.fullmatch(base)
    return m.group(1) if m else None


def _reports_at_commit(commit, cwd):
    p = _git_run(["git", "ls-tree", "-r", "-z", "--name-only", "--full-tree", commit, "--", "handoff/"], cwd)
    if p is None or p.returncode != 0:
        return None
    out = set()
    for part in (p.stdout or "").split("\0"):
        part = part.strip().replace("\\", "/")
        if part and part.lower().endswith("-report.md"):
            out.add(part)
    return out


def _handoff_reports_working_tree(toplevel):
    handoff = os.path.join(toplevel, "handoff")
    found = set()
    if os.path.isdir(handoff):
        for name in os.listdir(handoff):
            if name.lower().endswith("-report.md"):
                found.add(("handoff/" + name).replace("\\", "/"))
    return found


def _tree_report_names(cwd):
    top = _repo_toplevel(cwd)
    if top is None:
        return None, "git"
    wt = _handoff_reports_working_tree(top)
    head_p = _git_run(["git", "rev-parse", "HEAD"], cwd)
    if head_p is None or head_p.returncode != 0:
        return None, "git"
    head = (head_p.stdout or "").strip()
    at_head = _reports_at_commit(head, cwd)
    if at_head is None:
        return None, "git"
    return wt | at_head, None


def _branch_from_head(cwd):
    p = _git_run(["git", "symbolic-ref", "-q", "HEAD"], cwd)
    if p is None or p.returncode not in (0, 1):
        return None, "git"
    if p.returncode == 1:
        return None, "detached"
    ref = (p.stdout or "").strip()
    if ref.startswith("refs/heads/"):
        return ref[len("refs/heads/"):], None
    return None, "detached"


def _merge_base_with_main(branch, cwd):
    branch_ref = branch if branch.startswith("refs/") else "refs/heads/" + branch
    for main_ref in ("refs/remotes/origin/main", "refs/heads/main"):
        p = _git_run(["git", "rev-parse", "--verify", "-q", main_ref + "^{commit}"], cwd)
        if p is None or p.returncode not in (0, 1):
            return None, "git"
        if p.returncode == 1:
            continue
        mb = _git_run(["git", "merge-base", branch_ref, main_ref], cwd)
        if mb is None or mb.returncode not in (0, 1):
            return None, "git"
        if mb.returncode == 1:
            return None, "main"
        base = (mb.stdout or "").strip()
        if base:
            return base, None
    return None, "main"


def _row_valid_start(row, cwd, commit_cache):
    sc = row.get("start_commit")
    if not _valid_commit_name(sc):
        return None
    exists = _commit_exists(sc, cwd, commit_cache)
    if exists is None:
        return False
    if not exists:
        return None
    return sc


def _apply_drop_rule(rows, cwd, commit_cache=None):
    """Return rows that survive the clean-rebuild drop rule, in file order, or None if git does not answer."""
    if commit_cache is None:
        commit_cache = {}
    if not rows:
        return []
    kept = []
    for i, row in enumerate(rows):
        dropped = False
        for later in rows[i + 1:]:
            if later.get("clean") is not True:
                continue
            ls = _row_valid_start(later, cwd, commit_cache)
            es = _row_valid_start(row, cwd, commit_cache)
            if ls is False or es is False:
                return None
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
    for role in ("builder", "review_b"):
        mid, fam_o, _ = norm_entry(roster.get(role))
        if mid:
            fam = family_of(mid, fam_o)
            if fam:
                fams.add(fam)
    return fams


def _roster_model_family(roster, profiles, model_id):
    if not isinstance(model_id, str) or not model_id:
        return None
    for prof in profiles or []:
        for role in ("builder", "review_b", "review_b_alt"):
            mid, fam_o, _ = norm_entry(prof.get(role))
            if mid == model_id and fam_o:
                return family_of(mid, fam_o)
    for role in ("builder", "review_b", "review_a"):
        mid, fam_o, _ = norm_entry(roster.get(role))
        if mid == model_id and fam_o:
            return family_of(mid, fam_o)
    return family_of(model_id)


def _parse_run_line(line_b):
    if not line_b.strip():
        return None
    try:
        text = line_b.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return False
    if not text.strip():
        return None
    try:
        e = json.loads(text)
    except (ValueError, RecursionError):
        return False
    if not isinstance(e, dict):
        return False
    return e


def _parse_run_log_raw(run_log):
    run_log_base = os.path.basename(run_log)
    try:
        if os.path.isdir(run_log):
            return None, run_log_base, [], [], []
        with open(run_log, "rb") as f:
            raw_lines = f.read().split(b"\n")
    except OSError:
        if os.path.exists(run_log):
            return None, run_log_base, [], [], []
        return [], None, [], [], []
    bad = []
    objs = []
    good_bytes = []
    for line_b in raw_lines:
        if not line_b.strip():
            continue
        parsed = _parse_run_line(line_b)
        if parsed is None:
            continue
        if parsed is False:
            bad.append(line_b)
            continue
        objs.append(parsed)
        good_bytes.append(line_b)
    return objs, None, bad, raw_lines, good_bytes


def _branch_builder_rows(entries, branch):
    rows = []
    for e in entries:
        if e.get("kind") != "builder":
            continue
        if e.get("slot") == "not free":
            continue
        if e.get("branch") == branch:
            rows.append(e)
    return rows


def _unreadable(result, cause):
    result["status"] = "unreadable"
    result["unreadable_cause"] = cause
    return result


def built_families(run_log, branch=None, cwd=None, roster=None, profiles=None):
    """Families that built the branch, or empty / unknown / unreadable.

    Signature for TASK-086b: built_families(run_log, branch=None, cwd=None) -> dict with
    status, families, unknown_causes, unreadable_cause, parsing_rows, counted_rows, rebuild_end.
    cwd is the folder the branch is read in (default: process cwd). TASK-086b's launcher must pass
    the roster and its profiles for the same set the resolve reads; without them a row whose family
    only the roster names reads as unknown.
    """
    cwd = cwd or os.getcwd()
    branch_arg = branch
    roster = roster or {}
    profiles = profiles or roster.get("profiles") or []
    result = {"branch": branch or "", "status": "known", "families": set(), "unknown_causes": [],
              "unreadable_cause": None, "parsing_rows": [], "counted_rows": [],
              "rebuild_end": None, "run_log_base": os.path.basename(run_log)}
    if not _in_git_repo(cwd):
        result["status"] = "empty"
        return result
    branch_name, head_fail = _branch_from_head(cwd)
    if head_fail:
        return _unreadable(result, head_fail)
    branch = branch_arg or branch_name
    result["branch"] = branch
    tree_reports, rep_fail = _tree_report_names(cwd)
    if rep_fail:
        return _unreadable(result, rep_fail)
    added_reports = []
    if tree_reports:
        base, fail = _merge_base_with_main(branch, cwd)
        if fail:
            return _unreadable(result, fail)
        if base is None:
            return _unreadable(result, "main")
        base_reports = _reports_at_commit(base, cwd)
        if base_reports is None:
            return _unreadable(result, "git")
        base_cf = {p.casefold() for p in base_reports}
        added_reports = [r for r in tree_reports if r.casefold() not in base_cf]
    entries, open_fail, bad_lines, _raw, _good = _parse_run_log_raw(run_log)
    if open_fail:
        return _unreadable(result, open_fail)
    parsing_rows = _branch_builder_rows(entries, branch)
    result["parsing_rows"] = list(parsing_rows)
    commit_cache = {}
    counted = _apply_drop_rule(parsing_rows, cwd, commit_cache)
    if counted is None:
        return _unreadable(result, "git")
    result["counted_rows"] = counted
    unknown = []
    if bad_lines:
        unknown.append(("runs.jsonl", result["run_log_base"]))
        result["rebuild_end"] = "--repair-record"
    for row in counted:
        mid = row.get("model")
        fam = _roster_model_family(roster, profiles, mid)
        if not isinstance(mid, str) or not mid or fam is None:
            row_id = row.get("id", "?")
            label = "%s: builder row %s of model %r, whose family cannot be named; give the model its family in the roster" % (
                result["run_log_base"], row_id, mid)
            unknown.append((label, label))
            if result["rebuild_end"] is None:
                result["rebuild_end"] = "checkpoint"
            continue
        result["families"].add(fam)
    for rep in added_reports:
        rep_base = os.path.basename(rep.replace("\\", "/"))
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in rep_base):
            brief = None
        else:
            brief = _brief_from_report(rep)
        if brief is None or not any(r.get("brief") == brief for r in parsing_rows):
            unknown.append((rep, ascii(rep_base)))
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
    commit_cache = {}
    start = None
    for row in counted:
        sc = _row_valid_start(row, cwd, commit_cache)
        if sc is False:
            return None
        if sc:
            start = sc
            break
    if start is None:
        return True
    hypo = {"kind": "builder", "branch": branch, "model": "x", "start_commit": start, "clean": True}
    survived = _apply_drop_rule(counted + [hypo], cwd, commit_cache)
    if survived is None:
        return None
    return len(survived) > 1


def _rebuild_built_by_model(rows, r_fam, roster, profiles, fallback):
    for row in reversed(rows):
        mid = row.get("model")
        fam = _roster_model_family(roster, profiles, mid)
        if fam == r_fam and isinstance(mid, str) and mid:
            return mid
    return fallback


def _parsing_row_families(rows, roster, profiles):
    fams = set()
    for row in rows:
        fam = _roster_model_family(roster, profiles, row.get("model"))
        if fam:
            fams.add(fam)
    return fams


def _alt_independent(alt_fam, built_fams, ra_fam):
    return alt_fam and alt_fam != ra_fam and alt_fam not in built_fams


def _is_symlink_or_junction(st):
    if stat.S_ISLNK(st.st_mode):
        return True
    if getattr(st, "st_reparse_tag", 0):
        return True
    return False


def _nofollow_opener(path, flags):
    return os.open(path, flags | getattr(os, "O_NOFOLLOW", 0), 0o644)


def _record_path_unsafe(path):
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if _is_symlink_or_junction(st):
        return True
    if not stat.S_ISREG(st.st_mode):
        return True
    return False


def _damaged_path_unsafe(path):
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if _is_symlink_or_junction(st):
        return True
    if not stat.S_ISREG(st.st_mode):
        return True
    if st.st_nlink > 1:
        return True
    return False


def repair_record(run_log):
    if _record_path_unsafe(run_log):
        print("CANNOT REPAIR: refuse %s" % run_log)
        return 2
    _entries, open_fail, _bad, raw_lines, _good = _parse_run_log_raw(run_log)
    if open_fail is not None:
        print("CANNOT REPAIR: cannot read %s" % run_log)
        return 2
    kept_bytes = []
    moved_bytes = []
    for line_b in raw_lines:
        if not line_b.strip():
            continue
        parsed = _parse_run_line(line_b)
        if parsed is False:
            moved_bytes.append(line_b)
        elif parsed is not None:
            kept_bytes.append(line_b)
    if not moved_bytes:
        print("repair-record  kept %d  moved 0" % len(kept_bytes))
        return 0
    log_dir = os.path.dirname(os.path.abspath(run_log)) or "."
    base = os.path.basename(run_log)
    damaged = os.path.join(log_dir, "runs.damaged.jsonl")
    if _damaged_path_unsafe(damaged):
        print("CANNOT REPAIR: refuse %s" % damaged)
        return 2
    tmp_fd = tmp_path = None
    try:
        os.makedirs(log_dir, exist_ok=True)
        with open(damaged, "ab", opener=_nofollow_opener) as f:
            fst = os.fstat(f.fileno())
            if _is_symlink_or_junction(fst) or not stat.S_ISREG(fst.st_mode) or fst.st_nlink != 1:
                print("CANNOT REPAIR: refuse %s" % damaged)
                return 2
            for line_b in moved_bytes:
                f.write(line_b + b"\n")
            f.flush()
            os.fsync(f.fileno())
        tmp_fd, tmp_path = tempfile.mkstemp(dir=log_dir, prefix=base + ".")
        with os.fdopen(tmp_fd, "wb") as f:
            tmp_fd = None
            for line_b in kept_bytes:
                f.write(line_b + b"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, run_log)
        tmp_path = None
    except OSError as e:
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        print("CANNOT REPAIR: %s" % e)
        return 2
    print("repair-record  kept %d  moved %d" % (len(kept_bytes), len(moved_bytes)))
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
                           text=False, timeout=20, creationflags=NO_WINDOW)
        common_out = _git_decode_stdout(g.stdout) if g.returncode == 0 else None
        if common_out is not None and common_out.strip():
            common = common_out.strip()
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
        print("usage: roster-check.py docs/ROSTER.json [--command ...] [--no-probe] [--out <path>] [--repair-record] [--review-alt <reason>] | --record-failure <model> --stderr-file <path>")
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
        alt_val = argv[i] if i < len(argv) else None
        if alt_val is None or not REVIEW_ALT_WORD_RX.fullmatch(alt_val):
            got = repr(alt_val) if alt_val is not None else "nothing"
            print("FAIL  --review-alt: the reason must be one word of letters and hyphens, beginning with a letter (got %s)" % got)
            return 2
        review_alt_reason = alt_val

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
    bset = built_families(run_log, cwd=cwd, roster=roster, profiles=profiles)
    built_model = built_by(run_log, bset["branch"])
    built_fam_one = family_of(built_model) if built_model else None
    roster_b_fams = _roster_builder_families(roster, profiles)
    parse_b_fams = _parsing_row_families(bset["parsing_rows"], roster, profiles)
    parsing_unknown_family = any(
        not isinstance(row.get("model"), str) or not row.get("model")
        or _roster_model_family(roster, profiles, row.get("model")) is None
        for row in bset["parsing_rows"])
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

    def _rebuild_line_open(r_id, r_fam, builder_id):
        rows_for_rb = bset["counted_rows"] if set_status != "unknown" else bset["parsing_rows"]
        rb = _rebuild_built_by_model(rows_for_rb, r_fam, roster, profiles, built_model)
        if rb and _roster_model_family(roster, profiles, rb) == r_fam:
            return ("    REBUILD  review_b %s is of the %s family, which built the change in flight (%s): this profile's builder %s rebuilds it before Review B (step 3b); the reviewer of a change is never of the family that built it (release A4)" % (
                r_id, r_fam, rb, builder_id)), rb
        if r_fam in roster_b_fams:
            return ("    REBUILD  review_b %s is of the %s family, which is a builder's family in the roster file: this profile's builder %s rebuilds it before Review B (step 3b); the reviewer of a change is never of the family that built it (release A4)" % (
                r_id, r_fam, builder_id)), rb
        return ("    REBUILD  review_b %s is of the %s family, and a builder row of the branch names a model whose family cannot be named: this profile's builder %s rebuilds it before Review B (step 3b); the reviewer of a change is never of the family that built it (release A4)" % (
            r_id, r_fam, builder_id)), rb

    def _rebuild_entry(r_id, r_fam, builder_id, ask_new_branch):
        rb_line, rb_model = _rebuild_line_open(r_id, r_fam, builder_id)
        rebuild = {"built_by": rb_model, "rebuild_with": builder_id}
        end_marker = None
        new_branch_git_fail = False
        if ask_new_branch:
            nb = _rebuild_needs_new_branch(bset["counted_rows"], bset["branch"], cwd)
            if nb is None:
                new_branch_git_fail = True
            elif nb:
                end_marker = "new branch"
        return rb_line, rebuild, end_marker, new_branch_git_fail

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

    global_rebuild_end = rebuild_end

    def _evaluate_profile(prof, verbose):
        name = prof.get("name", "?")
        b_id, b_fam_o, b_pool_o = norm_entry(prof.get("builder"))
        r_id, r_fam_o, r_pool_o = norm_entry(prof.get("review_b"))
        a_id, a_fam_o, a_pool_o = norm_entry(prof.get("review_b_alt"))
        b_fam, r_fam = family_of(b_id, b_fam_o), family_of(r_id, r_fam_o)
        a_fam = family_of(a_id, a_fam_o) if a_id else None
        b_pool, r_pool = pool_of(b_id, b_pool_o), pool_of(r_id, r_pool_o)
        a_pool = pool_of(a_id, a_pool_o) if a_id else None
        if verbose:
            print("  profile %-8s builder=%s (%s, %s)  review_b=%s (%s, %s)" % (name, b_id, b_fam, b_pool, r_id, r_fam, r_pool))
        if b_fam is None or r_fam is None:
            if verbose:
                print("    skip: family unknown - add {\"model\": ..., \"family\": ...}")
            return None
        if other_pool == "exhausted" and b_pool == "other":
            how = (" automatically at " + roster["auto_exhausted_at"]) if roster.get("auto_exhausted_at") else " by the owner"
            if verbose:
                print("    skip: uses the other-models pool, marked exhausted%s" % how)
            return None
        if b_id in unavailable:
            if verbose:
                print("    skip: a model was marked unavailable after repeated failures (%s)" % b_id)
            return None
        fams = {"builder": b_fam, "review_a": ra_fam, "review_b": r_fam}
        if len(set(fams.values())) < 3:
            if verbose:
                print("    skip: family collision %s" % fams)
            return None

        r_excl = _r_excluded(r_id, r_pool)
        use_r_id, use_r_fam = r_id, r_fam
        rebuild = None
        deviation = None
        profile_rebuild_end = global_rebuild_end
        family_deviation = False

        family_only_unknown = (
            parsing_unknown_family
            and all("whose family cannot be named" in label for _n, label in bset["unknown_causes"]))

        if set_status == "unknown":
            if r_excl:
                if verbose:
                    print("    skip: review_b is excluded and no alternate may be resolved on an unknown built set")
                return None
            if r_fam in roster_b_fams or r_fam in parse_b_fams or parsing_unknown_family:
                rb_line, rebuild, end_marker, new_branch_git_fail = _rebuild_entry(r_id, r_fam, b_id, family_only_unknown)
                if new_branch_git_fail:
                    return "git-fail"
                if end_marker:
                    profile_rebuild_end = end_marker
                if verbose:
                    print(rb_line)
        elif set_status in ("known", "empty"):
            if not r_excl and r_id in unavailable:
                if verbose:
                    print("    skip: a model was marked unavailable after repeated failures (%s)" % r_id)
                return None
            if not r_excl and r_fam not in built_fam_set:
                pass
            elif not r_excl and r_fam in built_fam_set:
                family_deviation = True
                if a_id and _alt_independent(a_fam, built_fam_set, ra_fam) and _alt_pool_ok(a_id, a_pool):
                    use_r_id, use_r_fam = a_id, a_fam
                    known_built = sorted(built_fam_set)
                    deviation = {"review_b_alt": a_id, "reason": "family", "branch": bset["branch"], "built": known_built}
                else:
                    rb_line, rebuild, end_marker, new_branch_git_fail = _rebuild_entry(r_id, r_fam, b_id, True)
                    if new_branch_git_fail:
                        return "git-fail"
                    if end_marker:
                        profile_rebuild_end = end_marker
                    if verbose:
                        print(rb_line)
            elif r_excl:
                if a_id and _alt_independent(a_fam, built_fam_set, ra_fam) and _alt_pool_ok(a_id, a_pool):
                    use_r_id, use_r_fam = a_id, a_fam
                    known_built = sorted(built_fam_set)
                    deviation = {"review_b_alt": a_id, "reason": "unavailable", "branch": bset["branch"], "built": known_built}
                else:
                    if verbose:
                        print("    skip: review_b is excluded and no independent usable alternate")
                    return None

        if do_probe:
            ok_b, sign_in_b = _probe_roles([("builder", b_id)])
            if sign_in_b:
                return "sign-in"
            ok_rb = True
            ok_alt = True
            if not _r_excluded(r_id, r_pool):
                ok_rb, sign_in_rb = _probe_roles([("review_b", r_id)])
                if sign_in_rb:
                    return "sign-in"
            if deviation and a_id and _alt_pool_ok(a_id, a_pool):
                ok_alt, sign_in_alt = _probe_roles([("review_b_alt", a_id)])
                if sign_in_alt:
                    return "sign-in"
            if not ok_b:
                if verbose:
                    print("    skip: a model did not answer")
                return None
            if deviation and deviation.get("reason") == "unavailable":
                if not ok_alt:
                    if verbose:
                        print("    skip: a model did not answer")
                    return None
            elif deviation and family_deviation and rebuild is None:
                if not ok_alt:
                    rb_line, rebuild, end_marker, new_branch_git_fail = _rebuild_entry(r_id, r_fam, b_id, True)
                    if new_branch_git_fail:
                        return "git-fail"
                    if end_marker:
                        profile_rebuild_end = end_marker
                    deviation = None
                    use_r_id, use_r_fam = r_id, r_fam
                    if verbose:
                        print(rb_line)
                    if not ok_rb:
                        if verbose:
                            print("    skip: a model did not answer")
                        return None
            elif not deviation and not _r_excluded(r_id, r_pool) and not ok_rb:
                if verbose:
                    print("    skip: a model did not answer")
                return None

        fams_out = {"builder": b_fam, "review_a": ra_fam, "review_b": use_r_fam}
        return {"profile": name, "builder": b_id, "review_a": ra_id, "review_b": use_r_id, "families": fams_out,
                "deviation": deviation, "rebuild": rebuild, "profile_rebuild_end": profile_rebuild_end,
                "a_id": a_id, "a_fam": a_fam, "a_pool": a_pool, "r_id": r_id, "r_fam": r_fam}

    if review_alt_reason is not None:
        in_use = None
        for prof in profiles:
            u = _evaluate_profile(prof, False)
            if u == "sign-in":
                return 5
            if u == "git-fail":
                print("FAIL  cannot read the families that built this branch (git)")
                return 1
            if u is not None:
                in_use = prof
                break
        if in_use is None:
            print("FAIL  --review-alt refused: no profile is in use (every profile is skipped)")
            return 1
        name = in_use.get("name", "?")
        a_id, a_fam_o, a_pool_o = norm_entry(in_use.get("review_b_alt"))
        if not a_id:
            print("FAIL  --review-alt refused: no review_b_alt named in profile '%s'" % name)
            return 1
        a_fam = family_of(a_id, a_fam_o)
        a_pool = pool_of(a_id, a_pool_o)
        check_built = built_fam_set if set_status == "known" else set()
        if not a_fam:
            print("FAIL  --review-alt refused: review_b_alt %s: its family is unknown" % a_id)
            return 1
        if a_fam == ra_fam:
            print("FAIL  --review-alt refused: review_b_alt %s is of Review A's family (%s)" % (a_id, ra_fam))
            return 1
        if a_fam and a_fam in check_built:
            print("FAIL  --review-alt refused: review_b_alt %s is of the %s family, which built the branch" % (a_id, a_fam))
            return 1
        if a_id in unavailable:
            print("FAIL  --review-alt refused: review_b_alt %s is marked unavailable" % a_id)
            return 1
        if other_pool == "exhausted" and a_pool == "other":
            print("FAIL  --review-alt refused: review_b_alt %s: its pool is exhausted" % a_id)
            return 1
        b_id, b_fam_o, _ = norm_entry(in_use.get("builder"))
        b_fam = family_of(b_id, b_fam_o)
        if do_probe:
            ok, detail = probe(a_id)
            if ok is PROBE_SIGN_IN:
                print("    probe %-8s %s: tool sign-in required" % ("review_b_alt", a_id))
                print(SIGN_IN_LINE)
                return 5
            print("    probe %-8s %s: %s" % ("review_b_alt", a_id, detail))
            if not ok:
                print("FAIL  --review-alt refused: review_b_alt %s did not answer its probe" % a_id)
                return 1
        fams = {"builder": b_fam, "review_a": ra_fam, "review_b": a_fam}
        known_built = sorted(built_fam_set) if set_status == "known" else []
        chosen = {"profile": name, "builder": b_id, "review_a": ra_id, "review_b": a_id,
                  "families": fams, "other_pool": other_pool, "probed": do_probe,
                  "resolved_at": stamp(now_utc()), "reset_day": roster.get("reset_day"),
                  "deviation": {"review_b_alt": a_id, "reason": review_alt_reason, "branch": bset["branch"],
                                "built": known_built}}
        print("DEVIATION  review_b is %s on request (%s)" % (a_id, review_alt_reason))
        chosen_rebuild_end = None
    else:
        chosen = None
        chosen_rebuild_end = None

    if review_alt_reason is None:
        for prof in profiles:
            ev = _evaluate_profile(prof, True)
            if ev == "sign-in":
                return 5
            if ev == "git-fail":
                print("FAIL  cannot read the families that built this branch (git)")
                return 1
            if ev is None:
                continue
            chosen = {"profile": ev["profile"], "builder": ev["builder"], "review_a": ev["review_a"],
                      "review_b": ev["review_b"], "families": ev["families"], "other_pool": other_pool,
                      "probed": do_probe, "resolved_at": stamp(now_utc()), "reset_day": roster.get("reset_day")}
            if ev["deviation"]:
                chosen["deviation"] = ev["deviation"]
                print("DEVIATION  review_b is %s instead of %s (%s)" % (ev["a_id"], ev["r_id"], ev["deviation"]["reason"]))
            if ev["rebuild"]:
                chosen["rebuild"] = ev["rebuild"]
                chosen_rebuild_end = ev["profile_rebuild_end"]
            break
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
        end = chosen_rebuild_end
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
