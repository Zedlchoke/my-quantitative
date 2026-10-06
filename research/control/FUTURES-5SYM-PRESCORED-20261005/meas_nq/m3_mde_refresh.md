# M3 — NQ MDE refresh arithmetic for NQ-F2/NQ-F3 (G11 feed) — MEAS-NQ, wave 3

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **MEAS-NQ**, 2026-10-05. PREP-only,
  **descriptive arithmetic only** — no gate, no scored cell, no PnL, no conditional-on-signal statistic.
- Generator: `m3_mde_refresh_arith.py`. Output: `m3_mde_refresh.json`.
- Inputs: `m1_session_sigma_v3.json` (this lane's G11 re-derivation) + committed
  `nq_held_daily_v3.parquet` (canonical-CANDIDATE read posture, `SPEC_NQ.md` §2; D9 UNSIGNED).
- Full per-family MDE tables remain **post-freeze arithmetic (NOT_RUN)** per `SPEC_NQ.md` §7 —
  this file is the descriptive refresh feed for them, nothing more.

## 1. The census MDE formula (quoted, never re-invented)

`FUTURES-TEN-HYPO-PREP-20261004/es_nq/HYPOTHESES_ESNQ_R3.md` §7 (F5-K2):

> "court-method MDE (two-sided α=0.05, power 80%, z=2.80; dispersion proxy = committed
> session σ, an upper bound)"

i.e. **MDE = 2.80 × σ / √n** (the same per-event form stated in
`FUTURES-TEN-HYPO-PREP-20261004/cross/FALSIFICATION_MATRIX.md`, "per-event MDE ≈ 2σ/√n";
the committed ESNQ lane test record pins the arithmetic: "MDE=2.80×sigma/sqrt(66) with
committed sigmas ES 68.41bp … and NQ 112.30bp (NQ_a1_regimes yearly[].vol_ann_pct median
17.83%/sqrt(252))").

## 2. What the G11 defect correction does to the σ input (from M1)

| σ input | pre-recovery | v3 (M1) | delta | classification |
|---|---|---|---|---|
| **census proxy σ** (median-year law) | 112.2984 bp | 112.2984 bp | 0.0 | MEASUREMENT_IDENTICAL (median-invariant) |
| year-2020 stratum | 33.5434% ann (depleted year) | 34.8153% ann | +1.2719 pct-pts | DEFECT_CORRECTED |
| pooled σ F3 fold 2018–2021 (includes 2020) | not committed pre-recovery | **151.38 bp** | — | v3 measurement |
| pooled σ 2023–2026 (NQ-F2 era) | not committed | **126.33 bp** | — | v3 measurement |
| RTH 5-min dailyized sd, full era | — | **71.12 bp** median | — | v3 measurement (M1) |

The F3-fold stratum is where the defect correction actually bites (2020 sits inside it);
the census's median-year proxy is untouched.

## 3. NQ-F2 `MACRO-0730-NQ` refresh

n is taken **as declared by the census** (`CENSUS_5SYM.md` NQ-F2: scoring era confined
2023–26, "~160 event days", thin-power K7 pre-registered) — not re-derived here.

| σ law | σ (bp) | n | MDE = 2.80σ/√n |
|---|---|---|---|
| era-matched pooled daily σ 2023–26 (v3) | 126.33 | 160 | **27.96 bp** |
| census proxy σ (median-year, unchanged by G11) | 112.30 | 160 | 24.86 bp |
| RTH 5-min dailyized sd (M1 v3 measure) | 71.12 | 160 | 15.74 bp |

Reference scale (cited, `SPEC_NQ.md` §7): NQ RT(S2) modeled ≈ 2.849 pts = **15.8 bp
conservative / 1.1 bp modern** (MODELED / UNDER REVIEW). The era-matched MDE (27.96 bp)
sits above the conservative cost reference — i.e. at n≈160 a session-σ-scaled effect is
**power-marginal-to-poor**, consistent with the census's own thin-power pre-registration
(K7); the era-matched σ row is the honest feed for any post-freeze F2 table. The spread
across the three σ laws (15.7–28.0 bp) is itself the G11 deliverable: the dispersion
input choice moves the MDE by ~1.8×.

## 4. NQ-F3 `RUN-REV-NQ` refresh

Armed-cell census (runs ≥5 occurrence rate) is **NOT_RUN** (`CENSUS_5SYM.md` NQ-F3
field 3) ⇒ the MDE is parameterized in n; the full held-session count (4,219) is the
**optimistic upper bound on n ⇒ a lower bound on MDE**:

| σ law | σ (bp) | n | MDE |
|---|---|---|---|
| census proxy σ (full era, median-year) | 112.30 | 4,219 | **4.84 bp** (lower bound) |
| F3-fold pooled σ 2018–2021 (defect-corrected 2020 inside) | 151.38 | 4,219 | 6.52 bp |
| per-n table at σ=112.30 | — | 200 / 400 / 800 / 1,600 | 22.23 / 15.72 / 11.12 / 7.86 bp |

Reading: even at the most optimistic n the session-σ-scaled MDE (4.84 bp) is comparable
to the modern RT(S2) bp print (1.1 bp, cited above) at ~4×; at realistic armed-cell n
(NOT_RUN) it scales as 1/√n from the table. This is descriptive arithmetic feeding the
post-freeze table — **the armed-n census itself stays NOT_RUN** and is the binding
limitation.

## 5. Reference row — the census's own committed NQ MDE print (n=66)

| | old (pre-recovery σ) | new (M1 σ) | delta |
|---|---|---|---|
| MDE at n=66 (EXPWITCH-NQ leg class) | 38.70 bp | 38.70 bp | **0.0** |

The census's committed "MDE ≈ 38.7 bp" (`HYPOTHESES_ESNQ_R3.md` §7; census 10SYM row
"MDE 23.6bp ES / 38.7bp NQ") **survives the v3 repair exactly unchanged** — the G11
defect corrected the 2020 tail, not the median-year σ the print consumed.

## 6. Limitations

- The census MDE formula treats session σ as an upper-bound proxy for effect scale; per-family
  event-strata σ laws are a post-freeze parameterization choice (owner territory) — not invented here.
- Cost references are MODELED / UNDER REVIEW (`SPEC_NQ.md` §5); no cost number herein is measured.
- n inputs are census declarations (F2 ~160) or bounds (F3 4,219); the F2 exact vintage-correct
  event-day count and the F3 armed-cell census are NOT_RUN by law.
- cache_v3 consumed as canonical-CANDIDATE (D9 UNSIGNED), per-cycle cited.

— End M3. Descriptive arithmetic only; nothing herein gates, scores, or ratifies anything.
