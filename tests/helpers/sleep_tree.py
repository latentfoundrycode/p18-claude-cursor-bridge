"""A parent that starts a child; both record their pid and sleep. Used by test_bridge_run."""
import os
import subprocess
import sys
import time

pidfile = sys.argv[1]
code = "import sys,os,time; open(sys.argv[1],'a').write(str(os.getpid())+chr(10)); time.sleep(600)"
child = subprocess.Popen([sys.executable, "-c", code, pidfile])
with open(pidfile, "a") as f:
    f.write(str(os.getpid()) + chr(10))
time.sleep(600)
