# PLAN JEV-REGIME-ROUTER-V1 — Jev (TypeSafe AI) as a candidate regime classifier feeding a frozen strategy router

> Status: `PLANNED_NOT_STARTED`. Owner instruction 2026-09-22 (verbatim intent
> preserved in §0a). S0 historical research ONLY. NO paper/live trading.
> S1 stays `SEALED_UNTOUCHED` for every asset.

## 0. Cycle identity

```text
cycle_id     JEV-REGIME-ROUTER-V1
class        S0 RESEARCH (regime-classification × frozen strategy router,
             fully costed walk-forward, honest falsification design)
asset        shared (crypto + stocks legs; independent contracts per asset)
budget       12/12 scored cells = 2 eligible instruments × 6 arms
             (A BUY_HOLD_OR_CASH_BENCHMARK, B ALWAYS_ON_TREND,
             C ALWAYS_ON_MEAN_REVERSION, D DETERMINISTIC_REGIME_ROUTER,
             E JEV_REGIME_ROUTER, F RANDOM_MATCHED_ROUTER).
             Controls are diagnostics inside the arm cells and do not add
             budget. Every computed scored outcome consumes a slot even if
             reporting fails; slots never reassigned.
S1           SEALED_UNTOUCHED (every asset)
orders       NONE (no broker/paper/testnet/live surface anywhere in the code)
go_phrase_1  GO JEV REGIME V1 BULK HISTORICAL REPLAY   (STOP-1 gate)
go_phrase_2  GO JEV REGIME V1 SCORED BACKTEST          (STOP-2 gate)
forbidden    research/control/SANDBOX-OVERFIT-3ASSETS/ (never read, never
             used as input, never staged or committed)
```

Scientific question: does an external typed-classifier model ("Jev" via
TypeSafe AI `systemOne` choice questions), given ONLY causal anonymized
features, add incremental after-cost information over (i) always-on frozen
strategies, (ii) a simple deterministic trend×vol regime router, and (iii) a
random router matched on regime occupancy/switching/dwell — or does it merely
make backtests look better (trade less, decorate noise)?

Standing law inherited from the program: evidence-first; missing evidence is
`NOT_RUN`, never inferred `PASS`; freeze-before-outcome (P-6/Q-9); controls
are the product (P-24); margin-to-fail on every gate (P-2); per-fold series
persisted as launch contract outputs so DSR/PBO are computable at terminal
(P-11); costs conditioned on the router's own trading distribution with
preregistered ceilings and stress 2.0 (Q-2/P-21); random null must actually
move the signal and be structurally distinct, fail-closed when unmeasurable
(Q-11/P-20); gross/net pair on the identical accounting vehicle (Q-14);
measured beats stated, every single time (Q-8); a permutation that does not
move the signal is not a null (Q-11); smoke-namespace numbers may kill but
never select (P-15); no parameter/prompt/mapping change after any outcome is
visible (CLAUDE.md invariant).

## 0a. Owner instruction anchors (verbatim, binding)

The owner instruction of 2026-09-22 fixes, among others, these hard points;
this plan implements them and may only ADD stricter machinery:

- "Jev chỉ là candidate regime classifier" — no assumed edge; technical PASS
  ≠ profitable; confidence ≠ P(trade profitable).
- "KHÔNG GIẢ ĐỊNH JEV CÓ EDGE"; no rescuing Jev via prompt/threshold/mapping/
  feature edits after seeing PnL; no "production-ready"/"live-ready" claims.
- Regime classifier never selects orders, sizes, stops or sends orders.
- "Không gửi symbol thật / ngày tháng năm tuyệt đối / absolute price level";
  no strategy PnL / future return / fold verdict in payloads; no event names.
- Exactly five labels, outcome-blind definitions (§4).
- `maxRetries=0` in frozen replay; timeout/provider/schema error ⇒
  `TRANSITION_UNKNOWN`; "Không gọi lại để tìm câu trả lời đẹp hơn".
- API cost gate: ≤100 historical states in canary even with a key; stop
  before bulk for owner confirmation; no purchases on owner's behalf.
- Three mandatory stops (§9); current prompt is NOT a GO for billable bulk.

## 1. What this cycle is NOT

- NOT a live/paper/shadow deployment cycle; no broker API anywhere.
- NOT an S1 opening; NOT parameter search (no optimization grid exists in
  the design; every number is frozen before any outcome, from repo ancestry,
  regime semantics, or synthetic fixtures).
- NOT a claim that Jev is intelligent: the null hypotheses (arms B/C/D/F)
  are the point. A verdict of `JEV_NO_INCREMENTAL_VALUE` is a first-class
  successful close (Q-16).
- NOT cross-asset pooling: each instrument keeps its own calendar, clock,
  cost model, folds, and conclusion. No aggregate "3-asset" number exists.

## 2. Instruments (read-only S0 inventory → eligibility)

Inventory method (this section is the frozen eligibility record; digests are
re-measured and committed in `freezes/data_identity_freeze.json` BEFORE any
feature/outcome computation):

### 2.1 BTCUSDT — ELIGIBLE (two-tier: H1 regime clock / 15m execution clock)

- Data: Binance USD-M perp 15m LAST-EXTERNAL bars, machine-local catalog
  `catalog/data/binance_bar/BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/`
  (35,039 rows, 2025-08-20T02:34Z → 2026-08-20T02:34Z; V8X census: expected
  35,040 slots, 0 gaps, 0 unexplained — `data/v8x_manifests/crypto_universe_selection.json`,
  bars_dir_digest_sha256 `ac967c85…a3ccc`). Freeze re-measures the exact
  file sha256 + row count + first/last `ts_event`.
- H1 bars are a DETERMINISTIC resample of exactly four consecutive 15m bars
  per wall-clock hour (open=first open, close=last close, high/low=extremes,
  volume=sum). No interpolation. A missing 15m bar inside an hour makes that
  H1 bar INVALID (fail-closed, census says none exist in-window).
- Cost authority: no broker-grade crypto dossier exists in the authorized
  evidence space; therefore costs run as a DECLARED CONSERVATIVE FROZEN
  BOUND (status `DECLARED_CONSERVATIVE_BOUND`, not `MEASURED`): taker fee
  5.0 bps/side + slippage 1.0 bps/side (total 6 bps/side, 12 bps round
  trip), funding at the CRYPTO-NG4-frozen constant `1.377e-5` per 8h on
  signed notional (charged at every 8h boundary the position is open),
  stress tier ×2.0 PRIMARY (program law). Q-8 disclosure: the fee/slip
  numbers are exchange-schedule-derived conservative bounds, and the
  sensitivity of every arm-pair comparison to costs is reported (cost
  sweep 1.0×/1.5×/2.0×) so the verdict is not an artifact of the bound.
- Calendar: 24/7, no closures. Short side authorized by the cost contract
  (perp shorts pay/receive funding symmetrically).

### 2.2 SPY — ELIGIBLE (daily clock only; explicitly NOT intraday evidence)

- Data: EODHD EOD daily cache byte-pinned by STOCKS-SEARCH-V1 P0
  `retrieval_manifest.json` sha256 `0b6c4963…a8fd` (double-pull
  byte-identical), file
  `.worktrees/stocks-search-v1/integration/research/control/stocks_search_v1_run/p0/raw/eod_cache/SPY.json.gz`
  (read-only copy into this cycle's data namespace; source worktree is
  BLOCKED evidence and is never modified). Range 2015-01-02 → 2026-09-16
  (~2,92x sessions; freeze records exact count).
- Clock law: decision at session close t (from the completed daily bar);
  fills at next session OPEN (t+1). PIT: EODHD EOD close is published
  after close; using completed bar t to decide, fill t+1 open, satisfies
  availability (V7 law precedent). Corporate actions: use `adjusted_close`
  for returns/features, `close`+`open` raw for fill prices is INCONSISTENT —
  freeze: run entirely on the ADJUSTED series (adjusted open = open ×
  adjfactor) so fills/returns share one consistent vehicle (Q-14), and
  disclose that absolute levels are adjusted (irrelevant to the anonymized
  pipeline which never sends prices).
- Cost authority: STOCKS-SEARCH-V1 F6 frozen band model — SPY ADV ≫ $50M ⇒
  band A = 10 bps/fill (status: frozen band from `kernel_band_cost_v9.py`
  lineage / PLAN_stocks_search_v1.md F6), stress ×2.0 ⇒ 20 bps/fill
  worst-case ceiling. Long-only law (no borrow-cost authority — F6/NG6 F4):
  shorts FORBIDDEN on this instrument; the mapping freeze encodes it.
- Disclosure: "Đây KHÔNG phải 15m day-trading evidence" is printed on every
  SPY report. QQQ exists as pinned fallback but is NOT used (SPY passed).

### 2.3 EURUSD — `NOT_RUN` (recorded, fail-closed)

No intraday EURUSD OHLCV exists anywhere in the repo/worktrees; the daily
TD archive is digest-pinned but off-disk; forex broker cost authority is
`BLOCKED_BROKER_COST_AUTHORITY` (DEU lane-f dossier, only a 1.5 bps/fill
floor + stress 2.0 exist; Q-8/NG6 F4 law forbids inventing the rest).
Owner instruction: "Không dùng dữ liệu không rõ nguồn để ép đủ ba asset."
`NOT_RUN_EURUSD` is written into the data identity freeze with this
evidence; the cycle proceeds with 2 instruments and each keeps independent
conclusions.

### 2.4 Fold population floors (frozen)

BTCUSDT: ≥4 chronological folds, ≥1,000 valid regime decisions/fold
(H1 grid ≈ 2,140/fold after warmup). SPY: ≥4 chronological folds, ≥300
decisions/fold (≈660/fold). Fold boundaries frozen as exact bar timestamps
in `freezes/fold_contract.json` before any feature/outcome exists.
Purge/embargo law: features roll continuously (causal), so the only
cross-fold contamination channel is POSITIONS — fold-terminal
force-liquidation at last bar close (cost debited) is mandatory; embargo =
positions never span boundaries; no train/test split exists because
nothing is fitted (Jev model fixed, strategies frozen, persistence frozen).

## 3. Feature contract (causal, anonymized; `freezes/feature_contract.json`)

All features are computed on REGIME-CLOCK bars (BTC H1 resampled; SPY D1),
from completed bars only. Warmup = 192 regime bars (covers the longest
window 168 + rv24 = 192). No centered windows; no future normalization; no
whole-sample statistics; percentile/z-score windows are strictly trailing.

```text
f01 r1        log return last 1 regime bar
f02 r4        log return last 4 bars
f03 r12       log return last 12 bars
f04 r24       log return last 24 bars
f05 r72       log return last 72 bars
f06 ema_slope_fast  (EMA12_t / EMA12_{t-12} - 1) / 12
f07 ema_slope_slow  (EMA48_t / EMA48_{t-48} - 1) / 48
f08 dist_ema  (close/EMA50 - 1) / (ATR14/close)
f09 adx14     Wilder ADX(14) (repo ancestry regime.py)
f10 atr_pct   ATR14/close
f11 rv_pctile rank of current rv24 (std of last 24 log rets) among its own
              trailing 168 past values (exclusive of current) → [0,1]
f12 dd_168    close/max(close,168) - 1
f13 dist_low  close/min(close,168) - 1
f14 range_pos (close-min24)/(max24-min24) - 0.5, 24-bar Donchian position
f15 vol_z     (volume/mean(volume,168) - 1) / (std(volume,168)/mean(volume,168))
f16 clv_24    mean of ((close-low)/(high-low)) over last 24 bars, 0.5 if
              high==low (missing/zero-range bars are DROPPED from the mean,
              fail-closed if all 24 are zero-range)
f17 prior_regime  one-hot of the persisted regime state in force at t-1
              (all-zero at warmup start)
```

Anonymization law (payload to Jev): the `state` object contains ONLY
`{feature_vector: [f01..f16 as plain numbers], prior_regime: label}` — no
symbol, no dates, no absolute prices/volumes, no calendar features (session
bucket / day-of-week NOT preregistered ⇒ absent), no returns beyond the
trailing windows above, no PnL/outcome data of any kind, no event names.
`state_id` = sha256(asset_salt || bar_ts) hex — opaque, carries no
calendar. Verification is a golden test (§8).

Missing/stale state (NaN after warmup, invalid bar): decision is
`TRANSITION_UNKNOWN` by rule — the state is still SENT only if the feature
vector is fully finite; if any feature is non-finite the state is NOT sent
and the decision is locally forced UNKNOWN (provider never sees it).

## 4. Regime label contract (`freezes/regime_label_contract.json`)

Exactly five labels; outcome-blind causal definitions (verbatim in the
frozen Jev prompt; definitions mention ONLY past/当前 structure, never what
price does next):

```text
ACCUMULATION      a downtrend occurred previously; price now ranges/
                  compresses; downside pressure is weakening
UPTREND           positive causal trend exists now: higher-price structure
                  and measurable trend strength
DISTRIBUTION      an uptrend occurred previously; price now ranges/
                  compresses; upside pressure is weakening
DOWNTREND         negative causal trend exists now: lower-price structure
                  and measurable downside pressure
TRANSITION_UNKNOWN evidence conflicts, confidence low, data insufficient,
                  or state is changing
```

Required response fields per decision (validated, else UNKNOWN):
`regime` ∈ the 5 labels (free-text regimes are REJECTED), `probabilities`
covering all five (non-negative, sum 1.0 ± 0.01), `confidence`,
`model` (must equal pinned model), `request_id`, `input_digest`,
`latency_ms`, `status` ∈ {OK, TIMEOUT, PROVIDER_ERROR, SCHEMA_ERROR}.

## 5. Jev adapter contract (`freezes/adapter_contract.json`)

- Official SDK `@typesafe-ai/sdk` pinned EXACT `0.6.0` via package-lock
  (measured latest as of 2026-09-22; no caret range). Node ≥ 20 (host has
  24.5.0).
- TypeScript side ONLY: adapter, schema validation, request/response
  capture. Python side: data, features, folds, backtest, accounting.
  Boundary = versioned JSONL (§5a).
- Auth: `TYPESAFE_API_KEY` from environment only. Never in prompts, logs,
  git, handoffs, manifests. `dangerouslyAllowBrowser` stays default false;
  no browser execution. Adapter logs are redaction-safe (log level `warn`,
  credential headers redacted by SDK; adapter additionally never prints
  env or full headers).
- Model pin procedure: `client.models.list()` at canary time → freeze the
  exact model name (highest non-alias version; `jev-latest` is FORBIDDEN
  in frozen replay — owner law). Pin recorded in
  `freezes/model_pin.json` with `status: VERIFIED_LIVE` only when
  measured; without a key the pin stays `CANDIDATE_UNVERIFIED` and every
  live call is `BLOCKED_CREDENTIAL`. The response `model` field must
  equal the pin (schema test).
- Call discipline: `maxRetries: 0`, `timeout: 10000 ms` per call; any
  `APIError/APIConnectionError/APITimeoutError/schema violation` ⇒
  `TRANSITION_UNKNOWN` with status recorded. NO re-asking for a nicer
  answer. One call per state_id; append-only cache; duplicate request
  detection is a golden test.
- Cache: raw request/response JSONL append-only under
  `runtime/jev_cache/` (gitignored), keyed by
  `(model, state_id, feature_digest)`; replay reads cache, never re-calls.

### 5a. JSONL boundary (versioned `jrv1_decision_io@1`)

Python → adapter: one request line per state `{schema, state_id, state,
requested_model}`. Adapter → Python: one line
`{schema, state_id, status, regime?, probabilities?, confidence?, model?,
request_id?, input_digest, latency_ms, error_class?}`. `input_digest` =
sha256(canonical_json(state) || requested_model) computed on BOTH sides;
mismatch = schema error ⇒ UNKNOWN + incident.

## 6. Regime persistence (`freezes/persistence_contract.json`)

Numbers frozen from regime semantics + synthetic fixtures BEFORE any PnL
(not from outcomes): `min_confidence 0.50`, `min_margin 0.20` (top1−top2
probability), `confirm_bars 2` (candidate top-1 must persist 2 consecutive
regime bars), `min_dwell 6` regime bars, `cooldown 3` regime bars (a
candidate that fails confirmation is barred from re-candidacy 3 bars),
error/insufficient ⇒ `TRANSITION_UNKNOWN`. Full algorithm (candidate state
machine, UNKNOWN handling, initial state = UNKNOWN) is verbatim in the
freeze and golden-tested. The deterministic router (arm D) uses the SAME
persistence layer (one law, two classifiers).

## 7. Strategy mapping + arms (`freezes/regime_strategy_mapping_freeze.json`)

Jev (and arm D) NEVER choose strategies; this code-owned mapping does:

```text
ACCUMULATION      → MR_LONG          (BTCUSDT, SPY)
UPTREND           → TREND_LONG       (BTCUSDT, SPY)
DISTRIBUTION      → FLAT             (both; short-side MR lacks frozen
                                     authority for SPY and is not added
                                     for BTC to keep one uniform mapping)
DOWNTREND         → TREND_SHORT      (BTCUSDT only — cost contract covers
                                     shorts; SPY = FLAT by long-only law)
TRANSITION_UNKNOWN→ FLAT             (both; no new positions)
```

Frozen anchor strategies (execution clock; next-bar-open fills; one
position at a time; notional fraction 1.0 of current equity; no leverage):

```text
TREND_LONG   entry: close>EMA20 and EMA20>EMA50 (execution clock)
             exit : close<EMA20 | intrabar stop entry−3×ATR14 |
                    strategy turned off by regime | fold force-flat
TREND_SHORT  mirror (BTC only; stop entry+3×ATR14; funding signed)
MR_LONG      entry: RSI14<30 and close<BOLL(20,2) lower
             exit : close≥BOLL mid | RSI14>55 | 96 bars max hold |
                    intrabar stop entry−2×ATR14 | regime off | fold flat
```

Ancestry (repo, frozen parameters, no grids): EMA structure trends
(`strategy.py`/`strategy_trend_pullback.py` lineage), Bollinger+RSI MR with
ADK-era parameters (`strategy_mean_reversion.py`: RSI 30/55, BOLL 20/2,
2×ATR stop, wide-stop doctrine from NOTES §4.2), ADX/VHF regime semantics
(`regime.py`). Arm D deterministic classifier (trend×vol):
`dir=+1 if EMA12>EMA48 and close>EMA48; −1 if <; else 0`; ADX14 ≥ 22
(ancestry midpoint of regime.py adx_max 20 / breakout adx_min 25) ⇒
UPTREND/DOWNTREND by dir; else range with trailing-168-bar return < −10%
⇒ ACCUMULATION, > +10% ⇒ DISTRIBUTION, else TRANSITION_UNKNOWN; same
persistence layer. Arm F random matched router: seeded (21 seeds) segment
permutation of the Jev router's realized regime path preserving segment
lengths, matched to occupancy ±2pp / switches ±10% / mean dwell ±10% /
invested fraction ±2pp (fail-closed `NOT_RUN_CONTROL_MATCHING` with
measured deltas); headline = median seed; Q-11 live-null verification:
label-sequence lag-1 autocorrelation and regime→forward-return association
must both MOVE vs the Jev sequence (else the null is invalid, disclosed).

Risk engine (deterministic, outside Jev): next-bar-open fills; position
cap 1; gross exposure cap 1.0; stale-data rejection (decision older than 2
regime bars ⇒ flat); duplicate-order prevention; intrabar stops evaluated
on the bar after entry only via low/high crossing (stop fills at stop
price ± slippage); costs debited exactly once per fill; BTC funding every
8h boundary on open notional; fold-terminal force-liquidation; SPY
market-closure handled by session gaps (no synthetic bars, ever).

## 8. Tests (mandatory, written BEFORE any historical outcome exists)

Golden/unit tests (pytest, worktree `tests/test_jrv1_*.py`), all with
hand-computed fixtures: no-lookahead feature test (mutation test: altering
bar t+1.. never changes features at t); timestamp/PIT; rolling-
normalization causality; payload anonymization (no symbol/date/price/
event-name substrings; state_id opacity); exact model pin equality;
response schema validation incl. probability-sum; provider failure ⇒
UNKNOWN (timeout/error injection); cache immutability + no duplicate
requests; next-bar fill semantics; cost debit exactly once; fold
boundaries + force-flat; persistence (confirm/dwell/cooldown state machine
transitions hand-computed); minimum dwell; random-router matching
tolerances; S1 denial (any S1 path access raises); no broker/order surface
(static scan of the package for order/broker APIs); exactly-frozen mapping
(mapping file digest asserted in code); zero post-outcome mutation
(freeze-file digests asserted at runner start).

## 8a. Synthetic canaries (before ANY live call; expected labels frozen first)

Six fixtures (`freezes/synthetic_canary_fixtures.json`): clear uptrend;
clear downtrend; range-after-downtrend; range-after-uptrend;
contradictory/noisy; missing/stale state. Expected labels frozen BEFORE
any call. PASS requires: valid schema; no unsupported label; missing/stale
⇒ UNKNOWN; directional fixtures not absurdly inverted; raw request/
response hashed and stored; zero credential leakage. Mock-adapter canaries
validate the PLUMBING (smoke namespace, P-15: kill-only); live canaries
(only with key, ≤100 budget) validate the PROVIDER.

## 9. Gates, stops and phases

```text
G0    credential/env probe: TYPESAFE_API_KEY presence (name-only), SDK
      install + typecheck, models.list pin probe (only if key present).
      No key ⇒ BLOCKED_CREDENTIAL recorded; ALL code/tests/mock canaries
      still complete (owner law).
I     freeze contracts (this §2–§8 as JSON, digested) → lanes implement →
      integrate → full targeted tests green.
Z     mock-canary + SMOKE end-to-end run (mock decisions; unscored
      namespace; kills-never-selects; NOT counted in budget; labeled
      MOCK_SMOKE on every artifact).
A7-1  fresh-context pre-API audit: plan conformance, feature causality,
      anonymization, regime definitions, exact model/package pins,
      fixtures, API-key safety, call/cost estimate. A7 writes artifacts
      only. Zero unresolved HIGH/CRITICAL required to proceed.
STOP-1 (MANDATORY OWNER GATE) report: plan path; cycle/worktree/branch/
      full HEAD; eligible instruments; timeframe; model/package pins;
      tests; A7-1 verdict; canary results; actual API cost; projected
      total calls/cost; then WAIT for exact phrase
      `GO JEV REGIME V1 BULK HISTORICAL REPLAY`.
BULK  historical replay of all decision states (cache-first, resumable,
      append-only). Then: completeness + cache-integrity verify; response
      manifest/digests frozen; A7-2 pre-scoring audit (cached decisions,
      prompt freeze, persistence, mapping, costs, folds, controls, no
      outcome leakage, zero unresolved HIGH/CRITICAL).
STOP-2 (MANDATORY OWNER GATE) WAIT for exact phrase
      `GO JEV REGIME V1 SCORED BACKTEST`.
E     acquire machine-wide heavy lock; ALL frozen arms of an instrument in
      ONE atomic run; never read arm 1 to alter arm 2; no rerun on bad
      outcomes; count every observed result; release lock. Fold-terminal
      force-flat inside the run.
R     independent reproduce/reconcile (byte-level decisions+ledger), A7
      terminal fresh-context audit.
T     terminal verdict — ONLY from:
      JEV_INCREMENTAL_VALUE_SUPPORTED | JEV_NO_INCREMENTAL_VALUE |
      JEV_INCONSISTENT_ACROSS_FOLDS_OR_ASSETS |
      BLOCKED_CREDENTIAL_OR_COST | BLOCKED_DATA | BLOCKED_CONTROL_STATE |
      TECHABORT
```

`JEV_INCREMENTAL_VALUE_SUPPORTED` additionally requires ALL of: Jev router
net-positive after costs; beats arms B and C; beats arm D; beats arm F
(median); not driven by a single fold (top-fold profit share ≤ 0.50) nor a
single asset; reproduction matches; A7 terminal clean of unresolved
HIGH/CRITICAL. Even then it is S0 research support ONLY — "không phải
quyền paper/live".

Projected bulk size (measured from data identity at freeze): BTCUSDT ≈
8,568 H1 decision states − 192 warmup ≈ 8,376; SPY ≈ 2,92x − 192 ≈ 2,73x;
total ≈ 11,100 states ≈ 11,100 billable calls, each ≈ 1,200–1,800 input
tokens (state + frozen prompt) + minimal output. Canary ≤ 100 states
measures REAL latency/failure/tokens/cost; owner decides bulk with the
measured price in hand. No purchases by agents, ever.

## 10. Evaluation contract (`freezes/evaluation_contract.json`)

Per instrument × arm: gross PnL; costs (fee/slip/funding split); net PnL;
total return; CAGR (valid for both clocks); Sharpe; Sortino; max drawdown;
profit factor; expectancy/trade; trades; win rate; turnover; time in
market; regime switches; regime occupancy; average dwell; UNKNOWN share;
fold-by-fold results (per-fold series persisted for DSR/PBO at terminal,
P-11); concentration (top-fold profit share); skipped-trade PnL
(counterfactual TREND_LONG PnL on bars where the router was flat);
margin-to-fail for every comparison (P-2); cost sweep 1.0/1.5/2.0×.

The seven owner questions are answered explicitly: (1) Jev vs always-on
after costs; (2) Jev vs deterministic router; (3) Jev vs random matched;
(4) PnL of trades Jev blocked (skipped-trade analysis by regime); (5)
regime intelligence vs merely trading less (invested-fraction-matched
comparison arm F + turnover normalization); (6) stability across folds AND
instruments; (7) switching-cost attrition (cost share of gross edge on
regime-switch days, stress tier).

Reports: `REGIME_CLASSIFICATION_REPORT.md` (timeline, occupancy,
confidence distribution, transitions, dwell, UNKNOWN, canaries, stability
sample) and `REGIME_BACKTEST_REPORT.md` (per asset × arm tables, equity
curves, drawdowns, costs, folds, strategy×regime matrix — DIAGNOSTIC
ONLY, remapping after seeing it is forbidden in-cycle — skipped-trade
analysis) + machine-readable artifacts (raw JSONL, decision cache,
manifests, fold results, trade ledger, equity series, terminal verdict).

Five-year-old summary (mandatory): Jev gọi thời tiết gì? Có hay đổi ý?
Chọn strategy khiến tài khoản tốt hơn hay tệ hơn? Thông minh hơn luật đơn
giản hay chỉ giao dịch ít hơn? Có đáng mở prospective-shadow cycle kế
tiếp không?

## 11. Boundaries

No push, no merge to `main`, no edits to old cycles' artifacts/verdicts,
registry only via `researchctl`, one heavy worker machine-wide
(`NOT_RUN_RESOURCE_CONFLICT` if held), never kill foreign workers, S1
sealed, no orders, no credential leakage; feature generation and API
canary run LIGHT (no heavy lock); only BULK replay and scored backtest
are heavy-locked; root checkout is bootstrap/owner space only — all lane
work in the exact worktrees `.worktrees/jev-regime-router-v1/{integration,
lane-py,lane-ts}` on branches frozen at dispatch; commits by pathspec,
`git add -A` forbidden; owner-untracked dirs (`research/control/SANDBOX-
OVERFIT-3ASSETS/`, `.zcode/`, `research/control/d2_curiosity_v1_sources/`)
never touched.
