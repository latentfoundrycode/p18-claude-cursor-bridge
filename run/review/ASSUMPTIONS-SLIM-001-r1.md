# ASSUMPTIONS: SLIM-001, round 1

There was no builder run on this branch, so no builder's `Assumed, not verified` list exists. The branch's one commit message says: "Assumptions: none; no builder run, the maintainer wrote this diff."

What the maintainer assumed and did not verify, as extra places to look, never as the review's scope:

1. **The link is made as a directory junction on Windows and a symbolic link elsewhere.** Verified live only on the owner's Windows 11 machine (2026-11-11: link made, `cursor-agent status` logged in, 278 model lines listed with both folders redirected). The POSIX branch is exercised by the tests on CI's Ubuntu runner only, with a temporary folder standing in for `APPDATA`; on a real Linux or macOS machine `cursor-agent` keeps its login elsewhere and the link is expected to be absent and harmless. Not verified on a real non-Windows login.
2. **`%APPDATA%\Cursor` is all of the login state `cursor-agent` needs.** Probed: `APPDATA` redirected alone logs out, `LOCALAPPDATA` redirected alone does not. Not verified: a later Cursor version keeping state under `LOCALAPPDATA`.
3. **A project's test suite needs nothing from the owner's real `APPDATA` or `LOCALAPPDATA`.** True of this repository's suite (5,163 passed with `tests/conftest.py` pointing `APPDATA` at a temporary folder). Not verified for the three other projects; a suite that reads a tool's state there would find the agent home's empty folders.
4. **The squash subject of a merged pull request ends `(#<n>)` on `origin/main`**, which the text evidence form reads. True of this repository's history (read 2026-11-11); a repository with another squash setting would refuse the form.
5. **`gh pr view` returns the pull request's head and changed files** for `premerge-records <pr>`; the tests replace `gh` with a stand-in. Not run against GitHub.
