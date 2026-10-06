# SPEC_6B — British Pound FX futures (6B) PRE-SCORED packet draft, load-bearing laws

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **FXEB**, 2026-10-05. Worktree/branch/HEAD
  as in `SPEC_6E.md` header. PREP-only draft: **0 PnL, 0 scored runs, 0
  conditional-on-signal statistics.** Missing evidence = `NOT_RUN`/`NOT_OBTAINED`, never
  inferred PASS. **6B carries its own identity table, calendar law and cost numbers; no
  cell is shared silently with 6E.**
- **CONDITIONAL-ON-PB2-LIFT DRAFT. PB2 remains HOLD by Co-Owner ruling (PLAYBOOKS_DRAFT
  r5 §2; PB2_ANCESTRY_COURT_DRAFT §d; `PB2_HOLD_RESTATE.md` sha256
  `88386aa3443ac8713a1dc33eba628910d04c088cc2a9d64fce8238c9d9d5a75b`). NOTHING here is
  executable today; PB2 lift is NOT treated as given and is not asked for.** 6B carries
  two additional symbol-specific blockers beyond 6E's: the holiday/deviation grid is
  **0/42 NOT_OBTAINED (documented structural absence)** and the 2023Q1–2024Q2 expiry
  cells are NOT_OBTAINED — both fail-closed below.

## 1. Instrument identity (6B)

| field | value | status | source |
|---|---|---|---|
| Product | CME British Pound FX futures, Globex code `6B` | FACT (baseline restate) | `DATA_READINESS_6B.md` §1 (`FUTURES-SIX-READINESS-20261004/fx_eb/`, sha256 `555ab253…c4cf7`); machine twin `fx_eb_readiness.json` sha256 `adc15c67…52eb`, `6B.dims.1_identity_tick` |
| Contract size | **GBP 62,500** vs USD | PASS_BASELINE_RESTATE | same rows; baseline `dossiers_v2/6B_DEEP_v2.md` §0 + v1 §1 pins recorded in `fx_eb_readiness.json.artifact_pins` |
| Quotation | **USD per GBP** (implied USD quote currency) | PASS_BASELINE_RESTATE | same rows ("62500 GBP, USD quote") |
| Min tick | **0.0001 = $6.25/tick** | PASS_BASELINE_RESTATE | same rows, `tick: "0.0001", tick_value_usd: 6.25`; cross-verified `FXEB_K6_GATES.md` §0.5 declared tick 100,000 int-nano = $6.25 |
| Tick in data fixed-point | **100,000 int-nano** (price × 1e-9) | MEASURED | `FXEB_K6_GATES.md` §0.5/§4 (sha256 `861a04bd…0841`); `tick_constancy_6e6b.json` sha256 `b6b9927e…fca2` |
| Tick constancy at 2020-11-23 | **CONSTANT** — GCD == min-increment == 100,000 int-nano in all 5 sampled windows; close-on-grid share 1.0 | MEASURED (D-2 step iii CLOSED) | same files |
| Tick-value arithmetic | $6.25/tick ⇒ tick_value = 0.0001 × 62,500 [DERIVED, arithmetic check: 6.25] — consistent with the restated identity row | DERIVED (check only) | this lane |

Anything not in the table above (margin, delivery terms verbatim): **NOT_RUN** (sizing
facts only, court §b4). No verbatim 6B weekly-hours spec capture exists (§3).

## 2. Data / panel contract (6B)

- Outright 1m panel: **≈2.55M bars (2,549,633 annotated rows), 2020-01 → 2026-09-30**,
  5 vendor parquet files, full shas pinned in `6B_DEEP_v2.md` §0 [FACT,
  `DATA_READINESS_6B.md` §2; K6GATE §0.1 row count].
- Files re-hashed by THIS lane in THIS worktree (read-only single-shot; locks
  FREE_PROVEN before/after):
  - `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6B_cache/6b_annotated_1m.parquet`
    — sha256 `6133b0e7dec514b49de4c850585cb9c093bbbfca318f79b1db67a9b69166b322`, 57,985,992 bytes.
  - `…/6B_cache/6b_outright_1m.parquet` — sha256 `3e13a452e74d9770d1ce829a6bab94900ea4a839271c9db063dfd4aa7ff7f6dd`, 51,446,342 bytes.
  - `…/6B_cache/held_calendar.parquet` — 1,746 sessions 2020-01-02..2026-10-01;
    sha256 `dff43c4cab5f5419b07d9ac042480801b7ea7c039a037ecb9ea63aa8c179d09f` (equals the
    readiness pin), 11,369 bytes.
  - `…/6B_cache/chain_calendar.parquet` — sha256 `9cc849c22d2c32e4cdc0b98d67c26b43918bf078036ce3ea34459c5eaf258801`.
- **No `contract_registry.json` exists in `6B_cache`** (6E-only artifact) — the
  registry-gap cross-check is NOT computable for 6B; the official-calendar cross-reference
  is used instead [disclosed, `DATA_READINESS_6B.md` §3]. Two-rule roll agreement
  1,458/1,746 sessions (83.5%) documented in dossier v2 §3.
- Schema law: fixed-point 1e-9; serials/calendar-spreads excluded by design (57 dead
  serial clusters); strays isolated (`6BM5` quarantined) [carried,
  `FX_HYPOTHESES.md` §1.10].
- Held-contract restriction load-bearing: 469,545 of 2,549,633 rows share a timestamp
  with a different contract [MEASURED, K6GATE §0.7]; same held-only law as 6E applies.
- 0 weekend bars, exactly 1 maintenance-break bar in 6.8y [carried, `6B_a7_quality` cited
  `FX_HYPOTHESES.md` §4.1].

## 3. Session law + DST (6B)

- Template: **Globex ~23h, 17:00 CT (D-1) reopen → 16:00 CT (D), 60-min maintenance
  break** — same measured template class as 6E but independently evidenced on the 6B
  chain (1 maintenance-break bar in 6.8y). 348 Sunday-evening opens in the held chain.
- **No verbatim weekly-hours spec capture for 6B exists** [FACT, `DATA_READINESS_6B.md`
  §4 — "No verbatim weekly-hours spec capture for 6B"]. The holiday/deviation grid is
  **0/42 NOT_OBTAINED with documented structural absence** (product id 42 in NO archived
  by-product capture; CAL-EB two-route proof) — the largest remaining 6B data hole.
- DST: Europe/London local-clock law, DST-proven via the **BoE anchor minute-720
  stability** — MPC spike minute exactly 720 London-local, minute-stable across 8 UK/US
  DST-mismatch dates (07:00 CT except 2022-10-06 06:00 CT) [MEASURED,
  `6B_a4_events.json:boe` cited `FX_HYPOTHESES.md` §2.1].
- Segment labels: `6B_deep_lib.CITY_SEGMENTS` tz-aware labels (asia_early / asia_core /
  lon_pre_boe / lon_us_overlap / us_rth / us_close / other) — no separate `boe_release`
  label exists in the annotated column (K6GATE §3 discloses this; nothing re-segmented).
- London-morning share drift: 28.7% (2020-21) → 23.7% (2025-26) [MEASURED,
  `6B_a2_sessions.json:london_morning_share_07_12`] — mandatory built-in falsifier split
  for any 6B F1/F3 spec.

## 4. Calendar / roll law (6B) — details in CALENDAR_PIT_POLICY_6E_6B.md

- Expiry official cells 2023-2026: **10/16 OBTAINED** (BPU24..BPZ26 via this lane-family's
  Wayback capture of `ProductCalendar/Download.xls?productId=42` @2024-09-03 vintage,
  16,896 wire bytes, own xlrd parser); cumulative **62/68**; **2023Q1–2024Q2
  (BPH23..BPM24, 6 cells) NOT_OBTAINED — structural**: archived 6B calendars max out at
  Future/42 2018-04-08 (pre-span) and the Download.xls service drops expired contracts
  (cross-vintage drop demonstrated: BPU24/BPV24 present @2024-09-03, gone @2024-11-08;
  21/21 shared rows exact) [FACT, `fx_eb_expiry_2023_2026.json` sha256 `cf07d4e2…1ef07`;
  `CAL_EB_REPORT.md` sha256 `25678890…9ef77`; capture `pcal_42_6b_dl_20240903.xls`
  sha256 `ea9b129e…f9910e`, `pcal_42_6b_dl_20241108.xls` sha256
  `b38ef64e40c15823f07ea4cae737738e52c6b98c627dbfebf35841b09a8fb105`].
- Roll: **27 switches / 1,746 sessions, 28 contracts; lead 17 days** for the
  2024Q4→2026Q3 switches cross-referenced to the new official cells, **14 days** into the
  2026Q4 contract; earlier switches carry observed-expiry leads only [MEASURED,
  `cost_roll_events_fxeb.json`]. The PIT **k=5 + cease-guard** rule is the 6B-carried
  roll law (`FX_HYPOTHESES.md` §1.4, thin-window 1,069..13,222 contracts/day measured);
  its freeze-time binding to official dates remains **law-pending** exactly as for 6E
  (draft in `SPEC_6E.md` §4 applies mutatis mutandis, with 6B's own switch table).
- Holidays: **0/42 windows NOT_OBTAINED — documented structural absence** (709-row CDX:
  standalone id=42 = 0 rows; advisory/settlement PDFs = clearing memos with zero product
  hours; live service BLOCKED_TRANSPORT). **No holiday-adjacent exclusion is
  implementable for 6B; any future 6B spec's holiday stand-aside stays blocked on this
  grid — fail-closed posture: holiday-adjacent sessions are NOT excluded and the hole is
  declared on every 6B result** (K6GATE §2 verdict; `DATA_READINESS_6B.md` §4/§10).

## 5. Event PIT law (6B)

- **BoE MPC (6B primary overlay, FX-F2 base)**: 32 listed dates 2023–2026, **30 in
  panel** through 2026-09-30 (8/8/8/6 by year); **11 rate-change decisions in panel**
  (5 in 2023, 2 in 2024, 4 in 2025) cross-checked against
  `normalized/boe_bank_rate_tidy.parquet` (matches official Bank Rate history through
  2025-12-18); remaining 19 in-panel dates are hold decisions; 2026-11-05/2026-12-17 are
  forward-scheduled dates, never decisions [FACT/MEASURED, `DATA_READINESS_6B.md` §5].
  In-panel 2020-2026 MPC calendar: 56 dates (`6B_deep_lib.load_mpc_calendar()`).
  Decision-time-knowable stamps: Bank Rate decisions + minutes at 12:00 Europe/London
  (minute-720 anchor, DST-proven); MPC first-5m volume ×18.7 (7,090.5 vs 379.5), ±30m
  ×5.2 [MEASURED, `6B_a4_events.json:boe` cited `FX_HYPOTHESES.md` §2.1]. Change-vs-hold
  split 22/34 measured, reported as descriptive strata, base pools.
- **FOMC (6B secondary stratum)**: same 30-decision/58-in-panel inventory as 6E;
  first-5m ×9.5 on 6B [carried, `6B_a4_events.json:fomc`]. 2020 emergency timings
  excluded from base.
- **BLS 08:30 ET (FX-F3 base days)**: identical CPI/EMPSIT 204/204 vintage law as 6E
  (§5 of SPEC_6E), applied to 6B days via the same stamps.
- Vintage law: as-of decision date only; current-calendar inference FORBIDDEN.

## 6. Cost contract (6B) — full derivation in COST_CONTRACT_6E_6B.md

Tier-1 all-in **2.46 USD/side MODELED** (0.85 + 1.60 + 0.01; GBP alias row present but
6B never printed verbatim — mapping PARTIAL). Modeled RT ladder **6.3–11.2 bp** across
S1/S2/S3 ×1.0 at reference px 1.30 (notional $65.0k–88.8k across px 1.0392–1.4205;
slippage bp computed at the 1.30 reference per the family cost table). **6B is the
cost-weakest leg of the whole FX portfolio: modeled RT is 2.1–3.7× the dead spot proxy
3.0 bp** (court §b4/`FX_HYPOTHESES.md` §7). BBO NOT_RUN (D5); VERIFIED_VS_ACCOUNT=NOT_RUN;
UNDER REVIEW. "measured cost"/"complete cost" forbidden.

## 7. Folds, warmup, K-views (6B) — DRAFT law, binding only post-lift

- Folds: identical draft boundaries as `SPEC_6E.md` §7 (F1 2020-01..2021-12 ·
  F2 2022-01..2023-12 · F3 2024-01..2025-06 · F4 2025-07..2026-09) — 6B's own chain span
  is the same 1,746 sessions; boundaries re-fixed at any future registration freeze.
  Folds multiply evaluation, never identities.
- Warmup: 60 held sessions at each fold head (family law); 252-session alternative is an
  owner choice (P5-OD11).
- Declared K-views (6B-specific mandatory): K5 era 2020-22 vs 2023-26 (6B weekday
  reopen-gap dispersion FELL by a third across eras, 0.0486% → 0.0306% — anatomy only);
  **London-share-drift split 2020-22 vs 2023-26 (28.7→23.7%) as built-in falsifier**;
  DST-mismatch split (BoE minute-720 anchor); 2022 LDI/fiscal crisis as declared
  high-vol stratum (6B top-8 stress windows end 2022-11-28..12-20); BLS vintage regime
  2025.

## 8. Baselines / controls (6B, CONV-D per family per leg)

Same CONV-D structure as `SPEC_6E.md` §8 (8 core S2 + 3 scored controls = 11 per family
per leg; C1-class clock-only shadow single-seed/single-delay per PB1 C1 law; C2
always-on; C3 anchor). 6B family-specific negatives: F2-6B negative = FOMC stratum
(×9.5 vs ×18.7 intensity ordering falsifiable); F1-6B carries the London-share-drift
split + 6E/6B co-occurrence; F3-6B same canceled/unclassified negatives; F4-6B carries
**two standing gates**: the anatomy gate is now MEASURED (gap std weekday 0.0400%, all
pairs 0.0804%, Sunday 317 — `FXEB_K6_GATES.md` §2/§5 M2b verdict MEASURED) but the
**holiday stand-aside (ii) remains BLOCKED on the 0/42 grid**, so the 6B F4 leg stays
spec-gated exactly as before. The baseline-labeling finding (M2c): the owning docs'
"reopen-gap 0.3778%" was the 08:30-CT RTH-open gap; the true 17:00 reopen gap on 6B is
0.4286% RTH-method / 0.0804% all-pairs reopen — recorded append-only, nothing overwritten.

## 9. Verdict criteria + power honesty (6B)

- Gates: same G-series as `SPEC_6E.md` §9, computed on 6B's own chain; 6B-specific
  additions: F1/F3 London-drift split mandatory; F4-6B holiday gate stands.
- **Power honesty (6B numbers)**: F1 census n=1,342 base triggers ⇒ MDE-at-n ≈ **4.2
  bp/trade** (2.80 × 54.9bp/√1,342) vs modeled RT 6.3–11.2 bp — **6B's MDE sits BELOW
  its cost floor at the census n**: an edge at or below cost is both undetectable and
  unprofitable; the pre-registered death criterion applies with extra force. F2 n=56 MPC
  days ⇒ MDE ≈ 20.6 bp vs RT 6.3–11.2 bp (detectable only at tail-event scale). F3
  known-type n≈165 ⇒ MDE ≈ 12.0 bp. F4 weekday reopens n=1,283 (gap std 0.0400%).
- Court finding binds identically (power floor = cost floor at n≈300–900; a null at
  program-feasible n is the pre-registered death, NOT evidence of absence).
- Census gate ≥500: **6B PASS (1,342 ≥ 500)** [K6GATE §5 M1]. Schedules nothing; PB2
  HOLD unaffected; court §b1.1 anatomy NOT_RUN stands.

## 10. NOT_RUN register (6B, carried + this lane)

1. BBO / execution realism — NOT_RUN (D5).
2. Fee account verification — NOT_RUN; UNDER REVIEW.
3. FX Variant-A reg composition on the FX tier — DERIVED; owner ruling P5-OD7.
4. **Holiday/deviation grid 0/42 — NOT_OBTAINED (documented structural absence)**; no
   permitted route exists (CAL-EB closure attempt exhausted 10/35 budget, 0 new cells).
5. 2023Q1–2024Q2 expiry cells (6) — NOT_OBTAINED (structural expired-contract drop).
6. `contract_registry.json` — NOT_OBTAINED for 6B (6E-only artifact); official-calendar
   cross-ref substitutes.
7. 1m trigger-time anatomy (court §b1.1) — NOT_RUN.
8. Per-trade dispersion; F4 threshold value; F5 CIP vintages + SOFR source; surprise
   vintages; ATR(20d) levels — NOT_RUN (same items as SPEC_6E §10).
9. Weekly-hours verbatim spec capture for 6B — NOT_OBTAINED (structural).

— End SPEC_6B.md. Conditional-on-PB2-lift draft; nothing herein registers, schedules,
scores, or reopens any standing ruling.
