# PLAN PHASE-STRATEGY-V1 — per-phase strategy research on three independent cells

> Status: `PLANNED_NOT_STARTED`. Owner instruction 2026-09-23 (successor after
> REGIME-STRATEGY-MAPPING-V1 closed TERMINAL `NO_REGIME_STRATEGY_INCREMENTAL_VALUE`;
> JEV-REGIME-ROUTER-V2 remains TERMINAL `JEV_NO_INCREMENTAL_VALUE`).
> This is NOT a rescue cycle and NOT a rename of the old mapping: no Jev API
> call, no V2/RSMV1 artifact mutated, no old mapping/strategy reused with new
> parameters, no Jev label used as truth, no old PnL used to select rules.
> S0 discovery research ONLY. No paper/live/orders. S1 `SEALED_UNTOUCHED`.

## 0. Cycle identity

```text
cycle_id     PHASE-STRATEGY-V1
asset        shared (three separate cells: BTC_H1, BTC_H4, SPY_D1)
class        S0 DISCOVERY on historical data. Nothing in this cycle is OOS,
             including the BTC 2020–2024 history extension: it is history this
             program never computed on, which reduces but does not remove
             selection risk — labeled below as DISCOVERY_ON_NEVER_COMPUTED_
             HISTORY, never "out-of-sample".
question     For each of the three cells, and for each market phase
             (ACCUMULATION / UPTREND / DISTRIBUTION / DOWNTREND /
             TRANSITION_UNKNOWN): is there ONE economically motivated strategy
             whose PnL survives costs across pre-committed financial eras?
             A phase with no testable strategy is a valid result.
inputs       (a) BTC: BTCUSDT-PERP bar data. Existing frozen 15m catalog
             sha256 81d4f147… (2025-08-20→2026-08-20) re-verified read-only;
             history extension via Binance Vision keyless USDT-M klines
             (feasibility probed 2026-09-23T07:13Z: monthly 1h zips HTTP 200
             from 2020-01; 2019-12 monthly 404). (b) SPY: frozen snapshot
             sha256 3fd229f9… (2015-01-02→2026-09-16, 2,943 sessions,
             disclosed snapshot semantics), read-only reuse, no re-pull.
jev_calls    ZERO. Phase labels are computed by each cell's own PIT rule
             (code-owned, §5). The cached V2 Jev decisions are NOT read by the
             proposal lanes at all (§7). Jev labels are never truth.
budget       max 15 scored cells = 3 cells × ≤5 phase-candidates. Baselines
             (§8) and falsification controls are reference computations inside
             the scored run, not budget cells. Thin phases are NOT_RUN, never
             scored, never pooled.
s1           SEALED_UNTOUCHED (every asset; no S1 file is opened, read or
             scored by any lane in this cycle)
orders       NONE (no broker/paper/testnet/live surface anywhere)
go_phrase    GO PHASE STRATEGY V1 SCORED EXECUTION   (STOP-1 gate, §16)
predecessors REGIME-STRATEGY-MAPPING-V1 TERMINAL
             `NO_REGIME_STRATEGY_INCREMENTAL_VALUE` (integration head
             690b06c8, branch orca/regime-strategy-mapping-v1-integration);
             JEV-REGIME-ROUTER-V2 TERMINAL `JEV_NO_INCREMENTAL_VALUE`
             (integration head 0c277a94). Both byte-untouched in this cycle.
forbidden    research/control/SANDBOX-OVERFIT-3ASSETS/ (never read, by owner
             order); S1 and every frozen S1 set; Jev API of any kind; cached
             V2 decision files as proposal input (§7); mutating any V2/RSMV1
             artifact; strategy-level PnL numbers from predecessor corpora
             inside proposal lanes (§7.3); BTC H1-vs-H4 selection by PnL;
             treating BTC_H1 and BTC_H4 as two independent confirmations
             (same asset — §2); SPY short or leverage without a new owner
             authority (SPY is long/flat only); parameter rescue after any
             scored PnL is visible; silent relaxation of the 20/3/100 floors;
             scoring while the SPY calendar defect class is unfixed (§10).
```

## 1. Predecessor intake law (re-measured before this plan freezes anything)

All anchors re-measured on disk 2026-09-23 and must hold at every phase gate;
any drift ⇒ STOP and disclose before proceeding:

1. Registry: `REGIME-STRATEGY-MAPPING-V1` lifecycle TERMINAL,
   integration head `690b06c8`; `JEV-REGIME-ROUTER-V2` TERMINAL, head
   `0c277a94`; both trees clean at last measurement.
2. Verdicts recorded and NOT reopened: `NO_REGIME_STRATEGY_INCREMENTAL_VALUE`
   (45 observed across runs, repro 69/69) and `JEV_NO_INCREMENTAL_VALUE`
   (18/18 cells). Both reopening laws bind this cycle (§7).
3. Mechanism findings that THIS design must respect (class-level only):
   BTC losses were strategy-native gross + cost churn, not switching;
   SPY losses were dominated by a cost-churn collapse caused by a frozen-law
   calendar interaction — the Tuesday staleness defect (§10); only BTC_H1
   ACC/UP/DOWN carried sample at the 20/3/100 floors; a relaxed-floor
   comparison was preregistered there and its thin-positive SPY reading died
   at 1.5x costs — thin-sample mirage, never value.
4. SPY ALWAYS_ON_TREND remains a reported BASELINE (concentration-killed at
   V2); it is never citable as edge and never promoted. Its existence as a
   strong per-cell baseline is why G3 (§13) compares against frozen baselines.
5. S1 sealed; no predecessor paper/live/order anywhere.

## 2. Contamination law

- The entire price history involved is historical; every scored number this
  cycle can ever produce is S0 discovery. The BTC 2020–2024 extension is
  `DISCOVERY_ON_NEVER_COMPUTED_HISTORY` — a stronger discovery label, still
  not OOS, still not validation.
- BTC_H1 and BTC_H4 are separate CELLS (own labels, own folds, own trial
  accounting) but ONE asset: a surviving candidate on both is reported as
  one-asset corroboration with explicit shared-data caveat, never as two
  independent confirmations.
- No promotion to shadow, paper, live or orders — ever, from this cycle.
- The only forward path a passing candidate earns is a prospective-validation
  successor cycle. Verdict ceiling: `DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_
  VALIDATION`.

## 3. Cycle phases

```text
P0   plan -> registry hygiene -> researchctl register -> integration
     worktree (.worktrees/phase-strategy-v1/integration,
     orca/phase-strategy-v1-integration). Root checkout is never a lane.
P1   SELECTION RUBRIC FREEZE (§13 rubric + §4 eras/folds template + §5 phase
     contract + §6 proposal contract) committed on the integration branch
     BEFORE any lane is dispatched; WAVE_SHA = that commit.
P2   THREE outcome-blind lanes dispatched from WAVE_SHA (§3.1). Each lane:
     data gate (§9) -> phase-rule freeze + census (§5) -> proposals (§6) ->
     tests -> commit + structured handoff. No PnL path exists in lane code.
P3   A1 sequential integration (one lane at a time, targeted tests per pick),
     eligibility adjudication (§13): floors, PIT audit, ancestry rho,
     turnover/cost ceiling — all BEFORE any PnL.
P4   FREEZE: eligible candidate list + arms + folds + baselines + cost tiers
     + gate thresholds + budget, committed as freeze files with digests.
P5   A7 PRELAUNCH fresh-context audit (§16.1).
STOP-1 OWNER GATE (§16.2): report + wait for the exact GO phrase.
P6   scored run under the machine-wide heavy lock; full denominator (§17).
P7   independent reproduction (byte-compare) + A7 terminal fresh-context.
P8   close per §32 two-half close; verdict exactly one of §18.
```

### 3.1 Lanes

| Lane | Cell | Worktree | Branch |
|---|---|---|---|
| L1 | BTC_H1 | `.worktrees/phase-strategy-v1/lane-btc-h1` | `orca/psv1-lane-btc-h1` |
| L2 | BTC_H4 | `.worktrees/phase-strategy-v1/lane-btc-h4` | `orca/psv1-lane-btc-h4` |
| L3 | SPY_D1 | `.worktrees/phase-strategy-v1/lane-spy-d1` | `orca/psv1-lane-spy-d1` |

One agent per lane, fresh context, outcome-blind (§7.3), separate ownership,
no cross-lane reads of another lane's tree; the ONLY shared inputs are this
plan and the frozen data identities (§9). All three lanes are dispatched from
the same WAVE_SHA.

## 4. Eras and folds (pre-committed before any PnL exists)

Era boundaries are fixed from public market-calendar anatomy BEFORE lanes run;
no era is chosen or moved after any PnL is visible (none exists pre-GO).

### 4.1 BTC cells (UTC clock; halving-cycle anatomy)

```text
ERA-B1 post-halving expansion I      2020-01-01 → 2021-04-30
ERA-B2 contraction I                 2021-05-01 → 2022-12-31
ERA-B3 post-halving expansion II     2023-01-01 → 2024-12-31
ERA-B4 current regime                2025-01-01 → data end
```

Anchors: halvings 2020-05-11 / 2024-04-20, cycle top 2021-04, bear bottom
2022-12, public calendar constants; era 2020–2024 requires the Vision
extension (§9.1). The sub-window 2025-08-20→2026-08-20 overlaps the frozen
V2 15m catalog (outcome-observed corpus) — disclosed in every artifact.

### 4.2 SPY cell (session clock)

```text
ERA-S1 post-GFC expansion + vol shock   2015-01-02 → 2018-12-31
ERA-S2 COVID crash + recovery           2019-01-02 → 2020-12-31
ERA-S3 post-COVID expansion → 2022 bear 2021-01-04 → 2022-12-30
ERA-S4 2023–2026 expansion              2023-01-03 → data end (2026-09-16)
```

Extension earlier than 2015 ONLY if a valid entitled source is measured
(license + coverage); default is the four eras above. The V2 SPY snapshot
window (2015→2026-09-16) is the outcome-observed corpus — disclosed.

### 4.3 Folds and floors

- Per cell: 4 contiguous outer folds spanning the full post-warmup window;
  era→fold mapping recorded; boundaries land on era boundaries where the era
  count is 4, else an even-bar partition with boundaries recorded. Fold ends
  force-flat; fold attribution reconciliation identity required.
- Warmup: each lane freezes its own indicator warmup (bars), documented; eras
  and floors are evaluated POST-warmup only.
- Sample floors (immutable; owner-confirmed, never silently relaxed):
  - ≥ 20 independent episodes / phase / cell (total);
  - ≥ 3 independent episodes / phase / outer fold;
  - ≥ 100 eligible decisions / phase / outer fold.
  Below any floor ⇒ that phase×cell is `NOT_RUN_THIN_PHASE`, its strategy
  slot is FLAT, and it is reported, not scored. NEVER pool BTC_H1 with
  BTC_H4, or any two cells, to fake sample size.
- Every census reports margin-to-floor per phase×cell×fold, not just pass.

## 5. Phase identification contract (PIT; code-owned; no Jev)

Each lane freezes ONE phase rule for its cell:

1. Deterministic, causal: uses only bars with close time ≤ decision time.
   Decision at bar close; first executable fill at the NEXT bar open
   (≥1 executable bar lag). No intra-bar look-ahead; timezone/DST law fixed
   (BTC: UTC; SPY: XNYS session calendar).
2. Five named outputs exactly: ACCUMULATION, UPTREND, DISTRIBUTION,
   DOWNTREND, TRANSITION_UNKNOWN. TRANSITION_UNKNOWN must be code-owned by
   explicit uncertainty conditions (margin/transition-buffer/insufficient-
   evidence rules), never model abstention, never an LLM.
3. Parameters are round, domain-standard constants (or derived by a frozen
   formula) fixed BEFORE any history is scored; bins from conventions, never
   from PnL (none exists) and never from label-optimization sweeps. A
   documented sensitivity table (±1 parameter notch ⇒ label agreement %) is
   part of the freeze — reported, not optimized.
4. Label reliability census (no PnL): per era×fold: occupancy share, episode
   count (maximal contiguous runs), dwell distribution (min/median/max/
   quartiles), transition counts, UNKNOWN share, longest UNKNOWN run, and
   margin-to-floor. BTC_H1 and BTC_H4 censuses are computed independently.
5. The cached V2 Jev labels are NOT an input to any of this. A lane may cite
   their existence for ancestry context only; it may not read them.

## 6. Proposal contract (≤1 strategy per data-sufficient phase)

For each phase that meets the §4.3 floors on that cell, the lane proposes AT
MOST ONE strategy — chosen by economic mechanism, never by scanning PnL. For
phases below floor or mechanistically ambiguous: `NO_ELIGIBLE_PROPOSAL` or
`RESEARCH_ONLY` + default FLAT. DISTRIBUTION carries a STRICTER default:
without an explicit, evidenced forced-counterparty mechanism, DISTRIBUTION
defaults to FLAT (post-advance tops are where late longs get handed inventory;
no naked-short authority exists for SPY).

Every proposal freezes all of:

```text
mechanism         who is forced to trade (or is slow/late) in this phase,
                  and why the effect can exist after costs
observable        which data/observable measures the mechanism (PIT)
phase_rule        the cell's §5 rule; the strategy trades only while the
                  phase state is active (gated book), else FLAT
direction         BTC: long/short/flat allowed; SPY: long/flat ONLY
entry/exit        exact rules, indicator params, clocks, warmup
holding/sizing    min/max hold, fraction 1.0 (V2 accounting), stop policy
execution         decision at close, fill next executable open, no mid-bar
costs/capacity    cost model per §9; capacity narrative + turnover estimate
churn law         frozen min-dwell ≥ phase-rule dwell margin; no
                  unnecessary close-reopen (same-direction label noise must
                  not produce fills); explicit no-op law
control           ONE preregistered falsification control able to kill the
                  hypothesis (phase-shuffled matched control with Q-11
                  movement validation, or clock-only control, or neighbour);
                  control semantics fixed before scoring
failure_mode      expected failure interpretation, preregistered
identity          family_id PSV1-<CELL>-<PHASE>-<MECH>, arm_config_digest
```

## 7. Forbidden ancestry (measured-dead on this program; rho bar 0.20)

1. **Reopening laws inherited**: no retry of the V2/RSMV1 mapping/routing/
   specialist class with new parameters (RSM-V1 §reopening). Specifically
   FORBIDDEN as candidates: the RSM-V1 specialist library (ACC_RANGE_MR,
   ACC_FLAT_BREAKOUT_WAIT, UP_TREND_SLOW_LONG, UP_LONG_RISKOFF_EXIT,
   DIST_FLAT, DIST_SHORT_BTC, DOWN_SHORT_BTC, DOWN_FLAT_RISKOFF) and all V2
   arms (JEV_ONLY, DETERMINISTIC router, DETERMINISTIC+JEV_CONFIRM,
   RANDOM_MATCHED) — renamed, re-clocked or not. A phase-gated variant of
   any of these is the same mapping class and is vetoed at integration.
2. **Same-asset dead mechanisms** (a candidate whose signal-series |rho|
   with an applicable frozen dead shadow EXCEEDS 0.20 is VETOED before
   scoring; |rho| ≤ 0.20 passes novelty — the program-wide convention, same
   bar as §13 E3; canonical list
   `research/wayfinder/FAMILY_FAILURES.jsonl`, program-level):
   - crypto/BTC: close-displace-fade; rev24-style short-horizon reversal
     per-leg forms; run_imbalance; amihud-illiquidity proxy; OI-level and
     OI-share/stoch; generic DVOL shock; pair spread-trend composites.
   - stocks/SPY: relative-breadth rotation (QQQ/SPY z-of-ratio anchors);
     vol-state/bear-trap event-conditional books; filing-event/amendment-
     cadence families (also data-dead); dividend-transition books.
   Each lane runs the measured rho of its candidate's daily signal series
   against the applicable frozen shadows and records it; A1 re-measures at
   integration. rho is a correlation of information content (V2 D2
   convention), computed pre-PnL from signals, not returns.
3. **Outcome-blindness of lanes**: proposal lanes must NOT read any artifact
   bearing predecessor strategy PnL: `research/wayfinder/MAP.md`,
   `MECHANISM_ATTRIBUTION_REPORT*`, V2/RSMV1 terminal reports, tier files,
   `SURVIVORS.md`, or any scored ledger. Class-level findings needed for
   design live in §1 of this plan without strategy-level magnitudes. The
   ancestry LIST above (family IDs, mechanism classes, no PnL) is the only
   failure knowledge lanes receive. Violation ⇒ lane output rejected.
4. **Never**: Jev labels as truth; old PnL as rule-selection input; BTC
   H1-vs-H4 selection by PnL; BTC_H1+BTC_H4 claimed as independent.

## 8. Baselines (frozen now; reference computations, not candidates)

All computed on each cell's own grid, fold force-flat, same cost tiers:

```text
CASH               flat everywhere (0 by construction)
ALWAYS_ON_LONG     long from first post-warmup bar to window end, re-entered
                   at each fold start (fold force-flat); BTC perp long,
                   SPY long
ALWAYS_ON_TREND_LF long iff close > SMA200 of the cell clock (200×H1,
                   200×H4, 200 sessions), else flat
SPARSE_RISK_OFF    long unless stressed: flat while trailing drawdown from
                   the running window high > 30% (BTC) / > 20% (SPY);
                   re-entry when drawdown ≤ 10%; min-hold 5 bars (sparse by
                   construction; round frozen constants, disclosed)
```

G3 compares candidates against ALL FOUR on the same cell at 1.0x. SPY
baselines are long/flat only.

## 9. Data gates (P0, per lane, before census)

### 9.1 BTC_H1 / BTC_H4

- Source: Binance Vision keyless USDT-M futures klines, BTCUSDT-PERP
  (instrument identity = the V2 catalog instrument). 1h monthly zips
  2020-01→last complete month (HTTP 200 probed) + daily/current-month tail
  stitching to data end; every zip sha256-pinned into a manifest with URL,
  bytes, digest; deterministic re-retrieval verified on a sample.
- Integrity law: OHLC sanity (high≥low, close∈[low,high]), zero-volume bar
  flags, gap census vs a 1h calendar (UTC), duplicate-ts rejection
  fail-closed.
- Cross-check (AMENDED — see Amendments log A1): the frozen 15m catalog
  (sha 81d4f147) resampled to 1h was a mandatory equality gate in the
  original text. MEASURED OUTCOME (lanes L1/L2, independent, 2026-09-23):
  the check FAILED and forensics locate the defect in the catalog reference
  itself — close corr 0.999969 with correct +0h alignment, both decodes
  VWAP-sane, yet catalog volume scale is ~12x off at the median (per-day
  ratios 0.01–32x) and close diffs reach ±6,800; L2 independently found the
  same catalog non-corroborative on all 2,189 shared buckets while the
  native Vision 4h shadow matched 14,607/14,610 at 1e-9. ADJUDICATION (A1,
  pre-outcome): the catalog is not a usable bar record and cannot serve as
  an integrity reference; the equality gate is reclassified
  DIAGNOSTIC_REFERENCE_FAILED (forensics frozen in L1 `data/manifest.json`
  `cross_check_15m_catalog` / `cross_check_incident`). BTC integrity is
  instead anchored by: zero gaps/duplicates/OHLC violations; sha256-pinned
  deterministic re-retrieval; the native-4h shadow match; and the 0.999969
  price-tracking diagnostic. A future mismatch remains STOP-class if it
  ever points at the VISION series rather than the catalog. No smoothing.
- H4 derivation: H4 bucket = floor(open/4h) UTC (00/04/08/12/16/20),
  complete iff exactly 4 aligned H1 bars (RSM-V1 census law); partial
  buckets excluded from floors. L2 (BTC_H4) additionally cross-checks the
  aggregated H4 against native Vision 4h klines (shadow, tolerance) —
  derivation from the shared H1 manifest is the scored representation.
- PIT disclosure: Vision klines are retrospective exchange snapshots
  (retrieved_time 2026-09; no per-bar publication timestamps). Convention:
  bar knowable at its close + one executable-bar latency. This matches the
  accepted convention of prior Vision-based cycles and is disclosed in every
  artifact.

### 9.2 SPY_D1

- Reuse the frozen snapshot sha 3fd229f9 (read-only; no re-pull); re-verify
  digest at freeze; document session calendar, splits/dividend adjustment
  semantics of the snapshot as-is (frozen bytes), and the exact close/open
  timestamp convention MEASURED from the file.
- Long/flat only. Extension pre-2015: NOT_RUN unless a measured, licensed
  source exists; default stays the §4.2 eras.

## 10. SPY Tuesday-staleness gate (BLOCKING; the V2 defect class)

V2's SPY losses were dominated by a frozen-law interaction: SPY session
closes stamped next-midnight × a staleness rule (decision older than 2 regime
periods ⇒ FLAT) force-flattened open positions on every Tuesday open and
re-entered after — weekday-dependent churn generated by the clock convention,
not by any market view. This cycle deletes the defect class:

1. No staleness/force-flat law exists in PSV1 (no external decision stream;
   labels are computed per bar at close, §5). Any candidate that carries any
   age-based flat rule must express it in SESSIONS with an explicit frozen
   hysteresis — default is none.
2. Calendar law fixed and measured: SPY decision at session close (16:00 ET
   value), executable at next session open; BTC decision at hourly close,
   next hourly open. Bar timestamps documented from the measured file, not
   assumed.
3. MANDATORY regression (runs in every lane touching SPY, re-run at
   integration and in the scored run): weekday-rotation replay — relabel the
   calendar by shifting session dates +1..+4 days and assert trade count and
   per-fold signal occupancy are INVARIANT (no weekday-dependent exits);
   plus an explicit "Tuesday test" reproducing the V2 mechanism shape and
   asserting ZERO force-flats attributable to weekday. Fail ⇒ SPY scoring
   BLOCKED (`BLOCKED_SPY_CALENDAR_DEFECT`), no GO consumed.
4. A7 prelaunch re-verifies this gate from source, not from this text.

## 11. Turnover / cost-ceiling feasibility (pre-PnL)

Before any candidate is eligible, from the census and the frozen rules
(signal-path dry-run: counts and hold-time distributions ONLY — no returns,
no equity, no PnL path exists in lane code):

- expected trades per era×fold; round-trip cost at 1.0x (BTC 12 bps +
  funding; SPY 20 bps) vs the proposal's argued gross edge per trade with a
  stated margin; a candidate whose measured cadence makes 1.5x costs
  arithmetically unsurvivable at any plausible edge is struck at integration
  (documented arithmetic, disclosed as struck-by-ceiling, no PnL used);
- churn law sanity: position switches must be a small fraction of phase-rule
  transitions (the RSM-V1 anti-churn lesson); unnecessary_close_reopen must
  be structurally zero (no-op law test).

## 12. Trial identity and denominators

Every scored arm: cycle_id PHASE-STRATEGY-V1, cell, family_id, arm_id,
arm_config_digest, data manifest digest, code_freeze_sha, cost_tier, fold
contract. Observed denominator counts every computed outcome including
publication failures; published denominator only successes; both reported at
every checkpoint (P-9). Budget max 15; budget cells consumed only by
phase-candidates that actually run post-GO.

## 13. Selection rubric (frozen BEFORE lanes return; no PnL anywhere in it)

A phase-candidate is ELIGIBLE iff ALL pass at integration:

```text
E1 floors      §4.3 floors met on that phase×cell (margin reported)
E2 PIT         phase rule + strategy pass the PIT/no-lookahead audit
E3 ancestry    rho vs applicable dead shadows ≤ 0.20; not §7.1-forbidden
E4 feasibility §11 ceiling arithmetic passes; churn law sane
E5 identity    contract complete (§6); SPY direction long/flat only
E6 calendar    §10 gate PASS (SPY); no weekday-dependent behavior
```

Eligible candidates are ALL scored (full denominator, no selection by
anything). Below floor / struck candidates are reported as
`NOT_RUN_THIN_PHASE` / `STRUCK_BY_CEILING` / `ANCESTRY_VETOED` with reasons.

## 14. Implementation + tests

Namespace `psv1` under `research/control/phase_strategy_v1/` in the cycle
worktree; per-lane subnamespaces `lane_btc_h1|lane_btc_h4|lane_spy_d1`.
Mandatory tests (hand-computed fixtures, per lane):

- phase-rule golden: named outputs on synthetic paths; UNKNOWN assignment;
  causal/no-lookahead mutation (future-bar perturbation must not change past
  labels); timezone/DST boundary; warmup exclusion;
- census determinism + margin-to-floor calculator + thin-phase → FLAT;
- strategy golden: one-event entry/exit; next-bar fill; costs charged
  exactly once per fill; funding signed (BTC); fold force-flat;
  concentration and turnover counters; no-op law fixture (phase label
  change with same direction ⇒ zero fills);
- SPY lanes: the §10 weekday-rotation + Tuesday regressions;
- BTC lanes: Vision manifest digest chain + overlap cross-check vs the
  15m catalog; H4 derivation completeness law (L2);
- cost-tier sweep exactness 1.0/1.5/2.0 multiplication points;
- S1 denial + broker-surface scan + sanitized-dry-run hygiene.
```

Full pytest of touched suites only (heavy-lock discipline for the full suite
is a post-integration event, never in a lane).

## 15. Scored run contract (post-GO only)

One atomic process under the machine-wide heavy lock; ALL eligible
candidates + 4 baselines + controls across ALL THREE cells in the same run;
no mid-run stopping on ugly numbers; no rule/parameter edit after any PnL is
visible (bugs post-freeze follow §24 remediation law with a new freeze);
reporting per cell × phase × era: trades, gross, fees, slippage, funding,
net, drawdown, fold concentration, holding time — each against the §8
baselines; NOT_RUN clearly separated from FAIL everywhere.

## 16. Gates

### 16.1 A7 prelaunch (fresh-context; before STOP-1)

Audits from bytes and source: plan/freeze chain digests; data manifests +
PIT disclosures; phase-rule causality; census arithmetic + floor margins;
ancestry rho re-measurement; rubric integrity (no PnL anywhere pre-freeze);
Tuesday gate; trial identity; budget; S1 seal; no broker/order surface;
baseline definitions sane; zero unresolved HIGH/CRITICAL. Verdict:
`AUTHORIZED_FOR_DISCOVERY_STOP` or `REMEDIATION_REQUIRED` (+ remediation
loop precedent: refusals are normal).

### 16.2 STOP-1 — mandatory owner gate

After A7: STOP and report to owner (plain language): what each cell/phase
offers; which phases are thin (NOT_RUN); which candidates froze; costs,
budget, folds; how the Tuesday defect class is deleted; why this is not a
rescue of V2/RSMV1; the exact GO phrase. WAIT for the owner to type, at this
gate, verbatim: `GO PHASE STRATEGY V1 SCORED EXECUTION`. No other phrase
consumes; this prompt session is NOT a GO.

### 16.3 Candidate gates (per candidate, per cell; all must PASS)

```text
G1  net > 0 at 1.0x costs
G2  net > 0 at 1.5x costs
G3  beats ALL §8 baselines on that cell at 1.0x
G4  fold robustness: positive in ≥3/4 folds OR best-fold-removed net > 0
G5  no single fold contributes >50% of positive net
G6  preregistered control does not out-earn the candidate (control
    out-earning ⇒ kill; invalid control null ⇒ disclosed, rest on G1–G5)
G7  turnover within frozen ceiling; zero unnecessary close-reopen
G8  reproduction byte-match (P7)
G9  A7 terminal clean (0 unresolved HIGH/CRITICAL)
```

ALL-PASS on any candidate ⇒ ceiling verdict
`DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION` (never OOS, never
deployable, no orders).

## 17. Reproduction + terminal

Independent reproduction at the exact code/data freeze (detached twin):
byte-compare per-arm tier artifacts; ANY drift ⇒ TECHABORT-class incident,
never silent repair. A7 terminal fresh-context recompute: ancestry, gates
from source, accounting reconciliation (gross/net pairing per vehicle),
denominators, S1/boundary scan, strongest allowed label.

## 18. Terminal verdicts (exactly one)

```text
PHASE_STRATEGY_V1_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION
PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE
PHASE_STRATEGY_V1_NO_ELIGIBLE_PROPOSAL
PHASE_STRATEGY_V1_BLOCKED_DATA_OR_SELECTION
PHASE_STRATEGY_V1_BLOCKED_SPY_CALENDAR_DEFECT
TECHABORT
```

## 19. Boundaries

No push from lanes; no merge to main; registry only via researchctl; one
heavy worker machine-wide (light census jobs exempt if <5 min CPU / <2 GB —
anything larger takes the lock); never kill foreign processes; S1 sealed;
no orders; no credentials in logs; V2/RSMV1 artifacts byte-untouched; root
checkout is bootstrap/owner space; worktrees `.worktrees/phase-strategy-v1/*`.
Turn-scope law: pre-GO turns may implement, test, census, freeze and audit —
they may NOT run the scored backtest.

## 20. Amendments log

### A1 (2026-09-23, A1 controller, pre-outcome, pre-A7)

1. **§7.2 rho-bar wording fixed.** Original text inverted the program
   convention ("proposals within |rho| ≤ 0.20 … VETOED"), contradicting
   §13 E3. Corrected: VETO iff signal-series |rho| with an applicable dead
   shadow EXCEEDS 0.20; ≤ 0.20 passes. Both BTC lanes applied the correct
   convention in their measurements (L1 worst 0.082, L2 worst 0.168); L3
   self-killed a +0.559. No measurement changes; wording-only defect caught
   by lane L1 and fixed before any integration or scoring.
2. **§9.1 catalog equality gate → DIAGNOSTIC_REFERENCE_FAILED.** The
   mandatory 15m-catalog-vs-Vision equality check failed; independent
   forensics from two lanes locate the inconsistency in the catalog
   reference itself (volume scale ~12x median off, close diffs to ±6,800 at
   0.999969 close correlation), while the native Vision 4h shadow matches
   14,607/14,610 at 1e-9. Ruling + replacement anchors are written into
   §9.1. Evidence: L1 `lane_btc_h1/data/manifest.json` cross-check incident
   block; L2 data-gate disclosure. Eras, folds, floors, costs, gates:
   UNCHANGED.
3. **Lane handoff envelopes.** L2's handoff JSON was left uncommitted in its
   worktree (disclosed in its handoff `tree_status`); A1 commits it during
   integration with attribution. L1/L3 committed their handoffs on their
   branches.
