# PLAN VOL-NG1 — volatility term-structure cycle on platform v3 (new asset family)

> Status: `PLANNED_NOT_STARTED` (registered 2026-09-12).
>
> Generation note: first cycle of the new-assets generation (owner
> directive 2026-09-12, third generation); first `vol` asset family in
> program history — the same-asset ancestry inventory is EMPTY by
> construction, and the mechanism class (volatility risk premium /
> term-structure carry) has never been tested by any program family.
> A correct `VOL_NG1_REJECT_ALL` is a successful research run.

## 0. Owner directive and authority

Owner instruction, verbatim (2026-09-12): "mở cycle 3 assets mới suwt dụng
những nguồn dữ liệu mới và hướng mới bạn đề xuất. Nguồn dữ liệu phải là
miễn phí hoặc có trong gói EODO gì đó tôi mua." (typos preserved; gloss:
open a 3-new-assets generation on new data sources and new directions of
the Lead's proposal; every source must be free or inside the owner's EODHD
package — no purchases, no new keyed signups.)

Standing GO delegation continues (structure of ng1/ng2, owner directive
2026-09-11 carried forward): at this cycle's own prelaunch gate, AFTER
independent A7 publishes `VOL_NG1_S0_LAUNCH_AUTHORIZED` with zero
unresolved HIGH/CRITICAL, the Lead (A1) types the GO decision under the
owner's standing delegation. A7 REFUSED => no GO. Scope excludes S1
opening, push/merge to `main`, purchases, new keyed signups, credentials
in logs, live/paper/testnet.

GO phrase (typed only at this cycle's own gate):

```text
GO VOL NG1 SCORED EXECUTION
```

## 1. Prior verdicts and forbidden ancestry

- No vol family exists in the inventory. The information source is the
  OFFICIAL CBOE volatility-index term structure (VIX9D/VIX/VIX3M) — an
  options-market aggregate never consumed by any program family.
- Named cross-asset kill-candidates pooled into the D2 veto set:
  1. `v16_close_displace_fade` short-horizon reversal forms.
  2. `v17_oi_level` / `dvol_shock` derivative-level forms (crypto-ng1).
  3. `momentum_63s` generic price-momentum forms.
- Mandatory controls on every lane:
  a. **index-only shadow** — the same rule driven by the vol index series
     alone with no ETP leg (is the ETP decision beating its own index
     re-clock?); and
  b. **cost-path control** — ETP decay/roll drag is the mechanism's
     dominant cost (Q-16); the family must survive the measured path-cost
     ladder, not a vendor-stated one.
- Canonical inventory: `research/wayfinder/FAMILY_FAILURES.jsonl` +
  `research/wayfinder/HYPOTHESIS_LEDGER.md` (pooled, P-9/P-12).

## 2. Objective and terminal outcomes (frozen before any proposal)

Objective: test whether volatility term-structure slope and risk-premium
state structures carry after-cost expectancy on tradeable volatility-ETP
legs that no dead reversal / derivative-level / momentum family can
explain.

Terminal outcomes (preregistered, negative-first):

```text
VOL_NG1_REJECT_ALL
VOL_NG1_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
VOL_NG1_BLOCKED_DATA_OR_SELECTION
VOL_NG1_BLOCKED_PRELAUNCH
VOL_NG1_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Data authority and platform v3 adoption (P0)

Measured liveness 2026-09-12 (Lead probe, recorded): CBOE official CDN
daily-history CSVs served (VIX_History.csv verified from 1990-01-02;
VIX9D_History.csv served); EODHD family-1 EOD serves US ETPs fresh to
2026-09-11 (VXX 2018-01-18→, 2174 rows); EODHD serves no indices
(.IND 404 — CBOE official files are therefore the index authority) and
no futures; XIV.US returns an empty list on the plain endpoint, so
delisted inverse-vol ETP coverage MUST be proven via the US delisted=1
channel at P0 or the short-vol lane dies BLOCKED (fail-closed).

Frozen consumption set (nothing else; everything else stays BLOCKED_DATA):

- **S7 CBOE official volatility-index histories** (free, keyless):
  VIX, VIX9D, VIX3M (+ VIX6M if served — census at P0); deterministic
  retrieval; sha-pinned manifest; overlap census with explicit
  first-common-date record.
- **EODHD family-1 volatility US ETP EOD** (existing owner key,
  programmatic .env load, never echoed — V13 precedent): candidate legs
  VXX/UVXY/SVXY + delisted-channel probe (XIV and any dead vol ETPs via
  US delisted=1); the Feb-2018 XIV termination is a natural delisting
  canary; RAW primary + corp-actions cross-check (V8 convention).
- Floors (fail-closed at P0): common VIX9D×VIX×VIX3M daily coverage
  >= 8 years; >= 1000 daily term-structure instants post-2015; >= 2
  living ETP legs with >= 6y EOD; >= 1 delisted vol ETP proven via the
  delisted channel.
- P-7 canaries mandatory: fabricated dates, a never-existed index
  column, a fabricated ETP ticker — each must FAIL.

Adoption law: one per-asset adoption commit; consumption ONLY via
`consume_via_plane`; bounded shadow-parity pilot (plane-read vs raw CSV
bytes, digest equality on overlap) must PASS before lanes.

## 4. Phases and gates

Same law as `plans/PLAN_rates_ng1.md` §4 (P0 authority/adoption -> P1
kernel/costs -> P2 Q-6 floors -> D1 blind lanes -> D2 measured novelty ->
S freeze -> I -> Z dry-run -> A7 prelaunch
`VOL_NG1_S0_LAUNCH_AUTHORIZED` -> GO -> E scored under heavy lock budget
6 -> R detached twin -> T terminal + two-half close).

## 5. Cost, kernel and clock identity

- Clock: daily decision grid — CBOE index close facts + EODHD ETP EOD
  bars; bar-readable close+1 (V7 law); UTC/NY DST fixtures mandatory.
- Costs: measured ETP spreads at stress tier (Q-8); the ETP roll/decay
  path cost carried explicitly in the cost ladder (tier 2.0, Q-16);
  cost once per fill.
- Kernel: inherited dual-book accounting kernel with compatibility tests;
  14-canon diagnostics + prospective DSR (P-11); PBO fail-closed < 8 cells.

## 6. Proposal lanes (blind) and frozen selection rubric

Lane A4 — term-structure slope carry: VIX9D/VIX/VIX3M slope state as the
roll-yield proxy conditioning ETP long/short/flat decisions.

Lane A5 — risk-premium state: implied-vs-realized spread compression/
expansion regimes as conditioning states on ETP legs.

Both batteries: MANDATORY index-only shadow + cost-path control (§1),
calendar-clock shadow, placebo, one falsification rule; mechanisms
declared blind at D1 with forced/late participant identified.

Frozen rubric (before D1 returns; no threshold moves after any scored
number): identical 6 points to `plans/PLAN_forex_ng1.md` §6.

## 7-9. Dry-run/prelaunch/GO/E/R/T, orchestration, boundaries

Identical law to `plans/PLAN_crypto_ng1.md` §7-§9 with A7 verdict key
`VOL_NG1_S0_LAUNCH_AUTHORIZED`; heavy lock serialized machine-wide with
sibling cycles; reproduction detached twin (P-4); handoffs committed at
`research/control/VOL-NG1/orchestration/handoffs/` inside this cycle's
worktree; single-cycle MCP store disclosure as ng (store-level cycle_id
`ZCODE-ORCHESTRATION-V3`, real cycle in task objective). Hard boundaries:
no S1, no push/merge-main, no purchases, no new keyed signups, no
credentials in logs, no options-chain data of any tier (EODHD family-2
NOT entitled — known 404), no vendor vol data beyond the official CBOE
files.
