# ASSUMPTIONS: TASK-083, the builders' "Assumed, not verified" lists with the supervisor's dispositions

docs/HARDENING.md, TASK-083, carries the same list. Extra places to look, never the review's scope.

## Round 1 (handoff/TASK-083-r1-report.md)

- `{owner}/{repo}` is resolved by the real gh, as `cmd_premerge`'s auto-merge line already relies on. Disposition: accepted.
- A pending commit status of a context whose rule names an app pends the context. Disposition: accepted (HARDENING, TASK-083, ruling 1: fails closed).
- The ready record's `written` is in local time, as the premerge record's is. Disposition: accepted.
- An uppercase sha from GitHub reads as a moved head. Disposition: accepted (fails closed; `head_state` takes lowercase only).
- A `value` answer from the rule reader with no contexts is CANNOT CHECK. Disposition: accepted (defensive).

## Round 2 (handoff/TASK-083-r2-report.md)

- The value-taking short options of `gh pr merge` are `-t`, `-b`, `-F`, `-A`, `-R`. Disposition: accepted (matches gh 2.97.0, the security audit of round 2).
- `-` alone is a positional. Disposition: accepted.
- gh refuses a second positional. Disposition: accepted (the guard refuses it as well).
- A glued value holding a digit or a slash is read as a positional. Disposition: accepted (fails closed).

## Round 3 (handoff/TASK-083-r3-report.md)

- No supervisor command places another option before the gh subcommand. Disposition: accepted (Review A of round 3 checked the loop's commands).
- `-h` before a subcommand is refused. Disposition: accepted.

## Round 4 (handoff/TASK-083-r4-report.md)

- Every gh command name fits `[A-Za-z0-9][A-Za-z0-9-]*`. Disposition: accepted (a name that does not is refused, the safe side).
- Aliases and extensions likewise. Disposition: accepted (the same side; HARDENING, TASK-083, lead 1).
