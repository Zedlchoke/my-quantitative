# Owner note — bài học từ ERP1-TRACKA-COHORT-2 (2026-09-26)

**Trạng thái:** ghi chú bàn giao, không phải A7 terminal verdict hay bản ghi
`LESSONS.md`/`FAMILY_FAILURES.jsonl` chính thức. Cohort-2 vẫn là
`ACTIVE_LIGHT`, phase `GO-1 COMPLETE`, chờ A7 terminal và two-half close.
Không dùng ghi chú này làm GO-2, GO-3 hoặc GO mở cycle mới.

## Kết quả đã đo tại GO-1

- Slate rỗng: 7 đề xuất bị bác bỏ trước PnL; **0/18 scored cells, 0 holdout
  looks**. Registry ghi terminal condition `REJECT_ALL`, chưa flip `TERMINAL`.
- Holdout 2026-H1 AUDUSD/USDCAD còn sealed-unread. Không được dùng chúng để
  cứu một đề xuất đã chết.
- Nguồn: `plans/CYCLE_REGISTRY.json` (row `ERP1-TRACKA-COHORT-2`),
  `.worktrees/erp1-tracka-cohort-2/integration/research/control/
  ERP1-TRACKA-COHORT-2/freeze/GO1_freeze_artifact.json` và trial ledger.

## Sai lầm / falsification cần mang sang cohort sau

| Bài học | Bằng chứng cohort-2 | Luật cho cycle mới |
|---|---|---|
| Thêm gate/observable lên luật fade biên đã chết không tự tạo cơ chế mới. | C1 PROV-ABSORB, C2 RECLAIM-ABSORB, C3 PROBE-DEPLETION đều `VETO_VARIANT_SAME_FAMILY` tại F-0. | Mechanism-class court trước rho/PnL; bỏ observable mới mà còn cùng trigger-direction-exit/payer thì veto, không đổi tên rồi thử lại. |
| Cơ chế nghe hợp lý vẫn có thể không trả nổi hóa đơn giao dịch. | P4-A FIXCERT và P4-B QSKEW không qua F-5 declared-band; P4-B còn dưới base cost theo owner handoff. | Premium band và all-in cost authority phải được pin trước PnL. Không nới band sau khi thấy cost; chỉ tái nhập khi có bằng chứng kinh tế/venue mới độc lập, không phải tham số đẹp hơn. |
| Novelty và PIT sạch không đồng nghĩa có edge sau phí. | P3-A QCRD-H1 qua F-0, F-2 và F-1 (worst `|rho|` 0.0786/0.0883 trên 47 shadows) nhưng F-5 measured `CEILING_NEGATIVE_VETO`: crossing p50 AUDUSD 1.0 pip whole-dev, 0.9 pip last-6m ở base; ngưỡng cần ≤0.41 pip tại stress ×2.0. | Không score P3-A trên cost book hiện có. Chỉ xem xét lại nếu nguồn/venue hợp lệ chứng minh **toàn bộ chi phí có thể thực thi** dưới ngưỡng đã pin; không giả định maker/mid/no-slippage. |
| Đổi clock không cứu một họ momentum cũ. | P3-B DINV-1D chết F-1: `|rho|` 0.303/0.310 vượt bar 0.20. | So ancestry trên đúng frozen representation trước score; không re-clock, re-label hoặc đổi pair để né rho. |
| Kết quả âm trước PnL là tiết kiệm tài sản nghiên cứu. | 0 cells và 0 OOS looks; không có headline PnL để chọn winner. | Giữ trial ledger của cả 7 đề xuất, ghi cả các veto vào failure memory sau A7; tiếp tục chỉ từ thông tin/cơ chế mới có authority. |

## Ranh giới quyết định tiếp theo

1. A7 terminal độc lập xác nhận từng F-0/F-1/F-5, zero-PnL/zero-look,
   ledger/registry reconciliation; sau đó two-half close mới ghi chính thức
   vào `FAMILY_FAILURES.jsonl`, `MAP.md`, `LESSONS.md` và flip registry.
2. Trước khi lập cohort-3, kiểm điều kiện dừng của master plan §7: hai
   cohort liên tiếp `REJECT_ALL` không tự cấp quyền cho cohort thứ ba. Cần
   ít nhất một observable, nguồn dữ liệu/cost authority, hoặc cơ chế payer
   mới **có bằng chứng**, qua blind council. Nếu không có, báo
   `NO_CANDIDATE` hoặc `BLOCKED_*` thay vì lặp lại họ đã chết.
3. USDCHF và nguồn độc lập vẫn theo GO/source gate riêng; không đọc holdout,
   không thay worker/shadow, không tạo order từ ghi chú này.

**Primary evidence:** `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/
tracka_cohort2/SKEPTIC_F0_cohort2_REPORT.md`,
`SKEPTIC_F1_cohort2_REPORT.md`, `COSTAUDIT_F5_cohort2_REPORT.md`,
và worktree `falsifier/F5_ceiling_measured.json`.
