# OWNER DECISION PACKET — BTC4H-BANDRIDGE: luật sizing dưới chi phí & luật mốc fill

- Soạn: 2026-09-24, nhiệm vụ DASHBOARD-AND-SHADOW-RELIABILITY-V1 (G3).
- Tính chất: **CÂU HỎI LUẬT IDENTITY** — bên viết code KHÔNG tự quyết.
  Cho tới khi owner chọn, executor giữ nguyên hành vi fail-closed hiện
  hành (đã pin bằng regression test, commit 12540ebe).
- Bằng chứng gốc: ledger `results/prospective_shadow_v1/ledgers/BTC4H-BANDRIDGE.jsonl`
  — mọi quyết định H4 từ khi mount: `target_weights {BTCUSDT: 1.0}`,
  `accounting_status UNAVAILABLE_FAIL_CLOSED`, `virtual_fill_events []`,
  cash 100,000 đứng yên. Regression: `tests/test_shv1_executor.py::
  test_weight_1_0_single_leg_long_fails_closed_with_zero_fills` (hành vi
  hiện hành) và `::test_weight_1_0_refusal_is_cost_headroom_not_sizing_qty`
  (chứng minh nguyên nhân).

## Câu hỏi 1 — Sizing: trọng số 1.0 không thể fill được dưới chi phí dương

Cơ chế đo được (không phải suy đoán): sizing dùng giá ref
(`qty = w*equity/ref`), còn guard tiền mặt phía buy yêu cầu
`qty*fill_price + fee ≤ cash`, với `fill_price = ref + 1 tick` (buy trả
giá xấu hơn) và `fee = 0.05%` (book CURRENT_CONSERVATIVE_COST). Với
w=1.0: cần ≈ **100,050.02 USDT** cho 100,000 cash → `InsufficientCashError`
→ toàn bộ rebalance hủy TRƯỚC khi mutate → 0 fill, event ghi đúng trạng
thái fail-closed. Đây cùng họ lỗi với finding gross-1.0 tail-short của
ILLIQ (handoff_shv1-e-worker, phần phía shorts đã được remediate bằng
SIZING_AND_CAP_BASIS; phía buy chưa từng có remediation tương ứng).

| Lựa chọn | Ý nghĩa | Hệ quả |
|---|---|---|
| A. Giữ fail-closed (hiện trạng) | BANDRIDGE không bao giờ vào vị thế; sleeve = $100k đứng yên vĩnh viễn | Trung thực, không đổi gì; nhưng sleeve mất toàn bộ giá trị thông tin prospective |
| B. **Cost-aware sizing (khuyến nghị)** | Executor size qty theo khoản affordability: `qty = min(w*equity/ref, cash/(fill_price*(1+fee)))` → realized weight ≈ **0.99946** thay vì 1.0 | Vị thế thật gần target; `realized_weights` ghi cạnh `target_weights` từng event; chênh lệch bị chặn trên bởi cost book (≤ ~$50/100k/lần vào); CẦN amendment ghi rõ vào identity manifest |
| C. Tolerance trên guard tiền mặt | Cho `needed ≤ cash*(1+tol)` (vd tol 1e-3) → fill đủ 1.0, cash âm tạm ~$50 | Đổi ngữ nghĩa hạch toán (cho phép thấu chi vi mô); tương đương vay nội bộ — cần amendment mạnh hơn |

## Câu hỏi 2 — Mốc fill: docstring hứa "fill ở H4 open", executor fill ở bar 15m hoàn tất đầu tiên sau quyết định

Đã ghi nhận tại commit a8062b1a theo lệnh owner "recorded, not fixed".
BANDRIDGE chưa có fill nào nên chưa có gì vật chất hoá.

| Lựa chọn | Ý nghĩa |
|---|---|
| A. **Sửa doc cho khớp executor (khuyến nghị)** | Luật chính tắc = "fill tham chiếu bar 15m hoàn tất đầu tiên sau ranh giới H4" (forward-only, đúng đường thực thi đang chạy). Chỉ sửa tài liệu, không đụng code |
| B. Re-derive về H4-open | Đổi executor lấy giá OPEN của bar 15m đầu (== open của bar H4, hợp lệ forward-only tại 00:15) — là forward-only accounting amendment, phải preregister + test parity lại |

## Ràng buộc owner đã ra (2026-09-24, nhiệm vụ này)

Không tự hạ phí; không tăng vốn; không biến target 100% thành exposure
khác khi chưa có disclosure/quyền. Cả B lẫn C ở trên đều ĐỔI exposure
hoặc ngữ nghĩa hạch toán → đều cần chữ owner. Phương án A không cần gì
thêm.

Quyết định của owner: ________ (A/B/C cho câu 1; A/B cho câu 2)
