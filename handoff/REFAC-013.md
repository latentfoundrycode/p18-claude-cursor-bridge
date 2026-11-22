---
record: brief
header: 1
id: REFAC-013
round: 1
satisfies: [R-089]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-013-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-013: one matching of a round's cause, in bridge_env, for the launcher and the guard

## Objective
Refactoring - remove duplication / simplify **without any change in behaviour**.

This brief carries the second candidate of stage P3's refactoring pass. Two programs match the text after `Round cause:` against the list of round causes with the same few lines: the launcher, `bridge/cursor-bridge/bridge-run.py` (`round_cause`, release S), and the review guard, `bridge/cursor-bridge/review-guard.py` (`_cause_on_first_line`, copied there by TASK-069). The matching moves into `bridge/cursor-bridge/bridge_env.py` as one function, `round_cause_word(value)`, with the separator string `_CAUSE_SEPS` moved there beside it; both programs call it; the manifest is regenerated after it. Each program keeps its own way of finding the line. Behaviour stays exactly the same: every cause read, every `unstated`, every note the launcher prints, the `cause` of every round in the launcher's run log and in the guard's rounds record (`.git/bridge/rounds-<ID>.json`), and therefore every count `pace-report.py` prints. Line numbers below are as the three files stand at `c530abd` (TASK-078, the base of branch `refactor/P3`); REFAC-012, which lands on this branch before your run, edits `evaluate-reports.py` only, so these line numbers still hold when you start.

**The sites.**

1. `bridge/cursor-bridge/bridge-run.py`, lines 990-1007, the module constants and `round_cause(brief_text)`:

```python
ROUND_CAUSES = bridge_env.ROUND_CAUSES
ROUND_CAUSE_RE = re.compile(r"^Round cause:[ \t]*(.*?)[ \t]*$", re.M)


def round_cause(brief_text):
    ...docstring, lines 995-998...
    m = ROUND_CAUSE_RE.search(brief_text or "")
    if not m:
        return "unstated", "the brief has no `Round cause:` line (one of: %s); logged as unstated" % ", ".join(ROUND_CAUSES)
    value = m.group(1).lower()
    for cause in sorted(ROUND_CAUSES, key=len, reverse=True):
        rest = value[len(cause):].lstrip()
        if value.startswith(cause) and (not rest or rest[0] in "-:(,;<U+2013><U+2014>"):
            return cause, None
    return "unstated", "the brief's `Round cause:` names none of: %s; logged as unstated" % ", ".join(ROUND_CAUSES)
```

In the file, line 1005's string literal is the five ASCII characters `-:(,;` followed by the two characters U+2013 (EN DASH) and U+2014 (EM DASH) written literally; this brief writes them as `<U+2013><U+2014>` only to stay ASCII. Its one caller is line 1426, `meta["cause"], cause_note = round_cause(brief_text)`, whose note goes to `NOTES`.

2. `bridge/cursor-bridge/review-guard.py`, line 127, and `_cause_on_first_line(text)`, lines 765-784:

```python
_CAUSE_SEPS = "-:(,;" + <the escape for U+2013> + <the escape for U+2014>
```

(line 127 writes the two dashes as Python unicode escapes, a backslash, `u` and four hex digits, so the file stays ASCII), and

```python
def _cause_on_first_line(text):
    ...docstring, lines 766-770...
    causes = sorted(bridge_env.ROUND_CAUSES, key=len, reverse=True)
    prefix = "Round cause:"
    for line in (text or "").split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        if not line.startswith(prefix):
            continue
        value = line[len(prefix):].strip(" \t").lower()
        for cause in causes:
            rest = value[len(cause):].lstrip()
            if value.startswith(cause) and (not rest or rest[0] in _CAUSE_SEPS):
                return cause
        return "unstated"
    return "unstated"
```

Its one caller is `_round_cause(root, id_part)`, line 810, which reads the round's SCOPE file under `_SCOPE_CAUSE_CAP` (line 126) and feeds `"cause": _round_cause(root, id_part)` at line 992. `_CAUSE_SEPS` has no other use in review-guard.py (line 781 is its only reader).

3. `bridge/cursor-bridge/bridge_env.py`, lines 4417-4426, `ROUND_CAUSES`: the tuple `"defect"`, `"security"`, `"fix-induced"`, `"no external path"`, `"records"`, `"builder incomplete"`, `"brief error"`, `"base update"`, in that order. It stays exactly as it is (tests pin it).

**The comparison, character by character (the supervisor's condition for this candidate; the packager checked it at `c530abd`).** Given the same value string, the two copies return the same cause or the same "no cause":
- the list: bridge-run iterates `ROUND_CAUSES`, which line 990 binds to `bridge_env.ROUND_CAUSES` itself; review-guard iterates `bridge_env.ROUND_CAUSES`. The same tuple.
- the order: both `sorted(<that tuple>, key=len, reverse=True)`; the sort is stable, so the order is identical (the three causes of eleven characters, `fix-induced`, `brief error`, `base update`, are not prefixes of one another, so their order would not matter anyway).
- case: both apply `str.lower()` to the value and nothing else; the causes are lowercase literals.
- what follows the cause: both compute `rest = value[len(cause):].lstrip()` (no argument: every character Python counts as whitespace, a carriage return included) and accept when `value.startswith(cause)` and `rest` is empty or its first character is a separator.
- the separators: the same seven characters in both, `-`, `:`, `(`, `,`, `;`, U+2013, U+2014 (bridge-run as literal characters, review-guard as escapes).
- the answer: bridge-run returns `(cause, None)` or falls through to its `unstated` note; review-guard returns `cause` or `"unstated"`.

What differs is only how each program obtains the value, and that stays with each program: bridge-run takes the first line of the whole brief matched by `ROUND_CAUSE_RE` (multi-line mode) and uses `m.group(1)`: the regex has already dropped leading and trailing spaces and tabs, but on a text with CRLF line ends the group keeps the line's carriage return (and any spaces or tabs before it), since `.` matches it and `$` matches only before a line feed; review-guard splits on line feeds, drops one trailing carriage return, takes the first line that begins with `Round cause:`, and applies `.strip(" \t")`. Note: `.strip(" \t")` applied to bridge-run's `m.group(1)` changes nothing (the group never begins or ends with a space or a tab), so a strip of spaces and tabs may sit inside the shared function or stay in review-guard; either way each caller's answer must be today's for every input. Result: the candidate holds; no input is answered differently by the two matchings.

**The change.** `bridge_env.py` gains `_CAUSE_SEPS` (the same seven characters, written as review-guard line 127 writes them, so `bridge_env.py` stays ASCII) and `round_cause_word(value)`: given the text after `Round cause:` as each caller has it, it returns the cause from `ROUND_CAUSES` the value begins with (the comparison above: lowercased, longest cause first, followed by the end of the value or a separator after `lstrip()`), or `None`; no regular expression. review-guard.py keeps no `_CAUSE_SEPS`. `round_cause` keeps `ROUND_CAUSE_RE`, its `m` test and both notes, word for word; `_cause_on_first_line` keeps its line scan, its carriage-return drop, its `prefix`, and its two `"unstated"` returns; each replaces only its inner matching by a call of `bridge_env.round_cause_word`.

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.12a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as it is R-089 (the pace report counts every increment and every recorded round: `review-guard.py snapshot` reads `Round cause: <cause>` from the round's SCOPE file into the round's entry of the rounds record, deciding no count and no lift; the round causes stand once, in `bridge_env.py`, for the launcher, the guard, the in-flight program and the report, built by TASK-069).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-013-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser` and no program's module docstring)
- every file under `tests/`: no test file or fixture may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.12a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- in bridge_env.py: everything but the two added names; `ROUND_CAUSES` (lines 4417-4426) unchanged, the module docstring unchanged, no import added
- in bridge-run.py: everything but the matching lines of `round_cause` (1002-1006); line 990 `ROUND_CAUSES = bridge_env.ROUND_CAUSES` stays (a test reads `ROUND_CAUSES` from the loaded launcher and another requires the text `bridge_env.ROUND_CAUSES` in its source), line 991 `ROUND_CAUSE_RE` stays as it is, `round_cause`'s name, signature, docstring, return shape and both note texts stay; its caller at line 1426 stays
- in review-guard.py: everything but line 127 (removed) and the matching lines of `_cause_on_first_line` (771 and 778-783); its name, signature and docstring stay, `_round_cause`, `_SCOPE_CAUSE_CAP` and line 992 stay
- every other file under `bridge/`, `in-flight.py`, `pace-report.py` and `evaluate-reports.py` among them

## Context
**What the code is today** (`c530abd`). The three files have CRLF line endings on every line; keep them, and add no trailing whitespace. `bridge_env.py` and `review-guard.py` are ASCII only today (bridge_env's module docstring says so on purpose: cp1252 consoles); both must stay ASCII. bridge-run.py holds three non-ASCII characters today: the two dashes of line 1005 and the U+2026 ellipsis on each of lines 19 and 20 of its module docstring; after the change only the two ellipses remain. Both programs already import `bridge_env` (bridge-run.py uses it at line 990; review-guard.py imports it at line 122), so no import is added. The name `round_cause_word` exists nowhere today. REFAC-012 is this stage's earlier refactoring brief; this one touches none of its code.

**How the tests reach this code.** The tests run the Workspace programs as subprocesses, which import `bridge_env.py` from their own folder. `tests/test_release_s_launcher.py` drives the launcher through `tests/test_task032_supervisor_launcher.py`'s `Lab`, `write_brief` and `launch` (a stand-in `cursor-agent` on PATH): `test_m1_a_later_round_s_cause_is_read_into_the_run_log` (seven causes, among them `Builder incomplete:` in mixed case and three spaces before `security (`), `test_m1_a_missing_or_unknown_cause_is_logged_unstated_with_a_note_and_never_refused` (no line, `polish`, and `defective`, a cause followed by letters), `test_m1_a_first_round_carries_no_cause` and `test_m1_the_launcher_and_the_pace_report_hold_one_list_of_causes`. `tests/test_program_pace_rounds.py` (TASK-069, R-089) is both the launcher's and the guard's cause test: `test_r089_in_flight_and_the_launcher_accept_base_update`, `test_r089_the_guard_writes_the_round_s_cause_beside_its_time` (`review-guard.py snapshot` on a scratch repository: the first of two cause lines, a missing line, a word outside the list, a re-read) and `test_r089_r2_a_long_scope_line_never_stalls_the_snapshot` (a line of 200,000 spaces between two words must stay fast and unstated: the shared function must stay linear in the value's length, as both copies are today), and its pace-report cases count the causes. `git grep -l -e "Round cause" -- tests` lists exactly these two files; no other review-guard test file reads the cause. `tests/test_program_in_flight.py` pins the list's single home: `test_r088_the_launcher_the_report_and_this_program_hold_no_copy_of_the_list` reads bridge-run.py's source for the text `bridge_env.ROUND_CAUSES`, and `test_r088_the_launcher_and_the_pace_report_see_the_same_list_as_bridge_env` loads it. `tests/test_header_currency.py` reads, by syntax tree, the names the programs under `bridge/cursor-bridge/` define and use; it is in the command below as the guard that no retired reading came back. The tests make no network call. Some cases may be skipped on this machine (`tests/test_release_s_launcher.py` skips two where the account can make neither a symbolic link nor a junction); the skip count must be the same before and after.

**The expected count.** The supervisor's baseline run of the pytest command below at `c530abd`, with this brief untracked, ended "200 passed, 1 skipped". REFAC-012 changes no test, so the count stands after it. Your before-edit run is the baseline, and the after-edit run must match it (the same count passed, none failed, the same count skipped).

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for the three files; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.12a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.12a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.12a`. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** This is a logic surface over untrusted input: the launcher reads a brief, and the guard reads a SCOPE file of at most `_SCOPE_CAUSE_CAP` bytes (1048576) decoded with `errors="replace"`, and each turns one line of it into a word written to a record. The trust boundary is the content of those two files. `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). This change moves no boundary: the same values are accepted, nothing outside `ROUND_CAUSES` is ever returned as a cause, no regular expression is added (the guard's matching stays linear, R-089 round 2's advisory), and the guard's byte cap stays where it is.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders and the repositories they create there. Never run bridge-run.py, review-guard.py, pace-report.py or `bridge-install.py` yourself, against this repository or any other, never run `gh`, and never call GitHub.

## Diagrams
`docs/diagrams/D-002-components.md` - the elements `bridge_env` (`bridge/cursor-bridge/bridge_env.py`), `bridge_run` (`bridge/cursor-bridge/bridge-run.py`) and `review_guard` (`bridge/cursor-bridge/review-guard.py`), whose edges already exist:

```mermaid
    bridge_run --> bridge_env
    review_guard --> bridge_env
```

The change adds a function to `bridge_env` and a call to it from each of the two programs that already import it: no import and no edge, so the diagram does not change. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -e "_CAUSE_SEPS" -e "ROUND_CAUSES" -- bridge tests`. Expected: `_CAUSE_SEPS` on exactly two lines, `bridge/cursor-bridge/review-guard.py:127:` and `bridge/cursor-bridge/review-guard.py:781:`, and on no line under `tests/` (no test imports or reads `_CAUSE_SEPS` from review-guard); `ROUND_CAUSES` among others at `bridge/cursor-bridge/bridge_env.py:4417:`, `bridge/cursor-bridge/bridge-run.py:990:`, `:1003:` and `bridge/cursor-bridge/review-guard.py:771:`. Then run `git grep -n -w -e round_cause_word -- bridge tests` and confirm it prints nothing, and `git grep -l -e "Round cause" -- tests` and confirm it prints `tests/test_program_pace_rounds.py` and `tests/test_release_s_launcher.py` only. If a check does not hold (a test that names `_CAUSE_SEPS`, an existing `round_cause_word`, a line number other than these), stop, change nothing, and report it.
2. `bridge_env.py` defines `_CAUSE_SEPS` (the same seven characters, in ASCII source) and `round_cause_word(value)` once each, after `ROUND_CAUSES`; `round_cause_word` returns a member of `ROUND_CAUSES` or `None`, uses no regular expression, and for every string returns the cause both copies return today for that value.
3. `round_cause` in bridge-run.py and `_cause_on_first_line` in review-guard.py each call `bridge_env.round_cause_word` once in place of their own loop, and map its `None` to their own `unstated` answer exactly as today (bridge-run's second note, word for word; review-guard's `"unstated"` for the first `Round cause:` line, never a later one). Neither keeps a loop over the causes or a separator string.
4. review-guard.py no longer defines `_CAUSE_SEPS`.
5. No other line of the three files changes. They keep their CRLF line endings and gain no trailing whitespace; `bridge_env.py` and `review-guard.py` stay ASCII. No comment is added in place of the removed lines.
6. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: the same cause or `unstated` for every brief the launcher reads and every SCOPE file the guard reads (the first `Round cause:` line only, case, spaces and tabs, a carriage return, each separator, a cause followed by letters, the longest cause first), the same two notes from bridge-run, the same `cause` in the run log and in the rounds record, and so the same counts from pace-report.py.
- [ ] The report states, from your own reading of the two copies at the start, whether they accept the same values (list, order, case, `lstrip()`, the seven separators), and why the shared function gives each caller today's answer for every input, including the carriage return bridge-run's group can keep and review-guard's strip of spaces and tabs.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] Every caller uses the single implementation and the duplicate is gone: `git grep -n -w -e _CAUSE_SEPS -- bridge` prints lines of `bridge/cursor-bridge/bridge_env.py` only, one of them its definition; `git grep -n -F "def round_cause_word(" -- bridge` prints one line, in `bridge/cursor-bridge/bridge_env.py`; `git grep -n -w -e round_cause_word -- bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py` prints exactly two lines, one in each file; `git grep -n -F "rest[0] in" -- bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py` prints nothing; `git grep -n -F "ROUND_CAUSES = bridge_env.ROUND_CAUSES" -- bridge/cursor-bridge/bridge-run.py` prints one line; `git grep -n -w -e ROUND_CAUSE_RE -- bridge` prints two lines of bridge-run.py, as before.
- [ ] `python -c "import sys; [print(p) for p in sys.argv[1:] if not open(p, 'rb').read().isascii()]" bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/review-guard.py` prints nothing.
- [ ] No public signature changed: `round_cause(brief_text)` still returns `(cause, note)`, `_cause_on_first_line(text)` a word; no name other than `_CAUSE_SEPS` (moved) and `round_cause_word` (added) is added, renamed or removed; no file imports anything new.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.12a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.12a`).
- [ ] `git diff --stat` shows only `bridge/cursor-bridge/bridge_env.py`, `bridge/cursor-bridge/bridge-run.py`, `bridge/cursor-bridge/review-guard.py`, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This change talks to no external service, and its tests use no recorded reply; do not invent a mock of any service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only.
- No value in this task is marked as the owner's. The list `ROUND_CAUSES` is pinned by tests and stays exactly as it is.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_release_s_launcher.py tests/test_program_pace_rounds.py tests/test_program_in_flight.py tests/test_header_currency.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; `git diff --numstat -- bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py`; the six `git grep` commands of the fourth acceptance criterion; the `python -c` ASCII command of the fifth.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example `ROUND_CAUSE_RE`'s lazy group and the carriage return it can keep, the two programs' different ways of finding the line, or bridge-run reading any line of the brief where the guard reads the first line beginning `Round cause:`); report them in your summary instead. Do not introduce an abstraction beyond what the two copies need: one function and the moved separator string; no class, no regular expression, no new parameter on `round_cause` or `_cause_on_first_line`, no alias of the new function in either program.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-013-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the Requirements 1 grep commands with their output as the evidence;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, the two `git diff --numstat` commands, the fourth acceptance criterion's six `git grep` commands and the ASCII command, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- the comparison the second acceptance criterion asks for, from your own reading;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
