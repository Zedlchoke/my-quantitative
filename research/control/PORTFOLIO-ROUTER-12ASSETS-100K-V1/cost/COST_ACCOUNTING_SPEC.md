# COST_ACCOUNTING_SPEC — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (Lane L3)

Program: research-only simulated $100,000 single book trading 12 symbols
(EURUSD GBPUSD USDCAD USDJPY AUDUSD NZDUSD USDCHF XAUUSD XAGUSD BRENT WTI
NATGAS) under a router policy. This document is the **cost + accounting
specification a backtest must implement** so that net PnL is honest: cash,
FX conversion, overlapping positions, margin, funding/swap, roll, gaps,
stops and switching costs. Design artifact — no measurement was performed
in this lane; every measured number is cited to a file, every unmeasured
constant is registered in §4 with a pessimistic default and an owner
unblock. Nothing here is a PnL claim (all 1,200 ideas remain
HYPOTHESIS/NOT_RUN per LANE_CHARTER law 3).

Status conventions: `[MEASURED]` = cited file evidence; `[DEFAULT]` =
declared pessimistic placeholder, no file evidence, listed in §4;
`[DECLARED]` = assumption declared in a cited file but itself unmeasured.

## 0. Inputs read (authority for everything below)

1. `research/control/PORTFOLIO-ROUTER-12ASSETS-100K-V1/LANE_CHARTER.md` — lane scope/laws.
2. `research/control/DATA-FOUNDATION-SIXSOURCE-V1/FINAL_REPORT.md` — source-1 row: IBKR FX two-sided LIVE streaming AVAILABLE_VALIDATED from 2026-09-28T02:03Z, prospective only, **spread p50 0.1–0.6 pip in the ONE 02Z hour-bucket**; commission/swap/rollover-clock/min-size/slippage UNMEASURED pending owner statement.
3. `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/broker_cost_probe_FX_majors_2026-09/VERDICT_session2.md` — cost-component table (components 1–10), stress multiplier FROZEN 2.0, whatIf forbidden (margin NOT_RUN by law), owner-unblock document list.
4. `.../broker_cost_probe_FX_majors_2026-09/EVIDENCE_sanitized_2026-09-26.json` — minTick 5e-05 on EURUSD/GBPUSD/USDCAD/AUDUSD/NZDUSD (IDEALPRO CASH), `minSize` null, two-sided empty in weekend window.
5. `.../broker_cost_probe_FX_majors_2026-09/ERRATUM_2026-09-28_sixsource.md` — E1: weekend closure re-classified, two-sided stream valid 2026-09-28T02:03:35–02:08:38Z with per-pair p50/p90 spreads (below); E2: secdef minTick 0.5 pip vs stream 0.1-pip granularity discrepancy.
6. `research/control/SHARED-PORTFOLIO-100K-V1/README.md` + `epoch_config.json` + `AUDIT_sizing_fx_shared_100k_v1.md` — $100k single-book precedent: GROSS/HYPOTHETICAL FX disclosure, UNAVAILABLE ≠ $0, USD vs USDT separate books, capital rules R1–R5, pip value $10/pip/lot for USD-quote majors, margin 30:1 majors `[DECLARED]`, caps proposal 250/150/150% + 15% aggregate stress budget.
7. `research/control/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/UNIFIED_STRATEGY.md` §6 (cluster caps: USD-bloc ONE risk ≤2%, precious/energy caps, NATGAS ≤1%; per-trade 0.25–0.5%; cross-cluster netting rule) and §7 (execution guardrails: sessions, NATGAS/XAGUSD 2–3× cost warning, weekend gap policy, roll cost into hypothesis).
8. `.../symbols/NATGAS.md` §1.1–1.3 (10,000 MMBtu/contract, $0.001 tick, monthly roll, unadjusted broker chart distortion, CFD spread $0.02–0.06/MMBtu widening 3–10× at events, margin 1–5%, financing negative-for-long, weekend gaps 2–5%/10%+, EIA 5-s slippage 0.5–2%), `.../symbols/XAGUSD.md` §1.1–1.2 (5,000 oz/lot, retail spread $0.02–0.05/oz ≈ 3–8 bps = 3–10× FX majors, Asia 2–5×, swap negative-for-long, CME margin-hike cascade), `.../symbols/XAUUSD.md` §1.2 (Kitco OTC 4,144.80/4,146.80 ≈ $2 spread 2026-09-28; CFD long swap negative; rollover window ~21:00–22:00 spread widening; Asia 1.5–3×), `.../symbols/BRENT.md` (Asia CFD spread 2–5×; monthly ICE roll, spread widens 2–3 sessions around roll; **S10 back-adjustment guard: keep only systems whose signals differ <20% between back-adjusted and unadjusted continuous series**), `.../symbols/WTI.md` §1 (weekend = 48h event risk released in one reopening tick).
9. `NOTES.md` §1 — NautilusTrader 1.230.0 bot context, one-way/NETTING OMS precedent.

Lane-law boundary: no other lane's outputs were read (L1/L4 artifacts do
not exist yet at time of writing; `datacost/`, `router/`, `plan/` are
empty). Where vehicle choice is L1's authority, this spec is written
vehicle-class-parametric (energy: CFD and futures paths both specified).

---

## 1. Cost stack per vehicle class

### 1.1 FX spot — 7 pairs (EURUSD GBPUSD USDCAD USDJPY AUDUSD NZDUSD USDCHF)

Measured state (the ONLY measured cost fact in this program):

- Two-sided IDEALPRO paper-streaming spreads, ONE hour-bucket (02Z),
  2026-09-28T02:03:35–02:08:38Z, thin Sunday-evening ET book, n =
  1,373–1,982 valid obs/pair `[MEASURED, ERRATUM E1]`:

  | Pair | p50 (pip) | p90 (pip) | max (pip) |
  |---|---|---|---|
  | EURUSD | 0.1 | 0.2 | 0.3 |
  | GBPUSD | 0.4 | 0.5 | ~ |
  | AUDUSD | 0.1 | 0.2 | ~ |
  | USDCAD | 0.6 | 0.6 | 0.8 |
  | USDJPY | 0.4 | 0.6 | ~ |
  | NZDUSD | — | — | not in this probe |
  | USDCHF | — | — | never probed two-sided |

  (p50/p90 per ERRATUM E1; "max 0.3–0.8" across pairs per FINAL_REPORT.)
- Tick geometry: secdef `minTick` = 5e-05 (0.5 pip) on the four
  4-decimal pairs, 0.005 on USDJPY `[MEASURED, EVIDENCE_sanitized +
  ERRATUM E2]`; the live stream steps in 1e-05 (0.1 pip) increments, so
  **minTick is NOT a spread floor** — the two facts stand side by side
  and neither may be used to rescue or kill a cost argument until the
  venue's order-price rule is measured (owner statement).
- Everything else — commission, swap LONG/SHORT, triple-swap calendar,
  rollover clock, minimum size, execution slippage — **UNMEASURED**
  `[VERDICT V3 table rows 2–7]`.

Cost components charged per fill (see §3 kernel for exact formulas):

| Component | Base value | Status |
|---|---|---|
| Spread (per side) | hour-bucket schedule S(): measured-bucket base = p90; unmeasured buckets = 2 × measured p90, floor 0.5 pip; USDCHF/NZDUSD all buckets = 1.2 pip | p90 `[MEASURED in 02Z only]`; rest `[DEFAULT U1]` |
| Commission (per side) | 0.35 bps of notional (≈ $3.5 per $100k lot) | `[DEFAULT U2]` |
| Slippage beyond spread (per side) | 0.2 pip non-event; 1.0 pip inside event windows (CB ± window, top-tier data ±30 min, rollover 21:00–23:00 UTC per UNIFIED §7) | `[DEFAULT U3]` |
| Overnight swap | 1.0 pip/night charged AGAINST the held position (never income), Wednesday ×3 (spot T+2 settlement weekend-skip convention) | `[DEFAULT U4]` |
| Rollover clock | daily boundary 22:00 UTC (17:00 ET); positions open at boundary accrue that night | `[DEFAULT U5]` |
| Minimum size | 0.10 lot blocking threshold (R4 precedent) | `[DECLARED in epoch_config R4]` |
| Pip value | $10/pip/lot USD-quote majors (price-independent); USD-base pairs (USDCAD/USDCHF/USDJPY) pip value converts per §2.2 | `[DECLARED in AUDIT §1]` |

Pessimistic-default rationale (recorded so no one mistakes defaults for
measurements): the 02Z bucket is 1 of 24; its book was thin (Sunday ET
reopen +0–5h). Unknown-bucket bias direction is unknown, so the default
DOUBLES the only measured p90; swap is charged as pure cost in both
directions, which kills carry-favorable accounting until the statement
unblocks real two-sided rates.

Upgrade path: (a) SIXSOURCE bounded streaming sessions accumulate
per-bucket bands (scheduled fix 14:50Z / rollover 20:50Z windows, 2–3
sessions/week, per FINAL_REPORT §pilot) — when a (pair, bucket) cell
reaches ≥200 valid two-sided observations, its default is replaced by
the measured p90; (b) owner Activity/Flex statement with FX trades +
overnight FX positions at `~/.my-quantitative-data/ibkr_statement/`
unblocks commission/swap/triple-swap/rollover-clock/min-size
(`[VERDICT owner-documents list]`), replacing `[DEFAULT]` rows U2–U6.

### 1.2 Metals spot — XAUUSD, XAGUSD

No measurement exists for either metal (XAUUSD probe PAUSED and not
retried `[VERDICT §boundaries]`; XAGUSD never probed). Lane knowledge
that motivates the defaults (all `[DECLARED]` in the cited brainstorm
files, none measured by this workspace):

- XAGUSD: retail spread $0.02–0.05/oz at ~$65 ≈ 3–8 bps full spread =
  3–10× majors FX; Asia 2–5× widening; swap negative for long;
  5,000 oz/lot → notional ≈ $325k/lot at $65 — sizing must respect this
  against a $100k book `[XAGUSD.md §1.1–1.2]`.
- XAUUSD: institutional OTC reference $2 spread on ~$4,145 ≈ 4.8 bps
  full (large size, 2026-09-28 Kitco via XAUUSD.md §1.2); retail CFD
  wider; Asia 1.5–3×; rollover-window widening; CFD long swap negative
  `[XAUUSD.md §1.2]`.
- UNIFIED §7: NATGAS + XAGUSD carry a "2–3× more expensive
  spread/margin" warning; high-frequency ideas on expensive instruments
  auto-derank.

Cost components:

| Component | Default | Status |
|---|---|---|
| Spread (per side) | XAU 4 bps of notional (≈2× institutional full-spread reference); XAG 8 bps of notional (top of retail range) | `[DEFAULT U7]` |
| Event/rollover/Asia multiplier | ×3 inside 21:00–23:00 UTC rollover, ×2 Asia session (00:00–07:00 UTC London-ref), per cited widening ranges | `[DEFAULT U7]` |
| Overnight financing | charged against position both directions: XAU 3.0% p.a., XAG 4.0% p.a. on notional, 7-day accrual, Friday ×3 (weekend funding convention) | `[DEFAULT U8]` |
| Unit size | XAU 100 oz/lot, XAG 5,000 oz/lot notional conventions; blocking min-unit 0.10 lot | `[DEFAULT U15]` |
| Margin | 20:1 initial (5%) | `[DEFAULT U12]` |

Upgrade path: extend the SIXSOURCE read-only two-sided streaming probe
to the metals conids (owner re-enables the paused XAU template; same
bounded-session accumulation as FX); broker contract specification or
statement for swap/min-size.

### 1.3 Energy — BRENT, WTI, NATGAS (CFD path default; futures path if L1 selects it)

No measurement exists. Lane knowledge `[DECLARED, NATGAS.md §1.1–1.3;
BRENT.md; WTI.md §1]`:

- NATGAS: NG futures 10,000 MMBtu/contract, $0.001 tick; CFD spread
  $0.02–0.06/MMBtu ≈ 0.7–2% of price at $3, widening 3–10× around EIA
  Thu 10:30 ET, winter model runs, Sunday open; margin group 1–5%
  (20–100×), some brokers cut leverage in winter/storms; daily
  financing negative for long; monthly roll event; broker "continuous"
  chart NOT roll-adjusted — backtests on it are distorted by contango/
  backwardation; weekend gap 2–5% common, 10%+ on cold snaps; EIA-window
  stop slippage 0.5–2% within 5 seconds.
- BRENT/WTI: Asia CFD spread 2–5×; monthly roll around expiry with
  spread widening 2–3 sessions; war-regime weekend gap structural
  (WTI: 48h of event risk released in one reopening tick); term-structure
  roll-yield is a first-class cost/return component (backwardation
  long-tilt families exist to harvest it — the cost book must charge
  its symmetric negative).

Cost components (CFD path):

| Component | Default | Status |
|---|---|---|
| Spread (per side) | BRENT/WTI 6 bps of notional; NATGAS 100 bps (1.0% — top of the daily full-spread range, charged per SIDE) | `[DEFAULT U9]` |
| Event multiplier | ×3 inside EIA windows (Wed 10:30 ET WTI / Thu 10:30 ET NATGAS ±15 min), Sunday reopen first 15 min, OPEC± days | anchored to the 3–10× widening range `[DECLARED NATGAS §1.3]`, applied as `[DEFAULT U9]` |
| EIA stop slippage | stop-market fills inside the EIA window additionally graded worst-fill + 1% | `[DEFAULT U13, anchored to 0.5–2% in 5s NATGAS §1.3]` |
| Overnight financing | charged against position both directions: BRENT/WTI 5.0% p.a., NATGAS 8.0% p.a. on notional, 7-day accrual, Friday ×3 | `[DEFAULT U10]` |
| Roll cost per switch | measured |M1−M2|/M1 at the broker roll timestamp when curve data exists; otherwise flat charge BRENT/WTI 0.20%/switch, NATGAS 1.00%/switch | `[DEFAULT U11]` |
| Margin | initial 5% (top of 1–5% range = most capital blocked), NATGAS winter/event multiplier 1.5× | `[DEFAULT U12]` |

Futures path (if L1 selects exchange futures): commission per contract +
exchange/broker fees `[DEFAULT U16]`, exchange initial/maintenance margin
from CME/ICE schedule (L1/L4 supply; until then UNMEASURED), roll at
exchange calendar with the same |M1−M2| roll charge, and the
back-adjustment law §2.8 applies verbatim.

---

## 2. Accounting model for the shared $100,000

### 2.1 Single book, USD cash ledger

- ONE simulated account, opening cash = $100,000.00 USD, base currency
  USD. No sleeve fencing of capital (unlike SHARED-PORTFOLIO's 2-sleeve
  fence): the router's allocation IS the capital allocation; risk
  fencing is by cluster caps (§2.4), not by capital partition
  `[inheritance: SHARED-PORTFOLIO discipline of ONE book + declared
  allocation, re-parameterized for 12 assets by L4]`.
- Double-entry ledger, all lines timestamped UTC to bar-close /
  fill-time granularity, append-only. Line types: `FILL`, `CASH`
  (cost/financing), `FXCONV`, `ACCRTUAL` (swap), `ROLL`, `MARGIN`,
  `MARK` (valuation), `GAP_FILL`.
- Cash interest: 0 credit, 0 charge `[DEFAULT U17]`.
- Missing price for a mark or conversion = `UNAVAILABLE`, never $0,
  and the affected equity cell is reported UNAVAILABLE (no silent
  forward/backward fill) `[inherited law: SHARED-PORTFOLIO README
  "Thiếu dữ liệu = UNAVAILABLE, không bao giờ $0"]`.
- Netting: one net position per symbol (one-way/NETTING OMS precedent
  `[NOTES.md §1]`). Multiple simultaneous signal sources on one symbol
  keep virtual sub-position attribution but margin/exposure/fills are
  computed on the NET book position.

### 2.2 FX PnL conversion rules (no lookahead)

- USD-quoted pairs (EURUSD GBPUSD AUDUSD NZDUSD): PnL accrues directly
  in USD. Pip value $10/pip/lot `[DECLARED AUDIT §1]`.
- USD-base pairs (USDCAD USDCHF USDJPY): position PnL is denominated in
  CAD/CHF/JPY. Conversion to USD happens at **decision-time rates
  available at or before the conversion event** — the same bar's close
  of the converting pair itself, never a future print (PIT law; L1's
  PIT_SOURCE_TABLE governs available_at). Formula: `usd_value =
  quote_ccy_amount / rate_USDXXX(t_bar_close)`.
- Conversion cost: converting non-USD realized PnL is itself a crossing
  — charge 0.5 × S(converting pair at t) on the converted notional
  `[DEFAULT U14]`. Unrealized marks convert at mid (reporting only).
- Every conversion writes an `FXCONV` ledger line (rate source, rate,
  timestamp) so equity is reconstructible.

### 2.3 Position overlap & net USD exposure reporting

Reported at every decision timestamp and every fill:

- Per-symbol signed notional in USD and net position.
- Per-cluster gross (Σ|notional|) and net (Σ signed directional
  notional) exposure, in USD and as % of equity.
- Account net USD exposure: Σ over all FX positions of the signed USD
  leg (long EURUSD = short USD notional×rate; long USDCAD = long USD
  notional). Precedent for why: 1.5 lot same-side on two majors ≈
  −$368.7k USD-directional on $100k capital — same-side USD exposure
  ADDS UP `[AUDIT §3]`.
- Overlap disclosure: symbols with >1 virtual sub-position, and same-
  cluster positions in the same direction, listed with their combined
  stress scenario (cluster adverse move per UNIFIED §6 sizing rules).

### 2.4 Cluster exposure caps mechanics

Cluster map (UNIFIED §2 Layer 0, binding for cap accounting):

| Cluster | Symbols | Cap mechanics |
|---|---|---|
| USD-bloc | EURUSD GBPUSD USDJPY USDCHF | **counted as ONE risk**: cluster directional risk cap; positions on different USD-bloc symbols DO NOT diversify each other |
| Commodity-FX | USDCAD AUDUSD NZDUSD | cluster cap; cross-linked to Energy cluster for netting |
| Precious | XAUUSD XAGUSD | cluster cap |
| Energy | BRENT WTI | cluster cap |
| NATGAS | NATGAS | own cap, LOWER than others (fat tail; widow-maker) |

Mechanics (numbers are L4's authority; the accounting engine implements):

1. "Risk" per position = stop-distance × size in USD at entry (per-trade
   risk 0.25–0.5% equity per UNIFIED §6; ATR-based stops, no round
   static numbers).
2. Cluster risk = Σ per-position risk within cluster, same-direction
   additive; opposite-direction positions within a cluster net BEFORE
   the cap check (netted risk shown alongside gross).
3. Cross-cluster netting (UNIFIED §6): energy-long may be partially
   hedged by inverse commodity-FX WHEN the coupling condition is open;
   netted risk is charged to the LARGER cluster's cap.
4. Cap binding order inherits capital rules R1–R5 mechanics
   `[epoch_config.capital_rule.laws]`: R1 risk-reducing closes always
   allowed; R2 new risk processed in a declared performance-independent
   priority order at the same decision timestamp; R3 a fill that would
   breach cluster cap or total gross cap is scaled to headroom (min of
   the two); R4 scaled unit below min-unit (FX 0.10 lot; metals/energy
   0.10 lot `[DEFAULT U15]`) → BLOCKED + blocked_signals row; R5 caps
   bind NEW signals only.
5. Kill-switch liquidations (VIX term inversion, intervention confirmed,
   cluster drawdown >4% in current state per UNIFIED §6) execute as
   risk-reducing closes under R1 at worst-fill grading §2.6 with full
   cost kernel charged.

### 2.5 Margin accounting

- Margin ledger per fill: Σ initial margin per class; equity ≥ Σ
  initial margin to open new risk (hard fence: no leverage beyond
  declared class margin), plus total gross notional cap as a second
  fence (SHARED-PORTFOLIO proposal shape 250% total / per-class 150%
  `[DECLARED PROPOSAL in AUDIT §5 — numbers to be re-derived by L4 for
  12 assets; the ENGINE supports class-level gross caps]`).
- Initial margin per class: FX majors 30:1 (3.33%) `[DECLARED AUDIT §5,
  itself unmeasured — whatIf is forbidden by law VERDICT #9]`; metals
  20:1; energy 5% (top of 1–5% NATGAS range) with NATGAS winter/event
  ×1.5 `[DEFAULT U12]`; maintenance = 50% of initial `[DEFAULT U12]`.
- Margin call: equity < Σ maintenance → new risk blocked; equity <
  0.8 × Σ maintenance → forced liquidation of the worst-performing
  cluster at next bar open, worst-fill grading, full costs charged,
  `MARGIN` ledger line + incident row in the trial record
  `[DEFAULT U12]`.
- Margin-hike stress (metals): a CME-style margin increase scenario
  (XAG margin-cascade mechanism `[XAGUSD.md §1.2]`) is modeled as tier-
  2.0 stress on U12, not as a separate constant.

### 2.6 Stop/gap fills (weekend open-through, worst-fill grading — Q-5)

1. **Stops do not exist over market closure.** Energy + metals held
   over a weekend (allowed only at reduced size per UNIFIED §7 weekend
   policy; the size multiplier is L4's) are marked at Sunday reopen;
   if the reopen gaps through the stop level, the exit fills AT THE
   REOPEN, never at the stop price. NATGAS weekend gaps 2–5% common,
   10%+ possible; WTI releases 48h of event risk in one tick
   `[NATGAS §1.3, WTI §1]`.
2. **Worst-fill grading (Q-5) on every stop/exit evaluation**: on OHLC
   bars, a stop-market for a long fills at `min(bar_open, stop_level)`
   (shorts: `max(open, stop)`); limit entries/exits fill only if price
   trades THROUGH the limit by ≥1 tick (pessimistic touch rule). This
   replaces any "fill at stop price" fantasy and is structural — it
   needs no distributional assumption.
3. **Event-window fills**: EIA windows add the event slippage schedule
   (§1.3) on top of worst-fill grading.
4. FX book carries no weekend gap (24/5 market, weekend flat by
   construction); its closure risk is the swap accrual (§2.7) and the
   Friday-close / Sunday-reopen spread schedule (02Z-bucket band is the
   only measurement; Sunday reopen hours default to the unmeasured-
   bucket rule).

### 2.7 Swap/funding accrual

- FX: accrual at the rollover boundary 22:00 UTC `[DEFAULT U5]`;
  charged against the held position at 1.0 pip/night `[DEFAULT U4]`,
  **Wednesday ×3** (spot T+2 settlement weekend-skip convention). The
  exact clock and real two-sided rates come only from the statement
  (`Interest Accruals` rows, `[VERDICT owner-documents]`).
- CFD (metals + energy): daily financing charged against the position
  per §1.2/§1.3 rates, 7-day accrual with **Friday ×3** (weekend
  funding) `[DEFAULT U8/U10]`.
- Accruals post as `ACCRUAL` ledger lines per night per symbol; the
  NET book compounds them into cash; the GROSS book ignores them by
  definition (§3) and the drag is reported.
- Pessimistic symmetry rule: until measured, funding is a COST in both
  directions — no strategy may earn financing in the backtest.

### 2.8 Roll accounting + back-adjustment law (BRENT.md S10-style guard)

1. **Signals on back-adjusted, PnL on raw.** Trend/regime signals for
   energy (and any futures-based series) are computed on continuous
   BACK-ADJUSTED series with roll-date skip (no synthetic bar spans a
   roll); position accounting uses raw per-contract prices with the
   roll charged explicitly as a `ROLL` line.
2. **Roll cost per switch** = |front − next| / front at the roll
   timestamp when the curve is in the dataset (L1 dependency); flat
   defaults otherwise (§1.3, U11). Broker-roll dates govern the CFD
   path (broker rolls before expiry, spread widens 2–3 sessions around
   it `[BRENT.md]`); no new entries in the roll window (UNIFIED §7 /
   BRENT S54-class guard) — engine enforces the entry block and
   records it.
3. **S10 guard (mandatory for every energy trend family)**: run the
   system on back-adjusted AND unadjusted continuous series; keep it
   only if signals differ <20% between the two; larger divergence =
   roll-artefact edge → family killed `[BRENT.md S10, verbatim
   adoption]`.
4. NATGAS specifics: broker "continuous" charts are NOT roll-adjusted
   and distort lookback `[NATGAS §1.1]` — such series may never be the
   signal source; quoting-convention normalization (×100 vs ×1000)
   before multi-source joins `[NATGAS §1.3]`.
5. Roll charges scale with stress tier like all variable costs (§3.3).

### 2.9 Switching-cost accounting

- Every router state change that changes a symbol's target position
  books BOTH legs at full cost: the closing leg of the old position
  and the opening leg of the new one (entry + exit cost at every
  switch), each through the §3 kernel.
- **No amortization, ever.** Costs are expensed at fill time; they are
  never spread over holding period, never capitalized into basis.
- Switch-count is a first-class reported statistic per trial (switches/
  symbol/period), because a router that flips states pays the kernel
  each flip — the trial identity carries `switch_cost_share` (share of
  total cost drag attributable to switches).

---

## 3. NET vs GROSS books

### 3.1 Two books, identical fills

- **GROSS book**: identical fill prices and positions, ZERO costs
  applied. Exists only for comparability and drag attribution
  (precedent: FX journal GROSS/HYPOTHETICAL disclosure where no cost
  fields exist `[epoch_config FX-RANGEFADE-2M sizing_law]`). Any GROSS
  number shown externally must carry the HYPOTHETICAL label.
- **NET book**: full §1–2 cost stack applied. **NET is the only
  decision-grade book.** Report triple per trial: GROSS PnL, NET PnL,
  cost drag decomposed (spread / commission / slippage / swap / roll /
  FX conversion / margin-incident) per symbol and per cluster.

### 3.2 Per-trade cost kernel (Q-2: conditional, never flat constants)

```
cost_fill(sym, side, notional_usd, t, order_type)
  = C_spread + C_comm + C_slip

C_spread = 0.5 * S(sym, bucket(t), event(t)) * notional_usd
           # S in bps-of-notional for metals/energy, in pips→bps for FX
C_comm   = rate_comm(class) * notional_usd
C_slip   = slip(class, order_type, event(t)) * notional_usd

overnight: cost_swap(sym, nights_held_incl_Wed_mult)   # §2.7
switch:    kernel charged on BOTH legs of every state change  # §2.9
roll:      C_roll(sym, roll_date)                        # §2.8
conversion:0.5 * S(conv_pair, bucket(t)) * converted_notional  # §2.2

ALL variable components × stress_tier ∈ {1.0, 1.5, 2.0}
```

`S()`, `slip()`, `rate_comm()`, swap rates are **functions of symbol,
hour-bucket, and event-window** — a flat constant cost model is
non-compliant with this spec. Event-window flags (CB blackout windows,
EIA windows, rollover window 21:00–23:00 UTC, Sunday reopen, OPEC days)
follow UNIFIED §5/§7 calendars. Every fill record logs: `sym, class,
ts, bucket, event_flags, size, price, cost_components{}, tier,
defaults_digest`.

### 3.3 Stress tiers 1.0 / 1.5 / 2.0×

- All variable cost components (spread, commission, slippage, swap,
  roll, conversion) scale by the tier. The 2.0 anchor follows the
  workspace's frozen stress-multiplier precedent
  `[VERDICT component 10, FROZEN 2.0 lane-F]`.
- A router configuration is "cost-robust" only if its NET edge over
  baselines survives at 2.0× (report all three tiers side by side;
  L4's evaluation protocol consumes this).

### 3.4 Trial identity fields — `cost_tier` block

Every trial run records (consumed by L4's trial identity):

```
cost_tier: {
  cost_kernel_version,          # this spec's version
  defaults_digest,              # sha256 of the resolved parameter table
  stress_tier,                  # 1.0 | 1.5 | 2.0
  spread_schedule: {version, measured_cells: [(pair, bucket, n, p50, p90)]},
  swap_model_id, margin_model_id, roll_model_id + roll_calendar_version,
  unmeasured_count_at_run,      # §4 rows still on defaults
  weekend_policy_flags          # per energy/metals: open-through size multiplier
}
```

Precedent: cost-regime digest boundary at activation
`[epoch_config BTC4H sleeve "cost law 6 bps/side with
cost_regime_digest"]` — same discipline, 12-asset parametric version.

---

## 4. UNMEASURED register (every constant not yet measured)

Owner unblock forms: (A) IBKR Activity/Flex statement (FX trades +
overnight FX positions) placed at `~/.my-quantitative-data/ibkr_statement/`
— never into chat/git `[VERDICT + ERRATUM]`; (B) SIXSOURCE bounded
streaming sessions accumulation; (C) broker contract specification
sheets; (D) L1 data delivery (curves, calendar); (E) post-GO whatIf/
paper fills (forbidden now).

| # | Constant | Pessimistic default until measured | Unblock |
|---|---|---|---|
| U1 | FX spread outside 02Z bucket (23/24 buckets × 5 pairs; all buckets × USDCHF, NZDUSD) | 2 × measured p90, floor 0.5 pip; USDCHF/NZD 1.2 pip | B (≥200 obs/cell → measured p90) |
| U2 | FX commission/side | 0.35 bps of notional | A |
| U3 | FX slippage/side (non-event / event) | 0.2 pip / 1.0 pip | A or E |
| U4 | FX swap LONG/SHORT rates | 1.0 pip/night against position, Wed ×3, no income side | A (Interest Accruals) |
| U5 | FX rollover clock | 22:00 UTC daily boundary | A (dated rollover rows) |
| U6 | FX minimum trade size | 0.10 lot | A or C |
| U7 | Metals spreads (XAU/XAG, per bucket/event) | XAU 4 bps/side, XAG 8 bps/side; event ×3, Asia ×2 | B extended to metals conids; C |
| U8 | Metals overnight financing | XAU 3.0%/yr, XAG 4.0%/yr charged both directions, Fri ×3 | C; A |
| U9 | Energy spreads + event multipliers | BRENT/WTI 6 bps/side, NATGAS 100 bps/side; event ×3 | C; B |
| U10 | Energy overnight financing | BRENT/WTI 5.0%/yr, NATGAS 8.0%/yr charged, Fri ×3 | C |
| U11 | Roll calendar + roll charge per switch | monthly; BRENT/WTI 0.20%/switch, NATGAS 1.00%/switch; measured M1−M2 when D delivers | D + C |
| U12 | Margin initial/maintenance per class + margin-call thresholds + NATGAS winter multiplier | FX 30:1, metals 20:1, energy 5% init / NATGAS ×1.5 winter; maint = 50% init; call < maint; force-flat < 0.8×maint | C; E (whatIf post-GO only) |
| U13 | Gap/stop slippage distributions | none needed — structural worst-fill Q-5 + EIA +1% | E (paper fills post-GO) |
| U14 | FX conversion cost (quote≠USD PnL) | 0.5 × converting-pair spread per conversion | A |
| U15 | Min-unit metals/energy | 0.10 lot blocking | C |
| U16 | Futures-path commission/fees (if L1 selects futures) | $2.5/contract/side + fees | C |
| U17 | USD cash interest | 0 (no credit, no charge) | A |
| U18 | Weekend open-through size multiplier (energy/metals) | engine parameter, default = FLAT over weekend until L4 sets it | L4 + owner |

Count: **18 register rows on defaults** at spec time; measured cost
facts = 1 of 24 FX hour-buckets (5 pairs) + tick-geometry declarations.
No measured fact in this program covers commission, swap, min-size,
margin, metals or energy costs.

Standing rule (inheritance): any default replaced by a measurement
bumps `defaults_digest` and is recorded as a cost-kernel version change;
trials run under different digests are not comparable without
re-running both. UNMEASURED never becomes a favorable assumption; a
result computed under defaults is labeled `NET_DEFAULT_COST` until the
register is empty.

## 5. Inherited laws & disclosures

- GROSS numbers carry HYPOTHETICAL labels; NET-under-defaults carries
  `NET_DEFAULT_COST` (§4). No PnL claim exists in this spec.
- UNAVAILABLE ≠ $0 for any missing mark/rate (§2.1).
- One heavy job / no network / read-only session — honored: this lane
  wrote only its two declared outputs; no git operations performed;
  owner's dirty tree preserved untouched.
