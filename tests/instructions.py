"""The supervisor's instructions as the tests read them: since TASK-010 they are the core,
bridge/commands/supervisor.md, and its phase modules under bridge/cursor-bridge/workflow/phases/, in the
order the core's "The phase modules" table lists them. A test that asserts a passage of the instructions
reads them all, so that a passage moving between the core and a module does not make it fail or pass."""
import os
import re

BRIDGE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "bridge"))
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")


def read(path):
    return open(path, encoding="utf-8").read()


def module_paths():
    """The phase modules, in the order the core's table names them, then any sub-file of a module (sorted)."""
    core = read(CORE)
    table = core.split("\n## The phase modules", 1)[1].split("\n## ", 1)[0]
    keys = re.findall(r"`~/\.claude/cursor-bridge/workflow/phases/([a-z-]+)\.md`", table)
    assert keys, "the core names no phase module"
    paths = [os.path.join(PHASES, key + ".md") for key in keys]
    for key in keys:
        folder = os.path.join(PHASES, key)
        if os.path.isdir(folder):
            for dirpath, _dirs, files in sorted(os.walk(folder)):
                paths += [os.path.join(dirpath, f) for f in sorted(files) if f.endswith(".md")]
    return paths


def instruction_paths():
    return [CORE] + module_paths()


def instructions():
    """The core and every phase module, each ending in a newline, joined in order."""
    parts = []
    for path in instruction_paths():
        text = read(path)
        parts.append(text if text.endswith("\n") else text + "\n")
    return "\n".join(parts)
