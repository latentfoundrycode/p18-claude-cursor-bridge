# Resolution round: TASK-059, the regression round 6 caused (R1)

This file is the material of a resolution round (Merge-Verification-Policy, Resolution round). Read it whole. You are asked for a reasoned vote, not a review: engage the positions recorded below directly (not merely restate one), choose one candidate, and give the decisive reason. Read the code at the commits named; run what you need to settle a doubt.

## Why a resolution round

TASK-059 (R-078, the launcher's package-runner folder options) is above the review ceiling (round 6 of 3). Rounds 3, 4 and 5 each found a spelling of a folder value that the launcher's check read as one folder and npm as another (a tilde; a trimmed or expanded value; a last component whose trailing dots Windows drops). Round 6 changed the design so that the runner is handed the folder the rule checked, not the word as written: `_package_folder_rewrite` replaces each folder option's value with `os.path.abspath` of it, called in `main` after acceptance and before the cmd.exe check.

Round 6's two readers (Review A, the diff reviewer, and the security auditor) both confirmed that round 6 closes round 5's hole (every trailing-dot value now runs the folder checked, never the planted junction's target) and both block on one behaviour regression that round 6 itself caused, R1. The loop's rule is that a class line never lifts a round for a regression the previous fix caused; that case goes to a resolution round. This is it.

## The question

How should round 7 remove R1 while keeping round 5's hole (B1, trailing dots) closed?

## R1, as both readers reproduced it

- Class: behaviour against the brief (round 6's criterion: requirements 1 to 24 stay met as round 5's code met them; R-078: the launcher accepts the forms a project's suites need). It fails closed: not a security defect.
- (a) A project folder whose path holds a space, with npm at Node's default `C:\Program Files\nodejs\npm.cmd`: `npm --prefix frontend test`, `npm test --prefix=frontend` and `npm -C frontend test` now print `bridge-run: started`, then `'C:\Program' is not recognized as an internal or external command`, exit 1. At round 5 (f62855a) each ran the suite, exit 0; on main `npm test --prefix frontend` ran as written. Mechanism: `resolve` (bridge-run.py:2056-2061) starts a `.cmd` runner as `cmd.exe /d /c <found> <args>`; with the spaced absolute folder there are four quotes on the line, and `cmd.exe /c` without `/s` strips the first and the last.
- (b) A project folder whose path holds `(`, `)`, `&`, `%`, `!` or `^` (for example `Projects (old)` or `R&D`): the same three forms are now refused, exit 125, because `_cmd_exe_refuse_word` (bridge-run.py:492-498, called at 2154-2157) reads the rewritten absolute path and its character list (`CMD_EXE_BAD_CHARS`) holds those characters.
- Neither the acceptance tests nor the builder's case cover a launch folder with a space or a cmd.exe character.

## The material

- Round 6's diff: `git diff 19dd44e 009e42f` (branch `task-059`). Round 5's code: f62855a (19dd44e has the same bridge-run.py).
- `bridge/cursor-bridge/bridge-run.py` at 009e42f:
  - `_package_folder_ok` (lines 290-305): the check of a value: absolute path, a folder, under `launch_roots`, the link walk.
  - `_package_scan_folder_options` (308-348): the scan; the value must not start with `-`, must fullmatch `PACKAGE_FOLDER_VALUE_RE` (ASCII letters, digits, `.`, `_`, `-`, `/`, backslash, a leading drive), and pass `_package_folder_ok`.
  - `_package_folder_rewrite` (351-389): round 6's helper; line 373 computes `abs_path` exactly as the scan's `run_dir` (line 341).
  - `_cmd_exe_refuse_word` (492-498) and `resolve` (2048-2062).
  - `main` (2145-2157): acceptance, then the rewrite, then the cmd.exe check. `subprocess.Popen` (2374, 2389) is given no `cwd`, so the runner's working folder is the launch folder (`folder = os.getcwd()`).
- The acceptance tests: `tests/test_program_launcher_forms.py`, `test_r078_the_runner_is_given_the_folder_the_rule_checked` (it asserts the runner receives the absolute folder) and `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written`.
- `docs/HARDENING.md`, TASK-059: lead 1 (a spaced argument the agent writes, broken by the same cmd.exe quoting) and lead 3 (`\\.\GLOBALROOT\...` passes the character list and makes `relpath` raise `ValueError`); the round-5 entry's words "the relative form unaffected", which round 6 made false.

## The candidates

**A. Hand the runner the checked folder relative to the launch folder.** In `_package_folder_rewrite`, replace the value with `os.path.relpath(abs_path, base)` (`base` the launch folder), keeping round 6's absolute path only where `relpath` cannot be computed (another drive; lead 3's form). The cmd.exe check stays where it is, reading the rewritten words.
- For a folder at or under the launch folder, the handed word is made only of components of a value already held to the character list and normalised by `abspath` (`...` becomes `.`, `a..` becomes `a`), so the project's own location never reaches cmd.exe: (a) and (b) both go for the ordinary layout.
- The runner resolves the word against its working folder, the launch folder, the same base the check used, so the folder that runs is the folder checked, which is round 6's property.
- For a folder in another launch root (a worktree under `Worktrees/`, rule 39), the word climbs with `..` and names the layout's own folders between the common ancestor and the target (`Workspace`, `Worktrees`, the worktree's name); a space or a cmd.exe character there would still fail closed.
- The change stays inside the one helper; the acceptance test's "absolute folder" assertion becomes "a word that, resolved from the launch folder, is the folder checked, holding nothing of the launch folder's own path".

**B. Keep the absolute handoff and fix how `.cmd` runners are started.** Change `resolve` to start a `.cmd` or `.bat` runner as `cmd.exe /d /s /c "<the whole line>"`, so cmd.exe strips only the outer pair of quotes, and decide what the cmd.exe character check does with the launch folder's own characters.
- It cures (a), and with it lead 1 (a spaced argument the agent writes).
- It does not by itself cure (b): inside double quotes cmd.exe still expands `%NAME%` (and `!NAME!` where delayed expansion is on), so `%` and `!` in the launch folder's path cannot be let through by quoting; `(`, `)`, `&` and `^` are inert inside quotes, so the check would have to learn quoting to let those through.
- It changes how every `.cmd` runner starts (npm and npx without folder options, `gh.cmd` for the CI watch), and the whole line must reach `CreateProcess` as one string, since `subprocess.list2cmdline` would escape the inner quotes of a list.

**C. Revert round 6 and refuse the trailing-dot shapes by text.** Hand the runner the word as written (round 5's behaviour) and refuse, before any filesystem call, a folder value with a component that ends in a dot other than `.` and `..` (the shapes Windows path normalisation drops; spaces are already refused by the character list).
- It restores round 5's behaviour for every layout, so R1 goes entirely.
- It closes the spelling round 5 found, not the cause: rounds 3, 4 and 5 were each one more spelling the check read one way and npm another, closed one at a time; any further normalisation difference between Python's `abspath` and Node's path handling would reopen the class.

**D. Draw the line and record R1 in HARDENING.** Not open: R1 is behaviour against the brief, reproduced on an ordinary layout, a blocking class; the rule sends it back, it does not record it.

## The positions already held

- **Review A (round 6, diff reviewer):** REJECT on R1 ("the cause is the brief's design, an absolute value handed through cmd.exe, not the builder's code"). Offered (i) relpath where the folder lies under the launch folder, the absolute form only for a worktree root outside it, noting that its components then come from abspath's normalised output of a value already held to the list, so its last component can no longer end in a dot; or (ii) fix `resolve`'s quoting and decide the launch folder's own characters, noting that it touches code outside one helper.
- **Security auditor (round 6):** FAIL on R1 alone; trust boundaries enforced. Suggested relpath of the checked folder: the runner's working folder is the launch folder, the result is made only of the list's characters already normalised by abspath, and its components are the ones the link walk checked, so the folder that runs is still the folder checked and no project-path character reaches cmd.exe. Named `cmd.exe /d /s /c "<whole line>"` as the alternative, which also closes lead 1.
- **Review B:** holds no position yet; this round asks for its vote.

## What your reply must hold

1. `VOTE: A`, `VOTE: B` or `VOTE: C` on its own line.
2. The decisive reason, in a few sentences, measured against the question: R1 removed for the ordinary layout, round 5's hole kept closed.
3. Your answer to the strongest argument for the candidate you did not choose, naming it.
4. Any way the chosen candidate could hand the runner a word that resolves to a folder other than the one checked, or fail an ordinary layout, with the steps; or `none found` and what you checked.
5. One sentence quoted from this file that your vote turns on.
