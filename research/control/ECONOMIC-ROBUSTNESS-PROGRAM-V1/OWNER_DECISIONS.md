# OWNER_DECISIONS.md — ECONOMIC-ROBUSTNESS-PROGRAM-V1

Phiên draft 2026-09-25 (A1) · cập nhật phiên owner 2 (2026-09-25, quyết
định D1–D10) · cập nhật phiên 3 (sau A7 fresh r3: khôi phục phần bối cảnh
bị truncate — incident ghi tại §Incident).

## 1. Bảng quyết định owner (hiện hành)

| # | Quyết định (verbatim intent của owner) | Trạng thái thi hành |
|---|---|---|
| D1 | CHẤP THUẬN CÓ ĐIỀU KIỆN: đăng ký umbrella ACTIVE_LIGHT budget 0/0 bằng researchctl — **chỉ khi A7 fresh-context mới kết luận tất cả gate G1–G7 PASS**; không kế thừa verdict cũ; còn FAIL/BLOCKED/NOT_RUN thì không đăng ký, báo blocker | **DONE 2026-09-25T03:12:56Z**: A7 r3+r3b G1–G7 ALL PASS (PASS_WITH_FINDINGS 0H/0M/6L advisory) → registered; row verified ACTIVE_LIGHT 0/0 phase REGISTERED, S1 SEALED_UNTOUCHED, go_phrase none, workers 0, projection regenerated (registry sha256 0792e436…); `--asset shared` accepted by CLI (A7 F9 LOW resolved) |
| D2 | CHẤP THUẬN mức LẬP KẾ HOẠCH: amendment FX RANGEFADE (short-beta control + aggregate USD exposure + event-time stress-spread + trường fee/slippage); tham số & hành vi giao dịch giữ nguyên; review độc lập rồi DỪNG ở gate GO riêng | draft + review xong; chờ GO |
| D3 | DUYỆT LÀM NGAY phần chốt luật, trước fill đầu: sizing B + fill law A + GIỮ 6 bps/side trong identity; executor hash-matched trước khi fill có giá trị đánh giá; không hai cost law cùng tồn tại | amendment draft xong (đã remediate scoping theo review); chờ GO |
| D4 | CHO LẬP KẾ HOẠCH retire identity XSECT: giữ toàn bộ lịch sử; chốt timestamp dừng mở vị thế bằng amendment riêng; KHÔNG tắt worker từ quyết định này | amendment draft xong (đã remediate fixture); chờ GO |
| D5 | DUYỆT mốc D13 ILLIQ — chỉ phát hiện giả thuyết SAI / quyết định quan sát tiếp; 13 tuần KHÔNG phải bằng chứng promote | có hiệu lực khi umbrella đăng ký (C-IL-1) |
| D6 | GIỮ quan sát BASISLV, không promote; bắt buộc báo riêng price-only P&L | có hiệu lực khi umbrella đăng ký (C-BL-1..3) |
| D7 | DUYỆT thứ tự child (plan §10); từng child vẫn cần GO riêng | đứng sau các amendment đo lường |
| D8 | CHƯA duyệt gateway cutover — cần acceptance + rollback của cycle gateway riêng | không hành động |
| D9 | CHẤP THUẬN historical có ghi nhận — chỉ lỗi đã xác minh thuộc cycle TERMINAL cũ; lỗi mới hoặc lỗi ảnh hưởng child hiện tại vẫn chặn | P0-3 plan; A7 r3 measured 15 HIGH = 14 pause-packet + 1 LOCK_OWNER_DEAD (mới, thuộc stale-lock class bên dưới) |
| D10 | Display-only cho portfolio caps — chưa đặt cap số, chưa đổi hành vi giao dịch | plan §5.15 đúng hiện trạng |

## 2. Pending-decision register (quyết định owner còn thiếu — A7 r3 F2)

| # | Quyết định | GO phrase (draft, gõ đúng nguyên văn tại gate riêng) |
|---|---|---|
| P-G1 | GO amendment FX controls (D2) | `GO FX RANGEFADE AMENDMENT A1 CONTROLS MOUNT` |
| P-G2 | GO amendment BANDRIDGE pins (D3) | `GO PSCTV1 AMENDMENT A2 BANDRIDGE PINS` |
| P-G3 | GO amendment XSECT retire (D4) | `GO PSCTV1 AMENDMENT A3 XSECT RETIRE` |
| P-H1 | Registry/plan commit hygiene: sau khi D1 đăng ký, tree mang các file untracked mới (plan + 3 draft + namespace) và registry được ghi bởi researchctl; theo P-10 không để registry dirty kéo dài — owner cấp commit hygiene riêng (agent bị cấm commit theo chỉ thị gốc, chưa được tái cấp) | (không GO phrase — lệnh commit thường) |
| P-H2 | Stale heavy-lock row: RUNNING row pid dead (43712 → 45083 class) của CRYPTO-HISTORICAL-REPLICATION-3F-V1 — CONTROL_STATE_DRIFT; reclaim thuộc control-plane owner / Lead phiên CHR3F theo round-2 discipline, không thuộc umbrella | (không GO phrase) |
| P-H3 | Các child cycle Track A/B/C (plan §10 mục 5–8) — mở từng cái theo D7, mỗi child plan + A7 + GO riêng | (từng child tự đăng ký phrase) |

## 3. Bối cảnh lịch sử D1–D10 (khôi phục sau incident truncate)

- **D1** — Register umbrella: lý do registry là authority duy nhất; chỉ thị
  gốc cấm agent tự đăng ký nếu sinh quyền execution — owner đã duyệt có
  điều kiện ở phiên 2. Command đề xuất (đã đối chiếu `researchctl cycle
  register --help`; `--asset shared` theo tiền lệ SHADOW-PAPER-REVIEW-V1;
  branch/worktree rỗng khi planned):
  ```
  .venv/bin/python research/researchctl.py cycle register \
    --cycle ECONOMIC-ROBUSTNESS-PROGRAM-V1 \
    --asset shared \
    --plan plans/PLAN_economic_robustness_program_v1.md \
    --branch "" --worktree "" \
    --budget-max 0 --lifecycle ACTIVE_LIGHT \
    --reason "Owner D1 2026-09-25 conditional on A7 fresh r3/r3b all-gates PASS"
  ```
- **D2** — FX controls: không quyết thì mọi PnL FX prospective mang nhãn
  `SHORT_BETA_UNSEPARATED — NOT PROMOTABLE`.
- **D3** — BANDRIDGE pins: nếu không pin trước quyết định H4 fillable đầu
  tiên, fill đó bị gắn `UNPINNED_COST_LAW — NOT PROMOTABLE` vĩnh viễn.
  Owner chọn: sizing B, fill law A, giữ 6 bps/side trong identity.
- **D4** — XSECT retire: số liệu 77:1 cost:carry (2026-09-25 bytes);
  worker không tắt từ quyết định — timestamp `T_ret` chốt tại GO.
- **D5** — ILLIQ D13: 13 valid weekly decisions từ 2026-09-21 → interim
  ~2026-12; luật tại plan §4.4 C-IL-1.
- **D6** — BASISLV: skeptic flag tension (cùng premium với identity đang
  retire; dưới power 52 tuần) — owner xác nhận keep có chủ đích.
- **D7** — Thứ tự: đo lường sleeve hiện tại trước, ngân sách nghiên cứu sau.
- **D8** — Gateway: LIVE-DATA-GATEWAY-V1 sạch 24h nhưng chưa cutover.
- **D9** — Doctor HIGH: 14 pause-packet TERMINAL cũ chấp nhận-historical.
- **D10** — Caps: display-only.

## 4. Decisions NOT required (đã thuộc luật)

Floor evidence §5.14 (child tự power-analyze, chỉ được nâng); verdict
vocabulary §9; S1 one-shot §5.10; ancestry 0.20 bar §6.

## 5. Incident log (file này)

- **INC-OD-1 (2026-09-25, phiên 3)**: khi update bảng quyết định, A1 làm
  truncate file này còn 31 dòng (mất §3 bối cảnh lịch sử + command D1) —
  A7 fresh r3 bắt được như finding F1/G7-FAIL. Đã khôi phục nguyên nội dung
  + bổ sung pending-decision register (F2). Nguyên nhân: edit thay cả file
  bằng new_string kết thúc ở header mục D1. Phòng tránh: khi thay khối lớn,
  kết thúc new_string phải chứa lại toàn bộ phần đuôi còn giữ.
