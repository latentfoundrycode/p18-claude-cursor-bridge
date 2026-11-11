# SCOPE: SLIM-001, release S (1 of 3), the programs and their tests

Pull request #152, branch `slim-001`, base `origin/main` at 05962c2. The diff is `run/review/REVIEW-SLIM-001-r1.diff`, taken from committed state. There was no builder and no handoff brief: the bridge's maintainer wrote this diff in a separate clone, on the owner's word of 2026-11-11, to the terms of the pace audit of 2026-11-09 and the agreement with the bridge's supervisor of 2026-11-10. This file stands in for the brief's Scope and Out of scope.

## Scope (what this pull request is to do)

1. **C1, a stripped run no longer sees the owner's application data.** `bridge_env.stripped_env` points `APPDATA` and `LOCALAPPDATA` (and the cache names beside them) at folders under the agent home, `~/.cursor-bridge/agent-home`. `cursor-agent` keeps its login state under `%APPDATA%\Cursor` (probed live on 2026-11-11: with `APPDATA` redirected and no link it reports "Not logged in"; with the link it is logged in and lists its models), so `app_links` makes one link, `AppData/Roaming/Cursor` under the agent home, to the owner's `%APPDATA%\Cursor`. It fails open: where the link cannot be made or leads elsewhere, the run keeps the owner's `APPDATA`. `bridge-check.py` reports that state (`STALE    agent home`, "runs keep the owner's APPDATA") and writes nothing (`create=False`: a missing link or an empty folder is no problem); `bridge-install.py` repairs a link that leads elsewhere (`repair=True`) and never removes a folder with content. `cursor-agent.shim` does the same for a launch through the shim. D-004's note names the set variables.
2. **`--kind test` refuses a target outside the launch folder** (`bridge-run.py`, `outside_target`): a pytest or unittest path argument that resolves outside the folder the launcher was started in is refused, exit 125. (A project's suite once ran against another checkout's key file.)
3. **C18, a run that ends at its limit teaches nothing** (`bridge-run.py`): exit 124 never raises the learned limit; `--healthy <run id>` refuses a builder or review run that ended 124.
4. **Text evidence** (`completion-check.py`): an Evidence cell may read `text: <file>.md :: <heading> (#<pull request>)`. The file must exist, hold that heading, and the squash `(#<pull request>)` be on `origin/main`; the form is refused for a row whose Requirement names a program. Every other rule of the check is unchanged.
5. **The records short gate** (`review-guard.py premerge-records [<pr>]`): classifies the head's change against `origin/main` by path. Records are `docs/`, `handoff/` and `project.json`. Never records, whatever their folder: `docs/RUN_PARAMETERS.md`, any `docs/BUILD_PLAN*`, `docs/ROSTER*`, a changed Status cell of the register, a changed threat-model line of the inventory. It prints `SHORT GATE` (and with `<pr>` checks the head is the pull request's head and writes the premerge record), `FULL GATE` (exit 1, no record) or `CANNOT CHECK` (exit 2, no record).
6. **The hook's shorter list after a compaction** (`session-start.py`): the status file, the last entries of `run/supervisor/in-flight.md`, the one module of the step in hand; other files as `on demand:` lines. The 10,000-character limit of the hook's output is unchanged.
7. **The plan check's size note** (`plan-check.py`, `bridge_env.plan_done_when_items`): a `note:` for an increment with more than twelve acceptance items in its `Done when:` or more than twelve Scope paths. Never a failure; the exit code is unchanged. The reading of `Done when:` lives in `bridge_env.py` because `tests/test_header_plan_r3.py` holds that `plan-check.py` walks no plan itself.
8. **Round causes and rounds per model** (`bridge-run.py`, `pace-report.py`): a numbered brief after the first may carry `Round cause: <cause> - ...`; the launcher writes it to the run log as `cause` (`unstated` with a note where missing or unknown, never a refusal); the pace report prints one line of causes and one of builder rounds per model.
9. **Two word budgets as tests** (`tests/test_release_s_budgets.py`): every `.md` under `bridge/` except the changelog and the design seeds together at most 150,000 words; each phase module and step file at most 8,000.

## Out of scope (not this diff's defect)

- The instruction texts that describe these mechanisms (the core, the phase modules, the policy, the pitfalls, the agents): the third pull request. Until it merges, text and program disagree on purpose in places (the hook's list, the records gate, the Evidence form); nothing is installed before the stamp, `VERSION` stays 2026.11.11a.
- The retirement of size and hash pins, per-file caps and prose-literal tests: the second pull request.
- The supervisor's later program release: trace-check per passage, the carry comparison, `premerge`'s required-context check, a guard-side round cause, the launcher items C2 to C17 and C20 to C23.
- Design for later releases.

## Threat model (docs/INVENTORY.md, Decisions)

- **The review guard** (row "The review guard's threat model", for R-050, as KP-032 states it): what a reviewer does in passing in the checkout is inside it (a deletion, a rewrite, a planted hook, a moved ref under `.git`); a deliberate reach past it is outside it and recorded, never blocking by itself. The guard runs as the owner's Windows user beside the reviewer: it is not a sandbox.
- **The session-start hook** (row "The session-start hook's threat model"): a partial, mismatched or hand-edited install, not a hostile checker or module; nothing reaches the hook's output except as an exact string matching its pattern; `bridge_env` is loaded from the hook's own folder only.
- **The stripped environment** has no row of its own. KP-032 and KP-038 govern: builders and reviewers run with the owner's identity and keys withheld, as a guard against what an agent does in passing, not against one that reaches for the credential store on purpose. C1 narrows what such a run can read and overwrite in passing; the link to `%APPDATA%\Cursor` is the one deliberate opening, the login `cursor-agent` cannot run without.
- For the other parts the diff changes (the launcher's limits, `completion-check.py`, `plan-check.py`, `pace-report.py`) the inventory records no threat model: the five blocking classes stand unbounded there.

## Tests, each with what it enforces

| Test file | Enforces |
|---|---|
| `tests/test_account_keys.py` (changed) | item 1: the set and withheld names of a stripped run equal D-004's note; the four states of the link (made, already right, leads elsewhere, folder with content) and the fail-open result |
| `tests/test_release_t_strip.py`, `tests/test_bridge_run.py` (changed) | item 1 through the launcher: a stripped run's environment; the cache folders exist |
| `tests/test_install_check.py` (new test) | item 1: the check reports and writes nothing; the install repairs a link that leads elsewhere, refuses a folder with content, removes nothing through a link |
| `tests/conftest.py` (changed) | the suite's own `APPDATA` is a temporary folder, so no test makes a link to the owner's real one |
| `tests/test_release_s_launcher.py` (new) | items 2, 3 and 8: the outside-target refusal; exit 124 and the learned limit; `--healthy`'s refusal; the `cause` field; the pace report's two lines |
| `tests/test_task032_supervisor_launcher.py` (changed) | item 8: the run log's fields include `cause` |
| `tests/test_release_s_evidence.py` (new) | item 4 |
| `tests/test_release_s_records_gate.py` (new) | item 5: each path class, each never-records file, the Status cell and threat-model line, the record written only on `SHORT GATE` with a matching head |
| `tests/test_session_start.py`, `tests/test_session_start_module.py`, `tests/test_reads_only_applicable.py`, `tests/test_release_t_merge.py` (changed) | item 6: the hook's lines per phase, and its limit |
| `tests/test_release_s_plan_size.py` (new) | item 7 |
| `tests/test_release_s_budgets.py` (new) | item 9 |

No mutants file and no mutation driver: the maintainer ran no mutation run on this diff.

## Expected bookkeeping and records in the diff

- `bridge/cursor-bridge/MANIFEST.json` (regenerated by `tools/make-manifest.py`; CI compares it with the tree).
- `docs/CLI_REFERENCE.md`, `docs/cli-reference.json` (regenerated by `tools/dump-cli.py`; CI compares).
- `docs/diagrams/D-004-context-dfd.md` (the note's Set list, compared with the program by `tests/test_account_keys.py`).
- `docs/PROJECT_STATUS.md`: one line, `Last accepted:`, names PR #152 first, which `tests/test_release_b_bootstrap.py::test_r001_status_names_its_own_merge` requires of every pull request into main.
- `run/review/` (this file, the diff, the assumptions file), removed before the merge.

No `docs/BUILDER_NOTES.md` entry and no builder report: there was no builder run.
