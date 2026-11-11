# SCOPE: SLIM-001, release S (1 of 3), the programs and their tests

Pull request #152, branch `slim-001`, base `origin/main` at 05962c2. The diff is `run/review/REVIEW-SLIM-001-r2.diff` (round 2; "Round 2" below says what changed since round 1), taken from committed state. There was no builder and no handoff brief: the bridge's maintainer wrote this diff in a separate clone, on the owner's word of 2026-11-11, to the terms of the pace audit of 2026-11-09 and the agreement with the bridge's supervisor of 2026-11-10. This file stands in for the brief's Scope and Out of scope.

## Scope (what this pull request is to do)

1. **C1, a stripped run no longer sees the owner's application data.** `bridge_env.stripped_env` points `APPDATA` and `LOCALAPPDATA` (and the cache names beside them) at folders under the agent home, `~/.cursor-bridge/agent-home`. `cursor-agent` keeps its login state under `%APPDATA%\Cursor` (probed live on 2026-11-11: with `APPDATA` redirected and no link it reports "Not logged in"; with the link it is logged in and lists its models), so `app_links` makes one link, `AppData/Roaming/Cursor` under the agent home, to the owner's `%APPDATA%\Cursor`. It fails open: where the link cannot be made or leads elsewhere, the run keeps the owner's `APPDATA`. `bridge-check.py` reports that state (`STALE    agent home`, "runs keep the owner's APPDATA") and writes nothing (`create=False`: a missing link or an empty folder is no problem); `bridge-install.py` repairs a link that leads elsewhere (`repair=True`) and never removes a folder with content. `cursor-agent.shim` does the same for a launch through the shim. D-004's note names the set variables.
2. **`--kind test` refuses a target outside the project** (`bridge-run.py`, `outside_target`, `launch_roots`): a pytest or unittest run whose target leads outside is refused, exit 125. Inside means under the launch folder or one of the repository's worktrees (rule 39 keeps a second live branch under `<root>/Worktrees/`), links resolved. Checked since round 2: uv's `--project` and `--directory` before the word pytest (the second becomes the folder the targets are read against), the file `--config-file` names, the folder `--confcutdir` names, an `@file` of arguments (refused whatever it holds); the word after a value option (`--junitxml`, `--log-file`, `--ignore`, `-k` and the like) is its value and never a target, so a report written to a temporary folder is not refused. Not covered and not claimed: other runners (npm, go, cargo), `--pyargs`, an ini option set by `-o`. The supervisor writes the command; the refusal is a guard against a probe run in passing, not a sandbox.
3. **C18, a run that ends at its limit teaches nothing** (`bridge-run.py`): exit 124 never raises the learned limit; `--healthy <run id>` refuses a builder or review run that ended 124.
4. **Text evidence** (`completion-check.py`; narrowed in round 2): an Evidence cell may read `text: <file>.md :: <heading> (#<pull request>)`, only in a project whose `project.json` declares where its instruction texts are (`instruction_texts`, a list of folders; a record folder, the Workspace itself or a path outside it declares nothing). The file must stand under a declared folder, hold that heading outside a code block, and the squash `(#<pull request>)` be on `origin/main` and have changed that file (a note on a branch of unmerged work and in a shallow clone). For a row whose Requirement names a program a text entry never counts: the cell names a test beside it, and done mode still asks for a tracked test that names the row. A project that declares nothing takes no text entry at all, which is every project whose product is no instruction text. This repository's `project.json` gains the declaration (`bridge/`) in the third pull request, with the texts. Every other rule of the check is unchanged.
5. **The records short gate** (`review-guard.py premerge-records [<pr>]`; narrowed in round 2): classifies the head's change against `origin/main` (with `<pr>`, against the pull request's base, joined with GitHub's own list). A path takes the short gate only where it is a record by its folder (`docs/`, `handoff/`, or `project.json`), by its type (`.md`, `.json`, `.txt`, `.csv`, a picture) and by its mode (a plain file: no link, no submodule entry, no executable), and is none of these, compared in lower case: `docs/RUN_PARAMETERS.md`, any `docs/BUILD_PLAN*`, `docs/ROSTER*`, anything under `docs/diagrams/` (the diagrams, their index and the deviations decide what `diagram-check.py` allows), a removed status file, inventory, register or project file, the register where a Status cell changed, a row left, a new row is not `planned` or a built row's Evidence changed, the inventory where a line naming the threat model or a line under a heading naming it changed, the project file where `instruction_texts` changed or which cannot be read. With `<pr>` the pull request must merge into `main`. It prints `SHORT GATE` (and with `<pr>` checks the head is the pull request's head and writes the premerge record), `FULL GATE` (exit 1, no record) or `CANNOT CHECK` (exit 2, no record). It checks neither CI nor Review A: the branch rule holds the first, the supervisor's step the second, and its text now says so. Briefs under `handoff/` stay records: a brief reaches a builder only on an increment's branch, whose pull request takes the full gate with the brief in its diff.
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

## Round 2: what round 1 found and what was done

Round 1 was Review A alone (`diff-reviewer` and `security-auditor`), both REJECT, before any Review B run. The diff of round 2 is `run/review/REVIEW-SLIM-001-r2.diff`.

Blocking, fixed:

1. **A text entry proved any row** (both reviewers; `completion-check.py`): `text: README.md :: Install (#1)` passed done mode for a product row with no test, since only a program's name in the sentence refused the form and nothing tied the number to the file. Now item 4 above: declared folders only, the squash must have changed the file, a heading in a code block is none, a drive-relative path is no file, and a program row's text entry never counts. `tests/test_release_s_evidence.py`: `test_a_product_row_cannot_be_proved_by_a_text` is the reviewers' case; with it `test_only_a_file_under_a_declared_folder_counts_and_a_record_folder_is_never_one`, `test_the_pull_request_named_must_have_changed_the_file`, `test_a_heading_inside_a_code_block_is_no_heading`, `test_for_a_row_whose_sentence_names_a_program_a_text_entry_never_counts`.
2. **The short gate decided by folder alone** (`security-auditor`; `review-guard.py`): `docs/conf.py`, `docs/conftest.py`, `handoff/run.sh` and a link entry took the short gate. Now by type and mode too (item 5).
3. **Records a program reads to decide a gate took the short gate** (`diff-reviewer`): `docs/diagrams/DEVIATIONS.md`, the index and the diagrams. Now the whole of `docs/diagrams/` keeps the full gate. The maintainer's ruling on the pace question the reviewer left open: a diagram is normative (rule 45), so its change is read by both reviewers; the short gate is for the status file, the inventory's other rows, HARDENING, the notes and the briefs, which is where the audit counted the rounds.
4. **An Evidence-cell change took the short gate** (both): a built row's Evidence changed now keeps the full gate, so the pair of findings 1 and 4 is closed from both sides.

Advisory, taken: the status file's removal, and the inventory's, the register's and the project file's (full gate); names compared in lower case; a threat model written as a section under a heading; a pull request into another branch than `main`; the docstring's claim about CI and Review A; `outside_target`'s false passes (uv's folder options, `@file`, `--config-file`, a link leading outside) and false refusals (a value option's separate word), with a repository's worktrees now inside; the message for a file or a folder in use in the link's place; the missing space in the status file's line; the evidence test's docstring.

Advisory, not taken, each with its reason:

- `PYTHONUSERBASE` and `UV_PYTHON_INSTALL_DIR` still lead to the owner's folders, so a `pip install --user` in passing still writes there: no regression (all of `APPDATA` was the owner's before), and they are passed on purpose (`APP_CACHES`): the user's installed packages and uv's interpreters live there, and a run that lost them would download or build them again or not start its suite. A lead for the supervisor's program release.
- The shim keeps the owner's `APPDATA` where an empty folder stands in the link's place, and Python replaces it: both safe; the install makes the link, so the state is rare.
- An untracked text file passes locally: the squash-changed-the-file check fails it on merged work.
- Other runners than pytest and unittest in `outside_target`, `--pyargs`, `-o pythonpath=`: stated above as not covered.
- npm's `prefix=${APPDATA}\npm`, Volta and `py.ini` under `LOCALAPPDATA`: a stripped suite of another project may meet the agent home's empty folders and would fail visibly. One stripped suite run per project at its calibration settles it; the release's changelog entry names that step.

## Expected bookkeeping and records in the diff

- `bridge/cursor-bridge/MANIFEST.json` (regenerated by `tools/make-manifest.py`; CI compares it with the tree).
- `docs/CLI_REFERENCE.md`, `docs/cli-reference.json` (regenerated by `tools/dump-cli.py`; CI compares).
- `docs/diagrams/D-004-context-dfd.md` (the note's Set list, compared with the program by `tests/test_account_keys.py`).
- `docs/PROJECT_STATUS.md`: one line, `Last accepted:`, names PR #152 first, which `tests/test_release_b_bootstrap.py::test_r001_status_names_its_own_merge` requires of every pull request into main.
- `run/review/` (this file, the diff, the assumptions file), removed before the merge.

No `docs/BUILDER_NOTES.md` entry and no builder report: there was no builder run.
