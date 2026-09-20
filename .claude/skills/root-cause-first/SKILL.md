---
name: root-cause-first
description: Evidence-before-fix debugging. Apply whenever a bug, failing test, fired invariant, reviewer rejection, or user-reported defect is about to be "fixed" and the cause is not already proven by the failure itself. Reproduce deterministically, write competing hypotheses, instrument only to tell them apart, read the runtime evidence, and fix the confirmed cause — never the symptom. No reproduction, no fix; no confirmed cause, no fix brief.
---

# Root cause first

A fix written from a symptom is a guess with a diff attached. It passes the test that
was failing, often by suppressing what the test saw, and the cause stays in the code to
surface elsewhere. This skill replaces guessing with a short, bounded procedure that ends
in a fix whose reason is *known*, not hoped. It is the bridge's adaptation of the
"hypothesize → instrument → reproduce → analyze → fix → clean up" method to a headless
loop: the human reproducer becomes a deterministic reproduction, and the log server
becomes a file.

## When it applies — and when it does not

Apply it when **the cause is not already proven by the failure itself**. Signals:

- the failing test's message does not name the cause (an assertion on an output, a
  timeout, a wrong count, a crash deep in a call chain);
- a runtime invariant or `console.error` fired, or an inventory state is unreachable;
- a reviewer rejected for a behaviour defect, not a conformance omission;
- the defect is timing-related, intermittent, performance, memory, or a regression;
- a user reported it (their description is a symptom, never a cause);
- **this would be the second re-delegation for the same defect** — the first fix was a
  guess, by definition.

Skip it — proportionality — when the failure *is* the cause: a missing import named in the
traceback, a typo the linter points at, a requirement the brief listed and the diff simply
omitted. Then fix directly. Do not turn a one-line omission into a diagnosis.

## The procedure

### 1. Reproduce deterministically — no reproduction, no fix

Before anything else, make the bug fail **reliably**, on demand, without a human:

- a **failing test** at the narrowest level that shows it (unit before integration before
  end-to-end);
- for a UI-bearing project, an **observability test** that drives the app to the exact
  inventory state through the real render path (`Observability-Conventions.md`) — that is
  what the state-reachability contract exists for;
- under the project's **test-mode determinism** (fixed clock, seed, locale), so runs are
  comparable.

If it does not fail reliably, that is the first bug: run it N times, find what varies
(time, order, shared state, a real race) and pin it. A bug that cannot be reproduced is not
fixed by a diff; it is fixed by first making it reproducible. Record the reproduction
command and its failure output — this test is the future **regression test** and ships with
the fix.

### 2. Hypotheses, in writing, before touching code

Write `docs/debug/BUG-<nnn>.md` with:

```
# BUG-<nnn> — <symptom, one line>
Reproduction: <command>  → fails with: <the key line>
Trigger: <failing test | invariant | reviewer REJECT | user report | 2nd re-delegation>

## Hypotheses
H1: <candidate cause>  — would show as: <the observation that confirms it>  — refuted by: <the observation that rules it out>
H2: ...
H3: ...
```

At least **two** hypotheses; three is normal. The discipline is the *discriminator* column:
each hypothesis names the runtime observation that would confirm or refute it. A
hypothesis with no discriminator is a hunch, not a hypothesis — sharpen it or drop it. If
you can only think of one cause, you have not looked hard enough or the failure already
names it (then step 0 applied — fix directly).

### 3. Instrument only to discriminate

Add the fewest temporary log lines that separate the hypotheses — at the branch points
they disagree on, printing the *values* that decide (not "got here"). Every line carries
the tag `DEBUG-BUG-<nnn>` so nothing can be left behind unseen. Log to stderr or to the
project's test-mode logger; the run's output is captured to a file (step 4), never to a
server, never to a daemon.

The supervisor may write these itself. They are diagnostic scaffolding in the same class as
tests: they never ship, and the standing rule that **nothing is delegated from a dirty
tree** guarantees their removal before any fix brief goes out. Work on the increment's
branch with an uncommitted working tree, or on a throwaway `debug/BUG-<nnn>` branch that
is deleted afterwards — never on a commit that could reach a PR.

### 4. Run, capture, read

Run the reproduction; redirect the output to the project's gitignored artifacts directory
(`<artifacts>/debug/BUG-<nnn>/run-<k>.log`), where `secret-sentinel` already scans retained
runtime logs. Read the tagged lines against the discriminators:

- **one hypothesis survives** → that is the root cause; copy the confirming lines into
  `BUG-<nnn>.md` under **Evidence** and state the cause in one sentence that a second
  engineer could verify from those lines alone;
- **none survives** → the hypotheses were wrong, not the evidence; write new ones (what the
  values actually showed usually suggests them) and repeat from step 3;
- **more than one survives** → the instrumentation did not discriminate; add the line that
  does.

**Bounded:** three rounds. If the cause is still unconfirmed after three, do not start
guessing at fixes — write the question and the surviving hypotheses to a committed file
and convene the reviewer **resolution round** (`Merge-Verification-Policy.md`); a hard
diagnostic question is the council's, never the user's.

### 5. Clean up — verified, not assumed

Remove every instrumentation line. Then prove it:

```bash
git status --short          # must be clean apart from the new test and BUG-<nnn>.md
git grep -n "DEBUG-BUG-"    # must print nothing
```

Only a clean tree with an empty grep may proceed to the fix brief. `secret-sentinel`
treats a `DEBUG-BUG-` tag in any diff as a block, so a leak cannot reach a commit.

### 6. The fix brief carries the cause, not the symptom

The builder receives `handoff/BUG-<nnn>.md` (spec-packager's fix variant): the **confirmed
root cause** in one sentence, the **evidence lines**, the **reproduction test** that must go
from red to green, and two constraints — *fix that cause and nothing else*, and *if you
believe the cause is different, stop and report instead of fixing*. The builder is not
asked to diagnose; it is asked to repair a named defect. A fix that makes the test pass
without touching the named cause is a `FAIL` at review, however green it is.

### 7. Verify like the bug was reproduced

The reproduction test passes; the whole suite passes; nothing that passed before fails
now. For a timing or intermittent bug, run the reproduction **N times** (the N that
reliably failed before) — one green run proves nothing. The reproduction test stays in the
suite permanently.

### 8. Record the cause, not the story

The bug becomes an issue (`ISS-nnn` in `docs/LESSONS.md`, then the human-facing Issues
document) with the confirmed cause and the evidence. "How could it have been avoided" is
only honest once the cause is known — which is the point of the whole procedure.

## What reviewers hold against a fix

- **Symptom suppression:** a retry, a broad `try/except`, a widened tolerance, a null
  check that hides a wrong value, a `sleep` — any of these where the brief named a cause
  elsewhere. A `FAIL`, and under the merge policy a gate-integrity flag.
- **Cause not addressed:** the diff does not touch the mechanism the brief named.
- **Instrumentation residue:** a `DEBUG-BUG-` tag, a stray print, a changed log level.
- **Diagnosis by assertion:** a "Diagnosis" or "Cause" in a report with no observation
  behind it. Reports label every diagnosis **OBSERVED** (from a traceback, a log line, a
  value) or **INFERRED** (from reading code). An INFERRED diagnosis is a hypothesis and
  enters step 2; it is never the basis of a fix brief on its own.

## For any Claude Code session, not only the supervisor

The procedure needs no bridge machinery: a failing test, a scratch file of hypotheses,
tagged log lines, a captured run, a clean-up grep. When you are about to write a fix and
you cannot state the cause in one sentence backed by something you *observed*, you are
about to guess — stop and run steps 1 to 5 first.
