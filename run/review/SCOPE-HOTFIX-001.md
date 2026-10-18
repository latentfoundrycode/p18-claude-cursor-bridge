# SCOPE — HOTFIX-001 (hotfix 2026.10.18a)

The diff at `run/review/REVIEW-HOTFIX-001.diff` is the whole hotfix against the release state of 2026.10.11d (commit 64ad75a, the base branch `release/2026.10.11`), the `run/review/` records left out. It has two parts.

## 1. The governance text (the supervisor's, already criticised)

`bridge/commands/supervisor.md` (the digest's rule 6, Phase 2's two-critic loop, the launcher's ceiling, the owner's line, Phase 4, the change cycle's steps 2 and 4, the run parameters' optional lines, step 3b's exception, step 8's convergence, standing rule 6), `bridge/cursor-bridge/Merge-Verification-Policy.md`, `bridge/agents/plan-critic.md`, `bridge/cursor-bridge/Known-Pitfalls.md` (KP-062) and `bridge/cursor-bridge/CHANGELOG.md` (2026.10.18a). These were criticised by plan-critic and Review B's design mode for four rounds and a confirming read under the rule they set; a finding on them is in scope only where the text contradicts the program or itself, or cannot be met as written.

## 2. The program (the builder's, HOTFIX-001)

The brief `handoff/HOTFIX-001.md`, quoted:

> **Scope.** Files you may create or modify: `bridge/cursor-bridge/bridge-run.py`; `handoff/HOTFIX-001-r1-report.md`; `handoff/HOTFIX-001-r2-report.md` (round 2). Do not modify anything else. In `bridge-run.py`, the only docstring change allowed is one added line in the module docstring that names the new refusal.
>
> **Out of scope.** `.env` and `secrets/`; CI configuration (`.github/`); `docs/` and `handoff/` except the files the Scope names; `tests/`, all of it; `MANIFEST.json` and `VERSION` (the supervisor restamps them); every text file; every other program under `bridge/cursor-bridge/`; `run/` and `.git/`.

Its last section, "Round 2: corrections from Review A", replaces or extends points of its Requirements.

## The tests the supervisor wrote

`tests/test_bridge_run_design_ceiling.py`, 69 tests, enforcing supervisor.md Phase 2, "The launcher holds the ceiling" and "The owner's line" (KP-062): rounds 1 to 5 and R1 allowed; above five and R2 or later refused; a name that cannot be read refused; separators, dot segments, case of the folders, absolute paths, trailing punctuation and several names; the owner's line lifting one subject once, in its Markdown forms; the refusal's message; exit 125 before the started line, nothing logged.

## Expected bookkeeping and records in the diff

`handoff/HOTFIX-001.md` (the brief), `handoff/HOTFIX-001-r1-report.md` and `-r2-report.md` (the builder's reports), `bridge/cursor-bridge/VERSION` and `MANIFEST.json` (restamped 2026.10.18a by `tools/make-manifest.py`).

## Decided and recorded, not this review's findings

- Review A round 2's crash path: `int()` on a round or an owner's `<rounds>` of more than 4,300 digits raises out of `design_ceiling` (exit 1, a traceback, nothing started). Recorded for hardening: it fails closed and defeats no safety mechanism.
- `re.I` on the whole owner's-line pattern: harmless, a capitalised subject still lifts nothing. Recorded for hardening.
- Accepted limits of a name check: `x/..` segments, 8.3 short names, a prompt naming the file in other words or through another file, relaunching an allowed file, a supervisor starting `cursor-agent` without the launcher (the text says the floor is the launcher's and that breaks rule 8).
