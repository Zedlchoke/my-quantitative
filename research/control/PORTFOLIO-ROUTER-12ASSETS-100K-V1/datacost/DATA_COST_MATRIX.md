# DATA_COST_MATRIX — A1-consolidated (PORTFOLIO-ROUTER-12ASSETS-100K-V1, 2026-09-28)

Consolidates Lane L1's evidence (`DATA_COST_MATRIX_DRAFT.md` +
`PIT_SOURCE_TABLE.md`, same dir) into the program's binding eligibility view.
Pre-GO: this is a research matrix, not a trading mandate. Every FLAT below is
fail-closed per mission law — it flips to ELIGIBLE only when the named owner
action lands AND a PIT/cost gate passes.

## Eligibility table (12/12 symbols decided — no symbol forced into a trade)

| Symbol | Cluster | Backtest vehicle | Price history (repo evidence) | Cost authority | Verdict | Single unblock (owner action) |
|---|---|---|---|---|---|---|
| EURUSD | USD-bloc | FX spot (IDEALPRO-class; 6E alt.) | M1 bid/ask 2021-01→2026-09 (2,092 files/side, fx-rangefade worktree) + spread census p50 0.3 pip | spread 1/24 buckets measured; commission/swap UNMEASURED (pessimistic defaults per L3) | **ELIGIBLE** | IBKR Activity/Flex statement → measured commission/swap |
| GBPUSD | USD-bloc | FX spot | M1 2021-01→2026-09 (fx-majors-search worktree); census p50 0.8 pip | same class | **ELIGIBLE** | same statement |
| USDJPY | USD-bloc | FX spot | M1 2021-01→2026-09; census p50 0.5 pip | same class | **ELIGIBLE** | same statement |
| USDCAD | Comm-FX | FX spot | H1 bars 2021-01→2026-06 (erp1-tracka repro_twin; raw M1 not physically present; Duka re-fetch SNI-blocked) | same class | **ELIGIBLE** (H1 ceiling disclosed) | re-fetch decision if M1 needed |
| AUDUSD | Comm-FX | FX spot | H1 2021-01→2026-06 (30,420 rows, same) | same class | **ELIGIBLE** (H1 ceiling disclosed) | same |
| NZDUSD | Comm-FX | FX spot | MISSING (no corpus; spread never measured) | none | **FLAT_BLOCKED_DATA** | one M1-history source decision |
| USDCHF | USD-bloc | FX spot | MISSING (absent from both IBKR probes) | none | **FLAT_BLOCKED_DATA** | same single source decision |
| XAUUSD | Precious | spot metal | TD/TwelveData daily 1979→2026-09 ARCHIVE/REFERENCE only (sha 49c2684e…); venue ≠ executable; PIT lag unmeasured | IBKR London Gold prospective n=1; fees STATED not measured | **FLAT_PIT_UNPROVEN** | resume frozen bounded IBKR probe + ≥20-day overlap evidence |
| XAGUSD | Precious | spot metal | MISSING (0 bytes; COMEX transport-blocked) | none | **FLAT_BLOCKED_DATA** | one metals-history decision |
| BRENT | Energy | continuous futures or CFD (TBC) | MISSING (no price/roll/term series) | none | **FLAT_BLOCKED_DATA** | one energy continuous-futures decision (covers all 3 energies) |
| WTI | Energy | same | MISSING | none | **FLAT_BLOCKED_DATA** | same single decision |
| NATGAS | Energy | same | MISSING + no weather-forecast PIT archive | none | **FLAT_BLOCKED_DATA** | energy decision + weather archive decision |

**Initial executable universe = 5 FX pairs (EURUSD GBPUSD USDJPY USDCAD AUDUSD);
7/12 symbols FLAT by data authority.** The router policy is written for 12
columns; FLAT is a legitimate standing state per symbol — the owner's "đủ 12
tài sản nhưng không ép 12 lệnh" is satisfied by the matrix, not by fabricating
data. Energy/metals columns activate only through their named unblock + gates.

## Hard laws (binding)

1. **No vehicle PnL mixing** — spot, futures and CFD books are never pooled
   into one equity curve; a vehicle switch is a new preregistered identity.
2. **Prospective ≠ historical** — IBKR cost-band streaming (from 2026-09-28)
   prices future execution assumptions only; it is never joined as history.
3. **PIT join rule** — macro series join on the date the investor could FIRST
   know (publication timestamp), never the date the data describes (event/
   effective date). Only SOFR/EFFR has evidenced PIT today; every other macro
   source (COT, EIA, GDT, SNB, OIS, TIPS, DXY, VIX, OVX, BTP-Bund, weather)
   needs its `PIT_SOURCE_TABLE.md` gate passed first — see that file for the
   per-source event/publication/vintage rules.
4. **Missing cost authority ⇒ pessimistic default** (L3's UNMEASURED register
   U1–U18), never a favorable assumption; measured values replace defaults
   only via owner-supplied evidence (statements/probes).
5. UNAVAILABLE ≠ 0 anywhere in the portfolio accounting (SHARED-PORTFOLIO
   precedent inherited).

Detail, per-source PIT rules and evidence paths: see `DATA_COST_MATRIX_DRAFT.md`
and `PIT_SOURCE_TABLE.md` (Lane L1, same directory). Cost kernel and $100k
accounting: see `cost/COST_ACCOUNTING_SPEC.md` (Lane L3).
