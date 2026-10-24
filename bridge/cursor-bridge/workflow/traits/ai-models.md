# AI models

## Add at intake.questions

For a part whose results come from models, ask before design, and write each answer to the intake notes: which results a model produces; for each, the **evaluation set** that stands in for exact tests (the inputs, drawn from the owner's real cases, and what a good result is for each, as the owner judges it), and the **threshold** a result must meet (a share of the set passing, a score, a rate of a named failure no higher than a figure), each threshold the owner's value, fixed in a test (rule 52).

## Add at design.sections

The design has an **Evaluation** section: each evaluation set, where it lives and how it grows, the judge of each result (a rule a program checks, or a model of another family than the one judged, rule 51), each threshold with its source, and what a result below the threshold does to the gate.

## Add at configuration.items

Each model is **pinned**: its exact identifier and version, never a name that moves to a newer model, recorded in `docs/INVENTORY.md` (Resources), and changed only as a change of its own whose evaluation runs before and after. **Recorded outputs** have a home: the model's replies to the evaluation set, kept with the model's identifier and the date, under the project's test fixtures, so that the evaluation runs again without calling the model.

## Add at delegation-loop.test-checks

The evaluation runs against its thresholds on the recorded outputs with the change's tests: a result below a threshold is a correctness-class block (step 7), and an exact-match assertion on a model's output, where the evaluation set should judge it, is a finding of its own. A change that alters the prompt, the model or its settings records new outputs first, in a run the owner has approved where the model costs money, and the evaluation reads those.
