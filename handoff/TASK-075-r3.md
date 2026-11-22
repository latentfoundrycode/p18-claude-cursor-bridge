---
record: brief
header: 1
id: "TASK-075"
round: 3
satisfies: [R-095]
scope: ["bridge/cursor-bridge/roster-check.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-075-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-075 round 3: a reply that is not the tool's line is judged as before round 1 (R-095)

Round cause: brief error

## Objective
`bridge/cursor-bridge/roster-check.py` recognises the Cursor command-line tool's own sign-in line in its probe and in `--record-failure`, prints `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, writes nothing and exits 5. Rounds 1 and 2 built this. Round 2 is committed on branch `task-075`: its brief is `handoff/TASK-075-r2.md`, its report `handoff/TASK-075-r2-report.md`, and its code diff is `git diff d8b9739..HEAD~1 -- bridge/cursor-bridge/roster-check.py`. Both reviews of round 2 rejected it for one blocking finding, and the fault was the brief's, not the builder's.

The round-2 brief's R2, and the supervisor's case beside it, said that a model's reply quoting the tool's line on a line of its own was "answered off-script ... as before round 1". The code before round 1 (commit `6a1434d`) never answered such a reply: its error-word check matches the line's own word `Error`, so that reply was no answer. To pass that case, round 2 added `_stdout_for_probe_errors` and the variable `err_probe`, which remove the lines beginning with the tool's prefix before the error-word check. As a result, a signed-out tool that prints one more line on standard output resolves a usable profile, and the check fails open. A banner before its line, or words after it, is enough.

The supervisor has corrected the case in `tests/test_program_roster_sign_in.py` (committed at HEAD). This round removes that change, and nothing else. Every reply that is not the tool's line is judged exactly as at `6a1434d`. Everything else round 2 built stays.

Satisfies: R-095 - A signed-out Cursor tool is told from a failing model (C3): `roster-check.py`, in its probe and in `--record-failure`, knows the tool's own sign-in line, prints `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, counts no failure against a model or a pool and ends with exit 5; calibration's install run sheet ends with `cursor-agent status`, in the owner's terminal. (Its row in `docs/REQUIREMENTS.md` is line 121. The run sheet's `cursor-agent status` line is the supervisor's, in TASK-078. It is not this increment's work.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-075-r3-report.md

Limits on these paths:
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py`, and only if the docstring changed. None is expected, so these two files are expected to stay unchanged (Done, step 4).
- `docs/BUILDER_NOTES.md`: append dated lines only (Constraints).

Do not modify anything else. No test file is yours to edit in this round.

## Out of scope
- .env and anything under secrets/
- CI configuration (`.github/`)
- docs/ and handoff/, except the files the Scope section names
- every test file and fixture. These are read-only: `tests/test_program_roster_sign_in.py` (the supervisor's, 25 cases), `tests/fixtures/cursor/sign-in-required.txt`, `tests/test_roster_check.py`, `tests/test_roster_check_a4.py` and `tests/test_hotfix25a_roster_launcher.py`.
- `bridge/cursor-bridge/bridge_env.py`, `bridge/cursor-bridge/VERSION` (make-manifest rewrites it, and its content must not change), `bridge/cursor-bridge/CHANGELOG.md`, and every other file under `bridge/`
- every file under `tools/`
- any mutation script or mutants file: the mutation run is the supervisor's, after your run
- the real `cursor-agent`. You never run it, never run `cursor-agent login`, `logout` or `status`, and never sign anything in or out.
- `~/.claude`, `~/.cursor-bridge`, and any real installation or real roster state

## Context
**The design that binds this increment.** `docs/DESIGN.md` line 364, the bullet `*C3.*`: "`roster-check.py` knows a signed-out tool by the tool's own line: in the probe and in `--record-failure` it prints `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, counts no failure against a model or a pool, and ends with exit 5." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-075` (line 1947); its `Done when` (line 1956) says the line is "matched as the tool prints it and never by a model's words".

**The tool's own sign-in line**, recorded in `tests/fixtures/cursor/sign-in-required.txt` (one ASCII line):

```
Error: Authentication required. Please run 'agent login' first, or set CURSOR_API_KEY environment variable.
```

`CURSOR_API_KEY` is only a name in the tool's message. This increment reads no key and no environment variable.

**The rule, as it now stands** (this round changes none of it):
- On standard output, the tool's line counts only when it is the whole of that output: after the split and trim, exactly one line is non-empty, and it begins with `SIGN_IN_PREFIX`. Standard output means the probe's stdout and the `--stdout-file` text.
- On standard error, any line that begins with `SIGN_IN_PREFIX` after trimming counts. Standard error means the probe's stderr and the `--stderr-file` text.
- Lines are split at the line feed alone, and trimmed of space, tab, CR and LF alone.
- A reply that is not the tool's line by this rule is judged exactly as at `6a1434d`. A reply that holds the tool's line beside any other stdout line is therefore no answer, because of its word `Error`, and the profile is skipped. This is the correction of round 2's R2.

**`bridge/cursor-bridge/roster-check.py` at HEAD** (CRLF line endings; read it whole):
- **Constants.** `SIGN_IN_PREFIX` and `SIGN_IN_LINE` are at lines 91-92. `class _ProbeSignInSentinel` (lines 95-101) has `__bool__` returning `False`, and `PROBE_SIGN_IN = _ProbeSignInSentinel()` is at line 104. `_TRIM_EDGES = " \t\r\n"` is at line 193.
- **Line helpers.** `_lf_lines` (196-199), `_trim_line_edges` (202-203), `_line_starts_with_sign_in` (206-207), `tool_sign_in_on_stderr` (210-215) and `tool_sign_in_on_stdout` (218-221). Line 220 trims each line twice: `non_empty = [_trim_line_edges(line) for line in _lf_lines(text) if _trim_line_edges(line)]`. `_ascii_line` is at lines 224-225.
- **Round 2's fail-open change, to be removed.** `def _stdout_for_probe_errors(out):` (lines 228-235). In `probe`, line 264 is `err_probe = _stdout_for_probe_errors(out)`, and the error-word `re.search` (lines 265-267) runs on `err_probe`.
- **`probe` at `6a1434d`.** That same `re.search` ran on `out`:

  ```
      if (p.returncode == 0 and out and classify_failure(out + " " + (p.stderr or ""))[0] == "OTHER"
              and not re.search(r"(?i)\b(error|exception|failed|failure|traceback|unavailable|not available|denied|unauthori[sz]ed|forbidden"
                                r"|invalid|not found|unknown model|cannot use|not supported)\b", out)):
  ```

- **`probe` at HEAD otherwise** (lines 238-270). It returns `PROBE_SIGN_IN, ""` when `tool_sign_in_on_stdout(p.stdout or "") or tool_sign_in_on_stderr(p.stderr or "")` (lines 259-260). It decodes output with `encoding="utf-8", errors="replace"` (line 253). Its detail strings use `%a` (lines 268 and 270). All of that stays.
- **`record_failure(path, roster, model, stderr_text="", stdout_text="")`** (from line 440) and the `--record-failure` branch of `main()` (from line 537) read the two files apart. They are not touched in this round.

**The acceptance tests.** `tests/test_program_roster_sign_in.py` has 25 cases; read it whole. Three are red on round 2, and all three are killed by the fail-open change:
- `test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_judged_as_before_round_1` (line 305; corrected from round 2's `..._is_answered_as_today`);
- `test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer[banner-first]`;
- `test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer[line-first]` (line 316).

Each of the three expects exit 1, no `SIGN-IN` and no `RESOLVED` line, no probe line saying `answered`, and both of the second profile's models probed (`assert_judged_as_before_round_1`, lines 295-302).

The other 22 are green on round 2 and must stay green. Among them, `test_r095_r3_probe_returns_a_falsy_signed_out_result_in_its_pair` (line 326) calls `probe` directly with a patched `subprocess` and checks the pair, the identity and the falsiness.

**Other tests that hold this program.** `tests/test_roster_check.py`, `tests/test_roster_check_a4.py` and `tests/test_hotfix25a_roster_launcher.py`. The last unpacks `probe`'s pair (lines 83 and 92).

**External services.** The probe's call of `cursor-agent` is the only external call; it is unchanged (same arguments, `PROBE_TIMEOUT` 150 s, no retry). This round adds no external call and no network access. The tests replay the recorded line through a stand-in under `tmp_path`. You never run the real tool. The session's `claude --version` is not used.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. Untrusted text comes from the probe child's stdout and stderr and from the `--stderr-file`/`--stdout-file` files. The boundary this round restores is that output from a signed-out tool, or a model's words, never makes a profile usable that the code at `6a1434d` would have skipped. Fail closed. No exception escapes as a traceback.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you, this means three things:
- Run `roster-check.py` only through the test files named in Done.
- Never run it by hand against this Workspace's `docs/ROSTER.json`.
- Never run the installed copy.

**Host.** Windows 11 with the owner's Python 3.12, console code page cp1252. CI also runs on Ubuntu.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **R1. The fail-open change removed.** `_stdout_for_probe_errors` and `err_probe` are gone from the file. The error-word `re.search` in `probe` runs on `out` again, exactly as at `6a1434d` (quoted in Context). After `probe`'s sign-in check, every reply is judged exactly as at `6a1434d`, except for round 2's UTF-8 decoding and its `%a` in the detail strings.
2. **R2. Everything else stays.** Round 2's code stays as it is:
   - the stream rule (`tool_sign_in_on_stdout`, `tool_sign_in_on_stderr`);
   - the LF-only split and the trim of space, tab, CR and LF;
   - `PROBE_SIGN_IN` (falsy, returned in `probe`'s pair, tested by identity in `main()`);
   - the UTF-8 read;
   - `%a` and `_ascii_line` for the excerpts;
   - the two-file reading of `--record-failure`;
   - the docstring.
3. **R3. Optional tidy.** In `tool_sign_in_on_stdout`, each line may be trimmed once instead of twice, if behaviour is unchanged. No other tidy, rename or refactor.
4. **R4. The tree.** `roster-check.py` stays ASCII-only with CRLF line endings. `MANIFEST.json` is regenerated with `python tools/make-manifest.py` after your last edit; the version stays `2026.11.12a`, and `git diff -- bridge/cursor-bridge/VERSION` shows nothing. `python tools/dump-cli.py --check` exits 0, and the reference files stay unchanged.

## Acceptance criteria
- [ ] `tests/test_program_roster_sign_in.py` passes whole, unedited (25 cases).
- [ ] `tests/test_roster_check.py`, `tests/test_roster_check_a4.py` and `tests/test_hotfix25a_roster_launcher.py` pass unedited.
- [ ] `git diff d8b9739 -- bridge/cursor-bridge/roster-check.py` holds no `_stdout_for_probe_errors` and no `err_probe`, and its `re.search` hunk, if any, shows the search on `out` (R1).
- [ ] `python tools/dump-cli.py --check` exits 0.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`, run from the Workspace root, exits 0 and prints `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it.
- [ ] `git diff -- bridge/cursor-bridge/VERSION` is empty.
- [ ] `roster-check.py` decodes as ASCII and has no bare LF (R4).
- [ ] R-095's program part stays fully met, with no stand-in, placeholder or "later" text.
- [ ] No option, dependency, configuration key or environment variable is added. There is no new external call, no new Semgrep high finding, and no traceback (ASVS L2).

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit any test file or fixture. **If a test case seems wrong, stop and report it by its test id. Never work around it in the code.** Round 2's fail-open change came from working around a wrong case.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write holds a path of this computer, a user name or an account name. In the report, write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- This increment talks to one external service, the Cursor command-line tool, through the probe's existing call. The tests replay the **recorded real line** in `tests/fixtures/cursor/sign-in-required.txt`. Do not invent another shape of the tool's output. If you believe a fixture you need is missing, stop and report it. Never run the real `cursor-agent`, and add no call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` elsewhere; the program's `NO_WINDOW`). No new process is needed. The probe's call keeps `creationflags=NO_WINDOW`.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong. Change only what R1 and R3 name.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- A value the brief marks as the owner's: none. The `SIGN-IN` line's wording and exit 5 are fixed by R-095 and `docs/DESIGN.md` C3, and the tests pin them.
- Follow existing conventions in the files you touch: ASCII program text, CRLF in `roster-check.py`, no argparse.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `restore`. You read with `git status`, `git diff`, `git show`, `git log` and `git rev-parse` only.
- Numbers: this increment parses none.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it); the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutation run comes after yours. Apply each mutant below by hand, one at a time, to your finished `roster-check.py`, keeping CRLF. For each one:
  1. Apply the mutant.
  2. Run `python tools/make-manifest.py`.
  3. Run `python -m pytest -p no:cacheprovider -q tests/test_program_roster_sign_in.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_hotfix25a_roster_launcher.py`.
  4. Revert the mutant by hand, never with git.
  5. Run `python tools/make-manifest.py` again.
  6. Confirm with `git diff -- bridge/cursor-bridge/roster-check.py` that the file is back to your finished version.

  In the report, list each mutant by its label and text, with:
  - the code before and after, **whole**, every changed line written out, never elided with `...` or a comment, each in a fenced block;
  - the pytest output's `FAILED` lines and summary line, verbatim, in a fenced block;
  - the id of one test it made fail.

  If a mutant is not caught, write `not caught` and one line on the case that would catch it. You add no case. The mutants:
  - N1 the stdout whole-output rule dropped: a line-start match anywhere on stdout counts, as on stderr.
  - N2 `str.splitlines()` and bare `strip()` again in the line helpers.
  - N3 no UTF-8 decoding on the probe (no `encoding`/`errors` on its `subprocess.run`).
  - N4 `%r` again in the probe's detail strings, and the excerpt printed raw (without `_ascii_line`). Run step 3 **twice** for N4 and quote both runs, each labelled: first `N4 default`, as written; then `N4 PYTHONIOENCODING=utf-8`, with the environment variable `PYTHONIOENCODING` set to `utf-8` for that one command only and removed after it.
  - N5 `PROBE_SIGN_IN` made truthy (for example `PROBE_SIGN_IN = object()`).
  - N6 round 2's change put back: the error-word `re.search` run on stdout with the lines beginning with the tool's prefix removed.
- **Known failures.** Three cases fail on round 2 (Context). If a case of the four test files fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code (the frozen `minimal-code.mdc` is in force). This round mostly deletes code.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-075-r3-report.md`. Create it at the start and write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output. The file must exist before step 1 below, so that `git status --short` lists it.

When you finish, it holds:
- a list of every file you changed or created;
- a one-paragraph summary of what you did;
- for R1-R4, one line each on what meets it, naming the functions and their lines as the file stands after your change. Each line describes the code as it is, truthfully; if you took R3's tidy, say so, and if you did not, say that;
- the mutation self-check list, N1-N6, as Constraints asks;
- every command of the list below, with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: that a signed-out tool prints nothing else on standard output; that a real model never replies with the tool's line alone. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

**Every quoted output comes from the final tree.** Run the list below after your last edit to `roster-check.py` and after the mutation self-check, and quote only those runs for it. Never quote output from an earlier state of the files. The mutation runs are the one exception: quote each as its mutant ran.

Run these from the Workspace root, in this order, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short` (it lists `handoff/TASK-075-r3-report.md`)
2. `python tools/make-manifest.py` (expect `make-manifest: version 2026.11.12a, ...`)
3. `python -m pytest -p no:cacheprovider -q tests/test_program_roster_sign_in.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_hotfix25a_roster_launcher.py`
4. `python tools/dump-cli.py --check` (expect exit 0; quote its output and its exit code. If it reports the reference stale, run `python tools/dump-cli.py`, then `python tools/dump-cli.py --check` again, quote both, and say why the docstring changed.)
5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it, exit 0)
6. `python -c "open('bridge/cursor-bridge/roster-check.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
7. `python -c "d=open('bridge/cursor-bridge/roster-check.py','rb').read(); print('bare LF', d.count(b'\n')-d.count(b'\r\n'))"` (expect `bare LF 0`)
8. `git diff -- bridge/cursor-bridge/VERSION` (expect no output)
9. `git diff d8b9739 -- bridge/cursor-bridge/roster-check.py` (quote it whole; it holds no `_stdout_for_probe_errors` and no `err_probe`)
10. `git diff --stat`
11. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it and do not restore it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose: not in the summary, not in the R lines, not anywhere.
- A claim that a check passed quotes the output line that shows it.
- Each mutation is listed by its label and text, with its whole before and after code and what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 11, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
