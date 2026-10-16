## Sprint state (synced at the BTC-COMBO6-SCORED-V1 terminal, 2026-09-29)

- **BTC-COMBO6-SCORED-V1 TERMINAL -> `COMBO6_NO_INCREMENTAL_VALUE`** (owner-directed
  replication: 6 screenshot bot strategies combined into one $60k portfolio,
  BTCUSDT 2021-01..2025-12 walk-forward, 7/12 scored cells, 0 survivors).
  Branch `orca/btc-combo6-scored-v1-integration` terminal `6f9dfd52`
  (base main `2481f307`; chain 2481f307 -> 2db0e19b IMPL -> c0f97a9d FREEZE ->
  ce1dd0ef GO -> 7f3cce39 scored -> 6f9dfd52 terminal).
  - Combo net **−63,617.86** (PF 0.916, 4/10 folds, maxDD 97,271/60,000;
    ×1.5 −100,107; ×2.0 −136,597) vs **B1 always-long +10,689** — passive
    dominates. LEG-2 (MA 4h/24h turn +4,708) and LEG-3 (MA 12h/72h +1,662)
    pass P1 in isolation; LEG-1 momentum 1%/4h **−46,534** (3,795 trades ×
    ~$12 fees — pure churn); no leg promoted post-PnL.
  - Gate arc: sanitized dry-run (6/6 non-vacuous, leak-proof) -> A7 prelaunch
    AUTHORIZED_WITH_FINDINGS (wrapper-flag F-1 fixed pre-score) -> two-key GO
    (owner standing directive consumed at gate) -> scored under heavy lock ->
    repro twin ALL_MATCH (byte-equal + 18/18 truncation replay) -> A7 terminal
    CONFIRM_WITH_CONDITIONS (all numbers re-derived delta 0; C1 DSR
    NOT_COMPUTED erratum, C2 freeze binding, C3 digest typo I-1 — all
    discharged in TERMINAL_DECISION.md).
  - **Fold erratum precedent**: independent data lane (A3) caught the plan's
    260-week arithmetic slip (2025-12-26 -> 2025-12-29) BEFORE freeze — the
    cheap-win pattern for every future fold calendar.
  - Family death `BC6-OWNER-PINNED-TA-COMBO-6LEG` (FAMILY_FAILURES); ancestry
    fence now blocks TA re-parameterizations of these legs without a changed
    mechanism axis. Durable: btcombo6 engine + 102-zip sha-pinned perfect-grid
    5m corpus (707,616 bars) + measured funding series.
  - Denominators (P-9): +7 observed / +7 published this cycle; program union
    left to next canonical reconciliation.

## Sprint state (synced at the PORTFOLIO-ROUTER-12ASSETS-100K-V1 terminal, 2026-09-28)

- **PORTFOLIO-ROUTER-12ASSETS-100K-V1 TERMINAL → `ROUTER_STATES_THIN`** (0
  scored cells, 0 PnL, S1 SEALED, budget 0/64, GO phrase extinguished
  UNCONSUMED — the owner's standing scored delegation had no gate to open).
  Branch `orca/portfolio-router-12assets-100k-v1-integration` terminal
  `8669f478` (base main `abe7f70b` via `a51dc758` evidence landing).
  The 12-asset FX+metals+energy macro-state router died at the preregistered
  pre-PnL battery, twice, before any outcome existed:
  - **PIT first (owner's parallel priority): ALL 3 gates PASS_EVIDENCED**
    (`pit/PIT_DOSSIER.md`, 50 sha256'd raw files) — EFFR usable d+1 15:00 ET;
    VIX CBOE-channel d 16:15 ET (FRED mirror identical 9,278/9,278 dates,
    3-vintage no-retro-revision); Brent−WTI frozen conservative rule
    obs ≤ decision−10cd (measured EIA weekly-release cadence; T−1/T−2
    rejected as lookahead). NOT_RUN_PIT_GATE_FAILED did NOT fire — the data
    PIT-proved clean; the engine died on statistics.
  - **Kill 1 — state floors:** census over 286 Fridays 2021-01..2026-06:
    WAR_ENERGY 10 merged episodes (F1 margin 0), RISK_STRESS 7, TIGHTENING 2,
    EASING 3 → 3/4 states F1-fail; all states NOT_RUN_THIN → permanent FLAT
    rows; ≥2 thin ⇒ typed close (policy §3.5 / protocol §4.1, no relaxation).
  - **Kill 2 — P-29 representation-rho:** V2 (VIX 252d pct) vs dead
    RGC-G2/FXFV3-A6 vol-percentile class: 0.4828 / 0.3034 / 0.2179 vs the
    immovable 0.20 bar — floor-independent kill of the V2 layer.
  - A7 terminal `CONFIRM` 0C/0H/1M/3L/3I — rho + episode census independently
    recomputed to ≤4e-10; no post-census edits to frozen laws; close verified
    F2/F3-defect-independent. Battery payload `4a5f0fc5` double-reproduced.
  - **Durable assets:** PIT-evidenced raw store (VIX/Brent/WTI/EFFR with
    frozen available_at rules — the program's first fully-evidenced macro
    panel), 5-FX-pair verified data plane (M1×3 + H1×2, 286-week grid,
    UTC/DST-proven loaders, 33/33 tests), the state-engine + battery harness
    (truncation no-lookahead replay law), 1,200-row census with frozen
    pre-PnL rubric, and LESSONS P-31 (floor feasibility annex). Family death:
    `PR12A-MACROSTATE-3VAR-WEEKLY` (FAMILY_FAILURES line 170).
  - Census headline for successors: 1,200 brainstorm ideas = 15
    DISTINCT_TESTABLE (all on the 5 evidenced FX pairs) / 433 PIT_UNPROVEN /
    548 dead-class variants / 121+15 data/cost-blocked / 68 unfalsifiable —
    a sleeve-only program on the eligible pairs is the open successor
    question, requiring its own cycle (plan §0 / TERMINAL_DECISION).
  - Denominators UNCHANGED (P-9): +0/+0 scored cells.

## Sprint state (synced at the DTP-FX-MECHCOURT-V1 terminal, 2026-09-27)

- **DTP-FX-MECHCOURT-V1 CLOSED → `DTP_FX_V1_BLOCKED_DATA_OR_COST`**
  (owner instruction 2026-09-27 named three FX day-trading mechanisms;
  branch `orca/dtp-fx-mechcourt-v1-integration` terminal `c0193b8e`
  (base main `051aaae0`); **0/0 scored cells, 0 PnL, 0 holdout looks,
  sealed AUDUSD/USDCAD 2026-H1 UNREAD, S1 SEALED, GO phrase
  REGISTERED_NOT_CONSUMED → extinguished unconsumed** — no gate ever opened;
  no orders, no shadow/broker/dashboard touched; A7 terminal
  `CONFIRM_WITH_FINDINGS` 0C/0H/2L/3I — census recompute delta 0, anti-variant
  independently agreed 0/3 axes):
  - **A `DTPFX-A1` month-end London fix rebalancing → `F0_KILLED
    VETO_VARIANT_SAME_FAMILY`** vs `TRACKA2-P4A-FIXCERT-01` — month-end
    day-subset is a re-gate and public-MTD direction a rename of the fix
    pressure-sign; strip test leaves the dead FIXCERT decision law; RC bars
    parameter re-tunes. FAMILY_FAILURES `DTPFX1-A1-MEFIX-VARIANT`.
  - **B `DTPFX-B1` news→observed-rate-reaction→FX → `BLOCKED_DATA`** — the
    rate-reaction leg cannot be witnessed at entry: intraday rates = 0 bytes
    program-wide (OFR/NYFed daily-only; CME transport-blocked; futures
    0-byte stubs); PIT release ledger 10/131 FETCHED-verified, no consensus/
    revision vintages, self-labeled EVENTS_OVERLAY_ONLY_NOT_CAUSAL_EVIDENCE.
  - **C `DTPFX-C1` cross-venue synchronous quote discrepancy →
    `BLOCKED_DATA`** — one two-sided feed exists; second venue 0 bytes on
    every measured path (IBKR probe 0/357 obs/pair + minTick 0.5 pip;
    Dukascopy re-download SNI-blocked; EDQ1 owner-gated).
  - **New measured frontier asset: first full fix-window spread census**
    (EURUSD/GBPUSD/USDJPY, London-hours 13–17 × ME1/ME2/MID; 34,715
    non-vacuous obs, DST-verified, A7 delta 0): fix-window p50
    0.3/0.7–0.8/0.5 pip ≈ mid-month ±0.1 — the fix window is NOT an
    expensive bucket; only rollover 21–22UTC widens (p99 7.8–16 pips). The
    fix-family barrier is premium-evidence + venue, not spread.
  - Owner unblock packet (exact sources/access/data per mechanism):
    `research/control/DTP-FX-MECHCOURT-V1/OWNER_PACKET.md`. Denominators
    UNCHANGED (+0/+0; 3 ADJUDICATION_NOT_SCORED rows; P-9).

## Sprint state (synced at the DTP-CX-SOLUSDT-C1 terminal, 2026-09-27)

- **DAYTRADE-PLAYBOOKS-PROGRAM-V1 opened (charter GO-1 packet commit `9ba72e6c`;
  A7 plan review r1 AUTHORIZED_WITH_FINDINGS, F1–F11 remediated pre-commit) and
  its FIRST pair-child DTP-CX-SOLUSDT-C1 CLOSED → `NO_ELIGIBLE_PROPOSAL`**
  (2026-09-27; branch `orca/dtp-cx-solusdt-c1-integration` terminal `f85cb6b9`;
  budget **0/18 scored cells, 0 PnL anywhere, trial_ledger header-only, S1
  SEALED_UNTOUCHED, GO-2 phrase REGISTERED_NOT_CONSUMED (moot — freeze empty);
  no orders, no shadow/worker touched**; A7 terminal `CONFIRM_WITH_FINDINGS`
  (18/18 decisive recompute exact; 38 distinct family citations verified) →
  ERRATA E1–E4 (clock-note: artifact stamps must be MEASURED, not estimated) →
  A7 re-review `CONFIRM_CLOSE`): the owner-directed day-trading-playbook
  program (independent of running shadows; taxonomy-first with 11/13 classic
  playbook rows measured-dead pre-registration; FX track DORMANT pending
  reopener R1/R2/R3/R5; crypto no-candle→order-flow law enforced).
  - **I002 BTC→SOL 1m lead-lag (the only taxonomy OPEN-KILLRISK row) killed
    pre-PnL by 3 independent laws WITH power in hand**: SOL reprices within
    the signal minute (median 17.8–62.8 bps vs next-minute −0.245..0.000);
    ceiling×power grid jointly EMPTY (net −9.97..−11.47 bps/RT @1.0× vs
    measured RT ladder 11.92/17.88/23.84); representation rho 0.2341–0.5085
    (>0.20 at ALL θ). aggTrades budget-widening does NOT revive. FAMILY_FAILURES
    `DTPCX1-I002-LEAD-LAG-DIFFUSION`.
  - **I001 outcome-blind annotated playbook corpus (generator route): death
    rate measured 100%** — 12 admissible dated entries / 6 authors (floor PASS
    after a pre-declared bounded supplement, addendum r2, 37/50 fetches;
    Reddit/TradingView walls logged, not breached; no price panel ever
    loaded); skeptic court R2 killed 11/11 codified rules by skeleton
    collision (range-fade / breakout-continuation / trend-pullback /
    H&S-with-break = breakdown-continuation rename / news-fade; 38 distinct
    family_ids; K-COST fired on none). Scope-bounded close (mandatory sentence
    in CYCLE_VERDICT — NOT a claim that "day trading is dead"). FAMILY_FAILURES
    `DTPCX1-I001-PLAYBOOK-CORPUS`.
  - Durable assets: staged SOL 1m/15m/mark/index + BTC 1m corpora (404.6MB,
    sha-pinned, all-ms PIT-verified); RT cost ladder + ceiling×power grid
    template; frozen annotation protocol + corpus method; court scripts
    (A7-verified reproducible).
  - **Program decision (viability review, owner-directed): BTC next-pair
    request → `PARK_DTP_NO_NEW_FRONTIER`** — no BTC candidate differs on ≥2/3
    anti-variant axes with PIT+cost authority (V16's "sub-daily aggTrades" is
    a data axis, not a mechanism: every nameable skeleton on it is
    measured-dead; BTC spread census NOT_RUN = weaker cost authority than
    SOL's). Reopen via RC-1 new PIT information layer / RC-2 owner plan naming
    a mechanism / RC-3 FX reopener (DTP-FX AUDUSD is the program's lawful next
    surface) / RC-4 program-level NO_CANDIDATE close. Evidence:
  `research/control/DAYTRADE-PLAYBOOKS-PROGRAM-V1/VIABILITY_REVIEW_BTCUSDT.md`.
  - Denominators UNCHANGED (0 scored cells; P-9).

## Sprint state (synced at the DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 terminal, 2026-09-26)

- **DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 CLOSED → `DATA_FOUNDATION_V1_FOUNDATION_READY_FOR_NARROW_RESEARCH__BLOCKED_WITH_ACQUISITION_RUNBOOK`**
  (2026-09-26; branch `orca/data-foundation-v1-integration` terminal
  `bb010bc9`; owner-directed data/methodology cycle, **0 scored cells,
  0/0 budget, S1 SEALED, no orders, no PnL anywhere**; A7 plan review
  AUTHORIZED_WITH_FINDINGS (1 HIGH disk) remediated pre-registration +
  A7 terminal audit 0C/0H/3M/3L all closed; 5 survey lanes (fx/cx/st/pit/
  cost) with structured handoffs integrated serially; **91 authority rows
  validator-VALID — 32 AVAILABLE_VALIDATED re-measured from bytes**
  (Dukascopy M1 ×5 corpora, amihud 8,219/8,219 full re-hash, FTD 434 zips,
  Form-4 substrate digest EXACT, SOL/ETHUSDT/DEU crypto families 38/38
  sampled ALL_MATCH); PS1 probe measured **premiumIndexKlines available
  keyless on Binance Vision (sha-verified)** resolving the forecast-funding
  gap at ~7 MB; exposure map 28 audited rows vs 5 UNOPENED classes; cost
  authority census #4: FX 2/10 components measured (IBKR TWS alive today,
  API proven — gates are FX-subscription + statement export), crypto 3/10,
  stocks 0/10; **owner runbook R1–R8** (R1 = one IBKR Activity/Flex
  statement + free FX delayed data = highest-leverage action; R7 = 8/14
  staging_backups archives ABSENT incl. V14 OI forest — P-13 drift owner
  item); next frontiers F1 stocks READY-PARTIAL / F2 crypto READY / F3 FX
  BLOCKED-R1; denominators unchanged per P-9).

## Sprint state (synced at the PWS-CX-SOLUSDT-C1 terminal, 2026-09-26)

- **PWS-CX-SOLUSDT-C1 CLOSED → `NO_ELIGIBLE_PROPOSAL`** (2026-09-26; branch
  `orca/pws-cx-solusdt-c1-integration` terminal `c3671fad`; the FIRST
  pair-child of PWS-PROGRAM-V1 — the ≤100-identity pair-by-pair program
  opened 2026-09-26 under recorded owner delegation after double A7 plan
  review; budget **0/18 scored cells, 0 outcome views (trial_ledger 0
  rows), 0 holdout looks, S1 SEALED_UNTOUCHED**; A7 terminal
  `CONFIRM_NO_ELIGIBLE_PROPOSAL` 0 HIGH/1 MED/4 LOW with independent
  recompute of every decisive number; GO-2 phrase died UNCONSUMED; no
  orders; no shadow/worker touched): council outcome-blind ran 2 proposer
  lanes + skeptic F-0 court — **P1 killed all 11 expressible direction
  sources on the authorized observables pre-proposal; P2's sole identity
  I001 TAILPAYER-RUN-REGIME (funding run-capture) died `VETOED_SAME_FAMILY`
  by representation math on the funding plane, no PnL needed**: run-gate
  state correlates 0.316–0.703 (two-sided, A7-verified) with dead CARRY
  level-window shadows — SOL funding sign autocorr +0.853 makes a sign-run
  gate a smoothed level window (cosmetic gate, P-27 again); ceiling×power
  grid is jointly EMPTY (θ≥5.23 bps ⇒ ≤8 episodes vs ≥100 floor; deep
  payments are 7 single −200 bps prints = 19.3% of negative mass, invisible
  to any ≥K-run gate); K-CONC pre-kill (2022 = 59.1%, FTX 9-day = 42.2%).
  Durable assets: verified SOL data plane (klines 52,145 bars floor-exact
  + funding 6,580 settlements bit-exact + 6-month bookTicker spread census
  p50 0.469 bps, sha-pinned inventory, license ToU captured); the cheap
  pre-PnL kill pattern (representation-rho + ceiling×power grid) reusable
  for BNB/BTC/ETH children. IDENTITY_REGISTRY 1/100 consumed (I001
  F0_KILLED). Track note: pair-child #2 (BNBUSDT) remains lawful under the
  approved order (stop-rule needs 2 consecutive empty slates) but the
  fences here are pair-agnostic on the same observable classes — A7/A1
  recommend pair #2 only with an evidenced new-information angle, else the
  outcome repeats. Revival conditions in FAMILY_FAILURES
  `PWSCXSOL1-I001-TAILPAYER-RUN-REGIME`.

- **PWS-CX-BNBUSDT-C1 CLOSED → `NO_ELIGIBLE_PROPOSAL`** (2026-09-26 tối;
  branch `orca/pws-cx-bnbusdt-c1-integration` terminal `33a69f10`; budget
  **0/18 scored cells, 0 outcome views (trial_ledger 0 rows), 0 holdout
  looks, S1 SEALED_UNTOUCHED**; A7 terminal `CONFIRM_WITH_FINDINGS` 0
  HIGH/CRITICAL + 3 LOW errata'd — every recompute exact; GO-2 phrase died
  UNCONSUMED; **0 IDENTITY_REGISTRY slots consumed** — N_registry stays
  1/100; no orders): pair-child #2 under the discovery sprint (owner
  instruction 13:41Z: "kiểm tra pair kế tiếp theo luật PWS; nếu cùng thông
  tin cũ ⇒ đóng, không chạy backtest"; GO-1 consumed 14:10Z under the
  delegation GO-chain reading + independent A7 plan-review 9caac6ba
  AUTHORIZED_FOR_GO1_GATE; both readings recorded in the GO RECORD). C1
  measured BNB's own plane: klines 57,472 bars GAPLESS floor-exact
  2020-02-10; funding n=7,261, median 0, 49.6% zero prints, neg_share
  23.94%, worst −58.44 bps, 0 deep prints, 0 anomalous spacings — a REAL
  pair-contrast vs SOL; spread census `NOT_RUN_DISK_CONSTRAINT` (df 7GB <
  25GB, fail-closed, no substitution). Council: P1 blind enumeration 0/11
  direction sources survive (5 autopsies; BNB event-layer burn/SEC-DOJ =
  BLOCKED_NEW_DATA_OWNER_GATE, R5-class revival condition for the owner);
  skeptic-verify measured the kill ON BNB's series: sign persistence lag-1
  +0.759, representation rho 1.12×–2.97× the 0.20 bar vs CARRY level-window
  shadows at both thetas and BOTH side conventions; ceiling×power at
  fee-only floor 80 episodes < 100 floor (not empty like SOL — disclosed);
  K-CONC pre-kill does NOT transfer (25.5% < 50% — disclosed; the kill
  rests on same-family + K-ANC). **Track PWS-CX stop-rule §9(a) FIRES: 2
  consecutive empty pair-children ⇒ viability council mandatory before any
  new pair-child; LESSON P-29 "pair-swap opens nothing" now
  measured-confirmed on a second pair.**

## Sprint state (synced at the SRLV-CX-C1 terminal, 2026-09-26)

- **SRLV-CX-C1 CLOSED → `REJECT_ALL`** (2026-09-26; branch
  `orca/srlv-cx-c1-integration`; budget **6/18 scored cells observed, 0
  holdout/OOS looks, S1 SEALED_UNTOUCHED**; A7 terminal
  `CONFIRM_REJECT_ALL` via independent recompute under both freeze
  readings): cohort-1 of SRLV-PROGRAM-V1 (crypto track: S/R · sweep ·
  vol-state on Binance perps). Council outcome-blind froze 1 mechanism
  (skeptic vetoed 3 same-family pre-PnL; 2 slots left empty+closed):
  **M1 SETTLE-RESOLVE** — settlement-adjacent sweep-then-absorption at
  N=6 pivots, BTC/ETH 1h 2020-2026, flat-by-settlement (pin-10), fee
  5bps+1tick DECLARED. Died at dev gates on BOTH pairs: BTC net −24,956
  bps PF 0.651 (n=1,482; 749/733 per direction), ETH −33,515 bps PF 0.634
  (n=1,518); all folds/directions/tiers negative; DSR 0.0. Kill laws:
  G1–G4 + **K-CTRL inverted out-earns anchor both pairs (ETH inverted
  +2,573 PF 1.035 — settlement adjacency favors continuation, not
  absorption)** + **K-ANC rho 0.248 (rev24, BTC) / 0.256 (bandfade, ETH)
  > 0.20**. Baselines crush (long-hold +64.8k/+114.2k bps; funding
  measured 11.81/13.96%/yr). Fixtures ALL PASS pre-scoring (truncation
  0/512, mutation 0/25, flat 0 violations) — kill is economics, not
  leakage. The F-0 revival clause ("settlement schedule = new information
  layer") was granted in full and died at measured outcome. Surface
  closed against re-clock/re-label/buffer/window variants
  (FAMILY_FAILURES `SRLVCX1-M1-SETTLE-RESOLVE`). FX track untouched —
  NO_CANDIDATE stands, no reopener evidence yet.

- **ERP1-TRACKA-COHORT-2 CLOSED → `REJECT_ALL`** (2026-09-26; branch

- **ERP1-TRACKA-COHORT-2 CLOSED → `REJECT_ALL`** (2026-09-26; branch
  `orca/erp1-tracka-cohort-2-integration` terminal 206a157b; budget **0/18 —
  zero scored cells, zero holdout looks, zero PnL anywhere**; A7 terminal
  `TERMINAL_AUDIT_PASS` 0C/0H/2L/3I; S1 SEALED; GO-2 died
  REGISTERED_NOT_CONSUMED; no orders; no shadow worker touched): the first
  cohort run under the **F-0 mechanism-class court** (owner law 2026-09-26:
  "adding an observable is not a new mechanism") — **all 7 candidate
  mechanisms falsified BEFORE any PnL**:
  - C1 PROV-ABSORB / C2 RECLAIM-ABSORB / C3 PROBE-DEPLETION →
    `VETO_VARIANT_SAME_FAMILY` at F-0 (skeleton test: strip the gate, the
    dead RANGEFADE law remains; C1 double-killed by the cost lane's
    ceiling −1.6/−2.1 pips vs 3.6 stress).
  - P4-A FIXCERT-01 / P4-B QSKEW-01 (blind open-call, class-distinct) →
    killed by their OWN frozen declared bands (below the measured stressed
    book at their own fill hours; P4-B below even base ×1.0).
  - **P3-A QCRD-H1 — the cohort's flagship negative**: F-0 pass (dealer
    impact-cost payer), PIT battery PASS (0 truncation/future-mutation
    diffs), **F-1 PASS with worst |rho| 0.0786/0.0883 over 47 shadows**
    (A7 independently recomputed exact) — then **F-5 measured
    `CEILING_NEGATIVE_VETO`**: the binding condition needed tight-state
    crossings ≤0.41 pips @k=2.0; measured 0.9–1.0 pips. Novelty,
    PIT-cleanliness and decorrelation did not fund the bill (Q-1 live).
    Reopens only on measured all-in execution cost below the frozen
    threshold (broker/venue authority — BLOCKED program-wide).
  - P3-B DINV-1D → `ANCESTRY_RHO_BLOCK` 0.3032/0.3103 (H1TSMOM/H1DONCH +
    more; representation-robust): day-cadence quote-gated continuation is
    the dead momentum class re-clocked (Q-3).
  - Durable falsifier infrastructure: generic PIT battery (leak-catch
    proven on the RANGEFADE class), 47-shadow arrays + one-shot rho runner,
    engine inheritance chain (P-13), F-0 court procedure. Sealed holdouts
    2026-H1 AUDUSD+USDCAD remain UNREAD program assets. Next: owner-gated
    cohort-3 viability council (master §7 stop-conditions apply — two
    consecutive REJECT_ALL cohorts).
  - **Viability council verdict 2026-09-26: `NO_CANDIDATE` on the currently
    authorized frontier** (`forex_program/VIABILITY_cohort3_REPORT.md`: 0/12
    remaining mechanism classes pass pre-PnL checks; the measured cost floor
    3.6/4.4-pip stressed RT partitions the space with zero remainder;
    P3-A's reopening condition confirmed unsatisfiable without owner action;
    sealed map NOT empty, so frontier-terminal, not program-terminal). NO
    cohort-3 opened. Reopening = owner actions R1–R5 in
    `forex_program/OWNER_PACKET_program_status_2026-09-26.md` (broker cost
    authority via IBKR probe / EDQ1 source decision / financing band /
    USDCHF slate / new evidenced information layer).

# Wayfinder map: evidence-led profitability research for my-quantitative

## Sprint state (synced at the ETHUSDT-OPEN-SEARCH-V1 terminal, 2026-09-25)

- **ETHUSDT-OPEN-SEARCH-V1 CLOSED → `ETHUSDT_OPEN_SEARCH_V1_NO_INCREMENTAL_VALUE`**
  (2026-09-25; tranche 1 of the owner-directed ETHUSDT campaign, standing
  directive 2026-09-24 "mở cycle tìm kiếm strategy cho ETHUSDT cho tới khi
  tìm được strategy kiếm tiền có bằng chứng kinh tế rõ ràng"); branch
  `orca/ethusdt-open-search-v1-integration` terminal 8196e3ea (base main
  f3daf990), plan `plans/PLAN_ethusdt_open_search_v1.md`. POSTHOC S0
  DISCOVERY, single-asset ETHUSDT USDT-M perp H4 2020-01..2026-08, keyless
  Vision corpus (ES1 cross-check 80/80 byte-identical; funding measured,
  7,305 settlements floor-exact), 2 new-tuple lanes × 4 configs = 8 cells.
  **G3 wall killed all 8: ALWAYS_ON +1,653,470 @1.0x (98% in F1) vs max
  cell 625,621 — no long/flat gate book beats raw F1 beta posthoc.**
  Near-miss of record: E1-A1 (BTC-SMA200→ETH) 496,114 conc 0.488 and E1-A4
  (BTC∧ETH-SMA200) 485,187 conc 0.424 — 4/4 folds positive, beat
  TREND_LF, controls clean, fail ONLY the always-on raw-net wall (the wall
  reference is itself ~0.93 fold-concentrated: structural G3-vs-G5
  tension, disclosed, gates untouched). Lane E2 (ETHBTC ratio) G6-killed:
  shuffled ratio out-earns real ratio — no timing information. A7 prelaunch
  remediation arc (2 blocking pre-PnL defects fixed: G7 semantics,
  settlement PIT) + 2 zero-exposure TECHABORTs remediated; repro twin
  ALL_MATCH; A7 terminal CONFIRM_WITH_FINDINGS. Families EOS1-E1/E2 now
  dead (BTC-price-state gates and ratio-gates for ETH single-asset, incl.
  symbol swaps). CAMPAIGN CONTINUES per standing directive: tranche V2
  (BTC-vol-state + alt-breadth lanes — the last defensible new-tuple
  space on keyless data) registration follows; exhaustion ⇒ owner
  redirection decision.
- **BTC-BEAR-OPPORTUNITY recon CLOSED PRE-CYCLE → `NO_ELIGIBLE_PROPOSAL`**
  (2026-09-23, owner directive: forced-flow/liquidity-dislocation short or
  market-neutral mechanisms in BTC downtrends; NO cycle opened — P3
  precondition failed, no registry row, no scored cell, no GO; evidence
  `research/control/bear_opportunity_recon_2026-09/` committed this date;
  A7 CONFIRM_WITH_FINDINGS 0 blocking, decisive numbers independently
  reproduced): lane A2 measured data authority (klines/mark/index/premium/
  funding PIT_USABLE multi-year; **liquidationSnapshot ZERO coverage**;
  multi-year PIT OI/order-book none; frozen DOWNTREND label: 20.1% occupancy,
  59 merged independent episodes, floors PASS; in-downtrend funding mean
  +3.709e-5/8h RECEIVED by shorts, 24.7% settlements negative); lane A3
  (outcome-blind) proposed exactly 2 mechanisms; lane A4 vetoed both
  pre-PnL: **Confirmation-Lag Front-Run → VETOED_FICTIONAL_COUNTERPARTY**
  (counterparty = the repo's own research label; G6 already measured the
  label's timing informationless; 284 entries vs ≤59 claimed, 88% fake-outs)
  and **Mark-Trigger Catch-Down → VETOED ×3** (preregistered neighbour
  control fires opposite: wide-spread events −4.87% mean gross per short vs
  flat matched crashes; 13 independent clusters with 91.1% in one COVID
  week; ancestry class-7 premium-fade rho −0.418/−0.515 > 0.20 bar,
  construction identity −0.68). Bear-side short sub-family on BTCUSDT-PERP
  H4/5m measured-closed at the mechanism layer. Reopening: new PIT-authorized
  multi-year source (real liquidation/OI tape) or owner plan naming a
  mechanism outside the ancestry table; cross-venue/ETF sources NOT gated
  (separate data-authority cycle required).
- **BTC-H4-TWO-REGIME-V1 CLOSED → `BTC_H4_TWO_REGIME_V1_NO_ELIGIBLE_PROPOSAL`
  (2026-09-23)**; branch `orca/btc-h4-two-regime-v1-integration` terminal
  4d93ff9e (base = PSV1 anchor af52f358), plan
  `plans/PLAN_btc_h4_two_regime_v1.md` (113e0c2d); owner 2026-09-23
  directive: three-state BULL/BEAR/UNCERTAIN router over the frozen PSV1
  BTC_H4 Donchian long leg (FAILED G3/G5/G6 — test component) + one
  mechanism-backed DOWN leg. **Preregistered causal drawdown-hysteresis
  detector (−0.30/−0.10 bands + 90-bar dwell; PSV1 SPARSE_RISK_OFF
  constants) frozen BEFORE the census; census (14,589 post-warmup H4 bars):
  15 state changes in 6.7y, episodes merged BULL 5 / BEAR 6 / UNCERTAIN 5 —
  ALL THREE STATES FAIL the immutable floors 20/3/100 → every state-gated
  arm NOT_RUN_THIN, no relaxation (owner law); DOWN leg: zero candidates
  survive the preregistered E1–E5 law (E4 fails independently; liquidation
  tape 404 UNAVAILABLE_FAIL_CLOSED; cross-venue unstaged; funding-extreme
  overlay collapses to the dead DOWN_SHORT class + funding-LEVEL shadow
  exposure).** The detector HAS PIT evidence (no-lookahead fixture PASS) and
  is a genuinely different law (agreement BULL~PSV1-UPTREND 0.599 /
  BULL~SMA200 0.526 / BEAR~DOWNTREND 0.493), but a hysteresis machine on ONE
  asset over 6.7y is structurally thin; lag descriptive: first BEAR 17.0d
  after the 2021 top anchor, first BULL 520.7d after the 2022 bottom anchor,
  BEAR at data end since 2025-11-20. Repro: detached twin byte-identical
  modulo schema timestamp; A7 terminal fresh-context CONFIRM 0 blocking
  (independent recompute 144/144; 2 LOW verdict-invariant wording findings);
  budget 0/4; GO phrase `GO BTC H4 TWO REGIME V1 SCORED EXECUTION` died
  UNCONSUMED; S1 SEALED; no orders. Evidence:
  `.worktrees/btc-h4-two-regime-v1/integration/research/control/
  btc_h4_two_regime_v1/` (census/, P2_ADJUDICATION_AND_CLOSE.json,
  audits_a7/). Denominators UNCHANGED: program 283/286 (P-9).

- **FX-MAJORS-SEARCH-V1 CLOSED → per-pair `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`
  (GBPUSD with conviction / USDJPY thin)** (2026-09-24, owner: transfer the V2
  design to GBPUSD+USDJPY; branch `orca/fx-majors-search-v1-integration`
  terminal ff06fb74; budget 96/96; S1 SEALED; no orders; GO phrase
  extinguished UNCONSUMED; A7 prelaunch AUTHORIZED + terminal CONFIRM 0
  blocking): **the wide-range-day fade mechanism now generalizes across
  THREE pairs.**
  - GBPUSD (STRONG): dev +8,525.2 pips PF 1.642 **6/6 folds positive**;
    holdout 2026-H1 +164.2/+105.3/+46.4 @1x/1.5x/2x — in a choppy half-year
    where EVERY baseline lost (LONG −132.9, SHORT −47.1, RANDOM −1,546.9).
    The mechanism earned in both directions without a drift tailwind — the
    strongest anti-drift evidence in the program.
  - USDJPY (THIN): dev +3,573.6 PF 1.306 (PDHLOC-C2) / +3,128.1 PF 1.355
    (RANGEEXP-C3); holdout +35.4/+30.6 @1.0, die at 2× stress, and
    **LONG_ALWAYS +532.5 dominates the carry-rally window** — pass is
    technically valid but drift-confounded; **JPY carry-beta control
    MANDATORY** in the successor (alongside the EURUSD short-beta control).
  - Data plane: per-pair Dukascopy M1 bid/ask corpora (4,014 files/pair,
    0 missing); USDJPY 1e-3 price scale PROVEN by probe-vs-ticks; census
    BUILD_PASS both pairs (spread p50 0.8 / 0.5 pips).
  - Successor note: seed RANDOM_MATCHED deterministically (salted
    hash(pair) is not process-reproducible — A7-T1 LOW).
  - Denominators: forex 149→245/245 (this session's authority); program
    delta +96 (union reconciliation across concurrent sessions per §7).
- **EURUSD-RANGEEXP-SCORED-V1 CLOSED → `EURUSD_RANGEEXP_SCORED_V1_SCORED_RECONCILED_NO_DRIFT_FLAG`**
  (2026-09-24, owner option "1" + verbatim GO consumed at own gate; branch
  `orca/eurusd-rangeexp-scored-v1-integration` terminal 8326443; budget 6/6;
  A7 prelaunch r1 REFUSED (unregistered + cell gaps — guard worked) →
  remediated → r2 AUTHORIZED; A7 terminal CONFIRM 0 blocking): FX2-RANGEEXP
  is now **formally scored, reconciled, and measured two-sided**.
  S1 reproduction gate 12/12 byte-exact vs V2. Legs both long AND short
  profitable in both windows (C3 DEV +3,783L/+3,364S; C3 HOLDOUT
  +154.6L/+119.4S; C4 DEV +3,423L/+3,138S; C4 HOLDOUT +125.8L/+91.3S) — the
  long leg made money inside the falling 2026-H1 holdout. S6 mechanical
  drift rule **NO_DRIFT_FLAG ×4** (short share 42–48% < 50%). Mechanism
  status unchanged: `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`;
  **short-beta control stays mandatory** for the paper-forward successor
  (holdout margins −17.3/−17.6 pips). rng-continuation note disclosed
  (RANDOM holdout −267.7 continuation vs −353.5 fresh-generator; both valid
  cost-drag realizations). Denominators: forex 144→149/149; program
  **reconciled union** 395/398 → 400/403 (concurrent-session collision with
  BTC-H4-EDGE/BAND-RISK stamps documented in the RECONCILIATION stamp).
- **EURUSD-OPEN-SEARCH-V2 CLOSED → `EURUSD_OPEN_SEARCH_V2_CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`**
  (2026-09-23, owner option (a) "A" — same-day successor on the V1 data
  plane; branch `orca/eurusd-open-search-v2-integration` terminal 86668a5f;
  budget 48/96; S1 SEALED; no orders; GO phrase extinguished UNCONSUMED;
  A7 prelaunch AUTHORIZED + A7 terminal CONFIRM_CANDIDATE_PENDING_PROSPECTIVE
  0 blocking): **the program's FIRST forex candidate that survived a fresh
  holdout under measured two-sided costs.**
  - Mechanism (frozen pre-holdout): **FX2-RANGEEXP wide-prior-day-range
    fade** — when yesterday's true range is in the upper tail of its
    trailing 60-day distribution, fade today's extension beyond yesterday's
    high/low, exit halfway back, flat by 20:00 UTC (H1 exec, no
    rollover/weekend/swap risk). Dev 2021–2025: C3 +7,147.1 pips PF 1.7287,
    C4 +6,561.1 PF 1.6497, **6/6 folds positive each**. FRESH holdout
    2026-01..06 (one look, never touched by any search): **C3 +274.0 pips
    PF 1.31, C4 +217.1 PF 1.24 — both alive at 2.0× cost stress**; 87
    trades (~15/month). Verdict = pending PROSPECTIVE verification (paper-
    forward), NOT a real-money claim; **SHORT_ALWAYS +314.0 on the same
    window is disclosed** — successor must preregister a short-beta control.
  - Data plane extended: +2026-H1 corpus (362 files, 0 missing), full
    census BUILD_PASS (130,911 15m bars / 30,550 H1; spread p50 0.3 pips
    stable).
  - Incidents: dev RUN-1 VOIDED — f_daymom look-ahead (signal used the
    traded day's own close; printed +26k pips were fabricated by the bug)
    caught by RUN-1 crash + extended truncation fixtures; remediated
    (4/4 fixtures), freeze unchanged, whole run invalidated; A7-T1
    short-beta control note carried to successor.
  - Denominators: forex 96→144/144, program 331/334→379/382 (P-9 stamp).
- **EURUSD-OPEN-SEARCH-V1 CLOSED → `EURUSD_OPEN_SEARCH_V1_NO_CANDIDATE_NO_VALUE`**
  (2026-09-23 same-day lifecycle: registered BLOCKED at P1 → owner directive #2
  delegated source choice + machine downloads → ACTIVE_LIGHT → TERMINAL at
  2f5c6933; budget 48/96; S1 SEALED; no orders; GO phrase extinguished
  UNCONSUMED; A7 prelaunch AUTHORIZED + A7 terminal CONFIRM 0 blocking):
  - Data plane (new for forex): **Dukascopy public M1 BID/ASK candles
    2021-2025** — 3,652/3,652 day files 0 missing; bi5 24-byte layout
    PROVEN against tick ground truth (fail-closed probe caught a 20B-vs-24B
    misalignment first); census BUILD_PASS (119,038 valid 15m bars, 0
    non-positive-spread minutes, spread p50 0.3 pips; session/rollover
    spread census in census.json). Recorded OWNER_DIRECTIVE_SOURCE_AUTHORIZATION
    with TCU_RISK_DISCLOSED (site TCU posture unresolved with the vendor;
    owner explicitly delegated source choice + authorized machine downloads
    2026-09-23; no account/ToS/purchase; raw bytes machine-local, sha
    manifests committed). **Unblocks future FX cost-authority work: measured
    spread curves by session/rollover now exist sha-pinned on disk.**
  - Campaign (D2 owner-waived exploratory): 12 families × 4 configs = 48
    trials; engine v1 fixtures 7/7 (a pandas-3 datetime-unit bug broke
    force-flat in early code — caught by a hand fixture BEFORE any outcome).
    **5/48 positive after measured cost; 4/48 at 1.5× stress; 3/48 at 2.0×**;
    exactly 1 gate-eligible → frozen FXOS-04-C4 (Bollinger fade N=192 z=2.5,
    dev +1,203.6 pips PF 1.1445) → **FAILED its ONE preregistered holdout
    look** (2023-07..2025-12: −134.4 pips @1.0, −585.1 @1.5; 630 trades) →
    no rescue, terminal. Baselines same window: LONG_ALWAYS +286.7/−542.1,
    RANDOM_MATCHED −8,948.6 (engine cost honesty). Lesson: 15m EURUSD
    after-cost positives did not survive out-of-sample; dev edge here is
    selection luck across a 48-trial denominator.
  - Incidents: probe layout bug (pre-corpus, fail-closed); pandas-3 calendar
    bug (pre-outcome, fixture-caught); hand-typed digest corrected (188a2070,
    disclosed in candidates_frozen.json); A7-F4 verdict-text count corrected
    in terminal anchor.
  - Denominators: forex 48→96/96, program 283/286→331/334 (P-9 ledger
    stamp). EURUSD-DATA-QUALIFICATION-V1 verdict untouched.

- **PHASE-STRATEGY-V1 CLOSED → `PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE`**
  (2026-09-23, branch `orca/phase-strategy-v1-integration` terminal anchor
  af52f3582270bcc19634add3d88858e0c28959bf + closeout 0b25b230; owner GO
  `GO PHASE STRATEGY V1 SCORED EXECUTION` consumed at its own gate after A7
  prelaunch r2 AUTHORIZED; budget 4/15; observed 20/20 arm×cell = 52 raw
  computations; repro BYTE_MATCH 5/5 ×3; A7 terminal 0 HIGH/CRITICAL;
  S1 SEALED; no orders; registry TERMINAL, GO phrase DEAD):
  - All 4 eligible candidates failed G1–G7 on the merits: BTC_H1-UP +89,637
    (G3/G4/G5), BTC_H1-ACC +45,744 (G3/G5), BTC_H1-DOWN −44,486 (G1/G2/G6
    control-KILLED), **BTC_H4-DONCHIAN +177,692 (G3 7.2x-loss to TREND_LF,
    G5 0.5128, G6 KILLED — 30-bar block-shuffle gate placebo +190,392
    out-earns the candidate: the phase-break TIMING series carries no
    information)**. SPY_D1 closed zero-eligible (NO_ELIGIBLE_PROPOSAL).
    BTC buy-and-hold (+429k H1 / +814k H4) and TREND_LF dwarf every gated
    book; funding drag is a first-order cost on every BTC long book.
  - Durable assets: 2020–2026 BTC H1/H4 Vision panel + sha-pinned manifests
    (H4 manifest 3f1a6687…), code-owned PIT phase rules + label censuses,
    fill-class accounting engine (funding 8h signed, fold force-flat, tier
    exactness), frozen baseline/control definitions, G1–G9 evaluator.
  - Incidents recorded: registry row stale 10:21Z→close (Lead-session
    handover mid-P7; adopted-evidence receipt in closeout); prior-session
    close rows landed mixed inside AMIHUD-RETEST close commit 4fc3320c.
- **BTC-H4-CONTINUATION-V2 CLOSED → `BTC_H4_CONTINUATION_V2_NO_ELIGIBLE_PROPOSAL`**
  (2026-09-23 same-day successor; branch `orca/btc-h4-continuation-v2-integration`
  terminal c390375e, base af52f358; budget 0/2 — NO scored run, NO candidate
  PnL ever computed, GO phrase extinguished UNCONSUMED; A7 terminal
  CONFIRM_WITH_FINDINGS 0 blocking with independent engine recompute
  rel-err 0.0; S1 SEALED; no orders):
  - Forensic answer to the owner's question: F2/F4 losses of
    PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION are GROSS (−41,885/−43,504)
    — the arm pays breakout premiums in regimes without follow-through
    (win/loss collapses 3.78/2.45→0.95/0.66; MFE median 8.1%→3.1–3.8% with
    flat MAE); entries are mechanically identical across folds and NO
    measured at-entry PIT state separates the regimes (slope20 anti-sorted;
    SMA200 gate binds 0/86 entry bars). The owner's suspected min-hold
    culprit is measured INNOCENT (22 suppressed stops; immediate-stop
    counterfactual WORSE −3,785, F4 −13,066).
  - Durable assets: per-trade ledger + fold-comparison/min-hold-audit
    machinery over the frozen engine (reusable for any BTC_H4 arm
    forensics); third independent reproduction of the PSV1 BTC_H4 arm
    (day total: 3× byte-exact).
  - Reopening law: a materially NEW evidenced PIT observable (new data
    source = own data gate + PIT + license cycle) or an owner plan naming a
    changed mechanism; closing was judged NOT premature vs the strongest
    folklore alternative (breakout-strength gate) because any threshold now
    would be fold-PnL-informed (plan §2).

- **DATA-EDGE-UNLOCK-V1 CLOSED → `DATA_EDGE_UNLOCK_V1_PASS_D2_CONTROL_ONLY__BLOCKED_BROKER_COST_AUTHORITY__WAITING_COVERAGE`** (2026-09-17, branch `orca/data-edge-unlock-v1-integration` terminal 0f6cee90; owner directive 2026-09-17 "mở cycle nền tảng DATA-EDGE-UNLOCK-V1" — three independent data-authority lanes; budget 0/0, 0 scored cells, no GO phrase, S1 SEALED, no orders, denominators unchanged 257/260 P-9; **0 successors opened** — plan §7 exactness: Lane S needed PASS_DIRECT_SIGNAL_AUTHORITY, Lane F needed PASS, Lane C needed PASS_PROSPECTIVE_CONTROL_AUTHORITY):
  - **LANE S → PASS_D2_CONTROL_ONLY** (dossiers s_a3 PIT + s_a2 mechanism + s_a4 hostile critic): FTD PIT evidenced-conservative — settlement date is NEVER availability; FTD_CONSERVATIVE_AVAILABILITY@1 frozen then TIGHTENED to a binding **≥17-calendar-day guard** (A4 refuted the 16d advisory: 'a'-file end-of-month posting overshoots in 31-day months; A7 FND-1 corrected A4's leak share ~46%→~29% — the guard stands as exactly the right fix); F2 per-file posting timestamps / F5 historical CUSIP→entity mapping / F7 PIT denominator authority / N2 EDGAR acceptance datetimes all BLOCKED on network windows (403 class), with the ordered owner upgrade path **F7 > F5 > F2/N2**; M4 denominated forms infeasible, M5 event-conditioned books struck by construction (STOCKS-NG6 vol-state ancestry), M1/M2 FTD-level and M6 N-PORT crowding states usable as a D2 control plane only; direct historical scored use RETROSPECTIVE_ONLY. **NO STOCKS-NG7.**
  - **LANE F → BLOCKED_BROKER_COST_AUTHORITY** (third independent cost-authority census, NG6-F4/NG7-F4 class): zero account-bound bytes exist in the authorized evidence space — no broker credentials (env names census), no broker files on disk, IBKR gateway unauthenticated status probe timed out (PAUSED-probe standing NOT_RUN, no retry), OANDA/FXCM/Dukascopy account-gated; all ten components UNMEASURED (no stated-class declarations), stress multiplier 2.0 frozen PRIMARY pre-outcome; owner deliverables A/B/C recorded — clearest single action: **owner starts TWS/IB Gateway logged in (Read-Only API) once; the preregistered FX-majors probe (templates reused verbatim from the paused xauusd probe) then measures contractDetails + one full Wed-Sun Activity/Flex statement for the five TD majors**. **NO FOREX-NG8.**
  - **LANE C → WAITING_COVERAGE with committed resumable state** (new surface, NOT the pruned CNG4 tree): c_collection_contract@1 frozen pre-socket (adopting the CNG4-A3 conventions; 14-day cycle floors 303/336 + 152/168 STRICT, ≥4 cells/control/fold, ≥4 weekend days, STRESS-event bar else NOT_RUN_COVERAGE, outcome-independent stopping; 60-day CNG4 successor bar restated); keyless collectors ran 02:57:31Z→03:31:43Z then stopped cleanly via their SIGTERM handlers (workers=0; manifests finalized sha-chained 19/19); Coinbase STARTED_WITH_CHANNEL_DEGRADATION (l2_data rejected keyless again, verbatim); Kraken gen-2 gap_count 0 across 1.42M book rows live-verifying the measured per-product seq correction (gen-1's ~30k false-gap rows preserved verbatim); Deribit single-connection after the public/test keepalive fix; trades channel honestly excluded (keyless subscribe rejected, error 13778); 34min << 14-day floors honestly unmet; resume procedure committed. **NO CRYPTO-NG5 this cycle; when reopened it must be venue-native information only.**
  - Durable assets: the FTD/N-PORT PIT rulings + frozen guards; the ten-component broker cost checklist with frozen stress tier; the cross-venue collector machinery + contract + manifest chain (resumable at full floor); successor tests S1–S7 named for the stocks control plane.
  - Incidents: INC-DEU-1 (Lead registered the first terminal-audit task on a RECONSTRUCTED 40-hex sha — self-caught pre-dispatch, superseded by deu-a7-t2 on the measured head; validator's 40-hex check passed but bytes were wrong: short-SHA discipline applies to FULL shas too); a stale store row (deu-a7-cycle-audit) remains REGISTERED by the store's forward-only law; two short-SHA validator rejections at the registry update (measured before retry).
- **THREE-CYCLE PROGRAM CLOSED 0/9** (owner directive 2026-09-16:
  STOCKS-NG6 / FOREX-NG7 / CRYPTO-NG4 — three independent cycles, separate
  budgets/GOs/branches/ledgers; total max 9 scored cells; **0 consumed,
  0 survivors, all TERMINAL, all GO phrases died UNCONSUMED, S1 SEALED
  everywhere, no orders ever, PROSPECTIVE-SHADOW-V1 untouched throughout,
  FOREX-NG6R1 XAU probe untouched**):
  - **FOREX-NG7 → `FOREX_NG7_BLOCKED_SOURCE_OR_SCHEMA`** (branch
    `orca/forex-ng7-integration` terminal 3af2de8c; A7 plan r1 REFUSED →
    remediation a6a0da54 → r2 AUTHORIZED 0 blocking; M0 12/12 incl. G11
    dual-books fixture; P0 F1-F3/F5-F7 PASS — trigger census FEASIBLE
    721/802/674 per fold — then F4 decisive: NO citable financing band in
    the authorized evidence space (TD=vendor OHLC-only; FOREX-NG6 P0-F4
    precedent, second independent census) → the plan's preregistered
    dual-books clause fired; A7 terminal CONFIRM 9ccc8d7f 0 blocking.
    Reopening owner-only: broker-grade cost authority for TD majors).
  - **STOCKS-NG6 → `STOCKS_NG6_BLOCKED_DATA_OR_SELECTION`** (branch
    `orca/stocks-ng6-integration` terminal 77329ad8; A7 plan r1
    AUTHORIZED_WITH_FINDINGS 2 HIGH remediated; M0 11/11; P0 PASS 10/10
    AFTER a runtime-TLS crash + resumable-cache recovery (incident
    disclosed): 2,169 symbols 3.21M rows, bear-trap event population
    5,841/3,325 bookable, folds 1,136/1,495/694, band-C 13.8% — the
    family was FEASIBLE; D2 R0_VETO_ALL pre-score on the A4-BINDING
    event-conditional forms (vol_restricted_event_20d 0.260 / 60d 0.219 /
    dvol_shock −0.320 / reversal_5d 0.201 vs the immovable 0.20); A7
    terminal CONFIRM 204fc865 — independent rebuild reproduced all four
    rhos to 6 dp. Durable methodological asset: event-conditional rho for
    sparse event books).
  - **CRYPTO-NG4 → `CRYPTO_NG4_BLOCKED_DATA_OR_SELECTION`** (branch
    `orca/crypto-ng4-integration` terminal 535d802d; A7 plan r1 REFUSED →
    r2 AUTHORIZED 0 blocking + FLOOR AUDIT PASS; M0 28 tests; P0 PASS
    (panels/X1/funding/fold-span/SOL-RV24 all re-pinned); prospective
    collectors ran per the frozen contract ~2.4h then stopped cleanly at
    close (workers=0); D2 R0_VETO_ALL pre-score — 20 veto rows
    (rev24 per-leg 0.310/0.221, v16 close-displace-fade, v17proxy
    forms, pair spread-trend 0.207): the market-neutral pair book is
    measured to be a short-horizon reversal/displaced-fade composite —
    crypto ng proposals now 11/11 killed at the 0.20 bar; A7 terminal
    CONFIRM dd2ef319 (independent rebuild to 6 dp; caught + fixed the
    collector workers=0 gap pre-commit). Collection contract + collector
    machinery survive as reusable assets).
  - Program denominators UNCHANGED 257/260 (P-9). The falsification
    apparatus killed every proposal BEFORE any scored cell existed in all
    three cycles — 0/9 is the honest program result, cheaper than 9 cells
    of false hope.

## Sprint state (synced at the FREE-DATA-FRONTIER-V1R1 close, 2026-09-16)

- **FREE-DATA-FRONTIER-V1R1 CLOSED → `FREE_DATA_FRONTIER_V1R1_PASS_OFR_ACQUIRED`**
  (2026-09-16, branch `orca/free-data-frontier-v1r1-integration`, terminal
  66c12a2f, A7 fresh-context AUTHORIZED 0 HIGH/CRITICAL — cross-source
  authenticity 13/13 OFR-vs-NYFed exact date+value matches; budget 0/0, 0
  cells, S1 SEALED) — **append-only correction to terminal V1: the V1 OFR
  `BLOCKED_NETWORK` verdict was a FALSE blocker caused by the wrong
  endpoint.** V1 called `/v1/mnemonics/` and read the API-gateway 403
  "Missing Authentication Token" (route-not-mapped body, 43 bytes) as
  provider edge/TLS/IP blocking; the official routes
  `/v1/metadata/mnemonics/` and `/v1/series/full/?mnemonic=...` return 200
  on the same host. V1 artifacts remain byte-identical and TERMINAL; V1R1
  supersedes the claim only. Acquired: inventory 442 mnemonics + 5
  preregistered reference-rate series (SOFR 2111 rows 2018-04-02→
  2026-09-14; BGCR/TGCR 2111 from 2018-04-02; EFFR/OBFR 2648 from
  2016-03-01) — 6/6 raw re-hash ALL_MATCH, 67 targeted tests, OFR data is
  RETRIEVAL_TIME_ONLY/prospective (no per-row publication timestamps;
  "current vintage"), NOT authorized for historical scored joins.
  Denominators unchanged program 257/260 (P-9). Detail:
  `.worktrees/free-data-frontier-v1r1/integration/research/control/free_data_frontier_v1r1_run/terminal_correction.json`.

## Sprint state (synced at the FREE-DATA-FRONTIER-V1 close, 2026-09-16)

- **FREE-DATA-FRONTIER-V1 CLOSED → `FREE_DATA_FRONTIER_V1_PASS_PARTIAL`**
  (2026-09-16, branch `orca/free-data-frontier-v1-integration`, terminal
  4e49b3e7, A7 round-1 REFUSED (2 HIGH verdict-text defects, both A1
  authoring errors, zero data corruption) → remediation → round-2
  CONFIRM_WITH_FINDINGS 0 HIGH/CRITICAL; budget 0/0 — data-engineering
  cycle, 0 scored cells, S1 SEALED, no orders; PROSPECTIVE-SHADOW-V1
  untouched throughout) — the owner-directed free-source acquisition and
  authority census: 10 sources, 9 acquired. **PASS:** SEC FTD full served
  archive 434 zips (MEASURED span 2009-07→2026-08, two settlement
  cycles/month) + N-PORT 2026q2 one-quarter cap (QQQ accession
  0001067839-26-000024 → 102 holdings streamed from the 910 MB table,
  SPY measured-absent, GLD structural-absent non-1940-Act) + NY Fed 5
  reference rates (revisionIndicator MEASURED machine-served) + EIA route
  walk + 3 data probes + NWS 4-station preregistered set + USDA OCE 0826
  artifacts (esmis API measured 404, substitution disclosed) + 3/3 crypto
  public WS streams prospective-only (Coinbase 10,353 / Kraken Futures
  111,465 / Deribit 228 msgs; wire formats corrected by measurement). 8/8
  manifests ALL_MATCH from raw bytes (467 records, ~1.0 GiB outside Git);
  64 targeted tests; full suite 1971 passed + 7 failures all pre-existing
  at main. **BLOCKED:** OFR Short-Term Funding Monitor — HTTP 403 to every
  programmatic client incl. browser-UA (edge gate; no bypass per stop
  rules). PIT line: every record RETRIEVAL_TIME_ONLY (available_time NULL
  with evidence notes) — nothing here authorizes historical scored joins;
  "usable now" = prospective collection + engineering. Denominators
  unchanged program 257/260 (P-9). Detail:
  `.worktrees/free-data-frontier-v1/integration/research/control/free_data_frontier_v1_run/terminal_verdict_free_data_frontier_v1.json`.

## Sprint state (synced at the NG5/NG6 twin dispatch, 2026-09-16)

- **FOREX-NG6 CLOSED → `FOREX_NG6_BLOCKED_SOURCE_OR_COST`** (2026-09-16,
  branch `orca/forex-ng6-integration`, terminal 3b13d1da, A7 plan audit
  AUTHORIZED_WITH_FINDINGS 0 HIGH/CRITICAL 4 LOW carry + A7 terminal
  AUTHORIZED_WITH_FINDINGS 0 HIGH/CRITICAL, budget 0/3, 0 cells, 0
  proposals, GO died UNCONSUMED, S1 SEALED) — the XAUUSD real-yield / USD
  dislocation cycle (owner-directive dispatch, asset forex subtype
  metal_fx_quote; the program's FIRST M0 D2-methodology golden gate, G1-G10
  PASS 10/10). P0: price side F1-F3 PASS banked — TD XAU/USD 1day full
  depth 12,268 rows (1979-12-26 → 2026-09-16), 0 OHLC violations, weekend
  bars 155/154 non-flat measured, double-pull identical, canary 404 — then
  **F4 COST AUTHORITY fail-closed BLOCKED: TD is a vendor, not a broker —
  spread/commission/min-size/tick/swap/triple-swap/margin UNMEASURABLE
  from the entitled channel; zero citable band in the authorized evidence
  space (Q-8 refuses stated third-party pages); no GLD fallback in-cycle.**
  The outcome-blind lane's construction-B direction (mean-reversion of the
  macro-implied residual) stays preregistered and binding for a reopening.
  Durable assets: sha-pinned XAU/USD price authority + frozen clock
  convention + the shared M0 contract. REOPENING CONDITION: an owner
  broker-specific XAUUSD cost authority (measured venue evidence).
  Denominators unchanged forex 48/48, program 257/260 (P-9). Detail:
  `.worktrees/forex-ng6/integration/research/control/forex_ng6_run/p0/p0_census_verdict.json`.

- **STOCKS-NG5 IN FLIGHT → `PLANNED_NOT_STARTED` advanced to D2-pending**
  (2026-09-16, branch `orca/stocks-ng5-integration` at d7d21899, budget
  0/3) — the QQQ/SPY relative-breadth rotation (owner-directive dispatch):
  A7 plan audit round-1 AUTHORIZED_WITH_FINDINGS (0 HIGH/CRITICAL; 3
  MEDIUM remediated pre-registration at 6b0f12ef, 5 LOW fixed/carry); M0
  golden gate PASS 10/10 (a6964136; re-run 11/11 at 1bc2f19b after the
  owner-directive remediation — G4 dead assertion fixed + G4N negative
  control added, INC-NG5-3); P0 census F1-F9 PASS with one flagged
  gap (e553b4df — QQEW missing the 2008-11-28 half-day session, non-anchor;
  representation reconciled forward-only at 1bc2f19b: SKIP-AND-HOLD frozen
  as the single missing-close rule, superseding the P0 prior-close
  annotation; common window 2006-04-25..2026-09-15 =
  5,130 XNYS sessions, 5,129 with all four symbols — INC-NG5-3 prose
  correction, artifacts were always correct; ADV bands A measured 31B/44.6B;
  distributions censused 89/135/62/93 steps; D2 shadow inventory
  enumerated+frozen at 1bc2f19b: 13 shadow series + 1 template rule);
  D1 outcome-blind proposal freeze committed
  (d7d21899) bound to the frontier dossier sha a59af382: anchor L=13w z104
  (arms L4/L52), LEVEL neighbour (self-subsumption ≤ 0.98), inverted/
  delayed controls, R0-R6+K6 ordered kills, 11 controls. NEXT: D2
  non-scored (enumerated frozen shadow inventory, pooled |rho| ≤ 0.20
  immovable, cost ceiling) → S freeze → I → Z → A7 prelaunch → owner GO
  `GO STOCKS NG5 SCORED EXECUTION`. Denominators unchanged stocks 42/42,
  program 257/260 (P-9). PROSPECTIVE-SHADOW-V1 untouched throughout.

## Sprint state (synced at the CRYPTO-NG3 close, 2026-09-15)

- **CRYPTO-NG3 CLOSED → `CRYPTO_NG3_BLOCKED_DATA_OR_SELECTION`** (2026-09-15,
  branch `orca/crypto-ng3-integration`, terminal 9b1cccc3, A7 plan audit
  round-1 AUTHORIZED_WITH_FINDINGS 0 HIGH (fixed pre-registration) + A7
  terminal AUTHORIZED 0 HIGH/CRITICAL, budget 0/6, GO died UNCONSUMED,
  S1 SEALED) — the issuer-contract stablecoin net-flow census cycle:
  P0 census PASS C1-C11 (keyless finalized logs, 1.78M events, conservation
  366/366 EXACT, cross-transport byte-identity, Tron only_confirmed, folds
  146/109/111, minter netting measured with treasury honestly UNCLASSIFIED),
  2 outcome-blind proposals, then D2 VETO_ALL pre-score: **X3 — the new
  mandatory tape-fitted issuance proxy — reached 0.547/0.262: the tape alone
  explains the anchors**; X1 tape-liquidity relabel 0.402/0.426; X4 clock
  0.326/0.626; X5 nulls valid both. The 0.20 bar has now killed 10/10
  NG1/NG2/NG3 proposals. Census machinery survives as the standing probe.
  Denominators unchanged crypto 155/158, program 257/260 (P-9). Detail:
  `.worktrees/crypto-ng3/integration/research/control/crypto_ng3_run/terminal_verdict_crypto_ng3.json`.

- **FOREX-NG5 CLOSED → `FOREX_NG5_BLOCKED_DATA_OR_SELECTION`** (2026-09-15,
  branch `orca/forex-ng5-integration`, terminal 663a5ad6, A7 plan audit
  round-1 AUTHORIZED_WITH_FINDINGS 0 HIGH + A7 terminal AUTHORIZED 0
  HIGH/CRITICAL, budget 0/6, GO died UNCONSUMED, S1 SEALED) — the CFTC CoT
  positioning-state cycle: P0 census PASS A1-A7 (attempt-1 code-table defect
  corrected, both runs evidenced; codes not era-stable), 2 outcome-blind
  proposals, then D2 VETO_ALL pre-score: A4 killed by V1 clock-out-earn +
  V5 momentum 0.230 + S2 floor + E1 ceiling 18.07 bps; A5 by V5 0.353 + E1.
  V2 day-of-week survived here (0.036/0.029). The P-24 clock lesson fired a
  third time across planes; the E1 financing ceiling is the new weekly-hold
  killer. TD spot legs recovered byte-exact from the P-13 archive.
  Denominators unchanged forex 48/48, program 257/260 (P-9). Detail:
  `.worktrees/forex-ng5/integration/research/control/forex_ng5_run/terminal_verdict_forex_ng5.json`.

- **CRYPTO-NG3 OPENED → `PLANNED_NOT_STARTED` → P0 census running** (2026-09-15,
  registered; plan `plans/PLAN_crypto_ng3.md`) — issuer-contract stablecoin
  net-flow census (USDT Issue/Redeem, USDC Mint/Burn finalized logs, keyless
  transports) as float-state conditioning; plan audit round-1
  AUTHORIZED_WITH_FINDINGS (4 MEDIUM+1 LOW remediated pre-registration);
  C1-C11 gates pinned (Tron only_confirmed mandatory; full-window measured
  minter netting; X3 tape-fitted-issuance shadow).

- **STOCKS-NG4 CLOSED → `STOCKS_NG4_BLOCKED_SOURCE_OR_SCHEMA`** (2026-09-15,
  branch `orca/stocks-ng4-integration`, terminal 5fd712e, A7 plan-audit loop
  round-1 REFUSED → amendment A1 → round-2 AUTHORIZED_WITH_FINDINGS + A7
  terminal AUTHORIZED 0 HIGH/CRITICAL, budget 0/6, GO died UNCONSUMED,
  S1 SEALED) — the FINRA consolidated NMS daily off-exchange short-sale-volume
  direction (new information set, zero failure-registry ancestry) killed at
  P0 gate F1 AUTHORITY, the cycle's FIRST gate: operative FINRA Website ToU
  Restrictions (d)/(e)/(g) bar census-scale programmatic retrieval + database
  construction, (m) bars predictive-model use — no permissive data-specific
  terms locatable; the contrary reading (cdn bytes outside "FINRA Website")
  lands AMBIGUOUS = equally terminal (fail-closed). Anonymous free download is
  real; authorized research use is not. Zero bulk retrieval, zero adapter
  repair, zero cells. Reopening owner-only (FINRA data license or a different
  preregistered source). Denominators unchanged stocks 42/42, program 257/260
  (P-9). Detail:
  `.worktrees/stocks-ng4/integration/research/control/stocks_ng4_run/terminal_verdict_stocks_ng4.json`.

- **STOCKS-NG3 CLOSED → `STOCKS_NG3_BLOCKED_DATA_OR_SELECTION`** (2026-09-15,
  branch `orca/stocks-ng3-integration`, terminal 0d4b8352, A7 plan audit
  AUTHORIZED_WITH_FINDINGS 0 HIGH + A7 terminal AUTHORIZED 0 HIGH/CRITICAL,
  budget 0/6, GO died UNCONSUMED, S1 SEALED) — the earnings-surprise drift
  direction (consensus-free SUE, PEAD class, death-inclusive cohort) chosen by
  the owner-directed discovery mission as the highest-value surviving frontier,
  then killed by its own PREREGISTERED P0 census gate before any proposal lane:
  the EODHD "All World" entitlement (token alive, eod 200 frozen-transcript)
  does NOT serve the earnings-history channel (`/api/fundamentals` 403 Forbidden
  on 3/3 canaries, calendar 403, legacy /api/earnings 404). Reopening condition
  recorded in the terminal verdict + ledger row: an owner entitlement serving
  realized earnings history reopens the direction probe-first, with A7 LOW
  findings T3/T4 fixed in the standing census. Zero cells; denominators
  unchanged stocks 42/42, program 257/260 (P-9). PROSPECTIVE-SHADOW-V1 ran
  through the whole arc untouched (ACTIVE_LIGHT). Detail:
  `.worktrees/stocks-ng3/integration/research/control/stocks_ng3_run/terminal_verdict_stocks_ng3.json`.

## Sprint state (synced at the new-assets generation open, 2026-09-12)

- **COMMODITIES-NG1 CLOSED → `COMMODITIES_NG1_REJECT_ALL`** (2026-09-14, branch
  `orca/commodities-ng1-integration`, terminal 9abb88ae, A7 AUTHORIZED 0 HIGH/CRITICAL,
  reproduction 3/3 ALL_MATCH) — the first commodities-family cycle in program history on
  the platform v3 data plane: CFTC CoT positioning archives + EODHD commodity ETP legs
  (20 market-pairs, 11 fully-costed bookable); F1 coverage gate complete. D2 1/4 ELIGIBLE
  (A4-P2 crowd-carry 0.1096; 3 VETO by own price-only shadow). E NO SURVIVOR 3/3 KILL
  (NEUTRAL −2.0601 PF 0.568 n 249 / TAILWIDE −2.6360 PF 0.623 n 315 / WINDOWSHORT −4.1836
  PF 0.452 n 319): **the D1 falsification law fired — the bare release-clock control (no
  positioning input) out-earned every anchor after costs; the ARM3 window-short placebo
  also out-earned; kills overdetermined R1/R3/R4/R5/R6** — the edge belonged to the CoT
  release-calendar geometry, not positioning information. R 3/3 ALL_MATCH; T AUTHORIZED;
  budget 3/6 (3 unbooked, never reassigned); S1 SEALED. **the new-assets generation
  (rates/vol/commodities) is now fully closed: 3/3 REJECT_ALL, 12 cells scored,
  0 survivors, program 257/260** (P-9). Detail:
  `.worktrees/commodities-ng1/integration/research/control/commodities_ng1_run/terminal_report_comm_ng1.json`.

- **VOL-NG1 CLOSED → `VOL_NG1_REJECT_ALL`** (2026-09-14, branch
  `orca/vol-ng1-integration`, terminal 04da4374, A7 AUTHORIZED 0 HIGH/CRITICAL,
  reproduction 6/6 ALL_MATCH) — first vol-family cycle in program history on the
  platform v3 data plane: CBOE official VIX/VIX9D/VIX3M/VIX6M term structure +
  EODHD vol ETP legs (6 living, delisted TVIX+ZIV; XIV unprovable fail-closed);
  P0 floors all PASS (term-structure 15.69y, 2940 instants; Q-16 path-ladder
  cost contract). D2 2/4 ELIGIBLE (A4-P2 slope-acceleration 0.091; A5-P2
  premium-state asymmetry 0.070; 2 VETO as disguised vol-level). E NO SURVIVOR
  6/6 CELL_FAIL: A4 **cost-ceiling family kill fired at the R1/R5 binding site**
  — all arms <= 0 after the full Q-16 path ladder + expense (ANCHOR −55.83 PF
  0.292 n 424 / NEIGH-PERSIST −49.13 PF 0.310 n 92 / NEIGH-FAST −54.64 PF 0.312
  n 1780; R2 PASS via books_distinct per M-A binding); A5 dies R1/R3/R4/R5
  under the dominant decay path (ANCHOR −89.76 PF 0.484 n 204 / NEIGH-STRICT
  −84.99 PF 0.496 n 84 / NEIGH-FAST −72.13 PF 0.550 n 462; R2 PASS via frozen
  three-limb evaluator with the C8 implied-complex limitation verbatim; R6
  NOT_RUN honest gross <= 0). R 6/6 ALL_MATCH; T AUTHORIZED; budget 6/6; S1
  SEALED. **vol 6/6; program 254/257** (P-9). COMMODITIES-NG1 remains in flight
  at E scored (3 cells, 11 pairs). Detail:
  `.worktrees/vol-ng1/integration/research/control/vol_ng1_run/terminal_report_vol_ng1.json`.

- **RATES-NG1 CLOSED → `RATES_NG1_REJECT_ALL`** (2026-09-14, branch
  `orca/rates-ng1-integration`, terminal b14085e9, A7 AUTHORIZED 0 HIGH/CRITICAL,
  reproduction 3/3 ALL_MATCH) — first rates-family cycle in program history and the
  first scored close of the new-assets generation: Treasury.gov daily par-yield
  curve + FRED granted set (DGS10/DGS2/DFII10/DFII5/T10YIE/T5YIE/CPIAUCSL) +
  EODHD family-1 ETP legs (TLT/IEF/IEI/SHY); P0 floors all PASS. D2 1/4 ELIGIBLE
  (A5-P1 curvature-gated slope rho 0.139; auction lanes + A5-P2 VETO by
  momentum/calendar shadows). E NO SURVIVOR 3/3 KILL: NEUTRAL −11.92 PF 0.819
  (n 195); CONSERVATIVE −192.23 PF 0.0 (n=3, R3-barred); AGGRESSIVE +78.08
  PF 6.845 KILL(R2) — clock-only shadow +94.16 and placebo out-earn:
  **falsification-by-control #16**, the edge belonged to the release-calendar
  geometry, not curve-shape information. Budget 3/6; S1 SEALED. **rates 3/3;
  program 248/251** (P-9). Sibling cycles remain in flight at their own gates
  (VOL-NG1 E scored NO SURVIVOR, on its terminal path R then T; COMMODITIES-NG1
  GO consumed at its own gate, E scored next). Detail:
  `.worktrees/rates-ng1/integration/research/control/rates_ng1_run/terminal_report_rates_ng1.json`.

- **NEW-ASSETS GENERATION OPENED → RATES-NG1 / COMMODITIES-NG1 / VOL-NG1**
  (2026-09-12, owner directive verbatim: "mở cycle 3 assets mới suwt dụng
  những nguồn dữ liệu mới và hướng mới bạn đề xuất. Nguồn dữ liệu phải là
  miễn phí hoặc có trong gói EODO gì đó tôi mua."; plans
  `plans/PLAN_rates_ng1.md` / `plans/PLAN_commodities_ng1.md` /
  `plans/PLAN_vol_ng1.md`; registry 2026-09-12) — three FIRST-EVER asset
  families (rates / commodities / vol): same-asset ancestry inventories
  empty by construction. New information sources, all free-official or
  EODHD-entitled (Lead probe 2026-09-12): Treasury.gov daily par yield
  curve (live), CFTC CoT positioning archives (live — a positioning
  information type never used by any family), CBOE official VIX/VIX9D/
  VIX3M histories (live from 1990); tradeable legs via EODHD family-1 US
  ETP EOD (entitled: VXX/TLT/GLD fresh to 2026-09-11; indices .IND 404,
  futures .COMEX 404, Stooq curl JS-blocked → browser-class CANDIDATE
  only, never primary). Directions: rates = curve-shape + auction clocks
  (DGS10-level nominal-exposure shadow is the named kill-candidate — it
  killed two FX generations as a control); commodities = official
  positioning extremes/flows with mandatory price-only shadow;
  vol = term-structure slope carry + VRP states with mandatory
  index-only shadow and cost-path control (Q-16). Standing GO delegation
  continues (ng structure; A7 `*_S0_LAUNCH_AUTHORIZED` first). Program
  totals at open: 245 published / 248 observed, 0 survivors (P-9).

## Sprint state (synced at the ng1-generation open, 2026-09-11)

- **NG1 GENERATION OPENED → CRYPTO-NG1 / FOREX-NG1 / STOCKS-NG1** (2026-09-11)
  (`PLANNED_NOT_STARTED` at open, registry 2026-09-11; plans `plans/PLAN_crypto_ng1.md`
  / `plans/PLAN_forex_ng1.md` / `plans/PLAN_stocks_ng1.md`) — first asset cycles on
  the platform v3 data plane (CADS/AuthorityRegistry/QueryPlane `consume_via_plane`,
  per-asset adoption commits; frozen sets: S4 Binance H1 panels + OI / S2 FRED
  vintaged + S3 CPI archives + calendars / S1 Form-4 substrate + stream + EODHD
  corp-actions). New-mechanism lanes: crypto exogenous announcement +
  derivatives-calendar clocks; forex CPI print-deviation + release-order structure
  (vintaged GB/CA channel binding); stocks declared-plan (10b5-1) +
  amendment/revision observables. GO standing delegation to Lead per owner
  directive 2026-09-11 (RULES §7). All prior cycles TERMINAL (see closed-history
  bullets below; ledger authority P-9).

- **FOREX-NG1 CLOSED → `FOREX_NG1_REJECT_ALL`** (2026-09-11, branch
  `orca/forex-ng1-integration`, terminal e19c0a4, A7 AUTHORIZED 0 HIGH/CRITICAL,
  third independent recompute match; reproduction ALL_MATCH) — the ng1 generation's
  only scored cycle and first full pipeline on the platform v3 plane end-to-end.
  4/4 proposals ELIGIBLE at D2 (first non-empty ng1 selection); freeze d0992d1 with
  R1-R6 + cost contract frozen pre-implementation; GO consumed at own gate
  (A7 v3 AUTHORIZED after a 2-round authority-gate remediation arc + Lead under
  owner standing delegation). E 6/6 cells: A5-P1 −9.81/trade PF 0.827
  (R1/R3/R4/R5 FAIL; NOT a V7 re-clock); A4-P2 −6.63 PF 0.883 +
  **falsification-by-control #15** (CTL-DGS10LEVEL +4.13 out-earns — nominal-level
  exposure again); 0 survivors; budget 6/6; S1 SEALED. **forex 48/48;
  program 245/248** (P-9). Detail:
  `.worktrees/forex-ng1/integration/research/control/forex_ng1_run/terminal_report_ng1.json`.

- **FOREX-NG2 CLOSED → `FOREX_NG2_BLOCKED_DATA_OR_SELECTION`** (2026-09-11, terminal $N2T, A7 AUTHORIZED 0
  HIGH/CRITICAL) — opened under P-19; died at P0 by its own frozen floor (AU 26<30
  revision events; method-robust). 0 proposals / 0 cells / 0/6; GO died UNCONSUMED.
  Banked: GB bulk re-referencing artifact (first-print 8); CA first-print stream
  ALIVE (72/30 recent); successor FOREX-NG3 (CA-anchored) opens under P-19
  recursion. **forex 48/48; program 245/248** (P-9). Detail:
  `.worktrees/forex-ng2/integration/research/control/forex_ng2_run/terminal_report_ng2.json`.

- **FOREX-NG3 CLOSED → `FOREX_NG3_BLOCKED_DATA_OR_SELECTION`** (2026-09-11, terminal b3786a2, A7 AUTHORIZED 0 HIGH/CRITICAL, detached recompute value-identical) — P-19 recursion #2: CA-anchored revision-dynamics, census-informed floors all PASS at P0, then 4/4 D2 VETO pre-score (sign = release-order re-clock 0.2138; magnitude = commodity 1.0; differential = V7-re-clock CTL 1.0; transfer = day-of-week 0.8932). 0 cells / 0/6; GO died UNCONSUMED. **CA revision-dynamics frontier measured-closed; with ng1-ng3 the CPI-information family on the pinned plane is measured-exhausted — re-entry needs a new evidenced information source (owner data decision).** **forex 48/48; program 245/248** (P-9). Detail: `.worktrees/forex-ng3/integration/research/control/forex_ng3_run/terminal_report_ng3.json`.

- **CRYPTO-NG2 CLOSED → `CRYPTO_NG2_BLOCKED_DATA_OR_SELECTION`** (2026-09-12, terminal 71a29b1, A7 AUTHORIZED 0 HIGH/CRITICAL, byte-identical recompute) — owner new-sources cycle #1: BLS instants RECOVERED via controller-WebFetch (22 instants; Oct-2025 shutdown months excluded), funding grid 1094x3 verified; 4 blind proposals; D2 4/4 VETO vs dead-FOMC-form shadows (settlement forms clean on 29-panel, killed by dead-form envelope). 0 cells / 0/6; GO died UNCONSUMED. **crypto 155/158; program 245/248** (P-9). Detail: `.worktrees/crypto-ng2/integration/research/control/crypto_ng2_run/audits/a7_terminal_ng2.json`.

- **FOREX-NG4 CLOSED → `FOREX_NG4_BLOCKED_DATA_OR_SELECTION`** (2026-09-12, terminal a4ca659, A7v2 AUTHORIZED 0 HIGH/CRITICAL) — owner new-sources cycle #2: EURUSD pinned (TD entitlement), EZ HICP vintaged re-ingested (A7-F1 arc: as-of BLOCKED → wide-window PASS 37/16); 4 blind proposals; D2 4/4 VETO (Friday-v2-day geometry 0.89 + PPP 0.44 over-determined). 0 cells / 0/6; GO died UNCONSUMED. **EZ CPI frontier measured-closed. forex 48/48; program 245/248** (P-9). Detail: `.worktrees/forex-ng4/integration/research/control/forex_ng4_run/audits/a7_terminal_ng4_v2.json`.

- **STOCKS-NG2 CLOSED → `STOCKS_NG2_BLOCKED_DATA_OR_SELECTION`** (2026-09-12, terminal 4e483bb, A7 AUTHORIZED 0 HIGH/CRITICAL) — owner new-sources cycle #3: the ng1 amendment-reopening condition EXECUTED (EDGAR 4/A re-ingest 3,062 docs; 1,877 pairs — floor funded 9.4x); EODHD short-interests NOT ENTITLED (404; lane A5 dead). 2 blind proposals; D2 2/2 fail-closed: P1 16/17 vetoes CLEAN but v11 unmeasurable (zero-variance — structurally cannot express the shadow on this cohort); P2 16/17 CLEAN but own Q-6 fails (0 bookable 2025). **The amendment observables were NOT ancestry-dead — they died on data structure; that is the honest boundary of this substrate.** 0 cells / 0/6; GO died UNCONSUMED. **stocks 42/42; program 245/248** (P-9). Detail: `.worktrees/stocks-ng2/integration/research/control/stocks_ng2_run/audits/a7_terminal_ng2.json`.

- **CRYPTO-NG1 CLOSED → `CRYPTO_NG1_BLOCKED_DATA_OR_SELECTION`** (2026-09-11, branch
  `orca/crypto-ng1-integration`, terminal 0cfb9ac, A7 AUTHORIZED 0 HIGH/CRITICAL with
  detached recompute full-match) — first ng1-generation close, first crypto cycle on
  the platform v3 plane (S4 consume_via_plane 5/5 digests, shadow parity identical).
  P0: 8 FOMC instants PIT-evidenced; BLS blocked (CPI/NFP unavailable). D1: 4 blind
  proposals (FOMC-instant reaction x2, derivatives-calendar x2). D2: 4/4 VETO —
  0.4409 generic_dvol_shock / 0.3988 v16_close_displace_fade / 0.7483
  v17proxy_amihud (+Q-6 6<8) / 0.3904 v17_oi_level; selection empty; budget 0/6;
  GO died UNCONSUMED. Exogenous-clock crypto frontier measured-dead ancestry.
  **crypto 155/158; program 239/242** (P-9). Detail:
  `.worktrees/crypto-ng1/integration/research/control/crypto_ng1_run/terminal_report_ng1.json`.

- **STOCKS-NG1 CLOSED → `STOCKS_NG1_BLOCKED_DATA_OR_SELECTION`** (2026-09-11, branch
  `orca/stocks-ng1-integration`, terminal 65e447e, A7 AUTHORIZED 0 HIGH/CRITICAL,
  detached recompute exact, veto-shopping ruled out) — first stocks cycle on the
  platform v3 plane (S1 full re-pin 0 drift). Lane A5 (amendment/revision) P2-killed
  by frozen floor (0 docs 4/A in pinned substrate — coverage property). Lane A4:
  10b5-1 census floor MET (22,622 flagged txs); 2 blind proposals; D2 2/2 VETO
  (goodwill_bloat -0.3547 / -0.384, 15/15 measured, feasibility floors PASS).
  Selection empty; budget 0/6; GO died UNCONSUMED. Declared-intent frontier
  measured-dead ancestry. **stocks 42/42; program 239/242** (P-9). Detail:
  `.worktrees/stocks-ng1/integration/research/control/stocks_ng1_run/terminal_report_ng1.json`.

## Sprint state (synced at the FOREX-V9 close, 2026-09-10)

- **FOREX V9 CLOSED → `FOREX_FREE_V9_BLOCKED_DATA_OR_SELECTION`** (0 cells,
  budget 0/6; branch `orca/forex-free-v9-integration`, terminal 6e9f606,
  A7 prelaunch REFUSED 67229fa accepted) — the PPP-deviation frontier.
  P0: kill test PASSED (official-source staging GB/CA/AU + FRED vintaged
  GB/CA/AU/NZ/US self-contained; deterministic retrieval cross-cycle).
  D1: 4 outcome-blind proposals on wave 8b99412. D2: A4-P1 0.2599 / A4-P2
  0.4842 VETO; A5-P1/A5-P2 passed the A1 measurement (0.1062/0.0580) but
  **A7 prelaunch re-measured on the frozen daily-grid representation:
  0.3034/0.3119 vs V8-A5-P1-anchor — both VETO; the selection was invalid
  as measured and the cycle closed honestly at 0 cells**. Lessons: D2 rho
  must be measured on the runner's own decision grid, committed and
  reproducible; GB/CA current-vintage deviation recorded binding. Spot V1
  snapshot lost post-close; TD re-acquisition sample-proven. **forex
  42/42; program 236/239** (ledger authority, P-9). S1 SEALED. Detail:
  `.worktrees/forex-free-v9/integration/research/control/forex_free_v9_run/terminal_verdict_v9.json`.

- **FOREX V8 CLOSED → `FOREX_FREE_V8_REJECT_ALL`** (closed 2026-09-09, branch
  `orca/forex-free-v8-integration`, terminal 07de93c + closeout 4018884,
  A7 terminal `CONFIRM_FOREX_FREE_V8_REJECT_ALL` 0 HIGH/CRITICAL) — the
  real-rate frontier cycle under the owner FRED key. P0: lane 1
  (cross-economy market real-yield differentials) **BLOCKED_DATA measured**
  (US-only funding in the keyed catalog; owner PATH A ratified, keyless
  official sources DOCUMENTED_CANDIDATE for V9+). D2 lane kills: A4-P1
  0.3411 / A4-P2 0.3831 ancestry vetoes; A5-P2 blocked-data. E: FXFV8-A5-P1
  3/3 cells published — **falsification-by-control #14: the mandated
  DGS10-LEVEL control out-earns the anchor 4.01x same-sign (+19.77 vs
  +4.93/trade)** — nominal-yield-level exposure in new words; anchor
  whisper-positive (PF 1.0531) killed by its own control; DSR N=42
  0.341/0.406/0.540; reproduction ALL_MATCH (14/14 artifacts byte-identical,
  twin emission canon-identical); F2 strict ruling BOUND verdict-neutral.
  Budget 3/6, 3 slots dead; **forex 42/42; program 236/239** (ledger
  authority, P-9). S1 SEALED. Detail:
  `.worktrees/forex-free-v8/integration/research/control/forex_free_v8_run/terminal_verdict_v8.json`.

- **CRYPTO V17 / STOCKS V13**: V17 paused-maintenance (SHV1); V13
  bootstrapped through the hardened control plane (bulk ingest observed on
  the heavy lock).

- **CRYPTO V16 CLOSED → `V16_REJECT_ALL`** (closed 2026-09-08 07:45 VN,
  branch `orca/v16-integration`, terminal `46db31d` + canonical close
  `9d62d5c`) — the first aggTrades tick cycle and the first
  governance-native cycle (gate + lock + registry adopted and exercised
  end-to-end; per-period series persisted; two-key arc incl. a
  form-refused GO attempt correctly rejected). CLOSE-DISPLACE-FADE dies
  G2 PF razor (−0.0364) — plain negative; RUNPERSIST dies G1 with the
  control out-earning (corroborating shadow). D2 measured vetoes: 3
  proposals rho-blocked (0.2225/0.3385/0.3885); run_imb razor 0.1927.
  Budget 6/6; reproduction ALL_MATCH 60/60/1854; DSR NOT_RUN fail-closed
  for historical trials (prior Sharpes never persisted — prospective
  P-11 contract now in force). **aggTrades frontier measured-exhausted
  at the DAILY clock on BTC/ETH; sub-daily is the untested axis.**
  Crypto 155/158. Detail:
  `.worktrees/crypto/v16/integration/research/control/v16_run/terminal_report_v16.json`.

- **Program totals after all three closes (ledger authority, P-9):
  233 published / 236 observed, 0 survivors, S1 SEALED everywhere**
  (crypto 155/158, stocks 39/39, forex 39/39). Failure registry 55
  entries --verify PASS. No cycle is currently running; V17 (crypto),
  V12 (stocks) and V8 (forex) plans await owner dispatch.

- **FOREX V7 CLOSED → `FOREX_FREE_V7_REJECT_ALL`** (closed 2026-09-07
  20:32 VN, branch `orca/forex-free-v7-integration`, terminal `f59ea0c` +
  closeout `efb9601`) — the cross-economy spillover cycle. Both families
  mechanically negative AND control-killed: FXFV7-A4-P1 anchor −4.026/trade
  (PF 0.9088) with **falsification-by-control #12 — the +7d sham reproduces
  the anchor once the reaction window is closed before entry (F-A7-PL-1
  remediation): cross-economy conditioning carries no incremental
  information; together with V6 (own-economy, sham-NEGATIVE) the whole
  reaction-direction class is closed**. FXFV7-A6-P2 lead-lag −8.410/trade
  with the own-lag control out-earning the anchor (negative information).
  Budget 6/6; reproduction whole-file byte-identical (twin @ea905c8, ledger
  sha 1a82118b…); **first forex DSR from persisted per-period series
  (N=39, all ~0; P-11 gate delivering)**; A7 prelaunch arc R1 REFUSED
  (CRITICAL lookahead) → R3 AUTHORIZED → owner fresh GO; heavy lock waited
  out the V16 extraction (90 attempts). Forex 39/39. Detail:
  `.worktrees/forex-free-v7/integration/research/control/forex_free_v7_run/terminal_verdict_v7.json`.

- **STOCKS V11 CLOSED → `STOCKS_FREE_V11_REJECT_ALL`** (closed 2026-09-07
  22:49 VN, branch `orca/stocks-free-v11-integration@9d3a061`) — the
  filing-event/amendment-process cycle. The MANDATORY filing-event lane
  died measured at D2 (novelty 0.219/0.2192 vs momentum_63s); the single
  scored family SFV11-A5-H1 (amendment cadence-latency book)
  FALSIFIED_BY_CONTROL — anchor fails 7 gates and the shuffled-chain
  control reproduces its alpha 1.2042x same sign (**cluster #13**:
  cadence-latency spread is an exposure-shape artifact, not process
  information). A7 terminal CONFIRM 10/10 from bytes (0 HIGH/CRITICAL);
  reproduction ALL_MATCH byte-equal both files (twin @aac07d9); budget 3/6,
  3 slots dead forever; two-key arc incl. an A7 v1 REFUSED on an undisclosed
  push (INC-V11-4, resolved disclosed-owner-directed). Stocks 39/39. Detail:
  `.worktrees/stocks-free-v11/integration/research/control/stocks_free_v11_run/terminal_report.json`.

- **Program totals after the 2026-09-07 evening closes (superseded same
  night by V16): 227 published / 230 observed** — see the current totals
  above.

- **FOREX V6 CLOSED → `FOREX_FREE_V6_REJECT_ALL`** (closed 2026-09-07,
  branch `orca/forex-free-v6-integration@4d81dcd`) — the direction-conditioned
  calendar cycle. FXFV6-A4-P1 own-economy CPI reaction-direction drift is
  **the forex season's near-miss**: anchor fin-adj +824.37 @tier2.0
  (+0.963/trade, 208 trades) dying on FOUR robustness gates — PF margin
  −0.0021 (razor per P-2), GBPUSD concentration 0.4257, break-even 3.475bps,
  LOPO 3/4; k=10 neighbour out-earned (+1922.02, PF 1.1142) failing its own
  gates. **Sham control NEGATIVE (−910.40) while the anchor EARNS — release-
  DIRECTION conditioning carries genuine calendar information; V5's
  sham-shadow is counter-evidenced** (no falsification kill). FXFV6-A6-P2
  USD PC1-gated reversal mechanically dead (−3.299/trade; neighbour + placebo
  worse). Budget 6/6; reproduction whole-file byte-identical (twin @8a0fd01,
  ledger sha 8517ca36…); two-key P-8 legal. **A7 terminal NOT_RUN at close (disclosed in the ledger row) — ADDENDUM
  same day: it has since RUN → `CONFIRM_FOREX_FREE_V6_REJECT_ALL`
  (`0dead47`, 0 blocking, A7's own worktree re-run byte-identical; kernel debt
  F-A7-T-1 carried as owner item).** Forex 33/33; program 218/221 (ledger authority, P-9). S1
  sealed. Detail:
  `.worktrees/forex-free-v6/integration/research/control/forex_free_v6_run/terminal_verdict.json`.

- **CRYPTO V15 CLOSED → `V15_REJECT_ALL`** (closed 2026-09-07, branch
  `orca/v15-integration`, closeout `ad61fca` + terminal-line merge; code
  freeze `824190c`) — the archived-positioning-metrics cycle on
  data.binance.vision bulk daily metrics (keyless, sha256-pinned; staging
  PASS_UNDER_AMENDMENT_1: 4 global defect dates, ONG/ACE hole-heavy). 6/6
  cells published, 0 TECHABORT, reproduction ALL_MATCH 61,633 leaves. Both
  anchors fail rule order #1: ELITE-SIZE-ASYM −0.00173/day PF 0.897 with
  **falsification-by-control instance #11** (CTL-ELITELEVEL +0.00196
  PF 1.131 — asymmetry carries negative information vs plain elite level);
  TAKER-SAT −0.00380/day PF 0.842, control does not reproduce. A4's OI-axis
  pair novelty-blocked pre-score (rho 0.431 vs CTL-OISHARE, 0.253 vs
  OICYC-STOCH28 — the closed shadow measured). DSR/PBO NOT_RUN fail-closed
  (no per-period series persisted — driver-contract lesson for future
  cycles). Two-key P-8 proven again: fresh-context A7 REFUSED prelaunch on
  Q-LEAK_1 (fold-sign leak in q v1) → sanitized v2 + incident, exposure
  carried → AUTHORIZED → owner exact GO. The bulk-metrics frontier is
  measured-exhausted on this universe/window/cost regime pending an owner
  data decision. Crypto 149/152; program 212/215 (ledger authority, P-9).
  S1 sealed. Detail:
  `.worktrees/crypto/v15/integration/research/control/v15_run/terminal_report_v15.json`.

- **STOCKS V10 CLOSED → `STOCKS_FREE_V10_REJECT_ALL`** (closed 2026-09-06,
  branch `orca/stocks-free-v10-integration@bec559c`) — the filing-timing/
  revision cycle on the death-inclusive panel. Both families mechanical-REJECT:
  SFV10-A4-H1 own_z timing carries real directional content (raw-lag control
  opposite-sign; cohort_z neighbour same-sign) but dies PF margin −0.019 /
  ETF-share 0.8333 / SPY-excess 0/3 — sector-book drowning of a sub-cost
  signal (P-2 knife-edge class); SFV10-A5-H1 revision direction dead (−0.2047)
  with the severity neighbour equally dead → the revision axis is mined out.
  A7 terminal CONFIRM 8/8 (0 HIGH/CRITICAL); reproduction ALL_MATCH (twin
  @5b40d48, single by-design provenance leaf, INC-V10-1 adjudicated
  outcome-neutral); two-key P-8 proven end-to-end (A7 v1 REFUSED →
  remediation afad4b1 → v2 AUTHORIZED → owner exact GO). Budget 6/6; stocks
  36/36; program 206/209 (ledger authority, P-9). S1 sealed. Detail:
  `.worktrees/stocks-free-v10/integration/research/control/stocks_free_v10_run/terminal_report.json`.

- **FOREX V5 CLOSED → `FOREX_FREE_V5_REJECT_ALL`** (closed 2026-09-06, branch
  `orca/forex-free-v5-integration@3e8cacf`, terminal head 61100aa) — the
  inflation/real-rate axis cycle. P0 funded the per-print CPI axis on 4/8
  economies (GB 88 / CA 105 / AU 23 / NZ 30 evidenced in-S0 clocks; US OUT
  via archived BLS anti-bot 403 — owner hand-provision remains open; EMU/CH/
  JP release TIMING unevidenced) and closed the ALFRED vintage axis
  BLOCKED_DATA_AUTHORITY this host (license text unreachable — fail-closed;
  owner unblock options: FRED API key or alternate network path). P0c
  extended the announcement ledger 220→250 (cf1f01a7; CA 20/22, EMU 10/19
  via BoC/ECB PR bytes) and surfaced 9 EMU value-integrity findings —
  suspected MRO/DFR series mixing in the pinned base ledger, rows left
  UNEVIDENCED (owner debt, values never edited). D2 measured kills:
  A6-P2 ancestry rho 0.3257>0.20 (packet-consented); A4-P2 fold-infeasible;
  selection = FXFV5-A6-P1 alone. Scored REJECT: anchor FAIL 8 gates
  (gross-of-cost expectancy +0.712 only), sham-calendar neighbour
  out-earned the anchor (+2.744 vs −2.608) and died at the frozen primary
  stress gate (PF margin +0.0468 — falsification-by-control instance #10).
  Reproduction twin byte-identical whole-file; budget 3/3; two-key P-8
  re-proven. Denominators forex 27/27 (ledger: program 200/203 post-V5).
  S1 sealed. Detail:
  `.worktrees/forex-free-v5/integration/research/control/forex_free_v5_run/terminal_verdict.json`.

- **STOCKS V9 CLOSED → `STOCKS_FREE_V9_REJECT_ALL`** (synced by Lead,
  2026-09-06, branch `orca/stocks-free-v9-integration@3a61638`) — first
  cycle on the death-inclusive universe (evidenced Form-15 census,
  accession-union 3,395; dead-filer fundamentals extension; EODHD dead-name
  pulls — the probe-proven delisted capability finally exercised). Single
  eligible family SFV9-A4-H2 depletion-runway REJECT (PF 0.8095; control
  Cash/Assets opposite-sign weak-positive — informative shadow recorded,
  not rescuable); 5/6 proposals novelty-blocked vs the V8 shadow inventory;
  A1 refused post-hoc pooling re-adjudication. Budget 3/6; stocks 30/30;
  S1 sealed. Detail:
  `.worktrees/stocks-free-v9/integration/research/control/stocks_free_v9_run/terminal_report.json`.
- **CRYPTO V14 CLOSED → `V14_REJECT_ALL`** (2026-09-05, branch
  `orca/v14-integration@183554a`) — A7 terminal APPROVED 0_FAIL; reproduction
  ALL_MATCH at 874,334 leaf comparisons. PREMFADE-28D the near-miss of the
  cycle: +0.700 net, PF 1.360, MDD 11.6%, rejected on fold concentration
  0.5110 > 0.50 (marginal gate's third decisive kill). OICYC §1.1
  confirmatory entry closed with status bound in every cell (no exploratory
  recounting). First program DSR computed (0.00224 / 4.98e-07 over N=146 —
  effectively zero); PBO NOT_RUN fail-closed (<8 configs). Crypto 143/146.
  Detail: `.worktrees/crypto/v14/integration/research/control/v14_run/terminal_report_v14.json`.
- **FOREX V4 CLOSED → `FOREX_FREE_V4_REJECT_ALL`** (2026-09-05, branch
  `orca/forex-free-v4-integration@edba9bf`) — A7 terminal CONFIRM 8/8 from
  bytes; 6/6 cells, zero TECHABORT, twin ledger pinned 65725edc.
  Commodity-bloc risk-off whisper-positive (PF 1.0142, +0.675/trade) failing
  every robustness bar; family2 negative. Carry front door CLOSED at D2 by
  measured rho 0.997–1.000 vs both invalidated-ancestor variants. Two-key
  launch protocol proven in production (frozen phrase gate refused the
  19:48 shorthand; fresh exact-phrase GO 19:53). Inflation-axis classes
  DATA_BLOCKED_VALID → carried into PLAN_forex_v5.md. Forex 24/24.
- **STOCKS V8 CLOSED → `STOCKS_FREE_V8_REJECT_ALL`** (2026-09-05, branch
  `orca/stocks-free-v8-integration@9557f59`) — first cycle on the
  owner-entitled EODHD source (probe 6/6 PASS incl. delisted canaries);
  both families FALSIFIED_BY_CONTROL (cluster instances #8/#9); cohort
  honesty M-I1 honored (no delisted leg claimed). Stocks 27/27.
- Program totals after all four closes (ledger authority, P-9): **197
  published / 200 observed, 0 survivors, S1 SEALED everywhere** (crypto
  143/146, stocks 30/30, forex 24/24).

- **FOREX V3 CLOSED → V3R DATA_AUTHORITY_INVALIDATED** (synced by A1,
  2026-09-05, branch `orca/forex-free-v3r-integration@c356813`) — V3 locked
  FXFV3-A6-P1 (vol-gated policy-rate carry) provisionally pending evidenced
  PIT availability; the V3R remediation recomputed the six frozen cells
  under a pinned official announcement ledger (G4 twin ALL_MATCH; A7 PASS
  9/9, 0 blocking): anchor fails frozen STRESS_TIER_2.0 (PF 1.2825 fin-adj,
  expectancy +20.72 under honest availability), control arm refused by the
  frozen validator (mechanism sanity null). Verdict
  `FOREX_FREE_V3_DATA_AUTHORITY_INVALIDATED`; family2 in the forbidden
  inventory (economic observation recorded; front-door re-entry only via a
  future preregistered plan, standard ancestry rho gates). S1 never opened,
  stays SEALED. Denominators unchanged (forex 18/18; V3R published
  nothing). Detail:
  `.worktrees/forex-free-v3r/integration/research/control/forex_free_v3r_run/terminal_verdict.json`,
  S-1 entry in [SURVIVORS.md](SURVIVORS.md).

- **FOREX TERMINAL `FOREX_BLOCKED_SELECTION_INSUFFICIENT`** (synced by A1,
  2026-09-03, branch `forex@af707e3` + terminal closeout commit) — G10 spot-FX
  sprint closed honestly: F0 consumed the owner-authorized multi-asset core
  `8310366` (F0 PASS, 78 tests), F1 correctness engineering complete
  (FX0–FX6 PASS, 118-test forex suite; provider/instruments/loader/audit,
  sessions/DST/rollover clocks, conversion/rollover/accounting/execution,
  all synthetic-golden), F2 produced six outcome-blind proposals (pool
  `4b9ee91`) and A7 audited them 0 ELIGIBLE / 5 CONDITIONAL_ON_OWNER_DATA /
  1 INELIGIBLE. F3 never opened: no FX data authority exists (bid/ask 0/7
  pairs, rollover/swap, PIT rates all UNAVAILABLE_FAIL_CLOSED; owner did not
  authorize any provider). Scored cells 0, budget 0/6, denominators 0/0,
  S1 SEALED_UNTOUCHED, workers 0. The five conditional proposals are frozen
  future inputs; re-grading only after concrete data authority, outcome-blind.
  Evidence: `research/control/forex_run/terminal_report.json`,
  `research/audits/forex/f2_novelty/a7_f2_novelty_audit.json`.

- **V10P BLOCKED_PRELAUNCH** (synced by A1, 2026-08-27, branch
  `orca/v10-integration@86b7274`) — generic strategy→research adapter built and
  accepted (BG1–BG6, G15, F2 adopted-with-proof, G17 one measured authority,
  H08 12–20), family `A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL` frozen with 0/3
  scored cells consumed, W2=`d61a483` with detached R1b/R2b and 47/47 verified
  staged data. A7 prelaunch `NO_GO_BLOCKED_PRELAUNCH`: HIGH
  `G05_COVERAGE_SHORTFALL` (staged bars end 21.5 h before the preregistered
  window end; final daily close silently synthesized) + launch-window and
  measured-cap (final_cap=0) blockers. Entry conditions for the next thread:
  [CONTINUE.md](../../CONTINUE.md). Detail:
  `research/control/v10p_run/terminal_closeout_v10p.json`,
  `research/audits/v10p/a7_prelaunch_v10p.json`.
- **V9 REJECTED** — `V9_REJECT_ALL_MULTI_FAMILY` (5/5 frozen trials, all
  reproduced, terminal at `425843d`); V9H hardening
  `V9H_PASS_V10_AUTHORIZED` (14/14, `3241bd0`). Denominator 117.
- **V6P PASS** — engine/data/PIT/accounting validation sprint: 20/20 gates,
  A7 independent audit PASS (0 unresolved HIGH/CRITICAL), verdict
  `V6P_PASS_V6_AUTHORIZED`.
- **V6 REJECTED (family)** — `V6P_PASS_V6_CANDIDATE_FAIL`, 4/4 scored trials
  consumed, 0 candidates locked. Per-trial: CARRY-1D −5,679.96 PF 0.978
  mechanism_failure; CARRY-3D +2,076.03 PF 1.0116 edge_too_weak; CARRY-7D
  +20,580.87 PF 1.157 rejected on top-positive-fold concentration 51.66%>50%
  (MDD actually 8.84% PASS); REVERSE-3D −20,102.83 failed as designed
  (negative control). Terminal HEAD at closure `fbd2e9d` (clean tree).
  Authoritative detail + checksums:
  [v6-closure-addendum-20260825.md](evidence/v6-closure-addendum-20260825.md).
- **V7 PENDING** — 0/4 preregistered trials (`XSECT-FUND-PRICE-DIV-1D/3D/7D`
  normal + `REV-3D` reverse control) run or authorized. Status is strictly
  NOT_RUN / NOT_AUTHORIZED. Launch requires the V7P decision-surface repair
  and 18/18 prelaunch gates including A7 attestation (PLAN.md §7). Sprint V7P
  runs from bootstrap `dd026c0` across worktrees A2–A7.
- **S1 UNTOUCHED** — holdout never opened, observed, backfilled or analyzed;
  no paper/live trading; live money UNCHANGED_DISABLED.

## Destination

Produce a frozen, reproducible multi-asset research specification that is
credible enough for controlled signal-only/very-small testnet forward testing:
strategy rules, data contract, cost model, portfolio limits, and explicit
promotion/rejection evidence. Profitability is a hypothesis to test, not a
promise.

## Notes

- Domain: Binance USD-M perpetuals, ETH/BTC, liquid altcoins, and Binance TradFi
  perpetuals.
- Existing stack: NautilusTrader 1.230.0, 15-minute bars, funding/OI/mark-price
  data, shared risk manager, post-trade funding audit.
- Standing rules: no parameter tuning after seeing a fold; no forced transfer;
  no live-money execution; fail closed on incomplete data; preserve rejected
  symbols and negative results.
- Canonical repo notes: `NOTES.md` sections 13–16.
- Tracker: local Markdown because no issue tracker/connector is configured.

## Decisions so far

- [Current evidence baseline](tickets/current-evidence-baseline.md): ETH is the
  only candidate with a weak but repeatable signal; the three new baselines fail
  the shared-capital altcoin gate.
- [Funding is an accounting cost first](tickets/funding-accounting.md): funding
  is audited post-trade today; native intrarun settlement is required before
  margin-sensitive promotion.
- [Profitability gate and benchmark contract](tickets/define-profitability-gate.md):
  two-stage frozen screen/promotion gate; flat is the hard benchmark, while
  buy-and-hold and BTC-beta-neutral alpha are mandatory context checks. Every
  gate uses canonical after-cost PnL plus shared-capital replay.
- [Verify the next data snapshot and split contract](tickets/verify-data-snapshot.md):
  S0 is a clean one-year common crypto screen, but not untouched OOS; promotion
  requires a post-lock S1. The seven-symbol derivative overlay is now complete
  for S0 with a manifest and deterministic bar join.
- [Capture the missing ETH derivatives snapshot](tickets/capture-eth-derivatives-snapshot.md):
  ETH now has 90 funding, 2,880 OI and 2,880 mark rows in the same requested
  30-day interval as the altcoins; one trailing overlay row is excluded.

## Not yet specified

- Which asset-class buckets deserve separate frozen rules after the next data
  snapshot.
- The exact TradFi session/holiday/earnings data contract and whether its history
  is long enough for a credible out-of-sample test.

## Out of scope

- Live-money trading, automatic multi-strategy switching, leverage increases,
  and parameter grids in this map.
- Claiming a backtest is profitable without fees, slippage, funding and a
  portfolio-level test.
- Replacing the existing global default strategy before a separate promotion
  decision is closed.

## Frontier tickets

- [Capture the untouched future holdout](tickets/capture-untouched-holdout.md)
- [Decide the crowding and native-funding feature contract](tickets/crowding-funding-contract.md)

## Blocked tickets

- [Choose the ETH forward-test candidate](tickets/choose-eth-candidate.md) — blocked by the future holdout and crowding/funding contract.
- [Choose altcoin asset-class candidates](tickets/choose-altcoin-candidates.md) — blocked by the future holdout and crowding/funding contract.
- [Define the TradFi perpetual research contract](tickets/tradfi-research-contract.md) — blocked by the future holdout.
- [Set shared-capital and portfolio promotion rules](tickets/portfolio-promotion-gate.md) — blocked by candidate decisions.
- [Approve the controlled forward-test handoff](tickets/forward-test-handoff.md) — blocked by portfolio and execution decisions.
## CRYPTO-V17 (CLOSED 2026-09-10) — the intraday microstructure frontier, closed at the prelaunch gate

- Verdict `V17_BLOCKED_DATA_OR_SELECTION`: zero scored cells, budget 0/6, S1 SEALED. Both
  mandatory-lane-1 proposals (intraday BTC/ETH) died by their own frozen rules — SILRES
  rule-4 coverage (duty 0.81%/0.99% vs [5%,60%]) and WKNDLIQ G12 novelty (0.5628 corrected
  after a measurement-defect catch); the cross-lane survivors ATTN-PHASE and OICASCADE then
  died at A7 prelaunch v3 (G1 measured dead via the cycle's own smoke pipeline; OICASCADE
  also K1 control-out-earns + K2 fold-negative-majority). Owner decision A closed on the
  frozen-rule kills with smoke exposure disclosed.
- Governance arc: A7 refused three times, each refusal produced a real fix (rule
  enforcement wired fail-closed; a D2 measurement defect corrected; the endpoint
  alignment hints) — the first cycle where every refusal was a measurement or enforcement
  defect, never a threshold argument. INC-V17-1 (commit message vs content) recorded.
- Durable assets: the UTC-H1 panel (1.391B rows, 3 symbols, sha-pinned), the
  family-agnostic driver with fail-closed frozen-rule enforcement, the warmup-extended
  per-symbol-distinct OI authority (1,452-file manifest). Lane 1 re-opens only via a
  future owner plan. Registry 61 entries. Denominators unchanged 155/158, 233/236.
- STOCKS-FREE-V13 (2026-09-10): REJECT_ALL (mechanical) — A6-P1 dividend-transition folds 1/3; Form-4 XML substrate 345,150 sha-pinned; incidents INC-V13-1..16; A7 terminal 0ce70f3.

## FOREX-INTRA-BIDASK-V1 (CLOSED 2026-09-17) — intraday bid/ask foundation, blocked at transport

- Verdict `FOREX_INTRA_BIDASK_V1_BLOCKED_TRANSPORT`: zero scored cells, budget 0/0,
  no GO phrase ever registered, S1 SEALED, no orders, no PnL anywhere, denominators
  unchanged 257/260 (P-9). Owner directive 2026-09-17: a Forex direction independent
  of OANDA/MT5 that never assumes swap=0 — intraday bid/ask research with every
  position force-closed before rollover; Dukascopy Historical Data as the priority
  source. Identity is deliberately NOT FOREX-NG8 (that name is burned by
  DATA-EDGE-UNLOCK-V1 Lane-F law and remains burned).
- Chain: plan 79a21cc1 → A7 plan audit r1 AUTHORIZED_WITH_FINDINGS 0 HIGH/CRITICAL
  (4 MEDIUM + 3 LOW, all remediated pre-registration) 74d0632c / 1a9936f5 →
  registry bootstrap 094bbded → lane A2 (source/license/transport) d06ebce4 →
  integration pick b31bb1c0 → A7 terminal CONFIRM_WITH_FINDINGS 0 HIGH/CRITICAL
  8c4a563d → terminal 558b366c (worktree
  `.worktrees/forex-intra-bidask-v1/integration`, branch `orca/fibv1-integration`).
- Blockers: B1 transport — the official Dukascopy surface is unreachable from this
  environment (local resolver 127.0.0.1 for *.dukascopy.com; SNI/Host-keyed TLS
  resets regardless of destination IP; DoH-verified authentic origins reset;
  36 connection failures; zero circumvention attempted). B2 license gate
  UNAVAILABLE_FAIL_CLOSED — a co-blocker downstream of B1: Dukascopy licensing and
  data quality are UNMEASURED; nothing about the source was adjudicated. Waves
  A3/A4/A5 + the D2 battery were MOOT (input never existed) and stayed undispatched
  (STOCKS-NG4 "F2-F8 never dispatched" precedent).
- Durable assets: the frozen canary manifest + etiquette + decoder
  (`research/control/forex_intra_bidask_v1/lane-a2/` on the integration branch) are
  reusable as-is; the plan's preregistered contract (rollover-flat at T−300s,
  fill sides, cost stresses 1.0/1.5/2.0, ancestry bar 0.20) is frozen text that any
  reopening inherits unchanged.
- Reopening: owner provides a network path where *.dukascopy.com is reachable,
  then lane A2 re-runs from the frozen manifest; both blockers re-arm and are
  decided by evidence, not assumption. Successor door CLOSED — no successor plan.

## FX-FUTURES-FRONTIER-V1 (CLOSED 2026-09-17) — CME Micro FX futures frontier, blocked at transport (second estate)

- Verdict `FX_FUTURES_FRONTIER_V1_BLOCKED_TRANSPORT`: zero scored cells, budget 0/0,
  no GO phrase ever registered, S1 SEALED, no orders, no PnL anywhere, denominators
  unchanged 257/260 (P-9). Owner directive 2026-09-17: evaluate CME Micro FX futures
  (M6E/M6B/M6A/MCD/MJY candidates) as an independent FX trading vehicle replacing
  spot-FX/CFD — carry expressed in futures basis/roll, never a CFD swap line.
  FOREX-INTRA-BIDASK-V1 untouched; FOREX-NG8 remains burned.
- Chain: plan 994ff1f8 → A7 plan r1 REFUSED 2 HIGH (floors unpinned F-1; rule-11
  CONCEDED-binding-attack leak F-2) → remediated 5fd2cf4c → A7 r2 fresh-context
  AUTHORIZED_WITH_FINDINGS 0 HIGH/CRITICAL (all 8 r1 CLOSED) 1ff55598 → remediation
  r2 06af8ba5 → registry bootstrap 8230fa34 → lane A2 cee59971 → integration pick
  aea11aed → A7 terminal CONFIRM_WITH_FINDINGS 0 HIGH/CRITICAL 6296bff9 → terminal
  7decfce3 (worktree `.worktrees/fx-futures-frontier-v1/integration`, branch
  `orca/fxf-f-integration`).
- Blockers: B1 transport — the entire official CME estate unreachable (LAN resolver
  192.168.0.1 sinkholes www.cmegroup.com to 127.0.0.1/::1; SNI-keyed in-path reset
  proven at the DoH-authentic Akamai IP by same-IP different-SNI certificate
  delivery; apex TLS drops; ftp TCP dropped; neutral controls 200 OK; 0 content
  bytes; zero circumvention). B2 license gate UNAVAILABLE_FAIL_CLOSED — co-blocker
  downstream of B1: CME licensing and data quality are UNMEASURED; nothing about
  the exchange or Micro FX futures as an instrument was adjudicated. Waves
  fxf-a3..a6 + D2 MOOT undispatched (STOCKS-NG4 F2-F8 precedent).
- SYSTEMIC: this is the SECOND independent estate blocked with SNI-keyed in-path
  filter evidence in the same environment (FOREX-INTRA-BIDASK-V1: Dukascopy; this
  cycle: CME). ONE owner action — a network path without these domain filters —
  re-opens both cycles' lanes from their FROZEN manifests, plans unchanged.
- Durable assets: frozen canary manifest + census grid + fetch driver + identity-
  pack templates (`research/control/fx_futures_frontier_v1/lane-a2/` on the
  integration branch) reusable as-is; the plan's preregistered contract (actual
  dated contracts only, PIT roll law with pre-fetch K freeze, complete cost stack
  with UNKNOWN-commission posture, stress ladder observed/1.5x/2.0x, capital
  feasibility 1k/10k/300k frozen definition, 12 exact verdicts) is frozen text any
  reopening inherits unchanged.
- Reopening: owner provides an unfiltered network path to *.cmegroup.com (and
  *.dukascopy.com for the predecessor), then lane A2 re-runs from the frozen
  manifest; both blockers re-arm and are decided by evidence, not assumption.
  Successor door CLOSED — no successor plan.

## JEV-REGIME-ROUTER-V2 (CLOSED 2026-09-23, `JEV_NO_INCREMENTAL_VALUE`)

- Owner-instruction successor to JEV-REGIME-ROUTER-V1 (V1 closed
  `TECHABORT_OWNER_STOP_DESIGN_REVISION` at 990/8,567 bulk states after
  persisted-regime 990/990 TRANSITION_UNKNOWN — failure class `UNKNOWN_COLLAPSE`;
  partial outcome-observed, no PnL ever).
- V2 design (forced-choice 4-phase provider — no model abstention; code-owned
  UNKNOWN via confidence/margin/hierarchy-contradiction/staleness; named
  semantic state; structure/direction/phase hierarchy in ONE systemOne call;
  pin jev-1.13.0 VERIFIED_LIVE) FIXED the collapse: 13,315/13,315 historical
  decisions across BTC_H1/BTC_H4/SPY_D1, effUNKNOWN 0.43/0.27/0.29, real
  regime switching, 0.16% fail-closed errors, budget used-only 58.05M input
  tokens (< formula cap 58.17M; 85% checkpoint disclosed mid-run).
- Scored verdict (18/18 cells, one atomic run under GO authority, repro 54/54
  byte-identical, A7 terminal authorized 0 HIGH/CRITICAL): JEV_ONLY
  net-negative on ALL cells; loses to ALWAYS_ON_MEAN_REVERSION everywhere
  (−35.0k/−31.4k/−50.7k) and to RANDOM everywhere (random-null Q-11 invalid,
  disclosed); DETERMINISTIC+JEV_CONFIRM beats the deterministic router on BTC
  only by trading less, both deeply negative; switching-cost attrition
  decisive (monotonic 1.0/1.5/2.0x degradation); JEV fold nets negative 11/12.
  SPY ALWAYS_ON_TREND +19,813 is a BASELINE, concentration 0.69 > 0.50 kill,
  not promoted.
- Durable assets: the whole forced-choice + code-owned-UNKNOWN + semantic-state
  apparatus (tests 127 py + 47 ts), producer-digest/prompt-digest cache laws,
  strict sequential replay + collapse stop-law, per-cell bulk manifests, and
  the honest canary/preview pipeline — reusable for any future LLM-classifier
  cycle at near-zero marginal engineering cost.
- Reopening: an LLM-classifier cycle may reopen only with a CHANGED mechanism
  class (see Phase-4 successor proposals in the terminal report), never by
  prompt/threshold iteration on this corpus. EURUSD door: blocked on owner
  source/license decision (packet in EURUSD-DATA-QUALIFICATION-V1).

## REGIME-STRATEGY-MAPPING-V1 (CLOSED 2026-09-23, `NO_REGIME_STRATEGY_INCREMENTAL_VALUE`)

- Owner-instructed successor to JEV-REGIME-ROUTER-V2: regime-SPECIALIST
  mapping + switching-cost attrition study on the frozen V2 cached corpus.
  ZERO Jev calls (timeline rebuilt from cached decisions, verified
  90/31/34 switches); V2 byte-untouched at 0c277a94; S1 sealed.
- Orchestration: 5 parallel lanes (A3 census, A5 engine audit, A4
  outcome-blind specialist architect, A6 controls, A2 attribution)
  integrated A3→A5→A4→A6→A2; A7 pre-outcome took 3 rounds (F1 outer-thin
  gate missing; N1 fold-index off-by-one; then AUTHORIZED).
- Findings: BTC loss is strategy-native gross, SPY loss 94% cost churn
  (Tuesday-staleness artifact); only BTC_H1 ACC/UP/DOWN have sample
  (floors 20/3/100); the anti-churn turnover law saves +16–33k per cell
  on Jev-dependent arms but cannot make them net-positive; specialist
  router C loses (−49.7k BTC_H1) though it beats always-on-MR and the V2
  mapping; sparse veto D is the best Jev-aware arm and still negative;
  owner's relaxed-floor comparison (10/2/50, frozen pre-outcome): SPY
  +2,529 at 1.0x dies at 1.5x — thin-sample mirage, not value.
- Incidents (all disclosed, artifacts preserved): run-1 direction-dispatch
  bug voided C*/F* (remediation run 2 under one final routing law);
  D/E superseded; 45 observed total; reproduction 69/69 MATCH; A7 terminal
  authorized with 0 HIGH/CRITICAL.
- Durable assets: regime-timeline rebuild law (fail-closed vs V2 stats),
  specialist registry engine (equivalence-proven vs V2), turnover law
  (buffer/no-op/min-hold deferral), sanitized dry-run + GO quarantine
  pattern, floor-sensitivity preregistration pattern, census/no-pooling
  law.
- Reopening: a routing/specialist cycle on this corpus may not retry the
  same mapping class with new parameters; any Jev-classifier reuse needs a
  changed mechanism per the V2 reopening law. SPY +19,813 remains a
  concentration-killed baseline, never evidence.

## STOCKS-AMIHUD-V1 (CLOSED 2026-09-23, `STOCKS_AMIHUD_V1_REJECT_ALL`) — first Amihud on stocks; the PnL was a ghost ticker

- Owner-directed cycle (2026-09-23): Amihud (2002) illiquidity long-only on
  US listed-venue common stocks, folds CY2019 | CY2020 | CY2021-22, 3 cells
  (ILLIQ21/ILLIQ63/REVERSAL5). Plan A7-audited (REFUSED→remediate→AUTHORIZED);
  D2 skipped by owner amendment A3 (R0_NOT_RUN); prelaunch A7 took 3 rounds
  (round 2 caught a real annual_split KeyError with its own repro); owner GO
  fresh+exact at gate; 3/3 cells under heavy lock.
- Verdict: REJECT_ALL. Anchor/neighbour fail MDD (59.25%/56.79% vs 15%) and
  fold-concentration (50.1%/50.0% vs 50%, razor). The PF 54/56 "edge" is ONE
  non-tradable print: 99.7% of net = ticker HTV, for which EODHD serves
  2017-2022 bars although Hearst-Argyle Television went private in 2009
  (2019-12-06: 1.36→13,050 on volume 10). Reversal control negative — the
  anchor is not a reversal effect, it is a data-identity artifact.
- Identity-failure census (terminal_forensics.json): C1 ghost series
  (HTV/NLG); C2 same-security-two-tickers (BYON/OSTK same ISIN; 249
  collision groups); C3 shared-death-date batches (76@2018-01-30,
  38@2022-03-02); C4 reverse-split adjusted_close NOT smoothed (408-name
  extreme-print class — the forward-split F3a fixture was never tested on
  reverse splits); C5 zero-volume bars carrying prices; C6 11,345 no-ISIN
  codes; C7 vendor test tickers (NTEST-T).
- Owner waivers at close (recorded verbatim): reproduction NOT_RUN
  ('bỏ reproduction đi'), A7 terminal NOT_RUN ('không dispatch A7 terminal
  gì hết') — verdict is the A1's, backed by frozen gates + forensics.
- Successor: STOCKS-AMIHUD-RETEST-V1 (owner directive, retrospective
  retest with identity/execution gates). Denominators: stocks 45/45,
  program 260/263 (P-9). Detail:
  `.worktrees/stocks-amihud-v1/integration/research/control/stocks_amihud_v1/scored/terminal_verdict.json`.

## STOCKS-AMIHUD-RETEST-V1 (CLOSED 2026-09-23, `STOCKS_AMIHUD_RETEST_V1_REJECT_ALL`) — identity/execution remediation retest: the artifact is gone, and so is the "edge"

- Owner-directed retrospective retest (2026-09-23 directive) after the
  predecessor's PnL proved to be a ghost-ticker print. Launch under the
  owner standing directive + A7 plan adjudication SUBSTITUTION_VALID_
  AUTO_RUN_ALLOWED (B1..B8) + A7 prelaunch AUTHORIZED — the typed GO was
  never used (owner-reserved). Reproduction ALL_MATCH_VALUE_IDENTICAL
  (provenance-leaf-only); A7 terminal CONFIRM (recompute exact).
- Remediation: 645 of 8,216 staged codes quarantined with reason codes
  (499 ghosts incl. HTV/NLG; 52 vendor-test; 97 same-ISIN duplicates —
  BYON/OSTK are replicas of BBBY's series); B1 both-direction
  extreme-print law (798 bars excluded+unfillable); B2 zero-volume bars
  unfillable (452,333); X1 fill feasibility (15% of fill-bar DV; 68
  unfillable orders blocked; 65 proxy-marked exits disclosed).
- Verdict: REJECT_ALL three cells. 2019 thin (+$92k, PF 1.175), 2020
  +$402k (PF 1.465), 2021-22 -$959k (PF 0.646) — no repetition; MDD
  62/57/54% vs 15%; SPY-excess 1/3; stress negative; drop-one dead. The
  MATCHED-CHARACTERISTIC book beats the anchor in 2019 (+$170k vs +$92k)
  and 2020 (+$1,822k vs +$402k): no measurable Amihud illiquidity premium
  on this cohort/window under band costs. Residual single-symbol
  dependence: max |net| share 0.82% (was HTV 99.7%).
- Durable assets: the ticker≠identity quarantine law + census, the
  both-direction corporate-action fixture law, the fill-feasibility
  execution law — the data-plane template for future EODHD single-name
  cycles. Denominators: stocks 48/48, program 263/266 (P-9). Detail:
  `.worktrees/stocks-amihud-retest-v1/integration/research/control/
  stocks_amihud_retest_v1/scored/terminal_verdict.json`.

## ILLIQ-REG-V1 (CLOSED 2026-09-24, `ILLIQ_REG_V1_GATE_FALSIFIED`) — preregistered regime gate on the ILLIQ anchor, falsified by its own bar

- Owner-dispatched bootstrap (2026-09-24) → falsification-first cycle on the
  V11-reject `A8-V11-ILLIQ-AMIHUD` anchor under standing
  OUTCOME_EXPOSED_ANCESTRY (confirmation weight 0 on all history;
  forward/shadow only confirmatory surface). Two-variable gate frozen from
  the PREREG draft (V1 S90 rotation p70/p90 hysteresis; V2 BTC rvol30 p10
  floor ×0.90; GATED = V1 AND V2, Monday 00Z PIT, weekly apply), overlay via
  an engine-native skip suppressor on the frozen CHR3F plugin subclass —
  engine `c97283e0` untouched, CHR3F tree read-only.
- Staged budget phase-1-only (registry cap 4): 4/4 diagnostic cells on S0R
  2024-08-22..2025-08-21 under heavy lock, funding-wired `scan_2026_a` (the
  B2 law), 4-label invariant enforced on every row. Owner GO consumed at its
  own gate after A7 prelaunch AUTHORIZED 0 blocking (an earlier
  misclassification of that GO as "early" was retracted & corrected —
  recorded incident).
- Verdict **FALSIFIED** per the preregistered bar: gated ANCHOR baseline net
  −0.345789 (bar ≥ −0.2947 FAIL, margin −0.0511; improvement 38.6% < 50%) /
  MDD 0.419178 (bar ≤ 0.4372 PASS) — both required. Stress ×1.5/×2.0
  −0.3498/−0.3537 (price-driven); INV-gated +0.3297 coherent sign flip.
  Reproduction detached twin @31985732: 8/8 files byte-identical. A7
  terminal CONFIRM 0 blocking (independent recompute).
- Durable assets: the gate module + wiring law + 4-label invariant (M0 39/39),
  the subprocess-isolation pattern for v11/root package collision, the
  falsification-first template (negative terminal executed as designed, no
  tuning loop, no gate variants). Denominators: 4/4 diag cells, program
  303/306 (P-9). Detail:
  `.worktrees/illiq-reg-v1/integration/research/control/illiq_reg_v1/
  terminal_report.md`.

## ERP1-TRACKA-COHORT-1 (TERMINAL 2026-09-26, REJECT_ALL)

- Track A cohort 1 of ECONOMIC-ROBUSTNESS-PROGRAM-V1: first cycle to run the
  program's full falsification-first arc (council -> pre-PnL battery -> frozen
  scored cells -> repro twin -> A7 terminal -> two-half close).
- Decisive finding: the RANGEFADE/RANGEEXP "edge" across EURUSD/GBPUSD/USDJPY
  ancestry AND both fresh pairs (AUDUSD +3,207 / USDCAD +5,030 pips for the
  leaky twin, all 8 gates) was the whole-day mode lookahead (incident
  `tracka_cohort1/INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25.md`); the PIT-clean
  law has PF 1.03-1.05 and dies at 1.5x cost. M3 (quote-state gate) died at
  the F-5 cost ceiling pre-PnL; M2 (cross-pair gate) died at the D2 novelty
  veto pre-PnL. Holdout 2026-H1 on AUDUSD/USDCAD remains unread.
- Owner-directed diagnostic (branch orca/erp1-tracka-cohort-1-diag): the
  shadow's actual daemon-law (partial-range percentile) emulated on
  EURUSD/GBPUSD history shows no edge (EURUSD PF 1.06 @1.0x decaying to ~0 at
  2.0x; GBPUSD negative at every tier) — DIAGNOSTIC_OUTCOME_EXPOSED labels.
- Control plane: research/control/ERP1-TRACKA-COHORT-1/ (freeze+errata, 42-row
  ledger, censuses, audits A7 prelaunch+terminal, CYCLE_VERDICT with errata
  bundle); branch orca/erp1-tracka-cohort-1-integration terminal fa93b807.

## ERP1-TRACKB-COHORT-1 (TERMINAL 2026-09-26, REJECT_ALL) — BTCUSDT spot–perp delta-neutral carry: the funding axis is closed by identity, at zero cells

- Owner opened Track B (BTCUSDT spot–perp delta-neutral basis/carry) under
  ECONOMIC-ROBUSTNESS-PROGRAM-V1 with gate-by-gate authority; GO-1 consumed
  verbatim at its gate (`GO ERP1 TRACKB COHORT 1 REGISTER AND FREEZE`).
- Council (4 outcome-blind lanes + A7 plan-audit) admitted exactly ONE of
  nine mechanism classes: funding-level-gated low-turnover cash-and-carry
  with a breakeven-horizon entry law (enter only when trailing expected
  carry over the hold ≥ the ×2.0 all-in bill ≈45–60 bps; measured anchors:
  two-leg taker RT 20–25 bps; mean funding 11.798%/yr but only 1.11 bps/day
  in-downtrend; 24.7% in-downtrend settlements negative).
- The falsifier battery killed it before any PnL: **F-1 one-shot ancestry
  rho — the class's lawful entry observable IS the dead carry class's
  observable** (continuous pooled |rho| 1.0000 vs the CARRY-BAB proxy;
  binary 0.5308 skeptic / 0.658 A7-recompute, vs the immovable 0.20 bar).
  Everything else was CLEAN: PIT battery M-1..M-5 all PASS (318/318
  truncation-replay byte-identical), 42 non-overlapping holds ≥ floor,
  221/318 gate fires — the kill is ancestry identity, not leakage, not
  power, not cost.
- Outcome: `REJECT_ALL`, 0/7 scored cells, 0 PnL, 0 sealed looks, S1
  SEALED, GO-2 died REGISTERED_NOT_CONSUMED. The BTCUSDT funding/basis
  surface is closed against ALL funding-level-derived gates; reopening only
  on a non-funding-level PIT axis (OI / liquidation tape — both BLOCKED) or
  a dated measured cost-regime break.
- Durable assets: staging pipeline (funding 6,819 settlements zero-gap +
  spot/perp 1h corpus), the gate-law + PIT-fixture harness, the skeptic F-1
  rho runner, the F-0 court procedure (second adjudication), and the
  lesson: **vision spot archives switched to microsecond open_time in 2025
  — an ms-guard silently truncates grids; scale-normalize + verify grid
  endpoint against the declared window** (caught by the skeptic's
  independent epoch count, not by the author).

## DAYTRADER-100-V1 (TERMINAL 2026-09-28)
Owner-ordered rescore of 100 day-trader strategy brainstorm → census (55 ancestry-vetoed / 44 blocked / 1 runnable + owner-opened CARRY & BASISTERM) → 29 families / 87 cells scored under consumed GO + 12 owner-ordered remediation cells = 99 computations, REJECT_ALL, 0 survivors, repro ALL_MATCH. Ancestry-relaxed-by-owner disclosure on every row (non-independent trials). INC-DT100-1 spread-marking bug: caught, disclosed, remediated under owner order. Engine + keyless staging assets live in .worktrees/daytrader-100-v1/integration. Successor: REGIME-GATED-COMBO-V1 (conditional allocation over 6 dead legs, diagnostic-labeled). A7 terminal waived by owner verbatim.

### PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (TERMINAL 2026-10-01, POLICY_NO_INCREMENTAL_VALUE)
Amended-law portfolio program (owner 2026-09-29: novelty-label không phải gate; 1,200-idea corpus → 294 screened → 150 triage-runnable → 62 TRAIN-diagnosed → 12 survivors → 8 policy variants → scored 40/48 identities). Policy layers giảm net & tăng DD vs always-on; A7 terminal CONFIRM_WITH_CONDITIONS. Durable assets: 376-test engine, 846-row labeled discovery ledger, 43 COST_DOMINATED kills, COMPLEMENTARITY_TRAIN, IBKR probe chain + IDENTITY_FREEZE (7 daily candidates BLOCKED pending amendment), TB triple-barrier design (57-row budget registered, unspent). Worktree .worktrees/portfolio-composite-12assets-100k-v1/integration @ c93123db. Lesson P-33.

### ETHUSDT-OPEN-SEARCH-V2 (TERMINAL 2026-10-01, NO_INCREMENTAL_VALUE)
STOP-1 breadth-gate overlay: 8/8 cells, G3 wall fails 4/4, G10 fails 4/4; references reproduce V1 terminal 28/28 cent-exact; G8 repro ALL_MATCH; G9 A7 CONFIRM_WITH_CONDITIONS (r1 remediation lawful). First co-owner GO transmission (delegation 2026-09-30, auth record verbatim). §8 branch: tranche V3 pending owner decisions (new tuples / redirection / end). Worktree .worktrees/ethusdt-open-search-v2/integration @ 857af951. Lesson P-34.

### DAILY-EXPLORATORY-V1 (TERMINAL 2026-10-02, EXPLORATORY_COMPLETE_NEGATIVE_NO_PASS)
First exploratory-only cycle under the owner's no-statement election: 10 ids / 83 rows, quote-CCY engine, DECLARED costs x1.0/1.5/2.0, every trade + blocked signal journaled. All arms negative; NOT_RUN_THIN floors. Durable: engine + 32 tests, 85 journals, frozen input sets, envelope law, OI-1 framework, prospective-surface law (~2029-09). Worktree @e1872377.

### SPORTS-WINPROB-DISCOVERY-PREP-V1 (TERMINAL 2026-10-06, DISCOVERY_PREP_COMPLETE_PROPOSALS_ONLY)
Owner-directed expansion of pre-match win-prob research beyond NBA/WNBA/NFL: 5 parallel lanes + fresh-context verifier over 9 sport groups, $0, 0 scored cells. 40 competition verdict rows (PASS 2 — soccer internationals CC0 49,547 games, Retrosheet MLB attribution; CONDITIONAL 15; FAIL 1; NOT_RUN-family 22), ~529.4k measured games (~502.6k in 12 full-data-qualified corpora, ~191 MB outside git with sha256 manifests). Key measured facts: JeffSackmann tennis repos + chadwickbureau/baseballdatabank are 404 (mirrors substituted where licensed — tennis CC BY-NC-SA internal-only); cricsheet is ODC-BY 1.0; football-data.co.uk has free-use statement but no formal license; ESPN public API reaches NCAA to 2001-02 but only ~13% subset; Euroleague/FIBA/sports-reference/Kaggle/CFBD fail-closed. 5 successor PREP packets proposed, NONE registered (owner instruction per cycle required). A7 PASS_WITH_FINDINGS (0C/0H) discharged via ERRATA commit 1035bc79. Worktree .worktrees/sports-winprob-discovery-prep-v1/integration @ 23b81a26.

### SOCCER-INTL-WINPROB-PREP-V1 (TERMINAL 2026-10-07, PREP_COMPLETE_PENDING_OWNER_SCORED_DECISION)
First successor PREP from the DISCOVERY shortlist (owner instruction 2026-10-07): men's internationals 3-way win-prob protocol frozen on the CC0 martj42 corpus (49,547 games, sha df35268f unchanged since DISCOVERY). Central obligation DISCHARGED, not waived: date-only corpus → PIT_LAW_PROVEN_SAMEDAY_EXCLUSION (features = strictly-earlier dates; day-batch outcome-free ordering; same-day cost 0.4703% matches / 0.1423% edges; RETROSPECTIVE_ONLY_REPLAY; kickoff times never fabricated). Freeze: B0 = (0.495584, 0.231516, 0.272900) on 21,627 exclusion-clean train rows [1951,2001); B1 = Elo/Davidson 3-way procedure frozen UNFITTED; splits warmup/train/OOS 2001–2022/held-out 2023+; budget B0+B1+V1_HCA_REFIT; synth suite 6/6. A7 PASS_WITH_FINDINGS (0C/0H) — MEDIUM-1 (B0 vs exclusion law) discharged via errata. Known data defect frozen: Tahiti–New Caledonia 1974 contradictory duplicate excluded. Prospective = NOT_RUN_SOURCE (no $0 fixture feed). Worktree .worktrees/soccer-intl-winprob-prep-v1/integration @ 27bb57f2. Lesson P-37.

### SOCCER-INTL-WINPROB-SCORED-V1 (TERMINAL 2026-10-07, STAGE_A_EDGE_CANDIDATE_CONFIRMED)
First historical scored successor executed end-to-end under the two-key law (owner typed `GO SOCCER-INTL WINPROB V1 SCORED` verbatim after A7 AUTHORIZED_WITH_FINDINGS + delta AUTHORIZED_TO_EXECUTE_SCORED at the remediated gate). ONE scored pass, budget 3/3 (B0+B1+V1 frozen arms): chrono OOS [2001-01-01, 2023-01-01) n=20,708 — B0 LL 1.049906, **B1 Elo/Davidson (K=48/ν=0.6/HCA=65) LL 0.912037 (ΔLL −0.1379, ΔRPS −0.0465) and V1 (HCA=80) 0.909325 (−0.1406/−0.0473) both BEAT B0 beyond preregistered margins on ALL + competitive + friendly slices**. Repro twin byte-identical (ex generated_utc/tag); A7 terminal CONFIRM with from-bytes independent re-derivations (incl. a no-import B0 re-implementation). Incidents disclosed: INC-SIS-1 claims-format bug (metrics authoritative, engine byte-unchanged post-run); GO-gate defects (immutable genesis pin with no lawful path + registry-string convention mismatch) fixed by gate-only remediation BEFORE execution, delta-audited; **heldout 2023+ metrics were mechanically recorded (n=3,737/arm) though never used — PARTIALLY REVEALED, fresh owner gate required for any heldout use**. Stage-A candidate only: not deployment, not S1, not prospective (NOT_RUN_SOURCE). Worktree .worktrees/soccer-intl-winprob-scored-v1/integration @ 6d3e659b. Lessons P-38.

### NWSL-WINPROB-SCORED-PREP-V1 (TERMINAL 2026-10-15, SCORED_PASS_COMPLETE_B1_REJECTED)
First NWSL win-prob cycle: corpus ESPN 1,438 rows (warm-up 2016–2018 = 335, TRAIN 2019–2022 = 372 with 2020 excluded + 41 nwslR CC/Fall rows disclosed separately, OOS 2023–2025 = 515 game-IDs frozen sha bf293cab BEFORE any OOS metric, HIST-2026 216 not scored); deterministic 90-minute label law (ET/Pens/Golden Goal ⇒ DRAW-90, 14 rows); dispute law: 2017-06-17 kept as D via SoccerStatsUS third source, 2021-09-04 excluded; owner-frozen design (7 decisions); synthetic battery 9/9 incl. 5 mandated refusal cases; train-internal selection KEEP_B1 (all 6 hypothesis CIs incl 0 → third scored cell RELEASED, effective budget 2); single scored pass B0+B1 on the frozen list: **REJECT_B1_VS_B0** (RS dLL +0.004004/game, dRPS +6.46e-05 vs thresholds ≤−0.01/≤−0.005; B1 OOS slopes collapse to 0.225 pooled vs TRAIN 1.060 — OOS overconfidence; per-season incoherent +0.078/+0.062/−0.083). Repro twin ALL_MATCH; A7 prelaunch AUTHORIZED_WITH_FINDINGS + DELTA_VERIFIED; A7 terminal CONFIRM_WITH_FINDINGS 0C/0H with independent replay bit-exact. Claim cap: partially-exposed-window evidence, NO edge claims; prices-history research-only; NWSL paper scope untouched (NOT_RUN_NWSL_PAPER_HOOKUP). Worktree .worktrees/nwsl-winprob-scored-prep-v1/integration @ acf8b395. Successor: new round + changed mechanism axis only (K/ν/HCA re-tune on the same OOS ancestry-fenced).

## FUTURES-R2S-CAMPAIGN-V1 (CLOSED 2026-10-16) — research-to-strategy campaign: honest zero, one real-but-cost-dead signal, futures history audited

- Verdict `CAMPAIGN_COMPLETE_WITH_FINDINGS` (A7 fresh-context
  AUTHORIZED_WITH_FINDINGS 0C/0H/3L at terminal 269d4047). Owner
  sections A–J executed: W0 futures FAILURE_ATLAS (7 surfaces, 10
  groups, 5-class taxonomy, 17 preventive checks) → W1 tested layers
  (sealed chain-of-record loader, PIT level-memory adapter, bounded
  runner w/ hard 24-cap, fold law, hash-chained ledgers, deterministic
  agent + simulator + NO-ORDER boundary) → W2 five dossiers, frozen
  rubric, K1+K3 developed (20/24 configs, 0 scored) → K1 0/24 rows
  (permutation-null kills: level-memory gain on NQ reproduced 0.83× by
  random level assignment) → K3 real reversion signal (hit 0.60–0.64,
  symmetric, clean controls) cost-dead at reference bands (0.13–0.37×).
- Durable: campaign control dir on the terminal branch (atlas, evidence
  index, dossiers, verdicts, agent replay proof, capital feasibility,
  next-gate packet); sealed loader + bounded runner + fold law + agent
  machinery in `research/futr2s/` + `agent/` on that branch.
- Standing facts added: CME/macropin debts unchanged; IBKR handshake
  still UNVERIFIED; validator family_failures enum lacks `futures`
  (disclosed). S1 untouched; no orders; no push.

### SOL-MEME-WALLET-FOLLOW-PREP-V1 (TERMINAL 2026-10-16, PREP_COMPLETE_PENDING_OWNER_SCORED_DECISION)
First Solana new-token (memecoin) wallet-follow PREP: owner-authorized feasibility + specs + read-only core, ZERO scored cells (0/0), no GO by design, no push. Verdict: machinery verified, data authority PARTIAL. L1 SOURCE_MATRIX 19 sources (only SRC-SOLRPC-PUBLIC AUTHORIZED at $0; pump.fun frontend REJECTED_LICENSE ToS §21(h); Flipside/SolanaFM dead; Bitquery archive drops Trade_Side → structurally unfit for trader replay; Helius $49/mo = ORC-1 owner request; verdict BOUNDED_REPLAY_PARTIAL_CONDITIONAL), 7 program IDs pinned from official docs (independently cross-checked by the controller probe). G4 measured probe (36 archived requests/17.8MB, budget ≤400/20MB): public RPC serves blocks at measured ages 61/146/313/646 days; current solana-core 4.3.0 REFUSES blocks containing transaction version 1 unless `maxSupportedTransactionVersion:1` (-32015 silent completeness trap); failed txs visible (3/5 recent sample); sample mint Token-2022 (metadataPointer+tokenMetadata, freeze/mint authority null); NO historical account state on non-archive node → pool replay must bootstrap from creation tx; NO source anywhere exposes historical provider receive time → all latency MODELED. L2 specs: universe+no-lookahead wallet selection law; 3 concepts A/B/C with wave-1 budget exactly 12 configs (A×4,B×2,C×2,CTRL×3,BASE×1), all SPEC_CANDIDATE; execution latency-cost law with 12-cell MODELED_LATENCY grid. L3 core `research/solmeme/` stdlib-only (journal/dedupe/attribution fee-payer≠trader + hop-dedupe/Token-2022 flags/gates/shadow position STUCK_NO_EXIT/cost-latency exact-Fraction/deterministic replay/census-only NO PnL) + 137 tests PASS + NO_BROADCAST_PROOF. L4 fresh-context verifier: **PASS_WITH_FINDINGS** 12/12 items, 0 FAIL, 0 CRITICAL/HIGH, 2 MEDIUM + 5 LOW (F1 16→12 typo errata'd; F2 entry-delay timestamp assertion = pre-freeze blocker; F3 eligibility-snapshot module deferred; F7 12 SPEC_REGISTERED rows at acceptance). NEXT_GATE_PACKET: pre-freeze blockers + ORC-1..4 owner decisions; recommendation NOT-YET-scored. Worktree .worktrees/sol-meme-wallet-follow-prep-v1/integration @ a3e35cd3. Report_VI in control dir. Lesson P-41.

### FUTURES-FIRSTPASS-M1 (TERMINAL 2026-10-16, RUN_COMPLETE_M-A_FAIL)
First registered forecast-model experiment on the first-passage target
(owner pinned materiality M-A verbatim; lineage PREP-FORECAST-DESIGN →
TARGET-CENSUS-20261016 → FIRSTPASS-MODEL-PREP-20261016 → this cycle).
108/108 fits computed (3 specs × ES/NQ × z0.10/z0.05 × 9 evaluable folds
2014–2022 + 12 frozen empty-train records), single pass under
governance.heavy_lock; primary contrast S2−S1 paired Δlogloss ES z0.10 =
**+0.00281 nats (CI [+0.00106,+0.00460]) — level-position block WORSE
than fair context baseline; 0/3 eras; calibration slopes 0.149/0.049** →
M-A_FAIL, terminal verifier CONFIRM (independent reproduction 3.3e-17).
Diagnostics recorded without rescue: NQ|z0.1 −0.0025 (post-hoc flip,
fenced), z0.05 mixed. Fence: FUTR-FP-M1-LEVEL-POSITION-REJECT (no
re-tune rescue of context+level-position softmax on this target).
Durable: run_driver + frozen runner (digest 1fd92dea), deterministic
fold law with NOT_EVALUABLE_EMPTY_TRAIN handling, non-vacuous synthetic
dry-run machinery, terminal verifier artifacts. Control dir on terminal
branch @ 78e19823. All EXPLORATORY_OUTCOME_EXPOSED; NO PnL; S1 untouched.
