# Assumed, not verified: SLIM-002, round 1

Extra places to look, never the reviewer's scope.

1. That no retired function held, beside its wording or size assertion, an assertion on a program's behaviour, an owner's value or a program-parsed line that no kept test also holds. Each function was read once when the list was made (2026-11-11); the reading was not repeated on this base.
2. That the headings the new text entries name (`docs/REQUIREMENTS.md`) state the label's rule under that heading. `completion-check.py` confirms that the heading exists and that the cited pull request's squash changed the file; it does not read the heading's text for the rule.
3. That the cited pull requests (#119, #120, #121) are the ones that brought each rule into its file, not merely pull requests that changed the file. Found with `git log -S` on a phrase of the rule; not every label's phrase was searched again on this base.
4. That the whole suite passes on this head. It ran once on the prepared change on an earlier base; #152's later rounds changed `bridge/cursor-bridge/bridge-run.py`, `tests/test_release_s_launcher.py` and one row of `docs/INVENTORY.md`, none of which this diff touches. CI's run of the pull request is the proof.
5. That R-032's revised sentence states the two budgets as `tests/test_release_s_budgets.py` holds them (8,000 words per step file; 150,000 words for the rulebook).
6. That removing `assert_survival_list` from `tests/phase_modules.py` leaves no importer (the 21 files ran; the whole suite's collection passed with 5,104 cases).
