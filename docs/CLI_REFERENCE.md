# Bridge command reference

## bench-check.py

Path: `bridge/cursor-bridge/bench-check.py`

```
bench-check: compare benchmark results against budgets and a committed baseline.

  python bench-check.py bench/budgets.json bench/baseline.json bench/results/latest.json [--update-baseline]

Per budget (Performance-Conventions.md section 3):
  OVER BUDGET   value exceeds max (or falls below min)                -> FAIL
  REGRESSION    worse than baseline by more than tolerance_pct        -> FAIL
  NOT MEASURED  the budget's benchmark/metric is absent from results  -> FAIL
  IMPROVED      better than baseline by more than tolerance_pct       -> note (move the baseline in an optimization commit)
  OK            within budget and within the band
Metrics present in the baseline but without a budget are regression-checked with a
default 10% band. Results with neither budget nor baseline are listed as NEW.
--update-baseline writes the results into the baseline file (optimization commits only).
Exit 0 = no FAIL, 1 = at least one FAIL, 2 = cannot read an input.
ASCII-only on purpose (cp1252 consoles).
```

## boundary-check.py

Path: `bridge/cursor-bridge/boundary-check.py`

```
Workspace-boundary detector for the Cursor afterFileEdit hook (advisory).

Reads the hook's JSON from stdin, takes the edited file's path and the workspace
root(s), and records any edit that landed OUTSIDE the workspace to
<workspace>/docs/BOUNDARY_VIOLATIONS.md. The supervisor reads that file at
step 4 (Inspect) of the delegation loop and treats an entry like SCOPE DRIFT.

This hook runs AFTER the edit, so it cannot prevent it - it detects. Always
exits 0 (advisory; never fail-closed). ASCII-only on purpose (cp1252 consoles).
```

## bridge-check.py

Path: `bridge/cursor-bridge/bridge-check.py`

```
bridge-check: verify that the installed bridge tree matches its manifest.

The maintainer ships MANIFEST.json (file -> sha256, plus the version) with every
bridge release. This script hashes the live tree it is installed in and reports,
per file: OK, STALE (content differs), MISSING (not installed), and any EXTRA
governance files not in the manifest (informational). Line endings are normalized
before hashing, so a CRLF copy of an LF file is still OK.

Two files are not fingerprinted but compared by content (KP-030, KP-032):
- settings.json is shared with Claude Code and the owner, so only the bridge-owned entries
  (cursor-bridge/settings.bridge.json: allow and deny rules, hooks) must be present;
  everything else in it is the owner's and is ignored, except a hook that runs a
  cursor-bridge program which is not installed: that is reported, because it blocks;
- the cursor-agent shim at %LOCALAPPDATA%/cursor-agent/cursor-agent must equal
  cursor-bridge/cursor-agent.shim (Windows only);
- the agent's home folder %USERPROFILE%/.cursor-bridge/agent-home must hold its .cursor
  link (KP-038; Windows only).

Usage:  python ~/.claude/cursor-bridge/bridge-check.py [--root <path-to-.claude>] [--quiet]
        python bridge/cursor-bridge/bridge-check.py --root bridge --sources [--quiet]

--sources checks a source tree (the `bridge/` folder of the bridge's repository) against its
own manifest and nothing more: a source tree has no settings.json, since the owner's file is
not part of it, and the shim is a matter of the machine a release is installed on. In a
source tree a file the manifest does not list (EXTRA) fails the check as well.
Exit:   0 = every manifest file OK; 1 = at least one STALE or MISSING;
        2 = manifest unreadable.  ASCII-only on purpose (cp1252 consoles).
```

## bridge-install.py

Path: `bridge/cursor-bridge/bridge-install.py`

```
bridge-install: install or update the bridge into ~/.claude from a release folder, and
take a release back.

  python <release>/cursor-bridge/bridge-install.py [--target <path-to-.claude>] [--dry-run] [--anyway]
  python <release>/cursor-bridge/bridge-install.py --rollback [--target <path-to-.claude>] [--dry-run]

The release folder is the one this file lives in (its parent is the release tree: commands/,
agents/, skills/, cursor-bridge/; in the bridge's repository that tree is `bridge/`). Both
commands are run from a release folder, never from the installed copy: the installed copy
is replaced during a rollback, and a rollback that was interrupted could not be finished
with it when the release it restores has an installer that does not know the command.

Installing:

  0. REFUSES A FOLDER THAT IS NOT A RELEASE: every file must equal the fingerprint in the
     folder's own manifest and no file may be unlisted; and when the folder is a checkout of
     the bridge's repository it must be `main` as merged (on main, equal to origin/main,
     nothing uncommitted), because the install check cannot tell a merged release from a
     stamped branch. --anyway installs a checkout's state as it is (the maintainer's
     rehearsals, with --target);
  1. KEEPS THE PREVIOUS RELEASE: when the target holds a bridge of another version, the
     files its manifest lists are saved to <target>/cursor-bridge-previous/<that version>/
     first (one previous release is kept; an older saved one is removed; a kept copy of
     the same version is never written twice, see save_previous), and the kept copy is
     compared with that release's fingerprints: a file that was changed on this computer
     is named, because the way back refuses a copy that is not the release as shipped;
  2. REPLACES the installed release by this one (replace_release): the allow and deny
     rules and the hooks only the replaced release owned leave the target's settings.json,
     the files its manifest listed that this release no longer ships are removed,
     commands/, agents/, skills/ and cursor-bridge/ are copied file by file (every other
     file is left alone), and the bridge-owned settings (cursor-bridge/settings.bridge.json)
     are MERGED into settings.json: every allow and deny entry and every hook the bridge
     needs is added if missing, entries the bridge has RETIRED (its "retired" list) are
     removed, and every key the owner or Claude Code wrote there is kept untouched
     (KP-030). The previous settings.json is saved beside it as
     settings.json.bak-<date>-<time> before its first change;
  3. installs the cursor-agent shim (cursor-bridge/cursor-agent.shim) at
     %LOCALAPPDATA%/cursor-agent/cursor-agent, the file Claude Code's Bash tool runs for
     `cursor-agent` on Windows (KP-032), when that folder exists, keeping a different
     previous file as cursor-agent.bak-<date>-<time>, and prepares the home folder builder
     and reviewer runs get, %USERPROFILE%/.cursor-bridge/agent-home (KP-038);
  4. runs bridge-check.py on the result and prints its verdict.

Taking a release back (--rollback) is the same replacement with the kept release as its
source, so every install exercises the way back: the files, the allow and deny entries and
the hooks only the newer release added go, the owner's keys stay, the kept release's shim
is installed. The "If rolled back" items of the release taken back are written to
cursor-bridge/ROLLED-BACK.md for /calibrate-bridge (the restored changelog no longer holds
them; the next install removes the note), bridge-check.py runs on the result, and the kept
copy is removed only when that check passes. A kept copy that is not complete, or not the
release as shipped, is refused before anything changes.

The bridge is installed once per computer, so an install and a rollback reach every project:
the release's changelog entry says what a project that had calibrated forward must restore
("If rolled back"), and /calibrate-bridge applies it.

Exit 0 = installed (or rolled back) and verified; 1 = verification failed; 2 = refused,
stopped by a file that could not be read or written (the same command can be run again),
or nothing to roll back to. ASCII-only on purpose (cp1252 consoles).
```

## bridge-run.py

Path: `bridge/cursor-bridge/bridge-run.py`

```
bridge-run: run one of the loop's commands under a hard time limit that kills its whole
process tree.

  python ~/.claude/cursor-bridge/bridge-run.py --limit <seconds|auto> [--kind <kind>] [--key-file <path>] -- <command> [args...]
  python ~/.claude/cursor-bridge/bridge-run.py --healthy <run id> [--kind <kind>]

Why it exists (KP-033): a background builder, reviewer or watch that hangs holds the loop
until the owner notices, and on Windows a plain timeout kills only the first process while
its children (node under cmd.exe, a dev server under npx) live on and keep the output pipe
open, so the supervisor is never woken. This program puts ITSELF into a Windows Job Object
with "kill on close" before it starts the command, so every process the command creates is
born inside the job: at the limit the job is terminated and every member dies with it, the
pipe closes, and the supervisor wakes with exit code 124; at a normal end, closing the job
kills any orphan the command left behind. On other platforms the command runs in its own
process group, killed as a whole.

What it accepts (release 0a review, F6; release A2): only the commands the loop runs through
it, each by name: `cursor-agent …` (a builder, or Review B with `--kind review`), `gh pr
checks …` (the CI watch) and the test suites the supervisor awaits (`pytest`, `python -m
pytest`, `python -m unittest`, `uv run pytest`, `npm test`, `npm run test*`, `pnpm test`,
`yarn test`, `npx vitest`, `npx jest`, `npx playwright test`, `node --test`, `go test`,
`cargo test`, `dotnet test`); an option that would run another program or delete a folder
(`-exec`, `-p`, `-c`, `--config`, `--basetemp`) is refused, an `npx` tool is accepted only
when it is installed in the project (`node_modules/.bin/`), and `--key-file` is refused with
`cursor-agent` (a key must never reach the builder); anything else is refused with exit 125,
so the launcher's allow rule cannot become a way to run arbitrary commands unseen. A
benchmark or a runner the launcher does not know runs directly in the background, marked
`# wake`. The tests set BRIDGE_RUN_ALLOW_ANY=1 to run their own helpers through it.

Ceilings (release A2, plan 10.3): every run is logged to `run/launcher/runs.jsonl` under the
folder the launcher is started in (kind, limit, seconds, exit; never the prompt). `--limit
auto` takes the kind's default (builder 7200, review 3600, watch 3600, test 1800) or, once a
HEALTHY run of that kind is on record, one and a half times the longest healthy run, never
below the default and never above twice it unless `docs/RUN_PARAMETERS.md` carries the
owner's words on a line `Ceiling above twice: <kind> <seconds> (<their words>, <date>)`. The
supervisor marks a run healthy with `--healthy <run id>` once its work passed the gate (the
id is the launch time on the first stderr line, given whole or as a prefix that fits exactly
one run; a run ended at its limit whose kept work merged counts too, so the ceiling can grow);
a test run that exits 0 is marked by the launcher itself. The run that raised a ceiling is
named when the ceiling is chosen. A slow but healthy task is never ended before its ceiling.
An owner's cap below twice the default is ignored with a note: the line says "above twice".
Refuses a design critique round above the ceiling (exit 125, `design ceiling:`).

`--key-file <path>` (release A2): a file of `NAME=value` lines, outside the Workspace, whose
values reach the child's environment only; names are printed, values never (the owner's
rule of 2026-10-05: no secret through the environment the owner sets).

- stdout and stderr are inherited, so `2> run/agent/TASK-nnn.err` works unchanged.
- The first line on stderr is `bridge-run: started <UTC time>Z`, which is what
  pr-activity-check.py's --since needs; the last is `bridge-run: exit <code>`, which
  review-guard.py reads to tell a review that reached a verdict from one that failed.
- The exit code is the command's own; 124 = the limit was hit; 125 = refused or could not
  start.
- `cursor-agent` is started the way Windows needs it (the .cmd launcher) and with the
  owner's identity withheld, the same recipe as cursor-agent.shim (KP-032). `--strip`
  withholds it for any other accepted command too.

ASCII-only on purpose (cp1252 consoles).
```

## bridge-stop.py

Path: `bridge/cursor-bridge/bridge-stop.py`

```
bridge-stop: end a background task's whole process tree (release A4 follow-up, 2026.10.11c).

  python bridge-stop.py <run id>          a run of the launcher: its child's tree, then the launcher
  python bridge-stop.py --pid <pid>       any process and everything under it

Run from the Workspace root. The launcher's run log (`run/launcher/runs.jsonl`) carries each
run's `pid` (the launcher) and `child_pid` (the command it started) since 2026.10.11c; a run
id is exact or a unique prefix. On Windows the tree is ended with `taskkill /T /F`; elsewhere
the process group is signalled with SIGKILL, then the process itself. Stopping a verification
loop this way never advances it into its next driver, since the loop and its children end
together (KP-056); the app's own TaskStop ends the loop only. Prints what it ended and whether
anything of the tree survived. Exit 0 = ended or already gone, 1 = something survived,
2 = no such run or bad arguments. Windowless. Never writes the run log.
```

## completion-check.py

Path: `bridge/cursor-bridge/completion-check.py`

Check requirements coverage and shipped stand-ins.

### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--mode`; default: `"done"`; required: false; choices: ["plan", "done"]
  - - `--requirements`; default: `"docs/REQUIREMENTS.md"`; required: false
  - - `--only`; default: `""`; required: false; comma-separated requirement IDs; the run is limited to them

## conformance-check.py

Path: `bridge/cursor-bridge/conformance-check.py`

```
conformance-check: does this project's configuration carry the floors the bridge requires?

  python ~/.claude/cursor-bridge/conformance-check.py [<project root or Workspace>] [--screens] [--installable] [--offline] [--quiet]

Why (plan review R4): the bridge added floors over time (the security scanners in the gate,
SHA-pinned actions, the workspace boundary, the records), and nothing compared a project
configured before a floor existed with what the bridge now requires; the video factory ran
its gate with no scanner and actions pinned by tag while the Project Summary said the floor
applied everywhere. This check reads the project's files and reports, per floor, OK, MISSING
or NOTE. It runs at every calibration and every reflection point; each MISSING is a
calibration item, applied as configuration work in the next stage. It never changes anything.

What it checks, with the file it reads (the 0b review corrected several of these):
  - the gate workflows (.github/workflows/*.yml), step by step: a step runs Semgrep,
    OSV-Scanner and Socket; a scanner step guarded by `if:` is MISSING (it is skipped
    silently when its condition is false); Semgrep runs the bridge rules or the Pro engine
    (`semgrep ci`), not public rulesets alone (Cursor-Project-Configuration.md 5c); a scanner
    without a pinned version is a NOTE (rule 14); every `uses:` is pinned by a 40-character
    commit; the runner is Linux (a note otherwise);
  - on GitHub, read-only through `gh` unless --offline: the default branch has a required
    status check (N6), and the repository's visibility (a public repository is a NOTE);
  - the workspace boundary (.cursor/rules/workspace-boundary.mdc, the boundary-check hook in
    .cursor/hooks.json), the windowless check in the hooks (rule 24), and the frozen
    secure-coding rule (.cursor/rules/secure-coding.mdc);
  - a lockfile beside each manifest (package.json, pyproject.toml), and a transitive lock for
    a root requirements.txt (direct pins alone are not a lock; KP-018);
  - the records: docs/PROJECT_STATUS.md, INVENTORY.md, REQUIREMENTS.md, RUN_PARAMETERS.md,
    ROSTER.json, DESIGN.md (a design under other names is a NOTE naming them), and
    docs/diagrams/INDEX.md (missing = a diagram retrofit item);
  - the Workflows: line in docs/PROJECT_STATUS.md: missing, malformed, or not right after
    Phase: is MISSING (R-015);
  - with --screens (or a docs/mockups folder): the design detector in the gate;
  - release A1b: a spending limit recorded for every key, account or provider that can charge
    (the inventory's Resources rows); the inventory's `Development data:` decision; every
    adapter of a listed provider tested against recorded replies (the providers from the
    inventory's chargeable rows, one word each; the adapters among the project's own tracked
    files, naming the provider in a string of code, not a comment; the evidence a cassette or
    fixture file the adapter's test loads, a recording library, or a test that names cassettes
    in a repository that tracks a cassettes folder); `run/` ignored (a NOTE);
  - release A2: project.json at the Workspace root (name, purpose, kind, version, state), its
    keys and its phase against the status file;
  - with --installable (or docs/cli-reference.json present): the CLI reference and a check
    of it, in CI or in the test suite;
  - secrets within the builder's reach: variable NAMES in Workspace/.env, .env.* (not the
    examples) and <folder>/.env that look like account keys or tokens are MISSING; local
    service passwords the tests need (POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD, ...) are a
    NOTE; values are never read or printed (KP-032); the advice is a key file outside the
    Workspace, never the Windows user environment; key-like variable NAMES in the session's
    own environment are a NOTE (the launcher withholds them from builder and reviewer runs);
  - the private memory notes Claude Code keeps for this project (names only; calibration
    step 2b reviews them, rule 41);
  - the recorded bridge version against the installed one (calibration due).
Exit 0 = every floor present; 1 = at least one MISSING; 2 = not a workspace.
ASCII-only on purpose (cp1252 consoles). Never writes.
```

## diagram-check.py

Path: `bridge/cursor-bridge/diagram-check.py`

Check the normative design diagrams.

### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--mode`; default: `"design"`; required: false; choices: ["design", "code", "done"]
  - - `--index`; default: `"docs/diagrams/INDEX.md"`; required: false
  - - `--requirements`; default: `"docs/REQUIREMENTS.md"`; required: false

## evaluate-reports.py

Path: `bridge/cursor-bridge/evaluate-reports.py`

evaluate-reports: the report cycle's program (restructuring plan, section 12; release A3).

### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit

### Subcommand `collect`

#### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--ledger`; required: false
  - - `--project-root`; required: false; one project root instead of the three (tests)
  - - `--project-name`; required: false
  - - `--home`; required: false; the folder holding .claude/projects (tests)
  - - `--out`; required: false

### Subcommand `record`

#### Positionals

  - - `project`; required: true
  - - `id`; required: true
  - - `outcome`; required: true

#### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--ledger`; required: false
  - - `--project-root`; required: false; one project root instead of the three (tests)
  - - `--project-name`; required: false
  - - `--home`; required: false; the folder holding .claude/projects (tests)
  - - `--reason`; required: false
  - - `--force`; default: `false`; required: false

### Subcommand `seed`

#### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--ledger`; required: false
  - - `--project-root`; required: false; one project root instead of the three (tests)
  - - `--project-name`; required: false
  - - `--home`; required: false; the folder holding .claude/projects (tests)
  - - `--date`; required: false
  - - `--evaluations`; required: false; the folder of the first evaluation's tables (default Reports/Evaluations/2026-10-04)

### Subcommand `extract`

#### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--ledger`; required: false
  - - `--project-root`; required: false; one project root instead of the three (tests)
  - - `--project-name`; required: false
  - - `--home`; required: false; the folder holding .claude/projects (tests)
  - - `--out`; required: false
  - - `--since`; required: false; a date; default the ledger's last extract, else the newest evaluation folder

## inventory-check.py

Path: `bridge/cursor-bridge/inventory-check.py`

Check the project's current-state record.

### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--inventory`; default: `"docs/INVENTORY.md"`; required: false
  - - `--status`; default: `"docs/PROJECT_STATUS.md"`; required: false
  - - `--changes`; default: `"docs/CHANGES.md"`; required: false
  - - `--max-lines`; default: `120`; required: false
  - - `--max-chars`; default: `12000`; required: false

## invisible-check.py

Path: `bridge/cursor-bridge/invisible-check.py`

```
invisible-check: characters a reader cannot see in the files a diff changed (release A4, 13.1).

  python invisible-check.py [<base-ref>] [--all]

Run from the Workspace root. Reads the text files changed against <base-ref> (default HEAD:
the checkpoint) plus the untracked ones, or every tracked text file with --all, and lists
each line holding a zero-width character (U+200B..U+200D, U+2060, U+FEFF after the first
character), a bidirectional control (U+202A..U+202E, U+2066..U+2069: the "Trojan Source"
reordering), a soft hyphen (U+00AD) or a word joiner. Such a character hides a token from a
reviewer's eye and from a grep, and reorders what a reviewer reads. Exit 0 = none, 1 = at
least one, 2 = cannot verify. ASCII output; the character is named by its code point.
```

## lock-check.py

Path: `bridge/cursor-bridge/lock-check.py`

```
lock-check: a dependency manifest changed, so the lockfile CI installs from must have too.

Reviewers read what IS in a diff; this checks for what is MISSING from it. If a
dependency manifest changed against <base> and its lockfile did not, the resolved
closure CI installs is stale and the build will fail at import/collection time
(ISS-004, Known-Pitfalls KP-017).

  python lock-check.py <base-ref> [--lock <path>]...

Known pairs (manifest -> any of these lockfiles):
  pyproject.toml / requirements.in / setup.cfg -> requirements.lock, requirements.txt,
        uv.lock, poetry.lock, Pipfile.lock, pdm.lock
  package.json -> package-lock.json, pnpm-lock.yaml, yarn.lock, bun.lockb
  Cargo.toml -> Cargo.lock;  go.mod -> go.sum;  Gemfile -> Gemfile.lock
  composer.json -> composer.lock;  pubspec.yaml -> pubspec.lock;  *.csproj -> packages.lock.json
--lock adds a project-specific lockfile path to the candidate list.
A manifest changed outside its dependencies (a version bump, a tool setting) needs no lockfile
change; a folder with no lockfile in use beside the manifest has nothing to go stale (release
A4, 13.1: the false alarms). Exit 0 = consistent (or no manifest changed), 1 = manifest changed
without its lockfile, 2 = cannot verify. Untracked lockfiles count as changed. ASCII-only.
```

## loop-guard.py

Path: `bridge/cursor-bridge/loop-guard.py`

```
loop-guard: a Claude Code Stop hook that keeps a bridge supervisor from ending its turn
while the build loop has work and nothing is going to wake it.

Registered in the bridge's settings.json (hooks -> Stop). Reads the hook's JSON on stdin.
It BLOCKS the stop - exit code 2 with the reason on stderr, which Claude Code feeds back to
the model (documented; code.claude.com hooks reference) - only when ALL hold:

  1. the session runs in a bridge Workspace: <cwd>/docs/PROJECT_STATUS.md exists;
  2. its `Phase:` is building or changing;
  3. its `Awaiting user on:` is `nothing` (the supervisor is not waiting for the owner);
  (and, in every phase: a turn whose last message holds a shell block and names no terminal
  is sent back once, because a run sheet without its terminal cannot be followed, rule 27);
  4. nothing is pending that will wake the session. Since release A2 the hook's own lists
     decide: a background command *of a kind that finishes* (a builder run, a CI watch, a
     command run through bridge-run.py, or one marked `# wake`) counts until its limit plus a
     grace; a background agent counts only under its ceiling (an hour, or `Agent ceiling:` in
     the run parameters) AND only while a wake-timer command that ends no later than that
     ceiling is running, because a hung agent never completes and nothing else would wake the session
     (plan 10.1, case 5); a scheduled wake-up counts (one past due fires as soon as the
     session is idle). A background command of any other kind (a dev server, a worker, a
     probe) is NOT a wake source: a server never finishes (KP-031). When the hook hands no
     lists, the transcript is read as before, within GRACE_HOURS;
  5. this is not already a continuation forced by this hook (`stop_hook_active`), so it
     nudges at most once per stop sequence and can never trap the session.

Everything else - any other folder, any other phase, an owner question outstanding, a
background task pending, a missing or unreadable file - ALLOWS the stop. The guard fails
open: a parse problem never blocks. ASCII output only. Never writes anything.
```

## permission-guard.py

Path: `bridge/cursor-bridge/permission-guard.py`

```
permission-guard: a Claude Code PreToolUse hook for the Bash and PowerShell tools that
refuses the two actions the loop must never take, in every permission mode (KP-032):

  - merging a pull request past the repository's rules: `gh pr merge … --admin`, and the
    REST route `gh api … /pulls/<n>/merge` with a method that writes;
  - a force-push in any form: `--force`, `--force-with-lease`, `--force-if-includes`,
    `-f`, a combined short flag such as `-fu`, `--mirror`, a `+` refspec;
  - any `git worktree remove` (rule 19, release A1b): Git for Windows follows a gitignored
    junction or symbolic link inside the worktree into its target in an ordinary removal
    as in a forced one; `worktree-teardown.py` removes a worktree and refuses while a link
    is inside (it runs git as its own child, which this hook never sees);
  - a merge without the pre-merge check's record (release A1b): `gh pr merge` must carry
    `--match-head-commit <sha>`, and `review-guard.py premerge` must have written the record
    `<git common dir>/bridge/premerge/<sha>` for that sha when it printed OK; `--disable-auto`
    and `--help` pass; a `gh api graphql` call carrying a merge mutation is refused.

A command behind a wrapper shell (`bash -c`, `bash -lc`, `sh -c`, `cmd /c`, `cmd /k`,
`powershell -Command`), quoted or not, is checked as the command it is; a single `&` and the
PowerShell call operator `&`, joined or not, separate commands; `{`, `if`, `then`, `xargs` and
its options are dropped like `env` and `timeout`; a here-document's body is data (a commit
message that quotes a forbidden command is not a command); a `git -c alias.<x>=...` whose
value starts with `worktree`, `pr`, `push`, `api` or `!` is refused, and so is a `gh alias set`
for a merge; an abbreviated `--forc` counts as `--force`, as it does for git; `--help` exempts a
`gh pr merge` only when it is not the value of a flag such as `--subject`. A here-document
read by a shell (`bash <<EOF`) is that shell's script and is checked; one read by any other
program (a commit message) is data. `powershell` without `-Command` runs the rest of its line,
`-com` abbreviates `-Command`, `.` runs a program as `&` does, `find -exec` runs its command,
and `-XPUT` is a method: all read as what they run. An encoded PowerShell command and a
GraphQL query built by a command substitution are refused unread.
  - inside a bridge Workspace (one holding docs/PROJECT_STATUS.md), a chain of commands
    (`&&`, `;`, `||`, a new line) carrying a state-changing git or gh command, or a command
    wrapped in `cd …` (rule 8: one command per call; a chain once built an increment on a
    merged branch; release A4). A pipe into a reader and a chain of reads pass.
  - a commit or push that skips its checks: `--no-verify`, commit's `-n`, or a
    `-c core.hooksPath=…` override (rule 4; release A4), except the two snapshots the merge
    policy allows: the pre-delegation checkpoint, whose subject starts with "checkpoint" and
    names the increment (`checkpoint before TASK-nnn`, with a round or a note after it,
    `checkpoint: … before TASK-nnn …`) and carries no accept, merge or release word; and a
    builder's hand-off ("… hand-off") made inside a worktree (`-C …/Worktrees/…`).
  - the Cursor agent started around the bridge's shim (`agent`, `agent.cmd`, `agent.ps1`,
    `cursor-agent.cmd`, `cursor-agent.ps1`, `cursor-agent.exe`, also behind `cmd /c` or
    `powershell`), which would run it with the owner's real home and identity (KP-038): the
    agent is started as `cursor-agent`, or through bridge-run.py.

It parses the command rather than matching a pattern, so chains, wrappers and quoting do
not hide the action, and `git commit -m "never use --force"` is not refused. Deny rules in
settings.bridge.json cover the common spellings as a second layer; this hook is the one
that reads the whole command.

Registered by bridge-install.py from settings.bridge.json (hooks.PreToolUse, matcher
"Bash|PowerShell"). Reads the hook's JSON on stdin; exit 2 with the reason on stderr blocks
the call (documented), exit 0 lets it through. Fails open on anything unexpected: a guard
that cannot read its input never blocks the loop. ASCII-only on purpose. Never writes.
```

## plan-check.py

Path: `bridge/cursor-bridge/plan-check.py`

Validate the build plan and list ready increments.

### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--plan`; default: `"docs/BUILD_PLAN*.md"`; required: false
  - - `--base`; default: `"origin/main"`; required: false
  - - `--no-git`; default: `false`; required: false; skip deriving merged increments from git
  - - `--briefs`; default: `"handoff"`; required: false; folder of the briefs compared with their increments

## pr-activity-check.py

Path: `bridge/cursor-bridge/pr-activity-check.py`

```
pr-activity-check: prove that nobody wrote to a pull request as the owner during a run.

  python ~/.claude/cursor-bridge/pr-activity-check.py <pr-number> --since <ISO-8601 UTC> [--repo owner/name]

Why (KP-032): the cross-family reviewer and the builder run as `cursor-agent` processes on
the owner's machine. Before release 2026.10.04a they inherited the owner's GitHub login, and
a reviewer twice posted its verdict on a pull request under the owner's name. The shim and
bridge-run.py now withhold that login; this check is the proof, run after every Review B
and before every merge: it lists every comment, review and review comment on the pull
request created at or after --since and flags any written by the account `gh` is logged
in as (the owner); it then reads the owner's own GitHub events since --since and flags, in
the same repository, what an agent would do and a supervisor would not during a review: a
comment or review on any other pull request or issue, a merge, a push straight to main.
The supervisor's own pushes to task branches and its opening of pull requests, which go on
while a review runs, are not flagged. A read-only check: `gh api` GET calls only.

--since must carry a time zone (`2026-10-04T13:14:33Z`): the launcher prints exactly that
as its first stderr line, `bridge-run: started <time>Z`. A timestamp without a zone is
refused, because a local time read as UTC would open the window hours late (fail open).

Exit 0 = nothing written as the owner since --since; 1 = GATE-INTEGRITY, something was;
2 = cannot verify (gh not logged in, API error, bad timestamp) - never treat as clean.
What it cannot see: edits to an older comment, a change of title or body, a label; the
identity withheld from the agents (KP-032) is what stops those, this check is the proof
for the likely cases, not a boundary.
ASCII-only on purpose (cp1252 consoles).
```

## refactor-check.py

Path: `bridge/cursor-bridge/refactor-check.py`

```
refactor-check: deterministic purity check for a REFACTORING diff.

A refactoring increment must keep the same functionality. Three things are
checkable without judgement, and this script checks them against a base ref:

  1. No test file changed.  Tests pin behaviour; a refactoring diff that edits
     one may be changing what "correct" means. (Characterization tests the
     supervisor writes are committed BEFORE the base ref, so they are not in
     the diff.)
  2. docs/CHANGES.md did not change.  That log records behaviour changes; a
     refactoring diff has none to record.
  3. The diff is within the size budget one reviewer can hold well
     (default 400 changed lines = insertions + deletions).

Usage:  python refactor-check.py <base-ref> [--max-lines N] [--allow-test <path> ...] [--lane tests]
        --allow-test lists test files the brief explicitly allowed (a mechanical
        rename or an import path), each of which the reviewer must then read.
        --lane tests   the TEST-INFRASTRUCTURE lane: the supervisor consolidating its own
        test helpers. Inverts the rule - no production file may change, test files may;
        the supervisor separately proves the collected test set is identical before and
        after (e.g. `pytest --collect-only -q`). Still no docs/CHANGES.md change.

Prints PURE or IMPURE with the reasons. Exit 0 = pure, 1 = impure, 2 = cannot
verify (not a git repo, bad ref). ASCII-only on purpose (cp1252 consoles).
```

## review-guard.py

Path: `bridge/cursor-bridge/review-guard.py`

```
review-guard: the committed checkpoint a reviewer with execution runs on, snapshotted
before the launch, verified and restored after it, and checked once more before the merge.

  python ~/.claude/cursor-bridge/review-guard.py snapshot <nnn>          before launching Review B
  python ~/.claude/cursor-bridge/review-guard.py verify   <nnn>          after it returns
  python ~/.claude/cursor-bridge/review-guard.py premerge <nnn> [<pr>]   after the review files are removed, committed and pushed

Why (release 0b review, finding 2 and its second pass): Review B keeps `--force` so it can
run the tests and build reproductions (the owner's decision), and it acts after Review A and
right before the merge, so what it leaves behind has no gate after it. `git status` followed
by `git checkout -- .` and `git clean -fd` restores tracked and untracked files only: it does
not see a moved HEAD, a commit, a new ref or stash, a changed `.git/config` or hook (which
would make the supervisor's next git command run the reviewer's program with the owner's
identity), or a changed ignored file (`.env`, a record a project keeps gitignored, a brief).

What each step does:
  snapshot  refuses a dirty tree (commit first); records HEAD, the branch, every ref, the
            stash list, a hash of `.git/config`, of every file in the ACTIVE hooks folder
            (`core.hooksPath`, read from the config file, or `.git/hooks`) and in
            `.git/hooks`, and every ignored file with its size and mtime (cache folders
            such as `.venv`, `node_modules` and `__pycache__` are skipped); writes
            <git common dir>/bridge/review-<nnn>.json and prints that file's hash.
  verify    reads the configuration and the hooks folders FIRST, as files, without running
            git: a change is GATE-INTEGRITY and nothing else runs. Every git command the
            guard runs is given `-c core.hooksPath=<an empty folder> -c core.fsmonitor=false`,
            so no hook of the repository runs inside the guard. It then compares HEAD, the
            branch, the local refs (heads, tags, stash) and the stashes - a difference is
            GATE-INTEGRITY, and each ref is put back - restores the tree (`git reset --hard
            <sha>`, `git clean -fd`, keeping the launcher's own `run/review/REVIEW-<nnn>.err`,
            whose first line it prints), lists what it removed, and compares the ignored
            files: a change under docs/, handoff/, run/review/ or to `.env*` is
            GATE-INTEGRITY, any other is LEFT BEHIND. A moved remote-tracking ref (a fetch)
            is a note. It prints the snapshot file's hash again: compare it with the one
            `snapshot` printed, since the reviewer could rewrite the snapshot.
  premerge  needs the verified mark `verify` wrote for this snapshot (release A1b, second and
            third passes: Review B launched after the snapshot through the launcher and ended
            with exit 0, the last `verify` OK; `snapshot` and `verify` remove an older mark), so a
            merge that skipped the cross-family review has no way through; refuses a dirty
            tree; the head about to merge must descend from the reviewed head and differ from
            it only under run/review/ (the review files removed with `git rm`); with <pr>, the
            pull request's head on GitHub must equal the local HEAD (push first; a branch
            updated from main needs the reviews again). It writes the record the permission
            guard reads (<git common dir>/bridge/premerge/<head>) and prints the merge command
            with `--match-head-commit`.

Exit 0 = OK; 1 = GATE-INTEGRITY (open the flag, condition 4, and an issue; do not merge);
2 = cannot verify (no snapshot, dirty tree, git or gh failure). Never prints a value of
anything. ASCII-only.

What it does not cover, said plainly (KP-032): the contents of cache folders, anything
outside the checkout (the owner's profile, the installed bridge, other projects), and a
reviewer that deliberately reaches for the credential store. It is a guard against what a
reviewer does in passing, not a sandbox.
```

## roster-check.py

Path: `bridge/cursor-bridge/roster-check.py`

```
roster-check: resolve which models fill the builder / Review A / Review B roles today,
prove three distinct families, and (optionally) prove each model answers.

  python roster-check.py docs/ROSTER.json [--command "<delegate command>"] [--no-probe] [--out docs/ROSTER.resolved.json] [--run-log run/launcher/runs.jsonl]

docs/ROSTER.json (v2):
{
  "other_pool": "available" | "exhausted",      <- Cursor's "Other Models" usage pool (every
                                                    third-party model). Set automatically by
                                                    --record-failure, restored on reset_day, or
                                                    by the owner (--mark-exhausted/--mark-reset).
                                                    A probe cannot see 1% remaining.
  "review_a": "claude-opus-5-5",                  <- Review A runs in Claude Code, not Cursor.
  "profiles": [                                   <- tried in order; the first usable one wins
    {"name": "full",   "builder": "grok-4.7-high", "review_b": "gpt-5.6-sol-high"},
    {"name": "native", "builder": "composer-2.5",  "review_b": "grok-4.7-high"}
  ]
}
A model entry is an id string or {"model": id, "family": name, "pool": "native"|"other"}.
Pool is inferred from the id per Cursor's docs: Grok (any effort/host prefix) and Composer are
the "Cursor Models" pool (native); every third-party model is "Other Models".
A profile is skipped when other_pool is "exhausted" and any of its models is in the other
pool. Unless --no-probe, the builder and Review B of a candidate profile are each sent a
one-word request through `cursor-agent -p -f --model <id>`; a refusal, empty reply, or
timeout marks the profile unusable (this catches hard failures only, never a nearly-empty
quota). The chosen profile's three families must be distinct. The result is written to
docs/ROSTER.resolved.json for the delegate and Review B commands to read.
--record-failure <model> --stderr-file <path> [--stdout-file <path>]
  Classify a failed cursor-agent call. <model> must be a model id of this roster (a wrong
  argument exits 2 and changes nothing). USAGE-LIMIT (a usage/quota/limit message) or a
  second failure of the same model within 2 hours marks the model's pool exhausted in
  docs/ROSTER.json automatically (auto_exhausted_at / auto_exhausted_reason) and exits 3 =
  "re-resolve and restart the step". A connection error (lost, reset, reconnect, 5xx, 429)
  or a hit run limit (bridge-run's LIMIT line) is not the model's fault: exit 4 = "retry
  the same step once", twice per window, then exit 5 = "stop and tell the owner" (no
  switch helps a dead line). A first other failure is exit 4 too. The counts expire after
  8 hours, longer than any run limit, and --record-success <model> clears them. An
  automatic "unavailable" mark expires after 6 hours.
The changing state (pool, marks, counts) is kept in <git common dir>/bridge/roster-state.json,
never in the tracked roster, so a reset of the working tree cannot erase a switch; a roster
from an older release seeds the state file once.
--mark-exhausted   the owner said "usage exhausted": stamp other_pool exhausted now (UTC).
--mark-reset       the owner said "usage reset": restore other_pool and clear marks now.
Automatic reset: "reset_day" (day of month, UTC; e.g. 16) in the roster. When other_pool is
exhausted and the current UTC time is at or past 00:00 UTC of the first reset_day strictly
after exhausted_at, the check restores other_pool to "available" by itself, clears the
unavailable marks and failure counts, and says so. Timestamps are UTC. ROSTER_NOW=<ISO UTC>
overrides "now" for tests.
Exit 0 = resolved; 1 = no usable profile, a family collision, or a command mismatch;
2 = cannot read or a wrong model argument; 3 = pool/model marked exhausted, re-resolve;
4 = transient, retry once; 5 = repeated connection failures or time-outs, tell the owner.
ASCII-only on purpose.
```

## run-hidden.py

Path: `bridge/cursor-bridge/run-hidden.py`

```
run-hidden: launch a console command with NO visible console window (Windows).

Use it to wrap any direct-command hook entry in .cursor/hooks.json (the design
detector, Semgrep, a linter) so the child process cannot pop a terminal window on
the user's desktop. On non-Windows it is a transparent pass-through.

  <python.exe> .cursor/hooks/run-hidden.py <command> [args...]

- stdin (the hook's JSON payload) is inherited by the child unchanged.
- stdout / stderr / exit code are relayed unchanged, so hook semantics are kept.
- A .cmd/.bat executable (npx, semgrep shims) is run via cmd.exe /d /c, hidden.
- Never use this for a process the user is meant to watch or interact with.

ASCII-only on purpose (cp1252 consoles).
```

## scope-check.py

Path: `bridge/cursor-bridge/scope-check.py`

```

Bridge scope check - deterministic changeset-vs-brief verification.

After a delegation (run from the clean checkpoint commit), this compares what the builder
ACTUALLY changed - derived from git, never from the builder's own summary - against the
Scope the handoff brief declared. Any changed file outside that Scope is SCOPE DRIFT, and
it is surfaced deterministically here rather than discovered by eyeballing a diff.

Why git-derived: the builder's printed "files I changed" list is a self-report and has been
wrong in practice (claimed fixes not made, unrequested edits described as requested ones).
The working tree is the only trustworthy manifest. Region-level drift *within* an in-scope
file is still diff-reviewer's judgement; this tool owns the file-level floor.

Usage:
    python scope-check.py handoff/TASK-<nnn>.md [--base <git-ref>]

    --base   commit to diff against. Default: the commit that FIRST added the brief (the
             checkpoint commits the brief; a brief fixed and committed later never moves the
             base past the builder's commits); HEAD when the brief is not committed.

Output lines: BASE (with how it was chosen), SCOPE, NOT READ AS A PATH (a Scope bullet that
names no path, reported and ignored), CHANGED, BOOKKEEPING (the files a builder must write),
RECORDS (the supervisor's record files changed only by commits that touched records alone
since the checkpoint: not drift; a commit that mixes code with a record is the builder's),
IN SCOPE, SCOPE DRIFT, VERDICT. The Scope is the brief's top-level bullets up to the first
line that is neither a bullet nor blank (a bold note, prose): sub-bullets are not paths.

Exit codes:
    0  every changed file is inside the declared Scope
    1  SCOPE DRIFT - one or more changed files are outside Scope (listed on stdout)
    2  cannot verify (brief missing, no Scope section, or git failed) - treat as
       needs-attention; do NOT proceed as if scope were clean.

Scope entries (bullets under "## Scope", up to the next heading of any level) may be exact
files, directories (trailing "/" or a bare directory name), or globs (* and ?; brackets are
literal, as in a route folder `[id]`). A bullet may name several paths (commas, "and"),
quoted or in backticks; prose after a path is dropped; an ellipsis cannot be verified.
The bookkeeping files a builder must write (docs/BUILDER_NOTES.md, docs/BOUNDARY_VIOLATIONS.md,
anything under run/, its report file handoff/<brief>-rN-report.md) are never drift. Paths are compared with forward slashes.
```

## session-start.py

Path: `bridge/cursor-bridge/session-start.py`

```
session-start: a Claude Code SessionStart hook (matchers: compact, resume, fork) that puts
the supervisor's core rules back after a compaction, a resume or a fork (KP-035).

Why: when a session's context is compacted, Claude Code re-attaches only the first part of
an invoked command (measured: 20,000 of the supervisor's 150,000 characters, 13%), so the
supervisor carried on for hours without its loop, its gate and its standing rules, and the
record shows the rule-breaking that followed.

Claude Code caps every hook's plain stdout at 10,000 characters and, above that, replaces it
with a file path and a 2,000-character preview. The two things this hook prints do not fit
together under that cap on a real project (the 0b review measured 9,841 characters, and the
part that was cut was the pointers), so the bridge registers the hook TWICE for the same
event, each run printing one part under its own cap:

  --part pointers   the project's phase from docs/PROJECT_STATUS.md (the "awaiting" text
                    capped), the exact sections of supervisor.md to re-read before the next
                    action with their line ranges, the conventions that phase relies on, and
                    whether to continue or to wait for the owner;
  --part digest     the digest at the top of ~/.claude/commands/supervisor.md (between the
                    markers <!-- digest:start --> and <!-- digest:end -->), the one text the
                    maintainer keeps as the condensed core.

Without --part both are printed (tests, manual runs). It prints nothing outside a bridge
project (no docs/PROJECT_STATUS.md found from the session's folder, its Workspace, a parent,
or a worktree). It FAILS OPEN on purpose: a session that is not the project's supervisor
(a review or a planning session opened in a project folder) is told to ignore the message,
because a gate on the transcript silenced the hook on two of three live supervisor sessions
(one invoked through the Skill tool, one continuing an earlier transcript; the 0b review's
second pass, S1), and a silent supervisor is the failure this hook exists to prevent. A
forked session is told not to continue the loop (S8). It never blocks (exit 0 always), never
writes anything, and keeps each part under the cap. ASCII-only apart from what it quotes.
```

## shell-guard.py

Path: `bridge/cursor-bridge/shell-guard.py`

```

Bridge shell guard — a fail-closed `beforeShellExecution` hook for the headless
Cursor builder (cursor-agent). It runs BEFORE the builder executes any shell command
and DENIES a tight, high-confidence set of genuinely dangerous / irreversible /
data-exfil commands. Everything else passes untouched.

This is the ONE deliberately fail-closed hook in the bridge (the linter/design/security
detect hooks are advisory/fail-open). Wire it in `.cursor/hooks.json` with
`"failClosed": true` so a crash/timeout/bad-JSON BLOCKS — Cursor has a documented bug
where a malformed hook response silently ALLOWS, so this script also defaults to DENY on
any internal error (belt-and-suspenders).

Contract (Cursor hooks):
  - stdin  : JSON payload for the beforeShellExecution event (carries the command string).
             On Windows, Cursor prefixes it with a UTF-8 BOM — decode utf-8-sig.
  - stdout : {"permission": "allow"|"deny", "user_message": ..., "agent_message": ...}
  - exit   : 0 = proceed, 2 = block (equivalent to permission:"deny").

Scope note: this governs the BUILDER's shell (cursor-agent). The supervisor's own
`git reset --hard HEAD` recovery runs through Claude's Bash tool, NOT cursor-agent, so it
is unaffected — which is why blocking destructive git here is safe.

The deny-list below is the auditable policy. Keep it tight: an over-broad guard that
stalls normal builds is the fastest way to get a safety control switched off.
```

## sync-check.py

Path: `bridge/cursor-bridge/sync-check.py`

Compare local <base> with the remote's <base>.

### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--apply`; default: `false`; required: false; fast-forward local <base> when BEHIND
  - - `--strict`; default: `false`; required: false; project end: OFFLINE/UNPUBLISHED fail
  - - `--base`; default: `"main"`; required: false
  - - `--remote`; default: `"origin"`; required: false

## wake-timer.py

Path: `bridge/cursor-bridge/wake-timer.py`

```
wake-timer: a background command that ends at an agent's ceiling, so that its completion
wakes the session (release A4, KP-043).

  python wake-timer.py <seconds> "<what it bounds>"

Started in the background (the app's run-in-background Bash), it sleeps for <seconds> and
prints one line. A scheduled wake-up (CronCreate) does not fire while a background agent is
running, since the session is not idle for the scheduler (proven 2026-10-11, ISS-021 on
reAngle); a background command's completion notification does arrive, so this is the bound
of every waited-on background agent. The loop guard counts an agent as bounded only while a
timer that ends no later than the agent's ceiling is running. Windowless: spawns nothing.
Exit 0 after the sleep; 2 on bad arguments.
```

## windowless-check.py

Path: `bridge/cursor-bridge/windowless-check.py`

```
windowless-check: flag console subprocess launches that would pop a terminal
window on Windows.

Scans hook scripts and agent tooling (default: .cursor/hooks) plus any extra paths
given, and reports every Python subprocess.* / os.system / os.popen call and every
Node child_process spawn/exec call that does not carry the windowless flag:

  Python : creationflags=subprocess.CREATE_NO_WINDOW   (0 on non-Windows)
  Node   : { windowsHide: true }

A call may be exempted with a comment on the same line or the line above:

  # windowless: visible-ok <reason the window serves the user>
  // windowless: visible-ok <reason>

Signal caveat: a call that sets CREATE_NEW_PROCESS_GROUP (a CTRL_BREAK stop path)
is reported as NOTE, not FAIL, when it lacks CREATE_NO_WINDOW - hiding it must be
verified against the stop path, not flipped blindly.

Exit 0 = clean (NOTEs allowed), 1 = at least one FAIL, 2 = nothing scanned.
Usage: python windowless-check.py [path ...]
ASCII-only on purpose (cp1252 consoles).
```

## workflow-check.py

Path: `bridge/cursor-bridge/workflow-check.py`

workflow-check: keep conditional workflows honest against the open list and the extension-point registry (R-014, R-033).

  python workflow-check.py [--open-list FILE] [--registry FILE] [--status FILE]... [ROOT ...]

One program, run at three times: at intake (the project's status file), at every bridge release
(CI, over the bridge's workflow folder and the sample fixtures) and at every calibration (the
installed workflow folder and the project's status file).

ROOT is zero or more workflow folders. Files under ROOT/types/ and ROOT/traits/ are the
conditional workflows; nothing else in a root is read. With no ROOT and no --status, the root
is the workflow folder beside this program. With --status and no ROOT, only the status files
are checked. --open-list defaults to workflow/open-list.md beside this program, and --registry
to workflow/extension-points.md beside this program. --status FILE may be repeated. The same
two tables are used for every root and every status file of one run.

Finding lines, then one RESULT line:
  FAIL (a)        an Add at or Set at names a point key that is not a Key of the registry
  FAIL (b)        a trait file contains a Set at or a Replace heading
  FAIL (c)        a Replace names a module that is missing or whose Replaceable is not yes
  FAIL (d)        a sub-workflow's type folder, type file, or sub-type does not match
  FAIL (e)        a Workflows line's product type, sub-type, or part name is wrong
  FAIL (f)        a Workflows line names a product type or sub-type whose Written is not yes
  FAIL (set)      a Set at names a point whose Changes cell does not contain set
  FAIL (kind)     a delivery-kind heading or intake.delivery-kind value is missing or unlisted
  FAIL (unknown)  a file key or a Workflows name is not in the open list
  FAIL (form)     a file, a change heading, or a Workflows line has the wrong shape
  FLAG (trait)    a trait on a Workflows line is not yet written; flagged, work continues (non-fatal)

Exit 0 when no FAIL line was printed (FLAG lines may have been printed). Exit 1 when at least
one FAIL line was printed. Exit 2 when the check cannot run: a ROOT that is not a folder, a
folder under a root that cannot be listed, a types/ or traits/ path that cannot be examined,
an open list, registry, or status file that does not
exist or cannot be read as UTF-8, a required heading or required column missing, a table with
no separator row, or a table row whose cell count differs from its header. On exit 2 the
program prints ERROR lines and RESULT: not checked, and no traceback. A command-line usage
error also exits 2; the usage line argparse prints stays as it is, argparse's message is
escaped the same way as a printed field, and the last line on standard output is
RESULT: not checked.


### Positionals

  - - `roots`; required: false

### Options

  - - `-h --help`; default: `"==SUPPRESS=="`; required: false; show this help message and exit
  - - `--open-list`; default: `"<bridge folder>/workflow/open-list.md"`; required: false
  - - `--registry`; default: `"<bridge folder>/workflow/extension-points.md"`; required: false
  - - `--status`; default: `[]`; required: false

## worktree-teardown.py

Path: `bridge/cursor-bridge/worktree-teardown.py`

```
worktree-teardown: remove a git worktree safely (supervisor rule 19, release A1b).

  python ~/.claude/cursor-bridge/worktree-teardown.py <worktree path> [--dry-run]

`git worktree remove` follows a gitignored junction or symbolic link inside the worktree
(a per-worktree venv, a linked node_modules) and deletes the real target, in an ordinary
removal as in a forced one (Git for Windows 2.53, verified 2026-10-06); one project lost
its main checkout's installed packages that way, and forced the removal fourteen times in
four days. The permission guard refuses the git command; this program is the one way:

  1. every entry inside the folder is looked at without following links, whether git still
     lists it or not (a leftover of a failed removal too); a junction or a symbolic link
     anywhere inside refuses the teardown and is listed with its target, so the link can be
     removed by itself first (rmdir on the link, never through it);
  2. the path must be a worktree of the repository the current folder belongs to: a leftover
     (a folder whose .git file points to a git folder that is gone, or under Worktrees/) is
     named as such, and a folder that holds a registered worktree is refused;
  3. `git worktree remove <path>` without --force; git's own refusal (a dirty or locked
     worktree) is printed and ends the program, because forcing is what destroys data;
  4. `git worktree prune`, and the path must be gone.

Exit 0 = removed; 1 = git refused (commit or clean the worktree, never force); 2 = refused
here (not a worktree, or a link inside). ASCII-only on purpose (cp1252 consoles).
```
