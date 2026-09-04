# FXFV3-A6-P2 — Cross-pair information diffusion at the daily clock: leave-one-out basket lead-lag

Lane: FOREX-FREE-V3 / D1 / A6
Label: **RESEARCH_CANDIDATE_NOT_LIVE_READY**
Status: outcome-blind proposal. No returns, PnL, or backtest were computed or inspected in this lane.
Conditioning: **macro-free** (authorized H1 price snapshot only; the macro series enters only the mandated financing column).

---

## 1. Economic mechanism

Currency pairs share a common G10 factor and the information that moves it is
incorporated into related pairs with a measurable lag: returns show positive
cross-autocorrelation and a lead-lag structure produced by slow capital
reallocation and inattention (Lo & MacKinlay 1990; Hou 2007). The mechanism trades
that diffusion channel at the daily decision clock: for each pair i, the
**leave-one-out mean of the other six pairs' just-completed daily returns** is the
common-factor lead; pair i is held in the lead's direction for one frozen horizon.
The tradeable object is the CROSS-pair lag structure — not the pair's own past
return (that is the control's job to expose), not a same-period dispersion spread,
not any price-structure break.

## 2. Definitions (frozen; completed bars only)

- **Decision instant T**: completion of the daily 16:00 America/New_York flat bar
  (20:00Z EDT / 21:00Z EST via zoneinfo). One decision per pair per NY trading day;
  inherited session gate (Sun 21:00 → Fri 16:00 NY).
- **r_i(T)** = log return between consecutive completed 16:00-NY closes of pair i
  (weekend = one return). **lead_i(T)** = mean of r_j(T) over the 6 pairs j ≠ i
  (the pair's own return is excluded — the self ingredient lives only in the
  control arm). **direction** = sign(lead_i(T)); exact zero => NO_EVAL.
- Warmup: one completed prior NY-day (50 H1 bars with buffer). Fail-closed
  throughout: any missing bar => NO_EVAL / voided signal, never fill-forward.

## 3. Arms (exactly three)

| arm | definition | role |
|---|---|---|
| anchor | hold direction_i for **5 daily periods**; entry at next 16:00-NY bar open; one position per pair; force-flat at fold boundaries | validates the diffusion mechanism |
| neighbour | identical except holding = **2 daily periods** | same presumption, shorter horizon; must move together with anchor |
| control | identical except direction_i = sign(r_i(T)) — the pair's **own** lag-1 daily return | destroys exactly the cross-pair ingredient |

**Preregistered non-reproduction rule (control):** the family FAILS regardless of
anchor sign if control expectancy > 0 AND PF >= 1.10, or control expectancy >=
0.5 × anchor expectancy (a firing self-lag control means the anchor is generic
time-series momentum, not diffusion).

**Incremental benchmark (macro-free case):** the same mechanism under the
**placebo control schedule** — identical law with the lead read at T−2 NY-days
(stale diffusion information; schedule shape, cadence and costs identical). Gate:
anchor expectancy minus placebo expectancy > 0. Distinct from the control: the
placebo tests WHEN the information is used; the control tests WHETHER the
cross-pair ingredient matters.

## 4. Dual book and financing (frozen)

Every cell books BOTH `price_only_pnl_usd` and `financing_adjusted_pnl_usd`.
Formula frozen verbatim: `financing_adjusted_pnl = price_only_pnl + sign *
notional_usd * (r_base − r_quote) * holding_days/365`, accrued per calendar day at
the day-start as-of adopted policy-rate differential (availability-gated; never
effective-date-alone). **Disclosed approximation:** policy rates are unsecured
official rates, not swap/OIS rollover. **Gate:** the price-only book (this
family's primary object) must not be sign-inverted by the financing term.

## 5. Costs (frozen, F1-fixed)

1.5 bps/side base; tier ladder {1.0: 1.5, 1.5: 2.25, 2.0: 3.0} bps/side applied to
BOOKED stress PnL via the P1 kernel `book_stress` (base/1.5/2.0 rows pairwise
distinct when trades non-empty). One-event delay stress as a SEPARATE component.
Break-even bps per cell mandatory. **Disclosed ex ante:** the cadence is
cost-heavy — ~1 RT per ~6 NY-days needs ~3 bps gross per 5-day trade (~0.6
bps/day); if documented diffusion edges are smaller, the family dies to costs and
the reject is attributed honestly.

## 6. Turnover, folds, gates

- Decisions: ~1,600/pair (~11,000 total) >> the 40-decision floor. Trades: est.
  33–45 RT/pair-year, ~1,750–2,000 full sample. Floors: full-sample aggregate
  anchor min 900 trades; per-populated-fold 250 (inherited 30-trade population
  rule).
- Folds frozen [2020-03-01, 2022-05-01, 2024-07-01, 2026-09-02], purge 14d,
  force-flat at boundaries. Stage-A: expectancy > 0, PF >= 1.10, >= 2/3 folds
  positive, stress > 0 with multipliers applied, concentration (no pair > 40% of
  gross positive PnL), drop-one (>= 5/7, leads recomputed on the reduced set).
- USD-drift: the leave-one-out lead is a common-factor signal and the book can
  load on the USD factor; the inherited diagnostic (|corr| <= 0.3 over >= 60
  days) applies unchanged and FAILS the family if the edge is USD-wide drift
  rather than diffusion. Disclosed ex ante, not tuned around.

## 7. Falsification (preregistered)

Negative anchor => no after-cost cross-pair diffusion edge at frozen costs
(complete reject; break-even bps attributes cost vs gross absence). Control fires
=> generic momentum, cross-pair claim falsified. Incremental alpha <= 0 vs the
lag-2 placebo => schedule drift, not fresh diffusion. Neighbour diverges =>
knife-edge horizon. USD diagnostic flags => USD common factor, not diffusion. No
sign inversion, no horizon rescue, no pair subset, no lower cost, no re-clocking
of any forbidden row.

## 8. Trial count and novelty

7 anchor + 7 neighbour + 7 control cells + bench auxiliary schedule; one frozen
parameter set per arm (leave-one-out lead; horizons 5/2; placebo lag 2); no grid.
Novelty: no session clock, no range/channel/breach, no fade, no dispersion spread;
not a re-clock of any of the four forbidden rows (none is a cross-pair lead-lag
construction); vs FXFV2-A5: next-period continuation at daily grain, not
same-session dispersion convergence; vs FXFV2-A6-P1: no compression gate or
channel; honest adjacency note: a firing self-lag control is precisely the
generic-momentum case the preregistered rule rejects.

## 9. Sources

- Lo, A. W., MacKinlay, A. C. (1990). *When Are Contrarian Profits Due to Stock
  Market Overreaction?*, Review of Financial Studies 3(2), 175–205.
  https://academic.oup.com/rfs/article/3/2/175/1595488 — VERIFIED_METADATA via
  search 2026-09-04.
- Hou, K. (2007). *Industry Information Diffusion and the Lead-Lag Effect in
  Stock Returns*, Review of Financial Studies 20(4), 1113–1138.
  https://www.jstor.org/stable/4494798 — VERIFIED_METADATA via search 2026-09-04.
- Hong, H., Torous, W., Valkanov, I. (2007). *Do Industries Lead the Stock
  Market?* — title verified via related-literature listing in the Hou search;
  venue/year recalled (JFE) and NOT independently re-verified. Supporting
  citation only.
- Transfer claim (equity-market cross-asset lead-lag transfers to daily-grain G10
  FX pairs on free data 2020–2026): UNVERIFIED — the hypothesis under test.

Written outcome-blind 2026-09-04T13:59:00Z; full packet discipline, source-to-test
map and signed attestation in `proposal_2.json`.
