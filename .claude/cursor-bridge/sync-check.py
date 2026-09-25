#!/usr/bin/env python3
"""sync-check: does local <base> match the remote's <base>? Deterministic; run from the repo.

  python sync-check.py [--apply] [--strict] [--base main] [--remote origin]

Fetches the remote (read-only on the remote), then compares local <base> with <remote>/<base>
and prints one state:

  IN SYNC       nothing to do                                               exit 0
  NO REMOTE     the repo has no <remote>; nothing to sync (a valid reason)   exit 0
  OFFLINE       the fetch failed; comparison impossible right now            exit 0 (1 with --strict)
  UNPUBLISHED   <remote> has no <base> yet (the first push has not happened) exit 0 (1 with --strict)
  BEHIND        the remote has merges local <base> lacks (the usual cause: a squash merge
                completed on GitHub). With --apply it is fast-forwarded - never merged, never
                rebased; git refuses if a local change would be overwritten, and so does this
                script.                                                     exit 0 applied / 1 not
  AHEAD         local <base> has commits the remote lacks. <base> is protected, so they can
                never be pushed: they are STRANDED and must ride a PR.      exit 2
  DIVERGED      both at once: stranded local commits AND missing remote ones.  exit 2

For AHEAD / DIVERGED the script prints the stranded commits and the rescue sequence (keep the
commits on a rescue branch, repoint <base> at the remote, carry what is still needed through
a PR). Nothing is deleted; no history on the remote is touched. It never runs the rescue itself.

Informational lines (never change the exit code): the current branch; whether it contains
<remote>/<base> (a branch started from a stale <base> does not); uncommitted changes.

--strict is for project end: OFFLINE and UNPUBLISHED become failures, because "Project
complete" requires the remote to hold the release. NO REMOTE stays valid.
ASCII output only (Windows cp1252 consoles).
"""
import argparse
import datetime
import subprocess
import sys


def git(*args):
    p = subprocess.run(["git"] + list(args), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def first_error(err):
    lines = [l for l in err.splitlines() if l.strip()]
    for l in lines:
        if l.lower().startswith(("fatal:", "error:")):
            return l
    return lines[-1] if lines else "no detail"


def ok(*args):
    return git(*args)[0] == 0


def main():
    ap = argparse.ArgumentParser(description="Compare local <base> with the remote's <base>.")
    ap.add_argument("--apply", action="store_true", help="fast-forward local <base> when BEHIND")
    ap.add_argument("--strict", action="store_true", help="project end: OFFLINE/UNPUBLISHED fail")
    ap.add_argument("--base", default="main")
    ap.add_argument("--remote", default="origin")
    a = ap.parse_args()
    base, remote = a.base, a.remote
    rbase = "%s/%s" % (remote, base)

    if not ok("rev-parse", "--git-dir"):
        print("sync-check: not a git repository")
        return 1
    if not ok("remote", "get-url", remote):
        print("NO REMOTE: this repository has no '%s'; nothing to sync." % remote)
        return 0

    code, _, err = git("fetch", "--prune", remote)
    if code != 0:
        print("OFFLINE: 'git fetch %s' failed - %s" % (remote, first_error(err)))
        print("  The comparison is impossible right now; re-run when the remote is reachable.")
        return 1 if a.strict else 0

    if not ok("rev-parse", "--verify", "--quiet", "refs/heads/" + base):
        print("sync-check: there is no local branch '%s'" % base)
        return 1
    if not ok("rev-parse", "--verify", "--quiet", "refs/remotes/" + rbase):
        print("UNPUBLISHED: %s has no '%s' yet - the first push has not happened." % (remote, base))
        return 1 if a.strict else 0

    _, counts, _ = git("rev-list", "--left-right", "--count", "%s...%s" % (base, rbase))
    ahead, behind = (int(x) for x in counts.split())
    _, cur, _ = git("rev-parse", "--abbrev-ref", "HEAD")
    _, dirty, _ = git("status", "--porcelain")

    result = 0
    if ahead == 0 and behind == 0:
        print("IN SYNC: %s = %s" % (base, rbase))
    elif ahead == 0:
        print("BEHIND: %s lacks %d commit(s) on %s" % (base, behind, rbase))
        _, log, _ = git("log", "--oneline", "%s..%s" % (base, rbase))
        for line in log.splitlines()[:20]:
            print("    " + line)
        if not a.apply:
            print("  Re-run with --apply to fast-forward.")
            result = 1
        else:
            if cur == base:
                code, _, err = git("merge", "--ff-only", rbase)
            else:
                # updates the ref only if it is a fast-forward; the branch is not checked out
                code, _, err = git("fetch", remote, "%s:%s" % (base, base))
            if code == 0:
                print("  FAST-FORWARDED: %s now = %s" % (base, rbase))
            else:
                print("  FAST-FORWARD REFUSED by git - %s" % first_error(err))
                print("  Usually an uncommitted change to a file the merge touches: commit it on a")
                print("  branch (or move it aside), then re-run with --apply.")
                result = 1
    else:
        state = "DIVERGED" if behind else "AHEAD"
        print("%s: %s has %d commit(s) %s lacks%s - STRANDED (%s is protected; they can never be pushed)"
              % (state, base, ahead, rbase,
                 (" and lacks %d of its commit(s)" % behind) if behind else "", base))
        _, log, _ = git("log", "--oneline", "%s..%s" % (rbase, base))
        for line in log.splitlines()[:20]:
            print("    " + line)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        rescue = "rescue/%s-%s" % (base, stamp)
        print("  Rescue (nothing is deleted; run each line on its own):")
        if cur == base:
            print("    git switch -c %s" % rescue)
        else:
            print("    git branch %s %s" % (rescue, base))
        print("    git branch -f %s %s" % (base, rbase))
        print("  Then decide per commit: still needed -> a branch from %s that cherry-picks it" % rbase)
        print("  and rides a PR through the gate; bookkeeping already superseded -> leave it on the")
        print("  rescue branch. Record the cause as an issue.")
        result = 2

    # informational
    if cur != "HEAD" and cur != base:
        contains = ok("merge-base", "--is-ancestor", rbase, "HEAD")
        print("Current branch: %s - %s" % (
            cur, "contains %s" % rbase if contains else
            "does NOT contain %s (started from an older %s)" % (rbase, base)))
    else:
        print("Current branch: %s" % cur)
    if dirty:
        print("Uncommitted changes: %d path(s)" % len(dirty.splitlines()))
    return result


if __name__ == "__main__":
    sys.exit(main())
