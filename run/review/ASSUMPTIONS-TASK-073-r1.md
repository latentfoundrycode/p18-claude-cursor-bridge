# Assumptions, TASK-073

The builders' `Assumed, not verified` lists (handoff/TASK-073-r1-report.md, -r2-report.md, -r3-report.md) and the supervisor's, each with its disposition. Extra places to look, never the review's scope.

## Round 1
- A stale marker whose copy is gone does not block an install or a rollback -> accepted, made a requirement in round 2 (S1) and round 3 (F3).
- Non-version files or folders under cursor-bridge-previous/ are ignored by kept_release_names and not removed by save_previous unless version-shaped -> false (Review A: the loop removed every folder but the marked and saved ones); the round-2 brief required a true report (S6) and round 2 changed the listing and the rotation.
- Usage and refusal messages render on a cp1252 console -> accepted: the program is ASCII-only, checked in each round's Done.

## Round 2
- An orphan marker counts as no mark in save_previous and is cleared after a rollback when its name is gone -> accepted (Review A checked the lines).
- Stray non-folder entries are removed at the rotation -> true for removable files; a read-only one stopped every install (the security audit), corrected in round 3 (F2).
- cp1252 -> accepted, as round 1.

## Round 3
- The builder wrote none. Review A found its F4 line untrue: a stray entry named like the saved version that cannot be removed still stops the install at the rename -> recorded, HARDENING TASK-073 lead 2 (a hand-made layout).

## The supervisor's
- A value is a name, compared case-sensitively although Windows paths are not -> accepted (the plan's "exactly").
- --keep with --rollback is refused -> the supervisor's ruling; pinned by the acceptance file's keep-with-rollback form.
- Which kept copies a bare --rollback leaves (an older marked copy stays) -> the builder's choice, stated in round 1's report.
- tests/test_rollback.py cannot judge a mutant (it installs the repository's own stamped release) -> the mutation sweep is judged by the acceptance file alone, with the two cases added for it.
