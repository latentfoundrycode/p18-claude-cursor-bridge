# /evaluate-reports — the report cycle (plan 12; release A3)

A maintainer command, run in the bridge project by the maintainer session (the Bridge's Administrator Agent), never by a project supervisor. It turns what the projects report about the bridge into decisions, on a schedule, with a ledger so that nothing is raised twice.

**What is read, in place** (never copied, never edited): each project's `<Name> Issues During Development and Their Solutions.md` and `<Name> Claude-Cursor Bridge Feedback.md` in its `Documents/` folder; the supervisor's private notes (`~/.claude/projects/<key>/memory/*.md`); and, since the last run, the owner's typed messages and question-form answers from the projects' session records, which a program extracts with stated filters (a session continued after a compaction is followed; subagents' records, app-inserted text and the maintainer session's own messages are left out; a key's value is withheld).

**Steps, in order.**

1. **Collect.** From the bridge's root (the folder holding `Workspace/` and `Reports/`):

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py collect
   ```

   It writes `Reports/Evaluations/<date>/unprocessed.md`: every entry absent from the ledger (`Reports/ledger.json`) or whose text changed since it was evaluated (shown with the earlier verdict). "Nothing new" leaves steps 2 and 3 only the entries the owner's messages raise (the extract below), and the evaluation file only those and its Pace and Dependency scan sections (the ledger keeps the run's date); the pace report below runs all the same. Before the extract, run step 1b. Then:

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py extract
   ```

   Without `--since` it starts at the last extract's date in the ledger, and before any extract at the newest folder before today's that holds a run's files, or at the first evaluation's date, 2026-10-04, when none does; `--since <date>` overrides. It writes `Reports/Evaluations/<date>/owner-messages-<project>.md`. Read them for prods to a stalled loop, complaints, and incidents the documents do not mention; an incident found only there becomes an entry of the evaluation like any other. Then, on every run, a week with nothing new included:

   ```bash
   python ~/.claude/cursor-bridge/pace-report.py --tokens > Reports/Evaluations/<date>/pace.md
   ```

   It reads, read-only, every project's git history and its launcher's and review guard's records, and writes per project and per ISO week the increments started and merged, the rounds per increment (mean and maximum), the days from start to merge, the `docs/HARDENING.md` lines added and the tokens, with the increments over the code gate's three-round ceiling by ID and the lift each round above it used (a class line, the owner's line, `none`, or `unknown` where no launcher row or guard round records it, as for rounds run before release B's programs logged lifts). In a project that tracks any file under `handoff/`, an increment is an ID with a tracked brief, so one the supervisor built without a brief is not counted, and a project that tracks only builder reports there (`<ID>-report.md`, `<ID>-r<N>-report.md`, `<ID>-r<N><letter>-report.md`, which are no briefs) counts no increment at all (in a project that tracks nothing under `handoff/`, every ID a squash subject names is counted merged, and the started and rounds cells read `n/a`), and a stage review is listed only from the review guard's rounds files, which release B's guard writes from its install.

1b. **The weekly dependency scan and the Dependabot alerts**, for every project, a week with nothing new included (R-052, R-097), run before the extract, which rewrites the ledger's `_meta.last_extract` that the window of a project with no earlier read falls back on:

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py security
   ```

   It reads, with GET requests only, each project's weekly workflow, its runs since the last read, each failed run's exit line and its open Dependabot alerts, and writes `Reports/Evaluations/<date>/security.md`: per project its kind (a finding, a scanner failure, no completed run since the previous evaluation, the three of the bridge design's "The weekly dependency scan"; or `not configured`, `no remote`, or green), its `last run read:` time, any `finding standing:` run, its alerts and the remedy; `alerts off` and each open alert are findings of their own, beside the kind, whatever the kind reads. For a project written `no remote` or `not configured`, read its inventory's Decisions row that begins `Weekly scan:`: the reason it records (no GitHub remote, or a newer floor pin waiting for the bridge release that carries it) takes the place of the finding or the calibration's item, and a project that records none keeps them. A finding is fixed by a `DEP-<nnn>` increment (the merge policy's procedure), never by an unreviewed change; a 403 is the login's scope, named in a run sheet for the owner, never a token in text; exit 2 names a bad date, a missing or malformed projects file or an unreadable seed. Step 4's **Dependency scan** section is that file's, written every week beside the Pace section; a finding is an entry of the evaluation like any other.

2. **Classify** each entry: a bridge defect; a gap in the bridge; a pitfall worth recording; already addressed (cite the release); already planned (cite the plan's section); or project-specific, needing nothing.

3. **Check** each verdict against the installed governance (`~/.claude`), the restructuring plan and its pinned list, so that nothing is proposed twice and nothing pinned is reopened unasked.

4. **Write** `Reports/Evaluations/<date>.md`: one table of entries and verdicts; then what the maintainer decided, with reasons; then the decisions for the owner, each with what would change, in which release, and at what cost (platform and account); then a **Pace** section that reads `pace.md`: per project the week's rows against the weeks before, a creeping slowdown named the week it starts; then the **Dependency scan** section step 1b gives. An increment over the ceiling whose round used no lift (`none`), or whose class line a reviewer denied (its Issues entry), is an entry of the evaluation like any other; an `unknown` lift is a round no record covers, an entry only when the round was run after release B installed. In a week with nothing new the file is written all the same, holding the Pace and Dependency scan sections and any entry the owner's messages raised. Record every verdict in the ledger as you go:

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py record <project> <id> <outcome> --reason "<release | KP-nnn | plan section | why>"
   ```

   Outcomes: `fixed`, `pitfall`, `planned`, `declined`, `project-specific`. A declined entry carries its reason so it is not raised again; an entry that changes afterwards is evaluated once more, with the earlier decision beside it.

5. **Sign-off by scope.** The owner signs off what changes what they see, pay or decide, each as a question of its own in the app's question form; nothing of that kind changes before they do. Everything else the maintainer decides under the bridge's escalation rule and reports in the evaluation. An accepted fix goes into a release, an accepted pitfall into the Known Pitfalls, an accepted gap into the plan. A run nobody attends (the scheduled Sunday run) reaches the owner and the projects itself (the owner's decision of 2026-11-08): a push notification names the count of decisions; the first is asked in the question form at the end of the turn, the others named in it; a request to a project goes to its live session directly, as mechanics (rule 57), and is left as a paste-ready block only for a session that is offline. The answers are read from the maintainer session's record at the next run.

**The seed.** Before the first scheduled run, `python ~/.claude/cursor-bridge/evaluate-reports.py seed` enters the first evaluation's tables (`Reports/Evaluations/2026-10-04/*.md`) into the ledger with their classes, so that the first run raises nothing already handled.

**The schedule.** The desktop app's scheduled task runs this command every Sunday at 14:00 local time, in the bridge project, from a prompt that names the command and nothing else; the owner creates the task once after release A3 is installed (the setup guide's run sheet), and starts the first run by hand. A Sunday with nothing new writes the Pace and Dependency scan sections and any entry the owner's messages raised.
