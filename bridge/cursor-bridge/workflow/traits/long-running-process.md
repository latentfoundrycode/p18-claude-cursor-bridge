# Long-running process

## Add at configuration.items

A part that keeps a process running between uses (a server, a watcher, a scheduler) has, before its first increment, a written **start, stop and health** procedure: the one command that starts it, the one that stops it and everything it started, and the one that reports whether it is healthy, the start and stop commands taking the port and the data of the instance they start and stop, so that a test's instance runs and stops beside the instance the owner runs; each command is recorded in `docs/INVENTORY.md` (Resources: the process, its port or socket, its data, its log) and, for a project with a command-line surface, in its command reference, in the increment that builds it. Every run of the process the loop starts (a test, a demonstration, a check) meets founding rule N1's eight conditions, a run a test starts and stops being part of that test, so that no gate depends on a process it did not start; the conditions stay in the core (`supervisor.md`, "Founding rules", N1; Restructuring Plan §8.1): this addition is how a part that runs one keeps to them, never an exception to them.

## Add at delegation-loop.brief-constraints

A run leaves nothing running: a test starts an instance of its own, on a port and data of its own, never the instance the owner runs, and the brief says how a test starts that instance and how it stops it (the procedure's own start and stop commands given the test's port and data, or a fixture that calls them), and that every process the run starts is stopped before the run ends, its children included, a test failure no exception.

## Add at delegation-loop.test-checks

Nothing the run started is left running: after the change's tests and the suite, the supervisor checks that no process the tests started (one descended from the test run, or one on a test instance's port or data), and no port or socket such a process holds, outlives them; one that does is a correctness-class block (step 7), stopped by its process ID together with its children, or by the procedure's stop command given that instance's port and data, never by a command that reaches the instance the owner runs, and recorded with the test that left it. A process the owner started, or another session's, is left as it is.
