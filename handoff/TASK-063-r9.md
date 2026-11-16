---
record: brief
header: 1
id: "TASK-063"
round: 9
satisfies: [R-082]
scope: ["bridge/cursor-bridge/permission-guard.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_permission_guard.py", "tests/test_permission_guard_a4.py", "docs/BUILDER_NOTES.md", "handoff/TASK-063-r9-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-063, round 9: arguments an MSYS program parses again, powershell.exe's trimmed arguments, and environment that runs code (R-082)

Round cause: security

Blocking class: security - the security audit, round 8, B7: ssh-agent runs its arguments as a command and is not a refused launcher (ssh-agent git worktree remove y passes, as it does on round 7's tree and at the checkpoint fae0860)

Satisfies: R-082 - the permission guard reads a command as the shell does; the full text stands in round 1's brief, and the design is the flat grammar decided by the second resolution round (docs/CHANGES.md, 2026-11-15 TASK-063).

## Objective
Round 8 fixed every finding of round 7. Review A approved it with no blocking finding, after a differential fuzz and regression sweeps against round 7 and fae0860. The security audit confirmed every round-7 finding closed and found seven defects that were already in round 7 and at fae0860. **This round fixes those seven in round 8's code and changes nothing else.** Round 8's code (this brief's commit) is your starting tree: keep its structure, its function names and its passing behaviour. `handoff/TASK-063-r5.md` to `handoff/TASK-063-r8.md` stay in force; this brief governs where they seem to differ. Read r8 whole first, then r5 to r7 as you need them.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_permission_guard.py
- tests/test_permission_guard_a4.py
- docs/BUILDER_NOTES.md
- handoff/TASK-063-r9-report.md

Limits:
- The limits of `handoff/TASK-063-r5.md`'s Scope section apply unchanged (`main()`'s shape, the constants that never shrink, the generated files only as regenerated, an existing case changed only as they allow; no case that expects a refusal is removed or changed to accept a pass). An existing case that expects a pass and that requirement 1 to 7 makes unreadable changes to expect a refusal whose reason holds `cannot read`, under the tool concerned only; list each in the report with the requirement. Known: `test_allowed[PowerShell-find . -name '*.pyc' -delete]` in `tests/test_permission_guard.py` (requirement 1: `'*.pyc'` reaches find's MSYS runtime, which globs it; the Bash instance keeps its pass, so split the case). `ssh-agent -s` keeps its pass under both tools (requirement 7).

Do not modify anything else.

## Out of scope
- Everything the Out of scope sections of rounds 5 to 8 list, unchanged.
- `tests/test_program_permission_guard.py`, `tests/test_allowlist.py` and `tests/test_task032_supervisor_guard.py`: the supervisor's; edit nothing in them. The acceptance file's section headed "round 8's findings" holds this round's forms.
- Response files (`env @args.txt`) and globs that need a matching file are not a finding of this round (requirement 1 refuses a word beginning `@` or holding a glob character anyway); the cmd builtin rule behind a prefix (`cmd //c env call ...`: env.exe finds no such program); `exec 0<file` before a stdin-reading shell (the input is a file); `gh pr view <n> --json a,b` refused under the PowerShell tool by round 8's comma rule (5.1 splits it).

## Requirements
Line numbers are round 8's.

1. **Words an MSYS program parses again** (`_read_powershell` `emit_word` lines 1163-1200, the prefix walk lines 516-621, `_check_word_list` lines 2046-2077). A program of Git for Windows' MSYS runtime (`env`, `nice`, `nohup`, `stdbuf`, `timeout`, `setsid`, `sudo`, `bash`, `sh`, `find`, and the launchers already refused) started by a native parent (PowerShell or cmd) parses its own command line again: `'` acts as a quote, `''` is removed, braces are expanded, `*`, `?`, `[` and `~` are globbed, and `\\` inside quotes becomes `\`. So, under the PowerShell reading and the cmd reading, every word after such a program's name in the same command (its options, the inner command's words, a `bash`/`sh` command string, a `find` clause) is unreadable when it holds `'`, `"`, `{`, `}`, `*`, `?`, `[` or `]`, or holds `\` together with a blank, a tab, a carriage return or a new line, or begins with `~` or `@`. The rule attaches to the command word and to each prefix the walk crosses; in the cmd mode, where there is no prefix walk (round 8 requirement 5), it attaches to the first word. Under the bash reading the rule applies only to a `bash` or `sh` whose command word holds `/` or `\` and does not begin `/usr/bin/` or `/bin/` (Git's `bin\bash.exe` and `bin\sh.exe` are native launchers that hand their command line to `usr\bin\bash.exe`, which parses it again: `/c/PROGRA~1/Git/bin/bash.exe -c 'echo \\\; git worktree remove y'`); bash starts every other listed program as an MSYS child, which receives its arguments without a second parse.

2. **powershell.exe trims its arguments and skips empty ones** (`_ps_switch_walk` lines 673-704, `_ps_is_switch` lines 662-670). Every argument word of a `powershell` or `pwsh` wrapper (its switches, their values and the words of its inner command) that is empty, or begins or ends with whitespace, is unreadable, under either tool and at any depth: `powershell '' -Command <command>`, `powershell ' -Command' <command>`, `powershell ' ' -c <command>`, `echo x | powershell ' '` and `powershell -Command ''` are unreadable.

3. **env's and sudo's assignments** (`_walk_env` lines 361-392, and the words after `sudo` and its options). In `env`'s words and in the words after `sudo`, any word that does not begin with `-` and holds `=` is an assignment, never the command word; an assignment whose name (the part before the first `=`) is not `[A-Za-z_][A-Za-z0-9_]*` is unreadable (`env X.Y=1 <command>`, `env 'a b=1' <command>`, `env 'BASH_FUNC_echo%%=...'`). An assignment with a valid name is read as every leading assignment is (round 7 and round 8 rules apply: `HUSKY=0`, the `GIT_CONFIG` refusal, and requirement 4).

4. **Environment that makes a child bash run code** (`_take_assignments` lines 502-513, `_walk_env` lines 368-375). An assignment, anywhere it is read (leading assignments, `env`'s words, after `sudo`, at any depth, including a `bash`/`sh` command string's own assignments such as `bash -xc 'PS4=...; true'`), whose name, compared without regard to case, is `BASH_ENV`, `ENV`, `PS4`, `SHELLOPTS`, `BASHOPTS` or `PROMPT_COMMAND`, or begins with `BASH_FUNC_`, is unreadable. An assignment to `LANG`, `LC_ALL` or `LC_CTYPE` (any case) is unreadable unless its value is `C`, `POSIX`, or ends in `.UTF-8` or `.utf8` (any case): a locale with a multibyte charset (Big5, GBK, Shift JIS) makes the child bash decode its string so that a lead byte swallows a following `\` (`LC_ALL=zh_TW.BIG5 bash -c ...`); `LANG=C git log` and `LC_ALL=en_US.UTF-8 git status` pass.

5. **Git Bash's path-list conversion before powershell.exe** (`_check_word_list` lines 2054-2064, `shell_inner` lines 1904-1912). Git Bash rewrites an argument that looks like a POSIX path list (`/tmp:/c/x`, `x=/a:/b`) into a Windows list joined by `;`, and powershell.exe runs that `;` as a statement separator. In a `powershell`/`pwsh` inner command read with `slash_ok` false (round 8's requirement 2), a word holding both `/` and `:` is unreadable. This refuses more than the conversion touches (Git Bash leaves `C:/x` and `https://...` alone), which is accepted: no existing case is affected.

6. **A `find` clause whose program is the found file** (`_find_clauses` lines 1653-1690, `_check_word_list` lines 2067-2077). A clause is unreadable when, at any depth beneath it, `{}` stands as or within a command word (the clause's own after the prefix walk, a `bash`/`sh` command string's, an `eval`'s, a `cmd` or `powershell` inner command's), or when any of its words holds `{}` without being exactly `{}` (GNU find replaces `{}` inside an argument of `-exec ... ;`): `find /c/PROGRA~1/Git/cmd -name git.exe -exec {} worktree remove y ';'`, `... -exec env {} ...` and `... -exec bash -c '{} worktree remove y' ';'` are unreadable; `-exec echo {} +`, `-exec rm {} ;` and `-exec echo {} ';'` keep their passes.

7. **More launchers.** Under either tool (with or without `.exe`):
   - `gpg-agent`, `gpg-connect-agent`, `rundll32`, `pcalua`, `runas` and `wmic` are refused as a command word, as round 7's launchers are;
   - `ssh-agent` is readable only with options of its own table and no command (`-a` and `-E`, `-P`, `-t`, `-O` with a value, glued or not; `-c`, `-s`, `-D`, `-d`, `-k`); a word after its options (the command it would run) is unreadable: `ssh-agent -s` passes, `ssh-agent git worktree remove y` is unreadable;
   - `ssh` with an `-o` option (the value glued, `-oKey=...`, or the next word) whose key, compared without regard to case before the first `=` or blank, is `ProxyCommand`, `LocalCommand`, `PermitLocalCommand` or `KnownHostsCommand` is unreadable; `ssh -o BatchMode=yes git@github.com` passes.

8. **`chain_reason`'s default.** `chain_reason(command, cwd, tool="Bash", outermost=True, *, slash_ok)`: `slash_ok` keyword-only, with no default (round 8 computes it from the tool when it is left out, lines 1808-1809; no caller leaves it out).

9. **Your own cases**, each naming R-082, in `tests/test_permission_guard_a4.py`: at least one per requirement 1 to 7, each failing on round 8's code (this brief's commit) and passing on yours, each refusal asserting the key words of its own reason (the form, not only `cannot read`); the report names each case and states why it fails on round 8's code. A timing assertion allows for the interpreter's start-up (assert the check's own time, not the subprocess's). Every subprocess call in a test you add or change passes `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` on the same line and a timeout.

## Acceptance criteria
- [ ] Every test in `tests/test_program_permission_guard.py` passes, the file unchanged.
- [ ] Every test in `tests/test_allowlist.py`, `tests/test_task032_supervisor_guard.py`, `tests/test_review_guard.py` and `tests/test_release_s_records_gate.py` passes, unchanged; every test in `tests/test_permission_guard.py` and `tests/test_permission_guard_a4.py` passes, changed only as the Scope's Limits allow.
- [ ] Your cases of requirement 9 pass, name R-082, and are listed in the report.
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
- **Known failures.** At this brief's commit, on round 8's code, `tests/test_program_permission_guard.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py` give `42 failed, 923 passed, 20 skipped in 178.07s`: every one of the 42 in the acceptance file's section "round 8's findings", each a form round 8 lets through; none in the other two files. No other failure is known.
- Mutation is the supervisor's, after your run.

## Done
Your report is `handoff/TASK-063-r9-report.md`, written as you go, naming no computer path (`<Workspace>`, `~`; also in quoted command output). When you finish it holds: every file you changed; a one-paragraph summary; for each requirement (1 to 9) one sentence naming the function or line that meets it; each test case of `tests/test_permission_guard.py` and `tests/test_permission_guard_a4.py` you added or changed, by name, with its form; every command below with its output verbatim in a fenced block, each pytest summary line quoted verbatim; `Mutations: not run (the supervisor's)`; and a last section headed exactly `Assumed, not verified` (one item per line: what I assumed · why · what would confirm it).

Run these from the Workspace root, in this order, after your last edit, each in the foreground:
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check`
3. `python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py tests/test_review_guard.py tests/test_release_s_records_gate.py`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
5. `git diff --stat HEAD`
6. `git rev-parse HEAD` and `git status --short`

Your last message is the summary and the report file's path, and nothing follows it.
