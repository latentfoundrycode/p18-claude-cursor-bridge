# ASSUMPTIONS - CONFIG-B3b

From the branch's commit messages (`git log 42b1c40..HEAD --format=%B`), sections `Assumptions:`:

Assumptions:
- r1: argparse.SUPPRESS serialises as "==SUPPRESS==" -> test (criterion 2 tests against the helper)
- r1: sub-command order follows insertion order -> test (test_cfgb3b_evaluate_reports_subcommands_in_order)
- r1: the CRLF test does not exercise raw CRLF on Windows -> test (Linux CI leg; BUILDER_NOTES records the equivalent mutant)
- r2: none
- r3: normcase folds case and slashes on Windows -> test (CI windows-latest runs the home-case test)
- r3: mutation (q) case-only not re-run -> test (supervisor re-ran it on a copy: three variants, each caught)
- r4: the Git Bash form is caught through the drive-less fragment -> test (test_cfgb3b_r4_the_home_folder_without_its_drive_is_refused; the drive mechanism on the Windows leg only)
- r4: mutation (y) uncaught -> test (test_cfgb3b_r4_a_choice_holding_a_path_inside_a_string_is_refused)

Places to look all the same: any route by which a path of this computer reaches docs/cli-reference.json or docs/CLI_REFERENCE.md (a field the check does not read, a form the canonical comparison misses); the six programs whose parser moved into build_parser() (behaviour unchanged?); the CI step and the pre-commit block (can either pass a stale reference?); whether the generator runs any program code beyond build_parser(); any computer path in a committed file.
