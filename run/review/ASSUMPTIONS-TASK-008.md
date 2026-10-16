# ASSUMPTIONS-TASK-008

The builder's `Assumed, not verified` list (handoff/TASK-008-r1-report.md), each with the supervisor's disposition, from the accept commit 825b905. Extra places to look, never the review's scope.

- The Workflows line row sits right after the records-file loop → accepted (no output or verdict depends on a row's position).
- Any exception while loading workflow-check.py is "cannot be loaded (<class>)" → accepted (fails closed, as the brief asks).
- A load-failure reason goes through ASCII backslashreplace but not escape_field, which belongs to the module that failed → accepted (the path is the program's own folder; output stays ASCII).
- An exception after a successful load is "not checked: <workflow-check path>: <class>" → accepted (fails closed; no traceback).
- conformance-check judges an unreadable but existing PROJECT_STATUS.md as empty text, so it reports "missing" rather than "not checked" → accepted (the row is MISSING either way; the wording is recorded in docs/HARDENING.md).
- inventory-check's missing line makes the --status argument ASCII with backslashreplace → accepted (ASCII output; an ASCII path is unchanged).
