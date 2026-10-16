# PLAN — FUTURES-PAH-V1 (personal adaptive futures harness)

Status: REGISTERED (ACTIVE_LIGHT) · Owner authorization: verbatim dispatch
2026-10-16 ("OWNER AUTHORIZATION — PERSONAL ADAPTIVE FUTURES HARNESS,
Z05 + K3 SMALL-CONTRACT + ADAPTIVE STRATEGY RESEARCH"). Campaign ID:
`FUTURES-PAH-V1`. One Lead session owns this cycle (P-17). Terminal
outcomes preregistered (§I). No scored PnL, no GO gate exists in this
cycle: go_phrase NOT_REGISTERED by design (P-8 — a GO is typed only at a
cycle's own gate; this cycle has no gate that consumes one).

Measured intake base: root `main` @ 4f67cbf191769fb011d4a12ede6f361427876ca7
(13 ahead of origin/main, no push). Dirty untracked root paths classified
OWNER/POST-CAS and untouched: `plan_ml.md` (DRAFT_FOR_OWNER_REVIEW),
`research/control/FUTURES-VSA-ESNQ-V1-postCAS/` (lane evidence copy),
`research/control/weather_pred_prep_v1_draft/` (owner lane prep),
`.my-quantitative-data/` (owner data dir). Heavy lock FREE_PROVEN at
intake (2026-10-16). Disk free 15 GiB (92% used) — no large downloads;
TradingAgents clone is shallow-reading only.

## 0. Mission and one-paragraph spirit

Xây harness trading agent cá nhân: nghiên cứu, phát triển, đánh giá và
lựa chọn strategy theo bối cảnh, tự điều chỉnh trong phạm vi đã khóa và
kiểm chứng. Campaign này KHÔNG cam kết tìm strategy có lời. Nó chuyển
(1) SRML wave-2 population evidence (z05/z10) thành một bản quyết định
trung thực + tối đa 3 policy specs z05; (2) K3 NQ–ES behavioral signal
(REAL nhưng COST_DEAD ở full-size) thành một K3_SMALL_CONTRACT_FEASIBILITY
trên sizing micro được kiểm chứng spec; (3) một bộ adaptive concept
dossiers với tối đa 2 concept được implement so với static counterpart;
(4) một TradingAgents adoption review sau audit source @ pinned SHA;
(5) harness architecture + code/tests + verifier + next-stage packet.
Kết quả âm có bằng chứng đầy đủ là thành công.

## 1. Measured state at registration (evidence, not narrative)

- Read-only predecessor evidence (sha-pinned at consumption, never
  rewritten):
  - R2S terminal: worktree `.worktrees/futures-r2s-campaign-v1/integration`
    branch `orca/futures-r2s-campaign-v1-integration` @
    `269d40475d87b640c91f80e798ea1224c3028fad`, TERMINAL
    CAMPAIGN_COMPLETE_WITH_FINDINGS. Consumed: `dev/K3_RESULTS.json`,
    `dev/K3_VERDICT.json` (8 configs, hit 0.564–0.645, gross
    $11.5–33.2/episode, reference cost $89, gross:cost 0.13–0.37, ALL
    BEHAVIORAL_SIGNAL_COST_DEAD), `dev/K1_VERDICT.json`, `w2/SELECTION_FREEZE.json`,
    `w2/CONCEPT_DOSSIERS.md`, `h/CAPITAL_FEASIBILITY.md`,
    `NEXT_GATE_PACKET.md`, harness `research/futr2s/` + `agent/` +
    `tests/futr2s/`.
  - SRML DEV: worktree `.worktrees/srml-dev-20261015/integration`, branch
    `srml-dev-20261015` @ `0b53bad4b7d706d5cc317c9a8d32ef6cfd34b04c`.
    Wave 1 COMPLETE (24 configs, DEVELOPMENT_CANDIDATE=0,
    POPULATION_SHIFT_FINDING z0.05), wave 2 COMPLETE (B-z05/C-z05/
    B-z10/C-z10, 96 fits). Consumed: `research/control/SRML-DEV-20261015/
    census/` (dev_dataset_{ES,NQ}_{z0.05,z0.1}-b0.5.csv + summaries +
    rankings + ledgers + SHA256SUMS_dev.txt + SHA256SUMS_w2.txt),
    `packets/POLICY_BACKTEST_READINESS.md`, `packets/FEED_READINESS_IBKR.md`,
    `research/srml_dev/{policy_spec.py,dev_run.py,w2_feasibility.py}`,
    `tests/srml_dev/`.
  - VSA terminal REJECT_ALL 8/8 @ orca/vsa-esnq-v1-integration 55962650
    (S0 2010-06-06..2022-12-31 scored; S1 SEALED). ES-PB1 REJECT_ALL
    24/24; NQ-V1 29/29; FX-V1 73/73; ES-F2-V1 D2_BLOCKED_DATA_VETO;
    FX-FUTURES-FRONTIER-V1 BLOCKED_TRANSPORT (L-FXFF-1: CME estate
    SNI-filtered — standing environment fact).
- Data authority for development: 1m Databento GLBX.MDP3 ES/NQ
  2010-06-06→2026-09-30 at
  `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/`
  (manifest `data_hashes_1m.csv`, 41 files cross-verified). **Seal: any
  ts ≥ 2023-01-01 is refused in code (`SealedWindowRefused`), proven by
  test — carried unchanged from R2S L1.**
- Permission separation (owner §1): READ of terminal evidence is
  forensic; TRAINING on exposed development data (2010-06→2022-12) is
  the only authorized computation surface. Terminal outcome numbers are
  never a training corpus (§F-7 of R2S, carried).

## 2. Universe and authority scope (owner §2)

- ES primary, NQ replication. 6A: PARKED — no data read, no feature use,
  unchanged. MES/MNQ: research object of Lane B (specs/costs/feasibility),
  not a scored surface. CFD: research-later option only, needs its own
  broker quotes/cost evidence; never a default shortcut.
- Development window: ES/NQ 2010-06→2022-12 only (DEVELOPMENT_OUTCOME_
  EXPOSED). 2023+/S1 sealed untouched. FX new outcomes NOT authorized
  (spot or futures). IBKR read-only probe on 127.0.0.1:7497 with a
  dedicated clientId is AUTHORIZED (owner §3-B) under §4-B law below.
- No purchases/subscription changes, no TWS/collector config changes, no
  push/merge, no orders (broker mode NO_ORDER only), no scored policy
  PnL, no prospective activation, no self-typed GO.

## 3. LANE A — Z05: population → decision (owner §2)

Input law: NO new zone scans; z05/z10, horizons and baselines already
committed are the fixed starting point. SRML census datasets
(z0.05-b0.5, z0.1-b0.5 × ES/NQ) + wave-2 artifacts are sha-pinned
inputs; re-running their committed model identities to re-materialize
prediction streams is REUSE (0 new configs, logged), never re-selection.

A1. Audit the wave-2 claims before any decomposition:
  - lower entropy ≠ "not more predictable" (entropy is a property of the
    predicted distribution, not of label predictability);
  - accuracy can be carried by the NEUTRAL class (per-class metrics
    mandatory);
  - large decision overlap between z05/z10 does NOT prove z05-only adds
    no increment (overlap ≠ increment);
  - nested selection vs a fixed top-config table: compare committed
    nested-selection rankings against the fixed top-config choice on
    the SAME denominators.
A2. Decompose decisions on valid market-event identity (decision_id
    anchored to symbol+session+anchor+episode; NEVER force-match events
    at different times/estimands): A=common, B=z05-only, C=z10-only.
A3. Per population, same decision IDs and reporting denominator:
    class frequencies/entropy + unconditional baseline; calibration,
    logloss/Brier, per-class precision/recall; LONG/SHORT split;
    coverage/abstention; count of independent sessions; era/fold
    stability; magnitude and adverse movement (authority: descriptive
    statistics from committed census columns only, no new label
    construction); level increment beyond context/side/vol.
A4. Lock AT MOST 3 policy concepts (hard cap): P1 context-only
    baseline; P2 context+level; P3 context-dependent WAIT/trade rule
    (only if evidence warrants; otherwise 2). Each spec: entry/exit/
    sizing/cooldown contract + cost/fill contract referencing
    POLICY_BACKTEST_READINESS law. Probability OUTWARD is never expected
    return; PnL is NOT computed here (own gate).
A5. Verdict enum (exactly one): POPULATION_ONLY / MODEL_INCREMENT /
    POLICY_READY_FOR_TEST / INSUFFICIENT / NO_CANDIDATE.
Output: `lanes/z05/Z05_DECISION_REPORT.md` + machine JSON verdict +
per-population metric tables + decomposition counts.

## 4. LANE B — K3 small-contract feasibility (owner §3)

Law: "margin thấp" ≠ "rẻ" ≠ "an toàn". No linear scaling of gross edge
or PnL from ES/NQ to micro. Signal (ES/NQ), execution vehicle (MES/MNQ
candidates), basis/tracking, integer hedge-ratio rounding, tick
value/min size/contracts per leg, commissions/fees/spread/slippage,
partial fills/legging risk/emergency unwind, margin/stress/capital —
each is a separate component with an evidence class.

B1. Spec verification from CME/IBKR public sources where the network
    allows (L-FXFF-1 SNI-filter on cmegroup.com is a known blocker:
    if blocked, spec status = DOCUMENTED_CANDIDATE with source other
    than CME official, or NOT_VERIFIED — never silently asserted).
    Verify MES/MNQ: multiplier (×0.1 of ES/NQ), tick size/value,
    settlement, hours, margin class (public CME margin file if
    reachable).
B2. K3 same-sizing reconcile (owner §3): recompute the 8 committed K3
    configs' per-episode economics on ONE consistent trade sizing:
    same hedge ratio, same integer contract counts per leg under micro
    sizing (ES→N legs vs NQ→β·N legs with integer rounding law declared
    BEFORE arithmetic), same fills count, same units. Reconcile the
    committed gross $11–33/episode vs reference $89 (full-size 4-leg)
    against the micro 4-leg cost book built from tick values + public
    fee schedules (MEASURED=SOURCED class only; IBKR statement
    commissions only if owner-provided evidence exists — otherwise
    MODELED with source class). Feasibility condition: micro cost
    compared to gross edge PER CONFIG with an uncertainty margin —
    "cost < $89" alone is NOT sufficient; also report stress: 2×
    slippage, spread widening, legging (one leg filled, other missed).
B3. IBKR probe: single preregistered attempt on 127.0.0.1:7497,
    dedicated clientId ≥ 51, read-only: handshake (nextValidId),
    paper/live determination, entitlements, realtime/delayed market
    data type, contractDetails for MES/MNQ (allowed). NO placeOrder
    (what-if included if it routes through order API). NO config or
    subscription change. Account statements read only if owner-provided
    or valid authorization exists; never write account ID/NAV/
    credentials to repo/logs. Probe failure ⇒ NOT_RUN recorded once;
    no retry loop. ibapi may be pip-installed pinned (open-source
    client, $0) — disclosed in the lane report; no other dependency
    installs.
Output: `lanes/k3/K3_SMALL_CONTRACT_FEASIBILITY.md` + cost/sizing
matrix (per config × component × evidence class) + data gaps +
BLOCKED_DATA acquisition request drafts (no purchase).

## 5. LANE C — adaptive concepts (owner §4)

C1. Up to 6 concept dossiers (nulls and failures included; survivors
    not required) over the adaptation types: volatility-aware risk
    sizing; regime-dependent selection between frozen policies;
    calibrated confidence → WAIT/NO_TRADE; scheduled recalibration;
    scheduled rolling refit; drift detection → risk reduction/stop.
    Each dossier defines: information used + available_at; state/
    context; action space; which parameters adjust; when; training
    window + update lag; change bounds; rollback conditions; static
    baseline; null + kill criteria; data/power/cost; ancestry
    (DEAD_K2/VSA/SRML fences — no revival by rename/regime-shopping).
C2. "AI tự điều chỉnh" = a FROZEN update algorithm. Learning rule,
    selection rule and risk limits together are one policy. Never:
    change objective mid-run, open data scope, raise leverage, learn
    from incomplete outcomes, LLM-edited thresholds after losses, deep
    RL before a trusted static baseline + simulator.
C3. Rubric frozen BEFORE ranking (committed with the dossiers); at
    most 2 concepts implemented. Every implemented adaptive model is
    compared to its static counterpart on the SAME population, SAME
    cost assumptions, SAME execution timing, SAME resource budget;
    report update count, turnover, stability, failure recovery.
    Behavioral metrics only — no PnL.
Output: `lanes/adaptive/ADAPTIVE_CONCEPT_DOSSIERS.md` +
`SELECTION_FREEZE.json` (rubric) + implementation + tests +
`IMPLEMENTATION_REPORT.md`.

## 6. TradingAgents — audit first, narrow integration (owner §5)

T1. Clone public repo at a pinned SHA (record SHA, license, deps);
    read code, not README stars. Audit: graph/agent interfaces; data
    access + point-in-time behavior; memory/reflection/update timing;
    checkpoint/retry; structured decisions; backtest accounting;
    order/simulated-exchange paths; provider cost/latency/
    nondeterminism; applicability gap between stock/news workflow and
    futures intraday.
T2. Permitted roles ONLY: research proposer; bull/bear critic;
    evidence summarizer; model/strategy explanation; risk review
    proposal. Every output must cite artifact/source/time. LLM never:
    grants run permission, ratifies gates, re-picks winners, reads
    sealed data, sends orders.
T3. No future memory in historical runs; memory/checkpoint isolated per
    experiment/run with as-of cutoff enforced; no current news/web
    calls inside historical replay claimed as PIT.
T4. Integration via schema-explicit adapter; no wholesale stack import;
    the verified quant engine is never replaced by an LLM debate;
    value-add of LLM vs same harness without LLM must be measured
    (fixtures only this campaign).
T5. Public-source audit + offline tests with fixtures/mocks ONLY; NO
    paid LLM/provider calls (no API keys used); provider-cost estimate
    in the review instead.
Output: `lanes/ta/TRADINGAGENTS_ADOPTION_REVIEW.md` + pinned-SHA audit
notes + offline adapter test + estimate.

## 7. Common harness (owner §6)

Reuse-first from R2S L1–L10 + agent/ (sha-pinned copies, provenance
file, no history merge): data+session/contract authority (seal
enforced); feature snapshots; model registry; strategy/policy registry;
adaptation scheduler (new, Lane C consumer); independent risk engine
(veto over every agent); intent journal; replay/simulation broker;
read-only IBKR adapter (refusing order paths); reconciliation +
monitoring; TradingAgents research adapter (schema-explicit, offline).
Decision output schema (minimum): as_of / input_cutoff / data_quality /
model_version / policy_version / context / forecast / uncertainty /
action / size / expiry / risk_checks / evidence_refs / refusal_reason.
Action ∈ {LONG, SHORT, HOLD, EXIT, WAIT, NO_TRADE}. Broker mode
NO_ORDER; no order-routing implementation enabled. "$10k" is an owner-
stated capital scenario, not measured NAV; no NAV reads; no self-set
live risk limits presented as owner-approved.

## 8. Development budget (owner §7)

SEARCH_MANIFEST committed BEFORE any new computation: every planned
configuration, folds, variants, estimators, seeds, accounting. Campaign
cap **24 NEW behavioral/model configurations TOTAL** (both lanes; not
per lane). Allocation frozen at registration:
- Lane A: ≤3 policy specs z05 (P1/P2/P3) — behavioral evaluation only.
- Lane C: ≤2 adaptive concepts × (1 adaptive identity + static
  counterpart). Counterparts identical to committed SRML configs are
  REUSE (0); only genuinely new static identities count.
- Lane B / TradingAgents: 0 configurations (evidence arithmetic /
  source audit).
- Planned: 5; reserve: 19 with repair-only law (crash/fixture/seal
  defects in the SAME frozen questions, disclosed as incidents — never
  new search axes). No re-computation where valid artifacts exist to
  reuse. No budget expansion after results are seen.
ES/NQ development 2010-06→2022-12; nested chronological selection;
purge by horizon/episode; outer folds labeled DEVELOPMENT_OUTCOME_
EXPOSED, never pristine. Every adaptive model vs static counterpart
same-population same-cost same-timing same-budget. Losers, failure/
retry and observed/published accounting kept complete.

## 9. Execution, stop rule, owner gates (owner §8)

Order: intake (done, this plan) → control plane + SEARCH_MANIFEST →
source audit (T1) → lane implementations → synthetic verification →
authorized development (bounded) → independent verifier → next-stage
packet. Blocker on one lane ⇒ continue independent lanes; no routine
technical question returns to owner. Scored policy/registration/GO/
prospective/live gates: code, tests, cost/data readiness and run
packet completed BEFORE stopping; never bypassed by renaming to
"diagnostic"/"shadow".
OWNER GATES (not exercised this campaign): outcome 2023+/S1; new
outcome FX; scored policy PnL; prospective activation; paper/live
orders; purchases/subscriptions; push/merge; typed GO for any future
cycle.
Terminal outcomes (preregistered):
- T1 `CAMPAIGN_COMPLETE_WITH_FINDINGS` — all deliverables landed;
  verdicts per lane with evidence; 0–2 adaptive implementations.
- T2 `BLOCKED_DATA_OR_AUTHORITY` — a hard wall stops a lane; partial
  deliverables still land with blocker packets.
- T3 `NO_CANDIDATE_HONEST_ZERO` — budget consumed/selection empty.

## 10. Verifier + deliverables (owner §9)

Fresh-context verifier (audit-only, repairs nothing): rebuild selected
decisions from raw bytes with its own code; prefix replay + future
mutation over the whole vector; historical memory isolation; adaptive
update timing; same-population baselines; contract sizing/cost
arithmetic; no-order proof; complete trial accounting.
Deliverables (control dir `research/control/FUTURES-PAH-V1/`):
CAMPAIGN_PLAN (copy of this plan) · OWNERSHIP_MANIFEST.json ·
DISPATCH/ packets · SEARCH_MANIFEST.json · lanes/z05/Z05_DECISION_REPORT ·
lanes/k3/K3_SMALL_CONTRACT_FEASIBILITY · lanes/adaptive/ADAPTIVE_CONCEPT_
DOSSIERS + implementation · lanes/ta/TRADINGAGENTS_ADOPTION_REVIEW ·
HARNESS_ARCHITECTURE.md + code/tests · manifests + fit ledgers ·
VERIFIER/A7_VERDICT · NEXT_STAGE_PACKET.md · REPORT_VI.md ·
handoffs/<lane>.json (`zcode_orch_v3_handoff@1`).

## Appendix A — Fences carried (non-negotiable)

DEAD_K2 families (PB1 overnight pair, NQ F1/F2/F3, 6E/6B/6J F2/F3) not
revivable by rename/threshold/cadence; VSA sweep/BOS/iFVG descendants
fenced (REJECT_ALL both symbols); S/R behavioral classification is
SRML's lane — z05/z10 work reads their committed artifacts and builds
policy layers only, never re-runs z/b/h/λ variants of their 28; K1
level-memory 0/24 rows stand (permutation-null kills disclosed); K3
reopening path = venue-cost authority, which Lane B prepares evidence
for without claiming it. 6A PARK; FX-FUTURES-FRONTIER L-FXFF-1
transport blocker; S1 sealed. Appendix B cross-asset fences of R2S
(carry front door rho 0.997–1.000, DGS10 shadow, range-break+retest
placebo, Donchian phase, NG6 event-conditional selection, release-
calendar geometry, Q-7 clock shadow) bind any new concept D2 check.

## Appendix B — Coexistence rules

Read-only to R2S and SRML committed artifacts (their worktree trees +
branches at the SHAs in §1); no writes to their code/data/ledgers/
plans; sha-pin every consumed file; mismatch at verification ⇒
NOT_VERIFIED, never silent proceed. One heavy job machine-wide via
canonical lock; never kill foreign workers. Every delegated lane ends
with `zcode_orch_v3_handoff@1` at
`research/control/FUTURES-PAH-V1/handoffs/<lane>.json`; dispatch_sha
must equal actual_start_sha or the handoff is INVALID.
