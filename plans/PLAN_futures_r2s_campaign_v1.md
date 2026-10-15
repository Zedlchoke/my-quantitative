# PLAN — FUTURES-R2S-CAMPAIGN-V1 (research-to-strategy campaign)

Status: REGISTERED (ACTIVE_LIGHT) · Owner authorization: verbatim dispatch
2026-10-15 ("OWNER AUTHORIZATION — FUTURES RESEARCH-TO-STRATEGY PROGRAM",
sections A–J). Campaign ID: `FUTURES-R2S-CAMPAIGN-V1`. One Lead session
owns this cycle (P-17). Terminal outcomes preregistered below (§I).

Measured intake base: root `main` @ the commit that carries this plan;
registry row appended by `researchctl cycle register` in the same commit
window (plan + registry atomic). Worktree:
`.worktrees/futures-r2s-campaign-v1/integration`, branch
`orca/futures-r2s-campaign-v1-integration`.

---

## 0. Mission and the one-paragraph spirit

Chuyển toàn bộ lịch sử futures research thành (1) một bản kiểm toán trung
thực (FAILURE_ATLAS), (2) một hệ thống research-to-strategy có thể tái sử
dụng, (3) tối đa 2 concept phát triển trên ES/NQ 2010-06→2022-12, (4) một
trading-agent decision engine + simulator **không có đường gửi lệnh**, và
(5) một next-gate packet trung thực. Không cam kết tạo strategy có lợi
nhuận. Kết quả âm với bằng chứng đầy đủ là thành công (Q-16). Số smoke
chỉ dùng để kill, không dùng để chọn (P-15).

## 1. Measured state at registration (evidence, not narrative)

- Root `main` live (other lanes commit concurrently: WEATHER-TEMP-PROB-V1
  registered 2026-10-15; SRML DEV lane committing on its own branch).
  Every root commit by this campaign: re-anchor `git -C` + atomic
  pathspec staging (P-19, P-10).
- Heavy lock FREE at intake (researchctl locks inspect). Acquire for every
  fit/heavy job; `NOT_RUN_RESOURCE_CONFLICT` otherwise. Never kill the
  foreign `research.papertrade_exec.ops_service` process or any lane.
- Dirty root paths (classified, untouched):
  `plan_ml.md` = OWNER_DRAFT (DRAFT_FOR_OWNER_REVIEW, document-only,
  untracked by owner intent); `research/control/FUTURES-VSA-ESNQ-V1-postCAS/`
  = LANE_EVIDENCE copy (fault-suite log @ scored head dd5b8e2e);
  `research/control/weather_pred_prep_v1_draft/` = OWNER lane prep;
  `.my-quantitative-data/` = owner data dir (empty at root path).
- Futures cycles — ALL TERMINAL, GO phrases DEAD:
  - FUTURES-ES-PB1-V1 REJECT_ALL 24/24 (K2, PB1 family dead, re-param
    forbidden) @ prep/futures-es-reg-20261004 935556cf.
  - FUTURES-NQ-V1 29/29 (F1/F2 DEAD_K2, F3 NO_ELIGIBLE) and
    FUTURES-FX-V1 73/73 (6E/6B/6J six families DEAD_K2) @
    prep/futures-5sym-prescored-20261005 32b6d3c4.
  - FUTURES-ES-F2-V1 D2_BLOCKED_DATA_VETO 19/38 (pin mismatches; rho 1.0
    member) @ prep/futures-es-f2-reg-20261007 7f2cf211.
  - FUTURES-VSA-ESNQ-V1 REJECT_ALL 8/8 (all 8 identities FAIL G1/G2,
    negative both symbols; G6 primary>control +10–22$/day but both
    negative) @ orca/vsa-esnq-v1-integration 55962650. S0 scored window
    2010-06-06..2022-12-31; S1 (2023+) SEALED.
  - FX-FUTURES-FRONTIER-V1 BLOCKED_TRANSPORT 0/0 (CME estate SNI-filtered
    — standing program-level environment fact, L-FXFF-1) @ 7decfce3.
- Coexisting lane (read-only for this campaign): SRML DEV wave 2,
  worktree `.worktrees/srml-dev-20261015/integration`, branch
  `srml-dev-20261015` — wave 1 COMPLETE (24 configs/576 fits,
  DEVELOPMENT_CANDIDATE=0, POPULATION_SHIFT_FINDING z0.05), wave 2
  COMPLETE (4 configs B-z05/C-z05/B-z10/C-z10, 96 fits; policy_spec
  prepared, execution simulation NOT run). All committed with
  SHA256SUMS_dev.txt. Its `POLICY_BACKTEST_READINESS.md` binds any policy
  cycle: re-pin own cost book, fill-law freeze, FILL_UNVERIFIED_PRICE_PROXY
  declaration, baselines, and the DEVELOPMENT_OUTCOME_EXPOSED label.
- Data authority for development: 1m Databento GLBX.MDP3 ES/NQ
  2010-06-06→2026-09-30 at
  `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/`
  (ES 8,710,520 rows; NQ 7,330,320), manifest
  `data_hashes_1m.csv` (41 files, sha256 `a1e1a3f1…`, cross-verified by
  PREP-FUTURES-VIDSWEEP-20261010 "matched 41 / mismatched 0").
  6E/6B/6J/6A only 2020-01→2026-09. IBKR per-contract probe surface
  (10 syms) = SIGNAL_RESEARCH_READY only. **Outcome exposure boundary:
  development may read outcomes 2010-06→2022-12 ONLY. The 2023+ files
  exist on disk but are S1-sealed for this campaign — no loader call may
  open a row with ts ≥ 2023-01-01 (enforced in code, proven by test).**
  Terminal-cycles' outcome numbers are readable as forensic evidence but
  are NOT训练 corpus: no bulk import of exposed outcome tables into new
  training data (§F-7).

## 2. Universe and authority scope (owner §B)

- ES primary, NQ replication (equity-index branch). 6E/6B/6J: audit +
  data/cost mechanism preparation only (their scored surface is DEAD_K2 —
  no new direction families on FX futures this campaign). 6A: PARKED —
  no data read, no feature use.
- Allowed development window: ES/NQ 2010-06→2022-12 (exposed). 2023+/S1
  sealed. FX (spot and futures) new outcomes NOT authorized.
- No purchases, no subscription changes, no TWS/collector config changes,
  no push/merge, no S1, no orders. IBKR 127.0.0.1:7497 read-only
  readiness probe ONLY (separate clientId ≥ 50, never writes, never
  modifies TWS state; handshake-unverified today per SRML
  FEED_READINESS_IBKR — probe failure records NOT_RUN, never retried in a
  loop).

## 3. W0 — Historical audit (owner §C)

Deliverable: `research/control/FUTURES-R2S-CAMPAIGN-V1/FAILURE_ATLAS.md`
+ `EVIDENCE_INDEX.json`. Census = every futures cycle (§1 list) + SRML
PREP/DEV + shared-code incidents (INC-registry-bundle-0d1fe426,
INC-SHA-TYPED class, INC-1 lane-log write, INC-DT100-1 spread marking,
P-18/P-19 operator-error class) + cross-asset incidents that bind futures
work (L-SAMV1-1/2/3, P-18 ERP1 PIT seam, µs-stamp truncation L-TRACKB1-1,
P-23 empty-population, P-31 floor geometry, P-32 cost-frequency).

Law: every conclusion row carries path + measured SHA + authority + data
surface + budget + verdict; missing artifact ⇒ `NOT_VERIFIED` (never
report-as-evidence). Failure taxonomy — five classes, mutually exclusive:
IMPL_BUG (implementation invalidates result) / HONEST_NEGATIVE (ran
right, hypothesis failed) / DATA_OR_AUTHORITY_GAP / UNDERPOWERED /
PROCESS_OVERHEAD (cost without reliability gain). Atlas groups (owner's
10): data/calendar/roll/timestamp/unit; lookahead/availability/episode
aggregation; exposure/split/leakage; accounting/ledger/retry/publication;
cost/fill/sizing; power/sample/concentration; baseline/control/estimand
confounding; model selection/multiplicity; forecast→policy→execution
mismatch; authority/registry drift. Per failure: evidence → root cause →
affected claims → repair/status → preventive check → operating cost of
the check. Explicit non-goals: not every loser is a bug; no
"invert-the-loser" rescue reasoning anywhere.

## 4. W1 — System layers (owner §D)

Build-in-worktree, reuse-first, no repo rewrite, no retrofit of frozen
cycles. Each layer = small adapter + targeted tests aimed at an incident
class that actually happened:

- L1 data-access adapter: manifest-verified read-only 1m loader with the
  2023+ seal enforced in code (`SealedWindowRefused` on any ts ≥
  2023-01-01) — incident class: µs-stamp truncation, silent skip (W1 trap,
  L-TRACKB1-1).
- L2 PIT snapshot util: available_at = bar_end (MODELED_AVAILABILITY,
  SRML law); lag-mutation fixture — incident class: P-1/P-18 lookahead.
- L3 episode-engine adapter: consume SRML committed episode CSVs
  (sha-pinned copies in this cycle's control dir) + per-level grouping —
  incident class: episode aggregation ambiguity (PB1/VSA day laws).
- L4 bounded runner: config registry, JSONL fit ledger, hard counter
  assert ≤24 behavioral configs; every fit/retry logged — incident
  class: denominator drift (P-9), retry accounting.
- L5 chronological selection: 12 annual eval folds 2011–2022, train =
  strictly-prior years, purge = label horizon + embargo, inner-only
  tuning; ES/NQ never pooled for claims; session-block bootstrap —
  incident class: fold leakage, concentration (P-24-era kills).
- L6 policy simulator: pure `decide()` (SRML policy_spec pattern), no
  market-data access inside decide, position state machine, limits,
  intent journal — incident class: forecast→policy mismatch (P-33/P-34).
- L7 cost/fill interface: REFERENCE cost bands only (VSA COST_PIN ES/NQ
  declared as REFERENCES, never evidence); FILL_UNVERIFIED_PRICE_PROXY
  posture — incident class: Q-8 stated-vs-measured.
- L8 append-only journal + reconciliation (hash-chained rows) — incident
  class: publication/finalization (P-16).
- L9 risk controller: max 1 position, session exposure cap, per-day loss
  halt, stale-data guard (no decisions on gaps > N minutes), kill switch.
- L10 broker boundary: `BrokerAdapter` interface with a REFUSING
  implementation (`NoOrderBroker`); proof test asserts zero order-send
  paths exist in the allowed mode.

## 5. W2 — Strategy design (owner §E)

≤6 concept dossiers in `w2/CONCEPT_DOSSIERS.md`, each: actor/mechanism,
competing null hypothesis, PIT observables actually owned + data gaps,
concrete decision vocabulary (LONG/SHORT/WAIT/NO_TRADE/EXIT),
baselines/controls, sample/power + after-cost hurdle arithmetic, ancestry
to old families, falsification conditions, learned-vs-frozen parameter
split. **Frozen ranking rubric** (committed before any selection):
gates G-A ancestry clearance (measured rho < 0.20 vs fenced families, or
adjudicated distinctness), G-B PIT fundability on existing data only,
G-C non-duplication of SRML's 28 committed configs (appendix A); then
scored axes: S1 power (episodes/fold ≥ 30), S2 after-cost hurdle (expected
per-episode favorable excursion ≥ 2× reference RT cost band), S3 mechanism
specificity (declared causal control), S4 reuse/implementation cost.
Concept shortlist (may be killed, not force-filled to six):

- K1 LEVEL-MEMORY EPISODE OUTCOME (ES/NQ): directional outcome of S/R
  episodes conditioned on the *level's own PIT history* (prior episode
  outcomes at the same level, level age, prior rejection count) — new
  information axis vs SRML C/P sets (touch_ordinal is within-episode
  only). Reuses SRML census populations; baselines cite SRML committed
  numbers, never refit.
- K2 RISK-CONDITIONED ABSTENTION (vol/risk conditioning): hysteresis
  vol-state + confidence-state abstention policy over episode forecasts;
  decision space includes NO_TRADE/WAIT; evaluated behaviorally
  (coverage/precision/abstention counts), zero PnL claims.
- K3 NQ–ES RELATIVE DISLOCATION: beta-hedged NQ−β·ES intraday spread,
  trailing-only PIT beta, band-entry/timeout-exit episode book;
  clairvoyant delay-0/delay-1 pair (Q-4) + clock-only shadow (Q-7).
- K4 SINGLE-SESSION RECLAIM CONFIRMATION: failed-breakdown reclaim with
  confirmation on ES/NQ — explicitly folklore-test; expected ancestry
  pressure from STOCKS-NG6 event-conditional class and FXFV2-A4-P2
  placebo; admitted only to be measured and likely cheap-killed.
- K5 EVENT-WINDOW ABSTENTION (risk-side only): CPI/NFP/FOMC window
  NO_TRADE conditioning from evidenced calendars; no direction claim.

Fences: DEAD_K2 families (PB1 overnight pair, NQ F1/F2/F3, 6E/6B/6J
F2/F3) are not revivable by rename/threshold/cadence; VSA sweep/BOS/iFVG
descendants fenced (K2 REJECT_ALL both symbols); S/R *behavioral
classification* is SRML's live lane — this campaign touches S/R only via
new feature axes (level memory) and policy layers, never re-running
z/b/h/λ variants of their 28. Any fenced-descendant study requires a
written amendment/adjudication BEFORE any computation of that branch.

Selection: rubric applied + committed at `w2/SELECTION_FREEZE.json`;
max 2 concepts into development; honest zero accepted.

## 6. Development law (owner §F)

- Total cap **24 NEW behavioral configurations for the ENTIRE campaign**
  (all concepts, both symbols; registry budget unit = 1 configuration).
  A configuration = one frozen (feature-set × parameters × symbol)
  behavioral model identity fit over the fold law. Every fit, prediction
  batch, evaluation and retry logged in the fit ledger; budget counter
  enforced in code (L4) and mirrored to the registry at close.
- No configuration duplicating SRML's committed 28 (appendix A list);
  overlaps reuse their committed evidence instead.
- Nested chronological selection with purge by label horizon + episode
  boundary; ES/NQ dependence kept separate; parent-session clustering in
  every reported uncertainty (session-block bootstrap); outer folds on
  the exposed surface are NEVER called untouched (label:
  DEVELOPMENT_OUTCOME_EXPOSED everywhere).
- After budget exhaustion: no further search wave. Max 2
  DEVELOPMENT_CANDIDATE outputs; zero allowed.
- Synthetic tests run before any real-data fit (fixture: golden features,
  one-bar lag, no-lookahead mutation, purge geometry, seal refusal,
  config-counter).

## 7. Trading agent + simulator (owner §G)

`agent/` in the campaign worktree: deterministic decision engine with
input schema + feature cutoff + model/version pins; calibration report +
uncertainty; frozen context→action mapping (no LLM in the loop, no
recent-N rewrites); position state machine (FLAT→ARMED→ENTERED→EXITED,
WAIT/NO_TRADE default on missing evidence); limits (1 position, session
exposure cap, daily loss halt, stale-data); intent journal recording
accepted/blocked/deferred with reasons; idempotent restart (decision_id =
hash(state-vector, pins)); kill switch; reconciliation report;
research/simulation/broker adapters strictly separated with the broker
adapter refusing every path (no-order proof, §4-L10).
Simulation = synthetic fixtures + replay of historical *features* in
shadow mode (decisions logged, no outcome access in the decision path).
**Strategy PnL/scored backtest is NOT run in this campaign** — it is the
next-gate packet (§I): full plan/identity/budget/cost-PIT/engine/synthetic/
dry-run/independent-audit chain plus owner GO, per repo law; never
bypassed by calling it "simulation".

## 8. Small-account realism (owner §H)

`h/CAPITAL_FEASIBILITY.md`: MES/MNQ mapping evaluated as *components to
be evidenced*, never as scaled ES/NQ PnL. Components listed with measured
status each: margin (UNMEASURED — CME transport-blocked; IBKR whatIf
requires handshake that is UNVERIFIED), stop/gap risk (measurable only
with cost/fill authority), drawdown profile (from development stats
only, labeled MODELED), transaction costs (REFERENCE bands only), min
size (contract spec DOCUMENTED_CANDIDATE). CFD quotes/spread/financing:
needs separate evidence; none gathered this campaign.

## 9. Execution, stop rule, owner gates (owner §I)

Order: W0 atlas → W1 layers+tests → W2 dossiers+selection freeze →
DEV (bounded) → agent/simulator → H → A7 verifier → deliverables.
Blocker on one branch ⇒ continue independent valid branches; no routine
technical question returns to owner. OWNER GATES (not exercised this
campaign): outcome 2023+/S1; new registrations beyond this one; typed
GO/scored; purchases/subscriptions/account terms; prospective activation;
paper/live orders; push/merge. At any gate: complete all independent
work, then present a concrete packet (decision required, evidence,
options+consequences, run path, budget/cost, impact) — never a vague
"should we continue".
Terminal outcomes (preregistered):
- T1 `CAMPAIGN_COMPLETE_WITH_FINDINGS` — atlas+architecture+dossiers+
  bounded dev+agent delivered; 0–2 candidates; every candidate labeled
  DEVELOPMENT_OUTCOME_EXPOSED, never an edge claim.
- T2 `BLOCKED_DATA_OR_AUTHORITY` — a hard data/authority wall stops dev;
  partial deliverables still land.
- T3 `NO_CANDIDATE_HONEST_ZERO` — budget consumed, selection empty.
- Gate-hit branches pause with a packet instead of a terminal.

## 10. Independent audit + deliverables (owner §J)

Fresh-context verifier (A7) audits from bytes at final HEAD: recompute
atlas row sampling, config counter, seal enforcement, no-order proof,
journal integrity; writes audit only, repairs nothing.
Deliverables: (1) this CAMPAIGN_PLAN; (2) FAILURE_ATLAS + EVIDENCE_INDEX;
(3) research-to-strategy architecture note; (4) concept dossiers + frozen
ranking; (5) experiment manifest + full fit ledger; (6) development
results incl. losers; (7) trading-agent simulator + no-order proof;
(8) data/cost/feed readiness; (9) next-gate execution packet; (10)
REPORT_VI in the final Lead report. Every delegated lane ends with a
`zcode_orch_v3_handoff@1` JSON at
`research/control/FUTURES-R2S-CAMPAIGN-V1/handoffs/<lane>.json`.

---

## Appendix A — SRML fence list (committed, non-duplicable this campaign)

Wave 1 (24): UNCOND; CTX; B; C; P; C-z05; C-z20; P-z05; P-z20; B-z05;
B-z20; C-b25; C-b75; P-b25; P-b75; B-h30; C-h30; P-h30; B-l3; P-l3;
C-l3; C-z20-h30; P-b75-h30; B-b75 (feature sets CTX/B/C/P per
DEVELOPMENT_PLAN.md @ d2605e0b; z=zone_frac, b=bounce, h=horizon,
λ=L2). Wave 2 (4): B-z05, C-z05, B-z10, C-z10. Baselines for this
campaign CITE their committed logloss rankings (dev_{ES,NQ}_ranking.json)
instead of refitting.

## Appendix B — Cross-asset fences that bind concept D2 checks

Carry front door (rho 0.997–1.000); DGS10-level shadow (#14/#15);
session momentum/fade FX; range-break+retest placebo-reproduced
(FXFV2-A4-P2); Donchian/breakout phase timing (PSV1 control-killed);
event-conditional vol-state selection for reclaim books (STOCKS-NG6:
0.260/0.219/0.320/0.201); short-horizon reversal/displacement composite
(CNG4 BETDIS); release-calendar geometry as direction (P-24 class);
clock-only shadow mandatory for any event conditioning (Q-7).

## Appendix C — Coexistence rules with SRML DEV wave 2

Read-only to their committed artifacts (their worktree tree + branch).
No writes to their code/data/ledgers/plans. No z05-class re-run. No
request to change their conclusions. Dependencies this campaign consumes:
committed census CSVs (10, SHA-pinned copies), committed rankings
(baselines), POLICY_BACKTEST_READINESS gate law, FEED_READINESS_IBKR
status. If their lane is mid-commit on a file I read, my sha-pin records
what I consumed; a mismatch at verification is `NOT_VERIFIED`, not a
silent proceed.
