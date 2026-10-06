# OWNER_DECISION_PACKET_P5_V2 — bản tiếng Việt dễ hiểu, có khuyến nghị (wave-3)

- Supersede-by-reference OWNER_DECISION_PACKET_P5.md (v1 giữ nguyên làm bằng chứng;
  namespace map v1 §0 vẫn là luật). **Không có gì ở đây được tự phê.** Khuyến nghị
  (K/N) chỉ là lời khuyên của controller dựa bằng chứng đã verify; mọi slot trống
  till owner ký. 0 scored/PnL tồn tại.
- Phân loại: **A** làm ngay được (đã hết), **B** owner quyết (bảng dưới),
  **C** registration/A7/dry-run/GO/scored sau B.

## 1. Hai phát hiện mới của wave-3 cần owner định đo thái (mới sinh từ bằng chứng)

**P5-NEW-1 — FX-F5: ngưỡng chứng cứ phụ thuộc vintage.** Đo lại cho thấy tương
quan differential-vs-roll r = +0.9097 nếu dùng số liệu MỚI NHẤT (latest-vintage),
nhưng chỉ −0.1068 nếu dùng số liệu BIẾT ĐƯỢC TẠI THỜI ĐIỂM RA QUYẾT ĐỊNH
(vintage-as-of) — luật PIT của chương trình buộc dùng vế sau. Nghĩa là ngưỡng
0.20 hiện **KHÔNG ĐẠT** dưới luật PIT, trừ khi owner xử lý khác.
- K/N: lấy vintage-as-of làm luật đọc chuẩn (fail-closed); FX-F5 giữ NEEDS_EVIDENCE
  cho đến khi có bộ DFF vintage-as-of (liên quan P5-NEW-3). Alternative: owner
  chấp nhận latest-vintage làm proxy và ghi rõ hạn chế (không khuyến nghị — vi
  phạm luật vintage đang đứng).
- Tác động: data (cần acquisition vintage), family FX-F5 (0 ID mới), kết luận
  (bar chưa qua — không family nào chết, chỉ chưa đủ chứng cứ).

**P5-NEW-2 — FX-F4: chết về mặt công suất dưới thang M2c đã chỉnh.** r = RT/MDE
= 15.2–26.5 (6E) / 20.2–35.8 (6B) — chi phí lớn gấp 15–36 lần mức phát hiện được;
p95 gap 3.10/4.40bp nằm dưới sàn RT 3.6/6.3bp.
- K/N: ghi nhận FX-F4 là POWER-DEAD tại n khả thi (loại khỏi mọi slate FX tương
  lai; vẫn PB2 nên không gì chạy). Alternative: owner giữ F4 chờ thang chi phí
  mới (không khuyến nghị — số học đã fail-closed).
- Tác động: FX-B/FX-C composition nếu owner ký sau này (bảng 26-ID/6A không đổi).

**P5-NEW-3 — AF2 (6A): không có DFF vintage-as-of nào tồn tại (0/16 rolls có
số liệu).** Machinery đã sẵn (fixture-proven); chỉ thiếu dữ liệu — là acquisition
thuộc owner (kiểu P5-HYPO-OD3).
- K/N: nếu owner muốn giữ AF2 sống trong contingency 6A, phê acquisition DFF
  vintage; nếu không, ghi AF2 = NEEDS_EVIDENCE vĩnh viễn đến khi có dữ liệu.
- Tác động: 6A contingency (bảng 26 ID giữ nguyên — AF2 không nằm trong 26).

**P5-NEW-4 — 4 ô session-mask FX "rth 07:20-14:00" không có bằng chứng trong
tree.** CONTRACTS xác nhận zero evidence (grep: chỉ xuất hiện trong chính file
contracts). Law-of-record FX là template Globex 17:00→16:00 CT.
- K/N: hoặc owner phê "Globex-template = luật phiên FX" (một dòng), hoặc cấp
  nguồn chính thức cho khung RTH FX; tới lúc đó 4 ô giữ PENDING fail-closed
  (không chặn gì hiện tại — mọi đường chạy thật đã refuse trước đó).

## 2. Các quyết định chính (giữ từ v1, giờ kèm K/N và phần đã triển khai để review)

| ID | Câu hỏi (tiếng Việt đơn giản) | K/N của controller | Đã triển khai để review | Chỉ chạy được sau khi phê |
|---|---|---|---|---|
| **ADOPT-D9** (P5-NQ1) | Chốt cache_v3 là chuỗi NQ chính thức + luật cease-guard? | **K/N: Option A** — bằng chứng kín: 66 rolls, 0 vi phạm cease-guard trên v3, re-hash 10/10 byte-exact, v2 đã deprecated, harness rebuild sẵn sàng | meas_nq/m2 harness (39/39 + refusal demo); freeze_builder GATE-0 | Freeze thật NQ; rebuild F3 thật |
| **Trần NQ** (P5-NQ2) | Chọn 22/29/36 ID + cách đếm clock-shadow (a)/(b)? | **K/N: NQ-B 29 + reading (a)** — phủ 2 family điểm cao nhất (F1/F2 = 11/11) + F3 (tiền điều kiện rebuild đã có harness); NQ-C 36 chỉ thêm F4 vốn machinery-only; NQ-D 43 không có đường lawful (EXPWITCH chết) | adapt_nq/IDENTITY enumeration 36 ID draft; adapter NQ-A/B/C bind_option có sẵn | Registration NQ |
| **D3 basis** (P5-NQ3 + P5-FXEB-OD6/OD7 + P5-CALC-FEE-E14) | Phí regulatory: A 2.25/side (timeline NFA chính thức) hay B 2.24/side (offset IBKR ghi nhận được)? Chênh nhau $0.02/RT. | **K/N: Variant A** (cơ quan quản lý, single-source, bảo thủ); B hợp lệ nếu owner muốn khớp tài khoản IBKR — cả hai đã量化, delta không đổi verdict nào đã biết | Cost contracts NQ/6E/6B/6J/6A dual-variant; adapter cost ladders refuse khi chưa chọn | Freeze cost; mọi cost gate |
| **PB2** (P5-FXEB-OD1) | Mở chương trình 6E/6B? | Không đề nghị chủ động (của riêng owner). Bằng chứng hai chiều mới: F4 chết (P5-NEW-2), 6B MDE 4.2bp < sàn chi phí 6.3–11.2bp (chân yếu nhất); F2/F3 vẫn điểm cao nhất FX | adapt_fx_eb/ toàn bộ PROPOSED machinery + 86/86 | Mọi scored 6E/6B |
| **Trần FX** (P5-FXEB-OD2/OD3) | Nếu mở PB2: CONV-D 44/66/96 hay census-native? delay-slot nào? | **K/N nếu mở: FX-A 44 + CONV-D + {D0,D1B} + reading (a)**; FX-C cần thêm DC §1.3 (OD5) | IDENTITY_BUDGET_6E_6B phân rã đủ; FX-F4 nên loại theo P5-NEW-2 | Freeze 6E/6B |
| **Trần 6J** (P5-FXJA-D1) | J-A 29 / J-B 36 / J-C 33-40 + reading? | **K/N: J-A 29 + reading (a)** — JF1/JF3 đều PREP_ABLE; J-C cần DC §1.3 thêm | adapt_fx_ja/ J enumeration; adapter sẵn | Freeze 6J |
| **BBO/fill** (P5-FXJA-D3, P5-FXEB-OD8) | Giữ fill bảo thủ (next-bar open) hay tài trợ nghiên cứu BBO? | **K/N: giữ fill bảo thủ** (D5 đứng; mọi spec đã viết theo nó) | Runner conservative fill law + tests | Fill-sensitive gates |
| **Placebo** (P5-FXEB-OD4) | 1-seed mặc định hay mở rộng ≥100-seed? | **K/N: giữ 1-seed** (ES precedent; mở rộng ≥1.800 IDs chương trình) | Adapters implement single-seed law | Placebo layer |
| **EXPWITCH** (P5-NQ5/P5-HYPO-OD1) | Chấp nhận chết ở gate cho cả 2 chân? | **K/N: chấp nhận DEAD-AT-GATE** (điều kiện khai báo trước; không chỉnh sau) | expwitch_refusal.py never-convertible | (không mở lại trừ data-plane owner) |
| **6A bundle** (P5-FXJA-D5: PB3→D8→D9→fee→ABS/China) | Kích hoạt contingency 6A? | **K/N: giữ PB3 PARK** — không bằng chứng mới nghiêng về mở; mọi machinery contingency đã sẵn nếu mở | adapt_fx_ja/ AF1/AF3/AF4 + RMM-6A (era refusal, China-calendar refusal) | Mọi scored 6A |
| **BoJ stamps / ABS-China / JF2 threshold** (P5-HYPO-OD2/OD3/OD4) | Mua/thu thập gì, chốt hằng số nào? | K/N: không cần cho đường ngắn nhất (K3 đã anchor-insensitive; AF-family đang PARK); quyết khi bật 6A/J-C | Helpers always-refuse đúng luật | JF1 minute-anchor; AF3 K4; JF2 host |

## 3. Câu phê tối thiểu (nếu owner chỉ trả lời một lần)

> "D9 = Option A. Trần NQ = 29 (NQ-B), clock-shadow (a). D3 = A.
> Ghi nhận FX-F4 POWER-DEAD, FX-F5 bar theo vintage-as-of, AF2 chờ DFF vintage.
> 6E/6B/6J/6A: giữ nguyên PB2/PB3, chưa quyết trần."

— mỗi dòng một slot, không gì tự động; registration/GO vẫn là bước C riêng.

## 4. A/B/C sau wave-3

- **A (làm ngay được): HẾT.** WORK_QUEUE_V2 không còn mục A nào chưa đóng trong
  authority hiện hành (các PARTIAL-A đều đã làm tối đa phần được phép, phần còn
  lại phụ thuộc dữ liệu owner hoặc chữ ký).
- **B:** bảng §1–§2 (14 slot chính + 4 P5-NEW + các slot v1 chưa đổi).
- **C:** registration tại ROOT → prelaunch A7 → exact-arm dry-run → typed GO →
  scored dưới canonical lock → twin → terminal A7. Hạ tầng cho từng bước đã có
  (runner v2 + freeze_builder + wiring + CANONICAL_INTEGRATION sequence).

— Hết OWNER_DECISION_PACKET_P5_V2. Slots trống; không gì được tự phê.

## Erratum phụ (sau verify wave-3, append-only)
- NOTE-N1: phần §2 dòng PB2 trích "6B MDE 4.2bp" — số đúng theo artifact
  (meas_fx + FXEB K6 gates) là **4.31bp** (làm tròn sai, không đổi verdict:
  4.31bp vẫn dưới sàn chi phí 6.3–11.2bp). (Nguồn: verify/wave3/verify_findings_wave3.json)
- 5 MINOR của verify wave-3 đều là vệ sinh metadata handoff (không đụng evidence):
  đã ghi nhận; các round sau kế thừa chuẩn schema tốt hơn (3/7 conformant,
  cải thiện từ 0/7).

## WAVE-4 bổ sung (bằng chứng mới cho các slot cũ — không slot mới)
- Lỗi mixed-direction wiring đã đóng (FAIL record f1f69c8e → fix c12e6a5a, repro
  PASS): claim "19 adapter wired" nay đúng ở mức intent-execution semantics
  (timeline/folds/fill/exit giữ theo SPEC, test T-MD1..10). Không thay đổi
  khuyến nghị nào của §2.
- Canonical integration giờ là CODE đã test (14/14) — khi owner phê đăng ký
  cycle, 2 authorization mở phần NOT_RUN: (I) flip PREP_BUILD + row ACTIVE_HEAVY,
  (II) typed GO_RECORDED.json đúng mẫu. Câu phê tối thiểu §3 không đổi.
