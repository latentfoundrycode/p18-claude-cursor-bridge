# Assumptions - TASK-046, Review B round 1

The builder's `Assumed, not verified` lists with the supervisor's dispositions, taken from the `Assumptions:` sections of the branch's commit messages. Extra places to look, never the review's scope.

## From 3f69c6a TASK-046: the header reader, the schemas, the check and the agreement in bridge_env
- round 1: flow-list items y and n read as typed words -> test
- round 1: a merged None skipping scope and kind in header_agrees -> test (the defect removed)
- round 1: an unreachable branch (M12) -> test, the branch removed
- round 2: the list read `none`; the merge_unit tuple was an omitted assumption (Review A) -> test
- round 3: a merge_unit fallback read as a list compares like the tuple -> test (test_r057_r3_assumed_a_merge_unit_read_as_a_list_compares_like_the_tuple)
- round 3: an empty block right after the opening reads in every CRLF and LF variant -> test (test_r057_r3_assumed_an_empty_block_reads_in_every_line_ending), near-closers refused by test
