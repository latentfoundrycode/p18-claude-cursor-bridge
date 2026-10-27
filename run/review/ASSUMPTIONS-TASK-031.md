# ASSUMPTIONS - TASK-031

From the `Assumptions:` sections of the branch's commit messages, whole, by commit (extra places to look, never the review's scope).

## 989181d TASK-031: mutation reruns that skip what is unchanged, mutation-run.py

- r1: Requirement 11 cases not automated (killed run, editable installs,
  resolution refusal, checkpoint .env, refusals) -> test: written in rounds 2
  and 3, each killed by the supervisor's driver or a supervisor test
- r1: POSIX behaviour matches Windows for the process-group kill and the
  scratch paths -> test: CI's Ubuntu job runs the whole file
- r1: git archive line endings match the working tree for checkpoint copies
  -> accepted: the checkpoint runs the new tests on the old code, and a
  newline difference cannot make a passing test fail there; export
  attributes recorded in docs/HARDENING.md, TASK-031
- r1: pytest -rA names every collected id when the session ends with exit 0
  or 1 -> test: an expected id absent is an error (M24 killed), and a
  collection error is exit 2, an error
- r2: none -> unknown, not none: round 3's checkpoint defect was missed
  there (docs/HARDENING.md, TASK-031)
- r3: the window probe on Windows only, skipped elsewhere -> accepted:
  console windows exist only on Windows (rule 24); M06 killed on Windows
- r3: the tracked-link test's link kind -> test: a junction on Windows (M13
  killed here), a symbolic link on CI's Ubuntu job
- r3: the checkpoint's added-module behaviour on Linux -> test: CI's Ubuntu
  job runs the supervisor's test
- r3: round 2's `none` -> as above

## 43daf6e TASK-031 r4: the blocking findings of round 3's gate, as delivered

- r4: the outcomes plugin records every outcome under pytest-xdist, -p no:
  and other plugins -> accepted: the bridge's mutants run plain pytest,
  and a missing outcome record is an error, never a kill
- r4: an empty -c stops the upward search, pyproject.toml included -> test:
  test_task031_r4_b8_a_pytest_configuration_above_the_copy_is_not_read (a
  home pytest.ini deselecting every test does not configure the run); a
  parent pyproject.toml alone is not tested -> accepted: pytest's -c names
  the one configuration file and sets the rootdir search aside

## f3f304b TASK-031 r5: the bound's kill cannot hang on a pipe holder outside the tree

- r5: the abandoned reader threads and pipe handles are reclaimed when the
  holder exits or the program ends -> accepted: they are daemon threads of
  a one-shot program, and under the launcher's --kind driver the Job
  object ends the holder with the run (docs/HARDENING.md, TASK-031 round 4)
- r5: the POSIX path matches the Windows one -> test: CI's Ubuntu job runs
  the reproduction test and the builder's test

## e435e0e TASK-031 r6: the blocking findings of rounds 4 and 5's gate

- r6: pytest 9.1.1's configuration order read from its installed
  findpaths.py, and -c on a toml file read as its own search reads it ->
  test: test_task031_r6_b3_* (each name and section case); CI's Ubuntu job
  runs the same pytest from requirements.lock
- r6: the POSIX behaviour of the scratch forms, the .git identity check and
  the alive-after-kill stop -> test: CI's Ubuntu job runs the supervisor's
  and the builder's tests (the Windows-only forms skip there)
- r6: the in-tree grandchild holder ends with taskkill in about 7 s, so its
  test asserts the bound only -> accepted: the outside-tree holder's test
  and the supervisor's item-12 test assert the 30 s hold

## b8de2a7 TASK-031 r7: the blocking findings of round 6's gate

- r7: ConfigParser(interpolation=None) and pytest 9.1.1's iniconfig agree
  on whether a file parses and holds the section for the files projects
  write; where they differ (duplicate sections or keys, keys without =,
  continuations) the program refuses with exit 2, failing closed ->
  accepted: docs/HARDENING.md, TASK-031 round 7
- r7: under addopts = -s the grandchild holder's stdout is run_process's
  pipe -> accepted: the outside-tree holder's test and the supervisor's
  item-12 test assert the 30 s hold; this test's purpose is the end of the
  holder, which the builder's by-hand check with kill_tree a no-op showed
  failing
- r7: the POSIX process-group end of the grandchild holder -> test: CI's
  Ubuntu job runs it

## f148d71 TASK-031 r8: a pytest section header holding a comment is refused

- r8: the iniconfig 2.3.1 source the builder read is what pytest 9.1.1
  imports in CI -> accepted: requirements.lock pins iniconfig 2.3.1, which
  CI installs on both runners
- r8: other header differences (leading whitespace before `[`, a header
  not ending in `]` after the comment cut, `[]`, duplicate sections) ->
  accepted: docs/HARDENING.md, TASK-031 round 8; where both parsers
  recognise a header and disagree on its name, configparser's name holds
  the `]` iniconfig's ends at, so the check refuses it; the others make
  iniconfig raise, so the gate's own pytest cannot run either, or
  configparser raise, a refusal
- r8: a non-pytest section name holding `#`, `;` or `]` refuses a file
  pytest would read -> accepted: fails closed, exit 2, with the file named

## a2f7ce6 TASK-031 r9: the pytest configuration read with pytest's own iniconfig

- r9: iniconfig 2.3.0 (installed here) and 2.3.1 (locked, CI) make the
  same decisions -> test: CI installs 2.3.1 from requirements.lock and
  runs the round 7 to 9 configuration tests on Windows and Ubuntu; the
  program reads with whatever iniconfig the gate's pytest uses, so the
  two can no longer differ in one environment
- r9: iniconfig opens files as UTF-8 on Ubuntu too -> test: CI's Ubuntu
  job runs the does-not-decode tests
- r9: a setup.cfg holding only a plain [pytest] section is passed over
  where pytest stops with an error -> accepted: docs/HARDENING.md,
  TASK-031 round 6 (the gate's own pytest cannot run on that file)

## a7dc87c TASK-031 r10: a project's own top-level iniconfig is refused

- r10: the folder of the candidate file is always the copy root ->
  accepted: copy_pytest_config_file, the function's only caller, joins
  each candidate name under copy_root
- r10: `iniconfig` and `iniconfig.*` cover every top-level name Python
  3.12 imports as iniconfig (module, package, bytecode, extension
  modules) -> accepted: fails closed; names it does not import, such as
  iniconfig.txt, are refused too
- r10: a differently cased IniConfig.py on Windows may not be imported as
  iniconfig -> accepted: refused anyway, failing closed, as the brief asks
- r10: other routes by which a project changes what the gate's pytest
  imports (.pth files, conftest.py, sitecustomize, -p) -> accepted:
  docs/HARDENING.md, TASK-031 round 10; a project's conftest.py already
  runs its own code inside pytest

## 1d52cfd TASK-031 r11: a project module shadowing an installed one is refused

- r11: find_spec of a bare top-level name runs no project code, and the
  program's sys.path holds neither the copy root nor the Workspace ->
  accepted, corrected: an empty PYTHONPATH entry puts the working folder
  on it; the origin exclusion above makes that harmless
- r11: the suffix and __init__ rule covers every entry Python 3.12's path
  finder imports -> accepted: fails closed
- r11: __main__ is not in sys.stdlib_module_names -> accepted: the
  builder checked it on Python 3.12.10
- r11: a namespace spec is never what pytest imports in place of the
  project's regular package -> accepted: nothing is imported from one
- r11: treating every folder as a package (the brief's mutant 3) fails
  no test -> accepted: it only refuses more, never a false kill
- r11: other routes (.pth, conftest.py, sitecustomize, -p) -> accepted:
  docs/HARDENING.md, TASK-031 round 10

## 8381aba TASK-031 r12: the shadow check narrowed to pytest's configuration modules

- r12: the seven names are every top-level module pytest 9.1.1 imports
  to find and read its configuration -> accepted: findpaths.py imports
  iniconfig, tomllib (tomli before 3.11) and _pytest, all listed; pytest,
  pluggy and py are listed failing closed
- r12: shadowing a module outside the list cannot change which
  configuration file the gate's pytest picks -> accepted: the choice is
  made by findpaths.py with the listed modules; a shadowed module the
  program's plugin imports ends the mutant as an error (docs/HARDENING.md,
  TASK-031 round 11's reviews)

