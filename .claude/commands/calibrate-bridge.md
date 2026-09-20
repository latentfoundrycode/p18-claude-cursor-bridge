---
description: Re-read the installed bridge and align the running project with it — verifies the install, applies only the adjustments the project's current phase calls for, reopens no gate
argument-hint: [check]
---

# Calibrate to the installed bridge

The owner has updated the bridge tree under `~/.claude/` and restarted the app. Two things
are uncertain to them and must become certain: **did the copy land**, and **is this running
supervisor now working from the new rules**. This command answers both, then aligns the
project in flight with the new rules **without disturbing its order** — nothing approved is
re-presented, nothing in progress is restarted, and only the adjustments the new release
lists for the project's current or future phases are applied.

If `$ARGUMENTS` is `check`, do step 1 only and report.

## 1. Verify the install — deterministically

```bash
python ~/.claude/cursor-bridge/bridge-check.py
```

It hashes every governance file against the release manifest and prints `OK` / `STALE` /
`MISSING` per file and a `RESULT` line. **If the result is `NOT CALIBRATED`, stop here.**
Report it as a **run sheet** (`explain-for-decision` skill): which files are stale or
missing, the terminal to use, the literal copy commands from the bridge release folder to
`C:\Users\<you>\.claude\…` with the placeholder explained, the app restart, and
"then run `/calibrate-bridge` again". Do nothing else until the check passes — calibrating
to a half-copied tree would leave the project on a mixture of two releases.

## 2. Re-read the governing files — they supersede what you hold in context

Read, whole, in this order — even if you believe you already know them, and even if
the version has not changed (the owner is asking for certainty, not a version check):

1. `~/.claude/commands/supervisor.md`
2. `~/.claude/cursor-bridge/Merge-Verification-Policy.md`
3. `~/.claude/cursor-bridge/Cursor-Project-Configuration.md`
4. `~/.claude/cursor-bridge/Known-Pitfalls.md`
5. `~/.claude/cursor-bridge/Observability-Conventions.md` (UI-bearing projects)
6. Every `SKILL.md` under `~/.claude/skills/`

Subagent definitions under `~/.claude/agents/` are loaded fresh each time a subagent is
spawned, so they need no re-read here — but note that any subagent spawned **before** the
restart ran on the old definition; results from those runs are not re-done, they were valid
under the rules in force at the time.

From this point on, the text you just read is the governing text. Where anything you
remember from earlier in this conversation conflicts with it, the file wins.

## 3. Find the release delta

```bash
cat ~/.claude/cursor-bridge/VERSION
```

Compare with `Bridge version:` in `docs/PROJECT_STATUS.md` (absent means "before
2026.09.20"). Read `~/.claude/cursor-bridge/CHANGELOG.md` and collect the **Running
projects must** items of every entry newer than the recorded version. If the versions are
equal, there is no delta: say so, still confirm step 2 was done, update nothing but the
`Calibrated:` line in step 5, and report.

## 4. Apply the delta by phase — reopen nothing

Determine the project's current phase and position from `docs/PROJECT_STATUS.md` (phase,
current increment, current stage, what is awaiting the owner). Then sort every collected
item into exactly one of:

- **Now** — marked *(all phases)*, or marked for the current phase, or marked for a phase
  already passed whose item is a *record-keeping or configuration* addition (a status field,
  a hook, a Documents file that should already exist). Apply these in this command.
- **Later** — marked for a phase not yet reached. Record them under `Calibration pending:` in
  `PROJECT_STATUS.md` with the phase, and apply each when that phase begins. Do not pre-empt.
- **Passed** — marked for a phase already completed and requiring a *decision or gate* (a
  re-presented plan, a re-approved design). These are **not** applied. A gate the owner
  approved stays approved. Record them as "not applied — gate passed" so the omission is
  visible, not silent.

Rules while applying **Now** items:

- Configuration goes through `cursor-configurator` and is **append-only**: add the missing
  file, the missing hook entry, the missing pre-commit line; never rewrite an existing
  config. Commit the configuration change as its own checkpoint, exactly like Phase 5.
- A new field that carries an owner setting (the refactoring dial, a term classification)
  gets the release's **default**, and the report tells the owner in one line what was
  defaulted and how to change it. It does not become a question that stalls the loop.
- An increment currently delegated or under review finishes under the brief and rules it
  started with. The next brief is packaged under the new templates.
- A Documents file whose creation trigger has already passed (a Project Summary on a project
  past Phase 2) is created at the **next reflection point**, not now, unless the owner asks —
  reflection points are the only time Documents is written.
- Nothing here escalates. If an item genuinely cannot be applied without a decision only the
  owner can take (the layout rename of a pre-layout project), it becomes the single
  decision line of the report, with a run sheet, and the loop continues without it.

## 5. Record and report

Update `docs/PROJECT_STATUS.md`: `Bridge version: <new>` and a line
`Calibrated: <date> from <old> to <new> — applied: <items>; pending: <items @ phase>; not applied (gate passed): <items>`.
Commit it with the configuration checkpoint if there was one.

Report under the "Reporting to the user" rules — first line is the one thing they own or
**"Nothing needed — calibrated to <version>"**. Then, marked FYI:

```
Install check: <N> files OK (bridge <version>, <generated>)
Re-read: supervisor, merge policy, configuration, pitfalls, skills — in force from now
Delta: <old> → <new>
  applied now:     <items, one line each>
  pending:         <item @ phase>
  not applied:     <item — gate already passed>
Defaults set for you: <e.g. refactoring pass ON for remaining stages — say "off" to change>
Project position unchanged: <phase / increment / stage>
```

The test of a good calibration: the owner can read the first line and know whether they
are needed; the project's next action is the same one it was going to take before, executed
under the new rules; and nothing that was approved has been asked for again.
