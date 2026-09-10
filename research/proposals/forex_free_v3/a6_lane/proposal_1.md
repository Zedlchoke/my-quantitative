# FXFV3-A6-P1 — Realized-volatility regime-gated policy-rate-differential carry at the daily decision clock

Lane: FOREX-FREE-V3 / D1 / A6
Label: **RESEARCH_CANDIDATE_NOT_LIVE_READY**
Status: outcome-blind proposal. No returns, PnL, or backtest were computed or inspected in this lane.
Conditioning: **macro-conditioned** — adopted BIS WS_CBPOL policy-rate vintages (fallback: ECB SDMX EXR), PIT availability-gated.

---

## 1. Economic mechanism

UIP fails in a signed direction: the higher-policy-rate currency tends to appreciate
rather than depreciate by the differential (Fama 1984 forward-premium puzzle). But
differential-directed exposure carries crash risk concentrated in high-volatility
states: carry crashes coincide with global turbulence and rising volatility
(Brunnermeier, Nagel & Pedersen 2009), and carry returns load negatively on global
FX volatility innovations (Menkhoff, Sarno, Schmeling & Schrimpf 2012). The
mechanism therefore holds the per-pair differential direction **only while the
pair's own smoothed realized range sits in the LOW tail of its trailing block
distribution**, and unwinds to flat in the HIGH state. Direction comes exclusively
from adopted policy-rate vintages read point-in-time; the volatility state is a
holding gate, never a price-structure trigger.

## 2. Definitions (frozen; completed bars and availability-gated vintages only)

- **Decision instant T**: completion of the daily 16:00 America/New_York flat bar
  (20:00Z EDT / 21:00Z EST via zoneinfo). One decision per pair per NY trading day.
- **asof_diff_i(T)** = r_base(T) − r_quote(T) over the 8 areas {US, EMU, GB, JP,
  CH, CA, AU, NZ}, where r_area(T) is the latest BIS WS_CBPOL vintage with
  `available_time_utc <= T`. BINDING: a row is eligible at T only when
  available_time_utc <= T; CBPOL rows are never eligible on their own effective
  date; rows without owner ReleaseEvidence fail closed
  (MISSING_AVAILABLE_TIME_EVIDENCE). Missing leg => pair-day NO_EVAL.
- **Direction** = sign(asof_diff_i(T)); +1 = long base / short quote; exact zero
  => NO_EVAL.
- **rr_d** = (sum of H1 true ranges in NY-day d's window) / (d's 16:00-NY close);
  all of d's bars must exist.
- **vol_state(T)**: S = mean rr over the last 20 NY-days; B = median of the 10
  prior non-overlapping 20-day block means. LOW iff S < B (median split; no tuned
  threshold). Requires 220 completed NY-days, else NO_EVAL. First decisions land
  inside fold F1 (~2020-11).
- Fail-closed throughout: missing bars/vintages/warmup => NO_TRADE, never
  fill-forward. Live-fetch warmup coverage of the macro series is
  NOT_PROVEN_ON_LIVE_FETCH and must be proven at the P3/Q gates before conditioning
  is scored (disclosed per data_authority_v3.json).

## 3. Arms (exactly three)

| arm | definition | role |
|---|---|---|
| anchor | LOW state => hold differential direction; HIGH => flat; sign flip => reverse; entry/exit at next 16:00-NY bar open | validates the gated mechanism |
| neighbour | identical except the state input is the 20-day close-to-close return std vs its 10 prior block stds (same presumption, different estimator) | must move TOGETHER with anchor; divergence = knife-edge measurement |
| control | identical except direction = sign of a SHAM leg-pair's differential under a frozen derangement (base/quote legs rotated +2 along the pair order: EUR/USD→(AUD,USD), GBP/USD→(NZD,USD), AUD/USD→(USD,JPY), NZD/USD→(USD,CHF), USD/JPY→(USD,CAD), USD/CHF→(EUR,USD), USD/CAD→(GBP,USD)) | destroys exactly the pair-specific differential ingredient |

**Preregistered non-reproduction rule (control):** the family FAILS its control
gate regardless of anchor sign if control expectancy > 0 AND PF >= 1.10, or
control expectancy >= 0.5 × anchor expectancy.

**Incremental benchmark (macro conditioning removed):** identical law with the
as-of differential frozen at a **+270-day availability lag** (round constant, ex
ante). Gate: anchor financing-adjusted expectancy minus benchmark expectancy > 0.
Fresh policy-rate information, not the trading law alone, must carry the value.

## 4. Dual book and financing (frozen)

Every cell books BOTH `price_only_pnl_usd` and `financing_adjusted_pnl_usd`.
Formula frozen verbatim: `financing_adjusted_pnl = price_only_pnl + sign *
notional_usd * (r_base − r_quote) * holding_days/365`, accrued per calendar day at
the day-start as-of differential. **Disclosed approximation:** policy rates are
unsecured official rates, not swap/OIS rollover. **Gate:** the price-only book
must not invert the anchor expectancy sign — the financing term cannot manufacture
the edge. Series authorization never self-authorizes the strategy.

## 5. Costs (frozen, F1-fixed)

1.5 bps/side base; tier ladder {1.0: 1.5, 1.5: 2.25, 2.0: 3.0} bps/side applied to
BOOKED stress PnL via the P1 kernel `book_stress` (base/1.5/2.0 rows pairwise
distinct when trades non-empty). One-event delay stress carried as a SEPARATE
component, never blended into cost tiers. Break-even bps per cell mandatory; a
reject is attributable to cost vs absence of gross edge.

## 6. Turnover, folds, gates

- Decisions: ~1,600/pair (~11,000 total) >> the 40-decision floor. Trades: est.
  3–10 RT/pair-year (state transitions + sign reversals), ~140–455 full sample.
  Floors: full-sample aggregate anchor min 140 trades; per-populated-fold 30
  (inherited population rule).
- Folds frozen [2020-03-01, 2022-05-01, 2024-07-01, 2026-09-02], purge 14d,
  force-flat at boundaries. Stage-A: expectancy > 0, PF >= 1.10, >= 2/3 folds
  positive, stress > 0 with multipliers applied, concentration and drop-one
  (>= 5/7) survival, USD-drift diagnostic (|corr| <= 0.3, >= 60 days) — a
  differential book may legitimately load on USD-wide rates; if the inherited
  diagnostic flags it, the family FAILS, disclosed ex ante.

## 7. Falsification (preregistered)

Negative anchor => no after-cost edge for vol-gated differential carry at frozen
costs (complete reject; break-even bps attributes cost vs gross absence). Control
fires => differential not operative. Incremental alpha <= 0 => fresh macro
information worthless; conditioning claim falsified. Price-only book inverts the
sign => financing manufactured the edge; fail. Neighbour diverges => knife-edge
state; not promotable. No sign inversion, no threshold/lookback rescue, no pair
subset, no lower cost, no re-clocking of any forbidden row.

## 8. Trial count and novelty

7 anchor + 7 neighbour + 7 control cells (3 arms × 7 pairs) + bench auxiliary
schedule; one frozen parameter set per arm (20-day blocks, 10 blocks, derangement
rotation, +270d lag); no grid. Novelty: no session clock, no range break, no fade,
no compression-to-expansion trigger anywhere; not a re-clock of any of the four
forbidden rows (none is a differential-direction or vol-gated mechanism); no
result-aware reuse of V1/V2 packets.

## 9. Sources

- Fama, E. F. (1984). *Forward and Spot Exchange Rates*, J. Monetary Economics
  14(3), 319–338. UNVERIFIED_METADATA (recalled; search rate-limited).
- Brunnermeier, M. K., Nagel, S., Pedersen, L. H. (2009). *Carry Trades and
  Currency Crashes*, NBER Macroeconomics Annual 23, 313–348.
  https://www.nber.org/papers/w14473 — VERIFIED_METADATA via search 2026-09-04.
- Menkhoff, L., Sarno, L., Schmeling, M., Schrimpf, A. (2012). *Carry Trades and
  Global Foreign Exchange Volatility*, Journal of Finance 67(2), 681–718. doi
  10.1111/j.1540-6261.2012.01728.x — VERIFIED_METADATA via search 2026-09-04.
- Transfer claim (vol-gated policy-rate carry earns after-cost, financing-robust
  edge on free G10 data 2020–2026): UNVERIFIED — the hypothesis under test.

Written outcome-blind 2026-09-04T13:59:00Z; full packet discipline, source-to-test
map and signed attestation in `proposal_1.json`.
