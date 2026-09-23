# SHORT-SIDE FEASIBILITY NOTE — BTCUSDT-PERP (mechanism-neutral)

lane A2, cycle BTC-BEAR-OPPORTUNITY-RECON, measured 2026-09-23.
Scope: cost/execution FACTS only. No mechanism is proposed, no PnL is
computed, nothing is tuned. All funding numbers are decoded from the full
Vision fundingRate archive (2020-01..2026-08, 80 monthly files, sha-pinned in
`funding_sha256.json`) + REST backfill 2019-09-10..2019-12-31, split by the
census DOWNTREND windows in `downtrend_census.json` (primary PSV1 phase
label). Full numbers: `funding_in_downtrend.json`, events in
`funding_events.parquet`.

## 1. Fee stack (PSV1 frozen)

- Taker fee 5 bps + slippage 1 bps = **6 bps/side, symmetric** for long and
  short legs; round trip 12 bps; PSV1 cost tiers ×1.0/×1.5/×2.0 apply to the
  full stack. (lane_btc_h4 `pipeline/config.py`: TAKER_FEE_BPS=5.0,
  SLIPPAGE_BPS=1.0.) Nothing here re-prices or retunes them.

## 2. Funding is SIGNED — measured 2019-09-10 → 2026-09-22 (7,643 settlements)

Sign convention: funding > 0 → longs pay shorts → **a perp short RECEIVES
positive funding**; funding < 0 → shorts pay longs. BTCUSDT settles every
8h (`funding_interval_hours = 8` in all 80 archive files).

| population | n | mean /8h | median | min | max | share NEGATIVE |
|---|---|---|---|---|---|---|
| whole post-warmup window (2020-01-26 → 2026-09-22) | 7,228 | +1.073e-4 | +9.10e-5 | −3.0e-3 | +3.0e-3 | 14.2% |
| **WITHIN census DOWNTREND windows** | 1,472 | **+3.709e-5** | +4.71e-5 | −3.0e-3 | +6.23e-4 | **24.7%** |
| OUTSIDE DOWNTREND windows | 5,756 | +1.252e-4 | +1.00e-4 | −1.19e-3 | +3.0e-3 | 11.5% |

- **Headline: mean funding INSIDE measured downtrend windows is still
  POSITIVE (+3.71e-5 per 8h ≈ +4.06% annualized received by a short), not
  negative.** The prior "in downtrends funding is negative so shorts pay
  longs" is not the sample mode: negative settlements are ~2.2× more
  frequent inside downtrends (24.7% vs 11.5% outside) and the in−out mean
  gap is −8.81e-5/8h, but the average downtrend short still EARNS carry.
  Cumulative funding inside DOWNTREND windows over the whole sample:
  +5.46% of notional (sum of settlements).
- Tail: the worst single settlement inside a downtrend window is −0.30%
  of notional (the ±0.3% cap is binding in the extremes) — one bad 8h tick
  costs a short ≈ 2.5 round trips of fees. Max positive settlement inside
  downtrends is +6.23e-4.
- By year (mean/8h | negative share | in-DT mean | in-DT neg share):
  2020: 1.57e-4 | 14.9% | 2.27e-5 | 24.4% — 2021: 2.80e-4 | 7.3% | 7.44e-5 | 15.6% —
  2022: 3.80e-5 | 22.1% | 1.91e-5 | 35.2% — 2023: 7.18e-5 | 10.1% | 3.52e-5 | 18.6% —
  2024: 1.09e-4 | 8.4% | 4.99e-5 | 22.8% — 2025: 4.68e-5 | 12.9% | 4.22e-5 | 14.4% —
  2026 (to Sep 22): 2.39e-5 | 28.5% | 1.37e-5 | 33.7%.
- PSV1 froze `FUNDING_PER_8H = 1.377e-5` as its accounting constant. The
  measured full-window mean is ~7.8× larger. This disclosure does NOT
  retune the frozen constant; any new book must state which funding number
  it uses before scoring.

## 3. Margin / liquidation modeling a short book MUST add (gaps vs PSV1)

PSV1 accounting had **no margin engine** (linear costs, no equity path, no
liquidation logic). A perp-short book is invalid until it adds, at minimum:

1. **Maintenance-margin schedule → liquidation price** as a function of
   entry price, size, leverage and MMR tier (Binance BTCUSDT tiers — tier
   table not fetched in this recon; placeholder).
2. **Upside gap risk**: shorts are liquidated by UP moves; under PSV1's
   execution law (fill at next H4 open, no intra-bar fills) a bar can OPEN
   beyond the liquidation price. The accounting must define whether
   liquidation triggers on bar-open gap, on bar-high touch (conservative
   bound), or on a modeled mark path — none of these exists today.
3. **Funding cashflow accounting** at 00:00/08:00/16:00 UTC settlements on
   mark notional (section 2 numbers are the empirical input).
4. **ADL / partial-liquidation / insurance-fund interactions** — unmodeled
   placeholder; a forced-close is not a taker fill at 6 bps.
5. **Collateral treatment** for the USDT-margined linear contract (yield on
   collateral, haircuts) — unmodeled placeholder.

## 4. Borrow: perp vs spot-short (alternative-book note only)

A USDT-M perp short requires **no stock-loan/borrow**: it is an open sell
matched against an open interest counterparty. A spot-short alternative book
would instead require measured borrow availability + borrow fees + rebate
accounting — NOT measured in this recon; recorded as an alternative-book
requirement only.

## 5. Capacity / latency placeholders (PSV1 conventions)

No capacity, depth, market-impact or latency measurements exist in this
lane. Placeholder fields a later proposal must fill: adv/ participation
bound, impact model for taker shorts, settlement-timing congestion around
00/08/16 UTC, and data-tail live-funding source (REST, pinned at retrieval
per `PIT_DISCLOSURES.md`).

## 6. Facts that change what is proposeable (data layer only)

- Liquidation-print conditioning on BTCUSDT-PERP is **not measurable**
  (um tape absent entirely; cm sibling island stale since 2024-10).
- Tick top-of-book is **not measurable** outside the 2023-05..2024-04
  bookTicker island.
- Multi-year OI exists **only from 2020-09-01** (metrics daily, 5m,
  retrospective-only; REST OI history measured at ~41.6h).
- Funding, price and phase history over the frozen window: fully
  measurable, PIT-disciplined, and floors PASS (see `downtrend_census.json`).
