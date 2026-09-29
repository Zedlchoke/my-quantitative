# LADDER_V1_APPENDIX — the superseded session-1 eligibility ladder (A1, 2026-09-29)

Purpose (skeptic F-18 / A7 prereview): the session-1 builder
(`build_portfolio_eligibility.py` v1) was rewritten in place by v2 before
any commit (the control dir is uncommitted pre-GO evidence by design), so
v1 is not recoverable from git. This appendix preserves v1's logic and
counts verbatim-from-construction so the package is self-contained. **v1
is dead law** — superseded by the owner's amendment; nothing downstream
consumes it. It is recorded because its 0-admissible headline governed
session 1's honest reporting.

## v1 ladder logic (novelty-gated, in force 2026-09-29 session 1 only)

Status ladder, most-specific first (F-0 = SLEEVE-FX5 court):

1. `DEAD_MECHANISM_F0` — the 15 DISTINCT_TESTABLE rows, with
   AUDUSD-S087/S088 reopen-pool `P_C_M1_REFETCH` (data-conditional kill)
   and USDCAD-S047 `P_D2_SYMBOL_DATA`.
2. `NOT_RUN_MECHANISM_DEAD_CLASS` — census VARIANT_OR_DUPLICATE (ancestry
   law forbade rescoring dead classes: 548 rows).
3. `NOT_RUN_NOT_FALSIFIABLE` — census NOT_FALSIFIABLE.
4. `NOT_RUN_NO_PRICE_DATA` / `NOT_RUN_VENUE_UNEVIDENCED` — symbol-level
   price gates (identical to v2).
5. `NOT_RUN_BLOCKED_COST` — census BLOCKED_COST.
6. `NOT_RUN_BLOCKED_DATA` — census BLOCKED_DATA.
7. `PIT_UNPROVEN` split into `POOL_VOLUME_PROFILE_M1` (3 rows: EURUSD-S010,
   USDJPY-S030, USDJPY-S056 — volume/tick-feature blocker on M1 pairs),
   `NOT_RUN_PIT_UNPROVEN_PHYSICAL/COT/MACRO`.

## v1 headline counts (1,200 rows)

| status | rows |
|---|---|
| NOT_RUN_MECHANISM_DEAD_CLASS | 548 |
| NOT_RUN_NO_PRICE_DATA | 330 |
| NOT_RUN_PIT_UNPROVEN_MACRO | 136 |
| NOT_RUN_NOT_FALSIFIABLE | 68 |
| NOT_RUN_VENUE_UNEVIDENCED | 47 |
| NOT_RUN_BLOCKED_DATA | 36 |
| DEAD_MECHANISM_F0 | 15 |
| NOT_RUN_PIT_UNPROVEN_COT | 10 |
| NOT_RUN_BLOCKED_COST | 9 |
| POOL_VOLUME_PROFILE_M1 | 3 |
| NOT_RUN_PIT_UNPROVEN_PHYSICAL | 1 |

Admissible-today under v1: **0** on all 12 assets. The 3 volume-profile
rows were candidates, not admissions. v1's cost-axis GBPUSD cell carried
the `COST_AUTHORY` typo (fixed in v2; owner-caught).

## Why v1 died (owner amendment 2026-09-29 #2)

v1 implemented the then-standing novelty/ancestry law (handbook §14.3 as
applied by the SLEEVE-FX5 F-0 court). The owner's amendment re-scoped the
question to portfolio-complementarity diagnostics with outcome-exposed
labels, making ancestry a label rather than a gate — v2/v2.1 implements
that. Both ladders agree on the data/PIT/cost/mechanization blocks; they
differ ONLY on the ancestry axis.
