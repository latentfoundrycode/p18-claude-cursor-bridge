# SCOPE - T2-CORR: the closing records corrected

## What this pull request is
A records pull request with no builder run, no brief, no test and nothing under `bridge/`. It takes the same round as any pull request (merge.md: a pull request that changes only records). PR #134, merged 2026-11-04T09:10:19Z, said in `docs/HARDENING.md` and `docs/PROJECT_STATUS.md` that the TDP (the bridge's trial project, a separate repository) had not calibrated to 2026.11.03a. Its own status file shows it had. This pull request states the true position.

The increment ends with the status file as at this pull request's merge (Phase: done). `sync-check.py --apply --strict`, `completion-check.py --mode done` and `diagram-check.py --mode done` run again after the merge. The Documents folder (User Manual, Project Summary, Issues ISS-024 (m), Feedback FB-084 and PT10) lies outside the repository and is not in the diff.

## Scope: the files expected in the diff
- `docs/HARDENING.md`: the one bullet marked wrong when merged; the strict check's sentence; a new last section, "Correction to project end".
- `docs/PROJECT_STATUS.md`: Last accepted, Awaiting user on, Next, Working files, Remote sync and Calibration pending, as at the merge of this pull request, predicted #135 (newest pull request 134, no issues).
- `run/review/`: this file, the round's diff and its assumptions file, removed before the merge.

## Out of scope
Everything under `bridge/`. Any requirement's row: R-056 stays `built`. Any change of behaviour. Any correction of what the TDP records about itself.

## The threat model
None is recorded for what this diff changes: it is records.

## The tests
None written. The suite ran stripped, with the pull request's variables, on 9e94986, one commit before the review head: `run/agent/T2CORR-suite.out`, "3561 passed, 40 skipped in 1688.71s (0:28:08)". The commit after it, 602cceb, changes two sentences of `docs/HARDENING.md`, a file no test reads from this repository (the tests that name it write their own copy in a temporary repository).

## Review A
Review A read 3e2c580: REJECT, one blocking finding (the field acceptance narrowed to one of the CHANGELOG entry's three clauses), one Should fix, six Considers, all taken in 9e94986. Its confirming read of 3e2c580..9e94986: APPROVE, nothing blocking, two Shoulds in the records taken in 602cceb and one Should and one Consider taken in Documents. The status file's Next keeps its shorter wording of the weekly clause, naming HARDENING's section for the whole of it.

## The claims about another project
The diff states facts about the TDP. They cannot be checked from this repository: its checkout is named in the launch prompt, read-only. The earlier round's SCOPE file stated the false claim as a fact and no reviewer was asked to read the other project, so do read it here.

## The open item the diff states
The CHANGELOG entry's field acceptance has three clauses (`bridge/cursor-bridge/CHANGELOG.md:56`). The weekly clause stays open past the TDP's next increment; the diff says so and says why.
