#!/usr/bin/env python3
"""wake-timer: a background command that ends at an agent's ceiling, so that its completion
wakes the session (release A4, KP-043).

  python wake-timer.py <seconds> "<what it bounds>"

Started in the background (the app's run-in-background Bash), it sleeps for <seconds> and
prints one line. A scheduled wake-up (CronCreate) does not fire while a background agent is
running, since the session is not idle for the scheduler (proven 2026-10-11, ISS-021 on
reAngle); a background command's completion notification does arrive, so this is the bound
of every waited-on background agent. The loop guard counts an agent as bounded only while a
timer that ends no later than the agent's ceiling is running. Windowless: spawns nothing.
Exit 0 after the sleep; 2 on bad arguments.
"""
import sys
import time


def main(argv):
    if not argv or not argv[0].isdigit():
        print("usage: wake-timer.py <seconds> \"<what it bounds>\"")
        return 2
    seconds = int(argv[0])
    what = " ".join(argv[1:]) or "a background agent"
    print("wake-timer: started for %d s, bounding %s" % (seconds, what), flush=True)
    time.sleep(seconds)
    print("wake-timer: %d s are up - %s reached its ceiling; stop it with TaskStop if it still runs and run its task in the foreground (rule 43)" % (seconds, what))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main(sys.argv[1:]))
