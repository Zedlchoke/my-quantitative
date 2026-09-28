# DAYTRADER-100-V1 — DIAGNOSTIC: regime map of ≥2/4-fold families + combo ceiling

- diagnostic_utc: 2026-09-28, owner instruction (verbatim): "phân tích các family
  có fold từ 2/4 lời trở lên các thời điểm kinh tế lời, lỗ -> phân tích regime
  rồi lên kế hoạch kết hợp các family đó lại và có gate để đóng mở nhằm tối đa
  hoá lợi nhuận"
- label: **DIAGNOSTIC_OUTCOME_EXPOSED** (§39.3) — mọi số dưới đây đọc từ scored
  outcome ĐÃ LỘ của chính cycle này. Không được dùng để chọn-rồi-kiểm-tra trên
  cùng dữ liệu; không promote; không tune.
- cách đọc preregistered (4 mệnh đề): (1) không-bao giờ-promote các số này như
  edge; (2) nếu combo preregistered (kế hoạch đính kèm) sau này dương → đáng mở
  identity MỚI (cơ chế = conditional allocation), không phải vì các số này; (3)
  nếu âm → khép câu hỏi router/combo trên các legs đã chết; (4) không tune,
  không thử lại ngưỡng.

## 1. Sáu family đạt ngưỡng ≥2/4 fold dương (anchor, x1.0)

| fold (lịch) | 07-PDHLSWEEPFX (EUR) | 09-ASIANRANGE (EUR) | 10-LONDONMOM (EUR) | 34-WEEKEND (BTC) | 35-FUNDCONTRA (BTC) | 76-CORRBREAK (ETH) | ALWAYS_ON_6 | ORACLE* |
|---|---|---|---|---|---|---|---|---|
| GĐ1 2021-04-01→2022-06-30 | −687 | −105 | −230 | +559 | **+6032** | −1274 | +4296 | +6032 |
| GĐ2 2022-07-01→2023-09-30 | +237 | +15 | −374 | −354 | **+2771** | −1573 | +722 | +2771 |
| GĐ3 2023-10-01→2024-12-31 | +69 | **+1058** | +946 | +499 | −1964 | +1770 | +2379 | +1770 |
| GĐ4 2025-01-01→2026-08-31 | −366 | −26 | +110 | −1460 | −3265 | **+4849** | −159 | +4849 |

(đơn vị: bps của notional, tổng cả fold; FX P1–P4 ghép theo cùng lịch GĐ1–GĐ4,
P4 dài hơn GĐ4 23 ngày — disclosed)

- ALWAYS_ON_6 (equal-weight cả 6): **+7.238 bps / 5,4 năm ≈ +111 bps/tháng** trên
  notional 1x — GĐ4 âm (−159).
- *ORACLE (chọn family tốt nhất mỗi fold SAU KHI XEM): **+15.421 bps** — đây là
  TRẦN in-sample của một gate hoàn hảo, không chuyển giao, non-governing.
- Cặp bổ trợ thời gian: FUNDCONTRA (lời 2021–2022, chết 2023+) ↔ CORRBREAK (chết
  2021–2022, lời 2023+); combo 50/50 = +3.673 bps với 3/4 fold dương (GĐ3 −97 ≈
  phẳng). Khám phá BẰNG CÁCH NHÌN KẾT QUẢ → coi như giả thuyết, không phải bằng
  chứng.

## 2. Bản đồ regime kinh tế (chú giải)

- **GĐ1 (2021-04→2022-06)** — bull đỉnh + LUNA: funding/premium perp thường
  cao dương → chân funding-harvest ăn (FUNDCONTRA +6032). FX session books lỗ.
- **GĐ2 (2022-07→2023-09)** — FTX, đáy sâu, funding yếu: FUNDCONTRA vẫn dương
  (+2771, tàn dư vol cao); phần còn lại lỗ.
- **GĐ3 (2023-10→2024-12)** — rally + spot-ETF (2024-01), FX low-vol grind: FX
  session books bật sống (ASIANRANGE +1058, LONDONMOM +946); funding chết (−1964).
- **GĐ4 (2025-01→2026-08)** — từ dữ liệu: dislocation-tail mạnh (CORRBREAK
  +4849), mọi chân funding/session cũ âm sâu, WEEKEND vỡ (−1460).
- Quy luật đọc được: mỗi regime có MỘT chân khác nhau ăn — đúng bài toán gate;
  nhưng cũng đúng cảnh báo: 4 điểm dữ liệu (folds) là quá ít để thiết kế gate
  không overfit, và 2/6 chân bổ trợ có thể thuần ngẫu nhiên.

## 3. Cảnh báo ancestry (bắt buộc đọc trước kế hoạch)

Router/combo class đã chết **5 lần** trong chương trình: JEV-REGIME-ROUTER-V1/V2
(net-negative, thua ALWAYS_ON_MR và random; switching-cost attrition quyết định),
REGIME-STRATEGY-MAPPING, BTC-TWO-REGIME, PHASE-STRATEGY, ILLIQ-REG — cùng phán
quyết NO_INCREMENTAL_VALUE. Kế hoạch đính kèm phải thắng ĐƯỢC các baseline đó
mới được gọi là có giá trị. Ngoài ra 6 chân đều đã fail floors riêng (PF/concen-
tration/stress) — combo không "cứu" chân, chỉ tái phân bổ rủi ro.
