# TASK-075 round 3 report

## Files changed or created

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `handoff/TASK-075-r3-report.md`

## Summary

Round 3 removes round 2's fail-open `_stdout_for_probe_errors` helper and restores the probe's error-word `re.search` to run on full `out` as at `6a1434d`, so a model reply that quotes the tool's sign-in line on its own line is judged by the `Error` word and never resolves a profile, while stdout/stderr sign-in detection, UTF-8 decoding, `%a` detail strings, `PROBE_SIGN_IN`, and separate `--record-failure` file reads remain unchanged; `tool_sign_in_on_stdout` now trims each line once (R3).

## R1–R4

- **R1:** `_stdout_for_probe_errors` and `err_probe` are removed; in `probe` (lines 258–260) the error-word `re.search` runs on `out`.
- **R2:** Round 2 behaviour remains: `tool_sign_in_on_stdout` (218–225), `tool_sign_in_on_stderr` (210–215), `_lf_lines` / `_trim_line_edges`, `PROBE_SIGN_IN` (95–104), UTF-8 on `subprocess.run` (246–248), `%a` and `_ascii_line` in probe and `record_failure`, and separate stderr/stdout in `record_failure` / `--record-failure`.
- **R3:** Taken — `tool_sign_in_on_stdout` trims each LF-split line once in the loop (220–224) instead of twice in a comprehension.
- **R4:** `roster-check.py` is ASCII with CRLF only; `python tools/make-manifest.py` refreshed `MANIFEST.json`; `VERSION` unchanged at `2026.11.12a`; `dump-cli --check` exit 0 with no reference update.

## Mutation self-check

### N1 — the stdout whole-output rule dropped: a line-start match anywhere on stdout counts, as on stderr.

Before:

```python
def tool_sign_in_on_stdout(text):
    """True when standard output is only the tool's sign-in line (one non-empty trimmed line)."""
    non_empty = []
    for line in _lf_lines(text):
        trimmed = _trim_line_edges(line)
        if trimmed:
            non_empty.append(trimmed)
    return len(non_empty) == 1 and non_empty[0].startswith(SIGN_IN_PREFIX)
```

After:

```python
def tool_sign_in_on_stdout(text):
    """True when any whole line of standard output is the tool's sign-in line."""
    for line in _lf_lines(text):
        if _line_starts_with_sign_in(line):
            return True
    return False
```

Pytest:

```
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_judged_as_before_round_1
FAILED tests/test_program_roster_sign_in.py::test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer[banner-first]
FAILED tests/test_program_roster_sign_in.py::test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer[line-first]
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_stdout_file_with_the_line_after_other_lines_is_counted_as_today
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_stdout_file_quoting_the_line_beside_a_model_stderr_is_counted_as_today
5 failed, 43 passed in 15.14s
```

Caught: `test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer[banner-first]`

### N2 — `str.splitlines()` and bare `strip()` again in the line helpers.

Before:

```python
def _lf_lines(text):
    if not text:
        return []
    return text.split(NL)


def _trim_line_edges(line):
    return line.strip(_TRIM_EDGES)
```

After:

```python
def _lf_lines(text):
    if not text:
        return []
    return text.splitlines()


def _trim_line_edges(line):
    return line.strip()
```

Pytest:

```
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[vt]
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[ff]
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[fs]
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[nel]
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[ls]
5 failed, 43 passed in 16.10s
```

Caught: `test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[vt]`

### N3 — no UTF-8 decoding on the probe (no `encoding`/`errors` on its `subprocess.run`).

Before:

```python
        p = subprocess.run(launcher + ["-p", "-f", "--model", model_id, PROBE_PROMPT],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=PROBE_TIMEOUT, creationflags=NO_WINDOW, env=env)
```

After:

```python
        p = subprocess.run(launcher + ["-p", "-f", "--model", model_id, PROBE_PROMPT],
                           capture_output=True, text=True,
                           timeout=PROBE_TIMEOUT, creationflags=NO_WINDOW, env=env)
```

Pytest:

```
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_beyond_ascii_is_read_as_utf8
1 failed, 47 passed in 16.34s
```

Caught: `test_r095_r2_probe_a_reply_beyond_ascii_is_read_as_utf8`

### N4 — `%r` again in the probe's detail strings, and the excerpt printed raw (without `_ascii_line`).

Before:

```python
        return True, "answered off-script: %a" % out.replace(NL, " ")[:80]
    err =(p.stderr or "").strip().replace("\n", " ")[:200]
    return False, "exit %d; stdout=%a; stderr=%a" % (p.returncode, out[:80], err)
```

```python
    excerpt_out = _ascii_line(excerpt)
```

After:

```python
        return True, "answered off-script: %r" % out.replace(NL, " ")[:80]
    err =(p.stderr or "").strip().replace("\n", " ")[:200]
    return False, "exit %d; stdout=%r; stderr=%r" % (p.returncode, out[:80], err)
```

```python
    excerpt_out = excerpt
```

N4 default:

```
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_beyond_ascii_is_read_as_utf8
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_beyond_the_consoles_code_page_is_answered_and_printed_in_ascii
2 failed, 46 passed, 1 warning in 16.34s
```

N4 PYTHONIOENCODING=utf-8:

```
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_beyond_ascii_is_read_as_utf8
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_beyond_the_consoles_code_page_is_answered_and_printed_in_ascii
2 failed, 46 passed, 1 warning in 16.10s
```

Caught: `test_r095_r2_probe_a_reply_beyond_the_consoles_code_page_is_answered_and_printed_in_ascii`

### N5 — `PROBE_SIGN_IN` made truthy (for example `PROBE_SIGN_IN = object()`).

Before:

```python
PROBE_SIGN_IN = _ProbeSignInSentinel()  # falsy sentinel; main() tests ``ok is PROBE_SIGN_IN``
```

After:

```python
PROBE_SIGN_IN = object()  # falsy sentinel; main() tests ``ok is PROBE_SIGN_IN``
```

Pytest:

```
FAILED tests/test_program_roster_sign_in.py::test_r095_r3_probe_returns_a_falsy_signed_out_result_in_its_pair
1 failed, 47 passed in 16.23s
```

Caught: `test_r095_r3_probe_returns_a_falsy_signed_out_result_in_its_pair`

### N6 — round 2's change put back: the error-word `re.search` run on stdout with the lines beginning with the tool's prefix removed.

Before:

```python
    if (p.returncode == 0 and out and classify_failure(out + " " + (p.stderr or ""))[0] == "OTHER"
            and not re.search(r"(?i)\b(error|exception|failed|failure|traceback|unavailable|not available|denied|unauthori[sz]ed|forbidden"
                              r"|invalid|not found|unknown model|cannot use|not supported)\b", out)):
```

After:

```python
def _stdout_for_probe_errors(out):
    """Lines of a model stdout reply, without lines that are the tool's sign-in line (quoted on their own)."""
    parts = []
    for line in _lf_lines(out):
        trimmed = _trim_line_edges(line)
        if trimmed and not trimmed.startswith(SIGN_IN_PREFIX):
            parts.append(trimmed)
    return NL.join(parts)
```

```python
    err_probe = _stdout_for_probe_errors(out)
    if (p.returncode == 0 and out and classify_failure(out + " " + (p.stderr or ""))[0] == "OTHER"
            and not re.search(r"(?i)\b(error|exception|failed|failure|traceback|unavailable|not available|denied|unauthori[sz]ed|forbidden"
                              r"|invalid|not found|unknown model|cannot use|not supported)\b", err_probe)):
```

Pytest:

```
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_judged_as_before_round_1
FAILED tests/test_program_roster_sign_in.py::test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer[banner-first]
FAILED tests/test_program_roster_sign_in.py::test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer[line-first]
3 failed, 45 passed in 15.81s
```

Caught: `test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_judged_as_before_round_1`

## Verification commands

Commit for counts below: `5f4ae4ae71b53439d981386e7915a98dd37afee5`. Working tree after step 11 held uncommitted changes (`M` on `MANIFEST.json` and `roster-check.py`, `??` on this report).

### 1. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
?? handoff/TASK-075-r3-report.md
```

### 2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 3. `python -m pytest -p no:cacheprovider -q tests/test_program_roster_sign_in.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_hotfix25a_roster_launcher.py`

```
................................................                         [100%]
48 passed in 16.14s
```

### 4. `python tools/dump-cli.py --check`

```
exit code=0
```

### 5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-22 06:59) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
exit code=0
```

### 6. ASCII decode

```
ascii ok
```

### 7. Bare LF check

```
bare LF 0
```

### 8. `git diff -- bridge/cursor-bridge/VERSION`

```
(no output)
```

### 9. `git diff d8b9739 -- bridge/cursor-bridge/roster-check.py`

```
diff --git a/bridge/cursor-bridge/roster-check.py b/bridge/cursor-bridge/roster-check.py
index b6d91ae..033eafc 100644
--- a/bridge/cursor-bridge/roster-check.py
+++ b/bridge/cursor-bridge/roster-check.py
@@ -22,15 +22,15 @@ Pool is inferred from the id per Cursor's docs: Grok (any effort/host prefix) an
 the "Cursor Models" pool (native); every third-party model is "Other Models".
 A profile is skipped when other_pool is "exhausted" and any of its models is in the other
 pool. Unless --no-probe, the builder and Review B of a candidate profile are each sent a
-  one-word request through `cursor-agent -p -f --model <id>`; a refusal, empty reply,
+one-word request through `cursor-agent -p -f --model <id>`; a refusal, empty reply,
 usage-limit message or timeout marks the profile unusable (this catches hard failures only,
-never a nearly-empty quota); any other reply counts as answered, off-script. When the tool
-itself is signed out, its own sign-in line ends the run (exit 5, SIGN-IN) and counts no failure.
-The chosen
+never a nearly-empty quota); any other reply counts as answered, off-script. The chosen
 profile's three families must be distinct. The result is written to
 docs/ROSTER.resolved.json for the delegate and Review B commands to read, and only when it
 changes (the time of every check goes to the state file as last_resolved), so a check
 before a snapshot leaves the tree clean.
+When the Cursor tool itself is signed out, its own sign-in line (the whole of standard output,
+or any whole line of standard error) ends the run with SIGN-IN, exit 5, and counts no failure.
 The family rule governs Review B only (2026.10.25a): Review B is never of the family of the
 last builder run of the branch under review (none for a branch with no builder run). When
 the chosen profile's Review B is of that family - the change in flight was built under
@@ -90,7 +90,18 @@ PROBE_PROMPT = "Reply with exactly the single word OK and nothing else."
 PROBE_TIMEOUT = 150
 SIGN_IN_PREFIX = "Error: Authentication required. Please run 'agent login' first"
 SIGN_IN_LINE = "SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login"
-PROBE_SIGN_IN = object()
+
+
+class _ProbeSignInSentinel(object):
+    """Distinct falsy value probe returns when the Cursor tool is signed out (not ok, not False)."""
+
+    __slots__ = ()
+
+    def __bool__(self):
+        return False
+
+
+PROBE_SIGN_IN = _ProbeSignInSentinel()  # falsy sentinel; main() tests ``ok is PROBE_SIGN_IN``
 
 FAMILY_PREFIXES = [
     ("claude", "anthropic"), ("anthropic", "anthropic"),
@@ -179,21 +190,51 @@ def cursor_agent_cmd():
     return bridge_env.cursor_agent_launcher()
 
 
-def tool_sign_in_line_present(text):
-    """True when a line in text is the Cursor tool's own sign-in line (prefix at line start only)."""
+_TRIM_EDGES = " \t\r\n"
+
+
+def _lf_lines(text):
     if not text:
-        return False
-    for line in text.splitlines():
-        if line.strip().startswith(SIGN_IN_PREFIX):
+        return []
+    return text.split(NL)
+
+
+def _trim_line_edges(line):
+    return line.strip(_TRIM_EDGES)
+
+
+def _line_starts_with_sign_in(line):
+    return _trim_line_edges(line).startswith(SIGN_IN_PREFIX)
+
+
+def tool_sign_in_on_stderr(text):
+    """True when any whole line of standard error is the tool's sign-in line."""
+    for line in _lf_lines(text):
+        if _line_starts_with_sign_in(line):
             return True
     return False
 
 
+def tool_sign_in_on_stdout(text):
+    """True when standard output is only the tool's sign-in line (one non-empty trimmed line)."""
+    non_empty = []
+    for line in _lf_lines(text):
+        trimmed = _trim_line_edges(line)
+        if trimmed:
+            non_empty.append(trimmed)
+    return len(non_empty) == 1 and non_empty[0].startswith(SIGN_IN_PREFIX)
+
+
+def _ascii_line(text):
+    return (text or "").encode("ascii", errors="backslashreplace").decode("ascii")
+
+
 def probe(model_id):
     """Return (ok, detail). ok when the model replied 'OK' (case-insensitive) within the timeout, or
     replied something else that is not a usage-limit message: answered off-script, so the model is
     there (2026.10.25a: a sentence instead of the word printed FAIL, which sends the owner to buy
-    usage). A refusal (non-zero exit), an empty reply, a time-out or a usage-limit message is not ok."""
+    usage). A refusal (non-zero exit), an empty reply, a time-out or a usage-limit message is not ok.
+    When the Cursor tool is signed out, ok is PROBE_SIGN_IN (falsy, tested by identity in main())."""
     launcher = cursor_agent_cmd()
     if launcher is None:
         return False, "cursor-agent not found (PATH or %LOCALAPPDATA%/cursor-agent)"
@@ -203,13 +244,13 @@ def probe(model_id):
         return False, str(e)
     try:
         p = subprocess.run(launcher + ["-p", "-f", "--model", model_id, PROBE_PROMPT],
-                           capture_output=True, text=True, timeout=PROBE_TIMEOUT, creationflags=NO_WINDOW,
-                           env=env)
+                           capture_output=True, text=True, encoding="utf-8", errors="replace",
+                           timeout=PROBE_TIMEOUT, creationflags=NO_WINDOW, env=env)
     except subprocess.TimeoutExpired:
         return False, "timeout after %ds" % PROBE_TIMEOUT
     except FileNotFoundError:
         return False, "cursor-agent launcher not executable: %s" % launcher[0]
-    if tool_sign_in_line_present(p.stdout or "") or tool_sign_in_line_present(p.stderr or ""):
+    if tool_sign_in_on_stdout(p.stdout or "") or tool_sign_in_on_stderr(p.stderr or ""):
         return PROBE_SIGN_IN, ""
     out = (p.stdout or "").strip()
     if p.returncode == 0 and out.strip().strip(".").upper() == "OK":
@@ -217,9 +258,9 @@ def probe(model_id):
     if (p.returncode == 0 and out and classify_failure(out + " " + (p.stderr or ""))[0] == "OTHER"
             and not re.search(r"(?i)\b(error|exception|failed|failure|traceback|unavailable|not available|denied|unauthori[sz]ed|forbidden"
                               r"|invalid|not found|unknown model|cannot use|not supported)\b", out)):
-        return True, "answered off-script: %r" % out.replace(NL, " ")[:80]
+        return True, "answered off-script: %a" % out.replace(NL, " ")[:80]
     err =(p.stderr or "").strip().replace("\n", " ")[:200]
-    return False, "exit %d; stdout=%r; stderr=%r" % (p.returncode, out[:80], err)
+    return False, "exit %d; stdout=%a; stderr=%a" % (p.returncode, out[:80], err)
 
 
 def now_utc():
@@ -389,13 +430,14 @@ def expire_unavailable(roster):
     return dropped
 
 
-def record_failure(path, roster, model, text):
+def record_failure(path, roster, model, stderr_text="", stdout_text=""):
     """Mark the model's pool exhausted on a usage-limit message or a second consecutive
     failure within FAILURE_WINDOW_HOURS; a connection error is transient and never counted;
     otherwise count it. Writes the roster. Returns the exit code (2, 3, 4 or 5)."""
-    if tool_sign_in_line_present(text):
+    if tool_sign_in_on_stderr(stderr_text) or tool_sign_in_on_stdout(stdout_text):
         print(SIGN_IN_LINE)
         return 5
+    text = stderr_text + stdout_text
     if model not in roster_models(roster):
         print("CANNOT RECORD: %r is not a model in this roster (%s)" % (model, ", ".join(sorted(roster_models(roster)))))
         print("               the argument after --record-failure must be the model id of the failed call; nothing was changed")
@@ -404,6 +446,7 @@ def record_failure(path, roster, model, text):
     now = now_utc()
     when = stamp(now)
     excerpt = (text or "").strip().replace(NL, " ")[:300]
+    excerpt_out = _ascii_line(excerpt)
     if kind == "CONNECTION":
         conn = roster.setdefault("connection_failures", {})
         prev = conn.get(model)
@@ -417,10 +460,10 @@ def record_failure(path, roster, model, text):
         if count > CONNECTION_RETRIES:
             print("ESCALATE   %s: connection failure or time-out %d times in %d hours (%s)." % (model, count, FAILURE_WINDOW_HOURS, pat))
             print("           Not a model problem, so no switch: stop the step, write it on the Awaiting user on: line, and tell the owner.")
-            print("           excerpt: %s" % excerpt)
+            print("           excerpt: %s" % excerpt_out)
             return 5
         print("TRANSIENT  %s: connection error or time-out (%s), %d of %d - retry the same step once." % (model, pat, count, CONNECTION_RETRIES))
-        print("           excerpt: %s" % excerpt)
+        print("           excerpt: %s" % excerpt_out)
         return 4
     failures = roster.setdefault("failures", {})
     prev = failures.get(model)
@@ -450,7 +493,7 @@ def record_failure(path, roster, model, text):
         code = 3
     else:
         print("TRANSIENT  %s: first failure in %d hours, not a usage-limit message - retry the same step once." % (model, FAILURE_WINDOW_HOURS))
-        print("           excerpt: %s" % excerpt)
+        print("           excerpt: %s" % excerpt_out)
         code = 4
     save_state(path, roster)
     return code
@@ -486,14 +529,19 @@ def main():
         return 0
     if "--record-failure" in argv:
         model = argv[argv.index("--record-failure") + 1]
-        text = ""
-        for flag in ("--stderr-file", "--stdout-file"):
+        stderr_text = ""
+        stdout_text = ""
+        for flag, slot in (("--stderr-file", "stderr"), ("--stdout-file", "stdout")):
             if flag in argv and argv.index(flag) + 1 < len(argv):
                 try:
-                    text += open(argv[argv.index(flag) + 1], encoding="utf-8", errors="replace").read() + "\n"
+                    chunk = open(argv[argv.index(flag) + 1], encoding="utf-8", errors="replace").read() + "\n"
+                    if slot == "stderr":
+                        stderr_text = chunk
+                    else:
+                        stdout_text = chunk
                 except OSError:
                     pass
-        return record_failure(path, roster, model, text)
+        return record_failure(path, roster, model, stderr_text, stdout_text)
 
     if "--record-success" in argv:
         model = argv[argv.index("--record-success") + 1]
```

### 10. `git diff --stat`

```
 bridge/cursor-bridge/MANIFEST.json   |  4 ++--
 bridge/cursor-bridge/roster-check.py | 19 ++++++-------------
 2 files changed, 8 insertions(+), 15 deletions(-)
```

### 11. `git rev-parse HEAD` and `git status --short`

```
5f4ae4ae71b53439d981386e7915a98dd37afee5
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
?? handoff/TASK-075-r3-report.md
```

`bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- A live signed-out `cursor-agent` prints exactly one non-empty stdout line matching the fixture prefix with no extra banner or model text on stdout — the whole-output rule and tests assume that shape; confirming would need a real signed-out probe capture on the owner's machine.
- No production model ever answers a probe with only the tool's sign-in line as its sole stdout — if one did, the run would exit 5 as tool sign-in rather than probe failure; only fixture and brief text support that boundary.