# Assumptions, TASK-075

The builders' `Assumed, not verified` lists (handoff/TASK-075-r1-report.md, -r2-report.md, -r3-report.md) and the supervisor's, each with its disposition. Extra places to look, never the review's scope.

## Round 1
- The live tool keeps printing lines that begin exactly with the recorded prefix -> accepted: the fixture is the line as the tool printed it (ISS-020); a change of wording needs a new capture.
- When signed out in `-p -f` mode the tool may print the line on stdout with exit 0 as well as on stderr with a non-zero exit -> accepted: both shapes are tested through the stand-in.
- Error files written by the launcher place the tool's line at the start of a physical line -> accepted: the stderr rule takes any whole line, after launcher lines.

## Round 2
- A signed-out tool prints nothing else on standard output -> accepted, and the safe direction: if it printed more, the reply is judged as before (no answer, by its word Error), never answered (round 3's cases).
- The tool writes its output as UTF-8 -> accepted: errors are replaced, so a wrong guess loses characters, never the reply.
- Launcher stderr may place other lines before the tool's line -> accepted (the guard case with a bridge-run line first).

## Round 3
- A live signed-out tool prints exactly one non-empty stdout line -> as round 2.
- No model ever answers a probe with only the tool's sign-in line -> accepted: such a reply ends the run with SIGN-IN and exit 5, fail-closed (no profile resolves, the owner is told).

## The supervisor's
- A model's words never reach the tool's stderr -> lead 1 in HARDENING: a captured stderr of a real failed builder call would settle it; the effect if wrong is a stop with SIGN-IN, never a usable profile.
- The builder can write its own `.err` -> lead 2 in HARDENING: it could already delete a usage-limit line; the effect is a stop, the owner told.
