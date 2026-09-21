#!/usr/bin/env python3
"""bench-check: compare benchmark results against budgets and a committed baseline.

  python bench-check.py bench/budgets.json bench/baseline.json bench/results/latest.json [--update-baseline]

Per budget (Performance-Conventions.md section 3):
  OVER BUDGET   value exceeds max (or falls below min)                -> FAIL
  REGRESSION    worse than baseline by more than tolerance_pct        -> FAIL
  NOT MEASURED  the budget's benchmark/metric is absent from results  -> FAIL
  IMPROVED      better than baseline by more than tolerance_pct       -> note (move the baseline in an optimization commit)
  OK            within budget and within the band
Metrics present in the baseline but without a budget are regression-checked with a
default 10% band. Results with neither budget nor baseline are listed as NEW.
--update-baseline writes the results into the baseline file (optimization commits only).
Exit 0 = no FAIL, 1 = at least one FAIL, 2 = cannot read an input.
ASCII-only on purpose (cp1252 consoles).
"""
import json
import sys

DEFAULT_TOL = 10.0
LOWER_IS_BETTER_HINT = ("ms", "mb", "usd", "tokens", "bytes", "s", "kb", "gb")


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("bench-check: cannot read %s (%s)" % (path, e))
        sys.exit(2)


def index(results):
    out = {}
    for r in results.get("results", []):
        out[(r.get("benchmark"), r.get("metric"))] = float(r.get("value"))
    return out


def lower_is_better(budget, metric):
    if budget is not None:
        if "max" in budget:
            return True
        if "min" in budget:
            return False
    m = (metric or "").lower()
    return any(m == h or m.endswith("_" + h) or m.endswith(h) for h in LOWER_IS_BETTER_HINT)


def pct_change(new, old, lower_better):
    if old == 0:
        return 0.0
    worse = (new - old) if lower_better else (old - new)
    return 100.0 * worse / abs(old)  # positive = worse


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    update = "--update-baseline" in sys.argv
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    budgets = load(argv[0]).get("budgets", [])
    baseline_doc = load(argv[1])
    latest_doc = load(argv[2])
    base = index(baseline_doc)
    cur = index(latest_doc)

    fails = notes = 0
    seen = set()
    for b in budgets:
        key = (b.get("benchmark"), b.get("metric"))
        seen.add(key)
        bid = b.get("id", "?")
        tol = float(b.get("tolerance_pct", DEFAULT_TOL))
        lb = lower_is_better(b, key[1])
        if key not in cur:
            print("FAIL  %-9s %s/%s  NOT MEASURED" % (bid, key[0], key[1])); fails += 1; continue
        v = cur[key]
        limit = b.get("max") if lb else b.get("min")
        over = (limit is not None) and ((v > float(limit)) if lb else (v < float(limit)))
        if over:
            print("FAIL  %-9s %s/%s = %g  OVER BUDGET (limit %g)" % (bid, key[0], key[1], v, float(limit))); fails += 1; continue
        if key in base:
            ch = pct_change(v, base[key], lb)
            if ch > tol:
                print("FAIL  %-9s %s/%s = %g  REGRESSION %+.1f%% vs baseline %g (tolerance %g%%)" % (bid, key[0], key[1], v, ch, base[key], tol)); fails += 1; continue
            if ch < -tol:
                print("note  %-9s %s/%s = %g  IMPROVED %+.1f%% vs baseline %g - move the baseline in an optimization commit" % (bid, key[0], key[1], v, ch, base[key])); notes += 1; continue
            print("ok    %-9s %s/%s = %g  within budget %s%g, %+.1f%% vs baseline" % (bid, key[0], key[1], v, "<=" if lb else ">=", float(limit) if limit is not None else float("nan"), ch))
        else:
            print("ok    %-9s %s/%s = %g  within budget (no baseline yet - commit one)" % (bid, key[0], key[1], v)); notes += 1

    for key, old in sorted(base.items()):
        if key in seen:
            continue
        if key not in cur:
            print("FAIL  %-9s %s/%s  NOT MEASURED (baselined metric missing)" % ("-", key[0], key[1])); fails += 1; continue
        lb = lower_is_better(None, key[1])
        ch = pct_change(cur[key], old, lb)
        if ch > DEFAULT_TOL:
            print("FAIL  %-9s %s/%s = %g  REGRESSION %+.1f%% vs baseline %g (no budget; default %g%%)" % ("-", key[0], key[1], cur[key], ch, old, DEFAULT_TOL)); fails += 1
        elif ch < -DEFAULT_TOL:
            print("note  %-9s %s/%s = %g  IMPROVED %+.1f%% vs baseline %g" % ("-", key[0], key[1], cur[key], ch, old)); notes += 1
        else:
            print("ok    %-9s %s/%s = %g  %+.1f%% vs baseline" % ("-", key[0], key[1], cur[key], ch))
    for key in sorted(cur):
        if key not in seen and key not in base:
            print("new   %-9s %s/%s = %g  (no budget, no baseline)" % ("-", key[0], key[1], cur[key])); notes += 1

    print("bench-check: %d budget(s), %d FAIL, %d note(s)" % (len(budgets), fails, notes))
    if update:
        if fails:
            print("bench-check: --update-baseline refused while a FAIL is open")
            return 1
        with open(argv[1], "w", encoding="utf-8", newline="\n") as f:
            json.dump(latest_doc, f, indent=2); f.write("\n")
        print("bench-check: baseline updated from results")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
