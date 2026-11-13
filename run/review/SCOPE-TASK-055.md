# SCOPE for TASK-055 (Review B, round 1)

TASK-055 is the stripped suite's one failure (R-076), supervisor-authored, tests only, no builder run, no program changed. Branch task-055 from main d211e33 (PR #157's merge, the program release's design and plan). This is the review guard's first round for TASK-055, below the code gate's ceiling: there is no Blocking class line.

Where the increment ends: tests/conftest.py (the launch value of APPDATA kept under a name of the tests' own before the replacement) and tests/test_release_t_strip.py (reads it; R-076's four assumptions of the shell, each reproduced or struck), R-076 built, and the records. TASK-056 to TASK-058 (the rest of stage P1) follow; they are not this diff's defect. No program under bridge/ is in this diff.

Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-055)
Scope: tests/conftest.py; tests/test_release_t_strip.py
Scope notes: tests/conftest.py: the launch environment's `APPDATA` kept under a name of the tests' own before the replacement, nothing else; tests/test_release_t_strip.py: reads that name, and the four assumptions about the shell
Satisfies: R-076
Done when: the failure is reproduced first (the stripped launch of `tests/test_release_t_strip.py` alone, red on the checkpoint, its line quoted); `tests/conftest.py` keeps the value the launcher handed the run under a name of the tests' own before it replaces `APPDATA`, and the strip test reads that value where it claims the launcher's; each of the four further assumptions (the profile's layout, `GIT_CONFIG_COUNT` set, a redirected `HOME`, a key file's secret-like name) is reproduced red by a run with that condition set before its fix, or struck from the increment with the reason where it does not reproduce (root cause first); the file is green stripped and unstripped, and green with each condition set; one stripped run of the whole suite through the launcher is green on the branch (a whole suite the local run alone can make, CI's run being unstripped), its counts quoted in the accept commit; the test names R-076; R-076 reads built in the increment's records commit.

## The supervisor's tests, each with the paragraph it enforces
- tests/test_release_t_strip.py (its module docstring names R-052 and R-076): the main test reads the launch environment through launch_env (APPDATA put back from BRIDGE_TESTS_LAUNCH_APPDATA) and stripped_launch_check; test_r076_conftest_keeps_the_launch_appdata_under_its_own_name; the three conditions a later hand adds find nothing (a shell's GIT_CONFIG triple, Git Bash's helper, a key file's secret-like name); a moved HOME skips with its reason; eight breaks each found; five pins that bridge_env.stripped_env itself withholds each name the check excuses.
- Red on the checkpoint: no --checkpoint mutation run, since the increment changes no program (the checkpoint's programs are this branch's). The stripped launch of the file alone on the checkpoint: 1 failed, 1 passed (APPDATA was conftest's temporary folder). A probe on the checkpoint (a test under tests/, deleted after): the GIT_CONFIG triple red, the key file's name red, a moved HOME a skip (release S's 22dc72d), a LOCALAPPDATA outside the profile green (22dc72d removed the profile reading), so the last two are struck from the increment with that reason, the profile one without a test (it would repeat the control; the comment above CONDITIONS says so).

## The mutants
run/supervisor/TASK-055-mutants.json (11 mutants: conftest keeps no launch value; launch_env puts no APPDATA back; the strip keeps the GIT_CONFIG triple; the strip keeps secret-like names; the check reads no withheld name, no USERPROFILE, no application folder, no prompt setting; the shell excuse widened to the login; the shell excuse dropped; a moved HOME fails rather than skips). counts: run=11 cached=0 killed=11 survived=0 not applied=0 error=0 expected survive=0

## The threat model
None recorded in docs/INVENTORY.md for the tests; the strip itself (bridge_env.py) is unchanged. The narrowing (the check no longer reads secret-like names in the run, since the launcher adds a key file's names after the strip) is the register's ask; Review A judged it compensated (ASSUMPTIONS).

## Evidence
- Review A: round 1 APPROVE, 0 Blocking, 0 Should fix, 4 Consider (three taken in the test files, the fourth a HARDENING lead), no gate-integrity concern
- the whole suite, stripped, through the launcher, on this branch: 5071 passed, 42 skipped in 1950.07s (0:32:30), exit 0 (the first whole stripped run before Review A's considers: 1 failed, 5071 passed, 42 skipped, the failure tests/test_mutation_run.py:492 under load, passing alone)
- the file stripped "20 passed"; unstripped "19 passed, 1 skipped"; stripped with a key file of the conditions as quoted in the accept commit.

## Expected bookkeeping and records in the diff
docs/REQUIREMENTS.md (R-076 built), docs/HARDENING.md (TASK-055's section; three earlier leads marked resolved), docs/PROJECT_STATUS.md (as at PR #158's merge), and run/review/ (these files).
