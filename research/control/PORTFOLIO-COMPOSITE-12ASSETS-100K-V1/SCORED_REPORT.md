# SCORED REPORT — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (Stage-C)

Written 2026-09-30T16:00:21Z (Stage-C scored evaluation; GO `SCORED EXECUTION` consumed). Policy digest `93077163796abddc…` (verified MATCH at entry); winner V3 frozen at Stage-B with the honest NEGATIVE TRAIN objective.

## 1. Verdict (typed, provisional per plan §7 — owner confirms)

**POLICY_NO_INCREMENTAL_VALUE** — failed governing bars: ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']. Negative closes are first-class under the honest prior; no parameter was touched and no re-run was performed except the documented determinism check (journal/metrics byte-identical: True/True).

## 2. Bar matrix (every governing bar with its numbers)

| bar | status | key numbers |
|---|---|---|
| P1-B0 | PASS | net(P) +$603,340.60 vs 0 |
| P1 (PRIMARY) | FAIL | net(P) +$603,340.60 vs net(B1) +$688,604.03; DD(P) -$418,227.97 vs DD(B1) -$397,156.85 |
| P2a | PASS | vs B2: net +$603,340.60 vs +$356,100.53; DD -$418,227.97 vs -$798,001.22 |
| P2b | FAIL | vs B3(EURUSD-S013): net +$603,340.60 vs +$1,731.42; DD -$418,227.97 vs -$442.77 |
| P3-c1 | FAIL | obj(P) -2449821.71 exceeds 0/128 seeds (need ≥ 122) |
| P3-c2 | FAIL | net +$603,340.60 vs median +$194,094.57; DD -$418,227.97 vs median -$209,634.89 |
| P4a | FAIL | net +$603,340.60 vs +$54,024.18; DD -$418,227.97 vs -$366,331.83 |
| P4b | PASS | net +$603,340.60 vs -$256,347.66; DD -$418,227.97 vs -$1,428,762.16 |
| P4c | FAIL | net +$603,340.60 vs +$591,219.62; DD -$418,227.97 vs -$413,428.44 |
| P5a | FAIL | DSR 0.000208 (need > 0.95); SR̂ 0.073252 vs SR₀ 0.32177531461622605 (N=134, N_eff=29, V=0.024414); PSR 0.850919; raw-N DSR 1e-06 |
| P5b | PASS | PBO 0.346309 over 12870 combinations, 70 trials (need ≤ 0.5) |
| P6a | FAIL | @×1.5 net +$424,355.61 vs +$519,684.52; DD -$516,661.81 vs -$372,557.22 |
| P6b (reporting) | REPORTING | @×2.0 ΔPnL +$80,927.60, ΔDD -$126,387.82 (policy ×2.0 net +$494,103.59) |
| P6c (disclosure) | NO_LABEL | net(P@×2.0) +$494,103.59 (no sign flip) |
| P6d | PASS | @p90 net +$739,806.09 vs +$503,917.39; DD -$384,366.61 vs -$408,006.06 |
| P7 | FAIL | f0 net +$541,483.96 (share 89.7%, DD 64855/cap 104557); f1 net -$149,566.12 (share -24.8%, DD 350066/cap 104557); f2 net +$21,675.53 (share 3.6%, DD 119138/cap 104557); f3 net -$78,294.18 (share -13.0%, DD 139346/cap 104557); f4 net +$210,424.95 (share 34.9%, DD 183020/cap 104557); f5 net +$73,626.69 (share 12.2%, DD 136979/cap 104557); f6 net -$231,109.36 (share -38.3%, DD 306777/cap 104557); f7 net +$215,099.14 (share 35.7%, DD 63388/cap 104557) |
| P8 | FAIL | 7 removal(s) break P1-semantics |
| B8 ORACLE (reporting) | REPORTING | oracle net +$388,900.79, DD -$508,992.99 vs policy net +$603,340.60, DD -$418,227.97 |

## 3. Per-arm table (identities, pooled net, pooled maxDD)

| arm | tier | net PnL (pooled) | maxDD (USD) | fills | turnover USD | fold-edge FF cost | digest |
|---|---|---|---|---|---|---|---|
| B1_ALWAYS_ON | ×1.0 | +$688,604.03 | -$397,156.85 | 2363 | 2,732,067,903 | 7,114.83 | `806310bb7631` |
| B1_MO_EURUSD-S009 | ×1.0 | -$2,127.77 | -$2,251.39 | 126 | 1,356,346 | 16.00 | `b85f64921c0c` |
| B1_MO_EURUSD-S013 | ×1.0 | +$1,731.42 | -$442.77 | 238 | 2,570,720 | 7.55 | `2727d1e51646` |
| B1_MO_EURUSD-S046 | ×1.0 | +$79.62 | -$797.82 | 94 | 1,019,522 | 10.35 | `25b1783b4ed6` |
| B1_MO_GBPUSD-S002 | ×1.0 | +$1,037.46 | -$433.47 | 490 | 6,221,144 | 0.00 | `a54c8c85aaf2` |
| B1_MO_GBPUSD-S017 | ×1.0 | -$318.71 | -$358.91 | 78 | 974,657 | 0.00 | `a587d9838072` |
| B1_MO_USDJPY-S002 | ×1.0 | -$248,990.41 | -$487,954.44 | 82 | 119,043,540 | 2,696.75 | `39a289373fe1` |
| B1_MO_USDJPY-S003 | ×1.0 | +$216,221.02 | -$478,225.54 | 55 | 59,120,237 | 5,808.40 | `c7b0f1ad1bdd` |
| B1_MO_USDJPY-S014 | ×1.0 | +$109,448.16 | -$58,493.63 | 288 | 413,835,030 | 595.35 | `767c35d5cbfe` |
| B1_MO_USDJPY-S023 | ×1.0 | +$57,454.28 | -$125,153.43 | 16 | 23,820,220 | 385.35 | `15871ef719fc` |
| B1_MO_USDJPY-S026 | ×1.0 | +$9,203.41 | -$299,849.12 | 1844 | 2,634,017,910 | 3,446.75 | `552b7fb6c19a` |
| B1_MO_VC2-LVNFAIL-EURUSD | ×1.0 | +$75.30 | -$87.81 | 74 | 799,865 | 0.00 | `ea756ddcd7e8` |
| B1_MO_VC2-LVNFAIL-USDJPY | ×1.0 | -$384.70 | -$13,577.00 | 42 | 58,794,330 | 0.00 | `c34f2f141196` |
| B1_P90 | ×1.0 | +$503,917.39 | -$408,006.06 | 2178 | 2,334,197,493 | 13,349.74 | `7a685d58c545` |
| B1_X15 | ×1.5 | +$519,684.52 | -$372,557.22 | 2061 | 2,106,961,811 | 10,672.24 | `fd402df50a56` |
| B1_X20 | ×2.0 | +$413,176.00 | -$247,756.14 | 1856 | 1,705,761,092 | 14,229.66 | `1994dde9ac1e` |
| B2_EQUAL_WEIGHT | ×1.0 | +$356,100.53 | -$798,001.22 | 2220 | 2,880,877,212 | 7,691.92 | `306febf02a4c` |
| B3_BEST_SINGLE | ×1.0 | +$1,731.42 | -$442.77 | 238 | 2,570,720 | 7.55 | `3fbac7a653cb` |
| B5_CLOCK_GATE | ×1.0 | +$54,024.18 | -$366,331.83 | 2673 | 2,892,918,722 | 3,745.38 | `1ae2de8f1a8a` |
| B6_INVERTED | ×1.0 | -$256,347.66 | -$1,428,762.16 | 197 | 231,766,366 | 4,252.14 | `ba112c3a79e1` |
| B7_LAGGED | ×1.0 | +$591,219.62 | -$413,428.44 | 2370 | 3,295,287,713 | 8,854.11 | `5a64325b997e` |
| B8_ORACLE | ×1.0 | +$388,900.79 | -$508,992.99 | 1380 | 2,560,963,278 | 8,515.64 | `d2d7d7413162` |
| POLICY | ×1.0 | +$603,340.60 | -$418,227.97 | 2436 | 3,325,305,734 | 6,925.86 | `0f58a25a1c21` |
| POLICY_MO_EURUSD-S009 | ×1.0 | -$83.80 | -$83.80 | 2 | 22,739 | 0.00 | `1ccb0fdc8503` |
| POLICY_MO_EURUSD-S013 | ×1.0 | +$1,731.42 | -$442.77 | 238 | 2,570,720 | 7.55 | `c590914c1dcd` |
| POLICY_MO_EURUSD-S046 | ×1.0 | +$79.62 | -$797.82 | 94 | 1,019,522 | 10.35 | `23c50ccfa6a6` |
| POLICY_MO_GBPUSD-S002 | ×1.0 | +$1,037.46 | -$433.47 | 490 | 6,221,144 | 0.00 | `cafaf1956113` |
| POLICY_MO_GBPUSD-S017 | ×1.0 | -$95.02 | -$321.19 | 56 | 686,171 | 0.00 | `79ee101442f3` |
| POLICY_MO_USDJPY-S002 | ×1.0 | +$137,883.41 | -$182,201.55 | 34 | 46,606,640 | 2,051.40 | `d55a97a25063` |
| POLICY_MO_USDJPY-S003 | ×1.0 | +$216,221.02 | -$478,225.54 | 55 | 59,120,237 | 5,808.40 | `875af9abf831` |
| POLICY_MO_USDJPY-S014 | ×1.0 | +$109,448.16 | -$58,493.63 | 288 | 413,835,030 | 595.35 | `c065868a5f23` |
| POLICY_MO_USDJPY-S023 | ×1.0 | -$50,550.35 | -$70,024.32 | 2 | 2,885,210 | 0.00 | `af291fea740e` |
| POLICY_MO_USDJPY-S026 | ×1.0 | +$9,203.41 | -$299,849.12 | 1844 | 2,634,017,910 | 3,446.75 | `fb25320827eb` |
| POLICY_MO_VC2-LVNFAIL-EURUSD | ×1.0 | +$150.69 | -$10.54 | 30 | 320,231 | 0.00 | `b3d994cbc056` |
| POLICY_MO_VC2-LVNFAIL-USDJPY | ×1.0 | +$280.20 | -$7,301.40 | 28 | 37,639,470 | 0.00 | `d81b66ea221d` |
| POLICY_P90 | ×1.0 | +$739,806.09 | -$384,366.61 | 2184 | 2,759,848,994 | 9,104.08 | `9e80a24c08dc` |
| POLICY_X15 | ×1.5 | +$424,355.61 | -$516,661.81 | 2048 | 2,466,323,174 | 4,525.13 | `1be5c3a2ee84` |
| POLICY_X20 | ×2.0 | +$494,103.59 | -$374,143.96 | 1797 | 1,906,490,954 | 5,754.11 | `248a255e78c3` |
| B0_FLAT | ×1.0 | +$0.00 | +$0.00 | 0 | 0 | 0 | by construction |
| B4_RANDOM_GATE (128 seeds) | ×1.0 | median +$194,094.57 | median -$209,634.89 | [-194,065..588,810] | — | — | one identity |

## 4. Fold-edge force-flat cost companion (skeptic F-7)

Force-flat charges arms differentially by their fold-edge holdings (B1/B2 hold at every edge by construction; the policy may already be flat). Per-arm totals are in §3; per-arm per-fold totals are in each arm's metrics.json (`per_fold[].force_flat_cost_usd`). P1's PnL leg should be read net of this asymmetry.

## 5. Honest disclosure (what these numbers mean)

1. **Honest prior, stated at freeze**: the winner's TRAIN objective is NEGATIVE (−$1,054,702; deflation term $1.06M dwarfs TRAIN net +$138k). No TRAIN-side edge claim was made; Stage-C was expected to close negative, and any positive bar outcome would itself have required scrutiny.
2. **Pooled-test-vs-selection overlap (inherent to the registered design, disclosed)**: the fold calendar's expanding-train law holds PER FOLD (fold k's TRAIN ends ≥1 week before fold k's test start and never touches any later fold's window), but Stage-B froze ONE policy on the LONGEST TRAIN prefix (through 2025-06-20). Folds 0–5's test windows (2022-01-07..2024-12-27) and fold 6's window except its last 2 Fridays therefore lie INSIDE the policy's selection data; only fold 7 (2025-07-04..2025-12-26) is strictly post-selection. The pooled evaluation is the frozen E-Law-2 law; this overlap is why P5's IS/OOS double-correction disclosure (PSR alongside DSR) is carried.
3. **Book law**: per-symbol virtual $100k sub-accounts (the frozen Stage-B book law); portfolio equity = $100k + Σ sub-PnL; fold-edge force-flats keep every fold flat at both edges so per-fold net is an exact cash identity (residual asserted).
4. **Eligibility state is cold at the test-window start**: E1 arms 26 weeks after the engine's first TEST decision (the same engine law the TRAIN runs used; disclosed, not re-derived from TRAIN state).
5. **Realization notes**: B2 divides the policy's realized per-decision gross heat equally across its active legs (per-leg cap 100k units); B5 clock k = round-half-up(1/duty) phase 0; B6 complement (the policy has no PROBATION state, so the PROBATION clause is vacuous); B7 lag = 26 weeks with TRAIN fallback for fold 0 (fail-open ON when no verdict is recorded, counted); B8 admits legs with positive B1 paper (sum-of-legs) fold nets (REPORTING ONLY); B4 chains are two-state Markov with stationary duty and per-decision flip rate from the policy's TRAIN eligibility path (realized mismatch possible where clamps bind; per-leg duty/flip in TRAIN_EXTRACT.json).
6. **Mid-flight corrections (all engine-path-neutral, disclosed per the no-silent-continue law)**: (i) the first B3 execution ran the full slate by a spec-wiring defect (its metrics were byte-identical to POLICY — caught by exactly that identity); the arm was deleted and re-run correctly; the incorrect run never entered the ledger. (ii) A schedules-assembly bug (train/test verdict nesting) crashed orchestration run 1; POLICY/B1 were re-run after the fix so the whole battery carries one code digest. (iii) The battery was killed twice by session mechanics (harness kill, then a half-written seed journal refused by the append-only law); both resumes are deterministic (completed artifacts are never re-run). (iv) P5a's first evaluation used a dedup that collapsed N_eff to 4 (wave-1 screening rows carry no cluster_id); corrected to the frozen Stage-B formula (N=134, N_eff=29, SR0 0.3218 — MORE deflation, conservative direction); the verdict was identical before and after. No policy parameter, arm input, or engine path was touched after the POLICY arm froze the code digest; bars were evaluated twice (documented correction) and no scored arm was re-run except the POLICY determinism repro (byte-identical).
7. **Costs**: measured C1/C2/C3 cells + DECLARED U2/U3/U4 bands; every number carries NET_DEFAULT_COST / PROVISIONAL_PENDING_COST_AUTHORITY. Engine fills are bar-quoted spread-once (the frozen engine law); P6d re-prices at cell p90. The sealed tail (2026-01-02..2026-06-26) was never loaded; S1 SEALED_UNTOUCHED.

## 6. Budget accounting

- Scored identities consumed: **40 / 48** (policy 1, B0 1, B1 1, B2 1, B3 1, B5/B6/B7 3, B8 1, P6a pair 2, P6b/P6c ×2.0 pair 2, P6d pair 2, P8 pairs 24, B4 battery 1 — the dispatch's 38 + the 2 mandatory ×2.0 reporting runs P6b/P6c require).
- B4 battery: **1 identity = 128 seeded sub-runs** (seeds 770000..770127, list digest `f432cdf05f8f9b8d…`) on its own budget line (E-Law 8).
- Ledger rows: **846 / 1500** (stop line 1400 respected; ~40 C-SCORED rows appended).
- Determinism: policy re-run journal/metrics byte-identical (True/True); TRAIN V3 re-run reproduced the frozen selection statistic (True).
- Heavy lock: held end-to-end for the orchestrate job (disclosed in the registry).

## 8. Evidence index

- `diagnostics/stagec/BARS.json` — the bar matrix with every number.
- `diagnostics/stagec/ARMS/<ARM>/journal.jsonl|metrics.json` — per-arm hash-chained journal (journal_row@1, SCORED-TEST) and metrics.
- `diagnostics/stagec/B3_SELECTION.json` — TRAIN-only selection, frozen before any test run.
- `diagnostics/stagec/TRAIN_EXTRACT.json` — duty/flip per leg (B5/B4) + the TRAIN determinism guard.
- `diagnostics/stagec/B4_BATTERY.json` — 128-seed battery.
- `diagnostics/stagec/POLICY_SCHEDULES.json` / `B8_SETS.json` — the frozen B2/B7/B8 inputs.
- `TRIAL_LEDGER.jsonl` — C-SCORED rows.
- `diagnostics/stagec/B4/JOURNAL_MANIFEST.json` — sha256 + row count of each of the 128 seeded sub-run journals; the journal files themselves (862MB) stay on disk unmodified and are NOT committed wholesale (repo-size decision, disclosed here; reproducible from the frozen seed list under the proven engine determinism).
