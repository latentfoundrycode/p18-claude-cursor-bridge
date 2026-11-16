# ASSUMPTIONS: BUG-045, the builders' "Assumed, not verified" lists with the supervisor's dispositions

The branch's commit messages carry no `Assumptions:` section; these are the lists of the four builder reports, each with its disposition. Extra places to look, never the review's scope.

## Round 1 (handoff/BUG-045-report.md)

- The PowerShell tool's reader yields the same words as the Bash tool for these git commands. Disposition: probed by the supervisor, true: the Bash and PowerShell readings agree on 17 forms (round 1's acceptance).

## Round 2 (handoff/BUG-045-r2-report.md)

- git's handling of a glued `-Csub` or `-ccolor.ui=never`. Disposition: probed by the supervisor on git 2.53: both exit 129 (unknown option), so their refusal as unreadable is harmless.
- `--attr-source` before git 2.40, `--super-prefix` on git 2.53. Disposition: the security audit checked the known lists against git 2.53; a git that does not know an option rejects it, so reading it as value-taking refuses nothing git would run.
- The PowerShell tool passes a quoted alias word whole. Disposition: superseded by round 3 (every inline alias refused on its word alone); round 3's PowerShell cases showed the PowerShell reader refuses a literal double quote first, either refusal safe.
- An alias whose first word is `commit-tree` passed round 2. Disposition: superseded by round 3 (every inline alias refused).

## Round 3 (handoff/BUG-045-r3-report.md)

- git accepts an abbreviation of `--no-verify` on `am`, `cherry-pick` and `revert`. Disposition: the refusal is the same whether or not git accepts it; where git does not, it is a safe over-refusal.
- git treats a long-option abbreviation after `--` as an option. Disposition: it does not; the guard refusing such a word after `--` is a safe over-refusal.
- Semgrep not run by the builder. Disposition: CI runs the security floor on the pull request.

## Round 4 (handoff/BUG-045-r4-report.md)

- Other digits or a `=` form inside a push short-flag cluster. Disposition: git push's only digit flags are `-4` and `-6`; any other digit is an unknown switch and git pushes nothing, and `-f=x` is rejected by git (the flag takes no value); the guard passing them refuses nothing git would run.
- A later git adding a push option beginning with `m`, making `--m` ambiguous. Disposition: the refusal would then be a safe over-refusal.
- git reading a short-flag cluster after `--` as options. Disposition: it does not; the refusal after `--` is a safe over-refusal.
