# ASSUMPTIONS - BUG-034

From the `Assumptions:` sections of the branch's commit messages, whole, by commit (extra places to look, never the review's scope).

## b318f3e BUG-034 r1: the installer refuses a release of the installed version with other files

- few() lists the differing paths in sorted order -> accepted (cosmetic; the brief asks few(), no order)
- every listed path is a genuine manifest mismatch, one-sided paths included -> test (test_bug034's refusal test; one-sided cases added in round 2)

## 6958e86 BUG-034 r2: --anyway over a same-version release warns that no way back was kept

- the dry run with --anyway prints the WARNING and changes nothing -> test (test_bug034_a_dry_run_with_anyway_warns_and_changes_nothing, the supervisor's)
- the warning line as printed is exactly the brief's shape -> test (the --anyway test pins the line's start, its place after the banner, the count and the file list)

