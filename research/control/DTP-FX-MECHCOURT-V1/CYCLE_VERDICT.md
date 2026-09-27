# CYCLE VERDICT — DTP-FX-MECHCOURT-V1 (2026-09-27)

## Verdict

**`DTP_FX_V1_BLOCKED_DATA_OR_COST`**

| Cơ chế (owner instruction 2026-09-27) | Verdict | Căn cứ chính |
|---|---|---|
| `DTPFX-A1` month-end London fix rebalancing | **`F0_KILLED — VETO_VARIANT_SAME_FAMILY`** (vs `TRACKA2-P4A-FIXCERT-01`) + fallback `BLOCKED_FRONTIER_NOT_REOPENED` | Skeleton strip → đúng decision law FIXCERT (trigger pre-fix window / direction công khai từ giá / exit post-fix; payer fix-certainty). Month-end subset = re-gate; MTD direction = rename pressure-sign (anti-variant DTP master §2.3; owner law 2026-09-26). RC FIXCERT: "owner amendment with a NEW economic basis … parameter re-tunes are barred" |
| `DTPFX-B1` news → observed rate repricing → FX lag | **`BLOCKED_DATA`** | Leg rates intraday = 0 bytes toàn hệ (OFR/NYFed daily-only; futures 0-byte stubs; CME BLOCKED_TRANSPORT); PIT ledger 10/131 FETCHED-verified, không consensus/revision vintages, tự mang nhãn EVENTS_OVERLAY_ONLY_NOT_CAUSAL_EVIDENCE. Thay leg bằng phản ứng FX = news-fade = dead class (cấm proxy) |
| `DTPFX-C1` cross-venue synchronous quote discrepancy | **`BLOCKED_DATA`** | Một feed hai chiều duy nhất; venue-2 = 0 bytes mọi path (IBKR 0/357 obs/pair, minTick 0.5 pip; Dukascopy re-download BLOCKED_TRANSPORT; EDQ1 BLOCKED_SOURCE_LICENSE); 8/10 cost components UNMEASURED |

**0 scored cells (0/0 — đúng thiết kế), 0 PnL, 0 holdout looks, sealed
AUDUSD/USDCAD 2026-H1 UNREAD, S1 SEALED, không order, không đụng
shadow/broker/dashboard.** GO phrase `GO DTP FX MECHCOURT V1 SCORED EXECUTION`
chết UNCONSUMED (không gate nào mở để tiêu — không scored cell vô nghĩa nào
được chạy theo đúng owner instruction). P-9: +0/+0 scored (3 rows
ADJUDICATION_NOT_SCORED).

## Câu giới hạn phạm vi bắt buộc (theo precedent DTP-CX-SOLUSDT-C1)

Verdict này KHÔNG phải claim "day-trading FX chết" — nó là adjudication của
ĐÚNG BA cơ chế owner định danh trên authorized evidence space đo ngày
2026-09-27, dưới DTP-FX frontier law (không reopener ⇒ không score). Mọi
re-entry qua owner packet.

## Số đo mới banked (frontier assets)

1. **Fix-window spread census** lần đầu đo trọn bộ: EURUSD/GBPUSD/USDJPY,
   London-hours 13–17 × ME1/ME2/MID, 34,715 obs non-vacuous, DST-verified,
   second-code-path MATCH, A7 recompute delta 0. Kết quả: fix-window KHÔNG
   phải bucket đắt (p50 0.3/0.7–0.8/0.5 pip ≈ mid-month ±0.1; chỉ rollover
   21–22UTC giãn p99 7.8–16 pips). Barrier của fix-family = premium-evidence
   + venue, KHÔNG phải spread bucket.
2. **PIT honesty ceiling đo chính xác**: 10/131 FETCHED-verified (84/131
   schedule-asserted) — mọi tái sử dụng ledger failres phải nâng evidence
   class.
3. **Venue-2 = 0 bytes** re-verified lần thứ ba độc lập (sau DATA-EDGE-UNLOCK
   lane F, broker probe 2026-09-26).

## Chuỗi bằng chứng

- Plan `plans/PLAN_dtp_fx_mechcourt_v1.md` (main 051aaae0) — verdict rules
  pre-registered TRƯỚC khi lane chạy; census được đóng băng là "không cứu A".
- Lane S: `SKEPTIC_court_REPORT.md` (+ HANDOFF_S.json) — F-0 court, 139-row
  failure-memory diet đầy đủ.
- Lane D: `DATAPIT_census_REPORT.md` + `fixwindow_spread_census.json` +
  `fixwindow_census.py` (+ HANDOFF_D.json) — byte census + preregistered
  census.
- A7 terminal: `A7_TERMINAL_AUDIT.md` — **CONFIRM_WITH_FINDINGS** (0
  CRITICAL/HIGH; A7-F1/F2 LOW label-precision; A7-F3..F5 INFO); census
  recompute độc lập delta 0; anti-variant independent judgment đồng ý court
  (0/3 trục identity khác biệt so với ngưỡng ≥2); CONFIRM close.
- Verdict assembly: `VERDICT_assembly.md`; owner unblock: `OWNER_PACKET.md`;
  ledger: `trial_ledger.jsonl` (3 rows ADJUDICATION_NOT_SCORED).

## Registry flip

TERMINAL theo two-half close (branch terminal commit + root control-plane:
FAMILY_FAILURES row `DTPFX1-A1-MEFIX-VARIANT`, MAP bullet, HYPOTHESIS_LEDGER
+0/+0 stamp).
