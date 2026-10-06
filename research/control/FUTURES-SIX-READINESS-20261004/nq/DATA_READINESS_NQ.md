# DATA_READINESS_NQ.md — lane NQ-ALIAS-REPAIR

Round: FUTURES-SIX-READINESS-20261004 · Worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep`
· branch `codex/futures-six-readiness-20261004` · HEAD measured at lane start
`d7fc62312947b2613523dd401d44c9ec1a8d166b` (== dispatch_sha; no other git
commands run; controller commits).

**Scope**: repair the NQ 1-minute panel alias hole (ERRATUM F1 obligation) by
applying the PIT alias view rule, rebuilding the full-era chain, re-measuring
2020 aggregates before/after, with independent reproduction. DATA PREP ONLY:
no PnL, no strategy metrics, no scored cells, no S1, no hypotheses created, no
network access. Heavy lock: `FREE_PROVEN` at lane start (`researchctl.py locks
inspect`); lane did NOT take the lock (all jobs single-shot, <10 min each).

**Before state** (read-only, tracked at base):
`research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/` —
nq_outright_1m.parquet 6,688,533 rows; held_volume_k5.parquet 4,219 sessions /
66 rolls / 2010-06-07→2026-10-01; nq_sessions.parquet 11,549 (contract,
session) rows; nq_held_daily.parquet; contract_registry.json 111 clusters.
Untouched by this lane.

---

## 0. The fix (applied)

View rule, from `nq2020_hole_probe.json` adjudication `A_ALIAS_NOT_ABSENCE`
(ERRATUM F1): **`instrument_id == 16908 AND dt < 2020-06-01 UTC → raw_symbol =
'NQM0'` (relabel, include); all OTHER dash rows are true calendar-spread rows
and stay excluded.** Implemented in `nq_deep_lib_v3.py::load_outright_1m_v3()`
(faithful copy of baseline `NQ_deep_lib.py`; only path change + this loader +
an explicit cease-guard chain variant added). Baseline caches never written.

---

## 1. Identity / tick — **PASS**

- Alias lineage **re-derived from the RAW parquets** (not the cache),
  13 files, 7,330,320 parent rows — `nq/alias_lineage.json`:
  - dash rows total 641,787 (641,787 = 549,712 post-relabel drops + 92,075
    relabels); plain rows 6,688,533;
  - `NQU8-NQM9` rows = **92,075** (expectation met, re-derived not trusted),
    window 2018-08-15 14:37Z → 2020-05-31, volume **24,686,121**;
  - `NQU8-NQM9` instrument_ids = **[16908] only** → the relabel provably
    touches ONLY id 16908 (the other 169 distinct dash-row instrument ids
    are spread ids);
  - id 16908: 92,075 rows pre-cutover, **all** under the dash alias
    (`id16908_pre_non_dash_rows = 0`); 19,406 rows post-cutover, all under
    `NQM0` (expectation met), volume 5,159,596.
- Contract identity unchanged elsewhere: v3 registry 113 clusters = baseline
  111 + 2 (NQM0_2020 splits into 3 clusters under the 45-day-gap rule after
  relabel; all resolve to expiry 2020-06-19 → one contract key `NQM0_2020`).
  Cluster resolution code path identical to baseline.
- Price sanity on the v3 panel (`nq/v3_qc.json`): negative prices 0,
  high<low 0, close outside [low,high] 0, zero-volume bars 0 — same all-zero
  profile as baseline `NQ_a7_quality.json price_sanity`.
- Tick/cost identity (pointer only, unchanged): NQ tick 0.25 pt / $2.50
  (6.5-tick close proxy ⇒ $16.25 spread half-turn), per
  `FUTURES-OVERNIGHT-PREP-20261003/hypo/es_nq/esnq_hypotheses.json` cost_law.

## 2. O1M coverage + holes — **PASS (recovered; disclosures below)**

- v3 panel **6,780,608 bars** = 6,688,533 + **92,075 recovered** exactly
  (`nq/before_after_2020.json`); span 2010-06-06 22:00Z → 2026-09-30 23:59Z.
- Recovered window (2018-08-15→2020-06-30): bars +92,075, volume
  **+24,686,121** (both exactly as expected). Calendar 2020 subset: bars
  +91,251, volume +24,684,036.
- Held chain (k=5) 4,219 sessions: **NaN-close sessions 49 → 0** in both the
  alias window and calendar 2020 (before: 2020-03-23..2020-05-29 all-NaN;
  after: real front closes). Depleted sessions in window 53 → 3.
- 2020-03-16..03-20 now show real front coverage 0.96–1.00 with the true
  front trading 487,005 / 554,299 contracts on 03-19/03-20 (`nq/v3_qc.json`).
- **REMAINING holes: none in the absence sense.** 0 NaN closes on the v3
  chain. 154 sessions carry RTH coverage < 0.6 — these are real market
  structure (US holidays incl. Juneteenth from 2022, Dec-24 half days, era-A
  Friday early closes, DST-fall-back Sundays, partial last session
  2026-10-01), not data absence; full list in `nq/v3_qc.json`.
- **Disclosure — 2 recovered odd prints**: 2018-08-15 and 2018-09-13,
  id 16908, volume 1 each, close 81.05 / 94.75 pts (listing-period prints
  invisible to the baseline). Zero chain impact: held contracts on those
  sessions were NQU8_2018 (verified), never NQM0_2020; 1-contract trailing
  volume cannot trigger the crossover.

## 3. Roll / expiry — **PASS**

- Total chain rolls v3 k=5: **66 = baseline 66**; roll-by-roll reconciliation
  (`nq/before_after_2020.json`): 66 matched pairs, **exactly one date
  changed** — NQH0_2020→NQM0_2020 moved from the dead handoff 2020-06-01
  (dte −73; fired only because NQM0 started printing post-alias) to a real
  PIT volume crossover **2020-03-19** (dte +1; roll-day volume old 85,489 vs
  new 487,005). All other 65 rolls byte-identical dates.
- Rolls inside 2018-08..2020-06: before 3 (2019-12-18, 2020-06-01 artifact,
  2020-06-18); after 3 under plain k=5 AND under the cease-guard variant
  (2019-12-18, **2020-03-19**, 2020-06-18). Cease-guard chain ≡ plain chain
  (same 66 rolls; 0 guard firings).
- **dte>45 quarantine no longer needed**: baseline a3 quarantined hole-window
  rolls via `0<=dte<=45` (62 of 66 passed); on v3, **66 of 66** rolls have
  0 ≤ dte ≤ 45 (distribution dte=1 n=14, dte=2 n=32, dte=3 n=20; full audit
  in `before_after_2020.json::dte_quarantine_check_v3`).
- Cease-guard full-chain proof: see §4 output `nq/cease_guard_audit.json` —
  **0 violations plain k=5, 0 violations cease-guard**, vs **1 violation on
  the BEFORE chain** (NQH0_2020 dead-held 2020-03-23..2020-05-29 after its
  03-20 expiry — the exact 6J failure mode). 6J-law cross-reference:
  `6J_DEEP_v2.md` §8 ERRATUM M-5 (6J 2022-09-20: held ceased U2 while Z2
  traded 125,303 lots; baseline weak guard `NQ_deep_lib.py:266-267`).
  Cessation derivation DECLARED: last bars-present session per contract from
  each rebuild's own session table; cross-checked against registry
  `last_bar` — **0 mismatches on all 73 v3 real contracts**.
- Expiry calendar: **68/68** NQ quarterly expirations (36 product + 32
  family, zero divergence) — pointer `esnq_hypotheses.json::standing evidence
  nq_expirations` → `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es/
  nq_cal_coverage.json` (tracked at base; not re-verified here, no changes).

## 4. Session / holiday — **PASS (construction) / NOT_OBTAINED (2026 holiday times)**

- Sessionization is the BASELINE code path (Globex day boundary 17:00 CT;
  era-A close 16:15 CT → era-B 16:00 CT at `SESSION_SWITCH_DATE =
  2015-09-21`, the baseline's measured constant). v3 (contract, session)
  table = baseline 11,549 rows + 166 recovered NQM0_2020 rows, **0 rows lost**
  — measured strict superset.
- **Disclosure — baseline fall-back-DST quirk reproduced, not fixed**: the
  baseline lib comment claims DST-corrected `Day`-offset arithmetic, but the
  measured baseline cache proves ABSOLUTE 24h semantics: on fall-back
  Sundays, post-17:00 Globex-open bars keep the SUNDAY session_date (35
  (contract, session) rows across 2010–2024, e.g. `NQH0_2020 2019-11-03`
  17 bars 17:00–21:51 CT). Current pandas crashes on the baseline's exact
  expression; the v3 lib reproduces the measured behavior with a vectorized
  equivalent (proven by the 0-lost-rows superset diff). Flagged for owner;
  changing it was OUTSIDE this lane's alias-repair mandate (it would move
  rolls and break before/after reconciliation).
- NQ 2026 Globex holiday session-time deviations: **NOT_OBTAINED** (no
  network this lane; standing per P3-round matrix and
  `esnq_hypotheses.json::cross_cutting_not_run` — "ES/NQ 2026 Globex holiday
  session times NOT_OBTAINED ⇒ 2026 dubious days excluded"). Pointer:
  `FUTURES-P3-QUARANTINE-20261004/` (sibling worktree, read-only) and
  `esnq_hypotheses.json`.

## 5. Event PIT — **PASS — CLOSED-PREP** (pointer; no changes)

- FOMC statement archive with primary-source release-time proof +
  era anatomy: `FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_a4_events.json`
  (lull 0.68×, burst 2.3–2.8×, 84 clean 14:00-ET events). BLS PIT vintage
  law in force (current-calendar inference FORBIDDEN — standing ruling,
  DISPATCH_MANIFEST). CPI/NFP calendars remain NOT_RUN (baseline A7
  NOT_RUN inventory) — unchanged by this lane. Status recorded CLOSED-PREP
  per dispatch dimension list.

## 6. Fee / spread / slippage / BBO — **UNCHANGED — pointers only**

- Fees: **2.24/side MODELED COST**; `VERIFIED_VS_ACCOUNT = NOT_RUN`;
  **UNDER REVIEW** until owner-authorized A7 (standing ruling; D2 open).
  Pointer: `FEES_CORRECTED.md @72c9bc5b` + `esnq_hypotheses.json::cost_law`.
- Spread/slippage: composition per assumption D1 (NQ S1 23.49 / S2 28.49 /
  S3 33.49 per side, modeled). **D3 $0.01 open** (owner dispatch standing
  item) — untouched here.
- BBO: **NOT_RUN** (synchronous quotes absent; fill = next-bar-open law;
  close proxies only) — pointer `esnq_hypotheses.json::
  cross_cutting_not_run`. No changes made.

## 7. Trial budget — **PASS (no new trials)**

- NQ census recounted from the baseline census artifact
  `FUTURES-OVERNIGHT-PREP-20261003/hypo/es_nq/esnq_hypotheses.json`:
  **4 NQ families / 6 mechanisms, all register_status CONTINGENT** —
  NQ-F1 FOMC-ERA (M-NQ-CONT, M-NQ-UNW), NQ-F2 MACRO-0730 (M-NQ-MS),
  NQ-F3 RUN-REV (M-NQ-RR), NQ-F4 ROLLWK (role_A_construction, role_B_family).
- No NQ-specific numeric cap exists in standing rulings (the frozen cap on
  record is ES-only: 24 identities vs 36-census, headroom 0). Reported as-is;
  this lane created **0 new hypotheses/trial families**.
- Note: NQ-F3's register precondition "full-era rebuild on alias-recovered
  series" is now **evidence-satisfied** by this lane's v3 rebuild — that is a
  data-prep fact, NOT a scored outcome and NOT a GO.

## 8. Reproduction / A7 — **PASS (reproduction) / A7 READY-NOT-RUN / NO_GO_SCORE stands**

- Independent reproduction **REPRODUCED** (`nq/reproduction.json`): full
  rebuild run a second time in a fresh process (`nq_rebuild_v3.py all`);
  logical equality verified by sorted fixed-dtype CSV sha256 of held-chain
  key columns (session_date, held) — both k=5 chains digest
  `d359b4d4…e07e3d`, sessions key digest `64203dd2…f7da66` — plus panel
  row-count/ts min-max, plus `assert_frame_equal(check_exact=True)` PASS on
  both held chains vs the run-1 stash. Parquet byte equality NOT required
  (method disclosed in the artifact). The three analysis JSONs are also
  byte-identical when re-run against run-2 caches.
- A7 fee packet: **READY — NOT RUN** (owner-authorized A7 pending; pointer
  `FUTURES-DEEPRESEARCH-V2-20261003/audit/a7_nq/A7_DEEP_NQ.md` as the prior
  audit instance). **NO_GO_SCORE stands** (standing ruling, unchanged).

---

## 2020 before/after headline (descriptive only)

| metric | BEFORE (baseline) | AFTER (v3) |
|---|---|---|
| panel bars (2018-08-15→2020-06-30) | 736,136 | 828,211 (+92,075) |
| panel volume (same window) | 216,630,304 | 241,316,425 (+24,686,121) |
| held sessions w/ NaN close (window / cal-2020) | 49 / 49 | **0 / 0** |
| held contract sequence (Jun-19→Jun-20) | NQM9→NQU9→NQZ9→NQH0 (dead from 03-23)→NQM0@06-01→NQU0@06-18 | same through NQH0, then **NQM0@2020-03-19** (real crossover)→NQU0@06-18 |
| rolls in window (k=5 / k=5+cease-guard) | 3 (incl. dte −73 artifact) | 3 / 3 (all 0≤dte≤45) |
| 2020 unadjusted-chain embed pts (hazard of NOT adjusting) | −24.0 (holes; 3 rolls) | **−44.25** (4 rolls; adds the 2020-03-19 gap −20.25) |
| chain rolls total | 66 | 66 (only NQH0→NQM0 date changed) |
| cease-guard violations | 1 (NQH0_2020 dead-held 49 sessions) | **0 / 0** |
| corr(roll-day gap, spread-med-10) | 0.99908 (n=65) | 0.99899 (n=66) |

Embed = sum of roll-day gaps per calendar year — a HAZARD metric of running
an unadjusted chain, not a return statistic. All years other than 2020 are
unchanged baseline values (verified identical in
`before_after_2020.json`).

## Verdict

NQ 1m data is repair-complete at the data layer: alias hole closed at $0 with
zero regression (session superset, 65/66 rolls unchanged, non-2020 embed
identical), full-chain cease-guard clean, independently reproduced.

**data-ready ≠ scored-authorized.** Dims still blocking scored use: (6) fee
verification (VERIFIED_VS_ACCOUNT=NOT_RUN, D2 open, A7 fee packet READY-NOT-RUN,
D3 $0.01 open), BBO/slippage NOT_RUN; (4) NQ 2026 holiday session times
NOT_OBTAINED; standing NO_GO_SCORE / NO_GO_REGISTER / NO_GO_ORDER.

### Artifacts (all under `research/control/FUTURES-SIX-READINESS-20261004/nq/`)

`alias_lineage.py` + `alias_lineage.json`, `nq_deep_lib_v3.py`,
`nq_rebuild_v3.py`, `cache_v3/` (nq_outright_1m_v3.parquet,
nq_annotated_1m_v3.parquet, nq_sessions_v3.parquet, contract_registry_v3.json,
held_volume_k5_v3.parquet, held_volume_k5_cg_v3.parquet,
nq_held_daily_v3.parquet, rebuild_stats.json, v3_rolls_spread_stats.parquet,
v3_hold_segments_k5.parquet, `_repro_run1/` stash),
`nq_analysis_v3.py` → `before_after_2020.json`, `cease_guard_audit.json`,
`phantom_drift_v3.json`, `nq_v3_qc.py` → `v3_qc.json`,
`nq_reproduce_digest.py` → `reproduction.json`, this file.
