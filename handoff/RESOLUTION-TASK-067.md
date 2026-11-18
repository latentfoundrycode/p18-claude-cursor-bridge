# TASK-067: the resolution round on binary files (R-087)

## The question

How does the pre-push scan decide which files it reads line by line, so that no commit content can hide a text file's added lines (the round-3 finding the round-4 class line lifted), no real binary file gives a false hit, and a merge's combined diff is read as an ordinary commit's diff is?

## Why a resolution round

Round 4 (handoff/TASK-067-r4.md, lifted above the ceiling by its class line, which both reviewers confirmed against round 3's code at 776168e) added `--text` to the patch read and `--no-replace-objects` to every git call. Both reviewers of round 4 then found two blocking defects in the same line (bridge/cursor-bridge/push-scan.py:637, at this file's commit):

- **B1 (security; Review A and the security audit).** Git's combined diff of a merge (`diff --cc`) ignores `--text`. A merge whose resolution adds a line holding a path to a file marked `-diff` or `binary` (by a committed `.gitattributes`, the worktree's, or `.git/info/attributes`; in ordinary use a conflict resolved in a lockfile marked `-diff`) prints `diff --cc <file>`, `index ...`, `Binary files differ`, and the scan prints `push-scan: OK`, exit 0. Round 3 behaved the same; round 4 closed the finding for ordinary commits only.
- **B2 (behaviour, a regression round 4's fix caused; both reviewers).** `--text` applies to every file, so real binaries are read as text and the path patterns match random bytes at about 1.5 per MB: a 49 KB PNG gave one `path` hit, a 1.4 MB PNG one, a 4.7 MB zip seven, a 64 MB binary 86, and 10 of 40 compressed 200 KB blobs one each. Round 3 printed OK for every one of them. A push that adds an image ends `FOUND`, exit 1, and the owner cannot clear it.

A class line never lifts a round for a regression the previous fix caused (decide.md, "Stop"): the regression goes to a resolution round. Both reviewers proposed the same direction; this round tests it before any brief.

## The supervisor's probe (git 2.53.0.windows.2, a scratch repository, 2026-11-18)

- `git --attr-source=<the empty tree> show ...` reads no tree's `.gitattributes`: a commit that adds `*.md -diff` and a line to `notes.md` shows the line as a hunk (without it: `Binary files a/notes.md and b/notes.md differ`). The same for a merge's combined diff: its resolved line shows as `++RESOLVEDPATH` with or without `--text` (with the attribute in effect and `--text`: `Binary files differ`).
- A real binary (bytes 0 to 255 repeated) still shows as `Binary files /dev/null and b/blob.bin differ` under `--attr-source`: git's own content rule (a NUL in the first 8000 bytes) decides.
- `.git/info/attributes` still applies under `--attr-source` (`*.md binary` there still gave `Binary files ... differ`, with and without `-c core.attributesFile=`). Whether `-c core.attributesFile=` set empty disables a user attributes file on its own was not probed separately. Both are local settings, never commit content.
- `core.bigFileThreshold` and a diff driver's `binary` setting reached through a local attribute also show a text file as binary (the security audit, round 3).

## The candidates

### A. Attributes never decide; git's content rule does, and a text file shown as binary ends the scan

- The patch read drops `--text` and runs as `git --attr-source=<the empty tree> -c core.attributesFile= show ...` (the empty tree's id computed by `git hash-object -t tree` of empty input, so a SHA-256 repository works too), so no `.gitattributes` in any tree and no user attributes file decides how a file shows. A git without `--attr-source` (before 2.40) fails the call, exit 2, never a pass.
- A real binary (a NUL in the first 8000 bytes of its new blob, git's own rule) shows as `Binary files ... differ` and is not read; the scan counts such files and prints `push-scan: note - <n> binary file(s) not read`, never naming them. A path compiled into a real binary (an executable, a .pyc) stays unread: a recorded lead, as in rounds 1 to 3.
- Every section that shows `Binary files ... differ` (ordinary or combined) is checked against its new blob's own bytes (the blob id from its `index` line, read with `git cat-file`): where the blob holds no NUL in its first 8000 bytes, a local setting (`.git/info/attributes`, `core.bigFileThreshold`, a driver's `binary`) is hiding a text file, and the scan ends with exit 2 (`CANNOT SCAN - a text file is shown as binary`), never a pass and never a false hit.
- Trade-off: a NUL placed in the first 8000 bytes of a text file makes git treat it as binary and the scan does not read it (the file is counted in the note). That is git's own rule, the one `git diff` and every reviewer's view of the file follow.

### B. `--text` everywhere, with a stricter path rule inside binary files

- Keep `--text`; for a file whose new blob is binary by content, a path counts only inside a run of at least twelve printable ASCII characters around the match, and a name only as a whole word inside such a run.
- A merge's combined diff still ignores `--text`: read each merge's files with a pairwise `git diff --text` against each parent and keep the lines new against every parent, or end with exit 2 on a combined `Binary files differ`.
- Trade-off: real binaries are read (a path compiled into an executable is found), at a residual false-hit rate (about one in a few hundred MB at twelve characters) and a second reading of merges beside the combined diff.

### C. Fail closed on every binary section

- No `--text`, no attribute neutralising: every `Binary files ... differ` section ends the scan with exit 2.
- Trade-off: every push that adds or changes an image, a font or a lockfile marked `-diff` is refused until the owner removes the file from the range; nothing is ever missed or falsely hit.

## What the vote should engage

- Whether A's `--attr-source` and empty `core.attributesFile` close every route by which commit content (untrusted under D-004) decides how a file shows, ordinary and merge; and whether A's content check of each binary section (exit 2 for a text file shown as binary) is sound for the local routes (`.git/info/attributes`, `core.bigFileThreshold`, drivers), including in a combined diff, where the `index` line holds one id per parent and the result's id.
- Whether A's unread real binaries (counted, not named) are acceptable where rounds 1 to 3 also left them unread, against B's reading of them at a residual false-hit rate and a second reading of merges.
- Whether C's refusals are tolerable in ordinary use (images, fonts, lockfiles in a push).
- Any route A leaves by which a text file's added line is neither read nor refused.
