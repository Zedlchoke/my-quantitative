# DAYTRADER-100-V1 — G3 FREEZE ADDENDUM r1 (pre-PnL)

- recorded_utc: 2026-09-28, AFTER the G3 freeze commit 8b69d11d, BEFORE any
  scored PnL (the only numbers seen so far are dry-run decision COUNTS — no
  expectancy/PF/PnL at any depth; dry-run output schema excludes them).
- owner instruction #2, verbatim:

> "vậy là mở thêm các strategy mà trước bị thiếu những dữ kiện mà giờ đã có nhé"

## 1. Scope delta (owner-authorized)

Two families move BLOCKED → RUNNABLE via the keyless channel proven this
session (288/288 premium+funding fetch, HTTP 200 measured):

| family_id | strategy (census #) | newly-present dữ kiện | arms |
|---|---|---|---|
| DT100-46-CARRY | #46 cash-and-carry (funding harvest) | SPOT 1m BTCUSDT 2020-09..2026-08 (keyless fetch) | A/N1/N2 (band 1.5/1.0/2.0) |
| DT100-95-BASISTERM | #95 perp-vs-quarterly basis divergence | quarterly futures 1m (last-Friday contracts, continuous ≥30d-to-expiry roll) + premium index | A/N1/N2 (band 1.5/1.0/2.0) |

Totals: 27 → **29 families**, 81 → **87 scored-cell candidates** (ledger errata
below). FUNDCONTRA (#35) and FORECASTFUND (C1) were already in the base freeze
— their missing dữ kiện (funding/premium bytes) landed earlier this session.

Carry semantics frozen: spread = log(spot) − log(perp); enter long spread when
perp-premium z > band; costs ×2 legs; funding charged with sign −1 vs the
synthetic direction (short perp RECEIVES positive funding — income, not cost;
the exact opposite of a mismodeled constant).
BASISTERM semantics frozen: dz = z(term basis) − z(perp premium); dz > band →
SHORT the tradeable spread (short quarterly, long perp); PnL marks on
log(quarterly) − log(perp), never on the z-score.

## 2. Pre-PnL corrections (disclosed, no outcome was visible)

1. **FX loader rewritten**: the Dukascopy estate is day M1 **.bi5 candle files**
   (LZMA, 24-byte `>5if`, open-close-low-high order, points×1e5/1e3) — the
   first dry-run's CSV glob found nothing (18 FX rows NOT_RUN). Now parses the
   VERIFIED layout from EURUSD-OPEN-SEARCH-V1's duka_lib (reused semantics,
   cited). o/h/l/c = mid of the two sides; per-bar spread measured from the
   two closes (the billed quantity).
2. **Extra-key wiring**: `lead/other/legs` live at arm-spec top level; the
   first dry-run's TECHABORT rows (LEADLAG/pairs KeyError) are fixed.
3. **Control parity invariant corrected**: parity = FIRED-BAR count preserved
   under clock_shadow (trade counts legitimately differ when permuted
   directions merge/split). The dry-run checker now compares fired bars.
4. **BASISTERM direction inversion fixed pre-PnL** (dz>band must be short
   spread — convergence bet), caught during implementation review before any
   scored run.

## 3. Honest verdicts expected (no rescue)

- DT100-87-FVG fired ZERO times on BTC 1m across all arms in dry-run #1
  (literal 3-bar gap detector; 1m continuous data rarely gaps). Verdict at
  scoring: NOT_RUN_THIN/VACUOUS_ON_SUBSTRATE. No re-spec, no rescue —
  consistent with the DTP playbook-corpus death (11/11).
- DT100-34-WEEKEND n2 (band 2.0): 8 trades total → NOT_RUN_THIN verdict stands.

## 4. The other 26 blocked families — unchanged

The owner frontier table (OWNER_FRONTIER_STATUS_2026-09-28.md) adds L2 spot
(10 min), on-chain RPC (live), Deribit options (snapshot), IBKR live quotes
(5 pairs) — all prospective from 2026-09-28. None backfills multi-year history;
those families stay `NOT_RUN_DATA_BLOCKED_UNDER_OWNER_ORDER` for historical
scoring. Collector contracts for forward accumulation are an owner-gated
separate decision (recorded in the frontier note).

## 5. Ledger errata

Header row budget_max_scored_cells 81 → **87** by this addendum (errata row
appended to TRIAL_LEDGER.jsonl referencing the header; denominators unchanged
0/0).
