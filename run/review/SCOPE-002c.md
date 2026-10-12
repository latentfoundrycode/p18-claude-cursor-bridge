# SCOPE-002c — TASK-002, the security floor in the bridge's CI: re-review of the merged head

PR #16. The branch was approved by both reviewers at e9299e6 (Review A and Review B, second round; secret-sentinel CLEAR; spec test 12/12). It then conflicted with main, which had gained TASK-003 to TASK-007, on docs/PROJECT_STATUS.md. main was merged in (f9f33e6; the status file took main's form) and the records the branch had held back were committed. An updated branch is a new head, so it is reviewed again, whole.

## Files
- run/review/REVIEW-002c.diff — the whole branch against origin/main (read it whole; the review's subject).
- run/review/REVIEW-002c-records.diff — the records commit alone (f9f33e6..HEAD), for orientation.
- The floor's own files (.github/, requirements.lock, .semgrep.yml, osv-scanner.toml, socket.yml, tests/test_release_b_ci_floor.py) are byte-identical to the approved head e9299e6: `git diff --stat e9299e6 HEAD -- <those paths>` prints nothing.
- run/review/ASSUMPTIONS-002c.md — the branch's assumption lists; extra places to look.

## The increment (docs/BUILD_PLAN.md, TASK-002)
- Author: builder (composer-2.5), five rounds; the spec test is supervisor-authored.
- Scope: .github/workflows/tests.yml; .semgrep.yml; osv-scanner.toml; socket.yml; requirements.lock; tests/test_release_b_ci_floor.py
- Satisfies: R-002. Done when: CI installs from `requirements.lock` (the dependency manifest OSV/Socket read; a change to it pairs with itself for `lock-check`); a `gate` adds Semgrep (ubuntu authoritative), OSV-Scanner, and Socket, each action pinned by commit SHA; OSV/Socket find the lockfile and do not exit 128; `test_release_b_ci_floor.py` (names R-002) asserts the three scanners run and every action is SHA-pinned; green on this PR.
- Owner decisions in force: Semgrep runs the OSS engine with explicit rulesets and no token (2026-10-12); the Socket organization is named by the repository variable SOCKET_ORG_SLUG = latent-foundry, set by the owner 2026-10-12. Design for later increments is not this diff's defect; making the `security floor` job a required check on main follows the merge.

## What to check on this head
1. The merge brought nothing of main's into conflict with the floor: main's increments changed only governance text, tests and records (bridge/commands/supervisor.md, bridge/cursor-bridge/workflow/*, MANIFEST.json, tests/test_workflow_model.py, test_open_list.py, test_extension_points.py, test_workflows_line_text.py, docs/*). The workflow, lockfile and scanner configuration are exactly as approved at e9299e6.
2. The records (docs/REQUIREMENTS.md R-002 built; docs/INVENTORY.md the floor's feature row, scanner versions, lockfile, the two repository secrets and the variable by name only; the OSS-engine decision; docs/PROJECT_STATUS.md; docs/DESIGN_CRITIQUE.md TASK-007's round-2 record) agree with the workflow and with each other. No secret value is written anywhere; `latent-foundry` is not a secret.
3. The CI run on this head reads the variable (`SOCKET_CLI_ORG_SLUG` set in the Socket step's env).
4. Gate integrity: the CI workflow is the increment's own scope; the anti-gaming and security-control checks apply to it explicitly (no skip, no continue-on-error, no suppression, every action SHA-pinned, secrets only in step-level env).

## Tests
- tests/test_release_b_ci_floor.py (supervisor-authored; names R-002; enforces BUILD_PLAN TASK-002 Done when): 12 tests, unchanged since the approved head.
- Full suite on this head: 939 passed, 20 skipped (the 927 of main plus the floor's 12). secret-sentinel CLEAR on the merged branch.

## Expected bookkeeping and record files in the diff
- handoff/TASK-002*.md (the briefs r1–r5 and the builder's reports; the r1 brief and report describe an earlier design that later rounds replaced), docs/BUILDER_NOTES.md, docs/ROSTER.resolved.json (a resolved-at timestamp), the records above, run/review/ (these files).
