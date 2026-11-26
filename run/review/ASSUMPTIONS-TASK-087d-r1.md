# TASK-087d - the branch's assumption lists (from its commit messages)

Extra places to look, never the review's scope.

## TASK-087d: --review-alt acts on the profile the resolve picks (R-107)
- r1: none listed (the report wrote none; Review A found the double probe it relied on) -> test (round 2's tests)
- r2: alt_probe_ok set only where the alternate was probed, kept after a family REBUILD reset -> test (test_task087d_r2_an_alternate_that_did_not_answer_is_refused_on_its_one_answer)
- r2: the request probes once where the evaluation did not -> test (test_task087d_r2_an_alternate_the_evaluation_did_not_probe_is_probed_once_by_the_request, the supervisor's)
- r2: the unknown and unreadable set refusals precede the request's profile reading -> accepted (code order; the refusals' tests run at --no-probe)
- r2: the no-profile-in-use refusal untested -> test (test_task087d_r2_no_profile_in_use_refuses_the_request, the supervisor's)
- r3: the record holds only a real probe's boolean, never a sign-in -> test (the round-3 test; Review A's probe of the request's own sign-in)
- r3: alt_probe_ok kept on the evaluation's dict, unread by the request -> accepted (dead data, HARDENING)
- r3: the request probes once where the record has no entry -> test (the supervisor's round-2 test)
- r3: a recorded failure in a later profile drives the same skip or REBUILD as a live failure -> accepted (one code path, ok_alt from the record)
- r3: static refusals run before the record is read -> accepted (code order; Review A and the audit read it)
