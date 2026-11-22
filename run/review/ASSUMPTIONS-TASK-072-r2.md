# Assumptions, TASK-072 (the native rebuild)

The rebuild's `Assumed, not verified` lists (handoff/TASK-072-r1-report.md, handoff/TASK-072-r2-report.md, handoff/TASK-072-r4-report.md) and the supervisor's, each with its disposition. Extra places to look, never the review's scope.

## Rebuild round 1
- A workflow triggered by both push and `schedule:` counts toward both the gate and the weekly sets -> accepted, ruling 2's letter (HARDENING, grok's lead 2).
- An empty gate set equals an empty weekly set for OK -> accepted (HARDENING, grok's lead 1).
- Several scheduled workflows that differ from the gate: the detail names the first in path order -> accepted (HARDENING R7).
- `--lockfile` with a space instead of `=` is not read -> accepted, the brief's `--lockfile=` reading; the configurator writes the `=` form (HARDENING, grok's lead 1).
- `Weekly scan:` matched case-sensitively -> accepted.
- Review A called the list thin: the first `gitdir:` line from anywhere in the file (HARDENING R4) and the reparse attribute as the literal 0x400, every reparse point read as no git folder (HARDENING R5), were not on it.

## Rebuild rounds 2 and 4
- "none". Round 4's omits the `\\?\` and `\\.\` forms, refused by round 2's two-separator line and covered by the security audit's 40 forms, and a mapped drive letter, set up by the owner, outside the trust boundary (HARDENING R10).

## The supervisor's
- Each of --local, --no-includes and the GIT_CONFIG* withholding is redundant alone on git 2.53 -> accepted, kept as defence in depth; mutant n11 drops `--local` and `--no-includes` together.
- `gitdir: NUL` reaches os.lstat as the local NUL device -> accepted, it opens nothing (HARDENING R10).
- The `/??/` refusal is wider than needed (Windows reads it as a local folder) -> accepted, harmless (HARDENING R11).
