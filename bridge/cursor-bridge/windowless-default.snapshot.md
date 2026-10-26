# Windowless pytest suite default

This fenced block is the bridge's frozen windowless default for a project's test-root `conftest.py`. It comes from FIX-001 (supervisor standing rule 24, KP-014) and satisfies R-039: every project's pytest suite whose runner the bridge ships a default for carries this block verbatim (see `Cursor-Project-Configuration.md`, windowless-default item). Copy the block below into the rootdir `conftest.py` or into each `testpaths` root's `conftest.py` without change.

```python
import subprocess
import sys

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def windowless_kwargs(kwargs):
    """The keyword arguments of a launch, with CREATE_NO_WINDOW as its creation flags when it sets none.

    FIX-001 (rule 24, KP-014): the suite starts thousands of console programs. Run from a process with no console
    (a headless builder, a hook), Windows gives each one a visible console window; on 2026-10-19 a builder's suite run
    coincided with a crash that followed a flood of terminal windows. A launch that sets creation flags of its own
    keeps them; a grandchild inherits its parent's windowless console, so one level is enough. A launch that redirects
    none of its standard streams gets stdin=DEVNULL as well: Python then hands the child the suite's own output
    handles, where with the new console alone its output would go to that hidden console (lost from a failure report)
    and a read of its input would wait there for ever (bridge-run.py does the same)."""
    if not kwargs.get("creationflags"):
        kwargs = dict(kwargs, creationflags=NO_WINDOW)
        if all(kwargs.get(name) is None for name in ("stdin", "stdout", "stderr")):
            kwargs["stdin"] = subprocess.DEVNULL
    return kwargs


if sys.platform == "win32" and not getattr(subprocess.Popen.__init__, "windowless_default", False):
    _popen_init = subprocess.Popen.__init__

    def _windowless_init(self, *args, **kwargs):
        _popen_init(self, *args, **windowless_kwargs(kwargs))

    _windowless_init.windowless_default = True
    subprocess.Popen.__init__ = _windowless_init
```
