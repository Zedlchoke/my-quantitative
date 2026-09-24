# A7 pre-launch audit — ILLIQ — round 5 (delta: A5/S0R)

- Cycle: CRYPTO-HISTORICAL-REPLICATION-3F-V1, family ILLIQ-AMIHUD-28D-W
- Lane HEAD: `ed3e466e0345773e1b2ce2157baaa069fd03690e` (moved c2bee0c8 → ed3e466e mid-audit; bookkeeping-only commit, zero delta on the three code files — re-verified)
- Root HEAD: `7d1db60a5e99823effc109b585e9a1797a1b68fc` (A5 plan commit)
- Verdict JSON (gate path): `a7_prelaunch_illiq/a7_prelaunch_illiq.json` — round 5 **REFUSED**
- Method: everything recomputed from bytes; nothing trusted from dispatch or prior rounds.

## Verdict: REFUSED — one new blocking finding (B2), r4's B1 is fixed

The r4 blocker (labels) is resolved in bytes and the A5 fold/window/authority/data-existence
checks pass — but the S0R funding wiring is broken: the covering funding scan A5 itself cites
is never read by any code path, the disclosed S0R DIAG is a no-funding number, and launching
as-is would book funding-free "net" returns on a scored surface.

## B2 (blocking): funding scan not wired for S0R — data exists, code doesn't read it

Measured, not inferred:

- `illiq_cell_runner.py:23` hardcodes `SCAN = funding_data_scan/scan_2026`.
  Measured coverage (BTCUSDT/funding.json): 4534 rows, **2020-07-01 .. 2024-08-20**.
  The S0R window (2024-08-22..2025-08-21, load-end +3d) contains **zero** funding rows in this scan.
- The covering scan exists: `funding_data_scan/scan_2026_a` — 20 symbol dirs,
  BTCUSDT 2196 rows, **2024-08-20 .. 2026-08-21** ⊇ S0R. This is exactly the dataset the A5
  amendment cites ("funding scan_2026_a covers 2024-08-20..2026-08-22") to fire the V13
  reopening law. **Nothing reads it.** A5 commit 0ac412ec added per-fold selection for BAR
  catalogs only (`--catalog`); funding got no equivalent.
- Empirical proof the zero is missing-data, not a genuine zero — `portfolio_metrics.funding_sum`:
  - S0R-ANCHOR-A5 DIAG: **0.0** (no coverage in wired scan)
  - Y2024P-ANCHOR-A4 DIAG: **+0.020439531331**
  - Y2021-ANCHOR-v2 DIAG: **+0.028862963716**
- Consequences: (1) the disclosed outcome exposure net = −0.589 is a **no-funding** number —
  materially incomplete as the V12-brief figure; (2) if launched as wired, both S0R scored
  cells book funding-free "net" returns, cross-fold non-comparable with Y2024P. Same failure
  class as r3 F2 (covering bars existed but were not loaded), now on the funding leg.
- Y2024P cells are UNAFFECTED: window 2024-01-01..2024-08-19 is fully covered by scan_2026
  (last funding row 2024-08-20 covers the terminal stamp).

Remediation (owner): per-fold funding-scan selection mirroring the bar fix
(Y2024P → scan_2026, S0R → scan_2026_a), re-run the S0R DIAG with funding applied,
re-disclose the new numbers before the scored run, return for A7 r6 delta.

## What passed (recomputed)

1. **r4 B1 fix in bytes** — scored-row dict carries
   `labels: [REPLICATION_NOT_PROSPECTIVE, EQUIVALENCE_DATA_RESTAGE_UNPROVEN, UNIVERSE_LISTED_AT_WINDOW_START, OUTCOME_EXPOSED_AMENDMENT_A4]`
   (illiq_scored.py:67-70). (Minor: duplicate `"rc"` key, line 65 dead — later key wins; N1.)
2. **Sweep = 4 cells** — FOLDS = Y2024P + S0R × ARMS = ANCHOR/INV; per-fold catalogs in FOLDS;
   runner `--catalog` required and used for bars; resume filter skips nothing (13 status rows
   all rc=1). 125d warmup and +3d load-end present in runner bytes.
3. **S0R catalog** — 20 symbol dirs = SYMS; build report committed (tracked); spot-check EXACT:
   BTCUSDT 52608 rows, ENAUSDT 52462 rows vs report; parquet span 2024-04-01..2025-09-30 ⊇
   warmup (2024-04-19) + window + load-end (2025-08-24).
4. **A5 authority + window** — §A5 verbatim at root amendment, committed in 7d1db60a; FOLDS
   S0R = 2024-08-22T00:00Z..2025-08-21T00:00Z exact; adjacent non-overlap with the V11 scored
   window (starts 2025-08-22) and with Y2024P (ends 2024-08-19).
5. **Funding data existence** — scan_2026_a covers 2024-08-20..2026-08-21 ⊇ S0R (wiring fails → B2).
6. **DIAG S0R disclosure** — artifacts committed at lane HEAD; metrics match dispatch exactly
   (net −0.589311865184, PF 0.774223024221, MDD 0.624506837125, n=336; thirds sum exactly:
   −0.042406 −0.347927 −0.198979 = −0.589312; 96+128+112=336); anchor entry/exit
   2024-08-26/2025-08-18 inside window; `scored=False`; benchmarks `enters_denominator=false` ×3;
   no scored-status row, no scored outputs (only 8 rc=1 logs) → disclosure necessarily precedes
   any scored run. Caveat: the number is funding-free (B2).
7. **No regression** — engine frozen: 18 unique files (adapter_v10/*.py, hyp_a8_m01.py,
   v11/families/illiq_amihud/*.py) byte-identical to c97283e0; 0 scored ILLIQ cells; root
   tracked tree unmodified; lane clean except cycle-local untracked data; flock free (stale
   registry row pid 71445 dead — carried N2, reclaim per discipline only).
8. **Y2024P carry-over** — budget 8 (XSECT, counted in xsect_scored_summary.json) + 4 (ILLIQ)
   = 12 ≤ 24; Y2024P fold/window/funding/labels all sound.

## Non-blocking

- N1 duplicate `"rc"` key in the row literal (dead code, behavior correct).
- N2 stale heavy-lock registry row pid 71445 (dead), CONTROL_STATE_DRIFT, flock free (carried).
- N3 registry row stale vs amendment chain (phase text, budget.used=0, head 21e4f1be);
  prospective 12/24 holds per A4b+A5; refresh at next owner registry write.
- N4 no shape-only S0R census artifact; A5's "all 20 listed by 2024-04-02" claim not
  independently re-verified (ENAUSDT's 146-row deficit is directionally consistent).
- N5 launcher docstring still says "8 cells" (now stale twice); vestigial launcher SCAN constant.
- N6 carried r4 N4/N5 (frozen identity window strings; dead benchmark clause).

## Gate

`illiq_scored.py` reads exactly `a7_prelaunch_illiq/a7_prelaunch_illiq.json` and exits rc=5
unless verdict == AUTHORIZED. This round 5 REFUSED keeps the gate closed: the S0R cells cannot
run with the broken funding wiring. R4 verdict remains preserved in lane git history (c2bee0c8).
