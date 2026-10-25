# Claude Code extension

## Add at design.sections

The host is Claude Code, and its extension points include its commands, agents, skills, hooks, settings and permission rules. The version each fact in the design's host section was checked on is the one `claude --version` prints. The facts that cost most when they were wrong were of this kind: when a hook runs and what its output does (the Stop hook's), and which commands a permission rule matches (a rule for git that does not match git given a folder with -C); each such fact is checked in Claude Code itself before the design relies on it. Such a check runs, as the type's probes do, in a Claude Code kept apart from the owner's own.
