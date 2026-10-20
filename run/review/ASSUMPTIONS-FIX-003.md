# ASSUMPTIONS - FIX-003

From the branch's commit messages (`git log 17f9006..HEAD --format=%B`), sections `Assumptions:`:

Assumptions:
- round 1: "Assumed, not verified: none" -> no list; Review A found no unlisted assumption (the redirect covers print and sys.stderr.write, and a metaclass __name__ property overrides type.__name__: both exercised by test_r005_the_type_name_is_read_where_the_checker_cannot_print) -> test
- round 2: "Assumed, not verified: none" -> no list; the narrowed sentence rests on file_lines having one call site in the hook, confirmed by Review A reading the code -> accepted (a second call site would be a code change the docstring test does not see; reopens if the hook calls file_lines elsewhere)

Places to look all the same: any path by which text the checker controls reaches the hook's output inside the threat model (a partial, mismatched or hand-edited install); any exception that now escapes the hook, which must exit 0 and never block; whether the pointer-line grammar the code reads is the one the docstring states, since TASK-012 writes the first Sub-files: and Variants: lines against it; whether the regenerated stamps (MANIFEST.json, docs/cli-reference.json, docs/CLI_REFERENCE.md) match the sources; whether each test fails on the code before the fix; whether the records claim more than the tests show; any computer path in a committed file.
