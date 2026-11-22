# Assumptions, TASK-074

The builders' `Assumed, not verified` lists (handoff/TASK-074-r1-report.md, -r2-report.md, -r3-report.md) and the supervisor's, each with its disposition. Extra places to look, never the review's scope.

## Round 1
- The builder wrote none. Review A named what the code settles -> accepted: the cp1252 console is handled by the program's `backslashreplace` reconfigure; the mixed-line-ending rule (the last two bytes decide) is a choice, not an assumption.

## Round 2
- Device names other than CON that make `realpath` raise -> settled by the audit: of NUL, COM1, LPT1, CONIN$, CON.txt and others only `\\.\CON\<sub>` raises on Python 3.12.10; the refusal holds for each.
- The quoted refusal on a strict cp1252 console with non-ASCII folders -> accepted (backslashreplace).
- A VERSION with mixed or no final line ending -> accepted: anything not ending CR LF is written LF.

## Round 3
- DEL, U+0085, U+2028 and U+2029 are not escaped -> lead 2 in HARDENING: on a UTF-8 stdout a `--root` holding them splits into extra lines beginning `RESULT:`, the first still `RESULT: REFUSED`, exit 2; the input is the caller's own.
- POSIX link behaviour is exercised only on CI's Ubuntu run -> accepted: the two link cases run there (a symbolic link in place of the junction).
- Mutant M3 (files read under the root as spelled) uncaught by the round's cases -> settled: the supervisor's added case kills it (11 of 11 killed).

## The supervisor's
- Each acceptance case stamps its copy of bridge/ as it stands -> accepted: the cases judge the program's logic; the repository's own stamp is CI's `bridge-check.py --root bridge --sources --quiet` step, which still runs on the real tree.
- An installed copy whose `cursor-bridge` folder is a link into a source tree checks that tree -> accepted (round 3's case): the program and its manifest are that tree's own files.
