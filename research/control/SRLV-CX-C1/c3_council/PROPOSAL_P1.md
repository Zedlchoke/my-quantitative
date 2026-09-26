# P1 blind proposals — SRLV-CX-C1 outcome-blind mechanism council

Lane: P1 (blind proposer). Outcome-blind honored: no MAP.md / LESSONS.md /
HYPOTHESIS_LEDGER.md / ledger / scored-outcome file read. Sources read: this
dispatch packet + `plans/PLAN_srlv_cx_cohort_1.md` + `plans/PLAN_srlv_program_v1.md`
(law context only). Worktree verified: `.worktrees/srlv-cx-c1/integration`,
branch `orca/srlv-cx-c1-integration`, HEAD `d3f063a05338e498912a16d4678d4451fd0cb838`.

Design note before the proposals. The owner space is heavily fenced:
band-fade + any gate is dead, Donchian-style continuation is dead on BTC
(clock placebo out-earned it), nominal/round-number levels are a dead class
(K-ANC), prior-day/week calendar bands are dead class #1, funding-level and
vol-level sorts are dead, and every long-biased BTC book fails G8. The one
payer that exists in this market and did NOT exist in any dead FX class, and
that has MEASURED data staged (BTC 7,643 fapi + ETH 7,305 Vision settlements),
is the contractual perp funding transfer and the forced de-risking it imposes
on carry-burdened leveraged accounts at known-in-advance timestamps. I
therefore offer exactly two proposals that are the two mutually exclusive
readings of that single payer — H3 (forced flow overshoots and is absorbed ⇒
fade) and H2 (forced flow cascades through the level ⇒ continue). They share a
payer family but make opposite directional claims; at most one can be true,
and each serves as the other's inverted control in the limit. Both are
two-sided by construction (fence 5), both hold strictly inside one funding
interval (flat-by-settlement ⇒ base-book funding cost ≡ 0, measured-path
stress arm on BTC/ETH only), and both encode the payer test in the observable
itself (settlement-window concentration vs shifted placebo) so the fictional-
counterparty veto (BTC-BEAR precedent) has a pre-registered trigger.

Both proposals are labeled PROXY_NOT_ORDERBOOK throughout: no order book,
liquidation tape, or OI history exists; every level/sweep/absorption observable
is geometric from 1h klines, and the payer story must be testable through the
proxy (it is — see Falsifier in each).

---

## P1-A — "SETTLE-SWEEP-ABSORB": settlement-adjacent sweep-then-absorption at pivot-confirmed levels (H3)

**Skeleton (one paragraph).** On 1h klines, maintain pivot-confirmed swing
highs/lows. When a settlement-adjacent bar sweeps an intact level (wick through,
no intrabar ordering assumed) and a LATER bar closes back to the level's
original side (cross-bar reclaim), take the side opposite the sweep at the next
bar open. Hard flat before the next funding settlement. Two-sided by symmetric
construction.

**Ancestry position, stated openly.** The generic sweep-reclaim fade is the
dead band-fade-with-reclaim-gate family. This proposal survives only via the
master plan §2.2 revival clause: H2/H3 payer "stop beyond visible extremes"
died in FX and is revivable only with a NEW payer + new information layer. The
new payer is the funding-settlement forced de-risking flow (perp-specific,
contractual, measured for BTC/ETH); the new information layer is the settlement
calendar (t_known in advance, PIT-legal — the mechanism reads settlement TIMES,
never funding RATE levels, so fence 4 "funding-level gating" is not touched).
Pre-registered concession: if the skeptic lane rules the revival clause
inapplicable, P1-A is withdrawn without scoring (K-F0), no rescue.

### 1. Payer

Who pays: leveraged perp accounts whose cumulative funding carry plus adverse
mark-to-market puts them at margin pressure at the settlement print. For them
the settlement is a contractual cash-out event at a timestamp fixed in advance
(00:00/08:00/16:00 UTC); they cannot "decide not to pay" while holding, and
they cannot wait for a better price because margin pressure is immediate and
balance-sheet-bound, not discretionary. Their exit IS market flow into thin
books, and it clusters at the settlement boundary — that flow overshoots
visible levels (sweeps) and is then absorbed by resident liquidity once the
forced flush ends. Why they cannot arbitrage it away: escaping the payment
requires closing the position — the act of closing is the flow being traded
against. The absorption side earns rent for supplying immediacy at the moment
of maximum forced urgency, a role discretionary forced sellers structurally
cannot take at that moment.

### 2. Premium

Order of magnitude: gross 10–30 bps per event if the forced-flow concentration
is real. Reasoning: BTC/ETH 1h ATR is ~0.4–0.8% in mid-vol regimes; a
settlement-timed overshoot of 0.1–0.5× hourly ATR at a level, reverting within
1–3 bars, is 5–40 bps gross; conditioning on settlement adjacency (≤ ~2% of
hours) selects the tail where carry-forced flow is densest. Net of the ~11 bps
base RT cost book the expected edge is thin — this proposal is expected to be
K-COST-marginal, and that is the point of pricing it before scoring.

### 3. Persistence

Structural: perp funding is a permanent design feature of crypto markets (BTC
perp funding since 2019, measured anchor 11.798%/yr average longs-pay,
24.7% of settlements negative in downtrends, worst −0.30%/8h); retail leverage
concentration is structural. Eroded by: funding cadence/rate compression,
liquidation-engine parameter changes, settlement-time market makers amortizing
inventory across prints (they must hold the funding/floor risk to do it — that
is exactly the rent being priced), or venue fragmentation dispersing the flow.

### 4. Risk transferred

The tail risk that the sweep is not exhaustion but the first leg of a cascade:
the long arm buys a market in forced-selling (falling knife), the short arm
sells a market in forced-buying (squeeze). The strategy absorbs the adverse
selection of trading against the strongest urgency flow; when the flush is a
breakdown instead of a flush, this book pays for the continuation trader
(P1-B's rent). This is the risk being paid for, stated before any PnL.

### 5. Observable (PIT, 1h klines; PROXY_NOT_ORDERBOOK)

- **Levels.** Swing low L: `low[j]` strictly below lows of bars j−6..j−1 and
  j+1..j+6 (N=6 each side; neighbors frozen at N ∈ {3,10}). Mirror for swing
  highs. **t_known = close of bar j+6** (first bar at which every input of the
  level has closed). Pivot confirmation lag = 6 closed bars ≥ 1-bar law floor.
  A level is *intact* if no bar since t_known has closed on the far side.
- **Settlement windows (new information layer).** Settlement times S_k from the
  venue schedule (00/08/16 UTC; per-pair actual `fundingTime` grid from the
  measured series for BTC/ETH). Window W_k = bars whose close-time falls in
  [S_k − 1h, S_k + 3h]. The mechanism reads only these TIMES, never rate
  magnitudes (fence 4 respected).
- **Sweep event (cross-bar, no intrabar ordering).** Bar s inside W_k with
  `low[s] < L` (long side; mirror for highs) while L intact. Sweep state opens.
- **Reclaim confirmation.** First bar c, s < c ≤ s+3, with `close[c] > L`.
  If instead some bar in (s, c] closes below L − 0.25×ATR24, the event expires
  as a breakdown (P1-B's event, not traded here). If no reclaim by s+3, event
  expires flat.
- **Decision/fill.** Decision at close of bar c; fill at open of c+1 at the
  opposite-quote convention (next-bar open, 1 adverse tick). No same-bar
  confirm-then-backward-fill; sweep and reclaim are distinct closed bars.
- **State variables.** ATR24 = mean true range of the last 24 CLOSED bars at
  decision time (trailing only — no same-day full-range percentile, no
  unclosed-bar stats). No vol state in the anchor; see field 10 for the frozen
  vol-arm contract.
- Label: every element above is geometric from klines — **PROXY_NOT_ORDERBOOK**.

### 6. Holding horizon & decision clock

Decision clock: 1h closed bars, UTC. Entry at open of c+1, c ≤ s+3 ≤ S_k+3.
Exits (first of): (i) opposite-side reclaim close (exit next open);
(ii) disaster stop — close beyond the sweep extreme by > 1.0×ATR24, exit next
open; (iii) **hard flat-by-settlement time exit**: no position may be open at
any S_{k+1}; the pre-registered exit is the open of the last bar whose close
precedes S_{k+1} − 2h. Worst-case hold ≤ 4 bars. Max one position per pair;
one frozen identity applied panel-wide (mass test ≠ mass selection).

### 7. Capacity

Event-driven, unlevered 1x, ≤ 3 entries/day/pair worst case. BTCUSDT 1h volume
is ~$0.5–1B/bar in the modern sample; edge halves when our participation at
the level is a material fraction of hour volume — order of magnitude ~$50M
notional per entry (≈5–10% of one hour's flow), far above any program-scale
deployment. SOL/BNB capacity an order lower but same structure. Not the
binding constraint; costs are.

### 8. Costs

Round trip, base book: fee 5 bps + 1 adverse tick per side (DECLARED,
venue-published tier floor + frozen convention) ⇒ 10 bps + 2 ticks. Tick
burden is price-level-dependent and must be computed per fill time
(tick/price): BTC ~0.02 bp/tick, ETH ~0.04 bp/tick, SOL ~1 bp/tick at ~$100
and up to ~50 bp/tick in the 2020 low-price floor — SOL/BNB early-sample tick
cost is material and disclosed, not smoothed. Funding: **zero in the base
book by construction** (flat-by-settlement fixture; verified per-path).
Stress book (×1.5 / ×2.0 bands): fee+tick stress, plus the DECLARED
miss-one-settlement gap-reopen band; plus the MEASURED funding path applied to
any fixture-violating hold, received/paid separated (BTC/ETH only — SOL/BNB
funding unstaged, stress arms on those pairs are BLOCKED, not imputed).
Spread census NOT_RUN: what is needed is the bookTicker/aggTrades
hour-of-fill spread distribution at the exact fill hours (00–03/07–11/15–19
UTC buckets) to upgrade the adverse-tick convention to measured fill cost and
to run the Q-8 validation of the 5 bps tier floor against actual fills. Until
then: `FILL_QUALITY_CLASS_declared`. Ceiling: expected gross median per event
must exceed the stress RT (~17 bps on BTC/ETH) measured on the anchor's own
fill distribution, else K-COST veto before scoring.

### 9. Falsifier

Killed if any of:
- **Settlement-shifted placebo**: identical geometry with windows shifted
  ±4h (04/12/20 UTC) earns ≥ 0.5× anchor expectancy (K-CTRL) — then the
  settlement layer carries no information, the payer is the dead fictional
  stop-hunter, and the identity closes `VETOED_FICTIONAL_COUNTERPARTY`. This
  is the payer test run through the proxy itself.
- **Placebo levels**: sweeps of matched-distance synthetic levels (same
  distance-from-price distribution, no pivot provenance) earn the same ⇒
  level location adds nothing ⇒ kill.
- **Inverted control** (trade WITH the sweep direction, same windows)
  out-earns the anchor ⇒ kill.
- **Delay-1**: anchor quoted one bar later (Q-4 run even though 1h) loses the
  edge ⇒ market-maker compensation ⇒ kill.
- **Concentration** (G8): top fold > 50% of positive PnL ⇒ K-CONC. Two-sided
  by construction; per-direction folds reported separately.
- **Ancestry**: |rho| > 0.20 vs frozen dead-family representations
  (band-fade-reclaim, Donchian-H4, rev24) on the frozen representation
  (P-12) ⇒ K-ANC.
- **Power**: < 100 RT per direction per the §DATACOST floor ⇒
  `NOT_RUN_THIN`, no relaxation (settlement restriction may simply leave too
  few events; that is a legitimate death).

### 10. Controls & baseline

- Causal control: settlement-shifted ±4h windows (clock-only placebo,
  non-vacuous per Q-11 — same 8h rhythm, decorrelated hours) + block-shuffle
  twin + GMT-hour dummies.
- Inverted control: sweep-direction continuation on identical event set.
- Baselines: cash 0%; long-hold BTC/ETH on the same cost book (declared fee +
  measured funding path, `FUNDING_PATH_STRESSED` label); trend reference
  (TREND_LF precedent); short-beta control reported for both arms.
- Vol-state incrementality: the anchor uses no vol state and is frozen in
  that form before outcome. A permitted neighbor arm (trailing-24h realized-vol
  tercile conditioning) may be frozen alongside, and it must pass the
  incrementality test — nested comparison vs (i) clock-only, (ii) trend
  baseline, (iii) spread-state, with the occupancy/expectancy-ranking metric
  frozen at trial freeze; fail ⇒ the vol arm is dropped, and the anchor must
  stand unchanged without it or the whole identity dies (K-VOL).

### Crypto additions

- **Funding treatment**: base book funding ≡ 0 (flat-by-settlement fixture,
  V1 force-flat precedent); stress book applies the measured per-settlement
  path with received/paid separated (Q-14) on BTC/ETH only; SOL/BNB stress
  arms BLOCKED pending funding staging (base arms remain scoreable — the
  mechanism is flat-by-settlement, satisfying the C1 gate).
- **Weekend/quiet-hour disclosure**: entries are confined to fixed UTC hours
  by the settlement clock, so the weekend/quiet-hour occupancy of entries and
  a weekend-vs-weekday expectancy split are disclosed per pair. If the edge
  lives only in weekend-thin hours, the payer story changes (MM withdrawal,
  not settlement flow) and the identity must be re-judged at F-0, not scored.
- **Two-sidedness**: symmetric long/short arms from one identity (fence 5
  satisfied by construction; no long-biased BTC book).
- **Pairs**: one identity, panel-wide: BTCUSDT + ETHUSDT primary (funding
  measured, dual-book check), SOLUSDT + BNBUSDT under the flat-by-settlement
  construction with per-fill-time declared tick cost; per-pair data gate
  applies (SOL floor 2020-09-14, BNB 2020-02-10, 2 disclosed SOL gaps).
  `SINGLE_VENUE_PANEL` label applies to every verdict.

**Pre-mortem (honest):** most likely death is F-0 (skeptic rules the revival
clause inapplicable to a band-fade-shaped skeleton) or the settlement-shifted
placebo reproducing the edge. Both are acceptable, pre-registered deaths.

---

## P1-B — "SETTLE-BREAK-CASCADE": settlement-adjacent acceptance-break continuation at pivot-confirmed levels (H2)

**Skeleton.** Same level set as P1-A. When a settlement-adjacent bar CLOSES
through an intact pivot-confirmed level by an acceptance buffer, take the
break direction at the next bar open. Hard flat before the next settlement.
Two-sided by symmetric construction.

**Ancestry position, stated openly.** Strip the settlement-adjacency layer and
the skeleton is Donchian-style continuation — dead on BTC (clock placebo
out-earned it). The revival claim is the same clause as P1-A: new payer
(carry-burdened forced deleveraging at the settlement print initiates the
break, stops behind the level then cascade — the INITIATING payer is the
deleverager, not the fictional stop-cluster) + new information layer
(settlement calendar). The claim is that continuation drift exists ONLY in
the settlement-adjacent subset; if it exists equally elsewhere, this is the
dead Donchian family re-priced ⇒ K-ANC. Pre-registered concession: if the
skeptic rules the revival inapplicable to continuation shapes, P1-B is
withdrawn without scoring.

### 1. Payer

Who pays: the accounts holding the losing side of the level after the
settlement-adjacent break. The initiating flow is funding-burdened leveraged
longs (or shorts) whose contractual settlement obligation plus mark-to-market
loss forces de-risking at a known timestamp; their forced exit pushes price
through the visible level, and everyone positioned against the break must then
pay to exit into cascading flow (stop-losses are mechanical, not the payer —
the payer is the carry-forced side whose exit need predates and causes the
break). Why they cannot arbitrage: the obligation is contractual and
timestamp-fixed; delaying exit means paying more carry into the same pressure.
The continuation side earns rent for supplying the other side of a
balance-sheet-forced repricing concentrated at settlement prints.

### 2. Premium

Order of magnitude: gross 15–50 bps per event over the ≤ 4-bar hold if the
post-settlement cascade claim is true (1h momentum drift after
acceptance-breaks in trending regimes is historically 10–40 bps; the claim is
that settlement adjacency concentrates it). Net of ~11 bps base RT (stress
~17 bps), the margin is thin and must be shown on the anchor's own fill
distribution before scoring — expected to be K-COST-marginal, by design.

### 3. Persistence

Same structural base as P1-A (perp funding design + retail leverage
concentration). Additional erosion channel specific to B: if settlement-time
flow becomes predictable enough, pre-settlement positioning absorbs the drift;
the 8h cadence caps how fast this can be fully arbitraged without taking
overnight-equivalent funding risk.

### 4. Risk transferred

The false-break tail: paying the P1-A side (absorption traders) when the
settlement-adjacent break reverts. B is short exactly the option A is long;
the two proposals cannot both carry positive expectancy on the same event
population, and their relative base rates (how often settlement-adjacent
sweeps reclaim vs accept) are themselves a reportable fact.

### 5. Observable (PIT, 1h klines; PROXY_NOT_ORDERBOOK)

Identical level machinery to P1-A (N=6 pivot confirmation each side,
t_known = close of j+6, intact-level definition, ATR24 trailing-closed).
Break event: bar b inside W_k (close-time in [S_k − 1h, S_k + 3h]) with
`close[b] > H + 0.25×ATR24` for an intact swing high H (long side) or
`close[b] < L − 0.25×ATR24` for an intact swing low L (short side). The
buffer is close-based ⇒ no intrabar ordering is ever assumed. Decision at
close of b; fill at open of b+1, opposite-quote convention, 1 adverse tick.
Neighbors frozen: buffer ∈ {0.15, 0.40}×ATR24. **PROXY_NOT_ORDERBOOK**.

### 6. Holding horizon & decision clock

1h closed bars UTC. Entry open of b+1 (b ≤ S_k+3). Exits (first of):
(i) opposite acceptance — close back through the level by the same buffer,
exit next open; (ii) disaster stop — close beyond entry-side extreme by
> 1.0×ATR24 beyond the level, exit next open; (iii) hard flat-by-settlement —
no position open at any S_{k+1}; exit open of the last bar closing before
S_{k+1} − 2h. Worst-case hold ≤ 4 bars. The truncation is deliberate and
disclosed: the claim is post-settlement drift, so the horizon bound and the
claim coincide. One position per pair; one frozen identity panel-wide.

### 7. Capacity

Same structure and order of magnitude as P1-A (~$50M per entry on BTCUSDT
1h; proportionally lower on SOL/BNB). Not binding.

### 8. Costs

Identical books to P1-A: base 10 bps + 2 ticks RT (declared, per-fill-time
tick/price computation — SOL early-sample tick burden disclosed); funding ≡ 0
base (flat-by-settlement), measured-path stress with received/paid separated
on BTC/ETH only; stress bands ×1.5/×2.0 plus DECLARED gap-reopen
miss-settlement band; spread census NOT_RUN — same needed artifacts
(bookTicker/aggTrades hour-of-fill spread distribution at the fixed entry
hour buckets; Q-8 tier-floor validation). `FILL_QUALITY_CLASS_declared` until
then. K-COST ceiling identical: gross median per event must clear stress RT
on the anchor's own fills.

### 9. Falsifier

Killed if any of:
- **Settlement-shifted placebo** (±4h windows, identical geometry) earns
  ≥ 0.5× anchor ⇒ the settlement layer is inert ⇒ B reduces to dead Donchian
  continuation ⇒ K-ANC + `VETOED_FICTIONAL_COUNTERPARTY`.
- **Placebo levels** (matched-distance synthetic levels) break-and-continue
  equally ⇒ level provenance adds nothing ⇒ kill.
- **Inverted control** (fade the same breaks — the P1-A side) out-earns the
  anchor on the same population ⇒ kill.
- **Delay-1** quoting loses the edge ⇒ kill (Q-4).
- **Concentration**: top fold > 50% positive PnL ⇒ K-CONC.
- **Ancestry**: |rho| > 0.20 vs frozen Donchian-H4 representation ⇒ K-ANC.
- **Power**: < 100 RT per direction ⇒ `NOT_RUN_THIN`.

### 10. Controls & baseline

Same battery as P1-A: shifted-window clock placebo + block-shuffle + GMT-hour
dummies; inverted control = fade of the same break events; baselines = cash
0%, long-hold same cost book (measured funding path), TREND_LF trend
reference, short-beta control reported. Vol-state: none in the frozen anchor;
identical incrementality contract as P1-A field 10 (vol-tercile arm optional,
must beat clock/trend/spread nested controls on the frozen metric or is
dropped; anchor stands without vol or the identity dies).

### Crypto additions

Identical treatment to P1-A: flat-by-settlement base book (funding ≡ 0),
measured-path stress BTC/ETH with received/paid separated, SOL/BNB stress
BLOCKED pending staging; weekend/quiet-hour occupancy and weekday/weekend
expectancy split disclosed; two-sided symmetric arms (fence 5); one identity
panel-wide on BTC/ETH/SOL/BNB under per-pair data gates; `SINGLE_VENUE_PANEL`.

**Pre-mortem (honest):** most likely death is F-0 (continuation skeleton =
dead Donchian family regardless of window) or the shifted placebo showing the
break drift was never settlement-specific. Pre-registered, acceptable deaths.

---

## Negative space (candidates considered and self-rejected, for the council's record)

1. Prior-day/week high-low band reactions — dead class #1 / calendar geometry.
2. Round-number nominal levels — dead class (K-ANC nominal-level).
3. Weekend thin-book sweep fade — band fade + session gate, explicitly fenced.
4. Funding-level-conditioned breaks (trade breaks only in high-carry regimes)
   — trivial rename of funding-level gating (fence 4; "adding an observable
   is not a new mechanism").
5. Cascade-exhaustion reversal at multi-week extremes — rev24 /
   mean-reversion family, dead at the rho 0.20 bar.
6. Generic settlement-timing drift without any price level — outside the
   owner-defined mechanism space (H1/H2/H3 are level mechanisms).

## Budget note

Two mechanisms × ≤ 6 arms (anchor + ≤2 neighbors + causal control + inverted
control + baselines/references) ≈ 12 cells ≤ the 18-cell cohort cap, leaving
headroom for at most one further council mechanism.

## Trial-freeze items requested at freeze (before any PnL)

Level algorithm + code digest (sha256); N, buffers, window offsets, exit
rules, fold contract (F1 2020-01→2021-04, F2 2021-05→2022-12, F3
2023-01→2024-12, F4 2025-01→end; SOL/BNB floor-adjusted F1 starts), seeds,
cost-book classes, placebo offsets (±4h), ancestry representation vectors,
vol-arm incrementality metric — all pinned before any scored run.
