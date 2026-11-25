# TASK-087b round 2 report

## Summary

Round 2 fixes the digest hook and three cap tests so a cut second part stays within `MAX_OUTPUT` (shorter cap label `the second part`), cap tests assert 10,500 whole and 8,800 per part split at `<!-- digest:part -->`, an empty first part with a marker gets a true continuation placeholder, repeated marker lines are dropped from printed output, and `--part digest-2` with no marker writes no bytes; the module docstring documents `--part all` and restores the bridge-project sentence wrap; CLI reference and MANIFEST were regenerated; all 22 acceptance tests pass unedited.

## Files changed

- `bridge/cursor-bridge/session-start.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `docs/CLI_REFERENCE.md`
- `docs/cli-reference.json`
- `tests/test_session_start.py`
- `tests/test_loop_text_pace.py`
- `tests/test_a5_followups.py`
- `tests/test_release_s_budgets.py`
- `handoff/TASK-087b-r2-report.md`

`tests/test_allowlist.py`: no edit (unchanged from round 1).

## Requirements

- **Requirement 1 (R4):** `main` (line 688) passes `"the second part"` (16 characters) to `cap`; cut output is at most `MAX_OUTPUT` per `test_r2_a_cut_part_never_passes_max_output[digest-2]` (was 9802 with the 24-character label).
- **Requirement 2 (R7):** `test_digest_is_at_the_head_and_within_what_a_compaction_keeps`, `test_r042_the_digest_stays_within_its_cap_with_every_rule_number`, and `test_the_changelog_entry_exists_and_the_digest_is_unchanged_in_size` each assert whole at 10,500 and split at `<!-- digest:part -->` with each part at 8,800; `test_r2_each_cap_test_holds_the_whole_and_each_part` passes on source text.
- **Requirement 3 (R1):** `digest_part` (lines 631-640) with `continues_in_second` and `main` (line 686) use a placeholder when `split and not digest1`; output line from acceptance: `(the first part of the digest is empty here; the standing rules and permissions continue in the second part; re-read supervisor.md for the full text)`.
- **Requirement 4 (R2):** `split_digest` (lines 256-259) drops later marker lines from the second slice; no part prints `digest:part` per `test_r2_a_repeated_marker_line_is_never_printed`.
- **Requirement 5 (R2):** `main` (lines 689-690) writes only when `parts` is non-empty; `test_r2_the_second_part_without_the_marker_writes_nothing_at_all` asserts `raw == b''`.
- **Requirement 6 (R6):** Module docstring documents `--part all` (lines 34-37) and keeps the bridge-project sentence unbroken across words (lines 78-80); `python tools/dump-cli.py --check` exit 0.
- **Requirement 7 (R7 docstring):** `tests/test_release_s_budgets.py` lines 8-10 name `tests/test_improve_digest_parts.py`, `tests/test_session_start.py`, `tests/test_loop_text_pace.py`, and `tests/test_a5_followups.py`.

Plan quote 9,477 characters before the marker (brief Context): not read from an output. Checkpoint whole slice 9,500 before the marker (brief Context): not read from an output. Whole and each-part counts on the tree now: `test_r109_the_whole_digest_is_at_most_10500_and_each_part_at_most_8800` passes silently (not read from an output).

## R7 assertion changes (round 2)

### `tests/test_session_start.py`

- Whole: `assert len(whole) <= 10500` (unchanged from round 1).
- Added: split at `<!-- digest:part -->`, `assert len(part1) <= 8800` and `assert len(part2) <= 8800` with messages naming first/second part and count.

### `tests/test_loop_text_pace.py`

- Whole: `assert len(d) <= 10500` (unchanged from round 1).
- Added: same marker split and 8,800 assertions on inner digest lines.

### `tests/test_a5_followups.py`

- Whole: `assert len(whole) <= 10500` (unchanged from round 1).
- Added: same marker split and 8,800 assertions.

### `tests/test_b2_least_confident.py`

- Line 55 `"chars": 9500` unchanged (status-file shape, not the digest cap).

## Scratch test

No scratch test file (round 2 constraint).

## Mutation code points (K1-K4 and K5-K8)

- **K1** (second part never printed): `main` lines 687-688; caught by `test_r109_part_digest_2_prints_a_header_of_its_own_and_the_text_after_the_line`.
- **K2** (marker printed inside a part): `split_digest` lines 256-259; caught by `test_r109_part_digest_prints_its_header_and_the_text_before_the_line` and `test_r2_a_repeated_marker_line_is_never_printed`.
- **K3** (first part prints whole digest): `main` line 686 uses `digest1`; caught by `test_r109_part_digest_prints_its_header_and_the_text_before_the_line`.
- **K4** (second part uncut by cap): `main` line 688 `cap(digest_part_2(...), MAX_OUTPUT, ...)`; caught by `test_r109_each_part_is_cut_by_the_cap_and_the_note_names_the_part[digest-2]`.
- **K5** (cut note longer than room): `main` line 688 cap label passed to `cap`; caught by `test_r2_a_cut_part_never_passes_max_output[digest-2]`.
- **K6** (placeholder says no digest beside digest): `digest_part` lines 635-637; caught by `test_r2_a_marker_first_never_says_no_digest_was_found`.
- **K7** (later marker line printed inside a part): `split_digest` lines 258-259; caught by `test_r2_a_repeated_marker_line_is_never_printed`.
- **K8** (nothing to print writes a line feed): `main` lines 689-690; caught by `test_r2_the_second_part_without_the_marker_writes_nothing_at_all`.

## Missing acceptance cases

None.

## Commands and output

Commit for final counts: `cd4da8fbe78067e28830f8ab2bd5e642a095a7aa` (working tree uncommitted after step 12).

### 1. `git status --short` (before first edit)

```
```

### 2. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_digest_parts.py` (before first edit)

```
7 failed, 15 passed in 2.89s
```

Failing ids:

```
test_r2_a_cut_part_never_passes_max_output[digest-2]
test_r2_a_marker_first_never_says_no_digest_was_found
test_r2_a_repeated_marker_line_is_never_printed
test_r2_the_second_part_without_the_marker_writes_nothing_at_all
test_r2_each_cap_test_holds_the_whole_and_each_part[tests/test_session_start.py]
test_r2_each_cap_test_holds_the_whole_and_each_part[tests/test_loop_text_pace.py]
test_r2_each_cap_test_holds_the_whole_and_each_part[tests/test_a5_followups.py]
```

### 3. `python tools/dump-cli.py` then `python tools/dump-cli.py --check` (after last edit)

```
```

(Exit code 0 for both; `--check` prints nothing on success.)

### 4. `python tools/make-manifest.py` (after last edit)

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

### 5. `git status --short` (after manifest)

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/session-start.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_a5_followups.py
 M tests/test_loop_text_pace.py
 M tests/test_release_s_budgets.py
 M tests/test_session_start.py
```

(`bridge/cursor-bridge/VERSION` not listed; no restore needed.)

### 6. Scoped pytest (final)

```
336 passed, 20 skipped in 18.04s
```

Skip reasons (`-rs`):

```
SKIPPED [10] tests\test_allowlist.py:87: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:128: prose, not a runnable command
```

`tests/test_improve_digest_parts.py` (final):

```
22 passed in 13.80s
```

### 7. Out-of-scope pytest (final)

```
389 passed, 4 skipped in 316.52s (0:05:16)
```

Skip reasons (`-rs`):

```
SKIPPED [1] tests\test_session_start_module.py:312: this account cannot make a file link
SKIPPED [3] tests\test_session_start_module.py:574: this account cannot make a file link
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.24a (2026-11-25 18:17) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>\bridge\cursor-bridge
```

### 9. `git grep -n -e "9,500" -e "9500" -- bridge tests`

```
bridge/cursor-bridge/CHANGELOG.md:119:- **The tests that pin wording alone are retired** (S1): 6 size and hash pins (122 cases), 5 per-file caps (18 cases), the 34 prose-literal tests this release's text touched (42 cases) and 3 pins on a record's wording are retired, 48 functions and 185 cases of 5,289 (the list below, by file and name; approved by the owner by file and count on 2026-11-12). The register follows: R-032's sentence is revised in place (the two word budgets for the 1,500 lines and 60,000 characters per module), and where a retired test was a label's only evidence the cell names the text (R-042, R-045, R-049, R-050, R-051; R-047's cell is reworded where it named a retired test). Kept: the digest's cap of 9,500 characters, every value the owner chose, every line a program parses. A kept test may still hold an instruction sentence beside the value or the line it checks; such a literal goes when the test is next touched. In their place two word budgets held by `tests/test_release_s_budgets.py`: the rulebook (every `.md` under `bridge/` except this file and the design seeds) at 150,000 words, and each phase or step file at 8,000. An increment that changes instruction text alone has no wording test and no mutation run; its register row takes the text form of Evidence, `text: <file>.md :: <heading> (#<pull request>)`. The form exists only in a project whose `project.json` declares where its instruction texts are (`instruction_texts`, a list of folders, never a record folder; this repository declares `bridge/`), which is no project whose product is ordinary software: there a text entry fails. `completion-check.py` verifies each entry: the file under a declared folder, the heading outside a code block, the pull request's squash on `origin/main` and having changed that file. For a row whose sentence names a program a text entry never counts; its test stands beside it.
tests/test_b2_least_confident.py:55:        "chars": 9500,
tests/test_improve_digest_parts.py:330:    end marker, as the four tests measured 9,500) and each part at most 8,800 (its text as the hook prints it).
tests/test_improve_digest_parts.py:488:    the digest at 9,500 characters hold the whole digest at 10,500 and each part at 8,800"): each of the three tests
tests/test_improve_digest_parts.py:495:    assert "9500" not in src, "%s no longer holds the old cap" % rel
```

- `CHANGELOG.md:119`: history (S1 release note).
- `test_b2_least_confident.py:55`: not digest cap (fixture field); left unchanged.
- `test_improve_digest_parts.py:330`, `:488`, `:495`: supervisor acceptance file (out of scope to edit); history or intentional source checks, not live digest caps.

### 10. `git diff --stat`

```
 bridge/cursor-bridge/MANIFEST.json    |  4 ++--
 bridge/cursor-bridge/session-start.py | 34 +++++++++++++++++++++++-----------
 docs/CLI_REFERENCE.md                 | 12 +++++++-----
 docs/cli-reference.json               |  2 +-
 tests/test_a5_followups.py            | 11 ++++++++++-
 tests/test_loop_text_pace.py          |   8 ++++++++
 tests/test_release_s_budgets.py       |  3 ++-
 tests/test_session_start.py           | 11 ++++++++++-
 8 files changed, 63 insertions(+), 22 deletions(-)
```

### 11. `git diff -- bridge/cursor-bridge/session-start.py bridge/cursor-bridge/settings.bridge.json`

```
diff --git a/bridge/cursor-bridge/session-start.py b/bridge/cursor-bridge/session-start.py
index 8da58c9..3153dd3 100644
--- a/bridge/cursor-bridge/session-start.py
+++ b/bridge/cursor-bridge/session-start.py
@@ -30,9 +30,11 @@ only where it holds a command the settings file lacks):
                     <!-- digest:part --> when present, else the whole digest), the core
                     before the standing rules;
   --part digest-2   the second part: text after <!-- digest:part --> when present (else
-                    nothing).
+                    nothing);
+  --part all        the pointers, the digest's first part and, where the marker stands, the
+                    second part, each as its own --part prints it (tests, manual runs).
 
-Without --part both the pointers and both digest parts are printed (tests, manual runs).
+Without --part, the same as --part all.
 
 Pointer-line grammar (module files under workflow/phases/, read as UTF-8 with BOM dropped):
 a line outside fenced blocks (opening_fence / closing_fence as workflow-check.py reads them;
@@ -73,9 +75,9 @@ hand-edited
 install, not a hostile checker, which runs in-process and could write to its output directly.
 The hook still never blocks.
 
-It prints nothing outside a bridge
-project (no docs/PROJECT_STATUS.md found from the session's folder, its Workspace, a parent,
-or a worktree). It FAILS OPEN on purpose: a session that is not the project's supervisor
+It prints nothing outside a bridge project (no docs/PROJECT_STATUS.md found from the session's
+folder, its Workspace, a parent, or a worktree).
+It FAILS OPEN on purpose: a session that is not the project's supervisor
 (a review or a planning session opened in a project folder) is told to ignore the message,
 because a gate on the transcript silenced the hook on two of three live supervisor sessions
 (one invoked through the Skill tool, one continuing an earlier transcript; the 0b review's
@@ -252,7 +254,9 @@ def split_digest(digest):
     lines = digest.split("\n")
     for i, line in enumerate(lines):
         if line.strip() == DIGEST_PART_MARK:
-            return "\n".join(lines[:i]).strip(), "\n".join(lines[i + 1:]).strip(), True
+            first = "\n".join(lines[:i]).strip()
+            rest = [ln for ln in lines[i + 1:] if ln.strip() != DIGEST_PART_MARK]
+            return first, "\n".join(rest).strip(), True
     return digest, "", False
 
 
@@ -624,9 +628,16 @@ def pointers_part(status, source, status_path):
     return "\n".join(out)
 
 
-def digest_part(digest, version):
+def digest_part(digest, version, continues_in_second=False):
     head = "CLAUDE-CURSOR BRIDGE core digest (bridge %s) - the condensed core of ~/.claude/commands/supervisor.md; the full text governs:" % version
-    return head + "\n\n" + (digest if digest else "(no digest found in supervisor.md; re-read the whole file)")
+    if digest:
+        body = digest
+    elif continues_in_second:
+        body = ("(the first part of the digest is empty here; the standing rules and permissions "
+                "continue in the second part; re-read supervisor.md for the full text)")
+    else:
+        body = "(no digest found in supervisor.md; re-read the whole file)"
+    return head + "\n\n" + body
 
 
 def digest_part_2(body, version):
@@ -672,10 +683,11 @@ def main():
         else:
             parts.append(cap(pointers, MAX_OUTPUT, "the section pointers"))
     if part in ("digest", "all"):
-        parts.append(cap(digest_part(digest1, version), MAX_OUTPUT, "the digest"))
+        parts.append(cap(digest_part(digest1, version, split and not digest1), MAX_OUTPUT, "the digest"))
     if part in ("digest-2", "all") and split:
-        parts.append(cap(digest_part_2(digest2, version), MAX_OUTPUT, "the digest's second part"))
-    sys.stdout.write("\n\n".join(parts) + "\n")
+        parts.append(cap(digest_part_2(digest2, version), MAX_OUTPUT, "the second part"))
+    if parts:
+        sys.stdout.write("\n\n".join(parts) + "\n")
     return 0
 
 
```

`settings.bridge.json`: no diff (unchanged since round 1).

Non-ASCII added in the `session-start.py` diff: none.

### 12. `git rev-parse HEAD` and `git status --short`

```
cd4da8fbe78067e28830f8ab2bd5e642a095a7aa
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/session-start.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_a5_followups.py
 M tests/test_loop_text_pace.py
 M tests/test_release_s_budgets.py
 M tests/test_session_start.py
```

(`VERSION` not listed; no `tests/test_task087b_scratch_` file.)

## Assumed, not verified

- Where the marker is the first line of the digest and the first part is empty, the continuation placeholder is acceptable to the supervisor; confirmed only by `test_r2_a_marker_first_never_says_no_digest_was_found` | why: no brief line quoted the exact wording | what would confirm it: owner acceptance of the placeholder sentence on a live compaction.
- Whether Claude Code measures hook output caps in characters or bytes | why: host unit not stated in the brief | what would confirm it: a host probe beyond `run/supervisor/probe-087b.md` with byte and character counts side by side.
- `--part digest-2` with a marker present but no text after it prints only the second-part header and its empty-body placeholder | why: edge not named in either brief | what would confirm it: an acceptance case or owner decision on that output shape.