# SCOPE - TASK-022

A supervisor-authored increment of governance text and its tests, with no builder run and no program change. Its brief is docs/BUILD_PLAN.md, "### TASK-022 — Interface text: contract design and command design" (Scope, Satisfies R-026, Done when), with the three advisories of TASK-012's security audit it was to apply.

## Scope (quoted from the plan)
bridge/cursor-bridge/workflow/phases/interface/contract-design.md; bridge/cursor-bridge/workflow/phases/interface/command-design.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_interface_text.py; tests/test_phase_modules_close.py; tests/test_b3_least_confident.py

## Out of scope
- The declaring section of each variant file ("What this variant is", written by TASK-012 and TASK-014): byte-identical, its pin unchanged.
- Every program under bridge/, and every other phase module.
- The leads recorded in docs/HARDENING.md's new Stage B4 section: a build-time check that no option takes a secret (TASK-030 or TASK-034), a stale docstring in tests/test_phase_modules_interface_planning.py (TASK-035), a glossary row.

## The tests the supervisor wrote, and the paragraph each enforces
tests/test_interface_text.py has 11 tests, each naming R-026 and enforcing TASK-022's Done when:
- the headings of both files;
- the command design's artifact section by section, with no secret in failure output;
- a secret is never an option's value, the homes N2 and KP-032 name, the passphrase rule, a credential shown once;
- the command design's gate and authority;
- the contract design's two artifacts and its versioning, a breaking change escalating;
- each operation names who may call it and the mechanism that tells, including the stdio MCP case;
- each operation bounds what its inputs may reach;
- a refused call changes nothing and reveals nothing, and it is tested, including a wrong secret, a browser origin and a wrong Host header;
- credentials travel as the protocol carries them and live where N2 puts them;
- the contract design's gate, where an added or widened operation escalates;
- no stand-in wording, after the patterns are shown to match two stand-ins.

10 of the 11 fail against origin/main's text. The stand-in guard holds before and after, by design.

tests/test_phase_modules_close.py pins the four new sections beside the declaring ones (EXCUSED_SECTIONS). An entry without a pin fails that test.

## Expected bookkeeping and record files in the diff
docs/REQUIREMENTS.md (R-026 built), docs/INVENTORY.md (the interface-variants row), docs/HARDENING.md (the Stage B4 section; TASK-012's stand-in lead answered), docs/PROJECT_STATUS.md and project.json as at this pull request's merge, and run/review/ (these three files, removed before the merge).

## What to judge
Does the text meet every clause of the Done when and the advisories? Is it sound security guidance for a supervisor designing a product's commands and the protocol other software calls? Does it agree with the core's founding rule N2, Known-Pitfalls KP-032, interface.md and planning.md? Do the tests enforce their paragraphs and fail on a regression? Are the records accurate? Apply the anti-gaming checks.
