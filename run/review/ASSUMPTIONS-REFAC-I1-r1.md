# ASSUMPTIONS-REFAC-I1-r1

The branch's commit messages (git log origin/main..HEAD) carry no Assumptions: section. The three builders' reports each end "Assumed, not verified: none" (handoff/REFAC-015-r1-report.md, REFAC-016-r1-report.md, REFAC-017-r1-report.md). REFAC-015's report notes one point: built_by decoded with the default UTF-8, which is strict, and _parse_run_line decodes strictly; Review A confirmed the two skip the same lines.
