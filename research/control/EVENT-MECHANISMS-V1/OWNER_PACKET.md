# OWNER PACKET — EVENT-MECHANISMS-V1 (2026-09-27, stops at GO-scored gate by construction)

## One-line state

Cycle mở và chạy tới ranh giới gate đúng luật: **2 identity stocks được
đóng băng chờ falsification battery + implementation; 6/8 hướng chết/chặn
bằng bằng chứng đo; chưa có PnL nào, chưa tiêu cell nào (0/6), GO chưa
được tiêu — dừng ở đúng chỗ owner yêu cầu.**

## What ran (gates) — and what did not

| Gate | Verdict | Evidence |
|---|---|---|
| G0 intake | PASS | `INTAKE_2026-09-27.md` — HEAD/lock/workers/dirty-tree đo; registry DTP cũ được land (8d6fa365) với attribution; **quan sát: 0 process python — các shadow sleeve (PSV1, FX-RANGEFADE-2M, LIVE-DATA-GATEWAY) không chạy; ghi nhận, không đụng** (ngoài quyền cycle này) |
| G1 screening court (8 hướng × 8 trường + skeptic VETO) | PASS | `SCREENING_MATRIX.md` + `SKEPTIC_REPORT.md`; phán quyết tòa ở cuối SCREENING_MATRIX |
| G2 data authority (stocks priority) | PASS (probe-scale; điều kiện lane kèm theo) | `G2_DATA_GATE.md` + `data_gate/` (7 HTTP probes, sha-pinned) |
| G3 identity freeze (2 identity, ≤3 cap) | PASS | `G3_FREEZE.md` + `G3_FREEZE_ADDENDUM_r1.md` (band số theo A7 F-2) |
| A7 plan review | AUTHORIZED_WITH_FINDINGS (0 HIGH / 4 MEDIUM / 6 LOW; F-2/F-3 đã remediated) | `A7_PLAN_REVIEW.md` |
| G4 PIT battery / future-mutation / panel-truncation | **NOT_RUN** — implementation lanes chưa dispatch | dừng sạch ở ranh giới gate (§25); dispatch packets dưới đây |
| G5 independent implementation | **NOT_RUN** (như trên) | |
| G6 cost ceiling arithmetic | **NOT_RUN** (cost law đã freeze dạng PROXY-PRIOR; số đo do lane thực hiện từ band contract đã đóng băng) | |
| G7 A7 prelaunch | **NOT_RUN** | |
| Scored execution | **BLOCKED tại GO gate** — phrase `GO EVENT MECHANISMS V1 SCORED EXECUTION` REGISTERED_NOT_CONSUMED (P-8) | registry |
| Sealed OOS | gate riêng, sau này | |

## Screening outcome (8 hướng — đề xuất của bạn, đối chiếu provenance từng hướng)

| Hướng | Kết luận | Lý do một dòng |
|---|---|---|
| D1 stocks — EDGAR acceptance timestamp | **SỐNG → freeze** (EMV1-A1) | lớp thông tin mới thật (đồng hồ phút-phút; các event-form chết của NG6 đều theo ngày); điều kiện: staging cohort ở lane |
| D2 stocks — Form 4 | **SỐNG → freeze** (EMV1-A2, bỏ amendment arm) | payer/payload khác D1 (≥2/3 trục); rào ancestry SFNG1 (plan-cadence) vẽ đúng; amendment-lag chết y hệt SFNG2 — đo, không đoán lại |
| D3 stocks — corporate-action PIT | **data-plane GIỮ (N3/N4); event book BỊ VETO** | payer story sai cơ học (index split-invariant — không có forced flow); phần dư = các lớp reversal đã chết đo |
| D4 stocks — FTD × giá | CONTROL-PLANE-ONLY | luật posting-bound ≥17 ngày (P-26) giết mọi form PIT |
| D5 crypto — funding events | **VETO (ancestry identity)** | TRACKB1 rho 1.0000; FUNDJUMP; SRLV hai chiều; P-27/P-29 |
| D6 crypto — liquidation/forced-flow | **BLOCKED_DATA** | không có tape PIT nào trong authority (đo lại bởi skeptic); luật cấm suy từ nến |
| D7 crypto — basis/carry | **VETO (plane đóng)** | điều kiện mở lại của TRACKB không đạt (trục PIT phi-funding = D6, chính nó bị chặn) |
| D8 FX — after-cost events | **KHÔNG SCORE** | release-clock chết hai track; sàn chi phí ERP1 3.6/4.4 pips; lệnh cấm score FX của bạn hôm nay |

Ghi trung thực về "tám hướng": enumerate gốc của bạn không nằm trong repo;
8 hướng được dựng lại từ văn bản chỉ đạo của bạn (D1–D3 nguyên văn hôm nay)
+ plan_at.md (DRAFT 2026-09-25, chưa ghi nhận phê duyệt — erratum E-P1) +
DATA-FOUNDATION frontier. **Bạn có thể thay hướng nào trước khi lane G4
dispatch — screening chạy lại rẻ (tòa giấy).**

## Decisions only you can make (không chặn phần việc đang chạy)

1. **D3 event-book veto — phê chuẩn hay override?** (A7 F-4). Veto dựa trên
   cơ học: quỹ chỉ số KHÔNG phải giao dịch ở ex-date split (trọng số
   split-invariant) nên không có forced flow cho các lớp được nêu; phần
   dữ liệu N3/N4 vẫn làm. Override = bạn nêu mechanism thay thế, cycle mở
   identity thứ ba theo đúng luật F-0.
2. **GA-1 mở mạng www.sec.gov** (một fix cũng mở Dukascopy + CME) — KHÔNG
   cần cho identity hiện tại; chỉ cần nếu muốn fetch lại raw XML/FTD.
3. **GA-4 quyết định vendor liquidation crypto** (R4/O2) — D6 mãi mãi
   BLOCKED_DATA nếu không; class giữ trạng thái UNDETERMINED trung thực.
4. (Tùy chọn) **GA-2 dữ liệu chi phí giao dịch equities thật** — nâng cấp
   cost plane 0/10-measured; không cần cho S0 falsification-first.
5. (Ghi nhận, không phải quyết cycle này) **shadow sleeves đang dừng** —
   xem `DASHBOARD-AND-SHADOW-RELIABILITY-V1/` + incident PSV1 của phiên
   khác; tôi không đụng theo chỉ thị.

## Next authorized path (sau packet này)

Dispatch 3 lanes trong worktree `.worktrees/event-mechanisms-v1/`:
(a) data lane: P-13 restore substrate + eod_cache re-pin (N9) + N4 dated
identity map + cohort acceptance staging (C1–C5, không cần owner);
(b) implementation lane: G4 battery + engine theo G3_FREEZE (đóng băng,
một vòng sửa trước freeze đã dùng ở mức plan);
(c) independent lane: G5 re-implementation từ spec; rồi G6 số đo ceiling,
G7 A7 prelaunch — và packet thứ hai nêu **chính xác cell nào đủ điều kiện**
để bạn gõ GO phrase tại gate của cycle. Sau GO (nếu có): walk-forward ≤6
cell ghi cả thất bại, so baseline/controls, stress phí 1.5×/2.0× — rồi
dừng ở gate sealed OOS riêng. Nếu battery giết cả hai identity:
`NO_ELIGIBLE_PROPOSAL` đóng cùng bằng chứng (kết quả hợp lệ theo luật).

## Handover checklist (owner directive)

plan ✓ (`plans/PLAN_event_mechanisms_v1.md`) · data-gap/owner-action matrix
✓ (`DATA_GAP_OWNER_ACTION_MATRIX.md`) · veto list + lý do ✓ (bảng trên +
`SCREENING_MATRIX.md` court table) · trial ledger append-only ✓
(`TRIAL_LEDGER.jsonl`, 0/6, tạo TRƯỚC khi xem PnL — chưa có PnL nào) · A7
report ✓ (`A7_PLAN_REVIEW.md`, AUTHORIZED_WITH_FINDINGS) · GO/OOS status ✓
(GO REGISTERED_NOT_CONSUMED; OOS gate riêng chưa tồn tại) · khuyến nghị ✓
(bên dưới).

## Khuyến nghị của Lead

**Tiếp tục đúng trình tự đã đăng ký**: phê chuẩn packet này (hoặc sửa hướng
D5–D8 trước dispatch), để cycle chạy 3 lanes → A7 prelaunch → packet cell
điều kiện → GO của bạn. Không có cơ chế nào được score trước gate; không có
strategy "có lời" nào được claim ở bất kỳ đâu trong cycle này.
