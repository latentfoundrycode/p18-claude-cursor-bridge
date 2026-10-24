# Spends money

## Add at intake.questions

For a part whose actions cost real money (a paid API, a purchase, a metered model or service), ask before design, and write each answer to the intake notes: which actions cost money, on which **platform and account** each is charged; the **worst case** of each, the most one run of it can cost when it goes wrong as well as when it goes right (every retry, every item of the largest input, a run that does not stop), estimated in that platform's own units and in money; and the **cap** the owner sets, the most the project may spend in all, per month or per run as the owner names it, with what happens at the cap (the action stops and the owner is asked; never a silent overrun). No paid action runs without the owner's approval first, given in words for that action, with its estimate against the worst case and the platform and account named in the same sentence; an approval covers the action it names, never the next one. A paid call is a remote call, whose wait the trait *external services* bounds (its addition at `delegation-loop.inspect-checks`), so a part that pays a remote service is classified with *external services* too, which the design gate's trait decision checks.

## Add at configuration.items

**The store of paid results.** Before the first paid action, configure where its results are kept: a store under the project's data folder, outside the Workspace's disposable folders, that nothing in the loop discards (no clean, reset, cache purge or test teardown reaches it), each result kept with the request that bought it, so that a retry, a rerun or a crash reads the result already paid for instead of buying it again. Its path is a Resources row of `docs/INVENTORY.md`. **The cap** is recorded where the owner can read it: a Decisions row `Spending cap: <amount> <per month or per run> on <platform and account> (<the owner's words>, <date>)`, beside the provider's own spending limit in the account's Resources row, which configuration's spending-limits item sets.

## Add at delegation-loop.brief-constraints

The builder runs no paid action: a brief that needs one says so, and the paid run is the supervisor's, after the owner's approval for it. Before any paid run, the brief's increment has run once **dry**: on a copy of the data, with a stand-in provider that answers as the real one does (its recorded replies, the trait *external services*' contract capture) and charges nothing, the run's every paid call counted and compared with the estimate.

## Add at delegation-loop.inspect-checks

No paid action ran unapproved: the supervisor reads the builder run's log, the store of paid results and the provider's usage for the run's time, and a paid call with no approval naming it is a blocking finding, recorded as an issue, and told to the owner in the next report's first line with its amount, platform and account.
