---
record: brief
header: 1
id: "TASK-063"
round: 8
satisfies: [R-082]
scope: ["bridge/cursor-bridge/permission-guard.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_permission_guard.py", "tests/test_permission_guard_a4.py", "docs/BUILDER_NOTES.md", "handoff/TASK-063-r8-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-063, round 8: shells reading standard input, PowerShell's words and switches, and the last linear-time gaps (R-082)

Round cause: security

Blocking class: security - the security audit, round 7, B4: powershell.exe 5.1 does not know -settingsfile and runs the text after it as commands, while the guard skips it as a value switch (powershell -settingsfile 'x; git worktree remove y;' echo passes, as it does on round 6's tree and at the checkpoint fae0860)

Satisfies: R-082 - the permission guard reads a command as the shell does; the full text stands in round 1's brief, and the design is the flat grammar decided by the second resolution round (docs/CHANGES.md, 2026-11-15 TASK-063).

## Objective
Round 7 fixed every finding of round 6; both reviewers confirmed it, and Review A ran your sixteen cases against round 6's guard (all sixteen failed there, as they should). They found defects that were already in round 6: shells that read their commands from standard input, Windows PowerShell 5.1 splitting or re-joining a native program's arguments in three more ways, PowerShell switches 5.1 does not know, the single-slash rule recomputed at each depth, the cmd mode's prefix walk, one `find` option that takes two words, and a regular expression that runs past the hook's time. **This round fixes those defects in round 7's code and changes nothing else.** Round 7's code (this brief's commit) is your starting tree: keep its structure, its function names and its passing behaviour. `handoff/TASK-063-r5.md`, `handoff/TASK-063-r6.md` and `handoff/TASK-063-r7.md` stay in force; this brief adds precision where round 7's code went wrong, and where they seem to differ, this brief governs. Read all three whole first.

Where this brief narrows the PowerShell reading (requirement 3), it does so by refusing a whole kind of word rather than modelling one more of PowerShell 5.1's splitting rules: the guard reads a word only when its form leaves no doubt what the program receives.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_permission_guard.py
- tests/test_permission_guard_a4.py
- docs/BUILDER_NOTES.md
- handoff/TASK-063-r8-report.md

Limits:
- The limits of `handoff/TASK-063-r5.md`'s Scope section apply unchanged (`main()`'s shape, the constants that never shrink, the generated files only as regenerated, an existing case changed only as they allow; no case that expects a refusal is removed or changed to accept a pass). An existing PowerShell case that expects a pass and that requirement 3 or 4 makes unreadable changes to expect a refusal whose reason holds `cannot read`; list each in the report.

Do not modify anything else.

## Out of scope
- Everything the Out of scope sections of rounds 5 to 7 list, unchanged.
- `tests/test_program_permission_guard.py`, `tests/test_allowlist.py` and `tests/test_task032_supervisor_guard.py`: the supervisor's; read them; edit nothing in them. The acceptance file's section headed "round 7's findings" holds this round's forms; the supervisor moved `echo a'b c'` from the round-7 PowerShell passes to this section's unreadable forms.
- `-ok`/`-okdir` ending at `{} +` (GNU find ends them only at `;`; the guard's reading refuses more, no path); `git stash show stash@{0}` and `gh api repos/{owner}/{repo}/...` unreadable under PowerShell (round 5's brace and splat rules; refuses more).

## Context
- `handoff/TASK-063-r5.md`, `r6.md` and `r7.md`: the grammar and the fixes so far.
- `tests/test_program_permission_guard.py`: the acceptance file; its last section is this round's.

## Requirements
Line numbers are round 7's.

1. **Shells that read their commands from standard input are unreadable**, under either tool, at any depth:
   - `powershell`/`pwsh`: a `-command` switch (or any prefix of it, `-c` and longer) whose next word is `-` or that has no word after it; a `-file`/`-f` switch whose next word is `-`; and a `powershell` whose switches are followed by no command and no file (nothing left to run, so it reads standard input) (`_ps_switch_walk` lines 691-700, `shell_inner` line 1757);
   - `cmd`: the `/k` switch in every spelling (`/k`, `//k`, any case): cmd runs its command and then stays reading standard input (`CMD_OK_SWITCH`, `_cmd_switch_walk`);
   - `bash`/`sh` with a script word: unreadable, whatever the script's path, when its standard input is fed by the command line: it is a later stage of a pipeline in any reading (bash, PowerShell and cmd alike: the PowerShell and cmd readers mark later stages as the bash reader does; round 7 sets `"pipe": False` at lines 1198 and 1473), or it carries an input redirection (`<`, `<>`, `<&`, with or without a descriptor number), or it is reached at any depth through a re-read (a `bash`/`sh` command string, `eval`, a prefix wrapper, a `find` clause, a `cmd` or `powershell` inner command) of a command that is a later stage or carries an input redirection; the flag is passed down like `slash_ok` (requirement 2). So `echo x | env -C / bash dev/stdin` (under either tool), `... | env --chdir=/proc/self/fd bash 0`, `bash x.sh < cmds.txt`, `echo x | bash -c 'env -C / bash dev/stdin'` and `echo x | find / -maxdepth 0 -execdir bash dev/stdin ';'` are unreadable; round 7's absolute-path rule (requirement 8) stays.

2. **The single-slash rule is decided once, by the caller** (`_check_one` line 1836, also lines 1633, 1684 and 1900). `slash_ok` is a parameter passed down every re-read and never recomputed from the tool: it starts true only under the PowerShell tool in the PowerShell reading, and becomes false, for everything beneath, once a `bash`/`sh` command string, an `eval`, a `find` clause or a prefix wrapper is crossed; a `powershell` inner command inherits its caller's value. A `cmd` inner command's own words are read with false, as in round 7, and a `powershell` inner command beneath it is read with false too (cmd passes `/c` on unchanged, but the single-slash spelling is read only at the top of the PowerShell tool). `_command_changes` and `_chain_from_words` pass it the same way. So, under the PowerShell tool, `echo x | env powershell -c cmd /c echo hi`, `echo x | bash -c 'powershell -Command cmd /c echo hi'`, `find . -exec powershell -c cmd /c git status ';'` and `cmd /c powershell -Command cmd /c echo hi` are unreadable.

3. **PowerShell words** (`_read_powershell` lines 1147-1179, 1306-1316, 1386-1394). Under the PowerShell reading, in addition to round 7's requirement 4:
   - a quoted part is readable only as the whole word: a word holding a quote anywhere but at its first character, or continuing after its closing quote, is unreadable (PowerShell 5.1 splits `.'worktree'` into `.` and `worktree`, and `-x:'n'worktree` into `-x:n` and `worktree`); so `echo a'b c'`, `git -C .'worktree' remove y` and `git --namespace -x:'n'worktree remove y` are unreadable, and `git -C 'a b' status` passes. A doubled quote inside a quoted part (`'it''s'`) is a literal character of that part, not a quote; a leading call-operator `&` or `.` standing as its own word (round 5) is not part of the next word;
   - a word whose value (after quote removal) holds a blank, a tab, a carriage return or a new line and ends in a backslash is unreadable (5.1 wraps such a word in double quotes without doubling a trailing backslash, which then escapes the closing quote: `git push origin 'x \' 'y --force z'` hands git `x " y`, `--force`, `z`); a backslash elsewhere stays readable (`Get-ChildItem 'C:\dir'`, `cursor-agent -p "Read .\handoff\TASK-001.md"`);
   - an unquoted `,` anywhere is unreadable (the comma operator: `git --no-pager ,worktree remove y` hands git `worktree`).

4. **PowerShell value switches 5.1 knows** (`PS_VALUE_SWITCHES` lines 73-74, `_ps_switch_walk` lines 698-700). The switches that take a value are exactly `-executionpolicy`, `-ep`, `-ex`, `-windowstyle`, `-w`, `-inputformat`, `-if`, `-outputformat`, `-of` (compared whole, in lower case, after the prefix normalisation of round 5). Every other switch outside round 5's and round 7's tables is unreadable, among them `-settings`, `-settingsfile`, `-psc`, `-psconsolefile`, `-v`, `-version`, `-wd`, `-workingdirectory`, `-config`, `-configurationname` (5.1 runs the text after an unknown switch as commands, or goes interactive and reads standard input).

5. **The cmd mode takes no prefixes** (`_walk_to_command` lines 528-597, `_read_cmd` `close_cmd` lines 1467-1472). In the cmd mode there are no assignments and no prefix wrappers: the first word of every command is its command word, and the cmd command-word rules of round 7's requirement 2 (the character rule and the builtin rule, without `base()` or `_exe_stem`) apply to it. So `cmd //c powershell/command git status`, `cmd //c start/b/env git status` and `cmd //c call/nohup git status` are unreadable. The later checks of each cmd command (the refused actions, rule 8, the launchers) still see through the prefixes, because cmd runs Git's `env.exe` and the like as programs: `cmd //c env git worktree remove y` stays refused, its reason naming `worktree`.

6. **`find`'s options and their values** (`_FIND_TAKES_ARG` lines 82-88, `_find_clauses` lines 1607-1609). `-fprintf` takes two words; `-newerXY` (any two letters after `-newer`) and `-files0-from` take one; a bare `-O` takes none (its level is glued, `-O3`). And an `-exec`, `-execdir`, `-ok` or `-okdir` word that is consumed as an option's value makes the command unreadable (so a table error refuses, never passes): round 7's `find . -maxdepth 0 -name -exec -o -exec <command> ';'` is unreadable. With `-fprintf` taking two words, `find . -maxdepth 0 -fprintf out.txt -name -exec git worktree remove y ';'` starts a real clause at its `-exec` and is refused as the removal (`worktree` in the reason).

7. **No regular expression across the joined command** (line 1868, the `HUSKY=0` rule; line 1922, the alias rule). Replace each by two linear searches with no `.*`. For `HUSKY=0`: find the first match of `\bgit\b` (case-insensitive) in that command's words joined with a blank, then search `\b(commit|push|merge)\b` in the text after that match's end (so `git` and `commit` inside one word, as in `HUSKY=0 bash -c 'git commit -m x'` and `HUSKY=0 python -c "import os; os.system('git commit -m x')"`, still refuse). For the alias rule, keep `worktree\s+remove|pr\s+merge` and replace `push\b.*(...)` by the first match of `push\b`, then a search for `--forc|-f\b|\+` after it. Each gives round 7's result on every input within one line. Likewise, no regular expression with two adjacent unbounded repeats that can match the same characters runs over the agent's text: `ALIAS_RX` (line 69: the value after `=`, stripped of leading blanks and one optional quote, then compared by prefix) and the short-flag tests at lines 1989 and 2043 (a word beginning `-` whose remaining characters are all ASCII letters, holding `n` or `f` respectively) are rewritten as linear tests with the same results. `_too_long()` is tested after each such check. The acceptance file's long `HUSKY=0` form, long alias value and long short flag are each refused for the removal (`worktree` in the reason) within the hook's time.

8. **The deadline test by counter** (lines 867, 1254, 1486). Each reader tests `_too_long()` when its position reaches a next-check mark, then moves the mark 4096 characters on; a step of two characters never skips a test.

9. **Dead code.** Delete `_skip_assignments`, `_bash_interactive` and `_wrapper_opt_refusal` if nothing calls them.

10. **Your own cases**, each naming R-082, in `tests/test_permission_guard_a4.py`: at least one per requirement 1 to 8, each failing on round 7's code (this brief's commit) and passing on yours; the report names each case and states why it fails on round 7's code. Every refusal case asserts the reason's key words. Every subprocess call in a test you add or change passes `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` on the same line and a timeout (round 7 added two tests in `tests/test_permission_guard.py` through `run()`, which passes neither; `tests/test_permission_guard_a4.py`'s `run()` at lines 16-20 passes neither either: give both `run()` helpers both).

## Acceptance criteria
- [ ] Every test in `tests/test_program_permission_guard.py` passes, the file unchanged.
- [ ] Every test in `tests/test_allowlist.py`, `tests/test_task032_supervisor_guard.py`, `tests/test_review_guard.py` and `tests/test_release_s_records_gate.py` passes, unchanged; every test in `tests/test_permission_guard.py` and `tests/test_permission_guard_a4.py` passes, changed only as the Scope's Limits allow.
- [ ] Your cases of requirement 10 pass, name R-082, and are listed in the report.
- [ ] The report states, for requirement 2, that `slash_ok` is never computed from the tool below the first reading, and for requirement 7, that no `.*` regular expression runs over a whole command.
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
- **Known failures.** At this brief's commit, on round 7's code, `tests/test_program_permission_guard.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py` give `37 failed, 876 passed, 20 skipped in 215.71s`: every one of the 37 in the acceptance file's section "round 7's findings", none in the other two files. No other failure is known.
- Mutation is the supervisor's, after your run.

## Done
Your report is `handoff/TASK-063-r8-report.md`, written as you go, naming no computer path (`<Workspace>`, `~`; also in quoted command output). When you finish it holds: every file you changed; a one-paragraph summary; for each requirement (1 to 10) one sentence naming the function or line that meets it; each test case of `tests/test_permission_guard.py` and `tests/test_permission_guard_a4.py` you added or changed, by name, with its form; every command below with its output verbatim in a fenced block, each pytest summary line quoted verbatim; `Mutations: not run (the supervisor's)`; and a last section headed exactly `Assumed, not verified` (one item per line: what I assumed · why · what would confirm it).

Run these from the Workspace root, in this order, after your last edit, each in the foreground:
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check`
3. `python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py tests/test_review_guard.py tests/test_release_s_records_gate.py`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
5. `git diff --stat HEAD`
6. `git rev-parse HEAD` and `git status --short`

Your last message is the summary and the report file's path, and nothing follows it.
