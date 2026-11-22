---
record: brief
header: 1
id: "TASK-074"
round: 1
satisfies: [R-093]
scope: ["bridge/cursor-bridge/bridge-check.py", "tools/make-manifest.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_install_check.py", "docs/BUILDER_NOTES.md", "handoff/TASK-074-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-074: The release tooling checks the tree it stands in (R-093)

## Objective
Two small defects in the release tooling. First, `bridge/cursor-bridge/bridge-check.py --sources` checks the tree named by `--root` against the manifest that sits beside the program itself (`HERE/MANIFEST.json`), so the installed copy under `~/.claude/cursor-bridge`, run with `--root <Workspace>/bridge --sources`, judges a source tree against the installed release's manifest and its verdict means nothing. After this increment, under `--sources` only, the program compares the folder it stands in, resolved, with `<--root>/cursor-bridge`, resolved; where they differ it prints both folders and exits 2 before any file is hashed, and where they agree it runs as today and its RESULT line names the folder. Second, `tools/make-manifest.py` always writes `bridge/cursor-bridge/VERSION` with an LF line ending, so on a checkout where that file is CRLF every stamp rewrites its bytes (see `docs/BUILDER_NOTES.md`, the line dated 2026-10-17 BUG-002-r1, and the TASK-073 brief that had to `git restore` it); after this increment it keeps the line ending the file already has.

Satisfies: R-093 - The release tooling checks the tree it stands in (C21, J5): `bridge-check.py --sources` refuses, with exit 2, where the program does not stand in the tree it checks, and prints both folders on its result line; `tools/make-manifest.py` writes `VERSION` with the file's own line ending. (Its row in `docs/REQUIREMENTS.md` is line 119.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-check.py
- tools/make-manifest.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_install_check.py
- docs/BUILDER_NOTES.md
- handoff/TASK-074-r1-report.md

Limits on these paths:
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand.
- `tests/test_install_check.py`: every existing case must pass **unedited**. The one edit allowed is appending cases of your own at the very end, below a line you add, `# ---- builder's cases below this line`, each naming R-093 in its docstring. None is required.
- `tests/test_program_release_tooling.py` is the supervisor's acceptance file, committed at HEAD. It is **read-only** for you: read it whole and run it, never edit it. If a case seems wrong, stop and report it by its test id.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration (`.github/`)
- docs/ and handoff/, except the files the Scope section names. In particular `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are the supervisor's: it regenerates them after your build. Do not run `python tools/dump-cli.py` without `--check`, and do not edit either file.
- `bridge/cursor-bridge/VERSION` (make-manifest rewrites it; after your change its content must be unchanged, Done), `bridge/cursor-bridge/CHANGELOG.md` (no CHANGELOG entry in this increment), and every other file under `bridge/`.
- `tools/dump-cli.py` and every other file under `tools/`.
- Every test file other than `tests/test_install_check.py`; `tests/test_program_release_tooling.py` included (read-only).
- Any mutation script or mutants file: the mutation run is the supervisor's, after your run.
- `~/.claude`, `~/.cursor-bridge` and any real installation: you never install anything and never run the installed `bridge-check.py`.

## Context
**The design that binds this increment.** `docs/DESIGN.md` line 363, the bullet `*C21 and J5.*`: "`bridge-check.py --sources` refuses (exit 2) where the program does not stand in the tree it checks, and prints both folders on its result line. `tools/make-manifest.py` writes `VERSION` with the file's own line ending." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-074` (line 1936); its `Done when` (line 1945): "`bridge-check.py --sources` compares the folder the program itself stands in, resolved, with `<the tree it checks>/cursor-bridge`, and where they differ prints both folders and exits 2 before it hashes anything, so that the installed copy is never taken for a check of a source tree; where they agree its result line names both folders and its verdict and exit codes are as today; the check without `--sources` is unchanged; `tools/make-manifest.py` writes `VERSION` with the line ending the file has, and a tree whose `VERSION` ends in CRLF yields the same manifest hash for it before and after a second run; ... MANIFEST regenerated; no option added; no new dependency."

**`bridge/cursor-bridge/bridge-check.py` as it stands (236 lines; read it whole).**
- Module docstring lines 2-29. Usage lines 20-21; the `--sources` paragraph lines 23-26; the exit list lines 27-28: `Exit:   0 = every manifest file OK; 1 = at least one STALE or MISSING;` / `        2 = manifest unreadable.  ASCII-only on purpose (cp1252 consoles).`
- `HERE = os.path.dirname(os.path.abspath(__file__))` (line 36): the folder the program stands in.
- `main()` (lines 141-228): `root` defaults to `os.path.abspath(os.path.join(HERE, os.pardir))` (line 143); `--quiet` and `--sources` by membership (lines 144-145); `--root` read as `os.path.abspath(argv[argv.index("--root") + 1])` (lines 146-147); the manifest is always read from `HERE` (lines 148-154, exit 2 when unreadable); the loop over the manifest's files hashes each one under `root` (lines 159-171); settings, shim and agent home are skipped under `--sources` (lines 173-200); EXTRA files are collected (lines 202-209); then it prints `bridge-check: version %s (%s) at %s` (line 211), one line per problem as `  %-8s %s` (lines 213-214), the EXTRA lines (215-217), the count line `bridge-check: %d OK, %d STALE, %d MISSING, %d EXTRA` (line 218), and one RESULT line: under `--sources` with any STALE, MISSING or EXTRA, `RESULT: SOURCES DO NOT MATCH their stamp - run tools/make-manifest.py after the last edit, then re-run.` and exit 1 (lines 219-223); otherwise `RESULT: %s bridge %s` with `SOURCES MATCH` or `INSTALLED TREE MATCHES` and the version, exit 0 (line 227).
- The command reference records this program from its module docstring (`tools/dump-cli.py`, `classify_program`, line 182): a file whose text holds `ArgumentParser` without a top-level `build_parser()` makes dump-cli fail. Keep the program free of argparse; no option is added.

**`tools/make-manifest.py` as it stands (104 lines).** `CB` is `bridge/cursor-bridge` under the repository root found from the program's own location (line 29-31). `main()` hashes every file under `bridge/` except `MANIFEST.json` and `.pyc` files, skips `cursor-bridge/VERSION` in the walk (lines 87-88), then writes VERSION with `open(..., "w", encoding="utf-8", newline="\n")` and `f.write("%s\n" % version)` (lines 91-92), hashes it with `norm_hash` (line 93, which turns CRLF into LF before hashing, so the manifest entry is the same for a CRLF and an LF file), and writes `MANIFEST.json` (lines 94-97). The bridge's own `VERSION` in this checkout is CRLF (`2026.11.12a` then CR LF); the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md` is `2026.11.12a`, so a plain `python tools/make-manifest.py` stamps that same version. `.gitattributes` holds only `.githooks/** text eol=lf`.

**The acceptance tests.** `tests/test_program_release_tooling.py` (7 cases, all red at HEAD, the checkpoint) fixes the interface; its module docstring (lines 1-21) states the forms it pins and what it leaves open. Read it whole. Each case copies this repository's `bridge/` (and for the stamp case `tools/make-manifest.py`) under pytest's `tmp_path` and runs the copy's program as a subprocess, with HOME, USERPROFILE, LOCALAPPDATA and APPDATA pointed at scratch folders. What it pins, in short:
- A refused run (the program in tree A, `--root` tree B): exit 2; the output names A's `cursor-bridge` folder and B's, each as `os.path.realpath` gives it (the test compares with backslashes turned into `/` and, on Windows, lower case); no line whose first word after leading spaces is `OK`, `STALE`, `MISSING` or `EXTRA`, no `bridge-check:` line holding `OK,`; and no `RESULT: SOURCES MATCH` anywhere. This holds also when B holds a stale file.
- A run where the program stands in the tree it checks (`--root <tree>`, `--root .` with the working folder at the tree, `--root <tree>/cursor-bridge/..`): exit 0, and the last line starting `RESULT: SOURCES MATCH` holds the folder `<tree>/cursor-bridge` as `os.path.realpath` gives it; with an unlisted file it is exit 1, the line `  EXTRA    cursor-bridge/left-behind.md ...`, and the last line starting `RESULT: SOURCES DO NOT MATCH` holds that folder.
- The stamp: with VERSION written as `<version>` CR LF, two runs of `make-manifest.py --version <version>` each exit 0; after the first VERSION still ends in CR LF and holds no bare LF; the second leaves VERSION's bytes and its `MANIFEST.json` entry as the first wrote them.
- Not pinned: the refusal's wording beyond the two folders, the text around the folder on the RESULT line, separator and letter case.

Because each case copies the repository's `bridge/` with its `MANIFEST.json`, the cases where the program checks its own tree pass only once `MANIFEST.json` has been regenerated after your edit of `bridge-check.py` (before that, `bridge-check.py` itself is STALE in the copy). Run `python tools/make-manifest.py` before the pytest command (Done).

**The existing tests that hold the unchanged behaviour.** `tests/test_install_check.py` line 224 asserts `"RESULT: SOURCES MATCH bridge" in out` for the repository's own tree: the folder you add to that line must therefore come after `bridge <version>`, never between `SOURCES MATCH` and `bridge`. Line 235 asserts `"SOURCES DO NOT MATCH" in out`. The cases without `--sources` (`RESULT: INSTALLED TREE MATCHES`, lines 70 and 280, and `tests/test_program_install_keep.py`, which looks for `MATCHES bridge <version>`) hold the installed-tree check, which this increment does not change. `tests/test_release_b_ci_floor.py:116` pins the CI step's command text, which does not change.

**The CI step that must still pass.** `.github/workflows/tests.yml` line 29: `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`, run from the repository root on Windows and Ubuntu. There the program stands in `bridge/cursor-bridge`, so it must pass, exit 0. Line 31 runs `python tools/dump-cli.py --check`: if you extend the docstring's exit list (allowed, Requirements R4), that check reports `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` stale until the supervisor regenerates them after your build. Expect that, quote it in the report, and do not fix it.

**External services.** None. This increment makes no external call, so there is no call time and no retry limit to record. Make no network call. The session's `claude --version` is not used by this increment.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. Input crossing into these programs: the command-line words (`--root` is any text), and the files of the tree checked or stamped. The refusal is the boundary this increment adds: under `--sources` no file under a `--root` other than the program's own tree is read or hashed. No exception escapes as a traceback.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you: run `bridge-check.py` only as `bridge/cursor-bridge/bridge-check.py` of this Workspace (Done) or through the tests on their copies under `tmp_path`; never run the installed copy under your home folder, never run `bridge-install.py`, and never point `--root` at your home folder.

**Host.** Windows 11 with the owner's Python 3.12. CI also runs on Ubuntu.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **R1. The refusal.** Under `--sources` only, `bridge-check.py` compares `os.path.realpath` of the folder it stands in (`HERE`) with `os.path.realpath` of `<root>/cursor-bridge`, where `<root>` is the `--root` value as the program reads it today (or its default). Comparing both with `os.path.normcase` as well is allowed. The comparison runs before the loop over the manifest's files (before any file is hashed). Where the two differ, it prints a line beginning `RESULT: ` that names both resolved folders, and exits 2. That run prints no per-file verdict line, no `bridge-check: ... OK, ...` count line, and neither `RESULT: SOURCES MATCH` nor `SOURCES DO NOT MATCH` (the refusal is not a verdict on the tree). A missing `<root>/cursor-bridge` is a difference like any other.
2. **R2. The agreeing check.** Where the two agree, every verdict, line and exit code is as today, except that the RESULT line, both `RESULT: SOURCES MATCH bridge <version>` and `RESULT: SOURCES DO NOT MATCH ...`, also names the resolved folder (once is enough, since the two resolved folders are the same; print it as `os.path.realpath` gives it). On the match line the folder comes after `bridge <version>` (Context, line 224 of `tests/test_install_check.py`).
3. **R3. Without `--sources` nothing changes:** no comparison, no new line, the same RESULT lines and exit codes.
4. **R4. The docstring.** The module docstring's exit list may be extended so that exit 2 also names this refusal (one short clause, ASCII). Nothing else in the docstring needs to change. No option is added; no argparse.
5. **R5. The stamp's line ending.** `tools/make-manifest.py` writes `bridge/cursor-bridge/VERSION` with the line ending the existing file has: a file ending in CR LF stays CR LF, a file ending in LF stays LF, and a new file (none there before) is written with LF. The content stays the version followed by one line ending. The manifest entry for `cursor-bridge/VERSION` is unchanged across two runs (it already is, through `norm_hash`). Nothing else in the program's behaviour changes (its usage, its refusals, the files it hashes, the order and format of `MANIFEST.json`).
6. **R6. ASCII.** Both programs stay ASCII-only (their docstrings say why), and every line you add anywhere is ASCII. No path of this computer is hard-coded in a program, a test or a message.
7. **R7. The manifest.** `bridge/cursor-bridge/MANIFEST.json` is regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`; the version stays `2026.11.12a`, what `bridge/cursor-bridge/VERSION` holds, and `git diff -- bridge/cursor-bridge/VERSION` shows no change.

## Acceptance criteria
- [ ] `tests/test_program_release_tooling.py` passes whole, unedited (7 cases).
- [ ] `tests/test_install_check.py` passes, every existing case unedited; any case you added sits below the marker line and names R-093 in its docstring.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`, run from the Workspace root, exits 0 and prints `RESULT: SOURCES MATCH bridge 2026.11.12a` followed by the resolved `bridge/cursor-bridge` folder.
- [ ] Under `--sources` with another tree, exit 2, both folders named, nothing hashed (R1); without `--sources`, output and exit codes as before (R3).
- [ ] `tools/make-manifest.py` keeps a CRLF `VERSION` CRLF and an LF one LF, writes a new one LF, and two runs leave `VERSION` and its manifest entry byte-identical (R5).
- [ ] MANIFEST regenerated; `git status --short` does not list `bridge/cursor-bridge/VERSION`, and `git diff -- bridge/cursor-bridge/VERSION` is empty (R7).
- [ ] Both programs decode as ASCII (R6).
- [ ] R-093 is fully met, with no stand-in, placeholder or "later" text. The tests naming R-093 are the supervisor's acceptance tests.
- [ ] No option added, no new dependency, configuration key or environment variable, no network call. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_release_tooling.py`, any existing case of `tests/test_install_check.py`, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output (the CI-step command prints the resolved folder: replace it with `<Workspace>/bridge/cursor-bridge` in the quote).
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). This increment needs no new process.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong. In both programs change only what R1-R7 need; every other message, refusal and exit code stays as it is.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- A value the brief marks as the owner's: none in this increment.
- Follow existing conventions in the files you touch: ASCII program text, `main()` returning the exit code, messages beginning `bridge-check: ` or `make-manifest: ` (the RESULT lines begin `RESULT: `).
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `restore`. You read with `git status`, `git diff`, `git log` and `git rev-parse` only.
- Numbers: none are parsed by this increment.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutation run comes after yours. Before you finish, apply each of these by hand, one at a time; after applying a mutant to `bridge-check.py` run `python tools/make-manifest.py` (otherwise the copied tree is STALE and every case fails for the wrong reason), then run `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py`, then revert the mutant by hand and run `python tools/make-manifest.py` again; confirm with `git diff` that each revert is exact. List each in the report by its label and text, with the pytest summary line and the id of one test it made fail. If one is not caught, write `not caught` and one line on the case that would catch it (do not add that case):
  - M1 the folder comparison is skipped, so another tree is checked as today.
  - M2 the refusal exits 1 instead of 2.
  - M3 the `RESULT: SOURCES MATCH` line no longer names the folder.
  - M4 `make-manifest.py` writes `VERSION` with LF whatever the existing file holds (today's line 91-92).
- **Known failures.** All 7 acceptance cases fail before your change. If a case of either test file fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `HERE`, the existing `root` reading and the standard library (`os.path.realpath`). Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-074-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created;
- a one-paragraph summary of what you did;
- for R1-R7, one line each on what meets it, naming the functions and their lines as the file stands after your change; for R1 also whether the comparison runs before or after the manifest is read, and the exact refusal line with `<tmp>` for the folders;
- any case you added to `tests/test_install_check.py`, by test id;
- the mutation self-check list, M1-M4, each with its pytest summary line and the test id that caught it (or `not caught` and the case that would);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: how `os.path.realpath` treats a junction or a symbolic link under `~/.claude` on Windows; what a `VERSION` file with mixed line endings is written with; whether the folder on the RESULT line prints readably on a cp1252 console. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py` (expect `make-manifest: version 2026.11.12a, ...`)
3. `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py tests/test_install_check.py`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it, exit 0)
5. `python tools/dump-cli.py --check` (if you changed the docstring, expect it to report `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` stale; quote its output and fix nothing; the supervisor regenerates both)
6. `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge-check.py','tools/make-manifest.py')]; print('ascii ok')"` (expect `ascii ok`)
7. `git diff -- bridge/cursor-bridge/VERSION` (expect no output)
8. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it and do not restore it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 8, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
