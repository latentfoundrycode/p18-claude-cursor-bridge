# External services

## Add at planning.stages

For every **external service** the software talks to (a third-party API, SDK, or
provider), the plan's first increment on that integration is a **contract capture**: an
attended live call that records the service's real responses as fixtures (secrets
scrubbed), which the adapter's tests then replay. A mock the builder invents encodes the
builder's *assumption* about the service, and a wrong assumption produces a
self-consistent green test — six adapters once merged green that way and every one failed
on its first real call (KP-020). "Done" for an external-integration increment means passing
against recorded real responses or an attended live smoke, never against an invented mock.
The live call needs the owner's key and possibly money: that is the existing
secret/cost escalation, asked once per service.

## Add at planning.critic-lenses

- **External-service integrations.** For every third-party API, SDK, or provider the
  software talks to: is the first increment on it a **contract capture** (an attended live
  call recorded to fixtures, secrets scrubbed) that later increments replay, with "passes
  against recorded real responses" as the acceptance criterion? An adapter increment whose
  only evidence is a mock the builder writes is **Blocking**: it tests the builder's
  assumption about the service, not the service (KP-020).

## Add at delegation-loop.inspect-checks

Every wait on a remote service in the diff is bounded: a call to a service run by others carries a timeout and a bounded retry, and a wait with no bound is a blocking finding, re-delegated like any defect (step 7).

## Add at delegation-loop.test-checks

Before any deployment, the deployed layout is tested: the part runs from the files and the configuration it will be deployed with, its configuration read as the deployed part reads it, and a test that passes only in the development layout does not count; a failing one is a correctness-class block (step 7).

## Add at delegation-loop.brief-constraints

Every remote wait the increment adds is bounded: the brief names the timeout and the retry limit of each call to a service run by others, and the builder adds none without them.
