# ASSUMPTIONS - HOTFIX-001-main

From the branch's commit messages (`git log 9a8fc6e..HEAD --format=%B`), sections `Assumptions:`:

Assumptions:
- none new (records only).

Assumptions:
- none new on this branch: no builder ran; the builder's lists of
  HOTFIX-001 r1 to r3 were dispositioned in PR #39 (release/2026.10.11).
- supervisor.md merged by git alone is the hotfix plus main's own 42
  changed lines -> test (diff compared line for line; full suite 1563
  passed, 23 skipped).

Assumptions: the builder listed none; Review A found several (token
ends at ASCII white space only, re.I on the whole owner's line,
Unicode digits), carried into round 2.

Assumptions: the token ends at any Unicode white space, quote or
backquote (Review A: not a bypass); x/.. segments and 8.3 short names
are not normalised (accepted, the text holds them).

Assumptions: recorded, not fixed (Review A round 3 notes, all fail
closed or slow): the trim is quadratic on long runs of dots or spaces
(about 5 s near the command-line limit); an allowed name followed by a
space and a separator is refused as unreadable.

Places to look all the same: where git merged supervisor.md by itself; the regenerated MANIFEST.json against the files on the branch; whether a test on main reads a line the hotfix changed.
