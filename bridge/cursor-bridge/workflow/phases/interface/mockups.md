## Mockups

The mockups are the interface phase's variant for screens a person sees (`interface.md`, "The variants"). They are an addition, never a replacement: the trait *has screens* activates them at `interface.variants` for each part that has screens, beside any other variant the part runs, together with its design tooling below. The build-phase conditions of screens (the frozen interface rules in every brief, the design auditor's review, the observability tests of the running interface) are not this file's: they are the build phases' part of the trait *has screens*, read with the build modules.

After the design is approved and before the build plan, turn the agreed design into
something the user can *see*. Build an HTML/CSS mockup of the interface — a static,
disposable design artifact for the user to judge and change, not the product's real
frontend. Cursor implements the real frontend later, in the delegation loop; this mockup
is upstream of the author/reviewer split, so writing it yourself does not compromise
reviewer independence. It is design documentation, not implementation.

The mockup must map onto the agreed functionality **with no gaps, in both directions**:
every capability in `DESIGN.md` has a visible surface in the mockup, and every element in
the mockup traces back to an agreed capability — no orphan screens implying unspecified
features, no agreed feature with nowhere to live. Walk the design's feature list against
the mockup and account for each item before presenting.

Apply the `design-sense` skill (if installed) when building the mockup: design from the
product rather than a default layout, and actively avoid the tells that make a UI look
machine-generated — including this model's own persistent house style. A mockup that looks
like the generic default is a signal to reconsider, not to present.

Iterate with the user until they are satisfied — expect change requests; this is where UI
decisions are cheap to make. Use `AskUserQuestion` for discrete choices, plain discussion
otherwise.

### The design-tooling flow

For a UI-bearing project, build the mockup through the design tooling rather than freehand:

1. **Direction.** Run the aesthetic-direction exchange with the user via `/impeccable
   shape` — in the **main session**, since subagents cannot talk to the user.
2. **Optional seed.** If the user gestures at a known look, pull the matching
   `~/.claude/cursor-bridge/design-seeds/<brand>/DESIGN.md` as a **starting target**, then
   adapt it into the project's own identity. Never ship a near-clone of a real brand.
3. **Author the visual system.** Record it via `/impeccable document` at
   **`docs/design/DESIGN.md`** (+ `PRODUCT.md` if used). This is the file the detector reads.
4. **Build the mockup** applying Impeccable's design language + the frozen Vercel interface
   rules + the empty/sparse/dense/error states from the Phase 1 inventory.
5. **Detect before sign-off.** Run `npx impeccable@<pinned> detect docs/mockups/` — now
   design-system-aware because `docs/design/DESIGN.md` exists — and clear it to **no primary
   findings** before presenting.
6. **Approve the pair.** The user approves the **mockup and the visual `DESIGN.md`
   together** — that pair is the visual contract the builder must not stray from.

Save the mockup files under `docs/mockups/` (one file per screen or view is fine). The
design documents already live under `docs/`. Saving these concludes the mockups; the phase concludes when every variant the parts run is approved (`interface.md`, "The gate").

**Before the gate, make the mockup and the operational activity diagram agree** — every mockup screen is a `scr_` node and every `scr_` node is a mockup screen — **and add every mockup screen and every required state on it to `docs/REQUIREMENTS.md`** as its own row (Source: mockup screen "<name>"), unless an existing row already covers it — a screen in the mockup is a promise to the owner, and a tab that exists only as a picture is how a Settings screen went unbuilt (KP-029).

**Gate:** present the mockup **and the visual `docs/design/DESIGN.md`** to the user and get
explicit approval of the pair before writing the build plan. Do not proceed on an
unapproved mockup, one with unaccounted gaps in either direction against the design, or one
with unresolved primary detector findings.

The existing "approved mockup is guidance; wholesale divergence escalates" rule below
already governs when the contract is reopened. The design tooling adds **no new escalation
path** — a blocking design finding during the build re-delegates like any correctness
defect (Phase 6), it does not go to the user.

**The approved mockup's authority:** once approved, the mockup is **guidance**, not a
pixel contract. Hold to it substantially, with some leeway. A reasonable design
improvement discovered during the build — one that serves the same agreed functionality —
is fine and needs no re-approval; record it in `docs/CHANGES.md`. A *wholesale* divergence
from what was approved is a scope question (does the software now look/behave differently
than agreed?) and escalates to the user. Judge by that line: same intent, better
execution → proceed and note it; different intent → escalate.
