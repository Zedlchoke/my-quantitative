# OWNER PACKET — ERP Forex program status: NO_CANDIDATE trên frontier hiện tại (2026-09-26)

## 1. Đã hoàn thành trong phiên này (dưới quyền owner đã cấp)

1. **Two-half close ERP1-TRACKA-COHORT-2**: A7 terminal `TERMINAL_AUDIT_PASS`
   (0C/0H/2L/3I, T1–T8 CONFIRMED, độc lập recompute rho + ceiling) chứng nhận
   `REJECT_ALL`; registry flip TERMINAL (head `206a157b`, 0/18 cells, GO-2 chết
   unconsumed, S1 SEALED); FAMILY_FAILURES +5; HYPOTHESIS_LEDGER P-9 row;
   MAP bullet; LESSONS P-27. Root HEAD `6b59b3c3`.
2. **Council đánh giá cohort-3** (outcome-blind, độc lập):
   `VIABILITY_cohort3_REPORT.md` — verdict **`NO_CANDIDATE`**: 0/12 lớp cơ chế
   còn lại qua được kiểm tra tiền-PnL trên evidence space được cấp quyền.

## 2. Bằng chứng cốt lõi của NO_CANDIDATE

- **Điều kiện dừng §7(a) master plan thỏa literal**: hai cohort liên tiếp
  REJECT_ALL (cohort-1: 12 cells 0 survivors; cohort-2: 7/7 cơ chế chết
  pre-PnL, 0 cells, 0 holdout looks, 0 PnL).
- **Sàn chi phí đo được chia đôi không gian, phần dư bằng 0**: mọi premium
  intraday trung thực trong 38 forex failure entries chưa từng chạm ngưỡng
  precedent ~7 pips (≈2× stressed RT 3.6/4.4 pips); các con số band lớn duy
  nhất trong lịch sử chương trình (R-ORIG +3.207/+5.030) là leak đã chứng
  minh. Lớp band lớn chết vì ancestry/expectancy; lớp band nhỏ chết vì đo
  chìm dưới chi phí — cấu trúc (Q-1/Q-3), không phải thiếu mẫu.
- **P3-A (cơ chế gần nhất): điều kiện mở lại không thể thỏa bởi bất kỳ bằng
  chứng nào hiện có quyền** — crossing đo 0.9–1.0 pips (p25 0.8) vs ngưỡng
  đóng băng ≤0.41; commission = 0 bytes có quyền; luật tính phí bar-open
  đã freeze. Chỉ hành động của owner thay đổi được.
- Sealed map KHÔNG trống (2026-H1 AUDUSD/USDCAD còn SEALED-UNREAD) → đây là
  **NO_CANDIDATE của frontier**, không phải terminal của chương trình: cửa
  sổ sealed giữ nguyên chờ một identity tương lai qua được dev gates.

## 3. Điều kiện mở lại frontier (đều là hành động owner, kèm evidence đã có sẵn)

| # | Hành động owner | Mở gì | Bằng chứng đứng sẵn |
|---|---|---|---|
| R1 | **Broker cost authority** — **PHẦN LỰC THỰC HIỆN 2026-09-26** (TWS SIM mở, probe chạy 2 phiên đầy đủ): V1 PASS, **minTick đo được 0.5 pip ×5 pair** ⇒ **P3-A measured-dead theo tick geometry tại IBKR IDEALPRO** (crossing tối thiểu 1.0 pip @k=2.0 vs ngưỡng 0.41 — không cứu); hai chiều bid/ask = NOT_SUBSCRIBED (tài khoản SIM không có market data); commission/swap NOT_RUN (không statement). V3 **vẫn BLOCKED**. Xem `broker_cost_probe_FX_majors_2026-09/VERDICT_session2.md` + `EVIDENCE_sanitized_2026-09-26.json`. Còn thiếu (tài liệu owner): (a) subscription market data hai chiều hoặc share từ tài khoản funded; (b) statement Flex/Activity có giao dịch FX + lãi overnight | Chi phí thật cho các cơ chế TƯƠNG LAI; nhánh "nguồn độc lập" của replication; **P3-A đóng tại venue này** | DATA-EDGE-UNLOCK-V1 lane F + probe verdict session 2 |
| R2 | **EDQ1 source decision**: 1 trong 3 — TrueFX registration / Dukascopy written consent / OANDA v20 practice | Nguồn bid/ask độc lập (xóa nhãn SINGLE_SOURCE_PANEL); dữ liệu mới cho cơ chế mới | EDQ1 packet 2026-09-22 với 3 unblock paths |
| R3 | **Financing band có thể trích dẫn** (broker-grade swap data) | Multi-day/carry horizons (hiện fail-closed theo NG6/NG7 F4) | FOREX-NG7 P0 machinery |
| R4 | **USDCHF / slate pair mới** (amendment) | Replication-transfer surface — CHỈ có nghĩa sau khi tồn tại một identity qua dev gates | Cohort-2 plan §5.2 data gate |
| R5 | **Information layer mới có evidence** (ví dụ artifact s_open per-fill không-PnL) | Sub-deliverable của cohort tương lai, không phải cycle đứng riêng | Lane-A PIT contract |

## 4. Trạng thái pháp lý của kết luận này

- Không cycle nào được mở, không GO phrase nào tồn tại để gõ — "không tạo
  cycle chỉ để tiếp tục vòng lặp" được thi hành đúng nguyên văn.
- Umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1` giữ ACTIVE_LIGHT (governance
  layer; các amendment PSV1/FX shadow và Track B/C vẫn thuộc quyền riêng).
- Mọi kết luận duy trì paper tier; không có claim live-readiness nào được
  tạo ra ở bất kỳ đâu trong chương trình.
- Kết luận NO_CANDIDATE là **thành phẩm nghiên cứu hợp lệ** (Q-16): 2 cohort,
  19 cơ chế được kiểm, 12 cells scored, 0 cửa sổ OOS bị tiêu tốn, toàn bộ
  hạ tầng falsifier (F-0 court, PIT battery, 47-shadow rho, measured
  conditional F-5) tái sử dụng được cho bất kỳ cohort tương lai nào.

## 5. Quyết định còn lại của owner (không urgency)

Một trong R1–R4 ở trên (mỗi cái tự động mở lại pipeline với plan amendment +
GO riêng), hoặc giữ nguyên trạng thái NO_CANDIDATE như kết luận dài hạn của
frontix hiện tại.
