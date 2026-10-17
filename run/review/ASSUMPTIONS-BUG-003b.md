# ASSUMPTIONS-BUG-003b

From the branch's commit messages (`git log origin/main..HEAD --format=%B`):

- (builder, BUG-003 r1) none listed. The reviewers hunt unaided.
- (supervisor) The exact-findings tables were taken from the program's output on the checkpoint and read against each fixture by hand; a list that recorded a wrong finding as expected would pin a defect. Review A's three fixture parts in round 2 ran every case and named each output, which is what the lists hold.
- (round 2) no builder ran; nothing new assumed.
