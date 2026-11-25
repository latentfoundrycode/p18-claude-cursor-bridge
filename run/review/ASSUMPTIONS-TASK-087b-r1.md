# ASSUMPTIONS: TASK-087b (Review B, round 1)

The builder's `Assumed, not verified` lists, both rounds (round 1's was empty, one of Review A's smaller points; round 2's three items below), each with the supervisor's disposition. Extra places to look, never your scope.

1. Where the marker is the digest's first line and the first part is empty, the continuation placeholder ("the standing rules and permissions continue in the second part") is acceptable. Disposition: accepted; pinned by `test_r2_a_marker_first_never_says_no_digest_was_found` (K6); contrived, since the committed digest's first part holds the core. Recorded as a lead in HARDENING.
2. Whether Claude Code counts a hook's output cap in characters or bytes. Disposition: settled as far as the increment needs by the probe (an output of 8,800 characters and 9,400 bytes arrived whole) and by the hook's own test, which holds each part under 10,000 characters and 10,000 bytes; `MAX_OUTPUT` counts characters, and a part near 9,800 characters of many three-byte characters is a lead in HARDENING (the parts as they stand are far below).
3. `--part digest-2` with the marker present and no text after it prints the second part's header and its empty-body placeholder. Disposition: accepted as built; the committed digest has the standing rules and permissions after the marker. Recorded as a lead in HARDENING.
