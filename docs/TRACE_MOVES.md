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
