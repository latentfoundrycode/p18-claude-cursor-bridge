---
record: brief
header: 1
id: "TASK-063"
round: 7
satisfies: [R-082]
scope: ["bridge/cursor-bridge/permission-guard.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_permission_guard.py", "tests/test_permission_guard_a4.py", "docs/BUILDER_NOTES.md", "handoff/TASK-063-r7-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-063, round 7: the wrappers' second readings, PowerShell's argument passing, and cmd's command names (R-082)

Round cause: security

Blocking class: security - the security audit, round 6, B3: cmd ends a command name at ; , = @ and so runs a refused command the guard reads as an argument (cmd //c 'call;git worktree remove y' passes, as it does on round 5's and round 4's trees and at the checkpoint fae0860)

Satisfies: R-082 - the permission guard reads a command as the shell does; the full text stands in round 1's brief, and the design is the flat grammar decided by the second resolution round (docs/CHANGES.md, 2026-11-15 TASK-063).

## Objective
Round 6 fixed every finding of round 5; both reviewers confirmed it. They found new defects in four places: the wrappers whose inner command is read a second time from joined text (`find` clauses, `cmd /c`), the way Windows PowerShell 5.1 hands arguments to a native program, the way cmd ends a command name, and a handful of single checks (`bash +c`, the stdin path, a carriage return, a PowerShell switch with a glued value, rule 8 behind a wrapper). **This round fixes those defects in round 6's code and changes nothing else.** Round 6's code (this brief's commit) is your starting tree: keep its structure, its function names and its passing behaviour, and do not rewrite the reader. `handoff/TASK-063-r5.md` and `handoff/TASK-063-r6.md` stay in force; this brief adds precision where round 6's code went wrong, and where they seem to differ, this brief governs. Read both whole first, then `docs/CHANGES.md` (the entry "2026-11-15 TASK-063: second resolution round").

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_permission_guard.py
- tests/test_permission_guard_a4.py
- docs/BUILDER_NOTES.md
- handoff/TASK-063-r7-report.md

Limits:
- The limits of `handoff/TASK-063-r5.md`'s Scope section apply unchanged (`main()`'s shape, the constants that never shrink, the generated files only as regenerated, an existing case changed only as they allow; no case that expects a refusal is removed or changed to accept a pass).
- Requirement 6 makes `cmd /c ...` under the Bash tool unreadable: the cases of `test_allowed` in `tests/test_permission_guard.py` that pass `cmd /c echo agent` and `cmd /c dir agent` under both tools keep passing under PowerShell and, under Bash, change to expect a refusal whose reason holds `cannot read`; add the `cmd //c` spelling of each as a Bash pass. Requirement 4 makes the PowerShell case of `test_allowed`'s `gh api graphql -f query='query { repository(owner: "o", ...'` (line 160) unreadable: that PowerShell case changes to expect a refusal whose reason holds `cannot read`, and its Bash case stays a pass. In `tests/test_permission_guard_a4.py`, the `_R6_WRAPPERS` cmd row's pass `cmd /c git status` (line 303) becomes `cmd //c git status`, and `test_r082_req10_cmd_reads_every_switch_and_redirection` (line 380) uses `cmd //q //c git '>out' worktree remove z` in place of `cmd /q /c "git >out worktree remove z"`, still asserting `worktree`.

Do not modify anything else.

## Out of scope
- Everything round 5's and round 6's Out of scope sections list, unchanged.
- `tests/test_program_permission_guard.py` and `tests/test_allowlist.py`: the supervisor's; read both whole; edit nothing in them. The acceptance file's section headed "round 6's findings" holds this round's forms.
- `git merge --no-verify -m 'checkpoint before TASK-001'` passing as a checkpoint (older than this increment; recorded for later).

## Context
- `handoff/TASK-063-r5.md` and `handoff/TASK-063-r6.md`: the grammar and round 6's fixes.
- `docs/CHANGES.md`, the entry "2026-11-15 TASK-063: second resolution round": the decision.
- `tests/test_program_permission_guard.py`: the acceptance file; its last section is this round's.

## Requirements
Line numbers are round 6's.

1. **A `find` clause is checked as the word list it is** (`_check_one` lines 1641-1656, `_chain_lists` lines 1464-1472). Each `-exec`, `-execdir`, `-ok` or `-okdir` clause is the words after it up to its own `;` word, or a `+` word directly after a `{}` word (or the end of the words), with every word kept in its place (`{}` stays a word: find puts the file name there, so `-C {}` gives `-C` a value); it is checked once, as that list of words, exactly as a command the reader produced is checked (the command-word refusals, the prefix walk, every check of `_check_one`), never joined into text and read again. Clauses do not overlap: the words after a clause's terminator are read for the next clause. An `-exec`, `-execdir`, `-ok` or `-okdir` word inside a clause (before its terminator) makes the command unreadable, unless that clause's command word is `find`, whose own clauses are read when that clause is checked. A find option such as `-name` takes the next word as its value, so `find . -name -exec -o -exec <command> ';'` runs the second clause: an `-exec` word that is an option's value starts no clause, and the word after it does not end one. So `find . -maxdepth 0 -exec git -C '' worktree remove y ';'` is refused (git's `-C` takes the empty word), and so are the acceptance file's three other quoted forms, and the nested and long `find` forms finish within the hook's time.

2. **cmd: a command name ends where cmd ends it** (`_read_cmd` lines 1274-1394, `_walk_to_command` line 456). In the cmd mode:
   - any of `@`, `;`, `,` and `=` anywhere in the inner command is unreadable (cmd ends a command name at each, and `@` before a name hides its echo);
   - a command word holding any character other than a letter, a digit, `-`, `_` and `.` is unreadable (cmd ends a builtin's name at `/`, `+`, `[`, `]` and others: `start/b` is `start /b`);
   - no `NAME=` word is ever taken as an assignment in the cmd mode (cmd has none);
   - the cmd builtin rule (only `dir`, `echo`, `type`, `cd` and `ver` pass) compares the command word's part before its first `.`, in lower case, without `base()` or any splitting on `/` or `\`.

3. **cmd: the inner command's words must survive joining** (`shell_inner` lines 1531-1535). The words after `/c`, `/k` or `/r` are joined with a blank, as round 5 specifies; before that join, a word that is empty or holds a blank or a tab is unreadable (the shell that starts cmd quotes such a word, and the quotes reach cmd, which the cmd mode refuses as `"`). So `cmd //c git -C '' worktree remove y` and `cmd //c git -C 'a b' worktree remove y` are unreadable.

4. **PowerShell hands arguments to a native program unescaped** (`_read_powershell` lines 1025-1047, 1182-1187, 1233, 1257-1258). Under the PowerShell reading:
   - a word that begins with a quote and continues after its closing quote is unreadable (`git 'worktree'remove y` is three arguments to Windows PowerShell 5.1; `echo 'x'#y` ends at the comment); a word that begins with plain characters and continues into a quoted part stays readable (`echo a'b c'` passes);
   - a word holding a literal `"` after quote removal is unreadable (5.1 passes it unescaped and the program splits the argument again: `git -c 'a.b=x\" worktree remove y'`, `git 'worktree""' remove y`);
   - a word that begins with a single `-` (not `--`) and holds a `.` is unreadable (5.1 splits `-f..\r` into `-f` and `..\r`);
   - an unquoted `&` after a word has started is unreadable (PowerShell 7 runs `echo a&git worktree remove y` as a background job and the removal); a quoted `&` stays readable (`echo "a & b"` passes).

5. **PowerShell's switch table is read by one walk** (`_parse_ps_wrapper` lines 601-603, `shell_inner` lines 1522-1525). A `powershell` or `pwsh` switch holding `=` is outside the table and unreadable (`-ep=Bypass`, `-wd=.`): powershell.exe does not know it and starts the command text there. `shell_inner` takes the inner command's start from the same walk `_parse_ps_wrapper` makes; there is no second reader of the switch table. A switch is a table name compared whole, or a prefix of `-command` (`-c` and longer) as round 5 says; `-file` is exactly `-f` or `-file`; a switch that only begins with a name (`-filex`, `-commandx`) is unknown and unreadable (powershell.exe 5.1 runs the text after it as commands). The encoded-command refusal (`-e`, `-ec`, `-en...`) stays as it is. `PS_VERBS` holds every verb of round 5's requirement 4, `ConvertFrom` and `ConvertTo` included (so `ConvertTo-Html` is unreadable as a cmdlet outside the list).

6. **Single-slash switches where Git Bash passes them on** (lines 565-584 and 1531). Git Bash and every MSYS program (`find` among them) rewrite a single-slash argument such as `/c` into a path (`C:/`) when they start a native program, so cmd starts with no command and runs its standard input, and powershell.exe takes `/ep` as text to run. A `cmd` switch, or a `powershell`/`pwsh` switch, spelled with one slash is read only where no Git Bash or MSYS program passes it on: under the PowerShell tool, in the PowerShell reading, with no prefix wrapper and no `find` clause before `cmd` or `powershell`. Everywhere else it is unreadable, and only `//x` (and `-x` for powershell) is read. That covers the Bash tool at any depth (a powershell wrapper's inner command included), a `bash`/`sh` command string, a `find` clause, and after `env`, `nice`, `nohup`, `stdbuf`, `timeout`, `setsid` or `sudo`.

7. **`bash +c`** (`_parse_bash_sh_words` lines 241-247). A `+` flag holding `c` is unreadable (bash runs `+c` as `-c`); `+x`, `+e` and the other letters of round 5's table stay readable.

8. **A shell reading standard input, by its path** (`_bash_reads_stdin` line 280). A `bash` or `sh` script word is unreadable when it is `-`, or when the path is absolute (begins with `/`, `\` or a drive letter) or holds a `..` part, and any of its path parts, split on `/` and `\` (empty parts and `.` dropped), is `dev` or `proc` (any case): so `/./dev/stdin`, `///dev/stdin`, `/usr/../dev/stdin` and `/proc/thread-self/fd/0` are unreadable, and `bash tools/dev/setup.sh` stays a script file.

9. **A carriage return under the bash reading** (`_read_bash` line 892). A carriage return is never a blank. Outside quotes and comments it is unreadable, except directly after a backslash (round 6's requirement 2: the escaped carriage return is a character of the word). So `echo x` CR `#; git worktree remove y` is unreadable; the acceptance file's backslash, CR, LF form stays refused.

10. **Rule 8 sees through the wrappers** (`_stage_changes` lines 1428-1434, `_chain_lists` lines 1464-1472). In a Workspace, a stage of a part changes state when its own command does, or when any command of its wrapper's re-read does: `eval`, a `bash`/`sh` command string, a `cmd` or `powershell` inner command, and a `find` clause (requirement 1's word list), at any depth. So `echo hi; eval git commit -m x` (a refusal of fae0860, which round 5's requirement 6 keeps) and the acceptance file's four other wrapper forms are refused as a chain. A lone `cd x` (one part) passes in a Workspace, as at fae0860: the `cd` rule refuses a list of two or more parts whose first part's command word is `cd`.

11. **`sudo` keeps its assignments** (`_walk_to_command`). After `sudo` and its options, leading `NAME=value` words are assignments, read as every other leading assignment (the `HUSKY=0` rule and the `GIT_CONFIG` refusal apply): `sudo HUSKY=0 git commit -m x` is refused.

12. **More launchers refused under either tool.** Add `forfiles`, `conhost`, `schtasks`, `chroot`, `wt`, `git-bash` and `git-cmd` to the launchers round 5's requirement 3 refuses as a command word (with or without `.exe`).

13. **A deadline inside `check`.** `check()` takes the time when it starts; the reader and the command checks test it at least once per command and once per 4096 characters read, and when 8 seconds have passed the command is refused with a reason holding `cannot read` and `too long to read in time`. It never passes a command because time ran out. The clock is a module-level name (`_clock = time.monotonic`); test the deadline in your own cases by replacing `_clock` on the module, not with a slow input and not by patching the shared `time` module. `premerge_recorded`'s git call bounds its `timeout` by the time left before the deadline (round 6 gives it 20 seconds, past the hook's 15, and a timeout there must refuse, never pass).

14. **Dead code.** Delete `_brace_in_word_ok` and `_parse_env_words` if nothing calls them.

15. **Your own cases**, each naming R-082, in `tests/test_permission_guard_a4.py`: at least one per requirement 1 to 13, **each failing on round 6's code** (this brief's commit) and passing on yours; the report names each case and states that it fails on round 6's code (you can see this only by reading round 6's code: you may not run it, so state why). Every refusal case asserts the reason's key words, not only the exit status. Among them, one case each asserting that the acceptance file's long `find` form and its nested `find` form are refused with `worktree` in the reason (not `too long`) in under 2 seconds. Every subprocess call passes `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` on the same line and a timeout.

## Acceptance criteria
- [ ] Every test in `tests/test_program_permission_guard.py` passes, the file unchanged.
- [ ] Every test in `tests/test_allowlist.py`, `tests/test_task032_supervisor_guard.py`, `tests/test_review_guard.py` and `tests/test_release_s_records_gate.py` passes, unchanged; every test in `tests/test_permission_guard.py` and `tests/test_permission_guard_a4.py` passes, changed only as the Scope's Limits allow.
- [ ] Your cases of requirement 15 pass, name R-082, and are listed in the report.
- [ ] The report states, for requirement 1, that no `find` clause is joined into text and read again, and for requirement 5, that one walk reads the PowerShell switch table.
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
- **Known failures.** At this brief's commit, on round 6's code, `tests/test_program_permission_guard.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py` give `60 failed, 813 passed, 20 skipped in 205.99s`: every one of the 60 in the acceptance file's section "round 6's findings" (the forms Review A, the security audit and the pre-launch read found), none in the other two files. The supervisor changed two commands of `tests/test_task032_supervisor_guard.py`'s `PERMISSION_REFUSED` (a `bash -c` string and a `cmd` command without the inner double quotes, `cmd //c` for `cmd /c`) so that they still reach the launcher reason under this round's rules; that file is otherwise as before. `test_r082_a_long_run_of_find_clauses_is_refused_within_the_hooks_time` passes on round 6's code on this machine at about 12 seconds, near the hook's 15; requirement 1 makes it fast. No other failure is known.
- Mutation is the supervisor's, after your run.

## Done
Your report is `handoff/TASK-063-r7-report.md`, written as you go, naming no computer path (`<Workspace>`, `~`; also in quoted command output). When you finish it holds: every file you changed; a one-paragraph summary; for each requirement (1 to 15) one sentence naming the function or line that meets it; each test case of `tests/test_permission_guard.py` and `tests/test_permission_guard_a4.py` you added or changed, by name, with its form; every command below with its output verbatim in a fenced block, each pytest summary line quoted verbatim; `Mutations: not run (the supervisor's)`; and a last section headed exactly `Assumed, not verified` (one item per line: what I assumed · why · what would confirm it).

Run these from the Workspace root, in this order, after your last edit, each in the foreground:
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check`
3. `python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py tests/test_review_guard.py tests/test_release_s_records_gate.py`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
5. `git diff --stat HEAD`
6. `git rev-parse HEAD` and `git status --short`

Your last message is the summary and the report file's path, and nothing follows it.
