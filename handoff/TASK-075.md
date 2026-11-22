---
record: brief
header: 1
id: "TASK-075"
round: 1
satisfies: [R-095]
scope: ["bridge/cursor-bridge/roster-check.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_program_roster_sign_in.py", "tests/test_roster_check.py", "tests/test_roster_check_a4.py", "tests/fixtures/cursor/", "docs/BUILDER_NOTES.md", "handoff/TASK-075-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-075: A signed-out Cursor tool is told from a failing model (R-095)

## Objective
`bridge/cursor-bridge/roster-check.py` decides which models fill the builder and Review B roles. It probes each candidate model through `cursor-agent -p -f --model <id> <prompt>`, and its `--record-failure <model>` mode classifies a failed `cursor-agent` call and counts failures against the model or its pool. Today, when the Cursor command-line tool itself is signed out, every call prints the tool's own sign-in line, and roster-check takes that for a failure of the model: the probe skips the profile and tries the next one, and `--record-failure` counts a failure, then marks the model unavailable or the pool exhausted on the second one (the origin is ISS-020, met on 2026-10-30). No switch of model helps a signed-out tool. After this increment, roster-check recognises the tool's own sign-in line, as the tool prints it and never by a model's words, in the probe and in `--record-failure`; it then prints exactly `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, counts no failure against any model or pool, writes nothing, resolves no profile, and ends with exit 5. Every other failure is classified and counted exactly as today.

Satisfies: R-095 - A signed-out Cursor tool is told from a failing model (C3): `roster-check.py`, in its probe and in `--record-failure`, knows the tool's own sign-in line, prints `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, counts no failure against a model or a pool and ends with exit 5; calibration's install run sheet ends with `cursor-agent status`, in the owner's terminal. (Its row in `docs/REQUIREMENTS.md` is line 121. The run sheet's `cursor-agent status` line is instruction text that the supervisor writes in TASK-078. It is not this increment's work, and you touch no run sheet.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_program_roster_sign_in.py
- tests/test_roster_check.py
- tests/test_roster_check_a4.py
- tests/fixtures/cursor/
- docs/BUILDER_NOTES.md
- handoff/TASK-075-r1-report.md

Limits on these paths:
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), never by hand. Their diff may touch only the `roster-check.py` entry.
- `tests/test_program_roster_sign_in.py` is the supervisor's acceptance file, committed at HEAD. It is **read-only** for you: read it whole and run it, but never edit it. If a case seems wrong, stop and report it by its test id.
- `tests/fixtures/cursor/sign-in-required.txt` is the supervisor's recorded fixture. It is **read-only** for you. You need no other fixture. If you add one, it holds no account name, e-mail address, user name or path of this computer. The same holds for everything you write anywhere.
- `tests/test_roster_check.py` and `tests/test_roster_check_a4.py`: every existing case must pass **unedited**. The one edit allowed is appending cases of your own at the very end of a file, below a line you add, `# ---- builder's cases below this line (R-095)`, each case naming R-095 in its name or docstring. None is required (see the mutation self-check, M1).

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration (`.github/`)
- docs/ and handoff/, except the files the Scope section names
- `bridge/cursor-bridge/bridge_env.py`, `bridge/cursor-bridge/VERSION` (make-manifest rewrites it, and its content must not change: Done), `bridge/cursor-bridge/CHANGELOG.md` (this increment adds no CHANGELOG entry), and every other file under `bridge/`
- every file under `tools/` (you run `make-manifest.py` and `dump-cli.py`, and edit neither)
- every test file other than the two named for appended cases; `tests/test_program_roster_sign_in.py` included (read-only)
- calibration's install run sheet and every other instruction text (TASK-078, the supervisor's)
- any mutation script or mutants file: the mutation run is the supervisor's, after your run
- the real `cursor-agent`: you never run it, never run `cursor-agent login`, `logout` or `status`, and never sign anything in or out
- `~/.claude`, `~/.cursor-bridge`, and any real installation or real roster state

## Context
**The design that binds this increment.** `docs/DESIGN.md` line 364, the bullet `*C3.*`: "`roster-check.py` knows a signed-out tool by the tool's own line: in the probe and in `--record-failure` it prints `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, counts no failure against a model or a pool, and ends with exit 5." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-075` (line 1947), whose `Done when` (line 1956) reads: "`roster-check.py` knows the Cursor tool's own sign-in line, matched as the tool prints it and never by a model's words, in the probe's two shapes (a non-zero exit, and exit 0 with the line on standard output) and in `--record-failure`'s reading of an error file; it then prints `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, writes no failure against a model or a pool (the state file byte-identical, a test), resolves no other profile, and ends with exit 5; every other failure is counted as today, the existing tests green unedited; the docstring's exit list names exit 5 and the reference is regenerated where the help text changed; ... MANIFEST regenerated; no option added; no new dependency."

**The tool's own sign-in line**, as the tool printed it in the run that met it. It is recorded in `tests/fixtures/cursor/sign-in-required.txt` (one line, ASCII, ending in a line break):

```
Error: Authentication required. Please run 'agent login' first, or set CURSOR_API_KEY environment variable.
```

`CURSOR_API_KEY` here is only a name in the tool's message. This increment reads no key and no environment variable.

**`bridge/cursor-bridge/roster-check.py` as it stands** (609 lines, CRLF line endings in this checkout; read it whole):
- Module docstring lines 2-65. The `--record-failure` paragraph is lines 38-50. The exit list is lines 61-63: `Exit 0 = resolved; 1 = no usable profile, a family collision, or a command mismatch;` / `2 = cannot read or a wrong model argument; 3 = pool/model marked exhausted, re-resolve;` / `4 = transient, retry once; 5 = repeated connection failures or time-outs, tell the owner.` `tools/dump-cli.py` records this program's usage from that docstring, verbatim (`docs/cli-reference.json` line 1178; `docs/CLI_REFERENCE.md` line 997 holds the exit list's last line). Line 40 of the docstring says "within 2 hours" while `FAILURE_WINDOW_HOURS = 8` (line 78). That is not this increment's to fix: leave it as it is and mention it in the report.
- `NO_WINDOW` (line 77), `PROBE_PROMPT` (line 87), `PROBE_TIMEOUT = 150` (line 88).
- `def probe(model_id):` (lines 177-205) returns `(ok, detail)`. It runs `launcher + ["-p", "-f", "--model", model_id, PROBE_PROMPT]` with `capture_output=True, text=True, timeout=PROBE_TIMEOUT, creationflags=NO_WINDOW, env=env` (lines 190-192). An exit 0 with `OK` is answered (line 198). An exit 0 with other text that `classify_failure` calls `OTHER` and that holds none of the words of lines 201-202 (`error`, `failed`, `unauthori[sz]ed`, ...) is "answered off-script" (lines 200-203). Everything else is not ok (lines 204-205). Today the sign-in line on stdout with exit 0 is therefore not ok (it holds `Error`), and the profile is skipped.
- `def classify_failure(text):` (lines 331-340) returns `USAGE-LIMIT`, `CONNECTION` or `OTHER`. The sign-in line matches no pattern today, so it is `OTHER`.
- `def record_failure(path, roster, model, text):` (lines 375-436) first refuses a model id outside the roster with exit 2, changing nothing (lines 379-382). It then classifies, counts and calls `save_state` (lines 396 and 435). A first `OTHER` failure is exit 4. A second one inside `FAILURE_WINDOW_HOURS` marks the model unavailable (native pool) or the other pool exhausted, and that is exit 3.
- `main()` (lines 439-602): `load_roster(path)` (line 450) writes the state file only where none exists. The `--record-failure` branch (lines 467-476) reads `--stderr-file` and then `--stdout-file`, each with `encoding="utf-8", errors="replace"`, joins them with line breaks, and calls `record_failure`. For a plain check, `maybe_auto_reset` and `expire_unavailable` run first (lines 502-506) and may write the state file. **Leave both as they are.** Then the loop over the profiles (lines 527-566) probes the builder and then Review B of each candidate (lines 552-560), and skips the profile when either is not ok. After a profile resolves, `roster["last_resolved"]` is saved to the state file (lines 589-590), and the resolved file is written when it changed (lines 591-593).
- The state file is `<git common dir>/bridge/roster-state.json` (`state_path`, lines 238-253). The tracked roster is `docs/ROSTER.json`, and the resolved file is `docs/ROSTER.resolved.json` beside it (or `--out`).
- Program conventions: ASCII-only (the docstring says so), no argparse (flags read by membership in `argv`), `main()` returns the exit code, and output lines begin with an upper-case word (`TRANSIENT`, `ESCALATE`, `RESOLVED`, `FAIL`, ...).

**The acceptance tests.** `tests/test_program_roster_sign_in.py` has 8 cases. Read it whole: its module docstring (lines 1-30) states what it pins and what it leaves open. Five cases are red at HEAD: `test_r095_probe_sign_in_line_on_stderr_with_a_non_zero_exit`, `test_r095_probe_sign_in_line_on_stdout_with_exit_0`, `test_r095_record_failure_reads_the_sign_in_line_in_a_stderr_file`, `test_r095_record_failure_reads_the_sign_in_line_in_a_stdout_file` and `test_r095_record_failure_after_a_counted_failure_marks_nothing`. Three guards are green at HEAD and must stay green: `test_r095_a_model_reply_holding_the_words_is_answered_as_today`, `test_r095_a_model_sentence_in_an_error_file_is_counted_as_today` and `test_r095_the_tools_whole_line_quoted_inside_a_model_sentence_is_counted_as_today` (an error file holding the tool's whole line after other words, inside a model's sentence, is a first failure, exit 4). Every case runs `roster-check.py` as a subprocess in a git repository under `tmp_path`, with HOME, USERPROFILE, LOCALAPPDATA and APPDATA under `tmp_path`. Its `cursor-agent` is a stand-in under `tmp_path`, placed first on PATH (a `cursor-agent.cmd` on Windows), and PATH entries that hold another `cursor-agent` are dropped, so the real tool is never run. The roster's two profiles hold only native-pool models (`composer-2.5`/`grok-4.7-high`, then `grok-4.6`/`composer-1.5`). The tests compare the state file, `docs/ROSTER.json` and `docs/ROSTER.resolved.json` byte for byte, after seeding the state file. Not pinned: the wording of any line beyond the SIGN-IN line; whether the probe stops after the builder's probe or after both of the first profile's probes; the stream that carries the SIGN-IN line.

**The existing tests that hold today's behaviour.** `tests/test_roster_check.py` (11 cases) runs rosters outside git with `--no-probe` and `--record-*` only, and never calls `cursor-agent`. Line 73 pins exit 5 with `ESCALATE` for the third connection failure. That meaning of exit 5 stays. `tests/test_roster_check_a4.py` (1 case) holds the family rule.

**External services.** The probe's call of `cursor-agent` is the only external call this program makes. This increment leaves that call unchanged: same arguments, its time limit `PROBE_TIMEOUT` 150 s, no retry. It adds no external call and no network access. The tests replay the recorded line through a stand-in. You never run the real tool. The session's `claude --version` is not used by this increment.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. Text crossing into this program here comes from two places: the output of a child process (the probe) and the files named by `--stderr-file`/`--stdout-file`. Both may hold a model's words. The boundary this increment adds is that only the tool's own line, matched as a whole line, stops the run. A model's sentence never does. No exception escapes as a traceback.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you: run `roster-check.py` only through the three test files, on their rosters under `tmp_path`. Never run it by hand against this Workspace's `docs/ROSTER.json`: that would write the real state file under `.git/bridge/` and probe the real tool. Never run the installed copy under your home folder.

**Host.** Windows 11 with the owner's Python 3.12. CI also runs on Ubuntu.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **R1. The match.** A line is the tool's sign-in line when, stripped of surrounding whitespace (spaces, tabs, CR, LF), it **begins with** the tool's own prefix `Error: Authentication required. Please run 'agent login' first`, compared exactly as printed (case included). The fixture's line therefore matches. A line that holds these words anywhere other than at its start does not match, and neither do the words `authentication required` inside a sentence. Matching the words anywhere in the text, or ignoring case, is not allowed. The text is split into lines and each line is tested on its own.
2. **R2. In the probe.** The probe of a model recognises the line on the tool's stdout or stderr, whatever its exit code. At the least it recognises the two shapes the tests pin: (a) a non-zero exit with the line on stderr, and (b) exit 0 with the line on stdout. When the line is met, roster-check prints the line `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login` (exactly so, two spaces after `SIGN-IN`, on a line of its own). It then probes no further profile and no other model's profile, prints no `RESOLVED` line, and writes nothing: no failure, no mark, no `last_resolved`, and no resolved file. The state file, `docs/ROSTER.json` and the resolved file stay byte-identical to what they were when the probe began. It ends with exit 5. Whatever runs before the probe today (the automatic reset and the expiry of unavailable marks, `main()` lines 502-506) stays as it is. Whether the second model of the first profile is still probed is up to you.
3. **R3. In `--record-failure`.** When the text read from `--stderr-file` or `--stdout-file` holds the sign-in line (R1), roster-check prints the same `SIGN-IN` line, counts no failure against the model or its pool, writes nothing (the state file and the tracked files byte-identical), and ends with exit 5. This holds also where a failure of that model is already counted inside the window. The check comes before any counting and before any `save_state` call. A wrong model argument without the line exits 2 as today. Whether a wrong model argument *with* the line gives exit 2 or the SIGN-IN line is not pinned: either way nothing is written.
4. **R4. Everything else as today.** Every other probe result and every other failure is classified, counted, printed and exited exactly as today: usage limits, connection errors, the third connection failure's exit 5 with `ESCALATE`, first and second other failures, and an off-script answer. Both guard cases stay green. Every existing case of `tests/test_roster_check.py` and `tests/test_roster_check_a4.py` passes unedited.
5. **R5. The docstring and the reference.** The module docstring's exit list names exit 5 for a signed-out tool as well, beside its present meaning (repeated connection failures or time-outs, tell the owner), for example `5 = repeated connection failures or time-outs, or the Cursor tool signed out (SIGN-IN), tell the owner.` One short sentence in the `--record-failure` paragraph or the probe paragraph saying the same is allowed. Everything is ASCII. Nothing else in the docstring changes. Regenerate the command reference with `python tools/dump-cli.py` (Done). After that, `python tools/dump-cli.py --check` exits 0, and the reference diff touches only the `roster-check.py` entry.
6. **R6. No new surface.** No option, flag, environment variable, configuration key or dependency is added. There is no network call and no new process: the probe's one call is unchanged (R2). The program stays ASCII-only. No path of this computer and no account name appears in any program, test, fixture, message, note or report.
7. **R7. The manifest.** `bridge/cursor-bridge/MANIFEST.json` is regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`. The version stays `2026.11.12a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, and what `bridge/cursor-bridge/VERSION` holds), and `git diff -- bridge/cursor-bridge/VERSION` shows nothing. `make-manifest.py` keeps the file's line ending since TASK-074.
8. **R8. Line endings.** `roster-check.py` keeps its CRLF line endings. Do not convert the file.

## Acceptance criteria
- [ ] `tests/test_program_roster_sign_in.py` passes whole, unedited (8 cases).
- [ ] `tests/test_roster_check.py` and `tests/test_roster_check_a4.py` pass, every existing case unedited. Any case you added sits below the marker line and names R-095.
- [ ] The sign-in line is matched as R1 states, and never by a model's words (both guards green).
- [ ] Probe, both shapes: the `SIGN-IN` line, exit 5, no second profile probed, nothing written (R2).
- [ ] `--record-failure` with the line in either file: the `SIGN-IN` line, exit 5, nothing counted or written, including after a counted failure (R3).
- [ ] Every other failure is counted as today (R4).
- [ ] The docstring's exit list names exit 5 for a signed-out tool. `python tools/dump-cli.py --check` exits 0, and the reference diff touches only the `roster-check.py` entry (R5).
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`, run from the Workspace root, exits 0 and prints `RESULT: SOURCES MATCH bridge 2026.11.12a` (with the folder after it). `git diff -- bridge/cursor-bridge/VERSION` is empty (R7).
- [ ] `roster-check.py` decodes as ASCII and keeps CRLF (R6, R8).
- [ ] R-095's program part is fully met, with no stand-in, placeholder or "later" text. The tests naming R-095 are the supervisor's acceptance tests, plus any case you add.
- [ ] No option, dependency, configuration key or environment variable is added. There is no network call, no new Semgrep high finding, and no traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used, nothing else).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_roster_sign_in.py`, `tests/fixtures/cursor/sign-in-required.txt`, any existing case of `tests/test_roster_check.py` or `tests/test_roster_check_a4.py`, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, tests, the notes line, the report) holds a path of this computer, a user name or an account name. In the report, write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output (the bridge-check command prints the resolved folder: write `<Workspace>/bridge/cursor-bridge` in the quote).
- This increment talks to one external service, the Cursor command-line tool, through the probe's existing call. Its tests replay the **recorded real line** in `tests/fixtures/cursor/sign-in-required.txt`. Do not invent another shape of the tool's output. If you believe a fixture you need is missing, stop and report it, because that is a capture the supervisor must run. Never run the real `cursor-agent`, never sign it in or out, and add no call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; the program's `NO_WINDOW`). This increment needs no new process. The probe's existing call already passes `creationflags=NO_WINDOW`, and must keep doing so.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong. In `roster-check.py`, change only what R1-R8 need. Every other message, classification, refusal and exit code stays as it is.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"). `roster-check.py` runs only through the three test files.
- A value the brief marks as the owner's: none in this increment. The `SIGN-IN` line's wording and exit 5 are fixed by R-095 and `docs/DESIGN.md` C3, and the acceptance file pins them. Do not change either.
- Follow existing conventions in the files you touch: ASCII program text, CRLF in `roster-check.py`, flags read by membership in `argv` (no argparse; `tools/dump-cli.py` reads this program's docstring), and `main()` returning the exit code.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `restore`. You read with `git status`, `git diff`, `git log` and `git rev-parse` only.
- Numbers: this increment parses none.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). The whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutation run comes after yours. Before you finish, apply each of these mutants by hand, one at a time, to `roster-check.py`, keeping its CRLF line endings. For each mutant: apply it; run `python tools/make-manifest.py`; run `python -m pytest -p no:cacheprovider -q tests/test_program_roster_sign_in.py tests/test_roster_check.py tests/test_roster_check_a4.py`; revert the mutant by hand (never with git); run `python tools/make-manifest.py` again; and confirm with `git diff -- bridge/cursor-bridge/roster-check.py` that the file is back to your finished version. In the report, list each mutant by its label and text. For each, quote the exact code you changed in a fenced block (before and after), then the pytest summary line in a fenced block, then the id of one test it made fail. If a mutant is not caught, write `not caught` and one line on the case that would catch it:
  - M1 the sign-in line is matched anywhere in the text instead of as a whole line (R1).
  - M2 the probe's stdout shape is not checked (only stderr is read for the line).
  - M3 `--record-failure` counts (and saves) the failure before the sign-in check.
  - M4 the sign-in exit is 1 instead of 5.
  M1 is caught by the third guard, `test_r095_the_tools_whole_line_quoted_inside_a_model_sentence_is_counted_as_today`.
- **Known failures.** Five acceptance cases fail before your change (Context). If a case of the three test files fails that your change did not cause, report it by its test id with its failure lines, and fix none.
- Prefer reuse over new code: the existing `probe`, `record_failure` and `main` structure, `NO_WINDOW`, and the standard library. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-075-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name. Write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created;
- a one-paragraph summary of what you did;
- for R1-R8, one line each on what meets it, naming the functions and their lines as the file stands after your change. For R1, also the exact match (the prefix and how a line is stripped). For R2, also whether the probe stops after the first model or after both of the first profile's models;
- any case you added to the two existing test files, by test id;
- the mutation self-check list, M1-M4, each with its code before and after, its pytest summary line and the test id that caught it (or `not caught` and the case that would);
- every command of the list below, with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: that a later version of the tool keeps the prefix `Error: Authentication required. Please run 'agent login' first`; that the real tool, signed out, prints the line on stdout with exit 0 in `-p` mode as well as on stderr; that a real error file written by the launcher holds the line at the start of a line. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py` (expect `make-manifest: version 2026.11.12a, ...`)
3. `python tools/dump-cli.py`
4. `python -m pytest -p no:cacheprovider -q tests/test_program_roster_sign_in.py tests/test_roster_check.py tests/test_roster_check_a4.py`
5. `python tools/dump-cli.py --check` (expect exit 0; quote its output and its exit code)
6. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it, exit 0)
7. `python -c "open('bridge/cursor-bridge/roster-check.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
8. `python -c "d=open('bridge/cursor-bridge/roster-check.py','rb').read(); print('bare LF', d.count(b'\n')-d.count(b'\r\n'))"` (expect `bare LF 0`)
9. `git diff -- bridge/cursor-bridge/VERSION` (expect no output)
10. `git diff --stat` (expect only the Scope's files; the reference diff only in the `roster-check.py` entry)
11. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it and do not restore it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 11, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
