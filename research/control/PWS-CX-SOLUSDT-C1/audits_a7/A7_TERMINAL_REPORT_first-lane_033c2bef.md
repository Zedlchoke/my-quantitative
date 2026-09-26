# A7 TERMINAL REPORT — PWS-CX-SOLUSDT-C1

## VERDICT: CONFIRM_NO_ELIGIBLE_PROPOSAL

- Auditor: A7 terminal (fresh context, independent). Date 2026-09-26.
- Audited: worktree `/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-solusdt-c1/integration`
  @ branch `orca/pws-cx-solusdt-c1-integration`, HEAD `caccc2e6d587486c8f78018f39eef31b30bc29cd`
  (verified = registry row head = dispatch sha).
- The close under audit: verdict `NO_ELIGIBLE_PROPOSAL` at the F-0 gate — council
  produced 0 freezable mechanisms (P1: 0/11 direction sources survive; P2-1
  `VETOED_SAME_FAMILY`), 0/18 scored cells, 0 outcome views, GO-2 phrase
  `GO PWS CX SOLUSDT C1 SCORED EXECUTION` REGISTERED_NOT_CONSUMED (dies
  UNCONSUMED), S1 `SEALED_UNTOUCHED`, no orders, no shadow/worker touched.
- **Findings: 0 HIGH, 1 MED, 4 LOW. The MED finding does not flip the verdict —
  the load-bearing same-family kill was independently re-verified under BOTH the
  skeptic's one-sided reading and the literal two-sided proposal reading
  (see F-1).** No remediation blocks the close; the remediation notes at the
  end bind any future REUSE of the F-0 method (BNBUSDT/BTCUSDT/ETHUSDT).

## Findings table

| ID | Severity | Finding | Evidence | Verdict impact |
|---|---|---|---|---|
| F-1 | MED | The skeptic's episode/sweep/ceiling arithmetic is measured on **POSITIVE-rate runs only** (short-receiver half) while P2-1 is explicitly two-sided. My re-implementation matched every skeptic count exactly only under this convention (episodes 147/48/8/3/1, sweep 56/3/2/0). Under the literal two-sided reading, several headline zeros change: sweep "theta>=4 bps => 0 runs" is actually **12 runs** (8 with \|first-3 mean\| >= 5.23 bps), and ceiling cell (K=3, theta=5.23) is **8 negative-side episodes, not 0**. | Two-sided recompute from the same raw funding bytes: the 8 deep negative-side runs are 2020-11-22, 2020-11-26..12-02, 2020-12-12..16, 2020-12-28..2021-01-09, 2021-01-04..07 (full-mean 60.3 bps), 2022-11-08..13 (the FTX run, len 51, full-mean 55.96 bps), 2022-11-17..12-02, 2025-10-11..13 | **Kill survives, verified independently on the missing half:** (i) 8 episodes still miss the >=100-RT power floor by ~12x, so ceiling-x-power intersection stays EMPTY; (ii) 3/8 are 2022/FTX-season and the FTX run alone is 51 settlements x 55.96 bps = ~39% of all negative mass — K-CONC (2022 fold 59.1% > 0.50) remains structurally unreachable; (iii) two-sided representation rho vs funding-LEVEL shadows at theta=1.0 = 0.316–0.508 (theta=0.5: 0.422–0.703) — all above the 0.20 bar. Same-family VETO holds under both readings. |
| F-2 | LOW | Deepest-print concentration is misstated: skeptic report says "the 4 deepest settlements (-200 bps each) = 13.8% of negative mass"; the skeptic handoff says "top-5 = 13.8%". Actual from raw bytes: **7 settlements at exactly -0.02 = 1,400 bps = 19.3%** of the 7,252.5 bps negative mass. Neither 4 nor 5 matches the data; 13.8% corresponds to 5 prints. | `/tmp` recompute: count(r == -0.02) = 7; 1400/7252.5 = 19.3% | None — the error UNDERSTATES concentration; the K-CONC kill is strengthened, not weakened. |
| F-3 | LOW | FTX spacing composition: C1 recovery report (§2) and its handoff state "99 spacings of 1-4h + 2 spacings of 5-7h" and call the machine file's "101 spacings of 1-4h" loose. Actual: **all 101 non-8h spacings are 1-4h (largest exactly 4.0h); ZERO in 5-7h** — the machine file was right and the recovery "correction" was itself loose. Count (exactly 101) and window confinement (2022-11-09T16:00:00.004Z .. 2022-11-18T08:00:00.016Z) are exact in all three documents. | Spacing histogram recompute from merged funding bytes | None — the binding consequence (path accounting must use actual timestamps, never the nominal 8h grid) is unchanged. |
| F-4 | LOW | Handoff bookkeeping: `handoffs/` holds **4** schema-valid handoffs (P1, P2, skeptic, c1c2-recovery), while C3 §inputs says "5 handoff JSON dung schema". The 5th valid `zcode_orch_v3_handoff@1` with this cycle_id is the pre-GO-1 A7 child-plan review handoff (`research/control/PWS-PROGRAM-V1/plan_review/HANDOFF_a7_child_plan_review.json`, root) — defensible count, but the "handoffs/" pointer is imprecise. Also: HANDOFF_c1c2 uses `changed_files` instead of `changed_paths` (schema key deviation); HANDOFF_council_P2 has `tests: []` (its §0 measured arithmetic was taken from the C1 machine file — I verified those numbers correct: mean 0.0138 bps = 1.376e-6, median 0.86, neg 28.6%, worst -200 bps, max +33.2 bps). | Directory listing + key check of all 5 handoff files | None — every lane's evidence exists and reconciles; documentation precision only. |
| F-5 | LOW | Prose rho ranges are loose: C3/registry say "rho 0.353–0.615 at every power-viable gate" (that is exactly the theta=0.5 row); skeptic §0 says "0.31–0.61". At theta=1.0 (also power-viable, 48 episodes) the W=90 (30D) cell is 0.203 (skeptic) / 0.199–0.207 (my two implementations) — effectively ON the 0.20 bar. | Skeptic §2 table vs my recompute (max deviation 0.025 across all 25 rho cells) | None — the nearest-ancestor windows (1D/3D/7D level proxies and unconditional receiver) stay 0.31–0.62 at every power-viable gate, and the load-bearing kill is the F-0 skeleton test plus the measured gate-incrementality failure, not the marginal 30D cell. |

## Task results

### T1 — Zero-PnL / zero-look sweep: **PASS**

- `trial_ledger.jsonl` = **0 rows** (byte-verified; the only ledger file in the
  cycle namespace).
- Grep over the committed control namespace (md/json/jsonl, including handoffs)
  for `pnl|profit|equity|sharpe|drawdown|win_rate|total_return`: every hit is
  prose about outcome-blindness, pre-PnL kills, or the pre-registered price-only
  clause. **No scored outcome, no return series, no strategy PnL number exists
  anywhere in the cycle's artifacts.**
- The only numbers present are cost-book class: funding-settlement distribution
  (machine census — cost authority), spread census (cost), kline bar counts,
  representation-rho state correlations on the funding plane (explicitly NOT
  outcome data per dispatch). P2 §0's conditional-tail figures (2022 mean
  -3.25 bps, 2021 +2.61, extremes -200/+33.2 bps) are funding-census-derived
  cost statistics and reconcile with the machine file bit-exactly.

### T2 — Skeptic evidence recompute: **PASS** (independent re-implementation from raw bytes; findings F-1/F-2/F-5)

Source bytes: `data_local/funding/fapi_scan2026_H1_SOLUSDT.json` +
`fapi_scan2026a_H2_SOLUSDT.json` (sha256 `3dcac8d8…332c0` and `3c5366…1cb1c`
recomputed = machine pins); merged copy `SOLUSDT_funding.json` verified
row-identical to the H1 scan (4,385 rows); boundary duplicate dropped on
`fundingTime`.

- (a) **Headline stats — bit-exact:** n = 6,580; mean = +1.37616869300912e-06
  (bit-exact); median 8.5755e-05; sum 0.00905519000000001; neg_share
  0.28617021276595744; worst -0.02 (= -200 bps) at 2022-11-09T20:00:00.018Z;
  max 0.00332469 at 2021-02-10T08:00:00.014Z; 1 zero-rate settlement; first
  2020-09-13T16:00:00.004Z, last 2026-08-21T16:00:00.001Z.
- (b) **Persistence:** rate lag-1 autocorr **0.853296** (claim 0.853);
  P(next settlement same sign) = **0.812681** (claim 0.812); lag-2/3/6 =
  0.780/0.731/0.527 — all match the skeptic's mechanics claim.
- (c) **Representation rho table — reproduced.** Convention reverse-engineered
  and pinned: runs = maximal same-sign stretches (zeros break), gate = positive
  runs with len>=3, full-run span >= 18h, first-3 mean >= theta, state ON from
  the K-th settlement to run end, direction = receiving side; pooled Spearman
  vs trailing-W receiver shadows. Episodes 147/48/8/3/1 EXACT; occupancy
  48.5/26.7/3.9/1.9/0.2% EXACT; all 25 rho cells within 0.025 of the skeptic's
  (tolerance 0.03). The two required numbers: run-gate vs CARRY-1D (W=3) at
  theta=0.5: **+0.623 vs claimed +0.607 (delta 0.016)**; vs unconditional
  receiver at theta=0.5: **+0.615 vs claimed +0.615 (exact)**. V17-FUNDJUMP-style
  event shadow at theta=1.0: +0.333 vs claimed +0.319.
- (d) **Ceiling grid — exact under the skeptic's (one-sided) convention:**
  (K=3, 5.23) -> 0; (K=3, 6.98) -> 0; (K=5, 5.23) -> 1 episode / 12 settlements;
  (K=5, 6.98) -> 0; (K=8, 5.23) -> 1/12; (K=8, 6.98) -> 1/12. Theta sweep
  >=1/2/3/4 bps -> 56/3/2/0 runs EXACT. Ex-post full-run-mean upper bound
  5/2 EXACT. Two-sided correction: see finding F-1 (kill survives).
- (e) **K-CONC — exact:** total negative mass **7,252.5 bps** (exact); 2022 share
  **59.1%** (exact); FTX anomaly window 2022-11-09..18 share **42.2%** (exact).
  Deep prints: see finding F-2 (7 capped prints = 19.3%, worse than claimed).

### T3 — P1 enumeration sanity (hostile review): **PASS** (advisory)

I attempted to construct a direction source on the authorized observables
(1h klines OHLCV + settled funding + spread-as-cost) that escapes every fence in
P1's table, OUTCOME_EXPOSURE_MAP §4 (verified present, SRLV-PROGRAM-V1 line 99),
P-27/P-28 (verified present, LESSONS.md lines 968/1021), PROXY_NOT_ORDERBOOK and
the unlevered-taker cost reality. Candidates tried and where they die:

1. Funding second-moments (dispersion / vol-of-funding as direction) — inside
   the TRACKB1-CLASSA closing language ("ALL funding-level-derived gates —
   window/percentile/change/run transforms alike") + P-27; also P2 §3-6
   withdrawal. FENCED.
2. Price x funding conjunction (distress-divergence: price lows while payments
   run) — §2.3 filter-gate clause ("binding a filter-gate observable while
   trigger/direction/exit shape and payer are the same") + P2 §3-8. FENCED.
3. Spread-state as direction (wide/narrow book regime) — liquidity-state
   direction families dead (ILLIQ-AMIHUD et al.) + Q-7 clock-book law
   (spread state is session-clock-dominated); and the census covers 6 of 72
   months — it cannot anchor a 6-year direction source, only a cost book.
   FENCED + UNMEASURABLE at required horizon.
4. Funding-cap-proximity / cadence-aware carry variants — parameter subsets of
   the P2-1 gate (P2 §3-7); venue-cap PIT-provenance problems. FENCED.
5. Settlement-adjacent kline shapes (wick/absorption at 00/08/16 UTC) — P-28
   both-directions fence + SRLVCX1-M1-SETTLE-RESOLVE anchor + M01 family.
   FENCED.
6. Cross-pair state (SOL/BTC ratio, BTC funding spread) — requires observables
   outside this child's authorized plane (owner gate) + EOS1-E1/E2
   symbol-swap-invariant fence. UNCONSTRUCTIBLE IN SCOPE.

No escaping mechanism found. The P1 claim ("union of rows 1-11 = the entire
expressible space") withstands hostile review **under the recorded anti-variant
law**; the one honest caveat — that the law itself is what closes combinations
of dead observables, and a future owner could in principle change that law — is
exactly the R5-class revival path C3 already records. No FINDING.

### T4 — Data-gate artifact coherence: **PASS**

Committed at 2cad21d4 (verified in branch history). Three machine numbers
spot-verified against raw bytes — all three reproduce:

1. **Klines (full recount, all 72 zips — corpus is small, so I recounted
   everything, not one month):** 52,145 bars total = machine; 0 duplicate open
   times; first 2020-09-14T07:00Z, last 2026-08-31T23:00Z; ideal grid 52,265,
   **missing exactly 120** in exactly the two claimed windows —
   2022-02-26T00:00Z..2022-02-28T23:00Z (72 bars, month 2022-02 = 600/672) and
   2022-04-01T00:00Z..2022-04-02T23:00Z (48 bars, month 2022-04 = 672/720);
   all 72 monthly counts match the machine file (2021-01 = 744 checked too).
2. **Spread census 2023-05 recomputed from the raw bookTicker zip** (353 MB,
   27,234,787 CSV rows — exact match to the machine calibration number;
   systematic 1-in-13 stride, transaction_time base, bps-of-mid): all **24/24
   hourly p50 BIT-EXACT** (e.g. h00 = 0.4927443396000011, h23 =
   0.4913159898777456); max sampled spread bit-exact (96.86896223169141);
   invalid rows 0; sampled n 2,094,984 vs machine 2,094,971 (+13, the disclosed
   <=K stride warm-up, 6.2e-6 relative — immaterial and honestly disclosed).
3. **The 120-missing-bars claim** = item 1 (exact). FTX cadence anomaly:
   exactly 101 non-8h spacings, all inside 2022-11-09T16:00:00.004Z ..
   2022-11-18T08:00:00.016Z (composition nuance = finding F-3).
4. **Caveats honest:** `cross_check_vision: NOT_RUN` is kept NOT_RUN with the
   reason preserved verbatim in the machine file and the "never claim
   dual-source" condition stated in the report — fail-closed, not fabricated.
   Spread coverage honestly disclosed as 6 stratified months of the only 12
   keyless-measurable months (2023-05..2024-04) with pre-2023/2025-26 =
   UNKNOWN_WIDER and "pooled p50 must not be used as a floor for the unmeasured
   era". FTX cadence window pinned with the actual-timestamps binding condition.

### T5 — Governance reconciliation: **PASS** (findings F-4/F-5)

- **Registry row** (root `plans/CYCLE_REGISTRY.json`, 73 cycles): head =
  `caccc2e6d587486c8f78018f39eef31b30bc29cd` = worktree HEAD (verified);
  budget `{used: 0, max: 18}`; `go_phrase` = `GO PWS CX SOLUSDT C1 SCORED
  EXECUTION`, `go_phrase_state` = `REGISTERED_NOT_CONSUMED` (= dies UNCONSUMED);
  `s1: SEALED_UNTOUCHED`; workers 0. Events trail
  (`CYCLE_REGISTRY.events.jsonl`) consistent: 11:17:29Z head 0880ef24->ef3418d3
  "GO-1 consumed 2026-09-26T11:14Z under owner delegation"; 13:28:52Z head
  ef3418d3->caccc2e6 "C3 synthesis + CYCLE_VERDICT committed at child head";
  phase transitions match the artifact chain.
- **IDENTITY_REGISTRY.jsonl** (root PWS-PROGRAM-V1/): I001
  `PWS-CX-SOLUSDT-I001` has exactly 2 append-only rows — PROPOSED
  (2026-09-26T13:02:13Z) then F0_KILLED (13:59:00Z) — transition evidence paths
  all resolve inside the worktree (P2_PROPOSALS.md, HANDOFF_council_P2.json,
  SKEPTIC_F0_REPORT.md, HANDOFF_skeptic_f0.json; existence verified).
  N_registry = 1/100 ceiling.
- **Handoffs:** 5 valid `zcode_orch_v3_handoff@1` artifacts exist for this
  cycle_id — council P1 (commit 98061386), council P2 (5aadae7a), skeptic
  (9f1a8c4d), C1/C2 recovery (790542da), and the pre-GO-1 A7 child-plan review
  (root plan_review/). Dispatch/lanes each name their commit; all commits found
  in branch history. Bookkeeping nuances = finding F-4.
- **GO RECORD chain** (`OWNER_PACKET_program_open_2026-09-26.md` + delegation
  JSON): internally consistent — 10:55:14Z early-typed intent
  `GO PWS CX SOLUSDT C1 COUNCIL AND FREEZE` correctly classified per P-8 as
  EARLY-TYPED INTENT (gate did not exist: Q1/Q2 unrecorded, child plan and its
  A7 review absent at typing); 11:14:33Z owner delegation
  (`OWNER_DELEGATED_DECISION_charter_and_go1_2026-09-26.json`, verbatim quote
  recorded, interpretation_binding preserves the mission invariant — best
  result = strongest truest evidence, kills at gates are first-class); GO-1
  consumed 11:14Z only after the gate was established (child plan authored +
  A7 child-plan review AUTHORIZED_FOR_GO1_GATE delta-verified 5/5 + Q1 APPROVE
  / Q2 Option A recorded). GO-2 phrase untouched. Master stop-rule §9(a) and
  the 0.20 K-ANC bar verified present in the master plan (lines 368, 311-312).
- **Denominators (P-9):** HYPOTHESIS_LEDGER.md carries no SOLUSDT-scoped rows
  added by this cycle; nothing observed/published changed (0 scored cells).

### T6 — Decision-rights audit: **PASS**

Delegated scope (delegation JSON, `decision[4]`): "register child + worktree +
Phase C0->C3 (control plane, data plane, exposure verify, council
outcome-blind, falsifiers, trial freeze) THEN STOP before GO-2." Constraints:
no orders / no credentials / no purchases / no subscriptions; no S1 program
unseal; no push / no merge to main; no shadow/worker touch; heavy lock
respected; sealed AUDUSD/USDCAD + ETHUSDT-OPEN-SEARCH-V2 S1 inviolable; kill
laws/gates unchanged.

Executed vs scope:

| Action | In scope? | Evidence |
|---|---|---|
| Register child (registry row ACTIVE_LIGHT, worktree, branch) | YES | registry row + events 11:17:29Z |
| C0 control plane (commit ef3418d3) | YES | C0_control_plane.md; lock FREE_PROVEN; doctor HIGHs = accepted-historical class |
| C1/C2 data + PIT (commits 2cad21d4, 790542da) | YES | reports audited at T4; keyless public sources only |
| Council P1/P2 + skeptic F-0 (999baba5..9f1a8c4d) | YES | outcome-blind postures stated and consistent with T1 |
| C3 trial freeze + close (caccc2e6) | YES | 0 identities frozen, 0 cells, ledger 0 rows |
| STOP before GO-2 | YES | go_phrase_state REGISTERED_NOT_CONSUMED; no scored dev run exists |
| Orders / credentials / subscriptions | NONE | grep over cycle artifacts: no order placement, no apiKey/secret, no subscription/purchase strings (only "withdrawal" prose); C1 license posture: keyless Vision + public fapi, ToU pdf sha-pinned |
| S1 / sealed surfaces | UNTOUCHED | registry SEALED_UNTOUCHED; the single ETHUSDT contact was a read-only sha256 byte-identity comparison of our own klines copy against that worktree's copy (provenance check, no write, disclosed in INVENTORY + C2 §4) |
| Shadow/worker touch | NONE | workers 0; FX-RANGEFADE-2M-SHADOW-V1 / PROSPECTIVE-SHADOW-V1 untouched (C0-5, C2 §4) |
| Heavy lock | RESPECTED | FREE_PROVEN at audit time; all recomputation single-core streaming (census ~10-15 min/job disclosed) |
| Push / merge to main / history rewrite | NONE | branch-local commits only; root untouched except the pre-authorized charter-pack paths at 0880ef24 (in worktree) |
| Data downloads | IN SCOPE | child plan §2.1 mandates the data gate; all sources keyless public archive / public fapi endpoint; 12 GB zips left untracked per >50MB rule with full sha256 inventory (INVENTORY.md, 84 files) |

No action outside the delegated scope found. The delegation's
`interpretation_binding` explicitly preserves REJECT_ALL/empty-slate as a
first-class best outcome — the executed close is the delegated intent, not a
deviation from it.

## Required remediation (none blocking; binds future REUSE of the method)

1. Any reuse of the F-0 representation-math on the next pair (BNBUSDT per the
   approved order) must state the gate convention explicitly — the P2-1 F-0
   numbers are positive-run/short-receiver measurements; a two-sided proposal
   requires the two-sided grid (F-1). The kill logic itself transfers (my
   two-sided recompute confirms the conclusion on SOL).
2. Correct the deep-print arithmetic wherever quoted: 7 capped prints
   (-200 bps each) = 19.3% of negative mass, not "4 = 13.8%" (F-2).
3. Correct the FTX spacing composition note: 101 x 1-4h, 0 x 5-7h (F-3) — the
   original machine phrasing was accurate.
4. Handoff prose: the cycle's `handoffs/` dir holds 4 files; count 5 only when
   including the root plan_review A7 child-plan handoff (F-4).

## What stays binding

- **The close stands as a pre-PnL kill at zero outcome exposure:** 0/18 cells,
  trial_ledger empty, S1 sealed, OOS never opened (OOS = prospective D13/D26/D52,
  D104 final, per C2 — no in-history window is outcome-free for SOLUSDT).
- **GO-2 `GO PWS CX SOLUSDT C1 SCORED EXECUTION` remains REGISTERED_NOT_CONSUMED
  and now dies UNCONSUMED with the cycle closed.** Any future SOLUSDT child must
  register a new identity and pass F-0 fresh.
- **The family law of this kill is binding on the funding-carry surface for
  SOLUSDT** (and by the recorded pair-agnostic logic, on the same observable
  class for the next CX pairs): no re-clock/re-label/buffer/window/threshold/
  sign-flip/pair-swap rescue; revival only via (i) an R5-class owner-authorized
  information layer (unlock/event calendar, liquidation tape, multi-year OI,
  L2), (ii) a dated measured cost-regime break, or (iii) a dated distribution
  break — >=100 same-sign runs with entry-observable means above RT_stress/H_min
  — re-measured by this exact representation math.
- **The two-sided caveat (F-1) is itself binding knowledge:** the deep
  negative-side runs exist (8 at theta>=5.23 bps) but are power-starved and
  FTX-concentrated; a future proposer must defeat K-CONC on that structure,
  not rediscover it.
- **Registry accounting:** I001 consumed 1 of the 100-identity ceiling as
  PROPOSED->F0_KILLED; pair-child #1 of PWS-CX closed empty-slate; master
  §9(a) stop-rule (2 consecutive empty pair-children per track) has seen one
  of two — BNBUSDT remains authorized to open per the approved order, with the
  A1 recommendation recorded in CYCLE_VERDICT.md.

— A7 TERMINAL AUDITOR, PWS-CX-SOLUSDT-C1, 2026-09-26. Independent recompute
scripts: `/tmp/a7_t2_funding_recompute.py`, `/tmp/a7_t4_spread_2023_05.py`
(commands and outputs mirrored in `HANDOFF_a7_terminal.json` `tests`).
