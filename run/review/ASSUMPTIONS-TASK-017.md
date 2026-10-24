# ASSUMPTIONS - TASK-017

From the `Assumptions:` sections of the branch's commit messages (extra places to look, never the review's scope).

- A call that changes something at the service is one that must not run twice, beside a paid call -> accepted (the inspect check's wording; Review B reads it).
- The split constants equal the baseline units as trace-check.py reads them (the trace check passed before the move with those units unexcused) -> test (test_traits_existing.py puts each split's parts back in the unit's sentence order).
- delegation-loop.md's "2. Package the brief" holds that one paragraph, so its new entry excuses nothing else -> test (its section pinned in test_b3_least_confident.py).
- "Phase: mockups" maps to the interface module in the hook -> test (the case asserts interface.md named there).
- tests/test_phase_modules_build.py and tests/test_text_consistency.py need no change: no pin of theirs breaks -> test (the suite).
- R-032's bound read in characters, delegation-loop.md at 53,330 of 60,000 -> accepted (INVENTORY, Decisions, the size row).
- No security-auditor pass: the diff is governance text and tests, with no code surface -> accepted (reviewer routing; Review A and Review B read the moves of the security-relevant passages).
