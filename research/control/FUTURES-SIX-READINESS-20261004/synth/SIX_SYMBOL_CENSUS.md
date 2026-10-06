# SIX_SYMBOL_CENSUS — FUTURES-SIX-READINESS-20261004 (controller synth)

Round: worktree `.worktrees/futures-six-readiness/prep` @ branch `codex/futures-six-readiness-20261004`,
wave-1 checkpoint `9fa3fd148b7cd9b2e173e95e1c613b1f5f137066`, base `d7fc6231…` (topology per DISPATCH_MANIFEST
incl. INC-1). All four lanes independently **VERIFIED** by VERIFY-A7READY (0 CRITICAL / 0 MAJOR / 1 MINOR).
Machine mirror: `six_symbol_census.json`. Primary evidence = the six per-symbol dossiers; this file is an index.

**Law: data-ready ≠ scored-authorized.** No dimension below authorizes scoring. Gates unchanged:
NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER; ES 24 frozen; PB2 HOLD; PB3 PARK; 6F NOT_RUN_DATA_ABSENT;
all fees MODELED COST / VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW (A7-fee READY-NOT-RUN, D2 open).

## Census (6 symbols × 8 dimensions)

| Sym | 1 identity/tick | 2 O1M cov+holes | 3 roll/expiry | 4 session/holiday | 5 event PIT | 6 fee/sprd/slip/BBO | 7 trial budget | 8 repro/A7 |
|---|---|---|---|---|---|---|---|---|
| ES | PASS | PASS (4,204 sess; era ~97–100%) | PASS (68/68 re-derived; 66/66 data-side; OBSERVED) | PASS (17/17y; 2026 verified 23/23 from bytes) | PASS (CLOSED-PREP) | **BLOCKED** (D2/D3) | **BLOCKED** (36>24, D4) | PASS (repro from cache bytes; A7 READY-not-run) |
| NQ | PASS | **PASS-REPAIRED** (panel v3 6,780,608; hole closed; 0 NaN sessions) | **PASS-REPAIRED** (66 rolls; 2020-03-19 PIT crossover; 0 cease-guard violations; dte 0–45) | PARTIAL (2026 weekly = sibling-round claim, not re-verified this round; deviations NOT_OBTAINED) | PASS (CLOSED-PREP ptr) | **BLOCKED** (2.24 MODELED; D2/D3) | census recounted; families gated (sibling-after-cost/clock) | PASS (**REPRODUCED** identical digests) |
| 6E | PASS | measured (held 1,746 sess) | expiry **66/68** (ECH26+ECM26 closed; ECU26/ECZ26 NOT_OBTAINED); roll **MEASURED** 27 switches, lead 13–19d | PARTIAL (**34/42** windows; 8 aged-out INCONCLUSIVE) | PASS (FOMC 30 + BLS vintage law) | **BLOCKED** (2.46 MODELED; D2; e.1 alias PARTIAL) | 648 no-ceiling recounted | re-measures verified; A7 READY-not-run |
| 6B | PASS | measured (held 1,746 sess) | expiry **62/68** (first post-2018 calendar found; 2023Q1–24Q2 NOT_OBTAINED); roll MEASURED 27 | **0/42 NOT_OBTAINED** (documented absence) | PASS (BoE MPC 30/32) | **BLOCKED** (2.46 MODELED; D2) | 648 no-ceiling recounted | re-measures verified; A7 READY-not-run |
| 6J | PASS (**orientation PROVEN** own slice; notional $79,787.50) | 1,745-session chain; 2023 = 2 holiday weekdays only | expiry **58/68** (2023/2026 qtrs confirmed absent from captures); k=5 law documented (2022-09-20) | PARTIAL (2023 holes = 2 holiday weekdays) | PARTIAL (BoJ dates, no stamps — owner) | **BLOCKED** (RT $67.42 = 8.4499bp MODELED; D2; BBO NOT_RUN D5) | 6J6A census ~29–36 | re-derivations bit-identical |
| 6A | PASS **RESOLVED-PER-ERA** ($10/tick ≤2020-11-20; $5 from 2020-11-23) | measured | expiry **62/68** (Mar/Jun-2023 confirmed absent); roll **MEASURED** 27 rolls; **2 cease-guard violations** baseline k=5 → 0 with explicit guard | Mar/Jun-2023 zero missing weekdays | PASS-ish (RBA+DFF present; ABS/China NOT_RUN) | **BLOCKED** (D2 + era-aware cost law not yet frozen) | **PB3 PARK** (restated) | recomputes exact |

## What changed this round (verified)

1. **NQ ERRATUM-F1 obligation DISCHARGED**: alias view rule applied; 92,075 bars / 24,686,121 vol recovered
   exactly; 1 roll date corrected to the real PIT crossover (2020-03-19); the BEFORE chain's single
   cease-guard violation (NQH0_2020 dead-held 49 sessions) eliminated; dte>45 quarantine retired;
   reproduction byte/logical-identical. Cached v3 = corrected canonical candidate for any future NQ cycle.
2. **6E/6B calendar moved**: FX expiry cumulative 236/272 → **248/272**; first per-product 6E holiday
   table (34/42); first post-2018 archived 6B calendar; roll_rule cell upgraded NOT_RUN → MEASURED (27/27).
3. **6A two new laws measured**: tick conflict RESOLVED-PER-ERA from data ($10 → $5 at the 2020-11-20/23
   weekend); k=5 roll measured with **2 cease-guard violations** (2024-12-17, 2026-06-16 — the 6J
   2022-09-20 pathology, now 3 manifestations across 3 symbols: 6J ×1, 6A ×2, NQ-before ×1).
4. **Sibling-round over-claim caught**: Q5 coverage JSON lists 8/23 ES deviation captures that are absent
   on disk and absent from Q5's own fetch_log (no claimed cell depends on them) — MINOR, carried to owner.

## Blocking surface for any future scored decision (unchanged by this round)

- **D2/D3** fee account-verification (all 6 symbols) — A7-fee packet READY, NOT RUN, not authorized.
- **D4** ES trial budget 36 vs frozen 24 (headroom 0).
- PB2 HOLD (6E/6B), PB3 PARK (6A), NQ sibling-gates, 6J BoJ stamps.
- Residual NOT_OBTAINED calendar cells (see per-symbol dossiers) — none has a legitimate archive source
  identified; options in OWNER_DECISIONS.

— End SIX_SYMBOL_CENSUS.md.
