# ASSUMPTIONS - TASK-016

From the branch's commit messages (`git log 0a186da..HEAD --format=%B`), sections `Assumptions:`:

Assumptions:
- mutation (ab) not caught: the baseline path shares the workflow
  folder and is checked earlier -> accepted (redundant by layout; the
  dedicated check stays as the brief's guard; reopens if a file read by
  name moves out of workflow/)

Assumptions:
- mutation (v) not caught by the suite on this tree -> test
  (test_r029_a_link_on_the_way_is_refused_before_realpath)

Assumptions:
- mutation (l) not caught -> test (test_r029_a_reference_through_a_link_out_of_the_bridge_folder_does_not_resolve)
- a non-UTF-8 ls-tree path shown through a latin-1 decode and the
  escaping function -> accepted: the error fails closed (exit 2) and
  only its wording rests on the decode

Assumptions:
- list-item continuation inside a blockquote -> accepted: the core has
  no blockquote (grep), a module adding one is a later increment's
  review
- a heading's closing # characters kept in its text -> accepted: no
  heading of the core has them (grep)
- git ls-tree -z paths decoded as UTF-8 -> accepted: every path of the
  workflow folder is ASCII
- a 120-second timeout on each git command -> accepted: the largest
  git show is the 2,342-line core
- the citation pattern has no false positive on a word ending in
  see/per/under -> test (test_r029_a_word_ending_in_see_per_or_under_is_not_a_citation)

Places to look all the same: every path the program reads or prints (links, junctions, reparse points, device names, escaping); the order and exactness of every output line; the git commands it runs and what happens when each fails; whether each test fails on the defect its docstring names; whether the records claim more than the tests show; any computer path in a committed file.
