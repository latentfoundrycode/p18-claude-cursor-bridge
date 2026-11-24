# D-004 context-dfd — what crosses the bridge's trust boundaries (as built)

Level 2. Drawn as built (conventions §8) from the code on 2026-11-01; revised as designed on 2026-11-13 for the program release (`docs/DESIGN.md`, "Change: the program release", "Architecture — the diagrams the change touches"; the note so headed below), whose flows are built by its increments, and on 2026-11-24 for the improvements release ("Change: the improvements release (2026-11-24)", the same heading; the last note below), whose flows are built by its increments too. Realizes R-055, R-080, R-081, R-083, R-085, R-087, R-089, R-097, R-100, R-107, R-114, R-117, R-121, R-125, R-126, R-129. Enforced by review: `security-auditor` checks every edge crossing a `tb_` subgraph. A process that is a D-002 component has D-002's name behind `p_`.

Notes:

- `SECRET:` marks a flow carrying a secret or credential; `UNTRUSTED:` one carrying what another vendor's agent wrote or chose. `--x` is withheld by the code; a dotted edge is reachable only by a deliberate act the bridge does not prevent (KP-032: not a sandbox; the agents run as the owner's Windows user).
- **Stripped environment** (`bridge_env.stripped_env`; the shim applies the same test). Withheld: `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`, `GIT_ASKPASS`, `SSH_ASKPASS`, `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_0`, `GIT_CONFIG_VALUE_0`, every name `SECRET_LIKE` matches (whole-word TOKEN or SECRET, PAT, CREDS or AUTH as a name part bounded by `_` or the name ends, PASSWORD, PASSWD, PASSPHRASE, CREDENTIAL, API, ACCESS or PRIVATE KEY, a `_KEY` or `_KEYS` ending, DATABASE_URL, SSH_AUTH_SOCK) but `CURSOR_*` for builder and review runs only (withheld from test and driver runs) and `GIT_CONFIG_KEY_*` for every run. Set: `GH_CONFIG_DIR` (the empty folder), `GIT_TERMINAL_PROMPT=0`, `GIT_CONFIG_GLOBAL` (the bridge's gitconfig: includes `~/.gitconfig`, resets the helper list), `GIT_CONFIG_PARAMETERS='credential.helper='` (read after the checkout's `.git/config`), `HOME`, `USERPROFILE`, `HOMEDRIVE`, `HOMEPATH` (the agent home), `APPDATA`, `LOCALAPPDATA` (the agent home's skeleton, `AppData/Roaming` and `AppData/Local`, each where the launcher's own environment has the variable: a program the run starts that writes its key file, cache or state through either writes there and never into the owner's real folders; one link in the redirected `Roaming` folder, `Cursor`, leads to the owner's `%APPDATA%/Cursor`, where `cursor-agent` reads its login, and where that link cannot be made or leads elsewhere `APPDATA` keeps the owner's folder for the run; release S, probed on the owner's computer on 2026-11-11), `HF_HUB_CACHE`, `TORCH_HOME`, `PUPPETEER_CACHE_DIR`, `UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR`, `PIP_CACHE_DIR`, `PYTHONUSERBASE`, `NPM_CONFIG_CACHE`, `YARN_CACHE_FOLDER`, `PLAYWRIGHT_BROWSERS_PATH`, `GOCACHE` (the owner's caches and installed packages, where present and the variable unset). Passed: the rest; a program that asks Windows itself for a known folder is not redirected. An unusable agent home refuses the run (exit 125). A key file that names a home variable (`USERPROFILE`, `HOME`, `HOMEDRIVE`, `HOMEPATH`, `APPDATA` or `LOCALAPPDATA`) is refused before the run (exit 125, the name printed, the value never), since its value is applied after the strip.
- `bridge-run.py` strips for `cursor-agent` and with `--strip`; the loop's and the calibration's suite and driver launch commands carry `--strip` (R-052, TASK-041), the increment's own test files with them (BUG-043), the driver with `--scratch` naming its folder under the owner's profile, outside the agent home the strip names as `HOME`. A test, driver or watch run without the flag still gets the owner's environment; of the launcher's runs of builder-written code, the loop's text leaves the flag off by name for a driver whose suite needs a variable beyond `.env`, under a recorded Decision in `docs/INVENTORY.md` naming the variable. Whatever does not go through the launcher runs in a session's own environment, stated limits (`docs/INVENTORY.md`, Decisions; BUG-043), among them: a runner the launcher refuses, and a benchmark or profile; a build, a type check or a linter; a hook a commit runs; a reviewer's or auditor's own run beside its reading; a root-cause reproduction; an installer rehearsal; a live smoke and a stage demonstration's start of the product. A stripped run can still write `.git`, which a later git command of the session runs: step 4's check, not a boundary (KP-032). `--key-file` is refused with `cursor-agent` and a driver; a driver's copy carries the project's `.env`. A watch run (`gh pr checks`) runs no builder-written code and keeps the owner environment by design. `p_test_suite` stays in `tb_supervisor`: it is the owner's user running the project's own interpreter in the Workspace, launched and bounded by the supervisor, its environment stripped by the loop's `--strip` but its process no agent's.
- The guard's records lie in the checkout's `.git`; the sha256 copy outside it finds a rewritten snapshot. Both are in the owner's profile, which the agents' user can reach.
- **The program release** (docs/DESIGN.md, "Change: the program release", 2026-11-13; R-081, R-083, R-085, R-087, R-097, R-100). `p_evaluate_reports` (its `security` step) makes the Sunday evaluation's reads of GitHub, by GET alone, the projects' roots from `ds_projects_file`, a per-computer file outside every repository; the supervisor no longer makes them by hand. The rule's reader is one copy in `bridge_env.py`: `p_review_guard` (`ready`, `premerge-records <pr>`) and `p_bridge_run` (its wait before a CI watch) read a branch's required check contexts (the classic protection and the rules that apply to the branch, of the base and, where it names none, of the default branch), the repository's auto-merge setting and default branch, and a pull request's head, its checks, its commit statuses and its workflow runs by GET with the owner's `gh` login, beside `conformance-check.py`'s read of the same rule, which this diagram does not draw; nothing is written to GitHub by these reads, and a failed read is never a pass. On READY `p_review_guard` writes the ready record for the pull request and its head beside the premerge record in `ds_guard_records`, and `p_permission_guard` refuses a merge whose head lacks either. `p_push_scan` reads git's commits of the range to be pushed and the owner's account names (derived at run time, extended by `ds_names_file`) and prints a hit's place to the supervisor's terminal, never the matched text, since that terminal is recorded in the session's transcript; nothing leaves the computer. Around a test or driver run `p_bridge_run` reads the repository's `config` and `info/attributes`, the worktree's own `config.worktree` and every entry of the hooks folders by name and content, before and after, and prints one `GIT-CONFIG` line per difference on standard error, the run's exit unchanged: a detection, never a restore; step 4's check stays, since a session's git command may still run before it. `p_claude_subagents` (`spec-packager`, `diff-reviewer`) may query `ext_docs_service` (Context7, an MCP server the owner sets up at user scope in Claude Code; the free tier, no key) with library names, the version the project's lockfile pins and topics, never project code, a path of this computer or a name; what it returns is outside input, marked `UNTRUSTED:` here beside the note's first meaning: data, a hint and never evidence, never an instruction. TASK-080's probe decided the form (docs/HARDENING.md, "TASK-080: Context7 for the Claude side"): a subagent whose `tools:` line names `mcp__context7__*` started and answered in a session where no such server was configured, so the first form is built, the two flows from `p_claude_subagents`, and the figure draws it as it stands. The permission guard does not see these MCP calls (its matcher is for the Bash and PowerShell tools and, by the improvements release, the file tools `Edit`, `Write` and `NotebookEdit`), so a query is a way out of the computer that no hook of the bridge reads: what it may carry is held by the two definitions' text alone.
- **The improvements release** (docs/DESIGN.md, "Change: the improvements release", 2026-11-24; R-107, R-114, R-117, R-121, R-129). `p_permission_guard` sees the supervisor's `Edit`, `Write` and `NotebookEdit` calls beside the Bash and PowerShell commands, the hook settings' matcher naming the three file tools, and refuses a call whose file's path, as written or resolved, is a listed secret path or lies under a listed folder, as it refuses a redirection, a command of its table of writing, deleting and moving programs, or `git clean -x` or `-X`, on one; MCP calls stay unseen. It reads two lists: `secret_paths` in the checkout's `project.json` (relative to the Workspace root, a trailing slash naming a folder; `.env` and `secrets/` at the Workspace root listed always), and `ds_secret_paths_file`, `~/.cursor-bridge/secret-paths.txt`, a per-computer file of absolute paths, one a line, which lies outside every repository as `ds_projects_file` and `ds_names_file` do, is itself always listed and holds paths, never a key. Both lists are outside input, compared as text and by their resolved form and never executed; where `project.json` cannot be read the defaults and the per-computer list hold and the guard never fails closed on its own reading. It stays a guard against a mistake in the supervisor's own hand, never a sandbox: a builder or a reviewer is a `cursor-agent` process this hook never sees (TASK-100a, TASK-100b). Where a project enables the opt-in `p_shell_guard`, it reads the project's list from the checkout beside its fixed patterns and denies a builder's or a reviewer's redirection, `cp`, `mv`, `rm`, `tee` or `touch` onto a listed path; the per-computer file is out of its reach, a builder's or a reviewer's run having the agent home for its home (TASK-101). At a review launch `p_bridge_run` reads from `ds_guard_records` the snapshot record of the name given with `--review` and refuses the launch with exit 125 where the guard holds none; it opens `run/review/REVIEW-<name>.err` itself for its own and the child's standard error, names the reply file on a line of it, `bridge-run: reply run/review/REVIEW-<name>.out`, and writes the child's standard output, as it arrives, to that file, the kept reply, while passing it through. Both files are in `ds_run_outputs`, in the checkout and in the reviewer's reach as the `.err` is today; `verify` keeps and excuses them, flags any other new file under `run/review/` and, only where the log names a reply file, answers `REPLY EMPTY` where the run ended with exit 0 and that file is missing or holds no word, its mark then one `premerge` refuses and the launch no reply at `snapshot` either; a log that names no reply file, a review launched before the install, is read as before; the `--review` check proves that a snapshot of that name exists, `verify` that it is untouched (TASK-092). The built set (R-107): `p_roster_check` and `p_bridge_run` read the families that built the branch from `ds_runs_log`, every builder run of the branch's briefs, the runs before a rebuild from the checkpoint dropped by the rows' `head` and `clean`, beside the report files the branch adds under `handoff/` in `ds_checkout`; the record lies in the checkout, where a builder or a reviewer can write, so both reads are `UNTRUSTED:`, and the set is unknown, never read as nobody having built, where the record cannot be read whole or lacks the builder row of such a report. A launcher row gains the optional `retries`, a builder row the launch's `head` and `clean`. `p_roster_check` writes the resolved roster, `docs/ROSTER.resolved.json` in `ds_checkout`, with a `deviation` entry (the model, the reason, `family`, `unavailable` or the one given with `--review-alt`, the branch, the built families) in place of `rebuild` where the alternate reviewer resolves. `p_bridge_run` reads the same built set, never the last builder run alone, and refuses a review by a model of any family in it, and of any builder's family the roster file names where it is unknown; a review on the profile's builder model passes only where the resolved roster's `deviation` names that model for this branch, the set is known, the model's family is not in it and the entry's families equal the set read at the launch; otherwise it is refused, "resolve again", and nothing the launcher cannot read opens it (TASK-086a, TASK-086b). The interpreters (R-117): `p_bridge_run` reads `project.json`'s `interpreters` as the merge base of the branch with `origin/main` holds it, gated content read from the repository's objects, never from the working tree or the branch's own commits, none where there is no `origin/main`, and launches a named one for the driver or test kind, in a stripped run alone, where it lies inside the launch roots through no link; a builder that replaces the file at a listed path gains the stripped environment a test file already has, and nothing else (TASK-095). `p_loop_guard`, `loop-guard.py`, the stop hook, reads the current span's tool calls with their inputs from the session's transcript, a file of the host's (Claude Code) under `ext_claude_home`, a span being what the transcript holds after the later of the owner's last message and the guard's last evaluated stop, the span's last message arriving in the hook's own input, to see whether a `PushNotification` carrying the same opener or an `AskUserQuestion` call was made, and reads the status file's `Awaiting user on:` and the in-flight log's last line from the checkout; the transcript is the host's record, read, never written, read once more after two seconds where the call is not found, and where it cannot be read the hook allows. Its one record of its own, under the git common folder's `bridge/` (`ds_guard_records`), holds the wait's text, the transcript's place of its last evaluated stop, an opener owed after a refusal for a missing push and a question refused, and nothing else of the conversation. It refuses a `Needs you` line where no push carrying the same opener stands in the span, once more at the next stop where that push is still missing, and then drops the debt, so a request is refused twice at the most; a new wait without the line or such a push; and option labels in the form of an offered choice where the span holds no question form; the findings gathered into one refusal. Where its host fact holds (a `PreToolUse` matcher can name `AskUserQuestion`, TASK-110b's probe), a second entry of the hook settings runs it before a question form, which it refuses where no push stands in the span before the call and after any earlier question, unless its own record shows a question refused since the span began; where that probe fails, that increment's records-only pull request redraws the hook's element text, the question-form flow and this note to the three stop rows alone (TASK-110a, TASK-110b). `p_phrase_list` (R-125, TASK-105) and `p_test_readers` (R-126, TASK-106), read-only programs of the supervisor's shell as `p_push_scan` is, read the checkout and git's range and print to the supervisor's terminal; nothing leaves the computer, and their reads cross no boundary but the checkout's, inward, as `p_push_scan`'s do. None of these changes the stripped environment, the withheld and set names, CI's secrets or the agents' boundaries.
- **The listed projects' checkouts** (amended 2026-11-22 from TASK-077's report, docs/HARDENING.md, "D-004"; R-097). `ds_project_checkouts` stands for the Workspace checkout of every project `ds_projects_file` lists, each agent-writable in its own project as `ds_checkout` is here (where the bridge's own root is listed, its checkout is `ds_checkout`). `p_evaluate_reports` (`security`) reads each one's `origin` remote through git to name the OWNER/REPO its GETs read; the `.git/config` it comes from is one an agent may write, so the URL is `UNTRUSTED:` and only a URL that parses as a GitHub repository names one. `p_pace_report` reads the same file through `evaluate-reports.py`'s `load_projects` where no root is given, reads each listed checkout's history and records read-only, adds the bridge's own root where no root is given on the command line and the projects file does not list it, and writes nothing. The store stands in a boundary of its own, `tb_projects`: no snapshot or verify of this project's review covers another project's checkout (Review A of stage P3's close records). `p_pace_report` realizes R-089 too.

| Element | Paths |
|---|---|
| p_supervisor | bridge/commands/supervisor.md (the session) |
| p_permission_guard | bridge/cursor-bridge/permission-guard.py |
| p_loop_guard | bridge/cursor-bridge/loop-guard.py (the Stop hook and, where its host fact holds, a second entry before an AskUserQuestion call) |
| p_bridge_run | bridge/cursor-bridge/bridge-run.py |
| p_bridge_env | bridge/cursor-bridge/bridge_env.py |
| p_cursor_agent_shim | bridge/cursor-bridge/cursor-agent.shim |
| p_roster_check | bridge/cursor-bridge/roster-check.py |
| p_review_guard | bridge/cursor-bridge/review-guard.py |
| p_pr_activity_check | bridge/cursor-bridge/pr-activity-check.py |
| p_bridge_install | bridge/cursor-bridge/bridge-install.py |
| p_evaluate_reports | bridge/cursor-bridge/evaluate-reports.py (its security step) |
| p_pace_report | bridge/cursor-bridge/pace-report.py |
| p_push_scan | bridge/cursor-bridge/push-scan.py |
| p_phrase_list | bridge/cursor-bridge/phrase-list.py (designed; TASK-105) |
| p_test_readers | bridge/cursor-bridge/test-readers.py (designed; TASK-106) |
| p_claude_subagents | bridge/agents/spec-packager.md, bridge/agents/diff-reviewer.md (the Claude-side subagents that write briefs and review diffs) |
| p_test_suite | a project's suite, an increment's own test files or a mutation run under bridge-run.py, kind test or driver; a declared interpreter's run in a stripped run (designed; TASK-095) |
| p_builder | cursor-agent, builder run |
| p_review_b | cursor-agent, review run |
| p_shell_guard | bridge/cursor-bridge/shell-guard.py (.cursor/hooks/ copy) |
| p_ci_tests | .github/workflows/tests.yml, job tests |
| p_ci_security_floor | .github/workflows/tests.yml, job security-floor |
| p_dependency_scan | .github/workflows/dependency-scan.yml |
| ds_checkout | the Workspace and Worktrees/ checkouts |
| ds_project_checkouts | each project's Workspace/ under a root ~/.cursor-bridge/projects.json lists: its .git (config, refs/heads/main, bridge/ rounds files), run/, handoff/, docs/HARDENING.md |
| ds_run_outputs | run/agent/\*.err, run/agent/\*.out, run/review/REVIEW-nnn.err, run/review/REVIEW-nnn.out (designed; TASK-092) |
| ds_runs_log | run/launcher/runs.jsonl |
| ds_guard_records | git common dir bridge/ |
| ds_review_hashes | ~/.cursor-bridge/review-hashes/ |
| ds_heavy_lock | ~/.cursor-bridge/heavy.lock |
| ds_agent_home | ~/.cursor-bridge/agent-home/ |
| ds_bridge_gitconfig | ~/.cursor-bridge/gitconfig |
| ds_projects_file | ~/.cursor-bridge/projects.json |
| ds_names_file | ~/.cursor-bridge/names.txt |
| ds_secret_paths_file | ~/.cursor-bridge/secret-paths.txt |
| ds_gh_empty | ~/AppData/Local/cursor-bridge/gh-empty/ |
| ds_no_hooks | the system's temporary folder, review-guard-no-hooks-\*/ (outside the repository; made fresh and empty per process by tempfile.mkdtemp, removed at exit while it is empty, nothing checking that it is empty) |
| ds_actions_secrets | Actions secret SOCKET_SECURITY_API_KEY |
| ext_owner | the owner |
| ext_user_env | the Windows user environment |
| ext_credential_store | the system credential store |
| ext_owner_profile | ~/.gitconfig, ~/.ssh, ~/.aws, ~/AppData |
| ext_key_file | a key file outside the Workspace |
| ext_claude_home | ~/.claude |
| ext_cursor_home | ~/.cursor |
| ext_beside_workspace | the files beside the Workspace |
| ext_cursor_service | Cursor's service |
| ext_github | GitHub account, repository, API |
| ext_advisory | OSV, Socket, Semgrep registry |
| ext_docs_service | Context7, the documentation service (an MCP server the owner sets up at user scope in Claude Code) |

```mermaid
flowchart LR
ext_owner["Owner"]
ext_user_env["Windows user environment"]
ext_credential_store["Credential store"]
ext_owner_profile["Owner's profile stores"]
ext_key_file["Key file"]
ext_claude_home["~/.claude"]
ext_cursor_home["~/.cursor"]
ext_beside_workspace["Files beside the Workspace"]
ext_cursor_service["Cursor's service"]
ext_github["GitHub"]
ext_advisory["Advisory sources"]
ext_docs_service["Documentation service, Context7"]

subgraph tb_supervisor["Supervisor's session: the owner's identity"]
p_supervisor("Supervisor session")
p_permission_guard("permission-guard")
p_loop_guard("loop-guard, the stop hook")
p_bridge_run("bridge-run: job, limit, BOUNDARY")
p_bridge_env("stripped_env, agent_home")
p_cursor_agent_shim("cursor-agent shim")
p_roster_check("roster-check probe")
p_review_guard("review-guard")
p_pr_activity_check("pr-activity-check")
p_bridge_install("bridge-install")
p_test_suite("Suite or mutation run")
p_evaluate_reports("evaluate-reports security")
p_pace_report("pace-report")
p_push_scan("push-scan")
p_phrase_list("phrase-list")
p_test_readers("test-readers")
p_claude_subagents("spec-packager, diff-reviewer")
ds_review_hashes[("review-hashes")]
ds_heavy_lock[("heavy.lock")]
ds_bridge_gitconfig[("bridge gitconfig")]
ds_gh_empty[("gh-empty")]
ds_no_hooks[("review-guard-no-hooks")]
ds_projects_file[("projects.json")]
ds_names_file[("names.txt")]
ds_secret_paths_file[("secret-paths.txt")]
end

subgraph tb_agents["Agent processes: identity withheld"]
p_builder("Builder")
p_review_b("Review B, force")
p_shell_guard("shell-guard, fail-closed")
ds_agent_home[("agent-home: one link .cursor")]
end

subgraph tb_checkout["Checkout: agent-writable, Review B under snapshot and verify"]
ds_checkout[("Checkout")]
ds_run_outputs[("Agent replies")]
ds_runs_log[("runs.jsonl")]
ds_guard_records[("Guard records")]
end

subgraph tb_projects["Other projects' checkouts: agent-writable in their own projects, under no snapshot of this one"]
ds_project_checkouts[("Listed projects' checkouts")]
end

subgraph tb_ci["GitHub's CI: secrets as step-level env only"]
p_ci_tests("CI tests")
p_ci_security_floor("CI security floor")
p_dependency_scan("Weekly scan")
ds_actions_secrets[("Actions secret")]
end

ext_owner -->|"instructions, decisions"| p_supervisor
ext_claude_home -->|"commands, agents, hooks, digest"| p_supervisor
ext_user_env -->|"SECRET: whole environment, tokens and keys included"| p_supervisor
p_supervisor -->|"each Bash or PowerShell command"| p_permission_guard
p_permission_guard -->|"deny: admin or API merge, force-push, worktree remove, chains, no-verify, agent around the shim, merge without premerge record or, by the program release, ready record"| p_supervisor
ds_guard_records -->|"premerge record, ready record (R-083)"| p_permission_guard
p_supervisor -->|"each Edit, Write or NotebookEdit call, its file's path; MCP calls unseen (R-121)"| p_permission_guard
ds_checkout -->|"UNTRUSTED: project.json's secret_paths, relative to the Workspace root; outside input compared as text and by its resolved form, never executed (R-121)"| p_permission_guard
ds_secret_paths_file -->|"absolute secret paths, one a line, never a key; outside input compared as text and by its resolved form, never executed (R-121)"| p_permission_guard
p_permission_guard -->|"deny: an Edit, Write or NotebookEdit call, a redirection or a writing, deleting or moving command on a listed path, git clean -x or -X while one lies in the checkout (R-121)"| p_supervisor
p_supervisor -->|"SECRET: owner's gh and git login: push, PR, merge with --match-head-commit"| ext_github
p_supervisor -->|"briefs, checkpoints, nothing during a review"| ds_checkout
ds_run_outputs -->|"UNTRUSTED: builder note, Review B verdict"| p_supervisor

p_supervisor -->|"SECRET: owner environment, command"| p_bridge_run
p_bridge_run -->|"SECRET: environment to strip"| p_bridge_env
p_bridge_env -->|"stripped environment"| p_bridge_run
p_bridge_env -->|"empty folder"| ds_gh_empty
ext_owner_profile -->|"~/.gitconfig included: identity, safe.directory"| ds_bridge_gitconfig
p_bridge_env -->|"helper list reset"| ds_bridge_gitconfig
p_bridge_env -->|"link checked, skeleton"| ds_agent_home
p_bridge_run -->|"stripped environment, prompt, in the job"| p_builder & p_review_b
p_supervisor -->|"SECRET: owner environment"| p_cursor_agent_shim
p_cursor_agent_shim -->|"stripped environment"| p_builder
p_supervisor --> p_roster_check
p_roster_check -->|"SECRET: environment to strip"| p_bridge_env
p_roster_check -->|"probe run, one word, stripped environment"| p_builder & p_review_b
ds_runs_log -->|"UNTRUSTED: the builder rows of the branch's briefs, the record lying in the checkout where a builder or a reviewer can write: the families that built, the runs before a rebuild from the checkpoint dropped by head and clean; unknown where the record cannot be read whole or lacks the row of a report file the branch adds under handoff/, never read as nobody having built (R-107)"| p_roster_check
ds_checkout -->|"UNTRUSTED: the report files the branch adds under handoff/, each needing its brief's builder row in runs.jsonl (R-107)"| p_roster_check
p_roster_check -->|"docs/ROSTER.resolved.json, with a deviation entry in place of rebuild where the alternate resolves: the model, the reason (family, unavailable or the one given with --review-alt), the branch, the built families (R-107)"| ds_checkout
p_bridge_run -->|"kind, limit, seconds, exit, model, branch, boundary, the optional retries, on a builder row the launch's head and clean; never the prompt (R-107)"| ds_runs_log
ds_runs_log -->|"UNTRUSTED: learned limits; the built set, every builder run of the branch's briefs and never the last alone, the runs before a rebuild from the checkpoint dropped by head and clean; unknown where the record cannot be read whole or lacks the row of a report the branch adds, a review by any builder's family then refused (R-107)"| p_bridge_run
ds_checkout -->|"UNTRUSTED: the report files the branch adds under handoff/, each needing its brief's builder row, and docs/ROSTER.json's builder families, for the built set (R-107)"| p_bridge_run
ds_checkout -->|"UNTRUSTED: docs/ROSTER.resolved.json with its deviation entry (the model, the reason family or unavailable, the branch, the built families), honoured only where the built set is known, the model's family is not in it and the entry's families equal the set read at the launch; otherwise refused, resolve again (R-107)"| p_bridge_run
ds_checkout -->|"project.json's interpreters as the merge base of the branch with origin/main holds it: gated content read from the repository's objects, never from the working tree or the branch's own commits; none where there is no origin/main; a named one admitted where it lies inside the launch roots through no link (R-117)"| p_bridge_run
p_bridge_run -->|"a declared interpreter, admitted, for the driver or test kind in a stripped run alone: a builder that replaces the file at a listed path gains the stripped environment a test file already has, nothing else (R-117)"| p_test_suite
ds_guard_records -->|"rounds for the ceiling"| p_bridge_run
p_bridge_run <-->|"heavy slot, holder"| ds_heavy_lock
p_bridge_run -->|"listing before and after"| ext_beside_workspace
ext_key_file -->|"SECRET: NAME=value to the child only, not to cursor-agent or a driver"| p_bridge_run
p_bridge_run -->|"SECRET: stripped environment (--strip, R-052) on every suite and increment's own test files the loop launches and on every driver but one under a recorded Decision, a suite's or own-file run's named key values by --key-file, handed to that code, a driver's from the project's .env in its scratch copy, its scratch folder named by --scratch under the owner's profile, outside the agent home"| p_test_suite
ds_checkout -->|"UNTRUSTED: code and tests the builder wrote; SECRET: the .env service passwords a driver copies into its scratch copy"| p_test_suite
ds_checkout -->|"UNTRUSTED: code and tests the builder wrote, run in the session's own environment: stated limits (BUG-043)"| p_supervisor
p_test_suite -.->|"UNTRUSTED: a deliberate write, .git config, hooks, which a later git command of the session runs (BUG-043)"| ds_checkout
p_bridge_run -->|"SECRET: owner's gh login, CI watch"| ext_github
ds_checkout -->|"UNTRUSTED: .git/config, .git/config.worktree, .git/info/attributes, the hooks folders' names, read before and after a test or driver run"| p_bridge_run
p_bridge_run -->|"GIT-CONFIG line per difference on standard error, exit unchanged: a detection, never a restore (R-081)"| p_supervisor
p_bridge_run -->|"SECRET: owner's gh login, GET only, the rule's reader in bridge_env: the wait before a CI watch (R-085)"| ext_github
ext_github -->|"the base branch's required check contexts, the default branch's contexts, the pushed head's checks, commit statuses and workflow runs"| p_bridge_run
ds_guard_records -->|"UNTRUSTED: the snapshot record of the name given with --review; none, the launch refused with exit 125 (R-114)"| p_bridge_run
p_bridge_run -->|"UNTRUSTED: run/review/REVIEW-name.err, its own and the child's standard error and a line naming the reply file, bridge-run: reply run/review/REVIEW-name.out; REVIEW-name.out, the kept reply, the child's standard output as it arrives; both in the reviewer's reach (R-114)"| ds_run_outputs

ds_agent_home -->|"link .cursor"| ext_cursor_home
ext_cursor_home -->|"SECRET: Cursor account login"| p_builder & p_review_b
ds_gh_empty -->|"no gh login"| p_builder & p_review_b
ds_bridge_gitconfig -->|"no credential helper"| p_builder & p_review_b
p_builder & p_review_b -->|"prompt, checkout content"| ext_cursor_service
ext_cursor_service -->|"UNTRUSTED: model output"| p_builder & p_review_b
ds_checkout -->|"SECRET: source, .env service passwords"| p_builder & p_review_b
p_builder & p_review_b -->|"UNTRUSTED: edits, commits, refs, .git config, hooks, ignored files"| ds_checkout
p_builder & p_review_b -->|"UNTRUSTED: reply"| ds_run_outputs
p_builder & p_review_b -->|"each shell command"| p_shell_guard
p_shell_guard -->|"deny: irreversible git, protected deletes, download into a shell, exfiltration, hook tampering"| p_builder & p_review_b
ds_checkout -->|"UNTRUSTED: .cursor hook wiring"| p_shell_guard
ds_checkout -->|"UNTRUSTED: project.json's secret_paths, the project's list alone, the per-computer file out of a builder's reach (R-121)"| p_shell_guard
p_builder & p_review_b --x|"withheld: gh login, token, credential helper, prompt"| ext_github
p_builder & p_review_b --x|"no .claude in the home: hooks not imported"| ext_claude_home
p_builder & p_review_b -.->|"deliberate only"| ext_credential_store
p_test_suite -.->|"deliberate only"| ext_credential_store
p_builder & p_review_b -.->|"deliberate only, not found by default: the profile root's stores (~/.gitconfig, ~/.ssh, ~/.aws)"| ext_owner_profile
p_builder & p_review_b -->|"found by default: cursor-agent's login folder under APPDATA, by one link, and the tools' caches by their own variables; APPDATA and LOCALAPPDATA otherwise name the agent home since release S (KP-038)"| ext_owner_profile
p_builder & p_review_b -.->|"UNTRUSTED: write, reported after as BOUNDARY"| ext_beside_workspace
p_review_b -.->|"deliberate only: same user"| ds_review_hashes

p_supervisor -->|"snapshot, verify, premerge nnn"| p_review_guard
ds_checkout -->|"UNTRUSTED: HEAD, refs, stashes, .git config, hooks, ignored files"| p_review_guard
p_review_guard -->|"snapshot, rounds, verified mark, premerge record, ready record (R-083)"| ds_guard_records
ds_guard_records -->|"UNTRUSTED: snapshot, hash-checked"| p_review_guard
p_review_guard <-->|"sha256 copy"| ds_review_hashes
p_review_guard -->|"restore: reset, clean, refs back, hooks off"| ds_checkout
p_review_guard -->|"empty folder"| ds_no_hooks
ds_run_outputs -->|"UNTRUSTED: REVIEW-name.err's exit line and the line naming its reply file; REVIEW-name.out, the kept reply: REPLY EMPTY only where the log names a reply file, the run ended with exit 0 and that file is missing or holds no word, no reply at verify and at snapshot; a log that names none read as before (R-114)"| p_review_guard
p_review_guard -->|"OK, GATE-INTEGRITY, LEFT BEHIND, CANNOT VERIFY, hash, merge command; REPLY EMPTY beside OK where the log names a reply file that holds no word (designed, TASK-092)"| p_supervisor
ext_github -->|"SECRET: PR head, read with the owner's gh login"| p_review_guard
p_supervisor -->|"ready, premerge-records with the PR number"| p_review_guard
p_review_guard -->|"SECRET: owner's gh login, GET only, the rule's reader in bridge_env: ready, premerge-records (R-083)"| ext_github
ext_github -->|"a branch's required check contexts, the default branch's contexts, allow_auto_merge, the PR's head, its checks, commit statuses and workflow runs"| p_review_guard
p_review_guard -->|"READY, NOT READY, CANNOT CHECK; the auto-merge line"| p_supervisor

p_pr_activity_check -->|"SECRET: owner's gh login, GET only"| ext_github
ext_github -->|"PR comments, reviews, owner's events since launch"| p_pr_activity_check
p_pr_activity_check -->|"clean, GATE-INTEGRITY, CANNOT VERIFY"| p_supervisor

p_supervisor -->|"the Sunday evaluation's security step"| p_evaluate_reports
ds_projects_file -->|"the projects' roots"| p_evaluate_reports
ds_project_checkouts -->|"UNTRUSTED: each listed project's origin remote URL from its Workspace/.git config, read-only by git remote get-url, core.fsmonitor off, optional locks off and GIT_DIR and its kin cleared by git_read_env; parsed to the OWNER/REPO the GETs name, a project with no GitHub origin a no remote finding (R-097)"| p_evaluate_reports
p_evaluate_reports -->|"SECRET: owner's gh login, GET only: the weekly workflow's state and runs since the last read, the open Dependabot alerts (R-097)"| ext_github
ext_github -->|"workflow state, runs, conclusions, open alerts"| p_evaluate_reports
p_evaluate_reports -->|"security.md under Reports/Evaluations, a failed read a finding with its remedy, no log text beyond a step's exit line; the window's state in the ledger's _meta"| ext_beside_workspace

p_supervisor -->|"the evaluation's pace table"| p_pace_report
ds_projects_file -->|"the projects' roots where no root is given, read through evaluate-reports' load_projects (R-097)"| p_pace_report
ds_project_checkouts -->|"UNTRUSTED: refs/heads/main's commit log and docs/HARDENING.md numstat, handoff/ briefs and reports, .git/bridge rounds files, run/launcher/runs.jsonl, run/review/REVIEW-nnn.err, run/supervisor/in-flight.md; read-only, git with core.fsmonitor, core.untrackedCache and log.showSignature off, diffs without textconv or external diff, git_read_env"| p_pace_report
ds_checkout & ds_runs_log & ds_guard_records & ds_run_outputs -->|"UNTRUSTED: the bridge's own root, added to the listed ones: the same reads"| p_pace_report
ext_claude_home -->|"with --tokens: the session jsonl files' token counts"| p_pace_report
p_pace_report -->|"pace table, ASCII, to the terminal; writes nothing"| p_supervisor

p_supervisor -->|"before every push: the range"| p_push_scan
ds_checkout -->|"UNTRUSTED: commits of base..HEAD: messages, author and committer lines, added lines, added file names"| p_push_scan
ds_names_file -->|"the owner's further account names"| p_push_scan
ext_user_env -->|"USERNAME, the profile folder's name"| p_push_scan
ext_owner_profile -->|"git config user.name, the local part of user.email"| p_push_scan
p_push_scan -->|"hits to the terminal only: commit, place, line number, never the matched text; nothing leaves the computer (R-087)"| p_supervisor

p_supervisor -->|"a phrase a records diff retires, before its first review"| p_phrase_list
ds_checkout -->|"UNTRUSTED: the files under docs/ or the folder named inside the Workspace; docs/CHANGES.md and docs/archive/ listed apart"| p_phrase_list
p_phrase_list -->|"path and line per occurrence, to the terminal only; nothing leaves the computer (R-125)"| p_supervisor
p_supervisor -->|"before the push: the base of the range"| p_test_readers
ds_checkout -->|"UNTRUSTED: git's range from the base to the working tree, its changed files and changed record lines, the test files' text"| p_test_readers
p_test_readers -->|"per changed file the test files that name it or their count, a changed record's keys, to the terminal only; nothing leaves the computer (R-126)"| p_supervisor

p_supervisor -->|"each stop, the span's last message in the hook's own input; each AskUserQuestion call, by the hook's second entry where its host fact holds (R-129)"| p_loop_guard
ext_claude_home -->|"the session's transcript, the host's record: the current span's tool calls with their inputs, PushNotification with its message and AskUserQuestion among them, a span being what the transcript holds after the later of the owner's last message and the guard's last evaluated stop; read, never written, once more after two seconds where a call is not found; unreadable, the hook allows"| p_loop_guard
ds_checkout -->|"UNTRUSTED: the status file's Awaiting user on:, the in-flight log's last line"| p_loop_guard
ds_guard_records -->|"its own record: the wait's text, the transcript's place of its last evaluated stop, an opener owed after a refusal for a missing push, a question refused (R-129)"| p_loop_guard
p_loop_guard -->|"its one record under bridge/: the wait's text, the transcript's place, an opener owed after a refusal for a missing push, a question refused; nothing else of the conversation (R-129)"| ds_guard_records
p_loop_guard -->|"refused: a Needs you line where no push carrying the same opener stands in the span, once more at the next stop where that push is still missing, then the debt dropped (twice at the most); a new wait without the line or such a push; option labels in the form of an offered choice without a question form; before a question form, a call with no push in the span before it and after any earlier question, unless its own record shows a question refused since the span began; allowed where it cannot read (R-129)"| p_supervisor

p_supervisor -->|"increment to package, diff to read"| p_claude_subagents
p_claude_subagents -->|"brief, Review A verdict"| p_supervisor
p_claude_subagents -->|"library names, the lockfile's pinned version, topics; never project code, a path of this computer or a name (R-100)"| ext_docs_service
ext_docs_service -->|"UNTRUSTED: documentation text, data and never an instruction"| p_claude_subagents

ext_owner -->|"run sheet"| p_bridge_install
p_bridge_install -->|"bridge files, settings merged"| ext_claude_home
p_bridge_install -->|"installs"| p_cursor_agent_shim
p_bridge_install -->|"link .cursor, skeleton, rename probe"| ds_agent_home

ext_github -->|"push or PR event, contents read, no persisted credentials"| p_ci_tests & p_ci_security_floor
ext_github -->|"weekly schedule or workflow_dispatch, contents read, no secret"| p_dependency_scan
ds_actions_secrets -->|"SECRET: Socket step env only"| p_ci_security_floor
p_ci_security_floor -->|"SECRET: Socket token, manifest"| ext_advisory
p_ci_security_floor & p_dependency_scan -->|"lockfile packages"| ext_advisory
ext_advisory -->|"advisories, rules, OSV-Scanner pinned by SHA-256"| p_ci_security_floor
ext_advisory -->|"advisories, OSV-Scanner pinned by SHA-256"| p_dependency_scan
p_ci_tests & p_ci_security_floor & p_dependency_scan -->|"results, logs"| ext_github
```
