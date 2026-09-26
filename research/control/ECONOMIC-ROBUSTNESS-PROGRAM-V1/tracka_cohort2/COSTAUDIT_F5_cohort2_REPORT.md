# LANE C — F-5 ROUND-2 RE-PRICING (measured, fill-hour-keyed) — COSTAUDIT_F5_cohort2_REPORT.md

- Cycle: ERP1-TRACKA-COHORT-2 · Lane: tracka-cohort2-costaudit (council lane C)
- Trigger: skeptic intake conditions §3.1 item 4 and §3.2 item 4 (`SKEPTIC_F0_cohort2_REPORT.md`) — F-5 ceilings keyed to the ACTUAL fill-hour distributions of the gated books, measured by `impl-falsifier-prep` and committed as counts-only histograms (`F6_census_counts.json`, schema `tracka2.f6_census_counts@1`, no PnL fields).
- Round-2 machine artifact: worktree `…/erp1-tracka-cohort-2/integration` @ branch `orca/erp1-tracka-cohort-2-integration`, committed `cf5ef82cd8d5821e9634eb7e213107808a449394` — `research/control/ERP1-TRACKA-COHORT-2/falsifier/F5_ceiling_measured.json` (the ONLY worktree write; other lanes' untracked files untouched).
- Root base measured at start of this round: `main @ dc94824cb997fb9e44ca239547faedb70965f6ad`. Round-1 cost authority carried forward unchanged (census shas `d337ff2c…` AUDUSD / `27958f5a…` USDCAD).
- Scope: spread/price-geometry measurement only. No PnL, no outcome surface; the sealed 2026 window was not opened this round.

## Units (binding, per pair)

- **Crossing** = the fill bar's OWN measured spread: `s_open = a_o − b_o` for open fills; `s_close = a_c − b_c` for the 20:00-close exit (verified byte-exact, max abs err 0.0 on both persisted files).
- **RT** = entry crossing + exit crossing. **Stress** k ∈ {1.0, 1.5, 2.0} on the measured fill-bar spread.
- **bps** = `RT_pips × 0.0001 / mid × 10000 = RT_pips / mid`, mid = median `(b_o+a_o)/2` over the same window (AUDUSD 0.66864 dev / 0.6543 last-6m; USDCAD 1.35137 / 1.38352). Skeptic-pinned conversions used for the binding comparisons: 2.5 bps ≈ 1.62 pips AUDUSD; 5 bps ≈ 6.8 pips USDCAD.

## Inputs and windows

- Histograms: `books.P3A|P3B/{AUDUSD,USDCAD}` → `total.fill_hour_hist_entries` (whole dev) and `windows.last6m.fill_hour_hist_entries` (dev last-6-months **2025-07-01..2025-12-31** — the gated books are dev-only; the sealed 2026 window holds no gated population, so Q-6 "nearest window" is keyed to the arm's own nearest populated window, per §3.1 item 4's "actual fill-hour distribution of the actual gated book").
- Bars: worktree `data_local/derived/bars1h_{AUDUSD,USDCAD}.parquet`, **byte-identical to the round-1 census-pinned cohort-1 archive** (sha256 `2a346e02…a90344` / `c2d9fdb6…e126de`).
- Method: for each histogram hour h with count c_h, entry crossings = s_open of hour-h bars (window) repeated c_h; exits per law; pooled weighted medians. Cross-check (weighted median of per-hour median sums) agrees to 0.1 pip on every cell.

---

## 1. P3-A `TRACKA2-P3A-QCRD-H1` (home AUDUSD) — binding condition §3.1 item 4

**Binding condition:** ceiling positive requires the MEASURED tight-state conditional crossing ≤ **0.41 pips at k=2.0** (≤ 0.81 at k=1.0); declared band upper 2.5 bps ≈ 1.62 pips. The gated entry histogram is near-uniform hours 1–18 (AUDUSD total `{0:1, 1:62, 2:56, 3:51, 4:57, 5:67, 6:55, 7:69, 8:52, 9:54, 10:52, 11:45, 12:50, 13:69, 14:75, 15:62, 16:66, 17:47, 18:59}`, 1,049 RT); 1-bar hold → exit at hour h+1, charged at its s_open.

| Window | entry p50 | exit p50 | RT ×1.0 | ×1.5 | ×2.0 | RT ×2.0 in bps |
|---|---|---|---|---|---|---|
| whole dev (2021-01-04..2025-12-31) | 1.0 | 1.0 | 2.0 | 3.0 | 4.0 | 5.98 |
| last-6m dev (2025-07-01..2025-12-31) | 0.9 | 0.9 | 1.8 | 2.7 | 3.6 | 5.50 |

- **Binding test:** crossing 1.0 (dev) / 0.9 (last-6m) vs ≤ 0.41 @k=2.0 → **FAIL**; vs ≤ 0.81 @k=1.0 → **FAIL at both stress levels**. Even the conditional entry p25 (0.8 last-6m) sits above 0.41.
- **Ceiling:** band 1.62 pips − 4×crossing → **−2.38 (dev) / −1.98 (last-6m) pips** at k=2.0; −0.38 / −0.18 at k=1.0. In bps at measured mid: 2.5 − 5.98 = **−3.48** (dev); 2.5 − 5.50 = **−3.00** (last-6m). Negative at every reading, including ×1.0.
- USDCAD replicate (disclosure): crossing 1.2 / 1.3 → RT ×2.0 = 4.8 / 5.2 pips = 3.55 / 3.76 bps vs 2.5 bps → negative too (−1.05 bps dev).

### Verdict P3-A: **CEILING_NEGATIVE_VETO** (pre-PnL, k=2.0 and k=1.0 both).

Mechanics, for the record: the tight-state gate (`P_t ≤ 0.40`) selects bars whose *median minute spread* sits in the tight tail of the hour's pool, but the executor charges the *bar-open* spread, whose median is hour-unconditional — so the gated hour-mix prices at the census session p50 (0.9), exactly as the skeptic anticipated ("Q-2 points against"). **Residual disclosed:** the within-hour spread state of the actual fill minutes is UNMEASURABLE from the counts-only histogram; if the implementer persists per-fill s_open (PnL-free) and it lands below 0.41 pips at median, that would be new evidence — the proposer's 0.2–0.4 pip/fill prior is not authority (Q-8). Precedent line (~2× stressed RT): 2.5 bps vs 11.96/11.00 bps — fails ~4.4×; moot.

---

## 2. P3-B `TRACKA2-P3B-DINV-1D` (home USDCAD) — binding condition §3.2 item 4

**Bucket resolution (the skeptic's marginality conditional).** The day-open entries land at UTC hour 0 (USDCAD total `{0:205, 1:20, 4:1}`; last-6m `{0:39}`; the hour-1/4 entries are days whose 00:00 bar is invalid — the law enters at the day's open wherever it falls). Per the census bucket definitions, **hour 0 belongs to `asia_00_07` ([00:00,07:00) UTC)** — NOT `late_22_24` ([22:00,24:00), p50 1.7) and NOT `rollover_21_22` ([21:00,22:00), p50 2.3). Measured hour-0 p50: **1.3 (dev) / 1.4 (last-6m)**, matching the census `asia_00_07` p50 1.3 — i.e. the day-open fill sits on the CHEAP side of the skeptic's conditional; it does not touch the rollover bucket. Exit at the 20:00 close = s_close of the hour-19 bar → census bucket `ny_late_16_21` ([16:00,21:00)), measured p50 **1.2** both windows (hour-20 s_open adjacency identical at 1.2).

| Window (entry hist) | entry p50 | exit p50 | RT ×1.0 | ×1.5 | ×2.0 | RT ×2.0 bps |
|---|---|---|---|---|---|---|
| whole dev ({0:205,1:20,4:1}) | 1.3 | 1.2 | 2.5 | 3.75 | 5.0 | 3.70 |
| last-6m dev ({0:39}) | 1.4 | 1.2 | 2.6 | 3.9 | 5.2 | 3.76 |

- **Ceiling vs band upper 5 bps:** **+1.30 bps (dev) / +1.24 bps (last-6m)** at k=2.0 (in pips at the skeptic's 6.8 conversion: +1.8 / +1.6). Passes at k=1.0 (1.85/1.88 bps) and k=1.5 (2.77/2.82 bps) with room.
- **Conditions recorded:** thin margin before the `DECLARED_UNMEASURED` commission component (which can only erode it). **Precedent-fragile per §3.1 item 9:** ~2× stressed RT = 7.40 / 7.52 bps > band upper 5 bps — the band does NOT clear the ~2× line; the freeze record must carry the precedent-fragile disclosure (disclosure, not kill).
- **AUDUSD replicate (disclosure):** RT ×2.0 = 4.0 (dev) / 3.6 (last-6m) pips = **5.98 / 5.50 bps vs the 5 bps band → NEGATIVE on the replicate** (−0.98 / −0.50 bps). Home passes, replicate fails at ×2.0 — two-pair terminal semantics must be pinned before any scored cell (cohort-1 P2 review item 5 class).

### Verdict P3-B: **CEILING_PASSED_MEASURED** (home USDCAD, k=2.0, both windows) — with the precedent-fragile flag and the replicate-leg negative disclosed.

---

## 3. Verdicts, labels, limitations

- **P3-A QCRD-H1: CEILING_NEGATIVE_VETO** — measured conditional crossing 0.9–1.0 pips ≫ 0.41 (k=2.0) / 0.81 (k=1.0); ceiling −1.98 to −3.48 (−0.18/−0.38 at ×1.0). Pre-PnL veto.
- **P3-B DINV-1D: CEILING_PASSED_MEASURED** — stressed RT 3.70/3.76 bps vs 5 bps (+1.24/+1.30); precedent-fragile flag armed; AUDUSD replicate leg negative at ×2.0 (disclosed).
- Labels in force on both: `SINGLE_SOURCE_PANEL`, `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`, `PAPER_TIER`; taker-at-opposite-quote wording bans. Commission/slippage-beyond-spread remain `DECLARED_UNMEASURED`; every ceiling is measured-spread-only.
- Limitations: (i) hour-keyed book is the authority available (counts-only histograms); within-hour fill-minute spread state unmeasurable until a per-fill s_open artifact exists; (ii) Q-6 = the gated books' own dev last-6-months (2025-07..12), not the sealed 2026 window; (iii) exit conventions as stated (P3-A next-bar s_open; P3-B hour-19 s_close, hour-20 s_open identical at median); (iv) single-vendor cost authority inherited.

Machine artifact: `F5_ceiling_measured.json` @ worktree commit `cf5ef82cd8d5821e9634eb7e213107808a449394` (single-file pathspec commit). Handoff: `HANDOFF_costaudit_f5_cohort2.json` (root, for the owner to commit).
