---
record: brief
header: 1
id: "TASK-074"
round: 2
satisfies: [R-093]
scope: ["bridge/cursor-bridge/bridge-check.py", "tools/make-manifest.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_install_check.py", "docs/BUILDER_NOTES.md", "handoff/TASK-074-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-074 round 2: the refusal covers the whole tree, survives a name it cannot resolve, and says what it is (R-093)

Round cause: security - the security audit of round 1 rejected it (a defect of the class the brief's own acceptance criterion names: an exception escaping as a traceback on hostile input), with Should fix findings from both reviewers.

## Objective
Round 1 (committed at 961d8bf; its brief is `handoff/TASK-074.md`, its report `handoff/TASK-074-r1-report.md`) made `bridge/cursor-bridge/bridge-check.py --sources` refuse, with exit 2, a check where the program does not stand in the tree it checks, and made `tools/make-manifest.py` keep `VERSION`'s line ending. Its reviews found that the refusal can be bypassed and can crash: it compares only `<--root>/cursor-bridge`, so a tree whose `cursor-bridge` is a link into the program's tree is checked (its other folders hashed under the unresolved root) and passes; a `--root` that cannot be resolved (`CON` on Windows) escapes as a traceback; and the refusal line says neither that it refused nor which folder is which. This round repairs those findings and the smaller ones listed under Requirements, nothing else. Everything round 1 achieved stays: the 7 round-1 acceptance cases pass on round 1 and must still pass.

Satisfies: R-093 - The release tooling checks the tree it stands in (C21, J5): `bridge-check.py --sources` refuses, with exit 2, where the program does not stand in the tree it checks, and prints both folders on its result line; `tools/make-manifest.py` writes `VERSION` with the file's own line ending. (Its row in `docs/REQUIREMENTS.md` is line 119.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-check.py
- tools/make-manifest.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_install_check.py
- docs/BUILDER_NOTES.md
- handoff/TASK-074-r2-report.md

Limits on these paths:
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand.
- `tests/test_install_check.py`: every existing case must pass **unedited**. Append a line `# ---- builder's cases below this line` at the very end of the file, and your cases (Requirements R6) below it. Nothing above that line changes.
- `tests/test_program_release_tooling.py` is the supervisor's acceptance file (10 cases, committed at 67b515a). It is **read-only** for you: read it whole and run it, never edit it. If a case seems wrong, stop and report it by its test id.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration (`.github/`)
- docs/ and handoff/, except the files the Scope section names. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are the supervisor's: they are already regenerated for round 1's docstring, and if this round changes the docstring again the supervisor regenerates them after your build. Do not run `python tools/dump-cli.py` without `--check`, and do not edit either file.
- `bridge/cursor-bridge/VERSION` (make-manifest rewrites it; its content must stay unchanged, Done), `bridge/cursor-bridge/CHANGELOG.md` (no CHANGELOG entry), and every other file under `bridge/`.
- `tools/dump-cli.py` and every other file under `tools/`. In `tools/make-manifest.py`, the unused helper `read_version()` (lines 62-66) is not this round's.
- `--root` given as the last word raises `IndexError` (`bridge-check.py:147`, pre-existing): the supervisor has routed it to `docs/HARDENING.md`. Do not fix it.
- Every test file other than `tests/test_install_check.py`; `tests/test_program_release_tooling.py` included (read-only).
- Any mutation script or mutants file: the mutation run is the supervisor's, after your run.
- `~/.claude`, `~/.cursor-bridge` and any real installation: you never install anything and never run the installed `bridge-check.py`.

## Context
**The design that binds this increment.** `docs/DESIGN.md` line 363, the bullet `*C21 and J5.*`: "`bridge-check.py --sources` refuses (exit 2) where the program does not stand in the tree it checks, and prints both folders on its result line. `tools/make-manifest.py` writes `VERSION` with the file's own line ending." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-074` (line 1936), its `Done when` on line 1945.

**`bridge/cursor-bridge/bridge-check.py` after round 1 (246 lines; read it whole).**
- The docstring's exit list, lines 27-28: `Exit:   0 = every manifest file OK; 1 = at least one STALE or MISSING;` / `        2 = manifest unreadable, or under --sources the program does not stand in the tree it checks.  ASCII-only on purpose (cp1252 consoles).`
- `HERE = os.path.dirname(os.path.abspath(__file__))` (line 36).
- `main()` (lines 141-238): `root` defaults to `os.path.abspath(os.path.join(HERE, os.pardir))` (line 143), `--root` read as `os.path.abspath(argv[argv.index("--root") + 1])` (line 147); the manifest read from `HERE` (lines 148-154). Round 1's comparison, lines 156-161:
  ```
  if sources:
      here_folder = os.path.realpath(HERE)
      check_folder = os.path.realpath(os.path.join(root, "cursor-bridge"))
      if os.path.normcase(here_folder) != os.path.normcase(check_folder):
          print("RESULT: %s %s" % (here_folder, check_folder))
          return 2
  ```
  Then the manifest's files are hashed under the unresolved `root` (line 169), the EXTRA walk covers `commands`, `agents`, `skills` and `cursor-bridge` under that `root` (lines 209-216), and the RESULT lines: `RESULT: SOURCES DO NOT MATCH their stamp - run tools/make-manifest.py after the last edit, then re-run. %s` with `os.path.realpath(HERE)` (line 229, exit 1) and `RESULT: SOURCES MATCH bridge %s %s` with the version and `os.path.realpath(HERE)` (line 235, exit 0).
- The program is recorded in the command reference from its module docstring; keep it free of argparse (no `ArgumentParser`, no `build_parser()`), and add no option.

**`tools/make-manifest.py` after round 1 (112 lines).** Lines 91-100:
  ```
  version_path = os.path.join(CB, "VERSION")
  line_ending = b"\n"
  if os.path.isfile(version_path):
      existing = open(version_path, "rb").read()
      if existing.endswith(b"\r\n"):
          line_ending = b"\r\n"
      elif existing.endswith(b"\n"):
          line_ending = b"\n"
  with open(version_path, "wb") as f:
      f.write(("%s" % version).encode("ascii") + line_ending)
  ```
  Before round 1 it wrote VERSION with `open(..., "w", encoding="utf-8", newline="\n")`, i.e. UTF-8. The version it writes has passed `version not in changelog_versions()` (line 76), whose pattern is `^## (\d{4}\.\d{2}\.\d{2}[a-z]?)\b`. The bridge's own `VERSION` in this checkout is CRLF, `2026.11.12a`, which is also the newest CHANGELOG entry.

**The acceptance tests.** `tests/test_program_release_tooling.py`, 10 cases at 67b515a; its module docstring (lines 1-26) states the forms it pins and what it leaves open. Read it whole. On round 1's code: 3 failed, 7 passed (the 3 failing are the `test_r093_r2_` cases). `norm(text)` turns backslashes into `/` and, on Windows, lower-cases; `resolved(folder)` is `norm(os.path.realpath(folder))`; `names(text, folder)` is `resolved(folder) in norm(text)`, a substring test. What each refusal case looks for, which settles how the refusal names its folders:
- `test_r093_a_check_of_another_tree_is_refused_naming_both_folders` and `test_r093_a_stale_other_tree_is_refused_not_judged` (program in `A`, `--root B`, plain folders): exit 2; the output, anywhere, names `A/cursor-bridge` resolved **and `B/cursor-bridge` resolved**; nothing hashed (`hashed_nothing`: no line whose first word after leading spaces is `OK`, `STALE`, `MISSING` or `EXTRA`, no `bridge-check:` line holding `OK,`); no `RESULT: SOURCES MATCH`; the stale case also no `STALE` anywhere.
- `test_r093_r2_a_tree_whose_cursor_bridge_is_linked_into_the_program_tree_is_refused` (program in `A`; `--root X`, where `X` holds copies of A's other folders and `X/cursor-bridge` is a junction, or on Linux a symbolic link, to `A/cursor-bridge`): exit 2; the output names `A/cursor-bridge` resolved **and `X` resolved** (`os.path.realpath(X/cursor-bridge)` is A's folder, so printing only that does not name X); nothing hashed; neither `SOURCES MATCH` nor `SOURCES DO NOT MATCH` anywhere.
- `test_r093_r2_a_device_name_as_root_is_refused_without_a_traceback` (Windows only; `--root CON`): exit 2, no `Traceback`, nothing hashed, no `SOURCES MATCH`. On Python 3.12, `os.path.abspath("CON")` is `\\.\CON` (backslash, backslash, dot, backslash, CON), and the non-strict `os.path.realpath` of `\\.\CON\cursor-bridge` raises `OSError` (WinError 1168); this is the audit's Must fix.
- `test_r093_r2_the_refusal_says_it_refused_and_names_both_folders` (program in `tree A`, `--root "tree B"`, folders with a space): the last line starting `RESULT: REFUSED` holds `tree A/cursor-bridge` resolved and `tree B` resolved.
- So: the program's folder printed as `os.path.realpath(HERE)` meets every case. For the tree asked for, `os.path.realpath(root)` alone fails the two round-1 refusal cases (they look for `B/cursor-bridge`), and `os.path.realpath(<root>/cursor-bridge)` alone fails the linked case (it is A's folder); a spelling that holds the resolved root followed by `cursor-bridge` (the resolved root joined with `cursor-bridge`, not resolved again) meets all of them, as does printing both the resolved root and its `cursor-bridge` folder. Your choice, as long as all 10 cases pass.
- The matching cases (`--root <tree>`, `--root .` with the working folder at the tree, `--root <tree>/cursor-bridge/..`) need exit 0 and the folder on the `RESULT: SOURCES MATCH` line; the EXTRA case needs exit 1 and the folder on the `RESULT: SOURCES DO NOT MATCH` line. The stamp case needs a CRLF VERSION kept CRLF across two runs.

Each case copies this repository's `bridge/` with its `MANIFEST.json`, so the cases where the program checks its own tree pass only once `MANIFEST.json` has been regenerated after your last edit of `bridge-check.py`. Run `python tools/make-manifest.py` before the pytest command (Done).

**The existing tests that hold the unchanged behaviour.** `tests/test_install_check.py` line 224 asserts `"RESULT: SOURCES MATCH bridge" in out` for the repository's own tree (nothing may come between `SOURCES MATCH` and `bridge`); line 235 asserts `"SOURCES DO NOT MATCH" in out`. Its cases without `--sources` (`RESULT: INSTALLED TREE MATCHES`, lines 70 and 280) hold the installed-tree check, which does not change. Its `run(prog, tmp_path, *args)` helper (lines 29-35) runs a program as a subprocess with `LOCALAPPDATA` under `tmp_path`.

**The CI step that must still pass.** `.github/workflows/tests.yml` line 29: `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`, run from the repository root on Windows and Ubuntu, exit 0. Line 31 runs `python tools/dump-cli.py --check`: it exits 0 at HEAD; if you change the docstring, it reports `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` stale until the supervisor regenerates them. Quote its output either way; do not fix it.

**External services.** None. This increment makes no external call, so there is no call time and no retry limit to record. Make no network call. The session's `claude --version` is not used by this increment.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. Input crossing into these programs: the command-line words (`--root` is any text, a device name and a path through a link included) and the files and links of the tree checked or stamped. The refusal is the boundary: under `--sources` no file under a `--root` other than the program's own tree is read or hashed, and hostile input never ends in a traceback.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you: run `bridge-check.py` only as `bridge/cursor-bridge/bridge-check.py` of this Workspace (Done) or through the tests on their copies under `tmp_path`; run `tools/make-manifest.py` of this Workspace only in the Done steps and the mutation procedure, and in your own cases only a copy under `tmp_path`; never run the installed copy under your home folder, never run `bridge-install.py`, and never point `--root` at your home folder.

**Host.** Windows 11 with the owner's Python 3.12. CI also runs on Ubuntu.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
Round 1's requirements (`handoff/TASK-074.md`, R1-R7) still hold except where a requirement below changes them. Each finding below is one requirement.

1. **R1. A folder that cannot be resolved is a refusal** (Must fix, security audit; `bridge/cursor-bridge/bridge-check.py:157-158`). With `--root CON --sources` on Windows, `os.path.realpath` raises `OSError` [WinError 1168] for `\\.\CON\cursor-bridge`; the traceback escapes and the exit is 1. Required: any `OSError` or `ValueError` raised while resolving either folder under `--sources` is a refusal: exit 2, the refusal line of R3 naming both folders (where resolving failed, the unresolved spelling the program had, i.e. the `root` it read, or `HERE`), no traceback, nothing hashed. Case: `test_r093_r2_a_device_name_as_root_is_refused_without_a_traceback`.
2. **R2. The tree checked is the whole `--root`** (Should fix, security audit; `bridge/cursor-bridge/bridge-check.py:158`, with the hashing at line 169 and the EXTRA walk at line 211). Round 1 compares only `realpath(<root>/cursor-bridge)`, but `commands/`, `agents/` and `skills/` are hashed under the unresolved root, so a tree `X` whose `cursor-bridge` is a junction to the program's tree passes (round 1 printed `SOURCES MATCH` for it). Required: compare `os.path.realpath(root)` with `os.path.realpath(os.path.dirname(HERE))` (the program's tree), both under `os.path.normcase`; where they differ, refuse (exit 2, R3) before any file is hashed. Whether round 1's `cursor-bridge` comparison stays beside it is your choice; the round-1 cases must still pass. The refusal names the program's folder (its `cursor-bridge` folder or its tree) and the tree asked for, in a spelling that meets every case (Context, "The acceptance tests"). Case: `test_r093_r2_a_tree_whose_cursor_bridge_is_linked_into_the_program_tree_is_refused`.
3. **R3. The refusal says what it is** (Should fix, Review A and the security audit; `bridge/cursor-bridge/bridge-check.py:160`). Round 1's line, `RESULT: <a> <b>`, says neither that it refused, nor which folder is which, nor what to do, and with spaces in the folders nothing marks where one ends. Required: one line beginning `RESULT: REFUSED` that labels the program's folder and the tree asked for (each folder after its own label, delimited so that a folder with spaces reads as one, for example in quotes), and says to run the tree's own `bridge-check.py` instead (that is, `<the tree asked for>/cursor-bridge/bridge-check.py`). The line never holds `SOURCES MATCH` or `SOURCES DO NOT MATCH`. It is the only RESULT line of a refused run. Case: `test_r093_r2_the_refusal_says_it_refused_and_names_both_folders` (folders hold spaces).
4. **R4. The folder on the do-not-match line is labelled** (Consider, taken; Review A; `bridge/cursor-bridge/bridge-check.py:229`). The folder appended after `then re-run.` reads as part of the instruction. Required: label it, for example `(checked: <folder>)`; the folder stays on that line (`test_r093_an_unlisted_file_in_the_tree_it_stands_in_fails_with_the_folder_named` needs it), and the line still holds `SOURCES DO NOT MATCH`. The `RESULT: SOURCES MATCH bridge <version> <folder>` line may take the same label after the version, or stay as it is; nothing may come between `SOURCES MATCH` and `bridge`.
5. **R5. make-manifest writes VERSION safely** (Consider, taken; the audit and Review A; `tools/make-manifest.py:94-100`). Required: read the existing VERSION inside a `with` block; build the bytes to write (the version, encoded, and the line ending) before opening the file for writing, so that a failing encode never leaves VERSION empty; encode as UTF-8, as before round 1, rather than ASCII; drop the dead `elif` that sets `line_ending` to the default it already holds. The line-ending rule is unchanged: CRLF stays CRLF, LF stays LF, a new file is LF; the manifest entry for VERSION is unchanged across runs.
6. **R6. The two line-ending rules no test held get cases** (Consider, taken; Review A). Round 1's criteria "an LF VERSION stays LF" and "a new VERSION is written LF" have no test. Required: two cases below the marker line in `tests/test_install_check.py`, each naming R-093 in its docstring: (a) a VERSION ending in LF stays LF, with no CR in it, after two runs, its bytes and its `MANIFEST.json` entry the same after the second as after the first; (b) with VERSION removed, a run writes it as the version followed by a single LF. Each case runs a copy of `tools/make-manifest.py` beside a copy of `bridge/` under `tmp_path` (as `test_r093_make_manifest_keeps_a_crlf_version_file_crlf` does), passing `--version` with the version the copy's VERSION held; never the Workspace's own `tools/make-manifest.py`, which would stamp this repository.
7. **R7. The report's records** (Records, Review A). The round-1 report restated mutation counts in prose, M4's count did not match its command (its line shows `1 failed in 1.26s`, a single test, not the listed command), and the mutants were not given with their text. Required: the round-2 report quotes each mutant's text and each pytest summary line in fenced blocks, each from the exact command this brief lists for it (Constraints, the mutation self-check).
8. **R8. What stays.** Without `--sources` nothing changes. Under `--sources`, where the program stands in the tree it checks (in any spelling of `--root`), every verdict, line and exit code is as after round 1 apart from R4. No option added; no argparse; both programs ASCII-only; no path of this computer hard-coded. If the docstring's exit-2 clause needs a word for R1 (a folder that cannot be resolved), one short ASCII clause is allowed; nothing else in the docstring changes. `MANIFEST.json` is regenerated after your last edit under `bridge/`; the version stays `2026.11.12a`, and `git diff -- bridge/cursor-bridge/VERSION` is empty.

## Acceptance criteria
- [ ] `tests/test_program_release_tooling.py` passes whole, unedited: 10 cases (on Windows; on Linux the device case is skipped).
- [ ] `tests/test_install_check.py` passes, every existing case unedited; the two cases of R6 sit below the marker line and name R-093 in their docstrings.
- [ ] `--root CON --sources` on Windows exits 2 with a `RESULT: REFUSED` line and no traceback (R1).
- [ ] A `--root` whose `cursor-bridge` is a link into the program's tree is refused, exit 2, nothing hashed (R2).
- [ ] A refused run prints exactly one RESULT line, beginning `RESULT: REFUSED`, labelling both folders readably when they hold spaces and naming the tree's own `bridge-check.py` to run instead (R3).
- [ ] The folder on the `SOURCES DO NOT MATCH` line carries a label (R4).
- [ ] make-manifest reads VERSION in a `with` block, builds the bytes before opening it for writing, encodes UTF-8, and has no dead `elif` (R5).
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`, from the Workspace root, exits 0 and prints `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it.
- [ ] MANIFEST regenerated; `git status --short` does not list `bridge/cursor-bridge/VERSION`; `git diff -- bridge/cursor-bridge/VERSION` is empty.
- [ ] Both programs decode as ASCII.
- [ ] R-093 is fully met, with no stand-in, placeholder or "later" text. The tests naming R-093 are the supervisor's acceptance tests and your two R6 cases.
- [ ] No option added, no new dependency, configuration key or environment variable, no network call. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_release_tooling.py`, any existing case of `tests/test_install_check.py`, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output (the CI-step command prints the resolved folder: replace it with `<Workspace>/bridge/cursor-bridge` in the quote).
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). This increment needs no new process in a program; your two test cases run `make-manifest.py` the way the existing `run` helper of `tests/test_install_check.py` already does.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not fix by suppressing the symptom: R1 catches `OSError` and `ValueError` from resolving the two folders only, never a broad `except Exception` around the check or around `main()`.
- Do not refactor code outside the scope, even if it looks wrong. In both programs change only what R1-R8 need; every other message, refusal and exit code stays as it is.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- A value the brief marks as the owner's: none in this increment.
- Follow existing conventions in the files you touch: ASCII program text, `main()` returning the exit code, messages beginning `bridge-check: ` or `make-manifest: `, RESULT lines beginning `RESULT: `.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `restore`. You read with `git status`, `git diff`, `git log` and `git rev-parse` only.
- Numbers: none are parsed by this increment.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutation run comes after yours. Apply each of M1-M3 by hand, one at a time, to `bridge-check.py`; run `python tools/make-manifest.py` (otherwise the copied tree is STALE and every case fails for the wrong reason); run exactly `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py`; revert the mutant by hand; run `python tools/make-manifest.py` again; confirm with `git diff` that the revert is exact. In the report give each mutant's label and text, the exact command, and its pytest summary line in a fenced block, with the id of one test it made fail; if it is not caught, write `not caught` and one line on the case that would catch it (do not add that case).
  - M1 skip the whole-root comparison of R2 (only the `cursor-bridge` comparison kept).
  - M2 the resolve failure of R1 is not caught.
  - M3 the refusal line loses `RESULT: REFUSED`.
  - M4 make-manifest opens VERSION for writing before encoding. Prove this one by reading, not by running: write `not caught` and why no case can make the encode fail (the version has passed the CHANGELOG pattern of line 76 before it is written), and name the line where the bytes are built before the `open` for writing.
- **Known failures.** On round 1's code the acceptance file gives 3 failed, 7 passed (the 3 `test_r093_r2_` cases). If a case of either test file fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `HERE`, the existing `root` reading, round 1's comparison block, and the standard library (`os.path.realpath`, `os.path.normcase`). Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-074-r2-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created;
- a one-paragraph summary of what you did;
- for R1-R8, one line each on what meets it, naming the functions and their lines as the file stands after your change; for R2 whether round 1's `cursor-bridge` comparison stayed; for R3 the exact refusal line of `test_r093_r2_the_refusal_says_it_refused_and_names_both_folders`'s situation, with `<tmp>` for the folders, and the line printed for `--root CON`;
- your two R6 cases, by test id;
- the mutation self-check, M1-M4, each with its label, its text, its command and its pytest summary line in a fenced block, and the test id that caught it (M4: `not caught` and why);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: which other Windows device names (`NUL`, `COM1`, `CON.txt`) raise from `os.path.realpath` and which resolve; how `os.path.realpath` treats a junction under `~/.claude` that points into a Workspace; what a `VERSION` file with mixed line endings is written with; whether the refusal line prints readably on a cp1252 console. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py` (expect `make-manifest: version 2026.11.12a, ...`)
3. `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py tests/test_install_check.py`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it, exit 0)
5. `python tools/dump-cli.py --check` (exit 0 if the docstring is unchanged; if you changed it, expect `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` reported stale; quote its output and fix nothing; the supervisor regenerates both)
6. `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge-check.py','tools/make-manifest.py')]; print('ascii ok')"` (expect `ascii ok`)
7. `git diff -- bridge/cursor-bridge/VERSION` (expect no output)
8. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it and do not restore it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block, from the exact command listed for it. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it.
- Each mutation is listed by its label and its text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 8, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
