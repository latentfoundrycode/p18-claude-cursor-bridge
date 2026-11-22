# SCOPE - CLOSE-P3: stage P3's close records (the program release)

Records only, the supervisor's, after stage P3's review (round 1, closed by BUG-047, PR #198) and its demonstration live on main 8b65173 (33 of 33 checks). Pull request #199, branch close-p3 from origin/main 8b65173. review-guard's premerge-records named the full gate: docs/REQUIREMENTS.md (R-093 and R-094's Status cells) and docs/diagrams/D-004-context-dfd.md.

## What changed (run/review/REVIEW-CLOSE-P3-r1.diff is the whole change)
- docs/REQUIREMENTS.md: R-093 and R-094 read built, Evidence tests/test_program_release_tooling.py (TASK-074) and tests/test_program_install_keep.py (TASK-073); R-093's result-line clause qualified for the folder-name refusal.
- docs/INVENTORY.md: the security step's row names bridge/cursor-bridge/bridge_env.py.
- docs/HARDENING.md: TASK-077's first CI run (red on Linux) and its Review B round 1 Consider; the sections Stage P3's close, Stage P3's demonstration and Least confident (stage P3's close).
- docs/diagrams/D-004-context-dfd.md: the store ds_project_checkouts in a boundary of its own (tb_projects), its origin read into p_evaluate_reports; p_pace_report with its reads and its one output; R-089 in Realizes; a note.
- docs/PROJECT_STATUS.md, project.json: stage P3 closed, stage P4 next; the old Stage line and the 2026-11-12 Calibrated line moved word for word to docs/archive/STATUS_HISTORY.md (the status file's cap); the open issues as ten items.

## Review A
diff-reviewer APPROVE, no blocking, no should-fix; its three Considers (D-004's boundary and Realizes, R-093's clause, the demonstration's wording) taken in the second commit, with two leads recorded in HARDENING.

## What to check
- Each record true to its source: the programs (bridge/cursor-bridge/bridge-check.py, tools/make-manifest.py, bridge-install.py, evaluate-reports.py, pace-report.py, bridge_env.py), the tests named as evidence, run/agent/demo_p3-live.out is not in the checkout's tracked files (the demonstration's output; the HARDENING section quotes it), docs/BUILD_PLAN.md's Stage P3 and Stage P4.
- The diagram's added flows true to the code and its Mermaid valid (python bridge/cursor-bridge/diagram-check.py prints RESULT: OK).
- The status file's header and prose agree (python bridge/cursor-bridge/inventory-check.py prints RESULT: OK) and the moved lines appear word for word in the archive.
- No key, no computer path or user name in a tracked file (rule 54).

The Issues and Feedback entries, the Project Summary and the User Manual are under Documents/, outside the repository, written at this reflection point; they are not in this change.
