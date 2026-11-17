# ASSUMPTIONS: BUG-046, the builders' "Assumed, not verified" lists with the supervisor's dispositions

docs/HARDENING.md, BUG-046, carries the same list. Extra places to look, never the review's scope.

## Round 1 (handoff/BUG-046-report.md)

- `posixpath.normpath` resolves a leading `..` the way GitHub's server would. Disposition: moot (round 3 resolves no dot segment).
- A `..` or `%2e` inside a query or fragment is collapsed with the path. Disposition: the supervisor's finding, a regression, closed by round 2; moot under round 3.

## Round 2 (handoff/BUG-046-r2-report.md)

- No new Semgrep high finding (not run). Disposition: accepted (CI's security floor runs Semgrep on the pull request).
- A non-ASCII escape is decoded to the character its two hex digits name, then lower-cased. Disposition: accepted (this reading refuses more than keeping the word would).

## Round 3 (handoff/BUG-046-r3-report.md)

- No new Semgrep high finding (not run). Disposition: accepted (the same).
