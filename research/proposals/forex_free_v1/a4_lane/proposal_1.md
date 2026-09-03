# FXFV1-A4-P1 — Tokyo-morning range contraction → London-morning expansion breakout

Lane: FOREX-FREE-V1 / F4 / A4 (range expansion / breakout perspective)
Label: **RESEARCH_CANDIDATE_NOT_LIVE_READY**
Status: outcome-blind proposal. No returns, PnL, or backtest were computed or inspected in this lane.

---

## 1. Economic mechanism

Asian hours for the European-quoted majors are the quiet segment of the global
FX day. The intraday volatility periodicity of FX is deterministic and keyed to
the session clock (Andersen & Bollerslev 1997): activity bottoms in Asian
afternoon and expands sharply at the London open and again in the NY overlap.
Over the Tokyo night, stop-loss orders and option barriers accumulate just
outside the visible range. When London opens, dealers hedge into triggered
stops; clustered stop-loss orders produce self-reinforcing price cascades
(Osler 2005). The mechanism trades exactly that event: a quiet Tokyo-morning
range, then the first **completed-bar close** beyond it during the London
morning, held intraday only, always flat before the New York rollover.

Profit source: continuation during the London-open / NY-morning expansion.
Loss source: failed breakouts — London flow rejects the extreme and mean-reverts
into the range. The counterparty on winning trades is mechanical: price-
insensitive stop orders (Osler 2005) and the dealers who must hedge them; the
counterparty on losing trades is the range-fader.

Why H1 completed bars suffice: the range and its violation are multi-hour
session events, not tick-level microstructure events. Why no volume is used:
FX volume is decentralized; the mechanism is price-only.

## 2. Definitions (frozen; completed bars only)

Canonical data: Twelve Data H1 OHLC, UTC bar-open stamps, deduped canonical
series, 2020-01-29 → 2026-09-02, 7 pairs. A bar is actionable only at its
completion instant (open stamp + 1h).

**Tokyo range.** For each Tokyo business day D, take the completed H1 bars
whose open instants map into `[09:00, 15:00)` Asia/Tokyo (stamps 09–14 JST,
exactly 6 bars). `AH = max(high)`, `AL = min(low)`. If the window does not
contain exactly 6 canonical in-calendar bars, D is structurally invalid and
cannot trade. Japan has no DST, so this window is 00:00–06:00 UTC year-round.
Consequence: **Mondays are always invalid** — Mon 09:00–10:00 JST precedes the
Sunday 21:00 America/New_York weekly open (Mon 02:00 UTC EST / 01:00 UTC EDT).
This is a calendar fact of the frozen week, not a choice.

**Entry signal.** Decision window: completed bars whose open instants map into
`[08:00, 12:00)` Europe/London (stamps 08, 09, 10, 11 London; UK DST via
zoneinfo). In chronological order, on the first completed bar B with

- `close(B) > AH` (strict) → LONG signal, or
- `close(B) < AL` (strict) → SHORT signal,

take that signal; the first signal of the day only; the opposite side is
cancelled for that day; no signal by the end of the window → no trade.

**Execution.** Next-allowed-bar: fill at the open of the first canonical
calendar bar whose open instant is strictly after B's completion instant,
provided that open maps to a NY wall-clock time strictly before 15:00
America/New_York; otherwise the signal is discarded. No intrabar fills: a gap
through the range fills at the open, not at AH/AL.

**Exits.**

1. Stop: on any later completed bar C, `close(C) < AL` (long) or
   `close(C) > AH` (short) → fill at the next allowed bar open (same 15:00 NY
   cutoff). The opposite extreme is the structural stop; there is no profit
   target.
2. Mandatory flatten: any open position fills its exit at the open of the H1
   bar stamped **15:00 America/New_York** (completion 16:00 NY — two full hours
   strictly before the 17:00 NY rollover instant). Same rule on Friday, where
   the 15:00 NY bar is the last bar of the week (frozen weekly close Fri 16:00
   NY). One position per NY trading day; no re-entry after a stop; no
   stop-and-reverse.

**Flat invariant.** No fill may execute at a bar open at or after 15:00 NY.
The book is therefore flat from 15:00 NY wall clock — strictly before every
17:00 NY rollover under any bar-stamping convention — and never holds a
position across a rollover instant or the weekend. Financing exposure is zero
by construction; no financing data is used or needed.

## 3. Anchor / neighbour / negative control

| arm | definition | role |
|---|---|---|
| anchor | Tokyo range `[09:00,15:00)` JST (6 bars); London decisions `[08:00,12:00)` (4 bars); opposite-extreme stop; 15:00 NY flatten | validates: real session-structure edge should survive frozen conservative costs |
| neighbour | Tokyo range widened one bar each side: `[08:00,16:00)` JST (8 bars); all else identical | preregistered boundary-sensitivity test; a real mechanism degrades gracefully, an artifact flips |
| negative control | identical rule on the identical range, but entries restricted to completed bars stamped `[18:00,21:00)` America/New_York (Asian activity trough) | destroys: if breakout edge is equal/better in the trough, the timing story is false — the rule is generic breakout beta and the anchor is rejected |

The control holds the signal constant and moves only the session hour of
execution — it isolates the timing channel (causal in the falsifiable,
preregistered sense). No other variants are evaluable; anything more is a grid.

## 4. Frozen cost stress (frozen 2026-09-03, before any returns)

Round trip = one full proxy spread charged once per completed round trip:
`net_log_return = log(exit_open / entry_open) − cost_bps × 1e-4`.
Delay stress shifts every execution one additional completed bar later; a
delayed exit that would land at/after the 15:00 NY boundary collapses into the
15:00 NY flatten fill (the invariant is never violated by the stress).

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
spread claim). Six stress cells per arm per pair: {×1.0, ×1.5, ×2.0} ×
{no delay, one-bar delay}.

## 5. Falsification rule (preregistered)

Per pair per arm: mean per-trade net return (bps) with day-clustered t-stat and
trade count, under the stated stress cell. Evaluated only in the later
authorized phase; nothing here inspects outcomes.

- **K1 viability** — FAIL if <4 of 7 pairs have mean net trade expectancy > 0
  at ×1.0/no-delay, OR <4 of 7 at ×1.5/one-bar-delay, OR any pair below
  −5 bps/trade at ×1.5/one-bar-delay.
- **K2 session causality** — FAIL if anchor (×1.0) does not beat the negative
  control (×1.0) in ≥5 of 7 pairs.
- **K3 neighbour robustness** — FAIL if Spearman(anchor, neighbour) mean net
  expectancy across the 7 pairs < +0.5.
- **K4 cost fragility** — FAIL if expectancy sign differs between ×1.0 and
  ×2.0 in ≥4 pairs.

Survival requires K1 ∧ K2 ∧ K3 ∧ ¬K4. Any other outcome falsifies the proposal
as specified. No re-specification, no parameter rescue, no window change after
any return is visible.

## 6. Expected regimes and preregistered heterogeneity

Favours: post-compression expansion days; London/NY trend days; macro-surprise
weeks; normal-liquidity Tue–Thu. Adverse: holiday-thinned weeks; range-edge
whipsaw under stress; regimes where Asian hours carry the volatility.
Preregistered sub-prediction (not a kill rule): USD/JPY's "Tokyo morning" is its
home liquidity session, so the anchor should be weakest on USD/JPY and strongest
on EUR/USD, GBP/USD, USD/CHF.

Structural bounds (design facts, not results): ≤1 trade per non-Monday NY
trading day; expected order of magnitude 300–900 trades/pair over ~6.59y.

## 7. DST session clock

Frozen calendar: Sunday 21:00 America/New_York open → Friday 16:00 close;
rollover 17:00 NY; all boundaries via zoneinfo named zones (matches
`DEFAULT_FX_WEEK_CONVENTION`, `research/assets/forex/sessions.py`). Bars are
UTC-stamped; NY/London/Tokyo labels derived per bar via zoneinfo; UTC→zone is
single-valued so fall-back is unambiguous. US/UK DST transitions occur on
Sundays outside all Mon–Fri session windows used here, so no window is ever
truncated by a transition on a trading day. Flatten boundary: 15:00 NY bar
open in both EST and EDT.

## 8. Trial count (frozen)

7 anchor + 7 neighbour + 7 negative-control cells = **21 evaluation cells**;
6 stress cells each; 1 statistic set each; 0 free anchor parameters; 1
preregistered neighbour; 0 further variants; no grid search. Frozen
2026-09-03T08:26:56Z, before any return/PnL/backtest computation.

## 9. Data contract compliance

Uses only Twelve Data H1 open/high/low/close + UTC open stamps for the 7
authorized pairs over the authorized window. Volume (null), bid/ask,
rollover/financing, D1/H4 series, and all other providers are not used. The
frozen prior-cycle directory `research/proposals/forex/` was not opened.

## 10. Sources

- Osler, C. L. (2005). *Stop-Loss Orders and Price Cascades in Currency
  Markets*, J. Int. Money & Finance (also FRBNY Staff Report 150, 2002).
  https://www.sciencedirect.com/science/article/abs/pii/S0261560604001147 —
  retrieved 2026-09-03T08:26:56Z. VERIFIED_METADATA via search.
- Osler, C. L. (2000). *Support for Resistance: Technical Analysis and Intraday
  Exchange Rates*, FRBNY Economic Policy Review.
  https://www.newyorkfed.org/research/epr/00v06n2/0007osle.html — retrieved
  2026-09-03T08:26:56Z. UNVERIFIED (not re-fetched).
- Andersen, T. G., Bollerslev, T. (1997). *Intraday Periodicity and Volatility
  Persistence in Financial Markets*, J. Empirical Finance 4(2-3), 115-158.
  https://www.sciencedirect.com/science/article/pii/S0927539897000042 —
  retrieved 2026-09-03T08:26:56Z. VERIFIED_METADATA via search.
- Transfer claim (Tokyo-range breakout edge concentrated at the London open in
  G10 FX at H1, 2020–2026): UNVERIFIED — the hypothesis under test.
