# ASSUMPTIONS - TASK-049, Review B round 1

The builder's `Assumptions:` sections, from the branch's commit messages (`git log 4dac0f8..HEAD --format=%B`), each with the supervisor's disposition. Extra places to look, never the review's scope.

## Round 1 (ca9fb5b)

1. A header whose roles swap two column names agrees (TASK-046's `header_agrees`). Disposition: ruled a HARDENING lead in the brief's commit (TASK-046's A1, now live by role location: a deviations header swapping from and to agrees); recorded in HARDENING's TASK-049 section with a convergent mark.
2. With `reflected_through` null in an agreeing header and no `Reflected through:` line, inventory-check skipped the absorption checks rather than failing the missing line. Disposition: rejected by both reviewers (Review A B1, the audit's B1); fixed in round 2 (the same `SHAPE: no 'Reflected through:' line` finding and the absorption check as header-less), pinned by `test_r060_r2_a_null_reflected_through_keeps_the_missing_line_finding`.
3. A bridge_env stub exposing only `read_header` is refused through the existing `status_values` guard. Disposition: superseded in round 2: inventory-check checks every name it uses (`_INVENTORY_BRIDGE_NAMES`) and refuses before reading the inventory (SF-3), pinned by `test_r060_r2_inventory_check_without_bridge_env_refuses_without_a_traceback`.

## Round 2 (cc6f9f8)

None listed. Review A noted three choices the report did not list: an empty requirement text where every declared column is a role's; no refusal of an unusable bridge_env when the inventory is absent; the `(ImportError)` detail when a name is missing. Disposition: HARDENING leads (TASK-049's section).
