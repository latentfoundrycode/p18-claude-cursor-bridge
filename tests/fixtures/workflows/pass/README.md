A passing workflow folder for workflow-check.py (TASK-006), every case of which passes:

- every layer: a type workflow, its sub-workflow and two traits;
- a replaced module whose point a trait and a sub-workflow still add at, and a sub-workflow that replaces the module its type workflow replaced;
- a sub-workflow overriding its type workflow's setting, two points set in one file, a value in backticks and a value with spaces around it on the line under its heading;
- delivery additions for three kinds, two additions at one point from one file, and an addition at a point that also accepts set;
- change headings inside code fences: one pair at column 0, one pair indented up to three spaces, a backtick run with text after it that does not close its fence, and in the trait file tilde fences, one of them holding a four-backtick line and a shorter tilde line, one whose info string holds a backtick;
- a change heading indented four spaces, which is no heading;
- prose headings: an empty one, a `###` one, ones of punctuation, and ones whose first word starts like a change word (Settings, Setup, Additional, Replacement, Add-ons) or whose second word holds `at` (atop, combat) or is a part of it (a, t).

Nothing outside types/ and traits/ is read.
