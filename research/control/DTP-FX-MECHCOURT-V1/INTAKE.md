# INTAKE — DTP-FX-MECHCOURT-V1 (Lead, 2026-09-27)

## Machine state (đo tại intake)

- Root `/Users/hoangminhlong/my-quantitative`, branch `main`, HEAD `051aaae0`
  (commit đăng ký plan). Worktree
  `.worktrees/dtp-fx-mechcourt-v1/integration`, branch
  `orca/dtp-fx-mechcourt-v1-integration` @ `051aaae0`. Registry row
  DTP-FX-MECHCOURT-V1 ACTIVE_LIGHT, budget 0/0, GO phrase
  `GO DTP FX MECHCOURT V1 SCORED EXECUTION` REGISTERED_NOT_CONSUMED
  (registry_sha256 `cb934580fc57083f42c7d68c77048bdf44bd30edd409c7ed8605c3bcb1278c74`).
- Heavy lock `FREE_PROVEN` (đo 2026-09-27 đầu phiên; re-measure trước mỗi
  bước nặng — cycle này chỉ census nhẹ, không giữ lock).
- Disk 29 GiB free (`df -h /`).
- Dirty tree root = untracked của session khác (bảo toàn — P-10).

## Data plane (Lead đo sơ bộ; Lane D re-verify độc lập và là authority)

- Dukascopy M1 bid/ask: EURUSD `.worktrees/fx-rangefade-2m-shadow-v1/
  research/control/FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/` (qua
  2026-09-23, bars15.parquet 136,485 rows); GBPUSD/USDJPY
  `.worktrees/fx-majors-search-v1/integration/research/control/
  FX-MAJORS-SEARCH-V1/data_local/` (qua 2026-09-23). ĐỌC-ONLY public data;
  không đụng trạng thái nội bộ shadow (no-touch DTP §1.2).
- AUDUSD/USDCAD raw: KHÔNG trên đĩa; 1H ANC parquet trong
  `erp1-tracka-cohort-1/repro_twin/...` chứa sealed 2026-H1 rows — CẤM MỞ.
- Rates intraday: 0 bytes. Futures: 0 bytes. Venue-2: 0 bytes (IBKR probe
  2026-09-26: 0 two-sided obs, minTick 0.5 pip).
- PIT macro ledger: `research/control/ERP1-TRACKA-COHORT-1/failres/
  failres_events_timeline.jsonl` (131 events, 10/131 minute-exact,
  DIAGNOSTIC_OUTCOME_EXPOSED).
- Cost book pinned: AUDUSD/USDCAD conditional crossing p50 0.9/1.1 (last-6m)
  → stressed RT ×2.0 = 3.6/4.4 pips; EURUSD/GBPUSD/USDJPY crossing p50
  0.3/0.8/0.5 pips; rollover p50 2.0/2.3 p99 12.3/16.7; sunday 4.6/6.8.

## Frontier state

- VIABILITY cohort-3 (2026-09-26): `NO_CANDIDATE` 0/12 class; reopening =
  owner actions R1–R5. Broker probe: `BLOCKED_BROKER_COST_AUTHORITY` stands.
- EDQ1: `BLOCKED_SOURCE_LICENSE`, 3 unblock paths chờ owner. DTP GO-1 Q4:
  FX DORMANT. Reopener bytes mới từ 2026-09-26: KHÔNG.

## Dispatch (handoff paths)

- Lane S: `research/control/DTP-FX-MECHCOURT-V1/HANDOFF_S.json` →
  `SKEPTIC_court_REPORT.md`
- Lane D: `research/control/DTP-FX-MECHCOURT-V1/HANDOFF_D.json` →
  `DATAPIT_census_REPORT.md` + `fixwindow_spread_census.json` + script
- Lane A7 (sau verdict assembly): `HANDOFF_A7.json` → `A7_TERMINAL_AUDIT.md`
