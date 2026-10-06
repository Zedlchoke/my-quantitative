# MEAS_NQ_REPORT — LANE-MEAS-NQ, FUTURES-5SYM-PRESCORED-20261005 wave 3 (PREP-only)

- Lane: **MEAS-NQ**, worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`,
  branch `prep/futures-5sym-prescored-20261005`, HEAD at lane start `b2d086ca50996c628ec0373c4a3e8c2f2387c742`.
- Class: PREP continuation, **descriptive only** — 0 PnL, 0 scored cells, 0 conditional-on-signal returns,
  0 registrations, 0 commits. ADOPT-D9 UNSIGNED ⇒ cache_v3 consumed only in the permitted descriptive read
  posture (canonical-CANDIDATE, per-cycle cited per `SPEC_NQ.md` §2); **FREEZE consumption: NOT_RUN**;
  **real-data F3 rebuild: NOT_RUN (refusal demonstrated)**.
- Locks: `researchctl.py locks inspect` = FREE_PROVEN before and after every panel scan; the annotated-1m
  single-shot read ran ≤ 17 s wall (< 2 min ⇒ canonical heavy lock not required); no heavy lock taken; no
  foreign worker touched.
- Input integrity: 4/4 cache_v3 files re-hashed by this lane match `adopt/cache_v3_hashes.json` pins.

## Item table

| # | work-queue item | status | artifact(s) | headline | limitations |
|---|---|---|---|---|---|
| 1 | **A#11 — NQ session-σ dispersion proxy re-derivation on cache_v3 (G11)** | **DONE (descriptive)** | `m1_session_sigma_v3.md` + `.json`, `m1_per_session_rederived.parquet`, `m1_rederive_dispersion.py` | 285/285 committed k6gate dispersion comparisons reproduce **bit-identical**; per-session parquet 4,219 rows max delta 0.0. **G11 defect identified and quantified**: census σ proxy 112.3 bp came from the pre-recovery `NQ_a1_regimes.json` (hole-depleted year-2020: 51 depleted sessions; v2 dead-handoff roll). Re-derived on v3: **median-year σ defect-invariant (112.2984 bp, delta 0.0)**; year-2020 corrected 33.5434% → **34.8153%** ann (+1.2719 pct-pts, DEFECT_CORRECTED). NEW: per-session-class decomposition (RTH 2.75 bp / Globex 1.26 bp / maintenance-break 1.16 bp per-session mean medians; break bars in 532/4,219 sessions) | descriptive proxy only; per-class σ parameterization is owner territory; DST quirk inherited as measured |
| 2 | **A#3/#4 (harness half) — NQ-F3 full-era rebuild harness + synthetic checks** | **DONE (harness + synthetic); real run NOT_RUN** | `m2_f3_rebuild_harness/` (`rebuild_harness.py`, `expected_check.py`, `HARNESS_SPEC.md`, `runs/`) | Pipeline per the committed k6gate method (NaN-aware chain → per-session rets → a1/a2 aggregates → roll set → ret cross-check), input-manifest hashing, SPEC §6 fold boundaries (F1–F4, warmup 252 reported not applied), DST preserved-quirk enforced as observable. **Synthetic self-check: 39/39 checks PASS (exit 0)** on a deterministic fixture with 2 eras, 3 embedded rolls, hole/thin anomalies, closed-form crash+recovery; outputs byte-identical across re-runs on a fixed fixture. **Refusal demo: `--real` on real cache_v3 exits 20 `REFUSED_D9_UNSIGNED` twice recorded** (no artifact; wrong-schema artifact) with FINAL status artifacts | real-data rebuild **NOT_RUN pending ADOPT-D9** (harness hard-refuses; fail-closed, not defaulted); rvol/VR/tercile aggregates implement-and-assert only (documented) |
| 3 | **G11 feed — NQ MDE refresh arithmetic (NQ-F2/F3)** | **DONE (descriptive arithmetic)** | `m3_mde_refresh.md` + `.json`, `m3_mde_refresh_arith.py` | Census formula quoted (MDE = 2.80σ/√n, z=2.80 court-method). **NQ-F2** (n≈160 census-declared, era σ 2023–26 = 126.33 bp): MDE **27.96 bp** (range 15.74–27.96 across σ laws). **NQ-F3** (armed-n NOT_RUN; optimistic bound n=4,219): MDE **4.84 bp lower bound** (6.52 bp with defect-corrected F3-fold σ 151.38 bp). **Census's own print (n=66): 38.7 → 38.7 bp, delta 0.0 — the committed MDE survives the v3 repair unchanged** | post-freeze per-family MDE tables NOT_RUN per SPEC §7; F2 exact vintage event count + F3 armed-cell census NOT_RUN by law; costs MODELED/UNDER REVIEW |

## NOT_RUN register (this lane)

| item | grounds |
|---|---|
| NQ-F3 real-data rebuild on cache_v3 | ADOPT-D9 UNSIGNED — harness hard-refuses (exit 20, `REAL_RUN_REFUSED.json` ×2); unlock = owner-signed `d9_ratification@1` artifact |
| FREEZE consumption of cache_v3 | same D9 grounds; this lane's reads are descriptive only, per the k6gate NQ lane's read posture |
| Post-freeze per-family MDE tables | SPEC_NQ §7 law (post-freeze arithmetic); this wave delivers the descriptive refresh feed only |
| NQ-F3 armed-cell census (runs ≥5) | inherited NOT_RUN (`CENSUS_5SYM.md` NQ-F3 field 3) — binding limitation on the F3 MDE |
| Canonical heavy lock | not required — no scan exceeded 2 min (max 17 s wall); locks FREE_PROVEN throughout |

## Incidents

| id | severity | summary | disposition |
|---|---|---|---|
| MEASNQ-T1 | LOW | first M1 run produced 4 tiny diff cells (≤ 7.2e-4 bp): the implementation restricted to the held chain BEFORE computing r1, while the committed recipe computes r1 on the full panel first (first held bar of a contract carries the contract-internal diff) | recipe order corrected to verbatim; all 285 comparisons went bit-identical; intermediate disclosed in `m1_session_sigma_v3.md` §6, no artifact of it consumed |
| MEASNQ-T2 | LOW | first M3 run mislabeled pooled era σ as bp (returned annualized %) → F2 MDE printed 4.44 bp | unit law fixed (daily σ = std × 1e4); corrected values 27.96/4.84 bp; committed JSON regenerated |
| MEASNQ-T3 | INFO | dispatch manifest `base_sha` field reads `0732f22e…` while this lane's dispatch packet and HEAD read `b2d086ca…` | recorded; lane anchored to its packet's base (`b2d086ca…`, == measured HEAD); no writes outside meas_nq/ + handoff |

— End MEAS_NQ_REPORT.
