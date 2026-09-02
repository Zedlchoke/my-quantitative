# A9 V10-N1 blinded mechanism proposals — three document-only candidates

**Agent:** A9 (`a9-hypothesis-2` role, fresh wave-N worktree)
**Worktree:** `/Users/hoangminhlong/my-quantitative-v10-wt/n-a9-proposals`
**Branch:** `orca/v10-n-a9` · **Base HEAD verified:** `aec9324c97771c26e840c1c10b73dd56737f8f96`
**Written (UTC child clock):** 2026-08-27T05:1xZ–06:xxZ
**Artifact type:** evidence only. No strategy code, no backtest run, no scored
metric inspected or produced.
**Mandate:** PLAN §8 "N — blinded proposal firewall" (wave N1) as frozen in
`research/control/v10_discovery_run/v10_contract.json` (owner GO
"Freeze + Wave N now", recorded 2026-08-27T04:52Z).

> **Independence attestation.** This file was authored without reading, listing,
> or opening any A8 artifact under `research/audits/v10/proposals/a8_*`, and
> without reading any `results/**` tree, scoring/finalize artifact,
> reproduction metric file, or realized-performance number of any kind. No
> coordination message from A8 was received or sought.

**Exactly three proposals are offered.** Each carries every mandatory field from
PLAN §8 and consumes exactly 3 scored slots if selected (anchor + neighbor +
negative control). One additional candidate axis (a UTC-wall-clock liquidity-
carriage premium) was considered during drafting and deliberately **not**
developed past a one-line sketch: it would be dominated on cost by the friction
baseline and adding it would breach the three-proposal cap. It appears nowhere
below as a spec, so it cannot be counted, scored, or rescued later.

---

## 0. Reading scope actually used (for A5/A7 provenance)

| Path | Used for |
|---|---|
| `PLAN.md` §1–§15 | mandate fields, gate vocabulary, stress matrix |
| `research/control/v10_discovery_run/v10_contract.json` | budget, thresholds, cost baseline, prohibitions |
| `research/control/v10_hardened_run/worktree_manifest.json` | my own write allowlist only |
| `data/v9_manifests/universe_selection_v9.json` | universe membership, window, bar/funding file lists, BTC funding census |
| `data/v8x_manifests/crypto_universe_selection.json` | gap-census slot counts, rule constants (interval seconds, catalog roots) |
| `research/hypotheses/**` hypothesis headers (first ~14 lines each) | nearest-family enumeration and structural class only |
| `"sprint V1.md"` / `"sprint V2.md"` headings + `ANALYSIS_MEMO.md` framing sections | historical family name enumeration |

Nothing outside this list informed any construction below. Where historical
lookbacks, thresholds or cadences appear inside those files they were **not**
carried over: every constant used here derives either (i) mechanically from the
mechanism's own native timescale, (ii) from a frozen multiple of a measured
dispersion statistic, or (iii) from manifest-recorded structure such as the
900-second grid. Section 3 states the derivation of each constant so A7 can
audit non-tunability directly instead of trusting this author.

---

## 1. Constraints every proposal is written against

From `v10_contract.json` and PLAN §8–§12:

- Budget if selected: exactly **3 scored slots per family** = 1 anchor +
  1 neighbor + 1 negative control. Unused slots cannot be replaced after any
  metric becomes visible. Two families max across A8+A9, 6 cells total.
- Selection: total ≥ 75, novelty ≥ 28, **material deltas required in all four
  dimensions**, no hard/data fail, A7 no-rescue concurrence. Tie-break by
  frozen hypothesis ID — hence the IDs here sort deterministically
  (`FORCEDFLOW` < `INFSPILL` < `RVRELVAL`).
- Preregistered cost baseline: **5 bp taker per fill + one adverse tick +
  native funding**, or stricter, never looser.
- Stage-A hard gates that decide survival: post-cost expectancy > 0; PF ≥ 1.10;
  ≥ 2/3 folds positive; no populated fold PF < 0.80; fold contribution ≤ 50 %;
  MDD ≤ 10 %; symbol contribution/risk ≤ 40 %; sample floor; drop-one
  independence; stressed PnL > 0 and PF ≥ 1.00; reproduction `all_match`;
  zero HIGH/CRITICAL findings.
- Prohibited: rescue/tuning of any V1–V9 family including `TSTREND-L28`;
  substitute symbols; grids; S1 inspection; equity trials.
- Execution reality: ≥ 3 chronological folds, warmup outside scored OOS,
  purge/embargo ≥ holding horizon, completed-bar feature → next-event fill,
  heavy workers = 1 (serial waves), 12-hour V10 clock, hard deadline
  2026-08-27T16:55Z.

Each mechanism states one closed-form recipe with **no free parameter left
open**: one anchor cell, one neighbor cell differing by exactly one theoretically
motivated structural condition (never by a numeric scalar), one negative control.

---

## 2. Sample-feasibility base — arithmetic from manifests only

All numbers come from the two universe manifests. No data file content was read.

| Quantity | Value | Source / derivation |
|---|---|---|
| Scored contract window | `2025-08-21T00:00:00Z → 2026-08-21T00:00:00Z` = 365 d | `scored_window_contract`, both manifests |
| Bar granularity | 15-minute LAST-EXTERNAL (`bar_interval_seconds=900`) | `rule_constants.bar_interval_seconds` |
| Completed-bar slots per symbol, scored window | **35,040** | manifest `expected_15m_slots=35040`; equals 365 d × 96 |
| Selected universe size | **10** symbols; BTC excluded from ranking/trading | `selected_symbols` (n=10), `btc_excluded=true` |
| Universe bar rows, scored window | **350,400** (10 × 35,040) | product |
| Benchmark rows usable input-only | +35,040 (BTCUSDT) ⇒ **385,440** series rows | BTC `census_scored_window_gaps=0` |
| Gap census, whole panel both windows | 758,400 expected slots, **57 gaps, 0 unexplained** | `gap_census_15m_summary`; all 57 are the ETH capture-boundary run (`missing_slots=57`) at the scored-window start |
| Pre-window (selection) slots/symbol | 2,880 (30 d), **0 gaps on all ten** | per-symbol `pre_window.expected_15m_slots=2880, gaps_found=0` |
| Historical warmup depth before scored start | ≈ **364 d ≈ 34,944 bars/symbol** | earliest manifest bar-file starts 2024‑08‑21T13:49Z (SOL/XRP/DOGE/ADA/BNB/LINK) and 2024‑08‑23T04:58Z (ETH/BTC/ENA/SUI/PEPE) vs scored start |
| Total history available per symbol | ≈ 69,900 bars (warmup + scored) | sum |
| Funding series | one `funding.json` per symbol; BTC proven complete across the exposure span with **1,095 settlements / cadence mode 480 min**; selection rule required "held-exposure funding proof" for every selected symbol | BTC `funding_held_exposure_audit`; `selection_rule_reuse_note` |
| Frozen universe, rank order 1..10 | ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, ENAUSDT, SUIUSDT, 1000PEPEUSDT, ADAUSDT, BNBUSDT, LINKUSDT | `selected_symbols.rank` |
| Listing-age gate already applied upstream | onboard ≤ 2024‑08‑21 ⇒ ≥ 365 d age at scored start | `listing_age_rule` |

Two consequences worth freezing:

1. **Universe membership is known before the scored window opens** (selection
   window closes 2025‑08‑21T00:00Z) and is never re-ranked inside it ⇒
   survivorship-free membership for anything built inside the scored window,
   provided the implementation never reads post-window bars for selection.
2. **Warmup never overlaps scored OOS**: a trailing statistic needing L ≤ 250 d
   has ~364 pre-window days, so fold 1 scores without touching later bars
   (PLAN §11 requirement met structurally).

Quote volume availability is manifest-proven, not assumed: the pre-window
ranking metric is defined on "the 15m parquet native quote_volume (USDT)".

---

## 3. Parameter discipline (why none of this is a hidden grid)

Three permitted constant sources, declared at each use:

- **(S) Scale-free constants** — a threshold expressed as a multiple of a
  rolling dispersion measure of the *same* observable, so its meaning is
  "N dispersion units" identically in quiet and wild markets. The multiplier is
  fixed once per cell from the mechanism's claim, never searched.
- **(C) Structural constants** — integers fixed by market structure recorded in
  the manifests or by the mechanism's own native timescale (bar counts implied
  by session/diffusion/convergence reasoning).
- **(D) Data-derived medians/MAD-type scales** — computed from trailing bars
  inclusively; no fitted coefficient, no optimization target.

If implementing any anchor requires choosing between candidate numeric values
by looking at results, the implementer must stop and log `RESCUE_RISK_GRID`;
that proposal is then void rather than amended.

Uniform statistics policy across all three families (no asymmetric leniency):

- All rolling statistics use bars whose close stamp ≤ the signal bar's close
  stamp, inclusive. No centred window, no forward window anywhere.
- Missing-bar handling: evaluate a lookback on available bars only if available
  count ≥ 70 % of nominal; otherwise **suppress the signal fail-closed** and log
  `WARMUP_INSUFFICIENT`. Forward-filling an OHLC bar is forbidden.
- Signal stamp = `bar_open + 900 s` (completed-bar close). Fill stamp =
  OPEN stamp of the first bar strictly after the signal stamp; fill price =
  that bar's OPEN on the external-LAST basis. Never fill in the signal bar
  itself, never at its close/open price.
- Exit conditions evaluated only on bars completing at/after entry fill;
  exits execute at next bar open. Precedence when several fire simultaneously,
  frozen per cell: (1) scheduled/time exit, (2) opposite-sign exit condition,
  (3) timeout.
- Costs: every fill charges 5 bp taker + 1 adverse tick against its own fill
  price; funding accrues at each settlement instant strictly inside
  `[entry_fill_ts, exit_fill_ts)` using the rate settled at that instant
  (long pays positive funding).
- Purge/embargo: uniform rule `embargo = 72 h` (≥ 3 × the longest holding
  horizon in this set, itself ≥ PLAN §11's "≥ holding horizon"). Declared
  non-tunable and identical for all six potential cells so fold boundaries can
  never flatter one family.
- Fold layout requested from A5: 3 chronological folds after warmup exclusion,
  equal-length where divisibility allows, embargo strips at both ends of each
  scored segment.

---

# 4. Proposal P1 — `H-V10N1-A9-FORCEDFLOW-v1`

**Mechanism class:** forced-deleveraging immediacy provision. Event-driven,
both-sided, single-name.

## 4.1 Economic source and counterparty

Marginal holders on USD-M perpetuals run levered positions sized by their own
leverage budget. When adverse movement consumes maintenance margin, the venue's
margin engine reduces them **at whatever price clears the book, not at a price
reflecting value** — non-informational, price-insensitive flow by construction.
The proposed premium is the classical payment for supplying immediacy into
one-sided forced flow: absorbing a forced seller means buying below the level at
which unlevered holders were still willing to hold, and the excess return
compensates for the risk that the cascade continues through your fill.

- **Counterparty:** leveraged retail/small-fund perpetual holders being
  force-deleveraged (long side: insolvent longs sold out by the margin engine;
  mirror: liquidated shorts forced to buy back). Their clearing agent acts
  mechanically on their behalf.
- **Why they exist:** retail-accessible high leverage, a discretion-free
  maintenance-margin engine, and 24/7 trading mean deleveraging arrives in
  bursts whenever thresholds are crossed. No infrastructure assumption beyond
  the frozen data: ten perpetuals with funding and 15-minute liquidity, i.e.
  precisely the venue type where automated margin calls dominate.
- **What makes them predictable:** their motive is solvency, not opinion. They
  do not stop selling because price became attractive; they sell until margin
  is restored. Once the deficit is cleared the pressure stops mechanically,
  leaving price pushed away from levels supported by willing holders — which is
  where the harvested bounce lives.

## 4.2 PIT inputs

Completed 15-minute bars of the ten selected symbols only:

- `open_i, high_i, low_i, close_i` (external LAST print basis);
- `qvol_i` = native quote volume (manifest-proven field).

No OI series, no order book, no trades, no stablecoin index, no options data,
no external calendar. Why PIT-safe: every quantity belongs to a bar already
closed before the signal stamp; normalization windows trail and are inclusive
of the signal bar alone; nothing references future bars, centred medians, or
any symbol outside the frozen universe; universe membership itself was fixed
strictly before the scored window opened.

## 4.3 Causal sign, with mechanism-level justification

**Sign: FADE. LONG after capitulation-shaped down bars; SHORT after blow-off
shaped up bars.**

1. An involuntary seller transacts regardless of level ⇒ his sale pushes price
   below the willingness-to-hold level of unlevered holders.
2. Because he sells into resting bids until margin is restored, the terminal
   bar of his burst carries abnormal participation *and* closes near its low:
   the footprint is a joint extreme in (volatility-normalized excursion,
   intra-bar close location, participation), not merely a large negative return.
3. When the deficit clears, selling stops mechanically. No informational reason
   remains for price to keep falling, while bid-side buyers who did not need to
   act yet are still there.
4. Therefore conditional expected return over the following hours is positive
   ⇒ LONG. Mirror argument ⇒ SHORT after forced-buying blow-offs.

## 4.4 Clocks

- **Signal clock:** completed 15-minute bar closes (UTC, `bar_open+900s`).
- **Fill clock:** next allowed event = OPEN of the next 15-minute bar after the
  signal stamp, always strictly later (§3). Exits/re-evaluations also sit on
  completed-bar boundaries only.

## 4.5 Holding horizon

`hold_max = 16 bars` (4 h). Native-unit rationale: a deleveraging flush resolves
in hours; 4 h spans at most one settlement boundary and prevents the position
from quietly becoming a multi-day directional bet. An early-exit rule (§4.6)
may shorten it; nothing lengthens it.

## 4.6 Construction recipe

Per symbol s, computed on completed bars ending at signal index t:

```
r1_i   = ln(close_i / close_{i-1})
sig_i  = rolling std(r1_j ; j in [i-L_sig+1 .. i])              # L_sig = 96
exc_i  = (close_i - open_i) / (sqrt(L_exc) * sig_i)             # L_exc = 4
rng_i  = high_i - low_i
clv_i  = ((close_i - low_i) - (high_i - close_i)) / rng_i       # [-1,+1]; 0 if rng_i==0
qvz_i  = (qvol_i - mean(qvol_j, j=i-L_qv+1..i)) /
         (std(qvol_j , j=i-L_qv+1..i))                          # L_qv = 96
```

Entry tests, evaluated only when `rng_i > 0` and every 96-bar window has ≥ 67
available bars (else suppress):

- **Capitulation → go LONG:** `exc_t <= -2.0` **AND** `clv_t <= -0.50` **AND**
  `qvz_t >= 2.0`.
- **Blow-off → go SHORT:** `exc_t >= +2.0` **AND** `clv_t >= +0.50` **AND**
  `qvz_t >= 2.0`.

Fills at next bar open. Unit exposure per triggered symbol, single leg, no
pyramiding. A repeat trigger in the same direction while live is ignored; a
trigger in the opposite direction closes-and-reverses at the next open.

Exits, precedence (time, opposite-condition, timeout):

1. **Time target:** `bars_held == 16` → exit next open.
2. **Forced-flow exhaustion:** the same triple fires with opposite sign → exit
   (and reverse) next open.
3. Rule 1 already covers timeout; stated explicitly so no hidden stop/target
   logic exists. There is deliberately **no stop-loss and no profit target**.

Accounting per §3: fees/ticks per fill, funding accrual over held settlements,
flat benchmark compared on identical bars.

## 4.7 Regimes

- **Edge should concentrate:** post-leverage-flush mean-reverting churn;
  symbols that ran hot (recent leverage build-up) during sharp intraday
  reversals; volatile but non-trending tape where cascades self-exhaust within
  hours; stretches around settlement boundaries with one-sided crowding.
- **Should lose:** multi-day one-directional insolvency cascades (forced sellers
  are right and the bounce never comes); news/regulatory breaks where the first
  big-volume move IS informative; low-leverage grind where triggers fire on
  ordinary churn with no forced flow behind them; prolonged compression regimes
  where the 96-bar σ shrinks until "2σ" bars become ordinary.

## 4.8 Falsification procedure

Killed if ANY of:

1. After frozen baseline costs on the standard 3-fold layout with 72 h embargo:
   post-cost expectancy ≤ 0, or PF < 1.10, or < 2/3 folds positive, or any
   populated fold PF < 0.80, or MDD > 10 %, or drop-one-symbol / drop-one-fold
   flips expectancy sign.
2. Stressed variants (fee/slippage ×1.5, +2 ticks, +1 event delay) give
   PnL ≤ 0 or PF < 1.00 — failing "+1 event delay" specifically falsifies
   "immediacy provision", since it simulates being slower than the flush.
3. Event-thinness kill: if trigger rate lands under the frozen sample floor
   (floor value NOT visible to A9; see §9), report
   `INSUFFICIENT_SAMPLE_NO_SCORE`. Loosening a threshold instead is forbidden.
4. Mechanism-content kill via the control in §4.9 (the de-participation variant
   is deliberately outside the budget and will not be run).

## 4.9 Negative control (sign-targeting)

**Control `FORCEDFLOW-CTRL`: identical machinery entered WITH the flow.** SHORT
after capitulation triggers, LONG after blow-off triggers; filters, fills,
exits, costs, folds byte-identical otherwise.

Why this invalidator: the causal story rests on the marginal transactor's
motive — price-insensitive deleveraging, so HIS side loses money over the
following hours. If chasing the same footprints earns ≥ half the fade side's
expectancy, or PF ≥ 1.05, those footprints identify informed directional
pressure rather than a forced seller, and the causal sign is rejected even
though an absolute-looking profit exists. Controls are never promoted.

## 4.10 Nearest historical families and structural delta

Nearest families (names enumerated from repo docs; parameters deliberately not
consulted): root strategies `mean_reversion`, `reclaim_mr`,
`markdown_breakdown`, `vol_compression_breakout` (= `H-VOLCOMP-BRKOUT-v1`,
REJECTED), plus `H-V9-VOLSHOCK-v1`, `H-FUNDCROWD-MR-v1/v2`
(`funding_crowding`, feature `point_in_time_funding_percentile`), and
historically `ema_atr` / `trend_pullback`.

| Dimension | Nearest families' geometry | This proposal | Material? |
|---|---|---|---|
| Economic source | behavioural overreaction / volatility-regime transition / level reclaim | mechanical margin-engine deleveraging: identity and motive of the marginal transactor drive the sign | **Yes** — predicts *who* is trading, not merely that price overshot |
| Observable construction | price-level crossings, lookback return percentiles, vol-compression ratios, reclaimed levels, vol-shock magnitude | joint triple: σ-normalized open→close excursion × intra-bar CLOSE LOCATION VALUE × quote-volume z-score. CLV is used by **no** family in the inventory, and none conditions on participation concentration | **Yes** |
| Selection / payoff geometry | continuous state machines around levels; weekly rank baskets; squeeze-resolution breakouts; TS trend follow | rare symmetrical event scalps on BOTH sides, fixed 4-h horizon, zero reference to any price level, support/resistance, or percent-rank-of-prices | **Contested, argued yes** — see honesty flag below |
| Counterparty-or-regime prediction | regime classified from price/vol state alone | predicts counterparty identity (margin engine acting for an insolvent holder) and predicts his pressure terminates when the deficit clears | **Yes** |

**Net claim: 4/4 material dimensions claimed, with dimension 3 contested.**
An event-conditional reversal is payoff-shape-similar to `reclaim_mr`'s fade;
the asserted difference is that selection keys off participation extremes rather
than level relationships. If A7 rules dimension 3 immaterial, this proposal
fails the four-dimension requirement on its own and must be dropped without
amendment — flagged openly rather than argued away.

Rescue hygiene, made structural: no moving average or price band, no swing/
pivot/level, no percent-rank of returns, no lookback shorter than the single
96-bar σ/qv normalizer, no funding-derived threshold (funding plays NO role,
unlike `H-FUNDCROWD-MR-v2`), no session/weekday condition, no symbol-specific
setting, no stop/target pair.

## 4.11 Sample feasibility

Planning arithmetic on manifest counts (35,040 bars/symbol/year):

- Triple condition ⇒ rare: plan 0.2 %–0.8 % per bar ⇒ 70–280 events per
  symbol-year ⇒ **700–2,800 symbol-events/year** across ten names (both sides
  included).
- Per fold (≈121 scored days): **230–930 events**. The thin end sits uncomfortably
  near typical floors — this family's principal feasibility risk, disclosed
  rather than papered over (§4.8 item 3).
- Overlap clipping: triggers closer than 16 bars collapse into one live position;
  ceiling 35,040/16 = 2,190 positions/symbol-year never binds.
- Warmup trivial: 24 h of history suffices; hundreds of days exist.

Verdict: **feasible with medium confidence**, honest chance the sample floor
rejects it.

## 4.12 Audit cost estimate

Four rolling arrays over ~385 k rows, thousands of trades: 1–3 min per run-cell.
Scored surface = 3 cells × 5 stress variants = 15 runs, plus ~15 clean repro
runs ⇒ ~30 runs ⇒ **0.5–1.5 CPU-hours** ⇒ ≤ **1.5 wall-clock hours** serialized
at heavy cap 1. Well inside the 12-hour clock including reproduction parity.

## 4.13 Frozen cell configuration

**Anchor `FORCEDFLOW-ANCHOR`**

| item | value | constant class |
|---|---|---|
| universe | all ten selected symbols; BTC never traded | frozen manifest |
| `L_sig` | 96 bars (24 h) | C |
| `L_exc` | 4 bars (1 h burst) | C |
| `L_qv` | 96 bars (24 h) | C |
| `exc` threshold | \|2.0\| σ | S |
| `clv` threshold | \|0.50\| | S |
| `qvz` threshold | ≥ +2.0 | S |
| hold_max | 16 bars (4 h) | C |
| stop/target | none | by design |
| embargo / folds | 72 h / 3 | uniform policy |

**Neighbor `FORCEDFLOW-NB` — one structural addition only:** entry additionally
requires the participating extreme to coincide with the *local* price extreme of
the burst rather than a continuation leg, i.e.
`(low_t == min(low_{t-1}, low_t))` for capitulation entries and
`(high_t == max(high_{t-1}, high_t))` for blow-off entries (`L_local = 2`, class
C). Theory being tested: the harvested bounce comes from the TERMINAL transaction
of forced selling; if the extreme is still rolling forward, the cascade was not
exhausted. Prediction if the mechanism is real: fewer triggers, higher hit rate,
higher expectancy per trade than the anchor. Failure of that prediction rejects
the exhaustion interpretation even if the anchor passes.

**Control `FORCEDFLOW-CTRL`** is the third scored slot (§4.9). Cells used = 3.

---

# 5. Proposal P2 — `H-V10N1-A9-INFSPILL-v1`

**Mechanism class:** benchmark-led information spillover. Cross-instrument
diffusion lag; single-name directional; the benchmark instrument is NEVER traded.

## 5.1 Economic source and counterparty

Risk-relevant information about aggregate crypto beta (macro prints, ETF-side
hedging demand, leverage stress) hits the deepest instrument first — the BTC
perp, where institutional hedging/arbitrage desks concentrate size — because
transacting there costs least. Each alt perp is priced by a thinner population
with different monitoring frequency. Diffusion of the repricing into alts is
therefore incomplete within minutes: part of the alt holder base reacts late,
and multi-leg hedgers fill out their smaller legs after the benchmark.

- **Counterparty:** (a) delayed-repricing altcoin holders whose allocation
  process updates slowly (passive allocators, hand-managed books, bots keyed
  only to alt-local indicators); (b) hedgers who executed the benchmark leg
  first and complete alt legs at reduced urgency.
- **Why they exist:** alts carry far larger per-name risk relative to desk
  capacity and nobody monitors twenty small books as continuously as the
  flagship book. Institutional BTC-perp access and retail alt access coexist in
  one tape.
- **Predictability:** after a completed benchmark move, a fraction of the
  required alt repricing is still unexecuted ⇒ subsequent same-signed drift in
  alts ⇒ LONG alt after benchmark up-shock, SHORT alt after benchmark down-shock.

The null hypothesis — integration completes within one 15-minute bar — is the
*most likely* outcome, and the design's purpose is to bound how much lag
survives 15-minute granularity at 5 bp cost. Framed as a bounded measurement,
not an assumed edge.

## 5.2 PIT inputs

Completed 15-minute bars only:

- **Benchmark input, measurement role:** `BTCUSDT-PERP.BINANCE` `close_b`
  series. Availability is manifest-proven (`census_scored_window_gaps=0`) and
  the ancestor manifest fixes BTC's role as
  `benchmark_measurement_only_excluded_from_ranking_weights_pnl`. Using its
  completed bars as a conditioning observable is a measurement/context use,
  consistent with PLAN §11 ("buy-and-hold/BTC-beta-neutral only context"): no
  BTC leg is ever opened, no BTC PnL enters the scorecard, BTC is neither added
  to nor removed from the traded universe.
- **Traded inputs:** `open_s,i / close_s,i` for the ten selected symbols, plus
  σ estimators on both sides (same `r1` definition as §4.6).

Why PIT-safe: the shock statistic uses benchmark bars closing at or before the
signal stamp, inclusive; normalization trails on the same convention; the
decision instant equals the completion time of the last benchmark bar used and
is therefore knowable at that moment; both books share the manifest-documented
900 s grid, so the coincidence of completion stamps introduces no ordering
ambiguity (the newer bar cannot inform the older one, and none needs to).

## 5.3 Causal sign, with mechanism-level justification

**Sign: CONTINUATION. Take the SAME sign as the benchmark shock.**

1. A benchmark shock signals changed aggregate beta demand, not sentiment about
   one name.
2. Transmission requires transactions in each alt book; transaction rates there
   are lower (thinner restbook, wider quotes, slower holder update cycles).
3. Until those transactions occur, alt price understates the new beta level ⇒
   drift toward benchmark-implied fair value ⇒ same-signed continuation.
4. Diffusion completes ⇒ drift decays ⇒ fixed-horizon exit rather than
   stop/target: the mechanism predicts a finite life, not a trend.

The alternative world — alts OVER-react to benchmark shocks — flips the sign
and is enumerated as a legitimate possible outcome (§5.8/§5.9).

## 5.4 Clocks

- **Signal clock:** completed 15-minute bar closes, benchmark and alts aligned
  to the same UTC 900 s grid (manifest: common grid, zero unexplained gaps apart
  from the explained ETH boundary run).
- **Fill clock:** OPEN of the following 15-minute bar, strictly after the signal
  stamp. If a symbol's bar is missing at the fill instant the signal for that
  symbol is suppressed fail-closed — never back-filled from a later bar.
- Exits evaluated on the same completed-bar clock.

## 5.5 Holding horizon

`hold = 32 bars` (8 h). Native-unit rationale: diffusion and basket-completion
act over hours, so the exit is a multiple of the diffusion window rather than a
profit target; 8 h also aligns to the settlement cadence boundary, making
funding accounting unambiguous. The neighbor changes a *condition*, never this
number.

## 5.6 Construction recipe

At signal bar index t, for each alt symbol s:

```
# benchmark shock (measurement-only leg)
rb_j       = ln(close_B,j / close_B,j-1)
shockraw_t = sum(rb_j ; j in [t-L_shk+1 .. t])                    # L_shk = 6
sigB_t     = rolling std(shockraw_j ; j = t-L_normB+1 .. t)        # L_normB = 2880 (30 d)
mag_t      = abs(shockraw_t) / sigB_t                              # unitless
dir_t      = sign(shockraw_t)

# alt "did not yet react" statistic (NEIGHBOR only)
ra_j          = ln(close_s,j / close_s,j-1)
altmove_s,t   = sum(ra_j ; j in [t-L_shk+1..t]) /
                (rolling_std(ra_j ; j=t-L_sig+1..t) * sqrt(L_shk))

# ANCHOR entry    : mag_t >= 2.0
# NEIGHBOR entry  : mag_t >= 2.0  AND  abs(altmove_s,t) <= 1.0
side        = dir_t        # long if shock up, short if down
```

Execution: fill next bar OPEN in `side`; hold exactly 32 bars then exit at next
open; precedence = time exit only (no stop, no take-profit). While live on
symbol s, further signals on s are ignored (no stacking). Portfolio shape:
≤ 10 concurrent equal-notional single-leg exposures; benchmark never traded.
Accounting per §3, including funding on held alts across settlements.

## 5.7 Regimes

- **Edge should concentrate:** fast macro/shock weeks (large aggregate moves,
  elevated cross-sectional correlation, deep-book benchmark leading); bursts
  where the benchmark moved far beyond its recent norm while some alts barely
  moved; stressed sessions where alt depth withdraws first and refills later.
- **Should lose:** integrated quiet regimes where alts track the benchmark
  bar-for-bar (cost floor dominates); idiosyncratic alt news cycles that
  correctly detach an alt from benchmark beta (trading against information);
  strong one-directional regimes where an 8-h hold degenerates into beta and
  MDD dominates.

## 5.8 Falsification procedure

Killed if ANY of:

1. Anchor post-cost expectancy ≤ 0, or PF < 1.10, or < 2/3 folds positive, or a
   populated fold PF < 0.80, or MDD > 10 %, or drop-one-symbol dependence.
2. Stress variants fall to PnL ≤ 0 or PF < 1.00. The "+1 event delay" stress is
   the sharpest test here: it directly proxies "diffusion faster than claimed".
3. Neighbor prediction fails (§5.13-equivalent below): theory says restricting
   entries to not-yet-moved alts concentrates unexecuted repricing inventory and
   must raise hit rate/expectancy. A neighbor no better than the anchor
   contradicts the diffusion explanation even if the anchor passed.
4. Control behaves like a genuine effect (§5.9).

Neighbor (single structural addition, no scalar change): entry additionally
requires `abs(altmove_s,t) <= 1.0`. Prediction: fewer entries, higher expectancy
per trade, higher hit rate; support for the anchor if confirmed.

## 5.9 Negative control (causality-through-time targeting)

**Control `INFSPILL-CTRL`: stale-shock placebo.** Identical recipe, but the
benchmark shock window ends `L_stale = 192 bars` (48 h) earlier — information
already fully diffused under any plausible diffusion speed. Prediction under
the causal story: expectancy indistinguishable from zero, clearly below the
anchor.

Invalidation rule: if placebo expectancy ≥ 0.5 × anchor expectancy, or placebo
PF ≥ 1.05, then observed PnL comes from generic benchmark-alt co-momentum/beta
exposure rather than fresh incompletely diffused information, and the causal
sign claimed in §5.3 is rejected.

## 5.10 Nearest historical families and structural delta

Nearest families: `H-XSECT-MOM-v1` (dollar-neutral XS momentum),
`H-XSECT-REVERSAL-v1/v2` and `H-XSECT-REVERSAL-BREADTH-CRYPTO-v1` (weekly rank
reversal / breadth), `H-V9-TSTREND-v1` (TS trend), root `trend_pullback`,
root `breakout`, `H-XSECT-FUNDING-CARRY-v1`, `H-XSECT-FUNDING-PRICE-DIVERGENCE-v1`.

| Dimension | Nearest families | This proposal | Material? |
|---|---|---|---|
| Economic source | staggered attention to *each asset's own* trailing return; behavioural rank overreaction; trend persistence; crowding carry | inter-instrument information-transmission latency plus staged multi-leg hedging — a relational phenomenon with no single-asset analogue | **Yes** |
| Observable construction | percentiles/ranks of own trailing returns across names; TS trend indicator; funding percentile | benchmark shock magnitude in units of its own 30-day σ, measured on an instrument excluded from trading; no cross-sectional ranking operator exists anywhere in the design | **Yes** |
| Selection / payoff geometry | periodic rebalanced dollar-neutral baskets, or continuous single-name state machines on horizons of days-to-weeks | event-gated coincident-clock single-name entries with fixed 8-h decay horizon and benchmark conditioning — timing-triggered, not level- or rank-triggered | **Yes** |
| Counterparty-or-regime prediction | laggards/winner-loser ordering revert or persist collectively | names the specific late transactor (delayed allocators, second-pass hedgers) and predicts the *duration* of the delay (bounded horizon) | **Yes** |

**4/4 material dims claimed and defensible.** Rescue hygiene explicit: not TS
momentum (conditions on another instrument's shock; ignores the alt's own trend);
not XS momentum/reversal (no ranks, no dollar-neutral basket, no
formation/rebalance cycle); not a funding mechanism (no funding input); the
neighbor rewards an alt for having NOT moved, which is the opposite of a
breakout filter.

## 5.11 Sample feasibility

- Shock arithmetic: with `L_shk=6` normalized by 30-day σ, plan a 2–4 % breach
  rate ⇒ 700–1,400 benchmark shock bars/year ⇒ ×10 tradable alts ⇒
  **7,000–14,000 symbol-event opportunities/year** before overlap clipping.
- Clipping: 32-bar holds cap positions at ≤ 35,040/32 ≈ 1,095/symbol/year, so
  capacity never binds; realistic realized trades ≈ **2,000–6,000/year**.
- Per fold: roughly **650–2,000 trades** — the strongest feasibility profile of
  the three.
- Data completeness: benchmark gaps = 0; universe gaps = 57, all explained and
  confined to the ETH window-start boundary before fold 1.
- Warmup: 30-day normalization needs 2,880 bars ≪ 34,944 pre-window bars.

Verdict: **feasible with high confidence.**

## 5.12 Audit cost estimate

Vectorized rolling math over ~385 k rows; moderate trigger density. Estimate
2–5 min per run-cell ⇒ 15 stress + ~15 repro runs ⇒ **1–2.5 CPU-hours** ⇒
≤ **2.5 wall-clock hours** at heavy cap 1. Highest run count of the three yet
comfortably inside budget.

## 5.13 Frozen cell configuration

**Anchor `INFSPILL-ANCHOR`**

| item | value | constant class |
|---|---|---|
| traded universe | ten selected symbols | frozen manifest |
| benchmark leg | `BTCUSDT-PERP.BINANCE`, measurement only, never traded | manifest role |
| `L_shk` (shock window) | 6 bars (90 min) | C |
| `L_normB` (σ of shock) | 2,880 bars (30 d) | C |
| `L_sig` (alt σ) | 96 bars | C |
| shock threshold | `mag_t >= 2.0` | S |
| alt-move condition | none (anchor) | — |
| hold | 32 bars (8 h), time exit only | C |
| stop/target | none | by design |
| max concurrent positions | 1 per symbol, ≤ 10 total, equal notional | by design |
| embargo / folds | 72 h / 3 | uniform policy |

**Neighbor `INFSPILL-NB` — one structural addition only:** entry additionally
requires `abs(altmove_s,t) <= 1.0`, i.e. the alt itself has not yet repriced in
units of its own 6-bar σ. Theory being tested: the mechanism claims profit comes
from *unexecuted* repricing inventory; restricting entries to alts that have not
yet moved selects exactly that inventory. Prediction: fewer entries, higher
expectancy per trade, higher hit rate — support for the anchor. Equal or worse
performance contradicts the diffusion explanation even if the anchor passes.

**Control `INFSPILL-CTRL`** is the third scored slot (§5.9). Cells used = 3.

---

# 6. Proposal P3 — `H-V10N1-A9-RVRELVAL-v1`

**Mechanism class:** two-leg relative-value spread reversion against one-sided
idiosyncratic flow.

## 6.1 Economic source and counterparty

Two highly correlated perpetuals share nearly all systematic risk. When
something pushes ONE of them — a single-name headline, unlock/vest flow, a fund
unwinding a concentrated book, listing-driven rotation — the log ratio departs
from its recent centre although the shared factor did not move. Whoever caused
that departure reacted to something specific to one name and transacted more
size than absorbing liquidity could handle quietly; his pressure is transient
because his motive (a discrete allocation change, a collateral need) exhausts
itself, while the shared factor anchoring the ratio is unchanged.

- **Counterparty:** originators of one-sided single-name flow — allocation/
  unlock sellers, concentrated-book unwind desks, listing rotators — plus the
  passive makers whose resting size gets swept asymmetrically in exactly one
  instrument.
- **Why they exist:** crypto capital is unevenly concentrated and frequently
  must be redeployed on schedules (vest calendars, collateral calls,
  index-inclusion events) unrelated to relative value between two perpetuals.
  Nothing links one maker's SOL-specific flow exposure to another's XRP-specific
  flow, so one-sided imbalances arise routinely and stay unhedged until
  relativizing balance sheets act.
- **Predictability:** the divergence such flow creates gets closed by those
  relativizers (delta-arb desks rotating back, funded sellers stepping in on the
  rich leg), restoring the ratio toward local centre. What matters is whose
  balance sheet absorbs the imbalance — not whether either coin looks cheap.

Deliberate honesty: temporary-versus-structural is the crux. If flow reflects a
durable relative-supply shift (new issuance, persistent unlock schedule), the
ratio does not revert and the pair bleeds. That is why the participation
confirmation lives in the neighbor as theory, not decoration.

## 6.2 PIT inputs

Completed 15-minute bars for exactly two instruments chosen by a frozen
mechanical rule — **the two highest pre-window median-quote-volume symbols in
the frozen universe = rank 1 `ETHUSDT-PERP.BINANCE` (leg B, quote) and rank 2
`SOLUSDT-PERP.BINANCE` (leg A, base)**, per `selected_symbols.rank`. Rationale:
the deepest cross minimizes crossing cost, and depth was measured in a window
closing before the scored window opened; both legs show 0 pre-window gaps and
their only recorded scored-window gap is the explained ETH boundary run that
sits before fold 1. Series consumed: `ln(close_A,t)`, `ln(close_B,t)` and the
quote-volume z-score inputs of §4.6 (neighbor only).

Substitution rule: **none**. If either leg fails a data gate, the correct
outcome is a hard data fail for this family, not a different pair.

Why PIT-safe: pairs chosen from a pre-window manifest; all spread statistics
trail inclusively; no centred window; no forward fill; neither leg's own trend
nor any funding variable enters the signal.

## 6.3 Causal sign, with mechanism-level justification

**Sign: CONVERGENCE. Short the rich leg / long the cheap leg when the log ratio
is abnormally far from centre; close on reversion.**

Chain: unchanged shared factor ⇒ locally anchored equilibrium ratio ⇒ deviation
must come from a single-name imbalance ⇒ imbalance-originating flow is finite by
nature (discrete allocation decisions exhaust) ⇒ absorption by relativizers
restores the ratio ⇒ positive expected spread PnL over the convergence window.
Payoff arises from the difference, so common-factor risk cancels structurally.

## 6.4 Clocks

- **Signal clock:** completed 15-minute closes of BOTH legs on the shared
  900 s grid; both legs must have completed bars at the signal stamp or the
  signal is suppressed.
- **Fill clock:** both legs filled atomically at the OPEN of the next 15-minute
  bar, USD-equal notional at fill, charged two taker fees + ticks. If one leg's
  bar is missing, NEITHER leg fills (fail-closed atomicity). Exits likewise
  execute as two simultaneous next-open fills.

## 6.5 Holding horizon

`timeout = 48 bars` (12 h) maximum, earlier exit on convergence. Native-unit
rationale: dislocations from one-off flow are absorbed intraday; after 12 h
without convergence the mechanism's story is dead and continued holding would be
trend-following by inertia. Timeout exits at market next open — treated as a
normal exit, not a special loss case.

## 6.6 Construction recipe

Frozen pair `(A, B) = (SOLUSDT-PERP.BINANCE, ETHUSDT-PERP.BINANCE)`;
`N_A = N_B` USD-equal at fill, re-marked but never re-sized mid-trade.

```
rr_t  = ln(close_A,t / close_B,t)
mu_t  = rolling_median(rr_j ; j = t-L_w+1 .. t)               # L_w = 192 (48 h)
dev_t = rr_t - mu_t
sd_t  = rolling_std(dev_j ; j = t-L_w+1 .. t)
z_t   = dev_t / sd_t                                          # require sd_t > 0

entry_short_A_long_B : z_t >= +2.0                            # A rich -> short A
entry_long_A_short_B : z_t <= -2.0                            # A cheap -> long A
exit_convergence     : abs(z_t) <= 0.5
exit_timeout         : bars_held == 48
```

State machine: at most ONE spread position open globally; signals while live are
ignored unless they are the mirror extreme (`abs(z_t) >= 2.0` opposite side),
which closes-and-reverses at next open. Precedence: convergence, mirror
reversal, timeout.

Participation confirmation is deliberately NOT in the anchor, so anchor and
neighbor differ by exactly one condition:

- **Anchor:** entry purely on `abs(z_t) >= 2.0`.
- **NEIGHBOR:** additionally require dislocation-in-one-leg participation —
  `qvz` of the wider-moving leg over the last 6 bars `>= +1.0` while the other
  leg's `qvz < +1.0`, using §4.6's `qvz` with `L_qv = 96`. Rationale and
  prediction: evidence that flow, not a correlated factor repricing, created the
  dislocation should select convergent episodes ⇒ fewer entries, higher hit
  rate. Directly tests WHO the counterparty is.

Accounting: fees/slippage on both legs, funding on both legs separately across
held settlements, spread PnL = leg sum.

## 6.7 Regimes

- **Edge should concentrate:** choppy sideways tape with high pairwise
  correlation punctuated by episodic single-name flow shocks; high-volatility
  de-risking episodes where one leg moves first and others follow; quiet-regime
  rotations between similar-cap majors.
- **Should lose:** structural relative-supply shifts (sustained emission/unlock
  schedules, protocol-specific drawdowns, delisting or insurance-fund
  interventions in one leg ⇒ correlation collapse, spread trends); strong
  trending regimes where the rich leg keeps getting richer; hostile funding
  differentials paying against one leg repeatedly.

## 6.8 Falsification procedure

Killed if ANY of:

1. Post-cost expectancy ≤ 0 / PF < 1.10 / < 2/3 positive folds / populated fold
   PF < 0.80 / MDD > 10 %. Symbol-concentration reporting caveat: with a
   two-instrument book the applicable drop-one gate is drop-one-fold plus
   symbol-contribution reporting; dropping either leg destroys the spread by
   construction. Disclosed up front rather than discovered later.
2. Any stress variant degrades to PnL ≤ 0 or PF < 1.00. Two legs double friction
   (≥ 20 bp round trip), so this family faces a designed handicap versus its
   siblings; acknowledged, not engineered around.
3. Convergence-speed kill: if median holding time approaches the 12-h timeout
   (most exits timeouts, not convergences), behaviour contradicts transient-flow
   convergence ⇒ report `MECHANISM_INCONSISTENT` regardless of PnL.
4. Neighbor prediction fails: participation-consented entries must show ≥ the
   anchor's hit rate. The opposite result says faded dislocations were
   factor-correlated moves rather than flow.

## 6.9 Negative control (machinery-vs-mechanism targeting)

**Control `RVRELVAL-CTRL`: synthetic self-twin leg.** Rebuild the identical
pipeline with leg B replaced by leg A's own price displaced `m = 96 bars`
(24 h): `rr*_t = ln(close_A,t / close_A,t-m)` — a fake partner with matched
statistical texture (scale, autocorrelation, sampling) but no second asset and
therefore no genuine cross-sectional imbalance to unwind. Everything downstream
(median/MAD-type scaling, thresholds, timeouts, costs, folds, fills) is
byte-identical.

Invalidation rule: the causal driver (someone transacted one name and not the
other) cannot operate on a self-twin. If the control posts PF ≥ 1.05 or
expectancy ≥ 0.5 × anchor, the anchor's "convergence" is an artefact of the
normalization/state-machine machinery (spread autocorrelation plus symmetric ±2σ
entries cosmetically rewarded), and the claimed causal sign is rejected.
Secondary diagnostic reported alongside (not a separate scored cell): entering
the spread WITH momentum must lose money; if it profits, the sign claim dies.

## 6.10 Nearest historical families and structural delta

Nearest families: `H-XSECT-REVERSAL-v1/v2`,
`H-XSECT-REVERSAL-BREADTH-CRYPTO-v1` (rank-basket reversal), `H-XSECT-MOM-v1`
(rank-basket momentum), `H-XSECT-FUNDING-PRICE-DIVERGENCE-v1`
(relative-value flavored via funding-vs-price), root `mean_reversion`.

| Dimension | Nearest families | This proposal | Material? |
|---|---|---|---|
| Economic source | behavioural overreaction of ranked winners/losers; momentum persistence of ranked returns; crowding carry | one-sided idiosyncratic flow in a named pair (allocation/unlock/unwind) absorbed by relativizing balance sheets — a flow-motive account, not a mood/rank account | **Yes** |
| Observable construction | cross-sectional rank of trailing returns across N names; funding-vs-price divergence z-score; single-name MR bands | bivariate log-ratio of two named instruments normalized by its own trailing dispersion, executed as an atomic two-leg spread; no ranking operator appears | **Yes** |
| Selection / payoff geometry | long-bottom-k / short-top-k basket rebalanced weekly; single-name MR state machines | two-leg market-neutral spread, capped at one open position, dual exits (convergence/timeout), PnL generated by the difference with common factor cancelled | **Contested, argued yes** — shape similarity to `mean_reversion` acknowledged; difference asserted is the 1×1 pair anchoring plus dual-leg accounting |
| Counterparty-or-regime prediction | recently extreme-ranked coins revert/persist collectively | specific counterparty (unlock/unwind/rotation flow in exactly one leg) plus predicted relief SPEED (median time-to-convergence) | **Yes** |

**Net claim: 4/4 claimed, dimension 3 contestable.** Same disclosure posture as
§4.10: if A7 judges dimension 3 immaterial, this family fails the novelty
requirement alone and dies without amendment. Rescue hygiene: no percentile rank
of returns, no weekly rebalance, no bottom-k/top-k quota, no funding input, no
price level bands, no third leg, no pair substitution permitted even on failure.

## 6.11 Sample feasibility

- Entry rate: `abs(z) >= 2.0` on a well-behaved normalized ratio occurs ~2–5 %
  of bars, reduced by clustering and by the one-position-at-a-time state
  machine. Realistic plan **300–900 spread entries/year**, i.e. **100–300 per
  fold** — feasible, lowest headroom of the three.
- Both directions traded ⇒ twice the directional diversity of a one-sided
  version.
- Warmup: 192-bar window ≪ 34,944 pre-window bars per leg; both legs gap-free in
  scored territory apart from the explained pre-fold boundary run.
- Principal feasibility concern is flooring out on trades, not data (see §9).

Verdict: **feasible with medium-high confidence**, headroom warning attached.

## 6.12 Audit cost estimate

Single synchronized pair (~70 k rows), simple rolling stats: < 1 min per
run-cell; 15 stress + 15 repro runs ⇒ **~0.3–0.8 CPU-hours** ⇒ ≤ **1 wall-clock
hour** at cap 1. Cheapest of the three.

## 6.13 Frozen cell configuration

**Anchor `RVRELVAL-ANCHOR`**

| item | value | constant class |
|---|---|---|
| leg A (base) | `SOLUSDT-PERP.BINANCE`, rank 2 in the frozen pre-window manifest | manifest-ranked |
| leg B (quote) | `ETHUSDT-PERP.BINANCE`, rank 1 | manifest-ranked |
| pair substitution | forbidden on any failure outcome | by design |
| `L_w` (centre/scale window) | 192 bars (48 h), trailing inclusive | C |
| entry threshold | `abs(z_t) >= 2.0` | S |
| convergence exit | `abs(z_t) <= 0.5` | S |
| timeout | 48 bars (12 h) | C |
| max concurrent spread positions | 1 globally | by design |
| participation confirmation | OFF in anchor, ON in neighbor | structural delta |
| notional | USD-equal legs at fill, never re-sized | by design |
| embargo / folds | 72 h / 3 | uniform policy |

**Neighbor `RVRELVAL-NB` — one structural addition only:** entry additionally
requires dislocation-in-one-leg participation — `qvz` of the wider-moving leg
over the last 6 bars ≥ +1.0 while the other leg's `qvz < +1.0` (same `qvz`
definition as §4.6, `L_qv = 96`). Theory being tested: abnormal participation
confined to a single leg evidences flow rather than a correlated factor repricing,
so it selects episodes where a counterparty motive exists to be faded.
Prediction: fewer entries with higher hit rate; failure rejects the flow
attribution rather than merely lowering PnL.

**Control `RVRELVAL-CTRL`** is the third scored slot (§6.9). Cells used = 3.

---

## 7. Cross-family independence and packaging summary

Independence across MY OWN three (A5 may verify pairwise non-overlap):

| Axis | FORCEDFLOW | INFSPILL | RVRELVAL |
|---|---|---|---|
| Conditioning variable | own-bar participation/extreme trio | benchmark shock magnitude | bivariate log-ratio deviation |
| Legs | 1 (single name, both signs) | 1 (single name) | 2 (atomic spread) |
| Trigger type | joint-extreme event | magnitude-gated event | threshold crossing |
| Holding horizon | 4 h | 8 h | ≤ 12 h |
| Cross-sectional info needed | no | yes (benchmark) | yes (pair) |
| Position cap | per-symbol | per-symbol | global 1 |
| Funding sensitivity | incidental | incidental | material (two legs) |
| Common-mode beta exposure | low (short-lived, both sides) | medium | ~zero (neutral by construction) |
| Tunable scalars exposed | none beyond declared multiples | none | none |

No mechanism conditions on the same observable as another, and none can be
derived from a historical family by renaming, re-thresholding, re-cadencing or
symbol substitution. Each declares 3 cells ⇒ 9 candidate slots if all three were
selected; the contract allows at most 2 families sprint-wide, so A5/A7 choose.

Recommendation, offered without knowledge of A8's submissions and without any
performance information: prefer `INFSPILL` on feasibility and novelty
cleanliness; prefer `RVRELVAL` on geometric distinctness (nothing two-leg
exists in the inventory); prefer `FORCEDFLOW` on counterparty realism, accepting
its contested third dimension and thinner sample.

Audit-cost roll-up if two of mine are selected (max 6 cells): 60 runs
(30 stress + 30 repro) at 1–4 min/run ⇒ **~1–3.5 CPU-hours** scoring work,
serialized ⇒ **~2–4 wall-clock hours**, leaving margin inside the 12-hour clock
for prelaunch gates, golden/parity tests and the terminal audit. Estimates are
deliberately conservative, not best-case.

---

## 8. UNAVAILABLE_FAIL_CLOSED items

Recorded so A5/A7 treat these as sizing caveats, not silent assumptions:

1. **Numeric sample floor is not visible to me.** PLAN §12 lists "sample floor"
   as a hard gate, and no threshold constant exists in any document I am
   permitted to read. Every feasibility statement above is an absolute count
   (events/year, events/fold), never "passes the floor". A5 must apply the
   frozen floor; `FORCEDFLOW` and `RVRELVAL` both have a real chance of
   undercutting it.
2. **Per-symbol funding settlement row counts appear in no readable manifest**
   (files carry byte sizes only). I rely on BTC's audited completeness proof
   (1,095 settlements, cadence mode 480 min) plus the selection rule's blanket
   "held-exposure funding proof". Native-funding accounting therefore cannot be
   pre-sized by me; if a symbol settles at 3,600 s instead of 28,800 s, accrual
   resolution improves and no feasibility claim changes materially, but A6
   should confirm rather than inherit the assumption.
3. **Open-interest / liquidation-feed data unavailable.** `FORCEDFLOW` is built
   to need no OI stream; had OI existed, observing actual deleveraging events
   would be a stronger version of the same question. No proposal here may be
   implemented by fetching new data — that would violate the frozen-data rule
   and would require separate authorization.
4. **Fold-boundary divisibility** of the 365-day scored window into 3 folds plus
   72-h embargo strips is an A5 freeze item I cannot resolve; per-fold counts
   assume ≈121 scored days and are marked approximate.
5. **Maker fees / rebates unknown** to me; all costing assumes the
   preregistered taker-plus-tick baseline. None of the three mechanisms depends
   on maker fills, so no feasibility statement hinges on this.
6. **Scoring/statistics internals are unread by design** (blinding firewall):
   I cannot confirm which of the Stage-A concentration metrics A5 will compute
   natively versus derive from my specs; the specs above therefore define every
   quantity they depend on explicitly rather than referencing library behaviour.

## 9. Non-rescue attestation

- None of `H-VOLCOMP-BRKOUT-v1`, `H-FUNDCROWD-MR-v1/v2`,
  `H-XSECT-REVERSAL-v1/v2`, `H-XSECT-REVERSAL-BREADTH-CRYPTO-v1`,
  `H-XSECT-REVERSAL-BREADTH-EQUITY-v1`, `H-XSECT-MOM-v1`,
  `H-XSECT-FUNDING-CARRY-v1`, `H-XSECT-FUNDING-PRICE-DIVERGENCE-v1`,
  `H-V9-TSTREND-v1`, `H-V9-VOLSHOCK-v1`, nor any root strategy family
  (`ema_atr`, `mean_reversion`, `regime_switch`, `trend_pullback`, `breakout`,
  `reclaim_mr`, `markdown_breakdown`, `vol_compression_breakout`) contributed a
  lookback, threshold, cadence, symbol, cap, direction or filter to any design
  above.
- Every constant's derivation is stated in §3 and inside each recipe; nothing is
  presented as inherited practice.
- If any selected family fails Stage-A, permitted outcomes are only the PLAN
  §12/§13 verdicts. No retuning, no substitute symbol, no replacement cell once
  metrics are visible. Controls are never promoted.
