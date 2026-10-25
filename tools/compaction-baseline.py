#!/usr/bin/env python3
"""compaction-baseline: compactions per day per project, by unique compaction markers (plan 14.3).

    python tools/compaction-baseline.py [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--projects <folder>:<name> ...]

Reads every transcript (`*.jsonl`) under the named Claude Code project folders in
`~/.claude/projects/`, each with its `-Workspace` twin (the folder the app made on 2026-10-12 for
the sessions opened in the project's Workspace; item C9 of 2026-10-18), counted with the project's
other folder. A compaction is the record `type == "system", subtype == "compact_boundary"`;
a resumed or forked session copies earlier records, so markers are counted once by their `uuid`
(review R24). Prints, per project and day, the number of compactions, and the sessions seen; then
the totals before and after the digest hook (release 0b, installed 2026-10-04). Read-only; the
transcripts are never written. ASCII-only output on purpose.
"""
import argparse
import collections
import datetime
import glob
import json
import os
import re

HOOK_DATE = "2026-10-04"                                   # release 0b: the digest after every compaction
DEFAULT = [
    ("E--ck04k02s01-reangle-prototype", "reAngle"),
    ("E--p19-technical-documentation-provider", "TDP"),
    ("E--pk02k02s02-short-form-video-factory", "SFVF"),
    ("G--Project-Workspaces-Software-Cursor-short-form-video-factory", "SFVF"),
]


def folders_of(folder):
    """A project's transcript folders: the one named and its `-Workspace` twin (2026-10-12 on)."""
    return [folder] if folder.endswith("-Workspace") else [folder, folder + "-Workspace"]


DAY_RX = re.compile(r'"timestamp":\s*"(\d{4}-\d{2}-\d{2})')


def markers(folder, active):
    """{uuid: (timestamp, sessionId, trigger, preTokens)} over every transcript in the folder; `active`
    collects every day on which any record was written (the denominator of a per-day rate)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.jsonl"))):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = DAY_RX.search(line)
                if m:
                    active.add(m.group(1))
                if "compact_boundary" not in line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("type") != "system" or e.get("subtype") != "compact_boundary" or not e.get("uuid"):
                    continue
                meta = e.get("compactMetadata") or {}
                out.setdefault(e["uuid"], (e.get("timestamp", ""), e.get("sessionId", ""), meta.get("trigger", "?"), meta.get("preTokens")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None)
    ap.add_argument("--until", default=None)
    ap.add_argument("--projects", nargs="*", default=None, help="<folder under ~/.claude/projects>:<name>")
    a = ap.parse_args()
    root = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    pairs = [p.split(":", 1) for p in a.projects] if a.projects else DEFAULT
    per_day = collections.defaultdict(collections.Counter)                # name -> day -> n
    sessions = collections.defaultdict(set)
    triggers = collections.defaultdict(collections.Counter)
    before = collections.Counter()
    after = collections.Counter()
    days_seen = collections.defaultdict(set)
    active_days = collections.defaultdict(set)
    for folder, name in pairs:
        fulls = [os.path.join(root, f) for f in folders_of(folder) if os.path.isdir(os.path.join(root, f))]
        if not fulls:
            print("note: no folder %s" % os.path.join(root, folder))
            continue
        active, found = set(), {}
        for full in fulls:                                         # a marker copied into both folders counts once
            for uuid, rec in markers(full, active).items():
                found.setdefault(uuid, rec)
        for uuid, (ts, sid, trig, pre) in found.items():
            day = ts[:10]
            if (a.since and day < a.since) or (a.until and day > a.until):
                continue
            per_day[name][day] += 1
            sessions[name].add(sid)
            triggers[name][trig] += 1
            days_seen[name].add(day)
            (before if day < HOOK_DATE else after)[name] += 1
        active_days[name] |= {d for d in active if (not a.since or d >= a.since) and (not a.until or d <= a.until)}
    print("compactions per day (unique compact_boundary markers; hook date %s)" % HOOK_DATE)
    for name in sorted(per_day):
        print("\n%s  (%d sessions; triggers %s)" % (name, len(sessions[name]), dict(triggers[name])))
        for day in sorted(per_day[name]):
            print("  %s  %d" % (day, per_day[name][day]))
        d_before = sorted(d for d in active_days[name] if d < HOOK_DATE)
        d_after = sorted(d for d in active_days[name] if d >= HOOK_DATE)
        span = lambda ds: (datetime.date.fromisoformat(ds[-1]) - datetime.date.fromisoformat(ds[0])).days + 1 if ds else 0
        print("  before the hook: %d compactions on %d active days (any record written; %d calendar days) -> %.2f per active day" % (
            before[name], len(d_before), span(d_before), before[name] / len(d_before) if d_before else 0.0))
        print("  after the hook:  %d compactions on %d active days (any record written; %d calendar days) -> %.2f per active day" % (
            after[name], len(d_after), span(d_after), after[name] / len(d_after) if d_after else 0.0))
    print("\nall projects: before %d, after %d" % (sum(before.values()), sum(after.values())))


if __name__ == "__main__":
    main()
