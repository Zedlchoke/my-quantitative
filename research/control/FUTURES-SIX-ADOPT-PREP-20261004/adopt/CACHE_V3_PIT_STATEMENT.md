# CACHE_V3_PIT_STATEMENT — NQ cache_v3 as canonical-candidate

Round: FUTURES-SIX-ADOPT-PREP-20261004 · Lane ADOPT · 2026-10-04
Worktree `.worktrees/futures-six-adopt/prep` @ `9fb66c88d464fd90748bc04d78280c2d87939cd3` (measured, one `rev-parse`).

Subject: `research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3/**` (all file sha256 in
`adopt/cache_v3_hashes.json`, re-measured by this lane). Status word: **canonical-CANDIDATE** —
consumption as canonical requires owner ratification (decision item **D9**, Option A). Nothing here
ratifies anything.

---

## 1. The decisions the rebuild used, and their information timing

### 1.1 Alias view rule (the only NEW decision vs baseline)

* **Rule**: `instrument_id == 16908 AND ts_event < 2020-06-01 UTC → raw_symbol = 'NQM0'`; all other
  dash rows remain excluded as calendar spreads. Implemented `nq_deep_lib_v3.py::load_outright_1m_v3()`
  (`ALIAS_CUTOVER = 2020-06-01 UTC`), applied BEFORE the dash-excluding filter.
* **Provenance + timing**: the boundary (2020-06-01) and the relabel target (`NQM0`) come from the
  `nq2020_hole_probe.json` adjudication `A_ALIAS_NOT_ABSENCE`
  (`FUTURES-DEEPRESEARCH-V2-20261003/analysis/integration/`, `generated_utc
  2026-10-03T01:40:59.909111+00:00`) — **fixed ~1 day BEFORE the v3 rebuild ran** (rebuild round
  FUTURES-SIX-READINESS-20261004, 2026-10-04), in a different round, and **NOT tuned on any chain,
  roll, or outcome metric**. The adjudication's inputs were: vendor METADATA endpoints only
  (record_count / billable_size / get_cost; zero data downloaded; parent `NQ.FUT` window count
  169,992 == local delivered count 169,992; raw `NQM0` 100,034 == local id-16908 100,034) plus the
  local delivery's own label windows (id 16908 carried `NQU8-NQM9` from its 2018-08-15 listing until
  2020-06-01, then `NQM0`).
* **Why id-keyed, not symbol-keyed**: raw NQ symbols are year-epoch-ambiguous; the panel contains
  9,442 pre-cutover rows already labeled `NQM0` from OTHER instrument ids (earlier delivery years,
  e.g. June-2010). `alias_lineage.json` proves the dash alias `NQU8-NQM9` maps to
  **instrument_ids = [16908] only** (the other 169 distinct dash-row instrument ids are spread ids),
  so the rule provably touches only id 16908.
* **Corroboration seam (declared)**: the adjudication cross-checks against the vendor's CURRENT
  symbology ("attributes all 100,034 window records to raw NQM0"). That is a present-day identity
  lookup used to justify a historical relabel — standard identity/calendar resolution, not an
  outcome-tuned choice; the load-bearing evidence is the exact record-count reconciliation, which is
  point-in-time vendor metadata.

### 1.2 k=5 rule — UNCHANGED from baseline

`front_by_volume_crossover` (trailing-5-session mean volume, crossover to the max-mean candidate) is
a faithful copy of baseline `NQ_deep_lib.py`; parameter k=5 unchanged; sessionization, registry and
cluster-resolution code paths unchanged (`nq_deep_lib_v3.py` header; DATA_READINESS_NQ.md §0).
No parameter of the plain chain was re-fit on v3 outcomes.

### 1.3 Cease-guard variant — cessation from contract last-bars dates (past data only)

* `front_by_volume_crossover_cg()` adds a HARD cease: at session d, if the held contract has **no
  bars today**, or d is **past its bars-present cessation**, switch immediately to the next quarterly
  (first candidate with data today, else first with any data), regardless of trailing volume.
* `cessation(contract) = last session_date with any bars for that contract in the session table` —
  DECLARED DERIVATION, not exchange metadata (`nq/cease_guard_audit.json`); cross-checked against
  registry last_bar: **0 mismatches**.
* On NQ the guard fired **0 times** (`cg_guards_fired: 0`, `rebuild_stats.json`) and the cg chain is
  logically IDENTICAL to the plain chain (this lane: `assert_frame_equal` PASS both ways; identical
  lane-method digest `d359b4d4…07e3d`; the two parquets are even byte-identical,
  sha256 `99ff1ca1…`).

---

## 2. Classification

**PIT_CLEAN_BY_CONSTRUCTION** for the canonical-candidate set:
`nq_outright_1m_v3.parquet`, `held_volume_k5_v3.parquet`, `nq_held_daily_v3.parquet`,
`nq_sessions_v3.parquet`, `v3_hold_segments_k5.parquet`, `v3_rolls_spread_stats.parquet`,
`contract_registry_v3.json`.

Basis: (a) every bar in the panel is vendor-delivered raw data — the only transformation is the
declared identity relabel, whose boundary and target were adjudicated from vendor/local metadata
BEFORE the rebuild and involve no outcome information; (b) the held chain is built by the UNCHANGED
baseline k=5 rule evaluated strictly from trailing session volumes (each day's decision uses that
day's close-of-session volume state and earlier only); (c) rolls, segments and held-daily are pure
projections of (a)+(b). The round-1 reproduction (two independent full rebuilds, identical digests)
plus this lane's re-measurement (§3) establish determinism.

**PIT_CLEAN_PER_DECISION (declared construction seam)** for `held_volume_k5_cg_v3.parquet`:
the guard's firing condition at session d uses only information available at d — "no bars today"
(present) or "cessation < d" (past). The cessation MAP is derived from the full session table
(the last-bars date of a contract is only final after it stops trading), which the lane itself
discloses as a non-PIT-lookback-if-used-in-sample, diagnostic-variant-only construct
(`nq_deep_lib_v3.py` docstring). The seam is cosmetic for firing semantics: "d > cessation" is
implied by "no bars today" for any held contract, so an online implementation keying on
absence-of-bars-today alone produces the identical chain. Cease-guard variants across symbols are
labeled diagnostic until D9 rules on the standard (`CEASE_GUARD_STANDARD.md`).

## 3. Re-measured facts backing this statement (all by THIS lane, from committed bytes)

* Panel `nq_outright_1m_v3.parquet`: **6,780,608 rows**, ts 2010-06-06 22:00Z → 2026-09-30 23:59Z.
* id-16908 pre-2020-06-01 rows: **92,075** (volume **24,686,121**), **all `raw_symbol == 'NQM0'`**,
  window 2018-08-15 14:37Z → 2020-05-31 23:59Z; post-cutover id-16908 rows 19,406, all `NQM0`
  (matches hole-probe expectation 19,406 / 2020-06-01..06-19).
* Held chain: **66 rolls**, incl. exactly one `NQH0_2020 → NQM0_2020` at **2020-03-19** (dte +1;
  roll-day volume old 85,489 vs new 487,005); chain 4,219 sessions; cg chain identical (see §1.3).
* Lane-method digests recomputed: `d359b4d4…07e3d` (both chains), `64203dd2…7da66` (sessions,
  11,715 rows), panel rows/ts exact — **0 deltas vs round-1 `reproduction.json` / `run1_digests.json`**
  (full diff table in `adopt/cache_v3_hashes.json`).
* Known disclosed residue (no chain impact): 2 listing-period odd prints recovered into the panel
  (2018-08-15, 2018-09-13; id 16908; close 81.05 / 94.75 pts; volume 1 each) — held contracts those
  sessions were `NQU8_2018`, never `NQM0_2020` (`nq/v3_qc.json`); 154 low-coverage sessions are real
  market structure (holidays/half days), not absence.

## 4. Honest seams register

1. Vendor current-symbology corroboration is a present-day lookup backing a historical identity
   decision (§1.1) — declared, count-reconciled, no outcome data involved.
2. cg-variant cessation map is a full-sample construction; per-decision firing is time-t information
   only (§2).
3. The 45-day-gap cluster rule splits `NQM0_2020` into 3 registry clusters resolved to one contract
   key — baseline resolution logic, unchanged; disclosed in DATA_READINESS_NQ.md §1.
4. The rebuild is retrospective repair of a historical cache: PIT here concerns the information
   timing of the DECISIONS (§1), not the byte-write date of the artifacts.
5. Domain: av1trim corpus (2010-06-06..2026-09-30). Re-ingestion of new vendor chunks requires a new
   rebuild + re-hash under the same declared rules.

— Verdict: PIT_CLEAN_BY_CONSTRUCTION (canonical set) / PIT_CLEAN_PER_DECISION (cg variant), with
seams 1–5 declared. This statement is adoption input for D9; it is not a ruling.
