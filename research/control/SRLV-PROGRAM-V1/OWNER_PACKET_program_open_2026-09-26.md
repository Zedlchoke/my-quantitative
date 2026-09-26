# OWNER_PACKET — SRLV-PROGRAM-V1 — mở chương trình & các quyết định chờ owner

- Ngày: 2026-09-26. Người viết: Lead (phiên survey + planning theo owner
  instruction ngày 2026-09-26). Packet này KHÔNG PHẢI GO; không thay thế
  GO-1/GO-2/GO-3; không tiêu phrase nào.

## 0. GO RECORD

- **GO-2 SRLV-CX-C1 — CONSUMED.** Owner gõ đúng nguyên văn
  `GO SRLV CX C1 SCORED EXECUTION` (2026-09-26, ngay sau GO-1 complete:
  freeze M1 SETTLE-RESOLVE 6 cells, sha-pinned, 0 PnL). Phạm vi: A7
  prelaunch → triển khai engine + fixtures (F1–F7 + per-mech) → exact-arm
  dry-run → scored walk-forward 6 cells × 2 pairs (BTCUSDT/ETHUSDT) dưới
  heavy lock, gates G1–G8 + margins, dual cost book, DSR/PBO accounting,
  trial ledger + outcomes. KHÔNG gồm: GO-3 sealed/prospective OOS, mở S1,
  shadow promotion, bất kỳ hành động FX.
- **GO-1 SRLV-CX-C1 — CONSUMED.** Owner gõ đúng nguyên văn
  `GO SRLV CX C1 COUNCIL AND FREEZE` (phản hồi trực tiếp trong phiên Lead
  2026-09-26, ngay sau A7 audit PASS_WITH_FINDINGS và revision theo chỉ thị
  owner). Phạm vi mở: register child SRLV-CX-C1 qua researchctl + worktree
  riêng + Phase C0→C3 (control plane, data plane, exposure verify, council
  outcome-blind, falsifiers, trial freeze) — RỒI DỪNG chờ GO-2. KHÔNG gồm:
  GO-2 scored execution, GO-3 sealed OOS, đăng ký/điểm nhấn gì ở track FX
  (FX giữ NO_CANDIDATE tới khi có reopener thực), shadow/worker, orders.
  GO-1 FX (`GO SRLV FX C1 COUNCIL AND FREEZE`) vẫn CHƯA gõ — phrase đó chỉ
  có hiệu lực khi master §6 reopener có bằng chứng bytes (P-8).

## 1. Đã khảo sát (Bước 0, bằng chứng đo được)

- Root checkout `main` @ `e4e3b915` lúc survey (A7 đo lại ở audit: HEAD đã
  tiến tới `75d5f72a` do commit của lane khác ngoài SRLV); dirty tree = toàn
  owner paths + draft plans (giữ nguyên, không stage); heavy lock lúc survey
  `FREE_PROVEN`, lúc A7 audit `HELD_PROVEN` bởi ERP1-TRACKB-COHORT-1 (worker
  ngoại hợp lệ, SRLV không giữ/chờ); registry: 71 cycle rows, 9 ACTIVE_LIGHT
  (đo bởi A7 2026-09-26; con số theo registry tại thời điểm đo).
- Đọc: CLAUDE.md, handbook (headings + luật qua ERP plans), MAP.md, LESSONS.md
  (đầy đủ qua lane Explore), FAMILY_FAILURES.jsonl (134 entries), charter
  ERP-FOREX-PROGRAM-V1, ERP-TRACKB-PROGRAM-V1, VIABILITY_cohort3_REPORT,
  OWNER_NOTE_cohort2_lessons, R1 probe verdict.
- **Holdout Forex 2026-H1 (AUDUSD/USDCAD): KHÔNG ĐỌC** — chỉ liệt kê
  manifest/filename. Seal giữ nguyên.

## 2. Bàn giao (5 file mới, chưa commit — chờ owner duyệt)

| File | Nội dung |
|---|---|
| `plans/PLAN_srlv_program_v1.md` | Master plan: 2 track tách biệt, ≤3 cơ chế/cohort, cap 96 scored cells, kill rules K-F0…K-OOS, stop conditions, GO phrases |
| `plans/PLAN_srlv_fx_cohort_1.md` | Child FX: Phase D0 frontier gate (R1–R5) → D1 per-pair gate → D2 council+freeze → D3 scored → D4 sealed OOS → D5 A7 |
| `plans/PLAN_srlv_cx_cohort_1.md` | Child CX: C0 collision → C1 data plane → C2 exposure verify → C3 council+freeze → C4 scored → C5 sealed/prospective → C6 A7 |
| `research/control/SRLV-PROGRAM-V1/OUTCOME_EXPOSURE_MAP.md` | Bản đồ cặp × nguồn × thời gian + sealed assets + ancestry fences |
| `research/control/SRLV-PROGRAM-V1/DATACOST_FEASIBILITY_MATRIX.md` | Per-pair D/L/PIT/C/P + verdict + thành phần cost bắt buộc |

## 3. Phát hiện trọng yếu ảnh hưởng quyết định

1. **Forex frontier ĐÓNG thật sự trên dữ liệu hiện có**: 12 dead classes
   (VIABILITY) phủ hầu hết không gian S/R–sweep–vol naïve; 3/6 cặp
   outcome-exposed trọn window, 2/6 dev-exposed (range-fade class), USDCHF
   0 bytes. Chạy scoring trên panel cũ = tái chạy không gian đã đóng. Do đó
   SRLV-FX-C1 có **Phase D0 bắt buộc**: một reopener (R1/R2/R3/R5) với bằng
   chứng bytes, không có ⇒ `BLOCKED_FRONTIER_NOT_REOPENED`.
2. **Chi phí là lỗi giết chính**: conditional crossing đo 0.9–1.2 pips
   (AUD/CA), stressed RT 3.6/4.4 pips; ngưỡng pin P3-A ≤0.41 pip @k=2.0 còn
   nguyên. Lưu ý lớp bằng chứng: minTick 0.5 pip (IBKR, 5 cặp) chỉ là fact
   hình học tick — KHÔNG suy ra được executable spread/all-in; executable
   spread đang NOT_SUBSCRIBED, commission NOT_RUN ⇒ all-in thực sự CHƯA ĐO;
   R1 sẽ đo, kết quả có thể cao hơn hoặc thấp hơn. Cơ chế FX intraday cần
   band premium rõi ~7–9 pips để non-fragile — council phải trả lời được
   trước scoring.
3. **Crypto mở được nhưng phải trung thực về proxy**: không có order-book/
   liquidation/OI lịch sử ⇒ sweep/zone = `PROXY_NOT_ORDERBOOK`; payer story
   phải nổi fictional-counterparty veto. Funding measured (BTC 11.798%/yr)
   bắt buộc; G5 concentration 0.50 đo structurally unpassable cho BTC-long
   2020–2026 ⇒ long-biased cơ chế phải short-capable hoặc kết luận chỉ trên
   prospective.
4. **OOS thật còn rất ít**: FX chỉ còn AUDUSD/USDCAD 2026-H1 (sealed, một
   look cấp chương trình); crypto history gần hết exposed ⇒ kỳ vọng OOS thật
   của CX là prospective accumulation sau freeze.
5. **Va chạm cycle sống**: ETHUSDT-OPEN-SEARCH-V2 (chờ GO), CHR3F (đang
   scored, heavy lock), FX-RANGEFADE-2M-SHADOW-V1, PSV1 sleeves — kế hoạch
   đã đặt luật không xâm phạm.

## 4. Quyết định chờ owner (theo thứ tự)

| # | Quyết định | Hệ quả |
|---|---|---|
| **Q1** | Phê chuẩn charter SRLV-PROGRAM-V1 + 2 child draft (ghi quyết định vào packet này). Sau phê chuẩn: Lead commit drafts + đăng ký child cycles qua researchctl khi gate tương ứng mở | Không phê chuẩn ⇒ chương trình không mở, các file ở dạng draft |
| **Q2 (chọn ≥1 hoặc giữ nguyên)** | **R2** — nguồn bid/ask độc lập: đăng ký TrueFX (free) / OANDA v20 practice / xin Dukascopy written consent — owner-only (đăng ký/tài khoản) | Mở SRLV-FX-C1 Phase D0→D2 (council được phép trên observable mới; nguồn thứ hai cho cost authority) |
| | **R1** — IBKR: two-sided market data subscription + Flex statement (commission + overnight interest) | Commission/swap measured; all-in được ĐO — có thể xác nhận cao hơn hoặc thấp hơn ước tính hiện tại; cơ chế chết F-5 chỉ xét lại bằng số đo |
| | **R3** — financing band broker-grade | Mở class multi-day hold (đang BLOCKED F4) |
| | **Không chọn cái nào** | SRLV-FX-C1 đóng `BLOCKED_FRONTIER_NOT_REOPENED` (first-class close); track FX nghỉ tới khi owner mở |
| **Q3** | Duyệt mở **GO-1 SRLV-CX-C1** (`GO SRLV CX C1 COUNCIL AND FREEZE`) sau khi duyệt child plan — crypto không bị chặn frontier | CX chạy C0→C3 rồi DỪNG chờ GO-2 |
| **Q4** | (Sau này) mọi GO-2/GO-3 gõ đúng phrase tại đúng gate theo master §13 | GO gõ trước gate = intent chết (P-8) |

## 5. Cam kết vận hành (đã ghi trong plans)

- Không đặt lệnh, không sửa shadow/dashboard, không push/merge, không mở
  sealed OOS, không kill worker ngoại, heavy lock tôn trọng, mọi lane có
  dispatch packet + worktree đúng registry + handoff `zcode_orch_v3_handoff@1`.
- Trial ledger ghi mọi outcome-viewed trial; DSR mọi terminal; PBO ≥8 configs;
  REJECT_ALL/NO_CANDIDATE là kết quả hợp lệ; dừng đúng stop conditions —
  không chạy vô hạn để ép winner.
