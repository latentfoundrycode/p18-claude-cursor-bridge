---
record: brief
header: 1
id: "HOTFIX-004"
round: 1
satisfies: []
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/mutation-run.py", "tests/test_hotfix24a_heavy_slots.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/HOTFIX-004-r1-report.md"]
merge_unit: null
blocking_class: null
---
# HOTFIX-004: hotfix 2026.11.24a, the heavy slots

## Objective
This increment builds hotfix 2026.11.24a of the bridge: the installed release 2026.11.23a plus one feature, the number of machine-wide heavy slots as a setting. Today `bridge/cursor-bridge/bridge-run.py` lets exactly one heavy run (kind `builder`, `driver` or `test`) hold `~/.cursor-bridge/heavy.lock` at a time; every other heavy launch waits. After this change the owner can set 1 to 4 slots with `bridge-run.py --heavy-slots <n>` (stored in `~/.cursor-bridge/heavy-slots.json`); with no setting, or a malformed one, the launcher behaves byte for byte as 2026.11.23a. Beside the slots, three guards come with it: one heavy run per checkout (a byte lock on `~/.cursor-bridge/heavy-folder-<sha256 hex>.lock` taken before any slot), unique run ids (the pid file `run/launcher/pids/<run id>` created exclusively at launch), and a per-run-id lock in `mutation-run.py` so two runs of one mutants file cannot share a scratch folder. The behaviour is fixed by the supervisor's design, `run/supervisor/hotfix-004-design.md` (final after three critique rounds); read it whole before you start. Its section "The behaviour" is restated below as numbered requirements, with its exact lines, line formats and exits; where this brief and the design seem to disagree, stop and report it rather than choose.

Satisfies: there is no build-plan increment and no requirements register row for this work. The supervisor defined the increment under the owner's two decisions of 2026-11-24, given in question form and quoted from the design's first section, "The owner's words": (1) "Should I add a small increment ... that makes the number of heavy-job slots ... a setting, defaulting to one and set to two here?" answered "Add it, set to 2 (Recommended)"; (2) "The extra heavy-job slot only helps this release if it ships as a hotfix you install mid-release ... How should I deliver it?" answered "Hotfix now (Recommended)": hotfix 2026.11.24a = the installed 2026.11.23a plus only the slot setting, the full review gate, then the owner's run sheet (install, app restart, /calibrate-bridge). The trace is the supervisor's acceptance test file `tests/test_hotfix24a_heavy_slots.py` (31 cases, red on the checkpoint); each test's docstring names the design line it enforces. Do not add a test.

## Scope
Files you may create or modify, each only as the paragraph after the list allows:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/mutation-run.py
- tests/test_hotfix24a_heavy_slots.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/HOTFIX-004-r1-report.md

What each entry allows, exactly: `bridge-run.py` and `mutation-run.py` are the two programs you change. `tests/test_hotfix24a_heavy_slots.py` is listed so the scope check reads it; it is the supervisor's acceptance test: read it and run it, never edit it. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (checked with `python tools/dump-cli.py --check`); never edit them by hand. `docs/BUILDER_NOTES.md` takes one or more dated lines appended at its end, nothing else in it changes. `handoff/HOTFIX-004-r1-report.md` is your report, a new file. Do not modify anything else.

## Out of scope
- `.env` and anything under `secrets/`.
- CI configuration (`.github/`).
- `docs/` and `handoff/`, except the files the Scope section names.
- `bridge/cursor-bridge/MANIFEST.json`, `bridge/cursor-bridge/VERSION` and `bridge/cursor-bridge/CHANGELOG.md`: the supervisor stamps 2026.11.24a after your run. Do not run `tools/make-manifest.py`.
- Every other file under `bridge/`: `bridge_env.py`, `bridge-stop.py`, `bridge-install.py`, `loop-guard.py`, `Glossary.md`, `supervisor.md`, the loop's texts (`delegation-loop.md`, `run-parameters.md`) and every other program stay exactly as they are. The design's section "The loop's text" decides that the sentences that say one slot stay in this hotfix; the supervisor's change log names them.
- Every other test file, `tests/conftest.py` included. A failure in another test file is reported by its test id, never fixed in that file.
- `tools/`, all of it (you only run `tools/dump-cli.py`).
- `run/`, which holds the supervisor's records (read `run/supervisor/hotfix-004-design.md`, write nothing there), and `.git/`.
- Never run `bridge-run.py`, `mutation-run.py` or `bridge-install.py` against the real home folder (`~/.cursor-bridge`, `~/.claude`), this repository's real run record (`run/launcher/`), or the real `cursor-agent`. The tests below run them only under pytest's temporary folders with a temporary home.

## Context
**Where you are.** This checkout is the bridge's own source repository (not a supervised product), on branch `hotfix-004`, cut from `release/2026.11.23a` (main at `669d3b4`, whose `bridge/` is the installed 2026.11.23a). The hotfix's pull request targets `release/2026.11.23a`.

**Development data:** the inventory's decision (`docs/INVENTORY.md`, Resources) reads: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (section 15 condition 1, A1a condition 1)". For this increment: you run only the commands under Constraints. The acceptance tests give every launch a temporary home through `HOME` and `USERPROFILE` (so `~/.cursor-bridge` is a temporary folder), launch from folders under pytest's `tmp_path`, and run plain Python commands under `BRIDGE_RUN_ALLOW_ANY=1`; `tests/conftest.py` sets `HOME` and `USERPROFILE` to a temporary folder for every test in-process too.

**The design.** `run/supervisor/hotfix-004-design.md`: "The behaviour" (the setting, the slots, the mutation engine, unchanged), "Known limits" (recorded, not built: do not build them) and "Tests". The requirements below quote it.

**The acceptance test's harness** (`tests/test_hotfix24a_heavy_slots.py`, read it whole). `env` sets `BRIDGE_RUN_SLOT_SCALE=0.01` (the report every 0.6 s, a holder's grace 1.2 s, a test kind's floor 18 s); some tests set `0.001`. A launch holds its slot with a Python command that waits for a release file the test writes. `start_slot_holder` is a helper process that loads `bridge-run.py` as a module and uses its own names: `br.heavy_state_paths()[0]` (to find the state folder), `br._try_lock_byte(fd)` on `os.open(lock_path, os.O_RDWR | os.O_CREAT)`, `br.publish_holder_record(lock_path + ".holder", {...})` and `br.process_creation_epoch(pid)`, with records `{"kind": "test", "run_id": <fixed id>, "pid": ..., "created": ..., "start": <now>, "limit": <int>}` on `heavy.lock` or `heavy-2.lock`. Those four names keep their signatures and meaning. The mutation test's helper (`LOCK_HELPER_SRC`) holds `<scratch>/.mutation-run-lockt.lock` with `msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)` on Windows and `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)` (plus `fcntl.lockf`) elsewhere.

**bridge-run.py as it is (line numbers on this branch).**

- `heavy_state_paths` (lines 1553 to 1557), quoted exactly; it keeps this two-item answer for slot 1 (called by `tests/test_bridge_run_slot.py`, `tests/test_task032_supervisor_launcher.py`, `tests/test_bug029_agent_name.py` and the acceptance test):
```python
def heavy_state_paths(env=None):
    """`(~/.cursor-bridge/heavy.lock, ~/.cursor-bridge/heavy.lock.holder)` from the launcher's environment."""
    home = bridge_env.real_home(env or os.environ)
    folder = os.path.join(home, ".cursor-bridge")
    return os.path.join(folder, "heavy.lock"), os.path.join(folder, "heavy.lock.holder")
```
- `_try_lock_byte(fd)` (lines 1788 to 1804), the byte lock every slot, the folder lock and the mutation engine's lock use, quoted exactly:
```python
def _try_lock_byte(fd):
    if sys.platform == "win32":
        import errno
        import msvcrt
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return True
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EDEADLOCK):
                return False
            raise
    import fcntl
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False
```
`_unlock_byte(fd)` (lines 1807 to 1819) is its release. `msvcrt.locking` locks from the file's current position: the lock files are never written, so the position stays 0.
- `read_holder_record(holder_path)` (lines 1676 to 1734): the hardened opener the setting's reading reuses. Its open: `flags = (os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0))`, then `os.fstat` and `stat.S_ISREG`, `os.read(fd, 4097)` refused when over 4096 bytes, `.decode("utf-8")`, `json.loads`, catching `(OSError, ValueError, RecursionError, MemoryError, OverflowError)`. Then the strict record validation (kind in `KINDS`, `RUN_ID_RE`, start, pid, limit, created, and the process alive with that creation time). `bridge_env.is_link(path)` (bridge_env.py lines 82 to 87) is the link check: `os.lstat` plus `os.path.islink` or a reparse tag.
- `holder_end_time(record, grace)` (1737), `publish_holder_record(holder_path, record)` (1749; it writes a temporary `.heavy.holder.*.tmp` in the folder, then `os.replace`), `_waiting_line(record, grace)` (1822) and `_slot_not_free_line(record, grace)` (1832). Today's lines, exactly: `bridge-run: waiting for the slot held by unknown`, `bridge-run: waiting for the slot held by %s %s since %s, ends by %s` (kind, run id, start, end), `bridge-run: slot not free - held by unknown`, `bridge-run: slot not free - held by %s %s since %s, ends by %s`. `holder_end_time` adds `int(grace)` whole seconds to start + limit.
- `_open_heavy_lock(lock_path, state_dir)` (1842) and `acquire_heavy_slot(kind, run_id, limit, scale)` (1856 to 1926). Today: it opens `heavy.lock` (an `OSError` prints `bridge-run: refused - ~/.cursor-bridge/heavy.lock (<exception class name>)` and returns `"refused"`); per pass it tries the byte lock; on success it publishes the holder record `{"kind", "run_id", "pid", "created", "start": <taken>, "limit": max(1, int(limit))}` and then writes `bridge-run: slot taken <taken>` and returns `(lock_fd, waited_seconds)`; otherwise it reads the record, fixes the bound once from the first live record (`bound_wall = min(provisional_wall, max(own_floor_wall, start + limit + grace))`, `provisional_wall = wait_wall + (SLOT_BUILDER_CAP + SLOT_GRACE) * scale`, `own_floor_wall = wait_wall + KINDS[kind] * scale`), past the deadline writes the not-free line built from the last live record seen and `bridge-run: exit 123` and returns `None`, else writes a waiting line at the first pass and every `SLOT_REPORT * scale` seconds, and sleeps 1 s. Two tests call it in-process with four positional arguments: `tests/test_bridge_run_slot.py:251` (`br.acquire_heavy_slot("test", "2026-01-01T00:00:00Z", 5, 0.001)`, expects `None`) and `tests/test_bug029_agent_name.py:126` (`br.acquire_heavy_slot("test", "2026-10-26T12:00:00Z", 60, 1.0)`, expects a tuple, then calls `br._unlock_byte(result[0])` and `os.close(result[0])`, and checks the holder record at `heavy_state_paths()[1]` names the run when the `slot taken` line is written). Keep that call form and those return shapes working.
- `write_pid_file(folder, run_id, pid, child_pid)` (1530 to 1542) writes `run/launcher/pids/<run id with ":" replaced by "-">` holding `"%d %d\n" % (pid, child_pid)`, only where `<folder>/run` is a folder, returning the path or `None` (an `OSError` returns `None`, never a refusal); `remove_pid_file(path)` (1545). The watch path writes the launcher's own pid twice: `write_pid_file(folder, run_id, os.getpid(), os.getpid())` (line 2957).
- `workspace_of(argv, folder)` (1944): a cursor-agent run's `--workspace <path>` or `--workspace=<path>` joined to the launch folder, else the launch folder. `_git_rev_parse_path(folder, *args)` (2460) runs `git -C <folder> rev-parse <args>` windowless with `bridge_env.GIT_TIMEOUT` (30 s) and returns an absolute normalised path or `None` on a failure, a timeout or an empty answer.
- `main()` (2684): `--healthy` first; then `if "--limit" not in argv or "--" not in argv: return usage()` (exit 2). The run id (lines 2801 to 2806), quoted exactly:
```python
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    taken = [r.get("id") for r in read_log(folder)]
    n = 2
    while run_id in taken:                                 # two runs in one second: the second gets a suffix
        run_id = run_id.split("Z")[0] + "Z-%d" % n
        n += 1
```
After it come refusals that exit 125 (key file, cap, review-only, watch-only), then the first stderr line `bridge-run: started <run id>` (line 2832), the `NOTES` lines `bridge-run: note - <note>` and the scale note (2833 to 2837), more 125 exits (`AgentHomeError`, line 2850; key file, 2856; driver, 2897), the slot (2901 to 2911: `"refused"` returns 125; `None` writes the row with `slot="not free"` and returns 123), then 125 exits after the slot (brief changed, 2924; driver, 2937; cannot start, 2976, 2989, 3057, 3071), the child's start and `write_pid_file(folder, run_id, os.getpid(), proc.pid)` (3083), `remove_pid_file(pid_file)` (3106), and the row `write_log(folder, entry)` (3116). The row `entry` is built at line 2861.
- The module docstring (lines 2 to 100) is the source of `bridge-run.py`'s entry in `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` (`tools/dump-cli.py` uses a program's module docstring where it has no top-level `build_parser()`). Its heavy-runs bullet (lines 81 to 88) says one machine-wide slot on `heavy.lock`. `usage()` (line 152) is an existing printed line and stays byte-identical.

**mutation-run.py as it is.** `main(argv=None)` (line 1493) validates, gets `run_id = mutants_file_ok(workspace, args.mutants_file)` (the `<id>` of `run/supervisor/<id>-mutants.json`), then (lines 1513 to 1523): `scratch_base = args.scratch if args.scratch else default_scratch(workspace, os.environ)`; `scratch_base, work_sub = validate_scratch(scratch_base, workspace, run_id)` (`work_sub` is `<scratch base>/mutation-run-<run_id>`); `os.makedirs(scratch_base, exist_ok=True)`; `if os.path.isdir(work_sub): shutil.rmtree(work_sub, ignore_errors=True)`; `os.makedirs(work_sub, exist_ok=True)`; the copy root; `cache_path = os.path.join(workspace, "run", "supervisor", "mutation-cache", run_id + ".jsonl")`; `validate_cache_file`; `read_cache`. `run_main()` (1744) turns a raised `Refuse(msg)` into `print(msg, file=sys.stderr)` and exit 2. `bridge_env` is imported at the top (line 41; `None` with an import error, which `run_main` reports as exit 3). The module docstring and `build_parser()`'s description are the source of its reference entry.

**Security context.** The project's ASVS level is 2 (`docs/INVENTORY.md`). Trust boundaries this change touches: the launcher's command line (`--heavy-slots <n>`); the files under `~/.cursor-bridge` (the setting, every lock and holder file), which any process of the user can write, a builder included (a Known limit: the cap of 4 bounds it and the `(slot <k> of <n>)` suffix shows it); the answer of `git rev-parse --show-toplevel` for the launch folder; the scratch base of `mutation-run.py`. Every file under `~/.cursor-bridge` is read through the hardened opener (no link followed, a regular file only, bounded size) and every record is validated strictly. `.cursor/rules/secure-coding.mdc` is in force. No secret, key or token is involved; do not read any.

**Rules already in force:** `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc`, and the frozen minimal-code rule (`bridge/cursor-bridge/minimal-code.snapshot.md`).

## Diagrams
None. This repository has no normative diagrams for this work, and the increment is not in `docs/BUILD_PLAN.md`.

## Requirements
In each requirement, `<time>` and `<start>` and `<end>` are UTC stamps of the form `YYYY-MM-DDTHH:MM:SSZ`; "byte-identical" means the same characters as 2026.11.23a writes today.

**The setting (`~/.cursor-bridge/heavy-slots.json`).**

1. The setting is the file `heavy-slots.json` in the state folder (`os.path.dirname(heavy_state_paths()[0])`), "holding exactly `{"slots": <n>}`, n a JSON integer 1 to 4 (a bool, a float such as `2.0`, a string, extra keys or a byte-order mark are not that)". JSON whitespace around the object is allowed; the parsed value is a dict whose only key is `"slots"` and whose value has `type(...) is int` with 1 <= n <= 4. Absent (no file at the path): 1 slot, "as 2026.11.23a, no line printed".
2. It is "read at each heavy launch (no cache)", once per launch, "through the same hardened reading as the holder record (`read_holder_record`'s opener, plus a link check with `bridge_env.is_link` before the open, since that opener has no `O_NOFOLLOW` on Windows): no link followed, a regular file only, non-blocking, at most 4096 bytes, `RecursionError`, `MemoryError` and decoding errors caught". Only heavy launches (builder, driver, test) read it; review and watch launches do not.
3. Anything other than the exact form gives 1 slot and exactly one note line, `bridge-run: note - heavy-slots.json ignored (<cause>); one heavy slot`, "printed after `bridge-run: started <run id>` with the launch's other notes, never before it, never a refusal". The test reads the prefix `bridge-run: note - heavy-slots.json ignored (` and the suffix `); one heavy slot`, wants exactly one such line per launch, at an index above 0, and the first stderr line starting `bridge-run: started `. `<cause>` is yours: short, ASCII, on one line; the line ends with the exact suffix. The cases the test feeds, each a malformed setting: `not json`, `{"slots": 0}`, `{"slots": 5}`, `{"slots": true}`, `{"slots": "2"}`, `{"slots": 2.0}`, `{"slots": 2, "x": 1}`, the bytes `EF BB BF` before `{"slots": 2}`, `[2]`, an empty file, `{"slots": 2}` followed by 5000 spaces, and a folder at the path. With no file, no stderr line contains `heavy-slots`.

**The option `--heavy-slots <n>`.**

4. `bridge-run.py --heavy-slots <n>` with n 1 to 4 "writes the file atomically (a temporary file in the same folder, then replace), prints `bridge-run: heavy slots set to <n>`, exit 0, starts no command and writes no run row". It creates the state folder where it is absent. The file then reads back with `json.load` as `{"slots": <n>}`, and the state folder holds nothing it did not hold before except `heavy-slots.json` (the test wants `sorted(os.listdir(<state folder>)) == ["heavy-slots.json"]` after the first write into an empty home: no temporary file left, no lock file made). The test reads `bridge-run: heavy slots set to 2` as a whole line of stdout plus stderr, and wants neither `started` nor `slot taken` in stderr.
5. "Out of range or not an integer: exit 125 naming the range, the file unchanged." The value is parsed with `int()`; `0`, `5` and `x` are refused. The refusal line begins `bridge-run: refused - ` and names the range as `1 to 4` (the test's check is `re.search(r"1\D{1,8}4", stderr)`). The existing file's bytes are unchanged, no other file appears in the state folder, `started` is not in stderr, no row is written.
6. "Given with a command (`--`) or any other option: exit 125, nothing written." `--heavy-slots` counts when it is among the launcher's own words (the words before the first `--`, or every word when there is no `--`); the only accepted form is the whole argument list `--heavy-slots <n>`. The test runs `--heavy-slots 2 -- <python> -c "open(<marker>,'w').write('x')"` and `--heavy-slots 2 --kind test`: each exits 125, no `heavy-slots.json` exists after, the state folder is absent or empty, the command never ran, `started` is not in stderr, no row. This check comes before today's `--limit`/`--` usage check, so these forms never reach `usage()`.

**The slots.**

7. "Slot 1 keeps today's files, `~/.cursor-bridge/heavy.lock` and `heavy.lock.holder`; `heavy_state_paths(env)` keeps its two-item answer for slot 1, and a new function gives slot k's. Slot k (2..n) uses `heavy-<k>.lock` and `heavy-<k>.lock.holder`, opened, locked and published exactly as slot 1 (same byte lock, same holder record, same strict validation)."
8. "All n lock files are opened before the first pass, so a broken `heavy-2.lock` refuses the launch even while slot 1 is free." "An open or lock error on any slot's lock file refuses the launch with exit 125 and the line `bridge-run: refused - ~/.cursor-bridge/<that file> (<error class>)`, as today for slot 1." The test makes `heavy-2.lock` a folder with `{"slots": 2}` and slot 1 free, and wants exit 125, a line matching `^bridge-run: refused - ~/\.cursor-bridge/heavy-2\.lock \([^)]+\)$`, no `Traceback` in stderr, the command never started and no pid file left under `run/launcher/pids`.
9. "On each pass the launch tries slots 1..n in order and takes the first it can lock. With n > 1, `bridge-run: slot taken <time>Z` gains ` (slot <k> of <n>)`; with n = 1 (no setting, a malformed one, or `{"slots": 1}`) the line is byte-identical to today's." The test's forms: with n = 1 the whole line matches `bridge-run: slot taken \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ`; with n = 2 it is that followed by exactly ` (slot 1 of 2)` or ` (slot 2 of 2)`. The holder record is published before the `slot taken` line, as today.
10. Waiting with n > 1: "the waiting line is `bridge-run: waiting for a slot (<n> of <n> held): <clause>; <clause>` with one clause per slot in slot order, `<kind> <run id> since <start>, ends by <end>` for a live record and `unknown` for a held slot with no readable live record". `<end>` is `holder_end_time(record, grace)`. The test's form for two holders, test kind: `bridge-run: waiting for a slot \(2 of 2 held\): test <rid1> since <time>, ends by <time>; test <rid2> since <time>, ends by <time>`. Waiting lines come at the first pass and every report interval, as today.
11. The bound with n > 1: "The wait's bound is fixed once, on the first pass that reads any live record, as the earliest end among the live slot records (each start + limit + grace), floored at the waiter's own kind's limit and capped at the builder cap plus grace, as today for one; never recomputed." "At the bound: `bridge-run: slot not free - held by <the live holder with the earliest end> ...` in today's format, then exit 123" (`bridge-run: exit 123` the last line, the row with `"slot": "not free"` as today). Where no live record was read, today's `bridge-run: slot not free - held by unknown`. The test holds slot 1 (limit 600) and slot 2 (limit 2) at scale 0.001 and wants exit 123 within 9 s and the second-to-last line `bridge-run: slot not free - held by test 2026-09-01T02:00:00Z since <time>, ends by <time>`.
12. With n = 1, "every waiting line and the exit-123 lines are byte-identical to today's", and the whole of a one-slot launch's stderr is today's (the test with no setting wants `bridge-run: waiting for the slot held by test <first run id> since <time>, ends by <time>` and a last line `bridge-run: exit 0`).

**One heavy run per checkout.**

13. "Before it tries any slot, a heavy launch takes an exclusive byte lock on `~/.cursor-bridge/heavy-folder-<h>.lock`, `<h>` the SHA-256 (hex) of its checkout's identity: the folder the run works in (`workspace_of(argv, launch folder)`: a builder's `--workspace`, else the launch folder), raised to `git rev-parse --show-toplevel` of that folder where git answers (else the folder itself), resolved with `realpath`, case-folded on Windows." `<h>` is 64 lowercase hex characters (the test wants exactly one name in the state folder matching `heavy-folder-[0-9a-f]{64}\.lock` after one run). "Where `git rev-parse` fails, times out or answers no folder, the identity is the folder itself." A launch from a subfolder of a repository and one from its top folder get the same `<h>`.
14. "The lock is an OS byte lock, taken atomically, so two launches from one checkout started together cannot both pass it, a holder that publishes no record still holds it, and a killed run frees it; the file holds no path." It uses `_try_lock_byte`, as the slots do. "It holds the folder lock until it ends, as it holds its slot." Wherever today's code releases the slot before an exit (`_unlock_byte` and `os.close` at lines 2919, 2932, 2978, 2991, 3059, 3073), the folder lock is released too.
15. "An open or lock error on the folder lock file refuses with exit 125 and `bridge-run: refused - ~/.cursor-bridge/heavy-folder-<h>.lock (<error class>)`." The test replaces the lock file with a folder and wants exit 125, a line matching `^bridge-run: refused - ~/\.cursor-bridge/heavy-folder-<the 64 hex>\.lock \([^)]+\)$`, no `Traceback`, the command never started.
16. "Beside it the launcher publishes `heavy-folder-<h>.lock.holder` once, when it takes its slot, holding the same record as its slot's (kind, run id, pid, created, start = the slot-taken time, limit), under the same strict validation; until then the folder lock is held with no published record, and a waiter on it waits as today's waiter waits before a holder's record is published (`test_r040_wait_before_record_published`), its bound unfixed until a live record is read, capped at the builder cap plus grace." "The slot's holder record is unchanged (no `folder` field)."
17. "A launch waiting for the folder lock waits exactly as for a busy slot: its waiting line names the folder lock's holder (with n = 1 the line is today's line, that holder being the same run as the slot's), and its bound is that holder's end (same floor and cap)." The waiting line for the folder lock is always today's one-slot form, whatever n is: `bridge-run: waiting for the slot held by unknown` while no live folder record is read, then `bridge-run: waiting for the slot held by <kind> <run id> since <start>, ends by <end>`. The test with two slots wants, from a same-checkout waiter, `bridge-run: waiting for the slot held by test <first run id> since <time>, ends by <time>`; and, where the same-checkout holder H first waited for a slot itself, the waiter's first line exactly `bridge-run: waiting for the slot held by unknown`, then a line naming H whose `since` equals the time on H's `slot taken` line and whose `ends by` is 31 s later (H's limit 30 plus the scaled grace 1.2 taken as 1 whole second). While a same-checkout launch waits on the folder lock it holds no slot, so another folder's launch takes the free slot at once.
18. "The single deadline covers both waits: fixed once, on the first pass of either wait that reads a live record. At the bound the exit-123 line names the holder of the wait the launch is in when the bound passes: the folder lock's holder while it waits for the folder, else the live slot holder with the earliest end." The test holds slot 1 from another folder (limit 2) and slot 2 by a same-checkout launch (limit 600) at scale 0.001, and wants the waiter's exit 123 within 25 s with the second-to-last line `bridge-run: slot not free - held by test <the same-checkout run id> since <time>, ends by <time>`.
19. Review and watch launches take no folder lock and no slot, as today.

**Run ids and pid files.**

20. "The run id keeps today's form: the launch second, with today's `-<n>` suffix where taken. Where a project's `run/` folder exists, the id is made unique by creating its pid file `run/launcher/pids/<run id>` exclusively at launch (the next `-<n>` where it exists), holding the launcher's own pid twice while it waits, as the watch path writes it; the child's start rewrites it as today." The run-log check of today's code stays; the exclusive creation is added to it. The test starts two launches from one folder in one second and wants distinct ids, each matching `\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ(-[2-9]|-[1-9]\d+)?`, the later one equal to the earlier plus `-2` where their first 20 characters agree, both pid files (named with `:` replaced by `-`) present while one runs and one waits, and one row per id.
21. "Every exit before the child starts (each refusal with 125, an exit 123, a refused slot) removes it, so a refused launch leaves no pid file." That covers every return between the run id's choice and the child's start, listed under Context. The test wants no pid file after a launch refused with 125 at its slots (`heavy-3.lock` a folder, `{"slots": 3}`) and after one that ended with 123. "`bridge-stop.py <id>` on a waiting launch ends the waiter" (bridge-stop.py itself is unchanged). "Where no `run/` folder exists no pid file is written and no uniqueness is claimed, as today."

**The run row.**

22. "A heavy run's row gains `"slot": <k>`; `"slot": "not free"` stays as today." With no setting a lone heavy run's row has `"slot": 1`; with two slots each row's `slot` matches the slot its `slot taken` line names. "Every reader of `slot` compares with `"not free"` only (roster-check.py:153, pace-report.py:349, 450, 490, 655, scope-check.py:199), so an integer is read as today." Do not touch those readers.

**The mutation engine.**

23. "`mutation-run.py` takes an exclusive byte lock on `<scratch base>/.mutation-run-<run_id>.lock` (the same run id that names its `mutation-run-<run_id>` folder and its cache file), opened without following a link, before it removes or writes anything; a second run of the same run id ends at once with exit 2 and `mutation-run: refused - this mutants file is already running (<run id>); wait for it to end`, writing nothing. Runs of different ids share the base folder freely. The lock is released at exit (an OS byte lock, so a killed run frees it)." The lock primitive is exactly `_try_lock_byte`'s (Context; `bridge_env.py` is out of scope, so the primitive lives in `mutation-run.py`). The lock is held until the run ends and is taken before the existing `shutil.rmtree(work_sub, ...)`, `os.makedirs(work_sub, ...)` and any cache read or write. The test holds the lock from another process and wants: exit 2; the line, for run id `lockt`, `mutation-run: refused - this mutants file is already running (lockt); wait for it to end` as a whole line of stdout plus stderr; the scratch base's tree unchanged (every name, size and `st_mtime_ns`); no `run/supervisor/mutation-cache/lockt.jsonl`; the refusal within 30 s; a run of run id `othert` with the same base not refused; and, after the holder ends, a run of `lockt` not refused.

**The docstring and the reference.**

24. `bridge-run.py`'s module docstring states the behaviour as built: its usage block gains the form `python ~/.claude/cursor-bridge/bridge-run.py --heavy-slots <n>`, and its heavy-runs bullet says that the number of slots is the setting (1 by default, 1 to 4 by `--heavy-slots <n>`, slot k on `heavy-<k>.lock`), that one checkout holds at most one heavy run (`heavy-folder-<h>.lock`), and that with more than one slot the `slot taken` line carries ` (slot <k> of <n>)`. The docstring stays ASCII. `usage()`'s text is unchanged. If you change `mutation-run.py`'s docstring or its parser's description, keep it to naming the new refusal. Then run `python tools/dump-cli.py` so the two reference files match, and `python tools/dump-cli.py --check` passes.

**Unchanged.**

25. "Every existing line and exit of the launcher with one slot; the heavy launch's duration figures and the loop guard's counts (each waiter's bound stays capped at the builder cap plus grace); the review guard; the boundary listing." The Known limits of the design are recorded, not built: do not add a queue, a cleanup of old lock files, or a CPU or port guard.

## Acceptance criteria
- [ ] `python -m pytest tests/test_hotfix24a_heavy_slots.py -q -p no:cacheprovider` passes all 31 cases (Constraints, command 2).
- [ ] The regression batch (Constraints, command 3) passes with no failure, no test file edited.
- [ ] `python tools/dump-cli.py --check` exits 0 after `python tools/dump-cli.py` regenerated `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` (command 4).
- [ ] `windowless-check.py` reports no FAIL in `bridge/cursor-bridge/bridge-run.py` or `bridge/cursor-bridge/mutation-run.py` (command 5).
- [ ] Both changed programs are ASCII-only (command 6).
- [ ] `git status --short` after your run shows changes only to the Scope's files (command 7; `tests/test_hotfix24a_heavy_slots.py` may show as untracked or unchanged, never modified by you).
- [ ] With no `heavy-slots.json`, every line and exit of a launch is byte-identical to 2026.11.23a's except that a heavy run's row gains `"slot": 1` (Requirements 12, 22, 25).
- [ ] Every requirement above is fully met, with no stand-in and no "later" text; the trace is the acceptance file, whose docstrings name the design lines.
- [ ] No new Semgrep high finding; every file under `~/.cursor-bridge` and the mutation engine's lock file is opened with no link followed (secure-coding.mdc, ASVS level 2).

## Constraints
- Do not add dependencies. The standard library and the modules already imported are enough (`hashlib` is already imported in `bridge-run.py`).
- Do not read or write any file outside this workspace (the folder you were started in), except the system temporary folder, which pytest uses for its `tmp_path` and you may use for scratch files (delete yours when done). Everything you produce goes inside the workspace.
- Run pytest with `-p no:cacheprovider`, so no cache folder lands in the workspace.
- The mutation engine's lock uses exactly the launcher's primitive: `msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)` on byte 0 on Windows, `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)` elsewhere (the acceptance test's helper process holds it that way), with "held by another" told apart from an error as `_try_lock_byte` does.
- `heavy_state_paths(env)` keeps its two-item answer for slot 1; a new function gives slot k's paths. `acquire_heavy_slot(kind, run_id, limit, scale)` stays callable with those four positional arguments, returning a tuple whose first item is the taken slot's lock fd and second the waited seconds, `None` after the exit-123 lines, `"refused"` after a refusal line (extra parameters with defaults and extra tuple items are fine). `_try_lock_byte`, `_unlock_byte`, `publish_holder_record`, `read_holder_record`, `process_creation_epoch`, `holder_end_time`, `_waiting_line` and `_slot_not_free_line` keep their signatures and their behaviour.
- Every existing line and exit with one slot stays byte-identical (Requirement 25).
- No secret, key or token is involved. Do not read any.
- If the brief, the rules or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it at the end of `docs/BUILDER_NOTES.md`, in its form `YYYY-MM-DD HOTFIX-004-r1: <text>`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round).
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=NO_WINDOW`, the module's own constant, as every launch in both programs does; reuse `_git_rev_parse_path` for `git rev-parse --show-toplevel`, which already is). Capturing output does not prevent the window.
- Never start a server, a watcher or a daemon that outlives a test. The acceptance tests start and stop their own launches; nothing you run may be left running when you end.
- Do not refactor code outside the scope, even if it looks wrong; inside the two programs, change only what the requirements need. If you notice something worth changing (a message, an edge case), report it in your summary instead.
- Never run the product against the owner's live data: never run `bridge-run.py`, `mutation-run.py` or `bridge-install.py` by hand against the real home folder, this repository's `run/` record or the real `cursor-agent`. Run only the commands below.
- Follow the existing conventions in both files: the `bridge-run: ` and `mutation-run: ` line prefixes, `sys.stderr.write` for the launcher's lines, `Refuse` for the mutation engine's refusals, exception class names in the `(<error class>)` part.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff`, `git log` and `git show` only.
- Numbers are parsed with the language's own parser, never by slicing: the `--heavy-slots` value with `int()` (a count of slots, range 1 to 4); the setting's value with `json.loads` and `type(...) is int` (range 1 to 4).
- Each process this increment starts (the `git rev-parse` call) is windowless, bounded by `bridge_env.GIT_TIMEOUT`, and leaves nothing behind; its output is captured and closed by `subprocess.run`.
- ASCII-only source in both programs (both docstrings say so: cp1252 consoles), the docstrings included.
- Prefer reuse over new code: the existing byte lock, opener, record publishing and validation, line builders and git helper; write the minimum that meets the requirements (the frozen minimal-code rule).
- Mutation: you are not asked to run mutations. List the code points (Done). If you mutate by hand to check one, restore it in the same run and say so; no mutation script lands in the diff. The supervisor's mutation run comes after yours.
- Verification commands. Run them from the workspace root (the folder that holds `bridge/`, `tests/` and `tools/`), in PowerShell, in the foreground, exactly as written. The two pytest commands take several minutes (the tests wait on real launches); wait for each to end, never run one in the background.
  1. Before you change anything: `git status --short`
  2. The acceptance file: `python -m pytest tests/test_hotfix24a_heavy_slots.py -q -p no:cacheprovider`
  3. The regression batch: `python -m pytest tests/test_bridge_run_slot.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_bridge_run_review_ceiling.py tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_loop_text_windowless.py tests/test_dump_cli.py tests/test_program_launcher_forms.py tests/test_release_t_strip.py tests/test_task032_supervisor_launcher.py tests/test_bug029_agent_name.py -q -p no:cacheprovider`
  4. The reference: `python tools/dump-cli.py`, then `python tools/dump-cli.py --check`, then `echo $LASTEXITCODE` (want 0).
  5. Windowless: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`, then `echo $LASTEXITCODE` (want 0; a FAIL outside the two scoped files is reported, not fixed).
  6. ASCII: `python -c "import sys; bad=[(p,i+1) for p in ('bridge/cursor-bridge/bridge-run.py','bridge/cursor-bridge/mutation-run.py') for i,l in enumerate(open(p,'rb').read().split(b'\n')) if any(c>127 for c in l)]; print(bad or 'ascii ok'); sys.exit(1 if bad else 0)"` (want `ascii ok`).
  7. After your last edit of any file: `git status --short`, `git diff --stat`, `git rev-parse HEAD`.

## Done
Your report is the file `handoff/HOTFIX-004-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, what you could not do, so that nothing of it is lost when your run ends early. When you finish, it holds:
- every file you changed;
- a one-paragraph summary of what you did;
- each requirement (1 to 25) with the file and line that meets it;
- the mutation code points: for each requirement, the code point whose removal or change would break it, and the acceptance test (by name and parameter id) that would catch it, or `no test` where none would;
- a section headed `Missing acceptance cases`: each behaviour of the requirements that no case of `tests/test_hotfix24a_heavy_slots.py` exercises (for example a link at the setting's path, n of 3 or 4, a `--workspace` builder's identity, `bridge-stop.py` ending a waiter, a link at the mutation lock's path), one per line, or `none`;
- the output of every verification command, verbatim, in fenced blocks: both `git status --short` outputs, the last lines of both pytest runs (the summary line quoted whole, and every failure's test id), the dump-cli check's exit code, the windowless-check output and exit code, the ASCII check's output, `git diff --stat`, and `git rev-parse HEAD`. A command you did not run is written `not run`, never described as run. Run commands 2 to 7 once more after your last edit of any file, and write the results from that run, naming the commit (`git rev-parse HEAD`) and whether the working tree held uncommitted changes (`git status --short`);
- the dated lines you appended to `docs/BUILDER_NOTES.md`, or `Builder notes: none`;
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief, the design nor the existing code settled, and that you did not confirm. Examples: the `<cause>` texts you chose, how an open or lock error on the mutation lock file other than "held" ends the run, how the identity is case-folded on Windows, what a folder lock waiter prints when it moves from the folder wait to the slot wait, whether `git rev-parse --show-toplevel` answers inside a worktree as expected. One item per line: what you assumed; why; what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, so a message printed earlier and then followed by more work is lost.
