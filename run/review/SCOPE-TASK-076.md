# SCOPE for TASK-076 (Review B, round 1)

TASK-076 gives the allowlist test an example mark (R-096): tests/test_allowlist.py reads each instruction text through `commands_in`, its fenced bash lines as before and its inline commands line by line (split at the line feed), and an inline command on a line that carries `<!-- not run -->` is not collected; a marked line holding more than one inline command is refused with a ValueError, so a mark never hides an instructed command beside its example. The docstring states the mark and that it is for a command an instruction quotes as an example and does not instruct; the two skip lists (KNOWN_PROSE, PROSE_EXACT) keep what they hold; no instruction text carries the mark. Branch task-076 from main 7e8558a (PR #192's merge, TASK-075). The supervisor's own increment (the plan's Author: supervisor, a test file only): no builder, no brief; this is the review guard's first round for TASK-076: there is no Blocking class line.

Round cause: unstated

Where the increment ends: tests/test_allowlist.py and the records. The CHANGELOG sentence R-096 asks for is the release stamp's (TASK-081), recorded in docs/HARDENING.md under TASK-076, not this diff's.

Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-076)
Scope: tests/test_allowlist.py
Scope notes: tests/test_allowlist.py: the collection skips an inline command on a line that carries the mark, the mark stated in the docstring, the two skip lists kept
Satisfies: R-096
Done when: read it whole in docs/BUILD_PLAN.md under the heading TASK-076: the collection keeps reading inline commands, as many as before the change (the count quoted in the accept commit), and skips an inline command on a line that carries the mark; the docstring states the mark and its purpose; the two skip lists keep their entries; one test naming R-096 feeds the collector a marked and an unmarked line and asserts which is collected, red on a mutant that ignores the mark and on one that skips every line; no instruction text carries the mark; R-096 reads built in the records commit.

## Evidence
- Collection: 115 instructed commands before the change (260 tests), the same 115 ids in the same order after (262 tests, the two R-096 cases)
- tests/test_allowlist.py, stripped: 242 passed, 20 skipped (the prose skips, as before)
- Review A: APPROVE, one Should fix taken (a marked line holding more than one command refused, with a case); noted, not changed: the inline loop also reads lines inside fenced blocks
- the mutation sweep (run/supervisor/TASK-076-mutants.json): three mutants (the mark ignored; every line's commands dropped; the refusal removed), every one killed
- completion-check.py --mode plan OK (90 built, 2 deferred, 13 planned); inventory-check.py OK

## Expected bookkeeping and records in the diff
docs/REQUIREMENTS.md (R-096 built), docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md (as at this pull request's merge), and run/review/ (these files).
