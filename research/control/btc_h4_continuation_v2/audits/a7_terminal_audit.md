# A7 TERMINAL AUDIT — BTC-H4-CONTINUATION-V2 (fresh context)

Audited head `0724542b7c678bb674f168ded8edf6fddb387766` (orca/btc-h4-continuation-v2-integration,
base af52f358 = PSV1 terminal anchor). Measured 2026-09-23T12:20Z.
Heavy lock foreign-held (CRYPTO-HISTORICAL-REPLICATION-3F-V1 pid 77456); audit
recompute ran under plan §8 light exemption, measured 0.22 s CPU / 113.5 MB
(getrusage, cross-checked). Script: `audits/a7_recompute.py`.

## Checklist

- **C1 chain/registry — PASS.** Plan a8473839 on main; bootstrap 1442a76a is
  HEAD's parent; PSV1 row TERMINAL 4/15 with anchor af52f358; V2 row budget 0/2,
  S1 SEALED_UNTOUCHED — all measured in `plans/CYCLE_REGISTRY.json`.
- **C2 claim "lifecycle ACTIVE" — FAIL (LOW, non-blocking).** Registry says
  `PLANNED_NOT_STARTED`, head field still 1442a76a; "ACTIVE" is the
  OWNERSHIP_MANIFEST's `integration.status`, not the registry's lifecycle.
- **C3 reconciliation recompute — PASS.** My own script re-ran the frozen PSV1
  engine (cells/books/accounting, READ-ONLY) and reproduced the COMMITTED PSV1
  `scored_ledger.json` at max rel-err **0.0** across 1.0x/1.5x/2.0x (fold nets
  +140,843.28 / −46,959.99 / +133,820.83 / −50,012.30 @1.0x; 86/86/86;
  79 STOP + 7 GATE_INACTIVE). V2 `reconciliation.json` values cross-matched.
- **C4 min-hold branch — PASS.** Suppression law verbatim at `events.py:99-100`
  (exact), `MIN_HOLD_BARS = 12` (config.py:127); 22 STOP + 13 GATE_INACTIVE = 35
  suppressed triggers over 11 trades, delays 2–29 median 9; 6/6 spot-checked
  delayed trades match ledger + rebuilt book (hold ≥ 12); counterfactual deltas
  (+2,264/+5,201/+1,817/−13,066 → −3,785.07) faithful.
- **C5 entry-confirmation branch — PASS.** All 16 quoted PIT medians faithful;
  anti-sort (F2 5.12 > F1 4.52; F4 4.14 > F3 2.85) and wrong vol clusters
  ({F1,F2} vs {F3,F4}) correct; MFE collapse 8.1% vs 3.1–3.8% with flat MAE;
  rank 1.0 at all 86 entries.
- **C6 SMA200 no-op — PASS_WITH_FINDINGS.** Premise "every entry dd200 ≈ 0" is
  FALSE (17/86 entries > 1% below 200-bar max, min −23.3%); conclusion re-verified
  TRUE from the panel: `close > SMA200` binds 0/86 entry decision bars.
- **C7 budget/boundary — PASS.** Diff af52f358..HEAD = 12 files, all under
  `research/control/btc_h4_continuation_v2/`; no arm_id/family_id/candidate
  config anywhere in the V2 tree; runtime/ + tests_py/ empty; PSV1 worktrees
  porcelain-clean (integration @ 0b25b230 = registry head); no orders surface.
- **C8 denominators — PASS.** No §7 trial identity instantiated (no cycle_id/
  arm_id/arm_config_digest scored record); rebuild = predecessor reproduction
  (§1.1), created no new PnL; PSV1 ledger 52 observed / 4 budget unchanged;
  program 283/286 (wayfinder HYPOTHESIS_LEDGER.md).

## Findings

- **F-A7-1 LOW** — Claim/registry mismatch on lifecycle ("ACTIVE" vs measured
  `PLANNED_NOT_STARTED`, stale head); reconcile at close via researchctl.
- **F-A7-2 LOW** — P2's SMA200 proof overclaims ("every entry dd200 ≈ 0" false);
  the no-op conclusion itself independently confirmed. Restate as empirical.
- **F-A7-3 LOW** — Strongest alternative candidate named: breakout-strength
  (close clears prior channel high by ≥ 1.0×ATR(14); round, PIT, mechanism).
  Also considered: 20-bar range-compression gate; gate-age (in the G6-killed
  gate-timing class). Judgment: closing without scoring is NOT premature —
  identical entry geometry, flat MAE, failure in follow-through only, and any
  threshold now would be chosen from the F2/F4 record (fold-PnL scanning, §2).
  If a successor prospective cycle ever runs, preregister breakout-strength
  BEFORE seeing outcomes.
- **F-A7-4 INFO** — Lock/light-exemption discipline clean on both the P1 run
  and this audit; data manifest digest matches the plan pin; folds applied
  exactly as planned.

## Verdict

`CONFIRM_WITH_FINDINGS` — blocking_count **0**.
Strongest allowed label: `BTC_H4_CONTINUATION_V2_NO_ELIGIBLE_PROPOSAL`.
