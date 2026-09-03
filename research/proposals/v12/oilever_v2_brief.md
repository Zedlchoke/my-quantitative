# V12 OILEV-V2 brief — A12-V12-OILEVER-V2-DELEV (frozen)

New identity, cap-compatible. V11 `A8-V11-OILEVER-DELEV` was BLOCKED
pre-score (52/52 stamps |w|=0.5 > frozen 0.30 cap): **no PnL was ever
computed**, so this family is still outcome-blind. Raising the cap or
post-score renormalisation remains forbidden.

Mechanism unchanged: deleveraging/crowding through PIT OI flow/stock.
Feature definitions inherited unchanged from
`research/v11/families/oilever_delev/strategy.py`.

Arms:
- anchor `OILEV-V2-28D-FLOW-W`: 28d OI-flow;
- neighbour `OILEV-V2-56D-STOCK-W`: 56d OI-stock;
- control `OILEV-V2-28D-FLOW-W-INV`: sign-inverted 28d OI-flow
  (falsification: positive after-cost spread destroys the mechanism).

Frozen book (A4 construction, `research/v12/oilev_v2_book.py`): rank the
eligible universe by the frozen feature; when >=9 names are eligible take the
four lowest and four highest; equal weight per leg; frozen BTC beta hedge;
then uniformly scale the ENTIRE book when needed so every final absolute
weight <= 0.30. Never clip and renormalize individual names. BTCUSDT is a
context-only benchmark (never in the book).

Feasibility: PASS 52/52 stamps (>=9 eligible — observed min 19; exactly 4+4
legs; max |w| 0.125 <= 0.30; uniform scale never triggered)
(`research/audits/v12p/a4_oilev_v2_feasibility.json`). Open item for Q:
funding-events-while-held was UNAVAILABLE in A4's run and must be resolved
from the verified funding bundles before scoring.

Window/data: existing V11 S0 snapshot `2025-08-22..2026-08-21`, authorized
precisely because no OILEV PnL exists; bars 20/20 full, funding 20/20 zero
holes, OI 20/20 hash-match (`research/audits/v12p/a3_s0_snapshot_authorization.json`).

OILEV-V2 inherits no merit from being previously blocked: it must pass all
Stage-A gates fresh.
