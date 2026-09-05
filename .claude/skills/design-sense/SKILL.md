---
name: design-sense
description: The bridge's house design sense for building UI mockups and judging interfaces. Apply when designing a mockup, choosing a visual direction, or reviewing UI so the result looks intentional rather than machine-generated. Wires Impeccable's direction vocabulary and points at the detector as the checker.
---

# Design sense

This skill is the bridge's **house design sense** — the taste you bring when you design a
mockup or judge an interface. It is prose only: no scripts, no hooks, no keys. The
deterministic rules live in Impeccable's detector and the Vercel interface rules; this skill
is the *judgement* that decides direction and catches the generic default before it ships.

## Design from the product, not a default

A UI that looks machine-generated is a signal to reconsider, not to present. The tells to
avoid: the centred-card-on-grey default; uniform 8px-everything spacing with no rhythm;
one radius on everything; a colour palette that is just Tailwind defaults; equal visual
weight on every element so nothing leads. Design *from what the product is and who uses it*
— a fintech dashboard, a children's game, and a legal archive should not share a skin.

Guard specifically against **this model's own persistent house style** — the look it
reaches for by default across unrelated projects. If two different products would come out
looking the same under your hand, that sameness is the thing to break.

## Use the tools for direction, authoring, and checking

- **Direction** — run `/impeccable shape` with the user to settle the aesthetic direction
  (mood, references, the vocabulary of the look). This happens in the main session.
- **Authoring** — run `/impeccable document` to record the settled visual system at
  `docs/design/DESIGN.md` (fonts, colour roles, radius scale, spacing, elevation). That
  file is the contract, not this skill.
- **Checking** — the Impeccable detector (`impeccable detect`) is the deterministic checker
  for slop and drift; the frozen Vercel `vercel-interface.mdc` carries interface-quality
  rules. Do not restate or duplicate their rules here — cite them and let them do the work.

Optionally seed a direction from `~/.claude/cursor-bridge/design-seeds/<brand>/DESIGN.md`,
then **diverge** into the project's own identity — never ship a near-clone of a real brand.

## Project overrides

*The supervisor fills this section per project from the approved `docs/design/DESIGN.md`.*
Record the handful of decisions that override the house default for this project — the type
stack, the colour roles, the radius and spacing scale, the elevation model, and any
deliberate departure from the interface defaults. Keep it short: pointers into the visual
system, not a copy of it.

- (none yet — populated at Phase 2 for a UI-bearing project)
