# DRAFT PLAN — REGIME-GATED-COMBO-V1 (chờ owner duyệt; chưa đăng ký)

- proposing_utc: 2026-09-28, theo chỉ thị owner (diagnostic kèm:
  research/control/DAYTRADER-100-V1/DIAGNOSTIC_REGIME_COMBO_2026-09-28.md)
- cơ chế mới (identity): **conditional allocation** — một bộ gate theo biến
  trạng thái kinh tế đo được PIT, phân bổ notional giữa các chân đã rescore.
  KHÔNG phải trung bình cộng, KHÔNG phải chọn-fold.

## 1. Chân (legs) — 6 anchors đã S0-rescore (disclosed: individually dead)

PDHLSWEEPFX / ASIANRANGE / LONDONMOM (EURUSD M1), WEEKEND / FUNDCONTRA (BTC 1m),
CORRBREAK (ETH 1h). Mọi số chân kế thừa verdict CELL_FAIL gốc — combo không đổi
trạng thái chân.

## 2. Gate variables — CHỈ biến ngoại sinh, PIT-measurable, đóng băng TRƯỚC khi chạy

- G1 funding-regime: z 30 ngày của funding 8h BTC (đo từ bytes đã fetch).
- G2 vol-regime: percentile 30 ngày RV của BTC và của EURUSD (tính từ chính dữ liệu chân).
- G3 trend-state: |return 120h| / vol 120h của BTC.
- G4 corr-regime: rolling-corr 168h ETH–BTC (đúng observable của CORRBREAK).
- Ngưỡng mỗi biến: freezing tại G3-freeze của cycle mới, CHƯA nhìn combo output.
  Quy tắc phân bổ đóng băng dạng bảng: mỗi tổ hợp (high/mid/low × 4 biến) cho
  weights; mặc định equal-weight khi không vùng nào kích hoạt.

## 3. Ràng buộc chống-overfit (cái giá JEV đã trả)

- Gate tái phân bổ tối đa 1 lần/tuần; chi phí switching tính đủ (attrition).
- Baseline PHẢI thắng hết: ALWAYS_ON_6, random-gate (seed đóng băng), best-single-
  leg, clock-shadow gate (Q-7: bỏ payload giữ lịch). Thiếu một baseline = NOT_RUN.
- Folds: cùng lịch GĐ1–GĐ4; S1 SEALED. PBO ≥ 8 configs else NOT_RUN.
- Ancestry rho ≤ 0.20 vs các observable router đã chết (JEV V1/V2, phase, two-
  regime) — immovable.
- Budget: 3 cells (anchor combo + 2 neighbour = ngưỡng gate nới/thắt).

## 4. Kết quả đọc trước (preregistered)

- Âm hoặc không thắng baseline → `REGIME_COMBO_NO_INCREMENTAL_VALUE`, khép
  câu hỏi combo trên legs chết (lần thứ 6 của class — coi như đóng hẳn class).
- Dương và thắng hết baseline → mở identity mới; BƯỚC TIẾP THEO duy nhất được
  phép là paper-forward trên SHARED-PORTFOLIO-100K-V1 (forward-only, không dùng
  số quá khứ claim).
- Không tune ngưỡng sau khi thấy kết quả. Không retry.

## 5. Kỳ vọng trung thực (Lead)

Prior tiêu cực: 5 tiền lệ router chết + 4 folds quá ít + 6 chân đều đã fail
floors riêng. Trần in-sample của gate hoàn hảo là +15.421 bps (ORACLE, non-
governing) — con số thực tế sau switching-cost có xét sẽ thấp hơn nhiều.
Giá trị của cycle này là ĐO CHO CÂU HỎI ĐÓNG, không phải kỳ kỳ tìm sống sót.

## 6. Hai chìa khóa

A7 prelaunch như thường lệ; GO phrase đề xuất: `GO REGIME GATED COMBO V1 SCORED EXECUTION`.
