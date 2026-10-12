# TASK-002 — round 6 (the Socket CLI must not print part of its key)

Everything else in the floor is accepted: Review A and Review B approved the merged head 0517c5b, and CI ran green on it. **Fix only the Socket step**, in `.github/workflows/tests.yml`.

## What the CI log showed (PR #16, run 38309209568, job "security floor")
- The Socket CLI 1.7.0 prints a banner line before it runs: `CLI: v1.7.0 | cmd: socket ci | org: (not set) | token: <the first 5 characters of the API key>*** (env)`.
- GitHub masks a secret in a log only when the whole value appears, so those 5 characters stay readable. The repository is **public**, so anyone can read them.
- The banner reads `org: (not set)`, although the step's env shows `SOCKET_CLI_ORG_SLUG: latent-foundry`. The scan result still names `"orgSlug": "latent-foundry"`. So it is not proven that `socket ci` in 1.7.0 reads `SOCKET_CLI_ORG_SLUG`; it may be resolving the organization from the token instead.
- `Found 3 files to include in scan` does not name the files.

## The fix
1. Make every `socket ci` call run without the banner: `socket ci --no-banner`. Before you change the file, confirm in the pinned version's own help or bundled source (install `@socketsecurity/cli@1.7.0` globally or into a scratch folder outside the Workspace, then run `socket ci --help` and `socket --help`, or read the package's `dist/` files):
   - that `--no-banner` is accepted by `socket ci` in 1.7.0;
   - that with `--no-banner` no part of the token is printed anywhere else: search the bundled source for where the `token:` text of the banner is built, and for any other place that prints the token or a prefix of it.
   Record the commands, the help text and the source locations (file and line) in your report. **If 1.7.0 has no such flag, or the token is printed elsewhere too, stop and report; do not improvise flags, filters or redirections.** Never filter the step's output (`| grep -v`, `2>/dev/null`, `sed`), which would also hide real failures.
2. Settle whether `socket ci` in 1.7.0 reads `SOCKET_CLI_ORG_SLUG`, from its bundled source: name the file and line where the organization is taken for `socket ci`, and say whether that path reads the environment variable, a flag (`--org` or similar), the CLI's config, or the token's default organization. **Do not change the org handling in this round**; report what you found. The supervisor decides from your report.
3. Keep everything else in the step as it is: the pinned CLI version, the env (`SOCKET_CLI_API_TOKEN: ${{ secrets.SOCKET_SECURITY_API_KEY }}`, `SOCKET_CLI_ORG_SLUG: ${{ vars.SOCKET_ORG_SLUG }}`), no `if:`, no `continue-on-error`, no `|| …` status swallowers.

## The test is supervisor-owned
`tests/test_release_b_ci_floor.py` now has `test_r002_socket_prints_no_banner`, which requires `--no-banner` on every `socket ci` line and fails today. Do not modify the test file. Your change must make all 13 tests pass.

## Scope
- `.github/workflows/tests.yml` (the Socket step only)
- `docs/BUILDER_NOTES.md`
- your report `handoff/TASK-002-r6-report.md`
Nothing else. No secret value anywhere (never run `socket` with a real token; you have none and need none for `--help` or the source), no new dependencies beyond installing the pinned CLI outside the Workspace to read its help, no hard line wraps. Remove whatever you installed outside the Workspace when you are done, and leave no process running.

## Done when
- `python -m pytest tests/test_release_b_ci_floor.py -q` gives 13 passed.
- The full suite passes, and windowless, `bridge-check --sources`, and conformance-check's five floor lines are OK.
- The report records: the `--no-banner` confirmation with its source, the search for other places the token is printed with its result, and the organization finding with file and line.
- End with a one-paragraph summary, the report path, and an `Assumed, not verified` list. The CI run on the pushed head confirms the banner is gone from the log.
