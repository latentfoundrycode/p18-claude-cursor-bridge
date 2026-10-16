# TASK-008 round 2: the Workflows status line — the first review's corrections

## Objective
Round 1 (`handoff/TASK-008-r1-report.md`) was reviewed by Review A, a security auditor and Review B. Review B approved. Review A and the security auditor both found, independently, that loading `workflow-check.py` writes `__pycache__/workflow_check.*.pyc` beside the installed programs, although `conformance-check.py`'s docstring says "Never writes" and `inventory-check.py` reads only. Two reviewers naming the same defect makes it blocking. This round removes that write, and closes three small fail-closed gaps the reviewers found in the same function. **`handoff/TASK-008.md` still holds in full**; this file changes only what it says, and where they differ this file wins.

Satisfies: R-015 (unchanged).

## Scope
Files you may modify:
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json (regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`)
- docs/BUILDER_NOTES.md
- handoff/TASK-008-r2-report.md

Do not modify anything else. `bridge/cursor-bridge/workflow-check.py` does not change in this round.

## Written by the supervisor; do not edit
`tests/test_workflows_line_check.py` was extended for this round and is committed with this file. Do not edit, move, rename or add to it, nor `tests/test_conformance_check.py`, `tests/test_workflow_check.py` or anything under `tests/fixtures/workflows/`. If a supervisor test contradicts a brief, stop, change no test, and report the contradiction: the test name, the brief requirement, and what each says.

## Corrections (each is a requirement)
Each applies identically to `judge_workflows_line` in both programs.

### R2-1. Loading the checker writes no bytecode
While `judge_workflows_line` loads `workflow-check.py` (`spec.loader.exec_module(mod)`), `sys.dont_write_bytecode` is `True`. Save its previous value first and put it back in a `finally`, so the rest of the program behaves as before. After either program has run, no `__pycache__` folder exists beside it (unless one existed before). Both docstrings stay true as written ("Never writes", "reads only"); do not change them.

### R2-2. The checker's path is resolved through links
The folder the checker and its rule files are loaded from is `os.path.dirname(os.path.realpath(__file__))`, not `abspath`. Run through a symbolic link placed elsewhere, a program loads the `workflow-check.py` that sits beside its real file, never one beside the link.

### R2-3. Every printed field is escaped, or the check is not checked
`field(mod, value)` calls `mod.escape_field(value)` directly, then applies the ASCII `backslashreplace` as now. There is no fallback to the raw value: with a loaded module that lacks `escape_field`, a check that would print a field (a malformed line, a rule-file cause) is `not-checked` instead. The handler that reports an exception after a successful load must not itself call `field` (it would raise again): its reason, `<path to workflow-check.py>: <exception class name>`, goes through `ascii_text` only, as the load-failure reason already does.

### R2-4. A checker that exits while loading is "cannot be loaded"
The load step catches `SystemExit` as well as `Exception`: a `workflow-check.py` that calls `sys.exit(3)` at import gives the `not checked: <path>: cannot be loaded (SystemExit)` line (inventory-check) or row (conformance-check), never a silent exit. The same holds for the handler after a successful load (`<path>: SystemExit`). `KeyboardInterrupt` is not caught.

## Acceptance criteria
- [ ] `python -m pytest tests/test_workflows_line_check.py -q` passes (the supervisor's tests, extended for every correction above; the symlink test skips where the platform refuses to create a link).
- [ ] `python -m pytest tests/test_workflow_check.py tests/test_conformance_check.py tests/test_text_consistency.py -q` passes.
- [ ] `python -m pytest tests -q` passes in full.
- [ ] `windowless-check.py` and `bridge-check.py --sources` pass.

## Done
Run each from the repository root, in this order, and paste each command with its exit code and the relevant output into your report:
1. `python -m pytest tests/test_workflows_line_check.py -q`
2. `python -m pytest tests/test_workflow_check.py tests/test_conformance_check.py tests/test_text_consistency.py -q`
3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`
4. `python tools/make-manifest.py`, then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
5. `python -m pytest tests -q` (after the manifest, so the install tests see the regenerated one)
6. `git diff --stat`. Expected files: the two programs, the manifest, your report, and possibly `docs/BUILDER_NOTES.md`.

Your report is the file `handoff/TASK-008-r2-report.md`, written as you go, in the form `TASK-008.md`'s Done section describes, with a section headed exactly `Assumed, not verified` (one item per line: what you assumed · why · what would confirm it; or `Assumed, not verified: none`). Your last message is the summary and the report file's path, and nothing follows it.
