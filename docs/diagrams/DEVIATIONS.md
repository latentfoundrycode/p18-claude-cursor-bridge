---
record: deviations
header: 1
columns: [Diagram, From, To, "As built", Since, "Resolved by"]
roles:
  diagram: Diagram
  from: From
  to: To
  as_built: "As built"
  since: Since
  resolved_by: "Resolved by"
---
# Known deviations

The as-built diagrams of release T's retrofit (D-001 to D-004, 2026-11-01) against the design as corrected in docs/DESIGN.md, "Change: release T": the first draft of D-002 read the dependency rule as "nothing but bridge_env" and reported five loads of a sibling program by file; the design text was the one behind the code (the loads were built and accepted through the gate as the shared judge), so the rule was corrected and the loads are edges of D-002, not deviations. D-003's draft found one deviation in the review guard, the critique's round 3 a second and Review B of the pull request a third, D-004's draft two more (one in the stripped environment, one in the review guard) and the critique's round 2 a third of D-004's (the launcher's environment to a suite, which the design changes), none bent into its diagram. The first of D-004's, the stripped environment's, was closed by TASK-036 correcting KP-038 to the code (conventions §8's second case: the design corrected to the code); the other five were listed here as design regressions (conventions §8's first case). The launcher's environment to a suite, D-004's third, was closed by TASK-041 (2026-11-02): the loop's and the calibration's suite and driver launch commands carry `--strip`, the driver with its scratch folder named, and D-004's edge is drawn as they run it. The three D-003 rows and D-004's premerge row were closed by TASK-043 (BUG-039), 2026-11-02, whose fix widened from the four named sites to seven on the reviewers' reproductions; none stands.

| Diagram | From | To | As built | Since | Resolved by |
|---|---|---|---|---|---|
