# Long-running process

## Add at configuration.items

A part that keeps a process running between uses (a server, a watcher, a scheduler) has, before its first increment, a written **start, stop and health** procedure: the one command that starts it, the one that stops it and everything it started, and the one that reports whether it is healthy; each command is recorded in `docs/INVENTORY.md` (Resources: the process, its port or socket, its data, its log) and, for a project with a command-line surface, in its command reference, in the increment that builds it. Every run of the process the loop starts (a test, a demonstration, a check) meets founding rule N1's eight conditions, a run a test starts and stops being part of that test, so that no gate depends on a process it did not start; the conditions stay in the core (`supervisor.md`, "Founding rules", N1; Restructuring Plan §8.1): this addition is how a part that runs one keeps to them, never an exception to them.

## Add at delegation-loop.brief-constraints

A run leaves nothing running: a test starts an instance of its own, on a port and data of its own, never the instance the owner runs, and the brief says how a test starts that instance and how it stops it (the procedure's own start and stop commands given the test's port and data, or a fixture that calls them), and that every process the run starts is stopped before the run ends, its children included, a test failure no exception.

## Add at delegation-loop.test-checks

Nothing the run started is left running: after the change's tests and the suite, the supervisor checks that no process started during them, and no port or socket such a process holds, outlives them; one that does is a correctness-class block (step 7), stopped by itself and its children, never by the procedure's stop command, which would stop the instance the owner runs too, and recorded with the test that left it. A process the owner started is left as it is.
