# Long-running process

## Add at configuration.items

A part that keeps a process running between uses (a server, a watcher, a scheduler) has, before its first increment, a written **start, stop and health** procedure: the one command that starts it, the one that stops it and everything it started, and the one that reports whether it is healthy; each command is recorded in `docs/INVENTORY.md` (Resources: the process, its port or socket, its data, its log) and, for a project with a command-line surface, in its command reference, in the increment that builds it. Every run of the process the loop starts (a test, a demonstration, a check) meets founding rule N1's eight conditions, which stay in the core (`supervisor.md`, "Founding rules", N1; Restructuring Plan §8.1): this addition is how a part that runs one keeps to them, never an exception to them.

## Add at delegation-loop.brief-constraints

A run leaves nothing running: the brief says how a test starts the process and how it stops it (the procedure's own start and stop commands, or a fixture that calls them), and that every process the run starts is stopped before the run ends, its children included, a test failure no exception.

## Add at delegation-loop.test-checks

Nothing is left running: after the change's tests and the suite, the supervisor checks that no process the part runs, and no port or socket it holds, outlives them; one that does is a correctness-class block (step 7), stopped by the procedure's stop command and recorded with the test that left it.
