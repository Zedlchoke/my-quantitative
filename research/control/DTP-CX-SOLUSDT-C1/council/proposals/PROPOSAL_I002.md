# PROPOSAL DTP-CX-SOLUSDT-I002 — INTRADAY BTC→SOL LEAD-LAG DIFFUSION (two-sided)

- Lane: `p1` · Role: `blind-proposer` (playbook collector/definer) · Date: 2026-09-27 (UTC)
- Cycle: `DTP-CX-SOLUSDT-C1` · Parent program: `DAYTRADE-PLAYBOOKS-PROGRAM-V1`
- Measured worktree HEAD at proposal time: `9ba72e6cd2b28a039791cc6a6f75e8ac10ef1cb2`
  (branch `orca/dtp-cx-solusdt-c1-integration`). No commit made (lane writes only;
  commit_sha null by dispatch).
- Outcome-blind lane. Diet: master plan §3.3/§4.2/§6.4–6.5/§7, child plan §3, frozen
  taxonomy row 12 (OPEN-KILLRISK — the only "not-yet-measured" row), ERP umbrella
  §5.3/§5.5, crypto dead-class labels from `FAMILY_FAILURES.jsonl` + taxonomy
  Bảng 3. No outcome surface, no PnL, no sealed/holdout file was sought or read.
- Taxonomy route: **row 12 — cross-asset lead-lag intraday (BTC → alt)**, the
  single pre-council OPEN-KILLRISK row. This proposal does NOT claim row 12 is
  alive; it specifies the identity so the three kill-risks can be **measured**
  pre-PnL, and pre-declares the BLOCKED_DATA branch.

> **Chưa có PnL nào được xem hoặc tính toán cho identity này.**

## 1. Signal definition (exact, closed-bar constructible per master §4.2; final pins at trial freeze)

- **Clock/venue:** UTC; BTCUSDT and SOLUSDT USDⓈ-M perpetuals, same venue (Binance);
  BTC frame = 1m (primary) or 5m (secondary frame — exactly one frame frozen);
  exchange timestamps, PIT-aligned; no `available_at` beyond bar close.
- **Signal event E(t):** BTC bar `[t−1m, t)` **closes** with confirmed move
  `|close/open − 1| ≥ θ`. θ is frozen at trial freeze; the candidate values
  {0.15%, 0.25%, 0.40%} on 1m (equiv. {0.3%, 0.5%, 0.8%} on 5m) are enumerated
  ONLY for the pre-freeze power/cost grid (P-29 one-line grid), never tuned after
  any outcome.
- **One-shot discipline:** if a prior event's SOL position is still open, the new
  event is skipped (no stacking, no averaging into events).
- **Direction:** `sign(r_BTC)`. Symmetric by construction — two-sided.
- **Entry:** first tradable SOL quote **strictly after** the BTC signal-bar close
  timestamp: taker fill at the **opposite-side quote** of the first bookTicker
  quote with timestamp > signal-bar close (buy at ask if long; sell at bid if
  short). No same-bar fill based on intrabar high/low ordering
  (`NOT_CONSTRUCTIBLE_INTRABAR` law).
- **Exit (combination pinned at trial freeze; NO post-PnL amendment):** (a) fixed
  time-stop — exit at the close of bar `t+Δ` (Δ frozen, candidate class: minutes);
  (b) SOL-side hard stop at frozen adverse move `s`; (c) **flat-by rule:** force-
  flat before any 8h funding settlement boundary the window would otherwise cross,
  and before an opposing BTC signal. Rationale for (c), declared now: this keeps
  the identity out of the dead funding-adjacent family (taxonomy row 10) and makes
  funding a structural-zero by fixture, declared rather than assumed.

## 2. Information layer — the "SOL not yet adjusted" series (A7-F1 law)

The mechanism's load-bearing claim is that SOL lags BTC information. That lag must
be measured by named PIT series, which must pass the data gate:

- **IL-1: SOL aggTrades time-of-sales.** Per event: timestamps and sizes of SOL
  trades in `[t_close, t_close+δ]` vs a same-hour pre-event baseline rate; measures
  trade-tape repricing lag `Δ_trade = t(first SOL trade response) − t(BTC close)`
  and the post-confirm trade-price path vs the BTC-implied move.
- **IL-2: SOL bookTicker quote sequence.** Best bid/ask updates with timestamps;
  measures quote staleness `Δ_quote` = time until the SOL best quote moves ≥ a
  frozen fraction of the BTC move, plus quoted-spread behavior at event time.

**Explicit BLOCKED_DATA branch (no proxy substitution — master §3.3 / A7-F1 law):**
if aggTrades or bookTicker coverage is insufficient at the data gate (coverage-
verify per contract, per master §3.3 mandatory gate list), **I002 enters F-0 as
`BLOCKED_DATA`**. The identity's entry/exit rules are constructible from klines +
fill quotes, but without IL-1/IL-2 the payer claim is unverifiable — the identity
is NOT silently re-specified onto a kline-derived lag proxy (that would be a
`PROXY_NOT_ORDERBOOK` mislabel of the mechanism and is prohibited).

## 3. Payer hypothesis (and its fictional-counterparty exposure)

**Hypothesis:** SOL perp book makers quoting stale two-sided prices relative to
already-public BTC information are adversely selected by informed takers; the
taker harvests the pick-off premium (stale spread component + repricing drift
until quotes catch up). Why they must pay: makers post quotes without conditioning
on every BTC 1m confirmation — refresh latency (matching engine + feed processing)
and quote-posting economics put a floor under staleness. Why it does not
arbitrage away instantly: maker competition narrows spreads but cannot zero the
latency floor; it can erode it — that erosion is a declared persistence risk
(premium expected to decay over sample; decay profile itself measured, and
fold-concentration of any surviving premium checked at K-CONC).

**Fictional-counterparty risk, named:** on a single-venue panel we cannot observe
who is on the other side. The "stale maker" may be fictional — the real
counterparty may be an informed fast maker who repositions within the same tick,
in which case our fills occur precisely when the quote is already fair and adverse
selection runs against us. This is SRLV §7 veto exposure. It is answered only by
measurement: IL-1/IL-2 must demonstrate **positive event-time staleness before any
scored cell**, and the payer veto at F-0 applies if staleness ≈ 0.

## 4. The ten §5.3 fields

1. **Payer.** Stale-quote SOL makers adversely selected by BTC-informed takers
   (§3). Fails if IL staleness is not demonstrably positive at event time
   (fictional-counterparty veto).
2. **Premium.** Expected gross capture per event = stale fraction of the SOL
   spread at event time + drift until repricing completes, in bps per event.
   Honest prior, declared before any data: p50 spread census is 0.469 bps, and the
   declared fee-dominated RT ceiling is ~11–13 bps — so the naive prior is that
   pure-staleness capture is **single-digit bps and below ceiling**. The identity
   survives only if event-time capture (events cluster in high-vol moments where
   spread/staleness widen) clears the ceiling at the frozen θ and Δ. This tight
   band is exactly what the K-COST grid measures; a negative ceiling ⇒ VETO
   pre-PnL (VOL-NG1 precedent).
3. **Persistence.** Structural floor (latency) with erosive pressure (makers
   conditioning on cross-asset signals; colocation arms race). Erosion over the
   window is an expected finding, not a surprise; premium must not be
   concentrated in one early fold (K-CONC).
4. **Risk transferred.** Intraday directional risk over the Δ horizon, both
   sides. Named tail: SOL discontinuity against the position between BTC confirm
   and SOL fill (gap-through on thin book); absorbed by taker crossing and
   stress-covered ×1.5/×2.0. No carry risk by the flat-by fixture.
5. **Observable.** Signal: BTC 1m/5m klines (closed bars) + SOL bookTicker fill
   quotes, exchange-timestamped. Information layer: IL-1 (aggTrades) + IL-2
   (bookTicker), coverage-verified per contract at the data gate, else
   `BLOCKED_DATA` (§2). Availability evidence at proposal time: SOL 1h klines
   2020-09..2026-08 gapless floor-exact + funding 6,580 settlements bit-exact +
   6-month spread census p50 0.469 bps (PWS-CX-SOLUSDT durable assets, re-verify
   by bytes at gate); BTC 1h 2020-01..2026-08 + 15m catalog 2024-08+ staged; BTC
   1m and SOL 1m/15m NOT yet staged — staging is a data-gate item inside the
   ≤0.5 GB/staging and ≥5.0 GiB-free §3.4 budgets; **if BTC-1m staging breaches
   the disk budget ⇒ `BLOCKED_STORAGE`**, declared, not worked around.
   Event/effective/available/retrieved separated per handbook §13 (all
   observables available at bar/quote timestamps; retrieved = gate date).
6. **Holding horizon.** Minutes (Δ bars on the frozen frame); event-driven clock
   at BTC bar close; hard flat-by per §1(c).
7. **Capacity.** From top-of-book: capacity ≈ event-time top-of-book depth ×
   achievable event rate. Order-of-magnitude reasoning: the premium IS the
   stale-quote pick-off, which decays with own order size (bigger orders walk the
   book and self-consume the staleness), so capacity is small — well below
   institutional size; measured top-of-book depth at the data gate converts this
   into a notional band; depth history beyond the census is absent ⇒ labeled
   `UNMEASURED_BEYOND_TOP_OF_BOOK`.
8. **Costs.** Full RT decomposition, one-line ceiling×power grid (P-29): taker fee
   DECLARED 5 bps ×2 legs + 1 adverse tick ×2 + spread census **at the fill hour**
   (events cluster in vol — census per event hour, not global p50; out-of-window
   fills at declared band ×1.5/×2.0, `FILL_QUALITY_CLASS_declared`). Declared RT ≈
   2×5 bps + 2×~0.5 bps + 2 ticks ≈ **11–13 bps** at current price levels;
   honesty note: the 1-tick component scales with price era (tick 0.01 USDT on a
   $20 SOL = 5 bps/tick vs 0.67 bps at $150), so low-price-era RT is materially
   higher — tick-scaling enters the grid, not averaged away. Funding =
   structural-zero by the flat-by fixture (declared). Stress ×1.5/×2.0 applied to
   the full book.
9. **Falsifier.** Observable results that kill, pre-PnL:
   (a) **K-ANC** — representation |rho| > 0.20 vs `EOS1-E2` ratio-gate dead
   families and xsect momentum/reversal dead shadows on a frozen, committed,
   reproducible representation;
   (b) **payer veto** — IL-1/IL-2 event-time staleness ≈ 0 (fictional counterparty);
   (c) **K-COST** — negative ceiling on the θ×power grid (declared RT ~11–13 bps
   vs measured per-event gross capture);
   (d) **K-CTRL** — placebo (below) reproduces ≥0.5× anchor, or inverted control
   out-earns anchor (never read backwards as signal — P-28);
   (e) **K-POWER** — fewer than the ≥100 closed RT floor or <2 vol regimes with
   occupancy floors met; any positive sub-power result = INCONCLUSIVE.
10. **Control and baseline.** Causal control: clock-shifted placebo — the same
    BTC events re-timed +24h onto the SOL clock (delay-pair Q-4 discipline for
    sub-hour; constructible null that moves the signal — Q-11), must not
    reproduce ≥0.5× anchor. Inverted control: opposite direction on the same
    event times, runnable, must not out-earn anchor. Baseline: beta-matched
    per-pair baseline set per master §6.2 (SOL 1m same-cadence momentum with the
    same flat-by), anchor must beat baseline with ≥2× margin.

## 5. Power sketch (pre-data; measured counts computed at the data gate BEFORE freeze)

- Event supply at candidate θ: BTC prints 1,440 1m bars/day. At θ = 0.25% on 1m,
  |1m move| events are plausibly single-digit to low-tens per day depending on
  vol regime — **declared as `ESTIMATE_UNMEASURED` here**; the measured event
  count comes from staged BTC 1m klines at the data gate, before freeze, and is
  not re-derived after any outcome.
- Floor implication: ≥100 closed RT total (master §6.5 crypto intraday floor) +
  ≥2 vol regimes + occupancy floors ⇒ at one trade per qualifying event, the dev
  window must supply **≥ ~120 events after one-shot skips** (buffer for the
  open-position skip rule), with both directions individually above occupancy
  floors. If the measured count at the widest admissible θ is short, the identity
  is **not frozen** (K-POWER) and the measured count is recorded.
- Fold-plan honesty (G5 precedent acknowledged, not tuned around): BTC-led
  regimes concentrate long-side events in trending folds; short-side occupancy is
  verified at the gate, and fold-concentration gates (K-CONC > 50%) apply to
  event counts as well as PnL.

## 6. Two-sided capability statement

The identity is symmetric by construction: direction = `sign(r_BTC)`, entry/exit
rules mirror on both sides, both arms are scoreable, and the power/floors plan
above requires both sides to stand on their own occupancy. G5
fold-concentration (structurally unpassable for long-biased BTC 2020–2026) is
recorded as a live risk for a BTC-led mechanism: if short-side events or
short-arm occupancy fall below floors in early folds, the kill rules fire — this
is declared here as the honest shape of failure, not pre-empted by asymmetric
gating (which would itself be a variant-law violation).

## 7. Kill-risk summary (what the skeptic court should demand to see, in order)

1. **K-ANC** representation rho vs `EOS1-E2` ratio-gates + xsect
   momentum/reversal dead shadows (frozen representation, one-shot).
2. **K-COST** ceiling×power grid, one line (P-29): measured per-event gross
   capture vs declared RT ~11–13 bps (tick-era-scaled), at both candidate θ and
   the frozen Δ, base + ×1.5/×2.0.
3. **Payer veto**: IL-1/IL-2 event-time staleness measurement; BLOCKED_DATA
   branch if coverage fails; fictional-counterparty veto if staleness ≈ 0.

## 8. BLOCKED_INCOMPLETE items declared

- Frozen θ, frame (1m vs 5m), Δ, s, and the exact exit combination: pinned at
  trial freeze after the data gate supplies measured event counts and IL
  coverage (declared now as the freeze agenda; no value is pre-committed here
  because both are data-gate outputs, not choices made blind to feasibility).
- Measured event count / month at candidate θ: `ESTIMATE_UNMEASURED` (§5).
- Top-of-book depth band: `UNMEASURED_BEYOND_TOP_OF_BOOK` until the census.

---
*Blindness attestation: no backtest outcome, PnL, or sealed/holdout content was
sought, read, or used. All kill-risk numbers here are declared cost-book
arithmetic and pre-registered expectations, not measured results.*
