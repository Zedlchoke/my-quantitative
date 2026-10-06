# ERRATUM 1 — thu hẹp claim "mọi việc PREP được phép và không phụ thuộc owner đã hoàn tất cho cả năm mã"

- Round: FUTURES-5SYM-PRESCORED-20261005. Append-only; không sửa file cũ,
  không rút giá trị bằng chứng/th test đã đạt.
- Ngữ cảnh: báo cáo kết thúc wave-2 (synth/REPORT_VI.md, commit `0732f22e`)
  kết luận round đã xong toàn bộ PREP không phụ thuộc owner. Chủ sở hữu audit
  lại tại đúng `0732f22e` và chỉ ra phạm vi thực tế hẹp hơn.

## Claim bị thu hẹp

Câu "mọi việc PREP được phép và không phụ thuộc owner đã hoàn tất cho cả năm
mã" chỉ đúng trong phạm vi **gói packet-dossier + hạ tầng accounting sandbox**
mà round đó giao: readiness matrix, SPEC/budget/cost/calendar draft từng mã,
census + ancestry, runner v2 (accounting/finalization/lock-lifecycle sandbox)
và các phép đóng lịch. Nó KHÔNG bao gồm:

1. **Mục A còn mở trong WORK_QUEUE.md** (chính round đó tự liệt kê): đối
   chứng số hợp đồng runner (EXEC placeholders), FX-F5 CIP-vintage, FX-F6
   transfer, AF2 vintage-flip, NQ session-σ trên cache_v3, FX-F4 RT/MDE theo
   erratum M2c, machinery trigger-time anatomy, harness NQ-F3 rebuild.
   Liệt kê trong queue ≠ đã làm.
2. **Implementation từng family**: runner v2 hiện là hạ tầng accounting trên
   sandbox; evaluator của nó chỉ là quy tắc placeholder
   long-if-bar-up/short-if-bar-down dùng để thử đường accounting — KHÔNG phải
   implementation của bất kỳ family nào trong shortlist (NQ-F1/F2/F3,
   FX-F1..F4, JF1/JF3, các contingency 6A). Chưa có adapter/frozen-rule nào
   của family tồn tại.
3. **Freeze-builder thực**: chỉ có SPEC freeze-builder (spec giấy) + GATE-0
   refusal; chưa có builder chạy được từng mã/family, chưa có proof
   no-lookahead/boundary qua dữ liệu tổng hợp trên đường code sẽ dùng khi
   execution.

## Giá trị không bị rút lại

Đạt thật và đã verify (VERIFIED_WITH_NOTES, 0 CRITICAL): 74/74 digest khớp;
các số then chốt tính lại EXACT; pytest 42/42 (tái chạy tại SHA audit);
fix lớp BUG1/BUG2 finalization; sandbox isolation; census + ancestry sạch;
đóng mới các capture lịch chính thức. Những gì ERRATUM này làm là đặt lại
phạm vi đúng — phần việc còn lại thuộc đợt tiếp của cùng round.

— Hết ERRATUM 1 (đính kèm wave-3 của round; không thay đổi verdict verify cũ).
