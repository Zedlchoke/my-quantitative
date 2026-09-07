# Claude Code operating contract

This repository is an evidence-first quantitative research factory. A profitable
number is not a valid result unless identity, data, costs, trial accounting,
gates and reproduction all reconcile.

## Start every task

1. Read the applicable plan in full before changing files. All plans live in
   `plans/`; the highest version per asset is the live one (see `RULES.md`
   for the law summary and the agent roster):
   - crypto live: `plans/PLAN_crypto_v16.md`
   - stocks live: `plans/PLAN_stocks_v11.md`
   - forex live: `plans/PLAN_forex_v7.md`
2. Read `NOTES.md` and `research/wayfinder/MAP.md` when the task touches research.
3. Run `/repo-intake`. Re-measure the checkout; historical plan snapshots are
   evidence, not current truth.
4. Print and verify absolute `cwd`, full HEAD, branch and porcelain status.
5. Stop on an unexplained dirty tree, wrong branch/worktree, active scoring
   worker, missing authority file or identity mismatch. Preserve owner changes.

## Repository invariants

- Use `.venv/bin/python`; do not silently fall back to another interpreter.
- The root checkout is bootstrap/owner space. Implement research lanes only in
  the exact worktree and branch frozen by the applicable plan.
- A1 is the sole integration, merge, central-ledger and publication authority.
- Lane agents return one focused clean commit and a handoff; they never merge,
  rebase, push, amend another lane, or edit unspecified files.
- A7 is independent: it writes audit artifacts only and never repairs the code
  it audits.
- Crypto, stocks and forex have separate data contracts, calendars, costs,
  ledgers, counters and conclusions. Shared code must prove compatibility.
- S0 is screening, not untouched OOS. S1 stays sealed until a later explicitly
  authorized stage.
- Count every scientifically computed scored result in the observed counter,
  even when publication fails. Keep observed and published denominators separate.
- Historical worktrees, ledgers and scored artifacts are append-only evidence.
- No parameter rescue, family replacement or assumption change after scored PnL
  is visible unless a new plan explicitly preregisters a new experiment.
- Missing evidence is `NOT_RUN` or `UNAVAILABLE_FAIL_CLOSED`, never inferred PASS.
- Report gates only as `PASS`, `FAIL`, `NOT_RUN` or `BLOCKED`, backed by command,
  exit code, SHA, tree state and evidence paths.

## Execution discipline

- Use `/worktree-dispatch` before creating or assigning a lane.
- Use `/test-router` after code changes; run targeted tests after every
  integration pick. The full suite runs alone with zero heavy worker.
- Use `/gate-evidence` for release/research gates and `/trial-freeze` before any
  scored computation.
- Use `/pit-data-audit` for any new dataset or timestamped observable.
- Use `/reproduce-reconcile` before a terminal verdict.
- End delegated work with `/agent-handoff`.
- Do not claim visual, OOS, provider, live, paper, testnet or performance evidence
  that was not actually run and recorded.

## Forbidden without explicit owner authorization

- push, merge to `main`, delete/reset worktrees or branches, rewrite history;
- credentials, orders, leverage, paper/testnet/live deployment;
- purchases, paid provider activation or licensed raw-data commits;
- opening or scoring sealed S1 data.

The project hook blocks a narrow set of destructive shell commands. It is a
last-resort guard, not a substitute for the plans or the ownership manifest.
