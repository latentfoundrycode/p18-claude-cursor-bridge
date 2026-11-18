# Trace moves

This file records the instruction passages a pull request retires, rewords or moves out of `bridge/`. `trace-check.py --moves` reads it (R-077; docs/DESIGN.md, Change: the program release, T-MOVE).

## What the mode compares

The mode compares two sets of files: every `.md` file under `bridge/` except `bridge/cursor-bridge/CHANGELOG.md`, once at the base and once at HEAD. The base is the merge-base of HEAD with `origin/main`, or with the revision `--base` names.

A passage fails when it stands in a file that changed and appears in none of these files at HEAD. A passage reworded at HEAD counts as dropped. An entry this pull request adds can excuse a passage.

## The form of an entry

An entry is one line. Paste it from the failure the mode prints; never compose it by hand:

    - <the passage's hash: 64 lowercase hex digits> <its first eight words>

- **Normal form.** The mode uses the pinned mode's normal form:
  - a paragraph, list item or table has its whitespace collapsed to single spaces;
  - a fenced block keeps its lines, each with its trailing whitespace removed.
- **Hash.** The SHA-256 of the normal form's UTF-8 bytes.
- **First words.** The normal form's first eight whitespace-separated words, joined by single spaces. They are written with the pinned mode's escaping: every character outside printable ASCII becomes `\xhh`, `\uhhhh` or `\Uhhhhhhhh`, so every entry is ASCII.
- **What it excuses.** An entry excuses the one passage whose hash and first words both match it.

## Which entries are read

- **Only the range's.** The mode reads only the entries the range adds: the lines of this file added between the base and HEAD.
- **Earlier entries are never re-read.** An entry an earlier pull request added is not read again. It cannot excuse a later drop, and it causes no later failure.
- **An entry that excuses nothing is a finding.** An added entry that excuses no passage dropped in the range is reported.
- **Other lines are ignored.** A line not of the entry's form is not read.

The file stays after the merge. A change to it takes the full gate (`review-guard.py premerge-records`).

## Entries

- c5f8ee39b31e06981b027ed0b4f1b1725551827cece72ea6c45cc4cbf7747bbf **Before a push, every commit it publishes.** When
- 03ab2e5b8cb8f1a9129a84aa4591d6e7e2b30fef436ce627161b1bc5b2b29ee6 The brief opens with its header (the core's
- 0c072589e1a539c5921f30cf255cedf1ae19bb30e916fbf96c3ede774b9e133b **The loop (Phase 6, one increment).** 1 Checkpoint:
- 83b37fecef2529da9b7d4ebaeb4eb51ec72f9175d9bef6237a3aea418f89bc3e **CI green means the run of the pushed
- dc82b5d3a57038ec4a68adc4fe06879a106a8b37466ab19236911cbade916d2c The gate decides *whether* a branch may merge;
- 6fba56023fb431ab0d59ce9fdb5f3736af132335ee1a0fc0b4adffb5cfb330e2 2. **Only if both APPROVE and no gate-integrity
- adc6a2d4462fd8ed62281d84c0a5d973352d9fdd16f8a93c9f566a88074a0b25 **Completing the merge \u2014 do not depend on
- 3fba79ea0f77c8a56291b4666c03d7ab1969c35a2f64c9116436c03517fd81a6 So the model reviews gate the *authorisation*; the
- f732d7c5992f49e4bf0043d3801cb52e2e9ee3e9b9d3dd63010a810aa729ca94 **Do not use the CI status bar's blanket
- 34551f9ad92df915406021d171c4b0a05002d7e3e73a813dfbb4d64797ff123c After a run of what a builder wrote
- 45b102dc55443ef6ba8bc07d0a2cc7cac52690a4ce911d05678d99db05e15600 **Before every push.** Every commit the push publishes
- ba5e38e006deee02c4a76f22875902edeb5d647bf925d5a5e3bcd8dbb000334c When all four hold the merge is authorised.
- 10e1e62b1f912da34f11bfcbb4abab2bffbfca49c8702c66a2444b8f8b2abf01 **Then the stage's demonstration runs live:** the build
