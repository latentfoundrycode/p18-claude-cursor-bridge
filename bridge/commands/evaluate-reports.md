# /evaluate-reports — the report cycle (plan 12; release A3)

A maintainer command, run in the bridge project by the maintainer session (the Bridge's Administrator Agent), never by a project supervisor. It turns what the projects report about the bridge into decisions, on a schedule, with a ledger so that nothing is raised twice.

**What is read, in place** (never copied, never edited): each project's `<Name> Issues During Development and Their Solutions.md` and `<Name> Claude-Cursor Bridge Feedback.md` in its `Documents/` folder; the supervisor's private notes (`~/.claude/projects/<key>/memory/*.md`); and, since the last run, the owner's typed messages and question-form answers from the projects' session records, which a program extracts with stated filters (a session continued after a compaction is followed; subagents' records, app-inserted text and the maintainer session's own messages are left out; a key's value is withheld).

**Steps, in order.**

1. **Collect.** From the bridge's root (the folder holding `Workspace/` and `Reports/`):

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py collect
   ```

   It writes `Reports/Evaluations/<date>/unprocessed.md`: every entry absent from the ledger (`Reports/ledger.json`) or whose text changed since it was evaluated (shown with the earlier verdict). "Nothing new" leaves steps 2 and 3 only the entries the owner's messages raise (the extract below), and the evaluation file only those and its Pace and Dependency scan sections (the ledger keeps the run's date); the pace report below runs all the same. Before the extract, note the ledger's `_meta.last_extract`, the previous run's date, which the extract rewrites: it opens the window step 1b reads. Then:

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py extract
   ```

   Without `--since` it starts at the last extract's date in the ledger, and before any extract at the newest folder before today's that holds a run's files, or at the first evaluation's date, 2026-10-04, when none does; `--since <date>` overrides. It writes `Reports/Evaluations/<date>/owner-messages-<project>.md`. Read them for prods to a stalled loop, complaints, and incidents the documents do not mention; an incident found only there becomes an entry of the evaluation like any other. Then, on every run, a week with nothing new included:

   ```bash
   python ~/.claude/cursor-bridge/pace-report.py --tokens > Reports/Evaluations/<date>/pace.md
   ```

   It reads, read-only, every project's git history and its launcher's and review guard's records, and writes per project and per ISO week the increments started and merged, the rounds per increment (mean and maximum), the days from start to merge, the `docs/HARDENING.md` lines added and the tokens, with the increments over the code gate's three-round ceiling by ID and the lift each round above it used (a class line, the owner's line, `none`, or `unknown` where no launcher row or guard round records it, as for rounds run before release B's programs logged lifts). In a project that tracks any file under `handoff/`, an increment is an ID with a tracked brief, so one the supervisor built without a brief is not counted, and a project that tracks only builder reports there (`<ID>-report.md`, `<ID>-r<N>-report.md`, `<ID>-r<N><letter>-report.md`, which are no briefs) counts no increment at all (in a project that tracks nothing under `handoff/`, every ID a squash subject names is counted merged, and the started and rounds cells read `n/a`), and a stage review is listed only from the review guard's rounds files, which release B's guard writes from its install.

1b. **Read the weekly dependency scan and the Dependabot alerts**, for every project, a week with nothing new included (R-052; the three kinds below are the bridge design's, `docs/DESIGN.md`, "The weekly dependency scan"). `<owner>/<repo>` is the project's GitHub repository, read from its `origin` remote. First the workflow's state:

   ```bash
   gh workflow list --all --repo <owner>/<repo>
   ```

   Any disabled state of the workflow (`disabled_inactivity`, `disabled_manually`) is the third kind below whatever its runs show: GitHub disables a public repository's scheduled workflows after 60 days with no activity, and `gh run list` lists no run of a disabled workflow without `--all`. A list that holds no `dependency-scan` names a project that has not received the workflow yet (one not calibrated to release T): it is written `not configured`, its calibration's item, with `last run read: none`, and no run is read for it. Then the runs created since the date noted before the extract, each with its id, status and conclusion:

   ```bash
   gh run list --repo <owner>/<repo> --workflow dependency-scan.yml --created ">=<the ledger's _meta.last_extract>" --json databaseId,createdAt,status,conclusion
   ```

   The date is a day and the schedule runs on the morning of the evaluation's own Sunday, so that list also holds the runs the previous evaluation read. The window is the listed runs whose `createdAt` is later than the `last run read:` time the previous evaluation's Dependency scan section gives for the project, every listed run where that section reads `last run read: none`, and, where no previous section names the project, the listed runs whose `createdAt` falls on a later day than that date, so a run of that day cannot cover this Sunday; each evaluation's section gives, per project, `last run read: <createdAt>`, the creation time of the newest completed run of its window, or the previous section's value where the window completed none, `none` where there was no previous one, so a run still in progress at the reading is read the next Sunday (an older one beside a newer completed run goes unread, the newer run's time passing it), and a late or missing schedule leaves the window without a completed run. A run re-run from the Actions tab keeps its creation time and is not read again; the rerun this step names, `gh workflow run`, starts a new run. While a finding stands, the section also gives `finding standing: run <id>`, carried from each section to the next until a later run ends `success`, so the finding is reported every week it stands, beside whatever kind the week's own runs show. Then, for each run whose conclusion is `failure`, the step's exit line, `dependency-scan: OSV-Scanner exit <code>`:

   ```bash
   gh run view <run id> --repo <owner>/<repo> --log-failed
   ```

   Each project falls in one of three kinds, or is green:
   - **A finding**: a completed run of the window ended `failure` and its exit line reads `exit 1`, a flaw in a dependency, fixed by a `DEP-<nnn>` increment (the merge policy's procedure), never by an unreviewed change; it stands until a later run ends `success`, in this window or a later one.
   - **A scanner failure**: the window's last completed run proved nothing, a `failure` with another exit code or no exit line at all, or any conclusion other than `success` and `failure`; it is reported with the rerun's one command, `gh workflow run dependency-scan.yml --repo <owner>/<repo>`, and the rerun is read at the next evaluation, a finding that stands reported beside it, superseded by nothing but a `success`.
   - **No completed run since the previous evaluation**: the workflow disabled, no run of the window listed, a list the login cannot read, or only runs still queued or in progress, a finding of its own and never green (KP-005: silence is not green), reported with its remedy: where the workflow is disabled, a run sheet for the project's owner (`gh workflow enable dependency-scan.yml`, then `gh workflow run dependency-scan.yml`); where no run is listed, the rerun command; where a run is in progress, none, the next Sunday reading it.

   A window whose last completed run ended `success`, with no finding standing, is green. Then the Dependabot alerts, in two calls. The first,

   ```bash
   gh api repos/<owner>/<repo>/vulnerability-alerts
   ```

   answers 204 where the alerts are enabled and 404 where they are not, a 404 the finding "alerts off" and the second call not made; after a 204,

   ```bash
   gh api --paginate "repos/<owner>/<repo>/dependabot/alerts?state=open"
   ```

   lists the open alerts, every page of them, an empty list being alerts on with nothing open. A 403 on either call is the login's scope, named in a run sheet for the owner, never a token in text, the project's Security tab the fallback. Step 4's file gives each project's kind, its `last run read:` time and any `finding standing:` run, its alerts and the remedy in a **Dependency scan** section, written every week beside the Pace section; a finding of either is an entry of the evaluation like any other.

2. **Classify** each entry: a bridge defect; a gap in the bridge; a pitfall worth recording; already addressed (cite the release); already planned (cite the plan's section); or project-specific, needing nothing.

3. **Check** each verdict against the installed governance (`~/.claude`), the restructuring plan and its pinned list, so that nothing is proposed twice and nothing pinned is reopened unasked.

4. **Write** `Reports/Evaluations/<date>.md`: one table of entries and verdicts; then what the maintainer decided, with reasons; then the decisions for the owner, each with what would change, in which release, and at what cost (platform and account); then a **Pace** section that reads `pace.md`: per project the week's rows against the weeks before, a creeping slowdown named the week it starts; then the **Dependency scan** section step 1b gives. An increment over the ceiling whose round used no lift (`none`), or whose class line a reviewer denied (its Issues entry), is an entry of the evaluation like any other; an `unknown` lift is a round no record covers, an entry only when the round was run after release B installed. In a week with nothing new the file is written all the same, holding the Pace and Dependency scan sections and any entry the owner's messages raised. Record every verdict in the ledger as you go:

   ```bash
   python ~/.claude/cursor-bridge/evaluate-reports.py record <project> <id> <outcome> --reason "<release | KP-nnn | plan section | why>"
   ```

   Outcomes: `fixed`, `pitfall`, `planned`, `declined`, `project-specific`. A declined entry carries its reason so it is not raised again; an entry that changes afterwards is evaluated once more, with the earlier decision beside it.

5. **Sign-off by scope.** The owner signs off what changes what they see, pay or decide, each as a question of its own in the app's question form; nothing of that kind changes before they do. Everything else the maintainer decides under the bridge's escalation rule and reports in the evaluation. An accepted fix goes into a release, an accepted pitfall into the Known Pitfalls, an accepted gap into the plan.

**The seed.** Before the first scheduled run, `python ~/.claude/cursor-bridge/evaluate-reports.py seed` enters the first evaluation's tables (`Reports/Evaluations/2026-10-04/*.md`) into the ledger with their classes, so that the first run raises nothing already handled.

**The schedule.** The desktop app's scheduled task runs this command every Sunday at 14:00 local time, in the bridge project, from a prompt that names the command and nothing else; the owner creates the task once after release A3 is installed (the setup guide's run sheet), and starts the first run by hand. A Sunday with nothing new writes the Pace and Dependency scan sections and any entry the owner's messages raised.
