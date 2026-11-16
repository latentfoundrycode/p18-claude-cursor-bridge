# SCOPE: BUG-045, the permission guard's git reading (R-082), PR #173

Round cause: defect

BUG-045 is a defect found after TASK-063 merged as b05fbc8 (PR #171): a `-h` or `--help` word anywhere among git's words exempted every git refusal of the permission guard, so `git commit --no-verify -a -m -h` committed with the hooks skipped. The fix ran four builder rounds; this review reads the whole increment against origin/main (b05fbc8): `run/review/REVIEW-BUG-045-r1.diff`.

## Where the increment ends

The ruled behaviour, cumulative over the four briefs (handoff/BUG-045.md, -r2.md, -r3.md, -r4.md; the rulings in docs/debug/BUG-045.md):

1. The help exemption holds only where git can do nothing but print help: exactly one help word (`-h` or `--help`) after the subcommand, or `worktree remove` followed by exactly one help word. A help word as an option's value, after `--`, or beside other arguments exempts nothing (beside other arguments is a ruled, safe over-refusal).
2. git's global options before the subcommand are read from known lists (`_GIT_TAKES_VALUE`, `_GIT_TAKES_EQUALS`, `_GIT_FLAGS`); any other dash word there makes the subcommand unreadable, refused with a `cannot read` reason, and counted state-changing in a Workspace chain.
3. Every alias defined in the command is refused: a word of git's that begins `alias.` in any case and holds `=`.
4. A refused long option is read by any prefix git accepts: `--no-verify` from 6 characters on the hook skippers (keeping the snapshot exemption); on push `--mirror` from 3 characters and `--force`, `--force-with-lease`, `--force-if-includes` from 4, an `=value` suffix apart. A short-flag cluster holding `f` with the digits `4` or `6` is a force push.
5. `git config` naming `core.hooksPath` passes only in its three read forms (`git config core.hooksPath`, `git config --get core.hooksPath`, `git config get core.hooksPath`, the key in any case) and in `git config core.hooksPath .githooks`; every other form is refused.

Round 4's brief, Scope (quoted): files `bridge/cursor-bridge/permission-guard.py`, `bridge/cursor-bridge/MANIFEST.json` (regenerated only), `tests/test_bug045.py` (below the marker line only), `docs/BUILDER_NOTES.md`, `handoff/BUG-045-r4-report.md`; "Do not modify anything else." Out of scope (quoted in part): ".env and anything under secrets/", "CI configuration", every record under docs/, the PowerShell reader `_read_powershell` and its literal-double-quote refusal, commit's `-n` reading, "Change no existing refusal text", and the leads outside the threat model (`git -c include.path=<file>`, `git config alias.<x> "<value>"`, `--shallow-file`), each read as round 3's tree reads it.

## The threat model (docs/INVENTORY.md, Decisions, the guard's row of 2026-11-16)

Inside: a command that names a refused action in its own words, under any quoting, chain, wrapper shell, prefix, assignment or launcher the guard reads or sees through, and the guard's deadline. Outside: a deliberate reach that hides the action from that reading (code given to an interpreter, a command a program takes from an option, its configuration or the environment, a child program's second parse under a crafted runtime or locale, a path written to reach an excluded launcher). Outside input that reaches the guard: a builder's or reviewer's instruction text reaching the supervisor's shell. A finding outside the row is recorded, not blocking.

## The class lines of the rounds above the ceiling

- Round 3 (builder launched on 0344075, its brief's commit 0344075): `Blocking class: behaviour - a defeated safety mechanism, the supervisor's probe of round 2: git honours a global option at the start of an alias value, so git -c "alias.cm=-c core.hooksPath=/dev/null commit" cm -a -m x commits with the hooks off, and round 2's guard passes it (as round 1's did: no regression of round 2)`
- Round 4 (builder launched on f3277fc, its brief's commit f3277fc): `Blocking class: behaviour - a defeated safety mechanism, the security audit of round 3: git push --m origin passes and git 2.53 runs it as --mirror, a forced update, on round 3's code as on round 2's (no regression of round 3)`

Confirm or deny each against the code of the round it lifted (round 2's tree, ba7f18d's guard, for round 3; round 3's tree, f3277fc's guard, for round 4), never against the fixed code.

## The tests

- `tests/test_bug045.py` above its marker line is the supervisor's: the reproduction (round 1's section: the nine forms that passed on b05fbc8 refused, the lone help calls still passing, and the premise on git), then the sections "round 1's findings" (unknown global options, `--attr-source`, aliases for hook skippers), "round 2's findings" (every inline alias refused, accepted abbreviations of `--no-verify` and the push options, `git config` writes of `core.hooksPath`, reads still passing) and "round 3's findings" (`--m`, `--mi`, clusters `-4f`, `-f4`, `-6fu`). Below the marker: the builders' cases for each round's requirements.
- `tests/test_program_permission_guard.py`: one supervisor amendment at round 3, `test_r082_a_long_word_is_refused_for_its_removal_within_the_hooks_time`, accepting `worktree` or `alias` in the reason, since its alias case may now be refused for its alias first.
- The mutants file `run/supervisor/BUG-045-mutants.json` (13 single-line mutants over the guard, each listing every test it fails in `tests/test_bug045.py`; generator `run/supervisor/make_bug045_mutants.py`): 13 of 13 killed. The new tests against b05fbc8: 150 fail on the old code, 89 pass there (the lone help calls, the reads and the ordinary options the fix keeps).

## Expected bookkeeping and record files in the diff

`docs/BUILDER_NOTES.md`; the builders' reports `handoff/BUG-045-report.md`, `-r2-report.md`, `-r3-report.md`, `-r4-report.md`; the briefs `handoff/BUG-045.md` to `-r4.md`; the debug note `docs/debug/BUG-045.md`; the supervisor's records `docs/CHANGES.md`, `docs/HARDENING.md`, `docs/DESIGN.md`, `docs/REQUIREMENTS.md`, `docs/INVENTORY.md`, `docs/PROJECT_STATUS.md` (as it reads at this pull request's merge); `bridge/cursor-bridge/MANIFEST.json` (the guard's hash); `run/review/`.

The records also correct the supervisor's call on Review B's round-3 rejection of TASK-063 (`git worktree remove -- --help`), which was one operator of this defect: check that the correction states what happened.
