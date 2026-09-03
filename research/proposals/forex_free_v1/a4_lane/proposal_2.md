# FXFV1-A4-P2 — London-morning → New-York-overlap intraday continuation

Lane: FOREX-FREE-V1 / F4 / A4 (intraday session-structure timing perspective)
Label: **RESEARCH_CANDIDATE_NOT_LIVE_READY**
Status: outcome-blind proposal. No returns, PnL, or backtest were computed or inspected in this lane.

---

## 1. Economic mechanism

The FX day has a documented, deterministic activity clock: activity peaks in
the London morning and the NY overlap and troughs in the Asian afternoon
(Andersen & Bollerslev 1997). Intraday momentum — an early-session
directional move persisting into the late session — is documented in US equity
index futures (Gao, Han, Li & Zhou 2018: first half-hour predicts last
half-hour). This proposal transfers that pattern onto the FX session clock:
the directional move accumulated over the London morning (08:00–11:00 London
completed bars) predicts continuation through the London afternoon and the
NY-morning overlap. Mechanically: timezone-constrained hedgers and slower
participants transact into the overlap, order-flow imbalance takes hours to
diffuse, and 08:30 NY macro releases land inside the holding window on trend
days.

Profit source: persistence of flow imbalance in the highest-liquidity window
of the FX day. Loss source: overlap-ending mean reversion and profit-taking
into the NY afternoon; range days where the morning move is the entire
excursion. Counterparty on winners: dealers and fast accounts still
repositioning into the overlap. Counterparty on losers: late-overlap
liquidity providers fading the extension.

Why threshold-free: the anchor has **zero free parameters** — every valid day
trades the sign of the morning move. There is no filter level to tune, so the
mechanism either survives frozen conservative costs or is falsified. Why no
volume: FX volume is decentralized; the mechanism is price-only.

## 2. Definitions (frozen; completed bars only)

Canonical data: Twelve Data H1 OHLC, UTC bar-open stamps, deduped canonical
series, 2020-01-29 → 2026-09-02, 7 pairs. A bar is actionable only at its
completion instant (open stamp + 1h).

**Signal.** `R = close(bar stamped 11:00 Europe/London) − close(bar stamped
07:00 Europe/London)` — the cumulative return of the 4 completed H1 bars
stamped 08, 09, 10, 11 London. All 4 bars must be canonical and in-calendar
(true every Mon–Fri: London 07:00–11:00 always follows the Sunday 21:00 NY
weekly open). Direction = `sign(R)`; `R = 0` → no trade that day; no
magnitude filter.

**Entry.** Fill at the open of the next allowed bar after the 11:00-London
bar completes — the 12:00-London-stamped bar (~07:00 NY-equivalent) —
provided that open maps to a NY wall-clock time strictly before 15:00
America/New_York; otherwise the signal is discarded.

**Exit (single, mandatory).** Every position exits with fill at the open of
the H1 bar stamped **15:00 America/New_York** (completion 16:00 NY — two full
hours strictly before the 17:00 NY rollover instant). No stop, no target.
Same rule on Friday, where the 15:00 NY bar is the last bar of the week
(frozen weekly close Fri 16:00 NY). Holding window ≈ 07:00→15:00 NY,
entirely inside the London-afternoon/NY-morning activity peak.

**Flat invariant.** No fill may execute at a bar open at or after 15:00 NY.
The book is flat from 15:00 NY wall clock, strictly before every 17:00 NY
rollover under any bar-stamping convention, and never spans a rollover
instant or the weekend. Financing exposure is zero by construction.

## 3. Anchor / neighbour / negative control

| arm | definition | role |
|---|---|---|
| anchor | `R` over London stamps 08–11 (close-to-close from 07:00 London); enter `sign(R)` at 12:00 London open; single 15:00 NY flatten exit | validates: real session-continuation should survive frozen conservative costs threshold-free |
| neighbour | `R' = close(12:00 London) − close(07:00 London)` (5 bars, stamps 08–12); entry at 13:00 London open; exit unchanged | preregistered one-bar adjacency: a window-anchored flow phenomenon shifts smoothly; a snooped spike does not |
| negative control | same rule in Tokyo: `R_t = close(12:00 JST) − close(08:00 JST)` (stamps 09–12 JST); entry at 13:00 JST open; same 15:00 NY flatten; Mondays structurally invalid (Mon 08:00 JST precedes the Sunday 21:00 NY open) | destroys: if threshold-free continuation is equally strong in the Tokyo-midday activity trough, the anchor is generic daily momentum, not session structure — reject |

The control holds the rule, the (empty) threshold, the execution machinery
and the exit constant, and moves only the session of signal formation and
entry — it isolates the timing channel. No other variants are evaluable;
anything more is a grid.

## 4. Frozen cost stress (frozen 2026-09-03, before any returns)

Identical lane-level matrix as FXFV1-A4-P1. Round trip = one full proxy spread
charged once: `net_log_return = log(exit_open / entry_open) − cost_bps × 1e-4`.
Delay stress shifts every execution one additional completed bar later; a
delayed flatten that would land at/after the 15:00 NY boundary collapses into
the 15:00 NY flatten fill (the invariant is never violated by the stress).

| pair | ×1.0 (bps rt) | ×1.5 | ×2.0 |
|---|---|---|---|
| EUR/USD | 2.0 | 3.0 | 4.0 |
| GBP/USD | 3.0 | 4.5 | 6.0 |
| AUD/USD | 3.0 | 4.5 | 6.0 |
| NZD/USD | 4.0 | 6.0 | 8.0 |
| USD/JPY | 2.0 | 3.0 | 4.0 |
| USD/CHF | 3.0 | 4.5 | 6.0 |
| USD/CAD | 3.0 | 4.5 | 6.0 |

Proxies are set near twice typical ECN all-in round-trip costs for these
majors (UNVERIFIED practitioner levels — stress inputs only, never a live
spread claim). This mechanism trades nearly every day with no stop, so cost
survival **is** the primary scientific gate and is expected a priori to be the
binding constraint; that honesty is the design.

## 5. Falsification rule (preregistered)

Per pair per arm: mean per-trade net return (bps) with day-clustered t-stat
and trade count, under the stated stress cell. Evaluated only in the later
authorized phase; nothing here inspects outcomes.

- **V1 viability** — FAIL if <4 of 7 pairs have mean net trade expectancy > 0
  at ×1.0/no-delay, OR <4 of 7 at ×1.5/one-bar-delay.
- **V2 session causality** — FAIL if anchor (×1.0) does not beat the Tokyo
  control (×1.0) in ≥5 of 7 pairs.
- **V3 neighbour robustness** — FAIL if Spearman(anchor, neighbour) mean net
  expectancy across the 7 pairs < +0.5.
- **V4 cost fragility** — FAIL if expectancy sign differs between ×1.0 and
  ×2.0 in ≥5 pairs (stricter than P1's K4: exposure here is near-continuous).

Survival requires V1 ∧ V2 ∧ V3 ∧ ¬V4. Any other outcome falsifies the proposal
as specified. No re-specification, no filter added post hoc, no window change
after any return is visible.

## 6. Expected regimes and preregistered heterogeneity

Favours: high-liquidity trend days; macro-heavy mornings (08:30 NY releases
inside the window); weeks when London and NY agree. Adverse: range weeks;
risk-off illiquid episodes; holiday-thinned sessions; Japan-centric days when
Asian hours carry the information. Preregistered sub-prediction (not a kill
rule): continuation strongest in EUR/USD and GBP/USD, weakest in USD/JPY.

Structural bounds (design facts, not results): threshold-free → ~1 trade per
valid day, order of magnitude ~1,300 trades/pair over ~6.59y (anchor;
Tokyo control loses Mondays structurally).

## 7. DST session clock

Frozen calendar: Sunday 21:00 America/New_York open → Friday 16:00 close;
rollover 17:00 NY; all boundaries via zoneinfo named zones (matches
`DEFAULT_FX_WEEK_CONVENTION`, `research/assets/forex/sessions.py`). Bars are
UTC-stamped; London/Tokyo/NY labels derived per bar via zoneinfo; UTC→zone is
single-valued so fall-back is unambiguous. US/UK DST transitions occur on
Sundays outside all Mon–Fri windows used here, so no window or the flatten
boundary is ever truncated by a transition on a trading day. During the
~2–3 weeks/year of US/UK DST desync, the London-keyed entry drifts one hour
against NY; zoneinfo handles this exactly and no special case is made.

## 8. Trial count (frozen)

7 anchor + 7 neighbour + 7 negative-control cells = **21 evaluation cells**;
6 stress cells each; 1 statistic set each; 0 free anchor parameters
(threshold-free by design); 1 preregistered neighbour; 0 further variants; no
grid search. Frozen 2026-09-03T08:26:56Z, before any return/PnL/backtest
computation.

## 9. Data contract compliance

Uses only Twelve Data H1 closes + UTC open stamps for the 7 authorized pairs
over the authorized window. Volume (null), bid/ask, rollover/financing, D1/H4
series, and all other providers are not used. The frozen prior-cycle directory
`research/proposals/forex/` was not opened.

## 10. Sources

- Gao, L., Han, Y., Li, S. Z., Zhou, G. (2018). *Market Intraday Momentum*,
  Journal of Financial Economics 129(2), 394-414.
  https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 —
  retrieved 2026-09-03T08:26:56Z. VERIFIED_METADATA via search. Established
  for US equity index futures; the FX transfer is this proposal's hypothesis
  (UNVERIFIED).
- Andersen, T. G., Bollerslev, T. (1997). *Intraday Periodicity and Volatility
  Persistence in Financial Markets*, J. Empirical Finance 4(2-3), 115-158.
  https://www.sciencedirect.com/science/article/pii/S0927539897000042 —
  retrieved 2026-09-03T08:26:56Z. VERIFIED_METADATA via search.
- Bollerslev, T., Hood, B., Huss, J., Pedersen, L. H. (2018). *Risk Everywhere:
  Modeling and Managing Volatility*, Review of Financial Studies 31(7),
  2729-2773. https://academic.oup.com/rfs/article/31/7/2729/5001472 —
  retrieved 2026-09-03T08:26:56Z. VERIFIED_METADATA via search. Supporting
  context: short-horizon risk persistence.
- Transfer claim (London-morning return predicts NY-overlap continuation in
  G10 FX at H1, 2020–2026): UNVERIFIED — the hypothesis under test.
