# BÁO CÁO TIẾNG VIỆT — FUTURES-DEEPRESEARCH-V2-20261003 (A1 Lead, 2026-10-03)

Vòng nghiên cứu sâu theo yêu cầu owner ("nghiên cứu thật kỹ càng, tốn cả ngày
cũng được") trên dữ liệu mới + 7 A7 audit riêng từng phần + delta verify.

## Dữ liệu mới vòng này

- **Mua thêm (owner duyệt trong ceiling $125):** 4 mã FX lùi về **2020-01-01**
  ($12.34; lũy kế $118.15/$125, drift $0). NQ/ES giữ 16+ năm từ vòng trước.
- **Backup:** iCloud mirror **10,539/10,539 file SHA-khớp** cả hai dataset
  (av1-trim 76 chunks + nonprice), cập nhật tới các tidy mới nhất.

## Kết quả nghiên cứu (6 dossier v2, ~40-50 số headline mỗi mã, A7 recompute khớp)

**Nhận thức cấu trúc mới lớn nhất:**
1. **Cửa sổ v1 từng được dùng là "yên tĩnh bất thường"**: v1-window nằm ở
   percentile 57 (NQ), 6.8 (6E!) của phân bố 16 năm — mọi kết luận hành vi
   v1 giờ được đặt đúng vị trí trong phân bố đầy đủ.
2. **Roll-spread đảo dấu theo era lãi suất** (NQ/ES): chuỗi không adjust có
   thể nhúng +1,014 điểm drift ảo riêng năm 2024. CIP: 6B corr +0.84 theo
   differential BoE−Fed (kết quả "mixed-sign" của v1 bị overturn — 4 rolls
   v1 nằm đúng cửa sổ differential 0.00pp); 6A 16/16 khi differential ≥25bp;
   6J chưa từng flip; 6E 27/27 dấu nhưng **r=0.91 vintage-fragile** (PIT-as-of
   → −0.11; chỉ dấu là bền).
3. **Phiên 23 giờ giải phóng cấu trúcsession**: Globex mang 21-54% phương sai
   ngày (ES); ECB block 15.6% variance/12.5% volume (6E); Tokyo morning in
   18% session-highs (6J); 6A bimodal US+Sydney; RBA ±5 phút = 9.0× volume;
   FOMC phút release 3.5× (NQ) / 17.2× (6E 6E-a4) / presser re-spike.
4. **Roll migration đo đủ**: ES gần-deterministic (T-5 bám 0-2 phiên, 66
   rolls); 6E crossover Thứ Sáu trước expiry-week; 6J/6A/6B OI dẫn volume
   1-3/2-3/5-7 ngày; ES same-trading-day (sau sửa timezone artifact).
5. **CoT-null trung thực ở 3/6 mã** (NQ/6B/6A phẳng), U-shape ở ES (+2pp cả
   hai cực), crowded-short → vol cao hơn ở 6E — driver positioning không
   phải chuyện đơn giản và không được coi là đã có edge.
6. **6J: siêu chu kỳ yen-yếu = 1 drawdown −46.7% chưa phục hồi**, chân
   zigzag chạm đúng ops MOF (10 ops trong-cửa-sổ sau khi sửa normalizer);
   BoJ window mỏng hơn 35% = execution floor cho strategy MPM-timed.

## Audit (đúng lệnh "spawn nhiều A7 audit từng cái")

7 auditor fresh-context riêng: NQ 0/3/3/4 · ES 0/1/3/5 · 6E 0/2/5/5 ·
6J 0/5/6/6 · 6B 0/0/7/5 · 6A 0/0/3/4 · INTEGRATION 0/2/3/2 — **0 BLOCKER
tổng**. Mọi headline số recompute khớp (13/13 NQ, ~36 6B, 40+ 6A, 12/12 6E…).
Toàn bộ findings được sửa bằng erratum công khai + delta verify:
**DOSSIERS 40/41 VERIFIED (1 PARTIAL do Lead sửa nốt sau đó), SOURCE 9/9
VERIFIED.** Retraction đáng chú ý: "venue-OI 2×" của 6E (thực ra trùng
publication rows; dedupe → 1:1 CFTC); "vendor hole NQ 2020" (thực ra alias
symbology, data có đủ 100%).

## Sự cố & xử lý

- **Cúp điện** giữa 2 lane fix → relaunch nối tiếp phần đã làm (không làm
  lại); lane nguồn còn bắt được bug thật của bản dở dang (DISAG precedence
  ngược) trước khi kịp gây hại.
- **Thư mục nonprice tạm rỗng giữa audit** (nguyên nhân không truy hồi);
  hiện 10,539/10,539 SHA sạch, tidy đúng bản fix, mirror đồng bộ.
- Suite nonprice: 41 → **59/59 PASS** (MOF + DISAG + pins mới).

## Còn chờ (không đổi)

Trước scored: đăng ký budget/freeze + GO; khai báo slippage + phí sàn 9/10;
lịch lễ thật; serial IBKR re-fetch (time-critical); pin signed-surprise NG
trước khi NG-H1 tính số; CIP-vintage sensitivity phải lượng hóa trước khi
đăng ký bất kỳ hypothesis H2 nào.
