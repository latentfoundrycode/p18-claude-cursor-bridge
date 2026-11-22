# Assumptions, TASK-076

No builder ran, so there is no builder's list. The supervisor's assumptions, each with its disposition. Extra places to look, never the review's scope.

- An inline command never spans a line, so reading line by line finds what the whole-text reading found -> settled: the pattern excludes the line feed; the collected ids before and after are identical (Review A worked the equivalence through as well).
- Splitting at the line feed alone, not str.splitlines -> settled: splitlines would break at other separators the old pattern allowed inside a match.
- The mark is a line's, not a command's (the register's wording) -> accepted, with the refusal of a marked line holding more than one command, so the mark cannot hide an instructed command.
- A marked line inside a fenced block would skip that line's backticked spans in the inline reading -> accepted as noted: the fenced reading is unaffected and no text carries the mark.
