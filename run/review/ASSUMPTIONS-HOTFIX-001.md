# ASSUMPTIONS — HOTFIX-001

From the branch's commit messages (`git log 64ad75a..HEAD --format=%B`), sections `Assumptions:`:

Assumptions: recorded, not fixed (Review A round 3 notes, all fail
closed or slow): the trim is quadratic on long runs of dots or spaces
(about 5 s near the command-line limit); an allowed name followed by a
space and a separator is refused as unreadable.

Assumptions: the token ends at any Unicode white space, quote or
backquote (Review A: not a bypass); x/.. segments and 8.3 short names
are not normalised (accepted, the text holds them).

Assumptions: the builder listed none; Review A found several (token
ends at ASCII white space only, re.I on the whole owner's line,
Unicode digits), carried into round 2.

Places to look all the same: the normalisation regex of round 2 point 1 and what it can remove; the owner's-line regex's alternatives for the bold colon; how main orders the design refusal before the started line.
