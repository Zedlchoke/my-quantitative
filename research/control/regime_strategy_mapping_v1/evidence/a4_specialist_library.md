# A4 Specialist Library Proposal — REGIME-STRATEGY-MAPPING-V1

Lane: `a4-specialists` (A4, outcome-blind strategy architect)
Artifact: `freezes/specialist_library_proposal.json` (schema
`rsmv1_specialist_library_proposal@1`) — **PROPOSAL, ADVICE TO A1**. A1 freezes
the library and the mapping; nothing here is frozen by A4.
Status: outcome-blind. No evidence/, runtime/, V2-worktree,
`rsmv1/attribution.py`, `rsmv1/feasibility.py`, `rsmv1/arms.py`, or any
result-shaped file was read; no outcome fact was sought. Every design choice
below is derived from the regime's economic definition plus repo-standard
frozen conventions.

---

## 1. Design laws used

- **Bounds**: at most two specialists per regime; FLAT is always a valid
  choice and counts as a specialist. TRANSITION_UNKNOWN is code-owned
  abstention — FLAT is **fixed** there, never a selectable specialist.
- **No counter-trend** unless a separate forced-flow mechanism is stated.
  One specialist in this library (DIS-FAILED-HIGH-S) carries such a stated
  mechanism and is flagged below; everything else is regime-aligned.
- **No parameter grids**: one frozen parameter set per specialist, taken from
  repo/engine conventions wherever they exist (Turtle 20/10 Donchian windows,
  Wilder ATR14, 3.0x-ATR trend stops, EMA20/50 trend context, SMA20/BOLL-mid
  mean-revert targets, 96-exec-bar event horizon expressed as 24 regime bars).
- **Anti-churn**: no close/reopen when the target direction is unchanged;
  switches take effect only at flat or a direction change; every specialist
  declares its transition delay (all 0 regime bars — the regime machine's
  6-bar min-dwell is the confirmation gate).
- **Execution**: signals on completed exec-clock bars (BTCUSDT 15m; SPY D1),
  fill at the next exec bar open; one position per asset; notional fraction
  1.0; fold boundaries force flat with close costs charged.
- **Costs acknowledged everywhere**: BTCUSDT 12 bps round trip and funding at
  the frozen 1.377e-5 per 8h on signed notional (longs pay, shorts receive,
  ~0.41 bps/day); SPY 10 bps per fill, long-only authority.

Exit precedence declared library-wide: fold force-flat > price stop
(intrabar, overrides minimum holding) > maximum-holding time stop > rule
exits and regime-change exits (suppressed until the 6-regime-bar minimum
holding elapses).

## 2. The library (6 specialists; ≤2 per regime)

| Regime | Specialist | Dir | Assets | Mechanism in one line |
|---|---|---|---|---|
| ACCUMULATION | `ACC-BASE-RECLAIM-L` | LONG | BTCUSDT, SPY | Failed-low reclaim (spring): forced sellers exhausted, trapped probe-shorts must cover, mean-revert target at SMA20 |
| UPTREND | `UPT-DIPBUY-L` | LONG | BTCUSDT, SPY | Dip to EMA20 held inside EMA20>EMA50: resting trend demand absorbs profit-taking; trapped dip-shorts' covers stand behind |
| UPTREND | `UPT-BREAKOUT-L` | LONG | BTCUSDT, SPY | Close above trailing 20-bar high (Turtle): short-covering stops + momentum chase are mechanically triggered |
| DISTRIBUTION | `DIS-FAILED-HIGH-S` | SHORT | BTCUSDT only | Upthrust: probe above 20-bar high closes back below — trapped breakout buyers' stops are forced selling; cover at SMA20 |
| DOWNTREND | `DNT-CASCADE-S` | SHORT | BTCUSDT only | Close below trailing 20-bar low inside EMA20<EMA50: positioned with the auto-liquidation cascade, positive short carry |
| DOWNTREND | `DNT-RALLY-SOLD-S` | SHORT | BTCUSDT only | Rally to EMA20 rejected inside EMA20<EMA50: dormant-contingent holder supply activates at the rally and kills the bounce |

SPY is eligible only for the three LONG specialists. In DISTRIBUTION and
DOWNTREND, SPY's required mapping is FLAT (no short authority, and no long
mechanism exists in those regimes by definition). TRANSITION_UNKNOWN is
FLAT-fixed for both assets.

## 3. Per-specialist rationale (economics only)

### ACC-BASE-RECLAIM-L (ACCUMULATION, long, BTCUSDT+SPY)
Post-decline bases exist because price-insensitive forced selling
(liquidations, margin calls, capitulation stops) has finished; residual
sellers meet passive value demand. The regime definition's "downside
failures" is the observable witness: a bar that probes below the trailing
20-bar low and closes back above it proves the probe found no follow-through
supply. Traders who shorted the new low are trapped above water with rising
risk; their covering is forced buying. Entry requires the close still below
SMA20 so reversion room remains; the target is the mean itself (SMA20 — the
engine's existing BOLL-mid exit), the stop sits half an ATR below the spring
low because a re-break of that low factually kills the absorption thesis.
Time-capped at 24 regime bars: an absorption event that has not converted
within that horizon is not converting.
**Must lose when**: the "base" is a pause in an ongoing decline (probes keep
breaking for real), or in dead narrow ranges where the spring-to-mean span is
smaller than the round-trip cost.

### UPT-DIPBUY-L (UPTREND, long, BTCUSDT+SPY)
The regime definition itself names the mechanism: "higher highs/lows and
dip-buying". Trend-advance pullbacks are late-long profit-taking meeting a
temporary absence of new demand; EMA20 is where trend-aligned resting demand
(systematic re-levering, dip programs) sits. A dip that touches EMA20 and
closes back above was absorbed; shorts positioned against the trend have
risk covers above every such dip, and their covering is forced buying into
the resumption. The EMA20>EMA50 filter keeps the established advance's bid
behind the entry. Stop 3.0x ATR14 (repo TREND convention); rule exit on a
close below EMA20 (repo TREND_LONG exit); no intrinsic time cap — trend
economics hold until the regime machine or the fold says otherwise.
**Must lose when**: the advance is exhausted (dips stop being absorbed and
the fast mean breaks — the specialist buys each early-stage top), or in
choppy cells where UPTREND labeling persists over trendless advance.

### UPT-BREAKOUT-L (UPTREND, long, BTCUSDT+SPY)
The area just above a trailing 20-bar high is populated by contractual
flows: risk stops of counter-trend shorts (sell-to-cover, executed as market
buys through the level) and momentum/benchmark capital waiting to buy
strength. A close above the level mechanically converts both. The specialist
does not predict breakouts; it is the standing beneficiary of flows the level
itself triggers. Turtle 20/10 windows are the public, non-tuned landmark;
stop 3.0x ATR14. Acknowledged adverse-selection tax: entries cluster at the
worst prices in fakeout environments — that is this mechanism's declared
failure mode, not a hidden one.
**Must lose when**: breakouts above 20-bar highs routinely fail; the
specialist pays spread plus stop distance repeatedly.

### DIS-FAILED-HIGH-S (DISTRIBUTION, short, BTCUSDT only)
The one specialist carrying a counter-trend-shaped trigger, admitted under
the law's exception because the mechanism is a distinct forced-flow story:
after an advance the remaining buyers are late momentum chasers while early
holders sell into strength; an upthrust (probe above the trailing 20-bar
high closing back below it) proves the probe was supplied. Breakout buyers
entered on the new high are instantly trapped — their stops are forced sell
orders just below — and range traders who bought the failed breakout must
exit into the same book. Short entered before the mean is lost, covered at
SMA20; structural stop half an ATR above the upthrust high (a re-claim kills
the thesis); time-capped at 24 regime bars. Shorts receive the frozen
funding rate (~0.41 bps/day positive carry).
**SPY excluded**: the long-only authority forbids the short, and no long
mechanism exists in a supply-dominated top — SPY's conforming mapping is
FLAT. A1 may also choose FLAT for BTCUSDT (the predecessor baseline); this
specialist is the library's single new, optional element.
**Must lose when**: the top range resolves upward (it was
re-accumulation) — the short is run over by the true breakout; or in tall
choppy ranges where upthrusts close marginally above the mean target.

### DNT-CASCADE-S (DOWNTREND, short, BTCUSDT only)
The regime definition names the forced flow: liquidation cascades. Venue
auto-liquidation engines market-sell leveraged longs through successive
margin clusters; discretionary stop-losses are the same flow at smaller
size. Cascade sellers are price-insensitive — they must execute — while
dip-buyers are catching falling knives with exhausted capital. The close
below the trailing 20-bar low (with EMA20<EMA50 context) positions with the
liquidation engine, and the short side uniquely receives funding at the
frozen rate. The trigger is late by construction; that is the accepted cost
of only trading confirmed cascades. Turtle-mirrored 10-bar cover; stop
3.0x ATR14 above entry.
**Must lose when**: the cascade exhausts (open interest of stoppable longs
is finite) — the entry shorts the final liquidation leg before the first
base forms.

### DNT-RALLY-SOLD-S (DOWNTREND, short, BTCUSDT only)
"Rallies sold" is in the regime definition and has a concrete mechanism:
a standing population of holders has decided to exit and waits for a better
price — dormant-contingent supply that activates when a rally delivers
liquidity. Short-covering bounces deliver exactly that: price reaches EMA20,
waiting sellers execute into it, the bounce dies. The specialist is short at
the price where that known supply activates, with EMA20<EMA50 ensuring the
deeper cascade flow stands behind. It is the exact mirror of UPT-DIPBUY-L
with trapped longs instead of trapped shorts. Time-capped at 24 regime bars
(rejection events are short-horizon; without follow-through the decline is
ending).
**Must lose when**: the decline ends — rallies start holding above the fast
mean and become bases, and the specialist shorts the new uptrend's first
pullbacks until the regime exit fires.

## 4. Why the library is bounded at this size

- Each regime gets its economics expressed once, or twice only where two
  genuinely distinct forced flows exist (UPTREND: absorption at the mean vs.
  contractual breakout flow; DOWNTREND: cascade continuation vs. dormant
  supply at rallies). ACCUMULATION has one witness (the failed low) and
  DISTRIBUTION for BTCUSDT has one (the failed high); a second specialist in
  either would be a re-parameterization of the same flow, i.e., a grid.
- Per-regime count: 1 / 2 / 1 / 2 — all within the ≤2 bound; every specialist
  is single-direction, so "SPY never short" holds structurally, not by
  convention.
- The predecessor mapping is fully expressible from this library
  (ACC-BASE-RECLAIM-L / UPT-DIPBUY-L or UPT-BREAKOUT-L / FLAT /
  DNT-CASCADE-S / FLAT-fixed), so A1 can reproduce the conservative baseline
  without anything new; the only new element offered is DIS-FAILED-HIGH-S
  for BTCUSDT, explicitly optional.

## 5. Why no counter-trend specialist

Default-excluded by law. The two candidate counter-trend trades (buying
oversold in DOWNTREND, fading pops in UPTREND) fail the mechanism test: the
bounces/pops they trade are short-covering and profit-taking — flows that
the dominant forced flow (cascade, chase) consumes as fuel, not flows with
an independent economic engine. DIS-FAILED-HIGH-S is the single admission,
and only because its forced-flow story (trapped-breakout-buyer stop cascade
under dominant distribution supply) is separate and regime-aligned. Full
rejection list with reasons is in the proposal JSON
(`rejected_alternatives`, 8 entries).

## 6. Gaps and deliberate non-reads

- Deliberately not read: all `evidence/` and `runtime/` directories in any
  worktree; the V2 worktree; `rsmv1/attribution.py`; `rsmv1/feasibility.py`;
  `rsmv1/arms.py`; `rsmv1/engine.py`, `rsmv1/data.py`, decision caches
  (`data_local/*.jsonl`); any result, PnL, or winner/loser information. None
  was needed: the library is derivable from regime definitions plus engine
  conventions (`rsmv1/indicators.py`, `rsmv1/strategies.py`, freeze
  contracts), which is the entirety of what was consulted.
- Not verified by A4 (left to A1/implementer): that the exec-clock data
  arrays are long enough for SMA50/HH20 warmup at fold starts (warmup is 192
  regime bars in the fold contract, comfortably above every window used);
  exact funding settlement timestamps on the 15m grid (spec assumes the
  32-exec-bar cadence declared in `execution_law`).
- All parameters are convention-frozen (Turtle 20/10, Wilder ATR14,
  3.0x/0.5x ATR stop multipliers, EMA20/50, SMA20, 24-regime-bar event
  horizon). None was tuned to any data, and none could have been: no data
  was consulted.

## 7. Spec-level tests

`tests_py/test_specialist_specs.py` validates the proposal JSON structure:
schema identity, regime completeness, the ≤2-per-regime bound, UNK fixed
FLAT, required fields per specialist, direction consistency (id suffix =
direction; entry side = direction), eligibility law (SPY only in LONG
specialists; SHORT only in DISTRIBUTION/DOWNTREND; LONG only in
ACCUMULATION/UPTREND), minimum holding ≥ 6 regime bars, maximum holding
declared and consistent, transition delay declared, stop / max-hold / no-op
/ next-bar / costs acknowledgments present, unique ids, non-empty
`required_tests`, and non-empty `rejected_alternatives`. No engine, no data.
