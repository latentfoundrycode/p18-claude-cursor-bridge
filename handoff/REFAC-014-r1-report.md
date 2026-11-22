# REFAC-014 round 1 report

## Files changed

- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/in-flight.py
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/evaluate-reports.py
- bridge/cursor-bridge/MANIFEST.json

## Summary

REFAC-014 consolidated the seven-string reviewer kind tuple and the byte-identical read-only git environment builder into `bridge/cursor-bridge/bridge_env.py` as `REVIEWERS` (immediately after `ROUND_CAUSES`) and `git_read_env()`, removed the duplicate definitions from `in-flight.py`, `pace-report.py`, and `evaluate-reports.py`, pointed the three reviewer checks and three git subprocess calls at `bridge_env.REVIEWERS` and `bridge_env.git_read_env()`, and regenerated `MANIFEST.json`; targeted pytest stayed at 341 passed and 1 skipped before and after.

## Start state

```
git status --short
```

```
git rev-parse HEAD
```
```
74a0ad3f3626c25ce58407c563ae9d800c01cb2d
```

Working tree held no uncommitted changes at start.

## Requirement 1 (before edit)

```
git grep -n -w -e REVIEWERS -e _REVIEWERS -- bridge/cursor-bridge/in-flight.py bridge/cursor-bridge/pace-report.py
```
```
bridge/cursor-bridge/in-flight.py:27:REVIEWERS = (
bridge/cursor-bridge/in-flight.py:257:    if reviewer not in REVIEWERS:
bridge/cursor-bridge/pace-report.py:103:_REVIEWERS = (
bridge/cursor-bridge/pace-report.py:617:    if m.group(4) not in _REVIEWERS:
bridge/cursor-bridge/pace-report.py:739:        parts = ["%s %d" % (kind, counts[kind]) for kind in _REVIEWERS if counts.get(kind)]
```

```
git grep -n -A 14 -e "^def _git_env" -- bridge
```
```
bridge/cursor-bridge/evaluate-reports.py:503:def _git_env():
bridge/cursor-bridge/evaluate-reports.py-504-    env = os.environ.copy()
bridge/cursor-bridge/evaluate-reports.py-505-    env["GIT_OPTIONAL_LOCKS"] = "0"
bridge/cursor-bridge/evaluate-reports.py-506-    env["GIT_NO_LAZY_FETCH"] = "1"
bridge/cursor-bridge/evaluate-reports.py-507-    for key in (
bridge/cursor-bridge/evaluate-reports.py-508-        "GIT_DIR",
bridge/cursor-bridge/evaluate-reports.py-509-        "GIT_WORK_TREE",
bridge/cursor-bridge/evaluate-reports.py-510-        "GIT_INDEX_FILE",
bridge/cursor-bridge/evaluate-reports.py-511-        "GIT_OBJECT_DIRECTORY",
bridge/cursor-bridge/evaluate-reports.py-512-        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
bridge/cursor-bridge/evaluate-reports.py-513-        "GIT_COMMON_DIR",
bridge/cursor-bridge/evaluate-reports.py-514-        "GIT_NAMESPACE",
bridge/cursor-bridge/evaluate-reports.py-515-    ):
bridge/cursor-bridge/evaluate-reports.py-516-        env.pop(key, None)
bridge/cursor-bridge/evaluate-reports.py-517-    return env
--
bridge/cursor-bridge/pace-report.py:199:def _git_env():
bridge/cursor-bridge/pace-report.py-200-    env = os.environ.copy()
bridge/cursor-bridge/pace-report.py-201-    env["GIT_OPTIONAL_LOCKS"] = "0"
bridge/cursor-bridge/pace-report.py-202-    env["GIT_NO_LAZY_FETCH"] = "1"
bridge/cursor-bridge/pace-report.py-203-    for key in (
bridge/cursor-bridge/pace-report.py-204-        "GIT_DIR",
bridge/cursor-bridge/pace-report.py-205-        "GIT_WORK_TREE",
bridge/cursor-bridge/pace-report.py-206-        "GIT_INDEX_FILE",
bridge/cursor-bridge/pace-report.py-207-        "GIT_OBJECT_DIRECTORY",
bridge/cursor-bridge/pace-report.py-208-        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
bridge/cursor-bridge/pace-report.py-209-        "GIT_COMMON_DIR",
bridge/cursor-bridge/pace-report.py-210-        "GIT_NAMESPACE",
bridge/cursor-bridge/pace-report.py-211-    ):
bridge/cursor-bridge/pace-report.py-212-        env.pop(key, None)
bridge/cursor-bridge/pace-report.py-213-    return env
```

The two `_git_env` bodies are identical line for line; only the file path and line-number prefix in the grep output differ.

```
git grep -n -w -e _git_env -- bridge
```
```
bridge/cursor-bridge/evaluate-reports.py:503:def _git_env():
bridge/cursor-bridge/evaluate-reports.py:534:            env=_git_env(),
bridge/cursor-bridge/pace-report.py:199:def _git_env():
bridge/cursor-bridge/pace-report.py:243:                env=_git_env(),
bridge/cursor-bridge/pace-report.py:254:                env=_git_env(),
```

```
git grep -n -w -e _git_env -e REVIEWERS -e _REVIEWERS -e git_read_env -- tests
```
```
tests/test_program_in_flight.py:30:REVIEWERS = ("review-a", "review-b", "security-auditor", "design-auditor", "plan-critic", "design-critic-b", "supervisor")
tests/test_program_in_flight.py:143:@pytest.mark.parametrize("reviewer", REVIEWERS)
tests/test_release_t_ceiling.py:23:REVIEWERS = ("diff-reviewer.md", "security-auditor.md", "design-auditor.md")
tests/test_release_t_ceiling.py:90:    for name in REVIEWERS:
```

```
git grep -n -e "^REVIEWERS = " -e "def git_read_env" -e GIT_NO_LAZY_FETCH -- bridge/cursor-bridge/bridge_env.py
```
```
(empty)
```

```
git grep -n -F -e design-critic-b -- bridge
```
```
bridge/cursor-bridge/in-flight.py:33:    "design-critic-b",
bridge/cursor-bridge/pace-report.py:61:security-auditor, design-auditor, plan-critic, design-critic-b and supervisor, printed in that
bridge/cursor-bridge/pace-report.py:109:    "design-critic-b",
```

## Pytest (before edit, HEAD 74a0ad3f3626c25ce58407c563ae9d800c01cb2d)

```
python -m pytest -p no:cacheprovider -q -rs tests/test_program_in_flight.py tests/test_program_pace_rounds.py tests/test_pace_report.py tests/test_program_security_step.py tests/test_task033_supervisor_r3.py tests/test_release_t_ceiling.py tests/test_header_currency.py
```
```
.............................s.......................................... [ 21%]
........................................................................ [ 42%]
........................................................................ [ 63%]
........................................................................ [ 84%]
......................................................                   [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_program_in_flight.py:230: this account cannot create a symbolic link
341 passed, 1 skipped in 89.69s (0:01:29)
```

## Pytest (after edit, HEAD 74a0ad3f3626c25ce58407c563ae9d800c01cb2d, uncommitted changes present)

```
python -m pytest -p no:cacheprovider -q -rs tests/test_program_in_flight.py tests/test_program_pace_rounds.py tests/test_pace_report.py tests/test_program_security_step.py tests/test_task033_supervisor_r3.py tests/test_release_t_ceiling.py tests/test_header_currency.py
```
```
.............................s.......................................... [ 21%]
........................................................................ [ 42%]
........................................................................ [ 63%]
........................................................................ [ 84%]
......................................................                   [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_program_in_flight.py:230: this account cannot create a symbolic link
341 passed, 1 skipped in 89.39s (0:01:29)
```

## Post-edit verification

```
python tools/make-manifest.py
```
```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

```
python tools/dump-cli.py --check
```
```
(empty)
```

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```
```
bridge-check: version 2026.11.12a (2026-11-22 18:36) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
```

```
git diff --numstat -- bridge/cursor-bridge/VERSION
```
```
(empty)
```

```
git diff --numstat -- bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/in-flight.py bridge/cursor-bridge/pace-report.py bridge/cursor-bridge/evaluate-reports.py
```
```
27	0	bridge/cursor-bridge/bridge_env.py
1	18	bridge/cursor-bridge/evaluate-reports.py
1	10	bridge/cursor-bridge/in-flight.py
4	30	bridge/cursor-bridge/pace-report.py
```

```
git grep -n -w -e _git_env -e _REVIEWERS -- bridge
```
```
(empty)
```

```
git grep -n -e "def git_read_env" -- bridge
```
```
bridge/cursor-bridge/bridge_env.py:4449:def git_read_env():
```

```
git grep -n -w -e git_read_env -- bridge
```
```
bridge/cursor-bridge/bridge_env.py:4449:def git_read_env():
bridge/cursor-bridge/evaluate-reports.py:517:            env=bridge_env.git_read_env(),
bridge/cursor-bridge/pace-report.py:217:                env=bridge_env.git_read_env(),
bridge/cursor-bridge/pace-report.py:228:                env=bridge_env.git_read_env(),
```

```
git grep -n -F -e GIT_NO_LAZY_FETCH -- bridge
```
```
bridge/cursor-bridge/bridge_env.py:4452:    env["GIT_NO_LAZY_FETCH"] = "1"
```

```
git grep -n -e "^REVIEWERS = " -- bridge
```
```
bridge/cursor-bridge/bridge_env.py:4428:REVIEWERS = (
bridge/cursor-bridge/diagram-check.py:600:REVIEWERS = re.compile(r"\b(diff-reviewer|design-auditor|security-auditor|plan-critic|refactor-scout|Review [AB])\b")
```

```
git grep -n -F -e design-critic-b -- bridge
```
```
bridge/cursor-bridge/bridge_env.py:4434:    "design-critic-b",
bridge/cursor-bridge/pace-report.py:61:security-auditor, design-auditor, plan-critic, design-critic-b and supervisor, printed in that
```

## End state

```
git status --short
```
```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/evaluate-reports.py
 M bridge/cursor-bridge/in-flight.py
 M bridge/cursor-bridge/pace-report.py
?? handoff/REFAC-014-r1-report.md
```

```
git diff --stat
```
```
 bridge/cursor-bridge/MANIFEST.json       | 10 +++++-----
 bridge/cursor-bridge/bridge_env.py       | 27 +++++++++++++++++++++++++
 bridge/cursor-bridge/evaluate-reports.py | 19 +-----------------
 bridge/cursor-bridge/in-flight.py        | 11 +----------
 bridge/cursor-bridge/pace-report.py      | 34 ++++----------------------------
 5 files changed, 38 insertions(+), 63 deletions(-)
```

```
git rev-parse HEAD
```
```
74a0ad3f3626c25ce58407c563ae9d800c01cb2d
```

Working tree held uncommitted changes at end (five modified bridge files and this new report).

## Behaviour

The shared `REVIEWERS` tuple and `git_read_env()` bodies are byte-for-byte the same as the removed copies, and every call site now reads those definitions from `bridge_env` at the same points in control flow, so pass-line validation, refusals, per-week pass ordering, and git subprocess environments are unchanged.

## Noticed, not changed

`pace-report.py` still lists reviewer kinds in its module docstring while `in-flight.py` does not; `pace-report.py` still adds `("unstated",)` to `ROUND_CAUSES` locally; `git_origin_repo` and `_git` still pass different extra `git -c` flags beyond the shared environment.

## Assumed, not verified

Assumed, not verified: none.