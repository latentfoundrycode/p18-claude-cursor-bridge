"""wake-timer.py (release A4, KP-043): sleeps the seconds it is given and ends with the line the
supervisor reads; refuses bad arguments."""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "wake-timer.py")


def test_the_timer_ends_after_its_seconds_with_the_ceiling_line():
    t0 = time.time()
    p = subprocess.run([sys.executable, PROG, "1", "Review A (a1)"], capture_output=True, text=True)
    assert p.returncode == 0 and time.time() - t0 >= 1 and "reached its ceiling" in p.stdout and "Review A (a1)" in p.stdout and "TaskStop" in p.stdout, p.stdout
    p = subprocess.run([sys.executable, PROG, "soon"], capture_output=True, text=True)
    assert p.returncode == 2 and "usage" in p.stdout
