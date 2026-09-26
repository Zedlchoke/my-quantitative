# COSTEXEC_cohort1_REPORT — COST/EXECUTION AUDITOR lane, ERP-TRACKB-PROGRAM-V1 cohort-1

Lane: trackb-cohort1-costexec (outcome-blind; BLOCKED power where evidence missing).
Start sha: e4e3b9159685b9da0bafeed6814f0a73c872cbcb (main). Date: 2026-09-26.
Authority read: PLAN_erp_trackb_program_v1.md §2/§5; umbrella §4.5/§5.4/§8; LESSONS Q-2, Q-8, P-21, P-27, P-2.
No orders, no trading endpoints, no API keys, no S1, no scored results viewed. Read-only except this file + HANDOFF.

## 1. Component inventory and evidence class

Primary book = measured only (umbrella §8); declared components live in a labeled declared book, never override it.

| # | Component | Class | Basis / validation step |
|---|---|---|---|
| 1 | Spot taker/maker fees (venue tier schedule) | DECLARED-required | No local venue fee doc in repo (Q-8: stated=hypothesis). Validate at data gate: sha-pin venue-published tier table; reconcile against anchor two-leg taker RT 20–25 bps (umbrella §4.5); then validate vs simulated fills. Maker unusable until queue measured (§5.5 law). |
| 2 | Perp taker/maker fees | DECLARED-required | Same path as #1, perp schedule separately pinned. |
| 3 | Spot spread at fill hour | MEASURED-path (census pending; BLOCKED-for-scoring until staged) | vision bookTicker/aggTrades per Track B §2; fill-hour conditional census §2 below. |
| 4 | Perp spread at fill hour | MEASURED-path (same) | fapi/vision kline+bookTicker census, same schema. |
| 5 | Slippage | MEASURED-path; else DECLARED + stress | replay-vs-fill where available; absent → declared band in declared book only, ×1.5/×2.0 mandatory. |
| 6 | Funding received/paid | MEASURED | settled series fapi `/fapi/v1/fundingRate` + vision cross-check, floor 2020-07-18 (CHR3F §2). Anchors measured in-registry: 11.798%/yr full-window (CYCLE_REGISTRY.json:1720, 7.824× frozen constant); in-DT 4.06%/yr = 1.11 bps/day; 24.7% of in-DT settlements negative; worst −0.30%/8h (umbrella §5.4d). PIT: settled-at-fundingTime only; next-interval rate = PREDICTED, never booked. |
| 7 | Hedge drift / tracking error | MEASURED-path | two synchronized bar series (spot vs perp), per-bar notional drift; census-grade sync proof required (F-2 clock alignment). |
| 8 | Perp margin (initial/maintenance tiers) | DECLARED model | venue-published brackets NOT locally verifiable — no tier numbers stated here (Q-8). Validation: pull USDⓈ-M BTCUSDT leverage/bracket table into data gate, sha-pin, record MMR% at chosen notional bracket; liquidation model label `LIQUIDATION_MODEL_DECLARED`. |
| 9 | Liquidation tape | BLOCKED | Track C precedent: liquidationSnapshot ZERO coverage / 404. Declared, never measured. |
| 10 | Outage / gap reopen | DECLARED band | miss-3-settlements (24h) + adverse reopen band, §5 below; ×2.0 stress applies. |
| 11 | Capacity vs top-of-book depth | BLOCKED for numbers; order-of-magnitude declared only | no depth evidence locally; any bps capacity number without depth census is forbidden. |
| 12 | Maker fills / queue position | BLOCKED for cost book | §5.5: forbidden until queue position measured. Taker book mandatory for cohort-1. |

Counts: MEASURED-path 5 (#3,#4,#5-if-replay,#6,#7) — DECLARED-required 4 (#1,#2,#8,#10; #5 fallback) — BLOCKED 3 (#9,#11,#12) + program-wide borrow/margin forms and second venue (Track B law (e), §2 table).

## 2. Census requirements (P-27/Q-2 law: conditional, never global p50)

- **Spread census schema (both legs):** key = (leg ∈ {spot,perp}, utc_hour 0–23, month). Persist per-key **counts per fixed bps bucket** (bins: 0–0.5, 0.5–1, 1–2, 2–4, 4–8, 8–16, 16–32, >32) + n + percentiles computed ONLY from persisted counts + flags: `LOW_SAMPLE_BUCKET` (n<30 → declared book + stress), `EXCLUDED_BUCKET` (n<10 → fill hour not scoreable, SLOT_LEFT_EMPTY). Executor charges the gated fill-hour bucket distribution at event time; global p50 is inadmissible anywhere.
- **Funding census:** raw settlement rows (fundingTime, rate) persisted; histograms by sign × regime tag; adverse path sets derived only from persisted series. Conditional magnitude of NEGATIVE settlements is a census deliverable — until staged it is a DECLARED band (worst-anchor −0.30%/8h is the only measured magnitude today).
- **Drift census:** per-bar |notional drift|/N distribution, same bucket persistence.
- **Stress application:** ×1.5/×2.0 applied **per component** to its measured conditional value (fees, gated-bucket spread p50/p75, slippage, funding magnitude); funding-path stress is a **scenario-path** stress (§3/§4), not a pure multiplier. P-2: report margin-to-fail for every gate pass.

## 3. The 100,000 USDT book (1:1 unlevered cash-and-carry)

One book, two legs, never doubled (Track B §5.1). Recommended sizing (frozen at child GO-1):

- **N = 65,000 USDT** spot notional (qty = N/P); perp short same qty 1:1; **M = 35,000 USDT** perp margin + buffer from the same book (35% of book; 53.8% of N). Entry fee (anchor, declared): one-way pair ≈ 10–12.5 bps of N ≈ 65–81 USDT.
- **Margin path (declared model):** adverse price move Δ debits margin by N·Δ; spot leg gain is NOT cross-collateral (declared simulation rule — no margin-transfer without trading). Failure boundary: Δ_liq ≈ (M/N) − MMR = 53.8% − MMR; with venue MMR bracket DECLARED (typ. 0.5–5% → Δ_liq ≈ 49–53%, number not stated as verified — validation step §1#8).
- **Recommended buffer law (concrete band):** re-margin trigger when margin < 20% of N (13k → Δ ≈ +33.8%): top up from residual cash or reduce N; force-exit band when margin < 12% of N (7.8k → Δ ≈ +41.8%): synchronized two-leg unwind at taker; Δ_liq ≈ 49–53% never reachable while bands are honored. Reasoning: at 1:1 the solvency risk is price-path into the short leg, and a +30–40% adverse rally must be survivable WITHOUT touching the exit band (declared stress), while 35% margin keeps idle drag at 0.35 of book and the band survives the measured worst funding tick (−30 bps) repeated many times over.
- **Funding-path stress scenarios** (on measured settlement distribution): (a) baseline in-DT: 24.7% of 8h settlements negative; (b) declared adverse: 50% negative at half the DT-mean magnitude; (c) worst-path runs at the measured worst anchor −0.30%/8h. Independence run-expectation over a 42-day hold (126 settlements) at p=0.247: E[≥3-run] ≈ 124×0.247³ ≈ **1.9 — a 3-negative-run is EXPECTED in every downtrend hold**; E[≥5-run] ≈ 0.11 — budget ONE 5-run at declared negative magnitude. Worst-path drawdown: 5×30 bps = 150 bps of N ≈ 975 USDT ≈ 1.0% of book — a PnL drag, **not** a solvency event at 1:1 with M=35k. Funding stress hits carry; price stress hits margin; they are accounted on separate ledgers and summed net.

## 4. F-5 breakeven / cost-ceiling law (preregistered, pre-PnL; P-21 mechanical)

**Ceiling definition (bps of N):** C*(H) = 2.0 × RT_measured_conditional + OutageBand_declared(H), where RT_measured_conditional is the fill-hour-conditional two-leg taker round trip from the §2 census at the actual gated hours (P-27), and OutageBand is the declared miss/reopen cost accrued over hold H.

**KILL_COST_CEILING inequality (fires pre-PnL, mechanically):**
a mechanism (frozen premium band × frozen hold band) is killed iff for **every** (entry premium p, hold H) pair in its frozen space:
`expected_carry(p, H) < C*(H)`  where expected_carry = measured/predicted funding+basis premium accrued over H on the perp notional, PIT-clean.
Equivalent rebalance law (XSECT successor, umbrella §4.5 C-XS-2): **rebalance/roll only when expected carry over the intended holding period ≥ full round-trip stress cost.**

**Anchor arithmetic restated (verified):**
- ×1.0: 20–25 bps RT ÷ 1.11 bps/day in-DT mean = **18.0–22.5 → 18–23 days** ✓ (anchor reproduces).
- ×1.5 (RT 30–37.5): **27.0–33.8 → 27–34 days** ✓ (anchor reproduces).
- ×2.0 (RT 40–50): **36.0–45.0 → 36–45 days** — my extension; the stress mandate (Track B §5.3) makes ×2.0 the operative F-5 ceiling.
- Full-window mean 11.798%/yr = 3.23 bps/day → 6–8 day breakeven: **inadmissible for gating** (P-27: only the gated-hours conditional counts); engineering context only.

**Corrections to the anchor text:** (i) worst −0.30%/8h ≈ "2.5 fee round-trips" uses a ~12 bps one-way entry-pair unit; in full two-leg RT units the worst settlement is **1.2–1.5 RTs** — same fact, conservative direction preserved. (ii) Utilization factor: at N=65k both carry and costs scale by N/100k, so day-breakeven is invariant, but ALL book-level PnL attribution must carry ×0.65 on N-level rates (mismatch = accounting error). (iii) Funding accrues on the perp leg only; spot leg has no yield. (iv) in-DT mean 1.11 bps/day reconciles to the measured 4.06%/yr in-DT figure — the anchors are internally consistent. (v) Anchor RT 20–25 bps is usable ONLY as the ×1 anchor after fee-schedule validation (§1#1); before that the DECLARED book carries the venue-published schedule, which may sit at/above the band top.

## 5. Hedge/execution law skeleton (frozen at child GO-1)

- **Synchronization:** both legs fill on the same bar at opposite quotes (spot buy at ask, perp sell at bid); exactly one crossing per side per leg per synchronized event. A one-legged fill is flagged `HEDGE_UNMATCHED` and must be matched or unwound by next bar close; unmatched-window drift is charged. No leg may be opened outside a synchronized pair event (no legging accumulation).
- **Rebalance bands (hedge drift):** candidates with reasoning — enter rebalance at |drift|/N > 1.0%, exit at 0.5% (hysteresis), force-band 5%. Reasoning: a stressed rebalance costs up to a full RT (40–50 bps) on rebalance notional; below ~1% drift the tracking-error PnL is smaller than that bill, so rebalancing there burns carry; the frozen band must pass F-5 with census-counted crossing frequencies (band choice is a frozen hypothesis, not tuned post-hoc).
- **Outage bands (declared):** miss ≤3 settlements (24h) → economics continue, premium accrual pauses, no action; miss >3 or venue gap → reopen at the stressed spread of the reopen hour bucket (census), gap-against-book declared band +25–50 bps (×2.0 → 50–100 bps) charged to the declared book. Adverse-assumption rule: reopen never at mid.
- **Comparison books (mandatory, same cost book):** (1) cash 0%; (2) long-BTC spot (entry+exit spot-leg RT only); (3) perp-only unlevered funding structure if scoreable. Q-14 gross/declared-net/measured-net split on every artifact with funding-received / funding-paid / fees / slippage / drift columns separate. Price-only disclosure clause binds (Track B (c)).

## 6. BLOCKED list — components that may NOT enter any number + single unblocking action

| Component | Unblocking action (single) |
|---|---|
| Liquidation tape | data-authority cycle staging a venue liquidation/forced-order archive with measured coverage (Track C precedent: current feeds zero-coverage). |
| Maker fills / queue position | measured queue-position census (fill replay vs top-of-book) proving fill quality; until then taker-only book. |
| Top-of-book depth / capacity bps | depth snapshot census at fill hours; until then order-of-magnitude declared only, no capacity number. |
| Fee tier numbers (spot+perp) | sha-pin venue-published fee schedule in the data gate + reconcile to fills (DECLARED→MEASURED). |
| Maintenance/initial margin brackets | sha-pin venue-published bracket table at chosen notional; record MMR% (DECLARED model → validated). |
| Borrow / spot-margin / levered forms | program-wide BLOCKED (Track B (e)); owner data-authority cycle only. |
| Second venue replication (OKX/Bybit) | BLOCKED-unauthorized; owner unblock of source + license. |

## Lane verdict (pre-PnL, cost/execution authority)

Honest all-in taker RT band the cohort is held to: **anchor 20–25 bps at ×1 only after fee validation; operative preregistered F-5 ceiling = ×2.0 stressed ≈ 40–50 bps + declared outage/reopen band ⇒ all-in stressed RT ≈ 45–60 bps** on N, ≈ 0.65× that on book at N=65k. At the anchors, the 100k unlevered book clears the ceiling **only for ≥6–8 week holds in positive-funding regimes; in-downtrend conditional carry sits at the ceiling — knife-edge (P-2), not a clear pass** — so KILL_COST_CEILING must be armed exactly as §4, and in-downtrend entries die unless the frozen entry premium band measurably exceeds the stressed bill. 3 components BLOCKED; funding series is the load-bearing measured anchor and is staged-able now.

Labels binding on every cohort-1 row: `SINGLE_VENUE_PANEL`, `PAPER_TIER`, `ANCESTRY_EXPOSED_DEV`, `FUNDING_PATH_STRESSED`, `LIQUIDATION_MODEL_DECLARED`, `FILL_QUALITY_CLASS_<measured|declared>`.
