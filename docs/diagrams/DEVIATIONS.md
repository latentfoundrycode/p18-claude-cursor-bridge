# Known deviations

The as-built diagrams of release T's retrofit (D-001 to D-003, 2026-11-01) against the design as corrected in docs/DESIGN.md, "Change: release T": the first draft of D-002 read the dependency rule as "nothing but bridge_env" and reported five loads of a sibling program by file; the design text was the one behind the code (the loads were built and accepted through the gate as the shared judge), so the rule was corrected and the loads are edges of D-002, not deviations. D-003's draft found one deviation in the review guard, listed below as a design regression (conventions §8's first case).

| Diagram | From | To | As built | Since | Resolved by |
|---|---|---|---|---|---|
| D-003 | flagged_gate_integrity | reply_arrived | cmd_verify's four early GATE-INTEGRITY returns (the snapshot rewritten; .git/config or a hook changed; the branch held in another worktree; the branch not put back) never call record_flagged_launch, so the launch's exit 0 in REVIEW-<ID>-r<N>.err counts as the round's reply at the next snapshot of round N and the round is spent; the design (INVENTORY, Decisions, TASK-032's settled points) and record_flagged_launch's docstring say a flagged round spends nothing | 2026-11-01 | BUG-039 (release T's addendum) |
