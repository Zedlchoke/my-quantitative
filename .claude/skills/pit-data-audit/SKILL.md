---
name: pit-data-audit
description: Audit whether crypto, stock, or forex data was actually knowable at decision time, including timestamps, revisions, universe membership, corporate actions, sessions, funding, borrow, rollover, and provider lineage.
allowed-tools: Bash, Read, Grep, Glob
---

# Point-in-time data audit

Select exactly one asset profile from [asset-checklists.md](references/asset-checklists.md).
For every input field record source, raw timestamp, publication/availability
timestamp, timezone, revision policy, identifier, coverage, missingness, license,
and transformation digest.

Prove with adversarial fixtures that a row unavailable at decision time cannot
enter features, universe selection, costs, labels, fills, benchmarks, folds, or
controls. Apply the one-bar/declared execution lag after availability, not merely
after an event's economic date.

Fail closed on unknown timestamps, survivorship-only membership, silent forward
fill, revised fundamentals without vintage, midpoint-as-fill, or missing provider
lineage. A plausible value is not point-in-time evidence.
