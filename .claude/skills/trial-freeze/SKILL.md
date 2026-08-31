---
name: trial-freeze
description: Freeze immutable family, arm, data, code, window, cost, control, budget, and observed/published trial identities before any scored S0 computation.
allowed-tools: Bash, Read, Grep, Glob
---

# Trial freeze

Before scoring, create the PLAN-required selection/run contract and satisfy
[freeze-contract.md](references/freeze-contract.md). Hash canonical serialized
content, not mutable paths. Verify exact arm keys with a temporary-ledger dry run:
first publication succeeds, replay is idempotent, collisions fail, counters
remain isolated, and no S1 path is touched.

A freeze is invalid when any family/arm/control, parameter, universe, provider,
window, fold, lag, cost, benchmark, stress, terminal policy, code SHA, data digest,
or trial key remains implicit. After the first scored metric is visible, do not
edit the freeze, replace a cell, or recover unused budget from an observed result.
