# VERIFY_REPORT — VERIFY-A7READY, round FUTURES-SIX-READINESS-20261004

Independent fresh-context verification of the four wave-1 lanes + source /
entitlement / fee crosscheck. Measured worktree HEAD at verify start:
`9fa3fd148b7cd9b2e173e95e1c613b1f5f137066` (wave-1 checkpoint; one permitted
`rev-parse`). All recomputes from committed bytes; lane JSONs used only as
claims to test. Machine mirror: `verify_findings.json`. Raw evidence:
`handoff_audit.json`, `nq_recompute.json`, `es_crosscheck.json`,
`fxeb_provenance.json`, `fxja_crosscheck.json`, `source_inventory.json`,
`fee_a7_status.json`, `language_scan.json` (this directory).

## Verdicts

| Lane | Verdict | Basis |
|---|---|---|
| NQ-ALIAS-REPAIR | **VERIFIED** | all four spot-recomputes reproduce exactly from committed cache_v3 parquets |
| ES-READINESS | **VERIFIED** | 68/68 re-counted from rows; Q5 weekly capture byte-verified; 8/23 missing-captures confirmed |
| FX-EB-CALENDAR | **VERIFIED** | 6-cell provenance chain traced end-to-end; fetch budget 19 exact; zero unprovenanced OBTAINED cells |
| FX-JA-READINESS | **VERIFIED** | tick-era break, cease-guard violation, 6J RT arithmetic all reproduced from raw |
| Fee A7 | **READY-NOT-RUN (NOT_RUN stands)** | no D2 authorization artifact exists; not executed by this lane either |

## Recompute evidence (this lane's own numbers)

### NQ (from `nq/cache_v3/*.parquet`, not lane JSONs)
- Panel `nq_outright_1m_v3.parquet`: **6,780,608 rows** (exact); id-16908
  pre-2020-06-01 rows = **92,075** (exact), volume **24,686,121** (exact), all
  labeled `NQM0` in the committed cache.
- Held chain v3: **66 rolls**; the single `NQH0_2020 → NQM0_2020` roll dated
  **2020-03-19** (exact); cg chain also 66.
- cease_guard_audit.json claims 0/0 v3 violations + 1 BEFORE violation —
  BEFORE recompute from the baseline cache
  `FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/held_volume_k5.parquet`:
  held `NQH0_2020` sessions in 2020-03-23..05-29 = **49** (exact; strict
  post-cessation window >2020-03-20..05-29 also 49). NOTE F5: the dispatch
  task-text window 03-27..05-29 yields 45 — dispatch text imprecision, the
  audit JSON's own window and number are consistent.
- Digests recomputed with the lane's disclosed method (sorted fixed-dtype CSV
  sha256): held_volume_k5_v3 = `d359b4d4…07e3d`, held_volume_k5_cg_v3 = same,
  nq_sessions_v3 = `64203dd2…7da66` — **all three match** reproduction.json;
  run-1 stash parquets byte-equal to the live committed chains.

### ES
- `es_expiry_recheck.json` rows re-counted: **68 rows, 68 distinct quarters,
  complete 2010-03..2026-12 grid**, 67 third-Fridays + the Juneteenth-shifted
  **2026-06-18** row present. 68/68 CONFIRMED.
- Q5 weekly-session-times capture `cspecs_133_20260405234659.json`: our own
  sha256 `511fb8fa…8678c` == ES lane claim == sibling SHA256SUMS.txt; the
  claimed weekly string "Sunday 6:00 p.m. - Friday - 5:00 p.m. ET (5:00 p.m. -
  4:00 p.m. CT) …" **exists in the raw bytes** (after `&nbsp;` entity
  normalization; third TradingHours entry, Euro-equivalent cspecs layout).
- Missing-captures finding: 23 listed, **8 missing from disk, all 8 also
  absent from Q5's own fetch_log** — identical file list to the ES lane's
  claim. Finding F1 (MINOR, carried) stands.

### FX-EB
- Fetch budget: `fetch_log.jsonl` = **19 records** (17 SAVED + 2 FAILED =
  the two 0-byte CDX probes), all `curl(web.archive.org)` — matches the
  handoff exactly.
- Provenance chain (6 cells traced cell → capture → sha256 → log/sibling):
  ECH26 2026-03-16 and ECM26 2026-06-15 (sibling pcal_58 bytes re-parsed,
  sha `a97ec893…` match); BPU24/BPU25/BPZ26 from `pcal_42_6b_dl_20240903.xls`
  (sha `ea9b129e…` match; xlrd re-extraction gives 2024-09-16 / 2025-09-15 /
  2026-12-14, exact); 6E holiday window 2023-09-03 (capture sha match, in
  fetch log, id-58 deviation events re-counted = **7**, exact).
- IMM-rule scan: all **24/24 OBTAINED expiry cells** carry source_file +
  source_sha256; all 34 OBTAINED holiday windows carry capture+sha
  provenance; **0 unprovenanced / 0 rule-derived** values.

### FX-JA (from raw vendor parquets, own code)
- 6A tick-era break: 3 pre-2020-11-20 sessions (11-16/18/20) all GCD
  **100,000 int-nano = 1e-04 USD/AUD, zero odd 5e-5 prints**; 3 post-2020-11-23
  sessions (11-23/25/27) all GCD **50,000 = 5e-05**, odd-print share
  0.39–0.49. Break reproduces exactly at the 2020-11-20→23 weekend.
- Cease-guard violation 2024-12-17: independent 2024 k=5 chain (own identity
  mapping + own sessionization) held **6AZ4_2024** that day with **0 bars**
  (last bars 2024-12-16) while **6AH5_2025 traded exactly 55,675**; trailing-5
  46,490.25 vs 44,502.80 explains the baseline no-switch. Claim reproduced.
- 6J RT: 2 × (2.46 + 25.00 + 6.25) = **67.42** exact; components match
  `6j_orientation_recheck.json`.

## Handoff schema + honesty audit
All four handoffs: schema `zcode_orch_v3_handoff@1`, dispatch_sha
`d7fc6231…`, all required fields present, commit_sha null with disclosure.
FX-JA's annotated actual_start_sha carries the **controller attestation**
recorded here: worktree HEAD at wave-1 dispatch WAS d7fc6231 (measured at
creation and re-measured; DISPATCH_MANIFEST base_sha + clean tree). All
changed_paths exist on disk at HEAD 9fa3fd1 except the two disclosed
stray/ambiguous root-dispatch copies (F3, F4) — load-bearing artifacts all
present.

## Source inventory + entitlement classification (headline)
- **databento av1trim**: owner-authorized **PAID purchase** (sibling PREP
  round, owner approval 2026-10-02, ceiling $125 / hard stop $118; delivered
  **$105.81** over 72 mirrored chunks after owner rescope; backfill chain from
  DEEPRESEARCH-V2). Vendor commercial license (Databento GLBX.MDP3 / CME
  data). **This round consumed it READ-ONLY under the existing entitlement**;
  rights beyond read-only research reuse remain **UNRESOLVED (fail-closed)**
  — license text not localized, no inference made.
- **IBKR futures-10syms-v1**: existing IBKR paper entitlement (HANDOFF:
  "no orders; no subscriptions; no purchases"; 2.0GB byte cap, 1150 files
  checkpointed); NOT consumed by this round. Manifest path points at the
  visible root; corpus actually at the dot-path (F6).
- **nonprice** (fed/boj/boe/rba/ecb/mof/bls/fred/cftc/eia/...): official
  public archives.
- **Q5/sibling captures**: permitted-route archived-official (Wayback/svc);
  independently verified by this round — ES (15 captures, own sha + own
  parser), FX-EB (pcal_58 + 30 svc), FX-JA (pcal_69_6j + pcal_37_6a).
- **Own captures**: `fx_eb/captures/` = 19 files, 106,149 bytes, every
  sha256 == `SHA256SUMS_lane.txt`.

## Fee / A7 status (NOT run)
- (a) Tier-1 fees remain **MODELED COST / VERIFIED_VS_ACCOUNT=NOT_RUN /
  UNDER REVIEW** in all four lanes (ES 2.24 corrected; SPEC §5 21.006/33.506/
  46.006 UNDER-REVIEW-erratum; FX 2.46; A7-fee packet READY-not-run).
- (b) **No owner D2 authorization artifact exists**: recursive grep over both
  post-2026-10-04 control rounds (this round + sibling P3) — 71 raw hits,
  every one a negation/status restatement; sibling `OWNER_DECISIONS.md` §D2 is
  a decision *request* and states "Packet existence is NOT authorization; the
  A7 has not been run."
- (c) Therefore **A7-fee stays READY-NOT-RUN / NOT_RUN**; this lane did not
  execute it.
- (d) **D3 $0.01 NFA-basis divergence still OPEN**; both cited artifacts
  unedited vs lane pins: `SPEC_PB1_ES.md` 445f7499…, `fees_corrected.json`
  7cd65f25… (FEES_CORRECTED.md also re-hashed, match).

## Gates + language scan (54 md+json files)
0 forbidden positive claims. `scored` only in negations/blockers; `GO` only
as "awaiting owner GO" status; `edge`/`profitable`/`sealed`/`paper` = 0 hits;
`PnL` only as "0 PnL"; all `S1` hits are slippage-tier labels/trial IDs
(zero sealed-access mentions); `order` 1 hit = "NO_GO_REGISTER/SCORE/ORDER
stands"; `live` hits are product names + "live service BLOCKED_TRANSPORT".
Standing rulings restated unchanged: **ES 24 frozen** (census machine-counted),
**PB2 HOLD**, **PB3 PARK**, **6F NOT_RUN_DATA_ABSENT**.

## Findings by severity
- **CRITICAL: 0**
- **MAJOR: 0**
- **MINOR: 1** — F1 carried Q5 coverage over-claim (8/23 missing captures,
  independently re-confirmed; zero claimed cells depend on them).
- **NOTE: 6** — F2 FX-JA disclosure-key variant + annotated start sha
  (attestation recorded); F3 ES discarded root handoff; F4 FX-EB root-path
  ambiguity + "5 CDX" vs 3 on disk; F5 dispatch task-text window imprecision
  (45 vs 49); F6 manifest data-root paths (IBKR corpus dot-path; nonprice
  dual-root); F7 counted in findings JSON as NOTE (language scan clean —
  recorded as evidence, not a defect).

Lane files were never modified by this verifier; audit artifacts only, all
under `verify/**` plus `dispatch/handoff_VERIFY-A7READY.json`.
