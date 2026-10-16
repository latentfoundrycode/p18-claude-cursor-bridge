# Hardening

Leads the gate drew a line under, and the parts of each stage the supervisor is least sure of, each with the check that would settle it. The next stage's refactor-scout reads this file first. A lead a test can settle becomes a test before the next stage's first delegation.

## Stage B1 — supervised-project bootstrap

### Least confident (stage close, 2026-10-16)
1. **The floor's teeth against a real bad dependency.** OSV-Scanner and Socket have run green on the real lockfile, but neither has been seen to fail: no planted known-vulnerable or known-malicious pin has been put through them (Semgrep's teeth were proven with a planted SQL-concat fixture in TASK-002 r2). Check: a throwaway pull request pinning a version with a published advisory in requirements.lock must turn `security floor` red at the OSV step, and one adding a package Socket flags must turn it red at the Socket step; close the pull requests unmerged and delete their branches.
2. **The runner image change.** `ubuntu-latest` is to move to the next Ubuntu image (2026-10-19 by a reviewer's reading during TASK-002, not yet confirmed against GitHub's runner-images notice); the Semgrep step relies on `pipx` being on the image and Node 22 from setup-node. Check: the first `security floor` run after 2026-10-19 shows the Semgrep step running `pipx run semgrep==1.176.1` and the Socket step scanning; if pipx is gone the step fails red (it cannot pass silently, the tests pin its last line).
3. **What Socket's scan actually covers.** The supported-file list shows `requirements.lock` matches, and the scan reports "Found 3 files", unnamed. Check: open the scan of the next `security floor` run in the Socket dashboard (latent-foundry) and confirm pytest, pyyaml and their closure are listed, and which other two files were read.

### Leads (stage B1's review, 2026-10-16)
- The Semgrep rule packs `p/python` and `p/secrets` are fetched from the registry on every run; only the engine is pinned. An upstream rule change can turn an unrelated pull request red or drop coverage unseen. Settle: vendor a dated copy of the two packs into the repository, or accept the drift as a Decision.
- `npm install -g` of the Socket CLI resolves its transitive dependencies afresh on each run (24 packages, no lockfile for a global install). BUG-001 closed the install-time exposure only: whatever of them the CLI loads runs inside `socket ci`, with `SOCKET_CLI_API_TOKEN` in that process's environment, so an unpinned dependency is a risk of BUG-001's kind at scan time. Settle: install the CLI from a committed package-lock in a tool folder (`npm ci --ignore-scripts`), or record the drift as an accepted Decision with its reason; the first changes `test_r002_no_install_runs_beside_a_secret`'s pin, which reads the version on the install line, in the same increment.
- The structural CI test pins the `security floor` job verbatim (BUG-001 round 5); its pattern checks remain only as a second line for the tests job and later steps, and do not model every install form (pnpm or yarn installs have no script check; an npm option whose value starts with `-`). Settle when another job gains an install or a secret: pin that job as well rather than widen the patterns.
- The full-tree Semgrep audit (2026-10-16, one accepted finding) is a point-in-time result; diff-aware scans never see code a pull request does not touch. Re-run it at each release (recorded in INVENTORY Decisions).
- The repository secret SEMGREP_APP_TOKEN is stored but unused (OSS engine); the owner could delete it and revoke the token (least privilege; not a defect).

## Stage B2 — carried to its close (test lane)
- tests/test_open_list.py: pin "filled, including"; fix the stale comment at :25 (TASK-004 r3 Consider).
- tests/test_extension_points.py: pin the configuration.items CI route, the inspect step's members, and the placement sentence (TASK-005 r6 Consider).
