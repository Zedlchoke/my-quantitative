# V8 catalog novelty check — H-XSECT-REVERSAL-v2

Author: A6 (spec/preregistration owner). Drafted 2026-08-25, blind to all V7
results (no `results/portfolio_v7`, partial logs, metrics, or verdicts read).
Frozen with the V8 spec per PLAN §17.1 ("candidate/spec/novelty hash phải
freeze **trước scored artifact V7 đầu tiên**") and §17.2.

Question under test: is the weekly cross-sectional reversal contract — rank
six alts by past return over 3D/7D/14D formations, long bottom-2 losers /
short top-2 winners, Monday 00:00 UTC cadence, gross 0.80 net 0 — materially
distinct from every existing catalog specification?

Catalog scanned: `ls research/hypotheses/` → H-XSECT-MOM-v1,
H-XSECT-FUNDING-CARRY-v1, H-XSECT-FUNDING-PRICE-DIVERGENCE-v1,
H-VOLCOMP-BRKOUT-v1, H-FUNDCROWD-MR-v1, H-FUNDCROWD-MR-v2,
H-XSECT-REVERSAL-v1 (candidate/status/hypothesis files read). The six
entries named in PLAN §17.2 scope are compared below; H-FUNDCROWD-MR-v1 is
covered implicitly via its v2 successor (same gate structure, never scored).

## Per-entry comparison

| Catalog entry | State | Signal construction | Verdict vs V8 reversal | One-line justification |
|---|---|---|---|---|
| H-XSECT-MOM-v1 | SPEC_LOCKED (scored family) | `cumulative_log_return_rank` 3/7/14d, long top-2 winners / short bottom-2 losers, daily rebalance | **DISTINCT** | Exact sign flip: MOM longs the names V8 shorts and shorts the names V8 longs, and it rebalances daily at 00:00 UTC vs V8's weekly Monday clock. |
| H-XSECT-FUND-CARRY-v1 (repo dir `H-XSECT-FUNDING-CARRY-v1`, V6 sibling) | FROZEN_FOR_EXECUTION, zero scored trials | Rank by trailing mean settled funding alone; long bottom-2 / short top-2 funding, daily | **DISTINCT** | Carry-only ordering with no price-return formation anywhere; V8 ranks purely on past returns over multi-day lookbacks, so their orderings can disagree on every symbol. |
| H-XSECT-FUNDING-PRICE-DIVERGENCE-v1 (V7) | FROZEN_FOR_EXECUTION, zero scored trials | Signed difference of two percentile ranks: price return minus funding; daily | **DISTINCT** | A two-term spread score whose long side can buy relative STRENGTH (price rank minus carry), categorically different from V8's single-term pure-reversal rank on a weekly clock. |
| H-VOLCOMP-BRKOUT-v1 | REJECTED (scored) | Single-symbol long-only squeeze→Donchian breakout + volume burst on 15m bars | **DISTINCT** | No cross-sectional ranking at all; entry-timing pattern on one symbol vs V8's market-neutral two-leg weekly portfolio. |
| H-FUNDCROWD-MR-v2 | REJECTED (scored) | Point-in-time funding percentile as a SKIP-gate on frozen reclaim-MR entries, 15m bars | **DISTINCT** | Gate-vs-spread categorical difference: funding percentile filters individual entries and no past-return rank exists in that spec; V8 constructs a portfolio from cross-sectional return order. |
| H-XSECT-REVERSAL-v1 | IDEA / DRAFT-ONLY, zero trials, blocked DATA_INCOMPLETE | Sketch: trailing 7d return quintiles, weekly, 7 symbols incl. ETH; never implemented | **DISTINCT** | Same family lineage but v1 is an unimplemented draft with quintile buckets, no frozen lookback set, no control trial, and an ETH-containing universe; v2 is the only executable, fully frozen instantiation. |

## v1 → v2 delta statement

The v1→v2 delta is a **data-availability universe rule only**: ETH is dropped
because its common intersection was ~1y of data (the recorded v1 blocker),
leaving six alts with ~2y clean history — exactly v1's own promotion
criterion. This rule was frozen here BEFORE any V8 performance existed;
no symbol is removed or re-weighted on PnL, and no other scientific field
(direction logic, weekly clock, fold structure, budget discipline) changes in
kind from the preregistered v1 sketch.

## Duplicate-risk analysis

The nearest neighbor is H-XSECT-MOM-v1 (identical rank mechanics, opposite
sign). V8 is not a rerun or rename of it: sign-flipping makes the PnL claims
mutually exclusive rather than duplicative, and the negative control
XSECT-WMOM-7D-CONTROL exists precisely to measure whether reversal adds
anything over momentum. Shared scaffolding (15m bars, chronological folds,
cost model, S0 labels) is common protocol per PLAN §8/§16/§17, not signal
duplication.

## Final verdict

```text
NOVEL_MATERIAL_DISTINCT
```

No catalog entry is a material duplicate of H-XSECT-REVERSAL-v2; V8 is not
blocked on novelty grounds. This memo must be hashed by A7 together with
`candidate.yaml`/`status.yaml` (currently `PENDING_A7_HASH` in
`v8_spec_freeze.json`) before any scored V7 artifact timestamp is compared,
and must show no post-freeze diff thereafter.
