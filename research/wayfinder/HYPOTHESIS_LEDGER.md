# Hypothesis ledger — cumulative research memory

> Compiled 2026-09-04 by the Lead Engineer (Adam Hoàng) from primary control
> artifacts, `NOTES.md`, hypothesis dirs and terminal reports across all
> worktrees. Purpose: one authoritative index of every mechanism this factory
> has ever researched, why each failed (or is pending), and what is now
> forbidden. This file indexes evidence; the frozen artifacts in each run's
> control directory remain the authority. When a cycle closes, append its
> families here.

## Ground rules for reading this ledger

- A family listed here as REJECTED/BLOCKED is **ancestry-vetoed**: re-testing
  it, or any parameter/top-K/universe/relaxed-gate variant of it, is rescue
  and ineligible without a new owner plan preregistering a materially new
  mechanism (measured decorrelation vs the rejected ancestor, not prose).
- Cumulative scored denominators (post-V3R adjudication, 2026-09-05): crypto
  137 published / 140 observed logical; stocks 21/21; forex 18/18. S1
  untouched everywhere. **Program total: 176 published cells, 0 survivors.**
  The first Stage-A survivor (FXFV3-A6-P1) was invalidated by its own
  remediation cycle — see the Free-V3 row and `LESSONS.md` P-1..P-6.
- **No strategy has ever been promoted.** Every governed scored cycle closed
  REJECT_ALL / CANDIDATE_FAIL / BLOCKED. The near-misses below are the most
  information-dense rows in this ledger.

---

## A. CRYPTO — Binance USD-M perpetuals (governed V-series)

| Cycle | Family / hypothesis | Mechanism (short) | Outcome & decisive failure |
|---|---|---|---|
| V6 | CARRY-1D/3D/7D + REVERSE-3D ctrl | Funding-rate carry, 1/3/7-day | CANDIDATE_FAIL. 1D PF 0.978; 3D PF 1.0116 edge_too_weak; 7D PF 1.157 **but fold-positive-share 51.66% > 50%** → reject. Control failed as designed (valid falsifier). |
| V7 | XSECT-FUND-PRICE-DIV-1D/3D/7D + REV-3D | Funding/price divergence | NEVER RUN — preregistered 4 trials, V7P repair not completed; superseded by V8/V9. |
| V8/V8R | H-XSECT-REVERSAL-v2 (15-trial preflight) | Cross-sectional reversal | V8_REJECT_ALL (after V8 prep context-loss restart; no scored V8 artifact, V8R executed and rejected). |
| V9 | XSECT-TSTREND-L14/L28/CTRL | Time-series momentum, 10-altcoin universe, weekly clock, dead-zone long/short | V9_REJECT_ALL_MULTI_FAMILY 5/5 — all NOT_ELIGIBLE. Denominator reached 117. |
| V9 | XSECT-VOLSHK-S15/CTRL | Dollar-volume shock continuation (top-6 by 20d shock ratio; long 2 best / short 2 worst 3d return) | NOT_ELIGIBLE — same terminal. |
| V10/V10R | M01-AGGRESSOR-ABSORPTION-PANEL | Aggressor-side order-flow absorption (first generic-adapter cycle) | BLOCKED_PRELAUNCH (G05: staged bars end 21.5h short, synthesized tail) → V10R remediation → M01_FAMILY_REJECT (anchor+C2 published 2/9; neighbour publisher contract gap; repro 3/3 ALL_MATCH). |
| V11 | LOT — residual-MAX 7d, weekly | Max residual load vs benchmark | REJECT — **anchor lost (PF 0.72, MDD 79%) while sign-inverted control WON (PF 1.34)**: preregistered falsification condition triggered. |
| V11 | ILLIQ-AMIHUD — 28d formation, weekly | Amihud illiquidity premium | REJECT — **the closest any family has come: 12/13 gates, positive expectancy, PF 1.355, 3/3 folds positive, MDD 9.2%, stress-surviving**; failed the single frozen concentration gate at exactly 0.7055. V12 replication attempt → BLOCKED_DATA (window unavailable; 3 slots unused). |
| V11 | OILEV — OI-leverage weekly quintiles | Open-interest deleveraging | BLOCKED pre-score — weekly quintile books on 9-name DV universe produce 0.5–1.0 leg weights, incompatible with frozen 0.30 adapter cap. |
| V12 (CLOSED 2026-09-04, V12_REJECT_ALL, A7 terminal APPROVED 0 FAIL) | OILEV-V2 (28D-FLOW anchor / 56D-STOCK neighbour / INV control) | PIT OI flow/stock deleveraging-crowding | REJECT — **anchor −0.821 (PF 0.717, MDD 82%) and neighbour −0.845; sign-inverted control +0.758 (PF 1.360, MDD 17%, 2/3 folds, stress-positive): the frozen mechanism's sign is wrong on this window** (same falsification mode as V11 LOT). Attempt-1 crashed pre-metric → TECHABORT zero-budget, driver-only fix W12R2=ce52e3e. |
| V12 | BAB-LOWBETA (90d-beta anchor / DOWNCORR neighbour / INV control) | Frazzini–Pedersen betting-against-beta on perps | REJECT — anchor −0.0199 (**PF 0.992: dead after taker costs + funding**), neighbour −0.087, inverted control +0.0013 outperforms anchor. 6/6 cells published + reproduced ALL_MATCH; denominators 131/134. |
| V12 | ILLIQ replication | See V11 row | BLOCKED_DATA — 3 slots unused, not reassigned. |
| V12 (not selected) | A5-P2 MIX-ORDERSIZE; A6-RVX; A6-OSCOMP | Order-size mix; realized-vol EG/ADF pairs; overnight compression | P2/RVX eligible-but-loses-rubric; **OSCOMP INELIGIBLE: anchor rank = sign-inverted reserved ILLIQ rank (ρ 0.81–0.87) — a relabelled ancestor.** |
| V13 (CLOSED 2026-09-05, V13_REJECT_ALL, A7 terminal APPROVED 0 FAIL) | A13-V13-A8-OITD | OI term-structure days (28D anchor / 56D neighbour / sign-inv control) | REJECT — anchor −0.285 net (PF 0.879, MDD 30.5%), funding −0.007; mechanical reject; control worse than anchor so no falsification shadow. |
| V13 | A13-V13-A5-LIQEPIS | Liquidity-episode conditioning | REJECT — **price-only PnL already negative (−0.31)** so verdict-invariant, BUT terminal recorded a cost anomaly: cost_charged 25.03 over 600 positions ≈ 3–4 orders above the frozen per-fill schedule (suspected per-stamp accrual = cost-once violation). Mandatory fix before any future cost-sensitive cycle. Denominators 137/140; Data Fusion core adopted byte-identical — the PIT framework is now proven live in a scored cycle. |

## B. CRYPTO — pre-factory sprints (NOTES.md, 2026-08-21→24, semi-governed)

| Strategy / hypothesis | Outcome |
|---|---|
| `ema_atr` trend (default) | Baseline only; never promoted. Lesson: high win rate ≠ profit (§4.1). |
| `mean_reversion` (Bollinger+RSI, VHF/ADX/volume range filter) | ETH "validated" for demo (quick grid + OOS + directional WF) — **but frozen-rule transfer to 6 altcoins FAILED (13.3) and shared-capital portfolio FAILED (13.4)**. Remains demo/signal-only. |
| `regime_switch` (trend in trends, MR in ranges) | Not automatically better than legs (§4.3). |
| Wyckoff regime research + markdown-breakdown short | Regime facts recorded; best cell markdown_breakdown ADAUSDT exp +0.078 / PF 1.36 / 139 trades but fold_concentration FAIL. |
| H-VOLCOMP-BRKOUT-v1 (vol-compression breakout, markup-only) | REJECTED — 26/28 cells negative; 2 positive cells single-fold artifacts. |
| 24h sprint matrix (77 cells, then corrected 98/98) | **0 PASS Stage A.** No survivor → no portfolio/Tier 2. Most common FAIL: fold_concentration_high. |
| H-FUNDCROWD-MR-v2 (funding-crowding MR, PIT funding percentile) | REJECTED — 18/21 negative; 3 ETH combos positive (PF 1.34–1.40) but 68–81% concentration = single-fold + single-symbol artifact, per pre-locked falsification. |
| H-XSECT-MOM-v1 (cross-sectional momentum 3 lookbacks + reverse ctrl) | REJECTED — **MOM-7D +9.7k vs control −27.2k with beta-neutral achieved: a real signal**, but gross drift to 1.275 > 1.0 and MDD 24–37% broke risk gates. |
| H-XSECT-REVERSAL-v1, H-XSECT-REVERSAL-BREADTH-{CRYPTO,EQUITY}-v1, H-XSECT-FUNDING-CARRY-v1, H-XSECT-FUNDING-PRICE-DIVERGENCE-v1 | Proposal/analysis dirs; folded into the governed V-series above or superseded. |

## C. STOCKS — US sector-ETF cohort (12 ETF, SPY+sector-EW TR benchmark, daily)

| Cycle | Family | Mechanism (short) | Outcome & decisive failure |
|---|---|---|---|
| Stocks-free-V1 (z1/z2) | — | Cohort census + data authority build | No scored cells (0/6). Foundation cycle. |
| V2 | A4_XSEC_ETF_RELATIVE_MOMENTUM | 12-1 month cross-sectional relative momentum, top-3 sector ETFs | REJECT on **two independent grounds**: max-fold MDD 30.36% > 15%, and **causal control reproduced the mechanism — bottom-3 ranking earned 96.5% of anchor expectancy (long sector beta dominates; ranking carries no incremental information)**. All momentum variants (top-K, ETF subsets, relaxed MDD, post-hoc SPY hedge) = rescue. |
| V2 | A5-SFV2-TREND-DEFENSIVE | TSM12 + vol-target, SMA200-weekly defensive rotation | INCOMPLETE_NOT_PROMOTABLE — MDD 23.22% > 15%, fold-positive-share 60.7% > 50%, ETF-share attribution UNAVAILABLE_FAIL_CLOSED (CASH double-count bug, later fixed). |
| V3 | SFV3-A5-IDIO-SHOCK-REVERSAL | Idiosyncratic shock reversal | REJECT — anchor expectancy −0.00296 ≤ 0. |
| V3 | SFV3-A6-TOM-SETTLE | Turn-of-month settlement | REJECT — failed preregistered hard gates (turnover convention adjudicated post-scoring; no verdict changed). |
| V4 (TERMINAL 2026-09-04, REJECT_ALL 6/6 published, repro 6/6 EXACT_MATCH; A7T pending) | SFV4-A5-H1 PARTICIPATION-SHIFT | Gervais-2001/Lo-Wang 21d-vs-252d dollar-volume shock ratio; quarterly long top-3 / short bottom-3; stale-rank negative control | REJECT — **anchor −17.62% (PF 0.606, 1/3 folds, MDD 18.5%, incremental alpha −0.791 all folds); stale-rank control earned +14.91% raw PnL (PF 1.668) but its own alpha is −0.470 and concentration fails: the return belongs to the sector-exposure form, not the fresh-vs-stale mechanism**. |
| V4 | SFV4-A4-H1 SEMIVARIANCE-SHARE | Downside/total-variance shape, market-neutral, kappa fallback ex ante | REJECT — **anchor −28.08% (0/3 folds, MDD 32.1%); vol-LEVEL control earned +53.14% (PF 2.582) but MDD 34.1% + concentration fail: the shape axis was negative-information, all signal sits in plain vol-level sorting** (third appearance of the vol-level shadow effect; not Stage-A eligible, not rescuable). |
| V4 (not selected) | A4-H2 vol-of-vol; A5-H2 abnormal-volume; A6-H1 Garman-Klass; A6-H2 overnight-share | — | All blocked by **measured** control self-subsuming / rank-identity with own control (ρ 0.78–0.83) — the exact V2/V3 failure mode, now caught pre-selection. |
| V5 (CLOSED 2026-09-05, REJECT_ALL **A7T CONFIRMED** — 3/6 cells; only 1 of 6 proposals selectable) | SFV5-A6-H2 CROSS-SECTOR-COUPLING | Cross-sector coupling conditioning | REJECT — anchor PnL −1.35%, PF 1.054, 1/3 folds, MDD 18.1% > 15%, stress −4.2%, drop-one dead; **nominal-price placebo outperformed the anchor on the identifying metric (alpha 0.0252 vs 0.0077, ratio 3.27)** — falsification fires (7th instance of the cluster). Repro 3/3 EXACT_MATCH. 3 slots unused forever. |
| V5 (selection outcome — carry-forward data lesson) | 4 SEC-conditioned proposals | PIT fundamentals conditioning | **ALL INFEASIBLE: SEC single-vintage coverage collapse** (F1) — the V5 core bet was unfundable with staged data; SEC lane needs data-authority rebuild before any fundamentals-conditioned stocks cycle. A5-H2 vol-level confirmatory INELIGIBLE by measured front-door gate (ρ 0.319 > 0.20 — Section 1.1 worked as designed). Denominator stocks 21. |
| V6 (CLOSED 2026-09-05, `STOCKS_FREE_V6_BLOCKED_DATA_AUTHORITY` — plan-sanctioned legitimate close; zero cells scored, denominator unchanged 21/21, budget 0/6) | P0a F1 REMEDIATION — **PASS, durable asset** | Multi-vintage PIT fundamentals | V5's coverage collapse reproduced to the digit; mechanism isolated to the bridge's single-vintage semantics; rebuilt panel reaches `us-gaap:Assets` coverage 0.946/0.985/0.998 at S0 start/mid/end (p50 availability lag 121d); **154 fundable conditioning clocks frozen** (`p0a_clock_freeze.json`) — the stocks fundamentals frontier is unlocked for any future cycle. |
| V6 | P0b single-name price leg | Stooq / Massive Basic | **FAIL-CLOSED with evidence**: Stooq `UNAVAILABLE_FAIL_CLOSED` (JS proof-of-work gate blocks scripted access AND the rendering channel demonstrably corrupts OHLC — L7 cross-check caught it); Massive Basic `CANDIDATE_NOT_AUTHORIZED` (signup + key + non-commercial terms, nothing signed). **Owner decision 2026-09-05: ACCEPT_CLOSE (option C) via Lead Engineer; option B STANDING — any owner-entitled price source re-opens the stocks program as V7 inheriting the frozen panel + 154 clocks (V6 event log 9fafdf2).** **Lead ruling: the V6 standing GO is EXTINGUISHED UNCONSUMED at V6's terminal close — it does NOT carry to any next cycle; V7+ requires its own owner GO at its own prelaunch (handbook §2.5, agent inference is not owner authority).** |
| V7 (CLOSED 2026-09-05, `STOCKS_FREE_V7_BLOCKED_DATA_AUTHORITY` — fast honest probe close; zero cells, budget 0/6, denominator unchanged) | P0b-2 price probe: Twelve Data Basic under the existing entitlement | Single-name US daily prices | **FAIL at gate 3 (delisted coverage, the make-or-break)**: TWTR/SIVB(+SIVBQ)/TWX unservable by ticker AND alias AND search (never-existed control symbol reproduces identical 404 semantics); FRC only via OTC alias FRCB. **Gates 1/2/4/5/6 PASS with measured baselines**: ~20y depth ×8 names; CMG 50:1 + TJX 2:1 splits reconcile with SEC-recorded ratios; KO adjusted-vs-raw +6.24% vs SEC-dividend-implied +6.00%; 0 OHLC violations in 40k bars; Friday-bar-Saturday-present availability. Owner options recorded: provide a delisted-inclusive source (same gate suite) / authorize a Twelve Data plan upgrade (probe-first) / accept close. Assets keep: frozen panel + 154 clocks + probe evidence. |
| V8 (probe-terminal 2026-09-05, `STOCKS_FREE_V8_BLOCKED_DATA_AUTHORITY` — activation attempt on an owner-provided FREE source; cycle never bootstrapped, zero cells, budget 0/6, denominators unchanged 21/21) | P0 probe: Stooq bulk `d_us_txt.zip` hand-downloaded by the owner (sha256 `0a75aee8...`; `research/control/stocks_free_v8_probe/probe_verdict.json`) | Single-name US daily prices (free channel) | **FAIL at gate 3 (delisted), terminal by design**: bundle = 13,354 files of the currently-listed universe — living canaries 6/6 deep (KO 1970→, GE 1962→, through 2026-09-04) but **0/14 SEC-corroborated dead names** (TWTR/SIVB/SIVBQ/TWX/FRC/FRCB/BSC/LEHMQ/ENE/SHLDQ/JCP/BBBY...), absent with IDENTICAL semantics to never-existed controls (3/3) = survivorship-biased; all 662 pre-Sep-2026 terminations are ≤3 months old (SPAC units/warrants). Gate 2 PASS measured. **Canary method's second confirmed kill.** Remaining free avenue recorded: Stooq per-symbol endpoint ≠ bulk bundle (never measured for delisted) — owner 30-second browser test on twtr/sivb URLs decides whether the owner-authorized browser-channel route (410 symbols, six gates on certified bytes) revives. Assets intact: frozen panel + 154 clocks + V7 baselines. |

V8 addendum (2026-09-05, same day): the owner's own browser test of both Stooq
per-symbol endpoint URLs (twtr/sivb) returned nothing downloadable
(`endpoint_test_owner.json`) — the last free avenue is closed. The free
price-source space is now exhaustively measured: Stooq bundle FAIL G3,
Stooq endpoint FAIL G3 (owner-measured), Massive dead-by-depth, Twelve Data
Basic FAIL G3. Stocks stands dormant with no free path; re-opens only on an
owner-entitled delisted-inclusive source.

V8 activation addendum (2026-09-05, later): owner purchased EODHD "EOD
Historical Data — All World" ($19.99/mo, monthly cancel) and placed the key
in gitignored `.env`. **Six-gate probe: ALL PASS**
(`stocks_free_v8_probe/eodhd_probe_verdict.json`) — gate 3 decisive: 5/5
dead canaries with real history ending at exact death sessions (SIVB final
bar 2023-03-09; TWTR final bar 2022-10-27; FRC/TWX/SIVBQ all correct) +
59,923 delisted US symbols + 3/3 never-existed controls absent; CMG 50:1
(2024-06-26) and TJX 2:1 (2018-11-07) reconcile with SEC-pinned facts plus 7
bonus split signatures all correct; 0 OHLC violations/54,119 bars; double-pull
3/3 byte-identical. **V8 cycle authorized to start** — fundamentals-conditioned
discovery on the frozen 154 clocks; HARD STOP before first scored cell pending
owner GO phrase.

## D. FOREX — G10 spot, 7 free-data pairs

| Cycle | Family | Mechanism (short) | Outcome |
|---|---|---|---|
| F1 (orca/forex-integration) | — | Twelve-Data paid-source era | FOREX_BLOCKED_DATA_OR_ROLLOVER_AUTHORITY then FOREX_BLOCKED_SELECTION_INSUFFICIENT. Never scored; pivoted to free sources. |
| Free-V1 | FXFV1-A3-P1 London-open session continuation | London-open momentum, NY-open neighbour, sign-flipped control | REJECT — anchor expectancy −2.35/trade, PF 0.849, all 3 folds negative, 11,459 trades, 7 pairs. |
| Free-V1 | FXFV1-A3-P2 Late-NY fade | Fade of standardized intraday extension into late NY | REJECT — FOREX_FREE_V1_REJECT_ALL, 6/6, reproduced. |
| Free-V2 (CLOSED 2026-09-04, REJECT_ALL 6/6, repro byte-identical, A7 terminal PASS) | FXFV2-A4-P1 Tokyo-range compression → London-morning expansion | Session-range breakout; 1,541 trades anchor | REJECT — **all three arms FAIL EXPECTANCY_NONPOSITIVE (anchor −3.804/trade, PF 0.593; neighbour worse; control worse still)**: coherence exists (anchor > control) but no edge; break-even −0.40 bps → the gross pre-cost edge was already negative, costs only deepen it. |
| Free-V3 (SURVIVOR DOWNGRADED then **INVALIDATED 2026-09-05** by its own remediation `FOREX_FREE_V3_DATA_AUTHORITY_INVALIDATED`, V3R terminal `c356813`) | FXFV3-A6-P1 family2 | **Realized-vol regime-gated policy-rate-differential carry** (LOW-vol holds as-of BIS WS_CBPOL differential direction, HIGH unwinds; daily 16:00-NY clock; dual-book financing) | **INVALIDATED, recorded not repaired.** Under evidenced announcement availability (47/159 events evidenced, 112 conservative-later): anchor PF 1.2825 fin-adj / expectancy +20.72 — **economically present, contract-invalidated** — fails frozen STRESS_TIER_2.0; control arm irreproducible (ONE_EVENT_LAG_VIOLATION USDJPY, mechanism sanity null); availability correction flipped 19 positions across 158 decisions. Family2 in forbidden inventory (disposition DATA_AUTHORITY_INVALIDATED); front-door re-entry open only via a future owner-preregistered plan under ancestry rho gates. S1 never opened — the remediation pipeline conserved it (LESSONS.md P-5). |
| Free-V3 | FXFV3-A5-P1 family1 | (see cycle artifacts) | REJECT — all three arms FAIL EXPECTANCY_NONPOSITIVE (anchor −4.59 / neighbour −9.35 / control −33.30). Forex denominators 18/18. |
| Free-V2 | FXFV2-A4-P2 London-AM range break + retest-hold | Breakout confirmed by retest; 3,830 trades anchor | REJECT — anchor −3.093/trade PF 0.720; **control ≈ anchor (placebo reproduces the behaviour → mechanism not specific)**; break-even −0.05 bps; USD-drift ruled out (|corr| ≤ 0.072). Carry-forward lesson: MEDIUM F1 — stress-tier cost multipliers never applied to booked PnL; mandatory fix before any future cost-sensitive cycle. |

## E. Near-misses — the most informative rows (read before proposing anything)

1. **ILLIQ-AMIHUD (crypto V11)** — 12/13 gates; PF 1.355, MDD 9.2%, 3/3 folds.
   Failed only symbol-concentration 0.7055 vs single frozen gate. Replication
   blocked by data. The number to beat.
2. **CARRY-7D (crypto V6)** — PF 1.157, real carry, rejected on fold
   concentration 51.66% vs 50%. Marginal gates are doing real work.
3. **H-XSECT-MOM-v1 (crypto sprint V4)** — +9.7k vs −27.2k control,
   beta-neutral: genuine cross-sectional momentum signal destroyed by gross
   drift and MDD. A risk-engineering problem, not a signal problem.
4. **A4 stocks momentum (V2)** — raw expectancy fine, but bottom-3 control
   earned 96.5% of anchor: sector beta, not selection skill. First hard proof
   that long-beta can masquerade as mechanism in this cohort.
5. **LOT (crypto V11)** — inverted family: control won where anchor lost.
   Chasing the inversion would be rescue; recorded, not pursued.

## E.2 The falsification-by-control cluster (2026-09-04, V11→V12→V4)

Five of the last eight scored families were killed not by weak anchor PnL
alone but by **their own controls outperforming them**: V11 LOT (inverted
control PF 1.34), V12 OILEV-V2 (inverted control +0.758 vs anchor −0.821),
V12 BAB (inverted control ≈0 vs negative anchor), Stocks V4 participation
(stale-rank control +14.9% raw vs anchor −17.6%), Stocks V4 semivariance
(vol-level control +53.1% vs anchor −28.1%), and Forex V2 family2 (placebo
control ≈ anchor: the behaviour reproduces without the mechanism). This is the control apparatus
working exactly as designed: it proves the frozen mechanism identity/sign is
wrong, not merely unprofitable. Three "shadow effects" are now *measured
phenomena* — inverted-OI-flow, plain vol-level sorting, sector-exposure form —
each with raw PnL but each failing alpha/concentration/MDD gates. They are
NOT tradable findings and NOT rescuable descendants; a future cycle may
propose them as brand-new preregistered families with their own falsification
controls and measured decorrelation vs these ancestors, through a new owner
plan — never as a sign-flip of a rejected cell.

## F. What the cumulative evidence says (as of 2026-09-04)

- Price/volume-derived cross-sectional and time-series signals on liquid
  crypto perps at weekly/quarterly clocks: **mined to rejection** at current
  costs and gates — 125+ logical cells, zero promotions.
- Session/open FX momentum/fade on free G10 data: rejected at high trade
  counts (cost-dominated).
- Sector-ETF momentum/trend/TOM/idio-reversal at daily frequency with ETF
  costs: rejected; sector beta is the recurring confound.
- The surviving frontier is **conditioning variables from new information
  sets** (OI/leverage flows, illiquidity formation, participation, variance
  shape, session-range structure) — which is exactly what V12 (OILEV-V2,
  BAB-LOWBETA), Stocks V4 (participation-shift, semivariance-share) and Forex
  V2 (range structure) are now testing, and what Data Fusion V1 exists to
  widen further (PIT fundamentals, rates, vintage macro, positioning).
- Lesson registers (L1–L7 stocks, L-V11-1..7 crypto) and forbidden-family
  inventories are append-only and must be carried into every next plan.
