# PROPOSAL P2 — SRLV-CX-C1 outcome-blind council, lane P2

- Lane: blind proposer P2 (independent of P1; no P1 artifacts read).
- Date: 2026-09-26. Worktree verified: `.worktrees/srlv-cx-c1/integration`, branch `orca/srlv-cx-c1-integration`, HEAD `d3f063a05338e498912a16d4678d4451fd0cb838`.
- Blindness: NO scored outcomes, NO PnL, NO winner info consulted. No MAP/LESSONS/HYPOTHESIS_LEDGER or any outcomes/ledger file read. No file under `research/control/SRLV-CX-C1/c3_council/` was read. Law context read: `plans/PLAN_srlv_cx_cohort_1.md`, `plans/PLAN_srlv_program_v1.md` only.
- Data reality assumed (measured, non-outcome): 1h klines BTC/ETH full 2020-01..2026-08 (0 gaps), SOL from 2020-09-14 (2 disclosed gaps), BNB from 2020-02-10 (0 gaps). Funding MEASURED for BTCUSDT (fapi) and ETHUSDT (Vision) only; SOL/BNB funding NOT staged ⇒ SOL/BNB mechanisms must be flat-by-settlement. No order book / liquidation tape / OI. Fee book DECLARED: 5 bps taker + 1 adverse tick per side; spread census NOT_RUN. All arms unlevered 1x.
- Terminal labels this proposal carries everywhere: `PROXY_NOT_ORDERBOOK`, `PAPER_TIER`, `SINGLE_VENUE_PANEL`, `ANCESTRY_EXPOSED_DEV` (dev rows), `FILL_QUALITY_CLASS_declared`, `FUNDING_PATH_STRESSED` (funding-exposed arms).
- Exposure reality acknowledged: all four pairs' 1h history 2020–2026-08 is outcome-exposed per cohort plan §2.2 ⇒ any history result is at most `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`; the expected OOS path is prospective accumulation after trial freeze (D13/D26/D52). Both proposals are written to be adjudicated and frozen BEFORE any scored run.

## Fence / law compliance map (both proposals)

| Law | Compliance |
|---|---|
| Fence 1 (BTC-state gates, ratio gates) | Neither proposal uses any BTC-price-state or ratio gate. |
| Fence 2 (BTC H4 Donchian trend continuation) | M2 differs by trigger (close-through of a completed-window extreme = event), horizon (≤4-bar time box), and hard close-based invalidation; discriminator pre-registered (stale-shelf + trend-gate-independence). M1 has no trend component at all. |
| Fence 3 (momentum/continuation FX; range-edge/band fade + ANY gate; oscillators; fix-window/clock/calendar geometry; cross-pair lead-lag; vol-as-direction; tape quantities) | No oscillators. No rolling statistical band. No calendar/session geometry (24/7; levels are completed-bar data geometry, and the only clock element — M2's flat-by-settlement entry window on SOL/BNB — is a cost constraint applied identically to all controls). No cross-pair lead-lag. Vol appears only as a state variable under the §2.4 contract with a pre-registered incrementality test; vol is never a direction input. M2's continuation direction is declared as the H2 in-space form with explicit ancestry deltas and pre-registered kills (see M2 field 10 + F-0 self-assessment). |
| Fence 4 (dvol_shock, rev24, close-displace-fade, funding-level gating) | Not used. M1's differentiator vs displaced-fade is the anchored `t_known` level + next-bar reclaim confirmation; the discriminating experiment (synthetic relabeled level must NOT reproduce) is pre-registered as a kill. No funding-level gating anywhere. |
| Fence 5 (fold concentration; two-sidedness) | Both mechanisms are two-sided (mirror short leg defined in the anchor itself); per-side and per-fold contributions reported; K-CONC ≤ 0.50 enforced; if any side/fold exceeds 0.50 the conclusion is prospectively defined only. |
| PIT §3 (levels, pivot lag, fills, intrabar) | All levels from completed bars only, with ≥1 closed-bar confirmation lag; every "sweep"/"reclaim"/"acceptance" is a CROSS-BAR close-based sequence — no within-bar high/low ordering is assumed anywhere; decision on a closed bar, fill at the next open with adverse-tick cost; no same-day percentile/regime statistics (absorption/vol statistics are trailing completed-bar windows only). |
| Delay law (Q-4 spirit) | Delay-1 arm pre-registered for both; ~zero residual edge at delay-1 ⇒ MM compensation ⇒ kill. |
| Funding gate | M1 runs on BTC/ETH only (funding MEASURED; holds may span a settlement, funding paid and accounted). M2 runs BTC/ETH funding-exposed plus SOL/BNB strictly flat-by-settlement (zero funding exposure by construction). |
| Fictional-counterparty law | Payer stories are encoded ONLY through PIT-legal geometric proxies, each with its own necessity falsifier (F-e). Liquidation-adjacent narrative is forbidden and is not used. |

---

# PROPOSAL P2-M1 — Prior-Day-Extreme Sweep-then-Reclaim Reversal (PDSR)

Family: H3 (sweep then absorption/reversal). Level family: H1's "prior-day high/low" as the swept object. Label: `PROXY_NOT_ORDERBOOK` on every sweep/absorption observable.

### 1. Payer (who MUST pay, why not arbitraged away)

The payer is the trader who transacted on the sweep bar's close-through of a level that was public, static, and known a full day in advance (the prior-UTC-day extreme). Two identifiable flows pay the reversion:

(a) Break-chasers who entered momentum orders as bar t closed beyond the prior-day extreme. When bar t+1 closes back inside the prior-day range, they are trapped on the wrong side with their protective stops resting beyond the very level they just broke; their exit flow is directional and price-urgent.

(b) Positional holders whose resting stop orders at the prior-day extreme were triggered during bar t; after the reclaim, the flow that pushed through the level is exhausted (it has transacted), and the marginal resting liquidity re-forms at the level from the original side.

Why not arbitraged away: taking the other side requires leaning into the sweep bar itself (adverse selection while stops fire) — an inventory cost market-makers refuse to hold across bars; and the pattern is event-limited and capacity-thin (order ~1–2 events/pair/month), below the size at which systematic capital competes the premium away. The strategy explicitly refuses to catch the extreme: it enters only after paying the sweep and confirming the reclaim, i.e., it lets the previous marginal buyer at the extreme be its counterparty.

Proxy honesty: (a) and (b) are NOT directly observable on klines. The proxy through which the payer must prove itself is the **absorption proxy**: the reclaim bar must be a range-expansion bar (its range > median range of the trailing 24 completed bars) AND close back inside the prior-day range. If the edge does not concentrate in expansion reclaims (test F-e below), the payer exists only in narrative ⇒ re-scope to pure geometry or `VETOED_FICTIONAL_COUNTERPARTY`.

### 2. Premium (expected bps/period, order-of-magnitude)

BTC 1h bar σ ≈ 0.5–0.8% of price; prior-day range median ≈ 2.5–3.5%. Distance from entry (near the swept level) to target (prior-day mid) ≈ 0.8–1.2%. With close-based exits, adverse excursions and the 6-bar time cap, a capture fraction of 25–35% of that distance gives a target **gross ≈ 20–40 bps/trade**. Event rate ≈ 1–2/pair/month ⇒ ~80–160 events/pair over 2020-01..2026-08 ⇒ gross ≈ 0.2–0.5%/yr on 1x notional per pair — thin by design; the claim is per-trade edge >> per-trade cost, not high annual return.

K-COST ceiling (pre-registered, measured numbers to be computed at freeze): round-trip DECLARED cost = 10 bps fees + 2 adverse ticks (≈0.05 bps on BTC, ≈0.5 bps on SOL-class ticks) + measured funding for ≤1 crossed settlement (median ~1 bp; stress tail −0.30%/8h = 30 bp ⇒ `FUNDING_PATH_STRESSED` dual book). Ceiling requires gross/trade ≥ ~22–25 bps to clear base book and ≥ ~30 bps to clear stress book. If measured median gross/trade on dev folds is below the ceiling ⇒ K-COST, fail-closed, no pretty numbers.

### 3. Persistence (structural reason + what erodes it)

Structural: protective-stop placement at the most recent completed daily extreme is taught behavior (platform defaults, courses, documentation) and reproduces continuously as each UTC day closes a new level in; the 00:00 UTC day boundary is a convention shared by the venue's own settlement clock, so the level is maximally visible.

Erosion: (i) universal awareness pulls the effect inside the sweep bar (sub-hour), where the delay-1 law kills it — the surviving residue should be the cross-bar structure only; (ii) competitors with maker fills compress the taker-book net edge; (iii) fee-tier changes move the ceiling, not the gross.

### 4. Risk transferred (named tail)

Named tail: **cascade-continuation day.** A sweep-reclaim that resumes — the reclaim bar is followed by a second close through the level in a genuine trend day. Loss = one full adverse bar (re-cross close-based stop executes at the next open; perp opens can gap vs prior close). Expected worst-decile per-trade loss ≈ 3–6× median win; no hard per-trade loss cap exists. Secondary tail: funding while held — a single stressed settlement (−0.30%/8h ≈ 3× RT fee) exceeds the median target edge; mitigated only by short hold (≤6 bars ⇒ ≤1 settlement typically), reported via dual book.

### 5. Observable (PIT-measurable on 1h klines + funding)

All observables are closes/high/low of COMPLETED 1h bars. `PROXY_NOT_ORDERBOOK` applies to "sweep", "reclaim", "absorption".

- Level (pinned once per UTC day): at the close of the last bar of UTC day d−1, `H = max(high)` and `L = min(low)` over the 24 completed bars of day d−1. `t_known` = 00:00 UTC of day d. Pivot confirmation lag = 1 closed bar (level exists only after the day's final bar closes; usable from the first bar of day d).
- Sweep event (upside): closed bar t in day d satisfies `close_t > H`. Downside mirror at `L`. Wicks never trigger; close-through only.
- Reclaim confirmation (closed bar t+1): `L ≤ close_{t+1} ≤ H` (back inside the prior-day range). If instead `close_{t+1} > H` (upside case), the event is an acceptance and is NOT traded by M1 (that case belongs to M2; keeps the two mechanisms disjoint on the same events).
- Absorption proxy (`PROXY_NOT_ORDERBOOK`): `range_{t+1} > median(range over bars t−23..t)` — trailing completed bars only; no same-day-as-decision statistic, no unclosed-bar input.
- Decision: close of bar t+1. Entry: open of bar t+2, market order, direction = against the sweep (short after upside sweep; long after downside sweep). One position per pair at a time; 1x unlevered.
- Exits (all close-based, executed at the next open; first rule hit wins; the swept day's level set is frozen at entry even if the UTC day rolls mid-trade):
  (i) invalidation: close back through the swept level (`close > H` for shorts / `close < L` for longs);
  (ii) target: close at/beyond prior-day mid `M = (H+L)/2` in the trade's favor;
  (iii) time stop: M1 = 6 bars after the entry bar (exit decision at close of entry+6th bar).
- Signal validity window: the trade must originate from a sweep of the CURRENT day's pinned level; stale levels from previous days are never traded (this is what separates M1 from displaced-fade and from M2's rolling shelf).
- Funding: settlement rate applied per 8h boundary actually held across (MEASURED series; PIT rule: a settlement is known only AT its `fundingTime`).

### 6. Holding horizon & decision clock

Decision clock: closed 1h bar boundaries (UTC); decisions only on closed bars, fills at next open. Holding: 2–8 bars typical (max 6 bars after entry) ⇒ 0–1 funding settlements crossed. Funding-exposed by design on BTC/ETH (funding MEASURED there); **no SOL/BNB arms** — M1's hold can span settlements and SOL/BNB funding is NOT staged ⇒ BLOCKED-pending-staging rather than silently assumed (funding gate honored). If the council wants pair replication on SOL/BNB, the only lawful form is a flat-by-settlement neighbour (entry hours restricted as in M2 with M1≤3) — offered as optional neighbour config, not part of the anchor.

### 7. Capacity

No book-depth data exists; estimate from turnover: entering ≤0.5–1% of the entry-hour taker turnover keeps impact inside the cost convention ⇒ per-event notional ≈ **$1–5M BTC, $0.3–2M ETH** (order-of-magnitude, flagged estimate). Edge-halving notional is where impact approaches the 5 bps fee ≈ that same band. Program-level capacity is event-limited: ~80–160 events/pair/year-band × per-event notional. `SINGLE_VENUE_PANEL` label applies.

### 8. Costs

- DECLARED book: 5 bps + 1 adverse tick per side ⇒ ~10 bps + 2 ticks round trip (2 ticks ≈ 0.05 bps BTC / ≈0.5 bps SOL-class). `FILL_QUALITY_CLASS_declared`.
- MEASURED: funding per settlement actually held (BTC fapi / ETH Vision series), accounted per-settlement, `FUNDING_PATH_STRESSED` dual book vs frozen constant anchor.
- NOT_RUN: spread/slippage census. Need: hourly fill-time spread census from bookTicker/aggTrades (coverage-verified) to (a) validate the 1-tick adverse convention at 1h-open fills, (b) adjudicate any weekend/quiet-hour-concentrated edge (worst-case fills). Until then, spread-conditioning of fills is DECLARED band ×1.5/×2.0 in stress, fail-closed if the census is required for a GO.
- Stress book: fees ×2 + 3 ticks + funding worst-settlement path.

### 9. Falsifier (what kills it; controls that must NOT reproduce it)

- F-a (causal clock placebo): block-shuffle twin — same entry/exit engine, sweep bars replaced by GMT-hour-matched, vol-tercile-matched shuffled bars, synthetic levels at the same distance-from-price percentile. If twin ≥ 0.5× anchor ⇒ K-CTRL kill. (24/7 law: block-shuffle/GMT-hour dummies, not session windows.)
- F-b (synthetic relabeled level / skeleton discriminator vs displaced-fade): identical rule with the level relabeled to day d−4 extremes (stale level, same geometry, same displacement statistics). If it reproduces ≥ 0.5× anchor, the edge is displacement-shape, not level-identity ⇒ same dead family ⇒ K-ANC/K-CTRL kill. This is the pre-registered answer to the F-0 skeleton test.
- F-c (inverted control): trade the same events in the acceptance direction (long after upside sweep+reclaim). If inverted out-earns the anchor ⇒ K-CTRL kill.
- F-d (delay-1): entry at open of t+3. If residual edge ≈ 0 ⇒ the information evaporates one bar late ⇒ MM compensation ⇒ kill; if <50% survives ⇒ margin-to-fail review.
- F-e (expansion necessity / payer-through-proxy): edge in the non-expansion-reclaim arm ≥ anchor ⇒ the absorption proxy carries no information ⇒ payer story untestable on this data ⇒ re-scope as pure-geometry hypothesis (and re-adjudicate) or `VETOED_FICTIONAL_COUNTERPARTY`.
- F-g (K-COST): measured median gross/trade below the §2 ceiling at base or stress ⇒ fail-closed kill.
- F-h (K-CONC + power): any fold (F1 2020-01→2021-04, F2 2021-05→2022-12, F3 2023-01→2024-12, F4 2025-01→end) or side contributing >50% of positive PnL ⇒ kill; per-pair RT count below the ≥100 floor ⇒ per-pair row `NOT_RUN_THIN`, pooled-panel row carries adjudication (pre-registered here so pooling is not post-hoc).

### 10. Controls & baseline

- Causal control: F-a block-shuffle clock twin (above). Inverted control: F-c. Baselines: cash 0%; long-hold BTC/ETH on the identical cost book (fees DECLARED + funding measured) — the 2020–2026 drift reference; trend reference (TREND_LF precedent) reported for context, not a scored arm. Mass-test law: ONE frozen identity applied to the full allowed panel (BTC+ETH), reported per pair, per fold, panel, leave-one-out.
- Vol-state incrementality design (only state use): realized vol state `R_t` = std of trailing 24 completed 1h log returns, walk-forward terciles (PIT). Nested comparison: anchor vs anchor+R-tercile vs anchor+GMT-hour-bucket (clock-only shadow, Q-11) vs anchor+trend decile vs anchor+range-state (spread NOT_RUN ⇒ range-state declared proxy). Admissibility: R adds information only if tercile monotonicity of event edge survives clock-matched and trend-matched resampling AND delay-1. If incrementality fails ⇒ drop the vol variable; the anchor must stand unconditional (both forms frozen before outcome per §2.4 master). Vol is never a direction input.

### Crypto additions (M1)

- Funding treatment separated: price PnL and funding PnL are separate reported columns per settlement (Q-14); dual book measured-path vs frozen constant, never merged.
- Weekend/quiet-hour buckets: trades bucketed UTC weekend/weekday × R-tercile, disclosed; an edge that exists only in thin weekend buckets is flagged unadjudicable pending spread census.
- Two-sidedness: mirror short leg defined in the anchor; per-side PnL and per-fold contributions reported; K-CONC ≤0.50 else conclusion prospective-only.
- Pairs: BTCUSDT + ETHUSDT only (funding MEASURED). SOL/BNB: excluded from anchor (funding NOT staged + hold may cross settlements); optional flat-by-settlement neighbour only.

### F-0 court self-assessment (M1)

- Skeleton test: strip the level ⇒ "fade a two-bar displacement" = dead displaced-fade shape; the proposal ACCEPTS this and pre-registers F-b as the empirical skeleton test — if relabeled levels earn equally, M1 dies. The claim under trial is level-identity, and it is falsifiable.
- Payer test: encoded through the expansion-reclaim proxy with F-e necessity; no liquidation narrative.
- Information test: the observable adds the identity of a completed-day extreme + two-bar close sequence, which is not a function of GMT hour, 168h trend state, or bar-range state; verified by the nested controls in field 10. Spread-state NOT_RUN — declared limitation.

Arm mapping (≤6 cells): anchor BTC; anchor ETH; neighbour-1 reclaim-window 2 bars (M1=6 kept); causal control F-a; inverted control F-c; baseline long-hold same book. (F-b, F-d, F-e run as kill-able diagnostics inside dry-run/dev, kill-only, not selection arms.)

---

# PROPOSAL P2-M2 — Weekly-Shelf Break-Acceptance Impulse (WSA)

Family: H2 (level breaks driven by stop clusters / forced flow). Label: `PROXY_NOT_ORDERBOOK` on "stop shelf", "forced flow", "acceptance". Liquidation-adjacent narrative is forbidden and not used; the payer is expressed only through a PIT-legal proxy with its own falsifier.

### 1. Payer (who MUST pay, why not arbitraged away)

Resting protective stops of positional holders accumulate just beyond the most recent completed 7-day extreme — the deepest level that is simultaneously (i) visible to everyone and (ii) old enough to have real position inventory behind it. When a 1h close trades through that shelf and the NEXT bar closes beyond it again (acceptance), the shelf's stop book has been consumed: the flow that had to transact to fill those stops is complete, and the marginal resting liquidity re-forms on the far side. The traders who pay the impulse premium are the late entrants who chase AFTER acceptance completes (over the following hours) at progressively worse prices, plus position-protectors who re-seat stops at the new extreme and feed the next leg.

Why not arbitraged away: harvesting it requires holding through acceptance — most shelf breaks fail (close back inside), so passive providers demand the failure premium; the event is episodic and size-limited (order ~1–2/pair/month); and market-makers will not carry directional inventory across the 2–4 bar impulse window at these event sizes. The strategy pays for its information by taking the failure risk of every accepted break.

Proxy honesty: the stop shelf is NOT observable. The proxy is: (shelf) rolling 168 completed 1h bars' extreme — structurally where positional protective orders rest; (forced flow) the acceptance bar must be a range-expansion bar (`range_{t+1} > median(range, bars t−23..t)`). If the edge does not require expansion acceptance bars (F-e), or if a STALE shelf (one week older, same geometry) earns equally (F-b), the stop-cluster payer exists only in narrative ⇒ re-scope to generic momentum (which is class-dead ⇒ VETO) or `VETOED_FICTIONAL_COUNTERPARTY`.

### 2. Premium (expected bps/period, order-of-magnitude)

σ_1h ≈ 0.5–0.8% ⇒ σ_4bars ≈ 1.0–1.6%. Conditional post-acceptance drift, order 0.1–0.25σ ⇒ target **gross ≈ 15–40 bps/trade** over a ≤4-bar hold. Event rate: 168h-extreme close-throughs ≈ 1–3/pair/month; acceptance subset ≈ 40–60% ⇒ ~10–25/pair/year (SOL/BNB higher volatility ⇒ more), ~70–160 per pair over the panel; the flat-by-settlement restriction on SOL/BNB retains ~9/24 admissible entry hours (≈38%) — disclosed as a power cost. Same K-COST ceiling discipline as M1: gross/trade must clear ~22–25 bps base / ~30 bps stress (SOL/BNB flat arms carry zero funding by construction, slightly easing their ceiling).

### 3. Persistence (structural reason + what erodes it)

Structural: protective-order placement beyond the running 7-day extreme regenerates every hour as the window rolls; the behavior is institutionalized in risk systems (stop placement relative to the deepest recent visible extreme). Erosion: anticipatory trading shifts fills before acceptance completes (sub-hour), which the delay-1 law and the acceptance confirmation make unharvestable by construction — the design deliberately harvests only the post-acceptance residue; maker-filled competitors erode the taker net; a regime where breaks stop following through (chop) erodes the gross — that is the mechanism's own regime risk, measured, not assumed away.

### 4. Risk transferred (named tail)

Named tail: **acceptance-is-the-top.** The acceptance bar itself marks the local extreme; price closes back inside the window range immediately after entry. Loss = one full adverse bar to the close-based invalidation exit at the next open (perp opens can gap vs prior close). Expected worst-decile loss ≈ 3–6× median win; no hard per-trade cap. Funding tail on BTC/ETH arms as in M1 (`FUNDING_PATH_STRESSED`); zero on SOL/BNB flat-by-settlement arms.

### 5. Observable (PIT-measurable on 1h klines + funding)

All inputs are COMPLETED 1h bars. `PROXY_NOT_ORDERBOOK` throughout.

- Shelf level (rolling, recomputed each closed bar): at close of bar t, `W_high(t) = max(high)` and `W_low(t) = min(low)` over completed bars t−168..t−1 (168h = 7 completed days). The window excludes bar t ⇒ pivot confirmation lag ≥ 1 closed bar by construction. `t_known` = close of each bar (continuous).
- Break event (upside): closed bar t with `close_t > W_high(t)`. Downside mirror at `W_low(t)`.
- Level pinning: the event bar's `W_high/W_low` values are FROZEN for the life of the trade (the window is not re-rolled mid-trade).
- Acceptance confirmation (closed bar t+1): `close_{t+1} > W_high` (upside; mirror downside). One acceptance bar only; if t+1 fails to close beyond, no trade.
- Forced-flow proxy (`PROXY_NOT_ORDERBOOK`): acceptance bar expansion `range_{t+1} > median(range over bars t−23..t)` (trailing completed bars only).
- Decision: close of bar t+1. Entry: open of bar t+2, market, direction WITH the break (long upside / short downside). One position per pair; 1x unlevered.
- Exits (close-based, executed next open; first hit wins): (i) invalidation: close back inside the frozen `[W_low, W_high]` range; (ii) time stop M2 = 4 bars after entry. No profit target — the time box IS the impulse harvest window (deliberately short so this cannot become Donchian-style drift holding).
- Funding: BTC/ETH arms pay measured funding per settlement held across (≤1 typical). SOL/BNB arms: **flat-by-settlement** — entries allowed only at opens in UTC hours {01,02,03,09,10,11,17,18,19}; with M2=4 the position always closes ≥1 bar before the next 00/08/16 UTC boundary ⇒ zero funding exposure by construction. The same admissible-hour mask is applied identically to every control arm (it is a cost constraint, not a signal).
- SOL disclosed gaps (2 bars): events whose entry/hold spans a gap bar are skipped, disclosed in the census row.

### 6. Holding horizon & decision clock

Closed 1h-bar decision clock; decision on closed bar t+1, fill open t+2. Holding ≤4 bars ⇒ BTC/ETH arms cross ≤1 settlement (funding measured, paid, reported separately); SOL/BNB arms flat-by-settlement (funding gate honored — these pairs are lawful precisely because they never hold across a boundary).

### 7. Capacity

Same estimation method as M1: per-event notional ≈ **$1–5M BTC, $0.3–2M ETH, $0.1–0.5M SOL/BNB** (≤0.5–1% of entry-hour turnover; order-of-magnitude, flagged; no depth data). Event-limited aggregate capacity ≈ (70–160 events/pair) × per-event notional over the panel. `SINGLE_VENUE_PANEL`.

### 8. Costs

Identical layered book to M1: DECLARED 5 bps + 1 tick/side (≈10 bps + 2 ticks RT; 2 ticks ≈0.5–0.7 bps on SOL/BNB — non-trivial there, disclosed); MEASURED funding on BTC/ETH arms per-settlement, dual book; NOT_RUN spread census — needs identical to M1, with the SOL/BNB flat arms additionally needing the census to validate the wider-tick convention; stress = fees ×2 + 3 ticks + worst funding path (BTC/ETH) / fees ×2 + 3 ticks (SOL/BNB flat, no funding term).

### 9. Falsifier (what kills it; controls that must NOT reproduce it)

- F-a (clock block-shuffle placebo, vol/hour-matched as M1): twin ≥0.5× anchor ⇒ K-CTRL kill. This directly re-tests the PSV1-Donchian death mode (clock placebo out-earning).
- F-b (stale-shelf discriminator vs Donchian/momentum rename): identical rule on the shelf one week older (`W` over t−336..t−169, same entry/exit engine, same admissible hours). Stop-shelf logic says stale shelves have no resting stops ⇒ stale arm must NOT earn ≥0.5× anchor; if it does, the edge is generic continuation ⇒ class-dead ⇒ K-ANC kill.
- F-c (trend-gate independence): the anchor must earn WITHOUT any trend or vol gate. If the edge appears only when a trend/vol condition is added ⇒ it is the dead Donchian/continuation class wearing an observable ⇒ VETO.
- F-d (delay-1): entry at open t+3; ≈zero residual ⇒ MM compensation ⇒ kill.
- F-e (expansion necessity): non-expansion acceptance arm ≥ anchor ⇒ forced-flow proxy uninformative ⇒ payer fiction ⇒ re-scope/VETO.
- F-g (K-COST) and F-h (K-CONC ≤0.50 folds/sides; ≥100 RT floor per pair else `NOT_RUN_THIN` per pair, pooled-panel adjudication pre-registered) — as M1.
- Inverted control: the fade of the same accepted break (M1-family direction on these events) must NOT out-earn the anchor (K-CTRL inverted).

### 10. Controls & baseline

Causal control: F-a block-shuffle twin. Inverted control: F-c' fade-on-same-events. Neighbour controls: F-b stale shelf; SOL/BNB flat-by-settlement panel. Baselines: cash 0%; long-hold same cost book; trend reference reported. Vol-state incrementality: identical nested design to M1 field 10 (clock-only shadow Q-11 non-vacuous; drop-vol-not-identity rule; both anchor forms frozen pre-outcome). Mass-test law: one frozen identity, full panel, per-pair/per-fold/leave-one-out reporting.

### Crypto additions (M2)

- Funding treatment separated: identical to M1 (per-settlement columns, Q-14, dual book); SOL/BNB arms carry a structural-zero funding line by construction (force-flat fixture, disclosed).
- Weekend/quiet-hour buckets: disclosed as M1; additionally the SOL/BNB admissible-hour mask's interaction with GMT-hour buckets is disclosed (the mask over-samples hours 01–03/09–11/17–19 — the clock twin controls carry the identical mask).
- Two-sidedness: mirror legs in anchor; K-CONC ≤0.50 per side/fold; else prospective-only conclusion.
- Pairs: BTCUSDT + ETHUSDT funding-exposed; SOLUSDT + BNBUSDT flat-by-settlement secondary arms (funding gate: lawful because flat-by-settlement).

### F-0 court self-assessment (M2)

- Skeleton test: strip the shelf ⇒ "buy a close beyond a rolling max" = dead Donchian/continuation skeleton. Accepted; F-b (stale shelf) and F-c (gate independence) are the pre-registered empirical skeleton discriminators. The claim under trial is shelf-specific forced flow, falsifiable on this data.
- Payer test: expressed through the expansion-acceptance proxy (F-e) and the shelf-freshness contrast (F-b); no liquidation narrative.
- Information test: shelf freshness + acceptance + expansion is not recoverable from GMT hour, trend state, or range state; verified by the nested controls. Spread-state NOT_RUN — declared limitation.

Arm mapping (≤6 cells): anchor BTC; anchor ETH; neighbour-1 SOL+BNB flat-by-settlement panel; neighbour-2 stale shelf; causal control block-shuffle twin; inverted control fade-same-events; baseline long-hold same book.

---

## Cross-proposal notes for the council

- Disjointness: on a given level-event, M1 trades the reclaim (reversal) and M2 trades acceptance (continuation); the two never take the same side of the same event on the same level, and M1's levels are calendar-day extremes while M2's is a rolling 168h extreme — the inverted control of each is close to the other's direction, which makes the pair of proposals a joint discriminating experiment on H2 vs H3 at known levels.
- Both proposals expect to sit CLOSE to the K-COST ceiling under the 5 bps/side taker book. That is stated, not hidden: if the measured funding paths and the declared stress book push the ceiling above the achievable gross, the correct outcome is K-COST / REJECT_ALL — a valid terminal.
- Per-pair power is at risk (≥100 RT floor) for both mechanisms on BTC alone; pooled-panel adjudication is pre-registered above, before any outcome, so it cannot be treated as selection later.
- Freeze requirements (both): level algorithm + sha256 code digest; `t_known`; pivot lags; exit engine; admissible-hour mask (M2 SOL/BNB); fold contract F1–F4; both anchor forms (with and without vol-state); three lookahead classes (truncation replay byte-identical, future-mutation invariance, independent implementation); dry-run exact-arm non-vacuous + leak-scan before any scored run.

**Format self-check:** each proposal carries all 10 mandatory fields (1 Payer, 2 Premium, 3 Persistence, 4 Risk transferred, 5 Observable with level definition/t_known/pivot lag/PROXY label, 6 Holding horizon & decision clock, 7 Capacity, 8 Costs incl. NOT_RUN needs, 9 Falsifier, 10 Controls & baseline incl. vol incrementality design) plus the crypto additions (funding separated, weekend/quiet buckets, two-sidedness, pairs & funding gate). PASS.
