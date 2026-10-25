# Host extension

## Set at intake.delivery-kind

host-installation

## Add at design.sections

The host's rules are not the project's: the host decides how its extension points behave and changes them with its updates. So the design gains a section on the host, recording each behaviour of the host's extension points the part relies on (when a hook runs and what it may change, how a setting is read, what a command is allowed to do) as a verified fact: what was checked, how it was checked (a probe run in the host, or the host's own documentation for that version), and the host's version it was checked on. A probe that checks such a fact runs as the tests do, in a host kept apart from the owner's own, and its use of the owner's account or paid usage is put to the owner as the test step's addition says. A behaviour not yet checked is written as an assumption, and the first increment that relies on it checks it before anything is built on it. A fact holds for the version it names: when the host the project is built against reports another version, the facts the part relies on are checked again before the next increment that relies on them, and a fact found changed is a defect like any other, or a question for the owner where it changes what the part can do.

## Add at delegation-loop.test-checks

Beside the tests that run in isolation, each behaviour of the part that depends on the host is tested inside the real host, at the version the design's host section records, with the part installed into a host kept apart from the owner's own (a separate profile, folder or instance, as the host allows), never into the host the owner works in. The behaviour is driven there and its result read from what the host did. A host behaviour no test can reach inside the host is named in the increment's report as untested there, never counted as tested. Where driving the host uses the owner's account, that use is put to the owner once, before any test relies on it, and what it reaches is recorded in `docs/INVENTORY.md` (Decisions); where it draws paid usage, the part is classified with *spends money* too, and each run that draws it is a paid action of that trait's, approved for itself and run by the supervisor, never by the builder or in CI.

## Add at project-end.delivery for host-installation

- **Install into the host**: the owner's host receives the release through an install program the project ships, which the owner runs from a run sheet, since it acts outside the repository. The program copies the release's files into the host's extension folder, merges the part's entries into the host's settings without changing the owner's own entries (where an entry of the part's and one of the owner's name the same thing, it stops and puts the clash to the owner), keeps what it replaces so that the previous release can be put back, and ends by checking that the host loads the installed version, as the host reports it or a probe in the host sees it. The take-back puts the previous release's files and entries back the same way, and is proved once, on a host kept apart from the owner's own, before the first release is installed. The User Manual's first chapter says how to install, update and take back the release, and that the owner's own settings stay as they were.
