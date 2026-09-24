#!/usr/bin/env python3
"""roster-check: the builder, Review A, and Review B must be three different model families.

The merge gate's fourth condition (Merge-Verification-Policy.md) depends on this, and a
project once ran its builder on Review B's family without noticing (KP-022). This makes
the invariant a check instead of a sentence.

  python roster-check.py docs/ROSTER.json [--command "<the delegate command line>"]

docs/ROSTER.json:
  {"builder": "grok-4.6", "review_a": "claude-opus-4-8", "review_b": "gpt-5.6-sol"}
Optional per-entry family override when a model id is not recognised:
  {"builder": {"model": "my-house-model", "family": "acme"}, ...}
--command asserts the delegate command carries `--model <builder>` (so the family is set,
not inherited from a default that can change).
Exit 0 = three distinct families and (if given) the command matches; 1 = a collision,
an unknown family, or a command mismatch; 2 = cannot read. ASCII-only on purpose.
"""
import json
import re
import sys

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
    ("glm", "zhipu"), ("minimax", "minimax"), ("cursor", "cursor"), ("composer", "cursor"),
]


def family_of(entry):
    if isinstance(entry, dict):
        if entry.get("family"):
            return entry["family"].lower(), entry.get("model", "?")
        entry = entry.get("model", "")
    m = (entry or "").lower().replace("_", "-").strip()
    for prefix, fam in FAMILY_PREFIXES:
        if m.startswith(prefix) or ("-" + prefix) in m or ("/" + prefix) in m:
            return fam, entry
    return None, entry


def main():
    argv = sys.argv[1:]
    if not argv:
        print("usage: roster-check.py docs/ROSTER.json [--command \"<delegate command>\"]")
        return 2
    try:
        roster = json.load(open(argv[0], encoding="utf-8-sig"))
    except Exception as e:
        print("CANNOT VERIFY: cannot read %s (%s)" % (argv[0], e))
        return 2
    command = argv[argv.index("--command") + 1] if "--command" in argv and argv.index("--command") + 1 < len(argv) else None

    roles = ("builder", "review_a", "review_b")
    fams, ok = {}, True
    for r in roles:
        if r not in roster:
            print("FAIL  roster has no '%s' entry" % r); ok = False; continue
        fam, model = family_of(roster[r])
        if fam is None:
            print("FAIL  %-9s %s  family unknown - add {\"model\": ..., \"family\": ...}" % (r, model)); ok = False; continue
        fams[r] = (fam, model)
        print("ok    %-9s %s  family=%s" % (r, model, fam))
    seen = {}
    for r, (fam, model) in fams.items():
        if fam in seen:
            print("FAIL  %s and %s share the family '%s' - the gate's decorrelation is void" % (seen[fam], r, fam)); ok = False
        seen.setdefault(fam, r)
    if command is not None and "builder" in fams:
        builder_model = fams["builder"][1]
        m = re.search(r"--model[=\s]+(\S+)", command)
        if not m:
            print("FAIL  delegate command carries no --model; the builder family would be a default that can change"); ok = False
        elif m.group(1).strip("\"'") != builder_model:
            print("FAIL  delegate command uses --model %s but the roster's builder is %s" % (m.group(1), builder_model)); ok = False
        else:
            print("ok    delegate command sets --model %s" % builder_model)
    print("roster-check: %s" % ("three distinct families" if ok else "INVALID ROSTER"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
