# ASSUMPTIONS-002c — from the branch's commit messages (git log origin/main..HEAD)

Extra places to look, never the review's scope. Each "test (PR CI run)" item is settled by the CI run on the pushed head, which the reviewer can read (the Socket, OSV-Scanner and Semgrep step logs).

The security floor (e09e5f7, builder rounds r1–r4):
- Semgrep registry packs resolve in Actions without a token → test (PR CI run)
- socket ci discovers requirements.lock from the repo root → test (PR CI run)
- persist-credentials: false with fetch-depth: 0 still gives the merge-base → test (PR CI run)
- Node 22 on ubuntu-latest suits the Socket CLI → test (PR CI run)
- permissions: contents: read is enough for every step → test (PR CI run)
- OSV-Scanner reads requirements.lock via the requirements.txt parser → test (PR CI run)

r5 (afaa35c, the Socket CLI 1.7.0 and its organization):
- the live Socket API accepts the slug from vars.SOCKET_ORG_SLUG → test (PR CI, now that the owner has set the variable)
- the token in SOCKET_SECURITY_API_KEY belongs to that organization → test (PR CI)
- socket ci 1.7.0 still discovers requirements.lock → test (PR CI)

The records commit (this round):
- The Socket step's earlier green run without the variable shows the CLI resolving the organization from the token; the variable makes it explicit → the CI run on this head reads it; review.
