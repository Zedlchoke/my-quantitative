# FREEZE R1 ADDENDUM r2 — supplementary corpus round (pin trước khi chạy, 2026-09-27)

- Hoàn cảnh: corpus round 1 đạt 10/12 entries admissible (5/5 author floor
  ĐẠT) tại đúng cap 30/30 fetch; ranking theo protocol §1.5-3 CHƯA hợp pháp.
  Đóng cycle vì lỗi thu thập sẽ là close yếu hơn so với close bằng đo
  (death ledger) — mục đích chương trình.
- **Quyết định (A1, công khai trước khi chạy):** cấp MỘT vòng bổ sung
  **≤20 web fetch**, cùng toàn bộ tiêu chí admissibility/khoảng-cấm/K=5 như
  cũ, mục tiêu duy nhất: đóng khoảng trống ≥12 entries. Fetch-cap tổng của
  corpus build thành 50 (30 đã dùng + ≤20 bổ sung), ghi công khai trong
  FETCH_LOG.
- **Nếu sau vòng bổ sung vẫn <12 entries:** corpus close
  `CORPUS_FLOOR_FAILED` — council buộc phải adjudicate census tạm thời
  (10-11 entries) với disclosure đầy đủ; death ledger khi đó mang nhãn
  `PROVISIONAL_CORPUS`, không phải kết quả ranked.
- Không PnL, không outcome, không sealed — vẫn phạm vi GO-1 freeze.
