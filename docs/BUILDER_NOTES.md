# Builder notes

2026-10-12 TASK-002-r2: Semgrep CLI 1.176.1 rejects `semgrep scan --dry-run` (suggests `--dryrun`, which is autofix-only); used `semgrep --validate --config …` to confirm rule load counts per the handoff report.

2026-10-12 TASK-002-r3: Push-to-`main` Semgrep uses `--baseline-commit ${{ github.event.before }}` (skip baseline when `before` is the all-zero SHA) so the floor gates only code introduced by the push; PR path still uses `git merge-base`.

2026-10-12 TASK-002-r4: `@socketsecurity/cli@2.1.0` `socket ci` has no `--files` flag (it is ignored); the step runs `socket ci` from the repo root and the CLI scans `.`, picking up `requirements.lock` as a supported manifest.

2026-10-12 TASK-002-r5: Pin `@socketsecurity/cli@1.7.0` (npm `latest`, not deprecated; 2.1.0 is a deprecated bad build). Set `SOCKET_CLI_ORG_SLUG` from `vars.SOCKET_ORG_SLUG` so `socket ci` can resolve the org (404 without it on PR #16).

2026-10-12 TASK-002-r6: Run `socket ci --no-banner` so the CLI compact header does not print the first five characters of `SOCKET_CLI_API_TOKEN` (GitHub masks only whole secrets; the repo is public).

2026-10-16 TASK-006: `tests/test_workflow_check.py::test_r014_registry_heading_missing` replaces the first `## Extension points` in `extension-points.md`, which is the prose citation on the "How this file is read" line, not the heading on its own line, so a heading-line parser still sees the table and exits 0.

2026-10-16 TASK-006-r4: a missing `types/` or `traits/` is skipped with `os.path.lexists` before `is_link`. On both the `os.path.isjunction` branch and the Windows `lstat` fallback, `FileNotFoundError` and `NotADirectoryError` are not links; any other `OSError` is a link. A fence is zero to three leading spaces then three backticks; four spaces is not a fence.

2026-10-16 TASK-006-r5: a `types/` or `traits/` path is examined with `os.lstat` (missing means skip; any other `OSError` is `ERROR` and exit 2). `is_link` uses one `os.lstat` on every Python: `S_ISLNK`, or on Windows `FILE_ATTRIBUTE_REPARSE_POINT`. A fence is a CommonMark opening run of backticks or tildes, closed only by an equal or longer run of the same character with nothing after it but spaces or tabs.

2026-10-16 TASK-006-r6: `cells_of` removes one leading `|` and one trailing `|`, so a row ending or starting `||` keeps its empty cell. File text is split only at `\n` (`file_lines`); a final line feed does not add an empty line. Form feed, vertical tab, and the other `splitlines` breaks stay inside the line.

2026-10-16 TASK-008: Done runs `python -m pytest tests -q` before `python tools/make-manifest.py`, and the install and rollback tests refuse a bridge tree whose edited programs do not match MANIFEST.json, so that ordered run exits 1 until the manifest is regenerated and the suite is run again.

2026-10-17 TASK-008-r2: while `judge_workflows_line` loads `workflow-check.py`, `sys.dont_write_bytecode` is `True` and restored in `finally`. The checker path is `os.path.realpath` of the program file. `field` calls `escape_field` directly; a missing one, or `SystemExit` during or after load, is not-checked. The post-load handler prints through `ascii_text` only.

2026-10-17 BUG-002-r1: after `python tools/make-manifest.py`, `git diff --stat` warns that LF in `bridge/cursor-bridge/VERSION` will be replaced by CRLF the next time Git touches it, but VERSION is not a diff entry and `git diff -- bridge/cursor-bridge/VERSION` is empty.
