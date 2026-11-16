---
record: brief
header: 1
id: "TASK-063"
round: 6
satisfies: [R-082]
scope: ["bridge/cursor-bridge/permission-guard.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_permission_guard.py", "tests/test_permission_guard_a4.py", "docs/BUILDER_NOTES.md", "handoff/TASK-063-r6-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-063, round 6: the flat reader's local defects (R-082)

Round cause: security

Blocking class: security - Review A, round 5, B10: compgen -C runs a command, and the guard lets it through (compgen -C 'git worktree remove y' y passes, as it does on round 4's tree)

Satisfies: R-082 - the permission guard reads a command as the shell does; the full text stands in round 1's brief, and the design is the flat grammar decided by the second resolution round (docs/CHANGES.md, 2026-11-15 TASK-063).

## Objective
Round 5 wrote the flat reader that `handoff/TASK-063-r5.md` specifies, and its design stands. Review A and the security audit found twenty-five defects in it, every one local: a place where the code does not do what round 5's brief says. **This round fixes those defects in round 5's code, and changes nothing else.** Round 5's code (this brief's commit) is your starting tree: keep its structure, its function names and its passing behaviour, and do not rewrite the reader. `handoff/TASK-063-r5.md` stays in force word for word, requirements 1 to 11 included; this brief adds precision where round 5's code went wrong, and where the two seem to differ, this brief governs. Read `handoff/TASK-063-r5.md` whole first, then `docs/CHANGES.md` (the entry "2026-11-15 TASK-063: second resolution round").

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_permission_guard.py
- tests/test_permission_guard_a4.py
- docs/BUILDER_NOTES.md
- handoff/TASK-063-r6-report.md

Limits:
- The limits of `handoff/TASK-063-r5.md`'s Scope section apply unchanged (`main()`'s shape, the constants that never shrink, the generated files only as regenerated).
- The two test files: add cases, and restore the cases round 5 deleted (requirement 17). An existing case may change only as round 5's Limits allow. No case that expects a refusal is removed, or changed to accept a pass.

Do not modify anything else.

## Out of scope
- Everything round 5's Out of scope section lists, unchanged.
- `tests/test_program_permission_guard.py` and `tests/test_allowlist.py`: the supervisor's; read both whole; edit nothing in them. The acceptance file's section headed "round 5's findings" holds this round's forms.
- Advisory items, each left as it stands: the `find` clause join (round 5's audit S10); the `"2>&1"` slice (S11); a carriage return splitting words under the Bash reading, which only refuses more (S9).

## Context
- `handoff/TASK-063-r5.md`: the grammar, word for word.
- `docs/CHANGES.md`, the entry "2026-11-15 TASK-063: second resolution round": the decision.
- `tests/test_program_permission_guard.py`: the acceptance file; its last section is this round's.

## Requirements
Each item names the defect, where it is in round 5's code, and the fix. Line numbers are round 5's.

1. **A word started by quotes** (lines 521-522, 610 and 829). Keep a flag that a word has started, set by any character added to the word and by any opening quote. An empty quoted word (`''`, `""`) is a word: it is kept in the list, empty (`git -C '' worktree remove x` reads `-C` with the value `''`, then the subcommand `worktree`; `-m ''` takes the empty word as its value). A `#` starts a comment only when no word has started, under the bash and PowerShell readings alike (`echo ''#x` is the words `echo` and `#x`). Under the PowerShell reading an empty quoted word (`''`, `""`) standing as a whole word is unreadable: Windows PowerShell 5.1 drops it from a native program's arguments and PowerShell 7.3 and later passes it, so `git '' worktree remove x` or `git -C '' worktree remove x` runs the removal under one of them.

2. **A backslash before a line end** (lines 597-605). Outside quotes: a backslash and one new line are both removed (two characters, nothing more); a backslash before a carriage return adds a literal carriage return to the word and advances two characters, so the new line after it ends the command. Inside double quotes the same rule for a new line. A following second new line, or the new line after an escaped carriage return, is a separator.

3. **Redirection targets read by the main reader** (lines 682-731). Delete `_skip_redirect_target_bash` and the PowerShell target scanner (lines 893-902). When the reader reads a redirection operator, it sets a flag; the next word the main loop completes, with the same quote, escape and character rules as every word (so `$`, a backtick, `(`, a glob character, a non-ASCII character and the rest are unreadable inside it, under each reading's rules), is taken out as the target instead of joining the words. A redirection whose target is missing (end of the command, a separator, another operator) is unreadable. A run of digits before `<` or `>` is a descriptor number only when it is the whole word so far, with no quote and no backslash in it (in bash `\2>x` is the word `2` and a redirection to `x`); the reader decides this at the operator, from the word it is already holding, without rescanning (linear time, requirement 8); any other word held at the operator is completed as a word first (`echo hi>x` is `echo hi`). After `>&` or `<&` the target is the next whole word, read as above like every target, whatever it holds (`-`, digits, or a file name); it is taken out whole and never split, so in `git >&-C worktree remove y`, `git >&2C worktree remove y` and `git >&- worktree remove y` the word `worktree` is git's subcommand.

4. **A named descriptor before either operator** (line 636). A word that is wholly `{name}` directly followed by `<` or `>` (so `{fd}<x`, `{fd}<>x`, `{fd}>x`, `{fd}>>x`) is unreadable.

5. **The command word after the whole prefix chain** (lines 237, 361, 540-545 and 1149-1157). Walk each command's prefix chain once, in one function that both the refusals and `strip_prefix` use: leading assignments, then each prefix wrapper of round 5's requirement 5, each read with its own option table (an option outside its table is unreadable, `env -S` and `--split-string` refused, `GIT_CONFIG` assignments refused also when they are `env`'s `NAME=value` words), until the word that is no prefix. That word is the command word, and every command-word refusal of round 5's requirement 3 applies to it: the reserved words, the refused builtins, the launchers refused under either tool, a shell reading standard input, `bash -i`, the `bash`/`sh` option table, the `cmd` switch table, the `powershell` switch table. `strip_prefix` returns the same command word; it never skips "any word starting with `-`". A command of assignments alone, or `env` with no command, has no command word and passes (a Workspace included: no `IndexError`, line 1012).

6. **Program names compared without `.exe`** (lines 250 and 252). Remove a trailing `.exe` (any case) before comparing a command word with the shell, wrapper, prefix, launcher and builtin names of round 5's requirements 3 and 5 (`bash.exe` and `sh.exe` are `bash` and `sh`). Never before comparing with `AROUND_THE_SHIM` (`cursor-agent.exe` keeps refusing) or with the PowerShell cmdlet and alias lists (`where.exe` and `curl.exe` are native programs).

7. **The builtins list** (line 142). `REFUSED_BUILTINS` holds every builtin of round 5's requirement 3 except the ones it lets through: add `compgen`, `complete`, `compopt`, `continue`, and check the list against the requirement's list word by word. A shell whose first word after the options is `-` or begins `/dev/` or `/proc/` reads standard input or a descriptor and is unreadable (`echo x | bash /dev/stdin`, `bash /proc/thread-self/fd/0`).

8. **Linear time** (lines 635-641, 720 and 851). No slice to the end of the text (`text[i:]`), no regular expression run at a character, no split of the rest of the text, no rescan of a run already read. The brace forms of round 5's requirement 2 are recognised by reading ahead character by character, and a brace run that does not match is unreadable at the first character that breaks the form. The PowerShell `@` check reads the current word only. The acceptance file's three long inputs (sixty thousand digits, two hundred thousand `{}`, twenty-five thousand `@h/ ` words under PowerShell) each finish within the hook's fifteen seconds.

9. **The escaped `$`** (line 606). A `$` outside single quotes and comments is unreadable whether or not a backslash stands before it, as round 5's requirement 3 says; the same for a backtick.

10. **The cmd reader** (lines 428-431, 905-933 and 1084). The `cmd` switch table is read over every word before the inner command, not only the first switch: `/d /cgit` holds the glued switch `/cgit` and is unreadable, under either tool and after any prefix (`nohup cmd /cgit ...`). The cmd mode splits on `&`, `&&`, `||` and `|`, and takes redirections out wherever they stand (before the command word too): a redirection is an optional single digit that is the whole word so far, then `<`, `>`, `>>`, or `<&`/`>&` followed by one digit; `<`, `>` and `>>` take their target, the next word (a missing target is unreadable); `n>&m` takes none; so `cmd /c "git 2>x worktree remove y"` and `cmd /c "git >>x worktree remove y"` are refused as the removal. It then applies, to each command's word: the cmd builtin rule (only `dir`, `echo`, `type`, `cd` and `ver` pass; `chdir`, `mkdir`, `md`, `move`, `path` and the rest are unreadable), and every refusal round 5's requirement 3 applies under either tool (`winpty`, `wsl` and the other launchers); every other command is checked as a command.

11. **PowerShell** (lines 788-791, 806, 869 and 876-881).
    - Every character outside printable ASCII, tab, a new line and a carriage return before a new line is unreadable, wherever it stands (form feed and vertical tab included).
    - The redirections are `>` and `>>`, each optionally preceded by one of `1` to `6` or `*` that is the whole word so far, and `n>&1`/`n>&2` (n one of `1` to `6` or `*`). `>` and `>>` take a target read by requirement 3 (a missing target is unreadable). `n>&1` and `n>&2` are complete and take no target, so `python x.py 2>&1` passes and in `git 2>&1 worktree remove y` the word `worktree` is git's subcommand. Any other word held at `>` is completed as a word first (`echo hi>x` is `echo hi`).
    - A command word holding `\` whose part after the last `\` is of the `Verb-Noun` form, or an alias of either list, is unreadable whatever the cmdlet (round 5's requirement 4), so `Microsoft.PowerShell.Management\Start-Process` and `Microsoft.PowerShell.Management\Get-ChildItem` are both unreadable; a path to a native program (`C:\tools\git.exe`) is not module-qualified.
    - `-noexit` is outside round 5's PowerShell switch table: remove it from `_parse_ps_wrapper` (line 459) and `shell_inner` (line 1072), so it is unreadable (`echo x | powershell -NoExit -Command Get-ChildItem`).

12. **Rule 8 reads every pipeline stage** (lines 555 and 675). In a Workspace, a part of the top-level list (a pipeline counts as one part) changes state when any of its stages changes state, under round 5's requirement 6's rule; so `echo hi; git commit -m x | cat` is refused as a chain. The chain rule still reads every reading at every depth, each wrapper's re-read included (round 5's requirement 6; `bash -c "bash -c 'git add -A && git commit -m x'"` stays refused in a Workspace). Only the `cd` rule is limited to the outermost reading: `bash -c 'cd x'` passes in a Workspace.

12a. **The `HUSKY=0` rule uses the same prefix walk** (lines 1024-1053). `leading_husky_zero` walks the prefixes with requirement 5's one function, each option with its value, so `stdbuf -o L env HUSKY=0 git commit -m x` is refused.

13. **The checkpoint subject from `-m<text>`** (lines 1163-1170). `commit_message` reads `-m<text>` and `--message=<text>` as well as `-m <text>`, so `git commit -mcheckpoint\ before\ TASK-001 --no-verify` passes as the checkpoint.

14. **The docstring** (lines 24-26). The sentence saying a here-document read by a shell is that shell's script and is checked is replaced by one saying a here-document is unreadable; regenerate the command reference (round 5's requirement 11).

15. **Dead code.** Delete `_snapshot`, `READ_CACHE` (its `READ_CACHE.clear()` at line 1182 included) and `raw_parts` (Review A, N1).

16. **Your own cases**, each naming R-082, in `tests/test_permission_guard_a4.py` (round 5's requirement 10, which round 5 did not write): for each wrapper of round 5's requirement 5 (`env`, `nice`, `nohup`, `stdbuf`, `timeout`, `setsid`, `sudo`, `exec`, `command`, `builtin`, `eval`, `bash`, `sh`, `cmd`, `powershell`, `find`), one command that passes and one that is refused (an option outside the table, or a refused command behind it); and for each requirement 1 to 13 and 12a above, at least one case the acceptance file does not already hold. The report lists every case you added by its test name. Every subprocess call passes `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` on the same line and a timeout.

17. **The deleted cases restored.** Round 5 deleted cases its Limits said to change, not delete. Restore each: in `tests/test_permission_guard.py`, `find . -name '*.log' -exec rm {} ;` (it was in `test_allowed`, parametrised over Bash and PowerShell) as a Bash case expecting a pass and a PowerShell case expecting a refusal whose reason holds `cannot read`; the two here-document commit cases of `test_allowed` in `tests/test_permission_guard.py` (in Python source, `"git commit -F - <<'EOF'\nfix the guard\n\ngh pr merge 12 --squash is refused without the record\nEOF"` and `"git commit -F - <<'EOF'\nfix\n\nbash <<EOF2 is not what this message runs\nEOF"`) as cases expecting a refusal whose reason holds `cannot read` under both tools; and the case round 5 removed from the refusal list of `test_a_commit_that_skips_its_checks_is_refused` in `tests/test_permission_guard_a4.py` (in Python source, `"git commit --no-verify -m \"$(cat <<'EOF'\ncheckpoint before TASK-003\n\nthe tree as delegated\nEOF\n)\""`), put back in that list unchanged (a refusal expected; widen that test's reason assertion to accept `cannot read` if it checks a reason).

## Acceptance criteria
- [ ] Every test in `tests/test_program_permission_guard.py` passes, the file unchanged.
- [ ] Every test in `tests/test_allowlist.py`, `tests/test_task032_supervisor_guard.py`, `tests/test_review_guard.py` and `tests/test_release_s_records_gate.py` passes, unchanged; every test in `tests/test_permission_guard.py` and `tests/test_permission_guard_a4.py` passes, changed only as the Scope's Limits allow.
- [ ] Your cases of requirement 16 pass, name R-082, and are listed in the report.
- [ ] The report states, for requirement 3, that no second scanner of redirection targets remains, and for requirement 8, that no `text[i:]` slice, regular expression at a character, or split of the rest of the text remains in the reader.
- [ ] `python tools/dump-cli.py --check` current; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` matches; `VERSION` and `settings.bridge.json` unchanged.
- [ ] No dependency added; standard library only; every added line of `permission-guard.py` ASCII.

## Constraints
- Do not add dependencies. The standard library only.
- Do not read or write any file outside this workspace (the folder you were started in).
- No secret is needed or used.
- If the brief, the rules or the tooling got in your way, append one dated line to `docs/BUILDER_NOTES.md`; the same for a defect or a pitfall you learned. Do not fix the tooling.
- In any Markdown you write, one paragraph is one line.
- Run every command in the foreground; start nothing in the background; leave nothing running.
- While you work, run only these, each in the foreground: `python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py` and `python -m pytest -p no:cacheprovider -q tests/test_permission_guard.py tests/test_permission_guard_a4.py`. Run the Done section's commands once, after your last edit. Run no other Python: no probe scripts, no `python -c`; create no file outside the Scope. What you do not settle, list under `Assumed, not verified`.
- These git commands are not yours: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. Read with `git status`, `git diff`, `git log` only.
- If an acceptance test and this brief seem to disagree, stop and report it; do not edit the test.
- The frozen `minimal-code.mdc` is in force: fix each defect where it is; a form outside the grammar is refused, never read by a special case. This never overrides a security requirement.
- Rules in force: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc`, the frozen `minimal-code.mdc`. ASVS level 2.
- **Known failures.** At this brief's commit, on round 5's code, `tests/test_program_permission_guard.py tests/test_allowlist.py` give `71 failed, 587 passed, 20 skipped in 170.49s`: every one of the 71 in the acceptance file's section "round 5's findings" (the forms Review A and the security audit found), none in `tests/test_allowlist.py`. No other failure is known.
- Mutation is the supervisor's, after your run.

## Done
Your report is `handoff/TASK-063-r6-report.md`, written as you go, naming no computer path (`<Workspace>`, `~`; also in quoted command output). When you finish it holds: every file you changed; a one-paragraph summary; for each requirement (1 to 17) one sentence naming the function or line that meets it; each test case of `tests/test_permission_guard.py` and `tests/test_permission_guard_a4.py` you added or changed, by name, with its form; every command below with its output verbatim in a fenced block, each pytest summary line quoted verbatim; `Mutations: not run (the supervisor's)`; and a last section headed exactly `Assumed, not verified` (one item per line: what I assumed · why · what would confirm it).

Run these from the Workspace root, in this order, after your last edit, each in the foreground:
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check`
3. `python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py tests/test_review_guard.py tests/test_release_s_records_gate.py`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
5. `git diff --stat HEAD`
6. `git rev-parse HEAD` and `git status --short`

Your last message is the summary and the report file's path, and nothing follows it.
