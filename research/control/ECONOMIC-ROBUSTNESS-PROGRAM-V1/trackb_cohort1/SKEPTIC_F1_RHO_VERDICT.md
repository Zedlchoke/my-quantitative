# SKEPTIC_F1_RHO_VERDICT — ERP1-TRACKB-COHORT-1 F-1 one-shot ancestry rho (pre-PnL VETO)

- Lane: trackb-cohort1-skeptic. Representation law honored: rho computed BY this lane from the
  frozen bytes, not taken from any proposer artifact. ONE SHOT — no re-specification.
- Measured intake: worktree `orca/erp1-trackb-cohort-1-integration` @ `b680c5d42f048371192b77e543e7eb2f62c6cb7f`
  (== dispatch_sha); root HEAD `009b9a0811e11a8e93b7535ea123433adbb1167e`.
- Verdict in one line: **KILL_ANCESTRY_RHO** — pooled |rho| 0.5308 vs CARRY-BAB and 0.3337 vs
  BASISLV-PREMFADE-28D breach the immovable 0.20 bar, and the anchor's continuous decision
  variable is an EXACT monotone transform of the dead funding-level observable (rho = 1.0000).
  Cohort closes at GO-1 with 0 scored cells.

## 1. Machinery proof (before rho, M-class truncation discipline)

- Funding loader + estimator replayed against the M1-ANCHOR artifact `ec_bps` over all 232
  epochs: max |diff| = **1.14e-13 bps** under the convention settled-rate window **[t-90d, t]
  inclusive, settle_time <= T** (x105 settlements, 1e4 bps). All other conventions (settle < T,
  exclusive lower edge) fail by 4.5–7.3 bps. My reconstruction machinery is byte-exact against
  the frozen artifact — an independent confirmation of the M-1..M-5 replay claim.
- **Measured grid discrepancy (disclosed):** the artifact is 232 weekly epochs spanning
  **2020-07-24..2024-12-27**, Fridays, steps exactly 7d — NOT "2020-07-18..2026-08-21" as the
  dispatch prose states (232 weekly epochs cannot reach 2026-08-21; 318 are needed). All rho
  below is computed on the artifact bytes (the operative frozen representation). 181 fires /
  51 flat; occupancy 0.780; min ec|fire 45.07, max ec|flat 44.91 — C*=45 pinned exactly.

## 2. Dead-family reconstructions (exact formulas, same 232-epoch grid, PIT per §1)

| Family | Exact reconstruction used |
|---|---|
| CARRY-1D/3D/7D (V6) | state=1 iff trailing {1,3,7}-calendar-day mean of settled fundingRate (settle in [t-Nd, t]) > 0; continuous proxy = that mean (bps) |
| CARRY-BAB (V16 razor) | state=1 iff trailing-90d settled mean > full-window median (0.744 bps) of that same series; continuous proxy = trailing-90d mean. PIT-clean variant: expanding-median split (disclosed, same pass) |
| H-FUNDCROWD-MR-v2 | percentile of LAST settled rate within trailing-90d settled rates (mid-tie); state=1 (its SHORT-crowding extreme) iff pct >= 2/3; continuous proxy = pct |
| BASISLV-PREMFADE-28D | hourly synchronized (perp_close - spot_close)/spot_close on 40,902 common 1h bars (2020-05..2024-12, bars open_time < T only); per-epoch value = 28d trailing mean (1,056 bps-scale proxy); state=1 iff in top tercile (cut 1.21 bps) |

Fidelity note (pre-declared at council): V6/V14 registry windows are not byte-recoverable;
these are approximations BY CONSTRUCTION, each stated exactly. Faithfulness is judged in §3.

## 3. ONE-SHOT POOLED SPEARMAN, 232 epochs — bar |rho| <= 0.20, immovable

| Dead family | Reconstruction | pooled rho (binary state) | pooled rho (ec_bps vs continuous proxy) | Faithful? |
|---|---|---|---|---|
| CARRY-1D | 1d mean > 0 | +0.1744 | +0.4672 | approx |
| CARRY-3D | 3d mean > 0 | +0.0965 | +0.4836 | approx |
| CARRY-7D | 7d mean > 0 | +0.0795 | **+0.5101** | approx-faithful (V6) |
| CARRY-BAB | 90d mean > full-window median | **+0.5308** | **+1.0000** | faithful — see below |
| CARRY-BAB (PIT variant) | 90d mean > expanding median | **+0.3741** | **+1.0000** | faithful |
| H-FUNDCROWD-MR-v2 | top-tercile funding pct | -0.1901 | -0.1875 | approx |
| BASISLV-PREMFADE-28D | top-tercile 28d mean basis | **+0.3337** | **+0.7331** | faithful at level axis |

The continuous +1.0000 is an IDENTITY, not a reconstruction artifact: by FN-1 the anchor's
decision variable ec_bps IS (trailing-90d settled funding mean) x 105 — a strictly monotone
transform of the exact observable the dead carry family consumed. No reconstruction doubt can
attach to it. The binary CARRY-BAB breach survives the PIT variant (0.3741 > 0.20), i.e. the
kill is robust to the one disclosed approximation choice that could have mattered.

## 4. F-1 one-shot verdict: **KILL_ANCESTRY_RHO**

- Bar breached by two dead families judged faithful: CARRY-BAB 0.5308 (binary; both laws are
  threshold rules on the same funding-level observable — the F-0 information-test collision
  verbatim) and BASISLV-PREMFADE-28D 0.3337 (binary level state) with continuous 0.7331; the
  standing premium-fade class veto (-0.418/-0.515) applies regardless of rho.
- Honest adverse facts recorded (do not change the verdict): the pure V6 sign gates at 1/3/7d
  measure 0.17/0.10/0.08 binary — UNDER the bar (the 45 bps gate is far above a 0-sign gate);
  FUNDCROWD-MR-v2 percentile state 0.1901 — under by 0.0099. The anchor is NOT a
  funding-percentile re-gate and NOT a short-window sign gate; it IS the funding LEVEL itself.
- This is exactly the §2 calibration outcome pre-registered at council ("expected > 0.20;
  V16 cleared by 0.0073; V17 0.2439"): the entry law is monotone in funding level, and any
  decision state monotone in carry level inherits the carry-class precedent (FOREX-V4
  0.997–1.000). No-rescue: no re-gate, threshold, window or cadence change can re-run F-1.

## 5. Cohort-level pre-PnL verdict (adversarial integration; battery facts re-measured, not trusted)

1. The F-1 kill is terminal on its own: falsifier_order places F-1 before any PnL-bearing
   computation; a kill law firing ends the cohort at GO-1. Answer to "already dead regardless
   of rho": rho alone suffices; the rest corroborates.
2. **Battery correction #1 (recent fires):** "0 fires in last 6 months" is true only for
   2026-02-13..2026-08-07. On my extended weekly grid through the funding end (2026-08-21)
   there are **2 fires in the final 2 weeks** (2026-08-14 ec 47.9, 2026-08-21 ec 49.4), and 4
   more in 2026-01-15..2026-02-05. Recent-window unfundability is real for ~6 months (ec dips
   to 31 bps) but the "everywhere recent" claim is false at the window edge.
3. **Battery correction #2 (G5 grid dependency):** "34 non-overlapping 35d holds < 40" holds
   ONLY on the 232-epoch artifact grid (ends 2024-12-27) — my greedy count on that grid is
   exactly 34. On the freeze's declared dev window (..2026-08-21) the same gate law yields
   **41 closed non-overlapping 35d holds >= 40**. The NOT_RUN_THIN structural claim is
   therefore grid-dependent and NOT certified by this lane; the artifact-vs-freeze-window
   inconsistency is itself a defect the owner should record. This is NOT a rescue (no-rescue
   law): the frozen representation is what F-1 ran on and killed on, and at 41/40 the margin
   is 1 hold with ec margins of 2–5 bps over the 45 bps gate.
4. F-3 stands as disclosed: occupancy band exceeded and >=90%-differ structurally unreachable
   (Jaccard 0.384 vs chance 0.36) — the CAUSAL control cannot certify non-vacuity even
   absent the rho kill. Threshold sensitivity 181/170/148 at C*=45/50/60 shows the state is a
   funding-level dial, consistent with §4's identity result.

## 6. Recommendation: close the cohort at GO-1 with 0 scored cells (tracka-2 precedent)

- Terminal label: **KILL_ANCESTRY_RHO** (kill_laws: KILL_ANCESTRY_RHO_GT_0.20). Secondary
  recorded defects: F-3 predicate failure; artifact grid != freeze dev_window.
- NO arm merits a scored cell — including DIAG_DTX: BC-1/BC-2 leave it no PASS vocabulary, it
  never consumes F-1, and with the class dead there is nothing left to diagnose; scoring it
  would spend budget on a corpse (vocabulary: NOT_RUN / DIAGNOSTIC_OBSERVATION_ONLY).
- 0/7 scored cells used; trial_ledger records kills, not scores. This is a first-class outcome.

## 7. What a FUTURE cohort on this surface would need (new information only)

1. A decision observable NOT monotone in funding/basis level on a PIT-clean multi-year axis —
   on this surface the candidates are known-blocked (OI term structure: PIT overwritten ~41.6h;
   liquidation tape: zero coverage). No such axis exists today; nothing to propose.
2. A DATED, measured cost-regime break (venue fee-schedule change with sha-pinned schedule and
   measurable spread census) that moves the x2.0 ceiling — new information by the dated-boundary
   law; a re-tuned C* or wider hold is not.
3. An observably different funding regime is NOT new information (same observable, different
   window = rescue by rename). The funding LEVEL axis is dead here; the 2024+ compression (ec
   ~31–50 bps vs a 45+ bps x2.0 gate) is the measured reason no re-window can revive it.
4. If any future proposal arrives, F-1 reruns from zero on ITS representation with the same
   immovable bar; the 1.0000 identity result is the prior to beat.

— ECONOMIC SKEPTIC lane, 2026-09-26. No PnL computed anywhere; none exists in this cycle.
