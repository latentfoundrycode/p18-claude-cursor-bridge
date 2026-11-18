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

# The second resolution: round 5's regressions (2026-11-18)

## The question

Round 5 (handoff/TASK-067-r5.md, its class line confirmed by both reviewers against round 4's code) built the decision above. Both reviewers rejected it, and each blocking finding is a regression round 5 caused. A second fix that regresses goes to a resolution round (decide.md, "Stop"). How should the decided design be corrected so that none of the four routes below remains?

## The findings (bridge/cursor-bridge/push-scan.py at this file's commit, round 5's tree)

- **F1 (security; the security audit, B1).** `classify_blob` (866-876) calls a blob UTF-16 when it begins with `FF FE` or `FE FF` and the rest decodes strictly; ASCII byte pairs always decode strictly as UTF-16LE. `_by_class` (979-989) then reads only the UTF-16 decoding and ignores the hunks git showed. A commit adding `b"\xff\xfe" + b"hello\nsee <a path>\n\n"` (git shows it as text, with the path as an added line) prints `push-scan: OK`, no note; round 4 found it. Ordinary on Windows too: a file PowerShell 5.1 wrote (UTF-16LE with a byte-order mark) and then appended to in UTF-8 by another shell's `>>` (round 4 hit, round 5 OK; with an odd-length append the file falls to binary and is counted).
- **F2 (behaviour; Review A, B1).** For a text result git lists with no section, K5 runs the line diff. A clean merge where both branches changed a text file over 1 MiB in different places (a lockfile) is listed in the raw list, but `--cc` prints no section (every hunk takes one parent's lines unchanged), so the scan ends `CANNOT SCAN - a file too large to compare`; round 4 printed OK. Under 1 MiB the same leg is slow: a 930 KB Markdown file took 127 s (round 4: 0.5 s), since `SequenceMatcher` with `autojunk=False` is close to quadratic on repeated lines.
- **F3 (behaviour against K4; the security audit B2, Review A N1).** A type change to a gitlink (`:100644 160000 ... T lib`, a file replaced by a submodule at the same path) runs `cat-file blob` on the commit id in the `T` branch (992-995) before the submodule check: exit 2 (`git cat-file failed (exit 128)`); round 4 read it.
- **F4 (availability; both, advisory).** Inside the 1 MiB bound, content shaped to be slow takes `SequenceMatcher` far longer (16,000 one-character lines from four values: 15 s; extrapolated to 1 MiB: about an hour), and every changed blob is read whole into memory, one process each (1,500 small files: 30 s; round 4: 0.4 s).

## The supervisor's proposal

1. **A UTF-16 result is read both ways** (F1): as UTF-16 (decoded, by the line diff, as now) and as the patch is read (its section's hunks where git shows them; else the same line diff over the UTF-8 view, decoded with replacement, against each preimage's UTF-8 view). The hits of both readings are reported, each by its own line number. ASCII inside real UTF-16 is NUL-interleaved and UTF-16 decodings of ASCII are not path-shaped, so neither view adds a false hit the other lacks.
2. **A text result git lists with no section is read as nothing** (F2): git's dense combined diff leaves a listed file out only where every hunk takes one parent's lines, so no line is added against every parent; an attribute route makes git print a `Binary files differ` section instead (Review A's probes, committed and local attributes). The line diff runs only for a section git shows as `Binary files` and for UTF-16 (rule 1).
3. **A type change to a submodule is read as a submodule** (F3): in the `T` branch, where the result mode is `160000`, the addition section's lines are taken as the submodule branch takes them, never classified.
4. **F4 stays a lead** (docs/HARDENING.md): after rule 2 the line diff runs only for files git shows as binary by a local setting and for UTF-16, rare in ordinary use; it fails closed above 1 MiB. A bound on the line diff's work (the product of the line counts) and a bounded classification read (`cat-file -s`, the first 8000 bytes) are recorded for later.

## Alternatives to weigh

- For F1: classify as UTF-16 only where a NUL stands in the first 8000 bytes (so a BOM-prefixed file git treats as text is text), with or without rule 1's second reading (without it, the PowerShell-then-appended file's ASCII lines stay unread).
- For F2: keep the line diff for a listed file with no section but bound its work, refusing above the bound (a clean merge of a large lockfile then refuses).
- For F4: bound the line diff's work now (`len(pre) * len(result)` above a limit raises `a file too large to compare`).

## What the vote should engage

Whether rule 2's claim holds for every way git leaves a listed text file out of `--cc` (merges, octopus, user settings that reach the combined diff), so that reading nothing never hides an added line; whether rule 1 leaves any route by which a BOM-prefixed file's added line is neither read nor refused, or adds a false hit; whether rule 3 is complete for type changes (to and from a gitlink, a symlink); and whether F4 should be closed now.

## Review B's vote on the second resolution (gpt-5.6-sol-high): PROPOSAL WITH CHANGES

- F1 to F4 confirmed against round 5's code; F4 to be closed now (the matcher runs in process with no time limit, and UTF-16 content is the commit's).
- Rule 1 is not safe as written: (a) a byte-order mark followed by a UTF-16 prefix and an odd-length UTF-8 append fails strict decoding, holds NULs and is counted as binary, its appended line neither read nor refused; (b) the two views are ambiguous: `FF FE` then the byte pairs of `D:/xx` decodes to non-path characters, while the byte view holds a drive path, a hit no UTF-16 reader would see. Its change: a byte-order-mark file that fails to decode refuses the scan; for one that decodes, a match only in the byte view refuses with an ambiguous-encoding reason.
- Rule 2 holds (a line added against every parent puts `+` in every parent column and makes its hunk interesting; `--cc` cannot drop it; octopus too), implemented as: a section with no hunks takes the line-diff route; a section git does not print is skipped; never rely on the `Binary files` wording.
- Rule 3: dispatch by the result's mode, `160000` handled before any blob read whatever the status (ordinary `T` or a combined status); a gitlink preimage contributes no line; symlinks stay classified and scanned. Cases: regular to gitlink, symlink to gitlink, gitlink to regular, regular to symlink, and combined statuses.
- Rule 4 is wrong to defer: bound the matcher's total work across all parents before it runs; bound classification reads and batch object reads.

## The supervisor's revised proposal (after Review B's vote)

1. **A blob that begins with a UTF-16 byte-order mark is read both ways and never counted as binary**: the UTF-16 view decoded with replacement (so a malformed tail, such as an odd-length UTF-8 append, decodes and is read), and the byte view decoded as the patch is (the section's hunks where git shows them, else the line diff over the byte view). The hits of both are reported, each by its own line. A match only in the byte view is a hit, not a refusal: the bytes do hold the text, the push is held either way, and no new reason is added. A real binary that begins with such a mark is read both ways too: an accepted limit (its false-hit chance is the byte view's).
2. **Rule 2 as Review B states it**: a section that shows no hunk while its result differs from every preimage takes the line diff; a listed record with no section reads nothing; the `Binary files` wording decides nothing.
3. **Rule 3 as Review B states it**: a result of mode `160000` is handled first, before any blob read, for every status; its section's `Subproject commit` lines are read as today.
4. **The matcher's work is bounded now**: before any `SequenceMatcher` runs for a record, the sum over its preimages of `len(preimage lines) * len(result lines)` above 50,000,000 raises `a file too large to compare` (never a pass); the 1 MiB size bound stays. Classification reads stay one `cat-file blob` per changed blob, each under git's own time limit (a blob too large to read in time ends with exit 2, never a pass); batching and prefix reads are recorded as a lead, since they change speed and memory, never the result.


## Review A's vote on the second resolution (claude-opus-5-5): REVISED PROPOSAL WITH CHANGES

- Agrees with Review B on F1 to F4, rule 2 (verified on git 2.53: a clean octopus prints no section; one that re-adds a parent's line at a new position prints `+++`; a binary section is never dropped; a mode-only merge prints a header and no hunk) and rule 3 (regular, symlink and gitlink type changes, `TM` and `MT` merges verified).
- A hit, not a refusal, for a byte-view match: the bytes hold the text, a hit holds the push as a refusal does and names the line to fix.
- Lenient decoding reads the odd-length append through the byte view; a route remains, reproduced with Windows PowerShell 5.1: `>` (UTF-16LE with a mark), an odd-length Git Bash `>>`, then a PowerShell `>>` appending UTF-16LE at an odd offset: no view reads its path and, never counted, the note is lost. It asked for a third view (UTF-16 from offset 3).
- The untrimmed 50,000,000 bound refuses a one-line edit of an ordinary 0.7 MB UTF-16 file for good; trim common ends, bound the middles' product and the run's total, and over-read above the bound in place of refusing.
- A single-parent record with no section refuses; classification reads stay a lead.

## The decision on the second resolution

Recorded in docs/CHANGES.md (2026-11-18, "a marked file read without its NULs, merges read by git's own rule, the line diff bounded, the second resolution round"): a marked blob read as its bytes with every NUL removed and as UTF-16 in the mark's order, both by the line diff; rule 2 and rule 3 as both reviewers state them, with a single-parent record with no section refused; the line diff trimmed, bounded and over-reading in place of refusing, the 1 MiB bound and its reason withdrawn.

# The third resolution: round 7's regression (2026-11-18)

## The question

Review B, the pull request's round on round 6's tree (snapshot TASK-067-r4), rejected it: a commit whose message git records as ISO-8859-1 and holds a drive path whose first segment begins with a non-ASCII letter passed, because the commit object was decoded as UTF-8 with replacement and the replacement character began no segment; the same pass stood in an ISO-8859-1 file's added line. The supervisor decided (docs/CHANGES.md, the top entry): M1, a path's segment also begins with any non-ASCII character that is not whitespace; M2, the commit object is decoded in the encoding its `encoding` header names where Python knows it and it reads printable ASCII as ASCII, else UTF-8. Round 7 (handoff/TASK-067-r7.md) built it; both reviewers confirmed its class line on round 6's code and both found M1 right. Both rejected it on M2, a regression round 7 caused. A fix that regresses is not lifted by a class line (decide.md, "Stop"). How should M2 be corrected, or replaced, so that no header hides what round 6 found?

## The findings (bridge/cursor-bridge/push-scan.py at this file's commit, round 7's tree, `_decode_commit` 314-336, used at 1137)

- **G1 (security; both reviewers).** The ASCII check decodes one sample of printable ASCII, so multibyte and stateful codecs pass it and then swallow ASCII in a real message: `encoding ISO-2022-JP` with `ESC $ B` before `/Users/<seg>/x` or `/home/...` (round 6 hit, round 7 OK; the `/home/` and `AppData` forms look at no preceding character, so no UTF-8 text could hide them in round 6); `Shift_JIS`, `GBK`, `Big5` lead bytes swallowing a drive letter or a name's first letter; `unicode_escape` turning `\n` in `E:\new\...` into a line feed. The security audit counted 93 codecs that pass the check, 85 of them able to hide a path the UTF-8 reading finds.
- **G2 (behaviour against the owner's decision of 2026-11-18; the security audit).** git writes the author and committer lines in UTF-8 whatever `i18n.commitEncoding` says; decoded as ISO-8859-1, a configured identity holding a non-ASCII letter no longer equals `user.name`, so its lines lose the exemption and a searched name in them is a false hit (round 6 OK, round 7 HIT author, HIT committer).
- **Advisory.** `encoding idna` passes the check and the final replacing decode raises, so every such commit is refused (`internal error`, exit 2); `unicode_escape`'s check writes a DeprecationWarning carrying the program's path to stderr; several `encoding` lines, the last usable one wins where git reads the first.
- **Held.** The supervisor's cases, the section "the third resolution: a header never hides a hit" of tests/test_program_push_scan.py and the two guard cases above it: 7 of the 11 fail on round 7's tree, all 11 pass on round 6's code (run/agent/TASK-067-r8-known-r7.out and -r6.out).

## The supervisor's proposal: draw the line at M1

1. **M1 stays** (a segment begins with any non-ASCII character that is not whitespace): it alone closes Review B's finding for paths, in a message and in a file, whatever the encoding, and both reviewers found it right.
2. **M2 is withdrawn**: the commit object is decoded as UTF-8 with replacement, exactly as in round 6; `_decode_commit` goes.
3. **Accepted limit** (R-087, DESIGN C2, replacing round 7's): a non-ASCII name in text written in an encoding other than UTF-8 is not matched, in a file's lines or in a message, whatever its header records; a path in it is found by M1.
4. **Reasoning.** M2 served one case only, a non-ASCII account name in a message git records in a legacy encoding; every way of honouring the header adds a reading an attacker chooses, and the first try showed how wide that surface is. Withdrawing it returns to the reading rounds 1 to 6 were reviewed on.

## Alternatives to weigh

- **A (Review A's suggestion).** Keep M2 but accept the header's encoding only where its reading keeps this object's ASCII exactly (the decoded text's characters below U+0080, in order, equal the object's bytes below 0x80), else UTF-8. Closes G1's cases; G2 still needs the identity decided from the UTF-8 reading; the idna and warning advisories need a guarded decode.
- **B (the security audit's suggestion).** Read the object as UTF-8 always, as round 6 did, and where the header names a usable codec read it in that codec too, reporting the union of each place's kinds; the identity exemption decided from the UTF-8 line and applied to both readings. No header can remove a hit; a non-ASCII name in a legacy-encoded message is found.

## What the vote should engage

Whether M1 alone leaves any route by which a path the scan should find in a message or a file passes (an encoding in which a path's ASCII bytes do not stand as ASCII is UTF-16 or UTF-32, already decided or a limit); whether the limit in 3 is acceptable for R-087's names, given that a non-ASCII account name in a legacy-encoded message is the only case it gives up; and, if not, which of A or B, with what it must add for G2 and the advisories.

## Review B's vote on the third resolution (gpt-5.6-sol-high): OWN

Review B confirmed the SCOPE file's class line on round 6's code (ISO-8859-1 message and file line: OK; with M1 alone: both hit). It rejected the proposal because its premise that M1 covers paths whatever the encoding is false: in IBM037 (EBCDIC) a path's ASCII characters are not ASCII bytes, so a correctly labelled IBM037 message and an IBM037 file line holding a drive path both passed with M1 alone. It rejected A because one alternate decoding can hide a UTF-8 non-ASCII name while keeping every ASCII byte. Its own proposal: M1 and an unconditional UTF-8 baseline; the commit's framing parsed as ASCII bytes; the message payload alone decoded in the first usable `encoding` header as well, its findings united with the baseline's; codec lookup, decoding and warnings guarded; the alternate reading never used for the identity exemption; and the remaining routes accepted explicitly (a non-UTF-8 name, and a non-ASCII-compatible path, in a message with no usable header, in the author and committer lines, in file lines and in file names). `review-guard.py verify TASK-067-r5`: OK; `pr-activity-check.py 180`: OK.

## Review A's vote on the third resolution (claude-opus-5-5): OWN

Review A measured four copies (round 6, round 7, round 7 with M2 withdrawn, and that plus ESC and SO as segment starts) on fourteen scratch repositories and the test file. It agreed M2 must go and judged A and B not worth their surface: A is subtle, covers messages only and still needs G2's fix; B is safe by construction but gains only a header-labelled legacy message (git writes the header only where `i18n.commitEncoding` is set) while the same text in a file stays unread. It found the proposal's claim that M1 covers every encoding false in a second way: the ISO-2022 family (JP, KR, CN) writes a segment's non-ASCII first character as an ASCII shift (`ESC $ B`, or SO), so no non-ASCII character follows the separator; round 6, round 7 and the proposal all pass an ISO-2022-JP file line and an ISO-2022-KR one, and the proposal gives up the header-labelled message round 7 caught. One condition closes the family in messages and files with no codec: ESC (0x1B) and SO (0x0E) begin a segment; the whole test file passes with it but for M2's own case. Remaining, to be stated as limits: HZ and UTF-7 (UTF-7 writes even the backslash as `+AFw-`), EBCDIC, UTF-16 without a mark, UTF-32. Leads: two-byte legacy pairs that decode as U+00A0 or U+0085 (whitespace) at a segment's start; a drive letter or name directly after a CJK or kana character is bounded (`_bound`, `has_name`), an older behaviour route.

## The decision on the third resolution

Review A's proposal, with Review B's routes named in the limit (docs/CHANGES.md, "2026-11-18 TASK-067: the encoding header withdrawn, ESC and SO begin a segment, the third resolution round (R-087)"): M2 withdrawn (the commit object read as UTF-8 with replacement, as in rounds 1 to 6; the identity exemption from that reading, as before); M1 stays; ESC and SO also begin a segment; the limits stated in full. Review B's union reading is not taken: every route it would close in a header-labelled message stays open in a file, where no header exists, so a commit made to hide a path loses nothing by it, while the reading adds a codec the commit chooses.

# The fourth resolution: round 9's regression (2026-11-18)

## The question

Review B, the pull request's round on round 8's tree (snapshot TASK-067-r6), rejected it: a searched name holding a sharp s, written `SS` in a commit's added line, passed, because `has_name` matched with `re.IGNORECASE`, which folds one character to one. The supervisor decided (docs/CHANGES.md, the top entry): a name is found where the text and the name are equal under Unicode's compatibility caseless matching (each side NFKC, `casefold`, NFKC), searched as a whole word with the existing boundaries on the folded text. Round 9 (handoff/TASK-067-r9.md) built exactly that (`_caseless` and `has_name`, push-scan.py 133-147); both reviewers confirmed its class line on round 8's code, and both rejected it on a regression round 9 caused. A fix that regresses is not lifted by a class line (decide.md, "Stop"). How should the name match be corrected so that nothing round 8 found is lost and round 9's five spellings are still found?

## The findings (bridge/cursor-bridge/push-scan.py at this file's commit, round 9's tree)

- **H1 (security, a regression; both reviewers).** Folding the whole text changes the characters around a name, and the whole-word test is judged on the changed text: NFKC turns many symbols into letters, so a name directly beside one is no longer a whole word. Reproduced end to end, round 8 HIT and round 9 OK: a name followed by U+2122 (trade mark sign), U+2120, U+2121 or U+1F130; U+2116 (numero) or U+24D0 (circled a) before a name; a name followed by U+0345 (a combining mark that folds to iota) or by U+0301 (which NFKC composes into the name's last letter). Sweeps of every code point: Review A counted 785 characters after a name and 773 before it that round 8 catches and round 9 misses; the security audit 894 characters that are neither letter, digit nor mark but fold to contain one.
- **H2 (security, a regression; the security audit).** `re.IGNORECASE` matches U+0130 (capital I with a dot) and U+0131 (dotless i) to `i`; `casefold` does not. A name `Ilker` written `ILKER` with a dotted capital, or `lker` after a dotless i, and a names-file name holding U+0130 written with a plain `I`: round 8 HIT, round 9 OK. A sweep against the 26 ASCII letters found exactly these two characters.
- **Advisory (the security audit).** NFKC is quadratic on hostile text in CPython 3.12 (Unicode 15.0): alternating combining marks, 160k characters 4.9 s, 320k 20.3 s; U+FDFA repeated, 200k 6.5 s; round 8 was linear. A hang, never a pass. A spelling only folding equates beside one of H1's symbols (`KELSSOVAN` and U+2122) is missed by round 8 and round 9 alike.
- **Held.** The supervisor reproduced every H1 and H2 case in process (run/supervisor/probe_r9_audit_067.py): round 8 finds all nine, round 9 none, the union of the two all nine; round 9's own sharp s case is found by round 9 and the union only. Round 9's builder's own mutants W2 and W3 (an NFKC pass dropped) survived its cases; the supervisor added one case for each (a name holding U+1D2C written plainly; a name ending in `j` beside j with a caron, no hit), each failing under its mutant and passing on round 9 (Review A).

## The supervisor's proposal: the union, as both reviewers proposed

1. **`has_name` returns true where round 8's match or the folded match finds a name**: round 8's pattern on the text as written with `re.IGNORECASE`, exactly as round 8 had it, or round 9's pattern on the folded text with the folded name. Each only adds hits, so nothing round 8 found is lost (H1 and H2 closed by construction) and round 9's five spellings stay found.
2. **R-087's wording** changes from "a name is found where the text and the name are equal under Unicode's compatibility caseless matching" to "a name is found as a whole word in the text as written in any letter case, or as a whole word where the text and the name are equal under Unicode's compatibility caseless matching".
3. **Leads** (docs/HARDENING.md): a spelling only folding equates beside a symbol that folds to letters (both readings miss it); NFKC's cost on hostile text (a hang, not a pass; UAX #15's stream-safe format bounds runs of combining marks); the folded reading's dependence on the interpreter's Unicode version.
4. **Cases.** A name followed by U+2122; U+2116 before a name; a name followed by U+0345; a name followed by U+0301; `ILKER` with a dotted capital I for the name `Ilker`; each a hit.

## Alternatives to weigh

- **A (the security audit's raw-boundary variant).** Before folding, replace every character of the text as written that is not a letter, digit or combining mark with a space, then fold and search, and take the union with round 8's match. It also closes `KELSSOVAN` beside U+2122 (the lead in 3), at the cost of a second transformation whose own boundary cases (a mark that folds to a letter, such as U+0345, is kept and still joins the name) would need their own cases.
- **B.** Fold per word of the text as written (split at characters that are not word characters, fold each word, compare whole words to the folded name). The boundary is then always the raw one; a name holding punctuation or spanning a split needs its own rule.

## What the vote should engage

Whether the union leaves any route by which a spelling round 8 or round 9 found is now missed; whether the lead in 3 (a folding-only spelling beside a symbol that folds to letters) is acceptable as a lead, or A's added transformation is worth its own boundary cases; whether the cost advisory needs a bound in this round (it is a hang, never a pass) or is a lead; and anything the proposal's wording of R-087 gets wrong.
