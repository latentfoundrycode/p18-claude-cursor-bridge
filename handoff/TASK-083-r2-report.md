# TASK-083 round 2 report

## Files changed

- `bridge/cursor-bridge/permission-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (by `python tools/make-manifest.py` only)
- `tests/test_permission_guard.py`
- `docs/BUILDER_NOTES.md` (one dated line, written after step 11)
- `handoff/TASK-083-r2-report.md` (this report, written after step 11)

`tests/test_program_ready.py` was not edited. `bridge/cursor-bridge/VERSION` was restored with `git restore` after `make-manifest.py` and is not in the step 11 status. `docs/BUILDER_NOTES.md` and this report were written after step 11, so they are absent from that status.

## Summary

`merge_reason` now takes the head, the exemptions and the pull-request number from one pflag-style reading of the words after `gh pr merge` (`_read_merge_words`), so a flag's value and the tail of a short-flag cluster are never the sha, `--disable-auto`, the help, or the number, and `ready_recorded` no longer counts a ready name that ends in `.tmp`.

## H1-H4

H1. `_read_merge_words` (lines 2479-2547) reads the words after `merge` once, and `merge_reason` (lines 2550-2568) takes from that reading the last `--match-head-commit` value, the exemptions `--disable-auto` and the help (`--help`, or the word `-h` alone) only as options, and the single positional as the number, then refuses in round 1's order: `--admin` (lines 2552-2553), the exemptions (lines 2555-2556), no sha (lines 2557-2558), a malformed sha (lines 2559-2560), the number (lines 2561-2563), `premerge_recorded` (lines 2564-2565), `ready_recorded` (lines 2566-2567).

H2. Nothing returns None from `merge_reason` before the records are read except those two exemptions, at lines 2555-2556, and only when `_read_merge_words` found them as options.

H3. `ready_recorded` (lines 2451-2476) keeps the prefix match and, at line 2476, does not count a name whose lowered form ends in `.tmp`.

H4. Deleted `test_r083_ready_recorded_fails_closed_outside_a_repository` from `tests/test_permission_guard.py`, and added `test_r083_r2_a_second_positional_and_a_word_after_end_of_options_are_refused` (lines 281-291) for the gap the supervisor's section leaves open: two positionals when the first is the recorded pull request and the head matches, words after `--`, a trailing `--match-head-commit` with no value, and `-h` alone.

## Defects

1. The sha is only the last `--match-head-commit` option in `_read_merge_words`, which gives the next word to a value-taking flag even when that word begins with `-`, so `--subject --match-head-commit=A` (and `-t` or `-b` the same way) is a subject and the earlier head stays the sha.

2. `--disable-auto` and the help are exemptions only when that reading finds them as options, so `gh pr merge 12 --squash --subject --disable-auto` is not exempted and is refused for having no sha.

3. The number is the one positional after a short cluster is read letter by letter, a letter in `GH_VALUE_FLAGS` (`t`, `b`, `F`, `A`, `R`) taking the rest of the word or the next word, so `gh pr merge -sb 12 34 --match-head-commit <sha>` names pull request 34.

## Commands run before the Done list

### `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py -k "r083_r2 or r083_a_merge or r083_the_guard or r083_the_ready_record" tests/test_permission_guard.py -k "r083_r2 or test_a_merge_with_the_premerge"`

```
...........................................                              [100%]
43 passed, 357 deselected in 9.49s
```

### `python -m pytest -p no:cacheprovider -q -rfE tests/test_permission_guard.py --tb=line`

```
........................................................................ [ 24%]
........................................................................ [ 48%]
........................................................................ [ 72%]
........................................................................ [ 97%]
........                                                                 [100%]
296 passed in 30.21s
```

### `git diff --stat && git diff -- bridge/cursor-bridge/permission-guard.py tests/test_permission_guard.py`

```
 bridge/cursor-bridge/permission-guard.py | 97 ++++++++++++++++++++++++--------
 tests/test_permission_guard.py           | 20 ++++---
 2 files changed, 88 insertions(+), 29 deletions(-)
diff --git a/bridge/cursor-bridge/permission-guard.py b/bridge/cursor-bridge/permission-guard.py
index 45ef2da..5b1f25b 100644
--- a/bridge/cursor-bridge/permission-guard.py
+++ b/bridge/cursor-bridge/permission-guard.py
@@ -2473,39 +2473,92 @@ def ready_recorded(pr, sha, cwd):
     except OSError:
         return False
     prefix = ("%s-%s" % (pr, sha)).lower()
-    return any(name.lower().startswith(prefix) for name in names)
+    return any(name.lower().startswith(prefix) and not name.lower().endswith(".tmp") for name in names)
+
+
+def _read_merge_words(args):
+    """The words after `gh pr merge`, read once as gh reads them (pflag).
+    Returns the last `--match-head-commit` value (None when that option is absent, "" when nothing follows it), whether `--disable-auto` or the help (`--help`, or the word `-h` alone) stands as an option, and the positional words. A flag's value is never an option, and every word after `--` is a positional."""
+    long_value = tuple(flag for flag in GH_VALUE_FLAGS if flag[:2] == "--")
+    short_value = tuple(flag[1] for flag in GH_VALUE_FLAGS if len(flag) == 2 and flag[0] == "-" and flag[1] != "-")
+    sha = None
+    disable_auto = False
+    help_opt = False
+    positionals = []
+    ended = False
+    i, n = 0, len(args)
+    while i < n:
+        word = args[i]
+        if ended:
+            positionals.append(word)
+            i += 1
+            continue
+        if word == "--":
+            ended = True
+            i += 1
+            continue
+        if len(word) > 1 and word[0] == "-" and word[1] == "-":
+            name, eq, value = word.partition("=")
+            if eq:
+                if name == "--match-head-commit":
+                    sha = value
+                i += 1
+                continue
+            if word in long_value:
+                if i + 1 < n:
+                    value = args[i + 1]
+                    i += 2
+                else:
+                    value = ""
+                    i += 1
+                if word == "--match-head-commit":
+                    sha = value
+                continue
+            if word == "--disable-auto":
+                disable_auto = True
+            elif word == "--help":
+                help_opt = True
+            i += 1
+            continue
+        clustered = len(word) > 1 and word[0] == "-"
+        if clustered:
+            for ch in word[1:]:
+                if not (("A" <= ch <= "Z") or ("a" <= ch <= "z")):
+                    clustered = False
+                    break
+        if clustered:
+            body = word[1:]
+            k = 0
+            while k < len(body):
+                if body[k] in short_value:
+                    if body[k + 1:] or i + 1 >= n:
+                        i += 1
+                    else:
+                        i += 2
+                    break
+                k += 1
+            else:
+                i += 1
+            if word == "-h":
+                help_opt = True
+            continue
+        positionals.append(word)
+        i += 1
+    return sha, disable_auto, help_opt, positionals
 
 
 def merge_reason(args, cwd):
     """The reason to refuse a gh pr merge (args = the words after `merge`), or None."""
     if any(a == "--admin" or a.startswith("--admin=") for a in args):
         return "gh pr merge --admin (merging past the repository's rules)"
-    if "--disable-auto" in args:
+    sha, disable_auto, help_opt, positionals = _read_merge_words(args)
+    if disable_auto or help_opt:
         return None
-    for i, a in enumerate(args):
-        if a in ("--help", "-h") and (i == 0 or args[i - 1] not in GH_VALUE_FLAGS):
-            return None                                    # `--subject --help` is a subject, and gh merges
-    sha = None
-    for i, a in enumerate(args):
-        if a == "--match-head-commit":
-            sha = args[i + 1] if i + 1 < len(args) else ""
-        elif a.startswith("--match-head-commit="):
-            sha = a.split("=", 1)[1]
     if sha is None:
         return "gh pr merge without --match-head-commit <sha>: the sha, and the record review-guard.py premerge writes when it prints OK, are the gate's confirmation"
     if not re.fullmatch(r"[0-9a-fA-F]{7,64}", sha):
         return "gh pr merge with an empty or malformed --match-head-commit value"
-    number, i = None, 0
-    while i < len(args):
-        word = args[i]
-        if word in GH_VALUE_FLAGS:
-            i += 2
-            continue
-        if word.startswith("-"):
-            i += 1
-            continue
-        number = word
-        break
+    number = positionals[0] if len(positionals) == 1 else None
     if number is None or any(char < "0" or char > "9" for char in number):
         return "gh pr merge without the pull request's number: gh pr merge <n> --squash --match-head-commit <sha>"
     if not premerge_recorded(sha, cwd):
diff --git a/tests/test_permission_guard.py b/tests/test_permission_guard.py
index 42b0e33..817ab24 100644
--- a/tests/test_permission_guard.py
+++ b/tests/test_permission_guard.py
@@ -269,13 +269,6 @@ def test_r082_graphql_query_with_literal_quotes_passes_under_bash_only():
     assert rc == 2 and "cannot read" in err.lower(), err
 
 
-def test_r083_ready_recorded_fails_closed_outside_a_repository(tmp_path, program):
-    """R-083: ready_recorded is false outside a repository (D-003 ready_recorded is not reached)."""
-    guard = program("permission-guard")
-    assert guard.ready_recorded("12", SHA, str(tmp_path)) is False
-    assert guard.ready_recorded("12", "not-a-sha", str(tmp_path)) is False
-
-
 @pytest.mark.parametrize("command", ["cmd /c echo agent", "cmd /c dir agent"])
 def test_r082_cmd_single_slash_passes_under_powershell_and_is_unreadable_under_bash(command):
     """R-082 round 7 req 6: Git Bash rewrites a single-slash cmd switch; PowerShell does not."""
@@ -283,3 +276,16 @@ def test_r082_cmd_single_slash_passes_under_powershell_and_is_unreadable_under_b
     assert rc == 0, (command, err)
     rc, err = run("Bash", command)
     assert rc == 2 and "cannot read" in err.lower(), (command, err)
+
+
+@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
+def test_r083_r2_a_second_positional_and_a_word_after_end_of_options_are_refused(tool, recorded_repo):
+    """R-083: the number is the one positional, so a second positional is refused where the first is the recorded pull request; a word after -- is a positional, so --disable-auto there is not an exemption; a value-taking flag with no following word has the empty value; -h alone is the help."""
+    two, err = run(tool, "gh pr merge 12 34 --squash --match-head-commit " + SHA, cwd=recorded_repo)
+    assert two == 2 and "pull request's number" in err, err
+    ended, err = run(tool, "gh pr merge 12 -- --disable-auto --match-head-commit " + SHA, cwd=recorded_repo)
+    assert ended == 2 and "--match-head-commit" in err, err
+    empty, err = run(tool, "gh pr merge 12 --squash --match-head-commit", cwd=recorded_repo)
+    assert empty == 2 and "malformed" in err, err
+    help_rc, help_err = run(tool, "gh pr merge -h", cwd=recorded_repo)
+    assert help_rc == 0, help_err
```

Steps 1-6 below were one foreground shell, and steps 10-11 were another; each block quotes the lines that command printed.

## Done

### 1. `git status --short`

```
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_permission_guard.py
```

### 2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 3. `git restore bridge/cursor-bridge/VERSION`

Printed no lines. Exit 0.

### 4. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_permission_guard.py
```

`bridge/cursor-bridge/VERSION` is not listed.

### 5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-17 01:07) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 6. `python tools/dump-cli.py --check`

Printed no lines. Exit 0.

### 7. `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py`

```
........................................................................ [ 69%]
................................                                         [100%]
104 passed in 46.19s
```

### 8. `python -m pytest -p no:cacheprovider -q tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_program_permission_guard.py`

```
........................................................................ [  5%]
........................................................................ [ 11%]
........................................................................ [ 16%]
........................................................................ [ 22%]
........................................................................ [ 27%]
........................................................................ [ 33%]
......................s...ss.....sss....................s............... [ 38%]
s...............................................s...........s........... [ 44%]
......s...ss.....sss....................s...............s............... [ 49%]
................................s...........s........................... [ 55%]
........................................................................ [ 60%]
........................................................................ [ 66%]
........................................................................ [ 71%]
........................................................................ [ 77%]
........................................................................ [ 82%]
........................................................................ [ 88%]
........................................................................ [ 93%]
........................................................................ [ 99%]
...........                                                              [100%]
1287 passed, 20 skipped in 105.77s (0:01:45)
```

### 9. `python -m pytest -p no:cacheprovider -q tests/test_d003_review_round_states.py tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_program_branch_rule.py tests/test_program_release_s_rows.py tests/test_tests_windowless.py`

```
........................................................................ [ 23%]
........................................................................ [ 46%]
........................................................................ [ 69%]
........................................................................ [ 92%]
.........................                                                [100%]
313 passed in 201.12s (0:03:21)
```

### 10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

### 11. `git rev-parse HEAD` and `git status --short`

```
6bc52c09a5c2e38844a02e69aa951bc68e2eb6b8
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_permission_guard.py
```

`bridge/cursor-bridge/VERSION` is not listed.

## Results

The counts above belong to commit `6bc52c09a5c2e38844a02e69aa951bc68e2eb6b8`. At step 11 the working tree held uncommitted changes to `bridge/cursor-bridge/MANIFEST.json`, `bridge/cursor-bridge/permission-guard.py` and `tests/test_permission_guard.py`. This report and the `docs/BUILDER_NOTES.md` line were written after that status.

## Assumed, not verified

- Whether gh's `pr merge` has a short flag that takes a value beyond `t`, `b`, `F`, `A` and `R`. · The brief names those five as the short forms in `GH_VALUE_FLAGS`, which this round reads and does not edit, and every acceptance cluster uses those letters. · `gh pr merge --help` on a current gh, or the flag set of `pr merge` in the gh source.
- Whether pflag reads `-` alone as a positional. · The brief states that rule, and no acceptance case uses a lone `-`. · `gh pr merge - --squash --match-head-commit <sha>` against gh's parser.
- Whether gh refuses a second positional before it merges. · H1 requires the guard to refuse more than one positional, and the added case locks that refusal where the first positional is the recorded pull request; no case asks what gh does with two numbers. · `gh pr merge 12 34 --squash --match-head-commit <sha>` in gh.
- A short cluster is only a word whose characters after the single dash are ASCII letters, so a glued value that contains a digit or a slash (`-t12`, `-Rowner/repo`) is a positional and the guard refuses. · The brief defines a cluster as one dash and one or more letters, and every other word as a positional; the acceptance cases glue only letters (`-stdone`) or pass the value as the next word. · gh's reading of `gh pr merge -t12 12 --squash --match-head-commit <sha>`.
