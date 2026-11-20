# SCOPE - FIX-006 (stage P2's least-confident item 3 settled by a test)

## Where this ends
A supervisor-written test with its records; no builder run, no program change. The diff is run/review/REVIEW-FIX-006-r1.diff (`git diff origin/main HEAD`, five files); run/review/ASSUMPTIONS-FIX-006-r1.md holds the branch's assumption lists (none).

## What it settles (its specification)
docs/HARDENING.md, The program release, "Least confident (stage P2's close, 2026-11-19)", item 3: push-scan.py passes git's own option `--attr-source` (bridge/cursor-bridge/push-scan.py, the `show_options` near line 1119, placed before the `show` subcommand by `git()` near line 50), which git refuses before 2.40, so a scan there must end `CANNOT SCAN` with a reason naming the git call and exit 2, never a pass. The item's check: a test with a stand-in git refusing the option. The item's second half (`git --version` on the install's machines and CI's images, the run sheet stating the floor) is the install's, stage P4, and stays open.

## The tests and what each enforces
tests/test_p2_least_confident.py (new, 3 tests). The stand-in is a wrapper script written to pytest's tmp_path: it replaces `subprocess.run` with one that answers every command carrying `--attr-source` with exit 129 and nothing on standard output, as git before 2.40 does, every other git command running the real git, and then runs push-scan.py with runpy as `__main__`. A program named git on PATH is not used: a script of that name does not run on Windows (Python starts git by CreateProcess, which finds only an .exe). HARDENING's FIX-006 paragraph states this deviation from the item's wording.
- test_item3_a_git_refusing_attr_source_on_a_clean_range_cannot_scan_and_exits_2: R-087's "2 where git cannot be read": a clean range exits 0 with OK under the real git (control) and exits 2 with `push-scan: CANNOT SCAN - git show failed (exit 129)`, no OK and no HIT, under the stand-in.
- test_item3_a_git_refusing_attr_source_on_a_range_with_a_hit_exits_2_and_reports_no_partial_hits: a range whose second commit holds a path exits 1 with one hit under the real git (control) and exits 2 with no HIT line and no OK under the stand-in.
- test_item3_the_stand_in_refuses_only_the_attr_source_command: under the stand-in the earlier git calls still run: the output is `git show failed (exit 129)`, never `git cannot be started` or `internal error`.

Mutants: run/supervisor/FIX-006-mutants.json (gitignored, present in the checkout), run by mutation-run.py: "counts: run=3 cached=0 killed=3 survived=0 not applied=0 error=0 expected survive=0" (run/agent/FIX-006-mutation.out): m1 a refused `git show` read as an empty commit (both show checks let 129 through); m2 CANNOT SCAN exits 0; m3 the reason names no git call. No run against a checkpoint: the test pins built behaviour, so it passes there by construction; the mutants show it can fail.

## Threat model
docs/INVENTORY.md, Decisions, the push-scan threat-model row (R-087) for what the test exercises: a scan that cannot read git exits 2, a hold, never a pass. The test adds no program surface.

## The records in the diff (expected)
- docs/HARDENING.md: item 3 settled (FIX-006 paragraph); a new section, "Stage P2's close records, the ceiling round's notes (PR #183, 2026-11-20)", recording three records notes of Review A's round-3 read (the CI watch's wait row on --required and on gh's fail bucket, DESIGN F2 likewise, R-080's kinds against is_agent), each fixed by the next increment that edits its record.
- docs/REQUIREMENTS.md: R-087's Evidence names the test (its Status unchanged).
- docs/INVENTORY.md: the order-of-updates Decisions row places the prototype meta workflow third, directly after the program release (the owner's confirmation in this chat, 2026-11-20, in the question form, of the maintainer session's relayed placement, rule 57), the later items renumbered (4) to (11) with their text unchanged, the Decided column naming it; the older order row's list of revisions names it.
- docs/PROJECT_STATUS.md: Next (item 3 settled; the order after the program release begins with the prototype meta workflow) and Remote sync, as at this pull request's merge.

## Checks already run
Review A (diff-reviewer): APPROVE, no blocking, its records notes taken; `inventory-check.py` OK; `completion-check.py --mode plan` OK (89 built, 2 deferred, 14 planned); invisible-check OK; secret-sentinel PASS; the test beside ten record-reading test files, stripped: "381 passed, 1 skipped"; after the notes, the test with the records gate test: "74 passed".

## Out of this pull request
Stage P3's increments (TASK-068 onward); the install's git floor; the prototype meta workflow's design (on the owner's word after the program release).
