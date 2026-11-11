# ASSUMPTIONS: SLIM-001, round 2

There was no builder run on this branch, so no builder's `Assumed, not verified` list exists. Both commit messages say: "Assumptions: none; no builder run, the maintainer wrote this diff."

What the maintainer assumed and did not verify, as extra places to look, never as the review's scope:

1. **The link is made as a directory junction on Windows and a symbolic link elsewhere.** Verified live only on the owner's Windows 11 machine (2026-11-11: link made, `cursor-agent status` logged in, 278 model lines listed with both folders redirected). The POSIX branch is exercised by the tests on CI's Ubuntu runner only, with a temporary folder standing in for `APPDATA`. Not verified on a real non-Windows login.
2. **`%APPDATA%\Cursor` is all of the login state `cursor-agent` needs.** Probed: `APPDATA` redirected alone logs out, `LOCALAPPDATA` redirected alone does not. Not verified: a later Cursor version keeping state under `LOCALAPPDATA`.
3. **A project's test suite needs nothing from the owner's real `APPDATA` or `LOCALAPPDATA` beyond what `APP_CACHES` passes.** True of this repository's suite. Not verified for the three other projects: npm's built-in `prefix=${APPDATA}\npm`, Volta and `py.ini` live there (Review A, round 1), and a suite that reads them would meet the agent home's empty folders and fail visibly. One stripped suite run per project at its calibration settles it.
4. **The squash subject of a merged pull request ends `(#<n>)` on `origin/main`**, which the text evidence form reads. True of this repository's history (read 2026-11-11); a repository with another squash setting would refuse the form.
5. **`gh pr view --json headRefOid,baseRefOid,baseRefName,files` returns what `premerge-records <pr>` reads**; the tests replace `gh` with a stand-in. Not run against GitHub.
6. **`git worktree list --porcelain` prints one `worktree <path>` line per worktree**, which `launch_roots` reads. Run here on git 2.x for Windows through `tests/test_release_s_launcher.py::test_a_worktree_of_the_same_repository_is_inside`; not verified on an older git.
7. **A record is written in one of `.md`, `.json`, `.txt`, `.csv` or a picture.** Read from this repository's `docs/` and `handoff/`; a project that keeps another type there (a mockup's `.html`, a Mermaid `.mmd`) takes the full gate for it, which is the safe side.

Counts quoted from their output lines:

- The whole suite once, before round 1's fixes, in this clone: `1 failed, 5163 passed, 45 skipped in 2030.40s (0:33:50)`; the failure, `tests/test_header_plan_r3.py::test_r059_r3_the_program_walks_no_plan_itself[plan-check]`, fixed before the first commit.
- After round 2's fixes, with the pull request's variables set, seventeen files: `645 passed, 20 skipped in 288.78s (0:04:48)`.
- After round 2's fixes, eight guard and plan files: `555 passed in 196.12s (0:03:16)`.
- The whole suite runs again as CI's run on the pushed head.
