# HOTFIX-001 r2 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`

## Summary

Round 2 updates `design_ceiling` in `bridge-run.py` per Review A: path segments are normalised before matching `run/review/DESIGN-`; design names are parsed with one anchored regex; refusal reasons name the file, `(subject …, round …)`, and whether the name is unreadable, above the numbered ceiling, or past the resolution limit; owner's lines accept Markdown bold/colon variants and ASCII `[0-9]+` rounds only; `docs/RUN_PARAMETERS.md` is read only when the command names a design file; constants cover default round 5 and resolution limits 1 and 2; refusal text is forced to ASCII with `backslashreplace`.

## Tests run

Baseline before round 2 edits (acceptance only, round 1 code in tree): `python -m pytest -q tests/test_bridge_run_design_ceiling.py` → `15 failed, 54 passed in 1.71s`. Failed ids: `test_doubled_separators_and_dot_segments_name_the_same_file` (all six parametrized cases), `test_the_refusal_says_which_refusal_it_is_and_names_the_round` (five cases), `test_under_the_owners_line_the_refusal_names_the_lifted_ceiling`, `test_the_refusal_is_ascii_whatever_the_name_holds`, `test_the_owners_line_is_read_in_its_markdown_forms[colon-inside-bold]`, `test_the_owners_line_takes_a_lower_case_subject_and_ascii_digits_only[arabic-indic-digit]`.

Full-suite baseline from round 1 report (before any HOTFIX-001 edit): `76 failed, 835 passed, 20 skipped, 9 errors in 274.86s`.

Acceptance: `python -m pytest -q tests/test_bridge_run_design_ceiling.py` → `69 passed in 0.76s`.

Launcher: `python -m pytest -q tests/test_bridge_run.py` → `16 passed in 14.50s`.

Final full suite: `python -m pytest -q tests` → `38 failed, 891 passed, 20 skipped, 9 errors in 164.20s`.

## Test result changes (round 2 vs pre-r2 acceptance)

- All 15 previously failing `tests/test_bridge_run_design_ceiling.py` cases (and the 18 supervisor-added cases that already passed on round 1): now pass; total 69/69 on that module.
- Versus round 1 final full suite (`38 failed, 873 passed, 20 skipped, 9 errors`): pass count rose by 18 (new tests only); failure and error counts unchanged; `tests/test_install_check.py::test_the_source_tree_is_checked_against_its_manifest_only` still fails (`STALE cursor-bridge/bridge-run.py`; MANIFEST out of scope).
- `tests/test_rollback.py` failures/errors: unchanged versus round 1 final (25 failed, 9 errors).

## How `main` keeps the started line first on refusal

`design_ceiling` runs after command acceptance and the `--key-file` check but before `run_id`, `sys.stderr.write("bridge-run: started …")`, `write_log`, or `write_pid_file`; a refusal writes only `bridge-run: refused - …` and returns 125, so nothing is logged and no started line is emitted.

## Assumed, not verified

- Token ends at the first character in the class `[^\s\"'`]+` (space, tab, CR, LF, quotes, backquote) · matches round 1 behaviour and `test_trailing_punctuation_is_not_part_of_the_name` · a prompt with another delimiter would show otherwise.
- `DESIGN_LIFT_RE` uses `re.I` on the whole pattern so only the label is case-insensitive in practice; subject must match `[a-z0-9-]+` · `test_the_owners_line_takes_a_lower_case_subject_and_ascii_digits_only[subject-in-capitals]` · a line with a mixed-case subject that still matched `[a-z0-9-]+` would differ.
- Owner `<rounds>` must be ASCII `[0-9]+`; Arabic-Indic digits do not form a well-formed line · `test_the_owners_line_takes_a_lower_case_subject_and_ascii_digits_only[arabic-indic-digit]` · a line with only ASCII digits would lift.
- Path normalisation `re.sub(r"[/\\]+(?:\.[/\\]+)*", "/", text)` is sufficient for doubled separators and `/.` segments but not `..` or 8.3 names · handoff Round 2 point 1 · no test covers `x/..`.
- Non-`.md` tokens that fail the unreadable path still call `design_refuse_name(None, …)`; empty token after strip is skipped without refusal · no dedicated test · a `DESIGN-` with no token would need one.

## Builder notes

2026-10-18: Round 2 did not re-run the full pre-edit suite; full-suite comparison uses the round 1 report baseline and the post-r2 final run.
