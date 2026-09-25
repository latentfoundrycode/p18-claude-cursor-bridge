#!/usr/bin/env python3
"""roster-check: resolve which models fill the builder / Review A / Review B roles today,
prove three distinct families, and (optionally) prove each model answers.

  python roster-check.py docs/ROSTER.json [--command "<delegate command>"] [--no-probe] [--out docs/ROSTER.resolved.json]

docs/ROSTER.json (v2):
{
  "other_pool": "available" | "exhausted",      <- OWNER-SET. Cursor's "other models" usage
                                                    pool (OpenAI / Google / Anthropic / unprefixed
                                                    Grok). A probe cannot see 1% remaining; the
                                                    owner flips this when the dashboard says so.
  "review_a": "claude-opus-4-8",                  <- Review A runs in Claude Code, not Cursor.
  "profiles": [                                   <- tried in order; the first usable one wins
    {"name": "full",   "builder": "cursor-grok-4.6-high", "review_b": "gpt-5.6-sol-high"},
    {"name": "native", "builder": "composer-2.5",         "review_b": "cursor-grok-4.6-high"}
  ]
}
A model entry is an id string or {"model": id, "family": name, "pool": "native"|"other"}.
Pool is inferred from the id: `composer-*` and `cursor-*` are Cursor-native, all else "other".
A profile is skipped when other_pool is "exhausted" and any of its models is in the other
pool. Unless --no-probe, the builder and Review B of a candidate profile are each sent a
one-word request through `cursor-agent -p -f --model <id>`; a refusal, empty reply, or
timeout marks the profile unusable (this catches hard failures only, never a nearly-empty
quota). The chosen profile's three families must be distinct. The result is written to
docs/ROSTER.resolved.json for the delegate and Review B commands to read.
--record-failure <model> --stderr-file <path> [--stdout-file <path>]
  Classify a failed cursor-agent call. USAGE-LIMIT (a usage/quota/limit/billing message) or
  a second consecutive failure of the same model marks the model's pool exhausted in
  docs/ROSTER.json automatically (auto_exhausted_at / auto_exhausted_reason) and exits 3 =
  "re-resolve and restart the step". A first non-limit failure exits 4 = "transient - retry
  the same step once". The count lives in the roster (failures.<model>) and resets on
  success or on marking.
--mark-exhausted   the owner said "usage exhausted": stamp other_pool exhausted now (UTC).
--mark-reset       the owner said "usage reset": restore other_pool and clear marks now.
Automatic reset: "reset_day" (day of month, UTC; e.g. 16) in the roster. When other_pool is
exhausted and the current UTC time is at or past 00:00 UTC of the first reset_day strictly
after exhausted_at, the check restores other_pool to "available" by itself, clears the
unavailable marks and failure counts, and says so. Timestamps are UTC. ROSTER_NOW=<ISO UTC>
overrides "now" for tests.
Exit 0 = resolved; 1 = no usable profile, a family collision, or a command mismatch;
2 = cannot read; 3 = pool/model marked exhausted, re-resolve; 4 = transient, retry once.
ASCII-only on purpose.
"""
import datetime
import json
import os
import re
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
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
    core = m[len("cursor-"):] if m.startswith("cursor-") else m   # cursor-grok-4.6 is xAI, hosted by Cursor
    for prefix, fam in FAMILY_PREFIXES:
        if core.startswith(prefix) or ("-" + prefix) in core or ("/" + prefix) in core:
            return fam
    return None


def pool_of(model_id, override=None):
    if override:
        return override.lower()
    m = model_id.lower()
    return "native" if (m.startswith("composer") or m.startswith("cursor-")) else "other"


def cursor_agent_cmd():
    """Locate the CLI the way Windows needs it: the .cmd launcher run through cmd.exe, or the
    binary/shim elsewhere. Python's subprocess does not resolve a Git-Bash shim or a .cmd by
    bare name."""
    import shutil
    for cand in ("cursor-agent.cmd", "cursor-agent.exe", "cursor-agent"):
        found = shutil.which(cand)
        if found:
            break
    else:
        found = os.path.join(os.environ.get("LOCALAPPDATA", ""), "cursor-agent", "cursor-agent.cmd")
        if not os.path.isfile(found):
            return None
    if found.lower().endswith((".cmd", ".bat")):
        return ["cmd.exe", "/d", "/c", found]
    return [found]


def probe(model_id):
    """Return (ok, detail). ok only when the model replied 'OK' (case-insensitive) within the timeout."""
    launcher = cursor_agent_cmd()
    if launcher is None:
        return False, "cursor-agent not found (PATH or %LOCALAPPDATA%/cursor-agent)"
    try:
        p = subprocess.run(launcher + ["-p", "-f", "--model", model_id, PROBE_PROMPT],
                           capture_output=True, text=True, timeout=PROBE_TIMEOUT, creationflags=NO_WINDOW)
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
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(roster, f, indent=2); f.write("\n")
        print("AUTO-RESET  other_pool restored to 'available' (reset day %d passed at %s; exhausted since %s)" % (int(reset_day), stamp(due), stamp(ex)))
        return True
    print("note  other_pool exhausted since %s; automatic reset due %s (reset_day %d)" % (stamp(ex), stamp(due), int(reset_day)))
    return False


USAGE_LIMIT_PATTERNS = [
    r"usage[\s-]*limit", r"\busage\b.*\b(exhaust|exceed|reached|used up)", r"\bquota\b",
    r"\blimit\b.*\b(reached|exceeded)", r"exceeded.*\blimit", r"insufficient (credits|balance|usage)",
    r"no (remaining|more) (credits|usage|requests)", r"upgrade (your )?plan", r"billing", r"out of (credits|usage)",
    r"spend(ing)? limit", r"\b402\b", r"payment required",
]


def classify_failure(text):
    t = (text or "").lower()
    for pat in USAGE_LIMIT_PATTERNS:
        if re.search(pat, t):
            return "USAGE-LIMIT", pat
    return "OTHER", ""


def record_failure(path, roster, model, text):
    """Mark the model's pool exhausted on a usage-limit message or a second consecutive
    failure; otherwise count it. Writes the roster. Returns the exit code (3 or 4)."""
    kind, pat = classify_failure(text)
    failures = roster.setdefault("failures", {})
    count = failures.get(model, 0) + 1
    failures[model] = count
    pool = pool_of(model)
    when = stamp(now_utc())
    excerpt = (text or "").strip().replace("\n", " ")[:300]
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
        failures[model] = 0
        code = 3
    else:
        print("TRANSIENT  %s: first failure, not a usage-limit message - retry the same step once." % model)
        print("           excerpt: %s" % excerpt)
        code = 4
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(roster, f, indent=2); f.write("\n")
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
        roster = json.load(open(path, encoding="utf-8-sig"))
    except Exception as e:
        print("CANNOT VERIFY: cannot read %s (%s)" % (path, e))
        return 2

    if "--mark-exhausted" in argv:
        roster["other_pool"] = "exhausted"
        roster["exhausted_at"] = stamp(now_utc())
        roster["exhausted_reason"] = "owner said usage exhausted"
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(roster, f, indent=2); f.write("\n")
        print("MARKED  other_pool exhausted at %s (owner)" % roster["exhausted_at"])
        return 0
    if "--mark-reset" in argv:
        clear_marks(roster, "owner said usage reset")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(roster, f, indent=2); f.write("\n")
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

    maybe_auto_reset(path, roster)
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
    sys.exit(main())
