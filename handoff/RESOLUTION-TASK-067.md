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

## The first votes (2026-11-18)

### Review B (gpt-5.6-sol-high): VOTE NONE

- A neutralises committed and user attributes; ordinary and combined text diffs show their added lines; a combined `index` line reads `parent1,parent2..result`.
- Local `-diff`, binary drivers and `core.bigFileThreshold` can hide text; A's result-blob check can refuse them.
- Blocking gap in A: `.git/info/attributes` with `diff`, or a driver with `binary=false`, forces a real NUL-bearing binary into a text hunk under A's options; A checks only sections shown as binary, so it gives a false hit.
- B keeps a false-hit risk and reads merges a second, divergent way; C refuses ordinary binaries and committed `diff` attributes defeat its claim.
- Required: classify every result blob by content before reading its hunks; skip and count NUL blobs even when forced to text; refuse non-NUL blobs shown as binary; fail closed on missing or malformed result ids; test ordinary and combined diffs in both forced directions; accept git's binary definition explicitly.

The supervisor's launch named its error file after the round, not the snapshot, so `review-guard.py verify` raised GATE-INTEGRITY on it (the file held only the launcher's three lines; the tree was restored). This round's second Review B vote is launched under a matching name.

### Review A (claude-opus-5-5): VOTE A-EXTENDED

- Agrees with each of Review B's points, checked on git 2.53: `--full-index` expands the combined `index` line to full ids; the combined `index` line carries no mode; `core.bigFileThreshold` hides text in an ordinary diff but not in a combined one; `log.diffMerges` does not change `git show` of a merge.
- New: a UTF-16 text file (what Windows PowerShell 5.1 `>` and `Out-File` and `reg export` write) shows as binary, so under A, extended or not, a profile path in it is pushed with exit 0. Ordinary use on Windows.
- Refinements: submodule entries (mode 160000) and deleted files (an all-zero result id) are not classified; ids are full (`--full-index` on the patch, `--no-abbrev` on a raw read, since `--full-index` does not expand raw output); a text result shown as binary only because an old or parent blob holds a NUL is read, never refused (else a UTF-16-to-UTF-8 conversion ends exit 2 for good); a UTF-16 file starting with a BOM that decodes strictly is text.
- The content rule is reproduced in Python (`b"\0" in data[:8000]`), since no git option turns off `.git/info/attributes`; git's size threshold is left out of it on purpose.
- Residual: a BOM-less text file with a NUL in its first 8000 bytes is counted, not read; to be recorded in words as accepted.

## The supervisor's proposed decision: A extended, a text file is always read

Content decides; how git shows a file never does. Reading a text file that git shows as binary is chosen over refusing it: it never passes the file and never refuses a push on a local setting.

1. The patch read: `git --attr-source=<the empty tree> -c core.attributesFile= show --full-index` with today's options, without `--text`. A git without `--attr-source` fails the call, exit 2.
2. The file list: `show -z --raw --no-abbrev -M` under the same attribute options, replacing `--name-status`. Every id must be the repository's hash length (`rev-parse --show-object-format`) and lower-case hex, else exit 2. The check that every patch path is a listed path stays.
3. Every patch section with hunks or a `Binary files ... differ` line has an `index` line with one id per parent and a result id equal to the raw record's, else exit 2. A deleted file (an all-zero result id) has no added line (else exit 2) and is not classified; a submodule (result mode 160000) is not classified and its `Subproject commit` lines are read as today.
4. Every other result blob is read with `git cat-file` and classified: UTF-16 when it starts with `FF FE` or `FE FF` and decodes strictly as UTF-16; else binary when a NUL is in its first 8000 bytes; else text. A failed read ends with exit 2.
5. By class, never by how git shows the section:
   - text shown as hunks: the hunks' added lines are read, as today;
   - text shown as `Binary files ... differ` (any cause), and UTF-16 however shown: every line of the result blob not present in any parent's blob is read, each placed by its line in the result; a parent is decoded as the result is (UTF-16 as UTF-16, text as the patch lines are decoded), and a binary or absent parent contributes no line;
   - binary: its hunks, if any, are never read; it is counted in `push-scan: note - <n> binary file(s) not read`, never named.
6. Recorded as accepted in R-087 and DESIGN C2, beside a path compiled into a real binary: a BOM-less text file with a NUL in its first 8000 bytes, and UTF-16 without a BOM, are counted as binary and not read.

Why the set difference for a section git shows as binary: it is the combined diff's own meaning (a line counts when it is new against every parent), and a line present in a parent is either already on the remote or was read when the commit that added it was scanned.

## The second vote and the decision (2026-11-18)

Review B, second turn: the proposal with changes. Its blocking point: a set difference loses a duplicate added line (a parent `P, base`, a result `P, base, P`; git marks the last `P` added), in UTF-16 and in merges and octopus merges too; per-preimage line diffs, position by position, replace it. Its other changes: `--cc` asked for explicitly; the `Binary files` wording relied on nowhere; the raw parser strict (framing, modes, status, id counts, duplicates) with paths compared losslessly; a root commit's one all-zero preimage; the accepted limits stated in full (a BOM-prefixed binary that decodes strictly is read as UTF-16; UTF-32 and other encodings are not decoded). `review-guard.py verify TASK-067-r2`: OK.

The supervisor's decision, with those changes, is recorded in docs/CHANGES.md (2026-11-18, "content decides how the pre-push scan reads a file, a resolution round"); R-087, DESIGN C2 and the plan's TASK-067 entry carry it.
