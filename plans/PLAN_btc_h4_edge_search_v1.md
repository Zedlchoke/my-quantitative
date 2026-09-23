# PLAN BTC-H4-EDGE-SEARCH-V1 — mechanism-backed search for books that beat the frozen BTC_H4 baselines (vol-managed long / majors basket / band execution / measured-funding cost authority)

> Status: `PLANNED_NOT_STARTED`. Owner directives 2026-09-23 (#1 three-state
> router — closed TERMINAL NO_ELIGIBLE_PROPOSAL; #3 re-point the search loop
> to BTC 4H with full delegation of design/scope and machine downloads, and
> STOP for the owner's typed GO before any scored cell). This cycle answers
> #3. Class: POSTHOC S0 DISCOVERY — 2020–2026 is outcome-observed; every
> number is post-hoc, never OOS; ceiling verdict
> `POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`. NOT a rescue and
> NOT a re-run of dead classes: the search space below is exactly what the
> failure memory leaves open. S1 `SEALED_UNTOUCHED`. No paper/live/orders.

## 0. Cycle identity

```text
cycle_id     BTC-H4-EDGE-SEARCH-V1
asset        crypto (cell BTC_H4 primary; majors basket adds ETHUSDT-PERP,
             SOLUSDT-PERP from the SAME frozen Vision pipeline)
class        POSTHOC S0 DISCOVERY (declared: NO dev/holdout split is
             possible on this window — everything is outcome-observed; a
             survivor earns only a prospective-validation successor)
question     PSV1 measured that the frozen BASELINES dominate every timing/
             gated candidate on BTC_H4 (TREND_LF +1,278,271 >
             ALWAYS_ON_LONG +814,204 > Donchian +177,692 >
             SPARSE_RISK_OFF +99,457 @1.0x), and controls keep killing
             timing claims. The OPEN question this cycle preregisters:
             can a MECHANISM-BACKED book — vol-shaping, diversification,
             or cost-shaping, never entry-timing — beat ALL frozen
             baselines after costs on the same window? A NO is a valid
             terminal.
inputs       (a) SAME frozen BTC_H4 panel, manifest sha256 3f1a6687…
             (b) ETHUSDT-PERP + SOLUSDT-PERP 1h Vision klines staged by
             THIS cycle through the same pipeline law (keyless; per-symbol
             coverage measured at data gate, fail-closed; SOL USDT-M
             history may start later than BTC — documented, never patched).
             (c) MEASURED funding series: Binance Vision monthly
             fundingRate zips BTCUSDT (availability measured by the owner
             recon probe: 200, keyless, deterministic) — replaces the
             PSV1 CONSTANT 1.377e-5/8h as the funding cost authority for
             this cycle's arms (lane D). PIT unchanged: decision at H4
             close, first fill next H4 open.
folds         FROZEN (identical to PSV1/V2/TRV1): F1 2020-01-01→2021-04-30 ·
             F2 2021-05-01→2022-12-31 · F3 2023-01-01→2024-12-31 ·
             F4 2025-01-01→data end; ends force-flat; warmup truncated.
budget       max 12 scored cells = 3 lanes (A/B/C) × 4 configs. Lane D is
             an accounting upgrade applied inside the same run, not a cell.
             The four PSV1 baselines + per-lane controls are reference
             computations inside the scored run.
s1           SEALED_UNTOUCHED
orders       NONE
go_phrase    GO BTC H4 EDGE SEARCH V1 SCORED EXECUTION
             (STOP-1 gate §6; the dispatching prompt is NOT a GO)
predecessors PHASE-STRATEGY-V1 TERMINAL (anchor af52f358); V2 TERMINAL
             NO_ELIGIBLE_PROPOSAL (c390375e); TRV1 TERMINAL
             NO_ELIGIBLE_PROPOSAL (4d93ff9e). All byte-untouched. The old
             buy leg FAILED G3/G5/G6 — a test component, never certified.
forbidden    choosing any constant by scanning fold PnL; entry-TIMING
             families (all PSV1 §7.2 dead shadows + RSM-V1 specialist
             library + breakdown-short / OI-cascade / short-horizon
             reversal / basis-fade / funding-carry forms); regime/phase
             router class (RSM-V1/JEV/PSV1/TRV1 reopening law); leverage
             (sizing fraction ≤ 1.0 always); moving/excluding folds;
             relaxing gates after PnL; mid-run stop on ugly numbers;
             git add -A.
```

## 1. Why this space is open (failure-memory derivation, class-level)

```text
DEAD (vetoed at admission, no re-test): entry-timing on BTC (G6 control
kills: block-shuffle out-earns every gated book); regime/phase mapping and
routers (RSM-V1, JEV V1/V2, PSV1, TRV1); all §5.3-classes of TRV1
(breakdown-short, OI-*, reversal, basis-fade, funding carry/level/jump,
liquidation episodes, taker-flow classes, pair-spread, run-imbalance,
amihud, DVOL-shock, weekend/attention/ticket classes).
OPEN (never measured in this program):
  A. risk-SHAPING of already-strong long books (inverse-vol exposure
     scaling; Moreira–Muir vol-managed portfolio mechanism);
  B. DIVERSIFICATION across crypto majors with per-asset trend gates
     (portfolio construction — program only ever ran single-asset books);
  C. COST-SHAPING of the trend signal itself (dead-band/hysteresis on the
     SMA state = fewer whipsaw flips; attacks the measured flip cost of
     TREND_LF, not its entry timing);
  D. the funding CONSTANT in the PSV1 cost kernel was never audited
     against the measured funding path (Q-8: measured beats stated).
None of A–D is an entry-timing family. All are priced under the same
engine, folds, tiers and force-flat law.
```

## 2. Anti-overfitting law

All constants come from ROUND pre-declared ladders fixed in §3 BEFORE any
PnL (round = the same convention as PSV1 §5.3); sensitivity (±1 notch) is
reported as label-agreement/weight-agreement, never optimized. No fold PnL,
no year labels, no trade outcomes, no future peaks enter any rule. The
FULL distribution of the 12-cell campaign is reported — losers included.

## 3. Lanes, configs, controls (frozen BEFORE any arm PnL)

```text
LANE A — VOL-MANAGED LONG (mechanism: exposure scaled by inverse recent
  realized vol; scale_t = min(1, TARGETVOL_ANN / rvol_t_ANN), rvol = 150-H4-
  bar (25-day) realized vol of H4 closes, causal; scale ∈ [0,1] — NO
  leverage). Re-priced daily at 00:00 UTC H4 boundary.
  A1 vol-managed ALWAYS_ON_LONG, TARGETVOL_ANN = 0.60
  A2 vol-managed TREND_LF (SMA200 gate × vol scale), 0.60
  A3 vol-managed Donchian arm (the named ancestor — OWNER-WAIVED, expected
     high correlation by construction), 0.60
  A4 = A2 with TARGETVOL_ANN = 0.40 (round notch; sensitivity reported)
  control: block-shuffle (30 H4 bars) of the scale series (G6-A).

LANE B — MAJORS TREND BASKET (mechanism: trend + cross-major
  diversification; per-asset long iff close > SMA200(H4 of that asset),
  basket weights inverse-vol (150-bar) normalized to sum ≤ 1.0, rebalanced
  every 6 H4 bars, force-flat law per asset at its own fold ends).
  B1 BTC+ETH basket (full window; SOL excluded — coverage law)
  B2 BTC+ETH+SOL from SOL coverage start (documented shorter history)
  B3 BTC+ETH with BTC-gate: basket flat unless BTC itself SMA200-long
  B4 = B2 rebalanced every 12 bars (round notch)
  control: block-shuffle (30 bars) of each per-asset gate (G6-B).

LANE C — BAND EXECUTION ON TREND (mechanism: dead-band hysteresis on the
  SMA state — enter long when close > SMA200×(1+b), exit when close <
  SMA200×(1−b); flip cost falls with b; the SIGNAL is unchanged, the LAW
  of switching changes). Round ladder:
  C1 b=0.01  C2 b=0.02  C3 b=0.03  C4 b=0.005
  control: block-shuffle (30 bars) of the band-state series (G6-C).

LANE D — MEASURED-FUNDING COST AUTHORITY (accounting upgrade, inside the
  same scored run): stage the Vision fundingRate series (BTC 2020-01→
  2026-08 measured-available; per-settlement signed rates), build the
  funding cost path for a unit position, and price EVERY arm AND every
  baseline under BOTH the frozen PSV1 constant (comparability with the
  ancestor record) and the measured path (honesty). Report the drag delta
  per baseline; if the ranking of the baselines changes under measured
  funding, that fact is a first-class finding. Fail-closed: if the
  funding series cannot be staged with a deterministic digest chain, lane
  D is NOT_RUN and pricing stays on the frozen constant.
```

Same engine, same capital ($100,000, fraction ≤ 1.0), same execution
(decision H4 close, fill next H4 open, force-flat at fold ends), same cost
tiers 1.0×/1.5×/2.0×, same fold law — for every arm, baseline and control.

## 4. Gates (per scored cell; ALL must PASS)

```text
G1  net > 0 at 1.0x;  G2 net > 0 at 1.5x
G3  beats ALL FOUR frozen baselines at 1.0x (the wall, unchanged)
G4  positive in ≥3/4 folds OR best-fold-removed net > 0
G5  no single fold contributes >50% of positive net
G6  the lane's preregistered block-shuffle control must NOT out-earn the
    cell (out-earn ⇒ kill; invalid-control null ⇒ disclosed, rest on G1–G5)
G7  turnover within frozen ceiling; zero unnecessary close-reopen
G8  reproduction byte-match; G9 A7 terminal clean
G10 FOLD-TRADE-OFF disclosure vs the arm's own reference baseline
    (A vs ALWAYS_ON_LONG/TREND_LF; C vs TREND_LF; B vs BTC-only TREND_LF):
    report Δ per fold; combined net must increase; no fold flips
    positive→negative vs that reference.
G11 ANCESTRY (pre-PnL, A1 re-measures at freeze): signal/weight-series
    |rho| ≤ 0.20 vs applicable dead shadows — lane A vs generic_dvol_shock
    proxy (realized-vol shock z) and run_imbalance; lane B vs
    xsect_tstrend (V9) representation; lane C shares ancestry with
    TREND_LF BY CONSTRUCTION (declared; G3-vs-TREND_LF is the test, no
    novelty claim is made).
```

ALL-PASS on any cell ⇒ ceiling verdict
`BTC_H4_EDGE_SEARCH_V1_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_
VALIDATION`. Full-distribution report of all 12 cells regardless.

## 5. Floors (adapted, declared)

Continuous books: decision population = H4 bars in-fold (≥100 trivially;
margin reported). No state-episode floors (TRV1's trap does not apply —
no state machine exists here). G5 concentration is the fragility gate.

## 6. Cycle phases and verdicts

```text
P0   intake; registry hygiene; heavy-lock measurement.
P1   data authority: ETH/SOL kline staging through the BTC pipeline law
     (coverage census fail-closed) + funding series staging (lane D);
     ancestry rho measurements (G11) — all PRE-PnL.
P2   feasibility census (pre-PnL): TREND_LF flip count & flip cost on H4
     (lane C arithmetic), vol-path census (lane A), basket turnover
     (lane B); ceiling strikes before any PnL.
P3   freeze (configs/digests already in §3; freeze file + engine SHA
     committed) + fixtures (PIT mutation, scale-cap ≤1, band hysteresis
     golden, funding sign/cadence, fold force-flat, tier exactness) +
     sanitized dry-run (non-vacuous) + A7 prelaunch fresh-context.
STOP-1 OWNER GATE: report full-campaign charter, actual denominator,
     costs, overfit risk, and the exact GO phrase:
     GO BTC H4 EDGE SEARCH V1 SCORED EXECUTION
     The owner types it verbatim at this gate; no other phrase consumes;
     this prompt is NOT a GO.
P4   scored run under the machine-wide heavy lock (12 cells + baselines +
     controls, full denominator, both funding laws); no mid-run stop.
P5   independent reproduction byte-match + A7 terminal.
P6   two-half close; verdict exactly one of §6.1.
```

### 6.1 Terminal verdicts (exactly one)

```text
BTC_H4_EDGE_SEARCH_V1_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION
BTC_H4_EDGE_SEARCH_V1_NO_INCREMENTAL_VALUE
BTC_H4_EDGE_SEARCH_V1_BLOCKED_DATA_OR_SELECTION
BTC_H4_EDGE_SEARCH_V1_NO_ELIGIBLE_PROPOSAL
TECHABORT
```

## 7. Trial identity and denominators

Every scored cell: cycle_id BTC-H4-EDGE-SEARCH-V1; cell BTC_H4 (+basket
legs identified per asset); family_id ES1-<LANE>-<CONFIG>; arm_id;
arm_config_digest; data manifest digest(s); code_freeze_sha; cost_tier;
funding_law (constant|measured); fold contract. Observed denominator
counts every computed cell×tier×funding_law; published counts successes.

## 8. Boundaries

Worktree `.worktrees/btc-h4-edge-search-v1/integration`, branch
`orca/btc-h4-edge-search-v1-integration`; base = PSV1 terminal anchor
af52f3582270bcc19634add3d88858e0c28959bf (frozen engine inherited
verbatim). Registry only via researchctl. Heavy lock for heavy compute;
light census exempt (<5 min CPU / <2 GB). No leverage anywhere (fraction
≤ 1.0). S1 sealed; no orders; no credentials; raw staged bytes stay under
gitignored `data_local/`; only manifests/digests commit. PSV1/V2/TRV1
artifacts byte-untouched; root checkout is bootstrap/owner space.
Turn-scope: pre-GO turns may stage, census, freeze, test, audit — not run
the scored backtest.

## 9. Amendments log

None yet. Amendments pre-outcome only; may not touch folds, tiers, gates,
ladders or the verdict ceiling.
