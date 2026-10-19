# ASSUMPTIONS - BUG-016

From the branch's commit messages (`git log 1b8c8da..HEAD --format=%B`), sections `Assumptions:`:

Assumptions: GitHub Actions sets GITHUB_BASE_REF and GITHUB_EVENT_NAME on pull_request events -> test (this PR's CI run is into main: the guard must pass, not skip)

Assumptions: none (supervisor-written records)

Assumptions: GitHub Actions sets GITHUB_REF and GITHUB_EVENT_PATH for the pytest step -> test (the PR's CI run must show the guard ran, not skipped)

Places to look all the same: the guard against what GitHub Actions sets on pull_request and push events; the status file read alone as a resuming session would after this merge; each record claim against git.
