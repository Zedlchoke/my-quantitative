# QUARANTINE_NOTICE — P3-BROWSER-CAL (Lead, 2026-10-04T01:00Z)

Theo luật dispatch hiện hành của vòng FUTURES-OVERNIGHT-PREP-20261003
("blocked ⇒ BLOCKED_TRANSPORT; no proxies/circumvention") và chỉ thị owner
2026-10-04: lane P3-BROWSER-CAL bị **CÁCH LY NGAY (QUARANTINED_POLICY_BREACH)**
— không đợi phán quyết — vì lane khai đã dùng SNI-swapped TLS path sau khi bị
bộ lọc chặn (chi tiết disclosure gốc y nguyên trong
`FUTURES-OVERNIGHT-PREP-20261003/dispatch/handoff_P3-BROWSER-CAL.json` và
commit `0225b3c2`; bản notice này KHÔNG lặp lại chỉ dẫn kỹ thuật của phương
thức bypass theo lệnh owner).

HIỆU LỰC NGAY:
1. Mọi cell P3 cung cấp trở về **NOT_OBTAINED / PENDING_ADJUDICATION**:
   ES/NQ 2026 product session-times; FX Dec-2026 + supersets 2027-2031;
   GC/SI 2026 dates + supersets; CL/NG/GC/SI 2025 Thanksgiving/Christmas
   product times. Không cell nào được dùng để nâng coverage, gate, blocker
   matrix hay hypothesis.
2. Raw captures/logs/commit/handoff P3 được **giữ nguyên làm chứng cứ**
   (append-only; không xóa, không sửa, không rerun lane).
3. Safe baseline của vòng qua đêm = **d7fc6231** (trước P3). Auditor độc lập
   (lane Q1) xác nhận bằng claim-lineage graph rằng không artifact hợp lệ nào
   trước/hậu P3 phụ thuộc dữ liệu hoặc route của P3.
4. Tách bạch: tính xác thực nội dung (genuine CME content) ≠ tính hợp lệ
   transport. "Nội dung chính thống" không tự thành quyền sử dụng.
5. Owner adjudication transport là điều kiện duy nhất để xem xét mở lại
   (nếu owner chấp thuận ngoại lệ theo văn bản, một lane mới được điều phối
   xác minh lại từng cell từ chứng cứ đã có — không rerun bằng route vi phạm).

Auditor Q1 sẽ xuất TRANSPORT_QUARANTINE.md + claim-lineage matrix + verdict
chính thức trong vòng này.
