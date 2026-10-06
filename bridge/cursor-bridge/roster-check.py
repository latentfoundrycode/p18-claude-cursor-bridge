#!/usr/bin/env python3
"""roster-check: resolve which models fill the builder / Review A / Review B roles today,
prove three distinct families, and (optionally) prove each model answers.

  python roster-check.py docs/ROSTER.json [--command "<delegate command>"] [--no-probe] [--out docs/ROSTER.resolved.json]

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
    {"name": "native", "builder": "composer-2.5",  "review_b": "grok-4.7-high"}
  ]
}
A model entry is an id string or {"model": id, "family": name, "pool": "native"|"other"}.
Pool is inferred from the id per Cursor's docs: Grok (any effort/host prefix) and Composer are
the "Cursor Models" pool (native); every third-party model is "Other Models".
A profile is skipped when other_pool is "exhausted" and any of its models is in the other
pool. Unless --no-probe, the builder and Review B of a candidate profile are each sent a
one-word request through `cursor-agent -p -f --model <id>`; a refusal, empty reply, or
timeout marks the profile unusable (this catches hard failures only, never a nearly-empty
quota). The chosen profile's three families must be distinct. The result is written to
docs/ROSTER.resolved.json for the delegate and Review B commands to read.
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
  automatic "unavailable" mark expires after 6 hours.
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
Exit 0 = resolved; 1 = no usable profile, a family collision, or a command mismatch;
2 = cannot read or a wrong model argument; 3 = pool/model marked exhausted, re-resolve;
4 = transient, retry once; 5 = repeated connection failures or time-outs, tell the owner.
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
              "unavailable", "failures", "connection_failures", "last_reset")
NL = chr(10)
PROBE_PROMPT = "Reply with exactly the single word OK and nothing else."
PROBE_TIMEOUT = 150

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


def probe(model_id):
    """Return (ok, detail). ok only when the model replied 'OK' (case-insensitive) within the timeout."""
    launcher = cursor_agent_cmd()
    if launcher is None:
        return False, "cursor-agent not found (PATH or %LOCALAPPDATA%/cursor-agent)"
    try:
        env = bridge_env.stripped_env()
    except bridge_env.AgentHomeError as e:
        return False, str(e)
    try:
        p = subprocess.run(launcher + ["-p", "-f", "--model", model_id, PROBE_PROMPT],
                           capture_output=True, text=True, timeout=PROBE_TIMEOUT, creationflags=NO_WINDOW,
                           env=env)
    except subprocess.TimeoutExpired:
        return False, "timeout after %ds" % PROBE_TIMEOUT
    except FileNotFoundError:
        return False, "cursor-agent launcher not executable: %s" % launcher[0]
    out = (p.stdout or "").strip()
    if p.returncode == 0 and out.strip().strip(".").upper() == "OK":
        return True, "answered"
    err = (p.stderr or "").strip().replace("\n", " ")[:200]
    return False, "exit %d; stdout=%r; stderr=%r" % (p.returncode, out[:80], err)


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


def record_failure(path, roster, model, text):
    """Mark the model's pool exhausted on a usage-limit message or a second consecutive
    failure within FAILURE_WINDOW_HOURS; a connection error is transient and never counted;
    otherwise count it. Writes the roster. Returns the exit code (2, 3 or 4)."""
    if model not in roster_models(roster):
        print("CANNOT RECORD: %r is not a model in this roster (%s)" % (model, ", ".join(sorted(roster_models(roster)))))
        print("               the argument after --record-failure must be the model id of the failed call; nothing was changed")
        return 2
    kind, pat = classify_failure(text)
    now = now_utc()
    when = stamp(now)
    excerpt = (text or "").strip().replace(NL, " ")[:300]
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
            print("           excerpt: %s" % excerpt)
            return 5
        print("TRANSIENT  %s: connection error or time-out (%s), %d of %d - retry the same step once." % (model, pat, count, CONNECTION_RETRIES))
        print("           excerpt: %s" % excerpt)
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
        print("           excerpt: %s" % excerpt)
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
        text = ""
        for flag in ("--stderr-file", "--stdout-file"):
            if flag in argv and argv.index(flag) + 1 < len(argv):
                try:
                    text += open(argv[argv.index(flag) + 1], encoding="utf-8", errors="replace").read() + "\n"
                except OSError:
                    pass
        return record_failure(path, roster, model, text)

    if "--record-success" in argv:
        model = argv[argv.index("--record-success") + 1]
        changed = (roster.get("failures") or {}).pop(model, None) is not None
        changed = ((roster.get("connection_failures") or {}).pop(model, None) is not None) or changed
        if changed:
            save_state(path, roster)
        print(("ok    failure count cleared for %s" if changed else "ok    no failure count for %s") % model)
        return 0

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

    print("roster-check: other_pool=%s  review_a=%s (%s)" % (other_pool, ra_id, ra_fam))
    chosen = None
    for prof in profiles:
        name = prof.get("name", "?")
        b_id, b_fam_o, b_pool_o = norm_entry(prof.get("builder"))
        r_id, r_fam_o, r_pool_o = norm_entry(prof.get("review_b"))
        b_fam, r_fam = family_of(b_id, b_fam_o), family_of(r_id, r_fam_o)
        b_pool, r_pool = pool_of(b_id, b_pool_o), pool_of(r_id, r_pool_o)
        print("  profile %-8s builder=%s (%s, %s)  review_b=%s (%s, %s)" % (name, b_id, b_fam, b_pool, r_id, r_fam, r_pool))
        if b_fam is None or r_fam is None:
            print("    skip: family unknown - add {\"model\": ..., \"family\": ...}"); continue
        if other_pool == "exhausted" and ("other" in (b_pool, r_pool)):
            how = (" automatically at " + roster["auto_exhausted_at"]) if roster.get("auto_exhausted_at") else " by the owner"
            print("    skip: uses the other-models pool, marked exhausted%s" % how); continue
        if b_id in unavailable or r_id in unavailable:
            print("    skip: a model was marked unavailable after repeated failures (%s)" % ", ".join(m for m in (b_id, r_id) if m in unavailable)); continue
        fams = {"builder": b_fam, "review_a": ra_fam, "review_b": r_fam}
        if len(set(fams.values())) < 3:
            print("    skip: family collision %s" % fams); continue
        if do_probe:
            usable = True
            for role, mid in (("builder", b_id), ("review_b", r_id)):
                ok, detail = probe(mid)
                print("    probe %-8s %s: %s" % (role, mid, detail))
                if not ok:
                    usable = False
            if not usable:
                print("    skip: a model did not answer"); continue
        chosen = {"profile": name, "builder": b_id, "review_a": ra_id, "review_b": r_id, "families": fams,
                  "other_pool": other_pool, "probed": do_probe,
                  "resolved_at": stamp(now_utc()), "reset_day": roster.get("reset_day")}
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
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(chosen, f, indent=2); f.write("\n")
    print("RESOLVED profile '%s': builder=%s  review_a=%s  review_b=%s  -> %s" % (
        chosen["profile"], chosen["builder"], chosen["review_a"], chosen["review_b"], out_path))
    if chosen["profile"] != profiles[0].get("name", "?"):
        print("NOTE  the preferred profile '%s' is not in use - report this to the owner in the first line" % profiles[0].get("name", "?"))
    return 0 if ok else 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
