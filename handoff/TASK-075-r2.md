---
record: brief
header: 1
id: "TASK-075"
round: 2
satisfies: [R-095]
scope: ["bridge/cursor-bridge/roster-check.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-075-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-075 round 2: the tool's line read by its stream, the docstring restored, the probe's result unmistakable (R-095)

Round cause: defect

## Objective
Round 1 is committed on branch `task-075` (its brief is `handoff/TASK-075.md`, its report `handoff/TASK-075-r1-report.md`, its code diff `git diff 6a1434d..HEAD -- bridge/cursor-bridge/roster-check.py`). It taught `bridge/cursor-bridge/roster-check.py` to recognise the Cursor command-line tool's own sign-in line in the probe and in `--record-failure`. On that line the program prints `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, writes nothing and exits 5.

Round 1's reviews found five problems:
- It broke the module docstring.
- It matches the line at the start of any line on standard output, so a model's reply that quotes the line on a line of its own is taken for the tool's.
- It splits lines with `str.splitlines()` and trims with bare `strip()`, so separators other than the line feed start or trim a line.
- Its probe returns a truthy `object()` as `ok` for a signed-out tool.
- The probe reads the tool's output in the console's code page, and prints replies with `%r`, which can hold characters outside ASCII.

This round repairs those findings and nothing else. Everything round 1 achieved stays: the 8 round-1 cases of `tests/test_program_roster_sign_in.py` pass on round 1 and must still pass.

Satisfies: R-095 - A signed-out Cursor tool is told from a failing model (C3): `roster-check.py`, in its probe and in `--record-failure`, knows the tool's own sign-in line, prints `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, counts no failure against a model or a pool and ends with exit 5; calibration's install run sheet ends with `cursor-agent status`, in the owner's terminal. (Its row in `docs/REQUIREMENTS.md` is line 121. The supervisor writes the run sheet's `cursor-agent status` line in TASK-078. It is not this increment's work.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-075-r2-report.md

Limits on these paths:
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), never by hand. Their diff may touch only the `roster-check.py` entry.
- `docs/BUILDER_NOTES.md`: append dated lines only (Constraints).

Do not modify anything else. In particular, no test file is yours to edit in this round.

## Out of scope
- .env and anything under secrets/
- CI configuration (`.github/`)
- docs/ and handoff/, except the files the Scope section names
- every test file and fixture: `tests/test_program_roster_sign_in.py` (the supervisor's, 22 cases), `tests/fixtures/cursor/sign-in-required.txt` (the supervisor's recorded line), `tests/test_roster_check.py`, `tests/test_roster_check_a4.py` and `tests/test_hotfix25a_roster_launcher.py` are read-only for you
- `bridge/cursor-bridge/bridge_env.py`, `bridge/cursor-bridge/VERSION` (make-manifest rewrites it, and its content must not change), `bridge/cursor-bridge/CHANGELOG.md`, and every other file under `bridge/`
- every file under `tools/` (you run `make-manifest.py` and `dump-cli.py`, and edit neither)
- any mutation script or mutants file: the mutation run is the supervisor's, after your run
- the real `cursor-agent`: you never run it, never run `cursor-agent login`, `logout` or `status`, and never sign anything in or out
- `~/.claude`, `~/.cursor-bridge`, and any real installation or real roster state

## Context
**The design that binds this increment.** `docs/DESIGN.md` line 364, the bullet `*C3.*`: "`roster-check.py` knows a signed-out tool by the tool's own line: in the probe and in `--record-failure` it prints `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`, counts no failure against a model or a pool, and ends with exit 5." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-075` (line 1947). Its `Done when` (line 1956) says the line is "matched as the tool prints it and never by a model's words".

**The tool's own sign-in line**, recorded in `tests/fixtures/cursor/sign-in-required.txt` (one ASCII line):

```
Error: Authentication required. Please run 'agent login' first, or set CURSOR_API_KEY environment variable.
```

`CURSOR_API_KEY` is only a name in the tool's message. This increment reads no key and no environment variable.

**`bridge/cursor-bridge/roster-check.py` as round 1 left it** (634 lines, CRLF line endings; read it whole):
- **The docstring, lines 24-33.** Round 1 broke the paragraph. Line 25 now begins with two stray spaces (`  one-word request through ...`). Line 27's `The chosen` moved, and line 29 holds `The chosen` alone. Before round 1, the paragraph's lines read exactly as follows (shown by `git show 6a1434d:bridge/cursor-bridge/roster-check.py`, lines 24-28):

  ```
  pool. Unless --no-probe, the builder and Review B of a candidate profile are each sent a
  one-word request through `cursor-agent -p -f --model <id>`; a refusal, empty reply,
  usage-limit message or timeout marks the profile unusable (this catches hard failures only,
  never a nearly-empty quota); any other reply counts as answered, off-script. The chosen
  profile's three families must be distinct. The result is written to
  ```

  Line 65 holds round 1's exit-5 text: `4 = transient, retry once; 5 = repeated connection failures or time-outs, or the Cursor tool signed out (SIGN-IN), tell the owner.` That text stays. The `--record-failure` paragraph's "within 2 hours" (line 43) disagrees with `FAILURE_WINDOW_HOURS = 8`. It is not this round's to fix: leave it.
- **The constants, lines 91-93:** `SIGN_IN_PREFIX = "Error: Authentication required. Please run 'agent login' first"`, `SIGN_IN_LINE = "SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login"`, `PROBE_SIGN_IN = object()`.
- **`def tool_sign_in_line_present(text):`** (lines 182-189) loops `for line in text.splitlines():` and tests `line.strip().startswith(SIGN_IN_PREFIX)`. The same rule is used for every stream.
- **`def probe(model_id):`** (lines 192-222) returns `(ok, detail)`. It runs `subprocess.run(launcher + ["-p", "-f", "--model", model_id, PROBE_PROMPT], capture_output=True, text=True, timeout=PROBE_TIMEOUT, creationflags=NO_WINDOW, env=env)` (lines 205-207). It has no `encoding`, so the output is decoded in the locale's code page: a reply holding bytes `C3 81` raises `UnicodeDecodeError` on a cp1252 host. Lines 212-213 return `PROBE_SIGN_IN, ""` when either stream holds the line. The detail strings use `%r` on the reply: `"answered off-script: %r"` (line 220) and `"exit %d; stdout=%r; stderr=%r"` (line 222).
- **`def record_failure(path, roster, model, text):`** (lines 392-456) checks `tool_sign_in_line_present(text)` first (lines 396-398), then the model argument (lines 399-402), then classifies and counts. It prints the error text as `"           excerpt: %s" % excerpt` (lines 420, 423, 453).
- **`main()`'s `--record-failure` branch** (lines 487-496) reads `--stderr-file` and then `--stdout-file`, each with `open(..., encoding="utf-8", errors="replace").read() + "\n"`. It skips a file it cannot open, joins both into one `text`, and passes that text to `record_failure`. The probe loop (lines 572-584) tests `if ok is PROBE_SIGN_IN:`, prints the `SIGN-IN` line and returns 5 at the first signed-out probe.
- **The entry point** (lines 629-633) reconfigures stdout and stderr with `errors="backslashreplace"`.

**The acceptance tests.** `tests/test_program_roster_sign_in.py` has 22 cases. Read it whole, in particular the round-2 comment (lines 271-275).
- The 8 round-1 cases (lines 198-268) are green on round 1 and must stay green.
- The 14 cases named `test_r095_r2_*` (lines 294-380) are new. Ten of them are red on round 1:
  - `..._probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_answered_as_today`;
  - `..._record_failure_a_stdout_file_with_the_line_after_other_lines_is_counted_as_today`;
  - `..._record_failure_a_stdout_file_quoting_the_line_beside_a_model_stderr_is_counted_as_today`;
  - the five `..._record_failure_a_separator_other_than_the_line_feed_starts_no_line[vt|ff|fs|nel|ls]`;
  - `..._probe_a_reply_beyond_ascii_is_read_as_utf8`;
  - `..._probe_a_reply_beyond_the_consoles_code_page_is_answered_and_printed_in_ascii`.
- Four guards are green on round 1 and must stay green: `..._guard_a_stderr_file_with_a_launcher_line_first_is_signed_out`, `..._guard_a_stdout_file_of_the_line_alone_with_blank_lines_is_signed_out`, `..._guard_the_line_on_stderr_beside_a_model_stdout_is_signed_out` and `..._guard_the_probe_line_alone_on_stdout_with_blank_lines_is_signed_out`.

Every case runs the program as a subprocess under `tmp_path`, with a stand-in `cursor-agent` first on PATH. The real tool is never run.

**Other tests that hold this program.** `tests/test_roster_check.py` (11 cases) and `tests/test_roster_check_a4.py` (1 case) hold today's counting and the family rule. `tests/test_hotfix25a_roster_launcher.py` calls `probe` directly with a patched `subprocess` and unpacks **two** values (`ok, detail = rc.probe("grok-4.7-high")`, lines 83 and 92). Its fake `run` accepts any keyword. **`probe` must therefore keep returning a pair.**

**External services.** The probe's call of `cursor-agent` is the only external call. Its arguments stay exactly as they are. Its time limit stays `PROBE_TIMEOUT` 150 s, with no retry. This round changes only how its output is decoded (R5). It adds no external call and no network access. The tests replay the recorded line through a stand-in. You never run the real tool. The session's `claude --version` is not used.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. Untrusted text enters from the probe child's stdout and stderr and from the `--stderr-file`/`--stdout-file` files. A model's words can appear on standard output, and the boundary this round tightens is that they never pass for the tool's line there. No exception escapes as a traceback. Every line printed from that text stays ASCII.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you: run `roster-check.py` only through the test files named in Done. Never run it by hand against this Workspace's `docs/ROSTER.json`, which would write the real state file and probe the real tool. Never run the installed copy.

**Host.** Windows 11 with the owner's Python 3.12, console code page cp1252. CI also runs on Ubuntu.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **R1. The docstring restored (Must fix).** The five lines quoted in Context are again in the docstring, each byte for byte as before round 1, in that order, and adjacent. The stray spaces and the lone `The chosen` line are gone. The sign-in sentence goes on new lines of its own, directly after the line `before a snapshot leaves the tree clean.`, as these two lines:
   - `When the Cursor tool itself is signed out, its own sign-in line (the whole of standard output,`
   - `or any whole line of standard error) ends the run with SIGN-IN, exit 5, and counts no failure.`

   Compared with `git show 6a1434d:bridge/cursor-bridge/roster-check.py`, the docstring then differs only by those two added lines and line 65's exit-5 text. Then regenerate the reference with `python tools/dump-cli.py`.
2. **R2. The stream rule (Should fix).** The rule depends on the stream:
   - **Standard output:** this is the probe's stdout and the text of `--stdout-file`. Here the tool's line counts only when it is the whole of that output: after splitting and trimming (R3), exactly one line is non-empty, and that line begins with `SIGN_IN_PREFIX`.
   - **Standard error:** this is the probe's stderr and the text of `--stderr-file`. Here any line that begins with `SIGN_IN_PREFIX` after trimming counts, as in round 1.

   A model's reply that quotes the line on a line of its own after its own words is therefore answered off-script in the probe, and counted in `--record-failure`, exactly as before round 1.

   `--record-failure` reads the two files apart, so that each is judged by its own stream's rule. When neither holds the tool's line, the counting reads the same joined text as today: the `--stderr-file` text, then the `--stdout-file` text, each followed by a line feed, and a file that cannot be opened is skipped. Classification, counts, excerpts and exit codes then stay exactly as today.
3. **R3. Lines split at the line feed alone (Consider, taken).** Text is split into lines at the line feed (U+000A) alone. Each line is trimmed of space, tab, CR and LF alone. `str.splitlines()` and bare `strip()` (or `lstrip()`/`rstrip()` without arguments) are never used for this check. No vertical tab (U+000B), form feed (U+000C), file separator (U+001C), next line (U+0085), line separator (U+2028) or no-break space (U+00A0) starts, ends or trims a line. The text reaches the check as today's reads give it (see R7).
4. **R4. The probe's signed-out result (Should fix).** `probe` keeps returning a pair `(ok, detail)` (Context: `tests/test_hotfix25a_roster_launcher.py` unpacks two values). For a signed-out tool, `ok` is a module constant whose truth value is false (`bool(...)` is `False`), so any caller that tests truth treats it as not ok.
   - The constant is not `False`, `None`, `0` or a `str` (in particular, no named string constant compared by identity), so `is` tells it apart from every other value `probe` returns.
   - A comment at its definition says what it is.
   - `probe`'s docstring names it and says that a signed-out tool returns it.
   - `main()` still tests for it by identity before `if not ok`, and still stops at the first signed-out probe with the `SIGN-IN` line and exit 5, as in round 1.
5. **R5. The probe reads UTF-8 (Consider, taken).** The probe's `subprocess.run` decodes the tool's output as UTF-8 with `errors="replace"`, so a reply holding bytes outside the console's code page (`C3 81`, or an emoji's `F0 9F 98 80`) is read whole and is never lost as no reply. The arguments passed to `cursor-agent`, `timeout`, `creationflags` and `env` stay the same.
6. **R6. Printed lines stay ASCII (Consider, taken).** Every line the program prints from a reply or an error stays ASCII, whatever the console's encoding. This covers the probe's detail strings (lines 220 and 222) and the `excerpt:` lines of `record_failure` (lines 420, 423 and 453). For text that is all ASCII, each such line prints exactly as today: same characters, no added quotes. For example, `%a` in place of `%r` keeps the `%r` lines identical for ASCII, and an explicit `backslashreplace` to ASCII keeps the excerpt identical. What is stored in the state file is unchanged.
7. **R7. Not changed.**
   - The sign-in check stays before the model-argument check in `record_failure`.
   - Each file is still read whole with `open(..., encoding="utf-8", errors="replace").read()`. Text mode's newline translation stays as today: it turns a lone CR into a line feed before the split.
   - The `SIGN-IN` line, exit 5, `SIGN_IN_PREFIX` (compared case-sensitively), and everything that runs before the probe (the automatic reset, the expiry of unavailable marks) stay as round 1 left them.
   - No option, flag, environment variable, configuration key or dependency is added.
8. **R8. The tree.** `roster-check.py` stays ASCII-only with CRLF line endings. `MANIFEST.json` is regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`. The version stays `2026.11.12a`, and `git diff -- bridge/cursor-bridge/VERSION` shows nothing. The reference is regenerated, and `python tools/dump-cli.py --check` exits 0.

## Acceptance criteria
- [ ] `tests/test_program_roster_sign_in.py` passes whole, unedited (22 cases).
- [ ] `tests/test_roster_check.py`, `tests/test_roster_check_a4.py` and `tests/test_hotfix25a_roster_launcher.py` pass unedited.
- [ ] The docstring's paragraph is restored byte for byte, with the two sentence lines added, and nothing else differs from before round 1 but the exit-5 text (R1). `python tools/dump-cli.py --check` exits 0, and the reference diff touches only the `roster-check.py` entry.
- [ ] The stream rule (R2), the LF-only split and trim (R3), the falsy signed-out constant with `probe` still returning a pair (R4), the UTF-8 read (R5) and the ASCII printing (R6) are met.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`, run from the Workspace root, exits 0 and prints `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it. `git diff -- bridge/cursor-bridge/VERSION` is empty.
- [ ] `roster-check.py` decodes as ASCII and has no bare LF (R8).
- [ ] R-095's program part stays fully met, with no stand-in, placeholder or "later" text.
- [ ] No option, dependency, configuration key or environment variable is added. There is no new external call, no new Semgrep high finding, and no traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used, nothing else).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit any test file or fixture. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer, a user name or an account name. In the report, write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- This increment talks to one external service, the Cursor command-line tool, through the probe's existing call. The tests replay the **recorded real line** in `tests/fixtures/cursor/sign-in-required.txt`. Do not invent another shape of the tool's output. If you believe a fixture you need is missing, stop and report it. Never run the real `cursor-agent`, and add no call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` elsewhere; the program's `NO_WINDOW`). No new process is needed. The probe's call keeps `creationflags=NO_WINDOW`.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong. In `roster-check.py`, change only what R1-R8 need. Every other message, classification, refusal and exit code stays as it is.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- A value the brief marks as the owner's: none. The `SIGN-IN` line's wording and exit 5 are fixed by R-095 and `docs/DESIGN.md` C3, and the tests pin them. Do not change either.
- Follow existing conventions in the files you touch: ASCII program text, CRLF in `roster-check.py`, no argparse (`tools/dump-cli.py` reads this program's docstring), and `main()` returning the exit code.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `restore`. You read with `git status`, `git diff`, `git show`, `git log` and `git rev-parse` only.
- Numbers: this increment parses none.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). The whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutation run comes after yours. Before you finish, apply each mutant below by hand, one at a time, to `roster-check.py`, keeping CRLF. For each mutant, in this order:
  1. Apply the mutant.
  2. Run `python tools/make-manifest.py`.
  3. Run `python -m pytest -p no:cacheprovider -q tests/test_program_roster_sign_in.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_hotfix25a_roster_launcher.py`.
  4. Revert the mutant by hand (never with git).
  5. Run `python tools/make-manifest.py` again.
  6. Confirm with `git diff -- bridge/cursor-bridge/roster-check.py` that the file is back to your finished version.

  In the report, list each mutant by its label and text. For each, show the code before and after **whole**, every changed line written out, never elided with `...` or a comment, each in a fenced block. Then give the pytest summary line in a fenced block and the id of one test it made fail. If it is not caught, write `not caught` and one line on the case that would catch it (you add no case). The mutants:
  - N1 the stdout whole-output rule dropped: stdout is judged like stderr (a line-start match anywhere on stdout counts).
  - N2 the split goes back to `str.splitlines()` (and the trim to bare `strip()`).
  - N3 the probe's UTF-8 decoding removed (no `encoding`/`errors` on its `subprocess.run`).
  - N4 the ASCII printing removed: `%r` again in the probe's detail strings, and the excerpt printed as it is.
  - N5 the signed-out constant made truthy again (for example `object()`).

  N4 may survive on a cp1252 console, because the entry point's `backslashreplace` already escapes what cp1252 lacks. If it is not caught, run step 3 once more for N4 with the environment variable `PYTHONIOENCODING` set to `utf-8` for that one command only, and quote both results. N5 may survive, because no test calls `probe` directly with the sign-in line. Report it as it falls.
- **Known failures.** Ten round-2 cases fail on round 1 (Context). If a case of the four test files fails that your change did not cause, report it by its test id with its failure lines, and fix none.
- Prefer reuse over new code: round 1's helper and constants, the existing `probe`, `record_failure` and `main` structure, and the standard library. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-075-r2-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name. Write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created;
- a one-paragraph summary of what you did;
- for R1-R8, one line each on what meets it, naming the functions and their lines as the file stands after your change. For R4, also name the constant and the value you chose, and how `main()` tests it. For R2, also say how `--record-failure` reads the two files apart and still counts the joined text;
- the mutation self-check list, N1-N5, as Constraints asks;
- every command of the list below, with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: that a signed-out tool prints nothing else on standard output; that the tool writes its output as UTF-8; that a launcher's error file holds the tool's line on a line of its own. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

**Every quoted output in the report comes from the final tree.** Run the list below after your last edit, and quote those runs only: never an output from an earlier state of the files. The mutation runs are the one exception; quote them as each mutant ran.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py` (expect `make-manifest: version 2026.11.12a, ...`)
3. `python tools/dump-cli.py`
4. `python -m pytest -p no:cacheprovider -q tests/test_program_roster_sign_in.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_hotfix25a_roster_launcher.py`
5. `python tools/dump-cli.py --check` (expect exit 0; quote its output and its exit code)
6. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it, exit 0)
7. `python -c "open('bridge/cursor-bridge/roster-check.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
8. `python -c "d=open('bridge/cursor-bridge/roster-check.py','rb').read(); print('bare LF', d.count(b'\n')-d.count(b'\r\n'))"` (expect `bare LF 0`)
9. `git diff -- bridge/cursor-bridge/VERSION` (expect no output)
10. `git diff 6a1434d -- bridge/cursor-bridge/roster-check.py` (quote it whole; its docstring hunk shows only the exit-5 text and the two added lines, R1)
11. `git diff --stat`
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it and do not restore it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it.
- Each mutation is listed by its label and text, with its whole before and after code and what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 12, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
