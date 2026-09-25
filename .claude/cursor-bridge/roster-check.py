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
Exit 0 = resolved; 1 = no usable profile, a family collision, or a command mismatch;
2 = cannot read. ASCII-only on purpose.
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


def main():
    argv = sys.argv[1:]
    if not argv or argv[0].startswith("--"):
        print("usage: roster-check.py docs/ROSTER.json [--command \"<delegate command>\"] [--no-probe] [--out <path>]")
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

    other_pool = (roster.get("other_pool") or "available").lower()
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
            print("    skip: uses the other-models pool, which the owner marked exhausted"); continue
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
                  "resolved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
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
