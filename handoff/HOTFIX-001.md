# HOTFIX-001: the launcher holds the design critique's ceiling

## Objective
This is a hotfix of the bridge's release 2026.10.11d, cut on the branch `hotfix-ceiling` as version 2026.10.18a (KP-062). On 2026-10-18 one supervised project ran its design two-critic loop for 45 rounds on one change, which used up the owner's Cursor allowance. The text that limits that loop is already committed (`bridge/commands/supervisor.md`, Phase 2). This hotfix adds the program change that enforces it. `bridge/cursor-bridge/bridge-run.py`, the launcher every `cursor-agent` run goes through, gets a function `design_ceiling(argv, folder)`. It reads the `run/review/DESIGN-<name>.md` file names in a `cursor-agent` command and refuses a design round above the ceiling with exit 125, before anything starts. Commands that do not name a design file behave exactly as they do today.

Satisfies: there is no build-plan increment and no requirements register for this work. The increment id is HOTFIX-001. The requirement is the committed text quoted under Context ("The launcher holds the ceiling." and "The owner's line.", `bridge/commands/supervisor.md`, Phase 2), with the test list in `bridge/cursor-bridge/CHANGELOG.md`, entry `## 2026.10.18a`, bullet "**The launcher holds the ceiling**". The trace to that requirement is the docstring of `tests/test_bridge_run_design_ceiling.py`, which names 2026.10.18a, KP-062 and both paragraphs.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- handoff/HOTFIX-001-r1-report.md
- handoff/HOTFIX-001-r2-report.md (round 2)
- handoff/HOTFIX-001-r3-report.md (round 3)

Do not modify anything else. In `bridge-run.py`, the only docstring change allowed is one added line in the module docstring that names the new refusal. The rest of the docstring stays as it is.

## Out of scope
- .env and anything under secrets/
- CI configuration (`.github/`)
- docs/ and handoff/, except the files the Scope section names
- `tests/`, all of it. Do not edit `tests/test_bridge_run_design_ceiling.py`: the supervisor wrote it and it is the acceptance test. Do not edit `tests/conftest.py` or any other test either.
- `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/VERSION`. The supervisor restamps them after your run. Do not run `tools/make-manifest.py`.
- Every text file. That includes `bridge/commands/*.md`, `bridge/cursor-bridge/CHANGELOG.md`, `bridge/agents/*.md`, `README.md` and the `*.snapshot.md` files.
- Every other program under `bridge/cursor-bridge/` (`bridge_env.py`, `review-guard.py`, `bridge-check.py` and the rest).
- `run/` (the files there, such as `run/review/DESIGN-plan-*.md`, are records; do not touch them) and `.git/`.

## Context
**Where you are.** This checkout is the bridge's own source repository (the folder you were started in, branch `hotfix-ceiling`). It is not a supervised project. It has no `docs/BUILD_PLAN.md`, no `docs/DESIGN.md` and no `docs/INVENTORY.md`, and it has no `.cursor/rules/` folder. The secure-coding and minimal-code principles are in `bridge/cursor-bridge/secure-coding.snapshot.md` and `bridge/cursor-bridge/minimal-code.snapshot.md`. Read them as the rules in force. Do not copy them anywhere.

**Development data:** none. The work runs only the test suite, and the tests use pytest's `tmp_path` and a temporary home (`tests/conftest.py`, the `home_of_the_tests` autouse fixture). Never run `bridge-run.py` against a real project's folder or against the installed bridge under `~/.claude/cursor-bridge/`, and never run it with a real `cursor-agent` command.

**Security context.** The trust boundary is the launcher's command line. The supervisor writes the `cursor-agent` arguments, and the prompt text in them can carry names that came from model output. The launcher is the gate that must hold even when the supervisor does not, which is why `supervisor.md` says "The floor is the launcher's". So the reading must refuse whatever it cannot read and never let it through unchecked. No ASVS level is recorded for the bridge. The rules that apply: never print or read a key file (`key_file_env` is untouched by this work), no new dependency, standard library only.

**The governing text.** It is quoted below verbatim from `bridge/commands/supervisor.md`, Phase 2, lines 395 to 432. The text wins over this brief's specification if the two disagree. If you find a disagreement, stop: do not choose between them. Report the disagreement in your report and your last message.

```
**The launcher holds the ceiling.** `bridge-run.py` reads every `cursor-agent` command whose
arguments name, anywhere and with either path separator, a file `run/review/DESIGN-<name>.md`;
every such name is checked, and one refused name refuses the launch. A name is read from
`DESIGN-` up to `.md` and holds only lower-case letters, digits and hyphens, but for the round's
`R`. The round is the name's last hyphen-separated part: a positive integer written without a
leading zero, or `R` and such an integer; the subject is the rest. Without the owner's line,
rounds 1 to 5 and `R1` are allowed. A name of one part is a round with an empty subject, which
is not `plan` (`DESIGN-5.md`, the plan's file before 2026.10.18a: `DESIGN-1.md` to
`DESIGN-5.md` allowed, `DESIGN-45.md` refused; no line can name that subject, so it is never
lifted). It refuses, with exit 125, before anything starts, and with a message that begins
`bridge-run: refused - design ceiling: ` and names the file, the round and the
`docs/RUN_PARAMETERS.md` it looked in, three things: a name it cannot read that way (a space or
a capital in it, `0`, `05`, `06`, `R0`, a round that is no number, a `run/review/DESIGN-` with
no `.md` after its name), a round above five, and a resolution round `R2` or later. The floor is the launcher's:
a design-mode `cursor-agent` started other than through `bridge-run.py` has no ceiling and
breaks rule 8. A refusal is neither a failed review nor a model's failure (step 3b): it is not
retried and no `--record-failure` follows it; the subject goes on to its resolution round or its
gate, as above.

**The owner's line.** The owner's words lift the ceiling for one subject: a line
`Design rounds above five: <subject> <rounds> (<their words>, <date>)` in
`docs/RUN_PARAMETERS.md`, the subject compared exactly and `<rounds>` above five, lets the
launcher allow that subject rounds 1 to `<rounds>`, `R1` and `R2`, and nothing beyond. Under it
the subject runs the same shape once more from where it stands: critique rounds under the stop
rule up to `<rounds>` minus one, then a confirming read if the text changed (round `<rounds>` at
the most), then, if anything is still open, its next resolution round (`R1` if it has had none,
else `R2`, holding what is still open after the first), then the gate. You never ask for that
line: it is written only on the owner's own words, given unprompted or at the gate, where the
record shows what is open (an owner who sends a design back at its gate to be criticised again
gives exactly those words). `<rounds>` is a round number, never a count: the number of the
last numbered round run (a resolution round not counted) plus the number the owner names, or
plus five when they name none; it is never below six; the line records their words as given,
and the report that records it says in one line how `<rounds>` is spent: critique rounds through
`<rounds>` minus one, then the confirming read at `<rounds>` if the text changed (for an owner
who named two after round four: one critique round, then the confirming read). A subject is
lifted once: the first well-formed line for it stands and a later one is ignored: the owner's words to criticise it again after that make it a scoped revision, a change
with a subject of its own. Before the run-parameters step the line is written to
`docs/RUN_PARAMETERS.md` on its own, creating the file; that step adds its lines beside it.
```

The test list for this text is in `bridge/cursor-bridge/CHANGELOG.md`, entry `## 2026.10.18a`, bullet "**The launcher holds the ceiling**". Read it; do not edit it.

**What exists in `bridge/cursor-bridge/bridge-run.py` today.** Quoted exactly:
- `def head_of(argv):` returns `os.path.basename(argv[0]).lower().replace(".exe", "").replace(".cmd", "") if argv else ""`. Use it for "the head is `cursor-agent`".
- `def owner_cap(kind, folder):` is the sibling reader whose way of reading `docs/RUN_PARAMETERS.md` the new owner's line follows. Its body:
  ```python
  try:
      with open(os.path.join(folder, "docs", "RUN_PARAMETERS.md"), encoding="utf-8") as f:
          for line in f:
              m = re.match(r"^\s*[-*]?\s*\**Ceiling above twice\**\s*:\s*(\w+)\s+(\d+)\s*\((.+)\)", line.strip(), re.I)
              if m and m.group(1).lower() == kind and m.group(3).strip():
                  return int(m.group(2))
  except OSError:
      pass
  return None
  ```
- `def main():` sets `folder = os.getcwd()` (line 421). It then refuses an unaccepted command (lines 431 to 433) and refuses `--key-file` with `cursor-agent` (lines 434 to 436):
  ```python
      if "--key-file" in flags and head_of(cmd) == "cursor-agent":
          sys.stderr.write("bridge-run: refused - a key file never goes to a cursor-agent run (the builder and the reviewer must not see a key)\n")
          return 125
  ```
  After that, `main` chooses the kind and the limit, computes `run_id`, and writes the first stderr line of a started run (line 456): `sys.stderr.write("bridge-run: started %s\n" % run_id)`. The run is logged to `run/launcher/runs.jsonl` (`write_log`) only after the command has started.
- File conventions: plain module-level functions, `re`, short docstrings, constants in upper case near the top, ASCII-only source ("ASCII-only on purpose (cp1252 consoles)" in the module docstring), every refusal written as one `bridge-run: refused - ...` line followed by `return 125`.
- Tests load the program as a module through `tests/conftest.py`'s `program` fixture (`load_program("bridge-run")`) and call `br.design_ceiling(argv, str(tmp_path))` directly. So the function must be at module level with exactly that name and signature.

**A value fixed by the owner.** The ceiling is fixed: 5 rounds and `R1` without the owner's line, and `R2` as the most the line allows. The test file pins it. Do not change it.

## Diagrams
None. This repository has no normative diagrams, and the hotfix has no build-plan `Diagrams:` field.

## Requirements
1. `bridge-run.py` has a module-level function `design_ceiling(argv, folder)`. It returns `None` when the launch is allowed and a reason string when it is refused. `argv` is the inner command (the `cmd` list in `main`) and `folder` is the launcher's current folder.
2. Only a command whose `head_of(argv)` is `cursor-agent` is read; for any other command the function returns `None`. The mode (`--mode=ask`, `--force`, `--mode=plan`, or none) makes no difference.
3. The arguments are joined with spaces. Every occurrence of `run` + separator + `review` + separator + `DESIGN-` is found, where each separator is either `/` or `\` and the occurrence can be anywhere in the text (the prefix of an absolute path makes no difference). `REVIEW-DESIGN-` does not match, because the text right before `DESIGN-` must be the `review` folder and its separator. Match these three, `run`, `review` and `DESIGN-`, ignoring case (on Windows `Run\Review\DESIGN-x-6.md` names the same file and must not slip past); the name after `DESIGN-` is still read as point 5 says, capitals refused.
4. For each occurrence, the token is the text after `DESIGN-` up to the next white space, quote (`"` or `'`) or backquote. Strip any trailing `.`, `,`, `;`, `:`, `)`, `]`, `}` and quotes from it. The result must then end in `.md`; otherwise the name cannot be read. The name is the token without `.md`.
5. The name may hold only lower-case letters, digits and hyphens, except for an `R` that starts the round. The round is the name's last hyphen-separated part. The subject is everything before the last hyphen, and it is empty when there is no hyphen: a one-part name such as `5` is round 5 with an empty subject, and the empty subject is not `plan`. The round must be a positive integer without a leading zero (`[1-9][0-9]*`), or `R` followed by such an integer. Any other name cannot be read and is refused. That covers an empty round, `0`, `05`, `06`, `R`, `R0`, `R01`, `R02`, `r1`, `confirm`, `5b`, a capital letter or a space anywhere in the name, and a token that does not end in `.md`.
6. Without the owner's line, rounds 1 to 5 and `R1` are allowed. A round above 5, and `R2` or later, are refused.
7. The owner's line is read from `os.path.join(folder, "docs", "RUN_PARAMETERS.md")`, the way `owner_cap` reads `Ceiling above twice`. The line is `Design rounds above five: <subject> <rounds> (<their words>, <date>)`, optionally led by `-` or `*` and by bold marks. The subject is a token of lower-case letters, digits and hyphens, compared exactly. `<rounds>` is a decimal integer, parsed with `int`. The words inside the parentheses must not be empty.
8. A line without words, or whose `<rounds>` is not above 5, is not well-formed. Skip it: it does not use up the subject's lift. The first well-formed line for a subject stands, and any later line for the same subject is ignored. Under that line, the subject is allowed rounds 1 to `<rounds>`, `R1` and `R2`, and nothing beyond. No line can name the empty subject. A missing or unreadable file (an `OSError`, or content that does not decode as UTF-8) counts as no line.
9. Every name found in the command is checked. If any name is refused, the launch is refused, and the reason is the one for the first refused name.
10. The reason string begins with `design ceiling: ` and is one line, with no newline inside. It names all of the following:
    - the file: `DESIGN-<name>.md` as read, or the raw token when the name cannot be read
    - the subject
    - the round
    - the full path of the `docs/RUN_PARAMETERS.md` it looked in, built from `folder`, so the text contains the folder
    - the words `Design rounds above five:`, which start the line that lifts the ceiling
    - `supervisor.md` (Phase 2, where the rule is)
    The string is ASCII text.
11. `main()` calls `design_ceiling(cmd, folder)` right after the existing `--key-file` refusal (after line 436) and before the kind, the limit and the `bridge-run: started` line. When it returns a reason, `main` writes `bridge-run: refused - <reason>` and a newline to stderr and returns 125. Nothing is started, nothing is written to `run/launcher/runs.jsonl`, no pid file is written, and no `started` line is printed.
12. For every command that names no `run/review/DESIGN-` file, the behaviour is unchanged. That includes `cursor-agent` code reviews (`REVIEW-012.diff`, `STAGE-B2.diff`, `REVIEW-DESIGN-*.err`), `gh pr checks`, and the test suites. The `started` line stays the first stderr line of every run that starts.
13. It behaves the same on Windows and POSIX. It uses the standard library only (`re` and `os` are already imported) and adds no dependency.

## Acceptance criteria
- [ ] `tests/test_bridge_run_design_ceiling.py` passes in full, all 51 tests (today all 51 fail because `design_ceiling` does not exist):
  - `test_rounds_up_to_five_and_one_resolution_round_are_allowed`, 8 cases: `design-1`, `design-4`, `design-5`, `plan-5`, `azure-allowance-5`, `change-2-5`, `design-R1`, `5`
  - `test_a_sixth_round_and_a_second_resolution_round_are_refused`, 7 cases: `design-6`, `plan-7`, `azure-allowance-45`, `change-2-6`, `design-R2`, `design-R3`, `6`
  - `test_a_round_that_cannot_be_read_is_refused`, 14 cases: `design-0`, `design-05`, `design-R0`, `design-R01`, `design-confirm`, `ceiling-5b`, `design-`, `design-R`, `Azure monthly allowance-1`, `Design-1`, `azure-Allowance-2`, `design-r1`, `design-06`, `design-R02` (each with an owner's line for its subject present)
  - `test_a_design_file_whose_name_does_not_end_in_md_is_refused`
  - `test_a_one_part_name_is_a_round_with_an_empty_subject`, 5 cases: `1` allowed, `5` allowed, `45` refused, `R1` allowed, `R2` refused (with a line lifting `plan` present)
  - `test_trailing_punctuation_is_not_part_of_the_name`
  - `test_an_absolute_path_is_read_too`
  - `test_the_folders_are_matched_in_any_case`
  - `test_one_refused_name_among_several_refuses_the_launch`
  - `test_the_refusal_names_the_file_and_where_it_looked_for_the_owners_line`
  - `test_the_mode_does_not_matter`
  - `test_other_files_and_commands_are_not_touched`
  - `test_a_windows_path_is_read_too`
  - `test_the_owners_line_lifts_the_ceiling_for_its_subject_only`
  - `test_a_second_line_for_one_subject_is_ignored`
  - `test_the_first_well_formed_line_stands`
  - `test_a_line_without_the_owners_words_or_not_above_five_lifts_nothing`, 4 cases: `no-words`, `empty-words`, `not-above-five`, `below-five`
  - `test_the_launcher_refuses_with_125_before_it_starts_anything` (end to end: exit 125, stderr begins `bridge-run: refused - design ceiling: `, no `bridge-run: started`, no `run/launcher/runs.jsonl`)
- [ ] The rest of the suite gives the same results as before your change: the same tests pass and the same tests fail. There is one expected exception. `tests/test_install_check.py::test_the_source_tree_is_checked_against_its_manifest_only` compares the source tree with `MANIFEST.json`, which you do not restamp. If it passes before your change and fails after, report that and leave it; the supervisor restamps. Record the baseline before you change anything (see Done).
- [ ] No behaviour changes for a command that names no `run/review/DESIGN-` file. `tests/test_bridge_run.py` and the other suites that launch `bridge-run.py` give unchanged results.
- [ ] The governing text is fully met, with no placeholder, no stub and no "later" path. The trace to it is the acceptance test module's docstring, which already names 2026.10.18a, KP-062 and both paragraphs. Do not add a test.
- [ ] `bridge-run.py` stays ASCII-only, standard library only, with the same style (plain functions, `re`, short docstrings). Outside `design_ceiling` and its helpers (if any), the call in `main`, and at most one added line in the module docstring, the file is unchanged.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way, write one dated line describing it under a heading `Builder notes` in your report (this hotfix branch has no `docs/` folder; do not create one). That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Add one dated line the same way for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round), so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). The new code launches no process. Keep it that way.
- Never start a server, a watcher or a daemon that outlives a test.
- Do not refactor code outside the scope, even if it looks wrong. That includes `owner_cap`, `cap_for` and the rest of `main`. If you notice something worth changing there, report it instead.
- Never run the product, a migration, a seed or a test against the owner's live data. Here that means: never run `bridge-run.py` against a real project folder, against `~/.claude/cursor-bridge/`, or with a real `cursor-agent` command. Run only the test commands below.
- The ceiling values (5, `R1`, and `R2` under the line) are the owner's. The tests in `tests/test_bridge_run_design_ceiling.py` pin them. Do not change the values or the test. If the work seems to need a change, report it.
- Follow the existing conventions of `bridge-run.py`.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- Numbers from the text (the round, `<rounds>`) are read with a regular expression for their exact shape and converted with `int`. Never slice or split a string to get a number. A round is a count of review rounds, at least 1, with no upper bound. `<rounds>` is a round number and must be above 5 for its line to count.
- Never print or read a key file. `design_ceiling` reads only `docs/RUN_PARAMETERS.md` under `folder`.
- The `bridge-run: started` line stays the first stderr line of a run that starts. No new output is written before it on a run that starts.
- Never refuse with a traceback: whatever the arguments or the run parameters file hold, `design_ceiling` returns `None` or a reason string.
- Verification commands, run from the workspace root (the folder holding `bridge/` and `tests/`), exactly as written:
  - Baseline, before you change any file: `python -m pytest -q tests`. Copy its last summary line and the ids of every failing test into the report.
  - The acceptance test: `python -m pytest -q tests/test_bridge_run_design_ceiling.py`
  - The launcher's existing tests: `python -m pytest -q tests/test_bridge_run.py`
  - The full suite, after your change: `python -m pytest -q tests`. Compare it with the baseline.
- Prefer reuse over new code: `head_of`, the `owner_cap` reading pattern, `re` and `os`. Write the minimum that meets the acceptance criteria (the frozen `minimal-code` rule, `bridge/cursor-bridge/minimal-code.snapshot.md`, is in force). This never overrides the refusal of what cannot be read.

## Done
Your report is the file `handoff/HOTFIX-001-r1-report.md`. Write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing is lost if your run ends early. When you finish, the report holds:
- a list of every file you changed
- a one-paragraph summary of what you did
- the baseline and the final full-suite summary lines, with the ids of any test whose result changed
- one sentence on how `main` keeps the `started` line first and logs nothing on a refusal
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: a reading of the governing text you resolved one way, a quote or separator character you chose to end a token on, a behaviour of `re` or of the platform you expected. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, so a message printed earlier and then followed by more work is lost.

## Round 2: corrections from Review A

Round 1 is accepted in its core; this round changes `bridge/cursor-bridge/bridge-run.py` again and nothing else. Your report for this round is `handoff/HOTFIX-001-r2-report.md` (the same contents as round 1's, for this round); leave `handoff/HOTFIX-001-r1-report.md` as it is. The acceptance tests now number 69 in `tests/test_bridge_run_design_ceiling.py` (the supervisor added 18; 15 of them fail on round 1's code); all 69 pass when you are done, the rest of the suite unchanged. Every Requirement above still holds except where a point below replaces it.

1. **Separators and dot segments (replaces the matching in point 3).** Before looking for design files, normalise the joined text: replace every run of separators, with any `.` segments between them, by one `/`: exactly `re.sub(r"[/\\]+(?:\.[/\\]+)*", "/", text)`. Then find `run/review/DESIGN-` in the normalised text, ignoring case as before. So `run//review/`, `run\\review\\` (a JSON-escaped path), `run/./review/` and `.\run\.\review\` all name the file. (`x/..` segments and 8.3 short names are not handled: accepted, the text holds them.)
2. **One anchored match for the name (replaces the split and slice in point 5).** Read the name with one regular expression, `^(?:([a-z0-9-]*)-)?(R?)([1-9][0-9]*)$`: group 1 the subject (empty when absent), group 2 the `R` of a resolution round, group 3 the number, taken with `int`. No `rsplit` and no slice to get a number.
3. **The refusal says which refusal it is (extends point 8).** The reason reads, in this order: `design ceiling: `, the file as read, `(subject <subject>, round <round>)` where `<round>` is the name's text after its last hyphen as written (`05`, `confirm`, `R2`; the whole name when it has no hyphen), then one of three: `the name cannot be read`, `above round <N>` (`<N>` 5, or the owner's `<rounds>` for that subject), `a resolution round beyond R<k>` (`<k>` 1, or 2 under the owner's line); then the path of `docs/RUN_PARAMETERS.md` it looked in, the words `Design rounds above five:` and `supervisor.md, Phase 2`. The whole reason is ASCII: escape anything else with `encode("ascii", "backslashreplace").decode("ascii")`.
4. **The owner's line in its Markdown forms and its exact alphabet (replaces the regex of point 7).** Accept the colon inside or after the bold (`- **Design rounds above five:** design 8 (...)` and `**Design rounds above five**: design 8 (...)`), led by `-` or `*` or nothing. Only the label ignores case; the subject is `[a-z0-9-]+` as written (a line naming `DESIGN` lifts nothing), and `<rounds>` is ASCII digits `[0-9]+`, never `\d`.
5. **Minimal code (the frozen rule).** Use one constant for the default ceiling of 5 everywhere it is meant (also in the owner's-line check), and constants for the resolution limits 1 and 2. Take the token with a capture group and `str.rstrip` of the trailing punctuation instead of hand-written character loops. Open `docs/RUN_PARAMETERS.md` only when the command names at least one design file.
6. **Your `Assumed, not verified` list.** Round 1 said none; Review A found several (the token ending only at space, tab, CR and LF; `re.I` on the whole owner's line; Unicode digits). List every such fact this round, or confirm each with a test you can point to.

## Round 3: corrections from Review B and Review A's last item

Round 2 is accepted in its core; this round changes `bridge/cursor-bridge/bridge-run.py` again and nothing else. Your report for this round is `handoff/HOTFIX-001-r3-report.md`; leave the earlier reports as they are. The acceptance tests now number 75 (the supervisor added 6, all failing on round 2's code); all 75 pass when you are done, the rest of the suite unchanged.

1. **Trailing dots and spaces of a folder name (extends round 2 point 1).** Windows drops a path component's trailing dots and spaces, so `run./review./DESIGN-design-6.md` opens `run/review/DESIGN-design-6.md`. Before round 2's separator normalisation, remove every run of dots and spaces that stands right before a separator: `re.sub(r"[. ]+(?=[/\\])", "", text)`; then apply round 2's normalisation as it is. (A `..` segment loses its dots too and so cannot hide a folder; `x/..` stays an accepted limit, as do 8.3 short names.)
2. **No traceback on a number `int()` refuses (Review A round 2, the constraint "Never refuse with a traceback").** Python refuses `int()` on more than 4,300 digits with `ValueError`. Catch it where a round or an owner's `<rounds>` is read: a round that `int()` refuses is above every ceiling (refuse it as `above round <N>`, or `a resolution round beyond R<k>`); a line whose `<rounds>` `int()` refuses is not well-formed and is skipped. Do not cap the digit count in a regex.
3. **Only the label of the owner's line ignores case (round 2 point 4, its letter).** Scope the case-insensitivity to the label with `(?i:...)` and drop the whole-pattern `re.I`, so `[a-z0-9-]+` means lower case only.
