---
record: brief
header: 1
id: REFAC-009
round: 1
satisfies: [R-083, R-085]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-009-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-009: one reading of a reader's reply bits and a branch rule's contexts, in bridge_env

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries the second candidate of stage P2's refactoring pass: two pairs of copies that TASK-065 (the CI watch's wait in `bridge/cursor-bridge/bridge-run.py`, R-085) and TASK-083 (`review-guard.py ready`, R-083) left in the two scripts, because neither script may import the other. One pair reads the `source` and `reason` of a bridge_env reader's reply, with a fallback; the other sorts a `bridge_env.branch_rule` answer into "the contexts", "names none" or "cannot be read". Both move into `bridge/cursor-bridge/bridge_env.py`, the module both scripts already share; the manifest is regenerated after it. Behaviour stays exactly the same: every printed line, every error string, every exit code, every refusal. Line numbers below are as the files stand at `ff5786e` (REFAC-008, the head of branch `refactor/P2`), before your edit.

**The sites.**

1. `bridge/cursor-bridge/review-guard.py` lines 1478-1485:

```python
def _reader_bits(got, fallback):
    source, reason = fallback, "cannot read"
    if isinstance(got, dict):
        if isinstance(got.get("source"), str) and got.get("source"):
            source = got["source"]
        if isinstance(got.get("reason"), str) and got.get("reason"):
            reason = got["reason"]
    return source, reason
```

Its callers: lines 1527 and 1533 (inside `_rule_contexts`, fallback `"protection"`), 1611 (`_await_pull`'s `read`, fallback `"pull"`), 1651 (`prove_ci`, fallback `"repo"`), 1668 (`prove_ci`, fallback `"checks"`).

2. `bridge/cursor-bridge/bridge-run.py` lines 2030-2038, `_watch_bits(got, fallback)`, with the docstring `"""(source, reason) as the reader clipped them, or the fallback when the reply has neither."""`: the same six body lines as `_reader_bits`, except that its last line is `return _watch_plain(source), _watch_plain(reason)`. Its callers: lines 2107 (`"protection"`), 2112 (`"repo"`), 2130 (`"protection"`), 2290 (`"pull"`), 2301 (`"checks"`).

3. `bridge/cursor-bridge/review-guard.py` lines 1524-1535:

```python
def _rule_contexts(got, which):
    """(contexts, None) or (None, the CANNOT CHECK reason). An empty list is a rule that names none."""
    if not isinstance(got, dict) or got.get("answer") not in (bridge_env.ANSWER_VALUE, bridge_env.ANSWER_NONE):
        source, reason = _reader_bits(got, "protection")
        return None, "the %s branch's rule cannot be read (%s: %s)" % (which, source, reason)
    if got.get("answer") == bridge_env.ANSWER_NONE:
        return [], None
    contexts = got.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        source, reason = _reader_bits(got, "protection")
        return None, "the %s branch's rule cannot be read (%s: %s)" % (which, source, reason)
    return contexts, None
```

Its callers: `prove_ci` lines 1643 (`"base"`) and 1659 (`"default"`).

4. `bridge/cursor-bridge/bridge-run.py` lines 2084-2095:

```python
def _watch_contexts(rule):
    """The rule's contexts, [] where it names none, or None where it cannot be read (never a pass)."""
    if not isinstance(rule, dict):
        return None
    if rule.get("answer") == bridge_env.ANSWER_NONE:
        return []
    if rule.get("answer") != bridge_env.ANSWER_VALUE:
        return None
    contexts = rule.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        return None
    return contexts
```

Its callers: `_watch_name` lines 2102 and 2124.

**What the reality check found about their semantics** (the supervisor's packaging read every copy and every caller). `_reader_bits` and `_watch_bits` compute the same `(source, reason)` pair from the same tests on every input (a non-dict reply, a missing key, a non-string, an empty string all keep the fallback and `"cannot read"`); the only difference is `_watch_bits`'s `_watch_plain` on each of the two results, which stays in bridge-run.py. The fallback is always a literal at the call site (`"protection"`, `"pull"`, `"repo"`, `"checks"`); each caller keeps its own literal. `_rule_contexts` and `_watch_contexts` classify every input the same: a non-dict, or an `answer` that is neither `bridge_env.ANSWER_VALUE` (`"value"`) nor `bridge_env.ANSWER_NONE` (`"none"`), is unreadable; `answer == "none"` gives `[]` whatever `contexts` holds; `answer == "value"` with a `contexts` that is not a list, or is an empty list, is unreadable; otherwise the `contexts` list itself (the same object, not a copy) is returned, its entries unchecked by either copy (a list holding non-dict entries is returned as it is; `prove_ci` and the wait check entries later, and that stays as it is). `_rule_contexts`'s membership test `not in (ANSWER_VALUE, ANSWER_NONE)` and `_watch_contexts`'s `== ANSWER_NONE` / `!= ANSWER_VALUE` agree on every value a reply can hold. `_rule_contexts`'s two unreadable branches build the same message from the same reply with the same fallback, so one unreadable branch gives the same string. No copy is kept on account of a difference; the two differences (the `_watch_plain` wrap and review-guard's own error wording) stay at their callers.

**The proposed shape.** `bridge_env.py` gains two public functions in its GitHub reads section (the section that begins at line 3836 with `GH_COMMAND`, `ANSWER_VALUE`, `ANSWER_NONE`; the placement inside it is yours): `reply_bits(got, fallback)`, giving exactly the `(source, reason)` pair `_reader_bits` gives today, unwrapped; and `rule_contexts(got)`, giving the `contexts` list where the answer is a value with a non-empty list, `[]` where the answer is none, and `None` for everything else, exactly as `_watch_contexts` gives today. Then:

- review-guard.py: `_reader_bits` is deleted; its callers at lines 1611, 1651 and 1668 call `bridge_env.reply_bits(...)` with their own fallback. `_rule_contexts(got, which)` stays, with its name, signature, docstring and return values as today, and its body calls `bridge_env.rule_contexts(got)`; where that gives `None` it returns `None, "the %s branch's rule cannot be read (%s: %s)" % (which, source, reason)` with `source, reason` from `bridge_env.reply_bits(got, "protection")`; otherwise it returns the list and `None`. Its callers at 1643 and 1659 do not change.
- bridge-run.py: `_watch_contexts` is deleted; its callers at lines 2102 and 2124 call `bridge_env.rule_contexts(...)`. `_watch_bits(got, fallback)` stays, with its name, signature and docstring, and its body becomes `bridge_env.reply_bits(got, fallback)` with `_watch_plain` applied to each of the two results, as today. Its five callers do not change.

Use the module's existing `bridge_env.<name>(...)` form at each call; bind no module-level alias (no `_watch_contexts = bridge_env.rule_contexts`).

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.12a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as they are R-083 (one reader of a repository's branch rule, and the proof that CI passed as a program: `review-guard.py ready`, built by TASK-064 and TASK-083) and R-085 (a CI watch never returns before CI has run: the launcher's wait, built by TASK-065).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-009-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser` and no module docstring)
- every file under `tests/`: no test file may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.12a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- every other function of the three programs (in particular `_answer`, `_clip_reason`, `branch_rule`, `repo_settings`, `pull_refs`, `head_state`, `latest_of_each`, `is_int_id`, `app_id_of`, `suite_id` and the gh call path in bridge_env; `_watch_plain`, `_watch_name`, `watch_loop` and the rest of the wait in bridge-run.py; `_show`, `_cannot`, `_await_pull`, `prove_ci` beyond the call lines named in the Objective, and the rest of `ready` in review-guard.py), each module docstring, and every other file under `bridge/`

## Context
**What the code is today** (`ff5786e`). All three programs have CRLF line endings on every line; keep them, and add no trailing whitespace. Both scripts already `import bridge_env` and call it throughout in the form `bridge_env.<name>(...)`; nothing new is imported. REFAC-008, the commit at HEAD, moved the check app id and suite id readers into bridge_env the same way (`is_int_id`, `app_id_of`, `suite_id`, at bridge_env lines 4260-4288); this brief follows its pattern. bridge_env's readers build every reply through `_answer(answer, reason="", source="", **extra)` (line 3875), which sets `source` and `reason` only where the answer is `ANSWER_CANNOT` (`"cannot read"`); `branch_rule(repo, branch, cwd=None)` (line 4005) answers `value` with a non-empty `contexts` list, `none` with `contexts=[]`, or `cannot read` with `contexts=[]` and source `protection` or `rules`.

**Names.** At `ff5786e` the strings `reply_bits` and `rule_contexts` appear nowhere in the repository except as part of review-guard's `_rule_contexts`; the two public names are free. No file under `tests/`, `tools/` or `docs/` names `_reader_bits`, `_watch_bits`, `_rule_contexts` or `_watch_contexts`.

**How the tests reach this code.** `tests/test_program_watch_wait.py` (TASK-065) drives bridge-run.py's wait (`_watch_name`, `_watch_bits`, the unreadable-rule and unreadable-default lines); `tests/test_program_ready.py` (TASK-083) drives review-guard.py's `ready` (`prove_ci`, `_rule_contexts`, the CANNOT CHECK lines); `tests/test_program_branch_rule.py` (TASK-064) covers bridge_env's readers, `branch_rule` among them; `tests/test_bridge_run.py` and `tests/test_review_guard.py` hold the programs' other cases (the `test_r085_` and `test_r083_` ones among them). `tests/test_header_currency.py` reads, by syntax tree, the names the programs under `bridge/cursor-bridge/` define and use; it is in the command below because this change moves names. Every case answers GitHub from recorded replies under `tests/fixtures/github/` through a stand-in program: the tests set `bridge_env.GH_COMMAND` to this interpreter and the stand-in, so the real `gh` never runs and no network call is made. Some cases are marked POSIX-only and are skipped on Windows; that is expected, and the skip count must be the same before and after.

**Time and retry limits.** This change makes no call and adds no retry. The existing limits stay as they are and are not to be touched: `bridge_env.GH_API_TIMEOUT = 30` (seconds per gh call), `bridge_env._GH_MAX_PAGES = 100`, review-guard.py's `PR_HEAD_WAIT` and `PR_HEAD_STEP`, bridge-run.py's `WATCH_POLL = 15` (seconds between the wait's polls). This brief does not test on Claude Code: no `claude` command is part of it and no `claude --version` line is recorded.

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for the three programs; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.12a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.12a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.12a`. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** This is a logic and input-handling surface: the two functions read GitHub-derived replies (`gh api`, the trust boundary here, already clipped by bridge_env's `_clip_reason`) before the wait and `ready` print or compare them; `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). This change moves no boundary: an unreadable rule is still never a pass (`ready` still answers CANNOT CHECK, the wait still falls back to the workflow runs), and every text bridge-run.py prints from a reply still passes through `_watch_plain`.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders and the recorded fixtures. Never run bridge-run.py, review-guard.py or `bridge-install.py` yourself, against this repository or any other, and never call GitHub.

## Diagrams
`docs/diagrams/D-002-components.md` — the elements `bridge_env` (`bridge/cursor-bridge/bridge_env.py`), `bridge_run` (`bridge/cursor-bridge/bridge-run.py`) and `review_guard` (`bridge/cursor-bridge/review-guard.py`). Both scripts already draw an edge to bridge_env:

```mermaid
    bridge_run --> bridge_env
    review_guard --> bridge_env
```

The change adds no import and no edge (bridge-run.py must not import review-guard.py, nor the reverse; bridge_env imports neither), so the diagram does not change. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -e _reader_bits -e _watch_bits -e _rule_contexts -e _watch_contexts -- bridge tools tests docs` and confirm every line is in bridge-run.py or review-guard.py, at the definitions and calls listed in the Objective (line numbers may differ by a few). Run `git grep -n -w -e reply_bits -e rule_contexts` and confirm it shows nothing. If a check does not hold, stop, change nothing, and report it.
2. bridge_env.py defines `reply_bits(got, fallback)` and `rule_contexts(got)` once each, public, with the semantics stated in the Objective; `rule_contexts` returns the reply's own `contexts` list, not a copy.
3. review-guard.py no longer defines `_reader_bits`; bridge-run.py no longer defines `_watch_contexts`. `_rule_contexts` (review-guard.py) and `_watch_bits` (bridge-run.py) remain, with their signatures and docstrings, each calling the bridge_env function as the Objective states. Every caller gets, for every input, the value it got before.
4. No other line of the three programs changes. Each keeps its CRLF line endings and gains no trailing whitespace. No docstring or comment you leave states something the code no longer does.
5. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: the same printed lines, error strings, exit codes and refusals of `bridge-run.py` (the wait before a CI watch) and `review-guard.py ready`, for every input, including a reply that is not a dict, an `answer` that is neither value nor none, a value answer whose `contexts` is empty or not a list, a none answer that carries contexts, and a `contexts` list holding non-dict entries.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] Every listed caller uses the single implementation in bridge_env; the two deleted copies are gone (`git grep -n -e "def _reader_bits" -e "def _watch_contexts" -- bridge` shows nothing), and `git grep -n -e "def reply_bits" -e "def rule_contexts" -- bridge` shows one line each, both in bridge_env.py.
- [ ] No public signature outside the listed sites changed; the only new names are `bridge_env.reply_bits` and `bridge_env.rule_contexts`.
- [ ] Neither script imports anything new, and neither imports the other.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.12a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.12a`).
- [ ] `git diff --stat` shows only the three programs, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service: its tests replay the recorded real responses under `tests/fixtures/github/` through the stand-in the tests install; do not invent a mock of GitHub's responses, and do not add or change a fixture.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources, the recorded fixtures and pytest's temporary folders only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_program_ready.py tests/test_program_watch_wait.py tests/test_program_branch_rule.py tests/test_bridge_run.py tests/test_review_guard.py tests/test_header_currency.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; the two `git grep` commands of the third acceptance criterion.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example review-guard's `reply_bits` results reaching `_cannot` without a `_show`, or a `contexts` list whose entries are not dicts); report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: the two functions in bridge_env; no class, no new parameter (in particular, no `plain` or wrapper argument on `reply_bits`, and no message argument on `rule_contexts`), no module-level alias in either script, nothing new outside the three programs.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-009-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the Requirements 1 grep commands with their output as the evidence;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, `git diff --numstat -- bridge/cursor-bridge/VERSION` and the acceptance criterion's two `git grep` commands, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
