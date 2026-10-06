# BÁO CÁO TIẾNG VIỆT — FUTURES-ES-PB1-V1 đã ĐĂNG KÝ + gates 2-4 xong, dừng trước GO (2026-10-04)

## Registration (owner ủy quyền tường minh "tôi uỷ quyền đăng ký cho bạn")
- Registry row: **FUTURES-ES-PB1-V1**, ACTIVE_LIGHT, **budget 0/24**, asset
  futures, branch `prep/futures-es-reg-20261004`, head đăng ký
  `e7fc1d8d`, worktree `.worktrees/futures-es-reg/prep`, go_phrase
  **`GO FUTURES-ES-PB1-V1 SCORED EXECUTION`** (REGISTERED_NOT_CONSUMED,
  không alias — mẫu cũ PLAN §6 đã supersede bằng authority đã audit).
- Plan hợp pháp tại ROOT: `plans/PLAN_futures_es_pb1_v1.md` (file mới,
  append-only; tham chiếu freeze authority e7fc1d8d + freeze_pins_v2 +
  erratum chain; giải xung đột chuỗi GO theo quy tắc F-A5 đã verify).
- Pre-write audit: 34/34 pin khớp tại e7fc1d8d; commit control-plane
  `7926aac2` (root) — chỉ thêm hàng của ta + metadata CAS; hàng NBA
  nguyên vẹn, file NBA của owner không đụng.

## Strategy PB1 là gì (trả lời câu hỏi owner)
**PB1 = cặp giả thuyết qua đêm (OVN pair) trên ES futures, họ M-A/M-B**:
đo phần biến động/thông tin của phiên giao dịch điện tử qua đêm
(Globex) rồi giao dịchcontinuediệu hướng vào phiên chính RTH. **M-A
(continuation)**: khi đuôi biến động OVN vượt ngưỡng q80 (tính strict-past,
không lookahead), phiên RTH tiếp tục theo hướng đó. **M-B (reversal)**:
cùng tín hiệu nhưng dự đoán đảo chiều. 8 identity mỗi tay (biến thể
đuôi/độ trễ), 4 biến thể FOMC (tín hiệu quanh ngày Fed), 4 controls
(C1 placebo seed khai báo, C2 always-on, C3 flat zero-trade =
sàn accounting, C4 dose-response) = **đúng 24 identity = trần ES đã
đóng băng**. Vào/ra theo luật fill bảo thủ (next-bar open, SL-priority),
chi phí Variant A $2.25/side fees (owner đã ký D3), gióng ×1.0/1.5/2.0.
Đây là hypothesis PHẢI BÁC BỎ trước hết: mọi identity chết nếu sau chi
phí không vượt controls/clock-only; kết quả âm cũng là kết quả hợp lệ.

## Bảng gate (trạng thái đúng luật)
| Gate | Verdict | Bằng chứng |
|---|---|---|
| 1 Registration | **PASS** (owner-được-ủy-quyền) | registry row + plan + commit 7926aac2 |
| 2 Exclude list + selection freeze | **PASS** | 1,278 phiên exclude (FOMC 131, holiday-fact 10, holiday-uncertain 60, coverage<60 69, warmup 1,008); mặt đánh giá 2,926; 34-pin manifest; commit a33978b7 |
| 3 Prelaunch A7 (key 1/2) | **AUTHORIZED_WITH_FINDINGS — 0 HIGH/CRITICAL** | 34/34 pins, 24/24 identity tự-trích byte-exact, chi phí exact, coverage rule bit-exact vs K6; 1 MEDIUM sustained LAWFUL (2011-16 holiday pending — 0 phơi nhiễm thực nghiệm); commit 42885faf |
| 4 Exact-arm dry-run | **PASS (a,b,c)** | 24/24 enumeration byte-exact; 20/20 cost recompute; determinism 2 pass byte-identical (index sha db728f5c…); MỌI số liệt kê trong quarantine/ (descriptive-only, 0 denominator, 0 scored cell); rehearsal tự bắt + sửa 1 defect warmup FOMCIN trước phán quyết; 3 ambiguity PIN trước scored (D-A1 q80 method, D-A2 C2 direction, D-A3 C1 RNG); commit 476f0a2 |
| 5 Typed owner GO (key 2/2) | **NOT_RUN — CHỦ SỞ HỮU** | không bao giờ được ủy quyền; dừng ở đây đúng luật |
| 6 Scored + twin + terminal A7 | **NOT_RUN** | chờ GO |

## Số scored thật: **0** (dry-run là rehearsal cách ly, không đếm)

## Ghi chú trung thực
- Registry head field giữ giá trị đăng ký e7fc1d8d; branch thực tế đã
  tiến tới 476f0a2 (gates 2-4). Việc `cycle update --head` bị hoãn có
  chủ đích: root đang có NBA work-in-progress chưa commit của owner
  trong chính các file control-plane dùng chung — chạy update lúc này
  sẽ gộp thay đổi của owner vào commit của ta. Sync khi tree owner yên
  (reconcile chuẩn, không việc của gate).
- 3 pin D-A1/2/3 + nghĩa vụ 2011-16 holiday là các điểm owner/người
  đóng băng phải chốt trước scored (đều đã ghi record, không có gì âm
  thầm).

— Hết REPORT_VI của cycle (dừng đúng gate GO).
