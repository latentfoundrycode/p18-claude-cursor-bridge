# TASK-002: The security floor in the bridge's CI

## Objective
The bridge's GitHub Actions workflow today runs the test suite, a windowless check and a manifest check on Windows and Ubuntu, and installs its two test dependencies by naming them on a `pip install` line. This increment adds the bridge's security floor to that CI: a committed lockfile (`requirements.lock`) that CI installs from and that the dependency scanners read; Semgrep, OSV-Scanner and Socket running in the gate with their configuration files (`.semgrep.yml`, `osv-scanner.toml`, `socket.yml`); every GitHub Action and every scanner version pinned; and a structural test that keeps all of this from quietly eroding. The point is that a pull request on the bridge's own repository cannot go green while it introduces a known-vulnerable or malicious dependency or a high-severity code finding, and that no part of the floor can silently skip itself.

Satisfies: R-002 — The security floor (Semgrep, OSV-Scanner, Socket) runs in the bridge's own CI gate, pinned by commit, installing from a committed lockfile, alongside the tests it already runs.

## Scope
Files you may create or modify:
- .github/workflows/tests.yml
- .semgrep.yml
- osv-scanner.toml
- socket.yml
- requirements.lock
- tests/test_release_b_ci_floor.py
- docs/BUILDER_NOTES.md
- handoff/TASK-002-r1-report.md

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- Any other file under `.github/` (no new workflow file, no other workflow change beyond `.github/workflows/tests.yml`)
- Everything under `bridge/` (including `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/semgrep-bridge-rules.yml`, which you may reference but not edit)
- docs/ and handoff/, except the files the Scope section names (in particular `docs/INVENTORY.md`: the supervisor records the pins and the Semgrep mode there after this lands)
- Every existing test under `tests/` (only `tests/test_release_b_ci_floor.py` is yours)
- The repository's settings on GitHub: branch protection, required checks, repository secrets. Do not run `gh` against the repository at all.
- A `pyproject.toml`, `requirements.txt`, or any second dependency manifest

## Context
The repository root is the folder you were started in (it holds `.github/`, `bridge/`, `docs/`, `tests/`, `project.json`). Paths below are relative to it.

**The current workflow, `.github/workflows/tests.yml`, in full (this increment adds to it; the existing checks stay):**

```yaml
name: tests
on:
  push:
    branches: [main]
  pull_request:
jobs:
  tests:
    name: bridge programs (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [windows-latest, ubuntu-latest]
    steps:
      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
        with:
          python-version: "3.12"
      - run: python -m pip install pytest==9.1.1 pyyaml==6.0.3
      - run: python -m pytest tests -q
      - name: windowless check over the bridge's programs
        run: python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
      - name: the manifest matches the tree
        run: python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

The pinning style to follow is the one above: `owner/repo@<full 40-character commit SHA> # <tag>`. For an annotated release tag, the SHA is the commit the tag points at (the peeled `^{}` entry of `git ls-remote --tags https://github.com/<owner>/<repo>`), not the tag object's own SHA.

**No dependency manifest exists today.** There is no `requirements.lock`, `requirements.txt`, `pyproject.toml` or `setup.cfg` in the repository; the only dependency statement is the `pip install pytest==9.1.1 pyyaml==6.0.3` line above. Those two pins (pytest 9.1.1, pyyaml 6.0.3, on Python 3.12) are fixed by this increment; do not change either version.

**The bridge's own conformance check reads this workflow.** `bridge/cursor-bridge/conformance-check.py` (read its docstring, lines 1–54, and the workflow section, lines 304–345) judges a project's gate step by step: a scanner step is recognised by `semgrep`, `osv-scanner`, or `socket`/`socketsecurity` in its `run:`/`uses:` text; a scanner step guarded by `if:` is reported MISSING ("skipped silently when its condition is false"); a scanner with no version where it is installed or run is a NOTE; Semgrep counts as the floor only if it runs `semgrep ci` (the Pro engine) or the bridge rules (`bridge-rules` in the command) or `--config .semgrep...`; every `uses:` must end in `@` plus 40 lowercase hex characters. The bridge's floor must pass its own check.

**The bridge's reference texts for this floor** (installed copies, read-only, outside this workspace — their relevant content is restated here so you need not open them): the configuration guide's §5c and the file-formats guide say that `.semgrep.yml` holds the project's own rules only, in Semgrep's rule schema (`rules:` with `id`, `languages`, `severity`, `message`, `pattern`/`patterns`) — a registry pack such as `p/default` is not valid inside it and goes on the command line; `osv-scanner.toml` carries an empty `[[IgnoredVulns]]` (commented-out example only) until a reasoned, expiring exception is agreed; `socket.yml` is `version: 2` with empty `issueRules: {}`; Semgrep runs on Linux in CI, and with the `SEMGREP_APP_TOKEN` secret it runs `semgrep ci`, which uses the Pro engine; Socket runs `socket ci` (the Node CLI `@socketsecurity/cli`), non-zero on unhealthy alerts; scanners get only the minimum environment — no secret on a scanner's path beyond its own token. The bridge's vendored token-free Semgrep supplement already lives in the repository at `bridge/cursor-bridge/semgrep-bridge-rules.yml`; you may point a Semgrep config at it, but do not edit or copy it.

**Known pitfalls that apply** (from the bridge's Known-Pitfalls register): KP-005 — OSV-Scanner's exit codes are 0 clean, 1 findings (fail), 127 execution failed (fail), **128 no packages found (fail)**; an empty inventory must never pass as green, and the raw exit code is the pass/fail signal. KP-007 — Semgrep is reliable on Linux; CI on `ubuntu-latest` is authoritative; a scanner that will not start is a hard red, never a pass. KP-018 — CI installs from the lockfile; a manifest change pairs with its lockfile change. Here `requirements.lock` is both the manifest and the lock, so `bridge/cursor-bridge/lock-check.py` sees no separate manifest and reports nothing to verify; that is expected.

**Repository secrets.** Two secrets are already set in the GitHub repository by the owner: `SEMGREP_APP_TOKEN` (Semgrep, Pro engine) and `SOCKET_SECURITY_API_KEY` (Socket). Refer to them only as `${{ secrets.SEMGREP_APP_TOKEN }}` and `${{ secrets.SOCKET_SECURITY_API_KEY }}`. You do not have their values and do not need them. The bridge's records say the Socket CLI reads its token from an environment variable named `SOCKET_CLI_API_TOKEN`; the repository secret has a different name, so the workflow must expose the secret under whatever variable name the Socket CLI version you pin actually reads (confirm it from that version's own documentation or `--help`, and list it under Assumed, not verified).

**Security context.** This increment adds no application logic; its surface is the CI supply chain. Trust boundaries: (1) repository secrets enter the runner — each token reaches only the one step that needs it (step-level `env:`), is never echoed, and never appears in a committed file; (2) third-party code enters CI — every action is pinned by full commit SHA and every scanner by an exact version, never a mutable tag or "latest"; (3) the pull request's contents are what the scanners read. No ASVS level is recorded for the bridge in `docs/INVENTORY.md`; none is needed for CI configuration. There is no `.cursor/rules/` folder in this repository, so no frozen secure-coding or minimal-code rule file is in force; the constraints below are the whole set.

**Development data** (copied from `docs/INVENTORY.md` Decisions): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet." For this increment that means: run the test suite and the checks from this repository's sources as given in the Done section; never run anything against `~/.claude` or any other project. `tests/conftest.py` already redirects `HOME`/`USERPROFILE` to a temporary folder for every test.

**Existing test conventions.** See `tests/test_release_b_bootstrap.py`: module docstring naming the plan task and the requirement ID, `ROOT = pathlib.Path(__file__).resolve().parent.parent`, files read with `encoding="utf-8"`, each test's docstring naming the requirement. PyYAML 6.0.3 is available to tests (`import yaml`; note that `yaml.safe_load` turns the workflow's `on:` key into the boolean `True`).

## Diagrams
None. The build plan names no diagram for this increment (`docs/INVENTORY.md` Decisions: no diagram index for release B).

## Requirements
1. `requirements.lock` exists at the repository root and is the only dependency file CI installs Python packages from. It pins `pytest==9.1.1` and `pyyaml==6.0.3`, and it pins with `==` every package pip installs for them on Python 3.12 on both Windows and Linux (their transitive dependencies included, with an environment marker on any that is platform-specific), so that nothing CI installs from it is unpinned. It names no other direct dependency. Hashes are optional.
2. Both legs of the existing `tests` job install from `requirements.lock`; the old `pip install pytest==9.1.1 pyyaml==6.0.3` line is gone. The existing test, windowless and manifest steps keep running on both legs, unchanged.
3. The workflow runs Semgrep, OSV-Scanner and Socket on every pull request and on every push to `main`, each on `ubuntu-latest`. None of the three scanner steps is guarded by an `if:` condition, marked `continue-on-error`, or followed by anything (`|| true`, a swallowed exit code) that lets a failed scan pass. The Windows leg does not run Semgrep. Whether the scanners live in the existing job or in a new job is yours to decide, within these constraints and the conformance check described in Context.
4. Semgrep runs with the Pro engine, authenticated by `${{ secrets.SEMGREP_APP_TOKEN }}`, and the rules in `.semgrep.yml` are applied in the same Semgrep run or in a second Semgrep step. `.semgrep.yml` holds rules only, in Semgrep's rule schema (no registry pack inside it), and the pinned Semgrep version accepts it without a configuration error. A blocking finding fails the step. A Semgrep that fails to install, start or authenticate fails the step.
5. OSV-Scanner scans `requirements.lock` with `osv-scanner.toml` as its config. The step handles OSV's exit codes explicitly: 0 passes; 1, 127, 128 and any other non-zero code fail; 128 (no packages found) fails with a message saying the lockfile was not read. The OSV step receives no secret.
6. Socket runs `socket ci` (or the pinned CLI's equivalent CI scan) with `socket.yml` in the repository root, authenticated by `${{ secrets.SOCKET_SECURITY_API_KEY }}` exposed only to the Socket step. The step fails on an unhealthy report and fails when Socket finds no manifest to scan; it must actually scan `requirements.lock`.
7. `osv-scanner.toml` carries no active ignore (only a commented-out `[[IgnoredVulns]]` example with id, `ignoreUntil` and reason). `socket.yml` is `version: 2` with empty `issueRules: {}`. Neither contains a secret.
8. Every `uses:` in the workflow (step level and job level) is pinned as `owner/repo[/path]@<40 lowercase hex>` with the tag in a trailing comment, following the existing lines. Reuse the two existing pins for checkout and setup-python. The Semgrep, OSV-Scanner and Socket versions are each pinned exactly where they are installed or run (for example `semgrep==<x.y.z>`, `@socketsecurity/cli@<x.y.z>`, an OSV release `v<x.y.z>`); no scanner is installed as "latest". If you download a release binary, the step checks its SHA-256 against a value written in the workflow before running it.
9. `tests/test_release_b_ci_floor.py`, whose module docstring names R-002 and TASK-002, asserts by reading the committed files (it runs no scanner and starts no process): (a) the workflow parses as YAML; (b) a step runs each of Semgrep, OSV-Scanner and Socket, on a job whose `runs-on` is `ubuntu-latest`, and none of those steps carries `if:` or `continue-on-error`; (c) every `uses:` value in the workflow ends in `@` and 40 lowercase hex characters; (d) every pip install in the workflow installs from `requirements.lock` (`-r requirements.lock`) and no step installs pytest or pyyaml by name; (e) `requirements.lock` pins `pytest==9.1.1` and `pyyaml==6.0.3` and every requirement line in it is pinned with `==`; (f) the two secrets are referenced by name in the workflow as `secrets.SEMGREP_APP_TOKEN` and `secrets.SOCKET_SECURITY_API_KEY`, and neither appears in a job-level or workflow-level `env:`. Each test function's docstring names R-002.

## Acceptance criteria
- [ ] `requirements.lock` exists, pins pytest 9.1.1 and pyyaml 6.0.3 and their whole install closure with `==`, and both legs of the `tests` job install from it.
- [ ] Semgrep (Pro engine via `SEMGREP_APP_TOKEN`, `.semgrep.yml` applied), OSV-Scanner (`requirements.lock`, `osv-scanner.toml`, exit codes 0/1/127/128 handled, 128 fails) and Socket (`socket.yml`, `SOCKET_SECURITY_API_KEY`) run unguarded on `ubuntu-latest` on every PR and push to `main`.
- [ ] Every `uses:` is pinned by a full 40-hex commit SHA; each scanner version is pinned exactly.
- [ ] `python bridge/cursor-bridge/conformance-check.py . --offline` reports `OK` for "Semgrep in the gate", "OSV-Scanner in the gate", "Socket in the gate", "Semgrep bridge rules or Pro engine" and "CI actions pinned by commit", and no "… version pinned" NOTE for any of the three scanners. (Its overall exit code may be 1 because of floors outside this increment; only these lines are the criterion.)
- [ ] `tests/test_release_b_ci_floor.py` passes, names R-002, and covers (a)–(f) of Requirement 9; the full suite passes with no other change in results.
- [ ] No secret value appears in any file you wrote, in your report, or in any command output you paste.
- [ ] (Verified by the supervisor after the push, not by you.) The workflow is green on the pull request: both `tests` legs and the scanner steps, with Semgrep authoritative on ubuntu, OSV and Socket having read `requirements.lock` (neither exiting 128 or reporting no manifest).
- [ ] R-002 is fully met — no stand-in, placeholder step, `echo` in place of a scan, or "added later" text — and the test names R-002 so the trace is checkable.

## Constraints
- Do not add dependencies. `requirements.lock` pins the existing two test dependencies and their closure only; the scanners are CI tools installed by the workflow at pinned versions, never added to `requirements.lock`.
- Do not install Semgrep, OSV-Scanner or the Socket CLI on this computer, and do not try to run them here: they are verified on the pull request by the supervisor. Record what you expect of each (its flags, its exit codes, the token variable it reads, whether it recognises `requirements.lock`) under Assumed, not verified.
- If the Socket CLI or OSV-Scanner version you pin cannot be made to read a file named `requirements.lock` (check each tool's documented list of supported manifest names and any option that names the file's format), stop and report it; do not rename the lockfile, add a `requirements.txt`, or otherwise change the plan's file set. That is a scope decision for the supervisor.
- If Semgrep's Pro engine (`semgrep ci` with the token) cannot be combined with the rules in `.semgrep.yml` in the version you pin (for example, if that version refuses `--config` while a token is set), satisfy Requirement 4 with two Semgrep steps or report the conflict; do not drop either half.
- Do not suppress or ignore any finding: no `nosemgrep`, no `[[IgnoredVulns]]` entry, no Socket ignore, no `continue-on-error`, no exit code swallowed. If you expect a scanner to report a finding in existing code under `bridge/` or `tests/`, say so in your report; do not edit that code.
- The default `run:` shell on GitHub's Linux runners stops at the first failing command (`bash -e`, or `-eo pipefail` with `shell: bash`); a step that inspects a scanner's exit code must capture it without the shell aborting first.
- No secret value anywhere: refer to `SEMGREP_APP_TOKEN` and `SOCKET_SECURITY_API_KEY` only through `${{ secrets.<NAME> }}`; never echo, print or `set -x` around a step that holds one.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way — an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason — append one dated line describing it to `docs/BUILDER_NOTES.md` (create it if absent). Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python — `0` on other platforms). The test in this increment reads files only and should launch nothing.
- Never start a server, a watcher or a daemon that outlives a test.
- Never run the product, a migration, a seed or a test against the owner's live data; see the Development data paragraph in Context.
- Do not refactor code outside the scope, even if it looks wrong.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only. `git ls-remote` (read-only, to resolve an action's commit SHA) is allowed.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This applies to any exit code the workflow compares (an integer, range 0–255).
- Prefer reuse over new code — existing helpers, the standard library, already-installed dependencies — and write the minimum that meets the acceptance criteria. This never overrides a security requirement stated above.
- Every verification command the Done section asks you to run is written there in full; run exactly those.

## Done
Run each of these from the repository root (the folder you were started in), in this order, and paste each command with its exit code and the relevant output lines into your report:
1. `python -m pytest tests/test_release_b_ci_floor.py -q`
2. `python -m pytest tests -q`
3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
5. `python bridge/cursor-bridge/conformance-check.py . --offline` — paste the lines for the five floors named in the acceptance criteria and any "version pinned" NOTE.
6. `python bridge/cursor-bridge/lock-check.py origin/main` — expected exit 0.
7. `python -m pip install --dry-run --ignore-installed -r requirements.lock` — the "Would install" list must contain exactly the packages `requirements.lock` pins for this platform, at those versions (this needs network access; if it has none, say so).

Your report is the file `handoff/TASK-002-r1-report.md`, which you write as you go — what you did, what you changed, what you ran and what it printed, what you could not do — so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, the exact pinned versions and action tags you chose (the file each lives in; no secret), and a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm — at least: the environment variable the pinned Socket CLI reads its token from; whether Socket and OSV recognise `requirements.lock` and how; how the pinned Semgrep combines the Pro engine with `.semgrep.yml`; OSV's exit codes in the version you pinned; any finding you expect a scanner to raise on the first run. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
