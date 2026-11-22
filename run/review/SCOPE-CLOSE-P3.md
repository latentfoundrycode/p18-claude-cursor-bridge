# SCOPE - CLOSE-P3: stage P3's close records (the program release)

Records only, the supervisor's, after stage P3's review (round 1, closed by BUG-047, PR #198) and its demonstration live on main 8b65173 (33 of 33 checks). Pull request #199, branch close-p3 from origin/main 8b65173. review-guard's premerge-records named the full gate: docs/REQUIREMENTS.md (R-093 and R-094's Status cells) and docs/diagrams/D-004-context-dfd.md.

## Round 1 (approved)
Review A APPROVE (its Considers taken before Review B). Review B round 1 APPROVE with one Should fix and four Considers.

## Round 2
All five taken in the commit after "Review files for round CLOSE-P3-r1", whose diff is run/review/REVIEW-CLOSE-P3-r2.diff:
- Should fix: docs/HARDENING.md, "Records at the close": the security step calls bridge_env.GH_COMMAND and git_read_env (REFAC-014's git environment); REFAC-014's reviewer names serve in-flight.py and pace-report.py, not this step.
- Consider: HARDENING, TASK-077's Review B bullet: an undecodable origin URL ends in an exception (Python 3.12: the decode fails in subprocess's reader thread, the call returns no output, `.strip()` raises AttributeError), not UnicodeDecodeError as written.
- Consider: HARDENING, the demonstration's first bullet: the stand-in gh is tests/test_program_security_step.py's, set through TASK-064's bridge_env.GH_COMMAND seam, answering from tests/fixtures/github/security-*.json.
- Consider: HARDENING, a lead: test_r093_r3_a_copy_of_the_program_in_a_folder_of_another_name_is_refused checks exit 2 and RESULT: REFUSED, not the folder it names.
- Consider: docs/diagrams/D-004-context-dfd.md's note: pace-report adds the bridge's own root only where no root is given and the projects file does not list it (pace-report.py _default_roots).
diagram-check OK. Check each line against round 1's findings and the code, and that nothing else moved. This is the round's Review B round 2, below the guard's ceiling.
