# TASK-075 round 2 report

Commit reference for verification outputs: `d8b9739920789c47f26f1286fd95bfb310acfb49` (unchanged HEAD; working tree had uncommitted changes as listed in step 12).

## Files changed or created

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/TASK-075-r2-report.md`

## Summary

Round 2 repaired TASK-075 sign-in handling in `roster-check.py`: the module docstring was restored and extended per R1; sign-in detection now uses stream-specific rules with LF-only splitting (R2–R3); the probe returns a falsy `PROBE_SIGN_IN` sentinel (R4), decodes child output as UTF-8 (R5), and prints reply details in ASCII via `%a` and `_ascii_line` (R6); `--record-failure` judges each file by its stream before joining text for classification (R2/R7). Manifest and CLI reference were regenerated (R8). All 45 acceptance tests in the four named files pass.

## Requirements R1–R8

- **R1:** Docstring lines 23–33 match pre-round-1 text; lines 34–35 add the sign-in sentence; line 65 keeps exit-5 SIGN-IN wording (`python tools/dump-cli.py` run).
- **R2:** `tool_sign_in_on_stdout` (lines 218–221) requires a single non-empty trimmed LF line with the prefix; `tool_sign_in_on_stderr` (lines 210–215) matches any trimmed line; `probe` (259–260) and `record_failure` (444–447) use those; `main` (539–552) reads `--stderr-file` and `--stdout-file` into separate strings then passes both to `record_failure`, which joins `stderr_text + stdout_text` for classification when not signed out.
- **R3:** `_lf_lines` splits on `NL` only (196–199); `_trim_line_edges` uses `strip(_TRIM_EDGES)` with space, tab, CR, LF (202–203); `_line_starts_with_sign_in` (206–207) drives both stream helpers.
- **R4:** `_ProbeSignInSentinel` with `__bool__` returning `False` (95–101); `PROBE_SIGN_IN = _ProbeSignInSentinel()` (104); `probe` docstring (243) and return (259–260); `main` tests `ok is PROBE_SIGN_IN` (631–634) before `if not ok`.
- **R5:** `subprocess.run` in `probe` (252–254) sets `encoding="utf-8", errors="replace"`.
- **R6:** `probe` detail strings use `%a` (266–270); `record_failure` prints `excerpt_out` from `_ascii_line` (456, 470, 473, 503); state-file excerpts unchanged (479, 483).
- **R7:** Sign-in before model check in `record_failure`; file reads unchanged in `main`; constants and exit 5 text unchanged; `_stdout_for_probe_errors` (228–235) keeps multi-line model replies containing a quoted sign-in line from failing the error-word probe guard.
- **R8:** CRLF ASCII `roster-check.py`; `make-manifest` and `dump-cli --check` exit 0; `VERSION` diff empty.

## Mutation self-check

### N1 — the stdout whole-output rule dropped: stdout is judged like stderr

Before:

```python
def tool_sign_in_on_stdout(text):
    """True when standard output is only the tool's sign-in line (one non-empty trimmed line)."""
    non_empty = [_trim_line_edges(line) for line in _lf_lines(text) if _trim_line_edges(line)]
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

```text
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_answered_as_today
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_stdout_file_with_the_line_after_other_lines_is_counted_as_today
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_stdout_file_quoting_the_line_beside_a_model_stderr_is_counted_as_today
3 failed, 42 passed in 14.35s
```

Caught: `test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_answered_as_today`

### N2 — the split goes back to `str.splitlines()` (and the trim to bare `strip()`)

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

```text
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[vt]
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[ff]
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[fs]
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[nel]
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[ls]
5 failed, 40 passed in 14.49s
```

Caught: `test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line[vt]`

### N3 — the probe's UTF-8 decoding removed

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

```text
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_beyond_ascii_is_read_as_utf8
1 failed, 44 passed in 14.81s
```

Caught: `test_r095_r2_probe_a_reply_beyond_ascii_is_read_as_utf8`

### N4 — the ASCII printing removed: `%r` again in the probe's detail strings, and the excerpt printed as it is

Before:

```python
        return True, "answered off-script: %a" % out.replace(NL, " ")[:80]
    err =(p.stderr or "").strip().replace("\n", " ")[:200]
    return False, "exit %d; stdout=%a; stderr=%a" % (p.returncode, out[:80], err)
```

```python
    excerpt_out = _ascii_line(excerpt)
```

```python
            print("           excerpt: %s" % excerpt_out)
```

```python
        print("           excerpt: %s" % excerpt_out)
```

```python
        print("           excerpt: %s" % excerpt_out)
```

After:

```python
        return True, "answered off-script: %r" % out.replace(NL, " ")[:80]
    err =(p.stderr or "").strip().replace("\n", " ")[:200]
    return False, "exit %d; stdout=%r; stderr=%r" % (p.returncode, out[:80], err)
```

```python

```

```python
            print("           excerpt: %s" % excerpt)
```

```python
        print("           excerpt: %s" % excerpt)
```

```python
        print("           excerpt: %s" % excerpt)
```

```text
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_beyond_ascii_is_read_as_utf8
FAILED tests/test_program_roster_sign_in.py::test_r095_r2_probe_a_reply_beyond_the_consoles_code_page_is_answered_and_printed_in_ascii
2 failed, 43 passed, 1 warning in 14.64s
```

Caught: `test_r095_r2_probe_a_reply_beyond_the_consoles_code_page_is_answered_and_printed_in_ascii`

### N5 — the signed-out constant made truthy again (`object()`)

Before:

```python
class _ProbeSignInSentinel(object):
    """Distinct falsy value probe returns when the Cursor tool is signed out (not ok, not False)."""

    __slots__ = ()

    def __bool__(self):
        return False


PROBE_SIGN_IN = _ProbeSignInSentinel()  # falsy sentinel; main() tests ``ok is PROBE_SIGN_IN``
```

After:

```python
PROBE_SIGN_IN = object()
```

```text
45 passed in 14.75s
```

not caught — no test calls `probe` directly with the sign-in line; identity check in `main()` still catches signed-out runs; a direct `probe` caller testing `if not ok` would mis-classify.

## Verification commands

### 1. `git status --short`

```text
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

### 2. `python tools/make-manifest.py`

```text
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 3. `python tools/dump-cli.py`

```text

```

### 4. `python -m pytest -p no:cacheprovider -q tests/test_program_roster_sign_in.py tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_hotfix25a_roster_launcher.py`

```text
.............................................                            [100%]
45 passed in 14.42s
```

### 5. `python tools/dump-cli.py --check`

```text
exit 0
```

### 6. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```text
bridge-check: version 2026.11.12a (2026-11-22 06:45) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
exit 0
```

### 7. `python -c "open('bridge/cursor-bridge/roster-check.py','rb').read().decode('ascii'); print('ascii ok')"`

```text
ascii ok
```

### 8. `python -c "d=open('bridge/cursor-bridge/roster-check.py','rb').read(); print('bare LF', d.count(b'\n')-d.count(b'\r\n'))"`

```text
bare LF 0
```

### 9. `git diff -- bridge/cursor-bridge/VERSION`

```text

```

### 10. `git diff 6a1434d -- bridge/cursor-bridge/roster-check.py`

```diff
diff --git a/bridge/cursor-bridge/roster-check.py b/bridge/cursor-bridge/roster-check.py
index d426aef..8e344fd 100644
--- a/bridge/cursor-bridge/roster-check.py
+++ b/bridge/cursor-bridge/roster-check.py
@@ -29,6 +29,8 @@ profile's three families must be distinct. The result is written to
 docs/ROSTER.resolved.json for the delegate and Review B commands to read, and only when it
 changes (the time of every check goes to the state file as last_resolved), so a check
 before a snapshot leaves the tree clean.
+When the Cursor tool itself is signed out, its own sign-in line (the whole of standard output,
+or any whole line of standard error) ends the run with SIGN-IN, exit 5, and counts no failure.
 The family rule governs Review B only (2026.10.25a): Review B is never of the family of the
 last builder run of the branch under review (none for a branch with no builder run). When
 the chosen profile's Review B is of that family - the change in flight was built under
@@ -60,7 +62,7 @@ unavailable marks and failure counts, and says so. Timestamps are UTC. ROSTER_NO
 overrides "now" for tests.
 Exit 0 = resolved; 1 = no usable profile, a family collision, or a command mismatch;
 2 = cannot read or a wrong model argument; 3 = pool/model marked exhausted, re-resolve;
-4 = transient, retry once; 5 = repeated connection failures or time-outs, tell the owner.
+4 = transient, retry once; 5 = repeated connection failures or time-outs, or the Cursor tool signed out (SIGN-IN), tell the owner.
 ASCII-only on purpose.
 """
 import datetime
@@ -86,6 +88,20 @@ STATE_KEYS = ("other_pool", "exhausted_at", "exhausted_reason", "auto_exhausted_
 NL = chr(10)
 PROBE_PROMPT = "Reply with exactly the single word OK and nothing else."
 PROBE_TIMEOUT = 150
+SIGN_IN_PREFIX = "Error: Authentication required. Please run 'agent login' first"
+SIGN_IN_LINE = "SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login"
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
@@ -174,11 +190,57 @@ def cursor_agent_cmd():
     return bridge_env.cursor_agent_launcher()
 
 
+_TRIM_EDGES = " \t\r\n"
+
+
+def _lf_lines(text):
+    if not text:
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
+            return True
+    return False
+
+
+def tool_sign_in_on_stdout(text):
+    """True when standard output is only the tool's sign-in line (one non-empty trimmed line)."""
+    non_empty = [_trim_line_edges(line) for line in _lf_lines(text) if _trim_line_edges(line)]
+    return len(non_empty) == 1 and non_empty[0].startswith(SIGN_IN_PREFIX)
+
+
+def _ascii_line(text):
+    return (text or "").encode("ascii", errors="backslashreplace").decode("ascii")
+
+
+def _stdout_for_probe_errors(out):
+    """Lines of a model stdout reply, without lines that are the tool's sign-in line (quoted on their own)."""
+    parts = []
+    for line in _lf_lines(out):
+        trimmed = _trim_line_edges(line)
+        if trimmed and not trimmed.startswith(SIGN_IN_PREFIX):
+            parts.append(trimmed)
+    return NL.join(parts)
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
@@ -188,21 +250,24 @@ def probe(model_id):
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
+    if tool_sign_in_on_stdout(p.stdout or "") or tool_sign_in_on_stderr(p.stderr or ""):
+        return PROBE_SIGN_IN, ""
     out = (p.stdout or "").strip()
     if p.returncode == 0 and out.strip().strip(".").upper() == "OK":
         return True, "answered"
+    err_probe = _stdout_for_probe_errors(out)
     if (p.returncode == 0 and out and classify_failure(out + " " + (p.stderr or ""))[0] == "OTHER"
             and not re.search(r"(?i)\b(error|exception|failed|failure|traceback|unavailable|not available|denied|unauthori[sz]ed|forbidden"
-                              r"|invalid|not found|unknown model|cannot use|not supported)\b", out)):
-        return True, "answered off-script: %r" % out.replace(NL, " ")[:80]
+                              r"|invalid|not found|unknown model|cannot use|not supported)\b", err_probe)):
+        return True, "answered off-script: %a" % out.replace(NL, " ")[:80]
     err =(p.stderr or "").strip().replace("\n", " ")[:200]
-    return False, "exit %d; stdout=%r; stderr=%r" % (p.returncode, out[:80], err)
+    return False, "exit %d; stdout=%a; stderr=%a" % (p.returncode, out[:80], err)
 
 
 def now_utc():
@@ -372,10 +437,14 @@ def expire_unavailable(roster):
     return dropped
 
 
-def record_failure(path, roster, model, text):
+def record_failure(path, roster, model, stderr_text="", stdout_text=""):
     """Mark the model's pool exhausted on a usage-limit message or a second consecutive
     failure within FAILURE_WINDOW_HOURS; a connection error is transient and never counted;
-    otherwise count it. Writes the roster. Returns the exit code (2, 3 or 4)."""
+    otherwise count it. Writes the roster. Returns the exit code (2, 3, 4 or 5)."""
+    if tool_sign_in_on_stderr(stderr_text) or tool_sign_in_on_stdout(stdout_text):
+        print(SIGN_IN_LINE)
+        return 5
+    text = stderr_text + stdout_text
     if model not in roster_models(roster):
         print("CANNOT RECORD: %r is not a model in this roster (%s)" % (model, ", ".join(sorted(roster_models(roster)))))
         print("               the argument after --record-failure must be the model id of the failed call; nothing was changed")
@@ -384,6 +453,7 @@ def record_failure(path, roster, model, text):
     now = now_utc()
     when = stamp(now)
     excerpt = (text or "").strip().replace(NL, " ")[:300]
+    excerpt_out = _ascii_line(excerpt)
     if kind == "CONNECTION":
         conn = roster.setdefault("connection_failures", {})
         prev = conn.get(model)
@@ -397,10 +467,10 @@ def record_failure(path, roster, model, text):
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
@@ -430,7 +500,7 @@ def record_failure(path, roster, model, text):
         code = 3
     else:
         print("TRANSIENT  %s: first failure in %d hours, not a usage-limit message - retry the same step once." % (model, FAILURE_WINDOW_HOURS))
-        print("           excerpt: %s" % excerpt)
+        print("           excerpt: %s" % excerpt_out)
         code = 4
     save_state(path, roster)
     return code
@@ -466,14 +536,19 @@ def main():
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
@@ -553,6 +628,10 @@ def main():
             usable = True
             for role, mid in (("builder", b_id), ("review_b", r_id)):
                 ok, detail = probe(mid)
+                if ok is PROBE_SIGN_IN:
+                    print("    probe %-8s %s: tool sign-in required" % (role, mid))
+                    print(SIGN_IN_LINE)
+                    return 5
                 print("    probe %-8s %s: %s" % (role, mid, detail))
                 if not ok:
                     usable = False
```

### 11. `git diff --stat`

```text
 bridge/cursor-bridge/MANIFEST.json   |   4 +-
 bridge/cursor-bridge/roster-check.py | 107 ++++++++++++++++++++++++++---------
 docs/CLI_REFERENCE.md                |   8 +--
 docs/cli-reference.json              |   2 +-
 4 files changed, 88 insertions(+), 33 deletions(-)
```

### 12. `git rev-parse HEAD` and `git status --short`

```text
d8b9739920789c47f26f1286fd95bfb310acfb49
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

## Assumed, not verified

- A signed-out Cursor tool prints nothing else on standard output besides the sign-in line — required for the whole-stdout rule — would be confirmed by a live `cursor-agent` probe capture beyond the single fixture line.
- The tool encodes probe stdout/stderr as UTF-8 — R5 relies on this — would be confirmed by inspecting raw bytes from a real tool run on Windows.
- Launcher stderr may place unrelated lines before the tool's sign-in line — the stderr any-line rule assumes this pattern — would be confirmed from production launcher logs cited in the brief (e.g. `bridge-run` slot lines).