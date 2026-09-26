# SKEPTIC VERIFY REPORT — PWS-CX-BNBUSDT-C1 — F-0 court verification of the P1 kill

- **Lane:** economic-skeptic / F-0 court verification (outcome-blind, no PnL exists,
  none opened). Authored 2026-09-26.
- **Worktree / branch:** `/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-bnbusdt-c1/integration`
  @ `orca/pws-cx-bnbusdt-c1-integration`.
- **Actual start sha (measured):** `f4c55b17cc1364003c9ab24798a0e17f13d3bf2e`.
- **Job:** make P1's zero-proposal withdrawal **VERIFIED-BY-MEASUREMENT on BNB's own
  series**, not assertion-transferred from SOL — then give the C3 court verdict.
- **Outcome-blindness held:** no scored outcome file opened; no PnL exists for this
  program and none was sought. The funding plane was consumed read-only for
  representation math (gate-state / episode-count / cross-representation correlation —
  cost-book class, same authorization as the SOL skeptic used). The 1h kline plane was
  NOT consumed; no return series of any strategy was computed.
- **Inputs, sha-verified before use:** raw settled funding bytes
  `data_local/funding/fapi_scan_BNBUSDT_2026-09-26.json` — sha256
  `464da8832d53bf0454f286d8ef3566a357a69d93336de5aa5d2835876c0dc893` recomputed by this
  lane, matches `C1_machine_FUNDING_STATS_BNBUSDT.json` and the data-gate report §2/§7.
  Read first: machine funding-stats file + `C1_data_gate_REPORT.md` +
  `council/P1_PROPOSALS_BNBUSDT.md`; precedent pair
  `.worktrees/pws-cx-solusdt-c1/integration/research/control/PWS-CX-SOLUSDT-C1/council/`
  (`P1_PROPOSALS.md`, `SKEPTIC_F0_REPORT.md`); `research/wayfinder/FAMILY_FAILURES.jsonl`
  (137 rows) + `research/wayfinder/MAP.md`.

---

## 0. Role & blindness

This lane is the court, not a proposer. It audits P1's enumeration (each withdrawal must
cite a real recorded death/fence and apply the 2-of-3 axes law correctly), hunts for
direction sources P1 MISSED that the authorized observables can express, and converts
the P1 kill from an inherited claim into a measured one on BNB's own settled funding
series (sign persistence, representation rho vs the immovable 0.20 K-ANC bar at two
side conventions, ceiling×power spot-check). No outcome data was touched; zero scored
cells exist below.

## 1. Enumeration audit — the 5 withdrawals + missed-source check

Every withdrawal's cited deaths were greped against `FAMILY_FAILURES.jsonl` by this
lane; verdict classes confirmed:

| W | Cited deaths (verified verdict_class) | Axes law applied | Audit |
|---|---|---|---|
| W1 funding-carry/run | `CARRY-1D/3D/7D` SCIENTIFIC_REJECTION · `TRACKB1-CLASSA-FUNDING-LEVEL-GATED-CARRY` SELECTION_REJECTION (closing language closes "window/percentile/change/**run** transforms alike" BY NAME) · `H-FUNDCROWD-MR-v2` SCIENTIFIC_REJECTION · `V17-A6-P1-FUNDJUMP` SELECTION_REJECTION (rho 0.2439) · `PWSCXSOL1-I001-TAILPAYER-RUN-REGIME` VETOED_SAME_FAMILY_PRE_PNL | payer same (contractual) / information same settled series (run = transform) / risk shape same multi-day directional ⇒ ≤1-of-3 (universe) | **VERIFIED** — every citation real; law applied correctly |
| W2 event layer (burn calendar, SEC/DOJ 2023, Launchpool) | none cited — `BLOCKED_NEW_DATA_OWNER_GATE` | correctly NOT a death: the one class that could differ 3-of-3 IF the layer were authorized; outside the delegation boundary | **VERIFIED** — correct disposition (revival condition, not a proposal; not frozen by this lane either) |
| W3 exchange-token cross-pair state | `EOS1-E1` SCIENTIFIC_REJECTION (G3 baseline loss) · `EOS1-E2` SCIENTIFIC_REJECTION (G6: block-shuffled ratio state out-earned the real one — class-level death, symbol-swap-invariant) | payer FAIL / information FAIL / skeleton FAIL ⇒ 0-of-3 | **VERIFIED** |
| W4 weekend/clock/session | `V17-A4-P1-WKNDLIQ` SELECTION_REJECTION (its ANCESTRY_RHO_BLOCK failure code, corrected pooled rho 0.34–0.56 — P1 cites the code, consistent) · `V17-a5-P1-ATTN-PHASE` SELECTION_REJECTION · Q-7 law + mandated block-shuffle GMT twin | re-clock variant pre-vetoed (master §2.3) | **VERIFIED** |
| W5 tape/volume/OI/liq | `M01-AGGRESSOR-ABSORPTION-PANEL`, `ILLIQ-AMIHUD-28D`, `LOT-residual-MAX-7D`, `A5-V15-F1-ELITE-SIZE-ASYM`, `A6-V15-F1-TAKER-SAT`, `V17-a5-P2-TICKET-BREADTH`, `OILEV-quintiles` (SELECTION_REJECTION), `OILEV-V2`, `OITD`, `LIQEPIS`, `V17-A6-P2-OICASCADE` — all real, classes as cited | unconstructible tonight (child §2.1 prohibitions) + dead wherever measurable | **VERIFIED** |

- **Citation-surface nuance (disclosed, not material):** P1's enumeration row 3 cites
  "BTC-BEAR Confirmation-Lag Front-Run → VETOED_FICTIONAL_COUNTERPARTY" and
  "Mark-Trigger Catch-Down VETOED ×3". These vetoes are recorded in
  `research/wayfinder/MAP.md` (L147, L150), not as `FAMILY_FAILURES.jsonl` rows. Real
  recorded artifacts; wrong surface would only matter if a future proposal cited them
  as ledger rows.
- **Material errors found: NONE.**
- **Missed-source audit (mechanism space, not priors):** the authorized class
  {1h klines OHLCV; settled funding observable at settlement timestamps; spread census
  as cost book} expresses exactly: price-shape continuation/reversal (rows 1–2),
  kline-geometry order-flow proxies (row 3), funding level/state transforms (row 4),
  settlement-clock timing (row 5), volume/tape transforms (row 6), clock/calendar
  (row 7), cross-pair state (row 8 — note a cross-pair ratio needs BTC/ETH klines,
  which are not in tonight's BNB data plane; the fence binds either way), OI/liq/depth
  (row 9, unconstructible), vol-state (row 10), risk tilts (row 11). Combination
  constructs (funding×price interaction, vol-conditioned funding gates, volume-clock /
  dollar-bar re-clocking, timeframe downshifts) are transforms or gates bolted onto
  recorded-dead skeletons = variants per LESSON P-27, pre-vetoed. **P1 missed
  nothing.** The one genuinely 3-axis-different class (BNB event layer, W2) is named
  by P1 itself; it needs an owner data-authority action and then its own F-0 payer
  story per side (burn-supply vs regulatory-repricing are different mechanisms, neither
  ever measured in this program). This lane does NOT freeze it.

## 2. Measured representation law on BNB's own series (the load-bearing verification)

Definitions mirror the SOL skeptic (`PWS-CX-SOLUSDT-C1/council/SKEPTIC_F0_REPORT.md`):
maximal same-sign settlement runs, **zeros break runs** (run-census convention); entry
observable = mean of the **first K=3 completed settlements** (PIT at the K-th
settlement); gate state live from the run's (K+1)-th settlement onward; wall-clock span
pin irrelevant (BNB has **0 anomalous spacings** — measured, data-gate §2.2). Shadows
(trailing-window signed-mean sign states, strictly PIT): `W3/W9/W21/W90` settlements
(= CARRY-1D/3D/7D/30D level-window class) and the unconditional receiver (sign of the
expanding long-run mean). Representation rho = pooled Spearman (gate state vs shadow
state) over the settlement grid. Bar |rho| ≤ 0.20, immovable (master §6.4 K-ANC).

First, the raw series reproduces the C1 machine census exactly: n = 7,261;
sum −27.4199 bps; neg_share 0.239361; 3,601 zeros; run census 418 pos / 447 neg /
longest 63 / 46 / ≥3-runs 187 pos / 166 neg — all six match.

### 2a. Sign persistence

- Sign-series autocorrelation (zero settlements encoded as 0):
  **lag-1 +0.7587, lag-2 +0.6919, lag-3 +0.6642, lag-6 +0.5845**.
- P(next settlement same nonzero sign | adjacent pair both nonzero) = **0.9940** —
  consecutive nonzero prints essentially never alternate; BNB sign changes route
  through zero settlements (49.6% zero share).
- P(next settlement same sign | current nonzero; zero = break, the run-census
  convention) = **0.7637**.

A persistence gate on this series is the trailing level's sign, smoothed — same
mechanism SOL measured (lag-1 +0.853 there; BNB is somewhat less persistent because
zeros intervene, but persistence is extreme among consecutive nonzero prints).

### 2b. Representation rho vs the 0.20 bar — KILLS at both thetas

| gate (K=3, first-K-mean entry) | episodes | occ. 2-sided | rho vs W3 | vs W9 | **vs W21** | vs W90 | vs UNCOND |
|---|---|---|---|---|---|---|---|
| θ = 0.50 bps, two-sided | 152 pos / 156 neg | 24.3% | **+0.594** | **+0.527** | **+0.479** | **+0.383** | −0.058 |
| θ = 1.00 bps, two-sided | 102 / 126 | 21.3% | **+0.556** | **+0.493** | **+0.445** | **+0.353** | −0.035 |
| θ = 0.50 bps, neg-side-only (SOL mirror) | 156 neg | 11.4% | **+0.438** | **+0.390** | **+0.354** | **+0.237** | −0.175 |
| θ = 1.00 bps, neg-side-only | 126 neg | 10.7% | **+0.423** | **+0.376** | **+0.341** | **+0.225** | −0.168 |

**Every level-window shadow (W3/W9/W21/W90 — the CARRY-1D/3D/7D/30D dead family) at
every θ tested and under BOTH side conventions sits 1.12×–2.97× above the immovable
0.20 bar.** The gate is cosmetic on BNB's own series, exactly as P-29's operational law
predicts and as was measured on SOL (rho 0.316–0.703). Any funding-run/persistence gate
on this series is a member of the closed funding-level family — K-ANC, measured, not
asserted.

### 2c. Side conventions — disclosure

State convention: +1 while positioned to RECEIVE positive funding (short side receiving
at positive settlements), −1 while positioned to RECEIVE negative funding (long side
receiving at negative settlements), 0 otherwise; the "neg-side-only" convention keeps
only the long-receiver state (the SOL TAILPAYER mirror). **Which convention kills:
BOTH.** Two-sided is the harder kill (rho 0.35–0.59 vs windows); neg-side-only alone
still clears the bar everywhere (0.225–0.438). **Honest asymmetry disclosed:** the
vs-UNCONDITIONAL leg does NOT carry the kill on BNB (|rho| 0.035–0.175 < 0.20, both
conventions — BNB's expanding-mean sign is a slow flipper around a ≈0 mean with a 49.6%
zero share, unlike SOL where uncond rho hit +0.615). The binding fence on BNB is
specifically the **level-window shadow class** (CARRY-1D/3D/7D per the TRACKB1 closing
language) — which is the correct and sufficient reading of the fence.

## 3. Ceiling×power spot-check — honest, with the fee-only floor and a declared spread band

RT stress = fee 10 bps RT (DECLARED) + spread. Spread for BNBUSDT is
**NOT_RUN_DISK_CONSTRAINT** (data-gate §3; no substitution permitted) ⇒ the scored cost
gate is **BLOCKED tonight regardless of what follows**; this section is therefore a
declared-band sensitivity: spread ∈ {0 (fee-only floor), 0.5, 1.0} bps × {1.0, 1.5, 2.0}
stress. Ceiling law: episode's PIT first-K(=3)-mean ≥ θ_min where
θ_min × H_min(3 settlements) ≥ RT stress. Power floor: ≥100 closed RT.

| spread × stress | RT (bps) | θ_min (bps) | pos eps | neg eps | combined |
|---|---|---|---|---|---|
| 0.0 ×1.0 (fee-only floor) | 10.00 | 3.333 | 35 | 45 | **80** |
| 0.0 ×1.5 | 15.00 | 5.000 | 19 | 27 | 46 |
| 0.0 ×2.0 | 20.00 | 6.667 | 11 | 21 | 32 |
| 0.5 ×1.0 | 10.50 | 3.500 | 34 | 42 | 76 |
| 0.5 ×1.5 | 15.75 | 5.250 | 19 | 25 | 44 |
| 0.5 ×2.0 | 21.00 | 7.000 | 11 | 17 | 28 |
| 1.0 ×1.0 | 11.00 | 3.667 | 34 | 39 | 73 |
| 1.0 ×1.5 | 16.50 | 5.500 | 15 | 25 | 40 |
| 1.0 ×2.0 | 22.00 | 7.333 | 8 | 16 | 24 |

**HONESTY STATEMENT (as demanded by dispatch): BNB's ceiling grid is NOT EMPTY at the
fee-only floor** — 80 qualifying episodes combined (45 neg-side) at θ_min = 3.333 bps,
in flat contrast to SOL, where the feasible set was EMPTY at every (θ, K) even with
spread = 0. What this does and does not license:

- It does **NOT** resurrect the carry identity. The kill is **same-family + K-ANC
  measured on BNB's own series** (§2b: rho 0.225–0.594 vs the dead level-window family
  at every power-viable θ, both conventions). A non-empty ceiling grid only matters to
  a **future identity with a DIFFERENT information layer** — and such an identity would
  still owe 2-of-3 genuine axis differences AND a representation rho ≤ 0.20 on its own
  series, which every funding-run gate measured here fails.
- It does **NOT** clear the power floor: 80 < 100 in every PIT reading (max 45 on the
  SOL-mirror neg side). Only an ex-post LOOKAHEAD bracket (full-run means, both sides
  pooled: 49+95 = 144 at θ = 3.333) crosses 100 — lookahead is not PIT and is not
  eligible evidence.
- The cost gate is **BLOCKED tonight anyway** (spread census NOT_RUN_DISK_CONSTRAINT ⇒
  no measured RT ⇒ the ceiling law is unscoreable this cycle; K-COST verdict belongs to
  the cost auditor, not this lane).
- K-CONC pair-contrast, honestly recorded: BNB's negative-payment mass is far LESS
  year-concentrated than SOL's (largest year 2020 = 25.50%, next 2022 = 20.22%, 2023 =
  19.20%; top-2 = 45.72% — under the 0.50 fold bar; SOL had 59.1% in one year and 42.2%
  in one 9-day window). **The SOL K-CONC pre-kill does NOT transfer to BNB** — noted so
  no future lane inherits it. It is irrelevant tonight because the K-ANC kill carries
  the family and BNB has zero ≥75 bps deep prints (0 clamp-class mass) for any
  windfall-targeting variant.

## 4. Verdict for C3 — `SLATE_EMPTY_VERIFIED`

- P1 submitted **0 proposals**; this lane found **no material error** in the 5
  withdrawals (§1) and **no missed direction source** expressible on the authorized
  observable class (§1 mechanism-space audit).
- The kill is now **VERIFIED-BY-MEASUREMENT ON BNB**: same-family law (TRACKB1 closing
  language closes run transforms by name) + K-ANC measured on BNB's own series at two
  thetas and two side conventions (§2), all 1.12×–2.97× above the immovable 0.20 bar,
  with sign persistence measured (§2a) explaining why no gate construction can escape.
- **Freeze slate: EMPTY. No freezable identity. No backtest to run** (owner sprint
  instruction: same old information ⇒ close, don't score). **GO-2 dies UNCONSUMED.
  0 scored cells. 0 outcome views.**
- **What this licenses:** C3 may close the cycle with an empty slate; the measured
  BNB representation math (persistence, rho table, episode counts, declared-band
  ceiling) is a durable program asset for any future funding-class proposal, and for
  the revival conditions.
- **What it does NOT license:** no scoring, no spread claims (census NOT_RUN), no
  resurrection of the carry family via the non-empty fee-only ceiling grid, no
  transfer of SOL's K-CONC pre-kill to BNB, and no freezing of the W2 event-layer
  revival condition — that class stays open pending owner data authority, then owes a
  full F-0 (payer story per side) and the 2-of-3 axes test on entry.
- Revival conditions (standing, from P1 §4 + this lane's §2/§3 measurements): (i) owner
  R5-class data authority (BNB event calendar; liquidation tape / multi-year OI / L2;
  options surface); (ii) a dated cost-regime break (re-run §3 on new fee bytes); (iii)
  a dated distribution break — this exact representation math re-run on FUTURE BNB
  settlements showing a funding-run gate at |rho| ≤ 0.20 vs the level-window shadows
  with ≥100 PIT episodes ≥ its ceiling — currently failed at θ ∈ {0.5, 1.0}, K = 3,
  both conventions.

## 5. Durable facts for the record — pair contrast BNB vs SOL (funding plane)

| Fact | BNBUSDT (measured here) | SOLUSDT (SOL skeptic, same-day precedent) |
|---|---|---|
| n settlements | 7,261 (0 dup; floor 2020-02-10T08:00Z exact) | 6,580 |
| zero-rate share | **49.6%** (3,601) — median exactly 0 | ~0.02% (1) |
| neg_share / mean | 23.94% / −0.0038 bps | 28.62% / +0.0138 bps |
| worst print | −58.44 bps (2020-03-13); **0 prints ≥75 bps** | −200 bps ×4 (FTX clamp) |
| cadence anomalies | **0** (strict 8h throughout) | 101 sub-8h (FTX week) |
| sign autocorr lag-1 (zeros=0) | +0.759 | +0.853 |
| P(next same nonzero sign) | 0.9940 (adjacent-nonzero) / 0.7637 (run-census) | 0.812 |
| rho gate vs W3/W21 (θ=0.5, K=3) | +0.594 / +0.479 (two-sided); +0.438 / +0.354 (neg-only) | +0.607 / +0.493 |
| rho gate vs UNCOND | −0.058 (two-sided); −0.175 (neg-only) — **bar NOT breached** | +0.615 |
| K-CONC (neg mass, worst year) | 2020 = 25.50% (top-2 45.7%) | 2022 = 59.1% (FTX window 42.2%) |
| ceiling×power grid (fee-only floor) | **NOT EMPTY**: 80 eps PIT combined (45 neg) at θ_min 3.333 | **EMPTY** at every (θ,K) |

Net: the pair-swap reproduced the identity kill (level-window rho) and flipped the two
auxiliary kills (ceiling grid non-empty; K-CONC not binding) — which is why this
verification had to be measured on BNB and could not be assertion-transferred. The
verdict survives on the load-bearing leg.

## 6. Reproducibility

One-file script (stdlib + numpy), `/tmp/skeptic_bnb_rho.py`, run with
`/Users/hoangminhlong/my-quantitative/.venv/bin/python`; inputs = the sha-verified raw
scan only. Commands + numbers recorded in
`handoffs/HANDOFF_skeptic_verify.json` → `tests`. `/tmp` is ephemeral; the script's
full logic is 60 lines and its operations are fully specified in §2/§3 definitions.

## 7. Incidents / limitations

- Incidents: none.
- Limitations: (i) representation rho is a state-series correlation, not the formal F-1
  returns rho; (ii) spread UNKNOWN for BNB (NOT_RUN_DISK_CONSTRAINT) — §3 uses a
  declared fee-only floor + 0.5/1.0 bps sensitivity band, and the scored cost gate is
  BLOCKED regardless; (iii) funding series single-campaign fapi (Vision cross-check
  NOT_RUN — inherited disclosed caveat); affects level placement, not the
  order-of-magnitude rho result; (iv) `/tmp` script ephemeral (logic specified in-text);
  (v) P1's two fictional-counterparty vetoes cited from MAP.md rather than the JSONL
  ledger (disclosed §1, not material).

— ECONOMIC SKEPTIC lane, PWS-CX-BNBUSDT-C1, F-0 court verification
