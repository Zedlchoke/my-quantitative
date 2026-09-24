# PLAN — SHADOW-PAPER-REVIEW-V1 (review-only cycle)

- Registered: 2026-09-24, owner instruction (session verbatim): "bạn lên
  cycle [rà soát] các strategy đang chạy shadow paper và nếu ý kiến cải
  thiện các strategy theo tính khoa học kinh tế... Tối đa hoá subagent để
  tốc độ tốt".
- Asset: shared (crypto + forex + gold shadow sleeves).
- Lifecycle: ACTIVE_LIGHT. Budget 0/0 — this cycle computes ZERO scored
  cells, runs NO heavy job, places NO orders. It is an evidence review +
  improvement-opinion cycle only (JRV2-DECISION-AUDIT-V1 class).
- Heavy lock: machine-wide lock is HELD by CRYPTO-HISTORICAL-REPLICATION-3F-V1
  (data-staging, foreign) — irrelevant to this cycle; no heavy acquire
  attempts permitted.

## 1. Scope (measured 2026-09-24)

Shadow-paper strategies in flight (from CYCLE_REGISTRY.json +
DASHBOARD-AND-SHADOW-RELIABILITY-V1 measured report 2026-09-24):

| Sleeve | Cycle | Cadence | State at intake |
|---|---|---|---|
| XSECT-FUND-CARRY-7D | PROSPECTIVE-SHADOW-V1 | daily | PASS, 48 fills, realized +3,936.27 |
| ILLIQ-AMIHUD-28D-W | PROSPECTIVE-SHADOW-V1 | weekly | PASS, 8 fills |
| BASISLV-PREMFADE-28D | PROSPECTIVE-SHADOW-V1 | weekly | BLOCKED 09-21 (data gap, fail-closed; source healed; next 09-28) |
| BTC4H-BANDRIDGE | PROSPECTIVE-SHADOW-V1 | H4 | 0 fills — InsufficientCashError root cause; owner packet A/B/C open |
| EURUSD RANGEFADE-2M | FX-RANGEFADE-2M-SHADOW-V1 | H1 | PASS, 0 signals yet (valid) |
| GBPUSD RANGEFADE-2M | FX-RANGEFADE-2M-SHADOW-V1 | H1 | PASS, 0 signals yet (valid) |
| XAUUSD swing | XAUUSD-SHADOW-V1 | bar-driven | live worker pid 4755; entries structurally rare (frozen spec) |

Support planes reviewed for dependency risk only: LIVE-DATA-GATEWAY-V1,
quant shadow dashboard + Phorec apps (reliability PASS 2026-09-24).

## 2. Lanes (parallel subagents, read-only analysts)

- lane_crypto_sleeves — the 4 PROSPECTIVE-SHADOW-V1 families: ledger
  stats from bytes, economic-mechanism critique, improvement opinions,
  BANDRIDGE A/B/C + fill-law recommendation with reasoning.
- lane_fx_gold — FX-RANGEFADE-2M-SHADOW-V1 (EURUSD+GBPUSD) and
  XAUUSD-SHADOW-V1: status, mechanism critique, short-beta/carry-beta
  control status vs ancestors' mandatory laws, sample-size/opportunity-
  cost law for the rare-entry gold sleeve.
- lane_portfolio_program — program-level: promotion/kill laws and their
  statistical power, portfolio construction across sleeves, common
  data-source dependency risk, cost-book realism, measurement hygiene.

Each lane writes `research/control/SHADOW-PAPER-REVIEW-V1/<lane>/REPORT.md`
+ `HANDOFF.json` (schema zcode_orch_v3_handoff@1). Dispatched base sha
f0a8e800c47de1800011d20bccd9bcb2cc7e8546 (root checkout main).

## 3. Laws

- Read-only for lanes: no ledger/registry/manifest writes, no worker
  restarts, no foreign-process touch, no heavy jobs, no network beyond
  reading local artifacts. Light local python stats on jsonl ledgers
  allowed (read-only).
- NOT_RUN / BLOCKED vocabulary preserved; every number must cite an
  artifact path. No improvement opinion may be implemented by this
  cycle — implementation is a future owner-authorized cycle/amendment.
- Lane boundaries respected; synthesis (REVIEW.md) is A1-side.

## 4. Gates & close

- G1 all three lane REPORT.md + HANDOFF.json present and self-consistent.
- G2 synthesis REVIEW.md written with: per-sleeve verdict table,
  economic-science improvement opinions (each tagged
  OWNER_DECISION_REQUIRED / AMENDMENT_REQUIRED / ENGINEERING_ALLOWABLE),
  and explicit BANDRIDGE sizing/fill-law recommendation.
- G3 registry entry updated to REVIEW_COMPLETE; cycle stays ACTIVE_LIGHT
  (no terminal — the sleeves themselves keep running under their own
  cycles). No denominators touched (0 scored cells).
