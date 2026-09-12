# PLAN COMMODITIES-NG1 — commodity positioning cycle on platform v3 (new asset family)

> Status: `PLANNED_NOT_STARTED` (registered 2026-09-12).
>
> Generation note: first cycle of the new-assets generation (owner
> directive 2026-09-12, third generation); first `commodities` asset
> family in program history — the same-asset ancestry inventory is EMPTY
> by construction, and the information type (official positioning) has
> NEVER been used by any program family.
> A correct `COMMODITIES_NG1_REJECT_ALL` is a successful research run.

## 0. Owner directive and authority

Owner instruction, verbatim (2026-09-12): "mở cycle 3 assets mới suwt dụng
những nguồn dữ liệu mới và hướng mới bạn đề xuất. Nguồn dữ liệu phải là
miễn phí hoặc có trong gói EODO gì đó tôi mua." (typos preserved; gloss:
open a 3-new-assets generation on new data sources and new directions of
the Lead's proposal; every source must be free or inside the owner's EODHD
package — no purchases, no new keyed signups.)

Standing GO delegation continues (structure of ng1/ng2, owner directive
2026-09-11 carried forward): at this cycle's own prelaunch gate, AFTER
independent A7 publishes `COMMODITIES_NG1_S0_LAUNCH_AUTHORIZED` with zero
unresolved HIGH/CRITICAL, the Lead (A1) types the GO decision under the
owner's standing delegation. A7 REFUSED => no GO. Scope excludes S1
opening, push/merge to `main`, purchases, new keyed signups, credentials
in logs, live/paper/testnet.

GO phrase (typed only at this cycle's own gate):

```text
GO COMMODITIES NG1 SCORED EXECUTION
```

## 1. Prior verdicts and forbidden ancestry

- No commodity family exists in the inventory. The NEW information type
  is CFTC official positioning (Commitments of Traders) — distinct in kind
  from every dead family (announcement clocks, print surprises, insider
  filings, price-derived features).
- Named cross-asset kill-candidates pooled into the D2 veto set:
  1. `momentum_63s` and generic price-momentum forms — a positioning
     signal that reduces to trailing price momentum dies.
  2. `generic_dow_tue` calendar-clock forms — CoT release geometry is
     weekly; a proposal that is only the release weekday dies.
  3. `v16_close_displace_fade` short-horizon reversal forms.
- Mandatory control on every lane: a **price-only shadow** — the same
  tradeable rule driven by price features alone (no positioning input);
  the positioning family must beat its own price-only re-clock or dies.
- Q-16 LAW (the instrument is the asset): commodity ETP tracking/roll
  drag is part of the mechanism, not noise — it is declared, measured,
  and carried in the cost model.

Canonical inventory: `research/wayfinder/FAMILY_FAILURES.jsonl` +
`research/wayfinder/HYPOTHESIS_LEDGER.md` (pooled, P-9/P-12).

## 2. Objective and terminal outcomes (frozen before any proposal)

Objective: test whether official weekly positioning structures (extremes,
flows, commercial-vs-large-spec geometry) carry after-cost expectancy on
tradeable commodity-linked ETP legs that no dead momentum / calendar /
reversal family can explain.

Terminal outcomes (preregistered, negative-first):

```text
COMMODITIES_NG1_REJECT_ALL
COMMODITIES_NG1_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
COMMODITIES_NG1_BLOCKED_DATA_OR_SELECTION
COMMODITIES_NG1_BLOCKED_PRELAUNCH
COMMODITIES_NG1_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Data authority and platform v3 adoption (P0)

Measured liveness 2026-09-12 (Lead probe, recorded): CFTC historical
archive zips served (deacot2025.zip/deacot2026.zip HTTP 206 on range
probe — official, free, keyless, full-history futures-only reports);
EODHD family-1 EOD serves US ETPs fresh to 2026-09-11 (GLD 2004→, 5487
rows) but serves NO futures (.COMEX 404); Stooq futures CSV is
JavaScript-challenge-blocked for curl (browser-class CANDIDATE only,
never a primary authority).

Frozen consumption set (nothing else; everything else stays BLOCKED_DATA):

- **S6 CFTC Commitments of Traders** — legacy futures-only reports,
  annual archive zips (`dea/history/deacotYYYY.zip`), deterministic
  retrieval, sha-pinned manifest; the PIT clock is the Friday ~15:30 ET
  release of Tuesday-position data (no earlier use, ever).
- **EODHD family-1 commodity-linked US ETP EOD** (existing owner key,
  programmatic .env load, never echoed — V13 precedent): candidate legs
  GLD/SLV/USO/UNG/DBA/PPLT/CPER + census of commodity-linked ETPs with
  >= 8y EOD + delisted-channel probe (US delisted=1, V8-proven); RAW
  primary + corp-actions cross-check.
- Market-pair condition: a market enters ONLY if BOTH (a) >= 10y
  continuous weekly CoT coverage and (b) a matched tradeable ETP leg
  with >= 8y EOD exist. Floor: >= 15 qualifying market-pairs, else the
  cycle dies BLOCKED_DATA at P0 (fail-closed, no rescue).
- P-7 canaries mandatory: fabricated CFTC market codes, fabricated
  release dates, a never-existed report — each must FAIL.

Adoption law: one per-asset adoption commit; consumption ONLY via
`consume_via_plane`; bounded shadow-parity pilot (plane-read vs raw
archive parse, digest equality on overlap) must PASS before lanes.

## 4. Phases and gates

Same law as `plans/PLAN_rates_ng1.md` §4 (P0 authority/adoption -> P1
kernel/costs -> P2 Q-6 floors -> D1 blind lanes -> D2 measured novelty ->
S freeze -> I -> Z dry-run -> A7 prelaunch
`COMMODITIES_NG1_S0_LAUNCH_AUTHORIZED` -> GO -> E scored under heavy lock
budget 6 -> R detached twin -> T terminal + two-half close).

## 5. Cost, kernel and clock identity

- Clock: weekly decision grid — CoT release (Friday 15:30 ET, PIT) ->
  next ETP session decisions; daily EOD bars for execution and stops;
  bar-readable close+1 (V7 law); UTC/NY DST fixtures mandatory.
- Costs: measured ETP spreads at stress tier (Q-8); ETP expense/roll drag
  carried in the cost ladder (tier 2.0, Q-16); cost once per fill.
- Kernel: inherited dual-book accounting kernel with compatibility tests;
  14-canon diagnostics + prospective DSR (P-11); PBO fail-closed < 8 cells.

## 6. Proposal lanes (blind) and frozen selection rubric

Lane A4 — positioning-extreme structure: percentile extremes of official
positioning geometry (commercial vs large-spec net positioning) as
conditioning/reversal states on ETP legs.

Lane A5 — positioning-flow structure: changes in positioning (flows,
acceleration, divergence vs price) as conditioning states.

Both batteries: MANDATORY price-only shadow (§1), release-clock shadow,
shifted-release placebo (Q-11 invalid-null distinction), one
falsification rule; mechanisms declared blind at D1 with forced/late
participant identified.

Frozen rubric (before D1 returns; no threshold moves after any scored
number): identical 6 points to `plans/PLAN_forex_ng1.md` §6.

## 7-9. Dry-run/prelaunch/GO/E/R/T, orchestration, boundaries

Identical law to `plans/PLAN_crypto_ng1.md` §7-§9 with A7 verdict key
`COMMODITIES_NG1_S0_LAUNCH_AUTHORIZED`; heavy lock serialized
machine-wide with sibling cycles; reproduction detached twin (P-4);
handoffs committed at
`research/control/COMMODITIES-NG1/orchestration/handoffs/` inside this
cycle's worktree; single-cycle MCP store disclosure as ng (store-level
cycle_id `ZCODE-ORCHESTRATION-V3`, real cycle in task objective). Hard
boundaries: no S1, no push/merge-main, no purchases, no new keyed
signups, no credentials in logs, no vendor futures data (browser-class
futures probes are CANDIDATE evidence only and never authoritative).
