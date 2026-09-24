# PLAN ETHUSDT-OPEN-SEARCH-V1 — tranche 1 of the owner-directed ETHUSDT strategy-search campaign

> Owner directive 2026-09-24 (verbatim): "mở cycle tìm kiếm strategy cho
> ETHUSDT cho tới khi tìm được strategy kiếm tiền có bằng chứng kinh tế rõ
> ràng." This opens a MULTI-TRANCHE campaign. The directive is the campaign
> OPENER — it is NOT a scoring GO (P-8). Each tranche is a bounded cycle with
> its own preregistered families and its own fresh typed GO; successor
> tranches are authorized by the standing directive ONLY while no candidate
> exists, and each must bring a NEW (information-source, vehicle) tuple.
> Class: POSTHOC S0 DISCOVERY — declared outcome-observed (see §1); a
> survivor earns only `…CANDIDATE_FOR_PROSPECTIVE_VALIDATION`. S1
> `SEALED_UNTOUCHED`. No paper/live/orders.

## 0. Cycle identity

```text
cycle_id     ETHUSDT-OPEN-SEARCH-V1
asset        crypto (single asset: ETHUSDT USDT-M perpetual)
class        POSTHOC S0 DISCOVERY (campaign tranche 1)
question     Do ETHUSDT books driven by CROSS-ASSET information — BTC's own
             price state (lane E1) or the ETHBTC relative-strength ratio
             (lane E2), both executed long/flat on ETHUSDT only — beat the
             frozen ETH reference books after measured costs (fee + slippage
             + measured funding) across 2020-01..2026-08? A NO is a valid
             terminal. ETH's own single-asset entry-timing families are NOT
             tested here — they are ancestry-vetoed by the PSV1/ES1 BTC
             record (symbol-swap law, handbook §14.3).
budget       2 lanes × 4 configs = 8 scored cells MAX (references, controls
             and stresses computed inside cells; they consume no identity)
s1           SEALED_UNTOUCHED
orders       NONE
go_phrase    GO ETHUSDT OPEN SEARCH V1 SCORED EXECUTION
             (STOP-1 §7; the dispatching prompt is NOT a GO)
forbidden    re-testing any FAMILY_FAILURES class with only
             symbol/threshold/horizon/sign/session swapped; regime/phase
             routers keyed on the TRADED asset's own state (RSM-V1, JEV
             V1/V2, PSV1, TRV1, ILLIQ-REG-V1 reopening law); funding
             carry/level/jump signal forms; basis-fade; vol-managed sizing;
             band/dead-band execution; exit-side overlays; entry-timing on
             the asset's own price; short-side breakdown classes; leverage
             (fraction ≤ 1.0 always); choosing any constant by scanning
             fold PnL; moving/excluding folds; relaxing gates after PnL;
             mid-run stop on ugly numbers; git add -A.
```

## 1. Why this class and this space (ancestry, disclosed)

Outcome-exposure inventory (why POSTHOC, no dev/holdout claim):

- No single-asset ETHUSDT strategy outcome has EVER been computed in this
  program. ES1's lane B (majors basket with ETHUSDT-PERP legs) was
  registered but NEVER RUN — its scored set was lanes A/C only (measured:
  `scored_summary.json` cells = A1..A4, C1..C4).
- ETH windows WERE outcome-exposed at portfolio level through cross-sectional
  universes containing ETH: XSECT-FUND-CARRY (~1y to ≈2026-08),
  ILLIQ-AMIHUD-28D-W / BASISLV-PREMFADE-28D (2025-08-22..2026-08-21), and
  CRYPTO-HISTORICAL-REPLICATION-3F-V1 (2021..2024, scoring in progress, ETH
  in universe). Plus general price-history knowledge (2020-21 ETH bull
  dominates any long book's fold profile).
- Therefore every window available to this cycle is outcome-observed in the
  posthoc sense; truth-weight is carried by PROSPECTIVE validation (§9), the
  same posture as BTC-H4-EDGE-SEARCH-V1.

Open-space derivation (what the failure memory leaves open):

```text
DEAD for ETHUSDT by program record (never re-test): ETH-own-price
entry-timing (PSV1 BTC families — symbol swap); regime routers on the traded
asset's own state (RSM/JEV/PSV1/TRV1/ILLIQ-REG); funding carry/level/jump;
basis-fade; pair-spread TRADING; vol-managed sizing (ES1-A); band execution
(ES1-C); exit overlays (BRV1); weekend/attention/ticket classes (V17);
taker-flow/size (V15/V16/M01); OI/liquidation classes (TRV1, no keyless
multi-year source anyway); DVOL-shock (TRV1).
OPEN (new information-source × new vehicle, never measured in-program):
  E1  BTC's own price state as the ETH exposure driver (info source:
      BTCUSDT series; vehicle: single-asset ETHUSDT long/flat). The program
      has only ever gated a book by the traded asset's own state or by
      cross-sectional RELATIVE RANK among many symbols — never by another
      asset's absolute state with execution on one asset.
  E2  ETHBTC spot ratio's own trend as the ETH exposure driver (info
      source: ETHBTC relative-strength series; vehicle: single-asset
      ETHUSDT long/flat). Distinct from dead pair-spread (no second leg is
      traded; no spread PnL) and from dead routers (gate input is the
      ratio series, not ETH's own price).
Both lanes' novelty claim is exactly the (info-source, vehicle) tuple; it is
recorded pre-PnL with measured weight-series agreement vs the ETH-trend
reference (§5 G11). If A7 prelaunch adjudicates either lane an ancestry
violation, the lane dies pre-PnL and the verdict enum's
NO_ELIGIBLE_PROPOSAL branch applies.
```

Mechanisms (why these could be real, and when they must fail):

- E1 (BTC lead): BTC is crypto's anchor/reserve asset; macro and flow shocks
  price into BTC first, ETH re-rates with a lag (attention sequencing,
  flow concentration, index rebalancing). If ETH prices BTC information
  near-instantly at H4 boundaries, lag-execution earns nothing after
  costs — that is the falsification. Control: block-shuffled BTC state
  (timing information destroyed) must NOT out-earn.
- E2 (rotation): capital rotates between BTC and ETH in persistent waves;
  ETHBTC ratio trend is the standard rotation barometer. When ratio trend
  is down, ETH underperforms even with BTC flat. If ratio trend has no
  persistence beyond costs, the gate is noise — block-shuffled ratio state
  must NOT out-earn.

## 2. Data authority (P1 — keyless public Binance Vision only)

- `klines:ETHUSDT:1h` USDT-M monthly zips, 2019-11..2026-08. Months
  2019-11/2019-12 are WARMUP-ONLY (never scored; measured first month at
  the gate — if Vision's floor is later than 2019-11, warmup truncates
  further, disclosed). 2020-01..2026-08 must be complete (BUILD_PASS
  census) — the ES1 manifest (80 files, sha256 chain, worktree
  `.worktrees/btc-h4-edge-search-v1/integration/research/control/
  btc_h4_edge_search_v1/freezes/staging_manifest.json`) is the
  verify-on-read cross-check: any digest mismatch on an overlapping month
  = `BLOCKED_DATA` for that month, no silent merge (fail-closed).
- `fundingRate:ETHUSDT` USDT-M monthly zips (measured funding cost
  authority). Floor measured at the gate (expected ≈2020 for UM perps);
  settlements before the floor exist only in warmup-only months — from
  2020-01-01 every held period must have measured settlements, else the
  affected fold-months are `BLOCKED_DATA` with counts.
- `klines:ETHBTC:1h` SPOT monthly zips (lane E2 signal input; spot ratio —
  no funding basis inside the signal). Census law identical.
- `klines:BTCUSDT:1h` USDT-M monthly zips (lane E1 signal input). Restaged
  under this cycle's own manifest (self-contained provenance), cross-checked
  against ES1/PSV1-era staging where overlapping.
- Resample 1h→H4 deterministically at UTC boundaries 00/04/08/12/16/20
  (Vision open-time convention; fixture: golden resample + DST-free 24/7
  calendar; missing 1h bars inside a month → H4 bar dropped, positions
  roll, gaps counted, never interpolated).
- Costs (frozen): taker fee 5.0 bps/side floor; 1 adverse tick slippage
  (ETHUSDT tick 0.01); funding charged per settlement at MEASURED rates
  while held. Stress tiers ×1.0/×1.5/×2.0 scale fee+slippage only (funding
  is a measured cash-flow path, not scaled). Baseline notional $100,000,
  fraction ≤ 1.0.
- PIT law: decision at H4 close t using only series closed ≤ t (BTC/ETHBTC
  close of the SAME just-closed H4 boundary is available at t — no
  lookahead); first fill at ETHUSDT open of t+1. Mutation fixture: shifting
  the info series +1 bar must move fills (no-lookahead proof); one-bar-lag
  golden fixture per lane.
- Acquisition posture: `OWNER_DIRECTIVE_SOURCE_AUTHORIZATION` (campaign
  directive 2026-09-24; same class as 3F's ordered Binance acquisition);
  keyless, no account, no ToS acceptance, no purchase. Vision CDN requests
  ≥0.35 s apart; fapi not required by this cycle. Egress-IP etiquette per
  the 2026-09-21 418 precedent.

## 3. Windows and folds (frozen NOW; ES1-identical for comparability)

```text
F1 2020-01-01T00:00Z → 2021-04-30T24:00Z   (ETH 130→~2400 bull)
F2 2021-05-01T00:00Z → 2022-12-31T24:00Z   (crash/chop)
F3 2023-01-01T00:00Z → 2024-12-31T24:00Z   (recovery bull)
F4 2025-01-01T00:00Z → 2026-08-31T24:00Z   (data end = last staged bar)
force-flat at each fold end; warmup truncated inside F1 (SMA200-H4 needs
~34 d; SMA1200-H4 ≈ 200 d → E2-B2's first decisions start ≈2020-07,
disclosed as reduced fold population, floors still apply).
```

Structural risk preregistered (Q-6, ceiling of the nearest window): F1 is
so large for any ETH long book that G5 fold-share ≤0.50 may kill
structurally — exactly like ES1's C3 (0.71–0.73). The bar stays frozen;
if all cells die on F1 concentration, that IS the finding, and tranche V2
must attack concentration structurally, not by bar relaxation.

## 4. Reference books (computed inside the scored run; NOT cells)

```text
BASE_CASH            flat, zero fills
BASE_ALWAYS_ON_LONG  long every bar, 2019-11 warmup, funding paid (≡ ETH perp
                     buy-and-hold under the same cost law)
BASE_TREND_LF        ETH-own SMA200-H4 long/flat (the wall's strongest member)
REF_SHORT_ALWAYS     short every bar (beta-environment disclosure; EURUSD-V2
                     lesson: the short side must be visible, not assumed away)
```

## 5. Lanes, configs, controls (round ladders frozen BEFORE any PnL)

```text
LANE E1 — BTC-INFORMATION EXECUTION (BTC state drives ETH exposure)
  E1-A1  BTC SMA200(H4) state: long ETHUSDT iff BTC close > BTC SMA200(H4)
  E1-A2  BTC SMA100(H4) state                       (ladder notch)
  E1-A3  BTC 30-day momentum sign: long iff BTC 180-H4-bar return > 0
         (round 30d; related shape, declared)
  E1-A4  A1 ∧ ETH SMA200(H4) state                  (combo, declared)
  controls: block-shuffle(30 H4 bars) of the BTC state series (G6-E1a);
         sign-inverted ETH fills (G6-E1b).

LANE E2 — ETHBTC ROTATION (ratio trend drives ETH exposure)
  E2-B1  ETHBTC close > SMA600(H4) (≈100 d)
  E2-B2  ETHBTC close > SMA1200(H4) (≈200 d)        (ladder notch)
  E2-B3  ETHBTC 90-d percentile of close > 0.50     (round)
  E2-B4  B1 ∧ BTC SMA200(H4) state                  (combo, declared)
  controls: block-shuffle(30 H4 bars) of the ratio state (G6-E2a);
         sign-inverted ETH fills (G6-E2b).
```

All arms long/flat {0,1}, no shorts, no partial sizing, no leverage;
reprice at each H4 boundary; force-flat at fold ends; same engine, same
cost tiers, same fills law for arms, references and controls.

## 6. Gates (per scored cell; ALL must PASS)

```text
G1  net > 0 @1.0×;              G2  net > 0 @1.5×
G3  net @1.0× beats ALL references (BASE_ALWAYS_ON_LONG, BASE_TREND_LF,
    REF_SHORT_ALWAYS) — the wall
G4  ≥3/4 folds net > 0 OR best-fold-removed net > 0
G5  max positive-fold share ≤ 0.50
G6  both preregistered controls must NOT out-earn the cell @1.0×
    (out-earn ⇒ kill; control-does-worse ⇒ signal carries information)
G7  fills @1.5× ≤ 10,000 AND measured cost/round-trip ≤ 10 bps
G8  reproduction byte-match (detached twin at code-freeze SHA)
G9  A7 terminal clean (0 unresolved HIGH/CRITICAL)
G10 fold-trade-off vs BASE_TREND_LF: combined net increases AND no fold
    flips positive→negative
G11 ancestry (pre-PnL, recorded in the freeze): weight-series Spearman
    agreement vs BASE_TREND_LF weights, DISCLOSED (not a kill bar — the
    incrementality question is decided by G3/G10); hard bar |rho| ≤ 0.20
    applies only vs lawful dead-shadow proxies, of which none shares the
    (info-source, vehicle) tuple — declared, table recorded pre-PnL.
```

ALL-PASS on any cell ⇒ ceiling verdict
`ETHUSDT_OPEN_SEARCH_V1_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`.
Full 8-cell distribution reported, losers included. Smoke-namespace numbers
kill and disclose only (P-15).

## 7. Cycle phases

```text
P0  registration (researchctl) + integration worktree
    .worktrees/ethusdt-open-search-v1/integration, branch
    orca/ethusdt-open-search-v1-integration from the wave SHA measured at
    registration (this commit). Bootstrap control files committed.
P1  data authority: probe floors → stage 4 series → census + digests +
    cross-check vs ES1 manifest → committed staged manifest. Light work:
    ~85 files × 4 series, tens of MB, minutes — light-exemption ceilings
    (≤15 min CPU, ≤2 GB) declared; if exceeded or the machine heavy lock
    (currently held by CHR3F data-staging) is required → wait/NOT_RUN_
    RESOURCE_CONFLICT, never spin.
P2  feasibility census (pre-PnL): per-lane flip counts & flip cost at H4,
    fold populations, warmup truncation table, G6 control null-validity
    (shuffle must MOVE the signal — Q-7/Q-11), G11 agreement measurements.
P3  freeze (this §5 ladder + engine SHA) + fixtures (PIT mutation, one-bar
    lag, resample golden, fold force-flat, costs exactly once, funding
    sign/cadence golden, tick exactness, truncation invariance) +
    sanitized exact-arm dry-run (non-vacuous; no PnL/PF/stress at ANY
    record depth; pairwise-distinct IDs; zero denominator delta) + A7
    prelaunch fresh-context (novelty adjudication of E1/E2 included).
STOP-1  OWNER GATE — report full charter, denominators, costs, overfit
    risk; owner types verbatim: GO ETHUSDT OPEN SEARCH V1 SCORED EXECUTION
P4  scored run under heavy-lock discipline (light-exemption only if within
    declared ceilings, else acquire the lock); no mid-run stop; per-cell
    post-run report (identity, exit, runtime, denominators, verdicts).
P5  detached-twin reproduction (byte-match) + A7 terminal.
P6  two-half close (§32 handbook): registry TERMINAL + budget, projection,
    HYPOTHESIS_LEDGER, FAMILY_FAILURES, MAP.md, LESSONS (if any).
```

## 8. Trial identity and denominators

Every scored cell: cycle_id, family_id `EOS1-<LANE>-<CONFIG>`, arm_id,
arm_config_digest, data_snapshot_digest (staged manifest sha256),
code_freeze_sha, cost_tier list, funding_law=MEASURED, fold contract.
Observed denominator counts every computed cell×tier outcome even if
publication fails (P-9); published counts successes. Stresses/controls/
references are zero-denominator reference computations.

## 9. Campaign law (the owner's "cho tới khi tìm được", bounded lawfully)

- Tranche terminal `NO_INCREMENTAL_VALUE` or `NO_ELIGIBLE_PROPOSAL` ⇒ the
  standing directive authorizes registering the NEXT tranche (V2, V3, …)
  with NEW (info-source, vehicle) tuples only; the family dead-list grows
  monotonically; nothing dead is re-tested; every tranche needs its own
  plan + fresh GO. Unbounded in tranches, bounded in each.
- Tranche terminal `…CANDIDATE_FOR_PROSPECTIVE_VALIDATION` ⇒ campaign
  pauses new search; owner decides mounting a prospective sleeve under the
  PROSPECTIVE-SHADOW-V1 program. Per SHADOW-PAPER-REVIEW-V1 sec-3 findings,
  any sleeve mount decision MUST preregister: promote/kill/time-stop laws,
  a pre-fill cost-identity reconcile, and a short-beta control arm
  (EURUSD-V2 SHORT_ALWAYS lesson). "Bằng chứng kinh tế rõ ràng" is delivered
  in two steps: posthoc all-pass (this cycle) THEN prospective survival —
  neither alone is a deployable-strategy claim.
- The campaign never bypasses: S1 seal, P-8 GO law, no-orders law,
  ancestry law, denominator law.

## 10. Boundaries

Root checkout = bootstrap/owner space; all lane work in the named worktree
only. Registry writes only via researchctl. No push/merge-to-main in this
cycle's lanes. Raw staged bytes under gitignored `data_local/`; only
manifests/digests/fixtures commit. Other cycles' surfaces byte-untouched
(including ES1's evidence worktree — read-only cross-check only).
Turn-scope pre-GO: stage, census, freeze, fixture, dry-run, audit — never
run the scored backtest.

## 11. Terminal verdicts (exactly one)

```text
ETHUSDT_OPEN_SEARCH_V1_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION
ETHUSDT_OPEN_SEARCH_V1_NO_INCREMENTAL_VALUE
ETHUSDT_OPEN_SEARCH_V1_NO_ELIGIBLE_PROPOSAL
ETHUSDT_OPEN_SEARCH_V1_BLOCKED_DATA_OR_SELECTION
TECHABORT
```

## 12. Amendments log

None yet. Amendments pre-outcome only; may not touch folds, gates, ladders
or the verdict ceiling.
