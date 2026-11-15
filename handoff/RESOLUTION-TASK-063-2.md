# TASK-063: the second resolution round (R-082)

## The question

Four builder rounds have not produced a permission guard that reads its subset of the shell correctly. How is the guard's reader to be built so that it converges: continue the round-4 code, rebuild the same subset from scratch, or shrink the subset to a flat grammar?

## Why a second round

The first resolution round (docs/CHANGES.md, 2026-11-15 TASK-063: resolution round; handoff/RESOLUTION-TASK-063.md) decided design B: the guard reads a defined subset of the shell's grammar exactly, as a positive grammar, and refuses every other command as unreadable with a reason holding `cannot read`. That subset kept nested constructs: command substitution `$(...)` and process substitution, backtick bodies, top-level subshells, here-documents (plain or quoted delimiter, at top level or inside `$(`, a shell reading the body), `$'...'` and `$"..."` words, comments, the full redirection set, and rule 8 read per list (the top level, each substitution body, each subshell body).

- Round 3 (handoff/TASK-063-r3.md) ran to the launcher's two-hour limit and left 30 failing tests.
- Round 4 (handoff/TASK-063-r4.md, lifted above the ceiling by a class line) made all 30 green in 23 minutes: 968 passed, 20 skipped on the Done command. Then Review A found 17 blocking findings and the security audit 10, several of them regressions of refusals round 3 or the checkpoint fae0860 made. It is the third round that regressed something already passing (rounds 1, 2 and 4).

Round 4's code is at this file's commit: bridge/cursor-bridge/permission-guard.py, `read_shell` (about 870 lines of nested closures) and its callers.

## The findings on round 4 (R = git worktree remove ../Worktrees/TASK-012; NL = a new line)

Security audit:
- S1, new in round 4: in a Workspace, `FOO=bar && git push --force origin main` raises IndexError in chain_reason, exit 1, the hook's fail-open path.
- S2, new in round 4: strip_prefix lost `{` and `}`, so `{ git worktree remove /tmp/wt; }` passes.
- S3: a substitution's body is fed back into the parent's words, so `GH_TOKEN=$(cat t) gh pr merge 12 --squash` and `git -C $(git rev-parse --show-toplevel) push --force origin main` pass.
- S4: the `$(` state lacks the top-level unreadable checks, and iter_commands skips an unreadable body silently: `echo $(echo $((1)); R)` passes.
- S5: an unquoted `(` not at a command's start is read as a word character: under PowerShell `Write-Output (R)` and `@(R)` pass.
- S6: a redirection target starting with a quote or `$(` is left as a word: `git worktree >"x" remove ../Worktrees/TASK-012` passes.
- S7: commit_message is given the whole line, so a here-document in another command's substitution becomes the checkpoint subject.
- S8: per-commit and per-`{` re-reads are quadratic: 1000 substitutions and 1000 commits take 152 s, past the hook's 15-second timeout.
- S9: `gh api -X POST graphql -F query=@q.graphql` passes (-X, --method and -H take a value).
- S10: `coproc`, a PowerShell assignment `$x = R`, `iex 'R'`, and `1 | % { R }` pass.

Review A:
- B1, B2, B17: iter_commands skips a body past the bound and an unreadable shell-read body silently: `bash <<'EOF'` NL `case x in x) R;; esac` NL `EOF` passes, and so does R 70 nested bash here-documents deep. Its depth counter is separate from check's.
- B3, B4: scan_unquoted_hd_body is a second quote scanner that cuts `$(` by counting parentheses and treats quotes as quotes in an unquoted body: `cat <<EOF` NL `'$(R)'` NL `EOF` passes.
- B5, regression: a backslash-newline inside double quotes is no longer joined: `git push "--for\` NL `ce" origin main` passes.
- B6, regression: as S2.
- B7: the words of the command holding `<<` are those of the last command on its line, and the pipe test splits text: `bash <<'EOF' | cat` with R in the body passes (a regression), as do `<<'EOF' bash` and `cat <<'EOF' | { bash; }`.
- B8: rule 8 misses lists: sub_chains_list and sub_chain_wds_list are appended in different places, the last part is copied before its flush, and a here-document command merges into the next segment: in a Workspace, `(git add -A` NL `git commit -m x)` passes (a regression).
- B9: a delimiter line with trailing blanks ends the body: `cat <<'EOF'` NL `EOF ` NL `it's` NL `EOF` NL R NL `#'` passes.
- B10: `echo $"$(R)"` passes.
- B11: `$'--force\c@x'` passes (the `\c` escape).
- B12: a quoted redirection target is read as a word, so `git push --force origin main >'--help'` passes as a help call.
- B13: under PowerShell, a backtick inside double quotes is read as a bash backtick substitution: ``git push "--f`or`ce" origin main`` passes.
- B14: under the PowerShell tool, `bash -c 'git push --fo\rce origin main'` is read the PowerShell way and passes.
- B15: `grep -n case src/app.py` is refused as a case statement.
- B16: second reads of cut text remain in about fifteen places, against round 4's requirements 1 and 9.
- Non-blocking: N1 (`X=1` refused with a false reason), N4 (a growing join at every `(`), N8 (an unclosed here-document not refused).

Every family above is in a nested construct: a substitution's body and how it rejoins its parent's words, a here-document's body and the command that holds it, backtick bodies, subshells, rule 8's per-list reading, and texts cut out and read a second time.

## The candidates

### A. A flat subset: no nested construct is readable

The guard reads only a flat grammar, in which every command is one list of complete words. Everything nested is unreadable and refused with a reason that names the form.

Under the Bash tool, readable:
- plain characters;
- single quotes;
- double quotes, in which a backslash escapes `"`, `\`, `$` and a new line (the backslash-newline removed) and `$name` or `${name}` is text;
- a backslash outside quotes escaping the next character, and a backslash-newline outside quotes and comments as a blank;
- adjacent parts making one word;
- the separators `;`, `&&`, `||`, `|`, a single `&` that is not part of a redirection, and a new line, with empty commands skipped;
- the redirection set (an optional descriptor number, then `<`, `>`, `>>`, `>|`, `<>`, `<&n`, `>&n`, `>&-`, `&>`, `&>>`) with its target a word of the same grammar, taken out of the words wherever it stands;
- a `#` that starts a word outside quotes, as a comment to the end of its line;
- leading assignments and the existing wrappers.

Under the Bash tool, unreadable:
- `$(`, `$((`, a backtick anywhere outside single quotes, `<(`, `>(`;
- any `<<` (here-documents and here-strings);
- an unquoted `(` or `)`, and a standalone `{` or `}`;
- `$'`, `$"`, and a `${` that is not `${name}`;
- an unquoted brace expansion;
- a reserved word as a command word (`if then else elif fi for while until do done case esac select function coproc time !` `[[`);
- an unclosed quote.

Under the PowerShell tool:
- Readable: plain characters; single quotes (`''` inside them); double quotes with `$name` as text; the separators `;`, `|`, `&&`, `||` and a new line; a leading `&` call operator; the redirections `>`, `>>`, `2>`, `2>&1`, `*>`; `#` comments.
- Unreadable: a backtick anywhere except as a line continuation before a new line; `$(`, `@(`, `@{`, `@'`, `@"`, `(`, `)`, `{`, `}` and `[` outside quotes; `<#`; a lone carriage return; a word beginning `$` followed by `=` (an assignment); `iex`, `Invoke-Expression`, `%`, `ForEach-Object`, `?`, `Where-Object` and `Start-Process` as a command word.
- A backslash is a plain character.

Wrappers (bash/sh -c, pwsh/powershell -Command, cmd /c, eval, find -exec, xargs, env, and the existing prefixes) read their inner string again by its own shell's rules, the bash way for bash and sh and the PowerShell way for pwsh and powershell, whichever tool carried them. They share one depth counter, refused past 64. With no bodies, the wrappers are the only nesting.

Every check (force-push, merge, worktree, hook skippers, HUSKY per simple command, graphql, the gh api `&` remedy, the launcher bypass) reads complete word lists. Rule 8 reads the one top-level list. The checkpoint subject comes from the commit's own `-m` word only. The reader is one flat loop with no stack beyond the current quote, linear by construction, and replaces read_shell whole. It is about 200 lines against about 870.

What A refuses that the current subset reads, each one rewrite for the agent:
- the app's commit form `git commit -m "$(cat <<'EOF' ...)"` and `gh pr create --body "$(cat <<'EOF' ...)"`, which become `git commit -F <file>` and `gh pr create --body-file <file>` (the bridge's instructions already use -F);
- any `$(...)` (`cd "$(git rev-parse --show-toplevel)"`, `echo $(date)`);
- `for` and `while` loops and `if` (written as separate calls, or as a script file that a reviewer reads);
- subshells and brace groups;
- under PowerShell, `(Get-Item x).Length` and script blocks.

The first resolution round's principle stands: a false refusal costs one rewrite, and a hole costs a refused action.

### B. The same subset as round 3, rebuilt from scratch

Delete round 4's reader. A new reader of round 3's subset is written from nothing against a state table the supervisor writes into the brief, every state with its accepted characters and transitions. It is built by the full roster's builder (grok-4.7-medium), which returns at 2026-11-16 00:00 UTC, with the 27 findings above added as acceptance tests. The nested constructs stay readable, and the app's commit form stays a pass.

### C. Continue round 4's code

A fifth round fixes the 27 findings in place, lifted by a class line (security).

## What the vote should engage

- Whether A's refusals cost too much: the app's commit form, `$(...)`, loops, and PowerShell's parentheses, against the bridge's own instructed commands (tests/test_allowlist.py: the 106 runnable commands, none of which holds a substitution, a backtick, `${`, a here-document or ANSI-C quoting). Does any of them hold `(`, `{`, a reserved word as a command word, or a PowerShell form A refuses?
- Whether B can converge where rounds 1 to 4 did not, given that every finding family is in a nested construct.
- Whether C can converge with B16 (second reads in about fifteen places) and B8 (rule 8's lists) structural.
- Any hole that A itself leaves: a form A reads in which bash or PowerShell runs a command that the flat word list does not show.
