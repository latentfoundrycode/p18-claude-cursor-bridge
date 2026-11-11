---
record: brief
header: 1
id: REFAC-004
round: 1
satisfies: [R-042, R-055]
scope: ["bridge/cursor-bridge/review-guard.py", "docs/BUILDER_NOTES.md", "handoff/REFAC-004-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-004: review-guard.py reads the rounds record once when it records a flagged launch, and four dead lines go

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

`bridge/cursor-bridge/review-guard.py` is the guard around the code gate's Review B: `snapshot` before the review, `verify` after it, `premerge` before the merge. This brief carries stage T2's refactoring pass for that file, with two candidates. Behaviour stays exactly the same: the same printed lines, the same exit codes, the same record contents, the same order of reads (where a read was repeated, the repeat goes and nothing else moves).

**Candidate P1, the site:** `record_flagged_launch`, lines 399-427. Where `snap is None` it reads the rounds record twice: an isfile check, a `load_rounds` and a round lookup to decide, then all three again to write. It is reduced to one of each. Today's lines 399-427 read exactly:

```python
    if snap is None:
        rpath = rounds_path(common, id_part)
        if not os.path.isfile(rpath):
            return
        data_pre, _, err_pre = load_rounds(common, id_part, root=None, seed=False)
        if err_pre:
            return
        round_time = None
        for r in data_pre.get("rounds") or []:
            if r.get("round") == rnd:
                round_time = r.get("time")
                break
        if not round_time or not _launch_time_ge_round(launched_at, round_time):
            return
    else:
        snap_taken = (snap.get("taken") or "").rstrip("Z")
        if snap_taken and launched_at.rstrip("Z") < snap_taken:
            return
    rpath = rounds_path(common, id_part)
    if not os.path.isfile(rpath):
        return
    data, _, err = load_rounds(common, id_part, root=None, seed=False)
    if err:
        return
    for r in data.get("rounds") or []:
        if r.get("round") == rnd:
            r["flagged_launch"] = launched_at
            break
    write_rounds(common, id_part, data)
```

**The proposed shape of P1**, which replaces those lines:

```python
    if snap is not None:
        snap_taken = (snap.get("taken") or "").rstrip("Z")
        if snap_taken and launched_at.rstrip("Z") < snap_taken:
            return
    rpath = rounds_path(common, id_part)
    if not os.path.isfile(rpath):
        return
    data, _, err = load_rounds(common, id_part, root=None, seed=False)
    if err:
        return
    entry = next((r for r in data.get("rounds") or [] if r.get("round") == rnd), None)
    if snap is None and not (entry is not None and _launch_time_ge_round(launched_at, entry.get("time"))):
        return
    if entry is not None:
        entry["flagged_launch"] = launched_at
    write_rounds(common, id_part, data)
```

**Candidate P2, the sites:** four dead lines, numbered as the file stands before your edit: the local `import tempfile` at line 654 (in `write_rounds`); `rounds_data = None` at line 1063 and `rpath = None` at line 1064 (in `cmd_verify`); the second `id_part, rnd = parsed` at line 1080 (in `cmd_verify`).

**Callers to update:** none. `record_flagged_launch(common, root, nnn, snap)` keeps its signature, and its six call sites (lines 925, 942, 989, 998, 1047, 1055, all in `cmd_verify`) do not change.

Satisfies: no new requirement. This keeps as they are R-042 (the code gate has a round ceiling held by programs) and R-055 (the minimum set of diagrams is drawn as built and enforced), which D-003 realizes.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/review-guard.py
- docs/BUILDER_NOTES.md
- handoff/REFAC-004-r1-report.md

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/`. In particular, do **not** run `tools/make-manifest.py`
- docs/ and handoff/, except the files the Scope section names. That includes `docs/diagrams/`: this change needs no diagram change (see Diagrams)
- every file under `tests/`: no test file may be edited, renamed or created. This branch already carries the supervisor's tests-lane commits, and you must not touch them
- `bridge/cursor-bridge/MANIFEST.json`: the supervisor regenerates it after your run, not you. `bridge/cursor-bridge/VERSION` also stays as it is
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`: no command changes
- `no_hooks_dir` and the `common` argument around it (lines 105-113): that is recorded as a separate lead, leave it
- every other line of review-guard.py, and these look-alikes above all: `rounds_data = None` at line 809 and `id_part, rnd = parsed` at line 845 (both in `cmd_snapshot`), `id_part, rnd = parsed` at line 394 (in `record_flagged_launch`, above the site), `launched_at, exit_code = launch_info(err_path)` at line 396, the module-level `import tempfile` at line 79, and `_launch_time_ge_round` itself
- every other file under `bridge/`

## Context
**What the code is today** (branch `refactor/T2`, head `9af848a`). The file has CRLF line endings on every line; keep them. These facts were checked against the code for this brief. Confirm the ones the Requirements name before you rely on them.

`_launch_time_ge_round`, lines 364-367, reads exactly:

```python
def _launch_time_ge_round(launched_at, round_time):
    if not launched_at or not round_time:
        return False
    return launched_at.rstrip("Z") >= round_time.rstrip("Z")
```

So it returns False for any empty `round_time` (`None`, `""`, a missing `time`), and `not round_time or not _launch_time_ge_round(...)` means the same as `not _launch_time_ge_round(...)`. `record_flagged_launch` has already returned when `launched_at` is empty (line 397).

**Why the comparison stays first.** The snapshot-time comparison happens only when `snap is not None`, and before any read of the record. A launch before the snapshot must never read the record, because `load_rounds` can raise on a record its `except` does not cover: it catches `(OSError, ValueError)` around `json.load` (lines 641-645), and a record nested deep enough raises `RecursionError`. `tests/test_bug039.py`'s `test_bug039_void_path_*` tests pin this order and the branches of no entry and of an empty time, written by the supervisor on the code as it stood before your edit.

**The cases P1 must keep, one by one:**

| `snap` | Case | Today and after |
|---|---|---|
| `None` | no record file | return, no write |
| `None` | `load_rounds` returns an error | return, no write |
| `None` | no entry matches `rnd` | return, **`write_rounds` does not run** |
| `None` | entry with an empty or missing `time` | return, no write |
| `None` | launch before the entry's `time` | return, no write |
| `None` | launch at or after the entry's `time` | `flagged_launch` set on the entry, `write_rounds` runs |
| given | `taken` set and the launch before it | return **before any read of the record** |
| given | no record file, or `load_rounds` returns an error | return, no write |
| given | no entry matches `rnd` | **`write_rounds` still runs**, with the data as loaded |
| given | an entry matches | `flagged_launch` set on the entry, whatever its `time`, `write_rounds` runs |

Today's write loop takes the first matching round and breaks, and today's decision loop does the same, so `next(...)` over the same generator condition picks the same entry. `_validate_rounds_data` (lines 463-478) has already refused a record whose entries are not objects, so `r.get` behaves as it does today. `entry` is the object inside `data["rounds"]`, so setting its key changes what `write_rounds` writes.

**Why one read gives what two gave.** `load_rounds(common, id_part, root=None, seed=False)` calls `_rounds_tamper` (lines 606-625), whose one side effect is to write the hash copy when none exists. That happens on the first read; today's second read then finds the copy equal. With nothing else writing between the two, the second read returns what the first did.

**P2, the reads.** In `cmd_verify` (lines 914-1098), `rounds_data` and `rpath` are bound at lines 1067-1068 under `if parsed:` and read at lines 1072, 1081, 1082 and 1086; line 1072 is inside that `if parsed:`, and lines 1081-1086 are inside `if parsed and exit_code == 0 and launch_ok:`. `parsed` is bound once, at line 1062. No line of `cmd_verify` before 1063 or after 1086 names `rounds_data` or `rpath`. Between lines 1066 and 1080 neither `id_part` nor `rnd` is rebound, and `parsed` is not rebound. `tempfile` at line 657 resolves to the module-level import at line 79 once the local import goes (line 107 already uses it so); no test replaces the guard's `tempfile`.

**How the tests reach this code.** The six test files below run the Workspace source against git repositories they build under pytest's `tmp_path`; `tests/conftest.py` points `BRIDGE_REVIEW_HASHES` at a temporary folder. Relevant to P1: `test_bug039_site2_negative_a_launch_before_the_snapshot_is_not_voided` (`tests/test_bug039.py`), `test_d003_transition_the_snapshot_rewritten_voids_an_earlier_launch_at_resnapshotted` (`tests/test_d003_review_round_states.py`), which reaches the `snap is None` path through line 925, and `test_bug039_site2_negative_a_tampered_record_admits_no_launch`. Some tests replace `guard.write_rounds` with a failing one; none replaces `guard.load_rounds`.

**The manifest.** `bridge/cursor-bridge/MANIFEST.json` holds a sha256 of `cursor-bridge/review-guard.py`, which no longer matches after your edit. None of the six test files reads the manifest, so they do not fail on it; other test files do, and you do not run those. The supervisor regenerates the manifest after your run.

**The mutants are the supervisor's.** The supervisor re-anchors its mutants to the new lines and re-runs them after your run. You run no mutation, and no mutation script lands in the diff.

**Security context.** The guard is logic and data-access surface: `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). The trust boundaries: the reviewer's run may have changed what the guard reads afterwards, namely the rounds record (`rounds-<ID>.json`, checked against its hash copy), the `.err` file under `run/review/` and the snapshot. This change moves none of these boundaries: the tamper check still runs before the record is used, in `load_rounds`, on every path that reads it.

**Development data** (`docs/INVENTORY.md`, Decisions): the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the installed bridge in the user profile's `.claude` folder, never the one being edited, and installs reach running projects only through the owner's install run sheet. For you this means: the tests run the Workspace source against pytest's temporary folders. Never run `review-guard.py snapshot`, `verify` or `premerge` yourself in this checkout or any real project, since those commands write to the repository's git folder and restore its tree, and never run `bridge-install.py`.

## Diagrams
`docs/diagrams/D-003-review-round-states.md` — state `flagged_gate_integrity`, element `review_guard`. `docs/diagrams/D-002-components.md` — `review_guard` (no new import). D-003 draws the void by the round's recorded time, not the function's shape, so neither diagram changes. The line this change must keep true:

```
reply_arrived --> flagged_gate_integrity : verify GATE-INTEGRITY before restoring (...), nothing restored, no reply, no mark, the launch voided as flagged_launch, the snapshot rewritten voiding by the round's recorded time and reading nothing of the snapshot
```

D-003's table says the same of an older launch: "where the `.err` holds a started line at or after the snapshot's `taken` (at the snapshot-rewritten return, at or after the round's `time`), an older launch or an `.err` with no started line voiding nothing". **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **P1.** Lines 399-427 of `record_flagged_launch` become the proposed shape in the Objective, in that order: the snapshot-time comparison only when `snap is not None` and before any read of the record; then one isfile check, one `load_rounds` returning on its error as now, one lookup; then the `snap is None` return; then the assignment under `if entry is not None:`; then `write_rounds`.
2. **The `not round_time` test.** Verify in `_launch_time_ge_round` that it returns False for an empty time before relying on it. If that does not hold, keep the test in the `snap is None` return and say so in the report.
3. **`write_rounds`.** It still runs when no entry matches and a snapshot was given, and it still does not run when no entry matches and `snap` is `None`.
4. **P2, the local import.** Remove `import tempfile` at line 654, inside `write_rounds`.
5. **P2, the two initial values.** Remove `rounds_data = None` and `rpath = None` at lines 1063-1064, if your check confirms they are read only under `if parsed` and no path reads them unbound. If one path does, leave them and say so in the report.
6. **P2, the second unpacking.** Remove `id_part, rnd = parsed` at line 1080, if your check confirms neither name is rebound between lines 1066 and 1080. If one is, leave the line and say so in the report.
7. No other line of review-guard.py changes. The file keeps its CRLF line endings and gains no trailing whitespace.

## Acceptance criteria
- [ ] Behaviour is identical: the same printed lines, the same exit codes, the same record contents, the same order of reads, for every case in the Context table.
- [ ] The six test files pass before and after the edit with the **same** test set (the same count passed, none failed or newly skipped; both counts in the report), none edited. The whole suite is not yours to run: the supervisor runs it after your run.
- [ ] `python bridge/cursor-bridge/review-guard.py` with no arguments prints the same usage text and exits 2, before and after the edit.
- [ ] Inside `record_flagged_launch`, `load_rounds` and `os.path.isfile` each appear exactly once, and `data_pre`, `err_pre` and `round_time` are gone from it.
- [ ] The dead code is gone: `import tempfile` appears once in the file (line 79); `rpath = None` does not appear; `rounds_data = None` appears once (in `cmd_snapshot`); `id_part, rnd = parsed` appears three times (in `record_flagged_launch`, in `cmd_snapshot`, and once in `cmd_verify`). A line you left under Requirement 5 or 6 is named in the report instead.
- [ ] No public signature changed; the six call sites of `record_flagged_launch` are unchanged.
- [ ] `git diff --stat` shows `bridge/cursor-bridge/review-guard.py` as the only product file changed, 17 lines shorter on the proposed shape (13 from P1, 4 from P2). A line you kept under Requirement 2, 5 or 6 changes that count; say which.
- [ ] No test file changed; `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/VERSION` unchanged; no entry in `docs/CHANGES.md` or `bridge/cursor-bridge/CHANGELOG.md`; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way — an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason — append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python — `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change launches no process and must not add one.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in):
  - Before the edit, and again after it: `python -m pytest -q -p no:cacheprovider tests/test_bug039.py tests/test_bug041.py tests/test_d003_review_round_states.py tests/test_review_guard.py tests/test_review_guard_ceiling.py tests/test_bug036.py`
  - Before the edit, and again after it: `python bridge/cursor-bridge/review-guard.py` (no arguments: it prints its usage and exits 2, touching nothing)
  - At the end: `git status` and `git diff --stat`, both pasted into the report.
  - Do not run the whole suite or any other test file. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task: it re-anchors and re-runs its mutants after your run. Write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way; report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: no helper function, and no new name beyond `entry`.

## Done
Your report is the file `handoff/REFAC-004-r1-report.md`, which you write as you go — what you did, what you changed, what you ran and what it printed, what you could not do — so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the before and after outputs of the pytest command, with both counts, and of the no-argument run;
- `git status` and `git diff --stat`;
- what you found for each check the Requirements name: `_launch_time_ge_round` on an empty time; `rounds_data` and `rpath` read only under `if parsed`; `id_part` and `rnd` not rebound between lines 1066 and 1080; and any line you kept because of them;
- one sentence stating why the behaviour is identical;
- a line saying that `bridge/cursor-bridge/MANIFEST.json` is now stale for `cursor-bridge/review-guard.py`, for the supervisor to regenerate;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm — the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
