# PACKET — L-FX (forex data census + validation)

ROLE: A3-class data-authority survey lane. OBJECTIVE: complete §5 authority
rows + gap candidates for every FOREX dataset the program holds or has held.
WORKTREE: `/Users/hoangminhlong/my-quantitative/.worktrees/data-foundation-v1/lane-fx`
BRANCH: `orca/dfv1-lane-fx`. Allowed writes: `research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/fx/` inside that worktree only. COMMON.md applies in full.

## Owner priority list (verbatim from OWNER_DIRECTIVE.md — bind every gap row to these)
Forex: bid/ask có timestamp đủ mịn, spread đúng giờ đặt lệnh,
commission/slippage và swap/financing từ broker; lịch phiên và DST; sự kiện
kinh tế với thời điểm công bố và các lần sửa số liệu. Phân biệt giá
indicative với quote có thể giao dịch, dữ liệu một nguồn với replication
độc lập.

## Census targets (enumerate + row per dataset; verify existence first with du/ls, read manifests)
1. Dukascopy M1 BID/ASK corpora — EURUSD 2021–2025 +2026-H1 (in
   `.worktrees/eurusd-open-search-v1/`, `-v2/`, `eurusd-rangeexp-scored-v1/`),
   GBPUSD + USDJPY (`.worktrees/fx-majors-search-v1/`). Find the actual data
   roots (du -sh; look for data/staging dirs + SHA256SUMS/census.json).
   Validate: file counts vs census claims, first/last day-file names, spot
   sha sample; record spread census artifacts (p50 pips by session/rollover)
   as measured cost-evidence pointers.
2. TD (Twelve Data) spot OHLC legs (FOREX-NG5/NG6/NG7; XAU 1day 12,268 rows
   1979–2026) — likely in `.worktrees/forex-ng5|ng6|ng7/` and/or P-13
   tarballs under `~/staging_backups/` (check
   `research/control/staging_backups_manifest.md`). Status must carry the
   standing ruling: vendor OHLC-only, NO cost authority (F4 class).
3. Macro/event archives: BIS WS_CBPOL, ECB SDNX/HICP vintaged, FRED granted
   set + vintaged (S2), ALFRED, CFTC CoT, official release calendars
   (GB/CA/AU/NZ), CPI archives — locate via terminal verdicts under
   `.worktrees/forex-ng*/research/control/*_run/` and
   `erp1-tracka-cohort-1|2` (note: cohort worktrees exist; ERP1 sealed
   holdouts 2026-H1 AUDUSD/USDCAD are FORBIDDEN content — manifest metadata
   only). If archives were cleaned, resolve from `~/staging_backups` +
   manifests; a dataset that exists only as archive = status with
   `local_presence` = archived + manifest path.
4. `~/.my-quantitative-data/forex-intra-bidask-v1/` (8 KB canary) and
   `fx-futures-frontier-v1/` (0 B) — rows carrying BLOCKED_TRANSPORT (map
   note per §14 F9) with the standing SNI-filter evidence (FIBV1/FXF-F).
5. Cost-probe artifacts (read-only pointers for L-COST, but record them as
   datasets): `research/control/forex_mt5_cost_probe_2026-09/`,
   `research/control/xauusd_ibkr_probe_2026-09/`.
6. FX-RANGEFADE-2M-SHADOW-V1 data (ACTIVE_LIGHT, workers>0) — F5
   metadata-only rule.
7. FOREX-SEARCH-V1 staging (measured spread curves census) — locate + row.

## Gap candidates to draft (each: hypothesis class, prior kill it fixes, falsifying control, est. cost)
- Broker-grade spread/commission/swap for FX majors (the ERP1 3.6/4.4-pip
  cost floor that partitioned the space; NG6/NG7/DEU-LaneF kills).
- Tradables vs indicative quotes; independent second source for EURUSD
  (replication).
- Economic events with publication timestamps + revision vintages (beyond
  the CPI calendars already used; note what ERP1 cohorts consumed).
- Session/DST calendar authority (exchange_calendars / homegrown).
- Financed (swap) bands per pair — the NG7 F4 kill.
