# /evaluate-reports — the report cycle (plan 12; release A3)

A maintainer command, run in the bridge project by the maintainer session (the Bridge's Administrator Agent), never by a project supervisor. It turns what the projects report about the bridge into decisions, on a schedule, with a ledger so that nothing is raised twice.

**What is read, in place** (never copied, never edited): each project's `<Name> Issues During Development and Their Solutions.md` and `<Name> Claude-Cursor Bridge Feedback.md` in its `Documents/` folder; the supervisor's private notes (`~/.claude/projects/<key>/memory/*.md`); and, since the last run, the owner's typed messages and question-form answers from the projects' session records, which a program extracts with stated filters (a session continued after a compaction is followed; subagents' records, app-inserted text and the maintainer session's own messages are left out; a key's value is withheld).

**Steps, in order.**

1. **Collect.** From the bridge's root (the folder holding `Workspace/` and `Reports/`):

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py collect
   ```

   It writes `Reports/Evaluations/<date>/unprocessed.md`: every entry absent from the ledger (`Reports/ledger.json`) or whose text changed since it was evaluated (shown with the earlier verdict). "Nothing new" ends the run in one line, with no file. Then:

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py extract --since <the date of the last run>
   ```

   It writes `Reports/Evaluations/<date>/owner-messages-<project>.md`. Read them for prods to a stalled loop, complaints, and incidents the documents do not mention; an incident found only there becomes an entry of the evaluation like any other.

2. **Classify** each entry: a bridge defect; a gap in the bridge; a pitfall worth recording; already addressed (cite the release); already planned (cite the plan's section); or project-specific, needing nothing.

3. **Check** each verdict against the installed governance (`~/.claude`), the restructuring plan and its pinned list, so that nothing is proposed twice and nothing pinned is reopened unasked.

4. **Write** `Reports/Evaluations/<date>.md`: one table of entries and verdicts; then what the maintainer decided, with reasons; then the decisions for the owner, each with what would change, in which release, and at what cost (platform and account). Record every verdict in the ledger as you go:

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py record <project> <id> <outcome> --reason "<release | KP-nnn | plan section | why>"
   ```

   Outcomes: `fixed`, `pitfall`, `planned`, `declined`, `project-specific`. A declined entry carries its reason so it is not raised again; an entry that changes afterwards is evaluated once more, with the earlier decision beside it.

5. **Sign-off by scope.** The owner signs off what changes what they see, pay or decide, each as a question of its own in the app's question form; nothing of that kind changes before they do. Everything else the maintainer decides under the bridge's escalation rule and reports in the evaluation. An accepted fix goes into a release, an accepted pitfall into the Known Pitfalls, an accepted gap into the plan.

**The seed.** Before the first scheduled run, `python ~/.claude/cursor-bridge/evaluate-reports.py seed` enters the first evaluation's tables (`Reports/Evaluations/2026-10-04/*.md`) into the ledger with their classes, so that the first run raises nothing already handled.

**The schedule.** The desktop app's scheduled task runs this command every Sunday at 14:00 local time, in the bridge project, from a prompt that names the command and nothing else; the owner creates the task once after release A3 is installed (the setup guide's run sheet), and starts the first run by hand. A Sunday with nothing new ends in one line.
