# PLAN JEV-REGIME-ROUTER-V2 — forced-choice Jev classifier + code-owned abstention

> Status: `PLANNED_NOT_STARTED`. Owner instruction 2026-09-22 (after the
> authorized graceful stop of V1's bulk at 990/8,567 states with persisted
> regime 990/990 TRANSITION_UNKNOWN — failure class `UNKNOWN_COLLAPSE`).
> S0 historical research ONLY. No paper/live/orders. S1 `SEALED_UNTOUCHED`.

## 0. Cycle identity

```text
cycle_id     JEV-REGIME-ROUTER-V2
class        S0 RESEARCH (forced-choice regime classification x frozen
             strategy router; V1 evidence = one collapsed design, NOT a
             scientific comparison; V2 inherits NO cache, NO historical
             decisions, NO namespace from V1)
budget       18/18 scored cells = 3 cells (BTC H1/15m, BTC H4/15m, SPY D1)
             x 6 arms (ALWAYS_ON_TREND, ALWAYS_ON_MEAN_REVERSION,
             DETERMINISTIC_REGIME_ROUTER, JEV_ONLY_ROUTER,
             DETERMINISTIC_PLUS_JEV_CONFIRMATION [architecturally preferred],
             RANDOM_MATCHED_ROUTER); buy-hold computed as reference metric
             per cell, not a scored arm
S1           SEALED_UNTOUCHED (every asset)
orders       NONE (no broker/paper/testnet/live surface)
go_phrase    GO JEV REGIME V2 BULK HISTORICAL REPLAY   (STOP-1 V2 gate)
forbidden    research/control/SANDBOX-OVERFIT-3ASSETS/ (never read);
             V1 runtime/decisions/cache as INPUTS to any V2 decision or
             threshold (V1 is evidence of a failure class only)
```

V1 usage law: the ONLY permitted use of V1 observations is naming the
failure class `UNKNOWN_COLLAPSE` and justifying the V2 design change
(forced-choice + code-owned UNKNOWN). No V1 threshold, prompt fragment,
bin boundary or mapping may be tuned against V1 labels beyond that.

## 1. Core design changes vs V1 (owner law)

1. **Jev never abstains.** Raw provider output may ONLY be one of
   ACCUMULATION | UPTREND | DISTRIBUTION | DOWNTREND (schema-enforced
   choice set). TRANSITION_UNKNOWN does not exist as a provider option.
2. **Code-owned abstention.** The safety layer sets effective
   TRANSITION_UNKNOWN when: provider/schema failure; missing/stale state;
   phase-confidence < 0.50; phase top1−top2 margin < 0.20; hierarchical
   answers contradict; persistence confirmation fails. Confidence
   thresholds are NEVER lowered to force trades.
3. **Named semantic state.** The state is a named, documented object
   (semantic bins + raw numerics with names) — never an anonymous vector.
4. **Hierarchical classification in ONE provider call** (SDK supports
   multiple typed questions per `systemOne`): `structure` ∈ {TREND, RANGE},
   `direction` ∈ {UP, DOWN, NEUTRAL}, `phase` ∈ {4 labels}; each answer
   carries probabilities/confidence; schema version pinned. Consistency
   law: TREND+UP→UPTREND; TREND+DOWN→DOWNTREND; RANGE+NEUTRAL after prior
   DOWN→ACCUMULATION; RANGE+NEUTRAL after prior UP→DISTRIBUTION;
   anything else (TREND+NEUTRAL, RANGE+UP/DOWN, phase disagreeing with
   structure×direction, phase ACC/DIST with wrong prior direction) =
   contradiction → TRANSITION_UNKNOWN. No double-abstention: the model
   cannot output UNKNOWN; the code abstains only by the rules above.
5. **Arms** (all frozen before any PnL): deterministic-law-proposes +
   Jev-confirms-or-vetoes (`DETERMINISTIC_PLUS_JEV_CONFIRMATION`):
   trade the deterministic regime's strategy iff Jev's effective regime
   equals the proposal; disagreement → flat. Jev never selects alone in
   this arm; disagreement never invents a strategy.
6. **Cells**: BTC H1/15m and BTC H4/15m preregistered as INDEPENDENT
   cells (own folds, own trial accounting); SPY D1 continues. Selection
   between H1/H4 by PnL is forbidden; if API budget forces a choice, use
   canary classification-only collapse/stability, never PnL.

## 2. Data (re-verified, no re-pull)

Same frozen inputs as V1, digests re-verified at freeze: BTCUSDT 15m
catalog parquet sha256 `81d4f147…` (35,039 bars; H1 = 8,759 complete
hours; H4 = resample of exactly 16 aligned 15m bars, census at freeze);
SPY snapshot sha256 `3fd229f9…` (2,943 sessions, disclosed snapshot
semantics). EURUSD remains NOT_RUN. Fold floors: BTC-H1 4×~2,141
decisions (warmup 192 H1); BTC-H4 4×~499 (warmup 192 H4 ≈ 32 days;
floor ≥300); SPY 4×~672 (warmup 192 sessions; floor ≥300). Fold
boundaries frozen before any outcome; force-flat at fold ends; fold
attribution reconciliation identity (V1 remediation-r1 law) built in.

## 3. Semantic state contract (`freezes/semantic_state_contract.json`)

Named fields, causal/trailing-only, warmup 192 regime bars (H4 cell:
192 H4 bars), bins frozen from domain-standard conventions + synthetic
fixtures BEFORE any historical call — never from PnL:

```text
short_return   r4  (raw)          medium_return r24 (raw)
long_return    r72 (raw)          fast_trend    |ema_slope_fast| & sign:
               strong_up(>+.002) weak_up(+.0003..+.002) flat(-.0003..+.0003)
               weak_down strong_down (mirror)
slow_trend     same bins on ema_slope_slow
trend_strength adx14: low(<20) medium(20-30) high(>30)   [Wilder standard]
volatility_regime rv_pctile: low(<.25) normal(.25-.75) high(.75-.90) extreme(>.90)
drawdown_state dd_168: near_high(>-.05) mild(-.05..-.20) deep(<-.20)
range_location range_pos: near_low(<-.30) middle(-.30..+.30) near_high(>.30)
close_location clv_24: weak(<.40) neutral(.40-.60) strong(>.60)
volume_state   vol_z: low(<-1) normal(-1..1) high(>1)
dist_to_ema    dist_ema: extended_below(<-1.5) below(-1.5..-.25) at(-.25..+.25)
               above(+.25..+1.5) extended_above(>1.5)
prior_structure TREND_UP|TREND_DOWN|RANGE (from persisted effective regime)
prior_direction UP|DOWN|NEUTRAL
raw numerics kept WITH names (all V1 f01..f16 recomputed identically)
```

Anonymization unchanged: no symbol, no absolute dates, no price levels,
no calendar features, no event names, no PnL/outcomes; state_id =
sha256("JRV2"||asset||data_sha||bar_ts)[:16] — NEW salt family so V2
cache/ids can never collide with V1.

## 4. Question contract (`freezes/question_contract.json`)

One `systemOne` call per state, three typed questions
(`jrv2_question_io@1`): structure (2-choice), direction (3-choice),
phase (4-choice, NO UNKNOWN option). Response must carry per-question
choice + probabilities + confidence + model echo == pin + request_id +
usage (token accounting persisted per response — V1 design note fixed).
input_digest = producer-computed (V1 amendment_1 law) over
canonical_json(state)||requested_model; cache key = sha256(model||
state_id||input_digest||prompt_digest) (V1 amendment_2 law). SDK pin
`@typesafe-ai/sdk==0.6.0` exact; model pin re-probed at G0 (expected
jev-1.13.0; any drift re-frozen before calls); maxRetries 0; timeout
10 s; errors → code-owned UNKNOWN; NO re-asks.

Prompt budget: max 2 preregistered revisions BEFORE any historical call
(v0 = full schema + hierarchy rules; each revision = one observed design
trial, disclosed with fixtures evidence; after the FIRST historical
preview call, the prompt is FROZEN — no rescue iterations).

## 5. Safety layer + persistence (`freezes/safety_persistence_contract.json`)

Effective regime algorithm (deterministic, code-owned): provider ok AND
phase-confidence ≥ 0.50 AND phase margin ≥ 0.20 AND hierarchy consistent
(per §1.4 law incl. prior-direction rules) → phase label; else
TRANSITION_UNKNOWN. Persistence state machine identical to V1 frozen
params (0.50/0.20/confirm 2/dwell 6/cooldown 3) applied to effective
labels. Deterministic router (arm D) unchanged from V1 (EMA12/48
structure, ADX≥22, ±10% trailing-168 return) + same persistence.

## 6. Strategy mapping, costs, arms (`freezes/mapping_arms_freeze.json`)

Mapping and strategies IDENTICAL to V1 frozen contracts (TREND_LONG /
TREND_SHORT BTC-only / MR_LONG / FLAT; next-bar-open fills; fraction
1.0; fold force-flat; funding 1.377e-5/8h signed; BTC 6 bps/side
declared bound; SPY band A 10 bps/fill; stress ×2.0; cost sweep
1.0/1.5/2.0). Arm F confirm-law per §1.5. RANDOM_MATCHED null: 21 seeds,
matching tolerances occupancy ±2pp / switches ±10% / dwell ±10% /
invested ±2pp, Q-11 movement checks, fail-closed NOT_RUN_CONTROL_MATCHING.

## 7. Canary + historical preview (`freezes/canary_v2_contract.json`)

Synthetic suite (frozen with expected outcomes BEFORE any call): clear
uptrend; clear downtrend; range-after-downtrend; range-after-uptrend;
high-volatility conflict; low-volatility range; noisy contradictory;
missing/stale (not sent, local UNKNOWN); plus 8 perturbations per CLEAR
fixture (±10% jitter on raw numerics, seeded, preregistered).

Acceptance (preregistered): raw output NEVER contains a non-schema label;
100% schema-valid; clear directional fixtures not inverted; NO single raw
phase label > 70% across the balanced CLEAR fixtures; perturbation
stability ≥ 6/8 same effective label per clear family; ambiguous fixtures
ARE code-abstained (effective UNKNOWN) — safety layer must fire; clear
fixtures NOT mass-abstained by code (≥ 80% effective-labeled); zero
credential leakage; exact model pin; measured cost/latency recorded.

Historical preview (after synthetic PASS): ≤ 100 BTC H1 states sampled by
preregistered timestamp rule `i_k = floor(k*8567/100), k=0..99` (spread
across the year — NOT the warmup-window bias of V1's first-94 preview);
classification-only, no PnL, sequential prior law applies only where the
sample order preserves state continuity (prior for sampled states taken
from the last SAMPLED predecessor — documented approximation, preview-only,
never used in bulk). Collapse criteria (fail → STOP, no bulk, no prompt
rescue beyond the preregistered budget): any single effective label > 90%
OR effective UNKNOWN > 80%.

## 8. Tests (mandatory; hand-computed fixtures)

All V1 golden tests carried over (no-lookahead mutation, PIT, rolling
causality, digest echo cross-language incl. exponent-notation vectors,
sequential prior-state replay + resume determinism, fold partition
contiguity + reconciliation identity + no-span, next-bar fill, cost-once,
funding signed, S1 denial, broker-surface scan, freeze-digest assertions)
PLUS V2-specific: forced-choice schema (provider answer containing
UNKNOWN-equivalents rejected as SCHEMA_ERROR); code-owned UNKNOWN rules
(each trigger independently: low confidence, low margin, each
contradiction pattern, provider error, stale state); no
double-abstention (model never sees an UNKNOWN option in the question
schema — static check of the question builder); hierarchy consistency
matrix hand-computed (all 2×3×4 combinations → expected effective
outcome incl. prior-direction rules); confirm-arm law (deterministic
proposal × Jev answer matrix → flat/trade); semantic-bin boundary tests;
perturbation fixture generator determinism; preview sampling rule
determinism; V1-isolation test (V2 cache/state salts provably disjoint
from V1: hash-prefix collision test + no code path reads V1 runtime).

## 9. Gates and phases

```text
G0    credential name-check + models.list re-probe + pin re-freeze
I     plan -> register -> freezes (all contracts above) -> implementation
      (V1 codebase adapted; cache/data/runtime fully namespaced v2) -> tests
A7-1  fresh-context pre-bulk audit (owner checklist): no lookahead;
      forced-choice semantics; code-owned UNKNOWN; no double-abstention;
      cross-language digest; sequential prior replay; fold reconciliation;
      exact model pin; call/cost projection; no broker/order surface;
      V1 cache isolation. Zero unresolved HIGH/CRITICAL to proceed.
CANARY synthetic (billable, small) -> historical preview <=100 (billable)
      -> STOP if collapse criteria fire.
STOP-1 V2 (MANDATORY OWNER GATE): report canary + preview + measured
      cost + projection; WAIT for exact phrase
      `GO JEV REGIME V2 BULK HISTORICAL REPLAY`.
BULK  sequential replay per cell (BTC-H1, BTC-H4, SPY), heavy-locked,
      cache-first, resumable; freeze response manifests; A7-2 pre-scoring.
STOP-2 V2: WAIT for a fresh scored-backtest GO phrase.
E/R/T scored atomic run under heavy lock -> reproduce -> A7 terminal ->
      terminal verdict from the SAME vocabulary as V1 (JEV_* / BLOCKED_* /
      TECHABORT), now including the possibility that V2's forced-choice
      design yields a genuine comparison (V1 could not).
```

## 10. Boundaries

No push, no merge to main, registry only via researchctl, one heavy
worker machine-wide, never kill foreign processes, S1 sealed, no orders,
no credential leakage, V1 artifacts byte-untouched, root checkout is
bootstrap/owner space; worktrees `.worktrees/jev-regime-router-v2/*`.
Turn scope law (owner F): this turn may implement/test/bounded-canary/
preview/A7 — it may NOT bulk-replay, score, compute or view PnL, or
reuse V1's GO.
