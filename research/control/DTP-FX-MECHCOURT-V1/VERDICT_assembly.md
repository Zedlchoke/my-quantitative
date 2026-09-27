# VERDICT ASSEMBLY — DTP-FX-MECHCOURT-V1 (A1/Lead, 2026-09-27)

Inputs: SKEPTIC_court_REPORT.md (lane S), DATAPIT_census_REPORT.md +
fixwindow_spread_census.json (lane D), plan §4 (pre-registered verdict rules).
Lead tổng hợp; không đảo thứ tự ưu tiên; không thay verdict của lane.

## Verdicts (per plan §4 priority)

### A — `DTPFX-A1` month-end London fix rebalancing

**`F0_KILLED — VETO_VARIANT_SAME_FAMILY` (vs `TRACKA2-P4A-FIXCERT-01`)**
+ fallback ghi kèm: `BLOCKED_FRONTIER_NOT_REOPENED` (nếu skeleton được coi là
khác — vẫn không score được).

- Skeleton: strip "ước lượng rebalance theo benchmark từ thông tin công khai"
  → còn lại {trigger cửa sổ pre-fix cuối tháng; direction = dấu đại lượng
  công khai từ lịch sử giá; exit sau fix} = đúng decision law FIXCERT
  (entry F−1h, direction pressure-sign, exit F bar open). Month-end subset =
  re-gate/calendar re-clock; MTD direction = rename của pressure sign
  (anti-variant DTP master §2.3; owner law 2026-09-26 "adding an observable
  is not a new mechanism"; Q-3).
- Payer: fix-certainty premium — KHÔNG khác căn bản so với khai báo FIXCERT
  (đã PASS payer test ở cohort-2; kill không nằm ở payer).
- RC FIXCERT binding: "owner amendment with a NEW economic basis (cheaper
  measured execution or larger evidenced premium); parameter re-tunes are
  barred" — cơ chế A là parameter re-tune trên đúng family đã bị kill.
- Class 5 VIABILITY (fix-window/clock/calendar) DEAD; Q-7: direction = trend
  sign × calendar clock — không information layer mới.
- Census fix-window (lane D, MỚI ĐO): bucket chi phí fix-window trên
  EURUSD/GBPUSD/USDJPY p50 0.3/0.7–0.8/0.5 pip/crossing (bằng giữa tháng,
  ±0.1 pip; 34,715 obs non-vacuous; DST verified; second-path recompute
  MATCH) — số đo KHÔNG cứu A (kill là ancestry/class + frontier, đã đóng băng
  ở plan §4 trước khi census chạy); nó loại được giả thuyết "spread giãn ở
  fix là lý do chính" và làm sắc owner packet: barrier của A là
  premium-evidence + reopener, không phải spread bucket.
- Thiếu cho mọi re-entry: PIT fix-flow information layer (ngoài panel giá);
  bề mặt chưa exposure (USDCHF-class sau data gate; sealed 2026-H1 KHÔNG tiêu);
  cost authority R1/R2.

### B — `DTPFX-B1` news → observed rate repricing → FX lag

**`BLOCKED_DATA`** (primary) — adjacency class 7 ghi kèm như fence, không
phải verdict.

- Leg "phản ứng thị trường lãi suất ĐÃ QUAN SÁT ĐƯỢC" không thể kiến tạo:
  intraday rates-market series = 0 bytes toàn hệ (OFR/NYFed daily-only tới
  2026-09-14; futures = 5 stub 0-byte; CME BLOCKED_TRANSPORT L-FXFF-1).
  Daily reference rates không quan sát được phản ứng TRƯỚC thời điểm vào
  lệnh intraday — thay bằng phản ứng của chính FX = news-fade = dead class
  (bị cấm thay proxy, A7-F1 law; owner instruction: "không phải đoán tin
  hay news-fade").
- PIT release ledger hiện có dưới evidence floor: 131 events nhưng chỉ
  10/131 minute-exact FETCHED-verified (84/131 schedule-asserted); không
  consensus/revision vintages PIT; mọi row mang nhãn
  EVENTS_OVERLAY_ONLY_NOT_CAUSAL_EVIDENCE + DIAGNOSTIC_OUTCOME_EXPOSED —
  tự cấm dùng làm causal evidence.
- Fence cho mọi re-entry tương lai: DGS10-level exposure-form control là
  shadow BẮT BUỘC (shape đã giết FXFV8-A5-P1, FXNG1-A4-P2 — control
  out-earned anchor); sham-calendar control bắt buộc (FXFV5, FXFV7-A4-P1);
  clock-only shadow Q-7.

### C — `DTPFX-C1` cross-venue synchronous quote discrepancy

**`BLOCKED_DATA`** (primary). Court KHÔNG thi hành F0 kill (chính xác):
chưa có phép đo chết trực tiếp cho same-pair cross-venue — các họ hàng gần
nhất là fences vũ trang, không phải kill.

- Chỉ MỘT feed hai chiều tồn tại (Dukascopy archive, SINGLE_SOURCE_PANEL,
  TCU-risk posture). Venue-2: IBKR probe 0/357 valid obs/pair (1785/1785
  sentinel rows BID/ASK=−1); Dukascopy re-download BLOCKED_TRANSPORT
  (SNI-keyed, FOREX-INTRA-BIDASK-V1); TrueFX/OANDA owner-gated (EDQ1
  BLOCKED_SOURCE_LICENSE). Hai chân taker cần broker-grade books hai venue —
  8/10 cost components UNMEASURED.
- Fence vũ trang cho re-entry: Q-4 delay-pair + clairvoyant battery bắt
  buộc; shadows FXFV7-A6-P2 (own-lag out-earn), DTPCX1-I002
  (fictional-counterparty veto); M1 clock không đủ — cần tick hoặc tốt hơn
  CẢ HAI venue.

## Tổng hợp cycle

**Terminal: `DTP_FX_V1_BLOCKED_DATA_OR_COST`** — 0/0 scored cells (đúng thiết
kế), 0 holdout looks, sealed 2026-H1 AUDUSD/USDCAD UNREAD, S1 SEALED, không
order, không đụng shadow/broker/dashboard. GO phrase
`GO DTP FX MECHCOURT V1 SCORED EXECUTION` chết UNCONSUMED (chưa từng có gate
để tiêu — không cơ chế nào qua đủ điều kiện để mở freeze).

0 scored cell vô nghĩa đã được chạy: KHÔNG (đúng owner instruction). Kết quả
này khớp kỳ vọng modal từ VIABILITY 2026-09-26 (NO_CANDIDATE 0/12 class) —
Q-16: negative có bằng chứng là thành phẩm.

## Số mới banked cho frontier (dù verdict âm)

1. Bucket chi phí fix-window London (ME1/ME2/MID × hours 13–17) đo TRỌN ĐỦ
   lần đầu trên 3 pair exposed — fix-window KHÔNG phải bucket đắt; barrier
   của fix-family là premium-evidence + venue, không phải spread bucket.
2. Ledger PIT 131-event: honesty ceiling đo chính xác 10/131 FETCHED (sửa
   truyền miệng "minute-exact" mơ hồ) — mọi dùng lại phải qua nâng cấp
   evidence class này.
3. Bằng chứng venue-2 = 0 bytes được re-verify bằng bytes 2026-09-27 (thứ ba
   độc lập sau DATA-EDGE-UNLOCK lane F, broker probe).
